"""Payment gateway integration.

Provider-agnostic: a `payments` ledger + hosted checkout links + webhook endpoint.
Ships with a built-in MOCK provider so the full flow is demoable end-to-end;
swap `PROVIDER` / `create_session` for Stripe/Tap/PayTabs by implementing one method.
"""
import os, json, hmac, hashlib, secrets, datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

import db as D
import mailer as M
import gateways as G

pay = APIRouter()
con = None
HERE = os.path.dirname(__file__)
WEBHOOK_SECRET = "arena-crm-webhook-secret"

METHODS = [c["code"] for c in G.CHANNELS]


def init_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, amount REAL,
        currency TEXT DEFAULT 'USD', method TEXT, status TEXT DEFAULT 'pending',
        provider TEXT, provider_ref TEXT, token TEXT UNIQUE, payer_email TEXT,
        note TEXT, created_at TEXT, paid_at TEXT, created_by INTEGER,
        channel TEXT, fee REAL DEFAULT 0, net REAL DEFAULT 0, payer_ref TEXT)""")
    for col, typ in (("channel", "TEXT"), ("fee", "REAL DEFAULT 0"),
                     ("net", "REAL DEFAULT 0"), ("payer_ref", "TEXT")):
        try:
            c.execute(f"ALTER TABLE payments ADD COLUMN {col} {typ}")
        except Exception:
            pass
    c.execute("""CREATE TABLE IF NOT EXISTS payment_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT, payment_id INTEGER, event TEXT,
        payload TEXT, created_at TEXT)""")
    for k, v in [("currency", "USD"), ("payment_provider", "mock")]:
        if not c.execute("SELECT 1 FROM settings WHERE key=?", (k,)).fetchone():
            c.execute("INSERT INTO settings(key,value) VALUES(?,?)", (k, v))
    c.commit()


def ev(pid, event, payload=None):
    con.execute("INSERT INTO payment_events(payment_id,event,payload,created_at) VALUES(?,?,?,?)",
                (pid, event, json.dumps(payload or {}, ensure_ascii=False), D.now()))


def invoice_balance(inv_id):
    r = con.execute("SELECT COALESCE(amount,0) a, COALESCE(paid_amount,0) p FROM invoices WHERE id=?",
                    (inv_id,)).fetchone()
    if not r:
        return None
    return round(r["a"] - r["p"], 2)


def create_link(invoice_id, amount=None, payer_email="", created_by=None, method="Card"):
    inv = con.execute("SELECT * FROM invoices WHERE id=? AND deleted=0", (invoice_id,)).fetchone()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    bal = invoice_balance(invoice_id)
    amount = round(float(amount), 2) if amount else bal
    if amount <= 0:
        raise HTTPException(400, "Nothing to pay on this invoice")
    if amount > bal + 0.01:
        raise HTTPException(400, f"Amount exceeds outstanding balance ({bal})")
    tok = secrets.token_urlsafe(24)
    pid = con.execute("""INSERT INTO payments(invoice_id,amount,currency,method,status,provider,
        token,payer_email,created_at,created_by) VALUES(?,?,?,?,'pending',?,?,?,?,?)""",
        (invoice_id, amount, M.cfg("currency", "USD"), method,
         M.cfg("payment_provider", "mock"), tok, payer_email, D.now(), created_by)).lastrowid
    ev(pid, "link_created", {"amount": amount})
    con.commit()
    return {"payment_id": pid, "token": tok, "url": f"/pay/{tok}", "amount": amount}


def apply_payment(p_row, ref="", source="checkout"):
    """Mark payment captured and reconcile the invoice + notify + receipt email."""
    if p_row["status"] == "paid":
        return False
    ts = D.now()
    con.execute("UPDATE payments SET status='paid', paid_at=?, provider_ref=? WHERE id=?",
                (ts, ref or f"MOCK-{secrets.token_hex(6).upper()}", p_row["id"]))
    inv = con.execute("SELECT * FROM invoices WHERE id=?", (p_row["invoice_id"],)).fetchone()
    if inv:
        new_paid = round((inv["paid_amount"] or 0) + p_row["amount"], 2)
        status = "Paid" if new_paid >= (inv["amount"] or 0) - 0.01 else inv["status"]
        con.execute("UPDATE invoices SET paid_amount=?, status=?, updated_at=? WHERE id=?",
                    (new_paid, status, ts, inv["id"]))
        D.log(con, "invoices", inv["id"], "payment",
              {"amount": p_row["amount"], "source": source, "paid_total": new_paid}, None)
        if inv["owner_id"]:
            con.execute("INSERT INTO notifications(user_id,title,body,read,created_at) VALUES(?,?,?,0,?)",
                        (inv["owner_id"], "💳 Payment received",
                         f'{p_row["amount"]:,.0f} on {inv["subject"]}', ts))
        # receipt email
        to = p_row["payer_email"]
        if not to:
            c = con.execute("""SELECT c.email FROM contacts c WHERE c.deleted=0
                AND CAST(c.account_id AS INTEGER)=CAST(? AS INTEGER) AND c.email IS NOT NULL LIMIT 1""",
                (inv["account_id"],)).fetchone()
            to = c["email"] if c else None
        if to:
            M.send_template("payment_receipt", to,
                            {"name": "", "amount": f'{p_row["amount"]:,.2f} {p_row["currency"]}',
                             "subject": inv["subject"], "owner": M.cfg("company_name", "NebrasCRM")},
                            module="invoices", record_id=inv["id"])
    ev(p_row["id"], "captured", {"source": source, "ref": ref})
    con.commit()
    return True


# ---------------- hosted checkout (public, token-gated) ----------------
@pay.get("/pay/{token}", response_class=HTMLResponse)
def checkout_page(token: str):
    return FileResponse(os.path.join(HERE, "static", "pay.html"))


@pay.get("/pay/api/{token}")
def checkout_info(token: str):
    p = con.execute("SELECT * FROM payments WHERE token=?", (token,)).fetchone()
    if not p:
        raise HTTPException(404, "Payment link not found")
    inv = con.execute("SELECT * FROM invoices WHERE id=?", (p["invoice_id"],)).fetchone()
    acc = con.execute("SELECT name FROM accounts WHERE id=CAST(? AS INTEGER)",
                      (inv["account_id"],)).fetchone() if inv else None
    if p["status"] == "pending":
        ev(p["id"], "page_viewed"); con.commit()
    return {"amount": p["amount"], "currency": p["currency"], "status": p["status"],
            "invoice": inv["subject"] if inv else "", "due_date": inv["due_date"] if inv else "",
            "account": acc["name"] if acc else "", "ref": p["provider_ref"],
            "company": M.cfg("company_name", "NebrasCRM"),
            "channels": G.public_list()["channels"], "kinds": G.public_list()["kinds"]}


class PayBody(BaseModel):
    channel: str = "visa"
    card_number: str = ""
    card_name: str = ""
    exp: str = ""
    cvc: str = ""
    method: str = ""
    email: str = ""
    msisdn: str = ""
    otp: str = ""
    beneficiary: str = ""
    branch: str = ""
    voucher: str = ""
    mtcn: str = ""
    voucher_pin: str = ""
    token: str = ""


@pay.post("/pay/api/{token}/confirm")
def confirm(token: str, b: PayBody):
    p = con.execute("SELECT * FROM payments WHERE token=?", (token,)).fetchone()
    if not p:
        raise HTTPException(404, "Payment link not found")
    if p["status"] == "paid":
        raise HTTPException(400, "This invoice is already paid")

    ch = G.BY_CODE.get(b.channel)
    if not ch:
        raise HTTPException(400, "Unsupported payment channel")
    need = set(ch.get("fields", []))

    # ---- per-channel validation ----
    if "card" in need:
        num = "".join(c for c in b.card_number if c.isdigit())
        if len(num) < 13 or not luhn(num):
            ev(p["id"], "declined", {"reason": "invalid_card", "channel": b.channel}); con.commit()
            raise HTTPException(400, "Card number is invalid")
        scheme = G.detect_card_scheme(num)
        if ch["kind"] == "card" and scheme and scheme != b.channel and b.channel != "prepaid_card":
            ev(p["id"], "scheme_mismatch", {"picked": b.channel, "detected": scheme}); con.commit()
            raise HTTPException(400, f"This card looks like {G.BY_CODE[scheme]['name_en']}, not {ch['name_en']}")
        if ch.get("length") and len(num) not in ch["length"]:
            raise HTTPException(400, f"{ch['name_en']} numbers must be {ch['length']} digits")
        if not b.exp or not b.cvc:
            raise HTTPException(400, "Expiry and CVC are required")
        if num.endswith("0000"):
            ev(p["id"], "declined", {"reason": "test_decline"}); con.commit()
            raise HTTPException(402, "Card declined by issuer")
        payer_ref = "**** " + num[-4:]
    elif "msisdn" in need:
        msi = "".join(c for c in b.msisdn if c.isdigit())
        if len(msi) < 9:
            raise HTTPException(400, "Mobile number is invalid")
        pref = ch.get("prefix")
        local = msi[-9:]
        if pref and not any(local.startswith(x) for x in pref):
            raise HTTPException(400, f"{ch['name_en']} numbers start with {', '.join(pref)}")
        if not b.otp or len(b.otp) < 4:
            raise HTTPException(400, "OTP code is required")
        if b.otp == "0000":
            ev(p["id"], "declined", {"reason": "bad_otp"}); con.commit()
            raise HTTPException(402, "Invalid OTP code")
        payer_ref = msi
    elif "voucher_pin" in need:
        pin = (b.voucher_pin or "").strip()
        if len(pin) < 6:
            raise HTTPException(400, "Card PIN is too short")
        if pin.endswith("0000"):
            ev(p["id"], "declined", {"reason": "empty_card"}); con.commit()
            raise HTTPException(402, "This prepaid card has no balance")
        payer_ref = "PIN-" + pin[-4:]
    elif "mtcn" in need:
        if not b.mtcn or not b.beneficiary:
            raise HTTPException(400, "Beneficiary and control number are required")
        payer_ref = b.mtcn
    elif "beneficiary" in need:
        if not b.beneficiary:
            raise HTTPException(400, "Beneficiary name is required")
        payer_ref = b.voucher or b.beneficiary
    elif "email" in need:
        if "@" not in (b.email or ""):
            raise HTTPException(400, "A valid account email is required")
        payer_ref = b.email
    elif "token" in need:
        if not b.token:
            raise HTTPException(400, "Device token missing")
        payer_ref = "device"
    else:
        payer_ref = ""

    fee = G.compute_fee(b.channel, p["amount"])
    if b.email:
        con.execute("UPDATE payments SET payer_email=? WHERE id=?", (b.email, p["id"]))
    con.execute("UPDATE payments SET method=?, channel=?, fee=?, net=?, payer_ref=? WHERE id=?",
                (ch["name_en"], b.channel, fee, round(p["amount"] - fee, 2), payer_ref, p["id"]))
    p = con.execute("SELECT * FROM payments WHERE token=?", (token,)).fetchone()

    # offline channels settle later — record as pending, not captured
    if ch["kind"] in ("remittance", "bank") and not ch.get("instant"):
        con.execute("UPDATE payments SET status='awaiting_settlement' WHERE id=?", (p["id"],))
        ev(p["id"], "awaiting_settlement",
           {"channel": b.channel, "eta_hours": ch.get("settlement_hours")})
        con.commit()
        return {"status": "awaiting_settlement", "channel": ch["name_en"],
                "eta_hours": ch.get("settlement_hours"), "fee": fee,
                "amount": p["amount"], "currency": p["currency"]}

    apply_payment(p, ref=f'{b.channel.upper()[:6]}-{secrets.token_hex(5).upper()}', source="checkout")
    r = con.execute("SELECT * FROM payments WHERE id=?", (p["id"],)).fetchone()
    return {"status": "paid", "ref": r["provider_ref"], "amount": r["amount"],
            "currency": r["currency"], "fee": fee, "channel": ch["name_en"]}


@pay.get("/pay/api/channels")
def channels():
    return G.public_list()


def luhn(num: str) -> bool:
    tot, alt = 0, False
    for d in reversed(num):
        n = int(d)
        if alt:
            n *= 2
            if n > 9: n -= 9
        tot += n; alt = not alt
    return tot % 10 == 0


# ---------------- provider webhook ----------------
@pay.post("/pay/webhook")
async def webhook(request: Request):
    raw = await request.body()
    sig = request.headers.get("X-Signature", "")
    expected = hmac.new(WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(401, "Bad signature")
    data = json.loads(raw or b"{}")
    tok = data.get("token")
    p = con.execute("SELECT * FROM payments WHERE token=?", (tok,)).fetchone()
    if not p:
        raise HTTPException(404, "Unknown payment")
    evt = data.get("event", "payment.succeeded")
    if evt == "payment.succeeded":
        applied = apply_payment(p, ref=data.get("ref", ""), source="webhook")
        return {"ok": True, "applied": applied}
    if evt == "payment.failed":
        con.execute("UPDATE payments SET status='failed' WHERE id=?", (p["id"],))
        ev(p["id"], "failed", data); con.commit()
        return {"ok": True}
    if evt == "payment.refunded":
        con.execute("UPDATE payments SET status='refunded' WHERE id=?", (p["id"],))
        inv = con.execute("SELECT * FROM invoices WHERE id=?", (p["invoice_id"],)).fetchone()
        if inv:
            np_ = max(0, round((inv["paid_amount"] or 0) - p["amount"], 2))
            con.execute("UPDATE invoices SET paid_amount=?, status=? WHERE id=?",
                        (np_, "Sent" if np_ < (inv["amount"] or 0) else inv["status"], inv["id"]))
        ev(p["id"], "refunded", data); con.commit()
        return {"ok": True}
    return {"ok": True, "ignored": evt}


# ---------------- staff API ----------------
def register(app, current_user, require):
    @app.get("/api/payments")
    def list_payments(invoice_id: int = 0, status: str = "", user=Depends(current_user)):
        w, p = ["1=1"], []
        if invoice_id:
            w.append("p.invoice_id=?"); p.append(invoice_id)
        if status:
            w.append("p.status=?"); p.append(status)
        return [dict(r) for r in con.execute(
            f"""SELECT p.*, i.subject invoice_subject, a.name account
                FROM payments p LEFT JOIN invoices i ON i.id=p.invoice_id
                LEFT JOIN accounts a ON a.id=CAST(i.account_id AS INTEGER)
                WHERE {' AND '.join(w)} ORDER BY p.id DESC LIMIT 300""", p)]

    @app.get("/api/payments/summary")
    def psummary(user=Depends(current_user)):
        g = lambda s: con.execute(s).fetchone()[0] or 0
        return {
            "collected": g("SELECT SUM(amount) FROM payments WHERE status='paid'"),
            "pending": g("SELECT SUM(amount) FROM payments WHERE status='pending'"),
            "refunded": g("SELECT SUM(amount) FROM payments WHERE status='refunded'"),
            "awaiting": g("SELECT SUM(amount) FROM payments WHERE status='awaiting_settlement'"),
            "fees": g("SELECT SUM(fee) FROM payments WHERE status='paid'"),
            "net": g("SELECT SUM(net) FROM payments WHERE status='paid'"),
            "outstanding": g("""SELECT SUM(COALESCE(amount,0)-COALESCE(paid_amount,0)) FROM invoices
                                WHERE deleted=0 AND status NOT IN ('Paid','Cancelled')"""),
            "overdue": g(f"""SELECT SUM(COALESCE(amount,0)-COALESCE(paid_amount,0)) FROM invoices
                             WHERE deleted=0 AND status NOT IN ('Paid','Cancelled')
                             AND due_date < '{datetime.date.today().isoformat()}'"""),
            "by_method": [dict(r) for r in con.execute(
                "SELECT method k, SUM(amount) v, COUNT(*) n FROM payments WHERE status='paid' GROUP BY method")],
        }

    class LinkBody(BaseModel):
        invoice_id: int
        amount: Optional[float] = None
        email: str = ""
        send_email: bool = False

    @app.post("/api/payments/link")
    def make_link(b: LinkBody, user=Depends(current_user)):
        if user["role"] == "readonly":
            raise HTTPException(403, "Read-only user")
        r = create_link(b.invoice_id, b.amount, b.email, user["id"])
        inv = con.execute("SELECT * FROM invoices WHERE id=?", (b.invoice_id,)).fetchone()
        base = M.cfg("base_url", "")
        r["full_url"] = (base.rstrip("/") + r["url"]) if base else r["url"]
        if b.send_email:
            to = b.email
            if not to:
                c = con.execute("""SELECT email FROM contacts WHERE deleted=0
                    AND CAST(account_id AS INTEGER)=CAST(? AS INTEGER) AND email IS NOT NULL LIMIT 1""",
                    (inv["account_id"],)).fetchone()
                to = c["email"] if c else ""
            if to:
                M.send_template("invoice_due", to, {
                    "name": "", "subject": inv["subject"],
                    "amount": f'{r["amount"]:,.2f} {M.cfg("currency","USD")}',
                    "due_date": inv["due_date"] or "—", "pay_link": r["full_url"],
                    "owner": user["name"]},
                    module="invoices", record_id=inv["id"], user_id=user["id"])
                r["emailed_to"] = to
        return r

    class ManualPay(BaseModel):
        invoice_id: int
        amount: float
        method: str = "Bank Transfer"
        note: str = ""

    @app.post("/api/payments/manual")
    def manual(b: ManualPay, user=Depends(current_user)):
        if user["role"] == "readonly":
            raise HTTPException(403, "Read-only user")
        bal = invoice_balance(b.invoice_id)
        if bal is None:
            raise HTTPException(404, "Invoice not found")
        if b.amount <= 0 or b.amount > bal + 0.01:
            raise HTTPException(400, f"Amount must be between 0 and {bal}")
        pid = con.execute("""INSERT INTO payments(invoice_id,amount,currency,method,status,provider,
            token,note,created_at,created_by) VALUES(?,?,?,?,'pending','manual',?,?,?,?)""",
            (b.invoice_id, b.amount, M.cfg("currency", "USD"), b.method,
             secrets.token_urlsafe(18), b.note, D.now(), user["id"])).lastrowid
        con.commit()
        row = con.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
        apply_payment(row, ref=f"MANUAL-{pid}", source="manual")
        return {"ok": True, "payment_id": pid}

    @app.post("/api/payments/{pid}/settle")
    def settle(pid: int, user=Depends(current_user)):
        """Confirm an offline remittance / bank transfer actually arrived."""
        require(user, "admin", "manager")
        p = con.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
        if not p or p["status"] != "awaiting_settlement":
            raise HTTPException(400, "Payment is not awaiting settlement")
        apply_payment(p, ref=p["payer_ref"] or f"SETTLE-{pid}", source="settlement")
        return {"ok": True}

    @app.get("/api/payments/channels")
    def list_channels(user=Depends(current_user)):
        return G.public_list()

    @app.get("/api/payments/by-channel")
    def by_channel(user=Depends(current_user)):
        rows = [dict(r) for r in con.execute("""
            SELECT COALESCE(channel,'other') k, COUNT(*) n, SUM(amount) v,
                   SUM(fee) fees, SUM(net) net
            FROM payments WHERE status='paid' GROUP BY 1 ORDER BY v DESC""")]
        for r in rows:
            c = G.BY_CODE.get(r["k"])
            r["name_en"] = c["name_en"] if c else r["k"]
            r["name_ar"] = c["name_ar"] if c else r["k"]
            r["kind"] = c["kind"] if c else "other"
            r["icon"] = c.get("icon", "") if c else ""
        return rows

    @app.post("/api/payments/{pid}/refund")
    def refund(pid: int, user=Depends(current_user)):
        require(user, "admin", "manager")
        p = con.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
        if not p or p["status"] != "paid":
            raise HTTPException(400, "Only paid payments can be refunded")
        con.execute("UPDATE payments SET status='refunded' WHERE id=?", (pid,))
        inv = con.execute("SELECT * FROM invoices WHERE id=?", (p["invoice_id"],)).fetchone()
        if inv:
            np_ = max(0, round((inv["paid_amount"] or 0) - p["amount"], 2))
            con.execute("UPDATE invoices SET paid_amount=?, status=?, updated_at=? WHERE id=?",
                        (np_, "Sent" if np_ < (inv["amount"] or 0) else inv["status"], D.now(), inv["id"]))
            D.log(con, "invoices", inv["id"], "refund", {"amount": p["amount"]}, user["id"])
        ev(pid, "refunded", {"by": user["name"]}); con.commit()
        return {"ok": True}

    @app.get("/api/payments/{pid}/events")
    def events(pid: int, user=Depends(current_user)):
        return [dict(r) for r in con.execute(
            "SELECT * FROM payment_events WHERE payment_id=? ORDER BY id", (pid,))]


# ---------------- portal-side ----------------
def register_portal(portal_router, portal_user_dep):
    @portal_router.post("/portal/api/invoices/{inv_id}/pay")
    def portal_pay(inv_id: int, u=Depends(portal_user_dep)):
        try:
            aid = int(u["account_id"])
        except (TypeError, ValueError):
            aid = -1
        inv = con.execute("SELECT * FROM invoices WHERE id=? AND deleted=0 AND CAST(account_id AS INTEGER)=?",
                          (inv_id, aid)).fetchone()
        if not inv:
            raise HTTPException(404, "Not found")
        r = create_link(inv_id, None, u["email"], None)
        return r

    @portal_router.get("/portal/api/payments")
    def portal_payments(u=Depends(portal_user_dep)):
        try:
            aid = int(u["account_id"])
        except (TypeError, ValueError):
            aid = -1
        return [dict(r) for r in con.execute(
            """SELECT p.id,p.amount,p.currency,p.method,p.status,p.provider_ref,p.paid_at,p.created_at,
                      i.subject invoice_subject
               FROM payments p JOIN invoices i ON i.id=p.invoice_id
               WHERE CAST(i.account_id AS INTEGER)=? AND i.deleted=0
               ORDER BY p.id DESC""", (aid,))]
