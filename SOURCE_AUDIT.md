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

- Lines: 466
- Functions: _safe_json_value(24-27), _table_columns(28-29), snapshot_db(30-38), _row_key(39-43), _index_snapshot(44-48), merge_local_changes(49-70), _snapshot_has_records(71-73), __init__(75-91), _read_url(92-102), status_text(103-108), _request(109-118), _get_meta(119-125), _get_snapshot(126-132), _load_json(133-141), _atomic_save_json(142-156), _save_state(157-161), _save_pending(162-166), _clear_pending(167-172), _get_lock_etag(173-182), _try_acquire_lock(183-204), _release_lock(205-214), initialize(215-271), replace_local(272-289), _write_remote(290-311), push_changes(312-331), maybe_pull(332-397), __init__(400-402), execute(403-405), executemany(406-408), executescript(409-411), __getattr__(412-413), __init__(416-421), _before_write(422-425), _before_sql(426-432), execute(433-435), executemany(436-438), executescript(439-441), cursor(442-443), commit(444-455), rollback(457-460), close(461-462), backup(463-464), __getattr__(465-466)

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
0020: TABLES = (
0021:     "items", "mto_items", "parties", "demands", "demand_lines", "grr", "grr_lines",
0022:     "issues", "issue_lines", "transactions", "users",
0023: )
0024: def _safe_json_value(value: Any) -> Any:
0025:     if value is None or isinstance(value, (str, int, float, bool)):
0026:         return value
0027:     return str(value)
0028: def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
0029:     return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
0030: def snapshot_db(conn: sqlite3.Connection) -> Dict[str, Any]:
0031:     tables: Dict[str, Any] = {}
0032:     for table in TABLES:
0033:         cols = _table_columns(conn, table)
0034:         rows = []
0035:         for row in conn.execute(f"SELECT {','.join(cols)} FROM {table}").fetchall():
0036:             rows.append({col: _safe_json_value(row[i]) for i, col in enumerate(cols)})
0037:         tables[table] = {"columns": cols, "rows": rows}
0038:     return {"schema": 1, "tables": tables}
0039: def _row_key(table: str, row: Dict[str, Any]) -> Tuple[str, Any]:
0040:     if table in ("items", "mto_items", "demands", "grr", "issues", "users"):
```
```text
0066:         columns = (local.get("tables", {}).get(table, {}).get("columns") or
0067:                    remote.get("tables", {}).get(table, {}).get("columns") or
0068:                    baseline.get("tables", {}).get(table, {}).get("columns") or [])
0069:         merged["tables"][table] = {"columns": columns, "rows": list(out.values())}
0070:     return merged
0071: def _snapshot_has_records(snapshot: Dict[str, Any]) -> bool:
0072:     tables = snapshot.get("tables", {})
0073:     return any(tables.get(x, {}).get("rows") for x in TABLES)
0074: class FirebaseSync:
0075:     def __init__(self, url_file: str, install_dir: str, timeout: int = 15):
0076:         self.url_file = url_file
0077:         self.install_dir = install_dir
0078:         self.timeout = timeout
0079:         self.base_url = self._read_url()
0080:         self.enabled = bool(self.base_url and requests)
0081:         self.last_remote_version: Optional[str] = None
0082:         self.last_check = 0.0
0083:         self.check_interval = 1.5
0084:         self.pending_base: Optional[Dict[str, Any]] = None
0085:         self.pending_error: Optional[str] = None
0086:         self.session = requests.Session() if requests else None
```
```text
0082:         self.last_check = 0.0
0083:         self.check_interval = 1.5
0084:         self.pending_base: Optional[Dict[str, Any]] = None
0085:         self.pending_error: Optional[str] = None
0086:         self.session = requests.Session() if requests else None
0087:         self.client_id = f"{os.environ.get('COMPUTERNAME','PC')}-{uuid.uuid4().hex[:10]}"
0088:         data_dir = os.path.join(self.install_dir, "Data")
0089:         os.makedirs(data_dir, exist_ok=True)
0090:         self.state_path = os.path.join(data_dir, "firebase_sync_state.json")
0091:         self.pending_path = os.path.join(data_dir, "firebase_pending_sync.json")
0092:     def _read_url(self) -> str:
0093:         try:
0094:             with open(self.url_file, "r", encoding="utf-8-sig") as f:
0095:                 raw = f.read().strip().splitlines()
0096:         except Exception:
0097:             return ""
0098:         for line in raw:
0099:             line = line.strip()
0100:             if line and not line.startswith("#"):
0101:                 return line.rstrip("/")
0102:         return ""
```
```text
0097:             return ""
0098:         for line in raw:
0099:             line = line.strip()
0100:             if line and not line.startswith("#"):
0101:                 return line.rstrip("/")
0102:         return ""
0103:     def status_text(self) -> str:
0104:         if not self.enabled:
0105:             return "Firebase URL not configured"
0106:         if self.pending_error:
0107:             return "Online database sync pending"
0108:         return "Online database connected"
0109:     def _request(self, method: str, path: str, **kwargs):
0110:         if not self.enabled or not self.session:
0111:             raise RuntimeError("Firebase URL is not configured or requests is unavailable.")
0112:         url = f"{self.base_url}/{path.lstrip('/')}"
0113:         if not url.endswith(".json"):
0114:             url += ".json"
0115:         r = self.session.request(method, url, timeout=self.timeout, **kwargs)
0116:         if not r.ok:
0117:             raise RuntimeError(f"Firebase HTTP {r.status_code}: {r.text[:500]}")
```
```text
0123:         except Exception:
0124:             data = None
0125:         return (data.get("version"), data) if isinstance(data, dict) else (None, None)
0126:     def _get_snapshot(self) -> Optional[Dict[str, Any]]:
0127:         r = self._request("GET", "store_inventory/data.json")
0128:         try:
0129:             data = r.json()
0130:         except Exception as exc:
0131:             raise RuntimeError(f"Invalid Firebase data response: {exc}")
0132:         return data if isinstance(data, dict) else None
0133:     def _load_json(self, path: str) -> Optional[Dict[str, Any]]:
0134:         try:
0135:             if not os.path.exists(path):
0136:                 return None
0137:             with open(path, "r", encoding="utf-8") as f:
0138:                 value = json.load(f)
0139:             return value if isinstance(value, dict) else None
0140:         except Exception:
0141:             return None
0142:     def _atomic_save_json(self, path: str, value: Dict[str, Any]) -> None:
0143:         os.makedirs(os.path.dirname(path), exist_ok=True)
```
```text
0136:                 return None
0137:             with open(path, "r", encoding="utf-8") as f:
0138:                 value = json.load(f)
0139:             return value if isinstance(value, dict) else None
0140:         except Exception:
0141:             return None
0142:     def _atomic_save_json(self, path: str, value: Dict[str, Any]) -> None:
0143:         os.makedirs(os.path.dirname(path), exist_ok=True)
0144:         fd, tmp = tempfile.mkstemp(prefix="firebase_sync_", suffix=".tmp", dir=os.path.dirname(path))
0145:         try:
0146:             with os.fdopen(fd, "w", encoding="utf-8") as f:
0147:                 json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
0148:                 f.flush()
0149:                 os.fsync(f.fileno())
0150:             os.replace(tmp, path)
0151:         finally:
0152:             try:
0153:                 if os.path.exists(tmp):
0154:                     os.remove(tmp)
0155:             except OSError:
0156:                 pass
```
```text
0149:                 os.fsync(f.fileno())
0150:             os.replace(tmp, path)
0151:         finally:
0152:             try:
0153:                 if os.path.exists(tmp):
0154:                     os.remove(tmp)
0155:             except OSError:
0156:                 pass
0157:     def _save_state(self, snapshot: Dict[str, Any]) -> None:
0158:         try:
0159:             self._atomic_save_json(self.state_path, snapshot)
0160:         except Exception:
0161:             pass
0162:     def _save_pending(self, snapshot: Dict[str, Any], baseline: Dict[str, Any]) -> None:
0163:         try:
0164:             self._atomic_save_json(self.pending_path, {"snapshot": snapshot, "baseline": baseline, "saved_at": time.time()})
0165:         except Exception:
0166:             pass
0167:     def _clear_pending(self) -> None:
0168:         try:
0169:             if os.path.exists(self.pending_path):
```
```text
0167:     def _clear_pending(self) -> None:
0168:         try:
0169:             if os.path.exists(self.pending_path):
0170:                 os.remove(self.pending_path)
0171:         except OSError:
0172:             pass
0173:     def _get_lock_etag(self) -> tuple[Any, str]:
0174:         url = f"{self.base_url}/store_inventory/_lock.json"
0175:         r = self.session.get(url, headers={"X-Firebase-ETag": "true"}, timeout=self.timeout)
0176:         if not r.ok:
0177:             raise RuntimeError(f"Firebase lock GET HTTP {r.status_code}: {r.text[:300]}")
0178:         try:
0179:             value = r.json()
0180:         except Exception:
0181:             value = None
0182:         return value, r.headers.get("ETag", "null_etag")
0183:     def _try_acquire_lock(self, token: str) -> bool:
0184:         # The old lock could survive a crashed client forever. Use a short
0185:         # lease so one dead PC can never permanently block online sync.
0186:         value, etag = self._get_lock_etag()
0187:         if isinstance(value, dict):
```
```text
0207:             value, etag = self._get_lock_etag()
0208:             owner = value.get("token") if isinstance(value, dict) else value
0209:             if owner != token:
0210:                 return
0211:             url = f"{self.base_url}/store_inventory/_lock.json"
0212:             self.session.put(url, data="null", headers={"if-match": etag, "content-type": "application/json"}, timeout=self.timeout)
0213:         except Exception:
0214:             pass
0215:     def initialize(self, conn: sqlite3.Connection) -> None:
0216:         if not self.enabled:
0217:             return
0218:         local = snapshot_db(conn)
0219:         pending = self._load_json(self.pending_path)
0220:         state = self._load_json(self.state_path)
0221:         # A pending snapshot is the strongest local recovery source.
0222:         if isinstance(pending, dict) and isinstance(pending.get("snapshot"), dict):
0223:             local = pending["snapshot"]
0224:             self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
0225:         try:
0226:             remote = self._get_snapshot()
0227:             version, _ = self._get_meta()
```
```text
0224:             self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
0225:         try:
0226:             remote = self._get_snapshot()
0227:             version, _ = self._get_meta()
0228:             if remote and remote.get("tables"):
0229:                 # FIRST-RUN / FRESH INSTALL RULE:
0230:                 # A newly installed copy can contain seeded Inventory Codes,
0231:                 # but those seed rows are NOT a user's unsynchronized changes.
0232:                 # When there is no prior Firebase sync state and no pending
0233:                 # journal, Firebase is the source of truth and must be loaded
0234:                 # into the fresh PC. This is what makes a second PC on another
0235:                 # Internet network automatically receive the existing cloud data.
0236:                 has_sync_state = isinstance(state, dict) and _snapshot_has_records(state)
0237:                 has_pending = self.pending_base is not None
0238:                 if not has_sync_state and not has_pending:
0239:                     self.replace_local(conn, remote)
0240:                     self.last_remote_version = version
0241:                     self._save_state(remote)
0242:                 else:
0243:                     # Established installations use a three-way merge so local
0244:                     # offline/new records are preserved while remote records
```
```text
0244:                     # offline/new records are preserved while remote records
0245:                     # from other PCs are also retained.
0246:                     baseline = self.pending_base or state or {"schema": 1, "tables": {}}
0247:                     merged = merge_local_changes(remote, baseline, local)
0248:                     if merged != remote:
0249:                         new_version = self._write_remote(merged)
0250:                         self.replace_local(conn, merged)
0251:                         self.last_remote_version = new_version
0252:                         self._save_state(merged)
0253:                     else:
0254:                         self.replace_local(conn, remote)
0255:                         self.last_remote_version = version
0256:                         self._save_state(remote)
0257:                 self.pending_base = None
0258:                 self.pending_error = None
0259:                 self._clear_pending()
0260:             else:
0261:                 new_version = self._write_remote(local)
0262:                 self.last_remote_version = new_version
0263:                 self._save_state(local)
0264:                 self._clear_pending()
```
```text
0260:             else:
0261:                 new_version = self._write_remote(local)
0262:                 self.last_remote_version = new_version
0263:                 self._save_state(local)
0264:                 self._clear_pending()
0265:                 self.pending_base = None
0266:                 self.pending_error = None
0267:         except Exception as exc:
0268:             # Firebase being offline must never delete the local data. Keep
0269:             # the local snapshot and retry on the next start/commit.
0270:             self.pending_error = str(exc)
0271:             self._save_pending(local, self.pending_base or state or {"schema": 1, "tables": {}})
0272:     def replace_local(self, conn: sqlite3.Connection, snapshot: Dict[str, Any]) -> None:
0273:         old_isolation = conn.isolation_level
0274:         try:
0275:             conn.execute("BEGIN")
0276:             for table in TABLES:
0277:                 cols = _table_columns(conn, table)
0278:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0279:                 conn.execute(f"DELETE FROM {table}")
0280:                 if not rows:
```
```text
0276:             for table in TABLES:
0277:                 cols = _table_columns(conn, table)
0278:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0279:                 conn.execute(f"DELETE FROM {table}")
0280:                 if not rows:
0281:                     continue
0282:                 insert_cols = [c for c in cols if c in rows[0]]
0283:                 placeholders = ",".join("?" for _ in insert_cols)
0284:                 sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0285:                 for row in rows:
0286:                     conn.execute(sql, [row.get(c) for c in insert_cols])
0287:             conn.commit()
0288:         finally:
0289:             conn.isolation_level = old_isolation
0290:     def _write_remote(self, snapshot: Dict[str, Any]) -> str:
0291:         token = f"{self.client_id}-{uuid.uuid4().hex}"
0292:         acquired = False
0293:         last_exc = None
0294:         for _ in range(10):
0295:             try:
0296:                 if self._try_acquire_lock(token):
```
```text
0295:             try:
0296:                 if self._try_acquire_lock(token):
0297:                     acquired = True
0298:                     break
0299:             except Exception as exc:
0300:                 last_exc = exc
0301:             time.sleep(0.35)
0302:         if not acquired:
0303:             raise RuntimeError(f"Could not acquire Firebase sync lock. {last_exc or ''}".strip())
0304:         try:
0305:             new_version = f"{time.time_ns()}-{self.client_id}"
0306:             self._request("PUT", "store_inventory/data.json", json=snapshot)
0307:             self._request("PUT", "store_inventory/_meta/version.json", json=new_version)
0308:             self._request("PUT", "store_inventory/_meta/updated_by.json", json=self.client_id)
0309:             return new_version
0310:         finally:
0311:             self._release_lock(token)
0312:     def push_changes(self, conn: sqlite3.Connection, baseline: Dict[str, Any]) -> bool:
0313:         if not self.enabled:
0314:             return True
0315:         local = snapshot_db(conn)
```
```text
0316:         try:
0317:             remote = self._get_snapshot() or {"schema": 1, "tables": {}}
0318:             merged = merge_local_changes(remote, baseline or {"schema": 1, "tables": {}}, local)
0319:             new_version = self._write_remote(merged)
0320:             self.replace_local(conn, merged)
0321:             self.last_remote_version = new_version
0322:             self.pending_base = None
0323:             self.pending_error = None
0324:             self._save_state(merged)
0325:             self._clear_pending()
0326:             return True
0327:         except Exception as exc:
0328:             self.pending_base = deepcopy(baseline)
0329:             self.pending_error = str(exc)
0330:             self._save_pending(local, baseline or {"schema": 1, "tables": {}})
0331:             return False
0332:     def maybe_pull(self, conn: sqlite3.Connection) -> bool:
0333:         """Pull Firebase changes even when the remote metadata/version endpoint
0334:         is unavailable or cached. This is the live cross-PC synchronization path."""
0335:         if not self.enabled:
0336:             return False
```
```text
0335:         if not self.enabled:
0336:             return False
0337:         now = time.monotonic()
0338:         if now - self.last_check < self.check_interval:
0339:             return False
0340:         self.last_check = now
0341:         try:
0342:             # Do not depend on _meta/version for live synchronization. Read the
0343:             # actual shared dataset so a new entry saved by another laptop is
0344:             # detected even if metadata is missing, delayed, or filtered.
0345:             snapshot = self._get_snapshot()
0346:             if snapshot is None:
0347:                 return False
0348: 
0349:             # Compare the actual remote dataset with the last synchronized
0350:             # snapshot. This is intentionally simple and reliable for the
0351:             # application's dataset size.
0352:             current_signature = json.dumps(
0353:                 snapshot,
0354:                 ensure_ascii=False,
0355:                 sort_keys=True,
```
```text
0351:             # application's dataset size.
0352:             current_signature = json.dumps(
0353:                 snapshot,
0354:                 ensure_ascii=False,
0355:                 sort_keys=True,
0356:                 separators=(",", ":"),
0357:             )
0358:             state_snapshot = self._load_json(self.state_path)
0359:             state_signature = json.dumps(
0360:                 state_snapshot,
0361:                 ensure_ascii=False,
0362:                 sort_keys=True,
0363:                 separators=(",", ":"),
0364:             ) if isinstance(state_snapshot, dict) else ""
0365: 
0366:             if current_signature == state_signature:
0367:                 self.pending_error = None
0368:                 return False
0369: 
0370:             # Three-way merge remote changes with any local changes made since
0371:             # the last synchronized state. Never replace a newer local record
```
```text
0364:             ) if isinstance(state_snapshot, dict) else ""
0365: 
0366:             if current_signature == state_signature:
0367:                 self.pending_error = None
0368:                 return False
0369: 
0370:             # Three-way merge remote changes with any local changes made since
0371:             # the last synchronized state. Never replace a newer local record
0372:             # merely because another PC changed Firebase.
0373:             baseline = self.pending_base or (state_snapshot if isinstance(state_snapshot, dict) else {"schema": 1, "tables": {}})
0374:             local = snapshot_db(conn)
0375:             merged = merge_local_changes(snapshot, baseline, local)
0376: 
0377:             if merged != snapshot:
0378:                 new_version = self._write_remote(merged)
0379:                 self.replace_local(conn, merged)
0380:                 self.last_remote_version = new_version
0381:                 self._save_state(merged)
0382:             else:
0383:                 self.replace_local(conn, snapshot)
0384:                 try:
```
```text
0381:                 self._save_state(merged)
0382:             else:
0383:                 self.replace_local(conn, snapshot)
0384:                 try:
0385:                     version, _ = self._get_meta()
0386:                 except Exception:
0387:                     version = None
0388:                 self.last_remote_version = version
0389:                 self._save_state(snapshot)
0390: 
0391:             self.pending_error = None
0392:             self.pending_base = None
0393:             self._clear_pending()
0394:             return True
0395:         except Exception as exc:
0396:             self.pending_error = str(exc)
0397:             return False
0398: class _OnlineCursor:
0399:     """Cursor proxy that keeps Firebase sync active for conn.cursor().execute()."""
0400:     def __init__(self, owner, cursor):
0401:         self._owner = owner
```
```text
0395:         except Exception as exc:
0396:             self.pending_error = str(exc)
0397:             return False
0398: class _OnlineCursor:
0399:     """Cursor proxy that keeps Firebase sync active for conn.cursor().execute()."""
0400:     def __init__(self, owner, cursor):
0401:         self._owner = owner
0402:         self._cursor = cursor
0403:     def execute(self, sql, params=()):
0404:         self._owner._before_sql(sql)
0405:         return self._cursor.execute(sql, params)
0406:     def executemany(self, sql, seq_of_params):
0407:         self._owner._before_write()
0408:         return self._cursor.executemany(sql, seq_of_params)
0409:     def executescript(self, script):
0410:         self._owner._before_write()
0411:         return self._cursor.executescript(script)
0412:     def __getattr__(self, name):
0413:         return getattr(self._cursor, name)
0414: 
0415: class OnlineConnection:
```
```text
0408:         return self._cursor.executemany(sql, seq_of_params)
0409:     def executescript(self, script):
0410:         self._owner._before_write()
0411:         return self._cursor.executescript(script)
0412:     def __getattr__(self, name):
0413:         return getattr(self._cursor, name)
0414: 
0415: class OnlineConnection:
0416:     def __init__(self, db_path: str, sync: FirebaseSync):
0417:         self._conn = sqlite3.connect(db_path, timeout=20)
0418:         self._conn.execute("PRAGMA busy_timeout=20000")
0419:         self.sync = sync
0420:         self._dirty = False
0421:         self._baseline: Optional[Dict[str, Any]] = None
0422:     def _before_write(self):
0423:         if not self._dirty:
0424:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0425:             self._dirty = True
0426:     def _before_sql(self, sql):
0427:         s = str(sql).lstrip().upper()
0428:         is_read = s.startswith("SELECT") or s.startswith("PRAGMA") or s.startswith("WITH") or s.startswith("EXPLAIN")
```
```text
0425:             self._dirty = True
0426:     def _before_sql(self, sql):
0427:         s = str(sql).lstrip().upper()
0428:         is_read = s.startswith("SELECT") or s.startswith("PRAGMA") or s.startswith("WITH") or s.startswith("EXPLAIN")
0429:         if is_read and not self._dirty and self._baseline is None:
0430:             self.sync.maybe_pull(self._conn)
0431:         elif not is_read:
0432:             self._before_write()
0433:     def execute(self, sql: str, params: Iterable[Any] = ()):
0434:         self._before_sql(sql)
0435:         return self._conn.execute(sql, params)
0436:     def executemany(self, sql: str, seq_of_params):
0437:         self._before_write()
0438:         return self._conn.executemany(sql, seq_of_params)
0439:     def executescript(self, script):
0440:         self._before_write()
0441:         return self._conn.executescript(script)
0442:     def cursor(self, *args, **kwargs):
0443:         return _OnlineCursor(self, self._conn.cursor(*args, **kwargs))
0444:     def commit(self):
0445:         self._conn.commit()
```
```text
0440:         self._before_write()
0441:         return self._conn.executescript(script)
0442:     def cursor(self, *args, **kwargs):
0443:         return _OnlineCursor(self, self._conn.cursor(*args, **kwargs))
0444:     def commit(self):
0445:         self._conn.commit()
0446:         # Keep the recovery module available inside the generated sync module.
0447:         import durable_local
0448:         # Make local persistence independent of Firebase availability.
0449:         durable_local.save(self._conn)
0450:         if self._dirty:
0451:             self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
0452:             # push_changes may merge remote rows back into SQLite.
0453:             durable_local.save(self._conn)
0454:         self._dirty = False
0455:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0456: 
0457:     def rollback(self):
0458:         self._conn.rollback()
0459:         self._dirty = False
0460:         self._baseline = None
```
```text
0453:             durable_local.save(self._conn)
0454:         self._dirty = False
0455:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0456: 
0457:     def rollback(self):
0458:         self._conn.rollback()
0459:         self._dirty = False
0460:         self._baseline = None
0461:     def close(self):
0462:         self._conn.close()
0463:     def backup(self, target):
0464:         return self._conn.backup(target)
0465:     def __getattr__(self, name):
0466:         return getattr(self._conn, name)
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

