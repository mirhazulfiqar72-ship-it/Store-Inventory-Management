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

- Lines: 5445
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-436), restore_database(437-454), stock(456-461), fmt_num(463-465), to_iso_date(467-476), to_display_date(478-486), fiscal_year_key(488-499), fiscal_year_range(501-504), normalize_code(506-514), format_code(516-525), attach_code_mask(527-553), set_digits(530-535), key(536-546), paste(548-551), bind_add_to_list(555-576), on_enter(558-569), __init__(580-597), _check_for_updates(599-604), _setup_style(606-642), _shade(645-650), on_close(652-657), redo_network_setup(659-675), backup_now(677-684), restore_backup(686-704), _ctrl_f(706-718), _open_exact_find_text_popup(720-765), do_find(741-750), close(751-758), _global_enter(767-779), wipe(781-782), login(784-813), do_login(799-810), change_password(815-865), save_password(837-859), logout(867-872), home(874-900), _restore_dashboard_after_internal_close(902-916), _ensure_mdi_host(918-939), _internal_window(941-1033), normal_place(957-963), restore(964-971), maximize(972-978), minimize(979-1000), close(1001-1026), open_inventory_codes_detail_flow(1035-1053), open_inventory_codes_with_filters(1055-1069), open_inventory_codes_report_window(1071-1297), tbtn(1089-1094), balance_as_of(1151-1161), build_nav(1163-1185), selected_prefix(1187-1196), load(1198-1230), page_move(1232-1233), page_first(1234-1234), page_last(1235-1239), on_nav(1243-1244), find_popup(1247-1266), search_fn(1249-1264), print_report(1269-1272), export_pdf(1274-1276), export_word(1277-1279), export_excel(1280-1282), open_menu_window(1299-1321), close_window(1309-1316), _manual_check_update(1323-1327), _show_current_version(1329-1333), build_menu_bar(1335-1382), open_calendar_picker(1384-1432), pick(1402-1404), redraw(1406-1418), nav(1420-1424), make_date_field(1434-1441), clearbody(1443-1469), run_action(1458-1463), _portable_print_current(1471-1482), portable_print_dialog(1484-1557), build_receipt(1511-1529), send(1530-1543), refresh_printers(1544-1550), preview_tree(1559-1571), set_page_actions(1573-1581), _add_transaction_new_button(1583-1600), _report_header(1602-1666), _report_footer(1668-1675), _grr_signature_block(1677-1693), _finish_page(1695-1696), _wrap_text_to_width(1698-1723), fits(1705-1705), _pdf_table_report(1725-1794), table_header(1747-1752), show_preview_window(1796-1869), _safe_report_name(1871-1874), print_preview_window(1876-1879), _fallback_pdf_export(1881-1914), esc(1885-1886), add(1889-1891), _save_entry_report(1916-1936), export_preview_pdf(1938-1967), export_preview_word(1969-2009), export_preview_excel(2011-2047), make_tree(2049-2058), pick_item(2060-2081), choose(2061-2080), ld(2068-2072), sel(2074-2078), bind_item_lookup(2083-2100), lookup(2085-2098), _set_form_editable(2103-2116), walk(2106-2115), document_selector(2118-2152), refresh(2123-2134), selected(2135-2140), dashboard(2154-2266), load_details(2238-2262), _refresh_dashboard_kpis(2268-2282), dashboard_details(2284-2288), item_history(2290-2310), _ask_item_master_filters(2312-2396), finish(2365-2377), items(2398-2636), hierarchy(2439-2448), selected_prefix(2494-2507), balance_as_of(2509-2516), load(2518-2556), set_page(2558-2559), select_node(2561-2582), open_find(2588-2607), search_fn(2590-2605), visible_rows(2612-2614), print_inventory(2615-2619), export_inventory_word(2620-2622), export_inventory_excel(2623-2625), portable_inventory(2630-2632), inventory_codes(2638-2922), btn(2674-2679), close_editor(2715-2725), edit_cell(2727-2753), commit(2745-2751), rows_query(2755-2768), load(2770-2785), new_record(2787-2808), commit(2801-2805), selected_row(2810-2812), edit_record(2814-2822), save_record(2824-2867), delete_record(2869-2880), refresh(2882-2882), do_print(2883-2885), do_close(2886-2886), filter_grid(2904-2911), open_mto_inventory_flow(2924-2947), open_code_opening_flow(2949-2957), code_opening(2959-2960), _open_code_opening_popup(2962-2963), _open_code_opening_detail(2965-3208), norm(3035-3036), table_for(3038-3039), row_for(3041-3046), search_any_destination(3048-3061), desc_hit(3063-3067), clear_form(3069-3082), load_for_edit(3084-3105), check_duplicates(3107-3118), save_code(3123-3174), edit_action(3176-3180), delete_code(3182-3197), _mto_new_item_dialog(3210-3246), save(3226-3243), _item_filter_bar(3248-3260), _date_filter_bar(3262-3270), _ask_mto_inventory_filters(3272-3317), finish(3302-3310), mto_inventory(3319-3519), open_find(3353-3372), search_fn(3355-3370), hierarchy(3391-3395), rebuild_nav(3397-3408), mto_balance(3432-3441), load(3443-3485), set_page(3487-3487), select_node(3488-3497), visible_rows(3502-3502), do_print(3503-3507), export_word(3508-3510), export_excel(3511-3513), party_master(3521-3572), load(3531-3534), clear(3535-3539), new_form(3540-3541), save(3542-3548), load_party_row(3549-3553), on_party_select(3554-3555), edit(3557-3561), delete_party(3562-3568), user_management(3574-3658), sync_role(3601-3606), load(3610-3613), clear(3614-3617), edit(3618-3625), save(3626-3643), delete_user(3644-3655), _renumber_tree(3661-3664), demand(3666-3830), _restore_demand_tree_columns(3709-3715), add(3718-3726), edit_item(3728-3740), delete_item(3742-3750), new_form(3754-3760), save(3762-3778), delete_current(3782-3788), cancel_form(3789-3797), preview_now(3798-3808), edit_saved_demand(3809-3812), print_now(3813-3823), load_demand_into_form(3832-3844), refresh_saved_cache(3846-3858), grr(3860-4023), add(3892-3900), edit_item(3902-3912), delete_item(3914-3922), new_form(3926-3932), save(3934-3955), delete_current(3959-3965), cancel_form(3966-3974), preview_now(3975-3993), portable_current(3994-3997), edit_saved_grr(3999-4002), print_now(4003-4016), load_grr_into_form(4025-4037), issue(4039-4185), old_issue_qty(4068-4071), update_balance(4072-4080), add(4082-4091), edit_item(4093-4104), new_form(4108-4114), post(4116-4137), delete_current(4138-4144), cancel_form(4145-4153), preview_now(4154-4161), portable_current(4162-4164), load_saved_issue(4169-4171), edit_saved_issue(4172-4175), print_issue_now(4176-4181), load_issue_into_form(4187-4200), _ask_report_criteria(4202-4265), finish(4251-4259), _open_report_child(4267-4272), open_stock_balance_report_flow(4274-4277), open_grr_report_flow(4279-4282), open_demand_report_flow(4284-4287), open_issue_report_flow(4289-4292), open_party_report_flow(4294-4297), _ask_stock_balance_filters(4299-4322), ok(4314-4315), cancel(4316-4316), stock_balance(4324-4387), period(4340-4351), header_summary(4352-4353), load(4354-4363), reopen_filters(4364-4368), open_find_stock(4372-4385), search_fn(4374-4384), ledger(4389-4401), open_document_editor(4403-4411), _edit_from_selector(4413-4429), show_saved_records(4431-4462), view(4454-4458), documents(4464-4509), edit_selected(4483-4489), delete_selected(4490-4502), doc_export_selected(4511-4517), doc_preview_selected(4519-4529), doc_print_selected(4531-4539), load_document(4541-4571), _print_loaded_document(4565-4570), _report_filter_popup(4573-4590), ok(4586-4587), cancel(4588-4588), _report_window(4592-4636), load(4605-4612), hdr(4613-4613), open_find_report(4619-4633), search_fn(4621-4632), report_grr(4638-4649), pb(4640-4648), report_demand(4651-4662), pb(4653-4661), report_issue(4664-4673), pb(4666-4672), report_party(4675-4685), pb(4677-4684), reports(4687-4815), load_grr_item(4700-4705), load_grr_date(4713-4721), load_party(4733-4741), load_dem_item(4754-4759), load_dem_date(4767-4775), load_iss_item(4789-4794), load_iss_date(4802-4810), print_item_master(4817-4819), print_party_master(4821-4823), print_report(4825-4839), print_stock(4841-4846), print_ledger(4848-4855), _get_doc_data(4857-4885), export_word(4887-4934), export_excel(4936-4976), preview_pdf(4978-4986), _open_direct_printer(4988-5018), _select_windows_printer_for_pdf(5020-5391), render_preview(5145-5164), on_resize(5166-5168), parse_page_selection(5187-5203), selected_printer(5205-5207), print_rendered_pages(5209-5367), close(5369-5379), print_pdf(5393-5411), open_file(5413-5418), print_demand(5420-5425), print_grr(5427-5435), print_issue(5437-5442)

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
0993:             xb.pack(side="left")
0994:             old_task=state.get("task")
0995:             try:
0996:                 if old_task is not None and old_task is not item and old_task.winfo_exists():
0997:                     old_task.destroy()
0998:             except Exception:
0999:                 pass
1000:             state["task"]=item
1001:         def close():
1002:             try:
1003:                 task=state.get("task")
1004:                 if task and task.winfo_exists(): task.destroy()
1005:             except Exception: pass
1006:             try:
1007:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
1008:             except Exception: pass
1009:             try: outer.destroy()
1010:             except Exception: pass
1011:             if not getattr(self,"_mdi_windows",[]):
1012:                 self._mdi_host.place_forget()
1013:                 self._restore_dashboard_after_internal_close()
```
```text
1006:             try:
1007:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
1008:             except Exception: pass
1009:             try: outer.destroy()
1010:             except Exception: pass
1011:             if not getattr(self,"_mdi_windows",[]):
1012:                 self._mdi_host.place_forget()
1013:                 self._restore_dashboard_after_internal_close()
1014:                 self._restore_dashboard_after_internal_close()
1015:                 # Restore the original application shell FIRST, then rebuild
1016:                 # only the Dashboard body. This keeps the top header/navigation
1017:                 # exactly as they are when the application starts.
1018:                 try:
1019:                     if getattr(self,"_shell_header",None) is not None and self._shell_header.winfo_exists():
1020:                         self._shell_header.pack(fill="x",before=self.body)
1021:                     if getattr(self,"_shell_nav",None) is not None and self._shell_nav.winfo_exists():
1022:                         self._shell_nav.pack(fill="x",before=self.body,after=self._shell_header)
1023:                 except Exception: pass
1024:                 try:
1025:                     self.dashboard()
1026:                 except Exception: pass
```
```text
1059:             return None
1060:         self._inventory_codes_filter=criteria
1061:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1062:         try:
1063:             self.items(container=body)
1064:             win.lift()
1065:             return win
1066:         except Exception:
1067:             try: win._internal_close()
1068:             except Exception: pass
1069:             raise
1070: 
1071:     def open_inventory_codes_report_window(self, criteria=None):
1072:         """Open Inventory Codes as a real report-style child window.
1073: 
1074:         This intentionally mirrors the supplied Preview Report workflow: a
1075:         separate resizable/maximizable window with a left navigation tree,
1076:         compact report toolbar, Find dialog, and print/export commands.
1077:         The main application remains open behind it.
1078:         """
1079:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
1076:         compact report toolbar, Find dialog, and print/export commands.
1077:         The main application remains open behind it.
1078:         """
1079:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
1080:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
1081:         }
1082:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1083: 
1084:         # --- report-style toolbar ---
1085:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
1086:         toolbar.pack(fill="x",side="top")
1087:         toolbar.pack_propagate(False)
1088: 
1089:         def tbtn(text,cmd,width=9):
1090:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
1091:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
1092:                          padx=3,pady=1)
1093:             b.pack(side="left",padx=2,pady=6)
1094:             return b
1095: 
1096:         # --- main report body ---
```
```text
1107:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
1108:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
1109:         navscroll.config(command=code_tree.yview)
1110:         navscroll.pack(side="right",fill="y")
1111:         code_tree.pack(side="left",fill="both",expand=True)
1112: 
1113:         right=tk.Frame(content,bg="#EDEDED")
1114:         right.pack(side="left",fill="both",expand=True)
1115:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
1116:         reportbar.pack(fill="x")
1117:         reportbar.pack_propagate(False)
1118:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
1119:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
1120:         tab.pack(side="left",padx=4,pady=2)
1121:         titlevar=tk.StringVar(value="Inventory Summary")
1122:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
1123:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
1124: 
1125:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
1126:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
1127:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1261:                     vals=tree.item(iid,"values")
1262:                     if str(vals[1]).lower()==str(target).lower():
1263:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1264:                 return True
1265:             self._open_exact_find_text_popup(search_fn)
1266:             self._item_master_find_callback=find_popup
1267: 
1268: 
1269:         def print_report():
1270:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1271:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1272:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1273: 
1274:         def export_pdf():
1275:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1276:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1277:         def export_word():
1278:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1279:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1280:         def export_excel():
1281:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1277:         def export_word():
1278:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1279:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1280:         def export_excel():
1281:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1282:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1283: 
1284:         tbtn("Find",find_popup,7)
1285:         tbtn("Print",print_report,7)
1286:         tbtn("PDF",export_pdf,6)
1287:         tbtn("Word",export_word,6)
1288:         tbtn("Excel",export_excel,6)
1289:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1290:         tbtn("Refresh",load,8)
1291:         tbtn("Close",win._internal_close,7)
1292:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1293:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1294: 
1295:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1296:         build_nav(); load(); win.focus_force()
1297:         return win
```
```text
1307:         self.body=frame
1308:         closed={"done":False}
1309:         def close_window():
1310:             if closed["done"]: return
1311:             closed["done"]=True
1312:             if getattr(self,"body",None) is frame: self.body=old_body
1313:             self._page_actions=old_actions
1314:             self._item_master_find_callback=old_find
1315:             try: win._internal_close()
1316:             except Exception: win.destroy()
1317:         win._internal_close=close_window
1318:         try:
1319:             method(); self.update_idletasks(); win.lift(); return win
1320:         except Exception:
1321:             close_window(); raise
1322: 
1323:     def _manual_check_update(self):
1324:         try:
1325:             updater.check_for_update(self, manual=True)
1326:         except Exception as e:
1327:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1331:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1332:         except Exception as e:
1333:             messagebox.showerror("Current Version", str(e), parent=self)
1334: 
1335:     def build_menu_bar(self):
1336:         """Professional section / sub-section menu bar, ERP style:
1337:         Inventory > Item Master
1338:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1339:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1340:         Edit > Change Password, User Management
1341:         Help > Backup Now, Restore Backup, Network Setup
1342:         """
1343:         menubar=tk.Menu(self)
1344: 
1345:         m_inv=tk.Menu(menubar,tearoff=0)
1346:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1347:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1348:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1349:         menubar.add_cascade(label="Inventory",menu=m_inv)
1350: 
1351:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1351:         m_trans=tk.Menu(menubar,tearoff=0)
1352:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1353:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1354:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1355:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1356:         menubar.add_cascade(label="Transaction",menu=m_trans)
1357: 
1358:         m_rep=tk.Menu(menubar,tearoff=0)
1359:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1360:         m_rep.add_separator()
1361:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1362:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1363:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1364:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1365:         menubar.add_cascade(label="Report",menu=m_rep)
1366: 
1367:         m_edit=tk.Menu(menubar,tearoff=0)
1368:         m_edit.add_command(label="Change Password",command=self.change_password)
1369:         if self.is_admin:
1370:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1371:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1366: 
1367:         m_edit=tk.Menu(menubar,tearoff=0)
1368:         m_edit.add_command(label="Change Password",command=self.change_password)
1369:         if self.is_admin:
1370:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1371:         menubar.add_cascade(label="Edit",menu=m_edit)
1372: 
1373:         m_help=tk.Menu(menubar,tearoff=0)
1374:         m_help.add_command(label="Backup Now",command=self.backup_now)
1375:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1376:         m_help.add_command(label="Current Version",command=self._show_current_version)
1377:         if self.is_admin:
1378:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1379:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1380:         menubar.add_cascade(label="Help",menu=m_help)
1381: 
1382:         self.config(menu=menubar)
1383: 
1384:     def open_calendar_picker(self, var):
1385:         """Small month-grid calendar popup. Picking a day sets `var` to
1386:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1439:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1440:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1441:         return f
1442: 
1443:     def clearbody(self):
1444:         self._portable_print_context=None
1445:         for w in self.body.winfo_children(): w.destroy()
1446:         self._page_actions = {
1447:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1448:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1449:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1450:             "cancel": lambda: self.dashboard(),
1451:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1452:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1453:         }
1454:         # Single SAP-style toolbar at the very top.
1455:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1456:         self._page_action_bar=bar
1457:         self._page_action_first_button=None
1458:         def run_action(k):
1459:             if k=="edit" and not self.can_edit:
```
```text
1456:         self._page_action_bar=bar
1457:         self._page_action_first_button=None
1458:         def run_action(k):
1459:             if k=="edit" and not self.can_edit:
1460:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1461:             if k=="delete" and not self.can_delete:
1462:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1463:             self._page_actions[k]()
1464:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1465:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1466:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1467:             b.pack(side="left",padx=(0,2))
1468:             if self._page_action_first_button is None: self._page_action_first_button=b
1469:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1470: 
1471:     def _portable_print_current(self):
1472:         ctx=getattr(self,"_portable_print_context",None)
1473:         if not ctx:
1474:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1475:             return
1476:         try:
```
```text
1478:             if not data: return
1479:             title,header,columns,rows=data
1480:             self.portable_print_dialog(title,header,columns,rows)
1481:         except Exception as e:
1482:             messagebox.showerror("Portable Printer",str(e))
1483: 
1484:     def portable_print_dialog(self,title,header_lines,columns,rows):
1485:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1486:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1487:         if not WIN32PRINT_AVAILABLE:
1488:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1489:             return
1490:         try:
1491:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1492:         except Exception as e:
1493:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1494:             return
1495:         if not printers:
1496:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1497:             return
1498:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1548:                 if vals and pv.get() not in vals: pv.set(vals[0])
1549:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1550:             except Exception as ex: status.set(str(ex))
1551:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1552:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1553:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1554:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1555:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1556:         win.bind("<Escape>",lambda e:win._internal_close())
1557:         win.focus_force()
1558: 
1559:     def preview_tree(self, title, tree, header_lines=None):
1560:         """Preview the exact rows currently visible in a Treeview."""
1561:         cols=list(tree["columns"])
1562:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1563:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1564:         if not rows:
1565:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1566:             return
1567:         widths=[]
1568:         for c in cols:
```
```text
1565:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1566:             return
1567:         widths=[]
1568:         for c in cols:
1569:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1570:             except Exception: widths.append(100)
1571:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1572: 
1573:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1574:         self._page_actions.update({
1575:             "save": save or self._page_actions.get("save"),
1576:             "edit": edit or self._page_actions.get("edit"),
1577:             "delete": delete or self._page_actions.get("delete"),
1578:             "cancel": cancel or self._page_actions.get("cancel"),
1579:             "print": print or self._page_actions.get("print"),
1580:             "preview": preview or self._page_actions.get("preview"),
1581:         })
1582: 
1583:     def _add_transaction_new_button(self, command):
1584:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1585:         if bar is None or first is None: return
```
```text
1594:         sep.pack(side="left",fill="y",padx=4)
1595:         for w in existing:
1596:             try:
1597:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1598:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1599:                 else: w.pack(side="left")
1600:             except Exception: pass
1601: 
1602:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1603:         """Draw a consistent professional report header and return the first table Y.
1604: 
1605:         For GRN Receipt reports the document number is shown on the left and
1606:         the GRN Date is deliberately shown on the right in a bordered document
1607:         information panel.
1608:         """
1609:         W,H=page_size
1610:         if y_top is None: y_top=H-24
1611:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1612:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1613:         if os.path.exists(LOGO_FILE):
1614:             try:
```
```text
1607:         information panel.
1608:         """
1609:         W,H=page_size
1610:         if y_top is None: y_top=H-24
1611:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1612:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1613:         if os.path.exists(LOGO_FILE):
1614:             try:
1615:                 from reportlab.lib.utils import ImageReader
1616:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1617:             except Exception:
1618:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1619:         else:
1620:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1621:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1622:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1623:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1624:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1625: 
1626:         # Professional document information box.
1627:         info_top=logo_y-12
```
```text
1660:                 # naturally occupies the right-hand cell when supplied second.
1661:                 c.setFont("Helvetica-Bold",7)
1662:                 c.drawString(xx,yy,(label+":")[:28])
1663:                 c.setFont("Helvetica",7)
1664:                 c.drawString(xx+58,yy,val[:58])
1665:             return box_y-12
1666:         return info_top-6
1667: 
1668:     def _report_footer(self, c, page_no, page_size=A4):
1669:         W,H=page_size
1670:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1671:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1672:         c.drawString(24,13,REPORT_FOOTER)
1673:         c.drawCentredString(W/2,13,"Made by Zulfiqar Ali")
1674:         c.drawRightString(W-24,13,f"Page {page_no}")
1675:         c.setFillColorRGB(0,0,0)
1676: 
1677:     def _grr_signature_block(self, c, y, page_size=A4):
1678:         """Draw the three requested transaction-document signature lines."""
1679:         W,H=page_size
1680:         labels=["Prepared By","Store Keeper","Store Incharge"]
```
```text
1688:             x=left+i*col_w
1689:             c.setLineWidth(0.6)
1690:             c.line(x+30,top-34,x+col_w-30,top-34)
1691:             c.setFont("Helvetica-Bold",7)
1692:             c.drawCentredString(x+col_w/2,top-48,label)
1693:         return True
1694: 
1695:     def _finish_page(self, c, page_no, page_size=A4):
1696:         self._report_footer(c,page_no,page_size); c.showPage()
1697: 
1698:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1699:         """Word-wrap `text` into a list of lines that each fit inside
1700:         max_width (points) at the given font, breaking mid-word only when a
1701:         single word is itself wider than the column."""
1702:         text=str(text) if text is not None else ""
1703:         if not text:
1704:             return [""]
1705:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1706:         lines=[]; cur=""
1707:         for word in text.split(" "):
1708:             trial=(cur+" "+word).strip() if cur else word
```
```text
1717:                     mid=(lo+hi)//2
1718:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1719:                     else: hi=mid-1
1720:                 lines.append(w[:fit_at]); w=w[fit_at:]
1721:             cur=w
1722:         if cur: lines.append(cur)
1723:         return lines or [""]
1724: 
1725:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1726:         """Create a paginated professional PDF with logo, bordered information,
1727:         GRR signature lines and page numbers. Also keep the same report data in
1728:         memory so the built-in Windows printer dialog can print directly without
1729:         requiring a PDF application's PrintTo association."""
1730:         if not hasattr(self, "_print_jobs"):
1731:             self._print_jobs = {}
1732:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1733:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1734:         page=1
1735:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1736:         usable=W-56
1737:         n=max(1,len(headers))
```
```text
1759:             if desc_idx is not None and desc_idx < len(r):
1760:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1761:             else:
1762:                 desc_lines=[""]
1763:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1764:             # Reserve room on the final page for the three transaction signatures + footer.
1765:             reserve=120 if is_transaction_doc else 42
1766:             if y-row_h<reserve:
1767:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1768:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1769:             # Item rows are intentionally border-free. The section/header remains
1770:             # professional while avoiding the unwanted boxed line around each
1771:             # individual printed item row. Description is drawn separately
1772:             # below (auto-fit / wrapped), so it is skipped in this pass.
1773:             for ci,(xx,val) in enumerate(zip(xs,r)):
1774:                 if ci==desc_idx: continue
1775:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1776:             if desc_idx is not None and desc_idx < len(r):
1777:                 for li,ln in enumerate(desc_lines):
1778:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1779:             y-=row_h
```
```text
1774:                 if ci==desc_idx: continue
1775:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1776:             if desc_idx is not None and desc_idx < len(r):
1777:                 for li,ln in enumerate(desc_lines):
1778:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1779:             y-=row_h
1780:         if is_transaction_doc:
1781:             # Keep the three requested transaction signatures at the physical bottom
1782:             # final page, immediately above the report footer.  If the item
1783:             # table reaches this reserved area, start a fresh final page.
1784:             bottom_sig_y = 138
1785:             if y < 165:
1786:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1787:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1788:             # Draw signatures at a fixed bottom position so they never float
1789:             # directly after the last item row.
1790:             self._grr_signature_block(c,bottom_sig_y,page_size)
1791:         self._report_footer(c,page,page_size); c.save()
1792:         if auto_print:
1793:             self.print_pdf(path)
1794:         return path
```
```text
1788:             # Draw signatures at a fixed bottom position so they never float
1789:             # directly after the last item row.
1790:             self._grr_signature_block(c,bottom_sig_y,page_size)
1791:         self._report_footer(c,page,page_size); c.save()
1792:         if auto_print:
1793:             self.print_pdf(path)
1794:         return path
1795: 
1796:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1797:         """Professional on-screen preview showing bordered document information
1798:         and a bordered item section. GRN Date is displayed in the right column."""
1799:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1800:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1801:         # Preview intentionally hides the company logo and company name.
1802:         # The actual generated/printed PDF still contains both via
1803:         # _report_header(), so only the on-screen preview is affected.
1804:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1805:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1806:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1807: 
1808:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
```
```text
1829:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1830: 
1831:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1832:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1833:         tr=self.make_tree(items,columns,widths)
1834:         for r in rows: tr.insert("", "end", values=r)
1835: 
1836:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1837:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1838:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1839:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1840:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1841:         win.bind("<Control-f>",bind_preview_find)
1842:         win.bind("<Control-F>",bind_preview_find)
1843: 
1844:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1845:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1846:         if is_transaction_preview:
1847:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1848:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1849:                 sig.columnconfigure(i,weight=1)
```
```text
1847:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1848:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1849:                 sig.columnconfigure(i,weight=1)
1850:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1851:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1852:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1853: 
1854:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1855:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1856:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1857:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1858:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1859:         if on_save:
1860:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1861:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1862:         if not is_transaction_preview:
1863:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1864:         # IMPORTANT: this must remain a normal top-level window (not transient
1865:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1866:         # exactly like the Preview Report window in the supplied recording.
1867:         # The Find dialog is opened from this window and is independent.
```
```text
1860:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1861:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1862:         if not is_transaction_preview:
1863:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1864:         # IMPORTANT: this must remain a normal top-level window (not transient
1865:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1866:         # exactly like the Preview Report window in the supplied recording.
1867:         # The Find dialog is opened from this window and is independent.
1868:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1869:         win.focus_force()
1870: 
1871:     def _safe_report_name(self, title, extension):
1872:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1873:         safe=safe.replace(" ","_") or "Preview"
1874:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1875: 
1876:     def print_preview_window(self, title, header_lines, columns, rows):
1877:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1878:         self._open_direct_printer(title, header_lines, columns, rows,
1879:                                   landscape(A4) if len(columns) > 8 else A4)
1880: 
```
```text
1873:         safe=safe.replace(" ","_") or "Preview"
1874:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1875: 
1876:     def print_preview_window(self, title, header_lines, columns, rows):
1877:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1878:         self._open_direct_printer(title, header_lines, columns, rows,
1879:                                   landscape(A4) if len(columns) > 8 else A4)
1880: 
1881:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1882:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1883:         This keeps the Export PDF button functional on a machine where the bundled
1884:         ReportLab package cannot be imported."""
1885:         def esc(v):
1886:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1887:         W,H=842,595
1888:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1889:         def add(txt,size=8,leading=11):
1890:             lines.append(f"/F1 {size} Tf")
1891:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1892:         add(str(title),12,16)
1893:         for h in header_lines or []:
```
```text
1900:         lines.append("ET")
1901:         stream="\n".join(lines).encode("latin-1","replace")
1902:         objs=[]
1903:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1904:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1905:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1906:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1907:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1908:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1909:         for i,obj in enumerate(objs,1):
1910:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1911:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1912:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1913:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1914:         with open(path,"wb") as f: f.write(out)
1915: 
1916:     def _save_entry_report(self, title, header_lines, columns, rows):
1917:         try:
1918:             os.makedirs(REPORTS_DIR, exist_ok=True)
1919:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1920:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```
```text
1913:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1914:         with open(path,"wb") as f: f.write(out)
1915: 
1916:     def _save_entry_report(self, title, header_lines, columns, rows):
1917:         try:
1918:             os.makedirs(REPORTS_DIR, exist_ok=True)
1919:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1920:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
1921:             path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
1922:             page_size = landscape(A4) if len(columns) > 8 else A4
1923:             if REPORTLAB:
1924:                 self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
1925:             else:
1926:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1927:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1928:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1929:             with open(path, "rb") as f:
1930:                 if f.read(5) != b"%PDF-":
1931:                     raise IOError("Generated report is not a valid PDF.")
1932:             self._last_entry_report_path = path
1933:             return path
```
```text
1927:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1928:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1929:             with open(path, "rb") as f:
1930:                 if f.read(5) != b"%PDF-":
1931:                     raise IOError("Generated report is not a valid PDF.")
1932:             self._last_entry_report_path = path
1933:             return path
1934:         except Exception as exc:
1935:             self._last_entry_report_path = None
1936:             return None
1937: 
1938:     def export_preview_pdf(self, title, header_lines, columns, rows):
1939:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1940:         try:
1941:             os.makedirs(REPORTS_DIR, exist_ok=True)
1942:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1943:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1944:             generated = False
1945:             if REPORTLAB:
1946:                 try:
1947:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
```
```text
1944:             generated = False
1945:             if REPORTLAB:
1946:                 try:
1947:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1948:                     generated = True
1949:                 except Exception:
1950:                     generated = False
1951:             if not generated:
1952:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1953:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1954:                 raise IOError("The PDF file was not created in the Reports folder.")
1955:             with open(path, "rb") as pf:
1956:                 signature = pf.read(5)
1957:             if signature != b"%PDF-":
1958:                 raise IOError("The generated file is not a valid PDF.")
1959:             self._last_report_path = path
1960:             try:
1961:                 webbrowser.open("file://" + path)
1962:             except Exception:
1963:                 self.open_file(path)
1964:             return path
```
```text
1958:                 raise IOError("The generated file is not a valid PDF.")
1959:             self._last_report_path = path
1960:             try:
1961:                 webbrowser.open("file://" + path)
1962:             except Exception:
1963:                 self.open_file(path)
1964:             return path
1965:         except Exception as e:
1966:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1967:             return None
1968: 
1969:     def export_preview_word(self, title, header_lines, columns, rows):
1970:         """Export exactly what is visible in the current preview to Word."""
1971:         if not DOCX_AVAILABLE:
1972:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1973:         path=self._safe_report_name(title,"docx")
1974:         doc=Document()
1975:         sec=doc.sections[0]
1976:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1977:         sec.header.paragraphs[0].runs[0].bold=True
1978:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
```
```text
2000:             doc.add_paragraph("")
2001:             sig=doc.add_table(rows=2,cols=3)
2002:             labels=["Prepared By","Store Keeper","Store Incharge"]
2003:             for i,label in enumerate(labels):
2004:                 sig.cell(0,i).text="____________________"
2005:                 sig.cell(1,i).text=label
2006:                 for para in sig.cell(1,i).paragraphs:
2007:                     for run in para.runs: run.bold=True
2008:         doc.save(path)
2009:         self.open_file(path)
2010: 
2011:     def export_preview_excel(self, title, header_lines, columns, rows):
2012:         """Export exactly what is visible in the current preview to Excel."""
2013:         if not XLSX_AVAILABLE:
2014:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
2015:         path=self._safe_report_name(title,"xlsx")
2016:         wb=openpyxl.Workbook(); ws=wb.active
2017:         ws.title="Preview"
2018:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
2019:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
2020:         if not is_transaction_preview:
```
```text
2038:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
2039:             for col in range(1,4):
2040:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
2041:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
2042:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
2043:         for col_cells in ws.columns:
2044:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
2045:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
2046:         wb.save(path)
2047:         self.open_file(path)
2048: 
2049:     def make_tree(self,parent,cols,widths=None):
2050:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
2051:         tr=ttk.Treeview(fr,columns=cols,show="headings")
2052:         for i,c in enumerate(cols):
2053:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
2054:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
2055:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
2056:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
2057:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
2058:         return tr
```
```text
2111:                     w.state(["!disabled"] if editable else ["disabled"])
2112:             except Exception:
2113:                 try: w.configure(state="normal" if editable else "disabled")
2114:                 except Exception: pass
2115:             for ch in w.winfo_children(): walk(ch)
2116:         for root in roots: walk(root)
2117: 
2118:     def document_selector(self, parent, label, typ, var, load_callback):
2119:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
2120:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
2121:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
2122:         combo.pack(side="left", padx=4)
2123:         def refresh():
2124:             vals=[]
2125:             if typ=="demand":
2126:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
2127:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
2128:             elif typ=="grr":
2129:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
2130:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
2131:             else:
```
```text
2138:             no=text.split(" -> ",1)[0].strip()
2139:             var.set(no)
2140:             load_callback(no)
2141:         combo.bind("<<ComboboxSelected>>", selected)
2142:         combo.bind("<Return>", selected)
2143:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2144:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2145:         refresh()
2146:         # Keep the currently open transaction's saved-record list live.
2147:         # Each save calls refresh_saved_cache(), so newly saved records appear
2148:         # immediately without closing/reopening the window or pressing Refresh.
2149:         if not hasattr(self, "_document_selector_refreshers"):
2150:             self._document_selector_refreshers = {}
2151:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2152:         return combo
2153: 
2154:     def dashboard(self):
2155:         # Dashboard-only visual refresh. All existing data queries, filters,
2156:         # callbacks and report/detail behavior are intentionally preserved.
2157:         self.clearbody()
2158:         c=self.conn
```
```text
2239:             for x in tr.get_children(): tr.delete(x)
2240:             params=[];where=[]
2241:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2242:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2243:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2244:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2245:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2246:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2247:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2248:                    FROM transactions t JOIN items i ON i.code=t.code"""
2249:             if where: sql += " WHERE " + " AND ".join(where)
2250:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2251:             rows=list(c.execute(sql,params))
2252:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2253:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2254:             bal_after={}
2255:             for txid,cc,typ,qty in alltx:
2256:                 running.setdefault(cc,0.0)
2257:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2258:                 bal_after[txid]=running[cc]
2259:             for r in rows:
```
```text
2634:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2635:         load()
2636:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2637: 
2638:     def inventory_codes(self):
2639:         """Inventory Codes using the classic desktop inventory interface.
2640: 
2641:         This screen intentionally follows the uploaded Inventory Management
2642:         reference: a simple module title, compact New/Edit/Delete/Save/
2643:         Refresh/Print/Close action row, and a full-width editable data grid.
2644:         All records come from the V18 database, so existing inventory data is
2645:         preserved rather than recreated.
2646:         """
2647:         self.clearbody()
2648:         # Remove the generic SAP action row; this page owns its own classic
2649:         # action row just like the reference Inventory/Items screen.
2650:         if self.body.winfo_children():
2651:             try:
2652:                 self.body.winfo_children()[0].destroy()
2653:             except Exception:
2654:                 pass
```
```text
2707:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2708:         if filter_text:
2709:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2710:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2711: 
2712:         editing={"id":None,"new":False}
2713:         cell_editor={"widget":None}
2714: 
2715:         def close_editor(save_value=False):
2716:             w=cell_editor.get("widget")
2717:             if not w:
2718:                 return
2719:             try:
2720:                 if save_value:
2721:                     w.event_generate("<Return>")
2722:                 w.destroy()
2723:             except Exception:
2724:                 pass
2725:             cell_editor["widget"]=None
2726: 
2727:         def edit_cell(event=None):
```
```text
2737:             bbox=tree.bbox(iid,colid)
2738:             if not bbox: return
2739:             close_editor(False)
2740:             x,y,w,h=bbox
2741:             val=str(tree.item(iid,"values")[idx] or "")
2742:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2743:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2744:             cell_editor["widget"]=e
2745:             def commit(_=None):
2746:                 try:
2747:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2748:                 finally:
2749:                     try:e.destroy()
2750:                     except Exception:pass
2751:                     cell_editor["widget"]=None
2752:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2753:             e.bind("<FocusOut>",commit)
2754: 
2755:         def rows_query():
2756:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2757:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2759:             if tc: where.append("code <= ?"); params.append(tc)
2760:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2761:             if df or dt:
2762:                 sub=[]; sp=[]
2763:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2764:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2765:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2766:                 params.extend(sp)
2767:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2768:             return sql,params
2769: 
2770:         def load():
2771:             close_editor(False)
2772:             for i in tree.get_children(): tree.delete(i)
2773:             sql,params=rows_query()
2774:             count=0
2775:             for r in self.conn.execute(sql,params):
2776:                 # V18 stores UOM/opening and the original application may have
2777:                 # rate/remarks columns in some versions. Read them safely.
2778:                 rid,code,desc,uom,opening,rate,remarks=r
2779:                 bal=stock(self.conn,code)
```
```text
2793:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2794:             editing["id"]=None; editing["new"]=True
2795:             # Put the user directly into the Code cell.
2796:             try:
2797:                 bbox=tree.bbox(iid,"#2")
2798:                 if bbox:
2799:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2800:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2801:                     def commit(_=None):
2802:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2803:                         try:e.destroy()
2804:                         except Exception:pass
2805:                         cell_editor["widget"]=None
2806:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2807:             except Exception: pass
2808:             status.set("New row added — enter values, then press Save")
2809: 
2810:         def selected_row():
2811:             a=tree.selection()
2812:             return a[0] if a else None
2813: 
```
```text
2813: 
2814:         def edit_record():
2815:             iid=selected_row()
2816:             if not iid:
2817:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2818:             if not self.can_edit and not self.is_admin:
2819:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2820:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2821:             status.set("Edit mode — double-click any cell to change it, then press Save")
2822:             tree.focus(iid); tree.see(iid)
2823: 
2824:         def save_record():
2825:             iid=selected_row()
2826:             if not iid:
2827:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2828:             if not self.can_edit and not self.is_admin:
2829:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2830:             close_editor(True)
2831:             vals=list(tree.item(iid,"values"))
2832:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2833:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2831:             vals=list(tree.item(iid,"values"))
2832:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2833:             try: opening=float(str(vals[4]).strip() or 0)
2834:             except Exception: raise ValueError("Opening Qty must be a number.")
2835:             try: rate=float(str(vals[5]).strip() or 0)
2836:             except Exception: raise ValueError("Rate must be a number.")
2837:             remarks=str(vals[6]).strip()
2838:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2839:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2840:             if not desc:
2841:                 messagebox.showerror("Save","Description is required."); return
2842:             if opening<0:
2843:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2844:             rid=vals[0]
2845:             try:
2846:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2847:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2848:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2849:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2850:                 if rid:
2851:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2854:                                       (code,desc,uom,opening,rid))
2855:                     if oldcode!=code:
2856:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2857:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2858:                             except Exception:pass
2859:                 else:
2860:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2861:                                       (code,desc,uom,"",opening,0,"Local",0))
2862:                 self.conn.commit()
2863:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2864:                 backup_database(); load()
2865:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2866:             except Exception as ex:
2867:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2868: 
2869:         def delete_record():
2870:             iid=selected_row()
2871:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2872:             if not self.can_delete and not self.is_admin:
2873:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2874:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2870:             iid=selected_row()
2871:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2872:             if not self.can_delete and not self.is_admin:
2873:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2874:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2875:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2876:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2877:             try:
2878:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2879:             except Exception as ex:
2880:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2881: 
2882:         def refresh(): load()
2883:         def do_print():
2884:             try:self.preview_tree("Inventory Codes",tree)
2885:             except Exception as ex:messagebox.showerror("Print",str(ex))
2886:         def do_close(): self.dashboard()
2887: 
2888:         btn("New",new_record,8)
2889:         btn("Edit",edit_record,8)
2890:         btn("Delete",delete_record,8)
```
```text
2883:         def do_print():
2884:             try:self.preview_tree("Inventory Codes",tree)
2885:             except Exception as ex:messagebox.showerror("Print",str(ex))
2886:         def do_close(): self.dashboard()
2887: 
2888:         btn("New",new_record,8)
2889:         btn("Edit",edit_record,8)
2890:         btn("Delete",delete_record,8)
2891:         btn("Save",save_record,8)
2892:         btn("Refresh",refresh,9)
2893:         btn("Preview",do_print,8)
2894:         btn("Print",do_print,8)
2895:         btn("Close",do_close,8)
2896: 
2897:         # Search is deliberately small and sits on the right, without changing
2898:         # the reference layout of the action buttons.
2899:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2900:         search=tk.StringVar()
2901:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2902:         se.pack(side="left",padx=2)
2903:         self._item_master_search_entry=se
```
```text
2911:                     tree.detach(iid)
2912:         search.trace_add("write",filter_grid)
2913:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2914: 
2915:         tree.bind("<Double-1>",edit_cell)
2916:         tree.bind("<F2>",lambda e: edit_record())
2917:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2918:         self._page_actions={
2919:             "save":save_record,"edit":edit_record,"delete":delete_record,
2920:             "cancel":do_close,"print":do_print,"preview":do_print
2921:         }
2922:         load()
2923: 
2924:     def open_mto_inventory_flow(self):
2925:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2926: 
2927:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2928:         Cancel/X only closes the popup.
2929:         """
2930:         criteria = self._ask_mto_inventory_filters()
2931:         if not criteria or criteria.get("cancelled"):
```
```text
3093:                 return False
3094:             destination.set(found_dest)
3095:             edit_mode.update(on=True, original=r[0], dest=found_dest)
3096:             code.set(r[0])
3097:             desc.set(r[1] or "")
3098:             uom.set(r[2] or UOM_OPTIONS[0])
3099:             opening.set(str(r[3] if r[3] is not None else 0))
3100:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
3101:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
3102:             err.set("")
3103:             edit_btn.configure(text="SAVE EDIT")
3104:             ce.focus_set()
3105:             return True
3106: 
3107:         def check_duplicates(*_):
3108:             c = code.get().strip()
3109:             d = desc.get().strip()
3110:             dest = destination.get()
3111:             msgs = []
3112:             r = row_for(dest, c) if len(norm(c)) == 8 else None
3113:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
3115:             dh = desc_hit(dest, d) if d else None
3116:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
3117:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
3118:             hint.set("\n".join(msgs))
3119: 
3120:         code.trace_add("write", check_duplicates)
3121:         desc.trace_add("write", check_duplicates)
3122: 
3123:         def save_code():
3124:             try:
3125:                 c = code.get().strip()
3126:                 d = desc.get().strip()
3127:                 u = uom.get().strip()
3128:                 dest = destination.get()
3129:                 digits = norm(c)
3130:                 if len(digits) != 8:
3131:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3132:                 if not d:
3133:                     raise ValueError("Description is required.")
3134:                 try:
3135:                     op = float(opening.get().strip() or 0)
```
```text
3156:                         (c, d, u, op, iso, old)
3157:                     )
3158:                     action = "updated"
3159:                 else:
3160:                     self.conn.execute(
3161:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3162:                         (c, d, u, "", op, 0, iso)
3163:                     )
3164:                     action = "saved"
3165:                 self.conn.commit()
3166:                 backup_database()
3167:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3168:                 # Keep popup open for fast multiple entries.
3169:                 clear_form(keep_search=False)
3170:                 ce.focus_set()
3171:             except Exception as ex:
3172:                 self.conn.rollback()
3173:                 err.set(str(ex))
3174:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3175: 
3176:         def edit_action():
```
```text
3172:                 self.conn.rollback()
3173:                 err.set(str(ex))
3174:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3175: 
3176:         def edit_action():
3177:             if not edit_mode["on"]:
3178:                 load_for_edit()
3179:             else:
3180:                 save_code()
3181: 
3182:         def delete_code():
3183:             if not edit_mode["on"]:
3184:                 if not load_for_edit():
3185:                     return
3186:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3187:                 return
3188:             try:
3189:                 t = table_for(edit_mode["dest"])
3190:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3191:                 self.conn.commit()
3192:                 backup_database()
```
```text
3188:             try:
3189:                 t = table_for(edit_mode["dest"])
3190:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3191:                 self.conn.commit()
3192:                 backup_database()
3193:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3194:                 clear_form(keep_search=False)
3195:             except Exception as ex:
3196:                 self.conn.rollback()
3197:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3198: 
3199:         btns = ttk.Frame(box)
3200:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3201:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3202:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3203:         edit_btn.pack(side="left", padx=4, ipadx=8)
3204:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3205:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3206:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3207:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3208:         ce.focus_set()
```
```text
3202:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3203:         edit_btn.pack(side="left", padx=4, ipadx=8)
3204:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3205:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3206:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3207:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3208:         ce.focus_set()
3209: 
3210:     def _mto_new_item_dialog(self, on_saved):
3211:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3212:         brand-new item can be created without leaving that screen. Writes
3213:         straight into the same Item Master (items table) used everywhere."""
3214:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3215:         win.transient(self); win.grab_set()
3216:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3217:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3218:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3219:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3220:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3221:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3222:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3218:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3219:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3220:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3221:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3222:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3223:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3224:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3225:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3226:         def save():
3227:             try:
3228:                 c=code.get().strip(); d=desc.get().strip()
3229:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3230:                 if not d: raise ValueError("Description is required.")
3231:                 try:
3232:                     opening_val=float(opening.get() or 0)
3233:                 except ValueError:
3234:                     raise ValueError("Opening Qty must be a number.")
3235:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3236:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3237:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3238:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3231:                 try:
3232:                     opening_val=float(opening.get() or 0)
3233:                 except ValueError:
3234:                     raise ValueError("Opening Qty must be a number.")
3235:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3236:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3237:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3238:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3239:                 self.conn.commit(); backup_database()
3240:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3241:                 win.grab_release(); win.destroy()
3242:                 on_saved()
3243:             except Exception as ex: messagebox.showerror("Error",str(ex))
3244:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3245:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3246:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3247: 
3248:     def _item_filter_bar(self, parent, on_change):
3249:         """Item Code entry + item-master picker + Search/Show All. Calls
3250:         on_change() whenever the code changes or a button is pressed."""
3251:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3337:         self._item_master_find_callback=None
3338:         self._portable_print_context=None
3339:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3340:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3341:         }
3342: 
3343:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3344:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3345:         self.conn.commit()
3346: 
3347:         # ---- Same professional in-app window layout as Inventory Codes ----
3348:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3349:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3350:                   foreground=COLORS["primary_dark"]).pack(side="left")
3351:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3352: 
3353:         def open_find():
3354:             state_find={"index":-1}
3355:             def search_fn(text):
3356:                 text=text.strip().lower()
3357:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3444:             for i in table.get_children(): table.delete(i)
3445:             where=["1=1"]; params=[]
3446:             prefix=state.get("prefix",""); q=search.get().strip()
3447:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3448:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3449:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3450:             if fc: where.append("code >= ?"); params.append(fc)
3451:             if tc: where.append("code <= ?"); params.append(tc)
3452:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3453:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3454:             records=[]
3455:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3456:                 # If a date filter is supplied, accept an opening-date match OR
3457:                 # a transaction in that date range. This prevents valid MTO codes
3458:                 # from disappearing merely because an older record has no opening_date.
3459:                 if df or dt:
3460:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3461:                     if not ok:
3462:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3463:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3464:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3534:                 tr.insert("", "end", values=r)
3535:         def clear():
3536:             for x in v.values(): x.set("")
3537:             try: tr.selection_remove(tr.selection())
3538:             except Exception: pass
3539:             self._set_form_editable(party_form_roots, False)
3540:         def new_form():
3541:             clear(); self._set_form_editable(party_form_roots, True)
3542:         def save():
3543:             try:
3544:                 name=v["name"].get().strip()
3545:                 if not name: raise ValueError("Party Name is required.")
3546:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3547:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3548:             except Exception as ex: messagebox.showerror("Error",str(ex))
3549:         def load_party_row(a):
3550:             if not a:return
3551:             r=tr.item(a[0])["values"]
3552:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3553:             self._set_form_editable(party_form_roots, False)
3554:         def on_party_select(_=None):
```
```text
3560:             load_party_row(a)
3561:             self._set_form_editable(party_form_roots, True)
3562:         def delete_party():
3563:             a=tr.selection()
3564:             if not a:
3565:                 messagebox.showwarning("Delete", "Select a party first."); return
3566:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3567:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3568:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3569:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3570:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3571:         self._add_transaction_new_button(new_form)
3572:         load(); clear()
3573: 
3574:     def user_management(self):
3575:         self.clearbody()
3576:         if not self.is_admin:
3577:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3578:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3579:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3580:         role=tk.StringVar(value="User")
```
```text
3617:             u_ent.state(["!disabled"])
3618:         def edit():
3619:             a=tr.selection()
3620:             if not a:
3621:                 messagebox.showwarning("Edit User","Select a user row first."); return
3622:             r=tr.item(a[0])["values"]
3623:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3624:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3625:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3626:         def save():
3627:             try:
3628:                 username=v["username"].get().strip()
3629:                 if not username: raise ValueError("Username is required.")
3630:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3631:                 pw=v["password"].get()
3632:                 if exists:
3633:                     pw_hash = hash_password(pw) if pw else exists[0]
3634:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3635:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3636:                 else:
3637:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3632:                 if exists:
3633:                     pw_hash = hash_password(pw) if pw else exists[0]
3634:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3635:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3636:                 else:
3637:                     if not pw: raise ValueError("Password is required for a new user.")
3638:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3639:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3640:                 self.conn.commit(); backup_database(); load(); clear()
3641:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3642:             except Exception as ex:
3643:                 messagebox.showerror("Error", str(ex))
3644:         def delete_user():
3645:             a=tr.selection()
3646:             if not a:
3647:                 messagebox.showwarning("Delete User","Select a user row first."); return
3648:             username=tr.item(a[0])["values"][0]
3649:             if username==self.current_user:
3650:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3651:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3652:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3647:                 messagebox.showwarning("Delete User","Select a user row first."); return
3648:             username=tr.item(a[0])["values"][0]
3649:             if username==self.current_user:
3650:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3651:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3652:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3653:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3654:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3655:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3656:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3657:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3658:         load()
3659: 
3660:     @staticmethod
3661:     def _renumber_tree(tree, rows):
3662:         for i,iid in enumerate(tree.get_children()):
3663:             vals=list(tree.item(iid,"values"));
3664:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3665: 
3666:     def demand(self):
3667:         self.clearbody(); self.demand_lines=[]
```
```text
3664:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3665: 
3666:     def demand(self):
3667:         self.clearbody(); self.demand_lines=[]
3668:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3669:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3670:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3671:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3672:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3673:         # Demand Date is intentionally displayed as its own dedicated field.
3674:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3675:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3676:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3677:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3678:                 ("special","Special Instructions"),("source","Recommended Source")]
3679:         for i,(k,n) in enumerate(fields):
3680:             r=i//4*2+3; c=i%4*2
3681:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3682:             if k=="dept":
3683:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3684:             elif k=="urgency":
```
```text
3754:         def new_form():
3755:             self._editing_document_key=None
3756:             for z in v.values(): z.set("")
3757:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3758:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3759:             for iid in tree.get_children(): tree.delete(iid)
3760:             self._set_form_editable(form_roots, True, skip=[selector])
3761: 
3762:         def save():
3763:             try:
3764:                 no=v["no"].get().strip()
3765:                 if not no: raise ValueError("Demand No is required.")
3766:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3767:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3768:                 if dup and getattr(self,"_editing_document_key",None) != no:
3769:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3770:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3771:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3772:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3773:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3774:                 self.conn.commit()
```
```text
3767:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3768:                 if dup and getattr(self,"_editing_document_key",None) != no:
3769:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3770:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3771:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3772:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3773:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3774:                 self.conn.commit()
3775:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3776:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3777:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3778:             except Exception as ex: messagebox.showerror("Error",str(ex))
3779:         form_roots=[f,line,editbar]
3780:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3781:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3782:         def delete_current():
3783:             no=v["no"].get().strip()
3784:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3785:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3786:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3787:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3800:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3801:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3802:                     f"Justification: {v['just'].get()}",
3803:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3804:             if not self.demand_lines:
3805:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3806:             self.show_preview_window("Purchase Demand", header,
3807:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3808:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3809:         def edit_saved_demand():
3810:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3811:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3812:             self._set_form_editable(form_roots, True, skip=[selector])
3813:         def print_now():
3814:             if not self.demand_lines:
3815:                 messagebox.showwarning("Print","Add at least one item line first."); return
3816:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3817:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3818:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3819:                     f"Justification: {v['just'].get()}",
3820:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3816:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3817:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3818:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3819:                     f"Justification: {v['just'].get()}",
3820:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3821:             self._open_direct_printer("Purchase Demand",header,
3822:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3823:                 self.demand_lines,A4)
3824:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3825:         self._add_transaction_new_button(new_form)
3826:         self._set_form_editable(form_roots, False, skip=[selector])
3827:         try:
3828:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3829:         except Exception: pass
3830:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3831: 
3832:     def load_demand_into_form(self,no,v,tree):
3833:         v["no"].set(no)
3834:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3835:         if not r:return
3836:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3838:         self.demand_lines=[]
3839:         for i in tree.get_children():tree.delete(i)
3840:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3841:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3842:         roots=getattr(self,"_transaction_form_roots",None)
3843:         if roots and "demand" in roots:
3844:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3845: 
3846:     def refresh_saved_cache(self,typ):
3847:         # Refresh saved-document dropdowns immediately after a successful save.
3848:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3849:         alive=[]
3850:         for combo, refresh in refreshers:
3851:             try:
3852:                 if combo.winfo_exists():
3853:                     refresh()
3854:                     alive.append((combo, refresh))
3855:             except Exception:
3856:                 pass
3857:         if hasattr(self, "_document_selector_refreshers"):
3858:             self._document_selector_refreshers[typ] = alive
```
```text
3857:         if hasattr(self, "_document_selector_refreshers"):
3858:             self._document_selector_refreshers[typ] = alive
3859: 
3860:     def grr(self):
3861:         self.clearbody(); self.grr_lines=[]
3862:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3863:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3864:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3865:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3866:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3867:         for i,(k,n) in enumerate(fields):
3868:             r=i//4*2+2;c=i%4*2
3869:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3870:             if k=="department":
3871:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3872:             elif k=="supplier":
3873:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3874:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3875:             elif k=="date":
3876:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3877:             else:
```
```text
3926:         def new_form():
3927:             self._editing_document_key=None
3928:             for z in v.values(): z.set("")
3929:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3930:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3931:             for iid in tree.get_children(): tree.delete(iid)
3932:             self._set_form_editable(form_roots, True, skip=[selector])
3933: 
3934:         def save():
3935:             try:
3936:                 no=v["no"].get().strip()
3937:                 if not no:raise ValueError("GRN No is required.")
3938:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3939:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3940:                 if dup and getattr(self,"_editing_document_key",None) != no:
3941:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3942:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3943:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3944:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3945:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3946:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3943:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3944:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3945:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3946:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3947:                 for x in self.grr_lines:
3948:                     ltype=x[10] if len(x)>10 else "Local"
3949:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3950:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3951:                 self.conn.commit()
3952:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
3953:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
3954:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3955:             except Exception as ex:messagebox.showerror("Error",str(ex))
3956:         form_roots=[f,line,editbar]
3957:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3958:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3959:         def delete_current():
3960:             no=v["no"].get().strip()
3961:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3962:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3963:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
3956:         form_roots=[f,line,editbar]
3957:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3958:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3959:         def delete_current():
3960:             no=v["no"].get().strip()
3961:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3962:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3963:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3964:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3965:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3966:         def cancel_form():
3967:             self._editing_document_key=None
3968:             self._set_form_editable(form_roots, False, skip=[selector])
3969:             for z in v.values(): z.set("")
3970:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3971:             itype.set("Local")
3972:             self.grr_lines.clear()
3973:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3974:             for iid in tree.get_children(): tree.delete(iid)
3975:         def preview_now():
3976:             if not self.grr_lines:
```
```text
3985:                     ("Challan #", v['challan'].get()),
3986:                     ("Vehicle #", v['vehicle'].get()),
3987:                     ("Bill/Voucher #", v['bill'].get()),
3988:                     ("Reference", v['ref'].get()),
3989:                     ("Remarks", v['remarks'].get()),
3990:                     ("Total Value", fmt_num(total))]
3991:             self.show_preview_window("GRN Receipt", header,
3992:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3993:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3994:         def portable_current():
3995:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3996:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3997:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3998:         self._portable_print_context=portable_current
3999:         def edit_saved_grr():
4000:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4001:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
4002:             self._set_form_editable(form_roots, True, skip=[selector])
4003:         def print_now():
4004:             if not self.grr_lines:
4005:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
4009:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
4010:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
4011:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
4012:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
4013:                     ("Total Value", fmt_num(total))]
4014:             self._open_direct_printer("GRN Receipt",header,
4015:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
4016:                 self.grr_lines,landscape(A4))
4017:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
4018:         self._add_transaction_new_button(new_form)
4019:         self._set_form_editable(form_roots, False, skip=[selector])
4020:         try:
4021:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
4022:         except Exception: pass
4023:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
4024: 
4025:     def load_grr_into_form(self,no,v,tree):
4026:         v["no"].set(no)
4027:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
4028:         if not r:return
4029:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
4036:         if roots and "grr" in roots:
4037:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
4038: 
4039:     def issue(self):
4040:         self.clearbody(); self.issue_lines=[]
4041:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
4042:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
4043:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
4044:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
4045:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
4046:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
4047:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
4048:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
4049:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
4050:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
4051:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
4052:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
4053:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
4054:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
4055:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
4056:         itype=tk.StringVar(value="Local")
```
```text
4125:                 # Editing an existing issue replaces its old stock transaction and detail lines.
4126:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
4127:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
4128:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
4129:                 for x in self.issue_lines:
4130:                     ltype=x[7] if len(x)>7 else "Local"
4131:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
4132:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
4133:                 self.conn.commit()
4134:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
4135:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
4136:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4137:             except Exception as ex:messagebox.showerror("Error",str(ex))
4138:         def delete_current():
4139:             no=v["no"].get().strip()
4140:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
4141:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
4142:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
4143:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
4144:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
4145:         def cancel_form():
```
```text
4153:             for iid in tree.get_children(): tree.delete(iid)
4154:         def preview_now():
4155:             if not self.issue_lines:
4156:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4157:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4158:                     f"Items Use For: {v['items_use_for'].get()}"]
4159:             self.show_preview_window("Material Issue", header,
4160:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4161:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4162:         def portable_current():
4163:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4164:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4165:         self._portable_print_context=portable_current
4166:         form_roots=[f,usebar,line,editbar]
4167:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4168:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4169:         def load_saved_issue(no):
4170:             self.load_issue_into_form(no,v,tree)
4171:             self._set_form_editable(form_roots, False, skip=[selector])
4172:         def edit_saved_issue():
4173:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4166:         form_roots=[f,usebar,line,editbar]
4167:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4168:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4169:         def load_saved_issue(no):
4170:             self.load_issue_into_form(no,v,tree)
4171:             self._set_form_editable(form_roots, False, skip=[selector])
4172:         def edit_saved_issue():
4173:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4174:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4175:             self._set_form_editable(form_roots, True, skip=[selector])
4176:         def print_issue_now():
4177:             if not self.issue_lines:
4178:                 messagebox.showwarning("Print","Add at least one item line first."); return
4179:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4180:             self._open_direct_printer("Material Issue",header,
4181:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4182:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4183:         self._add_transaction_new_button(new_form)
4184:         self._set_form_editable(form_roots, False, skip=[selector])
4185:         self._active_form_loader = load_saved_issue
4186: 
```
```text
4194:         for i in tree.get_children():tree.delete(i)
4195:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4196:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4197:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4198:         roots=getattr(self,"_transaction_form_roots",None)
4199:         if roots and "issue" in roots:
4200:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4201: 
4202:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4203:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4204: 
4205:         The layout intentionally matches Inventory Codes' Selection Criteria
4206:         popup so all Report sub-sections have one consistent desktop workflow.
4207:         """
4208:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4209:         win=tk.Toplevel(self)
4210:         win.title(f"{report_title} - Selection Criteria")
4211:         win.resizable(False,False)
4212:         win.transient(self); win.grab_set()
4213:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4214:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4259:             except Exception: pass
4260:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4261:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4262:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4263:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4264:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4265:         e1.focus_set(); self.wait_window(win); return result
4266: 
4267:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4268:         self._pending_report_filters=criteria
4269:         try:
4270:             return self.open_menu_window(method,title,geometry)
4271:         finally:
4272:             self._pending_report_filters=None
4273: 
4274:     def open_stock_balance_report_flow(self):
4275:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4276:         if f.get("cancelled"): return None
4277:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4278: 
4279:     def open_grr_report_flow(self):
```
```text
4272:             self._pending_report_filters=None
4273: 
4274:     def open_stock_balance_report_flow(self):
4275:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4276:         if f.get("cancelled"): return None
4277:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4278: 
4279:     def open_grr_report_flow(self):
4280:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4281:         if f.get("cancelled"): return None
4282:         return self._open_report_child(self.report_grr,"GRN Report",f)
4283: 
4284:     def open_demand_report_flow(self):
4285:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4286:         if f.get("cancelled"): return None
4287:         return self._open_report_child(self.report_demand,"Demand Report",f)
4288: 
4289:     def open_issue_report_flow(self):
4290:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4291:         if f.get("cancelled"): return None
4292:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4286:         if f.get("cancelled"): return None
4287:         return self._open_report_child(self.report_demand,"Demand Report",f)
4288: 
4289:     def open_issue_report_flow(self):
4290:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4291:         if f.get("cancelled"): return None
4292:         return self._open_report_child(self.report_issue,"Issue Report",f)
4293: 
4294:     def open_party_report_flow(self):
4295:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4296:         if f.get("cancelled"): return None
4297:         return self._open_report_child(self.report_party,"Party Report",f)
4298: 
4299:     def _ask_stock_balance_filters(self):
4300:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4301:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4302:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4303:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4304:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4305:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4306:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4318:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4319:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4320:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4321:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4322:         e1.focus_set();self.wait_window(win);return result
4323: 
4324:     def stock_balance(self):
4325:         self.clearbody()
4326:         # Stock Balance is a Report sub-section and does not use the generic
4327:         # Save/Edit/Delete/Cancel/Print action strip.
4328:         children=self.body.winfo_children()
4329:         if children:
4330:             children[0].destroy()
4331:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4332:         if initial.get("cancelled"):
4333:             self.dashboard(); return
4334:         top=ttk.Frame(self.body);top.pack(fill="x")
4335:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4336:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4337:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4338:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4348:             for typ,qty in self.conn.execute(q,params):
4349:                 if typ=="GRR":gr+=float(qty or 0)
4350:                 elif typ=="ISSUE":iss+=float(qty or 0)
4351:             return opening_before,gr,iss,opening_before+gr-iss
4352:         def header_summary():
4353:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4354:         def load():
4355:             for i in tr.get_children():tr.delete(i)
4356:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4357:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4358:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4359:             sql+=" ORDER BY code"
4360:             for r in self.conn.execute(sql,params):
4361:                 op,gr,iss,cur=period(r[0],r[3])
4362:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4363:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4364:         def reopen_filters():
4365:             initial2=self._ask_stock_balance_filters()
4366:             if initial2.get("cancelled"):return
4367:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4368:             load()
```
```text
4406:         """
4407:         if typ=="demand": self.demand()
4408:         elif typ=="grr": self.grr()
4409:         else: self.issue()
4410:         loader=getattr(self,"_active_form_loader",None)
4411:         if loader: loader(str(no))
4412: 
4413:     def _edit_from_selector(self, typ, var, loader):
4414:         """Top Edit action: load the saved document directly into the current form.
4415:         If nothing is selected, use the newest saved document; never open a popup.
4416:         """
4417:         text=var.get().strip()
4418:         if text:
4419:             no=text.split(" -> ",1)[0].strip()
4420:         else:
4421:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4422:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4423:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4424:             if not r:
4425:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4426:                 return
```
```text
4423:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4424:             if not r:
4425:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4426:                 return
4427:             no=str(r[0])
4428:             var.set(no)
4429:         loader(no)
4430: 
4431:     def show_saved_records(self,typ):
4432:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4433:         if typ=="demand":
4434:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4435:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4436:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4437:             for r in rows:
4438:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4439:                 r=list(r); r[1]=to_display_date(r[1])
4440:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4441:         elif typ=="grr":
4442:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4443:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4454:         def view():
4455:             a=tr.selection()
4456:             if not a:return
4457:             no=tr.item(a[0])["values"][0]
4458:             win.destroy();self.open_document_editor(typ,no)
4459:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4460:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4461:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4462:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4463: 
4464:     def documents(self):
4465:         self.clearbody()
4466:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4467:         specs=[
4468:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4469:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4470:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4471:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4472:             ("Material Issues","issue",("No","Date","Department"),
4473:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4474:         ]
```
```text
4470:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4471:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4472:             ("Material Issues","issue",("No","Date","Department"),
4473:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4474:         ]
4475:         for title,typ,cols,query in specs:
4476:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4477:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4478:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4479:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4480:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4481:             for r in self.conn.execute(query):
4482:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4483:             def edit_selected(t=tr,k=typ):
4484:                 a=t.selection()
4485:                 if not a:
4486:                     messagebox.showwarning("Edit", "Select a saved record first.")
4487:                     return
4488:                 no=t.item(a[0])["values"][0]
4489:                 self.open_document_editor(k,no)
4490:             def delete_selected(t=tr,k=typ):
```
```text
4485:                 if not a:
4486:                     messagebox.showwarning("Edit", "Select a saved record first.")
4487:                     return
4488:                 no=t.item(a[0])["values"][0]
4489:                 self.open_document_editor(k,no)
4490:             def delete_selected(t=tr,k=typ):
4491:                 a=t.selection()
4492:                 if not a:
4493:                     messagebox.showwarning("Delete", "Select a saved record first.")
4494:                     return
4495:                 no=t.item(a[0])["values"][0]
4496:                 if k=="demand":
4497:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4498:                 elif k=="grr":
4499:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4500:                 else:
4501:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4502:                 self.conn.commit();backup_database();self.documents()
4503:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4504:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4505:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4499:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4500:                 else:
4501:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4502:                 self.conn.commit();backup_database();self.documents()
4503:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4504:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4505:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4506:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4507:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4508:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4509:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4510: 
4511:     def doc_export_selected(self,typ,tr,fmt):
4512:         a=tr.selection()
4513:         if not a:
4514:             messagebox.showwarning("Export","Select a saved record first."); return
4515:         no=tr.item(a[0])["values"][0]
4516:         if fmt=="word": self.export_word(typ,no)
4517:         else: self.export_excel(typ,no)
4518: 
4519:     def doc_preview_selected(self,typ,tr):
```
```text
4514:             messagebox.showwarning("Export","Select a saved record first."); return
4515:         no=tr.item(a[0])["values"][0]
4516:         if fmt=="word": self.export_word(typ,no)
4517:         else: self.export_excel(typ,no)
4518: 
4519:     def doc_preview_selected(self,typ,tr):
4520:         a=tr.selection()
4521:         if not a:
4522:             messagebox.showwarning("Preview","Select a saved record first."); return
4523:         no=tr.item(a[0])["values"][0]
4524:         data=self._get_doc_data(typ,no)
4525:         if not data:
4526:             messagebox.showwarning("Preview","Document not found."); return
4527:         title,header,cols,rows=data
4528:         header_lines=header
4529:         self.show_preview_window(title,header_lines,cols,rows)
4530: 
4531:     def doc_print_selected(self,typ,tr):
4532:         a=tr.selection()
4533:         if not a: return
4534:         no=tr.item(a[0])["values"][0]
```
```text
4565:         def _print_loaded_document():
4566:             data=self._get_doc_data(typ,no)
4567:             if not data:
4568:                 messagebox.showwarning("Document","Document not found."); return
4569:             title,header,cols,rows=data
4570:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4571:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4572: 
4573:     def _report_filter_popup(self, title, include_party=False):
4574:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4575:         win,winbody=self._internal_window(title,"520x420")
4576:         done=tk.BooleanVar(value=False)
4577:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4578:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4579:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4580:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4581:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4582:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4583:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4584:         if include_party:
4585:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4579:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4580:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4581:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4582:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4583:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4584:         if include_party:
4585:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4586:         def ok():
4587:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4588:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4589:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4590:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4591: 
4592:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4593:         self.clearbody()
4594:         # Report sub-sections use their own report toolbar; remove only the
4595:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4596:         children=self.body.winfo_children()
4597:         if children:
4598:             children[0].destroy()
4599:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4600:         if f.get("cancelled"):
4601:             self.dashboard();return
4602:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4603:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4604:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4605:         def load():
4606:             for i in tr.get_children():tr.delete(i)
4607:             params,where=params_builder(f)
4608:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4609:             for r in self.conn.execute(sql,params):
4610:                 vals=list(r)
4611:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4612:                 tr.insert("","end",values=vals)
4613:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4614:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4615:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4616:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4617:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4618:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4619:         def open_find_report():
4620:             state_find={"index":-1}
```
```text
4626:                 order=children[start:]+children[:start]
4627:                 for iid in order:
4628:                     vals=tr.item(iid,"values")
4629:                     if any(text in str(v).lower() for v in vals):
4630:                         state_find["index"]=children.index(iid)
4631:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4632:                 return False
4633:             self._open_exact_find_text_popup(search_fn)
4634:         self._item_master_find_callback=open_find_report
4635:         load()
4636:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4637: 
4638:     def report_grr(self):
4639:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4640:         def pb(f):
4641:             w=[];p=[]
4642:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4643:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4644:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4645:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4646:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4641:             w=[];p=[]
4642:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4643:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4644:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4645:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4646:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4647:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4648:             return p,w
4649:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4650: 
4651:     def report_demand(self):
4652:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4653:         def pb(f):
4654:             w=[];p=[]
4655:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4656:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4657:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4658:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4659:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4660:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4661:             return p,w
```
```text
4654:             w=[];p=[]
4655:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4656:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4657:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4658:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4659:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4660:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4661:             return p,w
4662:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4663: 
4664:     def report_issue(self):
4665:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4666:         def pb(f):
4667:             w=[];p=[]
4668:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4669:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4670:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4671:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4672:             return p,w
4673:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4674: 
```
```text
4667:             w=[];p=[]
4668:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4669:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4670:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4671:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4672:             return p,w
4673:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4674: 
4675:     def report_party(self):
4676:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4677:         def pb(f):
4678:             w=[];p=[]
4679:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4680:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4681:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4682:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4683:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4684:             return p,w
4685:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4686: 
4687:     def reports(self):
```
```text
4685:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4686: 
4687:     def reports(self):
4688:         self.clearbody()
4689:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4690: 
4691:         # ================= GRN Details =================
4692:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4693:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4694:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4695:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4696:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4697:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4698: 
4699:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4700:         def load_grr_item(codev=None):
4701:             for i in tr.get_children(): tr.delete(i)
4702:             q=codev.get().strip() if codev else ""
4703:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4704:             for r in self.conn.execute(sql,(q,) if q else ()):
4705:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4711:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4712:         tr=self.make_tree(fr,grr_cols,grr_widths)
4713:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4714:             for i in tr.get_children(): tr.delete(i)
4715:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4716:             conds=[];params=[]
4717:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4718:             if td: conds.append("g.grr_date<=?");params.append(td)
4719:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4720:             for r in self.conn.execute(sql,params):
4721:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4722:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4723:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4724:         load_grr_date(fdv,tdv)
4725: 
4726:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4727:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4728:         party=tk.StringVar(value="ALL")
4729:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4730:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4731:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4727:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4728:         party=tk.StringVar(value="ALL")
4729:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4730:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4731:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4732:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4733:         def load_party(*_):
4734:             for i in tr.get_children(): tr.delete(i)
4735:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4736:             if party.get()=="ALL":
4737:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4738:             else:
4739:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4740:             for r in rows:
4741:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4742:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4743:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4744: 
4745:         # ================= Demand Details =================
4746:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4747:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4743:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4744: 
4745:         # ================= Demand Details =================
4746:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4747:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4748:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4749:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4750:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4751:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4752: 
4753:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4754:         def load_dem_item(codev=None):
4755:             for i in tr.get_children(): tr.delete(i)
4756:             q=codev.get().strip() if codev else ""
4757:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4758:             for r in self.conn.execute(sql,(q,) if q else ()):
4759:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4760:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4761:         tr=self.make_tree(fr,dem_cols,dem_widths)
4762:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4763:         load_dem_item(codev)
```
```text
4765:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4766:         tr=self.make_tree(fr,dem_cols,dem_widths)
4767:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4768:             for i in tr.get_children(): tr.delete(i)
4769:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4770:             conds=[];params=[]
4771:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4772:             if td: conds.append("d.demand_date<=?");params.append(td)
4773:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4774:             for r in self.conn.execute(sql,params):
4775:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4776:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4777:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4778:         load_dem_date(fdv,tdv)
4779: 
4780:         # ================= Material Issue Details =================
4781:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4782:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4783:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4784:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4785:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4778:         load_dem_date(fdv,tdv)
4779: 
4780:         # ================= Material Issue Details =================
4781:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4782:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4783:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4784:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4785:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4786:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4787: 
4788:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4789:         def load_iss_item(codev=None):
4790:             for i in tr.get_children(): tr.delete(i)
4791:             q=codev.get().strip() if codev else ""
4792:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4793:             for r in self.conn.execute(sql,(q,) if q else ()):
4794:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4795:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4796:         tr=self.make_tree(fr,iss_cols,iss_widths)
4797:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4798:         load_iss_item(codev)
```
```text
4800:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4801:         tr=self.make_tree(fr,iss_cols,iss_widths)
4802:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4803:             for i in tr.get_children(): tr.delete(i)
4804:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4805:             conds=[];params=[]
4806:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4807:             if td: conds.append("i.issue_date<=?");params.append(td)
4808:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4809:             for r in self.conn.execute(sql,params):
4810:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4811:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4812:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4813:         load_iss_date(fdv,tdv)
4814: 
4815:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4816: 
4817:     def print_item_master(self):
4818:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4819:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4820: 
```
```text
4817:     def print_item_master(self):
4818:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4819:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4820: 
4821:     def print_party_master(self):
4822:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4823:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4824: 
4825:     def print_report(self,kind):
4826:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4827:         if kind=="grr":
4828:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4829:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4830:         elif kind=="demand":
4831:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4832:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4833:         elif kind=="issue":
4834:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4835:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4836:         else:
4837:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4838:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4839:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4840: 
4841:     def print_stock(self):
4842:         rows=[]
4843:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4844:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4845:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4846:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4847: 
4848:     def print_ledger(self):
4849:         rows=[]
4850:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4851:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4852:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4853:                 running += x[3] if x[1]=="GRR" else -x[3]
4854:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4855:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4856: 
4857:     def _get_doc_data(self, typ, no):
4858:         """Header + line items for one saved document, used by the on-screen
```
```text
4924:             sig=doc.add_table(rows=2,cols=3)
4925:             labels=["Prepared By","Store Keeper","Store Incharge"]
4926:             for i,label in enumerate(labels):
4927:                 sig.cell(0,i).text="____________________"
4928:                 sig.cell(1,i).text=label
4929:                 for para in sig.cell(1,i).paragraphs:
4930:                     for run in para.runs: run.bold=True
4931:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4932:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4933:         doc.save(path)
4934:         self.open_file(path)
4935: 
4936:     def export_excel(self, typ, no):
4937:         if not no or not no.strip():
4938:             return messagebox.showwarning("Excel Export","Select a document first.")
4939:         if not XLSX_AVAILABLE:
4940:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4941:         data=self._get_doc_data(typ,no)
4942:         if not data:
4943:             return messagebox.showwarning("Excel Export","Document not found.")
4944:         title,header,cols,rows=data
```
```text
4966:             for col in range(1,4):
4967:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4968:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4969:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4970:         for col_cells in ws.columns:
4971:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4972:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4973:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4974:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4975:         wb.save(path)
4976:         self.open_file(path)
4977: 
4978:     def preview_pdf(self,typ,no):
4979:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4980:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4981:         data=self._get_doc_data(typ,no)
4982:         if not data:return messagebox.showwarning("Document","Document not found.")
4983:         title,header,cols,rows=data
4984:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4985:         page_size = landscape(A4) if typ == "grr" else A4
4986:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4981:         data=self._get_doc_data(typ,no)
4982:         if not data:return messagebox.showwarning("Document","Document not found.")
4983:         title,header,cols,rows=data
4984:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4985:         page_size = landscape(A4) if typ == "grr" else A4
4986:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4987: 
4988:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4989:         """Open the print dialog with a real visual preview of the exact report.
4990: 
4991:         The report is rendered to a temporary PDF only in memory/on disk for the
4992:         duration of printing.  It is deleted after the print dialog closes, so
4993:         the Print button does not leave a PDF report behind.  Printing uses the
4994:         rendered report page itself rather than rebuilding rows as plain text;
4995:         this keeps the printed page identical to the application's report.
4996:         """
4997:         # Printing is always prepared as an A4 landscape page. This only affects
4998:         # the print path; the rest of the application's UI/report logic is unchanged.
4999:         page_size = landscape(A4)
5000:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
5001:             messagebox.showwarning(
```
```text
5003:                 "The print preview/printing components are not available.\n\n"
5004:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
5005:             )
5006:             return
5007:         if not rows and not columns:
5008:             messagebox.showwarning("Print", "There is no data to print.")
5009:             return
5010:         try:
5011:             os.makedirs(REPORTS_DIR, exist_ok=True)
5012:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
5013:             self._pdf_table_report(key,title,columns,rows,page_size,
5014:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
5015:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
5016:             self._select_windows_printer_for_pdf(key)
5017:         except Exception as e:
5018:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
5019: 
5020:     def _select_windows_printer_for_pdf(self, path):
5021:         """Print dialog with an actual page preview, printer selection and direct GDI output.
5022: 
5023:         The preview is rendered from the exact PDF produced by the application,
```
```text
5053:         job=getattr(self, "_print_jobs", {}).get(path)
5054:         if job:
5055:             title, header_lines, columns, rows, source_page_size = job
5056:         else:
5057:             title=os.path.splitext(os.path.basename(path))[0]
5058:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
5059: 
5060:         try:
5061:             doc=fitz.open(path)
5062:             total_pages=max(1,doc.page_count)
5063:         except Exception as e:
5064:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
5065:             return
5066: 
5067:         win=tk.Toplevel(self)
5068:         win.title("Printing from Win32 application - Print")
5069:         win.geometry("900x620")
5070:         win.minsize(850,580)
5071:         win.transient(self)
5072:         win.configure(bg="#f0f0f0")
5073: 
```
```text
5079:             pass
5080: 
5081:         outer=tk.Frame(win,bg="#f0f0f0")
5082:         outer.pack(fill="both",expand=True)
5083:         outer.columnconfigure(1,weight=1)
5084:         outer.rowconfigure(0,weight=1)
5085: 
5086:         # Left side mirrors the familiar system printer dialog: printers and
5087:         # print options. Right side contains the actual report page preview.
5088:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
5089:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
5090:         left.grid_propagate(False)
5091:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
5092:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
5093:         printer_list.pack(fill="x")
5094:         for pr in printers: printer_list.insert("end",pr)
5095:         try: printer_list.selection_set(printers.index(default_printer))
5096:         except Exception: printer_list.selection_set(0)
5097: 
5098:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
5099:         copies=tk.IntVar(value=1)
```
```text
5172:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5173: 
5174:         bottom=tk.Frame(win,bg="#f0f0f0")
5175:         # `outer` already uses pack() in `win`; using grid() for another direct
5176:         # child of the same toplevel raises TclError. Keep the action bar in the
5177:         # same geometry-manager family so Print/Cancel are always visible.
5178:         bottom.pack(fill="x",padx=12,pady=(0,12))
5179:         bottom.columnconfigure(0,weight=1)
5180:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5181:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5182:         print_btn=ttk.Button(bottom,text="Print",width=12)
5183:         print_btn.grid(row=0,column=2,padx=(8,0))
5184: 
5185:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5186: 
5187:         def parse_page_selection(total):
5188:             if pages_mode.get()=="All pages": return list(range(total))
5189:             raw=page_range.get().strip()
5190:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5191:             selected=[]
5192:             for part in raw.split(","):
```
```text
5189:             raw=page_range.get().strip()
5190:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5191:             selected=[]
5192:             for part in raw.split(","):
5193:                 part=part.strip()
5194:                 if "-" in part:
5195:                     a,b=part.split("-",1); a=int(a); b=int(b)
5196:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5197:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5198:                     selected.extend(range(a-1,b))
5199:                 else:
5200:                     n=int(part)
5201:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5202:                     selected.append(n-1)
5203:             return list(dict.fromkeys(selected))
5204: 
5205:         def selected_printer():
5206:             sel=printer_list.curselection()
5207:             return printer_list.get(sel[0]) if sel else printers[0]
5208: 
5209:         def print_rendered_pages():
```
```text
5302:                 finally:
5303:                     if hprinter is not None:
5304:                         try: win32print.ClosePrinter(hprinter)
5305:                         except Exception: pass
5306:                     if hdc:
5307:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5308:                         except Exception: pass
5309: 
5310:                 # Print the exact rendered PDF page through the printer DC.
5311:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5312:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5313:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5314:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5315: 
5316:                 for copy_no in range(count):
5317:                     dc.StartDoc(str(title)[:80])
5318:                     doc_ok=False
5319:                     try:
5320:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5321:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5322:                             dc.StartPage()
```
```text
5321:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5322:                             dc.StartPage()
5323:                             page_ok=False
5324:                             try:
5325:                                 cell_w=printable_w/float(cols_n)
5326:                                 cell_h=printable_h/float(rows_n)
5327:                                 for j,page_index in enumerate(batch):
5328:                                     page=doc.load_page(page_index)
5329:                                     pdf_w=max(1.0,float(page.rect.width))
5330:                                     pdf_h=max(1.0,float(page.rect.height))
5331:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5332:                                     fit=max(0.25,min(fit,8.0))
5333:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5334:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5335:                                     target_w=max(1,int(cell_w*0.96))
5336:                                     target_h=max(1,int(cell_h*0.96))
5337:                                     ratio=min(target_w/img.width,target_h/img.height)
5338:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5339:                                     if (nw,nh)!=(img.width,img.height):
5340:                                         img=img.resize((nw,nh),Image.LANCZOS)
5341:                                     dib=ImageWin.Dib(img)
```
```text
5361: 
5362:                 status.set("Print job sent successfully")
5363:                 win.update_idletasks()
5364:                 win.after(500,close)
5365:             except Exception as e:
5366:                 status.set("Print failed: "+str(e))
5367:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5368: 
5369:         def close():
5370:             try: doc.close()
5371:             except Exception: pass
5372:             try: win.destroy()
5373:             except Exception: pass
5374:             # Only the temporary PDF created by the Print button is removed.
5375:             # Existing report PDFs passed through the legacy print path are preserved.
5376:             try:
5377:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5378:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5379:             except Exception: pass
5380: 
5381:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5377:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5378:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5379:             except Exception: pass
5380: 
5381:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5382:         bottom.winfo_children()[1].configure(command=close)
5383:         print_btn.configure(command=print_rendered_pages)
5384:         win.protocol("WM_DELETE_WINDOW",close)
5385:         win.bind("<Escape>",lambda e:close())
5386:         win.grab_set()
5387:         # Keep the requested printer defaults visibly selected; no manual
5388:         # adjustment is required before pressing Print.
5389:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5390:         win.after(120,lambda:render_preview(0))
5391:         win.focus_force()
5392: 
5393:     def print_pdf(self,path):
5394:         """Open a printer-selection window for a generated PDF."""
5395:         path=os.path.abspath(path)
5396:         if not os.path.exists(path):
5397:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5393:     def print_pdf(self,path):
5394:         """Open a printer-selection window for a generated PDF."""
5395:         path=os.path.abspath(path)
5396:         if not os.path.exists(path):
5397:             messagebox.showwarning("Print", "The report file could not be found.")
5398:             return
5399: 
5400:         if sys.platform.startswith("win"):
5401:             self._select_windows_printer_for_pdf(path)
5402:             return
5403: 
5404:         try:
5405:             subprocess.run(["lp", path], check=True)
5406:         except Exception as e:
5407:             messagebox.showwarning(
5408:                 "Print",
5409:                 "The operating system could not start printing.\n\n"
5410:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5411:             )
5412: 
5413:     def open_file(self,path):
```
```text
5408:                 "Print",
5409:                 "The operating system could not start printing.\n\n"
5410:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5411:             )
5412: 
5413:     def open_file(self,path):
5414:         try:
5415:             if sys.platform.startswith("win"): os.startfile(path)
5416:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5417:             else: subprocess.Popen(["xdg-open",path])
5418:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5419: 
5420:     def print_demand(self,no):
5421:         data=self._get_doc_data("demand",no)
5422:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5423:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5424:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5425:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5426: 
5427:     def print_grr(self,no):
5428:         data=self._get_doc_data("grr",no)
```
```text
5422:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5423:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5424:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5425:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5426: 
5427:     def print_grr(self,no):
5428:         data=self._get_doc_data("grr",no)
5429:         if not data:return messagebox.showwarning("Document","GRN not found.")
5430:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5431:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5432:         # GRN has a wide item table. Generate the PDF itself in landscape so
5433:         # the printer dialog and printer driver receive a landscape document
5434:         # instead of a portrait page with rotated/cropped content.
5435:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5436: 
5437:     def print_issue(self,no):
5438:         data=self._get_doc_data("issue",no)
5439:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5440:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5441:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5442:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
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
