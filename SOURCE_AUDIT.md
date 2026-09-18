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

- Lines: 5438
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-436), restore_database(437-454), stock(456-461), fmt_num(463-465), to_iso_date(467-476), to_display_date(478-486), fiscal_year_key(488-499), fiscal_year_range(501-504), normalize_code(506-514), format_code(516-525), attach_code_mask(527-553), set_digits(530-535), key(536-546), paste(548-551), bind_add_to_list(555-576), on_enter(558-569), __init__(580-597), _check_for_updates(599-604), _setup_style(606-642), _shade(645-650), on_close(652-657), redo_network_setup(659-675), backup_now(677-684), restore_backup(686-704), _ctrl_f(706-718), _open_exact_find_text_popup(720-765), do_find(741-750), close(751-758), _global_enter(767-779), wipe(781-782), login(784-813), do_login(799-810), change_password(815-865), save_password(837-859), logout(867-872), home(874-900), _restore_dashboard_after_internal_close(902-916), _ensure_mdi_host(918-939), _internal_window(941-1027), normal_place(957-963), restore(964-971), maximize(972-978), minimize(979-994), close(995-1020), open_inventory_codes_detail_flow(1029-1047), open_inventory_codes_with_filters(1049-1063), open_inventory_codes_report_window(1065-1291), tbtn(1083-1088), balance_as_of(1145-1155), build_nav(1157-1179), selected_prefix(1181-1190), load(1192-1224), page_move(1226-1227), page_first(1228-1228), page_last(1229-1233), on_nav(1237-1238), find_popup(1241-1260), search_fn(1243-1258), print_report(1263-1266), export_pdf(1268-1270), export_word(1271-1273), export_excel(1274-1276), open_menu_window(1293-1315), close_window(1303-1310), _manual_check_update(1317-1321), _show_current_version(1323-1327), build_menu_bar(1329-1376), open_calendar_picker(1378-1426), pick(1396-1398), redraw(1400-1412), nav(1414-1418), make_date_field(1428-1435), clearbody(1437-1463), run_action(1452-1457), _portable_print_current(1465-1476), portable_print_dialog(1478-1551), build_receipt(1505-1523), send(1524-1537), refresh_printers(1538-1544), preview_tree(1553-1565), set_page_actions(1567-1575), _add_transaction_new_button(1577-1594), _report_header(1596-1660), _report_footer(1662-1668), _grr_signature_block(1670-1686), _finish_page(1688-1689), _wrap_text_to_width(1691-1716), fits(1698-1698), _pdf_table_report(1718-1787), table_header(1740-1745), show_preview_window(1789-1862), _safe_report_name(1864-1867), print_preview_window(1869-1872), _fallback_pdf_export(1874-1907), esc(1878-1879), add(1882-1884), _save_entry_report(1909-1929), export_preview_pdf(1931-1960), export_preview_word(1962-2002), export_preview_excel(2004-2040), make_tree(2042-2051), pick_item(2053-2074), choose(2054-2073), ld(2061-2065), sel(2067-2071), bind_item_lookup(2076-2093), lookup(2078-2091), _set_form_editable(2096-2109), walk(2099-2108), document_selector(2111-2145), refresh(2116-2127), selected(2128-2133), dashboard(2147-2259), load_details(2231-2255), _refresh_dashboard_kpis(2261-2275), dashboard_details(2277-2281), item_history(2283-2303), _ask_item_master_filters(2305-2389), finish(2358-2370), items(2391-2629), hierarchy(2432-2441), selected_prefix(2487-2500), balance_as_of(2502-2509), load(2511-2549), set_page(2551-2552), select_node(2554-2575), open_find(2581-2600), search_fn(2583-2598), visible_rows(2605-2607), print_inventory(2608-2612), export_inventory_word(2613-2615), export_inventory_excel(2616-2618), portable_inventory(2623-2625), inventory_codes(2631-2915), btn(2667-2672), close_editor(2708-2718), edit_cell(2720-2746), commit(2738-2744), rows_query(2748-2761), load(2763-2778), new_record(2780-2801), commit(2794-2798), selected_row(2803-2805), edit_record(2807-2815), save_record(2817-2860), delete_record(2862-2873), refresh(2875-2875), do_print(2876-2878), do_close(2879-2879), filter_grid(2897-2904), open_mto_inventory_flow(2917-2940), open_code_opening_flow(2942-2950), code_opening(2952-2953), _open_code_opening_popup(2955-2956), _open_code_opening_detail(2958-3201), norm(3028-3029), table_for(3031-3032), row_for(3034-3039), search_any_destination(3041-3054), desc_hit(3056-3060), clear_form(3062-3075), load_for_edit(3077-3098), check_duplicates(3100-3111), save_code(3116-3167), edit_action(3169-3173), delete_code(3175-3190), _mto_new_item_dialog(3203-3239), save(3219-3236), _item_filter_bar(3241-3253), _date_filter_bar(3255-3263), _ask_mto_inventory_filters(3265-3310), finish(3295-3303), mto_inventory(3312-3512), open_find(3346-3365), search_fn(3348-3363), hierarchy(3384-3388), rebuild_nav(3390-3401), mto_balance(3425-3434), load(3436-3478), set_page(3480-3480), select_node(3481-3490), visible_rows(3495-3495), do_print(3496-3500), export_word(3501-3503), export_excel(3504-3506), party_master(3514-3565), load(3524-3527), clear(3528-3532), new_form(3533-3534), save(3535-3541), load_party_row(3542-3546), on_party_select(3547-3548), edit(3550-3554), delete_party(3555-3561), user_management(3567-3651), sync_role(3594-3599), load(3603-3606), clear(3607-3610), edit(3611-3618), save(3619-3636), delete_user(3637-3648), _renumber_tree(3654-3657), demand(3659-3823), _restore_demand_tree_columns(3702-3708), add(3711-3719), edit_item(3721-3733), delete_item(3735-3743), new_form(3747-3753), save(3755-3771), delete_current(3775-3781), cancel_form(3782-3790), preview_now(3791-3801), edit_saved_demand(3802-3805), print_now(3806-3816), load_demand_into_form(3825-3837), refresh_saved_cache(3839-3851), grr(3853-4016), add(3885-3893), edit_item(3895-3905), delete_item(3907-3915), new_form(3919-3925), save(3927-3948), delete_current(3952-3958), cancel_form(3959-3967), preview_now(3968-3986), portable_current(3987-3990), edit_saved_grr(3992-3995), print_now(3996-4009), load_grr_into_form(4018-4030), issue(4032-4178), old_issue_qty(4061-4064), update_balance(4065-4073), add(4075-4084), edit_item(4086-4097), new_form(4101-4107), post(4109-4130), delete_current(4131-4137), cancel_form(4138-4146), preview_now(4147-4154), portable_current(4155-4157), load_saved_issue(4162-4164), edit_saved_issue(4165-4168), print_issue_now(4169-4174), load_issue_into_form(4180-4193), _ask_report_criteria(4195-4258), finish(4244-4252), _open_report_child(4260-4265), open_stock_balance_report_flow(4267-4270), open_grr_report_flow(4272-4275), open_demand_report_flow(4277-4280), open_issue_report_flow(4282-4285), open_party_report_flow(4287-4290), _ask_stock_balance_filters(4292-4315), ok(4307-4308), cancel(4309-4309), stock_balance(4317-4380), period(4333-4344), header_summary(4345-4346), load(4347-4356), reopen_filters(4357-4361), open_find_stock(4365-4378), search_fn(4367-4377), ledger(4382-4394), open_document_editor(4396-4404), _edit_from_selector(4406-4422), show_saved_records(4424-4455), view(4447-4451), documents(4457-4502), edit_selected(4476-4482), delete_selected(4483-4495), doc_export_selected(4504-4510), doc_preview_selected(4512-4522), doc_print_selected(4524-4532), load_document(4534-4564), _print_loaded_document(4558-4563), _report_filter_popup(4566-4583), ok(4579-4580), cancel(4581-4581), _report_window(4585-4629), load(4598-4605), hdr(4606-4606), open_find_report(4612-4626), search_fn(4614-4625), report_grr(4631-4642), pb(4633-4641), report_demand(4644-4655), pb(4646-4654), report_issue(4657-4666), pb(4659-4665), report_party(4668-4678), pb(4670-4677), reports(4680-4808), load_grr_item(4693-4698), load_grr_date(4706-4714), load_party(4726-4734), load_dem_item(4747-4752), load_dem_date(4760-4768), load_iss_item(4782-4787), load_iss_date(4795-4803), print_item_master(4810-4812), print_party_master(4814-4816), print_report(4818-4832), print_stock(4834-4839), print_ledger(4841-4848), _get_doc_data(4850-4878), export_word(4880-4927), export_excel(4929-4969), preview_pdf(4971-4979), _open_direct_printer(4981-5011), _select_windows_printer_for_pdf(5013-5384), render_preview(5138-5157), on_resize(5159-5161), parse_page_selection(5180-5196), selected_printer(5198-5200), print_rendered_pages(5202-5360), close(5362-5372), print_pdf(5386-5404), open_file(5406-5411), print_demand(5413-5418), print_grr(5420-5428), print_issue(5430-5435)

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
0987:             b.pack(side="left")
0988:             rb=tk.Button(item,text="□",font=("Segoe UI",8,"bold"),width=2,height=1,padx=0,pady=0,
0989:                          command=lambda:(restore(),maximize()),relief="flat",bd=0,bg="#e7e7e7")
0990:             rb.pack(side="left")
0991:             xb=tk.Button(item,text="×",font=("Segoe UI",9,"bold"),width=2,height=1,padx=0,pady=0,
0992:                          command=close,relief="flat",bd=0,bg="#e7e7e7")
0993:             xb.pack(side="left")
0994:             state["task"]=item
0995:         def close():
0996:             try:
0997:                 task=state.get("task")
0998:                 if task and task.winfo_exists(): task.destroy()
0999:             except Exception: pass
1000:             try:
1001:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
1002:             except Exception: pass
1003:             try: outer.destroy()
1004:             except Exception: pass
1005:             if not getattr(self,"_mdi_windows",[]):
1006:                 self._mdi_host.place_forget()
1007:                 self._restore_dashboard_after_internal_close()
```
```text
1000:             try:
1001:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
1002:             except Exception: pass
1003:             try: outer.destroy()
1004:             except Exception: pass
1005:             if not getattr(self,"_mdi_windows",[]):
1006:                 self._mdi_host.place_forget()
1007:                 self._restore_dashboard_after_internal_close()
1008:                 self._restore_dashboard_after_internal_close()
1009:                 # Restore the original application shell FIRST, then rebuild
1010:                 # only the Dashboard body. This keeps the top header/navigation
1011:                 # exactly as they are when the application starts.
1012:                 try:
1013:                     if getattr(self,"_shell_header",None) is not None and self._shell_header.winfo_exists():
1014:                         self._shell_header.pack(fill="x",before=self.body)
1015:                     if getattr(self,"_shell_nav",None) is not None and self._shell_nav.winfo_exists():
1016:                         self._shell_nav.pack(fill="x",before=self.body,after=self._shell_header)
1017:                 except Exception: pass
1018:                 try:
1019:                     self.dashboard()
1020:                 except Exception: pass
```
```text
1053:             return None
1054:         self._inventory_codes_filter=criteria
1055:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1056:         try:
1057:             self.items(container=body)
1058:             win.lift()
1059:             return win
1060:         except Exception:
1061:             try: win._internal_close()
1062:             except Exception: pass
1063:             raise
1064: 
1065:     def open_inventory_codes_report_window(self, criteria=None):
1066:         """Open Inventory Codes as a real report-style child window.
1067: 
1068:         This intentionally mirrors the supplied Preview Report workflow: a
1069:         separate resizable/maximizable window with a left navigation tree,
1070:         compact report toolbar, Find dialog, and print/export commands.
1071:         The main application remains open behind it.
1072:         """
1073:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
1070:         compact report toolbar, Find dialog, and print/export commands.
1071:         The main application remains open behind it.
1072:         """
1073:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
1074:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
1075:         }
1076:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1077: 
1078:         # --- report-style toolbar ---
1079:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
1080:         toolbar.pack(fill="x",side="top")
1081:         toolbar.pack_propagate(False)
1082: 
1083:         def tbtn(text,cmd,width=9):
1084:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
1085:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
1086:                          padx=3,pady=1)
1087:             b.pack(side="left",padx=2,pady=6)
1088:             return b
1089: 
1090:         # --- main report body ---
```
```text
1101:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
1102:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
1103:         navscroll.config(command=code_tree.yview)
1104:         navscroll.pack(side="right",fill="y")
1105:         code_tree.pack(side="left",fill="both",expand=True)
1106: 
1107:         right=tk.Frame(content,bg="#EDEDED")
1108:         right.pack(side="left",fill="both",expand=True)
1109:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
1110:         reportbar.pack(fill="x")
1111:         reportbar.pack_propagate(False)
1112:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
1113:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
1114:         tab.pack(side="left",padx=4,pady=2)
1115:         titlevar=tk.StringVar(value="Inventory Summary")
1116:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
1117:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
1118: 
1119:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
1120:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
1121:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1255:                     vals=tree.item(iid,"values")
1256:                     if str(vals[1]).lower()==str(target).lower():
1257:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1258:                 return True
1259:             self._open_exact_find_text_popup(search_fn)
1260:             self._item_master_find_callback=find_popup
1261: 
1262: 
1263:         def print_report():
1264:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1265:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1266:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1267: 
1268:         def export_pdf():
1269:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1270:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1271:         def export_word():
1272:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1273:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1274:         def export_excel():
1275:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1271:         def export_word():
1272:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1273:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1274:         def export_excel():
1275:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1276:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1277: 
1278:         tbtn("Find",find_popup,7)
1279:         tbtn("Print",print_report,7)
1280:         tbtn("PDF",export_pdf,6)
1281:         tbtn("Word",export_word,6)
1282:         tbtn("Excel",export_excel,6)
1283:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1284:         tbtn("Refresh",load,8)
1285:         tbtn("Close",win._internal_close,7)
1286:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1287:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1288: 
1289:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1290:         build_nav(); load(); win.focus_force()
1291:         return win
```
```text
1301:         self.body=frame
1302:         closed={"done":False}
1303:         def close_window():
1304:             if closed["done"]: return
1305:             closed["done"]=True
1306:             if getattr(self,"body",None) is frame: self.body=old_body
1307:             self._page_actions=old_actions
1308:             self._item_master_find_callback=old_find
1309:             try: win._internal_close()
1310:             except Exception: win.destroy()
1311:         win._internal_close=close_window
1312:         try:
1313:             method(); self.update_idletasks(); win.lift(); return win
1314:         except Exception:
1315:             close_window(); raise
1316: 
1317:     def _manual_check_update(self):
1318:         try:
1319:             updater.check_for_update(self, manual=True)
1320:         except Exception as e:
1321:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1325:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1326:         except Exception as e:
1327:             messagebox.showerror("Current Version", str(e), parent=self)
1328: 
1329:     def build_menu_bar(self):
1330:         """Professional section / sub-section menu bar, ERP style:
1331:         Inventory > Item Master
1332:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1333:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1334:         Edit > Change Password, User Management
1335:         Help > Backup Now, Restore Backup, Network Setup
1336:         """
1337:         menubar=tk.Menu(self)
1338: 
1339:         m_inv=tk.Menu(menubar,tearoff=0)
1340:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1341:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1342:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1343:         menubar.add_cascade(label="Inventory",menu=m_inv)
1344: 
1345:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1345:         m_trans=tk.Menu(menubar,tearoff=0)
1346:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1347:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1348:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1349:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1350:         menubar.add_cascade(label="Transaction",menu=m_trans)
1351: 
1352:         m_rep=tk.Menu(menubar,tearoff=0)
1353:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1354:         m_rep.add_separator()
1355:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1356:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1357:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1358:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1359:         menubar.add_cascade(label="Report",menu=m_rep)
1360: 
1361:         m_edit=tk.Menu(menubar,tearoff=0)
1362:         m_edit.add_command(label="Change Password",command=self.change_password)
1363:         if self.is_admin:
1364:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1365:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1360: 
1361:         m_edit=tk.Menu(menubar,tearoff=0)
1362:         m_edit.add_command(label="Change Password",command=self.change_password)
1363:         if self.is_admin:
1364:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1365:         menubar.add_cascade(label="Edit",menu=m_edit)
1366: 
1367:         m_help=tk.Menu(menubar,tearoff=0)
1368:         m_help.add_command(label="Backup Now",command=self.backup_now)
1369:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1370:         m_help.add_command(label="Current Version",command=self._show_current_version)
1371:         if self.is_admin:
1372:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1373:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1374:         menubar.add_cascade(label="Help",menu=m_help)
1375: 
1376:         self.config(menu=menubar)
1377: 
1378:     def open_calendar_picker(self, var):
1379:         """Small month-grid calendar popup. Picking a day sets `var` to
1380:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1433:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1434:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1435:         return f
1436: 
1437:     def clearbody(self):
1438:         self._portable_print_context=None
1439:         for w in self.body.winfo_children(): w.destroy()
1440:         self._page_actions = {
1441:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1442:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1443:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1444:             "cancel": lambda: self.dashboard(),
1445:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1446:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1447:         }
1448:         # Single SAP-style toolbar at the very top.
1449:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1450:         self._page_action_bar=bar
1451:         self._page_action_first_button=None
1452:         def run_action(k):
1453:             if k=="edit" and not self.can_edit:
```
```text
1450:         self._page_action_bar=bar
1451:         self._page_action_first_button=None
1452:         def run_action(k):
1453:             if k=="edit" and not self.can_edit:
1454:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1455:             if k=="delete" and not self.can_delete:
1456:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1457:             self._page_actions[k]()
1458:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1459:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1460:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1461:             b.pack(side="left",padx=(0,2))
1462:             if self._page_action_first_button is None: self._page_action_first_button=b
1463:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1464: 
1465:     def _portable_print_current(self):
1466:         ctx=getattr(self,"_portable_print_context",None)
1467:         if not ctx:
1468:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1469:             return
1470:         try:
```
```text
1472:             if not data: return
1473:             title,header,columns,rows=data
1474:             self.portable_print_dialog(title,header,columns,rows)
1475:         except Exception as e:
1476:             messagebox.showerror("Portable Printer",str(e))
1477: 
1478:     def portable_print_dialog(self,title,header_lines,columns,rows):
1479:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1480:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1481:         if not WIN32PRINT_AVAILABLE:
1482:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1483:             return
1484:         try:
1485:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1486:         except Exception as e:
1487:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1488:             return
1489:         if not printers:
1490:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1491:             return
1492:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1542:                 if vals and pv.get() not in vals: pv.set(vals[0])
1543:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1544:             except Exception as ex: status.set(str(ex))
1545:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1546:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1547:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1548:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1549:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1550:         win.bind("<Escape>",lambda e:win._internal_close())
1551:         win.focus_force()
1552: 
1553:     def preview_tree(self, title, tree, header_lines=None):
1554:         """Preview the exact rows currently visible in a Treeview."""
1555:         cols=list(tree["columns"])
1556:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1557:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1558:         if not rows:
1559:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1560:             return
1561:         widths=[]
1562:         for c in cols:
```
```text
1559:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1560:             return
1561:         widths=[]
1562:         for c in cols:
1563:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1564:             except Exception: widths.append(100)
1565:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1566: 
1567:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1568:         self._page_actions.update({
1569:             "save": save or self._page_actions.get("save"),
1570:             "edit": edit or self._page_actions.get("edit"),
1571:             "delete": delete or self._page_actions.get("delete"),
1572:             "cancel": cancel or self._page_actions.get("cancel"),
1573:             "print": print or self._page_actions.get("print"),
1574:             "preview": preview or self._page_actions.get("preview"),
1575:         })
1576: 
1577:     def _add_transaction_new_button(self, command):
1578:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1579:         if bar is None or first is None: return
```
```text
1588:         sep.pack(side="left",fill="y",padx=4)
1589:         for w in existing:
1590:             try:
1591:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1592:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1593:                 else: w.pack(side="left")
1594:             except Exception: pass
1595: 
1596:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1597:         """Draw a consistent professional report header and return the first table Y.
1598: 
1599:         For GRN Receipt reports the document number is shown on the left and
1600:         the GRN Date is deliberately shown on the right in a bordered document
1601:         information panel.
1602:         """
1603:         W,H=page_size
1604:         if y_top is None: y_top=H-24
1605:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1606:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1607:         if os.path.exists(LOGO_FILE):
1608:             try:
```
```text
1601:         information panel.
1602:         """
1603:         W,H=page_size
1604:         if y_top is None: y_top=H-24
1605:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1606:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1607:         if os.path.exists(LOGO_FILE):
1608:             try:
1609:                 from reportlab.lib.utils import ImageReader
1610:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1611:             except Exception:
1612:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1613:         else:
1614:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1615:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1616:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1617:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1618:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1619: 
1620:         # Professional document information box.
1621:         info_top=logo_y-12
```
```text
1654:                 # naturally occupies the right-hand cell when supplied second.
1655:                 c.setFont("Helvetica-Bold",7)
1656:                 c.drawString(xx,yy,(label+":")[:28])
1657:                 c.setFont("Helvetica",7)
1658:                 c.drawString(xx+58,yy,val[:58])
1659:             return box_y-12
1660:         return info_top-6
1661: 
1662:     def _report_footer(self, c, page_no, page_size=A4):
1663:         W,H=page_size
1664:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1665:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1666:         c.drawString(24,13,REPORT_FOOTER)
1667:         c.drawRightString(W-24,13,f"Page {page_no}")
1668:         c.setFillColorRGB(0,0,0)
1669: 
1670:     def _grr_signature_block(self, c, y, page_size=A4):
1671:         """Draw the three requested transaction-document signature lines."""
1672:         W,H=page_size
1673:         labels=["Prepared By","Store Keeper","Store Incharge"]
1674:         block_h=70
```
```text
1681:             x=left+i*col_w
1682:             c.setLineWidth(0.6)
1683:             c.line(x+30,top-34,x+col_w-30,top-34)
1684:             c.setFont("Helvetica-Bold",7)
1685:             c.drawCentredString(x+col_w/2,top-48,label)
1686:         return True
1687: 
1688:     def _finish_page(self, c, page_no, page_size=A4):
1689:         self._report_footer(c,page_no,page_size); c.showPage()
1690: 
1691:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1692:         """Word-wrap `text` into a list of lines that each fit inside
1693:         max_width (points) at the given font, breaking mid-word only when a
1694:         single word is itself wider than the column."""
1695:         text=str(text) if text is not None else ""
1696:         if not text:
1697:             return [""]
1698:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1699:         lines=[]; cur=""
1700:         for word in text.split(" "):
1701:             trial=(cur+" "+word).strip() if cur else word
```
```text
1710:                     mid=(lo+hi)//2
1711:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1712:                     else: hi=mid-1
1713:                 lines.append(w[:fit_at]); w=w[fit_at:]
1714:             cur=w
1715:         if cur: lines.append(cur)
1716:         return lines or [""]
1717: 
1718:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1719:         """Create a paginated professional PDF with logo, bordered information,
1720:         GRR signature lines and page numbers. Also keep the same report data in
1721:         memory so the built-in Windows printer dialog can print directly without
1722:         requiring a PDF application's PrintTo association."""
1723:         if not hasattr(self, "_print_jobs"):
1724:             self._print_jobs = {}
1725:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1726:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1727:         page=1
1728:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1729:         usable=W-56
1730:         n=max(1,len(headers))
```
```text
1752:             if desc_idx is not None and desc_idx < len(r):
1753:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1754:             else:
1755:                 desc_lines=[""]
1756:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1757:             # Reserve room on the final page for the three transaction signatures + footer.
1758:             reserve=120 if is_transaction_doc else 42
1759:             if y-row_h<reserve:
1760:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1761:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1762:             # Item rows are intentionally border-free. The section/header remains
1763:             # professional while avoiding the unwanted boxed line around each
1764:             # individual printed item row. Description is drawn separately
1765:             # below (auto-fit / wrapped), so it is skipped in this pass.
1766:             for ci,(xx,val) in enumerate(zip(xs,r)):
1767:                 if ci==desc_idx: continue
1768:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1769:             if desc_idx is not None and desc_idx < len(r):
1770:                 for li,ln in enumerate(desc_lines):
1771:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1772:             y-=row_h
```
```text
1767:                 if ci==desc_idx: continue
1768:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1769:             if desc_idx is not None and desc_idx < len(r):
1770:                 for li,ln in enumerate(desc_lines):
1771:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1772:             y-=row_h
1773:         if is_transaction_doc:
1774:             # Keep the three requested transaction signatures at the physical bottom
1775:             # final page, immediately above the report footer.  If the item
1776:             # table reaches this reserved area, start a fresh final page.
1777:             bottom_sig_y = 138
1778:             if y < 165:
1779:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1780:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1781:             # Draw signatures at a fixed bottom position so they never float
1782:             # directly after the last item row.
1783:             self._grr_signature_block(c,bottom_sig_y,page_size)
1784:         self._report_footer(c,page,page_size); c.save()
1785:         if auto_print:
1786:             self.print_pdf(path)
1787:         return path
```
```text
1781:             # Draw signatures at a fixed bottom position so they never float
1782:             # directly after the last item row.
1783:             self._grr_signature_block(c,bottom_sig_y,page_size)
1784:         self._report_footer(c,page,page_size); c.save()
1785:         if auto_print:
1786:             self.print_pdf(path)
1787:         return path
1788: 
1789:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1790:         """Professional on-screen preview showing bordered document information
1791:         and a bordered item section. GRN Date is displayed in the right column."""
1792:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1793:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1794:         # Preview intentionally hides the company logo and company name.
1795:         # The actual generated/printed PDF still contains both via
1796:         # _report_header(), so only the on-screen preview is affected.
1797:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1798:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1799:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1800: 
1801:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
```
```text
1822:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1823: 
1824:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1825:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1826:         tr=self.make_tree(items,columns,widths)
1827:         for r in rows: tr.insert("", "end", values=r)
1828: 
1829:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1830:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1831:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1832:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1833:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1834:         win.bind("<Control-f>",bind_preview_find)
1835:         win.bind("<Control-F>",bind_preview_find)
1836: 
1837:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1838:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1839:         if is_transaction_preview:
1840:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1841:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1842:                 sig.columnconfigure(i,weight=1)
```
```text
1840:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1841:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1842:                 sig.columnconfigure(i,weight=1)
1843:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1844:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1845:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1846: 
1847:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1848:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1849:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1850:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1851:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1852:         if on_save:
1853:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1854:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1855:         if not is_transaction_preview:
1856:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1857:         # IMPORTANT: this must remain a normal top-level window (not transient
1858:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1859:         # exactly like the Preview Report window in the supplied recording.
1860:         # The Find dialog is opened from this window and is independent.
```
```text
1853:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1854:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1855:         if not is_transaction_preview:
1856:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1857:         # IMPORTANT: this must remain a normal top-level window (not transient
1858:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1859:         # exactly like the Preview Report window in the supplied recording.
1860:         # The Find dialog is opened from this window and is independent.
1861:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1862:         win.focus_force()
1863: 
1864:     def _safe_report_name(self, title, extension):
1865:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1866:         safe=safe.replace(" ","_") or "Preview"
1867:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1868: 
1869:     def print_preview_window(self, title, header_lines, columns, rows):
1870:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1871:         self._open_direct_printer(title, header_lines, columns, rows,
1872:                                   landscape(A4) if len(columns) > 8 else A4)
1873: 
```
```text
1866:         safe=safe.replace(" ","_") or "Preview"
1867:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1868: 
1869:     def print_preview_window(self, title, header_lines, columns, rows):
1870:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1871:         self._open_direct_printer(title, header_lines, columns, rows,
1872:                                   landscape(A4) if len(columns) > 8 else A4)
1873: 
1874:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1875:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1876:         This keeps the Export PDF button functional on a machine where the bundled
1877:         ReportLab package cannot be imported."""
1878:         def esc(v):
1879:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1880:         W,H=842,595
1881:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1882:         def add(txt,size=8,leading=11):
1883:             lines.append(f"/F1 {size} Tf")
1884:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1885:         add(str(title),12,16)
1886:         for h in header_lines or []:
```
```text
1893:         lines.append("ET")
1894:         stream="\n".join(lines).encode("latin-1","replace")
1895:         objs=[]
1896:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1897:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1898:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1899:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1900:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1901:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1902:         for i,obj in enumerate(objs,1):
1903:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1904:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1905:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1906:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1907:         with open(path,"wb") as f: f.write(out)
1908: 
1909:     def _save_entry_report(self, title, header_lines, columns, rows):
1910:         try:
1911:             os.makedirs(REPORTS_DIR, exist_ok=True)
1912:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1913:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```
```text
1906:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1907:         with open(path,"wb") as f: f.write(out)
1908: 
1909:     def _save_entry_report(self, title, header_lines, columns, rows):
1910:         try:
1911:             os.makedirs(REPORTS_DIR, exist_ok=True)
1912:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1913:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
1914:             path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
1915:             page_size = landscape(A4) if len(columns) > 8 else A4
1916:             if REPORTLAB:
1917:                 self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
1918:             else:
1919:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1920:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1921:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1922:             with open(path, "rb") as f:
1923:                 if f.read(5) != b"%PDF-":
1924:                     raise IOError("Generated report is not a valid PDF.")
1925:             self._last_entry_report_path = path
1926:             return path
```
```text
1920:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1921:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1922:             with open(path, "rb") as f:
1923:                 if f.read(5) != b"%PDF-":
1924:                     raise IOError("Generated report is not a valid PDF.")
1925:             self._last_entry_report_path = path
1926:             return path
1927:         except Exception as exc:
1928:             self._last_entry_report_path = None
1929:             return None
1930: 
1931:     def export_preview_pdf(self, title, header_lines, columns, rows):
1932:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1933:         try:
1934:             os.makedirs(REPORTS_DIR, exist_ok=True)
1935:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1936:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1937:             generated = False
1938:             if REPORTLAB:
1939:                 try:
1940:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
```
```text
1937:             generated = False
1938:             if REPORTLAB:
1939:                 try:
1940:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1941:                     generated = True
1942:                 except Exception:
1943:                     generated = False
1944:             if not generated:
1945:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1946:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1947:                 raise IOError("The PDF file was not created in the Reports folder.")
1948:             with open(path, "rb") as pf:
1949:                 signature = pf.read(5)
1950:             if signature != b"%PDF-":
1951:                 raise IOError("The generated file is not a valid PDF.")
1952:             self._last_report_path = path
1953:             try:
1954:                 webbrowser.open("file://" + path)
1955:             except Exception:
1956:                 self.open_file(path)
1957:             return path
```
```text
1951:                 raise IOError("The generated file is not a valid PDF.")
1952:             self._last_report_path = path
1953:             try:
1954:                 webbrowser.open("file://" + path)
1955:             except Exception:
1956:                 self.open_file(path)
1957:             return path
1958:         except Exception as e:
1959:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1960:             return None
1961: 
1962:     def export_preview_word(self, title, header_lines, columns, rows):
1963:         """Export exactly what is visible in the current preview to Word."""
1964:         if not DOCX_AVAILABLE:
1965:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1966:         path=self._safe_report_name(title,"docx")
1967:         doc=Document()
1968:         sec=doc.sections[0]
1969:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1970:         sec.header.paragraphs[0].runs[0].bold=True
1971:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
```
```text
1993:             doc.add_paragraph("")
1994:             sig=doc.add_table(rows=2,cols=3)
1995:             labels=["Prepared By","Store Keeper","Store Incharge"]
1996:             for i,label in enumerate(labels):
1997:                 sig.cell(0,i).text="____________________"
1998:                 sig.cell(1,i).text=label
1999:                 for para in sig.cell(1,i).paragraphs:
2000:                     for run in para.runs: run.bold=True
2001:         doc.save(path)
2002:         self.open_file(path)
2003: 
2004:     def export_preview_excel(self, title, header_lines, columns, rows):
2005:         """Export exactly what is visible in the current preview to Excel."""
2006:         if not XLSX_AVAILABLE:
2007:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
2008:         path=self._safe_report_name(title,"xlsx")
2009:         wb=openpyxl.Workbook(); ws=wb.active
2010:         ws.title="Preview"
2011:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
2012:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
2013:         if not is_transaction_preview:
```
```text
2031:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
2032:             for col in range(1,4):
2033:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
2034:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
2035:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
2036:         for col_cells in ws.columns:
2037:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
2038:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
2039:         wb.save(path)
2040:         self.open_file(path)
2041: 
2042:     def make_tree(self,parent,cols,widths=None):
2043:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
2044:         tr=ttk.Treeview(fr,columns=cols,show="headings")
2045:         for i,c in enumerate(cols):
2046:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
2047:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
2048:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
2049:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
2050:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
2051:         return tr
```
```text
2104:                     w.state(["!disabled"] if editable else ["disabled"])
2105:             except Exception:
2106:                 try: w.configure(state="normal" if editable else "disabled")
2107:                 except Exception: pass
2108:             for ch in w.winfo_children(): walk(ch)
2109:         for root in roots: walk(root)
2110: 
2111:     def document_selector(self, parent, label, typ, var, load_callback):
2112:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
2113:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
2114:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
2115:         combo.pack(side="left", padx=4)
2116:         def refresh():
2117:             vals=[]
2118:             if typ=="demand":
2119:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
2120:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
2121:             elif typ=="grr":
2122:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
2123:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
2124:             else:
```
```text
2131:             no=text.split(" -> ",1)[0].strip()
2132:             var.set(no)
2133:             load_callback(no)
2134:         combo.bind("<<ComboboxSelected>>", selected)
2135:         combo.bind("<Return>", selected)
2136:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2137:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2138:         refresh()
2139:         # Keep the currently open transaction's saved-record list live.
2140:         # Each save calls refresh_saved_cache(), so newly saved records appear
2141:         # immediately without closing/reopening the window or pressing Refresh.
2142:         if not hasattr(self, "_document_selector_refreshers"):
2143:             self._document_selector_refreshers = {}
2144:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2145:         return combo
2146: 
2147:     def dashboard(self):
2148:         # Dashboard-only visual refresh. All existing data queries, filters,
2149:         # callbacks and report/detail behavior are intentionally preserved.
2150:         self.clearbody()
2151:         c=self.conn
```
```text
2232:             for x in tr.get_children(): tr.delete(x)
2233:             params=[];where=[]
2234:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2235:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2236:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2237:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2238:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2239:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2240:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2241:                    FROM transactions t JOIN items i ON i.code=t.code"""
2242:             if where: sql += " WHERE " + " AND ".join(where)
2243:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2244:             rows=list(c.execute(sql,params))
2245:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2246:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2247:             bal_after={}
2248:             for txid,cc,typ,qty in alltx:
2249:                 running.setdefault(cc,0.0)
2250:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2251:                 bal_after[txid]=running[cc]
2252:             for r in rows:
```
```text
2627:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2628:         load()
2629:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2630: 
2631:     def inventory_codes(self):
2632:         """Inventory Codes using the classic desktop inventory interface.
2633: 
2634:         This screen intentionally follows the uploaded Inventory Management
2635:         reference: a simple module title, compact New/Edit/Delete/Save/
2636:         Refresh/Print/Close action row, and a full-width editable data grid.
2637:         All records come from the V18 database, so existing inventory data is
2638:         preserved rather than recreated.
2639:         """
2640:         self.clearbody()
2641:         # Remove the generic SAP action row; this page owns its own classic
2642:         # action row just like the reference Inventory/Items screen.
2643:         if self.body.winfo_children():
2644:             try:
2645:                 self.body.winfo_children()[0].destroy()
2646:             except Exception:
2647:                 pass
```
```text
2700:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2701:         if filter_text:
2702:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2703:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2704: 
2705:         editing={"id":None,"new":False}
2706:         cell_editor={"widget":None}
2707: 
2708:         def close_editor(save_value=False):
2709:             w=cell_editor.get("widget")
2710:             if not w:
2711:                 return
2712:             try:
2713:                 if save_value:
2714:                     w.event_generate("<Return>")
2715:                 w.destroy()
2716:             except Exception:
2717:                 pass
2718:             cell_editor["widget"]=None
2719: 
2720:         def edit_cell(event=None):
```
```text
2730:             bbox=tree.bbox(iid,colid)
2731:             if not bbox: return
2732:             close_editor(False)
2733:             x,y,w,h=bbox
2734:             val=str(tree.item(iid,"values")[idx] or "")
2735:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2736:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2737:             cell_editor["widget"]=e
2738:             def commit(_=None):
2739:                 try:
2740:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2741:                 finally:
2742:                     try:e.destroy()
2743:                     except Exception:pass
2744:                     cell_editor["widget"]=None
2745:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2746:             e.bind("<FocusOut>",commit)
2747: 
2748:         def rows_query():
2749:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2750:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2752:             if tc: where.append("code <= ?"); params.append(tc)
2753:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2754:             if df or dt:
2755:                 sub=[]; sp=[]
2756:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2757:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2758:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2759:                 params.extend(sp)
2760:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2761:             return sql,params
2762: 
2763:         def load():
2764:             close_editor(False)
2765:             for i in tree.get_children(): tree.delete(i)
2766:             sql,params=rows_query()
2767:             count=0
2768:             for r in self.conn.execute(sql,params):
2769:                 # V18 stores UOM/opening and the original application may have
2770:                 # rate/remarks columns in some versions. Read them safely.
2771:                 rid,code,desc,uom,opening,rate,remarks=r
2772:                 bal=stock(self.conn,code)
```
```text
2786:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2787:             editing["id"]=None; editing["new"]=True
2788:             # Put the user directly into the Code cell.
2789:             try:
2790:                 bbox=tree.bbox(iid,"#2")
2791:                 if bbox:
2792:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2793:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2794:                     def commit(_=None):
2795:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2796:                         try:e.destroy()
2797:                         except Exception:pass
2798:                         cell_editor["widget"]=None
2799:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2800:             except Exception: pass
2801:             status.set("New row added — enter values, then press Save")
2802: 
2803:         def selected_row():
2804:             a=tree.selection()
2805:             return a[0] if a else None
2806: 
```
```text
2806: 
2807:         def edit_record():
2808:             iid=selected_row()
2809:             if not iid:
2810:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2811:             if not self.can_edit and not self.is_admin:
2812:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2813:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2814:             status.set("Edit mode — double-click any cell to change it, then press Save")
2815:             tree.focus(iid); tree.see(iid)
2816: 
2817:         def save_record():
2818:             iid=selected_row()
2819:             if not iid:
2820:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2821:             if not self.can_edit and not self.is_admin:
2822:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2823:             close_editor(True)
2824:             vals=list(tree.item(iid,"values"))
2825:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2826:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2824:             vals=list(tree.item(iid,"values"))
2825:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2826:             try: opening=float(str(vals[4]).strip() or 0)
2827:             except Exception: raise ValueError("Opening Qty must be a number.")
2828:             try: rate=float(str(vals[5]).strip() or 0)
2829:             except Exception: raise ValueError("Rate must be a number.")
2830:             remarks=str(vals[6]).strip()
2831:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2832:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2833:             if not desc:
2834:                 messagebox.showerror("Save","Description is required."); return
2835:             if opening<0:
2836:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2837:             rid=vals[0]
2838:             try:
2839:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2840:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2841:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2842:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2843:                 if rid:
2844:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2847:                                       (code,desc,uom,opening,rid))
2848:                     if oldcode!=code:
2849:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2850:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2851:                             except Exception:pass
2852:                 else:
2853:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2854:                                       (code,desc,uom,"",opening,0,"Local",0))
2855:                 self.conn.commit()
2856:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2857:                 backup_database(); load()
2858:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2859:             except Exception as ex:
2860:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2861: 
2862:         def delete_record():
2863:             iid=selected_row()
2864:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2865:             if not self.can_delete and not self.is_admin:
2866:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2867:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2863:             iid=selected_row()
2864:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2865:             if not self.can_delete and not self.is_admin:
2866:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2867:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2868:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2869:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2870:             try:
2871:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2872:             except Exception as ex:
2873:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2874: 
2875:         def refresh(): load()
2876:         def do_print():
2877:             try:self.preview_tree("Inventory Codes",tree)
2878:             except Exception as ex:messagebox.showerror("Print",str(ex))
2879:         def do_close(): self.dashboard()
2880: 
2881:         btn("New",new_record,8)
2882:         btn("Edit",edit_record,8)
2883:         btn("Delete",delete_record,8)
```
```text
2876:         def do_print():
2877:             try:self.preview_tree("Inventory Codes",tree)
2878:             except Exception as ex:messagebox.showerror("Print",str(ex))
2879:         def do_close(): self.dashboard()
2880: 
2881:         btn("New",new_record,8)
2882:         btn("Edit",edit_record,8)
2883:         btn("Delete",delete_record,8)
2884:         btn("Save",save_record,8)
2885:         btn("Refresh",refresh,9)
2886:         btn("Preview",do_print,8)
2887:         btn("Print",do_print,8)
2888:         btn("Close",do_close,8)
2889: 
2890:         # Search is deliberately small and sits on the right, without changing
2891:         # the reference layout of the action buttons.
2892:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2893:         search=tk.StringVar()
2894:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2895:         se.pack(side="left",padx=2)
2896:         self._item_master_search_entry=se
```
```text
2904:                     tree.detach(iid)
2905:         search.trace_add("write",filter_grid)
2906:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2907: 
2908:         tree.bind("<Double-1>",edit_cell)
2909:         tree.bind("<F2>",lambda e: edit_record())
2910:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2911:         self._page_actions={
2912:             "save":save_record,"edit":edit_record,"delete":delete_record,
2913:             "cancel":do_close,"print":do_print,"preview":do_print
2914:         }
2915:         load()
2916: 
2917:     def open_mto_inventory_flow(self):
2918:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2919: 
2920:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2921:         Cancel/X only closes the popup.
2922:         """
2923:         criteria = self._ask_mto_inventory_filters()
2924:         if not criteria or criteria.get("cancelled"):
```
```text
3086:                 return False
3087:             destination.set(found_dest)
3088:             edit_mode.update(on=True, original=r[0], dest=found_dest)
3089:             code.set(r[0])
3090:             desc.set(r[1] or "")
3091:             uom.set(r[2] or UOM_OPTIONS[0])
3092:             opening.set(str(r[3] if r[3] is not None else 0))
3093:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
3094:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
3095:             err.set("")
3096:             edit_btn.configure(text="SAVE EDIT")
3097:             ce.focus_set()
3098:             return True
3099: 
3100:         def check_duplicates(*_):
3101:             c = code.get().strip()
3102:             d = desc.get().strip()
3103:             dest = destination.get()
3104:             msgs = []
3105:             r = row_for(dest, c) if len(norm(c)) == 8 else None
3106:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
3108:             dh = desc_hit(dest, d) if d else None
3109:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
3110:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
3111:             hint.set("\n".join(msgs))
3112: 
3113:         code.trace_add("write", check_duplicates)
3114:         desc.trace_add("write", check_duplicates)
3115: 
3116:         def save_code():
3117:             try:
3118:                 c = code.get().strip()
3119:                 d = desc.get().strip()
3120:                 u = uom.get().strip()
3121:                 dest = destination.get()
3122:                 digits = norm(c)
3123:                 if len(digits) != 8:
3124:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3125:                 if not d:
3126:                     raise ValueError("Description is required.")
3127:                 try:
3128:                     op = float(opening.get().strip() or 0)
```
```text
3149:                         (c, d, u, op, iso, old)
3150:                     )
3151:                     action = "updated"
3152:                 else:
3153:                     self.conn.execute(
3154:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3155:                         (c, d, u, "", op, 0, iso)
3156:                     )
3157:                     action = "saved"
3158:                 self.conn.commit()
3159:                 backup_database()
3160:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3161:                 # Keep popup open for fast multiple entries.
3162:                 clear_form(keep_search=False)
3163:                 ce.focus_set()
3164:             except Exception as ex:
3165:                 self.conn.rollback()
3166:                 err.set(str(ex))
3167:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3168: 
3169:         def edit_action():
```
```text
3165:                 self.conn.rollback()
3166:                 err.set(str(ex))
3167:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3168: 
3169:         def edit_action():
3170:             if not edit_mode["on"]:
3171:                 load_for_edit()
3172:             else:
3173:                 save_code()
3174: 
3175:         def delete_code():
3176:             if not edit_mode["on"]:
3177:                 if not load_for_edit():
3178:                     return
3179:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3180:                 return
3181:             try:
3182:                 t = table_for(edit_mode["dest"])
3183:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3184:                 self.conn.commit()
3185:                 backup_database()
```
```text
3181:             try:
3182:                 t = table_for(edit_mode["dest"])
3183:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3184:                 self.conn.commit()
3185:                 backup_database()
3186:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3187:                 clear_form(keep_search=False)
3188:             except Exception as ex:
3189:                 self.conn.rollback()
3190:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3191: 
3192:         btns = ttk.Frame(box)
3193:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3194:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3195:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3196:         edit_btn.pack(side="left", padx=4, ipadx=8)
3197:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3198:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3199:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3200:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3201:         ce.focus_set()
```
```text
3195:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3196:         edit_btn.pack(side="left", padx=4, ipadx=8)
3197:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3198:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3199:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3200:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3201:         ce.focus_set()
3202: 
3203:     def _mto_new_item_dialog(self, on_saved):
3204:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3205:         brand-new item can be created without leaving that screen. Writes
3206:         straight into the same Item Master (items table) used everywhere."""
3207:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3208:         win.transient(self); win.grab_set()
3209:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3210:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3211:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3212:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3213:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3214:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3215:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3211:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3212:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3213:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3214:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3215:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3216:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3217:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3218:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3219:         def save():
3220:             try:
3221:                 c=code.get().strip(); d=desc.get().strip()
3222:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3223:                 if not d: raise ValueError("Description is required.")
3224:                 try:
3225:                     opening_val=float(opening.get() or 0)
3226:                 except ValueError:
3227:                     raise ValueError("Opening Qty must be a number.")
3228:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3229:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3230:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3231:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3224:                 try:
3225:                     opening_val=float(opening.get() or 0)
3226:                 except ValueError:
3227:                     raise ValueError("Opening Qty must be a number.")
3228:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3229:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3230:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3231:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3232:                 self.conn.commit(); backup_database()
3233:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3234:                 win.grab_release(); win.destroy()
3235:                 on_saved()
3236:             except Exception as ex: messagebox.showerror("Error",str(ex))
3237:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3238:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3239:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3240: 
3241:     def _item_filter_bar(self, parent, on_change):
3242:         """Item Code entry + item-master picker + Search/Show All. Calls
3243:         on_change() whenever the code changes or a button is pressed."""
3244:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3330:         self._item_master_find_callback=None
3331:         self._portable_print_context=None
3332:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3333:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3334:         }
3335: 
3336:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3337:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3338:         self.conn.commit()
3339: 
3340:         # ---- Same professional in-app window layout as Inventory Codes ----
3341:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3342:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3343:                   foreground=COLORS["primary_dark"]).pack(side="left")
3344:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3345: 
3346:         def open_find():
3347:             state_find={"index":-1}
3348:             def search_fn(text):
3349:                 text=text.strip().lower()
3350:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3437:             for i in table.get_children(): table.delete(i)
3438:             where=["1=1"]; params=[]
3439:             prefix=state.get("prefix",""); q=search.get().strip()
3440:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3441:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3442:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3443:             if fc: where.append("code >= ?"); params.append(fc)
3444:             if tc: where.append("code <= ?"); params.append(tc)
3445:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3446:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3447:             records=[]
3448:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3449:                 # If a date filter is supplied, accept an opening-date match OR
3450:                 # a transaction in that date range. This prevents valid MTO codes
3451:                 # from disappearing merely because an older record has no opening_date.
3452:                 if df or dt:
3453:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3454:                     if not ok:
3455:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3456:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3457:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3527:                 tr.insert("", "end", values=r)
3528:         def clear():
3529:             for x in v.values(): x.set("")
3530:             try: tr.selection_remove(tr.selection())
3531:             except Exception: pass
3532:             self._set_form_editable(party_form_roots, False)
3533:         def new_form():
3534:             clear(); self._set_form_editable(party_form_roots, True)
3535:         def save():
3536:             try:
3537:                 name=v["name"].get().strip()
3538:                 if not name: raise ValueError("Party Name is required.")
3539:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3540:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3541:             except Exception as ex: messagebox.showerror("Error",str(ex))
3542:         def load_party_row(a):
3543:             if not a:return
3544:             r=tr.item(a[0])["values"]
3545:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3546:             self._set_form_editable(party_form_roots, False)
3547:         def on_party_select(_=None):
```
```text
3553:             load_party_row(a)
3554:             self._set_form_editable(party_form_roots, True)
3555:         def delete_party():
3556:             a=tr.selection()
3557:             if not a:
3558:                 messagebox.showwarning("Delete", "Select a party first."); return
3559:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3560:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3561:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3562:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3563:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3564:         self._add_transaction_new_button(new_form)
3565:         load(); clear()
3566: 
3567:     def user_management(self):
3568:         self.clearbody()
3569:         if not self.is_admin:
3570:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3571:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3572:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3573:         role=tk.StringVar(value="User")
```
```text
3610:             u_ent.state(["!disabled"])
3611:         def edit():
3612:             a=tr.selection()
3613:             if not a:
3614:                 messagebox.showwarning("Edit User","Select a user row first."); return
3615:             r=tr.item(a[0])["values"]
3616:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3617:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3618:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3619:         def save():
3620:             try:
3621:                 username=v["username"].get().strip()
3622:                 if not username: raise ValueError("Username is required.")
3623:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3624:                 pw=v["password"].get()
3625:                 if exists:
3626:                     pw_hash = hash_password(pw) if pw else exists[0]
3627:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3628:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3629:                 else:
3630:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3625:                 if exists:
3626:                     pw_hash = hash_password(pw) if pw else exists[0]
3627:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3628:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3629:                 else:
3630:                     if not pw: raise ValueError("Password is required for a new user.")
3631:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3632:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3633:                 self.conn.commit(); backup_database(); load(); clear()
3634:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3635:             except Exception as ex:
3636:                 messagebox.showerror("Error", str(ex))
3637:         def delete_user():
3638:             a=tr.selection()
3639:             if not a:
3640:                 messagebox.showwarning("Delete User","Select a user row first."); return
3641:             username=tr.item(a[0])["values"][0]
3642:             if username==self.current_user:
3643:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3644:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3645:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3640:                 messagebox.showwarning("Delete User","Select a user row first."); return
3641:             username=tr.item(a[0])["values"][0]
3642:             if username==self.current_user:
3643:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3644:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3645:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3646:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3647:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3648:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3649:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3650:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3651:         load()
3652: 
3653:     @staticmethod
3654:     def _renumber_tree(tree, rows):
3655:         for i,iid in enumerate(tree.get_children()):
3656:             vals=list(tree.item(iid,"values"));
3657:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3658: 
3659:     def demand(self):
3660:         self.clearbody(); self.demand_lines=[]
```
```text
3657:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3658: 
3659:     def demand(self):
3660:         self.clearbody(); self.demand_lines=[]
3661:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3662:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3663:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3664:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3665:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3666:         # Demand Date is intentionally displayed as its own dedicated field.
3667:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3668:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3669:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3670:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3671:                 ("special","Special Instructions"),("source","Recommended Source")]
3672:         for i,(k,n) in enumerate(fields):
3673:             r=i//4*2+3; c=i%4*2
3674:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3675:             if k=="dept":
3676:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3677:             elif k=="urgency":
```
```text
3747:         def new_form():
3748:             self._editing_document_key=None
3749:             for z in v.values(): z.set("")
3750:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3751:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3752:             for iid in tree.get_children(): tree.delete(iid)
3753:             self._set_form_editable(form_roots, True, skip=[selector])
3754: 
3755:         def save():
3756:             try:
3757:                 no=v["no"].get().strip()
3758:                 if not no: raise ValueError("Demand No is required.")
3759:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3760:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3761:                 if dup and getattr(self,"_editing_document_key",None) != no:
3762:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3763:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3764:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3765:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3766:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3767:                 self.conn.commit()
```
```text
3760:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3761:                 if dup and getattr(self,"_editing_document_key",None) != no:
3762:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3763:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3764:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3765:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3766:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3767:                 self.conn.commit()
3768:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3769:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3770:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3771:             except Exception as ex: messagebox.showerror("Error",str(ex))
3772:         form_roots=[f,line,editbar]
3773:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3774:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3775:         def delete_current():
3776:             no=v["no"].get().strip()
3777:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3778:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3779:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3780:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3793:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3794:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3795:                     f"Justification: {v['just'].get()}",
3796:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3797:             if not self.demand_lines:
3798:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3799:             self.show_preview_window("Purchase Demand", header,
3800:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3801:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3802:         def edit_saved_demand():
3803:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3804:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3805:             self._set_form_editable(form_roots, True, skip=[selector])
3806:         def print_now():
3807:             if not self.demand_lines:
3808:                 messagebox.showwarning("Print","Add at least one item line first."); return
3809:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3810:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3811:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3812:                     f"Justification: {v['just'].get()}",
3813:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3809:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3810:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3811:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3812:                     f"Justification: {v['just'].get()}",
3813:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3814:             self._open_direct_printer("Purchase Demand",header,
3815:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3816:                 self.demand_lines,A4)
3817:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3818:         self._add_transaction_new_button(new_form)
3819:         self._set_form_editable(form_roots, False, skip=[selector])
3820:         try:
3821:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3822:         except Exception: pass
3823:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3824: 
3825:     def load_demand_into_form(self,no,v,tree):
3826:         v["no"].set(no)
3827:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3828:         if not r:return
3829:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3831:         self.demand_lines=[]
3832:         for i in tree.get_children():tree.delete(i)
3833:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3834:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3835:         roots=getattr(self,"_transaction_form_roots",None)
3836:         if roots and "demand" in roots:
3837:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3838: 
3839:     def refresh_saved_cache(self,typ):
3840:         # Refresh saved-document dropdowns immediately after a successful save.
3841:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3842:         alive=[]
3843:         for combo, refresh in refreshers:
3844:             try:
3845:                 if combo.winfo_exists():
3846:                     refresh()
3847:                     alive.append((combo, refresh))
3848:             except Exception:
3849:                 pass
3850:         if hasattr(self, "_document_selector_refreshers"):
3851:             self._document_selector_refreshers[typ] = alive
```
```text
3850:         if hasattr(self, "_document_selector_refreshers"):
3851:             self._document_selector_refreshers[typ] = alive
3852: 
3853:     def grr(self):
3854:         self.clearbody(); self.grr_lines=[]
3855:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3856:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3857:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3858:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3859:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3860:         for i,(k,n) in enumerate(fields):
3861:             r=i//4*2+2;c=i%4*2
3862:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3863:             if k=="department":
3864:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3865:             elif k=="supplier":
3866:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3867:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3868:             elif k=="date":
3869:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3870:             else:
```
```text
3919:         def new_form():
3920:             self._editing_document_key=None
3921:             for z in v.values(): z.set("")
3922:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3923:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3924:             for iid in tree.get_children(): tree.delete(iid)
3925:             self._set_form_editable(form_roots, True, skip=[selector])
3926: 
3927:         def save():
3928:             try:
3929:                 no=v["no"].get().strip()
3930:                 if not no:raise ValueError("GRN No is required.")
3931:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3932:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3933:                 if dup and getattr(self,"_editing_document_key",None) != no:
3934:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3935:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3936:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3937:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3938:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3939:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3936:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3937:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3938:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3939:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3940:                 for x in self.grr_lines:
3941:                     ltype=x[10] if len(x)>10 else "Local"
3942:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3943:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3944:                 self.conn.commit()
3945:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
3946:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
3947:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3948:             except Exception as ex:messagebox.showerror("Error",str(ex))
3949:         form_roots=[f,line,editbar]
3950:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3951:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3952:         def delete_current():
3953:             no=v["no"].get().strip()
3954:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3955:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3956:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
3949:         form_roots=[f,line,editbar]
3950:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3951:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3952:         def delete_current():
3953:             no=v["no"].get().strip()
3954:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3955:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3956:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3957:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3958:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3959:         def cancel_form():
3960:             self._editing_document_key=None
3961:             self._set_form_editable(form_roots, False, skip=[selector])
3962:             for z in v.values(): z.set("")
3963:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3964:             itype.set("Local")
3965:             self.grr_lines.clear()
3966:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3967:             for iid in tree.get_children(): tree.delete(iid)
3968:         def preview_now():
3969:             if not self.grr_lines:
```
```text
3978:                     ("Challan #", v['challan'].get()),
3979:                     ("Vehicle #", v['vehicle'].get()),
3980:                     ("Bill/Voucher #", v['bill'].get()),
3981:                     ("Reference", v['ref'].get()),
3982:                     ("Remarks", v['remarks'].get()),
3983:                     ("Total Value", fmt_num(total))]
3984:             self.show_preview_window("GRN Receipt", header,
3985:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3986:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3987:         def portable_current():
3988:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3989:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3990:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3991:         self._portable_print_context=portable_current
3992:         def edit_saved_grr():
3993:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3994:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
3995:             self._set_form_editable(form_roots, True, skip=[selector])
3996:         def print_now():
3997:             if not self.grr_lines:
3998:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
4002:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
4003:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
4004:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
4005:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
4006:                     ("Total Value", fmt_num(total))]
4007:             self._open_direct_printer("GRN Receipt",header,
4008:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
4009:                 self.grr_lines,landscape(A4))
4010:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
4011:         self._add_transaction_new_button(new_form)
4012:         self._set_form_editable(form_roots, False, skip=[selector])
4013:         try:
4014:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
4015:         except Exception: pass
4016:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
4017: 
4018:     def load_grr_into_form(self,no,v,tree):
4019:         v["no"].set(no)
4020:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
4021:         if not r:return
4022:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
4029:         if roots and "grr" in roots:
4030:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
4031: 
4032:     def issue(self):
4033:         self.clearbody(); self.issue_lines=[]
4034:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
4035:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
4036:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
4037:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
4038:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
4039:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
4040:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
4041:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
4042:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
4043:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
4044:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
4045:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
4046:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
4047:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
4048:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
4049:         itype=tk.StringVar(value="Local")
```
```text
4118:                 # Editing an existing issue replaces its old stock transaction and detail lines.
4119:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
4120:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
4121:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
4122:                 for x in self.issue_lines:
4123:                     ltype=x[7] if len(x)>7 else "Local"
4124:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
4125:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
4126:                 self.conn.commit()
4127:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
4128:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
4129:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4130:             except Exception as ex:messagebox.showerror("Error",str(ex))
4131:         def delete_current():
4132:             no=v["no"].get().strip()
4133:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
4134:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
4135:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
4136:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
4137:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
4138:         def cancel_form():
```
```text
4146:             for iid in tree.get_children(): tree.delete(iid)
4147:         def preview_now():
4148:             if not self.issue_lines:
4149:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4150:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4151:                     f"Items Use For: {v['items_use_for'].get()}"]
4152:             self.show_preview_window("Material Issue", header,
4153:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4154:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4155:         def portable_current():
4156:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4157:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4158:         self._portable_print_context=portable_current
4159:         form_roots=[f,usebar,line,editbar]
4160:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4161:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4162:         def load_saved_issue(no):
4163:             self.load_issue_into_form(no,v,tree)
4164:             self._set_form_editable(form_roots, False, skip=[selector])
4165:         def edit_saved_issue():
4166:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4159:         form_roots=[f,usebar,line,editbar]
4160:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4161:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4162:         def load_saved_issue(no):
4163:             self.load_issue_into_form(no,v,tree)
4164:             self._set_form_editable(form_roots, False, skip=[selector])
4165:         def edit_saved_issue():
4166:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4167:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4168:             self._set_form_editable(form_roots, True, skip=[selector])
4169:         def print_issue_now():
4170:             if not self.issue_lines:
4171:                 messagebox.showwarning("Print","Add at least one item line first."); return
4172:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4173:             self._open_direct_printer("Material Issue",header,
4174:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4175:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4176:         self._add_transaction_new_button(new_form)
4177:         self._set_form_editable(form_roots, False, skip=[selector])
4178:         self._active_form_loader = load_saved_issue
4179: 
```
```text
4187:         for i in tree.get_children():tree.delete(i)
4188:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4189:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4190:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4191:         roots=getattr(self,"_transaction_form_roots",None)
4192:         if roots and "issue" in roots:
4193:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4194: 
4195:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4196:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4197: 
4198:         The layout intentionally matches Inventory Codes' Selection Criteria
4199:         popup so all Report sub-sections have one consistent desktop workflow.
4200:         """
4201:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4202:         win=tk.Toplevel(self)
4203:         win.title(f"{report_title} - Selection Criteria")
4204:         win.resizable(False,False)
4205:         win.transient(self); win.grab_set()
4206:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4207:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4252:             except Exception: pass
4253:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4254:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4255:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4256:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4257:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4258:         e1.focus_set(); self.wait_window(win); return result
4259: 
4260:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4261:         self._pending_report_filters=criteria
4262:         try:
4263:             return self.open_menu_window(method,title,geometry)
4264:         finally:
4265:             self._pending_report_filters=None
4266: 
4267:     def open_stock_balance_report_flow(self):
4268:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4269:         if f.get("cancelled"): return None
4270:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4271: 
4272:     def open_grr_report_flow(self):
```
```text
4265:             self._pending_report_filters=None
4266: 
4267:     def open_stock_balance_report_flow(self):
4268:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4269:         if f.get("cancelled"): return None
4270:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4271: 
4272:     def open_grr_report_flow(self):
4273:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4274:         if f.get("cancelled"): return None
4275:         return self._open_report_child(self.report_grr,"GRN Report",f)
4276: 
4277:     def open_demand_report_flow(self):
4278:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4279:         if f.get("cancelled"): return None
4280:         return self._open_report_child(self.report_demand,"Demand Report",f)
4281: 
4282:     def open_issue_report_flow(self):
4283:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4284:         if f.get("cancelled"): return None
4285:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4279:         if f.get("cancelled"): return None
4280:         return self._open_report_child(self.report_demand,"Demand Report",f)
4281: 
4282:     def open_issue_report_flow(self):
4283:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4284:         if f.get("cancelled"): return None
4285:         return self._open_report_child(self.report_issue,"Issue Report",f)
4286: 
4287:     def open_party_report_flow(self):
4288:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4289:         if f.get("cancelled"): return None
4290:         return self._open_report_child(self.report_party,"Party Report",f)
4291: 
4292:     def _ask_stock_balance_filters(self):
4293:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4294:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4295:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4296:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4297:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4298:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4299:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4311:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4312:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4313:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4314:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4315:         e1.focus_set();self.wait_window(win);return result
4316: 
4317:     def stock_balance(self):
4318:         self.clearbody()
4319:         # Stock Balance is a Report sub-section and does not use the generic
4320:         # Save/Edit/Delete/Cancel/Print action strip.
4321:         children=self.body.winfo_children()
4322:         if children:
4323:             children[0].destroy()
4324:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4325:         if initial.get("cancelled"):
4326:             self.dashboard(); return
4327:         top=ttk.Frame(self.body);top.pack(fill="x")
4328:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4329:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4330:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4331:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4341:             for typ,qty in self.conn.execute(q,params):
4342:                 if typ=="GRR":gr+=float(qty or 0)
4343:                 elif typ=="ISSUE":iss+=float(qty or 0)
4344:             return opening_before,gr,iss,opening_before+gr-iss
4345:         def header_summary():
4346:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4347:         def load():
4348:             for i in tr.get_children():tr.delete(i)
4349:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4350:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4351:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4352:             sql+=" ORDER BY code"
4353:             for r in self.conn.execute(sql,params):
4354:                 op,gr,iss,cur=period(r[0],r[3])
4355:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4356:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4357:         def reopen_filters():
4358:             initial2=self._ask_stock_balance_filters()
4359:             if initial2.get("cancelled"):return
4360:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4361:             load()
```
```text
4399:         """
4400:         if typ=="demand": self.demand()
4401:         elif typ=="grr": self.grr()
4402:         else: self.issue()
4403:         loader=getattr(self,"_active_form_loader",None)
4404:         if loader: loader(str(no))
4405: 
4406:     def _edit_from_selector(self, typ, var, loader):
4407:         """Top Edit action: load the saved document directly into the current form.
4408:         If nothing is selected, use the newest saved document; never open a popup.
4409:         """
4410:         text=var.get().strip()
4411:         if text:
4412:             no=text.split(" -> ",1)[0].strip()
4413:         else:
4414:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4415:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4416:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4417:             if not r:
4418:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4419:                 return
```
```text
4416:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4417:             if not r:
4418:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4419:                 return
4420:             no=str(r[0])
4421:             var.set(no)
4422:         loader(no)
4423: 
4424:     def show_saved_records(self,typ):
4425:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4426:         if typ=="demand":
4427:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4428:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4429:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4430:             for r in rows:
4431:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4432:                 r=list(r); r[1]=to_display_date(r[1])
4433:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4434:         elif typ=="grr":
4435:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4436:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4447:         def view():
4448:             a=tr.selection()
4449:             if not a:return
4450:             no=tr.item(a[0])["values"][0]
4451:             win.destroy();self.open_document_editor(typ,no)
4452:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4453:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4454:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4455:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4456: 
4457:     def documents(self):
4458:         self.clearbody()
4459:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4460:         specs=[
4461:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4462:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4463:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4464:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4465:             ("Material Issues","issue",("No","Date","Department"),
4466:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4467:         ]
```
```text
4463:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4464:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4465:             ("Material Issues","issue",("No","Date","Department"),
4466:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4467:         ]
4468:         for title,typ,cols,query in specs:
4469:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4470:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4471:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4472:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4473:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4474:             for r in self.conn.execute(query):
4475:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4476:             def edit_selected(t=tr,k=typ):
4477:                 a=t.selection()
4478:                 if not a:
4479:                     messagebox.showwarning("Edit", "Select a saved record first.")
4480:                     return
4481:                 no=t.item(a[0])["values"][0]
4482:                 self.open_document_editor(k,no)
4483:             def delete_selected(t=tr,k=typ):
```
```text
4478:                 if not a:
4479:                     messagebox.showwarning("Edit", "Select a saved record first.")
4480:                     return
4481:                 no=t.item(a[0])["values"][0]
4482:                 self.open_document_editor(k,no)
4483:             def delete_selected(t=tr,k=typ):
4484:                 a=t.selection()
4485:                 if not a:
4486:                     messagebox.showwarning("Delete", "Select a saved record first.")
4487:                     return
4488:                 no=t.item(a[0])["values"][0]
4489:                 if k=="demand":
4490:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4491:                 elif k=="grr":
4492:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4493:                 else:
4494:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4495:                 self.conn.commit();backup_database();self.documents()
4496:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4497:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4498:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4492:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4493:                 else:
4494:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4495:                 self.conn.commit();backup_database();self.documents()
4496:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4497:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4498:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4499:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4500:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4501:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4502:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4503: 
4504:     def doc_export_selected(self,typ,tr,fmt):
4505:         a=tr.selection()
4506:         if not a:
4507:             messagebox.showwarning("Export","Select a saved record first."); return
4508:         no=tr.item(a[0])["values"][0]
4509:         if fmt=="word": self.export_word(typ,no)
4510:         else: self.export_excel(typ,no)
4511: 
4512:     def doc_preview_selected(self,typ,tr):
```
```text
4507:             messagebox.showwarning("Export","Select a saved record first."); return
4508:         no=tr.item(a[0])["values"][0]
4509:         if fmt=="word": self.export_word(typ,no)
4510:         else: self.export_excel(typ,no)
4511: 
4512:     def doc_preview_selected(self,typ,tr):
4513:         a=tr.selection()
4514:         if not a:
4515:             messagebox.showwarning("Preview","Select a saved record first."); return
4516:         no=tr.item(a[0])["values"][0]
4517:         data=self._get_doc_data(typ,no)
4518:         if not data:
4519:             messagebox.showwarning("Preview","Document not found."); return
4520:         title,header,cols,rows=data
4521:         header_lines=header
4522:         self.show_preview_window(title,header_lines,cols,rows)
4523: 
4524:     def doc_print_selected(self,typ,tr):
4525:         a=tr.selection()
4526:         if not a: return
4527:         no=tr.item(a[0])["values"][0]
```
```text
4558:         def _print_loaded_document():
4559:             data=self._get_doc_data(typ,no)
4560:             if not data:
4561:                 messagebox.showwarning("Document","Document not found."); return
4562:             title,header,cols,rows=data
4563:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4564:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4565: 
4566:     def _report_filter_popup(self, title, include_party=False):
4567:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4568:         win,winbody=self._internal_window(title,"520x420")
4569:         done=tk.BooleanVar(value=False)
4570:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4571:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4572:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4573:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4574:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4575:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4576:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4577:         if include_party:
4578:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4572:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4573:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4574:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4575:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4576:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4577:         if include_party:
4578:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4579:         def ok():
4580:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4581:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4582:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4583:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4584: 
4585:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4586:         self.clearbody()
4587:         # Report sub-sections use their own report toolbar; remove only the
4588:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4589:         children=self.body.winfo_children()
4590:         if children:
4591:             children[0].destroy()
4592:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4593:         if f.get("cancelled"):
4594:             self.dashboard();return
4595:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4596:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4597:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4598:         def load():
4599:             for i in tr.get_children():tr.delete(i)
4600:             params,where=params_builder(f)
4601:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4602:             for r in self.conn.execute(sql,params):
4603:                 vals=list(r)
4604:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4605:                 tr.insert("","end",values=vals)
4606:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4607:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4608:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4609:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4610:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4611:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4612:         def open_find_report():
4613:             state_find={"index":-1}
```
```text
4619:                 order=children[start:]+children[:start]
4620:                 for iid in order:
4621:                     vals=tr.item(iid,"values")
4622:                     if any(text in str(v).lower() for v in vals):
4623:                         state_find["index"]=children.index(iid)
4624:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4625:                 return False
4626:             self._open_exact_find_text_popup(search_fn)
4627:         self._item_master_find_callback=open_find_report
4628:         load()
4629:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4630: 
4631:     def report_grr(self):
4632:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4633:         def pb(f):
4634:             w=[];p=[]
4635:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4636:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4637:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4638:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4639:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4634:             w=[];p=[]
4635:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4636:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4637:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4638:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4639:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4640:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4641:             return p,w
4642:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4643: 
4644:     def report_demand(self):
4645:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4646:         def pb(f):
4647:             w=[];p=[]
4648:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4649:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4650:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4651:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4652:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4653:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4654:             return p,w
```
```text
4647:             w=[];p=[]
4648:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4649:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4650:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4651:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4652:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4653:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4654:             return p,w
4655:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4656: 
4657:     def report_issue(self):
4658:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4659:         def pb(f):
4660:             w=[];p=[]
4661:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4662:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4663:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4664:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4665:             return p,w
4666:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4667: 
```
```text
4660:             w=[];p=[]
4661:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4662:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4663:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4664:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4665:             return p,w
4666:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4667: 
4668:     def report_party(self):
4669:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4670:         def pb(f):
4671:             w=[];p=[]
4672:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4673:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4674:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4675:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4676:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4677:             return p,w
4678:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4679: 
4680:     def reports(self):
```
```text
4678:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4679: 
4680:     def reports(self):
4681:         self.clearbody()
4682:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4683: 
4684:         # ================= GRN Details =================
4685:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4686:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4687:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4688:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4689:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4690:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4691: 
4692:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4693:         def load_grr_item(codev=None):
4694:             for i in tr.get_children(): tr.delete(i)
4695:             q=codev.get().strip() if codev else ""
4696:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4697:             for r in self.conn.execute(sql,(q,) if q else ()):
4698:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4704:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4705:         tr=self.make_tree(fr,grr_cols,grr_widths)
4706:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4707:             for i in tr.get_children(): tr.delete(i)
4708:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4709:             conds=[];params=[]
4710:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4711:             if td: conds.append("g.grr_date<=?");params.append(td)
4712:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4713:             for r in self.conn.execute(sql,params):
4714:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4715:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4716:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4717:         load_grr_date(fdv,tdv)
4718: 
4719:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4720:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4721:         party=tk.StringVar(value="ALL")
4722:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4723:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4724:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4720:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4721:         party=tk.StringVar(value="ALL")
4722:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4723:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4724:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4725:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4726:         def load_party(*_):
4727:             for i in tr.get_children(): tr.delete(i)
4728:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4729:             if party.get()=="ALL":
4730:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4731:             else:
4732:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4733:             for r in rows:
4734:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4735:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4736:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4737: 
4738:         # ================= Demand Details =================
4739:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4740:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4736:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4737: 
4738:         # ================= Demand Details =================
4739:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4740:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4741:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4742:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4743:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4744:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4745: 
4746:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4747:         def load_dem_item(codev=None):
4748:             for i in tr.get_children(): tr.delete(i)
4749:             q=codev.get().strip() if codev else ""
4750:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4751:             for r in self.conn.execute(sql,(q,) if q else ()):
4752:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4753:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4754:         tr=self.make_tree(fr,dem_cols,dem_widths)
4755:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4756:         load_dem_item(codev)
```
```text
4758:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4759:         tr=self.make_tree(fr,dem_cols,dem_widths)
4760:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4761:             for i in tr.get_children(): tr.delete(i)
4762:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4763:             conds=[];params=[]
4764:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4765:             if td: conds.append("d.demand_date<=?");params.append(td)
4766:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4767:             for r in self.conn.execute(sql,params):
4768:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4769:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4770:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4771:         load_dem_date(fdv,tdv)
4772: 
4773:         # ================= Material Issue Details =================
4774:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4775:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4776:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4777:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4778:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4771:         load_dem_date(fdv,tdv)
4772: 
4773:         # ================= Material Issue Details =================
4774:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4775:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4776:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4777:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4778:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4779:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4780: 
4781:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4782:         def load_iss_item(codev=None):
4783:             for i in tr.get_children(): tr.delete(i)
4784:             q=codev.get().strip() if codev else ""
4785:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4786:             for r in self.conn.execute(sql,(q,) if q else ()):
4787:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4788:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4789:         tr=self.make_tree(fr,iss_cols,iss_widths)
4790:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4791:         load_iss_item(codev)
```
```text
4793:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4794:         tr=self.make_tree(fr,iss_cols,iss_widths)
4795:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4796:             for i in tr.get_children(): tr.delete(i)
4797:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4798:             conds=[];params=[]
4799:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4800:             if td: conds.append("i.issue_date<=?");params.append(td)
4801:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4802:             for r in self.conn.execute(sql,params):
4803:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4804:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4805:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4806:         load_iss_date(fdv,tdv)
4807: 
4808:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4809: 
4810:     def print_item_master(self):
4811:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4812:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4813: 
```
```text
4810:     def print_item_master(self):
4811:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4812:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4813: 
4814:     def print_party_master(self):
4815:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4816:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4817: 
4818:     def print_report(self,kind):
4819:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4820:         if kind=="grr":
4821:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4822:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4823:         elif kind=="demand":
4824:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4825:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4826:         elif kind=="issue":
4827:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4828:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4829:         else:
4830:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4831:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4832:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4833: 
4834:     def print_stock(self):
4835:         rows=[]
4836:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4837:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4838:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4839:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4840: 
4841:     def print_ledger(self):
4842:         rows=[]
4843:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4844:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4845:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4846:                 running += x[3] if x[1]=="GRR" else -x[3]
4847:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4848:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4849: 
4850:     def _get_doc_data(self, typ, no):
4851:         """Header + line items for one saved document, used by the on-screen
```
```text
4917:             sig=doc.add_table(rows=2,cols=3)
4918:             labels=["Prepared By","Store Keeper","Store Incharge"]
4919:             for i,label in enumerate(labels):
4920:                 sig.cell(0,i).text="____________________"
4921:                 sig.cell(1,i).text=label
4922:                 for para in sig.cell(1,i).paragraphs:
4923:                     for run in para.runs: run.bold=True
4924:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4925:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4926:         doc.save(path)
4927:         self.open_file(path)
4928: 
4929:     def export_excel(self, typ, no):
4930:         if not no or not no.strip():
4931:             return messagebox.showwarning("Excel Export","Select a document first.")
4932:         if not XLSX_AVAILABLE:
4933:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4934:         data=self._get_doc_data(typ,no)
4935:         if not data:
4936:             return messagebox.showwarning("Excel Export","Document not found.")
4937:         title,header,cols,rows=data
```
```text
4959:             for col in range(1,4):
4960:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4961:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4962:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4963:         for col_cells in ws.columns:
4964:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4965:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4966:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4967:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4968:         wb.save(path)
4969:         self.open_file(path)
4970: 
4971:     def preview_pdf(self,typ,no):
4972:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4973:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4974:         data=self._get_doc_data(typ,no)
4975:         if not data:return messagebox.showwarning("Document","Document not found.")
4976:         title,header,cols,rows=data
4977:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4978:         page_size = landscape(A4) if typ == "grr" else A4
4979:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4974:         data=self._get_doc_data(typ,no)
4975:         if not data:return messagebox.showwarning("Document","Document not found.")
4976:         title,header,cols,rows=data
4977:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4978:         page_size = landscape(A4) if typ == "grr" else A4
4979:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4980: 
4981:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4982:         """Open the print dialog with a real visual preview of the exact report.
4983: 
4984:         The report is rendered to a temporary PDF only in memory/on disk for the
4985:         duration of printing.  It is deleted after the print dialog closes, so
4986:         the Print button does not leave a PDF report behind.  Printing uses the
4987:         rendered report page itself rather than rebuilding rows as plain text;
4988:         this keeps the printed page identical to the application's report.
4989:         """
4990:         # Printing is always prepared as an A4 landscape page. This only affects
4991:         # the print path; the rest of the application's UI/report logic is unchanged.
4992:         page_size = landscape(A4)
4993:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
4994:             messagebox.showwarning(
```
```text
4996:                 "The print preview/printing components are not available.\n\n"
4997:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
4998:             )
4999:             return
5000:         if not rows and not columns:
5001:             messagebox.showwarning("Print", "There is no data to print.")
5002:             return
5003:         try:
5004:             os.makedirs(REPORTS_DIR, exist_ok=True)
5005:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
5006:             self._pdf_table_report(key,title,columns,rows,page_size,
5007:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
5008:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
5009:             self._select_windows_printer_for_pdf(key)
5010:         except Exception as e:
5011:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
5012: 
5013:     def _select_windows_printer_for_pdf(self, path):
5014:         """Print dialog with an actual page preview, printer selection and direct GDI output.
5015: 
5016:         The preview is rendered from the exact PDF produced by the application,
```
```text
5046:         job=getattr(self, "_print_jobs", {}).get(path)
5047:         if job:
5048:             title, header_lines, columns, rows, source_page_size = job
5049:         else:
5050:             title=os.path.splitext(os.path.basename(path))[0]
5051:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
5052: 
5053:         try:
5054:             doc=fitz.open(path)
5055:             total_pages=max(1,doc.page_count)
5056:         except Exception as e:
5057:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
5058:             return
5059: 
5060:         win=tk.Toplevel(self)
5061:         win.title("Printing from Win32 application - Print")
5062:         win.geometry("900x620")
5063:         win.minsize(850,580)
5064:         win.transient(self)
5065:         win.configure(bg="#f0f0f0")
5066: 
```
```text
5072:             pass
5073: 
5074:         outer=tk.Frame(win,bg="#f0f0f0")
5075:         outer.pack(fill="both",expand=True)
5076:         outer.columnconfigure(1,weight=1)
5077:         outer.rowconfigure(0,weight=1)
5078: 
5079:         # Left side mirrors the familiar system printer dialog: printers and
5080:         # print options. Right side contains the actual report page preview.
5081:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
5082:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
5083:         left.grid_propagate(False)
5084:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
5085:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
5086:         printer_list.pack(fill="x")
5087:         for pr in printers: printer_list.insert("end",pr)
5088:         try: printer_list.selection_set(printers.index(default_printer))
5089:         except Exception: printer_list.selection_set(0)
5090: 
5091:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
5092:         copies=tk.IntVar(value=1)
```
```text
5165:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5166: 
5167:         bottom=tk.Frame(win,bg="#f0f0f0")
5168:         # `outer` already uses pack() in `win`; using grid() for another direct
5169:         # child of the same toplevel raises TclError. Keep the action bar in the
5170:         # same geometry-manager family so Print/Cancel are always visible.
5171:         bottom.pack(fill="x",padx=12,pady=(0,12))
5172:         bottom.columnconfigure(0,weight=1)
5173:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5174:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5175:         print_btn=ttk.Button(bottom,text="Print",width=12)
5176:         print_btn.grid(row=0,column=2,padx=(8,0))
5177: 
5178:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5179: 
5180:         def parse_page_selection(total):
5181:             if pages_mode.get()=="All pages": return list(range(total))
5182:             raw=page_range.get().strip()
5183:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5184:             selected=[]
5185:             for part in raw.split(","):
```
```text
5182:             raw=page_range.get().strip()
5183:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5184:             selected=[]
5185:             for part in raw.split(","):
5186:                 part=part.strip()
5187:                 if "-" in part:
5188:                     a,b=part.split("-",1); a=int(a); b=int(b)
5189:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5190:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5191:                     selected.extend(range(a-1,b))
5192:                 else:
5193:                     n=int(part)
5194:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5195:                     selected.append(n-1)
5196:             return list(dict.fromkeys(selected))
5197: 
5198:         def selected_printer():
5199:             sel=printer_list.curselection()
5200:             return printer_list.get(sel[0]) if sel else printers[0]
5201: 
5202:         def print_rendered_pages():
```
```text
5295:                 finally:
5296:                     if hprinter is not None:
5297:                         try: win32print.ClosePrinter(hprinter)
5298:                         except Exception: pass
5299:                     if hdc:
5300:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5301:                         except Exception: pass
5302: 
5303:                 # Print the exact rendered PDF page through the printer DC.
5304:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5305:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5306:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5307:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5308: 
5309:                 for copy_no in range(count):
5310:                     dc.StartDoc(str(title)[:80])
5311:                     doc_ok=False
5312:                     try:
5313:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5314:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5315:                             dc.StartPage()
```
```text
5314:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5315:                             dc.StartPage()
5316:                             page_ok=False
5317:                             try:
5318:                                 cell_w=printable_w/float(cols_n)
5319:                                 cell_h=printable_h/float(rows_n)
5320:                                 for j,page_index in enumerate(batch):
5321:                                     page=doc.load_page(page_index)
5322:                                     pdf_w=max(1.0,float(page.rect.width))
5323:                                     pdf_h=max(1.0,float(page.rect.height))
5324:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5325:                                     fit=max(0.25,min(fit,8.0))
5326:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5327:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5328:                                     target_w=max(1,int(cell_w*0.96))
5329:                                     target_h=max(1,int(cell_h*0.96))
5330:                                     ratio=min(target_w/img.width,target_h/img.height)
5331:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5332:                                     if (nw,nh)!=(img.width,img.height):
5333:                                         img=img.resize((nw,nh),Image.LANCZOS)
5334:                                     dib=ImageWin.Dib(img)
```
```text
5354: 
5355:                 status.set("Print job sent successfully")
5356:                 win.update_idletasks()
5357:                 win.after(500,close)
5358:             except Exception as e:
5359:                 status.set("Print failed: "+str(e))
5360:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5361: 
5362:         def close():
5363:             try: doc.close()
5364:             except Exception: pass
5365:             try: win.destroy()
5366:             except Exception: pass
5367:             # Only the temporary PDF created by the Print button is removed.
5368:             # Existing report PDFs passed through the legacy print path are preserved.
5369:             try:
5370:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5371:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5372:             except Exception: pass
5373: 
5374:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5370:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5371:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5372:             except Exception: pass
5373: 
5374:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5375:         bottom.winfo_children()[1].configure(command=close)
5376:         print_btn.configure(command=print_rendered_pages)
5377:         win.protocol("WM_DELETE_WINDOW",close)
5378:         win.bind("<Escape>",lambda e:close())
5379:         win.grab_set()
5380:         # Keep the requested printer defaults visibly selected; no manual
5381:         # adjustment is required before pressing Print.
5382:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5383:         win.after(120,lambda:render_preview(0))
5384:         win.focus_force()
5385: 
5386:     def print_pdf(self,path):
5387:         """Open a printer-selection window for a generated PDF."""
5388:         path=os.path.abspath(path)
5389:         if not os.path.exists(path):
5390:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5386:     def print_pdf(self,path):
5387:         """Open a printer-selection window for a generated PDF."""
5388:         path=os.path.abspath(path)
5389:         if not os.path.exists(path):
5390:             messagebox.showwarning("Print", "The report file could not be found.")
5391:             return
5392: 
5393:         if sys.platform.startswith("win"):
5394:             self._select_windows_printer_for_pdf(path)
5395:             return
5396: 
5397:         try:
5398:             subprocess.run(["lp", path], check=True)
5399:         except Exception as e:
5400:             messagebox.showwarning(
5401:                 "Print",
5402:                 "The operating system could not start printing.\n\n"
5403:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5404:             )
5405: 
5406:     def open_file(self,path):
```
```text
5401:                 "Print",
5402:                 "The operating system could not start printing.\n\n"
5403:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5404:             )
5405: 
5406:     def open_file(self,path):
5407:         try:
5408:             if sys.platform.startswith("win"): os.startfile(path)
5409:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5410:             else: subprocess.Popen(["xdg-open",path])
5411:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5412: 
5413:     def print_demand(self,no):
5414:         data=self._get_doc_data("demand",no)
5415:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5416:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5417:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5418:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5419: 
5420:     def print_grr(self,no):
5421:         data=self._get_doc_data("grr",no)
```
```text
5415:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5416:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5417:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5418:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5419: 
5420:     def print_grr(self,no):
5421:         data=self._get_doc_data("grr",no)
5422:         if not data:return messagebox.showwarning("Document","GRN not found.")
5423:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5424:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5425:         # GRN has a wide item table. Generate the PDF itself in landscape so
5426:         # the printer dialog and printer driver receive a landscape document
5427:         # instead of a portrait page with rotated/cropped content.
5428:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5429: 
5430:     def print_issue(self,no):
5431:         data=self._get_doc_data("issue",no)
5432:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5433:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5434:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5435:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
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
