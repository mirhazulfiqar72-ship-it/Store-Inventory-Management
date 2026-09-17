from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent / "source"


def read(name):
    return (ROOT / name).read_text(encoding="utf-8-sig")


def write(name, text):
    (ROOT / name).write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Firebase: the previous CI patch used PowerShell backtick escape text inside
# Python source, producing a SyntaxError.  Normalize that corruption first,
# then make sure mto_items is included in the cloud snapshot table list.
# ---------------------------------------------------------------------------
sync = read("firebase_sync.py")
sync = sync.replace("`r`n", "\n").replace("`n", "\n").replace("`r", "\r")
if '"mto_items"' not in sync:
    pattern = r'("items",\s*\n)(\s*"parties",)'
    sync, count = re.subn(pattern, r'\1    "mto_items",\n\2', sync, count=1)
    if count != 1:
        raise RuntimeError("Could not add mto_items to firebase_sync.py safely.")
write("firebase_sync.py", sync)

# Fixed Realtime Database URL.  No API-key configuration is introduced.
write("firebase_database_url.txt", "https://store-inventory-a46b0-default-rtdb.firebaseio.com/\n")

# The updater reads this file from the installed application directory.
manifest_url = "https://raw.githubusercontent.com/mirhazulfiqar72-ship-it/Store-Inventory-Management/main/version.json"
write("update_config.json", json.dumps({"manifest_url": manifest_url}, indent=2) + "\n")

# ---------------------------------------------------------------------------
# Updater: keep the existing automatic update behavior, but make manual
# Help -> Check Update report both the current/no-update case and errors.
# ---------------------------------------------------------------------------
updater = read("updater.py")
updater = updater.replace("def check_for_update(parent):", "def check_for_update(parent, manual=False):")
updater = updater.replace(
    '        if not manifest_url:\n            return\n',
    '        if not manifest_url:\n            if manual:\n                messagebox.showwarning("Check Update", "Update checking is not configured.", parent=parent)\n            return False\n',
)
updater = updater.replace(
    '        except Exception:\n            # No internet / unavailable manifest must never disturb normal app startup.\n            return\n',
    '        except Exception as e:\n            # No internet must never disturb normal app startup; manual checks report it.\n            if manual:\n                messagebox.showwarning("Check Update", f"Could not check for updates.\\n\\n{e}", parent=parent)\n            return False\n',
)
updater = updater.replace(
    '        if not latest or not download_url or _version_tuple(latest) <= _version_tuple(APP_VERSION):\n            return\n',
    '        if not latest or not download_url or _version_tuple(latest) <= _version_tuple(APP_VERSION):\n            if manual:\n                messagebox.showinfo("Check Update", f"You are using the current version ({APP_VERSION}).", parent=parent)\n            return False\n',
)
# Successful update path returns True so callers can distinguish it from the
# normal no-update result. Existing startup behavior is unchanged.
updater = updater.replace(
    '            parent.destroy()\n        except Exception:\n',
    '            parent.destroy()\n            return True\n        except Exception:\n',
    1,
)
write("updater.py", updater)

# ---------------------------------------------------------------------------
# Main UI: add two non-admin Help items without changing the existing menus
# or page layout.  Manual Check Update uses the updater above; Current Version
# simply displays the bundled application version.
# ---------------------------------------------------------------------------
app = read("store_inventory.py")
if "import updater" not in app:
    # Put it after the standard imports; PyInstaller will then see the module
    # through the normal dependency graph as well as the explicit hidden import.
    m = re.search(r'^(import\s+[^\n]+\n)', app, flags=re.M)
    if m:
        app = app[:m.end()] + "import updater\n" + app[m.end():]
    else:
        app = "import updater\n" + app

if "def _manual_check_update(self):" not in app:
    marker = "    def build_menu_bar(self):\n"
    methods = '''    def _manual_check_update(self):\n        try:\n            updater.check_for_update(self, manual=True)\n        except Exception as e:\n            messagebox.showerror("Check Update", f"Could not check for updates.\\n\\n{e}", parent=self)\n\n    def _show_current_version(self):\n        try:\n            messagebox.showinfo("Current Version", f"Store Inventory Management\\n\\nCurrent version: {updater.APP_VERSION}", parent=self)\n        except Exception as e:\n            messagebox.showerror("Current Version", str(e), parent=self)\n\n'''
    if marker not in app:
        raise RuntimeError("Could not find build_menu_bar() in store_inventory.py.")
    app = app.replace(marker, methods + marker, 1)

# Add the requested Help submenu entries directly after Backup Now.  They are
# intentionally outside the admin-only block, so every logged-in user can use
# Check Update and Current Version.
needle = '        m_help.add_command(label="Backup Now",command=self.backup_now)\n'
replacement = needle + '        m_help.add_command(label="Check Update",command=self._manual_check_update)\n        m_help.add_command(label="Current Version",command=self._show_current_version)\n'
if 'label="Check Update"' not in app:
    if needle not in app:
        raise RuntimeError("Could not find Help menu in store_inventory.py.")
    app = app.replace(needle, replacement, 1)

write("store_inventory.py", app)

print("CI patch complete: Firebase module/config fixed; Help -> Check Update and Current Version added.")
