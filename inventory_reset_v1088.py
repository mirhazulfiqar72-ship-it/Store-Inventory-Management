"""One-time Firebase-authoritative reset for Store Inventory Management v1.0.88.

Backs up original cloud and SQLite data before changing anything. Keeps MTO,
parties and users, while replacing local Inventory Codes and clearing document
records and their transactions. Migration is idempotent across online clients.
"""
from __future__ import annotations
import csv
from copy import deepcopy
from datetime import datetime
import json
import os
import sqlite3
import tempfile
import time
import uuid

RESET_ID = "inventory-102-reset-v1.0.88"
CLEAR_TABLES = ("demands", "demand_lines", "grr", "grr_lines", "issues", "issue_lines", "transactions")
EXPECTED_ROWS = 102


def read_codes(path):
    with open(path, encoding="utf-8-sig", newline="") as fp:
        rows = list(csv.DictReader(fp))
    required = {"Item Code", "Description", "UOM", "Opening Balance"}
    if not rows or not required.issubset(rows[0]):
        raise RuntimeError("Inventory reset file has missing columns")
    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError("Inventory reset requires exactly 102 item codes")
    codes, used = [], set()
    for row in rows:
        code = row["Item Code"].strip()
        desc = row["Description"].strip()
        uom = row["UOM"].strip()
        if not code or not desc or not uom or code.casefold() in used:
            raise RuntimeError("Invalid or duplicate item code: " + code)
        try:
            qty = float(row["Opening Balance"] or "0")
        except ValueError as exc:
            raise RuntimeError("Invalid opening balance for: " + code) from exc
        if qty < 0 or qty != qty or qty == float("inf"):
            raise RuntimeError("Invalid opening balance for: " + code)
        used.add(code.casefold())
        codes.append((code, desc, uom, qty))
    return codes


def migrate_snapshot(snapshot, codes):
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("tables"), dict):
        raise RuntimeError("Firebase inventory snapshot missing: refused to reset")
    if snapshot.get("inventory_reset_id") == RESET_ID:
        return deepcopy(snapshot)
    tables = snapshot["tables"]
    for name in ("items", "mto_items", "parties", "users", *CLEAR_TABLES):
        if name not in tables or not isinstance(tables[name], dict) or "rows" not in tables[name]:
            raise RuntimeError("Firebase inventory table missing: " + name)
    result = deepcopy(snapshot)
    old_items = tables["items"]["rows"]
    mto = [deepcopy(row) for row in old_items
           if str(row.get("item_type") or "Local").strip().upper() == "MTO"]
    mto_keys = {str(row.get("code") or "").casefold() for row in mto}
    conflicts = mto_keys.intersection(code.casefold() for code, *_ in codes)
    if conflicts:
        raise RuntimeError("MTO code conflict; no data changed: " + ", ".join(sorted(conflicts)))
    result["tables"]["items"]["rows"] = mto + [
        dict(code=code, description=desc, uom=uom, category="",
             opening_qty=qty, min_level=0, item_type="Local", mto_opening_qty=0)
        for code, desc, uom, qty in codes
    ]
    for table in CLEAR_TABLES:
        result["tables"][table]["rows"] = []
    result["inventory_reset_id"] = RESET_ID
    return result


def _write_backup_json(snapshot, backup_dir):
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target = os.path.join(backup_dir, f"pre_inventory_reset_v1088_{stamp}.json")
    fd, temporary = tempfile.mkstemp(dir=backup_dir, prefix=".inventory_reset_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(snapshot, file, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def _backup_sqlite(conn, backup_dir):
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target = os.path.join(backup_dir, f"pre_inventory_reset_v1088_{stamp}.db")
    output = sqlite3.connect(target)
    try:
        conn.backup(output)
    finally:
        output.close()
    return target


def apply_reset(conn, sync, csv_path, backup_dir):
    """Replaces cloud data once, then aligns local DB and pending sync state."""
    state = sync._load_json(sync.state_path)
    if isinstance(state, dict) and state.get("inventory_reset_id") == RESET_ID:
        return False
    if not sync.enabled:
        raise RuntimeError("v1.0.88 inventory reset requires Firebase and Internet access")
    codes = read_codes(csv_path)
    old_timeout = sync.timeout
    sync.timeout = max(old_timeout, 20.0)
    token = f"reset-v1088-{uuid.uuid4().hex}"
    locked = False
    try:
        for _ in range(12):
            if sync._try_acquire_lock(token):
                locked = True
                break
            time.sleep(0.5)
        if not locked:
            raise RuntimeError("Firebase is busy; reopen app to retry reset")
        url = f"{sync.base_url}/store_inventory/data.json"
        response = sync.session.get(
            url, headers={"X-Firebase-ETag": "true"}, timeout=sync.timeout)
        response.raise_for_status()
        current = response.json()
        if not isinstance(current, dict):
            raise RuntimeError("Firebase snapshot missing; reset cancelled")
        old_etag = response.headers.get("ETag")
        if not old_etag:
            raise RuntimeError("Firebase did not supply an ETag; reset cancelled")
        already_done = current.get("inventory_reset_id") == RESET_ID
        if already_done:
            updated = current
        else:
            updated = migrate_snapshot(current, codes)
            # Both backups complete BEFORE changing cloud contents.
            _write_backup_json(current, backup_dir)
            _backup_sqlite(conn, backup_dir)
            uploaded = sync.session.put(
                url, json=updated,
                headers={"if-match": old_etag, "content-type": "application/json"},
                timeout=sync.timeout)
            if uploaded.status_code == 412:
                raise RuntimeError("Firebase changed during reset; reopen app to retry")
            uploaded.raise_for_status()
            sync._request("PUT", "store_inventory/_meta/version.json",
                          json=f"{time.time_ns()}-v1088-reset")
        # Prevent re-upload of the pre-reset 2437 codes or saved documents.
        sync.replace_local(conn, updated)
        sync._atomic_save_json(sync.state_path, updated)
        sync._clear_pending()
        sync.pending_base = None
        sync.pending_error = None
        try:
            os.unlink(sync.remote_cache_path)
        except FileNotFoundError:
            pass
        import durable_local
        durable_local.save(conn)
        return not already_done
    finally:
        if locked:
            sync._release_lock(token)
        sync.timeout = old_timeout
