"""Customer Portal — self-service area for contacts.
Separate auth realm from staff CRM users. A portal user is always tied to a contact
record, and every query is hard-scoped to that contact's account.
"""
import os, json, hmac, base64, hashlib, datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel

import db as D
import mailer as M
import datetime

PSECRET = "arena-crm-portal-secret"
portal = APIRouter()
HERE = os.path.dirname(__file__)
con = None  # injected from main


def init_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS portal_users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER UNIQUE, email TEXT UNIQUE, password TEXT,
        active INTEGER DEFAULT 1, last_login TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS portal_messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id INTEGER, body TEXT,
        author TEXT, author_name TEXT, created_at TEXT)""")
    c.commit()


def phash(pw: str) -> str:
    return hashlib.sha256((pw + PSECRET).encode()).hexdigest()


def ptoken(pid: int) -> str:
    p = base64.urlsafe_b64encode(json.dumps({"pid": pid}).encode()).decode()
    return f'{p}.{hmac.new(PSECRET.encode(), p.encode(), hashlib.sha256).hexdigest()[:32]}'


def parse_ptoken(tok: str):
    try:
        p, s = tok.split(".")
        if not hmac.compare_digest(s, hmac.new(PSECRET.encode(), p.encode(), hashlib.sha256).hexdigest()[:32]):
            return None
        return json.loads(base64.urlsafe_b64decode(p)).get("pid")
    except Exception:
        return None


def portal_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    pid = parse_ptoken(authorization[7:])
    if not pid:
        raise HTTPException(401, "Invalid token")
    r = con.execute("""SELECT p.*, c.name cname, c.account_id, c.title, c.phone,
                              a.name aname FROM portal_users p
                       JOIN contacts c ON c.id=p.contact_id
                       LEFT JOIN accounts a ON a.id=CAST(c.account_id AS INTEGER)
                       WHERE p.id=? AND p.active=1 AND c.deleted=0""", (pid,)).fetchone()
    if not r:
        raise HTTPException(401, "Portal access disabled")
    return dict(r)


class PLogin(BaseModel):
    email: str
    password: str


@portal.post("/portal/api/login")
def plogin(b: PLogin):
    r = con.execute("SELECT * FROM portal_users WHERE lower(email)=lower(?) AND active=1", (b.email,)).fetchone()
    if not r or r["password"] != phash(b.password):
        raise HTTPException(401, "Invalid credentials")
    con.execute("UPDATE portal_users SET last_login=? WHERE id=?", (D.now(), r["id"])); con.commit()
    c = con.execute("SELECT name, account_id FROM contacts WHERE id=?", (r["contact_id"],)).fetchone()
    return {"token": ptoken(r["id"]), "user": {"email": r["email"], "name": c["name"] if c else r["email"]}}


@portal.get("/portal/api/me")
def pme(u=Depends(portal_user)):
    return {"email": u["email"], "name": u["cname"], "account": u["aname"],
            "account_id": u["account_id"], "title": u["title"], "phone": u["phone"]}


def _scope(u):
    """Return (sql_fragment, params) restricting rows to this customer."""
    try:
        aid = int(u["account_id"])
    except (TypeError, ValueError):
        aid = -1
    return "CAST(account_id AS INTEGER)=?", [aid]


@portal.get("/portal/api/summary")
def psummary(u=Depends(portal_user)):
    w, p = _scope(u)
    g = lambda sql, pr: con.execute(sql, pr).fetchone()[0] or 0
    return {
        "open_tickets": g(f"SELECT COUNT(*) FROM tickets WHERE deleted=0 AND status!='Closed' AND {w}", p),
        "total_tickets": g(f"SELECT COUNT(*) FROM tickets WHERE deleted=0 AND {w}", p),
        "outstanding": g(f"SELECT SUM(COALESCE(amount,0)-COALESCE(paid_amount,0)) FROM invoices "
                         f"WHERE deleted=0 AND status NOT IN ('Paid','Cancelled') AND {w}", p),
        "paid": g(f"SELECT SUM(amount) FROM invoices WHERE deleted=0 AND status='Paid' AND {w}", p),
        "open_quotes": g(f"SELECT COUNT(*) FROM quotes WHERE deleted=0 AND status IN ('Draft','Sent') AND {w}", p),
    }


@portal.get("/portal/api/tickets")
def ptickets(u=Depends(portal_user)):
    w, p = _scope(u)
    rows = con.execute(f"""SELECT id,subject,status,priority,channel,category,due_date,created_at,description
                           FROM tickets WHERE deleted=0 AND {w} ORDER BY id DESC""", p).fetchall()
    return [dict(r) for r in rows]


@portal.get("/portal/api/tickets/{tid}")
def pticket(tid: int, u=Depends(portal_user)):
    w, p = _scope(u)
    r = con.execute(f"SELECT * FROM tickets WHERE id=? AND deleted=0 AND {w}", [tid] + p).fetchone()
    if not r:
        raise HTTPException(404, "Not found")
    d = dict(r)
    d["messages"] = [dict(x) for x in con.execute(
        "SELECT * FROM portal_messages WHERE ticket_id=? ORDER BY id", (tid,))]
    return d


class NewTicket(BaseModel):
    subject: str
    description: str = ""
    priority: str = "Medium"
    category: str = ""


@portal.post("/portal/api/tickets")
def pnew_ticket(b: NewTicket, u=Depends(portal_user)):
    if not b.subject.strip():
        raise HTTPException(400, "Subject required")
    owner = con.execute("SELECT owner_id FROM accounts WHERE id=?", (u["account_id"],)).fetchone()
    ts = D.now()
    tid = con.execute("""INSERT INTO tickets(created_at,updated_at,created_by,owner_id,deleted,
        subject,account_id,contact_id,status,priority,channel,category,description)
        VALUES(?,?,?,?,0,?,?,?,?,?,?,?,?)""",
        (ts, ts, None, owner["owner_id"] if owner else None, b.subject.strip(), u["account_id"],
         u["contact_id"], "Open", b.priority, "Web", b.category, b.description)).lastrowid
    con.execute("INSERT INTO portal_messages(ticket_id,body,author,author_name,created_at) VALUES(?,?,?,?,?)",
                (tid, b.description or b.subject, "customer", u["cname"], ts))
    D.log(con, "tickets", tid, "portal_create", {"by": u["email"]}, None)
    if owner and owner["owner_id"]:
        con.execute("INSERT INTO notifications(user_id,title,body,read,created_at) VALUES(?,?,?,0,?)",
                    (owner["owner_id"], "🎫 New portal ticket", f'{u["cname"]}: {b.subject}', ts))
        ow = con.execute("SELECT email,name FROM users WHERE id=?", (owner["owner_id"],)).fetchone()
        if ow and ow["email"]:
            M.send(ow["email"], f'[Ticket #{tid}] {b.subject}',
                   f'New portal ticket from {u["cname"]} ({u["aname"]}).\n\n{b.description}',
                   module="tickets", record_id=tid)
    con.commit()
    return {"id": tid}


class Reply(BaseModel):
    body: str


@portal.post("/portal/api/tickets/{tid}/reply")
def preply(tid: int, b: Reply, u=Depends(portal_user)):
    w, p = _scope(u)
    r = con.execute(f"SELECT * FROM tickets WHERE id=? AND deleted=0 AND {w}", [tid] + p).fetchone()
    if not r:
        raise HTTPException(404, "Not found")
    if not b.body.strip():
        raise HTTPException(400, "Empty message")
    ts = D.now()
    con.execute("INSERT INTO portal_messages(ticket_id,body,author,author_name,created_at) VALUES(?,?,?,?,?)",
                (tid, b.body.strip(), "customer", u["cname"], ts))
    if r["status"] in ("Closed", "Waiting on Customer"):
        con.execute("UPDATE tickets SET status='Open', updated_at=? WHERE id=?", (ts, tid))
    if r["owner_id"]:
        con.execute("INSERT INTO notifications(user_id,title,body,read,created_at) VALUES(?,?,?,0,?)",
                    (r["owner_id"], "💬 Portal reply", f'{u["cname"]} on #{tid}: {b.body[:60]}', ts))
    con.commit()
    return {"ok": True}


@portal.get("/portal/api/invoices")
def pinvoices(u=Depends(portal_user)):
    w, p = _scope(u)
    return [dict(r) for r in con.execute(
        f"""SELECT id,subject,status,invoice_date,due_date,amount,paid_amount,notes
            FROM invoices WHERE deleted=0 AND {w} ORDER BY id DESC""", p)]


@portal.get("/portal/api/quotes")
def pquotes(u=Depends(portal_user)):
    w, p = _scope(u)
    out = []
    for r in con.execute(f"""SELECT id,subject,status,valid_until,amount,terms
                             FROM quotes WHERE deleted=0 AND {w} ORDER BY id DESC""", p):
        d = dict(r)
        d["items"] = [dict(x) for x in con.execute(
            "SELECT name,qty,price,discount,tax FROM line_items WHERE module='quotes' AND record_id=?", (r["id"],))]
        out.append(d)
    return out


class QuoteAct(BaseModel):
    decision: str  # Accepted | Rejected


@portal.post("/portal/api/quotes/{qid}/decision")
def pquote_decision(qid: int, b: QuoteAct, u=Depends(portal_user)):
    if b.decision not in ("Accepted", "Rejected"):
        raise HTTPException(400, "Bad decision")
    w, p = _scope(u)
    r = con.execute(f"SELECT * FROM quotes WHERE id=? AND deleted=0 AND {w}", [qid] + p).fetchone()
    if not r:
        raise HTTPException(404, "Not found")
    if r["status"] in ("Accepted", "Rejected"):
        raise HTTPException(400, "Already decided")
    con.execute("UPDATE quotes SET status=?, updated_at=? WHERE id=?", (b.decision, D.now(), qid))
    D.log(con, "quotes", qid, "portal_" + b.decision.lower(), {"by": u["email"]}, None)
    if r["owner_id"]:
        con.execute("INSERT INTO notifications(user_id,title,body,read,created_at) VALUES(?,?,?,0,?)",
                    (r["owner_id"], f"📄 Quote {b.decision}", f'{u["cname"]} {b.decision.lower()} {r["subject"]}', D.now()))
    con.commit()
    return {"ok": True}


class PChangePw(BaseModel):
    current: str
    new: str


@portal.post("/portal/api/password")
def pchange(b: PChangePw, u=Depends(portal_user)):
    if u["password"] != phash(b.current):
        raise HTTPException(400, "Current password is incorrect")
    if len(b.new) < 6:
        raise HTTPException(400, "Password too short (min 6)")
    con.execute("UPDATE portal_users SET password=? WHERE id=?", (phash(b.new), u["id"])); con.commit()
    return {"ok": True}




# ---------------- catalogue & self-service orders ----------------
@portal.get("/portal/api/products")
def pproducts(q: str = "", u=Depends(portal_user)):
    """Catalogue with the customer's loyalty discount already applied."""
    import loyalty as LOY
    _rows, pts = LOY.compute("customer", int(u["account_id"] or 0)) if u["account_id"] else ([], 0)
    tier = LOY.tier_for(pts)
    disc = tier["discount"]
    w, p = ["deleted=0", "active='Yes'"], []
    if q:
        w.append("(name LIKE ? OR code LIKE ? OR category LIKE ?)"); p += [f"%{q}%"] * 3
    out = []
    for r in con.execute(f"SELECT * FROM products WHERE {' AND '.join(w)} ORDER BY category,name", p):
        d = dict(r)
        base = float(d["unit_price"] or 0)
        d["your_price"] = round(base * (1 - disc / 100), 2)
        d["discount"] = disc
        d["in_stock"] = (d["qty_in_stock"] or 0) > 0
        out.append(d)
    return {"products": out, "tier": tier, "discount": disc}


