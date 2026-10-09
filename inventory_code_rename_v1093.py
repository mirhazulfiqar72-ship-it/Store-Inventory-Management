"""Safe Inventory Code rename / import helpers for Store Inventory v1.0.93.

No database schema, MTO data, GRN numbers or transaction amounts are changed.
Move only item-code references belonging to the renamed Inventory Codes item.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
import os
import sqlite3

REFERENCE_TABLES = ("demand_lines", "grr_lines", "issue_lines", "transactions")


def normalized_description(value):
    return " ".join(str(value or "").split()).casefold()


def _columns(conn, table):
    return {str(row[1]).lower() for row in conn.execute(f'PRAGMA table_info("{table}")')}


def relink_transactions(conn, old_code, new_code, *, destination="Inventory Codes"):
    """Relink item-code references inside the surrounding SQLite transaction.

    Raises if a required table/column cannot be updated. No silent partial moves.
    """
    old_code, new_code = str(old_code).strip(), str(new_code).strip()
    if not old_code or not new_code:
        raise ValueError("An existing code and a new code are required")
    if old_code.casefold() == new_code.casefold():
        return {}
    is_mto = str(destination).strip().casefold() == "mto inventory"
    results = {}
    for table in REFERENCE_TABLES:
        cols = _columns(conn, table)
        if "code" not in cols:
            raise RuntimeError(f"Cannot safely rename: {table}.code is missing")
        where = 'LOWER(TRIM("code"))=LOWER(TRIM(?))'
        if "item_type" in cols:
            if is_mto:
                where += " AND UPPER(TRIM(COALESCE(item_type,'')))='MTO'"
            else:
                where += " AND UPPER(TRIM(COALESCE(item_type,'')))!='MTO'"
        elif is_mto:
            # An untyped legacy row cannot reliably be attributed to MTO.
            continue
        cursor = conn.execute(f'UPDATE "{table}" SET "code"=? WHERE {where}',
                              (new_code, old_code))
        results[table] = cursor.rowcount
    return results


def preview(conn, imports):
    """Return [(Item, action, prior_code_or_conflict_reason)].

    A changed item code is inferred only from a unique existing Description,
    or from an explicit Old Item Code column. Conflicting codes never overwrite
    another distinct item's record/history.
    """
    records = list(conn.execute(
        "SELECT code,description,uom,opening_qty,item_type FROM items"))
    by_code = {str(row[0]).strip().casefold(): row for row in records}
    by_description = defaultdict(list)
    for row in records:
        by_description[normalized_description(row[1])].append(row)
    try:
        mto_codes = {str(row[0]).strip().casefold()
                     for row in conn.execute("SELECT code FROM mto_items")}
    except sqlite3.OperationalError:
        mto_codes = set()

    result = []
    source_consumers = defaultdict(list)
    for item in imports:
        new_key = item.code.strip().casefold()
        current = by_code.get(new_key)
        prior = str(getattr(item, "old_code", None) or "").strip()
        desired = normalized_description(item.description)
        matches = [row for row in by_description.get(desired, [])
                   if str(row[0]).strip().casefold() != new_key]
        conflict = None
        source = None
        if new_key in mto_codes or (current and str(current[4] or "").upper() == "MTO"):
            conflict = "MTO code is protected"
        elif prior:
            source = by_code.get(prior.casefold())
            if prior.casefold() != new_key and source is None:
                if current and normalized_description(current[1]) == desired:
                    prior = ""
                else:
                    conflict = f"Old code {prior} not found"
            if source and str(source[4] or "").upper() == "MTO":
                conflict = "MTO source is protected"
        elif len(matches) > 1:
            conflict = "Description matches multiple existing codes"
        elif len(matches) == 1:
            source = matches[0]

        if conflict:
            result.append((item, "Conflict", conflict if conflict != "MTO code is protected" else "MTO conflict"))
            continue
        if source is not None and str(source[0]).strip().casefold() != new_key:
            if current is not None:
                result.append((item, "Conflict", f"{item.code} belongs to {current[1]}"))
                continue
            old_code = str(source[0])
            source_consumers[old_code.casefold()].append(len(result))
            result.append((item, "Rename", old_code))
            continue
        if current is None:
            result.append((item, "New", item.code))
        elif (normalized_description(current[1]) == desired
              and (item.uom is None or (current[2] or "") == item.uom)
              and (item.opening is None or abs(float(current[3] or 0) - item.opening) < 1e-10)):
            result.append((item, "Unchanged", current[0]))
        else:
            if matches:
                result.append((item, "Conflict", f"Description belongs to {matches[0][0]}"))
            else:
                result.append((item, "Update", current[0]))
    for old_key, indexes in source_consumers.items():
        if len(indexes) > 1:
            for index in indexes:
                item, _, _ = result[index]
                result[index] = (item, "Conflict", f"Old code {old_key} maps to multiple new codes")
    renames = {str(source).casefold() for _, action, source in result if action == "Rename"}
    for index, (item, action, source) in enumerate(result):
        if item.code.strip().casefold() in renames and action != "Rename":
            result[index] = (item, "Conflict", "This code is being renamed in another row")
    return result


def apply(conn, imports, backup_dir):
    """Update/Add and rename codes atomically, retaining old transaction history."""
    changes = preview(conn, imports)
    if not changes:
        raise ValueError("No rows to import")
    bad = [(item, action, info) for item, action, info in changes
           if action in ("Conflict", "MTO conflict")]
    if bad:
        details = "; ".join(f"{item.code}: {reason}" for item, _, reason in bad[:5])
        raise ValueError("Import blocked to prevent duplicate/wrong transactions: " + details)
    os.makedirs(backup_dir, exist_ok=True)
    backup = os.path.join(backup_dir, "inventory_before_code_change_" +
                          datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".db")
    dest = sqlite3.connect(backup)
    try:
        getattr(conn, "_conn", conn).backup(dest)
    finally:
        dest.close()
    stats = {"new": 0, "updated": 0, "renamed": 0, "unchanged": 0, "backup": backup}
    try:
        for item, action, prior in changes:
            if action == "Unchanged":
                stats["unchanged"] += 1
                continue
            if action == "New":
                conn.execute(
                    "INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (item.code, item.description, item.uom or "Number", "",
                     item.opening if item.opening is not None else 0, 0, "Local", 0))
                stats["new"] += 1
            elif action == "Update":
                previous = conn.execute(
                    "SELECT uom,opening_qty FROM items WHERE code=?", (prior,)).fetchone()
                if not previous:
                    raise RuntimeError(f"Code {prior} changed during import; retry")
                conn.execute("UPDATE items SET description=?,uom=?,opening_qty=? WHERE code=?",
                             (item.description,
                              item.uom if item.uom is not None else previous[0],
                              item.opening if item.opening is not None else previous[1],
                              prior))
                stats["updated"] += 1
            elif action == "Rename":
                previous = conn.execute(
                    "SELECT uom,opening_qty FROM items WHERE code=?", (prior,)).fetchone()
                if not previous:
                    raise RuntimeError(f"Old code {prior} changed during import; retry")
                conn.execute("UPDATE items SET code=?,description=?,uom=?,opening_qty=? WHERE code=?",
                             (item.code, item.description,
                              item.uom if item.uom is not None else previous[0],
                              item.opening if item.opening is not None else previous[1], prior))
                relink_transactions(conn, prior, item.code)
                stats["renamed"] += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    stats["online_pending"] = bool(getattr(getattr(conn, "sync", None), "pending_error", None))
    return stats
