"""Point of sale for NebrasCRM.

A POS checkout creates a normal CRM invoice and payment ledger entry, writes the
same invoice line items used elsewhere in the system, and atomically decrements
product stock.  That keeps retail sales visible in invoices, payments, reports,
and printable documents instead of creating a disconnected cash-register silo.
"""
from __future__ import annotations

import datetime
import json
import math
import secrets
from typing import Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

import db as D
import mailer as M
from authz import record_or_404

con = None  # injected by main

PAYMENT_METHODS = {
    "cash": {"ar": "نقداً", "en": "Cash", "payment": "Cash"},
    "card": {"ar": "بطاقة", "en": "Card", "payment": "Card"},
    "wallet": {"ar": "محفظة إلكترونية", "en": "Wallet", "payment": "Wallet"},
    "bank": {"ar": "تحويل بنكي", "en": "Bank transfer", "payment": "Bank Transfer"},
    "on_account": {"ar": "آجل / على الحساب", "en": "On account", "payment": "On Account"},
}


def _number(value, label: str = "Amount") -> float:
    if isinstance(value, bool):
        raise HTTPException(400, f"{label} must be a valid number")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise HTTPException(400, f"{label} must be a valid number")
    if not math.isfinite(number):
        raise HTTPException(400, f"{label} must be a valid number")
    return round(number, 2)


def _setting(key: str, default: str = "") -> str:
    row = con.execute("SELECT \"value\" FROM settings WHERE \"key\"=?", (key,)).fetchone()
    return (row["value"] if row else default) or default


def _bool_setting(key: str, default: bool = False) -> bool:
    return _setting(key, "1" if default else "0").strip().lower() in {"1", "true", "yes", "on"}


def _require_pos_user(user: dict):
    if user.get("role") == "readonly":
        raise HTTPException(403, "Read-only user")


def _sales_scope(user: dict, column: str = "s.cashier_id") -> tuple[str, list]:
    if user.get("role") == "agent":
        return f"{column}=?", [user["id"]]
    return "1=1", []


def _sale_or_404(sale_id: int, user: dict):
    _require_pos_user(user)
    sale = con.execute("SELECT * FROM pos_sales WHERE id=?", (sale_id,)).fetchone()
    if not sale or (user.get("role") == "agent" and sale["cashier_id"] != user["id"]):
        raise HTTPException(404, "POS sale not found")
    return sale


def _open_session(cashier_id: int):
    return con.execute("""SELECT * FROM pos_sessions
        WHERE cashier_id=? AND status='open' ORDER BY id DESC LIMIT 1""", (cashier_id,)).fetchone()


def _session_payload(row):
    if not row:
        return None
    session = dict(row)
    cash_sales = con.execute("""SELECT COALESCE(SUM(total),0) amount FROM pos_sales
        WHERE session_id=? AND status='completed' AND payment_method='cash'""", (session["id"],)).fetchone()
    opening = _number(session.get("opening_cash") or 0)
    session["cash_sales"] = _number(cash_sales["amount"] if cash_sales else 0)
    session["expected_cash"] = round(opening + session["cash_sales"], 2)
    return session