- Lines: 5469
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-436), restore_database(437-454), stock(456-461), fmt_num(463-465), to_iso_date(467-476), to_display_date(478-486), fiscal_year_key(488-499), fiscal_year_range(501-504), normalize_code(506-514), format_code(516-525), attach_code_mask(527-553), set_digits(530-535), key(536-546), paste(548-551), bind_add_to_list(555-576), on_enter(558-569), __init__(580-597), _check_for_updates(599-604), _setup_style(606-642), _shade(645-650), on_close(652-657), redo_network_setup(659-675), backup_now(677-684), restore_backup(686-704), _ctrl_f(706-718), _open_exact_find_text_popup(720-765), do_find(741-750), close(751-758), _global_enter(767-779), wipe(781-782), login(784-813), do_login(799-810), change_password(815-865), save_password(837-859), logout(867-872), home(874-900), _restore_dashboard_after_internal_close(902-916), _ensure_mdi_host(918-939), _internal_window(941-1057), normal_place(957-963), restore(964-979), maximize(980-994), minimize(995-1024), close(1025-1050), open_inventory_codes_detail_flow(1059-1077), open_inventory_codes_with_filters(1079-1093), open_inventory_codes_report_window(1095-1321), tbtn(1113-1118), balance_as_of(1175-1185), build_nav(1187-1209), selected_prefix(1211-1220), load(1222-1254), page_move(1256-1257), page_first(1258-1258), page_last(1259-1263), on_nav(1267-1268), find_popup(1271-1290), search_fn(1273-1288), print_report(1293-1296), export_pdf(1298-1300), export_word(1301-1303), export_excel(1304-1306), open_menu_window(1323-1345), close_window(1333-1340), _manual_check_update(1347-1351), _show_current_version(1353-1357), build_menu_bar(1359-1406), open_calendar_picker(1408-1456), pick(1426-1428), redraw(1430-1442), nav(1444-1448), make_date_field(1458-1465), clearbody(1467-1493), run_action(1482-1487), _portable_print_current(1495-1506), portable_print_dialog(1508-1581), build_receipt(1535-1553), send(1554-1567), refresh_printers(1568-1574), preview_tree(1583-1595), set_page_actions(1597-1605), _add_transaction_new_button(1607-1624), _report_header(1626-1690), _report_footer(1692-1699), _grr_signature_block(1701-1717), _finish_page(1719-1720), _wrap_text_to_width(1722-1747), fits(1729-1729), _pdf_table_report(1749-1818), table_header(1771-1776), show_preview_window(1820-1893), _safe_report_name(1895-1898), print_preview_window(1900-1903), _fallback_pdf_export(1905-1938), esc(1909-1910), add(1913-1915), _save_entry_report(1940-1960), export_preview_pdf(1962-1991), export_preview_word(1993-2033), export_preview_excel(2035-2071), make_tree(2073-2082), pick_item(2084-2105), choose(2085-2104), ld(2092-2096), sel(2098-2102), bind_item_lookup(2107-2124), lookup(2109-2122), _set_form_editable(2127-2140), walk(2130-2139), document_selector(2142-2176), refresh(2147-2158), selected(2159-2164), dashboard(2178-2290), load_details(2262-2286), _refresh_dashboard_kpis(2292-2306), dashboard_details(2308-2312), item_history(2314-2334), _ask_item_master_filters(2336-2420), finish(2389-2401), items(2422-2660), hierarchy(2463-2472), selected_prefix(2518-2531), balance_as_of(2533-2540), load(2542-2580), set_page(2582-2583), select_node(2585-2606), open_find(2612-2631), search_fn(2614-2629), visible_rows(2636-2638), print_inventory(2639-2643), export_inventory_word(2644-2646), export_inventory_excel(2647-2649), portable_inventory(2654-2656), inventory_codes(2662-2946), btn(2698-2703), close_editor(2739-2749), edit_cell(2751-2777), commit(2769-2775), rows_query(2779-2792), load(2794-2809), new_record(2811-2832), commit(2825-2829), selected_row(2834-2836), edit_record(2838-2846), save_record(2848-2891), delete_record(2893-2904), refresh(2906-2906), do_print(2907-2909), do_close(2910-2910), filter_grid(2928-2935), open_mto_inventory_flow(2948-2971), open_code_opening_flow(2973-2981), code_opening(2983-2984), _open_code_opening_popup(2986-2987), _open_code_opening_detail(2989-3232), norm(3059-3060), table_for(3062-3063), row_for(3065-3070), search_any_destination(3072-3085), desc_hit(3087-3091), clear_form(3093-3106), load_for_edit(3108-3129), check_duplicates(3131-3142), save_code(3147-3198), edit_action(3200-3204), delete_code(3206-3221), _mto_new_item_dialog(3234-3270), save(3250-3267), _item_filter_bar(3272-3284), _date_filter_bar(3286-3294), _ask_mto_inventory_filters(3296-3341), finish(3326-3334), mto_inventory(3343-3543), open_find(3377-3396), search_fn(3379-3394), hierarchy(3415-3419), rebuild_nav(3421-3432), mto_balance(3456-3465), load(3467-3509), set_page(3511-3511), select_node(3512-3521), visible_rows(3526-3526), do_print(3527-3531), export_word(3532-3534), export_excel(3535-3537), party_master(3545-3596), load(3555-3558), clear(3559-3563), new_form(3564-3565), save(3566-3572), load_party_row(3573-3577), on_party_select(3578-3579), edit(3581-3585), delete_party(3586-3592), user_management(3598-3682), sync_role(3625-3630), load(3634-3637), clear(3638-3641), edit(3642-3649), save(3650-3667), delete_user(3668-3679), _renumber_tree(3685-3688), demand(3690-3854), _restore_demand_tree_columns(3733-3739), add(3742-3750), edit_item(3752-3764), delete_item(3766-3774), new_form(3778-3784), save(3786-3802), delete_current(3806-3812), cancel_form(3813-3821), preview_now(3822-3832), edit_saved_demand(3833-3836), print_now(3837-3847), load_demand_into_form(3856-3868), refresh_saved_cache(3870-3882), grr(3884-4047), add(3916-3924), edit_item(3926-3936), delete_item(3938-3946), new_form(3950-3956), save(3958-3979), delete_current(3983-3989), cancel_form(3990-3998), preview_now(3999-4017), portable_current(4018-4021), edit_saved_grr(4023-4026), print_now(4027-4040), load_grr_into_form(4049-4061), issue(4063-4209), old_issue_qty(4092-4095), update_balance(4096-4104), add(4106-4115), edit_item(4117-4128), new_form(4132-4138), post(4140-4161), delete_current(4162-4168), cancel_form(4169-4177), preview_now(4178-4185), portable_current(4186-4188), load_saved_issue(4193-4195), edit_saved_issue(4196-4199), print_issue_now(4200-4205), load_issue_into_form(4211-4224), _ask_report_criteria(4226-4289), finish(4275-4283), _open_report_child(4291-4296), open_stock_balance_report_flow(4298-4301), open_grr_report_flow(4303-4306), open_demand_report_flow(4308-4311), open_issue_report_flow(4313-4316), open_party_report_flow(4318-4321), _ask_stock_balance_filters(4323-4346), ok(4338-4339), cancel(4340-4340), stock_balance(4348-4411), period(4364-4375), header_summary(4376-4377), load(4378-4387), reopen_filters(4388-4392), open_find_stock(4396-4409), search_fn(4398-4408), ledger(4413-4425), open_document_editor(4427-4435), _edit_from_selector(4437-4453), show_saved_records(4455-4486), view(4478-4482), documents(4488-4533), edit_selected(4507-4513), delete_selected(4514-4526), doc_export_selected(4535-4541), doc_preview_selected(4543-4553), doc_print_selected(4555-4563), load_document(4565-4595), _print_loaded_document(4589-4594), _report_filter_popup(4597-4614), ok(4610-4611), cancel(4612-4612), _report_window(4616-4660), load(4629-4636), hdr(4637-4637), open_find_report(4643-4657), search_fn(4645-4656), report_grr(4662-4673), pb(4664-4672), report_demand(4675-4686), pb(4677-4685), report_issue(4688-4697), pb(4690-4696), report_party(4699-4709), pb(4701-4708), reports(4711-4839), load_grr_item(4724-4729), load_grr_date(4737-4745), load_party(4757-4765), load_dem_item(4778-4783), load_dem_date(4791-4799), load_iss_item(4813-4818), load_iss_date(4826-4834), print_item_master(4841-4843), print_party_master(4845-4847), print_report(4849-4863), print_stock(4865-4870), print_ledger(4872-4879), _get_doc_data(4881-4909), export_word(4911-4958), export_excel(4960-5000), preview_pdf(5002-5010), _open_direct_printer(5012-5042), _select_windows_printer_for_pdf(5044-5415), render_preview(5169-5188), on_resize(5190-5192), parse_page_selection(5211-5227), selected_printer(5229-5231), print_rendered_pages(5233-5391), close(5393-5403), print_pdf(5417-5435), open_file(5437-5442), print_demand(5444-5449), print_grr(5451-5459), print_issue(5461-5466)

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
1696:         c.drawString(24,13,REPORT_FOOTER)
1697:         c.drawCentredString(W/2,13,"Made by Zulfiqar Ali")
1698:         c.drawRightString(W-24,13,f"Page {page_no}")
1699:         c.setFillColorRGB(0,0,0)
1700: 
1701:     def _grr_signature_block(self, c, y, page_size=A4):
1702:         """Draw the three requested transaction-document signature lines."""
1703:         W,H=page_size
1704:         labels=["Prepared By","Store Keeper","Store Incharge"]
```
```text
1712:             x=left+i*col_w
1713:             c.setLineWidth(0.6)
1714:             c.line(x+30,top-34,x+col_w-30,top-34)
1715:             c.setFont("Helvetica-Bold",7)
1716:             c.drawCentredString(x+col_w/2,top-48,label)
1717:         return True
1718: 
1719:     def _finish_page(self, c, page_no, page_size=A4):
1720:         self._report_footer(c,page_no,page_size); c.showPage()
1721: 
1722:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1723:         """Word-wrap `text` into a list of lines that each fit inside
1724:         max_width (points) at the given font, breaking mid-word only when a
1725:         single word is itself wider than the column."""
1726:         text=str(text) if text is not None else ""
1727:         if not text:
1728:             return [""]
1729:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1730:         lines=[]; cur=""
1731:         for word in text.split(" "):
1732:             trial=(cur+" "+word).strip() if cur else word
```
```text
1741:                     mid=(lo+hi)//2
1742:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1743:                     else: hi=mid-1
1744:                 lines.append(w[:fit_at]); w=w[fit_at:]
1745:             cur=w
1746:         if cur: lines.append(cur)
1747:         return lines or [""]
1748: 
1749:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1750:         """Create a paginated professional PDF with logo, bordered information,
1751:         GRR signature lines and page numbers. Also keep the same report data in
1752:         memory so the built-in Windows printer dialog can print directly without
1753:         requiring a PDF application's PrintTo association."""
1754:         if not hasattr(self, "_print_jobs"):
1755:             self._print_jobs = {}
1756:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1757:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1758:         page=1
1759:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1760:         usable=W-56
1761:         n=max(1,len(headers))
```
```text
1783:             if desc_idx is not None and desc_idx < len(r):
1784:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1785:             else:
1786:                 desc_lines=[""]
1787:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1788:             # Reserve room on the final page for the three transaction signatures + footer.
1789:             reserve=120 if is_transaction_doc else 42
1790:             if y-row_h<reserve:
1791:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1792:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1793:             # Item rows are intentionally border-free. The section/header remains
1794:             # professional while avoiding the unwanted boxed line around each
1795:             # individual printed item row. Description is drawn separately
1796:             # below (auto-fit / wrapped), so it is skipped in this pass.
1797:             for ci,(xx,val) in enumerate(zip(xs,r)):
1798:                 if ci==desc_idx: continue
1799:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1800:             if desc_idx is not None and desc_idx < len(r):
1801:                 for li,ln in enumerate(desc_lines):
1802:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1803:             y-=row_h
```
```text
1798:                 if ci==desc_idx: continue
1799:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1800:             if desc_idx is not None and desc_idx < len(r):
1801:                 for li,ln in enumerate(desc_lines):
1802:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
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
```
```text
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
2073:     def make_tree(self,parent,cols,widths=None):
2074:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
2075:         tr=ttk.Treeview(fr,columns=cols,show="headings")
2076:         for i,c in enumerate(cols):
2077:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
2078:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
2079:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
2080:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
2081:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
2082:         return tr
```
```text
2135:                     w.state(["!disabled"] if editable else ["disabled"])
2136:             except Exception:
2137:                 try: w.configure(state="normal" if editable else "disabled")
2138:                 except Exception: pass
2139:             for ch in w.winfo_children(): walk(ch)
2140:         for root in roots: walk(root)
2141: 
2142:     def document_selector(self, parent, label, typ, var, load_callback):
2143:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
2144:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
2145:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
2146:         combo.pack(side="left", padx=4)
2147:         def refresh():
2148:             vals=[]
2149:             if typ=="demand":
2150:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
2151:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
2152:             elif typ=="grr":
2153:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
2154:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
2155:             else:
```
```text
2162:             no=text.split(" -> ",1)[0].strip()
2163:             var.set(no)
2164:             load_callback(no)
2165:         combo.bind("<<ComboboxSelected>>", selected)
2166:         combo.bind("<Return>", selected)
2167:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2168:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2169:         refresh()
2170:         # Keep the currently open transaction's saved-record list live.
2171:         # Each save calls refresh_saved_cache(), so newly saved records appear
2172:         # immediately without closing/reopening the window or pressing Refresh.
2173:         if not hasattr(self, "_document_selector_refreshers"):
2174:             self._document_selector_refreshers = {}
2175:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2176:         return combo
2177: 
2178:     def dashboard(self):
2179:         # Dashboard-only visual refresh. All existing data queries, filters,
2180:         # callbacks and report/detail behavior are intentionally preserved.
2181:         self.clearbody()
2182:         c=self.conn
```
```text
2263:             for x in tr.get_children(): tr.delete(x)
2264:             params=[];where=[]
2265:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2266:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2267:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2268:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2269:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2270:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2271:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2272:                    FROM transactions t JOIN items i ON i.code=t.code"""
2273:             if where: sql += " WHERE " + " AND ".join(where)
2274:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2275:             rows=list(c.execute(sql,params))
2276:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2277:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2278:             bal_after={}
2279:             for txid,cc,typ,qty in alltx:
2280:                 running.setdefault(cc,0.0)
2281:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2282:                 bal_after[txid]=running[cc]
2283:             for r in rows:
```
```text
2658:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2659:         load()
2660:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2661: 
2662:     def inventory_codes(self):
2663:         """Inventory Codes using the classic desktop inventory interface.
2664: 
2665:         This screen intentionally follows the uploaded Inventory Management
2666:         reference: a simple module title, compact New/Edit/Delete/Save/
2667:         Refresh/Print/Close action row, and a full-width editable data grid.
2668:         All records come from the V18 database, so existing inventory data is
2669:         preserved rather than recreated.
2670:         """
2671:         self.clearbody()
2672:         # Remove the generic SAP action row; this page owns its own classic
2673:         # action row just like the reference Inventory/Items screen.
2674:         if self.body.winfo_children():
2675:             try:
2676:                 self.body.winfo_children()[0].destroy()
2677:             except Exception:
2678:                 pass
```
```text
2731:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2732:         if filter_text:
2733:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2734:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2735: 
2736:         editing={"id":None,"new":False}
2737:         cell_editor={"widget":None}
2738: 
2739:         def close_editor(save_value=False):
2740:             w=cell_editor.get("widget")
2741:             if not w:
2742:                 return
2743:             try:
2744:                 if save_value:
2745:                     w.event_generate("<Return>")
2746:                 w.destroy()
2747:             except Exception:
2748:                 pass
2749:             cell_editor["widget"]=None
2750: 
2751:         def edit_cell(event=None):
```
```text
2761:             bbox=tree.bbox(iid,colid)
2762:             if not bbox: return
2763:             close_editor(False)
2764:             x,y,w,h=bbox
2765:             val=str(tree.item(iid,"values")[idx] or "")
2766:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2767:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2768:             cell_editor["widget"]=e
2769:             def commit(_=None):
2770:                 try:
2771:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2772:                 finally:
2773:                     try:e.destroy()
2774:                     except Exception:pass
2775:                     cell_editor["widget"]=None
2776:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2777:             e.bind("<FocusOut>",commit)
2778: 
2779:         def rows_query():
2780:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2781:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2783:             if tc: where.append("code <= ?"); params.append(tc)
2784:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2785:             if df or dt:
2786:                 sub=[]; sp=[]
2787:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2788:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2789:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2790:                 params.extend(sp)
2791:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2792:             return sql,params
2793: 
2794:         def load():
2795:             close_editor(False)
2796:             for i in tree.get_children(): tree.delete(i)
2797:             sql,params=rows_query()
2798:             count=0
2799:             for r in self.conn.execute(sql,params):
2800:                 # V18 stores UOM/opening and the original application may have
2801:                 # rate/remarks columns in some versions. Read them safely.
2802:                 rid,code,desc,uom,opening,rate,remarks=r
2803:                 bal=stock(self.conn,code)
```
```text
2817:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2818:             editing["id"]=None; editing["new"]=True
2819:             # Put the user directly into the Code cell.
2820:             try:
2821:                 bbox=tree.bbox(iid,"#2")
2822:                 if bbox:
2823:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2824:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2825:                     def commit(_=None):
2826:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2827:                         try:e.destroy()
2828:                         except Exception:pass
2829:                         cell_editor["widget"]=None
2830:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2831:             except Exception: pass
2832:             status.set("New row added — enter values, then press Save")
2833: 
2834:         def selected_row():
2835:             a=tree.selection()
2836:             return a[0] if a else None
2837: 
```
```text
2837: 
2838:         def edit_record():
2839:             iid=selected_row()
2840:             if not iid:
2841:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2842:             if not self.can_edit and not self.is_admin:
2843:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2844:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2845:             status.set("Edit mode — double-click any cell to change it, then press Save")
2846:             tree.focus(iid); tree.see(iid)
2847: 
2848:         def save_record():
2849:             iid=selected_row()
2850:             if not iid:
2851:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2852:             if not self.can_edit and not self.is_admin:
2853:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2854:             close_editor(True)
2855:             vals=list(tree.item(iid,"values"))
2856:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2857:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2855:             vals=list(tree.item(iid,"values"))
2856:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2857:             try: opening=float(str(vals[4]).strip() or 0)
2858:             except Exception: raise ValueError("Opening Qty must be a number.")
2859:             try: rate=float(str(vals[5]).strip() or 0)
2860:             except Exception: raise ValueError("Rate must be a number.")
2861:             remarks=str(vals[6]).strip()
2862:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2863:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2864:             if not desc:
2865:                 messagebox.showerror("Save","Description is required."); return
2866:             if opening<0:
2867:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2868:             rid=vals[0]
2869:             try:
2870:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2871:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2872:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2873:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2874:                 if rid:
2875:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2878:                                       (code,desc,uom,opening,rid))
2879:                     if oldcode!=code:
2880:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2881:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2882:                             except Exception:pass
2883:                 else:
2884:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2885:                                       (code,desc,uom,"",opening,0,"Local",0))
2886:                 self.conn.commit()
2887:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2888:                 backup_database(); load()
2889:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2890:             except Exception as ex:
2891:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2892: 
2893:         def delete_record():
2894:             iid=selected_row()
2895:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2896:             if not self.can_delete and not self.is_admin:
2897:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2898:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2894:             iid=selected_row()
2895:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2896:             if not self.can_delete and not self.is_admin:
2897:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2898:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2899:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2900:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2901:             try:
2902:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2903:             except Exception as ex:
2904:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2905: 
2906:         def refresh(): load()
2907:         def do_print():
2908:             try:self.preview_tree("Inventory Codes",tree)
2909:             except Exception as ex:messagebox.showerror("Print",str(ex))
2910:         def do_close(): self.dashboard()
2911: 
2912:         btn("New",new_record,8)
2913:         btn("Edit",edit_record,8)
2914:         btn("Delete",delete_record,8)
```
```text
2907:         def do_print():
2908:             try:self.preview_tree("Inventory Codes",tree)
2909:             except Exception as ex:messagebox.showerror("Print",str(ex))
2910:         def do_close(): self.dashboard()
2911: 
2912:         btn("New",new_record,8)
2913:         btn("Edit",edit_record,8)
2914:         btn("Delete",delete_record,8)
2915:         btn("Save",save_record,8)
2916:         btn("Refresh",refresh,9)
2917:         btn("Preview",do_print,8)
2918:         btn("Print",do_print,8)
2919:         btn("Close",do_close,8)
2920: 
2921:         # Search is deliberately small and sits on the right, without changing
2922:         # the reference layout of the action buttons.
2923:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2924:         search=tk.StringVar()
2925:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2926:         se.pack(side="left",padx=2)
2927:         self._item_master_search_entry=se
```
```text
2935:                     tree.detach(iid)
2936:         search.trace_add("write",filter_grid)
2937:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2938: 
2939:         tree.bind("<Double-1>",edit_cell)
2940:         tree.bind("<F2>",lambda e: edit_record())
2941:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2942:         self._page_actions={
2943:             "save":save_record,"edit":edit_record,"delete":delete_record,
2944:             "cancel":do_close,"print":do_print,"preview":do_print
2945:         }
2946:         load()
2947: 
2948:     def open_mto_inventory_flow(self):
2949:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2950: 
2951:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2952:         Cancel/X only closes the popup.
2953:         """
2954:         criteria = self._ask_mto_inventory_filters()
2955:         if not criteria or criteria.get("cancelled"):
```
```text
3117:                 return False
3118:             destination.set(found_dest)
3119:             edit_mode.update(on=True, original=r[0], dest=found_dest)
3120:             code.set(r[0])
3121:             desc.set(r[1] or "")
3122:             uom.set(r[2] or UOM_OPTIONS[0])
3123:             opening.set(str(r[3] if r[3] is not None else 0))
3124:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
3125:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
3126:             err.set("")
3127:             edit_btn.configure(text="SAVE EDIT")
3128:             ce.focus_set()
3129:             return True
3130: 
3131:         def check_duplicates(*_):
3132:             c = code.get().strip()
3133:             d = desc.get().strip()
3134:             dest = destination.get()
3135:             msgs = []
3136:             r = row_for(dest, c) if len(norm(c)) == 8 else None
3137:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
3139:             dh = desc_hit(dest, d) if d else None
3140:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
3141:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
3142:             hint.set("\n".join(msgs))
3143: 
3144:         code.trace_add("write", check_duplicates)
3145:         desc.trace_add("write", check_duplicates)
3146: 
3147:         def save_code():
3148:             try:
3149:                 c = code.get().strip()
3150:                 d = desc.get().strip()
3151:                 u = uom.get().strip()
3152:                 dest = destination.get()
3153:                 digits = norm(c)
3154:                 if len(digits) != 8:
3155:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3156:                 if not d:
3157:                     raise ValueError("Description is required.")
3158:                 try:
3159:                     op = float(opening.get().strip() or 0)
```
```text
3180:                         (c, d, u, op, iso, old)
3181:                     )
3182:                     action = "updated"
3183:                 else:
3184:                     self.conn.execute(
3185:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3186:                         (c, d, u, "", op, 0, iso)
3187:                     )
3188:                     action = "saved"
3189:                 self.conn.commit()
3190:                 backup_database()
3191:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3192:                 # Keep popup open for fast multiple entries.
3193:                 clear_form(keep_search=False)
3194:                 ce.focus_set()
3195:             except Exception as ex:
3196:                 self.conn.rollback()
3197:                 err.set(str(ex))
3198:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3199: 
3200:         def edit_action():
```
```text
3196:                 self.conn.rollback()
3197:                 err.set(str(ex))
3198:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3199: 
3200:         def edit_action():
3201:             if not edit_mode["on"]:
3202:                 load_for_edit()
3203:             else:
3204:                 save_code()
3205: 
3206:         def delete_code():
3207:             if not edit_mode["on"]:
3208:                 if not load_for_edit():
3209:                     return
3210:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3211:                 return
3212:             try:
3213:                 t = table_for(edit_mode["dest"])
3214:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3215:                 self.conn.commit()
3216:                 backup_database()
```
```text
3212:             try:
3213:                 t = table_for(edit_mode["dest"])
3214:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3215:                 self.conn.commit()
3216:                 backup_database()
3217:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3218:                 clear_form(keep_search=False)
3219:             except Exception as ex:
3220:                 self.conn.rollback()
3221:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3222: 
3223:         btns = ttk.Frame(box)
3224:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3225:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3226:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3227:         edit_btn.pack(side="left", padx=4, ipadx=8)
3228:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3229:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3230:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3231:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3232:         ce.focus_set()
```
```text
3226:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3227:         edit_btn.pack(side="left", padx=4, ipadx=8)
3228:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3229:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3230:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3231:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3232:         ce.focus_set()
3233: 
3234:     def _mto_new_item_dialog(self, on_saved):
3235:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3236:         brand-new item can be created without leaving that screen. Writes
3237:         straight into the same Item Master (items table) used everywhere."""
3238:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3239:         win.transient(self); win.grab_set()
3240:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3241:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3242:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3243:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3244:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3245:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3246:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3242:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3243:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3244:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3245:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3246:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3247:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3248:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3249:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3250:         def save():
3251:             try:
3252:                 c=code.get().strip(); d=desc.get().strip()
3253:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3254:                 if not d: raise ValueError("Description is required.")
3255:                 try:
3256:                     opening_val=float(opening.get() or 0)
3257:                 except ValueError:
3258:                     raise ValueError("Opening Qty must be a number.")
3259:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3260:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3261:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3262:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3255:                 try:
3256:                     opening_val=float(opening.get() or 0)
3257:                 except ValueError:
3258:                     raise ValueError("Opening Qty must be a number.")
3259:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3260:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3261:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3262:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3263:                 self.conn.commit(); backup_database()
3264:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3265:                 win.grab_release(); win.destroy()
3266:                 on_saved()
3267:             except Exception as ex: messagebox.showerror("Error",str(ex))
3268:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3269:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3270:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3271: 
3272:     def _item_filter_bar(self, parent, on_change):
3273:         """Item Code entry + item-master picker + Search/Show All. Calls
3274:         on_change() whenever the code changes or a button is pressed."""
3275:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3361:         self._item_master_find_callback=None
3362:         self._portable_print_context=None
3363:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3364:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3365:         }
3366: 
3367:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3368:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3369:         self.conn.commit()
3370: 
3371:         # ---- Same professional in-app window layout as Inventory Codes ----
3372:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3373:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3374:                   foreground=COLORS["primary_dark"]).pack(side="left")
3375:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3376: 
3377:         def open_find():
3378:             state_find={"index":-1}
3379:             def search_fn(text):
3380:                 text=text.strip().lower()
3381:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3468:             for i in table.get_children(): table.delete(i)
3469:             where=["1=1"]; params=[]
3470:             prefix=state.get("prefix",""); q=search.get().strip()
3471:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3472:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3473:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3474:             if fc: where.append("code >= ?"); params.append(fc)
3475:             if tc: where.append("code <= ?"); params.append(tc)
3476:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3477:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3478:             records=[]
3479:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3480:                 # If a date filter is supplied, accept an opening-date match OR
3481:                 # a transaction in that date range. This prevents valid MTO codes
3482:                 # from disappearing merely because an older record has no opening_date.
3483:                 if df or dt:
3484:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3485:                     if not ok:
3486:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3487:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3488:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3558:                 tr.insert("", "end", values=r)
3559:         def clear():
3560:             for x in v.values(): x.set("")
3561:             try: tr.selection_remove(tr.selection())
3562:             except Exception: pass
3563:             self._set_form_editable(party_form_roots, False)
3564:         def new_form():
3565:             clear(); self._set_form_editable(party_form_roots, True)
3566:         def save():
3567:             try:
3568:                 name=v["name"].get().strip()
3569:                 if not name: raise ValueError("Party Name is required.")
3570:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3571:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3572:             except Exception as ex: messagebox.showerror("Error",str(ex))
3573:         def load_party_row(a):
3574:             if not a:return
3575:             r=tr.item(a[0])["values"]
3576:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3577:             self._set_form_editable(party_form_roots, False)
3578:         def on_party_select(_=None):
```
```text
3584:             load_party_row(a)
3585:             self._set_form_editable(party_form_roots, True)
3586:         def delete_party():
3587:             a=tr.selection()
3588:             if not a:
3589:                 messagebox.showwarning("Delete", "Select a party first."); return
3590:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3591:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3592:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3593:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3594:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3595:         self._add_transaction_new_button(new_form)
3596:         load(); clear()
3597: 
3598:     def user_management(self):
3599:         self.clearbody()
3600:         if not self.is_admin:
3601:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3602:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3603:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3604:         role=tk.StringVar(value="User")
```
```text
3641:             u_ent.state(["!disabled"])
3642:         def edit():
3643:             a=tr.selection()
3644:             if not a:
3645:                 messagebox.showwarning("Edit User","Select a user row first."); return
3646:             r=tr.item(a[0])["values"]
3647:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3648:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3649:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3650:         def save():
3651:             try:
3652:                 username=v["username"].get().strip()
3653:                 if not username: raise ValueError("Username is required.")
3654:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3655:                 pw=v["password"].get()
3656:                 if exists:
3657:                     pw_hash = hash_password(pw) if pw else exists[0]
3658:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3659:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3660:                 else:
3661:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3656:                 if exists:
3657:                     pw_hash = hash_password(pw) if pw else exists[0]
3658:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3659:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3660:                 else:
3661:                     if not pw: raise ValueError("Password is required for a new user.")
3662:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3663:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3664:                 self.conn.commit(); backup_database(); load(); clear()
3665:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3666:             except Exception as ex:
3667:                 messagebox.showerror("Error", str(ex))
3668:         def delete_user():
3669:             a=tr.selection()
3670:             if not a:
3671:                 messagebox.showwarning("Delete User","Select a user row first."); return
3672:             username=tr.item(a[0])["values"][0]
3673:             if username==self.current_user:
3674:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3675:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3676:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3671:                 messagebox.showwarning("Delete User","Select a user row first."); return
3672:             username=tr.item(a[0])["values"][0]
3673:             if username==self.current_user:
3674:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3675:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3676:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3677:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3678:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3679:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3680:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3681:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3682:         load()
3683: 
3684:     @staticmethod
3685:     def _renumber_tree(tree, rows):
3686:         for i,iid in enumerate(tree.get_children()):
3687:             vals=list(tree.item(iid,"values"));
3688:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3689: 
3690:     def demand(self):
3691:         self.clearbody(); self.demand_lines=[]
```
```text
3688:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3689: 
3690:     def demand(self):
3691:         self.clearbody(); self.demand_lines=[]
3692:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3693:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3694:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3695:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3696:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3697:         # Demand Date is intentionally displayed as its own dedicated field.
3698:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3699:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3700:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3701:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3702:                 ("special","Special Instructions"),("source","Recommended Source")]
3703:         for i,(k,n) in enumerate(fields):
3704:             r=i//4*2+3; c=i%4*2
3705:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3706:             if k=="dept":
3707:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3708:             elif k=="urgency":
```
```text
3778:         def new_form():
3779:             self._editing_document_key=None
3780:             for z in v.values(): z.set("")
3781:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3782:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3783:             for iid in tree.get_children(): tree.delete(iid)
3784:             self._set_form_editable(form_roots, True, skip=[selector])
3785: 
3786:         def save():
3787:             try:
3788:                 no=v["no"].get().strip()
3789:                 if not no: raise ValueError("Demand No is required.")
3790:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3791:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3792:                 if dup and getattr(self,"_editing_document_key",None) != no:
3793:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3794:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3795:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3796:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3797:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3798:                 self.conn.commit()
```
```text
3791:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3792:                 if dup and getattr(self,"_editing_document_key",None) != no:
3793:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3794:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3795:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3796:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3797:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3798:                 self.conn.commit()
3799:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3800:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3801:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3802:             except Exception as ex: messagebox.showerror("Error",str(ex))
3803:         form_roots=[f,line,editbar]
3804:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3805:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3806:         def delete_current():
3807:             no=v["no"].get().strip()
3808:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3809:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3810:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3811:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3824:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3825:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3826:                     f"Justification: {v['just'].get()}",
3827:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3828:             if not self.demand_lines:
3829:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3830:             self.show_preview_window("Purchase Demand", header,
3831:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3832:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3833:         def edit_saved_demand():
3834:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3835:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3836:             self._set_form_editable(form_roots, True, skip=[selector])
3837:         def print_now():
3838:             if not self.demand_lines:
3839:                 messagebox.showwarning("Print","Add at least one item line first."); return
3840:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3841:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3842:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3843:                     f"Justification: {v['just'].get()}",
3844:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3840:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3841:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3842:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3843:                     f"Justification: {v['just'].get()}",
3844:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3845:             self._open_direct_printer("Purchase Demand",header,
3846:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3847:                 self.demand_lines,A4)
3848:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3849:         self._add_transaction_new_button(new_form)
3850:         self._set_form_editable(form_roots, False, skip=[selector])
3851:         try:
3852:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3853:         except Exception: pass
3854:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3855: 
3856:     def load_demand_into_form(self,no,v,tree):
3857:         v["no"].set(no)
3858:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3859:         if not r:return
3860:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3862:         self.demand_lines=[]
3863:         for i in tree.get_children():tree.delete(i)
3864:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3865:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3866:         roots=getattr(self,"_transaction_form_roots",None)
3867:         if roots and "demand" in roots:
3868:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3869: 
3870:     def refresh_saved_cache(self,typ):
3871:         # Refresh saved-document dropdowns immediately after a successful save.
3872:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3873:         alive=[]
3874:         for combo, refresh in refreshers:
3875:             try:
3876:                 if combo.winfo_exists():
3877:                     refresh()
3878:                     alive.append((combo, refresh))
3879:             except Exception:
3880:                 pass
3881:         if hasattr(self, "_document_selector_refreshers"):
3882:             self._document_selector_refreshers[typ] = alive
```
```text
3881:         if hasattr(self, "_document_selector_refreshers"):
3882:             self._document_selector_refreshers[typ] = alive
3883: 
3884:     def grr(self):
3885:         self.clearbody(); self.grr_lines=[]
3886:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3887:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3888:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3889:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3890:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3891:         for i,(k,n) in enumerate(fields):
3892:             r=i//4*2+2;c=i%4*2
3893:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3894:             if k=="department":
3895:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3896:             elif k=="supplier":
3897:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3898:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3899:             elif k=="date":
3900:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3901:             else:
```
```text
3950:         def new_form():
3951:             self._editing_document_key=None
3952:             for z in v.values(): z.set("")
3953:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3954:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3955:             for iid in tree.get_children(): tree.delete(iid)
3956:             self._set_form_editable(form_roots, True, skip=[selector])
3957: 
3958:         def save():
3959:             try:
3960:                 no=v["no"].get().strip()
3961:                 if not no:raise ValueError("GRN No is required.")
3962:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3963:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3964:                 if dup and getattr(self,"_editing_document_key",None) != no:
3965:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3966:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3967:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3968:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3969:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3970:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3967:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3968:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3969:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3970:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3971:                 for x in self.grr_lines:
3972:                     ltype=x[10] if len(x)>10 else "Local"
3973:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3974:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3975:                 self.conn.commit()
3976:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
3977:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
3978:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3979:             except Exception as ex:messagebox.showerror("Error",str(ex))
3980:         form_roots=[f,line,editbar]
3981:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3982:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3983:         def delete_current():
3984:             no=v["no"].get().strip()
3985:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3986:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3987:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
3980:         form_roots=[f,line,editbar]
3981:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3982:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3983:         def delete_current():
3984:             no=v["no"].get().strip()
3985:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3986:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3987:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3988:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3989:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3990:         def cancel_form():
3991:             self._editing_document_key=None
3992:             self._set_form_editable(form_roots, False, skip=[selector])
3993:             for z in v.values(): z.set("")
3994:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3995:             itype.set("Local")
3996:             self.grr_lines.clear()
3997:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3998:             for iid in tree.get_children(): tree.delete(iid)
3999:         def preview_now():
4000:             if not self.grr_lines:
```
```text
4009:                     ("Challan #", v['challan'].get()),
4010:                     ("Vehicle #", v['vehicle'].get()),
4011:                     ("Bill/Voucher #", v['bill'].get()),
4012:                     ("Reference", v['ref'].get()),
4013:                     ("Remarks", v['remarks'].get()),
4014:                     ("Total Value", fmt_num(total))]
4015:             self.show_preview_window("GRN Receipt", header,
4016:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
4017:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
4018:         def portable_current():
4019:             total=sum(float(x[8] or 0) for x in self.grr_lines)
4020:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
4021:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
4022:         self._portable_print_context=portable_current
4023:         def edit_saved_grr():
4024:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4025:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
4026:             self._set_form_editable(form_roots, True, skip=[selector])
4027:         def print_now():
4028:             if not self.grr_lines:
4029:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
4033:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
4034:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
4035:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
4036:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
4037:                     ("Total Value", fmt_num(total))]
4038:             self._open_direct_printer("GRN Receipt",header,
4039:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
4040:                 self.grr_lines,landscape(A4))
4041:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
4042:         self._add_transaction_new_button(new_form)
4043:         self._set_form_editable(form_roots, False, skip=[selector])
4044:         try:
4045:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
4046:         except Exception: pass
4047:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
4048: 
4049:     def load_grr_into_form(self,no,v,tree):
4050:         v["no"].set(no)
4051:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
4052:         if not r:return
4053:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
4060:         if roots and "grr" in roots:
4061:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
4062: 
4063:     def issue(self):
4064:         self.clearbody(); self.issue_lines=[]
4065:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
4066:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
4067:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
4068:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
4069:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
4070:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
4071:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
4072:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
4073:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
4074:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
4075:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
4076:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
4077:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
4078:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
4079:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
4080:         itype=tk.StringVar(value="Local")
```
```text
4149:                 # Editing an existing issue replaces its old stock transaction and detail lines.
4150:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
4151:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
4152:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
4153:                 for x in self.issue_lines:
4154:                     ltype=x[7] if len(x)>7 else "Local"
4155:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
4156:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
4157:                 self.conn.commit()
4158:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
4159:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
4160:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4161:             except Exception as ex:messagebox.showerror("Error",str(ex))
4162:         def delete_current():
4163:             no=v["no"].get().strip()
4164:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
4165:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
4166:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
4167:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
4168:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
4169:         def cancel_form():
```
```text
4177:             for iid in tree.get_children(): tree.delete(iid)
4178:         def preview_now():
4179:             if not self.issue_lines:
4180:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4181:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4182:                     f"Items Use For: {v['items_use_for'].get()}"]
4183:             self.show_preview_window("Material Issue", header,
4184:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4185:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4186:         def portable_current():
4187:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4188:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4189:         self._portable_print_context=portable_current
4190:         form_roots=[f,usebar,line,editbar]
4191:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4192:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4193:         def load_saved_issue(no):
4194:             self.load_issue_into_form(no,v,tree)
4195:             self._set_form_editable(form_roots, False, skip=[selector])
4196:         def edit_saved_issue():
4197:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4190:         form_roots=[f,usebar,line,editbar]
4191:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4192:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4193:         def load_saved_issue(no):
4194:             self.load_issue_into_form(no,v,tree)
4195:             self._set_form_editable(form_roots, False, skip=[selector])
4196:         def edit_saved_issue():
4197:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4198:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4199:             self._set_form_editable(form_roots, True, skip=[selector])
4200:         def print_issue_now():
4201:             if not self.issue_lines:
4202:                 messagebox.showwarning("Print","Add at least one item line first."); return
4203:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4204:             self._open_direct_printer("Material Issue",header,
4205:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4206:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4207:         self._add_transaction_new_button(new_form)
4208:         self._set_form_editable(form_roots, False, skip=[selector])
4209:         self._active_form_loader = load_saved_issue
4210: 
```
```text
4218:         for i in tree.get_children():tree.delete(i)
4219:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4220:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4221:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4222:         roots=getattr(self,"_transaction_form_roots",None)
4223:         if roots and "issue" in roots:
4224:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4225: 
4226:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4227:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4228: 
4229:         The layout intentionally matches Inventory Codes' Selection Criteria
4230:         popup so all Report sub-sections have one consistent desktop workflow.
4231:         """
4232:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4233:         win=tk.Toplevel(self)
4234:         win.title(f"{report_title} - Selection Criteria")
4235:         win.resizable(False,False)
4236:         win.transient(self); win.grab_set()
4237:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4238:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4283:             except Exception: pass
4284:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4285:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4286:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4287:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4288:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4289:         e1.focus_set(); self.wait_window(win); return result
4290: 
4291:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4292:         self._pending_report_filters=criteria
4293:         try:
4294:             return self.open_menu_window(method,title,geometry)
4295:         finally:
4296:             self._pending_report_filters=None
4297: 
4298:     def open_stock_balance_report_flow(self):
4299:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4300:         if f.get("cancelled"): return None
4301:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4302: 
4303:     def open_grr_report_flow(self):
```
```text
4296:             self._pending_report_filters=None
4297: 
4298:     def open_stock_balance_report_flow(self):
4299:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4300:         if f.get("cancelled"): return None
4301:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4302: 
4303:     def open_grr_report_flow(self):
4304:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4305:         if f.get("cancelled"): return None
4306:         return self._open_report_child(self.report_grr,"GRN Report",f)
4307: 
4308:     def open_demand_report_flow(self):
4309:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4310:         if f.get("cancelled"): return None
4311:         return self._open_report_child(self.report_demand,"Demand Report",f)
4312: 
4313:     def open_issue_report_flow(self):
4314:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4315:         if f.get("cancelled"): return None
4316:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4310:         if f.get("cancelled"): return None
4311:         return self._open_report_child(self.report_demand,"Demand Report",f)
4312: 
4313:     def open_issue_report_flow(self):
4314:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4315:         if f.get("cancelled"): return None
4316:         return self._open_report_child(self.report_issue,"Issue Report",f)
4317: 
4318:     def open_party_report_flow(self):
4319:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4320:         if f.get("cancelled"): return None
4321:         return self._open_report_child(self.report_party,"Party Report",f)
4322: 
4323:     def _ask_stock_balance_filters(self):
4324:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4325:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4326:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4327:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4328:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4329:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4330:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4342:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4343:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4344:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4345:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4346:         e1.focus_set();self.wait_window(win);return result
4347: 
4348:     def stock_balance(self):
4349:         self.clearbody()
4350:         # Stock Balance is a Report sub-section and does not use the generic
4351:         # Save/Edit/Delete/Cancel/Print action strip.
4352:         children=self.body.winfo_children()
4353:         if children:
4354:             children[0].destroy()
4355:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4356:         if initial.get("cancelled"):
4357:             self.dashboard(); return
4358:         top=ttk.Frame(self.body);top.pack(fill="x")
4359:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4360:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4361:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4362:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4372:             for typ,qty in self.conn.execute(q,params):
4373:                 if typ=="GRR":gr+=float(qty or 0)
4374:                 elif typ=="ISSUE":iss+=float(qty or 0)
4375:             return opening_before,gr,iss,opening_before+gr-iss
4376:         def header_summary():
4377:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4378:         def load():
4379:             for i in tr.get_children():tr.delete(i)
4380:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4381:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4382:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4383:             sql+=" ORDER BY code"
4384:             for r in self.conn.execute(sql,params):
4385:                 op,gr,iss,cur=period(r[0],r[3])
4386:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4387:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4388:         def reopen_filters():
4389:             initial2=self._ask_stock_balance_filters()
4390:             if initial2.get("cancelled"):return
4391:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4392:             load()
```
```text
4430:         """
4431:         if typ=="demand": self.demand()
4432:         elif typ=="grr": self.grr()
4433:         else: self.issue()
4434:         loader=getattr(self,"_active_form_loader",None)
4435:         if loader: loader(str(no))
4436: 
4437:     def _edit_from_selector(self, typ, var, loader):
4438:         """Top Edit action: load the saved document directly into the current form.
4439:         If nothing is selected, use the newest saved document; never open a popup.
4440:         """
4441:         text=var.get().strip()
4442:         if text:
4443:             no=text.split(" -> ",1)[0].strip()
4444:         else:
4445:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4446:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4447:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4448:             if not r:
4449:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4450:                 return
```
```text
4447:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4448:             if not r:
4449:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4450:                 return
4451:             no=str(r[0])
4452:             var.set(no)
4453:         loader(no)
4454: 
4455:     def show_saved_records(self,typ):
4456:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4457:         if typ=="demand":
4458:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4459:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4460:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4461:             for r in rows:
4462:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4463:                 r=list(r); r[1]=to_display_date(r[1])
4464:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4465:         elif typ=="grr":
4466:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4467:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4478:         def view():
4479:             a=tr.selection()
4480:             if not a:return
4481:             no=tr.item(a[0])["values"][0]
4482:             win.destroy();self.open_document_editor(typ,no)
4483:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4484:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4485:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4486:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4487: 
4488:     def documents(self):
4489:         self.clearbody()
4490:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4491:         specs=[
4492:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4493:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4494:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4495:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4496:             ("Material Issues","issue",("No","Date","Department"),
4497:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4498:         ]
```
```text
4494:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4495:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4496:             ("Material Issues","issue",("No","Date","Department"),
4497:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4498:         ]
4499:         for title,typ,cols,query in specs:
4500:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4501:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4502:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4503:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4504:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4505:             for r in self.conn.execute(query):
4506:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4507:             def edit_selected(t=tr,k=typ):
4508:                 a=t.selection()
4509:                 if not a:
4510:                     messagebox.showwarning("Edit", "Select a saved record first.")
4511:                     return
4512:                 no=t.item(a[0])["values"][0]
4513:                 self.open_document_editor(k,no)
4514:             def delete_selected(t=tr,k=typ):
```
```text
4509:                 if not a:
4510:                     messagebox.showwarning("Edit", "Select a saved record first.")
4511:                     return
4512:                 no=t.item(a[0])["values"][0]
4513:                 self.open_document_editor(k,no)
4514:             def delete_selected(t=tr,k=typ):
4515:                 a=t.selection()
4516:                 if not a:
4517:                     messagebox.showwarning("Delete", "Select a saved record first.")
4518:                     return
4519:                 no=t.item(a[0])["values"][0]
4520:                 if k=="demand":
4521:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4522:                 elif k=="grr":
4523:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4524:                 else:
4525:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4526:                 self.conn.commit();backup_database();self.documents()
4527:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4528:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4529:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4523:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4524:                 else:
4525:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4526:                 self.conn.commit();backup_database();self.documents()
4527:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4528:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4529:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4530:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4531:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4532:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4533:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4534: 
4535:     def doc_export_selected(self,typ,tr,fmt):
4536:         a=tr.selection()
4537:         if not a:
4538:             messagebox.showwarning("Export","Select a saved record first."); return
4539:         no=tr.item(a[0])["values"][0]
4540:         if fmt=="word": self.export_word(typ,no)
4541:         else: self.export_excel(typ,no)
4542: 
4543:     def doc_preview_selected(self,typ,tr):
```
```text
4538:             messagebox.showwarning("Export","Select a saved record first."); return
4539:         no=tr.item(a[0])["values"][0]
4540:         if fmt=="word": self.export_word(typ,no)
4541:         else: self.export_excel(typ,no)
4542: 
4543:     def doc_preview_selected(self,typ,tr):
4544:         a=tr.selection()
4545:         if not a:
4546:             messagebox.showwarning("Preview","Select a saved record first."); return
4547:         no=tr.item(a[0])["values"][0]
4548:         data=self._get_doc_data(typ,no)
4549:         if not data:
4550:             messagebox.showwarning("Preview","Document not found."); return
4551:         title,header,cols,rows=data
4552:         header_lines=header
4553:         self.show_preview_window(title,header_lines,cols,rows)
4554: 
4555:     def doc_print_selected(self,typ,tr):
4556:         a=tr.selection()
4557:         if not a: return
4558:         no=tr.item(a[0])["values"][0]
```
```text
4589:         def _print_loaded_document():
4590:             data=self._get_doc_data(typ,no)
4591:             if not data:
4592:                 messagebox.showwarning("Document","Document not found."); return
4593:             title,header,cols,rows=data
4594:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4595:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4596: 
4597:     def _report_filter_popup(self, title, include_party=False):
4598:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4599:         win,winbody=self._internal_window(title,"520x420")
4600:         done=tk.BooleanVar(value=False)
4601:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4602:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4603:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4604:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4605:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4606:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4607:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4608:         if include_party:
4609:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4603:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4604:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4605:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4606:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4607:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4608:         if include_party:
4609:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4610:         def ok():
4611:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4612:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4613:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4614:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4615: 
4616:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4617:         self.clearbody()
4618:         # Report sub-sections use their own report toolbar; remove only the
4619:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4620:         children=self.body.winfo_children()
4621:         if children:
4622:             children[0].destroy()
4623:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4624:         if f.get("cancelled"):
4625:             self.dashboard();return
4626:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4627:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4628:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4629:         def load():
4630:             for i in tr.get_children():tr.delete(i)
4631:             params,where=params_builder(f)
4632:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4633:             for r in self.conn.execute(sql,params):
4634:                 vals=list(r)
4635:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4636:                 tr.insert("","end",values=vals)
4637:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4638:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4639:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4640:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4641:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4642:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4643:         def open_find_report():
4644:             state_find={"index":-1}
```
```text
4650:                 order=children[start:]+children[:start]
4651:                 for iid in order:
4652:                     vals=tr.item(iid,"values")
4653:                     if any(text in str(v).lower() for v in vals):
4654:                         state_find["index"]=children.index(iid)
4655:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4656:                 return False
4657:             self._open_exact_find_text_popup(search_fn)
4658:         self._item_master_find_callback=open_find_report
4659:         load()
4660:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4661: 
4662:     def report_grr(self):
4663:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4664:         def pb(f):
4665:             w=[];p=[]
4666:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4667:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4668:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4669:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4670:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4665:             w=[];p=[]
4666:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4667:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4668:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4669:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4670:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4671:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4672:             return p,w
4673:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4674: 
4675:     def report_demand(self):
4676:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4677:         def pb(f):
4678:             w=[];p=[]
4679:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4680:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4681:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4682:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4683:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4684:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4685:             return p,w
```
```text
4678:             w=[];p=[]
4679:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4680:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4681:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4682:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4683:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4684:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4685:             return p,w
4686:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4687: 
4688:     def report_issue(self):
4689:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4690:         def pb(f):
4691:             w=[];p=[]
4692:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4693:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4694:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4695:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4696:             return p,w
4697:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4698: 
```
```text
4691:             w=[];p=[]
4692:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4693:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4694:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4695:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4696:             return p,w
4697:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4698: 
4699:     def report_party(self):
4700:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4701:         def pb(f):
4702:             w=[];p=[]
4703:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4704:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4705:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4706:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4707:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4708:             return p,w
4709:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4710: 
4711:     def reports(self):
```
```text
4709:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4710: 
4711:     def reports(self):
4712:         self.clearbody()
4713:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4714: 
4715:         # ================= GRN Details =================
4716:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4717:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4718:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4719:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4720:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4721:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4722: 
4723:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4724:         def load_grr_item(codev=None):
4725:             for i in tr.get_children(): tr.delete(i)
4726:             q=codev.get().strip() if codev else ""
4727:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4728:             for r in self.conn.execute(sql,(q,) if q else ()):
4729:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4735:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4736:         tr=self.make_tree(fr,grr_cols,grr_widths)
4737:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4738:             for i in tr.get_children(): tr.delete(i)
4739:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4740:             conds=[];params=[]
4741:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4742:             if td: conds.append("g.grr_date<=?");params.append(td)
4743:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4744:             for r in self.conn.execute(sql,params):
4745:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4746:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4747:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4748:         load_grr_date(fdv,tdv)
4749: 
4750:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4751:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4752:         party=tk.StringVar(value="ALL")
4753:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4754:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4755:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4751:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4752:         party=tk.StringVar(value="ALL")
4753:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4754:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4755:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4756:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4757:         def load_party(*_):
4758:             for i in tr.get_children(): tr.delete(i)
4759:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4760:             if party.get()=="ALL":
4761:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4762:             else:
4763:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4764:             for r in rows:
4765:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4766:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4767:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4768: 
4769:         # ================= Demand Details =================
4770:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4771:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4767:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4768: 
4769:         # ================= Demand Details =================
4770:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4771:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4772:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4773:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4774:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4775:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4776: 
4777:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4778:         def load_dem_item(codev=None):
4779:             for i in tr.get_children(): tr.delete(i)
4780:             q=codev.get().strip() if codev else ""
4781:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4782:             for r in self.conn.execute(sql,(q,) if q else ()):
4783:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4784:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4785:         tr=self.make_tree(fr,dem_cols,dem_widths)
4786:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4787:         load_dem_item(codev)
```
```text
4789:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4790:         tr=self.make_tree(fr,dem_cols,dem_widths)
4791:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4792:             for i in tr.get_children(): tr.delete(i)
4793:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4794:             conds=[];params=[]
4795:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4796:             if td: conds.append("d.demand_date<=?");params.append(td)
4797:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4798:             for r in self.conn.execute(sql,params):
4799:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4800:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4801:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4802:         load_dem_date(fdv,tdv)
4803: 
4804:         # ================= Material Issue Details =================
4805:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4806:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4807:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4808:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4809:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4802:         load_dem_date(fdv,tdv)
4803: 
4804:         # ================= Material Issue Details =================
4805:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4806:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4807:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4808:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4809:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4810:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4811: 
4812:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4813:         def load_iss_item(codev=None):
4814:             for i in tr.get_children(): tr.delete(i)
4815:             q=codev.get().strip() if codev else ""
4816:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4817:             for r in self.conn.execute(sql,(q,) if q else ()):
4818:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4819:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4820:         tr=self.make_tree(fr,iss_cols,iss_widths)
4821:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4822:         load_iss_item(codev)
```
```text
4824:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4825:         tr=self.make_tree(fr,iss_cols,iss_widths)
4826:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4827:             for i in tr.get_children(): tr.delete(i)
4828:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4829:             conds=[];params=[]
4830:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4831:             if td: conds.append("i.issue_date<=?");params.append(td)
4832:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4833:             for r in self.conn.execute(sql,params):
4834:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4835:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4836:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4837:         load_iss_date(fdv,tdv)
4838: 
4839:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4840: 
4841:     def print_item_master(self):
4842:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4843:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4844: 
```
```text
4841:     def print_item_master(self):
4842:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4843:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4844: 
4845:     def print_party_master(self):
4846:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4847:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4848: 
4849:     def print_report(self,kind):
4850:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4851:         if kind=="grr":
4852:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4853:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4854:         elif kind=="demand":
4855:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4856:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4857:         elif kind=="issue":
4858:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4859:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4860:         else:
4861:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4862:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4863:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4864: 
4865:     def print_stock(self):
4866:         rows=[]
4867:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4868:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4869:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4870:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4871: 
4872:     def print_ledger(self):
4873:         rows=[]
4874:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4875:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4876:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4877:                 running += x[3] if x[1]=="GRR" else -x[3]
4878:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4879:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4880: 
4881:     def _get_doc_data(self, typ, no):
4882:         """Header + line items for one saved document, used by the on-screen
```
```text
4948:             sig=doc.add_table(rows=2,cols=3)
4949:             labels=["Prepared By","Store Keeper","Store Incharge"]
4950:             for i,label in enumerate(labels):
4951:                 sig.cell(0,i).text="____________________"
4952:                 sig.cell(1,i).text=label
4953:                 for para in sig.cell(1,i).paragraphs:
4954:                     for run in para.runs: run.bold=True
4955:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4956:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4957:         doc.save(path)
4958:         self.open_file(path)
4959: 
4960:     def export_excel(self, typ, no):
4961:         if not no or not no.strip():
4962:             return messagebox.showwarning("Excel Export","Select a document first.")
4963:         if not XLSX_AVAILABLE:
4964:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4965:         data=self._get_doc_data(typ,no)
4966:         if not data:
4967:             return messagebox.showwarning("Excel Export","Document not found.")
4968:         title,header,cols,rows=data
```
```text
4990:             for col in range(1,4):
4991:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4992:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4993:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4994:         for col_cells in ws.columns:
4995:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4996:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4997:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4998:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4999:         wb.save(path)
5000:         self.open_file(path)
5001: 
5002:     def preview_pdf(self,typ,no):
5003:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
5004:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
5005:         data=self._get_doc_data(typ,no)
5006:         if not data:return messagebox.showwarning("Document","Document not found.")
5007:         title,header,cols,rows=data
5008:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
5009:         page_size = landscape(A4) if typ == "grr" else A4
5010:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
5005:         data=self._get_doc_data(typ,no)
5006:         if not data:return messagebox.showwarning("Document","Document not found.")
5007:         title,header,cols,rows=data
5008:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
5009:         page_size = landscape(A4) if typ == "grr" else A4
5010:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
5011: 
5012:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
5013:         """Open the print dialog with a real visual preview of the exact report.
5014: 
5015:         The report is rendered to a temporary PDF only in memory/on disk for the
5016:         duration of printing.  It is deleted after the print dialog closes, so
5017:         the Print button does not leave a PDF report behind.  Printing uses the
5018:         rendered report page itself rather than rebuilding rows as plain text;
5019:         this keeps the printed page identical to the application's report.
5020:         """
5021:         # Printing is always prepared as an A4 landscape page. This only affects
5022:         # the print path; the rest of the application's UI/report logic is unchanged.
5023:         page_size = landscape(A4)
5024:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
5025:             messagebox.showwarning(
```
```text
5027:                 "The print preview/printing components are not available.\n\n"
5028:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
5029:             )
5030:             return
5031:         if not rows and not columns:
5032:             messagebox.showwarning("Print", "There is no data to print.")
5033:             return
5034:         try:
5035:             os.makedirs(REPORTS_DIR, exist_ok=True)
5036:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
5037:             self._pdf_table_report(key,title,columns,rows,page_size,
5038:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
5039:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
5040:             self._select_windows_printer_for_pdf(key)
5041:         except Exception as e:
5042:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
5043: 
5044:     def _select_windows_printer_for_pdf(self, path):
5045:         """Print dialog with an actual page preview, printer selection and direct GDI output.
5046: 
5047:         The preview is rendered from the exact PDF produced by the application,
```
```text
5077:         job=getattr(self, "_print_jobs", {}).get(path)
5078:         if job:
5079:             title, header_lines, columns, rows, source_page_size = job
5080:         else:
5081:             title=os.path.splitext(os.path.basename(path))[0]
5082:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
5083: 
5084:         try:
5085:             doc=fitz.open(path)
5086:             total_pages=max(1,doc.page_count)
5087:         except Exception as e:
5088:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
5089:             return
5090: 
5091:         win=tk.Toplevel(self)
5092:         win.title("Printing from Win32 application - Print")
5093:         win.geometry("900x620")
5094:         win.minsize(850,580)
5095:         win.transient(self)
5096:         win.configure(bg="#f0f0f0")
5097: 
```
```text
5103:             pass
5104: 
5105:         outer=tk.Frame(win,bg="#f0f0f0")
5106:         outer.pack(fill="both",expand=True)
5107:         outer.columnconfigure(1,weight=1)
5108:         outer.rowconfigure(0,weight=1)
5109: 
5110:         # Left side mirrors the familiar system printer dialog: printers and
5111:         # print options. Right side contains the actual report page preview.
5112:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
5113:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
5114:         left.grid_propagate(False)
5115:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
5116:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
5117:         printer_list.pack(fill="x")
5118:         for pr in printers: printer_list.insert("end",pr)
5119:         try: printer_list.selection_set(printers.index(default_printer))
5120:         except Exception: printer_list.selection_set(0)
5121: 
5122:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
5123:         copies=tk.IntVar(value=1)
```
```text
5196:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5197: 
5198:         bottom=tk.Frame(win,bg="#f0f0f0")
5199:         # `outer` already uses pack() in `win`; using grid() for another direct
5200:         # child of the same toplevel raises TclError. Keep the action bar in the
5201:         # same geometry-manager family so Print/Cancel are always visible.
5202:         bottom.pack(fill="x",padx=12,pady=(0,12))
5203:         bottom.columnconfigure(0,weight=1)
5204:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5205:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5206:         print_btn=ttk.Button(bottom,text="Print",width=12)
5207:         print_btn.grid(row=0,column=2,padx=(8,0))
5208: 
5209:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5210: 
5211:         def parse_page_selection(total):
5212:             if pages_mode.get()=="All pages": return list(range(total))
5213:             raw=page_range.get().strip()
5214:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5215:             selected=[]
5216:             for part in raw.split(","):
```
```text
5213:             raw=page_range.get().strip()
5214:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5215:             selected=[]
5216:             for part in raw.split(","):
5217:                 part=part.strip()
5218:                 if "-" in part:
5219:                     a,b=part.split("-",1); a=int(a); b=int(b)
5220:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5221:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5222:                     selected.extend(range(a-1,b))
5223:                 else:
5224:                     n=int(part)
5225:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5226:                     selected.append(n-1)
5227:             return list(dict.fromkeys(selected))
5228: 
5229:         def selected_printer():
5230:             sel=printer_list.curselection()
5231:             return printer_list.get(sel[0]) if sel else printers[0]
5232: 
5233:         def print_rendered_pages():
```
```text
5326:                 finally:
5327:                     if hprinter is not None:
5328:                         try: win32print.ClosePrinter(hprinter)
5329:                         except Exception: pass
5330:                     if hdc:
5331:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5332:                         except Exception: pass
5333: 
5334:                 # Print the exact rendered PDF page through the printer DC.
5335:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5336:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5337:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5338:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5339: 
5340:                 for copy_no in range(count):
5341:                     dc.StartDoc(str(title)[:80])
5342:                     doc_ok=False
5343:                     try:
5344:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5345:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5346:                             dc.StartPage()
```
```text
5345:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5346:                             dc.StartPage()
5347:                             page_ok=False
5348:                             try:
5349:                                 cell_w=printable_w/float(cols_n)
5350:                                 cell_h=printable_h/float(rows_n)
5351:                                 for j,page_index in enumerate(batch):
5352:                                     page=doc.load_page(page_index)
5353:                                     pdf_w=max(1.0,float(page.rect.width))
5354:                                     pdf_h=max(1.0,float(page.rect.height))
5355:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5356:                                     fit=max(0.25,min(fit,8.0))
5357:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5358:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5359:                                     target_w=max(1,int(cell_w*0.96))
5360:                                     target_h=max(1,int(cell_h*0.96))
5361:                                     ratio=min(target_w/img.width,target_h/img.height)
5362:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5363:                                     if (nw,nh)!=(img.width,img.height):
5364:                                         img=img.resize((nw,nh),Image.LANCZOS)
5365:                                     dib=ImageWin.Dib(img)
```
```text
5385: 
5386:                 status.set("Print job sent successfully")
5387:                 win.update_idletasks()
5388:                 win.after(500,close)
5389:             except Exception as e:
5390:                 status.set("Print failed: "+str(e))
5391:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5392: 
5393:         def close():
5394:             try: doc.close()
5395:             except Exception: pass
5396:             try: win.destroy()
5397:             except Exception: pass
5398:             # Only the temporary PDF created by the Print button is removed.
5399:             # Existing report PDFs passed through the legacy print path are preserved.
5400:             try:
5401:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5402:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5403:             except Exception: pass
5404: 
5405:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5401:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5402:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5403:             except Exception: pass
5404: 
5405:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5406:         bottom.winfo_children()[1].configure(command=close)
5407:         print_btn.configure(command=print_rendered_pages)
5408:         win.protocol("WM_DELETE_WINDOW",close)
5409:         win.bind("<Escape>",lambda e:close())
5410:         win.grab_set()
5411:         # Keep the requested printer defaults visibly selected; no manual
5412:         # adjustment is required before pressing Print.
5413:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5414:         win.after(120,lambda:render_preview(0))
5415:         win.focus_force()
5416: 
5417:     def print_pdf(self,path):
5418:         """Open a printer-selection window for a generated PDF."""
5419:         path=os.path.abspath(path)
5420:         if not os.path.exists(path):
5421:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5417:     def print_pdf(self,path):
5418:         """Open a printer-selection window for a generated PDF."""
5419:         path=os.path.abspath(path)
5420:         if not os.path.exists(path):
5421:             messagebox.showwarning("Print", "The report file could not be found.")
5422:             return
5423: 
5424:         if sys.platform.startswith("win"):
5425:             self._select_windows_printer_for_pdf(path)
5426:             return
5427: 
5428:         try:
5429:             subprocess.run(["lp", path], check=True)
5430:         except Exception as e:
5431:             messagebox.showwarning(
5432:                 "Print",
5433:                 "The operating system could not start printing.\n\n"
5434:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5435:             )
5436: 
5437:     def open_file(self,path):
```
```text
5432:                 "Print",
5433:                 "The operating system could not start printing.\n\n"
5434:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5435:             )
5436: 
5437:     def open_file(self,path):
5438:         try:
5439:             if sys.platform.startswith("win"): os.startfile(path)
5440:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5441:             else: subprocess.Popen(["xdg-open",path])
5442:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5443: 
5444:     def print_demand(self,no):
5445:         data=self._get_doc_data("demand",no)
5446:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5447:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5448:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5449:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5450: 
5451:     def print_grr(self,no):
5452:         data=self._get_doc_data("grr",no)
```
```text
5446:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5447:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5448:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5449:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5450: 
5451:     def print_grr(self,no):
5452:         data=self._get_doc_data("grr",no)
5453:         if not data:return messagebox.showwarning("Document","GRN not found.")
5454:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5455:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5456:         # GRN has a wide item table. Generate the PDF itself in landscape so
5457:         # the printer dialog and printer driver receive a landscape document
5458:         # instead of a portrait page with rotated/cropped content.
5459:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5460: 
5461:     def print_issue(self,no):
5462:         data=self._get_doc_data("issue",no)
5463:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5464:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5465:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5466:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
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
