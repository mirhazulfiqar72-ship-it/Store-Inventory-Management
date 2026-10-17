"""v1.0.94 regression tests; fake network only, no live Firebase writes."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
import inventory_online_v1094 as fix


class MockResponse:
    def __init__(self, data):
        self.data = deepcopy(data)
    def json(self):
        return deepcopy(self.data)


class MockSync:
    def __init__(self, store, temp_dir):
        self.remote = store
        self.state_path = str(Path(temp_dir) / "state_v2.json")
        self.pending_path = str(Path(temp_dir) / "pending_v2.json")
        self.remote_cache_path = str(Path(temp_dir) / "cache_v2.json")
        self.timeout = 2.5
        self.enabled = True
        self.saved = {}
        self.locked = False
        self.pending_error = None
        self.pending_base = None
        self.initialized = 0

    def _get_snapshot(self):
        return deepcopy(self.remote.get("store_inventory_v2/data"))

    def _request(self, method, path, **kwargs):
        assert method in {"GET", "PUT"}, (method, path)
        path = path.removesuffix(".json")
        if method == "GET":
            return MockResponse(self.remote.get(path))
        self.remote[path] = deepcopy(kwargs["json"])
        return MockResponse(self.remote[path])

    def _try_acquire_lock(self, token):
        if self.locked:
            return False
        self.locked = True
        return True

    def _release_lock(self, token):
        self.locked = False

    def _load_json(self, path):
        return deepcopy(self.saved.get(path))

    def _save_state(self, data):
        self.saved[self.state_path] = deepcopy(data)

    def _clear_pending(self):
        self.saved.pop(self.pending_path, None)

    def replace_local(self, conn, snapshot):
        for table, data in snapshot["tables"].items():
            columns = [c[1] for c in conn.execute('PRAGMA table_info("' + table + '")')]
            conn.execute('DELETE FROM "' + table + '"')
            for row in data["rows"]:
                keep = [c for c in columns if c in row]
                conn.execute('INSERT INTO "' + table + '"(' + ",".join(keep)
                             + ') VALUES (' + ",".join("?" for _ in keep) + ')',
                             tuple(row[c] for c in keep))
        conn.commit()

    def initialize(self, conn):
        if self.locked:
            raise AssertionError("Attempted a nested Firebase lock")
        self.initialized += 1


def make_db():
    conn = sqlite3.connect(":memory:")
    schemas = {
        "items": "code TEXT PRIMARY KEY,description TEXT,uom TEXT,category TEXT,opening_qty REAL,min_level REAL,item_type TEXT,mto_opening_qty REAL",
        "mto_items": "code TEXT PRIMARY KEY,description TEXT",
        "parties": "id INTEGER PRIMARY KEY,name TEXT",
        "users": "username TEXT PRIMARY KEY,password TEXT,role TEXT",
        "demands": "demand_no TEXT PRIMARY KEY",
        "demand_lines": "id INTEGER PRIMARY KEY,code TEXT",
        "grr": "grr_no TEXT PRIMARY KEY",
        "grr_lines": "id INTEGER PRIMARY KEY,code TEXT",
        "issues": "issue_no TEXT PRIMARY KEY",
        "issue_lines": "id INTEGER PRIMARY KEY,code TEXT",
        "transactions": "id INTEGER PRIMARY KEY,code TEXT",
    }
    for name, schema in schemas.items():
        conn.execute(f'CREATE TABLE {name}({schema})')
    conn.execute("INSERT INTO parties(id,name) VALUES(1,'Keep Party')")
    conn.execute("INSERT INTO users(username,password,role) VALUES('admin','hash','Admin')")
    conn.execute("INSERT INTO mto_items(code,description) VALUES('MTO-001','Keep MTO')")
    for i in range(2480):
        conn.execute(
            "INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) "
            "VALUES(?,?,?,?,?,?,?,?)", (f"OLD-{i:05}",f"Legacy {i}","Number","",0,0,"Local",0))
    conn.execute("INSERT INTO demands(demand_no) VALUES('OLD-DEMAND')")
    conn.execute("INSERT INTO grr(grr_no) VALUES('OLD-GRR')")
    conn.execute("INSERT INTO issues(issue_no) VALUES('OLD-ISSUE')")
    conn.execute("INSERT INTO transactions(id,code) VALUES(1,'OLD-00001')")
    conn.commit()
    return conn


def cloud_from_db(conn):
    from firebase_sync import snapshot_db
    result = snapshot_db(conn)
    result.pop("clean_inventory_namespace", None)
    return result


class CleanCloudTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.conn = make_db()
        self.addCleanup(self.conn.close)
        self.initial = cloud_from_db(self.conn)
        self.store = {"store_inventory/data": deepcopy(self.initial)}
        self.sync = MockSync(self.store, self.temp.name)
        self.csv = str(Path(__file__).with_name("inventory_codes_102.csv"))
        # Prevent tests from writing recovery files into the CI machine.
        self.durable_patch = patch("durable_local.save", return_value=True)
        self.durable_patch.start()
        self.addCleanup(self.durable_patch.stop)

    def run_clean(self):
        return fix.ensure_clean_online(
            self.conn, self.sync, self.csv, self.temp.name)

    def test_first_migration_is_102_and_legacy_unmodified(self):
        self.assertTrue(self.run_clean())
        snapshot = self.store["store_inventory_v2/data"]
        self.assertEqual(snapshot["clean_inventory_namespace"],fix.MARKER)
        self.assertEqual(len(snapshot["tables"]["items"]["rows"]),102)
        self.assertEqual(len(self.store["store_inventory/data"]["tables"]["items"]["rows"]),2480)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM items").fetchone()[0],102)
        for table in fix.DOCUMENTS:
            self.assertEqual(len(snapshot["tables"][table]["rows"]),0)
        self.assertEqual(len(snapshot["tables"]["parties"]["rows"]),1)
        self.assertEqual(len(snapshot["tables"]["mto_items"]["rows"]),1)
        self.assertEqual(len(snapshot["tables"]["users"]["rows"]),1)
        self.assertTrue(list(Path(self.temp.name).glob("legacy_cloud_before_v1094_*.json")))
        self.assertTrue(list(Path(self.temp.name).glob("before_online_clean_v1094_*.db")))

    def test_older_pc_cannot_republish_2480_into_clean_namespace(self):
        self.run_clean()
        self.store["store_inventory/data"]["tables"]["items"]["rows"].extend(
            [{"code":"OLD-EXTRA","description":"Old PC republished"}])
        self.assertTrue(self.run_clean())
        self.assertEqual(self.conn.execute("SELECT count(*) FROM items").fetchone()[0],102)
        self.assertEqual(len(self.store["store_inventory_v2/data"]["tables"]["items"]["rows"]),102)

    def test_second_laptop_with_stale_legacy_cache_is_reset_from_v2(self):
        self.run_clean()
        second = make_db()
        self.addCleanup(second.close)
        new_sync = MockSync(self.store, self.temp.name)
        self.assertTrue(fix.ensure_clean_online(second,new_sync,self.csv,self.temp.name))
        self.assertEqual(second.execute("SELECT count(*) FROM items").fetchone()[0],102)
        self.assertEqual(len(self.store["store_inventory/data"]["tables"]["items"]["rows"]),2480)

    def test_legitimate_new_code_in_v2_is_preserved(self):
        self.run_clean()
        self.store["store_inventory_v2/data"]["tables"]["items"]["rows"].append({
            "code":"NEW-0123","description":"New Inventory Code",
            "uom":"Number","category":"","opening_qty":1,"min_level":0,
            "item_type":"Local","mto_opening_qty":0})
        self.run_clean()
        self.assertEqual(self.conn.execute("SELECT count(*) FROM items").fetchone()[0],103)
        self.assertIsNotNone(self.conn.execute(
            "SELECT code FROM items WHERE code='NEW-0123'").fetchone())

    def test_v2_offline_pending_merges_only_after_unlock(self):
        self.run_clean()
        base = self.sync._load_json(self.sync.state_path)
        self.sync.saved[self.sync.pending_path] = {
            "snapshot":deepcopy(base),"baseline":deepcopy(base)}
        self.run_clean()
        self.assertEqual(self.sync.initialized,1)
        self.assertFalse(self.sync.locked)

    def test_first_start_offline_fails_safely(self):
        self.sync.enabled = False
        with self.assertRaisesRegex(RuntimeError,"Internet"):
            self.run_clean()
        self.assertEqual(self.conn.execute("SELECT count(*) FROM items").fetchone()[0],2480)
        self.assertIsNone(self.store.get("store_inventory_v2/data"))

    def test_v2_offline_reuses_current_clean_cache(self):
        self.run_clean()
        self.sync.enabled = False
        self.assertFalse(self.run_clean())
        self.assertEqual(self.conn.execute("SELECT count(*) FROM items").fetchone()[0],102)


if __name__ == "__main__":
    unittest.main()
