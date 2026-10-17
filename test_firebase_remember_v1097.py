"""v1.0.97: Firebase login is remembered across restarts/Windows updates.

All sign-in and refresh HTTP traffic is mocked; no production data is touched.
The fake DPAPI is TEST ONLY. Production always uses Windows win32crypt.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
import firebase_auth_v1095 as auth_module


class Response:
    ok = True
    status_code = 200
    def __init__(self, obj):
        self.obj = obj
    def json(self):
        return self.obj


class FakeIdentity:
    def __init__(self):
        self.logins = 0
        self.refreshes = 0
    def post(self, url, **kwargs):
        if "signInWithPassword" in url:
            self.logins += 1
            return Response({"idToken":"first-id", "refreshToken":"first-refresh",
                             "localId":"user-123", "expiresIn":"3600"})
        if "securetoken" in url:
            self.refreshes += 1
            return Response({"id_token":"renewed-id", "refresh_token":"renewed-refresh",
                             "user_id":"user-123", "expires_in":"3600"})
        raise AssertionError("Unapproved URL " + url)


class FakeWindowsDPAPI:
    def CryptProtectData(self, data, *args):
        return b"fake-dpapi-encrypted:" + bytes(data)[::-1]
    def CryptUnprotectData(self, data, *args):
        prefix = b"fake-dpapi-encrypted:"
        if not data.startswith(prefix):
            raise ValueError("Not a protected session")
        return "Fake DPAPI", data[len(prefix):][::-1]


class RememberLoginTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.install = self.base / "Install"
        self.user = self.base / "User-AppData"
        self.api = FakeIdentity()
        fake_crypto = patch.object(auth_module, "_secure_windows_token_storage",
                                   return_value=FakeWindowsDPAPI())
        fake_crypto.start()
        self.addCleanup(fake_crypto.stop)

    def manager(self, user_dir=None):
        return auth_module.FirebaseEmailAuth(
            self.install, session=self.api, user_data_dir=user_dir or self.user)

    def test_first_login_then_second_launch_uses_refresh_not_password(self):
        first = self.manager()
        first.sign_in("public-api-key", "user@example.com", "PRIVATE-DO-NOT-STORE")
        self.assertEqual(self.api.logins, 1)
        self.assertTrue(first.session_remembered)
        self.assertTrue(first.config_file.is_file())
        self.assertTrue(first.token_file.is_file())
        data = first.config_file.read_bytes() + first.token_file.read_bytes()
        self.assertNotIn(b"PRIVATE-DO-NOT-STORE", data)
        self.assertNotIn(b"first-refresh", data)
        self.assertFalse((self.install / "Data" / "firebase_auth_refresh_v1095.dpapi").exists())

        # Restart/new installer instance: silent login uses only DPAPI token.
        restarted = self.manager()
        self.assertEqual(restarted.api_key, "public-api-key")
        self.assertEqual(restarted.email, "user@example.com")
        self.assertTrue(restarted.restore_saved_session())
        self.assertEqual(self.api.logins, 1)
        self.assertEqual(self.api.refreshes, 1)
        self.assertEqual(restarted.id_token(), "renewed-id")
        self.assertTrue(restarted.session_remembered)

    def test_third_launch_uses_rotated_refresh_token(self):
        first = self.manager()
        first.sign_in("public-api-key", "user@example.com", "pass")
        self.assertTrue(self.manager().restore_saved_session())
        self.assertTrue(self.manager().restore_saved_session())
        self.assertEqual((self.api.logins, self.api.refreshes), (1,2))

    def test_existing_v1096_dpapi_session_migrates_without_password(self):
        legacy_dir = self.install / "Data"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "firebase_client_auth_v1095.json").write_text(
            json.dumps({"web_api_key":"old-public-key",
                        "email":"user@example.com"}),encoding="utf-8")
        previous = {"refresh_token":"existing-refresh", "email":"user@example.com",
                    "uid":"user-123"}
        (legacy_dir / "firebase_auth_refresh_v1095.dpapi").write_bytes(
            FakeWindowsDPAPI().CryptProtectData(json.dumps(previous).encode()))
        updated = self.manager()
        self.assertTrue(updated.restore_saved_session())
        self.assertEqual(updated.api_key, "old-public-key")
        self.assertEqual(self.api.logins, 0)
        self.assertEqual(self.api.refreshes, 1)
        self.assertTrue(updated.config_file.is_file())
        self.assertTrue(updated.token_file.is_file())
        self.assertTrue(self.manager().restore_saved_session())

    def test_different_windows_user_cannot_reuse_other_session(self):
        first = self.manager()
        first.sign_in("public-api-key", "user@example.com", "pass")
        second_user = self.manager(self.base / "Different-Windows-Profile")
        self.assertFalse(second_user.restore_saved_session())
        self.assertEqual(second_user.email, "")

    def test_missing_windows_dpapi_never_writes_plaintext_token(self):
        with patch.object(auth_module, "_secure_windows_token_storage", return_value=None):
            first = self.manager()
            first.sign_in("public-api-key","user@example.com","pass")
            self.assertFalse(first.session_remembered)
            self.assertFalse(first.token_file.exists())
            other = self.manager()
            self.assertFalse(other.restore_saved_session())
            self.assertEqual(other.api_key,"public-api-key")

    def test_no_stored_password_or_token_in_public_json(self):
        first = self.manager()
        first.sign_in("public-api-key","user@example.com","password-secret")
        stored = json.loads(first.config_file.read_text(encoding="utf-8"))
        self.assertEqual(set(stored), {"web_api_key","email"})
        self.assertNotIn("password", first.config_file.read_text())
        self.assertNotIn("refresh", first.config_file.read_text())


if __name__ == "__main__":
    unittest.main()
