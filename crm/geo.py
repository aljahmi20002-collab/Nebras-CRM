"""Global administrative geography for NebrasCRM.

The original Yemen-only hierarchy has been replaced by a globally portable model:
Country -> first-level administrative region/state -> city.  The bundled GeoNames
cities500 dataset covers every country, its published first-level regions, and more
than 235,000 cities/localities (cities with population >= 500 plus administrative
seats).  It is intentionally stored as a compact source archive and imported into
SQLite once, so the CRM works without a third-party geocoding API at runtime.

Legacy table/column names are retained internally for backward compatibility with
existing CRM records:
  geo_governorates = countries, geo_districts = regions, geo_villages = cities
  gov_id = country_id, district_id = region_id, village_id = city_id
New API endpoints use the global terminology exclusively.
"""
import datetime
import os
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel

con = None
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data" / "geonames"
DATASET_VERSION = "geonames-cities500-2026-08"
DATASET_NAME = "GeoNames cities500 + countryInfo + admin1CodesASCII"
DATASET_LICENSE = "GeoNames data is licensed under CC BY 4.0"

# The labels are supplied to the SPA and public API. Names themselves are kept in
# their source/local spelling and English ASCII form; Arabic UI users can still
# search either spelling.
LEVELS = {
    1: {"key": "country", "en": "Country", "ar": "دولة", "table": "geo_governorates"},
    2: {"key": "region", "en": "Region / State", "ar": "منطقة / ولاية", "table": "geo_districts"},
    3: {"key": "city", "en": "City", "ar": "مدينة", "table": "geo_villages"},
    4: {"key": "neighborhood", "en": "Neighborhood", "ar": "حي", "table": "geo_quarters"},
    5: {"key": "street", "en": "Street", "ar": "شارع", "table": "geo_streets"},
}


def _table_exists(c, table: str) -> bool:
    import db as D
    return D.table_exists(c, table)


def _columns(c, table: str) -> set[str]:
    import db as D
    return D.table_columns(c, table)


