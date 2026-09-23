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

# A local JSON snapshot is an independent crash/restart safety net. SQLite is
# still the live local database; the snapshot is only used when the DB becomes
# missing/empty unexpectedly.
if "import durable_local" not in sync:
    sync = sync.replace("import sqlite3\n", "import sqlite3\nimport durable_local\n", 1)

# Inventory-only records (items/users) must count as real local records. The
# previous implementation ignored them, so an empty/older Firebase snapshot
# could replace newly saved Inventory Codes on the next restart.
old_has_records = 'return any(tables.get(x, {}).get("rows") for x in ("demands", "demand_lines", "grr", "grr_lines", "issues", "issue_lines", "transactions", "parties", "mto_items"))'
new_has_records = 'return any(tables.get(x, {}).get("rows") for x in TABLES)'
if old_has_records in sync:
    sync = sync.replace(old_has_records, new_has_records, 1)

# Every local commit is snapshotted before the network operation and again
# after a successful merge. A failed Firebase write can therefore never turn a
# successful local save into a lost record after restart.
commit_re = re.compile(r'(?ms)^    def commit\(self\):\n.*?(?=^    def rollback\(self\):)')
commit_match = commit_re.search(sync)
if commit_match:
    new_commit = '''    def commit(self):
        self._conn.commit()
        # Keep the recovery module available inside the generated sync module.
        import durable_local
        # Make local persistence independent of Firebase availability.
        durable_local.save(self._conn)
        if self._dirty:
            self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
            # push_changes may merge remote rows back into SQLite.
            durable_local.save(self._conn)
        self._dirty = False
        self._baseline = None if self.sync.pending_base is None else self.sync.pending_base

'''
    sync = sync[:commit_match.start()] + new_commit + sync[commit_match.end():]
else:
    raise RuntimeError("Could not locate OnlineConnection.commit() in firebase_sync.py")
write("firebase_sync.py", sync)

# Ensure the new local snapshot module is available to the packaged source.
# The workflow copies durable_local.py before this patch is executed.

write("firebase_database_url.txt", "https://store-inventory-a46b0-default-rtdb.firebaseio.com/\n")
manifest_url = "https://raw.githubusercontent.com/mirhazulfiqar72-ship-it/Store-Inventory-Management/main/version.json"
write("update_config.json", json.dumps({"manifest_url": manifest_url}, indent=2) + "\n")

# Updater repair: generate one clean updater module. Automatic startup checks are silent
# unless GitHub's manifest reports a genuinely newer release.
updater = r'''import json
import os
import subprocess
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import requests

APP_VERSION = "0.0.0"
CONFIG_NAME = "update_config.json"
_CHECK_IN_PROGRESS = False
_AUTO_CHECK_DONE = False

def _version_tuple(value):
    parts = []
    for part in str(value or "").strip().lstrip("vV").split("."):
        n = ""
        for ch in part:
            if ch.isdigit():
                n += ch
            else:
                break
        parts.append(int(n or 0))
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])

def _config():
    path = Path(__file__).resolve().parent / CONFIG_NAME
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}

def _start_update_download(download_url):
    if not download_url:
        return False
    idm_paths = (
        os.path.expandvars(r"%PROGRAMFILES%\\Internet Download Manager\\IDMan.exe"),
        os.path.expandvars(r"%PROGRAMFILES(x86)%\\Internet Download Manager\\IDMan.exe"),
    )
    for path in idm_paths:
        if os.path.isfile(path):
            try:
                subprocess.Popen([path, "/d", download_url, "/n"], close_fds=True)
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
    global _CHECK_IN_PROGRESS, _AUTO_CHECK_DONE
    if _CHECK_IN_PROGRESS:
        return False
    if not manual and _AUTO_CHECK_DONE:
        return False
    if not manual:
        _AUTO_CHECK_DONE = True
    _CHECK_IN_PROGRESS = True
    try:
        cfg = _config()
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
        if not latest or not download_url:
            if manual:
                messagebox.showwarning("Check Update", "Update information is unavailable.", parent=parent)
            return False
        if _version_tuple(latest) <= _version_tuple(APP_VERSION):
            if manual:
                messagebox.showinfo("Check Update", f"You are using the current version ({APP_VERSION}).", parent=parent)
            return False
        answer = messagebox.askyesno(
            "Update Available",
            f"A new version ({latest}) is available.\\n\\nDo you want to download it now?",
            parent=parent,
        )
        if not answer:
            return False
        if _start_update_download(download_url):
            return True
        if manual:
            messagebox.showerror("Update Download", "Could not start the update download.", parent=parent)
        return False
    except Exception as exc:
        # Startup/background checking is completely silent on network/config errors.
        if manual:
            messagebox.showwarning("Check Update", f"Could not check for updates.\\n\\n{exc}", parent=parent)
        return False
    finally:
        _CHECK_IN_PROGRESS = False
'''
write("updater.py", updater)

# Main UI: preserve the existing interface and add only the requested Help items.
app = read("store_inventory.py")
# Check for updates once after the Dashboard is shown at login.
_home_block = """        self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
        self.main_body=self.body
        self.dashboard()
"""
_home_replacement = """        self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
        self.main_body=self.body
        self.dashboard()
        if not getattr(self, "_update_checked_this_session", False):
            self._update_checked_this_session = True
            # Startup check is silent: show a popup only when a newer version exists.
            self.after(900, lambda: updater.check_for_update(self, manual=False))
"""
if _home_block not in app:
    raise RuntimeError("Could not locate Home dashboard block for update check.")
app = app.replace(_home_block, _home_replacement, 1)
if "import updater" not in app:
    m = re.search(r'^(import\s+[^\n]+\n)', app, flags=re.M)
    if m:
        app = app[:m.end()] + "import updater\n" + app[m.end():]
    else:
        app = "import updater\n" + app
if "import durable_local" not in app:
    m = re.search(r'^(import updater\n)', app, flags=re.M)
    if m:
        app = app[:m.end()] + "import durable_local\n" + app[m.end():]
    else:
        app = "import durable_local\n" + app

