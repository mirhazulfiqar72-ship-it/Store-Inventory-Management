# Store Inventory source audit

Generated from `D:\a\Store-Inventory-Management\Store-Inventory-Management\source` after CI patches.

## firebase_sync.py

- Lines: 373
- Functions: _safe_json_value(24-27), _table_columns(28-29), snapshot_db(30-38), _row_key(39-43), _index_snapshot(44-48), merge_local_changes(49-70), _snapshot_has_records(71-73), __init__(75-91), _read_url(92-102), status_text(103-108), _request(109-118), _get_meta(119-125), _get_snapshot(126-132), _load_json(133-141), _atomic_save_json(142-156), _save_state(157-161), _save_pending(162-166), _clear_pending(167-172), _get_lock_etag(173-182), _try_acquire_lock(183-189), _release_lock(190-198), initialize(199-254), replace_local(255-272), _write_remote(273-294), push_changes(295-314), maybe_pull(315-336), __init__(338-343), execute(344-352), executemany(353-357), commit(358-363), rollback(364-367), close(368-369), backup(370-371), __getattr__(372-373)

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
0073:     return any(tables.get(x, {}).get("rows") for x in ("demands", "demand_lines", "grr", "grr_lines", "issues", "issue_lines", "transactions", "parties", "mto_items"))
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
0184:         value, etag = self._get_lock_etag()
0185:         if value not in (None, ""):
0186:             return False
0187:         url = f"{self.base_url}/store_inventory/_lock.json"
```
```text
0191:         try:
0192:             value, etag = self._get_lock_etag()
0193:             if value != token:
0194:                 return
0195:             url = f"{self.base_url}/store_inventory/_lock.json"
0196:             self.session.put(url, data="null", headers={"if-match": etag, "content-type": "application/json"}, timeout=self.timeout)
0197:         except Exception:
0198:             pass
0199:     def initialize(self, conn: sqlite3.Connection) -> None:
0200:         if not self.enabled:
0201:             return
0202:         local = snapshot_db(conn)
0203:         pending = self._load_json(self.pending_path)
0204:         state = self._load_json(self.state_path)
0205:         if isinstance(pending, dict) and isinstance(pending.get("snapshot"), dict):
0206:             local = pending["snapshot"]
0207:             self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
0208:         elif state:
0209:             self.pending_base = state
0210:         try:
0211:             remote = self._get_snapshot()
```
```text
0212:             version, _ = self._get_meta()
0213:             if remote and remote.get("tables"):
0214:                 if self.pending_base is not None:
0215:                     merged = merge_local_changes(remote, self.pending_base, local)
0216:                     if merged != remote:
0217:                         new_version = self._write_remote(merged)
0218:                         self.replace_local(conn, merged)
0219:                         self.last_remote_version = new_version
0220:                         self._save_state(merged)
0221:                         self._clear_pending()
0222:                     else:
0223:                         self.replace_local(conn, remote)
0224:                         self.last_remote_version = version
0225:                         self._save_state(remote)
0226:                         self._clear_pending()
0227:                 elif _snapshot_has_records(local):
0228:                     empty = {"schema": 1, "tables": {}}
0229:                     merged = merge_local_changes(remote, empty, local)
0230:                     if merged != remote:
0231:                         new_version = self._write_remote(merged)
0232:                         self.replace_local(conn, merged)
```
```text
0226:                         self._clear_pending()
0227:                 elif _snapshot_has_records(local):
0228:                     empty = {"schema": 1, "tables": {}}
0229:                     merged = merge_local_changes(remote, empty, local)
0230:                     if merged != remote:
0231:                         new_version = self._write_remote(merged)
0232:                         self.replace_local(conn, merged)
0233:                         self.last_remote_version = new_version
0234:                         self._save_state(merged)
0235:                     else:
0236:                         self.replace_local(conn, remote)
0237:                         self.last_remote_version = version
0238:                         self._save_state(remote)
0239:                 else:
0240:                     self.replace_local(conn, remote)
0241:                     self.last_remote_version = version
0242:                     self._save_state(remote)
0243:                 self.pending_base = None
0244:                 self.pending_error = None
0245:             else:
0246:                 new_version = self._write_remote(local)
```
```text
0240:                     self.replace_local(conn, remote)
0241:                     self.last_remote_version = version
0242:                     self._save_state(remote)
0243:                 self.pending_base = None
0244:                 self.pending_error = None
0245:             else:
0246:                 new_version = self._write_remote(local)
0247:                 self.last_remote_version = new_version
0248:                 self._save_state(local)
0249:                 self._clear_pending()
0250:                 self.pending_base = None
0251:                 self.pending_error = None
0252:         except Exception as exc:
0253:             self.pending_error = str(exc)
0254:             self._save_pending(local, self.pending_base or state or {"schema": 1, "tables": {}})
0255:     def replace_local(self, conn: sqlite3.Connection, snapshot: Dict[str, Any]) -> None:
0256:         old_isolation = conn.isolation_level
0257:         try:
0258:             conn.execute("BEGIN")
0259:             for table in TABLES:
0260:                 cols = _table_columns(conn, table)
```
```text
0259:             for table in TABLES:
0260:                 cols = _table_columns(conn, table)
0261:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0262:                 conn.execute(f"DELETE FROM {table}")
0263:                 if not rows:
0264:                     continue
0265:                 insert_cols = [c for c in cols if c in rows[0]]
0266:                 placeholders = ",".join("?" for _ in insert_cols)
0267:                 sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0268:                 for row in rows:
0269:                     conn.execute(sql, [row.get(c) for c in insert_cols])
0270:             conn.commit()
0271:         finally:
0272:             conn.isolation_level = old_isolation
0273:     def _write_remote(self, snapshot: Dict[str, Any]) -> str:
0274:         token = f"{self.client_id}-{uuid.uuid4().hex}"
0275:         acquired = False
0276:         last_exc = None
0277:         for _ in range(10):
0278:             try:
0279:                 if self._try_acquire_lock(token):
```
```text
0278:             try:
0279:                 if self._try_acquire_lock(token):
0280:                     acquired = True
0281:                     break
0282:             except Exception as exc:
0283:                 last_exc = exc
0284:             time.sleep(0.35)
0285:         if not acquired:
0286:             raise RuntimeError(f"Could not acquire Firebase sync lock. {last_exc or ''}".strip())
0287:         try:
0288:             new_version = f"{time.time_ns()}-{self.client_id}"
0289:             self._request("PUT", "store_inventory/data.json", json=snapshot)
0290:             self._request("PUT", "store_inventory/_meta/version.json", json=new_version)
0291:             self._request("PUT", "store_inventory/_meta/updated_by.json", json=self.client_id)
0292:             return new_version
0293:         finally:
0294:             self._release_lock(token)
0295:     def push_changes(self, conn: sqlite3.Connection, baseline: Dict[str, Any]) -> bool:
0296:         if not self.enabled:
0297:             return True
0298:         local = snapshot_db(conn)
```
```text
0299:         try:
0300:             remote = self._get_snapshot() or {"schema": 1, "tables": {}}
0301:             merged = merge_local_changes(remote, baseline or {"schema": 1, "tables": {}}, local)
0302:             new_version = self._write_remote(merged)
0303:             self.replace_local(conn, merged)
0304:             self.last_remote_version = new_version
0305:             self.pending_base = None
0306:             self.pending_error = None
0307:             self._save_state(merged)
0308:             self._clear_pending()
0309:             return True
0310:         except Exception as exc:
0311:             self.pending_base = deepcopy(baseline)
0312:             self.pending_error = str(exc)
0313:             self._save_pending(local, baseline or {"schema": 1, "tables": {}})
0314:             return False
0315:     def maybe_pull(self, conn: sqlite3.Connection) -> bool:
0316:         if not self.enabled or self.pending_base is not None:
0317:             return False
0318:         now = time.monotonic()
0319:         if now - self.last_check < self.check_interval:
```
```text
0323:             version, _ = self._get_meta()
0324:             if not version or version == self.last_remote_version:
0325:                 return False
0326:             snapshot = self._get_snapshot()
0327:             if snapshot is None:
0328:                 return False
0329:             self.replace_local(conn, snapshot)
0330:             self.last_remote_version = version
0331:             self._save_state(snapshot)
0332:             self.pending_error = None
0333:             return True
0334:         except Exception as exc:
0335:             self.pending_error = str(exc)
0336:             return False
0337: class OnlineConnection:
0338:     def __init__(self, db_path: str, sync: FirebaseSync):
0339:         self._conn = sqlite3.connect(db_path, timeout=20)
0340:         self._conn.execute("PRAGMA busy_timeout=20000")
0341:         self.sync = sync
0342:         self._dirty = False
0343:         self._baseline: Optional[Dict[str, Any]] = None
```
```text
0336:             return False
0337: class OnlineConnection:
0338:     def __init__(self, db_path: str, sync: FirebaseSync):
0339:         self._conn = sqlite3.connect(db_path, timeout=20)
0340:         self._conn.execute("PRAGMA busy_timeout=20000")
0341:         self.sync = sync
0342:         self._dirty = False
0343:         self._baseline: Optional[Dict[str, Any]] = None
0344:     def execute(self, sql: str, params: Iterable[Any] = ()):
0345:         s = sql.lstrip().upper()
0346:         is_read = s.startswith("SELECT") or s.startswith("PRAGMA") or s.startswith("WITH") or s.startswith("EXPLAIN")
0347:         if is_read and not self._dirty and self._baseline is None:
0348:             self.sync.maybe_pull(self._conn)
0349:         elif not is_read and not self._dirty:
0350:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0351:             self._dirty = True
0352:         return self._conn.execute(sql, params)
0353:     def executemany(self, sql: str, seq_of_params):
0354:         if not self._dirty:
0355:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0356:             self._dirty = True
```
```text
0349:         elif not is_read and not self._dirty:
0350:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0351:             self._dirty = True
0352:         return self._conn.execute(sql, params)
0353:     def executemany(self, sql: str, seq_of_params):
0354:         if not self._dirty:
0355:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0356:             self._dirty = True
0357:         return self._conn.executemany(sql, seq_of_params)
0358:     def commit(self):
0359:         self._conn.commit()
0360:         if self._dirty:
0361:             self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
0362:         self._dirty = False
0363:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0364:     def rollback(self):
0365:         self._conn.rollback()
0366:         self._dirty = False
0367:         self._baseline = None
0368:     def close(self):
0369:         self._conn.close()
```
```text
0362:         self._dirty = False
0363:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0364:     def rollback(self):
0365:         self._conn.rollback()
0366:         self._dirty = False
0367:         self._baseline = None
0368:     def close(self):
0369:         self._conn.close()
0370:     def backup(self, target):
0371:         return self._conn.backup(target)
0372:     def __getattr__(self, name):
0373:         return getattr(self._conn, name)
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