def _ensure_columns(c, table: str, columns: dict[str, str]):
    existing = _columns(c, table)
    for name, sql_type in columns.items():
        if name not in existing:
            c.execute(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {sql_type}')


def _setting(c, key: str, default: str = "") -> str:
    row = c.execute("SELECT \"value\" FROM settings WHERE \"key\"=?", (key,)).fetchone()
    return (row["value"] if row else default) or default


def _set_setting(c, key: str, value: str):
    c.execute(
        "INSERT INTO settings(\"key\",\"value\") VALUES(?,?) ON CONFLICT(\"key\") DO UPDATE SET \"value\"=excluded.\"value\"",
        (key, value),
    )


def _data_paths() -> tuple[Path, Path, Path]:
    return (
        DATA_DIR / "countryInfo.txt",
        DATA_DIR / "admin1CodesASCII.txt",
        DATA_DIR / "cities500.zip",
    )


def _require_data_files():
    files = _data_paths()
    missing = [str(path.relative_to(HERE)) for path in files if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Global geography data is missing: " + ", ".join(missing) +
            ". Restore the bundled data/geonames files before starting NebrasCRM."
        )
    return files


def _clear_legacy_yemen_data(c):
    """Remove Yemen-specific locations and location references before global import."""
    # Existing CRM records retain all business data; only their old Yemen map
    # pointers are cleared because numeric IDs no longer identify the same place.
    for table, cols in {
        "accounts": ("gov_id", "district_id", "village_id", "quarter_id", "street_id"),
        "agents": ("gov_id", "district_id", "village_id", "quarter_id"),
    }.items():
        if _table_exists(c, table):
            present = _columns(c, table)
            updates = [f'"{column}"=NULL' for column in cols if column in present]
            if updates:
                c.execute(f'UPDATE "{table}" SET {", ".join(updates)}')

    for table in ("territories", "geo_streets", "geo_quarters", "geo_villages", "geo_uzlah",
                  "geo_districts", "geo_governorates"):
        if _table_exists(c, table):
            c.execute(f'DELETE FROM "{table}"')


def _read_countries(path: Path):
    countries = {}
    rows = []
    with path.open(encoding="utf-8") as src:
        for line in src:
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 17:
                continue
            iso2, iso3, numeric, _fips, name, capital = fields[:6]
            try:
                geoname_id = int(fields[16])
                population = int(fields[7] or 0)
            except (TypeError, ValueError):
                continue
            if not iso2 or not geoname_id:
                continue
            country = {
                "id": geoname_id,
                "code": iso2,
                "iso3": iso3,
                "numeric": numeric,
                "name": name,
                "capital": capital,
                "continent": fields[8] if len(fields) > 8 else "",
                "phone": fields[12] if len(fields) > 12 else "",
                "population": population,
            }
            countries[iso2] = country
            rows.append((geoname_id, iso2, name, name, capital, capital, country["phone"],
                         iso3, country["continent"], population))
    return countries, rows


def _read_regions(path: Path, countries: dict):
    regions = {}
    rows = []
    with path.open(encoding="utf-8") as src:
        for line in src:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 4 or "." not in fields[0]:
                continue
            full_code, name, ascii_name, raw_id = fields[:4]
            country_code, region_code = full_code.split(".", 1)
            if country_code not in countries:
                continue
            try:
                geoname_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if not geoname_id:
                continue
            regions[(country_code, region_code)] = geoname_id
            rows.append((geoname_id, countries[country_code]["id"], full_code, name or ascii_name,
                         ascii_name or name, country_code))
    return regions, rows


def _city_batches(zip_path: Path, countries: dict, regions: dict, batch_size: int = 2_000):
    """Yield insertion batches without materialising the 235k-city file in RAM."""
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open("cities500.txt") as raw:
            batch = []
            for line in raw:
                fields = line.decode("utf-8", errors="replace").rstrip("\n").split("\t")
                if len(fields) < 19:
                    continue
                try:
                    city_id = int(fields[0])
                    latitude = float(fields[4])
                    longitude = float(fields[5])
                    population = int(fields[14] or 0)
                except (TypeError, ValueError):
                    continue
                country_code, admin1 = fields[8], fields[10]
                country = countries.get(country_code)
                if not country:
                    continue
                region_id = regions.get((country_code, admin1))
                name = fields[1] or fields[2]
                name_en = fields[2] or name
                batch.append((
                    city_id,
                    region_id,  # legacy uzlah_id is retained as a region pointer
                    name,
                    name_en,
                    region_id,
                    country["id"],
                    city_id,
                    population,
                    latitude,
                    longitude,
                    fields[17] or "",
                    country_code,
                    admin1 or "",
                    fields[7] or "",
                ))
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch


def import_world_dataset(c, force: bool = False):
    """Import bundled global countries, regions and cities into SQLite.

    This action deliberately removes the previous Yemen-only locations and
    clears their references from CRM records. It never deletes customers, deals,
    partners or any other business record.
    """
    current = _setting(c, "geo_dataset_version")
    count = c.execute("SELECT COUNT(*) n FROM geo_villages").fetchone()["n"]
    if not force and current == DATASET_VERSION and count >= 200_000:
        return world_status(c)

    country_path, region_path, city_zip = _require_data_files()
    countries, country_rows = _read_countries(country_path)
    regions, region_rows = _read_regions(region_path, countries)
    if len(countries) < 200 or len(regions) < 1_000:
        raise RuntimeError("Bundled global geography files are incomplete.")

    _clear_legacy_yemen_data(c)
    c.executemany(
        """INSERT INTO geo_governorates
           (id,code,name_ar,name_en,capital_ar,capital_en,phone_plan,iso3,continent,population)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        country_rows,
    )
    c.executemany(
        """INSERT INTO geo_districts(id,gov_id,code,name_ar,name_en,country_code)
           VALUES(?,?,?,?,?,?)""",
        region_rows,
    )

    inserted = 0
    for batch in _city_batches(city_zip, countries, regions):
        c.executemany(
            """INSERT INTO geo_villages
               (id,uzlah_id,name_ar,name_en,region_id,country_id,code,population,lat,lon,
                timezone,country_code,region_code,feature_code)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            batch,
        )
        inserted += len(batch)

    if inserted < 200_000:
        raise RuntimeError("Global city import was incomplete; previous data was not marked ready.")
    _set_setting(c, "geo_dataset_version", DATASET_VERSION)
    _set_setting(c, "geo_dataset_name", DATASET_NAME)
    _set_setting(c, "geo_dataset_license", DATASET_LICENSE)
    _set_setting(c, "geo_dataset_imported_at", datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"))
    c.commit()
    return world_status(c)


def world_status(c=None):
    db = c or con
    count = lambda table: db.execute(f'SELECT COUNT(*) n FROM "{table}"').fetchone()["n"]
    return {
        "version": _setting(db, "geo_dataset_version"),
        "name": _setting(db, "geo_dataset_name", DATASET_NAME),
        "license": _setting(db, "geo_dataset_license", DATASET_LICENSE),
        "imported_at": _setting(db, "geo_dataset_imported_at"),
        "counts": {
            "countries": count("geo_governorates"),
            "regions": count("geo_districts"),
            "cities": count("geo_villages"),
            "neighborhoods": count("geo_quarters"),
            "streets": count("geo_streets"),
        },
    }


def init_tables(c):
    # Legacy table names are kept so existing deployments can migrate in place.
    c.execute("""CREATE TABLE IF NOT EXISTS geo_governorates(
        id INTEGER PRIMARY KEY, code VARCHAR(16), name_ar VARCHAR(255), name_en VARCHAR(255),
        capital_ar VARCHAR(255), capital_en VARCHAR(255), phone_plan VARCHAR(64), lat REAL, lon REAL,
        iso3 VARCHAR(16), continent VARCHAR(16), population INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS geo_districts(
        id INTEGER PRIMARY KEY AUTOINCREMENT, gov_id INTEGER, code VARCHAR(64),
        name_ar VARCHAR(255), name_en VARCHAR(255), lat REAL, lon REAL, country_code VARCHAR(16))""")
    c.execute("""CREATE TABLE IF NOT EXISTS geo_uzlah(
        id INTEGER PRIMARY KEY AUTOINCREMENT, district_id INTEGER,
        name_ar VARCHAR(255), name_en VARCHAR(255))""")
    c.execute("""CREATE TABLE IF NOT EXISTS geo_villages(
        id INTEGER PRIMARY KEY AUTOINCREMENT, uzlah_id INTEGER,
        name_ar VARCHAR(255), name_en VARCHAR(255), region_id INTEGER, country_id INTEGER,
        code INTEGER, population INTEGER DEFAULT 0, lat REAL, lon REAL,
        timezone VARCHAR(64), country_code VARCHAR(16), region_code VARCHAR(32), feature_code VARCHAR(32))""")
    c.execute("""CREATE TABLE IF NOT EXISTS geo_quarters(
        id INTEGER PRIMARY KEY AUTOINCREMENT, district_id INTEGER, village_id INTEGER,
        name_ar VARCHAR(255), name_en VARCHAR(255), notes TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS geo_streets(
        id INTEGER PRIMARY KEY AUTOINCREMENT, quarter_id INTEGER, district_id INTEGER,
        name_ar VARCHAR(255), name_en VARCHAR(255), notes TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS territories(
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id INTEGER,
        gov_id INTEGER, district_id INTEGER, exclusive INTEGER DEFAULT 1,
        created_at TEXT)""")
    if not _table_exists(c, "settings"):
        c.execute("CREATE TABLE settings(\"key\" VARCHAR(255) PRIMARY KEY, \"value\" TEXT)")

    _ensure_columns(c, "geo_governorates", {
        "iso3": "TEXT", "continent": "TEXT", "population": "INTEGER DEFAULT 0",
    })
    _ensure_columns(c, "geo_districts", {"country_code": "TEXT"})
    _ensure_columns(c, "geo_villages", {
        "region_id": "INTEGER", "country_id": "INTEGER", "code": "INTEGER",
        "population": "INTEGER DEFAULT 0", "lat": "REAL", "lon": "REAL", "timezone": "TEXT",
        "country_code": "TEXT", "region_code": "TEXT", "feature_code": "TEXT",
    })
    for sql in (
        "CREATE INDEX IF NOT EXISTS ix_region_country ON geo_districts(gov_id)",
        "CREATE INDEX IF NOT EXISTS ix_city_region ON geo_villages(region_id)",
        "CREATE INDEX IF NOT EXISTS ix_city_country ON geo_villages(country_id)",
        "CREATE INDEX IF NOT EXISTS ix_city_en ON geo_villages(name_en)",
        "CREATE INDEX IF NOT EXISTS ix_city_local ON geo_villages(name_ar)",
        "CREATE INDEX IF NOT EXISTS ix_quarter_city ON geo_quarters(village_id)",
        "CREATE INDEX IF NOT EXISTS ix_street_quarter ON geo_streets(quarter_id)",
        "CREATE INDEX IF NOT EXISTS ix_territory_agent ON territories(agent_id)",
    ):
        c.execute(sql)
    c.commit()
    import_world_dataset(c)


def _limit(value: int, maximum: int = 200, default: int = 50) -> int:
    try:
        return min(maximum, max(1, int(value)))
    except (TypeError, ValueError):
        return default


def _country_or_404(country_id: int):
    row = con.execute("SELECT * FROM geo_governorates WHERE id=?", (country_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Country not found")
    return row


def _region_or_404(region_id: int):
    row = con.execute("SELECT * FROM geo_districts WHERE id=?", (region_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Region not found")
    return row


def _city_or_404(city_id: int):
    row = con.execute("SELECT * FROM geo_villages WHERE id=?", (city_id,)).fetchone()
    if not row:
        raise HTTPException(404, "City not found")
    return row


def _country_rows(q: str = "", limit: int = 300):
    where, params = [], []
    if q:
        where.append("(c.name_ar LIKE ? OR c.name_en LIKE ? OR c.code LIKE ? OR c.iso3 LIKE ?)")
        params += [f"%{q}%"] * 4
    clause = "WHERE " + " AND ".join(where) if where else ""
    return [dict(row) for row in con.execute(f"""
        SELECT c.*,
               (SELECT COUNT(*) FROM geo_districts r WHERE r.gov_id=c.id) regions,
               (SELECT COUNT(*) FROM geo_villages ci WHERE ci.country_id=c.id) cities,
               (SELECT COUNT(*) FROM accounts a WHERE a.deleted=0 AND CAST(a.gov_id AS INTEGER)=c.id) accounts
        FROM geo_governorates c {clause}
        ORDER BY LOWER(c.name_en) LIMIT ?""", params + [_limit(limit, 300, 300)])]


def _region_rows(country_id: int = 0, q: str = "", limit: int = 200):
    where, params = [], []
    if country_id:
        where.append("r.gov_id=?")
        params.append(country_id)
    if q:
        where.append("(r.name_ar LIKE ? OR r.name_en LIKE ? OR r.code LIKE ?)")
        params += [f"%{q}%"] * 3
    clause = "WHERE " + " AND ".join(where) if where else ""
    return [dict(row) for row in con.execute(f"""
        SELECT r.*, c.name_ar country_ar, c.name_en country_en,
               (SELECT COUNT(*) FROM geo_villages ci WHERE ci.region_id=r.id) cities
        FROM geo_districts r JOIN geo_governorates c ON c.id=r.gov_id
        {clause} ORDER BY LOWER(r.name_en) LIMIT ?""", params + [_limit(limit)])]


def _city_rows(country_id: int = 0, region_id: int = 0, q: str = "", limit: int = 100):
    where, params = [], []
    if country_id:
        where.append("ci.country_id=?")
        params.append(country_id)
    if region_id:
        where.append("ci.region_id=?")
        params.append(region_id)
    if q:
        where.append("(ci.name_ar LIKE ? OR ci.name_en LIKE ?)")
        params += [f"%{q}%"] * 2
    # Listing all 235k cities without a parent/query is intentionally prevented.
    if not where:
        return []
    return [dict(row) for row in con.execute(f"""
        SELECT ci.*, r.name_ar region_ar, r.name_en region_en,
               c.name_ar country_ar, c.name_en country_en
        FROM geo_villages ci
        LEFT JOIN geo_districts r ON r.id=ci.region_id
        JOIN geo_governorates c ON c.id=ci.country_id
        WHERE {' AND '.join(where)}
        ORDER BY ci.population DESC, LOWER(ci.name_en) LIMIT ?""", params + [_limit(limit)])]


def _search(q: str, limit: int = 30):
    q = q.strip()
    if len(q) < 2:
        return []
    like = f"%{q}%"
    out = []
    for row in con.execute("""SELECT id,name_ar,name_en,NULL parent,'country' kind FROM geo_governorates
                            WHERE name_ar LIKE ? OR name_en LIKE ? OR code LIKE ? LIMIT 12""",
                         (like, like, like)):
        out.append(dict(row))
    for row in con.execute("""SELECT r.id,r.name_ar,r.name_en,c.name_ar parent,'region' kind
                            FROM geo_districts r JOIN geo_governorates c ON c.id=r.gov_id
                            WHERE r.name_ar LIKE ? OR r.name_en LIKE ? LIMIT 18""", (like, like)):
        out.append(dict(row))
    for row in con.execute("""SELECT ci.id,ci.name_ar,ci.name_en,
                                   COALESCE(r.name_ar,c.name_ar) parent,'city' kind,
                                   ci.population
                            FROM geo_villages ci
                            LEFT JOIN geo_districts r ON r.id=ci.region_id
                            JOIN geo_governorates c ON c.id=ci.country_id
                            WHERE ci.name_ar LIKE ? OR ci.name_en LIKE ?
                            ORDER BY ci.population DESC LIMIT 40""", (like, like)):
        out.append(dict(row))
    for item in out:
        level = next(number for number, meta in LEVELS.items() if meta["key"] == item["kind"])
        item["level"] = level
        item["level_ar"] = LEVELS[level]["ar"]
        item["level_en"] = LEVELS[level]["en"]
    return out[:_limit(limit, 60, 30)]


def register(app, current_user, require):
    @app.get("/api/geo/levels")
    def levels(user=Depends(current_user)):
        return LEVELS

    @app.get("/api/geo/status")
    def status(user=Depends(current_user)):
        return world_status()

    @app.post("/api/geo/rebuild")
    def rebuild(user=Depends(current_user)):
        require(user, "admin")
        return import_world_dataset(con, force=True)

    # ---------------- global public geography ----------------
    @app.get("/api/geo/countries")
    def countries(q: str = "", limit: int = 300, user=Depends(current_user)):
        return _country_rows(q.strip()[:120], limit)

    @app.get("/api/geo/regions")
    def regions(country_id: int = 0, q: str = "", limit: int = 200, user=Depends(current_user)):
        if country_id:
            _country_or_404(country_id)
        return _region_rows(country_id, q.strip()[:120], limit)

    @app.get("/api/geo/cities")
    def cities(country_id: int = 0, region_id: int = 0, q: str = "", limit: int = 100,
               user=Depends(current_user)):
        if region_id:
            region = _region_or_404(region_id)
            if country_id and region["gov_id"] != country_id:
                raise HTTPException(400, "Region does not belong to that country")
            country_id = region["gov_id"]
        elif country_id:
            _country_or_404(country_id)
        return _city_rows(country_id, region_id, q.strip()[:120], limit)

    @app.get("/api/geo/cities/{city_id}")
    def city(city_id: int, user=Depends(current_user)):
        row = dict(_city_or_404(city_id))
        region = con.execute("SELECT name_ar,name_en FROM geo_districts WHERE id=?", (row["region_id"],)).fetchone()
        country = _country_or_404(row["country_id"])
        row["region_ar"] = region["name_ar"] if region else ""
        row["region_en"] = region["name_en"] if region else ""
        row["country_ar"] = country["name_ar"]
        row["country_en"] = country["name_en"]
        return row

    @app.get("/api/geo/search")
    def geo_search(q: str, limit: int = 30, user=Depends(current_user)):
        return _search(q, limit)

    # ---------------- backwards-compatible aliases ----------------
    @app.get("/api/geo/governorates")
    def governorates(q: str = "", limit: int = 300, user=Depends(current_user)):
        """Deprecated alias for countries; retained for existing integrations."""
        return _country_rows(q.strip()[:120], limit)

    @app.get("/api/geo/districts")
    def districts(gov_id: int = 0, country_id: int = 0, q: str = "", limit: int = 200,
                  user=Depends(current_user)):
        return _region_rows(country_id or gov_id, q.strip()[:120], limit)

    @app.get("/api/geo/uzlah")
    def uzlah(district_id: int = 0, region_id: int = 0, q: str = "", limit: int = 100,
              user=Depends(current_user)):
        """Deprecated alias for cities within a region."""
        return _city_rows(0, region_id or district_id, q.strip()[:120], limit)

    @app.get("/api/geo/villages")
    def villages(uzlah_id: int = 0, city_id: int = 0, user=Depends(current_user)):
        """Legacy endpoint. Cities are now the deepest imported global level."""
        selected = city_id or uzlah_id
        return [dict(_city_or_404(selected))] if selected else []

    # ---------------- neighborhoods and streets managed by the CRM ----------------
    @app.get("/api/geo/neighborhoods")
    def neighborhoods(region_id: int = 0, city_id: int = 0, user=Depends(current_user)):
        where, params = [], []
        if region_id:
            where.append("district_id=?")
            params.append(region_id)
        if city_id:
            where.append("village_id=?")
            params.append(city_id)
        sql = "SELECT * FROM geo_quarters" + (" WHERE " + " AND ".join(where) if where else "")
        return [dict(row) for row in con.execute(sql + " ORDER BY LOWER(name_en), name_ar", params)]

    @app.get("/api/geo/quarters")
    def quarters(district_id: int = 0, village_id: int = 0, user=Depends(current_user)):
        return neighborhoods(district_id, village_id, user)

    @app.get("/api/geo/streets")
    def streets(neighborhood_id: int = 0, quarter_id: int = 0, region_id: int = 0,
                district_id: int = 0, user=Depends(current_user)):
        where, params = [], []
        selected_quarter = neighborhood_id or quarter_id
        selected_region = region_id or district_id
        if selected_quarter:
            where.append("quarter_id=?")
            params.append(selected_quarter)
        if selected_region:
            where.append("district_id=?")
            params.append(selected_region)
        sql = "SELECT * FROM geo_streets" + (" WHERE " + " AND ".join(where) if where else "")
        return [dict(row) for row in con.execute(sql + " ORDER BY LOWER(name_en), name_ar", params)]

    class Place(BaseModel):
        name: str = ""
        name_ar: str = ""  # legacy field accepted for existing callers
        name_en: str = ""
        region_id: int = 0
        city_id: int = 0
        neighborhood_id: int = 0
        district_id: int = 0  # legacy aliases
        village_id: int = 0
        quarter_id: int = 0
        notes: str = ""

        def display_name(self) -> str:
            return (self.name or self.name_ar or self.name_en).strip()

    @app.post("/api/geo/neighborhoods")
    @app.post("/api/geo/quarters")
    def add_neighborhood(b: Place, user=Depends(current_user)):
        require(user, "admin", "manager")
        name = b.display_name()
        if not name or len(name) > 200 or len(b.name_en) > 200 or len(b.notes) > 2_000:
            raise HTTPException(400, "A valid neighborhood name is required")
        city_id = b.city_id or b.village_id
        region_id = b.region_id or b.district_id
        if city_id:
            city_row = _city_or_404(city_id)
            if region_id and city_row["region_id"] != region_id:
                raise HTTPException(400, "City does not belong to that region")
            region_id = city_row["region_id"]
        elif region_id:
            _region_or_404(region_id)
        else:
            raise HTTPException(400, "Pick a city or region")
        import db as D
        qid = con.execute("""INSERT INTO geo_quarters(district_id,village_id,name_ar,name_en,notes,created_at)
            VALUES(?,?,?,?,?,?)""", (region_id or None, city_id or None, name, b.name_en or name,
                                       b.notes, D.now())).lastrowid
        con.commit()
        return {"id": qid}

    @app.post("/api/geo/streets")
    def add_street(b: Place, user=Depends(current_user)):
        require(user, "admin", "manager")
        name = b.display_name()
        if not name or len(name) > 200 or len(b.name_en) > 200 or len(b.notes) > 2_000:
            raise HTTPException(400, "A valid street name is required")
        neighborhood_id = b.neighborhood_id or b.quarter_id
        region_id = b.region_id or b.district_id
        if neighborhood_id:
            quarter = con.execute("SELECT * FROM geo_quarters WHERE id=?", (neighborhood_id,)).fetchone()
            if not quarter:
                raise HTTPException(404, "Neighborhood not found")
            if region_id and quarter["district_id"] != region_id:
                raise HTTPException(400, "Neighborhood does not belong to that region")
            region_id = quarter["district_id"]
        if not region_id:
            raise HTTPException(400, "Pick a region or neighborhood")
        _region_or_404(region_id)
        import db as D
        street_id = con.execute("""INSERT INTO geo_streets(quarter_id,district_id,name_ar,name_en,notes,created_at)
            VALUES(?,?,?,?,?,?)""", (neighborhood_id or None, region_id, name, b.name_en or name,
                                       b.notes, D.now())).lastrowid
        con.commit()
        return {"id": street_id}

    # ---------------- global performance ----------------
    @app.get("/api/geo/stats")
    def stats(user=Depends(current_user)):
        status_data = world_status()
        by_country = [dict(row) for row in con.execute("""
            SELECT c.id, c.name_ar k, c.name_en k_en, c.code, c.continent,
                   (SELECT COUNT(*) FROM geo_districts r WHERE r.gov_id=c.id) regions,
                   (SELECT COUNT(*) FROM geo_villages ci WHERE ci.country_id=c.id) cities,
                   (SELECT COUNT(*) FROM accounts a WHERE a.deleted=0
                     AND CAST(a.gov_id AS INTEGER)=c.id) accounts,
                   (SELECT COALESCE(SUM(d.amount),0) FROM deals d
                     JOIN accounts a2 ON a2.id=CAST(d.account_id AS INTEGER)
                     WHERE d.deleted=0 AND d.stage='Closed Won'
                     AND CAST(a2.gov_id AS INTEGER)=c.id) revenue,
                   (SELECT COUNT(*) FROM territories t WHERE t.gov_id=c.id) partners
            FROM geo_governorates c ORDER BY revenue DESC, LOWER(c.name_en)""")]
        counts = status_data["counts"]
        # Legacy aliases ease a non-breaking migration for clients using old keys.
        counts.update({
            "governorates": counts["countries"],
            "districts": counts["regions"],
            "villages": counts["cities"],
            "quarters": counts["neighborhoods"],
        })
        return {**status_data, "counts": counts, "by_country": by_country,
                "by_governorate": by_country}

    # ---------------- partner territories ----------------
    class Territory(BaseModel):
        agent_id: int
        country_id: int = 0
        region_id: int = 0
        gov_id: int = 0       # legacy aliases
        district_id: int = 0
        exclusive: bool = True

    @app.get("/api/geo/territories")
    def list_territories(agent_id: int = 0, user=Depends(current_user)):
        where = "WHERE t.agent_id=?" if agent_id else ""
        params = [agent_id] if agent_id else []
        return [dict(row) for row in con.execute(f"""
            SELECT t.*, a.name agent_name,
                   c.name_ar country_ar, c.name_en country_en,
                   r.name_ar region_ar, r.name_en region_en,
                   c.name_ar gov_ar, c.name_en gov_en, r.name_ar dis_ar, r.name_en dis_en
            FROM territories t
            LEFT JOIN agents a ON a.id=t.agent_id
            LEFT JOIN geo_governorates c ON c.id=t.gov_id
            LEFT JOIN geo_districts r ON r.id=t.district_id
            {where} ORDER BY t.id DESC""", params)]

    @app.post("/api/geo/territories")
    def add_territory(b: Territory, user=Depends(current_user)):
        require(user, "admin", "manager")
        country_id = b.country_id or b.gov_id
        region_id = b.region_id or b.district_id
        if not country_id and not region_id:
            raise HTTPException(400, "Pick a country or region")
        agent = con.execute("SELECT id FROM agents WHERE id=? AND deleted=0", (b.agent_id,)).fetchone()
        if not agent:
            raise HTTPException(400, "Partner not found")
        if region_id:
            region = _region_or_404(region_id)
            if country_id and region["gov_id"] != country_id:
                raise HTTPException(400, "Region does not belong to that country")
            country_id = region["gov_id"]
        else:
            _country_or_404(country_id)

        if b.exclusive:
            if region_id:
                clash = con.execute("""SELECT t.id, a.name FROM territories t
                    LEFT JOIN agents a ON a.id=t.agent_id
                    WHERE t.exclusive=1 AND t.agent_id!=?
                      AND (t.district_id=? OR (t.gov_id=? AND t.district_id IS NULL)) LIMIT 1""",
                    (b.agent_id, region_id, country_id)).fetchone()
            else:
                clash = con.execute("""SELECT t.id, a.name FROM territories t
                    LEFT JOIN agents a ON a.id=t.agent_id
                    WHERE t.exclusive=1 AND t.agent_id!=? AND t.gov_id=? LIMIT 1""",
                    (b.agent_id, country_id)).fetchone()
            if clash:
                raise HTTPException(400, f"Already assigned exclusively to {clash['name']}")
        duplicate = con.execute("""SELECT 1 FROM territories WHERE agent_id=?
            AND COALESCE(gov_id,0)=COALESCE(?,0) AND COALESCE(district_id,0)=COALESCE(?,0)""",
            (b.agent_id, country_id, region_id)).fetchone()
        if duplicate:
            raise HTTPException(400, "This territory is already assigned to the partner")
        import db as D
        territory_id = con.execute("""INSERT INTO territories(agent_id,gov_id,district_id,exclusive,created_at)
            VALUES(?,?,?,?,?)""", (b.agent_id, country_id, region_id or None,
                                     1 if b.exclusive else 0, D.now())).lastrowid
        con.commit()
        return {"id": territory_id, "country_id": country_id, "region_id": region_id or None}

    @app.delete("/api/geo/territories/{territory_id}")
    def delete_territory(territory_id: int, user=Depends(current_user)):
        require(user, "admin", "manager")
        cur = con.execute("DELETE FROM territories WHERE id=?", (territory_id,))
        if not cur.rowcount:
            raise HTTPException(404, "Territory not found")
        con.commit()
        return {"ok": True}