# Restore a larger local snapshot before Firebase startup sync when SQLite is
# unexpectedly empty/smaller. This is deliberately non-destructive: it never
# restores over a database that already contains at least as many records.
marker = '    migrate_old_item_codes(raw)\n'
restore_code = '''    migrate_old_item_codes(raw)
    try:
        durable_local.restore_if_newer(raw)
    except Exception:
        pass
'''
if "durable_local.restore_if_newer(raw)" not in app:
    if marker not in app:
        raise RuntimeError("Could not find connect() migration point in store_inventory.py.")
    app = app.replace(marker, restore_code, 1)

# Save a current local snapshot after startup synchronization has completed.
marker2 = '    return OnlineConnection(DB, sync)\n'
replace2 = '''    try:
        durable_local.save(raw)
    except Exception:
        pass
    return OnlineConnection(DB, sync)
'''
if "durable_local.save(raw)" not in app:
    if marker2 not in app:
        raise RuntimeError("Could not find connect() return point in store_inventory.py.")
    app = app.replace(marker2, replace2, 1)

# IMPORTANT: old builds rotated automatic backups and deleted older files.
# The requested behavior is never to auto-delete stored data/backups.
app, backup_patch_count = re.subn(
    r'(?ms)^        # Rotate: keep all manual backups, but only the newest 30 automatic ones\.\n.*?^        return zpath',
    '        # Automatic backup rotation/deletion is intentionally disabled.\n        # Stored backups remain until the user explicitly deletes/restores them.\n        return zpath',
    app,
    count=1,
)
# Some clean source revisions already have backup rotation disabled.
# Do not fail an otherwise valid build when that legacy block is absent.
if backup_patch_count not in (0, 1):
    raise RuntimeError("Unexpected backup patch match count.")

# Repair manual backup creation for the permanent C: database.
# The old routine checked/copied the pre-patch database location, which could
# report "database exists" even though the live DB is under C:\\StoreInventoryManagement\\Data.
backup_re = re.compile(r'(?ms)^def backup_database\(manual=False\):\n.*?(?=^def restore_database\()', re.M)
backup_match = backup_re.search(app)
if not backup_match:
    raise RuntimeError("Could not locate backup_database() in store_inventory.py.")
backup_function = '''def backup_database(manual=False):
    """Create a consistent full SQLite backup in C:\StoreInventoryManagement\Backups."""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # The live database is permanently under C:\StoreInventoryManagement\Data.
        # Also accept the legacy DB variable/path and any SQLite file already
        # present in the install tree so Backup Now never depends on the old
        # pre-online database location.
        known = []
        try:
            legacy_db = globals().get("DB")
            if legacy_db:
                known.append(os.path.abspath(os.fspath(legacy_db)))
        except Exception:
            pass
        known.extend([
            os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db"),
            os.path.join(r"C:\StoreInventoryManagement", "Data", "inventory.db"),
            os.path.join(r"C:\StoreInventoryManagement", "store_inventory.db"),
        ])
        db_candidates = []
        for p in known:
            if p and p not in db_candidates:
                db_candidates.append(p)
        # Discover the actual SQLite file if its legacy filename differs.
        for root in (
            os.path.join(r"C:\StoreInventoryManagement", "Data"),
            r"C:\StoreInventoryManagement",
        ):
            try:
                if os.path.isdir(root):
                    for name in os.listdir(root):
                        if os.path.splitext(name)[1].lower() in (".db", ".sqlite", ".sqlite3", ".db3"):
                            p = os.path.join(root, name)
                            if p not in db_candidates:
                                db_candidates.append(p)
            except Exception:
                pass

        db_path = next((p for p in db_candidates if os.path.isfile(p)), None)
        if not db_path:
            # Create the expected database path if the database has not yet
            # been materialized by the storage layer.
            db_path = os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db")
            try:
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                probe = sqlite3.connect(db_path, timeout=30)
                probe.close()
            except Exception:
                return None
            if not os.path.isfile(db_path):
                return None

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        tag = "manual" if manual else "auto"
        latest = os.path.join(BACKUP_DIR, "inventory_backup_latest.db")
        dated = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.db")
        zpath = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.zip")

        src = sqlite3.connect(db_path, timeout=30)
        try:
            try:
                src.execute("PRAGMA wal_checkpoint(FULL)")
            except Exception:
                pass
            dst = sqlite3.connect(dated, timeout=30)
            try:
                with dst:
                    src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()

        # Keep the latest convenience copy, replacing only that fixed filename.
        # Historical/manual backup archives are never automatically deleted.
        if os.path.exists(latest):
            try:
                os.remove(latest)
            except OSError:
                pass
        latest_src = sqlite3.connect(dated, timeout=30)
        try:
            latest_dst = sqlite3.connect(latest, timeout=30)
            try:
                with latest_dst:
                    latest_src.backup(latest_dst)
            finally:
                latest_dst.close()
        finally:
            latest_src.close()

        if not os.path.isfile(dated) or os.path.getsize(dated) <= 0:
            return None
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(dated, "store_inventory.db")
        if not os.path.isfile(zpath) or os.path.getsize(zpath) <= 0:
            return None
        # Also store a cloud copy of the same complete database snapshot.
        # This uses the Firebase Realtime Database URL only; no API key is needed.
        # A cloud-backup failure never invalidates an already-created local backup.
        try:
            import requests
            url_file = Path(__file__).resolve().parent / "firebase_database_url.txt"
            base_url = ""
            if url_file.exists():
                for line in url_file.read_text(encoding="utf-8-sig").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        base_url = line.rstrip("/")
                        break
            if base_url:
                cloud_stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                cloud_url = f"{base_url}/store_inventory/backups/{cloud_stamp}.json"
                with open(dated, "rb") as bf:
                    import base64
                    encoded = base64.b64encode(bf.read()).decode("ascii")
                response = requests.put(
                    cloud_url,
                    json={
                        "created_at": cloud_stamp,
                        "type": "sqlite_backup",
                        "filename": os.path.basename(zpath),
                        "database_base64": encoded,
                    },
                    timeout=30,
                )
                response.raise_for_status()
        except Exception:
            pass
        return zpath
    except Exception:
        return None
'''

