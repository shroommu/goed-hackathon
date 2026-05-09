from __future__ import annotations

import importlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import text


def _encode_jwt(
    *,
    secret: str,
    sub: str,
    admin: bool = False,
    exp: datetime | None = None,
) -> str:
    if exp is None:
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
    payload: dict = {
        "sub": sub,
        "email": f"{sub}@example.com",
        "aud": "authenticated",
        "exp": exp,
    }
    if admin:
        payload["app_metadata"] = {"role": "admin"}
    encoded = jwt.encode(payload, secret, algorithm="HS256")
    return encoded if isinstance(encoded, str) else encoded.decode("ascii")


class Be011AuthTests(unittest.TestCase):
    API_PREFIX = "/api"

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls._db_path = os.path.join(cls._tmpdir.name, "be011_test.db")

        os.environ["DATABASE_URL"] = f"sqlite:///{cls._db_path}"
        os.environ["APP_ENV"] = "local"
        os.environ["SUPABASE_JWT_SECRET"] = "be011-test-jwt-secret"
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
        os.environ.pop("SUPABASE_JWT_SECRET", None)

    def setUp(self):
        with self.app.app_context():
            self.db.session.execute(text("DELETE FROM verification_events"))
            self.db.session.execute(text("DELETE FROM claim_requests"))
            self.db.session.execute(text("DELETE FROM companies"))
            self.db.session.commit()

    def test_submit_listing_without_token_returns_401(self):
        with self.assertLogs("app.auth_audit", level="INFO") as captured:
            response = self.client.post(
                f"{self.API_PREFIX}/companies",
                json={"startup_name": "X", "website": "https://x.dev"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["code"], "missing_auth_token")
        self.assertTrue(
            any(
                "auth_401" in r.getMessage()
                for r in captured.records
            ),
            captured.output,
        )

    def test_expired_jwt_returns_401(self):
        secret = os.environ["SUPABASE_JWT_SECRET"]
        token = _encode_jwt(
            secret=secret,
            sub="user-exp",
            exp=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        with self.assertLogs("app.auth_audit", level="INFO") as captured:
            response = self.client.post(
                f"{self.API_PREFIX}/companies",
                headers={"Authorization": f"Bearer {token}"},
                json={"startup_name": "Y", "website": "https://y.dev"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["code"], "invalid_auth_token")
        self.assertTrue(
            any(
                "token_verify_failure" in r.getMessage()
                and "expired" in r.getMessage()
                for r in captured.records
            ),
            captured.output,
        )

    def test_non_admin_cannot_access_admin_claims_list(self):
        secret = os.environ["SUPABASE_JWT_SECRET"]
        token = _encode_jwt(secret=secret, sub="regular-user", admin=False)
        with self.assertLogs("app.auth_audit", level="INFO") as captured:
            response = self.client.get(
                f"{self.API_PREFIX}/admin/claims",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"]["code"], "admin_required")
        self.assertTrue(
            any("auth_403" in r.getMessage() for r in captured.records),
            captured.output,
        )

    def test_admin_can_list_claims_and_audit_logs_mutation_on_decision(self):
        with self.app.app_context():
            company_id = self.db.session.execute(
                text("""
                    INSERT INTO companies (startup_name, website)
                    VALUES ('Co', 'https://co.dev')
                    RETURNING id
                    """),
            ).scalar_one()
            claim_id = self.db.session.execute(
                text("""
                    INSERT INTO claim_requests (company_id, user_id, status)
                    VALUES (:cid, 'u1', 'pending')
                    RETURNING id
                    """),
                {"cid": company_id},
            ).scalar_one()
            self.db.session.commit()

        secret = os.environ["SUPABASE_JWT_SECRET"]
        admin_token = _encode_jwt(secret=secret, sub="admin-user", admin=True)

        with self.assertLogs("app.auth_audit", level="INFO") as captured:
            response = self.client.patch(
                f"{self.API_PREFIX}/admin/claims/{claim_id}/verification",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"decision": "approve", "notes": "ok"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["item"]["status"], "verified")
        messages = [r.getMessage() for r in captured.records]
        self.assertTrue(
            any(
                "admin_mutation_success" in m
                and "claim_request" in m
                for m in messages
            ),
            messages,
        )
        # Structured JSON log line
        self.assertTrue(
            any(
                json.loads(m).get("event") == "admin_mutation_success"
                for m in messages
                if m.startswith("{")
            ),
        )


if __name__ == "__main__":
    unittest.main()
