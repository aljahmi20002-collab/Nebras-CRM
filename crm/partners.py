"""Channel partners: agents (وكلاء), distributors (موزعون), sales reps (مندوبون).

Handles the full financial relationship — commissions earned, payouts made,
inventory consigned, debts owed — i.e. "ما لهم وما عليهم" (a running statement
of account per partner).
"""
import datetime
from typing import Optional
from fastapi import Depends, HTTPException
from pydantic import BaseModel

import db as D

con = None

TYPES = {
    "agent":       {"en": "Agent", "ar": "وكيل", "icon": "🤝"},
    "distributor": {"en": "Distributor", "ar": "موزع", "icon": "🚚"},
    "rep":         {"en": "Sales Rep", "ar": "مندوب", "icon": "🧑‍💼"},
    "broker":      {"en": "Broker", "ar": "وسيط", "icon": "🔗"},
}

# Commission models
COMM_MODELS = {
    "percent":   {"en": "% of sale", "ar": "نسبة من المبيعات"},
    "tiered":    {"en": "Tiered %", "ar": "نسبة تصاعدية"},
    "flat":      {"en": "Flat per deal", "ar": "مبلغ ثابت لكل صفقة"},
    "per_unit":  {"en": "Per unit sold", "ar": "لكل وحدة مباعة"},
}

# Default tier ladder (monthly sales volume -> rate)
DEFAULT_TIERS = [
    {"min": 0,      "rate": 3.0},
    {"min": 50000,  "rate": 4.5},
    {"min": 150000, "rate": 6.0},
    {"min": 400000, "rate": 8.0},
]

TXN_KINDS = {
    "commission": {"en": "Commission earned", "ar": "عمولة مستحقة", "sign": +1},
    "bonus":      {"en": "Bonus", "ar": "مكافأة", "sign": +1},
    "adjustment": {"en": "Adjustment", "ar": "تسوية", "sign": +1},
    "payout":     {"en": "Payout", "ar": "صرف مستحقات", "sign": -1},
    "deduction":  {"en": "Deduction", "ar": "خصم", "sign": -1},
    "advance":    {"en": "Advance", "ar": "سلفة", "sign": -1},
    "penalty":    {"en": "Penalty", "ar": "غرامة", "sign": -1},
}