# Replace the legacy backup implementation with the C: Data-aware version.
app = app[:backup_match.start()] + backup_function + app[backup_match.end():]

# Make Preview -> Export PDF fail loudly and leave the verified file in the
# permanent Reports folder. Print buttons remain print-only.
export_re = re.compile(r'(?ms)^    def export_preview_pdf\(self, title, header_lines, columns, rows\):\n.*?(?=^    def export_preview_word\(self, title, header_lines, columns, rows\):)')
export_match = export_re.search(app)
if export_match:
    export_function = '''    def export_preview_pdf(self, title, header_lines, columns, rows):
        """Write the visible preview to C:\\StoreInventoryManagement\\Reports."""
        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)
            safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
            path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
            generated = False
            if REPORTLAB:
                try:
                    self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
                    generated = True
                except Exception:
                    generated = False
            if not generated:
                self._fallback_pdf_export(path, title, header_lines, columns, rows)
            if not os.path.isfile(path) or os.path.getsize(path) <= 0:
                raise IOError("The PDF file was not created in the Reports folder.")
            with open(path, "rb") as pf:
                signature = pf.read(5)
            if signature != b"%PDF-":
                raise IOError("The generated file is not a valid PDF.")
            self._last_report_path = path
            try:
                webbrowser.open("file://" + path)
            except Exception:
                self.open_file(path)
            return path
        except Exception as e:
            messagebox.showerror("PDF Export", f"Could not generate the PDF.\\n\\n{e}")
            return None

'''
    app = app[:export_match.start()] + export_function + app[export_match.end():]
else:
    raise RuntimeError("Could not locate export_preview_pdf() in store_inventory.py")

# Every saved business entry also gets a durable PDF copy in Reports. This is
# deliberately best-effort: a report failure must never roll back an already
# committed database transaction.
if "def _save_entry_report(self, title, header_lines, columns, rows):" not in app:
    marker_report = "    def export_preview_pdf(self, title, header_lines, columns, rows):\n"
    report_method = '''    def _save_entry_report(self, title, header_lines, columns, rows):
        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)
            safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
            page_size = landscape(A4) if len(columns) > 8 else A4
            if REPORTLAB:
                self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
            else:
                self._fallback_pdf_export(path, title, header_lines, columns, rows)
            if not os.path.isfile(path) or os.path.getsize(path) <= 0:
                raise IOError("PDF was not created in C:\\\\StoreInventoryManagement\\\\Reports.")
            with open(path, "rb") as f:
                if f.read(5) != b"%PDF-":
                    raise IOError("Generated report is not a valid PDF.")
            self._last_entry_report_path = path
            return path
        except Exception as exc:
            self._last_entry_report_path = None
            return None

'''
    if marker_report not in app:
        raise RuntimeError("Could not find build_menu_bar() for report method insertion.")
    app = app.replace(marker_report, report_method + marker_report, 1)

# Add automatic report creation immediately after each successful database commit.
# Existing UI, preview, print and report windows remain unchanged.
old='''                self.conn.commit(); backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector]); messagebox.showinfo("Saved",f"Demand {no} saved successfully.")'''
new='''                self.conn.commit()
                report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
                backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
                messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
if old in app: app=app.replace(old,new,1)
else: print("Demand report patch already present or source layout differs; continuing.")
old='''                self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("grr");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock.")'''
new='''                self.conn.commit()
                report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
                backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
                messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
if old in app: app=app.replace(old,new,1)
else: print("GRN report patch already present or source layout differs; continuing.")
old='''                self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("issue");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock.")'''
new='''                self.conn.commit()
                report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
                backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
                messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
if old in app: app=app.replace(old,new,1)
else: print("Issue report patch already present or source layout differs; continuing.")

# Inventory Codes and Party Master saves also create durable PDF evidence in Reports.
if 'report_path = self._save_entry_report("Inventory Code"' not in app:
    old_item = '''                self.conn.commit(); backup_database(); load()
                messagebox.showinfo("Saved","Inventory Code saved successfully.")'''
    new_item = '''                self.conn.commit()
                report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
                backup_database(); load()
                messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
    if old_item not in app:
        raise RuntimeError("Could not find Inventory Code save block.")
    app = app.replace(old_item, new_item, 1)

if "def _manual_check_update(self):" not in app:
    marker = "    def build_menu_bar(self):\n"
    methods = '''    def _manual_check_update(self):
        try:
            updater.check_for_update(self, manual=True)
        except Exception as e:
            messagebox.showerror("Check Update", f"Could not check for updates.\\n\\n{e}", parent=self)

    def _show_current_version(self):
        try:
            messagebox.showinfo("Current Version", f"Store Inventory Management\\n\\nCurrent version: {updater.APP_VERSION}", parent=self)
        except Exception as e:
            messagebox.showerror("Current Version", str(e), parent=self)

'''
    if marker not in app:
        raise RuntimeError("Could not find build_menu_bar() in store_inventory.py.")
    app = app.replace(marker, methods + marker, 1)

needle = '        m_help.add_command(label="Backup Now",command=self.backup_now)\n'
replacement = needle + '        m_help.add_command(label="Check Update",command=self._manual_check_update)\n        m_help.add_command(label="Current Version",command=self._show_current_version)\n'
if 'label="Check Update"' not in app:
    if needle not in app:
        raise RuntimeError("Could not find Help menu in store_inventory.py.")
    app = app.replace(needle, replacement, 1)

