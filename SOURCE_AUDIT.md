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

- Lines: 5515
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-436), restore_database(437-454), stock(456-461), fmt_num(463-465), to_iso_date(467-476), to_display_date(478-486), fiscal_year_key(488-499), fiscal_year_range(501-504), normalize_code(506-514), format_code(516-525), attach_code_mask(527-553), set_digits(530-535), key(536-546), paste(548-551), bind_add_to_list(555-576), on_enter(558-569), __init__(580-597), _check_for_updates(599-604), _setup_style(606-642), _shade(645-650), on_close(652-657), redo_network_setup(659-675), backup_now(677-684), restore_backup(686-704), _ctrl_f(706-718), _open_exact_find_text_popup(720-765), do_find(741-750), close(751-758), _global_enter(767-779), wipe(781-782), login(784-813), do_login(799-810), change_password(815-865), save_password(837-859), logout(867-872), home(874-900), _restore_dashboard_after_internal_close(902-916), _ensure_mdi_host(918-939), _internal_window(941-1057), normal_place(957-963), restore(964-979), maximize(980-994), minimize(995-1024), close(1025-1050), open_inventory_codes_detail_flow(1059-1077), open_inventory_codes_with_filters(1079-1093), open_inventory_codes_report_window(1095-1321), tbtn(1113-1118), balance_as_of(1175-1185), build_nav(1187-1209), selected_prefix(1211-1220), load(1222-1254), page_move(1256-1257), page_first(1258-1258), page_last(1259-1263), on_nav(1267-1268), find_popup(1271-1290), search_fn(1273-1288), print_report(1293-1296), export_pdf(1298-1300), export_word(1301-1303), export_excel(1304-1306), open_menu_window(1323-1345), close_window(1333-1340), _manual_check_update(1347-1351), _show_current_version(1353-1357), build_menu_bar(1359-1406), open_calendar_picker(1408-1456), pick(1426-1428), redraw(1430-1442), nav(1444-1448), make_date_field(1458-1465), clearbody(1467-1493), run_action(1482-1487), _portable_print_current(1495-1506), portable_print_dialog(1508-1581), build_receipt(1535-1553), send(1554-1567), refresh_printers(1568-1574), preview_tree(1583-1595), set_page_actions(1597-1605), _add_transaction_new_button(1607-1624), _report_header(1626-1690), _report_footer(1692-1700), _grr_signature_block(1702-1718), _finish_page(1720-1721), _wrap_text_to_width(1723-1748), fits(1730-1730), _pdf_table_report(1750-1818), table_header(1772-1777), show_preview_window(1820-1893), _safe_report_name(1895-1898), print_preview_window(1900-1903), _fallback_pdf_export(1905-1938), esc(1909-1910), add(1913-1915), _save_entry_report(1940-1960), export_preview_pdf(1962-1991), export_preview_word(1993-2033), export_preview_excel(2035-2071), _auto_fit_tree_columns(2073-2098), make_tree(2100-2128), schedule_fit(2111-2121), fitted_insert(2122-2125), pick_item(2130-2151), choose(2131-2150), ld(2138-2142), sel(2144-2148), bind_item_lookup(2153-2170), lookup(2155-2168), _set_form_editable(2173-2186), walk(2176-2185), document_selector(2188-2222), refresh(2193-2204), selected(2205-2210), dashboard(2224-2336), load_details(2308-2332), _refresh_dashboard_kpis(2338-2352), dashboard_details(2354-2358), item_history(2360-2380), _ask_item_master_filters(2382-2466), finish(2435-2447), items(2468-2706), hierarchy(2509-2518), selected_prefix(2564-2577), balance_as_of(2579-2586), load(2588-2626), set_page(2628-2629), select_node(2631-2652), open_find(2658-2677), search_fn(2660-2675), visible_rows(2682-2684), print_inventory(2685-2689), export_inventory_word(2690-2692), export_inventory_excel(2693-2695), portable_inventory(2700-2702), inventory_codes(2708-2992), btn(2744-2749), close_editor(2785-2795), edit_cell(2797-2823), commit(2815-2821), rows_query(2825-2838), load(2840-2855), new_record(2857-2878), commit(2871-2875), selected_row(2880-2882), edit_record(2884-2892), save_record(2894-2937), delete_record(2939-2950), refresh(2952-2952), do_print(2953-2955), do_close(2956-2956), filter_grid(2974-2981), open_mto_inventory_flow(2994-3017), open_code_opening_flow(3019-3027), code_opening(3029-3030), _open_code_opening_popup(3032-3033), _open_code_opening_detail(3035-3278), norm(3105-3106), table_for(3108-3109), row_for(3111-3116), search_any_destination(3118-3131), desc_hit(3133-3137), clear_form(3139-3152), load_for_edit(3154-3175), check_duplicates(3177-3188), save_code(3193-3244), edit_action(3246-3250), delete_code(3252-3267), _mto_new_item_dialog(3280-3316), save(3296-3313), _item_filter_bar(3318-3330), _date_filter_bar(3332-3340), _ask_mto_inventory_filters(3342-3387), finish(3372-3380), mto_inventory(3389-3589), open_find(3423-3442), search_fn(3425-3440), hierarchy(3461-3465), rebuild_nav(3467-3478), mto_balance(3502-3511), load(3513-3555), set_page(3557-3557), select_node(3558-3567), visible_rows(3572-3572), do_print(3573-3577), export_word(3578-3580), export_excel(3581-3583), party_master(3591-3642), load(3601-3604), clear(3605-3609), new_form(3610-3611), save(3612-3618), load_party_row(3619-3623), on_party_select(3624-3625), edit(3627-3631), delete_party(3632-3638), user_management(3644-3728), sync_role(3671-3676), load(3680-3683), clear(3684-3687), edit(3688-3695), save(3696-3713), delete_user(3714-3725), _renumber_tree(3731-3734), demand(3736-3900), _restore_demand_tree_columns(3779-3785), add(3788-3796), edit_item(3798-3810), delete_item(3812-3820), new_form(3824-3830), save(3832-3848), delete_current(3852-3858), cancel_form(3859-3867), preview_now(3868-3878), edit_saved_demand(3879-3882), print_now(3883-3893), load_demand_into_form(3902-3914), refresh_saved_cache(3916-3928), grr(3930-4093), add(3962-3970), edit_item(3972-3982), delete_item(3984-3992), new_form(3996-4002), save(4004-4025), delete_current(4029-4035), cancel_form(4036-4044), preview_now(4045-4063), portable_current(4064-4067), edit_saved_grr(4069-4072), print_now(4073-4086), load_grr_into_form(4095-4107), issue(4109-4255), old_issue_qty(4138-4141), update_balance(4142-4150), add(4152-4161), edit_item(4163-4174), new_form(4178-4184), post(4186-4207), delete_current(4208-4214), cancel_form(4215-4223), preview_now(4224-4231), portable_current(4232-4234), load_saved_issue(4239-4241), edit_saved_issue(4242-4245), print_issue_now(4246-4251), load_issue_into_form(4257-4270), _ask_report_criteria(4272-4335), finish(4321-4329), _open_report_child(4337-4342), open_stock_balance_report_flow(4344-4347), open_grr_report_flow(4349-4352), open_demand_report_flow(4354-4357), open_issue_report_flow(4359-4362), open_party_report_flow(4364-4367), _ask_stock_balance_filters(4369-4392), ok(4384-4385), cancel(4386-4386), stock_balance(4394-4457), period(4410-4421), header_summary(4422-4423), load(4424-4433), reopen_filters(4434-4438), open_find_stock(4442-4455), search_fn(4444-4454), ledger(4459-4471), open_document_editor(4473-4481), _edit_from_selector(4483-4499), show_saved_records(4501-4532), view(4524-4528), documents(4534-4579), edit_selected(4553-4559), delete_selected(4560-4572), doc_export_selected(4581-4587), doc_preview_selected(4589-4599), doc_print_selected(4601-4609), load_document(4611-4641), _print_loaded_document(4635-4640), _report_filter_popup(4643-4660), ok(4656-4657), cancel(4658-4658), _report_window(4662-4706), load(4675-4682), hdr(4683-4683), open_find_report(4689-4703), search_fn(4691-4702), report_grr(4708-4719), pb(4710-4718), report_demand(4721-4732), pb(4723-4731), report_issue(4734-4743), pb(4736-4742), report_party(4745-4755), pb(4747-4754), reports(4757-4885), load_grr_item(4770-4775), load_grr_date(4783-4791), load_party(4803-4811), load_dem_item(4824-4829), load_dem_date(4837-4845), load_iss_item(4859-4864), load_iss_date(4872-4880), print_item_master(4887-4889), print_party_master(4891-4893), print_report(4895-4909), print_stock(4911-4916), print_ledger(4918-4925), _get_doc_data(4927-4955), export_word(4957-5004), export_excel(5006-5046), preview_pdf(5048-5056), _open_direct_printer(5058-5088), _select_windows_printer_for_pdf(5090-5461), render_preview(5215-5234), on_resize(5236-5238), parse_page_selection(5257-5273), selected_printer(5275-5277), print_rendered_pages(5279-5437), close(5439-5449), print_pdf(5463-5481), open_file(5483-5488), print_demand(5490-5495), print_grr(5497-5505), print_issue(5507-5512)

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
0261:             sync.initialize(raw)
0262:             # Firebase may contain an older snapshot whose items table does not
0263:             # yet have the MTO columns. Re-run the local schema migration after
0264:             # the remote snapshot is restored so Code Opening can always create
0265:             # and display MTO records.
0266:             _init_schema(raw)
0267:         except Exception as exc:
0268:             # Keep the application usable with its local cache when the
0269:             # internet/Firebase is temporarily unavailable. The next write or
0270:             # restart will retry sync.
```
```text
0265:             # and display MTO records.
0266:             _init_schema(raw)
0267:         except Exception as exc:
0268:             # Keep the application usable with its local cache when the
0269:             # internet/Firebase is temporarily unavailable. The next write or
0270:             # restart will retry sync.
0271:             sync.pending_error = str(exc)
0272:     try:
0273:         durable_local.save(raw)
0274:     except Exception:
0275:         pass
0276:     return OnlineConnection(DB, sync)
0277: 
0278: def migrate_old_item_codes(c):
0279:     """Migrate old 00-00-00-0000 item codes to 00-00-0000 everywhere."""
0280:     rows=c.execute("SELECT code FROM items").fetchall()
0281:     for (old,) in rows:
0282:         digits="".join(ch for ch in str(old) if ch.isdigit())
0283:         if len(digits)!=10: continue
0284:         new=format_code(digits)
0285:         if not new or new==old: continue
```
```text
0284:         new=format_code(digits)
0285:         if not new or new==old: continue
0286:         if c.execute("SELECT 1 FROM items WHERE code=?",(new,)).fetchone():
0287:             # Do not destroy an existing code; leave this collision visible for manual resolution.
0288:             continue
0289:         c.execute("UPDATE items SET code=? WHERE code=?",(new,old))
0290:         for table,col in (("demand_lines","code"),("grr_lines","code"),("issue_lines","code"),("transactions","code")):
0291:             c.execute(f"UPDATE {table} SET {col}=? WHERE {col}=?",(new,old))
0292:     c.commit()
0293: 
0294: def seed_items(c):
0295:     if c.execute("SELECT COUNT(*) FROM items").fetchone()[0]: return
0296:     if not os.path.exists(SEED): return
0297:     with open(SEED,encoding="utf-8-sig") as f:
0298:         for r in csv.DictReader(f):
0299:             c.execute("INSERT OR IGNORE INTO items(code,description,uom) VALUES(?,?,?)",
0300:                       (format_code(r.get("code","").strip()),r.get("description","").strip(),r.get("uom","").strip()))
0301:     c.commit()
0302: 
0303: def backup_database(manual=False):
0304:     """Create a consistent full SQLite backup in C:\StoreInventoryManagement\Backups."""
```
```text
0298:         for r in csv.DictReader(f):
0299:             c.execute("INSERT OR IGNORE INTO items(code,description,uom) VALUES(?,?,?)",
0300:                       (format_code(r.get("code","").strip()),r.get("description","").strip(),r.get("uom","").strip()))
0301:     c.commit()
0302: 
0303: def backup_database(manual=False):
0304:     """Create a consistent full SQLite backup in C:\StoreInventoryManagement\Backups."""
0305:     try:
0306:         os.makedirs(BACKUP_DIR, exist_ok=True)
0307: 
0308:         # The live database is permanently under C:\StoreInventoryManagement\Data.
0309:         # Also accept the legacy DB variable/path and any SQLite file already
0310:         # present in the install tree so Backup Now never depends on the old
0311:         # pre-online database location.
0312:         known = []
0313:         try:
0314:             legacy_db = globals().get("DB")
0315:             if legacy_db:
0316:                 known.append(os.path.abspath(os.fspath(legacy_db)))
0317:         except Exception:
0318:             pass
```
```text
0316:                 known.append(os.path.abspath(os.fspath(legacy_db)))
0317:         except Exception:
0318:             pass
0319:         known.extend([
0320:             os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db"),
0321:             os.path.join(r"C:\StoreInventoryManagement", "Data", "inventory.db"),
0322:             os.path.join(r"C:\StoreInventoryManagement", "store_inventory.db"),
0323:         ])
0324:         db_candidates = []
0325:         for p in known:
0326:             if p and p not in db_candidates:
0327:                 db_candidates.append(p)
0328:         # Discover the actual SQLite file if its legacy filename differs.
0329:         for root in (
0330:             os.path.join(r"C:\StoreInventoryManagement", "Data"),
0331:             r"C:\StoreInventoryManagement",
0332:         ):
0333:             try:
0334:                 if os.path.isdir(root):
0335:                     for name in os.listdir(root):
0336:                         if os.path.splitext(name)[1].lower() in (".db", ".sqlite", ".sqlite3", ".db3"):
```
```text
0330:             os.path.join(r"C:\StoreInventoryManagement", "Data"),
0331:             r"C:\StoreInventoryManagement",
0332:         ):
0333:             try:
0334:                 if os.path.isdir(root):
0335:                     for name in os.listdir(root):
0336:                         if os.path.splitext(name)[1].lower() in (".db", ".sqlite", ".sqlite3", ".db3"):
0337:                             p = os.path.join(root, name)
0338:                             if p not in db_candidates:
0339:                                 db_candidates.append(p)
0340:             except Exception:
0341:                 pass
0342: 
0343:         db_path = next((p for p in db_candidates if os.path.isfile(p)), None)
0344:         if not db_path:
0345:             # Create the expected database path if the database has not yet
0346:             # been materialized by the storage layer.
0347:             db_path = os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db")
0348:             try:
0349:                 os.makedirs(os.path.dirname(db_path), exist_ok=True)
0350:                 probe = sqlite3.connect(db_path, timeout=30)
```
```text
0343:         db_path = next((p for p in db_candidates if os.path.isfile(p)), None)
0344:         if not db_path:
0345:             # Create the expected database path if the database has not yet
0346:             # been materialized by the storage layer.
0347:             db_path = os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db")
0348:             try:
0349:                 os.makedirs(os.path.dirname(db_path), exist_ok=True)
0350:                 probe = sqlite3.connect(db_path, timeout=30)
0351:                 probe.close()
0352:             except Exception:
0353:                 return None
0354:             if not os.path.isfile(db_path):
0355:                 return None
0356: 
0357:         stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
0358:         tag = "manual" if manual else "auto"
0359:         latest = os.path.join(BACKUP_DIR, "inventory_backup_latest.db")
0360:         dated = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.db")
0361:         zpath = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.zip")
0362: 
0363:         src = sqlite3.connect(db_path, timeout=30)
```
```text
0361:         zpath = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.zip")
0362: 
0363:         src = sqlite3.connect(db_path, timeout=30)
0364:         try:
0365:             try:
0366:                 src.execute("PRAGMA wal_checkpoint(FULL)")
0367:             except Exception:
0368:                 pass
0369:             dst = sqlite3.connect(dated, timeout=30)
0370:             try:
0371:                 with dst:
0372:                     src.backup(dst)
0373:             finally:
0374:                 dst.close()
0375:         finally:
0376:             src.close()
0377: 
0378:         # Keep the latest convenience copy, replacing only that fixed filename.
0379:         # Historical/manual backup archives are never automatically deleted.
0380:         if os.path.exists(latest):
0381:             try:
```
```text
0377: 
0378:         # Keep the latest convenience copy, replacing only that fixed filename.
0379:         # Historical/manual backup archives are never automatically deleted.
0380:         if os.path.exists(latest):
0381:             try:
0382:                 os.remove(latest)
0383:             except OSError:
0384:                 pass
0385:         latest_src = sqlite3.connect(dated, timeout=30)
0386:         try:
0387:             latest_dst = sqlite3.connect(latest, timeout=30)
0388:             try:
0389:                 with latest_dst:
0390:                     latest_src.backup(latest_dst)
0391:             finally:
0392:                 latest_dst.close()
0393:         finally:
0394:             latest_src.close()
0395: 
0396:         if not os.path.isfile(dated) or os.path.getsize(dated) <= 0:
0397:             return None
```
```text
0394:             latest_src.close()
0395: 
0396:         if not os.path.isfile(dated) or os.path.getsize(dated) <= 0:
0397:             return None
0398:         with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
0399:             z.write(dated, "store_inventory.db")
0400:         if not os.path.isfile(zpath) or os.path.getsize(zpath) <= 0:
0401:             return None
0402:         # Also store a cloud copy of the same complete database snapshot.
0403:         # This uses the Firebase Realtime Database URL only; no API key is needed.
0404:         # A cloud-backup failure never invalidates an already-created local backup.
0405:         try:
0406:             import requests
0407:             url_file = Path(__file__).resolve().parent / "firebase_database_url.txt"
0408:             base_url = ""
0409:             if url_file.exists():
0410:                 for line in url_file.read_text(encoding="utf-8-sig").splitlines():
0411:                     line = line.strip()
0412:                     if line and not line.startswith("#"):
0413:                         base_url = line.rstrip("/")
0414:                         break
```
```text
0409:             if url_file.exists():
0410:                 for line in url_file.read_text(encoding="utf-8-sig").splitlines():
0411:                     line = line.strip()
0412:                     if line and not line.startswith("#"):
0413:                         base_url = line.rstrip("/")
0414:                         break
0415:             if base_url:
0416:                 cloud_stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
0417:                 cloud_url = f"{base_url}/store_inventory/backups/{cloud_stamp}.json"
0418:                 with open(dated, "rb") as bf:
0419:                     import base64
0420:                     encoded = base64.b64encode(bf.read()).decode("ascii")
0421:                 response = requests.put(
0422:                     cloud_url,
0423:                     json={
0424:                         "created_at": cloud_stamp,
0425:                         "type": "sqlite_backup",
0426:                         "filename": os.path.basename(zpath),
0427:                         "database_base64": encoded,
0428:                     },
0429:                     timeout=30,
```
```text
0429:                     timeout=30,
0430:                 )
0431:                 response.raise_for_status()
0432:         except Exception:
0433:             pass
0434:         return zpath
0435:     except Exception:
0436:         return None
0437: def restore_database(backup_path):
0438:     """Restore the database from a .db or .zip backup file. The current
0439:     database is itself backed up first, so a restore can never destroy data."""
0440:     try:
0441:         backup_database(manual=True)  # safety net before touching anything
0442:         if backup_path.lower().endswith(".zip"):
0443:             with zipfile.ZipFile(backup_path,"r") as z:
0444:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0445:                 os.makedirs(tmp_dir,exist_ok=True)
0446:                 z.extractall(tmp_dir)
0447:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0448:                 shutil.copy2(extracted,DB)
0449:                 shutil.rmtree(tmp_dir,ignore_errors=True)
```
```text
0443:             with zipfile.ZipFile(backup_path,"r") as z:
0444:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0445:                 os.makedirs(tmp_dir,exist_ok=True)
0446:                 z.extractall(tmp_dir)
0447:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0448:                 shutil.copy2(extracted,DB)
0449:                 shutil.rmtree(tmp_dir,ignore_errors=True)
0450:         else:
0451:             shutil.copy2(backup_path,DB)
0452:         return True
0453:     except Exception:
0454:         return False
0455: 
0456: def stock(c, code):
0457:     r=c.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()
0458:     q=float(r[0] or 0) if r else 0
0459:     for typ,qty in c.execute("SELECT doc_type,qty FROM transactions WHERE code=? ORDER BY id", (code,)):
0460:         q += float(qty or 0) if typ=="GRR" else -float(qty or 0) if typ=="ISSUE" else 0
0461:     return q
0462: 
0463: def fmt_num(x):
```
```text
0461:     return q
0462: 
0463: def fmt_num(x):
0464:     x=float(x or 0)
0465:     return f"{x:,.2f}".rstrip("0").rstrip(".")
0466: 
0467: def to_iso_date(s):
0468:     """Convert a user-entered DD/MM/YYYY date (or an already-ISO date) into
0469:     ISO YYYY-MM-DD for storage in the database and for date-range queries,
0470:     which rely on ISO strings sorting/comparing correctly."""
0471:     s=(s or "").strip()
0472:     if not s: return ""
0473:     for f in ("%d/%m/%Y","%Y-%m-%d"):
0474:         try: return datetime.strptime(s,f).strftime("%Y-%m-%d")
0475:         except Exception: continue
0476:     return s
0477: 
0478: def to_display_date(s):
0479:     """Convert an ISO YYYY-MM-DD date (as stored in the database) into the
0480:     DD/MM/YYYY format used everywhere on screen and on printed reports."""
0481:     s=(s or "").strip()
```
```text
0576:     return on_enter
0577: 
0578: 
0579: class App(tk.Tk):
0580:     def __init__(self):
0581:         super().__init__()
0582:         self.title("Store Inventory Management System | SAP Style")
0583:         self.geometry("1400x820"); self.minsize(1150,700)
0584:         self.conn=connect()
0585:         self.demand_lines=[]; self.grr_lines=[]; self.issue_lines=[]
0586:         self.current_user=None; self.current_role=None
0587:         self._item_master_search_entry=None
0588:         self._item_master_find_callback=None
0589:         self._portable_print_context=None
0590:         self.can_edit=False; self.can_delete=False; self.is_admin=False
0591:         self._setup_style()
0592:         # Any focused button can be activated with Enter.
0593:         self.bind_all("<Return>", self._global_enter, add="+")
0594:         self.bind_all("<KP_Enter>", self._global_enter, add="+")
0595:         self.bind_all("<Control-f>", self._ctrl_f, add="+")
0596:         self.protocol("WM_DELETE_WINDOW", self.on_close)
```
```text
0644:     @staticmethod
0645:     def _shade(hexcolor, factor):
0646:         """Return a slightly darker version of a #RRGGBB color (for hover/press states)."""
0647:         h=hexcolor.lstrip("#")
0648:         r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
0649:         r,g,b=(max(0,int(v*factor)) for v in (r,g,b))
0650:         return f"#{r:02x}{g:02x}{b:02x}"
0651: 
0652:     def on_close(self):
0653:         try:
0654:             self.conn.commit(); backup_database()
0655:         except Exception:
0656:             pass
0657:         self.destroy()
0658: 
0659:     def redo_network_setup(self):
0660:         if not messagebox.askyesno("Network Setup",
0661:             "This will clear the online database URL saved on this computer.\n\n"
0662:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0663:             "Continue?"):
0664:             return
```
```text
0658: 
0659:     def redo_network_setup(self):
0660:         if not messagebox.askyesno("Network Setup",
0661:             "This will clear the online database URL saved on this computer.\n\n"
0662:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0663:             "Continue?"):
0664:             return
0665:         try:
0666:             self.conn.commit(); backup_database()
0667:         except Exception:
0668:             pass
0669:         try:
0670:             if os.path.exists(FIREBASE_URL_FILE): os.remove(FIREBASE_URL_FILE)
0671:         except Exception:
0672:             pass
0673:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0674:         self.destroy()
0675:         sys.exit(0)
0676: 
0677:     def backup_now(self):
0678:         path=backup_database(manual=True)
```
```text
0672:             pass
0673:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0674:         self.destroy()
0675:         sys.exit(0)
0676: 
0677:     def backup_now(self):
0678:         path=backup_database(manual=True)
0679:         if path:
0680:             messagebox.showinfo("Backup Complete",
0681:                 f"A full backup was saved to:\n\n{path}\n\n"
0682:                 f"All backups are kept in:\n{BACKUP_DIR}")
0683:         else:
0684:             messagebox.showerror("Backup Failed","Could not create a backup. Make sure the database exists.")
0685: 
0686:     def restore_backup(self):
0687:         from tkinter import filedialog
0688:         if not messagebox.askyesno("Restore Backup",
0689:             "This will replace all current data with the selected backup.\n"
0690:             "A safety backup of the current data will be made first.\n\n"
0691:             "Continue?"):
0692:             return
```
```text
0686:     def restore_backup(self):
0687:         from tkinter import filedialog
0688:         if not messagebox.askyesno("Restore Backup",
0689:             "This will replace all current data with the selected backup.\n"
0690:             "A safety backup of the current data will be made first.\n\n"
0691:             "Continue?"):
0692:             return
0693:         path=filedialog.askopenfilename(
0694:             title="Select a backup file",
0695:             initialdir=BACKUP_DIR,
0696:             filetypes=[("Backup files","*.zip *.db"),("All files","*.*")])
0697:         if not path: return
0698:         if restore_database(path):
0699:             messagebox.showinfo("Restore Complete",
0700:                 "Data has been restored. The application will now restart.")
0701:             self.conn.close()
0702:             os.execv(sys.executable, [sys.executable]+sys.argv)
0703:         else:
0704:             messagebox.showerror("Restore Failed","Could not restore from that backup file.")
0705: 
0706:     def _ctrl_f(self, event=None):
```
```text
0743:             if not text:
0744:                 fe.focus_set(); return
0745:             try:
0746:                 found=search_fn(text)
0747:             except Exception:
0748:                 found=False
0749:             if found is False:
0750:                 messagebox.showinfo("Find Text","No matching text found.",parent=dlg)
0751:         def close():
0752:             try:
0753:                 dlg.grab_release()
0754:             except Exception: pass
0755:             try: dlg.destroy()
0756:             except Exception: pass
0757:             if getattr(self,"_exact_find_text_dialog",None) is dlg:
0758:                 self._exact_find_text_dialog=None
0759:         ttk.Button(box,text="Find Next",command=do_find,width=13).grid(row=0,column=3,padx=4,pady=4)
0760:         ttk.Button(box,text="Cancel",command=close,width=13).grid(row=1,column=3,padx=4,pady=4)
0761:         fe.bind("<Return>",lambda e:(do_find(),"break"))
0762:         dlg.bind("<Escape>",lambda e:close())
0763:         dlg.protocol("WM_DELETE_WINDOW",close)
```
```text
0829:         cur_ent=ttk.Entry(box,textvariable=current,width=28,show="*"); cur_ent.grid(row=2,column=1,pady=7)
0830:         ttk.Label(box,text="New Password").grid(row=3,column=0,sticky="w",pady=7)
0831:         new_ent=ttk.Entry(box,textvariable=new,width=28,show="*"); new_ent.grid(row=3,column=1,pady=7)
0832:         ttk.Label(box,text="Confirm New Password").grid(row=4,column=0,sticky="w",pady=7)
0833:         conf_ent=ttk.Entry(box,textvariable=confirm,width=28,show="*"); conf_ent.grid(row=4,column=1,pady=7)
0834:         err=ttk.Label(box,text="",foreground="#c0392b",wraplength=380,justify="left")
0835:         err.grid(row=5,column=0,columnspan=2,pady=(5,8))
0836: 
0837:         def save_password(event=None):
0838:             old_pw=current.get()
0839:             new_pw=new.get()
0840:             confirm_pw=confirm.get()
0841:             row=self.conn.execute("SELECT password FROM users WHERE username=?",(self.current_user,)).fetchone()
0842:             if not row or not verify_password(old_pw,row[0]):
0843:                 err.config(text="Current password is incorrect."); return
0844:             if len(new_pw) < 4:
0845:                 err.config(text="New password must be at least 4 characters."); return
0846:             if new_pw != confirm_pw:
0847:                 err.config(text="New password and confirmation do not match."); return
0848:             if new_pw == old_pw:
0849:                 err.config(text="New password must be different from the current password."); return
```
```text
0845:                 err.config(text="New password must be at least 4 characters."); return
0846:             if new_pw != confirm_pw:
0847:                 err.config(text="New password and confirmation do not match."); return
0848:             if new_pw == old_pw:
0849:                 err.config(text="New password must be different from the current password."); return
0850:             try:
0851:                 self.conn.execute("UPDATE users SET password=? WHERE username=?",
0852:                                   (hash_password(new_pw),self.current_user))
0853:                 self.conn.commit()
0854:                 backup_database()
0855:                 win.grab_release(); win.destroy()
0856:                 messagebox.showinfo("Password Changed",
0857:                     "Your password has been changed successfully.\n\nUse the new password the next time you log in.", parent=self)
0858:             except Exception as ex:
0859:                 err.config(text=f"Could not change password: {ex}")
0860: 
0861:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0862:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0863:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0864:         conf_ent.bind("<Return>",save_password)
0865:         cur_ent.focus_set()
```
```text
0861:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0862:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0863:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0864:         conf_ent.bind("<Return>",save_password)
0865:         cur_ent.focus_set()
0866: 
0867:     def logout(self):
0868:         try:
0869:             self.conn.commit(); backup_database()
0870:         except Exception:
0871:             pass
0872:         self.login()
0873: 
0874:     def home(self):
0875:         self.wipe()
0876:         self.build_menu_bar()
0877:         hdr=tk.Frame(self,bg=COLORS["primary_dark"]);hdr.pack(fill="x")
0878:         self._shell_header=hdr
0879:         inner=tk.Frame(hdr,bg=COLORS["primary_dark"],padx=16,pady=10);inner.pack(fill="x")
0880:         tk.Label(inner,text=COMPANY,font=("Segoe UI",16,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="left")
0881:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
```
```text
0881:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
0882:         tk.Label(inner,text=f"Data: {DATA_DIR}",font=("Segoe UI",8),bg=COLORS["primary_dark"],fg="#9FB8DA").pack(side="left",padx=14)
0883:         ttk.Button(inner,text="Logout",style="Danger.TButton",command=self.logout).pack(side="right")
0884:         tk.Label(inner,text=f"{self.current_user}  ({self.current_role})",font=("Segoe UI",9,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="right",padx=12)
0885:         nav=tk.Frame(self,bg=COLORS["primary"]);nav.pack(fill="x")
0886:         self._shell_nav=nav
0887:         navin=tk.Frame(nav,bg=COLORS["primary"],padx=10,pady=6);navin.pack(fill="x")
0888:         ttk.Button(navin,text="🏠  Dashboard",style="Accent.TButton",command=self.dashboard).pack(side="left",padx=3)
0889:         tk.Label(navin,text="Inventory  |  Transaction  |  Report  |  Edit  |  Help  —  see the menu bar above for every other section.",
0890:                  font=("Segoe UI",8),bg=COLORS["primary"],fg="#E7EFFB").pack(side="left",padx=14)
0891:         self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
0892:         self.main_body=self.body
0893:         self.dashboard()
0894:         if not getattr(self, "_update_checked_this_session", False):
0895:             self._update_checked_this_session = True
0896:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0897:         if not getattr(self, "_update_checked_this_session", False):
0898:             self._update_checked_this_session = True
0899:             # Startup check is silent: show a popup only when a newer version exists.
0900:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0901: 
```
```text
0894:         if not getattr(self, "_update_checked_this_session", False):
0895:             self._update_checked_this_session = True
0896:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0897:         if not getattr(self, "_update_checked_this_session", False):
0898:             self._update_checked_this_session = True
0899:             # Startup check is silent: show a popup only when a newer version exists.
0900:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0901: 
0902:     def _restore_dashboard_after_internal_close(self):
0903:         try:
0904:             if getattr(self, "_mdi_windows", []):
0905:                 return
0906:             host = getattr(self, "_mdi_host", None)
0907:             if host is not None and host.winfo_exists():
0908:                 host.place_forget()
0909:             # Repaint the existing Dashboard only after the child is fully closed.
0910:             # This restores the visible Dashboard surface without changing its layout.
0911:             self.after_idle(self.home)
0912:         except Exception:
0913:             try:
0914:                 self.after_idle(self.dashboard)
```
```text
1017:             xb.pack(side="left")
1018:             old_task=state.get("task")
1019:             try:
1020:                 if old_task is not None and old_task is not item and old_task.winfo_exists():
1021:                     old_task.destroy()
1022:             except Exception:
1023:                 pass
1024:             state["task"]=item
1025:         def close():
1026:             try:
1027:                 task=state.get("task")
1028:                 if task and task.winfo_exists(): task.destroy()
1029:             except Exception: pass
1030:             try:
1031:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
1032:             except Exception: pass
1033:             try: outer.destroy()
1034:             except Exception: pass
1035:             if not getattr(self,"_mdi_windows",[]):
1036:                 self._mdi_host.place_forget()
1037:                 self._restore_dashboard_after_internal_close()
```
```text
1030:             try:
1031:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
1032:             except Exception: pass
1033:             try: outer.destroy()
1034:             except Exception: pass
1035:             if not getattr(self,"_mdi_windows",[]):
1036:                 self._mdi_host.place_forget()
1037:                 self._restore_dashboard_after_internal_close()
1038:                 self._restore_dashboard_after_internal_close()
1039:                 # Restore the original application shell FIRST, then rebuild
1040:                 # only the Dashboard body. This keeps the top header/navigation
1041:                 # exactly as they are when the application starts.
1042:                 try:
1043:                     if getattr(self,"_shell_header",None) is not None and self._shell_header.winfo_exists():
1044:                         self._shell_header.pack(fill="x",before=self.body)
1045:                     if getattr(self,"_shell_nav",None) is not None and self._shell_nav.winfo_exists():
1046:                         self._shell_nav.pack(fill="x",before=self.body,after=self._shell_header)
1047:                 except Exception: pass
1048:                 try:
1049:                     self.dashboard()
1050:                 except Exception: pass
```
```text
1083:             return None
1084:         self._inventory_codes_filter=criteria
1085:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1086:         try:
1087:             self.items(container=body)
1088:             win.lift()
1089:             return win
1090:         except Exception:
1091:             try: win._internal_close()
1092:             except Exception: pass
1093:             raise
1094: 
1095:     def open_inventory_codes_report_window(self, criteria=None):
1096:         """Open Inventory Codes as a real report-style child window.
1097: 
1098:         This intentionally mirrors the supplied Preview Report workflow: a
1099:         separate resizable/maximizable window with a left navigation tree,
1100:         compact report toolbar, Find dialog, and print/export commands.
1101:         The main application remains open behind it.
1102:         """
1103:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
1100:         compact report toolbar, Find dialog, and print/export commands.
1101:         The main application remains open behind it.
1102:         """
1103:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
1104:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
1105:         }
1106:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1107: 
1108:         # --- report-style toolbar ---
1109:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
1110:         toolbar.pack(fill="x",side="top")
1111:         toolbar.pack_propagate(False)
1112: 
1113:         def tbtn(text,cmd,width=9):
1114:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
1115:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
1116:                          padx=3,pady=1)
1117:             b.pack(side="left",padx=2,pady=6)
1118:             return b
1119: 
1120:         # --- main report body ---
```
```text
1131:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
1132:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
1133:         navscroll.config(command=code_tree.yview)
1134:         navscroll.pack(side="right",fill="y")
1135:         code_tree.pack(side="left",fill="both",expand=True)
1136: 
1137:         right=tk.Frame(content,bg="#EDEDED")
1138:         right.pack(side="left",fill="both",expand=True)
1139:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
1140:         reportbar.pack(fill="x")
1141:         reportbar.pack_propagate(False)
1142:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
1143:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
1144:         tab.pack(side="left",padx=4,pady=2)
1145:         titlevar=tk.StringVar(value="Inventory Summary")
1146:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
1147:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
1148: 
1149:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
1150:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
1151:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1285:                     vals=tree.item(iid,"values")
1286:                     if str(vals[1]).lower()==str(target).lower():
1287:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1288:                 return True
1289:             self._open_exact_find_text_popup(search_fn)
1290:             self._item_master_find_callback=find_popup
1291: 
1292: 
1293:         def print_report():
1294:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1295:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1296:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1297: 
1298:         def export_pdf():
1299:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1300:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1301:         def export_word():
1302:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1303:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1304:         def export_excel():
1305:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1301:         def export_word():
1302:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1303:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1304:         def export_excel():
1305:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1306:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1307: 
1308:         tbtn("Find",find_popup,7)
1309:         tbtn("Print",print_report,7)
1310:         tbtn("PDF",export_pdf,6)
1311:         tbtn("Word",export_word,6)
1312:         tbtn("Excel",export_excel,6)
1313:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1314:         tbtn("Refresh",load,8)
1315:         tbtn("Close",win._internal_close,7)
1316:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1317:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1318: 
1319:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1320:         build_nav(); load(); win.focus_force()
1321:         return win
```
```text
1331:         self.body=frame
1332:         closed={"done":False}
1333:         def close_window():
1334:             if closed["done"]: return
1335:             closed["done"]=True
1336:             if getattr(self,"body",None) is frame: self.body=old_body
1337:             self._page_actions=old_actions
1338:             self._item_master_find_callback=old_find
1339:             try: win._internal_close()
1340:             except Exception: win.destroy()
1341:         win._internal_close=close_window
1342:         try:
1343:             method(); self.update_idletasks(); win.lift(); return win
1344:         except Exception:
1345:             close_window(); raise
1346: 
1347:     def _manual_check_update(self):
1348:         try:
1349:             updater.check_for_update(self, manual=True)
1350:         except Exception as e:
1351:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1355:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1356:         except Exception as e:
1357:             messagebox.showerror("Current Version", str(e), parent=self)
1358: 
1359:     def build_menu_bar(self):
1360:         """Professional section / sub-section menu bar, ERP style:
1361:         Inventory > Item Master
1362:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1363:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1364:         Edit > Change Password, User Management
1365:         Help > Backup Now, Restore Backup, Network Setup
1366:         """
1367:         menubar=tk.Menu(self)
1368: 
1369:         m_inv=tk.Menu(menubar,tearoff=0)
1370:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1371:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1372:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1373:         menubar.add_cascade(label="Inventory",menu=m_inv)
1374: 
1375:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1375:         m_trans=tk.Menu(menubar,tearoff=0)
1376:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1377:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1378:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1379:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1380:         menubar.add_cascade(label="Transaction",menu=m_trans)
1381: 
1382:         m_rep=tk.Menu(menubar,tearoff=0)
1383:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1384:         m_rep.add_separator()
1385:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1386:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1387:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1388:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1389:         menubar.add_cascade(label="Report",menu=m_rep)
1390: 
1391:         m_edit=tk.Menu(menubar,tearoff=0)
1392:         m_edit.add_command(label="Change Password",command=self.change_password)
1393:         if self.is_admin:
1394:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1395:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1390: 
1391:         m_edit=tk.Menu(menubar,tearoff=0)
1392:         m_edit.add_command(label="Change Password",command=self.change_password)
1393:         if self.is_admin:
1394:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1395:         menubar.add_cascade(label="Edit",menu=m_edit)
1396: 
1397:         m_help=tk.Menu(menubar,tearoff=0)
1398:         m_help.add_command(label="Backup Now",command=self.backup_now)
1399:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1400:         m_help.add_command(label="Current Version",command=self._show_current_version)
1401:         if self.is_admin:
1402:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1403:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1404:         menubar.add_cascade(label="Help",menu=m_help)
1405: 
1406:         self.config(menu=menubar)
1407: 
1408:     def open_calendar_picker(self, var):
1409:         """Small month-grid calendar popup. Picking a day sets `var` to
1410:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1463:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1464:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1465:         return f
1466: 
1467:     def clearbody(self):
1468:         self._portable_print_context=None
1469:         for w in self.body.winfo_children(): w.destroy()
1470:         self._page_actions = {
1471:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1472:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1473:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1474:             "cancel": lambda: self.dashboard(),
1475:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1476:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1477:         }
1478:         # Single SAP-style toolbar at the very top.
1479:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1480:         self._page_action_bar=bar
1481:         self._page_action_first_button=None
1482:         def run_action(k):
1483:             if k=="edit" and not self.can_edit:
```
```text
1480:         self._page_action_bar=bar
1481:         self._page_action_first_button=None
1482:         def run_action(k):
1483:             if k=="edit" and not self.can_edit:
1484:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1485:             if k=="delete" and not self.can_delete:
1486:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1487:             self._page_actions[k]()
1488:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1489:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1490:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1491:             b.pack(side="left",padx=(0,2))
1492:             if self._page_action_first_button is None: self._page_action_first_button=b
1493:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1494: 
1495:     def _portable_print_current(self):
1496:         ctx=getattr(self,"_portable_print_context",None)
1497:         if not ctx:
1498:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1499:             return
1500:         try:
```
```text
1502:             if not data: return
1503:             title,header,columns,rows=data
1504:             self.portable_print_dialog(title,header,columns,rows)
1505:         except Exception as e:
1506:             messagebox.showerror("Portable Printer",str(e))
1507: 
1508:     def portable_print_dialog(self,title,header_lines,columns,rows):
1509:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1510:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1511:         if not WIN32PRINT_AVAILABLE:
1512:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1513:             return
1514:         try:
1515:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1516:         except Exception as e:
1517:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1518:             return
1519:         if not printers:
1520:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1521:             return
1522:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1572:                 if vals and pv.get() not in vals: pv.set(vals[0])
1573:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1574:             except Exception as ex: status.set(str(ex))
1575:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1576:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1577:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1578:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1579:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1580:         win.bind("<Escape>",lambda e:win._internal_close())
1581:         win.focus_force()
1582: 
1583:     def preview_tree(self, title, tree, header_lines=None):
1584:         """Preview the exact rows currently visible in a Treeview."""
1585:         cols=list(tree["columns"])
1586:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1587:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1588:         if not rows:
1589:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1590:             return
1591:         widths=[]
1592:         for c in cols:
```
```text
1589:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1590:             return
1591:         widths=[]
1592:         for c in cols:
1593:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1594:             except Exception: widths.append(100)
1595:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1596: 
1597:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1598:         self._page_actions.update({
1599:             "save": save or self._page_actions.get("save"),
1600:             "edit": edit or self._page_actions.get("edit"),
1601:             "delete": delete or self._page_actions.get("delete"),
1602:             "cancel": cancel or self._page_actions.get("cancel"),
1603:             "print": print or self._page_actions.get("print"),
1604:             "preview": preview or self._page_actions.get("preview"),
1605:         })
1606: 
1607:     def _add_transaction_new_button(self, command):
1608:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1609:         if bar is None or first is None: return
```
```text
1618:         sep.pack(side="left",fill="y",padx=4)
1619:         for w in existing:
1620:             try:
1621:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1622:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1623:                 else: w.pack(side="left")
1624:             except Exception: pass
1625: 
1626:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1627:         """Draw a consistent professional report header and return the first table Y.
1628: 
1629:         For GRN Receipt reports the document number is shown on the left and
1630:         the GRN Date is deliberately shown on the right in a bordered document
1631:         information panel.
1632:         """
1633:         W,H=page_size
1634:         if y_top is None: y_top=H-24
1635:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1636:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1637:         if os.path.exists(LOGO_FILE):
1638:             try:
```
```text
1631:         information panel.
1632:         """
1633:         W,H=page_size
1634:         if y_top is None: y_top=H-24
1635:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1636:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1637:         if os.path.exists(LOGO_FILE):
1638:             try:
1639:                 from reportlab.lib.utils import ImageReader
1640:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1641:             except Exception:
1642:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1643:         else:
1644:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1645:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1646:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1647:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1648:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1649: 
1650:         # Professional document information box.
1651:         info_top=logo_y-12
```
```text
1684:                 # naturally occupies the right-hand cell when supplied second.
1685:                 c.setFont("Helvetica-Bold",7)
1686:                 c.drawString(xx,yy,(label+":")[:28])
1687:                 c.setFont("Helvetica",7)
1688:                 c.drawString(xx+58,yy,val[:58])
1689:             return box_y-12
1690:         return info_top-6
1691: 
1692:     def _report_footer(self, c, page_no, page_size=A4):
1693:         W,H=page_size
1694:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1695:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1696:         current_name=str(getattr(self,"current_user","") or "Unknown User").strip()
1697:         c.drawString(24,13,f"Generated by {current_name}")
1698:         c.drawCentredString(W/2,13,"Made by Muhammad Shahzad")
1699:         c.drawRightString(W-24,13,f"Page {page_no}")
1700:         c.setFillColorRGB(0,0,0)
1701: 
1702:     def _grr_signature_block(self, c, y, page_size=A4):
1703:         """Draw the three requested transaction-document signature lines."""
1704:         W,H=page_size
```
```text
1713:             x=left+i*col_w
1714:             c.setLineWidth(0.6)
1715:             c.line(x+30,top-34,x+col_w-30,top-34)
1716:             c.setFont("Helvetica-Bold",7)
1717:             c.drawCentredString(x+col_w/2,top-48,label)
1718:         return True
1719: 
1720:     def _finish_page(self, c, page_no, page_size=A4):
1721:         self._report_footer(c,page_no,page_size); c.showPage()
1722: 
1723:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1724:         """Word-wrap `text` into a list of lines that each fit inside
1725:         max_width (points) at the given font, breaking mid-word only when a
1726:         single word is itself wider than the column."""
1727:         text=str(text) if text is not None else ""
1728:         if not text:
1729:             return [""]
1730:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1731:         lines=[]; cur=""
1732:         for word in text.split(" "):
1733:             trial=(cur+" "+word).strip() if cur else word
```
```text
1742:                     mid=(lo+hi)//2
1743:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1744:                     else: hi=mid-1
1745:                 lines.append(w[:fit_at]); w=w[fit_at:]
1746:             cur=w
1747:         if cur: lines.append(cur)
1748:         return lines or [""]
1749: 
1750:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1751:         """Create a paginated professional PDF with logo, bordered information,
1752:         GRR signature lines and page numbers. Also keep the same report data in
1753:         memory so the built-in Windows printer dialog can print directly without
1754:         requiring a PDF application's PrintTo association."""
1755:         if not hasattr(self, "_print_jobs"):
1756:             self._print_jobs = {}
1757:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1758:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1759:         page=1
1760:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1761:         usable=W-56
1762:         n=max(1,len(headers))
```
```text
1786:             for ci in range(min(len(headers),len(r))):
1787:                 cell_lines=self._wrap_text_to_width(r[ci],"Helvetica",font_size,max(20,widths[ci]-4))
1788:                 wrapped_cells.append(cell_lines)
1789:                 max_lines=max(max_lines,len(cell_lines))
1790:             row_h=max(11 if font_size<=7 else 13, max_lines*line_h+2)
1791:             # Reserve room on the final page for the three transaction signatures + footer.
1792:             reserve=120 if is_transaction_doc else 42
1793:             if y-row_h<reserve:
1794:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1795:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1796:             # Item rows are intentionally border-free. The section/header remains
1797:             # professional while avoiding the unwanted boxed line around each
1798:             # individual printed item row. Description is drawn separately
1799:             # below (auto-fit / wrapped), so it is skipped in this pass.
1800:             for ci,(xx,cell_lines) in enumerate(zip(xs,wrapped_cells)):
1801:                 for li,ln in enumerate(cell_lines):
1802:                     c.drawString(xx,y-li*line_h,ln)
1803:             y-=row_h
1804:         if is_transaction_doc:
1805:             # Keep the three requested transaction signatures at the physical bottom
1806:             # final page, immediately above the report footer.  If the item
```
```text
1802:                     c.drawString(xx,y-li*line_h,ln)
1803:             y-=row_h
1804:         if is_transaction_doc:
1805:             # Keep the three requested transaction signatures at the physical bottom
1806:             # final page, immediately above the report footer.  If the item
1807:             # table reaches this reserved area, start a fresh final page.
1808:             bottom_sig_y = 138
1809:             if y < 165:
1810:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1811:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1812:             # Draw signatures at a fixed bottom position so they never float
1813:             # directly after the last item row.
1814:             self._grr_signature_block(c,bottom_sig_y,page_size)
1815:         self._report_footer(c,page,page_size); c.save()
1816:         if auto_print:
1817:             self.print_pdf(path)
1818:         return path
1819: 
1820:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1821:         """Professional on-screen preview showing bordered document information
1822:         and a bordered item section. GRN Date is displayed in the right column."""
```
```text
1815:         self._report_footer(c,page,page_size); c.save()
1816:         if auto_print:
1817:             self.print_pdf(path)
1818:         return path
1819: 
1820:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1821:         """Professional on-screen preview showing bordered document information
1822:         and a bordered item section. GRN Date is displayed in the right column."""
1823:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1824:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1825:         # Preview intentionally hides the company logo and company name.
1826:         # The actual generated/printed PDF still contains both via
1827:         # _report_header(), so only the on-screen preview is affected.
1828:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1829:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1830:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1831: 
1832:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
1833:         parsed=[]
1834:         for item in header_lines or []:
1835:             if isinstance(item,(tuple,list)) and len(item)>=2:
```
```text
1853:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1854: 
1855:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1856:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1857:         tr=self.make_tree(items,columns,widths)
1858:         for r in rows: tr.insert("", "end", values=r)
1859: 
1860:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1861:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1862:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1863:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1864:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1865:         win.bind("<Control-f>",bind_preview_find)
1866:         win.bind("<Control-F>",bind_preview_find)
1867: 
1868:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1869:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1870:         if is_transaction_preview:
1871:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1872:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1873:                 sig.columnconfigure(i,weight=1)
```
```text
1871:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1872:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1873:                 sig.columnconfigure(i,weight=1)
1874:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1875:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1876:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1877: 
1878:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1879:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1880:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1881:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1882:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1883:         if on_save:
1884:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1885:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1886:         if not is_transaction_preview:
1887:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1888:         # IMPORTANT: this must remain a normal top-level window (not transient
1889:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1890:         # exactly like the Preview Report window in the supplied recording.
1891:         # The Find dialog is opened from this window and is independent.
```
```text
1884:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1885:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1886:         if not is_transaction_preview:
1887:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1888:         # IMPORTANT: this must remain a normal top-level window (not transient
1889:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1890:         # exactly like the Preview Report window in the supplied recording.
1891:         # The Find dialog is opened from this window and is independent.
1892:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1893:         win.focus_force()
1894: 
1895:     def _safe_report_name(self, title, extension):
1896:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1897:         safe=safe.replace(" ","_") or "Preview"
1898:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1899: 
1900:     def print_preview_window(self, title, header_lines, columns, rows):
1901:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1902:         self._open_direct_printer(title, header_lines, columns, rows,
1903:                                   landscape(A4) if len(columns) > 8 else A4)
1904: 
```
```text
1897:         safe=safe.replace(" ","_") or "Preview"
1898:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1899: 
1900:     def print_preview_window(self, title, header_lines, columns, rows):
1901:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1902:         self._open_direct_printer(title, header_lines, columns, rows,
1903:                                   landscape(A4) if len(columns) > 8 else A4)
1904: 
1905:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1906:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1907:         This keeps the Export PDF button functional on a machine where the bundled
1908:         ReportLab package cannot be imported."""
1909:         def esc(v):
1910:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1911:         W,H=842,595
1912:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1913:         def add(txt,size=8,leading=11):
1914:             lines.append(f"/F1 {size} Tf")
1915:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1916:         add(str(title),12,16)
1917:         for h in header_lines or []:
```
```text
1924:         lines.append("ET")
1925:         stream="\n".join(lines).encode("latin-1","replace")
1926:         objs=[]
1927:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1928:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1929:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1930:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1931:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1932:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1933:         for i,obj in enumerate(objs,1):
1934:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1935:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1936:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1937:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1938:         with open(path,"wb") as f: f.write(out)
1939: 
1940:     def _save_entry_report(self, title, header_lines, columns, rows):
1941:         try:
1942:             os.makedirs(REPORTS_DIR, exist_ok=True)
1943:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1944:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```
```text
1937:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1938:         with open(path,"wb") as f: f.write(out)
1939: 
1940:     def _save_entry_report(self, title, header_lines, columns, rows):
1941:         try:
1942:             os.makedirs(REPORTS_DIR, exist_ok=True)
1943:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1944:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
1945:             path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
1946:             page_size = landscape(A4) if len(columns) > 8 else A4
1947:             if REPORTLAB:
1948:                 self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
1949:             else:
1950:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1951:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1952:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1953:             with open(path, "rb") as f:
1954:                 if f.read(5) != b"%PDF-":
1955:                     raise IOError("Generated report is not a valid PDF.")
1956:             self._last_entry_report_path = path
1957:             return path
```
```text
1951:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1952:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1953:             with open(path, "rb") as f:
1954:                 if f.read(5) != b"%PDF-":
1955:                     raise IOError("Generated report is not a valid PDF.")
1956:             self._last_entry_report_path = path
1957:             return path
1958:         except Exception as exc:
1959:             self._last_entry_report_path = None
1960:             return None
1961: 
1962:     def export_preview_pdf(self, title, header_lines, columns, rows):
1963:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1964:         try:
1965:             os.makedirs(REPORTS_DIR, exist_ok=True)
1966:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1967:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1968:             generated = False
1969:             if REPORTLAB:
1970:                 try:
1971:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
```
```text
1968:             generated = False
1969:             if REPORTLAB:
1970:                 try:
1971:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1972:                     generated = True
1973:                 except Exception:
1974:                     generated = False
1975:             if not generated:
1976:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1977:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1978:                 raise IOError("The PDF file was not created in the Reports folder.")
1979:             with open(path, "rb") as pf:
1980:                 signature = pf.read(5)
1981:             if signature != b"%PDF-":
1982:                 raise IOError("The generated file is not a valid PDF.")
1983:             self._last_report_path = path
1984:             try:
1985:                 webbrowser.open("file://" + path)
1986:             except Exception:
1987:                 self.open_file(path)
1988:             return path
```
```text
1982:                 raise IOError("The generated file is not a valid PDF.")
1983:             self._last_report_path = path
1984:             try:
1985:                 webbrowser.open("file://" + path)
1986:             except Exception:
1987:                 self.open_file(path)
1988:             return path
1989:         except Exception as e:
1990:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1991:             return None
1992: 
1993:     def export_preview_word(self, title, header_lines, columns, rows):
1994:         """Export exactly what is visible in the current preview to Word."""
1995:         if not DOCX_AVAILABLE:
1996:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1997:         path=self._safe_report_name(title,"docx")
1998:         doc=Document()
1999:         sec=doc.sections[0]
2000:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
2001:         sec.header.paragraphs[0].runs[0].bold=True
2002:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
```
```text
2024:             doc.add_paragraph("")
2025:             sig=doc.add_table(rows=2,cols=3)
2026:             labels=["Prepared By","Store Keeper","Store Incharge"]
2027:             for i,label in enumerate(labels):
2028:                 sig.cell(0,i).text="____________________"
2029:                 sig.cell(1,i).text=label
2030:                 for para in sig.cell(1,i).paragraphs:
2031:                     for run in para.runs: run.bold=True
2032:         doc.save(path)
2033:         self.open_file(path)
2034: 
2035:     def export_preview_excel(self, title, header_lines, columns, rows):
2036:         """Export exactly what is visible in the current preview to Excel."""
2037:         if not XLSX_AVAILABLE:
2038:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
2039:         path=self._safe_report_name(title,"xlsx")
2040:         wb=openpyxl.Workbook(); ws=wb.active
2041:         ws.title="Preview"
2042:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
2043:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
2044:         if not is_transaction_preview:
```
```text
2062:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
2063:             for col in range(1,4):
2064:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
2065:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
2066:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
2067:         for col_cells in ws.columns:
2068:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
2069:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
2070:         wb.save(path)
2071:         self.open_file(path)
2072: 
2073:     def _auto_fit_tree_columns(self, tr, max_width=420):
2074:         try:
2075:             import tkinter.font as tkfont
2076:             try:
2077:                 font=tkfont.nametofont("TkDefaultFont")
2078:             except Exception:
2079:                 font=None
2080:             children=tr.get_children("")
2081:             sample=children[:250]
2082:             for c in tr["columns"]:
```
```text
2181:                     w.state(["!disabled"] if editable else ["disabled"])
2182:             except Exception:
2183:                 try: w.configure(state="normal" if editable else "disabled")
2184:                 except Exception: pass
2185:             for ch in w.winfo_children(): walk(ch)
2186:         for root in roots: walk(root)
2187: 
2188:     def document_selector(self, parent, label, typ, var, load_callback):
2189:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
2190:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
2191:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
2192:         combo.pack(side="left", padx=4)
2193:         def refresh():
2194:             vals=[]
2195:             if typ=="demand":
2196:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
2197:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
2198:             elif typ=="grr":
2199:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
2200:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
2201:             else:
```
```text
2208:             no=text.split(" -> ",1)[0].strip()
2209:             var.set(no)
2210:             load_callback(no)
2211:         combo.bind("<<ComboboxSelected>>", selected)
2212:         combo.bind("<Return>", selected)
2213:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2214:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2215:         refresh()
2216:         # Keep the currently open transaction's saved-record list live.
2217:         # Each save calls refresh_saved_cache(), so newly saved records appear
2218:         # immediately without closing/reopening the window or pressing Refresh.
2219:         if not hasattr(self, "_document_selector_refreshers"):
2220:             self._document_selector_refreshers = {}
2221:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2222:         return combo
2223: 
2224:     def dashboard(self):
2225:         # Dashboard-only visual refresh. All existing data queries, filters,
2226:         # callbacks and report/detail behavior are intentionally preserved.
2227:         self.clearbody()
2228:         c=self.conn
```
```text
2309:             for x in tr.get_children(): tr.delete(x)
2310:             params=[];where=[]
2311:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2312:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2313:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2314:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2315:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2316:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2317:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2318:                    FROM transactions t JOIN items i ON i.code=t.code"""
2319:             if where: sql += " WHERE " + " AND ".join(where)
2320:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2321:             rows=list(c.execute(sql,params))
2322:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2323:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2324:             bal_after={}
2325:             for txid,cc,typ,qty in alltx:
2326:                 running.setdefault(cc,0.0)
2327:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2328:                 bal_after[txid]=running[cc]
2329:             for r in rows:
```
```text
2704:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2705:         load()
2706:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2707: 
2708:     def inventory_codes(self):
2709:         """Inventory Codes using the classic desktop inventory interface.
2710: 
2711:         This screen intentionally follows the uploaded Inventory Management
2712:         reference: a simple module title, compact New/Edit/Delete/Save/
2713:         Refresh/Print/Close action row, and a full-width editable data grid.
2714:         All records come from the V18 database, so existing inventory data is
2715:         preserved rather than recreated.
2716:         """
2717:         self.clearbody()
2718:         # Remove the generic SAP action row; this page owns its own classic
2719:         # action row just like the reference Inventory/Items screen.
2720:         if self.body.winfo_children():
2721:             try:
2722:                 self.body.winfo_children()[0].destroy()
2723:             except Exception:
2724:                 pass
```
```text
2777:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2778:         if filter_text:
2779:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2780:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2781: 
2782:         editing={"id":None,"new":False}
2783:         cell_editor={"widget":None}
2784: 
2785:         def close_editor(save_value=False):
2786:             w=cell_editor.get("widget")
2787:             if not w:
2788:                 return
2789:             try:
2790:                 if save_value:
2791:                     w.event_generate("<Return>")
2792:                 w.destroy()
2793:             except Exception:
2794:                 pass
2795:             cell_editor["widget"]=None
2796: 
2797:         def edit_cell(event=None):
```
```text
2807:             bbox=tree.bbox(iid,colid)
2808:             if not bbox: return
2809:             close_editor(False)
2810:             x,y,w,h=bbox
2811:             val=str(tree.item(iid,"values")[idx] or "")
2812:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2813:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2814:             cell_editor["widget"]=e
2815:             def commit(_=None):
2816:                 try:
2817:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2818:                 finally:
2819:                     try:e.destroy()
2820:                     except Exception:pass
2821:                     cell_editor["widget"]=None
2822:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2823:             e.bind("<FocusOut>",commit)
2824: 
2825:         def rows_query():
2826:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2827:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2829:             if tc: where.append("code <= ?"); params.append(tc)
2830:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2831:             if df or dt:
2832:                 sub=[]; sp=[]
2833:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2834:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2835:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2836:                 params.extend(sp)
2837:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2838:             return sql,params
2839: 
2840:         def load():
2841:             close_editor(False)
2842:             for i in tree.get_children(): tree.delete(i)
2843:             sql,params=rows_query()
2844:             count=0
2845:             for r in self.conn.execute(sql,params):
2846:                 # V18 stores UOM/opening and the original application may have
2847:                 # rate/remarks columns in some versions. Read them safely.
2848:                 rid,code,desc,uom,opening,rate,remarks=r
2849:                 bal=stock(self.conn,code)
```
```text
2863:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2864:             editing["id"]=None; editing["new"]=True
2865:             # Put the user directly into the Code cell.
2866:             try:
2867:                 bbox=tree.bbox(iid,"#2")
2868:                 if bbox:
2869:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2870:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2871:                     def commit(_=None):
2872:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2873:                         try:e.destroy()
2874:                         except Exception:pass
2875:                         cell_editor["widget"]=None
2876:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2877:             except Exception: pass
2878:             status.set("New row added — enter values, then press Save")
2879: 
2880:         def selected_row():
2881:             a=tree.selection()
2882:             return a[0] if a else None
2883: 
```
```text
2883: 
2884:         def edit_record():
2885:             iid=selected_row()
2886:             if not iid:
2887:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2888:             if not self.can_edit and not self.is_admin:
2889:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2890:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2891:             status.set("Edit mode — double-click any cell to change it, then press Save")
2892:             tree.focus(iid); tree.see(iid)
2893: 
2894:         def save_record():
2895:             iid=selected_row()
2896:             if not iid:
2897:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2898:             if not self.can_edit and not self.is_admin:
2899:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2900:             close_editor(True)
2901:             vals=list(tree.item(iid,"values"))
2902:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2903:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2901:             vals=list(tree.item(iid,"values"))
2902:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2903:             try: opening=float(str(vals[4]).strip() or 0)
2904:             except Exception: raise ValueError("Opening Qty must be a number.")
2905:             try: rate=float(str(vals[5]).strip() or 0)
2906:             except Exception: raise ValueError("Rate must be a number.")
2907:             remarks=str(vals[6]).strip()
2908:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2909:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2910:             if not desc:
2911:                 messagebox.showerror("Save","Description is required."); return
2912:             if opening<0:
2913:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2914:             rid=vals[0]
2915:             try:
2916:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2917:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2918:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2919:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2920:                 if rid:
2921:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2924:                                       (code,desc,uom,opening,rid))
2925:                     if oldcode!=code:
2926:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2927:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2928:                             except Exception:pass
2929:                 else:
2930:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2931:                                       (code,desc,uom,"",opening,0,"Local",0))
2932:                 self.conn.commit()
2933:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2934:                 backup_database(); load()
2935:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2936:             except Exception as ex:
2937:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2938: 
2939:         def delete_record():
2940:             iid=selected_row()
2941:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2942:             if not self.can_delete and not self.is_admin:
2943:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2944:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2940:             iid=selected_row()
2941:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2942:             if not self.can_delete and not self.is_admin:
2943:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2944:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2945:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2946:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2947:             try:
2948:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2949:             except Exception as ex:
2950:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2951: 
2952:         def refresh(): load()
2953:         def do_print():
2954:             try:self.preview_tree("Inventory Codes",tree)
2955:             except Exception as ex:messagebox.showerror("Print",str(ex))
2956:         def do_close(): self.dashboard()
2957: 
2958:         btn("New",new_record,8)
2959:         btn("Edit",edit_record,8)
2960:         btn("Delete",delete_record,8)
```
```text
2953:         def do_print():
2954:             try:self.preview_tree("Inventory Codes",tree)
2955:             except Exception as ex:messagebox.showerror("Print",str(ex))
2956:         def do_close(): self.dashboard()
2957: 
2958:         btn("New",new_record,8)
2959:         btn("Edit",edit_record,8)
2960:         btn("Delete",delete_record,8)
2961:         btn("Save",save_record,8)
2962:         btn("Refresh",refresh,9)
2963:         btn("Preview",do_print,8)
2964:         btn("Print",do_print,8)
2965:         btn("Close",do_close,8)
2966: 
2967:         # Search is deliberately small and sits on the right, without changing
2968:         # the reference layout of the action buttons.
2969:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2970:         search=tk.StringVar()
2971:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2972:         se.pack(side="left",padx=2)
2973:         self._item_master_search_entry=se
```
```text
2981:                     tree.detach(iid)
2982:         search.trace_add("write",filter_grid)
2983:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2984: 
2985:         tree.bind("<Double-1>",edit_cell)
2986:         tree.bind("<F2>",lambda e: edit_record())
2987:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2988:         self._page_actions={
2989:             "save":save_record,"edit":edit_record,"delete":delete_record,
2990:             "cancel":do_close,"print":do_print,"preview":do_print
2991:         }
2992:         load()
2993: 
2994:     def open_mto_inventory_flow(self):
2995:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2996: 
2997:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2998:         Cancel/X only closes the popup.
2999:         """
3000:         criteria = self._ask_mto_inventory_filters()
3001:         if not criteria or criteria.get("cancelled"):
```
```text
3163:                 return False
3164:             destination.set(found_dest)
3165:             edit_mode.update(on=True, original=r[0], dest=found_dest)
3166:             code.set(r[0])
3167:             desc.set(r[1] or "")
3168:             uom.set(r[2] or UOM_OPTIONS[0])
3169:             opening.set(str(r[3] if r[3] is not None else 0))
3170:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
3171:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
3172:             err.set("")
3173:             edit_btn.configure(text="SAVE EDIT")
3174:             ce.focus_set()
3175:             return True
3176: 
3177:         def check_duplicates(*_):
3178:             c = code.get().strip()
3179:             d = desc.get().strip()
3180:             dest = destination.get()
3181:             msgs = []
3182:             r = row_for(dest, c) if len(norm(c)) == 8 else None
3183:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
3185:             dh = desc_hit(dest, d) if d else None
3186:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
3187:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
3188:             hint.set("\n".join(msgs))
3189: 
3190:         code.trace_add("write", check_duplicates)
3191:         desc.trace_add("write", check_duplicates)
3192: 
3193:         def save_code():
3194:             try:
3195:                 c = code.get().strip()
3196:                 d = desc.get().strip()
3197:                 u = uom.get().strip()
3198:                 dest = destination.get()
3199:                 digits = norm(c)
3200:                 if len(digits) != 8:
3201:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3202:                 if not d:
3203:                     raise ValueError("Description is required.")
3204:                 try:
3205:                     op = float(opening.get().strip() or 0)
```
```text
3226:                         (c, d, u, op, iso, old)
3227:                     )
3228:                     action = "updated"
3229:                 else:
3230:                     self.conn.execute(
3231:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3232:                         (c, d, u, "", op, 0, iso)
3233:                     )
3234:                     action = "saved"
3235:                 self.conn.commit()
3236:                 backup_database()
3237:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3238:                 # Keep popup open for fast multiple entries.
3239:                 clear_form(keep_search=False)
3240:                 ce.focus_set()
3241:             except Exception as ex:
3242:                 self.conn.rollback()
3243:                 err.set(str(ex))
3244:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3245: 
3246:         def edit_action():
```
```text
3242:                 self.conn.rollback()
3243:                 err.set(str(ex))
3244:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3245: 
3246:         def edit_action():
3247:             if not edit_mode["on"]:
3248:                 load_for_edit()
3249:             else:
3250:                 save_code()
3251: 
3252:         def delete_code():
3253:             if not edit_mode["on"]:
3254:                 if not load_for_edit():
3255:                     return
3256:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3257:                 return
3258:             try:
3259:                 t = table_for(edit_mode["dest"])
3260:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3261:                 self.conn.commit()
3262:                 backup_database()
```
```text
3258:             try:
3259:                 t = table_for(edit_mode["dest"])
3260:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3261:                 self.conn.commit()
3262:                 backup_database()
3263:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3264:                 clear_form(keep_search=False)
3265:             except Exception as ex:
3266:                 self.conn.rollback()
3267:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3268: 
3269:         btns = ttk.Frame(box)
3270:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3271:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3272:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3273:         edit_btn.pack(side="left", padx=4, ipadx=8)
3274:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3275:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3276:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3277:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3278:         ce.focus_set()
```
```text
3272:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3273:         edit_btn.pack(side="left", padx=4, ipadx=8)
3274:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3275:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3276:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3277:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3278:         ce.focus_set()
3279: 
3280:     def _mto_new_item_dialog(self, on_saved):
3281:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3282:         brand-new item can be created without leaving that screen. Writes
3283:         straight into the same Item Master (items table) used everywhere."""
3284:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3285:         win.transient(self); win.grab_set()
3286:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3287:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3288:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3289:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3290:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3291:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3292:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3288:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3289:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3290:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3291:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3292:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3293:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3294:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3295:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3296:         def save():
3297:             try:
3298:                 c=code.get().strip(); d=desc.get().strip()
3299:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3300:                 if not d: raise ValueError("Description is required.")
3301:                 try:
3302:                     opening_val=float(opening.get() or 0)
3303:                 except ValueError:
3304:                     raise ValueError("Opening Qty must be a number.")
3305:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3306:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3307:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3308:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3301:                 try:
3302:                     opening_val=float(opening.get() or 0)
3303:                 except ValueError:
3304:                     raise ValueError("Opening Qty must be a number.")
3305:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3306:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3307:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3308:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3309:                 self.conn.commit(); backup_database()
3310:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3311:                 win.grab_release(); win.destroy()
3312:                 on_saved()
3313:             except Exception as ex: messagebox.showerror("Error",str(ex))
3314:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3315:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3316:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3317: 
3318:     def _item_filter_bar(self, parent, on_change):
3319:         """Item Code entry + item-master picker + Search/Show All. Calls
3320:         on_change() whenever the code changes or a button is pressed."""
3321:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3407:         self._item_master_find_callback=None
3408:         self._portable_print_context=None
3409:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3410:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3411:         }
3412: 
3413:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3414:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3415:         self.conn.commit()
3416: 
3417:         # ---- Same professional in-app window layout as Inventory Codes ----
3418:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3419:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3420:                   foreground=COLORS["primary_dark"]).pack(side="left")
3421:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3422: 
3423:         def open_find():
3424:             state_find={"index":-1}
3425:             def search_fn(text):
3426:                 text=text.strip().lower()
3427:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3514:             for i in table.get_children(): table.delete(i)
3515:             where=["1=1"]; params=[]
3516:             prefix=state.get("prefix",""); q=search.get().strip()
3517:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3518:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3519:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3520:             if fc: where.append("code >= ?"); params.append(fc)
3521:             if tc: where.append("code <= ?"); params.append(tc)
3522:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3523:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3524:             records=[]
3525:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3526:                 # If a date filter is supplied, accept an opening-date match OR
3527:                 # a transaction in that date range. This prevents valid MTO codes
3528:                 # from disappearing merely because an older record has no opening_date.
3529:                 if df or dt:
3530:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3531:                     if not ok:
3532:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3533:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3534:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3604:                 tr.insert("", "end", values=r)
3605:         def clear():
3606:             for x in v.values(): x.set("")
3607:             try: tr.selection_remove(tr.selection())
3608:             except Exception: pass
3609:             self._set_form_editable(party_form_roots, False)
3610:         def new_form():
3611:             clear(); self._set_form_editable(party_form_roots, True)
3612:         def save():
3613:             try:
3614:                 name=v["name"].get().strip()
3615:                 if not name: raise ValueError("Party Name is required.")
3616:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3617:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3618:             except Exception as ex: messagebox.showerror("Error",str(ex))
3619:         def load_party_row(a):
3620:             if not a:return
3621:             r=tr.item(a[0])["values"]
3622:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3623:             self._set_form_editable(party_form_roots, False)
3624:         def on_party_select(_=None):
```
```text
3630:             load_party_row(a)
3631:             self._set_form_editable(party_form_roots, True)
3632:         def delete_party():
3633:             a=tr.selection()
3634:             if not a:
3635:                 messagebox.showwarning("Delete", "Select a party first."); return
3636:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3637:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3638:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3639:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3640:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3641:         self._add_transaction_new_button(new_form)
3642:         load(); clear()
3643: 
3644:     def user_management(self):
3645:         self.clearbody()
3646:         if not self.is_admin:
3647:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3648:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3649:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3650:         role=tk.StringVar(value="User")
```
```text
3687:             u_ent.state(["!disabled"])
3688:         def edit():
3689:             a=tr.selection()
3690:             if not a:
3691:                 messagebox.showwarning("Edit User","Select a user row first."); return
3692:             r=tr.item(a[0])["values"]
3693:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3694:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3695:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3696:         def save():
3697:             try:
3698:                 username=v["username"].get().strip()
3699:                 if not username: raise ValueError("Username is required.")
3700:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3701:                 pw=v["password"].get()
3702:                 if exists:
3703:                     pw_hash = hash_password(pw) if pw else exists[0]
3704:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3705:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3706:                 else:
3707:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3702:                 if exists:
3703:                     pw_hash = hash_password(pw) if pw else exists[0]
3704:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3705:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3706:                 else:
3707:                     if not pw: raise ValueError("Password is required for a new user.")
3708:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3709:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3710:                 self.conn.commit(); backup_database(); load(); clear()
3711:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3712:             except Exception as ex:
3713:                 messagebox.showerror("Error", str(ex))
3714:         def delete_user():
3715:             a=tr.selection()
3716:             if not a:
3717:                 messagebox.showwarning("Delete User","Select a user row first."); return
3718:             username=tr.item(a[0])["values"][0]
3719:             if username==self.current_user:
3720:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3721:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3722:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3717:                 messagebox.showwarning("Delete User","Select a user row first."); return
3718:             username=tr.item(a[0])["values"][0]
3719:             if username==self.current_user:
3720:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3721:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3722:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3723:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3724:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3725:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3726:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3727:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3728:         load()
3729: 
3730:     @staticmethod
3731:     def _renumber_tree(tree, rows):
3732:         for i,iid in enumerate(tree.get_children()):
3733:             vals=list(tree.item(iid,"values"));
3734:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3735: 
3736:     def demand(self):
3737:         self.clearbody(); self.demand_lines=[]
```
```text
3734:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3735: 
3736:     def demand(self):
3737:         self.clearbody(); self.demand_lines=[]
3738:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3739:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3740:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3741:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3742:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3743:         # Demand Date is intentionally displayed as its own dedicated field.
3744:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3745:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3746:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3747:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3748:                 ("special","Special Instructions"),("source","Recommended Source")]
3749:         for i,(k,n) in enumerate(fields):
3750:             r=i//4*2+3; c=i%4*2
3751:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3752:             if k=="dept":
3753:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3754:             elif k=="urgency":
```
```text
3824:         def new_form():
3825:             self._editing_document_key=None
3826:             for z in v.values(): z.set("")
3827:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3828:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3829:             for iid in tree.get_children(): tree.delete(iid)
3830:             self._set_form_editable(form_roots, True, skip=[selector])
3831: 
3832:         def save():
3833:             try:
3834:                 no=v["no"].get().strip()
3835:                 if not no: raise ValueError("Demand No is required.")
3836:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3837:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3838:                 if dup and getattr(self,"_editing_document_key",None) != no:
3839:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3840:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3841:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3842:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3843:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3844:                 self.conn.commit()
```
```text
3837:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3838:                 if dup and getattr(self,"_editing_document_key",None) != no:
3839:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3840:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3841:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3842:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3843:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3844:                 self.conn.commit()
3845:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3846:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3847:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3848:             except Exception as ex: messagebox.showerror("Error",str(ex))
3849:         form_roots=[f,line,editbar]
3850:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3851:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3852:         def delete_current():
3853:             no=v["no"].get().strip()
3854:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3855:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3856:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3857:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3870:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3871:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3872:                     f"Justification: {v['just'].get()}",
3873:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3874:             if not self.demand_lines:
3875:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3876:             self.show_preview_window("Purchase Demand", header,
3877:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3878:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3879:         def edit_saved_demand():
3880:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3881:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3882:             self._set_form_editable(form_roots, True, skip=[selector])
3883:         def print_now():
3884:             if not self.demand_lines:
3885:                 messagebox.showwarning("Print","Add at least one item line first."); return
3886:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3887:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3888:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3889:                     f"Justification: {v['just'].get()}",
3890:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3886:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3887:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3888:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3889:                     f"Justification: {v['just'].get()}",
3890:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3891:             self._open_direct_printer("Purchase Demand",header,
3892:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3893:                 self.demand_lines,A4)
3894:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3895:         self._add_transaction_new_button(new_form)
3896:         self._set_form_editable(form_roots, False, skip=[selector])
3897:         try:
3898:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3899:         except Exception: pass
3900:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3901: 
3902:     def load_demand_into_form(self,no,v,tree):
3903:         v["no"].set(no)
3904:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3905:         if not r:return
3906:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3908:         self.demand_lines=[]
3909:         for i in tree.get_children():tree.delete(i)
3910:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3911:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3912:         roots=getattr(self,"_transaction_form_roots",None)
3913:         if roots and "demand" in roots:
3914:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3915: 
3916:     def refresh_saved_cache(self,typ):
3917:         # Refresh saved-document dropdowns immediately after a successful save.
3918:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3919:         alive=[]
3920:         for combo, refresh in refreshers:
3921:             try:
3922:                 if combo.winfo_exists():
3923:                     refresh()
3924:                     alive.append((combo, refresh))
3925:             except Exception:
3926:                 pass
3927:         if hasattr(self, "_document_selector_refreshers"):
3928:             self._document_selector_refreshers[typ] = alive
```
```text
3927:         if hasattr(self, "_document_selector_refreshers"):
3928:             self._document_selector_refreshers[typ] = alive
3929: 
3930:     def grr(self):
3931:         self.clearbody(); self.grr_lines=[]
3932:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3933:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3934:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3935:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3936:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3937:         for i,(k,n) in enumerate(fields):
3938:             r=i//4*2+2;c=i%4*2
3939:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3940:             if k=="department":
3941:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3942:             elif k=="supplier":
3943:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3944:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3945:             elif k=="date":
3946:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3947:             else:
```
```text
3996:         def new_form():
3997:             self._editing_document_key=None
3998:             for z in v.values(): z.set("")
3999:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
4000:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
4001:             for iid in tree.get_children(): tree.delete(iid)
4002:             self._set_form_editable(form_roots, True, skip=[selector])
4003: 
4004:         def save():
4005:             try:
4006:                 no=v["no"].get().strip()
4007:                 if not no:raise ValueError("GRN No is required.")
4008:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
4009:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
4010:                 if dup and getattr(self,"_editing_document_key",None) != no:
4011:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
4012:                 if not self.grr_lines:raise ValueError("Add at least one item.")
4013:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
4014:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
4015:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
4016:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
4013:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
4014:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
4015:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
4016:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
4017:                 for x in self.grr_lines:
4018:                     ltype=x[10] if len(x)>10 else "Local"
4019:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
4020:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
4021:                 self.conn.commit()
4022:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
4023:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
4024:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4025:             except Exception as ex:messagebox.showerror("Error",str(ex))
4026:         form_roots=[f,line,editbar]
4027:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4028:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
4029:         def delete_current():
4030:             no=v["no"].get().strip()
4031:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
4032:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
4033:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
4026:         form_roots=[f,line,editbar]
4027:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4028:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
4029:         def delete_current():
4030:             no=v["no"].get().strip()
4031:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
4032:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
4033:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
4034:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
4035:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
4036:         def cancel_form():
4037:             self._editing_document_key=None
4038:             self._set_form_editable(form_roots, False, skip=[selector])
4039:             for z in v.values(): z.set("")
4040:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
4041:             itype.set("Local")
4042:             self.grr_lines.clear()
4043:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
4044:             for iid in tree.get_children(): tree.delete(iid)
4045:         def preview_now():
4046:             if not self.grr_lines:
```
```text
4055:                     ("Challan #", v['challan'].get()),
4056:                     ("Vehicle #", v['vehicle'].get()),
4057:                     ("Bill/Voucher #", v['bill'].get()),
4058:                     ("Reference", v['ref'].get()),
4059:                     ("Remarks", v['remarks'].get()),
4060:                     ("Total Value", fmt_num(total))]
4061:             self.show_preview_window("GRN Receipt", header,
4062:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
4063:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
4064:         def portable_current():
4065:             total=sum(float(x[8] or 0) for x in self.grr_lines)
4066:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
4067:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
4068:         self._portable_print_context=portable_current
4069:         def edit_saved_grr():
4070:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4071:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
4072:             self._set_form_editable(form_roots, True, skip=[selector])
4073:         def print_now():
4074:             if not self.grr_lines:
4075:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
4079:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
4080:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
4081:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
4082:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
4083:                     ("Total Value", fmt_num(total))]
4084:             self._open_direct_printer("GRN Receipt",header,
4085:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
4086:                 self.grr_lines,landscape(A4))
4087:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
4088:         self._add_transaction_new_button(new_form)
4089:         self._set_form_editable(form_roots, False, skip=[selector])
4090:         try:
4091:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
4092:         except Exception: pass
4093:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
4094: 
4095:     def load_grr_into_form(self,no,v,tree):
4096:         v["no"].set(no)
4097:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
4098:         if not r:return
4099:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
4106:         if roots and "grr" in roots:
4107:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
4108: 
4109:     def issue(self):
4110:         self.clearbody(); self.issue_lines=[]
4111:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
4112:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
4113:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
4114:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
4115:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
4116:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
4117:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
4118:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
4119:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
4120:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
4121:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
4122:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
4123:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
4124:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
4125:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
4126:         itype=tk.StringVar(value="Local")
```
```text
4195:                 # Editing an existing issue replaces its old stock transaction and detail lines.
4196:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
4197:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
4198:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
4199:                 for x in self.issue_lines:
4200:                     ltype=x[7] if len(x)>7 else "Local"
4201:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
4202:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
4203:                 self.conn.commit()
4204:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
4205:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
4206:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4207:             except Exception as ex:messagebox.showerror("Error",str(ex))
4208:         def delete_current():
4209:             no=v["no"].get().strip()
4210:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
4211:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
4212:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
4213:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
4214:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
4215:         def cancel_form():
```
```text
4223:             for iid in tree.get_children(): tree.delete(iid)
4224:         def preview_now():
4225:             if not self.issue_lines:
4226:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4227:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4228:                     f"Items Use For: {v['items_use_for'].get()}"]
4229:             self.show_preview_window("Material Issue", header,
4230:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4231:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4232:         def portable_current():
4233:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4234:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4235:         self._portable_print_context=portable_current
4236:         form_roots=[f,usebar,line,editbar]
4237:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4238:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4239:         def load_saved_issue(no):
4240:             self.load_issue_into_form(no,v,tree)
4241:             self._set_form_editable(form_roots, False, skip=[selector])
4242:         def edit_saved_issue():
4243:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4236:         form_roots=[f,usebar,line,editbar]
4237:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4238:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4239:         def load_saved_issue(no):
4240:             self.load_issue_into_form(no,v,tree)
4241:             self._set_form_editable(form_roots, False, skip=[selector])
4242:         def edit_saved_issue():
4243:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4244:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4245:             self._set_form_editable(form_roots, True, skip=[selector])
4246:         def print_issue_now():
4247:             if not self.issue_lines:
4248:                 messagebox.showwarning("Print","Add at least one item line first."); return
4249:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4250:             self._open_direct_printer("Material Issue",header,
4251:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4252:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4253:         self._add_transaction_new_button(new_form)
4254:         self._set_form_editable(form_roots, False, skip=[selector])
4255:         self._active_form_loader = load_saved_issue
4256: 
```
```text
4264:         for i in tree.get_children():tree.delete(i)
4265:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4266:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4267:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4268:         roots=getattr(self,"_transaction_form_roots",None)
4269:         if roots and "issue" in roots:
4270:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4271: 
4272:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4273:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4274: 
4275:         The layout intentionally matches Inventory Codes' Selection Criteria
4276:         popup so all Report sub-sections have one consistent desktop workflow.
4277:         """
4278:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4279:         win=tk.Toplevel(self)
4280:         win.title(f"{report_title} - Selection Criteria")
4281:         win.resizable(False,False)
4282:         win.transient(self); win.grab_set()
4283:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4284:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4329:             except Exception: pass
4330:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4331:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4332:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4333:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4334:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4335:         e1.focus_set(); self.wait_window(win); return result
4336: 
4337:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4338:         self._pending_report_filters=criteria
4339:         try:
4340:             return self.open_menu_window(method,title,geometry)
4341:         finally:
4342:             self._pending_report_filters=None
4343: 
4344:     def open_stock_balance_report_flow(self):
4345:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4346:         if f.get("cancelled"): return None
4347:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4348: 
4349:     def open_grr_report_flow(self):
```
```text
4342:             self._pending_report_filters=None
4343: 
4344:     def open_stock_balance_report_flow(self):
4345:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4346:         if f.get("cancelled"): return None
4347:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4348: 
4349:     def open_grr_report_flow(self):
4350:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4351:         if f.get("cancelled"): return None
4352:         return self._open_report_child(self.report_grr,"GRN Report",f)
4353: 
4354:     def open_demand_report_flow(self):
4355:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4356:         if f.get("cancelled"): return None
4357:         return self._open_report_child(self.report_demand,"Demand Report",f)
4358: 
4359:     def open_issue_report_flow(self):
4360:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4361:         if f.get("cancelled"): return None
4362:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4356:         if f.get("cancelled"): return None
4357:         return self._open_report_child(self.report_demand,"Demand Report",f)
4358: 
4359:     def open_issue_report_flow(self):
4360:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4361:         if f.get("cancelled"): return None
4362:         return self._open_report_child(self.report_issue,"Issue Report",f)
4363: 
4364:     def open_party_report_flow(self):
4365:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4366:         if f.get("cancelled"): return None
4367:         return self._open_report_child(self.report_party,"Party Report",f)
4368: 
4369:     def _ask_stock_balance_filters(self):
4370:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4371:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4372:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4373:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4374:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4375:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4376:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4388:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4389:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4390:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4391:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4392:         e1.focus_set();self.wait_window(win);return result
4393: 
4394:     def stock_balance(self):
4395:         self.clearbody()
4396:         # Stock Balance is a Report sub-section and does not use the generic
4397:         # Save/Edit/Delete/Cancel/Print action strip.
4398:         children=self.body.winfo_children()
4399:         if children:
4400:             children[0].destroy()
4401:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4402:         if initial.get("cancelled"):
4403:             self.dashboard(); return
4404:         top=ttk.Frame(self.body);top.pack(fill="x")
4405:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4406:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4407:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4408:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4418:             for typ,qty in self.conn.execute(q,params):
4419:                 if typ=="GRR":gr+=float(qty or 0)
4420:                 elif typ=="ISSUE":iss+=float(qty or 0)
4421:             return opening_before,gr,iss,opening_before+gr-iss
4422:         def header_summary():
4423:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4424:         def load():
4425:             for i in tr.get_children():tr.delete(i)
4426:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4427:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4428:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4429:             sql+=" ORDER BY code"
4430:             for r in self.conn.execute(sql,params):
4431:                 op,gr,iss,cur=period(r[0],r[3])
4432:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4433:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4434:         def reopen_filters():
4435:             initial2=self._ask_stock_balance_filters()
4436:             if initial2.get("cancelled"):return
4437:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4438:             load()
```
```text
4476:         """
4477:         if typ=="demand": self.demand()
4478:         elif typ=="grr": self.grr()
4479:         else: self.issue()
4480:         loader=getattr(self,"_active_form_loader",None)
4481:         if loader: loader(str(no))
4482: 
4483:     def _edit_from_selector(self, typ, var, loader):
4484:         """Top Edit action: load the saved document directly into the current form.
4485:         If nothing is selected, use the newest saved document; never open a popup.
4486:         """
4487:         text=var.get().strip()
4488:         if text:
4489:             no=text.split(" -> ",1)[0].strip()
4490:         else:
4491:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4492:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4493:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4494:             if not r:
4495:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4496:                 return
```
```text
4493:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4494:             if not r:
4495:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4496:                 return
4497:             no=str(r[0])
4498:             var.set(no)
4499:         loader(no)
4500: 
4501:     def show_saved_records(self,typ):
4502:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4503:         if typ=="demand":
4504:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4505:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4506:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4507:             for r in rows:
4508:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4509:                 r=list(r); r[1]=to_display_date(r[1])
4510:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4511:         elif typ=="grr":
4512:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4513:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4524:         def view():
4525:             a=tr.selection()
4526:             if not a:return
4527:             no=tr.item(a[0])["values"][0]
4528:             win.destroy();self.open_document_editor(typ,no)
4529:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4530:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4531:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4532:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4533: 
4534:     def documents(self):
4535:         self.clearbody()
4536:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4537:         specs=[
4538:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4539:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4540:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4541:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4542:             ("Material Issues","issue",("No","Date","Department"),
4543:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4544:         ]
```
```text
4540:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4541:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4542:             ("Material Issues","issue",("No","Date","Department"),
4543:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4544:         ]
4545:         for title,typ,cols,query in specs:
4546:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4547:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4548:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4549:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4550:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4551:             for r in self.conn.execute(query):
4552:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4553:             def edit_selected(t=tr,k=typ):
4554:                 a=t.selection()
4555:                 if not a:
4556:                     messagebox.showwarning("Edit", "Select a saved record first.")
4557:                     return
4558:                 no=t.item(a[0])["values"][0]
4559:                 self.open_document_editor(k,no)
4560:             def delete_selected(t=tr,k=typ):
```
```text
4555:                 if not a:
4556:                     messagebox.showwarning("Edit", "Select a saved record first.")
4557:                     return
4558:                 no=t.item(a[0])["values"][0]
4559:                 self.open_document_editor(k,no)
4560:             def delete_selected(t=tr,k=typ):
4561:                 a=t.selection()
4562:                 if not a:
4563:                     messagebox.showwarning("Delete", "Select a saved record first.")
4564:                     return
4565:                 no=t.item(a[0])["values"][0]
4566:                 if k=="demand":
4567:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4568:                 elif k=="grr":
4569:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4570:                 else:
4571:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4572:                 self.conn.commit();backup_database();self.documents()
4573:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4574:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4575:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4569:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4570:                 else:
4571:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4572:                 self.conn.commit();backup_database();self.documents()
4573:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4574:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4575:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4576:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4577:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4578:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4579:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4580: 
4581:     def doc_export_selected(self,typ,tr,fmt):
4582:         a=tr.selection()
4583:         if not a:
4584:             messagebox.showwarning("Export","Select a saved record first."); return
4585:         no=tr.item(a[0])["values"][0]
4586:         if fmt=="word": self.export_word(typ,no)
4587:         else: self.export_excel(typ,no)
4588: 
4589:     def doc_preview_selected(self,typ,tr):
```
```text
4584:             messagebox.showwarning("Export","Select a saved record first."); return
4585:         no=tr.item(a[0])["values"][0]
4586:         if fmt=="word": self.export_word(typ,no)
4587:         else: self.export_excel(typ,no)
4588: 
4589:     def doc_preview_selected(self,typ,tr):
4590:         a=tr.selection()
4591:         if not a:
4592:             messagebox.showwarning("Preview","Select a saved record first."); return
4593:         no=tr.item(a[0])["values"][0]
4594:         data=self._get_doc_data(typ,no)
4595:         if not data:
4596:             messagebox.showwarning("Preview","Document not found."); return
4597:         title,header,cols,rows=data
4598:         header_lines=header
4599:         self.show_preview_window(title,header_lines,cols,rows)
4600: 
4601:     def doc_print_selected(self,typ,tr):
4602:         a=tr.selection()
4603:         if not a: return
4604:         no=tr.item(a[0])["values"][0]
```
```text
4635:         def _print_loaded_document():
4636:             data=self._get_doc_data(typ,no)
4637:             if not data:
4638:                 messagebox.showwarning("Document","Document not found."); return
4639:             title,header,cols,rows=data
4640:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4641:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4642: 
4643:     def _report_filter_popup(self, title, include_party=False):
4644:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4645:         win,winbody=self._internal_window(title,"520x420")
4646:         done=tk.BooleanVar(value=False)
4647:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4648:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4649:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4650:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4651:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4652:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4653:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4654:         if include_party:
4655:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4649:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4650:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4651:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4652:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4653:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4654:         if include_party:
4655:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4656:         def ok():
4657:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4658:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4659:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4660:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4661: 
4662:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4663:         self.clearbody()
4664:         # Report sub-sections use their own report toolbar; remove only the
4665:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4666:         children=self.body.winfo_children()
4667:         if children:
4668:             children[0].destroy()
4669:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4670:         if f.get("cancelled"):
4671:             self.dashboard();return
4672:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4673:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4674:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4675:         def load():
4676:             for i in tr.get_children():tr.delete(i)
4677:             params,where=params_builder(f)
4678:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4679:             for r in self.conn.execute(sql,params):
4680:                 vals=list(r)
4681:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4682:                 tr.insert("","end",values=vals)
4683:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4684:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4685:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4686:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4687:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4688:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4689:         def open_find_report():
4690:             state_find={"index":-1}
```
```text
4696:                 order=children[start:]+children[:start]
4697:                 for iid in order:
4698:                     vals=tr.item(iid,"values")
4699:                     if any(text in str(v).lower() for v in vals):
4700:                         state_find["index"]=children.index(iid)
4701:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4702:                 return False
4703:             self._open_exact_find_text_popup(search_fn)
4704:         self._item_master_find_callback=open_find_report
4705:         load()
4706:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4707: 
4708:     def report_grr(self):
4709:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4710:         def pb(f):
4711:             w=[];p=[]
4712:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4713:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4714:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4715:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4716:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4711:             w=[];p=[]
4712:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4713:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4714:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4715:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4716:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4717:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4718:             return p,w
4719:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4720: 
4721:     def report_demand(self):
4722:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4723:         def pb(f):
4724:             w=[];p=[]
4725:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4726:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4727:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4728:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4729:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4730:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4731:             return p,w
```
```text
4724:             w=[];p=[]
4725:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4726:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4727:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4728:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4729:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4730:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4731:             return p,w
4732:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4733: 
4734:     def report_issue(self):
4735:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4736:         def pb(f):
4737:             w=[];p=[]
4738:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4739:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4740:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4741:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4742:             return p,w
4743:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4744: 
```
```text
4737:             w=[];p=[]
4738:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4739:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4740:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4741:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4742:             return p,w
4743:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4744: 
4745:     def report_party(self):
4746:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4747:         def pb(f):
4748:             w=[];p=[]
4749:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4750:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4751:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4752:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4753:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4754:             return p,w
4755:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4756: 
4757:     def reports(self):
```
```text
4755:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4756: 
4757:     def reports(self):
4758:         self.clearbody()
4759:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4760: 
4761:         # ================= GRN Details =================
4762:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4763:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4764:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4765:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4766:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4767:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4768: 
4769:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4770:         def load_grr_item(codev=None):
4771:             for i in tr.get_children(): tr.delete(i)
4772:             q=codev.get().strip() if codev else ""
4773:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4774:             for r in self.conn.execute(sql,(q,) if q else ()):
4775:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4781:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4782:         tr=self.make_tree(fr,grr_cols,grr_widths)
4783:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4784:             for i in tr.get_children(): tr.delete(i)
4785:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4786:             conds=[];params=[]
4787:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4788:             if td: conds.append("g.grr_date<=?");params.append(td)
4789:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4790:             for r in self.conn.execute(sql,params):
4791:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4792:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4793:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4794:         load_grr_date(fdv,tdv)
4795: 
4796:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4797:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4798:         party=tk.StringVar(value="ALL")
4799:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4800:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4801:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4797:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4798:         party=tk.StringVar(value="ALL")
4799:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4800:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4801:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4802:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4803:         def load_party(*_):
4804:             for i in tr.get_children(): tr.delete(i)
4805:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4806:             if party.get()=="ALL":
4807:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4808:             else:
4809:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4810:             for r in rows:
4811:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4812:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4813:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4814: 
4815:         # ================= Demand Details =================
4816:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4817:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4813:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4814: 
4815:         # ================= Demand Details =================
4816:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4817:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4818:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4819:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4820:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4821:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4822: 
4823:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4824:         def load_dem_item(codev=None):
4825:             for i in tr.get_children(): tr.delete(i)
4826:             q=codev.get().strip() if codev else ""
4827:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4828:             for r in self.conn.execute(sql,(q,) if q else ()):
4829:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4830:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4831:         tr=self.make_tree(fr,dem_cols,dem_widths)
4832:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4833:         load_dem_item(codev)
```
```text
4835:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4836:         tr=self.make_tree(fr,dem_cols,dem_widths)
4837:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4838:             for i in tr.get_children(): tr.delete(i)
4839:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4840:             conds=[];params=[]
4841:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4842:             if td: conds.append("d.demand_date<=?");params.append(td)
4843:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4844:             for r in self.conn.execute(sql,params):
4845:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4846:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4847:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4848:         load_dem_date(fdv,tdv)
4849: 
4850:         # ================= Material Issue Details =================
4851:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4852:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4853:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4854:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4855:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4848:         load_dem_date(fdv,tdv)
4849: 
4850:         # ================= Material Issue Details =================
4851:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4852:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4853:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4854:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4855:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4856:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4857: 
4858:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4859:         def load_iss_item(codev=None):
4860:             for i in tr.get_children(): tr.delete(i)
4861:             q=codev.get().strip() if codev else ""
4862:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4863:             for r in self.conn.execute(sql,(q,) if q else ()):
4864:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4865:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4866:         tr=self.make_tree(fr,iss_cols,iss_widths)
4867:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4868:         load_iss_item(codev)
```
```text
4870:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4871:         tr=self.make_tree(fr,iss_cols,iss_widths)
4872:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4873:             for i in tr.get_children(): tr.delete(i)
4874:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4875:             conds=[];params=[]
4876:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4877:             if td: conds.append("i.issue_date<=?");params.append(td)
4878:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4879:             for r in self.conn.execute(sql,params):
4880:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4881:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4882:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4883:         load_iss_date(fdv,tdv)
4884: 
4885:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4886: 
4887:     def print_item_master(self):
4888:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4889:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4890: 
```
```text
4887:     def print_item_master(self):
4888:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4889:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4890: 
4891:     def print_party_master(self):
4892:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4893:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4894: 
4895:     def print_report(self,kind):
4896:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4897:         if kind=="grr":
4898:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4899:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4900:         elif kind=="demand":
4901:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4902:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4903:         elif kind=="issue":
4904:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4905:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4906:         else:
4907:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4908:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4909:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4910: 
4911:     def print_stock(self):
4912:         rows=[]
4913:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4914:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4915:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4916:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4917: 
4918:     def print_ledger(self):
4919:         rows=[]
4920:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4921:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4922:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4923:                 running += x[3] if x[1]=="GRR" else -x[3]
4924:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4925:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4926: 
4927:     def _get_doc_data(self, typ, no):
4928:         """Header + line items for one saved document, used by the on-screen
```
```text
4994:             sig=doc.add_table(rows=2,cols=3)
4995:             labels=["Prepared By","Store Keeper","Store Incharge"]
4996:             for i,label in enumerate(labels):
4997:                 sig.cell(0,i).text="____________________"
4998:                 sig.cell(1,i).text=label
4999:                 for para in sig.cell(1,i).paragraphs:
5000:                     for run in para.runs: run.bold=True
5001:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
5002:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
5003:         doc.save(path)
5004:         self.open_file(path)
5005: 
5006:     def export_excel(self, typ, no):
5007:         if not no or not no.strip():
5008:             return messagebox.showwarning("Excel Export","Select a document first.")
5009:         if not XLSX_AVAILABLE:
5010:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
5011:         data=self._get_doc_data(typ,no)
5012:         if not data:
5013:             return messagebox.showwarning("Excel Export","Document not found.")
5014:         title,header,cols,rows=data
```
```text
5036:             for col in range(1,4):
5037:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
5038:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
5039:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
5040:         for col_cells in ws.columns:
5041:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
5042:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
5043:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
5044:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
5045:         wb.save(path)
5046:         self.open_file(path)
5047: 
5048:     def preview_pdf(self,typ,no):
5049:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
5050:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
5051:         data=self._get_doc_data(typ,no)
5052:         if not data:return messagebox.showwarning("Document","Document not found.")
5053:         title,header,cols,rows=data
5054:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
5055:         page_size = landscape(A4) if typ == "grr" else A4
5056:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
5051:         data=self._get_doc_data(typ,no)
5052:         if not data:return messagebox.showwarning("Document","Document not found.")
5053:         title,header,cols,rows=data
5054:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
5055:         page_size = landscape(A4) if typ == "grr" else A4
5056:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
5057: 
5058:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
5059:         """Open the print dialog with a real visual preview of the exact report.
5060: 
5061:         The report is rendered to a temporary PDF only in memory/on disk for the
5062:         duration of printing.  It is deleted after the print dialog closes, so
5063:         the Print button does not leave a PDF report behind.  Printing uses the
5064:         rendered report page itself rather than rebuilding rows as plain text;
5065:         this keeps the printed page identical to the application's report.
5066:         """
5067:         # Printing is always prepared as an A4 landscape page. This only affects
5068:         # the print path; the rest of the application's UI/report logic is unchanged.
5069:         page_size = landscape(A4)
5070:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
5071:             messagebox.showwarning(
```
```text
5073:                 "The print preview/printing components are not available.\n\n"
5074:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
5075:             )
5076:             return
5077:         if not rows and not columns:
5078:             messagebox.showwarning("Print", "There is no data to print.")
5079:             return
5080:         try:
5081:             os.makedirs(REPORTS_DIR, exist_ok=True)
5082:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
5083:             self._pdf_table_report(key,title,columns,rows,page_size,
5084:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
5085:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
5086:             self._select_windows_printer_for_pdf(key)
5087:         except Exception as e:
5088:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
5089: 
5090:     def _select_windows_printer_for_pdf(self, path):
5091:         """Print dialog with an actual page preview, printer selection and direct GDI output.
5092: 
5093:         The preview is rendered from the exact PDF produced by the application,
```
```text
5123:         job=getattr(self, "_print_jobs", {}).get(path)
5124:         if job:
5125:             title, header_lines, columns, rows, source_page_size = job
5126:         else:
5127:             title=os.path.splitext(os.path.basename(path))[0]
5128:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
5129: 
5130:         try:
5131:             doc=fitz.open(path)
5132:             total_pages=max(1,doc.page_count)
5133:         except Exception as e:
5134:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
5135:             return
5136: 
5137:         win=tk.Toplevel(self)
5138:         win.title("Printing from Win32 application - Print")
5139:         win.geometry("900x620")
5140:         win.minsize(850,580)
5141:         win.transient(self)
5142:         win.configure(bg="#f0f0f0")
5143: 
```
```text
5149:             pass
5150: 
5151:         outer=tk.Frame(win,bg="#f0f0f0")
5152:         outer.pack(fill="both",expand=True)
5153:         outer.columnconfigure(1,weight=1)
5154:         outer.rowconfigure(0,weight=1)
5155: 
5156:         # Left side mirrors the familiar system printer dialog: printers and
5157:         # print options. Right side contains the actual report page preview.
5158:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
5159:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
5160:         left.grid_propagate(False)
5161:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
5162:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
5163:         printer_list.pack(fill="x")
5164:         for pr in printers: printer_list.insert("end",pr)
5165:         try: printer_list.selection_set(printers.index(default_printer))
5166:         except Exception: printer_list.selection_set(0)
5167: 
5168:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
5169:         copies=tk.IntVar(value=1)
```
```text
5242:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5243: 
5244:         bottom=tk.Frame(win,bg="#f0f0f0")
5245:         # `outer` already uses pack() in `win`; using grid() for another direct
5246:         # child of the same toplevel raises TclError. Keep the action bar in the
5247:         # same geometry-manager family so Print/Cancel are always visible.
5248:         bottom.pack(fill="x",padx=12,pady=(0,12))
5249:         bottom.columnconfigure(0,weight=1)
5250:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5251:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5252:         print_btn=ttk.Button(bottom,text="Print",width=12)
5253:         print_btn.grid(row=0,column=2,padx=(8,0))
5254: 
5255:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5256: 
5257:         def parse_page_selection(total):
5258:             if pages_mode.get()=="All pages": return list(range(total))
5259:             raw=page_range.get().strip()
5260:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5261:             selected=[]
5262:             for part in raw.split(","):
```
```text
5259:             raw=page_range.get().strip()
5260:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5261:             selected=[]
5262:             for part in raw.split(","):
5263:                 part=part.strip()
5264:                 if "-" in part:
5265:                     a,b=part.split("-",1); a=int(a); b=int(b)
5266:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5267:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5268:                     selected.extend(range(a-1,b))
5269:                 else:
5270:                     n=int(part)
5271:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5272:                     selected.append(n-1)
5273:             return list(dict.fromkeys(selected))
5274: 
5275:         def selected_printer():
5276:             sel=printer_list.curselection()
5277:             return printer_list.get(sel[0]) if sel else printers[0]
5278: 
5279:         def print_rendered_pages():
```
```text
5372:                 finally:
5373:                     if hprinter is not None:
5374:                         try: win32print.ClosePrinter(hprinter)
5375:                         except Exception: pass
5376:                     if hdc:
5377:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5378:                         except Exception: pass
5379: 
5380:                 # Print the exact rendered PDF page through the printer DC.
5381:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5382:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5383:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5384:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5385: 
5386:                 for copy_no in range(count):
5387:                     dc.StartDoc(str(title)[:80])
5388:                     doc_ok=False
5389:                     try:
5390:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5391:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5392:                             dc.StartPage()
```
```text
5391:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5392:                             dc.StartPage()
5393:                             page_ok=False
5394:                             try:
5395:                                 cell_w=printable_w/float(cols_n)
5396:                                 cell_h=printable_h/float(rows_n)
5397:                                 for j,page_index in enumerate(batch):
5398:                                     page=doc.load_page(page_index)
5399:                                     pdf_w=max(1.0,float(page.rect.width))
5400:                                     pdf_h=max(1.0,float(page.rect.height))
5401:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5402:                                     fit=max(0.25,min(fit,8.0))
5403:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5404:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5405:                                     target_w=max(1,int(cell_w*0.96))
5406:                                     target_h=max(1,int(cell_h*0.96))
5407:                                     ratio=min(target_w/img.width,target_h/img.height)
5408:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5409:                                     if (nw,nh)!=(img.width,img.height):
5410:                                         img=img.resize((nw,nh),Image.LANCZOS)
5411:                                     dib=ImageWin.Dib(img)
```
```text
5431: 
5432:                 status.set("Print job sent successfully")
5433:                 win.update_idletasks()
5434:                 win.after(500,close)
5435:             except Exception as e:
5436:                 status.set("Print failed: "+str(e))
5437:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5438: 
5439:         def close():
5440:             try: doc.close()
5441:             except Exception: pass
5442:             try: win.destroy()
5443:             except Exception: pass
5444:             # Only the temporary PDF created by the Print button is removed.
5445:             # Existing report PDFs passed through the legacy print path are preserved.
5446:             try:
5447:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5448:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5449:             except Exception: pass
5450: 
5451:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5447:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5448:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5449:             except Exception: pass
5450: 
5451:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5452:         bottom.winfo_children()[1].configure(command=close)
5453:         print_btn.configure(command=print_rendered_pages)
5454:         win.protocol("WM_DELETE_WINDOW",close)
5455:         win.bind("<Escape>",lambda e:close())
5456:         win.grab_set()
5457:         # Keep the requested printer defaults visibly selected; no manual
5458:         # adjustment is required before pressing Print.
5459:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5460:         win.after(120,lambda:render_preview(0))
5461:         win.focus_force()
5462: 
5463:     def print_pdf(self,path):
5464:         """Open a printer-selection window for a generated PDF."""
5465:         path=os.path.abspath(path)
5466:         if not os.path.exists(path):
5467:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5463:     def print_pdf(self,path):
5464:         """Open a printer-selection window for a generated PDF."""
5465:         path=os.path.abspath(path)
5466:         if not os.path.exists(path):
5467:             messagebox.showwarning("Print", "The report file could not be found.")
5468:             return
5469: 
5470:         if sys.platform.startswith("win"):
5471:             self._select_windows_printer_for_pdf(path)
5472:             return
5473: 
5474:         try:
5475:             subprocess.run(["lp", path], check=True)
5476:         except Exception as e:
5477:             messagebox.showwarning(
5478:                 "Print",
5479:                 "The operating system could not start printing.\n\n"
5480:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5481:             )
5482: 
5483:     def open_file(self,path):
```
```text
5478:                 "Print",
5479:                 "The operating system could not start printing.\n\n"
5480:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5481:             )
5482: 
5483:     def open_file(self,path):
5484:         try:
5485:             if sys.platform.startswith("win"): os.startfile(path)
5486:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5487:             else: subprocess.Popen(["xdg-open",path])
5488:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5489: 
5490:     def print_demand(self,no):
5491:         data=self._get_doc_data("demand",no)
5492:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5493:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5494:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5495:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5496: 
5497:     def print_grr(self,no):
5498:         data=self._get_doc_data("grr",no)
```
```text
5492:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5493:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5494:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5495:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5496: 
5497:     def print_grr(self,no):
5498:         data=self._get_doc_data("grr",no)
5499:         if not data:return messagebox.showwarning("Document","GRN not found.")
5500:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5501:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5502:         # GRN has a wide item table. Generate the PDF itself in landscape so
5503:         # the printer dialog and printer driver receive a landscape document
5504:         # instead of a portrait page with rotated/cropped content.
5505:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5506: 
5507:     def print_issue(self,no):
5508:         data=self._get_doc_data("issue",no)
5509:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5510:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5511:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5512:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
```

## updater.py

- Lines: 105
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
