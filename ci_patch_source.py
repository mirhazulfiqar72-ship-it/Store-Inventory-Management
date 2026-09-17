from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent / "source"

def read(name):
    return (ROOT / name).read_text(encoding="utf-8-sig")

def write(name, text):
    (ROOT / name).write_text(text, encoding="utf-8")

# Firebase source is supplied by the repository root firebase_sync.py so the
# release build always uses the durable/restart-safe sync implementation.
sync = read("firebase_sync.py")
sync = sync.replace("`r`n", "\n").replace("`n", "\n").replace("`r", "\r")
write("firebase_sync.py", sync)

write("firebase_database_url.txt", "https://store-inventory-a46b0-default-rtdb.firebaseio.com/\n")
manifest_url = "https://raw.githubusercontent.com/mirhazulfiqar72-ship-it/Store-Inventory-Management/main/version.json"
write("update_config.json", json.dumps({"manifest_url": manifest_url}, indent=2) + "\n")

# Updater repair: do NOT internally download/install and do NOT verify a
# downloaded file. The requested update flow is to launch IDM or the browser.
updater = read("updater.py")
updater = re.sub(r'^import storage_lock\s*\n', '', updater, count=1, flags=re.M)
updater = "import storage_lock\n" + updater
for line in ["import os\n", "import subprocess\n", "import webbrowser\n", "from pathlib import Path\n"]:
    if line.strip() not in updater:
        updater = line + updater

new_function = r'''def _start_update_download(download_url):
    """Start update download with IDM when installed, otherwise browser."""
    if not download_url:
        return False
    candidates = [
        os.path.expandvars(r"%PROGRAMFILES%\Internet Download Manager\IDMan.exe"),
        os.path.expandvars(r"%PROGRAMFILES(x86)%\Internet Download Manager\IDMan.exe"),
    ]
    for idm in candidates:
        if idm and os.path.isfile(idm):
            try:
                subprocess.Popen([idm, "/d", download_url, "/n"], close_fds=True)
                return True
            except Exception:
                pass
    try:
        return bool(webbrowser.open(download_url, new=2))
    except Exception:
        try:
            os.startfile(download_url)
            return True
        except Exception:
            return False


def check_for_update(parent, manual=False):
    try:
        config_path = Path(__file__).resolve().parent / "update_config.json"
        cfg = json.loads(config_path.read_text(encoding="utf-8-sig")) if config_path.exists() else {}
        manifest_url = str(cfg.get("manifest_url", "")).strip()
        if not manifest_url:
            if manual:
                messagebox.showwarning("Check Update", "Update checking is not configured.", parent=parent)
            return False
        response = requests.get(manifest_url, timeout=12)
        response.raise_for_status()
        data = response.json()
        latest = str(data.get("version", "")).strip()
        download_url = str(data.get("url", "")).strip()
        if not latest or not download_url or _version_tuple(latest) <= _version_tuple(APP_VERSION):
            if manual:
                messagebox.showinfo("Check Update", f"You are using the current version ({APP_VERSION}).", parent=parent)
            return False
        if not messagebox.askyesno("Update Available", f"A new version ({latest}) is available.\n\nDo you want to download it now?", parent=parent):
            return False
        if _start_update_download(download_url):
            messagebox.showinfo("Download Started", "The update Setup download has been started in Internet Download Manager or your default browser.", parent=parent)
            return True
        messagebox.showerror("Update Download", "Could not start the update download.", parent=parent)
        return False
    except Exception as e:
        if manual:
            messagebox.showwarning("Check Update", f"Could not check for updates.\n\n{e}", parent=parent)
        return False

'''
pattern = r'(?ms)^def check_for_update\(.*?(?=^def |\Z)'
m = re.search(pattern, updater)
if m:
    updater = updater[:m.start()] + new_function + updater[m.end():]
else:
    pattern2 = r'(?ms)^def check_for_updates\(.*?(?=^def |\Z)'
    m2 = re.search(pattern2, updater)
    if m2:
        updater = updater[:m2.start()] + new_function + updater[m2.end():]
    else:
        updater += "\n" + new_function
write("updater.py", updater)

# Main UI: preserve the existing interface and add only the requested Help items.
app = read("store_inventory.py")
if "import updater" not in app:
    m = re.search(r'^(import\s+[^\n]+\n)', app, flags=re.M)
    if m:
        app = app[:m.end()] + "import updater\n" + app[m.end():]
    else:
        app = "import updater\n" + app

# IMPORTANT: old builds rotated automatic backups and deleted older files.
# The requested behavior is never to auto-delete stored data/backups.
app, backup_patch_count = re.subn(
    r'(?ms)^        # Rotate: keep all manual backups, but only the newest 30 automatic ones\.\n.*?^        return zpath',
    '        # Automatic backup rotation/deletion is intentionally disabled.\n        # Stored backups remain until the user explicitly deletes/restores them.\n        return zpath',
    app,
    count=1,
)
if backup_patch_count != 1:
    raise RuntimeError("Could not disable automatic backup deletion safely.")

if "def _manual_check_update(self):" not in app:
    marker = "    def build_menu_bar(self):\n"
    methods = '''    def _manual_check_update(self):\n        try:\n            updater.check_for_update(self, manual=True)\n        except Exception as e:\n            messagebox.showerror("Check Update", f"Could not check for updates.\\n\\n{e}", parent=self)\n\n    def _show_current_version(self):\n        try:\n            messagebox.showinfo("Current Version", f"Store Inventory Management\\n\\nCurrent version: {updater.APP_VERSION}", parent=self)\n        except Exception as e:\n            messagebox.showerror("Current Version", str(e), parent=self)\n\n'''
    if marker not in app:
        raise RuntimeError("Could not find build_menu_bar() in store_inventory.py.")
    app = app.replace(marker, methods + marker, 1)

needle = '        m_help.add_command(label="Backup Now",command=self.backup_now)\n'
replacement = needle + '        m_help.add_command(label="Check Update",command=self._manual_check_update)\n        m_help.add_command(label="Current Version",command=self._show_current_version)\n'
if 'label="Check Update"' not in app:
    if needle not in app:
        raise RuntimeError("Could not find Help menu in store_inventory.py.")
    app = app.replace(needle, replacement, 1)

write("store_inventory.py", app)
print("CI patch complete: durable Firebase sync, persistent local data, no automatic backup deletion, and IDM/browser update downloads.")
