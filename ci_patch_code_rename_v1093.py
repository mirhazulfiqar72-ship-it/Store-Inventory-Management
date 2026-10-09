"""v1.0.93: only item-code rename transaction integrity, import, and preview.

Run after all previous v1.0.92 patch scripts. Fail build if any expected source
anchor has moved, rather than shipping a partly modified application.
"""
from pathlib import Path
import re

root=Path(__file__).resolve().parent / 'source'

def get(name):return (root/name).read_text(encoding='utf-8-sig')
def put(name,data):
    compile(data,name,'exec')
    (root/name).write_text(data,encoding='utf-8')

def once(s, old, new, desc):
    assert s.count(old)==1, f'{desc}: expected exactly one source anchor, got {s.count(old)}'
    return s.replace(old,new,1)

# Add optional Old Item Code import-column and delegate matching/renaming to
# the shared transaction-safe engine, retaining all existing formats and I/O.
s=get('inventory_import_v1089.py')
s=once(s, '    location: str\n', '    location: str\n    old_code: str | None = None\n','Item dataclass')
s=once(s,'ALIASES = {\n',
        'ALIASES = {\n    "old_code": {"oldcode","olditemcode","previouscode","previousitemcode","existingitemcode","fromitemcode"},\n',
        'Column aliases')
s=once(s,'items.append(Item(code, description, uom or None, opening, location))',
       'items.append(Item(code, description, uom or None, opening, location,\n                          _clean(_get(row, mapping.get("old_code"))) or None))',
       'import row parsing')
s += '\n\n# v1.0.93: do not silently duplicate a renamed Inventory Code.\n'
s += 'from inventory_code_rename_v1093 import preview, apply\n'
put('inventory_import_v1089.py',s)

# Preview continues to allow Update & Add, but marks Rename and any conflicts
# BEFORE the confirmation; target collisions cannot write wrong history.
s=get('inventory_import_ui_v1089.py')
s=once(s, 'for name in ("New", "Update", "Unchanged", "MTO conflict")',
       'for name in ("New", "Update", "Rename", "Unchanged", "Conflict", "MTO conflict")',
       'import preview total options')
s=once(s,'f"Update: {totals[\'Update\']}    Unchanged: {totals[\'Unchanged\']}    "',
       'f"Update: {totals[\'Update\']}    Rename: {totals[\'Rename\']}    "\n        f"Unchanged: {totals[\'Unchanged\']}    Conflicts: {totals[\'Conflict\']}    "',
       'preview totals label')
s=once(s, 'columns = ("Action", "Code", "Description", "UOM", "Opening Balance")',
       'columns = ("Action", "Code", "Description", "UOM", "Opening Balance", "Old Code / Conflict")',
       'preview columns')
s=once(s,'for column, width in zip(columns, (125, 150, 390, 115, 135)):',
       'for column, width in zip(columns, (100, 120, 240, 90, 115, 235)):',
       'preview column widths')
s=once(s,'for item, action, _ in changes:', 'for item, action, source in changes:', 'preview row source')
s=once(s, 'item.opening if item.opening is not None else "(keep/0)"))',
       'item.opening if item.opening is not None else "(keep/0)",\n            source if action in ("Rename", "Conflict", "MTO conflict") else ""))',
       'preview source values')
s=once(s,
       'warning = "MTO conflict found - remove conflicting rows before import." if totals["MTO conflict"] else (',
       'warning = "Code collision found: assign an unused code to the existing item, then retry. No changes will be made." if (totals["Conflict"] or totals["MTO conflict"]) else (',
       'preview collision warning')
s=once(s,
       'f"Add {totals[\'New\']} new codes and update {totals[\'Update\']} existing codes?\\n"',
       'f"Add {totals[\'New\']} new, update {totals[\'Update\']}, and rename {totals[\'Rename\']} existing codes?\\n"',
       'import confirmation')
s=once(s,
       'f"New codes: {result[\'new\']}   Updated: {result[\'updated\']}   "',
       'f"New codes: {result[\'new\']}   Updated: {result[\'updated\']}   Renamed: {result[\'renamed\']}   "',
       'import result summary')
s=once(s,
       'state="disabled" if totals["MTO conflict"] else "normal"',
       'state="disabled" if (totals["MTO conflict"] or totals["Conflict"]) else "normal"',
       'preview import disabled for collision')
put('inventory_import_ui_v1089.py',s)

s=get('store_inventory.py')
start=s.index('    def inventory_codes(self):')
end=s.index('\n    def open_mto_inventory_flow(',start)
classic=s[start:end]
needle='''                        for table in ("demand_lines","grr_lines","issue_lines","transactions"):
                            try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
                            except Exception:pass
'''
classic=once(classic,needle,
             '''                        from inventory_code_rename_v1093 import relink_transactions
                        relink_transactions(self.conn, oldcode, code)
''',
             'Inventory Codes Edit: move all transactions without ignoring errors')
s=s[:start]+classic+s[end:]

start=s.index('    def _open_code_opening_detail(')
end=s.index('\n    def _mto_new_item_dialog(',start)
opening=s[start:end]
anchor='''                    action = "updated"
                else:
'''
opening=once(opening,anchor,
   '''                    action = "updated"
                    if dest == "Inventory Codes" and old != c:
                        from inventory_code_rename_v1093 import relink_transactions
                        relink_transactions(self.conn, old, c)
                else:
''',
   'Code Opening Edit: move associated transactions before committing')
s=s[:start]+opening+s[end:]
put('store_inventory.py',s)
print('v1.0.93: safe manual and Excel/PDF item-code renames with linked history, explicit old code support and collision preview')