class OrderLine(BaseModel):
    product_id: int
    qty: float = 1


class NewOrder(BaseModel):
    items: list
    note: str = ""


@portal.post("/portal/api/orders")
def pnew_order(b: NewOrder, u=Depends(portal_user)):
    """Customer places an order -> creates a Draft quote for staff to confirm."""
    if not b.items:
        raise HTTPException(400, "Your cart is empty")
    acc = con.execute("SELECT owner_id, list_tag FROM accounts WHERE id=CAST(? AS INTEGER)",
                      (u["account_id"],)).fetchone()
    if acc and acc["list_tag"] == "Blacklist":
        raise HTTPException(403, "Ordering is disabled for this account. Please contact us.")
    import loyalty as LOY
    _r, pts = LOY.compute("customer", int(u["account_id"] or 0))
    disc = LOY.tier_for(pts)["discount"]
    ts = D.now()
    qid = con.execute("""INSERT INTO quotes(created_at,updated_at,created_by,owner_id,deleted,
        subject,account_id,status,valid_until,amount,terms)
        VALUES(?,?,NULL,?,0,?,?,'Draft',?,0,?)""",
        (ts, ts, acc["owner_id"] if acc else None,
         f'طلب من البوابة — {u["cname"]}', u["account_id"],
         (datetime.date.today() + datetime.timedelta(days=14)).isoformat(),
         b.note or "طلب مقدَّم عبر بوابة العملاء")).lastrowid
    total = 0.0
    for it in b.items:
        pr = con.execute("SELECT * FROM products WHERE id=? AND deleted=0",
                         (int(it.get("product_id", 0)),)).fetchone()
        if not pr:
            continue
        qty = max(1.0, float(it.get("qty", 1)))
        price = float(pr["unit_price"] or 0)
        tax = float(pr["tax_rate"] or 0)
        line = qty * price * (1 - disc / 100) * (1 + tax / 100)
        total += line
        con.execute("""INSERT INTO line_items(module,record_id,product_id,name,qty,price,discount,tax)
                       VALUES('quotes',?,?,?,?,?,?,?)""",
                    (qid, pr["id"], pr["name"], qty, price, disc, tax))
    con.execute("UPDATE quotes SET amount=? WHERE id=?", (round(total, 2), qid))
    D.log(con, "quotes", qid, "portal_order", {"by": u["email"], "total": round(total, 2)}, None)
    if acc and acc["owner_id"]:
        con.execute("INSERT INTO notifications(user_id,title,body,read,created_at) VALUES(?,?,?,0,?)",
                    (acc["owner_id"], "🛒 طلب جديد من البوابة",
                     f'{u["cname"]} — {total:,.0f}', ts))
        ow = con.execute("SELECT email FROM users WHERE id=?", (acc["owner_id"],)).fetchone()
        if ow and ow["email"]:
            M.send(ow["email"], f"[Portal Order] {u['cname']}",
                   f'طلب جديد بقيمة {total:,.2f} من {u["cname"]} ({u["aname"]}).',
                   module="quotes", record_id=qid)
    con.commit()
    return {"id": qid, "total": round(total, 2), "discount": disc}