# Fix only the reported MDI close behavior: when the last in-app child window
# is closed, restore the Dashboard surface instead of leaving the MDI host/shell
# visually empty. No dashboard layout, data query, or other UI behavior is changed.
if "def _restore_dashboard_after_internal_close(self):" not in app:
    marker_mdi = "    def _ensure_mdi_host(self):\n"
    restore_method = '''    def _restore_dashboard_after_internal_close(self):
        try:
            if getattr(self, "_mdi_windows", []):
                return
            host = getattr(self, "_mdi_host", None)
            if host is not None and host.winfo_exists():
                host.place_forget()
            # Repaint the existing Dashboard only after the child is fully closed.
            # This restores the visible Dashboard surface without changing its layout.
            self.after_idle(self.home)
        except Exception:
            try:
                self.after_idle(self.dashboard)
            except Exception:
                pass

'''
    if marker_mdi not in app:
        raise RuntimeError("Could not locate MDI host method for dashboard-close fix.")
    app = app.replace(marker_mdi, restore_method + marker_mdi, 1)

close_re = re.compile(r'(?m)(^\s+if not getattr\(self,"_mdi_windows",\[\]\):\n\s+self\._mdi_host\.place_forget\(\)\n)')
close_m = close_re.search(app)
if not close_m:
    raise RuntimeError("Could not locate last-MDI-window close block for dashboard-close fix.")
app = app[:close_m.end()] + '                self._restore_dashboard_after_internal_close()\n' + app[close_m.end():]

# Dashboard live counters: update KPI values in place every 1.2 seconds so
# newly saved Purchase Demands/GRNs/Issues/Items appear immediately without
# rebuilding or changing the existing dashboard layout.
if "_dashboard_kpi_vars" not in app:
    cards_marker = "        cards_row=tk.Frame(self.body,bg=COLORS[\"bg\"]);cards_row.pack(fill=\"x\",pady=(0,10))" + chr(10)
    if cards_marker not in app:
        raise RuntimeError("Could not locate Dashboard KPI card row.")
    loop_marker = "        for title,val,color,short in cards:" + chr(10)
    if loop_marker not in app:
        raise RuntimeError("Could not locate Dashboard KPI card loop.")
    app=app.replace(loop_marker,"        for idx,(title,val,color,short) in enumerate(cards):" + chr(10),1)
    app=app.replace(
        cards_marker,
        "        self._dashboard_kpi_vars=[tk.StringVar(value=str(x[1])) for x in cards]" + chr(10)
        + "        self._dashboard_kpi_job=None" + chr(10) + cards_marker,
        1
    )
    value_marker = "            tk.Label(bottom,text=str(val),bg=\"white\",fg=COLORS[\"primary_dark\"]," + chr(10) + "                     font=(\"Segoe UI\",21,\"bold\")).pack(side=\"left\")" + chr(10)
    value_repl = "            tk.Label(bottom,textvariable=self._dashboard_kpi_vars[idx],bg=\"white\",fg=COLORS[\"primary_dark\"]," + chr(10) + "                     font=(\"Segoe UI\",21,\"bold\")).pack(side=\"left\")" + chr(10)
    if value_marker in app:
        app=app.replace(value_marker,value_repl,1)
    else:
        raise RuntimeError("Could not locate Dashboard KPI value label.")
    method_marker = "    def dashboard_details(self,code):" + chr(10)
    refresh_method = '''    def _refresh_dashboard_kpis(self):
        try:
            if not hasattr(self,"_dashboard_kpi_vars") or not self.body.winfo_exists():
                return
            values=(
                self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0],
                self.conn.execute("SELECT COUNT(*) FROM demands").fetchone()[0],
                self.conn.execute("SELECT COUNT(*) FROM grr").fetchone()[0],
                self.conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0],
            )
            for var,val in zip(self._dashboard_kpi_vars,values):
                var.set(str(val))
            self._dashboard_kpi_job=self.after(1200,self._refresh_dashboard_kpis)
        except Exception:
            self._dashboard_kpi_job=None

'''
    if method_marker not in app:
        raise RuntimeError("Could not locate dashboard_details() for KPI refresh.")
    app=app.replace(method_marker,refresh_method+method_marker,1)
    dash_action = "        self.set_page_actions(preview=lambda:self.preview_tree(\"Dashboard Details\",tr,[f\"Item Code: {code.get() or 'ALL'}\"]))" + chr(10)
    if dash_action in app:
        app=app.replace(dash_action,dash_action+"        self._refresh_dashboard_kpis()" + chr(10),1)

# Cache-bust GitHub raw manifest so old installed builds always see the current release.
if 'import time\n' not in updater:
    updater = updater.replace('import requests\n', 'import requests\nimport time\n', 1)
updater = updater.replace(
'''        response = requests.get(manifest_url, timeout=12)
        response.raise_for_status()
''',
'''        cache_bust = int(time.time() * 1000)
        separator = "&" if "?" in manifest_url else "?"
        fresh_manifest_url = f"{manifest_url}{separator}_cb={cache_bust}"
        response = requests.get(
            fresh_manifest_url,
            headers={"Cache-Control": "no-cache, no-store, max-age=0", "Pragma": "no-cache", "Accept": "application/json"},
            timeout=12,
        )
        response.raise_for_status()
''', 1)

# Requested v1.0.82 UI/print-only fixes.
# 1) Keep exactly one taskbar tab per in-app window across repeated minimize/maximize cycles.
# The legacy minimize handler creates a new task frame each time; remove the previous
# frame immediately before creating its replacement. Window contents/state are untouched.
_task_assign_marker = '            state["task"]=item\n'
if _task_assign_marker in app and "old_task=state.get(\"task\")" not in app:
    _task_assign_replacement = '''            old_task=state.get("task")
            try:
                if old_task is not None and old_task is not item and old_task.winfo_exists():
                    old_task.destroy()
            except Exception:
                pass
            state["task"]=item
'''
    app = app.replace(_task_assign_marker, _task_assign_replacement, 1)
elif "old_task=state.get(\"task\")" not in app:
    raise RuntimeError("Could not locate MDI task assignment for duplicate-tab fix.")

