import os, io, csv, json, datetime, hashlib, hmac, base64, sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Request, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import APIRouter

import db as D
import portal as P
import mailer as M
import payments as PAY
import intel as INTEL
import segments as SEG
import geo as GEO
import partners as PT
import loyalty as LOY
import agentportal as AP
import ai as AI
import platform_ext as PF
import reports as RPT
from schema import MODULES, GROUPS, ROLES

SECRET = os.environ.get("CRM_SECRET", "arena-crm-secret-key-change-me")

# ---- brute-force protection & rate limiting (in-memory, per-process) ----
import time as _time
from collections import defaultdict, deque
_LOGIN_FAILS = defaultdict(list)
_RATE = defaultdict(lambda: deque(maxlen=240))
LOCKOUT_TRIES, LOCKOUT_WINDOW, LOCKOUT_MINS = 5, 900, 15
RATE_LIMIT, RATE_WINDOW = 240, 60


def _client(request):
    fwd = request.headers.get("X-Forwarded-For", "")
    return (fwd.split(",")[0].strip() if fwd else
            (request.client.host if request.client else "unknown"))


def check_lockout(key):
    now = _time.time()
    fails = [t for t in _LOGIN_FAILS[key] if now - t < LOCKOUT_WINDOW]
    _LOGIN_FAILS[key] = fails
    if len(fails) >= LOCKOUT_TRIES:
        wait = int((LOCKOUT_WINDOW - (now - fails[0])) / 60) + 1
        raise HTTPException(429, f"Too many failed attempts. Try again in {wait} minutes.")


def record_fail(key):
    _LOGIN_FAILS[key].append(_time.time())


def clear_fails(key):
    _LOGIN_FAILS.pop(key, None)
app = FastAPI(title="NebrasCRM API", version="1.0")
gen = APIRouter()  # generic catch-all CRUD, mounted last
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def guard(request: Request, call_next):
    ip = _client(request)
    now = _time.time()
    q = _RATE[ip]
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT and request.url.path.startswith("/api"):
        return JSONResponse({"detail": "Rate limit exceeded. Slow down."}, status_code=429)
    q.append(now)
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "geolocation=(self), microphone=(), camera=()"
    return resp
con = D.init()
P.con = con
P.init_tables(con)
M.con = con
M.init_tables(con)
PAY.con = con
PAY.init_tables(con)
INTEL.con = con
SEG.con = con
GEO.con = con
GEO.init_tables(con)
PT.con = con
PT.init_tables(con)
LOY.con = con
LOY.init_tables(con)
AP.con = con
AP.init_tables(con)
AI.con = con
PF.con = con
PF.init_tables(con)
RPT.con = con

# ---------------- auth ----------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256((pw + SECRET).encode()).hexdigest()

def make_token(uid: int) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"uid": uid}).encode()).decode()
    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{payload}.{sig}"

def parse_token(tok: str):
    try:
        payload, sig = tok.split(".")
        if not hmac.compare_digest(sig, hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]):
            return None
        return json.loads(base64.urlsafe_b64decode(payload)).get("uid")
    except Exception:
        return None

def current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    uid = parse_token(authorization[7:])
    if not uid:
        raise HTTPException(401, "Invalid token")
    r = con.execute("SELECT * FROM users WHERE id=? AND active=1", (uid,)).fetchone()
    if not r:
        raise HTTPException(401, "User disabled")
    return dict(r)

def require(user, *roles):
    if user["role"] not in roles:
        raise HTTPException(403, "Insufficient permissions")

def can_write(user):
    if user["role"] == "readonly":
        raise HTTPException(403, "Read-only user")