@portal.get("/portal/api/orders")
def porders(u=Depends(portal_user)):
    w, p = _scope(u)
    out = []
    for r in con.execute(f"""SELECT id,subject,status,valid_until,amount,created_at
                             FROM quotes WHERE deleted=0 AND {w} ORDER BY id DESC""", p):
        d = dict(r)
        d["items"] = [dict(x) for x in con.execute(
            "SELECT name,qty,price,discount,tax FROM line_items WHERE module='quotes' AND record_id=?",
            (r["id"],))]
        out.append(d)
    return out


# ---------------- loyalty ----------------
@portal.get("/portal/api/loyalty")
def ployalty(u=Depends(portal_user)):
    import loyalty as LOY
    aid = int(u["account_id"] or 0)
    rows, total = LOY.compute("customer", aid)
    t = LOY.tier_for(total)
    nxt = None
    for x in reversed(LOY.TIERS):
        if x["min"] > total:
            nxt = {"tier": x, "gap": round(x["min"] - total, 1)}
            break
    red = [dict(r) for r in con.execute("""SELECT * FROM loyalty_redemptions
        WHERE member_type='customer' AND member_id=? ORDER BY id DESC""", (aid,))]
    spent = sum(float(r["points"] or 0) for r in red if r["status"] == "approved")
    return {"points": total, "available": round(total - spent, 1), "redeemed": spent,
            "tier": t, "next": nxt, "breakdown": rows, "redemptions": red,
            "tiers": LOY.TIERS, "rules": LOY.RULES,
            "principles": LOY.register.__doc__ if False else None}


