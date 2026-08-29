"""Email integration — templates, outbox, delivery tracking, SMTP and Resend.

Works out of the box in SANDBOX mode (messages are stored and viewable in the
staff Email screen). Administrators can select SMTP or Resend in Delivery
Settings; both transports share the same outbox and template workflow.
"""
import os, re, json, smtplib, threading, datetime
from urllib import error as urlerror
from urllib import request as urlrequest
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

import db as D
from authz import record_or_404
from schema import MODULES

mail = APIRouter()
con = None  # injected

DEFAULT_TEMPLATES = [
    ("welcome_lead", "Welcome / ترحيب بعميل محتمل", "Welcome to {{company}}, {{name}}!",
     "Hi {{name}},\n\nThank you for your interest in {{company}}. Our team will reach out shortly.\n\n"
     "مرحباً {{name}}،\n\nشكراً لاهتمامك بـ {{company}}. سيتواصل معك فريقنا قريباً.\n\n— {{owner}}"),
    ("quote_sent", "Quote sent / إرسال عرض سعر", "Your quote {{subject}} — {{amount}}",
     "Dear {{name}},\n\nPlease find your quote {{subject}} for {{amount}}, valid until {{valid_until}}.\n"
     "You can review and accept it in our customer portal.\n\n"
     "عزيزي {{name}}،\n\nنرفق عرض السعر {{subject}} بقيمة {{amount}}، صالح حتى {{valid_until}}.\n\n— {{owner}}"),
    ("invoice_due", "Invoice / إشعار فاتورة", "Invoice {{subject}} — {{amount}} due {{due_date}}",
     "Dear {{name}},\n\nInvoice {{subject}} for {{amount}} is due on {{due_date}}.\n"
     "Pay securely here: {{pay_link}}\n\n"
     "عزيزي {{name}}،\n\nفاتورة {{subject}} بقيمة {{amount}} مستحقة بتاريخ {{due_date}}.\n"
     "للدفع الآمن: {{pay_link}}\n\n— {{owner}}"),
    ("payment_receipt", "Payment receipt / إيصال دفع", "Payment received — {{amount}}",
     "Dear {{name}},\n\nWe received your payment of {{amount}} for {{subject}}. Thank you!\n\n"
     "عزيزي {{name}}،\n\nاستلمنا دفعتك بمبلغ {{amount}} عن {{subject}}. شكراً لك!\n\n— {{owner}}"),
    ("ticket_reply", "Ticket reply / رد على تذكرة", "Re: {{subject}} [#{{id}}]",
     "Hello {{name}},\n\n{{body}}\n\nView the full conversation in the customer portal.\n\n— {{owner}}"),
    ("portal_invite", "Portal invite / دعوة للبوابة", "Your {{company}} portal access",
     "Hello {{name}},\n\nYour customer portal account is ready.\n"
     "URL: {{portal_url}}\nEmail: {{email}}\nPassword: {{password}}\n\n"
     "مرحباً {{name}}،\n\nتم تفعيل حسابك في بوابة العملاء.\n\n— {{owner}}"),
]


