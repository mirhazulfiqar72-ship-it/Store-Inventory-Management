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

- Lines: 372
- Functions: _safe_json_value(25-28), _table_columns(29-30), snapshot_db(31-39), _row_key(40-44), _index_snapshot(45-49), merge_local_changes(50-71), _snapshot_has_records(72-74), __init__(76-92), _read_url(93-103), status_text(104-109), _request(110-119), _get_meta(120-126), _get_snapshot(127-133), _load_json(134-142), _atomic_save_json(143-157), _save_state(158-162), _save_pending(163-167), _clear_pending(168-173), _get_lock_etag(174-183), _try_acquire_lock(184-190), _release_lock(191-199), initialize(200-248), replace_local(249-266), _write_remote(267-288), push_changes(289-308), maybe_pull(309-330), __init__(332-337), execute(338-346), executemany(347-351), commit(352-361), rollback(363-366), close(367-368), backup(369-370), __getattr__(371-372)

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
0206:         # A pending snapshot is the strongest local recovery source.
0207:         if isinstance(pending, dict) and isinstance(pending.get("snapshot"), dict):
0208:             local = pending["snapshot"]
0209:             self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
0210:         try:
0211:             remote = self._get_snapshot()
0212:             version, _ = self._get_meta()
```
```text
0206:         # A pending snapshot is the strongest local recovery source.
0207:         if isinstance(pending, dict) and isinstance(pending.get("snapshot"), dict):
0208:             local = pending["snapshot"]
0209:             self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
0210:         try:
0211:             remote = self._get_snapshot()
0212:             version, _ = self._get_meta()
0213:             if remote and remote.get("tables"):
0214:                 # Never discard a non-empty local database just because the
0215:                 # cloud has an older/partial snapshot. Merge local rows into
0216:                 # remote on startup, then publish the merged result.
0217:                 empty = {"schema": 1, "tables": {}}
0218:                 baseline = self.pending_base or empty
0219:                 if _snapshot_has_records(local) or self.pending_base is not None:
0220:                     merged = merge_local_changes(remote, baseline, local)
0221:                     if merged != remote:
0222:                         new_version = self._write_remote(merged)
0223:                         self.replace_local(conn, merged)
0224:                         self.last_remote_version = new_version
0225:                         self._save_state(merged)
0226:                     else:
```
```text
0221:                     if merged != remote:
0222:                         new_version = self._write_remote(merged)
0223:                         self.replace_local(conn, merged)
0224:                         self.last_remote_version = new_version
0225:                         self._save_state(merged)
0226:                     else:
0227:                         self.replace_local(conn, remote)
0228:                         self.last_remote_version = version
0229:                         self._save_state(remote)
0230:                 else:
0231:                     self.replace_local(conn, remote)
0232:                     self.last_remote_version = version
0233:                     self._save_state(remote)
0234:                 self.pending_base = None
0235:                 self.pending_error = None
0236:                 self._clear_pending()
0237:             else:
0238:                 new_version = self._write_remote(local)
0239:                 self.last_remote_version = new_version
0240:                 self._save_state(local)
0241:                 self._clear_pending()
```
```text
0237:             else:
0238:                 new_version = self._write_remote(local)
0239:                 self.last_remote_version = new_version
0240:                 self._save_state(local)
0241:                 self._clear_pending()
0242:                 self.pending_base = None
0243:                 self.pending_error = None
0244:         except Exception as exc:
0245:             # Firebase being offline must never delete the local data. Keep
0246:             # the local snapshot and retry on the next start/commit.
0247:             self.pending_error = str(exc)
0248:             self._save_pending(local, self.pending_base or state or {"schema": 1, "tables": {}})
0249:     def replace_local(self, conn: sqlite3.Connection, snapshot: Dict[str, Any]) -> None:
0250:         old_isolation = conn.isolation_level
0251:         try:
0252:             conn.execute("BEGIN")
0253:             for table in TABLES:
0254:                 cols = _table_columns(conn, table)
0255:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0256:                 conn.execute(f"DELETE FROM {table}")
0257:                 if not rows:
```
```text
0253:             for table in TABLES:
0254:                 cols = _table_columns(conn, table)
0255:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0256:                 conn.execute(f"DELETE FROM {table}")
0257:                 if not rows:
0258:                     continue
0259:                 insert_cols = [c for c in cols if c in rows[0]]
0260:                 placeholders = ",".join("?" for _ in insert_cols)
0261:                 sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0262:                 for row in rows:
0263:                     conn.execute(sql, [row.get(c) for c in insert_cols])
0264:             conn.commit()
0265:         finally:
0266:             conn.isolation_level = old_isolation
0267:     def _write_remote(self, snapshot: Dict[str, Any]) -> str:
0268:         token = f"{self.client_id}-{uuid.uuid4().hex}"
0269:         acquired = False
0270:         last_exc = None
0271:         for _ in range(10):
0272:             try:
0273:                 if self._try_acquire_lock(token):
```
```text
0272:             try:
0273:                 if self._try_acquire_lock(token):
0274:                     acquired = True
0275:                     break
0276:             except Exception as exc:
0277:                 last_exc = exc
0278:             time.sleep(0.35)
0279:         if not acquired:
0280:             raise RuntimeError(f"Could not acquire Firebase sync lock. {last_exc or ''}".strip())
0281:         try:
0282:             new_version = f"{time.time_ns()}-{self.client_id}"
0283:             self._request("PUT", "store_inventory/data.json", json=snapshot)
0284:             self._request("PUT", "store_inventory/_meta/version.json", json=new_version)
0285:             self._request("PUT", "store_inventory/_meta/updated_by.json", json=self.client_id)
0286:             return new_version
0287:         finally:
0288:             self._release_lock(token)
0289:     def push_changes(self, conn: sqlite3.Connection, baseline: Dict[str, Any]) -> bool:
0290:         if not self.enabled:
0291:             return True
0292:         local = snapshot_db(conn)
```
```text
0293:         try:
0294:             remote = self._get_snapshot() or {"schema": 1, "tables": {}}
0295:             merged = merge_local_changes(remote, baseline or {"schema": 1, "tables": {}}, local)
0296:             new_version = self._write_remote(merged)
0297:             self.replace_local(conn, merged)
0298:             self.last_remote_version = new_version
0299:             self.pending_base = None
0300:             self.pending_error = None
0301:             self._save_state(merged)
0302:             self._clear_pending()
0303:             return True
0304:         except Exception as exc:
0305:             self.pending_base = deepcopy(baseline)
0306:             self.pending_error = str(exc)
0307:             self._save_pending(local, baseline or {"schema": 1, "tables": {}})
0308:             return False
0309:     def maybe_pull(self, conn: sqlite3.Connection) -> bool:
0310:         if not self.enabled or self.pending_base is not None:
0311:             return False
0312:         now = time.monotonic()
0313:         if now - self.last_check < self.check_interval:
```
```text
0317:             version, _ = self._get_meta()
0318:             if not version or version == self.last_remote_version:
0319:                 return False
0320:             snapshot = self._get_snapshot()
0321:             if snapshot is None:
0322:                 return False
0323:             self.replace_local(conn, snapshot)
0324:             self.last_remote_version = version
0325:             self._save_state(snapshot)
0326:             self.pending_error = None
0327:             return True
0328:         except Exception as exc:
0329:             self.pending_error = str(exc)
0330:             return False
0331: class OnlineConnection:
0332:     def __init__(self, db_path: str, sync: FirebaseSync):
0333:         self._conn = sqlite3.connect(db_path, timeout=20)
0334:         self._conn.execute("PRAGMA busy_timeout=20000")
0335:         self.sync = sync
0336:         self._dirty = False
0337:         self._baseline: Optional[Dict[str, Any]] = None
```
```text
0330:             return False
0331: class OnlineConnection:
0332:     def __init__(self, db_path: str, sync: FirebaseSync):
0333:         self._conn = sqlite3.connect(db_path, timeout=20)
0334:         self._conn.execute("PRAGMA busy_timeout=20000")
0335:         self.sync = sync
0336:         self._dirty = False
0337:         self._baseline: Optional[Dict[str, Any]] = None
0338:     def execute(self, sql: str, params: Iterable[Any] = ()):
0339:         s = sql.lstrip().upper()
0340:         is_read = s.startswith("SELECT") or s.startswith("PRAGMA") or s.startswith("WITH") or s.startswith("EXPLAIN")
0341:         if is_read and not self._dirty and self._baseline is None:
0342:             self.sync.maybe_pull(self._conn)
0343:         elif not is_read and not self._dirty:
0344:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0345:             self._dirty = True
0346:         return self._conn.execute(sql, params)
0347:     def executemany(self, sql: str, seq_of_params):
0348:         if not self._dirty:
0349:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0350:             self._dirty = True
```
```text
0343:         elif not is_read and not self._dirty:
0344:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0345:             self._dirty = True
0346:         return self._conn.execute(sql, params)
0347:     def executemany(self, sql: str, seq_of_params):
0348:         if not self._dirty:
0349:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0350:             self._dirty = True
0351:         return self._conn.executemany(sql, seq_of_params)
0352:     def commit(self):
0353:         self._conn.commit()
0354:         # Make local persistence independent of Firebase availability.
0355:         durable_local.save(self._conn)
0356:         if self._dirty:
0357:             self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
0358:             # push_changes may merge remote rows back into SQLite.
0359:             durable_local.save(self._conn)
0360:         self._dirty = False
0361:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0362: 
0363:     def rollback(self):
```
```text
0356:         if self._dirty:
0357:             self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
0358:             # push_changes may merge remote rows back into SQLite.
0359:             durable_local.save(self._conn)
0360:         self._dirty = False
0361:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0362: 
0363:     def rollback(self):
0364:         self._conn.rollback()
0365:         self._dirty = False
0366:         self._baseline = None
0367:     def close(self):
0368:         self._conn.close()
0369:     def backup(self, target):
0370:         return self._conn.backup(target)
0371:     def __getattr__(self, name):
0372:         return getattr(self._conn, name)
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

