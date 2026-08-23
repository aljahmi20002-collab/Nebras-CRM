"""Platform layer: 360° view, omnichannel timeline, custom fields (no-code),
saved dashboards, API keys, integrations catalogue and WhatsApp/social capture.
"""
import os, json, secrets, hmac, hashlib, datetime, math
from typing import Optional
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

from authz import record_or_404, scope_clause

con = None

CHANNELS = {
    "email":     {"ar": "بريد إلكتروني", "en": "Email", "icon": "✉️"},
    "call":      {"ar": "مكالمة", "en": "Call", "icon": "📞"},
    "meeting":   {"ar": "اجتماع", "en": "Meeting", "icon": "🤝"},
    "whatsapp":  {"ar": "واتساب", "en": "WhatsApp", "icon": "💬"},
    "sms":       {"ar": "رسالة نصية", "en": "SMS", "icon": "📱"},
    "portal":    {"ar": "بوابة العملاء", "en": "Portal", "icon": "🌐"},
    "facebook":  {"ar": "فيسبوك", "en": "Facebook", "icon": "📘"},
    "instagram": {"ar": "إنستغرام", "en": "Instagram", "icon": "📸"},
    "x":         {"ar": "منصة X", "en": "X", "icon": "✖️"},
    "linkedin":  {"ar": "لينكدإن", "en": "LinkedIn", "icon": "💼"},
    "web":       {"ar": "الموقع", "en": "Website", "icon": "🌍"},
    "note":      {"ar": "ملاحظة", "en": "Note", "icon": "📝"},
}

INTEGRATIONS = [
    {"code": "whatsapp", "name_en": "WhatsApp Business", "name_ar": "واتساب للأعمال",
     "cat": "messaging", "icon": "💬", "status": "available",
     "desc_ar": "استقبال وإرسال الرسائل وتسجيلها تلقائياً على سجل العميل",
     "webhook": "/api/hooks/whatsapp"},
    {"code": "telegram", "name_en": "Telegram", "name_ar": "تيليجرام", "cat": "messaging",
     "icon": "✈️", "status": "available", "desc_ar": "قناة رسائل إضافية", "webhook": "/api/hooks/telegram"},
    {"code": "facebook", "name_en": "Facebook Lead Ads", "name_ar": "إعلانات فيسبوك",
     "cat": "marketing", "icon": "📘", "status": "available",
     "desc_ar": "سحب العملاء المحتملين من نماذج فيسبوك", "webhook": "/api/hooks/leadform"},
    {"code": "webform", "name_en": "Web Forms", "name_ar": "نماذج الموقع", "cat": "marketing",
     "icon": "📝", "status": "active", "desc_ar": "نموذج على موقعك ينشئ عميلاً محتملاً فوراً",
     "webhook": "/api/hooks/leadform"},
    {"code": "woocommerce", "name_en": "WooCommerce", "name_ar": "ووكومرس", "cat": "ecommerce",
     "icon": "🛒", "status": "available", "desc_ar": "مزامنة الطلبات والعملاء",
     "webhook": "/api/hooks/order"},
    {"code": "shopify", "name_en": "Shopify", "name_ar": "شوبيفاي", "cat": "ecommerce",
     "icon": "🛍️", "status": "available", "desc_ar": "مزامنة الطلبات والمنتجات",
     "webhook": "/api/hooks/order"},
    {"code": "quickbooks", "name_en": "QuickBooks", "name_ar": "كويك بوكس", "cat": "erp",
     "icon": "📊", "status": "available", "desc_ar": "مزامنة الفواتير والمدفوعات مع المحاسبة"},
    {"code": "odoo_erp", "name_en": "Odoo ERP", "name_ar": "أودو", "cat": "erp", "icon": "🏭",
     "status": "available", "desc_ar": "ربث ثنائي الاتجاه مع المخزون والمحاسبة"},
    {"code": "onyx_erp", "name_en": "Onyx Pro ERP", "name_ar": "أونكس برو", "cat": "erp",
     "icon": "🧾", "status": "available", "desc_ar": "تكامل مع أنظمة المحاسبة المحلية"},
    {"code": "gmail", "name_en": "Gmail / SMTP", "name_ar": "بريد جوجل", "cat": "productivity",
     "icon": "📧", "status": "active", "desc_ar": "إرسال واستقبال البريد داخل النظام"},
    {"code": "gcal", "name_en": "Google Calendar", "name_ar": "تقويم جوجل", "cat": "productivity",
     "icon": "📅", "status": "available", "desc_ar": "مزامنة الاجتماعات والمهام"},
    {"code": "slack", "name_en": "Slack", "name_ar": "سلاك", "cat": "productivity", "icon": "💼",
     "status": "available", "desc_ar": "إشعارات الصفقات في قنوات الفريق"},
    {"code": "zapier", "name_en": "Zapier", "name_ar": "زابير", "cat": "automation", "icon": "⚡",
     "status": "available", "desc_ar": "اربط مع 5000+ تطبيق دون كود"},
    {"code": "stripe", "name_en": "Stripe", "name_ar": "سترايب", "cat": "payments", "icon": "🟦",
     "status": "active", "desc_ar": "بوابة دفع دولية", "webhook": "/pay/webhook"},
    {"code": "tap", "name_en": "Tap Payments", "name_ar": "تاب", "cat": "payments", "icon": "🟢",
     "status": "active", "desc_ar": "بوابة دفع خليجية", "webhook": "/pay/webhook"},
    {"code": "jawali", "name_en": "Jawali Wallet", "name_ar": "محفظة جوالي", "cat": "payments",
     "icon": "📱", "status": "active", "desc_ar": "محفظة جوال يمنية"},
    {"code": "twilio", "name_en": "Twilio SMS", "name_ar": "تويليو", "cat": "messaging",
     "icon": "📲", "status": "available", "desc_ar": "رسائل نصية جماعية"},
    {"code": "powerbi", "name_en": "Power BI", "name_ar": "باور بي آي", "cat": "analytics",
     "icon": "📈", "status": "available", "desc_ar": "تصدير البيانات للتحليل المتقدم"},
]

