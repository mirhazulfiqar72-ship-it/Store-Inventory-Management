# Store Inventory source audit

Generated from `D:\a\Store-Inventory-Management\Store-Inventory-Management\source` after CI patches.

## durable_local.py

- Lines: 113
- Functions: _columns(26-27), snapshot(29-39), _row_count(41-42), save(44-66), load(68-77), restore_if_newer(79-113)

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
0014: from pathlib import Path
0015: from typing import Any, Dict
```
```text
0018: DATA_DIR = INSTALL_ROOT / "Data"
0019: SNAPSHOT_PATH = DATA_DIR / "local_data_snapshot.json"
0020: TABLES = (
0021:     "items", "mto_items", "parties", "demands", "demand_lines", "grr", "grr_lines",
0022:     "issues", "issue_lines", "transactions", "users",
0023: )
0024: LAST_ERROR = ""
0025: 
0026: def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
0027:     return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
0028: 
0029: def snapshot(conn: sqlite3.Connection) -> Dict[str, Any]:
0030:     tables: Dict[str, Any] = {}
0031:     for table in TABLES:
0032:         cols = _columns(conn, table)
0033:         rows = []
0034:         if cols:
0035:             for row in conn.execute(f"SELECT {','.join(cols)} FROM {table}").fetchall():
0036:                 rows.append({c: (v if v is None or isinstance(v, (str, int, float, bool)) else str(v))
0037:                              for c, v in zip(cols, row)})
0038:         tables[table] = {"columns": cols, "rows": rows}
```
```text
0036:                 rows.append({c: (v if v is None or isinstance(v, (str, int, float, bool)) else str(v))
0037:                              for c, v in zip(cols, row)})
0038:         tables[table] = {"columns": cols, "rows": rows}
0039:     return {"schema": 1, "tables": tables}
0040: 
0041: def _row_count(s: Dict[str, Any]) -> int:
0042:     return sum(len(v.get("rows", []) or []) for v in s.get("tables", {}).values())
0043: 
0044: def save(conn: sqlite3.Connection) -> bool:
0045:     global LAST_ERROR
0046:     LAST_ERROR = ""
0047:     try:
0048:         DATA_DIR.mkdir(parents=True, exist_ok=True)
0049:         value = snapshot(conn)
0050:         fd, tmp = tempfile.mkstemp(prefix="local_snapshot_", suffix=".tmp", dir=str(DATA_DIR))
0051:         try:
0052:             with os.fdopen(fd, "w", encoding="utf-8") as f:
0053:                 json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
0054:                 f.flush()
0055:                 os.fsync(f.fileno())
0056:             os.replace(tmp, SNAPSHOT_PATH)
```
```text
0071:         if not SNAPSHOT_PATH.exists():
0072:             return None
0073:         value = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
0074:         return value if isinstance(value, dict) else None
0075:     except Exception as exc:
0076:         LAST_ERROR = repr(exc)
0077:         return None
0078: 
0079: def restore_if_newer(conn: sqlite3.Connection) -> bool:
0080:     global LAST_ERROR
0081:     LAST_ERROR = ""
0082:     saved = load()
0083:     if not saved or _row_count(saved) <= 0:
0084:         return False
0085:     current = snapshot(conn)
0086:     if _row_count(current) >= _row_count(saved):
0087:         return False
0088:     try:
0089:         conn.execute("BEGIN")
0090:         for table in TABLES:
0091:             cols = _columns(conn, table)
```
```text
0084:         return False
0085:     current = snapshot(conn)
0086:     if _row_count(current) >= _row_count(saved):
0087:         return False
0088:     try:
0089:         conn.execute("BEGIN")
0090:         for table in TABLES:
0091:             cols = _columns(conn, table)
0092:             rows = saved.get("tables", {}).get(table, {}).get("rows", []) or []
0093:             if not cols:
0094:                 continue
0095:             conn.execute(f"DELETE FROM {table}")
0096:             if not rows:
0097:                 continue
0098:             insert_cols = [c for c in cols if c in rows[0]]
0099:             if not insert_cols:
0100:                 continue
0101:             placeholders = ",".join("?" for _ in insert_cols)
0102:             sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0103:             for row in rows:
0104:                 conn.execute(sql, [row.get(c) for c in insert_cols])
```
```text
0097:                 continue
0098:             insert_cols = [c for c in cols if c in rows[0]]
0099:             if not insert_cols:
0100:                 continue
0101:             placeholders = ",".join("?" for _ in insert_cols)
0102:             sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0103:             for row in rows:
0104:                 conn.execute(sql, [row.get(c) for c in insert_cols])
0105:         conn.commit()
0106:         return True
0107:     except Exception as exc:
0108:         LAST_ERROR = repr(exc)
0109:         try:
0110:             conn.rollback()
0111:         except Exception:
0112:             pass
0113:         return False
```

## firebase_sync.py

- Lines: 379
- Functions: _safe_json_value(25-28), _table_columns(29-30), snapshot_db(31-39), _row_key(40-44), _index_snapshot(45-49), merge_local_changes(50-71), _snapshot_has_records(72-74), __init__(76-92), _read_url(93-103), status_text(104-109), _request(110-119), _get_meta(120-126), _get_snapshot(127-133), _load_json(134-142), _atomic_save_json(143-157), _save_state(158-162), _save_pending(163-167), _clear_pending(168-173), _get_lock_etag(174-183), _try_acquire_lock(184-190), _release_lock(191-199), initialize(200-255), replace_local(256-273), _write_remote(274-295), push_changes(296-315), maybe_pull(316-337), __init__(339-344), execute(345-353), executemany(354-358), commit(359-368), rollback(370-373), close(374-375), backup(376-377), __getattr__(378-379)

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
0011: import durable_local
0012: import tempfile
0013: import time
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
0076:     def __init__(self, url_file: str, install_dir: str, timeout: int = 15):
0077:         self.url_file = url_file
0078:         self.install_dir = install_dir
0079:         self.timeout = timeout
0080:         self.base_url = self._read_url()
0081:         self.enabled = bool(self.base_url and requests)
0082:         self.last_remote_version: Optional[str] = None
0083:         self.last_check = 0.0
0084:         self.check_interval = 1.5
0085:         self.pending_base: Optional[Dict[str, Any]] = None
0086:         self.pending_error: Optional[str] = None
0087:         self.session = requests.Session() if requests else None
```
```text
0083:         self.last_check = 0.0
0084:         self.check_interval = 1.5
0085:         self.pending_base: Optional[Dict[str, Any]] = None
0086:         self.pending_error: Optional[str] = None
0087:         self.session = requests.Session() if requests else None
0088:         self.client_id = f"{os.environ.get('COMPUTERNAME','PC')}-{uuid.uuid4().hex[:10]}"
0089:         data_dir = os.path.join(self.install_dir, "Data")
0090:         os.makedirs(data_dir, exist_ok=True)
0091:         self.state_path = os.path.join(data_dir, "firebase_sync_state.json")
0092:         self.pending_path = os.path.join(data_dir, "firebase_pending_sync.json")
0093:     def _read_url(self) -> str:
0094:         try:
0095:             with open(self.url_file, "r", encoding="utf-8-sig") as f:
0096:                 raw = f.read().strip().splitlines()
0097:         except Exception:
0098:             return ""
0099:         for line in raw:
0100:             line = line.strip()
0101:             if line and not line.startswith("#"):
0102:                 return line.rstrip("/")
0103:         return ""
```
```text
0098:             return ""
0099:         for line in raw:
0100:             line = line.strip()
0101:             if line and not line.startswith("#"):
0102:                 return line.rstrip("/")
0103:         return ""
0104:     def status_text(self) -> str:
0105:         if not self.enabled:
0106:             return "Firebase URL not configured"
0107:         if self.pending_error:
0108:             return "Online database sync pending"
0109:         return "Online database connected"
0110:     def _request(self, method: str, path: str, **kwargs):
0111:         if not self.enabled or not self.session:
0112:             raise RuntimeError("Firebase URL is not configured or requests is unavailable.")
0113:         url = f"{self.base_url}/{path.lstrip('/')}"
0114:         if not url.endswith(".json"):
0115:             url += ".json"
0116:         r = self.session.request(method, url, timeout=self.timeout, **kwargs)
0117:         if not r.ok:
0118:             raise RuntimeError(f"Firebase HTTP {r.status_code}: {r.text[:500]}")
```
```text
0124:         except Exception:
0125:             data = None
0126:         return (data.get("version"), data) if isinstance(data, dict) else (None, None)
0127:     def _get_snapshot(self) -> Optional[Dict[str, Any]]:
0128:         r = self._request("GET", "store_inventory/data.json")
0129:         try:
0130:             data = r.json()
0131:         except Exception as exc:
0132:             raise RuntimeError(f"Invalid Firebase data response: {exc}")
0133:         return data if isinstance(data, dict) else None
0134:     def _load_json(self, path: str) -> Optional[Dict[str, Any]]:
0135:         try:
0136:             if not os.path.exists(path):
0137:                 return None
0138:             with open(path, "r", encoding="utf-8") as f:
0139:                 value = json.load(f)
0140:             return value if isinstance(value, dict) else None
0141:         except Exception:
0142:             return None
0143:     def _atomic_save_json(self, path: str, value: Dict[str, Any]) -> None:
0144:         os.makedirs(os.path.dirname(path), exist_ok=True)
```
```text
0137:                 return None
0138:             with open(path, "r", encoding="utf-8") as f:
0139:                 value = json.load(f)
0140:             return value if isinstance(value, dict) else None
0141:         except Exception:
0142:             return None
0143:     def _atomic_save_json(self, path: str, value: Dict[str, Any]) -> None:
0144:         os.makedirs(os.path.dirname(path), exist_ok=True)
0145:         fd, tmp = tempfile.mkstemp(prefix="firebase_sync_", suffix=".tmp", dir=os.path.dirname(path))
0146:         try:
0147:             with os.fdopen(fd, "w", encoding="utf-8") as f:
0148:                 json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
0149:                 f.flush()
0150:                 os.fsync(f.fileno())
0151:             os.replace(tmp, path)
0152:         finally:
0153:             try:
0154:                 if os.path.exists(tmp):
0155:                     os.remove(tmp)
0156:             except OSError:
0157:                 pass
```
```text
0150:                 os.fsync(f.fileno())
0151:             os.replace(tmp, path)
0152:         finally:
0153:             try:
0154:                 if os.path.exists(tmp):
0155:                     os.remove(tmp)
0156:             except OSError:
0157:                 pass
0158:     def _save_state(self, snapshot: Dict[str, Any]) -> None:
0159:         try:
0160:             self._atomic_save_json(self.state_path, snapshot)
0161:         except Exception:
0162:             pass
0163:     def _save_pending(self, snapshot: Dict[str, Any], baseline: Dict[str, Any]) -> None:
0164:         try:
0165:             self._atomic_save_json(self.pending_path, {"snapshot": snapshot, "baseline": baseline, "saved_at": time.time()})
0166:         except Exception:
0167:             pass
0168:     def _clear_pending(self) -> None:
0169:         try:
0170:             if os.path.exists(self.pending_path):
```
```text
0168:     def _clear_pending(self) -> None:
0169:         try:
0170:             if os.path.exists(self.pending_path):
0171:                 os.remove(self.pending_path)
0172:         except OSError:
0173:             pass
0174:     def _get_lock_etag(self) -> tuple[Any, str]:
0175:         url = f"{self.base_url}/store_inventory/_lock.json"
0176:         r = self.session.get(url, headers={"X-Firebase-ETag": "true"}, timeout=self.timeout)
0177:         if not r.ok:
0178:             raise RuntimeError(f"Firebase lock GET HTTP {r.status_code}: {r.text[:300]}")
0179:         try:
0180:             value = r.json()
0181:         except Exception:
0182:             value = None
0183:         return value, r.headers.get("ETag", "null_etag")
0184:     def _try_acquire_lock(self, token: str) -> bool:
0185:         value, etag = self._get_lock_etag()
0186:         if value not in (None, ""):
0187:             return False
0188:         url = f"{self.base_url}/store_inventory/_lock.json"
```
```text
0192:         try:
0193:             value, etag = self._get_lock_etag()
0194:             if value != token:
0195:                 return
0196:             url = f"{self.base_url}/store_inventory/_lock.json"
0197:             self.session.put(url, data="null", headers={"if-match": etag, "content-type": "application/json"}, timeout=self.timeout)
0198:         except Exception:
0199:             pass
0200:     def initialize(self, conn: sqlite3.Connection) -> None:
0201:         if not self.enabled:
0202:             return
0203:         local = snapshot_db(conn)
0204:         pending = self._load_json(self.pending_path)
0205:         state = self._load_json(self.state_path)
0206:         if isinstance(pending, dict) and isinstance(pending.get("snapshot"), dict):
0207:             local = pending["snapshot"]
0208:             self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
0209:         elif state:
0210:             self.pending_base = state
0211:         try:
0212:             remote = self._get_snapshot()
```
```text
0213:             version, _ = self._get_meta()
0214:             if remote and remote.get("tables"):
0215:                 if self.pending_base is not None:
0216:                     merged = merge_local_changes(remote, self.pending_base, local)
0217:                     if merged != remote:
0218:                         new_version = self._write_remote(merged)
0219:                         self.replace_local(conn, merged)
0220:                         self.last_remote_version = new_version
0221:                         self._save_state(merged)
0222:                         self._clear_pending()
0223:                     else:
0224:                         self.replace_local(conn, remote)
0225:                         self.last_remote_version = version
0226:                         self._save_state(remote)
0227:                         self._clear_pending()
0228:                 elif _snapshot_has_records(local):
0229:                     empty = {"schema": 1, "tables": {}}
0230:                     merged = merge_local_changes(remote, empty, local)
0231:                     if merged != remote:
0232:                         new_version = self._write_remote(merged)
0233:                         self.replace_local(conn, merged)
```
```text
0227:                         self._clear_pending()
0228:                 elif _snapshot_has_records(local):
0229:                     empty = {"schema": 1, "tables": {}}
0230:                     merged = merge_local_changes(remote, empty, local)
0231:                     if merged != remote:
0232:                         new_version = self._write_remote(merged)
0233:                         self.replace_local(conn, merged)
0234:                         self.last_remote_version = new_version
0235:                         self._save_state(merged)
0236:                     else:
0237:                         self.replace_local(conn, remote)
0238:                         self.last_remote_version = version
0239:                         self._save_state(remote)
0240:                 else:
0241:                     self.replace_local(conn, remote)
0242:                     self.last_remote_version = version
0243:                     self._save_state(remote)
0244:                 self.pending_base = None
0245:                 self.pending_error = None
0246:             else:
0247:                 new_version = self._write_remote(local)
```
```text
0241:                     self.replace_local(conn, remote)
0242:                     self.last_remote_version = version
0243:                     self._save_state(remote)
0244:                 self.pending_base = None
0245:                 self.pending_error = None
0246:             else:
0247:                 new_version = self._write_remote(local)
0248:                 self.last_remote_version = new_version
0249:                 self._save_state(local)
0250:                 self._clear_pending()
0251:                 self.pending_base = None
0252:                 self.pending_error = None
0253:         except Exception as exc:
0254:             self.pending_error = str(exc)
0255:             self._save_pending(local, self.pending_base or state or {"schema": 1, "tables": {}})
0256:     def replace_local(self, conn: sqlite3.Connection, snapshot: Dict[str, Any]) -> None:
0257:         old_isolation = conn.isolation_level
0258:         try:
0259:             conn.execute("BEGIN")
0260:             for table in TABLES:
0261:                 cols = _table_columns(conn, table)
```
```text
0260:             for table in TABLES:
0261:                 cols = _table_columns(conn, table)
0262:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0263:                 conn.execute(f"DELETE FROM {table}")
0264:                 if not rows:
0265:                     continue
0266:                 insert_cols = [c for c in cols if c in rows[0]]
0267:                 placeholders = ",".join("?" for _ in insert_cols)
0268:                 sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0269:                 for row in rows:
0270:                     conn.execute(sql, [row.get(c) for c in insert_cols])
0271:             conn.commit()
0272:         finally:
0273:             conn.isolation_level = old_isolation
0274:     def _write_remote(self, snapshot: Dict[str, Any]) -> str:
0275:         token = f"{self.client_id}-{uuid.uuid4().hex}"
0276:         acquired = False
0277:         last_exc = None
0278:         for _ in range(10):
0279:             try:
0280:                 if self._try_acquire_lock(token):
```
```text
0279:             try:
0280:                 if self._try_acquire_lock(token):
0281:                     acquired = True
0282:                     break
0283:             except Exception as exc:
0284:                 last_exc = exc
0285:             time.sleep(0.35)
0286:         if not acquired:
0287:             raise RuntimeError(f"Could not acquire Firebase sync lock. {last_exc or ''}".strip())
0288:         try:
0289:             new_version = f"{time.time_ns()}-{self.client_id}"
0290:             self._request("PUT", "store_inventory/data.json", json=snapshot)
0291:             self._request("PUT", "store_inventory/_meta/version.json", json=new_version)
0292:             self._request("PUT", "store_inventory/_meta/updated_by.json", json=self.client_id)
0293:             return new_version
0294:         finally:
0295:             self._release_lock(token)
0296:     def push_changes(self, conn: sqlite3.Connection, baseline: Dict[str, Any]) -> bool:
0297:         if not self.enabled:
0298:             return True
0299:         local = snapshot_db(conn)
```
```text
0300:         try:
0301:             remote = self._get_snapshot() or {"schema": 1, "tables": {}}
0302:             merged = merge_local_changes(remote, baseline or {"schema": 1, "tables": {}}, local)
0303:             new_version = self._write_remote(merged)
0304:             self.replace_local(conn, merged)
0305:             self.last_remote_version = new_version
0306:             self.pending_base = None
0307:             self.pending_error = None
0308:             self._save_state(merged)
0309:             self._clear_pending()
0310:             return True
0311:         except Exception as exc:
0312:             self.pending_base = deepcopy(baseline)
0313:             self.pending_error = str(exc)
0314:             self._save_pending(local, baseline or {"schema": 1, "tables": {}})
0315:             return False
0316:     def maybe_pull(self, conn: sqlite3.Connection) -> bool:
0317:         if not self.enabled or self.pending_base is not None:
0318:             return False
0319:         now = time.monotonic()
0320:         if now - self.last_check < self.check_interval:
```
```text
0324:             version, _ = self._get_meta()
0325:             if not version or version == self.last_remote_version:
0326:                 return False
0327:             snapshot = self._get_snapshot()
0328:             if snapshot is None:
0329:                 return False
0330:             self.replace_local(conn, snapshot)
0331:             self.last_remote_version = version
0332:             self._save_state(snapshot)
0333:             self.pending_error = None
0334:             return True
0335:         except Exception as exc:
0336:             self.pending_error = str(exc)
0337:             return False
0338: class OnlineConnection:
0339:     def __init__(self, db_path: str, sync: FirebaseSync):
0340:         self._conn = sqlite3.connect(db_path, timeout=20)
0341:         self._conn.execute("PRAGMA busy_timeout=20000")
0342:         self.sync = sync
0343:         self._dirty = False
0344:         self._baseline: Optional[Dict[str, Any]] = None
```
```text
0337:             return False
0338: class OnlineConnection:
0339:     def __init__(self, db_path: str, sync: FirebaseSync):
0340:         self._conn = sqlite3.connect(db_path, timeout=20)
0341:         self._conn.execute("PRAGMA busy_timeout=20000")
0342:         self.sync = sync
0343:         self._dirty = False
0344:         self._baseline: Optional[Dict[str, Any]] = None
0345:     def execute(self, sql: str, params: Iterable[Any] = ()):
0346:         s = sql.lstrip().upper()
0347:         is_read = s.startswith("SELECT") or s.startswith("PRAGMA") or s.startswith("WITH") or s.startswith("EXPLAIN")
0348:         if is_read and not self._dirty and self._baseline is None:
0349:             self.sync.maybe_pull(self._conn)
0350:         elif not is_read and not self._dirty:
0351:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0352:             self._dirty = True
0353:         return self._conn.execute(sql, params)
0354:     def executemany(self, sql: str, seq_of_params):
0355:         if not self._dirty:
0356:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0357:             self._dirty = True
```
```text
0350:         elif not is_read and not self._dirty:
0351:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0352:             self._dirty = True
0353:         return self._conn.execute(sql, params)
0354:     def executemany(self, sql: str, seq_of_params):
0355:         if not self._dirty:
0356:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0357:             self._dirty = True
0358:         return self._conn.executemany(sql, seq_of_params)
0359:     def commit(self):
0360:         self._conn.commit()
0361:         # Make local persistence independent of Firebase availability.
0362:         durable_local.save(self._conn)
0363:         if self._dirty:
0364:             self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
0365:             # push_changes may merge remote rows back into SQLite.
0366:             durable_local.save(self._conn)
0367:         self._dirty = False
0368:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0369: 
0370:     def rollback(self):
```
```text
0363:         if self._dirty:
0364:             self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
0365:             # push_changes may merge remote rows back into SQLite.
0366:             durable_local.save(self._conn)
0367:         self._dirty = False
0368:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0369: 
0370:     def rollback(self):
0371:         self._conn.rollback()
0372:         self._dirty = False
0373:         self._baseline = None
0374:     def close(self):
0375:         self._conn.close()
0376:     def backup(self, target):
0377:         return self._conn.backup(target)
0378:     def __getattr__(self, name):
0379:         return getattr(self._conn, name)
```

