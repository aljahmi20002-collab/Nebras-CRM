import os, io, csv, json, datetime, math, sqlite3
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
from authz import SHARED_MODULES, record_or_404, scope_clause
from security import (
    client_ip, configured_secret, hash_password, make_token as sign_token,
    parse_token as parse_signed_token, password_error, verify_password,
)

# Development defaults keep the bundled demonstration data usable.  A production
# deployment must set CRM_SECRET (see README) and cannot silently use this value.
LEGACY_SECRET = "arena-crm-secret-key-change-me"
SECRET = configured_secret("CRM_SECRET", LEGACY_SECRET, "NebrasCRM staff authentication")
try:
    STAFF_TOKEN_TTL = max(300, int(os.environ.get("CRM_TOKEN_TTL_SECONDS", "28800")))
except ValueError:
    STAFF_TOKEN_TTL = 28800

# ---- brute-force protection & rate limiting (in-memory, per-process) ----
import time as _time
from collections import defaultdict, deque
_LOGIN_FAILS = defaultdict(list)
_RATE = defaultdict(lambda: deque(maxlen=240))
LOCKOUT_TRIES, LOCKOUT_WINDOW, LOCKOUT_MINS = 5, 900, 15
RATE_LIMIT, RATE_WINDOW = 240, 60


def _client(request):
    return client_ip(request)


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
def _cors_origins():
    configured = os.environ.get("CRM_CORS_ORIGINS", "").strip()
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    # Same-origin is the secure production default.  The permissive setting is
    # retained for local development and the bundled demo only.
    return [] if os.environ.get("CRM_ENV", "").lower() in {"prod", "production"} else ["*"]


app = FastAPI(title="NebrasCRM API", version="1.0")
gen = APIRouter()  # generic catch-all CRUD, mounted last
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def guard(request: Request, call_next):
    protected_path = request.url.path.startswith(("/api", "/portal/api", "/agent/api", "/pay/api"))
    if protected_path:
        ip = _client(request)
        now = _time.time()
        q = _RATE[ip]
        while q and now - q[0] > RATE_WINDOW:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return JSONResponse({"detail": "Rate limit exceeded. Slow down."}, status_code=429)
        q.append(now)
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    # The Capacitor shell intentionally embeds /app in a local WebView iframe.
    # Keep clickjacking protection for every other route without breaking mobile.
    if request.url.path != "/app":
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
    """Password hash used by seed scripts and all new staff accounts."""
    return hash_password(pw)


def verify_pw(pw: str, stored: str) -> tuple[bool, bool]:
    # Include the original demo secret so an existing bundled database can be
    # upgraded after its first successful login, even when CRM_SECRET changes.
    return verify_password(pw, stored, legacy_secrets=(SECRET, LEGACY_SECRET))


def make_token(uid: int) -> str:
    return sign_token(uid, SECRET, STAFF_TOKEN_TTL)


def parse_token(tok: str):
    return parse_signed_token(tok, SECRET)

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

def can_write(user, module: str | None = None):
    if user["role"] == "readonly":
        raise HTTPException(403, "Read-only user")
    if module in SHARED_MODULES and user["role"] == "agent":
        raise HTTPException(403, "Only managers can modify shared reference data")

