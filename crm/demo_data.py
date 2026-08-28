"""Controlled cleanup of NebrasCRM demonstration business data.

The cleanup intentionally preserves administrator accounts, system settings,
email templates, API keys, integrations and the bundled global geography dataset.
That makes it safe to turn a seeded demonstration installation into an empty
working CRM without losing access to the system or its core configuration.
"""
from __future__ import annotations

from collections.abc import Iterable

import datetime

import db as D

ADD_CONFIRMATION = "ADD DEMO DATA"
DEMO_PRODUCT_PREFIX = "DEMO-POS-"

# Delete child/ledger tables before their parent business objects. All names are
# source-controlled constants rather than client input, so quoted identifiers are
# safe here.
DEMO_TABLES = (
    "pos_sales",
    "pos_sessions",
    "payment_events",
    "payments",
    "line_items",
    "portal_messages",
    "portal_users",
    "agent_requests",
    "agent_stock",
    "agent_txn",
    "agent_users",
    "territories",
    "loyalty_redemptions",
    "loyalty_points",
    "loyalty_members",
    "emails",
    "interactions",
    "notes",
    "notifications",
    "audit",
    "competitor_products",
    "market_research",
    "competitors",
    "opportunities",
    "deals",
    "quotes",
    "invoices",
    "tickets",
    "activities",
    "contacts",
    "leads",
    "campaigns",
    "products",
    "vendors",
    "accounts",
    "agents",
)

PRESERVED = (
    "users",
    "settings",
    "email_templates",
    "workflows",
    "dashboards",
    "custom_fields",
    "api_keys",
    "integrations",
    "geo_governorates",
    "geo_districts",
    "geo_uzlah",
    "geo_villages",
    "geo_quarters",
    "geo_streets",
)


def _existing_tables(con) -> set[str]:
    return D.list_tables(con)


def _counts(con, tables: Iterable[str]) -> dict[str, int]:
    existing = _existing_tables(con)
    return {
        table: con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        for table in tables
        if table in existing
    }


def summary(con) -> dict:
    """Describe exactly what a cleanup action will remove and preserve."""
    counts = _counts(con, DEMO_TABLES)
    return {
        "tables": counts,
        "total": sum(counts.values()),
        "preserved": list(PRESERVED),
        "confirmation": "DELETE DEMO DATA",
        "add_confirmation": ADD_CONFIRMATION,
        "sample_pack_present": _has_sample_records(con),
    }


def _has_sample_records(con) -> bool:
    """Whether the compact, UI-created sample pack is already present."""
    try:
        row = con.execute("SELECT 1 FROM products WHERE deleted=0 AND code LIKE ? LIMIT 1",
                          (f"{DEMO_PRODUCT_PREFIX}%",)).fetchone()
        return bool(row)
    except Exception:
        return False


def _insert(con, table: str, **values) -> int:
    """Insert a source-controlled row without accepting caller-controlled SQL."""
    keys = list(values)
    quoted = ",".join(f'"{key}"' for key in keys)
    placeholders = ",".join("?" for _ in keys)
    return con.execute(
        f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})', [values[key] for key in keys]
    ).lastrowid


def _business_values(user_id: int, **values) -> dict:
    now = D.now()
    return {
        "created_at": now,
        "updated_at": now,
        "created_by": user_id,
        "owner_id": user_id,
        "deleted": 0,
        **values,
    }


def _line_total(qty: float, price: float, discount: float = 0, tax: float = 0) -> float:
    net = qty * price * (1 - discount / 100)
    return round(net * (1 + tax / 100), 2)


