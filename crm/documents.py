"""Printable invoice and quotation document data.

The browser renders the visual layout, while this module provides one consistent,
permission-checked payload for staff documents. Keeping totals on the server makes
the printed view match saved line items instead of trusting browser calculations.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException

import db as D
from authz import record_or_404

con = None

DOCUMENTS = {
    "invoice": {"module": "invoices", "label_ar": "فاتورة", "label_en": "Invoice", "prefix": "INV"},
    "quote": {"module": "quotes", "label_ar": "عرض سعر", "label_en": "Quotation", "prefix": "QTE"},
}


def _num(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _round(value) -> float:
    return round(value + 0.0, 2)


def _settings():
    keys = ("company_name", "company_phone", "company_address", "tax_number", "currency", "invoice_prefix")
    placeholders = ",".join("?" for _ in keys)
    values = {row["key"]: row["value"] for row in con.execute(
        f'''SELECT \"key\",\"value\" FROM settings WHERE "key" IN ({placeholders})''', list(keys)
    )}
    return {
        "name": values.get("company_name") or "NebrasCRM",
        "phone": values.get("company_phone") or "",
        "address": values.get("company_address") or "",
        "tax_number": values.get("tax_number") or "",
        "currency": values.get("currency") or "USD",
        "invoice_prefix": values.get("invoice_prefix") or "INV",
    }


def _account(account_id):
    if not account_id:
        return {}
    return dict(con.execute(
        "SELECT * FROM accounts WHERE id=CAST(? AS INTEGER) AND deleted=0", (account_id,)
    ).fetchone() or {})


def _contact(document, account_id):
    # Quotes may be linked to a deal with a selected contact. Invoices do not
    # carry a direct contact field, so use the first active account contact.
    if document.get("deal_id"):
        row = con.execute("""SELECT c.* FROM deals d
            LEFT JOIN contacts c ON c.id=CAST(d.contact_id AS INTEGER) AND c.deleted=0
            WHERE d.id=CAST(? AS INTEGER) AND d.deleted=0""", (document["deal_id"],)).fetchone()
        if row:
            return dict(row)
    if account_id:
        row = con.execute("""SELECT * FROM contacts WHERE deleted=0
            AND CAST(account_id AS INTEGER)=CAST(? AS INTEGER)
            ORDER BY id LIMIT 1""", (account_id,)).fetchone()
        if row:
            return dict(row)
    return {}


def _items(module: str, record_id: int):
    items = []
    for row in con.execute("""SELECT li.*, p.code product_code, p.category product_category
        FROM line_items li LEFT JOIN products p ON p.id=li.product_id AND p.deleted=0
        WHERE li.module=? AND li.record_id=? ORDER BY li.id""", (module, record_id)):
        item = dict(row)
        qty = max(0, _num(item.get("qty")))
        price = max(0, _num(item.get("price")))
        discount_rate = min(100, max(0, _num(item.get("discount"))))
        tax_rate = min(100, max(0, _num(item.get("tax"))))
        gross = qty * price
        discount_amount = gross * discount_rate / 100
        net = gross - discount_amount
        tax_amount = net * tax_rate / 100
        item.update(
            qty=qty,
            price=price,
            discount=discount_rate,
            tax=tax_rate,
            gross=_round(gross),
            discount_amount=_round(discount_amount),
            net=_round(net),
            tax_amount=_round(tax_amount),
            line_total=_round(net + tax_amount),
        )
        items.append(item)
    return items


def _owner(owner_id):
    if not owner_id:
        return {}
    row = con.execute("SELECT id,name,email FROM users WHERE id=?", (owner_id,)).fetchone()
    return dict(row) if row else {}


def build_payment(record_id: int, user: dict | None = None, account_id: int | None = None):
    """Build a permission-checked payment voucher payload.

    A payment belongs to an invoice rather than a metadata-driven CRM module, so
    its authorization is inherited from that invoice.  ``account_id`` is used by
    the customer portal, where access is scoped to one customer account.
    """
    payment_row = con.execute("SELECT * FROM payments WHERE id=?", (record_id,)).fetchone()
    if not payment_row:
        raise HTTPException(404, "Payment not found")
    payment = dict(payment_row)

    try:
        invoice_id = int(payment.get("invoice_id"))
    except (TypeError, ValueError):
        raise HTTPException(404, "Invoice not found")

    if user is not None:
        invoice = dict(record_or_404(con, "invoices", invoice_id, user))
    elif account_id is not None:
        invoice_row = con.execute("""SELECT * FROM invoices
            WHERE id=? AND deleted=0 AND CAST(account_id AS INTEGER)=CAST(? AS INTEGER)""",
            (invoice_id, account_id)).fetchone()
        if not invoice_row:
            raise HTTPException(404, "Payment not found")
        invoice = dict(invoice_row)
    else:
        invoice_row = con.execute("SELECT * FROM invoices WHERE id=? AND deleted=0", (invoice_id,)).fetchone()
        if not invoice_row:
            raise HTTPException(404, "Invoice not found")
        invoice = dict(invoice_row)

    company = _settings()
    account = _account(invoice.get("account_id"))
    contact = _contact(invoice, invoice.get("account_id"))
    owner = _owner(payment.get("created_by"))
    invoice_total = _round(_num(invoice.get("amount")))
    invoice_paid = _round(_num(invoice.get("paid_amount")))
    reference = (payment.get("provider_ref") or "").strip() or f"PAY-{record_id:05d}"

    return {
        "kind": "payment",
        "label_ar": "سند دفع",
        "label_en": "Payment Voucher",
        "reference": reference,
        "company": company,
        "account": {
            "name": account.get("name") or "",
            "phone": account.get("phone") or "",
            "website": account.get("website") or "",
            "address": account.get("billing_address") or "",
        },
        "contact": {
            "name": contact.get("name") or "",
            "title": contact.get("title") or "",
            "email": contact.get("email") or "",
            "phone": contact.get("phone") or contact.get("mobile") or "",
        },
        "owner": owner,
        "payment": {
            "id": payment["id"],
            "amount": _round(_num(payment.get("amount"))),
            "currency": payment.get("currency") or company["currency"],
            "method": payment.get("method") or "",
            "channel": payment.get("channel") or "",
            "status": payment.get("status") or "",
            "provider": payment.get("provider") or "",
            "provider_ref": payment.get("provider_ref") or "",
            "payer_ref": payment.get("payer_ref") or "",
            "note": payment.get("note") or "",
            "fee": _round(_num(payment.get("fee"))),
            "net": _round(_num(payment.get("net"))),
            "created_on": payment.get("created_at") or "",
            "paid_on": payment.get("paid_at") or "",
        },
        "invoice": {
            "id": invoice["id"],
            "subject": invoice.get("subject") or f"INV-{invoice['id']:05d}",
            "status": invoice.get("status") or "",
            "issued_on": invoice.get("invoice_date") or "",
            "due_on": invoice.get("due_date") or "",
            "total": invoice_total,
            "paid": invoice_paid,
            "remaining": _round(max(0, invoice_total - invoice_paid)),
        },
        "generated_at": D.now(),
    }


def build(kind: str, record_id: int, user: dict | None = None):
    if kind == "payment":
        return build_payment(record_id, user=user)
    meta = DOCUMENTS.get(kind)
    if not meta:
        raise HTTPException(404, "Unknown document")
    module = meta["module"]
    if user is not None:
        row = record_or_404(con, module, record_id, user)
    else:
        row = con.execute(f'SELECT * FROM "{module}" WHERE id=? AND deleted=0', (record_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Document not found")
    document = dict(row)
    account = _account(document.get("account_id"))
    contact = _contact(document, document.get("account_id"))
    items = _items(module, record_id)

    subtotal = _round(sum(item["gross"] for item in items))
    discount_total = _round(sum(item["discount_amount"] for item in items))
    tax_total = _round(sum(item["tax_amount"] for item in items))
    computed_total = _round(sum(item["line_total"] for item in items))
    stored_total = _round(_num(document.get("amount")))
    total = computed_total if items else stored_total
    paid = _round(_num(document.get("paid_amount"))) if kind == "invoice" else 0.0
    remaining = _round(max(0, total - paid)) if kind == "invoice" else 0.0
    company = _settings()
    owner = _owner(document.get("owner_id"))

    reference = (document.get("subject") or "").strip()
    if not reference:
        prefix = company["invoice_prefix"] if kind == "invoice" else meta["prefix"]
        reference = f"{prefix}-{record_id:05d}"

    return {
        "kind": kind,
        "module": module,
        "label_ar": meta["label_ar"],
        "label_en": meta["label_en"],
        "reference": reference,
        "document": {
            "id": document["id"],
            "subject": document.get("subject") or "",
            "status": document.get("status") or "",
            "issued_on": document.get("invoice_date") if kind == "invoice" else document.get("created_at"),
            "due_on": document.get("due_date") if kind == "invoice" else document.get("valid_until"),
            "terms": document.get("notes") if kind == "invoice" else document.get("terms"),
            "stored_total": stored_total,
            "paid": paid,
            "remaining": remaining,
        },
        "company": company,
        "account": {
            "name": account.get("name") or "",
            "phone": account.get("phone") or "",
            "website": account.get("website") or "",
            "address": account.get("billing_address") or "",
            "industry": account.get("industry") or "",
        },
        "contact": {
            "name": contact.get("name") or "",
            "title": contact.get("title") or "",
            "email": contact.get("email") or "",
            "phone": contact.get("phone") or contact.get("mobile") or "",
        },
        "owner": owner,
        "items": items,
        "totals": {
            "subtotal": subtotal,
            "discount_total": discount_total,
            "tax_total": tax_total,
            "total": total,
            "computed_total": computed_total,
        },
        "generated_at": D.now(),
    }


def register(app, current_user):
    @app.get("/api/documents/{kind}/{record_id}")
    def printable_document(kind: str, record_id: int, user=Depends(current_user)):
        return build(kind, record_id, user)
