"""Yemen administrative geography.

Official 4-level hierarchy imported from open datasets:
  Governorate (محافظة) -> District (مديرية) -> Uzlah (عزلة) -> Village (قرية)
Plus two user-managed urban levels that no open dataset covers:
  Quarter/Hara (حارة) and Street (شارع)

Territories map governorates/districts to agents for exclusive coverage.
"""
import os, json
from typing import Optional
from fastapi import Depends, HTTPException
from pydantic import BaseModel

con = None
HERE = os.path.dirname(os.path.abspath(__file__))

LEVELS = {
    1: {"en": "Governorate", "ar": "محافظة", "table": "geo_governorates"},
    2: {"en": "District",    "ar": "مديرية",  "table": "geo_districts"},
    3: {"en": "Uzlah",       "ar": "عزلة",    "table": "geo_uzlah"},
    4: {"en": "Village",     "ar": "قرية",    "table": "geo_villages"},
    5: {"en": "Quarter",     "ar": "حارة",    "table": "geo_quarters"},
    6: {"en": "Street",      "ar": "شارع",    "table": "geo_streets"},
}


def init_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS geo_governorates(
        id INTEGER PRIMARY KEY, code TEXT, name_ar TEXT, name_en TEXT,
        capital_ar TEXT, capital_en TEXT, phone_plan TEXT, lat REAL, lon REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS geo_districts(
        id INTEGER PRIMARY KEY AUTOINCREMENT, gov_id INTEGER, code TEXT,
        name_ar TEXT, name_en TEXT, lat REAL, lon REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS geo_uzlah(
        id INTEGER PRIMARY KEY AUTOINCREMENT, district_id INTEGER,
        name_ar TEXT, name_en TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS geo_villages(
        id INTEGER PRIMARY KEY AUTOINCREMENT, uzlah_id INTEGER,
        name_ar TEXT, name_en TEXT)""")
    # user-managed urban levels
    c.execute("""CREATE TABLE IF NOT EXISTS geo_quarters(
        id INTEGER PRIMARY KEY AUTOINCREMENT, district_id INTEGER, village_id INTEGER,
        name_ar TEXT, name_en TEXT, notes TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS geo_streets(
        id INTEGER PRIMARY KEY AUTOINCREMENT, quarter_id INTEGER, district_id INTEGER,
        name_ar TEXT, name_en TEXT, notes TEXT, created_at TEXT)""")
    # agent territory assignment
    c.execute("""CREATE TABLE IF NOT EXISTS territories(
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id INTEGER,
        gov_id INTEGER, district_id INTEGER, exclusive INTEGER DEFAULT 1,
        created_at TEXT)""")
    for idx, sql in [
        ("ix_dis_gov", "CREATE INDEX IF NOT EXISTS ix_dis_gov ON geo_districts(gov_id)"),
        ("ix_uz_dis", "CREATE INDEX IF NOT EXISTS ix_uz_dis ON geo_uzlah(district_id)"),
        ("ix_vl_uz", "CREATE INDEX IF NOT EXISTS ix_vl_uz ON geo_villages(uzlah_id)"),
        ("ix_ter_ag", "CREATE INDEX IF NOT EXISTS ix_ter_ag ON territories(agent_id)"),
        ("ix_vl_name", "CREATE INDEX IF NOT EXISTS ix_vl_name ON geo_villages(name_ar)"),
    ]:
        c.execute(sql)
    c.commit()


def import_dataset(c, path):
    """Import the full hierarchy. Idempotent."""
    if c.execute("SELECT COUNT(*) n FROM geo_governorates").fetchone()["n"]:
        return {"skipped": True}
    data = json.load(open(path, encoding="utf-8"))
    ng = nd = nu = nv = 0
    for g in data["governorates"]:
        c.execute("""INSERT OR REPLACE INTO geo_governorates
            (id,code,name_ar,name_en,capital_ar,capital_en,phone_plan) VALUES(?,?,?,?,?,?,?)""",
            (g["id"], g.get("phone_numbering_plan"), g["name_ar"], g["name_en"],
             g.get("capital_name_ar"), g.get("capital_name_en"), g.get("phone_numbering_plan")))
        ng += 1
        for d in g.get("districts", []):
            did = c.execute("""INSERT INTO geo_districts(gov_id,name_ar,name_en)
                               VALUES(?,?,?)""", (g["id"], d["name_ar"], d["name_en"])).lastrowid
            nd += 1
            for u in d.get("uzaal", []) or []:
                uid = c.execute("""INSERT INTO geo_uzlah(district_id,name_ar,name_en)
                                   VALUES(?,?,?)""", (did, u["name_ar"], u["name_en"])).lastrowid
                nu += 1
                for v in u.get("villages", []) or []:
                    c.execute("""INSERT INTO geo_villages(uzlah_id,name_ar,name_en)
                                 VALUES(?,?,?)""", (uid, v["name_ar"], v["name_en"]))
                    nv += 1
    c.commit()
    return {"governorates": ng, "districts": nd, "uzlah": nu, "villages": nv}


def enrich_coords(c, path):
    """Attach lat/lon from the open-admin-data set (matched by English name)."""
    try:
        gov = json.load(open(path, encoding="utf-8"))
    except Exception:
        return 0
    n = 0
    for g in gov:
        nm = (g.get("name") or {}).get("en", "")
        geo = g.get("geo") or {}
        if not nm or not geo.get("lat"):
            continue
        r = c.execute("SELECT id FROM geo_governorates WHERE name_en LIKE ?",
                      ("%" + nm.split()[0] + "%",)).fetchone()
        if r:
            c.execute("UPDATE geo_governorates SET lat=?, lon=? WHERE id=?",
                      (float(geo["lat"]), float(geo["lon"]), r["id"]))
            n += 1
    c.commit()
    return n


def register(app, current_user, require):

    @app.get("/api/geo/levels")
    def levels(user=Depends(current_user)):
        return LEVELS

    @app.get("/api/geo/governorates")
    def governorates(user=Depends(current_user)):
        return [dict(r) for r in con.execute("""
            SELECT g.*, (SELECT COUNT(*) FROM geo_districts d WHERE d.gov_id=g.id) districts,
                   (SELECT COUNT(*) FROM accounts a WHERE a.deleted=0
                     AND CAST(a.gov_id AS INTEGER)=g.id) accounts
            FROM geo_governorates g ORDER BY g.name_ar""")]

    @app.get("/api/geo/districts")
    def districts(gov_id: int, user=Depends(current_user)):
        return [dict(r) for r in con.execute("""
            SELECT d.*, (SELECT COUNT(*) FROM geo_uzlah u WHERE u.district_id=d.id) uzlah
            FROM geo_districts d WHERE d.gov_id=? ORDER BY d.name_ar""", (gov_id,))]

    @app.get("/api/geo/uzlah")
    def uzlah(district_id: int, user=Depends(current_user)):
        return [dict(r) for r in con.execute("""
            SELECT u.*, (SELECT COUNT(*) FROM geo_villages v WHERE v.uzlah_id=u.id) villages
            FROM geo_uzlah u WHERE u.district_id=? ORDER BY u.name_ar""", (district_id,))]

    @app.get("/api/geo/villages")
    def villages(uzlah_id: int, user=Depends(current_user)):
        return [dict(r) for r in con.execute(
            "SELECT * FROM geo_villages WHERE uzlah_id=? ORDER BY name_ar", (uzlah_id,))]

    @app.get("/api/geo/quarters")
    def quarters(district_id: int = 0, village_id: int = 0, user=Depends(current_user)):
        w, p = [], []
        if district_id: w.append("district_id=?"); p.append(district_id)
        if village_id:  w.append("village_id=?"); p.append(village_id)
        sql = "SELECT * FROM geo_quarters" + (" WHERE " + " AND ".join(w) if w else "")
        return [dict(r) for r in con.execute(sql + " ORDER BY name_ar", p)]

    @app.get("/api/geo/streets")
    def streets(quarter_id: int = 0, district_id: int = 0, user=Depends(current_user)):
        w, p = [], []
        if quarter_id: w.append("quarter_id=?"); p.append(quarter_id)
        if district_id: w.append("district_id=?"); p.append(district_id)
        sql = "SELECT * FROM geo_streets" + (" WHERE " + " AND ".join(w) if w else "")
        return [dict(r) for r in con.execute(sql + " ORDER BY name_ar", p)]

    class Place(BaseModel):
        name_ar: str
        name_en: str = ""
        district_id: int = 0
        village_id: int = 0
        quarter_id: int = 0
        notes: str = ""

    @app.post("/api/geo/quarters")
    def add_quarter(b: Place, user=Depends(current_user)):
        if user["role"] == "readonly": raise HTTPException(403, "Read-only user")
        import db as D
        qid = con.execute("""INSERT INTO geo_quarters(district_id,village_id,name_ar,name_en,notes,created_at)
            VALUES(?,?,?,?,?,?)""", (b.district_id or None, b.village_id or None,
            b.name_ar, b.name_en, b.notes, D.now())).lastrowid
        con.commit(); return {"id": qid}

    @app.post("/api/geo/streets")
    def add_street(b: Place, user=Depends(current_user)):
        if user["role"] == "readonly": raise HTTPException(403, "Read-only user")
        import db as D
        sid = con.execute("""INSERT INTO geo_streets(quarter_id,district_id,name_ar,name_en,notes,created_at)
            VALUES(?,?,?,?,?,?)""", (b.quarter_id or None, b.district_id or None,
            b.name_ar, b.name_en, b.notes, D.now())).lastrowid
        con.commit(); return {"id": sid}

    @app.get("/api/geo/search")
    def geo_search(q: str, limit: int = 30, user=Depends(current_user)):
        if len(q) < 2: return []
        out, like = [], f"%{q}%"
        for lvl, sql in [
            (1, "SELECT id,name_ar,name_en,NULL parent FROM geo_governorates WHERE name_ar LIKE ? OR name_en LIKE ? LIMIT 8"),
            (2, """SELECT d.id,d.name_ar,d.name_en,g.name_ar parent FROM geo_districts d
                   JOIN geo_governorates g ON g.id=d.gov_id
                   WHERE d.name_ar LIKE ? OR d.name_en LIKE ? LIMIT 10"""),
            (3, """SELECT u.id,u.name_ar,u.name_en,d.name_ar parent FROM geo_uzlah u
                   JOIN geo_districts d ON d.id=u.district_id
                   WHERE u.name_ar LIKE ? OR u.name_en LIKE ? LIMIT 10"""),
            (4, """SELECT v.id,v.name_ar,v.name_en,u.name_ar parent FROM geo_villages v
                   JOIN geo_uzlah u ON u.id=v.uzlah_id
                   WHERE v.name_ar LIKE ? OR v.name_en LIKE ? LIMIT 12"""),
        ]:
            for r in con.execute(sql, (like, like)):
                d = dict(r); d["level"] = lvl
                d["level_ar"] = LEVELS[lvl]["ar"]; d["level_en"] = LEVELS[lvl]["en"]
                out.append(d)
        return out[:limit]

    @app.get("/api/geo/stats")
    def stats(user=Depends(current_user)):
        g = lambda s: con.execute(s).fetchone()[0] or 0
        by_gov = [dict(r) for r in con.execute("""
            SELECT g.id, g.name_ar k, g.name_en k_en,
                   (SELECT COUNT(*) FROM accounts a WHERE a.deleted=0
                     AND CAST(a.gov_id AS INTEGER)=g.id) n,
                   (SELECT COALESCE(SUM(d.amount),0) FROM deals d
                     JOIN accounts a2 ON a2.id=CAST(d.account_id AS INTEGER)
                     WHERE d.deleted=0 AND d.stage='Closed Won'
                     AND CAST(a2.gov_id AS INTEGER)=g.id) v,
                   (SELECT COUNT(*) FROM territories t WHERE t.gov_id=g.id) agents
            FROM geo_governorates g ORDER BY v DESC""")]
        return {
            "counts": {
                "governorates": g("SELECT COUNT(*) FROM geo_governorates"),
                "districts": g("SELECT COUNT(*) FROM geo_districts"),
                "uzlah": g("SELECT COUNT(*) FROM geo_uzlah"),
                "villages": g("SELECT COUNT(*) FROM geo_villages"),
                "quarters": g("SELECT COUNT(*) FROM geo_quarters"),
                "streets": g("SELECT COUNT(*) FROM geo_streets"),
            },
            "by_governorate": by_gov,
        }

    # ---------------- territories ----------------
    class Terr(BaseModel):
        agent_id: int
        gov_id: int = 0
        district_id: int = 0
        exclusive: bool = True

    @app.get("/api/geo/territories")
    def list_terr(agent_id: int = 0, user=Depends(current_user)):
        w = "WHERE t.agent_id=?" if agent_id else ""
        p = [agent_id] if agent_id else []
        return [dict(r) for r in con.execute(f"""
            SELECT t.*, a.name agent_name, g.name_ar gov_ar, g.name_en gov_en,
                   d.name_ar dis_ar, d.name_en dis_en
            FROM territories t
            LEFT JOIN agents a ON a.id=t.agent_id
            LEFT JOIN geo_governorates g ON g.id=t.gov_id
            LEFT JOIN geo_districts d ON d.id=t.district_id
            {w} ORDER BY t.id DESC""", p)]

    @app.post("/api/geo/territories")
    def add_terr(b: Terr, user=Depends(current_user)):
        require(user, "admin", "manager")
        if not b.gov_id and not b.district_id:
            raise HTTPException(400, "Pick a governorate or a district")
        # exclusivity guard: a district can only have one exclusive agent
        if b.exclusive:
            clash = con.execute("""SELECT t.id, a.name FROM territories t
                LEFT JOIN agents a ON a.id=t.agent_id
                WHERE t.exclusive=1 AND t.agent_id!=?
                  AND ((t.district_id=? AND ?!=0) OR (t.gov_id=? AND t.district_id IS NULL AND ?!=0))""",
                (b.agent_id, b.district_id, b.district_id, b.gov_id, b.gov_id)).fetchone()
            if clash:
                raise HTTPException(400, f"Already assigned exclusively to {clash['name']}")
        import db as D
        tid = con.execute("""INSERT INTO territories(agent_id,gov_id,district_id,exclusive,created_at)
            VALUES(?,?,?,?,?)""", (b.agent_id, b.gov_id or None, b.district_id or None,
            1 if b.exclusive else 0, D.now())).lastrowid
        con.commit(); return {"id": tid}

    @app.delete("/api/geo/territories/{tid}")
    def del_terr(tid: int, user=Depends(current_user)):
        require(user, "admin", "manager")
        con.execute("DELETE FROM territories WHERE id=?", (tid,)); con.commit()
        return {"ok": True}
