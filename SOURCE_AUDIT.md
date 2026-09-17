# Store Inventory source audit

Generated from `D:\a\Store-Inventory-Management\Store-Inventory-Management\source` after CI patches.

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

- Lines: 5257
- Functions: resource_path(56-60), hash_password(123-128), verify_password(130-133), _copy_legacy_database_if_needed(135-152), _init_schema(155-243), connect(246-275), migrate_old_item_codes(277-291), seed_items(293-300), backup_database(302-331), restore_database(333-350), stock(352-357), fmt_num(359-361), to_iso_date(363-372), to_display_date(374-382), fiscal_year_key(384-395), fiscal_year_range(397-400), normalize_code(402-410), format_code(412-421), attach_code_mask(423-449), set_digits(426-431), key(432-442), paste(444-447), bind_add_to_list(451-472), on_enter(454-465), __init__(476-493), _check_for_updates(495-500), _setup_style(502-538), _shade(541-546), on_close(548-553), redo_network_setup(555-571), backup_now(573-580), restore_backup(582-600), _ctrl_f(602-614), _open_exact_find_text_popup(616-661), do_find(637-646), close(647-654), _global_enter(663-675), wipe(677-678), login(680-709), do_login(695-706), change_password(711-761), save_password(733-755), logout(763-768), home(770-789), _ensure_mdi_host(791-812), _internal_window(814-898), normal_place(830-836), restore(837-844), maximize(845-851), minimize(852-867), close(868-891), open_inventory_codes_detail_flow(900-918), open_inventory_codes_with_filters(920-934), open_inventory_codes_report_window(936-1162), tbtn(954-959), balance_as_of(1016-1026), build_nav(1028-1050), selected_prefix(1052-1061), load(1063-1095), page_move(1097-1098), page_first(1099-1099), page_last(1100-1104), on_nav(1108-1109), find_popup(1112-1131), search_fn(1114-1129), print_report(1134-1137), export_pdf(1139-1141), export_word(1142-1144), export_excel(1145-1147), open_menu_window(1164-1186), close_window(1174-1181), _manual_check_update(1188-1192), _show_current_version(1194-1198), build_menu_bar(1200-1247), open_calendar_picker(1249-1297), pick(1267-1269), redraw(1271-1283), nav(1285-1289), make_date_field(1299-1306), clearbody(1308-1334), run_action(1323-1328), _portable_print_current(1336-1347), portable_print_dialog(1349-1422), build_receipt(1376-1394), send(1395-1408), refresh_printers(1409-1415), preview_tree(1424-1436), set_page_actions(1438-1446), _add_transaction_new_button(1448-1465), _report_header(1467-1531), _report_footer(1533-1539), _grr_signature_block(1541-1557), _finish_page(1559-1560), _wrap_text_to_width(1562-1587), fits(1569-1569), _pdf_table_report(1589-1658), table_header(1611-1616), show_preview_window(1660-1733), _safe_report_name(1735-1738), print_preview_window(1740-1743), _fallback_pdf_export(1745-1778), esc(1749-1750), add(1753-1755), export_preview_pdf(1780-1809), export_preview_word(1811-1851), export_preview_excel(1853-1889), make_tree(1891-1900), pick_item(1902-1923), choose(1903-1922), ld(1910-1914), sel(1916-1920), bind_item_lookup(1925-1942), lookup(1927-1940), _set_form_editable(1945-1958), walk(1948-1957), document_selector(1960-1994), refresh(1965-1976), selected(1977-1982), dashboard(1996-2105), load_details(2078-2102), dashboard_details(2107-2111), item_history(2113-2133), _ask_item_master_filters(2135-2219), finish(2188-2200), items(2221-2459), hierarchy(2262-2271), selected_prefix(2317-2330), balance_as_of(2332-2339), load(2341-2379), set_page(2381-2382), select_node(2384-2405), open_find(2411-2430), search_fn(2413-2428), visible_rows(2435-2437), print_inventory(2438-2442), export_inventory_word(2443-2445), export_inventory_excel(2446-2448), portable_inventory(2453-2455), inventory_codes(2461-2743), btn(2497-2502), close_editor(2538-2548), edit_cell(2550-2576), commit(2568-2574), rows_query(2578-2591), load(2593-2608), new_record(2610-2631), commit(2624-2628), selected_row(2633-2635), edit_record(2637-2645), save_record(2647-2688), delete_record(2690-2701), refresh(2703-2703), do_print(2704-2706), do_close(2707-2707), filter_grid(2725-2732), open_mto_inventory_flow(2745-2768), open_code_opening_flow(2770-2778), code_opening(2780-2781), _open_code_opening_popup(2783-2784), _open_code_opening_detail(2786-3029), norm(2856-2857), table_for(2859-2860), row_for(2862-2867), search_any_destination(2869-2882), desc_hit(2884-2888), clear_form(2890-2903), load_for_edit(2905-2926), check_duplicates(2928-2939), save_code(2944-2995), edit_action(2997-3001), delete_code(3003-3018), _mto_new_item_dialog(3031-3067), save(3047-3064), _item_filter_bar(3069-3081), _date_filter_bar(3083-3091), _ask_mto_inventory_filters(3093-3138), finish(3123-3131), mto_inventory(3140-3340), open_find(3174-3193), search_fn(3176-3191), hierarchy(3212-3216), rebuild_nav(3218-3229), mto_balance(3253-3262), load(3264-3306), set_page(3308-3308), select_node(3309-3318), visible_rows(3323-3323), do_print(3324-3328), export_word(3329-3331), export_excel(3332-3334), party_master(3342-3393), load(3352-3355), clear(3356-3360), new_form(3361-3362), save(3363-3369), load_party_row(3370-3374), on_party_select(3375-3376), edit(3378-3382), delete_party(3383-3389), user_management(3395-3479), sync_role(3422-3427), load(3431-3434), clear(3435-3438), edit(3439-3446), save(3447-3464), delete_user(3465-3476), _renumber_tree(3482-3485), demand(3487-3648), _restore_demand_tree_columns(3530-3536), add(3539-3547), edit_item(3549-3561), delete_item(3563-3571), new_form(3575-3581), save(3583-3596), delete_current(3600-3606), cancel_form(3607-3615), preview_now(3616-3626), edit_saved_demand(3627-3630), print_now(3631-3641), load_demand_into_form(3650-3662), refresh_saved_cache(3664-3676), grr(3678-3838), add(3710-3718), edit_item(3720-3730), delete_item(3732-3740), new_form(3744-3750), save(3752-3770), delete_current(3774-3780), cancel_form(3781-3789), preview_now(3790-3808), portable_current(3809-3812), edit_saved_grr(3814-3817), print_now(3818-3831), load_grr_into_form(3840-3852), issue(3854-3997), old_issue_qty(3883-3886), update_balance(3887-3895), add(3897-3906), edit_item(3908-3919), new_form(3923-3929), post(3931-3949), delete_current(3950-3956), cancel_form(3957-3965), preview_now(3966-3973), portable_current(3974-3976), load_saved_issue(3981-3983), edit_saved_issue(3984-3987), print_issue_now(3988-3993), load_issue_into_form(3999-4012), _ask_report_criteria(4014-4077), finish(4063-4071), _open_report_child(4079-4084), open_stock_balance_report_flow(4086-4089), open_grr_report_flow(4091-4094), open_demand_report_flow(4096-4099), open_issue_report_flow(4101-4104), open_party_report_flow(4106-4109), _ask_stock_balance_filters(4111-4134), ok(4126-4127), cancel(4128-4128), stock_balance(4136-4199), period(4152-4163), header_summary(4164-4165), load(4166-4175), reopen_filters(4176-4180), open_find_stock(4184-4197), search_fn(4186-4196), ledger(4201-4213), open_document_editor(4215-4223), _edit_from_selector(4225-4241), show_saved_records(4243-4274), view(4266-4270), documents(4276-4321), edit_selected(4295-4301), delete_selected(4302-4314), doc_export_selected(4323-4329), doc_preview_selected(4331-4341), doc_print_selected(4343-4351), load_document(4353-4383), _print_loaded_document(4377-4382), _report_filter_popup(4385-4402), ok(4398-4399), cancel(4400-4400), _report_window(4404-4448), load(4417-4424), hdr(4425-4425), open_find_report(4431-4445), search_fn(4433-4444), report_grr(4450-4461), pb(4452-4460), report_demand(4463-4474), pb(4465-4473), report_issue(4476-4485), pb(4478-4484), report_party(4487-4497), pb(4489-4496), reports(4499-4627), load_grr_item(4512-4517), load_grr_date(4525-4533), load_party(4545-4553), load_dem_item(4566-4571), load_dem_date(4579-4587), load_iss_item(4601-4606), load_iss_date(4614-4622), print_item_master(4629-4631), print_party_master(4633-4635), print_report(4637-4651), print_stock(4653-4658), print_ledger(4660-4667), _get_doc_data(4669-4697), export_word(4699-4746), export_excel(4748-4788), preview_pdf(4790-4798), _open_direct_printer(4800-4830), _select_windows_printer_for_pdf(4832-5203), render_preview(4957-4976), on_resize(4978-4980), parse_page_selection(4999-5015), selected_printer(5017-5019), print_rendered_pages(5021-5179), close(5181-5191), print_pdf(5205-5223), open_file(5225-5230), print_demand(5232-5237), print_grr(5239-5247), print_issue(5249-5254)

### Relevant source locations