- Lines: 5252
- Functions: resource_path(56-60), hash_password(123-128), verify_password(130-133), _copy_legacy_database_if_needed(135-152), _init_schema(155-243), connect(246-267), migrate_old_item_codes(269-283), seed_items(285-292), backup_database(294-323), restore_database(325-342), stock(344-349), fmt_num(351-353), to_iso_date(355-364), to_display_date(366-374), fiscal_year_key(376-387), fiscal_year_range(389-392), normalize_code(394-402), format_code(404-413), attach_code_mask(415-441), set_digits(418-423), key(424-434), paste(436-439), bind_add_to_list(443-464), on_enter(446-457), __init__(468-485), _check_for_updates(487-492), _setup_style(494-530), _shade(533-538), on_close(540-545), redo_network_setup(547-563), backup_now(565-572), restore_backup(574-592), _ctrl_f(594-606), _open_exact_find_text_popup(608-653), do_find(629-638), close(639-646), _global_enter(655-667), wipe(669-670), login(672-701), do_login(687-698), change_password(703-753), save_password(725-747), logout(755-760), home(762-781), _ensure_mdi_host(783-804), _internal_window(806-890), normal_place(822-828), restore(829-836), maximize(837-843), minimize(844-859), close(860-883), open_inventory_codes_detail_flow(892-910), open_inventory_codes_with_filters(912-926), open_inventory_codes_report_window(928-1154), tbtn(946-951), balance_as_of(1008-1018), build_nav(1020-1042), selected_prefix(1044-1053), load(1055-1087), page_move(1089-1090), page_first(1091-1091), page_last(1092-1096), on_nav(1100-1101), find_popup(1104-1123), search_fn(1106-1121), print_report(1126-1129), export_pdf(1131-1133), export_word(1134-1136), export_excel(1137-1139), open_menu_window(1156-1178), close_window(1166-1173), _manual_check_update(1180-1184), _show_current_version(1186-1190), build_menu_bar(1192-1239), open_calendar_picker(1241-1289), pick(1259-1261), redraw(1263-1275), nav(1277-1281), make_date_field(1291-1298), clearbody(1300-1326), run_action(1315-1320), _portable_print_current(1328-1339), portable_print_dialog(1341-1414), build_receipt(1368-1386), send(1387-1400), refresh_printers(1401-1407), preview_tree(1416-1428), set_page_actions(1430-1438), _add_transaction_new_button(1440-1457), _report_header(1459-1523), _report_footer(1525-1531), _grr_signature_block(1533-1549), _finish_page(1551-1552), _wrap_text_to_width(1554-1579), fits(1561-1561), _pdf_table_report(1581-1650), table_header(1603-1608), show_preview_window(1652-1725), _safe_report_name(1727-1730), print_preview_window(1732-1735), _fallback_pdf_export(1737-1770), esc(1741-1742), add(1745-1747), export_preview_pdf(1772-1804), export_preview_word(1806-1846), export_preview_excel(1848-1884), make_tree(1886-1895), pick_item(1897-1918), choose(1898-1917), ld(1905-1909), sel(1911-1915), bind_item_lookup(1920-1937), lookup(1922-1935), _set_form_editable(1940-1953), walk(1943-1952), document_selector(1955-1989), refresh(1960-1971), selected(1972-1977), dashboard(1991-2100), load_details(2073-2097), dashboard_details(2102-2106), item_history(2108-2128), _ask_item_master_filters(2130-2214), finish(2183-2195), items(2216-2454), hierarchy(2257-2266), selected_prefix(2312-2325), balance_as_of(2327-2334), load(2336-2374), set_page(2376-2377), select_node(2379-2400), open_find(2406-2425), search_fn(2408-2423), visible_rows(2430-2432), print_inventory(2433-2437), export_inventory_word(2438-2440), export_inventory_excel(2441-2443), portable_inventory(2448-2450), inventory_codes(2456-2738), btn(2492-2497), close_editor(2533-2543), edit_cell(2545-2571), commit(2563-2569), rows_query(2573-2586), load(2588-2603), new_record(2605-2626), commit(2619-2623), selected_row(2628-2630), edit_record(2632-2640), save_record(2642-2683), delete_record(2685-2696), refresh(2698-2698), do_print(2699-2701), do_close(2702-2702), filter_grid(2720-2727), open_mto_inventory_flow(2740-2763), open_code_opening_flow(2765-2773), code_opening(2775-2776), _open_code_opening_popup(2778-2779), _open_code_opening_detail(2781-3024), norm(2851-2852), table_for(2854-2855), row_for(2857-2862), search_any_destination(2864-2877), desc_hit(2879-2883), clear_form(2885-2898), load_for_edit(2900-2921), check_duplicates(2923-2934), save_code(2939-2990), edit_action(2992-2996), delete_code(2998-3013), _mto_new_item_dialog(3026-3062), save(3042-3059), _item_filter_bar(3064-3076), _date_filter_bar(3078-3086), _ask_mto_inventory_filters(3088-3133), finish(3118-3126), mto_inventory(3135-3335), open_find(3169-3188), search_fn(3171-3186), hierarchy(3207-3211), rebuild_nav(3213-3224), mto_balance(3248-3257), load(3259-3301), set_page(3303-3303), select_node(3304-3313), visible_rows(3318-3318), do_print(3319-3323), export_word(3324-3326), export_excel(3327-3329), party_master(3337-3388), load(3347-3350), clear(3351-3355), new_form(3356-3357), save(3358-3364), load_party_row(3365-3369), on_party_select(3370-3371), edit(3373-3377), delete_party(3378-3384), user_management(3390-3474), sync_role(3417-3422), load(3426-3429), clear(3430-3433), edit(3434-3441), save(3442-3459), delete_user(3460-3471), _renumber_tree(3477-3480), demand(3482-3643), _restore_demand_tree_columns(3525-3531), add(3534-3542), edit_item(3544-3556), delete_item(3558-3566), new_form(3570-3576), save(3578-3591), delete_current(3595-3601), cancel_form(3602-3610), preview_now(3611-3621), edit_saved_demand(3622-3625), print_now(3626-3636), load_demand_into_form(3645-3657), refresh_saved_cache(3659-3671), grr(3673-3833), add(3705-3713), edit_item(3715-3725), delete_item(3727-3735), new_form(3739-3745), save(3747-3765), delete_current(3769-3775), cancel_form(3776-3784), preview_now(3785-3803), portable_current(3804-3807), edit_saved_grr(3809-3812), print_now(3813-3826), load_grr_into_form(3835-3847), issue(3849-3992), old_issue_qty(3878-3881), update_balance(3882-3890), add(3892-3901), edit_item(3903-3914), new_form(3918-3924), post(3926-3944), delete_current(3945-3951), cancel_form(3952-3960), preview_now(3961-3968), portable_current(3969-3971), load_saved_issue(3976-3978), edit_saved_issue(3979-3982), print_issue_now(3983-3988), load_issue_into_form(3994-4007), _ask_report_criteria(4009-4072), finish(4058-4066), _open_report_child(4074-4079), open_stock_balance_report_flow(4081-4084), open_grr_report_flow(4086-4089), open_demand_report_flow(4091-4094), open_issue_report_flow(4096-4099), open_party_report_flow(4101-4104), _ask_stock_balance_filters(4106-4129), ok(4121-4122), cancel(4123-4123), stock_balance(4131-4194), period(4147-4158), header_summary(4159-4160), load(4161-4170), reopen_filters(4171-4175), open_find_stock(4179-4192), search_fn(4181-4191), ledger(4196-4208), open_document_editor(4210-4218), _edit_from_selector(4220-4236), show_saved_records(4238-4269), view(4261-4265), documents(4271-4316), edit_selected(4290-4296), delete_selected(4297-4309), doc_export_selected(4318-4324), doc_preview_selected(4326-4336), doc_print_selected(4338-4346), load_document(4348-4378), _print_loaded_document(4372-4377), _report_filter_popup(4380-4397), ok(4393-4394), cancel(4395-4395), _report_window(4399-4443), load(4412-4419), hdr(4420-4420), open_find_report(4426-4440), search_fn(4428-4439), report_grr(4445-4456), pb(4447-4455), report_demand(4458-4469), pb(4460-4468), report_issue(4471-4480), pb(4473-4479), report_party(4482-4492), pb(4484-4491), reports(4494-4622), load_grr_item(4507-4512), load_grr_date(4520-4528), load_party(4540-4548), load_dem_item(4561-4566), load_dem_date(4574-4582), load_iss_item(4596-4601), load_iss_date(4609-4617), print_item_master(4624-4626), print_party_master(4628-4630), print_report(4632-4646), print_stock(4648-4653), print_ledger(4655-4662), _get_doc_data(4664-4692), export_word(4694-4741), export_excel(4743-4783), preview_pdf(4785-4793), _open_direct_printer(4795-4825), _select_windows_printer_for_pdf(4827-5198), render_preview(4952-4971), on_resize(4973-4975), parse_page_selection(4994-5010), selected_printer(5012-5014), print_rendered_pages(5016-5174), close(5176-5186), print_pdf(5200-5218), open_file(5220-5225), print_demand(5227-5232), print_grr(5234-5242), print_issue(5244-5249)

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
0252: 
0253:     sync = FirebaseSync(FIREBASE_URL_FILE, INSTALL_DIR)
0254:     if sync.enabled:
0255:         try:
```
```text
0249:     _init_schema(raw)
0250:     seed_items(raw)
0251:     migrate_old_item_codes(raw)
0252: 
0253:     sync = FirebaseSync(FIREBASE_URL_FILE, INSTALL_DIR)
0254:     if sync.enabled:
0255:         try:
0256:             sync.initialize(raw)
0257:             # Firebase may contain an older snapshot whose items table does not
0258:             # yet have the MTO columns. Re-run the local schema migration after
0259:             # the remote snapshot is restored so Code Opening can always create
0260:             # and display MTO records.
0261:             _init_schema(raw)
0262:         except Exception as exc:
0263:             # Keep the application usable with its local cache when the
0264:             # internet/Firebase is temporarily unavailable. The next write or
0265:             # restart will retry sync.
0266:             sync.pending_error = str(exc)
0267:     return OnlineConnection(DB, sync)
0268: 
0269: def migrate_old_item_codes(c):
```
```text
0275:         new=format_code(digits)
0276:         if not new or new==old: continue
0277:         if c.execute("SELECT 1 FROM items WHERE code=?",(new,)).fetchone():
0278:             # Do not destroy an existing code; leave this collision visible for manual resolution.
0279:             continue
0280:         c.execute("UPDATE items SET code=? WHERE code=?",(new,old))
0281:         for table,col in (("demand_lines","code"),("grr_lines","code"),("issue_lines","code"),("transactions","code")):
0282:             c.execute(f"UPDATE {table} SET {col}=? WHERE {col}=?",(new,old))
0283:     c.commit()
0284: 
0285: def seed_items(c):
0286:     if c.execute("SELECT COUNT(*) FROM items").fetchone()[0]: return
0287:     if not os.path.exists(SEED): return
0288:     with open(SEED,encoding="utf-8-sig") as f:
0289:         for r in csv.DictReader(f):
0290:             c.execute("INSERT OR IGNORE INTO items(code,description,uom) VALUES(?,?,?)",
0291:                       (format_code(r.get("code","").strip()),r.get("description","").strip(),r.get("uom","").strip()))
0292:     c.commit()
0293: 
0294: def backup_database(manual=False):
0295:     """Create a safe, restorable full backup (a .db snapshot + a .zip copy)
```
```text
0288:     with open(SEED,encoding="utf-8-sig") as f:
0289:         for r in csv.DictReader(f):
0290:             c.execute("INSERT OR IGNORE INTO items(code,description,uom) VALUES(?,?,?)",
0291:                       (format_code(r.get("code","").strip()),r.get("description","").strip(),r.get("uom","").strip()))
0292:     c.commit()
0293: 
0294: def backup_database(manual=False):
0295:     """Create a safe, restorable full backup (a .db snapshot + a .zip copy)
0296:     in BACKUP_DIR. Runs automatically on every logout/exit, and can also be
0297:     triggered manually from the Backup Now button. Keeps the most recent
0298:     30 automatic backups plus every manual one, so disk space stays sane."""
0299:     try:
0300:         if not os.path.exists(DB): return None
0301:         stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
0302:         tag="manual" if manual else "auto"
0303:         latest=os.path.join(BACKUP_DIR,"inventory_backup_latest.db")
0304:         dated=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.db")
0305:         zpath=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.zip")
0306: 
0307:         src=sqlite3.connect(DB)
0308:         for path in (latest,dated):
```
```text
0302:         tag="manual" if manual else "auto"
0303:         latest=os.path.join(BACKUP_DIR,"inventory_backup_latest.db")
0304:         dated=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.db")
0305:         zpath=os.path.join(BACKUP_DIR,f"inventory_backup_{tag}_{stamp}.zip")
0306: 
0307:         src=sqlite3.connect(DB)
0308:         for path in (latest,dated):
0309:             if os.path.exists(path): os.remove(path)
0310:             dst=sqlite3.connect(path)
0311:             with dst:
0312:                 src.backup(dst)
0313:             dst.close()
0314:         src.close()
0315: 
0316:         with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
0317:             z.write(dated,"store_inventory.db")
0318: 
0319:         # Automatic backup rotation/deletion is intentionally disabled.
0320:         # Stored backups remain until the user explicitly deletes/restores them.
0321:         return zpath
0322:     except Exception:
```
```text
0317:             z.write(dated,"store_inventory.db")
0318: 
0319:         # Automatic backup rotation/deletion is intentionally disabled.
0320:         # Stored backups remain until the user explicitly deletes/restores them.
0321:         return zpath
0322:     except Exception:
0323:         return None
0324: 
0325: def restore_database(backup_path):
0326:     """Restore the database from a .db or .zip backup file. The current
0327:     database is itself backed up first, so a restore can never destroy data."""
0328:     try:
0329:         backup_database(manual=True)  # safety net before touching anything
0330:         if backup_path.lower().endswith(".zip"):
0331:             with zipfile.ZipFile(backup_path,"r") as z:
0332:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0333:                 os.makedirs(tmp_dir,exist_ok=True)
0334:                 z.extractall(tmp_dir)
0335:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0336:                 shutil.copy2(extracted,DB)
0337:                 shutil.rmtree(tmp_dir,ignore_errors=True)
```
```text
0331:             with zipfile.ZipFile(backup_path,"r") as z:
0332:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0333:                 os.makedirs(tmp_dir,exist_ok=True)
0334:                 z.extractall(tmp_dir)
0335:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0336:                 shutil.copy2(extracted,DB)
0337:                 shutil.rmtree(tmp_dir,ignore_errors=True)
0338:         else:
0339:             shutil.copy2(backup_path,DB)
0340:         return True
0341:     except Exception:
0342:         return False
0343: 
0344: def stock(c, code):
0345:     r=c.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()
0346:     q=float(r[0] or 0) if r else 0
0347:     for typ,qty in c.execute("SELECT doc_type,qty FROM transactions WHERE code=? ORDER BY id", (code,)):
0348:         q += float(qty or 0) if typ=="GRR" else -float(qty or 0) if typ=="ISSUE" else 0
0349:     return q
0350: 
0351: def fmt_num(x):
```
```text
0349:     return q
0350: 
0351: def fmt_num(x):
0352:     x=float(x or 0)
0353:     return f"{x:,.2f}".rstrip("0").rstrip(".")
0354: 
0355: def to_iso_date(s):
0356:     """Convert a user-entered DD/MM/YYYY date (or an already-ISO date) into
0357:     ISO YYYY-MM-DD for storage in the database and for date-range queries,
0358:     which rely on ISO strings sorting/comparing correctly."""
0359:     s=(s or "").strip()
0360:     if not s: return ""
0361:     for f in ("%d/%m/%Y","%Y-%m-%d"):
0362:         try: return datetime.strptime(s,f).strftime("%Y-%m-%d")
0363:         except Exception: continue
0364:     return s
0365: 
0366: def to_display_date(s):
0367:     """Convert an ISO YYYY-MM-DD date (as stored in the database) into the
0368:     DD/MM/YYYY format used everywhere on screen and on printed reports."""
0369:     s=(s or "").strip()
```
```text
0464:     return on_enter
0465: 
0466: 
0467: class App(tk.Tk):
0468:     def __init__(self):
0469:         super().__init__()
0470:         self.title("Store Inventory Management System | SAP Style")
0471:         self.geometry("1400x820"); self.minsize(1150,700)
0472:         self.conn=connect()
0473:         self.demand_lines=[]; self.grr_lines=[]; self.issue_lines=[]
0474:         self.current_user=None; self.current_role=None
0475:         self._item_master_search_entry=None
0476:         self._item_master_find_callback=None
0477:         self._portable_print_context=None
0478:         self.can_edit=False; self.can_delete=False; self.is_admin=False
0479:         self._setup_style()
0480:         # Any focused button can be activated with Enter.
0481:         self.bind_all("<Return>", self._global_enter, add="+")
0482:         self.bind_all("<KP_Enter>", self._global_enter, add="+")
0483:         self.bind_all("<Control-f>", self._ctrl_f, add="+")
0484:         self.protocol("WM_DELETE_WINDOW", self.on_close)
```
```text
0532:     @staticmethod
0533:     def _shade(hexcolor, factor):
0534:         """Return a slightly darker version of a #RRGGBB color (for hover/press states)."""
0535:         h=hexcolor.lstrip("#")
0536:         r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
0537:         r,g,b=(max(0,int(v*factor)) for v in (r,g,b))
0538:         return f"#{r:02x}{g:02x}{b:02x}"
0539: 
0540:     def on_close(self):
0541:         try:
0542:             self.conn.commit(); backup_database()
0543:         except Exception:
0544:             pass
0545:         self.destroy()
0546: 
0547:     def redo_network_setup(self):
0548:         if not messagebox.askyesno("Network Setup",
0549:             "This will clear the online database URL saved on this computer.\n\n"
0550:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0551:             "Continue?"):
0552:             return
```
```text
0546: 
0547:     def redo_network_setup(self):
0548:         if not messagebox.askyesno("Network Setup",
0549:             "This will clear the online database URL saved on this computer.\n\n"
0550:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0551:             "Continue?"):
0552:             return
0553:         try:
0554:             self.conn.commit(); backup_database()
0555:         except Exception:
0556:             pass
0557:         try:
0558:             if os.path.exists(FIREBASE_URL_FILE): os.remove(FIREBASE_URL_FILE)
0559:         except Exception:
0560:             pass
0561:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0562:         self.destroy()
0563:         sys.exit(0)
0564: 
0565:     def backup_now(self):
0566:         path=backup_database(manual=True)
```
```text
0560:             pass
0561:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0562:         self.destroy()
0563:         sys.exit(0)
0564: 
0565:     def backup_now(self):
0566:         path=backup_database(manual=True)
0567:         if path:
0568:             messagebox.showinfo("Backup Complete",
0569:                 f"A full backup was saved to:\n\n{path}\n\n"
0570:                 f"All backups are kept in:\n{BACKUP_DIR}")
0571:         else:
0572:             messagebox.showerror("Backup Failed","Could not create a backup. Make sure the database exists.")
0573: 
0574:     def restore_backup(self):
0575:         from tkinter import filedialog
0576:         if not messagebox.askyesno("Restore Backup",
0577:             "This will replace all current data with the selected backup.\n"
0578:             "A safety backup of the current data will be made first.\n\n"
0579:             "Continue?"):
0580:             return
```
```text
0574:     def restore_backup(self):
0575:         from tkinter import filedialog
0576:         if not messagebox.askyesno("Restore Backup",
0577:             "This will replace all current data with the selected backup.\n"
0578:             "A safety backup of the current data will be made first.\n\n"
0579:             "Continue?"):
0580:             return
0581:         path=filedialog.askopenfilename(
0582:             title="Select a backup file",
0583:             initialdir=BACKUP_DIR,
0584:             filetypes=[("Backup files","*.zip *.db"),("All files","*.*")])
0585:         if not path: return
0586:         if restore_database(path):
0587:             messagebox.showinfo("Restore Complete",
0588:                 "Data has been restored. The application will now restart.")
0589:             self.conn.close()
0590:             os.execv(sys.executable, [sys.executable]+sys.argv)
0591:         else:
0592:             messagebox.showerror("Restore Failed","Could not restore from that backup file.")
0593: 
0594:     def _ctrl_f(self, event=None):
```
```text
0631:             if not text:
0632:                 fe.focus_set(); return
0633:             try:
0634:                 found=search_fn(text)
0635:             except Exception:
0636:                 found=False
0637:             if found is False:
0638:                 messagebox.showinfo("Find Text","No matching text found.",parent=dlg)
0639:         def close():
0640:             try:
0641:                 dlg.grab_release()
0642:             except Exception: pass
0643:             try: dlg.destroy()
0644:             except Exception: pass
0645:             if getattr(self,"_exact_find_text_dialog",None) is dlg:
0646:                 self._exact_find_text_dialog=None
0647:         ttk.Button(box,text="Find Next",command=do_find,width=13).grid(row=0,column=3,padx=4,pady=4)
0648:         ttk.Button(box,text="Cancel",command=close,width=13).grid(row=1,column=3,padx=4,pady=4)
0649:         fe.bind("<Return>",lambda e:(do_find(),"break"))
0650:         dlg.bind("<Escape>",lambda e:close())
0651:         dlg.protocol("WM_DELETE_WINDOW",close)
```
```text
0717:         cur_ent=ttk.Entry(box,textvariable=current,width=28,show="*"); cur_ent.grid(row=2,column=1,pady=7)
0718:         ttk.Label(box,text="New Password").grid(row=3,column=0,sticky="w",pady=7)
0719:         new_ent=ttk.Entry(box,textvariable=new,width=28,show="*"); new_ent.grid(row=3,column=1,pady=7)
0720:         ttk.Label(box,text="Confirm New Password").grid(row=4,column=0,sticky="w",pady=7)
0721:         conf_ent=ttk.Entry(box,textvariable=confirm,width=28,show="*"); conf_ent.grid(row=4,column=1,pady=7)
0722:         err=ttk.Label(box,text="",foreground="#c0392b",wraplength=380,justify="left")
0723:         err.grid(row=5,column=0,columnspan=2,pady=(5,8))
0724: 
0725:         def save_password(event=None):
0726:             old_pw=current.get()
0727:             new_pw=new.get()
0728:             confirm_pw=confirm.get()
0729:             row=self.conn.execute("SELECT password FROM users WHERE username=?",(self.current_user,)).fetchone()
0730:             if not row or not verify_password(old_pw,row[0]):
0731:                 err.config(text="Current password is incorrect."); return
0732:             if len(new_pw) < 4:
0733:                 err.config(text="New password must be at least 4 characters."); return
0734:             if new_pw != confirm_pw:
0735:                 err.config(text="New password and confirmation do not match."); return
0736:             if new_pw == old_pw:
0737:                 err.config(text="New password must be different from the current password."); return
```
```text
0733:                 err.config(text="New password must be at least 4 characters."); return
0734:             if new_pw != confirm_pw:
0735:                 err.config(text="New password and confirmation do not match."); return
0736:             if new_pw == old_pw:
0737:                 err.config(text="New password must be different from the current password."); return
0738:             try:
0739:                 self.conn.execute("UPDATE users SET password=? WHERE username=?",
0740:                                   (hash_password(new_pw),self.current_user))
0741:                 self.conn.commit()
0742:                 backup_database()
0743:                 win.grab_release(); win.destroy()
0744:                 messagebox.showinfo("Password Changed",
0745:                     "Your password has been changed successfully.\n\nUse the new password the next time you log in.", parent=self)
0746:             except Exception as ex:
0747:                 err.config(text=f"Could not change password: {ex}")
0748: 
0749:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0750:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0751:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0752:         conf_ent.bind("<Return>",save_password)
0753:         cur_ent.focus_set()
```
```text
0749:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0750:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0751:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0752:         conf_ent.bind("<Return>",save_password)
0753:         cur_ent.focus_set()
0754: 
0755:     def logout(self):
0756:         try:
0757:             self.conn.commit(); backup_database()
0758:         except Exception:
0759:             pass
0760:         self.login()
0761: 
0762:     def home(self):
0763:         self.wipe()
0764:         self.build_menu_bar()
0765:         hdr=tk.Frame(self,bg=COLORS["primary_dark"]);hdr.pack(fill="x")
0766:         self._shell_header=hdr
0767:         inner=tk.Frame(hdr,bg=COLORS["primary_dark"],padx=16,pady=10);inner.pack(fill="x")
0768:         tk.Label(inner,text=COMPANY,font=("Segoe UI",16,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="left")
0769:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
```
```text
0769:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
0770:         tk.Label(inner,text=f"Data: {DATA_DIR}",font=("Segoe UI",8),bg=COLORS["primary_dark"],fg="#9FB8DA").pack(side="left",padx=14)
0771:         ttk.Button(inner,text="Logout",style="Danger.TButton",command=self.logout).pack(side="right")
0772:         tk.Label(inner,text=f"{self.current_user}  ({self.current_role})",font=("Segoe UI",9,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="right",padx=12)
0773:         nav=tk.Frame(self,bg=COLORS["primary"]);nav.pack(fill="x")
0774:         self._shell_nav=nav
0775:         navin=tk.Frame(nav,bg=COLORS["primary"],padx=10,pady=6);navin.pack(fill="x")
0776:         ttk.Button(navin,text="🏠  Dashboard",style="Accent.TButton",command=self.dashboard).pack(side="left",padx=3)
0777:         tk.Label(navin,text="Inventory  |  Transaction  |  Report  |  Edit  |  Help  —  see the menu bar above for every other section.",
0778:                  font=("Segoe UI",8),bg=COLORS["primary"],fg="#E7EFFB").pack(side="left",padx=14)
0779:         self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
0780:         self.main_body=self.body
0781:         self.dashboard()
0782: 
0783:     def _ensure_mdi_host(self):
0784:         """Create the in-app MDI workspace. Child windows never leave the main program."""
0785:         host=getattr(self,"_mdi_host",None)
0786:         if host is None or not host.winfo_exists():
0787:             host=tk.Frame(self.main_body,bg="#d9dde3",bd=0,highlightthickness=0)
0788:             self._mdi_host=host
0789:         host.place(relx=0,rely=0,relwidth=1,relheight=1)
```
```text
0852:             b.pack(side="left")
0853:             rb=tk.Button(item,text="□",font=("Segoe UI",8,"bold"),width=2,height=1,padx=0,pady=0,
0854:                          command=lambda:(restore(),maximize()),relief="flat",bd=0,bg="#e7e7e7")
0855:             rb.pack(side="left")
0856:             xb=tk.Button(item,text="×",font=("Segoe UI",9,"bold"),width=2,height=1,padx=0,pady=0,
0857:                          command=close,relief="flat",bd=0,bg="#e7e7e7")
0858:             xb.pack(side="left")
0859:             state["task"]=item
0860:         def close():
0861:             try:
0862:                 task=state.get("task")
0863:                 if task and task.winfo_exists(): task.destroy()
0864:             except Exception: pass
0865:             try:
0866:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
0867:             except Exception: pass
0868:             try: outer.destroy()
0869:             except Exception: pass
0870:             if not getattr(self,"_mdi_windows",[]):
0871:                 self._mdi_host.place_forget()
0872:                 # Restore the original application shell FIRST, then rebuild
```
```text
0916:             return None
0917:         self._inventory_codes_filter=criteria
0918:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0919:         try:
0920:             self.items(container=body)
0921:             win.lift()
0922:             return win
0923:         except Exception:
0924:             try: win._internal_close()
0925:             except Exception: pass
0926:             raise
0927: 
0928:     def open_inventory_codes_report_window(self, criteria=None):
0929:         """Open Inventory Codes as a real report-style child window.
0930: 
0931:         This intentionally mirrors the supplied Preview Report workflow: a
0932:         separate resizable/maximizable window with a left navigation tree,
0933:         compact report toolbar, Find dialog, and print/export commands.
0934:         The main application remains open behind it.
0935:         """
0936:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
0933:         compact report toolbar, Find dialog, and print/export commands.
0934:         The main application remains open behind it.
0935:         """
0936:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
0937:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
0938:         }
0939:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0940: 
0941:         # --- report-style toolbar ---
0942:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
0943:         toolbar.pack(fill="x",side="top")
0944:         toolbar.pack_propagate(False)
0945: 
0946:         def tbtn(text,cmd,width=9):
0947:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
0948:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
0949:                          padx=3,pady=1)
0950:             b.pack(side="left",padx=2,pady=6)
0951:             return b
0952: 
0953:         # --- main report body ---
```
```text
0964:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
0965:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
0966:         navscroll.config(command=code_tree.yview)
0967:         navscroll.pack(side="right",fill="y")
0968:         code_tree.pack(side="left",fill="both",expand=True)
0969: 
0970:         right=tk.Frame(content,bg="#EDEDED")
0971:         right.pack(side="left",fill="both",expand=True)
0972:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
0973:         reportbar.pack(fill="x")
0974:         reportbar.pack_propagate(False)
0975:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
0976:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
0977:         tab.pack(side="left",padx=4,pady=2)
0978:         titlevar=tk.StringVar(value="Inventory Summary")
0979:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
0980:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
0981: 
0982:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
0983:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
0984:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1118:                     vals=tree.item(iid,"values")
1119:                     if str(vals[1]).lower()==str(target).lower():
1120:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1121:                 return True
1122:             self._open_exact_find_text_popup(search_fn)
1123:             self._item_master_find_callback=find_popup
1124: 
1125: 
1126:         def print_report():
1127:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1128:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1129:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1130: 
1131:         def export_pdf():
1132:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1133:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1134:         def export_word():
1135:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1136:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1137:         def export_excel():
1138:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1134:         def export_word():
1135:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1136:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1137:         def export_excel():
1138:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1139:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1140: 
1141:         tbtn("Find",find_popup,7)
1142:         tbtn("Print",print_report,7)
1143:         tbtn("PDF",export_pdf,6)
1144:         tbtn("Word",export_word,6)
1145:         tbtn("Excel",export_excel,6)
1146:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1147:         tbtn("Refresh",load,8)
1148:         tbtn("Close",win._internal_close,7)
1149:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1150:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1151: 
1152:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1153:         build_nav(); load(); win.focus_force()
1154:         return win
```
```text
1164:         self.body=frame
1165:         closed={"done":False}
1166:         def close_window():
1167:             if closed["done"]: return
1168:             closed["done"]=True
1169:             if getattr(self,"body",None) is frame: self.body=old_body
1170:             self._page_actions=old_actions
1171:             self._item_master_find_callback=old_find
1172:             try: win._internal_close()
1173:             except Exception: win.destroy()
1174:         win._internal_close=close_window
1175:         try:
1176:             method(); self.update_idletasks(); win.lift(); return win
1177:         except Exception:
1178:             close_window(); raise
1179: 
1180:     def _manual_check_update(self):
1181:         try:
1182:             updater.check_for_update(self, manual=True)
1183:         except Exception as e:
1184:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1188:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1189:         except Exception as e:
1190:             messagebox.showerror("Current Version", str(e), parent=self)
1191: 
1192:     def build_menu_bar(self):
1193:         """Professional section / sub-section menu bar, ERP style:
1194:         Inventory > Item Master
1195:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1196:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1197:         Edit > Change Password, User Management
1198:         Help > Backup Now, Restore Backup, Network Setup
1199:         """
1200:         menubar=tk.Menu(self)
1201: 
1202:         m_inv=tk.Menu(menubar,tearoff=0)
1203:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1204:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1205:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1206:         menubar.add_cascade(label="Inventory",menu=m_inv)
1207: 
1208:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1208:         m_trans=tk.Menu(menubar,tearoff=0)
1209:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1210:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1211:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1212:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1213:         menubar.add_cascade(label="Transaction",menu=m_trans)
1214: 
1215:         m_rep=tk.Menu(menubar,tearoff=0)
1216:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1217:         m_rep.add_separator()
1218:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1219:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1220:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1221:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1222:         menubar.add_cascade(label="Report",menu=m_rep)
1223: 
1224:         m_edit=tk.Menu(menubar,tearoff=0)
1225:         m_edit.add_command(label="Change Password",command=self.change_password)
1226:         if self.is_admin:
1227:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1228:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1223: 
1224:         m_edit=tk.Menu(menubar,tearoff=0)
1225:         m_edit.add_command(label="Change Password",command=self.change_password)
1226:         if self.is_admin:
1227:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1228:         menubar.add_cascade(label="Edit",menu=m_edit)
1229: 
1230:         m_help=tk.Menu(menubar,tearoff=0)
1231:         m_help.add_command(label="Backup Now",command=self.backup_now)
1232:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1233:         m_help.add_command(label="Current Version",command=self._show_current_version)
1234:         if self.is_admin:
1235:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1236:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1237:         menubar.add_cascade(label="Help",menu=m_help)
1238: 
1239:         self.config(menu=menubar)
1240: 
1241:     def open_calendar_picker(self, var):
1242:         """Small month-grid calendar popup. Picking a day sets `var` to
1243:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1296:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1297:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1298:         return f
1299: 
1300:     def clearbody(self):
1301:         self._portable_print_context=None
1302:         for w in self.body.winfo_children(): w.destroy()
1303:         self._page_actions = {
1304:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1305:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1306:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1307:             "cancel": lambda: self.dashboard(),
1308:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1309:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1310:         }
1311:         # Single SAP-style toolbar at the very top.
1312:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1313:         self._page_action_bar=bar
1314:         self._page_action_first_button=None
1315:         def run_action(k):
1316:             if k=="edit" and not self.can_edit:
```
```text
1313:         self._page_action_bar=bar
1314:         self._page_action_first_button=None
1315:         def run_action(k):
1316:             if k=="edit" and not self.can_edit:
1317:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1318:             if k=="delete" and not self.can_delete:
1319:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1320:             self._page_actions[k]()
1321:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1322:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1323:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1324:             b.pack(side="left",padx=(0,2))
1325:             if self._page_action_first_button is None: self._page_action_first_button=b
1326:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1327: 
1328:     def _portable_print_current(self):
1329:         ctx=getattr(self,"_portable_print_context",None)
1330:         if not ctx:
1331:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1332:             return
1333:         try:
```
```text
1335:             if not data: return
1336:             title,header,columns,rows=data
1337:             self.portable_print_dialog(title,header,columns,rows)
1338:         except Exception as e:
1339:             messagebox.showerror("Portable Printer",str(e))
1340: 
1341:     def portable_print_dialog(self,title,header_lines,columns,rows):
1342:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1343:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1344:         if not WIN32PRINT_AVAILABLE:
1345:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1346:             return
1347:         try:
1348:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1349:         except Exception as e:
1350:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1351:             return
1352:         if not printers:
1353:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1354:             return
1355:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1405:                 if vals and pv.get() not in vals: pv.set(vals[0])
1406:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1407:             except Exception as ex: status.set(str(ex))
1408:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1409:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1410:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1411:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1412:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1413:         win.bind("<Escape>",lambda e:win._internal_close())
1414:         win.focus_force()
1415: 
1416:     def preview_tree(self, title, tree, header_lines=None):
1417:         """Preview the exact rows currently visible in a Treeview."""
1418:         cols=list(tree["columns"])
1419:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1420:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1421:         if not rows:
1422:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1423:             return
1424:         widths=[]
1425:         for c in cols:
```
```text
1422:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1423:             return
1424:         widths=[]
1425:         for c in cols:
1426:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1427:             except Exception: widths.append(100)
1428:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1429: 
1430:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1431:         self._page_actions.update({
1432:             "save": save or self._page_actions.get("save"),
1433:             "edit": edit or self._page_actions.get("edit"),
1434:             "delete": delete or self._page_actions.get("delete"),
1435:             "cancel": cancel or self._page_actions.get("cancel"),
1436:             "print": print or self._page_actions.get("print"),
1437:             "preview": preview or self._page_actions.get("preview"),
1438:         })
1439: 
1440:     def _add_transaction_new_button(self, command):
1441:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1442:         if bar is None or first is None: return
```
```text
1451:         sep.pack(side="left",fill="y",padx=4)
1452:         for w in existing:
1453:             try:
1454:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1455:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1456:                 else: w.pack(side="left")
1457:             except Exception: pass
1458: 
1459:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1460:         """Draw a consistent professional report header and return the first table Y.
1461: 
1462:         For GRN Receipt reports the document number is shown on the left and
1463:         the GRN Date is deliberately shown on the right in a bordered document
1464:         information panel.
1465:         """
1466:         W,H=page_size
1467:         if y_top is None: y_top=H-24
1468:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1469:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1470:         if os.path.exists(LOGO_FILE):
1471:             try:
```
```text
1464:         information panel.
1465:         """
1466:         W,H=page_size
1467:         if y_top is None: y_top=H-24
1468:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1469:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1470:         if os.path.exists(LOGO_FILE):
1471:             try:
1472:                 from reportlab.lib.utils import ImageReader
1473:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1474:             except Exception:
1475:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1476:         else:
1477:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1478:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1479:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1480:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1481:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1482: 
1483:         # Professional document information box.
1484:         info_top=logo_y-12
```
```text
1517:                 # naturally occupies the right-hand cell when supplied second.
1518:                 c.setFont("Helvetica-Bold",7)
1519:                 c.drawString(xx,yy,(label+":")[:28])
1520:                 c.setFont("Helvetica",7)
1521:                 c.drawString(xx+58,yy,val[:58])
1522:             return box_y-12
1523:         return info_top-6
1524: 
1525:     def _report_footer(self, c, page_no, page_size=A4):
1526:         W,H=page_size
1527:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1528:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1529:         c.drawString(24,13,REPORT_FOOTER)
1530:         c.drawRightString(W-24,13,f"Page {page_no}")
1531:         c.setFillColorRGB(0,0,0)
1532: 
1533:     def _grr_signature_block(self, c, y, page_size=A4):
1534:         """Draw the three requested transaction-document signature lines."""
1535:         W,H=page_size
1536:         labels=["Prepared By","Store Keeper","Store Incharge"]
1537:         block_h=70
```
```text
1544:             x=left+i*col_w
1545:             c.setLineWidth(0.6)
1546:             c.line(x+30,top-34,x+col_w-30,top-34)
1547:             c.setFont("Helvetica-Bold",7)
1548:             c.drawCentredString(x+col_w/2,top-48,label)
1549:         return True
1550: 
1551:     def _finish_page(self, c, page_no, page_size=A4):
1552:         self._report_footer(c,page_no,page_size); c.showPage()
1553: 
1554:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1555:         """Word-wrap `text` into a list of lines that each fit inside
1556:         max_width (points) at the given font, breaking mid-word only when a
1557:         single word is itself wider than the column."""
1558:         text=str(text) if text is not None else ""
1559:         if not text:
1560:             return [""]
1561:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1562:         lines=[]; cur=""
1563:         for word in text.split(" "):
1564:             trial=(cur+" "+word).strip() if cur else word
```
```text
1573:                     mid=(lo+hi)//2
1574:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1575:                     else: hi=mid-1
1576:                 lines.append(w[:fit_at]); w=w[fit_at:]
1577:             cur=w
1578:         if cur: lines.append(cur)
1579:         return lines or [""]
1580: 
1581:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1582:         """Create a paginated professional PDF with logo, bordered information,
1583:         GRR signature lines and page numbers. Also keep the same report data in
1584:         memory so the built-in Windows printer dialog can print directly without
1585:         requiring a PDF application's PrintTo association."""
1586:         if not hasattr(self, "_print_jobs"):
1587:             self._print_jobs = {}
1588:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1589:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1590:         page=1
1591:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1592:         usable=W-56
1593:         n=max(1,len(headers))
```
```text
1615:             if desc_idx is not None and desc_idx < len(r):
1616:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1617:             else:
1618:                 desc_lines=[""]
1619:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1620:             # Reserve room on the final page for the three transaction signatures + footer.
1621:             reserve=120 if is_transaction_doc else 42
1622:             if y-row_h<reserve:
1623:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1624:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1625:             # Item rows are intentionally border-free. The section/header remains
1626:             # professional while avoiding the unwanted boxed line around each
1627:             # individual printed item row. Description is drawn separately
1628:             # below (auto-fit / wrapped), so it is skipped in this pass.
1629:             for ci,(xx,val) in enumerate(zip(xs,r)):
1630:                 if ci==desc_idx: continue
1631:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1632:             if desc_idx is not None and desc_idx < len(r):
1633:                 for li,ln in enumerate(desc_lines):
1634:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1635:             y-=row_h
```
```text
1630:                 if ci==desc_idx: continue
1631:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1632:             if desc_idx is not None and desc_idx < len(r):
1633:                 for li,ln in enumerate(desc_lines):
1634:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1635:             y-=row_h
1636:         if is_transaction_doc:
1637:             # Keep the three requested transaction signatures at the physical bottom
1638:             # final page, immediately above the report footer.  If the item
1639:             # table reaches this reserved area, start a fresh final page.
1640:             bottom_sig_y = 138
1641:             if y < 165:
1642:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1643:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1644:             # Draw signatures at a fixed bottom position so they never float
1645:             # directly after the last item row.
1646:             self._grr_signature_block(c,bottom_sig_y,page_size)
1647:         self._report_footer(c,page,page_size); c.save()
1648:         if auto_print:
1649:             self.print_pdf(path)
1650:         return path
```
```text
1644:             # Draw signatures at a fixed bottom position so they never float
1645:             # directly after the last item row.
1646:             self._grr_signature_block(c,bottom_sig_y,page_size)
1647:         self._report_footer(c,page,page_size); c.save()
1648:         if auto_print:
1649:             self.print_pdf(path)
1650:         return path
1651: 
1652:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1653:         """Professional on-screen preview showing bordered document information
1654:         and a bordered item section. GRN Date is displayed in the right column."""
1655:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1656:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1657:         # Preview intentionally hides the company logo and company name.
1658:         # The actual generated/printed PDF still contains both via
1659:         # _report_header(), so only the on-screen preview is affected.
1660:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1661:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1662:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1663: 
1664:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
```
```text
1685:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1686: 
1687:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1688:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1689:         tr=self.make_tree(items,columns,widths)
1690:         for r in rows: tr.insert("", "end", values=r)
1691: 
1692:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1693:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1694:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1695:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1696:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1697:         win.bind("<Control-f>",bind_preview_find)
1698:         win.bind("<Control-F>",bind_preview_find)
1699: 
1700:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1701:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1702:         if is_transaction_preview:
1703:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1704:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1705:                 sig.columnconfigure(i,weight=1)
```
```text
1703:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1704:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1705:                 sig.columnconfigure(i,weight=1)
1706:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1707:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1708:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1709: 
1710:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1711:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1712:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1713:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1714:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1715:         if on_save:
1716:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1717:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1718:         if not is_transaction_preview:
1719:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1720:         # IMPORTANT: this must remain a normal top-level window (not transient
1721:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1722:         # exactly like the Preview Report window in the supplied recording.
1723:         # The Find dialog is opened from this window and is independent.
```
```text
1716:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1717:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1718:         if not is_transaction_preview:
1719:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1720:         # IMPORTANT: this must remain a normal top-level window (not transient
1721:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1722:         # exactly like the Preview Report window in the supplied recording.
1723:         # The Find dialog is opened from this window and is independent.
1724:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1725:         win.focus_force()
1726: 
1727:     def _safe_report_name(self, title, extension):
1728:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1729:         safe=safe.replace(" ","_") or "Preview"
1730:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1731: 
1732:     def print_preview_window(self, title, header_lines, columns, rows):
1733:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1734:         self._open_direct_printer(title, header_lines, columns, rows,
1735:                                   landscape(A4) if len(columns) > 8 else A4)
1736: 
```
```text
1729:         safe=safe.replace(" ","_") or "Preview"
1730:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1731: 
1732:     def print_preview_window(self, title, header_lines, columns, rows):
1733:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1734:         self._open_direct_printer(title, header_lines, columns, rows,
1735:                                   landscape(A4) if len(columns) > 8 else A4)
1736: 
1737:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1738:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1739:         This keeps the Export PDF button functional on a machine where the bundled
1740:         ReportLab package cannot be imported."""
1741:         def esc(v):
1742:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1743:         W,H=842,595
1744:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1745:         def add(txt,size=8,leading=11):
1746:             lines.append(f"/F1 {size} Tf")
1747:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1748:         add(str(title),12,16)
1749:         for h in header_lines or []:
```
```text
1756:         lines.append("ET")
1757:         stream="\n".join(lines).encode("latin-1","replace")
1758:         objs=[]
1759:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1760:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1761:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1762:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1763:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1764:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1765:         for i,obj in enumerate(objs,1):
1766:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1767:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1768:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1769:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1770:         with open(path,"wb") as f: f.write(out)
1771: 
1772:     def export_preview_pdf(self, title, header_lines, columns, rows):
1773:         """Generate a real PDF file for the current preview without requiring
1774:         any external PDF application.  ReportLab is preferred; the bundled
1775:         dependency-free writer is used automatically if ReportLab is unavailable.
1776:         """
```
```text
1770:         with open(path,"wb") as f: f.write(out)
1771: 
1772:     def export_preview_pdf(self, title, header_lines, columns, rows):
1773:         """Generate a real PDF file for the current preview without requiring
1774:         any external PDF application.  ReportLab is preferred; the bundled
1775:         dependency-free writer is used automatically if ReportLab is unavailable.
1776:         """
1777:         try:
1778:             os.makedirs(REPORTS_DIR, exist_ok=True)
1779:             safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ","_") or "Preview"
1780:             path=os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf")
1781:             generated=False
1782:             if REPORTLAB:
1783:                 try:
1784:                     self._pdf_table_report(path,title,columns,rows,landscape(A4),7,header_lines=header_lines,auto_print=False)
1785:                     generated=True
1786:                 except Exception:
1787:                     generated=False
1788:             if not generated:
1789:                 self._fallback_pdf_export(path,title,header_lines,columns,rows)
1790:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
```
```text
1783:                 try:
1784:                     self._pdf_table_report(path,title,columns,rows,landscape(A4),7,header_lines=header_lines,auto_print=False)
1785:                     generated=True
1786:                 except Exception:
1787:                     generated=False
1788:             if not generated:
1789:                 self._fallback_pdf_export(path,title,header_lines,columns,rows)
1790:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1791:                 raise IOError("The PDF file was not created.")
1792:             with open(path,"rb") as _pf:
1793:                 if _pf.read(5) != b"%PDF-":
1794:                     raise IOError("The generated file is not a valid PDF.")
1795:             # Export PDF is intentionally silent: open the generated PDF
1796:             # directly in the default web browser without showing a confirmation popup.
1797:             try:
1798:                 webbrowser.open("file://" + os.path.abspath(path))
1799:             except Exception:
1800:                 self.open_file(path)
1801:             return path
1802:         except Exception as e:
1803:             messagebox.showerror("PDF Export",f"Could not generate the PDF.\n\n{e}")
```
```text
1802:         except Exception as e:
1803:             messagebox.showerror("PDF Export",f"Could not generate the PDF.\n\n{e}")
1804:             return None
1805: 
1806:     def export_preview_word(self, title, header_lines, columns, rows):
1807:         """Export exactly what is visible in the current preview to Word."""
1808:         if not DOCX_AVAILABLE:
1809:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1810:         path=self._safe_report_name(title,"docx")
1811:         doc=Document()
1812:         sec=doc.sections[0]
1813:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1814:         sec.header.paragraphs[0].runs[0].bold=True
1815:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1816:         fp=sec.footer.paragraphs[0]
1817:         fp.alignment=2
1818:         if not is_transaction_preview:
1819:             fp.add_run("Authorized Signatory: ____________________    Store In-Charge: ____________________    Page ")
1820:             fld=fp.add_run(); fld._r.append(__import__('docx').oxml.OxmlElement('w:fldChar')); fld._r[-1].set(__import__('docx').oxml.ns.qn('w:fldCharType'),'begin')
1821:             instr=__import__('docx').oxml.OxmlElement('w:instrText'); instr.text='PAGE'; fld._r.append(instr)
1822:             fld2=__import__('docx').oxml.OxmlElement('w:fldChar'); fld2.set(__import__('docx').oxml.ns.qn('w:fldCharType'),'end'); fld._r.append(fld2)
```
```text
1837:             doc.add_paragraph("")
1838:             sig=doc.add_table(rows=2,cols=3)
1839:             labels=["Prepared By","Store Keeper","Store Incharge"]
1840:             for i,label in enumerate(labels):
1841:                 sig.cell(0,i).text="____________________"
1842:                 sig.cell(1,i).text=label
1843:                 for para in sig.cell(1,i).paragraphs:
1844:                     for run in para.runs: run.bold=True
1845:         doc.save(path)
1846:         self.open_file(path)
1847: 
1848:     def export_preview_excel(self, title, header_lines, columns, rows):
1849:         """Export exactly what is visible in the current preview to Excel."""
1850:         if not XLSX_AVAILABLE:
1851:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
1852:         path=self._safe_report_name(title,"xlsx")
1853:         wb=openpyxl.Workbook(); ws=wb.active
1854:         ws.title="Preview"
1855:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
1856:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1857:         if not is_transaction_preview:
```
```text
1875:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
1876:             for col in range(1,4):
1877:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
1878:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
1879:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
1880:         for col_cells in ws.columns:
1881:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
1882:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
1883:         wb.save(path)
1884:         self.open_file(path)
1885: 
1886:     def make_tree(self,parent,cols,widths=None):
1887:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
1888:         tr=ttk.Treeview(fr,columns=cols,show="headings")
1889:         for i,c in enumerate(cols):
1890:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
1891:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
1892:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
1893:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
1894:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
1895:         return tr
```
```text
1948:                     w.state(["!disabled"] if editable else ["disabled"])
1949:             except Exception:
1950:                 try: w.configure(state="normal" if editable else "disabled")
1951:                 except Exception: pass
1952:             for ch in w.winfo_children(): walk(ch)
1953:         for root in roots: walk(root)
1954: 
1955:     def document_selector(self, parent, label, typ, var, load_callback):
1956:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
1957:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
1958:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
1959:         combo.pack(side="left", padx=4)
1960:         def refresh():
1961:             vals=[]
1962:             if typ=="demand":
1963:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
1964:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
1965:             elif typ=="grr":
1966:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
1967:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
1968:             else:
```
```text
1975:             no=text.split(" -> ",1)[0].strip()
1976:             var.set(no)
1977:             load_callback(no)
1978:         combo.bind("<<ComboboxSelected>>", selected)
1979:         combo.bind("<Return>", selected)
1980:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
1981:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
1982:         refresh()
1983:         # Keep the currently open transaction's saved-record list live.
1984:         # Each save calls refresh_saved_cache(), so newly saved records appear
1985:         # immediately without closing/reopening the window or pressing Refresh.
1986:         if not hasattr(self, "_document_selector_refreshers"):
1987:             self._document_selector_refreshers = {}
1988:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
1989:         return combo
1990: 
1991:     def dashboard(self):
1992:         # Dashboard-only visual refresh. All existing data queries, filters,
1993:         # callbacks and report/detail behavior are intentionally preserved.
1994:         self.clearbody()
1995:         c=self.conn
```
```text
2074:             for x in tr.get_children(): tr.delete(x)
2075:             params=[];where=[]
2076:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2077:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2078:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2079:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2080:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2081:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2082:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2083:                    FROM transactions t JOIN items i ON i.code=t.code"""
2084:             if where: sql += " WHERE " + " AND ".join(where)
2085:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2086:             rows=list(c.execute(sql,params))
2087:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2088:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2089:             bal_after={}
2090:             for txid,cc,typ,qty in alltx:
2091:                 running.setdefault(cc,0.0)
2092:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2093:                 bal_after[txid]=running[cc]
2094:             for r in rows:
```
```text
2452:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2453:         load()
2454:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2455: 
2456:     def inventory_codes(self):
2457:         """Inventory Codes using the classic desktop inventory interface.
2458: 
2459:         This screen intentionally follows the uploaded Inventory Management
2460:         reference: a simple module title, compact New/Edit/Delete/Save/
2461:         Refresh/Print/Close action row, and a full-width editable data grid.
2462:         All records come from the V18 database, so existing inventory data is
2463:         preserved rather than recreated.
2464:         """
2465:         self.clearbody()
2466:         # Remove the generic SAP action row; this page owns its own classic
2467:         # action row just like the reference Inventory/Items screen.
2468:         if self.body.winfo_children():
2469:             try:
2470:                 self.body.winfo_children()[0].destroy()
2471:             except Exception:
2472:                 pass
```
```text
2525:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2526:         if filter_text:
2527:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2528:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2529: 
2530:         editing={"id":None,"new":False}
2531:         cell_editor={"widget":None}
2532: 
2533:         def close_editor(save_value=False):
2534:             w=cell_editor.get("widget")
2535:             if not w:
2536:                 return
2537:             try:
2538:                 if save_value:
2539:                     w.event_generate("<Return>")
2540:                 w.destroy()
2541:             except Exception:
2542:                 pass
2543:             cell_editor["widget"]=None
2544: 
2545:         def edit_cell(event=None):
```
```text
2555:             bbox=tree.bbox(iid,colid)
2556:             if not bbox: return
2557:             close_editor(False)
2558:             x,y,w,h=bbox
2559:             val=str(tree.item(iid,"values")[idx] or "")
2560:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2561:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2562:             cell_editor["widget"]=e
2563:             def commit(_=None):
2564:                 try:
2565:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2566:                 finally:
2567:                     try:e.destroy()
2568:                     except Exception:pass
2569:                     cell_editor["widget"]=None
2570:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2571:             e.bind("<FocusOut>",commit)
2572: 
2573:         def rows_query():
2574:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2575:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2577:             if tc: where.append("code <= ?"); params.append(tc)
2578:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2579:             if df or dt:
2580:                 sub=[]; sp=[]
2581:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2582:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2583:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2584:                 params.extend(sp)
2585:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2586:             return sql,params
2587: 
2588:         def load():
2589:             close_editor(False)
2590:             for i in tree.get_children(): tree.delete(i)
2591:             sql,params=rows_query()
2592:             count=0
2593:             for r in self.conn.execute(sql,params):
2594:                 # V18 stores UOM/opening and the original application may have
2595:                 # rate/remarks columns in some versions. Read them safely.
2596:                 rid,code,desc,uom,opening,rate,remarks=r
2597:                 bal=stock(self.conn,code)
```
```text
2611:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2612:             editing["id"]=None; editing["new"]=True
2613:             # Put the user directly into the Code cell.
2614:             try:
2615:                 bbox=tree.bbox(iid,"#2")
2616:                 if bbox:
2617:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2618:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2619:                     def commit(_=None):
2620:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2621:                         try:e.destroy()
2622:                         except Exception:pass
2623:                         cell_editor["widget"]=None
2624:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2625:             except Exception: pass
2626:             status.set("New row added — enter values, then press Save")
2627: 
2628:         def selected_row():
2629:             a=tree.selection()
2630:             return a[0] if a else None
2631: 
```
```text
2631: 
2632:         def edit_record():
2633:             iid=selected_row()
2634:             if not iid:
2635:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2636:             if not self.can_edit and not self.is_admin:
2637:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2638:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2639:             status.set("Edit mode — double-click any cell to change it, then press Save")
2640:             tree.focus(iid); tree.see(iid)
2641: 
2642:         def save_record():
2643:             iid=selected_row()
2644:             if not iid:
2645:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2646:             if not self.can_edit and not self.is_admin:
2647:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2648:             close_editor(True)
2649:             vals=list(tree.item(iid,"values"))
2650:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2651:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2649:             vals=list(tree.item(iid,"values"))
2650:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2651:             try: opening=float(str(vals[4]).strip() or 0)
2652:             except Exception: raise ValueError("Opening Qty must be a number.")
2653:             try: rate=float(str(vals[5]).strip() or 0)
2654:             except Exception: raise ValueError("Rate must be a number.")
2655:             remarks=str(vals[6]).strip()
2656:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2657:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2658:             if not desc:
2659:                 messagebox.showerror("Save","Description is required."); return
2660:             if opening<0:
2661:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2662:             rid=vals[0]
2663:             try:
2664:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2665:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2666:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2667:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2668:                 if rid:
2669:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2672:                                       (code,desc,uom,opening,rid))
2673:                     if oldcode!=code:
2674:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2675:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2676:                             except Exception:pass
2677:                 else:
2678:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2679:                                       (code,desc,uom,"",opening,0,"Local",0))
2680:                 self.conn.commit(); backup_database(); load()
2681:                 messagebox.showinfo("Saved","Inventory Code saved successfully.")
2682:             except Exception as ex:
2683:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2684: 
2685:         def delete_record():
2686:             iid=selected_row()
2687:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2688:             if not self.can_delete and not self.is_admin:
2689:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2690:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2691:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2692:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
```
```text
2686:             iid=selected_row()
2687:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2688:             if not self.can_delete and not self.is_admin:
2689:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2690:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2691:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2692:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2693:             try:
2694:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2695:             except Exception as ex:
2696:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2697: 
2698:         def refresh(): load()
2699:         def do_print():
2700:             try:self.preview_tree("Inventory Codes",tree)
2701:             except Exception as ex:messagebox.showerror("Print",str(ex))
2702:         def do_close(): self.dashboard()
2703: 
2704:         btn("New",new_record,8)
2705:         btn("Edit",edit_record,8)
2706:         btn("Delete",delete_record,8)
```
```text
2699:         def do_print():
2700:             try:self.preview_tree("Inventory Codes",tree)
2701:             except Exception as ex:messagebox.showerror("Print",str(ex))
2702:         def do_close(): self.dashboard()
2703: 
2704:         btn("New",new_record,8)
2705:         btn("Edit",edit_record,8)
2706:         btn("Delete",delete_record,8)
2707:         btn("Save",save_record,8)
2708:         btn("Refresh",refresh,9)
2709:         btn("Preview",do_print,8)
2710:         btn("Print",do_print,8)
2711:         btn("Close",do_close,8)
2712: 
2713:         # Search is deliberately small and sits on the right, without changing
2714:         # the reference layout of the action buttons.
2715:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2716:         search=tk.StringVar()
2717:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2718:         se.pack(side="left",padx=2)
2719:         self._item_master_search_entry=se
```
```text
2727:                     tree.detach(iid)
2728:         search.trace_add("write",filter_grid)
2729:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2730: 
2731:         tree.bind("<Double-1>",edit_cell)
2732:         tree.bind("<F2>",lambda e: edit_record())
2733:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2734:         self._page_actions={
2735:             "save":save_record,"edit":edit_record,"delete":delete_record,
2736:             "cancel":do_close,"print":do_print,"preview":do_print
2737:         }
2738:         load()
2739: 
2740:     def open_mto_inventory_flow(self):
2741:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2742: 
2743:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2744:         Cancel/X only closes the popup.
2745:         """
2746:         criteria = self._ask_mto_inventory_filters()
2747:         if not criteria or criteria.get("cancelled"):
```
```text
2909:                 return False
2910:             destination.set(found_dest)
2911:             edit_mode.update(on=True, original=r[0], dest=found_dest)
2912:             code.set(r[0])
2913:             desc.set(r[1] or "")
2914:             uom.set(r[2] or UOM_OPTIONS[0])
2915:             opening.set(str(r[3] if r[3] is not None else 0))
2916:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
2917:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
2918:             err.set("")
2919:             edit_btn.configure(text="SAVE EDIT")
2920:             ce.focus_set()
2921:             return True
2922: 
2923:         def check_duplicates(*_):
2924:             c = code.get().strip()
2925:             d = desc.get().strip()
2926:             dest = destination.get()
2927:             msgs = []
2928:             r = row_for(dest, c) if len(norm(c)) == 8 else None
2929:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
2931:             dh = desc_hit(dest, d) if d else None
2932:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
2933:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
2934:             hint.set("\n".join(msgs))
2935: 
2936:         code.trace_add("write", check_duplicates)
2937:         desc.trace_add("write", check_duplicates)
2938: 
2939:         def save_code():
2940:             try:
2941:                 c = code.get().strip()
2942:                 d = desc.get().strip()
2943:                 u = uom.get().strip()
2944:                 dest = destination.get()
2945:                 digits = norm(c)
2946:                 if len(digits) != 8:
2947:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
2948:                 if not d:
2949:                     raise ValueError("Description is required.")
2950:                 try:
2951:                     op = float(opening.get().strip() or 0)
```
```text
2972:                         (c, d, u, op, iso, old)
2973:                     )
2974:                     action = "updated"
2975:                 else:
2976:                     self.conn.execute(
2977:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
2978:                         (c, d, u, "", op, 0, iso)
2979:                     )
2980:                     action = "saved"
2981:                 self.conn.commit()
2982:                 backup_database()
2983:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
2984:                 # Keep popup open for fast multiple entries.
2985:                 clear_form(keep_search=False)
2986:                 ce.focus_set()
2987:             except Exception as ex:
2988:                 self.conn.rollback()
2989:                 err.set(str(ex))
2990:                 messagebox.showerror("Code Opening", str(ex), parent=win)
2991: 
2992:         def edit_action():
```
```text
2988:                 self.conn.rollback()
2989:                 err.set(str(ex))
2990:                 messagebox.showerror("Code Opening", str(ex), parent=win)
2991: 
2992:         def edit_action():
2993:             if not edit_mode["on"]:
2994:                 load_for_edit()
2995:             else:
2996:                 save_code()
2997: 
2998:         def delete_code():
2999:             if not edit_mode["on"]:
3000:                 if not load_for_edit():
3001:                     return
3002:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3003:                 return
3004:             try:
3005:                 t = table_for(edit_mode["dest"])
3006:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3007:                 self.conn.commit()
3008:                 backup_database()
```
```text
3004:             try:
3005:                 t = table_for(edit_mode["dest"])
3006:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3007:                 self.conn.commit()
3008:                 backup_database()
3009:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3010:                 clear_form(keep_search=False)
3011:             except Exception as ex:
3012:                 self.conn.rollback()
3013:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3014: 
3015:         btns = ttk.Frame(box)
3016:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3017:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3018:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3019:         edit_btn.pack(side="left", padx=4, ipadx=8)
3020:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3021:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3022:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3023:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3024:         ce.focus_set()
```
```text
3018:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3019:         edit_btn.pack(side="left", padx=4, ipadx=8)
3020:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3021:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3022:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3023:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3024:         ce.focus_set()
3025: 
3026:     def _mto_new_item_dialog(self, on_saved):
3027:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3028:         brand-new item can be created without leaving that screen. Writes
3029:         straight into the same Item Master (items table) used everywhere."""
3030:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3031:         win.transient(self); win.grab_set()
3032:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3033:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3034:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3035:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3036:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3037:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3038:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3034:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3035:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3036:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3037:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3038:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3039:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3040:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3041:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3042:         def save():
3043:             try:
3044:                 c=code.get().strip(); d=desc.get().strip()
3045:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3046:                 if not d: raise ValueError("Description is required.")
3047:                 try:
3048:                     opening_val=float(opening.get() or 0)
3049:                 except ValueError:
3050:                     raise ValueError("Opening Qty must be a number.")
3051:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3052:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3053:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3054:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3047:                 try:
3048:                     opening_val=float(opening.get() or 0)
3049:                 except ValueError:
3050:                     raise ValueError("Opening Qty must be a number.")
3051:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3052:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3053:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3054:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3055:                 self.conn.commit(); backup_database()
3056:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3057:                 win.grab_release(); win.destroy()
3058:                 on_saved()
3059:             except Exception as ex: messagebox.showerror("Error",str(ex))
3060:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3061:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3062:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3063: 
3064:     def _item_filter_bar(self, parent, on_change):
3065:         """Item Code entry + item-master picker + Search/Show All. Calls
3066:         on_change() whenever the code changes or a button is pressed."""
3067:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3153:         self._item_master_find_callback=None
3154:         self._portable_print_context=None
3155:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3156:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3157:         }
3158: 
3159:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3160:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3161:         self.conn.commit()
3162: 
3163:         # ---- Same professional in-app window layout as Inventory Codes ----
3164:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3165:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3166:                   foreground=COLORS["primary_dark"]).pack(side="left")
3167:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3168: 
3169:         def open_find():
3170:             state_find={"index":-1}
3171:             def search_fn(text):
3172:                 text=text.strip().lower()
3173:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3260:             for i in table.get_children(): table.delete(i)
3261:             where=["1=1"]; params=[]
3262:             prefix=state.get("prefix",""); q=search.get().strip()
3263:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3264:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3265:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3266:             if fc: where.append("code >= ?"); params.append(fc)
3267:             if tc: where.append("code <= ?"); params.append(tc)
3268:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3269:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3270:             records=[]
3271:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3272:                 # If a date filter is supplied, accept an opening-date match OR
3273:                 # a transaction in that date range. This prevents valid MTO codes
3274:                 # from disappearing merely because an older record has no opening_date.
3275:                 if df or dt:
3276:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3277:                     if not ok:
3278:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3279:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3280:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3350:                 tr.insert("", "end", values=r)
3351:         def clear():
3352:             for x in v.values(): x.set("")
3353:             try: tr.selection_remove(tr.selection())
3354:             except Exception: pass
3355:             self._set_form_editable(party_form_roots, False)
3356:         def new_form():
3357:             clear(); self._set_form_editable(party_form_roots, True)
3358:         def save():
3359:             try:
3360:                 name=v["name"].get().strip()
3361:                 if not name: raise ValueError("Party Name is required.")
3362:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3363:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3364:             except Exception as ex: messagebox.showerror("Error",str(ex))
3365:         def load_party_row(a):
3366:             if not a:return
3367:             r=tr.item(a[0])["values"]
3368:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3369:             self._set_form_editable(party_form_roots, False)
3370:         def on_party_select(_=None):
```
```text
3376:             load_party_row(a)
3377:             self._set_form_editable(party_form_roots, True)
3378:         def delete_party():
3379:             a=tr.selection()
3380:             if not a:
3381:                 messagebox.showwarning("Delete", "Select a party first."); return
3382:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3383:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3384:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3385:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3386:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3387:         self._add_transaction_new_button(new_form)
3388:         load(); clear()
3389: 
3390:     def user_management(self):
3391:         self.clearbody()
3392:         if not self.is_admin:
3393:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3394:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3395:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3396:         role=tk.StringVar(value="User")
```
```text
3433:             u_ent.state(["!disabled"])
3434:         def edit():
3435:             a=tr.selection()
3436:             if not a:
3437:                 messagebox.showwarning("Edit User","Select a user row first."); return
3438:             r=tr.item(a[0])["values"]
3439:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3440:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3441:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3442:         def save():
3443:             try:
3444:                 username=v["username"].get().strip()
3445:                 if not username: raise ValueError("Username is required.")
3446:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3447:                 pw=v["password"].get()
3448:                 if exists:
3449:                     pw_hash = hash_password(pw) if pw else exists[0]
3450:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3451:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3452:                 else:
3453:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3448:                 if exists:
3449:                     pw_hash = hash_password(pw) if pw else exists[0]
3450:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3451:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3452:                 else:
3453:                     if not pw: raise ValueError("Password is required for a new user.")
3454:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3455:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3456:                 self.conn.commit(); backup_database(); load(); clear()
3457:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3458:             except Exception as ex:
3459:                 messagebox.showerror("Error", str(ex))
3460:         def delete_user():
3461:             a=tr.selection()
3462:             if not a:
3463:                 messagebox.showwarning("Delete User","Select a user row first."); return
3464:             username=tr.item(a[0])["values"][0]
3465:             if username==self.current_user:
3466:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3467:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3468:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3463:                 messagebox.showwarning("Delete User","Select a user row first."); return
3464:             username=tr.item(a[0])["values"][0]
3465:             if username==self.current_user:
3466:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3467:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3468:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3469:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3470:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3471:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3472:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3473:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3474:         load()
3475: 
3476:     @staticmethod
3477:     def _renumber_tree(tree, rows):
3478:         for i,iid in enumerate(tree.get_children()):
3479:             vals=list(tree.item(iid,"values"));
3480:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3481: 
3482:     def demand(self):
3483:         self.clearbody(); self.demand_lines=[]
```
```text
3480:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3481: 
3482:     def demand(self):
3483:         self.clearbody(); self.demand_lines=[]
3484:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3485:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3486:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3487:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3488:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3489:         # Demand Date is intentionally displayed as its own dedicated field.
3490:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3491:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3492:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3493:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3494:                 ("special","Special Instructions"),("source","Recommended Source")]
3495:         for i,(k,n) in enumerate(fields):
3496:             r=i//4*2+3; c=i%4*2
3497:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3498:             if k=="dept":
3499:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3500:             elif k=="urgency":
```
```text
3570:         def new_form():
3571:             self._editing_document_key=None
3572:             for z in v.values(): z.set("")
3573:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3574:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3575:             for iid in tree.get_children(): tree.delete(iid)
3576:             self._set_form_editable(form_roots, True, skip=[selector])
3577: 
3578:         def save():
3579:             try:
3580:                 no=v["no"].get().strip()
3581:                 if not no: raise ValueError("Demand No is required.")
3582:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3583:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3584:                 if dup and getattr(self,"_editing_document_key",None) != no:
3585:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3586:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3587:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3588:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3589:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3590:                 self.conn.commit(); backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector]); messagebox.showinfo("Saved",f"Demand {no} saved successfully.")
```
```text
3590:                 self.conn.commit(); backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector]); messagebox.showinfo("Saved",f"Demand {no} saved successfully.")
3591:             except Exception as ex: messagebox.showerror("Error",str(ex))
3592:         form_roots=[f,line,editbar]
3593:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3594:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3595:         def delete_current():
3596:             no=v["no"].get().strip()
3597:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3598:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3599:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3600:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
3601:             self.demand(); messagebox.showinfo("Deleted",f"Demand {no} deleted.")
3602:         def cancel_form():
3603:             self._editing_document_key=None
3604:             self._set_form_editable(form_roots, False, skip=[selector])
3605:             for z in v.values(): z.set("")
3606:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3607:             itype.set("Local")
3608:             self.demand_lines.clear()
3609:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3610:             for iid in tree.get_children(): tree.delete(iid)
```
```text
3613:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3614:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3615:                     f"Justification: {v['just'].get()}",
3616:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3617:             if not self.demand_lines:
3618:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3619:             self.show_preview_window("Purchase Demand", header,
3620:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3621:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3622:         def edit_saved_demand():
3623:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3624:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3625:             self._set_form_editable(form_roots, True, skip=[selector])
3626:         def print_now():
3627:             if not self.demand_lines:
3628:                 messagebox.showwarning("Print","Add at least one item line first."); return
3629:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3630:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3631:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3632:                     f"Justification: {v['just'].get()}",
3633:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3629:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3630:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3631:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3632:                     f"Justification: {v['just'].get()}",
3633:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3634:             self._open_direct_printer("Purchase Demand",header,
3635:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3636:                 self.demand_lines,A4)
3637:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3638:         self._add_transaction_new_button(new_form)
3639:         self._set_form_editable(form_roots, False, skip=[selector])
3640:         try:
3641:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3642:         except Exception: pass
3643:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3644: 
3645:     def load_demand_into_form(self,no,v,tree):
3646:         v["no"].set(no)
3647:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3648:         if not r:return
3649:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3651:         self.demand_lines=[]
3652:         for i in tree.get_children():tree.delete(i)
3653:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3654:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3655:         roots=getattr(self,"_transaction_form_roots",None)
3656:         if roots and "demand" in roots:
3657:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3658: 
3659:     def refresh_saved_cache(self,typ):
3660:         # Refresh saved-document dropdowns immediately after a successful save.
3661:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3662:         alive=[]
3663:         for combo, refresh in refreshers:
3664:             try:
3665:                 if combo.winfo_exists():
3666:                     refresh()
3667:                     alive.append((combo, refresh))
3668:             except Exception:
3669:                 pass
3670:         if hasattr(self, "_document_selector_refreshers"):
3671:             self._document_selector_refreshers[typ] = alive
```
```text
3670:         if hasattr(self, "_document_selector_refreshers"):
3671:             self._document_selector_refreshers[typ] = alive
3672: 
3673:     def grr(self):
3674:         self.clearbody(); self.grr_lines=[]
3675:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3676:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3677:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3678:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3679:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3680:         for i,(k,n) in enumerate(fields):
3681:             r=i//4*2+2;c=i%4*2
3682:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3683:             if k=="department":
3684:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3685:             elif k=="supplier":
3686:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3687:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3688:             elif k=="date":
3689:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3690:             else:
```
```text
3739:         def new_form():
3740:             self._editing_document_key=None
3741:             for z in v.values(): z.set("")
3742:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3743:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3744:             for iid in tree.get_children(): tree.delete(iid)
3745:             self._set_form_editable(form_roots, True, skip=[selector])
3746: 
3747:         def save():
3748:             try:
3749:                 no=v["no"].get().strip()
3750:                 if not no:raise ValueError("GRN No is required.")
3751:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3752:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3753:                 if dup and getattr(self,"_editing_document_key",None) != no:
3754:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3755:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3756:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3757:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3758:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3759:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3756:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3757:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3758:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3759:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3760:                 for x in self.grr_lines:
3761:                     ltype=x[10] if len(x)>10 else "Local"
3762:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3763:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3764:                 self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("grr");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock.")
3765:             except Exception as ex:messagebox.showerror("Error",str(ex))
3766:         form_roots=[f,line,editbar]
3767:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3768:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3769:         def delete_current():
3770:             no=v["no"].get().strip()
3771:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3772:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3773:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3774:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3775:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3776:         def cancel_form():
```
```text
3795:                     ("Challan #", v['challan'].get()),
3796:                     ("Vehicle #", v['vehicle'].get()),
3797:                     ("Bill/Voucher #", v['bill'].get()),
3798:                     ("Reference", v['ref'].get()),
3799:                     ("Remarks", v['remarks'].get()),
3800:                     ("Total Value", fmt_num(total))]
3801:             self.show_preview_window("GRN Receipt", header,
3802:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3803:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3804:         def portable_current():
3805:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3806:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3807:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3808:         self._portable_print_context=portable_current
3809:         def edit_saved_grr():
3810:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3811:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
3812:             self._set_form_editable(form_roots, True, skip=[selector])
3813:         def print_now():
3814:             if not self.grr_lines:
3815:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
3819:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
3820:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
3821:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
3822:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
3823:                     ("Total Value", fmt_num(total))]
3824:             self._open_direct_printer("GRN Receipt",header,
3825:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3826:                 self.grr_lines,landscape(A4))
3827:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3828:         self._add_transaction_new_button(new_form)
3829:         self._set_form_editable(form_roots, False, skip=[selector])
3830:         try:
3831:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3832:         except Exception: pass
3833:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
3834: 
3835:     def load_grr_into_form(self,no,v,tree):
3836:         v["no"].set(no)
3837:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
3838:         if not r:return
3839:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
3846:         if roots and "grr" in roots:
3847:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
3848: 
3849:     def issue(self):
3850:         self.clearbody(); self.issue_lines=[]
3851:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
3852:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
3853:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3854:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
3855:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
3856:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
3857:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3858:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3859:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
3860:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
3861:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
3862:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
3863:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
3864:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
3865:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
3866:         itype=tk.StringVar(value="Local")
```
```text
3935:                 # Editing an existing issue replaces its old stock transaction and detail lines.
3936:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
3937:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
3938:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
3939:                 for x in self.issue_lines:
3940:                     ltype=x[7] if len(x)>7 else "Local"
3941:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
3942:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
3943:                 self.conn.commit();backup_database();self._editing_document_key=None;self.refresh_saved_cache("issue");self._set_form_editable(form_roots, False, skip=[selector]);messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock.")
3944:             except Exception as ex:messagebox.showerror("Error",str(ex))
3945:         def delete_current():
3946:             no=v["no"].get().strip()
3947:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
3948:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
3949:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
3950:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
3951:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
3952:         def cancel_form():
3953:             self._editing_document_key=None
3954:             self._set_form_editable(form_roots, False, skip=[selector])
3955:             for z in v.values(): z.set("")
```
```text
3960:             for iid in tree.get_children(): tree.delete(iid)
3961:         def preview_now():
3962:             if not self.issue_lines:
3963:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3964:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3965:                     f"Items Use For: {v['items_use_for'].get()}"]
3966:             self.show_preview_window("Material Issue", header,
3967:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
3968:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
3969:         def portable_current():
3970:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
3971:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
3972:         self._portable_print_context=portable_current
3973:         form_roots=[f,usebar,line,editbar]
3974:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3975:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
3976:         def load_saved_issue(no):
3977:             self.load_issue_into_form(no,v,tree)
3978:             self._set_form_editable(form_roots, False, skip=[selector])
3979:         def edit_saved_issue():
3980:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
3973:         form_roots=[f,usebar,line,editbar]
3974:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3975:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
3976:         def load_saved_issue(no):
3977:             self.load_issue_into_form(no,v,tree)
3978:             self._set_form_editable(form_roots, False, skip=[selector])
3979:         def edit_saved_issue():
3980:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3981:             self._edit_from_selector("issue", v["no"], load_saved_issue)
3982:             self._set_form_editable(form_roots, True, skip=[selector])
3983:         def print_issue_now():
3984:             if not self.issue_lines:
3985:                 messagebox.showwarning("Print","Add at least one item line first."); return
3986:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
3987:             self._open_direct_printer("Material Issue",header,
3988:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
3989:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
3990:         self._add_transaction_new_button(new_form)
3991:         self._set_form_editable(form_roots, False, skip=[selector])
3992:         self._active_form_loader = load_saved_issue
3993: 
```
```text
4001:         for i in tree.get_children():tree.delete(i)
4002:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4003:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4004:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4005:         roots=getattr(self,"_transaction_form_roots",None)
4006:         if roots and "issue" in roots:
4007:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4008: 
4009:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4010:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4011: 
4012:         The layout intentionally matches Inventory Codes' Selection Criteria
4013:         popup so all Report sub-sections have one consistent desktop workflow.
4014:         """
4015:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4016:         win=tk.Toplevel(self)
4017:         win.title(f"{report_title} - Selection Criteria")
4018:         win.resizable(False,False)
4019:         win.transient(self); win.grab_set()
4020:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4021:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4066:             except Exception: pass
4067:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4068:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4069:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4070:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4071:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4072:         e1.focus_set(); self.wait_window(win); return result
4073: 
4074:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4075:         self._pending_report_filters=criteria
4076:         try:
4077:             return self.open_menu_window(method,title,geometry)
4078:         finally:
4079:             self._pending_report_filters=None
4080: 
4081:     def open_stock_balance_report_flow(self):
4082:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4083:         if f.get("cancelled"): return None
4084:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4085: 
4086:     def open_grr_report_flow(self):
```
```text
4079:             self._pending_report_filters=None
4080: 
4081:     def open_stock_balance_report_flow(self):
4082:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4083:         if f.get("cancelled"): return None
4084:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4085: 
4086:     def open_grr_report_flow(self):
4087:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4088:         if f.get("cancelled"): return None
4089:         return self._open_report_child(self.report_grr,"GRN Report",f)
4090: 
4091:     def open_demand_report_flow(self):
4092:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4093:         if f.get("cancelled"): return None
4094:         return self._open_report_child(self.report_demand,"Demand Report",f)
4095: 
4096:     def open_issue_report_flow(self):
4097:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4098:         if f.get("cancelled"): return None
4099:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4093:         if f.get("cancelled"): return None
4094:         return self._open_report_child(self.report_demand,"Demand Report",f)
4095: 
4096:     def open_issue_report_flow(self):
4097:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4098:         if f.get("cancelled"): return None
4099:         return self._open_report_child(self.report_issue,"Issue Report",f)
4100: 
4101:     def open_party_report_flow(self):
4102:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4103:         if f.get("cancelled"): return None
4104:         return self._open_report_child(self.report_party,"Party Report",f)
4105: 
4106:     def _ask_stock_balance_filters(self):
4107:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4108:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4109:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4110:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4111:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4112:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4113:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4125:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4126:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4127:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4128:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4129:         e1.focus_set();self.wait_window(win);return result
4130: 
4131:     def stock_balance(self):
4132:         self.clearbody()
4133:         # Stock Balance is a Report sub-section and does not use the generic
4134:         # Save/Edit/Delete/Cancel/Print action strip.
4135:         children=self.body.winfo_children()
4136:         if children:
4137:             children[0].destroy()
4138:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4139:         if initial.get("cancelled"):
4140:             self.dashboard(); return
4141:         top=ttk.Frame(self.body);top.pack(fill="x")
4142:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4143:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4144:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4145:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4155:             for typ,qty in self.conn.execute(q,params):
4156:                 if typ=="GRR":gr+=float(qty or 0)
4157:                 elif typ=="ISSUE":iss+=float(qty or 0)
4158:             return opening_before,gr,iss,opening_before+gr-iss
4159:         def header_summary():
4160:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4161:         def load():
4162:             for i in tr.get_children():tr.delete(i)
4163:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4164:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4165:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4166:             sql+=" ORDER BY code"
4167:             for r in self.conn.execute(sql,params):
4168:                 op,gr,iss,cur=period(r[0],r[3])
4169:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4170:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4171:         def reopen_filters():
4172:             initial2=self._ask_stock_balance_filters()
4173:             if initial2.get("cancelled"):return
4174:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4175:             load()
```
```text
4213:         """
4214:         if typ=="demand": self.demand()
4215:         elif typ=="grr": self.grr()
4216:         else: self.issue()
4217:         loader=getattr(self,"_active_form_loader",None)
4218:         if loader: loader(str(no))
4219: 
4220:     def _edit_from_selector(self, typ, var, loader):
4221:         """Top Edit action: load the saved document directly into the current form.
4222:         If nothing is selected, use the newest saved document; never open a popup.
4223:         """
4224:         text=var.get().strip()
4225:         if text:
4226:             no=text.split(" -> ",1)[0].strip()
4227:         else:
4228:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4229:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4230:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4231:             if not r:
4232:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4233:                 return
```
```text
4230:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4231:             if not r:
4232:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4233:                 return
4234:             no=str(r[0])
4235:             var.set(no)
4236:         loader(no)
4237: 
4238:     def show_saved_records(self,typ):
4239:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4240:         if typ=="demand":
4241:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4242:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4243:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4244:             for r in rows:
4245:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4246:                 r=list(r); r[1]=to_display_date(r[1])
4247:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4248:         elif typ=="grr":
4249:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4250:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4261:         def view():
4262:             a=tr.selection()
4263:             if not a:return
4264:             no=tr.item(a[0])["values"][0]
4265:             win.destroy();self.open_document_editor(typ,no)
4266:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4267:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4268:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4269:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4270: 
4271:     def documents(self):
4272:         self.clearbody()
4273:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4274:         specs=[
4275:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4276:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4277:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4278:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4279:             ("Material Issues","issue",("No","Date","Department"),
4280:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4281:         ]
```
```text
4277:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4278:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4279:             ("Material Issues","issue",("No","Date","Department"),
4280:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4281:         ]
4282:         for title,typ,cols,query in specs:
4283:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4284:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4285:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4286:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4287:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4288:             for r in self.conn.execute(query):
4289:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4290:             def edit_selected(t=tr,k=typ):
4291:                 a=t.selection()
4292:                 if not a:
4293:                     messagebox.showwarning("Edit", "Select a saved record first.")
4294:                     return
4295:                 no=t.item(a[0])["values"][0]
4296:                 self.open_document_editor(k,no)
4297:             def delete_selected(t=tr,k=typ):
```
```text
4292:                 if not a:
4293:                     messagebox.showwarning("Edit", "Select a saved record first.")
4294:                     return
4295:                 no=t.item(a[0])["values"][0]
4296:                 self.open_document_editor(k,no)
4297:             def delete_selected(t=tr,k=typ):
4298:                 a=t.selection()
4299:                 if not a:
4300:                     messagebox.showwarning("Delete", "Select a saved record first.")
4301:                     return
4302:                 no=t.item(a[0])["values"][0]
4303:                 if k=="demand":
4304:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4305:                 elif k=="grr":
4306:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4307:                 else:
4308:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4309:                 self.conn.commit();backup_database();self.documents()
4310:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4311:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4312:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4306:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4307:                 else:
4308:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4309:                 self.conn.commit();backup_database();self.documents()
4310:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4311:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4312:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4313:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4314:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4315:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4316:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4317: 
4318:     def doc_export_selected(self,typ,tr,fmt):
4319:         a=tr.selection()
4320:         if not a:
4321:             messagebox.showwarning("Export","Select a saved record first."); return
4322:         no=tr.item(a[0])["values"][0]
4323:         if fmt=="word": self.export_word(typ,no)
4324:         else: self.export_excel(typ,no)
4325: 
4326:     def doc_preview_selected(self,typ,tr):
```
```text
4321:             messagebox.showwarning("Export","Select a saved record first."); return
4322:         no=tr.item(a[0])["values"][0]
4323:         if fmt=="word": self.export_word(typ,no)
4324:         else: self.export_excel(typ,no)
4325: 
4326:     def doc_preview_selected(self,typ,tr):
4327:         a=tr.selection()
4328:         if not a:
4329:             messagebox.showwarning("Preview","Select a saved record first."); return
4330:         no=tr.item(a[0])["values"][0]
4331:         data=self._get_doc_data(typ,no)
4332:         if not data:
4333:             messagebox.showwarning("Preview","Document not found."); return
4334:         title,header,cols,rows=data
4335:         header_lines=header
4336:         self.show_preview_window(title,header_lines,cols,rows)
4337: 
4338:     def doc_print_selected(self,typ,tr):
4339:         a=tr.selection()
4340:         if not a: return
4341:         no=tr.item(a[0])["values"][0]
```
```text
4372:         def _print_loaded_document():
4373:             data=self._get_doc_data(typ,no)
4374:             if not data:
4375:                 messagebox.showwarning("Document","Document not found."); return
4376:             title,header,cols,rows=data
4377:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4378:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4379: 
4380:     def _report_filter_popup(self, title, include_party=False):
4381:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4382:         win,winbody=self._internal_window(title,"520x420")
4383:         done=tk.BooleanVar(value=False)
4384:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4385:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4386:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4387:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4388:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4389:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4390:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4391:         if include_party:
4392:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4386:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4387:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4388:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4389:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4390:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4391:         if include_party:
4392:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4393:         def ok():
4394:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4395:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4396:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4397:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4398: 
4399:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4400:         self.clearbody()
4401:         # Report sub-sections use their own report toolbar; remove only the
4402:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4403:         children=self.body.winfo_children()
4404:         if children:
4405:             children[0].destroy()
4406:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4407:         if f.get("cancelled"):
4408:             self.dashboard();return
4409:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4410:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4411:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4412:         def load():
4413:             for i in tr.get_children():tr.delete(i)
4414:             params,where=params_builder(f)
4415:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4416:             for r in self.conn.execute(sql,params):
4417:                 vals=list(r)
4418:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4419:                 tr.insert("","end",values=vals)
4420:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4421:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4422:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4423:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4424:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4425:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4426:         def open_find_report():
4427:             state_find={"index":-1}
```
```text
4433:                 order=children[start:]+children[:start]
4434:                 for iid in order:
4435:                     vals=tr.item(iid,"values")
4436:                     if any(text in str(v).lower() for v in vals):
4437:                         state_find["index"]=children.index(iid)
4438:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4439:                 return False
4440:             self._open_exact_find_text_popup(search_fn)
4441:         self._item_master_find_callback=open_find_report
4442:         load()
4443:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4444: 
4445:     def report_grr(self):
4446:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4447:         def pb(f):
4448:             w=[];p=[]
4449:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4450:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4451:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4452:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4453:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4448:             w=[];p=[]
4449:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4450:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4451:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4452:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4453:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4454:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4455:             return p,w
4456:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4457: 
4458:     def report_demand(self):
4459:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4460:         def pb(f):
4461:             w=[];p=[]
4462:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4463:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4464:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4465:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4466:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4467:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4468:             return p,w
```
```text
4461:             w=[];p=[]
4462:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4463:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4464:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4465:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4466:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4467:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4468:             return p,w
4469:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4470: 
4471:     def report_issue(self):
4472:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4473:         def pb(f):
4474:             w=[];p=[]
4475:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4476:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4477:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4478:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4479:             return p,w
4480:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4481: 
```
```text
4474:             w=[];p=[]
4475:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4476:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4477:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4478:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4479:             return p,w
4480:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4481: 
4482:     def report_party(self):
4483:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4484:         def pb(f):
4485:             w=[];p=[]
4486:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4487:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4488:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4489:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4490:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4491:             return p,w
4492:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4493: 
4494:     def reports(self):
```
```text
4492:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4493: 
4494:     def reports(self):
4495:         self.clearbody()
4496:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4497: 
4498:         # ================= GRN Details =================
4499:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4500:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4501:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4502:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4503:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4504:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4505: 
4506:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4507:         def load_grr_item(codev=None):
4508:             for i in tr.get_children(): tr.delete(i)
4509:             q=codev.get().strip() if codev else ""
4510:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4511:             for r in self.conn.execute(sql,(q,) if q else ()):
4512:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4518:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4519:         tr=self.make_tree(fr,grr_cols,grr_widths)
4520:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4521:             for i in tr.get_children(): tr.delete(i)
4522:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4523:             conds=[];params=[]
4524:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4525:             if td: conds.append("g.grr_date<=?");params.append(td)
4526:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4527:             for r in self.conn.execute(sql,params):
4528:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4529:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4530:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4531:         load_grr_date(fdv,tdv)
4532: 
4533:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4534:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4535:         party=tk.StringVar(value="ALL")
4536:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4537:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4538:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4534:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4535:         party=tk.StringVar(value="ALL")
4536:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4537:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4538:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4539:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4540:         def load_party(*_):
4541:             for i in tr.get_children(): tr.delete(i)
4542:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4543:             if party.get()=="ALL":
4544:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4545:             else:
4546:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4547:             for r in rows:
4548:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4549:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4550:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4551: 
4552:         # ================= Demand Details =================
4553:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4554:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4550:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4551: 
4552:         # ================= Demand Details =================
4553:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4554:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4555:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4556:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4557:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4558:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4559: 
4560:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4561:         def load_dem_item(codev=None):
4562:             for i in tr.get_children(): tr.delete(i)
4563:             q=codev.get().strip() if codev else ""
4564:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4565:             for r in self.conn.execute(sql,(q,) if q else ()):
4566:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4567:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4568:         tr=self.make_tree(fr,dem_cols,dem_widths)
4569:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4570:         load_dem_item(codev)
```
```text
4572:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4573:         tr=self.make_tree(fr,dem_cols,dem_widths)
4574:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4575:             for i in tr.get_children(): tr.delete(i)
4576:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4577:             conds=[];params=[]
4578:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4579:             if td: conds.append("d.demand_date<=?");params.append(td)
4580:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4581:             for r in self.conn.execute(sql,params):
4582:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4583:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4584:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4585:         load_dem_date(fdv,tdv)
4586: 
4587:         # ================= Material Issue Details =================
4588:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4589:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4590:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4591:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4592:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4585:         load_dem_date(fdv,tdv)
4586: 
4587:         # ================= Material Issue Details =================
4588:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4589:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4590:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4591:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4592:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4593:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4594: 
4595:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4596:         def load_iss_item(codev=None):
4597:             for i in tr.get_children(): tr.delete(i)
4598:             q=codev.get().strip() if codev else ""
4599:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4600:             for r in self.conn.execute(sql,(q,) if q else ()):
4601:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4602:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4603:         tr=self.make_tree(fr,iss_cols,iss_widths)
4604:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4605:         load_iss_item(codev)
```
```text
4607:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4608:         tr=self.make_tree(fr,iss_cols,iss_widths)
4609:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4610:             for i in tr.get_children(): tr.delete(i)
4611:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4612:             conds=[];params=[]
4613:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4614:             if td: conds.append("i.issue_date<=?");params.append(td)
4615:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4616:             for r in self.conn.execute(sql,params):
4617:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4618:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4619:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4620:         load_iss_date(fdv,tdv)
4621: 
4622:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4623: 
4624:     def print_item_master(self):
4625:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4626:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4627: 
```
```text
4624:     def print_item_master(self):
4625:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4626:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4627: 
4628:     def print_party_master(self):
4629:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4630:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4631: 
4632:     def print_report(self,kind):
4633:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4634:         if kind=="grr":
4635:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4636:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4637:         elif kind=="demand":
4638:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4639:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4640:         elif kind=="issue":
4641:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4642:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4643:         else:
4644:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4645:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4646:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4647: 
4648:     def print_stock(self):
4649:         rows=[]
4650:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4651:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4652:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4653:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4654: 
4655:     def print_ledger(self):
4656:         rows=[]
4657:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4658:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4659:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4660:                 running += x[3] if x[1]=="GRR" else -x[3]
4661:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4662:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4663: 
4664:     def _get_doc_data(self, typ, no):
4665:         """Header + line items for one saved document, used by the on-screen
```
```text
4731:             sig=doc.add_table(rows=2,cols=3)
4732:             labels=["Prepared By","Store Keeper","Store Incharge"]
4733:             for i,label in enumerate(labels):
4734:                 sig.cell(0,i).text="____________________"
4735:                 sig.cell(1,i).text=label
4736:                 for para in sig.cell(1,i).paragraphs:
4737:                     for run in para.runs: run.bold=True
4738:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4739:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4740:         doc.save(path)
4741:         self.open_file(path)
4742: 
4743:     def export_excel(self, typ, no):
4744:         if not no or not no.strip():
4745:             return messagebox.showwarning("Excel Export","Select a document first.")
4746:         if not XLSX_AVAILABLE:
4747:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4748:         data=self._get_doc_data(typ,no)
4749:         if not data:
4750:             return messagebox.showwarning("Excel Export","Document not found.")
4751:         title,header,cols,rows=data
```
```text
4773:             for col in range(1,4):
4774:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4775:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4776:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4777:         for col_cells in ws.columns:
4778:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4779:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4780:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4781:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4782:         wb.save(path)
4783:         self.open_file(path)
4784: 
4785:     def preview_pdf(self,typ,no):
4786:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4787:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4788:         data=self._get_doc_data(typ,no)
4789:         if not data:return messagebox.showwarning("Document","Document not found.")
4790:         title,header,cols,rows=data
4791:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4792:         page_size = landscape(A4) if typ == "grr" else A4
4793:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4788:         data=self._get_doc_data(typ,no)
4789:         if not data:return messagebox.showwarning("Document","Document not found.")
4790:         title,header,cols,rows=data
4791:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4792:         page_size = landscape(A4) if typ == "grr" else A4
4793:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4794: 
4795:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4796:         """Open the print dialog with a real visual preview of the exact report.
4797: 
4798:         The report is rendered to a temporary PDF only in memory/on disk for the
4799:         duration of printing.  It is deleted after the print dialog closes, so
4800:         the Print button does not leave a PDF report behind.  Printing uses the
4801:         rendered report page itself rather than rebuilding rows as plain text;
4802:         this keeps the printed page identical to the application's report.
4803:         """
4804:         # Printing is always prepared as an A4 landscape page. This only affects
4805:         # the print path; the rest of the application's UI/report logic is unchanged.
4806:         page_size = landscape(A4)
4807:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
4808:             messagebox.showwarning(
```
```text
4810:                 "The print preview/printing components are not available.\n\n"
4811:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
4812:             )
4813:             return
4814:         if not rows and not columns:
4815:             messagebox.showwarning("Print", "There is no data to print.")
4816:             return
4817:         try:
4818:             os.makedirs(REPORTS_DIR, exist_ok=True)
4819:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
4820:             self._pdf_table_report(key,title,columns,rows,page_size,
4821:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
4822:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
4823:             self._select_windows_printer_for_pdf(key)
4824:         except Exception as e:
4825:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
4826: 
4827:     def _select_windows_printer_for_pdf(self, path):
4828:         """Print dialog with an actual page preview, printer selection and direct GDI output.
4829: 
4830:         The preview is rendered from the exact PDF produced by the application,
```
```text
4860:         job=getattr(self, "_print_jobs", {}).get(path)
4861:         if job:
4862:             title, header_lines, columns, rows, source_page_size = job
4863:         else:
4864:             title=os.path.splitext(os.path.basename(path))[0]
4865:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
4866: 
4867:         try:
4868:             doc=fitz.open(path)
4869:             total_pages=max(1,doc.page_count)
4870:         except Exception as e:
4871:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
4872:             return
4873: 
4874:         win=tk.Toplevel(self)
4875:         win.title("Printing from Win32 application - Print")
4876:         win.geometry("900x620")
4877:         win.minsize(850,580)
4878:         win.transient(self)
4879:         win.configure(bg="#f0f0f0")
4880: 
```
```text
4886:             pass
4887: 
4888:         outer=tk.Frame(win,bg="#f0f0f0")
4889:         outer.pack(fill="both",expand=True)
4890:         outer.columnconfigure(1,weight=1)
4891:         outer.rowconfigure(0,weight=1)
4892: 
4893:         # Left side mirrors the familiar system printer dialog: printers and
4894:         # print options. Right side contains the actual report page preview.
4895:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
4896:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
4897:         left.grid_propagate(False)
4898:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
4899:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
4900:         printer_list.pack(fill="x")
4901:         for pr in printers: printer_list.insert("end",pr)
4902:         try: printer_list.selection_set(printers.index(default_printer))
4903:         except Exception: printer_list.selection_set(0)
4904: 
4905:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
4906:         copies=tk.IntVar(value=1)
```
```text
4979:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
4980: 
4981:         bottom=tk.Frame(win,bg="#f0f0f0")
4982:         # `outer` already uses pack() in `win`; using grid() for another direct
4983:         # child of the same toplevel raises TclError. Keep the action bar in the
4984:         # same geometry-manager family so Print/Cancel are always visible.
4985:         bottom.pack(fill="x",padx=12,pady=(0,12))
4986:         bottom.columnconfigure(0,weight=1)
4987:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
4988:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
4989:         print_btn=ttk.Button(bottom,text="Print",width=12)
4990:         print_btn.grid(row=0,column=2,padx=(8,0))
4991: 
4992:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
4993: 
4994:         def parse_page_selection(total):
4995:             if pages_mode.get()=="All pages": return list(range(total))
4996:             raw=page_range.get().strip()
4997:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
4998:             selected=[]
4999:             for part in raw.split(","):
```
```text
4996:             raw=page_range.get().strip()
4997:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
4998:             selected=[]
4999:             for part in raw.split(","):
5000:                 part=part.strip()
5001:                 if "-" in part:
5002:                     a,b=part.split("-",1); a=int(a); b=int(b)
5003:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5004:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5005:                     selected.extend(range(a-1,b))
5006:                 else:
5007:                     n=int(part)
5008:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5009:                     selected.append(n-1)
5010:             return list(dict.fromkeys(selected))
5011: 
5012:         def selected_printer():
5013:             sel=printer_list.curselection()
5014:             return printer_list.get(sel[0]) if sel else printers[0]
5015: 
5016:         def print_rendered_pages():
```
```text
5109:                 finally:
5110:                     if hprinter is not None:
5111:                         try: win32print.ClosePrinter(hprinter)
5112:                         except Exception: pass
5113:                     if hdc:
5114:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5115:                         except Exception: pass
5116: 
5117:                 # Print the exact rendered PDF page through the printer DC.
5118:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5119:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5120:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5121:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5122: 
5123:                 for copy_no in range(count):
5124:                     dc.StartDoc(str(title)[:80])
5125:                     doc_ok=False
5126:                     try:
5127:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5128:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5129:                             dc.StartPage()
```
```text
5128:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5129:                             dc.StartPage()
5130:                             page_ok=False
5131:                             try:
5132:                                 cell_w=printable_w/float(cols_n)
5133:                                 cell_h=printable_h/float(rows_n)
5134:                                 for j,page_index in enumerate(batch):
5135:                                     page=doc.load_page(page_index)
5136:                                     pdf_w=max(1.0,float(page.rect.width))
5137:                                     pdf_h=max(1.0,float(page.rect.height))
5138:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5139:                                     fit=max(0.25,min(fit,8.0))
5140:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5141:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5142:                                     target_w=max(1,int(cell_w*0.96))
5143:                                     target_h=max(1,int(cell_h*0.96))
5144:                                     ratio=min(target_w/img.width,target_h/img.height)
5145:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5146:                                     if (nw,nh)!=(img.width,img.height):
5147:                                         img=img.resize((nw,nh),Image.LANCZOS)
5148:                                     dib=ImageWin.Dib(img)
```
```text
5168: 
5169:                 status.set("Print job sent successfully")
5170:                 win.update_idletasks()
5171:                 win.after(500,close)
5172:             except Exception as e:
5173:                 status.set("Print failed: "+str(e))
5174:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5175: 
5176:         def close():
5177:             try: doc.close()
5178:             except Exception: pass
5179:             try: win.destroy()
5180:             except Exception: pass
5181:             # Only the temporary PDF created by the Print button is removed.
5182:             # Existing report PDFs passed through the legacy print path are preserved.
5183:             try:
5184:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5185:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5186:             except Exception: pass
5187: 
5188:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5184:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5185:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5186:             except Exception: pass
5187: 
5188:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5189:         bottom.winfo_children()[1].configure(command=close)
5190:         print_btn.configure(command=print_rendered_pages)
5191:         win.protocol("WM_DELETE_WINDOW",close)
5192:         win.bind("<Escape>",lambda e:close())
5193:         win.grab_set()
5194:         # Keep the requested printer defaults visibly selected; no manual
5195:         # adjustment is required before pressing Print.
5196:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5197:         win.after(120,lambda:render_preview(0))
5198:         win.focus_force()
5199: 
5200:     def print_pdf(self,path):
5201:         """Open a printer-selection window for a generated PDF."""
5202:         path=os.path.abspath(path)
5203:         if not os.path.exists(path):
5204:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5200:     def print_pdf(self,path):
5201:         """Open a printer-selection window for a generated PDF."""
5202:         path=os.path.abspath(path)
5203:         if not os.path.exists(path):
5204:             messagebox.showwarning("Print", "The report file could not be found.")
5205:             return
5206: 
5207:         if sys.platform.startswith("win"):
5208:             self._select_windows_printer_for_pdf(path)
5209:             return
5210: 
5211:         try:
5212:             subprocess.run(["lp", path], check=True)
5213:         except Exception as e:
5214:             messagebox.showwarning(
5215:                 "Print",
5216:                 "The operating system could not start printing.\n\n"
5217:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5218:             )
5219: 
5220:     def open_file(self,path):
```
```text
5215:                 "Print",
5216:                 "The operating system could not start printing.\n\n"
5217:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5218:             )
5219: 
5220:     def open_file(self,path):
5221:         try:
5222:             if sys.platform.startswith("win"): os.startfile(path)
5223:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5224:             else: subprocess.Popen(["xdg-open",path])
5225:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5226: 
5227:     def print_demand(self,no):
5228:         data=self._get_doc_data("demand",no)
5229:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5230:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5231:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5232:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5233: 
5234:     def print_grr(self,no):
5235:         data=self._get_doc_data("grr",no)
```
```text
5229:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5230:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5231:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5232:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5233: 
5234:     def print_grr(self,no):
5235:         data=self._get_doc_data("grr",no)
5236:         if not data:return messagebox.showwarning("Document","GRN not found.")
5237:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5238:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5239:         # GRN has a wide item table. Generate the PDF itself in landscape so
5240:         # the printer dialog and printer driver receive a landscape document
5241:         # instead of a portrait page with rotated/cropped content.
5242:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5243: 
5244:     def print_issue(self,no):
5245:         data=self._get_doc_data("issue",no)
5246:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5247:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5248:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5249:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
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
