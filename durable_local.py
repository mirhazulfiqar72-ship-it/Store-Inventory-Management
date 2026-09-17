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
from pathlib import Path
from typing import Any, Dict

INSTALL_ROOT = Path(r"C:\StoreInventoryManagement")
DATA_DIR = INSTALL_ROOT / "Data"
SNAPSHOT_PATH = DATA_DIR / "local_data_snapshot.json"
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

def save(conn: sqlite3.Connection) -> bool:
    global LAST_ERROR
    LAST_ERROR = ""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        value = snapshot(conn)
        fd, tmp = tempfile.mkstemp(prefix="local_snapshot_", suffix=".tmp", dir=str(DATA_DIR))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, SNAPSHOT_PATH)
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
        return True
    except Exception as exc:
        LAST_ERROR = repr(exc)
        return False

def load() -> Dict[str, Any] | None:
    global LAST_ERROR
    try:
        if not SNAPSHOT_PATH.exists():
            return None
        value = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception as exc:
        LAST_ERROR = repr(exc)
        return None

def restore_if_newer(conn: sqlite3.Connection) -> bool:
    global LAST_ERROR
    LAST_ERROR = ""
    saved = load()
    if not saved or _row_count(saved) <= 0:
        return False
    current = snapshot(conn)
    if _row_count(current) >= _row_count(saved):
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
    except Exception as exc:
        LAST_ERROR = repr(exc)
        try:
            conn.rollback()
        except Exception:
            pass
        return False