def init_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS pos_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cashier_id INTEGER, status VARCHAR(20) DEFAULT 'open',
        opening_cash REAL DEFAULT 0, closing_cash REAL, expected_cash REAL,
        difference REAL, note TEXT, opened_at TEXT, closed_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS pos_sales(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_no VARCHAR(100) UNIQUE, invoice_id INTEGER, payment_id INTEGER,
        session_id INTEGER, account_id INTEGER, customer_name TEXT, customer_phone TEXT,
        cashier_id INTEGER, subtotal REAL DEFAULT 0, discount_total REAL DEFAULT 0,
        tax_total REAL DEFAULT 0, total REAL DEFAULT 0, amount_received REAL DEFAULT 0,
        change_due REAL DEFAULT 0, payment_method VARCHAR(30), payment_status VARCHAR(30),
        status VARCHAR(30) DEFAULT 'completed', note TEXT, created_at VARCHAR(40),
        refunded_at TEXT, refunded_by INTEGER, refund_note TEXT)""")
    # MySQL cannot index a TEXT/BLOB column without an index-prefix length.
    # Earlier builds created pos_sales.created_at as TEXT, so make the upgrade
    # idempotent before creating ix_pos_sales_created below. SQLite and
    # PostgreSQL can index TEXT directly and therefore need no migration.
    if D.is_mariadb():
        # Select a constant rather than the INFORMATION_SCHEMA column name: some
        # MySQL builds expose that mapping as DATA_TYPE while others preserve
        # data_type.  Only the existence of a legacy TEXT-family type matters.
        legacy_text_timestamp = c.execute("""SELECT 1 FROM information_schema.columns
            WHERE table_schema=DATABASE() AND table_name='pos_sales' AND column_name='created_at'
              AND data_type IN ('tinytext','text','mediumtext','longtext')""").fetchone()
        if legacy_text_timestamp:
            c.execute("ALTER TABLE pos_sales MODIFY COLUMN created_at VARCHAR(40)")
    for sql in (
        "CREATE INDEX IF NOT EXISTS ix_pos_sales_cashier ON pos_sales(cashier_id)",
        "CREATE INDEX IF NOT EXISTS ix_pos_sales_created ON pos_sales(created_at)",
        "CREATE INDEX IF NOT EXISTS ix_pos_sales_session ON pos_sales(session_id)",
        "CREATE INDEX IF NOT EXISTS ix_pos_sessions_cashier ON pos_sessions(cashier_id)",
    ):
        c.execute(sql)
    for key, value in (
        ("pos_allow_negative_stock", "0"),
        ("pos_allow_price_override", "0"),
        ("pos_require_session", "0"),
    ):
        if not c.execute("SELECT 1 FROM settings WHERE \"key\"=?", (key,)).fetchone():
            c.execute("INSERT INTO settings(\"key\",\"value\") VALUES(?,?)", (key, value))
    c.commit()


class POSItem(BaseModel):
    product_id: int
    qty: float = Field(gt=0, le=100000)
    discount: float = Field(default=0, ge=0, le=100)


class SaleBody(BaseModel):
    items: list[POSItem] = Field(min_length=1, max_length=150)
    account_id: Optional[int] = None
    customer_name: str = ""
    customer_phone: str = ""
    payment_method: str = "cash"
    amount_received: Optional[float] = None
    note: str = ""
    send_receipt: bool = False
    receipt_email: str = ""


class OpenSessionBody(BaseModel):
    opening_cash: float = Field(default=0, ge=0)
    note: str = ""


class CloseSessionBody(BaseModel):
    closing_cash: float = Field(ge=0)
    note: str = ""


class RefundBody(BaseModel):
    note: str = ""


def _customer(body: SaleBody, user: dict):
    account = {}
    contact = {}
    if body.account_id is not None:
        account = dict(record_or_404(con, "accounts", body.account_id, user))
        contact_row = con.execute("""SELECT * FROM contacts WHERE deleted=0
            AND CAST(account_id AS INTEGER)=CAST(? AS INTEGER) ORDER BY id LIMIT 1""",
            (body.account_id,)).fetchone()
        contact = dict(contact_row) if contact_row else {}
        customer_name = account.get("name") or ""
        customer_phone = contact.get("phone") or account.get("phone") or ""
    else:
        customer_name = (body.customer_name or "").strip() or "Walk-in customer"
        customer_phone = (body.customer_phone or "").strip()
    if len(customer_name) > 250 or len(customer_phone) > 100:
        raise HTTPException(400, "Customer details are too long")
    return account, contact, customer_name, customer_phone


def _prepare_items(items: list[POSItem]):
    allow_negative = _bool_setting("pos_allow_negative_stock")
    prepared, seen = [], set()
    subtotal = discount_total = tax_total = total = 0.0
    for line in items:
        if line.product_id in seen:
            raise HTTPException(400, "Add each product to the sale only once")
        seen.add(line.product_id)
        product = con.execute("SELECT * FROM products WHERE id=? AND deleted=0 AND active='Yes'",
                              (line.product_id,)).fetchone()
        if not product:
            raise HTTPException(400, "One of the products is unavailable")
        product = dict(product)
        qty = _number(line.qty, "Quantity")
        discount = _number(line.discount, "Discount")
        if qty <= 0 or not 0 <= discount <= 100:
            raise HTTPException(400, "Invalid sale line")
        stock = _number(product.get("qty_in_stock") or 0, "Stock")
        if not allow_negative and qty > stock + 0.00001:
            raise HTTPException(400, f"Insufficient stock for {product.get('name') or 'product'}")
        price = max(0, _number(product.get("unit_price") or 0, "Price"))
        tax_rate = min(100, max(0, _number(product.get("tax_rate") or 0, "Tax")))
        gross = round(qty * price, 2)
        discount_amount = round(gross * discount / 100, 2)
        taxable = round(gross - discount_amount, 2)
        tax_amount = round(taxable * tax_rate / 100, 2)
        line_total = round(taxable + tax_amount, 2)
        prepared.append({
            "product": product, "qty": qty, "price": price, "discount": discount,
            "tax": tax_rate, "gross": gross, "discount_amount": discount_amount,
            "tax_amount": tax_amount, "line_total": line_total,
        })
        subtotal += gross
        discount_total += discount_amount
        tax_total += tax_amount
        total += line_total
    return prepared, {
        "subtotal": round(subtotal, 2),
        "discount_total": round(discount_total, 2),
        "tax_total": round(tax_total, 2),
        "total": round(total, 2),
    }


def register(app, current_user, require):
    @app.get("/api/pos/catalog")
    def catalog(q: str = "", category: str = "", user=Depends(current_user)):
        _require_pos_user(user)
        q = q.strip()
        category = category.strip()
        if len(q) > 160 or len(category) > 120:
            raise HTTPException(400, "Search is too long")
        where, params = ["deleted=0", "active='Yes'"], []
        if q:
            where.append("(name LIKE ? OR code LIKE ? OR category LIKE ?)")
            params += [f"%{q}%"] * 3
        if category:
            where.append("category=?")
            params.append(category)
        products = [dict(row) for row in con.execute(f"""SELECT id,name,code,category,unit_price,
                qty_in_stock,reorder_level,tax_rate,active FROM products
                WHERE {' AND '.join(where)} ORDER BY category,name LIMIT 500""", params)]
        categories = [row["category"] for row in con.execute("""SELECT DISTINCT category FROM products
            WHERE deleted=0 AND active='Yes' AND category IS NOT NULL AND category!='' ORDER BY category""")]
        return {
            "products": products,
            "categories": categories,
            "currency": _setting("currency", "USD"),
            "allow_negative_stock": _bool_setting("pos_allow_negative_stock"),
            "allow_price_override": _bool_setting("pos_allow_price_override"),
            "require_session": _bool_setting("pos_require_session"),
            "payment_methods": PAYMENT_METHODS,
        }

    @app.get("/api/pos/customers")
    def customers(q: str = "", limit: int = 80, user=Depends(current_user)):
        _require_pos_user(user)
        q = q.strip()
        if len(q) > 160:
            raise HTTPException(400, "Search is too long")
        limit = max(1, min(int(limit), 200))
        where, params = ["a.deleted=0"], []
        if user.get("role") == "agent":
            where.append("(a.owner_id=? OR a.owner_id IS NULL)")
            params.append(user["id"])
        if q:
            where.append("(a.name LIKE ? OR a.phone LIKE ?)")
            params += [f"%{q}%", f"%{q}%"]
        return [dict(row) for row in con.execute(f"""SELECT a.id,a.name,a.phone,a.type,
                (SELECT c.name FROM contacts c WHERE c.deleted=0 AND CAST(c.account_id AS INTEGER)=a.id
                 ORDER BY c.id LIMIT 1) contact_name,
                (SELECT c.email FROM contacts c WHERE c.deleted=0 AND CAST(c.account_id AS INTEGER)=a.id
                 ORDER BY c.id LIMIT 1) contact_email
            FROM accounts a WHERE {' AND '.join(where)} ORDER BY a.name LIMIT ?""", params + [limit])]

    @app.get("/api/pos/session")
    def session(user=Depends(current_user)):
        _require_pos_user(user)
        return {"session": _session_payload(_open_session(user["id"]))}

    @app.post("/api/pos/sessions/open")
    def open_session(body: OpenSessionBody, user=Depends(current_user)):
        _require_pos_user(user)
        if len(body.note) > 1000:
            raise HTTPException(400, "Note is too long")
        if _open_session(user["id"]):
            raise HTTPException(409, "You already have an open POS session")
        opening_cash = _number(body.opening_cash, "Opening cash")
        session_id = con.execute("""INSERT INTO pos_sessions(cashier_id,status,opening_cash,note,opened_at)
            VALUES(?,'open',?,?,?)""", (user["id"], opening_cash, body.note.strip(), D.now())).lastrowid
        con.commit()
        return {"session": _session_payload(con.execute("SELECT * FROM pos_sessions WHERE id=?", (session_id,)).fetchone())}

    @app.post("/api/pos/sessions/{session_id}/close")
    def close_session(session_id: int, body: CloseSessionBody, user=Depends(current_user)):
        _require_pos_user(user)
        row = con.execute("SELECT * FROM pos_sessions WHERE id=? AND status='open'", (session_id,)).fetchone()
        if not row or (user.get("role") == "agent" and row["cashier_id"] != user["id"]):
            raise HTTPException(404, "Open POS session not found")
        if len(body.note) > 1000:
            raise HTTPException(400, "Note is too long")
        session_data = _session_payload(row)
        counted = _number(body.closing_cash, "Closing cash")
        expected = session_data["expected_cash"]
        difference = round(counted - expected, 2)
        con.execute("""UPDATE pos_sessions SET status='closed',closing_cash=?,expected_cash=?,difference=?,
            note=?,closed_at=? WHERE id=?""",
            (counted, expected, difference, body.note.strip() or row["note"], D.now(), session_id))
        con.commit()
        session_data.update(status="closed", closing_cash=counted, expected_cash=expected,
                            difference=difference, closed_at=D.now(), note=body.note.strip() or row["note"])
        return {"session": session_data}

    @app.get("/api/pos/summary")
    def summary(user=Depends(current_user)):
        _require_pos_user(user)
        today = datetime.date.today().isoformat()
        scope, params = _sales_scope(user)
        where = ["s.status='completed'", "substr(s.created_at,1,10)=?", scope]
        rows = con.execute(f"""SELECT COUNT(*) count, COALESCE(SUM(s.total),0) total,
            COALESCE(SUM(CASE WHEN s.payment_method='cash' THEN s.total ELSE 0 END),0) cash,
            COALESCE(SUM(CASE WHEN s.payment_method='card' THEN s.total ELSE 0 END),0) card
            FROM pos_sales s WHERE {' AND '.join(where)}""", [today] + params).fetchone()
        low_stock = con.execute("""SELECT COUNT(*) count FROM products WHERE deleted=0 AND active='Yes'
            AND reorder_level>0 AND COALESCE(qty_in_stock,0)<=reorder_level""").fetchone()["count"]
        return {
            "today": {"count": rows["count"] or 0, "total": round(float(rows["total"] or 0), 2),
                      "cash": round(float(rows["cash"] or 0), 2), "card": round(float(rows["card"] or 0), 2)},
            "low_stock": low_stock or 0,
            "session": _session_payload(_open_session(user["id"])),
            "currency": _setting("currency", "USD"),
        }

    @app.get("/api/pos/sales")
    def sales(limit: int = 20, user=Depends(current_user)):
        _require_pos_user(user)
        limit = max(1, min(int(limit), 200))
        scope, params = _sales_scope(user)
        return [dict(row) for row in con.execute(f"""SELECT s.*, a.name account_name, u.name cashier_name,
                i.status invoice_status FROM pos_sales s
            LEFT JOIN accounts a ON a.id=CAST(s.account_id AS INTEGER)
            LEFT JOIN users u ON u.id=s.cashier_id
            LEFT JOIN invoices i ON i.id=s.invoice_id
            WHERE {scope} ORDER BY s.id DESC LIMIT ?""", params + [limit])]

    @app.post("/api/pos/sale")
    def create_sale(body: SaleBody, user=Depends(current_user)):
        _require_pos_user(user)
        if body.payment_method not in PAYMENT_METHODS:
            raise HTTPException(400, "Unsupported POS payment method")
        if len(body.note) > 2000 or len(body.receipt_email) > 320:
            raise HTTPException(400, "Sale details are too long")
        if body.receipt_email and ("@" not in body.receipt_email or "\n" in body.receipt_email or "\r" in body.receipt_email):
            raise HTTPException(400, "Invalid receipt email")

        account, contact, customer_name, customer_phone = _customer(body, user)
        prepared, totals = _prepare_items(body.items)
        if totals["total"] <= 0:
            raise HTTPException(400, "The sale total must be greater than zero")
        active_session = _open_session(user["id"])
        if _bool_setting("pos_require_session") and not active_session:
            raise HTTPException(400, "Open a POS session before completing a sale")

        is_credit = body.payment_method == "on_account"
        if is_credit:
            received = 0.0
            change_due = 0.0
        elif body.payment_method == "cash":
            received = _number(body.amount_received if body.amount_received is not None else totals["total"], "Cash received")
            if received + 0.00001 < totals["total"]:
                raise HTTPException(400, "Cash received is less than the sale total")
            change_due = round(received - totals["total"], 2)
        else:
            received = totals["total"]
            change_due = 0.0

        receipt_no = f"POS-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"
        ts = D.now()
        invoice_id = payment_id = None
        try:
            invoice_id = con.execute("""INSERT INTO invoices(created_at,updated_at,created_by,owner_id,deleted,
                subject,account_id,status,invoice_date,due_date,amount,paid_amount,notes)
                VALUES(?,?,?,?,0,?,?,?,?,?,?,?,?)""",
                (ts, ts, user["id"], user["id"], receipt_no, account.get("id") or None,
                 "Sent" if is_credit else "Paid", ts[:10], ts[:10], totals["total"],
                 0 if is_credit else totals["total"], (body.note or "").strip())).lastrowid

            for item in prepared:
                con.execute("""INSERT INTO line_items(module,record_id,product_id,name,qty,price,discount,tax)
                    VALUES('invoices',?,?,?,?,?,?,?)""",
                    (invoice_id, item["product"]["id"], item["product"].get("name") or "",
                     item["qty"], item["price"], item["discount"], item["tax"]))
                if _bool_setting("pos_allow_negative_stock"):
                    updated = con.execute("""UPDATE products SET qty_in_stock=COALESCE(qty_in_stock,0)-?
                        WHERE id=? AND deleted=0""", (item["qty"], item["product"]["id"])).rowcount
                else:
                    updated = con.execute("""UPDATE products SET qty_in_stock=COALESCE(qty_in_stock,0)-?
                        WHERE id=? AND deleted=0 AND COALESCE(qty_in_stock,0)>=?""",
                        (item["qty"], item["product"]["id"], item["qty"])).rowcount
                if updated != 1:
                    raise HTTPException(409, f"Stock changed for {item['product'].get('name') or 'a product'}; refresh and try again")

            if not is_credit:
                channel = f"pos_{body.payment_method}"
                payment_id = con.execute("""INSERT INTO payments(invoice_id,amount,currency,method,status,provider,
                    provider_ref,token,note,created_at,paid_at,created_by,channel,fee,net)
                    VALUES(?,?,?,?, 'paid','pos',?,?,?,?,?,?,?,?,?)""",
                    (invoice_id, totals["total"], _setting("currency", "USD"),
                     PAYMENT_METHODS[body.payment_method]["payment"], receipt_no, secrets.token_urlsafe(18),
                     (body.note or "").strip(), ts, ts, user["id"], channel, 0, totals["total"])).lastrowid
                con.execute("""INSERT INTO payment_events(payment_id,event,payload,created_at)
                    VALUES(?,?,?,?)""", (payment_id, "pos_sale", json.dumps({"receipt_no": receipt_no}, ensure_ascii=False), ts))

            sale_id = con.execute("""INSERT INTO pos_sales(receipt_no,invoice_id,payment_id,session_id,account_id,
                customer_name,customer_phone,cashier_id,subtotal,discount_total,tax_total,total,amount_received,
                change_due,payment_method,payment_status,status,note,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (receipt_no, invoice_id, payment_id, active_session["id"] if active_session else None,
                 account.get("id") or None, customer_name, customer_phone, user["id"], totals["subtotal"],
                 totals["discount_total"], totals["tax_total"], totals["total"], received, change_due,
                 body.payment_method, "unpaid" if is_credit else "paid", "completed", (body.note or "").strip(), ts)).lastrowid
            D.log(con, "invoices", invoice_id, "pos_sale", {
                "sale_id": sale_id, "receipt_no": receipt_no, "total": totals["total"],
                "payment_method": body.payment_method, "items": len(prepared),
            }, user["id"])
            con.commit()
        except HTTPException:
            con.rollback()
            raise
        except Exception:
            con.rollback()
            raise

        receipt_to = (body.receipt_email or contact.get("email") or "").strip()
        if body.send_receipt and receipt_to:
            M.send_template("payment_receipt", receipt_to, {
                "name": contact.get("name") or customer_name,
                "amount": f"{totals['total']:,.2f} {_setting('currency', 'USD')}",
                "subject": receipt_no,
                "owner": user.get("name") or "",
            }, to_name=contact.get("name") or customer_name, module="invoices", record_id=invoice_id, user_id=user["id"])

        return {
            "sale_id": sale_id, "receipt_no": receipt_no, "invoice_id": invoice_id,
            "payment_id": payment_id, "totals": totals, "amount_received": received,
            "change_due": change_due, "payment_status": "unpaid" if is_credit else "paid",
            "receipt_queued": bool(body.send_receipt and receipt_to),
        }

    @app.get("/api/pos/sales/{sale_id}/receipt")
    def receipt(sale_id: int, user=Depends(current_user)):
        sale = dict(_sale_or_404(sale_id, user))
        invoice = con.execute("SELECT * FROM invoices WHERE id=?", (sale["invoice_id"],)).fetchone()
        account = con.execute("SELECT * FROM accounts WHERE id=CAST(? AS INTEGER)", (sale["account_id"],)).fetchone() if sale.get("account_id") else None
        cashier = con.execute("SELECT id,name,email FROM users WHERE id=?", (sale["cashier_id"],)).fetchone()
        items = [dict(row) for row in con.execute("""SELECT li.*, p.code product_code
            FROM line_items li LEFT JOIN products p ON p.id=li.product_id
            WHERE li.module='invoices' AND li.record_id=? ORDER BY li.id""", (sale["invoice_id"],))]
        return {
            "sale": sale,
            "invoice": dict(invoice) if invoice else {},
            "account": dict(account) if account else {},
            "cashier": dict(cashier) if cashier else {},
            "items": items,
            "company": {
                "name": _setting("company_name", "NebrasCRM"),
                "phone": _setting("company_phone", ""),
                "address": _setting("company_address", ""),
                "tax_number": _setting("tax_number", ""),
                "currency": _setting("currency", "USD"),
            },
        }

    @app.post("/api/pos/sales/{sale_id}/refund")
    def refund_sale(sale_id: int, body: RefundBody, user=Depends(current_user)):
        require(user, "admin", "manager")
        sale = con.execute("SELECT * FROM pos_sales WHERE id=?", (sale_id,)).fetchone()
        if not sale:
            raise HTTPException(404, "POS sale not found")
        if sale["status"] != "completed":
            raise HTTPException(400, "Only completed POS sales can be refunded")
        if len(body.note) > 2000:
            raise HTTPException(400, "Refund note is too long")
        ts = D.now()
        try:
            items = con.execute("""SELECT product_id,qty FROM line_items
                WHERE module='invoices' AND record_id=?""", (sale["invoice_id"],)).fetchall()
            for item in items:
                if item["product_id"]:
                    con.execute("UPDATE products SET qty_in_stock=COALESCE(qty_in_stock,0)+? WHERE id=?",
                                (item["qty"], item["product_id"]))
            if sale["payment_id"]:
                con.execute("UPDATE payments SET status='refunded' WHERE id=? AND status='paid'", (sale["payment_id"],))
                con.execute("""INSERT INTO payment_events(payment_id,event,payload,created_at)
                    VALUES(?,?,?,?)""", (sale["payment_id"], "pos_refund",
                    json.dumps({"sale_id": sale_id, "note": body.note.strip()}, ensure_ascii=False), ts))
            con.execute("UPDATE invoices SET paid_amount=0,status='Cancelled',updated_at=? WHERE id=?",
                        (ts, sale["invoice_id"]))
            con.execute("""UPDATE pos_sales SET status='refunded',refunded_at=?,refunded_by=?,refund_note=?
                WHERE id=?""", (ts, user["id"], body.note.strip(), sale_id))
            D.log(con, "invoices", sale["invoice_id"], "pos_refund", {
                "sale_id": sale_id, "receipt_no": sale["receipt_no"], "total": sale["total"],
            }, user["id"])
            con.commit()
        except Exception:
            con.rollback()
            raise
        return {"ok": True, "sale_id": sale_id, "status": "refunded"}
