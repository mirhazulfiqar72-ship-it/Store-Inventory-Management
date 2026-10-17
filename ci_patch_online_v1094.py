"""Apply v1.0.94's online-isolation fix after all existing UI/data patches.

The Firebase DATABASE URL, UI screens, import functions and application data
schema do not change. Only the shared Firebase storage namespace and recovery
policy are changed; old namespace remains as a non-destructive archive.
"""
from pathlib import Path

root=Path(__file__).resolve().parent/"source"

def load(name):
    return (root/name).read_text(encoding="utf-8-sig")

def save(name, data):
    compile(data,name,"exec")
    (root/name).write_text(data,encoding="utf-8")

def one(text, old, new, name):
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f"{name} expected one source block; got {n}")
    return text.replace(old,new,1)

# Switch ALL runtime reads, writes, locks and background refreshes from v1 to
# v2. The original Firebase RTDB URL and request stack remain untouched.
sync=load("firebase_sync.py")
assert sync.count('store_inventory/') >= 7
sync=sync.replace("store_inventory/","store_inventory_v2/")
for filename in ("firebase_sync_state.json",
                 "firebase_pending_sync.json",
                 "firebase_remote_cache.json"):
    sync=one(sync, filename,
             filename.replace(".json","_v2.json"),
             "namespace-specific sync file")
sync=one(sync,
    'return {"schema": 1, "tables": tables}',
    'return {"schema": 1, "tables": tables, "clean_inventory_namespace": "isolated-inventory-102-v1.0.94"}',
    "snapshot epoch marker")
assert "store_inventory/data.json" not in sync
assert "store_inventory_v2/data.json" in sync
save("firebase_sync.py",sync)

# Suppress the old recovery heuristic after v2 sync has been activated.
# Previously it chose the snapshot with the MOST records, so a stale 2480-row
# backup could resurrect items deleted from the 102-code clean inventory.
durable=load("durable_local.py")
durable=one(durable,
    'return max(candidates, key=_row_count)',
    '''# Newest successfully written snapshot wins, never the largest obsolete one.
        return max(candidates, key=lambda value: value[1])[0]''',
    "snapshot preference")
# Change the collection to store the mtime along with each snapshot.
durable=one(durable,
    'candidates.append(value)',
    'candidates.append((value, path.stat().st_mtime_ns))',
    "snapshot mtime")
durable=one(durable,
    '    saved = load()\n    if not saved or _row_count(saved) <= 0:',
    '''    # A clean v2 cloud state is authoritative. Never restore an obsolete
    # v1 recovery snapshot, even if it contains thousands of extra rows.
    if (DATA_DIR / "firebase_sync_state_v2.json").is_file():
        return False
    saved = load()
    if not saved or _row_count(saved) <= 0:''',
    "old snapshot restoration")
save("durable_local.py",durable)

# Replace ONLY the original v1.0.88 reset hook. It ran against the old
# namespace and short-circuited whenever local reset marker existed,
# regardless of cloud having been repopulated by an old PC.
app=load("store_inventory.py")
app=one(app,
    '''    # v1.0.88: one-time cloud-authoritative Inventory Codes/document reset.
    from inventory_reset_v1088 import apply_reset
    apply_reset(raw, sync, resource_path("inventory_codes_102.csv"), BACKUP_DIR)
''',
    '''    # v1.0.94: preserve the legacy online data as an archive; use a clean
    # isolated namespace so older PCs cannot republish deleted codes.
    from inventory_online_v1094 import ensure_clean_online
    ensure_clean_online(raw, sync, resource_path("inventory_codes_102.csv"), BACKUP_DIR)
''',
    "old reset call")
assert "ensure_clean_online(raw, sync" in app
assert "apply_reset(raw, sync" not in app
save("store_inventory.py",app)

print("v1.0.94: Firebase isolated; 102-code online state authoritative; old backups cannot resurrect deleted records")
