"""Integrate Import Excel/PDF button into EXISTING Inventory Codes window only."""
from pathlib import Path
import re

path = Path(__file__).resolve().parent / "source" / "store_inventory.py"
text = path.read_text(encoding="utf-8-sig")
begin = text.index("    def items(self, container=None):")
end = text.index("\n    def inventory_codes(self):", begin)
section = text[begin:end]
marker = '        ttk.Button(head,text="Refresh",style="Success.TButton",command=load).pack(side="right",padx=3)'
assert section.count(marker) == 1, "Expected Inventory Codes Refresh button was not found"
assert "Import Excel / PDF" not in section, "Duplicate Import button"
insertion = (
    '        from inventory_import_ui_v1089 import show_import_dialog\n'
    '        ttk.Button(head,text="Import Excel / PDF",style="Primary.TButton",\n'
    '                   command=lambda:show_import_dialog(self,lambda:self.items(container=body),BACKUP_DIR)).pack(side="right",padx=3)\n'
)
section = section.replace(marker, insertion + marker, 1)
text = text[:begin] + section + text[end:]
compile(text, str(path), "exec")
path.write_text(text, encoding="utf-8")
print("v1.0.89 Inventory Codes Import button integrated; UI and all other sections unchanged")