# v1.0.84: root fix for repeated in-app minimize/maximize tabs.
# Always remove the current task button before restore/maximize/minimize changes state.
# This guarantees one visible task tab per in-app child window.
if "_single_mdi_task_cleanup_v1084" not in app:
    def _inject_task_cleanup(func_name):
        nonlocal_placeholder = None
        marker = f"        def {func_name}():\n"
        if marker not in app:
            raise RuntimeError(f"Could not locate internal-window {func_name}() for single-tab fix.")
        cleanup = '''        def __FUNC__():
            # _single_mdi_task_cleanup_v1084
            try:
                task=state.get("task")
                if task is not None and task.winfo_exists():
                    task.destroy()
            except Exception:
                pass
            state["task"]=None
'''.replace("__FUNC__", func_name)
        return app.replace(marker, cleanup, 1)

    app = _inject_task_cleanup("restore")
    app = _inject_task_cleanup("maximize")
    app = _inject_task_cleanup("minimize")

# 2) Requested print footer: current logged-in user + maker name.
_footer_re = re.compile(
    r'(?ms)^    def _report_footer\(self, c, page_no, page_size=A4\):\n.*?(?=^    def _grr_signature_block\()'
)
_footer_match = _footer_re.search(app)
if not _footer_match:
    raise RuntimeError("Could not locate report footer for current-user footer patch.")
_footer_function = '''    def _report_footer(self, c, page_no, page_size=A4):
        W,H=page_size
        c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
        c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
        current_name=str(getattr(self,"current_user","") or "Unknown User").strip()
        c.drawString(24,13,f"Generated by {current_name}")
        c.drawCentredString(W/2,13,"Made by Muhammad Shahzad")
        c.drawRightString(W-24,13,f"Page {page_no}")
        c.setFillColorRGB(0,0,0)

'''
app = app[:_footer_match.start()] + _footer_function + app[_footer_match.end():]

# 3) Auto-adjust printed rows to actual entered content.
# Wrap every cell (not only Description) and make each printed row only as tall
# as the longest wrapped value in that row.
_old_row_layout = '''            if desc_idx is not None and desc_idx < len(r):
                desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
            else:
                desc_lines=[""]
            row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
'''
_new_row_layout = '''            wrapped_cells=[]
            max_lines=1
            for ci in range(min(len(headers),len(r))):
                cell_lines=self._wrap_text_to_width(r[ci],"Helvetica",font_size,max(20,widths[ci]-4))
                wrapped_cells.append(cell_lines)
                max_lines=max(max_lines,len(cell_lines))
            row_h=max(11 if font_size<=7 else 13, max_lines*line_h+2)
'''
if _old_row_layout not in app:
    raise RuntimeError("Could not locate printed-row sizing block for auto-adjust patch.")
app = app.replace(_old_row_layout,_new_row_layout,1)

_old_row_draw = '''            for ci,(xx,val) in enumerate(zip(xs,r)):
                if ci==desc_idx: continue
                c.drawString(xx,y,str(val if val is not None else "")[:28])
            if desc_idx is not None and desc_idx < len(r):
                for li,ln in enumerate(desc_lines):
                    c.drawString(xs[desc_idx],y-li*line_h,ln)
'''
_new_row_draw = '''            for ci,(xx,cell_lines) in enumerate(zip(xs,wrapped_cells)):
                for li,ln in enumerate(cell_lines):
                    c.drawString(xx,y-li*line_h,ln)
'''
if _old_row_draw not in app:
    raise RuntimeError("Could not locate printed-row drawing block for auto-adjust patch.")
app = app.replace(_old_row_draw,_new_row_draw,1)

# 4) Auto-fit on-screen data-grid columns to entered content without changing
# the overall screen design. Debounced so bulk loads remain fast.
_make_tree_re = re.compile(r'(?ms)^    def make_tree\(self,parent,cols,widths=None\):\n.*?(?=^    def pick_item\()')
_make_tree_match = _make_tree_re.search(app)
if not _make_tree_match:
    raise RuntimeError("Could not locate make_tree() for auto-fit grid patch.")
_make_tree_function = '''    def _auto_fit_tree_columns(self, tr, max_width=420):
        try:
            import tkinter.font as tkfont
            try:
                font=tkfont.nametofont("TkDefaultFont")
            except Exception:
                font=None
            children=tr.get_children("")
            sample=children[:250]
            for c in tr["columns"]:
                values=[tr.heading(c,"text") or str(c)]
                for iid in sample:
                    vals=tr.item(iid,"values")
                    try:
                        idx=list(tr["columns"]).index(c)
                        if idx < len(vals): values.append(vals[idx])
                    except Exception:
                        pass
                if font is not None:
                    need=max((font.measure(str(v if v is not None else "")) for v in values),default=60)+24
                else:
                    need=max((len(str(v if v is not None else ""))*8 for v in values),default=60)+24
                current=int(tr.column(c,"width") or 0)
                tr.column(c,width=min(max(current,need),max_width))
        except Exception:
            pass

    def make_tree(self,parent,cols,widths=None):
        fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
        tr=ttk.Treeview(fr,columns=cols,show="headings")
        for i,c in enumerate(cols):
            tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
        y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
        tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
        fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)

        original_insert=tr.insert
        def schedule_fit():
            try:
                job=getattr(tr,"_autofit_job",None)
                if job:
                    self.after_cancel(job)
            except Exception:
                pass
            try:
                tr._autofit_job=self.after(120,lambda:self._auto_fit_tree_columns(tr))
            except Exception:
                pass
        def fitted_insert(*args,**kwargs):
            iid=original_insert(*args,**kwargs)
            schedule_fit()
            return iid
        tr.insert=fitted_insert
        schedule_fit()
        return tr

'''
app = app[:_make_tree_match.start()] + _make_tree_function + app[_make_tree_match.end():]

write("store_inventory.py", app)
print("CI patch complete: durable local snapshot + SQLite persistence + safe Firebase merge + permanent Reports exports + no automatic backup deletion.")

