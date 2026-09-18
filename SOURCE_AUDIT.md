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

- Lines: 5361
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-360), restore_database(361-378), stock(380-385), fmt_num(387-389), to_iso_date(391-400), to_display_date(402-410), fiscal_year_key(412-423), fiscal_year_range(425-428), normalize_code(430-438), format_code(440-449), attach_code_mask(451-477), set_digits(454-459), key(460-470), paste(472-475), bind_add_to_list(479-500), on_enter(482-493), __init__(504-521), _check_for_updates(523-528), _setup_style(530-566), _shade(569-574), on_close(576-581), redo_network_setup(583-599), backup_now(601-608), restore_backup(610-628), _ctrl_f(630-642), _open_exact_find_text_popup(644-689), do_find(665-674), close(675-682), _global_enter(691-703), wipe(705-706), login(708-737), do_login(723-734), change_password(739-789), save_password(761-783), logout(791-796), home(798-823), _restore_dashboard_after_internal_close(825-839), _ensure_mdi_host(841-862), _internal_window(864-950), normal_place(880-886), restore(887-894), maximize(895-901), minimize(902-917), close(918-943), open_inventory_codes_detail_flow(952-970), open_inventory_codes_with_filters(972-986), open_inventory_codes_report_window(988-1214), tbtn(1006-1011), balance_as_of(1068-1078), build_nav(1080-1102), selected_prefix(1104-1113), load(1115-1147), page_move(1149-1150), page_first(1151-1151), page_last(1152-1156), on_nav(1160-1161), find_popup(1164-1183), search_fn(1166-1181), print_report(1186-1189), export_pdf(1191-1193), export_word(1194-1196), export_excel(1197-1199), open_menu_window(1216-1238), close_window(1226-1233), _manual_check_update(1240-1244), _show_current_version(1246-1250), build_menu_bar(1252-1299), open_calendar_picker(1301-1349), pick(1319-1321), redraw(1323-1335), nav(1337-1341), make_date_field(1351-1358), clearbody(1360-1386), run_action(1375-1380), _portable_print_current(1388-1399), portable_print_dialog(1401-1474), build_receipt(1428-1446), send(1447-1460), refresh_printers(1461-1467), preview_tree(1476-1488), set_page_actions(1490-1498), _add_transaction_new_button(1500-1517), _report_header(1519-1583), _report_footer(1585-1591), _grr_signature_block(1593-1609), _finish_page(1611-1612), _wrap_text_to_width(1614-1639), fits(1621-1621), _pdf_table_report(1641-1710), table_header(1663-1668), show_preview_window(1712-1785), _safe_report_name(1787-1790), print_preview_window(1792-1795), _fallback_pdf_export(1797-1830), esc(1801-1802), add(1805-1807), _save_entry_report(1832-1852), export_preview_pdf(1854-1883), export_preview_word(1885-1925), export_preview_excel(1927-1963), make_tree(1965-1974), pick_item(1976-1997), choose(1977-1996), ld(1984-1988), sel(1990-1994), bind_item_lookup(1999-2016), lookup(2001-2014), _set_form_editable(2019-2032), walk(2022-2031), document_selector(2034-2068), refresh(2039-2050), selected(2051-2056), dashboard(2070-2182), load_details(2154-2178), _refresh_dashboard_kpis(2184-2198), dashboard_details(2200-2204), item_history(2206-2226), _ask_item_master_filters(2228-2312), finish(2281-2293), items(2314-2552), hierarchy(2355-2364), selected_prefix(2410-2423), balance_as_of(2425-2432), load(2434-2472), set_page(2474-2475), select_node(2477-2498), open_find(2504-2523), search_fn(2506-2521), visible_rows(2528-2530), print_inventory(2531-2535), export_inventory_word(2536-2538), export_inventory_excel(2539-2541), portable_inventory(2546-2548), inventory_codes(2554-2838), btn(2590-2595), close_editor(2631-2641), edit_cell(2643-2669), commit(2661-2667), rows_query(2671-2684), load(2686-2701), new_record(2703-2724), commit(2717-2721), selected_row(2726-2728), edit_record(2730-2738), save_record(2740-2783), delete_record(2785-2796), refresh(2798-2798), do_print(2799-2801), do_close(2802-2802), filter_grid(2820-2827), open_mto_inventory_flow(2840-2863), open_code_opening_flow(2865-2873), code_opening(2875-2876), _open_code_opening_popup(2878-2879), _open_code_opening_detail(2881-3124), norm(2951-2952), table_for(2954-2955), row_for(2957-2962), search_any_destination(2964-2977), desc_hit(2979-2983), clear_form(2985-2998), load_for_edit(3000-3021), check_duplicates(3023-3034), save_code(3039-3090), edit_action(3092-3096), delete_code(3098-3113), _mto_new_item_dialog(3126-3162), save(3142-3159), _item_filter_bar(3164-3176), _date_filter_bar(3178-3186), _ask_mto_inventory_filters(3188-3233), finish(3218-3226), mto_inventory(3235-3435), open_find(3269-3288), search_fn(3271-3286), hierarchy(3307-3311), rebuild_nav(3313-3324), mto_balance(3348-3357), load(3359-3401), set_page(3403-3403), select_node(3404-3413), visible_rows(3418-3418), do_print(3419-3423), export_word(3424-3426), export_excel(3427-3429), party_master(3437-3488), load(3447-3450), clear(3451-3455), new_form(3456-3457), save(3458-3464), load_party_row(3465-3469), on_party_select(3470-3471), edit(3473-3477), delete_party(3478-3484), user_management(3490-3574), sync_role(3517-3522), load(3526-3529), clear(3530-3533), edit(3534-3541), save(3542-3559), delete_user(3560-3571), _renumber_tree(3577-3580), demand(3582-3746), _restore_demand_tree_columns(3625-3631), add(3634-3642), edit_item(3644-3656), delete_item(3658-3666), new_form(3670-3676), save(3678-3694), delete_current(3698-3704), cancel_form(3705-3713), preview_now(3714-3724), edit_saved_demand(3725-3728), print_now(3729-3739), load_demand_into_form(3748-3760), refresh_saved_cache(3762-3774), grr(3776-3939), add(3808-3816), edit_item(3818-3828), delete_item(3830-3838), new_form(3842-3848), save(3850-3871), delete_current(3875-3881), cancel_form(3882-3890), preview_now(3891-3909), portable_current(3910-3913), edit_saved_grr(3915-3918), print_now(3919-3932), load_grr_into_form(3941-3953), issue(3955-4101), old_issue_qty(3984-3987), update_balance(3988-3996), add(3998-4007), edit_item(4009-4020), new_form(4024-4030), post(4032-4053), delete_current(4054-4060), cancel_form(4061-4069), preview_now(4070-4077), portable_current(4078-4080), load_saved_issue(4085-4087), edit_saved_issue(4088-4091), print_issue_now(4092-4097), load_issue_into_form(4103-4116), _ask_report_criteria(4118-4181), finish(4167-4175), _open_report_child(4183-4188), open_stock_balance_report_flow(4190-4193), open_grr_report_flow(4195-4198), open_demand_report_flow(4200-4203), open_issue_report_flow(4205-4208), open_party_report_flow(4210-4213), _ask_stock_balance_filters(4215-4238), ok(4230-4231), cancel(4232-4232), stock_balance(4240-4303), period(4256-4267), header_summary(4268-4269), load(4270-4279), reopen_filters(4280-4284), open_find_stock(4288-4301), search_fn(4290-4300), ledger(4305-4317), open_document_editor(4319-4327), _edit_from_selector(4329-4345), show_saved_records(4347-4378), view(4370-4374), documents(4380-4425), edit_selected(4399-4405), delete_selected(4406-4418), doc_export_selected(4427-4433), doc_preview_selected(4435-4445), doc_print_selected(4447-4455), load_document(4457-4487), _print_loaded_document(4481-4486), _report_filter_popup(4489-4506), ok(4502-4503), cancel(4504-4504), _report_window(4508-4552), load(4521-4528), hdr(4529-4529), open_find_report(4535-4549), search_fn(4537-4548), report_grr(4554-4565), pb(4556-4564), report_demand(4567-4578), pb(4569-4577), report_issue(4580-4589), pb(4582-4588), report_party(4591-4601), pb(4593-4600), reports(4603-4731), load_grr_item(4616-4621), load_grr_date(4629-4637), load_party(4649-4657), load_dem_item(4670-4675), load_dem_date(4683-4691), load_iss_item(4705-4710), load_iss_date(4718-4726), print_item_master(4733-4735), print_party_master(4737-4739), print_report(4741-4755), print_stock(4757-4762), print_ledger(4764-4771), _get_doc_data(4773-4801), export_word(4803-4850), export_excel(4852-4892), preview_pdf(4894-4902), _open_direct_printer(4904-4934), _select_windows_printer_for_pdf(4936-5307), render_preview(5061-5080), on_resize(5082-5084), parse_page_selection(5103-5119), selected_printer(5121-5123), print_rendered_pages(5125-5283), close(5285-5295), print_pdf(5309-5327), open_file(5329-5334), print_demand(5336-5341), print_grr(5343-5351), print_issue(5353-5358)

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
0307:         db_candidates = [
0308:             os.path.abspath(DB),
0309:             os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db"),
0310:             os.path.join(r"C:\StoreInventoryManagement", "store_inventory.db"),
0311:         ]
0312:         db_path = next((p for p in db_candidates if os.path.isfile(p)), None)
0313:         if not db_path:
0314:             # The live connection may have been created through the storage
0315:             # layer even when the original legacy path is absent.
0316:             try:
0317:                 raw = sqlite3.connect(os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db"))
0318:                 raw.close()
```
```text
0311:         ]
0312:         db_path = next((p for p in db_candidates if os.path.isfile(p)), None)
0313:         if not db_path:
0314:             # The live connection may have been created through the storage
0315:             # layer even when the original legacy path is absent.
0316:             try:
0317:                 raw = sqlite3.connect(os.path.join(r"C:\StoreInventoryManagement", "Data", "store_inventory.db"))
0318:                 raw.close()
0319:                 db_path = db_candidates[1] if os.path.isfile(db_candidates[1]) else None
0320:             except Exception:
0321:                 db_path = None
0322:         if not db_path:
0323:             return None
0324: 
0325:         stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
0326:         tag = "manual" if manual else "auto"
0327:         latest = os.path.join(BACKUP_DIR, "inventory_backup_latest.db")
0328:         dated = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.db")
0329:         zpath = os.path.join(BACKUP_DIR, f"inventory_backup_{tag}_{stamp}.zip")
0330: 
0331:         src = sqlite3.connect(db_path, timeout=30)
```
```text
0335:             except Exception:
0336:                 pass
0337:             for path in (latest, dated):
0338:                 if os.path.exists(path):
0339:                     try:
0340:                         os.remove(path)
0341:                     except OSError:
0342:                         pass
0343:                 dst = sqlite3.connect(path, timeout=30)
0344:                 try:
0345:                     with dst:
0346:                         src.backup(dst)
0347:                 finally:
0348:                     dst.close()
0349:         finally:
0350:             src.close()
0351: 
0352:         if not os.path.isfile(dated) or os.path.getsize(dated) <= 0:
0353:             return None
0354:         with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
0355:             z.write(dated, "store_inventory.db")
```
```text
0353:             return None
0354:         with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
0355:             z.write(dated, "store_inventory.db")
0356:         if not os.path.isfile(zpath) or os.path.getsize(zpath) <= 0:
0357:             return None
0358:         return zpath
0359:     except Exception:
0360:         return None
0361: def restore_database(backup_path):
0362:     """Restore the database from a .db or .zip backup file. The current
0363:     database is itself backed up first, so a restore can never destroy data."""
0364:     try:
0365:         backup_database(manual=True)  # safety net before touching anything
0366:         if backup_path.lower().endswith(".zip"):
0367:             with zipfile.ZipFile(backup_path,"r") as z:
0368:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0369:                 os.makedirs(tmp_dir,exist_ok=True)
0370:                 z.extractall(tmp_dir)
0371:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0372:                 shutil.copy2(extracted,DB)
0373:                 shutil.rmtree(tmp_dir,ignore_errors=True)
```
```text
0367:             with zipfile.ZipFile(backup_path,"r") as z:
0368:                 tmp_dir=os.path.join(BACKUP_DIR,"_restore_tmp")
0369:                 os.makedirs(tmp_dir,exist_ok=True)
0370:                 z.extractall(tmp_dir)
0371:                 extracted=os.path.join(tmp_dir,"store_inventory.db")
0372:                 shutil.copy2(extracted,DB)
0373:                 shutil.rmtree(tmp_dir,ignore_errors=True)
0374:         else:
0375:             shutil.copy2(backup_path,DB)
0376:         return True
0377:     except Exception:
0378:         return False
0379: 
0380: def stock(c, code):
0381:     r=c.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()
0382:     q=float(r[0] or 0) if r else 0
0383:     for typ,qty in c.execute("SELECT doc_type,qty FROM transactions WHERE code=? ORDER BY id", (code,)):
0384:         q += float(qty or 0) if typ=="GRR" else -float(qty or 0) if typ=="ISSUE" else 0
0385:     return q
0386: 
0387: def fmt_num(x):
```
```text
0385:     return q
0386: 
0387: def fmt_num(x):
0388:     x=float(x or 0)
0389:     return f"{x:,.2f}".rstrip("0").rstrip(".")
0390: 
0391: def to_iso_date(s):
0392:     """Convert a user-entered DD/MM/YYYY date (or an already-ISO date) into
0393:     ISO YYYY-MM-DD for storage in the database and for date-range queries,
0394:     which rely on ISO strings sorting/comparing correctly."""
0395:     s=(s or "").strip()
0396:     if not s: return ""
0397:     for f in ("%d/%m/%Y","%Y-%m-%d"):
0398:         try: return datetime.strptime(s,f).strftime("%Y-%m-%d")
0399:         except Exception: continue
0400:     return s
0401: 
0402: def to_display_date(s):
0403:     """Convert an ISO YYYY-MM-DD date (as stored in the database) into the
0404:     DD/MM/YYYY format used everywhere on screen and on printed reports."""
0405:     s=(s or "").strip()
```
```text
0500:     return on_enter
0501: 
0502: 
0503: class App(tk.Tk):
0504:     def __init__(self):
0505:         super().__init__()
0506:         self.title("Store Inventory Management System | SAP Style")
0507:         self.geometry("1400x820"); self.minsize(1150,700)
0508:         self.conn=connect()
0509:         self.demand_lines=[]; self.grr_lines=[]; self.issue_lines=[]
0510:         self.current_user=None; self.current_role=None
0511:         self._item_master_search_entry=None
0512:         self._item_master_find_callback=None
0513:         self._portable_print_context=None
0514:         self.can_edit=False; self.can_delete=False; self.is_admin=False
0515:         self._setup_style()
0516:         # Any focused button can be activated with Enter.
0517:         self.bind_all("<Return>", self._global_enter, add="+")
0518:         self.bind_all("<KP_Enter>", self._global_enter, add="+")
0519:         self.bind_all("<Control-f>", self._ctrl_f, add="+")
0520:         self.protocol("WM_DELETE_WINDOW", self.on_close)
```
```text
0568:     @staticmethod
0569:     def _shade(hexcolor, factor):
0570:         """Return a slightly darker version of a #RRGGBB color (for hover/press states)."""
0571:         h=hexcolor.lstrip("#")
0572:         r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
0573:         r,g,b=(max(0,int(v*factor)) for v in (r,g,b))
0574:         return f"#{r:02x}{g:02x}{b:02x}"
0575: 
0576:     def on_close(self):
0577:         try:
0578:             self.conn.commit(); backup_database()
0579:         except Exception:
0580:             pass
0581:         self.destroy()
0582: 
0583:     def redo_network_setup(self):
0584:         if not messagebox.askyesno("Network Setup",
0585:             "This will clear the online database URL saved on this computer.\n\n"
0586:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0587:             "Continue?"):
0588:             return
```
```text
0582: 
0583:     def redo_network_setup(self):
0584:         if not messagebox.askyesno("Network Setup",
0585:             "This will clear the online database URL saved on this computer.\n\n"
0586:             "The program will close - edit firebase_database_url.txt, then run it again.\n\n"
0587:             "Continue?"):
0588:             return
0589:         try:
0590:             self.conn.commit(); backup_database()
0591:         except Exception:
0592:             pass
0593:         try:
0594:             if os.path.exists(FIREBASE_URL_FILE): os.remove(FIREBASE_URL_FILE)
0595:         except Exception:
0596:             pass
0597:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0598:         self.destroy()
0599:         sys.exit(0)
0600: 
0601:     def backup_now(self):
0602:         path=backup_database(manual=True)
```
```text
0596:             pass
0597:         messagebox.showinfo("Network Setup","Online setup cleared. The program will now close. Add the Firebase Realtime Database URL to firebase_database_url.txt and start again.")
0598:         self.destroy()
0599:         sys.exit(0)
0600: 
0601:     def backup_now(self):
0602:         path=backup_database(manual=True)
0603:         if path:
0604:             messagebox.showinfo("Backup Complete",
0605:                 f"A full backup was saved to:\n\n{path}\n\n"
0606:                 f"All backups are kept in:\n{BACKUP_DIR}")
0607:         else:
0608:             messagebox.showerror("Backup Failed","Could not create a backup. Make sure the database exists.")
0609: 
0610:     def restore_backup(self):
0611:         from tkinter import filedialog
0612:         if not messagebox.askyesno("Restore Backup",
0613:             "This will replace all current data with the selected backup.\n"
0614:             "A safety backup of the current data will be made first.\n\n"
0615:             "Continue?"):
0616:             return
```
```text
0610:     def restore_backup(self):
0611:         from tkinter import filedialog
0612:         if not messagebox.askyesno("Restore Backup",
0613:             "This will replace all current data with the selected backup.\n"
0614:             "A safety backup of the current data will be made first.\n\n"
0615:             "Continue?"):
0616:             return
0617:         path=filedialog.askopenfilename(
0618:             title="Select a backup file",
0619:             initialdir=BACKUP_DIR,
0620:             filetypes=[("Backup files","*.zip *.db"),("All files","*.*")])
0621:         if not path: return
0622:         if restore_database(path):
0623:             messagebox.showinfo("Restore Complete",
0624:                 "Data has been restored. The application will now restart.")
0625:             self.conn.close()
0626:             os.execv(sys.executable, [sys.executable]+sys.argv)
0627:         else:
0628:             messagebox.showerror("Restore Failed","Could not restore from that backup file.")
0629: 
0630:     def _ctrl_f(self, event=None):
```
```text
0667:             if not text:
0668:                 fe.focus_set(); return
0669:             try:
0670:                 found=search_fn(text)
0671:             except Exception:
0672:                 found=False
0673:             if found is False:
0674:                 messagebox.showinfo("Find Text","No matching text found.",parent=dlg)
0675:         def close():
0676:             try:
0677:                 dlg.grab_release()
0678:             except Exception: pass
0679:             try: dlg.destroy()
0680:             except Exception: pass
0681:             if getattr(self,"_exact_find_text_dialog",None) is dlg:
0682:                 self._exact_find_text_dialog=None
0683:         ttk.Button(box,text="Find Next",command=do_find,width=13).grid(row=0,column=3,padx=4,pady=4)
0684:         ttk.Button(box,text="Cancel",command=close,width=13).grid(row=1,column=3,padx=4,pady=4)
0685:         fe.bind("<Return>",lambda e:(do_find(),"break"))
0686:         dlg.bind("<Escape>",lambda e:close())
0687:         dlg.protocol("WM_DELETE_WINDOW",close)
```
```text
0753:         cur_ent=ttk.Entry(box,textvariable=current,width=28,show="*"); cur_ent.grid(row=2,column=1,pady=7)
0754:         ttk.Label(box,text="New Password").grid(row=3,column=0,sticky="w",pady=7)
0755:         new_ent=ttk.Entry(box,textvariable=new,width=28,show="*"); new_ent.grid(row=3,column=1,pady=7)
0756:         ttk.Label(box,text="Confirm New Password").grid(row=4,column=0,sticky="w",pady=7)
0757:         conf_ent=ttk.Entry(box,textvariable=confirm,width=28,show="*"); conf_ent.grid(row=4,column=1,pady=7)
0758:         err=ttk.Label(box,text="",foreground="#c0392b",wraplength=380,justify="left")
0759:         err.grid(row=5,column=0,columnspan=2,pady=(5,8))
0760: 
0761:         def save_password(event=None):
0762:             old_pw=current.get()
0763:             new_pw=new.get()
0764:             confirm_pw=confirm.get()
0765:             row=self.conn.execute("SELECT password FROM users WHERE username=?",(self.current_user,)).fetchone()
0766:             if not row or not verify_password(old_pw,row[0]):
0767:                 err.config(text="Current password is incorrect."); return
0768:             if len(new_pw) < 4:
0769:                 err.config(text="New password must be at least 4 characters."); return
0770:             if new_pw != confirm_pw:
0771:                 err.config(text="New password and confirmation do not match."); return
0772:             if new_pw == old_pw:
0773:                 err.config(text="New password must be different from the current password."); return
```
```text
0769:                 err.config(text="New password must be at least 4 characters."); return
0770:             if new_pw != confirm_pw:
0771:                 err.config(text="New password and confirmation do not match."); return
0772:             if new_pw == old_pw:
0773:                 err.config(text="New password must be different from the current password."); return
0774:             try:
0775:                 self.conn.execute("UPDATE users SET password=? WHERE username=?",
0776:                                   (hash_password(new_pw),self.current_user))
0777:                 self.conn.commit()
0778:                 backup_database()
0779:                 win.grab_release(); win.destroy()
0780:                 messagebox.showinfo("Password Changed",
0781:                     "Your password has been changed successfully.\n\nUse the new password the next time you log in.", parent=self)
0782:             except Exception as ex:
0783:                 err.config(text=f"Could not change password: {ex}")
0784: 
0785:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0786:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0787:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0788:         conf_ent.bind("<Return>",save_password)
0789:         cur_ent.focus_set()
```
```text
0785:         btns=ttk.Frame(box); btns.grid(row=6,column=0,columnspan=2,pady=(5,0))
0786:         ttk.Button(btns,text="CHANGE PASSWORD",command=save_password).pack(side="left",padx=5)
0787:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left",padx=5)
0788:         conf_ent.bind("<Return>",save_password)
0789:         cur_ent.focus_set()
0790: 
0791:     def logout(self):
0792:         try:
0793:             self.conn.commit(); backup_database()
0794:         except Exception:
0795:             pass
0796:         self.login()
0797: 
0798:     def home(self):
0799:         self.wipe()
0800:         self.build_menu_bar()
0801:         hdr=tk.Frame(self,bg=COLORS["primary_dark"]);hdr.pack(fill="x")
0802:         self._shell_header=hdr
0803:         inner=tk.Frame(hdr,bg=COLORS["primary_dark"],padx=16,pady=10);inner.pack(fill="x")
0804:         tk.Label(inner,text=COMPANY,font=("Segoe UI",16,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="left")
0805:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
```
```text
0805:         tk.Label(inner,text="  |  Store Inventory Management",font=("Segoe UI",11),bg=COLORS["primary_dark"],fg="#CFE0F5").pack(side="left")
0806:         tk.Label(inner,text=f"Data: {DATA_DIR}",font=("Segoe UI",8),bg=COLORS["primary_dark"],fg="#9FB8DA").pack(side="left",padx=14)
0807:         ttk.Button(inner,text="Logout",style="Danger.TButton",command=self.logout).pack(side="right")
0808:         tk.Label(inner,text=f"{self.current_user}  ({self.current_role})",font=("Segoe UI",9,"bold"),bg=COLORS["primary_dark"],fg="white").pack(side="right",padx=12)
0809:         nav=tk.Frame(self,bg=COLORS["primary"]);nav.pack(fill="x")
0810:         self._shell_nav=nav
0811:         navin=tk.Frame(nav,bg=COLORS["primary"],padx=10,pady=6);navin.pack(fill="x")
0812:         ttk.Button(navin,text="🏠  Dashboard",style="Accent.TButton",command=self.dashboard).pack(side="left",padx=3)
0813:         tk.Label(navin,text="Inventory  |  Transaction  |  Report  |  Edit  |  Help  —  see the menu bar above for every other section.",
0814:                  font=("Segoe UI",8),bg=COLORS["primary"],fg="#E7EFFB").pack(side="left",padx=14)
0815:         self.body=ttk.Frame(self,padding=12);self.body.pack(fill="both",expand=True)
0816:         self.main_body=self.body
0817:         self.dashboard()
0818:         if not getattr(self, "_update_checked_this_session", False):
0819:             self._update_checked_this_session = True
0820:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0821:         if not getattr(self, "_update_checked_this_session", False):
0822:             self._update_checked_this_session = True
0823:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0824: 
0825:     def _restore_dashboard_after_internal_close(self):
```
```text
0910:             b.pack(side="left")
0911:             rb=tk.Button(item,text="□",font=("Segoe UI",8,"bold"),width=2,height=1,padx=0,pady=0,
0912:                          command=lambda:(restore(),maximize()),relief="flat",bd=0,bg="#e7e7e7")
0913:             rb.pack(side="left")
0914:             xb=tk.Button(item,text="×",font=("Segoe UI",9,"bold"),width=2,height=1,padx=0,pady=0,
0915:                          command=close,relief="flat",bd=0,bg="#e7e7e7")
0916:             xb.pack(side="left")
0917:             state["task"]=item
0918:         def close():
0919:             try:
0920:                 task=state.get("task")
0921:                 if task and task.winfo_exists(): task.destroy()
0922:             except Exception: pass
0923:             try:
0924:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
0925:             except Exception: pass
0926:             try: outer.destroy()
0927:             except Exception: pass
0928:             if not getattr(self,"_mdi_windows",[]):
0929:                 self._mdi_host.place_forget()
0930:                 self._restore_dashboard_after_internal_close()
```
```text
0923:             try:
0924:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
0925:             except Exception: pass
0926:             try: outer.destroy()
0927:             except Exception: pass
0928:             if not getattr(self,"_mdi_windows",[]):
0929:                 self._mdi_host.place_forget()
0930:                 self._restore_dashboard_after_internal_close()
0931:                 self._restore_dashboard_after_internal_close()
0932:                 # Restore the original application shell FIRST, then rebuild
0933:                 # only the Dashboard body. This keeps the top header/navigation
0934:                 # exactly as they are when the application starts.
0935:                 try:
0936:                     if getattr(self,"_shell_header",None) is not None and self._shell_header.winfo_exists():
0937:                         self._shell_header.pack(fill="x",before=self.body)
0938:                     if getattr(self,"_shell_nav",None) is not None and self._shell_nav.winfo_exists():
0939:                         self._shell_nav.pack(fill="x",before=self.body,after=self._shell_header)
0940:                 except Exception: pass
0941:                 try:
0942:                     self.dashboard()
0943:                 except Exception: pass
```
```text
0976:             return None
0977:         self._inventory_codes_filter=criteria
0978:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0979:         try:
0980:             self.items(container=body)
0981:             win.lift()
0982:             return win
0983:         except Exception:
0984:             try: win._internal_close()
0985:             except Exception: pass
0986:             raise
0987: 
0988:     def open_inventory_codes_report_window(self, criteria=None):
0989:         """Open Inventory Codes as a real report-style child window.
0990: 
0991:         This intentionally mirrors the supplied Preview Report workflow: a
0992:         separate resizable/maximizable window with a left navigation tree,
0993:         compact report toolbar, Find dialog, and print/export commands.
0994:         The main application remains open behind it.
0995:         """
0996:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
0993:         compact report toolbar, Find dialog, and print/export commands.
0994:         The main application remains open behind it.
0995:         """
0996:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
0997:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
0998:         }
0999:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
1000: 
1001:         # --- report-style toolbar ---
1002:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
1003:         toolbar.pack(fill="x",side="top")
1004:         toolbar.pack_propagate(False)
1005: 
1006:         def tbtn(text,cmd,width=9):
1007:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
1008:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
1009:                          padx=3,pady=1)
1010:             b.pack(side="left",padx=2,pady=6)
1011:             return b
1012: 
1013:         # --- main report body ---
```
```text
1024:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
1025:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
1026:         navscroll.config(command=code_tree.yview)
1027:         navscroll.pack(side="right",fill="y")
1028:         code_tree.pack(side="left",fill="both",expand=True)
1029: 
1030:         right=tk.Frame(content,bg="#EDEDED")
1031:         right.pack(side="left",fill="both",expand=True)
1032:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
1033:         reportbar.pack(fill="x")
1034:         reportbar.pack_propagate(False)
1035:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
1036:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
1037:         tab.pack(side="left",padx=4,pady=2)
1038:         titlevar=tk.StringVar(value="Inventory Summary")
1039:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
1040:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
1041: 
1042:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
1043:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
1044:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1178:                     vals=tree.item(iid,"values")
1179:                     if str(vals[1]).lower()==str(target).lower():
1180:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1181:                 return True
1182:             self._open_exact_find_text_popup(search_fn)
1183:             self._item_master_find_callback=find_popup
1184: 
1185: 
1186:         def print_report():
1187:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1188:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1189:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1190: 
1191:         def export_pdf():
1192:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1193:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1194:         def export_word():
1195:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1196:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1197:         def export_excel():
1198:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1194:         def export_word():
1195:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1196:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1197:         def export_excel():
1198:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1199:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1200: 
1201:         tbtn("Find",find_popup,7)
1202:         tbtn("Print",print_report,7)
1203:         tbtn("PDF",export_pdf,6)
1204:         tbtn("Word",export_word,6)
1205:         tbtn("Excel",export_excel,6)
1206:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1207:         tbtn("Refresh",load,8)
1208:         tbtn("Close",win._internal_close,7)
1209:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1210:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1211: 
1212:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1213:         build_nav(); load(); win.focus_force()
1214:         return win
```
```text
1224:         self.body=frame
1225:         closed={"done":False}
1226:         def close_window():
1227:             if closed["done"]: return
1228:             closed["done"]=True
1229:             if getattr(self,"body",None) is frame: self.body=old_body
1230:             self._page_actions=old_actions
1231:             self._item_master_find_callback=old_find
1232:             try: win._internal_close()
1233:             except Exception: win.destroy()
1234:         win._internal_close=close_window
1235:         try:
1236:             method(); self.update_idletasks(); win.lift(); return win
1237:         except Exception:
1238:             close_window(); raise
1239: 
1240:     def _manual_check_update(self):
1241:         try:
1242:             updater.check_for_update(self, manual=True)
1243:         except Exception as e:
1244:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1248:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1249:         except Exception as e:
1250:             messagebox.showerror("Current Version", str(e), parent=self)
1251: 
1252:     def build_menu_bar(self):
1253:         """Professional section / sub-section menu bar, ERP style:
1254:         Inventory > Item Master
1255:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1256:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1257:         Edit > Change Password, User Management
1258:         Help > Backup Now, Restore Backup, Network Setup
1259:         """
1260:         menubar=tk.Menu(self)
1261: 
1262:         m_inv=tk.Menu(menubar,tearoff=0)
1263:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1264:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1265:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1266:         menubar.add_cascade(label="Inventory",menu=m_inv)
1267: 
1268:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1268:         m_trans=tk.Menu(menubar,tearoff=0)
1269:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1270:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1271:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1272:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1273:         menubar.add_cascade(label="Transaction",menu=m_trans)
1274: 
1275:         m_rep=tk.Menu(menubar,tearoff=0)
1276:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1277:         m_rep.add_separator()
1278:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1279:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1280:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1281:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1282:         menubar.add_cascade(label="Report",menu=m_rep)
1283: 
1284:         m_edit=tk.Menu(menubar,tearoff=0)
1285:         m_edit.add_command(label="Change Password",command=self.change_password)
1286:         if self.is_admin:
1287:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1288:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1283: 
1284:         m_edit=tk.Menu(menubar,tearoff=0)
1285:         m_edit.add_command(label="Change Password",command=self.change_password)
1286:         if self.is_admin:
1287:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1288:         menubar.add_cascade(label="Edit",menu=m_edit)
1289: 
1290:         m_help=tk.Menu(menubar,tearoff=0)
1291:         m_help.add_command(label="Backup Now",command=self.backup_now)
1292:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1293:         m_help.add_command(label="Current Version",command=self._show_current_version)
1294:         if self.is_admin:
1295:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1296:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1297:         menubar.add_cascade(label="Help",menu=m_help)
1298: 
1299:         self.config(menu=menubar)
1300: 
1301:     def open_calendar_picker(self, var):
1302:         """Small month-grid calendar popup. Picking a day sets `var` to
1303:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1356:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1357:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1358:         return f
1359: 
1360:     def clearbody(self):
1361:         self._portable_print_context=None
1362:         for w in self.body.winfo_children(): w.destroy()
1363:         self._page_actions = {
1364:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1365:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1366:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1367:             "cancel": lambda: self.dashboard(),
1368:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1369:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1370:         }
1371:         # Single SAP-style toolbar at the very top.
1372:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1373:         self._page_action_bar=bar
1374:         self._page_action_first_button=None
1375:         def run_action(k):
1376:             if k=="edit" and not self.can_edit:
```
```text
1373:         self._page_action_bar=bar
1374:         self._page_action_first_button=None
1375:         def run_action(k):
1376:             if k=="edit" and not self.can_edit:
1377:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1378:             if k=="delete" and not self.can_delete:
1379:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1380:             self._page_actions[k]()
1381:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1382:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1383:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1384:             b.pack(side="left",padx=(0,2))
1385:             if self._page_action_first_button is None: self._page_action_first_button=b
1386:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1387: 
1388:     def _portable_print_current(self):
1389:         ctx=getattr(self,"_portable_print_context",None)
1390:         if not ctx:
1391:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1392:             return
1393:         try:
```
```text
1395:             if not data: return
1396:             title,header,columns,rows=data
1397:             self.portable_print_dialog(title,header,columns,rows)
1398:         except Exception as e:
1399:             messagebox.showerror("Portable Printer",str(e))
1400: 
1401:     def portable_print_dialog(self,title,header_lines,columns,rows):
1402:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1403:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1404:         if not WIN32PRINT_AVAILABLE:
1405:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1406:             return
1407:         try:
1408:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1409:         except Exception as e:
1410:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1411:             return
1412:         if not printers:
1413:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1414:             return
1415:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1465:                 if vals and pv.get() not in vals: pv.set(vals[0])
1466:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1467:             except Exception as ex: status.set(str(ex))
1468:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1469:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1470:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1471:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1472:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1473:         win.bind("<Escape>",lambda e:win._internal_close())
1474:         win.focus_force()
1475: 
1476:     def preview_tree(self, title, tree, header_lines=None):
1477:         """Preview the exact rows currently visible in a Treeview."""
1478:         cols=list(tree["columns"])
1479:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1480:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1481:         if not rows:
1482:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1483:             return
1484:         widths=[]
1485:         for c in cols:
```
```text
1482:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1483:             return
1484:         widths=[]
1485:         for c in cols:
1486:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1487:             except Exception: widths.append(100)
1488:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1489: 
1490:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1491:         self._page_actions.update({
1492:             "save": save or self._page_actions.get("save"),
1493:             "edit": edit or self._page_actions.get("edit"),
1494:             "delete": delete or self._page_actions.get("delete"),
1495:             "cancel": cancel or self._page_actions.get("cancel"),
1496:             "print": print or self._page_actions.get("print"),
1497:             "preview": preview or self._page_actions.get("preview"),
1498:         })
1499: 
1500:     def _add_transaction_new_button(self, command):
1501:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1502:         if bar is None or first is None: return
```
```text
1511:         sep.pack(side="left",fill="y",padx=4)
1512:         for w in existing:
1513:             try:
1514:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1515:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1516:                 else: w.pack(side="left")
1517:             except Exception: pass
1518: 
1519:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1520:         """Draw a consistent professional report header and return the first table Y.
1521: 
1522:         For GRN Receipt reports the document number is shown on the left and
1523:         the GRN Date is deliberately shown on the right in a bordered document
1524:         information panel.
1525:         """
1526:         W,H=page_size
1527:         if y_top is None: y_top=H-24
1528:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1529:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1530:         if os.path.exists(LOGO_FILE):
1531:             try:
```
```text
1524:         information panel.
1525:         """
1526:         W,H=page_size
1527:         if y_top is None: y_top=H-24
1528:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1529:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1530:         if os.path.exists(LOGO_FILE):
1531:             try:
1532:                 from reportlab.lib.utils import ImageReader
1533:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1534:             except Exception:
1535:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1536:         else:
1537:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1538:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1539:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1540:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1541:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1542: 
1543:         # Professional document information box.
1544:         info_top=logo_y-12
```
```text
1577:                 # naturally occupies the right-hand cell when supplied second.
1578:                 c.setFont("Helvetica-Bold",7)
1579:                 c.drawString(xx,yy,(label+":")[:28])
1580:                 c.setFont("Helvetica",7)
1581:                 c.drawString(xx+58,yy,val[:58])
1582:             return box_y-12
1583:         return info_top-6
1584: 
1585:     def _report_footer(self, c, page_no, page_size=A4):
1586:         W,H=page_size
1587:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1588:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1589:         c.drawString(24,13,REPORT_FOOTER)
1590:         c.drawRightString(W-24,13,f"Page {page_no}")
1591:         c.setFillColorRGB(0,0,0)
1592: 
1593:     def _grr_signature_block(self, c, y, page_size=A4):
1594:         """Draw the three requested transaction-document signature lines."""
1595:         W,H=page_size
1596:         labels=["Prepared By","Store Keeper","Store Incharge"]
1597:         block_h=70
```
```text
1604:             x=left+i*col_w
1605:             c.setLineWidth(0.6)
1606:             c.line(x+30,top-34,x+col_w-30,top-34)
1607:             c.setFont("Helvetica-Bold",7)
1608:             c.drawCentredString(x+col_w/2,top-48,label)
1609:         return True
1610: 
1611:     def _finish_page(self, c, page_no, page_size=A4):
1612:         self._report_footer(c,page_no,page_size); c.showPage()
1613: 
1614:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1615:         """Word-wrap `text` into a list of lines that each fit inside
1616:         max_width (points) at the given font, breaking mid-word only when a
1617:         single word is itself wider than the column."""
1618:         text=str(text) if text is not None else ""
1619:         if not text:
1620:             return [""]
1621:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1622:         lines=[]; cur=""
1623:         for word in text.split(" "):
1624:             trial=(cur+" "+word).strip() if cur else word
```
```text
1633:                     mid=(lo+hi)//2
1634:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1635:                     else: hi=mid-1
1636:                 lines.append(w[:fit_at]); w=w[fit_at:]
1637:             cur=w
1638:         if cur: lines.append(cur)
1639:         return lines or [""]
1640: 
1641:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1642:         """Create a paginated professional PDF with logo, bordered information,
1643:         GRR signature lines and page numbers. Also keep the same report data in
1644:         memory so the built-in Windows printer dialog can print directly without
1645:         requiring a PDF application's PrintTo association."""
1646:         if not hasattr(self, "_print_jobs"):
1647:             self._print_jobs = {}
1648:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1649:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1650:         page=1
1651:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1652:         usable=W-56
1653:         n=max(1,len(headers))
```
```text
1675:             if desc_idx is not None and desc_idx < len(r):
1676:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1677:             else:
1678:                 desc_lines=[""]
1679:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1680:             # Reserve room on the final page for the three transaction signatures + footer.
1681:             reserve=120 if is_transaction_doc else 42
1682:             if y-row_h<reserve:
1683:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1684:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1685:             # Item rows are intentionally border-free. The section/header remains
1686:             # professional while avoiding the unwanted boxed line around each
1687:             # individual printed item row. Description is drawn separately
1688:             # below (auto-fit / wrapped), so it is skipped in this pass.
1689:             for ci,(xx,val) in enumerate(zip(xs,r)):
1690:                 if ci==desc_idx: continue
1691:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1692:             if desc_idx is not None and desc_idx < len(r):
1693:                 for li,ln in enumerate(desc_lines):
1694:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1695:             y-=row_h
```
```text
1690:                 if ci==desc_idx: continue
1691:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1692:             if desc_idx is not None and desc_idx < len(r):
1693:                 for li,ln in enumerate(desc_lines):
1694:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1695:             y-=row_h
1696:         if is_transaction_doc:
1697:             # Keep the three requested transaction signatures at the physical bottom
1698:             # final page, immediately above the report footer.  If the item
1699:             # table reaches this reserved area, start a fresh final page.
1700:             bottom_sig_y = 138
1701:             if y < 165:
1702:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1703:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1704:             # Draw signatures at a fixed bottom position so they never float
1705:             # directly after the last item row.
1706:             self._grr_signature_block(c,bottom_sig_y,page_size)
1707:         self._report_footer(c,page,page_size); c.save()
1708:         if auto_print:
1709:             self.print_pdf(path)
1710:         return path
```
```text
1704:             # Draw signatures at a fixed bottom position so they never float
1705:             # directly after the last item row.
1706:             self._grr_signature_block(c,bottom_sig_y,page_size)
1707:         self._report_footer(c,page,page_size); c.save()
1708:         if auto_print:
1709:             self.print_pdf(path)
1710:         return path
1711: 
1712:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1713:         """Professional on-screen preview showing bordered document information
1714:         and a bordered item section. GRN Date is displayed in the right column."""
1715:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1716:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1717:         # Preview intentionally hides the company logo and company name.
1718:         # The actual generated/printed PDF still contains both via
1719:         # _report_header(), so only the on-screen preview is affected.
1720:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1721:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1722:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1723: 
1724:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
```
```text
1745:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1746: 
1747:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1748:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1749:         tr=self.make_tree(items,columns,widths)
1750:         for r in rows: tr.insert("", "end", values=r)
1751: 
1752:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1753:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1754:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1755:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1756:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1757:         win.bind("<Control-f>",bind_preview_find)
1758:         win.bind("<Control-F>",bind_preview_find)
1759: 
1760:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1761:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1762:         if is_transaction_preview:
1763:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1764:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1765:                 sig.columnconfigure(i,weight=1)
```
```text
1763:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1764:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1765:                 sig.columnconfigure(i,weight=1)
1766:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1767:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1768:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1769: 
1770:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1771:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1772:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1773:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1774:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1775:         if on_save:
1776:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1777:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1778:         if not is_transaction_preview:
1779:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1780:         # IMPORTANT: this must remain a normal top-level window (not transient
1781:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1782:         # exactly like the Preview Report window in the supplied recording.
1783:         # The Find dialog is opened from this window and is independent.
```
```text
1776:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1777:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1778:         if not is_transaction_preview:
1779:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1780:         # IMPORTANT: this must remain a normal top-level window (not transient
1781:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1782:         # exactly like the Preview Report window in the supplied recording.
1783:         # The Find dialog is opened from this window and is independent.
1784:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1785:         win.focus_force()
1786: 
1787:     def _safe_report_name(self, title, extension):
1788:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1789:         safe=safe.replace(" ","_") or "Preview"
1790:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1791: 
1792:     def print_preview_window(self, title, header_lines, columns, rows):
1793:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1794:         self._open_direct_printer(title, header_lines, columns, rows,
1795:                                   landscape(A4) if len(columns) > 8 else A4)
1796: 
```
```text
1789:         safe=safe.replace(" ","_") or "Preview"
1790:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1791: 
1792:     def print_preview_window(self, title, header_lines, columns, rows):
1793:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1794:         self._open_direct_printer(title, header_lines, columns, rows,
1795:                                   landscape(A4) if len(columns) > 8 else A4)
1796: 
1797:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1798:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1799:         This keeps the Export PDF button functional on a machine where the bundled
1800:         ReportLab package cannot be imported."""
1801:         def esc(v):
1802:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1803:         W,H=842,595
1804:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1805:         def add(txt,size=8,leading=11):
1806:             lines.append(f"/F1 {size} Tf")
1807:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1808:         add(str(title),12,16)
1809:         for h in header_lines or []:
```
```text
1816:         lines.append("ET")
1817:         stream="\n".join(lines).encode("latin-1","replace")
1818:         objs=[]
1819:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1820:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1821:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1822:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1823:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1824:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1825:         for i,obj in enumerate(objs,1):
1826:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1827:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1828:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1829:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1830:         with open(path,"wb") as f: f.write(out)
1831: 
1832:     def _save_entry_report(self, title, header_lines, columns, rows):
1833:         try:
1834:             os.makedirs(REPORTS_DIR, exist_ok=True)
1835:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1836:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```
```text
1829:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1830:         with open(path,"wb") as f: f.write(out)
1831: 
1832:     def _save_entry_report(self, title, header_lines, columns, rows):
1833:         try:
1834:             os.makedirs(REPORTS_DIR, exist_ok=True)
1835:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1836:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
1837:             path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
1838:             page_size = landscape(A4) if len(columns) > 8 else A4
1839:             if REPORTLAB:
1840:                 self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
1841:             else:
1842:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1843:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1844:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1845:             with open(path, "rb") as f:
1846:                 if f.read(5) != b"%PDF-":
1847:                     raise IOError("Generated report is not a valid PDF.")
1848:             self._last_entry_report_path = path
1849:             return path
```
```text
1843:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1844:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1845:             with open(path, "rb") as f:
1846:                 if f.read(5) != b"%PDF-":
1847:                     raise IOError("Generated report is not a valid PDF.")
1848:             self._last_entry_report_path = path
1849:             return path
1850:         except Exception as exc:
1851:             self._last_entry_report_path = None
1852:             return None
1853: 
1854:     def export_preview_pdf(self, title, header_lines, columns, rows):
1855:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1856:         try:
1857:             os.makedirs(REPORTS_DIR, exist_ok=True)
1858:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1859:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1860:             generated = False
1861:             if REPORTLAB:
1862:                 try:
1863:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
```
```text
1860:             generated = False
1861:             if REPORTLAB:
1862:                 try:
1863:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1864:                     generated = True
1865:                 except Exception:
1866:                     generated = False
1867:             if not generated:
1868:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1869:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1870:                 raise IOError("The PDF file was not created in the Reports folder.")
1871:             with open(path, "rb") as pf:
1872:                 signature = pf.read(5)
1873:             if signature != b"%PDF-":
1874:                 raise IOError("The generated file is not a valid PDF.")
1875:             self._last_report_path = path
1876:             try:
1877:                 webbrowser.open("file://" + path)
1878:             except Exception:
1879:                 self.open_file(path)
1880:             return path
```
```text
1874:                 raise IOError("The generated file is not a valid PDF.")
1875:             self._last_report_path = path
1876:             try:
1877:                 webbrowser.open("file://" + path)
1878:             except Exception:
1879:                 self.open_file(path)
1880:             return path
1881:         except Exception as e:
1882:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1883:             return None
1884: 
1885:     def export_preview_word(self, title, header_lines, columns, rows):
1886:         """Export exactly what is visible in the current preview to Word."""
1887:         if not DOCX_AVAILABLE:
1888:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1889:         path=self._safe_report_name(title,"docx")
1890:         doc=Document()
1891:         sec=doc.sections[0]
1892:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1893:         sec.header.paragraphs[0].runs[0].bold=True
1894:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
```
```text
1916:             doc.add_paragraph("")
1917:             sig=doc.add_table(rows=2,cols=3)
1918:             labels=["Prepared By","Store Keeper","Store Incharge"]
1919:             for i,label in enumerate(labels):
1920:                 sig.cell(0,i).text="____________________"
1921:                 sig.cell(1,i).text=label
1922:                 for para in sig.cell(1,i).paragraphs:
1923:                     for run in para.runs: run.bold=True
1924:         doc.save(path)
1925:         self.open_file(path)
1926: 
1927:     def export_preview_excel(self, title, header_lines, columns, rows):
1928:         """Export exactly what is visible in the current preview to Excel."""
1929:         if not XLSX_AVAILABLE:
1930:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
1931:         path=self._safe_report_name(title,"xlsx")
1932:         wb=openpyxl.Workbook(); ws=wb.active
1933:         ws.title="Preview"
1934:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
1935:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1936:         if not is_transaction_preview:
```
```text
1954:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
1955:             for col in range(1,4):
1956:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
1957:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
1958:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
1959:         for col_cells in ws.columns:
1960:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
1961:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
1962:         wb.save(path)
1963:         self.open_file(path)
1964: 
1965:     def make_tree(self,parent,cols,widths=None):
1966:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
1967:         tr=ttk.Treeview(fr,columns=cols,show="headings")
1968:         for i,c in enumerate(cols):
1969:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
1970:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
1971:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
1972:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
1973:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
1974:         return tr
```
```text
2027:                     w.state(["!disabled"] if editable else ["disabled"])
2028:             except Exception:
2029:                 try: w.configure(state="normal" if editable else "disabled")
2030:                 except Exception: pass
2031:             for ch in w.winfo_children(): walk(ch)
2032:         for root in roots: walk(root)
2033: 
2034:     def document_selector(self, parent, label, typ, var, load_callback):
2035:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
2036:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
2037:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
2038:         combo.pack(side="left", padx=4)
2039:         def refresh():
2040:             vals=[]
2041:             if typ=="demand":
2042:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
2043:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
2044:             elif typ=="grr":
2045:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
2046:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
2047:             else:
```
```text
2054:             no=text.split(" -> ",1)[0].strip()
2055:             var.set(no)
2056:             load_callback(no)
2057:         combo.bind("<<ComboboxSelected>>", selected)
2058:         combo.bind("<Return>", selected)
2059:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2060:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2061:         refresh()
2062:         # Keep the currently open transaction's saved-record list live.
2063:         # Each save calls refresh_saved_cache(), so newly saved records appear
2064:         # immediately without closing/reopening the window or pressing Refresh.
2065:         if not hasattr(self, "_document_selector_refreshers"):
2066:             self._document_selector_refreshers = {}
2067:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2068:         return combo
2069: 
2070:     def dashboard(self):
2071:         # Dashboard-only visual refresh. All existing data queries, filters,
2072:         # callbacks and report/detail behavior are intentionally preserved.
2073:         self.clearbody()
2074:         c=self.conn
```
```text
2155:             for x in tr.get_children(): tr.delete(x)
2156:             params=[];where=[]
2157:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2158:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2159:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2160:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2161:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2162:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2163:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2164:                    FROM transactions t JOIN items i ON i.code=t.code"""
2165:             if where: sql += " WHERE " + " AND ".join(where)
2166:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2167:             rows=list(c.execute(sql,params))
2168:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2169:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2170:             bal_after={}
2171:             for txid,cc,typ,qty in alltx:
2172:                 running.setdefault(cc,0.0)
2173:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2174:                 bal_after[txid]=running[cc]
2175:             for r in rows:
```
```text
2550:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2551:         load()
2552:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2553: 
2554:     def inventory_codes(self):
2555:         """Inventory Codes using the classic desktop inventory interface.
2556: 
2557:         This screen intentionally follows the uploaded Inventory Management
2558:         reference: a simple module title, compact New/Edit/Delete/Save/
2559:         Refresh/Print/Close action row, and a full-width editable data grid.
2560:         All records come from the V18 database, so existing inventory data is
2561:         preserved rather than recreated.
2562:         """
2563:         self.clearbody()
2564:         # Remove the generic SAP action row; this page owns its own classic
2565:         # action row just like the reference Inventory/Items screen.
2566:         if self.body.winfo_children():
2567:             try:
2568:                 self.body.winfo_children()[0].destroy()
2569:             except Exception:
2570:                 pass
```
```text
2623:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2624:         if filter_text:
2625:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2626:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2627: 
2628:         editing={"id":None,"new":False}
2629:         cell_editor={"widget":None}
2630: 
2631:         def close_editor(save_value=False):
2632:             w=cell_editor.get("widget")
2633:             if not w:
2634:                 return
2635:             try:
2636:                 if save_value:
2637:                     w.event_generate("<Return>")
2638:                 w.destroy()
2639:             except Exception:
2640:                 pass
2641:             cell_editor["widget"]=None
2642: 
2643:         def edit_cell(event=None):
```
```text
2653:             bbox=tree.bbox(iid,colid)
2654:             if not bbox: return
2655:             close_editor(False)
2656:             x,y,w,h=bbox
2657:             val=str(tree.item(iid,"values")[idx] or "")
2658:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2659:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2660:             cell_editor["widget"]=e
2661:             def commit(_=None):
2662:                 try:
2663:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2664:                 finally:
2665:                     try:e.destroy()
2666:                     except Exception:pass
2667:                     cell_editor["widget"]=None
2668:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2669:             e.bind("<FocusOut>",commit)
2670: 
2671:         def rows_query():
2672:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2673:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2675:             if tc: where.append("code <= ?"); params.append(tc)
2676:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2677:             if df or dt:
2678:                 sub=[]; sp=[]
2679:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2680:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2681:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2682:                 params.extend(sp)
2683:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2684:             return sql,params
2685: 
2686:         def load():
2687:             close_editor(False)
2688:             for i in tree.get_children(): tree.delete(i)
2689:             sql,params=rows_query()
2690:             count=0
2691:             for r in self.conn.execute(sql,params):
2692:                 # V18 stores UOM/opening and the original application may have
2693:                 # rate/remarks columns in some versions. Read them safely.
2694:                 rid,code,desc,uom,opening,rate,remarks=r
2695:                 bal=stock(self.conn,code)
```
```text
2709:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2710:             editing["id"]=None; editing["new"]=True
2711:             # Put the user directly into the Code cell.
2712:             try:
2713:                 bbox=tree.bbox(iid,"#2")
2714:                 if bbox:
2715:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2716:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2717:                     def commit(_=None):
2718:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2719:                         try:e.destroy()
2720:                         except Exception:pass
2721:                         cell_editor["widget"]=None
2722:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2723:             except Exception: pass
2724:             status.set("New row added — enter values, then press Save")
2725: 
2726:         def selected_row():
2727:             a=tree.selection()
2728:             return a[0] if a else None
2729: 
```
```text
2729: 
2730:         def edit_record():
2731:             iid=selected_row()
2732:             if not iid:
2733:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2734:             if not self.can_edit and not self.is_admin:
2735:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2736:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2737:             status.set("Edit mode — double-click any cell to change it, then press Save")
2738:             tree.focus(iid); tree.see(iid)
2739: 
2740:         def save_record():
2741:             iid=selected_row()
2742:             if not iid:
2743:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2744:             if not self.can_edit and not self.is_admin:
2745:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2746:             close_editor(True)
2747:             vals=list(tree.item(iid,"values"))
2748:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2749:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2747:             vals=list(tree.item(iid,"values"))
2748:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2749:             try: opening=float(str(vals[4]).strip() or 0)
2750:             except Exception: raise ValueError("Opening Qty must be a number.")
2751:             try: rate=float(str(vals[5]).strip() or 0)
2752:             except Exception: raise ValueError("Rate must be a number.")
2753:             remarks=str(vals[6]).strip()
2754:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2755:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2756:             if not desc:
2757:                 messagebox.showerror("Save","Description is required."); return
2758:             if opening<0:
2759:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2760:             rid=vals[0]
2761:             try:
2762:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2763:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2764:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2765:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2766:                 if rid:
2767:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2770:                                       (code,desc,uom,opening,rid))
2771:                     if oldcode!=code:
2772:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2773:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2774:                             except Exception:pass
2775:                 else:
2776:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2777:                                       (code,desc,uom,"",opening,0,"Local",0))
2778:                 self.conn.commit()
2779:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2780:                 backup_database(); load()
2781:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2782:             except Exception as ex:
2783:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2784: 
2785:         def delete_record():
2786:             iid=selected_row()
2787:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2788:             if not self.can_delete and not self.is_admin:
2789:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2790:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2786:             iid=selected_row()
2787:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2788:             if not self.can_delete and not self.is_admin:
2789:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2790:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2791:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2792:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2793:             try:
2794:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2795:             except Exception as ex:
2796:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2797: 
2798:         def refresh(): load()
2799:         def do_print():
2800:             try:self.preview_tree("Inventory Codes",tree)
2801:             except Exception as ex:messagebox.showerror("Print",str(ex))
2802:         def do_close(): self.dashboard()
2803: 
2804:         btn("New",new_record,8)
2805:         btn("Edit",edit_record,8)
2806:         btn("Delete",delete_record,8)
```
```text
2799:         def do_print():
2800:             try:self.preview_tree("Inventory Codes",tree)
2801:             except Exception as ex:messagebox.showerror("Print",str(ex))
2802:         def do_close(): self.dashboard()
2803: 
2804:         btn("New",new_record,8)
2805:         btn("Edit",edit_record,8)
2806:         btn("Delete",delete_record,8)
2807:         btn("Save",save_record,8)
2808:         btn("Refresh",refresh,9)
2809:         btn("Preview",do_print,8)
2810:         btn("Print",do_print,8)
2811:         btn("Close",do_close,8)
2812: 
2813:         # Search is deliberately small and sits on the right, without changing
2814:         # the reference layout of the action buttons.
2815:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2816:         search=tk.StringVar()
2817:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2818:         se.pack(side="left",padx=2)
2819:         self._item_master_search_entry=se
```
```text
2827:                     tree.detach(iid)
2828:         search.trace_add("write",filter_grid)
2829:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2830: 
2831:         tree.bind("<Double-1>",edit_cell)
2832:         tree.bind("<F2>",lambda e: edit_record())
2833:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2834:         self._page_actions={
2835:             "save":save_record,"edit":edit_record,"delete":delete_record,
2836:             "cancel":do_close,"print":do_print,"preview":do_print
2837:         }
2838:         load()
2839: 
2840:     def open_mto_inventory_flow(self):
2841:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2842: 
2843:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2844:         Cancel/X only closes the popup.
2845:         """
2846:         criteria = self._ask_mto_inventory_filters()
2847:         if not criteria or criteria.get("cancelled"):
```
```text
3009:                 return False
3010:             destination.set(found_dest)
3011:             edit_mode.update(on=True, original=r[0], dest=found_dest)
3012:             code.set(r[0])
3013:             desc.set(r[1] or "")
3014:             uom.set(r[2] or UOM_OPTIONS[0])
3015:             opening.set(str(r[3] if r[3] is not None else 0))
3016:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
3017:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
3018:             err.set("")
3019:             edit_btn.configure(text="SAVE EDIT")
3020:             ce.focus_set()
3021:             return True
3022: 
3023:         def check_duplicates(*_):
3024:             c = code.get().strip()
3025:             d = desc.get().strip()
3026:             dest = destination.get()
3027:             msgs = []
3028:             r = row_for(dest, c) if len(norm(c)) == 8 else None
3029:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
3031:             dh = desc_hit(dest, d) if d else None
3032:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
3033:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
3034:             hint.set("\n".join(msgs))
3035: 
3036:         code.trace_add("write", check_duplicates)
3037:         desc.trace_add("write", check_duplicates)
3038: 
3039:         def save_code():
3040:             try:
3041:                 c = code.get().strip()
3042:                 d = desc.get().strip()
3043:                 u = uom.get().strip()
3044:                 dest = destination.get()
3045:                 digits = norm(c)
3046:                 if len(digits) != 8:
3047:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3048:                 if not d:
3049:                     raise ValueError("Description is required.")
3050:                 try:
3051:                     op = float(opening.get().strip() or 0)
```
```text
3072:                         (c, d, u, op, iso, old)
3073:                     )
3074:                     action = "updated"
3075:                 else:
3076:                     self.conn.execute(
3077:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3078:                         (c, d, u, "", op, 0, iso)
3079:                     )
3080:                     action = "saved"
3081:                 self.conn.commit()
3082:                 backup_database()
3083:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3084:                 # Keep popup open for fast multiple entries.
3085:                 clear_form(keep_search=False)
3086:                 ce.focus_set()
3087:             except Exception as ex:
3088:                 self.conn.rollback()
3089:                 err.set(str(ex))
3090:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3091: 
3092:         def edit_action():
```
```text
3088:                 self.conn.rollback()
3089:                 err.set(str(ex))
3090:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3091: 
3092:         def edit_action():
3093:             if not edit_mode["on"]:
3094:                 load_for_edit()
3095:             else:
3096:                 save_code()
3097: 
3098:         def delete_code():
3099:             if not edit_mode["on"]:
3100:                 if not load_for_edit():
3101:                     return
3102:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3103:                 return
3104:             try:
3105:                 t = table_for(edit_mode["dest"])
3106:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3107:                 self.conn.commit()
3108:                 backup_database()
```
```text
3104:             try:
3105:                 t = table_for(edit_mode["dest"])
3106:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3107:                 self.conn.commit()
3108:                 backup_database()
3109:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3110:                 clear_form(keep_search=False)
3111:             except Exception as ex:
3112:                 self.conn.rollback()
3113:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3114: 
3115:         btns = ttk.Frame(box)
3116:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3117:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3118:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3119:         edit_btn.pack(side="left", padx=4, ipadx=8)
3120:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3121:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3122:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3123:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3124:         ce.focus_set()
```
```text
3118:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3119:         edit_btn.pack(side="left", padx=4, ipadx=8)
3120:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3121:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3122:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3123:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3124:         ce.focus_set()
3125: 
3126:     def _mto_new_item_dialog(self, on_saved):
3127:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3128:         brand-new item can be created without leaving that screen. Writes
3129:         straight into the same Item Master (items table) used everywhere."""
3130:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3131:         win.transient(self); win.grab_set()
3132:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3133:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3134:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3135:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3136:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3137:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3138:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3134:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3135:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3136:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3137:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3138:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3139:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3140:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3141:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3142:         def save():
3143:             try:
3144:                 c=code.get().strip(); d=desc.get().strip()
3145:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3146:                 if not d: raise ValueError("Description is required.")
3147:                 try:
3148:                     opening_val=float(opening.get() or 0)
3149:                 except ValueError:
3150:                     raise ValueError("Opening Qty must be a number.")
3151:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3152:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3153:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3154:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3147:                 try:
3148:                     opening_val=float(opening.get() or 0)
3149:                 except ValueError:
3150:                     raise ValueError("Opening Qty must be a number.")
3151:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3152:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3153:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3154:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3155:                 self.conn.commit(); backup_database()
3156:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3157:                 win.grab_release(); win.destroy()
3158:                 on_saved()
3159:             except Exception as ex: messagebox.showerror("Error",str(ex))
3160:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3161:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3162:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3163: 
3164:     def _item_filter_bar(self, parent, on_change):
3165:         """Item Code entry + item-master picker + Search/Show All. Calls
3166:         on_change() whenever the code changes or a button is pressed."""
3167:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3253:         self._item_master_find_callback=None
3254:         self._portable_print_context=None
3255:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3256:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3257:         }
3258: 
3259:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3260:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3261:         self.conn.commit()
3262: 
3263:         # ---- Same professional in-app window layout as Inventory Codes ----
3264:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3265:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3266:                   foreground=COLORS["primary_dark"]).pack(side="left")
3267:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3268: 
3269:         def open_find():
3270:             state_find={"index":-1}
3271:             def search_fn(text):
3272:                 text=text.strip().lower()
3273:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3360:             for i in table.get_children(): table.delete(i)
3361:             where=["1=1"]; params=[]
3362:             prefix=state.get("prefix",""); q=search.get().strip()
3363:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3364:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3365:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3366:             if fc: where.append("code >= ?"); params.append(fc)
3367:             if tc: where.append("code <= ?"); params.append(tc)
3368:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3369:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3370:             records=[]
3371:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3372:                 # If a date filter is supplied, accept an opening-date match OR
3373:                 # a transaction in that date range. This prevents valid MTO codes
3374:                 # from disappearing merely because an older record has no opening_date.
3375:                 if df or dt:
3376:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3377:                     if not ok:
3378:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3379:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3380:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3450:                 tr.insert("", "end", values=r)
3451:         def clear():
3452:             for x in v.values(): x.set("")
3453:             try: tr.selection_remove(tr.selection())
3454:             except Exception: pass
3455:             self._set_form_editable(party_form_roots, False)
3456:         def new_form():
3457:             clear(); self._set_form_editable(party_form_roots, True)
3458:         def save():
3459:             try:
3460:                 name=v["name"].get().strip()
3461:                 if not name: raise ValueError("Party Name is required.")
3462:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3463:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3464:             except Exception as ex: messagebox.showerror("Error",str(ex))
3465:         def load_party_row(a):
3466:             if not a:return
3467:             r=tr.item(a[0])["values"]
3468:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3469:             self._set_form_editable(party_form_roots, False)
3470:         def on_party_select(_=None):
```
```text
3476:             load_party_row(a)
3477:             self._set_form_editable(party_form_roots, True)
3478:         def delete_party():
3479:             a=tr.selection()
3480:             if not a:
3481:                 messagebox.showwarning("Delete", "Select a party first."); return
3482:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3483:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3484:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3485:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3486:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3487:         self._add_transaction_new_button(new_form)
3488:         load(); clear()
3489: 
3490:     def user_management(self):
3491:         self.clearbody()
3492:         if not self.is_admin:
3493:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3494:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3495:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3496:         role=tk.StringVar(value="User")
```
```text
3533:             u_ent.state(["!disabled"])
3534:         def edit():
3535:             a=tr.selection()
3536:             if not a:
3537:                 messagebox.showwarning("Edit User","Select a user row first."); return
3538:             r=tr.item(a[0])["values"]
3539:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3540:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3541:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3542:         def save():
3543:             try:
3544:                 username=v["username"].get().strip()
3545:                 if not username: raise ValueError("Username is required.")
3546:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3547:                 pw=v["password"].get()
3548:                 if exists:
3549:                     pw_hash = hash_password(pw) if pw else exists[0]
3550:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3551:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3552:                 else:
3553:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3548:                 if exists:
3549:                     pw_hash = hash_password(pw) if pw else exists[0]
3550:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3551:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3552:                 else:
3553:                     if not pw: raise ValueError("Password is required for a new user.")
3554:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3555:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3556:                 self.conn.commit(); backup_database(); load(); clear()
3557:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3558:             except Exception as ex:
3559:                 messagebox.showerror("Error", str(ex))
3560:         def delete_user():
3561:             a=tr.selection()
3562:             if not a:
3563:                 messagebox.showwarning("Delete User","Select a user row first."); return
3564:             username=tr.item(a[0])["values"][0]
3565:             if username==self.current_user:
3566:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3567:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3568:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3563:                 messagebox.showwarning("Delete User","Select a user row first."); return
3564:             username=tr.item(a[0])["values"][0]
3565:             if username==self.current_user:
3566:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3567:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3568:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3569:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3570:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3571:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3572:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3573:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3574:         load()
3575: 
3576:     @staticmethod
3577:     def _renumber_tree(tree, rows):
3578:         for i,iid in enumerate(tree.get_children()):
3579:             vals=list(tree.item(iid,"values"));
3580:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3581: 
3582:     def demand(self):
3583:         self.clearbody(); self.demand_lines=[]
```
```text
3580:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3581: 
3582:     def demand(self):
3583:         self.clearbody(); self.demand_lines=[]
3584:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3585:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3586:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3587:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3588:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3589:         # Demand Date is intentionally displayed as its own dedicated field.
3590:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3591:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3592:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3593:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3594:                 ("special","Special Instructions"),("source","Recommended Source")]
3595:         for i,(k,n) in enumerate(fields):
3596:             r=i//4*2+3; c=i%4*2
3597:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3598:             if k=="dept":
3599:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3600:             elif k=="urgency":
```
```text
3670:         def new_form():
3671:             self._editing_document_key=None
3672:             for z in v.values(): z.set("")
3673:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3674:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3675:             for iid in tree.get_children(): tree.delete(iid)
3676:             self._set_form_editable(form_roots, True, skip=[selector])
3677: 
3678:         def save():
3679:             try:
3680:                 no=v["no"].get().strip()
3681:                 if not no: raise ValueError("Demand No is required.")
3682:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3683:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3684:                 if dup and getattr(self,"_editing_document_key",None) != no:
3685:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3686:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3687:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3688:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3689:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3690:                 self.conn.commit()
```
```text
3683:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3684:                 if dup and getattr(self,"_editing_document_key",None) != no:
3685:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3686:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3687:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3688:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3689:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3690:                 self.conn.commit()
3691:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3692:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3693:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3694:             except Exception as ex: messagebox.showerror("Error",str(ex))
3695:         form_roots=[f,line,editbar]
3696:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3697:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3698:         def delete_current():
3699:             no=v["no"].get().strip()
3700:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3701:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3702:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3703:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3716:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3717:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3718:                     f"Justification: {v['just'].get()}",
3719:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3720:             if not self.demand_lines:
3721:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3722:             self.show_preview_window("Purchase Demand", header,
3723:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3724:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3725:         def edit_saved_demand():
3726:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3727:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3728:             self._set_form_editable(form_roots, True, skip=[selector])
3729:         def print_now():
3730:             if not self.demand_lines:
3731:                 messagebox.showwarning("Print","Add at least one item line first."); return
3732:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3733:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3734:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3735:                     f"Justification: {v['just'].get()}",
3736:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3732:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3733:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3734:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3735:                     f"Justification: {v['just'].get()}",
3736:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3737:             self._open_direct_printer("Purchase Demand",header,
3738:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3739:                 self.demand_lines,A4)
3740:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3741:         self._add_transaction_new_button(new_form)
3742:         self._set_form_editable(form_roots, False, skip=[selector])
3743:         try:
3744:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3745:         except Exception: pass
3746:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3747: 
3748:     def load_demand_into_form(self,no,v,tree):
3749:         v["no"].set(no)
3750:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3751:         if not r:return
3752:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3754:         self.demand_lines=[]
3755:         for i in tree.get_children():tree.delete(i)
3756:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3757:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3758:         roots=getattr(self,"_transaction_form_roots",None)
3759:         if roots and "demand" in roots:
3760:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3761: 
3762:     def refresh_saved_cache(self,typ):
3763:         # Refresh saved-document dropdowns immediately after a successful save.
3764:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3765:         alive=[]
3766:         for combo, refresh in refreshers:
3767:             try:
3768:                 if combo.winfo_exists():
3769:                     refresh()
3770:                     alive.append((combo, refresh))
3771:             except Exception:
3772:                 pass
3773:         if hasattr(self, "_document_selector_refreshers"):
3774:             self._document_selector_refreshers[typ] = alive
```
```text
3773:         if hasattr(self, "_document_selector_refreshers"):
3774:             self._document_selector_refreshers[typ] = alive
3775: 
3776:     def grr(self):
3777:         self.clearbody(); self.grr_lines=[]
3778:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3779:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3780:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3781:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3782:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3783:         for i,(k,n) in enumerate(fields):
3784:             r=i//4*2+2;c=i%4*2
3785:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3786:             if k=="department":
3787:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3788:             elif k=="supplier":
3789:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3790:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3791:             elif k=="date":
3792:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3793:             else:
```
```text
3842:         def new_form():
3843:             self._editing_document_key=None
3844:             for z in v.values(): z.set("")
3845:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3846:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3847:             for iid in tree.get_children(): tree.delete(iid)
3848:             self._set_form_editable(form_roots, True, skip=[selector])
3849: 
3850:         def save():
3851:             try:
3852:                 no=v["no"].get().strip()
3853:                 if not no:raise ValueError("GRN No is required.")
3854:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3855:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3856:                 if dup and getattr(self,"_editing_document_key",None) != no:
3857:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3858:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3859:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3860:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3861:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3862:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3859:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3860:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3861:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3862:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3863:                 for x in self.grr_lines:
3864:                     ltype=x[10] if len(x)>10 else "Local"
3865:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3866:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3867:                 self.conn.commit()
3868:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
3869:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
3870:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3871:             except Exception as ex:messagebox.showerror("Error",str(ex))
3872:         form_roots=[f,line,editbar]
3873:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3874:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3875:         def delete_current():
3876:             no=v["no"].get().strip()
3877:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3878:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3879:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
3872:         form_roots=[f,line,editbar]
3873:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3874:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3875:         def delete_current():
3876:             no=v["no"].get().strip()
3877:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3878:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3879:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3880:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3881:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3882:         def cancel_form():
3883:             self._editing_document_key=None
3884:             self._set_form_editable(form_roots, False, skip=[selector])
3885:             for z in v.values(): z.set("")
3886:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3887:             itype.set("Local")
3888:             self.grr_lines.clear()
3889:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3890:             for iid in tree.get_children(): tree.delete(iid)
3891:         def preview_now():
3892:             if not self.grr_lines:
```
```text
3901:                     ("Challan #", v['challan'].get()),
3902:                     ("Vehicle #", v['vehicle'].get()),
3903:                     ("Bill/Voucher #", v['bill'].get()),
3904:                     ("Reference", v['ref'].get()),
3905:                     ("Remarks", v['remarks'].get()),
3906:                     ("Total Value", fmt_num(total))]
3907:             self.show_preview_window("GRN Receipt", header,
3908:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3909:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3910:         def portable_current():
3911:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3912:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3913:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3914:         self._portable_print_context=portable_current
3915:         def edit_saved_grr():
3916:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3917:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
3918:             self._set_form_editable(form_roots, True, skip=[selector])
3919:         def print_now():
3920:             if not self.grr_lines:
3921:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
3925:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
3926:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
3927:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
3928:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
3929:                     ("Total Value", fmt_num(total))]
3930:             self._open_direct_printer("GRN Receipt",header,
3931:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3932:                 self.grr_lines,landscape(A4))
3933:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3934:         self._add_transaction_new_button(new_form)
3935:         self._set_form_editable(form_roots, False, skip=[selector])
3936:         try:
3937:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3938:         except Exception: pass
3939:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
3940: 
3941:     def load_grr_into_form(self,no,v,tree):
3942:         v["no"].set(no)
3943:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
3944:         if not r:return
3945:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
3952:         if roots and "grr" in roots:
3953:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
3954: 
3955:     def issue(self):
3956:         self.clearbody(); self.issue_lines=[]
3957:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
3958:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
3959:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3960:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
3961:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
3962:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
3963:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3964:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3965:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
3966:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
3967:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
3968:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
3969:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
3970:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
3971:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
3972:         itype=tk.StringVar(value="Local")
```
```text
4041:                 # Editing an existing issue replaces its old stock transaction and detail lines.
4042:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
4043:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
4044:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
4045:                 for x in self.issue_lines:
4046:                     ltype=x[7] if len(x)>7 else "Local"
4047:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
4048:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
4049:                 self.conn.commit()
4050:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
4051:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
4052:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4053:             except Exception as ex:messagebox.showerror("Error",str(ex))
4054:         def delete_current():
4055:             no=v["no"].get().strip()
4056:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
4057:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
4058:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
4059:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
4060:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
4061:         def cancel_form():
```
```text
4069:             for iid in tree.get_children(): tree.delete(iid)
4070:         def preview_now():
4071:             if not self.issue_lines:
4072:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4073:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4074:                     f"Items Use For: {v['items_use_for'].get()}"]
4075:             self.show_preview_window("Material Issue", header,
4076:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4077:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4078:         def portable_current():
4079:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4080:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4081:         self._portable_print_context=portable_current
4082:         form_roots=[f,usebar,line,editbar]
4083:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4084:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4085:         def load_saved_issue(no):
4086:             self.load_issue_into_form(no,v,tree)
4087:             self._set_form_editable(form_roots, False, skip=[selector])
4088:         def edit_saved_issue():
4089:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4082:         form_roots=[f,usebar,line,editbar]
4083:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4084:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4085:         def load_saved_issue(no):
4086:             self.load_issue_into_form(no,v,tree)
4087:             self._set_form_editable(form_roots, False, skip=[selector])
4088:         def edit_saved_issue():
4089:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4090:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4091:             self._set_form_editable(form_roots, True, skip=[selector])
4092:         def print_issue_now():
4093:             if not self.issue_lines:
4094:                 messagebox.showwarning("Print","Add at least one item line first."); return
4095:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4096:             self._open_direct_printer("Material Issue",header,
4097:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4098:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4099:         self._add_transaction_new_button(new_form)
4100:         self._set_form_editable(form_roots, False, skip=[selector])
4101:         self._active_form_loader = load_saved_issue
4102: 
```
```text
4110:         for i in tree.get_children():tree.delete(i)
4111:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4112:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4113:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4114:         roots=getattr(self,"_transaction_form_roots",None)
4115:         if roots and "issue" in roots:
4116:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4117: 
4118:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4119:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4120: 
4121:         The layout intentionally matches Inventory Codes' Selection Criteria
4122:         popup so all Report sub-sections have one consistent desktop workflow.
4123:         """
4124:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4125:         win=tk.Toplevel(self)
4126:         win.title(f"{report_title} - Selection Criteria")
4127:         win.resizable(False,False)
4128:         win.transient(self); win.grab_set()
4129:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4130:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4175:             except Exception: pass
4176:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4177:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4178:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4179:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4180:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4181:         e1.focus_set(); self.wait_window(win); return result
4182: 
4183:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4184:         self._pending_report_filters=criteria
4185:         try:
4186:             return self.open_menu_window(method,title,geometry)
4187:         finally:
4188:             self._pending_report_filters=None
4189: 
4190:     def open_stock_balance_report_flow(self):
4191:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4192:         if f.get("cancelled"): return None
4193:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4194: 
4195:     def open_grr_report_flow(self):
```
```text
4188:             self._pending_report_filters=None
4189: 
4190:     def open_stock_balance_report_flow(self):
4191:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4192:         if f.get("cancelled"): return None
4193:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4194: 
4195:     def open_grr_report_flow(self):
4196:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4197:         if f.get("cancelled"): return None
4198:         return self._open_report_child(self.report_grr,"GRN Report",f)
4199: 
4200:     def open_demand_report_flow(self):
4201:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4202:         if f.get("cancelled"): return None
4203:         return self._open_report_child(self.report_demand,"Demand Report",f)
4204: 
4205:     def open_issue_report_flow(self):
4206:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4207:         if f.get("cancelled"): return None
4208:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4202:         if f.get("cancelled"): return None
4203:         return self._open_report_child(self.report_demand,"Demand Report",f)
4204: 
4205:     def open_issue_report_flow(self):
4206:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4207:         if f.get("cancelled"): return None
4208:         return self._open_report_child(self.report_issue,"Issue Report",f)
4209: 
4210:     def open_party_report_flow(self):
4211:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4212:         if f.get("cancelled"): return None
4213:         return self._open_report_child(self.report_party,"Party Report",f)
4214: 
4215:     def _ask_stock_balance_filters(self):
4216:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4217:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4218:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4219:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4220:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4221:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4222:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4234:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4235:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4236:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4237:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4238:         e1.focus_set();self.wait_window(win);return result
4239: 
4240:     def stock_balance(self):
4241:         self.clearbody()
4242:         # Stock Balance is a Report sub-section and does not use the generic
4243:         # Save/Edit/Delete/Cancel/Print action strip.
4244:         children=self.body.winfo_children()
4245:         if children:
4246:             children[0].destroy()
4247:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4248:         if initial.get("cancelled"):
4249:             self.dashboard(); return
4250:         top=ttk.Frame(self.body);top.pack(fill="x")
4251:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4252:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4253:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4254:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4264:             for typ,qty in self.conn.execute(q,params):
4265:                 if typ=="GRR":gr+=float(qty or 0)
4266:                 elif typ=="ISSUE":iss+=float(qty or 0)
4267:             return opening_before,gr,iss,opening_before+gr-iss
4268:         def header_summary():
4269:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4270:         def load():
4271:             for i in tr.get_children():tr.delete(i)
4272:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4273:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4274:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4275:             sql+=" ORDER BY code"
4276:             for r in self.conn.execute(sql,params):
4277:                 op,gr,iss,cur=period(r[0],r[3])
4278:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4279:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4280:         def reopen_filters():
4281:             initial2=self._ask_stock_balance_filters()
4282:             if initial2.get("cancelled"):return
4283:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4284:             load()
```
```text
4322:         """
4323:         if typ=="demand": self.demand()
4324:         elif typ=="grr": self.grr()
4325:         else: self.issue()
4326:         loader=getattr(self,"_active_form_loader",None)
4327:         if loader: loader(str(no))
4328: 
4329:     def _edit_from_selector(self, typ, var, loader):
4330:         """Top Edit action: load the saved document directly into the current form.
4331:         If nothing is selected, use the newest saved document; never open a popup.
4332:         """
4333:         text=var.get().strip()
4334:         if text:
4335:             no=text.split(" -> ",1)[0].strip()
4336:         else:
4337:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4338:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4339:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4340:             if not r:
4341:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4342:                 return
```
```text
4339:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4340:             if not r:
4341:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4342:                 return
4343:             no=str(r[0])
4344:             var.set(no)
4345:         loader(no)
4346: 
4347:     def show_saved_records(self,typ):
4348:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4349:         if typ=="demand":
4350:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4351:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4352:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4353:             for r in rows:
4354:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4355:                 r=list(r); r[1]=to_display_date(r[1])
4356:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4357:         elif typ=="grr":
4358:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4359:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4370:         def view():
4371:             a=tr.selection()
4372:             if not a:return
4373:             no=tr.item(a[0])["values"][0]
4374:             win.destroy();self.open_document_editor(typ,no)
4375:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4376:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4377:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4378:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4379: 
4380:     def documents(self):
4381:         self.clearbody()
4382:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4383:         specs=[
4384:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4385:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4386:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4387:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4388:             ("Material Issues","issue",("No","Date","Department"),
4389:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4390:         ]
```
```text
4386:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4387:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4388:             ("Material Issues","issue",("No","Date","Department"),
4389:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4390:         ]
4391:         for title,typ,cols,query in specs:
4392:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4393:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4394:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4395:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4396:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4397:             for r in self.conn.execute(query):
4398:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4399:             def edit_selected(t=tr,k=typ):
4400:                 a=t.selection()
4401:                 if not a:
4402:                     messagebox.showwarning("Edit", "Select a saved record first.")
4403:                     return
4404:                 no=t.item(a[0])["values"][0]
4405:                 self.open_document_editor(k,no)
4406:             def delete_selected(t=tr,k=typ):
```
```text
4401:                 if not a:
4402:                     messagebox.showwarning("Edit", "Select a saved record first.")
4403:                     return
4404:                 no=t.item(a[0])["values"][0]
4405:                 self.open_document_editor(k,no)
4406:             def delete_selected(t=tr,k=typ):
4407:                 a=t.selection()
4408:                 if not a:
4409:                     messagebox.showwarning("Delete", "Select a saved record first.")
4410:                     return
4411:                 no=t.item(a[0])["values"][0]
4412:                 if k=="demand":
4413:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4414:                 elif k=="grr":
4415:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4416:                 else:
4417:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4418:                 self.conn.commit();backup_database();self.documents()
4419:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4420:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4421:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4415:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4416:                 else:
4417:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4418:                 self.conn.commit();backup_database();self.documents()
4419:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4420:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4421:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4422:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4423:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4424:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4425:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4426: 
4427:     def doc_export_selected(self,typ,tr,fmt):
4428:         a=tr.selection()
4429:         if not a:
4430:             messagebox.showwarning("Export","Select a saved record first."); return
4431:         no=tr.item(a[0])["values"][0]
4432:         if fmt=="word": self.export_word(typ,no)
4433:         else: self.export_excel(typ,no)
4434: 
4435:     def doc_preview_selected(self,typ,tr):
```
```text
4430:             messagebox.showwarning("Export","Select a saved record first."); return
4431:         no=tr.item(a[0])["values"][0]
4432:         if fmt=="word": self.export_word(typ,no)
4433:         else: self.export_excel(typ,no)
4434: 
4435:     def doc_preview_selected(self,typ,tr):
4436:         a=tr.selection()
4437:         if not a:
4438:             messagebox.showwarning("Preview","Select a saved record first."); return
4439:         no=tr.item(a[0])["values"][0]
4440:         data=self._get_doc_data(typ,no)
4441:         if not data:
4442:             messagebox.showwarning("Preview","Document not found."); return
4443:         title,header,cols,rows=data
4444:         header_lines=header
4445:         self.show_preview_window(title,header_lines,cols,rows)
4446: 
4447:     def doc_print_selected(self,typ,tr):
4448:         a=tr.selection()
4449:         if not a: return
4450:         no=tr.item(a[0])["values"][0]
```
```text
4481:         def _print_loaded_document():
4482:             data=self._get_doc_data(typ,no)
4483:             if not data:
4484:                 messagebox.showwarning("Document","Document not found."); return
4485:             title,header,cols,rows=data
4486:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4487:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4488: 
4489:     def _report_filter_popup(self, title, include_party=False):
4490:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4491:         win,winbody=self._internal_window(title,"520x420")
4492:         done=tk.BooleanVar(value=False)
4493:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4494:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4495:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4496:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4497:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4498:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4499:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4500:         if include_party:
4501:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4495:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4496:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4497:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4498:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4499:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4500:         if include_party:
4501:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4502:         def ok():
4503:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4504:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4505:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4506:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4507: 
4508:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4509:         self.clearbody()
4510:         # Report sub-sections use their own report toolbar; remove only the
4511:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4512:         children=self.body.winfo_children()
4513:         if children:
4514:             children[0].destroy()
4515:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4516:         if f.get("cancelled"):
4517:             self.dashboard();return
4518:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4519:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4520:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4521:         def load():
4522:             for i in tr.get_children():tr.delete(i)
4523:             params,where=params_builder(f)
4524:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4525:             for r in self.conn.execute(sql,params):
4526:                 vals=list(r)
4527:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4528:                 tr.insert("","end",values=vals)
4529:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4530:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4531:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4532:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4533:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4534:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4535:         def open_find_report():
4536:             state_find={"index":-1}
```
```text
4542:                 order=children[start:]+children[:start]
4543:                 for iid in order:
4544:                     vals=tr.item(iid,"values")
4545:                     if any(text in str(v).lower() for v in vals):
4546:                         state_find["index"]=children.index(iid)
4547:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4548:                 return False
4549:             self._open_exact_find_text_popup(search_fn)
4550:         self._item_master_find_callback=open_find_report
4551:         load()
4552:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4553: 
4554:     def report_grr(self):
4555:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4556:         def pb(f):
4557:             w=[];p=[]
4558:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4559:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4560:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4561:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4562:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4557:             w=[];p=[]
4558:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4559:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4560:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4561:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4562:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4563:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4564:             return p,w
4565:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4566: 
4567:     def report_demand(self):
4568:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4569:         def pb(f):
4570:             w=[];p=[]
4571:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4572:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4573:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4574:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4575:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4576:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4577:             return p,w
```
```text
4570:             w=[];p=[]
4571:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4572:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4573:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4574:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4575:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4576:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4577:             return p,w
4578:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4579: 
4580:     def report_issue(self):
4581:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4582:         def pb(f):
4583:             w=[];p=[]
4584:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4585:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4586:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4587:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4588:             return p,w
4589:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4590: 
```
```text
4583:             w=[];p=[]
4584:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4585:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4586:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4587:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4588:             return p,w
4589:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4590: 
4591:     def report_party(self):
4592:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4593:         def pb(f):
4594:             w=[];p=[]
4595:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4596:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4597:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4598:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4599:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4600:             return p,w
4601:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4602: 
4603:     def reports(self):
```
```text
4601:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4602: 
4603:     def reports(self):
4604:         self.clearbody()
4605:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4606: 
4607:         # ================= GRN Details =================
4608:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4609:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4610:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4611:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4612:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4613:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4614: 
4615:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4616:         def load_grr_item(codev=None):
4617:             for i in tr.get_children(): tr.delete(i)
4618:             q=codev.get().strip() if codev else ""
4619:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4620:             for r in self.conn.execute(sql,(q,) if q else ()):
4621:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4627:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4628:         tr=self.make_tree(fr,grr_cols,grr_widths)
4629:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4630:             for i in tr.get_children(): tr.delete(i)
4631:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4632:             conds=[];params=[]
4633:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4634:             if td: conds.append("g.grr_date<=?");params.append(td)
4635:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4636:             for r in self.conn.execute(sql,params):
4637:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4638:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4639:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4640:         load_grr_date(fdv,tdv)
4641: 
4642:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4643:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4644:         party=tk.StringVar(value="ALL")
4645:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4646:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4647:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4643:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4644:         party=tk.StringVar(value="ALL")
4645:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4646:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4647:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4648:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4649:         def load_party(*_):
4650:             for i in tr.get_children(): tr.delete(i)
4651:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4652:             if party.get()=="ALL":
4653:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4654:             else:
4655:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4656:             for r in rows:
4657:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4658:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4659:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4660: 
4661:         # ================= Demand Details =================
4662:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4663:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4659:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4660: 
4661:         # ================= Demand Details =================
4662:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4663:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4664:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4665:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4666:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4667:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4668: 
4669:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4670:         def load_dem_item(codev=None):
4671:             for i in tr.get_children(): tr.delete(i)
4672:             q=codev.get().strip() if codev else ""
4673:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4674:             for r in self.conn.execute(sql,(q,) if q else ()):
4675:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4676:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4677:         tr=self.make_tree(fr,dem_cols,dem_widths)
4678:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4679:         load_dem_item(codev)
```
```text
4681:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4682:         tr=self.make_tree(fr,dem_cols,dem_widths)
4683:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4684:             for i in tr.get_children(): tr.delete(i)
4685:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4686:             conds=[];params=[]
4687:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4688:             if td: conds.append("d.demand_date<=?");params.append(td)
4689:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4690:             for r in self.conn.execute(sql,params):
4691:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4692:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4693:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4694:         load_dem_date(fdv,tdv)
4695: 
4696:         # ================= Material Issue Details =================
4697:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4698:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4699:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4700:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4701:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4694:         load_dem_date(fdv,tdv)
4695: 
4696:         # ================= Material Issue Details =================
4697:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4698:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4699:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4700:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4701:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4702:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4703: 
4704:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4705:         def load_iss_item(codev=None):
4706:             for i in tr.get_children(): tr.delete(i)
4707:             q=codev.get().strip() if codev else ""
4708:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4709:             for r in self.conn.execute(sql,(q,) if q else ()):
4710:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4711:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4712:         tr=self.make_tree(fr,iss_cols,iss_widths)
4713:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4714:         load_iss_item(codev)
```
```text
4716:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4717:         tr=self.make_tree(fr,iss_cols,iss_widths)
4718:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4719:             for i in tr.get_children(): tr.delete(i)
4720:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4721:             conds=[];params=[]
4722:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4723:             if td: conds.append("i.issue_date<=?");params.append(td)
4724:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4725:             for r in self.conn.execute(sql,params):
4726:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4727:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4728:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4729:         load_iss_date(fdv,tdv)
4730: 
4731:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4732: 
4733:     def print_item_master(self):
4734:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4735:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4736: 
```
```text
4733:     def print_item_master(self):
4734:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4735:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4736: 
4737:     def print_party_master(self):
4738:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4739:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4740: 
4741:     def print_report(self,kind):
4742:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4743:         if kind=="grr":
4744:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4745:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4746:         elif kind=="demand":
4747:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4748:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4749:         elif kind=="issue":
4750:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4751:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4752:         else:
4753:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4754:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4755:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4756: 
4757:     def print_stock(self):
4758:         rows=[]
4759:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4760:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4761:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4762:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4763: 
4764:     def print_ledger(self):
4765:         rows=[]
4766:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4767:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4768:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4769:                 running += x[3] if x[1]=="GRR" else -x[3]
4770:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4771:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4772: 
4773:     def _get_doc_data(self, typ, no):
4774:         """Header + line items for one saved document, used by the on-screen
```
```text
4840:             sig=doc.add_table(rows=2,cols=3)
4841:             labels=["Prepared By","Store Keeper","Store Incharge"]
4842:             for i,label in enumerate(labels):
4843:                 sig.cell(0,i).text="____________________"
4844:                 sig.cell(1,i).text=label
4845:                 for para in sig.cell(1,i).paragraphs:
4846:                     for run in para.runs: run.bold=True
4847:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4848:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4849:         doc.save(path)
4850:         self.open_file(path)
4851: 
4852:     def export_excel(self, typ, no):
4853:         if not no or not no.strip():
4854:             return messagebox.showwarning("Excel Export","Select a document first.")
4855:         if not XLSX_AVAILABLE:
4856:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4857:         data=self._get_doc_data(typ,no)
4858:         if not data:
4859:             return messagebox.showwarning("Excel Export","Document not found.")
4860:         title,header,cols,rows=data
```
```text
4882:             for col in range(1,4):
4883:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4884:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4885:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4886:         for col_cells in ws.columns:
4887:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4888:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4889:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4890:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4891:         wb.save(path)
4892:         self.open_file(path)
4893: 
4894:     def preview_pdf(self,typ,no):
4895:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4896:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4897:         data=self._get_doc_data(typ,no)
4898:         if not data:return messagebox.showwarning("Document","Document not found.")
4899:         title,header,cols,rows=data
4900:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4901:         page_size = landscape(A4) if typ == "grr" else A4
4902:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4897:         data=self._get_doc_data(typ,no)
4898:         if not data:return messagebox.showwarning("Document","Document not found.")
4899:         title,header,cols,rows=data
4900:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4901:         page_size = landscape(A4) if typ == "grr" else A4
4902:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4903: 
4904:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4905:         """Open the print dialog with a real visual preview of the exact report.
4906: 
4907:         The report is rendered to a temporary PDF only in memory/on disk for the
4908:         duration of printing.  It is deleted after the print dialog closes, so
4909:         the Print button does not leave a PDF report behind.  Printing uses the
4910:         rendered report page itself rather than rebuilding rows as plain text;
4911:         this keeps the printed page identical to the application's report.
4912:         """
4913:         # Printing is always prepared as an A4 landscape page. This only affects
4914:         # the print path; the rest of the application's UI/report logic is unchanged.
4915:         page_size = landscape(A4)
4916:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
4917:             messagebox.showwarning(
```
```text
4919:                 "The print preview/printing components are not available.\n\n"
4920:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
4921:             )
4922:             return
4923:         if not rows and not columns:
4924:             messagebox.showwarning("Print", "There is no data to print.")
4925:             return
4926:         try:
4927:             os.makedirs(REPORTS_DIR, exist_ok=True)
4928:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
4929:             self._pdf_table_report(key,title,columns,rows,page_size,
4930:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
4931:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
4932:             self._select_windows_printer_for_pdf(key)
4933:         except Exception as e:
4934:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
4935: 
4936:     def _select_windows_printer_for_pdf(self, path):
4937:         """Print dialog with an actual page preview, printer selection and direct GDI output.
4938: 
4939:         The preview is rendered from the exact PDF produced by the application,
```
```text
4969:         job=getattr(self, "_print_jobs", {}).get(path)
4970:         if job:
4971:             title, header_lines, columns, rows, source_page_size = job
4972:         else:
4973:             title=os.path.splitext(os.path.basename(path))[0]
4974:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
4975: 
4976:         try:
4977:             doc=fitz.open(path)
4978:             total_pages=max(1,doc.page_count)
4979:         except Exception as e:
4980:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
4981:             return
4982: 
4983:         win=tk.Toplevel(self)
4984:         win.title("Printing from Win32 application - Print")
4985:         win.geometry("900x620")
4986:         win.minsize(850,580)
4987:         win.transient(self)
4988:         win.configure(bg="#f0f0f0")
4989: 
```
```text
4995:             pass
4996: 
4997:         outer=tk.Frame(win,bg="#f0f0f0")
4998:         outer.pack(fill="both",expand=True)
4999:         outer.columnconfigure(1,weight=1)
5000:         outer.rowconfigure(0,weight=1)
5001: 
5002:         # Left side mirrors the familiar system printer dialog: printers and
5003:         # print options. Right side contains the actual report page preview.
5004:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
5005:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
5006:         left.grid_propagate(False)
5007:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
5008:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
5009:         printer_list.pack(fill="x")
5010:         for pr in printers: printer_list.insert("end",pr)
5011:         try: printer_list.selection_set(printers.index(default_printer))
5012:         except Exception: printer_list.selection_set(0)
5013: 
5014:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
5015:         copies=tk.IntVar(value=1)
```
```text
5088:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5089: 
5090:         bottom=tk.Frame(win,bg="#f0f0f0")
5091:         # `outer` already uses pack() in `win`; using grid() for another direct
5092:         # child of the same toplevel raises TclError. Keep the action bar in the
5093:         # same geometry-manager family so Print/Cancel are always visible.
5094:         bottom.pack(fill="x",padx=12,pady=(0,12))
5095:         bottom.columnconfigure(0,weight=1)
5096:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5097:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5098:         print_btn=ttk.Button(bottom,text="Print",width=12)
5099:         print_btn.grid(row=0,column=2,padx=(8,0))
5100: 
5101:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5102: 
5103:         def parse_page_selection(total):
5104:             if pages_mode.get()=="All pages": return list(range(total))
5105:             raw=page_range.get().strip()
5106:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5107:             selected=[]
5108:             for part in raw.split(","):
```
```text
5105:             raw=page_range.get().strip()
5106:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5107:             selected=[]
5108:             for part in raw.split(","):
5109:                 part=part.strip()
5110:                 if "-" in part:
5111:                     a,b=part.split("-",1); a=int(a); b=int(b)
5112:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5113:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5114:                     selected.extend(range(a-1,b))
5115:                 else:
5116:                     n=int(part)
5117:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5118:                     selected.append(n-1)
5119:             return list(dict.fromkeys(selected))
5120: 
5121:         def selected_printer():
5122:             sel=printer_list.curselection()
5123:             return printer_list.get(sel[0]) if sel else printers[0]
5124: 
5125:         def print_rendered_pages():
```
```text
5218:                 finally:
5219:                     if hprinter is not None:
5220:                         try: win32print.ClosePrinter(hprinter)
5221:                         except Exception: pass
5222:                     if hdc:
5223:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5224:                         except Exception: pass
5225: 
5226:                 # Print the exact rendered PDF page through the printer DC.
5227:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5228:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5229:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5230:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5231: 
5232:                 for copy_no in range(count):
5233:                     dc.StartDoc(str(title)[:80])
5234:                     doc_ok=False
5235:                     try:
5236:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5237:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5238:                             dc.StartPage()
```
```text
5237:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5238:                             dc.StartPage()
5239:                             page_ok=False
5240:                             try:
5241:                                 cell_w=printable_w/float(cols_n)
5242:                                 cell_h=printable_h/float(rows_n)
5243:                                 for j,page_index in enumerate(batch):
5244:                                     page=doc.load_page(page_index)
5245:                                     pdf_w=max(1.0,float(page.rect.width))
5246:                                     pdf_h=max(1.0,float(page.rect.height))
5247:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5248:                                     fit=max(0.25,min(fit,8.0))
5249:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5250:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5251:                                     target_w=max(1,int(cell_w*0.96))
5252:                                     target_h=max(1,int(cell_h*0.96))
5253:                                     ratio=min(target_w/img.width,target_h/img.height)
5254:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5255:                                     if (nw,nh)!=(img.width,img.height):
5256:                                         img=img.resize((nw,nh),Image.LANCZOS)
5257:                                     dib=ImageWin.Dib(img)
```
```text
5277: 
5278:                 status.set("Print job sent successfully")
5279:                 win.update_idletasks()
5280:                 win.after(500,close)
5281:             except Exception as e:
5282:                 status.set("Print failed: "+str(e))
5283:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5284: 
5285:         def close():
5286:             try: doc.close()
5287:             except Exception: pass
5288:             try: win.destroy()
5289:             except Exception: pass
5290:             # Only the temporary PDF created by the Print button is removed.
5291:             # Existing report PDFs passed through the legacy print path are preserved.
5292:             try:
5293:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5294:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5295:             except Exception: pass
5296: 
5297:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5293:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5294:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5295:             except Exception: pass
5296: 
5297:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5298:         bottom.winfo_children()[1].configure(command=close)
5299:         print_btn.configure(command=print_rendered_pages)
5300:         win.protocol("WM_DELETE_WINDOW",close)
5301:         win.bind("<Escape>",lambda e:close())
5302:         win.grab_set()
5303:         # Keep the requested printer defaults visibly selected; no manual
5304:         # adjustment is required before pressing Print.
5305:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5306:         win.after(120,lambda:render_preview(0))
5307:         win.focus_force()
5308: 
5309:     def print_pdf(self,path):
5310:         """Open a printer-selection window for a generated PDF."""
5311:         path=os.path.abspath(path)
5312:         if not os.path.exists(path):
5313:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5309:     def print_pdf(self,path):
5310:         """Open a printer-selection window for a generated PDF."""
5311:         path=os.path.abspath(path)
5312:         if not os.path.exists(path):
5313:             messagebox.showwarning("Print", "The report file could not be found.")
5314:             return
5315: 
5316:         if sys.platform.startswith("win"):
5317:             self._select_windows_printer_for_pdf(path)
5318:             return
5319: 
5320:         try:
5321:             subprocess.run(["lp", path], check=True)
5322:         except Exception as e:
5323:             messagebox.showwarning(
5324:                 "Print",
5325:                 "The operating system could not start printing.\n\n"
5326:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5327:             )
5328: 
5329:     def open_file(self,path):
```
```text
5324:                 "Print",
5325:                 "The operating system could not start printing.\n\n"
5326:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5327:             )
5328: 
5329:     def open_file(self,path):
5330:         try:
5331:             if sys.platform.startswith("win"): os.startfile(path)
5332:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5333:             else: subprocess.Popen(["xdg-open",path])
5334:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5335: 
5336:     def print_demand(self,no):
5337:         data=self._get_doc_data("demand",no)
5338:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5339:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5340:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5341:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5342: 
5343:     def print_grr(self,no):
5344:         data=self._get_doc_data("grr",no)
```
```text
5338:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5339:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5340:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5341:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5342: 
5343:     def print_grr(self,no):
5344:         data=self._get_doc_data("grr",no)
5345:         if not data:return messagebox.showwarning("Document","GRN not found.")
5346:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5347:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5348:         # GRN has a wide item table. Generate the PDF itself in landscape so
5349:         # the printer dialog and printer driver receive a landscape document
5350:         # instead of a portrait page with rotated/cropped content.
5351:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5352: 
5353:     def print_issue(self,no):
5354:         data=self._get_doc_data("issue",no)
5355:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5356:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5357:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5358:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
```

## updater.py

- Lines: 202
- AST parse error: unexpected character after line continuation character (<unknown>, line 1)

### Relevant source locations

```text
0033:         parts.append(0)
0034:     return tuple(parts[:4])
0035: 
0036: 
0037: def _load_config():
0038:     path = os.path.join(_app_dir(), CONFIG_NAME)
0039:     if not os.path.exists(path):
0040:         return {}
0041:     with open(path, "r", encoding="utf-8") as f:
0042:         return json.load(f)
0043: 
0044: 
0045: def _download(url, destination):
0046:     req = urllib.request.Request(url, headers={"User-Agent": "StoreInventoryManagement-Updater"})
0047:     with urllib.request.urlopen(req, timeout=30) as response, open(destination, "wb") as out:
0048:         while True:
0049:             chunk = response.read(1024 * 1024)
0050:             if not chunk:
0051:                 break
0052:             out.write(chunk)
0053: 
```
```text
0049:             chunk = response.read(1024 * 1024)
0050:             if not chunk:
0051:                 break
0052:             out.write(chunk)
0053: 
0054: 
0055: def _sha256(path):
0056:     h = hashlib.sha256()
0057:     with open(path, "rb") as f:
0058:         for chunk in iter(lambda: f.read(1024 * 1024), b""):
0059:             h.update(chunk)
0060:     return h.hexdigest().lower()
0061: 
0062: 
0063: def _install_after_exit(new_exe, current_exe):
0064:     app_dir = os.path.dirname(current_exe)
0065:     script = os.path.join(app_dir, ".store_inventory_update.cmd")
0066:     pid = os.getpid()
0067:     script_text = f'''@echo off\nsetlocal\nset "NEW={new_exe}"\nset "OLD={current_exe}"\nset "PID={pid}"\n:wait\ntasklist /FI "PID eq %PID%" 2>nul | findstr /I "%PID%" >nul\nif not errorlevel 1 (\n  timeout /t 1 /nobreak >nul\n  goto wait\n)\ntimeout /t 1 /nobreak >nul\nmove /Y "%NEW%" "%OLD%" >nul 2>&1\nif not exist "%OLD%" goto fail\nstart "" "%OLD%"\ndel "%~f0"\nexit /b 0\n:fail\nstart "" "%OLD%"\ndel "%~f0"\nexit /b 1\n'''
0068:     with open(script, "w", encoding="utf-8") as f:
0069:         f.write(script_text)
```
```text
0062: 
0063: def _install_after_exit(new_exe, current_exe):
0064:     app_dir = os.path.dirname(current_exe)
0065:     script = os.path.join(app_dir, ".store_inventory_update.cmd")
0066:     pid = os.getpid()
0067:     script_text = f'''@echo off\nsetlocal\nset "NEW={new_exe}"\nset "OLD={current_exe}"\nset "PID={pid}"\n:wait\ntasklist /FI "PID eq %PID%" 2>nul | findstr /I "%PID%" >nul\nif not errorlevel 1 (\n  timeout /t 1 /nobreak >nul\n  goto wait\n)\ntimeout /t 1 /nobreak >nul\nmove /Y "%NEW%" "%OLD%" >nul 2>&1\nif not exist "%OLD%" goto fail\nstart "" "%OLD%"\ndel "%~f0"\nexit /b 0\n:fail\nstart "" "%OLD%"\ndel "%~f0"\nexit /b 1\n'''
0068:     with open(script, "w", encoding="utf-8") as f:
0069:         f.write(script_text)
0070:     subprocess.Popen(["cmd.exe", "/c", script], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
0071: 
0072: 
0073: def _start_update_download(download_url):
0074:     """Start the fixed-location update installer with IDM when available."""
0075:     if not download_url:
0076:         return False
0077:     candidates = [
0078:         os.path.expandvars(r"%PROGRAMFILES%\Internet Download Manager\IDMan.exe"),
0079:         os.path.expandvars(r"%PROGRAMFILES(x86)%\Internet Download Manager\IDMan.exe"),
0080:     ]
0081:     for idm in candidates:
0082:         if idm and os.path.isfile(idm):
```
```text
0076:         return False
0077:     candidates = [
0078:         os.path.expandvars(r"%PROGRAMFILES%\Internet Download Manager\IDMan.exe"),
0079:         os.path.expandvars(r"%PROGRAMFILES(x86)%\Internet Download Manager\IDMan.exe"),
0080:     ]
0081:     for idm in candidates:
0082:         if idm and os.path.isfile(idm):
0083:             try:
0084:                 subprocess.Popen([idm, "/d", download_url, "/n"], close_fds=True)
0085:                 return True
0086:             except Exception:
0087:                 pass
0088:     try:
0089:         return bool(webbrowser.open(download_url, new=2))
0090:     except Exception:
0091:         try:
0092:             os.startfile(download_url)
0093:             return True
0094:         except Exception:
0095:             return False
0096: 
```
```text
0122:         return False
0123:     candidates = [
0124:         os.path.expandvars(r"%PROGRAMFILES%\Internet Download Manager\IDMan.exe"),
0125:         os.path.expandvars(r"%PROGRAMFILES(x86)%\Internet Download Manager\IDMan.exe"),
0126:     ]
0127:     for idm in candidates:
0128:         if idm and os.path.isfile(idm):
0129:             try:
0130:                 subprocess.Popen([idm, "/d", download_url, "/n"], close_fds=True)
0131:                 return True
0132:             except Exception:
0133:                 pass
0134:     try:
0135:         return bool(webbrowser.open(download_url, new=2))
0136:     except Exception:
0137:         try:
0138:             os.startfile(download_url)
0139:             return True
0140:         except Exception:
0141:             return False
0142: 
```