# ---------------- statement of account ----------------
@portal.get("/portal/api/statement")
def pstatement(u=Depends(portal_user)):
    w, p = _scope(u)
    rows = []
    for i in con.execute(f"""SELECT id,subject,invoice_date,due_date,amount,paid_amount,status
                             FROM invoices WHERE deleted=0 AND {w}
                             AND status!='Cancelled' ORDER BY invoice_date""", p):
        rows.append({"date": i["invoice_date"], "ref": i["subject"], "kind": "invoice",
                     "debit": float(i["amount"] or 0), "credit": 0.0, "id": i["id"],
                     "status": i["status"]})
    try:
        aid = int(u["account_id"])
    except (TypeError, ValueError):
        aid = -1
    for pay in con.execute("""SELECT p.id,p.amount,p.paid_at,p.method,p.provider_ref,i.subject
        FROM payments p JOIN invoices i ON i.id=p.invoice_id
        WHERE p.status='paid' AND CAST(i.account_id AS INTEGER)=? AND i.deleted=0
        ORDER BY p.paid_at""", (aid,)):
        rows.append({"date": (pay["paid_at"] or "")[:10], "ref": f'{pay["subject"]} — {pay["method"] or ""}',
                     "kind": "payment", "debit": 0.0, "credit": float(pay["amount"] or 0),
                     "id": pay["id"], "status": pay["provider_ref"]})
    rows.sort(key=lambda r: r["date"] or "")
    run = 0.0
    for r in rows:
        run += r["debit"] - r["credit"]
        r["running"] = round(run, 2)
    rows.reverse()
    return {"rows": rows, "balance": round(run, 2)}


