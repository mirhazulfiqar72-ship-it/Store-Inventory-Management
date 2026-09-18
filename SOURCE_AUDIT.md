# Store Inventory source audit

Generated from `D:\a\Store-Inventory-Management\Store-Inventory-Management\source` after CI patches.

## durable_local.py

- Lines: 114
- Functions: _columns(27-28), snapshot(30-40), _row_count(42-43), save(45-67), load(69-78), restore_if_newer(80-114)

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
0019: DATA_DIR = INSTALL_ROOT / "Data"
0020: SNAPSHOT_PATH = DATA_DIR / "local_data_snapshot.json"
0021: TABLES = (
0022:     "items", "mto_items", "parties", "demands", "demand_lines", "grr", "grr_lines",
0023:     "issues", "issue_lines", "transactions", "users",
0024: )
0025: LAST_ERROR = ""
0026: 
0027: def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
0028:     return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
0029: 
0030: def snapshot(conn: sqlite3.Connection) -> Dict[str, Any]:
0031:     tables: Dict[str, Any] = {}
0032:     for table in TABLES:
0033:         cols = _columns(conn, table)
0034:         rows = []
0035:         if cols:
0036:             for row in conn.execute(f"SELECT {','.join(cols)} FROM {table}").fetchall():
0037:                 rows.append({c: (v if v is None or isinstance(v, (str, int, float, bool)) else str(v))
0038:                              for c, v in zip(cols, row)})
0039:         tables[table] = {"columns": cols, "rows": rows}
```
```text
0037:                 rows.append({c: (v if v is None or isinstance(v, (str, int, float, bool)) else str(v))
0038:                              for c, v in zip(cols, row)})
0039:         tables[table] = {"columns": cols, "rows": rows}
0040:     return {"schema": 1, "tables": tables}
0041: 
0042: def _row_count(s: Dict[str, Any]) -> int:
0043:     return sum(len(v.get("rows", []) or []) for v in s.get("tables", {}).values())
0044: 
0045: def save(conn: sqlite3.Connection) -> bool:
0046:     global LAST_ERROR
0047:     LAST_ERROR = ""
0048:     try:
0049:         DATA_DIR.mkdir(parents=True, exist_ok=True)
0050:         value = snapshot(conn)
0051:         fd, tmp = tempfile.mkstemp(prefix="local_snapshot_", suffix=".tmp", dir=str(DATA_DIR))
0052:         try:
0053:             with os.fdopen(fd, "w", encoding="utf-8") as f:
0054:                 json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
0055:                 f.flush()
0056:                 os.fsync(f.fileno())
0057:             os.replace(tmp, SNAPSHOT_PATH)
```
```text
0072:         if not SNAPSHOT_PATH.exists():
0073:             return None
0074:         value = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
0075:         return value if isinstance(value, dict) else None
0076:     except Exception:
0077:         LAST_ERROR = traceback.format_exc()
0078:         return None
0079: 
0080: def restore_if_newer(conn: sqlite3.Connection) -> bool:
0081:     global LAST_ERROR
0082:     LAST_ERROR = ""
0083:     saved = load()
0084:     if not saved or _row_count(saved) <= 0:
0085:         return False
0086:     current = snapshot(conn)
0087:     if _row_count(current) >= _row_count(saved):
0088:         return False
0089:     try:
0090:         conn.execute("BEGIN")
0091:         for table in TABLES:
0092:             cols = _columns(conn, table)
```
```text
0085:         return False
0086:     current = snapshot(conn)
0087:     if _row_count(current) >= _row_count(saved):
0088:         return False
0089:     try:
0090:         conn.execute("BEGIN")
0091:         for table in TABLES:
0092:             cols = _columns(conn, table)
0093:             rows = saved.get("tables", {}).get(table, {}).get("rows", []) or []
0094:             if not cols:
0095:                 continue
0096:             conn.execute(f"DELETE FROM {table}")
0097:             if not rows:
0098:                 continue
0099:             insert_cols = [c for c in cols if c in rows[0]]
0100:             if not insert_cols:
0101:                 continue
0102:             placeholders = ",".join("?" for _ in insert_cols)
0103:             sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0104:             for row in rows:
0105:                 conn.execute(sql, [row.get(c) for c in insert_cols])
```
```text
0098:                 continue
0099:             insert_cols = [c for c in cols if c in rows[0]]
0100:             if not insert_cols:
0101:                 continue
0102:             placeholders = ",".join("?" for _ in insert_cols)
0103:             sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0104:             for row in rows:
0105:                 conn.execute(sql, [row.get(c) for c in insert_cols])
0106:         conn.commit()
0107:         return True
0108:     except Exception:
0109:         LAST_ERROR = traceback.format_exc()
0110:         try:
0111:             conn.rollback()
0112:         except Exception:
0113:             pass
0114:         return False
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