FIELD_TYPES = {
    "text": {"ar": "نص", "en": "Text"}, "textarea": {"ar": "نص طويل", "en": "Long text"},
    "number": {"ar": "رقم", "en": "Number"}, "currency": {"ar": "مبلغ", "en": "Currency"},
    "date": {"ar": "تاريخ", "en": "Date"}, "select": {"ar": "قائمة", "en": "Dropdown"},
    "checkbox": {"ar": "خانة اختيار", "en": "Checkbox"}, "email": {"ar": "بريد", "en": "Email"},
    "phone": {"ar": "هاتف", "en": "Phone"}, "url": {"ar": "رابط", "en": "URL"},
}


def init_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS interactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, record_id INTEGER,
        account_id INTEGER, contact_id INTEGER, channel TEXT, direction TEXT,
        subject TEXT, body TEXT, actor TEXT, external_id TEXT, meta TEXT,
        occurred_at TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS custom_fields(
        id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, name TEXT, label_ar TEXT,
        label_en TEXT, type TEXT, options TEXT, required INTEGER DEFAULT 0,
        show_in_list INTEGER DEFAULT 0, position INTEGER DEFAULT 100,
        created_at TEXT, UNIQUE(module, name))""")
    c.execute("""CREATE TABLE IF NOT EXISTS dashboards(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, owner_id INTEGER,
        shared INTEGER DEFAULT 0, layout TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS api_keys(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, prefix TEXT, hash TEXT,
        scopes TEXT DEFAULT 'read', active INTEGER DEFAULT 1, last_used TEXT,
        calls INTEGER DEFAULT 0, created_by INTEGER, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS integrations(
        code TEXT PRIMARY KEY, enabled INTEGER DEFAULT 0, config TEXT, updated_at TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS ix_int_acc ON interactions(account_id)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_int_mod ON interactions(module,record_id)")
    c.commit()


def log_interaction(module, rid, channel, subject="", body="", direction="in",
                    account_id=None, contact_id=None, actor="", external_id=None, meta=None):
    import db as D
    con.execute("""INSERT INTO interactions(module,record_id,account_id,contact_id,channel,
        direction,subject,body,actor,external_id,meta,occurred_at,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (module, rid, account_id, contact_id, channel, direction, subject, body, actor,
         external_id, json.dumps(meta or {}, ensure_ascii=False), D.now(), D.now()))
    con.commit()


def _f(v):
    try: return float(v or 0)
    except (TypeError, ValueError): return 0.0


def register(app, current_user, require):

    # ---------------- 360 view ----------------
    @app.get("/api/360/{module}/{rid}")
    def view360(module: str, rid: int, user=Depends(current_user)):
        """Everything about a customer on one screen."""
        if module not in ("accounts", "contacts", "leads"):
            raise HTTPException(400, "Unsupported module")
        rec = record_or_404(con, module, rid, user)
        rec = dict(rec)
        aid = rid if module == "accounts" else rec.get("account_id")
        try: aid = int(aid)
        except (TypeError, ValueError): aid = None

        out = {"record": rec, "module": module, "account_id": aid}
        if aid:
            out["contacts"] = [dict(r) for r in con.execute(
                "SELECT id,name,title,email,phone FROM contacts WHERE deleted=0 AND CAST(account_id AS INTEGER)=?", (aid,))]
            out["deals"] = [dict(r) for r in con.execute(
                """SELECT id,name,amount,stage,probability,closing_date FROM deals
                   WHERE deleted=0 AND CAST(account_id AS INTEGER)=? ORDER BY id DESC LIMIT 20""", (aid,))]
            out["opportunities"] = [dict(r) for r in con.execute(
                """SELECT id,name,value,stage,outcome FROM opportunities
                   WHERE deleted=0 AND CAST(account_id AS INTEGER)=? ORDER BY id DESC LIMIT 10""", (aid,))]
            out["invoices"] = [dict(r) for r in con.execute(
                """SELECT id,subject,amount,paid_amount,status,due_date FROM invoices
                   WHERE deleted=0 AND CAST(account_id AS INTEGER)=? ORDER BY id DESC LIMIT 20""", (aid,))]
            out["quotes"] = [dict(r) for r in con.execute(
                """SELECT id,subject,amount,status,valid_until FROM quotes
                   WHERE deleted=0 AND CAST(account_id AS INTEGER)=? ORDER BY id DESC LIMIT 10""", (aid,))]
            out["tickets"] = [dict(r) for r in con.execute(
                """SELECT id,subject,status,priority,due_date FROM tickets
                   WHERE deleted=0 AND CAST(account_id AS INTEGER)=? ORDER BY id DESC LIMIT 15""", (aid,))]
            out["payments"] = [dict(r) for r in con.execute(
                """SELECT p.id,p.amount,p.method,p.status,p.paid_at FROM payments p
                   JOIN invoices i ON i.id=p.invoice_id
                   WHERE CAST(i.account_id AS INTEGER)=? ORDER BY p.id DESC LIMIT 15""", (aid,))]
            rev = _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0
                AND stage='Closed Won' AND CAST(account_id AS INTEGER)=?""", (aid,)).fetchone()[0])
            outstanding = _f(con.execute("""SELECT SUM(COALESCE(amount,0)-COALESCE(paid_amount,0))
                FROM invoices WHERE deleted=0 AND CAST(account_id AS INTEGER)=?
                AND status NOT IN ('Paid','Cancelled')""", (aid,)).fetchone()[0])
            import loyalty as LOY
            _b, pts = LOY.compute("customer", aid)
            out["kpi"] = {"revenue": rev, "outstanding": outstanding,
                          "deals": len(out["deals"]), "open_tickets":
                              sum(1 for t in out["tickets"] if t["status"] != "Closed"),
                          "loyalty_points": pts, "loyalty_tier": LOY.tier_for(pts)}
            import ai as AI
            out["ai"] = AI.next_best_action("accounts", aid) if module == "accounts" else None

        # unified omnichannel timeline
        tl = []
        w = "account_id=?" if aid else "module=? AND record_id=?"
        p = [aid] if aid else [module, rid]
        for r in con.execute(f"""SELECT * FROM interactions WHERE {w}
                                 ORDER BY occurred_at DESC LIMIT 60""", p):
            d = dict(r); d["kind"] = "interaction"; tl.append(d)
        for r in con.execute("""SELECT * FROM emails WHERE module=? AND record_id=?
                                ORDER BY id DESC LIMIT 25""", (module, rid)):
            d = dict(r)
            tl.append({"kind": "interaction", "channel": "email", "direction": "out",
                       "subject": d["subject"], "body": d["body"], "actor": d["to_email"],
                       "occurred_at": d["created_at"], "meta": "{}"})
        for r in con.execute("""SELECT n.*,u.name uname FROM notes n LEFT JOIN users u ON u.id=n.user_id
                                WHERE n.module=? AND n.record_id=? ORDER BY n.id DESC LIMIT 25""",
                             (module, rid)):
            d = dict(r)
            tl.append({"kind": "interaction", "channel": "note", "direction": "internal",
                       "subject": "ملاحظة", "body": d["body"], "actor": d.get("uname") or "",
                       "occurred_at": d["created_at"], "meta": "{}"})
        if aid:
            for r in con.execute("""SELECT id,subject,type,status,due_date,created_at
                FROM activities WHERE deleted=0 AND related_to LIKE ? ORDER BY id DESC LIMIT 25""",
                (f"%accounts#{aid}%",)):
                d = dict(r)
                tl.append({"kind": "interaction",
                           "channel": {"Call": "call", "Meeting": "meeting", "Email": "email"}.get(d["type"], "note"),
                           "direction": "out", "subject": d["subject"], "body": d.get("status", ""),
                           "actor": "", "occurred_at": d["created_at"], "meta": "{}"})
        tl.sort(key=lambda x: x.get("occurred_at") or "", reverse=True)
        out["timeline"] = tl[:80]
        out["channels"] = CHANNELS
        counts = {}
        for t in out["timeline"]:
            counts[t["channel"]] = counts.get(t["channel"], 0) + 1
        out["channel_counts"] = counts
        return out

    class Interaction(BaseModel):
        module: str
        record_id: int
        channel: str
        subject: str = ""
        body: str = ""
        direction: str = "out"
        account_id: Optional[int] = None

    @app.post("/api/interactions")
    def add_interaction(b: Interaction, user=Depends(current_user)):
        if user["role"] == "readonly":
            raise HTTPException(403, "Read-only user")
        from schema import MODULES
        if b.module not in MODULES:
            raise HTTPException(400, "Unknown module")
        if b.channel not in CHANNELS or b.direction not in {"in", "out", "internal"}:
            raise HTTPException(400, "Unknown channel or direction")
        if len(b.subject) > 500 or len(b.body) > 20_000:
            raise HTTPException(400, "Interaction is too long")
        record_or_404(con, b.module, b.record_id, user)
        aid = b.account_id
        if not aid and b.module == "accounts":
            aid = b.record_id
        if aid:
            record_or_404(con, "accounts", int(aid), user)
        log_interaction(b.module, b.record_id, b.channel, b.subject, b.body,
                        b.direction, aid, actor=user["name"])
        return {"ok": True}

    @app.get("/api/interactions/stats")
    def interaction_stats(user=Depends(current_user)):
        if user["role"] == "agent":
            raise HTTPException(403, "Manager permissions required")
        rows = [dict(r) for r in con.execute("""
            SELECT channel k, COUNT(*) n, SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END) inbound
            FROM interactions GROUP BY channel ORDER BY n DESC""")]
        for r in rows:
            c = CHANNELS.get(r["k"], {})
            r["ar"] = c.get("ar", r["k"]); r["en"] = c.get("en", r["k"]); r["icon"] = c.get("icon", "")
        return rows

    # ---------------- custom fields (no-code) ----------------
    @app.get("/api/custom-fields")
    def list_cf(module: str = "", user=Depends(current_user)):
        w = "WHERE module=?" if module else ""
        p = [module] if module else []
        return {"fields": [dict(r) for r in con.execute(
            f"SELECT * FROM custom_fields {w} ORDER BY module,position", p)],
            "types": FIELD_TYPES}

    class CF(BaseModel):
        module: str
        name: str
        label_ar: str
        label_en: str = ""
        type: str = "text"
        options: str = ""
        required: bool = False
        show_in_list: bool = False

    @app.post("/api/custom-fields")
    def add_cf(b: CF, user=Depends(current_user)):
        require(user, "admin")
        import db as D
        from schema import MODULES
        if b.module not in MODULES: raise HTTPException(400, "Unknown module")
        if b.type not in FIELD_TYPES: raise HTTPException(400, "Unknown type")
        name = "cf_" + "".join(ch if ch.isalnum() else "_" for ch in b.name.strip().lower())[:40]
        if not name.strip("cf_"): raise HTTPException(400, "Invalid field name")
        existing = {r["name"] for r in con.execute(f'PRAGMA table_info("{b.module}")')}
        if name in existing: raise HTTPException(400, "Field already exists")
        sqlt = "REAL" if b.type in ("number", "currency") else "TEXT"
        con.execute(f'ALTER TABLE "{b.module}" ADD COLUMN "{name}" {sqlt}')
        con.execute("""INSERT INTO custom_fields(module,name,label_ar,label_en,type,options,
            required,show_in_list,position,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (b.module, name, b.label_ar, b.label_en or b.label_ar, b.type, b.options,
             1 if b.required else 0, 1 if b.show_in_list else 0, 100, D.now()))
        con.commit()
        return {"ok": True, "name": name, "restart_hint": False}

    @app.delete("/api/custom-fields/{cid}")
    def del_cf(cid: int, user=Depends(current_user)):
        require(user, "admin")
        # column is kept (SQLite drop-column is destructive); definition removed
        con.execute("DELETE FROM custom_fields WHERE id=?", (cid,)); con.commit()
        return {"ok": True}

    # ---------------- saved dashboards ----------------
    @app.get("/api/dashboards")
    def list_dash(user=Depends(current_user)):
        return [dict(r) for r in con.execute(
            "SELECT * FROM dashboards WHERE owner_id=? OR shared=1 ORDER BY id DESC", (user["id"],))]

    class Dash(BaseModel):
        name: str
        layout: list
        shared: bool = False

    @app.post("/api/dashboards")
    def save_dash(b: Dash, user=Depends(current_user)):
        if user["role"] == "readonly":
            raise HTTPException(403, "Read-only user")
        if not b.name.strip() or len(b.name) > 200 or len(b.layout) > 50:
            raise HTTPException(400, "Invalid dashboard")
        if b.shared and user["role"] not in ("admin", "manager"):
            raise HTTPException(403, "Only managers can share dashboards")
        import db as D
        did = con.execute("""INSERT INTO dashboards(name,owner_id,shared,layout,created_at)
            VALUES(?,?,?,?,?)""", (b.name.strip(), user["id"], 1 if b.shared else 0,
            json.dumps(b.layout, ensure_ascii=False), D.now())).lastrowid
        con.commit(); return {"id": did}

    @app.delete("/api/dashboards/{did}")
    def del_dash(did: int, user=Depends(current_user)):
        r = con.execute("SELECT owner_id FROM dashboards WHERE id=?", (did,)).fetchone()
        if not r: raise HTTPException(404, "Not found")
        if r["owner_id"] != user["id"] and user["role"] != "admin":
            raise HTTPException(403, "Not your dashboard")
        con.execute("DELETE FROM dashboards WHERE id=?", (did,)); con.commit()
        return {"ok": True}

    @app.get("/api/widget")
    def widget(module: str, metric: str = "count", field: str = "", group_by: str = "",
               filter_field: str = "", filter_value: str = "", user=Depends(current_user)):
        """Generic widget data source — powers the custom dashboard builder."""
        from schema import MODULES
        if module not in MODULES: raise HTTPException(400, "Unknown module")
        cols = [f["name"] for f in MODULES[module]["fields"]] + \
               [r["name"] for r in con.execute("SELECT name FROM custom_fields WHERE module=?", (module,))]
        scoped, scope_params = scope_clause(user, module)
        w, p = ["deleted=0", scoped], list(scope_params)
        if filter_field and filter_field in cols and filter_value:
            w.append(f'"{filter_field}"=?'); p.append(filter_value)
        agg = {"count": "COUNT(*)", "sum": f'SUM("{field}")', "avg": f'AVG("{field}")',
               "max": f'MAX("{field}")', "min": f'MIN("{field}")'}.get(metric)
        if metric != "count" and field not in cols: raise HTTPException(400, "Bad field")
        if not agg: raise HTTPException(400, "Bad metric")
        if group_by:
            if group_by not in cols: raise HTTPException(400, "Bad group_by")
            rows = con.execute(f'''SELECT COALESCE("{group_by}",'—') k, {agg} v FROM "{module}"
                WHERE {" AND ".join(w)} GROUP BY 1 ORDER BY 2 DESC LIMIT 30''', p).fetchall()
            return {"rows": [{"k": r["k"], "v": _f(r["v"])} for r in rows]}
        v = con.execute(f'SELECT {agg} v FROM "{module}" WHERE {" AND ".join(w)}', p).fetchone()["v"]
        return {"value": _f(v)}

    # ---------------- API keys & public API ----------------
    @app.get("/api/keys")
    def list_keys(user=Depends(current_user)):
        require(user, "admin")
        return [dict(r) for r in con.execute(
            "SELECT id,name,prefix,scopes,active,last_used,calls,created_at FROM api_keys ORDER BY id DESC")]

    class KeyBody(BaseModel):
        name: str
        scopes: str = "read"

    @app.post("/api/keys")
    def create_key(b: KeyBody, user=Depends(current_user)):
        require(user, "admin")
        scopes = {scope.strip() for scope in (b.scopes or "").split(",") if scope.strip()}
        if not scopes or not scopes <= {"read", "write"}:
            raise HTTPException(400, "Scopes must be read, write, or read,write")
        name = b.name.strip()
        if not name or len(name) > 200:
            raise HTTPException(400, "API key name is required")
        import db as D
        raw = "nx_" + secrets.token_urlsafe(30)
        pref = raw[:11]
        con.execute("""INSERT INTO api_keys(name,prefix,hash,scopes,active,created_by,created_at)
            VALUES(?,?,?,?,1,?,?)""", (name, pref,
            hashlib.sha256(raw.encode()).hexdigest(), ",".join(sorted(scopes)), user["id"], D.now()))
        con.commit()
        return {"key": raw, "prefix": pref,
                "note": "احفظ المفتاح الآن — لن يُعرض مرة أخرى"}

    @app.delete("/api/keys/{kid}")
    def del_key(kid: int, user=Depends(current_user)):
        require(user, "admin")
        con.execute("DELETE FROM api_keys WHERE id=?", (kid,)); con.commit()
        return {"ok": True}

    def check_api_key(key: str, need_write=False):
        if not key: raise HTTPException(401, "API key required")
        h = hashlib.sha256(key.encode()).hexdigest()
        r = con.execute("SELECT * FROM api_keys WHERE hash=? AND active=1", (h,)).fetchone()
        if not r: raise HTTPException(401, "Invalid API key")
        scopes = {scope.strip() for scope in (r["scopes"] or "").split(",") if scope.strip()}
        if need_write and "write" not in scopes:
            raise HTTPException(403, "Key lacks write scope")
        import db as D
        con.execute("UPDATE api_keys SET last_used=?, calls=calls+1 WHERE id=?", (D.now(), r["id"]))
        con.commit()
        return dict(r)

    @app.get("/api/v1/{module}")
    def public_list(module: str, request: Request, limit: int = 50, offset: int = 0):
        from schema import MODULES
        check_api_key(request.headers.get("X-API-Key", ""))
        if module not in MODULES:
            raise HTTPException(404, "Unknown module")
        if not 1 <= limit <= 200 or offset < 0:
            raise HTTPException(400, "limit must be 1-200 and offset cannot be negative")
        rows = con.execute(f'SELECT * FROM "{module}" WHERE deleted=0 LIMIT ? OFFSET ?',
                           (limit, offset)).fetchall()
        total = con.execute(f'SELECT COUNT(*) n FROM "{module}" WHERE deleted=0').fetchone()["n"]
        return {"data": [dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}

    @app.post("/api/v1/{module}")
    async def public_create(module: str, request: Request):
        from schema import MODULES
        import db as D
        check_api_key(request.headers.get("X-API-Key", ""), need_write=True)
        if module not in MODULES: raise HTTPException(404, "Unknown module")
        body = await request.json()
        cols = {f["name"] for f in MODULES[module]["fields"]}
        data = {k: v for k, v in body.items() if k in cols}
        if not data: raise HTTPException(400, "No valid fields")
        data.update(created_at=D.now(), updated_at=D.now(), deleted=0)
        keys = list(data)
        rid = con.execute(f'INSERT INTO "{module}" ({",".join(chr(34)+k+chr(34) for k in keys)}) '
                          f'VALUES ({",".join("?"*len(keys))})', [data[k] for k in keys]).lastrowid
        con.commit()
        return {"id": rid}

    # ---------------- integrations & inbound hooks ----------------
    @app.get("/api/integrations")
    def list_int(user=Depends(current_user)):
        saved = {r["code"]: dict(r) for r in con.execute("SELECT * FROM integrations")}
        out = []
        for i in INTEGRATIONS:
            d = dict(i)
            s = saved.get(i["code"])
            d["enabled"] = bool(s and s["enabled"])
            out.append(d)
        cats = {"messaging": {"ar": "المراسلة", "en": "Messaging"},
                "marketing": {"ar": "التسويق", "en": "Marketing"},
                "ecommerce": {"ar": "التجارة الإلكترونية", "en": "E-commerce"},
                "erp": {"ar": "المحاسبة و ERP", "en": "ERP & Accounting"},
                "productivity": {"ar": "الإنتاجية", "en": "Productivity"},
                "automation": {"ar": "الأتمتة", "en": "Automation"},
                "payments": {"ar": "المدفوعات", "en": "Payments"},
                "analytics": {"ar": "التحليلات", "en": "Analytics"}}
        return {"integrations": out, "categories": cats}

    @app.put("/api/integrations/{code}")
    def toggle_int(code: str, body: dict, user=Depends(current_user)):
        require(user, "admin")
        if code not in {item["code"] for item in INTEGRATIONS}:
            raise HTTPException(404, "Unknown integration")
        if not isinstance(body, dict) or not isinstance(body.get("config", {}), dict):
            raise HTTPException(400, "Invalid integration configuration")
        import db as D
        con.execute("""INSERT INTO integrations(code,enabled,config,updated_at) VALUES(?,?,?,?)
            ON CONFLICT(code) DO UPDATE SET enabled=excluded.enabled,
            config=excluded.config, updated_at=excluded.updated_at""",
            (code, 1 if body.get("enabled") else 0,
             json.dumps(body.get("config", {}), ensure_ascii=False), D.now()))
        con.commit(); return {"ok": True}

    def _find_by_phone(phone):
        digits = "".join(c for c in (phone or "") if c.isdigit())[-9:]
        if not digits: return None, None
        c = con.execute("""SELECT id, account_id FROM contacts WHERE deleted=0
            AND replace(replace(replace(phone,'-',''),' ',''),'+','') LIKE ?""",
            (f"%{digits}%",)).fetchone()
        if c: return c["id"], c["account_id"]
        return None, None

    @app.post("/api/hooks/whatsapp")
    async def hook_whatsapp(request: Request):
        """Inbound WhatsApp Business message -> logged on the customer timeline."""
        check_api_key(request.headers.get("X-API-Key", ""), need_write=True)
        try:
            b = await request.json()
        except (TypeError, ValueError, json.JSONDecodeError):
            raise HTTPException(400, "Invalid JSON payload")
        if not isinstance(b, dict):
            raise HTTPException(400, "Invalid JSON payload")
        phone = str(b.get("from") or b.get("phone") or "").strip()
        text = str(b.get("text") or b.get("body") or "").strip()
        external_id = str(b.get("message_id") or "").strip()[:200]
        if not phone or not text or len(text) > 20_000:
            raise HTTPException(400, "phone and text are required")
        if external_id:
            existing = con.execute("SELECT module,record_id FROM interactions WHERE channel='whatsapp' AND external_id=?",
                                   (external_id,)).fetchone()
            if existing:
                return {"ok": True, "duplicate": True, "module": existing["module"],
                        "record_id": existing["record_id"]}
        cid, aid = _find_by_phone(phone)
        module, rid = ("contacts", cid) if cid else ("leads", 0)
        if not cid:
            import db as D
            name = str(b.get("name") or phone).strip()[:200]
            rid = con.execute("""INSERT INTO leads(created_at,updated_at,deleted,name,phone,
                status,source,rating,description) VALUES(?,?,0,?,?,'New','Web','Warm',?)""",
                (D.now(), D.now(), name, phone[:100], "أول رسالة واتساب: " + text[:200])).lastrowid
            con.commit()
        log_interaction(module, rid or 0, "whatsapp", "رسالة واتساب", text, "in",
                        int(aid) if aid else None, cid, actor=phone[:100], external_id=external_id or None)
        return {"ok": True, "module": module, "record_id": rid, "matched": bool(cid)}

    @app.post("/api/hooks/leadform")
    async def hook_leadform(request: Request):
        """Website / Facebook lead form -> new lead + AI score."""
        check_api_key(request.headers.get("X-API-Key", ""), need_write=True)
        import db as D, ai as AI
        try:
            b = await request.json()
        except (TypeError, ValueError, json.JSONDecodeError):
            raise HTTPException(400, "Invalid JSON payload")
        if not isinstance(b, dict):
            raise HTTPException(400, "Invalid JSON payload")
        name, email = str(b.get("name") or "").strip(), str(b.get("email") or "").strip()
        if not name and not email:
            raise HTTPException(400, "name or email required")
        if len(name) > 200 or len(email) > 320 or (email and "@" not in email):
            raise HTTPException(400, "Invalid lead data")
        rid = con.execute("""INSERT INTO leads(created_at,updated_at,deleted,name,company,email,
            phone,city,status,source,rating,description) VALUES(?,?,0,?,?,?,?,?,'New',?,'Warm',?)""",
            (D.now(), D.now(), (name or email)[:200], str(b.get("company", ""))[:200],
             email, str(b.get("phone", ""))[:100], str(b.get("city", ""))[:200],
             str(b.get("source", "Web"))[:100], str(b.get("message", ""))[:20_000])).lastrowid
        con.commit()
        log_interaction("leads", rid, b.get("channel", "web"), "نموذج ويب",
                        b.get("message", ""), "in", actor=b.get("email", ""))
        l = dict(con.execute("SELECT * FROM leads WHERE id=?", (rid,)).fetchone())
        s = AI.score_lead(l)
        for m in con.execute("SELECT id FROM users WHERE role IN ('admin','manager') AND active=1"):
            con.execute("""INSERT INTO notifications(user_id,title,body,read,created_at)
                VALUES(?,?,?,0,?)""", (m["id"], "🌐 عميل محتمل جديد",
                f'{l["name"]} — درجة {s["score"]} ({s["band_ar"]})', D.now()))
        con.commit()
        return {"id": rid, "score": s["score"], "band": s["band"]}

    @app.post("/api/hooks/order")
    async def hook_order(request: Request):
        """E-commerce order -> account + invoice."""
        check_api_key(request.headers.get("X-API-Key", ""), need_write=True)
        import db as D
        try:
            b = await request.json()
        except (TypeError, ValueError, json.JSONDecodeError):
            raise HTTPException(400, "Invalid JSON payload")
        if not isinstance(b, dict):
            raise HTTPException(400, "Invalid JSON payload")
        email = str(b.get("email", "")).strip()
        name = str(b.get("customer") or email).strip()
        try:
            total = float(b.get("total"))
        except (TypeError, ValueError):
            raise HTTPException(400, "A valid order total is required")
        if not math.isfinite(total) or total <= 0 or not name or len(name) > 200:
            raise HTTPException(400, "A valid order total and customer are required")
        if email and (len(email) > 320 or "@" not in email):
            raise HTTPException(400, "Invalid customer email")
        c = con.execute("SELECT id,account_id FROM contacts WHERE deleted=0 AND lower(email)=lower(?)",
                        (email,)).fetchone()
        if c and c["account_id"]:
            aid = int(c["account_id"])
        else:
            aid = con.execute("""INSERT INTO accounts(created_at,updated_at,deleted,name,type)
                VALUES(?,?,0,?,'Customer')""", (D.now(), D.now(), name)).lastrowid
            if email:
                con.execute("""INSERT INTO contacts(created_at,updated_at,deleted,name,email,account_id)
                    VALUES(?,?,0,?,?,?)""", (D.now(), D.now(), name, email, aid))
        iid = con.execute("""INSERT INTO invoices(created_at,updated_at,deleted,subject,account_id,
            status,invoice_date,amount,paid_amount) VALUES(?,?,0,?,?,?,?,?,?)""",
            (D.now(), D.now(), f'طلب متجر #{b.get("order_id","")}', aid,
             "Paid" if b.get("paid") else "Sent", datetime.date.today().isoformat(),
             total, total if b.get("paid") else 0)).lastrowid
        con.commit()
        log_interaction("accounts", aid, "web", "طلب من المتجر",
                        f'#{b.get("order_id","")} — {total}', "in", aid)
        return {"account_id": aid, "invoice_id": iid}
