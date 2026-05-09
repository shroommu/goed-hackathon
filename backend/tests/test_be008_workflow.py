import importlib
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from sqlalchemy import text


class Be008WorkflowTests(unittest.TestCase):
    API_PREFIX = "/api"
    AUTH_GET = "app.auth.requests.get"

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls._db_path = os.path.join(cls._tmpdir.name, "be008_test.db")

        os.environ["DATABASE_URL"] = f"sqlite:///{cls._db_path}"
        os.environ["APP_ENV"] = "local"
        os.environ["SUPABASE_URL"] = "https://example.supabase.co"
        os.environ["SUPABASE_PUBLISHABLE_KEY"] = "sb_publishable_test_key"
        os.environ.pop("DB_SSLMODE", None)

        import app.config as config_module

        importlib.reload(config_module)

        import app as app_module

        importlib.reload(app_module)

        cls._app_module = app_module
        cls.app = app_module.create_app()
        cls.client = cls.app.test_client()

        from app.extensions import db

        cls.db = db
        with cls.app.app_context():
            cls.db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS companies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        startup_name TEXT,
                        description TEXT,
                        website TEXT,
                        stage TEXT,
                        employees TEXT,
                        sector TEXT,
                        full_address TEXT,
                        linkedin TEXT,
                        updated_at TEXT,
                        archived INTEGER NOT NULL DEFAULT 0
                    )
                    """))
            cls.db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS claim_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_id INTEGER NOT NULL,
                        user_id TEXT,
                        submitter_email TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        message TEXT,
                        requested_updates TEXT
                    )
                    """))
            cls.db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS verification_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        claim_request_id INTEGER,
                        event_type TEXT,
                        actor_email TEXT,
                        notes TEXT
                    )
                    """))
            cls.db.session.commit()

    @classmethod
    def tearDownClass(cls):
        cls._tmpdir.cleanup()

    def setUp(self):
        with self.app.app_context():
            self.db.session.execute(text("DELETE FROM verification_events"))
            self.db.session.execute(text("DELETE FROM claim_requests"))
            self.db.session.execute(text("DELETE FROM companies"))
            self.db.session.commit()

    def _insert_company(
        self, startup_name: str = "Acme", website: str = "https://acme.com"
    ) -> int:
        with self.app.app_context():
            company_id = self.db.session.execute(
                text("""
                    INSERT INTO companies (startup_name, website, description, stage, employees, sector, full_address, linkedin)
                    VALUES (:startup_name, :website, 'desc', 'seed', '10', 'software', 'Utah', 'https://linkedin.com/company/acme')
                    RETURNING id
                    """),
                {"startup_name": startup_name, "website": website},
            ).scalar_one()
            self.db.session.commit()
            return int(company_id)

    def _auth_response(
        self,
        user_id: str,
        email: str,
        *,
        role: str | None = None,
        roles: list[str] | None = None,
    ):
        app_metadata = {}
        if role:
            app_metadata["role"] = role
        if roles:
            app_metadata["roles"] = roles

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "id": user_id,
            "email": email,
            "app_metadata": app_metadata,
        }
        return response

    def test_create_listing_requires_required_fields(self):
        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("u-list", "lister@example.com"),
        ):
            response = self.client.post(
                f"{self.API_PREFIX}/companies",
                headers={"Authorization": "Bearer token-list"},
                json={"startup_name": "Only Name"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"]["code"], "invalid_request_body")

    def test_create_listing_success(self):
        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("u-list", "lister@example.com"),
        ):
            response = self.client.post(
                f"{self.API_PREFIX}/companies",
                headers={"Authorization": "Bearer token-list"},
                json={
                    "startup_name": "Bright Labs",
                    "website": "https://brightlabs.dev",
                    "description": "A new startup.",
                    "stage": "seed",
                    "employees": "12",
                    "sector": "AI",
                    "full_address": "Salt Lake City, UT",
                    "linkedin": "https://linkedin.com/company/brightlabs",
                },
            )

        body = response.get_json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["item"]["startup_name"], "Bright Labs")
        self.assertEqual(body["item"]["website"], "https://brightlabs.dev")
        self.assertEqual(body["duplicate_domain_matches"], [])

    def test_create_claim_success(self):
        company_id = self._insert_company()

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("user-1", "owner@example.com"),
        ):
            response = self.client.post(
                f"{self.API_PREFIX}/companies/{company_id}/claims",
                headers={"Authorization": "Bearer token-1"},
                json={
                    "role_at_company": "Founder",
                    "claimant_note": "I am the founder.",
                },
            )

        body = response.get_json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["item"]["status"], "pending")
        self.assertEqual(body["item"]["company_id"], company_id)
        self.assertEqual(body["item"]["user_id"], "user-1")

    def test_claim_conflict_when_company_has_pending_or_verified_claim(self):
        company_id = self._insert_company()
        with self.app.app_context():
            self.db.session.execute(
                text("""
                    INSERT INTO claim_requests (company_id, user_id, submitter_email, status)
                    VALUES (:company_id, 'other-user', 'other@example.com', 'pending')
                    """),
                {"company_id": company_id},
            )
            self.db.session.commit()

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("user-2", "new@example.com"),
        ):
            response = self.client.post(
                f"{self.API_PREFIX}/companies/{company_id}/claims",
                headers={"Authorization": "Bearer token-2"},
                json={"role_at_company": "Operator"},
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "claim_conflict")

    def test_claim_conflict_when_user_has_active_pending_claim(self):
        company_one = self._insert_company(
            startup_name="One", website="https://one.dev"
        )
        company_two = self._insert_company(
            startup_name="Two", website="https://two.dev"
        )

        with self.app.app_context():
            self.db.session.execute(
                text("""
                    INSERT INTO claim_requests (company_id, user_id, submitter_email, status)
                    VALUES (:company_id, 'user-1', 'owner@example.com', 'pending')
                    """),
                {"company_id": company_one},
            )
            self.db.session.commit()

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("user-1", "owner@example.com"),
        ):
            response = self.client.post(
                f"{self.API_PREFIX}/companies/{company_two}/claims",
                headers={"Authorization": "Bearer token-1"},
                json={"role_at_company": "CEO"},
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "claim_conflict")

    def test_patch_company_allows_verified_owner_only(self):
        company_id = self._insert_company()
        with self.app.app_context():
            self.db.session.execute(
                text("""
                    INSERT INTO claim_requests (company_id, user_id, submitter_email, status)
                    VALUES (:company_id, 'verified-user', 'verified@example.com', 'verified')
                    """),
                {"company_id": company_id},
            )
            self.db.session.commit()

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("verified-user", "verified@example.com"),
        ):
            ok_response = self.client.patch(
                f"{self.API_PREFIX}/companies/{company_id}",
                headers={"Authorization": "Bearer token-ok"},
                json={"description": "Updated by verified owner"},
            )

        self.assertEqual(ok_response.status_code, 200)
        self.assertEqual(
            ok_response.get_json()["item"]["description"],
            "Updated by verified owner",
        )

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("pending-user", "pending@example.com"),
        ):
            deny_response = self.client.patch(
                f"{self.API_PREFIX}/companies/{company_id}",
                headers={"Authorization": "Bearer token-deny"},
                json={"description": "Should fail"},
            )

        self.assertEqual(deny_response.status_code, 403)
        self.assertEqual(
            deny_response.get_json()["error"]["code"], "ownership_required"
        )

    def test_claim_status_endpoint_returns_claim_and_audit_events(self):
        company_id = self._insert_company()

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("user-1", "owner@example.com"),
        ):
            create_response = self.client.post(
                f"{self.API_PREFIX}/companies/{company_id}/claims",
                headers={"Authorization": "Bearer token-1"},
                json={
                    "role_at_company": "Founder",
                    "claimant_note": "I can verify ownership.",
                },
            )

        self.assertEqual(create_response.status_code, 201)

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("user-1", "owner@example.com"),
        ):
            status_response = self.client.get(
                f"{self.API_PREFIX}/companies/{company_id}/claims/me",
                headers={"Authorization": "Bearer token-1"},
            )

        self.assertEqual(status_response.status_code, 200)
        body = status_response.get_json()
        self.assertEqual(body["item"]["company_id"], company_id)
        self.assertEqual(body["item"]["status"], "pending")
        self.assertEqual(body["item"]["role_at_company"], "Founder")
        self.assertGreaterEqual(len(body["item"]["verification_events"]), 1)
        self.assertEqual(
            body["item"]["verification_events"][0]["event_type"],
            "claim_submitted",
        )

    def test_admin_can_approve_claim_and_verified_owner_can_update_company(self):
        company_id = self._insert_company()

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("owner-1", "owner@example.com"),
        ):
            create_response = self.client.post(
                f"{self.API_PREFIX}/companies/{company_id}/claims",
                headers={"Authorization": "Bearer owner-token"},
                json={"role_at_company": "CEO"},
            )

        self.assertEqual(create_response.status_code, 201)
        claim_id = create_response.get_json()["item"]["id"]

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response(
                "admin-1", "admin@example.com", role="admin"
            ),
        ):
            approve_response = self.client.patch(
                f"{self.API_PREFIX}/admin/claims/{claim_id}/verification",
                headers={"Authorization": "Bearer admin-token"},
                json={
                    "decision": "approve",
                    "notes": "Domain verification passed.",
                },
            )

        self.assertEqual(approve_response.status_code, 200)
        approved = approve_response.get_json()["item"]
        self.assertEqual(approved["status"], "verified")
        self.assertEqual(
            approved["verification_events"][-1]["event_type"], "claim_approved"
        )

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("owner-1", "owner@example.com"),
        ):
            patch_response = self.client.patch(
                f"{self.API_PREFIX}/companies/{company_id}",
                headers={"Authorization": "Bearer owner-token"},
                json={"description": "Approved owner update."},
            )

        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(
            patch_response.get_json()["item"]["description"],
            "Approved owner update.",
        )

    def test_admin_can_reject_claim_and_rejected_user_cannot_publish(self):
        company_id = self._insert_company()

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("owner-2", "owner2@example.com"),
        ):
            create_response = self.client.post(
                f"{self.API_PREFIX}/companies/{company_id}/claims",
                headers={"Authorization": "Bearer owner2-token"},
                json={"role_at_company": "Founder"},
            )

        self.assertEqual(create_response.status_code, 201)
        claim_id = create_response.get_json()["item"]["id"]

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response(
                "admin-1", "admin@example.com", role="admin"
            ),
        ):
            reject_response = self.client.patch(
                f"{self.API_PREFIX}/admin/claims/{claim_id}/verification",
                headers={"Authorization": "Bearer admin-token"},
                json={"decision": "reject", "notes": "Insufficient proof."},
            )

        self.assertEqual(reject_response.status_code, 200)
        self.assertEqual(reject_response.get_json()["item"]["status"], "rejected")

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("owner-2", "owner2@example.com"),
        ):
            update_response = self.client.patch(
                f"{self.API_PREFIX}/companies/{company_id}",
                headers={"Authorization": "Bearer owner2-token"},
                json={"description": "Should not publish"},
            )

        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(
            update_response.get_json()["error"]["code"],
            "ownership_required",
        )

    def test_non_admin_cannot_decide_claim(self):
        company_id = self._insert_company()

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("owner-3", "owner3@example.com"),
        ):
            create_response = self.client.post(
                f"{self.API_PREFIX}/companies/{company_id}/claims",
                headers={"Authorization": "Bearer owner3-token"},
                json={"role_at_company": "Founder"},
            )

        self.assertEqual(create_response.status_code, 201)
        claim_id = create_response.get_json()["item"]["id"]

        with patch(
            self.AUTH_GET,
            return_value=self._auth_response("user-x", "userx@example.com"),
        ):
            response = self.client.patch(
                f"{self.API_PREFIX}/admin/claims/{claim_id}/verification",
                headers={"Authorization": "Bearer user-token"},
                json={"decision": "approve"},
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"]["code"], "admin_required")


if __name__ == "__main__":
    unittest.main()
