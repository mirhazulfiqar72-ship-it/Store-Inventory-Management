"""Reliable Firebase Realtime Database synchronization for Store Inventory Management.

Uses only the Firebase Realtime Database URL (no API key).  Local SQLite is
always kept durable; Firebase synchronization is retried and failed writes
are journaled so an application restart cannot discard locally saved records.
"""
from __future__ import annotations
import json
import os
import sqlite3
import tempfile
import time
import uuid
from copy import deepcopy
from typing import Any, Dict, Iterable, Optional, Tuple
try:
    import requests
except Exception:
    requests = None
TABLES = (
    "items", "mto_items", "parties", "demands", "demand_lines", "grr", "grr_lines",
    "issues", "issue_lines", "transactions", "users",
)
def _safe_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
def snapshot_db(conn: sqlite3.Connection) -> Dict[str, Any]:
    tables: Dict[str, Any] = {}
    for table in TABLES:
        cols = _table_columns(conn, table)
        rows = []
        for row in conn.execute(f"SELECT {','.join(cols)} FROM {table}").fetchall():
            rows.append({col: _safe_json_value(row[i]) for i, col in enumerate(cols)})
        tables[table] = {"columns": cols, "rows": rows}
    return {"schema": 1, "tables": tables}
def _row_key(table: str, row: Dict[str, Any]) -> Tuple[str, Any]:
    if table in ("items", "mto_items", "demands", "grr", "issues", "users"):
        key = {"items": "code", "mto_items": "code", "demands": "demand_no", "grr": "grr_no", "issues": "issue_no", "users": "username"}[table]
        return key, row.get(key)
    return "id", row.get("id")
def _index_snapshot(snapshot: Dict[str, Any], table: str) -> Dict[Tuple[str, Any], Dict[str, Any]]:
    result = {}
    for row in snapshot.get("tables", {}).get(table, {}).get("rows", []) or []:
        result[_row_key(table, row)] = row
    return result
