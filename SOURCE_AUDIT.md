# Store Inventory source audit

Generated from `D:\a\Store-Inventory-Management\Store-Inventory-Management\source` after CI patches.

## durable_local.py

- Lines: 158
- Functions: _columns(34-35), snapshot(37-47), _row_count(49-50), _has_more_business_data(52-60), _atomic_write(62-76), save(78-100), load(102-122), restore_if_newer(124-158)

### Relevant source locations

```text
0001: """Crash/restart-safe local snapshot for Store Inventory Management.
0002: 
0003: The SQLite database remains the live local cache. This small journal is an
0004: additional safety net: every successful local commit is copied to a durable
0005: JSON snapshot under C:\\StoreInventoryManagement\\Data before network sync.
0006: It is only used to recover a database that is missing or unexpectedly empty;
0007: it never deletes the SQLite database or user data.
0008: """
0009: from __future__ import annotations
0010: import json
0011: import os
0012: import sqlite3
0013: import tempfile
0014: import traceback
0015: from pathlib import Path
```
```text
0015: from pathlib import Path
0016: from typing import Any, Dict
0017: 
0018: INSTALL_ROOT = Path(r"C:\StoreInventoryManagement")
0019: DATA_DIR = INSTALL_ROOT / "Data"
0020: SNAPSHOT_PATH = DATA_DIR / "local_data_snapshot.json"
0021: 
0022: # Secondary recovery copy lives outside the installation folder. This copy
0023: # survives deletion/reinstallation of C:\StoreInventoryManagement; Firebase
0024: # remains the primary online copy.
0025: LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
0026: RECOVERY_DIR = LOCALAPPDATA / "StoreInventoryManagement" / "Recovery"
0027: RECOVERY_SNAPSHOT_PATH = RECOVERY_DIR / "local_data_snapshot.json"
0028: TABLES = (
0029:     "items", "mto_items", "parties", "demands", "demand_lines", "grr", "grr_lines",
0030:     "issues", "issue_lines", "transactions", "users",
0031: )
0032: LAST_ERROR = ""
0033: 
0034: def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
0035:     return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
```
```text
0029:     "items", "mto_items", "parties", "demands", "demand_lines", "grr", "grr_lines",
0030:     "issues", "issue_lines", "transactions", "users",
0031: )
0032: LAST_ERROR = ""
0033: 
0034: def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
0035:     return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
0036: 
0037: def snapshot(conn: sqlite3.Connection) -> Dict[str, Any]:
0038:     tables: Dict[str, Any] = {}
0039:     for table in TABLES:
0040:         cols = _columns(conn, table)
0041:         rows = []
0042:         if cols:
0043:             for row in conn.execute(f"SELECT {','.join(cols)} FROM {table}").fetchall():
0044:                 rows.append({c: (v if v is None or isinstance(v, (str, int, float, bool)) else str(v))
0045:                              for c, v in zip(cols, row)})
0046:         tables[table] = {"columns": cols, "rows": rows}
0047:     return {"schema": 1, "tables": tables}
0048: 
0049: def _row_count(s: Dict[str, Any]) -> int:
```
```text
0044:                 rows.append({c: (v if v is None or isinstance(v, (str, int, float, bool)) else str(v))
0045:                              for c, v in zip(cols, row)})
0046:         tables[table] = {"columns": cols, "rows": rows}
0047:     return {"schema": 1, "tables": tables}
0048: 
0049: def _row_count(s: Dict[str, Any]) -> int:
0050:     return sum(len(v.get("rows", []) or []) for v in s.get("tables", {}).values())
0051: 
0052: def _has_more_business_data(saved: Dict[str, Any], current: Dict[str, Any]) -> bool:
0053:     # Compare each table so seeded Inventory Codes cannot block recovery of
0054:     # saved Demand/GRN/Issue/Party records after a reinstall.
0055:     for table in TABLES:
0056:         saved_n = len(saved.get("tables", {}).get(table, {}).get("rows", []) or [])
0057:         current_n = len(current.get("tables", {}).get(table, {}).get("rows", []) or [])
0058:         if saved_n > current_n:
0059:             return True
0060:     return False
0061: 
0062: def _atomic_write(path: Path, value: Dict[str, Any]) -> None:
0063:     path.parent.mkdir(parents=True, exist_ok=True)
0064:     fd, tmp = tempfile.mkstemp(prefix="local_snapshot_", suffix=".tmp", dir=str(path.parent))
```
```text
0058:         if saved_n > current_n:
0059:             return True
0060:     return False
0061: 
0062: def _atomic_write(path: Path, value: Dict[str, Any]) -> None:
0063:     path.parent.mkdir(parents=True, exist_ok=True)
0064:     fd, tmp = tempfile.mkstemp(prefix="local_snapshot_", suffix=".tmp", dir=str(path.parent))
0065:     try:
0066:         with os.fdopen(fd, "w", encoding="utf-8") as f:
0067:             json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
0068:             f.flush()
0069:             os.fsync(f.fileno())
0070:         os.replace(tmp, path)
0071:     finally:
0072:         try:
0073:             if os.path.exists(tmp):
0074:                 os.remove(tmp)
0075:         except OSError:
0076:             pass
0077: 
0078: def save(conn: sqlite3.Connection) -> bool:
```
```text
0088:         except Exception:
0089:             pass
0090:         try:
0091:             _atomic_write(RECOVERY_SNAPSHOT_PATH, value)
0092:             recovery_ok = True
0093:         except Exception:
0094:             recovery_ok = False
0095:         if not (c_ok or recovery_ok):
0096:             raise IOError("Could not save the local recovery snapshot.")
0097:         return True
0098:     except Exception:
0099:         LAST_ERROR = traceback.format_exc()
0100:         return False
0101: 
0102: def load() -> Dict[str, Any] | None:
0103:     global LAST_ERROR
0104:     try:
0105:         candidates = []
0106:         # The C: snapshot is convenient for normal operation, while the
0107:         # AppData recovery copy survives deletion/reinstallation of the
0108:         # installation folder.
```
```text
0116:                 pass
0117:         if not candidates:
0118:             return None
0119:         return max(candidates, key=_row_count)
0120:     except Exception:
0121:         LAST_ERROR = traceback.format_exc()
0122:         return None
0123: 
0124: def restore_if_newer(conn: sqlite3.Connection) -> bool:
0125:     global LAST_ERROR
0126:     LAST_ERROR = ""
0127:     saved = load()
0128:     if not saved or _row_count(saved) <= 0:
0129:         return False
0130:     current = snapshot(conn)
0131:     if not _has_more_business_data(saved, current):
0132:         return False
0133:     try:
0134:         conn.execute("BEGIN")
0135:         for table in TABLES:
0136:             cols = _columns(conn, table)
```
```text
0129:         return False
0130:     current = snapshot(conn)
0131:     if not _has_more_business_data(saved, current):
0132:         return False
0133:     try:
0134:         conn.execute("BEGIN")
0135:         for table in TABLES:
0136:             cols = _columns(conn, table)
0137:             rows = saved.get("tables", {}).get(table, {}).get("rows", []) or []
0138:             if not cols:
0139:                 continue
0140:             conn.execute(f"DELETE FROM {table}")
0141:             if not rows:
0142:                 continue
0143:             insert_cols = [c for c in cols if c in rows[0]]
0144:             if not insert_cols:
0145:                 continue
0146:             placeholders = ",".join("?" for _ in insert_cols)
0147:             sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0148:             for row in rows:
0149:                 conn.execute(sql, [row.get(c) for c in insert_cols])
```
```text
0142:                 continue
0143:             insert_cols = [c for c in cols if c in rows[0]]
0144:             if not insert_cols:
0145:                 continue
0146:             placeholders = ",".join("?" for _ in insert_cols)
0147:             sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0148:             for row in rows:
0149:                 conn.execute(sql, [row.get(c) for c in insert_cols])
0150:         conn.commit()
0151:         return True
0152:     except Exception:
0153:         LAST_ERROR = traceback.format_exc()
0154:         try:
0155:             conn.rollback()
0156:         except Exception:
0157:             pass
0158:         return False
```

## firebase_sync.py

- Lines: 547
- Functions: _safe_json_value(25-28), _table_columns(29-30), snapshot_db(31-39), _row_key(40-44), _index_snapshot(45-49), merge_local_changes(50-71), _snapshot_has_records(72-74), __init__(76-95), _read_url(96-106), status_text(107-112), _request(113-122), _get_meta(123-129), _get_snapshot(130-136), _load_json(137-145), _atomic_save_json(146-160), _save_state(161-165), _save_pending(166-170), _clear_pending(171-176), _get_lock_etag(177-186), _try_acquire_lock(187-208), _release_lock(209-218), initialize(219-276), replace_local(277-294), _write_remote(295-316), push_changes(317-336), _background_pull_worker(337-353), kick_background_pull(355-372), apply_cached_pull(374-400), maybe_pull(402-467), __init__(470-472), execute(473-475), executemany(476-478), executescript(479-481), __getattr__(482-483), __init__(486-500), _before_write(501-504), _before_sql(505-513), execute(514-516), executemany(517-519), executescript(520-522), cursor(523-524), commit(525-536), rollback(538-541), close(542-543), backup(544-545), __getattr__(546-547)

### Relevant source locations