for import_line, pattern in [
    ("import os\\n", r"^import\\s+os\\s*$"),
    ("import subprocess\\n", r"^import\\s+subprocess\\s*$"),
    ("import webbrowser\\n", r"^import\\s+webbrowser\\s*$"),
    ("from pathlib import Path\\n", r"^from\\s+pathlib\\s+import\\s+Path\\s*$"),
    ("import tkinter as tk\\n", r"^import\\s+tkinter\\s+as\\s+tk\\s*$"),
    ("from tkinter import ttk, messagebox\\n", r"^from\\s+tkinter\\s+import\\s+ttk\\s*,\\s*messagebox\\s*$"),
    ("import json\\n", r"^import\\s+json\\s*$"),
    ("import requests\\n", r"^import\\s+requests\\s*$"),
]:
    if not re.search(pattern, updater, flags=re.M):
        updater = import_line + updater

# Always ensure requests is a real top-level import in the generated updater.
if not re.search(r"^import\\s+requests\\s*$", updater, flags=re.M):
    updater = "import requests\\n" + updater

if not re.search(r"^import\\s+threading\\s*$", updater, flags=re.M):
    updater = "import threading\\n" + updater


new_function = r'''def _fetch_update_info():
    config_path = Path(__file__).resolve().parent / "update_config.json"
    cfg = json.loads(config_path.read_text(encoding="utf-8-sig")) if config_path.exists() else {}
    manifest_url = str(cfg.get("manifest_url", "")).strip()
    if not manifest_url:
        raise RuntimeError("Update checking is not configured.")
    response = requests.get(
        manifest_url,
        headers={"Cache-Control": "no-cache, no-store, max-age=0", "Pragma": "no-cache"},
        timeout=3,
    )
    response.raise_for_status()
    data = response.json()
    latest = str(data.get("version", "")).strip()
    download_url = str(data.get("url", "")).strip()
    if not latest or not download_url:
        raise RuntimeError("Update information is unavailable.")
    return latest, download_url

def check_for_update(parent, manual=False):
    global _CHECK_IN_PROGRESS, _AUTO_CHECK_DONE
    if _CHECK_IN_PROGRESS:
        return False
    if manual:
        _CHECK_IN_PROGRESS = True
        try:
            latest, download_url = _fetch_update_info()
            if _version_tuple(latest) <= _version_tuple(APP_VERSION):
                messagebox.showinfo("Check Update", f"You are using the current version ({APP_VERSION}).", parent=parent)
                return False
            if not messagebox.askyesno(
                "Update Available",
                f"A new version ({latest}) is available.\n\nDo you want to download it now?",
                parent=parent,
            ):
                return False
            return _start_update_download(download_url)
        except Exception as exc:
            messagebox.showwarning("Check Update", f"Could not check for updates.\n\n{exc}", parent=parent)
            return False
        finally:
            _CHECK_IN_PROGRESS = False

    if _AUTO_CHECK_DONE:
        return False
    _AUTO_CHECK_DONE = True
    _CHECK_IN_PROGRESS = True

    def worker():
        global _CHECK_IN_PROGRESS
        try:
            latest, download_url = _fetch_update_info()
            if _version_tuple(latest) <= _version_tuple(APP_VERSION):
                _CHECK_IN_PROGRESS = False
                return
            def prompt_on_ui():
                global _CHECK_IN_PROGRESS
                try:
                    if messagebox.askyesno(
                        "Update Available",
                        f"A new version ({latest}) is available.\n\nDo you want to download it now?",
                        parent=parent,
                    ):
                        _start_update_download(download_url)
                finally:
                    _CHECK_IN_PROGRESS = False
            try:
                parent.after(0, prompt_on_ui)
            except Exception:
                _CHECK_IN_PROGRESS = False
        except Exception:
            _CHECK_IN_PROGRESS = False

    threading.Thread(target=worker, name="UpdateCheck", daemon=True).start()
    return True
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
# Check for updates once after the Dashboard is shown at login.
_home_block = """        self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
        self.main_body=self.body
        self.dashboard()
"""
_home_replacement = """        self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
        self.main_body=self.body
        self.dashboard()
        if not getattr(self, "_update_checked_this_session", False):
            self._update_checked_this_session = True
            self.after(900, lambda: updater.check_for_update(self, manual=False))
"""
if _home_block not in app:
    raise RuntimeError("Could not locate Home dashboard block for update check.")
app = app.replace(_home_block, _home_replacement, 1)
if "import updater" not in app:
    m = re.search(r'^(import\s+[^\n]+\n)', app, flags=re.M)
    if m:
        app = app[:m.end()] + "import updater\n" + app[m.end():]
    else:
        app = "import updater\n" + app
if "import durable_local" not in app:
    m = re.search(r'^(import updater\n)', app, flags=re.M)
    if m:
        app = app[:m.end()] + "import durable_local\n" + app[m.end():]
    else:
        app = "import durable_local\n" + app

# Restore a larger local snapshot before Firebase startup sync when SQLite is
# unexpectedly empty/smaller. This is deliberately non-destructive: it never
# restores over a database that already contains at least as many records.
marker = '    migrate_old_item_codes(raw)\n'
restore_code = '''    migrate_old_item_codes(raw)
    try:
        durable_local.restore_if_newer(raw)
    except Exception:
        pass
'''
if "durable_local.restore_if_newer(raw)" not in app:
    if marker not in app:
        raise RuntimeError("Could not find connect() migration point in store_inventory.py.")
    app = app.replace(marker, restore_code, 1)

# Save a current local snapshot after startup synchronization has completed.
marker2 = '    return OnlineConnection(DB, sync)\n'
replace2 = '''    try:
        durable_local.save(raw)
    except Exception:
        pass
    return OnlineConnection(DB, sync)