- Lines: 5291
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-332), restore_database(334-351), stock(353-358), fmt_num(360-362), to_iso_date(364-373), to_display_date(375-383), fiscal_year_key(385-396), fiscal_year_range(398-401), normalize_code(403-411), format_code(413-422), attach_code_mask(424-450), set_digits(427-432), key(433-443), paste(445-448), bind_add_to_list(452-473), on_enter(455-466), __init__(477-494), _check_for_updates(496-501), _setup_style(503-539), _shade(542-547), on_close(549-554), redo_network_setup(556-572), backup_now(574-581), restore_backup(583-601), _ctrl_f(603-615), _open_exact_find_text_popup(617-662), do_find(638-647), close(648-655), _global_enter(664-676), wipe(678-679), login(681-710), do_login(696-707), change_password(712-762), save_password(734-756), logout(764-769), home(771-790), _ensure_mdi_host(792-813), _internal_window(815-899), normal_place(831-837), restore(838-845), maximize(846-852), minimize(853-868), close(869-892), open_inventory_codes_detail_flow(901-919), open_inventory_codes_with_filters(921-935), open_inventory_codes_report_window(937-1163), tbtn(955-960), balance_as_of(1017-1027), build_nav(1029-1051), selected_prefix(1053-1062), load(1064-1096), page_move(1098-1099), page_first(1100-1100), page_last(1101-1105), on_nav(1109-1110), find_popup(1113-1132), search_fn(1115-1130), print_report(1135-1138), export_pdf(1140-1142), export_word(1143-1145), export_excel(1146-1148), open_menu_window(1165-1187), close_window(1175-1182), _manual_check_update(1189-1193), _show_current_version(1195-1199), build_menu_bar(1201-1248), open_calendar_picker(1250-1298), pick(1268-1270), redraw(1272-1284), nav(1286-1290), make_date_field(1300-1307), clearbody(1309-1335), run_action(1324-1329), _portable_print_current(1337-1348), portable_print_dialog(1350-1423), build_receipt(1377-1395), send(1396-1409), refresh_printers(1410-1416), preview_tree(1425-1437), set_page_actions(1439-1447), _add_transaction_new_button(1449-1466), _report_header(1468-1532), _report_footer(1534-1540), _grr_signature_block(1542-1558), _finish_page(1560-1561), _wrap_text_to_width(1563-1588), fits(1570-1570), _pdf_table_report(1590-1659), table_header(1612-1617), show_preview_window(1661-1734), _safe_report_name(1736-1739), print_preview_window(1741-1744), _fallback_pdf_export(1746-1779), esc(1750-1751), add(1754-1756), _save_entry_report(1781-1801), export_preview_pdf(1803-1832), export_preview_word(1834-1874), export_preview_excel(1876-1912), make_tree(1914-1923), pick_item(1925-1946), choose(1926-1945), ld(1933-1937), sel(1939-1943), bind_item_lookup(1948-1965), lookup(1950-1963), _set_form_editable(1968-1981), walk(1971-1980), document_selector(1983-2017), refresh(1988-1999), selected(2000-2005), dashboard(2019-2128), load_details(2101-2125), dashboard_details(2130-2134), item_history(2136-2156), _ask_item_master_filters(2158-2242), finish(2211-2223), items(2244-2482), hierarchy(2285-2294), selected_prefix(2340-2353), balance_as_of(2355-2362), load(2364-2402), set_page(2404-2405), select_node(2407-2428), open_find(2434-2453), search_fn(2436-2451), visible_rows(2458-2460), print_inventory(2461-2465), export_inventory_word(2466-2468), export_inventory_excel(2469-2471), portable_inventory(2476-2478), inventory_codes(2484-2768), btn(2520-2525), close_editor(2561-2571), edit_cell(2573-2599), commit(2591-2597), rows_query(2601-2614), load(2616-2631), new_record(2633-2654), commit(2647-2651), selected_row(2656-2658), edit_record(2660-2668), save_record(2670-2713), delete_record(2715-2726), refresh(2728-2728), do_print(2729-2731), do_close(2732-2732), filter_grid(2750-2757), open_mto_inventory_flow(2770-2793), open_code_opening_flow(2795-2803), code_opening(2805-2806), _open_code_opening_popup(2808-2809), _open_code_opening_detail(2811-3054), norm(2881-2882), table_for(2884-2885), row_for(2887-2892), search_any_destination(2894-2907), desc_hit(2909-2913), clear_form(2915-2928), load_for_edit(2930-2951), check_duplicates(2953-2964), save_code(2969-3020), edit_action(3022-3026), delete_code(3028-3043), _mto_new_item_dialog(3056-3092), save(3072-3089), _item_filter_bar(3094-3106), _date_filter_bar(3108-3116), _ask_mto_inventory_filters(3118-3163), finish(3148-3156), mto_inventory(3165-3365), open_find(3199-3218), search_fn(3201-3216), hierarchy(3237-3241), rebuild_nav(3243-3254), mto_balance(3278-3287), load(3289-3331), set_page(3333-3333), select_node(3334-3343), visible_rows(3348-3348), do_print(3349-3353), export_word(3354-3356), export_excel(3357-3359), party_master(3367-3418), load(3377-3380), clear(3381-3385), new_form(3386-3387), save(3388-3394), load_party_row(3395-3399), on_party_select(3400-3401), edit(3403-3407), delete_party(3408-3414), user_management(3420-3504), sync_role(3447-3452), load(3456-3459), clear(3460-3463), edit(3464-3471), save(3472-3489), delete_user(3490-3501), _renumber_tree(3507-3510), demand(3512-3676), _restore_demand_tree_columns(3555-3561), add(3564-3572), edit_item(3574-3586), delete_item(3588-3596), new_form(3600-3606), save(3608-3624), delete_current(3628-3634), cancel_form(3635-3643), preview_now(3644-3654), edit_saved_demand(3655-3658), print_now(3659-3669), load_demand_into_form(3678-3690), refresh_saved_cache(3692-3704), grr(3706-3869), add(3738-3746), edit_item(3748-3758), delete_item(3760-3768), new_form(3772-3778), save(3780-3801), delete_current(3805-3811), cancel_form(3812-3820), preview_now(3821-3839), portable_current(3840-3843), edit_saved_grr(3845-3848), print_now(3849-3862), load_grr_into_form(3871-3883), issue(3885-4031), old_issue_qty(3914-3917), update_balance(3918-3926), add(3928-3937), edit_item(3939-3950), new_form(3954-3960), post(3962-3983), delete_current(3984-3990), cancel_form(3991-3999), preview_now(4000-4007), portable_current(4008-4010), load_saved_issue(4015-4017), edit_saved_issue(4018-4021), print_issue_now(4022-4027), load_issue_into_form(4033-4046), _ask_report_criteria(4048-4111), finish(4097-4105), _open_report_child(4113-4118), open_stock_balance_report_flow(4120-4123), open_grr_report_flow(4125-4128), open_demand_report_flow(4130-4133), open_issue_report_flow(4135-4138), open_party_report_flow(4140-4143), _ask_stock_balance_filters(4145-4168), ok(4160-4161), cancel(4162-4162), stock_balance(4170-4233), period(4186-4197), header_summary(4198-4199), load(4200-4209), reopen_filters(4210-4214), open_find_stock(4218-4231), search_fn(4220-4230), ledger(4235-4247), open_document_editor(4249-4257), _edit_from_selector(4259-4275), show_saved_records(4277-4308), view(4300-4304), documents(4310-4355), edit_selected(4329-4335), delete_selected(4336-4348), doc_export_selected(4357-4363), doc_preview_selected(4365-4375), doc_print_selected(4377-4385), load_document(4387-4417), _print_loaded_document(4411-4416), _report_filter_popup(4419-4436), ok(4432-4433), cancel(4434-4434), _report_window(4438-4482), load(4451-4458), hdr(4459-4459), open_find_report(4465-4479), search_fn(4467-4478), report_grr(4484-4495), pb(4486-4494), report_demand(4497-4508), pb(4499-4507), report_issue(4510-4519), pb(4512-4518), report_party(4521-4531), pb(4523-4530), reports(4533-4661), load_grr_item(4546-4551), load_grr_date(4559-4567), load_party(4579-4587), load_dem_item(4600-4605), load_dem_date(4613-4621), load_iss_item(4635-4640), load_iss_date(4648-4656), print_item_master(4663-4665), print_party_master(4667-4669), print_report(4671-4685), print_stock(4687-4692), print_ledger(4694-4701), _get_doc_data(4703-4731), export_word(4733-4780), export_excel(4782-4822), preview_pdf(4824-4832), _open_direct_printer(4834-4864), _select_windows_printer_for_pdf(4866-5237), render_preview(4991-5010), on_resize(5012-5014), parse_page_selection(5033-5049), selected_printer(5051-5053), print_rendered_pages(5055-5213), close(5215-5225), print_pdf(5239-5257), open_file(5259-5264), print_demand(5266-5271), print_grr(5273-5281), print_issue(5283-5288)

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
1781:     def _save_entry_report(self, title, header_lines, columns, rows):
1782:         try:
1783:             os.makedirs(REPORTS_DIR, exist_ok=True)
1784:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1785:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```
```text
1778:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1779:         with open(path,"wb") as f: f.write(out)
1780: 
1781:     def _save_entry_report(self, title, header_lines, columns, rows):
1782:         try:
1783:             os.makedirs(REPORTS_DIR, exist_ok=True)
1784:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1785:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
1786:             path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
1787:             page_size = landscape(A4) if len(columns) > 8 else A4
1788:             if REPORTLAB:
1789:                 self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
1790:             else:
1791:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1792:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1793:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1794:             with open(path, "rb") as f:
1795:                 if f.read(5) != b"%PDF-":
1796:                     raise IOError("Generated report is not a valid PDF.")
1797:             self._last_entry_report_path = path
1798:             return path
```
```text
1792:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1793:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1794:             with open(path, "rb") as f:
1795:                 if f.read(5) != b"%PDF-":
1796:                     raise IOError("Generated report is not a valid PDF.")
1797:             self._last_entry_report_path = path
1798:             return path
1799:         except Exception as exc:
1800:             self._last_entry_report_path = None
1801:             return None
1802: 
1803:     def export_preview_pdf(self, title, header_lines, columns, rows):
1804:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1805:         try:
1806:             os.makedirs(REPORTS_DIR, exist_ok=True)
1807:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1808:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1809:             generated = False
1810:             if REPORTLAB:
1811:                 try:
1812:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
```
```text
1809:             generated = False
1810:             if REPORTLAB:
1811:                 try:
1812:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1813:                     generated = True
1814:                 except Exception:
1815:                     generated = False
1816:             if not generated:
1817:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1818:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1819:                 raise IOError("The PDF file was not created in the Reports folder.")
1820:             with open(path, "rb") as pf:
1821:                 signature = pf.read(5)
1822:             if signature != b"%PDF-":
1823:                 raise IOError("The generated file is not a valid PDF.")
1824:             self._last_report_path = path
1825:             try:
1826:                 webbrowser.open("file://" + path)
1827:             except Exception:
1828:                 self.open_file(path)
1829:             return path
```
```text
1823:                 raise IOError("The generated file is not a valid PDF.")
1824:             self._last_report_path = path
1825:             try:
1826:                 webbrowser.open("file://" + path)
1827:             except Exception:
1828:                 self.open_file(path)
1829:             return path
1830:         except Exception as e:
1831:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1832:             return None
1833: 
1834:     def export_preview_word(self, title, header_lines, columns, rows):
1835:         """Export exactly what is visible in the current preview to Word."""
1836:         if not DOCX_AVAILABLE:
1837:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1838:         path=self._safe_report_name(title,"docx")
1839:         doc=Document()
1840:         sec=doc.sections[0]
1841:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1842:         sec.header.paragraphs[0].runs[0].bold=True
1843:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
```
```text
1865:             doc.add_paragraph("")
1866:             sig=doc.add_table(rows=2,cols=3)
1867:             labels=["Prepared By","Store Keeper","Store Incharge"]
1868:             for i,label in enumerate(labels):
1869:                 sig.cell(0,i).text="____________________"
1870:                 sig.cell(1,i).text=label
1871:                 for para in sig.cell(1,i).paragraphs:
1872:                     for run in para.runs: run.bold=True
1873:         doc.save(path)
1874:         self.open_file(path)
1875: 
1876:     def export_preview_excel(self, title, header_lines, columns, rows):
1877:         """Export exactly what is visible in the current preview to Excel."""
1878:         if not XLSX_AVAILABLE:
1879:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
1880:         path=self._safe_report_name(title,"xlsx")
1881:         wb=openpyxl.Workbook(); ws=wb.active
1882:         ws.title="Preview"
1883:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
1884:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1885:         if not is_transaction_preview:
```
```text
1903:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
1904:             for col in range(1,4):
1905:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
1906:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
1907:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
1908:         for col_cells in ws.columns:
1909:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
1910:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
1911:         wb.save(path)
1912:         self.open_file(path)
1913: 
1914:     def make_tree(self,parent,cols,widths=None):
1915:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
1916:         tr=ttk.Treeview(fr,columns=cols,show="headings")
1917:         for i,c in enumerate(cols):
1918:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
1919:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
1920:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
1921:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
1922:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
1923:         return tr
```
```text
1976:                     w.state(["!disabled"] if editable else ["disabled"])
1977:             except Exception:
1978:                 try: w.configure(state="normal" if editable else "disabled")
1979:                 except Exception: pass
1980:             for ch in w.winfo_children(): walk(ch)
1981:         for root in roots: walk(root)
1982: 
1983:     def document_selector(self, parent, label, typ, var, load_callback):
1984:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
1985:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
1986:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
1987:         combo.pack(side="left", padx=4)
1988:         def refresh():
1989:             vals=[]
1990:             if typ=="demand":
1991:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
1992:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
1993:             elif typ=="grr":
1994:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
1995:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
1996:             else:
```
```text
2003:             no=text.split(" -> ",1)[0].strip()
2004:             var.set(no)
2005:             load_callback(no)
2006:         combo.bind("<<ComboboxSelected>>", selected)
2007:         combo.bind("<Return>", selected)
2008:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2009:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2010:         refresh()
2011:         # Keep the currently open transaction's saved-record list live.
2012:         # Each save calls refresh_saved_cache(), so newly saved records appear
2013:         # immediately without closing/reopening the window or pressing Refresh.
2014:         if not hasattr(self, "_document_selector_refreshers"):
2015:             self._document_selector_refreshers = {}
2016:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2017:         return combo
2018: 
2019:     def dashboard(self):
2020:         # Dashboard-only visual refresh. All existing data queries, filters,
2021:         # callbacks and report/detail behavior are intentionally preserved.
2022:         self.clearbody()
2023:         c=self.conn
```
```text
2102:             for x in tr.get_children(): tr.delete(x)
2103:             params=[];where=[]
2104:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2105:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2106:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2107:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2108:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2109:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2110:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2111:                    FROM transactions t JOIN items i ON i.code=t.code"""
2112:             if where: sql += " WHERE " + " AND ".join(where)
2113:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2114:             rows=list(c.execute(sql,params))
2115:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2116:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2117:             bal_after={}
2118:             for txid,cc,typ,qty in alltx:
2119:                 running.setdefault(cc,0.0)
2120:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2121:                 bal_after[txid]=running[cc]
2122:             for r in rows:
```
```text
2480:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2481:         load()
2482:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2483: 
2484:     def inventory_codes(self):
2485:         """Inventory Codes using the classic desktop inventory interface.
2486: 
2487:         This screen intentionally follows the uploaded Inventory Management
2488:         reference: a simple module title, compact New/Edit/Delete/Save/
2489:         Refresh/Print/Close action row, and a full-width editable data grid.
2490:         All records come from the V18 database, so existing inventory data is
2491:         preserved rather than recreated.
2492:         """
2493:         self.clearbody()
2494:         # Remove the generic SAP action row; this page owns its own classic
2495:         # action row just like the reference Inventory/Items screen.
2496:         if self.body.winfo_children():
2497:             try:
2498:                 self.body.winfo_children()[0].destroy()
2499:             except Exception:
2500:                 pass
```
```text
2553:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2554:         if filter_text:
2555:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2556:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2557: 
2558:         editing={"id":None,"new":False}
2559:         cell_editor={"widget":None}
2560: 
2561:         def close_editor(save_value=False):
2562:             w=cell_editor.get("widget")
2563:             if not w:
2564:                 return
2565:             try:
2566:                 if save_value:
2567:                     w.event_generate("<Return>")
2568:                 w.destroy()
2569:             except Exception:
2570:                 pass
2571:             cell_editor["widget"]=None
2572: 
2573:         def edit_cell(event=None):
```
```text
2583:             bbox=tree.bbox(iid,colid)
2584:             if not bbox: return
2585:             close_editor(False)
2586:             x,y,w,h=bbox
2587:             val=str(tree.item(iid,"values")[idx] or "")
2588:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2589:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2590:             cell_editor["widget"]=e
2591:             def commit(_=None):
2592:                 try:
2593:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2594:                 finally:
2595:                     try:e.destroy()
2596:                     except Exception:pass
2597:                     cell_editor["widget"]=None
2598:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2599:             e.bind("<FocusOut>",commit)
2600: 
2601:         def rows_query():
2602:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2603:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2605:             if tc: where.append("code <= ?"); params.append(tc)
2606:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2607:             if df or dt:
2608:                 sub=[]; sp=[]
2609:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2610:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2611:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2612:                 params.extend(sp)
2613:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2614:             return sql,params
2615: 
2616:         def load():
2617:             close_editor(False)
2618:             for i in tree.get_children(): tree.delete(i)
2619:             sql,params=rows_query()
2620:             count=0
2621:             for r in self.conn.execute(sql,params):
2622:                 # V18 stores UOM/opening and the original application may have
2623:                 # rate/remarks columns in some versions. Read them safely.
2624:                 rid,code,desc,uom,opening,rate,remarks=r
2625:                 bal=stock(self.conn,code)
```
```text
2639:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2640:             editing["id"]=None; editing["new"]=True
2641:             # Put the user directly into the Code cell.
2642:             try:
2643:                 bbox=tree.bbox(iid,"#2")
2644:                 if bbox:
2645:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2646:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2647:                     def commit(_=None):
2648:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2649:                         try:e.destroy()
2650:                         except Exception:pass
2651:                         cell_editor["widget"]=None
2652:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2653:             except Exception: pass
2654:             status.set("New row added — enter values, then press Save")
2655: 
2656:         def selected_row():
2657:             a=tree.selection()
2658:             return a[0] if a else None
2659: 
```
```text
2659: 
2660:         def edit_record():
2661:             iid=selected_row()
2662:             if not iid:
2663:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2664:             if not self.can_edit and not self.is_admin:
2665:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2666:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2667:             status.set("Edit mode — double-click any cell to change it, then press Save")
2668:             tree.focus(iid); tree.see(iid)
2669: 
2670:         def save_record():
2671:             iid=selected_row()
2672:             if not iid:
2673:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2674:             if not self.can_edit and not self.is_admin:
2675:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2676:             close_editor(True)
2677:             vals=list(tree.item(iid,"values"))
2678:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2679:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2677:             vals=list(tree.item(iid,"values"))
2678:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2679:             try: opening=float(str(vals[4]).strip() or 0)
2680:             except Exception: raise ValueError("Opening Qty must be a number.")
2681:             try: rate=float(str(vals[5]).strip() or 0)
2682:             except Exception: raise ValueError("Rate must be a number.")
2683:             remarks=str(vals[6]).strip()
2684:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2685:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2686:             if not desc:
2687:                 messagebox.showerror("Save","Description is required."); return
2688:             if opening<0:
2689:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2690:             rid=vals[0]
2691:             try:
2692:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2693:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2694:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2695:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2696:                 if rid:
2697:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2700:                                       (code,desc,uom,opening,rid))
2701:                     if oldcode!=code:
2702:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2703:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2704:                             except Exception:pass
2705:                 else:
2706:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2707:                                       (code,desc,uom,"",opening,0,"Local",0))
2708:                 self.conn.commit()
2709:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2710:                 backup_database(); load()
2711:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2712:             except Exception as ex:
2713:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2714: 
2715:         def delete_record():
2716:             iid=selected_row()
2717:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2718:             if not self.can_delete and not self.is_admin:
2719:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2720:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2716:             iid=selected_row()
2717:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2718:             if not self.can_delete and not self.is_admin:
2719:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2720:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2721:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2722:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2723:             try:
2724:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2725:             except Exception as ex:
2726:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2727: 
2728:         def refresh(): load()
2729:         def do_print():
2730:             try:self.preview_tree("Inventory Codes",tree)
2731:             except Exception as ex:messagebox.showerror("Print",str(ex))
2732:         def do_close(): self.dashboard()
2733: 
2734:         btn("New",new_record,8)
2735:         btn("Edit",edit_record,8)
2736:         btn("Delete",delete_record,8)
```
```text
2729:         def do_print():
2730:             try:self.preview_tree("Inventory Codes",tree)
2731:             except Exception as ex:messagebox.showerror("Print",str(ex))
2732:         def do_close(): self.dashboard()
2733: 
2734:         btn("New",new_record,8)
2735:         btn("Edit",edit_record,8)
2736:         btn("Delete",delete_record,8)
2737:         btn("Save",save_record,8)
2738:         btn("Refresh",refresh,9)
2739:         btn("Preview",do_print,8)
2740:         btn("Print",do_print,8)
2741:         btn("Close",do_close,8)
2742: 
2743:         # Search is deliberately small and sits on the right, without changing
2744:         # the reference layout of the action buttons.
2745:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2746:         search=tk.StringVar()
2747:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2748:         se.pack(side="left",padx=2)
2749:         self._item_master_search_entry=se
```
```text
2757:                     tree.detach(iid)
2758:         search.trace_add("write",filter_grid)
2759:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2760: 
2761:         tree.bind("<Double-1>",edit_cell)
2762:         tree.bind("<F2>",lambda e: edit_record())
2763:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2764:         self._page_actions={
2765:             "save":save_record,"edit":edit_record,"delete":delete_record,
2766:             "cancel":do_close,"print":do_print,"preview":do_print
2767:         }
2768:         load()
2769: 
2770:     def open_mto_inventory_flow(self):
2771:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2772: 
2773:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2774:         Cancel/X only closes the popup.
2775:         """
2776:         criteria = self._ask_mto_inventory_filters()
2777:         if not criteria or criteria.get("cancelled"):
```
```text
2939:                 return False
2940:             destination.set(found_dest)
2941:             edit_mode.update(on=True, original=r[0], dest=found_dest)
2942:             code.set(r[0])
2943:             desc.set(r[1] or "")
2944:             uom.set(r[2] or UOM_OPTIONS[0])
2945:             opening.set(str(r[3] if r[3] is not None else 0))
2946:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
2947:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
2948:             err.set("")
2949:             edit_btn.configure(text="SAVE EDIT")
2950:             ce.focus_set()
2951:             return True
2952: 
2953:         def check_duplicates(*_):
2954:             c = code.get().strip()
2955:             d = desc.get().strip()
2956:             dest = destination.get()
2957:             msgs = []
2958:             r = row_for(dest, c) if len(norm(c)) == 8 else None
2959:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
2961:             dh = desc_hit(dest, d) if d else None
2962:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
2963:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
2964:             hint.set("\n".join(msgs))
2965: 
2966:         code.trace_add("write", check_duplicates)
2967:         desc.trace_add("write", check_duplicates)
2968: 
2969:         def save_code():
2970:             try:
2971:                 c = code.get().strip()
2972:                 d = desc.get().strip()
2973:                 u = uom.get().strip()
2974:                 dest = destination.get()
2975:                 digits = norm(c)
2976:                 if len(digits) != 8:
2977:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
2978:                 if not d:
2979:                     raise ValueError("Description is required.")
2980:                 try:
2981:                     op = float(opening.get().strip() or 0)
```
```text
3002:                         (c, d, u, op, iso, old)
3003:                     )
3004:                     action = "updated"
3005:                 else:
3006:                     self.conn.execute(
3007:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3008:                         (c, d, u, "", op, 0, iso)
3009:                     )
3010:                     action = "saved"
3011:                 self.conn.commit()
3012:                 backup_database()
3013:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3014:                 # Keep popup open for fast multiple entries.
3015:                 clear_form(keep_search=False)
3016:                 ce.focus_set()
3017:             except Exception as ex:
3018:                 self.conn.rollback()
3019:                 err.set(str(ex))
3020:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3021: 
3022:         def edit_action():
```
```text
3018:                 self.conn.rollback()
3019:                 err.set(str(ex))
3020:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3021: 
3022:         def edit_action():
3023:             if not edit_mode["on"]:
3024:                 load_for_edit()
3025:             else:
3026:                 save_code()
3027: 
3028:         def delete_code():
3029:             if not edit_mode["on"]:
3030:                 if not load_for_edit():
3031:                     return
3032:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3033:                 return
3034:             try:
3035:                 t = table_for(edit_mode["dest"])
3036:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3037:                 self.conn.commit()
3038:                 backup_database()
```
```text
3034:             try:
3035:                 t = table_for(edit_mode["dest"])
3036:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3037:                 self.conn.commit()
3038:                 backup_database()
3039:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3040:                 clear_form(keep_search=False)
3041:             except Exception as ex:
3042:                 self.conn.rollback()
3043:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3044: 
3045:         btns = ttk.Frame(box)
3046:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3047:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3048:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3049:         edit_btn.pack(side="left", padx=4, ipadx=8)
3050:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3051:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3052:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3053:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3054:         ce.focus_set()
```
```text
3048:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3049:         edit_btn.pack(side="left", padx=4, ipadx=8)
3050:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3051:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3052:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3053:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3054:         ce.focus_set()
3055: 
3056:     def _mto_new_item_dialog(self, on_saved):
3057:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3058:         brand-new item can be created without leaving that screen. Writes
3059:         straight into the same Item Master (items table) used everywhere."""
3060:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3061:         win.transient(self); win.grab_set()
3062:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3063:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3064:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3065:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3066:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3067:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3068:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3064:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3065:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3066:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3067:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3068:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3069:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3070:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3071:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3072:         def save():
3073:             try:
3074:                 c=code.get().strip(); d=desc.get().strip()
3075:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3076:                 if not d: raise ValueError("Description is required.")
3077:                 try:
3078:                     opening_val=float(opening.get() or 0)
3079:                 except ValueError:
3080:                     raise ValueError("Opening Qty must be a number.")
3081:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3082:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3083:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3084:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3077:                 try:
3078:                     opening_val=float(opening.get() or 0)
3079:                 except ValueError:
3080:                     raise ValueError("Opening Qty must be a number.")
3081:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3082:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3083:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3084:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3085:                 self.conn.commit(); backup_database()
3086:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3087:                 win.grab_release(); win.destroy()
3088:                 on_saved()
3089:             except Exception as ex: messagebox.showerror("Error",str(ex))
3090:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3091:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3092:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3093: 
3094:     def _item_filter_bar(self, parent, on_change):
3095:         """Item Code entry + item-master picker + Search/Show All. Calls
3096:         on_change() whenever the code changes or a button is pressed."""
3097:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3183:         self._item_master_find_callback=None
3184:         self._portable_print_context=None
3185:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3186:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3187:         }
3188: 
3189:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3190:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3191:         self.conn.commit()
3192: 
3193:         # ---- Same professional in-app window layout as Inventory Codes ----
3194:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3195:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3196:                   foreground=COLORS["primary_dark"]).pack(side="left")
3197:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3198: 
3199:         def open_find():
3200:             state_find={"index":-1}
3201:             def search_fn(text):
3202:                 text=text.strip().lower()
3203:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3290:             for i in table.get_children(): table.delete(i)
3291:             where=["1=1"]; params=[]
3292:             prefix=state.get("prefix",""); q=search.get().strip()
3293:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3294:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3295:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3296:             if fc: where.append("code >= ?"); params.append(fc)
3297:             if tc: where.append("code <= ?"); params.append(tc)
3298:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3299:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3300:             records=[]
3301:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3302:                 # If a date filter is supplied, accept an opening-date match OR
3303:                 # a transaction in that date range. This prevents valid MTO codes
3304:                 # from disappearing merely because an older record has no opening_date.
3305:                 if df or dt:
3306:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3307:                     if not ok:
3308:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3309:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3310:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3380:                 tr.insert("", "end", values=r)
3381:         def clear():
3382:             for x in v.values(): x.set("")
3383:             try: tr.selection_remove(tr.selection())
3384:             except Exception: pass
3385:             self._set_form_editable(party_form_roots, False)
3386:         def new_form():
3387:             clear(); self._set_form_editable(party_form_roots, True)
3388:         def save():
3389:             try:
3390:                 name=v["name"].get().strip()
3391:                 if not name: raise ValueError("Party Name is required.")
3392:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3393:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3394:             except Exception as ex: messagebox.showerror("Error",str(ex))
3395:         def load_party_row(a):
3396:             if not a:return
3397:             r=tr.item(a[0])["values"]
3398:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3399:             self._set_form_editable(party_form_roots, False)
3400:         def on_party_select(_=None):
```
```text
3406:             load_party_row(a)
3407:             self._set_form_editable(party_form_roots, True)
3408:         def delete_party():
3409:             a=tr.selection()
3410:             if not a:
3411:                 messagebox.showwarning("Delete", "Select a party first."); return
3412:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3413:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3414:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3415:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3416:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3417:         self._add_transaction_new_button(new_form)
3418:         load(); clear()
3419: 
3420:     def user_management(self):
3421:         self.clearbody()
3422:         if not self.is_admin:
3423:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3424:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3425:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3426:         role=tk.StringVar(value="User")
```
```text
3463:             u_ent.state(["!disabled"])
3464:         def edit():
3465:             a=tr.selection()
3466:             if not a:
3467:                 messagebox.showwarning("Edit User","Select a user row first."); return
3468:             r=tr.item(a[0])["values"]
3469:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3470:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3471:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3472:         def save():
3473:             try:
3474:                 username=v["username"].get().strip()
3475:                 if not username: raise ValueError("Username is required.")
3476:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3477:                 pw=v["password"].get()
3478:                 if exists:
3479:                     pw_hash = hash_password(pw) if pw else exists[0]
3480:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3481:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3482:                 else:
3483:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3478:                 if exists:
3479:                     pw_hash = hash_password(pw) if pw else exists[0]
3480:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3481:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3482:                 else:
3483:                     if not pw: raise ValueError("Password is required for a new user.")
3484:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3485:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3486:                 self.conn.commit(); backup_database(); load(); clear()
3487:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3488:             except Exception as ex:
3489:                 messagebox.showerror("Error", str(ex))
3490:         def delete_user():
3491:             a=tr.selection()
3492:             if not a:
3493:                 messagebox.showwarning("Delete User","Select a user row first."); return
3494:             username=tr.item(a[0])["values"][0]
3495:             if username==self.current_user:
3496:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3497:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3498:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3493:                 messagebox.showwarning("Delete User","Select a user row first."); return
3494:             username=tr.item(a[0])["values"][0]
3495:             if username==self.current_user:
3496:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3497:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3498:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3499:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3500:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3501:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3502:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3503:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3504:         load()
3505: 
3506:     @staticmethod
3507:     def _renumber_tree(tree, rows):
3508:         for i,iid in enumerate(tree.get_children()):
3509:             vals=list(tree.item(iid,"values"));
3510:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3511: 
3512:     def demand(self):
3513:         self.clearbody(); self.demand_lines=[]
```
```text
3510:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3511: 
3512:     def demand(self):
3513:         self.clearbody(); self.demand_lines=[]
3514:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3515:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3516:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3517:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3518:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3519:         # Demand Date is intentionally displayed as its own dedicated field.
3520:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3521:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3522:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3523:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3524:                 ("special","Special Instructions"),("source","Recommended Source")]
3525:         for i,(k,n) in enumerate(fields):
3526:             r=i//4*2+3; c=i%4*2
3527:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3528:             if k=="dept":
3529:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3530:             elif k=="urgency":
```
```text
3600:         def new_form():
3601:             self._editing_document_key=None
3602:             for z in v.values(): z.set("")
3603:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3604:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3605:             for iid in tree.get_children(): tree.delete(iid)
3606:             self._set_form_editable(form_roots, True, skip=[selector])
3607: 
3608:         def save():
3609:             try:
3610:                 no=v["no"].get().strip()
3611:                 if not no: raise ValueError("Demand No is required.")
3612:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3613:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3614:                 if dup and getattr(self,"_editing_document_key",None) != no:
3615:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3616:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3617:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3618:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3619:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3620:                 self.conn.commit()
```
```text
3613:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3614:                 if dup and getattr(self,"_editing_document_key",None) != no:
3615:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3616:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3617:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3618:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3619:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3620:                 self.conn.commit()
3621:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3622:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3623:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3624:             except Exception as ex: messagebox.showerror("Error",str(ex))
3625:         form_roots=[f,line,editbar]
3626:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3627:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3628:         def delete_current():
3629:             no=v["no"].get().strip()
3630:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3631:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3632:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3633:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3646:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3647:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3648:                     f"Justification: {v['just'].get()}",
3649:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3650:             if not self.demand_lines:
3651:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3652:             self.show_preview_window("Purchase Demand", header,
3653:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3654:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3655:         def edit_saved_demand():
3656:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3657:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3658:             self._set_form_editable(form_roots, True, skip=[selector])
3659:         def print_now():
3660:             if not self.demand_lines:
3661:                 messagebox.showwarning("Print","Add at least one item line first."); return
3662:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3663:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3664:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3665:                     f"Justification: {v['just'].get()}",
3666:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3662:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3663:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3664:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3665:                     f"Justification: {v['just'].get()}",
3666:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3667:             self._open_direct_printer("Purchase Demand",header,
3668:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3669:                 self.demand_lines,A4)
3670:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3671:         self._add_transaction_new_button(new_form)
3672:         self._set_form_editable(form_roots, False, skip=[selector])
3673:         try:
3674:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3675:         except Exception: pass
3676:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3677: 
3678:     def load_demand_into_form(self,no,v,tree):
3679:         v["no"].set(no)
3680:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3681:         if not r:return
3682:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3684:         self.demand_lines=[]
3685:         for i in tree.get_children():tree.delete(i)
3686:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3687:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3688:         roots=getattr(self,"_transaction_form_roots",None)
3689:         if roots and "demand" in roots:
3690:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3691: 
3692:     def refresh_saved_cache(self,typ):
3693:         # Refresh saved-document dropdowns immediately after a successful save.
3694:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3695:         alive=[]
3696:         for combo, refresh in refreshers:
3697:             try:
3698:                 if combo.winfo_exists():
3699:                     refresh()
3700:                     alive.append((combo, refresh))
3701:             except Exception:
3702:                 pass
3703:         if hasattr(self, "_document_selector_refreshers"):
3704:             self._document_selector_refreshers[typ] = alive
```
```text
3703:         if hasattr(self, "_document_selector_refreshers"):
3704:             self._document_selector_refreshers[typ] = alive
3705: 
3706:     def grr(self):
3707:         self.clearbody(); self.grr_lines=[]
3708:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3709:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3710:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3711:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3712:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3713:         for i,(k,n) in enumerate(fields):
3714:             r=i//4*2+2;c=i%4*2
3715:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3716:             if k=="department":
3717:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3718:             elif k=="supplier":
3719:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3720:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3721:             elif k=="date":
3722:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3723:             else:
```
```text
3772:         def new_form():
3773:             self._editing_document_key=None
3774:             for z in v.values(): z.set("")
3775:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3776:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3777:             for iid in tree.get_children(): tree.delete(iid)
3778:             self._set_form_editable(form_roots, True, skip=[selector])
3779: 
3780:         def save():
3781:             try:
3782:                 no=v["no"].get().strip()
3783:                 if not no:raise ValueError("GRN No is required.")
3784:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3785:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3786:                 if dup and getattr(self,"_editing_document_key",None) != no:
3787:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3788:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3789:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3790:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3791:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3792:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3789:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3790:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3791:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3792:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3793:                 for x in self.grr_lines:
3794:                     ltype=x[10] if len(x)>10 else "Local"
3795:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3796:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3797:                 self.conn.commit()
3798:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
3799:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
3800:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3801:             except Exception as ex:messagebox.showerror("Error",str(ex))
3802:         form_roots=[f,line,editbar]
3803:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3804:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3805:         def delete_current():
3806:             no=v["no"].get().strip()
3807:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3808:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3809:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
3802:         form_roots=[f,line,editbar]
3803:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3804:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3805:         def delete_current():
3806:             no=v["no"].get().strip()
3807:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3808:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3809:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3810:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3811:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3812:         def cancel_form():
3813:             self._editing_document_key=None
3814:             self._set_form_editable(form_roots, False, skip=[selector])
3815:             for z in v.values(): z.set("")
3816:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3817:             itype.set("Local")
3818:             self.grr_lines.clear()
3819:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3820:             for iid in tree.get_children(): tree.delete(iid)
3821:         def preview_now():
3822:             if not self.grr_lines:
```
```text
3831:                     ("Challan #", v['challan'].get()),
3832:                     ("Vehicle #", v['vehicle'].get()),
3833:                     ("Bill/Voucher #", v['bill'].get()),
3834:                     ("Reference", v['ref'].get()),
3835:                     ("Remarks", v['remarks'].get()),
3836:                     ("Total Value", fmt_num(total))]
3837:             self.show_preview_window("GRN Receipt", header,
3838:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3839:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3840:         def portable_current():
3841:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3842:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3843:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3844:         self._portable_print_context=portable_current
3845:         def edit_saved_grr():
3846:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3847:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
3848:             self._set_form_editable(form_roots, True, skip=[selector])
3849:         def print_now():
3850:             if not self.grr_lines:
3851:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
3855:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
3856:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
3857:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
3858:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
3859:                     ("Total Value", fmt_num(total))]
3860:             self._open_direct_printer("GRN Receipt",header,
3861:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3862:                 self.grr_lines,landscape(A4))
3863:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3864:         self._add_transaction_new_button(new_form)
3865:         self._set_form_editable(form_roots, False, skip=[selector])
3866:         try:
3867:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3868:         except Exception: pass
3869:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
3870: 
3871:     def load_grr_into_form(self,no,v,tree):
3872:         v["no"].set(no)
3873:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
3874:         if not r:return
3875:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
3882:         if roots and "grr" in roots:
3883:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
3884: 
3885:     def issue(self):
3886:         self.clearbody(); self.issue_lines=[]
3887:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
3888:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
3889:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3890:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
3891:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
3892:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
3893:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3894:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3895:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
3896:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
3897:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
3898:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
3899:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
3900:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
3901:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
3902:         itype=tk.StringVar(value="Local")
```
```text
3971:                 # Editing an existing issue replaces its old stock transaction and detail lines.
3972:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
3973:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
3974:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
3975:                 for x in self.issue_lines:
3976:                     ltype=x[7] if len(x)>7 else "Local"
3977:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
3978:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
3979:                 self.conn.commit()
3980:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
3981:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
3982:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3983:             except Exception as ex:messagebox.showerror("Error",str(ex))
3984:         def delete_current():
3985:             no=v["no"].get().strip()
3986:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
3987:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
3988:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
3989:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
3990:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
3991:         def cancel_form():
```
```text
3999:             for iid in tree.get_children(): tree.delete(iid)
4000:         def preview_now():
4001:             if not self.issue_lines:
4002:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4003:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4004:                     f"Items Use For: {v['items_use_for'].get()}"]
4005:             self.show_preview_window("Material Issue", header,
4006:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4007:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4008:         def portable_current():
4009:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4010:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4011:         self._portable_print_context=portable_current
4012:         form_roots=[f,usebar,line,editbar]
4013:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4014:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4015:         def load_saved_issue(no):
4016:             self.load_issue_into_form(no,v,tree)
4017:             self._set_form_editable(form_roots, False, skip=[selector])
4018:         def edit_saved_issue():
4019:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4012:         form_roots=[f,usebar,line,editbar]
4013:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4014:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4015:         def load_saved_issue(no):
4016:             self.load_issue_into_form(no,v,tree)
4017:             self._set_form_editable(form_roots, False, skip=[selector])
4018:         def edit_saved_issue():
4019:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4020:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4021:             self._set_form_editable(form_roots, True, skip=[selector])
4022:         def print_issue_now():
4023:             if not self.issue_lines:
4024:                 messagebox.showwarning("Print","Add at least one item line first."); return
4025:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4026:             self._open_direct_printer("Material Issue",header,
4027:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4028:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4029:         self._add_transaction_new_button(new_form)
4030:         self._set_form_editable(form_roots, False, skip=[selector])
4031:         self._active_form_loader = load_saved_issue
4032: 
```
```text
4040:         for i in tree.get_children():tree.delete(i)
4041:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4042:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4043:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4044:         roots=getattr(self,"_transaction_form_roots",None)
4045:         if roots and "issue" in roots:
4046:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4047: 
4048:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4049:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4050: 
4051:         The layout intentionally matches Inventory Codes' Selection Criteria
4052:         popup so all Report sub-sections have one consistent desktop workflow.
4053:         """
4054:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4055:         win=tk.Toplevel(self)
4056:         win.title(f"{report_title} - Selection Criteria")
4057:         win.resizable(False,False)
4058:         win.transient(self); win.grab_set()
4059:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4060:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4105:             except Exception: pass
4106:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4107:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4108:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4109:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4110:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4111:         e1.focus_set(); self.wait_window(win); return result
4112: 
4113:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4114:         self._pending_report_filters=criteria
4115:         try:
4116:             return self.open_menu_window(method,title,geometry)
4117:         finally:
4118:             self._pending_report_filters=None
4119: 
4120:     def open_stock_balance_report_flow(self):
4121:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4122:         if f.get("cancelled"): return None
4123:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4124: 
4125:     def open_grr_report_flow(self):
```
```text
4118:             self._pending_report_filters=None
4119: 
4120:     def open_stock_balance_report_flow(self):
4121:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4122:         if f.get("cancelled"): return None
4123:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4124: 
4125:     def open_grr_report_flow(self):
4126:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4127:         if f.get("cancelled"): return None
4128:         return self._open_report_child(self.report_grr,"GRN Report",f)
4129: 
4130:     def open_demand_report_flow(self):
4131:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4132:         if f.get("cancelled"): return None
4133:         return self._open_report_child(self.report_demand,"Demand Report",f)
4134: 
4135:     def open_issue_report_flow(self):
4136:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4137:         if f.get("cancelled"): return None
4138:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4132:         if f.get("cancelled"): return None
4133:         return self._open_report_child(self.report_demand,"Demand Report",f)
4134: 
4135:     def open_issue_report_flow(self):
4136:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4137:         if f.get("cancelled"): return None
4138:         return self._open_report_child(self.report_issue,"Issue Report",f)
4139: 
4140:     def open_party_report_flow(self):
4141:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4142:         if f.get("cancelled"): return None
4143:         return self._open_report_child(self.report_party,"Party Report",f)
4144: 
4145:     def _ask_stock_balance_filters(self):
4146:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4147:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4148:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4149:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4150:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4151:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4152:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4164:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4165:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4166:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4167:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4168:         e1.focus_set();self.wait_window(win);return result
4169: 
4170:     def stock_balance(self):
4171:         self.clearbody()
4172:         # Stock Balance is a Report sub-section and does not use the generic
4173:         # Save/Edit/Delete/Cancel/Print action strip.
4174:         children=self.body.winfo_children()
4175:         if children:
4176:             children[0].destroy()
4177:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4178:         if initial.get("cancelled"):
4179:             self.dashboard(); return
4180:         top=ttk.Frame(self.body);top.pack(fill="x")
4181:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4182:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4183:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4184:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4194:             for typ,qty in self.conn.execute(q,params):
4195:                 if typ=="GRR":gr+=float(qty or 0)
4196:                 elif typ=="ISSUE":iss+=float(qty or 0)
4197:             return opening_before,gr,iss,opening_before+gr-iss
4198:         def header_summary():
4199:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4200:         def load():
4201:             for i in tr.get_children():tr.delete(i)
4202:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4203:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4204:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4205:             sql+=" ORDER BY code"
4206:             for r in self.conn.execute(sql,params):
4207:                 op,gr,iss,cur=period(r[0],r[3])
4208:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4209:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4210:         def reopen_filters():
4211:             initial2=self._ask_stock_balance_filters()
4212:             if initial2.get("cancelled"):return
4213:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4214:             load()
```
```text
4252:         """
4253:         if typ=="demand": self.demand()
4254:         elif typ=="grr": self.grr()
4255:         else: self.issue()
4256:         loader=getattr(self,"_active_form_loader",None)
4257:         if loader: loader(str(no))
4258: 
4259:     def _edit_from_selector(self, typ, var, loader):
4260:         """Top Edit action: load the saved document directly into the current form.
4261:         If nothing is selected, use the newest saved document; never open a popup.
4262:         """
4263:         text=var.get().strip()
4264:         if text:
4265:             no=text.split(" -> ",1)[0].strip()
4266:         else:
4267:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4268:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4269:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4270:             if not r:
4271:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4272:                 return
```
```text
4269:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4270:             if not r:
4271:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4272:                 return
4273:             no=str(r[0])
4274:             var.set(no)
4275:         loader(no)
4276: 
4277:     def show_saved_records(self,typ):
4278:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4279:         if typ=="demand":
4280:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4281:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4282:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4283:             for r in rows:
4284:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4285:                 r=list(r); r[1]=to_display_date(r[1])
4286:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4287:         elif typ=="grr":
4288:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4289:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4300:         def view():
4301:             a=tr.selection()
4302:             if not a:return
4303:             no=tr.item(a[0])["values"][0]
4304:             win.destroy();self.open_document_editor(typ,no)
4305:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4306:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4307:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4308:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4309: 
4310:     def documents(self):
4311:         self.clearbody()
4312:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4313:         specs=[
4314:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4315:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4316:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4317:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4318:             ("Material Issues","issue",("No","Date","Department"),
4319:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4320:         ]
```
```text
4316:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4317:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4318:             ("Material Issues","issue",("No","Date","Department"),
4319:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4320:         ]
4321:         for title,typ,cols,query in specs:
4322:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4323:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4324:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4325:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4326:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4327:             for r in self.conn.execute(query):
4328:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4329:             def edit_selected(t=tr,k=typ):
4330:                 a=t.selection()
4331:                 if not a:
4332:                     messagebox.showwarning("Edit", "Select a saved record first.")
4333:                     return
4334:                 no=t.item(a[0])["values"][0]
4335:                 self.open_document_editor(k,no)
4336:             def delete_selected(t=tr,k=typ):
```
```text
4331:                 if not a:
4332:                     messagebox.showwarning("Edit", "Select a saved record first.")
4333:                     return
4334:                 no=t.item(a[0])["values"][0]
4335:                 self.open_document_editor(k,no)
4336:             def delete_selected(t=tr,k=typ):
4337:                 a=t.selection()
4338:                 if not a:
4339:                     messagebox.showwarning("Delete", "Select a saved record first.")
4340:                     return
4341:                 no=t.item(a[0])["values"][0]
4342:                 if k=="demand":
4343:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4344:                 elif k=="grr":
4345:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4346:                 else:
4347:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4348:                 self.conn.commit();backup_database();self.documents()
4349:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4350:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4351:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4345:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4346:                 else:
4347:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4348:                 self.conn.commit();backup_database();self.documents()
4349:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4350:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4351:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4352:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4353:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4354:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4355:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4356: 
4357:     def doc_export_selected(self,typ,tr,fmt):
4358:         a=tr.selection()
4359:         if not a:
4360:             messagebox.showwarning("Export","Select a saved record first."); return
4361:         no=tr.item(a[0])["values"][0]
4362:         if fmt=="word": self.export_word(typ,no)
4363:         else: self.export_excel(typ,no)
4364: 
4365:     def doc_preview_selected(self,typ,tr):
```
```text
4360:             messagebox.showwarning("Export","Select a saved record first."); return
4361:         no=tr.item(a[0])["values"][0]
4362:         if fmt=="word": self.export_word(typ,no)
4363:         else: self.export_excel(typ,no)
4364: 
4365:     def doc_preview_selected(self,typ,tr):
4366:         a=tr.selection()
4367:         if not a:
4368:             messagebox.showwarning("Preview","Select a saved record first."); return
4369:         no=tr.item(a[0])["values"][0]
4370:         data=self._get_doc_data(typ,no)
4371:         if not data:
4372:             messagebox.showwarning("Preview","Document not found."); return
4373:         title,header,cols,rows=data
4374:         header_lines=header
4375:         self.show_preview_window(title,header_lines,cols,rows)
4376: 
4377:     def doc_print_selected(self,typ,tr):
4378:         a=tr.selection()
4379:         if not a: return
4380:         no=tr.item(a[0])["values"][0]
```
```text
4411:         def _print_loaded_document():
4412:             data=self._get_doc_data(typ,no)
4413:             if not data:
4414:                 messagebox.showwarning("Document","Document not found."); return
4415:             title,header,cols,rows=data
4416:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4417:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4418: 
4419:     def _report_filter_popup(self, title, include_party=False):
4420:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4421:         win,winbody=self._internal_window(title,"520x420")
4422:         done=tk.BooleanVar(value=False)
4423:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4424:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4425:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4426:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4427:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4428:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4429:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4430:         if include_party:
4431:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4425:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4426:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4427:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4428:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4429:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4430:         if include_party:
4431:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4432:         def ok():
4433:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4434:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4435:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4436:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4437: 
4438:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4439:         self.clearbody()
4440:         # Report sub-sections use their own report toolbar; remove only the
4441:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4442:         children=self.body.winfo_children()
4443:         if children:
4444:             children[0].destroy()
4445:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4446:         if f.get("cancelled"):
4447:             self.dashboard();return
4448:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4449:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4450:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4451:         def load():
4452:             for i in tr.get_children():tr.delete(i)
4453:             params,where=params_builder(f)
4454:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4455:             for r in self.conn.execute(sql,params):
4456:                 vals=list(r)
4457:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4458:                 tr.insert("","end",values=vals)
4459:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4460:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4461:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4462:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4463:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4464:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4465:         def open_find_report():
4466:             state_find={"index":-1}
```
```text
4472:                 order=children[start:]+children[:start]
4473:                 for iid in order:
4474:                     vals=tr.item(iid,"values")
4475:                     if any(text in str(v).lower() for v in vals):
4476:                         state_find["index"]=children.index(iid)
4477:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4478:                 return False
4479:             self._open_exact_find_text_popup(search_fn)
4480:         self._item_master_find_callback=open_find_report
4481:         load()
4482:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4483: 
4484:     def report_grr(self):
4485:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4486:         def pb(f):
4487:             w=[];p=[]
4488:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4489:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4490:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4491:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4492:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4487:             w=[];p=[]
4488:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4489:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4490:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4491:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4492:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4493:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4494:             return p,w
4495:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4496: 
4497:     def report_demand(self):
4498:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4499:         def pb(f):
4500:             w=[];p=[]
4501:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4502:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4503:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4504:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4505:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4506:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4507:             return p,w
```
```text
4500:             w=[];p=[]
4501:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4502:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4503:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4504:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4505:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4506:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4507:             return p,w
4508:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4509: 
4510:     def report_issue(self):
4511:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4512:         def pb(f):
4513:             w=[];p=[]
4514:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4515:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4516:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4517:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4518:             return p,w
4519:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4520: 
```
```text
4513:             w=[];p=[]
4514:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4515:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4516:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4517:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4518:             return p,w
4519:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4520: 
4521:     def report_party(self):
4522:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4523:         def pb(f):
4524:             w=[];p=[]
4525:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4526:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4527:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4528:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4529:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4530:             return p,w
4531:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4532: 
4533:     def reports(self):
```
```text
4531:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4532: 
4533:     def reports(self):
4534:         self.clearbody()
4535:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4536: 
4537:         # ================= GRN Details =================
4538:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4539:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4540:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4541:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4542:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4543:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4544: 
4545:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4546:         def load_grr_item(codev=None):
4547:             for i in tr.get_children(): tr.delete(i)
4548:             q=codev.get().strip() if codev else ""
4549:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4550:             for r in self.conn.execute(sql,(q,) if q else ()):
4551:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4557:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4558:         tr=self.make_tree(fr,grr_cols,grr_widths)
4559:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4560:             for i in tr.get_children(): tr.delete(i)
4561:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4562:             conds=[];params=[]
4563:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4564:             if td: conds.append("g.grr_date<=?");params.append(td)
4565:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4566:             for r in self.conn.execute(sql,params):
4567:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4568:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4569:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4570:         load_grr_date(fdv,tdv)
4571: 
4572:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4573:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4574:         party=tk.StringVar(value="ALL")
4575:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4576:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4577:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4573:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4574:         party=tk.StringVar(value="ALL")
4575:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4576:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4577:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4578:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4579:         def load_party(*_):
4580:             for i in tr.get_children(): tr.delete(i)
4581:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4582:             if party.get()=="ALL":
4583:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4584:             else:
4585:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4586:             for r in rows:
4587:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4588:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4589:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4590: 
4591:         # ================= Demand Details =================
4592:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4593:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4589:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4590: 
4591:         # ================= Demand Details =================
4592:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4593:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4594:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4595:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4596:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4597:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4598: 
4599:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4600:         def load_dem_item(codev=None):
4601:             for i in tr.get_children(): tr.delete(i)
4602:             q=codev.get().strip() if codev else ""
4603:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4604:             for r in self.conn.execute(sql,(q,) if q else ()):
4605:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4606:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4607:         tr=self.make_tree(fr,dem_cols,dem_widths)
4608:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4609:         load_dem_item(codev)
```
```text
4611:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4612:         tr=self.make_tree(fr,dem_cols,dem_widths)
4613:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4614:             for i in tr.get_children(): tr.delete(i)
4615:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4616:             conds=[];params=[]
4617:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4618:             if td: conds.append("d.demand_date<=?");params.append(td)
4619:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4620:             for r in self.conn.execute(sql,params):
4621:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4622:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4623:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4624:         load_dem_date(fdv,tdv)
4625: 
4626:         # ================= Material Issue Details =================
4627:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4628:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4629:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4630:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4631:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4624:         load_dem_date(fdv,tdv)
4625: 
4626:         # ================= Material Issue Details =================
4627:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4628:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4629:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4630:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4631:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4632:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4633: 
4634:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4635:         def load_iss_item(codev=None):
4636:             for i in tr.get_children(): tr.delete(i)
4637:             q=codev.get().strip() if codev else ""
4638:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4639:             for r in self.conn.execute(sql,(q,) if q else ()):
4640:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4641:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4642:         tr=self.make_tree(fr,iss_cols,iss_widths)
4643:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4644:         load_iss_item(codev)
```
```text
4646:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4647:         tr=self.make_tree(fr,iss_cols,iss_widths)
4648:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4649:             for i in tr.get_children(): tr.delete(i)
4650:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4651:             conds=[];params=[]
4652:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4653:             if td: conds.append("i.issue_date<=?");params.append(td)
4654:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4655:             for r in self.conn.execute(sql,params):
4656:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4657:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4658:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4659:         load_iss_date(fdv,tdv)
4660: 
4661:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4662: 
4663:     def print_item_master(self):
4664:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4665:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4666: 
```
```text
4663:     def print_item_master(self):
4664:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4665:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4666: 
4667:     def print_party_master(self):
4668:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4669:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4670: 
4671:     def print_report(self,kind):
4672:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4673:         if kind=="grr":
4674:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4675:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4676:         elif kind=="demand":
4677:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4678:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4679:         elif kind=="issue":
4680:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4681:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4682:         else:
4683:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4684:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4685:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4686: 
4687:     def print_stock(self):
4688:         rows=[]
4689:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4690:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4691:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4692:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4693: 
4694:     def print_ledger(self):
4695:         rows=[]
4696:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4697:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4698:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4699:                 running += x[3] if x[1]=="GRR" else -x[3]
4700:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4701:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4702: 
4703:     def _get_doc_data(self, typ, no):
4704:         """Header + line items for one saved document, used by the on-screen
```
```text
4770:             sig=doc.add_table(rows=2,cols=3)
4771:             labels=["Prepared By","Store Keeper","Store Incharge"]
4772:             for i,label in enumerate(labels):
4773:                 sig.cell(0,i).text="____________________"
4774:                 sig.cell(1,i).text=label
4775:                 for para in sig.cell(1,i).paragraphs:
4776:                     for run in para.runs: run.bold=True
4777:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4778:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4779:         doc.save(path)
4780:         self.open_file(path)
4781: 
4782:     def export_excel(self, typ, no):
4783:         if not no or not no.strip():
4784:             return messagebox.showwarning("Excel Export","Select a document first.")
4785:         if not XLSX_AVAILABLE:
4786:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4787:         data=self._get_doc_data(typ,no)
4788:         if not data:
4789:             return messagebox.showwarning("Excel Export","Document not found.")
4790:         title,header,cols,rows=data
```
```text
4812:             for col in range(1,4):
4813:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4814:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4815:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4816:         for col_cells in ws.columns:
4817:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4818:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4819:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4820:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4821:         wb.save(path)
4822:         self.open_file(path)
4823: 
4824:     def preview_pdf(self,typ,no):
4825:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4826:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4827:         data=self._get_doc_data(typ,no)
4828:         if not data:return messagebox.showwarning("Document","Document not found.")
4829:         title,header,cols,rows=data
4830:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4831:         page_size = landscape(A4) if typ == "grr" else A4
4832:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4827:         data=self._get_doc_data(typ,no)
4828:         if not data:return messagebox.showwarning("Document","Document not found.")
4829:         title,header,cols,rows=data
4830:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4831:         page_size = landscape(A4) if typ == "grr" else A4
4832:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4833: 
4834:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4835:         """Open the print dialog with a real visual preview of the exact report.
4836: 
4837:         The report is rendered to a temporary PDF only in memory/on disk for the
4838:         duration of printing.  It is deleted after the print dialog closes, so
4839:         the Print button does not leave a PDF report behind.  Printing uses the
4840:         rendered report page itself rather than rebuilding rows as plain text;
4841:         this keeps the printed page identical to the application's report.
4842:         """
4843:         # Printing is always prepared as an A4 landscape page. This only affects
4844:         # the print path; the rest of the application's UI/report logic is unchanged.
4845:         page_size = landscape(A4)
4846:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
4847:             messagebox.showwarning(
```
```text
4849:                 "The print preview/printing components are not available.\n\n"
4850:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
4851:             )
4852:             return
4853:         if not rows and not columns:
4854:             messagebox.showwarning("Print", "There is no data to print.")
4855:             return
4856:         try:
4857:             os.makedirs(REPORTS_DIR, exist_ok=True)
4858:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
4859:             self._pdf_table_report(key,title,columns,rows,page_size,
4860:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
4861:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
4862:             self._select_windows_printer_for_pdf(key)
4863:         except Exception as e:
4864:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
4865: 
4866:     def _select_windows_printer_for_pdf(self, path):
4867:         """Print dialog with an actual page preview, printer selection and direct GDI output.
4868: 
4869:         The preview is rendered from the exact PDF produced by the application,
```
```text
4899:         job=getattr(self, "_print_jobs", {}).get(path)
4900:         if job:
4901:             title, header_lines, columns, rows, source_page_size = job
4902:         else:
4903:             title=os.path.splitext(os.path.basename(path))[0]
4904:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
4905: 
4906:         try:
4907:             doc=fitz.open(path)
4908:             total_pages=max(1,doc.page_count)
4909:         except Exception as e:
4910:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
4911:             return
4912: 
4913:         win=tk.Toplevel(self)
4914:         win.title("Printing from Win32 application - Print")
4915:         win.geometry("900x620")
4916:         win.minsize(850,580)
4917:         win.transient(self)
4918:         win.configure(bg="#f0f0f0")
4919: 
```
```text
4925:             pass
4926: 
4927:         outer=tk.Frame(win,bg="#f0f0f0")
4928:         outer.pack(fill="both",expand=True)
4929:         outer.columnconfigure(1,weight=1)
4930:         outer.rowconfigure(0,weight=1)
4931: 
4932:         # Left side mirrors the familiar system printer dialog: printers and
4933:         # print options. Right side contains the actual report page preview.
4934:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
4935:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
4936:         left.grid_propagate(False)
4937:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
4938:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
4939:         printer_list.pack(fill="x")
4940:         for pr in printers: printer_list.insert("end",pr)
4941:         try: printer_list.selection_set(printers.index(default_printer))
4942:         except Exception: printer_list.selection_set(0)
4943: 
4944:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
4945:         copies=tk.IntVar(value=1)
```
```text
5018:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5019: 
5020:         bottom=tk.Frame(win,bg="#f0f0f0")
5021:         # `outer` already uses pack() in `win`; using grid() for another direct
5022:         # child of the same toplevel raises TclError. Keep the action bar in the
5023:         # same geometry-manager family so Print/Cancel are always visible.
5024:         bottom.pack(fill="x",padx=12,pady=(0,12))
5025:         bottom.columnconfigure(0,weight=1)
5026:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5027:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5028:         print_btn=ttk.Button(bottom,text="Print",width=12)
5029:         print_btn.grid(row=0,column=2,padx=(8,0))
5030: 
5031:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5032: 
5033:         def parse_page_selection(total):
5034:             if pages_mode.get()=="All pages": return list(range(total))
5035:             raw=page_range.get().strip()
5036:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5037:             selected=[]
5038:             for part in raw.split(","):
```
```text
5035:             raw=page_range.get().strip()
5036:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5037:             selected=[]
5038:             for part in raw.split(","):
5039:                 part=part.strip()
5040:                 if "-" in part:
5041:                     a,b=part.split("-",1); a=int(a); b=int(b)
5042:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5043:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5044:                     selected.extend(range(a-1,b))
5045:                 else:
5046:                     n=int(part)
5047:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5048:                     selected.append(n-1)
5049:             return list(dict.fromkeys(selected))
5050: 
5051:         def selected_printer():
5052:             sel=printer_list.curselection()
5053:             return printer_list.get(sel[0]) if sel else printers[0]
5054: 
5055:         def print_rendered_pages():
```
```text
5148:                 finally:
5149:                     if hprinter is not None:
5150:                         try: win32print.ClosePrinter(hprinter)
5151:                         except Exception: pass
5152:                     if hdc:
5153:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5154:                         except Exception: pass
5155: 
5156:                 # Print the exact rendered PDF page through the printer DC.
5157:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5158:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5159:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5160:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5161: 
5162:                 for copy_no in range(count):
5163:                     dc.StartDoc(str(title)[:80])
5164:                     doc_ok=False
5165:                     try:
5166:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5167:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5168:                             dc.StartPage()
```
```text
5167:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5168:                             dc.StartPage()
5169:                             page_ok=False
5170:                             try:
5171:                                 cell_w=printable_w/float(cols_n)
5172:                                 cell_h=printable_h/float(rows_n)
5173:                                 for j,page_index in enumerate(batch):
5174:                                     page=doc.load_page(page_index)
5175:                                     pdf_w=max(1.0,float(page.rect.width))
5176:                                     pdf_h=max(1.0,float(page.rect.height))
5177:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5178:                                     fit=max(0.25,min(fit,8.0))
5179:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5180:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5181:                                     target_w=max(1,int(cell_w*0.96))
5182:                                     target_h=max(1,int(cell_h*0.96))
5183:                                     ratio=min(target_w/img.width,target_h/img.height)
5184:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5185:                                     if (nw,nh)!=(img.width,img.height):
5186:                                         img=img.resize((nw,nh),Image.LANCZOS)
5187:                                     dib=ImageWin.Dib(img)
```
```text
5207: 
5208:                 status.set("Print job sent successfully")
5209:                 win.update_idletasks()
5210:                 win.after(500,close)
5211:             except Exception as e:
5212:                 status.set("Print failed: "+str(e))
5213:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5214: 
5215:         def close():
5216:             try: doc.close()
5217:             except Exception: pass
5218:             try: win.destroy()
5219:             except Exception: pass
5220:             # Only the temporary PDF created by the Print button is removed.
5221:             # Existing report PDFs passed through the legacy print path are preserved.
5222:             try:
5223:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5224:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5225:             except Exception: pass
5226: 
5227:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5223:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5224:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5225:             except Exception: pass
5226: 
5227:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5228:         bottom.winfo_children()[1].configure(command=close)
5229:         print_btn.configure(command=print_rendered_pages)
5230:         win.protocol("WM_DELETE_WINDOW",close)
5231:         win.bind("<Escape>",lambda e:close())
5232:         win.grab_set()
5233:         # Keep the requested printer defaults visibly selected; no manual
5234:         # adjustment is required before pressing Print.
5235:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5236:         win.after(120,lambda:render_preview(0))
5237:         win.focus_force()
5238: 
5239:     def print_pdf(self,path):
5240:         """Open a printer-selection window for a generated PDF."""
5241:         path=os.path.abspath(path)
5242:         if not os.path.exists(path):
5243:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5239:     def print_pdf(self,path):
5240:         """Open a printer-selection window for a generated PDF."""
5241:         path=os.path.abspath(path)
5242:         if not os.path.exists(path):
5243:             messagebox.showwarning("Print", "The report file could not be found.")
5244:             return
5245: 
5246:         if sys.platform.startswith("win"):
5247:             self._select_windows_printer_for_pdf(path)
5248:             return
5249: 
5250:         try:
5251:             subprocess.run(["lp", path], check=True)
5252:         except Exception as e:
5253:             messagebox.showwarning(
5254:                 "Print",
5255:                 "The operating system could not start printing.\n\n"
5256:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5257:             )
5258: 
5259:     def open_file(self,path):
```
```text
5254:                 "Print",
5255:                 "The operating system could not start printing.\n\n"
5256:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5257:             )
5258: 
5259:     def open_file(self,path):
5260:         try:
5261:             if sys.platform.startswith("win"): os.startfile(path)
5262:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5263:             else: subprocess.Popen(["xdg-open",path])
5264:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5265: 
5266:     def print_demand(self,no):
5267:         data=self._get_doc_data("demand",no)
5268:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5269:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5270:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5271:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5272: 
5273:     def print_grr(self,no):
5274:         data=self._get_doc_data("grr",no)
```
```text
5268:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5269:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5270:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5271:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5272: 
5273:     def print_grr(self,no):
5274:         data=self._get_doc_data("grr",no)
5275:         if not data:return messagebox.showwarning("Document","GRN not found.")
5276:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5277:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5278:         # GRN has a wide item table. Generate the PDF itself in landscape so
5279:         # the printer dialog and printer driver receive a landscape document
5280:         # instead of a portrait page with rotated/cropped content.
5281:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5282: 
5283:     def print_issue(self,no):
5284:         data=self._get_doc_data("issue",no)
5285:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5286:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5287:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5288:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
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