## storage_lock.py

- Lines: 164
- Functions: _inside(19-23), _runtime_temp_root(26-28), _is_runtime_temp(31-33), _is_database_path(36-37), _permanent_db_target(40-41), _classify_relative(44-52), _write_target(55-67), _read_target(70-88), _is_write_mode(91-92), _open(95-101), _io_open(104-110), _sqlite_connect(113-131), _copy2(134-137), _copyfile(140-143), install(153-161)

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
0056:     p = Path(os.fspath(path))
0057:     if p.is_absolute():
0058:         if _inside(p, DATA_DIR) or _inside(p, BACKUP_DIR) or _inside(p, REPORTS_DIR):
0059:             return p
0060:         if _is_database_path(p) and (_is_runtime_temp(p) or _inside(p, INSTALL_ROOT) or _inside(p, Path(sys.executable).parent)):
0061:             return _permanent_db_target(p)
```
```text
0055: def _write_target(path, backup=False, report=False):
0056:     p = Path(os.fspath(path))
0057:     if p.is_absolute():
0058:         if _inside(p, DATA_DIR) or _inside(p, BACKUP_DIR) or _inside(p, REPORTS_DIR):
0059:             return p
0060:         if _is_database_path(p) and (_is_runtime_temp(p) or _inside(p, INSTALL_ROOT) or _inside(p, Path(sys.executable).parent)):
0061:             return _permanent_db_target(p)
0062:         if _inside(p, INSTALL_ROOT):
0063:             root = BACKUP_DIR if backup else REPORTS_DIR if report else DATA_DIR
0064:             return root / p.relative_to(INSTALL_ROOT)
0065:         return p
0066:     root = BACKUP_DIR if backup else REPORTS_DIR if report else _classify_relative(p)
0067:     return root / p
0068: 
0069: 
0070: def _read_target(path):
0071:     p = Path(os.fspath(path))
0072:     if p.is_absolute():
0073:         if _is_database_path(p) and (_inside(p, INSTALL_ROOT) or _inside(p, Path(sys.executable).parent) or _is_runtime_temp(p)):
0074:             candidate = _permanent_db_target(p)
0075:             if candidate.exists():
```
```text
0069: 
0070: def _read_target(path):
0071:     p = Path(os.fspath(path))
0072:     if p.is_absolute():
0073:         if _is_database_path(p) and (_inside(p, INSTALL_ROOT) or _inside(p, Path(sys.executable).parent) or _is_runtime_temp(p)):
0074:             candidate = _permanent_db_target(p)
0075:             if candidate.exists():
0076:                 return candidate
0077:             # Even when the permanent database does not exist yet, force all
0078:             # future reads/creates to the permanent Data directory. This avoids
0079:             # one-file PyInstaller runtime (_MEIPASS) data disappearing on exit.
0080:             return candidate
0081:         return p
0082:     if p.name.casefold() in _CONFIG_FILES or p.name.casefold() in _RESOURCE_FILES:
0083:         return p
0084: 
0085:     # User/application data must always resolve to permanent storage. Do not
0086:     # fall back to the current working directory or PyInstaller temp folder.
0087:     root = _classify_relative(p)
0088:     return root / p
0089: 
```
```text
0087:     root = _classify_relative(p)
0088:     return root / p
0089: 
0090: 
0091: def _is_write_mode(mode):
0092:     return any(ch in mode for ch in ("w", "a", "x", "+"))
0093: 
0094: 
0095: def _open(file, mode="r", *args, **kwargs):
0096:     if _is_write_mode(mode):
0097:         file = _write_target(file)
0098:         Path(file).parent.mkdir(parents=True, exist_ok=True)
0099:     else:
0100:         file = _read_target(file)
0101:     return _ORIGINAL_OPEN(file, mode, *args, **kwargs)
0102: 
0103: 
0104: def _io_open(file, mode="r", *args, **kwargs):
0105:     if _is_write_mode(mode):
0106:         file = _write_target(file)
0107:         Path(file).parent.mkdir(parents=True, exist_ok=True)
```
```text
0102: 
0103: 
0104: def _io_open(file, mode="r", *args, **kwargs):
0105:     if _is_write_mode(mode):
0106:         file = _write_target(file)
0107:         Path(file).parent.mkdir(parents=True, exist_ok=True)
0108:     else:
0109:         file = _read_target(file)
0110:     return _ORIGINAL_IO_OPEN(file, mode, *args, **kwargs)
0111: 
0112: 
0113: def _sqlite_connect(database, *args, **kwargs):
0114:     if isinstance(database, (str, os.PathLike)) and str(database) not in (":memory:", ""):
0115:         original = Path(os.fspath(database))
0116:         target = _write_target(original)
0117:         target.parent.mkdir(parents=True, exist_ok=True)
0118: 
0119:         # Migrate an older database into permanent storage exactly once. Carry
0120:         # SQLite WAL/SHM sidecars as well so committed transactions are not lost.
0121:         if original.is_absolute() and original != target and original.exists() and not target.exists():
0122:             try:
```
```text
0122:             try:
0123:                 shutil.copy2(original, target)
0124:                 for suffix in ("-wal", "-shm"):
0125:                     sidecar = Path(str(original) + suffix)
0126:                     if sidecar.exists():
0127:                         shutil.copy2(sidecar, Path(str(target) + suffix))
0128:             except OSError:
0129:                 pass
0130:         database = str(target)
0131:     return _ORIGINAL_SQLITE_CONNECT(database, *args, **kwargs)
0132: 
0133: 
0134: def _copy2(src, dst, *args, **kwargs):
0135:     dst = _write_target(dst, backup="backup" in str(dst).casefold())
0136:     Path(dst).parent.mkdir(parents=True, exist_ok=True)
0137:     return _ORIGINAL_COPY2(src, dst, *args, **kwargs)
0138: 
0139: 
0140: def _copyfile(src, dst, *args, **kwargs):
0141:     dst = _write_target(dst, backup="backup" in str(dst).casefold())
0142:     Path(dst).parent.mkdir(parents=True, exist_ok=True)
```
```text
0140: def _copyfile(src, dst, *args, **kwargs):
0141:     dst = _write_target(dst, backup="backup" in str(dst).casefold())
0142:     Path(dst).parent.mkdir(parents=True, exist_ok=True)
0143:     return _ORIGINAL_COPYFILE(src, dst, *args, **kwargs)
0144: 
0145: 
0146: _ORIGINAL_OPEN = builtins.open
0147: _ORIGINAL_IO_OPEN = io.open
0148: _ORIGINAL_SQLITE_CONNECT = sqlite3.connect
0149: _ORIGINAL_COPY2 = shutil.copy2
0150: _ORIGINAL_COPYFILE = shutil.copyfile
0151: 
0152: 
0153: def install():
0154:     DATA_DIR.mkdir(parents=True, exist_ok=True)
0155:     BACKUP_DIR.mkdir(parents=True, exist_ok=True)
0156:     REPORTS_DIR.mkdir(parents=True, exist_ok=True)
0157:     builtins.open = _open
0158:     io.open = _io_open
0159:     sqlite3.connect = _sqlite_connect
0160:     shutil.copy2 = _copy2
```

## store_inventory.py

- Lines: 5258
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-332), restore_database(334-351), stock(353-358), fmt_num(360-362), to_iso_date(364-373), to_display_date(375-383), fiscal_year_key(385-396), fiscal_year_range(398-401), normalize_code(403-411), format_code(413-422), attach_code_mask(424-450), set_digits(427-432), key(433-443), paste(445-448), bind_add_to_list(452-473), on_enter(455-466), __init__(477-494), _check_for_updates(496-501), _setup_style(503-539), _shade(542-547), on_close(549-554), redo_network_setup(556-572), backup_now(574-581), restore_backup(583-601), _ctrl_f(603-615), _open_exact_find_text_popup(617-662), do_find(638-647), close(648-655), _global_enter(664-676), wipe(678-679), login(681-710), do_login(696-707), change_password(712-762), save_password(734-756), logout(764-769), home(771-790), _ensure_mdi_host(792-813), _internal_window(815-899), normal_place(831-837), restore(838-845), maximize(846-852), minimize(853-868), close(869-892), open_inventory_codes_detail_flow(901-919), open_inventory_codes_with_filters(921-935), open_inventory_codes_report_window(937-1163), tbtn(955-960), balance_as_of(1017-1027), build_nav(1029-1051), selected_prefix(1053-1062), load(1064-1096), page_move(1098-1099), page_first(1100-1100), page_last(1101-1105), on_nav(1109-1110), find_popup(1113-1132), search_fn(1115-1130), print_report(1135-1138), export_pdf(1140-1142), export_word(1143-1145), export_excel(1146-1148), open_menu_window(1165-1187), close_window(1175-1182), _manual_check_update(1189-1193), _show_current_version(1195-1199), build_menu_bar(1201-1248), open_calendar_picker(1250-1298), pick(1268-1270), redraw(1272-1284), nav(1286-1290), make_date_field(1300-1307), clearbody(1309-1335), run_action(1324-1329), _portable_print_current(1337-1348), portable_print_dialog(1350-1423), build_receipt(1377-1395), send(1396-1409), refresh_printers(1410-1416), preview_tree(1425-1437), set_page_actions(1439-1447), _add_transaction_new_button(1449-1466), _report_header(1468-1532), _report_footer(1534-1540), _grr_signature_block(1542-1558), _finish_page(1560-1561), _wrap_text_to_width(1563-1588), fits(1570-1570), _pdf_table_report(1590-1659), table_header(1612-1617), show_preview_window(1661-1734), _safe_report_name(1736-1739), print_preview_window(1741-1744), _fallback_pdf_export(1746-1779), esc(1750-1751), add(1754-1756), export_preview_pdf(1781-1810), export_preview_word(1812-1852), export_preview_excel(1854-1890), make_tree(1892-1901), pick_item(1903-1924), choose(1904-1923), ld(1911-1915), sel(1917-1921), bind_item_lookup(1926-1943), lookup(1928-1941), _set_form_editable(1946-1959), walk(1949-1958), document_selector(1961-1995), refresh(1966-1977), selected(1978-1983), dashboard(1997-2106), load_details(2079-2103), dashboard_details(2108-2112), item_history(2114-2134), _ask_item_master_filters(2136-2220), finish(2189-2201), items(2222-2460), hierarchy(2263-2272), selected_prefix(2318-2331), balance_as_of(2333-2340), load(2342-2380), set_page(2382-2383), select_node(2385-2406), open_find(2412-2431), search_fn(2414-2429), visible_rows(2436-2438), print_inventory(2439-2443), export_inventory_word(2444-2446), export_inventory_excel(2447-2449), portable_inventory(2454-2456), inventory_codes(2462-2744), btn(2498-2503), close_editor(2539-2549), edit_cell(2551-2577), commit(2569-2575), rows_query(2579-2592), load(2594-2609), new_record(2611-2632), commit(2625-2629), selected_row(2634-2636), edit_record(2638-2646), save_record(2648-2689), delete_record(2691-2702), refresh(2704-2704), do_print(2705-2707), do_close(2708-2708), filter_grid(2726-2733), open_mto_inventory_flow(2746-2769), open_code_opening_flow(2771-2779), code_opening(2781-2782), _open_code_opening_popup(2784-2785), _open_code_opening_detail(2787-3030), norm(2857-2858), table_for(2860-2861), row_for(2863-2868), search_any_destination(2870-2883), desc_hit(2885-2889), clear_form(2891-2904), load_for_edit(2906-2927), check_duplicates(2929-2940), save_code(2945-2996), edit_action(2998-3002), delete_code(3004-3019), _mto_new_item_dialog(3032-3068), save(3048-3065), _item_filter_bar(3070-3082), _date_filter_bar(3084-3092), _ask_mto_inventory_filters(3094-3139), finish(3124-3132), mto_inventory(3141-3341), open_find(3175-3194), search_fn(3177-3192), hierarchy(3213-3217), rebuild_nav(3219-3230), mto_balance(3254-3263), load(3265-3307), set_page(3309-3309), select_node(3310-3319), visible_rows(3324-3324), do_print(3325-3329), export_word(3330-3332), export_excel(3333-3335), party_master(3343-3394), load(3353-3356), clear(3357-3361), new_form(3362-3363), save(3364-3370), load_party_row(3371-3375), on_party_select(3376-3377), edit(3379-3383), delete_party(3384-3390), user_management(3396-3480), sync_role(3423-3428), load(3432-3435), clear(3436-3439), edit(3440-3447), save(3448-3465), delete_user(3466-3477), _renumber_tree(3483-3486), demand(3488-3649), _restore_demand_tree_columns(3531-3537), add(3540-3548), edit_item(3550-3562), delete_item(3564-3572), new_form(3576-3582), save(3584-3597), delete_current(3601-3607), cancel_form(3608-3616), preview_now(3617-3627), edit_saved_demand(3628-3631), print_now(3632-3642), load_demand_into_form(3651-3663), refresh_saved_cache(3665-3677), grr(3679-3839), add(3711-3719), edit_item(3721-3731), delete_item(3733-3741), new_form(3745-3751), save(3753-3771), delete_current(3775-3781), cancel_form(3782-3790), preview_now(3791-3809), portable_current(3810-3813), edit_saved_grr(3815-3818), print_now(3819-3832), load_grr_into_form(3841-3853), issue(3855-3998), old_issue_qty(3884-3887), update_balance(3888-3896), add(3898-3907), edit_item(3909-3920), new_form(3924-3930), post(3932-3950), delete_current(3951-3957), cancel_form(3958-3966), preview_now(3967-3974), portable_current(3975-3977), load_saved_issue(3982-3984), edit_saved_issue(3985-3988), print_issue_now(3989-3994), load_issue_into_form(4000-4013), _ask_report_criteria(4015-4078), finish(4064-4072), _open_report_child(4080-4085), open_stock_balance_report_flow(4087-4090), open_grr_report_flow(4092-4095), open_demand_report_flow(4097-4100), open_issue_report_flow(4102-4105), open_party_report_flow(4107-4110), _ask_stock_balance_filters(4112-4135), ok(4127-4128), cancel(4129-4129), stock_balance(4137-4200), period(4153-4164), header_summary(4165-4166), load(4167-4176), reopen_filters(4177-4181), open_find_stock(4185-4198), search_fn(4187-4197), ledger(4202-4214), open_document_editor(4216-4224), _edit_from_selector(4226-4242), show_saved_records(4244-4275), view(4267-4271), documents(4277-4322), edit_selected(4296-4302), delete_selected(4303-4315), doc_export_selected(4324-4330), doc_preview_selected(4332-4342), doc_print_selected(4344-4352), load_document(4354-4384), _print_loaded_document(4378-4383), _report_filter_popup(4386-4403), ok(4399-4400), cancel(4401-4401), _report_window(4405-4449), load(4418-4425), hdr(4426-4426), open_find_report(4432-4446), search_fn(4434-4445), report_grr(4451-4462), pb(4453-4461), report_demand(4464-4475), pb(4466-4474), report_issue(4477-4486), pb(4479-4485), report_party(4488-4498), pb(4490-4497), reports(4500-4628), load_grr_item(4513-4518), load_grr_date(4526-4534), load_party(4546-4554), load_dem_item(4567-4572), load_dem_date(4580-4588), load_iss_item(4602-4607), load_iss_date(4615-4623), print_item_master(4630-4632), print_party_master(4634-4636), print_report(4638-4652), print_stock(4654-4659), print_ledger(4661-4668), _get_doc_data(4670-4698), export_word(4700-4747), export_excel(4749-4789), preview_pdf(4791-4799), _open_direct_printer(4801-4831), _select_windows_printer_for_pdf(4833-5204), render_preview(4958-4977), on_resize(4979-4981), parse_page_selection(5000-5016), selected_printer(5018-5020), print_rendered_pages(5022-5180), close(5182-5192), print_pdf(5206-5224), open_file(5226-5231), print_demand(5233-5238), print_grr(5240-5248), print_issue(5250-5255)

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
0304:     """Create a safe, restorable full backup (a .db snapshot + a .zip copy)
```
```text
0297:     with open(SEED,encoding="utf-8-sig") as f:
0298:         for r in csv.DictReader(f):
0299:             c.execute("INSERT OR IGNORE INTO items(code,description,uom) VALUES(?,?,?)",
0300:                       (format_code(r.get("code","").strip()),r.get("description","").strip(),r.get("uom","").strip()))
0301:     c.commit()
0302: 
0303: def backup_database(manual=False):
0304:     """Create a safe, restorable full backup (a .db snapshot + a .zip copy)
0305:     in BACKUP_DIR. Runs automatically on every logout/exit, and can also be
0306:     triggered manually from the Backup Now button. Keeps the most recent
0307:     30 automatic backups plus every manual one, so disk space stays sane."""
0308:     try:
0309:         if not os.path.exists(DB): return None
0310:         stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
0311:         tag="manual" if manual else "auto"
0312:         latest=os.path.join(BACKUP_DIR,"inventory_backup_latest.db")
0313:         dated=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.db")
0314:         zpath=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.zip")
0315: 
0316:         src=sqlite3.connect(DB)
0317:         for path in (latest,dated):
```
```text
0311:         tag="manual" if manual else "auto"
0312:         latest=os.path.join(BACKUP_DIR,"inventory_backup_latest.db")
0313:         dated=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.db")
0314:         zpath=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.zip")
0315: 
0316:         src=sqlite3.connect(DB)
0317:         for path in (latest,dated):
0318:             if os.path.exists(path): os.remove(path)
0319:             dst=sqlite3.connect(path)
0320:             with dst:
0321:                 src.backup(dst)
0322:             dst.close()
0323:         src.close()
0324: 
0325:         with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
0326:             z.write(dated,"store_inventory.db")
0327: 
0328:         # Automatic backup rotation/deletion is intentionally disabled.
0329:         # Stored backups remain until the user explicitly deletes/restores them.
0330:         return zpath
0331:     except Exception:
```
```text
0326:             z.write(dated,"store_inventory.db")
0327: 
0328:         # Automatic backup rotation/deletion is intentionally disabled.
0329:         # Stored backups remain until the user explicitly deletes/restores them.
0330:         return zpath
0331:     except Exception:
0332:         return None
0333: 
0334: def restore_database(backup_path):
0335:     """Restore the database from a .db or .zip backup file. The current
0336:     database is itself backed up first, so a restore can never destroy data."""
0337:     try:
0338:         backup_database(manual=True)  # safety net before touching anything
0339:         if backup_path.lower().endswith(".zip"):
0340:             with zipfile.ZipFile(backup_path,"r") as z:
0341:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0342:                 os.makedirs(tmp_dir,exist_ok=True)
0343:                 z.extractall(tmp_dir)
0344:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0345:                 shutil.copy2(extracted,DB)
0346:                 shutil.rmtree(tmp_dir,ignore_errors=True)
```
```text
0340:             with zipfile.ZipFile(backup_path,"r") as z:
0341:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0342:                 os.makedirs(tmp_dir,exist_ok=True)
0343:                 z.extractall(tmp_dir)
0344:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0345:                 shutil.copy2(extracted,DB)
0346:                 shutil.rmtree(tmp_dir,ignore_errors=True)
0347:         else:
0348:             shutil.copy2(backup_path,DB)
0349:         return True
0350:     except Exception:
0351:         return False
0352: 
0353: def stock(c, code):
0354:     r=c.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()
0355:     q=float(r[0] or 0) if r else 0
0356:     for typ,qty in c.execute("SELECT doc_type,qty FROM transactions WHERE code=? ORDER BY id", (code,)):
0357:         q += float(qty or 0) if typ=="GRR" else -float(qty or 0) if typ=="ISSUE" else 0
0358:     return q
0359: 
0360: def fmt_num(x):
```
```text
0358:     return q
0359: 
0360: def fmt_num(x):
0361:     x=float(x or 0)
0362:     return f"{x:,.2f}".rstrip("0").rstrip(".")
0363: 
0364: def to_iso_date(s):
0365:     """Convert a user-entered DD/MM/YYYY date (or an already-ISO date) into
0366:     ISO YYYY-MM-DD for storage in the database and for date-range queries,
0367:     which rely on ISO strings sorting/comparing correctly."""
0368:     s=(s or "").strip()
0369:     if not s: return ""
0370:     for f in ("%d/%m/%Y","%Y-%m-%d"):
0371:         try: return datetime.strptime(s,f).strftime("%Y-%m-%d")
0372:         except Exception: continue
0373:     return s
0374: 
0375: def to_display_date(s):
0376:     """Convert an ISO YYYY-MM-DD date (as stored in the database) into the
0377:     DD/MM/YYYY format used everywhere on screen and on printed reports."""
0378:     s=(s or "").strip()
```
```text
0473:     return on_enter
0474: 
0475: 
0476: class App(tk.Tk):
0477:     def __init__(self):
0478:         super().__init__()
0479:         self.title("Store Inventory Management System | SAP Style")
0480:         self.geometry("1400x820"); self.minsize(1150,700)
0481:         self.conn=connect()
0482:         self.demand_lines=[]; self.grr_lines=[]; self.issue_lines=[]
0483:         self.current_user=None; self.current_role=None
0484:         self._item_master_search_entry=None
0485:         self._item_master_find_callback=None
0486:         self._portable_print_context=None
0487:         self.can_edit=False; self.can_delete=False; self.is_admin=False
0488:         self._setup_style()
0489:         # Any focused button can be activated with Enter.
0490:         self.bind_all("<Return>", self._global_enter, add="+")
0491:         self.bind_all("<KP_Enter>", self._global_enter, add="+")
0492:         self.bind_all("<Control-f>", self._ctrl_f, add="+")
0493:         self.protocol("WM_DELETE_WINDOW", self.on_close)
```
```text
0541:     @staticmethod
0542:     def _shade(hexcolor, factor):
0543:         """Return a slightly darker version of a #RRGGBB color (for hover/press states)."""
0544:         h=hexcolor.lstrip("#")
0545:         r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
0546:         r,g,b=(max(0,int(v*factor)) for v in (r,g,b))
0547:         return f"#{r:02x}{g:02x}{b:02x}"
0548: 
0549:     def on_close(self):
0550:         try:
0551:             self.conn.commit(); backup_database()
0552:         except Exception:
0553:             pass
0554:         self.destroy()
0555: 
0556:     def redo_network_setup(self):
0557:         if not messagebox.askyesno("Network Setup",
0558:             "This will clear the online database URL saved on this computer.\n\n"
0559:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0560:             "Continue?"):
0561:             return
```
```text
0555: 
0556:     def redo_network_setup(self):
0557:         if not messagebox.askyesno("Network Setup",
0558:             "This will clear the online database URL saved on this computer.\n\n"
0559:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0560:             "Continue?"):
0561:             return
0562:         try:
0563:             self.conn.commit(); backup_database()
0564:         except Exception:
0565:             pass
0566:         try:
0567:             if os.path.exists(FIREBASE_URL_FILE): os.remove(FIREBASE_URL_FILE)
0568:         except Exception:
0569:             pass
0570:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0571:         self.destroy()
0572:         sys.exit(0)
0573: 
0574:     def backup_now(self):
0575:         path=backup_database(manual=True)
```
```text
0569:             pass
0570:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0571:         self.destroy()
0572:         sys.exit(0)
0573: 
0574:     def backup_now(self):
0575:         path=backup_database(manual=True)
0576:         if path:
0577:             messagebox.showinfo("Backup Complete",
0578:                 f"A full backup was saved to:\n\n{path}\n\n"
0579:                 f"All backups are kept in:\n{BACKUP_DIR}")
0580:         else:
0581:             messagebox.showerror("Backup Failed","Could not create a backup. Make sure the database exists.")
0582: 
0583:     def restore_backup(self):
0584:         from tkinter import filedialog
0585:         if not messagebox.askyesno("Restore Backup",
0586:             "This will replace all current data with the selected backup.\n"
0587:             "A safety backup of the current data will be made first.\n\n"
0588:             "Continue?"):
0589:             return
```
```text
0583:     def restore_backup(self):
0584:         from tkinter import filedialog
0585:         if not messagebox.askyesno("Restore Backup",
0586:             "This will replace all current data with the selected backup.\n"
0587:             "A safety backup of the current data will be made first.\n\n"
0588:             "Continue?"):
0589:             return
0590:         path=filedialog.askopenfilename(
0591:             title="Select a backup file",
0592:             initialdir=BACKUP_DIR,
0593:             filetypes=[("Backup files","*.zip *.db"),("All files","*.*")])
0594:         if not path: return
0595:         if restore_database(path):
0596:             messagebox.showinfo("Restore Complete",
0597:                 "Data has been restored. The application will now restart.")
0598:             self.conn.close()
0599:             os.execv(sys.executable, [sys.executable]+sys.argv)
0600:         else:
0601:             messagebox.showerror("Restore Failed","Could not restore from that backup file.")
0602: 
0603:     def _ctrl_f(self, event=None):
```
```text
0640:             if not text:
0641:                 fe.focus_set(); return
0642:             try:
0643:                 found=search_fn(text)
0644:             except Exception:
0645:                 found=False
0646:             if found is False:
0647:                 messagebox.showinfo("Find Text","No matching text found.",parent=dlg)
0648:         def close():
0649:             try:
0650:                 dlg.grab_release()
0651:             except Exception: pass
0652:             try: dlg.destroy()
0653:             except Exception: pass
0654:             if getattr(self,"_exact_find_text_dialog",None) is dlg:
0655:                 self._exact_find_text_dialog=None
0656:         ttk.Button(box,text="Find Next",command=do_find,width=13).grid(row=0,column=3,padx=4,pady=4)
0657:         ttk.Button(box,text="Cancel",command=close,width=13).grid(row=1,column=3,padx=4,pady=4)
0658:         fe.bind("<Return>",lambda e:(do_find(),"break"))
0659:         dlg.bind("<Escape>",lambda e:close())
0660:         dlg.protocol("WM_DELETE_WINDOW",close)
```
```text
0726:         cur_ent=ttk.Entry(box,textvariable=current,width=28,show="*"); cur_ent.grid(row=2,column=1,pady=7)
0727:         ttk.Label(box,text="New Password").grid(row=3,column=0,sticky="w",pady=7)
0728:         new_ent=ttk.Entry(box,textvariable=new,width=28,show="*"); new_ent.grid(row=3,column=1,pady=7)
0729:         ttk.Label(box,text="Confirm New Password").grid(row=4,column=0,sticky="w",pady=7)
0730:         conf_ent=ttk.Entry(box,textvariable=confirm,width=28,show="*"); conf_ent.grid(row=4,column=1,pady=7)
0731:         err=ttk.Label(box,text="",foreground="#c0392b",wraplength=380,justify="left")
0732:         err.grid(row=5,column=0,columnspan=2,pady=(5,8))
0733: 
0734:         def save_password(event=None):
0735:             old_pw=current.get()
0736:             new_pw=new.get()
0737:             confirm_pw=confirm.get()
0738:             row=self.conn.execute("SELECT password FROM users WHERE username=?",(self.current_user,)).fetchone()
0739:             if not row or not verify_password(old_pw,row[0]):
0740:                 err.config(text="Current password is incorrect."); return
0741:             if len(new_pw) < 4:
0742:                 err.config(text="New password must be at least 4 characters."); return
0743:             if new_pw != confirm_pw:
0744:                 err.config(text="New password and confirmation do not match."); return
0745:             if new_pw == old_pw:
0746:                 err.config(text="New password must be different from the current password."); return
```
```text
0742:                 err.config(text="New password must be at least 4 characters."); return
0743:             if new_pw != confirm_pw:
0744:                 err.config(text="New password and confirmation do not match."); return
0745:             if new_pw == old_pw:
0746:                 err.config(text="New password must be different from the current password."); return
0747:             try:
0748:                 self.conn.execute("UPDATE users SET password=? WHERE username=?",
0749:                                   (hash_password(new_pw),self.current_user))
0750:                 self.conn.commit()
0751:                 backup_database()
0752:                 win.grab_release(); win.destroy()
0753:                 messagebox.showinfo("Password Changed",
0754:                     "Your password has been changed successfully.\n\nUse the new password the next time you log in.", parent=self)
0755:             except Exception as ex:
0756:                 err.config(text=f"Could not change password: {ex}")
0757: 
0758:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0759:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0760:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0761:         conf_ent.bind("<Return>",save_password)
0762:         cur_ent.focus_set()
```
```text
0758:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0759:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0760:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0761:         conf_ent.bind("<Return>",save_password)
0762:         cur_ent.focus_set()
0763: 
0764:     def logout(self):
0765:         try:
0766:             self.conn.commit(); backup_database()
0767:         except Exception:
0768:             pass
0769:         self.login()
0770: 
0771:     def home(self):
0772:         self.wipe()
0773:         self.build_menu_bar()
0774:         hdr=tk.Frame(self,bg=COLORS["primary_dark"]);hdr.pack(fill="x")
0775:         self._shell_header=hdr
0776:         inner=tk.Frame(hdr,bg=COLORS["primary_dark"],padx=16,pady=10);inner.pack(fill="x")
0777:         tk.Label(inner,text=COMPANY,font=("Segoe UI",16,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="left")
0778:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
```
```text
0778:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
0779:         tk.Label(inner,text=f"Data: {DATA_DIR}",font=("Segoe UI",8),bg=COLORS["primary_dark"],fg="#9FB8DA").pack(side="left",padx=14)
0780:         ttk.Button(inner,text="Logout",style="Danger.TButton",command=self.logout).pack(side="right")
0781:         tk.Label(inner,text=f"{self.current_user}  ({self.current_role})",font=("Segoe UI",9,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="right",padx=12)
0782:         nav=tk.Frame(self,bg=COLORS["primary"]);nav.pack(fill="x")
0783:         self._shell_nav=nav
0784:         navin=tk.Frame(nav,bg=COLORS["primary"],padx=10,pady=6);navin.pack(fill="x")
0785:         ttk.Button(navin,text="🏠  Dashboard",style="Accent.TButton",command=self.dashboard).pack(side="left",padx=3)
0786:         tk.Label(navin,text="Inventory  |  Transaction  |  Report  |  Edit  |  Help  —  see the menu bar above for every other section.",
0787:                  font=("Segoe UI",8),bg=COLORS["primary"],fg="#E7EFFB").pack(side="left",padx=14)
0788:         self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
0789:         self.main_body=self.body
0790:         self.dashboard()
0791: 
0792:     def _ensure_mdi_host(self):
0793:         """Create the in-app MDI workspace. Child windows never leave the main program."""
0794:         host=getattr(self,"_mdi_host",None)
0795:         if host is None or not host.winfo_exists():
0796:             host=tk.Frame(self.main_body,bg="#d9dde3",bd=0,highlightthickness=0)
0797:             self._mdi_host=host
0798:         host.place(relx=0,rely=0,relwidth=1,relheight=1)
```
```text
0861:             b.pack(side="left")
0862:             rb=tk.Button(item,text="□",font=("Segoe UI",8,"bold"),width=2,height=1,padx=0,pady=0,
0863:                          command=lambda:(restore(),maximize()),relief="flat",bd=0,bg="#e7e7e7")
0864:             rb.pack(side="left")
0865:             xb=tk.Button(item,text="×",font=("Segoe UI",9,"bold"),width=2,height=1,padx=0,pady=0,
0866:                          command=close,relief="flat",bd=0,bg="#e7e7e7")
0867:             xb.pack(side="left")
0868:             state["task"]=item
0869:         def close():
0870:             try:
0871:                 task=state.get("task")
0872:                 if task and task.winfo_exists(): task.destroy()
0873:             except Exception: pass
0874:             try:
0875:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
0876:             except Exception: pass
0877:             try: outer.destroy()
0878:             except Exception: pass
0879:             if not getattr(self,"_mdi_windows",[]):
0880:                 self._mdi_host.place_forget()
0881:                 # Restore the original application shell FIRST, then rebuild
```
```text
0925:             return None
0926:         self._inventory_codes_filter=criteria
0927:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0928:         try:
0929:             self.items(container=body)
0930:             win.lift()
0931:             return win
0932:         except Exception:
0933:             try: win._internal_close()
0934:             except Exception: pass
0935:             raise
0936: 
0937:     def open_inventory_codes_report_window(self, criteria=None):
0938:         """Open Inventory Codes as a real report-style child window.
0939: 
0940:         This intentionally mirrors the supplied Preview Report workflow: a
0941:         separate resizable/maximizable window with a left navigation tree,
0942:         compact report toolbar, Find dialog, and print/export commands.
0943:         The main application remains open behind it.
0944:         """
0945:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
0942:         compact report toolbar, Find dialog, and print/export commands.
0943:         The main application remains open behind it.
0944:         """
0945:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
0946:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
0947:         }
0948:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0949: 
0950:         # --- report-style toolbar ---
0951:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
0952:         toolbar.pack(fill="x",side="top")
0953:         toolbar.pack_propagate(False)
0954: 
0955:         def tbtn(text,cmd,width=9):
0956:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
0957:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
0958:                          padx=3,pady=1)
0959:             b.pack(side="left",padx=2,pady=6)
0960:             return b
0961: 
0962:         # --- main report body ---
```
```text
0973:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
0974:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
0975:         navscroll.config(command=code_tree.yview)
0976:         navscroll.pack(side="right",fill="y")
0977:         code_tree.pack(side="left",fill="both",expand=True)
0978: 
0979:         right=tk.Frame(content,bg="#EDEDED")
0980:         right.pack(side="left",fill="both",expand=True)
0981:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
0982:         reportbar.pack(fill="x")
0983:         reportbar.pack_propagate(False)
0984:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
0985:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
0986:         tab.pack(side="left",padx=4,pady=2)
0987:         titlevar=tk.StringVar(value="Inventory Summary")
0988:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
0989:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
0990: 
0991:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
0992:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
0993:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1127:                     vals=tree.item(iid,"values")
1128:                     if str(vals[1]).lower()==str(target).lower():
1129:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1130:                 return True
1131:             self._open_exact_find_text_popup(search_fn)
1132:             self._item_master_find_callback=find_popup
1133: 
1134: 
1135:         def print_report():
1136:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1137:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1138:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1139: 
1140:         def export_pdf():
1141:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1142:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1143:         def export_word():
1144:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1145:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1146:         def export_excel():
1147:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1143:         def export_word():
1144:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1145:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1146:         def export_excel():
1147:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1148:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1149: 
1150:         tbtn("Find",find_popup,7)
1151:         tbtn("Print",print_report,7)
1152:         tbtn("PDF",export_pdf,6)
1153:         tbtn("Word",export_word,6)
1154:         tbtn("Excel",export_excel,6)
1155:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1156:         tbtn("Refresh",load,8)
1157:         tbtn("Close",win._internal_close,7)
1158:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1159:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1160: 
1161:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1162:         build_nav(); load(); win.focus_force()
1163:         return win
```
```text
1173:         self.body=frame
1174:         closed={"done":False}
1175:         def close_window():
1176:             if closed["done"]: return
1177:             closed["done"]=True
1178:             if getattr(self,"body",None) is frame: self.body=old_body
1179:             self._page_actions=old_actions
1180:             self._item_master_find_callback=old_find
1181:             try: win._internal_close()
1182:             except Exception: win.destroy()
1183:         win._internal_close=close_window
1184:         try:
1185:             method(); self.update_idletasks(); win.lift(); return win
1186:         except Exception:
1187:             close_window(); raise
1188: 
1189:     def _manual_check_update(self):
1190:         try:
1191:             updater.check_for_update(self, manual=True)
1192:         except Exception as e:
1193:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1197:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1198:         except Exception as e:
1199:             messagebox.showerror("Current Version", str(e), parent=self)
1200: 
1201:     def build_menu_bar(self):
1202:         """Professional section / sub-section menu bar, ERP style:
1203:         Inventory > Item Master
1204:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1205:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1206:         Edit > Change Password, User Management
1207:         Help > Backup Now, Restore Backup, Network Setup
1208:         """
1209:         menubar=tk.Menu(self)
1210: 
1211:         m_inv=tk.Menu(menubar,tearoff=0)
1212:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1213:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1214:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1215:         menubar.add_cascade(label="Inventory",menu=m_inv)
1216: 
1217:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1217:         m_trans=tk.Menu(menubar,tearoff=0)
1218:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1219:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1220:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1221:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1222:         menubar.add_cascade(label="Transaction",menu=m_trans)
1223: 
1224:         m_rep=tk.Menu(menubar,tearoff=0)
1225:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1226:         m_rep.add_separator()
1227:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1228:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1229:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1230:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1231:         menubar.add_cascade(label="Report",menu=m_rep)
1232: 
1233:         m_edit=tk.Menu(menubar,tearoff=0)
1234:         m_edit.add_command(label="Change Password",command=self.change_password)
1235:         if self.is_admin:
1236:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1237:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1232: 
1233:         m_edit=tk.Menu(menubar,tearoff=0)
1234:         m_edit.add_command(label="Change Password",command=self.change_password)
1235:         if self.is_admin:
1236:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1237:         menubar.add_cascade(label="Edit",menu=m_edit)
1238: 
1239:         m_help=tk.Menu(menubar,tearoff=0)
1240:         m_help.add_command(label="Backup Now",command=self.backup_now)
1241:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1242:         m_help.add_command(label="Current Version",command=self._show_current_version)
1243:         if self.is_admin:
1244:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1245:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1246:         menubar.add_cascade(label="Help",menu=m_help)
1247: 
1248:         self.config(menu=menubar)
1249: 
1250:     def open_calendar_picker(self, var):
1251:         """Small month-grid calendar popup. Picking a day sets `var` to
1252:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1305:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1306:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1307:         return f
1308: 
1309:     def clearbody(self):
1310:         self._portable_print_context=None
1311:         for w in self.body.winfo_children(): w.destroy()
1312:         self._page_actions = {
1313:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1314:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1315:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1316:             "cancel": lambda: self.dashboard(),
1317:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1318:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1319:         }
1320:         # Single SAP-style toolbar at the very top.
1321:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1322:         self._page_action_bar=bar
1323:         self._page_action_first_button=None
1324:         def run_action(k):
1325:             if k=="edit" and not self.can_edit:
```
```text
1322:         self._page_action_bar=bar
1323:         self._page_action_first_button=None
1324:         def run_action(k):
1325:             if k=="edit" and not self.can_edit:
1326:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1327:             if k=="delete" and not self.can_delete:
1328:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1329:             self._page_actions[k]()
1330:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1331:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1332:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1333:             b.pack(side="left",padx=(0,2))
1334:             if self._page_action_first_button is None: self._page_action_first_button=b
1335:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1336: 
1337:     def _portable_print_current(self):
1338:         ctx=getattr(self,"_portable_print_context",None)
1339:         if not ctx:
1340:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1341:             return
1342:         try:
```
```text
1344:             if not data: return
1345:             title,header,columns,rows=data
1346:             self.portable_print_dialog(title,header,columns,rows)
1347:         except Exception as e:
1348:             messagebox.showerror("Portable Printer",str(e))
1349: 
1350:     def portable_print_dialog(self,title,header_lines,columns,rows):
1351:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1352:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1353:         if not WIN32PRINT_AVAILABLE:
1354:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1355:             return
1356:         try:
1357:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1358:         except Exception as e:
1359:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1360:             return
1361:         if not printers:
1362:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1363:             return
1364:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1414:                 if vals and pv.get() not in vals: pv.set(vals[0])
1415:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1416:             except Exception as ex: status.set(str(ex))
1417:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1418:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1419:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1420:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1421:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1422:         win.bind("<Escape>",lambda e:win._internal_close())
1423:         win.focus_force()
1424: 
1425:     def preview_tree(self, title, tree, header_lines=None):
1426:         """Preview the exact rows currently visible in a Treeview."""
1427:         cols=list(tree["columns"])
1428:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1429:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1430:         if not rows:
1431:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1432:             return
1433:         widths=[]
1434:         for c in cols:
```
```text
1431:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1432:             return
1433:         widths=[]
1434:         for c in cols:
1435:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1436:             except Exception: widths.append(100)
1437:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1438: 
1439:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1440:         self._page_actions.update({
1441:             "save": save or self._page_actions.get("save"),
1442:             "edit": edit or self._page_actions.get("edit"),
1443:             "delete": delete or self._page_actions.get("delete"),
1444:             "cancel": cancel or self._page_actions.get("cancel"),
1445:             "print": print or self._page_actions.get("print"),
1446:             "preview": preview or self._page_actions.get("preview"),
1447:         })
1448: 
1449:     def _add_transaction_new_button(self, command):
1450:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1451:         if bar is None or first is None: return
```
```text
1460:         sep.pack(side="left",fill="y",padx=4)
1461:         for w in existing:
1462:             try:
1463:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1464:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1465:                 else: w.pack(side="left")
1466:             except Exception: pass
1467: 
1468:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1469:         """Draw a consistent professional report header and return the first table Y.
1470: 
1471:         For GRN Receipt reports the document number is shown on the left and
1472:         the GRN Date is deliberately shown on the right in a bordered document
1473:         information panel.
1474:         """
1475:         W,H=page_size
1476:         if y_top is None: y_top=H-24
1477:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1478:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1479:         if os.path.exists(LOGO_FILE):
1480:             try:
```
```text
1473:         information panel.
1474:         """
1475:         W,H=page_size
1476:         if y_top is None: y_top=H-24
1477:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1478:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1479:         if os.path.exists(LOGO_FILE):
1480:             try:
1481:                 from reportlab.lib.utils import ImageReader
1482:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1483:             except Exception:
1484:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1485:         else:
1486:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1487:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1488:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1489:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1490:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1491: 
1492:         # Professional document information box.
1493:         info_top=logo_y-12
```
```text
1526:                 # naturally occupies the right-hand cell when supplied second.
1527:                 c.setFont("Helvetica-Bold",7)
1528:                 c.drawString(xx,yy,(label+":")[:28])
1529:                 c.setFont("Helvetica",7)
1530:                 c.drawString(xx+58,yy,val[:58])
1531:             return box_y-12
1532:         return info_top-6
1533: 
1534:     def _report_footer(self, c, page_no, page_size=A4):
1535:         W,H=page_size
1536:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1537:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1538:         c.drawString(24,13,REPORT_FOOTER)
1539:         c.drawRightString(W-24,13,f"Page {page_no}")
1540:         c.setFillColorRGB(0,0,0)
1541: 
1542:     def _grr_signature_block(self, c, y, page_size=A4):
1543:         """Draw the three requested transaction-document signature lines."""
1544:         W,H=page_size
1545:         labels=["Prepared By","Store Keeper","Store Incharge"]
1546:         block_h=70
```
```text
1553:             x=left+i*col_w
1554:             c.setLineWidth(0.6)
1555:             c.line(x+30,top-34,x+col_w-30,top-34)
1556:             c.setFont("Helvetica-Bold",7)
1557:             c.drawCentredString(x+col_w/2,top-48,label)
1558:         return True
1559: 
1560:     def _finish_page(self, c, page_no, page_size=A4):
1561:         self._report_footer(c,page_no,page_size); c.showPage()
1562: 
1563:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1564:         """Word-wrap `text` into a list of lines that each fit inside
1565:         max_width (points) at the given font, breaking mid-word only when a
1566:         single word is itself wider than the column."""
1567:         text=str(text) if text is not None else ""
1568:         if not text:
1569:             return [""]
1570:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1571:         lines=[]; cur=""
1572:         for word in text.split(" "):
1573:             trial=(cur+" "+word).strip() if cur else word
```
```text
1582:                     mid=(lo+hi)//2
1583:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1584:                     else: hi=mid-1
1585:                 lines.append(w[:fit_at]); w=w[fit_at:]
1586:             cur=w
1587:         if cur: lines.append(cur)
1588:         return lines or [""]
1589: 
1590:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1591:         """Create a paginated professional PDF with logo, bordered information,
1592:         GRR signature lines and page numbers. Also keep the same report data in
1593:         memory so the built-in Windows printer dialog can print directly without
1594:         requiring a PDF application's PrintTo association."""
1595:         if not hasattr(self, "_print_jobs"):
1596:             self._print_jobs = {}
1597:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1598:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1599:         page=1
1600:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1601:         usable=W-56
1602:         n=max(1,len(headers))
```
```text
1624:             if desc_idx is not None and desc_idx < len(r):
1625:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1626:             else:
1627:                 desc_lines=[""]
1628:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1629:             # Reserve room on the final page for the three transaction signatures + footer.
1630:             reserve=120 if is_transaction_doc else 42
1631:             if y-row_h<reserve:
1632:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1633:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1634:             # Item rows are intentionally border-free. The section/header remains
1635:             # professional while avoiding the unwanted boxed line around each
1636:             # individual printed item row. Description is drawn separately
1637:             # below (auto-fit / wrapped), so it is skipped in this pass.
1638:             for ci,(xx,val) in enumerate(zip(xs,r)):
1639:                 if ci==desc_idx: continue
1640:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1641:             if desc_idx is not None and desc_idx < len(r):
1642:                 for li,ln in enumerate(desc_lines):
1643:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1644:             y-=row_h
```
```text
1639:                 if ci==desc_idx: continue
1640:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1641:             if desc_idx is not None and desc_idx < len(r):
1642:                 for li,ln in enumerate(desc_lines):
1643:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1644:             y-=row_h
1645:         if is_transaction_doc:
1646:             # Keep the three requested transaction signatures at the physical bottom
1647:             # final page, immediately above the report footer.  If the item
1648:             # table reaches this reserved area, start a fresh final page.
1649:             bottom_sig_y = 138
1650:             if y < 165:
1651:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1652:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1653:             # Draw signatures at a fixed bottom position so they never float
1654:             # directly after the last item row.
1655:             self._grr_signature_block(c,bottom_sig_y,page_size)
1656:         self._report_footer(c,page,page_size); c.save()
1657:         if auto_print:
1658:             self.print_pdf(path)
1659:         return path
```
```text
1653:             # Draw signatures at a fixed bottom position so they never float
1654:             # directly after the last item row.
1655:             self._grr_signature_block(c,bottom_sig_y,page_size)
1656:         self._report_footer(c,page,page_size); c.save()
1657:         if auto_print:
1658:             self.print_pdf(path)
1659:         return path
1660: 
1661:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1662:         """Professional on-screen preview showing bordered document information
1663:         and a bordered item section. GRN Date is displayed in the right column."""
1664:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1665:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1666:         # Preview intentionally hides the company logo and company name.
1667:         # The actual generated/printed PDF still contains both via
1668:         # _report_header(), so only the on-screen preview is affected.
1669:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1670:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1671:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1672: 
1673:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
```
```text
1694:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1695: 
1696:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1697:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1698:         tr=self.make_tree(items,columns,widths)
1699:         for r in rows: tr.insert("", "end", values=r)
1700: 
1701:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1702:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1703:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1704:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1705:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1706:         win.bind("<Control-f>",bind_preview_find)
1707:         win.bind("<Control-F>",bind_preview_find)
1708: 
1709:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1710:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1711:         if is_transaction_preview:
1712:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1713:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1714:                 sig.columnconfigure(i,weight=1)
```
```text
1712:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1713:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1714:                 sig.columnconfigure(i,weight=1)
1715:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1716:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1717:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1718: 
1719:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1720:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1721:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1722:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1723:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1724:         if on_save:
1725:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1726:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1727:         if not is_transaction_preview:
1728:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1729:         # IMPORTANT: this must remain a normal top-level window (not transient
1730:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1731:         # exactly like the Preview Report window in the supplied recording.
1732:         # The Find dialog is opened from this window and is independent.
```
```text
1725:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1726:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1727:         if not is_transaction_preview:
1728:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1729:         # IMPORTANT: this must remain a normal top-level window (not transient
1730:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1731:         # exactly like the Preview Report window in the supplied recording.
1732:         # The Find dialog is opened from this window and is independent.
1733:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1734:         win.focus_force()
1735: 
1736:     def _safe_report_name(self, title, extension):
1737:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1738:         safe=safe.replace(" ","_") or "Preview"
1739:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1740: 
1741:     def print_preview_window(self, title, header_lines, columns, rows):
1742:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1743:         self._open_direct_printer(title, header_lines, columns, rows,
1744:                                   landscape(A4) if len(columns) > 8 else A4)
1745: 
```
```text
1738:         safe=safe.replace(" ","_") or "Preview"
1739:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1740: 
1741:     def print_preview_window(self, title, header_lines, columns, rows):
1742:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1743:         self._open_direct_printer(title, header_lines, columns, rows,
1744:                                   landscape(A4) if len(columns) > 8 else A4)
1745: 
1746:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1747:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1748:         This keeps the Export PDF button functional on a machine where the bundled
1749:         ReportLab package cannot be imported."""
1750:         def esc(v):
1751:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1752:         W,H=842,595
1753:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1754:         def add(txt,size=8,leading=11):
1755:             lines.append(f"/F1 {size} Tf")
1756:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1757:         add(str(title),12,16)
1758:         for h in header_lines or []:
```
```text
1765:         lines.append("ET")
1766:         stream="\n".join(lines).encode("latin-1","replace")
1767:         objs=[]
1768:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1769:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1770:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1771:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1772:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1773:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1774:         for i,obj in enumerate(objs,1):
1775:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1776:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1777:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1778:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1779:         with open(path,"wb") as f: f.write(out)
1780: 
1781:     def export_preview_pdf(self, title, header_lines, columns, rows):
1782:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1783:         try:
1784:             os.makedirs(REPORTS_DIR, exist_ok=True)
1785:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
```
```text
1778:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1779:         with open(path,"wb") as f: f.write(out)
1780: 
1781:     def export_preview_pdf(self, title, header_lines, columns, rows):
1782:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1783:         try:
1784:             os.makedirs(REPORTS_DIR, exist_ok=True)
1785:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1786:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1787:             generated = False
1788:             if REPORTLAB:
1789:                 try:
1790:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1791:                     generated = True
1792:                 except Exception:
1793:                     generated = False
1794:             if not generated:
1795:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1796:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1797:                 raise IOError("The PDF file was not created in the Reports folder.")
1798:             with open(path, "rb") as pf:
```
```text
1792:                 except Exception:
1793:                     generated = False
1794:             if not generated:
1795:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1796:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1797:                 raise IOError("The PDF file was not created in the Reports folder.")
1798:             with open(path, "rb") as pf:
1799:                 signature = pf.read(5)
1800:             if signature != b"%PDF-":
1801:                 raise IOError("The generated file is not a valid PDF.")
1802:             self._last_report_path = path
1803:             try:
1804:                 webbrowser.open("file://" + path)
1805:             except Exception:
1806:                 self.open_file(path)
1807:             return path
1808:         except Exception as e:
1809:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1810:             return None
1811: 
1812:     def export_preview_word(self, title, header_lines, columns, rows):
```
```text
1808:         except Exception as e:
1809:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1810:             return None
1811: 
1812:     def export_preview_word(self, title, header_lines, columns, rows):
1813:         """Export exactly what is visible in the current preview to Word."""
1814:         if not DOCX_AVAILABLE:
1815:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1816:         path=self._safe_report_name(title,"docx")
1817:         doc=Document()
1818:         sec=doc.sections[0]
1819:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1820:         sec.header.paragraphs[0].runs[0].bold=True
1821:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1822:         fp=sec.footer.paragraphs[0]
1823:         fp.alignment=2
1824:         if not is_transaction_preview:
1825:             fp.add_run("Authorized Signatory: ____________________    Store In-Charge: ____________________    Page ")
1826:             fld=fp.add_run(); fld._r.append(__import__('docx').oxml.OxmlElement('w:fldChar')); fld._r[-1].set(__import__('docx').oxml.ns.qn('w:fldCharType'),'begin')
1827:             instr=__import__('docx').oxml.OxmlElement('w:instrText'); instr.text='PAGE'; fld._r.append(instr)
1828:             fld2=__import__('docx').oxml.OxmlElement('w:fldChar'); fld2.set(__import__('docx').oxml.ns.qn('w:fldCharType'),'end'); fld._r.append(fld2)
```
```text
1843:             doc.add_paragraph("")
1844:             sig=doc.add_table(rows=2,cols=3)
1845:             labels=["Prepared By","Store Keeper","Store Incharge"]
1846:             for i,label in enumerate(labels):
1847:                 sig.cell(0,i).text="____________________"
1848:                 sig.cell(1,i).text=label
1849:                 for para in sig.cell(1,i).paragraphs:
1850:                     for run in para.runs: run.bold=True
1851:         doc.save(path)
1852:         self.open_file(path)
1853: 
1854:     def export_preview_excel(self, title, header_lines, columns, rows):
1855:         """Export exactly what is visible in the current preview to Excel."""
1856:         if not XLSX_AVAILABLE:
1857:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
1858:         path=self._safe_report_name(title,"xlsx")
1859:         wb=openpyxl.Workbook(); ws=wb.active
1860:         ws.title="Preview"
1861:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
1862:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1863:         if not is_transaction_preview:
```
```text
1881:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
1882:             for col in range(1,4):
1883:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
1884:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
1885:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
1886:         for col_cells in ws.columns:
1887:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
1888:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
1889:         wb.save(path)
1890:         self.open_file(path)
1891: 
1892:     def make_tree(self,parent,cols,widths=None):
1893:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
1894:         tr=ttk.Treeview(fr,columns=cols,show="headings")
1895:         for i,c in enumerate(cols):
1896:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
1897:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
1898:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
1899:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
1900:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
1901:         return tr
```
```text
1954:                     w.state(["!disabled"] if editable else ["disabled"])
1955:             except Exception:
1956:                 try: w.configure(state="normal" if editable else "disabled")
1957:                 except Exception: pass
1958:             for ch in w.winfo_children(): walk(ch)
1959:         for root in roots: walk(root)
1960: 
1961:     def document_selector(self, parent, label, typ, var, load_callback):
1962:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
1963:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
1964:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
1965:         combo.pack(side="left", padx=4)
1966:         def refresh():
1967:             vals=[]
1968:             if typ=="demand":
1969:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
1970:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
1971:             elif typ=="grr":
1972:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
1973:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
1974:             else:
```
```text
1981:             no=text.split(" -> ",1)[0].strip()
1982:             var.set(no)
1983:             load_callback(no)
1984:         combo.bind("<<ComboboxSelected>>", selected)
1985:         combo.bind("<Return>", selected)
1986:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
1987:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
1988:         refresh()
1989:         # Keep the currently open transaction's saved-record list live.
1990:         # Each save calls refresh_saved_cache(), so newly saved records appear
1991:         # immediately without closing/reopening the window or pressing Refresh.
1992:         if not hasattr(self, "_document_selector_refreshers"):
1993:             self._document_selector_refreshers = {}
1994:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
1995:         return combo
1996: 
1997:     def dashboard(self):
1998:         # Dashboard-only visual refresh. All existing data queries, filters,
1999:         # callbacks and report/detail behavior are intentionally preserved.
2000:         self.clearbody()
2001:         c=self.conn
```
```text
2080:             for x in tr.get_children(): tr.delete(x)
2081:             params=[];where=[]
2082:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2083:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2084:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2085:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2086:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2087:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2088:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2089:                    FROM transactions t JOIN items i ON i.code=t.code"""
2090:             if where: sql += " WHERE " + " AND ".join(where)
2091:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2092:             rows=list(c.execute(sql,params))
2093:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2094:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2095:             bal_after={}
2096:             for txid,cc,typ,qty in alltx:
2097:                 running.setdefault(cc,0.0)
2098:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2099:                 bal_after[txid]=running[cc]
2100:             for r in rows:
```
```text
2458:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2459:         load()
2460:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2461: 
2462:     def inventory_codes(self):
2463:         """Inventory Codes using the classic desktop inventory interface.
2464: 
2465:         This screen intentionally follows the uploaded Inventory Management
2466:         reference: a simple module title, compact New/Edit/Delete/Save/
2467:         Refresh/Print/Close action row, and a full-width editable data grid.
2468:         All records come from the V18 database, so existing inventory data is
2469:         preserved rather than recreated.
2470:         """
2471:         self.clearbody()
2472:         # Remove the generic SAP action row; this page owns its own classic
2473:         # action row just like the reference Inventory/Items screen.
2474:         if self.body.winfo_children():
2475:             try:
2476:                 self.body.winfo_children()[0].destroy()
2477:             except Exception:
2478:                 pass
```
```text
2531:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2532:         if filter_text:
2533:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2534:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2535: 
2536:         editing={"id":None,"new":False}
2537:         cell_editor={"widget":None}
2538: 
2539:         def close_editor(save_value=False):
2540:             w=cell_editor.get("widget")
2541:             if not w:
2542:                 return
2543:             try:
2544:                 if save_value:
2545:                     w.event_generate("<Return>")
2546:                 w.destroy()
2547:             except Exception:
2548:                 pass
2549:             cell_editor["widget"]=None
2550: 
2551:         def edit_cell(event=None):
```
```text
2561:             bbox=tree.bbox(iid,colid)
2562:             if not bbox: return
2563:             close_editor(False)
2564:             x,y,w,h=bbox
2565:             val=str(tree.item(iid,"values")[idx] or "")
2566:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2567:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2568:             cell_editor["widget"]=e
2569:             def commit(_=None):
2570:                 try:
2571:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2572:                 finally:
2573:                     try:e.destroy()
2574:                     except Exception:pass
2575:                     cell_editor["widget"]=None
2576:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2577:             e.bind("<FocusOut>",commit)
2578: 
2579:         def rows_query():
2580:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2581:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2583:             if tc: where.append("code <= ?"); params.append(tc)
2584:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2585:             if df or dt:
2586:                 sub=[]; sp=[]
2587:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2588:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2589:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2590:                 params.extend(sp)
2591:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2592:             return sql,params
2593: 
2594:         def load():
2595:             close_editor(False)
2596:             for i in tree.get_children(): tree.delete(i)
2597:             sql,params=rows_query()
2598:             count=0
2599:             for r in self.conn.execute(sql,params):
2600:                 # V18 stores UOM/opening and the original application may have
2601:                 # rate/remarks columns in some versions. Read them safely.
2602:                 rid,code,desc,uom,opening,rate,remarks=r
2603:                 bal=stock(self.conn,code)
```
```text
2617:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2618:             editing["id"]=None; editing["new"]=True
2619:             # Put the user directly into the Code cell.
2620:             try:
2621:                 bbox=tree.bbox(iid,"#2")
2622:                 if bbox:
2623:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2624:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2625:                     def commit(_=None):
2626:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2627:                         try:e.destroy()
2628:                         except Exception:pass
2629:                         cell_editor["widget"]=None
2630:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2631:             except Exception: pass
2632:             status.set("New row added — enter values, then press Save")
2633: 
2634:         def selected_row():
2635:             a=tree.selection()
2636:             return a[0] if a else None
2637: 
```
```text
2637: 
2638:         def edit_record():
2639:             iid=selected_row()
2640:             if not iid:
2641:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2642:             if not self.can_edit and not self.is_admin:
2643:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2644:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2645:             status.set("Edit mode — double-click any cell to change it, then press Save")
2646:             tree.focus(iid); tree.see(iid)
2647: 
2648:         def save_record():
2649:             iid=selected_row()
2650:             if not iid:
2651:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2652:             if not self.can_edit and not self.is_admin:
2653:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2654:             close_editor(True)
2655:             vals=list(tree.item(iid,"values"))
2656:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2657:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2655:             vals=list(tree.item(iid,"values"))
2656:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2657:             try: opening=float(str(vals[4]).strip() or 0)
2658:             except Exception: raise ValueError("Opening Qty must be a number.")
2659:             try: rate=float(str(vals[5]).strip() or 0)
2660:             except Exception: raise ValueError("Rate must be a number.")
2661:             remarks=str(vals[6]).strip()
2662:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2663:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2664:             if not desc:
2665:                 messagebox.showerror("Save","Description is required."); return
2666:             if opening<0:
2667:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2668:             rid=vals[0]
2669:             try:
2670:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2671:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2672:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2673:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2674:                 if rid:
2675:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2678:                                       (code,desc,uom,opening,rid))
2679:                     if oldcode!=code:
2680:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2681:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2682:                             except Exception:pass
2683:                 else:
2684:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2685:                                       (code,desc,uom,"",opening,0,"Local",0))
2686:                 self.conn.commit(); backup_database(); load()
2687:                 messagebox.showinfo("Saved","Inventory Code saved successfully.")
2688:             except Exception as ex:
2689:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2690: 
2691:         def delete_record():
2692:             iid=selected_row()
2693:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2694:             if not self.can_delete and not self.is_admin:
2695:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2696:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2697:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2698:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
```
```text
2692:             iid=selected_row()
2693:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2694:             if not self.can_delete and not self.is_admin:
2695:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2696:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2697:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2698:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2699:             try:
2700:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2701:             except Exception as ex:
2702:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2703: 
2704:         def refresh(): load()
2705:         def do_print():
2706:             try:self.preview_tree("Inventory Codes",tree)
2707:             except Exception as ex:messagebox.showerror("Print",str(ex))
2708:         def do_close(): self.dashboard()
2709: 
2710:         btn("New",new_record,8)
2711:         btn("Edit",edit_record,8)
2712:         btn("Delete",delete_record,8)
```
```text
2705:         def do_print():
2706:             try:self.preview_tree("Inventory Codes",tree)
2707:             except Exception as ex:messagebox.showerror("Print",str(ex))
2708:         def do_close(): self.dashboard()
2709: 
2710:         btn("New",new_record,8)
2711:         btn("Edit",edit_record,8)
2712:         btn("Delete",delete_record,8)
2713:         btn("Save",save_record,8)
2714:         btn("Refresh",refresh,9)
2715:         btn("Preview",do_print,8)
2716:         btn("Print",do_print,8)
2717:         btn("Close",do_close,8)
2718: 
2719:         # Search is deliberately small and sits on the right, without changing
2720:         # the reference layout of the action buttons.
2721:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2722:         search=tk.StringVar()
2723:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2724:         se.pack(side="left",padx=2)
2725:         self._item_master_search_entry=se
```
```text
2733:                     tree.detach(iid)
2734:         search.trace_add("write",filter_grid)
2735:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2736: 
2737:         tree.bind("<Double-1>",edit_cell)
2738:         tree.bind("<F2>",lambda e: edit_record())
2739:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2740:         self._page_actions={
2741:             "save":save_record,"edit":edit_record,"delete":delete_record,
2742:             "cancel":do_close,"print":do_print,"preview":do_print
2743:         }
2744:         load()
2745: 
2746:     def open_mto_inventory_flow(self):
2747:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2748: 
2749:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2750:         Cancel/X only closes the popup.
2751:         """
2752:         criteria = self._ask_mto_inventory_filters()
2753:         if not criteria or criteria.get("cancelled"):
```
```text
2915:                 return False
2916:             destination.set(found_dest)
2917:             edit_mode.update(on=True, original=r[0], dest=found_dest)
2918:             code.set(r[0])
2919:             desc.set(r[1] or "")
2920:             uom.set(r[2] or UOM_OPTIONS[0])
2921:             opening.set(str(r[3] if r[3] is not None else 0))
2922:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
2923:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
2924:             err.set("")
2925:             edit_btn.configure(text="SAVE EDIT")
2926:             ce.focus_set()
2927:             return True
2928: 
2929:         def check_duplicates(*_):
2930:             c = code.get().strip()
2931:             d = desc.get().strip()
2932:             dest = destination.get()
2933:             msgs = []
2934:             r = row_for(dest, c) if len(norm(c)) == 8 else None
2935:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
2937:             dh = desc_hit(dest, d) if d else None
2938:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
2939:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
2940:             hint.set("\n".join(msgs))
2941: 
2942:         code.trace_add("write", check_duplicates)
2943:         desc.trace_add("write", check_duplicates)
2944: 
2945:         def save_code():
2946:             try:
2947:                 c = code.get().strip()
2948:                 d = desc.get().strip()
2949:                 u = uom.get().strip()
2950:                 dest = destination.get()
2951:                 digits = norm(c)
2952:                 if len(digits) != 8:
2953:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
2954:                 if not d:
2955:                     raise ValueError("Description is required.")
2956:                 try:
2957:                     op = float(opening.get().strip() or 0)
```
```text
2978:                         (c, d, u, op, iso, old)
2979:                     )
2980:                     action = "updated"
2981:                 else:
2982:                     self.conn.execute(
2983:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
2984:                         (c, d, u, "", op, 0, iso)
2985:                     )
2986:                     action = "saved"
2987:                 self.conn.commit()
2988:                 backup_database()
2989:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
2990:                 # Keep popup open for fast multiple entries.
2991:                 clear_form(keep_search=False)
2992:                 ce.focus_set()
2993:             except Exception as ex:
2994:                 self.conn.rollback()
2995:                 err.set(str(ex))
2996:                 messagebox.showerror("Code Opening", str(ex), parent=win)
2997: 
2998:         def edit_action():
```
```text
2994:                 self.conn.rollback()
2995:                 err.set(str(ex))
2996:                 messagebox.showerror("Code Opening", str(ex), parent=win)
2997: 
2998:         def edit_action():
2999:             if not edit_mode["on"]:
3000:                 load_for_edit()
3001:             else:
3002:                 save_code()
3003: 
3004:         def delete_code():
3005:             if not edit_mode["on"]:
3006:                 if not load_for_edit():
3007:                     return
3008:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3009:                 return
3010:             try:
3011:                 t = table_for(edit_mode["dest"])
3012:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3013:                 self.conn.commit()
3014:                 backup_database()
```
```text
3010:             try:
3011:                 t = table_for(edit_mode["dest"])
3012:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3013:                 self.conn.commit()
3014:                 backup_database()
3015:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3016:                 clear_form(keep_search=False)
3017:             except Exception as ex:
3018:                 self.conn.rollback()
3019:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3020: 
3021:         btns = ttk.Frame(box)
3022:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3023:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3024:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3025:         edit_btn.pack(side="left", padx=4, ipadx=8)
3026:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3027:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3028:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3029:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3030:         ce.focus_set()
```
```text
3024:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3025:         edit_btn.pack(side="left", padx=4, ipadx=8)
3026:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3027:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3028:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3029:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3030:         ce.focus_set()
3031: 
3032:     def _mto_new_item_dialog(self, on_saved):
3033:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3034:         brand-new item can be created without leaving that screen. Writes
3035:         straight into the same Item Master (items table) used everywhere."""
3036:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3037:         win.transient(self); win.grab_set()
3038:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3039:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3040:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3041:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3042:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3043:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3044:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3040:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3041:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3042:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3043:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3044:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3045:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3046:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3047:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3048:         def save():
3049:             try:
3050:                 c=code.get().strip(); d=desc.get().strip()
3051:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3052:                 if not d: raise ValueError("Description is required.")
3053:                 try:
3054:                     opening_val=float(opening.get() or 0)
3055:                 except ValueError:
3056:                     raise ValueError("Opening Qty must be a number.")
3057:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3058:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3059:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3060:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3053:                 try:
3054:                     opening_val=float(opening.get() or 0)
3055:                 except ValueError:
3056:                     raise ValueError("Opening Qty must be a number.")
3057:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3058:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3059:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3060:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3061:                 self.conn.commit(); backup_database()
3062:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3063:                 win.grab_release(); win.destroy()
3064:                 on_saved()
3065:             except Exception as ex: messagebox.showerror("Error",str(ex))
3066:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3067:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3068:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3069: 
3070:     def _item_filter_bar(self, parent, on_change):
3071:         """Item Code entry + item-master picker + Search/Show All. Calls
3072:         on_change() whenever the code changes or a button is pressed."""
3073:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3159:         self._item_master_find_callback=None
3160:         self._portable_print_context=None
3161:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3162:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3163:         }
3164: 
3165:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3166:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3167:         self.conn.commit()
3168: 
3169:         # ---- Same professional in-app window layout as Inventory Codes ----
3170:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3171:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3172:                   foreground=COLORS["primary_dark"]).pack(side="left")
3173:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3174: 
3175:         def open_find():
3176:             state_find={"index":-1}
3177:             def search_fn(text):
3178:                 text=text.strip().lower()
3179:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3266:             for i in table.get_children(): table.delete(i)
3267:             where=["1=1"]; params=[]
3268:             prefix=state.get("prefix",""); q=search.get().strip()
3269:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3270:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3271:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3272:             if fc: where.append("code >= ?"); params.append(fc)
3273:             if tc: where.append("code <= ?"); params.append(tc)
3274:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3275:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3276:             records=[]
3277:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3278:                 # If a date filter is supplied, accept an opening-date match OR
3279:                 # a transaction in that date range. This prevents valid MTO codes
3280:                 # from disappearing merely because an older record has no opening_date.
3281:                 if df or dt:
3282:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3283:                     if not ok:
3284:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3285:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3286:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3356:                 tr.insert("", "end", values=r)
3357:         def clear():
3358:             for x in v.values(): x.set("")
3359:             try: tr.selection_remove(tr.selection())
3360:             except Exception: pass
3361:             self._set_form_editable(party_form_roots, False)
3362:         def new_form():
3363:             clear(); self._set_form_editable(party_form_roots, True)
3364:         def save():
3365:             try:
3366:                 name=v["name"].get().strip()
3367:                 if not name: raise ValueError("Party Name is required.")
3368:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3369:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3370:             except Exception as ex: messagebox.showerror("Error",str(ex))
3371:         def load_party_row(a):
3372:             if not a:return
3373:             r=tr.item(a[0])["values"]
3374:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3375:             self._set_form_editable(party_form_roots, False)
3376:         def on_party_select(_=None):
```
```text
3382:             load_party_row(a)
3383:             self._set_form_editable(party_form_roots, True)
3384:         def delete_party():
3385:             a=tr.selection()
3386:             if not a:
3387:                 messagebox.showwarning("Delete", "Select a party first."); return
3388:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3389:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3390:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3391:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3392:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3393:         self._add_transaction_new_button(new_form)
3394:         load(); clear()
3395: 
3396:     def user_management(self):
3397:         self.clearbody()
3398:         if not self.is_admin:
3399:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3400:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3401:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3402:         role=tk.StringVar(value="User")
```
```text
3439:             u_ent.state(["!disabled"])
3440:         def edit():
3441:             a=tr.selection()
3442:             if not a:
3443:                 messagebox.showwarning("Edit User","Select a user row first."); return
3444:             r=tr.item(a[0])["values"]
3445:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3446:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3447:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3448:         def save():
3449:             try:
3450:                 username=v["username"].get().strip()
3451:                 if not username: raise ValueError("Username is required.")
3452:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3453:                 pw=v["password"].get()
3454:                 if exists:
3455:                     pw_hash = hash_password(pw) if pw else exists[0]
3456:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3457:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3458:                 else:
3459:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3454:                 if exists:
3455:                     pw_hash = hash_password(pw) if pw else exists[0]
3456:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3457:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3458:                 else:
3459:                     if not pw: raise ValueError("Password is required for a new user.")
3460:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3461:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3462:                 self.conn.commit(); backup_database(); load(); clear()
3463:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3464:             except Exception as ex:
3465:                 messagebox.showerror("Error", str(ex))
3466:         def delete_user():
3467:             a=tr.selection()
3468:             if not a:
3469:                 messagebox.showwarning("Delete User","Select a user row first."); return
3470:             username=tr.item(a[0])["values"][0]
3471:             if username==self.current_user:
3472:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3473:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3474:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3469:                 messagebox.showwarning("Delete User","Select a user row first."); return
3470:             username=tr.item(a[0])["values"][0]
3471:             if username==self.current_user:
3472:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3473:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3474:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3475:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3476:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3477:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3478:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3479:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3480:         load()
3481: 
3482:     @staticmethod
3483:     def _renumber_tree(tree, rows):
3484:         for i,iid in enumerate(tree.get_children()):
3485:             vals=list(tree.item(iid,"values"));
3486:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3487: 
3488:     def demand(self):
3489:         self.clearbody(); self.demand_lines=[]
```
```text
3486:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3487: 
3488:     def demand(self):
3489:         self.clearbody(); self.demand_lines=[]
3490:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3491:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3492:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3493:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3494:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3495:         # Demand Date is intentionally displayed as its own dedicated field.
3496:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3497:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3498:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3499:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3500:                 ("special","Special Instructions"),("source","Recommended Source")]
3501:         for i,(k,n) in enumerate(fields):
3502:             r=i//4*2+3; c=i%4*2
3503:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3504:             if k=="dept":
3505:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3506:             elif k=="urgency":
```
```text
3576:         def new_form():
3577:             self._editing_document_key=None
3578:             for z in v.values(): z.set("")
3579:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3580:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3581:             for iid in tree.get_children(): tree.delete(iid)
3582:             self._set_form_editable(form_roots, True, skip=[selector])
3583: 
3584:         def save():
3585:             try:
3586:                 no=v["no"].get().strip()
3587:                 if not no: raise ValueError("Demand No is required.")
3588:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3589:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3590:                 if dup and getattr(self,"_editing_document_key",None) != no:
3591:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3592:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3593:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3594:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3595:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3596:                 self.conn.commit(); backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector]); messagebox.showinfo("Saved",f"Demand {no} saved successfully.")
```
```text
3596:                 self.conn.commit(); backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector]); messagebox.showinfo("Saved",f"Demand {no} saved successfully.")
3597:             except Exception as ex: messagebox.showerror("Error",str(ex))
3598:         form_roots=[f,line,editbar]
3599:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3600:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3601:         def delete_current():
3602:             no=v["no"].get().strip()
3603:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3604:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3605:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3606:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
3607:             self.demand(); messagebox.showinfo("Deleted",f"Demand {no} deleted.")
3608:         def cancel_form():
3609:             self._editing_document_key=None
3610:             self._set_form_editable(form_roots, False, skip=[selector])
3611:             for z in v.values(): z.set("")
3612:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3613:             itype.set("Local")
3614:             self.demand_lines.clear()
3615:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3616:             for iid in tree.get_children(): tree.delete(iid)
```
```text
3619:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3620:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3621:                     f"Justification: {v['just'].get()}",
3622:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3623:             if not self.demand_lines:
3624:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3625:             self.show_preview_window("Purchase Demand", header,
3626:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3627:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3628:         def edit_saved_demand():
3629:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3630:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3631:             self._set_form_editable(form_roots, True, skip=[selector])
3632:         def print_now():
3633:             if not self.demand_lines:
3634:                 messagebox.showwarning("Print","Add at least one item line first."); return
3635:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3636:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3637:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3638:                     f"Justification: {v['just'].get()}",
3639:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3635:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3636:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3637:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3638:                     f"Justification: {v['just'].get()}",
3639:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3640:             self._open_direct_printer("Purchase Demand",header,
3641:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3642:                 self.demand_lines,A4)
3643:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3644:         self._add_transaction_new_button(new_form)
3645:         self._set_form_editable(form_roots, False, skip=[selector])
3646:         try:
3647:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3648:         except Exception: pass
3649:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3650: 
3651:     def load_demand_into_form(self,no,v,tree):
3652:         v["no"].set(no)
3653:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3654:         if not r:return
3655:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3657:         self.demand_lines=[]
3658:         for i in tree.get_children():tree.delete(i)
3659:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3660:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3661:         roots=getattr(self,"_transaction_form_roots",None)
3662:         if roots and "demand" in roots:
3663:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3664: 
3665:     def refresh_saved_cache(self,typ):
3666:         # Refresh saved-document dropdowns immediately after a successful save.
3667:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3668:         alive=[]
3669:         for combo, refresh in refreshers:
3670:             try:
3671:                 if combo.winfo_exists():
3672:                     refresh()
3673:                     alive.append((combo, refresh))
3674:             except Exception:
3675:                 pass
3676:         if hasattr(self, "_document_selector_refreshers"):
3677:             self._document_selector_refreshers[typ] = alive
```
```text
3676:         if hasattr(self, "_document_selector_refreshers"):
3677:             self._document_selector_refreshers[typ] = alive
3678: 
3679:     def grr(self):
3680:         self.clearbody(); self.grr_lines=[]
3681:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3682:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3683:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3684:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3685:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3686:         for i,(k,n) in enumerate(fields):
3687:             r=i//4*2+2;c=i%4*2
3688:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3689:             if k=="department":
3690:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3691:             elif k=="supplier":
3692:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3693:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3694:             elif k=="date":
3695:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3696:             else:
```
```text
3745:         def new_form():
3746:             self._editing_document_key=None
3747:             for z in v.values(): z.set("")
3748:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3749:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3750:             for iid in tree.get_children(): tree.delete(iid)
3751:             self._set_form_editable(form_roots, True, skip=[selector])
3752: 
3753:         def save():
3754:             try:
3755:                 no=v["no"].get().strip()
3756:                 if not no:raise ValueError("GRN No is required.")
3757:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3758:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3759:                 if dup and getattr(self,"_editing_document_key",None) != no:
3760:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3761:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3762:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3763:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3764:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3765:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3762:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3763:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3764:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3765:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3766:                 for x in self.grr_lines:
3767:                     ltype=x[10] if len(x)>10 else "Local"
3768:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3769:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3770:                 self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("grr");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock.")
3771:             except Exception as ex:messagebox.showerror("Error",str(ex))
3772:         form_roots=[f,line,editbar]
3773:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3774:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3775:         def delete_current():
3776:             no=v["no"].get().strip()
3777:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3778:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3779:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3780:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3781:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3782:         def cancel_form():
```
```text
3801:                     ("Challan #", v['challan'].get()),
3802:                     ("Vehicle #", v['vehicle'].get()),
3803:                     ("Bill/Voucher #", v['bill'].get()),
3804:                     ("Reference", v['ref'].get()),
3805:                     ("Remarks", v['remarks'].get()),
3806:                     ("Total Value", fmt_num(total))]
3807:             self.show_preview_window("GRN Receipt", header,
3808:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3809:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3810:         def portable_current():
3811:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3812:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3813:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3814:         self._portable_print_context=portable_current
3815:         def edit_saved_grr():
3816:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3817:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
3818:             self._set_form_editable(form_roots, True, skip=[selector])
3819:         def print_now():
3820:             if not self.grr_lines:
3821:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
3825:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
3826:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
3827:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
3828:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
3829:                     ("Total Value", fmt_num(total))]
3830:             self._open_direct_printer("GRN Receipt",header,
3831:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3832:                 self.grr_lines,landscape(A4))
3833:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3834:         self._add_transaction_new_button(new_form)
3835:         self._set_form_editable(form_roots, False, skip=[selector])
3836:         try:
3837:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3838:         except Exception: pass
3839:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
3840: 
3841:     def load_grr_into_form(self,no,v,tree):
3842:         v["no"].set(no)
3843:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
3844:         if not r:return
3845:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
3852:         if roots and "grr" in roots:
3853:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
3854: 
3855:     def issue(self):
3856:         self.clearbody(); self.issue_lines=[]
3857:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
3858:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
3859:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3860:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
3861:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
3862:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
3863:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3864:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3865:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
3866:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
3867:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
3868:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
3869:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
3870:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
3871:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
3872:         itype=tk.StringVar(value="Local")
```
```text
3941:                 # Editing an existing issue replaces its old stock transaction and detail lines.
3942:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
3943:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
3944:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
3945:                 for x in self.issue_lines:
3946:                     ltype=x[7] if len(x)>7 else "Local"
3947:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
3948:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
3949:                 self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("issue");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock.")
3950:             except Exception as ex:messagebox.showerror("Error",str(ex))
3951:         def delete_current():
3952:             no=v["no"].get().strip()
3953:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
3954:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
3955:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
3956:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
3957:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
3958:         def cancel_form():
3959:             self._editing_document_key=None
3960:             self._set_form_editable(form_roots, False, skip=[selector])
3961:             for z in v.values(): z.set("")
```
```text
3966:             for iid in tree.get_children(): tree.delete(iid)
3967:         def preview_now():
3968:             if not self.issue_lines:
3969:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3970:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3971:                     f"Items Use For: {v['items_use_for'].get()}"]
3972:             self.show_preview_window("Material Issue", header,
3973:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
3974:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
3975:         def portable_current():
3976:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
3977:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
3978:         self._portable_print_context=portable_current
3979:         form_roots=[f,usebar,line,editbar]
3980:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3981:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
3982:         def load_saved_issue(no):
3983:             self.load_issue_into_form(no,v,tree)
3984:             self._set_form_editable(form_roots, False, skip=[selector])
3985:         def edit_saved_issue():
3986:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
3979:         form_roots=[f,usebar,line,editbar]
3980:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3981:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
3982:         def load_saved_issue(no):
3983:             self.load_issue_into_form(no,v,tree)
3984:             self._set_form_editable(form_roots, False, skip=[selector])
3985:         def edit_saved_issue():
3986:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3987:             self._edit_from_selector("issue", v["no"], load_saved_issue)
3988:             self._set_form_editable(form_roots, True, skip=[selector])
3989:         def print_issue_now():
3990:             if not self.issue_lines:
3991:                 messagebox.showwarning("Print","Add at least one item line first."); return
3992:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
3993:             self._open_direct_printer("Material Issue",header,
3994:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
3995:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
3996:         self._add_transaction_new_button(new_form)
3997:         self._set_form_editable(form_roots, False, skip=[selector])
3998:         self._active_form_loader = load_saved_issue
3999: 
```
```text
4007:         for i in tree.get_children():tree.delete(i)
4008:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4009:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4010:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4011:         roots=getattr(self,"_transaction_form_roots",None)
4012:         if roots and "issue" in roots:
4013:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4014: 
4015:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4016:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4017: 
4018:         The layout intentionally matches Inventory Codes' Selection Criteria
4019:         popup so all Report sub-sections have one consistent desktop workflow.
4020:         """
4021:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4022:         win=tk.Toplevel(self)
4023:         win.title(f"{report_title} - Selection Criteria")
4024:         win.resizable(False,False)
4025:         win.transient(self); win.grab_set()
4026:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4027:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4072:             except Exception: pass
4073:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4074:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4075:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4076:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4077:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4078:         e1.focus_set(); self.wait_window(win); return result
4079: 
4080:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4081:         self._pending_report_filters=criteria
4082:         try:
4083:             return self.open_menu_window(method,title,geometry)
4084:         finally:
4085:             self._pending_report_filters=None
4086: 
4087:     def open_stock_balance_report_flow(self):
4088:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4089:         if f.get("cancelled"): return None
4090:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4091: 
4092:     def open_grr_report_flow(self):
```
```text
4085:             self._pending_report_filters=None
4086: 
4087:     def open_stock_balance_report_flow(self):
4088:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4089:         if f.get("cancelled"): return None
4090:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4091: 
4092:     def open_grr_report_flow(self):
4093:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4094:         if f.get("cancelled"): return None
4095:         return self._open_report_child(self.report_grr,"GRN Report",f)
4096: 
4097:     def open_demand_report_flow(self):
4098:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4099:         if f.get("cancelled"): return None
4100:         return self._open_report_child(self.report_demand,"Demand Report",f)
4101: 
4102:     def open_issue_report_flow(self):
4103:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4104:         if f.get("cancelled"): return None
4105:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4099:         if f.get("cancelled"): return None
4100:         return self._open_report_child(self.report_demand,"Demand Report",f)
4101: 
4102:     def open_issue_report_flow(self):
4103:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4104:         if f.get("cancelled"): return None
4105:         return self._open_report_child(self.report_issue,"Issue Report",f)
4106: 
4107:     def open_party_report_flow(self):
4108:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4109:         if f.get("cancelled"): return None
4110:         return self._open_report_child(self.report_party,"Party Report",f)
4111: 
4112:     def _ask_stock_balance_filters(self):
4113:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4114:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4115:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4116:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4117:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4118:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4119:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4131:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4132:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4133:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4134:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4135:         e1.focus_set();self.wait_window(win);return result
4136: 
4137:     def stock_balance(self):
4138:         self.clearbody()
4139:         # Stock Balance is a Report sub-section and does not use the generic
4140:         # Save/Edit/Delete/Cancel/Print action strip.
4141:         children=self.body.winfo_children()
4142:         if children:
4143:             children[0].destroy()
4144:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4145:         if initial.get("cancelled"):
4146:             self.dashboard(); return
4147:         top=ttk.Frame(self.body);top.pack(fill="x")
4148:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4149:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4150:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4151:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4161:             for typ,qty in self.conn.execute(q,params):
4162:                 if typ=="GRR":gr+=float(qty or 0)
4163:                 elif typ=="ISSUE":iss+=float(qty or 0)
4164:             return opening_before,gr,iss,opening_before+gr-iss
4165:         def header_summary():
4166:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4167:         def load():
4168:             for i in tr.get_children():tr.delete(i)
4169:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4170:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4171:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4172:             sql+=" ORDER BY code"
4173:             for r in self.conn.execute(sql,params):
4174:                 op,gr,iss,cur=period(r[0],r[3])
4175:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4176:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4177:         def reopen_filters():
4178:             initial2=self._ask_stock_balance_filters()
4179:             if initial2.get("cancelled"):return
4180:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4181:             load()
```
```text
4219:         """
4220:         if typ=="demand": self.demand()
4221:         elif typ=="grr": self.grr()
4222:         else: self.issue()
4223:         loader=getattr(self,"_active_form_loader",None)
4224:         if loader: loader(str(no))
4225: 
4226:     def _edit_from_selector(self, typ, var, loader):
4227:         """Top Edit action: load the saved document directly into the current form.
4228:         If nothing is selected, use the newest saved document; never open a popup.
4229:         """
4230:         text=var.get().strip()
4231:         if text:
4232:             no=text.split(" -> ",1)[0].strip()
4233:         else:
4234:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4235:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4236:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4237:             if not r:
4238:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4239:                 return
```
```text
4236:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4237:             if not r:
4238:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4239:                 return
4240:             no=str(r[0])
4241:             var.set(no)
4242:         loader(no)
4243: 
4244:     def show_saved_records(self,typ):
4245:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4246:         if typ=="demand":
4247:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4248:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4249:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4250:             for r in rows:
4251:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4252:                 r=list(r); r[1]=to_display_date(r[1])
4253:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4254:         elif typ=="grr":
4255:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4256:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4267:         def view():
4268:             a=tr.selection()
4269:             if not a:return
4270:             no=tr.item(a[0])["values"][0]
4271:             win.destroy();self.open_document_editor(typ,no)
4272:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4273:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4274:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4275:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4276: 
4277:     def documents(self):
4278:         self.clearbody()
4279:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4280:         specs=[
4281:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4282:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4283:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4284:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4285:             ("Material Issues","issue",("No","Date","Department"),
4286:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4287:         ]
```
```text
4283:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4284:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4285:             ("Material Issues","issue",("No","Date","Department"),
4286:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4287:         ]
4288:         for title,typ,cols,query in specs:
4289:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4290:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4291:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4292:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4293:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4294:             for r in self.conn.execute(query):
4295:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4296:             def edit_selected(t=tr,k=typ):
4297:                 a=t.selection()
4298:                 if not a:
4299:                     messagebox.showwarning("Edit", "Select a saved record first.")
4300:                     return
4301:                 no=t.item(a[0])["values"][0]
4302:                 self.open_document_editor(k,no)
4303:             def delete_selected(t=tr,k=typ):
```
```text
4298:                 if not a:
4299:                     messagebox.showwarning("Edit", "Select a saved record first.")
4300:                     return
4301:                 no=t.item(a[0])["values"][0]
4302:                 self.open_document_editor(k,no)
4303:             def delete_selected(t=tr,k=typ):
4304:                 a=t.selection()
4305:                 if not a:
4306:                     messagebox.showwarning("Delete", "Select a saved record first.")
4307:                     return
4308:                 no=t.item(a[0])["values"][0]
4309:                 if k=="demand":
4310:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4311:                 elif k=="grr":
4312:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4313:                 else:
4314:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4315:                 self.conn.commit();backup_database();self.documents()
4316:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4317:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4318:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4312:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4313:                 else:
4314:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4315:                 self.conn.commit();backup_database();self.documents()
4316:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4317:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4318:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4319:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4320:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4321:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4322:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4323: 
4324:     def doc_export_selected(self,typ,tr,fmt):
4325:         a=tr.selection()
4326:         if not a:
4327:             messagebox.showwarning("Export","Select a saved record first."); return
4328:         no=tr.item(a[0])["values"][0]
4329:         if fmt=="word": self.export_word(typ,no)
4330:         else: self.export_excel(typ,no)
4331: 
4332:     def doc_preview_selected(self,typ,tr):
```
```text
4327:             messagebox.showwarning("Export","Select a saved record first."); return
4328:         no=tr.item(a[0])["values"][0]
4329:         if fmt=="word": self.export_word(typ,no)
4330:         else: self.export_excel(typ,no)
4331: 
4332:     def doc_preview_selected(self,typ,tr):
4333:         a=tr.selection()
4334:         if not a:
4335:             messagebox.showwarning("Preview","Select a saved record first."); return
4336:         no=tr.item(a[0])["values"][0]
4337:         data=self._get_doc_data(typ,no)
4338:         if not data:
4339:             messagebox.showwarning("Preview","Document not found."); return
4340:         title,header,cols,rows=data
4341:         header_lines=header
4342:         self.show_preview_window(title,header_lines,cols,rows)
4343: 
4344:     def doc_print_selected(self,typ,tr):
4345:         a=tr.selection()
4346:         if not a: return
4347:         no=tr.item(a[0])["values"][0]
```
```text
4378:         def _print_loaded_document():
4379:             data=self._get_doc_data(typ,no)
4380:             if not data:
4381:                 messagebox.showwarning("Document","Document not found."); return
4382:             title,header,cols,rows=data
4383:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4384:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4385: 
4386:     def _report_filter_popup(self, title, include_party=False):
4387:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4388:         win,winbody=self._internal_window(title,"520x420")
4389:         done=tk.BooleanVar(value=False)
4390:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4391:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4392:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4393:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4394:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4395:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4396:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4397:         if include_party:
4398:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4392:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4393:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4394:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4395:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4396:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4397:         if include_party:
4398:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4399:         def ok():
4400:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4401:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4402:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4403:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4404: 
4405:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4406:         self.clearbody()
4407:         # Report sub-sections use their own report toolbar; remove only the
4408:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4409:         children=self.body.winfo_children()
4410:         if children:
4411:             children[0].destroy()
4412:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4413:         if f.get("cancelled"):
4414:             self.dashboard();return
4415:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4416:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4417:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4418:         def load():
4419:             for i in tr.get_children():tr.delete(i)
4420:             params,where=params_builder(f)
4421:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4422:             for r in self.conn.execute(sql,params):
4423:                 vals=list(r)
4424:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4425:                 tr.insert("","end",values=vals)
4426:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4427:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4428:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4429:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4430:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4431:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4432:         def open_find_report():
4433:             state_find={"index":-1}
```
```text
4439:                 order=children[start:]+children[:start]
4440:                 for iid in order:
4441:                     vals=tr.item(iid,"values")
4442:                     if any(text in str(v).lower() for v in vals):
4443:                         state_find["index"]=children.index(iid)
4444:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4445:                 return False
4446:             self._open_exact_find_text_popup(search_fn)
4447:         self._item_master_find_callback=open_find_report
4448:         load()
4449:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4450: 
4451:     def report_grr(self):
4452:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4453:         def pb(f):
4454:             w=[];p=[]
4455:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4456:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4457:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4458:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4459:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4454:             w=[];p=[]
4455:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4456:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4457:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4458:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4459:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4460:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4461:             return p,w
4462:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4463: 
4464:     def report_demand(self):
4465:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4466:         def pb(f):
4467:             w=[];p=[]
4468:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4469:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4470:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4471:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4472:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4473:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4474:             return p,w
```
```text
4467:             w=[];p=[]
4468:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4469:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4470:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4471:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4472:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4473:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4474:             return p,w
4475:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4476: 
4477:     def report_issue(self):
4478:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4479:         def pb(f):
4480:             w=[];p=[]
4481:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4482:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4483:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4484:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4485:             return p,w
4486:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4487: 
```
```text
4480:             w=[];p=[]
4481:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4482:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4483:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4484:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4485:             return p,w
4486:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4487: 
4488:     def report_party(self):
4489:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4490:         def pb(f):
4491:             w=[];p=[]
4492:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4493:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4494:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4495:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4496:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4497:             return p,w
4498:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4499: 
4500:     def reports(self):
```
```text
4498:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4499: 
4500:     def reports(self):
4501:         self.clearbody()
4502:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4503: 
4504:         # ================= GRN Details =================
4505:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4506:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4507:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4508:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4509:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4510:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4511: 
4512:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4513:         def load_grr_item(codev=None):
4514:             for i in tr.get_children(): tr.delete(i)
4515:             q=codev.get().strip() if codev else ""
4516:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4517:             for r in self.conn.execute(sql,(q,) if q else ()):
4518:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4524:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4525:         tr=self.make_tree(fr,grr_cols,grr_widths)
4526:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4527:             for i in tr.get_children(): tr.delete(i)
4528:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4529:             conds=[];params=[]
4530:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4531:             if td: conds.append("g.grr_date<=?");params.append(td)
4532:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4533:             for r in self.conn.execute(sql,params):
4534:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4535:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4536:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4537:         load_grr_date(fdv,tdv)
4538: 
4539:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4540:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4541:         party=tk.StringVar(value="ALL")
4542:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4543:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4544:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4540:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4541:         party=tk.StringVar(value="ALL")
4542:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4543:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4544:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4545:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4546:         def load_party(*_):
4547:             for i in tr.get_children(): tr.delete(i)
4548:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4549:             if party.get()=="ALL":
4550:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4551:             else:
4552:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4553:             for r in rows:
4554:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4555:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4556:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4557: 
4558:         # ================= Demand Details =================
4559:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4560:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4556:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4557: 
4558:         # ================= Demand Details =================
4559:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4560:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4561:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4562:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4563:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4564:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4565: 
4566:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4567:         def load_dem_item(codev=None):
4568:             for i in tr.get_children(): tr.delete(i)
4569:             q=codev.get().strip() if codev else ""
4570:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4571:             for r in self.conn.execute(sql,(q,) if q else ()):
4572:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4573:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4574:         tr=self.make_tree(fr,dem_cols,dem_widths)
4575:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4576:         load_dem_item(codev)
```
```text
4578:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4579:         tr=self.make_tree(fr,dem_cols,dem_widths)
4580:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4581:             for i in tr.get_children(): tr.delete(i)
4582:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4583:             conds=[];params=[]
4584:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4585:             if td: conds.append("d.demand_date<=?");params.append(td)
4586:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4587:             for r in self.conn.execute(sql,params):
4588:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4589:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4590:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4591:         load_dem_date(fdv,tdv)
4592: 
4593:         # ================= Material Issue Details =================
4594:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4595:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4596:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4597:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4598:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4591:         load_dem_date(fdv,tdv)
4592: 
4593:         # ================= Material Issue Details =================
4594:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4595:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4596:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4597:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4598:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4599:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4600: 
4601:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4602:         def load_iss_item(codev=None):
4603:             for i in tr.get_children(): tr.delete(i)
4604:             q=codev.get().strip() if codev else ""
4605:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4606:             for r in self.conn.execute(sql,(q,) if q else ()):
4607:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4608:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4609:         tr=self.make_tree(fr,iss_cols,iss_widths)
4610:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4611:         load_iss_item(codev)
```
```text
4613:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4614:         tr=self.make_tree(fr,iss_cols,iss_widths)
4615:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4616:             for i in tr.get_children(): tr.delete(i)
4617:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4618:             conds=[];params=[]
4619:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4620:             if td: conds.append("i.issue_date<=?");params.append(td)
4621:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4622:             for r in self.conn.execute(sql,params):
4623:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4624:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4625:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4626:         load_iss_date(fdv,tdv)
4627: 
4628:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4629: 
4630:     def print_item_master(self):
4631:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4632:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4633: 
```
```text
4630:     def print_item_master(self):
4631:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4632:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4633: 
4634:     def print_party_master(self):
4635:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4636:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4637: 
4638:     def print_report(self,kind):
4639:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4640:         if kind=="grr":
4641:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4642:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4643:         elif kind=="demand":
4644:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4645:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4646:         elif kind=="issue":
4647:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4648:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4649:         else:
4650:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4651:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4652:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4653: 
4654:     def print_stock(self):
4655:         rows=[]
4656:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4657:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4658:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4659:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4660: 
4661:     def print_ledger(self):
4662:         rows=[]
4663:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4664:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4665:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4666:                 running += x[3] if x[1]=="GRR" else -x[3]
4667:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4668:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4669: 
4670:     def _get_doc_data(self, typ, no):
4671:         """Header + line items for one saved document, used by the on-screen
```
```text
4737:             sig=doc.add_table(rows=2,cols=3)
4738:             labels=["Prepared By","Store Keeper","Store Incharge"]
4739:             for i,label in enumerate(labels):
4740:                 sig.cell(0,i).text="____________________"
4741:                 sig.cell(1,i).text=label
4742:                 for para in sig.cell(1,i).paragraphs:
4743:                     for run in para.runs: run.bold=True
4744:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4745:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4746:         doc.save(path)
4747:         self.open_file(path)
4748: 
4749:     def export_excel(self, typ, no):
4750:         if not no or not no.strip():
4751:             return messagebox.showwarning("Excel Export","Select a document first.")
4752:         if not XLSX_AVAILABLE:
4753:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4754:         data=self._get_doc_data(typ,no)
4755:         if not data:
4756:             return messagebox.showwarning("Excel Export","Document not found.")
4757:         title,header,cols,rows=data
```
```text
4779:             for col in range(1,4):
4780:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4781:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4782:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4783:         for col_cells in ws.columns:
4784:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4785:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4786:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4787:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4788:         wb.save(path)
4789:         self.open_file(path)
4790: 
4791:     def preview_pdf(self,typ,no):
4792:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4793:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4794:         data=self._get_doc_data(typ,no)
4795:         if not data:return messagebox.showwarning("Document","Document not found.")
4796:         title,header,cols,rows=data
4797:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4798:         page_size = landscape(A4) if typ == "grr" else A4
4799:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4794:         data=self._get_doc_data(typ,no)
4795:         if not data:return messagebox.showwarning("Document","Document not found.")
4796:         title,header,cols,rows=data
4797:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4798:         page_size = landscape(A4) if typ == "grr" else A4
4799:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4800: 
4801:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4802:         """Open the print dialog with a real visual preview of the exact report.
4803: 
4804:         The report is rendered to a temporary PDF only in memory/on disk for the
4805:         duration of printing.  It is deleted after the print dialog closes, so
4806:         the Print button does not leave a PDF report behind.  Printing uses the
4807:         rendered report page itself rather than rebuilding rows as plain text;
4808:         this keeps the printed page identical to the application's report.
4809:         """
4810:         # Printing is always prepared as an A4 landscape page. This only affects
4811:         # the print path; the rest of the application's UI/report logic is unchanged.
4812:         page_size = landscape(A4)
4813:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
4814:             messagebox.showwarning(
```
```text
4816:                 "The print preview/printing components are not available.\n\n"
4817:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
4818:             )
4819:             return
4820:         if not rows and not columns:
4821:             messagebox.showwarning("Print", "There is no data to print.")
4822:             return
4823:         try:
4824:             os.makedirs(REPORTS_DIR, exist_ok=True)
4825:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
4826:             self._pdf_table_report(key,title,columns,rows,page_size,
4827:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
4828:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
4829:             self._select_windows_printer_for_pdf(key)
4830:         except Exception as e:
4831:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
4832: 
4833:     def _select_windows_printer_for_pdf(self, path):
4834:         """Print dialog with an actual page preview, printer selection and direct GDI output.
4835: 
4836:         The preview is rendered from the exact PDF produced by the application,
```
```text
4866:         job=getattr(self, "_print_jobs", {}).get(path)
4867:         if job:
4868:             title, header_lines, columns, rows, source_page_size = job
4869:         else:
4870:             title=os.path.splitext(os.path.basename(path))[0]
4871:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
4872: 
4873:         try:
4874:             doc=fitz.open(path)
4875:             total_pages=max(1,doc.page_count)
4876:         except Exception as e:
4877:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
4878:             return
4879: 
4880:         win=tk.Toplevel(self)
4881:         win.title("Printing from Win32 application - Print")
4882:         win.geometry("900x620")
4883:         win.minsize(850,580)
4884:         win.transient(self)
4885:         win.configure(bg="#f0f0f0")
4886: 
```
```text
4892:             pass
4893: 
4894:         outer=tk.Frame(win,bg="#f0f0f0")
4895:         outer.pack(fill="both",expand=True)
4896:         outer.columnconfigure(1,weight=1)
4897:         outer.rowconfigure(0,weight=1)
4898: 
4899:         # Left side mirrors the familiar system printer dialog: printers and
4900:         # print options. Right side contains the actual report page preview.
4901:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
4902:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
4903:         left.grid_propagate(False)
4904:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
4905:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
4906:         printer_list.pack(fill="x")
4907:         for pr in printers: printer_list.insert("end",pr)
4908:         try: printer_list.selection_set(printers.index(default_printer))
4909:         except Exception: printer_list.selection_set(0)
4910: 
4911:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
4912:         copies=tk.IntVar(value=1)
```
```text
4985:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
4986: 
4987:         bottom=tk.Frame(win,bg="#f0f0f0")
4988:         # `outer` already uses pack() in `win`; using grid() for another direct
4989:         # child of the same toplevel raises TclError. Keep the action bar in the
4990:         # same geometry-manager family so Print/Cancel are always visible.
4991:         bottom.pack(fill="x",padx=12,pady=(0,12))
4992:         bottom.columnconfigure(0,weight=1)
4993:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
4994:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
4995:         print_btn=ttk.Button(bottom,text="Print",width=12)
4996:         print_btn.grid(row=0,column=2,padx=(8,0))
4997: 
4998:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
4999: 
5000:         def parse_page_selection(total):
5001:             if pages_mode.get()=="All pages": return list(range(total))
5002:             raw=page_range.get().strip()
5003:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5004:             selected=[]
5005:             for part in raw.split(","):
```
```text
5002:             raw=page_range.get().strip()
5003:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5004:             selected=[]
5005:             for part in raw.split(","):
5006:                 part=part.strip()
5007:                 if "-" in part:
5008:                     a,b=part.split("-",1); a=int(a); b=int(b)
5009:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5010:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5011:                     selected.extend(range(a-1,b))
5012:                 else:
5013:                     n=int(part)
5014:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5015:                     selected.append(n-1)
5016:             return list(dict.fromkeys(selected))
5017: 
5018:         def selected_printer():
5019:             sel=printer_list.curselection()
5020:             return printer_list.get(sel[0]) if sel else printers[0]
5021: 
5022:         def print_rendered_pages():
```
```text
5115:                 finally:
5116:                     if hprinter is not None:
5117:                         try: win32print.ClosePrinter(hprinter)
5118:                         except Exception: pass
5119:                     if hdc:
5120:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5121:                         except Exception: pass
5122: 
5123:                 # Print the exact rendered PDF page through the printer DC.
5124:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5125:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5126:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5127:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5128: 
5129:                 for copy_no in range(count):
5130:                     dc.StartDoc(str(title)[:80])
5131:                     doc_ok=False
5132:                     try:
5133:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5134:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5135:                             dc.StartPage()
```
```text
5134:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5135:                             dc.StartPage()
5136:                             page_ok=False
5137:                             try:
5138:                                 cell_w=printable_w/float(cols_n)
5139:                                 cell_h=printable_h/float(rows_n)
5140:                                 for j,page_index in enumerate(batch):
5141:                                     page=doc.load_page(page_index)
5142:                                     pdf_w=max(1.0,float(page.rect.width))
5143:                                     pdf_h=max(1.0,float(page.rect.height))
5144:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5145:                                     fit=max(0.25,min(fit,8.0))
5146:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5147:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5148:                                     target_w=max(1,int(cell_w*0.96))
5149:                                     target_h=max(1,int(cell_h*0.96))
5150:                                     ratio=min(target_w/img.width,target_h/img.height)
5151:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5152:                                     if (nw,nh)!=(img.width,img.height):
5153:                                         img=img.resize((nw,nh),Image.LANCZOS)
5154:                                     dib=ImageWin.Dib(img)
```
```text
5174: 
5175:                 status.set("Print job sent successfully")
5176:                 win.update_idletasks()
5177:                 win.after(500,close)
5178:             except Exception as e:
5179:                 status.set("Print failed: "+str(e))
5180:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5181: 
5182:         def close():
5183:             try: doc.close()
5184:             except Exception: pass
5185:             try: win.destroy()
5186:             except Exception: pass
5187:             # Only the temporary PDF created by the Print button is removed.
5188:             # Existing report PDFs passed through the legacy print path are preserved.
5189:             try:
5190:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5191:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5192:             except Exception: pass
5193: 
5194:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5190:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5191:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5192:             except Exception: pass
5193: 
5194:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5195:         bottom.winfo_children()[1].configure(command=close)
5196:         print_btn.configure(command=print_rendered_pages)
5197:         win.protocol("WM_DELETE_WINDOW",close)
5198:         win.bind("<Escape>",lambda e:close())
5199:         win.grab_set()
5200:         # Keep the requested printer defaults visibly selected; no manual
5201:         # adjustment is required before pressing Print.
5202:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5203:         win.after(120,lambda:render_preview(0))
5204:         win.focus_force()
5205: 
5206:     def print_pdf(self,path):
5207:         """Open a printer-selection window for a generated PDF."""
5208:         path=os.path.abspath(path)
5209:         if not os.path.exists(path):
5210:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5206:     def print_pdf(self,path):
5207:         """Open a printer-selection window for a generated PDF."""
5208:         path=os.path.abspath(path)
5209:         if not os.path.exists(path):
5210:             messagebox.showwarning("Print", "The report file could not be found.")
5211:             return
5212: 
5213:         if sys.platform.startswith("win"):
5214:             self._select_windows_printer_for_pdf(path)
5215:             return
5216: 
5217:         try:
5218:             subprocess.run(["lp", path], check=True)
5219:         except Exception as e:
5220:             messagebox.showwarning(
5221:                 "Print",
5222:                 "The operating system could not start printing.\n\n"
5223:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5224:             )
5225: 
5226:     def open_file(self,path):
```
```text
5221:                 "Print",
5222:                 "The operating system could not start printing.\n\n"
5223:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5224:             )
5225: 
5226:     def open_file(self,path):
5227:         try:
5228:             if sys.platform.startswith("win"): os.startfile(path)
5229:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5230:             else: subprocess.Popen(["xdg-open",path])
5231:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5232: 
5233:     def print_demand(self,no):
5234:         data=self._get_doc_data("demand",no)
5235:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5236:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5237:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5238:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5239: 
5240:     def print_grr(self,no):
5241:         data=self._get_doc_data("grr",no)
```
```text
5235:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5236:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5237:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5238:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5239: 
5240:     def print_grr(self,no):
5241:         data=self._get_doc_data("grr",no)
5242:         if not data:return messagebox.showwarning("Document","GRN not found.")
5243:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5244:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5245:         # GRN has a wide item table. Generate the PDF itself in landscape so
5246:         # the printer dialog and printer driver receive a landscape document
5247:         # instead of a portrait page with rotated/cropped content.
5248:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5249: 
5250:     def print_issue(self,no):
5251:         data=self._get_doc_data("issue",no)
5252:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5253:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5254:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5255:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
```