```text
0001: 
0002: import csv, sqlite3, os, sys, subprocess, webbrowser, shutil, zipfile, hashlib, secrets, calendar, textwrap, ctypes
0003: import updater
0004: from datetime import datetime
0005: import tkinter as tk
0006: from tkinter import ttk, messagebox
0007: 
0008: try:
0009:     import fitz  # PyMuPDF: render the exact report PDF for print preview/printing
0010:     FITZ_AVAILABLE=True
0011: except Exception:
0012:     FITZ_AVAILABLE=False
0013:     fitz=None
0014: 
```
```text
0014: 
0015: try:
0016:     from PIL import Image, ImageTk, ImageWin
0017:     PIL_AVAILABLE=True
0018: except Exception:
0019:     PIL_AVAILABLE=False
0020:     Image=ImageTk=ImageWin=None
0021: 
0022: from firebase_sync import FirebaseSync, OnlineConnection
0023: 
0024: try:
0025:     from reportlab.lib.pagesizes import A4, landscape
0026:     from reportlab.pdfgen import canvas
0027:     from reportlab.pdfbase.pdfmetrics import stringWidth
0028:     REPORTLAB=True
0029: except Exception:
0030:     REPORTLAB=False
0031: 
0032: try:
0033:     from docx import Document
0034:     DOCX_AVAILABLE=True
```
```text
0062: # ---------------------------------------------------------------------------
0063: # MULTI-COMPUTER SHARED DATA
0064: #
0065: # One computer is the "Main" computer: its Data folder is what everyone
0066: # actually reads and writes to. Every other computer is a "Connected"
0067: # computer: it does NOT keep its own copy of the data, it points straight
0068: # at the Main computer's shared Data folder over the network
0069: # (e.g. \\MAIN-PC\StoreInventoryData). That way every laptop always shows
0070: # the exact same, live data - there is only ever one real database file.
0071: #
0072: # This choice is made once, the first time the program runs on a computer,
0073: # and remembered in CONFIG_FILE from then on.
0074: # ---------------------------------------------------------------------------
0075: if os.name == "nt":
0076:     INSTALL_DIR = r"C:\StoreInventoryManagement"
0077: else:
0078:     INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))  # dev/testing only
0079: 
0080: os.makedirs(INSTALL_DIR, exist_ok=True)
0081: # ONLINE DATABASE CONFIGURATION
0082: # Only a Firebase Realtime Database URL is required. No Firebase API key is
```
```text
0077: else:
0078:     INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))  # dev/testing only
0079: 
0080: os.makedirs(INSTALL_DIR, exist_ok=True)
0081: # ONLINE DATABASE CONFIGURATION
0082: # Only a Firebase Realtime Database URL is required. No Firebase API key is
0083: # used by this desktop app. The file is intentionally separate from the UI so
0084: # the existing interface remains unchanged.
0085: FIREBASE_URL_FILE = os.path.join(INSTALL_DIR, "firebase_database_url.txt")
0086: BACKUP_DIR = os.path.join(INSTALL_DIR, "Backups")   # local safety backups
0087: REPORTS_DIR = os.path.join(INSTALL_DIR, "Reports")  # local reports
0088: os.makedirs(BACKUP_DIR, exist_ok=True)
0089: os.makedirs(REPORTS_DIR, exist_ok=True)
0090: 
0091: # Keep the old local Data folder name for backwards compatibility and for the
0092: # existing Home-screen Data label. The actual shared source of truth is now
0093: # Firebase; this local SQLite file is the app's private cache.
0094: DATA_DIR = os.path.join(INSTALL_DIR, "Data")
0095: os.makedirs(DATA_DIR, exist_ok=True)
0096: BASE=REPORTS_DIR
0097: DB=os.path.join(DATA_DIR,"store_inventory.db")
```
```text
0093: # Firebase; this local SQLite file is the app's private cache.
0094: DATA_DIR = os.path.join(INSTALL_DIR, "Data")
0095: os.makedirs(DATA_DIR, exist_ok=True)
0096: BASE=REPORTS_DIR
0097: DB=os.path.join(DATA_DIR,"store_inventory.db")
0098: SEED=resource_path("inventory_seed.csv")
0099: COMPANY="Hunza Citrus and Pulp (Private) Limited"
0100: LOGO_FILE=resource_path("company_logo.png")
0101: REPORT_FOOTER="Generated by Store Inventory Management"
0102: DEPARTMENTS=["Administration","Production","Mechanical","Electrical","Finance"]
0103: # Standard Unit-of-Measure choices offered on Inventory Codes / Item Master.
0104: # Shown as a dropdown but left editable, so an uncommon unit can still be typed.
0105: UOM_OPTIONS=["NOS","FT","LTR","PKT","KG","MTR","PCS","SET","BOX","BAG","ROLL","GM","TON","DZN"]
0106: 
0107: # ---------------------------------------------------------------------------
0108: # PROFESSIONAL COLOR PALETTE (used to theme the whole application)
0109: # ---------------------------------------------------------------------------
0110: COLORS={
0111:     "primary":      "#1565C0",   # main brand blue
0112:     "primary_dark": "#0D47A1",   # header bar / hover
0113:     "accent":       "#00897B",   # teal accent
```
```text
0106: 
0107: # ---------------------------------------------------------------------------
0108: # PROFESSIONAL COLOR PALETTE (used to theme the whole application)
0109: # ---------------------------------------------------------------------------
0110: COLORS={
0111:     "primary":      "#1565C0",   # main brand blue
0112:     "primary_dark": "#0D47A1",   # header bar / hover
0113:     "accent":       "#00897B",   # teal accent
0114:     "success":      "#2E7D32",   # save / positive actions
0115:     "warning":      "#EF6C00",   # edit / caution actions
0116:     "danger":       "#C62828",   # delete / logout actions
0117:     "muted":        "#607D8B",   # secondary / cancel actions
0118:     "bg":           "#EEF2F7",   # app background
0119:     "card_bg":      "#FFFFFF",   # cards / trees
0120:     "text_dark":    "#1B2430",
0121: }
0122: 
0123: def hash_password(password, salt=None):
0124:     """Simple salted SHA-256 hash, stored as 'salt$hash'. Not for internet-
0125:     facing use, but a reasonable step up from plaintext for a LAN app."""
0126:     salt = salt or secrets.token_hex(8)
```
```text
0127:     h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
0128:     return f"{salt}${h}"
0129: 
0130: def verify_password(password, stored):
0131:     if not stored or "$" not in stored: return False
0132:     salt, _ = stored.split("$", 1)
0133:     return hash_password(password, salt) == stored
0134: 
0135: def _copy_legacy_database_if_needed():
0136:     """Migrate the previous LAN/shared SQLite database into this PC's local
0137:     cache once. This preserves existing records when upgrading the old build."""
0138:     if os.path.exists(DB):
0139:         return
0140:     legacy_cfg = os.path.join(INSTALL_DIR, "network_config.txt")
0141:     if not os.path.exists(legacy_cfg):
0142:         return
0143:     try:
0144:         with open(legacy_cfg, encoding="utf-8") as f:
0145:             legacy_dir = f.read().strip()
0146:         if not legacy_dir:
0147:             return
```
```text
0235:     demand_lines_cols={r[1] for r in c.execute("PRAGMA table_info(demand_lines)").fetchall()}
0236:     if "item_type" not in demand_lines_cols: c.execute("ALTER TABLE demand_lines ADD COLUMN item_type TEXT DEFAULT 'Local'")
0237:     grr_lines_cols={r[1] for r in c.execute("PRAGMA table_info(grr_lines)").fetchall()}
0238:     if "item_type" not in grr_lines_cols: c.execute("ALTER TABLE grr_lines ADD COLUMN item_type TEXT DEFAULT 'Local'")
0239:     issue_lines_cols={r[1] for r in c.execute("PRAGMA table_info(issue_lines)").fetchall()}
0240:     if "item_type" not in issue_lines_cols: c.execute("ALTER TABLE issue_lines ADD COLUMN item_type TEXT DEFAULT 'Local'")
0241:     txn_cols={r[1] for r in c.execute("PRAGMA table_info(transactions)").fetchall()}
0242:     if "item_type" not in txn_cols: c.execute("ALTER TABLE transactions ADD COLUMN item_type TEXT DEFAULT 'Local'")
0243:     c.commit()
0244: 
0245: 
0246: def connect():
0247:     _copy_legacy_database_if_needed()
0248:     raw = sqlite3.connect(DB, timeout=20)
0249:     _init_schema(raw)
0250:     seed_items(raw)
0251:     migrate_old_item_codes(raw)
0252:     try:
0253:         durable_local.restore_if_newer(raw)
0254:     except Exception:
0255:         pass
```
```text
0249:     _init_schema(raw)
0250:     seed_items(raw)
0251:     migrate_old_item_codes(raw)
0252:     try:
0253:         durable_local.restore_if_newer(raw)
0254:     except Exception:
0255:         pass
0256: 
0257:     sync = FirebaseSync(FIREBASE_URL_FILE, INSTALL_DIR)
0258:     if sync.enabled:
0259:         try:
0260:             sync.initialize(raw)
0261:             # Firebase may contain an older snapshot whose items table does not
0262:             # yet have the MTO columns. Re-run the local schema migration after
0263:             # the remote snapshot is restored so Code Opening can always create
0264:             # and display MTO records.
0265:             _init_schema(raw)
0266:         except Exception as exc:
0267:             # Keep the application usable with its local cache when the
0268:             # internet/Firebase is temporarily unavailable. The next write or
0269:             # restart will retry sync.
```
```text
0264:             # and display MTO records.
0265:             _init_schema(raw)
0266:         except Exception as exc:
0267:             # Keep the application usable with its local cache when the
0268:             # internet/Firebase is temporarily unavailable. The next write or
0269:             # restart will retry sync.
0270:             sync.pending_error = str(exc)
0271:     try:
0272:         durable_local.save(raw)
0273:     except Exception:
0274:         pass
0275:     return OnlineConnection(DB, sync)
0276: 
0277: def migrate_old_item_codes(c):
0278:     """Migrate old 00-00-00-0000 item codes to 00-00-0000 everywhere."""
0279:     rows=c.execute("SELECT code FROM items").fetchall()
0280:     for (old,) in rows:
0281:         digits="".join(ch for ch in str(old) if ch.isdigit())
0282:         if len(digits)!=10: continue
0283:         new=format_code(digits)
0284:         if not new or new==old: continue
```
```text
0283:         new=format_code(digits)
0284:         if not new or new==old: continue
0285:         if c.execute("SELECT 1 FROM items WHERE code=?",(new,)).fetchone():
0286:             # Do not destroy an existing code; leave this collision visible for manual resolution.
0287:             continue
0288:         c.execute("UPDATE items SET code=? WHERE code=?",(new,old))
0289:         for table,col in (("demand_lines","code"),("grr_lines","code"),("issue_lines","code"),("transactions","code")):
0290:             c.execute(f"UPDATE {table} SET {col}=? WHERE {col}=?",(new,old))
0291:     c.commit()
0292: 
0293: def seed_items(c):
0294:     if c.execute("SELECT COUNT(*) FROM items").fetchone()[0]: return
0295:     if not os.path.exists(SEED): return
0296:     with open(SEED,encoding="utf-8-sig") as f:
0297:         for r in csv.DictReader(f):
0298:             c.execute("INSERT OR IGNORE INTO items(code,description,uom) VALUES(?,?,?)",
0299:                       (format_code(r.get("code","").strip()),r.get("description","").strip(),r.get("uom","").strip()))
0300:     c.commit()
0301: 
0302: def backup_database(manual=False):
0303:     """Create a safe, restorable full backup (a .db snapshot + a .zip copy)
```
```text
0296:     with open(SEED,encoding="utf-8-sig") as f:
0297:         for r in csv.DictReader(f):
0298:             c.execute("INSERT OR IGNORE INTO items(code,description,uom) VALUES(?,?,?)",
0299:                       (format_code(r.get("code","").strip()),r.get("description","").strip(),r.get("uom","").strip()))
0300:     c.commit()
0301: 
0302: def backup_database(manual=False):
0303:     """Create a safe, restorable full backup (a .db snapshot + a .zip copy)
0304:     in BACKUP_DIR. Runs automatically on every logout/exit, and can also be
0305:     triggered manually from the Backup Now button. Keeps the most recent
0306:     30 automatic backups plus every manual one, so disk space stays sane."""
0307:     try:
0308:         if not os.path.exists(DB): return None
0309:         stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
0310:         tag="manual" if manual else "auto"
0311:         latest=os.path.join(BACKUP_DIR,"inventory_backup_latest.db")
0312:         dated=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.db")
0313:         zpath=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.zip")
0314: 
0315:         src=sqlite3.connect(DB)
0316:         for path in (latest,dated):
```
```text
0310:         tag="manual" if manual else "auto"
0311:         latest=os.path.join(BACKUP_DIR,"inventory_backup_latest.db")
0312:         dated=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.db")
0313:         zpath=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.zip")
0314: 
0315:         src=sqlite3.connect(DB)
0316:         for path in (latest,dated):
0317:             if os.path.exists(path): os.remove(path)
0318:             dst=sqlite3.connect(path)
0319:             with dst:
0320:                 src.backup(dst)
0321:             dst.close()
0322:         src.close()
0323: 
0324:         with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
0325:             z.write(dated,"store_inventory.db")
0326: 
0327:         # Automatic backup rotation/deletion is intentionally disabled.
0328:         # Stored backups remain until the user explicitly deletes/restores them.
0329:         return zpath
0330:     except Exception:
```
```text
0325:             z.write(dated,"store_inventory.db")
0326: 
0327:         # Automatic backup rotation/deletion is intentionally disabled.
0328:         # Stored backups remain until the user explicitly deletes/restores them.
0329:         return zpath
0330:     except Exception:
0331:         return None
0332: 
0333: def restore_database(backup_path):
0334:     """Restore the database from a .db or .zip backup file. The current
0335:     database is itself backed up first, so a restore can never destroy data."""
0336:     try:
0337:         backup_database(manual=True)  # safety net before touching anything
0338:         if backup_path.lower().endswith(".zip"):
0339:             with zipfile.ZipFile(backup_path,"r") as z:
0340:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0341:                 os.makedirs(tmp_dir,exist_ok=True)
0342:                 z.extractall(tmp_dir)
0343:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0344:                 shutil.copy2(extracted,DB)
0345:                 shutil.rmtree(tmp_dir,ignore_errors=True)
```
```text
0339:             with zipfile.ZipFile(backup_path,"r") as z:
0340:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0341:                 os.makedirs(tmp_dir,exist_ok=True)
0342:                 z.extractall(tmp_dir)
0343:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0344:                 shutil.copy2(extracted,DB)
0345:                 shutil.rmtree(tmp_dir,ignore_errors=True)
0346:         else:
0347:             shutil.copy2(backup_path,DB)
0348:         return True
0349:     except Exception:
0350:         return False
0351: 
0352: def stock(c, code):
0353:     r=c.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()
0354:     q=float(r[0] or 0) if r else 0
0355:     for typ,qty in c.execute("SELECT doc_type,qty FROM transactions WHERE code=? ORDER BY id", (code,)):
0356:         q += float(qty or 0) if typ=="GRR" else -float(qty or 0) if typ=="ISSUE" else 0
0357:     return q
0358: 
0359: def fmt_num(x):
```
```text
0357:     return q
0358: 
0359: def fmt_num(x):
0360:     x=float(x or 0)
0361:     return f"{x:,.2f}".rstrip("0").rstrip(".")
0362: 
0363: def to_iso_date(s):
0364:     """Convert a user-entered DD/MM/YYYY date (or an already-ISO date) into
0365:     ISO YYYY-MM-DD for storage in the database and for date-range queries,
0366:     which rely on ISO strings sorting/comparing correctly."""
0367:     s=(s or "").strip()
0368:     if not s: return ""
0369:     for f in ("%d/%m/%Y","%Y-%m-%d"):
0370:         try: return datetime.strptime(s,f).strftime("%Y-%m-%d")
0371:         except Exception: continue
0372:     return s
0373: 
0374: def to_display_date(s):
0375:     """Convert an ISO YYYY-MM-DD date (as stored in the database) into the
0376:     DD/MM/YYYY format used everywhere on screen and on printed reports."""
0377:     s=(s or "").strip()
```
```text
0472:     return on_enter
0473: 
0474: 
0475: class App(tk.Tk):
0476:     def __init__(self):
0477:         super().__init__()
0478:         self.title("Store Inventory Management System | SAP Style")
0479:         self.geometry("1400x820"); self.minsize(1150,700)
0480:         self.conn=connect()
0481:         self.demand_lines=[]; self.grr_lines=[]; self.issue_lines=[]
0482:         self.current_user=None; self.current_role=None
0483:         self._item_master_search_entry=None
0484:         self._item_master_find_callback=None
0485:         self._portable_print_context=None
0486:         self.can_edit=False; self.can_delete=False; self.is_admin=False
0487:         self._setup_style()
0488:         # Any focused button can be activated with Enter.
0489:         self.bind_all("<Return>", self._global_enter, add="+")
0490:         self.bind_all("<KP_Enter>", self._global_enter, add="+")
0491:         self.bind_all("<Control-f>", self._ctrl_f, add="+")
0492:         self.protocol("WM_DELETE_WINDOW", self.on_close)
```
```text
0540:     @staticmethod
0541:     def _shade(hexcolor, factor):
0542:         """Return a slightly darker version of a #RRGGBB color (for hover/press states)."""
0543:         h=hexcolor.lstrip("#")
0544:         r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
0545:         r,g,b=(max(0,int(v*factor)) for v in (r,g,b))
0546:         return f"#{r:02x}{g:02x}{b:02x}"
0547: 
0548:     def on_close(self):
0549:         try:
0550:             self.conn.commit(); backup_database()
0551:         except Exception:
0552:             pass
0553:         self.destroy()
0554: 
0555:     def redo_network_setup(self):
0556:         if not messagebox.askyesno("Network Setup",
0557:             "This will clear the online database URL saved on this computer.\n\n"
0558:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0559:             "Continue?"):
0560:             return
```
```text
0554: 
0555:     def redo_network_setup(self):
0556:         if not messagebox.askyesno("Network Setup",
0557:             "This will clear the online database URL saved on this computer.\n\n"
0558:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0559:             "Continue?"):
0560:             return
0561:         try:
0562:             self.conn.commit(); backup_database()
0563:         except Exception:
0564:             pass
0565:         try:
0566:             if os.path.exists(FIREBASE_URL_FILE): os.remove(FIREBASE_URL_FILE)
0567:         except Exception:
0568:             pass
0569:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0570:         self.destroy()
0571:         sys.exit(0)
0572: 
0573:     def backup_now(self):
0574:         path=backup_database(manual=True)
```
```text
0568:             pass
0569:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0570:         self.destroy()
0571:         sys.exit(0)
0572: 
0573:     def backup_now(self):
0574:         path=backup_database(manual=True)
0575:         if path:
0576:             messagebox.showinfo("Backup Complete",
0577:                 f"A full backup was saved to:\n\n{path}\n\n"
0578:                 f"All backups are kept in:\n{BACKUP_DIR}")
0579:         else:
0580:             messagebox.showerror("Backup Failed","Could not create a backup. Make sure the database exists.")
0581: 
0582:     def restore_backup(self):
0583:         from tkinter import filedialog
0584:         if not messagebox.askyesno("Restore Backup",
0585:             "This will replace all current data with the selected backup.\n"
0586:             "A safety backup of the current data will be made first.\n\n"
0587:             "Continue?"):
0588:             return
```
```text
0582:     def restore_backup(self):
0583:         from tkinter import filedialog
0584:         if not messagebox.askyesno("Restore Backup",
0585:             "This will replace all current data with the selected backup.\n"
0586:             "A safety backup of the current data will be made first.\n\n"
0587:             "Continue?"):
0588:             return
0589:         path=filedialog.askopenfilename(
0590:             title="Select a backup file",
0591:             initialdir=BACKUP_DIR,
0592:             filetypes=[("Backup files","*.zip *.db"),("All files","*.*")])
0593:         if not path: return
0594:         if restore_database(path):
0595:             messagebox.showinfo("Restore Complete",
0596:                 "Data has been restored. The application will now restart.")
0597:             self.conn.close()
0598:             os.execv(sys.executable, [sys.executable]+sys.argv)
0599:         else:
0600:             messagebox.showerror("Restore Failed","Could not restore from that backup file.")
0601: 
0602:     def _ctrl_f(self, event=None):
```
```text
0639:             if not text:
0640:                 fe.focus_set(); return
0641:             try:
0642:                 found=search_fn(text)
0643:             except Exception:
0644:                 found=False
0645:             if found is False:
0646:                 messagebox.showinfo("Find Text","No matching text found.",parent=dlg)
0647:         def close():
0648:             try:
0649:                 dlg.grab_release()
0650:             except Exception: pass
0651:             try: dlg.destroy()
0652:             except Exception: pass
0653:             if getattr(self,"_exact_find_text_dialog",None) is dlg:
0654:                 self._exact_find_text_dialog=None
0655:         ttk.Button(box,text="Find Next",command=do_find,width=13).grid(row=0,column=3,padx=4,pady=4)
0656:         ttk.Button(box,text="Cancel",command=close,width=13).grid(row=1,column=3,padx=4,pady=4)
0657:         fe.bind("<Return>",lambda e:(do_find(),"break"))
0658:         dlg.bind("<Escape>",lambda e:close())
0659:         dlg.protocol("WM_DELETE_WINDOW",close)
```
```text
0725:         cur_ent=ttk.Entry(box,textvariable=current,width=28,show="*"); cur_ent.grid(row=2,column=1,pady=7)
0726:         ttk.Label(box,text="New Password").grid(row=3,column=0,sticky="w",pady=7)
0727:         new_ent=ttk.Entry(box,textvariable=new,width=28,show="*"); new_ent.grid(row=3,column=1,pady=7)
0728:         ttk.Label(box,text="Confirm New Password").grid(row=4,column=0,sticky="w",pady=7)
0729:         conf_ent=ttk.Entry(box,textvariable=confirm,width=28,show="*"); conf_ent.grid(row=4,column=1,pady=7)
0730:         err=ttk.Label(box,text="",foreground="#c0392b",wraplength=380,justify="left")
0731:         err.grid(row=5,column=0,columnspan=2,pady=(5,8))
0732: 
0733:         def save_password(event=None):
0734:             old_pw=current.get()
0735:             new_pw=new.get()
0736:             confirm_pw=confirm.get()
0737:             row=self.conn.execute("SELECT password FROM users WHERE username=?",(self.current_user,)).fetchone()
0738:             if not row or not verify_password(old_pw,row[0]):
0739:                 err.config(text="Current password is incorrect."); return
0740:             if len(new_pw) < 4:
0741:                 err.config(text="New password must be at least 4 characters."); return
0742:             if new_pw != confirm_pw:
0743:                 err.config(text="New password and confirmation do not match."); return
0744:             if new_pw == old_pw:
0745:                 err.config(text="New password must be different from the current password."); return
```
```text
0741:                 err.config(text="New password must be at least 4 characters."); return
0742:             if new_pw != confirm_pw:
0743:                 err.config(text="New password and confirmation do not match."); return
0744:             if new_pw == old_pw:
0745:                 err.config(text="New password must be different from the current password."); return
0746:             try:
0747:                 self.conn.execute("UPDATE users SET password=? WHERE username=?",
0748:                                   (hash_password(new_pw),self.current_user))
0749:                 self.conn.commit()
0750:                 backup_database()
0751:                 win.grab_release(); win.destroy()
0752:                 messagebox.showinfo("Password Changed",
0753:                     "Your password has been changed successfully.\n\nUse the new password the next time you log in.", parent=self)
0754:             except Exception as ex:
0755:                 err.config(text=f"Could not change password: {ex}")
0756: 
0757:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0758:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0759:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0760:         conf_ent.bind("<Return>",save_password)
0761:         cur_ent.focus_set()
```
```text
0757:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0758:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0759:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0760:         conf_ent.bind("<Return>",save_password)
0761:         cur_ent.focus_set()
0762: 
0763:     def logout(self):
0764:         try:
0765:             self.conn.commit(); backup_database()
0766:         except Exception:
0767:             pass
0768:         self.login()
0769: 
0770:     def home(self):
0771:         self.wipe()
0772:         self.build_menu_bar()
0773:         hdr=tk.Frame(self,bg=COLORS["primary_dark"]);hdr.pack(fill="x")
0774:         self._shell_header=hdr
0775:         inner=tk.Frame(hdr,bg=COLORS["primary_dark"],padx=16,pady=10);inner.pack(fill="x")
0776:         tk.Label(inner,text=COMPANY,font=("Segoe UI",16,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="left")
0777:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
```
```text
0777:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
0778:         tk.Label(inner,text=f"Data: {DATA_DIR}",font=("Segoe UI",8),bg=COLORS["primary_dark"],fg="#9FB8DA").pack(side="left",padx=14)
0779:         ttk.Button(inner,text="Logout",style="Danger.TButton",command=self.logout).pack(side="right")
0780:         tk.Label(inner,text=f"{self.current_user}  ({self.current_role})",font=("Segoe UI",9,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="right",padx=12)
0781:         nav=tk.Frame(self,bg=COLORS["primary"]);nav.pack(fill="x")
0782:         self._shell_nav=nav
0783:         navin=tk.Frame(nav,bg=COLORS["primary"],padx=10,pady=6);navin.pack(fill="x")
0784:         ttk.Button(navin,text="🏠  Dashboard",style="Accent.TButton",command=self.dashboard).pack(side="left",padx=3)
0785:         tk.Label(navin,text="Inventory  |  Transaction  |  Report  |  Edit  |  Help  —  see the menu bar above for every other section.",
0786:                  font=("Segoe UI",8),bg=COLORS["primary"],fg="#E7EFFB").pack(side="left",padx=14)
0787:         self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
0788:         self.main_body=self.body
0789:         self.dashboard()
0790: 
0791:     def _ensure_mdi_host(self):
0792:         """Create the in-app MDI workspace. Child windows never leave the main program."""
0793:         host=getattr(self,"_mdi_host",None)
0794:         if host is None or not host.winfo_exists():
0795:             host=tk.Frame(self.main_body,bg="#d9dde3",bd=0,highlightthickness=0)
0796:             self._mdi_host=host
0797:         host.place(relx=0,rely=0,relwidth=1,relheight=1)
```
```text
0860:             b.pack(side="left")
0861:             rb=tk.Button(item,text="□",font=("Segoe UI",8,"bold"),width=2,height=1,padx=0,pady=0,
0862:                          command=lambda:(restore(),maximize()),relief="flat",bd=0,bg="#e7e7e7")
0863:             rb.pack(side="left")
0864:             xb=tk.Button(item,text="×",font=("Segoe UI",9,"bold"),width=2,height=1,padx=0,pady=0,
0865:                          command=close,relief="flat",bd=0,bg="#e7e7e7")
0866:             xb.pack(side="left")
0867:             state["task"]=item
0868:         def close():
0869:             try:
0870:                 task=state.get("task")
0871:                 if task and task.winfo_exists(): task.destroy()
0872:             except Exception: pass
0873:             try:
0874:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
0875:             except Exception: pass
0876:             try: outer.destroy()
0877:             except Exception: pass
0878:             if not getattr(self,"_mdi_windows",[]):
0879:                 self._mdi_host.place_forget()
0880:                 # Restore the original application shell FIRST, then rebuild
```
```text
0924:             return None
0925:         self._inventory_codes_filter=criteria
0926:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0927:         try:
0928:             self.items(container=body)
0929:             win.lift()
0930:             return win
0931:         except Exception:
0932:             try: win._internal_close()
0933:             except Exception: pass
0934:             raise
0935: 
0936:     def open_inventory_codes_report_window(self, criteria=None):
0937:         """Open Inventory Codes as a real report-style child window.
0938: 
0939:         This intentionally mirrors the supplied Preview Report workflow: a
0940:         separate resizable/maximizable window with a left navigation tree,
0941:         compact report toolbar, Find dialog, and print/export commands.
0942:         The main application remains open behind it.
0943:         """
0944:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
0941:         compact report toolbar, Find dialog, and print/export commands.
0942:         The main application remains open behind it.
0943:         """
0944:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
0945:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
0946:         }
0947:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0948: 
0949:         # --- report-style toolbar ---
0950:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
0951:         toolbar.pack(fill="x",side="top")
0952:         toolbar.pack_propagate(False)
0953: 
0954:         def tbtn(text,cmd,width=9):
0955:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
0956:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
0957:                          padx=3,pady=1)
0958:             b.pack(side="left",padx=2,pady=6)
0959:             return b
0960: 
0961:         # --- main report body ---
```
```text
0972:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
0973:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
0974:         navscroll.config(command=code_tree.yview)
0975:         navscroll.pack(side="right",fill="y")
0976:         code_tree.pack(side="left",fill="both",expand=True)
0977: 
0978:         right=tk.Frame(content,bg="#EDEDED")
0979:         right.pack(side="left",fill="both",expand=True)
0980:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
0981:         reportbar.pack(fill="x")
0982:         reportbar.pack_propagate(False)
0983:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
0984:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
0985:         tab.pack(side="left",padx=4,pady=2)
0986:         titlevar=tk.StringVar(value="Inventory Summary")
0987:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
0988:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
0989: 
0990:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
0991:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
0992:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1126:                     vals=tree.item(iid,"values")
1127:                     if str(vals[1]).lower()==str(target).lower():
1128:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1129:                 return True
1130:             self._open_exact_find_text_popup(search_fn)
1131:             self._item_master_find_callback=find_popup
1132: 
1133: 
1134:         def print_report():
1135:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1136:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1137:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1138: 
1139:         def export_pdf():
1140:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1141:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1142:         def export_word():
1143:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1144:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1145:         def export_excel():
1146:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1142:         def export_word():
1143:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1144:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1145:         def export_excel():
1146:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1147:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1148: 
1149:         tbtn("Find",find_popup,7)
1150:         tbtn("Print",print_report,7)
1151:         tbtn("PDF",export_pdf,6)
1152:         tbtn("Word",export_word,6)
1153:         tbtn("Excel",export_excel,6)
1154:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1155:         tbtn("Refresh",load,8)
1156:         tbtn("Close",win._internal_close,7)
1157:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1158:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1159: 
1160:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1161:         build_nav(); load(); win.focus_force()
1162:         return win
```
```text
1172:         self.body=frame
1173:         closed={"done":False}
1174:         def close_window():
1175:             if closed["done"]: return
1176:             closed["done"]=True
1177:             if getattr(self,"body",None) is frame: self.body=old_body
1178:             self._page_actions=old_actions
1179:             self._item_master_find_callback=old_find
1180:             try: win._internal_close()
1181:             except Exception: win.destroy()
1182:         win._internal_close=close_window
1183:         try:
1184:             method(); self.update_idletasks(); win.lift(); return win
1185:         except Exception:
1186:             close_window(); raise
1187: 
1188:     def _manual_check_update(self):
1189:         try:
1190:             updater.check_for_update(self, manual=True)
1191:         except Exception as e:
1192:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1196:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1197:         except Exception as e:
1198:             messagebox.showerror("Current Version", str(e), parent=self)
1199: 
1200:     def build_menu_bar(self):
1201:         """Professional section / sub-section menu bar, ERP style:
1202:         Inventory > Item Master
1203:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1204:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1205:         Edit > Change Password, User Management
1206:         Help > Backup Now, Restore Backup, Network Setup
1207:         """
1208:         menubar=tk.Menu(self)
1209: 
1210:         m_inv=tk.Menu(menubar,tearoff=0)
1211:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1212:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1213:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1214:         menubar.add_cascade(label="Inventory",menu=m_inv)
1215: 
1216:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1216:         m_trans=tk.Menu(menubar,tearoff=0)
1217:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1218:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1219:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1220:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1221:         menubar.add_cascade(label="Transaction",menu=m_trans)
1222: 
1223:         m_rep=tk.Menu(menubar,tearoff=0)
1224:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1225:         m_rep.add_separator()
1226:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1227:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1228:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1229:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1230:         menubar.add_cascade(label="Report",menu=m_rep)
1231: 
1232:         m_edit=tk.Menu(menubar,tearoff=0)
1233:         m_edit.add_command(label="Change Password",command=self.change_password)
1234:         if self.is_admin:
1235:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1236:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1231: 
1232:         m_edit=tk.Menu(menubar,tearoff=0)
1233:         m_edit.add_command(label="Change Password",command=self.change_password)
1234:         if self.is_admin:
1235:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1236:         menubar.add_cascade(label="Edit",menu=m_edit)
1237: 
1238:         m_help=tk.Menu(menubar,tearoff=0)
1239:         m_help.add_command(label="Backup Now",command=self.backup_now)
1240:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1241:         m_help.add_command(label="Current Version",command=self._show_current_version)
1242:         if self.is_admin:
1243:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1244:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1245:         menubar.add_cascade(label="Help",menu=m_help)
1246: 
1247:         self.config(menu=menubar)
1248: 
1249:     def open_calendar_picker(self, var):
1250:         """Small month-grid calendar popup. Picking a day sets `var` to
1251:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1304:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1305:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1306:         return f
1307: 
1308:     def clearbody(self):
1309:         self._portable_print_context=None
1310:         for w in self.body.winfo_children(): w.destroy()
1311:         self._page_actions = {
1312:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1313:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1314:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1315:             "cancel": lambda: self.dashboard(),
1316:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1317:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1318:         }
1319:         # Single SAP-style toolbar at the very top.
1320:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1321:         self._page_action_bar=bar
1322:         self._page_action_first_button=None
1323:         def run_action(k):
1324:             if k=="edit" and not self.can_edit:
```
```text
1321:         self._page_action_bar=bar
1322:         self._page_action_first_button=None
1323:         def run_action(k):
1324:             if k=="edit" and not self.can_edit:
1325:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1326:             if k=="delete" and not self.can_delete:
1327:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1328:             self._page_actions[k]()
1329:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1330:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1331:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1332:             b.pack(side="left",padx=(0,2))
1333:             if self._page_action_first_button is None: self._page_action_first_button=b
1334:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1335: 
1336:     def _portable_print_current(self):
1337:         ctx=getattr(self,"_portable_print_context",None)
1338:         if not ctx:
1339:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1340:             return
1341:         try:
```
```text
1343:             if not data: return
1344:             title,header,columns,rows=data
1345:             self.portable_print_dialog(title,header,columns,rows)
1346:         except Exception as e:
1347:             messagebox.showerror("Portable Printer",str(e))
1348: 
1349:     def portable_print_dialog(self,title,header_lines,columns,rows):
1350:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1351:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1352:         if not WIN32PRINT_AVAILABLE:
1353:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1354:             return
1355:         try:
1356:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1357:         except Exception as e:
1358:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1359:             return
1360:         if not printers:
1361:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1362:             return
1363:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1413:                 if vals and pv.get() not in vals: pv.set(vals[0])
1414:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1415:             except Exception as ex: status.set(str(ex))
1416:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1417:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1418:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1419:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1420:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1421:         win.bind("<Escape>",lambda e:win._internal_close())
1422:         win.focus_force()
1423: 
1424:     def preview_tree(self, title, tree, header_lines=None):
1425:         """Preview the exact rows currently visible in a Treeview."""
1426:         cols=list(tree["columns"])
1427:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1428:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1429:         if not rows:
1430:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1431:             return
1432:         widths=[]
1433:         for c in cols:
```
```text
1430:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1431:             return
1432:         widths=[]
1433:         for c in cols:
1434:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1435:             except Exception: widths.append(100)
1436:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1437: 
1438:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1439:         self._page_actions.update({
1440:             "save": save or self._page_actions.get("save"),
1441:             "edit": edit or self._page_actions.get("edit"),
1442:             "delete": delete or self._page_actions.get("delete"),
1443:             "cancel": cancel or self._page_actions.get("cancel"),
1444:             "print": print or self._page_actions.get("print"),
1445:             "preview": preview or self._page_actions.get("preview"),
1446:         })
1447: 
1448:     def _add_transaction_new_button(self, command):
1449:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1450:         if bar is None or first is None: return
```
```text
1459:         sep.pack(side="left",fill="y",padx=4)
1460:         for w in existing:
1461:             try:
1462:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1463:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1464:                 else: w.pack(side="left")
1465:             except Exception: pass
1466: 
1467:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1468:         """Draw a consistent professional report header and return the first table Y.
1469: 
1470:         For GRN Receipt reports the document number is shown on the left and
1471:         the GRN Date is deliberately shown on the right in a bordered document
1472:         information panel.
1473:         """
1474:         W,H=page_size
1475:         if y_top is None: y_top=H-24
1476:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1477:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1478:         if os.path.exists(LOGO_FILE):
1479:             try:
```
```text
1472:         information panel.
1473:         """
1474:         W,H=page_size
1475:         if y_top is None: y_top=H-24
1476:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1477:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1478:         if os.path.exists(LOGO_FILE):
1479:             try:
1480:                 from reportlab.lib.utils import ImageReader
1481:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1482:             except Exception:
1483:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1484:         else:
1485:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1486:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1487:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1488:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1489:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1490: 
1491:         # Professional document information box.
1492:         info_top=logo_y-12
```
```text
1525:                 # naturally occupies the right-hand cell when supplied second.
1526:                 c.setFont("Helvetica-Bold",7)
1527:                 c.drawString(xx,yy,(label+":")[:28])
1528:                 c.setFont("Helvetica",7)
1529:                 c.drawString(xx+58,yy,val[:58])
1530:             return box_y-12
1531:         return info_top-6
1532: 
1533:     def _report_footer(self, c, page_no, page_size=A4):
1534:         W,H=page_size
1535:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1536:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1537:         c.drawString(24,13,REPORT_FOOTER)
1538:         c.drawRightString(W-24,13,f"Page {page_no}")
1539:         c.setFillColorRGB(0,0,0)
1540: 
1541:     def _grr_signature_block(self, c, y, page_size=A4):
1542:         """Draw the three requested transaction-document signature lines."""
1543:         W,H=page_size
1544:         labels=["Prepared By","Store Keeper","Store Incharge"]
1545:         block_h=70
```
```text
1552:             x=left+i*col_w
1553:             c.setLineWidth(0.6)
1554:             c.line(x+30,top-34,x+col_w-30,top-34)
1555:             c.setFont("Helvetica-Bold",7)
1556:             c.drawCentredString(x+col_w/2,top-48,label)
1557:         return True
1558: 
1559:     def _finish_page(self, c, page_no, page_size=A4):
1560:         self._report_footer(c,page_no,page_size); c.showPage()
1561: 
1562:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1563:         """Word-wrap `text` into a list of lines that each fit inside
1564:         max_width (points) at the given font, breaking mid-word only when a
1565:         single word is itself wider than the column."""
1566:         text=str(text) if text is not None else ""
1567:         if not text:
1568:             return [""]
1569:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1570:         lines=[]; cur=""
1571:         for word in text.split(" "):
1572:             trial=(cur+" "+word).strip() if cur else word
```
```text
1581:                     mid=(lo+hi)//2
1582:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1583:                     else: hi=mid-1
1584:                 lines.append(w[:fit_at]); w=w[fit_at:]
1585:             cur=w
1586:         if cur: lines.append(cur)
1587:         return lines or [""]
1588: 
1589:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1590:         """Create a paginated professional PDF with logo, bordered information,
1591:         GRR signature lines and page numbers. Also keep the same report data in
1592:         memory so the built-in Windows printer dialog can print directly without
1593:         requiring a PDF application's PrintTo association."""
1594:         if not hasattr(self, "_print_jobs"):
1595:             self._print_jobs = {}
1596:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1597:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1598:         page=1
1599:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1600:         usable=W-56
1601:         n=max(1,len(headers))
```
```text
1623:             if desc_idx is not None and desc_idx < len(r):
1624:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1625:             else:
1626:                 desc_lines=[""]
1627:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1628:             # Reserve room on the final page for the three transaction signatures + footer.
1629:             reserve=120 if is_transaction_doc else 42
1630:             if y-row_h<reserve:
1631:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1632:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1633:             # Item rows are intentionally border-free. The section/header remains
1634:             # professional while avoiding the unwanted boxed line around each
1635:             # individual printed item row. Description is drawn separately
1636:             # below (auto-fit / wrapped), so it is skipped in this pass.
1637:             for ci,(xx,val) in enumerate(zip(xs,r)):
1638:                 if ci==desc_idx: continue
1639:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1640:             if desc_idx is not None and desc_idx < len(r):
1641:                 for li,ln in enumerate(desc_lines):
1642:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1643:             y-=row_h
```
```text
1638:                 if ci==desc_idx: continue
1639:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1640:             if desc_idx is not None and desc_idx < len(r):
1641:                 for li,ln in enumerate(desc_lines):
1642:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1643:             y-=row_h
1644:         if is_transaction_doc:
1645:             # Keep the three requested transaction signatures at the physical bottom
1646:             # final page, immediately above the report footer.  If the item
1647:             # table reaches this reserved area, start a fresh final page.
1648:             bottom_sig_y = 138
1649:             if y < 165:
1650:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1651:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1652:             # Draw signatures at a fixed bottom position so they never float
1653:             # directly after the last item row.
1654:             self._grr_signature_block(c,bottom_sig_y,page_size)
1655:         self._report_footer(c,page,page_size); c.save()
1656:         if auto_print:
1657:             self.print_pdf(path)
1658:         return path
```
```text
1652:             # Draw signatures at a fixed bottom position so they never float
1653:             # directly after the last item row.
1654:             self._grr_signature_block(c,bottom_sig_y,page_size)
1655:         self._report_footer(c,page,page_size); c.save()
1656:         if auto_print:
1657:             self.print_pdf(path)
1658:         return path
1659: 
1660:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1661:         """Professional on-screen preview showing bordered document information
1662:         and a bordered item section. GRN Date is displayed in the right column."""
1663:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1664:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1665:         # Preview intentionally hides the company logo and company name.
1666:         # The actual generated/printed PDF still contains both via
1667:         # _report_header(), so only the on-screen preview is affected.
1668:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1669:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1670:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1671: 
1672:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
```
```text
1693:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1694: 
1695:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1696:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1697:         tr=self.make_tree(items,columns,widths)
1698:         for r in rows: tr.insert("", "end", values=r)
1699: 
1700:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1701:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1702:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1703:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1704:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1705:         win.bind("<Control-f>",bind_preview_find)
1706:         win.bind("<Control-F>",bind_preview_find)
1707: 
1708:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1709:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1710:         if is_transaction_preview:
1711:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1712:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1713:                 sig.columnconfigure(i,weight=1)
```
```text
1711:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1712:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1713:                 sig.columnconfigure(i,weight=1)
1714:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1715:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1716:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1717: 
1718:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1719:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1720:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1721:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1722:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1723:         if on_save:
1724:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1725:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1726:         if not is_transaction_preview:
1727:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1728:         # IMPORTANT: this must remain a normal top-level window (not transient
1729:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1730:         # exactly like the Preview Report window in the supplied recording.
1731:         # The Find dialog is opened from this window and is independent.
```
```text
1724:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1725:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1726:         if not is_transaction_preview:
1727:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1728:         # IMPORTANT: this must remain a normal top-level window (not transient
1729:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1730:         # exactly like the Preview Report window in the supplied recording.
1731:         # The Find dialog is opened from this window and is independent.
1732:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1733:         win.focus_force()
1734: 
1735:     def _safe_report_name(self, title, extension):
1736:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1737:         safe=safe.replace(" ","_") or "Preview"
1738:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1739: 
1740:     def print_preview_window(self, title, header_lines, columns, rows):
1741:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1742:         self._open_direct_printer(title, header_lines, columns, rows,
1743:                                   landscape(A4) if len(columns) > 8 else A4)
1744: 
```
```text
1737:         safe=safe.replace(" ","_") or "Preview"
1738:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1739: 
1740:     def print_preview_window(self, title, header_lines, columns, rows):
1741:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1742:         self._open_direct_printer(title, header_lines, columns, rows,
1743:                                   landscape(A4) if len(columns) > 8 else A4)
1744: 
1745:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1746:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1747:         This keeps the Export PDF button functional on a machine where the bundled
1748:         ReportLab package cannot be imported."""
1749:         def esc(v):
1750:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1751:         W,H=842,595
1752:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1753:         def add(txt,size=8,leading=11):
1754:             lines.append(f"/F1 {size} Tf")
1755:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1756:         add(str(title),12,16)
1757:         for h in header_lines or []:
```
```text
1764:         lines.append("ET")
1765:         stream="\n".join(lines).encode("latin-1","replace")
1766:         objs=[]
1767:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1768:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1769:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1770:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1771:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1772:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1773:         for i,obj in enumerate(objs,1):
1774:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1775:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1776:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1777:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1778:         with open(path,"wb") as f: f.write(out)
1779: 
1780:     def export_preview_pdf(self, title, header_lines, columns, rows):
1781:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1782:         try:
1783:             os.makedirs(REPORTS_DIR, exist_ok=True)
1784:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
```
```text
1777:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1778:         with open(path,"wb") as f: f.write(out)
1779: 
1780:     def export_preview_pdf(self, title, header_lines, columns, rows):
1781:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1782:         try:
1783:             os.makedirs(REPORTS_DIR, exist_ok=True)
1784:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1785:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1786:             generated = False
1787:             if REPORTLAB:
1788:                 try:
1789:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1790:                     generated = True
1791:                 except Exception:
1792:                     generated = False
1793:             if not generated:
1794:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1795:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1796:                 raise IOError("The PDF file was not created in the Reports folder.")
1797:             with open(path, "rb") as pf:
```
```text
1791:                 except Exception:
1792:                     generated = False
1793:             if not generated:
1794:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1795:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1796:                 raise IOError("The PDF file was not created in the Reports folder.")
1797:             with open(path, "rb") as pf:
1798:                 signature = pf.read(5)
1799:             if signature != b"%PDF-":
1800:                 raise IOError("The generated file is not a valid PDF.")
1801:             self._last_report_path = path
1802:             try:
1803:                 webbrowser.open("file://" + path)
1804:             except Exception:
1805:                 self.open_file(path)
1806:             return path
1807:         except Exception as e:
1808:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1809:             return None
1810: 
1811:     def export_preview_word(self, title, header_lines, columns, rows):
```
```text
1807:         except Exception as e:
1808:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1809:             return None
1810: 
1811:     def export_preview_word(self, title, header_lines, columns, rows):
1812:         """Export exactly what is visible in the current preview to Word."""
1813:         if not DOCX_AVAILABLE:
1814:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1815:         path=self._safe_report_name(title,"docx")
1816:         doc=Document()
1817:         sec=doc.sections[0]
1818:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1819:         sec.header.paragraphs[0].runs[0].bold=True
1820:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1821:         fp=sec.footer.paragraphs[0]
1822:         fp.alignment=2
1823:         if not is_transaction_preview:
1824:             fp.add_run("Authorized Signatory: ____________________    Store In-Charge: ____________________    Page ")
1825:             fld=fp.add_run(); fld._r.append(__import__('docx').oxml.OxmlElement('w:fldChar')); fld._r[-1].set(__import__('docx').oxml.ns.qn('w:fldCharType'),'begin')
1826:             instr=__import__('docx').oxml.OxmlElement('w:instrText'); instr.text='PAGE'; fld._r.append(instr)
1827:             fld2=__import__('docx').oxml.OxmlElement('w:fldChar'); fld2.set(__import__('docx').oxml.ns.qn('w:fldCharType'),'end'); fld._r.append(fld2)
```
```text
1842:             doc.add_paragraph("")
1843:             sig=doc.add_table(rows=2,cols=3)
1844:             labels=["Prepared By","Store Keeper","Store Incharge"]
1845:             for i,label in enumerate(labels):
1846:                 sig.cell(0,i).text="____________________"
1847:                 sig.cell(1,i).text=label
1848:                 for para in sig.cell(1,i).paragraphs:
1849:                     for run in para.runs: run.bold=True
1850:         doc.save(path)
1851:         self.open_file(path)
1852: 
1853:     def export_preview_excel(self, title, header_lines, columns, rows):
1854:         """Export exactly what is visible in the current preview to Excel."""
1855:         if not XLSX_AVAILABLE:
1856:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
1857:         path=self._safe_report_name(title,"xlsx")
1858:         wb=openpyxl.Workbook(); ws=wb.active
1859:         ws.title="Preview"
1860:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
1861:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1862:         if not is_transaction_preview:
```
```text
1880:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
1881:             for col in range(1,4):
1882:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
1883:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
1884:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
1885:         for col_cells in ws.columns:
1886:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
1887:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
1888:         wb.save(path)
1889:         self.open_file(path)
1890: 
1891:     def make_tree(self,parent,cols,widths=None):
1892:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
1893:         tr=ttk.Treeview(fr,columns=cols,show="headings")
1894:         for i,c in enumerate(cols):
1895:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
1896:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
1897:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
1898:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
1899:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
1900:         return tr
```
```text
1953:                     w.state(["!disabled"] if editable else ["disabled"])
1954:             except Exception:
1955:                 try: w.configure(state="normal" if editable else "disabled")
1956:                 except Exception: pass
1957:             for ch in w.winfo_children(): walk(ch)
1958:         for root in roots: walk(root)
1959: 
1960:     def document_selector(self, parent, label, typ, var, load_callback):
1961:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
1962:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
1963:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
1964:         combo.pack(side="left", padx=4)
1965:         def refresh():
1966:             vals=[]
1967:             if typ=="demand":
1968:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
1969:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
1970:             elif typ=="grr":
1971:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
1972:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
1973:             else:
```
```text
1980:             no=text.split(" -> ",1)[0].strip()
1981:             var.set(no)
1982:             load_callback(no)
1983:         combo.bind("<<ComboboxSelected>>", selected)
1984:         combo.bind("<Return>", selected)
1985:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
1986:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
1987:         refresh()
1988:         # Keep the currently open transaction's saved-record list live.
1989:         # Each save calls refresh_saved_cache(), so newly saved records appear
1990:         # immediately without closing/reopening the window or pressing Refresh.
1991:         if not hasattr(self, "_document_selector_refreshers"):
1992:             self._document_selector_refreshers = {}
1993:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
1994:         return combo
1995: 
1996:     def dashboard(self):
1997:         # Dashboard-only visual refresh. All existing data queries, filters,
1998:         # callbacks and report/detail behavior are intentionally preserved.
1999:         self.clearbody()
2000:         c=self.conn
```
```text
2079:             for x in tr.get_children(): tr.delete(x)
2080:             params=[];where=[]
2081:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2082:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2083:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2084:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2085:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2086:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2087:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2088:                    FROM transactions t JOIN items i ON i.code=t.code"""
2089:             if where: sql += " WHERE " + " AND ".join(where)
2090:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2091:             rows=list(c.execute(sql,params))
2092:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2093:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2094:             bal_after={}
2095:             for txid,cc,typ,qty in alltx:
2096:                 running.setdefault(cc,0.0)
2097:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2098:                 bal_after[txid]=running[cc]
2099:             for r in rows:
```
```text
2457:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2458:         load()
2459:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2460: 
2461:     def inventory_codes(self):
2462:         """Inventory Codes using the classic desktop inventory interface.
2463: 
2464:         This screen intentionally follows the uploaded Inventory Management
2465:         reference: a simple module title, compact New/Edit/Delete/Save/
2466:         Refresh/Print/Close action row, and a full-width editable data grid.
2467:         All records come from the V18 database, so existing inventory data is
2468:         preserved rather than recreated.
2469:         """
2470:         self.clearbody()
2471:         # Remove the generic SAP action row; this page owns its own classic
2472:         # action row just like the reference Inventory/Items screen.
2473:         if self.body.winfo_children():
2474:             try:
2475:                 self.body.winfo_children()[0].destroy()
2476:             except Exception:
2477:                 pass
```
```text
2530:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2531:         if filter_text:
2532:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2533:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2534: 
2535:         editing={"id":None,"new":False}
2536:         cell_editor={"widget":None}
2537: 
2538:         def close_editor(save_value=False):
2539:             w=cell_editor.get("widget")
2540:             if not w:
2541:                 return
2542:             try:
2543:                 if save_value:
2544:                     w.event_generate("<Return>")
2545:                 w.destroy()
2546:             except Exception:
2547:                 pass
2548:             cell_editor["widget"]=None
2549: 
2550:         def edit_cell(event=None):
```
```text
2560:             bbox=tree.bbox(iid,colid)
2561:             if not bbox: return
2562:             close_editor(False)
2563:             x,y,w,h=bbox
2564:             val=str(tree.item(iid,"values")[idx] or "")
2565:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2566:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2567:             cell_editor["widget"]=e
2568:             def commit(_=None):
2569:                 try:
2570:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2571:                 finally:
2572:                     try:e.destroy()
2573:                     except Exception:pass
2574:                     cell_editor["widget"]=None
2575:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2576:             e.bind("<FocusOut>",commit)
2577: 
2578:         def rows_query():
2579:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2580:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2582:             if tc: where.append("code <= ?"); params.append(tc)
2583:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2584:             if df or dt:
2585:                 sub=[]; sp=[]
2586:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2587:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2588:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2589:                 params.extend(sp)
2590:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2591:             return sql,params
2592: 
2593:         def load():
2594:             close_editor(False)
2595:             for i in tree.get_children(): tree.delete(i)
2596:             sql,params=rows_query()
2597:             count=0
2598:             for r in self.conn.execute(sql,params):
2599:                 # V18 stores UOM/opening and the original application may have
2600:                 # rate/remarks columns in some versions. Read them safely.
2601:                 rid,code,desc,uom,opening,rate,remarks=r
2602:                 bal=stock(self.conn,code)
```
```text
2616:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2617:             editing["id"]=None; editing["new"]=True
2618:             # Put the user directly into the Code cell.
2619:             try:
2620:                 bbox=tree.bbox(iid,"#2")
2621:                 if bbox:
2622:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2623:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2624:                     def commit(_=None):
2625:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2626:                         try:e.destroy()
2627:                         except Exception:pass
2628:                         cell_editor["widget"]=None
2629:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2630:             except Exception: pass
2631:             status.set("New row added — enter values, then press Save")
2632: 
2633:         def selected_row():
2634:             a=tree.selection()
2635:             return a[0] if a else None
2636: 
```
```text
2636: 
2637:         def edit_record():
2638:             iid=selected_row()
2639:             if not iid:
2640:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2641:             if not self.can_edit and not self.is_admin:
2642:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2643:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2644:             status.set("Edit mode — double-click any cell to change it, then press Save")
2645:             tree.focus(iid); tree.see(iid)
2646: 
2647:         def save_record():
2648:             iid=selected_row()
2649:             if not iid:
2650:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2651:             if not self.can_edit and not self.is_admin:
2652:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2653:             close_editor(True)
2654:             vals=list(tree.item(iid,"values"))
2655:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2656:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2654:             vals=list(tree.item(iid,"values"))
2655:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2656:             try: opening=float(str(vals[4]).strip() or 0)
2657:             except Exception: raise ValueError("Opening Qty must be a number.")
2658:             try: rate=float(str(vals[5]).strip() or 0)
2659:             except Exception: raise ValueError("Rate must be a number.")
2660:             remarks=str(vals[6]).strip()
2661:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2662:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2663:             if not desc:
2664:                 messagebox.showerror("Save","Description is required."); return
2665:             if opening<0:
2666:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2667:             rid=vals[0]
2668:             try:
2669:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2670:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2671:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2672:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2673:                 if rid:
2674:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2677:                                       (code,desc,uom,opening,rid))
2678:                     if oldcode!=code:
2679:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2680:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2681:                             except Exception:pass
2682:                 else:
2683:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2684:                                       (code,desc,uom,"",opening,0,"Local",0))
2685:                 self.conn.commit(); backup_database(); load()
2686:                 messagebox.showinfo("Saved","Inventory Code saved successfully.")
2687:             except Exception as ex:
2688:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2689: 
2690:         def delete_record():
2691:             iid=selected_row()
2692:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2693:             if not self.can_delete and not self.is_admin:
2694:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2695:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2696:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2697:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
```
```text
2691:             iid=selected_row()
2692:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2693:             if not self.can_delete and not self.is_admin:
2694:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2695:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2696:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2697:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2698:             try:
2699:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2700:             except Exception as ex:
2701:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2702: 
2703:         def refresh(): load()
2704:         def do_print():
2705:             try:self.preview_tree("Inventory Codes",tree)
2706:             except Exception as ex:messagebox.showerror("Print",str(ex))
2707:         def do_close(): self.dashboard()
2708: 
2709:         btn("New",new_record,8)
2710:         btn("Edit",edit_record,8)
2711:         btn("Delete",delete_record,8)
```
```text
2704:         def do_print():
2705:             try:self.preview_tree("Inventory Codes",tree)
2706:             except Exception as ex:messagebox.showerror("Print",str(ex))
2707:         def do_close(): self.dashboard()
2708: 
2709:         btn("New",new_record,8)
2710:         btn("Edit",edit_record,8)
2711:         btn("Delete",delete_record,8)
2712:         btn("Save",save_record,8)
2713:         btn("Refresh",refresh,9)
2714:         btn("Preview",do_print,8)
2715:         btn("Print",do_print,8)
2716:         btn("Close",do_close,8)
2717: 
2718:         # Search is deliberately small and sits on the right, without changing
2719:         # the reference layout of the action buttons.
2720:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2721:         search=tk.StringVar()
2722:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2723:         se.pack(side="left",padx=2)
2724:         self._item_master_search_entry=se
```
```text
2732:                     tree.detach(iid)
2733:         search.trace_add("write",filter_grid)
2734:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2735: 
2736:         tree.bind("<Double-1>",edit_cell)
2737:         tree.bind("<F2>",lambda e: edit_record())
2738:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2739:         self._page_actions={
2740:             "save":save_record,"edit":edit_record,"delete":delete_record,
2741:             "cancel":do_close,"print":do_print,"preview":do_print
2742:         }
2743:         load()
2744: 
2745:     def open_mto_inventory_flow(self):
2746:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2747: 
2748:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2749:         Cancel/X only closes the popup.
2750:         """
2751:         criteria = self._ask_mto_inventory_filters()
2752:         if not criteria or criteria.get("cancelled"):
```
```text
2914:                 return False
2915:             destination.set(found_dest)
2916:             edit_mode.update(on=True, original=r[0], dest=found_dest)
2917:             code.set(r[0])
2918:             desc.set(r[1] or "")
2919:             uom.set(r[2] or UOM_OPTIONS[0])
2920:             opening.set(str(r[3] if r[3] is not None else 0))
2921:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
2922:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
2923:             err.set("")
2924:             edit_btn.configure(text="SAVE EDIT")
2925:             ce.focus_set()
2926:             return True
2927: 
2928:         def check_duplicates(*_):
2929:             c = code.get().strip()
2930:             d = desc.get().strip()
2931:             dest = destination.get()
2932:             msgs = []
2933:             r = row_for(dest, c) if len(norm(c)) == 8 else None
2934:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
2936:             dh = desc_hit(dest, d) if d else None
2937:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
2938:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
2939:             hint.set("\n".join(msgs))
2940: 
2941:         code.trace_add("write", check_duplicates)
2942:         desc.trace_add("write", check_duplicates)
2943: 
2944:         def save_code():
2945:             try:
2946:                 c = code.get().strip()
2947:                 d = desc.get().strip()
2948:                 u = uom.get().strip()
2949:                 dest = destination.get()
2950:                 digits = norm(c)
2951:                 if len(digits) != 8:
2952:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
2953:                 if not d:
2954:                     raise ValueError("Description is required.")
2955:                 try:
2956:                     op = float(opening.get().strip() or 0)
```
```text
2977:                         (c, d, u, op, iso, old)
2978:                     )
2979:                     action = "updated"
2980:                 else:
2981:                     self.conn.execute(
2982:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
2983:                         (c, d, u, "", op, 0, iso)
2984:                     )
2985:                     action = "saved"
2986:                 self.conn.commit()
2987:                 backup_database()
2988:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
2989:                 # Keep popup open for fast multiple entries.
2990:                 clear_form(keep_search=False)
2991:                 ce.focus_set()
2992:             except Exception as ex:
2993:                 self.conn.rollback()
2994:                 err.set(str(ex))
2995:                 messagebox.showerror("Code Opening", str(ex), parent=win)
2996: 
2997:         def edit_action():
```
```text
2993:                 self.conn.rollback()
2994:                 err.set(str(ex))
2995:                 messagebox.showerror("Code Opening", str(ex), parent=win)
2996: 
2997:         def edit_action():
2998:             if not edit_mode["on"]:
2999:                 load_for_edit()
3000:             else:
3001:                 save_code()
3002: 
3003:         def delete_code():
3004:             if not edit_mode["on"]:
3005:                 if not load_for_edit():
3006:                     return
3007:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3008:                 return
3009:             try:
3010:                 t = table_for(edit_mode["dest"])
3011:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3012:                 self.conn.commit()
3013:                 backup_database()
```
```text
3009:             try:
3010:                 t = table_for(edit_mode["dest"])
3011:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3012:                 self.conn.commit()
3013:                 backup_database()
3014:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3015:                 clear_form(keep_search=False)
3016:             except Exception as ex:
3017:                 self.conn.rollback()
3018:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3019: 
3020:         btns = ttk.Frame(box)
3021:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3022:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3023:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3024:         edit_btn.pack(side="left", padx=4, ipadx=8)
3025:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3026:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3027:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3028:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3029:         ce.focus_set()
```
```text
3023:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3024:         edit_btn.pack(side="left", padx=4, ipadx=8)
3025:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3026:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3027:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3028:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3029:         ce.focus_set()
3030: 
3031:     def _mto_new_item_dialog(self, on_saved):
3032:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3033:         brand-new item can be created without leaving that screen. Writes
3034:         straight into the same Item Master (items table) used everywhere."""
3035:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3036:         win.transient(self); win.grab_set()
3037:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3038:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3039:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3040:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3041:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3042:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3043:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3039:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3040:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3041:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3042:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3043:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3044:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3045:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3046:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3047:         def save():
3048:             try:
3049:                 c=code.get().strip(); d=desc.get().strip()
3050:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3051:                 if not d: raise ValueError("Description is required.")
3052:                 try:
3053:                     opening_val=float(opening.get() or 0)
3054:                 except ValueError:
3055:                     raise ValueError("Opening Qty must be a number.")
3056:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3057:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3058:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3059:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3052:                 try:
3053:                     opening_val=float(opening.get() or 0)
3054:                 except ValueError:
3055:                     raise ValueError("Opening Qty must be a number.")
3056:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3057:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3058:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3059:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3060:                 self.conn.commit(); backup_database()
3061:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3062:                 win.grab_release(); win.destroy()
3063:                 on_saved()
3064:             except Exception as ex: messagebox.showerror("Error",str(ex))
3065:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3066:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3067:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3068: 
3069:     def _item_filter_bar(self, parent, on_change):
3070:         """Item Code entry + item-master picker + Search/Show All. Calls
3071:         on_change() whenever the code changes or a button is pressed."""
3072:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3158:         self._item_master_find_callback=None
3159:         self._portable_print_context=None
3160:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3161:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3162:         }
3163: 
3164:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3165:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3166:         self.conn.commit()
3167: 
3168:         # ---- Same professional in-app window layout as Inventory Codes ----
3169:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3170:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3171:                   foreground=COLORS["primary_dark"]).pack(side="left")
3172:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3173: 
3174:         def open_find():
3175:             state_find={"index":-1}
3176:             def search_fn(text):
3177:                 text=text.strip().lower()
3178:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3265:             for i in table.get_children(): table.delete(i)
3266:             where=["1=1"]; params=[]
3267:             prefix=state.get("prefix",""); q=search.get().strip()
3268:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3269:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3270:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3271:             if fc: where.append("code >= ?"); params.append(fc)
3272:             if tc: where.append("code <= ?"); params.append(tc)
3273:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3274:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3275:             records=[]
3276:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3277:                 # If a date filter is supplied, accept an opening-date match OR
3278:                 # a transaction in that date range. This prevents valid MTO codes
3279:                 # from disappearing merely because an older record has no opening_date.
3280:                 if df or dt:
3281:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3282:                     if not ok:
3283:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3284:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3285:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3355:                 tr.insert("", "end", values=r)
3356:         def clear():
3357:             for x in v.values(): x.set("")
3358:             try: tr.selection_remove(tr.selection())
3359:             except Exception: pass
3360:             self._set_form_editable(party_form_roots, False)
3361:         def new_form():
3362:             clear(); self._set_form_editable(party_form_roots, True)
3363:         def save():
3364:             try:
3365:                 name=v["name"].get().strip()
3366:                 if not name: raise ValueError("Party Name is required.")
3367:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3368:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3369:             except Exception as ex: messagebox.showerror("Error",str(ex))
3370:         def load_party_row(a):
3371:             if not a:return
3372:             r=tr.item(a[0])["values"]
3373:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3374:             self._set_form_editable(party_form_roots, False)
3375:         def on_party_select(_=None):
```
```text
3381:             load_party_row(a)
3382:             self._set_form_editable(party_form_roots, True)
3383:         def delete_party():
3384:             a=tr.selection()
3385:             if not a:
3386:                 messagebox.showwarning("Delete", "Select a party first."); return
3387:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3388:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3389:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3390:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3391:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3392:         self._add_transaction_new_button(new_form)
3393:         load(); clear()
3394: 
3395:     def user_management(self):
3396:         self.clearbody()
3397:         if not self.is_admin:
3398:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3399:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3400:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3401:         role=tk.StringVar(value="User")
```
```text
3438:             u_ent.state(["!disabled"])
3439:         def edit():
3440:             a=tr.selection()
3441:             if not a:
3442:                 messagebox.showwarning("Edit User","Select a user row first."); return
3443:             r=tr.item(a[0])["values"]
3444:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3445:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3446:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3447:         def save():
3448:             try:
3449:                 username=v["username"].get().strip()
3450:                 if not username: raise ValueError("Username is required.")
3451:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3452:                 pw=v["password"].get()
3453:                 if exists:
3454:                     pw_hash = hash_password(pw) if pw else exists[0]
3455:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3456:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3457:                 else:
3458:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3453:                 if exists:
3454:                     pw_hash = hash_password(pw) if pw else exists[0]
3455:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3456:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3457:                 else:
3458:                     if not pw: raise ValueError("Password is required for a new user.")
3459:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3460:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3461:                 self.conn.commit(); backup_database(); load(); clear()
3462:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3463:             except Exception as ex:
3464:                 messagebox.showerror("Error", str(ex))
3465:         def delete_user():
3466:             a=tr.selection()
3467:             if not a:
3468:                 messagebox.showwarning("Delete User","Select a user row first."); return
3469:             username=tr.item(a[0])["values"][0]
3470:             if username==self.current_user:
3471:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3472:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3473:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3468:                 messagebox.showwarning("Delete User","Select a user row first."); return
3469:             username=tr.item(a[0])["values"][0]
3470:             if username==self.current_user:
3471:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3472:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3473:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3474:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3475:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3476:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3477:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3478:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3479:         load()
3480: 
3481:     @staticmethod
3482:     def _renumber_tree(tree, rows):
3483:         for i,iid in enumerate(tree.get_children()):
3484:             vals=list(tree.item(iid,"values"));
3485:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3486: 
3487:     def demand(self):
3488:         self.clearbody(); self.demand_lines=[]
```
```text
3485:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3486: 
3487:     def demand(self):
3488:         self.clearbody(); self.demand_lines=[]
3489:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3490:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3491:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3492:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3493:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3494:         # Demand Date is intentionally displayed as its own dedicated field.
3495:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3496:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3497:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3498:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3499:                 ("special","Special Instructions"),("source","Recommended Source")]
3500:         for i,(k,n) in enumerate(fields):
3501:             r=i//4*2+3; c=i%4*2
3502:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3503:             if k=="dept":
3504:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3505:             elif k=="urgency":
```
```text
3575:         def new_form():
3576:             self._editing_document_key=None
3577:             for z in v.values(): z.set("")
3578:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3579:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3580:             for iid in tree.get_children(): tree.delete(iid)
3581:             self._set_form_editable(form_roots, True, skip=[selector])
3582: 
3583:         def save():
3584:             try:
3585:                 no=v["no"].get().strip()
3586:                 if not no: raise ValueError("Demand No is required.")
3587:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3588:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3589:                 if dup and getattr(self,"_editing_document_key",None) != no:
3590:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3591:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3592:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3593:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3594:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3595:                 self.conn.commit(); backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector]); messagebox.showinfo("Saved",f"Demand {no} saved successfully.")
```
```text
3595:                 self.conn.commit(); backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector]); messagebox.showinfo("Saved",f"Demand {no} saved successfully.")
3596:             except Exception as ex: messagebox.showerror("Error",str(ex))
3597:         form_roots=[f,line,editbar]
3598:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3599:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3600:         def delete_current():
3601:             no=v["no"].get().strip()
3602:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3603:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3604:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3605:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
3606:             self.demand(); messagebox.showinfo("Deleted",f"Demand {no} deleted.")
3607:         def cancel_form():
3608:             self._editing_document_key=None
3609:             self._set_form_editable(form_roots, False, skip=[selector])
3610:             for z in v.values(): z.set("")
3611:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3612:             itype.set("Local")
3613:             self.demand_lines.clear()
3614:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3615:             for iid in tree.get_children(): tree.delete(iid)
```
```text
3618:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3619:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3620:                     f"Justification: {v['just'].get()}",
3621:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3622:             if not self.demand_lines:
3623:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3624:             self.show_preview_window("Purchase Demand", header,
3625:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3626:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3627:         def edit_saved_demand():
3628:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3629:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3630:             self._set_form_editable(form_roots, True, skip=[selector])
3631:         def print_now():
3632:             if not self.demand_lines:
3633:                 messagebox.showwarning("Print","Add at least one item line first."); return
3634:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3635:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3636:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3637:                     f"Justification: {v['just'].get()}",
3638:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3634:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3635:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3636:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3637:                     f"Justification: {v['just'].get()}",
3638:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3639:             self._open_direct_printer("Purchase Demand",header,
3640:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3641:                 self.demand_lines,A4)
3642:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3643:         self._add_transaction_new_button(new_form)
3644:         self._set_form_editable(form_roots, False, skip=[selector])
3645:         try:
3646:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3647:         except Exception: pass
3648:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3649: 
3650:     def load_demand_into_form(self,no,v,tree):
3651:         v["no"].set(no)
3652:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3653:         if not r:return
3654:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3656:         self.demand_lines=[]
3657:         for i in tree.get_children():tree.delete(i)
3658:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3659:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3660:         roots=getattr(self,"_transaction_form_roots",None)
3661:         if roots and "demand" in roots:
3662:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3663: 
3664:     def refresh_saved_cache(self,typ):
3665:         # Refresh saved-document dropdowns immediately after a successful save.
3666:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3667:         alive=[]
3668:         for combo, refresh in refreshers:
3669:             try:
3670:                 if combo.winfo_exists():
3671:                     refresh()
3672:                     alive.append((combo, refresh))
3673:             except Exception:
3674:                 pass
3675:         if hasattr(self, "_document_selector_refreshers"):
3676:             self._document_selector_refreshers[typ] = alive
```
```text
3675:         if hasattr(self, "_document_selector_refreshers"):
3676:             self._document_selector_refreshers[typ] = alive
3677: 
3678:     def grr(self):
3679:         self.clearbody(); self.grr_lines=[]
3680:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3681:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3682:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3683:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3684:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3685:         for i,(k,n) in enumerate(fields):
3686:             r=i//4*2+2;c=i%4*2
3687:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3688:             if k=="department":
3689:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3690:             elif k=="supplier":
3691:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3692:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3693:             elif k=="date":
3694:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3695:             else:
```
```text
3744:         def new_form():
3745:             self._editing_document_key=None
3746:             for z in v.values(): z.set("")
3747:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3748:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3749:             for iid in tree.get_children(): tree.delete(iid)
3750:             self._set_form_editable(form_roots, True, skip=[selector])
3751: 
3752:         def save():
3753:             try:
3754:                 no=v["no"].get().strip()
3755:                 if not no:raise ValueError("GRN No is required.")
3756:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3757:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3758:                 if dup and getattr(self,"_editing_document_key",None) != no:
3759:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3760:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3761:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3762:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3763:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3764:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3761:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3762:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3763:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3764:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3765:                 for x in self.grr_lines:
3766:                     ltype=x[10] if len(x)>10 else "Local"
3767:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3768:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3769:                 self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("grr");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock.")
3770:             except Exception as ex:messagebox.showerror("Error",str(ex))
3771:         form_roots=[f,line,editbar]
3772:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3773:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3774:         def delete_current():
3775:             no=v["no"].get().strip()
3776:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3777:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3778:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3779:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3780:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3781:         def cancel_form():
```
```text
3800:                     ("Challan #", v['challan'].get()),
3801:                     ("Vehicle #", v['vehicle'].get()),
3802:                     ("Bill/Voucher #", v['bill'].get()),
3803:                     ("Reference", v['ref'].get()),
3804:                     ("Remarks", v['remarks'].get()),
3805:                     ("Total Value", fmt_num(total))]
3806:             self.show_preview_window("GRN Receipt", header,
3807:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3808:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3809:         def portable_current():
3810:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3811:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3812:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3813:         self._portable_print_context=portable_current
3814:         def edit_saved_grr():
3815:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3816:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
3817:             self._set_form_editable(form_roots, True, skip=[selector])
3818:         def print_now():
3819:             if not self.grr_lines:
3820:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
3824:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
3825:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
3826:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
3827:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
3828:                     ("Total Value", fmt_num(total))]
3829:             self._open_direct_printer("GRN Receipt",header,
3830:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3831:                 self.grr_lines,landscape(A4))
3832:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3833:         self._add_transaction_new_button(new_form)
3834:         self._set_form_editable(form_roots, False, skip=[selector])
3835:         try:
3836:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3837:         except Exception: pass
3838:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
3839: 
3840:     def load_grr_into_form(self,no,v,tree):
3841:         v["no"].set(no)
3842:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
3843:         if not r:return
3844:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
3851:         if roots and "grr" in roots:
3852:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
3853: 
3854:     def issue(self):
3855:         self.clearbody(); self.issue_lines=[]
3856:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
3857:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
3858:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3859:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
3860:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
3861:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
3862:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3863:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3864:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
3865:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
3866:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
3867:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
3868:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
3869:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
3870:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
3871:         itype=tk.StringVar(value="Local")
```
```text
3940:                 # Editing an existing issue replaces its old stock transaction and detail lines.
3941:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
3942:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
3943:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
3944:                 for x in self.issue_lines:
3945:                     ltype=x[7] if len(x)>7 else "Local"
3946:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
3947:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
3948:                 self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("issue");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock.")
3949:             except Exception as ex:messagebox.showerror("Error",str(ex))
3950:         def delete_current():
3951:             no=v["no"].get().strip()
3952:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
3953:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
3954:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
3955:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
3956:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
3957:         def cancel_form():
3958:             self._editing_document_key=None
3959:             self._set_form_editable(form_roots, False, skip=[selector])
3960:             for z in v.values(): z.set("")
```
```text
3965:             for iid in tree.get_children(): tree.delete(iid)
3966:         def preview_now():
3967:             if not self.issue_lines:
3968:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3969:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3970:                     f"Items Use For: {v['items_use_for'].get()}"]
3971:             self.show_preview_window("Material Issue", header,
3972:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
3973:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
3974:         def portable_current():
3975:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
3976:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
3977:         self._portable_print_context=portable_current
3978:         form_roots=[f,usebar,line,editbar]
3979:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3980:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
3981:         def load_saved_issue(no):
3982:             self.load_issue_into_form(no,v,tree)
3983:             self._set_form_editable(form_roots, False, skip=[selector])
3984:         def edit_saved_issue():
3985:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
3978:         form_roots=[f,usebar,line,editbar]
3979:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3980:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
3981:         def load_saved_issue(no):
3982:             self.load_issue_into_form(no,v,tree)
3983:             self._set_form_editable(form_roots, False, skip=[selector])
3984:         def edit_saved_issue():
3985:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3986:             self._edit_from_selector("issue", v["no"], load_saved_issue)
3987:             self._set_form_editable(form_roots, True, skip=[selector])
3988:         def print_issue_now():
3989:             if not self.issue_lines:
3990:                 messagebox.showwarning("Print","Add at least one item line first."); return
3991:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
3992:             self._open_direct_printer("Material Issue",header,
3993:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
3994:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
3995:         self._add_transaction_new_button(new_form)
3996:         self._set_form_editable(form_roots, False, skip=[selector])
3997:         self._active_form_loader = load_saved_issue
3998: 
```
```text
4006:         for i in tree.get_children():tree.delete(i)
4007:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4008:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4009:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4010:         roots=getattr(self,"_transaction_form_roots",None)
4011:         if roots and "issue" in roots:
4012:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4013: 
4014:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4015:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4016: 
4017:         The layout intentionally matches Inventory Codes' Selection Criteria
4018:         popup so all Report sub-sections have one consistent desktop workflow.
4019:         """
4020:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4021:         win=tk.Toplevel(self)
4022:         win.title(f"{report_title} - Selection Criteria")
4023:         win.resizable(False,False)
4024:         win.transient(self); win.grab_set()
4025:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4026:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4071:             except Exception: pass
4072:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4073:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4074:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4075:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4076:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4077:         e1.focus_set(); self.wait_window(win); return result
4078: 
4079:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4080:         self._pending_report_filters=criteria
4081:         try:
4082:             return self.open_menu_window(method,title,geometry)
4083:         finally:
4084:             self._pending_report_filters=None
4085: 
4086:     def open_stock_balance_report_flow(self):
4087:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4088:         if f.get("cancelled"): return None
4089:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4090: 
4091:     def open_grr_report_flow(self):
```
```text
4084:             self._pending_report_filters=None
4085: 
4086:     def open_stock_balance_report_flow(self):
4087:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4088:         if f.get("cancelled"): return None
4089:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4090: 
4091:     def open_grr_report_flow(self):
4092:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4093:         if f.get("cancelled"): return None
4094:         return self._open_report_child(self.report_grr,"GRN Report",f)
4095: 
4096:     def open_demand_report_flow(self):
4097:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4098:         if f.get("cancelled"): return None
4099:         return self._open_report_child(self.report_demand,"Demand Report",f)
4100: 
4101:     def open_issue_report_flow(self):
4102:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4103:         if f.get("cancelled"): return None
4104:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4098:         if f.get("cancelled"): return None
4099:         return self._open_report_child(self.report_demand,"Demand Report",f)
4100: 
4101:     def open_issue_report_flow(self):
4102:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4103:         if f.get("cancelled"): return None
4104:         return self._open_report_child(self.report_issue,"Issue Report",f)
4105: 
4106:     def open_party_report_flow(self):
4107:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4108:         if f.get("cancelled"): return None
4109:         return self._open_report_child(self.report_party,"Party Report",f)
4110: 
4111:     def _ask_stock_balance_filters(self):
4112:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4113:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4114:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4115:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4116:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4117:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4118:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4130:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4131:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4132:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4133:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4134:         e1.focus_set();self.wait_window(win);return result
4135: 
4136:     def stock_balance(self):
4137:         self.clearbody()
4138:         # Stock Balance is a Report sub-section and does not use the generic
4139:         # Save/Edit/Delete/Cancel/Print action strip.
4140:         children=self.body.winfo_children()
4141:         if children:
4142:             children[0].destroy()
4143:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4144:         if initial.get("cancelled"):
4145:             self.dashboard(); return
4146:         top=ttk.Frame(self.body);top.pack(fill="x")
4147:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4148:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4149:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4150:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4160:             for typ,qty in self.conn.execute(q,params):
4161:                 if typ=="GRR":gr+=float(qty or 0)
4162:                 elif typ=="ISSUE":iss+=float(qty or 0)
4163:             return opening_before,gr,iss,opening_before+gr-iss
4164:         def header_summary():
4165:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4166:         def load():
4167:             for i in tr.get_children():tr.delete(i)
4168:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4169:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4170:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4171:             sql+=" ORDER BY code"
4172:             for r in self.conn.execute(sql,params):
4173:                 op,gr,iss,cur=period(r[0],r[3])
4174:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4175:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4176:         def reopen_filters():
4177:             initial2=self._ask_stock_balance_filters()
4178:             if initial2.get("cancelled"):return
4179:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4180:             load()
```
```text
4218:         """
4219:         if typ=="demand": self.demand()
4220:         elif typ=="grr": self.grr()
4221:         else: self.issue()
4222:         loader=getattr(self,"_active_form_loader",None)
4223:         if loader: loader(str(no))
4224: 
4225:     def _edit_from_selector(self, typ, var, loader):
4226:         """Top Edit action: load the saved document directly into the current form.
4227:         If nothing is selected, use the newest saved document; never open a popup.
4228:         """
4229:         text=var.get().strip()
4230:         if text:
4231:             no=text.split(" -> ",1)[0].strip()
4232:         else:
4233:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4234:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4235:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4236:             if not r:
4237:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4238:                 return
```
```text
4235:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4236:             if not r:
4237:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4238:                 return
4239:             no=str(r[0])
4240:             var.set(no)
4241:         loader(no)
4242: 
4243:     def show_saved_records(self,typ):
4244:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4245:         if typ=="demand":
4246:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4247:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4248:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4249:             for r in rows:
4250:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4251:                 r=list(r); r[1]=to_display_date(r[1])
4252:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4253:         elif typ=="grr":
4254:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4255:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4266:         def view():
4267:             a=tr.selection()
4268:             if not a:return
4269:             no=tr.item(a[0])["values"][0]
4270:             win.destroy();self.open_document_editor(typ,no)
4271:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4272:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4273:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4274:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4275: 
4276:     def documents(self):
4277:         self.clearbody()
4278:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4279:         specs=[
4280:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4281:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4282:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4283:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4284:             ("Material Issues","issue",("No","Date","Department"),
4285:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4286:         ]
```
```text
4282:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4283:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4284:             ("Material Issues","issue",("No","Date","Department"),
4285:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4286:         ]
4287:         for title,typ,cols,query in specs:
4288:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4289:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4290:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4291:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4292:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4293:             for r in self.conn.execute(query):
4294:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4295:             def edit_selected(t=tr,k=typ):
4296:                 a=t.selection()
4297:                 if not a:
4298:                     messagebox.showwarning("Edit", "Select a saved record first.")
4299:                     return
4300:                 no=t.item(a[0])["values"][0]
4301:                 self.open_document_editor(k,no)
4302:             def delete_selected(t=tr,k=typ):
```
```text
4297:                 if not a:
4298:                     messagebox.showwarning("Edit", "Select a saved record first.")
4299:                     return
4300:                 no=t.item(a[0])["values"][0]
4301:                 self.open_document_editor(k,no)
4302:             def delete_selected(t=tr,k=typ):
4303:                 a=t.selection()
4304:                 if not a:
4305:                     messagebox.showwarning("Delete", "Select a saved record first.")
4306:                     return
4307:                 no=t.item(a[0])["values"][0]
4308:                 if k=="demand":
4309:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4310:                 elif k=="grr":
4311:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4312:                 else:
4313:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4314:                 self.conn.commit();backup_database();self.documents()
4315:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4316:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4317:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4311:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4312:                 else:
4313:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4314:                 self.conn.commit();backup_database();self.documents()
4315:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4316:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4317:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4318:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4319:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4320:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4321:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4322: 
4323:     def doc_export_selected(self,typ,tr,fmt):
4324:         a=tr.selection()
4325:         if not a:
4326:             messagebox.showwarning("Export","Select a saved record first."); return
4327:         no=tr.item(a[0])["values"][0]
4328:         if fmt=="word": self.export_word(typ,no)
4329:         else: self.export_excel(typ,no)
4330: 
4331:     def doc_preview_selected(self,typ,tr):
```
```text
4326:             messagebox.showwarning("Export","Select a saved record first."); return
4327:         no=tr.item(a[0])["values"][0]
4328:         if fmt=="word": self.export_word(typ,no)
4329:         else: self.export_excel(typ,no)
4330: 
4331:     def doc_preview_selected(self,typ,tr):
4332:         a=tr.selection()
4333:         if not a:
4334:             messagebox.showwarning("Preview","Select a saved record first."); return
4335:         no=tr.item(a[0])["values"][0]
4336:         data=self._get_doc_data(typ,no)
4337:         if not data:
4338:             messagebox.showwarning("Preview","Document not found."); return
4339:         title,header,cols,rows=data
4340:         header_lines=header
4341:         self.show_preview_window(title,header_lines,cols,rows)
4342: 
4343:     def doc_print_selected(self,typ,tr):
4344:         a=tr.selection()
4345:         if not a: return
4346:         no=tr.item(a[0])["values"][0]
```
```text
4377:         def _print_loaded_document():
4378:             data=self._get_doc_data(typ,no)
4379:             if not data:
4380:                 messagebox.showwarning("Document","Document not found."); return
4381:             title,header,cols,rows=data
4382:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4383:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4384: 
4385:     def _report_filter_popup(self, title, include_party=False):
4386:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4387:         win,winbody=self._internal_window(title,"520x420")
4388:         done=tk.BooleanVar(value=False)
4389:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4390:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4391:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4392:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4393:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4394:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4395:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4396:         if include_party:
4397:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4391:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4392:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4393:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4394:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4395:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4396:         if include_party:
4397:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4398:         def ok():
4399:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4400:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4401:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4402:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4403: 
4404:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4405:         self.clearbody()
4406:         # Report sub-sections use their own report toolbar; remove only the
4407:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4408:         children=self.body.winfo_children()
4409:         if children:
4410:             children[0].destroy()
4411:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4412:         if f.get("cancelled"):
4413:             self.dashboard();return
4414:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4415:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4416:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4417:         def load():
4418:             for i in tr.get_children():tr.delete(i)
4419:             params,where=params_builder(f)
4420:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4421:             for r in self.conn.execute(sql,params):
4422:                 vals=list(r)
4423:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4424:                 tr.insert("","end",values=vals)
4425:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4426:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4427:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4428:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4429:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4430:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4431:         def open_find_report():
4432:             state_find={"index":-1}
```
```text
4438:                 order=children[start:]+children[:start]
4439:                 for iid in order:
4440:                     vals=tr.item(iid,"values")
4441:                     if any(text in str(v).lower() for v in vals):
4442:                         state_find["index"]=children.index(iid)
4443:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4444:                 return False
4445:             self._open_exact_find_text_popup(search_fn)
4446:         self._item_master_find_callback=open_find_report
4447:         load()
4448:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4449: 
4450:     def report_grr(self):
4451:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4452:         def pb(f):
4453:             w=[];p=[]
4454:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4455:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4456:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4457:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4458:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4453:             w=[];p=[]
4454:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4455:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4456:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4457:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4458:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4459:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4460:             return p,w
4461:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4462: 
4463:     def report_demand(self):
4464:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4465:         def pb(f):
4466:             w=[];p=[]
4467:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4468:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4469:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4470:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4471:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4472:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4473:             return p,w
```
```text
4466:             w=[];p=[]
4467:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4468:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4469:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4470:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4471:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4472:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4473:             return p,w
4474:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4475: 
4476:     def report_issue(self):
4477:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4478:         def pb(f):
4479:             w=[];p=[]
4480:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4481:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4482:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4483:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4484:             return p,w
4485:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4486: 
```
```text
4479:             w=[];p=[]
4480:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4481:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4482:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4483:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4484:             return p,w
4485:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4486: 
4487:     def report_party(self):
4488:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4489:         def pb(f):
4490:             w=[];p=[]
4491:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4492:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4493:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4494:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4495:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4496:             return p,w
4497:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4498: 
4499:     def reports(self):
```
```text
4497:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4498: 
4499:     def reports(self):
4500:         self.clearbody()
4501:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4502: 
4503:         # ================= GRN Details =================
4504:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4505:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4506:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4507:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4508:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4509:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4510: 
4511:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4512:         def load_grr_item(codev=None):
4513:             for i in tr.get_children(): tr.delete(i)
4514:             q=codev.get().strip() if codev else ""
4515:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4516:             for r in self.conn.execute(sql,(q,) if q else ()):
4517:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4523:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4524:         tr=self.make_tree(fr,grr_cols,grr_widths)
4525:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4526:             for i in tr.get_children(): tr.delete(i)
4527:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4528:             conds=[];params=[]
4529:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4530:             if td: conds.append("g.grr_date<=?");params.append(td)
4531:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4532:             for r in self.conn.execute(sql,params):
4533:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4534:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4535:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4536:         load_grr_date(fdv,tdv)
4537: 
4538:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4539:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4540:         party=tk.StringVar(value="ALL")
4541:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4542:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4543:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4539:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4540:         party=tk.StringVar(value="ALL")
4541:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4542:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4543:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4544:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4545:         def load_party(*_):
4546:             for i in tr.get_children(): tr.delete(i)
4547:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4548:             if party.get()=="ALL":
4549:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4550:             else:
4551:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4552:             for r in rows:
4553:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4554:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4555:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4556: 
4557:         # ================= Demand Details =================
4558:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4559:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4555:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4556: 
4557:         # ================= Demand Details =================
4558:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4559:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4560:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4561:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4562:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4563:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4564: 
4565:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4566:         def load_dem_item(codev=None):
4567:             for i in tr.get_children(): tr.delete(i)
4568:             q=codev.get().strip() if codev else ""
4569:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4570:             for r in self.conn.execute(sql,(q,) if q else ()):
4571:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4572:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4573:         tr=self.make_tree(fr,dem_cols,dem_widths)
4574:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4575:         load_dem_item(codev)
```
```text
4577:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4578:         tr=self.make_tree(fr,dem_cols,dem_widths)
4579:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4580:             for i in tr.get_children(): tr.delete(i)
4581:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4582:             conds=[];params=[]
4583:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4584:             if td: conds.append("d.demand_date<=?");params.append(td)
4585:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4586:             for r in self.conn.execute(sql,params):
4587:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4588:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4589:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4590:         load_dem_date(fdv,tdv)
4591: 
4592:         # ================= Material Issue Details =================
4593:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4594:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4595:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4596:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4597:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4590:         load_dem_date(fdv,tdv)
4591: 
4592:         # ================= Material Issue Details =================
4593:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4594:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4595:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4596:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4597:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4598:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4599: 
4600:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4601:         def load_iss_item(codev=None):
4602:             for i in tr.get_children(): tr.delete(i)
4603:             q=codev.get().strip() if codev else ""
4604:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4605:             for r in self.conn.execute(sql,(q,) if q else ()):
4606:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4607:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4608:         tr=self.make_tree(fr,iss_cols,iss_widths)
4609:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4610:         load_iss_item(codev)
```
```text
4612:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4613:         tr=self.make_tree(fr,iss_cols,iss_widths)
4614:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4615:             for i in tr.get_children(): tr.delete(i)
4616:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4617:             conds=[];params=[]
4618:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4619:             if td: conds.append("i.issue_date<=?");params.append(td)
4620:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4621:             for r in self.conn.execute(sql,params):
4622:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4623:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4624:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4625:         load_iss_date(fdv,tdv)
4626: 
4627:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4628: 
4629:     def print_item_master(self):
4630:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4631:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4632: 
```
```text
4629:     def print_item_master(self):
4630:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4631:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4632: 
4633:     def print_party_master(self):
4634:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4635:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4636: 
4637:     def print_report(self,kind):
4638:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4639:         if kind=="grr":
4640:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4641:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4642:         elif kind=="demand":
4643:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4644:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4645:         elif kind=="issue":
4646:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4647:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4648:         else:
4649:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4650:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4651:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4652: 
4653:     def print_stock(self):
4654:         rows=[]
4655:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4656:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4657:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4658:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4659: 
4660:     def print_ledger(self):
4661:         rows=[]
4662:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4663:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4664:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4665:                 running += x[3] if x[1]=="GRR" else -x[3]
4666:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4667:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4668: 
4669:     def _get_doc_data(self, typ, no):
4670:         """Header + line items for one saved document, used by the on-screen
```
```text
4736:             sig=doc.add_table(rows=2,cols=3)
4737:             labels=["Prepared By","Store Keeper","Store Incharge"]
4738:             for i,label in enumerate(labels):
4739:                 sig.cell(0,i).text="____________________"
4740:                 sig.cell(1,i).text=label
4741:                 for para in sig.cell(1,i).paragraphs:
4742:                     for run in para.runs: run.bold=True
4743:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4744:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4745:         doc.save(path)
4746:         self.open_file(path)
4747: 
4748:     def export_excel(self, typ, no):
4749:         if not no or not no.strip():
4750:             return messagebox.showwarning("Excel Export","Select a document first.")
4751:         if not XLSX_AVAILABLE:
4752:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4753:         data=self._get_doc_data(typ,no)
4754:         if not data:
4755:             return messagebox.showwarning("Excel Export","Document not found.")
4756:         title,header,cols,rows=data
```
```text
4778:             for col in range(1,4):
4779:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4780:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4781:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4782:         for col_cells in ws.columns:
4783:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4784:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4785:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4786:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4787:         wb.save(path)
4788:         self.open_file(path)
4789: 
4790:     def preview_pdf(self,typ,no):
4791:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4792:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4793:         data=self._get_doc_data(typ,no)
4794:         if not data:return messagebox.showwarning("Document","Document not found.")
4795:         title,header,cols,rows=data
4796:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4797:         page_size = landscape(A4) if typ == "grr" else A4
4798:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4793:         data=self._get_doc_data(typ,no)
4794:         if not data:return messagebox.showwarning("Document","Document not found.")
4795:         title,header,cols,rows=data
4796:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4797:         page_size = landscape(A4) if typ == "grr" else A4
4798:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4799: 
4800:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4801:         """Open the print dialog with a real visual preview of the exact report.
4802: 
4803:         The report is rendered to a temporary PDF only in memory/on disk for the
4804:         duration of printing.  It is deleted after the print dialog closes, so
4805:         the Print button does not leave a PDF report behind.  Printing uses the
4806:         rendered report page itself rather than rebuilding rows as plain text;
4807:         this keeps the printed page identical to the application's report.
4808:         """
4809:         # Printing is always prepared as an A4 landscape page. This only affects
4810:         # the print path; the rest of the application's UI/report logic is unchanged.
4811:         page_size = landscape(A4)
4812:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
4813:             messagebox.showwarning(
```
```text
4815:                 "The print preview/printing components are not available.\n\n"
4816:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
4817:             )
4818:             return
4819:         if not rows and not columns:
4820:             messagebox.showwarning("Print", "There is no data to print.")
4821:             return
4822:         try:
4823:             os.makedirs(REPORTS_DIR, exist_ok=True)
4824:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
4825:             self._pdf_table_report(key,title,columns,rows,page_size,
4826:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
4827:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
4828:             self._select_windows_printer_for_pdf(key)
4829:         except Exception as e:
4830:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
4831: 
4832:     def _select_windows_printer_for_pdf(self, path):
4833:         """Print dialog with an actual page preview, printer selection and direct GDI output.
4834: 
4835:         The preview is rendered from the exact PDF produced by the application,
```
```text
4865:         job=getattr(self, "_print_jobs", {}).get(path)
4866:         if job:
4867:             title, header_lines, columns, rows, source_page_size = job
4868:         else:
4869:             title=os.path.splitext(os.path.basename(path))[0]
4870:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
4871: 
4872:         try:
4873:             doc=fitz.open(path)
4874:             total_pages=max(1,doc.page_count)
4875:         except Exception as e:
4876:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
4877:             return
4878: 
4879:         win=tk.Toplevel(self)
4880:         win.title("Printing from Win32 application - Print")
4881:         win.geometry("900x620")
4882:         win.minsize(850,580)
4883:         win.transient(self)
4884:         win.configure(bg="#f0f0f0")
4885: 
```
```text
4891:             pass
4892: 
4893:         outer=tk.Frame(win,bg="#f0f0f0")
4894:         outer.pack(fill="both",expand=True)
4895:         outer.columnconfigure(1,weight=1)
4896:         outer.rowconfigure(0,weight=1)
4897: 
4898:         # Left side mirrors the familiar system printer dialog: printers and
4899:         # print options. Right side contains the actual report page preview.
4900:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
4901:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
4902:         left.grid_propagate(False)
4903:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
4904:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
4905:         printer_list.pack(fill="x")
4906:         for pr in printers: printer_list.insert("end",pr)
4907:         try: printer_list.selection_set(printers.index(default_printer))
4908:         except Exception: printer_list.selection_set(0)
4909: 
4910:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
4911:         copies=tk.IntVar(value=1)
```
```text
4984:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
4985: 
4986:         bottom=tk.Frame(win,bg="#f0f0f0")
4987:         # `outer` already uses pack() in `win`; using grid() for another direct
4988:         # child of the same toplevel raises TclError. Keep the action bar in the
4989:         # same geometry-manager family so Print/Cancel are always visible.
4990:         bottom.pack(fill="x",padx=12,pady=(0,12))
4991:         bottom.columnconfigure(0,weight=1)
4992:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
4993:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
4994:         print_btn=ttk.Button(bottom,text="Print",width=12)
4995:         print_btn.grid(row=0,column=2,padx=(8,0))
4996: 
4997:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
4998: 
4999:         def parse_page_selection(total):
5000:             if pages_mode.get()=="All pages": return list(range(total))
5001:             raw=page_range.get().strip()
5002:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5003:             selected=[]
5004:             for part in raw.split(","):
```
```text
5001:             raw=page_range.get().strip()
5002:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5003:             selected=[]
5004:             for part in raw.split(","):
5005:                 part=part.strip()
5006:                 if "-" in part:
5007:                     a,b=part.split("-",1); a=int(a); b=int(b)
5008:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5009:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5010:                     selected.extend(range(a-1,b))
5011:                 else:
5012:                     n=int(part)
5013:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5014:                     selected.append(n-1)
5015:             return list(dict.fromkeys(selected))
5016: 
5017:         def selected_printer():
5018:             sel=printer_list.curselection()
5019:             return printer_list.get(sel[0]) if sel else printers[0]
5020: 
5021:         def print_rendered_pages():
```
```text
5114:                 finally:
5115:                     if hprinter is not None:
5116:                         try: win32print.ClosePrinter(hprinter)
5117:                         except Exception: pass
5118:                     if hdc:
5119:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5120:                         except Exception: pass
5121: 
5122:                 # Print the exact rendered PDF page through the printer DC.
5123:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5124:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5125:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5126:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5127: 
5128:                 for copy_no in range(count):
5129:                     dc.StartDoc(str(title)[:80])
5130:                     doc_ok=False
5131:                     try:
5132:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5133:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5134:                             dc.StartPage()
```
```text
5133:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5134:                             dc.StartPage()
5135:                             page_ok=False
5136:                             try:
5137:                                 cell_w=printable_w/float(cols_n)
5138:                                 cell_h=printable_h/float(rows_n)
5139:                                 for j,page_index in enumerate(batch):
5140:                                     page=doc.load_page(page_index)
5141:                                     pdf_w=max(1.0,float(page.rect.width))
5142:                                     pdf_h=max(1.0,float(page.rect.height))
5143:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5144:                                     fit=max(0.25,min(fit,8.0))
5145:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5146:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5147:                                     target_w=max(1,int(cell_w*0.96))
5148:                                     target_h=max(1,int(cell_h*0.96))
5149:                                     ratio=min(target_w/img.width,target_h/img.height)
5150:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5151:                                     if (nw,nh)!=(img.width,img.height):
5152:                                         img=img.resize((nw,nh),Image.LANCZOS)
5153:                                     dib=ImageWin.Dib(img)
```
```text
5173: 
5174:                 status.set("Print job sent successfully")
5175:                 win.update_idletasks()
5176:                 win.after(500,close)
5177:             except Exception as e:
5178:                 status.set("Print failed: "+str(e))
5179:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5180: 
5181:         def close():
5182:             try: doc.close()
5183:             except Exception: pass
5184:             try: win.destroy()
5185:             except Exception: pass
5186:             # Only the temporary PDF created by the Print button is removed.
5187:             # Existing report PDFs passed through the legacy print path are preserved.
5188:             try:
5189:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5190:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5191:             except Exception: pass
5192: 
5193:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5189:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5190:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5191:             except Exception: pass
5192: 
5193:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5194:         bottom.winfo_children()[1].configure(command=close)
5195:         print_btn.configure(command=print_rendered_pages)
5196:         win.protocol("WM_DELETE_WINDOW",close)
5197:         win.bind("<Escape>",lambda e:close())
5198:         win.grab_set()
5199:         # Keep the requested printer defaults visibly selected; no manual
5200:         # adjustment is required before pressing Print.
5201:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5202:         win.after(120,lambda:render_preview(0))
5203:         win.focus_force()
5204: 
5205:     def print_pdf(self,path):
5206:         """Open a printer-selection window for a generated PDF."""
5207:         path=os.path.abspath(path)
5208:         if not os.path.exists(path):
5209:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5205:     def print_pdf(self,path):
5206:         """Open a printer-selection window for a generated PDF."""
5207:         path=os.path.abspath(path)
5208:         if not os.path.exists(path):
5209:             messagebox.showwarning("Print", "The report file could not be found.")
5210:             return
5211: 
5212:         if sys.platform.startswith("win"):
5213:             self._select_windows_printer_for_pdf(path)
5214:             return
5215: 
5216:         try:
5217:             subprocess.run(["lp", path], check=True)
5218:         except Exception as e:
5219:             messagebox.showwarning(
5220:                 "Print",
5221:                 "The operating system could not start printing.\n\n"
5222:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5223:             )
5224: 
5225:     def open_file(self,path):
```
```text
5220:                 "Print",
5221:                 "The operating system could not start printing.\n\n"
5222:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5223:             )
5224: 
5225:     def open_file(self,path):
5226:         try:
5227:             if sys.platform.startswith("win"): os.startfile(path)
5228:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5229:             else: subprocess.Popen(["xdg-open",path])
5230:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5231: 
5232:     def print_demand(self,no):
5233:         data=self._get_doc_data("demand",no)
5234:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5235:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5236:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5237:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5238: 
5239:     def print_grr(self,no):
5240:         data=self._get_doc_data("grr",no)
```
```text
5234:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5235:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5236:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5237:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5238: 
5239:     def print_grr(self,no):
5240:         data=self._get_doc_data("grr",no)
5241:         if not data:return messagebox.showwarning("Document","GRN not found.")
5242:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5243:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5244:         # GRN has a wide item table. Generate the PDF itself in landscape so
5245:         # the printer dialog and printer driver receive a landscape document
5246:         # instead of a portrait page with rotated/cropped content.
5247:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5248: 
5249:     def print_issue(self,no):
5250:         data=self._get_doc_data("issue",no)
5251:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5252:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5253:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5254:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
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
