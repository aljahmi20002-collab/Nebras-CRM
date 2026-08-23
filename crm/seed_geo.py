"""Initialise global geography and globally distributed partner demo data.

The importer is idempotent. It replaces the retired Yemen-only administrative
hierarchy with countries, first-level regions/states and GeoNames cities500 data.
On a fresh demo database it also creates partner portal accounts spread across
several world regions, so `/agent` remains usable after the geography migration.
"""
import datetime
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import agentportal as AP
import db as D
import geo as GEO
import partners as PT

random.seed(41)
con = D.connect()
GEO.con = con
GEO.init_tables(con)
PT.con = con
PT.init_tables(con)
AP.con = con
AP.init_tables(con)


def region_for(country_code: str):
    row = con.execute("""SELECT r.id, r.gov_id FROM geo_districts r
        JOIN geo_governorates c ON c.id=r.gov_id
        WHERE c.code=? ORDER BY r.name_en LIMIT 1""", (country_code,)).fetchone()
    return (row["gov_id"], row["id"]) if row else (None, None)


def city_for(region_id: int):
    row = con.execute("SELECT id FROM geo_villages WHERE region_id=? ORDER BY population DESC LIMIT 1",
                      (region_id,)).fetchone()
    return row["id"] if row else None


if not con.execute("SELECT 1 FROM agents WHERE deleted=0 LIMIT 1").fetchone():
    # A global, non-country-specific partner demo set.  The familiar demo emails
    # are retained so the portal UI and documentation keep working.
    PARTNERS = [
        ("Global North America Partner", "agent", "US", "tiered", 0, 420000),
        ("Gulf Distribution Network", "distributor", "AE", "tiered", 0, 380000),
        ("European Commercial Partner", "agent", "DE", "percent", 5.0, 260000),
        ("South Asia Distribution", "distributor", "IN", "percent", 4.0, 210000),
        ("East Asia Technology Partner", "agent", "JP", "tiered", 0, 340000),
        ("Latin America Channel", "agent", "BR", "percent", 4.5, 180000),
        ("Africa Sales Representative", "rep", "ZA", "percent", 3.0, 90000),
        ("Oceania Sales Representative", "rep", "AU", "percent", 3.0, 70000),
        ("Global Tender Broker", "broker", "GB", "flat", 500, 110000),
        ("Canada Enterprise Broker", "broker", "CA", "percent", 2.0, 150000),
    ]
    aids = []
    for index, (name, partner_type, country_code, model, rate, target) in enumerate(PARTNERS):
        country_id, region_id = region_for(country_code)
        if not country_id:
            continue
        aid = con.execute("""INSERT INTO agents(code,name,type,phone,email,gov_id,district_id,
            commission_model,commission_rate,tiers,target,credit_limit,status,rating,
            joined_at,created_at,updated_at,deleted,address)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'Active',?,?,?,?,0,?)""",
            (f"AG-{1001 + index}", name, partner_type,
             f"+1-555-{1000 + index:04d}", f"agent{index}@partners.ye", country_id, region_id,
             model, rate, json.dumps(PT.DEFAULT_TIERS) if model == "tiered" else None,
             target, random.choice([0, 5000, 10000, 20000]), round(random.uniform(3.2, 4.9), 1),
             (datetime.date.today() - datetime.timedelta(days=random.randint(120, 1500))).isoformat(),
             D.now(), D.now(), country_code)).lastrowid
        aids.append((aid, country_id, region_id))
        con.execute("""INSERT INTO agent_users(agent_id,email,password,active,created_at)
            VALUES(?,?,?,?,?)""", (aid, f"agent{index}@partners.ye", AP.ahash("agent123"), 1, D.now()))
        if partner_type != "broker":
            con.execute("""INSERT INTO territories(agent_id,gov_id,district_id,exclusive,created_at)
                VALUES(?,?,?,?,?)""", (aid, country_id, None, 1, D.now()))

    # Put a small selection of demo accounts in real global locations.
    accounts = [row["id"] for row in con.execute("SELECT id FROM accounts WHERE deleted=0 ORDER BY id")]
    for account_id, (agent_id, country_id, region_id) in zip(accounts, aids * max(1, len(accounts) // max(1, len(aids)) + 1)):
        con.execute("UPDATE accounts SET gov_id=?,district_id=?,village_id=?,agent_id=? WHERE id=?",
                    (country_id, region_id, city_for(region_id), agent_id, account_id))
    con.commit()

status = GEO.world_status(con)
counts = status["counts"]
print(
    f"global geography ready: {counts['countries']} countries | "
    f"{counts['regions']} regions | {counts['cities']} cities "
    f"({status['version']})"
)
