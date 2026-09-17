import os
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
import storage_lock
import durable_local

storage_lock.install()
base = storage_lock.DATA_DIR
base.mkdir(parents=True, exist_ok=True)
db = base / "journal_debug.db"
try: db.unlink()
except OSError: pass
c = sqlite3.connect(str(db))
c.execute("CREATE TABLE items(code TEXT)")
c.execute("INSERT INTO items VALUES (?)", ("JOURNAL-OK",))
c.commit()
print("snapshot before save:", durable_local.snapshot(c))
print("save result:", durable_local.save(c), "error:", durable_local.LAST_ERROR)
print("snapshot file:", durable_local.SNAPSHOT_PATH, durable_local.SNAPSHOT_PATH.exists(), durable_local.SNAPSHOT_PATH.stat().st_size if durable_local.SNAPSHOT_PATH.exists() else 0)
print("loaded rows:", sum(len(v.get("rows", [])) for v in (durable_local.load() or {}).get("tables", {}).values()))
c.execute("DELETE FROM items")
c.commit()
print("current rows after delete:", c.execute("SELECT COUNT(*) FROM items").fetchone()[0])
print("restore result:", durable_local.restore_if_newer(c), "error:", durable_local.LAST_ERROR)
print("rows after restore:", c.execute("SELECT code FROM items").fetchall())
c.close()
try: db.unlink()
except OSError: pass