```text
0001: """Reliable Firebase Realtime Database synchronization for Store Inventory Management.
0002: 
0003: Uses only the Firebase Realtime Database URL (no API key).  Local SQLite is
0004: always kept durable; Firebase synchronization is retried and failed writes
0005: are journaled so an application restart cannot discard locally saved records.
0006: """
0007: from __future__ import annotations
0008: import json
0009: import os
0010: import sqlite3
0011: import tempfile
0012: import time
0013: import uuid
```
```text
0021: TABLES = (
0022:     "items", "mto_items", "parties", "demands", "demand_lines", "grr", "grr_lines",
0023:     "issues", "issue_lines", "transactions", "users",
0024: )
0025: def _safe_json_value(value: Any) -> Any:
0026:     if value is None or isinstance(value, (str, int, float, bool)):
0027:         return value
0028:     return str(value)
0029: def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
0030:     return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
0031: def snapshot_db(conn: sqlite3.Connection) -> Dict[str, Any]:
0032:     tables: Dict[str, Any] = {}
0033:     for table in TABLES:
0034:         cols = _table_columns(conn, table)
0035:         rows = []
0036:         for row in conn.execute(f"SELECT {','.join(cols)} FROM {table}").fetchall():
0037:             rows.append({col: _safe_json_value(row[i]) for i, col in enumerate(cols)})
0038:         tables[table] = {"columns": cols, "rows": rows}
0039:     return {"schema": 1, "tables": tables}
0040: def _row_key(table: str, row: Dict[str, Any]) -> Tuple[str, Any]:
0041:     if table in ("items", "mto_items", "demands", "grr", "issues", "users"):
```
```text
0067:         columns = (local.get("tables", {}).get(table, {}).get("columns") or
0068:                    remote.get("tables", {}).get(table, {}).get("columns") or
0069:                    baseline.get("tables", {}).get(table, {}).get("columns") or [])
0070:         merged["tables"][table] = {"columns": columns, "rows": list(out.values())}
0071:     return merged
0072: def _snapshot_has_records(snapshot: Dict[str, Any]) -> bool:
0073:     tables = snapshot.get("tables", {})
0074:     return any(tables.get(x, {}).get("rows") for x in TABLES)
0075: class FirebaseSync:
0076:     def __init__(self, url_file: str, install_dir: str, timeout: float = 2.5):
0077:         self.url_file = url_file
0078:         self.install_dir = install_dir
0079:         self.timeout = timeout
0080:         self.base_url = self._read_url()
0081:         self.enabled = bool(self.base_url and requests)
0082:         self.last_remote_version: Optional[str] = None
0083:         self.last_check = 0.0
0084:         self.check_interval = 10.0
0085:         self.pending_base: Optional[Dict[str, Any]] = None
0086:         self.pending_error: Optional[str] = None
0087:         self.session = requests.Session() if requests else None
```
```text
0083:         self.last_check = 0.0
0084:         self.check_interval = 10.0
0085:         self.pending_base: Optional[Dict[str, Any]] = None
0086:         self.pending_error: Optional[str] = None
0087:         self.session = requests.Session() if requests else None
0088:         self.client_id = f"{os.environ.get('COMPUTERNAME','PC')}-{uuid.uuid4().hex[:10]}"
0089:         data_dir = os.path.join(self.install_dir, "Data")
0090:         os.makedirs(data_dir, exist_ok=True)
0091:         self.state_path = os.path.join(data_dir, "firebase_sync_state.json")
0092:         self.pending_path = os.path.join(data_dir, "firebase_pending_sync.json")
0093:         self.remote_cache_path = os.path.join(data_dir, "firebase_remote_cache.json")
0094:         self._pull_thread = None
0095:         self._pull_lock = threading.Lock()
0096:     def _read_url(self) -> str:
0097:         try:
0098:             with open(self.url_file, "r", encoding="utf-8-sig") as f:
0099:                 raw = f.read().strip().splitlines()
0100:         except Exception:
0101:             return ""
0102:         for line in raw:
0103:             line = line.strip()
```
```text
0101:             return ""
0102:         for line in raw:
0103:             line = line.strip()
0104:             if line and not line.startswith("#"):
0105:                 return line.rstrip("/")
0106:         return ""
0107:     def status_text(self) -> str:
0108:         if not self.enabled:
0109:             return "Firebase URL not configured"
0110:         if self.pending_error:
0111:             return "Online database sync pending"
0112:         return "Online database connected"
0113:     def _request(self, method: str, path: str, **kwargs):
0114:         if not self.enabled or not self.session:
0115:             raise RuntimeError("Firebase URL is not configured or requests is unavailable.")
0116:         url = f"{self.base_url}/{path.lstrip('/')}"
0117:         if not url.endswith(".json"):
0118:             url += ".json"
0119:         r = self.session.request(method, url, timeout=self.timeout, **kwargs)
0120:         if not r.ok:
0121:             raise RuntimeError(f"Firebase HTTP {r.status_code}: {r.text[:500]}")
```
```text
0127:         except Exception:
0128:             data = None
0129:         return (data.get("version"), data) if isinstance(data, dict) else (None, None)
0130:     def _get_snapshot(self) -> Optional[Dict[str, Any]]:
0131:         r = self._request("GET", "store_inventory/data.json")
0132:         try:
0133:             data = r.json()
0134:         except Exception as exc:
0135:             raise RuntimeError(f"Invalid Firebase data response: {exc}")
0136:         return data if isinstance(data, dict) else None
0137:     def _load_json(self, path: str) -> Optional[Dict[str, Any]]:
0138:         try:
0139:             if not os.path.exists(path):
0140:                 return None
0141:             with open(path, "r", encoding="utf-8") as f:
0142:                 value = json.load(f)
0143:             return value if isinstance(value, dict) else None
0144:         except Exception:
0145:             return None
0146:     def _atomic_save_json(self, path: str, value: Dict[str, Any]) -> None:
0147:         os.makedirs(os.path.dirname(path), exist_ok=True)
```
```text
0140:                 return None
0141:             with open(path, "r", encoding="utf-8") as f:
0142:                 value = json.load(f)
0143:             return value if isinstance(value, dict) else None
0144:         except Exception:
0145:             return None
0146:     def _atomic_save_json(self, path: str, value: Dict[str, Any]) -> None:
0147:         os.makedirs(os.path.dirname(path), exist_ok=True)
0148:         fd, tmp = tempfile.mkstemp(prefix="firebase_sync_", suffix=".tmp", dir=os.path.dirname(path))
0149:         try:
0150:             with os.fdopen(fd, "w", encoding="utf-8") as f:
0151:                 json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
0152:                 f.flush()
0153:                 os.fsync(f.fileno())
0154:             os.replace(tmp, path)
0155:         finally:
0156:             try:
0157:                 if os.path.exists(tmp):
0158:                     os.remove(tmp)
0159:             except OSError:
0160:                 pass
```
```text
0153:                 os.fsync(f.fileno())
0154:             os.replace(tmp, path)
0155:         finally:
0156:             try:
0157:                 if os.path.exists(tmp):
0158:                     os.remove(tmp)
0159:             except OSError:
0160:                 pass
0161:     def _save_state(self, snapshot: Dict[str, Any]) -> None:
0162:         try:
0163:             self._atomic_save_json(self.state_path, snapshot)
0164:         except Exception:
0165:             pass
0166:     def _save_pending(self, snapshot: Dict[str, Any], baseline: Dict[str, Any]) -> None:
0167:         try:
0168:             self._atomic_save_json(self.pending_path, {"snapshot": snapshot, "baseline": baseline, "saved_at": time.time()})
0169:         except Exception:
0170:             pass
0171:     def _clear_pending(self) -> None:
0172:         try:
0173:             if os.path.exists(self.pending_path):
```
```text
0171:     def _clear_pending(self) -> None:
0172:         try:
0173:             if os.path.exists(self.pending_path):
0174:                 os.remove(self.pending_path)
0175:         except OSError:
0176:             pass
0177:     def _get_lock_etag(self) -> tuple[Any, str]:
0178:         url = f"{self.base_url}/store_inventory/_lock.json"
0179:         r = self.session.get(url, headers={"X-Firebase-ETag": "true"}, timeout=self.timeout)
0180:         if not r.ok:
0181:             raise RuntimeError(f"Firebase lock GET HTTP {r.status_code}: {r.text[:300]}")
0182:         try:
0183:             value = r.json()
0184:         except Exception:
0185:             value = None
0186:         return value, r.headers.get("ETag", "null_etag")
0187:     def _try_acquire_lock(self, token: str) -> bool:
0188:         # The old lock could survive a crashed client forever. Use a short
0189:         # lease so one dead PC can never permanently block online sync.
0190:         value, etag = self._get_lock_etag()
0191:         if isinstance(value, dict):
```
```text
0211:             value, etag = self._get_lock_etag()
0212:             owner = value.get("token") if isinstance(value, dict) else value
0213:             if owner != token:
0214:                 return
0215:             url = f"{self.base_url}/store_inventory/_lock.json"
0216:             self.session.put(url, data="null", headers={"if-match": etag, "content-type": "application/json"}, timeout=self.timeout)
0217:         except Exception:
0218:             pass
0219:     def initialize(self, conn: sqlite3.Connection) -> None:
0220:         if not self.enabled:
0221:             return
0222:         local = snapshot_db(conn)
0223:         pending = self._load_json(self.pending_path)
0224:         state = self._load_json(self.state_path)
0225:         # A pending snapshot is the strongest local recovery source.
0226:         if isinstance(pending, dict) and isinstance(pending.get("snapshot"), dict):
0227:             local = pending["snapshot"]
0228:             self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
0229:         try:
0230:             remote = self._get_snapshot()
0231:             # Avoid a second startup HTTP request; metadata is optional here.
```
```text
0229:         try:
0230:             remote = self._get_snapshot()
0231:             # Avoid a second startup HTTP request; metadata is optional here.
0232:             version = None
0233:             if remote and remote.get("tables"):
0234:                 # FIRST-RUN / FRESH INSTALL RULE:
0235:                 # A newly installed copy can contain seeded Inventory Codes,
0236:                 # but those seed rows are NOT a user's unsynchronized changes.
0237:                 # When there is no prior Firebase sync state and no pending
0238:                 # journal, Firebase is the source of truth and must be loaded
0239:                 # into the fresh PC. This is what makes a second PC on another
0240:                 # Internet network automatically receive the existing cloud data.
0241:                 has_sync_state = isinstance(state, dict) and _snapshot_has_records(state)
0242:                 has_pending = self.pending_base is not None
0243:                 if not has_sync_state and not has_pending:
0244:                     self.replace_local(conn, remote)
0245:                     self.last_remote_version = version
0246:                     self._save_state(remote)
0247:                 else:
0248:                     # Established installations use a three-way merge so local
0249:                     # offline/new records are preserved while remote records
```
```text
0249:                     # offline/new records are preserved while remote records
0250:                     # from other PCs are also retained.
0251:                     baseline = self.pending_base or state or {"schema": 1, "tables": {}}
0252:                     merged = merge_local_changes(remote, baseline, local)
0253:                     if merged != remote:
0254:                         new_version = self._write_remote(merged)
0255:                         self.replace_local(conn, merged)
0256:                         self.last_remote_version = new_version
0257:                         self._save_state(merged)
0258:                     else:
0259:                         self.replace_local(conn, remote)
0260:                         self.last_remote_version = version
0261:                         self._save_state(remote)
0262:                 self.pending_base = None
0263:                 self.pending_error = None
0264:                 self._clear_pending()
0265:             else:
0266:                 new_version = self._write_remote(local)
0267:                 self.last_remote_version = new_version
0268:                 self._save_state(local)
0269:                 self._clear_pending()
```
```text
0265:             else:
0266:                 new_version = self._write_remote(local)
0267:                 self.last_remote_version = new_version
0268:                 self._save_state(local)
0269:                 self._clear_pending()
0270:                 self.pending_base = None
0271:                 self.pending_error = None
0272:         except Exception as exc:
0273:             # Firebase being offline must never delete the local data. Keep
0274:             # the local snapshot and retry on the next start/commit.
0275:             self.pending_error = str(exc)
0276:             self._save_pending(local, self.pending_base or state or {"schema": 1, "tables": {}})
0277:     def replace_local(self, conn: sqlite3.Connection, snapshot: Dict[str, Any]) -> None:
0278:         old_isolation = conn.isolation_level
0279:         try:
0280:             conn.execute("BEGIN")
0281:             for table in TABLES:
0282:                 cols = _table_columns(conn, table)
0283:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0284:                 conn.execute(f"DELETE FROM {table}")
0285:                 if not rows:
```
```text
0281:             for table in TABLES:
0282:                 cols = _table_columns(conn, table)
0283:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0284:                 conn.execute(f"DELETE FROM {table}")
0285:                 if not rows:
0286:                     continue
0287:                 insert_cols = [c for c in cols if c in rows[0]]
0288:                 placeholders = ",".join("?" for _ in insert_cols)
0289:                 sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0290:                 for row in rows:
0291:                     conn.execute(sql, [row.get(c) for c in insert_cols])
0292:             conn.commit()
0293:         finally:
0294:             conn.isolation_level = old_isolation
0295:     def _write_remote(self, snapshot: Dict[str, Any]) -> str:
0296:         token = f"{self.client_id}-{uuid.uuid4().hex}"
0297:         acquired = False
0298:         last_exc = None
0299:         for _ in range(10):
0300:             try:
0301:                 if self._try_acquire_lock(token):
```
```text
0300:             try:
0301:                 if self._try_acquire_lock(token):
0302:                     acquired = True
0303:                     break
0304:             except Exception as exc:
0305:                 last_exc = exc
0306:             time.sleep(0.35)
0307:         if not acquired:
0308:             raise RuntimeError(f"Could not acquire Firebase sync lock. {last_exc or ''}".strip())
0309:         try:
0310:             new_version = f"{time.time_ns()}-{self.client_id}"
0311:             self._request("PUT", "store_inventory/data.json", json=snapshot)
0312:             self._request("PUT", "store_inventory/_meta/version.json", json=new_version)
0313:             self._request("PUT", "store_inventory/_meta/updated_by.json", json=self.client_id)
0314:             return new_version
0315:         finally:
0316:             self._release_lock(token)
0317:     def push_changes(self, conn: sqlite3.Connection, baseline: Dict[str, Any]) -> bool:
0318:         if not self.enabled:
0319:             return True
0320:         local = snapshot_db(conn)
```
```text
0321:         try:
0322:             remote = self._get_snapshot() or {"schema": 1, "tables": {}}
0323:             merged = merge_local_changes(remote, baseline or {"schema": 1, "tables": {}}, local)
0324:             new_version = self._write_remote(merged)
0325:             self.replace_local(conn, merged)
0326:             self.last_remote_version = new_version
0327:             self.pending_base = None
0328:             self.pending_error = None
0329:             self._save_state(merged)
0330:             self._clear_pending()
0331:             return True
0332:         except Exception as exc:
0333:             self.pending_base = deepcopy(baseline)
0334:             self.pending_error = str(exc)
0335:             self._save_pending(local, baseline or {"schema": 1, "tables": {}})
0336:             return False
0337:     def _background_pull_worker(self) -> None:
0338:         try:
0339:             if not self.enabled or requests is None:
0340:                 return
0341:             url = f"{self.base_url}/store_inventory/data.json"
```
```text
0336:             return False
0337:     def _background_pull_worker(self) -> None:
0338:         try:
0339:             if not self.enabled or requests is None:
0340:                 return
0341:             url = f"{self.base_url}/store_inventory/data.json"
0342:             r = requests.get(url, timeout=self.timeout)
0343:             if not r.ok:
0344:                 raise RuntimeError(f"Firebase HTTP {r.status_code}: {r.text[:300]}")
0345:             data = r.json()
0346:             if isinstance(data, dict):
0347:                 self._atomic_save_json(self.remote_cache_path, data)
0348:             self.pending_error = None
0349:         except Exception as exc:
0350:             self.pending_error = str(exc)
0351:         finally:
0352:             with self._pull_lock:
0353:                 self._pull_thread = None
0354: 
0355:     def kick_background_pull(self, force: bool = False) -> bool:
0356:         """Start a remote refresh without blocking Tk/UI reads."""
```
```text
0360:         with self._pull_lock:
0361:             if not force and now - self.last_check < self.check_interval:
0362:                 return False
0363:             if self._pull_thread is not None and self._pull_thread.is_alive():
0364:                 return False
0365:             self.last_check = now
0366:             self._pull_thread = threading.Thread(
0367:                 target=self._background_pull_worker,
0368:                 name="FirebasePull",
0369:                 daemon=True,
0370:             )
0371:             self._pull_thread.start()
0372:         return True
0373: 
0374:     def apply_cached_pull(self, conn: sqlite3.Connection) -> bool:
0375:         """Apply a completed background pull only when local data has no unsynced edits."""
0376:         cached = self._load_json(self.remote_cache_path)
0377:         if not isinstance(cached, dict):
0378:             return False
0379:         state = self._load_json(self.state_path)
0380:         local = snapshot_db(conn)
```
```text
0377:         if not isinstance(cached, dict):
0378:             return False
0379:         state = self._load_json(self.state_path)
0380:         local = snapshot_db(conn)
0381:         try:
0382:             if isinstance(state, dict) and local == state:
0383:                 if cached != state:
0384:                     self.replace_local(conn, cached)
0385:                     self._save_state(cached)
0386:                 try:
0387:                     os.remove(self.remote_cache_path)
0388:                 except OSError:
0389:                     pass
0390:                 self.pending_error = None
0391:                 return True
0392:             # Preserve local/offline edits. A normal push will merge them with Firebase.
0393:             try:
0394:                 os.remove(self.remote_cache_path)
0395:             except OSError:
0396:                 pass
0397:             return False
```
```text
0394:                 os.remove(self.remote_cache_path)
0395:             except OSError:
0396:                 pass
0397:             return False
0398:         except Exception as exc:
0399:             self.pending_error = str(exc)
0400:             return False
0401: 
0402:     def maybe_pull(self, conn: sqlite3.Connection) -> bool:
0403:         """Pull Firebase changes even when the remote metadata/version endpoint
0404:         is unavailable or cached. This is the live cross-PC synchronization path."""
0405:         if not self.enabled:
0406:             return False
0407:         now = time.monotonic()
0408:         if now - self.last_check < self.check_interval:
0409:             return False
0410:         self.last_check = now
0411:         try:
0412:             # Do not depend on _meta/version for live synchronization. Read the
0413:             # actual shared dataset so a new entry saved by another laptop is
0414:             # detected even if metadata is missing, delayed, or filtered.
```
```text
0414:             # detected even if metadata is missing, delayed, or filtered.
0415:             snapshot = self._get_snapshot()
0416:             if snapshot is None:
0417:                 return False
0418: 
0419:             # Compare the actual remote dataset with the last synchronized
0420:             # snapshot. This is intentionally simple and reliable for the
0421:             # application's dataset size.
0422:             current_signature = json.dumps(
0423:                 snapshot,
0424:                 ensure_ascii=False,
0425:                 sort_keys=True,
0426:                 separators=(",", ":"),
0427:             )
0428:             state_snapshot = self._load_json(self.state_path)
0429:             state_signature = json.dumps(
0430:                 state_snapshot,
0431:                 ensure_ascii=False,
0432:                 sort_keys=True,
0433:                 separators=(",", ":"),
0434:             ) if isinstance(state_snapshot, dict) else ""
```
```text
0434:             ) if isinstance(state_snapshot, dict) else ""
0435: 
0436:             if current_signature == state_signature:
0437:                 self.pending_error = None
0438:                 return False
0439: 
0440:             # Three-way merge remote changes with any local changes made since
0441:             # the last synchronized state. Never replace a newer local record
0442:             # merely because another PC changed Firebase.
0443:             baseline = self.pending_base or (state_snapshot if isinstance(state_snapshot, dict) else {"schema": 1, "tables": {}})
0444:             local = snapshot_db(conn)
0445:             merged = merge_local_changes(snapshot, baseline, local)
0446: 
0447:             if merged != snapshot:
0448:                 new_version = self._write_remote(merged)
0449:                 self.replace_local(conn, merged)
0450:                 self.last_remote_version = new_version
0451:                 self._save_state(merged)
0452:             else:
0453:                 self.replace_local(conn, snapshot)
0454:                 try:
```
```text
0451:                 self._save_state(merged)
0452:             else:
0453:                 self.replace_local(conn, snapshot)
0454:                 try:
0455:                     version, _ = self._get_meta()
0456:                 except Exception:
0457:                     version = None
0458:                 self.last_remote_version = version
0459:                 self._save_state(snapshot)
0460: 
0461:             self.pending_error = None
0462:             self.pending_base = None
0463:             self._clear_pending()
0464:             return True
0465:         except Exception as exc:
0466:             self.pending_error = str(exc)
0467:             return False
0468: class _OnlineCursor:
0469:     """Cursor proxy that keeps Firebase sync active for conn.cursor().execute()."""
0470:     def __init__(self, owner, cursor):
0471:         self._owner = owner
```
```text
0465:         except Exception as exc:
0466:             self.pending_error = str(exc)
0467:             return False
0468: class _OnlineCursor:
0469:     """Cursor proxy that keeps Firebase sync active for conn.cursor().execute()."""
0470:     def __init__(self, owner, cursor):
0471:         self._owner = owner
0472:         self._cursor = cursor
0473:     def execute(self, sql, params=()):
0474:         self._owner._before_sql(sql)
0475:         return self._cursor.execute(sql, params)
0476:     def executemany(self, sql, seq_of_params):
0477:         self._owner._before_write()
0478:         return self._cursor.executemany(sql, seq_of_params)
0479:     def executescript(self, script):
0480:         self._owner._before_write()
0481:         return self._cursor.executescript(script)
0482:     def __getattr__(self, name):
0483:         return getattr(self._cursor, name)
0484: 
0485: class OnlineConnection:
```
```text
0478:         return self._cursor.executemany(sql, seq_of_params)
0479:     def executescript(self, script):
0480:         self._owner._before_write()
0481:         return self._cursor.executescript(script)
0482:     def __getattr__(self, name):
0483:         return getattr(self._cursor, name)
0484: 
0485: class OnlineConnection:
0486:     def __init__(self, db_path: str, sync: FirebaseSync):
0487:         self._conn = sqlite3.connect(db_path, timeout=20)
0488:         self._conn.execute("PRAGMA busy_timeout=20000")
0489:         # Safe local-cache performance tuning. Firebase remains the online source;
0490:         # these pragmas only reduce UI stalls on local reads/writes.
0491:         try:
0492:             self._conn.execute("PRAGMA journal_mode=WAL")
0493:             self._conn.execute("PRAGMA synchronous=NORMAL")
0494:             self._conn.execute("PRAGMA temp_store=MEMORY")
0495:             self._conn.execute("PRAGMA cache_size=-12000")
0496:         except Exception:
0497:             pass
0498:         self.sync = sync
```
```text
0497:             pass
0498:         self.sync = sync
0499:         self._dirty = False
0500:         self._baseline: Optional[Dict[str, Any]] = None
0501:     def _before_write(self):
0502:         if not self._dirty:
0503:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0504:             self._dirty = True
0505:     def _before_sql(self, sql):
0506:         s = str(sql).lstrip().upper()
0507:         is_read = s.startswith("SELECT") or s.startswith("PRAGMA") or s.startswith("WITH") or s.startswith("EXPLAIN")
0508:         if is_read and not self._dirty and self._baseline is None:
0509:             # Never perform network I/O on the Tk/UI thread.
0510:             self.sync.apply_cached_pull(self._conn)
0511:             self.sync.kick_background_pull()
0512:         elif not is_read:
0513:             self._before_write()
0514:     def execute(self, sql: str, params: Iterable[Any] = ()):
0515:         self._before_sql(sql)
0516:         return self._conn.execute(sql, params)
0517:     def executemany(self, sql: str, seq_of_params):
```
```text
0511:             self.sync.kick_background_pull()
0512:         elif not is_read:
0513:             self._before_write()
0514:     def execute(self, sql: str, params: Iterable[Any] = ()):
0515:         self._before_sql(sql)
0516:         return self._conn.execute(sql, params)
0517:     def executemany(self, sql: str, seq_of_params):
0518:         self._before_write()
0519:         return self._conn.executemany(sql, seq_of_params)
0520:     def executescript(self, script):
0521:         self._before_write()
0522:         return self._conn.executescript(script)
0523:     def cursor(self, *args, **kwargs):
0524:         return _OnlineCursor(self, self._conn.cursor(*args, **kwargs))
0525:     def commit(self):
0526:         self._conn.commit()
0527:         # Keep the recovery module available inside the generated sync module.
0528:         import durable_local
0529:         # Make local persistence independent of Firebase availability.
0530:         durable_local.save(self._conn)
0531:         if self._dirty:
```
```text
0525:     def commit(self):
0526:         self._conn.commit()
0527:         # Keep the recovery module available inside the generated sync module.
0528:         import durable_local
0529:         # Make local persistence independent of Firebase availability.
0530:         durable_local.save(self._conn)
0531:         if self._dirty:
0532:             self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
0533:             # push_changes may merge remote rows back into SQLite.
0534:             durable_local.save(self._conn)
0535:         self._dirty = False
0536:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0537: 
0538:     def rollback(self):
0539:         self._conn.rollback()
0540:         self._dirty = False
0541:         self._baseline = None
0542:     def close(self):
0543:         self._conn.close()
0544:     def backup(self, target):
0545:         return self._conn.backup(target)
```

## storage_lock.py

- Lines: 171
- Functions: _inside(19-23), _runtime_temp_root(26-28), _is_runtime_temp(31-33), _is_database_path(36-37), _permanent_db_target(40-41), _classify_relative(44-52), _write_target(55-70), _read_target(73-91), _is_write_mode(94-95), _open(98-106), _io_open(109-117), _sqlite_connect(120-138), _copy2(141-144), _copyfile(147-150), install(160-168)

### Relevant source locations

```text
0001: from pathlib import Path
0002: import builtins
0003: import io
0004: import os
0005: import shutil
0006: import sqlite3
0007: import sys
0008: 
0009: INSTALL_ROOT = Path(r"C:\StoreInventoryManagement")
0010: DATA_DIR = INSTALL_ROOT / "Data"
0011: BACKUP_DIR = INSTALL_ROOT / "Backups"
0012: REPORTS_DIR = INSTALL_ROOT / "Reports"
0013: 
0014: _CONFIG_FILES = {"firebase_database_url.txt", "update_config.json", "firebase_rules_url_only.json"}
0015: _RESOURCE_FILES = {"inventory_seed.csv", "company_logo.png"}
0016: _DB_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".db3"}
0017: 
0018: 
```
```text
0028:     return Path(value) if value else None
0029: 
0030: 
0031: def _is_runtime_temp(path):
0032:     temp_root = _runtime_temp_root()
0033:     return bool(temp_root and _inside(path, temp_root))
0034: 
0035: 
0036: def _is_database_path(path):
0037:     return Path(os.fspath(path)).suffix.casefold() in _DB_SUFFIXES
0038: 
0039: 
0040: def _permanent_db_target(p):
0041:     return DATA_DIR / p.name
0042: 
0043: 
0044: def _classify_relative(path):
0045:     p = Path(os.fspath(path))
0046:     name = p.name.casefold()
0047:     parts = {x.casefold() for x in p.parts}
0048:     if "backup" in name or "backups" in parts:
```
```text
0041:     return DATA_DIR / p.name
0042: 
0043: 
0044: def _classify_relative(path):
0045:     p = Path(os.fspath(path))
0046:     name = p.name.casefold()
0047:     parts = {x.casefold() for x in p.parts}
0048:     if "backup" in name or "backups" in parts:
0049:         return BACKUP_DIR
0050:     if "report" in name or "reports" in parts:
0051:         return REPORTS_DIR
0052:     return DATA_DIR
0053: 
0054: 
0055: def _write_target(path, backup=False, report=False):
0056:     # File descriptors are not paths and must pass through unchanged.
0057:     if isinstance(path, int):
0058:         return path
0059:     p = Path(os.fspath(path))
0060:     if p.is_absolute():
0061:         if _inside(p, DATA_DIR) or _inside(p, BACKUP_DIR) or _inside(p, REPORTS_DIR):
```
```text
0055: def _write_target(path, backup=False, report=False):
0056:     # File descriptors are not paths and must pass through unchanged.
0057:     if isinstance(path, int):
0058:         return path
0059:     p = Path(os.fspath(path))
0060:     if p.is_absolute():
0061:         if _inside(p, DATA_DIR) or _inside(p, BACKUP_DIR) or _inside(p, REPORTS_DIR):
0062:             return p
0063:         if _is_database_path(p) and (_is_runtime_temp(p) or _inside(p, INSTALL_ROOT) or _inside(p, Path(sys.executable).parent)):
0064:             return _permanent_db_target(p)
0065:         if _inside(p, INSTALL_ROOT):
0066:             root = BACKUP_DIR if backup else REPORTS_DIR if report else DATA_DIR
0067:             return root / p.relative_to(INSTALL_ROOT)
0068:         return p
0069:     root = BACKUP_DIR if backup else REPORTS_DIR if report else _classify_relative(p)
0070:     return root / p
0071: 
0072: 
0073: def _read_target(path):
0074:     # File descriptors are not paths and must pass through unchanged.
0075:     if isinstance(path, int):
```
```text
0071: 
0072: 
0073: def _read_target(path):
0074:     # File descriptors are not paths and must pass through unchanged.
0075:     if isinstance(path, int):
0076:         return path
0077:     p = Path(os.fspath(path))
0078:     if p.is_absolute():
0079:         if _is_database_path(p) and (_inside(p, INSTALL_ROOT) or _inside(p, Path(sys.executable).parent) or _is_runtime_temp(p)):
0080:             candidate = _permanent_db_target(p)
0081:             if candidate.exists():
0082:                 return candidate
0083:             return candidate
0084:         return p
0085:     if p.name.casefold() in _CONFIG_FILES or p.name.casefold() in _RESOURCE_FILES:
0086:         return p
0087: 
0088:     # User/application data must always resolve to permanent storage. Do not
0089:     # fall back to the current working directory or PyInstaller temp folder.
0090:     root = _classify_relative(p)
0091:     return root / p
```
```text
0090:     root = _classify_relative(p)
0091:     return root / p
0092: 
0093: 
0094: def _is_write_mode(mode):
0095:     return any(ch in mode for ch in ("w", "a", "x", "+"))
0096: 
0097: 
0098: def _open(file, mode="r", *args, **kwargs):
0099:     if isinstance(file, int):
0100:         return _ORIGINAL_OPEN(file, mode, *args, **kwargs)
0101:     if _is_write_mode(mode):
0102:         file = _write_target(file)
0103:         Path(file).parent.mkdir(parents=True, exist_ok=True)
0104:     else:
0105:         file = _read_target(file)
0106:     return _ORIGINAL_OPEN(file, mode, *args, **kwargs)
0107: 
0108: 
0109: def _io_open(file, mode="r", *args, **kwargs):
0110:     if isinstance(file, int):
```
```text
0103:         Path(file).parent.mkdir(parents=True, exist_ok=True)
0104:     else:
0105:         file = _read_target(file)
0106:     return _ORIGINAL_OPEN(file, mode, *args, **kwargs)
0107: 
0108: 
0109: def _io_open(file, mode="r", *args, **kwargs):
0110:     if isinstance(file, int):
0111:         return _ORIGINAL_IO_OPEN(file, mode, *args, **kwargs)
0112:     if _is_write_mode(mode):
0113:         file = _write_target(file)
0114:         Path(file).parent.mkdir(parents=True, exist_ok=True)
0115:     else:
0116:         file = _read_target(file)
0117:     return _ORIGINAL_IO_OPEN(file, mode, *args, **kwargs)
0118: 
0119: 
0120: def _sqlite_connect(database, *args, **kwargs):
0121:     if isinstance(database, (str, os.PathLike)) and str(database) not in (":memory:", ""):
0122:         original = Path(os.fspath(database))
0123:         target = _write_target(original)
```
```text
0118: 
0119: 
0120: def _sqlite_connect(database, *args, **kwargs):
0121:     if isinstance(database, (str, os.PathLike)) and str(database) not in (":memory:", ""):
0122:         original = Path(os.fspath(database))
0123:         target = _write_target(original)
0124:         target.parent.mkdir(parents=True, exist_ok=True)
0125: 
0126:         # Migrate an older database into permanent storage exactly once. Carry
0127:         # SQLite WAL/SHM sidecars as well so committed transactions are not lost.
0128:         if original.is_absolute() and original != target and original.exists() and not target.exists():
0129:             try:
0130:                 shutil.copy2(original, target)
0131:                 for suffix in ("-wal", "-shm"):
0132:                     sidecar = Path(str(original) + suffix)
0133:                     if sidecar.exists():
0134:                         shutil.copy2(sidecar, Path(str(target) + suffix))
0135:             except OSError:
0136:                 pass
0137:         database = str(target)
0138:     return _ORIGINAL_SQLITE_CONNECT(database, *args, **kwargs)
```
```text
0134:                         shutil.copy2(sidecar, Path(str(target) + suffix))
0135:             except OSError:
0136:                 pass
0137:         database = str(target)
0138:     return _ORIGINAL_SQLITE_CONNECT(database, *args, **kwargs)
0139: 
0140: 
0141: def _copy2(src, dst, *args, **kwargs):
0142:     dst = _write_target(dst, backup="backup" in str(dst).casefold())
0143:     Path(dst).parent.mkdir(parents=True, exist_ok=True)
0144:     return _ORIGINAL_COPY2(src, dst, *args, **kwargs)
0145: 
0146: 
0147: def _copyfile(src, dst, *args, **kwargs):
0148:     dst = _write_target(dst, backup="backup" in str(dst).casefold())
0149:     Path(dst).parent.mkdir(parents=True, exist_ok=True)
0150:     return _ORIGINAL_COPYFILE(src, dst, *args, **kwargs)
0151: 
0152: 
0153: _ORIGINAL_OPEN = builtins.open
0154: _ORIGINAL_IO_OPEN = io.open
```
```text
0147: def _copyfile(src, dst, *args, **kwargs):
0148:     dst = _write_target(dst, backup="backup" in str(dst).casefold())
0149:     Path(dst).parent.mkdir(parents=True, exist_ok=True)
0150:     return _ORIGINAL_COPYFILE(src, dst, *args, **kwargs)
0151: 
0152: 
0153: _ORIGINAL_OPEN = builtins.open
0154: _ORIGINAL_IO_OPEN = io.open
0155: _ORIGINAL_SQLITE_CONNECT = sqlite3.connect
0156: _ORIGINAL_COPY2 = shutil.copy2
0157: _ORIGINAL_COPYFILE = shutil.copyfile
0158: 
0159: 
0160: def install():
0161:     DATA_DIR.mkdir(parents=True, exist_ok=True)
0162:     BACKUP_DIR.mkdir(parents=True, exist_ok=True)
0163:     REPORTS_DIR.mkdir(parents=True, exist_ok=True)
0164:     builtins.open = _open
0165:     io.open = _io_open
0166:     sqlite3.connect = _sqlite_connect
0167:     shutil.copy2 = _copy2
```

