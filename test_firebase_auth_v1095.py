"""v1.0.95 offline tests: Firebase authentication, scoped tokens, no password storage."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
import firebase_auth_v1095 as login


class Response:
    def __init__(self, data=None, status_code=200):
        self.payload = data or {}
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = json.dumps(self.payload)
    def json(self):
        return self.payload


class FakeAuthHTTP:
    def __init__(self):
        self.requests = []
    def post(self, url, **kwargs):
        self.requests.append((url, kwargs))
        if url.startswith("https://identitytoolkit.googleapis.com/"):
            return Response({"idToken":"short-lived-id-token",
                             "refreshToken":"refresh-token-A", "localId":"allowed-uid",
                             "expiresIn":"3600"})
        if url.startswith("https://securetoken.googleapis.com/"):
            return Response({"id_token":"new-id-token",
                             "refresh_token":"refresh-token-B", "user_id":"allowed-uid",
                             "expires_in":"3600"})
        raise AssertionError("Unexpected network destination: " + url)


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.http = FakeAuthHTTP()
        self.clock = [1000.]
        self.auth = login.FirebaseEmailAuth(
            self.tmp.name, session=self.http, clock=lambda: self.clock[0], user_data_dir=self.tmp.name)
        no_dpapi = patch.object(login, "_secure_windows_token_storage", return_value=None)
        no_dpapi.start()
        self.addCleanup(no_dpapi.stop)

    def test_password_not_persisted_and_api_key_saved(self):
        self.auth.sign_in("public-web-key","authorized@example.com","PRIVATE-PASSWORD")
        self.assertEqual(self.auth.uid,"allowed-uid")
        self.assertEqual(self.auth.id_token(),"short-lived-id-token")
        self.assertTrue(self.auth.config_file.is_file())
        self.assertFalse(self.auth.token_file.exists(),
                         "Without DPAPI, a refresh token MUST NEVER be written as plaintext")
        config = self.auth.config_file.read_text()
        self.assertIn("public-web-key", config)
        self.assertNotIn("PRIVATE-PASSWORD", config)
        self.assertNotIn("refresh-token-A", config)
        self.assertEqual(self.http.requests[0][1]["json"]["password"],"PRIVATE-PASSWORD")

    def test_expired_token_refreshes_using_google_securetoken(self):
        self.auth.sign_in("public-web-key","authorized@example.com","PRIVATE-PASSWORD")
        self.clock[0] += 5000
        self.assertEqual(self.auth.id_token(),"new-id-token")
        self.assertEqual(self.http.requests[-1][1]["data"]["grant_type"],"refresh_token")
        self.assertNotIn("PRIVATE-PASSWORD", json.dumps(self.http.requests[-1]))

    def test_auth_attached_only_to_firebase_project(self):
        self.auth.sign_in("public-web-key","authorized@example.com","PRIVATE-PASSWORD")
        requests_seen = []
        def fake_request(_self, method, url, **kwargs):
            requests_seen.append((method,url,kwargs))
            return Response({"ok":True})
        with patch.object(login.requests.Session,"request",new=fake_request):
            session = login.AuthenticatedFirebaseSession(
                self.auth,"https://store-inventory-a46b0-default-rtdb.firebaseio.com")
            session.get("https://store-inventory-a46b0-default-rtdb.firebaseio.com/store_inventory_v2/data.json",
                        headers={"X-Firebase-ETag":"true"})
            session.get("https://example.com/data.json")
            session.put("https://store-inventory-a46b0-default-rtdb.firebaseio.com/store_inventory_v2/_lock.json",
                        params={"print":"pretty"})
        self.assertEqual(requests_seen[0][2]["params"]["auth"],"short-lived-id-token")
        self.assertIn("X-Firebase-ETag", requests_seen[0][2]["headers"])
        self.assertNotIn("auth",requests_seen[1][2].get("params") or {})
        self.assertEqual(requests_seen[2][2]["params"]["print"],"pretty")
        self.assertIn("auth",requests_seen[2][2]["params"])

    def test_firebase_401_triggers_refresh_then_retry(self):
        self.auth.sign_in("public-web-key","authorized@example.com","PRIVATE-PASSWORD")
        requests_seen = []
        def fake_request(_self, method, url, **kwargs):
            requests_seen.append(kwargs["params"]["auth"])
            return Response(status_code=401 if len(requests_seen)==1 else 200)
        with patch.object(login.requests.Session,"request",new=fake_request):
            sess=login.AuthenticatedFirebaseSession(
                self.auth,"https://store-inventory-a46b0-default-rtdb.firebaseio.com")
            result=sess.get("https://store-inventory-a46b0-default-rtdb.firebaseio.com/store_inventory_v2/data.json")
        self.assertTrue(result.ok)
        self.assertEqual(requests_seen,["short-lived-id-token","new-id-token"])

    def test_bogus_credentials_do_not_create_session(self):
        class Reject(FakeAuthHTTP):
            def post(self, url, **kwargs):
                return Response({"error":{"message":"INVALID_LOGIN_CREDENTIALS"}},400)
        auth=login.FirebaseEmailAuth(self.tmp.name, session=Reject(), user_data_dir=self.tmp.name)
        with self.assertRaisesRegex(login.FirebaseAuthenticationError,"Invalid Firebase"):
            auth.sign_in("web-key","x@y.com","wrong")
        self.assertFalse(auth.token_file.exists())
        self.assertFalse(auth.config_file.exists())


if __name__ == "__main__":
    unittest.main()
