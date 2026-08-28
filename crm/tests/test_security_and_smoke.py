"""Regression smoke tests for the repaired NebrasCRM API.

Run from crm/ with:
    python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


class NebrasApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="nebrascrm-test-")
        source_db = Path(__file__).resolve().parents[1] / "crm.db"
        cls.db_path = Path(cls.tmpdir) / "crm.db"
        shutil.copy2(source_db, cls.db_path)
        os.environ["CRM_DB_PATH"] = str(cls.db_path)
        # Import only after the per-test database path is configured.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from fastapi.testclient import TestClient
        import main
        import payments

        cls.main = main
        cls.payments = payments
        cls.client = TestClient(main.app, raise_server_exceptions=True)
        cls.admin = cls._login("admin@nebrascrm.io", "admin123")
        cls.manager = cls._login("manager@nebrascrm.io", "manager123")
        cls.agent = cls._login("sara@nebrascrm.io", "sara123")
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin}"}
        cls.manager_headers = {"Authorization": f"Bearer {cls.manager}"}
        cls.agent_headers = {"Authorization": f"Bearer {cls.agent}"}

    @classmethod
    def tearDownClass(cls):
        cls.main.con.close()
        os.environ.pop("CRM_DB_PATH", None)

    @classmethod
    def _login(cls, email, password):
        response = cls.client.post("/api/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return response.json()["token"]

    def test_legacy_demo_hash_is_upgraded_and_token_expires(self):
        stored = self.main.con.execute("SELECT password FROM users WHERE email=?", ("admin@nebrascrm.io",)).fetchone()[0]
        self.assertTrue(stored.startswith("pbkdf2_sha256$"))
        self.assertEqual(self.client.get("/api/auth/me", headers=self.admin_headers).status_code, 200)

    def test_empty_production_database_bootstraps_one_admin_from_environment(self):
        """A fresh MySQL-style deployment gets one configured, non-demo admin."""
        import sqlite3

        temporary = sqlite3.connect(":memory:")
        temporary.row_factory = sqlite3.Row
        temporary.execute("""CREATE TABLE users(
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT,
            name TEXT, role TEXT, active INTEGER, target REAL, created_at TEXT
        )""")
        temporary.execute("""CREATE TABLE audit(
            id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, record_id INTEGER,
            action TEXT, changes TEXT, user_id INTEGER, created_at TEXT
        )""")
        previous_connection = self.main.con
        env = {
            "CRM_ENV": "production",
            "CRM_BOOTSTRAP_ADMIN_EMAIL": "first.admin@example.test",
            "CRM_BOOTSTRAP_ADMIN_NAME": "First Administrator",
            "CRM_BOOTSTRAP_ADMIN_PASSWORD": "a-secure-first-password",
        }
        previous_env = {key: os.environ.get(key) for key in env}
        self.main.con = temporary
        try:
            os.environ.update(env)
            self.assertTrue(self.main._bootstrap_admin_from_environment())
            admin = temporary.execute("SELECT * FROM users").fetchone()
            self.assertEqual(admin["email"], env["CRM_BOOTSTRAP_ADMIN_EMAIL"])
            self.assertEqual(admin["role"], "admin")
            self.assertEqual(admin["active"], 1)
            self.assertTrue(admin["password"].startswith("pbkdf2_sha256$"))
            self.assertTrue(self.main.verify_pw(env["CRM_BOOTSTRAP_ADMIN_PASSWORD"], admin["password"])[0])
            self.assertFalse(self.main._bootstrap_admin_from_environment())
            self.assertEqual(temporary.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)
        finally:
            self.main.con = previous_connection
            temporary.close()
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_agent_cannot_read_or_mutate_another_agents_record(self):
        foreign = self.main.con.execute(
            "SELECT id FROM deals WHERE deleted=0 AND owner_id NOT IN (?, 0) AND owner_id IS NOT NULL LIMIT 1",
            (3,),
        ).fetchone()[0]
        self.assertEqual(self.client.get(f"/api/deals/{foreign}", headers=self.agent_headers).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/deals/{foreign}", headers=self.agent_headers).status_code, 404)

    def test_agent_cannot_spoof_owner_on_create_or_update(self):
        response = self.client.post(
            "/api/accounts",
            headers=self.agent_headers,
            json={"name": "Authorization regression account", "owner_id": 1},
        )
        self.assertEqual(response.status_code, 200, response.text)
        record_id = response.json()["id"]
        row = self.main.con.execute("SELECT owner_id FROM accounts WHERE id=?", (record_id,)).fetchone()
        self.assertEqual(row["owner_id"], 3)

        response = self.client.put(
            f"/api/accounts/{record_id}",
            headers=self.agent_headers,
            json={"name": "Updated authorization account", "owner_id": 1},
        )
        self.assertEqual(response.status_code, 200, response.text)
        row = self.main.con.execute("SELECT owner_id FROM accounts WHERE id=?", (record_id,)).fetchone()
        self.assertEqual(row["owner_id"], 3)

    def test_agents_cannot_modify_shared_catalogue_data(self):
        response = self.client.post(
            "/api/products", headers=self.agent_headers,
            json={"name": "Unauthorized product", "unit_price": 1},
        )
        self.assertEqual(response.status_code, 403)

    def test_export_requires_bearer_header_and_is_scoped(self):
        no_header = self.client.get(f"/api/deals/export/csv?token={self.agent}")
        self.assertEqual(no_header.status_code, 401)
        response = self.client.get("/api/deals/export/csv", headers=self.agent_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["content-type"])
        self.assertIn("id,name", response.text)

    def test_resend_delivery_settings_are_admin_only_and_secret_is_masked(self):
        self.assertEqual(self.client.get("/api/email/settings", headers=self.agent_headers).status_code, 403)
        saved = self.client.put(
            "/api/email/settings", headers=self.admin_headers,
            json={"email_provider": "resend", "resend_api_key": "re_test_secret_123",
                  "resend_from": "NebrasCRM <sales@example.com>", "resend_reply_to": "support@example.com"},
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        settings = self.client.get("/api/email/settings", headers=self.admin_headers)
        self.assertEqual(settings.status_code, 200, settings.text)
        body = settings.json()
        self.assertEqual(body["email_provider"], "resend")
        self.assertTrue(body["resend_configured"])
        self.assertEqual(body["resend_api_key"], "••••")
        self.assertNotIn("re_test_secret_123", settings.text)
        self.assertEqual(
            self.client.put("/api/email/settings", headers=self.admin_headers,
                            json={"email_provider": "not-a-provider"}).status_code,
            400,
        )

    def test_sensitive_admin_and_financial_operations_are_not_open_to_agents(self):
        self.assertEqual(self.client.get("/api/admin/users", headers=self.agent_headers).status_code, 403)
        self.assertEqual(self.client.get("/api/admin/workflows", headers=self.agent_headers).status_code, 403)
        self.assertEqual(self.client.get("/api/portal-access", headers=self.agent_headers).status_code, 403)
        self.assertEqual(
            self.client.post("/api/payments/manual", headers=self.agent_headers,
                             json={"invoice_id": 1, "amount": 1}).status_code,
            403,
        )

    def test_payment_capture_and_refund_webhook_are_idempotent(self):
        invoice = self.main.con.execute(
            "SELECT id,paid_amount FROM invoices WHERE deleted=0 AND amount > paid_amount AND status!='Cancelled' LIMIT 1"
        ).fetchone()
        self.assertIsNotNone(invoice)
        link = self.client.post(
            "/api/payments/link", headers=self.admin_headers,
            json={"invoice_id": invoice["id"], "amount": 1},
        )
        self.assertEqual(link.status_code, 200, link.text)
        token = link.json()["token"]
        paid = self.client.post(
            f"/pay/api/{token}/confirm",
            json={"channel": "visa", "card_number": "4242 4242 4242 4242", "exp": "12/30", "cvc": "123"},
        )
        self.assertEqual(paid.status_code, 200, paid.text)
        self.assertEqual(
            self.client.post(
                f"/pay/api/{token}/confirm",
                json={"channel": "visa", "card_number": "4242 4242 4242 4242", "exp": "12/30", "cvc": "123"},
            ).status_code,
            409,
        )

        payload = json.dumps({"token": token, "event": "payment.refunded", "ref": "test-refund"}).encode()
        signature = hmac.new(self.payments.WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
        first = self.client.post("/pay/webhook", content=payload, headers={"X-Signature": signature})
        second = self.client.post("/pay/webhook", content=payload, headers={"X-Signature": signature})
        self.assertEqual(first.status_code, 200, first.text)
        self.assertTrue(first.json()["applied"])
        self.assertEqual(second.status_code, 200, second.text)
        self.assertFalse(second.json()["applied"])
        restored = self.main.con.execute("SELECT paid_amount FROM invoices WHERE id=?", (invoice["id"],)).fetchone()[0]
        self.assertEqual(restored, invoice["paid_amount"])

    def test_pos_checkout_updates_inventory_creates_invoice_payment_and_receipt(self):
        product = self.client.post(
            "/api/products", headers=self.admin_headers,
            json={"name": "POS regression product", "code": "POS-REG", "unit_price": 100,
                  "qty_in_stock": 3, "tax_rate": 5, "active": "Yes"},
        )
        self.assertEqual(product.status_code, 200, product.text)
        product_id = product.json()["id"]

        opened = self.client.post(
            "/api/pos/sessions/open", headers=self.agent_headers,
            json={"opening_cash": 0, "note": "POS regression shift"},
        )
        self.assertEqual(opened.status_code, 200, opened.text)
        session_id = opened.json()["session"]["id"]

        sale = self.client.post(
            "/api/pos/sale", headers=self.agent_headers,
            json={"items": [{"product_id": product_id, "qty": 2, "discount": 0}],
                  "payment_method": "cash", "amount_received": 250, "customer_name": "Walk-in regression"},
        )
        self.assertEqual(sale.status_code, 200, sale.text)
        payload = sale.json()
        self.assertEqual(payload["totals"]["subtotal"], 200.0)
        self.assertEqual(payload["totals"]["tax_total"], 10.0)
        self.assertEqual(payload["totals"]["total"], 210.0)
        self.assertEqual(payload["change_due"], 40.0)
        self.assertIsNotNone(payload["invoice_id"])
        self.assertIsNotNone(payload["payment_id"])

        stock = self.client.get(f"/api/products/{product_id}", headers=self.agent_headers)
        self.assertEqual(stock.status_code, 200, stock.text)
        self.assertEqual(stock.json()["qty_in_stock"], 1.0)
        receipt = self.client.get(f"/api/pos/sales/{payload['sale_id']}/receipt", headers=self.agent_headers)
        self.assertEqual(receipt.status_code, 200, receipt.text)
        self.assertEqual(receipt.json()["sale"]["receipt_no"], payload["receipt_no"])
        self.assertEqual(receipt.json()["items"][0]["product_id"], product_id)
        self.assertEqual(self.client.get("/api/pos/sales", headers=self.agent_headers).status_code, 200)

        closed = self.client.post(
            f"/api/pos/sessions/{session_id}/close", headers=self.agent_headers,
            json={"closing_cash": 210},
        )
        self.assertEqual(closed.status_code, 200, closed.text)
        self.assertEqual(closed.json()["session"]["difference"], 0.0)
        self.assertEqual(
            self.client.post(f"/api/pos/sales/{payload['sale_id']}/refund", headers=self.agent_headers, json={}).status_code,
            403,
        )
        refunded = self.client.post(
            f"/api/pos/sales/{payload['sale_id']}/refund", headers=self.manager_headers,
            json={"note": "Regression refund"},
        )
        self.assertEqual(refunded.status_code, 200, refunded.text)
        restored = self.client.get(f"/api/products/{product_id}", headers=self.agent_headers).json()
        self.assertEqual(restored["qty_in_stock"], 3.0)
        invoice = self.main.con.execute("SELECT status,paid_amount FROM invoices WHERE id=?", (payload["invoice_id"],)).fetchone()
        self.assertEqual(invoice["status"], "Cancelled")
        self.assertEqual(invoice["paid_amount"], 0.0)

    def test_printable_invoice_and_quote_include_customer_items_and_totals(self):
        account = self.main.con.execute("SELECT id,name FROM accounts WHERE deleted=0 ORDER BY id LIMIT 1").fetchone()
        self.assertIsNotNone(account)
        product = self.client.post(
            "/api/products", headers=self.admin_headers,
            json={"name": "Document test product", "unit_price": 100, "active": "Yes"},
        )
        self.assertEqual(product.status_code, 200, product.text)
        product_id = product.json()["id"]
        invoice = self.client.post(
            "/api/invoices", headers=self.admin_headers,
            json={"subject": "Invoice print test", "account_id": account["id"], "invoice_date": "2026-08-23", "due_date": "2026-09-23"},
        )
        self.assertEqual(invoice.status_code, 200, invoice.text)
        invoice_id = invoice.json()["id"]
        items = [{"product_id": product_id, "name": "Document test product", "qty": 2, "price": 100, "discount": 10, "tax": 5}]
        saved = self.client.post(f"/api/items/invoices/{invoice_id}", headers=self.admin_headers, json={"items": items})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual(saved.json()["total"], 189.0)
        document = self.client.get(f"/api/documents/invoice/{invoice_id}", headers=self.admin_headers)
        self.assertEqual(document.status_code, 200, document.text)
        payload = document.json()
        self.assertEqual(payload["account"]["name"], account["name"])
        self.assertEqual(payload["items"][0]["line_total"], 189.0)
        self.assertEqual(payload["totals"]["subtotal"], 200.0)
        self.assertEqual(payload["totals"]["discount_total"], 20.0)
        self.assertEqual(payload["totals"]["tax_total"], 9.0)
        self.assertEqual(payload["totals"]["total"], 189.0)
        self.assertEqual(self.client.get(f"/api/documents/invoice/{invoice_id}", headers=self.agent_headers).status_code, 404)

        payment = self.client.post(
            "/api/payments/manual", headers=self.admin_headers,
            json={"invoice_id": invoice_id, "amount": 40, "method": "Cash", "note": "Voucher regression test"},
        )
        self.assertEqual(payment.status_code, 200, payment.text)
        payment_id = payment.json()["payment_id"]
        voucher = self.client.get(f"/api/documents/payment/{payment_id}", headers=self.admin_headers)
        self.assertEqual(voucher.status_code, 200, voucher.text)
        voucher_data = voucher.json()
        self.assertEqual(voucher_data["label_ar"], "سند دفع")
        self.assertEqual(voucher_data["payment"]["amount"], 40.0)
        self.assertEqual(voucher_data["payment"]["method"], "Cash")
        self.assertEqual(voucher_data["invoice"]["id"], invoice_id)
        self.assertEqual(voucher_data["invoice"]["total"], 189.0)
        self.assertEqual(voucher_data["invoice"]["remaining"], 149.0)
        self.assertEqual(self.client.get(f"/api/documents/payment/{payment_id}", headers=self.agent_headers).status_code, 404)

        quote = self.client.post(
            "/api/quotes", headers=self.admin_headers,
            json={"subject": "Quotation print test", "account_id": account["id"], "valid_until": "2026-10-01"},
        )
        self.assertEqual(quote.status_code, 200, quote.text)
        quote_id = quote.json()["id"]
        self.assertEqual(
            self.client.post(f"/api/items/quotes/{quote_id}", headers=self.admin_headers, json={"items": items}).status_code,
            200,
        )
        quote_document = self.client.get(f"/api/documents/quote/{quote_id}", headers=self.admin_headers)
        self.assertEqual(quote_document.status_code, 200, quote_document.text)
        self.assertEqual(quote_document.json()["totals"]["total"], 189.0)

    def test_global_geography_is_loaded_from_the_bundled_dataset(self):
        status = self.client.get("/api/geo/status", headers=self.admin_headers)
        self.assertEqual(status.status_code, 200, status.text)
        counts = status.json()["counts"]
        self.assertGreaterEqual(counts["countries"], 250)
        self.assertGreaterEqual(counts["regions"], 3_800)
        self.assertGreaterEqual(counts["cities"], 235_000)

        countries = self.client.get("/api/geo/countries?q=United", headers=self.admin_headers).json()
        usa = next(row for row in countries if row["code"] == "US")
        regions = self.client.get(
            f"/api/geo/regions?country_id={usa['id']}&q=California", headers=self.admin_headers
        ).json()
        self.assertTrue(regions)
        cities = self.client.get(
            f"/api/geo/cities?region_id={regions[0]['id']}&q=San%20Francisco", headers=self.admin_headers
        ).json()
        san_francisco = next(city for city in cities if city["name_en"] == "San Francisco")
        neighborhood = self.client.post(
            "/api/geo/neighborhoods", headers=self.admin_headers,
            json={"name": "Regression neighborhood", "city_id": san_francisco["id"]},
        )
        self.assertEqual(neighborhood.status_code, 200, neighborhood.text)
        street = self.client.post(
            "/api/geo/streets", headers=self.admin_headers,
            json={"name": "Regression street", "neighborhood_id": neighborhood.json()["id"]},
        )
        self.assertEqual(street.status_code, 200, street.text)

    def test_customer_and_partner_portals_still_authenticate(self):
        portal = self.client.post("/portal/api/login", json={"email": "ahmed.saleh@example.com", "password": "portal123"})
        self.assertEqual(portal.status_code, 200, portal.text)
        portal_headers = {"Authorization": f"Bearer {portal.json()['token']}"}
        portal_me = self.client.get("/portal/api/me", headers=portal_headers)
        self.assertEqual(portal_me.status_code, 200, portal_me.text)

        portal_invoice = self.client.post(
            "/api/invoices", headers=self.admin_headers,
            json={"subject": "Portal voucher regression", "account_id": portal_me.json()["account_id"], "amount": 20},
        )
        self.assertEqual(portal_invoice.status_code, 200, portal_invoice.text)
        portal_payment = self.client.post(
            "/api/payments/manual", headers=self.admin_headers,
            json={"invoice_id": portal_invoice.json()["id"], "amount": 5, "method": "Cash"},
        )
        self.assertEqual(portal_payment.status_code, 200, portal_payment.text)
        portal_voucher = self.client.get(
            f"/portal/api/payments/{portal_payment.json()['payment_id']}/receipt", headers=portal_headers,
        )
        self.assertEqual(portal_voucher.status_code, 200, portal_voucher.text)
        self.assertEqual(portal_voucher.json()["payment"]["amount"], 5.0)
        self.assertEqual(portal_voucher.json()["contact"]["name"], portal_me.json()["name"])

        foreign_account = self.main.con.execute(
            "SELECT id FROM accounts WHERE deleted=0 AND id!=? ORDER BY id LIMIT 1", (portal_me.json()["account_id"],)
        ).fetchone()
        self.assertIsNotNone(foreign_account)
        foreign_invoice = self.client.post(
            "/api/invoices", headers=self.admin_headers,
            json={"subject": "Foreign portal voucher", "account_id": foreign_account["id"], "amount": 20},
        )
        self.assertEqual(foreign_invoice.status_code, 200, foreign_invoice.text)
        foreign_payment = self.client.post(
            "/api/payments/manual", headers=self.admin_headers,
            json={"invoice_id": foreign_invoice.json()["id"], "amount": 5, "method": "Cash"},
        )
        self.assertEqual(foreign_payment.status_code, 200, foreign_payment.text)
        self.assertEqual(
            self.client.get(
                f"/portal/api/payments/{foreign_payment.json()['payment_id']}/receipt", headers=portal_headers,
            ).status_code,
            404,
        )

        agent = self.client.post("/agent/api/login", json={"email": "agent0@partners.ye", "password": "agent123"})
        self.assertEqual(agent.status_code, 200, agent.text)

    def test_mysql_alias_uses_the_mariadb_dialect(self):
        self.assertEqual(self.main.D.normalize_engine("mysql"), "mariadb")
        self.assertEqual(self.main.D.normalize_engine("MARIADB"), "mariadb")
        self.assertEqual(self.main.D.normalize_engine("postgres"), "postgresql")

    def test_mariadb_dialect_translation_for_core_sql(self):
        db = self.main.D
        original_engine = db.DB_ENGINE
        try:
            db.DB_ENGINE = "mariadb"
            upsert = db._translate_sql(
                'INSERT INTO "settings"(key,value) VALUES(?,?) '
                'ON CONFLICT(key) DO UPDATE SET value=excluded.value'
            )
            self.assertIn('`settings`', upsert)
            self.assertIn('ON DUPLICATE KEY UPDATE', upsert)
            self.assertIn('VALUES(value)', upsert)
            self.assertEqual(upsert.count('%s'), 2)
            ddl = db._translate_sql('CREATE TABLE t(id INTEGER PRIMARY KEY AUTOINCREMENT, value REAL)')
            self.assertIn('BIGINT AUTO_INCREMENT PRIMARY KEY', ddl)
            self.assertIn('DOUBLE', ddl)
            self.assertIn('CURRENT_DATE', db._translate_sql("SELECT date('now')"))
        finally:
            db.DB_ENGINE = original_engine

    def test_mariadb_pos_schema_uses_an_indexable_timestamp_and_upgrades_legacy_text(self):
        """MySQL 8 forbids a normal index on a TEXT created_at column."""
        db = self.main.D
        pos = self.main.POS

        class RawCursor:
            def __init__(self, owner):
                self.owner = owner
                self.sql = ""
                self.lastrowid = 0
                self.rowcount = 0

            def execute(self, sql, params=()):
                self.sql = sql
                self.owner.calls.append(sql)

            def fetchone(self):
                if "information_schema.columns" in self.sql:
                    # MySQL may preserve the INFORMATION_SCHEMA column name in
                    # uppercase; POS migration must not depend on its mapping key.
                    return {"DATA_TYPE": "text"}
                return None

            def fetchall(self):
                return []

            def close(self):
                pass

        class RawConnection:
            def __init__(self):
                self.calls = []
                self.committed = False

            def cursor(self):
                return RawCursor(self)

            def commit(self):
                self.committed = True

            def rollback(self):
                pass

            def close(self):
                pass

        raw = RawConnection()
        original_engine = db.DB_ENGINE
        try:
            db.DB_ENGINE = "mariadb"
            pos.init_tables(db.MariaConnection(raw))
        finally:
            db.DB_ENGINE = original_engine

        sales_ddl = next(sql for sql in raw.calls if "CREATE TABLE IF NOT EXISTS pos_sales" in sql)
        self.assertIn("created_at VARCHAR(40)", sales_ddl)
        legacy_lookup = next(sql for sql in raw.calls if "information_schema.columns" in sql)
        self.assertIn("data_type IN ('tinytext','text','mediumtext','longtext')", legacy_lookup)
        alter_index = next(index for index, sql in enumerate(raw.calls)
                           if "ALTER TABLE pos_sales MODIFY COLUMN created_at VARCHAR(40)" in sql)
        created_index = next(index for index, sql in enumerate(raw.calls)
                             if "ix_pos_sales_created" in sql)
        self.assertLess(alter_index, created_index)
        self.assertTrue(raw.committed)

    def test_postgresql_dialect_translation_for_core_sql(self):
        db = self.main.D
        original_engine = db.DB_ENGINE
        try:
            db.DB_ENGINE = "postgresql"
            upsert = db._translate_sql(
                'INSERT INTO "settings"("key","value") VALUES(?,?) '
                'ON CONFLICT("key") DO UPDATE SET "value"=excluded.value'
            )
            self.assertIn('"settings"', upsert)
            self.assertIn('ON CONFLICT("key") DO UPDATE', upsert)
            self.assertIn('excluded.value', upsert)
            self.assertEqual(upsert.count('%s'), 2)
            ddl = db._translate_sql('CREATE TABLE t(id INTEGER PRIMARY KEY AUTOINCREMENT, value REAL)')
            self.assertIn('BIGSERIAL PRIMARY KEY', ddl)
            self.assertIn('REAL', ddl)
            self.assertEqual('SELECT CURRENT_DATE::text', db._translate_sql("SELECT date('now')"))
        finally:
            db.DB_ENGINE = original_engine

    def test_mobile_embedding_exception_is_limited_to_app_shell(self):
        app_page = self.client.get("/app")
        api = self.client.get("/api/meta")
        self.assertIsNone(app_page.headers.get("x-frame-options"))
        self.assertEqual(api.headers.get("x-frame-options"), "SAMEORIGIN")

    def test_y_demo_data_add_is_admin_only_idempotent_and_restores_a_working_sample_pack(self):
        self.assertEqual(
            self.client.post("/api/admin/demo-data/add", headers=self.agent_headers,
                             json={"confirmation": "ADD DEMO DATA"}).status_code,
            403,
        )
        # Exercise the intended recovery path: clean a database, then restore a
        # compact sample pack from System Settings without changing users/geography.
        cleared = self.client.post("/api/admin/demo-data/clear", headers=self.admin_headers,
                                   json={"confirmation": "DELETE DEMO DATA"})
        self.assertEqual(cleared.status_code, 200, cleared.text)
        self.assertEqual(
            self.client.post("/api/admin/demo-data/add", headers=self.admin_headers,
                             json={"confirmation": "wrong phrase"}).status_code,
            400,
        )
        added = self.client.post("/api/admin/demo-data/add", headers=self.admin_headers,
                                 json={"confirmation": "ADD DEMO DATA"})
        self.assertEqual(added.status_code, 200, added.text)
        payload = added.json()
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["already_present"])
        self.assertGreater(payload["total"], 10)
        self.assertGreaterEqual(self.main.con.execute(
            "SELECT COUNT(*) FROM products WHERE code LIKE 'DEMO-POS-%'"
        ).fetchone()[0], 4)
        self.assertGreaterEqual(self.main.con.execute("SELECT COUNT(*) FROM pos_sales").fetchone()[0], 1)
        self.assertGreaterEqual(self.main.con.execute("SELECT COUNT(*) FROM invoices").fetchone()[0], 2)
        summary = self.client.get("/api/admin/demo-data/summary", headers=self.admin_headers)
        self.assertTrue(summary.json()["sample_pack_present"])
        self.assertEqual(summary.json()["add_confirmation"], "ADD DEMO DATA")

        repeated = self.client.post("/api/admin/demo-data/add", headers=self.admin_headers,
                                    json={"confirmation": "ADD DEMO DATA"})
        self.assertEqual(repeated.status_code, 200, repeated.text)
        self.assertTrue(repeated.json()["already_present"])
        self.assertEqual(repeated.json()["total"], 0)

    def test_z_demo_data_cleanup_is_admin_only_and_preserves_system_data(self):
        self.assertEqual(
            self.client.get("/api/admin/demo-data/summary", headers=self.agent_headers).status_code,
            403,
        )
        summary = self.client.get("/api/admin/demo-data/summary", headers=self.admin_headers)
        self.assertEqual(summary.status_code, 200, summary.text)
        self.assertGreater(summary.json()["total"], 0)
        self.assertEqual(
            self.client.post("/api/admin/demo-data/clear", headers=self.admin_headers,
                             json={"confirmation": "not confirmed"}).status_code,
            400,
        )
        cleared = self.client.post("/api/admin/demo-data/clear", headers=self.admin_headers,
                                   json={"confirmation": "DELETE DEMO DATA"})
        self.assertEqual(cleared.status_code, 200, cleared.text)
        self.assertTrue(cleared.json()["ok"])
        for table in ("accounts", "leads", "deals", "invoices", "payments", "agents"):
            self.assertEqual(self.main.con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0)
        self.assertGreaterEqual(self.main.con.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)
        self.assertGreaterEqual(
            self.main.con.execute("SELECT COUNT(*) FROM geo_villages").fetchone()[0], 235_000
        )
        self.assertEqual(self.client.get("/api/auth/me", headers=self.admin_headers).status_code, 200)


if __name__ == "__main__": 
    unittest.main()
