"""Crash/restart-safe local snapshot for Store Inventory Management.

The SQLite database remains the live local cache. This small journal is an
additional safety net: every successful local commit is copied to a durable
JSON snapshot under C:\\StoreInventoryManagement\\Data before network sync.
It is only used to recover a database that is missing or unexpectedly empty;
it never deletes the SQLite database or user data.
"""
from __future__ import annotations
import json
import os
import sqlite3
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict

INSTALL_ROOT = Path(r"C:\StoreInventoryManagement")
DATA_DIR = INSTALL_ROOT / "Data"
SNAPSHOT_PATH = DATA_DIR / "local_data_snapshot.json"

# Secondary recovery copy lives outside the installation folder. This copy
# survives deletion/reinstallation of C:\StoreInventoryManagement; Firebase
# remains the primary online copy.
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
RECOVERY_DIR = LOCALAPPDATA / "StoreInventoryManagement" / "Recovery"
RECOVERY_SNAPSHOT_PATH = RECOVERY_DIR / "local_data_snapshot.json"
TABLES = (
    "items", "mto_items", "parties", "demands", "demand_lines", "grr", "grr_lines",
    "issues", "issue_lines", "transactions", "users",
)
LAST_ERROR = ""

def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]

def snapshot(conn: sqlite3.Connection) -> Dict[str, Any]:
    tables: Dict[str, Any] = {}
    for table in TABLES:
        cols = _columns(conn, table)
        rows = []
        if cols:
            for row in conn.execute(f"SELECT {','.join(cols)} FROM {table}").fetchall():
                rows.append({c: (v if v is None or isinstance(v, (str, int, float, bool)) else str(v))
                             for c, v in zip(cols, row)})
        tables[table] = {"columns": cols, "rows": rows}
    return {"schema": 1, "tables": tables}

def _row_count(s: Dict[str, Any]) -> int:
    return sum(len(v.get("rows", []) or []) for v in s.get("tables", {}).values())

def _has_more_business_data(saved: Dict[str, Any], current: Dict[str, Any]) -> bool:
    # Compare each table so seeded Inventory Codes cannot block recovery of
    # saved Demand/GRN/Issue/Party records after a reinstall.
    for table in TABLES:
        saved_n = len(saved.get("tables", {}).get(table, {}).get("rows", []) or [])
        current_n = len(current.get("tables", {}).get(table, {}).get("rows", []) or [])
        if saved_n > current_n:
            return True
    return False

def _atomic_write(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="local_snapshot_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass

def save(conn: sqlite3.Connection) -> bool:
    global LAST_ERROR
    LAST_ERROR = ""
    try:
        value = snapshot(conn)
        c_ok = False
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            _atomic_write(SNAPSHOT_PATH, value)
            c_ok = True
        except Exception:
            pass
        try:
            _atomic_write(RECOVERY_SNAPSHOT_PATH, value)
            recovery_ok = True
        except Exception:
            recovery_ok = False
        if not (c_ok or recovery_ok):
            raise IOError("Could not save the local recovery snapshot.")
        return True
    except Exception:
        LAST_ERROR = traceback.format_exc()
        return False

def load() -> Dict[str, Any] | None:
    global LAST_ERROR
    try:
        candidates = []
        # The C: snapshot is convenient for normal operation, while the
        # AppData recovery copy survives deletion/reinstallation of the
        # installation folder.
        for path in (SNAPSHOT_PATH, RECOVERY_SNAPSHOT_PATH):
            try:
                if path.exists():
                    value = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(value, dict):
                        candidates.append(value)
            except Exception:
                pass
        if not candidates:
            return None
        return max(candidates, key=_row_count)
    except Exception:
        LAST_ERROR = traceback.format_exc()
        return None

def restore_if_newer(conn: sqlite3.Connection) -> bool:
    global LAST_ERROR
    LAST_ERROR = ""
    saved = load()
    if not saved or _row_count(saved) <= 0:
        return False
    current = snapshot(conn)
    if not _has_more_business_data(saved, current):
        return False
    try:
        conn.execute("BEGIN")
        for table in TABLES:
            cols = _columns(conn, table)
            rows = saved.get("tables", {}).get(table, {}).get("rows", []) or []
            if not cols:
                continue
            conn.execute(f"DELETE FROM {table}")
            if not rows:
                continue
            insert_cols = [c for c in cols if c in rows[0]]
            if not insert_cols:
                continue
            placeholders = ",".join("?" for _ in insert_cols)
            sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
            for row in rows:
                conn.execute(sql, [row.get(c) for c in insert_cols])
        conn.commit()
        return True
    except Exception:
        LAST_ERROR = traceback.format_exc()
        try:
            conn.rollback()
        except Exception:
            pass
        return False