- Lines: 5327
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-332), restore_database(334-351), stock(353-358), fmt_num(360-362), to_iso_date(364-373), to_display_date(375-383), fiscal_year_key(385-396), fiscal_year_range(398-401), normalize_code(403-411), format_code(413-422), attach_code_mask(424-450), set_digits(427-432), key(433-443), paste(445-448), bind_add_to_list(452-473), on_enter(455-466), __init__(477-494), _check_for_updates(496-501), _setup_style(503-539), _shade(542-547), on_close(549-554), redo_network_setup(556-572), backup_now(574-581), restore_backup(583-601), _ctrl_f(603-615), _open_exact_find_text_popup(617-662), do_find(638-647), close(648-655), _global_enter(664-676), wipe(678-679), login(681-710), do_login(696-707), change_password(712-762), save_password(734-756), logout(764-769), home(771-790), _restore_dashboard_after_internal_close(792-806), _ensure_mdi_host(808-829), _internal_window(831-916), normal_place(847-853), restore(854-861), maximize(862-868), minimize(869-884), close(885-909), open_inventory_codes_detail_flow(918-936), open_inventory_codes_with_filters(938-952), open_inventory_codes_report_window(954-1180), tbtn(972-977), balance_as_of(1034-1044), build_nav(1046-1068), selected_prefix(1070-1079), load(1081-1113), page_move(1115-1116), page_first(1117-1117), page_last(1118-1122), on_nav(1126-1127), find_popup(1130-1149), search_fn(1132-1147), print_report(1152-1155), export_pdf(1157-1159), export_word(1160-1162), export_excel(1163-1165), open_menu_window(1182-1204), close_window(1192-1199), _manual_check_update(1206-1210), _show_current_version(1212-1216), build_menu_bar(1218-1265), open_calendar_picker(1267-1315), pick(1285-1287), redraw(1289-1301), nav(1303-1307), make_date_field(1317-1324), clearbody(1326-1352), run_action(1341-1346), _portable_print_current(1354-1365), portable_print_dialog(1367-1440), build_receipt(1394-1412), send(1413-1426), refresh_printers(1427-1433), preview_tree(1442-1454), set_page_actions(1456-1464), _add_transaction_new_button(1466-1483), _report_header(1485-1549), _report_footer(1551-1557), _grr_signature_block(1559-1575), _finish_page(1577-1578), _wrap_text_to_width(1580-1605), fits(1587-1587), _pdf_table_report(1607-1676), table_header(1629-1634), show_preview_window(1678-1751), _safe_report_name(1753-1756), print_preview_window(1758-1761), _fallback_pdf_export(1763-1796), esc(1767-1768), add(1771-1773), _save_entry_report(1798-1818), export_preview_pdf(1820-1849), export_preview_word(1851-1891), export_preview_excel(1893-1929), make_tree(1931-1940), pick_item(1942-1963), choose(1943-1962), ld(1950-1954), sel(1956-1960), bind_item_lookup(1965-1982), lookup(1967-1980), _set_form_editable(1985-1998), walk(1988-1997), document_selector(2000-2034), refresh(2005-2016), selected(2017-2022), dashboard(2036-2148), load_details(2120-2144), _refresh_dashboard_kpis(2150-2164), dashboard_details(2166-2170), item_history(2172-2192), _ask_item_master_filters(2194-2278), finish(2247-2259), items(2280-2518), hierarchy(2321-2330), selected_prefix(2376-2389), balance_as_of(2391-2398), load(2400-2438), set_page(2440-2441), select_node(2443-2464), open_find(2470-2489), search_fn(2472-2487), visible_rows(2494-2496), print_inventory(2497-2501), export_inventory_word(2502-2504), export_inventory_excel(2505-2507), portable_inventory(2512-2514), inventory_codes(2520-2804), btn(2556-2561), close_editor(2597-2607), edit_cell(2609-2635), commit(2627-2633), rows_query(2637-2650), load(2652-2667), new_record(2669-2690), commit(2683-2687), selected_row(2692-2694), edit_record(2696-2704), save_record(2706-2749), delete_record(2751-2762), refresh(2764-2764), do_print(2765-2767), do_close(2768-2768), filter_grid(2786-2793), open_mto_inventory_flow(2806-2829), open_code_opening_flow(2831-2839), code_opening(2841-2842), _open_code_opening_popup(2844-2845), _open_code_opening_detail(2847-3090), norm(2917-2918), table_for(2920-2921), row_for(2923-2928), search_any_destination(2930-2943), desc_hit(2945-2949), clear_form(2951-2964), load_for_edit(2966-2987), check_duplicates(2989-3000), save_code(3005-3056), edit_action(3058-3062), delete_code(3064-3079), _mto_new_item_dialog(3092-3128), save(3108-3125), _item_filter_bar(3130-3142), _date_filter_bar(3144-3152), _ask_mto_inventory_filters(3154-3199), finish(3184-3192), mto_inventory(3201-3401), open_find(3235-3254), search_fn(3237-3252), hierarchy(3273-3277), rebuild_nav(3279-3290), mto_balance(3314-3323), load(3325-3367), set_page(3369-3369), select_node(3370-3379), visible_rows(3384-3384), do_print(3385-3389), export_word(3390-3392), export_excel(3393-3395), party_master(3403-3454), load(3413-3416), clear(3417-3421), new_form(3422-3423), save(3424-3430), load_party_row(3431-3435), on_party_select(3436-3437), edit(3439-3443), delete_party(3444-3450), user_management(3456-3540), sync_role(3483-3488), load(3492-3495), clear(3496-3499), edit(3500-3507), save(3508-3525), delete_user(3526-3537), _renumber_tree(3543-3546), demand(3548-3712), _restore_demand_tree_columns(3591-3597), add(3600-3608), edit_item(3610-3622), delete_item(3624-3632), new_form(3636-3642), save(3644-3660), delete_current(3664-3670), cancel_form(3671-3679), preview_now(3680-3690), edit_saved_demand(3691-3694), print_now(3695-3705), load_demand_into_form(3714-3726), refresh_saved_cache(3728-3740), grr(3742-3905), add(3774-3782), edit_item(3784-3794), delete_item(3796-3804), new_form(3808-3814), save(3816-3837), delete_current(3841-3847), cancel_form(3848-3856), preview_now(3857-3875), portable_current(3876-3879), edit_saved_grr(3881-3884), print_now(3885-3898), load_grr_into_form(3907-3919), issue(3921-4067), old_issue_qty(3950-3953), update_balance(3954-3962), add(3964-3973), edit_item(3975-3986), new_form(3990-3996), post(3998-4019), delete_current(4020-4026), cancel_form(4027-4035), preview_now(4036-4043), portable_current(4044-4046), load_saved_issue(4051-4053), edit_saved_issue(4054-4057), print_issue_now(4058-4063), load_issue_into_form(4069-4082), _ask_report_criteria(4084-4147), finish(4133-4141), _open_report_child(4149-4154), open_stock_balance_report_flow(4156-4159), open_grr_report_flow(4161-4164), open_demand_report_flow(4166-4169), open_issue_report_flow(4171-4174), open_party_report_flow(4176-4179), _ask_stock_balance_filters(4181-4204), ok(4196-4197), cancel(4198-4198), stock_balance(4206-4269), period(4222-4233), header_summary(4234-4235), load(4236-4245), reopen_filters(4246-4250), open_find_stock(4254-4267), search_fn(4256-4266), ledger(4271-4283), open_document_editor(4285-4293), _edit_from_selector(4295-4311), show_saved_records(4313-4344), view(4336-4340), documents(4346-4391), edit_selected(4365-4371), delete_selected(4372-4384), doc_export_selected(4393-4399), doc_preview_selected(4401-4411), doc_print_selected(4413-4421), load_document(4423-4453), _print_loaded_document(4447-4452), _report_filter_popup(4455-4472), ok(4468-4469), cancel(4470-4470), _report_window(4474-4518), load(4487-4494), hdr(4495-4495), open_find_report(4501-4515), search_fn(4503-4514), report_grr(4520-4531), pb(4522-4530), report_demand(4533-4544), pb(4535-4543), report_issue(4546-4555), pb(4548-4554), report_party(4557-4567), pb(4559-4566), reports(4569-4697), load_grr_item(4582-4587), load_grr_date(4595-4603), load_party(4615-4623), load_dem_item(4636-4641), load_dem_date(4649-4657), load_iss_item(4671-4676), load_iss_date(4684-4692), print_item_master(4699-4701), print_party_master(4703-4705), print_report(4707-4721), print_stock(4723-4728), print_ledger(4730-4737), _get_doc_data(4739-4767), export_word(4769-4816), export_excel(4818-4858), preview_pdf(4860-4868), _open_direct_printer(4870-4900), _select_windows_printer_for_pdf(4902-5273), render_preview(5027-5046), on_resize(5048-5050), parse_page_selection(5069-5085), selected_printer(5087-5089), print_rendered_pages(5091-5249), close(5251-5261), print_pdf(5275-5293), open_file(5295-5300), print_demand(5302-5307), print_grr(5309-5317), print_issue(5319-5324)

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
0792:     def _restore_dashboard_after_internal_close(self):
0793:         try:
0794:             if getattr(self, "_mdi_windows", []):
0795:                 return
0796:             host = getattr(self, "_mdi_host", None)
0797:             if host is not None and host.winfo_exists():
0798:                 host.place_forget()
```
```text
0877:             b.pack(side="left")
0878:             rb=tk.Button(item,text="□",font=("Segoe UI",8,"bold"),width=2,height=1,padx=0,pady=0,
0879:                          command=lambda:(restore(),maximize()),relief="flat",bd=0,bg="#e7e7e7")
0880:             rb.pack(side="left")
0881:             xb=tk.Button(item,text="×",font=("Segoe UI",9,"bold"),width=2,height=1,padx=0,pady=0,
0882:                          command=close,relief="flat",bd=0,bg="#e7e7e7")
0883:             xb.pack(side="left")
0884:             state["task"]=item
0885:         def close():
0886:             try:
0887:                 task=state.get("task")
0888:                 if task and task.winfo_exists(): task.destroy()
0889:             except Exception: pass
0890:             try:
0891:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
0892:             except Exception: pass
0893:             try: outer.destroy()
0894:             except Exception: pass
0895:             if not getattr(self,"_mdi_windows",[]):
0896:                 self._mdi_host.place_forget()
0897:                 self._restore_dashboard_after_internal_close()
```
```text
0942:             return None
0943:         self._inventory_codes_filter=criteria
0944:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0945:         try:
0946:             self.items(container=body)
0947:             win.lift()
0948:             return win
0949:         except Exception:
0950:             try: win._internal_close()
0951:             except Exception: pass
0952:             raise
0953: 
0954:     def open_inventory_codes_report_window(self, criteria=None):
0955:         """Open Inventory Codes as a real report-style child window.
0956: 
0957:         This intentionally mirrors the supplied Preview Report workflow: a
0958:         separate resizable/maximizable window with a left navigation tree,
0959:         compact report toolbar, Find dialog, and print/export commands.
0960:         The main application remains open behind it.
0961:         """
0962:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
0959:         compact report toolbar, Find dialog, and print/export commands.
0960:         The main application remains open behind it.
0961:         """
0962:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
0963:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
0964:         }
0965:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0966: 
0967:         # --- report-style toolbar ---
0968:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
0969:         toolbar.pack(fill="x",side="top")
0970:         toolbar.pack_propagate(False)
0971: 
0972:         def tbtn(text,cmd,width=9):
0973:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
0974:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
0975:                          padx=3,pady=1)
0976:             b.pack(side="left",padx=2,pady=6)
0977:             return b
0978: 
0979:         # --- main report body ---
```
```text
0990:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
0991:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
0992:         navscroll.config(command=code_tree.yview)
0993:         navscroll.pack(side="right",fill="y")
0994:         code_tree.pack(side="left",fill="both",expand=True)
0995: 
0996:         right=tk.Frame(content,bg="#EDEDED")
0997:         right.pack(side="left",fill="both",expand=True)
0998:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
0999:         reportbar.pack(fill="x")
1000:         reportbar.pack_propagate(False)
1001:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
1002:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
1003:         tab.pack(side="left",padx=4,pady=2)
1004:         titlevar=tk.StringVar(value="Inventory Summary")
1005:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
1006:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
1007: 
1008:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
1009:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
1010:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1144:                     vals=tree.item(iid,"values")
1145:                     if str(vals[1]).lower()==str(target).lower():
1146:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1147:                 return True
1148:             self._open_exact_find_text_popup(search_fn)
1149:             self._item_master_find_callback=find_popup
1150: 
1151: 
1152:         def print_report():
1153:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1154:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1155:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1156: 
1157:         def export_pdf():
1158:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1159:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1160:         def export_word():
1161:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1162:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1163:         def export_excel():
1164:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1160:         def export_word():
1161:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1162:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1163:         def export_excel():
1164:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1165:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1166: 
1167:         tbtn("Find",find_popup,7)
1168:         tbtn("Print",print_report,7)
1169:         tbtn("PDF",export_pdf,6)
1170:         tbtn("Word",export_word,6)
1171:         tbtn("Excel",export_excel,6)
1172:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1173:         tbtn("Refresh",load,8)
1174:         tbtn("Close",win._internal_close,7)
1175:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1176:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1177: 
1178:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1179:         build_nav(); load(); win.focus_force()
1180:         return win
```
```text
1190:         self.body=frame
1191:         closed={"done":False}
1192:         def close_window():
1193:             if closed["done"]: return
1194:             closed["done"]=True
1195:             if getattr(self,"body",None) is frame: self.body=old_body
1196:             self._page_actions=old_actions
1197:             self._item_master_find_callback=old_find
1198:             try: win._internal_close()
1199:             except Exception: win.destroy()
1200:         win._internal_close=close_window
1201:         try:
1202:             method(); self.update_idletasks(); win.lift(); return win
1203:         except Exception:
1204:             close_window(); raise
1205: 
1206:     def _manual_check_update(self):
1207:         try:
1208:             updater.check_for_update(self, manual=True)
1209:         except Exception as e:
1210:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1214:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1215:         except Exception as e:
1216:             messagebox.showerror("Current Version", str(e), parent=self)
1217: 
1218:     def build_menu_bar(self):
1219:         """Professional section / sub-section menu bar, ERP style:
1220:         Inventory > Item Master
1221:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1222:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1223:         Edit > Change Password, User Management
1224:         Help > Backup Now, Restore Backup, Network Setup
1225:         """
1226:         menubar=tk.Menu(self)
1227: 
1228:         m_inv=tk.Menu(menubar,tearoff=0)
1229:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1230:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1231:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1232:         menubar.add_cascade(label="Inventory",menu=m_inv)
1233: 
1234:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1234:         m_trans=tk.Menu(menubar,tearoff=0)
1235:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1236:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1237:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1238:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1239:         menubar.add_cascade(label="Transaction",menu=m_trans)
1240: 
1241:         m_rep=tk.Menu(menubar,tearoff=0)
1242:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1243:         m_rep.add_separator()
1244:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1245:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1246:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1247:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1248:         menubar.add_cascade(label="Report",menu=m_rep)
1249: 
1250:         m_edit=tk.Menu(menubar,tearoff=0)
1251:         m_edit.add_command(label="Change Password",command=self.change_password)
1252:         if self.is_admin:
1253:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1254:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1249: 
1250:         m_edit=tk.Menu(menubar,tearoff=0)
1251:         m_edit.add_command(label="Change Password",command=self.change_password)
1252:         if self.is_admin:
1253:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1254:         menubar.add_cascade(label="Edit",menu=m_edit)
1255: 
1256:         m_help=tk.Menu(menubar,tearoff=0)
1257:         m_help.add_command(label="Backup Now",command=self.backup_now)
1258:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1259:         m_help.add_command(label="Current Version",command=self._show_current_version)
1260:         if self.is_admin:
1261:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1262:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1263:         menubar.add_cascade(label="Help",menu=m_help)
1264: 
1265:         self.config(menu=menubar)
1266: 
1267:     def open_calendar_picker(self, var):
1268:         """Small month-grid calendar popup. Picking a day sets `var` to
1269:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1322:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1323:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1324:         return f
1325: 
1326:     def clearbody(self):
1327:         self._portable_print_context=None
1328:         for w in self.body.winfo_children(): w.destroy()
1329:         self._page_actions = {
1330:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1331:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1332:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1333:             "cancel": lambda: self.dashboard(),
1334:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1335:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1336:         }
1337:         # Single SAP-style toolbar at the very top.
1338:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1339:         self._page_action_bar=bar
1340:         self._page_action_first_button=None
1341:         def run_action(k):
1342:             if k=="edit" and not self.can_edit:
```
```text
1339:         self._page_action_bar=bar
1340:         self._page_action_first_button=None
1341:         def run_action(k):
1342:             if k=="edit" and not self.can_edit:
1343:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1344:             if k=="delete" and not self.can_delete:
1345:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1346:             self._page_actions[k]()
1347:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1348:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1349:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1350:             b.pack(side="left",padx=(0,2))
1351:             if self._page_action_first_button is None: self._page_action_first_button=b
1352:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1353: 
1354:     def _portable_print_current(self):
1355:         ctx=getattr(self,"_portable_print_context",None)
1356:         if not ctx:
1357:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1358:             return
1359:         try:
```
```text
1361:             if not data: return
1362:             title,header,columns,rows=data
1363:             self.portable_print_dialog(title,header,columns,rows)
1364:         except Exception as e:
1365:             messagebox.showerror("Portable Printer",str(e))
1366: 
1367:     def portable_print_dialog(self,title,header_lines,columns,rows):
1368:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1369:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1370:         if not WIN32PRINT_AVAILABLE:
1371:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1372:             return
1373:         try:
1374:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1375:         except Exception as e:
1376:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1377:             return
1378:         if not printers:
1379:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1380:             return
1381:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1431:                 if vals and pv.get() not in vals: pv.set(vals[0])
1432:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1433:             except Exception as ex: status.set(str(ex))
1434:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1435:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1436:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1437:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1438:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1439:         win.bind("<Escape>",lambda e:win._internal_close())
1440:         win.focus_force()
1441: 
1442:     def preview_tree(self, title, tree, header_lines=None):
1443:         """Preview the exact rows currently visible in a Treeview."""
1444:         cols=list(tree["columns"])
1445:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1446:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1447:         if not rows:
1448:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1449:             return
1450:         widths=[]
1451:         for c in cols:
```
```text
1448:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1449:             return
1450:         widths=[]
1451:         for c in cols:
1452:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1453:             except Exception: widths.append(100)
1454:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1455: 
1456:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1457:         self._page_actions.update({
1458:             "save": save or self._page_actions.get("save"),
1459:             "edit": edit or self._page_actions.get("edit"),
1460:             "delete": delete or self._page_actions.get("delete"),
1461:             "cancel": cancel or self._page_actions.get("cancel"),
1462:             "print": print or self._page_actions.get("print"),
1463:             "preview": preview or self._page_actions.get("preview"),
1464:         })
1465: 
1466:     def _add_transaction_new_button(self, command):
1467:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1468:         if bar is None or first is None: return
```
```text
1477:         sep.pack(side="left",fill="y",padx=4)
1478:         for w in existing:
1479:             try:
1480:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1481:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1482:                 else: w.pack(side="left")
1483:             except Exception: pass
1484: 
1485:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1486:         """Draw a consistent professional report header and return the first table Y.
1487: 
1488:         For GRN Receipt reports the document number is shown on the left and
1489:         the GRN Date is deliberately shown on the right in a bordered document
1490:         information panel.
1491:         """
1492:         W,H=page_size
1493:         if y_top is None: y_top=H-24
1494:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1495:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1496:         if os.path.exists(LOGO_FILE):
1497:             try:
```
```text
1490:         information panel.
1491:         """
1492:         W,H=page_size
1493:         if y_top is None: y_top=H-24
1494:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1495:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1496:         if os.path.exists(LOGO_FILE):
1497:             try:
1498:                 from reportlab.lib.utils import ImageReader
1499:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1500:             except Exception:
1501:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1502:         else:
1503:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1504:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1505:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1506:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1507:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1508: 
1509:         # Professional document information box.
1510:         info_top=logo_y-12
```
```text
1543:                 # naturally occupies the right-hand cell when supplied second.
1544:                 c.setFont("Helvetica-Bold",7)
1545:                 c.drawString(xx,yy,(label+":")[:28])
1546:                 c.setFont("Helvetica",7)
1547:                 c.drawString(xx+58,yy,val[:58])
1548:             return box_y-12
1549:         return info_top-6
1550: 
1551:     def _report_footer(self, c, page_no, page_size=A4):
1552:         W,H=page_size
1553:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1554:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1555:         c.drawString(24,13,REPORT_FOOTER)
1556:         c.drawRightString(W-24,13,f"Page {page_no}")
1557:         c.setFillColorRGB(0,0,0)
1558: 
1559:     def _grr_signature_block(self, c, y, page_size=A4):
1560:         """Draw the three requested transaction-document signature lines."""
1561:         W,H=page_size
1562:         labels=["Prepared By","Store Keeper","Store Incharge"]
1563:         block_h=70
```
```text
1570:             x=left+i*col_w
1571:             c.setLineWidth(0.6)
1572:             c.line(x+30,top-34,x+col_w-30,top-34)
1573:             c.setFont("Helvetica-Bold",7)
1574:             c.drawCentredString(x+col_w/2,top-48,label)
1575:         return True
1576: 
1577:     def _finish_page(self, c, page_no, page_size=A4):
1578:         self._report_footer(c,page_no,page_size); c.showPage()
1579: 
1580:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1581:         """Word-wrap `text` into a list of lines that each fit inside
1582:         max_width (points) at the given font, breaking mid-word only when a
1583:         single word is itself wider than the column."""
1584:         text=str(text) if text is not None else ""
1585:         if not text:
1586:             return [""]
1587:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1588:         lines=[]; cur=""
1589:         for word in text.split(" "):
1590:             trial=(cur+" "+word).strip() if cur else word
```
```text
1599:                     mid=(lo+hi)//2
1600:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1601:                     else: hi=mid-1
1602:                 lines.append(w[:fit_at]); w=w[fit_at:]
1603:             cur=w
1604:         if cur: lines.append(cur)
1605:         return lines or [""]
1606: 
1607:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1608:         """Create a paginated professional PDF with logo, bordered information,
1609:         GRR signature lines and page numbers. Also keep the same report data in
1610:         memory so the built-in Windows printer dialog can print directly without
1611:         requiring a PDF application's PrintTo association."""
1612:         if not hasattr(self, "_print_jobs"):
1613:             self._print_jobs = {}
1614:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1615:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1616:         page=1
1617:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1618:         usable=W-56
1619:         n=max(1,len(headers))
```
```text
1641:             if desc_idx is not None and desc_idx < len(r):
1642:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1643:             else:
1644:                 desc_lines=[""]
1645:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1646:             # Reserve room on the final page for the three transaction signatures + footer.
1647:             reserve=120 if is_transaction_doc else 42
1648:             if y-row_h<reserve:
1649:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1650:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1651:             # Item rows are intentionally border-free. The section/header remains
1652:             # professional while avoiding the unwanted boxed line around each
1653:             # individual printed item row. Description is drawn separately
1654:             # below (auto-fit / wrapped), so it is skipped in this pass.
1655:             for ci,(xx,val) in enumerate(zip(xs,r)):
1656:                 if ci==desc_idx: continue
1657:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1658:             if desc_idx is not None and desc_idx < len(r):
1659:                 for li,ln in enumerate(desc_lines):
1660:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1661:             y-=row_h
```
```text
1656:                 if ci==desc_idx: continue
1657:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1658:             if desc_idx is not None and desc_idx < len(r):
1659:                 for li,ln in enumerate(desc_lines):
1660:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1661:             y-=row_h
1662:         if is_transaction_doc:
1663:             # Keep the three requested transaction signatures at the physical bottom
1664:             # final page, immediately above the report footer.  If the item
1665:             # table reaches this reserved area, start a fresh final page.
1666:             bottom_sig_y = 138
1667:             if y < 165:
1668:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1669:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1670:             # Draw signatures at a fixed bottom position so they never float
1671:             # directly after the last item row.
1672:             self._grr_signature_block(c,bottom_sig_y,page_size)
1673:         self._report_footer(c,page,page_size); c.save()
1674:         if auto_print:
1675:             self.print_pdf(path)
1676:         return path
```
```text
1670:             # Draw signatures at a fixed bottom position so they never float
1671:             # directly after the last item row.
1672:             self._grr_signature_block(c,bottom_sig_y,page_size)
1673:         self._report_footer(c,page,page_size); c.save()
1674:         if auto_print:
1675:             self.print_pdf(path)
1676:         return path
1677: 
1678:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1679:         """Professional on-screen preview showing bordered document information
1680:         and a bordered item section. GRN Date is displayed in the right column."""
1681:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1682:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1683:         # Preview intentionally hides the company logo and company name.
1684:         # The actual generated/printed PDF still contains both via
1685:         # _report_header(), so only the on-screen preview is affected.
1686:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1687:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1688:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1689: 
1690:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
```
```text
1711:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1712: 
1713:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1714:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1715:         tr=self.make_tree(items,columns,widths)
1716:         for r in rows: tr.insert("", "end", values=r)
1717: 
1718:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1719:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1720:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1721:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1722:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1723:         win.bind("<Control-f>",bind_preview_find)
1724:         win.bind("<Control-F>",bind_preview_find)
1725: 
1726:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1727:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1728:         if is_transaction_preview:
1729:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1730:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1731:                 sig.columnconfigure(i,weight=1)
```
```text
1729:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1730:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1731:                 sig.columnconfigure(i,weight=1)
1732:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1733:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1734:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1735: 
1736:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1737:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1738:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1739:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1740:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1741:         if on_save:
1742:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1743:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1744:         if not is_transaction_preview:
1745:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1746:         # IMPORTANT: this must remain a normal top-level window (not transient
1747:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1748:         # exactly like the Preview Report window in the supplied recording.
1749:         # The Find dialog is opened from this window and is independent.
```
```text
1742:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1743:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1744:         if not is_transaction_preview:
1745:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1746:         # IMPORTANT: this must remain a normal top-level window (not transient
1747:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1748:         # exactly like the Preview Report window in the supplied recording.
1749:         # The Find dialog is opened from this window and is independent.
1750:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1751:         win.focus_force()
1752: 
1753:     def _safe_report_name(self, title, extension):
1754:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1755:         safe=safe.replace(" ","_") or "Preview"
1756:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1757: 
1758:     def print_preview_window(self, title, header_lines, columns, rows):
1759:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1760:         self._open_direct_printer(title, header_lines, columns, rows,
1761:                                   landscape(A4) if len(columns) > 8 else A4)
1762: 
```
```text
1755:         safe=safe.replace(" ","_") or "Preview"
1756:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1757: 
1758:     def print_preview_window(self, title, header_lines, columns, rows):
1759:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1760:         self._open_direct_printer(title, header_lines, columns, rows,
1761:                                   landscape(A4) if len(columns) > 8 else A4)
1762: 
1763:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1764:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1765:         This keeps the Export PDF button functional on a machine where the bundled
1766:         ReportLab package cannot be imported."""
1767:         def esc(v):
1768:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1769:         W,H=842,595
1770:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1771:         def add(txt,size=8,leading=11):
1772:             lines.append(f"/F1 {size} Tf")
1773:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1774:         add(str(title),12,16)
1775:         for h in header_lines or []:
```
```text
1782:         lines.append("ET")
1783:         stream="\n".join(lines).encode("latin-1","replace")
1784:         objs=[]
1785:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1786:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1787:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1788:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1789:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1790:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1791:         for i,obj in enumerate(objs,1):
1792:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1793:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1794:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1795:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1796:         with open(path,"wb") as f: f.write(out)
1797: 
1798:     def _save_entry_report(self, title, header_lines, columns, rows):
1799:         try:
1800:             os.makedirs(REPORTS_DIR, exist_ok=True)
1801:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1802:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```
```text
1795:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1796:         with open(path,"wb") as f: f.write(out)
1797: 
1798:     def _save_entry_report(self, title, header_lines, columns, rows):
1799:         try:
1800:             os.makedirs(REPORTS_DIR, exist_ok=True)
1801:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1802:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
1803:             path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
1804:             page_size = landscape(A4) if len(columns) > 8 else A4
1805:             if REPORTLAB:
1806:                 self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
1807:             else:
1808:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1809:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1810:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1811:             with open(path, "rb") as f:
1812:                 if f.read(5) != b"%PDF-":
1813:                     raise IOError("Generated report is not a valid PDF.")
1814:             self._last_entry_report_path = path
1815:             return path
```
```text
1809:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1810:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1811:             with open(path, "rb") as f:
1812:                 if f.read(5) != b"%PDF-":
1813:                     raise IOError("Generated report is not a valid PDF.")
1814:             self._last_entry_report_path = path
1815:             return path
1816:         except Exception as exc:
1817:             self._last_entry_report_path = None
1818:             return None
1819: 
1820:     def export_preview_pdf(self, title, header_lines, columns, rows):
1821:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1822:         try:
1823:             os.makedirs(REPORTS_DIR, exist_ok=True)
1824:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1825:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1826:             generated = False
1827:             if REPORTLAB:
1828:                 try:
1829:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
```
```text
1826:             generated = False
1827:             if REPORTLAB:
1828:                 try:
1829:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1830:                     generated = True
1831:                 except Exception:
1832:                     generated = False
1833:             if not generated:
1834:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1835:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1836:                 raise IOError("The PDF file was not created in the Reports folder.")
1837:             with open(path, "rb") as pf:
1838:                 signature = pf.read(5)
1839:             if signature != b"%PDF-":
1840:                 raise IOError("The generated file is not a valid PDF.")
1841:             self._last_report_path = path
1842:             try:
1843:                 webbrowser.open("file://" + path)
1844:             except Exception:
1845:                 self.open_file(path)
1846:             return path
```
```text
1840:                 raise IOError("The generated file is not a valid PDF.")
1841:             self._last_report_path = path
1842:             try:
1843:                 webbrowser.open("file://" + path)
1844:             except Exception:
1845:                 self.open_file(path)
1846:             return path
1847:         except Exception as e:
1848:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1849:             return None
1850: 
1851:     def export_preview_word(self, title, header_lines, columns, rows):
1852:         """Export exactly what is visible in the current preview to Word."""
1853:         if not DOCX_AVAILABLE:
1854:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1855:         path=self._safe_report_name(title,"docx")
1856:         doc=Document()
1857:         sec=doc.sections[0]
1858:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1859:         sec.header.paragraphs[0].runs[0].bold=True
1860:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
```
```text
1882:             doc.add_paragraph("")
1883:             sig=doc.add_table(rows=2,cols=3)
1884:             labels=["Prepared By","Store Keeper","Store Incharge"]
1885:             for i,label in enumerate(labels):
1886:                 sig.cell(0,i).text="____________________"
1887:                 sig.cell(1,i).text=label
1888:                 for para in sig.cell(1,i).paragraphs:
1889:                     for run in para.runs: run.bold=True
1890:         doc.save(path)
1891:         self.open_file(path)
1892: 
1893:     def export_preview_excel(self, title, header_lines, columns, rows):
1894:         """Export exactly what is visible in the current preview to Excel."""
1895:         if not XLSX_AVAILABLE:
1896:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
1897:         path=self._safe_report_name(title,"xlsx")
1898:         wb=openpyxl.Workbook(); ws=wb.active
1899:         ws.title="Preview"
1900:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
1901:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1902:         if not is_transaction_preview:
```
```text
1920:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
1921:             for col in range(1,4):
1922:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
1923:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
1924:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
1925:         for col_cells in ws.columns:
1926:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
1927:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
1928:         wb.save(path)
1929:         self.open_file(path)
1930: 
1931:     def make_tree(self,parent,cols,widths=None):
1932:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
1933:         tr=ttk.Treeview(fr,columns=cols,show="headings")
1934:         for i,c in enumerate(cols):
1935:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
1936:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
1937:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
1938:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
1939:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
1940:         return tr
```
```text
1993:                     w.state(["!disabled"] if editable else ["disabled"])
1994:             except Exception:
1995:                 try: w.configure(state="normal" if editable else "disabled")
1996:                 except Exception: pass
1997:             for ch in w.winfo_children(): walk(ch)
1998:         for root in roots: walk(root)
1999: 
2000:     def document_selector(self, parent, label, typ, var, load_callback):
2001:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
2002:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
2003:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
2004:         combo.pack(side="left", padx=4)
2005:         def refresh():
2006:             vals=[]
2007:             if typ=="demand":
2008:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
2009:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
2010:             elif typ=="grr":
2011:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
2012:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
2013:             else:
```
```text
2020:             no=text.split(" -> ",1)[0].strip()
2021:             var.set(no)
2022:             load_callback(no)
2023:         combo.bind("<<ComboboxSelected>>", selected)
2024:         combo.bind("<Return>", selected)
2025:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2026:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2027:         refresh()
2028:         # Keep the currently open transaction's saved-record list live.
2029:         # Each save calls refresh_saved_cache(), so newly saved records appear
2030:         # immediately without closing/reopening the window or pressing Refresh.
2031:         if not hasattr(self, "_document_selector_refreshers"):
2032:             self._document_selector_refreshers = {}
2033:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2034:         return combo
2035: 
2036:     def dashboard(self):
2037:         # Dashboard-only visual refresh. All existing data queries, filters,
2038:         # callbacks and report/detail behavior are intentionally preserved.
2039:         self.clearbody()
2040:         c=self.conn
```
```text
2121:             for x in tr.get_children(): tr.delete(x)
2122:             params=[];where=[]
2123:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2124:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2125:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2126:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2127:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2128:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2129:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2130:                    FROM transactions t JOIN items i ON i.code=t.code"""
2131:             if where: sql += " WHERE " + " AND ".join(where)
2132:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2133:             rows=list(c.execute(sql,params))
2134:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2135:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2136:             bal_after={}
2137:             for txid,cc,typ,qty in alltx:
2138:                 running.setdefault(cc,0.0)
2139:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2140:                 bal_after[txid]=running[cc]
2141:             for r in rows:
```
```text
2516:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2517:         load()
2518:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2519: 
2520:     def inventory_codes(self):
2521:         """Inventory Codes using the classic desktop inventory interface.
2522: 
2523:         This screen intentionally follows the uploaded Inventory Management
2524:         reference: a simple module title, compact New/Edit/Delete/Save/
2525:         Refresh/Print/Close action row, and a full-width editable data grid.
2526:         All records come from the V18 database, so existing inventory data is
2527:         preserved rather than recreated.
2528:         """
2529:         self.clearbody()
2530:         # Remove the generic SAP action row; this page owns its own classic
2531:         # action row just like the reference Inventory/Items screen.
2532:         if self.body.winfo_children():
2533:             try:
2534:                 self.body.winfo_children()[0].destroy()
2535:             except Exception:
2536:                 pass
```
```text
2589:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2590:         if filter_text:
2591:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2592:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2593: 
2594:         editing={"id":None,"new":False}
2595:         cell_editor={"widget":None}
2596: 
2597:         def close_editor(save_value=False):
2598:             w=cell_editor.get("widget")
2599:             if not w:
2600:                 return
2601:             try:
2602:                 if save_value:
2603:                     w.event_generate("<Return>")
2604:                 w.destroy()
2605:             except Exception:
2606:                 pass
2607:             cell_editor["widget"]=None
2608: 
2609:         def edit_cell(event=None):
```
```text
2619:             bbox=tree.bbox(iid,colid)
2620:             if not bbox: return
2621:             close_editor(False)
2622:             x,y,w,h=bbox
2623:             val=str(tree.item(iid,"values")[idx] or "")
2624:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2625:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2626:             cell_editor["widget"]=e
2627:             def commit(_=None):
2628:                 try:
2629:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2630:                 finally:
2631:                     try:e.destroy()
2632:                     except Exception:pass
2633:                     cell_editor["widget"]=None
2634:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2635:             e.bind("<FocusOut>",commit)
2636: 
2637:         def rows_query():
2638:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2639:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2641:             if tc: where.append("code <= ?"); params.append(tc)
2642:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2643:             if df or dt:
2644:                 sub=[]; sp=[]
2645:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2646:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2647:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2648:                 params.extend(sp)
2649:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2650:             return sql,params
2651: 
2652:         def load():
2653:             close_editor(False)
2654:             for i in tree.get_children(): tree.delete(i)
2655:             sql,params=rows_query()
2656:             count=0
2657:             for r in self.conn.execute(sql,params):
2658:                 # V18 stores UOM/opening and the original application may have
2659:                 # rate/remarks columns in some versions. Read them safely.
2660:                 rid,code,desc,uom,opening,rate,remarks=r
2661:                 bal=stock(self.conn,code)
```
```text
2675:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2676:             editing["id"]=None; editing["new"]=True
2677:             # Put the user directly into the Code cell.
2678:             try:
2679:                 bbox=tree.bbox(iid,"#2")
2680:                 if bbox:
2681:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2682:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2683:                     def commit(_=None):
2684:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2685:                         try:e.destroy()
2686:                         except Exception:pass
2687:                         cell_editor["widget"]=None
2688:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2689:             except Exception: pass
2690:             status.set("New row added — enter values, then press Save")
2691: 
2692:         def selected_row():
2693:             a=tree.selection()
2694:             return a[0] if a else None
2695: 
```
```text
2695: 
2696:         def edit_record():
2697:             iid=selected_row()
2698:             if not iid:
2699:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2700:             if not self.can_edit and not self.is_admin:
2701:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2702:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2703:             status.set("Edit mode — double-click any cell to change it, then press Save")
2704:             tree.focus(iid); tree.see(iid)
2705: 
2706:         def save_record():
2707:             iid=selected_row()
2708:             if not iid:
2709:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2710:             if not self.can_edit and not self.is_admin:
2711:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2712:             close_editor(True)
2713:             vals=list(tree.item(iid,"values"))
2714:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2715:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2713:             vals=list(tree.item(iid,"values"))
2714:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2715:             try: opening=float(str(vals[4]).strip() or 0)
2716:             except Exception: raise ValueError("Opening Qty must be a number.")
2717:             try: rate=float(str(vals[5]).strip() or 0)
2718:             except Exception: raise ValueError("Rate must be a number.")
2719:             remarks=str(vals[6]).strip()
2720:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2721:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2722:             if not desc:
2723:                 messagebox.showerror("Save","Description is required."); return
2724:             if opening<0:
2725:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2726:             rid=vals[0]
2727:             try:
2728:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2729:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2730:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2731:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2732:                 if rid:
2733:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2736:                                       (code,desc,uom,opening,rid))
2737:                     if oldcode!=code:
2738:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2739:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2740:                             except Exception:pass
2741:                 else:
2742:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2743:                                       (code,desc,uom,"",opening,0,"Local",0))
2744:                 self.conn.commit()
2745:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2746:                 backup_database(); load()
2747:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2748:             except Exception as ex:
2749:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2750: 
2751:         def delete_record():
2752:             iid=selected_row()
2753:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2754:             if not self.can_delete and not self.is_admin:
2755:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2756:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2752:             iid=selected_row()
2753:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2754:             if not self.can_delete and not self.is_admin:
2755:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2756:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2757:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2758:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2759:             try:
2760:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2761:             except Exception as ex:
2762:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2763: 
2764:         def refresh(): load()
2765:         def do_print():
2766:             try:self.preview_tree("Inventory Codes",tree)
2767:             except Exception as ex:messagebox.showerror("Print",str(ex))
2768:         def do_close(): self.dashboard()
2769: 
2770:         btn("New",new_record,8)
2771:         btn("Edit",edit_record,8)
2772:         btn("Delete",delete_record,8)
```
```text
2765:         def do_print():
2766:             try:self.preview_tree("Inventory Codes",tree)
2767:             except Exception as ex:messagebox.showerror("Print",str(ex))
2768:         def do_close(): self.dashboard()
2769: 
2770:         btn("New",new_record,8)
2771:         btn("Edit",edit_record,8)
2772:         btn("Delete",delete_record,8)
2773:         btn("Save",save_record,8)
2774:         btn("Refresh",refresh,9)
2775:         btn("Preview",do_print,8)
2776:         btn("Print",do_print,8)
2777:         btn("Close",do_close,8)
2778: 
2779:         # Search is deliberately small and sits on the right, without changing
2780:         # the reference layout of the action buttons.
2781:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2782:         search=tk.StringVar()
2783:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2784:         se.pack(side="left",padx=2)
2785:         self._item_master_search_entry=se
```
```text
2793:                     tree.detach(iid)
2794:         search.trace_add("write",filter_grid)
2795:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2796: 
2797:         tree.bind("<Double-1>",edit_cell)
2798:         tree.bind("<F2>",lambda e: edit_record())
2799:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2800:         self._page_actions={
2801:             "save":save_record,"edit":edit_record,"delete":delete_record,
2802:             "cancel":do_close,"print":do_print,"preview":do_print
2803:         }
2804:         load()
2805: 
2806:     def open_mto_inventory_flow(self):
2807:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2808: 
2809:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2810:         Cancel/X only closes the popup.
2811:         """
2812:         criteria = self._ask_mto_inventory_filters()
2813:         if not criteria or criteria.get("cancelled"):
```
```text
2975:                 return False
2976:             destination.set(found_dest)
2977:             edit_mode.update(on=True, original=r[0], dest=found_dest)
2978:             code.set(r[0])
2979:             desc.set(r[1] or "")
2980:             uom.set(r[2] or UOM_OPTIONS[0])
2981:             opening.set(str(r[3] if r[3] is not None else 0))
2982:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
2983:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
2984:             err.set("")
2985:             edit_btn.configure(text="SAVE EDIT")
2986:             ce.focus_set()
2987:             return True
2988: 
2989:         def check_duplicates(*_):
2990:             c = code.get().strip()
2991:             d = desc.get().strip()
2992:             dest = destination.get()
2993:             msgs = []
2994:             r = row_for(dest, c) if len(norm(c)) == 8 else None
2995:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
2997:             dh = desc_hit(dest, d) if d else None
2998:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
2999:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
3000:             hint.set("\n".join(msgs))
3001: 
3002:         code.trace_add("write", check_duplicates)
3003:         desc.trace_add("write", check_duplicates)
3004: 
3005:         def save_code():
3006:             try:
3007:                 c = code.get().strip()
3008:                 d = desc.get().strip()
3009:                 u = uom.get().strip()
3010:                 dest = destination.get()
3011:                 digits = norm(c)
3012:                 if len(digits) != 8:
3013:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3014:                 if not d:
3015:                     raise ValueError("Description is required.")
3016:                 try:
3017:                     op = float(opening.get().strip() or 0)
```
```text
3038:                         (c, d, u, op, iso, old)
3039:                     )
3040:                     action = "updated"
3041:                 else:
3042:                     self.conn.execute(
3043:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3044:                         (c, d, u, "", op, 0, iso)
3045:                     )
3046:                     action = "saved"
3047:                 self.conn.commit()
3048:                 backup_database()
3049:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3050:                 # Keep popup open for fast multiple entries.
3051:                 clear_form(keep_search=False)
3052:                 ce.focus_set()
3053:             except Exception as ex:
3054:                 self.conn.rollback()
3055:                 err.set(str(ex))
3056:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3057: 
3058:         def edit_action():
```
```text
3054:                 self.conn.rollback()
3055:                 err.set(str(ex))
3056:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3057: 
3058:         def edit_action():
3059:             if not edit_mode["on"]:
3060:                 load_for_edit()
3061:             else:
3062:                 save_code()
3063: 
3064:         def delete_code():
3065:             if not edit_mode["on"]:
3066:                 if not load_for_edit():
3067:                     return
3068:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3069:                 return
3070:             try:
3071:                 t = table_for(edit_mode["dest"])
3072:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3073:                 self.conn.commit()
3074:                 backup_database()
```
```text
3070:             try:
3071:                 t = table_for(edit_mode["dest"])
3072:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3073:                 self.conn.commit()
3074:                 backup_database()
3075:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3076:                 clear_form(keep_search=False)
3077:             except Exception as ex:
3078:                 self.conn.rollback()
3079:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3080: 
3081:         btns = ttk.Frame(box)
3082:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3083:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3084:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3085:         edit_btn.pack(side="left", padx=4, ipadx=8)
3086:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3087:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3088:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3089:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3090:         ce.focus_set()
```
```text
3084:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3085:         edit_btn.pack(side="left", padx=4, ipadx=8)
3086:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3087:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3088:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3089:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3090:         ce.focus_set()
3091: 
3092:     def _mto_new_item_dialog(self, on_saved):
3093:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3094:         brand-new item can be created without leaving that screen. Writes
3095:         straight into the same Item Master (items table) used everywhere."""
3096:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3097:         win.transient(self); win.grab_set()
3098:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3099:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3100:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3101:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3102:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3103:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3104:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3100:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3101:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3102:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3103:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3104:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3105:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3106:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3107:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3108:         def save():
3109:             try:
3110:                 c=code.get().strip(); d=desc.get().strip()
3111:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3112:                 if not d: raise ValueError("Description is required.")
3113:                 try:
3114:                     opening_val=float(opening.get() or 0)
3115:                 except ValueError:
3116:                     raise ValueError("Opening Qty must be a number.")
3117:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3118:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3119:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3120:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3113:                 try:
3114:                     opening_val=float(opening.get() or 0)
3115:                 except ValueError:
3116:                     raise ValueError("Opening Qty must be a number.")
3117:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3118:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3119:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3120:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3121:                 self.conn.commit(); backup_database()
3122:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3123:                 win.grab_release(); win.destroy()
3124:                 on_saved()
3125:             except Exception as ex: messagebox.showerror("Error",str(ex))
3126:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3127:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3128:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3129: 
3130:     def _item_filter_bar(self, parent, on_change):
3131:         """Item Code entry + item-master picker + Search/Show All. Calls
3132:         on_change() whenever the code changes or a button is pressed."""
3133:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3219:         self._item_master_find_callback=None
3220:         self._portable_print_context=None
3221:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3222:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3223:         }
3224: 
3225:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3226:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3227:         self.conn.commit()
3228: 
3229:         # ---- Same professional in-app window layout as Inventory Codes ----
3230:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3231:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3232:                   foreground=COLORS["primary_dark"]).pack(side="left")
3233:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3234: 
3235:         def open_find():
3236:             state_find={"index":-1}
3237:             def search_fn(text):
3238:                 text=text.strip().lower()
3239:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3326:             for i in table.get_children(): table.delete(i)
3327:             where=["1=1"]; params=[]
3328:             prefix=state.get("prefix",""); q=search.get().strip()
3329:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3330:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3331:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3332:             if fc: where.append("code >= ?"); params.append(fc)
3333:             if tc: where.append("code <= ?"); params.append(tc)
3334:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3335:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3336:             records=[]
3337:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3338:                 # If a date filter is supplied, accept an opening-date match OR
3339:                 # a transaction in that date range. This prevents valid MTO codes
3340:                 # from disappearing merely because an older record has no opening_date.
3341:                 if df or dt:
3342:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3343:                     if not ok:
3344:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3345:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3346:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3416:                 tr.insert("", "end", values=r)
3417:         def clear():
3418:             for x in v.values(): x.set("")
3419:             try: tr.selection_remove(tr.selection())
3420:             except Exception: pass
3421:             self._set_form_editable(party_form_roots, False)
3422:         def new_form():
3423:             clear(); self._set_form_editable(party_form_roots, True)
3424:         def save():
3425:             try:
3426:                 name=v["name"].get().strip()
3427:                 if not name: raise ValueError("Party Name is required.")
3428:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3429:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3430:             except Exception as ex: messagebox.showerror("Error",str(ex))
3431:         def load_party_row(a):
3432:             if not a:return
3433:             r=tr.item(a[0])["values"]
3434:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3435:             self._set_form_editable(party_form_roots, False)
3436:         def on_party_select(_=None):
```
```text
3442:             load_party_row(a)
3443:             self._set_form_editable(party_form_roots, True)
3444:         def delete_party():
3445:             a=tr.selection()
3446:             if not a:
3447:                 messagebox.showwarning("Delete", "Select a party first."); return
3448:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3449:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3450:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3451:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3452:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3453:         self._add_transaction_new_button(new_form)
3454:         load(); clear()
3455: 
3456:     def user_management(self):
3457:         self.clearbody()
3458:         if not self.is_admin:
3459:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3460:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3461:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3462:         role=tk.StringVar(value="User")
```
```text
3499:             u_ent.state(["!disabled"])
3500:         def edit():
3501:             a=tr.selection()
3502:             if not a:
3503:                 messagebox.showwarning("Edit User","Select a user row first."); return
3504:             r=tr.item(a[0])["values"]
3505:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3506:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3507:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3508:         def save():
3509:             try:
3510:                 username=v["username"].get().strip()
3511:                 if not username: raise ValueError("Username is required.")
3512:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3513:                 pw=v["password"].get()
3514:                 if exists:
3515:                     pw_hash = hash_password(pw) if pw else exists[0]
3516:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3517:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3518:                 else:
3519:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3514:                 if exists:
3515:                     pw_hash = hash_password(pw) if pw else exists[0]
3516:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3517:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3518:                 else:
3519:                     if not pw: raise ValueError("Password is required for a new user.")
3520:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3521:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3522:                 self.conn.commit(); backup_database(); load(); clear()
3523:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3524:             except Exception as ex:
3525:                 messagebox.showerror("Error", str(ex))
3526:         def delete_user():
3527:             a=tr.selection()
3528:             if not a:
3529:                 messagebox.showwarning("Delete User","Select a user row first."); return
3530:             username=tr.item(a[0])["values"][0]
3531:             if username==self.current_user:
3532:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3533:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3534:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3529:                 messagebox.showwarning("Delete User","Select a user row first."); return
3530:             username=tr.item(a[0])["values"][0]
3531:             if username==self.current_user:
3532:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3533:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3534:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3535:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3536:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3537:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3538:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3539:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3540:         load()
3541: 
3542:     @staticmethod
3543:     def _renumber_tree(tree, rows):
3544:         for i,iid in enumerate(tree.get_children()):
3545:             vals=list(tree.item(iid,"values"));
3546:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3547: 
3548:     def demand(self):
3549:         self.clearbody(); self.demand_lines=[]
```
```text
3546:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3547: 
3548:     def demand(self):
3549:         self.clearbody(); self.demand_lines=[]
3550:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3551:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3552:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3553:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3554:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3555:         # Demand Date is intentionally displayed as its own dedicated field.
3556:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3557:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3558:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3559:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3560:                 ("special","Special Instructions"),("source","Recommended Source")]
3561:         for i,(k,n) in enumerate(fields):
3562:             r=i//4*2+3; c=i%4*2
3563:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3564:             if k=="dept":
3565:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3566:             elif k=="urgency":
```
```text
3636:         def new_form():
3637:             self._editing_document_key=None
3638:             for z in v.values(): z.set("")
3639:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3640:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3641:             for iid in tree.get_children(): tree.delete(iid)
3642:             self._set_form_editable(form_roots, True, skip=[selector])
3643: 
3644:         def save():
3645:             try:
3646:                 no=v["no"].get().strip()
3647:                 if not no: raise ValueError("Demand No is required.")
3648:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3649:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3650:                 if dup and getattr(self,"_editing_document_key",None) != no:
3651:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3652:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3653:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3654:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3655:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3656:                 self.conn.commit()
```
```text
3649:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3650:                 if dup and getattr(self,"_editing_document_key",None) != no:
3651:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3652:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3653:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3654:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3655:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3656:                 self.conn.commit()
3657:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3658:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3659:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3660:             except Exception as ex: messagebox.showerror("Error",str(ex))
3661:         form_roots=[f,line,editbar]
3662:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3663:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3664:         def delete_current():
3665:             no=v["no"].get().strip()
3666:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3667:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3668:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3669:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3682:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3683:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3684:                     f"Justification: {v['just'].get()}",
3685:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3686:             if not self.demand_lines:
3687:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3688:             self.show_preview_window("Purchase Demand", header,
3689:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3690:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3691:         def edit_saved_demand():
3692:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3693:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3694:             self._set_form_editable(form_roots, True, skip=[selector])
3695:         def print_now():
3696:             if not self.demand_lines:
3697:                 messagebox.showwarning("Print","Add at least one item line first."); return
3698:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3699:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3700:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3701:                     f"Justification: {v['just'].get()}",
3702:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3698:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3699:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3700:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3701:                     f"Justification: {v['just'].get()}",
3702:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3703:             self._open_direct_printer("Purchase Demand",header,
3704:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3705:                 self.demand_lines,A4)
3706:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3707:         self._add_transaction_new_button(new_form)
3708:         self._set_form_editable(form_roots, False, skip=[selector])
3709:         try:
3710:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3711:         except Exception: pass
3712:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3713: 
3714:     def load_demand_into_form(self,no,v,tree):
3715:         v["no"].set(no)
3716:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3717:         if not r:return
3718:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3720:         self.demand_lines=[]
3721:         for i in tree.get_children():tree.delete(i)
3722:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3723:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3724:         roots=getattr(self,"_transaction_form_roots",None)
3725:         if roots and "demand" in roots:
3726:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3727: 
3728:     def refresh_saved_cache(self,typ):
3729:         # Refresh saved-document dropdowns immediately after a successful save.
3730:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3731:         alive=[]
3732:         for combo, refresh in refreshers:
3733:             try:
3734:                 if combo.winfo_exists():
3735:                     refresh()
3736:                     alive.append((combo, refresh))
3737:             except Exception:
3738:                 pass
3739:         if hasattr(self, "_document_selector_refreshers"):
3740:             self._document_selector_refreshers[typ] = alive
```
```text
3739:         if hasattr(self, "_document_selector_refreshers"):
3740:             self._document_selector_refreshers[typ] = alive
3741: 
3742:     def grr(self):
3743:         self.clearbody(); self.grr_lines=[]
3744:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3745:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3746:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3747:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3748:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3749:         for i,(k,n) in enumerate(fields):
3750:             r=i//4*2+2;c=i%4*2
3751:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3752:             if k=="department":
3753:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3754:             elif k=="supplier":
3755:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3756:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3757:             elif k=="date":
3758:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3759:             else:
```
```text
3808:         def new_form():
3809:             self._editing_document_key=None
3810:             for z in v.values(): z.set("")
3811:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3812:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3813:             for iid in tree.get_children(): tree.delete(iid)
3814:             self._set_form_editable(form_roots, True, skip=[selector])
3815: 
3816:         def save():
3817:             try:
3818:                 no=v["no"].get().strip()
3819:                 if not no:raise ValueError("GRN No is required.")
3820:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3821:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3822:                 if dup and getattr(self,"_editing_document_key",None) != no:
3823:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3824:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3825:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3826:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3827:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3828:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3825:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3826:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3827:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3828:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3829:                 for x in self.grr_lines:
3830:                     ltype=x[10] if len(x)>10 else "Local"
3831:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3832:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3833:                 self.conn.commit()
3834:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
3835:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
3836:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3837:             except Exception as ex:messagebox.showerror("Error",str(ex))
3838:         form_roots=[f,line,editbar]
3839:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3840:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3841:         def delete_current():
3842:             no=v["no"].get().strip()
3843:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3844:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3845:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
3838:         form_roots=[f,line,editbar]
3839:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3840:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3841:         def delete_current():
3842:             no=v["no"].get().strip()
3843:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3844:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3845:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3846:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3847:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3848:         def cancel_form():
3849:             self._editing_document_key=None
3850:             self._set_form_editable(form_roots, False, skip=[selector])
3851:             for z in v.values(): z.set("")
3852:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3853:             itype.set("Local")
3854:             self.grr_lines.clear()
3855:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3856:             for iid in tree.get_children(): tree.delete(iid)
3857:         def preview_now():
3858:             if not self.grr_lines:
```
```text
3867:                     ("Challan #", v['challan'].get()),
3868:                     ("Vehicle #", v['vehicle'].get()),
3869:                     ("Bill/Voucher #", v['bill'].get()),
3870:                     ("Reference", v['ref'].get()),
3871:                     ("Remarks", v['remarks'].get()),
3872:                     ("Total Value", fmt_num(total))]
3873:             self.show_preview_window("GRN Receipt", header,
3874:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3875:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3876:         def portable_current():
3877:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3878:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3879:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3880:         self._portable_print_context=portable_current
3881:         def edit_saved_grr():
3882:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3883:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
3884:             self._set_form_editable(form_roots, True, skip=[selector])
3885:         def print_now():
3886:             if not self.grr_lines:
3887:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
3891:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
3892:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
3893:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
3894:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
3895:                     ("Total Value", fmt_num(total))]
3896:             self._open_direct_printer("GRN Receipt",header,
3897:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3898:                 self.grr_lines,landscape(A4))
3899:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3900:         self._add_transaction_new_button(new_form)
3901:         self._set_form_editable(form_roots, False, skip=[selector])
3902:         try:
3903:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3904:         except Exception: pass
3905:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
3906: 
3907:     def load_grr_into_form(self,no,v,tree):
3908:         v["no"].set(no)
3909:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
3910:         if not r:return
3911:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
3918:         if roots and "grr" in roots:
3919:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
3920: 
3921:     def issue(self):
3922:         self.clearbody(); self.issue_lines=[]
3923:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
3924:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
3925:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3926:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
3927:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
3928:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
3929:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3930:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3931:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
3932:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
3933:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
3934:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
3935:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
3936:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
3937:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
3938:         itype=tk.StringVar(value="Local")
```
```text
4007:                 # Editing an existing issue replaces its old stock transaction and detail lines.
4008:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
4009:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
4010:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
4011:                 for x in self.issue_lines:
4012:                     ltype=x[7] if len(x)>7 else "Local"
4013:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
4014:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
4015:                 self.conn.commit()
4016:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
4017:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
4018:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4019:             except Exception as ex:messagebox.showerror("Error",str(ex))
4020:         def delete_current():
4021:             no=v["no"].get().strip()
4022:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
4023:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
4024:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
4025:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
4026:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
4027:         def cancel_form():
```
```text
4035:             for iid in tree.get_children(): tree.delete(iid)
4036:         def preview_now():
4037:             if not self.issue_lines:
4038:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4039:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4040:                     f"Items Use For: {v['items_use_for'].get()}"]
4041:             self.show_preview_window("Material Issue", header,
4042:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4043:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4044:         def portable_current():
4045:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4046:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4047:         self._portable_print_context=portable_current
4048:         form_roots=[f,usebar,line,editbar]
4049:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4050:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4051:         def load_saved_issue(no):
4052:             self.load_issue_into_form(no,v,tree)
4053:             self._set_form_editable(form_roots, False, skip=[selector])
4054:         def edit_saved_issue():
4055:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4048:         form_roots=[f,usebar,line,editbar]
4049:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4050:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4051:         def load_saved_issue(no):
4052:             self.load_issue_into_form(no,v,tree)
4053:             self._set_form_editable(form_roots, False, skip=[selector])
4054:         def edit_saved_issue():
4055:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4056:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4057:             self._set_form_editable(form_roots, True, skip=[selector])
4058:         def print_issue_now():
4059:             if not self.issue_lines:
4060:                 messagebox.showwarning("Print","Add at least one item line first."); return
4061:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4062:             self._open_direct_printer("Material Issue",header,
4063:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4064:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4065:         self._add_transaction_new_button(new_form)
4066:         self._set_form_editable(form_roots, False, skip=[selector])
4067:         self._active_form_loader = load_saved_issue
4068: 
```
```text
4076:         for i in tree.get_children():tree.delete(i)
4077:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4078:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4079:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4080:         roots=getattr(self,"_transaction_form_roots",None)
4081:         if roots and "issue" in roots:
4082:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4083: 
4084:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4085:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4086: 
4087:         The layout intentionally matches Inventory Codes' Selection Criteria
4088:         popup so all Report sub-sections have one consistent desktop workflow.
4089:         """
4090:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4091:         win=tk.Toplevel(self)
4092:         win.title(f"{report_title} - Selection Criteria")
4093:         win.resizable(False,False)
4094:         win.transient(self); win.grab_set()
4095:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4096:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4141:             except Exception: pass
4142:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4143:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4144:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4145:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4146:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4147:         e1.focus_set(); self.wait_window(win); return result
4148: 
4149:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4150:         self._pending_report_filters=criteria
4151:         try:
4152:             return self.open_menu_window(method,title,geometry)
4153:         finally:
4154:             self._pending_report_filters=None
4155: 
4156:     def open_stock_balance_report_flow(self):
4157:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4158:         if f.get("cancelled"): return None
4159:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4160: 
4161:     def open_grr_report_flow(self):
```
```text
4154:             self._pending_report_filters=None
4155: 
4156:     def open_stock_balance_report_flow(self):
4157:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4158:         if f.get("cancelled"): return None
4159:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4160: 
4161:     def open_grr_report_flow(self):
4162:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4163:         if f.get("cancelled"): return None
4164:         return self._open_report_child(self.report_grr,"GRN Report",f)
4165: 
4166:     def open_demand_report_flow(self):
4167:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4168:         if f.get("cancelled"): return None
4169:         return self._open_report_child(self.report_demand,"Demand Report",f)
4170: 
4171:     def open_issue_report_flow(self):
4172:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4173:         if f.get("cancelled"): return None
4174:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4168:         if f.get("cancelled"): return None
4169:         return self._open_report_child(self.report_demand,"Demand Report",f)
4170: 
4171:     def open_issue_report_flow(self):
4172:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4173:         if f.get("cancelled"): return None
4174:         return self._open_report_child(self.report_issue,"Issue Report",f)
4175: 
4176:     def open_party_report_flow(self):
4177:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4178:         if f.get("cancelled"): return None
4179:         return self._open_report_child(self.report_party,"Party Report",f)
4180: 
4181:     def _ask_stock_balance_filters(self):
4182:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4183:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4184:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4185:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4186:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4187:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4188:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4200:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4201:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4202:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4203:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4204:         e1.focus_set();self.wait_window(win);return result
4205: 
4206:     def stock_balance(self):
4207:         self.clearbody()
4208:         # Stock Balance is a Report sub-section and does not use the generic
4209:         # Save/Edit/Delete/Cancel/Print action strip.
4210:         children=self.body.winfo_children()
4211:         if children:
4212:             children[0].destroy()
4213:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4214:         if initial.get("cancelled"):
4215:             self.dashboard(); return
4216:         top=ttk.Frame(self.body);top.pack(fill="x")
4217:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4218:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4219:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4220:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4230:             for typ,qty in self.conn.execute(q,params):
4231:                 if typ=="GRR":gr+=float(qty or 0)
4232:                 elif typ=="ISSUE":iss+=float(qty or 0)
4233:             return opening_before,gr,iss,opening_before+gr-iss
4234:         def header_summary():
4235:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4236:         def load():
4237:             for i in tr.get_children():tr.delete(i)
4238:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4239:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4240:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4241:             sql+=" ORDER BY code"
4242:             for r in self.conn.execute(sql,params):
4243:                 op,gr,iss,cur=period(r[0],r[3])
4244:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4245:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4246:         def reopen_filters():
4247:             initial2=self._ask_stock_balance_filters()
4248:             if initial2.get("cancelled"):return
4249:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4250:             load()
```
```text
4288:         """
4289:         if typ=="demand": self.demand()
4290:         elif typ=="grr": self.grr()
4291:         else: self.issue()
4292:         loader=getattr(self,"_active_form_loader",None)
4293:         if loader: loader(str(no))
4294: 
4295:     def _edit_from_selector(self, typ, var, loader):
4296:         """Top Edit action: load the saved document directly into the current form.
4297:         If nothing is selected, use the newest saved document; never open a popup.
4298:         """
4299:         text=var.get().strip()
4300:         if text:
4301:             no=text.split(" -> ",1)[0].strip()
4302:         else:
4303:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4304:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4305:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4306:             if not r:
4307:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4308:                 return
```
```text
4305:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4306:             if not r:
4307:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4308:                 return
4309:             no=str(r[0])
4310:             var.set(no)
4311:         loader(no)
4312: 
4313:     def show_saved_records(self,typ):
4314:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4315:         if typ=="demand":
4316:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4317:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4318:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4319:             for r in rows:
4320:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4321:                 r=list(r); r[1]=to_display_date(r[1])
4322:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4323:         elif typ=="grr":
4324:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4325:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4336:         def view():
4337:             a=tr.selection()
4338:             if not a:return
4339:             no=tr.item(a[0])["values"][0]
4340:             win.destroy();self.open_document_editor(typ,no)
4341:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4342:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4343:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4344:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4345: 
4346:     def documents(self):
4347:         self.clearbody()
4348:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4349:         specs=[
4350:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4351:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4352:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4353:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4354:             ("Material Issues","issue",("No","Date","Department"),
4355:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4356:         ]
```
```text
4352:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4353:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4354:             ("Material Issues","issue",("No","Date","Department"),
4355:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4356:         ]
4357:         for title,typ,cols,query in specs:
4358:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4359:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4360:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4361:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4362:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4363:             for r in self.conn.execute(query):
4364:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4365:             def edit_selected(t=tr,k=typ):
4366:                 a=t.selection()
4367:                 if not a:
4368:                     messagebox.showwarning("Edit", "Select a saved record first.")
4369:                     return
4370:                 no=t.item(a[0])["values"][0]
4371:                 self.open_document_editor(k,no)
4372:             def delete_selected(t=tr,k=typ):
```
```text
4367:                 if not a:
4368:                     messagebox.showwarning("Edit", "Select a saved record first.")
4369:                     return
4370:                 no=t.item(a[0])["values"][0]
4371:                 self.open_document_editor(k,no)
4372:             def delete_selected(t=tr,k=typ):
4373:                 a=t.selection()
4374:                 if not a:
4375:                     messagebox.showwarning("Delete", "Select a saved record first.")
4376:                     return
4377:                 no=t.item(a[0])["values"][0]
4378:                 if k=="demand":
4379:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4380:                 elif k=="grr":
4381:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4382:                 else:
4383:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4384:                 self.conn.commit();backup_database();self.documents()
4385:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4386:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4387:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4381:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4382:                 else:
4383:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4384:                 self.conn.commit();backup_database();self.documents()
4385:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4386:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4387:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4388:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4389:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4390:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4391:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4392: 
4393:     def doc_export_selected(self,typ,tr,fmt):
4394:         a=tr.selection()
4395:         if not a:
4396:             messagebox.showwarning("Export","Select a saved record first."); return
4397:         no=tr.item(a[0])["values"][0]
4398:         if fmt=="word": self.export_word(typ,no)
4399:         else: self.export_excel(typ,no)
4400: 
4401:     def doc_preview_selected(self,typ,tr):
```
```text
4396:             messagebox.showwarning("Export","Select a saved record first."); return
4397:         no=tr.item(a[0])["values"][0]
4398:         if fmt=="word": self.export_word(typ,no)
4399:         else: self.export_excel(typ,no)
4400: 
4401:     def doc_preview_selected(self,typ,tr):
4402:         a=tr.selection()
4403:         if not a:
4404:             messagebox.showwarning("Preview","Select a saved record first."); return
4405:         no=tr.item(a[0])["values"][0]
4406:         data=self._get_doc_data(typ,no)
4407:         if not data:
4408:             messagebox.showwarning("Preview","Document not found."); return
4409:         title,header,cols,rows=data
4410:         header_lines=header
4411:         self.show_preview_window(title,header_lines,cols,rows)
4412: 
4413:     def doc_print_selected(self,typ,tr):
4414:         a=tr.selection()
4415:         if not a: return
4416:         no=tr.item(a[0])["values"][0]
```
```text
4447:         def _print_loaded_document():
4448:             data=self._get_doc_data(typ,no)
4449:             if not data:
4450:                 messagebox.showwarning("Document","Document not found."); return
4451:             title,header,cols,rows=data
4452:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4453:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4454: 
4455:     def _report_filter_popup(self, title, include_party=False):
4456:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4457:         win,winbody=self._internal_window(title,"520x420")
4458:         done=tk.BooleanVar(value=False)
4459:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4460:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4461:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4462:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4463:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4464:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4465:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4466:         if include_party:
4467:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4461:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4462:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4463:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4464:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4465:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4466:         if include_party:
4467:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4468:         def ok():
4469:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4470:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4471:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4472:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4473: 
4474:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4475:         self.clearbody()
4476:         # Report sub-sections use their own report toolbar; remove only the
4477:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4478:         children=self.body.winfo_children()
4479:         if children:
4480:             children[0].destroy()
4481:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4482:         if f.get("cancelled"):
4483:             self.dashboard();return
4484:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4485:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4486:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4487:         def load():
4488:             for i in tr.get_children():tr.delete(i)
4489:             params,where=params_builder(f)
4490:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4491:             for r in self.conn.execute(sql,params):
4492:                 vals=list(r)
4493:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4494:                 tr.insert("","end",values=vals)
4495:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4496:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4497:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4498:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4499:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4500:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4501:         def open_find_report():
4502:             state_find={"index":-1}
```
```text
4508:                 order=children[start:]+children[:start]
4509:                 for iid in order:
4510:                     vals=tr.item(iid,"values")
4511:                     if any(text in str(v).lower() for v in vals):
4512:                         state_find["index"]=children.index(iid)
4513:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4514:                 return False
4515:             self._open_exact_find_text_popup(search_fn)
4516:         self._item_master_find_callback=open_find_report
4517:         load()
4518:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4519: 
4520:     def report_grr(self):
4521:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4522:         def pb(f):
4523:             w=[];p=[]
4524:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4525:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4526:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4527:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4528:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4523:             w=[];p=[]
4524:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4525:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4526:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4527:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4528:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4529:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4530:             return p,w
4531:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4532: 
4533:     def report_demand(self):
4534:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4535:         def pb(f):
4536:             w=[];p=[]
4537:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4538:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4539:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4540:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4541:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4542:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4543:             return p,w
```
```text
4536:             w=[];p=[]
4537:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4538:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4539:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4540:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4541:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4542:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4543:             return p,w
4544:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4545: 
4546:     def report_issue(self):
4547:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4548:         def pb(f):
4549:             w=[];p=[]
4550:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4551:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4552:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4553:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4554:             return p,w
4555:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4556: 
```
```text
4549:             w=[];p=[]
4550:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4551:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4552:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4553:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4554:             return p,w
4555:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4556: 
4557:     def report_party(self):
4558:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4559:         def pb(f):
4560:             w=[];p=[]
4561:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4562:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4563:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4564:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4565:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4566:             return p,w
4567:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4568: 
4569:     def reports(self):
```
```text
4567:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4568: 
4569:     def reports(self):
4570:         self.clearbody()
4571:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4572: 
4573:         # ================= GRN Details =================
4574:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4575:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4576:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4577:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4578:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4579:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4580: 
4581:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4582:         def load_grr_item(codev=None):
4583:             for i in tr.get_children(): tr.delete(i)
4584:             q=codev.get().strip() if codev else ""
4585:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4586:             for r in self.conn.execute(sql,(q,) if q else ()):
4587:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4593:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4594:         tr=self.make_tree(fr,grr_cols,grr_widths)
4595:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4596:             for i in tr.get_children(): tr.delete(i)
4597:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4598:             conds=[];params=[]
4599:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4600:             if td: conds.append("g.grr_date<=?");params.append(td)
4601:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4602:             for r in self.conn.execute(sql,params):
4603:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4604:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4605:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4606:         load_grr_date(fdv,tdv)
4607: 
4608:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4609:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4610:         party=tk.StringVar(value="ALL")
4611:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4612:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4613:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4609:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4610:         party=tk.StringVar(value="ALL")
4611:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4612:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4613:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4614:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4615:         def load_party(*_):
4616:             for i in tr.get_children(): tr.delete(i)
4617:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4618:             if party.get()=="ALL":
4619:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4620:             else:
4621:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4622:             for r in rows:
4623:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4624:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4625:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4626: 
4627:         # ================= Demand Details =================
4628:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4629:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4625:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4626: 
4627:         # ================= Demand Details =================
4628:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4629:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4630:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4631:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4632:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4633:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4634: 
4635:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4636:         def load_dem_item(codev=None):
4637:             for i in tr.get_children(): tr.delete(i)
4638:             q=codev.get().strip() if codev else ""
4639:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4640:             for r in self.conn.execute(sql,(q,) if q else ()):
4641:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4642:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4643:         tr=self.make_tree(fr,dem_cols,dem_widths)
4644:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4645:         load_dem_item(codev)
```
```text
4647:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4648:         tr=self.make_tree(fr,dem_cols,dem_widths)
4649:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4650:             for i in tr.get_children(): tr.delete(i)
4651:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4652:             conds=[];params=[]
4653:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4654:             if td: conds.append("d.demand_date<=?");params.append(td)
4655:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4656:             for r in self.conn.execute(sql,params):
4657:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4658:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4659:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4660:         load_dem_date(fdv,tdv)
4661: 
4662:         # ================= Material Issue Details =================
4663:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4664:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4665:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4666:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4667:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4660:         load_dem_date(fdv,tdv)
4661: 
4662:         # ================= Material Issue Details =================
4663:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4664:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4665:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4666:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4667:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4668:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4669: 
4670:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4671:         def load_iss_item(codev=None):
4672:             for i in tr.get_children(): tr.delete(i)
4673:             q=codev.get().strip() if codev else ""
4674:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4675:             for r in self.conn.execute(sql,(q,) if q else ()):
4676:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4677:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4678:         tr=self.make_tree(fr,iss_cols,iss_widths)
4679:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4680:         load_iss_item(codev)
```
```text
4682:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4683:         tr=self.make_tree(fr,iss_cols,iss_widths)
4684:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4685:             for i in tr.get_children(): tr.delete(i)
4686:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4687:             conds=[];params=[]
4688:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4689:             if td: conds.append("i.issue_date<=?");params.append(td)
4690:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4691:             for r in self.conn.execute(sql,params):
4692:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4693:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4694:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4695:         load_iss_date(fdv,tdv)
4696: 
4697:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4698: 
4699:     def print_item_master(self):
4700:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4701:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4702: 
```
```text
4699:     def print_item_master(self):
4700:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4701:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4702: 
4703:     def print_party_master(self):
4704:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4705:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4706: 
4707:     def print_report(self,kind):
4708:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4709:         if kind=="grr":
4710:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4711:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4712:         elif kind=="demand":
4713:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4714:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4715:         elif kind=="issue":
4716:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4717:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4718:         else:
4719:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4720:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4721:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4722: 
4723:     def print_stock(self):
4724:         rows=[]
4725:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4726:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4727:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4728:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4729: 
4730:     def print_ledger(self):
4731:         rows=[]
4732:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4733:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4734:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4735:                 running += x[3] if x[1]=="GRR" else -x[3]
4736:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4737:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4738: 
4739:     def _get_doc_data(self, typ, no):
4740:         """Header + line items for one saved document, used by the on-screen
```
```text
4806:             sig=doc.add_table(rows=2,cols=3)
4807:             labels=["Prepared By","Store Keeper","Store Incharge"]
4808:             for i,label in enumerate(labels):
4809:                 sig.cell(0,i).text="____________________"
4810:                 sig.cell(1,i).text=label
4811:                 for para in sig.cell(1,i).paragraphs:
4812:                     for run in para.runs: run.bold=True
4813:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4814:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4815:         doc.save(path)
4816:         self.open_file(path)
4817: 
4818:     def export_excel(self, typ, no):
4819:         if not no or not no.strip():
4820:             return messagebox.showwarning("Excel Export","Select a document first.")
4821:         if not XLSX_AVAILABLE:
4822:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4823:         data=self._get_doc_data(typ,no)
4824:         if not data:
4825:             return messagebox.showwarning("Excel Export","Document not found.")
4826:         title,header,cols,rows=data
```
```text
4848:             for col in range(1,4):
4849:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4850:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4851:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4852:         for col_cells in ws.columns:
4853:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4854:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4855:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4856:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4857:         wb.save(path)
4858:         self.open_file(path)
4859: 
4860:     def preview_pdf(self,typ,no):
4861:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4862:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4863:         data=self._get_doc_data(typ,no)
4864:         if not data:return messagebox.showwarning("Document","Document not found.")
4865:         title,header,cols,rows=data
4866:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4867:         page_size = landscape(A4) if typ == "grr" else A4
4868:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4863:         data=self._get_doc_data(typ,no)
4864:         if not data:return messagebox.showwarning("Document","Document not found.")
4865:         title,header,cols,rows=data
4866:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4867:         page_size = landscape(A4) if typ == "grr" else A4
4868:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4869: 
4870:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4871:         """Open the print dialog with a real visual preview of the exact report.
4872: 
4873:         The report is rendered to a temporary PDF only in memory/on disk for the
4874:         duration of printing.  It is deleted after the print dialog closes, so
4875:         the Print button does not leave a PDF report behind.  Printing uses the
4876:         rendered report page itself rather than rebuilding rows as plain text;
4877:         this keeps the printed page identical to the application's report.
4878:         """
4879:         # Printing is always prepared as an A4 landscape page. This only affects
4880:         # the print path; the rest of the application's UI/report logic is unchanged.
4881:         page_size = landscape(A4)
4882:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
4883:             messagebox.showwarning(
```
```text
4885:                 "The print preview/printing components are not available.\n\n"
4886:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
4887:             )
4888:             return
4889:         if not rows and not columns:
4890:             messagebox.showwarning("Print", "There is no data to print.")
4891:             return
4892:         try:
4893:             os.makedirs(REPORTS_DIR, exist_ok=True)
4894:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
4895:             self._pdf_table_report(key,title,columns,rows,page_size,
4896:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
4897:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
4898:             self._select_windows_printer_for_pdf(key)
4899:         except Exception as e:
4900:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
4901: 
4902:     def _select_windows_printer_for_pdf(self, path):
4903:         """Print dialog with an actual page preview, printer selection and direct GDI output.
4904: 
4905:         The preview is rendered from the exact PDF produced by the application,
```
```text
4935:         job=getattr(self, "_print_jobs", {}).get(path)
4936:         if job:
4937:             title, header_lines, columns, rows, source_page_size = job
4938:         else:
4939:             title=os.path.splitext(os.path.basename(path))[0]
4940:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
4941: 
4942:         try:
4943:             doc=fitz.open(path)
4944:             total_pages=max(1,doc.page_count)
4945:         except Exception as e:
4946:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
4947:             return
4948: 
4949:         win=tk.Toplevel(self)
4950:         win.title("Printing from Win32 application - Print")
4951:         win.geometry("900x620")
4952:         win.minsize(850,580)
4953:         win.transient(self)
4954:         win.configure(bg="#f0f0f0")
4955: 
```
```text
4961:             pass
4962: 
4963:         outer=tk.Frame(win,bg="#f0f0f0")
4964:         outer.pack(fill="both",expand=True)
4965:         outer.columnconfigure(1,weight=1)
4966:         outer.rowconfigure(0,weight=1)
4967: 
4968:         # Left side mirrors the familiar system printer dialog: printers and
4969:         # print options. Right side contains the actual report page preview.
4970:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
4971:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
4972:         left.grid_propagate(False)
4973:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
4974:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
4975:         printer_list.pack(fill="x")
4976:         for pr in printers: printer_list.insert("end",pr)
4977:         try: printer_list.selection_set(printers.index(default_printer))
4978:         except Exception: printer_list.selection_set(0)
4979: 
4980:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
4981:         copies=tk.IntVar(value=1)
```
```text
5054:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5055: 
5056:         bottom=tk.Frame(win,bg="#f0f0f0")
5057:         # `outer` already uses pack() in `win`; using grid() for another direct
5058:         # child of the same toplevel raises TclError. Keep the action bar in the
5059:         # same geometry-manager family so Print/Cancel are always visible.
5060:         bottom.pack(fill="x",padx=12,pady=(0,12))
5061:         bottom.columnconfigure(0,weight=1)
5062:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5063:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5064:         print_btn=ttk.Button(bottom,text="Print",width=12)
5065:         print_btn.grid(row=0,column=2,padx=(8,0))
5066: 
5067:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5068: 
5069:         def parse_page_selection(total):
5070:             if pages_mode.get()=="All pages": return list(range(total))
5071:             raw=page_range.get().strip()
5072:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5073:             selected=[]
5074:             for part in raw.split(","):
```
```text
5071:             raw=page_range.get().strip()
5072:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5073:             selected=[]
5074:             for part in raw.split(","):
5075:                 part=part.strip()
5076:                 if "-" in part:
5077:                     a,b=part.split("-",1); a=int(a); b=int(b)
5078:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5079:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5080:                     selected.extend(range(a-1,b))
5081:                 else:
5082:                     n=int(part)
5083:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5084:                     selected.append(n-1)
5085:             return list(dict.fromkeys(selected))
5086: 
5087:         def selected_printer():
5088:             sel=printer_list.curselection()
5089:             return printer_list.get(sel[0]) if sel else printers[0]
5090: 
5091:         def print_rendered_pages():
```
```text
5184:                 finally:
5185:                     if hprinter is not None:
5186:                         try: win32print.ClosePrinter(hprinter)
5187:                         except Exception: pass
5188:                     if hdc:
5189:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5190:                         except Exception: pass
5191: 
5192:                 # Print the exact rendered PDF page through the printer DC.
5193:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5194:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5195:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5196:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5197: 
5198:                 for copy_no in range(count):
5199:                     dc.StartDoc(str(title)[:80])
5200:                     doc_ok=False
5201:                     try:
5202:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5203:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5204:                             dc.StartPage()
```
```text
5203:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5204:                             dc.StartPage()
5205:                             page_ok=False
5206:                             try:
5207:                                 cell_w=printable_w/float(cols_n)
5208:                                 cell_h=printable_h/float(rows_n)
5209:                                 for j,page_index in enumerate(batch):
5210:                                     page=doc.load_page(page_index)
5211:                                     pdf_w=max(1.0,float(page.rect.width))
5212:                                     pdf_h=max(1.0,float(page.rect.height))
5213:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5214:                                     fit=max(0.25,min(fit,8.0))
5215:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5216:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5217:                                     target_w=max(1,int(cell_w*0.96))
5218:                                     target_h=max(1,int(cell_h*0.96))
5219:                                     ratio=min(target_w/img.width,target_h/img.height)
5220:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5221:                                     if (nw,nh)!=(img.width,img.height):
5222:                                         img=img.resize((nw,nh),Image.LANCZOS)
5223:                                     dib=ImageWin.Dib(img)
```
```text
5243: 
5244:                 status.set("Print job sent successfully")
5245:                 win.update_idletasks()
5246:                 win.after(500,close)
5247:             except Exception as e:
5248:                 status.set("Print failed: "+str(e))
5249:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5250: 
5251:         def close():
5252:             try: doc.close()
5253:             except Exception: pass
5254:             try: win.destroy()
5255:             except Exception: pass
5256:             # Only the temporary PDF created by the Print button is removed.
5257:             # Existing report PDFs passed through the legacy print path are preserved.
5258:             try:
5259:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5260:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5261:             except Exception: pass
5262: 
5263:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5259:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5260:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5261:             except Exception: pass
5262: 
5263:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5264:         bottom.winfo_children()[1].configure(command=close)
5265:         print_btn.configure(command=print_rendered_pages)
5266:         win.protocol("WM_DELETE_WINDOW",close)
5267:         win.bind("<Escape>",lambda e:close())
5268:         win.grab_set()
5269:         # Keep the requested printer defaults visibly selected; no manual
5270:         # adjustment is required before pressing Print.
5271:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5272:         win.after(120,lambda:render_preview(0))
5273:         win.focus_force()
5274: 
5275:     def print_pdf(self,path):
5276:         """Open a printer-selection window for a generated PDF."""
5277:         path=os.path.abspath(path)
5278:         if not os.path.exists(path):
5279:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5275:     def print_pdf(self,path):
5276:         """Open a printer-selection window for a generated PDF."""
5277:         path=os.path.abspath(path)
5278:         if not os.path.exists(path):
5279:             messagebox.showwarning("Print", "The report file could not be found.")
5280:             return
5281: 
5282:         if sys.platform.startswith("win"):
5283:             self._select_windows_printer_for_pdf(path)
5284:             return
5285: 
5286:         try:
5287:             subprocess.run(["lp", path], check=True)
5288:         except Exception as e:
5289:             messagebox.showwarning(
5290:                 "Print",
5291:                 "The operating system could not start printing.\n\n"
5292:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5293:             )
5294: 
5295:     def open_file(self,path):
```
```text
5290:                 "Print",
5291:                 "The operating system could not start printing.\n\n"
5292:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5293:             )
5294: 
5295:     def open_file(self,path):
5296:         try:
5297:             if sys.platform.startswith("win"): os.startfile(path)
5298:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5299:             else: subprocess.Popen(["xdg-open",path])
5300:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5301: 
5302:     def print_demand(self,no):
5303:         data=self._get_doc_data("demand",no)
5304:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5305:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5306:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5307:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5308: 
5309:     def print_grr(self,no):
5310:         data=self._get_doc_data("grr",no)
```
```text
5304:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5305:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5306:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5307:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5308: 
5309:     def print_grr(self,no):
5310:         data=self._get_doc_data("grr",no)
5311:         if not data:return messagebox.showwarning("Document","GRN not found.")
5312:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5313:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5314:         # GRN has a wide item table. Generate the PDF itself in landscape so
5315:         # the printer dialog and printer driver receive a landscape document
5316:         # instead of a portrait page with rotated/cropped content.
5317:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5318: 
5319:     def print_issue(self,no):
5320:         data=self._get_doc_data("issue",no)
5321:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5322:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5323:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5324:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
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