# ---------------- documents ----------------
@portal.get("/portal/api/documents")
def pdocuments(u=Depends(portal_user)):
    w, p = _scope(u)
    docs = []
    for i in con.execute(f"""SELECT id,subject,invoice_date,amount,status FROM invoices
                             WHERE deleted=0 AND {w} ORDER BY id DESC""", p):
        docs.append({"type": "invoice", "type_ar": "فاتورة", "id": i["id"], "title": i["subject"],
                     "date": i["invoice_date"], "amount": i["amount"], "status": i["status"]})
    for q in con.execute(f"""SELECT id,subject,valid_until,amount,status FROM quotes
                             WHERE deleted=0 AND {w} ORDER BY id DESC""", p):
        docs.append({"type": "quote", "type_ar": "عرض سعر", "id": q["id"], "title": q["subject"],
                     "date": q["valid_until"], "amount": q["amount"], "status": q["status"]})
    return docs


@portal.get("/portal/api/document/{kind}/{did}")
def pdocument(kind: str, did: int, u=Depends(portal_user)):
    if kind not in ("invoice", "quote"):
        raise HTTPException(404, "Unknown document")
    tbl = "invoices" if kind == "invoice" else "quotes"
    w, p = _scope(u)
    r = con.execute(f"SELECT * FROM {tbl} WHERE id=? AND deleted=0 AND {w}", [did] + p).fetchone()
    if not r:
        raise HTTPException(404, "Not found")
    d = dict(r)
    d["items"] = [dict(x) for x in con.execute(
        "SELECT * FROM line_items WHERE module=? AND record_id=?", (tbl, did))]
    d["company"] = M.cfg("company_name", "NebrasCRM")
    d["account_name"] = u["aname"]
    d["contact_name"] = u["cname"]
    return d


# ---------------- profile self-service ----------------
class ProfileUpd(BaseModel):
    phone: str = ""
    title: str = ""
    mailing_address: str = ""


@portal.put("/portal/api/profile")
def pprofile(b: ProfileUpd, u=Depends(portal_user)):
    sets, vals = [], []
    for k, v in (("phone", b.phone), ("title", b.title), ("mailing_address", b.mailing_address)):
        if v:
            sets.append(f"{k}=?"); vals.append(v)
    if sets:
        con.execute(f"UPDATE contacts SET {','.join(sets)}, updated_at=? WHERE id=?",
                    vals + [D.now(), u["contact_id"]])
        D.log(con, "contacts", u["contact_id"], "portal_profile", b.dict(), None)
        con.commit()
    return {"ok": True}


