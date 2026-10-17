"""v1.0.95: authenticate the EXISTING Firebase data sync (no UI redesign).

Apply after ci_patch_online_v1094.py. Firebase login is a small first-run
dialog, required by current RTDB Rules auth != null. The email/password only
goes to Google Identity Toolkit over HTTPS; the local app never saves it.
"""
from pathlib import Path

root = Path(__file__).resolve().parent / "source"

def read(name):
    return (root / name).read_text(encoding="utf-8-sig")

def update(name, contents):
    compile(contents, name, "exec")
    (root / name).write_text(contents, encoding="utf-8")

def only(src, old, new, name):
    occurrences = src.count(old)
    if occurrences != 1:
        raise RuntimeError(f"{name}: expected exactly one source anchor, got {occurrences}")
    return src.replace(old, new, 1)

sync = read("firebase_sync.py")
# Non-blocking background sync must use the same authenticated HTTP session.
sync = only(sync,
    'r = requests.get(url, timeout=self.timeout)',
    'r = self.session.get(url, timeout=self.timeout)',
    'background Firebase GET authentication')
assert "store_inventory_v2/data.json" in sync
update("firebase_sync.py", sync)

app = read("store_inventory.py")
# Sign in BEFORE any SQLite/Firebase migration. Missing credentials cannot
# accidentally show/republish the legacy 2480-code cache.
app = only(app,
    '        self.conn=connect()\n',
    '''        from firebase_auth_v1095 import request_login
        if not request_login(self, INSTALL_DIR):
            self.destroy()
            raise SystemExit(0)
        self.conn=connect()
''',
    "Tk root Firebase login")
app = only(app,
    '    sync = FirebaseSync(FIREBASE_URL_FILE, INSTALL_DIR)\n',
    '''    sync = FirebaseSync(FIREBASE_URL_FILE, INSTALL_DIR)
    from firebase_auth_v1095 import get_authenticated_session
    sync.session = get_authenticated_session(sync.base_url)
''',
    'Authenticated online connection')
assert "ensure_clean_online(raw, sync," in app
update("store_inventory.py", app)
print("v1.0.95: Firebase Email/Password login + automatic secure token refresh; old dataset isolated")
