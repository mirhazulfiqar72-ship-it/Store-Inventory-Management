"""v1.0.90: Fix MDI minimize screen selection only.

Builds on the existing source after all prior patches. No data schema, logic,
transactions, Firebase, screen layout, or report changes.
"""
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / 'source' / 'store_inventory.py'
app = SOURCE.read_text(encoding='utf-8-sig')

start = app.index('    def _ensure_mdi_host(self):\n')
end = app.index('\n    def open_inventory_codes_with_filters(self):', start)
mdi = app[start:end]


def replace_once(old, new):
    global mdi
    count = mdi.count(old)
    if count != 1:
        where = mdi.find('        def restore')
        context = mdi[max(0,where-80):where+500] if where >= 0 else mdi[0:900]
        raise RuntimeError(f'MDI patch anchor unexpectedly occurs {count} times: {old!r}\\nActual MDI excerpt: {context!r}')
    mdi = mdi.replace(old, new, 1)


helpers = '''    def _mdi_hide_dashboard_minimized_bar(self):
        """Remove only the temporary restore buttons on Dashboard."""
        bar = getattr(self, "_mdi_dashboard_minimized_bar", None)
        if bar is not None:
            try:
                if bar.winfo_exists():
                    bar.destroy()
            except Exception:
                pass
        self._mdi_dashboard_minimized_bar = None

    def _mdi_show_next_after_minimize(self):
        """Reveal another open child; otherwise show Dashboard, not grey MDI."""
        windows = [w for w in getattr(self, "_mdi_windows", []) if w.winfo_exists()]
        unminimized = [w for w in windows if not getattr(w, "_mdi_minimized", False)]
        if unminimized:
            self._mdi_hide_dashboard_minimized_bar()
            unminimized[-1].lift()
            return
        host = getattr(self, "_mdi_host", None)
        if host is not None and host.winfo_exists():
            host.place_forget()
        # The original Dashboard is still present behind the in-app host.
        # Restore the existing header/navbar without rebuilding the application.
        for attr in ("_shell_header", "_shell_nav"):
            widget = getattr(self, attr, None)
            if widget is not None and widget.winfo_exists():
                try:
                    widget.pack(fill="x", before=self.main_body)
                except Exception:
                    widget.pack(fill="x")
        self._mdi_hide_dashboard_minimized_bar()
        minimized = [w for w in windows if getattr(w, "_mdi_minimized", False)]
        if not minimized:
            return
        # The original minimized tabs are children of the hidden MDI host.
        # Mirror their Restore actions on the Dashboard so they stay clickable.
        bar = tk.Frame(self.main_body, bg="#e7e7e7", bd=1,
                       relief="sunken", height=28)
        bar.place(relx=0, rely=1, relwidth=1, y=-28, height=28)
        self._mdi_dashboard_minimized_bar = bar
        for window in minimized:
            tk.Button(bar, text=getattr(window, "_mdi_title", "Window"),
                      font=("Segoe UI", 8), height=1, padx=5, pady=0,
                      command=window._internal_restore, relief="raised",
                      bg="#e7e7e7").pack(side="left", padx=2, pady=2)
        bar.lift()

'''
app = app[:start] + helpers + app[start:]
start = app.index('    def _ensure_mdi_host(self):\n')
end = app.index('\n    def open_inventory_codes_with_filters(self):', start)
mdi = app[start:end]

replace_once('        host.lift()\n',
             '        host.lift()\n        self._mdi_hide_dashboard_minimized_bar()\n')
replace_once('        outer=tk.Frame(host,bg="white",bd=1,relief="raised")\n',
             '        outer=tk.Frame(host,bg="white",bd=1,relief="raised")\n'
             '        outer._mdi_title=str(title)\n'
             '        outer._mdi_minimized=False\n')
replace_once('''        def restore():
''', '''        def restore():
            if state["min"]:
                self._ensure_mdi_host()
                outer._mdi_minimized=False
''')
replace_once('''            outer.place_forget(); state["min"]=True
''', '''            outer.place_forget(); state["min"]=True
            outer._mdi_minimized=True
''')
replace_once('''            state["task"]=item
''', '''            state["task"]=item
            self._mdi_show_next_after_minimize()
''')
replace_once('''        tk.Button(controls,text="_",''', '''            # Closing a visible child also reveals another open child; if all
            # remaining children are minimized, show Dashboard with restore tabs.
            if getattr(self,"_mdi_windows",[]):
                self._mdi_show_next_after_minimize()
            else:
                self._mdi_hide_dashboard_minimized_bar()
        tk.Button(controls,text="_",''')

app = app[:start] + mdi + app[end:]
compile(app, str(SOURCE), 'exec')
SOURCE.write_text(app, encoding='utf-8')
print('v1.0.90 MDI minimize patch applied: dashboard fallback, open-child promotion, restore tabs')