# ---------- staff-side administration of portal access ----------
def register_admin(app, current_user, require):
    @app.get("/api/portal-access")
    def list_access(user=Depends(current_user)):
        return [dict(r) for r in con.execute("""
            SELECT p.id,p.contact_id,p.email,p.active,p.last_login,p.created_at,
                   c.name cname, a.name aname
            FROM portal_users p LEFT JOIN contacts c ON c.id=p.contact_id
            LEFT JOIN accounts a ON a.id=CAST(c.account_id AS INTEGER) ORDER BY p.id DESC""")]

    @app.post("/api/portal-access")
    def grant(body: dict, user=Depends(current_user)):
        require(user, "admin", "manager")
        cid = int(body.get("contact_id", 0))
        c = con.execute("SELECT * FROM contacts WHERE id=? AND deleted=0", (cid,)).fetchone()
        if not c:
            raise HTTPException(404, "Contact not found")
        email = (body.get("email") or c["email"] or "").strip()
        if not email:
            raise HTTPException(400, "Contact has no email")
        pw = body.get("password") or "portal123"
        if con.execute("SELECT 1 FROM portal_users WHERE contact_id=? OR lower(email)=lower(?)", (cid, email)).fetchone():
            raise HTTPException(400, "Portal access already exists for this contact/email")
        con.execute("INSERT INTO portal_users(contact_id,email,password,active,created_at) VALUES(?,?,?,1,?)",
                    (cid, email, phash(pw), D.now()))
        con.commit()
        base = M.cfg("base_url", "")
        M.send_template("portal_invite", email, {
            "name": c["name"], "email": email, "password": pw,
            "portal_url": (base.rstrip("/") + "/portal") if base else "/portal",
            "owner": user["name"]}, to_name=c["name"], module="contacts",
            record_id=cid, user_id=user["id"])
        return {"ok": True, "email": email, "password": pw, "emailed": True}

    @app.put("/api/portal-access/{pid}")
    def upd_access(pid: int, body: dict, user=Depends(current_user)):
        require(user, "admin", "manager")
        if "active" in body:
            con.execute("UPDATE portal_users SET active=? WHERE id=?", (int(body["active"]), pid))
        if body.get("password"):
            con.execute("UPDATE portal_users SET password=? WHERE id=?", (phash(body["password"]), pid))
        con.commit()
        return {"ok": True}

    @app.delete("/api/portal-access/{pid}")
    def del_access(pid: int, user=Depends(current_user)):
        require(user, "admin")
        con.execute("DELETE FROM portal_users WHERE id=?", (pid,)); con.commit()
        return {"ok": True}

    @app.get("/api/tickets/{tid}/portal-thread")
    def thread(tid: int, user=Depends(current_user)):
        return [dict(r) for r in con.execute(
            "SELECT * FROM portal_messages WHERE ticket_id=? ORDER BY id", (tid,))]

    @app.post("/api/tickets/{tid}/portal-thread")
    def staff_reply(tid: int, body: dict, user=Depends(current_user)):
        if user["role"] == "readonly":
            raise HTTPException(403, "Read-only user")
        con.execute("INSERT INTO portal_messages(ticket_id,body,author,author_name,created_at) VALUES(?,?,?,?,?)",
                    (tid, body.get("body", ""), "staff", user["name"], D.now()))
        con.execute("UPDATE tickets SET status='Waiting on Customer', updated_at=? WHERE id=? AND status!='Closed'",
                    (D.now(), tid))
        con.commit()
        tk = con.execute("""SELECT t.subject, c.email, c.name FROM tickets t
                            LEFT JOIN contacts c ON c.id=CAST(t.contact_id AS INTEGER)
                            WHERE t.id=?""", (tid,)).fetchone()
        if tk and tk["email"]:
            M.send_template("ticket_reply", tk["email"],
                            {"name": tk["name"] or "", "subject": tk["subject"], "id": tid,
                             "body": body.get("body", ""), "owner": user["name"]},
                            to_name=tk["name"] or "", module="tickets", record_id=tid,
                            user_id=user["id"])
        return {"ok": True}


@portal.get("/portal")
def portal_index():
    return FileResponse(os.path.join(HERE, "static", "portal.html"))


@portal.get("/portal.js")
def portal_js():
    return FileResponse(os.path.join(HERE, "static", "portal.js"), media_type="application/javascript")
