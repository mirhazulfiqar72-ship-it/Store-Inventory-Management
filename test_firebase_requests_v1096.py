"""Regression tests for Firebase/Requests session integration."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
from firebase_auth_v1095 import AuthenticatedFirebaseSession


class RequestsSessionRegression(unittest.TestCase):
    def setUp(self):
        self.manager = SimpleNamespace(id_token=lambda: "sample-token", expire=lambda: None)
        self.client = AuthenticatedFirebaseSession(self.manager, "https://database.example.test")

    def test_requests_auth_hook_unoccupied(self):
        self.assertIsNone(self.client.auth)
        self.assertIs(self.client.firebase_auth, self.manager)
        req = requests.Request("GET", "https://database.example.test/store_inventory_v2/data.json")
        prepared = self.client.prepare_request(req)
        self.assertEqual(prepared.method, "GET")

    def test_real_request_pipeline_injects_token_without_callable_crash(self):
        sent = []
        def fake_send(_session, prepared, **kwargs):
            sent.append(prepared)
            reply = requests.Response()
            reply.status_code = 200
            reply._content = b"{}"
            reply.url = prepared.url
            return reply
        with patch.object(requests.Session, "send", fake_send):
            self.client.get("https://database.example.test/store_inventory_v2/data.json")
            self.client.put("https://database.example.test/store_inventory_v2/_lock.json",
                            json={"token": "sample"})
            self.client.get("https://unrelated.example.test/info")
        self.assertEqual(len(sent), 3)
        self.assertIn("sample-token", sent[0].url)
        self.assertIn("sample-token", sent[1].url)
        self.assertNotIn("sample-token", sent[2].url)
        self.assertEqual(sent[1].method, "PUT")


if __name__ == "__main__":
    unittest.main()
