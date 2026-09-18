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
if backup_patch_count != 1:
    raise RuntimeError("Could not disable automatic backup deletion safely.")

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
else: raise RuntimeError("Demand save pattern not found.")
old='''                self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("grr");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock.")'''
new='''                self.conn.commit()
                report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
                backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
                messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
if old in app: app=app.replace(old,new,1)
else: raise RuntimeError("GRN save pattern not found.")
old='''                self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("issue");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock.")'''
new='''                self.conn.commit()
                report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
                backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
                messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\\n\\nReport saved to:\\n{report_path}" if report_path else "\\n\\nWarning: PDF report could not be generated; the saved data is retained."))'''
if old in app: app=app.replace(old,new,1)
else: raise RuntimeError("Issue save pattern not found.")

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
    marker_mdi = "    def _ensure_mdi_host(self):\\n"
    restore_method = '''    def _restore_dashboard_after_internal_close(self):
        try:
            if getattr(self, "_mdi_windows", []):
                return
            host = getattr(self, "_mdi_host", None)
            if host is not None and host.winfo_exists():
                host.place_forget()
            # Repaint the existing Dashboard only after the child is fully closed.
            # This restores the visible Dashboard surface without changing its layout.
            self.after_idle(self.dashboard)
        except Exception:
            try:
                self.after_idle(self.dashboard)
            except Exception:
                pass

'''
    if marker_mdi not in app:
        raise RuntimeError("Could not locate MDI host method for dashboard-close fix.")
    app = app.replace(marker_mdi, restore_method + marker_mdi, 1)

close_re = re.compile(r'(?m)(^\\s+if not getattr\\(self,"_mdi_windows",\\[\\]\\):\\n\\s+self\\._mdi_host\\.place_forget\\(\\)\\n)')
close_m = close_re.search(app)
if not close_m:
    raise RuntimeError("Could not locate last-MDI-window close block for dashboard-close fix.")
app = app[:close_m.end()] + '                self._restore_dashboard_after_internal_close()\\n' + app[close_m.end():]

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

write("store_inventory.py", app)
print("CI patch complete: durable local snapshot + SQLite persistence + safe Firebase merge + permanent Reports exports + no automatic backup deletion.")
