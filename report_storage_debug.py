import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
import storage_lock
storage_lock.install()
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

reports = storage_lock.REPORTS_DIR
reports.mkdir(parents=True, exist_ok=True)
pdf = reports / "__ci_report_write_test.pdf"
if pdf.exists():
    pdf.unlink()
c = canvas.Canvas(str(pdf), pagesize=A4)
c.drawString(72, 780, "Store Inventory report write test")
c.save()
assert pdf.exists() and pdf.stat().st_size > 0, pdf
with pdf.open("rb") as f:
    assert f.read(5) == b"%PDF-", "invalid PDF signature"
pdf.unlink()
print("ReportLab -> Reports folder: OK", reports)
