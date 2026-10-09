"""v1.0.91: Move Inventory Codes import to Code Opening, avoid duplicate views.

Patch runs after the v1.0.89 importer and v1.0.90 MDI behavior patches.
Only Inventory Codes list UI and Code Opening import control are touched.
"""
from pathlib import Path

source = Path(__file__).resolve().parent / "source" / "store_inventory.py"
app = source.read_text(encoding="utf-8-sig")

items_start = app.index("    def items(self, container=None):")
items_end = app.index("\n    def inventory_codes(self):", items_start)
items = app[items_start:items_end]
old_import = (
    '        from inventory_import_ui_v1089 import show_import_dialog\n'
    '        ttk.Button(head,text="Import Excel / PDF",style="Primary.TButton",\n'
    '                   command=lambda:show_import_dialog(self,lambda:self.items(container=body),BACKUP_DIR)).pack(side="right",padx=3)\n'
)
assert items.count(old_import) == 1, "Original Inventory Codes import button/callback was not found"
items = items.replace(old_import, "", 1)
# A re-render of a child view must replace the existing view completely, not
# just its first heading widget. This prevents stacked/duplicate lists.
old_clear = '''        if body.winfo_children():
            try: body.winfo_children()[0].destroy()
            except Exception: pass
'''
new_clear = '''        if container is not None:
            for old_widget in list(body.winfo_children()):
                old_widget.destroy()
        elif body.winfo_children():
            try: body.winfo_children()[0].destroy()
            except Exception: pass
'''
assert items.count(old_clear) == 1, "Existing Inventory Codes rendering cleanup changed"
items = items.replace(old_clear, new_clear, 1)
app = app[:items_start] + items + app[items_end:]

# Code Opening is an existing MDI popup. Add the action directly to its
# existing buttons row; do not create any Inventory Codes window in the import.
start = app.index("    def _open_code_opening_detail(")
end = app.index("\n    def _mto_new_item_dialog(", start)
opening = app[start:end]
button_anchor = '        btns = ttk.Frame(box)\n'
assert opening.count(button_anchor) == 1, "Code Opening buttons frame not found"
assert 'text="Import Excel / PDF"' not in opening, "Code Opening already has import button"

handler = '''        def _refresh_existing_inventory_codes_after_import():
            # Refresh only already-open Inventory Codes list windows.
            # The old callback called items() again and duplicated the screen.
            def invoke_refresh(widget):
                try:
                    if isinstance(widget, (ttk.Button, tk.Button)) and widget.cget("text") == "Refresh":
                        widget.invoke()
                        return True
                    for child in widget.winfo_children():
                        if invoke_refresh(child):
                            return True
                except tk.TclError:
                    pass
                return False

            for child_window in list(getattr(self, "_mdi_windows", ())):
                try:
                    if (child_window.winfo_exists() and
                            "inventory codes" in str(getattr(child_window, "_mdi_title", "")).lower()):
                        invoke_refresh(child_window)
                except tk.TclError:
                    continue

        def _import_inventory_codes_from_opening():
            from inventory_import_ui_v1089 import show_import_dialog
            show_import_dialog(self, _refresh_existing_inventory_codes_after_import, BACKUP_DIR)

'''
opening = opening.replace(button_anchor, handler + button_anchor, 1)
# Separate second row prevents extra buttons from overcrowding the original
# Save/Edit/Delete/Cancel row and leaves the form dimensions unchanged.
cancel_line = '        ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)\n'
assert opening.count(cancel_line) == 1, "Code Opening CANCEL button changed"
opening = opening.replace(cancel_line, cancel_line +
    '        ttk.Button(box, text="Import Excel / PDF", style="Primary.TButton",\n'
    '                   command=_import_inventory_codes_from_opening).grid(row=9, column=0, columnspan=4, pady=(6, 0))\n', 1)
app = app[:start] + opening + app[end:]
assert app.count('text="Import Excel / PDF"') == 1, "Import control must appear in Code Opening only"
assert 'command=lambda:show_import_dialog(self,lambda:self.items(container=body),BACKUP_DIR)' not in app
compile(app, str(source), "exec")
source.write_text(app, encoding="utf-8")
print("v1.0.91: import moved to Code Opening; one control; no duplicate Inventory Codes rebuild")
