"""Read-only online health counts for migration diagnostics; prints no record data."""
import json
from pathlib import Path
import requests

config = Path(__file__).resolve().parent / "source" / "firebase_database_url.txt"
url = next((line.strip().rstrip("/") for line in config.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.startswith("#")), "")
if not url.startswith("https://"):
    raise SystemExit("Cannot audit online counts: Firebase URL not configured")

for label, namespace in (("legacy", "store_inventory"),
                         ("clean", "store_inventory_v2")):
    try:
        response = requests.get(url + "/" + namespace + "/data.json", timeout=20)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            print(label + ": remote namespace not initialized")
            continue
        tables = data.get("tables") or {}
        counts = {name: len((tables.get(name) or {}).get("rows") or [])
                  for name in ("items", "mto_items", "demands", "grr", "issues", "transactions")}
        marker = "clean" if data.get("clean_inventory_namespace") == "isolated-inventory-102-v1.0.94" else "legacy/unknown"
        print(label + " online counts: " + json.dumps(counts, sort_keys=True)
              + " namespace_marker=" + marker)
    except Exception as error:
        print(label + ": online health check unavailable: " + type(error).__name__)
