import importlib
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class Be016SafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["APP_ENV"] = "local"

        import app as app_module

        importlib.reload(app_module)
        cls.app = app_module.create_app()
        cls.client = cls.app.test_client()

    def test_sparse_context_returns_follow_up_before_recommendations(self):
        with patch("app.routes_navigator.search_resources") as mock_search:
            response = self.client.post(
                "/api/navigator/chat/message",
                json={"message": "I need help", "context": {}},
            )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["recommendations"], [])
        self.assertIn("follow_up_question", body)
        mock_search.assert_not_called()

    def test_unknown_resource_id_is_filtered_out(self):
        candidates = [
            SimpleNamespace(
                id=11,
                title="Known Resource",
                description="Trusted program",
                topics="funding",
                industries="Technology",
                communities="Founders",
                locations="Utah",
                link="https://known.example.com",
            )
        ]

        llm_payload = {
            "assistant_message": "Here are recommendations",
            "derived_context": {"industry": "Technology", "objectives": ["funding"]},
            "recommendations": [
                {"id": 999, "rationale": "Hallucinated"},
                {"id": 11, "rationale": "Valid"},
            ],
        }

        with patch("app.routes_navigator.search_resources", return_value=candidates), patch(
            "app.routes_navigator.get_llm_client", return_value=object()
        ), patch(
            "app.routes_navigator.generate_llm_response", return_value=llm_payload
        ):
            response = self.client.post(
                "/api/navigator/chat/message",
                json={
                    "message": "I run a tech startup in Utah and need funding",
                    "context": {"industry": "Technology", "objectives": ["funding"]},
                },
            )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(body["recommendations"]), 1)
        self.assertEqual(body["recommendations"][0]["id"], 11)

    def test_url_mismatch_is_blocked_and_debug_reason_is_exposed(self):
        candidates = [
            SimpleNamespace(
                id=12,
                title="Official Resource",
                description="Program",
                topics="networking",
                industries="Technology",
                communities="Founders",
                locations="Utah",
                link="https://official.example.com",
            )
        ]

        llm_payload = {
            "assistant_message": "One recommendation",
            "derived_context": {
                "industry": "Technology",
                "location": "Utah",
                "objectives": ["networking"],
            },
            "recommendations": [
                {
                    "id": 12,
                    "url": "https://fake.example.com",
                    "rationale": "This should be blocked",
                }
            ],
        }

        with patch("app.routes_navigator.search_resources", return_value=candidates), patch(
            "app.routes_navigator.get_llm_client", return_value=object()
        ), patch(
            "app.routes_navigator.generate_llm_response", return_value=llm_payload
        ):
            response = self.client.post(
                "/api/navigator/chat/message?debug=1",
                headers={"X-Admin-Debug": "true"},
                json={
                    "message": "Tech startup in Utah looking for networking support",
                    "context": {
                        "industry": "Technology",
                        "location": "Utah",
                        "objectives": ["networking"],
                    },
                },
            )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["recommendations"], [])
        self.assertIn("validation_debug", body)
        self.assertEqual(body["validation_debug"]["blocked_count"], 1)
        self.assertIn(
            "url_mismatch_for_resource_id:12",
            body["validation_debug"]["validation_fail_reasons"],
        )

    def test_llm_timeout_falls_back_to_deterministic_recommendations(self):
        candidates = [
            SimpleNamespace(
                id=13,
                title="Fallback Resource",
                description="Program",
                topics="funding",
                industries="Technology",
                communities="Founders",
                locations="Utah",
                link="https://fallback.example.com",
            )
        ]

        with patch("app.routes_navigator.search_resources", return_value=candidates), patch(
            "app.routes_navigator.get_llm_client", return_value=object()
        ), patch(
            "app.routes_navigator.generate_llm_response",
            side_effect=TimeoutError("timed out"),
        ):
            response = self.client.post(
                "/api/navigator/chat/message",
                json={
                    "message": "Tech startup in Utah needs funding",
                    "context": {
                        "industry": "Technology",
                        "location": "Utah",
                        "objectives": ["funding"],
                    },
                },
            )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(body["recommendations"]), 1)
        self.assertEqual(
            body["recommendations"][0]["rationale"],
            "Selected via deterministic fallback ranking based on your provided context.",
        )


if __name__ == "__main__":
    unittest.main()
