"""v1.0.92: Make Find Text dialog match user's compact 357 x 130 reference.

Only swaps the common Find Text popup presentation: same callable search_fn,
Enter/ Escape behavior, no data/logic/other-window modifications.
"""
from pathlib import Path

file = Path(__file__).resolve().parent / "source" / "store_inventory.py"
src = file.read_text(encoding="utf-8-sig")
begin_token = "    def _open_exact_find_text_popup(self, search_fn):\n"
end_token = "    def _global_enter(self, event=None):\n"
assert src.count(begin_token) == 1, "Cannot locate unique Find Text popup"
start = src.index(begin_token)
end = src.index(end_token, start)
original = src[start:end]
assert "Find Next" in original and "Cancel" in original
assert "search_fn(" in original and "grab_release" in original

new = '''    def _open_exact_find_text_popup(self, search_fn):
        """Compact Windows Find Text dialog: 357x130 including the title bar."""
        existing = getattr(self, "_exact_find_text_dialog", None)
        try:
            if existing is not None and existing.winfo_exists():
                existing.lift()
                existing.focus_force()
                return
        except tk.TclError:
            pass

        dlg = tk.Toplevel(self)
        self._exact_find_text_dialog = dlg
        dlg.title("Find Text")
        # Windows title bar is about 30 px; client area is 357x100.
        dlg.geometry("357x100")
        dlg.resizable(False, False)
        dlg.transient(self)

        # Match screenshot #2's text/input/buttons position exactly.
        ttk.Label(dlg, text="Find what:").place(x=14, y=15)
        value = tk.StringVar()
        fe = ttk.Entry(dlg, textvariable=value)
        fe.place(x=14, y=40, width=199, height=21)

        def do_find():
            text = value.get().strip()
            if not text:
                fe.focus_set()
                return
            try:
                found = search_fn(text)
            except Exception:
                found = False
            if found is False:
                messagebox.showinfo("Find Text", "No matching text found.", parent=dlg)

        def close():
            try:
                dlg.grab_release()
            except Exception:
                pass
            try:
                dlg.destroy()
            except Exception:
                pass
            if getattr(self, "_exact_find_text_dialog", None) is dlg:
                self._exact_find_text_dialog = None

        ttk.Button(dlg, text="Find Next", command=do_find).place(
            x=229, y=40, width=113, height=23)
        ttk.Button(dlg, text="Cancel", command=close).place(
            x=229, y=69, width=113, height=23)

        fe.bind("<Return>", lambda event: (do_find(), "break")[1])
        dlg.bind("<Escape>", lambda event: (close(), "break")[1])
        dlg.protocol("WM_DELETE_WINDOW", close)
        dlg.grab_set()
        dlg.after_idle(fe.focus_set)

'''
updated = src[:start] + new + src[end:]
assert updated[:start] == src[:start]
assert updated.endswith(src[end:])
assert updated.count('dlg.geometry("357x100")') == 1
assert updated.count('ttk.Button(dlg, text="Find Next"') == 1
assert updated.count('ttk.Button(dlg, text="Cancel"') == 1
compile(updated, str(file), "exec")
file.write_text(updated, encoding="utf-8")
print("Find Text dialog visual-only patch applied: 357x100 client (357x130 outer), native ttk controls")
