"""Automated regression tests for v1.0.89 import; no live Firebase writes."""
from pathlib import Path
import os
import sqlite3
import tempfile
import unittest
import inventory_import_v1089 as engine

class InventoryImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.conn = sqlite3.connect(":memory:")
        self.addCleanup(self.conn.close)
        self.conn.execute("""
            CREATE TABLE items(
                code TEXT PRIMARY KEY,description TEXT,uom TEXT,category TEXT,
                opening_qty REAL,min_level REAL,item_type TEXT,mto_opening_qty REAL)""")
        self.conn.execute("CREATE TABLE mto_items(code TEXT PRIMARY KEY)")
        self.conn.execute("CREATE TABLE demands(demand_no TEXT PRIMARY KEY)")
        self.conn.execute("INSERT INTO demands VALUES('DEMAND-KEEP')")
        self.conn.execute("INSERT INTO items VALUES('01-01-0001','Old description','Number','',5,0,'Local',0)")
        self.conn.execute("INSERT INTO items VALUES('UNLISTED-OLD','Keep this','Pair','',7,0,'Local',0)")
        self.conn.execute("INSERT INTO items VALUES('MTO-CODE','MTO description','Pair','',0,0,'MTO',10)")
        self.conn.commit()

    def test_original_102_csv_parsed(self):
        p = Path(__file__).with_name("inventory_codes_102.csv")
        result = engine.read_file(str(p))
        self.assertEqual(len(result), 102)
        self.assertEqual(len({i.code.lower() for i in result}), 102)
        self.assertEqual(result[0].description, "Ball Bearing 608")

    def test_excel_update_add_and_keep_others(self):
        from openpyxl import Workbook
        file = os.path.join(self.temp.name, "sample.xlsx")
        wb = Workbook()
        sheet = wb.active
        sheet.append(["Serial", "Item Code", "Description", "UOM", "Opening Balance"])
        sheet.append([1, "01-01-0001", "Updated bearing", "Pair", 12])
        sheet.append([2, "CODE-NEW", "New bearing", "Number", 3])
        wb.save(file)
        imported = engine.read_file(file)
        changes = engine.preview(self.conn, imported)
        self.assertEqual([a for _, a, _ in changes], ["Update", "New"])
        result = engine.apply(self.conn, imported, self.temp.name)
        self.assertEqual((result["new"], result["updated"]), (1, 1))
        self.assertTrue(Path(result["backup"]).is_file())
        self.assertEqual(self.conn.execute("SELECT description,uom,opening_qty FROM items WHERE code='01-01-0001'").fetchone(),
                         ("Updated bearing", "Pair", 12))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items WHERE code='UNLISTED-OLD'").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM demands").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT mto_opening_qty FROM items WHERE code='MTO-CODE'").fetchone()[0], 10)
        result2 = engine.apply(self.conn, imported, self.temp.name)
        self.assertEqual(result2["unchanged"], 2)

    def test_mto_conflict_cancels_entire_import(self):
        data = [engine.Item("CODE-NEW","New item","Number",1,"Test!1"),
                engine.Item("MTO-CODE","Collision","Number",1,"Test!2")]
        with self.assertRaisesRegex(ValueError, "MTO"):
            engine.apply(self.conn, data, self.temp.name)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items WHERE code='CODE-NEW'").fetchone()[0], 0)

    def test_csv_duplicate_code_is_rejected(self):
        path = os.path.join(self.temp.name,"duplicates.csv")
        Path(path).write_text("Code,Description,UOM,Opening Bal\nAB-123,One,Pair,5\nAB-123,Two,Pair,6\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"duplicate"):
            engine.read_file(path)

    def test_searchable_pdf(self):
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib import colors
        path = os.path.join(self.temp.name, "codes.pdf")
        document = SimpleDocTemplate(path)
        table = Table([
            ["Item Code","Description","UOM","Opening Balance"],
            ["AA-1000","Sample PDF bearing","Pair","7"],
            ["AA-1001","Another PDF bearing","Number","12"],
        ], colWidths=[100,190,80,100])
        table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.6,colors.black)]))
        document.build([table])
        result = engine.read_file(path)
        self.assertEqual([x.code for x in result], ["AA-1000","AA-1001"])
        self.assertEqual(result[0].uom, "Pair")

if __name__ == "__main__":
    unittest.main()
