"""Add ONLY v1.0.88 Firebase reset hook and Pair UOM after existing CI patch.

This script is run after ci_patch_source.py, before source audit and PyInstaller.
"""
from pathlib import Path
import re

root = Path(__file__).resolve().parent
p = root / "source" / "store_inventory.py"
app = p.read_text(encoding="utf-8-sig")
marker = '    sync = FirebaseSync(FIREBASE_URL_FILE, INSTALL_DIR)\n'
assert app.count(marker) == 1, "connect() Firebase hook changed; review required"
hook = (
    marker
    + '    # v1.0.88: one-time cloud-authoritative Inventory Codes/document reset.\n'
    + '    from inventory_reset_v1088 import apply_reset\n'
    + '    apply_reset(raw, sync, resource_path("inventory_codes_102.csv"), BACKUP_DIR)\n'
)
app = app.replace(marker, hook, 1)
match = re.search(r'(?m)^(UOM_OPTIONS\s*=\s*\[)([^\n]*?)(\])', app)
assert match, "UOM_OPTIONS missing in source"
if '"Pair"' not in match.group(2) and "'Pair'" not in match.group(2):
    app = app[:match.start(3)] + ',"Pair"' + app[match.start(3):]
assert 'apply_reset(raw, sync, resource_path("inventory_codes_102.csv"), BACKUP_DIR)' in app
assert '"Pair"' in app or "'Pair'" in app
p.write_text(app, encoding="utf-8")
print("v1.0.88 post-patch complete: one-time inventory reset, Pair UOM")