def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def init_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS agents(
        id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, name TEXT, type TEXT DEFAULT 'agent',
        phone TEXT, email TEXT, national_id TEXT,
        gov_id INTEGER, district_id INTEGER, village_id INTEGER, quarter_id INTEGER,
        address TEXT, user_id INTEGER,
        commission_model TEXT DEFAULT 'percent', commission_rate REAL DEFAULT 3.0,
        tiers TEXT, target REAL DEFAULT 0, credit_limit REAL DEFAULT 0,
        status TEXT DEFAULT 'Active', rating REAL DEFAULT 0,
        joined_at TEXT, created_at TEXT, updated_at TEXT, deleted INTEGER DEFAULT 0,
        notes TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS agent_txn(
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id INTEGER, kind TEXT,
        amount REAL, currency TEXT DEFAULT 'USD', ref_module TEXT, ref_id INTEGER,
        note TEXT, status TEXT DEFAULT 'posted', period TEXT,
        created_by INTEGER, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS agent_stock(
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id INTEGER, product_id INTEGER,
        qty REAL DEFAULT 0, consigned REAL DEFAULT 0, sold REAL DEFAULT 0,
        updated_at TEXT)""")
    for sql in [
        "CREATE INDEX IF NOT EXISTS ix_txn_agent ON agent_txn(agent_id)",
        "CREATE INDEX IF NOT EXISTS ix_stock_agent ON agent_stock(agent_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_commission_deal ON agent_txn(ref_module,ref_id) "
        "WHERE kind='commission' AND ref_module='deals'",
    ]:
        c.execute(sql)
    # link deals/accounts to the partner who owns them
    # Check first instead of relying on a caught duplicate-ALTER error. PostgreSQL
    # marks the transaction failed after any DDL error, even if Python catches it.
    known_columns = {table: D.table_columns(c, table) for table in ("deals", "accounts")}
    for tbl, col in (("deals", "agent_id"), ("accounts", "agent_id"),
                     ("accounts", "gov_id"), ("accounts", "district_id"),
                     ("accounts", "village_id"), ("accounts", "quarter_id"),
                     ("accounts", "street_id")):
        if col not in known_columns[tbl]:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT")
            known_columns[tbl].add(col)
    c.commit()


def tier_rate(agent, volume):
    import json
    tiers = DEFAULT_TIERS
    if agent.get("tiers"):
        try:
            tiers = json.loads(agent["tiers"])
        except Exception:
            pass
    rate = tiers[0]["rate"]
    for t in sorted(tiers, key=lambda x: x["min"]):
        if volume >= t["min"]:
            rate = t["rate"]
    return rate


def compute_commission(agent, amount, volume=0, units=0):
    m = agent.get("commission_model") or "percent"
    if m == "percent":
        return round(amount * _f(agent.get("commission_rate")) / 100, 2), _f(agent.get("commission_rate"))
    if m == "tiered":
        r = tier_rate(agent, volume)
        return round(amount * r / 100, 2), r
    if m == "flat":
        return round(_f(agent.get("commission_rate")), 2), None
    if m == "per_unit":
        return round(_f(agent.get("commission_rate")) * (units or 1), 2), None
    return 0.0, None


def balance(agent_id):
    """ما له وما عليه — running statement."""
    rows = con.execute("SELECT kind, SUM(amount) s FROM agent_txn WHERE agent_id=? GROUP BY kind",
                       (agent_id,)).fetchall()
    credit = debit = 0.0
    detail = {}
    for r in rows:
        k = r["kind"]; amt = _f(r["s"])
        detail[k] = amt
        if TXN_KINDS.get(k, {}).get("sign", 1) > 0:
            credit += amt
        else:
            debit += amt
    return {"credit": round(credit, 2), "debit": round(debit, 2),
            "balance": round(credit - debit, 2), "detail": detail}


def register(app, current_user, require):

    @app.get("/api/partners/meta")
    def meta(user=Depends(current_user)):
        return {"types": TYPES, "models": COMM_MODELS, "txn_kinds": TXN_KINDS,
                "default_tiers": DEFAULT_TIERS}

    @app.get("/api/partners")
    def list_partners(q: str = "", type: str = "", gov_id: int = 0, status: str = "",
                      user=Depends(current_user)):
        require(user, "admin", "manager")
        w, p = ["a.deleted=0"], []
        if q: w.append("(a.name LIKE ? OR a.code LIKE ? OR a.phone LIKE ?)"); p += [f"%{q}%"]*3
        if type: w.append("a.type=?"); p.append(type)
        if gov_id: w.append("a.gov_id=?"); p.append(gov_id)
        if status: w.append("a.status=?"); p.append(status)
        rows = [dict(r) for r in con.execute(f"""
            SELECT a.*, g.name_ar gov_ar, g.name_en gov_en, d.name_ar dis_ar, d.name_en dis_en
            FROM agents a
            LEFT JOIN geo_governorates g ON g.id=a.gov_id
            LEFT JOIN geo_districts d ON d.id=a.district_id
            WHERE {' AND '.join(w)} ORDER BY a.id DESC""", p)]
        for r in rows:
            b = balance(r["id"])
            r["balance"] = b["balance"]; r["credit"] = b["credit"]; r["debit"] = b["debit"]
            r["sales"] = _f(con.execute("""SELECT SUM(amount) FROM deals
                WHERE deleted=0 AND stage='Closed Won' AND CAST(agent_id AS INTEGER)=?""",
                (r["id"],)).fetchone()[0])
        return rows

    @app.get("/api/partners/{aid}")
    def get_partner(aid: int, user=Depends(current_user)):
        require(user, "admin", "manager")
        r = con.execute("""SELECT a.*, g.name_ar gov_ar, d.name_ar dis_ar
            FROM agents a LEFT JOIN geo_governorates g ON g.id=a.gov_id
            LEFT JOIN geo_districts d ON d.id=a.district_id
            WHERE a.id=? AND a.deleted=0""", (aid,)).fetchone()
        if not r: raise HTTPException(404, "Partner not found")
        d = dict(r)
        d["balance"] = balance(aid)
        d["txns"] = [dict(x) for x in con.execute(
            "SELECT * FROM agent_txn WHERE agent_id=? ORDER BY id DESC LIMIT 100", (aid,))]
        d["territories"] = [dict(x) for x in con.execute("""
            SELECT t.*, g.name_ar gov_ar, dd.name_ar dis_ar FROM territories t
            LEFT JOIN geo_governorates g ON g.id=t.gov_id
            LEFT JOIN geo_districts dd ON dd.id=t.district_id
            WHERE t.agent_id=?""", (aid,))]
        d["deals"] = [dict(x) for x in con.execute("""
            SELECT id,name,amount,stage,closing_date FROM deals
            WHERE deleted=0 AND CAST(agent_id AS INTEGER)=? ORDER BY id DESC LIMIT 20""", (aid,))]
        d["accounts"] = con.execute("""SELECT COUNT(*) n FROM accounts
            WHERE deleted=0 AND CAST(agent_id AS INTEGER)=?""", (aid,)).fetchone()["n"]
        d["stock"] = [dict(x) for x in con.execute("""
            SELECT s.*, p.name product FROM agent_stock s
            LEFT JOIN products p ON p.id=s.product_id WHERE s.agent_id=?""", (aid,))]
        sales = _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0
            AND stage='Closed Won' AND CAST(agent_id AS INTEGER)=?""", (aid,)).fetchone()[0])
        d["sales"] = sales
        d["achievement"] = round(sales / _f(d["target"]) * 100, 1) if _f(d["target"]) else None
        d["current_rate"] = tier_rate(d, sales) if d["commission_model"] == "tiered" else _f(d["commission_rate"])
        return d

    class Partner(BaseModel):
        name: str
        type: str = "agent"
        code: str = ""
        phone: str = ""
        email: str = ""
        national_id: str = ""
        gov_id: int = 0
        district_id: int = 0
        village_id: int = 0
        quarter_id: int = 0
        address: str = ""
        commission_model: str = "percent"
        commission_rate: float = 3.0
        tiers: str = ""
        target: float = 0
        credit_limit: float = 0
        status: str = "Active"
        notes: str = ""

    @app.post("/api/partners")
    def create_partner(b: Partner, user=Depends(current_user)):
        require(user, "admin", "manager")
        import db as D
        if not b.name.strip() or len(b.name) > 200:
            raise HTTPException(400, "Name required")
        if b.type not in TYPES or b.commission_model not in COMM_MODELS or b.status not in {"Active", "Suspended", "Inactive"}:
            raise HTTPException(400, "Invalid partner configuration")
        if b.commission_rate < 0 or b.target < 0 or b.credit_limit < 0:
            raise HTTPException(400, "Financial values cannot be negative")
        if b.tiers:
            try:
                import json
                tiers = json.loads(b.tiers)
                if not isinstance(tiers, list) or not tiers:
                    raise ValueError
                for tier in tiers:
                    if not isinstance(tier, dict) or float(tier.get("min", -1)) < 0 or float(tier.get("rate", -1)) < 0:
                        raise ValueError
            except (TypeError, ValueError, json.JSONDecodeError):
                raise HTTPException(400, "Invalid commission tiers")
        code = (b.code or f"AG-{con.execute('SELECT COALESCE(MAX(id),0)+1 n FROM agents').fetchone()['n']:04d}").strip()
        if not code or len(code) > 100:
            raise HTTPException(400, "Invalid partner code")
        if con.execute("SELECT 1 FROM agents WHERE code=? AND deleted=0", (code,)).fetchone():
            raise HTTPException(400, "Partner code already exists")
        aid = con.execute("""INSERT INTO agents(code,name,type,phone,email,national_id,gov_id,
            district_id,village_id,quarter_id,address,commission_model,commission_rate,tiers,
            target,credit_limit,status,joined_at,created_at,updated_at,deleted,notes)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?)""",
            (code, b.name.strip(), b.type, b.phone, b.email, b.national_id, b.gov_id or None,
             b.district_id or None, b.village_id or None, b.quarter_id or None, b.address,
             b.commission_model, b.commission_rate, b.tiers or None, b.target, b.credit_limit,
             b.status, datetime.date.today().isoformat(), D.now(), D.now(), b.notes)).lastrowid
        D.log(con, "agents", aid, "create", {"name": b.name}, user["id"])
        con.commit(); return {"id": aid, "code": code}

    @app.put("/api/partners/{aid}")
    def update_partner(aid: int, body: dict, user=Depends(current_user)):
        require(user, "admin", "manager")
        import db as D
        cols = ["name","type","code","phone","email","national_id","gov_id","district_id",
                "village_id","quarter_id","address","commission_model","commission_rate",
                "tiers","target","credit_limit","status","notes"]
        sets, vals = [], []
        for k in cols:
            if k in body: sets.append(f"{k}=?"); vals.append(body[k])
        if sets:
            sets.append("updated_at=?"); vals.append(D.now())
            con.execute(f"UPDATE agents SET {','.join(sets)} WHERE id=?", vals + [aid])
            D.log(con, "agents", aid, "update", body, user["id"]); con.commit()
        return {"ok": True}

    @app.delete("/api/partners/{aid}")
    def del_partner(aid: int, user=Depends(current_user)):
        require(user, "admin")
        if not con.execute("SELECT 1 FROM agents WHERE id=? AND deleted=0", (aid,)).fetchone():
            raise HTTPException(404, "Partner not found")
        b = balance(aid)
        if abs(b["balance"]) > 0.01:
            raise HTTPException(400, f"Settle the balance first ({b['balance']})")
        con.execute("UPDATE agents SET deleted=1 WHERE id=?", (aid,)); con.commit()
        return {"ok": True}

    # ---------------- ledger ----------------
    class Txn(BaseModel):
        agent_id: int
        kind: str
        amount: float
        note: str = ""
        ref_module: Optional[str] = None
        ref_id: Optional[int] = None
        period: str = ""

    @app.post("/api/partners/txn")
    def add_txn(b: Txn, user=Depends(current_user)):
        require(user, "admin", "manager")
        if b.kind not in TXN_KINDS:
            raise HTTPException(400, "Unknown transaction kind")
        if b.amount <= 0:
            raise HTTPException(400, "Amount must be positive")
        partner = con.execute("SELECT * FROM agents WHERE id=? AND deleted=0", (b.agent_id,)).fetchone()
        if not partner:
            raise HTTPException(404, "Partner not found")
        if partner["status"] != "Active" and b.kind in ("commission", "bonus", "advance", "payout"):
            raise HTTPException(400, "Partner is not active")
        if b.kind in ("payout", "advance"):
            bal = balance(b.agent_id)
            if b.kind == "payout" and b.amount > bal["balance"] + 0.01:
                raise HTTPException(400, f"Payout exceeds what is owed ({bal['balance']})")
            if b.kind == "advance":
                lim = _f(con.execute("SELECT credit_limit FROM agents WHERE id=?",
                                     (b.agent_id,)).fetchone()["credit_limit"])
                outstanding = max(0.0, -bal["balance"]) + b.amount
                if lim and outstanding > lim:
                    raise HTTPException(400, f"Advance exceeds credit limit ({lim})")
        import db as D
        tid = con.execute("""INSERT INTO agent_txn(agent_id,kind,amount,ref_module,ref_id,note,
            period,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?)""",
            (b.agent_id, b.kind, b.amount, b.ref_module, b.ref_id, b.note,
             b.period or datetime.date.today().strftime("%Y-%m"), user["id"], D.now())).lastrowid
        D.log(con, "agents", b.agent_id, "txn", {"kind": b.kind, "amount": b.amount}, user["id"])
        con.commit()
        return {"id": tid, "balance": balance(b.agent_id)}

    @app.post("/api/partners/accrue")
    def accrue(period: str = "", user=Depends(current_user)):
        """Post commission for every won deal that has an agent and isn't accrued yet."""
        require(user, "admin", "manager")
        import db as D
        period = period or datetime.date.today().strftime("%Y-%m")
        done = {r["ref_id"] for r in con.execute(
            "SELECT ref_id FROM agent_txn WHERE kind='commission' AND ref_module='deals'")}
        posted, total = 0, 0.0
        for d in con.execute("""SELECT id,name,amount,agent_id,closing_date FROM deals
                                WHERE deleted=0 AND stage='Closed Won'
                                AND agent_id IS NOT NULL AND agent_id!=''"""):
            if d["id"] in done: continue
            ag = con.execute("SELECT * FROM agents WHERE id=CAST(? AS INTEGER) AND deleted=0",
                             (d["agent_id"],)).fetchone()
            if not ag: continue
            ag = dict(ag)
            volume = _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0
                AND stage='Closed Won' AND CAST(agent_id AS INTEGER)=?""",
                (ag["id"],)).fetchone()[0])
            amt, rate = compute_commission(ag, _f(d["amount"]), volume)
            if amt <= 0: continue
            con.execute("""INSERT INTO agent_txn(agent_id,kind,amount,ref_module,ref_id,note,
                period,created_by,created_at) VALUES(?,'commission',?,'deals',?,?,?,?,?)""",
                (ag["id"], amt, d["id"],
                 f'{d["name"]} @ {rate}%' if rate else d["name"],
                 (d["closing_date"] or "")[:7] or period, user["id"], D.now()))
            posted += 1; total += amt
        con.commit()
        return {"posted": posted, "total": round(total, 2), "period": period}

    @app.get("/api/partners/{aid}/statement")
    def statement(aid: int, user=Depends(current_user)):
        """كشف حساب — running balance, oldest first."""
        require(user, "admin", "manager")
        rows = [dict(r) for r in con.execute(
            "SELECT * FROM agent_txn WHERE agent_id=? ORDER BY id", (aid,))]
        run = 0.0
        for r in rows:
            sign = TXN_KINDS.get(r["kind"], {}).get("sign", 1)
            r["signed"] = round(sign * _f(r["amount"]), 2)
            run += r["signed"]
            r["running"] = round(run, 2)
            r["kind_ar"] = TXN_KINDS.get(r["kind"], {}).get("ar", r["kind"])
            r["kind_en"] = TXN_KINDS.get(r["kind"], {}).get("en", r["kind"])
        rows.reverse()
        return {"rows": rows, "balance": balance(aid)}

    @app.get("/api/partners/analytics/summary")
    def summary(user=Depends(current_user)):
        require(user, "admin", "manager")
        g = lambda s: _f(con.execute(s).fetchone()[0])
        by_type = [dict(r) for r in con.execute("""
            SELECT type k, COUNT(*) n FROM agents WHERE deleted=0 GROUP BY type""")]
        top = []
        for r in con.execute("SELECT id,name,type,target FROM agents WHERE deleted=0"):
            sales = _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0
                AND stage='Closed Won' AND CAST(agent_id AS INTEGER)=?""", (r["id"],)).fetchone()[0])
            b = balance(r["id"])
            top.append({"id": r["id"], "k": r["name"], "type": r["type"], "v": sales,
                        "target": _f(r["target"]), "balance": b["balance"],
                        "achievement": round(sales / _f(r["target"]) * 100, 1) if _f(r["target"]) else None})
        top.sort(key=lambda x: -x["v"])
        by_country = [dict(r) for r in con.execute("""
            SELECT COALESCE(g.name_ar,'—') k, COUNT(a.id) n FROM agents a
            LEFT JOIN geo_governorates g ON g.id=a.gov_id
            WHERE a.deleted=0 GROUP BY 1 ORDER BY n DESC""")]
        return {
            "kpi": {
                "partners": int(g("SELECT COUNT(*) FROM agents WHERE deleted=0")),
                "active": int(g("SELECT COUNT(*) FROM agents WHERE deleted=0 AND status='Active'")),
                "commission_earned": g("SELECT SUM(amount) FROM agent_txn WHERE kind IN ('commission','bonus')"),
                "paid_out": g("SELECT SUM(amount) FROM agent_txn WHERE kind='payout'"),
                "owed": g("""SELECT SUM(CASE WHEN kind IN ('commission','bonus','adjustment')
                             THEN amount ELSE -amount END) FROM agent_txn"""),
                "advances": g("SELECT SUM(amount) FROM agent_txn WHERE kind='advance'"),
                "partner_sales": g("""SELECT SUM(amount) FROM deals WHERE deleted=0
                                      AND stage='Closed Won' AND agent_id IS NOT NULL AND agent_id!=''"""),
            },
            "by_type": by_type, "leaderboard": top[:15],
            "by_country": by_country, "by_governorate": by_country,
        }
