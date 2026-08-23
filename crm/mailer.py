"""Email integration — templates, outbox, delivery tracking, SMTP transport.

Works out of the box in SANDBOX mode (messages are stored and viewable in the
staff Email screen). Configure real SMTP in Settings to deliver for real.
"""
import os, re, json, smtplib, threading, datetime
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
        id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, name TEXT,
        subject TEXT, body TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS emails(
        id INTEGER PRIMARY KEY AUTOINCREMENT, to_email TEXT, to_name TEXT,
        subject TEXT, body TEXT, status TEXT DEFAULT 'queued', error TEXT,
        module TEXT, record_id INTEGER, template TEXT, user_id INTEGER,
        opened INTEGER DEFAULT 0, created_at TEXT, sent_at TEXT)""")
    for code, name, subj, body in DEFAULT_TEMPLATES:
        if not c.execute("SELECT 1 FROM email_templates WHERE code=?", (code,)).fetchone():
            c.execute("INSERT INTO email_templates(code,name,subject,body,created_at) VALUES(?,?,?,?,?)",
                      (code, name, subj, body, D.now()))
    for k, v in [("smtp_host", ""), ("smtp_port", "587"), ("smtp_user", ""), ("smtp_pass", ""),
                 ("smtp_from", "no-reply@nebrascrm.io"), ("smtp_tls", "1"),
                 ("company_name", "NebrasCRM"), ("base_url", ""),
                 ("openai_key", ""), ("openai_model", "gpt-4o-mini"),
                 ("openai_base", "https://api.openai.com/v1")]:
        if not c.execute("SELECT 1 FROM settings WHERE key=?", (k,)).fetchone():
            c.execute("INSERT INTO settings(key,value) VALUES(?,?)", (k, v))
    c.commit()


def cfg(key, default=""):
    r = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return (r["value"] if r else default) or default


def render(text: str, ctx: dict) -> str:
    def sub(m):
        return str(ctx.get(m.group(1).strip(), ""))
    return re.sub(r"\{\{([^}]+)\}\}", sub, text or "")


def _smtp_send(to_email, subject, body, eid):
    """Deliver using an independent SQLite connection (safe for the worker thread)."""
    worker = D.connect()
    def worker_cfg(key, default=""):
        row = worker.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return (row["value"] if row else default) or default
    try:
        host = worker_cfg("smtp_host")
        if not host:
            worker.execute("UPDATE emails SET status='sandbox', sent_at=? WHERE id=?", (D.now(), eid))
            worker.commit()
            return
        msg = MIMEMultipart()
        msg["From"] = worker_cfg("smtp_from", "no-reply@nebrascrm.io")
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        smtp = smtplib.SMTP(host, int(worker_cfg("smtp_port", "587") or 587), timeout=15)
        if worker_cfg("smtp_tls", "1") == "1":
            smtp.starttls()
        if worker_cfg("smtp_user"):
            smtp.login(worker_cfg("smtp_user"), worker_cfg("smtp_pass"))
        smtp.sendmail(msg["From"], [to_email], msg.as_string())
        smtp.quit()
        worker.execute("UPDATE emails SET status='sent', sent_at=? WHERE id=?", (D.now(), eid))
    except Exception as exc:
        worker.execute("UPDATE emails SET status='failed', error=?, sent_at=? WHERE id=?",
                       (str(exc)[:300], D.now(), eid))
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
    threading.Thread(target=_smtp_send, args=(to_email, subject, body, eid), daemon=True).start()
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
        d["smtp_pass"] = "••••" if d.get("smtp_pass") else ""
        d["openai_key"] = "••••" if d.get("openai_key") else ""
        d["mode"] = "smtp" if d.get("smtp_host") else "sandbox"
        return d

    @app.put("/api/email/settings")
    def set_settings(body: dict, user=Depends(current_user)):
        require(user, "admin")
        for k, v in body.items():
            if k in ("smtp_host", "smtp_port", "smtp_user", "smtp_pass", "smtp_from",
                     "smtp_tls", "company_name", "base_url",
                     "openai_key", "openai_model", "openai_base"):
                if k in ("smtp_pass", "openai_key") and v == "••••":
                    continue
                con.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, str(v)))
        con.commit(); return {"ok": True}

    @app.post("/api/email/test")
    def test_mail(body: dict, user=Depends(current_user)):
        require(user, "admin")
        eid = send(body.get("to") or user["email"], "NebrasCRM SMTP test",
                   "This is a test message from NebrasCRM. If you received it, SMTP works. ✅",
                   user_id=user["id"])
        import time; time.sleep(1.2)
        r = con.execute("SELECT status,error FROM emails WHERE id=?", (eid,)).fetchone()
        return {"status": r["status"], "error": r["error"]}