## updater.py

- Lines: 124
- Functions: _app_dir(18-21), _version_tuple(24-31), _load_config(34-39), _download(42-49), _sha256(52-57), _install_after_exit(60-67), _start_update_download(70-92), check_for_update(95-123)

### Relevant source locations

```text
0030:         parts.append(0)
0031:     return tuple(parts[:4])
0032: 
0033: 
0034: def _load_config():
0035:     path = os.path.join(_app_dir(), CONFIG_NAME)
0036:     if not os.path.exists(path):
0037:         return {}
0038:     with open(path, "r", encoding="utf-8") as f:
0039:         return json.load(f)
0040: 
0041: 
0042: def _download(url, destination):
0043:     req = urllib.request.Request(url, headers={"User-Agent": "StoreInventoryManagement-Updater"})
0044:     with urllib.request.urlopen(req, timeout=30) as response, open(destination, "wb") as out:
0045:         while True:
0046:             chunk = response.read(1024 * 1024)
0047:             if not chunk:
0048:                 break
0049:             out.write(chunk)
0050: 
```
```text
0046:             chunk = response.read(1024 * 1024)
0047:             if not chunk:
0048:                 break
0049:             out.write(chunk)
0050: 
0051: 
0052: def _sha256(path):
0053:     h = hashlib.sha256()
0054:     with open(path, "rb") as f:
0055:         for chunk in iter(lambda: f.read(1024 * 1024), b""):
0056:             h.update(chunk)
0057:     return h.hexdigest().lower()
0058: 
0059: 
0060: def _install_after_exit(new_exe, current_exe):
0061:     app_dir = os.path.dirname(current_exe)
0062:     script = os.path.join(app_dir, ".store_inventory_update.cmd")
0063:     pid = os.getpid()
0064:     script_text = f'''@echo off\nsetlocal\nset "NEW={new_exe}"\nset "OLD={current_exe}"\nset "PID={pid}"\n:wait\ntasklist /FI "PID eq %PID%" 2>nul | findstr /I "%PID%" >nul\nif not errorlevel 1 (\n  timeout /t 1 /nobreak >nul\n  goto wait\n)\ntimeout /t 1 /nobreak >nul\nmove /Y "%NEW%" "%OLD%" >nul 2>&1\nif not exist "%OLD%" goto fail\nstart "" "%OLD%"\ndel "%~f0"\nexit /b 0\n:fail\nstart "" "%OLD%"\ndel "%~f0"\nexit /b 1\n'''
0065:     with open(script, "w", encoding="utf-8") as f:
0066:         f.write(script_text)
```
```text
0059: 
0060: def _install_after_exit(new_exe, current_exe):
0061:     app_dir = os.path.dirname(current_exe)
0062:     script = os.path.join(app_dir, ".store_inventory_update.cmd")
0063:     pid = os.getpid()
0064:     script_text = f'''@echo off\nsetlocal\nset "NEW={new_exe}"\nset "OLD={current_exe}"\nset "PID={pid}"\n:wait\ntasklist /FI "PID eq %PID%" 2>nul | findstr /I "%PID%" >nul\nif not errorlevel 1 (\n  timeout /t 1 /nobreak >nul\n  goto wait\n)\ntimeout /t 1 /nobreak >nul\nmove /Y "%NEW%" "%OLD%" >nul 2>&1\nif not exist "%OLD%" goto fail\nstart "" "%OLD%"\ndel "%~f0"\nexit /b 0\n:fail\nstart "" "%OLD%"\ndel "%~f0"\nexit /b 1\n'''
0065:     with open(script, "w", encoding="utf-8") as f:
0066:         f.write(script_text)
0067:     subprocess.Popen(["cmd.exe", "/c", script], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
0068: 
0069: 
0070: def _start_update_download(download_url):
0071:     """Start update download with IDM when installed, otherwise browser."""
0072:     if not download_url:
0073:         return False
0074:     candidates = [
0075:         os.path.expandvars(r"%PROGRAMFILES%\Internet Download Manager\IDMan.exe"),
0076:         os.path.expandvars(r"%PROGRAMFILES(x86)%\Internet Download Manager\IDMan.exe"),
0077:     ]
0078:     for idm in candidates:
0079:         if idm and os.path.isfile(idm):
```
```text
0073:         return False
0074:     candidates = [
0075:         os.path.expandvars(r"%PROGRAMFILES%\Internet Download Manager\IDMan.exe"),
0076:         os.path.expandvars(r"%PROGRAMFILES(x86)%\Internet Download Manager\IDMan.exe"),
0077:     ]
0078:     for idm in candidates:
0079:         if idm and os.path.isfile(idm):
0080:             try:
0081:                 subprocess.Popen([idm, "/d", download_url, "/n"], close_fds=True)
0082:                 return True
0083:             except Exception:
0084:                 pass
0085:     try:
0086:         return bool(webbrowser.open(download_url, new=2))
0087:     except Exception:
0088:         try:
0089:             os.startfile(download_url)
0090:             return True
0091:         except Exception:
0092:             return False
0093: 
```