## store_inventory.py

- Lines: 5520
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-281), migrate_old_item_codes(283-297), seed_items(299-306), backup_database(308-441), restore_database(442-459), stock(461-466), fmt_num(468-470), to_iso_date(472-481), to_display_date(483-491), fiscal_year_key(493-504), fiscal_year_range(506-509), normalize_code(511-519), format_code(521-530), attach_code_mask(532-558), set_digits(535-540), key(541-551), paste(553-556), bind_add_to_list(560-581), on_enter(563-574), __init__(585-602), _check_for_updates(604-609), _setup_style(611-647), _shade(650-655), on_close(657-662), redo_network_setup(664-680), backup_now(682-689), restore_backup(691-709), _ctrl_f(711-723), _open_exact_find_text_popup(725-770), do_find(746-755), close(756-763), _global_enter(772-784), wipe(786-787), login(789-818), do_login(804-815), change_password(820-870), save_password(842-864), logout(872-877), home(879-905), _restore_dashboard_after_internal_close(907-921), _ensure_mdi_host(923-944), _internal_window(946-1062), normal_place(962-968), restore(969-984), maximize(985-999), minimize(1000-1029), close(1030-1055), open_inventory_codes_detail_flow(1064-1082), open_inventory_codes_with_filters(1084-1098), open_inventory_codes_report_window(1100-1326), tbtn(1118-1123), balance_as_of(1180-1190), build_nav(1192-1214), selected_prefix(1216-1225), load(1227-1259), page_move(1261-1262), page_first(1263-1263), page_last(1264-1268), on_nav(1272-1273), find_popup(1276-1295), search_fn(1278-1293), print_report(1298-1301), export_pdf(1303-1305), export_word(1306-1308), export_excel(1309-1311), open_menu_window(1328-1350), close_window(1338-1345), _manual_check_update(1352-1356), _show_current_version(1358-1362), build_menu_bar(1364-1411), open_calendar_picker(1413-1461), pick(1431-1433), redraw(1435-1447), nav(1449-1453), make_date_field(1463-1470), clearbody(1472-1498), run_action(1487-1492), _portable_print_current(1500-1511), portable_print_dialog(1513-1586), build_receipt(1540-1558), send(1559-1572), refresh_printers(1573-1579), preview_tree(1588-1600), set_page_actions(1602-1610), _add_transaction_new_button(1612-1629), _report_header(1631-1695), _report_footer(1697-1705), _grr_signature_block(1707-1723), _finish_page(1725-1726), _wrap_text_to_width(1728-1753), fits(1735-1735), _pdf_table_report(1755-1823), table_header(1777-1782), show_preview_window(1825-1898), _safe_report_name(1900-1903), print_preview_window(1905-1908), _fallback_pdf_export(1910-1943), esc(1914-1915), add(1918-1920), _save_entry_report(1945-1965), export_preview_pdf(1967-1996), export_preview_word(1998-2038), export_preview_excel(2040-2076), _auto_fit_tree_columns(2078-2103), make_tree(2105-2133), schedule_fit(2116-2126), fitted_insert(2127-2130), pick_item(2135-2156), choose(2136-2155), ld(2143-2147), sel(2149-2153), bind_item_lookup(2158-2175), lookup(2160-2173), _set_form_editable(2178-2191), walk(2181-2190), document_selector(2193-2227), refresh(2198-2209), selected(2210-2215), dashboard(2229-2341), load_details(2313-2337), _refresh_dashboard_kpis(2343-2357), dashboard_details(2359-2363), item_history(2365-2385), _ask_item_master_filters(2387-2471), finish(2440-2452), items(2473-2711), hierarchy(2514-2523), selected_prefix(2569-2582), balance_as_of(2584-2591), load(2593-2631), set_page(2633-2634), select_node(2636-2657), open_find(2663-2682), search_fn(2665-2680), visible_rows(2687-2689), print_inventory(2690-2694), export_inventory_word(2695-2697), export_inventory_excel(2698-2700), portable_inventory(2705-2707), inventory_codes(2713-2997), btn(2749-2754), close_editor(2790-2800), edit_cell(2802-2828), commit(2820-2826), rows_query(2830-2843), load(2845-2860), new_record(2862-2883), commit(2876-2880), selected_row(2885-2887), edit_record(2889-2897), save_record(2899-2942), delete_record(2944-2955), refresh(2957-2957), do_print(2958-2960), do_close(2961-2961), filter_grid(2979-2986), open_mto_inventory_flow(2999-3022), open_code_opening_flow(3024-3032), code_opening(3034-3035), _open_code_opening_popup(3037-3038), _open_code_opening_detail(3040-3283), norm(3110-3111), table_for(3113-3114), row_for(3116-3121), search_any_destination(3123-3136), desc_hit(3138-3142), clear_form(3144-3157), load_for_edit(3159-3180), check_duplicates(3182-3193), save_code(3198-3249), edit_action(3251-3255), delete_code(3257-3272), _mto_new_item_dialog(3285-3321), save(3301-3318), _item_filter_bar(3323-3335), _date_filter_bar(3337-3345), _ask_mto_inventory_filters(3347-3392), finish(3377-3385), mto_inventory(3394-3594), open_find(3428-3447), search_fn(3430-3445), hierarchy(3466-3470), rebuild_nav(3472-3483), mto_balance(3507-3516), load(3518-3560), set_page(3562-3562), select_node(3563-3572), visible_rows(3577-3577), do_print(3578-3582), export_word(3583-3585), export_excel(3586-3588), party_master(3596-3647), load(3606-3609), clear(3610-3614), new_form(3615-3616), save(3617-3623), load_party_row(3624-3628), on_party_select(3629-3630), edit(3632-3636), delete_party(3637-3643), user_management(3649-3733), sync_role(3676-3681), load(3685-3688), clear(3689-3692), edit(3693-3700), save(3701-3718), delete_user(3719-3730), _renumber_tree(3736-3739), demand(3741-3905), _restore_demand_tree_columns(3784-3790), add(3793-3801), edit_item(3803-3815), delete_item(3817-3825), new_form(3829-3835), save(3837-3853), delete_current(3857-3863), cancel_form(3864-3872), preview_now(3873-3883), edit_saved_demand(3884-3887), print_now(3888-3898), load_demand_into_form(3907-3919), refresh_saved_cache(3921-3933), grr(3935-4098), add(3967-3975), edit_item(3977-3987), delete_item(3989-3997), new_form(4001-4007), save(4009-4030), delete_current(4034-4040), cancel_form(4041-4049), preview_now(4050-4068), portable_current(4069-4072), edit_saved_grr(4074-4077), print_now(4078-4091), load_grr_into_form(4100-4112), issue(4114-4260), old_issue_qty(4143-4146), update_balance(4147-4155), add(4157-4166), edit_item(4168-4179), new_form(4183-4189), post(4191-4212), delete_current(4213-4219), cancel_form(4220-4228), preview_now(4229-4236), portable_current(4237-4239), load_saved_issue(4244-4246), edit_saved_issue(4247-4250), print_issue_now(4251-4256), load_issue_into_form(4262-4275), _ask_report_criteria(4277-4340), finish(4326-4334), _open_report_child(4342-4347), open_stock_balance_report_flow(4349-4352), open_grr_report_flow(4354-4357), open_demand_report_flow(4359-4362), open_issue_report_flow(4364-4367), open_party_report_flow(4369-4372), _ask_stock_balance_filters(4374-4397), ok(4389-4390), cancel(4391-4391), stock_balance(4399-4462), period(4415-4426), header_summary(4427-4428), load(4429-4438), reopen_filters(4439-4443), open_find_stock(4447-4460), search_fn(4449-4459), ledger(4464-4476), open_document_editor(4478-4486), _edit_from_selector(4488-4504), show_saved_records(4506-4537), view(4529-4533), documents(4539-4584), edit_selected(4558-4564), delete_selected(4565-4577), doc_export_selected(4586-4592), doc_preview_selected(4594-4604), doc_print_selected(4606-4614), load_document(4616-4646), _print_loaded_document(4640-4645), _report_filter_popup(4648-4665), ok(4661-4662), cancel(4663-4663), _report_window(4667-4711), load(4680-4687), hdr(4688-4688), open_find_report(4694-4708), search_fn(4696-4707), report_grr(4713-4724), pb(4715-4723), report_demand(4726-4737), pb(4728-4736), report_issue(4739-4748), pb(4741-4747), report_party(4750-4760), pb(4752-4759), reports(4762-4890), load_grr_item(4775-4780), load_grr_date(4788-4796), load_party(4808-4816), load_dem_item(4829-4834), load_dem_date(4842-4850), load_iss_item(4864-4869), load_iss_date(4877-4885), print_item_master(4892-4894), print_party_master(4896-4898), print_report(4900-4914), print_stock(4916-4921), print_ledger(4923-4930), _get_doc_data(4932-4960), export_word(4962-5009), export_excel(5011-5051), preview_pdf(5053-5061), _open_direct_printer(5063-5093), _select_windows_printer_for_pdf(5095-5466), render_preview(5220-5239), on_resize(5241-5243), parse_page_selection(5262-5278), selected_printer(5280-5282), print_rendered_pages(5284-5442), close(5444-5454), print_pdf(5468-5486), open_file(5488-5493), print_demand(5495-5500), print_grr(5502-5510), print_issue(5512-5517)

### Relevant source locations