class Login(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
def login(b: Login, request: Request):
    email = b.email.strip().lower()
    if not email or len(email) > 320:
        raise HTTPException(400, "Invalid email")
    key = f"{_client(request)}|{email}"
    check_lockout(key)
    r = con.execute("SELECT * FROM users WHERE lower(email)=lower(?) AND active=1", (email,)).fetchone()
    valid, upgrade = verify_pw(b.password, r["password"] if r else "")
    if not r or not valid:
        record_fail(key)
        left = max(0, LOCKOUT_TRIES - len(_LOGIN_FAILS[key]))
        raise HTTPException(401, f"Invalid credentials ({left} attempts left)" if left > 0
                            else "Invalid credentials")
    if upgrade:
        con.execute("UPDATE users SET password=? WHERE id=?", (hash_pw(b.password), r["id"]))
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
    mod_or_404(module)
    if page < 1:
        raise HTTPException(400, "page must be at least 1")
    if not 1 <= per_page <= 200:
        raise HTTPException(400, "per_page must be between 1 and 200")
    if len(q) > 250:
        raise HTTPException(400, "Search query is too long")

    flds = all_fields(module)
    cols = [f["name"] for f in flds]
    scoped, scoped_params = scope_clause(user, module)
    where, params = ["deleted=0", scoped], list(scoped_params)
    if q:
        searchable = [f["name"] for f in flds if f["type"] in ("text", "email", "phone", "textarea")]
        if searchable:
            where.append("(" + " OR ".join(f'"{c}" LIKE ?' for c in searchable) + ")")
            params += [f"%{q}%"] * len(searchable)
    if mine:
        where.append("owner_id=?")
        params.append(user["id"])
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except (TypeError, ValueError, json.JSONDecodeError):
            raise HTTPException(400, "Invalid filters")
        if not isinstance(parsed_filters, list) or len(parsed_filters) > 20:
            raise HTTPException(400, "Invalid filters")
        for f in parsed_filters:
            if not isinstance(f, dict):
                raise HTTPException(400, "Invalid filter")
            field, value, op = f.get("field"), f.get("value"), f.get("op", "eq")
            if field not in cols or value in (None, ""):
                continue
            if op == "eq":
                where.append(f'"{field}"=?'); params.append(value)
            elif op == "ne":
                where.append(f'"{field}"!=?'); params.append(value)
            elif op == "contains":
                where.append(f'"{field}" LIKE ?'); params.append(f"%{value}%")
            elif op == "gt":
                where.append(f'"{field}">?'); params.append(value)
            elif op == "lt":
                where.append(f'"{field}"<?'); params.append(value)
            else:
                raise HTTPException(400, "Invalid filter operator")
    w = " AND ".join(where)
    sort = sort if sort in cols + ["id", "created_at", "updated_at"] else "id"
    direction = "DESC" if dir.lower() == "desc" else "ASC"
    total = con.execute(f'SELECT COUNT(*) c FROM "{module}" WHERE {w}', params).fetchone()["c"]
    rows = con.execute(
        f'SELECT * FROM "{module}" WHERE {w} ORDER BY "{sort}" {direction} LIMIT ? OFFSET ?',
        params + [per_page, (page - 1) * per_page],
    ).fetchall()
    return {"data": enrich(rows, module), "total": total, "page": page, "per_page": per_page}


@gen.get("/api/{module}/{rid}")
def get_record(module: str, rid: int, user=Depends(current_user)):
    mod_or_404(module)
    r = record_or_404(con, module, rid, user)
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


@gen.post("/api/{module}")
def create_record(module: str, body: dict, user=Depends(current_user)):
    mod_or_404(module)
    can_write(user, module)
    data = clean(module, body)
    fields = all_fields(module)
    for f in fields:
        if f.get("default") is not None and data.get(f["name"]) in (None, ""):
            data[f["name"]] = f["default"]
        if f.get("required") and data.get(f["name"]) in (None, ""):
            raise HTTPException(400, f'Field required: {f["label_en"]}')

    if module == "opportunities":
        if data.get("stage") in ("Won", "Lost"):
            data["outcome"] = data["stage"]
        data["weighted_value"] = round(_num(data.get("value")) * _num(data.get("probability") or 0) / 100, 2)
        if data.get("outcome") in ("Won", "Lost") and not data.get("actual_close"):
            data["actual_close"] = datetime.date.today().isoformat()

    # Agents always create records under themselves.  Only management may assign
    # a record to someone else at creation time.
    if user["role"] == "agent":
        data["owner_id"] = user["id"]
    elif user["role"] not in ("admin", "manager"):
        data.pop("owner_id", None)
    data.setdefault("owner_id", user["id"])
    data.update(created_at=D.now(), updated_at=D.now(), created_by=user["id"], deleted=0)
    keys = list(data)
    cur = con.execute(
        f'INSERT INTO "{module}" ({",".join(chr(34)+k+chr(34) for k in keys)}) '
        f'VALUES ({",".join("?" * len(keys))})',
        [data[k] for k in keys],
    )
    rid = cur.lastrowid
    D.log(con, module, rid, "create", data, user["id"])
    con.commit()
    fired = run_workflows(module, rid, data, user["id"])
    return {"id": rid, "workflows": fired}


@gen.put("/api/{module}/{rid}")
def update_record(module: str, rid: int, body: dict, user=Depends(current_user)):
    mod_or_404(module)
    can_write(user, module)
    old = record_or_404(con, module, rid, user)
    data = clean(module, body)
    if user["role"] not in ("admin", "manager"):
        data.pop("owner_id", None)

    if module == "opportunities":
        merged_v = data.get("value", old["value"] if "value" in old.keys() else 0)
        merged_p = data.get("probability", old["probability"] if "probability" in old.keys() else 0)
        data["weighted_value"] = round(_num(merged_v) * _num(merged_p) / 100, 2)
        if data.get("stage") in ("Won", "Lost"):
            data["outcome"] = data["stage"]
        if data.get("outcome") in ("Won", "Lost") and not data.get("actual_close") \
           and not (old["actual_close"] if "actual_close" in old.keys() else None):
            data["actual_close"] = datetime.date.today().isoformat()

    merged = dict(old)
    merged.update(data)
    for f in all_fields(module):
        if f.get("required") and merged.get(f["name"]) in (None, ""):
            raise HTTPException(400, f'Field required: {f["label_en"]}')

    changes = {
        k: [old[k] if k in old.keys() else None, v]
        for k, v in data.items()
        if (old[k] if k in old.keys() else None) != v
    }
    if not changes:
        return {"ok": True, "changes": {}, "workflows": []}
    data["updated_at"] = D.now()
    con.execute(
        f'UPDATE "{module}" SET {",".join(chr(34)+k+chr(34)+"=?" for k in data)} WHERE id=?',
        list(data.values()) + [rid],
    )
    D.log(con, module, rid, "update", changes, user["id"])
    con.commit()
    merged.update(data)
    fired = run_workflows(module, rid, merged, user["id"])
    return {"ok": True, "changes": changes, "workflows": fired}


@gen.delete("/api/{module}/{rid}")
def delete_record(module: str, rid: int, user=Depends(current_user)):
    mod_or_404(module)
    can_write(user, module)
    record_or_404(con, module, rid, user)
    con.execute(f'UPDATE "{module}" SET deleted=1, updated_at=? WHERE id=?', (D.now(), rid))
    D.log(con, module, rid, "delete", {}, user["id"])
    con.commit()
    return {"ok": True}


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
    try:
        n = float(v)
        return n if math.isfinite(n) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _numeric_or_400(value, field_name):
    if isinstance(value, bool):
        raise HTTPException(400, f"{field_name} must be a number")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise HTTPException(400, f"{field_name} must be a number")
    if not math.isfinite(number):
        raise HTTPException(400, f"{field_name} must be finite")
    return number


def clean(module, body):
    """Allow only declared fields and validate values before dynamic SQL uses them."""
    if not isinstance(body, dict):
        raise HTTPException(400, "Request body must be an object")
    cols = {f["name"]: f for f in all_fields(module)}
    out = {}
    for k, v in body.items():
        f = cols.get(k)
        if not f:
            continue
        typ = f["type"]
        if v in ("", None):
            out[k] = None
            continue
        if typ in ("number", "currency"):
            v = _numeric_or_400(v, f["label_en"])
        elif typ == "select":
            options = f.get("options", [])
            if options and v not in options:
                raise HTTPException(400, f'Invalid value for {f["label_en"]}')
        elif typ == "date":
            try:
                v = datetime.date.fromisoformat(str(v)[:10]).isoformat()
            except (TypeError, ValueError):
                raise HTTPException(400, f'Invalid date for {f["label_en"]}')
        elif typ == "email":
            v = str(v).strip()
            if len(v) > 320 or "@" not in v or "\n" in v or "\r" in v:
                raise HTTPException(400, f'Invalid email for {f["label_en"]}')
        elif typ == "lookup":
            try:
                v = int(v)
            except (TypeError, ValueError):
                raise HTTPException(400, f'Invalid reference for {f["label_en"]}')
            target = f.get("target")
            if target not in MODULES or not con.execute(
                f'SELECT 1 FROM "{target}" WHERE id=? AND deleted=0', (v,)
            ).fetchone():
                raise HTTPException(400, f'Unknown reference for {f["label_en"]}')
        elif typ == "user":
            try:
                v = int(v)
            except (TypeError, ValueError):
                raise HTTPException(400, f'Invalid user for {f["label_en"]}')
            if not con.execute("SELECT 1 FROM users WHERE id=? AND active=1", (v,)).fetchone():
                raise HTTPException(400, f'Unknown user for {f["label_en"]}')
        elif isinstance(v, str):
            if len(v) > 20_000:
                raise HTTPException(400, f'{f["label_en"]} is too long')
            v = v.strip() if typ in ("text", "phone", "url") else v
        out[k] = v
    return out

class Bulk(BaseModel):
    ids: list[int]
    action: str
    field: str = ""
    value: object = None


@app.post("/api/{module}/bulk")
def bulk(module: str, b: Bulk, user=Depends(current_user)):
    mod_or_404(module)
    can_write(user, module)
    ids = list(dict.fromkeys(b.ids))
    if not ids:
        return {"ok": True, "affected": 0}
    if len(ids) > 200:
        raise HTTPException(400, "At most 200 records can be updated at once")
    if b.action not in {"delete", "update"}:
        raise HTTPException(400, "Unknown bulk action")

    scope, scope_params = scope_clause(user, module)
    placeholders = ",".join("?" * len(ids))
    rows = con.execute(
        f'SELECT * FROM "{module}" WHERE id IN ({placeholders}) AND deleted=0 AND {scope}',
        ids + scope_params,
    ).fetchall()
    if len(rows) != len(ids):
        # Do not disclose whether an inaccessible record exists.
        raise HTTPException(404, "One or more records were not found")

    if b.action == "delete":
        con.execute(
            f'UPDATE "{module}" SET deleted=1, updated_at=? WHERE id IN ({placeholders})',
            [D.now()] + ids,
        )
        for row in rows:
            D.log(con, module, row["id"], "delete", {}, user["id"])
    else:
        if b.field == "owner_id" and user["role"] not in ("admin", "manager"):
            raise HTTPException(403, "Only managers can reassign records")
        data = clean(module, {b.field: b.value})
        if b.field not in data:
            raise HTTPException(400, "Bad field")
        field_meta = next((f for f in all_fields(module) if f["name"] == b.field), None)
        if field_meta and field_meta.get("required") and data[b.field] in (None, ""):
            raise HTTPException(400, f'Field required: {field_meta["label_en"]}')
        con.execute(
            f'UPDATE "{module}" SET "{b.field}"=?, updated_at=? WHERE id IN ({placeholders})',
            [data[b.field], D.now()] + ids,
        )
        for row in rows:
            old = row[b.field] if b.field in row.keys() else None
            D.log(con, module, row["id"], "update", {b.field: [old, data[b.field]]}, user["id"])
    con.commit()
    return {"ok": True, "affected": len(ids)}


# ---------------- notes ----------------
@app.post("/api/notes/{module}/{rid}")
def add_note(module: str, rid: int, body: dict, user=Depends(current_user)):
    mod_or_404(module)
    can_write(user, module)
    record_or_404(con, module, rid, user)
    text = str((body or {}).get("body", "")).strip()
    if not text:
        raise HTTPException(400, "Note body is required")
    if len(text) > 20_000:
        raise HTTPException(400, "Note is too long")
    con.execute("INSERT INTO notes(module,record_id,body,user_id,created_at) VALUES(?,?,?,?,?)",
                (module, rid, text, user["id"], D.now()))
    D.log(con, module, rid, "note", {"length": len(text)}, user["id"])
    con.commit()
    return {"ok": True}


# ---------------- line items ----------------
@app.post("/api/items/{module}/{rid}")
def save_items(module: str, rid: int, body: dict, user=Depends(current_user)):
    meta = mod_or_404(module)
    can_write(user)
    if not meta.get("line_items"):
        raise HTTPException(400, "This module does not support line items")
    record_or_404(con, module, rid, user)
    items = (body or {}).get("items", [])
    if not isinstance(items, list) or len(items) > 500:
        raise HTTPException(400, "Invalid line items")

    prepared, total = [], 0.0
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise HTTPException(400, f"Line item {index} is invalid")
        qty = _numeric_or_400(item.get("qty", 1), "Quantity")
        price = _numeric_or_400(item.get("price", 0), "Price")
        discount = _numeric_or_400(item.get("discount", 0), "Discount")
        tax = _numeric_or_400(item.get("tax", 0), "Tax")
        if qty <= 0 or price < 0 or not 0 <= discount <= 100 or not 0 <= tax <= 100:
            raise HTTPException(400, f"Line item {index} has invalid amounts")
        product_id = item.get("product_id")
        if product_id not in (None, ""):
            try:
                product_id = int(product_id)
            except (TypeError, ValueError):
                raise HTTPException(400, f"Line item {index} has an invalid product")
            if not con.execute("SELECT 1 FROM products WHERE id=? AND deleted=0", (product_id,)).fetchone():
                raise HTTPException(400, f"Line item {index} references an unknown product")
        name = str(item.get("name", "")).strip()
        if len(name) > 500:
            raise HTTPException(400, f"Line item {index} name is too long")
        line = qty * price * (1 - discount / 100) * (1 + tax / 100)
        total += line
        prepared.append((product_id, name, qty, price, discount, tax))

    con.execute("DELETE FROM line_items WHERE module=? AND record_id=?", (module, rid))
    for product_id, name, qty, price, discount, tax in prepared:
        con.execute("""INSERT INTO line_items(module,record_id,product_id,name,qty,price,discount,tax)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (module, rid, product_id, name, qty, price, discount, tax))
    total = round(total, 2)
    con.execute(f'UPDATE "{module}" SET amount=?, updated_at=? WHERE id=?', (total, D.now(), rid))
    D.log(con, module, rid, "line_items", {"count": len(prepared), "total": total}, user["id"])
    con.commit()
    return {"ok": True, "total": total}


# ---------------- convert lead ----------------
@app.post("/api/leads/{rid}/convert")
def convert(rid: int, user=Depends(current_user)):
    can_write(user)
    l = record_or_404(con, "leads", rid, user)
    if l["status"] == "Converted":
        raise HTTPException(400, "Already converted")
    ts = D.now()
    owner_id = l["owner_id"] if l["owner_id"] is not None else user["id"]
    acc = con.execute("""INSERT INTO accounts(created_at,updated_at,created_by,owner_id,deleted,
        name,industry,phone,type,annual_revenue) VALUES(?,?,?,?,0,?,?,?,?,?)""",
        (ts, ts, user["id"], owner_id, l["company"] or l["name"], l["industry"],
         l["phone"], "Customer", l["annual_revenue"])).lastrowid
    ct = con.execute("""INSERT INTO contacts(created_at,updated_at,created_by,owner_id,deleted,
        name,account_id,email,phone) VALUES(?,?,?,?,0,?,?,?,?)""",
        (ts, ts, user["id"], owner_id, l["name"], acc, l["email"], l["phone"])).lastrowid
    dl = con.execute("""INSERT INTO deals(created_at,updated_at,created_by,owner_id,deleted,
        name,account_id,contact_id,amount,stage,probability,source,closing_date) VALUES(?,?,?,?,0,?,?,?,?,?,?,?,?)""",
        (ts, ts, user["id"], owner_id, f'{l["company"] or l["name"]} — Opportunity', acc, ct,
         l["annual_revenue"] or 0, "Qualification", 20, l["source"],
         (datetime.date.today() + datetime.timedelta(days=30)).isoformat())).lastrowid
    con.execute("UPDATE leads SET status='Converted', updated_at=? WHERE id=?", (ts, rid))
    D.log(con, "leads", rid, "convert", {"account": acc, "contact": ct, "deal": dl}, user["id"])
    con.commit()
    return {"account_id": acc, "contact_id": ct, "deal_id": dl}


# ---------------- dashboard & reports ----------------
@app.get("/api/analytics/dashboard")
def dashboard(user=Depends(current_user)):
    """Return a dashboard scoped to the current staff member where required."""
    def scalar(sql, params=()):
        return con.execute(sql, params).fetchone()[0] or 0

    deal_scope, deal_params = scope_clause(user, "deals")
    lead_scope, lead_params = scope_clause(user, "leads")
    account_scope, account_params = scope_clause(user, "accounts")
    contact_scope, contact_params = scope_clause(user, "contacts")
    ticket_scope, ticket_params = scope_clause(user, "tickets")
    activity_scope, activity_params = scope_clause(user, "activities")
    invoice_scope, invoice_params = scope_clause(user, "invoices")
    deals_where = f"deleted=0 AND {deal_scope}"

    won = scalar(f"SELECT SUM(amount) FROM deals WHERE {deals_where} AND stage='Closed Won'", deal_params)
    lost = scalar(f"SELECT SUM(amount) FROM deals WHERE {deals_where} AND stage='Closed Lost'", deal_params)
    open_amt = scalar(
        f"SELECT SUM(amount) FROM deals WHERE {deals_where} AND stage NOT IN ('Closed Won','Closed Lost')",
        deal_params,
    )
    nwon = scalar(f"SELECT COUNT(*) FROM deals WHERE {deals_where} AND stage='Closed Won'", deal_params)
    nlost = scalar(f"SELECT COUNT(*) FROM deals WHERE {deals_where} AND stage='Closed Lost'", deal_params)
    pipeline = [dict(r) for r in con.execute(
        f"SELECT stage k, COUNT(*) n, SUM(amount) v FROM deals WHERE {deals_where} GROUP BY stage", deal_params)]
    leads_status = [dict(r) for r in con.execute(
        f"SELECT status k, COUNT(*) n FROM leads WHERE deleted=0 AND {lead_scope} GROUP BY status", lead_params)]
    sources = [dict(r) for r in con.execute(
        f"SELECT COALESCE(source,'Other') k, COUNT(*) n, SUM(amount) v FROM deals "
        f"WHERE {deals_where} GROUP BY source", deal_params)]
    if user["role"] == "agent":
        leaderboard = [{
            "k": user["name"], "target": user.get("target") or 0,
            "v": won, "n": scalar(f"SELECT COUNT(*) FROM deals WHERE {deals_where}", deal_params),
        }]
    else:
        leaderboard = [dict(r) for r in con.execute("""
            SELECT u.name k, u.target target, COALESCE(SUM(CASE WHEN d.stage='Closed Won' THEN d.amount END),0) v,
                   COUNT(d.id) n FROM users u LEFT JOIN deals d ON d.owner_id=u.id AND d.deleted=0
            WHERE u.active=1 GROUP BY u.id ORDER BY v DESC""")]
    monthly = [dict(r) for r in con.execute(
        f"SELECT substr(closing_date,1,7) k, SUM(amount) v, COUNT(*) n FROM deals "
        f"WHERE {deals_where} AND stage='Closed Won' AND closing_date IS NOT NULL GROUP BY k ORDER BY k",
        deal_params,
    )]
    tickets = [dict(r) for r in con.execute(
        f"SELECT status k, COUNT(*) n FROM tickets WHERE deleted=0 AND {ticket_scope} GROUP BY status",
        ticket_params,
    )]
    return {
        "kpi": {
            "revenue_won": won, "revenue_lost": lost, "pipeline_value": open_amt,
            "win_rate": round(nwon / (nwon + nlost) * 100, 1) if (nwon + nlost) else 0,
            "avg_deal": round(won / nwon, 2) if nwon else 0,
            "leads": scalar(f"SELECT COUNT(*) FROM leads WHERE deleted=0 AND {lead_scope}", lead_params),
            "accounts": scalar(f"SELECT COUNT(*) FROM accounts WHERE deleted=0 AND {account_scope}", account_params),
            "contacts": scalar(f"SELECT COUNT(*) FROM contacts WHERE deleted=0 AND {contact_scope}", contact_params),
            "open_deals": scalar(
                f"SELECT COUNT(*) FROM deals WHERE {deals_where} AND stage NOT IN ('Closed Won','Closed Lost')",
                deal_params,
            ),
            "open_tickets": scalar(
                f"SELECT COUNT(*) FROM tickets WHERE deleted=0 AND {ticket_scope} AND status!='Closed'", ticket_params
            ),
            "overdue_tasks": scalar(
                f"SELECT COUNT(*) FROM activities WHERE deleted=0 AND {activity_scope} "
                "AND status!='Completed' AND due_date<?",
                activity_params + [datetime.date.today().isoformat()],
            ),
            "unpaid": scalar(
                f"SELECT SUM(COALESCE(amount,0)-COALESCE(paid_amount,0)) FROM invoices "
                f"WHERE deleted=0 AND {invoice_scope} AND status NOT IN ('Paid','Cancelled')",
                invoice_params,
            ),
        },
        "pipeline": pipeline, "leads_status": leads_status, "sources": sources,
        "leaderboard": leaderboard, "monthly": monthly, "tickets": tickets,
    }


@app.get("/api/analytics/report")
def report(module: str, group_by: str, metric: str = "count", field: str = "", user=Depends(current_user)):
    mod_or_404(module)
    cols = [f["name"] for f in all_fields(module)]
    if group_by not in cols:
        raise HTTPException(400, "Bad group_by")
    if metric == "count":
        sel = "COUNT(*)"
    else:
        aggregations = {"sum": "SUM", "avg": "AVG", "max": "MAX", "min": "MIN"}
        if metric not in aggregations or field not in cols:
            raise HTTPException(400, "Bad metric or field")
        sel = f'{aggregations[metric]}("{field}")'
    scoped, params = scope_clause(user, module)
    rows = con.execute(
        f'SELECT COALESCE("{group_by}",\'—\') k, {sel} v FROM "{module}" '
        f'WHERE deleted=0 AND {scoped} GROUP BY 1 ORDER BY 2 DESC',
        params,
    ).fetchall()
    return {"rows": [{"k": r["k"], "v": r["v"] or 0} for r in rows]}


# ---------------- import / export ----------------
def _csv_cell(value):
    """Prevent spreadsheet applications from interpreting user data as a formula."""
    if value is None:
        return ""
    text = str(value)
    return "'" + text if text[:1] in {"=", "+", "-", "@"} else text


@app.get("/api/{module}/export/csv")
def export_csv(module: str, user=Depends(current_user)):
    mod_or_404(module)
    cols = ["id"] + [f["name"] for f in all_fields(module)] + ["created_at"]
    scoped, params = scope_clause(user, module)
    rows = con.execute(f'SELECT * FROM "{module}" WHERE deleted=0 AND {scoped}', params).fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(cols)
    for row in rows:
        writer.writerow([_csv_cell(row[c] if c in row.keys() else "") for c in cols])
    return StreamingResponse(
        iter(["\ufeff" + buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{module}.csv"'},
    )


@app.post("/api/{module}/import")
async def import_csv(module: str, file: UploadFile = File(...), user=Depends(current_user)):
    mod_or_404(module)
    can_write(user, module)
    raw_file = await file.read(5 * 1024 * 1024 + 1)
    if len(raw_file) > 5 * 1024 * 1024:
        raise HTTPException(413, "CSV file is too large (max 5 MB)")
    try:
        text = raw_file.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "CSV must be UTF-8 encoded")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(400, "CSV must include a header row")
    rows = list(reader)
    if len(rows) > 2_000:
        raise HTTPException(400, "CSV contains too many rows (max 2000)")

    imported = []
    try:
        for number, row in enumerate(rows, start=2):
            raw = {
                key.strip(): value
                for key, value in row.items()
                if key and key.strip() in {f["name"] for f in all_fields(module)} and value not in ("", None)
            }
            if not raw:
                continue
            data = clean(module, raw)
            for field in all_fields(module):
                if field.get("default") is not None and data.get(field["name"]) in (None, ""):
                    data[field["name"]] = field["default"]
                if field.get("required") and data.get(field["name"]) in (None, ""):
                    raise HTTPException(400, f'Row {number}: field required: {field["label_en"]}')
            if user["role"] == "agent":
                data["owner_id"] = user["id"]
            elif user["role"] not in ("admin", "manager"):
                data.pop("owner_id", None)
            data.setdefault("owner_id", user["id"])
            if module == "opportunities":
                if data.get("stage") in ("Won", "Lost"):
                    data["outcome"] = data["stage"]
                data["weighted_value"] = round(
                    _num(data.get("value")) * _num(data.get("probability") or 0) / 100, 2
                )
            data.update(created_at=D.now(), updated_at=D.now(), created_by=user["id"], deleted=0)
            keys = list(data)
            rid = con.execute(
                f'INSERT INTO "{module}" ({",".join(chr(34)+k+chr(34) for k in keys)}) '
                f'VALUES ({",".join("?" * len(keys))})',
                [data[k] for k in keys],
            ).lastrowid
            D.log(con, module, rid, "import", {"row": number}, user["id"])
            imported.append(rid)
        con.commit()
    except HTTPException:
        con.rollback()
        raise
    except Exception:
        con.rollback()
        raise HTTPException(400, "Unable to import CSV")
    return {"imported": len(imported)}


# ---------------- users ----------------
def _valid_email(value):
    email = str(value or "").strip().lower()
    if len(email) > 320 or "@" not in email or "\n" in email or "\r" in email:
        raise HTTPException(400, "Invalid email")
    return email


@app.get("/api/admin/users")
def users(user=Depends(current_user)):
    require(user, "admin")
    return [{k: v for k, v in dict(r).items() if k != "password"}
            for r in con.execute("SELECT * FROM users ORDER BY id")]


@app.post("/api/admin/users")
def create_user(body: dict, user=Depends(current_user)):
    require(user, "admin")
    email = _valid_email((body or {}).get("email"))
    name = str((body or {}).get("name", "")).strip()
    role = (body or {}).get("role", "agent")
    password = (body or {}).get("password", "")
    if not name or len(name) > 200:
        raise HTTPException(400, "A valid name is required")
    if role not in ROLES:
        raise HTTPException(400, "Invalid role")
    error = password_error(password)
    if error:
        raise HTTPException(400, error)
    target = _numeric_or_400((body or {}).get("target", 0), "Target")
    if target < 0:
        raise HTTPException(400, "Target cannot be negative")
    active = 1 if (body or {}).get("active", 1) not in (0, False, "0", "false") else 0
    try:
        cur = con.execute(
            "INSERT INTO users(email,password,name,role,active,target,created_at) VALUES(?,?,?,?,?,?,?)",
            (email, hash_pw(password), name, role, active, target, D.now()),
        )
        D.log(con, "users", cur.lastrowid, "create", {"email": email, "role": role}, user["id"])
        con.commit()
        return {"id": cur.lastrowid}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Email already exists")


@app.put("/api/admin/users/{uid}")
def update_user(uid: int, body: dict, user=Depends(current_user)):
    require(user, "admin")
    target_user = con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not target_user:
        raise HTTPException(404, "User not found")
    body = body or {}
    sets, vals = [], []
    if "name" in body:
        name = str(body["name"] or "").strip()
        if not name or len(name) > 200:
            raise HTTPException(400, "A valid name is required")
        sets.append("name=?"); vals.append(name)
    if "role" in body:
        if body["role"] not in ROLES:
            raise HTTPException(400, "Invalid role")
        if uid == user["id"] and body["role"] != "admin":
            raise HTTPException(400, "You cannot remove your own administrator role")
        sets.append("role=?"); vals.append(body["role"])
    if "active" in body:
        active = 1 if body["active"] not in (0, False, "0", "false") else 0
        if uid == user["id"] and not active:
            raise HTTPException(400, "You cannot deactivate your own account")
        sets.append("active=?"); vals.append(active)
    if "target" in body:
        target = _numeric_or_400(body["target"], "Target")
        if target < 0:
            raise HTTPException(400, "Target cannot be negative")
        sets.append("target=?"); vals.append(target)
    if body.get("password"):
        error = password_error(body["password"])
        if error:
            raise HTTPException(400, error)
        sets.append("password=?"); vals.append(hash_pw(body["password"]))
    if sets:
        con.execute(f"UPDATE users SET {','.join(sets)} WHERE id=?", vals + [uid])
        D.log(con, "users", uid, "update", {"fields": [x.split("=")[0] for x in sets]}, user["id"])
        con.commit()
    return {"ok": True}


# ---------------- workflows ----------------
@app.get("/api/admin/workflows")
def get_wf(user=Depends(current_user)):
    require(user, "admin", "manager")
    return [dict(r) for r in con.execute("SELECT * FROM workflows ORDER BY id DESC")]


@app.post("/api/admin/workflows")
def add_wf(body: dict, user=Depends(current_user)):
    require(user, "admin", "manager")
    body = body or {}
    module, field = body.get("module"), body.get("field")
    if module not in MODULES or field not in {f["name"] for f in all_fields(module)}:
        raise HTTPException(400, "Invalid workflow module or field")
    operator = body.get("operator", "eq")
    action = body.get("action", "notify")
    if operator not in {"eq", "ne", "contains", "gt", "lt"}:
        raise HTTPException(400, "Invalid workflow operator")
    if action not in {"notify", "create_task", "send_email", "set_field"}:
        raise HTTPException(400, "Invalid workflow action")
    name = str(body.get("name", "")).strip()
    if not name or len(name) > 200:
        raise HTTPException(400, "Workflow name is required")
    con.execute("""INSERT INTO workflows(name,module,trigger,field,operator,value,action,action_value,active,created_at)
        VALUES(?,?,?,?,?,?,?,?,1,?)""",
        (name, module, body.get("trigger", "save"), field, operator, str(body.get("value", "")),
         action, str(body.get("action_value", "")), D.now()))
    con.commit()
    return {"ok": True}


@app.delete("/api/admin/workflows/{wid}")
def del_wf(wid: int, user=Depends(current_user)):
    require(user, "admin", "manager")
    con.execute("DELETE FROM workflows WHERE id=?", (wid,))
    con.commit()
    return {"ok": True}


@app.get("/api/notifications")
def notifs(user=Depends(current_user)):
    return [dict(r) for r in con.execute(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 30", (user["id"],))]


@app.post("/api/notifications/read")
def read_notifs(user=Depends(current_user)):
    con.execute("UPDATE notifications SET read=1 WHERE user_id=?", (user["id"],))
    con.commit()
    return {"ok": True}


@app.get("/api/search")
def global_search(q: str, user=Depends(current_user)):
    q = q.strip()
    if len(q) < 2:
        return []
    if len(q) > 250:
        raise HTTPException(400, "Search query is too long")
    out = []
    for module, meta in MODULES.items():
        title = meta["title"]
        scoped, params = scope_clause(user, module)
        for row in con.execute(
            f'SELECT id,"{title}" AS t FROM "{module}" '
            f'WHERE deleted=0 AND {scoped} AND "{title}" LIKE ? LIMIT 5',
            params + [f"%{q}%"],
        ):
            out.append({"module": module, "id": row["id"], "title": row["t"],
                        "icon": meta["icon"], "label_en": meta["label_en"], "label_ar": meta["label_ar"]})
    return out[:25]


@app.get("/api/timeline")
def timeline(user=Depends(current_user)):
    if user["role"] == "agent":
        rows = con.execute(
            "SELECT a.*,u.name uname FROM audit a LEFT JOIN users u ON u.id=a.user_id "
            "WHERE a.user_id=? ORDER BY a.id DESC LIMIT 40", (user["id"],)
        )
    else:
        rows = con.execute(
            "SELECT a.*,u.name uname FROM audit a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 40"
        )
    return [dict(row) for row in rows]


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
