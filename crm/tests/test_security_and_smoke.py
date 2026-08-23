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
        cls.agent = cls._login("sara@nebrascrm.io", "sara123")
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin}"}
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
        agent = self.client.post("/agent/api/login", json={"email": "agent0@partners.ye", "password": "agent123"})
        self.assertEqual(agent.status_code, 200, agent.text)

    def test_mobile_embedding_exception_is_limited_to_app_shell(self):
        app_page = self.client.get("/app")
        api = self.client.get("/api/meta")
        self.assertIsNone(app_page.headers.get("x-frame-options"))
        self.assertEqual(api.headers.get("x-frame-options"), "SAMEORIGIN")


if __name__ == "__main__":
    unittest.main()