class Login(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
def login(b: Login, request: Request):
    key = f"{_client(request)}|{b.email.lower()}"
    check_lockout(key)
    r = con.execute("SELECT * FROM users WHERE lower(email)=lower(?) AND active=1", (b.email,)).fetchone()
    if not r or r["password"] != hash_pw(b.password):
        record_fail(key)
        left = LOCKOUT_TRIES - len(_LOGIN_FAILS[key])
        raise HTTPException(401, f"Invalid credentials ({left} attempts left)" if left > 0
                            else "Invalid credentials")
    clear_fails(key)
    D.log(con, "users", r["id"], "login", {"ip": _client(request)}, r["id"])
    con.commit()
    u = dict(r); u.pop("password")
    return {"token": make_token(r["id"]), "user": u}

@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    user.pop("password", None)
    return user

# ---------------- metadata ----------------
@app.get("/api/meta")
def meta():
    import copy
    mods = copy.deepcopy(MODULES)
    try:
        for r in con.execute("SELECT * FROM custom_fields ORDER BY position"):
            m = r["module"]
            if m not in mods: continue
            f = {"name": r["name"], "label_en": r["label_en"] or r["label_ar"],
                 "label_ar": r["label_ar"], "type": r["type"], "custom": True}
            if r["required"]: f["required"] = True
            if r["type"] == "select":
                f["options"] = [o.strip() for o in (r["options"] or "").split(",") if o.strip()]
            mods[m]["fields"].append(f)
            if r["show_in_list"] and r["name"] not in mods[m]["list"]:
                mods[m]["list"].append(r["name"])
    except Exception:
        pass
    company = "NebrasCRM"
    try:
        r = con.execute("SELECT value FROM settings WHERE key='company_name'").fetchone()
        if r and r["value"]: company = r["value"]
    except Exception:
        pass
    return {"modules": mods, "groups": GROUPS, "roles": ROLES, "company": company}

# ---------------- generic CRUD ----------------
def custom_fields(module):
    """Custom fields defined at runtime, merged into validation everywhere."""
    try:
        rows = con.execute("SELECT * FROM custom_fields WHERE module=? ORDER BY position",
                           (module,)).fetchall()
    except Exception:
        return []
    out = []
    for r in rows:
        f = {"name": r["name"], "label_en": r["label_en"] or r["label_ar"],
             "label_ar": r["label_ar"], "type": r["type"], "custom": True}
        if r["type"] == "select":
            f["options"] = [o.strip() for o in (r["options"] or "").split(",") if o.strip()]
        out.append(f)
    return out


def all_fields(module):
    return MODULES[module]["fields"] + custom_fields(module)


def mod_or_404(m):
    if m not in MODULES:
        raise HTTPException(404, "Unknown module")
    return MODULES[m]

def enrich(rows, module):
    """Resolve lookups + owner names for display."""
    meta = MODULES[module]
    users = {u["id"]: u["name"] for u in con.execute("SELECT id,name FROM users")}
    lookups = {}
    for f in meta["fields"]:
        if f["type"] == "lookup":
            t = f["target"]
            tn = MODULES[t]["title"]
            lookups[f["name"]] = (t, {r["id"]: r[tn] for r in con.execute(f'SELECT id,"{tn}" FROM "{t}" WHERE deleted=0')})
    out = []
    for r in rows:
        d = dict(r)
        d["_display"] = {}
        d["_display"]["owner_id"] = users.get(d.get("owner_id"), "—")
        for fn, (t, mp) in lookups.items():
            v = d.get(fn)
            try:
                d["_display"][fn] = mp.get(int(v)) if v else None
            except (ValueError, TypeError):
                d["_display"][fn] = None
        out.append(d)
    return out

@gen.get("/api/{module}")
def list_records(module: str, q: str = "", sort: str = "id", dir: str = "desc",
                 page: int = 1, per_page: int = 25, filters: str = "", mine: int = 0,
                 user=Depends(current_user)):
    meta = mod_or_404(module)
    flds = all_fields(module)
    cols = [f["name"] for f in flds]
    where, params = ["deleted=0"], []
    if q:
        searchable = [f["name"] for f in flds if f["type"] in ("text", "email", "phone", "textarea")]
        if searchable:
            where.append("(" + " OR ".join(f'"{c}" LIKE ?' for c in searchable) + ")")
            params += [f"%{q}%"] * len(searchable)
    if mine:
        where.append("owner_id=?"); params.append(user["id"])
    if filters:
        try:
            for f in json.loads(filters):
                if f["field"] in cols and f.get("value") not in (None, ""):
                    op = f.get("op", "eq")
                    if op == "eq": where.append(f'"{f["field"]}"=?'); params.append(f["value"])
                    elif op == "ne": where.append(f'"{f["field"]}"!=?'); params.append(f["value"])
                    elif op == "contains": where.append(f'"{f["field"]}" LIKE ?'); params.append(f'%{f["value"]}%')
                    elif op == "gt": where.append(f'"{f["field"]}">?'); params.append(f["value"])
                    elif op == "lt": where.append(f'"{f["field"]}"<?'); params.append(f["value"])
        except Exception:
            pass
    # Market intelligence is shared org-wide knowledge — never scoped per rep.
    SHARED = {"competitors", "competitor_products", "market_research", "products"}
    if user["role"] == "agent" and module not in SHARED:
        where.append("(owner_id=? OR owner_id IS NULL)"); params.append(user["id"])
    w = " AND ".join(where)
    sort = sort if sort in cols + ["id", "created_at", "updated_at"] else "id"
    dir = "DESC" if dir.lower() == "desc" else "ASC"
    total = con.execute(f'SELECT COUNT(*) c FROM "{module}" WHERE {w}', params).fetchone()["c"]
    per_page = min(per_page, 200)
    rows = con.execute(
        f'SELECT * FROM "{module}" WHERE {w} ORDER BY "{sort}" {dir} LIMIT ? OFFSET ?',
        params + [per_page, (page - 1) * per_page]).fetchall()
    return {"data": enrich(rows, module), "total": total, "page": page, "per_page": per_page}

@gen.get("/api/{module}/{rid}")
def get_record(module: str, rid: int, user=Depends(current_user)):
    mod_or_404(module)
    r = con.execute(f'SELECT * FROM "{module}" WHERE id=? AND deleted=0', (rid,)).fetchone()
    if not r:
        raise HTTPException(404, "Not found")
    d = enrich([r], module)[0]
    d["_notes"] = [dict(x) for x in con.execute(
        "SELECT n.*,u.name uname FROM notes n LEFT JOIN users u ON u.id=n.user_id "
        "WHERE module=? AND record_id=? ORDER BY n.id DESC", (module, rid))]
    d["_audit"] = [dict(x) for x in con.execute(
        "SELECT a.*,u.name uname FROM audit a LEFT JOIN users u ON u.id=a.user_id "
        "WHERE module=? AND record_id=? ORDER BY a.id DESC LIMIT 50", (module, rid))]
    if MODULES[module].get("line_items"):
        d["_items"] = [dict(x) for x in con.execute(
            "SELECT * FROM line_items WHERE module=? AND record_id=?", (module, rid))]
    return d

def run_workflows(module, rid, data, uid):
    fired = []
    for wf in con.execute("SELECT * FROM workflows WHERE module=? AND active=1", (module,)):
        val = str(data.get(wf["field"], "") or "")
        target = str(wf["value"] or "")
        ok = ((wf["operator"] == "eq" and val == target) or
              (wf["operator"] == "ne" and val != target) or
              (wf["operator"] == "contains" and target in val) or
              (wf["operator"] == "gt" and _num(val) > _num(target)) or
              (wf["operator"] == "lt" and _num(val) < _num(target)))
        if not ok:
            continue
        con.execute("UPDATE workflows SET runs=runs+1 WHERE id=?", (wf["id"],))
        if wf["action"] == "notify":
            con.execute("INSERT INTO notifications(user_id,title,body,read,created_at) VALUES(?,?,?,0,?)",
                        (uid, wf["name"], wf["action_value"] or f"{module}#{rid}", D.now()))
        elif wf["action"] == "create_task":
            con.execute("""INSERT INTO activities(created_at,updated_at,created_by,owner_id,deleted,
                subject,type,status,priority,related_to) VALUES(?,?,?,?,0,?,?,?,?,?)""",
                (D.now(), D.now(), uid, uid, wf["action_value"] or wf["name"],
                 "Task", "Not Started", "High", f"{module}#{rid}"))
        elif wf["action"] == "send_email" and wf["action_value"]:
            # action_value = "template_code" ; recipient resolved from record email/contact
            to = data.get("email")
            if not to and data.get("contact_id"):
                c = con.execute("SELECT email,name FROM contacts WHERE id=CAST(? AS INTEGER)",
                                (data.get("contact_id"),)).fetchone()
                to = c["email"] if c else None
            if not to and data.get("account_id"):
                c = con.execute("""SELECT email FROM contacts WHERE deleted=0
                    AND CAST(account_id AS INTEGER)=CAST(? AS INTEGER) AND email IS NOT NULL LIMIT 1""",
                    (data.get("account_id"),)).fetchone()
                to = c["email"] if c else None
            if to:
                M.send_template(wf["action_value"], to, {
                    "name": data.get("name") or data.get("subject") or "",
                    "subject": data.get("subject") or data.get("name") or "",
                    "amount": f'{float(data.get("amount") or 0):,.2f}',
                    "valid_until": data.get("valid_until") or "",
                    "due_date": data.get("due_date") or "",
                    "pay_link": "", "owner": "NebrasCRM"},
                    module=module, record_id=rid, user_id=uid)
        elif wf["action"] == "set_field" and wf["action_value"] and ":" in wf["action_value"]:
            fn, fv = wf["action_value"].split(":", 1)
            cols = [f["name"] for f in MODULES[module]["fields"]]
            if fn in cols:
                con.execute(f'UPDATE "{module}" SET "{fn}"=? WHERE id=?', (fv, rid))
        fired.append(wf["name"])
    con.commit()
    return fired

def _num(v):
    try: return float(v)
    except Exception: return 0.0

def clean(module, body):
    cols = {f["name"]: f for f in all_fields(module)}
    out = {}
    for k, v in body.items():
        if k in cols:
            if cols[k]["type"] in ("number", "currency"):
                v = _num(v) if v not in ("", None) else None
            out[k] = v
    return out

@gen.post("/api/{module}")
def create_record(module: str, body: dict, user=Depends(current_user)):
    meta = mod_or_404(module); can_write(user)
    data = clean(module, body)
    for f in meta["fields"]:
        if f.get("required") and not data.get(f["name"]):
            raise HTTPException(400, f'Field required: {f["label_en"]}')
        if f.get("default") is not None and data.get(f["name"]) in (None, ""):
            data[f["name"]] = f["default"]
    if module == "opportunities":
        data["weighted_value"] = round(_num(data.get("value")) * _num(data.get("probability") or 0) / 100, 2)
        if data.get("outcome") in ("Won", "Lost") and not data.get("actual_close"):
            data["actual_close"] = datetime.date.today().isoformat()
    data.setdefault("owner_id", user["id"])
    data.update(created_at=D.now(), updated_at=D.now(), created_by=user["id"], deleted=0)
    keys = list(data)
    cur = con.execute(f'INSERT INTO "{module}" ({",".join(chr(34)+k+chr(34) for k in keys)}) '
                      f'VALUES ({",".join("?"*len(keys))})', [data[k] for k in keys])
    rid = cur.lastrowid
    D.log(con, module, rid, "create", data, user["id"])
    con.commit()
    fired = run_workflows(module, rid, data, user["id"])
    return {"id": rid, "workflows": fired}

@gen.put("/api/{module}/{rid}")
def update_record(module: str, rid: int, body: dict, user=Depends(current_user)):
    mod_or_404(module); can_write(user)
    old = con.execute(f'SELECT * FROM "{module}" WHERE id=? AND deleted=0', (rid,)).fetchone()
    if not old:
        raise HTTPException(404, "Not found")
    if user["role"] == "agent" and old["owner_id"] not in (user["id"], None):
        raise HTTPException(403, "Not your record")
    data = clean(module, body)
    if "owner_id" in body and user["role"] in ("admin", "manager"):
        data["owner_id"] = body["owner_id"]
    changes = {k: [old[k] if k in old.keys() else None, v] for k, v in data.items()
               if (old[k] if k in old.keys() else None) != v}
    if module == "opportunities":
        merged_v = data.get("value", old["value"] if "value" in old.keys() else 0)
        merged_p = data.get("probability", old["probability"] if "probability" in old.keys() else 0)
        data["weighted_value"] = round(_num(merged_v) * _num(merged_p) / 100, 2)
        # stage drives outcome first, then stamp the close date
        if data.get("stage") == "Won": data.setdefault("outcome", "Won")
        if data.get("stage") == "Lost": data.setdefault("outcome", "Lost")
        if data.get("outcome") in ("Won", "Lost") and not data.get("actual_close") \
           and not (old["actual_close"] if "actual_close" in old.keys() else None):
            data["actual_close"] = datetime.date.today().isoformat()
    data["updated_at"] = D.now()
    con.execute(f'UPDATE "{module}" SET {",".join(f_+chr(61)+"?" for f_ in [chr(34)+k+chr(34) for k in data])} WHERE id=?',
                list(data.values()) + [rid])
    D.log(con, module, rid, "update", changes, user["id"])
    con.commit()
    merged = dict(old); merged.update(data)
    fired = run_workflows(module, rid, merged, user["id"])
    return {"ok": True, "changes": changes, "workflows": fired}

@gen.delete("/api/{module}/{rid}")
def delete_record(module: str, rid: int, user=Depends(current_user)):
    mod_or_404(module); can_write(user)
    con.execute(f'UPDATE "{module}" SET deleted=1 WHERE id=?', (rid,))
    D.log(con, module, rid, "delete", {}, user["id"]); con.commit()
    return {"ok": True}

class Bulk(BaseModel):
    ids: list
    action: str
    field: str = ""
    value: str = ""

@app.post("/api/{module}/bulk")
def bulk(module: str, b: Bulk, user=Depends(current_user)):
    mod_or_404(module); can_write(user)
    ph = ",".join("?" * len(b.ids))
    if not b.ids: return {"ok": True, "affected": 0}
    if b.action == "delete":
        con.execute(f'UPDATE "{module}" SET deleted=1 WHERE id IN ({ph})', b.ids)
    elif b.action == "update":
        cols = [f["name"] for f in all_fields(module)]
        if b.field not in cols: raise HTTPException(400, "Bad field")
        con.execute(f'UPDATE "{module}" SET "{b.field}"=?, updated_at=? WHERE id IN ({ph})',
                    [b.value, D.now()] + b.ids)
    con.commit()
    return {"ok": True, "affected": len(b.ids)}

# ---------------- notes ----------------
@app.post("/api/notes/{module}/{rid}")
def add_note(module: str, rid: int, body: dict, user=Depends(current_user)):
    can_write(user)
    con.execute("INSERT INTO notes(module,record_id,body,user_id,created_at) VALUES(?,?,?,?,?)",
                (module, rid, body.get("body", ""), user["id"], D.now()))
    con.commit(); return {"ok": True}

# ---------------- line items ----------------
@app.post("/api/items/{module}/{rid}")
def save_items(module: str, rid: int, body: dict, user=Depends(current_user)):
    can_write(user)
    con.execute("DELETE FROM line_items WHERE module=? AND record_id=?", (module, rid))
    total = 0
    for it in body.get("items", []):
        qty, price = _num(it.get("qty", 1)), _num(it.get("price", 0))
        disc, tax = _num(it.get("discount", 0)), _num(it.get("tax", 0))
        line = (qty * price) * (1 - disc / 100) * (1 + tax / 100)
        total += line
        con.execute("""INSERT INTO line_items(module,record_id,product_id,name,qty,price,discount,tax)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (module, rid, it.get("product_id"), it.get("name", ""), qty, price, disc, tax))
    con.execute(f'UPDATE "{module}" SET amount=?, updated_at=? WHERE id=?', (round(total, 2), D.now(), rid))
    con.commit(); return {"ok": True, "total": round(total, 2)}

# ---------------- convert lead ----------------
@app.post("/api/leads/{rid}/convert")
def convert(rid: int, user=Depends(current_user)):
    can_write(user)
    l = con.execute("SELECT * FROM leads WHERE id=? AND deleted=0", (rid,)).fetchone()
    if not l: raise HTTPException(404, "Not found")
    if l["status"] == "Converted": raise HTTPException(400, "Already converted")
    ts = D.now()
    acc = con.execute("""INSERT INTO accounts(created_at,updated_at,created_by,owner_id,deleted,
        name,industry,phone,type,annual_revenue) VALUES(?,?,?,?,0,?,?,?,?,?)""",
        (ts, ts, user["id"], l["owner_id"], l["company"] or l["name"], l["industry"],
         l["phone"], "Customer", l["annual_revenue"])).lastrowid
    ct = con.execute("""INSERT INTO contacts(created_at,updated_at,created_by,owner_id,deleted,
        name,account_id,email,phone) VALUES(?,?,?,?,0,?,?,?,?)""",
        (ts, ts, user["id"], l["owner_id"], l["name"], acc, l["email"], l["phone"])).lastrowid
    dl = con.execute("""INSERT INTO deals(created_at,updated_at,created_by,owner_id,deleted,
        name,account_id,contact_id,amount,stage,probability,source,closing_date) VALUES(?,?,?,?,0,?,?,?,?,?,?,?,?)""",
        (ts, ts, user["id"], l["owner_id"], f'{l["company"] or l["name"]} — Opportunity', acc, ct,
         l["annual_revenue"] or 0, "Qualification", 20, l["source"],
         (datetime.date.today() + datetime.timedelta(days=30)).isoformat())).lastrowid
    con.execute("UPDATE leads SET status='Converted', updated_at=? WHERE id=?", (ts, rid))
    D.log(con, "leads", rid, "convert", {"account": acc, "contact": ct, "deal": dl}, user["id"])
    con.commit()
    return {"account_id": acc, "contact_id": ct, "deal_id": dl}

# ---------------- dashboard & reports ----------------
@app.get("/api/analytics/dashboard")
def dashboard(user=Depends(current_user)):
    g = lambda sql, p=(): con.execute(sql, p).fetchone()[0] or 0
    won = g("SELECT SUM(amount) FROM deals WHERE deleted=0 AND stage='Closed Won'")
    lost = g("SELECT SUM(amount) FROM deals WHERE deleted=0 AND stage='Closed Lost'")
    open_amt = g("SELECT SUM(amount) FROM deals WHERE deleted=0 AND stage NOT IN ('Closed Won','Closed Lost')")
    nwon = g("SELECT COUNT(*) FROM deals WHERE deleted=0 AND stage='Closed Won'")
    nlost = g("SELECT COUNT(*) FROM deals WHERE deleted=0 AND stage='Closed Lost'")
    pipeline = [dict(r) for r in con.execute(
        "SELECT stage k, COUNT(*) n, SUM(amount) v FROM deals WHERE deleted=0 GROUP BY stage")]
    leads_status = [dict(r) for r in con.execute(
        "SELECT status k, COUNT(*) n FROM leads WHERE deleted=0 GROUP BY status")]
    sources = [dict(r) for r in con.execute(
        "SELECT COALESCE(source,'Other') k, COUNT(*) n, SUM(amount) v FROM deals WHERE deleted=0 GROUP BY source")]
    leaderboard = [dict(r) for r in con.execute("""
        SELECT u.name k, u.target target, COALESCE(SUM(CASE WHEN d.stage='Closed Won' THEN d.amount END),0) v,
               COUNT(d.id) n FROM users u LEFT JOIN deals d ON d.owner_id=u.id AND d.deleted=0
        GROUP BY u.id ORDER BY v DESC""")]
    monthly = [dict(r) for r in con.execute("""
        SELECT substr(closing_date,1,7) k, SUM(amount) v, COUNT(*) n FROM deals
        WHERE deleted=0 AND stage='Closed Won' AND closing_date IS NOT NULL
        GROUP BY k ORDER BY k""")]
    tickets = [dict(r) for r in con.execute(
        "SELECT status k, COUNT(*) n FROM tickets WHERE deleted=0 GROUP BY status")]
    return {
        "kpi": {
            "revenue_won": won, "revenue_lost": lost, "pipeline_value": open_amt,
            "win_rate": round(nwon / (nwon + nlost) * 100, 1) if (nwon + nlost) else 0,
            "avg_deal": round(won / nwon, 2) if nwon else 0,
            "leads": g("SELECT COUNT(*) FROM leads WHERE deleted=0"),
            "accounts": g("SELECT COUNT(*) FROM accounts WHERE deleted=0"),
            "contacts": g("SELECT COUNT(*) FROM contacts WHERE deleted=0"),
            "open_deals": g("SELECT COUNT(*) FROM deals WHERE deleted=0 AND stage NOT IN ('Closed Won','Closed Lost')"),
            "open_tickets": g("SELECT COUNT(*) FROM tickets WHERE deleted=0 AND status!='Closed'"),
            "overdue_tasks": g("SELECT COUNT(*) FROM activities WHERE deleted=0 AND status!='Completed' AND due_date<?",
                               (datetime.date.today().isoformat(),)),
            "unpaid": g("SELECT SUM(COALESCE(amount,0)-COALESCE(paid_amount,0)) FROM invoices WHERE deleted=0 AND status!='Paid'"),
        },
        "pipeline": pipeline, "leads_status": leads_status, "sources": sources,
        "leaderboard": leaderboard, "monthly": monthly, "tickets": tickets,
    }

@app.get("/api/analytics/report")
def report(module: str, group_by: str, metric: str = "count", field: str = "", user=Depends(current_user)):
    mod_or_404(module)
    cols = [f["name"] for f in all_fields(module)]
    if group_by not in cols: raise HTTPException(400, "Bad group_by")
    if metric == "count":
        sel = "COUNT(*)"
    else:
        if field not in cols: raise HTTPException(400, "Bad field")
        sel = f'{ {"sum":"SUM","avg":"AVG","max":"MAX","min":"MIN"}.get(metric,"SUM") }("{field}")'
    rows = con.execute(f'SELECT COALESCE("{group_by}",\'—\') k, {sel} v FROM "{module}" '
                       f'WHERE deleted=0 GROUP BY 1 ORDER BY 2 DESC').fetchall()
    return {"rows": [{"k": r["k"], "v": r["v"] or 0} for r in rows]}

# ---------------- import / export ----------------
@app.get("/api/{module}/export/csv")
def export_csv(module: str, token: str = "", user=None):
    uid = parse_token(token)
    if not uid: raise HTTPException(401, "Auth required")
    mod_or_404(module)
    cols = ["id"] + [f["name"] for f in all_fields(module)] + ["created_at"]
    rows = con.execute(f'SELECT * FROM "{module}" WHERE deleted=0').fetchall()
    buf = io.StringIO(); w = csv.writer(buf); w.writerow(cols)
    for r in rows:
        w.writerow([r[c] if c in r.keys() else "" for c in cols])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{module}.csv"'})

@app.post("/api/{module}/import")
async def import_csv(module: str, file: UploadFile = File(...), user=Depends(current_user)):
    mod_or_404(module); can_write(user)
    text = (await file.read()).decode("utf-8-sig")
    rd = csv.DictReader(io.StringIO(text))
    cols = {f["name"] for f in all_fields(module)}
    n = 0
    for row in rd:
        data = {k.strip(): v for k, v in row.items() if k and k.strip() in cols and v not in ("", None)}
        if not data: continue
        data.update(created_at=D.now(), updated_at=D.now(), created_by=user["id"], deleted=0)
        data.setdefault("owner_id", user["id"])
        keys = list(data)
        con.execute(f'INSERT INTO "{module}" ({",".join(chr(34)+k+chr(34) for k in keys)}) '
                    f'VALUES ({",".join("?"*len(keys))})', [data[k] for k in keys])
        n += 1
    con.commit(); return {"imported": n}

# ---------------- users ----------------
@app.get("/api/admin/users")
def users(user=Depends(current_user)):
    return [{k: v for k, v in dict(r).items() if k != "password"}
            for r in con.execute("SELECT * FROM users ORDER BY id")]

@app.post("/api/admin/users")
def create_user(body: dict, user=Depends(current_user)):
    require(user, "admin")
    try:
        cur = con.execute("INSERT INTO users(email,password,name,role,active,target,created_at) VALUES(?,?,?,?,1,?,?)",
            (body["email"], hash_pw(body.get("password", "changeme")), body.get("name", ""),
             body.get("role", "agent"), _num(body.get("target", 0)), D.now()))
        con.commit(); return {"id": cur.lastrowid}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Email already exists")

@app.put("/api/admin/users/{uid}")
def update_user(uid: int, body: dict, user=Depends(current_user)):
    require(user, "admin")
    sets, vals = [], []
    for k in ("name", "role", "active", "target"):
        if k in body: sets.append(f"{k}=?"); vals.append(body[k])
    if body.get("password"): sets.append("password=?"); vals.append(hash_pw(body["password"]))
    if sets:
        con.execute(f"UPDATE users SET {','.join(sets)} WHERE id=?", vals + [uid]); con.commit()
    return {"ok": True}

# ---------------- workflows ----------------
@app.get("/api/admin/workflows")
def get_wf(user=Depends(current_user)):
    return [dict(r) for r in con.execute("SELECT * FROM workflows ORDER BY id DESC")]

@app.post("/api/admin/workflows")
def add_wf(body: dict, user=Depends(current_user)):
    require(user, "admin", "manager")
    con.execute("""INSERT INTO workflows(name,module,trigger,field,operator,value,action,action_value,active,created_at)
        VALUES(?,?,?,?,?,?,?,?,1,?)""",
        (body.get("name"), body.get("module"), body.get("trigger", "save"), body.get("field"),
         body.get("operator", "eq"), body.get("value"), body.get("action", "notify"),
         body.get("action_value", ""), D.now()))
    con.commit(); return {"ok": True}

@app.delete("/api/admin/workflows/{wid}")
def del_wf(wid: int, user=Depends(current_user)):
    require(user, "admin", "manager")
    con.execute("DELETE FROM workflows WHERE id=?", (wid,)); con.commit(); return {"ok": True}

@app.get("/api/notifications")
def notifs(user=Depends(current_user)):
    return [dict(r) for r in con.execute(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 30", (user["id"],))]

@app.post("/api/notifications/read")
def read_notifs(user=Depends(current_user)):
    con.execute("UPDATE notifications SET read=1 WHERE user_id=?", (user["id"],)); con.commit()
    return {"ok": True}

@app.get("/api/search")
def global_search(q: str, user=Depends(current_user)):
    out = []
    if len(q) < 2: return out
    for m, meta in MODULES.items():
        t = meta["title"]
        for r in con.execute(f'SELECT id,"{t}" AS t FROM "{m}" WHERE deleted=0 AND "{t}" LIKE ? LIMIT 5', (f"%{q}%",)):
            out.append({"module": m, "id": r["id"], "title": r["t"],
                        "icon": meta["icon"], "label_en": meta["label_en"], "label_ar": meta["label_ar"]})
    return out[:25]

@app.get("/api/timeline")
def timeline(user=Depends(current_user)):
    return [dict(r) for r in con.execute(
        "SELECT a.*,u.name uname FROM audit a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 40")]

# ---------------- static ----------------
HERE = os.path.dirname(__file__)

@app.get("/")
def landing():
    return FileResponse(os.path.join(HERE, "static", "landing.html"))


@app.get("/app")
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"))

@app.get("/app.js")
def appjs():
    return FileResponse(os.path.join(HERE, "static", "app.js"), media_type="application/javascript")

@app.get("/brand/{sub}/{name}")
def brandfile(sub: str, name: str):
    """Serve the visual-identity assets (logo, favicons, social, tokens)."""
    if sub not in ("logo", "favicon", "social", "assets") or "/" in name or ".." in name:
        raise HTTPException(404, "Not found")
    p = os.path.join(HERE, "brand", sub, name)
    if not os.path.isfile(p):
        raise HTTPException(404, "Not found")
    ext = name.rsplit(".", 1)[-1].lower()
    mt = {"svg": "image/svg+xml", "png": "image/png", "ico": "image/x-icon",
          "json": "application/json", "webmanifest": "application/manifest+json",
          "css": "text/css"}.get(ext, "application/octet-stream")
    return FileResponse(p, media_type=mt,
                        headers={"Cache-Control": "public, max-age=604800"})


@app.get("/favicon.ico")
def favicon():
    return FileResponse(os.path.join(HERE, "brand", "favicon", "favicon.ico"),
                        media_type="image/x-icon")


@app.get("/site.webmanifest")
def webmanifest():
    return FileResponse(os.path.join(HERE, "brand", "assets", "site.webmanifest"),
                        media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    """Served from root so its scope covers the whole origin."""
    return FileResponse(os.path.join(HERE, "static", "sw.js"),
                        media_type="application/javascript",
                        headers={"Cache-Control": "no-cache",
                                 "Service-Worker-Allowed": "/"})


@app.get("/pwa.js")
def pwa_js():
    return FileResponse(os.path.join(HERE, "static", "pwa.js"),
                        media_type="application/javascript")


@app.get("/offline")
def offline_page():
    return FileResponse(os.path.join(HERE, "static", "offline.html"))


@app.get("/theme-check")
def themecheck():
    return FileResponse(os.path.join(HERE, "static", "theme-check.html"))


@app.get("/font-check")
def fontcheck():
    return FileResponse(os.path.join(HERE, "static", "font-check.html"))


@app.get("/fonts/{name}")
def fontfile(name: str):
    if not name.replace("-", "").replace(".", "").isalnum():
        raise HTTPException(404, "Not found")
    p = os.path.join(HERE, "static", "fonts", name)
    if not os.path.isfile(p):
        raise HTTPException(404, "Not found")
    mt = "font/woff2" if name.endswith(".woff2") else "font/woff"
    return FileResponse(p, media_type=mt, headers={"Cache-Control": "public, max-age=31536000"})


@app.get("/styles.css")
def css():
    return FileResponse(os.path.join(HERE, "static", "styles.css"), media_type="text/css")

# generic CRUD mounted LAST so specific routes win
P.register_admin(app, current_user, require)
M.register(app, current_user, require)
PAY.register(app, current_user, require)
INTEL.register(app, current_user, require)
SEG.register(app, current_user, require)
GEO.register(app, current_user, require)
PT.register(app, current_user, require)
LOY.register(app, current_user, require)
AI.register(app, current_user, require)
PF.register(app, current_user, require)
RPT.register(app, current_user, require)
AP.register_admin(app, current_user, require)
app.include_router(AP.aportal)
PAY.register_portal(P.portal, P.portal_user)
app.include_router(PAY.pay)
app.include_router(P.portal)
app.include_router(gen)
