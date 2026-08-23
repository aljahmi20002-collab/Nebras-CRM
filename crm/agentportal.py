"""Partner Portal — self-service for agents, distributors and sales reps.

A third, independent auth realm (separate from staff CRM and customer portal).
A partner user is bound to one `agents` row and every query is hard-scoped to it,
so a partner can never see another partner's customers, commissions or balances.
"""
import os, datetime, secrets
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

import db as D
import mailer as M
import partners as PT
from security import (
    LoginThrottle, client_ip, configured_secret, hash_password, make_token as sign_token,
    parse_token as parse_signed_token, password_error, verify_password,
)

LEGACY_ASECRET = "arena-crm-agent-portal-secret"
ASECRET = configured_secret("CRM_AGENT_PORTAL_SECRET", LEGACY_ASECRET, "NebrasCRM partner portal authentication")
try:
    AGENT_TOKEN_TTL = max(300, int(os.environ.get("CRM_AGENT_TOKEN_TTL_SECONDS", "28800")))
except ValueError:
    AGENT_TOKEN_TTL = 28800
AGENT_LOGIN_THROTTLE = LoginThrottle()
aportal = APIRouter()
HERE = os.path.dirname(os.path.abspath(__file__))
con = None


def init_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS agent_users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id INTEGER UNIQUE,
        email TEXT UNIQUE, password TEXT, active INTEGER DEFAULT 1,
        last_login TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS agent_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id INTEGER, kind TEXT,
        amount REAL, subject TEXT, body TEXT, status TEXT DEFAULT 'pending',
        decided_by INTEGER, decided_at TEXT, reply TEXT, created_at TEXT)""")
    c.commit()


def ahash(pw: str) -> str:
    return hash_password(pw)


def _verify_password(pw: str, stored: str):
    return verify_password(pw, stored, legacy_secrets=(ASECRET, LEGACY_ASECRET))


def atoken(uid: int) -> str:
    return sign_token(uid, ASECRET, AGENT_TOKEN_TTL)


def parse_atoken(tok: str):
    return parse_signed_token(tok, ASECRET)


def agent_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    uid = parse_atoken(authorization[7:])
    if not uid:
        raise HTTPException(401, "Invalid token")
    r = con.execute("""SELECT au.*, a.name aname, a.code, a.type, a.commission_model,
                              a.commission_rate, a.tiers, a.target, a.credit_limit, a.status,
                              a.phone, a.joined_at, a.gov_id, a.district_id,
                              g.name_ar gov_ar, d.name_ar dis_ar,
               g.name_ar country_ar, d.name_ar region_ar,
                              g.name_ar country_ar, g.name_en country_en,
                              d.name_ar region_ar, d.name_en region_en
                       FROM agent_users au JOIN agents a ON a.id=au.agent_id
                       LEFT JOIN geo_governorates g ON g.id=a.gov_id
                       LEFT JOIN geo_districts d ON d.id=a.district_id
                       WHERE au.id=? AND au.active=1 AND a.deleted=0""", (uid,)).fetchone()
    if not r:
        raise HTTPException(401, "Portal access disabled")
    d = dict(r)
    if d["status"] != "Active":
        raise HTTPException(403, "Your partner account is suspended")
    return d


class ALogin(BaseModel):
    email: str
    password: str


@aportal.post("/agent/api/login")
def alogin(b: ALogin, request: Request):
    email = b.email.strip().lower()
    if not email or len(email) > 320:
        raise HTTPException(400, "Invalid email")
    key = f"{client_ip(request)}|{email}"
    wait = AGENT_LOGIN_THROTTLE.wait_minutes(key)
    if wait:
        raise HTTPException(429, f"Too many failed attempts. Try again in {wait} minutes.")
    r = con.execute("SELECT * FROM agent_users WHERE lower(email)=lower(?) AND active=1",
                    (email,)).fetchone()
    valid, upgrade = _verify_password(b.password, r["password"] if r else "")
    if not r or not valid:
        AGENT_LOGIN_THROTTLE.fail(key)
        raise HTTPException(401, "Invalid credentials")
    if upgrade:
        con.execute("UPDATE agent_users SET password=? WHERE id=?", (ahash(b.password), r["id"]))
    AGENT_LOGIN_THROTTLE.clear(key)
    con.execute("UPDATE agent_users SET last_login=? WHERE id=?", (D.now(), r["id"]))
    con.commit()
    a = con.execute("SELECT name,type FROM agents WHERE id=?", (r["agent_id"],)).fetchone()
    return {"token": atoken(r["id"]),
            "user": {"email": r["email"], "name": a["name"] if a else r["email"],
                     "type": a["type"] if a else "agent"}}


@aportal.get("/agent/api/me")
def ame(u=Depends(agent_user)):
    aid = u["agent_id"]
    sales = PT._f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0
        AND stage='Closed Won' AND CAST(agent_id AS INTEGER)=?""", (aid,)).fetchone()[0])
    return {"email": u["email"], "name": u["aname"], "code": u["code"], "type": u["type"],
            "phone": u["phone"], "country": u["country_ar"], "region": u["region_ar"],
            # Deprecated aliases retained for older portal clients.
            "gov": u["country_ar"], "district": u["region_ar"],
            "target": u["target"], "sales": sales, "joined_at": u["joined_at"],
            "commission_model": u["commission_model"],
            "rate": PT.tier_rate(u, sales) if u["commission_model"] == "tiered" else u["commission_rate"]}


