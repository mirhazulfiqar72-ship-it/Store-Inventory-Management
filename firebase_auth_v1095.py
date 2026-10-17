"""Firebase Email/Password authentication for Store Inventory Management v1.0.95.

Firebase Realtime Database Rules require auth != null. Sign in through Firebase
Identity Toolkit and attach a short-lived ID token to REST calls. Never persist
the user's password. Persist refresh tokens ONLY encrypted with Windows DPAPI;
if DPAPI is unavailable, request credentials on the next launch instead.

The Web API Key is a public client identifier, NOT an admin/service-account key.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit

import requests

_CONFIG_NAME = "firebase_client_auth_v1095.json"
_TOKEN_NAME = "firebase_auth_refresh_v1095.dpapi"
_MANAGER = None


class FirebaseAuthenticationError(RuntimeError):
    pass


def _secure_windows_token_storage():
    try:
        import win32crypt
        return win32crypt
    except ImportError:
        return None


class FirebaseEmailAuth:
    def __init__(self, install_dir, session=None, clock=None, user_data_dir=None):
        # User-scoped data survives software updates and is not part of the
        # installer's managed files. DPAPI also binds credentials to this
        # Windows account, so another local user cannot reuse the session.
        self.legacy_data_dir = Path(install_dir) / "Data"
        if user_data_dir is not None:
            self.data_dir = Path(user_data_dir)
        else:
            local_appdata = os.environ.get("LOCALAPPDATA")
            if not local_appdata:
                local_appdata = str(Path.home() / "AppData" / "Local")
            self.data_dir = Path(local_appdata) / "StoreInventoryManagement" / "Auth"
        self.config_file = self.data_dir / _CONFIG_NAME
        # Token is scoped to the current Windows account (DPAPI).
        self.token_file = self.data_dir / _TOKEN_NAME
        self.http = session or requests.Session()
        self.clock = clock or time.time
        self.lock = threading.RLock()
        self.api_key = ""
        self.email = ""
        self.uid = ""
        self._id_token = ""
        self._refresh_token = ""
        self._expiry = 0.0
        self.session_remembered = False
        self._load_config()

    def _load_config(self):
        # Read the new per-user settings first. If upgrading from v1.0.96,
        # migrate the previous settings without asking for the API key/email.
        for path in (self.config_file, self.legacy_data_dir / _CONFIG_NAME):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                key = str(data.get("web_api_key") or "").strip()
                email = str(data.get("email") or "").strip()
                if not key or not email:
                    continue
                self.api_key, self.email = key, email
                if path != self.config_file:
                    try:
                        self._save_config()
                    except OSError:
                        pass
                return
            except (OSError, ValueError, TypeError):
                continue

    def _save_config(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        safe = {"web_api_key": self.api_key, "email": self.email}
        temp = self.config_file.with_suffix(".tmp")
        temp.write_text(json.dumps(safe, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, self.config_file)

    def _save_protected_refresh_token(self):
        """Persist only an encrypted refresh token, not a password or ID token."""
        crypto = _secure_windows_token_storage()
        self.session_remembered = False
        if not crypto or not self._refresh_token:
            return False
        try:
            raw = json.dumps({"refresh_token": self._refresh_token,
                              "email": self.email, "uid": self.uid}).encode("utf-8")
            encrypted = crypto.CryptProtectData(raw, "Store Inventory Firebase session",
                                                None, None, None, 0)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            temp = self.token_file.with_suffix(".tmp")
            try:
                temp.write_bytes(encrypted)
                os.replace(temp, self.token_file)
            finally:
                if temp.is_file():
                    temp.unlink()
            self.session_remembered = True
            return True
        except (OSError, ValueError, TypeError):
            # Never downgrade to a plaintext token or saved password.
            return False
        except Exception:
            # A pywin32/DPAPI error means the user needs to sign in again,
            # not that insecure credential storage should be used.
            return False

    def _load_protected_refresh_token(self):
        crypto = _secure_windows_token_storage()
        if not crypto:
            return False
        for path in (self.token_file, self.legacy_data_dir / _TOKEN_NAME):
            if not path.is_file():
                continue
            try:
                _, raw = crypto.CryptUnprotectData(path.read_bytes(),
                                                   None, None, None, 0)
                saved = json.loads(raw.decode("utf-8"))
                if str(saved.get("email") or "").casefold() != self.email.casefold():
                    continue
                refresh = str(saved.get("refresh_token") or "")
                if not refresh:
                    continue
                self._refresh_token = refresh
                self.uid = str(saved.get("uid") or "")
                self.session_remembered = True
                if path != self.token_file:
                    # An already authenticated v1.0.96 Windows account is
                    # migrated to per-user AppData without another password.
                    self._save_protected_refresh_token()
                return True
            except Exception:
                continue
        return False

    @staticmethod
    def _body(response):
        try:
            value = response.json()
            return value if isinstance(value, dict) else {}
        except ValueError:
            return {}

    def _auth_error(self, response):
        msg = self._body(response).get("error") or {}
        reason = str(msg.get("message") if isinstance(msg, dict) else msg)
        supported = {"INVALID_PASSWORD": "Invalid Firebase email or password",
                     "INVALID_LOGIN_CREDENTIALS": "Invalid Firebase email or password",
                     "EMAIL_NOT_FOUND": "Firebase account not found",
                     "USER_DISABLED": "Firebase account is disabled",
                     "API_KEY_INVALID": "Web API Key is incorrect",
                     "INVALID_API_KEY": "Web API Key is incorrect",
                     "OPERATION_NOT_ALLOWED": "Email/Password sign-in is disabled"}
        label = supported.get(reason, "Firebase sign-in failed (HTTP " +
                              str(response.status_code) + ")")
        raise FirebaseAuthenticationError(label)

    def _remember_tokens(self, payload):
        token = str(payload.get("idToken") or payload.get("id_token") or "")
        refresh = str(payload.get("refreshToken") or payload.get("refresh_token") or "")
        if not token or not refresh:
            raise FirebaseAuthenticationError("Firebase returned an incomplete login session")
        self._id_token = token
        self._refresh_token = refresh
        self.uid = str(payload.get("localId") or payload.get("user_id") or self.uid)
        expiry = payload.get("expiresIn", payload.get("expires_in", 3600))
        self._expiry = self.clock() + max(60, int(expiry))
        self._save_protected_refresh_token()

    def sign_in(self, web_api_key, email, password):
        key, email = str(web_api_key or "").strip(), str(email or "").strip()
        if not key or not email or not password:
            raise FirebaseAuthenticationError("Web API Key, email and password are required")
        url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        try:
            response = self.http.post(
                url, params={"key": key},
                json={"email": email, "password": password, "returnSecureToken": True},
                timeout=20)
        except requests.RequestException as exc:
            raise FirebaseAuthenticationError("Could not reach Firebase Authentication") from exc
        if not response.ok:
            self._auth_error(response)
        with self.lock:
            self.api_key, self.email = key, email
            self._remember_tokens(self._body(response))
            self._save_config()

    def refresh(self):
        with self.lock:
            if not self.api_key or not self._refresh_token:
                raise FirebaseAuthenticationError("Sign in to Firebase again")
            try:
                response = self.http.post(
                    "https://securetoken.googleapis.com/v1/token",
                    params={"key": self.api_key},
                    data={"grant_type": "refresh_token",
                          "refresh_token": self._refresh_token},
                    timeout=20)
            except requests.RequestException as exc:
                raise FirebaseAuthenticationError("Could not refresh the Firebase session") from exc
            if not response.ok:
                self._auth_error(response)
            self._remember_tokens(self._body(response))

    def restore_saved_session(self):
        if not self.api_key or not self.email:
            return False
        if not self._load_protected_refresh_token():
            return False
        try:
            self.refresh()
            return True
        except FirebaseAuthenticationError:
            return False

    def id_token(self):
        with self.lock:
            if not self._id_token or self.clock() > self._expiry - 60:
                self.refresh()
            return self._id_token

    def expire(self):
        with self.lock:
            self._expiry = 0


class AuthenticatedFirebaseSession(requests.Session):
    """Adds auth token only to URLs under the configured Firebase RTDB URL."""
    def __init__(self, auth: FirebaseEmailAuth, database_url: str):
        super().__init__()
        # requests.Session.auth is a reserved Requests HTTPAuth hook.
        # Storing a FirebaseEmailAuth instance in that attribute makes Requests
        # attempt to CALL it while preparing every request, crashing the EXE.
        self.firebase_auth = auth
        parsed = urlsplit(str(database_url or "").rstrip("/"))
        if parsed.scheme != "https" or not parsed.hostname:
            raise FirebaseAuthenticationError("Firebase Realtime Database URL must be HTTPS")
        self.database_url = database_url.rstrip("/")

    def request(self, method, url, **kwargs):
        if isinstance(url, str) and url.startswith(self.database_url + "/"):
            params = kwargs.get("params")
            if isinstance(params, dict):
                params = dict(params)
            elif params is None:
                params = {}
            else:
                params = dict(params)
            params["auth"] = self.firebase_auth.id_token()
            kwargs["params"] = params
            response = super().request(method, url, **kwargs)
            if response.status_code == 401:
                self.firebase_auth.expire()
                params["auth"] = self.firebase_auth.id_token()
                response = super().request(method, url, **kwargs)
            return response
        return super().request(method, url, **kwargs)


def get_authenticated_session(database_url):
    if _MANAGER is None or not _MANAGER.api_key:
        raise FirebaseAuthenticationError("Firebase sign-in is required before online sync")
    return AuthenticatedFirebaseSession(_MANAGER, database_url)


def request_login(parent, install_dir):
    """Existing Tk root shows a one-time auth dialog; never reveals password."""
    global _MANAGER
    if _MANAGER and _MANAGER._id_token:
        return True

    auth = FirebaseEmailAuth(install_dir)
    if auth.restore_saved_session():
        _MANAGER = auth
        return True

    # Existing clean v2 installations remain usable offline. The cached
    # DPAPI-protected refresh token proves this Windows user previously
    # signed in; online requests retry refresh when connectivity returns.
    v2_state = auth.data_dir / "firebase_sync_state_v2.json"
    if v2_state.is_file() and auth._load_protected_refresh_token():
        _MANAGER = auth
        return True

    import tkinter as tk
    from tkinter import ttk, messagebox

    window = tk.Toplevel(parent)
    window.title("Firebase Online Sign-in")
    window.geometry("460x284")
    window.resizable(False, False)
    window.transient(parent)
    window.grab_set()

    frame = ttk.Frame(window, padding=16)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Connect to Store Inventory Online",
              font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2,
                                                  sticky="w", pady=(0, 8))
    ttk.Label(frame, text="Web API Key:").grid(row=1, column=0, sticky="w", pady=4)
    key_value = tk.StringVar(value=auth.api_key)
    key_entry = ttk.Entry(frame, textvariable=key_value, width=42)
    key_entry.grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Firebase email:").grid(row=2, column=0, sticky="w", pady=4)
    email_value = tk.StringVar(value=auth.email)
    email_entry = ttk.Entry(frame, textvariable=email_value, width=42)
    email_entry.grid(row=2, column=1, sticky="ew", pady=4)
    ttk.Label(frame, text="Password:").grid(row=3, column=0, sticky="w", pady=4)
    password_value = tk.StringVar()
    password_entry = ttk.Entry(frame, textvariable=password_value, show="*", width=42)
    password_entry.grid(row=3, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Find Web API Key: Firebase Console → Project settings → General",
              wraplength=405).grid(row=4, column=0, columnspan=2, sticky="w",
                                   pady=(7, 2))
    status = tk.StringVar(value="Your password will never be saved.")
    ttk.Label(frame, textvariable=status, foreground="#a62a2a",
              wraplength=410).grid(row=5, column=0, columnspan=2,
                                   sticky="w", pady=(4, 7))
    result = {"ok": False}
    buttons = ttk.Frame(frame)
    buttons.grid(row=6, column=0, columnspan=2, sticky="e")

    def sign_in():
        try:
            button.config(state="disabled")
            status.set("Signing in securely…")
            window.update_idletasks()
            auth.sign_in(key_value.get(), email_value.get(), password_value.get())
        except Exception as exc:
            # Never display password or Firebase tokens.
            status.set(str(exc) if isinstance(exc, FirebaseAuthenticationError)
                       else "Firebase sign-in unavailable. Check Internet and credentials.")
            button.config(state="normal")
            return
        finally:
            password_value.set("")
        if not auth.session_remembered:
            messagebox.showwarning(
                "Firebase login",
                "You are signed in, but Windows could not securely save this session. "
                "You may need to sign in next time. Check AppData access or Windows DPAPI.",
                parent=window)
        result["ok"] = True
        window.destroy()

    def cancel():
        password_value.set("")
        window.destroy()

    button = ttk.Button(buttons, text="Sign In", command=sign_in)
    button.pack(side="right", padx=(8, 0))
    ttk.Button(buttons, text="Cancel", command=cancel).pack(side="right")
    frame.columnconfigure(1, weight=1)
    window.bind("<Return>", lambda event: sign_in())
    window.bind("<Escape>", lambda event: cancel())
    window.protocol("WM_DELETE_WINDOW", cancel)
    if not key_value.get():
        key_entry.focus_set()
    elif not email_value.get():
        email_entry.focus_set()
    else:
        password_entry.focus_set()
    parent.wait_window(window)
    if result["ok"]:
        _MANAGER = auth
        return True
    return False