def add(con, user_id: int) -> dict:
    """Add one deterministic sample pack without touching real operating data.

    This is intentionally separate from the command-line seed scripts: it works
    after an administrator has cleared a demo installation, does not create or
    overwrite users/settings/geography, and is idempotent through DEMO-POS codes.
    """
    if _has_sample_records(con):
        return {
            "ok": True,
            "added": {},
            "total": 0,
            "already_present": True,
            "message": "The NebrasCRM sample pack is already present.",
        }

    existing = _existing_tables(con)
    required = {"products", "accounts", "contacts", "leads", "deals", "quotes", "invoices", "line_items"}
    if not required.issubset(existing):
        raise RuntimeError("The CRM business tables have not been initialized yet.")

    added: dict[str, int] = {}

    def count(table: str, amount: int = 1):
        added[table] = added.get(table, 0) + amount

    today = datetime.date.today()
    date = lambda days: (today + datetime.timedelta(days=days)).isoformat()
    currency_row = con.execute('SELECT \"value\" FROM settings WHERE \"key\"=\'currency\'').fetchone()
    currency = (currency_row["value"] if currency_row else "USD") or "USD"

    try:
        # --- Retail catalogue: intentionally useful for POS, quotes and invoices.
        product_specs = [
            ("Nebras POS Starter Kit", "Hardware", 185.0, 52, 10, 5.0),
            ("Wireless Barcode Scanner", "Hardware", 74.0, 36, 8, 5.0),
            ("Retail Analytics Add-on", "Software", 129.0, 96, 15, 5.0),
            ("Customer Success Workshop", "Services", 360.0, 24, 5, 0.0),
        ]
        product_ids = []
        for index, (name, category, price, stock, reorder, tax) in enumerate(product_specs, 1):
            product_ids.append(_insert(con, "products", **_business_values(user_id,
                name=name, code=f"{DEMO_PRODUCT_PREFIX}{index:03d}", category=category,
                unit_price=price, cost=round(price * 0.58, 2), qty_in_stock=stock,
                reorder_level=reorder, tax_rate=tax, active="Yes",
                description="NebrasCRM sample catalogue item.")))
            count("products")

        # --- Customers and their primary contacts.
        account_specs = [
            ("Demo Horizon Retail", "Retail", "+967-1-555001", "Sanaa, Yemen"),
            ("Demo Cedar Medical", "Healthcare", "+966-11-555002", "Riyadh, Saudi Arabia"),
            ("Demo Blue Harbor Logistics", "Logistics", "+971-4-555003", "Dubai, UAE"),
        ]
        account_ids, contact_ids = [], []
        for index, (name, industry, phone, address) in enumerate(account_specs, 1):
            account_id = _insert(con, "accounts", **_business_values(user_id,
                name=name, industry=industry, type="Customer", phone=phone,
                website=f"https://demo{index}.example.com", annual_revenue=150000 + index * 50000,
                employees=30 + index * 15, segment="Gold", billing_address=address,
                description="NebrasCRM sample customer."))
            account_ids.append(account_id)
            count("accounts")
            contact_id = _insert(con, "contacts", **_business_values(user_id,
                name=("Maya Hassan", "Omar Saleh", "Lina Kareem")[index - 1], account_id=account_id,
                title=("Operations Manager", "Procurement Lead", "Finance Director")[index - 1],
                email=("maya.hassan", "omar.saleh", "lina.kareem")[index - 1] + "@demo.example",
                phone=phone, mobile=phone, department=("Operations", "Procurement", "Finance")[index - 1],
                mailing_address=address, description="Primary sample contact."))
            contact_ids.append(contact_id)
            count("contacts")

        campaign_id = _insert(con, "campaigns", **_business_values(user_id,
            name="Demo Retail Growth Campaign", type="Email", status="Active", start_date=date(-18),
            end_date=date(42), budget=8500, actual_cost=3100, expected_revenue=58000,
            leads_generated=24, description="Sample campaign for the dashboard."))
        count("campaigns")

        for index, name in enumerate(("Rami Al-Sayed", "Noura Hamid", "Tariq Nasser"), 1):
            _insert(con, "leads", **_business_values(user_id,
                name=name, company=("Demo Atlas Stores", "Demo Green Pharmacy", "Demo Gulf Supplies")[index - 1],
                email=f"lead{index}@demo.example", phone=f"+967-77-0000{index:03d}",
                status=("New", "Contacted", "Qualified")[index - 1], source="Campaign",
                rating=("Warm", "Hot", "Warm")[index - 1], industry="Retail", annual_revenue=60000 + index * 25000,
                city=("Sanaa", "Aden", "Dubai")[index - 1], country=("Yemen", "Yemen", "United Arab Emirates")[index - 1],
                description="Sample lead created by the demo pack."))
            count("leads")

        for index, stage in enumerate(("Proposal", "Negotiation", "Closed Won")):
            amount = (4200, 7800, 5600)[index]
            _insert(con, "deals", **_business_values(user_id,
                name=f"Demo retail rollout {index + 1}", account_id=account_ids[index], contact_id=contact_ids[index],
                amount=amount, stage=stage, probability=(60, 80, 100)[index], closing_date=date(18 - index * 10),
                source="Campaign", campaign_id=campaign_id, next_step=("Send proposal", "Review contract", "Onboard customer")[index],
                description="Sample sales opportunity."))
            count("deals")

        _insert(con, "activities", **_business_values(user_id,
            subject="Demo POS launch review", type="Meeting", status="Not Started", priority="High",
            due_date=date(4), related_to="Demo Horizon Retail", description="Review the sample POS rollout."))
        count("activities")
        _insert(con, "tickets", **_business_values(user_id,
            subject="Demo checkout configuration", account_id=account_ids[0], contact_id=contact_ids[0],
            status="Open", priority="Medium", channel="Web", category="Configuration", due_date=date(3),
            description="Sample support ticket for the dashboard."))
        count("tickets")

        # --- Quotation with saved item rows.
        quote_items = [
            (product_ids[0], product_specs[0][0], 2, product_specs[0][2], 5.0, product_specs[0][5]),
            (product_ids[1], product_specs[1][0], 4, product_specs[1][2], 0.0, product_specs[1][5]),
        ]
        quote_total = round(sum(_line_total(qty, price, discount, tax) for _, _, qty, price, discount, tax in quote_items), 2)
        quote_id = _insert(con, "quotes", **_business_values(user_id,
            subject="DEMO-QTE-2026-001 — Retail counter package", account_id=account_ids[0], deal_id=None,
            status="Sent", valid_until=date(21), amount=quote_total,
            terms="Sample quote: prices are valid for 21 days."))
        count("quotes")
        for product_id, name, qty, price, discount, tax in quote_items:
            _insert(con, "line_items", module="quotes", record_id=quote_id, product_id=product_id,
                    name=name, qty=qty, price=price, discount=discount, tax=tax)
            count("line_items")

        # --- A paid invoice and payment voucher for the finance screens.
        invoice_items = [
            (product_ids[2], product_specs[2][0], 3, product_specs[2][2], 10.0, product_specs[2][5]),
            (product_ids[3], product_specs[3][0], 1, product_specs[3][2], 0.0, product_specs[3][5]),
        ]
        invoice_total = round(sum(_line_total(qty, price, discount, tax) for _, _, qty, price, discount, tax in invoice_items), 2)
        invoice_id = _insert(con, "invoices", **_business_values(user_id,
            subject="DEMO-INV-2026-001 — Analytics rollout", account_id=account_ids[1], status="Paid",
            invoice_date=date(-7), due_date=date(23), amount=invoice_total, paid_amount=invoice_total,
            notes="Sample paid invoice generated by the demo-data control."))
        count("invoices")
        for product_id, name, qty, price, discount, tax in invoice_items:
            _insert(con, "line_items", module="invoices", record_id=invoice_id, product_id=product_id,
                    name=name, qty=qty, price=price, discount=discount, tax=tax)
            count("line_items")

        payment_id = None
        if "payments" in existing:
            payment_id = _insert(con, "payments", invoice_id=invoice_id, amount=invoice_total, currency=currency,
                method="Card", status="paid", provider="demo", provider_ref="DEMO-PAY-2026-001",
                token="demo-payment-2026-001", payer_email="omar.saleh@demo.example",
                note="Sample payment", created_at=D.now(), paid_at=D.now(), created_by=user_id,
                channel="visa", fee=0, net=invoice_total, payer_ref="**** 4242")
            count("payments")
            if "payment_events" in existing:
                _insert(con, "payment_events", payment_id=payment_id, event="demo_captured",
                        payload='{"source":"demo-data"}', created_at=D.now())
                count("payment_events")

        # --- A historical POS sale enables immediate testing of cash sessions and receipts.
        if {"pos_sessions", "pos_sales"}.issubset(existing):
            pos_item = (product_ids[1], product_specs[1][0], 2, product_specs[1][2], 0.0, product_specs[1][5])
            pos_total = _line_total(pos_item[2], pos_item[3], pos_item[4], pos_item[5])
            session_cash = round(250 + pos_total, 2)
            session_id = _insert(con, "pos_sessions", cashier_id=user_id, status="closed", opening_cash=250,
                closing_cash=session_cash, expected_cash=session_cash, difference=0, note="Sample closed POS shift",
                opened_at=D.now(), closed_at=D.now())
            count("pos_sessions")
            pos_invoice_id = _insert(con, "invoices", **_business_values(user_id,
                subject="DEMO-POS-2026-001", account_id=account_ids[2], status="Paid", invoice_date=date(-1),
                due_date=date(-1), amount=pos_total, paid_amount=pos_total, notes="Sample POS receipt invoice."))
            count("invoices")
            _insert(con, "line_items", module="invoices", record_id=pos_invoice_id, product_id=pos_item[0],
                    name=pos_item[1], qty=pos_item[2], price=pos_item[3], discount=pos_item[4], tax=pos_item[5])
            count("line_items")
            pos_payment_id = None
            if "payments" in existing:
                pos_payment_id = _insert(con, "payments", invoice_id=pos_invoice_id, amount=pos_total, currency=currency,
                    method="Cash", status="paid", provider="pos", provider_ref="DEMO-POS-2026-001",
                    token="demo-pos-payment-2026-001", payer_email="", note="Sample POS cash sale",
                    created_at=D.now(), paid_at=D.now(), created_by=user_id, channel="pos_cash", fee=0,
                    net=pos_total, payer_ref="Cash")
                count("payments")
                if "payment_events" in existing:
                    _insert(con, "payment_events", payment_id=pos_payment_id, event="pos_sale",
                            payload='{"receipt_no":"DEMO-POS-2026-001"}', created_at=D.now())
                    count("payment_events")
            _insert(con, "pos_sales", receipt_no="DEMO-POS-2026-001", invoice_id=pos_invoice_id,
                    payment_id=pos_payment_id, session_id=session_id, account_id=account_ids[2],
                    customer_name=account_specs[2][0], customer_phone=account_specs[2][2], cashier_id=user_id,
                    subtotal=round(pos_item[2] * pos_item[3], 2), discount_total=0,
                    tax_total=round(pos_total - pos_item[2] * pos_item[3], 2), total=pos_total,
                    amount_received=200, change_due=round(200 - pos_total, 2), payment_method="cash",
                    payment_status="paid", status="completed", note="Sample POS sale", created_at=D.now())
            count("pos_sales")

        D.log(con, "system", 0, "add_demo_data", {"added": added, "marker": DEMO_PRODUCT_PREFIX}, user_id)
        con.commit()
    except Exception:
        con.rollback()
        raise

    return {
        "ok": True,
        "added": added,
        "total": sum(added.values()),
        "already_present": False,
        "message": "NebrasCRM sample data was added.",
    }


def clear(con, user_id: int) -> dict:
    """Delete seeded/business demo data and leave a clean operational CRM."""
    before = _counts(con, DEMO_TABLES)
    existing = _existing_tables(con)
    try:
        for table in DEMO_TABLES:
            if table in existing:
                con.execute(f'DELETE FROM "{table}"')

        # Reset AUTO_INCREMENT counters only for tables that were cleared. Never
        # reset users or global geography IDs, because they are intentionally kept.
        D.reset_identity(con, before)

        # Keep a single audit event explaining the intentionally destructive action.
        D.log(
            con,
            "system",
            0,
            "clear_demo_data",
            {"deleted": before, "preserved": list(PRESERVED)},
            user_id,
        )
        con.commit()
    except Exception:
        con.rollback()
        raise

    return {
        "ok": True,
        "deleted": before,
        "total": sum(before.values()),
        "preserved": list(PRESERVED),
    }
