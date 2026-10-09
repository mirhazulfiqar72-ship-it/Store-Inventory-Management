"""Regression tests for v1.0.93 code changes, never touch live Firebase."""
from pathlib import Path
import os
import sqlite3
import tempfile
import unittest
import sys
# Always exercise the PATCHED source used by the Windows EXE, never root originals.
sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
import inventory_import_v1089 as importer
from inventory_code_rename_v1093 import REFERENCE_TABLES, relink_transactions


class RenameTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.conn = sqlite3.connect(":memory:")
        self.addCleanup(self.conn.close)
        self.conn.execute("""CREATE TABLE items(
            id INTEGER PRIMARY KEY, code TEXT UNIQUE, description TEXT, uom TEXT,
            opening_qty REAL, category TEXT, min_level REAL,
            item_type TEXT, mto_opening_qty REAL)""")
        self.conn.execute("CREATE TABLE mto_items(code TEXT PRIMARY KEY)")
        self.conn.executemany(
            "INSERT INTO items(code,description,uom,opening_qty,category,min_level,item_type,mto_opening_qty) "
            "VALUES(?,?,?,?,?,?,?,?)", [
                ("01-01-0024","Ball Bearing 51113","Number",4,"",0,"Local",0),
                ("01-01-0017","Ball Bearing 6201","Number",8,"",0,"Local",0)])
        for table in REFERENCE_TABLES:
            self.conn.execute(
                f"CREATE TABLE {table}(id INTEGER PRIMARY KEY, code TEXT, item_type TEXT DEFAULT 'Local', qty REAL)")
            self.conn.execute(f"INSERT INTO {table}(code,item_type,qty) VALUES(?,?,?)",
                              ("01-01-0024","Local",4))
            self.conn.execute(f"INSERT INTO {table}(code,item_type,qty) VALUES(?,?,?)",
                              ("01-01-0024","MTO",99))
        self.conn.commit()

    def item(self,code,desc="Ball Bearing 51113",old_code=None):
        return importer.Item(code,desc,"Number",4,"Sheet1!2",old_code)

    def test_collision_occupied_new_code_preserves_both_and_history(self):
        items=[self.item("01-01-0017")]
        changes=importer.preview(self.conn, items)
        self.assertEqual(changes[0][1],"Conflict")
        self.assertIn("Ball Bearing 6201", changes[0][2])
        with self.assertRaisesRegex(ValueError,"blocked"):
            importer.apply(self.conn,items,self.tmp.name)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM items").fetchone()[0],2)
        self.assertEqual(self.conn.execute(
            "SELECT count(*) FROM demand_lines WHERE code='01-01-0024'").fetchone()[0],2)

    def test_free_new_code_inferred_rename_moves_transaction_history(self):
        target="01-01-0300"
        self.assertEqual(importer.preview(self.conn,[self.item(target)])[0][1],"Rename")
        result=importer.apply(self.conn,[self.item(target)],self.tmp.name)
        self.assertEqual(result["renamed"],1)
        self.assertTrue(Path(result["backup"]).exists())
        self.assertEqual(self.conn.execute(
            "SELECT count(*) FROM items WHERE code='01-01-0024'").fetchone()[0],0)
        self.assertEqual(self.conn.execute(
            "SELECT description FROM items WHERE code=?", (target,)).fetchone()[0],"Ball Bearing 51113")
        for table in REFERENCE_TABLES:
            self.assertEqual(self.conn.execute(
                f"SELECT code FROM {table} WHERE item_type='Local'").fetchone()[0],target)
            self.assertEqual(self.conn.execute(
                f"SELECT code FROM {table} WHERE item_type='MTO'").fetchone()[0],"01-01-0024")
        self.assertEqual(importer.preview(self.conn,[self.item(target)])[0][1],"Unchanged")

    def test_explicit_old_item_code_from_csv(self):
        file=os.path.join(self.tmp.name,"codes.csv")
        Path(file).write_text(
            "Old Item Code,Item Code,Description,UOM,Opening Balance\n"
            "01-01-0024,01-01-0301,Ball Bearing 51113,Number,4\n",
            encoding="utf-8")
        incoming=importer.read_file(file)
        self.assertEqual(incoming[0].old_code,"01-01-0024")
        self.assertEqual(importer.preview(self.conn,incoming)[0][1],"Rename")
        self.assertEqual(importer.apply(self.conn,incoming,self.tmp.name)["renamed"],1)

    def test_manual_relink_local_only(self):
        with self.conn:
            self.conn.execute("UPDATE items SET code='01-01-0302' WHERE code='01-01-0024'")
            moved=relink_transactions(self.conn,"01-01-0024","01-01-0302")
        self.assertEqual(set(moved),set(REFERENCE_TABLES))
        for table in REFERENCE_TABLES:
            self.assertEqual(self.conn.execute(
                f"SELECT code FROM {table} WHERE item_type='Local'").fetchone()[0],"01-01-0302")
            self.assertEqual(self.conn.execute(
                f"SELECT code FROM {table} WHERE item_type='MTO'").fetchone()[0],"01-01-0024")

    def test_shared_descriptions_do_not_rename_existing_item(self):
        # Real inventory includes different codes sharing the same description.
        self.conn.execute(
            "INSERT INTO items(code,description,uom,opening_qty,category,min_level,item_type,mto_opening_qty) "
            "VALUES(?,?,?,?,?,?,?,?)",
            ("01-01-0008","Ball Bearing 6201","Number",5,"",0,"Local",0))
        self.conn.commit()
        incoming=[self.item("01-01-0017","Ball Bearing 6201")]
        self.assertIn(importer.preview(self.conn,incoming)[0][1],("Unchanged","Update"))
        self.assertEqual(importer.apply(self.conn,incoming,self.tmp.name)["renamed"],0)
        self.assertEqual(self.conn.execute(
            "SELECT COUNT(*) FROM items WHERE description='Ball Bearing 6201'").fetchone()[0],2)

    def test_other_codes_remain_unchanged(self):
        extra=[self.item("01-01-0300"),importer.Item("01-05-0100","New item","Number",2,"Sheet!3")]
        result=importer.apply(self.conn,extra,self.tmp.name)
        self.assertEqual((result["renamed"],result["new"]),(1,1))
        self.assertEqual(self.conn.execute("SELECT description FROM items WHERE code='01-01-0017'").fetchone()[0],"Ball Bearing 6201")


if __name__=="__main__":
    unittest.main()