def merge_local_changes(remote: Dict[str, Any], baseline: Dict[str, Any], local: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(remote)
    merged.setdefault("schema", 1)
    merged.setdefault("tables", {})
    for table in TABLES:
        b_idx = _index_snapshot(baseline, table)
        l_idx = _index_snapshot(local, table)
        r_idx = _index_snapshot(remote, table)
        out = dict(r_idx)
        for key in set(b_idx) | set(l_idx):
            b, l = b_idx.get(key), l_idx.get(key)
            if l == b:
                continue
            if l is None:
                out.pop(key, None)
            else:
                out[key] = deepcopy(l)
        columns = (local.get("tables", {}).get(table, {}).get("columns") or
                   remote.get("tables", {}).get(table, {}).get("columns") or
                   baseline.get("tables", {}).get(table, {}).get("columns") or [])
        merged["tables"][table] = {"columns": columns, "rows": list(out.values())}
    return merged
def _snapshot_has_records(snapshot: Dict[str, Any]) -> bool:
    tables = snapshot.get("tables", {})
    return any(tables.get(x, {}).get("rows") for x in TABLES)
class FirebaseSync:
    def __init__(self, url_file: str, install_dir: str, timeout: int = 15):
        self.url_file = url_file
        self.install_dir = install_dir
        self.timeout = timeout
        self.base_url = self._read_url()
        self.enabled = bool(self.base_url and requests)
        self.last_remote_version: Optional[str] = None
        self.last_check = 0.0
        self.check_interval = 1.5
        self.pending_base: Optional[Dict[str, Any]] = None
        self.pending_error: Optional[str] = None
        self.session = requests.Session() if requests else None
        self.client_id = f"{os.environ.get('COMPUTERNAME','PC')}-{uuid.uuid4().hex[:10]}"
        data_dir = os.path.join(self.install_dir, "Data")
        os.makedirs(data_dir, exist_ok=True)
        self.state_path = os.path.join(data_dir, "firebase_sync_state.json")
        self.pending_path = os.path.join(data_dir, "firebase_pending_sync.json")
    def _read_url(self) -> str:
        try:
            with open(self.url_file, "r", encoding="utf-8-sig") as f:
                raw = f.read().strip().splitlines()
        except Exception:
            return ""
        for line in raw:
            line = line.strip()
            if line and not line.startswith("#"):
                return line.rstrip("/")
        return ""
    def status_text(self) -> str:
        if not self.enabled:
            return "Firebase URL not configured"
        if self.pending_error:
            return "Online database sync pending"
        return "Online database connected"
    def _request(self, method: str, path: str, **kwargs):
        if not self.enabled or not self.session:
            raise RuntimeError("Firebase URL is not configured or requests is unavailable.")
        url = f"{self.base_url}/{path.lstrip('/')}"
        if not url.endswith(".json"):
            url += ".json"
        r = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if not r.ok:
            raise RuntimeError(f"Firebase HTTP {r.status_code}: {r.text[:500]}")
        return r
    def _get_meta(self) -> tuple[Optional[str], Optional[dict]]:
        r = self._request("GET", "store_inventory/_meta.json")
        try:
            data = r.json()
        except Exception:
            data = None
        return (data.get("version"), data) if isinstance(data, dict) else (None, None)
    def _get_snapshot(self) -> Optional[Dict[str, Any]]:
        r = self._request("GET", "store_inventory/data.json")
        try:
            data = r.json()
        except Exception as exc:
            raise RuntimeError(f"Invalid Firebase data response: {exc}")
        return data if isinstance(data, dict) else None
    def _load_json(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            if not os.path.exists(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                value = json.load(f)
            return value if isinstance(value, dict) else None
        except Exception:
            return None
    def _atomic_save_json(self, path: str, value: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix="firebase_sync_", suffix=".tmp", dir=os.path.dirname(path))
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
    def _save_state(self, snapshot: Dict[str, Any]) -> None:
        try:
            self._atomic_save_json(self.state_path, snapshot)
        except Exception:
            pass
    def _save_pending(self, snapshot: Dict[str, Any], baseline: Dict[str, Any]) -> None:
        try:
            self._atomic_save_json(self.pending_path, {"snapshot": snapshot, "baseline": baseline, "saved_at": time.time()})
        except Exception:
            pass
    def _clear_pending(self) -> None:
        try:
            if os.path.exists(self.pending_path):
                os.remove(self.pending_path)
        except OSError:
            pass
    def _get_lock_etag(self) -> tuple[Any, str]:
        url = f"{self.base_url}/store_inventory/_lock.json"
        r = self.session.get(url, headers={"X-Firebase-ETag": "true"}, timeout=self.timeout)
        if not r.ok:
            raise RuntimeError(f"Firebase lock GET HTTP {r.status_code}: {r.text[:300]}")
        try:
            value = r.json()
        except Exception:
            value = None
        return value, r.headers.get("ETag", "null_etag")
    def _try_acquire_lock(self, token: str) -> bool:
        # The old lock could survive a crashed client forever. Use a short
        # lease so one dead PC can never permanently block online sync.
        value, etag = self._get_lock_etag()
        if isinstance(value, dict):
            owner = str(value.get("token") or "")
            created = float(value.get("created_at") or 0)
            if owner and (time.time() - created) < 30:
                return False
        elif value not in (None, ""):
            # Legacy string locks from older builds are treated as stale.
            # The ETag still prevents two clients from replacing each other
            # at the same instant.
            pass
        url = f"{self.base_url}/store_inventory/_lock.json"
        payload = {"token": token, "created_at": time.time()}
        r = self.session.put(
            url, json=payload,
            headers={"if-match": etag, "content-type": "application/json"},
            timeout=self.timeout,
        )
        return r.status_code in (200, 201)
    def _release_lock(self, token: str) -> None:
        try:
            value, etag = self._get_lock_etag()
            owner = value.get("token") if isinstance(value, dict) else value
            if owner != token:
                return
            url = f"{self.base_url}/store_inventory/_lock.json"
            self.session.put(url, data="null", headers={"if-match": etag, "content-type": "application/json"}, timeout=self.timeout)
        except Exception:
            pass
    def initialize(self, conn: sqlite3.Connection) -> None:
        if not self.enabled:
            return
        local = snapshot_db(conn)
        pending = self._load_json(self.pending_path)
        state = self._load_json(self.state_path)
        # A pending snapshot is the strongest local recovery source.
        if isinstance(pending, dict) and isinstance(pending.get("snapshot"), dict):
            local = pending["snapshot"]
            self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
        try:
            remote = self._get_snapshot()
            version, _ = self._get_meta()
            if remote and remote.get("tables"):
                # FIRST-RUN / FRESH INSTALL RULE:
                # A newly installed copy can contain seeded Inventory Codes,
                # but those seed rows are NOT a user's unsynchronized changes.
                # When there is no prior Firebase sync state and no pending
                # journal, Firebase is the source of truth and must be loaded
                # into the fresh PC. This is what makes a second PC on another
                # Internet network automatically receive the existing cloud data.
                has_sync_state = isinstance(state, dict) and _snapshot_has_records(state)
                has_pending = self.pending_base is not None
                if not has_sync_state and not has_pending:
                    self.replace_local(conn, remote)
                    self.last_remote_version = version
                    self._save_state(remote)
                else:
                    # Established installations use a three-way merge so local
                    # offline/new records are preserved while remote records
                    # from other PCs are also retained.
                    baseline = self.pending_base or state or {"schema": 1, "tables": {}}
                    merged = merge_local_changes(remote, baseline, local)
                    if merged != remote:
                        new_version = self._write_remote(merged)
                        self.replace_local(conn, merged)
                        self.last_remote_version = new_version
                        self._save_state(merged)
                    else:
                        self.replace_local(conn, remote)
                        self.last_remote_version = version
                        self._save_state(remote)
                self.pending_base = None
                self.pending_error = None
                self._clear_pending()
            else:
                new_version = self._write_remote(local)
                self.last_remote_version = new_version
                self._save_state(local)
                self._clear_pending()
                self.pending_base = None
                self.pending_error = None
        except Exception as exc:
            # Firebase being offline must never delete the local data. Keep
            # the local snapshot and retry on the next start/commit.
            self.pending_error = str(exc)
            self._save_pending(local, self.pending_base or state or {"schema": 1, "tables": {}})
    def replace_local(self, conn: sqlite3.Connection, snapshot: Dict[str, Any]) -> None:
        old_isolation = conn.isolation_level
        try:
            conn.execute("BEGIN")
            for table in TABLES:
                cols = _table_columns(conn, table)
                rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
                conn.execute(f"DELETE FROM {table}")
                if not rows:
                    continue
                insert_cols = [c for c in cols if c in rows[0]]
                placeholders = ",".join("?" for _ in insert_cols)
                sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
                for row in rows:
                    conn.execute(sql, [row.get(c) for c in insert_cols])
            conn.commit()
        finally:
            conn.isolation_level = old_isolation
    def _write_remote(self, snapshot: Dict[str, Any]) -> str:
        token = f"{self.client_id}-{uuid.uuid4().hex}"
        acquired = False
        last_exc = None
        for _ in range(10):
            try:
                if self._try_acquire_lock(token):
                    acquired = True
                    break
            except Exception as exc:
                last_exc = exc
            time.sleep(0.35)
        if not acquired:
            raise RuntimeError(f"Could not acquire Firebase sync lock. {last_exc or ''}".strip())
        try:
            new_version = f"{time.time_ns()}-{self.client_id}"
            self._request("PUT", "store_inventory/data.json", json=snapshot)
            self._request("PUT", "store_inventory/_meta/version.json", json=new_version)
            self._request("PUT", "store_inventory/_meta/updated_by.json", json=self.client_id)
            return new_version
        finally:
            self._release_lock(token)
    def push_changes(self, conn: sqlite3.Connection, baseline: Dict[str, Any]) -> bool:
        if not self.enabled:
            return True
        local = snapshot_db(conn)
        try:
            remote = self._get_snapshot() or {"schema": 1, "tables": {}}
            merged = merge_local_changes(remote, baseline or {"schema": 1, "tables": {}}, local)
            new_version = self._write_remote(merged)
            self.replace_local(conn, merged)
            self.last_remote_version = new_version
            self.pending_base = None
            self.pending_error = None
            self._save_state(merged)
            self._clear_pending()
            return True
        except Exception as exc:
            self.pending_base = deepcopy(baseline)
            self.pending_error = str(exc)
            self._save_pending(local, baseline or {"schema": 1, "tables": {}})
            return False
    def maybe_pull(self, conn: sqlite3.Connection) -> bool:
        """Pull Firebase changes even when the remote metadata/version endpoint
        is unavailable or cached. This is the live cross-PC synchronization path."""
        if not self.enabled:
            return False
        now = time.monotonic()
        if now - self.last_check < self.check_interval:
            return False
        self.last_check = now
        try:
            # Do not depend on _meta/version for live synchronization. Read the
            # actual shared dataset so a new entry saved by another laptop is
            # detected even if metadata is missing, delayed, or filtered.
            snapshot = self._get_snapshot()
            if snapshot is None:
                return False

            # Compare the actual remote dataset with the last synchronized
            # snapshot. This is intentionally simple and reliable for the
            # application's dataset size.
            current_signature = json.dumps(
                snapshot,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            state_snapshot = self._load_json(self.state_path)
            state_signature = json.dumps(
                state_snapshot,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ) if isinstance(state_snapshot, dict) else ""

            if current_signature == state_signature:
                self.pending_error = None
                return False

            # Three-way merge remote changes with any local changes made since
            # the last synchronized state. Never replace a newer local record
            # merely because another PC changed Firebase.
            baseline = self.pending_base or (state_snapshot if isinstance(state_snapshot, dict) else {"schema": 1, "tables": {}})
            local = snapshot_db(conn)
            merged = merge_local_changes(snapshot, baseline, local)

            if merged != snapshot:
                new_version = self._write_remote(merged)
                self.replace_local(conn, merged)
                self.last_remote_version = new_version
                self._save_state(merged)
            else:
                self.replace_local(conn, snapshot)
                try:
                    version, _ = self._get_meta()
                except Exception:
                    version = None
                self.last_remote_version = version
                self._save_state(snapshot)

            self.pending_error = None
            self.pending_base = None
            self._clear_pending()
            return True
        except Exception as exc:
            self.pending_error = str(exc)
            return False
class _OnlineCursor:
    """Cursor proxy that keeps Firebase sync active for conn.cursor().execute()."""
    def __init__(self, owner, cursor):
        self._owner = owner
        self._cursor = cursor
    def execute(self, sql, params=()):
        self._owner._before_sql(sql)
        return self._cursor.execute(sql, params)
    def executemany(self, sql, seq_of_params):
        self._owner._before_write()
        return self._cursor.executemany(sql, seq_of_params)
    def executescript(self, script):
        self._owner._before_write()
        return self._cursor.executescript(script)
    def __getattr__(self, name):
        return getattr(self._cursor, name)

class OnlineConnection:
    def __init__(self, db_path: str, sync: FirebaseSync):
        self._conn = sqlite3.connect(db_path, timeout=20)
        self._conn.execute("PRAGMA busy_timeout=20000")
        self.sync = sync
        self._dirty = False
        self._baseline: Optional[Dict[str, Any]] = None
    def _before_write(self):
        if not self._dirty:
            self._baseline = self.sync.pending_base or snapshot_db(self._conn)
            self._dirty = True
    def _before_sql(self, sql):
        s = str(sql).lstrip().upper()
        is_read = s.startswith("SELECT") or s.startswith("PRAGMA") or s.startswith("WITH") or s.startswith("EXPLAIN")
        if is_read and not self._dirty and self._baseline is None:
            self.sync.maybe_pull(self._conn)
        elif not is_read:
            self._before_write()
    def execute(self, sql: str, params: Iterable[Any] = ()):
        self._before_sql(sql)
        return self._conn.execute(sql, params)
    def executemany(self, sql: str, seq_of_params):
        self._before_write()
        return self._conn.executemany(sql, seq_of_params)
    def executescript(self, script):
        self._before_write()
        return self._conn.executescript(script)
    def cursor(self, *args, **kwargs):
        return _OnlineCursor(self, self._conn.cursor(*args, **kwargs))
    def commit(self):
        self._conn.commit()
        import durable_local
        durable_local.save(self._conn)
        local = snapshot_db(self._conn)
        baseline = self._baseline
        if baseline is None:
            state = self.sync._load_json(self.sync.state_path)
            baseline = state if isinstance(state, dict) else None
        if baseline is None or local != baseline:
            self.sync.push_changes(self._conn, baseline or {"schema": 1, "tables": {}})
            durable_local.save(self._conn)
        self._dirty = False
        self._baseline = None
    def rollback(self):
        self._conn.rollback()
        self._dirty = False
        self._baseline = None
    def close(self):
        self._conn.close()
    def backup(self, target):
        return self._conn.backup(target)
    def __getattr__(self, name):
        return getattr(self._conn, name)