@aportal.get("/agent/api/summary")
def asummary(u=Depends(agent_user)):
    aid = u["agent_id"]
    g = lambda s, p=(): PT._f(con.execute(s, p).fetchone()[0])
    sales = g("""SELECT SUM(amount) FROM deals WHERE deleted=0 AND stage='Closed Won'
                 AND CAST(agent_id AS INTEGER)=?""", (aid,))
    bal = PT.balance(aid)
    pipeline = g("""SELECT SUM(amount) FROM deals WHERE deleted=0
                    AND stage NOT IN ('Closed Won','Closed Lost')
                    AND CAST(agent_id AS INTEGER)=?""", (aid,))
    month = datetime.date.today().strftime("%Y-%m")
    monthly = [dict(r) for r in con.execute("""
        SELECT substr(closing_date,1,7) k, SUM(amount) v, COUNT(*) n FROM deals
        WHERE deleted=0 AND stage='Closed Won' AND CAST(agent_id AS INTEGER)=?
        AND closing_date IS NOT NULL GROUP BY k ORDER BY k DESC LIMIT 12""", (aid,))]
    monthly.reverse()
    import loyalty as LOY
    _r, pts = LOY.compute("partner", aid)
    tier = LOY.tier_for(pts)
    # anonymised rank among peers — motivating without exposing others' figures
    peers = []
    for x in con.execute("SELECT id FROM agents WHERE deleted=0 AND status='Active'"):
        peers.append((x["id"], PT._f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0
            AND stage='Closed Won' AND CAST(agent_id AS INTEGER)=?""", (x["id"],)).fetchone()[0])))
    peers.sort(key=lambda z: -z[1])
    rank = next((i + 1 for i, z in enumerate(peers) if z[0] == aid), None)
    return {
        "sales": sales, "pipeline": pipeline,
        "balance": bal["balance"], "credit": bal["credit"], "debit": bal["debit"],
        "target": PT._f(u["target"]),
        "achievement": round(sales / PT._f(u["target"]) * 100, 1) if PT._f(u["target"]) else None,
        "commission_month": g("""SELECT SUM(amount) FROM agent_txn WHERE agent_id=?
                                 AND kind='commission' AND period=?""", (aid, month)),
        "customers": int(g("""SELECT COUNT(*) FROM accounts WHERE deleted=0
                              AND CAST(agent_id AS INTEGER)=?""", (aid,))),
        "open_deals": int(g("""SELECT COUNT(*) FROM deals WHERE deleted=0
                               AND stage NOT IN ('Closed Won','Closed Lost')
                               AND CAST(agent_id AS INTEGER)=?""", (aid,))),
        "monthly": monthly, "loyalty": {"points": pts, "tier": tier},
        "rank": rank, "peer_count": len(peers),
    }


@aportal.get("/agent/api/customers")
def acustomers(u=Depends(agent_user)):
    return [dict(r) for r in con.execute("""
        SELECT a.id,a.name,a.industry,a.phone,a.segment,a.list_tag,
               g.name_ar gov_ar, d.name_ar dis_ar,
               g.name_ar country_ar, d.name_ar region_ar,
               (SELECT COALESCE(SUM(dl.amount),0) FROM deals dl WHERE dl.deleted=0
                 AND dl.stage='Closed Won' AND CAST(dl.account_id AS INTEGER)=a.id) revenue,
               (SELECT COALESCE(SUM(COALESCE(i.amount,0)-COALESCE(i.paid_amount,0)),0)
                 FROM invoices i WHERE i.deleted=0 AND CAST(i.account_id AS INTEGER)=a.id
                 AND i.status NOT IN ('Paid','Cancelled')) outstanding
        FROM accounts a
        LEFT JOIN geo_governorates g ON g.id=a.gov_id
        LEFT JOIN geo_districts d ON d.id=a.district_id
        WHERE a.deleted=0 AND CAST(a.agent_id AS INTEGER)=? ORDER BY revenue DESC""",
        (u["agent_id"],))]


@aportal.get("/agent/api/deals")
def adeals(u=Depends(agent_user)):
    return [dict(r) for r in con.execute("""
        SELECT d.id,d.name,d.amount,d.stage,d.probability,d.closing_date,d.next_step,
               a.name account
        FROM deals d LEFT JOIN accounts a ON a.id=CAST(d.account_id AS INTEGER)
        WHERE d.deleted=0 AND CAST(d.agent_id AS INTEGER)=? ORDER BY d.id DESC""",
        (u["agent_id"],))]


class ALead(BaseModel):
    name: str
    company: str = ""
    phone: str = ""
    email: str = ""
    city: str = ""
    description: str = ""
    estimated_value: float = 0


@aportal.post("/agent/api/leads")
def anew_lead(b: ALead, u=Depends(agent_user)):
    """Partner submits a lead from the field."""
    if not b.name.strip():
        raise HTTPException(400, "Name is required")
    ts = D.now()
    lid = con.execute("""INSERT INTO leads(created_at,updated_at,created_by,owner_id,deleted,
        name,company,phone,email,city,status,source,rating,annual_revenue,description)
        VALUES(?,?,NULL,NULL,0,?,?,?,?,?,'New','Partner','Warm',?,?)""",
        (ts, ts, b.name.strip(), b.company, b.phone, b.email, b.city,
         b.estimated_value, f'{b.description}\n\n— عبر الوكيل: {u["aname"]}')).lastrowid
    D.log(con, "leads", lid, "partner_submit", {"agent": u["aname"]}, None)
    for m in con.execute("SELECT id,email FROM users WHERE role IN ('admin','manager') AND active=1"):
        con.execute("INSERT INTO notifications(user_id,title,body,read,created_at) VALUES(?,?,?,0,?)",
                    (m["id"], "🌱 عميل محتمل من وكيل", f'{u["aname"]}: {b.name}', ts))
    con.commit()
    return {"id": lid}


@aportal.get("/agent/api/leads")
def aleads(u=Depends(agent_user)):
    return [dict(r) for r in con.execute("""
        SELECT id,name,company,phone,status,rating,created_at FROM leads
        WHERE deleted=0 AND description LIKE ? ORDER BY id DESC LIMIT 100""",
        (f'%عبر الوكيل: {u["aname"]}%',))]


@aportal.get("/agent/api/statement")
def astatement(u=Depends(agent_user)):
    aid = u["agent_id"]
    rows = [dict(r) for r in con.execute(
        "SELECT * FROM agent_txn WHERE agent_id=? ORDER BY id", (aid,))]
    run = 0.0
    for r in rows:
        sign = PT.TXN_KINDS.get(r["kind"], {}).get("sign", 1)
        r["signed"] = round(sign * PT._f(r["amount"]), 2)
        run += r["signed"]
        r["running"] = round(run, 2)
        r["kind_ar"] = PT.TXN_KINDS.get(r["kind"], {}).get("ar", r["kind"])
        r["kind_en"] = PT.TXN_KINDS.get(r["kind"], {}).get("en", r["kind"])
    rows.reverse()
    return {"rows": rows, "balance": PT.balance(aid)}


@aportal.get("/agent/api/stock")
def astock(u=Depends(agent_user)):
    return [dict(r) for r in con.execute("""
        SELECT s.*, p.name product, p.unit_price, p.code FROM agent_stock s
        LEFT JOIN products p ON p.id=s.product_id WHERE s.agent_id=?""", (u["agent_id"],))]


@aportal.get("/agent/api/territories")
def aterritories(u=Depends(agent_user)):
    return [dict(r) for r in con.execute("""
        SELECT t.*, g.name_ar gov_ar, g.name_en gov_en, d.name_ar dis_ar,
               g.name_ar country_ar, g.name_en country_en, d.name_ar region_ar, d.name_en region_en
        FROM territories t
        LEFT JOIN geo_governorates g ON g.id=t.gov_id
        LEFT JOIN geo_districts d ON d.id=t.district_id
        WHERE t.agent_id=?""", (u["agent_id"],))]


@aportal.get("/agent/api/loyalty")
def aloyalty(u=Depends(agent_user)):
    import loyalty as LOY
    aid = u["agent_id"]
    rows, total = LOY.compute("partner", aid)
    t = LOY.tier_for(total)
    nxt = None
    for x in reversed(LOY.TIERS):
        if x["min"] > total:
            nxt = {"tier": x, "gap": round(x["min"] - total, 1)}
            break
    red = [dict(r) for r in con.execute("""SELECT * FROM loyalty_redemptions
        WHERE member_type='partner' AND member_id=? ORDER BY id DESC""", (aid,))]
    spent = sum(PT._f(r["points"]) for r in red if r["status"] == "approved")
    return {"points": total, "available": round(total - spent, 1), "tier": t, "next": nxt,
            "breakdown": rows, "redemptions": red, "tiers": LOY.TIERS, "rules": LOY.RULES}


# ---------------- requests (payout / stock / support) ----------------
class ARequest(BaseModel):
    kind: str            # payout | stock | support
    amount: float = 0
    subject: str = ""
    body: str = ""


REQ_KINDS = {"payout": "طلب صرف مستحقات", "stock": "طلب بضاعة", "support": "طلب دعم"}


@aportal.post("/agent/api/requests")
def anew_request(b: ARequest, u=Depends(agent_user)):
    if b.kind not in REQ_KINDS:
        raise HTTPException(400, "Unknown request type")
    aid = u["agent_id"]
    if b.kind == "payout":
        bal = PT.balance(aid)["balance"]
        if b.amount <= 0:
            raise HTTPException(400, "Enter an amount")
        if b.amount > bal + 0.01:
            raise HTTPException(400, f"لا يمكن طلب أكثر من رصيدك المستحق ({bal:,.2f})")
    ts = D.now()
    rid = con.execute("""INSERT INTO agent_requests(agent_id,kind,amount,subject,body,status,created_at)
        VALUES(?,?,?,?,?,'pending',?)""",
        (aid, b.kind, b.amount, b.subject or REQ_KINDS[b.kind], b.body, ts)).lastrowid
    for m in con.execute("SELECT id,email FROM users WHERE role IN ('admin','manager') AND active=1"):
        con.execute("INSERT INTO notifications(user_id,title,body,read,created_at) VALUES(?,?,?,0,?)",
                    (m["id"], f"📨 {REQ_KINDS[b.kind]}",
                     f'{u["aname"]}: {b.amount:,.0f}' if b.amount else u["aname"], ts))
    con.commit()
    return {"id": rid}


@aportal.get("/agent/api/requests")
def arequests(u=Depends(agent_user)):
    return [dict(r) for r in con.execute(
        "SELECT * FROM agent_requests WHERE agent_id=? ORDER BY id DESC", (u["agent_id"],))]


class APw(BaseModel):
    current: str
    new: str


@aportal.post("/agent/api/password")
def apassword(b: APw, u=Depends(agent_user)):
    valid, _upgrade = _verify_password(b.current, u["password"])
    if not valid:
        raise HTTPException(400, "Current password is incorrect")
    error = password_error(b.new)
    if error:
        raise HTTPException(400, error)
    con.execute("UPDATE agent_users SET password=? WHERE id=?", (ahash(b.new), u["id"]))
    con.commit()
    return {"ok": True}


# ---------------- staff administration ----------------
def register_admin(app, current_user, require):

    @app.get("/api/agent-access")
    def list_access(user=Depends(current_user)):
        require(user, "admin", "manager")
        return [dict(r) for r in con.execute("""
            SELECT au.id,au.agent_id,au.email,au.active,au.last_login,au.created_at,
                   a.name aname, a.type FROM agent_users au
            LEFT JOIN agents a ON a.id=au.agent_id ORDER BY au.id DESC""")]

    @app.post("/api/agent-access")
    def grant(body: dict, user=Depends(current_user)):
        require(user, "admin", "manager")
        aid = int(body.get("agent_id", 0))
        a = con.execute("SELECT * FROM agents WHERE id=? AND deleted=0", (aid,)).fetchone()
        if not a:
            raise HTTPException(404, "Partner not found")
        email = (body.get("email") or a["email"] or "").strip()
        if not email:
            raise HTTPException(400, "This partner has no email")
        pw = body.get("password") or secrets.token_urlsafe(12)
        error = password_error(pw)
        if error:
            raise HTTPException(400, error)
        if con.execute("SELECT 1 FROM agent_users WHERE agent_id=? OR lower(email)=lower(?)",
                       (aid, email)).fetchone():
            raise HTTPException(400, "Portal access already exists for this partner/email")
        con.execute("INSERT INTO agent_users(agent_id,email,password,active,created_at) VALUES(?,?,?,1,?)",
                    (aid, email, ahash(pw), D.now()))
        con.commit()
        base = M.cfg("base_url", "")
        M.send(email, f'بوابة الشركاء — {a["name"]}',
               f'مرحباً {a["name"]},\n\nتم تفعيل حسابك في بوابة الشركاء.\n'
               f'الرابط: {(base.rstrip("/") + "/agent") if base else "/agent"}\n'
               f'البريد: {email}\nكلمة المرور: {pw}\n\n— {M.cfg("company_name","NebrasCRM")}',
               module="agents", record_id=aid, user_id=user["id"])
        return {"ok": True, "email": email, "password": pw}

    @app.put("/api/agent-access/{uid}")
    def upd_access(uid: int, body: dict, user=Depends(current_user)):
        require(user, "admin", "manager")
        if "active" in body:
            con.execute("UPDATE agent_users SET active=? WHERE id=?", (int(body["active"]), uid))
        if body.get("password"):
            error = password_error(body["password"])
            if error:
                raise HTTPException(400, error)
            con.execute("UPDATE agent_users SET password=? WHERE id=?",
                        (ahash(body["password"]), uid))
        con.commit()
        return {"ok": True}

    @app.delete("/api/agent-access/{uid}")
    def del_access(uid: int, user=Depends(current_user)):
        require(user, "admin")
        con.execute("DELETE FROM agent_users WHERE id=?", (uid,)); con.commit()
        return {"ok": True}

    @app.get("/api/agent-requests")
    def staff_requests(status: str = "", user=Depends(current_user)):
        require(user, "admin", "manager")
        w = "WHERE r.status=?" if status else ""
        p = [status] if status else []
        return [dict(r) for r in con.execute(f"""
            SELECT r.*, a.name aname, a.type FROM agent_requests r
            LEFT JOIN agents a ON a.id=r.agent_id {w} ORDER BY r.id DESC""", p)]

    @app.post("/api/agent-requests/{rid}/decide")
    def decide(rid: int, body: dict, user=Depends(current_user)):
        require(user, "admin", "manager")
        r = con.execute("SELECT * FROM agent_requests WHERE id=?", (rid,)).fetchone()
        if not r:
            raise HTTPException(404, "Not found")
        if r["status"] != "pending":
            raise HTTPException(400, "Already decided")
        decision = body.get("decision")
        if decision not in ("approved", "rejected"):
            raise HTTPException(400, "Bad decision")
        ts = D.now()
        if decision == "approved" and r["kind"] == "payout":
            bal = PT.balance(r["agent_id"])["balance"]
            if PT._f(r["amount"]) > bal + 0.01:
                raise HTTPException(400, f"Payout exceeds current balance ({bal:,.2f})")
            con.execute("""INSERT INTO agent_txn(agent_id,kind,amount,note,period,created_by,created_at)
                VALUES(?,'payout',?,?,?,?,?)""",
                (r["agent_id"], r["amount"], f'صرف بناءً على طلب #{rid}',
                 datetime.date.today().strftime("%Y-%m"), user["id"], ts))
        con.execute("""UPDATE agent_requests SET status=?, decided_by=?, decided_at=?, reply=?
                       WHERE id=?""", (decision, user["id"], ts, body.get("reply", ""), rid))
        D.log(con, "agents", r["agent_id"], "request_" + decision,
              {"request": rid, "amount": r["amount"]}, user["id"])
        con.commit()
        return {"ok": True}


@aportal.get("/agent")
def agent_index():
    return FileResponse(os.path.join(HERE, "static", "agent.html"))


@aportal.get("/agent.js")
def agent_js():
    return FileResponse(os.path.join(HERE, "static", "agent.js"),
                        media_type="application/javascript")
