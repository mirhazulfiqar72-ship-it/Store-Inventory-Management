"""Compact import Preview dialog for Inventory Codes, no other UI changes."""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import inventory_import_v1089 as engine

def show_import_dialog(app, on_success, backup_dir):
    filename = filedialog.askopenfilename(
        parent=app,
        title="Import Inventory Codes - Update & Add",
        filetypes=[("Excel / PDF / CSV", "*.xlsx *.xlsm *.xls *.pdf *.csv"),
                   ("Excel", "*.xlsx *.xlsm *.xls"),
                   ("PDF", "*.pdf"),
                   ("CSV", "*.csv")])
    if not filename:
        return
    try:
        imported = engine.read_file(filename)
        changes = engine.preview(app.conn, imported)
    except Exception as error:
        messagebox.showerror("Import Inventory Codes", str(error), parent=app)
        return
    totals = {name: sum(action == name for _, action, _ in changes)
              for name in ("New", "Update", "Unchanged", "MTO conflict")}
    dialog = tk.Toplevel(app)
    dialog.title("Import Inventory Codes - Preview")
    dialog.geometry("980x550")
    dialog.minsize(760, 390)
    dialog.transient(app)
    dialog.grab_set()
    body = ttk.Frame(dialog, padding=12)
    body.pack(fill="both", expand=True)
    ttk.Label(body, text="Import Inventory Codes - Update & Add",
              font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
    ttk.Label(body, text="File: " + os.path.basename(filename)).pack(anchor="w")
    ttk.Label(body, text=(
        f"Total: {len(changes)}    New: {totals['New']}    "
        f"Update: {totals['Update']}    Unchanged: {totals['Unchanged']}    "
        f"MTO conflicts: {totals['MTO conflict']}")).pack(anchor="w", pady=(4, 2))
    ttk.Label(body, text="Codes absent from this file stay unchanged. GRN, Demand and Issue data are not removed.").pack(anchor="w", pady=(0, 7))
    frame = ttk.Frame(body)
    frame.pack(fill="both", expand=True)
    columns = ("Action", "Code", "Description", "UOM", "Opening Balance")
    table = ttk.Treeview(frame, columns=columns, show="headings")
    for column, width in zip(columns, (125, 150, 390, 115, 135)):
        table.heading(column, text=column)
        table.column(column, width=width, anchor=("w" if column == "Description" else "center"))
    scroll = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    table.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    for item, action, _ in changes:
        table.insert("", "end", values=(
            action, item.code, item.description,
            item.uom if item.uom is not None else "(keep/default)",
            item.opening if item.opening is not None else "(keep/0)"))
    warning = "MTO conflict found - remove conflicting rows before import." if totals["MTO conflict"] else (
        "A full timestamped SQLite backup is saved before import. Firebase sync stays enabled.")
    ttk.Label(body, text=warning, wraplength=830).pack(anchor="w", pady=(8, 6))
    row = ttk.Frame(body)
    row.pack(fill="x")
    def do_import():
        if not messagebox.askyesno(
            "Confirm Import",
            f"Add {totals['New']} new codes and update {totals['Update']} existing codes?\n"
            "Unlisted codes remain. A database backup will be saved first.",
            parent=dialog):
            return
        try:
            result = engine.apply(app.conn, imported, backup_dir)
        except Exception as error:
            messagebox.showerror("Inventory Import Failed", str(error), parent=dialog)
            return
        dialog.destroy()
        summary = (
            f"New codes: {result['new']}   Updated: {result['updated']}   "
            f"Unchanged: {result['unchanged']}\n\nBackup: {result['backup']}")
        if result["online_pending"]:
            messagebox.showwarning("Inventory Imported - Online Sync Pending",
                                   summary + "\n\nFirebase sync pending; the app will retry.", parent=app)
        else:
            messagebox.showinfo("Inventory Codes Imported", summary, parent=app)
        on_success()
    ttk.Button(row, text="Cancel", command=dialog.destroy).pack(side="right", padx=4)
    ttk.Button(row, text="Import & Sync", command=do_import,
               state="disabled" if totals["MTO conflict"] else "normal").pack(side="right", padx=4)
    dialog.bind("<Escape>", lambda event: dialog.destroy())