def init_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS email_templates(
        id INTEGER PRIMARY KEY AUTOINCREMENT, code VARCHAR(100) UNIQUE, name TEXT,
        subject TEXT, body TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS emails(
        id INTEGER PRIMARY KEY AUTOINCREMENT, to_email TEXT, to_name TEXT,
        subject TEXT, body TEXT, status TEXT DEFAULT 'queued', error TEXT,
        module TEXT, record_id INTEGER, template TEXT, user_id INTEGER,
        opened INTEGER DEFAULT 0, provider VARCHAR(30), created_at TEXT, sent_at TEXT)""")
    # Avoid a failed duplicate ALTER on PostgreSQL: unlike SQLite/MariaDB, an
    # error leaves the whole transaction aborted until rollback.
    if "provider" not in D.table_columns(c, "emails"):
        c.execute("ALTER TABLE emails ADD COLUMN provider VARCHAR(30)")
    for code, name, subj, body in DEFAULT_TEMPLATES:
        if not c.execute("SELECT 1 FROM email_templates WHERE code=?", (code,)).fetchone():
            c.execute("INSERT INTO email_templates(code,name,subject,body,created_at) VALUES(?,?,?,?,?)",
                      (code, name, subj, body, D.now()))
    smtp_configured = c.execute("SELECT \"value\" FROM settings WHERE \"key\"='smtp_host'").fetchone()
    default_provider = "smtp" if smtp_configured and smtp_configured["value"] else "sandbox"
    for k, v in [("email_provider", default_provider),
                 ("smtp_host", ""), ("smtp_port", "587"), ("smtp_user", ""), ("smtp_pass", ""),
                 ("smtp_from", "no-reply@nebrascrm.io"), ("smtp_tls", "1"),
                 ("resend_api_key", ""), ("resend_from", ""), ("resend_reply_to", ""),
                 ("company_name", "NebrasCRM"), ("base_url", ""),
                 ("openai_key", ""), ("openai_model", "gpt-4o-mini"),
                 ("openai_base", "https://api.openai.com/v1")]:
        if not c.execute("SELECT 1 FROM settings WHERE \"key\"=?", (k,)).fetchone():
            c.execute("INSERT INTO settings(\"key\",\"value\") VALUES(?,?)", (k, v))
    c.commit()


def cfg(key, default=""):
    r = con.execute("SELECT \"value\" FROM settings WHERE \"key\"=?", (key,)).fetchone()
    return (r["value"] if r else default) or default


EMAIL_SETTING_KEYS = {
    "email_provider", "smtp_host", "smtp_port", "smtp_user", "smtp_pass", "smtp_from", "smtp_tls",
    "resend_api_key", "resend_from", "resend_reply_to", "company_name", "base_url",
    "openai_key", "openai_model", "openai_base",
}
SENSITIVE_SETTING_KEYS = {"smtp_pass", "resend_api_key", "openai_key"}


def delivery_mode(values: dict | None = None) -> str:
    values = values or {}
    provider = str(values.get("email_provider") or "").strip().lower()
    if provider in {"sandbox", "smtp", "resend"}:
        return provider
    return "smtp" if values.get("smtp_host") else "sandbox"


def render(text: str, ctx: dict) -> str:
    def sub(m):
        return str(ctx.get(m.group(1).strip(), ""))
    return re.sub(r"\{\{([^}]+)\}\}", sub, text or "")


RESEND_EMAILS_URL = "https://api.resend.com/emails"


def _smtp_delivery(worker_cfg, to_email: str, subject: str, body: str):
    host = worker_cfg("smtp_host")
    if not host:
        raise RuntimeError("SMTP host is not configured")
    msg = MIMEMultipart()
    msg["From"] = worker_cfg("smtp_from", "no-reply@nebrascrm.io")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    smtp = smtplib.SMTP(host, int(worker_cfg("smtp_port", "587") or 587), timeout=15)
    try:
        if worker_cfg("smtp_tls", "1") == "1":
            smtp.starttls()
        if worker_cfg("smtp_user"):
            smtp.login(worker_cfg("smtp_user"), worker_cfg("smtp_pass"))
        smtp.sendmail(msg["From"], [to_email], msg.as_string())
    finally:
        smtp.quit()


def _resend_delivery(worker_cfg, to_email: str, subject: str, body: str):
    """Send a plain-text message through Resend's HTTPS API without extra deps."""
    api_key = worker_cfg("resend_api_key") or os.environ.get("CRM_RESEND_API_KEY", "")
    sender = worker_cfg("resend_from") or worker_cfg("smtp_from", "")
    reply_to = worker_cfg("resend_reply_to")
    if not api_key:
        raise RuntimeError("Resend API key is not configured")
    if not sender or "@" not in sender:
        raise RuntimeError("A verified Resend From address is required")
    payload = {"from": sender, "to": [to_email], "subject": subject, "text": body}
    if reply_to:
        payload["reply_to"] = reply_to
    request = urlrequest.Request(
        RESEND_EMAILS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(request, timeout=15) as response:
            # Consume the response so HTTP errors are surfaced before the email
            # row is marked sent. Resend responds with a JSON id on success.
            response.read()
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace").replace("\n", " ")[:220]
        raise RuntimeError(f"Resend {exc.code}: {detail or exc.reason}") from exc
    except urlerror.URLError as exc:
        raise RuntimeError(f"Resend connection failed: {exc.reason}") from exc


def _deliver_email(to_email, subject, body, eid):
    """Dispatch a queued message from an independent database connection."""
    worker = D.connect()

    def worker_cfg(key, default=""):
        row = worker.execute("SELECT \"value\" FROM settings WHERE \"key\"=?", (key,)).fetchone()
        return (row["value"] if row else default) or default

    provider = "sandbox"
    try:
        configured = worker_cfg("email_provider", "").strip().lower()
        # Existing installations had SMTP settings before email_provider existed.
        # Preserve that behavior when a provider has not been explicitly chosen.
        if configured in {"smtp", "resend", "sandbox"}:
            provider = configured
        elif worker_cfg("smtp_host"):
            provider = "smtp"
        if provider == "sandbox":
            worker.execute("UPDATE emails SET status='sandbox',provider=?,sent_at=? WHERE id=?",
                           (provider, D.now(), eid))
        elif provider == "smtp":
            _smtp_delivery(worker_cfg, to_email, subject, body)
            worker.execute("UPDATE emails SET status='sent',provider=?,sent_at=? WHERE id=?",
                           (provider, D.now(), eid))
        else:
            _resend_delivery(worker_cfg, to_email, subject, body)
            worker.execute("UPDATE emails SET status='sent',provider=?,sent_at=? WHERE id=?",
                           (provider, D.now(), eid))
    except Exception as exc:
        worker.execute("UPDATE emails SET status='failed',provider=?,error=?,sent_at=? WHERE id=?",
                       (provider, str(exc)[:300], D.now(), eid))
    finally:
        worker.commit()
        worker.close()


def send(to_email, subject, body, to_name="", module=None, record_id=None,
         template=None, user_id=None):
    """Queue + dispatch an email. Returns the email row id."""
    if not to_email:
        return None
    eid = con.execute("""INSERT INTO emails(to_email,to_name,subject,body,status,module,record_id,
        template,user_id,created_at) VALUES(?,?,?,?,'queued',?,?,?,?,?)""",
        (to_email, to_name, subject, body, module, record_id, template, user_id, D.now())).lastrowid
    con.commit()
    threading.Thread(target=_deliver_email, args=(to_email, subject, body, eid), daemon=True).start()
    return eid


def send_template(code, to_email, ctx, to_name="", module=None, record_id=None, user_id=None):
    tpl = con.execute("SELECT * FROM email_templates WHERE code=?", (code,)).fetchone()
    if not tpl:
        return None
    ctx = {"company": cfg("company_name", "NebrasCRM"), **ctx}
    return send(to_email, render(tpl["subject"], ctx), render(tpl["body"], ctx),
                to_name=to_name, module=module, record_id=record_id, template=code, user_id=user_id)


# ---------------- staff API ----------------
def register(app, current_user, require):
    @app.get("/api/email/templates")
    def tpls(user=Depends(current_user)):
        return [dict(r) for r in con.execute("SELECT * FROM email_templates ORDER BY id")]

    @app.put("/api/email/templates/{tid}")
    def upd_tpl(tid: int, body: dict, user=Depends(current_user)):
        require(user, "admin", "manager")
        con.execute("UPDATE email_templates SET name=?,subject=?,body=? WHERE id=?",
                    (body.get("name"), body.get("subject"), body.get("body"), tid))
        con.commit(); return {"ok": True}

    @app.get("/api/email/outbox")
    def outbox(q: str = "", status: str = "", user=Depends(current_user)):
        require(user, "admin", "manager")
        if len(q) > 250:
            raise HTTPException(400, "Search query is too long")
        w, p = ["1=1"], []
        if q:
            w.append("(to_email LIKE ? OR subject LIKE ?)"); p += [f"%{q}%"] * 2
        if status:
            w.append("status=?"); p.append(status)
        return [dict(r) for r in con.execute(
            f"SELECT * FROM emails WHERE {' AND '.join(w)} ORDER BY id DESC LIMIT 200", p)]

    @app.get("/api/email/thread/{module}/{rid}")
    def thread(module: str, rid: int, user=Depends(current_user)):
        if module not in MODULES:
            raise HTTPException(404, "Unknown module")
        record_or_404(con, module, rid, user)
        return [dict(r) for r in con.execute(
            "SELECT * FROM emails WHERE module=? AND record_id=? ORDER BY id DESC", (module, rid))]

    class Compose(BaseModel):
        to_email: str
        subject: str
        body: str
        to_name: str = ""
        module: Optional[str] = None
        record_id: Optional[int] = None

    @app.post("/api/email/send")
    def compose(b: Compose, user=Depends(current_user)):
        if user["role"] == "readonly":
            raise HTTPException(403, "Read-only user")
        email = b.to_email.strip()
        if len(email) > 320 or "@" not in email or "\n" in email or "\r" in email:
            raise HTTPException(400, "Invalid recipient email")
        if len(b.subject) > 500 or len(b.body) > 20_000 or len(b.to_name) > 200:
            raise HTTPException(400, "Email content is too long")
        if b.module or b.record_id:
            if not b.module or b.record_id is None or b.module not in MODULES:
                raise HTTPException(400, "A valid related record is required")
            record_or_404(con, b.module, b.record_id, user)
        ctx = {"owner": user["name"], "company": cfg("company_name", "NebrasCRM"), "name": b.to_name}
        eid = send(email, render(b.subject, ctx), render(b.body, ctx), to_name=b.to_name,
                   module=b.module, record_id=b.record_id, user_id=user["id"])
        r = con.execute("SELECT status FROM emails WHERE id=?", (eid,)).fetchone()
        return {"id": eid, "status": r["status"] if r else "queued"}

    @app.get("/api/email/settings")
    def get_settings(user=Depends(current_user)):
        require(user, "admin")
        d = {r["key"]: r["value"] for r in con.execute("SELECT * FROM settings")}
        d["email_provider"] = delivery_mode(d)
        for key in SENSITIVE_SETTING_KEYS:
            d[key] = "••••" if d.get(key) or (key == "resend_api_key" and os.environ.get("CRM_RESEND_API_KEY")) else ""
        d["resend_configured"] = bool(d.get("resend_api_key") or os.environ.get("CRM_RESEND_API_KEY"))
        d["mode"] = d["email_provider"]
        return d

    @app.put("/api/email/settings")
    def set_settings(body: dict, user=Depends(current_user)):
        require(user, "admin")
        provider = body.get("email_provider")
        if provider is not None and str(provider).strip().lower() not in {"sandbox", "smtp", "resend"}:
            raise HTTPException(400, "Unsupported email provider")
        for key in ("resend_from", "resend_reply_to", "smtp_from"):
            value = body.get(key)
            if value not in (None, "") and ("\n" in str(value) or "\r" in str(value) or "@" not in str(value)):
                raise HTTPException(400, f"Invalid {key}")
        if "smtp_port" in body:
            try:
                port = int(body["smtp_port"])
            except (TypeError, ValueError):
                raise HTTPException(400, "Invalid SMTP port")
            if not 1 <= port <= 65535:
                raise HTTPException(400, "Invalid SMTP port")
        for k, v in body.items():
            if k not in EMAIL_SETTING_KEYS:
                continue
            if k in SENSITIVE_SETTING_KEYS and v == "••••":
                continue
            value = str(v).strip() if k in {"email_provider", "resend_from", "resend_reply_to", "smtp_host", "smtp_user", "smtp_from"} else str(v)
            if len(value) > 2000:
                raise HTTPException(400, "Setting value is too long")
            con.execute("INSERT INTO settings(\"key\",\"value\") VALUES(?,?) "
                        "ON CONFLICT(\"key\") DO UPDATE SET \"value\"=excluded.\"value\"", (k, value))
        con.commit()
        current = {row["key"]: row["value"] for row in con.execute("SELECT * FROM settings")}
        return {"ok": True, "mode": delivery_mode(current)}

    @app.post("/api/email/test")
    def test_mail(body: dict, user=Depends(current_user)):
        require(user, "admin")
        recipient = str(body.get("to") or user["email"] or "").strip()
        if not recipient or "@" not in recipient or "\n" in recipient or "\r" in recipient:
            raise HTTPException(400, "Invalid recipient email")
        mode = delivery_mode({r["key"]: r["value"] for r in con.execute("SELECT * FROM settings")})
        eid = send(recipient, f"NebrasCRM {mode.title()} test",
                   f"This is a test message sent through NebrasCRM using {mode}. ✅",
                   user_id=user["id"])
        import time; time.sleep(1.2)
        r = con.execute("SELECT status,error,provider FROM emails WHERE id=?", (eid,)).fetchone()
        return {"status": r["status"], "error": r["error"], "provider": r["provider"] or mode}
