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

- Lines: 371
- Functions: _safe_json_value(24-27), _table_columns(28-29), snapshot_db(30-38), _row_key(39-43), _index_snapshot(44-48), merge_local_changes(49-70), _snapshot_has_records(71-73), __init__(75-91), _read_url(92-102), status_text(103-108), _request(109-118), _get_meta(119-125), _get_snapshot(126-132), _load_json(133-141), _atomic_save_json(142-156), _save_state(157-161), _save_pending(162-166), _clear_pending(167-172), _get_lock_etag(173-182), _try_acquire_lock(183-189), _release_lock(190-198), initialize(199-247), replace_local(248-265), _write_remote(266-287), push_changes(288-307), maybe_pull(308-329), __init__(331-336), execute(337-345), executemany(346-350), commit(351-360), rollback(362-365), close(366-367), backup(368-369), __getattr__(370-371)

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
0205:         # A pending snapshot is the strongest local recovery source.
0206:         if isinstance(pending, dict) and isinstance(pending.get("snapshot"), dict):
0207:             local = pending["snapshot"]
0208:             self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
0209:         try:
0210:             remote = self._get_snapshot()
0211:             version, _ = self._get_meta()
```
```text
0205:         # A pending snapshot is the strongest local recovery source.
0206:         if isinstance(pending, dict) and isinstance(pending.get("snapshot"), dict):
0207:             local = pending["snapshot"]
0208:             self.pending_base = pending.get("baseline") if isinstance(pending.get("baseline"), dict) else state
0209:         try:
0210:             remote = self._get_snapshot()
0211:             version, _ = self._get_meta()
0212:             if remote and remote.get("tables"):
0213:                 # Never discard a non-empty local database just because the
0214:                 # cloud has an older/partial snapshot. Merge local rows into
0215:                 # remote on startup, then publish the merged result.
0216:                 empty = {"schema": 1, "tables": {}}
0217:                 baseline = self.pending_base or empty
0218:                 if _snapshot_has_records(local) or self.pending_base is not None:
0219:                     merged = merge_local_changes(remote, baseline, local)
0220:                     if merged != remote:
0221:                         new_version = self._write_remote(merged)
0222:                         self.replace_local(conn, merged)
0223:                         self.last_remote_version = new_version
0224:                         self._save_state(merged)
0225:                     else:
```
```text
0220:                     if merged != remote:
0221:                         new_version = self._write_remote(merged)
0222:                         self.replace_local(conn, merged)
0223:                         self.last_remote_version = new_version
0224:                         self._save_state(merged)
0225:                     else:
0226:                         self.replace_local(conn, remote)
0227:                         self.last_remote_version = version
0228:                         self._save_state(remote)
0229:                 else:
0230:                     self.replace_local(conn, remote)
0231:                     self.last_remote_version = version
0232:                     self._save_state(remote)
0233:                 self.pending_base = None
0234:                 self.pending_error = None
0235:                 self._clear_pending()
0236:             else:
0237:                 new_version = self._write_remote(local)
0238:                 self.last_remote_version = new_version
0239:                 self._save_state(local)
0240:                 self._clear_pending()
```
```text
0236:             else:
0237:                 new_version = self._write_remote(local)
0238:                 self.last_remote_version = new_version
0239:                 self._save_state(local)
0240:                 self._clear_pending()
0241:                 self.pending_base = None
0242:                 self.pending_error = None
0243:         except Exception as exc:
0244:             # Firebase being offline must never delete the local data. Keep
0245:             # the local snapshot and retry on the next start/commit.
0246:             self.pending_error = str(exc)
0247:             self._save_pending(local, self.pending_base or state or {"schema": 1, "tables": {}})
0248:     def replace_local(self, conn: sqlite3.Connection, snapshot: Dict[str, Any]) -> None:
0249:         old_isolation = conn.isolation_level
0250:         try:
0251:             conn.execute("BEGIN")
0252:             for table in TABLES:
0253:                 cols = _table_columns(conn, table)
0254:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0255:                 conn.execute(f"DELETE FROM {table}")
0256:                 if not rows:
```
```text
0252:             for table in TABLES:
0253:                 cols = _table_columns(conn, table)
0254:                 rows = snapshot.get("tables", {}).get(table, {}).get("rows", []) or []
0255:                 conn.execute(f"DELETE FROM {table}")
0256:                 if not rows:
0257:                     continue
0258:                 insert_cols = [c for c in cols if c in rows[0]]
0259:                 placeholders = ",".join("?" for _ in insert_cols)
0260:                 sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0261:                 for row in rows:
0262:                     conn.execute(sql, [row.get(c) for c in insert_cols])
0263:             conn.commit()
0264:         finally:
0265:             conn.isolation_level = old_isolation
0266:     def _write_remote(self, snapshot: Dict[str, Any]) -> str:
0267:         token = f"{self.client_id}-{uuid.uuid4().hex}"
0268:         acquired = False
0269:         last_exc = None
0270:         for _ in range(10):
0271:             try:
0272:                 if self._try_acquire_lock(token):
```
```text
0271:             try:
0272:                 if self._try_acquire_lock(token):
0273:                     acquired = True
0274:                     break
0275:             except Exception as exc:
0276:                 last_exc = exc
0277:             time.sleep(0.35)
0278:         if not acquired:
0279:             raise RuntimeError(f"Could not acquire Firebase sync lock. {last_exc or ''}".strip())
0280:         try:
0281:             new_version = f"{time.time_ns()}-{self.client_id}"
0282:             self._request("PUT", "store_inventory/data.json", json=snapshot)
0283:             self._request("PUT", "store_inventory/_meta/version.json", json=new_version)
0284:             self._request("PUT", "store_inventory/_meta/updated_by.json", json=self.client_id)
0285:             return new_version
0286:         finally:
0287:             self._release_lock(token)
0288:     def push_changes(self, conn: sqlite3.Connection, baseline: Dict[str, Any]) -> bool:
0289:         if not self.enabled:
0290:             return True
0291:         local = snapshot_db(conn)
```
```text
0292:         try:
0293:             remote = self._get_snapshot() or {"schema": 1, "tables": {}}
0294:             merged = merge_local_changes(remote, baseline or {"schema": 1, "tables": {}}, local)
0295:             new_version = self._write_remote(merged)
0296:             self.replace_local(conn, merged)
0297:             self.last_remote_version = new_version
0298:             self.pending_base = None
0299:             self.pending_error = None
0300:             self._save_state(merged)
0301:             self._clear_pending()
0302:             return True
0303:         except Exception as exc:
0304:             self.pending_base = deepcopy(baseline)
0305:             self.pending_error = str(exc)
0306:             self._save_pending(local, baseline or {"schema": 1, "tables": {}})
0307:             return False
0308:     def maybe_pull(self, conn: sqlite3.Connection) -> bool:
0309:         if not self.enabled or self.pending_base is not None:
0310:             return False
0311:         now = time.monotonic()
0312:         if now - self.last_check < self.check_interval:
```
```text
0316:             version, _ = self._get_meta()
0317:             if not version or version == self.last_remote_version:
0318:                 return False
0319:             snapshot = self._get_snapshot()
0320:             if snapshot is None:
0321:                 return False
0322:             self.replace_local(conn, snapshot)
0323:             self.last_remote_version = version
0324:             self._save_state(snapshot)
0325:             self.pending_error = None
0326:             return True
0327:         except Exception as exc:
0328:             self.pending_error = str(exc)
0329:             return False
0330: class OnlineConnection:
0331:     def __init__(self, db_path: str, sync: FirebaseSync):
0332:         self._conn = sqlite3.connect(db_path, timeout=20)
0333:         self._conn.execute("PRAGMA busy_timeout=20000")
0334:         self.sync = sync
0335:         self._dirty = False
0336:         self._baseline: Optional[Dict[str, Any]] = None
```
```text
0329:             return False
0330: class OnlineConnection:
0331:     def __init__(self, db_path: str, sync: FirebaseSync):
0332:         self._conn = sqlite3.connect(db_path, timeout=20)
0333:         self._conn.execute("PRAGMA busy_timeout=20000")
0334:         self.sync = sync
0335:         self._dirty = False
0336:         self._baseline: Optional[Dict[str, Any]] = None
0337:     def execute(self, sql: str, params: Iterable[Any] = ()):
0338:         s = sql.lstrip().upper()
0339:         is_read = s.startswith("SELECT") or s.startswith("PRAGMA") or s.startswith("WITH") or s.startswith("EXPLAIN")
0340:         if is_read and not self._dirty and self._baseline is None:
0341:             self.sync.maybe_pull(self._conn)
0342:         elif not is_read and not self._dirty:
0343:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0344:             self._dirty = True
0345:         return self._conn.execute(sql, params)
0346:     def executemany(self, sql: str, seq_of_params):
0347:         if not self._dirty:
0348:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0349:             self._dirty = True
```
```text
0342:         elif not is_read and not self._dirty:
0343:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0344:             self._dirty = True
0345:         return self._conn.execute(sql, params)
0346:     def executemany(self, sql: str, seq_of_params):
0347:         if not self._dirty:
0348:             self._baseline = self.sync.pending_base or snapshot_db(self._conn)
0349:             self._dirty = True
0350:         return self._conn.executemany(sql, seq_of_params)
0351:     def commit(self):
0352:         self._conn.commit()
0353:         # Make local persistence independent of Firebase availability.
0354:         durable_local.save(self._conn)
0355:         if self._dirty:
0356:             self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
0357:             # push_changes may merge remote rows back into SQLite.
0358:             durable_local.save(self._conn)
0359:         self._dirty = False
0360:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0361: 
0362:     def rollback(self):
```
```text
0355:         if self._dirty:
0356:             self.sync.push_changes(self._conn, self._baseline or snapshot_db(self._conn))
0357:             # push_changes may merge remote rows back into SQLite.
0358:             durable_local.save(self._conn)
0359:         self._dirty = False
0360:         self._baseline = None if self.sync.pending_base is None else self.sync.pending_base
0361: 
0362:     def rollback(self):
0363:         self._conn.rollback()
0364:         self._dirty = False
0365:         self._baseline = None
0366:     def close(self):
0367:         self._conn.close()
0368:     def backup(self, target):
0369:         return self._conn.backup(target)
0370:     def __getattr__(self, name):
0371:         return getattr(self._conn, name)
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