'''
if "durable_local.save(raw)" not in app:
    if marker2 not in app:
        raise RuntimeError("Could not find connect() return point in store_inventory.py.")
    app = app.replace(marker2, replace2, 1)

# IMPORTANT: old builds rotated automatic backups and deleted older files.
# The requested behavior is never to auto-delete stored data/backups.
app, backup_patch_count = re.subn(
    r'(?ms)^        # Rotate: keep all manual backups, but only the newest 30 automatic ones\.\n.*?^        return zpath',
    '        # Automatic backup rotation/deletion is intentionally disabled.\n        # Stored backups remain until the user explicitly deletes/restores them.\n        return zpath',
    app,
    count=1,
)
if backup_patch_count not in (0, 1):
    raise RuntimeError("Unexpected backup patch match count.")

# Make Preview -> Export PDF fail loudly and leave the verified file in the
# permanent Reports folder. Print buttons remain print-only.
export_re = re.compile(r'(?ms)^    def export_preview_pdf\(self, title, header_lines, columns, rows\):\n.*?(?=^    def export_preview_word\(self, title, header_lines, columns, rows\):)')
export_match = export_re.search(app)
if export_match:
    export_function = '''    def export_preview_pdf(self, title, header_lines, columns, rows):
        """Write the visible preview to C:\\StoreInventoryManagement\\Reports."""
        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)
            safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
            path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
            generated = False
            if REPORTLAB:
                try:
                    self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
                    generated = True
                except Exception:
                    generated = False
            if not generated:
                self._fallback_pdf_export(path, title, header_lines, columns, rows)
            if not os.path.isfile(path) or os.path.getsize(path) <= 0:
                raise IOError("The PDF file was not created in the Reports folder.")
            with open(path, "rb") as pf:
                signature = pf.read(5)
            if signature != b"%PDF-":
                raise IOError("The generated file is not a valid PDF.")
            self._last_report_path = path
            try:
                webbrowser.open("file://" + path)
            except Exception:
                self.open_file(path)
            return path
        except Exception as e:
            messagebox.showerror("PDF Export", f"Could not generate the PDF.\\n\\n{e}")
            return None

'''
    app = app[:export_match.start()] + export_function + app[export_match.end():]
else:
    raise RuntimeError("Could not locate export_preview_pdf() in store_inventory.py")

# Every saved business entry also gets a durable PDF copy in Reports. This is
# deliberately best-effort: a report failure must never roll back an already
# committed database transaction.
if "def _save_entry_report(self, title, header_lines, columns, rows):" not in app:
    marker_report = "    def export_preview_pdf(self, title, header_lines, columns, rows):\n"
    report_method = '''    def _save_entry_report(self, title, header_lines, columns, rows):
        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)
            safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
            page_size = landscape(A4) if len(columns) > 8 else A4
            if REPORTLAB:
                self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
            else:
                self._fallback_pdf_export(path, title, header_lines, columns, rows)
            if not os.path.isfile(path) or os.path.getsize(path) <= 0:
                raise IOError("PDF was not created in C:\\\\StoreInventoryManagement\\\\Reports.")
            with open(path, "rb") as f:
                if f.read(5) != b"%PDF-":
                    raise IOError("Generated report is not a valid PDF.")
            self._last_entry_report_path = path
            return path
        except Exception as exc:
            self._last_entry_report_path = None
            return None

'''
    if marker_report not in app:
        raise RuntimeError("Could not find build_menu_bar() for report method insertion.")
    app = app.replace(marker_report, report_method + marker_report, 1)

# Add automatic report creation immediately after each successful database commit.
# Existing UI, preview, print and report windows remain unchanged.
old='''                self.conn.commit(); backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector]); messagebox.showinfo("Saved",f"Demand {no} saved successfully.")'''
new='''                self.conn.commit()
                report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
                backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
                messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
if old in app: app=app.replace(old,new,1)
else: print("Demand save report patch already present or source layout differs; continuing.")
old='''                self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("grr");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock.")'''
new='''                self.conn.commit()
                report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
                backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
                messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
if old in app: app=app.replace(old,new,1)
else: print("GRN save report patch already present or source layout differs; continuing.")
old='''                self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("issue");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock.")'''
new='''                self.conn.commit()
                report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
                backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
                messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
if old in app: app=app.replace(old,new,1)
else: print("Issue save report patch already present or source layout differs; continuing.")

# Inventory Codes and Party Master saves also create durable PDF evidence in Reports.
if 'report_path = self._save_entry_report("Inventory Code"' not in app:
    old_item = '''                self.conn.commit(); backup_database(); load()
                messagebox.showinfo("Saved","Inventory Code saved successfully.")'''
    new_item = '''                self.conn.commit()
                report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
                backup_database(); load()
                messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
    if old_item not in app:
        raise RuntimeError("Could not find Inventory Code save block.")
    app = app.replace(old_item, new_item, 1)

if "def _manual_check_update(self):" not in app:
    marker = "    def build_menu_bar(self):\n"
    methods = '''    def _manual_check_update(self):
        try:
            updater.check_for_update(self, manual=True)
        except Exception as e:
            messagebox.showerror("Check Update", f"Could not check for updates.\\n\\n{e}", parent=self)

    def _show_current_version(self):
        try:
            messagebox.showinfo("Current Version", f"Store Inventory Management\\n\\nCurrent version: {updater.APP_VERSION}", parent=self)
        except Exception as e:
            messagebox.showerror("Current Version", str(e), parent=self)

'''
    if marker not in app:
        raise RuntimeError("Could not find build_menu_bar() in store_inventory.py.")
    app = app.replace(marker, methods + marker, 1)

needle = '        m_help.add_command(label="Backup Now",command=self.backup_now)\n'
replacement = needle + '        m_help.add_command(label="Check Update",command=self._manual_check_update)\n        m_help.add_command(label="Current Version",command=self._show_current_version)\n'
if 'label="Check Update"' not in app:
    if needle not in app:
        raise RuntimeError("Could not find Help menu in store_inventory.py.")
    app = app.replace(needle, replacement, 1)