```text
0001: 
0002: import csv, sqlite3, os, sys, subprocess, webbrowser, shutil, zipfile, hashlib, secrets, calendar, textwrap, ctypes
0003: import updater
0004: import durable_local
0005: from datetime import datetime
0006: import tkinter as tk
0007: from tkinter import ttk, messagebox
0008: 
0009: try:
0010:     import fitz  # PyMuPDF: render the exact report PDF for print preview/printing
0011:     FITZ_AVAILABLE=True
0012: except Exception:
0013:     FITZ_AVAILABLE=False
0014:     fitz=None
```
```text
0015: 
0016: try:
0017:     from PIL import Image, ImageTk, ImageWin
0018:     PIL_AVAILABLE=True
0019: except Exception:
0020:     PIL_AVAILABLE=False
0021:     Image=ImageTk=ImageWin=None
0022: 
0023: from firebase_sync import FirebaseSync, OnlineConnection
0024: 
0025: try:
0026:     from reportlab.lib.pagesizes import A4, landscape
0027:     from reportlab.pdfgen import canvas
0028:     from reportlab.pdfbase.pdfmetrics import stringWidth
0029:     REPORTLAB=True
0030: except Exception:
0031:     REPORTLAB=False
0032: 
0033: try:
0034:     from docx import Document
0035:     DOCX_AVAILABLE=True
```
```text
0063: # ---------------------------------------------------------------------------
0064: # MULTI-COMPUTER SHARED DATA
0065: #
0066: # One computer is the "Main" computer: its Data folder is what everyone
0067: # actually reads and writes to. Every other computer is a "Connected"
0068: # computer: it does NOT keep its own copy of the data, it points straight
0069: # at the Main computer's shared Data folder over the network
0070: # (e.g. \\MAIN-PC\StoreInventoryData). That way every laptop always shows
0071: # the exact same, live data - there is only ever one real database file.
0072: #
0073: # This choice is made once, the first time the program runs on a computer,
0074: # and remembered in CONFIG_FILE from then on.
0075: # ---------------------------------------------------------------------------
0076: if os.name == "nt":
0077:     INSTALL_DIR = r"C:\StoreInventoryManagement"
0078: else:
0079:     INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))  # dev/testing only
0080: 
0081: os.makedirs(INSTALL_DIR, exist_ok=True)
0082: # ONLINE DATABASE CONFIGURATION
0083: # Only a Firebase Realtime Database URL is required. No Firebase API key is
```
```text
0078: else:
0079:     INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))  # dev/testing only
0080: 
0081: os.makedirs(INSTALL_DIR, exist_ok=True)
0082: # ONLINE DATABASE CONFIGURATION
0083: # Only a Firebase Realtime Database URL is required. No Firebase API key is
0084: # used by this desktop app. The file is intentionally separate from the UI so
0085: # the existing interface remains unchanged.
0086: FIREBASE_URL_FILE = os.path.join(INSTALL_DIR, "firebase_database_url.txt")
0087: BACKUP_DIR = os.path.join(INSTALL_DIR, "Backups")   # local safety backups
0088: REPORTS_DIR = os.path.join(INSTALL_DIR, "Reports")  # local reports
0089: os.makedirs(BACKUP_DIR, exist_ok=True)
0090: os.makedirs(REPORTS_DIR, exist_ok=True)
0091: 
0092: # Keep the old local Data folder name for backwards compatibility and for the
0093: # existing Home-screen Data label. The actual shared source of truth is now
0094: # Firebase; this local SQLite file is the app's private cache.
0095: DATA_DIR = os.path.join(INSTALL_DIR, "Data")
0096: os.makedirs(DATA_DIR, exist_ok=True)
0097: BASE=REPORTS_DIR
0098: DB=os.path.join(DATA_DIR,"store_inventory.db")
```
```text
0094: # Firebase; this local SQLite file is the app's private cache.
0095: DATA_DIR = os.path.join(INSTALL_DIR, "Data")
0096: os.makedirs(DATA_DIR, exist_ok=True)
0097: BASE=REPORTS_DIR
0098: DB=os.path.join(DATA_DIR,"store_inventory.db")
0099: SEED=resource_path("inventory_seed.csv")
0100: COMPANY="Hunza Citrus and Pulp (Private) Limited"
0101: LOGO_FILE=resource_path("company_logo.png")
0102: REPORT_FOOTER="Generated by Store Inventory Management"
0103: DEPARTMENTS=["Administration","Production","Mechanical","Electrical","Finance"]
0104: # Standard Unit-of-Measure choices offered on Inventory Codes / Item Master.
0105: # Shown as a dropdown but left editable, so an uncommon unit can still be typed.
0106: UOM_OPTIONS=["NOS","FT","LTR","PKT","KG","MTR","PCS","SET","BOX","BAG","ROLL","GM","TON","DZN"]
0107: 
0108: # ---------------------------------------------------------------------------
0109: # PROFESSIONAL COLOR PALETTE (used to theme the whole application)
0110: # ---------------------------------------------------------------------------
0111: COLORS={
0112:     "primary":      "#1565C0",   # main brand blue
0113:     "primary_dark": "#0D47A1",   # header bar / hover
0114:     "accent":       "#00897B",   # teal accent
```
```text
0107: 
0108: # ---------------------------------------------------------------------------
0109: # PROFESSIONAL COLOR PALETTE (used to theme the whole application)
0110: # ---------------------------------------------------------------------------
0111: COLORS={
0112:     "primary":      "#1565C0",   # main brand blue
0113:     "primary_dark": "#0D47A1",   # header bar / hover
0114:     "accent":       "#00897B",   # teal accent
0115:     "success":      "#2E7D32",   # save / positive actions
0116:     "warning":      "#EF6C00",   # edit / caution actions
0117:     "danger":       "#C62828",   # delete / logout actions
0118:     "muted":        "#607D8B",   # secondary / cancel actions
0119:     "bg":           "#EEF2F7",   # app background
0120:     "card_bg":      "#FFFFFF",   # cards / trees
0121:     "text_dark":    "#1B2430",
0122: }
0123: 
0124: def hash_password(password, salt=None):
0125:     """Simple salted SHA-256 hash, stored as 'salt$hash'. Not for internet-
0126:     facing use, but a reasonable step up from plaintext for a LAN app."""
0127:     salt = salt or secrets.token_hex(8)
```
```text
0128:     h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
0129:     return f"{salt}${h}"
0130: 
0131: def verify_password(password, stored):
0132:     if not stored or "$" not in stored: return False
0133:     salt, _ = stored.split("$", 1)
0134:     return hash_password(password, salt) == stored
0135: 
0136: def _copy_legacy_database_if_needed():
0137:     """Migrate the previous LAN/shared SQLite database into this PC's local
0138:     cache once. This preserves existing records when upgrading the old build."""
0139:     if os.path.exists(DB):
0140:         return
0141:     legacy_cfg = os.path.join(INSTALL_DIR, "network_config.txt")
0142:     if not os.path.exists(legacy_cfg):
0143:         return
0144:     try:
0145:         with open(legacy_cfg, encoding="utf-8") as f:
0146:             legacy_dir = f.read().strip()
0147:         if not legacy_dir:
0148:             return
```
```text
0236:     demand_lines_cols={r[1] for r in c.execute("PRAGMA table_info(demand_lines)").fetchall()}
0237:     if "item_type" not in demand_lines_cols: c.execute("ALTER TABLE demand_lines ADD COLUMN item_type TEXT DEFAULT 'Local'")
0238:     grr_lines_cols={r[1] for r in c.execute("PRAGMA table_info(grr_lines)").fetchall()}
0239:     if "item_type" not in grr_lines_cols: c.execute("ALTER TABLE grr_lines ADD COLUMN item_type TEXT DEFAULT 'Local'")
0240:     issue_lines_cols={r[1] for r in c.execute("PRAGMA table_info(issue_lines)").fetchall()}
0241:     if "item_type" not in issue_lines_cols: c.execute("ALTER TABLE issue_lines ADD COLUMN item_type TEXT DEFAULT 'Local'")
0242:     txn_cols={r[1] for r in c.execute("PRAGMA table_info(transactions)").fetchall()}
0243:     if "item_type" not in txn_cols: c.execute("ALTER TABLE transactions ADD COLUMN item_type TEXT DEFAULT 'Local'")
0244:     c.commit()
0245: 
0246: 
0247: def connect():
0248:     _copy_legacy_database_if_needed()
0249:     raw = sqlite3.connect(DB, timeout=20)
0250:     _init_schema(raw)
0251:     seed_items(raw)
0252:     migrate_old_item_codes(raw)
0253:     try:
0254:         durable_local.restore_if_newer(raw)
0255:     except Exception:
0256:         pass
```
```text
0250:     _init_schema(raw)
0251:     seed_items(raw)
0252:     migrate_old_item_codes(raw)
0253:     try:
0254:         durable_local.restore_if_newer(raw)
0255:     except Exception:
0256:         pass
0257: 
0258:     sync = FirebaseSync(FIREBASE_URL_FILE, INSTALL_DIR)
0259:     if sync.enabled:
0260:         try:
0261:             # Established installations open immediately from the durable local cache.
0262:             # Firebase refresh runs in the background and is applied on a later read.
0263:             state_ready = os.path.isfile(sync.state_path) and os.path.getsize(sync.state_path) > 2
0264:             if state_ready:
0265:                 sync.kick_background_pull(force=True)
0266:             else:
0267:                 # First install still receives cloud data before use, with the short
0268:                 # Firebase timeout configured in firebase_sync.py.
0269:                 sync.initialize(raw)
0270:                 _init_schema(raw)
```
```text
0270:                 _init_schema(raw)
0271:         except Exception as exc:
0272:             sync.pending_error = str(exc)
0273:     try:
0274:         # Do not rewrite a full JSON recovery snapshot on every launch.
0275:         # Commits still update the durable snapshot exactly as before.
0276:         snap_path = getattr(durable_local, "SNAPSHOT_PATH", None)
0277:         if not snap_path or not os.path.exists(os.fspath(snap_path)):
0278:             durable_local.save(raw)
0279:     except Exception:
0280:         pass
0281:     return OnlineConnection(DB, sync)
0282: 
0283: def migrate_old_item_codes(c):
0284:     """Migrate old 00-00-00-0000 item codes to 00-00-0000 everywhere."""
0285:     rows=c.execute("SELECT code FROM items").fetchall()
0286:     for (old,) in rows:
0287:         digits="".join(ch for ch in str(old) if ch.isdigit())
0288:         if len(digits)!=10: continue
0289:         new=format_code(digits)
0290:         if not new or new==old: continue
```
```text
0289:         new=format_code(digits)
0290:         if not new or new==old: continue
0291:         if c.execute("SELECT 1 FROM items WHERE code=?",(new,)).fetchone():
0292:             # Do not destroy an existing code; leave this collision visible for manual resolution.
0293:             continue
0294:         c.execute("UPDATE items SET code=? WHERE code=?",(new,old))
0295:         for table,col in (("demand_lines","code"),("grr_lines","code"),("issue_lines","code"),("transactions","code")):
0296:             c.execute(f"UPDATE {table} SET {col}=? WHERE {col}=?",(new,old))
0297:     c.commit()
0298: 
0299: def seed_items(c):
0300:     if c.execute("SELECT COUNT(*) FROM items").fetchone()[0]: return
0301:     if not os.path.exists(SEED): return
0302:     with open(SEED,encoding="utf-8-sig") as f:
0303:         for r in csv.DictReader(f):
0304:             c.execute("INSERT OR IGNORE INTO items(code,description,uom) VALUES(?,?,?)",
0305:                       (format_code(r.get("code","").strip()),r.get("description","").strip(),r.get("uom","").strip()))
0306:     c.commit()
0307: 
0308: def backup_database(manual=False):
0309:     """Create a consistent full SQLite backup in C:\StoreInventoryManagement\Backups."""
```
```text
0303:         for r in csv.DictReader(f):
0304:             c.execute("INSERT OR IGNORE INTO items(code,description,uom) VALUES(?,?,?)",
0305:                       (format_code(r.get("code","").strip()),r.get("description","").strip(),r.get("uom","").strip()))
0306:     c.commit()
0307: 
0308: def backup_database(manual=False):
0309:     """Create a consistent full SQLite backup in C:\StoreInventoryManagement\Backups."""
0310:     try:
0311:         os.makedirs(BACKUP_DIR, exist_ok=True)
0312: 
0313:         # The live database is permanently under C:\StoreInventoryManagement\Data.
0314:         # Also accept the legacy DB variable/path and any SQLite file already
0315:         # present in the install tree so Backup Now never depends on the old
0316:         # pre-online database location.
0317:         known = []
0318:         try:
0319:             legacy_db = globals().get("DB")
0320:             if legacy_db:
0321:                 known.append(os.path.abspath(os.fspath(legacy_db)))
0322:         except Exception:
0323:             pass
```
```text
0321:                 known.append(os.path.abspath(os.fspath(legacy_db)))
0322:         except Exception:
0323:             pass
0324:         known.extend([
0325:             os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db"),
0326:             os.path.join(r"C:\StoreInventoryManagement", "Data", "inventory.db"),
0327:             os.path.join(r"C:\StoreInventoryManagement", "store_inventory.db"),
0328:         ])
0329:         db_candidates = []
0330:         for p in known:
0331:             if p and p not in db_candidates:
0332:                 db_candidates.append(p)
0333:         # Discover the actual SQLite file if its legacy filename differs.
0334:         for root in (
0335:             os.path.join(r"C:\StoreInventoryManagement", "Data"),
0336:             r"C:\StoreInventoryManagement",
0337:         ):
0338:             try:
0339:                 if os.path.isdir(root):
0340:                     for name in os.listdir(root):
0341:                         if os.path.splitext(name)[1].lower() in (".db", ".sqlite", ".sqlite3", ".db3"):
```
```text
0335:             os.path.join(r"C:\StoreInventoryManagement", "Data"),
0336:             r"C:\StoreInventoryManagement",
0337:         ):
0338:             try:
0339:                 if os.path.isdir(root):
0340:                     for name in os.listdir(root):
0341:                         if os.path.splitext(name)[1].lower() in (".db", ".sqlite", ".sqlite3", ".db3"):
0342:                             p = os.path.join(root, name)
0343:                             if p not in db_candidates:
0344:                                 db_candidates.append(p)
0345:             except Exception:
0346:                 pass
0347: 
0348:         db_path = next((p for p in db_candidates if os.path.isfile(p)), None)
0349:         if not db_path:
0350:             # Create the expected database path if the database has not yet
0351:             # been materialized by the storage layer.
0352:             db_path = os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db")
0353:             try:
0354:                 os.makedirs(os.path.dirname(db_path), exist_ok=True)
0355:                 probe = sqlite3.connect(db_path, timeout=30)
```
```text
0348:         db_path = next((p for p in db_candidates if os.path.isfile(p)), None)
0349:         if not db_path:
0350:             # Create the expected database path if the database has not yet
0351:             # been materialized by the storage layer.
0352:             db_path = os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db")
0353:             try:
0354:                 os.makedirs(os.path.dirname(db_path), exist_ok=True)
0355:                 probe = sqlite3.connect(db_path, timeout=30)
0356:                 probe.close()
0357:             except Exception:
0358:                 return None
0359:             if not os.path.isfile(db_path):
0360:                 return None
0361: 
0362:         stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
0363:         tag = "manual" if manual else "auto"
0364:         latest = os.path.join(BACKUP_DIR, "inventory_backup_latest.db")
0365:         dated = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.db")
0366:         zpath = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.zip")
0367: 
0368:         src = sqlite3.connect(db_path, timeout=30)
```
```text
0366:         zpath = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.zip")
0367: 
0368:         src = sqlite3.connect(db_path, timeout=30)
0369:         try:
0370:             try:
0371:                 src.execute("PRAGMA wal_checkpoint(FULL)")
0372:             except Exception:
0373:                 pass
0374:             dst = sqlite3.connect(dated, timeout=30)
0375:             try:
0376:                 with dst:
0377:                     src.backup(dst)
0378:             finally:
0379:                 dst.close()
0380:         finally:
0381:             src.close()
0382: 
0383:         # Keep the latest convenience copy, replacing only that fixed filename.
0384:         # Historical/manual backup archives are never automatically deleted.
0385:         if os.path.exists(latest):
0386:             try:
```
```text
0382: 
0383:         # Keep the latest convenience copy, replacing only that fixed filename.
0384:         # Historical/manual backup archives are never automatically deleted.
0385:         if os.path.exists(latest):
0386:             try:
0387:                 os.remove(latest)
0388:             except OSError:
0389:                 pass
0390:         latest_src = sqlite3.connect(dated, timeout=30)
0391:         try:
0392:             latest_dst = sqlite3.connect(latest, timeout=30)
0393:             try:
0394:                 with latest_dst:
0395:                     latest_src.backup(latest_dst)
0396:             finally:
0397:                 latest_dst.close()
0398:         finally:
0399:             latest_src.close()
0400: 
0401:         if not os.path.isfile(dated) or os.path.getsize(dated) <= 0:
0402:             return None
```
```text
0399:             latest_src.close()
0400: 
0401:         if not os.path.isfile(dated) or os.path.getsize(dated) <= 0:
0402:             return None
0403:         with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
0404:             z.write(dated, "store_inventory.db")
0405:         if not os.path.isfile(zpath) or os.path.getsize(zpath) <= 0:
0406:             return None
0407:         # Also store a cloud copy of the same complete database snapshot.
0408:         # This uses the Firebase Realtime Database URL only; no API key is needed.
0409:         # A cloud-backup failure never invalidates an already-created local backup.
0410:         try:
0411:             import requests
0412:             url_file = Path(__file__).resolve().parent / "firebase_database_url.txt"
0413:             base_url = ""
0414:             if url_file.exists():
0415:                 for line in url_file.read_text(encoding="utf-8-sig").splitlines():
0416:                     line = line.strip()
0417:                     if line and not line.startswith("#"):
0418:                         base_url = line.rstrip("/")
0419:                         break
```
```text
0414:             if url_file.exists():
0415:                 for line in url_file.read_text(encoding="utf-8-sig").splitlines():
0416:                     line = line.strip()
0417:                     if line and not line.startswith("#"):
0418:                         base_url = line.rstrip("/")
0419:                         break
0420:             if base_url:
0421:                 cloud_stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
0422:                 cloud_url = f"{base_url}/store_inventory/backups/{cloud_stamp}.json"
0423:                 with open(dated, "rb") as bf:
0424:                     import base64
0425:                     encoded = base64.b64encode(bf.read()).decode("ascii")
0426:                 response = requests.put(
0427:                     cloud_url,
0428:                     json={
0429:                         "created_at": cloud_stamp,
0430:                         "type": "sqlite_backup",
0431:                         "filename": os.path.basename(zpath),
0432:                         "database_base64": encoded,
0433:                     },
0434:                     timeout=30,
```
```text
0434:                     timeout=30,
0435:                 )
0436:                 response.raise_for_status()
0437:         except Exception:
0438:             pass
0439:         return zpath
0440:     except Exception:
0441:         return None
0442: def restore_database(backup_path):
0443:     """Restore the database from a .db or .zip backup file. The current
0444:     database is itself backed up first, so a restore can never destroy data."""
0445:     try:
0446:         backup_database(manual=True)  # safety net before touching anything
0447:         if backup_path.lower().endswith(".zip"):
0448:             with zipfile.ZipFile(backup_path,"r") as z:
0449:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0450:                 os.makedirs(tmp_dir,exist_ok=True)
0451:                 z.extractall(tmp_dir)
0452:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0453:                 shutil.copy2(extracted,DB)
0454:                 shutil.rmtree(tmp_dir,ignore_errors=True)
```
```text
0448:             with zipfile.ZipFile(backup_path,"r") as z:
0449:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0450:                 os.makedirs(tmp_dir,exist_ok=True)
0451:                 z.extractall(tmp_dir)
0452:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0453:                 shutil.copy2(extracted,DB)
0454:                 shutil.rmtree(tmp_dir,ignore_errors=True)
0455:         else:
0456:             shutil.copy2(backup_path,DB)
0457:         return True
0458:     except Exception:
0459:         return False
0460: 
0461: def stock(c, code):
0462:     r=c.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()
0463:     q=float(r[0] or 0) if r else 0
0464:     for typ,qty in c.execute("SELECT doc_type,qty FROM transactions WHERE code=? ORDER BY id", (code,)):
0465:         q += float(qty or 0) if typ=="GRR" else -float(qty or 0) if typ=="ISSUE" else 0
0466:     return q
0467: 
0468: def fmt_num(x):
```
```text
0466:     return q
0467: 
0468: def fmt_num(x):
0469:     x=float(x or 0)
0470:     return f"{x:,.2f}".rstrip("0").rstrip(".")
0471: 
0472: def to_iso_date(s):
0473:     """Convert a user-entered DD/MM/YYYY date (or an already-ISO date) into
0474:     ISO YYYY-MM-DD for storage in the database and for date-range queries,
0475:     which rely on ISO strings sorting/comparing correctly."""
0476:     s=(s or "").strip()
0477:     if not s: return ""
0478:     for f in ("%d/%m/%Y","%Y-%m-%d"):
0479:         try: return datetime.strptime(s,f).strftime("%Y-%m-%d")
0480:         except Exception: continue
0481:     return s
0482: 
0483: def to_display_date(s):
0484:     """Convert an ISO YYYY-MM-DD date (as stored in the database) into the
0485:     DD/MM/YYYY format used everywhere on screen and on printed reports."""
0486:     s=(s or "").strip()
```
```text
0581:     return on_enter
0582: 
0583: 
0584: class App(tk.Tk):
0585:     def __init__(self):
0586:         super().__init__()
0587:         self.title("Store Inventory Management System | SAP Style")
0588:         self.geometry("1400x820"); self.minsize(1150,700)
0589:         self.conn=connect()
0590:         self.demand_lines=[]; self.grr_lines=[]; self.issue_lines=[]
0591:         self.current_user=None; self.current_role=None
0592:         self._item_master_search_entry=None
0593:         self._item_master_find_callback=None
0594:         self._portable_print_context=None
0595:         self.can_edit=False; self.can_delete=False; self.is_admin=False
0596:         self._setup_style()
0597:         # Any focused button can be activated with Enter.
0598:         self.bind_all("<Return>", self._global_enter, add="+")
0599:         self.bind_all("<KP_Enter>", self._global_enter, add="+")
0600:         self.bind_all("<Control-f>", self._ctrl_f, add="+")
0601:         self.protocol("WM_DELETE_WINDOW", self.on_close)
```
```text
0649:     @staticmethod
0650:     def _shade(hexcolor, factor):
0651:         """Return a slightly darker version of a #RRGGBB color (for hover/press states)."""
0652:         h=hexcolor.lstrip("#")
0653:         r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
0654:         r,g,b=(max(0,int(v*factor)) for v in (r,g,b))
0655:         return f"#{r:02x}{g:02x}{b:02x}"
0656: 
0657:     def on_close(self):
0658:         try:
0659:             self.conn.commit(); backup_database()
0660:         except Exception:
0661:             pass
0662:         self.destroy()
0663: 
0664:     def redo_network_setup(self):
0665:         if not messagebox.askyesno("Network Setup",
0666:             "This will clear the online database URL saved on this computer.\n\n"
0667:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0668:             "Continue?"):
0669:             return
```
```text
0663: 
0664:     def redo_network_setup(self):
0665:         if not messagebox.askyesno("Network Setup",
0666:             "This will clear the online database URL saved on this computer.\n\n"
0667:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0668:             "Continue?"):
0669:             return
0670:         try:
0671:             self.conn.commit(); backup_database()
0672:         except Exception:
0673:             pass
0674:         try:
0675:             if os.path.exists(FIREBASE_URL_FILE): os.remove(FIREBASE_URL_FILE)
0676:         except Exception:
0677:             pass
0678:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0679:         self.destroy()
0680:         sys.exit(0)
0681: 
0682:     def backup_now(self):
0683:         path=backup_database(manual=True)
```
```text
0677:             pass
0678:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0679:         self.destroy()
0680:         sys.exit(0)
0681: 
0682:     def backup_now(self):
0683:         path=backup_database(manual=True)
0684:         if path:
0685:             messagebox.showinfo("Backup Complete",
0686:                 f"A full backup was saved to:\n\n{path}\n\n"
0687:                 f"All backups are kept in:\n{BACKUP_DIR}")
0688:         else:
0689:             messagebox.showerror("Backup Failed","Could not create a backup. Make sure the database exists.")
0690: 
0691:     def restore_backup(self):
0692:         from tkinter import filedialog
0693:         if not messagebox.askyesno("Restore Backup",
0694:             "This will replace all current data with the selected backup.\n"
0695:             "A safety backup of the current data will be made first.\n\n"
0696:             "Continue?"):
0697:             return
```
```text
0691:     def restore_backup(self):
0692:         from tkinter import filedialog
0693:         if not messagebox.askyesno("Restore Backup",
0694:             "This will replace all current data with the selected backup.\n"
0695:             "A safety backup of the current data will be made first.\n\n"
0696:             "Continue?"):
0697:             return
0698:         path=filedialog.askopenfilename(
0699:             title="Select a backup file",
0700:             initialdir=BACKUP_DIR,
0701:             filetypes=[("Backup files","*.zip *.db"),("All files","*.*")])
0702:         if not path: return
0703:         if restore_database(path):
0704:             messagebox.showinfo("Restore Complete",
0705:                 "Data has been restored. The application will now restart.")
0706:             self.conn.close()
0707:             os.execv(sys.executable, [sys.executable]+sys.argv)
0708:         else:
0709:             messagebox.showerror("Restore Failed","Could not restore from that backup file.")
0710: 
0711:     def _ctrl_f(self, event=None):
```
```text
0748:             if not text:
0749:                 fe.focus_set(); return
0750:             try:
0751:                 found=search_fn(text)
0752:             except Exception:
0753:                 found=False
0754:             if found is False:
0755:                 messagebox.showinfo("Find Text","No matching text found.",parent=dlg)
0756:         def close():
0757:             try:
0758:                 dlg.grab_release()
0759:             except Exception: pass
0760:             try: dlg.destroy()
0761:             except Exception: pass
0762:             if getattr(self,"_exact_find_text_dialog",None) is dlg:
0763:                 self._exact_find_text_dialog=None
0764:         ttk.Button(box,text="Find Next",command=do_find,width=13).grid(row=0,column=3,padx=4,pady=4)
0765:         ttk.Button(box,text="Cancel",command=close,width=13).grid(row=1,column=3,padx=4,pady=4)
0766:         fe.bind("<Return>",lambda e:(do_find(),"break"))
0767:         dlg.bind("<Escape>",lambda e:close())
0768:         dlg.protocol("WM_DELETE_WINDOW",close)
```
```text
0834:         cur_ent=ttk.Entry(box,textvariable=current,width=28,show="*"); cur_ent.grid(row=2,column=1,pady=7)
0835:         ttk.Label(box,text="New Password").grid(row=3,column=0,sticky="w",pady=7)
0836:         new_ent=ttk.Entry(box,textvariable=new,width=28,show="*"); new_ent.grid(row=3,column=1,pady=7)
0837:         ttk.Label(box,text="Confirm New Password").grid(row=4,column=0,sticky="w",pady=7)
0838:         conf_ent=ttk.Entry(box,textvariable=confirm,width=28,show="*"); conf_ent.grid(row=4,column=1,pady=7)
0839:         err=ttk.Label(box,text="",foreground="#c0392b",wraplength=380,justify="left")
0840:         err.grid(row=5,column=0,columnspan=2,pady=(5,8))
0841: 
0842:         def save_password(event=None):
0843:             old_pw=current.get()
0844:             new_pw=new.get()
0845:             confirm_pw=confirm.get()
0846:             row=self.conn.execute("SELECT password FROM users WHERE username=?",(self.current_user,)).fetchone()
0847:             if not row or not verify_password(old_pw,row[0]):
0848:                 err.config(text="Current password is incorrect."); return
0849:             if len(new_pw) < 4:
0850:                 err.config(text="New password must be at least 4 characters."); return
0851:             if new_pw != confirm_pw:
0852:                 err.config(text="New password and confirmation do not match."); return
0853:             if new_pw == old_pw:
0854:                 err.config(text="New password must be different from the current password."); return
```
```text
0850:                 err.config(text="New password must be at least 4 characters."); return
0851:             if new_pw != confirm_pw:
0852:                 err.config(text="New password and confirmation do not match."); return
0853:             if new_pw == old_pw:
0854:                 err.config(text="New password must be different from the current password."); return
0855:             try:
0856:                 self.conn.execute("UPDATE users SET password=? WHERE username=?",
0857:                                   (hash_password(new_pw),self.current_user))
0858:                 self.conn.commit()
0859:                 backup_database()
0860:                 win.grab_release(); win.destroy()
0861:                 messagebox.showinfo("Password Changed",
0862:                     "Your password has been changed successfully.\n\nUse the new password the next time you log in.", parent=self)
0863:             except Exception as ex:
0864:                 err.config(text=f"Could not change password: {ex}")
0865: 
0866:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0867:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0868:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0869:         conf_ent.bind("<Return>",save_password)
0870:         cur_ent.focus_set()
```
```text
0866:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0867:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0868:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0869:         conf_ent.bind("<Return>",save_password)
0870:         cur_ent.focus_set()
0871: 
0872:     def logout(self):
0873:         try:
0874:             self.conn.commit(); backup_database()
0875:         except Exception:
0876:             pass
0877:         self.login()
0878: 
0879:     def home(self):
0880:         self.wipe()
0881:         self.build_menu_bar()
0882:         hdr=tk.Frame(self,bg=COLORS["primary_dark"]);hdr.pack(fill="x")
0883:         self._shell_header=hdr
0884:         inner=tk.Frame(hdr,bg=COLORS["primary_dark"],padx=16,pady=10);inner.pack(fill="x")
0885:         tk.Label(inner,text=COMPANY,font=("Segoe UI",16,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="left")
0886:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
```
```text
0886:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
0887:         tk.Label(inner,text=f"Data: {DATA_DIR}",font=("Segoe UI",8),bg=COLORS["primary_dark"],fg="#9FB8DA").pack(side="left",padx=14)
0888:         ttk.Button(inner,text="Logout",style="Danger.TButton",command=self.logout).pack(side="right")
0889:         tk.Label(inner,text=f"{self.current_user}  ({self.current_role})",font=("Segoe UI",9,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="right",padx=12)
0890:         nav=tk.Frame(self,bg=COLORS["primary"]);nav.pack(fill="x")
0891:         self._shell_nav=nav
0892:         navin=tk.Frame(nav,bg=COLORS["primary"],padx=10,pady=6);navin.pack(fill="x")
0893:         ttk.Button(navin,text="🏠  Dashboard",style="Accent.TButton",command=self.dashboard).pack(side="left",padx=3)
0894:         tk.Label(navin,text="Inventory  |  Transaction  |  Report  |  Edit  |  Help  —  see the menu bar above for every other section.",
0895:                  font=("Segoe UI",8),bg=COLORS["primary"],fg="#E7EFFB").pack(side="left",padx=14)
0896:         self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
0897:         self.main_body=self.body
0898:         self.dashboard()
0899:         if not getattr(self, "_update_checked_this_session", False):
0900:             self._update_checked_this_session = True
0901:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0902:         if not getattr(self, "_update_checked_this_session", False):
0903:             self._update_checked_this_session = True
0904:             # Startup check is silent: show a popup only when a newer version exists.
0905:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0906: 
```
```text
0899:         if not getattr(self, "_update_checked_this_session", False):
0900:             self._update_checked_this_session = True
0901:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0902:         if not getattr(self, "_update_checked_this_session", False):
0903:             self._update_checked_this_session = True
0904:             # Startup check is silent: show a popup only when a newer version exists.
0905:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0906: 
0907:     def _restore_dashboard_after_internal_close(self):
0908:         try:
0909:             if getattr(self, "_mdi_windows", []):
0910:                 return
0911:             host = getattr(self, "_mdi_host", None)
0912:             if host is not None and host.winfo_exists():
0913:                 host.place_forget()
0914:             # Repaint the existing Dashboard only after the child is fully closed.
0915:             # This restores the visible Dashboard surface without changing its layout.
0916:             self.after_idle(self.home)
0917:         except Exception:
0918:             try:
0919:                 self.after_idle(self.dashboard)
```
```text
1022:             xb.pack(side="left")
1023:             old_task=state.get("task")
1024:             try:
1025:                 if old_task is not None and old_task is not item and old_task.winfo_exists():
1026:                     old_task.destroy()
1027:             except Exception:
1028:                 pass
1029:             state["task"]=item
1030:         def close():
1031:             try:
1032:                 task=state.get("task")
1033:                 if task and task.winfo_exists(): task.destroy()
1034:             except Exception: pass
1035:             try:
1036:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
1037:             except Exception: pass
1038:             try: outer.destroy()
1039:             except Exception: pass
1040:             if not getattr(self,"_mdi_windows",[]):
1041:                 self._mdi_host.place_forget()
1042:                 self._restore_dashboard_after_internal_close()
```
```text
1035:             try:
1036:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
1037:             except Exception: pass
1038:             try: outer.destroy()
1039:             except Exception: pass
1040:             if not getattr(self,"_mdi_windows",[]):
1041:                 self._mdi_host.place_forget()
1042:                 self._restore_dashboard_after_internal_close()
1043:                 self._restore_dashboard_after_internal_close()
1044:                 # Restore the original application shell FIRST, then rebuild
1045:                 # only the Dashboard body. This keeps the top header/navigation
1046:                 # exactly as they are when the application starts.
1047:                 try:
1048:                     if getattr(self,"_shell_header",None) is not None and self._shell_header.winfo_exists():
1049:                         self._shell_header.pack(fill="x",before=self.body)
1050:                     if getattr(self,"_shell_nav",None) is not None and self._shell_nav.winfo_exists():
1051:                         self._shell_nav.pack(fill="x",before=self.body,after=self._shell_header)
1052:                 except Exception: pass
1053:                 try:
1054:                     self.dashboard()
1055:                 except Exception: pass
```
```text
1088:             return None
1089:         self._inventory_codes_filter=criteria
1090:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1091:         try:
1092:             self.items(container=body)
1093:             win.lift()
1094:             return win
1095:         except Exception:
1096:             try: win._internal_close()
1097:             except Exception: pass
1098:             raise
1099: 
1100:     def open_inventory_codes_report_window(self, criteria=None):
1101:         """Open Inventory Codes as a real report-style child window.
1102: 
1103:         This intentionally mirrors the supplied Preview Report workflow: a
1104:         separate resizable/maximizable window with a left navigation tree,
1105:         compact report toolbar, Find dialog, and print/export commands.
1106:         The main application remains open behind it.
1107:         """
1108:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
1105:         compact report toolbar, Find dialog, and print/export commands.
1106:         The main application remains open behind it.
1107:         """
1108:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
1109:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
1110:         }
1111:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1112: 
1113:         # --- report-style toolbar ---
1114:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
1115:         toolbar.pack(fill="x",side="top")
1116:         toolbar.pack_propagate(False)
1117: 
1118:         def tbtn(text,cmd,width=9):
1119:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
1120:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
1121:                          padx=3,pady=1)
1122:             b.pack(side="left",padx=2,pady=6)
1123:             return b
1124: 
1125:         # --- main report body ---
```
```text
1136:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
1137:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
1138:         navscroll.config(command=code_tree.yview)
1139:         navscroll.pack(side="right",fill="y")
1140:         code_tree.pack(side="left",fill="both",expand=True)
1141: 
1142:         right=tk.Frame(content,bg="#EDEDED")
1143:         right.pack(side="left",fill="both",expand=True)
1144:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
1145:         reportbar.pack(fill="x")
1146:         reportbar.pack_propagate(False)
1147:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
1148:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
1149:         tab.pack(side="left",padx=4,pady=2)
1150:         titlevar=tk.StringVar(value="Inventory Summary")
1151:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
1152:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
1153: 
1154:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
1155:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
1156:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1290:                     vals=tree.item(iid,"values")
1291:                     if str(vals[1]).lower()==str(target).lower():
1292:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1293:                 return True
1294:             self._open_exact_find_text_popup(search_fn)
1295:             self._item_master_find_callback=find_popup
1296: 
1297: 
1298:         def print_report():
1299:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1300:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1301:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1302: 
1303:         def export_pdf():
1304:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1305:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1306:         def export_word():
1307:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1308:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1309:         def export_excel():
1310:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1306:         def export_word():
1307:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1308:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1309:         def export_excel():
1310:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1311:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1312: 
1313:         tbtn("Find",find_popup,7)
1314:         tbtn("Print",print_report,7)
1315:         tbtn("PDF",export_pdf,6)
1316:         tbtn("Word",export_word,6)
1317:         tbtn("Excel",export_excel,6)
1318:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1319:         tbtn("Refresh",load,8)
1320:         tbtn("Close",win._internal_close,7)
1321:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1322:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1323: 
1324:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1325:         build_nav(); load(); win.focus_force()
1326:         return win
```
```text
1336:         self.body=frame
1337:         closed={"done":False}
1338:         def close_window():
1339:             if closed["done"]: return
1340:             closed["done"]=True
1341:             if getattr(self,"body",None) is frame: self.body=old_body
1342:             self._page_actions=old_actions
1343:             self._item_master_find_callback=old_find
1344:             try: win._internal_close()
1345:             except Exception: win.destroy()
1346:         win._internal_close=close_window
1347:         try:
1348:             method(); self.update_idletasks(); win.lift(); return win
1349:         except Exception:
1350:             close_window(); raise
1351: 
1352:     def _manual_check_update(self):
1353:         try:
1354:             updater.check_for_update(self, manual=True)
1355:         except Exception as e:
1356:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1360:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1361:         except Exception as e:
1362:             messagebox.showerror("Current Version", str(e), parent=self)
1363: 
1364:     def build_menu_bar(self):
1365:         """Professional section / sub-section menu bar, ERP style:
1366:         Inventory > Item Master
1367:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1368:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1369:         Edit > Change Password, User Management
1370:         Help > Backup Now, Restore Backup, Network Setup
1371:         """
1372:         menubar=tk.Menu(self)
1373: 
1374:         m_inv=tk.Menu(menubar,tearoff=0)
1375:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1376:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1377:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1378:         menubar.add_cascade(label="Inventory",menu=m_inv)
1379: 
1380:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1380:         m_trans=tk.Menu(menubar,tearoff=0)
1381:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1382:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1383:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1384:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1385:         menubar.add_cascade(label="Transaction",menu=m_trans)
1386: 
1387:         m_rep=tk.Menu(menubar,tearoff=0)
1388:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1389:         m_rep.add_separator()
1390:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1391:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1392:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1393:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1394:         menubar.add_cascade(label="Report",menu=m_rep)
1395: 
1396:         m_edit=tk.Menu(menubar,tearoff=0)
1397:         m_edit.add_command(label="Change Password",command=self.change_password)
1398:         if self.is_admin:
1399:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1400:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1395: 
1396:         m_edit=tk.Menu(menubar,tearoff=0)
1397:         m_edit.add_command(label="Change Password",command=self.change_password)
1398:         if self.is_admin:
1399:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1400:         menubar.add_cascade(label="Edit",menu=m_edit)
1401: 
1402:         m_help=tk.Menu(menubar,tearoff=0)
1403:         m_help.add_command(label="Backup Now",command=self.backup_now)
1404:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1405:         m_help.add_command(label="Current Version",command=self._show_current_version)
1406:         if self.is_admin:
1407:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1408:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1409:         menubar.add_cascade(label="Help",menu=m_help)
1410: 
1411:         self.config(menu=menubar)
1412: 
1413:     def open_calendar_picker(self, var):
1414:         """Small month-grid calendar popup. Picking a day sets `var` to
1415:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1468:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1469:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1470:         return f
1471: 
1472:     def clearbody(self):
1473:         self._portable_print_context=None
1474:         for w in self.body.winfo_children(): w.destroy()
1475:         self._page_actions = {
1476:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1477:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1478:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1479:             "cancel": lambda: self.dashboard(),
1480:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1481:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1482:         }
1483:         # Single SAP-style toolbar at the very top.
1484:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1485:         self._page_action_bar=bar
1486:         self._page_action_first_button=None
1487:         def run_action(k):
1488:             if k=="edit" and not self.can_edit:
```
```text
1485:         self._page_action_bar=bar
1486:         self._page_action_first_button=None
1487:         def run_action(k):
1488:             if k=="edit" and not self.can_edit:
1489:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1490:             if k=="delete" and not self.can_delete:
1491:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1492:             self._page_actions[k]()
1493:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1494:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1495:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1496:             b.pack(side="left",padx=(0,2))
1497:             if self._page_action_first_button is None: self._page_action_first_button=b
1498:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1499: 
1500:     def _portable_print_current(self):
1501:         ctx=getattr(self,"_portable_print_context",None)
1502:         if not ctx:
1503:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1504:             return
1505:         try:
```
```text
1507:             if not data: return
1508:             title,header,columns,rows=data
1509:             self.portable_print_dialog(title,header,columns,rows)
1510:         except Exception as e:
1511:             messagebox.showerror("Portable Printer",str(e))
1512: 
1513:     def portable_print_dialog(self,title,header_lines,columns,rows):
1514:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1515:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1516:         if not WIN32PRINT_AVAILABLE:
1517:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1518:             return
1519:         try:
1520:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1521:         except Exception as e:
1522:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1523:             return
1524:         if not printers:
1525:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1526:             return
1527:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1577:                 if vals and pv.get() not in vals: pv.set(vals[0])
1578:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1579:             except Exception as ex: status.set(str(ex))
1580:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1581:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1582:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1583:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1584:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1585:         win.bind("<Escape>",lambda e:win._internal_close())
1586:         win.focus_force()
1587: 
1588:     def preview_tree(self, title, tree, header_lines=None):
1589:         """Preview the exact rows currently visible in a Treeview."""
1590:         cols=list(tree["columns"])
1591:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1592:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1593:         if not rows:
1594:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1595:             return
1596:         widths=[]
1597:         for c in cols:
```
```text
1594:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1595:             return
1596:         widths=[]
1597:         for c in cols:
1598:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1599:             except Exception: widths.append(100)
1600:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1601: 
1602:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1603:         self._page_actions.update({
1604:             "save": save or self._page_actions.get("save"),
1605:             "edit": edit or self._page_actions.get("edit"),
1606:             "delete": delete or self._page_actions.get("delete"),
1607:             "cancel": cancel or self._page_actions.get("cancel"),
1608:             "print": print or self._page_actions.get("print"),
1609:             "preview": preview or self._page_actions.get("preview"),
1610:         })
1611: 
1612:     def _add_transaction_new_button(self, command):
1613:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1614:         if bar is None or first is None: return
```
```text
1623:         sep.pack(side="left",fill="y",padx=4)
1624:         for w in existing:
1625:             try:
1626:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1627:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1628:                 else: w.pack(side="left")
1629:             except Exception: pass
1630: 
1631:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1632:         """Draw a consistent professional report header and return the first table Y.
1633: 
1634:         For GRN Receipt reports the document number is shown on the left and
1635:         the GRN Date is deliberately shown on the right in a bordered document
1636:         information panel.
1637:         """
1638:         W,H=page_size
1639:         if y_top is None: y_top=H-24
1640:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1641:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1642:         if os.path.exists(LOGO_FILE):
1643:             try:
```
```text
1636:         information panel.
1637:         """
1638:         W,H=page_size
1639:         if y_top is None: y_top=H-24
1640:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1641:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1642:         if os.path.exists(LOGO_FILE):
1643:             try:
1644:                 from reportlab.lib.utils import ImageReader
1645:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1646:             except Exception:
1647:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1648:         else:
1649:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1650:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1651:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1652:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1653:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1654: 
1655:         # Professional document information box.
1656:         info_top=logo_y-12
```
```text
1689:                 # naturally occupies the right-hand cell when supplied second.
1690:                 c.setFont("Helvetica-Bold",7)
1691:                 c.drawString(xx,yy,(label+":")[:28])
1692:                 c.setFont("Helvetica",7)
1693:                 c.drawString(xx+58,yy,val[:58])
1694:             return box_y-12
1695:         return info_top-6
1696: 
1697:     def _report_footer(self, c, page_no, page_size=A4):
1698:         W,H=page_size
1699:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1700:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1701:         current_name=str(getattr(self,"current_user","") or "Unknown User").strip()
1702:         c.drawString(24,13,f"Generated by {current_name}")
1703:         c.drawCentredString(W/2,13,"Made by Muhammad Shahzad")
1704:         c.drawRightString(W-24,13,f"Page {page_no}")
1705:         c.setFillColorRGB(0,0,0)
1706: 
1707:     def _grr_signature_block(self, c, y, page_size=A4):
1708:         """Draw the three requested transaction-document signature lines."""
1709:         W,H=page_size
```
```text
1718:             x=left+i*col_w
1719:             c.setLineWidth(0.6)
1720:             c.line(x+30,top-34,x+col_w-30,top-34)
1721:             c.setFont("Helvetica-Bold",7)
1722:             c.drawCentredString(x+col_w/2,top-48,label)
1723:         return True
1724: 
1725:     def _finish_page(self, c, page_no, page_size=A4):
1726:         self._report_footer(c,page_no,page_size); c.showPage()
1727: 
1728:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1729:         """Word-wrap `text` into a list of lines that each fit inside
1730:         max_width (points) at the given font, breaking mid-word only when a
1731:         single word is itself wider than the column."""
1732:         text=str(text) if text is not None else ""
1733:         if not text:
1734:             return [""]
1735:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1736:         lines=[]; cur=""
1737:         for word in text.split(" "):
1738:             trial=(cur+" "+word).strip() if cur else word
```
```text
1747:                     mid=(lo+hi)//2
1748:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1749:                     else: hi=mid-1
1750:                 lines.append(w[:fit_at]); w=w[fit_at:]
1751:             cur=w
1752:         if cur: lines.append(cur)
1753:         return lines or [""]
1754: 
1755:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1756:         """Create a paginated professional PDF with logo, bordered information,
1757:         GRR signature lines and page numbers. Also keep the same report data in
1758:         memory so the built-in Windows printer dialog can print directly without
1759:         requiring a PDF application's PrintTo association."""
1760:         if not hasattr(self, "_print_jobs"):
1761:             self._print_jobs = {}
1762:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1763:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1764:         page=1
1765:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1766:         usable=W-56
1767:         n=max(1,len(headers))
```
```text
1791:             for ci in range(min(len(headers),len(r))):
1792:                 cell_lines=self._wrap_text_to_width(r[ci],"Helvetica",font_size,max(20,widths[ci]-4))
1793:                 wrapped_cells.append(cell_lines)
1794:                 max_lines=max(max_lines,len(cell_lines))
1795:             row_h=max(11 if font_size<=7 else 13, max_lines*line_h+2)
1796:             # Reserve room on the final page for the three transaction signatures + footer.
1797:             reserve=120 if is_transaction_doc else 42
1798:             if y-row_h<reserve:
1799:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1800:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1801:             # Item rows are intentionally border-free. The section/header remains
1802:             # professional while avoiding the unwanted boxed line around each
1803:             # individual printed item row. Description is drawn separately
1804:             # below (auto-fit / wrapped), so it is skipped in this pass.
1805:             for ci,(xx,cell_lines) in enumerate(zip(xs,wrapped_cells)):
1806:                 for li,ln in enumerate(cell_lines):
1807:                     c.drawString(xx,y-li*line_h,ln)
1808:             y-=row_h
1809:         if is_transaction_doc:
1810:             # Keep the three requested transaction signatures at the physical bottom
1811:             # final page, immediately above the report footer.  If the item
```
```text
1807:                     c.drawString(xx,y-li*line_h,ln)
1808:             y-=row_h
1809:         if is_transaction_doc:
1810:             # Keep the three requested transaction signatures at the physical bottom
1811:             # final page, immediately above the report footer.  If the item
1812:             # table reaches this reserved area, start a fresh final page.
1813:             bottom_sig_y = 138
1814:             if y < 165:
1815:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1816:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1817:             # Draw signatures at a fixed bottom position so they never float
1818:             # directly after the last item row.
1819:             self._grr_signature_block(c,bottom_sig_y,page_size)
1820:         self._report_footer(c,page,page_size); c.save()
1821:         if auto_print:
1822:             self.print_pdf(path)
1823:         return path
1824: 
1825:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1826:         """Professional on-screen preview showing bordered document information
1827:         and a bordered item section. GRN Date is displayed in the right column."""
```
```text
1820:         self._report_footer(c,page,page_size); c.save()
1821:         if auto_print:
1822:             self.print_pdf(path)
1823:         return path
1824: 
1825:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1826:         """Professional on-screen preview showing bordered document information
1827:         and a bordered item section. GRN Date is displayed in the right column."""
1828:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1829:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1830:         # Preview intentionally hides the company logo and company name.
1831:         # The actual generated/printed PDF still contains both via
1832:         # _report_header(), so only the on-screen preview is affected.
1833:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1834:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1835:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1836: 
1837:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
1838:         parsed=[]
1839:         for item in header_lines or []:
1840:             if isinstance(item,(tuple,list)) and len(item)>=2:
```
```text
1858:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1859: 
1860:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1861:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1862:         tr=self.make_tree(items,columns,widths)
1863:         for r in rows: tr.insert("", "end", values=r)
1864: 
1865:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1866:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1867:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1868:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1869:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1870:         win.bind("<Control-f>",bind_preview_find)
1871:         win.bind("<Control-F>",bind_preview_find)
1872: 
1873:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1874:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1875:         if is_transaction_preview:
1876:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1877:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1878:                 sig.columnconfigure(i,weight=1)
```
```text
1876:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1877:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1878:                 sig.columnconfigure(i,weight=1)
1879:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1880:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1881:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1882: 
1883:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1884:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1885:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1886:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1887:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1888:         if on_save:
1889:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1890:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1891:         if not is_transaction_preview:
1892:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1893:         # IMPORTANT: this must remain a normal top-level window (not transient
1894:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1895:         # exactly like the Preview Report window in the supplied recording.
1896:         # The Find dialog is opened from this window and is independent.
```
```text
1889:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1890:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1891:         if not is_transaction_preview:
1892:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1893:         # IMPORTANT: this must remain a normal top-level window (not transient
1894:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1895:         # exactly like the Preview Report window in the supplied recording.
1896:         # The Find dialog is opened from this window and is independent.
1897:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1898:         win.focus_force()
1899: 
1900:     def _safe_report_name(self, title, extension):
1901:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1902:         safe=safe.replace(" ","_") or "Preview"
1903:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1904: 
1905:     def print_preview_window(self, title, header_lines, columns, rows):
1906:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1907:         self._open_direct_printer(title, header_lines, columns, rows,
1908:                                   landscape(A4) if len(columns) > 8 else A4)
1909: 
```
```text
1902:         safe=safe.replace(" ","_") or "Preview"
1903:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1904: 
1905:     def print_preview_window(self, title, header_lines, columns, rows):
1906:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1907:         self._open_direct_printer(title, header_lines, columns, rows,
1908:                                   landscape(A4) if len(columns) > 8 else A4)
1909: 
1910:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1911:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1912:         This keeps the Export PDF button functional on a machine where the bundled
1913:         ReportLab package cannot be imported."""
1914:         def esc(v):
1915:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1916:         W,H=842,595
1917:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1918:         def add(txt,size=8,leading=11):
1919:             lines.append(f"/F1 {size} Tf")
1920:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1921:         add(str(title),12,16)
1922:         for h in header_lines or []:
```
```text
1929:         lines.append("ET")
1930:         stream="\n".join(lines).encode("latin-1","replace")
1931:         objs=[]
1932:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1933:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1934:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1935:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1936:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1937:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1938:         for i,obj in enumerate(objs,1):
1939:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1940:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1941:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1942:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1943:         with open(path,"wb") as f: f.write(out)
1944: 
1945:     def _save_entry_report(self, title, header_lines, columns, rows):
1946:         try:
1947:             os.makedirs(REPORTS_DIR, exist_ok=True)
1948:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1949:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```
```text
1942:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1943:         with open(path,"wb") as f: f.write(out)
1944: 
1945:     def _save_entry_report(self, title, header_lines, columns, rows):
1946:         try:
1947:             os.makedirs(REPORTS_DIR, exist_ok=True)
1948:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1949:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
1950:             path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
1951:             page_size = landscape(A4) if len(columns) > 8 else A4
1952:             if REPORTLAB:
1953:                 self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
1954:             else:
1955:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1956:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1957:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1958:             with open(path, "rb") as f:
1959:                 if f.read(5) != b"%PDF-":
1960:                     raise IOError("Generated report is not a valid PDF.")
1961:             self._last_entry_report_path = path
1962:             return path
```
```text
1956:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1957:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1958:             with open(path, "rb") as f:
1959:                 if f.read(5) != b"%PDF-":
1960:                     raise IOError("Generated report is not a valid PDF.")
1961:             self._last_entry_report_path = path
1962:             return path
1963:         except Exception as exc:
1964:             self._last_entry_report_path = None
1965:             return None
1966: 
1967:     def export_preview_pdf(self, title, header_lines, columns, rows):
1968:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1969:         try:
1970:             os.makedirs(REPORTS_DIR, exist_ok=True)
1971:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1972:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1973:             generated = False
1974:             if REPORTLAB:
1975:                 try:
1976:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
```
```text
1973:             generated = False
1974:             if REPORTLAB:
1975:                 try:
1976:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1977:                     generated = True
1978:                 except Exception:
1979:                     generated = False
1980:             if not generated:
1981:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1982:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1983:                 raise IOError("The PDF file was not created in the Reports folder.")
1984:             with open(path, "rb") as pf:
1985:                 signature = pf.read(5)
1986:             if signature != b"%PDF-":
1987:                 raise IOError("The generated file is not a valid PDF.")
1988:             self._last_report_path = path
1989:             try:
1990:                 webbrowser.open("file://" + path)
1991:             except Exception:
1992:                 self.open_file(path)
1993:             return path
```
```text
1987:                 raise IOError("The generated file is not a valid PDF.")
1988:             self._last_report_path = path
1989:             try:
1990:                 webbrowser.open("file://" + path)
1991:             except Exception:
1992:                 self.open_file(path)
1993:             return path
1994:         except Exception as e:
1995:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1996:             return None
1997: 
1998:     def export_preview_word(self, title, header_lines, columns, rows):
1999:         """Export exactly what is visible in the current preview to Word."""
2000:         if not DOCX_AVAILABLE:
2001:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
2002:         path=self._safe_report_name(title,"docx")
2003:         doc=Document()
2004:         sec=doc.sections[0]
2005:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
2006:         sec.header.paragraphs[0].runs[0].bold=True
2007:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
```
```text
2029:             doc.add_paragraph("")
2030:             sig=doc.add_table(rows=2,cols=3)
2031:             labels=["Prepared By","Store Keeper","Store Incharge"]
2032:             for i,label in enumerate(labels):
2033:                 sig.cell(0,i).text="____________________"
2034:                 sig.cell(1,i).text=label
2035:                 for para in sig.cell(1,i).paragraphs:
2036:                     for run in para.runs: run.bold=True
2037:         doc.save(path)
2038:         self.open_file(path)
2039: 
2040:     def export_preview_excel(self, title, header_lines, columns, rows):
2041:         """Export exactly what is visible in the current preview to Excel."""
2042:         if not XLSX_AVAILABLE:
2043:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
2044:         path=self._safe_report_name(title,"xlsx")
2045:         wb=openpyxl.Workbook(); ws=wb.active
2046:         ws.title="Preview"
2047:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
2048:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
2049:         if not is_transaction_preview:
```
```text
2067:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
2068:             for col in range(1,4):
2069:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
2070:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
2071:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
2072:         for col_cells in ws.columns:
2073:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
2074:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
2075:         wb.save(path)
2076:         self.open_file(path)
2077: 
2078:     def _auto_fit_tree_columns(self, tr, max_width=420):
2079:         try:
2080:             import tkinter.font as tkfont
2081:             try:
2082:                 font=tkfont.nametofont("TkDefaultFont")
2083:             except Exception:
2084:                 font=None
2085:             children=tr.get_children("")
2086:             sample=children[:250]
2087:             for c in tr["columns"]:
```
```text
2186:                     w.state(["!disabled"] if editable else ["disabled"])
2187:             except Exception:
2188:                 try: w.configure(state="normal" if editable else "disabled")
2189:                 except Exception: pass
2190:             for ch in w.winfo_children(): walk(ch)
2191:         for root in roots: walk(root)
2192: 
2193:     def document_selector(self, parent, label, typ, var, load_callback):
2194:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
2195:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
2196:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
2197:         combo.pack(side="left", padx=4)
2198:         def refresh():
2199:             vals=[]
2200:             if typ=="demand":
2201:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
2202:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
2203:             elif typ=="grr":
2204:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
2205:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
2206:             else:
```
```text
2213:             no=text.split(" -> ",1)[0].strip()
2214:             var.set(no)
2215:             load_callback(no)
2216:         combo.bind("<<ComboboxSelected>>", selected)
2217:         combo.bind("<Return>", selected)
2218:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2219:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2220:         refresh()
2221:         # Keep the currently open transaction's saved-record list live.
2222:         # Each save calls refresh_saved_cache(), so newly saved records appear
2223:         # immediately without closing/reopening the window or pressing Refresh.
2224:         if not hasattr(self, "_document_selector_refreshers"):
2225:             self._document_selector_refreshers = {}
2226:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2227:         return combo
2228: 
2229:     def dashboard(self):
2230:         # Dashboard-only visual refresh. All existing data queries, filters,
2231:         # callbacks and report/detail behavior are intentionally preserved.
2232:         self.clearbody()
2233:         c=self.conn
```
```text
2314:             for x in tr.get_children(): tr.delete(x)
2315:             params=[];where=[]
2316:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2317:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2318:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2319:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2320:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2321:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2322:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2323:                    FROM transactions t JOIN items i ON i.code=t.code"""
2324:             if where: sql += " WHERE " + " AND ".join(where)
2325:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2326:             rows=list(c.execute(sql,params))
2327:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2328:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2329:             bal_after={}
2330:             for txid,cc,typ,qty in alltx:
2331:                 running.setdefault(cc,0.0)
2332:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2333:                 bal_after[txid]=running[cc]
2334:             for r in rows:
```
```text
2709:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2710:         load()
2711:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2712: 
2713:     def inventory_codes(self):
2714:         """Inventory Codes using the classic desktop inventory interface.
2715: 
2716:         This screen intentionally follows the uploaded Inventory Management
2717:         reference: a simple module title, compact New/Edit/Delete/Save/
2718:         Refresh/Print/Close action row, and a full-width editable data grid.
2719:         All records come from the V18 database, so existing inventory data is
2720:         preserved rather than recreated.
2721:         """
2722:         self.clearbody()
2723:         # Remove the generic SAP action row; this page owns its own classic
2724:         # action row just like the reference Inventory/Items screen.
2725:         if self.body.winfo_children():
2726:             try:
2727:                 self.body.winfo_children()[0].destroy()
2728:             except Exception:
2729:                 pass
```
```text
2782:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2783:         if filter_text:
2784:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2785:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2786: 
2787:         editing={"id":None,"new":False}
2788:         cell_editor={"widget":None}
2789: 
2790:         def close_editor(save_value=False):
2791:             w=cell_editor.get("widget")
2792:             if not w:
2793:                 return
2794:             try:
2795:                 if save_value:
2796:                     w.event_generate("<Return>")
2797:                 w.destroy()
2798:             except Exception:
2799:                 pass
2800:             cell_editor["widget"]=None
2801: 
2802:         def edit_cell(event=None):
```
```text
2812:             bbox=tree.bbox(iid,colid)
2813:             if not bbox: return
2814:             close_editor(False)
2815:             x,y,w,h=bbox
2816:             val=str(tree.item(iid,"values")[idx] or "")
2817:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2818:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2819:             cell_editor["widget"]=e
2820:             def commit(_=None):
2821:                 try:
2822:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2823:                 finally:
2824:                     try:e.destroy()
2825:                     except Exception:pass
2826:                     cell_editor["widget"]=None
2827:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2828:             e.bind("<FocusOut>",commit)
2829: 
2830:         def rows_query():
2831:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2832:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2834:             if tc: where.append("code <= ?"); params.append(tc)
2835:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2836:             if df or dt:
2837:                 sub=[]; sp=[]
2838:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2839:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2840:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2841:                 params.extend(sp)
2842:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2843:             return sql,params
2844: 
2845:         def load():
2846:             close_editor(False)
2847:             for i in tree.get_children(): tree.delete(i)
2848:             sql,params=rows_query()
2849:             count=0
2850:             for r in self.conn.execute(sql,params):
2851:                 # V18 stores UOM/opening and the original application may have
2852:                 # rate/remarks columns in some versions. Read them safely.
2853:                 rid,code,desc,uom,opening,rate,remarks=r
2854:                 bal=stock(self.conn,code)
```
```text
2868:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2869:             editing["id"]=None; editing["new"]=True
2870:             # Put the user directly into the Code cell.
2871:             try:
2872:                 bbox=tree.bbox(iid,"#2")
2873:                 if bbox:
2874:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2875:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2876:                     def commit(_=None):
2877:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2878:                         try:e.destroy()
2879:                         except Exception:pass
2880:                         cell_editor["widget"]=None
2881:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2882:             except Exception: pass
2883:             status.set("New row added — enter values, then press Save")
2884: 
2885:         def selected_row():
2886:             a=tree.selection()
2887:             return a[0] if a else None
2888: 
```
```text
2888: 
2889:         def edit_record():
2890:             iid=selected_row()
2891:             if not iid:
2892:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2893:             if not self.can_edit and not self.is_admin:
2894:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2895:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2896:             status.set("Edit mode — double-click any cell to change it, then press Save")
2897:             tree.focus(iid); tree.see(iid)
2898: 
2899:         def save_record():
2900:             iid=selected_row()
2901:             if not iid:
2902:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2903:             if not self.can_edit and not self.is_admin:
2904:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2905:             close_editor(True)
2906:             vals=list(tree.item(iid,"values"))
2907:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2908:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2906:             vals=list(tree.item(iid,"values"))
2907:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2908:             try: opening=float(str(vals[4]).strip() or 0)
2909:             except Exception: raise ValueError("Opening Qty must be a number.")
2910:             try: rate=float(str(vals[5]).strip() or 0)
2911:             except Exception: raise ValueError("Rate must be a number.")
2912:             remarks=str(vals[6]).strip()
2913:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2914:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2915:             if not desc:
2916:                 messagebox.showerror("Save","Description is required."); return
2917:             if opening<0:
2918:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2919:             rid=vals[0]
2920:             try:
2921:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2922:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2923:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2924:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2925:                 if rid:
2926:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2929:                                       (code,desc,uom,opening,rid))
2930:                     if oldcode!=code:
2931:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2932:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2933:                             except Exception:pass
2934:                 else:
2935:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2936:                                       (code,desc,uom,"",opening,0,"Local",0))
2937:                 self.conn.commit()
2938:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2939:                 backup_database(); load()
2940:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2941:             except Exception as ex:
2942:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2943: 
2944:         def delete_record():
2945:             iid=selected_row()
2946:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2947:             if not self.can_delete and not self.is_admin:
2948:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2949:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2945:             iid=selected_row()
2946:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2947:             if not self.can_delete and not self.is_admin:
2948:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2949:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2950:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2951:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2952:             try:
2953:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2954:             except Exception as ex:
2955:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2956: 
2957:         def refresh(): load()
2958:         def do_print():
2959:             try:self.preview_tree("Inventory Codes",tree)
2960:             except Exception as ex:messagebox.showerror("Print",str(ex))
2961:         def do_close(): self.dashboard()
2962: 
2963:         btn("New",new_record,8)
2964:         btn("Edit",edit_record,8)
2965:         btn("Delete",delete_record,8)
```
```text
2958:         def do_print():
2959:             try:self.preview_tree("Inventory Codes",tree)
2960:             except Exception as ex:messagebox.showerror("Print",str(ex))
2961:         def do_close(): self.dashboard()
2962: 
2963:         btn("New",new_record,8)
2964:         btn("Edit",edit_record,8)
2965:         btn("Delete",delete_record,8)
2966:         btn("Save",save_record,8)
2967:         btn("Refresh",refresh,9)
2968:         btn("Preview",do_print,8)
2969:         btn("Print",do_print,8)
2970:         btn("Close",do_close,8)
2971: 
2972:         # Search is deliberately small and sits on the right, without changing
2973:         # the reference layout of the action buttons.
2974:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2975:         search=tk.StringVar()
2976:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2977:         se.pack(side="left",padx=2)
2978:         self._item_master_search_entry=se
```
```text
2986:                     tree.detach(iid)
2987:         search.trace_add("write",filter_grid)
2988:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2989: 
2990:         tree.bind("<Double-1>",edit_cell)
2991:         tree.bind("<F2>",lambda e: edit_record())
2992:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2993:         self._page_actions={
2994:             "save":save_record,"edit":edit_record,"delete":delete_record,
2995:             "cancel":do_close,"print":do_print,"preview":do_print
2996:         }
2997:         load()
2998: 
2999:     def open_mto_inventory_flow(self):
3000:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
3001: 
3002:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
3003:         Cancel/X only closes the popup.
3004:         """
3005:         criteria = self._ask_mto_inventory_filters()
3006:         if not criteria or criteria.get("cancelled"):
```
```text
3168:                 return False
3169:             destination.set(found_dest)
3170:             edit_mode.update(on=True, original=r[0], dest=found_dest)
3171:             code.set(r[0])
3172:             desc.set(r[1] or "")
3173:             uom.set(r[2] or UOM_OPTIONS[0])
3174:             opening.set(str(r[3] if r[3] is not None else 0))
3175:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
3176:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
3177:             err.set("")
3178:             edit_btn.configure(text="SAVE EDIT")
3179:             ce.focus_set()
3180:             return True
3181: 
3182:         def check_duplicates(*_):
3183:             c = code.get().strip()
3184:             d = desc.get().strip()
3185:             dest = destination.get()
3186:             msgs = []
3187:             r = row_for(dest, c) if len(norm(c)) == 8 else None
3188:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
3190:             dh = desc_hit(dest, d) if d else None
3191:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
3192:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
3193:             hint.set("\n".join(msgs))
3194: 
3195:         code.trace_add("write", check_duplicates)
3196:         desc.trace_add("write", check_duplicates)
3197: 
3198:         def save_code():
3199:             try:
3200:                 c = code.get().strip()
3201:                 d = desc.get().strip()
3202:                 u = uom.get().strip()
3203:                 dest = destination.get()
3204:                 digits = norm(c)
3205:                 if len(digits) != 8:
3206:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3207:                 if not d:
3208:                     raise ValueError("Description is required.")
3209:                 try:
3210:                     op = float(opening.get().strip() or 0)
```
```text
3231:                         (c, d, u, op, iso, old)
3232:                     )
3233:                     action = "updated"
3234:                 else:
3235:                     self.conn.execute(
3236:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3237:                         (c, d, u, "", op, 0, iso)
3238:                     )
3239:                     action = "saved"
3240:                 self.conn.commit()
3241:                 backup_database()
3242:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3243:                 # Keep popup open for fast multiple entries.
3244:                 clear_form(keep_search=False)
3245:                 ce.focus_set()
3246:             except Exception as ex:
3247:                 self.conn.rollback()
3248:                 err.set(str(ex))
3249:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3250: 
3251:         def edit_action():
```
```text
3247:                 self.conn.rollback()
3248:                 err.set(str(ex))
3249:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3250: 
3251:         def edit_action():
3252:             if not edit_mode["on"]:
3253:                 load_for_edit()
3254:             else:
3255:                 save_code()
3256: 
3257:         def delete_code():
3258:             if not edit_mode["on"]:
3259:                 if not load_for_edit():
3260:                     return
3261:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3262:                 return
3263:             try:
3264:                 t = table_for(edit_mode["dest"])
3265:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3266:                 self.conn.commit()
3267:                 backup_database()
```
```text
3263:             try:
3264:                 t = table_for(edit_mode["dest"])
3265:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3266:                 self.conn.commit()
3267:                 backup_database()
3268:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3269:                 clear_form(keep_search=False)
3270:             except Exception as ex:
3271:                 self.conn.rollback()
3272:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3273: 
3274:         btns = ttk.Frame(box)
3275:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3276:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3277:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3278:         edit_btn.pack(side="left", padx=4, ipadx=8)
3279:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3280:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3281:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3282:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3283:         ce.focus_set()
```
```text
3277:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3278:         edit_btn.pack(side="left", padx=4, ipadx=8)
3279:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3280:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3281:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3282:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3283:         ce.focus_set()
3284: 
3285:     def _mto_new_item_dialog(self, on_saved):
3286:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3287:         brand-new item can be created without leaving that screen. Writes
3288:         straight into the same Item Master (items table) used everywhere."""
3289:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3290:         win.transient(self); win.grab_set()
3291:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3292:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3293:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3294:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3295:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3296:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3297:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3293:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3294:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3295:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3296:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3297:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3298:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3299:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3300:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3301:         def save():
3302:             try:
3303:                 c=code.get().strip(); d=desc.get().strip()
3304:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3305:                 if not d: raise ValueError("Description is required.")
3306:                 try:
3307:                     opening_val=float(opening.get() or 0)
3308:                 except ValueError:
3309:                     raise ValueError("Opening Qty must be a number.")
3310:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3311:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3312:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3313:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3306:                 try:
3307:                     opening_val=float(opening.get() or 0)
3308:                 except ValueError:
3309:                     raise ValueError("Opening Qty must be a number.")
3310:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3311:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3312:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3313:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3314:                 self.conn.commit(); backup_database()
3315:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3316:                 win.grab_release(); win.destroy()
3317:                 on_saved()
3318:             except Exception as ex: messagebox.showerror("Error",str(ex))
3319:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3320:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3321:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3322: 
3323:     def _item_filter_bar(self, parent, on_change):
3324:         """Item Code entry + item-master picker + Search/Show All. Calls
3325:         on_change() whenever the code changes or a button is pressed."""
3326:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3412:         self._item_master_find_callback=None
3413:         self._portable_print_context=None
3414:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3415:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3416:         }
3417: 
3418:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3419:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3420:         self.conn.commit()
3421: 
3422:         # ---- Same professional in-app window layout as Inventory Codes ----
3423:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3424:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3425:                   foreground=COLORS["primary_dark"]).pack(side="left")
3426:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3427: 
3428:         def open_find():
3429:             state_find={"index":-1}
3430:             def search_fn(text):
3431:                 text=text.strip().lower()
3432:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3519:             for i in table.get_children(): table.delete(i)
3520:             where=["1=1"]; params=[]
3521:             prefix=state.get("prefix",""); q=search.get().strip()
3522:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3523:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3524:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3525:             if fc: where.append("code >= ?"); params.append(fc)
3526:             if tc: where.append("code <= ?"); params.append(tc)
3527:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3528:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3529:             records=[]
3530:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3531:                 # If a date filter is supplied, accept an opening-date match OR
3532:                 # a transaction in that date range. This prevents valid MTO codes
3533:                 # from disappearing merely because an older record has no opening_date.
3534:                 if df or dt:
3535:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3536:                     if not ok:
3537:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3538:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3539:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3609:                 tr.insert("", "end", values=r)
3610:         def clear():
3611:             for x in v.values(): x.set("")
3612:             try: tr.selection_remove(tr.selection())
3613:             except Exception: pass
3614:             self._set_form_editable(party_form_roots, False)
3615:         def new_form():
3616:             clear(); self._set_form_editable(party_form_roots, True)
3617:         def save():
3618:             try:
3619:                 name=v["name"].get().strip()
3620:                 if not name: raise ValueError("Party Name is required.")
3621:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3622:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3623:             except Exception as ex: messagebox.showerror("Error",str(ex))
3624:         def load_party_row(a):
3625:             if not a:return
3626:             r=tr.item(a[0])["values"]
3627:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3628:             self._set_form_editable(party_form_roots, False)
3629:         def on_party_select(_=None):
```
```text
3635:             load_party_row(a)
3636:             self._set_form_editable(party_form_roots, True)
3637:         def delete_party():
3638:             a=tr.selection()
3639:             if not a:
3640:                 messagebox.showwarning("Delete", "Select a party first."); return
3641:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3642:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3643:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3644:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3645:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3646:         self._add_transaction_new_button(new_form)
3647:         load(); clear()
3648: 
3649:     def user_management(self):
3650:         self.clearbody()
3651:         if not self.is_admin:
3652:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3653:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3654:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3655:         role=tk.StringVar(value="User")
```
```text
3692:             u_ent.state(["!disabled"])
3693:         def edit():
3694:             a=tr.selection()
3695:             if not a:
3696:                 messagebox.showwarning("Edit User","Select a user row first."); return
3697:             r=tr.item(a[0])["values"]
3698:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3699:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3700:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3701:         def save():
3702:             try:
3703:                 username=v["username"].get().strip()
3704:                 if not username: raise ValueError("Username is required.")
3705:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3706:                 pw=v["password"].get()
3707:                 if exists:
3708:                     pw_hash = hash_password(pw) if pw else exists[0]
3709:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3710:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3711:                 else:
3712:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3707:                 if exists:
3708:                     pw_hash = hash_password(pw) if pw else exists[0]
3709:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3710:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3711:                 else:
3712:                     if not pw: raise ValueError("Password is required for a new user.")
3713:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3714:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3715:                 self.conn.commit(); backup_database(); load(); clear()
3716:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3717:             except Exception as ex:
3718:                 messagebox.showerror("Error", str(ex))
3719:         def delete_user():
3720:             a=tr.selection()
3721:             if not a:
3722:                 messagebox.showwarning("Delete User","Select a user row first."); return
3723:             username=tr.item(a[0])["values"][0]
3724:             if username==self.current_user:
3725:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3726:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3727:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3722:                 messagebox.showwarning("Delete User","Select a user row first."); return
3723:             username=tr.item(a[0])["values"][0]
3724:             if username==self.current_user:
3725:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3726:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3727:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3728:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3729:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3730:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3731:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3732:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3733:         load()
3734: 
3735:     @staticmethod
3736:     def _renumber_tree(tree, rows):
3737:         for i,iid in enumerate(tree.get_children()):
3738:             vals=list(tree.item(iid,"values"));
3739:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3740: 
3741:     def demand(self):
3742:         self.clearbody(); self.demand_lines=[]
```
```text
3739:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3740: 
3741:     def demand(self):
3742:         self.clearbody(); self.demand_lines=[]
3743:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3744:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3745:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3746:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3747:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3748:         # Demand Date is intentionally displayed as its own dedicated field.
3749:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3750:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3751:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3752:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3753:                 ("special","Special Instructions"),("source","Recommended Source")]
3754:         for i,(k,n) in enumerate(fields):
3755:             r=i//4*2+3; c=i%4*2
3756:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3757:             if k=="dept":
3758:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3759:             elif k=="urgency":
```
```text
3829:         def new_form():
3830:             self._editing_document_key=None
3831:             for z in v.values(): z.set("")
3832:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3833:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3834:             for iid in tree.get_children(): tree.delete(iid)
3835:             self._set_form_editable(form_roots, True, skip=[selector])
3836: 
3837:         def save():
3838:             try:
3839:                 no=v["no"].get().strip()
3840:                 if not no: raise ValueError("Demand No is required.")
3841:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3842:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3843:                 if dup and getattr(self,"_editing_document_key",None) != no:
3844:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3845:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3846:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3847:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3848:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3849:                 self.conn.commit()
```
```text
3842:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3843:                 if dup and getattr(self,"_editing_document_key",None) != no:
3844:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3845:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3846:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3847:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3848:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3849:                 self.conn.commit()
3850:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3851:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3852:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3853:             except Exception as ex: messagebox.showerror("Error",str(ex))
3854:         form_roots=[f,line,editbar]
3855:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3856:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3857:         def delete_current():
3858:             no=v["no"].get().strip()
3859:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3860:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3861:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3862:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3875:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3876:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3877:                     f"Justification: {v['just'].get()}",
3878:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3879:             if not self.demand_lines:
3880:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3881:             self.show_preview_window("Purchase Demand", header,
3882:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3883:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3884:         def edit_saved_demand():
3885:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3886:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3887:             self._set_form_editable(form_roots, True, skip=[selector])
3888:         def print_now():
3889:             if not self.demand_lines:
3890:                 messagebox.showwarning("Print","Add at least one item line first."); return
3891:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3892:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3893:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3894:                     f"Justification: {v['just'].get()}",
3895:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3891:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3892:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3893:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3894:                     f"Justification: {v['just'].get()}",
3895:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3896:             self._open_direct_printer("Purchase Demand",header,
3897:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3898:                 self.demand_lines,A4)
3899:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3900:         self._add_transaction_new_button(new_form)
3901:         self._set_form_editable(form_roots, False, skip=[selector])
3902:         try:
3903:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3904:         except Exception: pass
3905:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3906: 
3907:     def load_demand_into_form(self,no,v,tree):
3908:         v["no"].set(no)
3909:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3910:         if not r:return
3911:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3913:         self.demand_lines=[]
3914:         for i in tree.get_children():tree.delete(i)
3915:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3916:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3917:         roots=getattr(self,"_transaction_form_roots",None)
3918:         if roots and "demand" in roots:
3919:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3920: 
3921:     def refresh_saved_cache(self,typ):
3922:         # Refresh saved-document dropdowns immediately after a successful save.
3923:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3924:         alive=[]
3925:         for combo, refresh in refreshers:
3926:             try:
3927:                 if combo.winfo_exists():
3928:                     refresh()
3929:                     alive.append((combo, refresh))
3930:             except Exception:
3931:                 pass
3932:         if hasattr(self, "_document_selector_refreshers"):
3933:             self._document_selector_refreshers[typ] = alive
```
```text
3932:         if hasattr(self, "_document_selector_refreshers"):
3933:             self._document_selector_refreshers[typ] = alive
3934: 
3935:     def grr(self):
3936:         self.clearbody(); self.grr_lines=[]
3937:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3938:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3939:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3940:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3941:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3942:         for i,(k,n) in enumerate(fields):
3943:             r=i//4*2+2;c=i%4*2
3944:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3945:             if k=="department":
3946:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3947:             elif k=="supplier":
3948:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3949:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3950:             elif k=="date":
3951:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3952:             else:
```
```text
4001:         def new_form():
4002:             self._editing_document_key=None
4003:             for z in v.values(): z.set("")
4004:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
4005:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
4006:             for iid in tree.get_children(): tree.delete(iid)
4007:             self._set_form_editable(form_roots, True, skip=[selector])
4008: 
4009:         def save():
4010:             try:
4011:                 no=v["no"].get().strip()
4012:                 if not no:raise ValueError("GRN No is required.")
4013:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
4014:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
4015:                 if dup and getattr(self,"_editing_document_key",None) != no:
4016:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
4017:                 if not self.grr_lines:raise ValueError("Add at least one item.")
4018:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
4019:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
4020:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
4021:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
4018:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
4019:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
4020:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
4021:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
4022:                 for x in self.grr_lines:
4023:                     ltype=x[10] if len(x)>10 else "Local"
4024:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
4025:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
4026:                 self.conn.commit()
4027:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
4028:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
4029:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4030:             except Exception as ex:messagebox.showerror("Error",str(ex))
4031:         form_roots=[f,line,editbar]
4032:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4033:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
4034:         def delete_current():
4035:             no=v["no"].get().strip()
4036:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
4037:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
4038:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
4031:         form_roots=[f,line,editbar]
4032:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4033:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
4034:         def delete_current():
4035:             no=v["no"].get().strip()
4036:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
4037:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
4038:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
4039:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
4040:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
4041:         def cancel_form():
4042:             self._editing_document_key=None
4043:             self._set_form_editable(form_roots, False, skip=[selector])
4044:             for z in v.values(): z.set("")
4045:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
4046:             itype.set("Local")
4047:             self.grr_lines.clear()
4048:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
4049:             for iid in tree.get_children(): tree.delete(iid)
4050:         def preview_now():
4051:             if not self.grr_lines:
```
```text
4060:                     ("Challan #", v['challan'].get()),
4061:                     ("Vehicle #", v['vehicle'].get()),
4062:                     ("Bill/Voucher #", v['bill'].get()),
4063:                     ("Reference", v['ref'].get()),
4064:                     ("Remarks", v['remarks'].get()),
4065:                     ("Total Value", fmt_num(total))]
4066:             self.show_preview_window("GRN Receipt", header,
4067:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
4068:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
4069:         def portable_current():
4070:             total=sum(float(x[8] or 0) for x in self.grr_lines)
4071:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
4072:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
4073:         self._portable_print_context=portable_current
4074:         def edit_saved_grr():
4075:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4076:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
4077:             self._set_form_editable(form_roots, True, skip=[selector])
4078:         def print_now():
4079:             if not self.grr_lines:
4080:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
4084:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
4085:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
4086:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
4087:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
4088:                     ("Total Value", fmt_num(total))]
4089:             self._open_direct_printer("GRN Receipt",header,
4090:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
4091:                 self.grr_lines,landscape(A4))
4092:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
4093:         self._add_transaction_new_button(new_form)
4094:         self._set_form_editable(form_roots, False, skip=[selector])
4095:         try:
4096:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
4097:         except Exception: pass
4098:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
4099: 
4100:     def load_grr_into_form(self,no,v,tree):
4101:         v["no"].set(no)
4102:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
4103:         if not r:return
4104:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
4111:         if roots and "grr" in roots:
4112:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
4113: 
4114:     def issue(self):
4115:         self.clearbody(); self.issue_lines=[]
4116:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
4117:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
4118:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
4119:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
4120:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
4121:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
4122:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
4123:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
4124:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
4125:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
4126:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
4127:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
4128:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
4129:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
4130:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
4131:         itype=tk.StringVar(value="Local")
```
```text
4200:                 # Editing an existing issue replaces its old stock transaction and detail lines.
4201:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
4202:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
4203:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
4204:                 for x in self.issue_lines:
4205:                     ltype=x[7] if len(x)>7 else "Local"
4206:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
4207:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
4208:                 self.conn.commit()
4209:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
4210:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
4211:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4212:             except Exception as ex:messagebox.showerror("Error",str(ex))
4213:         def delete_current():
4214:             no=v["no"].get().strip()
4215:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
4216:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
4217:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
4218:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
4219:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
4220:         def cancel_form():
```
```text
4228:             for iid in tree.get_children(): tree.delete(iid)
4229:         def preview_now():
4230:             if not self.issue_lines:
4231:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4232:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4233:                     f"Items Use For: {v['items_use_for'].get()}"]
4234:             self.show_preview_window("Material Issue", header,
4235:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4236:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4237:         def portable_current():
4238:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4239:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4240:         self._portable_print_context=portable_current
4241:         form_roots=[f,usebar,line,editbar]
4242:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4243:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4244:         def load_saved_issue(no):
4245:             self.load_issue_into_form(no,v,tree)
4246:             self._set_form_editable(form_roots, False, skip=[selector])
4247:         def edit_saved_issue():
4248:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4241:         form_roots=[f,usebar,line,editbar]
4242:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4243:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4244:         def load_saved_issue(no):
4245:             self.load_issue_into_form(no,v,tree)
4246:             self._set_form_editable(form_roots, False, skip=[selector])
4247:         def edit_saved_issue():
4248:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4249:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4250:             self._set_form_editable(form_roots, True, skip=[selector])
4251:         def print_issue_now():
4252:             if not self.issue_lines:
4253:                 messagebox.showwarning("Print","Add at least one item line first."); return
4254:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4255:             self._open_direct_printer("Material Issue",header,
4256:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4257:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4258:         self._add_transaction_new_button(new_form)
4259:         self._set_form_editable(form_roots, False, skip=[selector])
4260:         self._active_form_loader = load_saved_issue
4261: 
```
```text
4269:         for i in tree.get_children():tree.delete(i)
4270:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4271:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4272:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4273:         roots=getattr(self,"_transaction_form_roots",None)
4274:         if roots and "issue" in roots:
4275:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4276: 
4277:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4278:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4279: 
4280:         The layout intentionally matches Inventory Codes' Selection Criteria
4281:         popup so all Report sub-sections have one consistent desktop workflow.
4282:         """
4283:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4284:         win=tk.Toplevel(self)
4285:         win.title(f"{report_title} - Selection Criteria")
4286:         win.resizable(False,False)
4287:         win.transient(self); win.grab_set()
4288:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4289:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4334:             except Exception: pass
4335:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4336:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4337:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4338:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4339:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4340:         e1.focus_set(); self.wait_window(win); return result
4341: 
4342:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4343:         self._pending_report_filters=criteria
4344:         try:
4345:             return self.open_menu_window(method,title,geometry)
4346:         finally:
4347:             self._pending_report_filters=None
4348: 
4349:     def open_stock_balance_report_flow(self):
4350:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4351:         if f.get("cancelled"): return None
4352:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4353: 
4354:     def open_grr_report_flow(self):
```
```text
4347:             self._pending_report_filters=None
4348: 
4349:     def open_stock_balance_report_flow(self):
4350:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4351:         if f.get("cancelled"): return None
4352:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4353: 
4354:     def open_grr_report_flow(self):
4355:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4356:         if f.get("cancelled"): return None
4357:         return self._open_report_child(self.report_grr,"GRN Report",f)
4358: 
4359:     def open_demand_report_flow(self):
4360:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4361:         if f.get("cancelled"): return None
4362:         return self._open_report_child(self.report_demand,"Demand Report",f)
4363: 
4364:     def open_issue_report_flow(self):
4365:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4366:         if f.get("cancelled"): return None
4367:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4361:         if f.get("cancelled"): return None
4362:         return self._open_report_child(self.report_demand,"Demand Report",f)
4363: 
4364:     def open_issue_report_flow(self):
4365:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4366:         if f.get("cancelled"): return None
4367:         return self._open_report_child(self.report_issue,"Issue Report",f)
4368: 
4369:     def open_party_report_flow(self):
4370:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4371:         if f.get("cancelled"): return None
4372:         return self._open_report_child(self.report_party,"Party Report",f)
4373: 
4374:     def _ask_stock_balance_filters(self):
4375:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4376:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4377:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4378:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4379:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4380:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4381:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4393:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4394:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4395:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4396:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4397:         e1.focus_set();self.wait_window(win);return result
4398: 
4399:     def stock_balance(self):
4400:         self.clearbody()
4401:         # Stock Balance is a Report sub-section and does not use the generic
4402:         # Save/Edit/Delete/Cancel/Print action strip.
4403:         children=self.body.winfo_children()
4404:         if children:
4405:             children[0].destroy()
4406:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4407:         if initial.get("cancelled"):
4408:             self.dashboard(); return
4409:         top=ttk.Frame(self.body);top.pack(fill="x")
4410:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4411:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4412:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4413:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4423:             for typ,qty in self.conn.execute(q,params):
4424:                 if typ=="GRR":gr+=float(qty or 0)
4425:                 elif typ=="ISSUE":iss+=float(qty or 0)
4426:             return opening_before,gr,iss,opening_before+gr-iss
4427:         def header_summary():
4428:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4429:         def load():
4430:             for i in tr.get_children():tr.delete(i)
4431:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4432:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4433:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4434:             sql+=" ORDER BY code"
4435:             for r in self.conn.execute(sql,params):
4436:                 op,gr,iss,cur=period(r[0],r[3])
4437:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4438:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4439:         def reopen_filters():
4440:             initial2=self._ask_stock_balance_filters()
4441:             if initial2.get("cancelled"):return
4442:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4443:             load()
```
```text
4481:         """
4482:         if typ=="demand": self.demand()
4483:         elif typ=="grr": self.grr()
4484:         else: self.issue()
4485:         loader=getattr(self,"_active_form_loader",None)
4486:         if loader: loader(str(no))
4487: 
4488:     def _edit_from_selector(self, typ, var, loader):
4489:         """Top Edit action: load the saved document directly into the current form.
4490:         If nothing is selected, use the newest saved document; never open a popup.
4491:         """
4492:         text=var.get().strip()
4493:         if text:
4494:             no=text.split(" -> ",1)[0].strip()
4495:         else:
4496:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4497:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4498:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4499:             if not r:
4500:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4501:                 return
```
```text
4498:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4499:             if not r:
4500:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4501:                 return
4502:             no=str(r[0])
4503:             var.set(no)
4504:         loader(no)
4505: 
4506:     def show_saved_records(self,typ):
4507:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4508:         if typ=="demand":
4509:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4510:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4511:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4512:             for r in rows:
4513:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4514:                 r=list(r); r[1]=to_display_date(r[1])
4515:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4516:         elif typ=="grr":
4517:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4518:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4529:         def view():
4530:             a=tr.selection()
4531:             if not a:return
4532:             no=tr.item(a[0])["values"][0]
4533:             win.destroy();self.open_document_editor(typ,no)
4534:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4535:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4536:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4537:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4538: 
4539:     def documents(self):
4540:         self.clearbody()
4541:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4542:         specs=[
4543:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4544:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4545:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4546:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4547:             ("Material Issues","issue",("No","Date","Department"),
4548:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4549:         ]
```
```text
4545:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4546:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4547:             ("Material Issues","issue",("No","Date","Department"),
4548:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4549:         ]
4550:         for title,typ,cols,query in specs:
4551:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4552:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4553:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4554:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4555:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4556:             for r in self.conn.execute(query):
4557:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4558:             def edit_selected(t=tr,k=typ):
4559:                 a=t.selection()
4560:                 if not a:
4561:                     messagebox.showwarning("Edit", "Select a saved record first.")
4562:                     return
4563:                 no=t.item(a[0])["values"][0]
4564:                 self.open_document_editor(k,no)
4565:             def delete_selected(t=tr,k=typ):
```
```text
4560:                 if not a:
4561:                     messagebox.showwarning("Edit", "Select a saved record first.")
4562:                     return
4563:                 no=t.item(a[0])["values"][0]
4564:                 self.open_document_editor(k,no)
4565:             def delete_selected(t=tr,k=typ):
4566:                 a=t.selection()
4567:                 if not a:
4568:                     messagebox.showwarning("Delete", "Select a saved record first.")
4569:                     return
4570:                 no=t.item(a[0])["values"][0]
4571:                 if k=="demand":
4572:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4573:                 elif k=="grr":
4574:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4575:                 else:
4576:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4577:                 self.conn.commit();backup_database();self.documents()
4578:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4579:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4580:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4574:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4575:                 else:
4576:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4577:                 self.conn.commit();backup_database();self.documents()
4578:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4579:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4580:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4581:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4582:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4583:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4584:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4585: 
4586:     def doc_export_selected(self,typ,tr,fmt):
4587:         a=tr.selection()
4588:         if not a:
4589:             messagebox.showwarning("Export","Select a saved record first."); return
4590:         no=tr.item(a[0])["values"][0]
4591:         if fmt=="word": self.export_word(typ,no)
4592:         else: self.export_excel(typ,no)
4593: 
4594:     def doc_preview_selected(self,typ,tr):
```
```text
4589:             messagebox.showwarning("Export","Select a saved record first."); return
4590:         no=tr.item(a[0])["values"][0]
4591:         if fmt=="word": self.export_word(typ,no)
4592:         else: self.export_excel(typ,no)
4593: 
4594:     def doc_preview_selected(self,typ,tr):
4595:         a=tr.selection()
4596:         if not a:
4597:             messagebox.showwarning("Preview","Select a saved record first."); return
4598:         no=tr.item(a[0])["values"][0]
4599:         data=self._get_doc_data(typ,no)
4600:         if not data:
4601:             messagebox.showwarning("Preview","Document not found."); return
4602:         title,header,cols,rows=data
4603:         header_lines=header
4604:         self.show_preview_window(title,header_lines,cols,rows)
4605: 
4606:     def doc_print_selected(self,typ,tr):
4607:         a=tr.selection()
4608:         if not a: return
4609:         no=tr.item(a[0])["values"][0]
```
```text
4640:         def _print_loaded_document():
4641:             data=self._get_doc_data(typ,no)
4642:             if not data:
4643:                 messagebox.showwarning("Document","Document not found."); return
4644:             title,header,cols,rows=data
4645:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4646:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4647: 
4648:     def _report_filter_popup(self, title, include_party=False):
4649:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4650:         win,winbody=self._internal_window(title,"520x420")
4651:         done=tk.BooleanVar(value=False)
4652:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4653:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4654:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4655:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4656:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4657:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4658:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4659:         if include_party:
4660:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4654:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4655:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4656:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4657:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4658:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4659:         if include_party:
4660:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4661:         def ok():
4662:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4663:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4664:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4665:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4666: 
4667:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4668:         self.clearbody()
4669:         # Report sub-sections use their own report toolbar; remove only the
4670:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4671:         children=self.body.winfo_children()
4672:         if children:
4673:             children[0].destroy()
4674:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4675:         if f.get("cancelled"):
4676:             self.dashboard();return
4677:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4678:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4679:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4680:         def load():
4681:             for i in tr.get_children():tr.delete(i)
4682:             params,where=params_builder(f)
4683:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4684:             for r in self.conn.execute(sql,params):
4685:                 vals=list(r)
4686:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4687:                 tr.insert("","end",values=vals)
4688:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4689:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4690:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4691:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4692:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4693:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4694:         def open_find_report():
4695:             state_find={"index":-1}
```
```text
4701:                 order=children[start:]+children[:start]
4702:                 for iid in order:
4703:                     vals=tr.item(iid,"values")
4704:                     if any(text in str(v).lower() for v in vals):
4705:                         state_find["index"]=children.index(iid)
4706:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4707:                 return False
4708:             self._open_exact_find_text_popup(search_fn)
4709:         self._item_master_find_callback=open_find_report
4710:         load()
4711:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4712: 
4713:     def report_grr(self):
4714:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4715:         def pb(f):
4716:             w=[];p=[]
4717:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4718:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4719:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4720:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4721:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4716:             w=[];p=[]
4717:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4718:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4719:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4720:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4721:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4722:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4723:             return p,w
4724:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4725: 
4726:     def report_demand(self):
4727:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4728:         def pb(f):
4729:             w=[];p=[]
4730:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4731:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4732:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4733:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4734:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4735:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4736:             return p,w
```
```text
4729:             w=[];p=[]
4730:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4731:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4732:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4733:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4734:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4735:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4736:             return p,w
4737:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4738: 
4739:     def report_issue(self):
4740:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4741:         def pb(f):
4742:             w=[];p=[]
4743:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4744:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4745:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4746:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4747:             return p,w
4748:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4749: 
```
```text
4742:             w=[];p=[]
4743:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4744:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4745:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4746:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4747:             return p,w
4748:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4749: 
4750:     def report_party(self):
4751:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4752:         def pb(f):
4753:             w=[];p=[]
4754:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4755:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4756:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4757:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4758:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4759:             return p,w
4760:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4761: 
4762:     def reports(self):
```
```text
4760:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4761: 
4762:     def reports(self):
4763:         self.clearbody()
4764:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4765: 
4766:         # ================= GRN Details =================
4767:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4768:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4769:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4770:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4771:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4772:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4773: 
4774:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4775:         def load_grr_item(codev=None):
4776:             for i in tr.get_children(): tr.delete(i)
4777:             q=codev.get().strip() if codev else ""
4778:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4779:             for r in self.conn.execute(sql,(q,) if q else ()):
4780:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4786:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4787:         tr=self.make_tree(fr,grr_cols,grr_widths)
4788:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4789:             for i in tr.get_children(): tr.delete(i)
4790:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4791:             conds=[];params=[]
4792:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4793:             if td: conds.append("g.grr_date<=?");params.append(td)
4794:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4795:             for r in self.conn.execute(sql,params):
4796:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4797:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4798:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4799:         load_grr_date(fdv,tdv)
4800: 
4801:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4802:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4803:         party=tk.StringVar(value="ALL")
4804:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4805:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4806:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4802:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4803:         party=tk.StringVar(value="ALL")
4804:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4805:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4806:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4807:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4808:         def load_party(*_):
4809:             for i in tr.get_children(): tr.delete(i)
4810:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4811:             if party.get()=="ALL":
4812:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4813:             else:
4814:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4815:             for r in rows:
4816:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4817:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4818:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4819: 
4820:         # ================= Demand Details =================
4821:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4822:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4818:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4819: 
4820:         # ================= Demand Details =================
4821:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4822:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4823:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4824:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4825:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4826:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4827: 
4828:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4829:         def load_dem_item(codev=None):
4830:             for i in tr.get_children(): tr.delete(i)
4831:             q=codev.get().strip() if codev else ""
4832:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4833:             for r in self.conn.execute(sql,(q,) if q else ()):
4834:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4835:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4836:         tr=self.make_tree(fr,dem_cols,dem_widths)
4837:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4838:         load_dem_item(codev)
```
```text
4840:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4841:         tr=self.make_tree(fr,dem_cols,dem_widths)
4842:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4843:             for i in tr.get_children(): tr.delete(i)
4844:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4845:             conds=[];params=[]
4846:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4847:             if td: conds.append("d.demand_date<=?");params.append(td)
4848:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4849:             for r in self.conn.execute(sql,params):
4850:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4851:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4852:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4853:         load_dem_date(fdv,tdv)
4854: 
4855:         # ================= Material Issue Details =================
4856:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4857:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4858:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4859:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4860:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4853:         load_dem_date(fdv,tdv)
4854: 
4855:         # ================= Material Issue Details =================
4856:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4857:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4858:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4859:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4860:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4861:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4862: 
4863:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4864:         def load_iss_item(codev=None):
4865:             for i in tr.get_children(): tr.delete(i)
4866:             q=codev.get().strip() if codev else ""
4867:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4868:             for r in self.conn.execute(sql,(q,) if q else ()):
4869:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4870:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4871:         tr=self.make_tree(fr,iss_cols,iss_widths)
4872:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4873:         load_iss_item(codev)
```
```text
4875:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4876:         tr=self.make_tree(fr,iss_cols,iss_widths)
4877:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4878:             for i in tr.get_children(): tr.delete(i)
4879:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4880:             conds=[];params=[]
4881:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4882:             if td: conds.append("i.issue_date<=?");params.append(td)
4883:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4884:             for r in self.conn.execute(sql,params):
4885:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4886:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4887:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4888:         load_iss_date(fdv,tdv)
4889: 
4890:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4891: 
4892:     def print_item_master(self):
4893:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4894:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4895: 
```
```text
4892:     def print_item_master(self):
4893:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4894:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4895: 
4896:     def print_party_master(self):
4897:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4898:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4899: 
4900:     def print_report(self,kind):
4901:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4902:         if kind=="grr":
4903:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4904:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4905:         elif kind=="demand":
4906:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4907:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4908:         elif kind=="issue":
4909:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4910:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4911:         else:
4912:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4913:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4914:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4915: 
4916:     def print_stock(self):
4917:         rows=[]
4918:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4919:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4920:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4921:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4922: 
4923:     def print_ledger(self):
4924:         rows=[]
4925:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4926:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4927:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4928:                 running += x[3] if x[1]=="GRR" else -x[3]
4929:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4930:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4931: 
4932:     def _get_doc_data(self, typ, no):
4933:         """Header + line items for one saved document, used by the on-screen
```
```text
4999:             sig=doc.add_table(rows=2,cols=3)
5000:             labels=["Prepared By","Store Keeper","Store Incharge"]
5001:             for i,label in enumerate(labels):
5002:                 sig.cell(0,i).text="____________________"
5003:                 sig.cell(1,i).text=label
5004:                 for para in sig.cell(1,i).paragraphs:
5005:                     for run in para.runs: run.bold=True
5006:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
5007:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
5008:         doc.save(path)
5009:         self.open_file(path)
5010: 
5011:     def export_excel(self, typ, no):
5012:         if not no or not no.strip():
5013:             return messagebox.showwarning("Excel Export","Select a document first.")
5014:         if not XLSX_AVAILABLE:
5015:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
5016:         data=self._get_doc_data(typ,no)
5017:         if not data:
5018:             return messagebox.showwarning("Excel Export","Document not found.")
5019:         title,header,cols,rows=data
```
```text
5041:             for col in range(1,4):
5042:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
5043:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
5044:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
5045:         for col_cells in ws.columns:
5046:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
5047:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
5048:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
5049:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
5050:         wb.save(path)
5051:         self.open_file(path)
5052: 
5053:     def preview_pdf(self,typ,no):
5054:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
5055:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
5056:         data=self._get_doc_data(typ,no)
5057:         if not data:return messagebox.showwarning("Document","Document not found.")
5058:         title,header,cols,rows=data
5059:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
5060:         page_size = landscape(A4) if typ == "grr" else A4
5061:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
5056:         data=self._get_doc_data(typ,no)
5057:         if not data:return messagebox.showwarning("Document","Document not found.")
5058:         title,header,cols,rows=data
5059:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
5060:         page_size = landscape(A4) if typ == "grr" else A4
5061:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
5062: 
5063:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
5064:         """Open the print dialog with a real visual preview of the exact report.
5065: 
5066:         The report is rendered to a temporary PDF only in memory/on disk for the
5067:         duration of printing.  It is deleted after the print dialog closes, so
5068:         the Print button does not leave a PDF report behind.  Printing uses the
5069:         rendered report page itself rather than rebuilding rows as plain text;
5070:         this keeps the printed page identical to the application's report.
5071:         """
5072:         # Printing is always prepared as an A4 landscape page. This only affects
5073:         # the print path; the rest of the application's UI/report logic is unchanged.
5074:         page_size = landscape(A4)
5075:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
5076:             messagebox.showwarning(
```
```text
5078:                 "The print preview/printing components are not available.\n\n"
5079:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
5080:             )
5081:             return
5082:         if not rows and not columns:
5083:             messagebox.showwarning("Print", "There is no data to print.")
5084:             return
5085:         try:
5086:             os.makedirs(REPORTS_DIR, exist_ok=True)
5087:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
5088:             self._pdf_table_report(key,title,columns,rows,page_size,
5089:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
5090:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
5091:             self._select_windows_printer_for_pdf(key)
5092:         except Exception as e:
5093:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
5094: 
5095:     def _select_windows_printer_for_pdf(self, path):
5096:         """Print dialog with an actual page preview, printer selection and direct GDI output.
5097: 
5098:         The preview is rendered from the exact PDF produced by the application,
```
```text
5128:         job=getattr(self, "_print_jobs", {}).get(path)
5129:         if job:
5130:             title, header_lines, columns, rows, source_page_size = job
5131:         else:
5132:             title=os.path.splitext(os.path.basename(path))[0]
5133:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
5134: 
5135:         try:
5136:             doc=fitz.open(path)
5137:             total_pages=max(1,doc.page_count)
5138:         except Exception as e:
5139:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
5140:             return
5141: 
5142:         win=tk.Toplevel(self)
5143:         win.title("Printing from Win32 application - Print")
5144:         win.geometry("900x620")
5145:         win.minsize(850,580)
5146:         win.transient(self)
5147:         win.configure(bg="#f0f0f0")
5148: 
```
```text
5154:             pass
5155: 
5156:         outer=tk.Frame(win,bg="#f0f0f0")
5157:         outer.pack(fill="both",expand=True)
5158:         outer.columnconfigure(1,weight=1)
5159:         outer.rowconfigure(0,weight=1)
5160: 
5161:         # Left side mirrors the familiar system printer dialog: printers and
5162:         # print options. Right side contains the actual report page preview.
5163:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
5164:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
5165:         left.grid_propagate(False)
5166:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
5167:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
5168:         printer_list.pack(fill="x")
5169:         for pr in printers: printer_list.insert("end",pr)
5170:         try: printer_list.selection_set(printers.index(default_printer))
5171:         except Exception: printer_list.selection_set(0)
5172: 
5173:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
5174:         copies=tk.IntVar(value=1)
```
```text
5247:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5248: 
5249:         bottom=tk.Frame(win,bg="#f0f0f0")
5250:         # `outer` already uses pack() in `win`; using grid() for another direct
5251:         # child of the same toplevel raises TclError. Keep the action bar in the
5252:         # same geometry-manager family so Print/Cancel are always visible.
5253:         bottom.pack(fill="x",padx=12,pady=(0,12))
5254:         bottom.columnconfigure(0,weight=1)
5255:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5256:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5257:         print_btn=ttk.Button(bottom,text="Print",width=12)
5258:         print_btn.grid(row=0,column=2,padx=(8,0))
5259: 
5260:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5261: 
5262:         def parse_page_selection(total):
5263:             if pages_mode.get()=="All pages": return list(range(total))
5264:             raw=page_range.get().strip()
5265:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5266:             selected=[]
5267:             for part in raw.split(","):
```
```text
5264:             raw=page_range.get().strip()
5265:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5266:             selected=[]
5267:             for part in raw.split(","):
5268:                 part=part.strip()
5269:                 if "-" in part:
5270:                     a,b=part.split("-",1); a=int(a); b=int(b)
5271:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5272:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5273:                     selected.extend(range(a-1,b))
5274:                 else:
5275:                     n=int(part)
5276:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5277:                     selected.append(n-1)
5278:             return list(dict.fromkeys(selected))
5279: 
5280:         def selected_printer():
5281:             sel=printer_list.curselection()
5282:             return printer_list.get(sel[0]) if sel else printers[0]
5283: 
5284:         def print_rendered_pages():
```
```text
5377:                 finally:
5378:                     if hprinter is not None:
5379:                         try: win32print.ClosePrinter(hprinter)
5380:                         except Exception: pass
5381:                     if hdc:
5382:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5383:                         except Exception: pass
5384: 
5385:                 # Print the exact rendered PDF page through the printer DC.
5386:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5387:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5388:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5389:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5390: 
5391:                 for copy_no in range(count):
5392:                     dc.StartDoc(str(title)[:80])
5393:                     doc_ok=False
5394:                     try:
5395:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5396:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5397:                             dc.StartPage()
```
```text
5396:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5397:                             dc.StartPage()
5398:                             page_ok=False
5399:                             try:
5400:                                 cell_w=printable_w/float(cols_n)
5401:                                 cell_h=printable_h/float(rows_n)
5402:                                 for j,page_index in enumerate(batch):
5403:                                     page=doc.load_page(page_index)
5404:                                     pdf_w=max(1.0,float(page.rect.width))
5405:                                     pdf_h=max(1.0,float(page.rect.height))
5406:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5407:                                     fit=max(0.25,min(fit,8.0))
5408:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5409:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5410:                                     target_w=max(1,int(cell_w*0.96))
5411:                                     target_h=max(1,int(cell_h*0.96))
5412:                                     ratio=min(target_w/img.width,target_h/img.height)
5413:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5414:                                     if (nw,nh)!=(img.width,img.height):
5415:                                         img=img.resize((nw,nh),Image.LANCZOS)
5416:                                     dib=ImageWin.Dib(img)
```
```text
5436: 
5437:                 status.set("Print job sent successfully")
5438:                 win.update_idletasks()
5439:                 win.after(500,close)
5440:             except Exception as e:
5441:                 status.set("Print failed: "+str(e))
5442:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5443: 
5444:         def close():
5445:             try: doc.close()
5446:             except Exception: pass
5447:             try: win.destroy()
5448:             except Exception: pass
5449:             # Only the temporary PDF created by the Print button is removed.
5450:             # Existing report PDFs passed through the legacy print path are preserved.
5451:             try:
5452:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5453:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5454:             except Exception: pass
5455: 
5456:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5452:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5453:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5454:             except Exception: pass
5455: 
5456:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5457:         bottom.winfo_children()[1].configure(command=close)
5458:         print_btn.configure(command=print_rendered_pages)
5459:         win.protocol("WM_DELETE_WINDOW",close)
5460:         win.bind("<Escape>",lambda e:close())
5461:         win.grab_set()
5462:         # Keep the requested printer defaults visibly selected; no manual
5463:         # adjustment is required before pressing Print.
5464:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5465:         win.after(120,lambda:render_preview(0))
5466:         win.focus_force()
5467: 
5468:     def print_pdf(self,path):
5469:         """Open a printer-selection window for a generated PDF."""
5470:         path=os.path.abspath(path)
5471:         if not os.path.exists(path):
5472:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5468:     def print_pdf(self,path):
5469:         """Open a printer-selection window for a generated PDF."""
5470:         path=os.path.abspath(path)
5471:         if not os.path.exists(path):
5472:             messagebox.showwarning("Print", "The report file could not be found.")
5473:             return
5474: 
5475:         if sys.platform.startswith("win"):
5476:             self._select_windows_printer_for_pdf(path)
5477:             return
5478: 
5479:         try:
5480:             subprocess.run(["lp", path], check=True)
5481:         except Exception as e:
5482:             messagebox.showwarning(
5483:                 "Print",
5484:                 "The operating system could not start printing.\n\n"
5485:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5486:             )
5487: 
5488:     def open_file(self,path):
```
```text
5483:                 "Print",
5484:                 "The operating system could not start printing.\n\n"
5485:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5486:             )
5487: 
5488:     def open_file(self,path):
5489:         try:
5490:             if sys.platform.startswith("win"): os.startfile(path)
5491:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5492:             else: subprocess.Popen(["xdg-open",path])
5493:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5494: 
5495:     def print_demand(self,no):
5496:         data=self._get_doc_data("demand",no)
5497:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5498:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5499:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5500:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5501: 
5502:     def print_grr(self,no):
5503:         data=self._get_doc_data("grr",no)
```
```text
5497:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5498:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5499:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5500:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5501: 
5502:     def print_grr(self,no):
5503:         data=self._get_doc_data("grr",no)
5504:         if not data:return messagebox.showwarning("Document","GRN not found.")
5505:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5506:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5507:         # GRN has a wide item table. Generate the PDF itself in landscape so
5508:         # the printer dialog and printer driver receive a landscape document
5509:         # instead of a portrait page with rotated/cropped content.
5510:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5511: 
5512:     def print_issue(self,no):
5513:         data=self._get_doc_data("issue",no)
5514:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5515:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5516:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5517:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
```

## updater.py

- Lines: 137
- AST parse error: unexpected character after line continuation character (<unknown>, line 1)

### Relevant source locations

```text
0042:         return False
0043:     idm_paths = (
0044:         os.path.expandvars(r"%PROGRAMFILES%\\Internet Download Manager\\IDMan.exe"),
0045:         os.path.expandvars(r"%PROGRAMFILES(x86)%\\Internet Download Manager\\IDMan.exe"),
0046:     )
0047:     for path in idm_paths:
0048:         if os.path.isfile(path):
0049:             try:
0050:                 subprocess.Popen([path, "/d", download_url, "/n"], close_fds=True)
0051:                 return True
0052:             except Exception:
0053:                 pass
0054:     try:
0055:         return bool(webbrowser.open(download_url, new=2))
0056:     except Exception:
0057:         try:
0058:             os.startfile(download_url)
0059:             return True
0060:         except Exception:
0061:             return False
0062: 
```