- Lines: 5405
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-404), restore_database(405-422), stock(424-429), fmt_num(431-433), to_iso_date(435-444), to_display_date(446-454), fiscal_year_key(456-467), fiscal_year_range(469-472), normalize_code(474-482), format_code(484-493), attach_code_mask(495-521), set_digits(498-503), key(504-514), paste(516-519), bind_add_to_list(523-544), on_enter(526-537), __init__(548-565), _check_for_updates(567-572), _setup_style(574-610), _shade(613-618), on_close(620-625), redo_network_setup(627-643), backup_now(645-652), restore_backup(654-672), _ctrl_f(674-686), _open_exact_find_text_popup(688-733), do_find(709-718), close(719-726), _global_enter(735-747), wipe(749-750), login(752-781), do_login(767-778), change_password(783-833), save_password(805-827), logout(835-840), home(842-867), _restore_dashboard_after_internal_close(869-883), _ensure_mdi_host(885-906), _internal_window(908-994), normal_place(924-930), restore(931-938), maximize(939-945), minimize(946-961), close(962-987), open_inventory_codes_detail_flow(996-1014), open_inventory_codes_with_filters(1016-1030), open_inventory_codes_report_window(1032-1258), tbtn(1050-1055), balance_as_of(1112-1122), build_nav(1124-1146), selected_prefix(1148-1157), load(1159-1191), page_move(1193-1194), page_first(1195-1195), page_last(1196-1200), on_nav(1204-1205), find_popup(1208-1227), search_fn(1210-1225), print_report(1230-1233), export_pdf(1235-1237), export_word(1238-1240), export_excel(1241-1243), open_menu_window(1260-1282), close_window(1270-1277), _manual_check_update(1284-1288), _show_current_version(1290-1294), build_menu_bar(1296-1343), open_calendar_picker(1345-1393), pick(1363-1365), redraw(1367-1379), nav(1381-1385), make_date_field(1395-1402), clearbody(1404-1430), run_action(1419-1424), _portable_print_current(1432-1443), portable_print_dialog(1445-1518), build_receipt(1472-1490), send(1491-1504), refresh_printers(1505-1511), preview_tree(1520-1532), set_page_actions(1534-1542), _add_transaction_new_button(1544-1561), _report_header(1563-1627), _report_footer(1629-1635), _grr_signature_block(1637-1653), _finish_page(1655-1656), _wrap_text_to_width(1658-1683), fits(1665-1665), _pdf_table_report(1685-1754), table_header(1707-1712), show_preview_window(1756-1829), _safe_report_name(1831-1834), print_preview_window(1836-1839), _fallback_pdf_export(1841-1874), esc(1845-1846), add(1849-1851), _save_entry_report(1876-1896), export_preview_pdf(1898-1927), export_preview_word(1929-1969), export_preview_excel(1971-2007), make_tree(2009-2018), pick_item(2020-2041), choose(2021-2040), ld(2028-2032), sel(2034-2038), bind_item_lookup(2043-2060), lookup(2045-2058), _set_form_editable(2063-2076), walk(2066-2075), document_selector(2078-2112), refresh(2083-2094), selected(2095-2100), dashboard(2114-2226), load_details(2198-2222), _refresh_dashboard_kpis(2228-2242), dashboard_details(2244-2248), item_history(2250-2270), _ask_item_master_filters(2272-2356), finish(2325-2337), items(2358-2596), hierarchy(2399-2408), selected_prefix(2454-2467), balance_as_of(2469-2476), load(2478-2516), set_page(2518-2519), select_node(2521-2542), open_find(2548-2567), search_fn(2550-2565), visible_rows(2572-2574), print_inventory(2575-2579), export_inventory_word(2580-2582), export_inventory_excel(2583-2585), portable_inventory(2590-2592), inventory_codes(2598-2882), btn(2634-2639), close_editor(2675-2685), edit_cell(2687-2713), commit(2705-2711), rows_query(2715-2728), load(2730-2745), new_record(2747-2768), commit(2761-2765), selected_row(2770-2772), edit_record(2774-2782), save_record(2784-2827), delete_record(2829-2840), refresh(2842-2842), do_print(2843-2845), do_close(2846-2846), filter_grid(2864-2871), open_mto_inventory_flow(2884-2907), open_code_opening_flow(2909-2917), code_opening(2919-2920), _open_code_opening_popup(2922-2923), _open_code_opening_detail(2925-3168), norm(2995-2996), table_for(2998-2999), row_for(3001-3006), search_any_destination(3008-3021), desc_hit(3023-3027), clear_form(3029-3042), load_for_edit(3044-3065), check_duplicates(3067-3078), save_code(3083-3134), edit_action(3136-3140), delete_code(3142-3157), _mto_new_item_dialog(3170-3206), save(3186-3203), _item_filter_bar(3208-3220), _date_filter_bar(3222-3230), _ask_mto_inventory_filters(3232-3277), finish(3262-3270), mto_inventory(3279-3479), open_find(3313-3332), search_fn(3315-3330), hierarchy(3351-3355), rebuild_nav(3357-3368), mto_balance(3392-3401), load(3403-3445), set_page(3447-3447), select_node(3448-3457), visible_rows(3462-3462), do_print(3463-3467), export_word(3468-3470), export_excel(3471-3473), party_master(3481-3532), load(3491-3494), clear(3495-3499), new_form(3500-3501), save(3502-3508), load_party_row(3509-3513), on_party_select(3514-3515), edit(3517-3521), delete_party(3522-3528), user_management(3534-3618), sync_role(3561-3566), load(3570-3573), clear(3574-3577), edit(3578-3585), save(3586-3603), delete_user(3604-3615), _renumber_tree(3621-3624), demand(3626-3790), _restore_demand_tree_columns(3669-3675), add(3678-3686), edit_item(3688-3700), delete_item(3702-3710), new_form(3714-3720), save(3722-3738), delete_current(3742-3748), cancel_form(3749-3757), preview_now(3758-3768), edit_saved_demand(3769-3772), print_now(3773-3783), load_demand_into_form(3792-3804), refresh_saved_cache(3806-3818), grr(3820-3983), add(3852-3860), edit_item(3862-3872), delete_item(3874-3882), new_form(3886-3892), save(3894-3915), delete_current(3919-3925), cancel_form(3926-3934), preview_now(3935-3953), portable_current(3954-3957), edit_saved_grr(3959-3962), print_now(3963-3976), load_grr_into_form(3985-3997), issue(3999-4145), old_issue_qty(4028-4031), update_balance(4032-4040), add(4042-4051), edit_item(4053-4064), new_form(4068-4074), post(4076-4097), delete_current(4098-4104), cancel_form(4105-4113), preview_now(4114-4121), portable_current(4122-4124), load_saved_issue(4129-4131), edit_saved_issue(4132-4135), print_issue_now(4136-4141), load_issue_into_form(4147-4160), _ask_report_criteria(4162-4225), finish(4211-4219), _open_report_child(4227-4232), open_stock_balance_report_flow(4234-4237), open_grr_report_flow(4239-4242), open_demand_report_flow(4244-4247), open_issue_report_flow(4249-4252), open_party_report_flow(4254-4257), _ask_stock_balance_filters(4259-4282), ok(4274-4275), cancel(4276-4276), stock_balance(4284-4347), period(4300-4311), header_summary(4312-4313), load(4314-4323), reopen_filters(4324-4328), open_find_stock(4332-4345), search_fn(4334-4344), ledger(4349-4361), open_document_editor(4363-4371), _edit_from_selector(4373-4389), show_saved_records(4391-4422), view(4414-4418), documents(4424-4469), edit_selected(4443-4449), delete_selected(4450-4462), doc_export_selected(4471-4477), doc_preview_selected(4479-4489), doc_print_selected(4491-4499), load_document(4501-4531), _print_loaded_document(4525-4530), _report_filter_popup(4533-4550), ok(4546-4547), cancel(4548-4548), _report_window(4552-4596), load(4565-4572), hdr(4573-4573), open_find_report(4579-4593), search_fn(4581-4592), report_grr(4598-4609), pb(4600-4608), report_demand(4611-4622), pb(4613-4621), report_issue(4624-4633), pb(4626-4632), report_party(4635-4645), pb(4637-4644), reports(4647-4775), load_grr_item(4660-4665), load_grr_date(4673-4681), load_party(4693-4701), load_dem_item(4714-4719), load_dem_date(4727-4735), load_iss_item(4749-4754), load_iss_date(4762-4770), print_item_master(4777-4779), print_party_master(4781-4783), print_report(4785-4799), print_stock(4801-4806), print_ledger(4808-4815), _get_doc_data(4817-4845), export_word(4847-4894), export_excel(4896-4936), preview_pdf(4938-4946), _open_direct_printer(4948-4978), _select_windows_printer_for_pdf(4980-5351), render_preview(5105-5124), on_resize(5126-5128), parse_page_selection(5147-5163), selected_printer(5165-5167), print_rendered_pages(5169-5327), close(5329-5339), print_pdf(5353-5371), open_file(5373-5378), print_demand(5380-5385), print_grr(5387-5395), print_issue(5397-5402)

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
0397:             return None
0398:         with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
0399:             z.write(dated, "store_inventory.db")
0400:         if not os.path.isfile(zpath) or os.path.getsize(zpath) <= 0:
0401:             return None
0402:         return zpath
0403:     except Exception:
0404:         return None
0405: def restore_database(backup_path):
0406:     """Restore the database from a .db or .zip backup file. The current
0407:     database is itself backed up first, so a restore can never destroy data."""
0408:     try:
0409:         backup_database(manual=True)  # safety net before touching anything
0410:         if backup_path.lower().endswith(".zip"):
0411:             with zipfile.ZipFile(backup_path,"r") as z:
0412:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0413:                 os.makedirs(tmp_dir,exist_ok=True)
0414:                 z.extractall(tmp_dir)
0415:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0416:                 shutil.copy2(extracted,DB)
0417:                 shutil.rmtree(tmp_dir,ignore_errors=True)
```
```text
0411:             with zipfile.ZipFile(backup_path,"r") as z:
0412:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0413:                 os.makedirs(tmp_dir,exist_ok=True)
0414:                 z.extractall(tmp_dir)
0415:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0416:                 shutil.copy2(extracted,DB)
0417:                 shutil.rmtree(tmp_dir,ignore_errors=True)
0418:         else:
0419:             shutil.copy2(backup_path,DB)
0420:         return True
0421:     except Exception:
0422:         return False
0423: 
0424: def stock(c, code):
0425:     r=c.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()
0426:     q=float(r[0] or 0) if r else 0
0427:     for typ,qty in c.execute("SELECT doc_type,qty FROM transactions WHERE code=? ORDER BY id", (code,)):
0428:         q += float(qty or 0) if typ=="GRR" else -float(qty or 0) if typ=="ISSUE" else 0
0429:     return q
0430: 
0431: def fmt_num(x):
```
```text
0429:     return q
0430: 
0431: def fmt_num(x):
0432:     x=float(x or 0)
0433:     return f"{x:,.2f}".rstrip("0").rstrip(".")
0434: 
0435: def to_iso_date(s):
0436:     """Convert a user-entered DD/MM/YYYY date (or an already-ISO date) into
0437:     ISO YYYY-MM-DD for storage in the database and for date-range queries,
0438:     which rely on ISO strings sorting/comparing correctly."""
0439:     s=(s or "").strip()
0440:     if not s: return ""
0441:     for f in ("%d/%m/%Y","%Y-%m-%d"):
0442:         try: return datetime.strptime(s,f).strftime("%Y-%m-%d")
0443:         except Exception: continue
0444:     return s
0445: 
0446: def to_display_date(s):
0447:     """Convert an ISO YYYY-MM-DD date (as stored in the database) into the
0448:     DD/MM/YYYY format used everywhere on screen and on printed reports."""
0449:     s=(s or "").strip()
```
```text
0544:     return on_enter
0545: 
0546: 
0547: class App(tk.Tk):
0548:     def __init__(self):
0549:         super().__init__()
0550:         self.title("Store Inventory Management System | SAP Style")
0551:         self.geometry("1400x820"); self.minsize(1150,700)
0552:         self.conn=connect()
0553:         self.demand_lines=[]; self.grr_lines=[]; self.issue_lines=[]
0554:         self.current_user=None; self.current_role=None
0555:         self._item_master_search_entry=None
0556:         self._item_master_find_callback=None
0557:         self._portable_print_context=None
0558:         self.can_edit=False; self.can_delete=False; self.is_admin=False
0559:         self._setup_style()
0560:         # Any focused button can be activated with Enter.
0561:         self.bind_all("<Return>", self._global_enter, add="+")
0562:         self.bind_all("<KP_Enter>", self._global_enter, add="+")
0563:         self.bind_all("<Control-f>", self._ctrl_f, add="+")
0564:         self.protocol("WM_DELETE_WINDOW", self.on_close)
```
```text
0612:     @staticmethod
0613:     def _shade(hexcolor, factor):
0614:         """Return a slightly darker version of a #RRGGBB color (for hover/press states)."""
0615:         h=hexcolor.lstrip("#")
0616:         r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
0617:         r,g,b=(max(0,int(v*factor)) for v in (r,g,b))
0618:         return f"#{r:02x}{g:02x}{b:02x}"
0619: 
0620:     def on_close(self):
0621:         try:
0622:             self.conn.commit(); backup_database()
0623:         except Exception:
0624:             pass
0625:         self.destroy()
0626: 
0627:     def redo_network_setup(self):
0628:         if not messagebox.askyesno("Network Setup",
0629:             "This will clear the online database URL saved on this computer.\n\n"
0630:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0631:             "Continue?"):
0632:             return
```
```text
0626: 
0627:     def redo_network_setup(self):
0628:         if not messagebox.askyesno("Network Setup",
0629:             "This will clear the online database URL saved on this computer.\n\n"
0630:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0631:             "Continue?"):
0632:             return
0633:         try:
0634:             self.conn.commit(); backup_database()
0635:         except Exception:
0636:             pass
0637:         try:
0638:             if os.path.exists(FIREBASE_URL_FILE): os.remove(FIREBASE_URL_FILE)
0639:         except Exception:
0640:             pass
0641:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0642:         self.destroy()
0643:         sys.exit(0)
0644: 
0645:     def backup_now(self):
0646:         path=backup_database(manual=True)
```
```text
0640:             pass
0641:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0642:         self.destroy()
0643:         sys.exit(0)
0644: 
0645:     def backup_now(self):
0646:         path=backup_database(manual=True)
0647:         if path:
0648:             messagebox.showinfo("Backup Complete",
0649:                 f"A full backup was saved to:\n\n{path}\n\n"
0650:                 f"All backups are kept in:\n{BACKUP_DIR}")
0651:         else:
0652:             messagebox.showerror("Backup Failed","Could not create a backup. Make sure the database exists.")
0653: 
0654:     def restore_backup(self):
0655:         from tkinter import filedialog
0656:         if not messagebox.askyesno("Restore Backup",
0657:             "This will replace all current data with the selected backup.\n"
0658:             "A safety backup of the current data will be made first.\n\n"
0659:             "Continue?"):
0660:             return
```
```text
0654:     def restore_backup(self):
0655:         from tkinter import filedialog
0656:         if not messagebox.askyesno("Restore Backup",
0657:             "This will replace all current data with the selected backup.\n"
0658:             "A safety backup of the current data will be made first.\n\n"
0659:             "Continue?"):
0660:             return
0661:         path=filedialog.askopenfilename(
0662:             title="Select a backup file",
0663:             initialdir=BACKUP_DIR,
0664:             filetypes=[("Backup files","*.zip *.db"),("All files","*.*")])
0665:         if not path: return
0666:         if restore_database(path):
0667:             messagebox.showinfo("Restore Complete",
0668:                 "Data has been restored. The application will now restart.")
0669:             self.conn.close()
0670:             os.execv(sys.executable, [sys.executable]+sys.argv)
0671:         else:
0672:             messagebox.showerror("Restore Failed","Could not restore from that backup file.")
0673: 
0674:     def _ctrl_f(self, event=None):
```
```text
0711:             if not text:
0712:                 fe.focus_set(); return
0713:             try:
0714:                 found=search_fn(text)
0715:             except Exception:
0716:                 found=False
0717:             if found is False:
0718:                 messagebox.showinfo("Find Text","No matching text found.",parent=dlg)
0719:         def close():
0720:             try:
0721:                 dlg.grab_release()
0722:             except Exception: pass
0723:             try: dlg.destroy()
0724:             except Exception: pass
0725:             if getattr(self,"_exact_find_text_dialog",None) is dlg:
0726:                 self._exact_find_text_dialog=None
0727:         ttk.Button(box,text="Find Next",command=do_find,width=13).grid(row=0,column=3,padx=4,pady=4)
0728:         ttk.Button(box,text="Cancel",command=close,width=13).grid(row=1,column=3,padx=4,pady=4)
0729:         fe.bind("<Return>",lambda e:(do_find(),"break"))
0730:         dlg.bind("<Escape>",lambda e:close())
0731:         dlg.protocol("WM_DELETE_WINDOW",close)
```
```text
0797:         cur_ent=ttk.Entry(box,textvariable=current,width=28,show="*"); cur_ent.grid(row=2,column=1,pady=7)
0798:         ttk.Label(box,text="New Password").grid(row=3,column=0,sticky="w",pady=7)
0799:         new_ent=ttk.Entry(box,textvariable=new,width=28,show="*"); new_ent.grid(row=3,column=1,pady=7)
0800:         ttk.Label(box,text="Confirm New Password").grid(row=4,column=0,sticky="w",pady=7)
0801:         conf_ent=ttk.Entry(box,textvariable=confirm,width=28,show="*"); conf_ent.grid(row=4,column=1,pady=7)
0802:         err=ttk.Label(box,text="",foreground="#c0392b",wraplength=380,justify="left")
0803:         err.grid(row=5,column=0,columnspan=2,pady=(5,8))
0804: 
0805:         def save_password(event=None):
0806:             old_pw=current.get()
0807:             new_pw=new.get()
0808:             confirm_pw=confirm.get()
0809:             row=self.conn.execute("SELECT password FROM users WHERE username=?",(self.current_user,)).fetchone()
0810:             if not row or not verify_password(old_pw,row[0]):
0811:                 err.config(text="Current password is incorrect."); return
0812:             if len(new_pw) < 4:
0813:                 err.config(text="New password must be at least 4 characters."); return
0814:             if new_pw != confirm_pw:
0815:                 err.config(text="New password and confirmation do not match."); return
0816:             if new_pw == old_pw:
0817:                 err.config(text="New password must be different from the current password."); return
```
```text
0813:                 err.config(text="New password must be at least 4 characters."); return
0814:             if new_pw != confirm_pw:
0815:                 err.config(text="New password and confirmation do not match."); return
0816:             if new_pw == old_pw:
0817:                 err.config(text="New password must be different from the current password."); return
0818:             try:
0819:                 self.conn.execute("UPDATE users SET password=? WHERE username=?",
0820:                                   (hash_password(new_pw),self.current_user))
0821:                 self.conn.commit()
0822:                 backup_database()
0823:                 win.grab_release(); win.destroy()
0824:                 messagebox.showinfo("Password Changed",
0825:                     "Your password has been changed successfully.\n\nUse the new password the next time you log in.", parent=self)
0826:             except Exception as ex:
0827:                 err.config(text=f"Could not change password: {ex}")
0828: 
0829:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0830:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0831:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0832:         conf_ent.bind("<Return>",save_password)
0833:         cur_ent.focus_set()
```
```text
0829:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0830:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0831:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0832:         conf_ent.bind("<Return>",save_password)
0833:         cur_ent.focus_set()
0834: 
0835:     def logout(self):
0836:         try:
0837:             self.conn.commit(); backup_database()
0838:         except Exception:
0839:             pass
0840:         self.login()
0841: 
0842:     def home(self):
0843:         self.wipe()
0844:         self.build_menu_bar()
0845:         hdr=tk.Frame(self,bg=COLORS["primary_dark"]);hdr.pack(fill="x")
0846:         self._shell_header=hdr
0847:         inner=tk.Frame(hdr,bg=COLORS["primary_dark"],padx=16,pady=10);inner.pack(fill="x")
0848:         tk.Label(inner,text=COMPANY,font=("Segoe UI",16,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="left")
0849:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
```
```text
0849:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
0850:         tk.Label(inner,text=f"Data: {DATA_DIR}",font=("Segoe UI",8),bg=COLORS["primary_dark"],fg="#9FB8DA").pack(side="left",padx=14)
0851:         ttk.Button(inner,text="Logout",style="Danger.TButton",command=self.logout).pack(side="right")
0852:         tk.Label(inner,text=f"{self.current_user}  ({self.current_role})",font=("Segoe UI",9,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="right",padx=12)
0853:         nav=tk.Frame(self,bg=COLORS["primary"]);nav.pack(fill="x")
0854:         self._shell_nav=nav
0855:         navin=tk.Frame(nav,bg=COLORS["primary"],padx=10,pady=6);navin.pack(fill="x")
0856:         ttk.Button(navin,text="🏠  Dashboard",style="Accent.TButton",command=self.dashboard).pack(side="left",padx=3)
0857:         tk.Label(navin,text="Inventory  |  Transaction  |  Report  |  Edit  |  Help  —  see the menu bar above for every other section.",
0858:                  font=("Segoe UI",8),bg=COLORS["primary"],fg="#E7EFFB").pack(side="left",padx=14)
0859:         self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
0860:         self.main_body=self.body
0861:         self.dashboard()
0862:         if not getattr(self, "_update_checked_this_session", False):
0863:             self._update_checked_this_session = True
0864:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0865:         if not getattr(self, "_update_checked_this_session", False):
0866:             self._update_checked_this_session = True
0867:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0868: 
0869:     def _restore_dashboard_after_internal_close(self):
```
```text
0954:             b.pack(side="left")
0955:             rb=tk.Button(item,text="□",font=("Segoe UI",8,"bold"),width=2,height=1,padx=0,pady=0,
0956:                          command=lambda:(restore(),maximize()),relief="flat",bd=0,bg="#e7e7e7")
0957:             rb.pack(side="left")
0958:             xb=tk.Button(item,text="×",font=("Segoe UI",9,"bold"),width=2,height=1,padx=0,pady=0,
0959:                          command=close,relief="flat",bd=0,bg="#e7e7e7")
0960:             xb.pack(side="left")
0961:             state["task"]=item
0962:         def close():
0963:             try:
0964:                 task=state.get("task")
0965:                 if task and task.winfo_exists(): task.destroy()
0966:             except Exception: pass
0967:             try:
0968:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
0969:             except Exception: pass
0970:             try: outer.destroy()
0971:             except Exception: pass
0972:             if not getattr(self,"_mdi_windows",[]):
0973:                 self._mdi_host.place_forget()
0974:                 self._restore_dashboard_after_internal_close()
```
```text
0967:             try:
0968:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
0969:             except Exception: pass
0970:             try: outer.destroy()
0971:             except Exception: pass
0972:             if not getattr(self,"_mdi_windows",[]):
0973:                 self._mdi_host.place_forget()
0974:                 self._restore_dashboard_after_internal_close()
0975:                 self._restore_dashboard_after_internal_close()
0976:                 # Restore the original application shell FIRST, then rebuild
0977:                 # only the Dashboard body. This keeps the top header/navigation
0978:                 # exactly as they are when the application starts.
0979:                 try:
0980:                     if getattr(self,"_shell_header",None) is not None and self._shell_header.winfo_exists():
0981:                         self._shell_header.pack(fill="x",before=self.body)
0982:                     if getattr(self,"_shell_nav",None) is not None and self._shell_nav.winfo_exists():
0983:                         self._shell_nav.pack(fill="x",before=self.body,after=self._shell_header)
0984:                 except Exception: pass
0985:                 try:
0986:                     self.dashboard()
0987:                 except Exception: pass
```
```text
1020:             return None
1021:         self._inventory_codes_filter=criteria
1022:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1023:         try:
1024:             self.items(container=body)
1025:             win.lift()
1026:             return win
1027:         except Exception:
1028:             try: win._internal_close()
1029:             except Exception: pass
1030:             raise
1031: 
1032:     def open_inventory_codes_report_window(self, criteria=None):
1033:         """Open Inventory Codes as a real report-style child window.
1034: 
1035:         This intentionally mirrors the supplied Preview Report workflow: a
1036:         separate resizable/maximizable window with a left navigation tree,
1037:         compact report toolbar, Find dialog, and print/export commands.
1038:         The main application remains open behind it.
1039:         """
1040:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
1037:         compact report toolbar, Find dialog, and print/export commands.
1038:         The main application remains open behind it.
1039:         """
1040:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
1041:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
1042:         }
1043:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1044: 
1045:         # --- report-style toolbar ---
1046:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
1047:         toolbar.pack(fill="x",side="top")
1048:         toolbar.pack_propagate(False)
1049: 
1050:         def tbtn(text,cmd,width=9):
1051:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
1052:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
1053:                          padx=3,pady=1)
1054:             b.pack(side="left",padx=2,pady=6)
1055:             return b
1056: 
1057:         # --- main report body ---
```
```text
1068:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
1069:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
1070:         navscroll.config(command=code_tree.yview)
1071:         navscroll.pack(side="right",fill="y")
1072:         code_tree.pack(side="left",fill="both",expand=True)
1073: 
1074:         right=tk.Frame(content,bg="#EDEDED")
1075:         right.pack(side="left",fill="both",expand=True)
1076:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
1077:         reportbar.pack(fill="x")
1078:         reportbar.pack_propagate(False)
1079:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
1080:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
1081:         tab.pack(side="left",padx=4,pady=2)
1082:         titlevar=tk.StringVar(value="Inventory Summary")
1083:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
1084:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
1085: 
1086:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
1087:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
1088:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1222:                     vals=tree.item(iid,"values")
1223:                     if str(vals[1]).lower()==str(target).lower():
1224:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1225:                 return True
1226:             self._open_exact_find_text_popup(search_fn)
1227:             self._item_master_find_callback=find_popup
1228: 
1229: 
1230:         def print_report():
1231:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1232:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1233:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1234: 
1235:         def export_pdf():
1236:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1237:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1238:         def export_word():
1239:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1240:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1241:         def export_excel():
1242:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1238:         def export_word():
1239:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1240:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1241:         def export_excel():
1242:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1243:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1244: 
1245:         tbtn("Find",find_popup,7)
1246:         tbtn("Print",print_report,7)
1247:         tbtn("PDF",export_pdf,6)
1248:         tbtn("Word",export_word,6)
1249:         tbtn("Excel",export_excel,6)
1250:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1251:         tbtn("Refresh",load,8)
1252:         tbtn("Close",win._internal_close,7)
1253:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1254:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1255: 
1256:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1257:         build_nav(); load(); win.focus_force()
1258:         return win
```
```text
1268:         self.body=frame
1269:         closed={"done":False}
1270:         def close_window():
1271:             if closed["done"]: return
1272:             closed["done"]=True
1273:             if getattr(self,"body",None) is frame: self.body=old_body
1274:             self._page_actions=old_actions
1275:             self._item_master_find_callback=old_find
1276:             try: win._internal_close()
1277:             except Exception: win.destroy()
1278:         win._internal_close=close_window
1279:         try:
1280:             method(); self.update_idletasks(); win.lift(); return win
1281:         except Exception:
1282:             close_window(); raise
1283: 
1284:     def _manual_check_update(self):
1285:         try:
1286:             updater.check_for_update(self, manual=True)
1287:         except Exception as e:
1288:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1292:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1293:         except Exception as e:
1294:             messagebox.showerror("Current Version", str(e), parent=self)
1295: 
1296:     def build_menu_bar(self):
1297:         """Professional section / sub-section menu bar, ERP style:
1298:         Inventory > Item Master
1299:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1300:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1301:         Edit > Change Password, User Management
1302:         Help > Backup Now, Restore Backup, Network Setup
1303:         """
1304:         menubar=tk.Menu(self)
1305: 
1306:         m_inv=tk.Menu(menubar,tearoff=0)
1307:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1308:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1309:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1310:         menubar.add_cascade(label="Inventory",menu=m_inv)
1311: 
1312:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1312:         m_trans=tk.Menu(menubar,tearoff=0)
1313:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1314:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1315:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1316:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1317:         menubar.add_cascade(label="Transaction",menu=m_trans)
1318: 
1319:         m_rep=tk.Menu(menubar,tearoff=0)
1320:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1321:         m_rep.add_separator()
1322:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1323:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1324:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1325:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1326:         menubar.add_cascade(label="Report",menu=m_rep)
1327: 
1328:         m_edit=tk.Menu(menubar,tearoff=0)
1329:         m_edit.add_command(label="Change Password",command=self.change_password)
1330:         if self.is_admin:
1331:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1332:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1327: 
1328:         m_edit=tk.Menu(menubar,tearoff=0)
1329:         m_edit.add_command(label="Change Password",command=self.change_password)
1330:         if self.is_admin:
1331:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1332:         menubar.add_cascade(label="Edit",menu=m_edit)
1333: 
1334:         m_help=tk.Menu(menubar,tearoff=0)
1335:         m_help.add_command(label="Backup Now",command=self.backup_now)
1336:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1337:         m_help.add_command(label="Current Version",command=self._show_current_version)
1338:         if self.is_admin:
1339:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1340:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1341:         menubar.add_cascade(label="Help",menu=m_help)
1342: 
1343:         self.config(menu=menubar)
1344: 
1345:     def open_calendar_picker(self, var):
1346:         """Small month-grid calendar popup. Picking a day sets `var` to
1347:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1400:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1401:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1402:         return f
1403: 
1404:     def clearbody(self):
1405:         self._portable_print_context=None
1406:         for w in self.body.winfo_children(): w.destroy()
1407:         self._page_actions = {
1408:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1409:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1410:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1411:             "cancel": lambda: self.dashboard(),
1412:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1413:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1414:         }
1415:         # Single SAP-style toolbar at the very top.
1416:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1417:         self._page_action_bar=bar
1418:         self._page_action_first_button=None
1419:         def run_action(k):
1420:             if k=="edit" and not self.can_edit:
```
```text
1417:         self._page_action_bar=bar
1418:         self._page_action_first_button=None
1419:         def run_action(k):
1420:             if k=="edit" and not self.can_edit:
1421:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1422:             if k=="delete" and not self.can_delete:
1423:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1424:             self._page_actions[k]()
1425:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1426:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1427:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1428:             b.pack(side="left",padx=(0,2))
1429:             if self._page_action_first_button is None: self._page_action_first_button=b
1430:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1431: 
1432:     def _portable_print_current(self):
1433:         ctx=getattr(self,"_portable_print_context",None)
1434:         if not ctx:
1435:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1436:             return
1437:         try:
```
```text
1439:             if not data: return
1440:             title,header,columns,rows=data
1441:             self.portable_print_dialog(title,header,columns,rows)
1442:         except Exception as e:
1443:             messagebox.showerror("Portable Printer",str(e))
1444: 
1445:     def portable_print_dialog(self,title,header_lines,columns,rows):
1446:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1447:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1448:         if not WIN32PRINT_AVAILABLE:
1449:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1450:             return
1451:         try:
1452:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1453:         except Exception as e:
1454:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1455:             return
1456:         if not printers:
1457:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1458:             return
1459:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1509:                 if vals and pv.get() not in vals: pv.set(vals[0])
1510:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1511:             except Exception as ex: status.set(str(ex))
1512:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1513:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1514:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1515:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1516:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1517:         win.bind("<Escape>",lambda e:win._internal_close())
1518:         win.focus_force()
1519: 
1520:     def preview_tree(self, title, tree, header_lines=None):
1521:         """Preview the exact rows currently visible in a Treeview."""
1522:         cols=list(tree["columns"])
1523:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1524:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1525:         if not rows:
1526:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1527:             return
1528:         widths=[]
1529:         for c in cols:
```
```text
1526:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1527:             return
1528:         widths=[]
1529:         for c in cols:
1530:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1531:             except Exception: widths.append(100)
1532:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1533: 
1534:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1535:         self._page_actions.update({
1536:             "save": save or self._page_actions.get("save"),
1537:             "edit": edit or self._page_actions.get("edit"),
1538:             "delete": delete or self._page_actions.get("delete"),
1539:             "cancel": cancel or self._page_actions.get("cancel"),
1540:             "print": print or self._page_actions.get("print"),
1541:             "preview": preview or self._page_actions.get("preview"),
1542:         })
1543: 
1544:     def _add_transaction_new_button(self, command):
1545:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1546:         if bar is None or first is None: return
```
```text
1555:         sep.pack(side="left",fill="y",padx=4)
1556:         for w in existing:
1557:             try:
1558:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1559:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1560:                 else: w.pack(side="left")
1561:             except Exception: pass
1562: 
1563:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1564:         """Draw a consistent professional report header and return the first table Y.
1565: 
1566:         For GRN Receipt reports the document number is shown on the left and
1567:         the GRN Date is deliberately shown on the right in a bordered document
1568:         information panel.
1569:         """
1570:         W,H=page_size
1571:         if y_top is None: y_top=H-24
1572:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1573:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1574:         if os.path.exists(LOGO_FILE):
1575:             try:
```
```text
1568:         information panel.
1569:         """
1570:         W,H=page_size
1571:         if y_top is None: y_top=H-24
1572:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1573:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1574:         if os.path.exists(LOGO_FILE):
1575:             try:
1576:                 from reportlab.lib.utils import ImageReader
1577:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1578:             except Exception:
1579:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1580:         else:
1581:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1582:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1583:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1584:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1585:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1586: 
1587:         # Professional document information box.
1588:         info_top=logo_y-12
```
```text
1621:                 # naturally occupies the right-hand cell when supplied second.
1622:                 c.setFont("Helvetica-Bold",7)
1623:                 c.drawString(xx,yy,(label+":")[:28])
1624:                 c.setFont("Helvetica",7)
1625:                 c.drawString(xx+58,yy,val[:58])
1626:             return box_y-12
1627:         return info_top-6
1628: 
1629:     def _report_footer(self, c, page_no, page_size=A4):
1630:         W,H=page_size
1631:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1632:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1633:         c.drawString(24,13,REPORT_FOOTER)
1634:         c.drawRightString(W-24,13,f"Page {page_no}")
1635:         c.setFillColorRGB(0,0,0)
1636: 
1637:     def _grr_signature_block(self, c, y, page_size=A4):
1638:         """Draw the three requested transaction-document signature lines."""
1639:         W,H=page_size
1640:         labels=["Prepared By","Store Keeper","Store Incharge"]
1641:         block_h=70
```
```text
1648:             x=left+i*col_w
1649:             c.setLineWidth(0.6)
1650:             c.line(x+30,top-34,x+col_w-30,top-34)
1651:             c.setFont("Helvetica-Bold",7)
1652:             c.drawCentredString(x+col_w/2,top-48,label)
1653:         return True
1654: 
1655:     def _finish_page(self, c, page_no, page_size=A4):
1656:         self._report_footer(c,page_no,page_size); c.showPage()
1657: 
1658:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1659:         """Word-wrap `text` into a list of lines that each fit inside
1660:         max_width (points) at the given font, breaking mid-word only when a
1661:         single word is itself wider than the column."""
1662:         text=str(text) if text is not None else ""
1663:         if not text:
1664:             return [""]
1665:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1666:         lines=[]; cur=""
1667:         for word in text.split(" "):
1668:             trial=(cur+" "+word).strip() if cur else word
```
```text
1677:                     mid=(lo+hi)//2
1678:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1679:                     else: hi=mid-1
1680:                 lines.append(w[:fit_at]); w=w[fit_at:]
1681:             cur=w
1682:         if cur: lines.append(cur)
1683:         return lines or [""]
1684: 
1685:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1686:         """Create a paginated professional PDF with logo, bordered information,
1687:         GRR signature lines and page numbers. Also keep the same report data in
1688:         memory so the built-in Windows printer dialog can print directly without
1689:         requiring a PDF application's PrintTo association."""
1690:         if not hasattr(self, "_print_jobs"):
1691:             self._print_jobs = {}
1692:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1693:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1694:         page=1
1695:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1696:         usable=W-56
1697:         n=max(1,len(headers))
```
```text
1719:             if desc_idx is not None and desc_idx < len(r):
1720:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1721:             else:
1722:                 desc_lines=[""]
1723:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1724:             # Reserve room on the final page for the three transaction signatures + footer.
1725:             reserve=120 if is_transaction_doc else 42
1726:             if y-row_h<reserve:
1727:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1728:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1729:             # Item rows are intentionally border-free. The section/header remains
1730:             # professional while avoiding the unwanted boxed line around each
1731:             # individual printed item row. Description is drawn separately
1732:             # below (auto-fit / wrapped), so it is skipped in this pass.
1733:             for ci,(xx,val) in enumerate(zip(xs,r)):
1734:                 if ci==desc_idx: continue
1735:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1736:             if desc_idx is not None and desc_idx < len(r):
1737:                 for li,ln in enumerate(desc_lines):
1738:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1739:             y-=row_h
```
```text
1734:                 if ci==desc_idx: continue
1735:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1736:             if desc_idx is not None and desc_idx < len(r):
1737:                 for li,ln in enumerate(desc_lines):
1738:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1739:             y-=row_h
1740:         if is_transaction_doc:
1741:             # Keep the three requested transaction signatures at the physical bottom
1742:             # final page, immediately above the report footer.  If the item
1743:             # table reaches this reserved area, start a fresh final page.
1744:             bottom_sig_y = 138
1745:             if y < 165:
1746:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1747:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1748:             # Draw signatures at a fixed bottom position so they never float
1749:             # directly after the last item row.
1750:             self._grr_signature_block(c,bottom_sig_y,page_size)
1751:         self._report_footer(c,page,page_size); c.save()
1752:         if auto_print:
1753:             self.print_pdf(path)
1754:         return path
```
```text
1748:             # Draw signatures at a fixed bottom position so they never float
1749:             # directly after the last item row.
1750:             self._grr_signature_block(c,bottom_sig_y,page_size)
1751:         self._report_footer(c,page,page_size); c.save()
1752:         if auto_print:
1753:             self.print_pdf(path)
1754:         return path
1755: 
1756:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1757:         """Professional on-screen preview showing bordered document information
1758:         and a bordered item section. GRN Date is displayed in the right column."""
1759:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1760:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1761:         # Preview intentionally hides the company logo and company name.
1762:         # The actual generated/printed PDF still contains both via
1763:         # _report_header(), so only the on-screen preview is affected.
1764:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1765:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1766:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1767: 
1768:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
```
```text
1789:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1790: 
1791:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1792:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1793:         tr=self.make_tree(items,columns,widths)
1794:         for r in rows: tr.insert("", "end", values=r)
1795: 
1796:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1797:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1798:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1799:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1800:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1801:         win.bind("<Control-f>",bind_preview_find)
1802:         win.bind("<Control-F>",bind_preview_find)
1803: 
1804:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1805:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1806:         if is_transaction_preview:
1807:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1808:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1809:                 sig.columnconfigure(i,weight=1)
```
```text
1807:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1808:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1809:                 sig.columnconfigure(i,weight=1)
1810:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1811:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1812:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1813: 
1814:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1815:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1816:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1817:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1818:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1819:         if on_save:
1820:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1821:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1822:         if not is_transaction_preview:
1823:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1824:         # IMPORTANT: this must remain a normal top-level window (not transient
1825:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1826:         # exactly like the Preview Report window in the supplied recording.
1827:         # The Find dialog is opened from this window and is independent.
```
```text
1820:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1821:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1822:         if not is_transaction_preview:
1823:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1824:         # IMPORTANT: this must remain a normal top-level window (not transient
1825:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1826:         # exactly like the Preview Report window in the supplied recording.
1827:         # The Find dialog is opened from this window and is independent.
1828:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1829:         win.focus_force()
1830: 
1831:     def _safe_report_name(self, title, extension):
1832:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1833:         safe=safe.replace(" ","_") or "Preview"
1834:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1835: 
1836:     def print_preview_window(self, title, header_lines, columns, rows):
1837:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1838:         self._open_direct_printer(title, header_lines, columns, rows,
1839:                                   landscape(A4) if len(columns) > 8 else A4)
1840: 
```
```text
1833:         safe=safe.replace(" ","_") or "Preview"
1834:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1835: 
1836:     def print_preview_window(self, title, header_lines, columns, rows):
1837:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1838:         self._open_direct_printer(title, header_lines, columns, rows,
1839:                                   landscape(A4) if len(columns) > 8 else A4)
1840: 
1841:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1842:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1843:         This keeps the Export PDF button functional on a machine where the bundled
1844:         ReportLab package cannot be imported."""
1845:         def esc(v):
1846:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1847:         W,H=842,595
1848:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1849:         def add(txt,size=8,leading=11):
1850:             lines.append(f"/F1 {size} Tf")
1851:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1852:         add(str(title),12,16)
1853:         for h in header_lines or []:
```
```text
1860:         lines.append("ET")
1861:         stream="\n".join(lines).encode("latin-1","replace")
1862:         objs=[]
1863:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1864:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1865:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1866:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1867:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1868:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1869:         for i,obj in enumerate(objs,1):
1870:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1871:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1872:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1873:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1874:         with open(path,"wb") as f: f.write(out)
1875: 
1876:     def _save_entry_report(self, title, header_lines, columns, rows):
1877:         try:
1878:             os.makedirs(REPORTS_DIR, exist_ok=True)
1879:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1880:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```
```text
1873:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1874:         with open(path,"wb") as f: f.write(out)
1875: 
1876:     def _save_entry_report(self, title, header_lines, columns, rows):
1877:         try:
1878:             os.makedirs(REPORTS_DIR, exist_ok=True)
1879:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1880:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
1881:             path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
1882:             page_size = landscape(A4) if len(columns) > 8 else A4
1883:             if REPORTLAB:
1884:                 self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
1885:             else:
1886:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1887:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1888:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1889:             with open(path, "rb") as f:
1890:                 if f.read(5) != b"%PDF-":
1891:                     raise IOError("Generated report is not a valid PDF.")
1892:             self._last_entry_report_path = path
1893:             return path
```
```text
1887:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1888:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1889:             with open(path, "rb") as f:
1890:                 if f.read(5) != b"%PDF-":
1891:                     raise IOError("Generated report is not a valid PDF.")
1892:             self._last_entry_report_path = path
1893:             return path
1894:         except Exception as exc:
1895:             self._last_entry_report_path = None
1896:             return None
1897: 
1898:     def export_preview_pdf(self, title, header_lines, columns, rows):
1899:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1900:         try:
1901:             os.makedirs(REPORTS_DIR, exist_ok=True)
1902:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1903:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1904:             generated = False
1905:             if REPORTLAB:
1906:                 try:
1907:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
```
```text
1904:             generated = False
1905:             if REPORTLAB:
1906:                 try:
1907:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1908:                     generated = True
1909:                 except Exception:
1910:                     generated = False
1911:             if not generated:
1912:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1913:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1914:                 raise IOError("The PDF file was not created in the Reports folder.")
1915:             with open(path, "rb") as pf:
1916:                 signature = pf.read(5)
1917:             if signature != b"%PDF-":
1918:                 raise IOError("The generated file is not a valid PDF.")
1919:             self._last_report_path = path
1920:             try:
1921:                 webbrowser.open("file://" + path)
1922:             except Exception:
1923:                 self.open_file(path)
1924:             return path
```
```text
1918:                 raise IOError("The generated file is not a valid PDF.")
1919:             self._last_report_path = path
1920:             try:
1921:                 webbrowser.open("file://" + path)
1922:             except Exception:
1923:                 self.open_file(path)
1924:             return path
1925:         except Exception as e:
1926:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1927:             return None
1928: 
1929:     def export_preview_word(self, title, header_lines, columns, rows):
1930:         """Export exactly what is visible in the current preview to Word."""
1931:         if not DOCX_AVAILABLE:
1932:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1933:         path=self._safe_report_name(title,"docx")
1934:         doc=Document()
1935:         sec=doc.sections[0]
1936:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1937:         sec.header.paragraphs[0].runs[0].bold=True
1938:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
```
```text
1960:             doc.add_paragraph("")
1961:             sig=doc.add_table(rows=2,cols=3)
1962:             labels=["Prepared By","Store Keeper","Store Incharge"]
1963:             for i,label in enumerate(labels):
1964:                 sig.cell(0,i).text="____________________"
1965:                 sig.cell(1,i).text=label
1966:                 for para in sig.cell(1,i).paragraphs:
1967:                     for run in para.runs: run.bold=True
1968:         doc.save(path)
1969:         self.open_file(path)
1970: 
1971:     def export_preview_excel(self, title, header_lines, columns, rows):
1972:         """Export exactly what is visible in the current preview to Excel."""
1973:         if not XLSX_AVAILABLE:
1974:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
1975:         path=self._safe_report_name(title,"xlsx")
1976:         wb=openpyxl.Workbook(); ws=wb.active
1977:         ws.title="Preview"
1978:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
1979:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1980:         if not is_transaction_preview:
```
```text
1998:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
1999:             for col in range(1,4):
2000:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
2001:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
2002:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
2003:         for col_cells in ws.columns:
2004:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
2005:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
2006:         wb.save(path)
2007:         self.open_file(path)
2008: 
2009:     def make_tree(self,parent,cols,widths=None):
2010:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
2011:         tr=ttk.Treeview(fr,columns=cols,show="headings")
2012:         for i,c in enumerate(cols):
2013:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
2014:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
2015:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
2016:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
2017:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
2018:         return tr
```
```text
2071:                     w.state(["!disabled"] if editable else ["disabled"])
2072:             except Exception:
2073:                 try: w.configure(state="normal" if editable else "disabled")
2074:                 except Exception: pass
2075:             for ch in w.winfo_children(): walk(ch)
2076:         for root in roots: walk(root)
2077: 
2078:     def document_selector(self, parent, label, typ, var, load_callback):
2079:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
2080:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
2081:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
2082:         combo.pack(side="left", padx=4)
2083:         def refresh():
2084:             vals=[]
2085:             if typ=="demand":
2086:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
2087:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
2088:             elif typ=="grr":
2089:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
2090:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
2091:             else:
```
```text
2098:             no=text.split(" -> ",1)[0].strip()
2099:             var.set(no)
2100:             load_callback(no)
2101:         combo.bind("<<ComboboxSelected>>", selected)
2102:         combo.bind("<Return>", selected)
2103:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2104:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2105:         refresh()
2106:         # Keep the currently open transaction's saved-record list live.
2107:         # Each save calls refresh_saved_cache(), so newly saved records appear
2108:         # immediately without closing/reopening the window or pressing Refresh.
2109:         if not hasattr(self, "_document_selector_refreshers"):
2110:             self._document_selector_refreshers = {}
2111:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2112:         return combo
2113: 
2114:     def dashboard(self):
2115:         # Dashboard-only visual refresh. All existing data queries, filters,
2116:         # callbacks and report/detail behavior are intentionally preserved.
2117:         self.clearbody()
2118:         c=self.conn
```
```text
2199:             for x in tr.get_children(): tr.delete(x)
2200:             params=[];where=[]
2201:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2202:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2203:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2204:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2205:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2206:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2207:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2208:                    FROM transactions t JOIN items i ON i.code=t.code"""
2209:             if where: sql += " WHERE " + " AND ".join(where)
2210:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2211:             rows=list(c.execute(sql,params))
2212:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2213:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2214:             bal_after={}
2215:             for txid,cc,typ,qty in alltx:
2216:                 running.setdefault(cc,0.0)
2217:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2218:                 bal_after[txid]=running[cc]
2219:             for r in rows:
```
```text
2594:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2595:         load()
2596:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2597: 
2598:     def inventory_codes(self):
2599:         """Inventory Codes using the classic desktop inventory interface.
2600: 
2601:         This screen intentionally follows the uploaded Inventory Management
2602:         reference: a simple module title, compact New/Edit/Delete/Save/
2603:         Refresh/Print/Close action row, and a full-width editable data grid.
2604:         All records come from the V18 database, so existing inventory data is
2605:         preserved rather than recreated.
2606:         """
2607:         self.clearbody()
2608:         # Remove the generic SAP action row; this page owns its own classic
2609:         # action row just like the reference Inventory/Items screen.
2610:         if self.body.winfo_children():
2611:             try:
2612:                 self.body.winfo_children()[0].destroy()
2613:             except Exception:
2614:                 pass
```
```text
2667:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2668:         if filter_text:
2669:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2670:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2671: 
2672:         editing={"id":None,"new":False}
2673:         cell_editor={"widget":None}
2674: 
2675:         def close_editor(save_value=False):
2676:             w=cell_editor.get("widget")
2677:             if not w:
2678:                 return
2679:             try:
2680:                 if save_value:
2681:                     w.event_generate("<Return>")
2682:                 w.destroy()
2683:             except Exception:
2684:                 pass
2685:             cell_editor["widget"]=None
2686: 
2687:         def edit_cell(event=None):
```
```text
2697:             bbox=tree.bbox(iid,colid)
2698:             if not bbox: return
2699:             close_editor(False)
2700:             x,y,w,h=bbox
2701:             val=str(tree.item(iid,"values")[idx] or "")
2702:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2703:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2704:             cell_editor["widget"]=e
2705:             def commit(_=None):
2706:                 try:
2707:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2708:                 finally:
2709:                     try:e.destroy()
2710:                     except Exception:pass
2711:                     cell_editor["widget"]=None
2712:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2713:             e.bind("<FocusOut>",commit)
2714: 
2715:         def rows_query():
2716:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2717:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2719:             if tc: where.append("code <= ?"); params.append(tc)
2720:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2721:             if df or dt:
2722:                 sub=[]; sp=[]
2723:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2724:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2725:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2726:                 params.extend(sp)
2727:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2728:             return sql,params
2729: 
2730:         def load():
2731:             close_editor(False)
2732:             for i in tree.get_children(): tree.delete(i)
2733:             sql,params=rows_query()
2734:             count=0
2735:             for r in self.conn.execute(sql,params):
2736:                 # V18 stores UOM/opening and the original application may have
2737:                 # rate/remarks columns in some versions. Read them safely.
2738:                 rid,code,desc,uom,opening,rate,remarks=r
2739:                 bal=stock(self.conn,code)
```
```text
2753:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2754:             editing["id"]=None; editing["new"]=True
2755:             # Put the user directly into the Code cell.
2756:             try:
2757:                 bbox=tree.bbox(iid,"#2")
2758:                 if bbox:
2759:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2760:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2761:                     def commit(_=None):
2762:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2763:                         try:e.destroy()
2764:                         except Exception:pass
2765:                         cell_editor["widget"]=None
2766:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2767:             except Exception: pass
2768:             status.set("New row added — enter values, then press Save")
2769: 
2770:         def selected_row():
2771:             a=tree.selection()
2772:             return a[0] if a else None
2773: 
```
```text
2773: 
2774:         def edit_record():
2775:             iid=selected_row()
2776:             if not iid:
2777:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2778:             if not self.can_edit and not self.is_admin:
2779:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2780:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2781:             status.set("Edit mode — double-click any cell to change it, then press Save")
2782:             tree.focus(iid); tree.see(iid)
2783: 
2784:         def save_record():
2785:             iid=selected_row()
2786:             if not iid:
2787:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2788:             if not self.can_edit and not self.is_admin:
2789:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2790:             close_editor(True)
2791:             vals=list(tree.item(iid,"values"))
2792:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2793:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2791:             vals=list(tree.item(iid,"values"))
2792:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2793:             try: opening=float(str(vals[4]).strip() or 0)
2794:             except Exception: raise ValueError("Opening Qty must be a number.")
2795:             try: rate=float(str(vals[5]).strip() or 0)
2796:             except Exception: raise ValueError("Rate must be a number.")
2797:             remarks=str(vals[6]).strip()
2798:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2799:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2800:             if not desc:
2801:                 messagebox.showerror("Save","Description is required."); return
2802:             if opening<0:
2803:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2804:             rid=vals[0]
2805:             try:
2806:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2807:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2808:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2809:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2810:                 if rid:
2811:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2814:                                       (code,desc,uom,opening,rid))
2815:                     if oldcode!=code:
2816:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2817:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2818:                             except Exception:pass
2819:                 else:
2820:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2821:                                       (code,desc,uom,"",opening,0,"Local",0))
2822:                 self.conn.commit()
2823:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2824:                 backup_database(); load()
2825:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2826:             except Exception as ex:
2827:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2828: 
2829:         def delete_record():
2830:             iid=selected_row()
2831:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2832:             if not self.can_delete and not self.is_admin:
2833:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2834:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2830:             iid=selected_row()
2831:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2832:             if not self.can_delete and not self.is_admin:
2833:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2834:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2835:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2836:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2837:             try:
2838:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2839:             except Exception as ex:
2840:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2841: 
2842:         def refresh(): load()
2843:         def do_print():
2844:             try:self.preview_tree("Inventory Codes",tree)
2845:             except Exception as ex:messagebox.showerror("Print",str(ex))
2846:         def do_close(): self.dashboard()
2847: 
2848:         btn("New",new_record,8)
2849:         btn("Edit",edit_record,8)
2850:         btn("Delete",delete_record,8)
```
```text
2843:         def do_print():
2844:             try:self.preview_tree("Inventory Codes",tree)
2845:             except Exception as ex:messagebox.showerror("Print",str(ex))
2846:         def do_close(): self.dashboard()
2847: 
2848:         btn("New",new_record,8)
2849:         btn("Edit",edit_record,8)
2850:         btn("Delete",delete_record,8)
2851:         btn("Save",save_record,8)
2852:         btn("Refresh",refresh,9)
2853:         btn("Preview",do_print,8)
2854:         btn("Print",do_print,8)
2855:         btn("Close",do_close,8)
2856: 
2857:         # Search is deliberately small and sits on the right, without changing
2858:         # the reference layout of the action buttons.
2859:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2860:         search=tk.StringVar()
2861:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2862:         se.pack(side="left",padx=2)
2863:         self._item_master_search_entry=se
```
```text
2871:                     tree.detach(iid)
2872:         search.trace_add("write",filter_grid)
2873:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2874: 
2875:         tree.bind("<Double-1>",edit_cell)
2876:         tree.bind("<F2>",lambda e: edit_record())
2877:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2878:         self._page_actions={
2879:             "save":save_record,"edit":edit_record,"delete":delete_record,
2880:             "cancel":do_close,"print":do_print,"preview":do_print
2881:         }
2882:         load()
2883: 
2884:     def open_mto_inventory_flow(self):
2885:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2886: 
2887:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2888:         Cancel/X only closes the popup.
2889:         """
2890:         criteria = self._ask_mto_inventory_filters()
2891:         if not criteria or criteria.get("cancelled"):
```
```text
3053:                 return False
3054:             destination.set(found_dest)
3055:             edit_mode.update(on=True, original=r[0], dest=found_dest)
3056:             code.set(r[0])
3057:             desc.set(r[1] or "")
3058:             uom.set(r[2] or UOM_OPTIONS[0])
3059:             opening.set(str(r[3] if r[3] is not None else 0))
3060:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
3061:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
3062:             err.set("")
3063:             edit_btn.configure(text="SAVE EDIT")
3064:             ce.focus_set()
3065:             return True
3066: 
3067:         def check_duplicates(*_):
3068:             c = code.get().strip()
3069:             d = desc.get().strip()
3070:             dest = destination.get()
3071:             msgs = []
3072:             r = row_for(dest, c) if len(norm(c)) == 8 else None
3073:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
3075:             dh = desc_hit(dest, d) if d else None
3076:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
3077:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
3078:             hint.set("\n".join(msgs))
3079: 
3080:         code.trace_add("write", check_duplicates)
3081:         desc.trace_add("write", check_duplicates)
3082: 
3083:         def save_code():
3084:             try:
3085:                 c = code.get().strip()
3086:                 d = desc.get().strip()
3087:                 u = uom.get().strip()
3088:                 dest = destination.get()
3089:                 digits = norm(c)
3090:                 if len(digits) != 8:
3091:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3092:                 if not d:
3093:                     raise ValueError("Description is required.")
3094:                 try:
3095:                     op = float(opening.get().strip() or 0)
```
```text
3116:                         (c, d, u, op, iso, old)
3117:                     )
3118:                     action = "updated"
3119:                 else:
3120:                     self.conn.execute(
3121:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3122:                         (c, d, u, "", op, 0, iso)
3123:                     )
3124:                     action = "saved"
3125:                 self.conn.commit()
3126:                 backup_database()
3127:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3128:                 # Keep popup open for fast multiple entries.
3129:                 clear_form(keep_search=False)
3130:                 ce.focus_set()
3131:             except Exception as ex:
3132:                 self.conn.rollback()
3133:                 err.set(str(ex))
3134:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3135: 
3136:         def edit_action():
```
```text
3132:                 self.conn.rollback()
3133:                 err.set(str(ex))
3134:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3135: 
3136:         def edit_action():
3137:             if not edit_mode["on"]:
3138:                 load_for_edit()
3139:             else:
3140:                 save_code()
3141: 
3142:         def delete_code():
3143:             if not edit_mode["on"]:
3144:                 if not load_for_edit():
3145:                     return
3146:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3147:                 return
3148:             try:
3149:                 t = table_for(edit_mode["dest"])
3150:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3151:                 self.conn.commit()
3152:                 backup_database()
```
```text
3148:             try:
3149:                 t = table_for(edit_mode["dest"])
3150:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3151:                 self.conn.commit()
3152:                 backup_database()
3153:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3154:                 clear_form(keep_search=False)
3155:             except Exception as ex:
3156:                 self.conn.rollback()
3157:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3158: 
3159:         btns = ttk.Frame(box)
3160:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3161:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3162:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3163:         edit_btn.pack(side="left", padx=4, ipadx=8)
3164:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3165:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3166:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3167:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3168:         ce.focus_set()
```
```text
3162:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3163:         edit_btn.pack(side="left", padx=4, ipadx=8)
3164:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3165:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3166:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3167:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3168:         ce.focus_set()
3169: 
3170:     def _mto_new_item_dialog(self, on_saved):
3171:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3172:         brand-new item can be created without leaving that screen. Writes
3173:         straight into the same Item Master (items table) used everywhere."""
3174:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3175:         win.transient(self); win.grab_set()
3176:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3177:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3178:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3179:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3180:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3181:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3182:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3178:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3179:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3180:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3181:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3182:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3183:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3184:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3185:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3186:         def save():
3187:             try:
3188:                 c=code.get().strip(); d=desc.get().strip()
3189:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3190:                 if not d: raise ValueError("Description is required.")
3191:                 try:
3192:                     opening_val=float(opening.get() or 0)
3193:                 except ValueError:
3194:                     raise ValueError("Opening Qty must be a number.")
3195:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3196:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3197:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3198:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3191:                 try:
3192:                     opening_val=float(opening.get() or 0)
3193:                 except ValueError:
3194:                     raise ValueError("Opening Qty must be a number.")
3195:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3196:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3197:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3198:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3199:                 self.conn.commit(); backup_database()
3200:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3201:                 win.grab_release(); win.destroy()
3202:                 on_saved()
3203:             except Exception as ex: messagebox.showerror("Error",str(ex))
3204:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3205:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3206:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3207: 
3208:     def _item_filter_bar(self, parent, on_change):
3209:         """Item Code entry + item-master picker + Search/Show All. Calls
3210:         on_change() whenever the code changes or a button is pressed."""
3211:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3297:         self._item_master_find_callback=None
3298:         self._portable_print_context=None
3299:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3300:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3301:         }
3302: 
3303:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3304:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3305:         self.conn.commit()
3306: 
3307:         # ---- Same professional in-app window layout as Inventory Codes ----
3308:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3309:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3310:                   foreground=COLORS["primary_dark"]).pack(side="left")
3311:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3312: 
3313:         def open_find():
3314:             state_find={"index":-1}
3315:             def search_fn(text):
3316:                 text=text.strip().lower()
3317:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3404:             for i in table.get_children(): table.delete(i)
3405:             where=["1=1"]; params=[]
3406:             prefix=state.get("prefix",""); q=search.get().strip()
3407:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3408:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3409:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3410:             if fc: where.append("code >= ?"); params.append(fc)
3411:             if tc: where.append("code <= ?"); params.append(tc)
3412:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3413:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3414:             records=[]
3415:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3416:                 # If a date filter is supplied, accept an opening-date match OR
3417:                 # a transaction in that date range. This prevents valid MTO codes
3418:                 # from disappearing merely because an older record has no opening_date.
3419:                 if df or dt:
3420:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3421:                     if not ok:
3422:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3423:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3424:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3494:                 tr.insert("", "end", values=r)
3495:         def clear():
3496:             for x in v.values(): x.set("")
3497:             try: tr.selection_remove(tr.selection())
3498:             except Exception: pass
3499:             self._set_form_editable(party_form_roots, False)
3500:         def new_form():
3501:             clear(); self._set_form_editable(party_form_roots, True)
3502:         def save():
3503:             try:
3504:                 name=v["name"].get().strip()
3505:                 if not name: raise ValueError("Party Name is required.")
3506:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3507:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3508:             except Exception as ex: messagebox.showerror("Error",str(ex))
3509:         def load_party_row(a):
3510:             if not a:return
3511:             r=tr.item(a[0])["values"]
3512:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3513:             self._set_form_editable(party_form_roots, False)
3514:         def on_party_select(_=None):
```
```text
3520:             load_party_row(a)
3521:             self._set_form_editable(party_form_roots, True)
3522:         def delete_party():
3523:             a=tr.selection()
3524:             if not a:
3525:                 messagebox.showwarning("Delete", "Select a party first."); return
3526:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3527:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3528:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3529:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3530:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3531:         self._add_transaction_new_button(new_form)
3532:         load(); clear()
3533: 
3534:     def user_management(self):
3535:         self.clearbody()
3536:         if not self.is_admin:
3537:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3538:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3539:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3540:         role=tk.StringVar(value="User")
```
```text
3577:             u_ent.state(["!disabled"])
3578:         def edit():
3579:             a=tr.selection()
3580:             if not a:
3581:                 messagebox.showwarning("Edit User","Select a user row first."); return
3582:             r=tr.item(a[0])["values"]
3583:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3584:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3585:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3586:         def save():
3587:             try:
3588:                 username=v["username"].get().strip()
3589:                 if not username: raise ValueError("Username is required.")
3590:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3591:                 pw=v["password"].get()
3592:                 if exists:
3593:                     pw_hash = hash_password(pw) if pw else exists[0]
3594:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3595:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3596:                 else:
3597:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3592:                 if exists:
3593:                     pw_hash = hash_password(pw) if pw else exists[0]
3594:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3595:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3596:                 else:
3597:                     if not pw: raise ValueError("Password is required for a new user.")
3598:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3599:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3600:                 self.conn.commit(); backup_database(); load(); clear()
3601:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3602:             except Exception as ex:
3603:                 messagebox.showerror("Error", str(ex))
3604:         def delete_user():
3605:             a=tr.selection()
3606:             if not a:
3607:                 messagebox.showwarning("Delete User","Select a user row first."); return
3608:             username=tr.item(a[0])["values"][0]
3609:             if username==self.current_user:
3610:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3611:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3612:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3607:                 messagebox.showwarning("Delete User","Select a user row first."); return
3608:             username=tr.item(a[0])["values"][0]
3609:             if username==self.current_user:
3610:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3611:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3612:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3613:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3614:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3615:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3616:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3617:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3618:         load()
3619: 
3620:     @staticmethod
3621:     def _renumber_tree(tree, rows):
3622:         for i,iid in enumerate(tree.get_children()):
3623:             vals=list(tree.item(iid,"values"));
3624:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3625: 
3626:     def demand(self):
3627:         self.clearbody(); self.demand_lines=[]
```
```text
3624:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3625: 
3626:     def demand(self):
3627:         self.clearbody(); self.demand_lines=[]
3628:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3629:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3630:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3631:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3632:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3633:         # Demand Date is intentionally displayed as its own dedicated field.
3634:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3635:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3636:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3637:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3638:                 ("special","Special Instructions"),("source","Recommended Source")]
3639:         for i,(k,n) in enumerate(fields):
3640:             r=i//4*2+3; c=i%4*2
3641:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3642:             if k=="dept":
3643:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3644:             elif k=="urgency":
```
```text
3714:         def new_form():
3715:             self._editing_document_key=None
3716:             for z in v.values(): z.set("")
3717:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3718:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3719:             for iid in tree.get_children(): tree.delete(iid)
3720:             self._set_form_editable(form_roots, True, skip=[selector])
3721: 
3722:         def save():
3723:             try:
3724:                 no=v["no"].get().strip()
3725:                 if not no: raise ValueError("Demand No is required.")
3726:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3727:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3728:                 if dup and getattr(self,"_editing_document_key",None) != no:
3729:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3730:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3731:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3732:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3733:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3734:                 self.conn.commit()
```
```text
3727:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3728:                 if dup and getattr(self,"_editing_document_key",None) != no:
3729:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3730:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3731:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3732:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3733:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3734:                 self.conn.commit()
3735:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3736:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3737:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3738:             except Exception as ex: messagebox.showerror("Error",str(ex))
3739:         form_roots=[f,line,editbar]
3740:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3741:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3742:         def delete_current():
3743:             no=v["no"].get().strip()
3744:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3745:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3746:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3747:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3760:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3761:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3762:                     f"Justification: {v['just'].get()}",
3763:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3764:             if not self.demand_lines:
3765:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3766:             self.show_preview_window("Purchase Demand", header,
3767:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3768:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3769:         def edit_saved_demand():
3770:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3771:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3772:             self._set_form_editable(form_roots, True, skip=[selector])
3773:         def print_now():
3774:             if not self.demand_lines:
3775:                 messagebox.showwarning("Print","Add at least one item line first."); return
3776:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3777:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3778:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3779:                     f"Justification: {v['just'].get()}",
3780:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3776:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3777:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3778:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3779:                     f"Justification: {v['just'].get()}",
3780:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3781:             self._open_direct_printer("Purchase Demand",header,
3782:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3783:                 self.demand_lines,A4)
3784:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3785:         self._add_transaction_new_button(new_form)
3786:         self._set_form_editable(form_roots, False, skip=[selector])
3787:         try:
3788:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3789:         except Exception: pass
3790:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3791: 
3792:     def load_demand_into_form(self,no,v,tree):
3793:         v["no"].set(no)
3794:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3795:         if not r:return
3796:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3798:         self.demand_lines=[]
3799:         for i in tree.get_children():tree.delete(i)
3800:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3801:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3802:         roots=getattr(self,"_transaction_form_roots",None)
3803:         if roots and "demand" in roots:
3804:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3805: 
3806:     def refresh_saved_cache(self,typ):
3807:         # Refresh saved-document dropdowns immediately after a successful save.
3808:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3809:         alive=[]
3810:         for combo, refresh in refreshers:
3811:             try:
3812:                 if combo.winfo_exists():
3813:                     refresh()
3814:                     alive.append((combo, refresh))
3815:             except Exception:
3816:                 pass
3817:         if hasattr(self, "_document_selector_refreshers"):
3818:             self._document_selector_refreshers[typ] = alive
```
```text
3817:         if hasattr(self, "_document_selector_refreshers"):
3818:             self._document_selector_refreshers[typ] = alive
3819: 
3820:     def grr(self):
3821:         self.clearbody(); self.grr_lines=[]
3822:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3823:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3824:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3825:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3826:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3827:         for i,(k,n) in enumerate(fields):
3828:             r=i//4*2+2;c=i%4*2
3829:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3830:             if k=="department":
3831:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3832:             elif k=="supplier":
3833:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3834:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3835:             elif k=="date":
3836:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3837:             else:
```
```text
3886:         def new_form():
3887:             self._editing_document_key=None
3888:             for z in v.values(): z.set("")
3889:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3890:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3891:             for iid in tree.get_children(): tree.delete(iid)
3892:             self._set_form_editable(form_roots, True, skip=[selector])
3893: 
3894:         def save():
3895:             try:
3896:                 no=v["no"].get().strip()
3897:                 if not no:raise ValueError("GRN No is required.")
3898:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3899:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3900:                 if dup and getattr(self,"_editing_document_key",None) != no:
3901:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3902:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3903:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3904:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3905:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3906:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3903:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3904:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3905:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3906:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3907:                 for x in self.grr_lines:
3908:                     ltype=x[10] if len(x)>10 else "Local"
3909:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3910:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3911:                 self.conn.commit()
3912:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
3913:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
3914:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3915:             except Exception as ex:messagebox.showerror("Error",str(ex))
3916:         form_roots=[f,line,editbar]
3917:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3918:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3919:         def delete_current():
3920:             no=v["no"].get().strip()
3921:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3922:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3923:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
3916:         form_roots=[f,line,editbar]
3917:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3918:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3919:         def delete_current():
3920:             no=v["no"].get().strip()
3921:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3922:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3923:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3924:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3925:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3926:         def cancel_form():
3927:             self._editing_document_key=None
3928:             self._set_form_editable(form_roots, False, skip=[selector])
3929:             for z in v.values(): z.set("")
3930:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3931:             itype.set("Local")
3932:             self.grr_lines.clear()
3933:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3934:             for iid in tree.get_children(): tree.delete(iid)
3935:         def preview_now():
3936:             if not self.grr_lines:
```
```text
3945:                     ("Challan #", v['challan'].get()),
3946:                     ("Vehicle #", v['vehicle'].get()),
3947:                     ("Bill/Voucher #", v['bill'].get()),
3948:                     ("Reference", v['ref'].get()),
3949:                     ("Remarks", v['remarks'].get()),
3950:                     ("Total Value", fmt_num(total))]
3951:             self.show_preview_window("GRN Receipt", header,
3952:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3953:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3954:         def portable_current():
3955:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3956:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3957:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3958:         self._portable_print_context=portable_current
3959:         def edit_saved_grr():
3960:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3961:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
3962:             self._set_form_editable(form_roots, True, skip=[selector])
3963:         def print_now():
3964:             if not self.grr_lines:
3965:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
3969:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
3970:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
3971:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
3972:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
3973:                     ("Total Value", fmt_num(total))]
3974:             self._open_direct_printer("GRN Receipt",header,
3975:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3976:                 self.grr_lines,landscape(A4))
3977:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3978:         self._add_transaction_new_button(new_form)
3979:         self._set_form_editable(form_roots, False, skip=[selector])
3980:         try:
3981:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3982:         except Exception: pass
3983:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
3984: 
3985:     def load_grr_into_form(self,no,v,tree):
3986:         v["no"].set(no)
3987:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
3988:         if not r:return
3989:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
3996:         if roots and "grr" in roots:
3997:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
3998: 
3999:     def issue(self):
4000:         self.clearbody(); self.issue_lines=[]
4001:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
4002:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
4003:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
4004:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
4005:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
4006:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
4007:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
4008:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
4009:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
4010:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
4011:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
4012:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
4013:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
4014:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
4015:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
4016:         itype=tk.StringVar(value="Local")
```
```text
4085:                 # Editing an existing issue replaces its old stock transaction and detail lines.
4086:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
4087:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
4088:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
4089:                 for x in self.issue_lines:
4090:                     ltype=x[7] if len(x)>7 else "Local"
4091:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
4092:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
4093:                 self.conn.commit()
4094:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
4095:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
4096:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4097:             except Exception as ex:messagebox.showerror("Error",str(ex))
4098:         def delete_current():
4099:             no=v["no"].get().strip()
4100:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
4101:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
4102:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
4103:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
4104:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
4105:         def cancel_form():
```
```text
4113:             for iid in tree.get_children(): tree.delete(iid)
4114:         def preview_now():
4115:             if not self.issue_lines:
4116:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4117:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4118:                     f"Items Use For: {v['items_use_for'].get()}"]
4119:             self.show_preview_window("Material Issue", header,
4120:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4121:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4122:         def portable_current():
4123:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4124:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4125:         self._portable_print_context=portable_current
4126:         form_roots=[f,usebar,line,editbar]
4127:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4128:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4129:         def load_saved_issue(no):
4130:             self.load_issue_into_form(no,v,tree)
4131:             self._set_form_editable(form_roots, False, skip=[selector])
4132:         def edit_saved_issue():
4133:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4126:         form_roots=[f,usebar,line,editbar]
4127:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4128:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4129:         def load_saved_issue(no):
4130:             self.load_issue_into_form(no,v,tree)
4131:             self._set_form_editable(form_roots, False, skip=[selector])
4132:         def edit_saved_issue():
4133:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4134:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4135:             self._set_form_editable(form_roots, True, skip=[selector])
4136:         def print_issue_now():
4137:             if not self.issue_lines:
4138:                 messagebox.showwarning("Print","Add at least one item line first."); return
4139:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4140:             self._open_direct_printer("Material Issue",header,
4141:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4142:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4143:         self._add_transaction_new_button(new_form)
4144:         self._set_form_editable(form_roots, False, skip=[selector])
4145:         self._active_form_loader = load_saved_issue
4146: 
```
```text
4154:         for i in tree.get_children():tree.delete(i)
4155:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4156:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4157:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4158:         roots=getattr(self,"_transaction_form_roots",None)
4159:         if roots and "issue" in roots:
4160:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4161: 
4162:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4163:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4164: 
4165:         The layout intentionally matches Inventory Codes' Selection Criteria
4166:         popup so all Report sub-sections have one consistent desktop workflow.
4167:         """
4168:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4169:         win=tk.Toplevel(self)
4170:         win.title(f"{report_title} - Selection Criteria")
4171:         win.resizable(False,False)
4172:         win.transient(self); win.grab_set()
4173:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4174:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4219:             except Exception: pass
4220:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4221:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4222:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4223:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4224:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4225:         e1.focus_set(); self.wait_window(win); return result
4226: 
4227:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4228:         self._pending_report_filters=criteria
4229:         try:
4230:             return self.open_menu_window(method,title,geometry)
4231:         finally:
4232:             self._pending_report_filters=None
4233: 
4234:     def open_stock_balance_report_flow(self):
4235:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4236:         if f.get("cancelled"): return None
4237:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4238: 
4239:     def open_grr_report_flow(self):
```
```text
4232:             self._pending_report_filters=None
4233: 
4234:     def open_stock_balance_report_flow(self):
4235:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4236:         if f.get("cancelled"): return None
4237:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4238: 
4239:     def open_grr_report_flow(self):
4240:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4241:         if f.get("cancelled"): return None
4242:         return self._open_report_child(self.report_grr,"GRN Report",f)
4243: 
4244:     def open_demand_report_flow(self):
4245:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4246:         if f.get("cancelled"): return None
4247:         return self._open_report_child(self.report_demand,"Demand Report",f)
4248: 
4249:     def open_issue_report_flow(self):
4250:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4251:         if f.get("cancelled"): return None
4252:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4246:         if f.get("cancelled"): return None
4247:         return self._open_report_child(self.report_demand,"Demand Report",f)
4248: 
4249:     def open_issue_report_flow(self):
4250:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4251:         if f.get("cancelled"): return None
4252:         return self._open_report_child(self.report_issue,"Issue Report",f)
4253: 
4254:     def open_party_report_flow(self):
4255:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4256:         if f.get("cancelled"): return None
4257:         return self._open_report_child(self.report_party,"Party Report",f)
4258: 
4259:     def _ask_stock_balance_filters(self):
4260:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4261:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4262:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4263:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4264:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4265:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4266:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4278:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4279:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4280:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4281:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4282:         e1.focus_set();self.wait_window(win);return result
4283: 
4284:     def stock_balance(self):
4285:         self.clearbody()
4286:         # Stock Balance is a Report sub-section and does not use the generic
4287:         # Save/Edit/Delete/Cancel/Print action strip.
4288:         children=self.body.winfo_children()
4289:         if children:
4290:             children[0].destroy()
4291:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4292:         if initial.get("cancelled"):
4293:             self.dashboard(); return
4294:         top=ttk.Frame(self.body);top.pack(fill="x")
4295:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4296:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4297:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4298:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4308:             for typ,qty in self.conn.execute(q,params):
4309:                 if typ=="GRR":gr+=float(qty or 0)
4310:                 elif typ=="ISSUE":iss+=float(qty or 0)
4311:             return opening_before,gr,iss,opening_before+gr-iss
4312:         def header_summary():
4313:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4314:         def load():
4315:             for i in tr.get_children():tr.delete(i)
4316:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4317:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4318:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4319:             sql+=" ORDER BY code"
4320:             for r in self.conn.execute(sql,params):
4321:                 op,gr,iss,cur=period(r[0],r[3])
4322:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4323:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4324:         def reopen_filters():
4325:             initial2=self._ask_stock_balance_filters()
4326:             if initial2.get("cancelled"):return
4327:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4328:             load()
```
```text
4366:         """
4367:         if typ=="demand": self.demand()
4368:         elif typ=="grr": self.grr()
4369:         else: self.issue()
4370:         loader=getattr(self,"_active_form_loader",None)
4371:         if loader: loader(str(no))
4372: 
4373:     def _edit_from_selector(self, typ, var, loader):
4374:         """Top Edit action: load the saved document directly into the current form.
4375:         If nothing is selected, use the newest saved document; never open a popup.
4376:         """
4377:         text=var.get().strip()
4378:         if text:
4379:             no=text.split(" -> ",1)[0].strip()
4380:         else:
4381:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4382:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4383:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4384:             if not r:
4385:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4386:                 return
```
```text
4383:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4384:             if not r:
4385:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4386:                 return
4387:             no=str(r[0])
4388:             var.set(no)
4389:         loader(no)
4390: 
4391:     def show_saved_records(self,typ):
4392:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4393:         if typ=="demand":
4394:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4395:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4396:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4397:             for r in rows:
4398:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4399:                 r=list(r); r[1]=to_display_date(r[1])
4400:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4401:         elif typ=="grr":
4402:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4403:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4414:         def view():
4415:             a=tr.selection()
4416:             if not a:return
4417:             no=tr.item(a[0])["values"][0]
4418:             win.destroy();self.open_document_editor(typ,no)
4419:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4420:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4421:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4422:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4423: 
4424:     def documents(self):
4425:         self.clearbody()
4426:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4427:         specs=[
4428:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4429:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4430:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4431:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4432:             ("Material Issues","issue",("No","Date","Department"),
4433:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4434:         ]
```
```text
4430:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4431:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4432:             ("Material Issues","issue",("No","Date","Department"),
4433:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4434:         ]
4435:         for title,typ,cols,query in specs:
4436:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4437:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4438:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4439:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4440:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4441:             for r in self.conn.execute(query):
4442:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4443:             def edit_selected(t=tr,k=typ):
4444:                 a=t.selection()
4445:                 if not a:
4446:                     messagebox.showwarning("Edit", "Select a saved record first.")
4447:                     return
4448:                 no=t.item(a[0])["values"][0]
4449:                 self.open_document_editor(k,no)
4450:             def delete_selected(t=tr,k=typ):
```
```text
4445:                 if not a:
4446:                     messagebox.showwarning("Edit", "Select a saved record first.")
4447:                     return
4448:                 no=t.item(a[0])["values"][0]
4449:                 self.open_document_editor(k,no)
4450:             def delete_selected(t=tr,k=typ):
4451:                 a=t.selection()
4452:                 if not a:
4453:                     messagebox.showwarning("Delete", "Select a saved record first.")
4454:                     return
4455:                 no=t.item(a[0])["values"][0]
4456:                 if k=="demand":
4457:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4458:                 elif k=="grr":
4459:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4460:                 else:
4461:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4462:                 self.conn.commit();backup_database();self.documents()
4463:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4464:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4465:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4459:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4460:                 else:
4461:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4462:                 self.conn.commit();backup_database();self.documents()
4463:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4464:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4465:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4466:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4467:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4468:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4469:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4470: 
4471:     def doc_export_selected(self,typ,tr,fmt):
4472:         a=tr.selection()
4473:         if not a:
4474:             messagebox.showwarning("Export","Select a saved record first."); return
4475:         no=tr.item(a[0])["values"][0]
4476:         if fmt=="word": self.export_word(typ,no)
4477:         else: self.export_excel(typ,no)
4478: 
4479:     def doc_preview_selected(self,typ,tr):
```
```text
4474:             messagebox.showwarning("Export","Select a saved record first."); return
4475:         no=tr.item(a[0])["values"][0]
4476:         if fmt=="word": self.export_word(typ,no)
4477:         else: self.export_excel(typ,no)
4478: 
4479:     def doc_preview_selected(self,typ,tr):
4480:         a=tr.selection()
4481:         if not a:
4482:             messagebox.showwarning("Preview","Select a saved record first."); return
4483:         no=tr.item(a[0])["values"][0]
4484:         data=self._get_doc_data(typ,no)
4485:         if not data:
4486:             messagebox.showwarning("Preview","Document not found."); return
4487:         title,header,cols,rows=data
4488:         header_lines=header
4489:         self.show_preview_window(title,header_lines,cols,rows)
4490: 
4491:     def doc_print_selected(self,typ,tr):
4492:         a=tr.selection()
4493:         if not a: return
4494:         no=tr.item(a[0])["values"][0]
```
```text
4525:         def _print_loaded_document():
4526:             data=self._get_doc_data(typ,no)
4527:             if not data:
4528:                 messagebox.showwarning("Document","Document not found."); return
4529:             title,header,cols,rows=data
4530:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4531:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4532: 
4533:     def _report_filter_popup(self, title, include_party=False):
4534:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4535:         win,winbody=self._internal_window(title,"520x420")
4536:         done=tk.BooleanVar(value=False)
4537:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4538:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4539:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4540:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4541:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4542:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4543:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4544:         if include_party:
4545:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4539:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4540:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4541:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4542:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4543:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4544:         if include_party:
4545:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4546:         def ok():
4547:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4548:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4549:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4550:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4551: 
4552:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4553:         self.clearbody()
4554:         # Report sub-sections use their own report toolbar; remove only the
4555:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4556:         children=self.body.winfo_children()
4557:         if children:
4558:             children[0].destroy()
4559:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4560:         if f.get("cancelled"):
4561:             self.dashboard();return
4562:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4563:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4564:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4565:         def load():
4566:             for i in tr.get_children():tr.delete(i)
4567:             params,where=params_builder(f)
4568:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4569:             for r in self.conn.execute(sql,params):
4570:                 vals=list(r)
4571:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4572:                 tr.insert("","end",values=vals)
4573:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4574:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4575:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4576:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4577:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4578:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4579:         def open_find_report():
4580:             state_find={"index":-1}
```
```text
4586:                 order=children[start:]+children[:start]
4587:                 for iid in order:
4588:                     vals=tr.item(iid,"values")
4589:                     if any(text in str(v).lower() for v in vals):
4590:                         state_find["index"]=children.index(iid)
4591:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4592:                 return False
4593:             self._open_exact_find_text_popup(search_fn)
4594:         self._item_master_find_callback=open_find_report
4595:         load()
4596:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4597: 
4598:     def report_grr(self):
4599:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4600:         def pb(f):
4601:             w=[];p=[]
4602:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4603:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4604:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4605:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4606:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4601:             w=[];p=[]
4602:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4603:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4604:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4605:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4606:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4607:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4608:             return p,w
4609:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4610: 
4611:     def report_demand(self):
4612:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4613:         def pb(f):
4614:             w=[];p=[]
4615:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4616:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4617:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4618:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4619:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4620:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4621:             return p,w
```
```text
4614:             w=[];p=[]
4615:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4616:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4617:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4618:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4619:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4620:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4621:             return p,w
4622:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4623: 
4624:     def report_issue(self):
4625:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4626:         def pb(f):
4627:             w=[];p=[]
4628:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4629:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4630:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4631:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4632:             return p,w
4633:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4634: 
```
```text
4627:             w=[];p=[]
4628:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4629:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4630:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4631:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4632:             return p,w
4633:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4634: 
4635:     def report_party(self):
4636:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4637:         def pb(f):
4638:             w=[];p=[]
4639:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4640:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4641:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4642:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4643:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4644:             return p,w
4645:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4646: 
4647:     def reports(self):
```
```text
4645:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4646: 
4647:     def reports(self):
4648:         self.clearbody()
4649:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4650: 
4651:         # ================= GRN Details =================
4652:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4653:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4654:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4655:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4656:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4657:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4658: 
4659:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4660:         def load_grr_item(codev=None):
4661:             for i in tr.get_children(): tr.delete(i)
4662:             q=codev.get().strip() if codev else ""
4663:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4664:             for r in self.conn.execute(sql,(q,) if q else ()):
4665:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4671:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4672:         tr=self.make_tree(fr,grr_cols,grr_widths)
4673:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4674:             for i in tr.get_children(): tr.delete(i)
4675:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4676:             conds=[];params=[]
4677:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4678:             if td: conds.append("g.grr_date<=?");params.append(td)
4679:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4680:             for r in self.conn.execute(sql,params):
4681:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4682:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4683:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4684:         load_grr_date(fdv,tdv)
4685: 
4686:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4687:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4688:         party=tk.StringVar(value="ALL")
4689:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4690:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4691:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4687:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4688:         party=tk.StringVar(value="ALL")
4689:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4690:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4691:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4692:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4693:         def load_party(*_):
4694:             for i in tr.get_children(): tr.delete(i)
4695:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4696:             if party.get()=="ALL":
4697:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4698:             else:
4699:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4700:             for r in rows:
4701:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4702:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4703:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4704: 
4705:         # ================= Demand Details =================
4706:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4707:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4703:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4704: 
4705:         # ================= Demand Details =================
4706:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4707:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4708:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4709:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4710:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4711:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4712: 
4713:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4714:         def load_dem_item(codev=None):
4715:             for i in tr.get_children(): tr.delete(i)
4716:             q=codev.get().strip() if codev else ""
4717:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4718:             for r in self.conn.execute(sql,(q,) if q else ()):
4719:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4720:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4721:         tr=self.make_tree(fr,dem_cols,dem_widths)
4722:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4723:         load_dem_item(codev)
```
```text
4725:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4726:         tr=self.make_tree(fr,dem_cols,dem_widths)
4727:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4728:             for i in tr.get_children(): tr.delete(i)
4729:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4730:             conds=[];params=[]
4731:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4732:             if td: conds.append("d.demand_date<=?");params.append(td)
4733:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4734:             for r in self.conn.execute(sql,params):
4735:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4736:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4737:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4738:         load_dem_date(fdv,tdv)
4739: 
4740:         # ================= Material Issue Details =================
4741:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4742:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4743:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4744:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4745:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4738:         load_dem_date(fdv,tdv)
4739: 
4740:         # ================= Material Issue Details =================
4741:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4742:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4743:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4744:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4745:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4746:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4747: 
4748:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4749:         def load_iss_item(codev=None):
4750:             for i in tr.get_children(): tr.delete(i)
4751:             q=codev.get().strip() if codev else ""
4752:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4753:             for r in self.conn.execute(sql,(q,) if q else ()):
4754:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4755:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4756:         tr=self.make_tree(fr,iss_cols,iss_widths)
4757:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4758:         load_iss_item(codev)
```
```text
4760:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4761:         tr=self.make_tree(fr,iss_cols,iss_widths)
4762:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4763:             for i in tr.get_children(): tr.delete(i)
4764:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4765:             conds=[];params=[]
4766:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4767:             if td: conds.append("i.issue_date<=?");params.append(td)
4768:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4769:             for r in self.conn.execute(sql,params):
4770:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4771:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4772:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4773:         load_iss_date(fdv,tdv)
4774: 
4775:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4776: 
4777:     def print_item_master(self):
4778:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4779:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4780: 
```
```text
4777:     def print_item_master(self):
4778:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4779:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4780: 
4781:     def print_party_master(self):
4782:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4783:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4784: 
4785:     def print_report(self,kind):
4786:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4787:         if kind=="grr":
4788:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4789:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4790:         elif kind=="demand":
4791:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4792:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4793:         elif kind=="issue":
4794:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4795:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4796:         else:
4797:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4798:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4799:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4800: 
4801:     def print_stock(self):
4802:         rows=[]
4803:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4804:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4805:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4806:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4807: 
4808:     def print_ledger(self):
4809:         rows=[]
4810:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4811:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4812:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4813:                 running += x[3] if x[1]=="GRR" else -x[3]
4814:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4815:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4816: 
4817:     def _get_doc_data(self, typ, no):
4818:         """Header + line items for one saved document, used by the on-screen
```
```text
4884:             sig=doc.add_table(rows=2,cols=3)
4885:             labels=["Prepared By","Store Keeper","Store Incharge"]
4886:             for i,label in enumerate(labels):
4887:                 sig.cell(0,i).text="____________________"
4888:                 sig.cell(1,i).text=label
4889:                 for para in sig.cell(1,i).paragraphs:
4890:                     for run in para.runs: run.bold=True
4891:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4892:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4893:         doc.save(path)
4894:         self.open_file(path)
4895: 
4896:     def export_excel(self, typ, no):
4897:         if not no or not no.strip():
4898:             return messagebox.showwarning("Excel Export","Select a document first.")
4899:         if not XLSX_AVAILABLE:
4900:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4901:         data=self._get_doc_data(typ,no)
4902:         if not data:
4903:             return messagebox.showwarning("Excel Export","Document not found.")
4904:         title,header,cols,rows=data
```
```text
4926:             for col in range(1,4):
4927:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4928:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4929:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4930:         for col_cells in ws.columns:
4931:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4932:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4933:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4934:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4935:         wb.save(path)
4936:         self.open_file(path)
4937: 
4938:     def preview_pdf(self,typ,no):
4939:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4940:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4941:         data=self._get_doc_data(typ,no)
4942:         if not data:return messagebox.showwarning("Document","Document not found.")
4943:         title,header,cols,rows=data
4944:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4945:         page_size = landscape(A4) if typ == "grr" else A4
4946:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4941:         data=self._get_doc_data(typ,no)
4942:         if not data:return messagebox.showwarning("Document","Document not found.")
4943:         title,header,cols,rows=data
4944:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4945:         page_size = landscape(A4) if typ == "grr" else A4
4946:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4947: 
4948:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4949:         """Open the print dialog with a real visual preview of the exact report.
4950: 
4951:         The report is rendered to a temporary PDF only in memory/on disk for the
4952:         duration of printing.  It is deleted after the print dialog closes, so
4953:         the Print button does not leave a PDF report behind.  Printing uses the
4954:         rendered report page itself rather than rebuilding rows as plain text;
4955:         this keeps the printed page identical to the application's report.
4956:         """
4957:         # Printing is always prepared as an A4 landscape page. This only affects
4958:         # the print path; the rest of the application's UI/report logic is unchanged.
4959:         page_size = landscape(A4)
4960:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
4961:             messagebox.showwarning(
```
```text
4963:                 "The print preview/printing components are not available.\n\n"
4964:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
4965:             )
4966:             return
4967:         if not rows and not columns:
4968:             messagebox.showwarning("Print", "There is no data to print.")
4969:             return
4970:         try:
4971:             os.makedirs(REPORTS_DIR, exist_ok=True)
4972:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
4973:             self._pdf_table_report(key,title,columns,rows,page_size,
4974:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
4975:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
4976:             self._select_windows_printer_for_pdf(key)
4977:         except Exception as e:
4978:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
4979: 
4980:     def _select_windows_printer_for_pdf(self, path):
4981:         """Print dialog with an actual page preview, printer selection and direct GDI output.
4982: 
4983:         The preview is rendered from the exact PDF produced by the application,
```
```text
5013:         job=getattr(self, "_print_jobs", {}).get(path)
5014:         if job:
5015:             title, header_lines, columns, rows, source_page_size = job
5016:         else:
5017:             title=os.path.splitext(os.path.basename(path))[0]
5018:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
5019: 
5020:         try:
5021:             doc=fitz.open(path)
5022:             total_pages=max(1,doc.page_count)
5023:         except Exception as e:
5024:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
5025:             return
5026: 
5027:         win=tk.Toplevel(self)
5028:         win.title("Printing from Win32 application - Print")
5029:         win.geometry("900x620")
5030:         win.minsize(850,580)
5031:         win.transient(self)
5032:         win.configure(bg="#f0f0f0")
5033: 
```
```text
5039:             pass
5040: 
5041:         outer=tk.Frame(win,bg="#f0f0f0")
5042:         outer.pack(fill="both",expand=True)
5043:         outer.columnconfigure(1,weight=1)
5044:         outer.rowconfigure(0,weight=1)
5045: 
5046:         # Left side mirrors the familiar system printer dialog: printers and
5047:         # print options. Right side contains the actual report page preview.
5048:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
5049:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
5050:         left.grid_propagate(False)
5051:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
5052:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
5053:         printer_list.pack(fill="x")
5054:         for pr in printers: printer_list.insert("end",pr)
5055:         try: printer_list.selection_set(printers.index(default_printer))
5056:         except Exception: printer_list.selection_set(0)
5057: 
5058:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
5059:         copies=tk.IntVar(value=1)
```
```text
5132:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5133: 
5134:         bottom=tk.Frame(win,bg="#f0f0f0")
5135:         # `outer` already uses pack() in `win`; using grid() for another direct
5136:         # child of the same toplevel raises TclError. Keep the action bar in the
5137:         # same geometry-manager family so Print/Cancel are always visible.
5138:         bottom.pack(fill="x",padx=12,pady=(0,12))
5139:         bottom.columnconfigure(0,weight=1)
5140:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5141:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5142:         print_btn=ttk.Button(bottom,text="Print",width=12)
5143:         print_btn.grid(row=0,column=2,padx=(8,0))
5144: 
5145:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5146: 
5147:         def parse_page_selection(total):
5148:             if pages_mode.get()=="All pages": return list(range(total))
5149:             raw=page_range.get().strip()
5150:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5151:             selected=[]
5152:             for part in raw.split(","):
```
```text
5149:             raw=page_range.get().strip()
5150:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5151:             selected=[]
5152:             for part in raw.split(","):
5153:                 part=part.strip()
5154:                 if "-" in part:
5155:                     a,b=part.split("-",1); a=int(a); b=int(b)
5156:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5157:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5158:                     selected.extend(range(a-1,b))
5159:                 else:
5160:                     n=int(part)
5161:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5162:                     selected.append(n-1)
5163:             return list(dict.fromkeys(selected))
5164: 
5165:         def selected_printer():
5166:             sel=printer_list.curselection()
5167:             return printer_list.get(sel[0]) if sel else printers[0]
5168: 
5169:         def print_rendered_pages():
```
```text
5262:                 finally:
5263:                     if hprinter is not None:
5264:                         try: win32print.ClosePrinter(hprinter)
5265:                         except Exception: pass
5266:                     if hdc:
5267:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5268:                         except Exception: pass
5269: 
5270:                 # Print the exact rendered PDF page through the printer DC.
5271:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5272:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5273:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5274:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5275: 
5276:                 for copy_no in range(count):
5277:                     dc.StartDoc(str(title)[:80])
5278:                     doc_ok=False
5279:                     try:
5280:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5281:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5282:                             dc.StartPage()
```
```text
5281:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5282:                             dc.StartPage()
5283:                             page_ok=False
5284:                             try:
5285:                                 cell_w=printable_w/float(cols_n)
5286:                                 cell_h=printable_h/float(rows_n)
5287:                                 for j,page_index in enumerate(batch):
5288:                                     page=doc.load_page(page_index)
5289:                                     pdf_w=max(1.0,float(page.rect.width))
5290:                                     pdf_h=max(1.0,float(page.rect.height))
5291:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5292:                                     fit=max(0.25,min(fit,8.0))
5293:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5294:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5295:                                     target_w=max(1,int(cell_w*0.96))
5296:                                     target_h=max(1,int(cell_h*0.96))
5297:                                     ratio=min(target_w/img.width,target_h/img.height)
5298:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5299:                                     if (nw,nh)!=(img.width,img.height):
5300:                                         img=img.resize((nw,nh),Image.LANCZOS)
5301:                                     dib=ImageWin.Dib(img)
```
```text
5321: 
5322:                 status.set("Print job sent successfully")
5323:                 win.update_idletasks()
5324:                 win.after(500,close)
5325:             except Exception as e:
5326:                 status.set("Print failed: "+str(e))
5327:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5328: 
5329:         def close():
5330:             try: doc.close()
5331:             except Exception: pass
5332:             try: win.destroy()
5333:             except Exception: pass
5334:             # Only the temporary PDF created by the Print button is removed.
5335:             # Existing report PDFs passed through the legacy print path are preserved.
5336:             try:
5337:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5338:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5339:             except Exception: pass
5340: 
5341:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5337:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5338:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5339:             except Exception: pass
5340: 
5341:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5342:         bottom.winfo_children()[1].configure(command=close)
5343:         print_btn.configure(command=print_rendered_pages)
5344:         win.protocol("WM_DELETE_WINDOW",close)
5345:         win.bind("<Escape>",lambda e:close())
5346:         win.grab_set()
5347:         # Keep the requested printer defaults visibly selected; no manual
5348:         # adjustment is required before pressing Print.
5349:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5350:         win.after(120,lambda:render_preview(0))
5351:         win.focus_force()
5352: 
5353:     def print_pdf(self,path):
5354:         """Open a printer-selection window for a generated PDF."""
5355:         path=os.path.abspath(path)
5356:         if not os.path.exists(path):
5357:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5353:     def print_pdf(self,path):
5354:         """Open a printer-selection window for a generated PDF."""
5355:         path=os.path.abspath(path)
5356:         if not os.path.exists(path):
5357:             messagebox.showwarning("Print", "The report file could not be found.")
5358:             return
5359: 
5360:         if sys.platform.startswith("win"):
5361:             self._select_windows_printer_for_pdf(path)
5362:             return
5363: 
5364:         try:
5365:             subprocess.run(["lp", path], check=True)
5366:         except Exception as e:
5367:             messagebox.showwarning(
5368:                 "Print",
5369:                 "The operating system could not start printing.\n\n"
5370:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5371:             )
5372: 
5373:     def open_file(self,path):
```
```text
5368:                 "Print",
5369:                 "The operating system could not start printing.\n\n"
5370:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5371:             )
5372: 
5373:     def open_file(self,path):
5374:         try:
5375:             if sys.platform.startswith("win"): os.startfile(path)
5376:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5377:             else: subprocess.Popen(["xdg-open",path])
5378:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5379: 
5380:     def print_demand(self,no):
5381:         data=self._get_doc_data("demand",no)
5382:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5383:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5384:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5385:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5386: 
5387:     def print_grr(self,no):
5388:         data=self._get_doc_data("grr",no)
```
```text
5382:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5383:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5384:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5385:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5386: 
5387:     def print_grr(self,no):
5388:         data=self._get_doc_data("grr",no)
5389:         if not data:return messagebox.showwarning("Document","GRN not found.")
5390:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5391:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5392:         # GRN has a wide item table. Generate the PDF itself in landscape so
5393:         # the printer dialog and printer driver receive a landscape document
5394:         # instead of a portrait page with rotated/cropped content.
5395:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5396: 
5397:     def print_issue(self,no):
5398:         data=self._get_doc_data("issue",no)
5399:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5400:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5401:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5402:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
```

## updater.py

- Lines: 158
- AST parse error: unexpected character after line continuation character (<unknown>, line 1)

### Relevant source locations

```text
0034:     if not download_url:
0035:         return False
0036:     for raw in (
0037:         os.path.expandvars(r"%PROGRAMFILES%\Internet Download Manager\IDMan.exe"),
0038:         os.path.expandvars(r"%PROGRAMFILES(x86)%\Internet Download Manager\IDMan.exe"),
0039:     ):
0040:         if os.path.isfile(raw):
0041:             try:
0042:                 subprocess.Popen([raw, "/d", download_url, "/n"], close_fds=True)
0043:                 return True
0044:             except Exception:
0045:                 pass
0046:     try:
0047:         return bool(webbrowser.open(download_url, new=2))
0048:     except Exception:
0049:         try:
0050:             os.startfile(download_url)
0051:             return True
0052:         except Exception:
0053:             return False
0054: 
```
```text
0078:         return False
0079:     candidates = [
0080:         os.path.expandvars(r"%PROGRAMFILES%\Internet Download Manager\IDMan.exe"),
0081:         os.path.expandvars(r"%PROGRAMFILES(x86)%\Internet Download Manager\IDMan.exe"),
0082:     ]
0083:     for idm in candidates:
0084:         if idm and os.path.isfile(idm):
0085:             try:
0086:                 subprocess.Popen([idm, "/d", download_url, "/n"], close_fds=True)
0087:                 return True
0088:             except Exception:
0089:                 pass
0090:     try:
0091:         return bool(webbrowser.open(download_url, new=2))
0092:     except Exception:
0093:         try:
0094:             os.startfile(download_url)
0095:             return True
0096:         except Exception:
0097:             return False
0098: 
```