# Fix only the reported MDI close behavior: when the last in-app child window
# is closed, restore the Dashboard surface instead of leaving the MDI host/shell
# visually empty. No dashboard layout, data query, or other UI behavior is changed.
if "def _restore_dashboard_after_internal_close(self):" not in app:
    marker_mdi = "    def _ensure_mdi_host(self):\n"
    restore_method = '''    def _restore_dashboard_after_internal_close(self):
        try:
            if getattr(self, "_mdi_windows", []):
                return
            host = getattr(self, "_mdi_host", None)
            if host is not None and host.winfo_exists():
                host.place_forget()
            # Repaint the existing Dashboard only after the child is fully closed.
            # This restores the visible Dashboard surface without changing its layout.
            self.after_idle(self.home)
        except Exception:
            try:
                self.after_idle(self.dashboard)
            except Exception:
                pass

'''
    if marker_mdi not in app:
        raise RuntimeError("Could not locate MDI host method for dashboard-close fix.")
    app = app.replace(marker_mdi, restore_method + marker_mdi, 1)

close_re = re.compile(r'(?m)(^\s+if not getattr\(self,"_mdi_windows",\[\]\):\n\s+self\._mdi_host\.place_forget\(\)\n)')
close_m = close_re.search(app)
if not close_m:
    raise RuntimeError("Could not locate last-MDI-window close block for dashboard-close fix.")
app = app[:close_m.end()] + '                self._restore_dashboard_after_internal_close()\n' + app[close_m.end():]

# Dashboard live counters: update KPI values in place every 1.2 seconds so
# newly saved Purchase Demands/GRNs/Issues/Items appear immediately without
# rebuilding or changing the existing dashboard layout.
if "_dashboard_kpi_vars" not in app:
    cards_marker = "        cards_row=tk.Frame(self.body,bg=COLORS[\"bg\"]);cards_row.pack(fill=\"x\",pady=(0,10))" + chr(10)
    if cards_marker not in app:
        raise RuntimeError("Could not locate Dashboard KPI card row.")
    loop_marker = "        for title,val,color,short in cards:" + chr(10)
    if loop_marker not in app:
        raise RuntimeError("Could not locate Dashboard KPI card loop.")
    app=app.replace(loop_marker,"        for idx,(title,val,color,short) in enumerate(cards):" + chr(10),1)
    app=app.replace(
        cards_marker,
        "        self._dashboard_kpi_vars=[tk.StringVar(value=str(x[1])) for x in cards]" + chr(10)
        + "        self._dashboard_kpi_job=None" + chr(10) + cards_marker,
        1
    )
    value_marker = "            tk.Label(bottom,text=str(val),bg=\"white\",fg=COLORS[\"primary_dark\"]," + chr(10) + "                     font=(\"Segoe UI\",21,\"bold\")).pack(side=\"left\")" + chr(10)
    value_repl = "            tk.Label(bottom,textvariable=self._dashboard_kpi_vars[idx],bg=\"white\",fg=COLORS[\"primary_dark\"]," + chr(10) + "                     font=(\"Segoe UI\",21,\"bold\")).pack(side=\"left\")" + chr(10)
    if value_marker in app:
        app=app.replace(value_marker,value_repl,1)
    else:
        raise RuntimeError("Could not locate Dashboard KPI value label.")
    method_marker = "    def dashboard_details(self,code):" + chr(10)
    refresh_method = '''    def _refresh_dashboard_kpis(self):
        try:
            if not hasattr(self,"_dashboard_kpi_vars") or not self.body.winfo_exists():
                return
            values=(
                self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0],
                self.conn.execute("SELECT COUNT(*) FROM demands").fetchone()[0],
                self.conn.execute("SELECT COUNT(*) FROM grr").fetchone()[0],
                self.conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0],
            )
            for var,val in zip(self._dashboard_kpi_vars,values):
                var.set(str(val))
            self._dashboard_kpi_job=self.after(1200,self._refresh_dashboard_kpis)
        except Exception:
            self._dashboard_kpi_job=None

'''
    if method_marker not in app:
        raise RuntimeError("Could not locate dashboard_details() for KPI refresh.")
    app=app.replace(method_marker,refresh_method+method_marker,1)
    dash_action = "        self.set_page_actions(preview=lambda:self.preview_tree(\"Dashboard Details\",tr,[f\"Item Code: {code.get() or 'ALL'}\"]))" + chr(10)
    if dash_action in app:
        app=app.replace(dash_action,dash_action+"        self._refresh_dashboard_kpis()" + chr(10),1)


# v1.0.87 performance-only patch: local-cache-first startup and non-blocking network refresh.
# Existing UI, data model, reports, permissions and screen layout remain unchanged.
_connect_sync_re = re.compile(
    r'(?ms)^    sync = FirebaseSync\(FIREBASE_URL_FILE, INSTALL_DIR\)\n.*?^    return OnlineConnection\(DB, sync\)\n'
)
_connect_sync_match = _connect_sync_re.search(app)
if not _connect_sync_match:
    raise RuntimeError("Could not locate connect() Firebase startup block for performance patch.")
_fast_connect = '''    sync = FirebaseSync(FIREBASE_URL_FILE, INSTALL_DIR)
    if sync.enabled:
        try:
            # Established installations open immediately from the durable local cache.
            # Firebase refresh runs in the background and is applied on a later read.
            state_ready = os.path.isfile(sync.state_path) and os.path.getsize(sync.state_path) > 2
            if state_ready:
                sync.kick_background_pull(force=True)
            else:
                # First install still receives cloud data before use, with the short
                # Firebase timeout configured in firebase_sync.py.
                sync.initialize(raw)
                _init_schema(raw)
        except Exception as exc:
            sync.pending_error = str(exc)
    try:
        # Do not rewrite a full JSON recovery snapshot on every launch.
        # Commits still update the durable snapshot exactly as before.
        snap_path = getattr(durable_local, "SNAPSHOT_PATH", None)
        if not snap_path or not os.path.exists(os.fspath(snap_path)):
            durable_local.save(raw)
    except Exception:
        pass
    return OnlineConnection(DB, sync)
'''
app = app[:_connect_sync_match.start()] + _fast_connect + app[_connect_sync_match.end():]

write("store_inventory.py", app)
print("CI patch complete: durable local snapshot + SQLite persistence + safe Firebase merge + permanent Reports exports + no automatic backup deletion.")
