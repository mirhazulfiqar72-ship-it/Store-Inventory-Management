# Store Inventory source audit

Generated from `D:\a\Store-Inventory-Management\Store-Inventory-Management\source` after CI patches.

## durable_local.py

- Lines: 147
- Functions: _columns(34-35), snapshot(37-47), _row_count(49-50), _has_more_business_data(52-60), _atomic_write(62-76), save(78-100), load(102-111), restore_if_newer(113-147)

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
0105:         if not SNAPSHOT_PATH.exists():
0106:             return None
0107:         value = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
0108:         return value if isinstance(value, dict) else None
```
```text
0105:         if not SNAPSHOT_PATH.exists():
0106:             return None
0107:         value = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
0108:         return value if isinstance(value, dict) else None
0109:     except Exception:
0110:         LAST_ERROR = traceback.format_exc()
0111:         return None
0112: 
0113: def restore_if_newer(conn: sqlite3.Connection) -> bool:
0114:     global LAST_ERROR
0115:     LAST_ERROR = ""
0116:     saved = load()
0117:     if not saved or _row_count(saved) <= 0:
0118:         return False
0119:     current = snapshot(conn)
0120:     if not _has_more_business_data(saved, current):
0121:         return False
0122:     try:
0123:         conn.execute("BEGIN")
0124:         for table in TABLES:
0125:             cols = _columns(conn, table)
```
```text
0118:         return False
0119:     current = snapshot(conn)
0120:     if not _has_more_business_data(saved, current):
0121:         return False
0122:     try:
0123:         conn.execute("BEGIN")
0124:         for table in TABLES:
0125:             cols = _columns(conn, table)
0126:             rows = saved.get("tables", {}).get(table, {}).get("rows", []) or []
0127:             if not cols:
0128:                 continue
0129:             conn.execute(f"DELETE FROM {table}")
0130:             if not rows:
0131:                 continue
0132:             insert_cols = [c for c in cols if c in rows[0]]
0133:             if not insert_cols:
0134:                 continue
0135:             placeholders = ",".join("?" for _ in insert_cols)
0136:             sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0137:             for row in rows:
0138:                 conn.execute(sql, [row.get(c) for c in insert_cols])
```
```text
0131:                 continue
0132:             insert_cols = [c for c in cols if c in rows[0]]
0133:             if not insert_cols:
0134:                 continue
0135:             placeholders = ",".join("?" for _ in insert_cols)
0136:             sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
0137:             for row in rows:
0138:                 conn.execute(sql, [row.get(c) for c in insert_cols])
0139:         conn.commit()
0140:         return True
0141:     except Exception:
0142:         LAST_ERROR = traceback.format_exc()
0143:         try:
0144:             conn.rollback()
0145:         except Exception:
0146:             pass
0147:         return False
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

- Lines: 5330
- Functions: resource_path(57-61), hash_password(124-129), verify_password(131-134), _copy_legacy_database_if_needed(136-153), _init_schema(156-244), connect(247-276), migrate_old_item_codes(278-292), seed_items(294-301), backup_database(303-332), restore_database(334-351), stock(353-358), fmt_num(360-362), to_iso_date(364-373), to_display_date(375-383), fiscal_year_key(385-396), fiscal_year_range(398-401), normalize_code(403-411), format_code(413-422), attach_code_mask(424-450), set_digits(427-432), key(433-443), paste(445-448), bind_add_to_list(452-473), on_enter(455-466), __init__(477-494), _check_for_updates(496-501), _setup_style(503-539), _shade(542-547), on_close(549-554), redo_network_setup(556-572), backup_now(574-581), restore_backup(583-601), _ctrl_f(603-615), _open_exact_find_text_popup(617-662), do_find(638-647), close(648-655), _global_enter(664-676), wipe(678-679), login(681-710), do_login(696-707), change_password(712-762), save_password(734-756), logout(764-769), home(771-793), _restore_dashboard_after_internal_close(795-809), _ensure_mdi_host(811-832), _internal_window(834-919), normal_place(850-856), restore(857-864), maximize(865-871), minimize(872-887), close(888-912), open_inventory_codes_detail_flow(921-939), open_inventory_codes_with_filters(941-955), open_inventory_codes_report_window(957-1183), tbtn(975-980), balance_as_of(1037-1047), build_nav(1049-1071), selected_prefix(1073-1082), load(1084-1116), page_move(1118-1119), page_first(1120-1120), page_last(1121-1125), on_nav(1129-1130), find_popup(1133-1152), search_fn(1135-1150), print_report(1155-1158), export_pdf(1160-1162), export_word(1163-1165), export_excel(1166-1168), open_menu_window(1185-1207), close_window(1195-1202), _manual_check_update(1209-1213), _show_current_version(1215-1219), build_menu_bar(1221-1268), open_calendar_picker(1270-1318), pick(1288-1290), redraw(1292-1304), nav(1306-1310), make_date_field(1320-1327), clearbody(1329-1355), run_action(1344-1349), _portable_print_current(1357-1368), portable_print_dialog(1370-1443), build_receipt(1397-1415), send(1416-1429), refresh_printers(1430-1436), preview_tree(1445-1457), set_page_actions(1459-1467), _add_transaction_new_button(1469-1486), _report_header(1488-1552), _report_footer(1554-1560), _grr_signature_block(1562-1578), _finish_page(1580-1581), _wrap_text_to_width(1583-1608), fits(1590-1590), _pdf_table_report(1610-1679), table_header(1632-1637), show_preview_window(1681-1754), _safe_report_name(1756-1759), print_preview_window(1761-1764), _fallback_pdf_export(1766-1799), esc(1770-1771), add(1774-1776), _save_entry_report(1801-1821), export_preview_pdf(1823-1852), export_preview_word(1854-1894), export_preview_excel(1896-1932), make_tree(1934-1943), pick_item(1945-1966), choose(1946-1965), ld(1953-1957), sel(1959-1963), bind_item_lookup(1968-1985), lookup(1970-1983), _set_form_editable(1988-2001), walk(1991-2000), document_selector(2003-2037), refresh(2008-2019), selected(2020-2025), dashboard(2039-2151), load_details(2123-2147), _refresh_dashboard_kpis(2153-2167), dashboard_details(2169-2173), item_history(2175-2195), _ask_item_master_filters(2197-2281), finish(2250-2262), items(2283-2521), hierarchy(2324-2333), selected_prefix(2379-2392), balance_as_of(2394-2401), load(2403-2441), set_page(2443-2444), select_node(2446-2467), open_find(2473-2492), search_fn(2475-2490), visible_rows(2497-2499), print_inventory(2500-2504), export_inventory_word(2505-2507), export_inventory_excel(2508-2510), portable_inventory(2515-2517), inventory_codes(2523-2807), btn(2559-2564), close_editor(2600-2610), edit_cell(2612-2638), commit(2630-2636), rows_query(2640-2653), load(2655-2670), new_record(2672-2693), commit(2686-2690), selected_row(2695-2697), edit_record(2699-2707), save_record(2709-2752), delete_record(2754-2765), refresh(2767-2767), do_print(2768-2770), do_close(2771-2771), filter_grid(2789-2796), open_mto_inventory_flow(2809-2832), open_code_opening_flow(2834-2842), code_opening(2844-2845), _open_code_opening_popup(2847-2848), _open_code_opening_detail(2850-3093), norm(2920-2921), table_for(2923-2924), row_for(2926-2931), search_any_destination(2933-2946), desc_hit(2948-2952), clear_form(2954-2967), load_for_edit(2969-2990), check_duplicates(2992-3003), save_code(3008-3059), edit_action(3061-3065), delete_code(3067-3082), _mto_new_item_dialog(3095-3131), save(3111-3128), _item_filter_bar(3133-3145), _date_filter_bar(3147-3155), _ask_mto_inventory_filters(3157-3202), finish(3187-3195), mto_inventory(3204-3404), open_find(3238-3257), search_fn(3240-3255), hierarchy(3276-3280), rebuild_nav(3282-3293), mto_balance(3317-3326), load(3328-3370), set_page(3372-3372), select_node(3373-3382), visible_rows(3387-3387), do_print(3388-3392), export_word(3393-3395), export_excel(3396-3398), party_master(3406-3457), load(3416-3419), clear(3420-3424), new_form(3425-3426), save(3427-3433), load_party_row(3434-3438), on_party_select(3439-3440), edit(3442-3446), delete_party(3447-3453), user_management(3459-3543), sync_role(3486-3491), load(3495-3498), clear(3499-3502), edit(3503-3510), save(3511-3528), delete_user(3529-3540), _renumber_tree(3546-3549), demand(3551-3715), _restore_demand_tree_columns(3594-3600), add(3603-3611), edit_item(3613-3625), delete_item(3627-3635), new_form(3639-3645), save(3647-3663), delete_current(3667-3673), cancel_form(3674-3682), preview_now(3683-3693), edit_saved_demand(3694-3697), print_now(3698-3708), load_demand_into_form(3717-3729), refresh_saved_cache(3731-3743), grr(3745-3908), add(3777-3785), edit_item(3787-3797), delete_item(3799-3807), new_form(3811-3817), save(3819-3840), delete_current(3844-3850), cancel_form(3851-3859), preview_now(3860-3878), portable_current(3879-3882), edit_saved_grr(3884-3887), print_now(3888-3901), load_grr_into_form(3910-3922), issue(3924-4070), old_issue_qty(3953-3956), update_balance(3957-3965), add(3967-3976), edit_item(3978-3989), new_form(3993-3999), post(4001-4022), delete_current(4023-4029), cancel_form(4030-4038), preview_now(4039-4046), portable_current(4047-4049), load_saved_issue(4054-4056), edit_saved_issue(4057-4060), print_issue_now(4061-4066), load_issue_into_form(4072-4085), _ask_report_criteria(4087-4150), finish(4136-4144), _open_report_child(4152-4157), open_stock_balance_report_flow(4159-4162), open_grr_report_flow(4164-4167), open_demand_report_flow(4169-4172), open_issue_report_flow(4174-4177), open_party_report_flow(4179-4182), _ask_stock_balance_filters(4184-4207), ok(4199-4200), cancel(4201-4201), stock_balance(4209-4272), period(4225-4236), header_summary(4237-4238), load(4239-4248), reopen_filters(4249-4253), open_find_stock(4257-4270), search_fn(4259-4269), ledger(4274-4286), open_document_editor(4288-4296), _edit_from_selector(4298-4314), show_saved_records(4316-4347), view(4339-4343), documents(4349-4394), edit_selected(4368-4374), delete_selected(4375-4387), doc_export_selected(4396-4402), doc_preview_selected(4404-4414), doc_print_selected(4416-4424), load_document(4426-4456), _print_loaded_document(4450-4455), _report_filter_popup(4458-4475), ok(4471-4472), cancel(4473-4473), _report_window(4477-4521), load(4490-4497), hdr(4498-4498), open_find_report(4504-4518), search_fn(4506-4517), report_grr(4523-4534), pb(4525-4533), report_demand(4536-4547), pb(4538-4546), report_issue(4549-4558), pb(4551-4557), report_party(4560-4570), pb(4562-4569), reports(4572-4700), load_grr_item(4585-4590), load_grr_date(4598-4606), load_party(4618-4626), load_dem_item(4639-4644), load_dem_date(4652-4660), load_iss_item(4674-4679), load_iss_date(4687-4695), print_item_master(4702-4704), print_party_master(4706-4708), print_report(4710-4724), print_stock(4726-4731), print_ledger(4733-4740), _get_doc_data(4742-4770), export_word(4772-4819), export_excel(4821-4861), preview_pdf(4863-4871), _open_direct_printer(4873-4903), _select_windows_printer_for_pdf(4905-5276), render_preview(5030-5049), on_resize(5051-5053), parse_page_selection(5072-5088), selected_printer(5090-5092), print_rendered_pages(5094-5252), close(5254-5264), print_pdf(5278-5296), open_file(5298-5303), print_demand(5305-5310), print_grr(5312-5320), print_issue(5322-5327)

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
0791:         if not getattr(self, "_update_checked_this_session", False):
0792:             self._update_checked_this_session = True
0793:             self.after(900, lambda: updater.check_for_update(self, manual=False))
0794: 
0795:     def _restore_dashboard_after_internal_close(self):
0796:         try:
0797:             if getattr(self, "_mdi_windows", []):
0798:                 return
```
```text
0880:             b.pack(side="left")
0881:             rb=tk.Button(item,text="□",font=("Segoe UI",8,"bold"),width=2,height=1,padx=0,pady=0,
0882:                          command=lambda:(restore(),maximize()),relief="flat",bd=0,bg="#e7e7e7")
0883:             rb.pack(side="left")
0884:             xb=tk.Button(item,text="×",font=("Segoe UI",9,"bold"),width=2,height=1,padx=0,pady=0,
0885:                          command=close,relief="flat",bd=0,bg="#e7e7e7")
0886:             xb.pack(side="left")
0887:             state["task"]=item
0888:         def close():
0889:             try:
0890:                 task=state.get("task")
0891:                 if task and task.winfo_exists(): task.destroy()
0892:             except Exception: pass
0893:             try:
0894:                 if outer in getattr(self,"_mdi_windows",[]): self._mdi_windows.remove(outer)
0895:             except Exception: pass
0896:             try: outer.destroy()
0897:             except Exception: pass
0898:             if not getattr(self,"_mdi_windows",[]):
0899:                 self._mdi_host.place_forget()
0900:                 self._restore_dashboard_after_internal_close()
```
```text
0945:             return None
0946:         self._inventory_codes_filter=criteria
0947:         win,body=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0948:         try:
0949:             self.items(container=body)
0950:             win.lift()
0951:             return win
0952:         except Exception:
0953:             try: win._internal_close()
0954:             except Exception: pass
0955:             raise
0956: 
0957:     def open_inventory_codes_report_window(self, criteria=None):
0958:         """Open Inventory Codes as a real report-style child window.
0959: 
0960:         This intentionally mirrors the supplied Preview Report workflow: a
0961:         separate resizable/maximizable window with a left navigation tree,
0962:         compact report toolbar, Find dialog, and print/export commands.
0963:         The main application remains open behind it.
0964:         """
0965:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
```
```text
0962:         compact report toolbar, Find dialog, and print/export commands.
0963:         The main application remains open behind it.
0964:         """
0965:         criteria=criteria or getattr(self,"_inventory_codes_filter",None) or {
0966:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
0967:         }
0968:         win,winbody=self._internal_window("Inventory Management - [Inventory Codes]","1180x760")
0969: 
0970:         # --- report-style toolbar ---
0971:         toolbar=tk.Frame(winbody,bg="#E7E7E7",height=42,bd=1,relief="raised")
0972:         toolbar.pack(fill="x",side="top")
0973:         toolbar.pack_propagate(False)
0974: 
0975:         def tbtn(text,cmd,width=9):
0976:             b=tk.Button(toolbar,text=text,command=cmd,width=width,height=1,
0977:                          font=("Microsoft Sans Serif",8),relief="raised",bd=1,
0978:                          padx=3,pady=1)
0979:             b.pack(side="left",padx=2,pady=6)
0980:             return b
0981: 
0982:         # --- main report body ---
```
```text
0993:         navscroll=ttk.Scrollbar(navbox,orient="vertical")
0994:         code_tree=ttk.Treeview(navbox,show="tree",yscrollcommand=navscroll.set)
0995:         navscroll.config(command=code_tree.yview)
0996:         navscroll.pack(side="right",fill="y")
0997:         code_tree.pack(side="left",fill="both",expand=True)
0998: 
0999:         right=tk.Frame(content,bg="#EDEDED")
1000:         right.pack(side="left",fill="both",expand=True)
1001:         reportbar=tk.Frame(right,bg="#D9D9D9",height=34,bd=1,relief="raised")
1002:         reportbar.pack(fill="x")
1003:         reportbar.pack_propagate(False)
1004:         tab=tk.Label(reportbar,text="Main Report",bg="#F5F5F5",bd=1,relief="raised",
1005:                       font=("Microsoft Sans Serif",8),padx=10,pady=4)
1006:         tab.pack(side="left",padx=4,pady=2)
1007:         titlevar=tk.StringVar(value="Inventory Summary")
1008:         tk.Label(reportbar,textvariable=titlevar,bg="#D9D9D9",
1009:                  font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=8)
1010: 
1011:         tableframe=tk.Frame(right,bg="white",bd=1,relief="sunken")
1012:         tableframe.pack(fill="both",expand=True,padx=5,pady=5)
1013:         cols=("SR#","Code","Dscr","UOM","Opening","Balance","Status")
```
```text
1147:                     vals=tree.item(iid,"values")
1148:                     if str(vals[1]).lower()==str(target).lower():
1149:                         tree.selection_set(iid); tree.focus(iid); tree.see(iid); break
1150:                 return True
1151:             self._open_exact_find_text_popup(search_fn)
1152:             self._item_master_find_callback=find_popup
1153: 
1154: 
1155:         def print_report():
1156:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1157:             if not rows: messagebox.showwarning("Print","There is no data to print.",parent=win); return
1158:             self.show_preview_window("Inventory Codes",["Selection: "+("Include Zero Balance" if criteria.get("zero_mode")=="include" else "Exclude Zero Balance")],list(cols),rows,[55,125,320,85,90,100,95])
1159: 
1160:         def export_pdf():
1161:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1162:             if rows: self.export_preview_pdf("Inventory Codes",["Inventory Codes"],list(cols),rows)
1163:         def export_word():
1164:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1165:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1166:         def export_excel():
1167:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
```
```text
1163:         def export_word():
1164:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1165:             if rows: self.export_preview_word("Inventory Codes",["Inventory Codes"],list(cols),rows)
1166:         def export_excel():
1167:             rows=[tuple(tree.item(i,"values")) for i in tree.get_children("")]
1168:             if rows: self.export_preview_excel("Inventory Codes",["Inventory Codes"],list(cols),rows)
1169: 
1170:         tbtn("Find",find_popup,7)
1171:         tbtn("Print",print_report,7)
1172:         tbtn("PDF",export_pdf,6)
1173:         tbtn("Word",export_word,6)
1174:         tbtn("Excel",export_excel,6)
1175:         tbtn("Portable",lambda:self.portable_print_dialog("Inventory Codes",["Inventory Codes"],list(cols),[tuple(tree.item(i,"values")) for i in tree.get_children("")]),9)
1176:         tbtn("Refresh",load,8)
1177:         tbtn("Close",win._internal_close,7)
1178:         tk.Label(toolbar,text="  Inventory Codes",bg="#E7E7E7",font=("Microsoft Sans Serif",8,"bold")).pack(side="left",padx=10)
1179:         tk.Label(toolbar,text="Include Zero" if criteria.get("zero_mode")=="include" else "Exclude Zero",bg="#E7E7E7",font=("Microsoft Sans Serif",8)).pack(side="right",padx=8)
1180: 
1181:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1182:         build_nav(); load(); win.focus_force()
1183:         return win
```
```text
1193:         self.body=frame
1194:         closed={"done":False}
1195:         def close_window():
1196:             if closed["done"]: return
1197:             closed["done"]=True
1198:             if getattr(self,"body",None) is frame: self.body=old_body
1199:             self._page_actions=old_actions
1200:             self._item_master_find_callback=old_find
1201:             try: win._internal_close()
1202:             except Exception: win.destroy()
1203:         win._internal_close=close_window
1204:         try:
1205:             method(); self.update_idletasks(); win.lift(); return win
1206:         except Exception:
1207:             close_window(); raise
1208: 
1209:     def _manual_check_update(self):
1210:         try:
1211:             updater.check_for_update(self, manual=True)
1212:         except Exception as e:
1213:             messagebox.showerror("Check Update", f"Could not check for updates.\n\n{e}", parent=self)
```
```text
1217:             messagebox.showinfo("Current Version", f"Store Inventory Management\n\nCurrent version: {updater.APP_VERSION}", parent=self)
1218:         except Exception as e:
1219:             messagebox.showerror("Current Version", str(e), parent=self)
1220: 
1221:     def build_menu_bar(self):
1222:         """Professional section / sub-section menu bar, ERP style:
1223:         Inventory > Item Master
1224:         Transaction > Purchase Demand, GRN Receipt, Party Master, Material Issue
1225:         Report > Stock Balance, GRN Report, Demand Report, Issue Report, Party Report
1226:         Edit > Change Password, User Management
1227:         Help > Backup Now, Restore Backup, Network Setup
1228:         """
1229:         menubar=tk.Menu(self)
1230: 
1231:         m_inv=tk.Menu(menubar,tearoff=0)
1232:         m_inv.add_command(label="Inventory Codes",command=self.open_inventory_codes_detail_flow)
1233:         m_inv.add_command(label="Code Opening",command=self.open_code_opening_flow)
1234:         m_inv.add_command(label="MTO Inventory",command=self.open_mto_inventory_flow)
1235:         menubar.add_cascade(label="Inventory",menu=m_inv)
1236: 
1237:         m_trans=tk.Menu(menubar,tearoff=0)
```
```text
1237:         m_trans=tk.Menu(menubar,tearoff=0)
1238:         m_trans.add_command(label="Purchase Demand",command=lambda:self.open_menu_window(self.demand,"Purchase Demand"))
1239:         m_trans.add_command(label="GRN Receipt",command=lambda:self.open_menu_window(self.grr,"GRN Receipt"))
1240:         m_trans.add_command(label="Party Master",command=lambda:self.open_menu_window(self.party_master,"Party Master"))
1241:         m_trans.add_command(label="Material Issue",command=lambda:self.open_menu_window(self.issue,"Material Issue"))
1242:         menubar.add_cascade(label="Transaction",menu=m_trans)
1243: 
1244:         m_rep=tk.Menu(menubar,tearoff=0)
1245:         m_rep.add_command(label="Stock Balance",command=self.open_stock_balance_report_flow)
1246:         m_rep.add_separator()
1247:         m_rep.add_command(label="GRN Report",command=self.open_grr_report_flow)
1248:         m_rep.add_command(label="Demand Report",command=self.open_demand_report_flow)
1249:         m_rep.add_command(label="Issue Report",command=self.open_issue_report_flow)
1250:         m_rep.add_command(label="Party Report",command=self.open_party_report_flow)
1251:         menubar.add_cascade(label="Report",menu=m_rep)
1252: 
1253:         m_edit=tk.Menu(menubar,tearoff=0)
1254:         m_edit.add_command(label="Change Password",command=self.change_password)
1255:         if self.is_admin:
1256:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1257:         menubar.add_cascade(label="Edit",menu=m_edit)
```
```text
1252: 
1253:         m_edit=tk.Menu(menubar,tearoff=0)
1254:         m_edit.add_command(label="Change Password",command=self.change_password)
1255:         if self.is_admin:
1256:             m_edit.add_command(label="User Management",command=lambda:self.open_menu_window(self.user_management,"User Management"))
1257:         menubar.add_cascade(label="Edit",menu=m_edit)
1258: 
1259:         m_help=tk.Menu(menubar,tearoff=0)
1260:         m_help.add_command(label="Backup Now",command=self.backup_now)
1261:         m_help.add_command(label="Check Update",command=self._manual_check_update)
1262:         m_help.add_command(label="Current Version",command=self._show_current_version)
1263:         if self.is_admin:
1264:             m_help.add_command(label="Restore Backup",command=self.restore_backup)
1265:             m_help.add_command(label="Network Setup",command=self.redo_network_setup)
1266:         menubar.add_cascade(label="Help",menu=m_help)
1267: 
1268:         self.config(menu=menubar)
1269: 
1270:     def open_calendar_picker(self, var):
1271:         """Small month-grid calendar popup. Picking a day sets `var` to
1272:         DD/MM/YYYY. Works purely with tkinter's built-in `calendar` module -
```
```text
1325:         ttk.Entry(f,textvariable=var,width=width).pack(side="left")
1326:         ttk.Button(f,text="\U0001F4C5",width=3,command=lambda:self.open_calendar_picker(var)).pack(side="left",padx=(2,0))
1327:         return f
1328: 
1329:     def clearbody(self):
1330:         self._portable_print_context=None
1331:         for w in self.body.winfo_children(): w.destroy()
1332:         self._page_actions = {
1333:             "save": lambda: messagebox.showinfo("Save", "Save is not applicable on this screen."),
1334:             "edit": lambda: messagebox.showinfo("Edit", "Edit is not applicable on this screen."),
1335:             "delete": lambda: messagebox.showinfo("Delete", "Delete is not applicable on this screen."),
1336:             "cancel": lambda: self.dashboard(),
1337:             "print": lambda: messagebox.showinfo("Print", "Print is not applicable on this screen."),
1338:             "preview": lambda: messagebox.showinfo("Preview", "Preview is not applicable on this screen."),
1339:         }
1340:         # Single SAP-style toolbar at the very top.
1341:         bar=ttk.Frame(self.body, padding=(0,0,0,8)); bar.pack(fill="x", side="top")
1342:         self._page_action_bar=bar
1343:         self._page_action_first_button=None
1344:         def run_action(k):
1345:             if k=="edit" and not self.can_edit:
```
```text
1342:         self._page_action_bar=bar
1343:         self._page_action_first_button=None
1344:         def run_action(k):
1345:             if k=="edit" and not self.can_edit:
1346:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission. Ask an Admin if you need this."); return
1347:             if k=="delete" and not self.can_delete:
1348:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission. Ask an Admin if you need this."); return
1349:             self._page_actions[k]()
1350:         for text,key,style in (("Save","save","Success"),("Edit","edit","Warning"),
1351:                                ("Delete","delete","Danger"),("Cancel","cancel","Muted"),("Print","print","Primary")):
1352:             b=ttk.Button(bar,text=text,style=f"{style}.TButton",command=lambda k=key: run_action(k))
1353:             b.pack(side="left",padx=(0,2))
1354:             if self._page_action_first_button is None: self._page_action_first_button=b
1355:             ttk.Separator(bar,orient="vertical").pack(side="left",fill="y",padx=4)
1356: 
1357:     def _portable_print_current(self):
1358:         ctx=getattr(self,"_portable_print_context",None)
1359:         if not ctx:
1360:             messagebox.showinfo("Portable Printer","Portable printing is available on GRN, SIR and Preview Report screens.")
1361:             return
1362:         try:
```
```text
1364:             if not data: return
1365:             title,header,columns,rows=data
1366:             self.portable_print_dialog(title,header,columns,rows)
1367:         except Exception as e:
1368:             messagebox.showerror("Portable Printer",str(e))
1369: 
1370:     def portable_print_dialog(self,title,header_lines,columns,rows):
1371:         """Compact direct ESC/POS printer dialog. Uses Windows print spooler,
1372:         not a PDF helper. Works with installed USB/Bluetooth/LAN thermal printers."""
1373:         if not WIN32PRINT_AVAILABLE:
1374:             messagebox.showwarning("Portable Printer","Windows printer support is not available.\n\nRun BUILD_AND_INSTALL.bat again to install pywin32.")
1375:             return
1376:         try:
1377:             printers=[x[2] for x in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
1378:         except Exception as e:
1379:             messagebox.showerror("Portable Printer",f"Could not read Windows printers.\n\n{e}")
1380:             return
1381:         if not printers:
1382:             messagebox.showwarning("Portable Printer","No Windows printer is installed. Connect/install your portable thermal printer first.")
1383:             return
1384:         win,body=self._internal_window("Portable Printer - Receipt Print","470x330")
```
```text
1434:                 if vals and pv.get() not in vals: pv.set(vals[0])
1435:                 status.set(f"{len(rows)} line(s) ready to print | {len(vals)} printer(s) found")
1436:             except Exception as ex: status.set(str(ex))
1437:         printer_combo=ttk.Combobox(box,textvariable=pv,values=printers,state="readonly",width=38)
1438:         printer_combo.grid(row=1,column=1,sticky="w",pady=5)
1439:         ttk.Button(box,text="REFRESH PRINTERS",style="Dashboard.TButton",command=refresh_printers).grid(row=5,column=0,pady=8,sticky="w")
1440:         ttk.Button(box,text="TEST / PRINT RECEIPT",style="Success.TButton",command=send).grid(row=5,column=1,pady=8,sticky="e")
1441:         ttk.Button(box,text="CLOSE",style="Dashboard.TButton",command=win._internal_close).grid(row=6,column=1,sticky="e",pady=3)
1442:         win.bind("<Escape>",lambda e:win._internal_close())
1443:         win.focus_force()
1444: 
1445:     def preview_tree(self, title, tree, header_lines=None):
1446:         """Preview the exact rows currently visible in a Treeview."""
1447:         cols=list(tree["columns"])
1448:         headings=tuple(tree.heading(c, "text") or c for c in cols)
1449:         rows=[tuple(tree.item(i, "values")) for i in tree.get_children("")]
1450:         if not rows:
1451:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1452:             return
1453:         widths=[]
1454:         for c in cols:
```
```text
1451:             messagebox.showwarning("Preview", "There is no data to preview in this section.")
1452:             return
1453:         widths=[]
1454:         for c in cols:
1455:             try: widths.append(max(70, min(260, int(tree.column(c, "width")))))
1456:             except Exception: widths.append(100)
1457:         self.show_preview_window(title, header_lines or [], headings, rows, widths)
1458: 
1459:     def set_page_actions(self, save=None, edit=None, delete=None, cancel=None, print=None, preview=None):
1460:         self._page_actions.update({
1461:             "save": save or self._page_actions.get("save"),
1462:             "edit": edit or self._page_actions.get("edit"),
1463:             "delete": delete or self._page_actions.get("delete"),
1464:             "cancel": cancel or self._page_actions.get("cancel"),
1465:             "print": print or self._page_actions.get("print"),
1466:             "preview": preview or self._page_actions.get("preview"),
1467:         })
1468: 
1469:     def _add_transaction_new_button(self, command):
1470:         bar=getattr(self,"_page_action_bar",None); first=getattr(self,"_page_action_first_button",None)
1471:         if bar is None or first is None: return
```
```text
1480:         sep.pack(side="left",fill="y",padx=4)
1481:         for w in existing:
1482:             try:
1483:                 if isinstance(w,ttk.Button): w.pack(side="left",padx=(0,2))
1484:                 elif isinstance(w,ttk.Separator): w.pack(side="left",fill="y",padx=4)
1485:                 else: w.pack(side="left")
1486:             except Exception: pass
1487: 
1488:     def _report_header(self, c, title, page_size=A4, landscape_mode=False, y_top=None, header_lines=None):
1489:         """Draw a consistent professional report header and return the first table Y.
1490: 
1491:         For GRN Receipt reports the document number is shown on the left and
1492:         the GRN Date is deliberately shown on the right in a bordered document
1493:         information panel.
1494:         """
1495:         W,H=page_size
1496:         if y_top is None: y_top=H-24
1497:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1498:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1499:         if os.path.exists(LOGO_FILE):
1500:             try:
```
```text
1493:         information panel.
1494:         """
1495:         W,H=page_size
1496:         if y_top is None: y_top=H-24
1497:         logo_x, logo_y, logo_w, logo_h=24, y_top-34, 58, 40
1498:         c.setLineWidth(0.8); c.rect(logo_x, logo_y, logo_w, logo_h, stroke=1, fill=0)
1499:         if os.path.exists(LOGO_FILE):
1500:             try:
1501:                 from reportlab.lib.utils import ImageReader
1502:                 c.drawImage(ImageReader(LOGO_FILE), logo_x+3, logo_y+3, logo_w-6, logo_h-6, preserveAspectRatio=True, anchor='c', mask='auto')
1503:             except Exception:
1504:                 c.setFont("Helvetica-Bold",6); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-2,"LOGO")
1505:         else:
1506:             c.setFont("Helvetica-Bold",7); c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2+4,"COMPANY")
1507:             c.drawCentredString(logo_x+logo_w/2, logo_y+logo_h/2-6,"LOGO")
1508:         c.setFont("Helvetica-Bold",14); c.drawCentredString(W/2+18, y_top-10, COMPANY)
1509:         c.setFont("Helvetica-Bold",10); c.drawCentredString(W/2+18, y_top-26, str(title).upper())
1510:         c.setFont("Helvetica",7); c.drawRightString(W-24, y_top-43, datetime.now().strftime("Printed: %d-%m-%Y %H:%M"))
1511: 
1512:         # Professional document information box.
1513:         info_top=logo_y-12
```
```text
1546:                 # naturally occupies the right-hand cell when supplied second.
1547:                 c.setFont("Helvetica-Bold",7)
1548:                 c.drawString(xx,yy,(label+":")[:28])
1549:                 c.setFont("Helvetica",7)
1550:                 c.drawString(xx+58,yy,val[:58])
1551:             return box_y-12
1552:         return info_top-6
1553: 
1554:     def _report_footer(self, c, page_no, page_size=A4):
1555:         W,H=page_size
1556:         c.setStrokeColorRGB(0.45,0.45,0.45); c.setLineWidth(0.5); c.line(24,24,W-24,24)
1557:         c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica",7)
1558:         c.drawString(24,13,REPORT_FOOTER)
1559:         c.drawRightString(W-24,13,f"Page {page_no}")
1560:         c.setFillColorRGB(0,0,0)
1561: 
1562:     def _grr_signature_block(self, c, y, page_size=A4):
1563:         """Draw the three requested transaction-document signature lines."""
1564:         W,H=page_size
1565:         labels=["Prepared By","Store Keeper","Store Incharge"]
1566:         block_h=70
```
```text
1573:             x=left+i*col_w
1574:             c.setLineWidth(0.6)
1575:             c.line(x+30,top-34,x+col_w-30,top-34)
1576:             c.setFont("Helvetica-Bold",7)
1577:             c.drawCentredString(x+col_w/2,top-48,label)
1578:         return True
1579: 
1580:     def _finish_page(self, c, page_no, page_size=A4):
1581:         self._report_footer(c,page_no,page_size); c.showPage()
1582: 
1583:     def _wrap_text_to_width(self, text, font_name, font_size, max_width):
1584:         """Word-wrap `text` into a list of lines that each fit inside
1585:         max_width (points) at the given font, breaking mid-word only when a
1586:         single word is itself wider than the column."""
1587:         text=str(text) if text is not None else ""
1588:         if not text:
1589:             return [""]
1590:         def fits(s): return stringWidth(s, font_name, font_size) <= max_width
1591:         lines=[]; cur=""
1592:         for word in text.split(" "):
1593:             trial=(cur+" "+word).strip() if cur else word
```
```text
1602:                     mid=(lo+hi)//2
1603:                     if fits(w[:mid]): fit_at=mid; lo=mid+1
1604:                     else: hi=mid-1
1605:                 lines.append(w[:fit_at]); w=w[fit_at:]
1606:             cur=w
1607:         if cur: lines.append(cur)
1608:         return lines or [""]
1609: 
1610:     def _pdf_table_report(self, path, title, headers, rows, page_size=landscape(A4), font_size=7, col_widths=None, header_lines=None, auto_print=True):
1611:         """Create a paginated professional PDF with logo, bordered information,
1612:         GRR signature lines and page numbers. Also keep the same report data in
1613:         memory so the built-in Windows printer dialog can print directly without
1614:         requiring a PDF application's PrintTo association."""
1615:         if not hasattr(self, "_print_jobs"):
1616:             self._print_jobs = {}
1617:         self._print_jobs[os.path.abspath(path)] = (title, header_lines or [], tuple(headers), [tuple(r) for r in rows], page_size)
1618:         c=canvas.Canvas(path,pagesize=page_size); W,H=page_size; c.setTitle(str(title))
1619:         page=1
1620:         y=self._report_header(c,title,page_size,header_lines=header_lines)
1621:         usable=W-56
1622:         n=max(1,len(headers))
```
```text
1644:             if desc_idx is not None and desc_idx < len(r):
1645:                 desc_lines=self._wrap_text_to_width(r[desc_idx],"Helvetica",font_size,max(20,widths[desc_idx]-4))
1646:             else:
1647:                 desc_lines=[""]
1648:             row_h=max(11 if font_size<=7 else 13, len(desc_lines)*line_h+2)
1649:             # Reserve room on the final page for the three transaction signatures + footer.
1650:             reserve=120 if is_transaction_doc else 42
1651:             if y-row_h<reserve:
1652:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1653:                 y=self._report_header(c,title,page_size,header_lines=header_lines); table_header()
1654:             # Item rows are intentionally border-free. The section/header remains
1655:             # professional while avoiding the unwanted boxed line around each
1656:             # individual printed item row. Description is drawn separately
1657:             # below (auto-fit / wrapped), so it is skipped in this pass.
1658:             for ci,(xx,val) in enumerate(zip(xs,r)):
1659:                 if ci==desc_idx: continue
1660:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1661:             if desc_idx is not None and desc_idx < len(r):
1662:                 for li,ln in enumerate(desc_lines):
1663:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1664:             y-=row_h
```
```text
1659:                 if ci==desc_idx: continue
1660:                 c.drawString(xx,y,str(val if val is not None else "")[:28])
1661:             if desc_idx is not None and desc_idx < len(r):
1662:                 for li,ln in enumerate(desc_lines):
1663:                     c.drawString(xs[desc_idx],y-li*line_h,ln)
1664:             y-=row_h
1665:         if is_transaction_doc:
1666:             # Keep the three requested transaction signatures at the physical bottom
1667:             # final page, immediately above the report footer.  If the item
1668:             # table reaches this reserved area, start a fresh final page.
1669:             bottom_sig_y = 138
1670:             if y < 165:
1671:                 self._report_footer(c,page,page_size); c.showPage(); page+=1
1672:                 y=self._report_header(c,title,page_size,header_lines=header_lines)
1673:             # Draw signatures at a fixed bottom position so they never float
1674:             # directly after the last item row.
1675:             self._grr_signature_block(c,bottom_sig_y,page_size)
1676:         self._report_footer(c,page,page_size); c.save()
1677:         if auto_print:
1678:             self.print_pdf(path)
1679:         return path
```
```text
1673:             # Draw signatures at a fixed bottom position so they never float
1674:             # directly after the last item row.
1675:             self._grr_signature_block(c,bottom_sig_y,page_size)
1676:         self._report_footer(c,page,page_size); c.save()
1677:         if auto_print:
1678:             self.print_pdf(path)
1679:         return path
1680: 
1681:     def show_preview_window(self, title, header_lines, columns, rows, widths=None, on_save=None):
1682:         """Professional on-screen preview showing bordered document information
1683:         and a bordered item section. GRN Date is displayed in the right column."""
1684:         win,winbody=self._internal_window("Inventory Management - [Preview Report]","1180x760")
1685:         brand=ttk.Frame(winbody,padding=(14,10)); brand.pack(fill="x")
1686:         # Preview intentionally hides the company logo and company name.
1687:         # The actual generated/printed PDF still contains both via
1688:         # _report_header(), so only the on-screen preview is affected.
1689:         brand_text=ttk.Frame(brand); brand_text.pack(fill="x",expand=True)
1690:         ttk.Label(brand_text,text=str(title).upper(),font=("Segoe UI",10,"bold")).pack(anchor="center")
1691:         ttk.Label(brand_text,text=datetime.now().strftime("Printed: %d-%m-%Y %H:%M"),font=("Segoe UI",8)).pack(anchor="center")
1692: 
1693:         info=ttk.LabelFrame(winbody,text="Document Information",padding=8); info.pack(fill="x",padx=14,pady=(2,8))
```
```text
1714:         ttk.Separator(winbody,orient="horizontal").pack(fill="x")
1715: 
1716:         items=ttk.LabelFrame(winbody,text=f"ITEMS / RECEIPT DETAILS  —  {len(rows)} line(s)",padding=8)
1717:         items.pack(fill="both",expand=True,padx=14,pady=(4,8))
1718:         tr=self.make_tree(items,columns,widths)
1719:         for r in rows: tr.insert("", "end", values=r)
1720: 
1721:         ttk.Button(toolbar,text="Print",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1722:         ttk.Button(toolbar,text="Export PDF",style="Dashboard.TButton",command=lambda:self.export_preview_pdf(title,header_lines,columns,rows)).pack(side="left",padx=2)
1723:         ttk.Button(toolbar,text="Export Word",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1724:         ttk.Button(toolbar,text="Export Excel",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1725:         ttk.Button(toolbar,text="Close",style="Dashboard.TButton",command=win._internal_close).pack(side="right",padx=2)
1726:         win.bind("<Control-f>",bind_preview_find)
1727:         win.bind("<Control-F>",bind_preview_find)
1728: 
1729:         # GRN Receipt and Purchase Demand use the requested three signature lines at the bottom.
1730:         is_transaction_preview=("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1731:         if is_transaction_preview:
1732:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1733:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1734:                 sig.columnconfigure(i,weight=1)
```
```text
1732:             sig=ttk.Frame(winbody,padding=7); sig.pack(fill="x",padx=14,pady=(0,6))
1733:             for i,label in enumerate(["Prepared By","Store Keeper","Store Incharge"]):
1734:                 sig.columnconfigure(i,weight=1)
1735:                 cell=ttk.Frame(sig,padding=4); cell.grid(row=0,column=i,sticky="ew")
1736:                 ttk.Label(cell,text="________________",font=("Segoe UI",8),anchor="center").pack(fill="x")
1737:                 ttk.Label(cell,text=label,font=("Segoe UI",8,"bold"),anchor="center").pack(fill="x",pady=(3,0))
1738: 
1739:         btnbar=ttk.Frame(winbody,padding=(14,6)); btnbar.pack(fill="x")
1740:         ttk.Button(btnbar,text="PRINT / PDF",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1741:         ttk.Button(btnbar,text="PRINT AGAIN",style="Dashboard.TButton",command=lambda:self.print_preview_window(title,header_lines,columns,rows)).pack(side="left",padx=2)
1742:         ttk.Button(btnbar,text="EXPORT WORD",style="Dashboard.TButton",command=lambda:self.export_preview_word(title,header_lines,columns,rows)).pack(side="left",padx=2)
1743:         ttk.Button(btnbar,text="EXPORT EXCEL",style="Dashboard.TButton",command=lambda:self.export_preview_excel(title,header_lines,columns,rows)).pack(side="left",padx=2)
1744:         if on_save:
1745:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1746:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1747:         if not is_transaction_preview:
1748:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1749:         # IMPORTANT: this must remain a normal top-level window (not transient
1750:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1751:         # exactly like the Preview Report window in the supplied recording.
1752:         # The Find dialog is opened from this window and is independent.
```
```text
1745:             ttk.Button(btnbar,text="LOOKS GOOD - SAVE NOW",command=lambda:(on_save(),win._internal_close())).pack(side="left",padx=4)
1746:         ttk.Button(btnbar,text="CLOSE PREVIEW",style="Dashboard.TButton",command=win._internal_close).pack(side="left",padx=2)
1747:         if not is_transaction_preview:
1748:             ttk.Label(winbody,text="Authorized Signatory: ____________________    Store In-Charge: ____________________    Page 1 / Preview",font=("Segoe UI",8)).pack(fill="x",padx=14,pady=(0,8))
1749:         # IMPORTANT: this must remain a normal top-level window (not transient
1750:         # and not grab_set) so Windows displays Minimize + Maximize + Close
1751:         # exactly like the Preview Report window in the supplied recording.
1752:         # The Find dialog is opened from this window and is independent.
1753:         win.bind("<Escape>",lambda e:(win._internal_close(),"break"))
1754:         win.focus_force()
1755: 
1756:     def _safe_report_name(self, title, extension):
1757:         safe="".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip()
1758:         safe=safe.replace(" ","_") or "Preview"
1759:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1760: 
1761:     def print_preview_window(self, title, header_lines, columns, rows):
1762:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1763:         self._open_direct_printer(title, header_lines, columns, rows,
1764:                                   landscape(A4) if len(columns) > 8 else A4)
1765: 
```
```text
1758:         safe=safe.replace(" ","_") or "Preview"
1759:         return os.path.join(REPORTS_DIR, f"{safe}_Preview.{extension}")
1760: 
1761:     def print_preview_window(self, title, header_lines, columns, rows):
1762:         # Printing opens only the printer dialog. It must NOT generate a PDF.
1763:         self._open_direct_printer(title, header_lines, columns, rows,
1764:                                   landscape(A4) if len(columns) > 8 else A4)
1765: 
1766:     def _fallback_pdf_export(self, path, title, header_lines, columns, rows):
1767:         """Minimal dependency-free PDF fallback used only if ReportLab is unavailable.
1768:         This keeps the Export PDF button functional on a machine where the bundled
1769:         ReportLab package cannot be imported."""
1770:         def esc(v):
1771:             return str(v if v is not None else "").replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," ")
1772:         W,H=842,595
1773:         lines=["BT", "/F1 12 Tf", "40 560 Td"]
1774:         def add(txt,size=8,leading=11):
1775:             lines.append(f"/F1 {size} Tf")
1776:             lines.append(f"0 -{leading} Td ({esc(txt)}) Tj")
1777:         add(str(title),12,16)
1778:         for h in header_lines or []:
```
```text
1785:         lines.append("ET")
1786:         stream="\n".join(lines).encode("latin-1","replace")
1787:         objs=[]
1788:         objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
1789:         objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
1790:         objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode())
1791:         objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
1792:         objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode()+stream+b"\nendstream")
1793:         out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
1794:         for i,obj in enumerate(objs,1):
1795:             offsets.append(len(out)); out.extend(f"{i} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
1796:         xref=len(out); out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
1797:         for off in offsets[1:]: out.extend(f"{off:010d} 00000 n \n".encode())
1798:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1799:         with open(path,"wb") as f: f.write(out)
1800: 
1801:     def _save_entry_report(self, title, header_lines, columns, rows):
1802:         try:
1803:             os.makedirs(REPORTS_DIR, exist_ok=True)
1804:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1805:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```
```text
1798:         out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
1799:         with open(path,"wb") as f: f.write(out)
1800: 
1801:     def _save_entry_report(self, title, header_lines, columns, rows):
1802:         try:
1803:             os.makedirs(REPORTS_DIR, exist_ok=True)
1804:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Entry"
1805:             stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
1806:             path = os.path.join(REPORTS_DIR, f"{safe}_{stamp}.pdf")
1807:             page_size = landscape(A4) if len(columns) > 8 else A4
1808:             if REPORTLAB:
1809:                 self._pdf_table_report(path, title, columns, rows, page_size, 7, header_lines=header_lines, auto_print=False)
1810:             else:
1811:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1812:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1813:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1814:             with open(path, "rb") as f:
1815:                 if f.read(5) != b"%PDF-":
1816:                     raise IOError("Generated report is not a valid PDF.")
1817:             self._last_entry_report_path = path
1818:             return path
```
```text
1812:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1813:                 raise IOError("PDF was not created in C:\\StoreInventoryManagement\\Reports.")
1814:             with open(path, "rb") as f:
1815:                 if f.read(5) != b"%PDF-":
1816:                     raise IOError("Generated report is not a valid PDF.")
1817:             self._last_entry_report_path = path
1818:             return path
1819:         except Exception as exc:
1820:             self._last_entry_report_path = None
1821:             return None
1822: 
1823:     def export_preview_pdf(self, title, header_lines, columns, rows):
1824:         """Write the visible preview to C:\StoreInventoryManagement\Reports."""
1825:         try:
1826:             os.makedirs(REPORTS_DIR, exist_ok=True)
1827:             safe = "".join(ch for ch in str(title) if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "Preview"
1828:             path = os.path.abspath(os.path.join(REPORTS_DIR, f"{safe}_Preview_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
1829:             generated = False
1830:             if REPORTLAB:
1831:                 try:
1832:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
```
```text
1829:             generated = False
1830:             if REPORTLAB:
1831:                 try:
1832:                     self._pdf_table_report(path, title, columns, rows, landscape(A4), 7, header_lines=header_lines, auto_print=False)
1833:                     generated = True
1834:                 except Exception:
1835:                     generated = False
1836:             if not generated:
1837:                 self._fallback_pdf_export(path, title, header_lines, columns, rows)
1838:             if not os.path.isfile(path) or os.path.getsize(path) <= 0:
1839:                 raise IOError("The PDF file was not created in the Reports folder.")
1840:             with open(path, "rb") as pf:
1841:                 signature = pf.read(5)
1842:             if signature != b"%PDF-":
1843:                 raise IOError("The generated file is not a valid PDF.")
1844:             self._last_report_path = path
1845:             try:
1846:                 webbrowser.open("file://" + path)
1847:             except Exception:
1848:                 self.open_file(path)
1849:             return path
```
```text
1843:                 raise IOError("The generated file is not a valid PDF.")
1844:             self._last_report_path = path
1845:             try:
1846:                 webbrowser.open("file://" + path)
1847:             except Exception:
1848:                 self.open_file(path)
1849:             return path
1850:         except Exception as e:
1851:             messagebox.showerror("PDF Export", f"Could not generate the PDF.\n\n{e}")
1852:             return None
1853: 
1854:     def export_preview_word(self, title, header_lines, columns, rows):
1855:         """Export exactly what is visible in the current preview to Word."""
1856:         if not DOCX_AVAILABLE:
1857:             return messagebox.showwarning("Word Export","Word export needs the python-docx package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install python-docx")
1858:         path=self._safe_report_name(title,"docx")
1859:         doc=Document()
1860:         sec=doc.sections[0]
1861:         sec.header.paragraphs[0].text=f"[ COMPANY LOGO ]    {COMPANY}"
1862:         sec.header.paragraphs[0].runs[0].bold=True
1863:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
```
```text
1885:             doc.add_paragraph("")
1886:             sig=doc.add_table(rows=2,cols=3)
1887:             labels=["Prepared By","Store Keeper","Store Incharge"]
1888:             for i,label in enumerate(labels):
1889:                 sig.cell(0,i).text="____________________"
1890:                 sig.cell(1,i).text=label
1891:                 for para in sig.cell(1,i).paragraphs:
1892:                     for run in para.runs: run.bold=True
1893:         doc.save(path)
1894:         self.open_file(path)
1895: 
1896:     def export_preview_excel(self, title, header_lines, columns, rows):
1897:         """Export exactly what is visible in the current preview to Excel."""
1898:         if not XLSX_AVAILABLE:
1899:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
1900:         path=self._safe_report_name(title,"xlsx")
1901:         wb=openpyxl.Workbook(); ws=wb.active
1902:         ws.title="Preview"
1903:         ws.oddHeader.center.text=f"[ COMPANY LOGO ]   {COMPANY}\n{title}"
1904:         is_transaction_preview = ("GOODS RECEIPT" in str(title).upper() or str(title).upper().startswith("PURCHASE DEMAND"))
1905:         if not is_transaction_preview:
```
```text
1923:             ws.append(["Prepared By","Store Keeper","Store Incharge"])
1924:             for col in range(1,4):
1925:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
1926:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
1927:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
1928:         for col_cells in ws.columns:
1929:             length=max((len(str(c.value)) for c in col_cells if c.value is not None),default=10)
1930:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
1931:         wb.save(path)
1932:         self.open_file(path)
1933: 
1934:     def make_tree(self,parent,cols,widths=None):
1935:         fr=ttk.Frame(parent);fr.pack(fill="both",expand=True)
1936:         tr=ttk.Treeview(fr,columns=cols,show="headings")
1937:         for i,c in enumerate(cols):
1938:             tr.heading(c,text=c,anchor="center");tr.column(c,width=(widths[i] if widths else 120),anchor="center",stretch=True)
1939:         y=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);x=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
1940:         tr.configure(yscrollcommand=y.set,xscrollcommand=x.set)
1941:         tr.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew")
1942:         fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
1943:         return tr
```
```text
1996:                     w.state(["!disabled"] if editable else ["disabled"])
1997:             except Exception:
1998:                 try: w.configure(state="normal" if editable else "disabled")
1999:                 except Exception: pass
2000:             for ch in w.winfo_children(): walk(ch)
2001:         for root in roots: walk(root)
2002: 
2003:     def document_selector(self, parent, label, typ, var, load_callback):
2004:         """Dropdown for previously saved documents; typing a document number and pressing Enter also loads it."""
2005:         ttk.Label(parent, text=label).pack(side="left", padx=(4,4))
2006:         combo=ttk.Combobox(parent, textvariable=var, width=52, state="normal")
2007:         combo.pack(side="left", padx=4)
2008:         def refresh():
2009:             vals=[]
2010:             if typ=="demand":
2011:                 rows=self.conn.execute("SELECT demand_no,demand_date,department FROM demands ORDER BY rowid DESC").fetchall()
2012:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]}" for r in rows]
2013:             elif typ=="grr":
2014:                 rows=self.conn.execute("SELECT grr_no,grr_date,department,supplier FROM grr ORDER BY rowid DESC").fetchall()
2015:                 vals=[f"{r[0]} -> {r[1]} -> {r[2]} -> {r[3]}" for r in rows]
2016:             else:
```
```text
2023:             no=text.split(" -> ",1)[0].strip()
2024:             var.set(no)
2025:             load_callback(no)
2026:         combo.bind("<<ComboboxSelected>>", selected)
2027:         combo.bind("<Return>", selected)
2028:         ttk.Button(parent,text="LOAD",command=selected).pack(side="left",padx=3)
2029:         ttk.Button(parent,text="REFRESH",command=refresh).pack(side="left",padx=3)
2030:         refresh()
2031:         # Keep the currently open transaction's saved-record list live.
2032:         # Each save calls refresh_saved_cache(), so newly saved records appear
2033:         # immediately without closing/reopening the window or pressing Refresh.
2034:         if not hasattr(self, "_document_selector_refreshers"):
2035:             self._document_selector_refreshers = {}
2036:         self._document_selector_refreshers.setdefault(typ, []).append((combo, refresh))
2037:         return combo
2038: 
2039:     def dashboard(self):
2040:         # Dashboard-only visual refresh. All existing data queries, filters,
2041:         # callbacks and report/detail behavior are intentionally preserved.
2042:         self.clearbody()
2043:         c=self.conn
```
```text
2124:             for x in tr.get_children(): tr.delete(x)
2125:             params=[];where=[]
2126:             fd_iso=to_iso_date(from_date.get().strip()); td_iso=to_iso_date(to_date.get().strip())
2127:             if fd_iso: where.append("t.doc_date>=?");params.append(fd_iso)
2128:             if td_iso: where.append("t.doc_date<=?");params.append(td_iso)
2129:             if item_filter.get().strip(): where.append("i.description LIKE ?");params.append("%"+item_filter.get().strip()+"%")
2130:             if code_filter.get().strip(): where.append("t.code LIKE ?");params.append("%"+code_filter.get().strip()+"%")
2131:             if doc_filter.get()!="ALL": where.append("t.doc_type=?");params.append("GRR" if doc_filter.get()=="GRN" else doc_filter.get())
2132:             sql="""SELECT t.doc_date,t.doc_type,t.doc_no,t.code,i.description,i.uom,t.qty,t.party,t.ref_no
2133:                    FROM transactions t JOIN items i ON i.code=t.code"""
2134:             if where: sql += " WHERE " + " AND ".join(where)
2135:             sql += " ORDER BY t.doc_date DESC,t.id DESC"
2136:             rows=list(c.execute(sql,params))
2137:             running={r[0]:float(r[1] or 0) for r in c.execute("SELECT code,opening_qty FROM items")}
2138:             alltx=list(c.execute("SELECT id,code,doc_type,qty FROM transactions ORDER BY id"))
2139:             bal_after={}
2140:             for txid,cc,typ,qty in alltx:
2141:                 running.setdefault(cc,0.0)
2142:                 running[cc]+=float(qty or 0) if typ=="GRR" else -float(qty or 0)
2143:                 bal_after[txid]=running[cc]
2144:             for r in rows:
```
```text
2519:         self.set_page_actions(print=print_inventory,preview=lambda:self.preview_tree("Inventory Codes",tree,[selected_label.get()]))
2520:         load()
2521:         tree.bind("<Double-1>",lambda e:self.item_history(tree.item(tree.selection()[0])["values"][1]) if tree.selection() else None)
2522: 
2523:     def inventory_codes(self):
2524:         """Inventory Codes using the classic desktop inventory interface.
2525: 
2526:         This screen intentionally follows the uploaded Inventory Management
2527:         reference: a simple module title, compact New/Edit/Delete/Save/
2528:         Refresh/Print/Close action row, and a full-width editable data grid.
2529:         All records come from the V18 database, so existing inventory data is
2530:         preserved rather than recreated.
2531:         """
2532:         self.clearbody()
2533:         # Remove the generic SAP action row; this page owns its own classic
2534:         # action row just like the reference Inventory/Items screen.
2535:         if self.body.winfo_children():
2536:             try:
2537:                 self.body.winfo_children()[0].destroy()
2538:             except Exception:
2539:                 pass
```
```text
2592:         if criteria.get("zero_mode")=="exclude": filter_text.append("Zero Balance excluded")
2593:         if filter_text:
2594:             tk.Label(status_bar,text=" | ".join(filter_text),anchor="e",font=("Microsoft Sans Serif",8),
2595:                      bg=COLORS["bg"],fg=COLORS["primary_dark"]).pack(side="right")
2596: 
2597:         editing={"id":None,"new":False}
2598:         cell_editor={"widget":None}
2599: 
2600:         def close_editor(save_value=False):
2601:             w=cell_editor.get("widget")
2602:             if not w:
2603:                 return
2604:             try:
2605:                 if save_value:
2606:                     w.event_generate("<Return>")
2607:                 w.destroy()
2608:             except Exception:
2609:                 pass
2610:             cell_editor["widget"]=None
2611: 
2612:         def edit_cell(event=None):
```
```text
2622:             bbox=tree.bbox(iid,colid)
2623:             if not bbox: return
2624:             close_editor(False)
2625:             x,y,w,h=bbox
2626:             val=str(tree.item(iid,"values")[idx] or "")
2627:             e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2628:             e.insert(0,val); e.select_range(0,tk.END); e.focus_set(); e.place(x=x,y=y,width=w,height=h)
2629:             cell_editor["widget"]=e
2630:             def commit(_=None):
2631:                 try:
2632:                     vals=list(tree.item(iid,"values")); vals[idx]=e.get().strip(); tree.item(iid,values=vals)
2633:                 finally:
2634:                     try:e.destroy()
2635:                     except Exception:pass
2636:                     cell_editor["widget"]=None
2637:             e.bind("<Return>",commit); e.bind("<Escape>",lambda _:(e.destroy(),cell_editor.__setitem__("widget",None)))
2638:             e.bind("<FocusOut>",commit)
2639: 
2640:         def rows_query():
2641:             where=["COALESCE(item_type,'Local')='Local'"]; params=[]
2642:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
```
```text
2644:             if tc: where.append("code <= ?"); params.append(tc)
2645:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
2646:             if df or dt:
2647:                 sub=[]; sp=[]
2648:                 if df: sub.append("doc_date >= ?"); sp.append(df)
2649:                 if dt: sub.append("doc_date <= ?"); sp.append(dt)
2650:                 where.append("EXISTS (SELECT 1 FROM transactions tx WHERE tx.code=items.code AND " + " AND ".join(sub) + ")")
2651:                 params.extend(sp)
2652:             sql="SELECT id,code,description,uom,opening_qty,0 as rate,'' as remarks FROM items WHERE " + " AND ".join(where) + " ORDER BY code"
2653:             return sql,params
2654: 
2655:         def load():
2656:             close_editor(False)
2657:             for i in tree.get_children(): tree.delete(i)
2658:             sql,params=rows_query()
2659:             count=0
2660:             for r in self.conn.execute(sql,params):
2661:                 # V18 stores UOM/opening and the original application may have
2662:                 # rate/remarks columns in some versions. Read them safely.
2663:                 rid,code,desc,uom,opening,rate,remarks=r
2664:                 bal=stock(self.conn,code)
```
```text
2678:             tree.selection_set(iid); tree.focus(iid); tree.see(iid)
2679:             editing["id"]=None; editing["new"]=True
2680:             # Put the user directly into the Code cell.
2681:             try:
2682:                 bbox=tree.bbox(iid,"#2")
2683:                 if bbox:
2684:                     x,y,w,h=bbox; e=tk.Entry(grid_frame,font=("Microsoft Sans Serif",9),justify="center")
2685:                     e.place(x=x,y=y,width=w,height=h); e.focus_set(); cell_editor["widget"]=e
2686:                     def commit(_=None):
2687:                         vals=list(tree.item(iid,"values")); vals[1]=e.get().strip(); tree.item(iid,values=vals)
2688:                         try:e.destroy()
2689:                         except Exception:pass
2690:                         cell_editor["widget"]=None
2691:                     e.bind("<Return>",commit); e.bind("<FocusOut>",commit)
2692:             except Exception: pass
2693:             status.set("New row added — enter values, then press Save")
2694: 
2695:         def selected_row():
2696:             a=tree.selection()
2697:             return a[0] if a else None
2698: 
```
```text
2698: 
2699:         def edit_record():
2700:             iid=selected_row()
2701:             if not iid:
2702:                 messagebox.showwarning("Edit","Select an Inventory Codes row first."); return
2703:             if not self.can_edit and not self.is_admin:
2704:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2705:             editing["id"]=tree.item(iid,"values")[0]; editing["new"]=False
2706:             status.set("Edit mode — double-click any cell to change it, then press Save")
2707:             tree.focus(iid); tree.see(iid)
2708: 
2709:         def save_record():
2710:             iid=selected_row()
2711:             if not iid:
2712:                 messagebox.showwarning("Save","Select a row first, or press New."); return
2713:             if not self.can_edit and not self.is_admin:
2714:                 messagebox.showwarning("Permission Denied","Your account does not have Edit permission."); return
2715:             close_editor(True)
2716:             vals=list(tree.item(iid,"values"))
2717:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2718:             try: opening=float(str(vals[4]).strip() or 0)
```
```text
2716:             vals=list(tree.item(iid,"values"))
2717:             code=str(vals[1]).strip(); desc=str(vals[2]).strip(); uom=str(vals[3]).strip()
2718:             try: opening=float(str(vals[4]).strip() or 0)
2719:             except Exception: raise ValueError("Opening Qty must be a number.")
2720:             try: rate=float(str(vals[5]).strip() or 0)
2721:             except Exception: raise ValueError("Rate must be a number.")
2722:             remarks=str(vals[6]).strip()
2723:             if not code or len("".join(ch for ch in code if ch.isdigit()))!=8:
2724:                 messagebox.showerror("Save","Item Code must be exactly 8 digits in format 00-00-0000."); return
2725:             if not desc:
2726:                 messagebox.showerror("Save","Description is required."); return
2727:             if opening<0:
2728:                 messagebox.showerror("Save","Opening Qty cannot be less than 0."); return
2729:             rid=vals[0]
2730:             try:
2731:                 dup_code=self.conn.execute("SELECT id FROM items WHERE code=? AND id!=?",(code, rid or 0)).fetchone()
2732:                 if dup_code: raise ValueError(f"Item Code {code} already exists. Duplicate codes are not allowed.")
2733:                 dup_desc=self.conn.execute("SELECT id FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?)) AND id!=?",(desc,rid or 0)).fetchone()
2734:                 if dup_desc: raise ValueError(f"An item with the description \"{desc}\" already exists. Duplicate descriptions are not allowed.")
2735:                 if rid:
2736:                     old=self.conn.execute("SELECT code FROM items WHERE id=?",(rid,)).fetchone()
```
```text
2739:                                       (code,desc,uom,opening,rid))
2740:                     if oldcode!=code:
2741:                         for table in ("demand_lines","grr_lines","issue_lines","transactions"):
2742:                             try:self.conn.execute(f"UPDATE {table} SET code=? WHERE code=?",(code,oldcode))
2743:                             except Exception:pass
2744:                 else:
2745:                     self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level,item_type,mto_opening_qty) VALUES(?,?,?,?,?,?,?,?)",
2746:                                       (code,desc,uom,"",opening,0,"Local",0))
2747:                 self.conn.commit()
2748:                 report_path = self._save_entry_report("Inventory Code", [f"Item Code: {code}", f"Description: {desc}", f"UOM: {uom}"], ("Code","Description","UOM","Opening Qty"), [(code,desc,uom,opening)])
2749:                 backup_database(); load()
2750:                 messagebox.showinfo("Saved","Inventory Code saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
2751:             except Exception as ex:
2752:                 self.conn.rollback(); messagebox.showerror("Save Failed",str(ex))
2753: 
2754:         def delete_record():
2755:             iid=selected_row()
2756:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2757:             if not self.can_delete and not self.is_admin:
2758:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2759:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
```
```text
2755:             iid=selected_row()
2756:             if not iid: messagebox.showwarning("Delete","Select an Inventory Codes row first."); return
2757:             if not self.can_delete and not self.is_admin:
2758:                 messagebox.showwarning("Permission Denied","Your account does not have Delete permission."); return
2759:             vals=tree.item(iid,"values"); rid=vals[0]; code=vals[1]
2760:             if not rid: tree.delete(iid); status.set("New row cancelled"); return
2761:             if not messagebox.askyesno("Confirm","Delete selected record?\n\n"+str(code)): return
2762:             try:
2763:                 self.conn.execute("DELETE FROM items WHERE id=?",(rid,)); self.conn.commit(); backup_database(); load()
2764:             except Exception as ex:
2765:                 self.conn.rollback(); messagebox.showerror("Delete Error",str(ex))
2766: 
2767:         def refresh(): load()
2768:         def do_print():
2769:             try:self.preview_tree("Inventory Codes",tree)
2770:             except Exception as ex:messagebox.showerror("Print",str(ex))
2771:         def do_close(): self.dashboard()
2772: 
2773:         btn("New",new_record,8)
2774:         btn("Edit",edit_record,8)
2775:         btn("Delete",delete_record,8)
```
```text
2768:         def do_print():
2769:             try:self.preview_tree("Inventory Codes",tree)
2770:             except Exception as ex:messagebox.showerror("Print",str(ex))
2771:         def do_close(): self.dashboard()
2772: 
2773:         btn("New",new_record,8)
2774:         btn("Edit",edit_record,8)
2775:         btn("Delete",delete_record,8)
2776:         btn("Save",save_record,8)
2777:         btn("Refresh",refresh,9)
2778:         btn("Preview",do_print,8)
2779:         btn("Print",do_print,8)
2780:         btn("Close",do_close,8)
2781: 
2782:         # Search is deliberately small and sits on the right, without changing
2783:         # the reference layout of the action buttons.
2784:         tk.Label(actions,text="  Search:",bg=COLORS["bg"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=(18,2))
2785:         search=tk.StringVar()
2786:         se=tk.Entry(actions,textvariable=search,width=24,font=("Microsoft Sans Serif",9),justify="center")
2787:         se.pack(side="left",padx=2)
2788:         self._item_master_search_entry=se
```
```text
2796:                     tree.detach(iid)
2797:         search.trace_add("write",filter_grid)
2798:         tk.Label(actions,text="Ctrl+F",bg=COLORS["bg"],fg=COLORS["muted"],font=("Microsoft Sans Serif",8)).pack(side="left",padx=5)
2799: 
2800:         tree.bind("<Double-1>",edit_cell)
2801:         tree.bind("<F2>",lambda e: edit_record())
2802:         self._item_master_find_callback=lambda: (se.focus_set(),se.selection_range(0,tk.END))
2803:         self._page_actions={
2804:             "save":save_record,"edit":edit_record,"delete":delete_record,
2805:             "cancel":do_close,"print":do_print,"preview":do_print
2806:         }
2807:         load()
2808: 
2809:     def open_mto_inventory_flow(self):
2810:         """Open MTO Inventory through the same selection-criteria popup as Inventory Codes.
2811: 
2812:         The MTO list itself is NOT created until the user presses OPEN MTO INVENTORY.
2813:         Cancel/X only closes the popup.
2814:         """
2815:         criteria = self._ask_mto_inventory_filters()
2816:         if not criteria or criteria.get("cancelled"):
```
```text
2978:                 return False
2979:             destination.set(found_dest)
2980:             edit_mode.update(on=True, original=r[0], dest=found_dest)
2981:             code.set(r[0])
2982:             desc.set(r[1] or "")
2983:             uom.set(r[2] or UOM_OPTIONS[0])
2984:             opening.set(str(r[3] if r[3] is not None else 0))
2985:             opening_date.set(to_display_date(r[4]) if r[4] else opening_date.get())
2986:             hint.set(f"Loaded: {r[0]} — {r[1] or ''} ({found_dest}). Edit the details and click SAVE EDIT.")
2987:             err.set("")
2988:             edit_btn.configure(text="SAVE EDIT")
2989:             ce.focus_set()
2990:             return True
2991: 
2992:         def check_duplicates(*_):
2993:             c = code.get().strip()
2994:             d = desc.get().strip()
2995:             dest = destination.get()
2996:             msgs = []
2997:             r = row_for(dest, c) if len(norm(c)) == 8 else None
2998:             if r and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(c)):
```
```text
3000:             dh = desc_hit(dest, d) if d else None
3001:             if dh and not (edit_mode["on"] and edit_mode["dest"] == dest and norm(edit_mode["original"]) == norm(dh[0])):
3002:                 msgs.append(f'DUPLICATE DESCRIPTION: "{d}" already exists in {dest} under code {dh[0]}.')
3003:             hint.set("\n".join(msgs))
3004: 
3005:         code.trace_add("write", check_duplicates)
3006:         desc.trace_add("write", check_duplicates)
3007: 
3008:         def save_code():
3009:             try:
3010:                 c = code.get().strip()
3011:                 d = desc.get().strip()
3012:                 u = uom.get().strip()
3013:                 dest = destination.get()
3014:                 digits = norm(c)
3015:                 if len(digits) != 8:
3016:                     raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3017:                 if not d:
3018:                     raise ValueError("Description is required.")
3019:                 try:
3020:                     op = float(opening.get().strip() or 0)
```
```text
3041:                         (c, d, u, op, iso, old)
3042:                     )
3043:                     action = "updated"
3044:                 else:
3045:                     self.conn.execute(
3046:                         f"INSERT INTO {t}(code,description,uom,category,opening_qty,min_level,opening_date) VALUES(?,?,?,?,?,?,?)",
3047:                         (c, d, u, "", op, 0, iso)
3048:                     )
3049:                     action = "saved"
3050:                 self.conn.commit()
3051:                 backup_database()
3052:                 messagebox.showinfo("Code Opening", f"{c} {action} successfully in {dest}.", parent=win)
3053:                 # Keep popup open for fast multiple entries.
3054:                 clear_form(keep_search=False)
3055:                 ce.focus_set()
3056:             except Exception as ex:
3057:                 self.conn.rollback()
3058:                 err.set(str(ex))
3059:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3060: 
3061:         def edit_action():
```
```text
3057:                 self.conn.rollback()
3058:                 err.set(str(ex))
3059:                 messagebox.showerror("Code Opening", str(ex), parent=win)
3060: 
3061:         def edit_action():
3062:             if not edit_mode["on"]:
3063:                 load_for_edit()
3064:             else:
3065:                 save_code()
3066: 
3067:         def delete_code():
3068:             if not edit_mode["on"]:
3069:                 if not load_for_edit():
3070:                     return
3071:             if not messagebox.askyesno("Delete Code", f"Delete {edit_mode['original']} from {edit_mode['dest']}?", parent=win):
3072:                 return
3073:             try:
3074:                 t = table_for(edit_mode["dest"])
3075:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3076:                 self.conn.commit()
3077:                 backup_database()
```
```text
3073:             try:
3074:                 t = table_for(edit_mode["dest"])
3075:                 self.conn.execute(f"DELETE FROM {t} WHERE code=?", (edit_mode["original"],))
3076:                 self.conn.commit()
3077:                 backup_database()
3078:                 messagebox.showinfo("Delete Code", f"{edit_mode['original']} deleted from {edit_mode['dest']}.", parent=win)
3079:                 clear_form(keep_search=False)
3080:             except Exception as ex:
3081:                 self.conn.rollback()
3082:                 messagebox.showerror("Delete Code", str(ex), parent=win)
3083: 
3084:         btns = ttk.Frame(box)
3085:         btns.grid(row=8, column=0, columnspan=4, pady=(12, 0))
3086:         ttk.Button(btns, text="SAVE", style="Success.TButton", command=save_code).pack(side="left", padx=4, ipadx=8)
3087:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3088:         edit_btn.pack(side="left", padx=4, ipadx=8)
3089:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3090:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3091:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3092:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3093:         ce.focus_set()
```
```text
3087:         edit_btn = ttk.Button(btns, text="EDIT", style="Warning.TButton", command=edit_action)
3088:         edit_btn.pack(side="left", padx=4, ipadx=8)
3089:         ttk.Button(btns, text="DELETE", style="Danger.TButton", command=delete_code).pack(side="left", padx=4, ipadx=8)
3090:         ttk.Button(btns, text="CANCEL", style="Muted.TButton", command=win.destroy).pack(side="left", padx=4)
3091:         win.protocol("WM_DELETE_WINDOW", win.destroy)
3092:         win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
3093:         ce.focus_set()
3094: 
3095:     def _mto_new_item_dialog(self, on_saved):
3096:         """Small 'Add New Item Code' dialog launched from MTO Inventory, so a
3097:         brand-new item can be created without leaving that screen. Writes
3098:         straight into the same Item Master (items table) used everywhere."""
3099:         win=tk.Toplevel(self); win.title("Add New Item Code"); win.geometry("420x260"); win.resizable(False,False)
3100:         win.transient(self); win.grab_set()
3101:         f=ttk.Frame(win,padding=14); f.pack(fill="both",expand=True)
3102:         code=tk.StringVar(); desc=tk.StringVar(); uom=tk.StringVar(value=UOM_OPTIONS[0]); opening=tk.StringVar(value="0")
3103:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3104:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3105:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3106:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3107:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
```
```text
3103:         ttk.Label(f,text="Item Code (00-00-0000)").grid(row=0,column=0,sticky="w",pady=(0,2))
3104:         ent=ttk.Entry(f,textvariable=code,width=20); ent.grid(row=1,column=0,sticky="w",pady=(0,10)); attach_code_mask(ent,code)
3105:         ttk.Label(f,text="Description").grid(row=2,column=0,sticky="w",pady=(0,2))
3106:         ttk.Entry(f,textvariable=desc,width=40).grid(row=3,column=0,sticky="w",pady=(0,10))
3107:         ttk.Label(f,text="UOM").grid(row=4,column=0,sticky="w",pady=(0,2))
3108:         ttk.Combobox(f,textvariable=uom,values=UOM_OPTIONS,width=13).grid(row=5,column=0,sticky="w",pady=(0,10))
3109:         ttk.Label(f,text="Opening Qty (Open Balance)").grid(row=6,column=0,sticky="w",pady=(0,2))
3110:         ttk.Entry(f,textvariable=opening,width=15).grid(row=7,column=0,sticky="w",pady=(0,10))
3111:         def save():
3112:             try:
3113:                 c=code.get().strip(); d=desc.get().strip()
3114:                 if not c or len("".join(ch for ch in c if ch.isdigit()))!=8: raise ValueError("Item Code must be exactly 8 digits in format 00-00-0000.")
3115:                 if not d: raise ValueError("Description is required.")
3116:                 try:
3117:                     opening_val=float(opening.get() or 0)
3118:                 except ValueError:
3119:                     raise ValueError("Opening Qty must be a number.")
3120:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3121:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3122:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3123:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
```
```text
3116:                 try:
3117:                     opening_val=float(opening.get() or 0)
3118:                 except ValueError:
3119:                     raise ValueError("Opening Qty must be a number.")
3120:                 if opening_val<0: raise ValueError("Opening Qty (Open Balance) cannot be less than 0.")
3121:                 if self.conn.execute("SELECT 1 FROM items WHERE code=?",(c,)).fetchone(): raise ValueError(f"Item code {c} already exists in Item Master. Duplicate codes are not allowed.")
3122:                 if self.conn.execute("SELECT 1 FROM items WHERE LOWER(TRIM(description))=LOWER(TRIM(?))",(d,)).fetchone(): raise ValueError(f"An item with the description \"{d}\" already exists. Duplicate descriptions are not allowed.")
3123:                 self.conn.execute("INSERT INTO items(code,description,uom,category,opening_qty,min_level) VALUES(?,?,?,?,?,?)",(c,d,uom.get().strip(),"",opening_val,0))
3124:                 self.conn.commit(); backup_database()
3125:                 messagebox.showinfo("Saved",f"Item {c} added to Item Master.")
3126:                 win.grab_release(); win.destroy()
3127:                 on_saved()
3128:             except Exception as ex: messagebox.showerror("Error",str(ex))
3129:         btns=ttk.Frame(f); btns.grid(row=8,column=0,sticky="w",pady=(6,0))
3130:         ttk.Button(btns,text="SAVE",style="Success.TButton",command=save).pack(side="left",padx=(0,6))
3131:         ttk.Button(btns,text="CANCEL",command=lambda:(win.grab_release(),win.destroy())).pack(side="left")
3132: 
3133:     def _item_filter_bar(self, parent, on_change):
3134:         """Item Code entry + item-master picker + Search/Show All. Calls
3135:         on_change() whenever the code changes or a button is pressed."""
3136:         bar=ttk.Frame(parent); bar.pack(fill="x",pady=(0,6))
```
```text
3222:         self._item_master_find_callback=None
3223:         self._portable_print_context=None
3224:         criteria=getattr(self,"_mto_inventory_filter",None) or {
3225:             "from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"
3226:         }
3227: 
3228:         # MTO uses its own namespace/table, so the same code may also exist in Inventory Codes.
3229:         self.conn.execute("CREATE TABLE IF NOT EXISTS mto_items(code TEXT PRIMARY KEY, description TEXT NOT NULL, uom TEXT, category TEXT DEFAULT '', opening_qty REAL DEFAULT 0, min_level REAL DEFAULT 0, opening_date TEXT DEFAULT '')")
3230:         self.conn.commit()
3231: 
3232:         # ---- Same professional in-app window layout as Inventory Codes ----
3233:         head=ttk.Frame(body); head.pack(fill="x",pady=(0,7))
3234:         ttk.Label(head,text="MTO Inventory",font=("Segoe UI",15,"bold"),
3235:                   foreground=COLORS["primary_dark"]).pack(side="left")
3236:         ttk.Label(head,text="  MTO Inventory Code List",foreground=COLORS["muted"]).pack(side="left",padx=6)
3237: 
3238:         def open_find():
3239:             state_find={"index":-1}
3240:             def search_fn(text):
3241:                 text=text.strip().lower()
3242:                 rows=self.conn.execute("SELECT code,description FROM mto_items WHERE (LOWER(code) LIKE ? OR LOWER(description) LIKE ?) ORDER BY code",("%"+text+"%","%"+text+"%")).fetchall()
```
```text
3329:             for i in table.get_children(): table.delete(i)
3330:             where=["1=1"]; params=[]
3331:             prefix=state.get("prefix",""); q=search.get().strip()
3332:             if prefix: where.append("code LIKE ?"); params.append(prefix+"%")
3333:             if q: where.append("(LOWER(code) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"); params.extend(["%"+q+"%","%"+q+"%"])
3334:             fc=(criteria.get("from_code") or "").strip(); tc=(criteria.get("to_code") or "").strip()
3335:             if fc: where.append("code >= ?"); params.append(fc)
3336:             if tc: where.append("code <= ?"); params.append(tc)
3337:             sql="SELECT code,description,uom,COALESCE(opening_qty,0),COALESCE(opening_date,'') FROM mto_items WHERE "+" AND ".join(where)+" ORDER BY code"
3338:             df=to_iso_date((criteria.get("from_date") or "").strip()); dt=to_iso_date((criteria.get("to_date") or "").strip())
3339:             records=[]
3340:             for code,desc,uom,opening,od in self.conn.execute(sql,params):
3341:                 # If a date filter is supplied, accept an opening-date match OR
3342:                 # a transaction in that date range. This prevents valid MTO codes
3343:                 # from disappearing merely because an older record has no opening_date.
3344:                 if df or dt:
3345:                     ok=bool(od and (not df or od>=df) and (not dt or od<=dt))
3346:                     if not ok:
3347:                         txwhere=["code=?","UPPER(TRIM(COALESCE(item_type,'')))='MTO'"]; tp=[code]
3348:                         if df: txwhere.append("doc_date>=?"); tp.append(df)
3349:                         if dt: txwhere.append("doc_date<=?"); tp.append(dt)
```
```text
3419:                 tr.insert("", "end", values=r)
3420:         def clear():
3421:             for x in v.values(): x.set("")
3422:             try: tr.selection_remove(tr.selection())
3423:             except Exception: pass
3424:             self._set_form_editable(party_form_roots, False)
3425:         def new_form():
3426:             clear(); self._set_form_editable(party_form_roots, True)
3427:         def save():
3428:             try:
3429:                 name=v["name"].get().strip()
3430:                 if not name: raise ValueError("Party Name is required.")
3431:                 self.conn.execute("INSERT INTO parties(name,contact,address,remarks) VALUES(?,?,?,?) ON CONFLICT(name) DO UPDATE SET contact=excluded.contact,address=excluded.address,remarks=excluded.remarks",(name,v["contact"].get().strip(),v["address"].get().strip(),v["remarks"].get().strip()))
3432:                 self.conn.commit(); backup_database(); load(); clear(); messagebox.showinfo("Saved",f"Party '{name}' saved successfully.")
3433:             except Exception as ex: messagebox.showerror("Error",str(ex))
3434:         def load_party_row(a):
3435:             if not a:return
3436:             r=tr.item(a[0])["values"]
3437:             v["name"].set(r[1]);v["contact"].set(r[2]);v["address"].set(r[3]);v["remarks"].set(r[4])
3438:             self._set_form_editable(party_form_roots, False)
3439:         def on_party_select(_=None):
```
```text
3445:             load_party_row(a)
3446:             self._set_form_editable(party_form_roots, True)
3447:         def delete_party():
3448:             a=tr.selection()
3449:             if not a:
3450:                 messagebox.showwarning("Delete", "Select a party first."); return
3451:             pid=tr.item(a[0])["values"][0]; name=tr.item(a[0])["values"][1]
3452:             if messagebox.askyesno("Delete Party", f"Delete party '{name}'?"):
3453:                 self.conn.execute("DELETE FROM parties WHERE id=?",(pid,)); self.conn.commit(); backup_database(); load(); clear()
3454:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Party Master",tr)).grid(row=2,column=6,sticky="w",padx=8,pady=(8,0))
3455:         self.set_page_actions(save=save, edit=edit, delete=delete_party, cancel=clear, print=lambda:self.print_party_master(),preview=lambda:self.preview_tree("Party Master",tr))
3456:         self._add_transaction_new_button(new_form)
3457:         load(); clear()
3458: 
3459:     def user_management(self):
3460:         self.clearbody()
3461:         if not self.is_admin:
3462:             messagebox.showwarning("Permission Denied","Only an Admin can manage users."); self.dashboard(); return
3463:         f=ttk.LabelFrame(self.body,text="User Management (Admin Only)",padding=10); f.pack(fill="x")
3464:         v={k:tk.StringVar() for k in ("username","password","full_name")}
3465:         role=tk.StringVar(value="User")
```
```text
3502:             u_ent.state(["!disabled"])
3503:         def edit():
3504:             a=tr.selection()
3505:             if not a:
3506:                 messagebox.showwarning("Edit User","Select a user row first."); return
3507:             r=tr.item(a[0])["values"]
3508:             v["username"].set(r[0]); v["full_name"].set(r[1]); v["password"].set("")
3509:             role.set(r[2]); edit_flag.set(r[3]=="Yes"); delete_flag.set(r[4]=="Yes")
3510:             u_ent.state(["disabled"])  # username is the key; rename not supported here
3511:         def save():
3512:             try:
3513:                 username=v["username"].get().strip()
3514:                 if not username: raise ValueError("Username is required.")
3515:                 exists=self.conn.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
3516:                 pw=v["password"].get()
3517:                 if exists:
3518:                     pw_hash = hash_password(pw) if pw else exists[0]
3519:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3520:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3521:                 else:
3522:                     if not pw: raise ValueError("Password is required for a new user.")
```
```text
3517:                 if exists:
3518:                     pw_hash = hash_password(pw) if pw else exists[0]
3519:                     self.conn.execute("UPDATE users SET password=?,role=?,can_edit=?,can_delete=?,full_name=? WHERE username=?",
3520:                         (pw_hash, role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip(), username))
3521:                 else:
3522:                     if not pw: raise ValueError("Password is required for a new user.")
3523:                     self.conn.execute("INSERT INTO users(username,password,role,can_edit,can_delete,full_name) VALUES(?,?,?,?,?,?)",
3524:                         (username, hash_password(pw), role.get(), int(edit_flag.get()), int(delete_flag.get()), v["full_name"].get().strip()))
3525:                 self.conn.commit(); backup_database(); load(); clear()
3526:                 messagebox.showinfo("Saved", f"User '{username}' saved successfully.")
3527:             except Exception as ex:
3528:                 messagebox.showerror("Error", str(ex))
3529:         def delete_user():
3530:             a=tr.selection()
3531:             if not a:
3532:                 messagebox.showwarning("Delete User","Select a user row first."); return
3533:             username=tr.item(a[0])["values"][0]
3534:             if username==self.current_user:
3535:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3536:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3537:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
```
```text
3532:                 messagebox.showwarning("Delete User","Select a user row first."); return
3533:             username=tr.item(a[0])["values"][0]
3534:             if username==self.current_user:
3535:                 messagebox.showerror("Not Allowed","You cannot delete the account you are currently logged in with."); return
3536:             if self.conn.execute("SELECT COUNT(*) FROM users WHERE role='Admin'").fetchone()[0]<=1 and \
3537:                self.conn.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()[0]=="Admin":
3538:                 messagebox.showerror("Not Allowed","At least one Admin account must remain."); return
3539:             if messagebox.askyesno("Delete User", f"Delete user '{username}'?"):
3540:                 self.conn.execute("DELETE FROM users WHERE username=?",(username,)); self.conn.commit(); backup_database(); load(); clear()
3541:         ttk.Button(f,text="PREVIEW CURRENT",command=lambda:self.preview_tree("User Management",tr)).grid(row=3,column=0,sticky="w",padx=5,pady=(8,0))
3542:         self.set_page_actions(save=save, edit=edit, delete=delete_user, cancel=clear, print=None, preview=lambda:self.preview_tree("User Management",tr))
3543:         load()
3544: 
3545:     @staticmethod
3546:     def _renumber_tree(tree, rows):
3547:         for i,iid in enumerate(tree.get_children()):
3548:             vals=list(tree.item(iid,"values"));
3549:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3550: 
3551:     def demand(self):
3552:         self.clearbody(); self.demand_lines=[]
```
```text
3549:             if vals: vals[0]=i+1; tree.item(iid,values=vals)
3550: 
3551:     def demand(self):
3552:         self.clearbody(); self.demand_lines=[]
3553:         f=ttk.LabelFrame(self.body,text="Purchase Demand",padding=10); f.pack(fill="x")
3554:         v={k:tk.StringVar() for k in ["no","date","dept","required","remarks","urgency","annual","status","just","special","source"]}
3555:         v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3556:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3557:         self.document_selector(selector,"Description / Saved Demand", "demand", v["no"], lambda no: self.load_demand_into_form(no,v,tree))
3558:         # Demand Date is intentionally displayed as its own dedicated field.
3559:         ttk.Label(f,text="Demand Date (DD/MM/YYYY)").grid(row=1,column=0,sticky="w",padx=5,pady=(2,0))
3560:         self.make_date_field(f,v["date"],width=16).grid(row=2,column=0,padx=5,pady=(2,8),sticky="w")
3561:         fields=[("no","Demand No"),("dept","Department"),("required","Required For"),("remarks","Remarks"),
3562:                 ("urgency","Urgency"),("annual","Annual Demand No"),("status","Status"),("just","Justification"),
3563:                 ("special","Special Instructions"),("source","Recommended Source")]
3564:         for i,(k,n) in enumerate(fields):
3565:             r=i//4*2+3; c=i%4*2
3566:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3567:             if k=="dept":
3568:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3569:             elif k=="urgency":
```
```text
3639:         def new_form():
3640:             self._editing_document_key=None
3641:             for z in v.values(): z.set("")
3642:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["urgency"].set("Immediate"); v["status"].set("Draft")
3643:             itype.set("Local"); self.demand_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3644:             for iid in tree.get_children(): tree.delete(iid)
3645:             self._set_form_editable(form_roots, True, skip=[selector])
3646: 
3647:         def save():
3648:             try:
3649:                 no=v["no"].get().strip()
3650:                 if not no: raise ValueError("Demand No is required.")
3651:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3652:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3653:                 if dup and getattr(self,"_editing_document_key",None) != no:
3654:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3655:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3656:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3657:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3658:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3659:                 self.conn.commit()
```
```text
3652:                 dup=self.conn.execute("SELECT demand_no,demand_date FROM demands WHERE demand_no=? AND demand_date>=? AND demand_date<=?",(no,fy_start,fy_end)).fetchone()
3653:                 if dup and getattr(self,"_editing_document_key",None) != no:
3654:                     raise ValueError(f"Demand No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3655:                 if not self.demand_lines: raise ValueError("Add at least one item.")
3656:                 self.conn.execute("INSERT OR REPLACE INTO demands(demand_no,demand_date,department,required_for,remarks,urgency,status,annual_demand_no,status_date,justification,special_instructions,recommended_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),v["required"].get(),v["remarks"].get(),v["urgency"].get(),v["status"].get(),v["annual"].get(),datetime.now().strftime("%Y-%m-%d %H:%M"),v["just"].get(),v["special"].get(),v["source"].get()))
3657:                 self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,))
3658:                 for x in self.demand_lines:self.conn.execute("INSERT INTO demand_lines(demand_no,sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,*x[:7],x[9] if len(x)>9 else "Local"))
3659:                 self.conn.commit()
3660:                 report_path = self._save_entry_report("Purchase Demand", [f"Demand No: {no}", f"Demand Date: {v['date'].get()}", f"Department: {v['dept'].get()}"], ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"), self.demand_lines)
3661:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("demand"); self._set_form_editable(form_roots, False, skip=[selector])
3662:                 messagebox.showinfo("Saved",f"Demand {no} saved successfully." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3663:             except Exception as ex: messagebox.showerror("Error",str(ex))
3664:         form_roots=[f,line,editbar]
3665:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3666:         self._transaction_form_roots["demand"]=form_roots; self._transaction_form_roots["selector"]=selector
3667:         def delete_current():
3668:             no=v["no"].get().strip()
3669:             if not no or not self.conn.execute("SELECT 1 FROM demands WHERE demand_no=?",(no,)).fetchone():
3670:                 messagebox.showwarning("Delete", "Load/select a saved Demand first."); return
3671:             if not messagebox.askyesno("Delete Demand", f"Delete Demand {no}? This cannot be undone."): return
3672:             self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,)); self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,)); self.conn.commit(); backup_database()
```
```text
3685:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3686:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3687:                     f"Justification: {v['just'].get()}",
3688:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3689:             if not self.demand_lines:
3690:                 messagebox.showwarning("Preview","Add at least one item line first."); return
3691:             self.show_preview_window("Purchase Demand", header,
3692:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3693:                 self.demand_lines, [50,110,290,55,70,70,80,140,170,65], on_save=save)
3694:         def edit_saved_demand():
3695:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3696:             self._edit_from_selector("demand", v["no"], lambda no:self.load_demand_into_form(no,v,tree))
3697:             self._set_form_editable(form_roots, True, skip=[selector])
3698:         def print_now():
3699:             if not self.demand_lines:
3700:                 messagebox.showwarning("Print","Add at least one item line first."); return
3701:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3702:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3703:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3704:                     f"Justification: {v['just'].get()}",
3705:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
```
```text
3701:             header=[f"Demand No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
3702:                     f"Required For: {v['required'].get()}   Urgency: {v['urgency'].get()}   Status: {v['status'].get()}",
3703:                     f"Annual Demand No: {v['annual'].get()}   Recommended Source: {v['source'].get()}",
3704:                     f"Justification: {v['just'].get()}",
3705:                     f"Special Instructions: {v['special'].get()}   Remarks: {v['remarks'].get()}"]
3706:             self._open_direct_printer("Purchase Demand",header,
3707:                 ("Sr #","Code","Description","UOM","Demand","Available","To Purchase","Required For","Remarks","Type"),
3708:                 self.demand_lines,A4)
3709:         self.set_page_actions(save=save, edit=edit_saved_demand, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3710:         self._add_transaction_new_button(new_form)
3711:         self._set_form_editable(form_roots, False, skip=[selector])
3712:         try:
3713:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3714:         except Exception: pass
3715:         self._active_form_loader = lambda no: self.load_demand_into_form(no,v,tree)
3716: 
3717:     def load_demand_into_form(self,no,v,tree):
3718:         v["no"].set(no)
3719:         r=self.conn.execute("SELECT demand_date,department,required_for,remarks,urgency,status,annual_demand_no,justification,special_instructions,recommended_source FROM demands WHERE demand_no=?",(no,)).fetchone()
3720:         if not r:return
3721:         for k,val in zip(["date","dept","required","remarks","urgency","status","annual","just","special","source"],r):
```
```text
3723:         self.demand_lines=[]
3724:         for i in tree.get_children():tree.delete(i)
3725:         for r in self.conn.execute("SELECT sr_no,code,description,uom,demand_qty,available_qty,to_purchase,item_type FROM demand_lines WHERE demand_no=? ORDER BY sr_no",(no,)):
3726:             row=tuple(r[:7])+(v["required"].get(),v["remarks"].get(),r[7] or "Local"); self.demand_lines.append(row); tree.insert("", "end",values=row)
3727:         roots=getattr(self,"_transaction_form_roots",None)
3728:         if roots and "demand" in roots:
3729:             self._set_form_editable(roots["demand"], False, skip=[roots.get("selector")])
3730: 
3731:     def refresh_saved_cache(self,typ):
3732:         # Refresh saved-document dropdowns immediately after a successful save.
3733:         refreshers = getattr(self, "_document_selector_refreshers", {}).get(typ, [])
3734:         alive=[]
3735:         for combo, refresh in refreshers:
3736:             try:
3737:                 if combo.winfo_exists():
3738:                     refresh()
3739:                     alive.append((combo, refresh))
3740:             except Exception:
3741:                 pass
3742:         if hasattr(self, "_document_selector_refreshers"):
3743:             self._document_selector_refreshers[typ] = alive
```
```text
3742:         if hasattr(self, "_document_selector_refreshers"):
3743:             self._document_selector_refreshers[typ] = alive
3744: 
3745:     def grr(self):
3746:         self.clearbody(); self.grr_lines=[]
3747:         f=ttk.LabelFrame(self.body,text="GRN Receipt",padding=10); f.pack(fill="x")
3748:         v={k:tk.StringVar() for k in ["no","date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"]}; v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3749:         selector=ttk.Frame(f); selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3750:         self.document_selector(selector,"Description / Saved GRN", "grr", v["no"], lambda no: self.load_grr_into_form(no,v,tree))
3751:         fields=[("no","GRN No"),("date","Date"),("department","Department"),("supplier","Supplier"),("invoice","Invoice #"),("po","PO #"),("challan","Challan #"),("vehicle","Vehicle #"),("bill","Bill/Voucher #"),("ref","Reference"),("remarks","Remarks")]
3752:         for i,(k,n) in enumerate(fields):
3753:             r=i//4*2+2;c=i%4*2
3754:             ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5,pady=2)
3755:             if k=="department":
3756:                 ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3757:             elif k=="supplier":
3758:                 party_values=[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
3759:                 ttk.Combobox(f,textvariable=v[k],values=party_values,width=22).grid(row=r+1,column=c,padx=5,pady=2)
3760:             elif k=="date":
3761:                 self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3762:             else:
```
```text
3811:         def new_form():
3812:             self._editing_document_key=None
3813:             for z in v.values(): z.set("")
3814:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0]); itype.set("Local")
3815:             self.grr_lines.clear(); editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3816:             for iid in tree.get_children(): tree.delete(iid)
3817:             self._set_form_editable(form_roots, True, skip=[selector])
3818: 
3819:         def save():
3820:             try:
3821:                 no=v["no"].get().strip()
3822:                 if not no:raise ValueError("GRN No is required.")
3823:                 fy_start,fy_end=fiscal_year_range(v["date"].get())
3824:                 dup=self.conn.execute("SELECT grr_no,grr_date FROM grr WHERE grr_no=? AND grr_date>=? AND grr_date<=?",(no,fy_start,fy_end)).fetchone()
3825:                 if dup and getattr(self,"_editing_document_key",None) != no:
3826:                     raise ValueError(f"GRN No {no} already exists in fiscal year {fiscal_year_key(v["date"].get())}. Duplicate numbers are not allowed from 1 July through 30 June.")
3827:                 if not self.grr_lines:raise ValueError("Add at least one item.")
3828:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3829:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3830:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3831:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
```
```text
3828:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,))
3829:                 total=sum(float(x[8] or 0) for x in self.grr_lines)
3830:                 self.conn.execute("INSERT OR REPLACE INTO grr(grr_no,grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks,total_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["department"].get(),v["supplier"].get(),v["invoice"].get(),v["po"].get(),v["challan"].get(),v["vehicle"].get(),v["bill"].get(),v["ref"].get(),v["remarks"].get(),total))
3831:                 self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,))
3832:                 for x in self.grr_lines:
3833:                     ltype=x[10] if len(x)>10 else "Local"
3834:                     self.conn.execute("INSERT INTO grr_lines(grr_no,sr_no,code,description,uom,received_qty,rejected_qty,accepted_qty,rate,amount,item_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(no,*x[:9],ltype))
3835:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,rate,remarks,item_type) VALUES('GRR',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[6],v["supplier"].get(),v["ref"].get(),x[7],v["remarks"].get(),ltype))
3836:                 self.conn.commit()
3837:                 report_path = self._save_entry_report("GRN Receipt", [f"GRN No: {no}", f"GRN Date: {v['date'].get()}", f"Department: {v['department'].get()}", f"Supplier: {v['supplier'].get()}"], ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"), self.grr_lines)
3838:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("grr"); self._set_form_editable(form_roots, False, skip=[selector])
3839:                 messagebox.showinfo("Saved",f"GRN {no} saved. Accepted quantity added to stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
3840:             except Exception as ex:messagebox.showerror("Error",str(ex))
3841:         form_roots=[f,line,editbar]
3842:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3843:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3844:         def delete_current():
3845:             no=v["no"].get().strip()
3846:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3847:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3848:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
```
```text
3841:         form_roots=[f,line,editbar]
3842:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
3843:         self._transaction_form_roots["grr"]=form_roots; self._transaction_form_roots["grr_selector"]=selector
3844:         def delete_current():
3845:             no=v["no"].get().strip()
3846:             if not no or not self.conn.execute("SELECT 1 FROM grr WHERE grr_no=?",(no,)).fetchone():
3847:                 messagebox.showwarning("Delete", "Load/select a saved GRR first."); return
3848:             if not messagebox.askyesno("Delete GRR", f"Delete GRR {no} and its stock transaction? This cannot be undone."): return
3849:             self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,)); self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,)); self.conn.commit(); backup_database()
3850:             self.grr(); messagebox.showinfo("Deleted",f"GRR {no} deleted.")
3851:         def cancel_form():
3852:             self._editing_document_key=None
3853:             self._set_form_editable(form_roots, False, skip=[selector])
3854:             for z in v.values(): z.set("")
3855:             v["date"].set(datetime.now().strftime("%d/%m/%Y")); v["department"].set(DEPARTMENTS[0])
3856:             itype.set("Local")
3857:             self.grr_lines.clear()
3858:             editing["index"]=None; item_edit_btn.configure(text="ITEMS EDIT")
3859:             for iid in tree.get_children(): tree.delete(iid)
3860:         def preview_now():
3861:             if not self.grr_lines:
```
```text
3870:                     ("Challan #", v['challan'].get()),
3871:                     ("Vehicle #", v['vehicle'].get()),
3872:                     ("Bill/Voucher #", v['bill'].get()),
3873:                     ("Reference", v['ref'].get()),
3874:                     ("Remarks", v['remarks'].get()),
3875:                     ("Total Value", fmt_num(total))]
3876:             self.show_preview_window("GRN Receipt", header,
3877:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3878:                 self.grr_lines, [40,100,260,50,65,65,65,60,80,130,60], on_save=save)
3879:         def portable_current():
3880:             total=sum(float(x[8] or 0) for x in self.grr_lines)
3881:             return ("GRN Receipt",[("GRN No",v["no"].get()),("GRN Date",v["date"].get()),("Department",v["department"].get()),("Supplier",v["supplier"].get())],
3882:                     ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount"),self.grr_lines)
3883:         self._portable_print_context=portable_current
3884:         def edit_saved_grr():
3885:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
3886:             self._edit_from_selector("grr", v["no"], lambda no:self.load_grr_into_form(no,v,tree))
3887:             self._set_form_editable(form_roots, True, skip=[selector])
3888:         def print_now():
3889:             if not self.grr_lines:
3890:                 messagebox.showwarning("Print","Add at least one item line first."); return
```
```text
3894:                     ("Supplier", v['supplier'].get()),("Invoice #", v['invoice'].get()),
3895:                     ("PO #", v['po'].get()),("Challan #", v['challan'].get()),
3896:                     ("Vehicle #", v['vehicle'].get()),("Bill/Voucher #", v['bill'].get()),
3897:                     ("Reference", v['ref'].get()),("Remarks", v['remarks'].get()),
3898:                     ("Total Value", fmt_num(total))]
3899:             self._open_direct_printer("GRN Receipt",header,
3900:                 ("Sr #","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks","Type"),
3901:                 self.grr_lines,landscape(A4))
3902:         self.set_page_actions(save=save, edit=edit_saved_grr, delete=delete_current, cancel=cancel_form, print=print_now, preview=preview_now)
3903:         self._add_transaction_new_button(new_form)
3904:         self._set_form_editable(form_roots, False, skip=[selector])
3905:         try:
3906:             ttk.Button(self.body.winfo_children()[0],text="Preview",style="Primary.TButton",command=preview_now).pack(side="left",padx=(0,2))
3907:         except Exception: pass
3908:         self._active_form_loader = lambda no: self.load_grr_into_form(no,v,tree)
3909: 
3910:     def load_grr_into_form(self,no,v,tree):
3911:         v["no"].set(no)
3912:         r=self.conn.execute("SELECT grr_date,department,supplier,invoice_no,po_no,challan_no,vehicle_no,bill_no,ref_no,remarks FROM grr WHERE grr_no=?",(no,)).fetchone()
3913:         if not r:return
3914:         for k,val in zip(["date","department","supplier","invoice","po","challan","vehicle","bill","ref","remarks"],r):
```
```text
3921:         if roots and "grr" in roots:
3922:             self._set_form_editable(roots["grr"], False, skip=[roots.get("grr_selector")])
3923: 
3924:     def issue(self):
3925:         self.clearbody(); self.issue_lines=[]
3926:         f=ttk.LabelFrame(self.body,text="Material Issue",padding=10);f.pack(fill="x")
3927:         v={k:tk.StringVar() for k in ["no","date","dept","items_use_for"]};v["date"].set(datetime.now().strftime("%d/%m/%Y"));v["dept"].set(DEPARTMENTS[0])
3928:         selector=ttk.Frame(f);selector.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,8))
3929:         self.document_selector(selector,"Description / Saved Material Issue", "issue", v["no"], lambda no:self.load_issue_into_form(no,v,tree))
3930:         for i,(k,n) in enumerate([("no","Issue No"),("date","Date"),("dept","Department")]):
3931:             r=i//4*2+2;c=i%4*2;ttk.Label(f,text=n).grid(row=r,column=c,sticky="w",padx=5)
3932:             if k=="dept": ttk.Combobox(f,textvariable=v[k],values=DEPARTMENTS,state="readonly",width=22).grid(row=r+1,column=c,padx=5,pady=2)
3933:             elif k=="date": self.make_date_field(f,v[k],width=16).grid(row=r+1,column=c,padx=5,pady=2,sticky="w")
3934:             else: ttk.Entry(f,textvariable=v[k],width=25).grid(row=r+1,column=c,padx=5,pady=2)
3935:         usebar=ttk.Frame(self.body);usebar.pack(fill="x",pady=(4,2))
3936:         ttk.Label(usebar,text="Items Use For",font=("Segoe UI",9,"bold")).pack(side="left",padx=(5,8))
3937:         ttk.Entry(usebar,textvariable=v["items_use_for"],width=85).pack(side="left",fill="x",expand=True,padx=4)
3938:         ttk.Label(usebar,text="(Enter any purpose / description)",foreground="#666").pack(side="left",padx=5)
3939:         line=ttk.Frame(self.body);line.pack(fill="x",pady=8)
3940:         code=tk.StringVar();desc=tk.StringVar();uom=tk.StringVar();qty=tk.StringVar();bal=tk.StringVar(value="0")
3941:         itype=tk.StringVar(value="Local")
```
```text
4010:                 # Editing an existing issue replaces its old stock transaction and detail lines.
4011:                 self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,))
4012:                 self.conn.execute("INSERT OR REPLACE INTO issues(issue_no,issue_date,department,reference,remarks,items_use_for) VALUES(?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),v["dept"].get(),"","",v["items_use_for"].get()))
4013:                 self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,))
4014:                 for x in self.issue_lines:
4015:                     ltype=x[7] if len(x)>7 else "Local"
4016:                     self.conn.execute("INSERT INTO issue_lines(issue_no,sr_no,code,description,uom,issue_qty,a_c_unit,remarks,item_type) VALUES(?,?,?,?,?,?,?,?,?)",(no,x[0],x[1],x[2],x[3],x[4],"","",ltype))
4017:                     self.conn.execute("INSERT INTO transactions(doc_type,doc_no,doc_date,code,qty,party,ref_no,a_c_unit,remarks,item_type) VALUES('ISSUE',?,?,?,?,?,?,?,?,?)",(no,to_iso_date(v["date"].get()),x[1],x[4],v["dept"].get(),"","","",ltype))
4018:                 self.conn.commit()
4019:                 report_path = self._save_entry_report("Material Issue", [f"Issue No: {no}", f"Issue Date: {v['date'].get()}", f"Department: {v['dept'].get()}", f"Items Use For: {v['items_use_for'].get()}"], ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"), self.issue_lines)
4020:                 backup_database(); self._editing_document_key=None; self.refresh_saved_cache("issue"); self._set_form_editable(form_roots, False, skip=[selector])
4021:                 messagebox.showinfo("Posted",f"Material Issue {no} posted. Quantity deducted from stock." + (f"\n\nReport saved to:\n{report_path}" if report_path else "\n\nWarning: PDF report could not be generated; the saved data is retained."))
4022:             except Exception as ex:messagebox.showerror("Error",str(ex))
4023:         def delete_current():
4024:             no=v["no"].get().strip()
4025:             if not no or not self.conn.execute("SELECT 1 FROM issues WHERE issue_no=?",(no,)).fetchone():
4026:                 messagebox.showwarning("Delete", "Load/select a saved Material Issue first."); return
4027:             if not messagebox.askyesno("Delete Material Issue", f"Delete Material Issue {no} and restore its stock? This cannot be undone."): return
4028:             self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,)); self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,)); self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,)); self.conn.commit(); backup_database()
4029:             self.issue(); messagebox.showinfo("Deleted",f"Material Issue {no} deleted.")
4030:         def cancel_form():
```
```text
4038:             for iid in tree.get_children(): tree.delete(iid)
4039:         def preview_now():
4040:             if not self.issue_lines:
4041:                 messagebox.showwarning("Preview","Add at least one item line first."); return
4042:             header=[f"Issue No: {v['no'].get() or '(not set)'}   Date: {v['date'].get()}   Department: {v['dept'].get()}",
4043:                     f"Items Use For: {v['items_use_for'].get()}"]
4044:             self.show_preview_window("Material Issue", header,
4045:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),
4046:                 self.issue_lines, [40,110,290,55,70,90,190,60], on_save=post)
4047:         def portable_current():
4048:             return ("Material Issue / SIR",[("SIR #",v["no"].get()),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())],
4049:                     ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines)
4050:         self._portable_print_context=portable_current
4051:         form_roots=[f,usebar,line,editbar]
4052:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4053:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4054:         def load_saved_issue(no):
4055:             self.load_issue_into_form(no,v,tree)
4056:             self._set_form_editable(form_roots, False, skip=[selector])
4057:         def edit_saved_issue():
4058:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
```
```text
4051:         form_roots=[f,usebar,line,editbar]
4052:         if not hasattr(self,"_transaction_form_roots"): self._transaction_form_roots={}
4053:         self._transaction_form_roots["issue"]=form_roots; self._transaction_form_roots["issue_selector"]=selector
4054:         def load_saved_issue(no):
4055:             self.load_issue_into_form(no,v,tree)
4056:             self._set_form_editable(form_roots, False, skip=[selector])
4057:         def edit_saved_issue():
4058:             self._editing_document_key=v["no"].get().strip().split(" -> ",1)[0] if v["no"].get().strip() else None
4059:             self._edit_from_selector("issue", v["no"], load_saved_issue)
4060:             self._set_form_editable(form_roots, True, skip=[selector])
4061:         def print_issue_now():
4062:             if not self.issue_lines:
4063:                 messagebox.showwarning("Print","Add at least one item line first."); return
4064:             header=[("SIR #",v["no"].get() or "(not set)"),("SIR Date",v["date"].get()),("Department",v["dept"].get()),("Items Use For",v["items_use_for"].get())]
4065:             self._open_direct_printer("Material Issue",header,
4066:                 ("Sr #","Code","Description","UOM","Issue Qty","Balance After","Items Use For","Type"),self.issue_lines,A4)
4067:         self.set_page_actions(save=post, edit=edit_saved_issue, delete=delete_current, cancel=cancel_form, print=print_issue_now, preview=preview_now)
4068:         self._add_transaction_new_button(new_form)
4069:         self._set_form_editable(form_roots, False, skip=[selector])
4070:         self._active_form_loader = load_saved_issue
4071: 
```
```text
4079:         for i in tree.get_children():tree.delete(i)
4080:         for r in self.conn.execute("SELECT sr_no,code,description,uom,issue_qty,item_type FROM issue_lines WHERE issue_no=? ORDER BY sr_no",(no,)):
4081:             vals=tuple(r[:5]);code=vals[1];after=stock(self.conn,code)+float(self.conn.execute("SELECT COALESCE(SUM(issue_qty),0) FROM issue_lines WHERE issue_no=? AND code=?",(no,code)).fetchone()[0] or 0)-sum(float(x[4]) for x in self.issue_lines if x[1]==code)-float(vals[4])
4082:             row=(*vals,after,v["items_use_for"].get(),r[5] or "Local");self.issue_lines.append(row);tree.insert("", "end",values=row)
4083:         roots=getattr(self,"_transaction_form_roots",None)
4084:         if roots and "issue" in roots:
4085:             self._set_form_editable(roots["issue"], False, skip=[roots.get("issue_selector")])
4086: 
4087:     def _ask_report_criteria(self, report_title, button_text="OPEN REPORT", include_zero=False, include_party=False, document_label=None, document_key=None):
4088:         """Show a real modal criteria popup BEFORE creating the report MDI child.
4089: 
4090:         The layout intentionally matches Inventory Codes' Selection Criteria
4091:         popup so all Report sub-sections have one consistent desktop workflow.
4092:         """
4093:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include","party":"ALL","from_document":"","to_document":""}
4094:         win=tk.Toplevel(self)
4095:         win.title(f"{report_title} - Selection Criteria")
4096:         win.resizable(False,False)
4097:         win.transient(self); win.grab_set()
4098:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4099:         tk.Label(head,text=f"{report_title.upper()} - SELECTION CRITERIA",
```
```text
4144:             except Exception: pass
4145:         btns=ttk.Frame(box); btns.grid(row=next_row,column=0,columnspan=2,pady=(22,0))
4146:         ttk.Button(btns,text=button_text,style="Success.TButton",command=lambda:finish(False)).pack(side="left",padx=6,ipadx=8)
4147:         ttk.Button(btns,text="CANCEL",style="Muted.TButton",command=lambda:finish(True)).pack(side="left",padx=6)
4148:         win.protocol("WM_DELETE_WINDOW",lambda:finish(True)); win.bind("<Escape>",lambda e:finish(True)); win.bind("<Return>",lambda e:finish(False))
4149:         win.update_idletasks(); w=max(500,win.winfo_reqwidth()); h=max(430,win.winfo_reqheight()); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight(); win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4150:         e1.focus_set(); self.wait_window(win); return result
4151: 
4152:     def _open_report_child(self, method, title, criteria, geometry="1400x820"):
4153:         self._pending_report_filters=criteria
4154:         try:
4155:             return self.open_menu_window(method,title,geometry)
4156:         finally:
4157:             self._pending_report_filters=None
4158: 
4159:     def open_stock_balance_report_flow(self):
4160:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4161:         if f.get("cancelled"): return None
4162:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4163: 
4164:     def open_grr_report_flow(self):
```
```text
4157:             self._pending_report_filters=None
4158: 
4159:     def open_stock_balance_report_flow(self):
4160:         f=self._ask_report_criteria("Stock Balance", "OPEN STOCK BALANCE", include_zero=True)
4161:         if f.get("cancelled"): return None
4162:         return self._open_report_child(self.stock_balance,"Stock Balance",f)
4163: 
4164:     def open_grr_report_flow(self):
4165:         f=self._ask_report_criteria("GRN Report", "OPEN REPORT", document_label="GRN No", document_key="grr_no")
4166:         if f.get("cancelled"): return None
4167:         return self._open_report_child(self.report_grr,"GRN Report",f)
4168: 
4169:     def open_demand_report_flow(self):
4170:         f=self._ask_report_criteria("Demand Report", "OPEN REPORT", document_label="Demand No", document_key="demand_no")
4171:         if f.get("cancelled"): return None
4172:         return self._open_report_child(self.report_demand,"Demand Report",f)
4173: 
4174:     def open_issue_report_flow(self):
4175:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4176:         if f.get("cancelled"): return None
4177:         return self._open_report_child(self.report_issue,"Issue Report",f)
```
```text
4171:         if f.get("cancelled"): return None
4172:         return self._open_report_child(self.report_demand,"Demand Report",f)
4173: 
4174:     def open_issue_report_flow(self):
4175:         f=self._ask_report_criteria("Issue Report", "OPEN REPORT")
4176:         if f.get("cancelled"): return None
4177:         return self._open_report_child(self.report_issue,"Issue Report",f)
4178: 
4179:     def open_party_report_flow(self):
4180:         f=self._ask_report_criteria("Party Report", "OPEN REPORT", include_party=True)
4181:         if f.get("cancelled"): return None
4182:         return self._open_report_child(self.report_party,"Party Report",f)
4183: 
4184:     def _ask_stock_balance_filters(self):
4185:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","zero_mode":"include"}
4186:         win=tk.Toplevel(self); win.title("Stock Balance - Selection Criteria"); win.resizable(False,False)
4187:         head=tk.Frame(win,bg=COLORS["primary_dark"]); head.pack(fill="x")
4188:         tk.Label(head,text="STOCK BALANCE - SELECTION CRITERIA",font=("Segoe UI",13,"bold"),bg=COLORS["primary_dark"],fg="white",padx=16,pady=12).pack(anchor="w")
4189:         box=ttk.Frame(win,padding=22); box.pack(fill="both",expand=True)
4190:         ttk.Label(box,text="Select Item Code and Date range. Leave a field blank to skip that filter.").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4191:         fc=tk.StringVar(); tc=tk.StringVar(); fd=tk.StringVar(); td=tk.StringVar(); zm=tk.StringVar(value="include")
```
```text
4203:         ttk.Button(bf,text="OPEN STOCK BALANCE",style="Success.TButton",command=ok).pack(side="left",padx=5)
4204:         ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4205:         win.protocol("WM_DELETE_WINDOW",cancel);win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel())
4206:         win.update_idletasks();w=win.winfo_reqwidth();h=win.winfo_reqheight();sw=win.winfo_screenwidth();sh=win.winfo_screenheight();win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
4207:         e1.focus_set();self.wait_window(win);return result
4208: 
4209:     def stock_balance(self):
4210:         self.clearbody()
4211:         # Stock Balance is a Report sub-section and does not use the generic
4212:         # Save/Edit/Delete/Cancel/Print action strip.
4213:         children=self.body.winfo_children()
4214:         if children:
4215:             children[0].destroy()
4216:         initial=getattr(self,"_pending_report_filters",None) or self._ask_stock_balance_filters()
4217:         if initial.get("cancelled"):
4218:             self.dashboard(); return
4219:         top=ttk.Frame(self.body);top.pack(fill="x")
4220:         ttk.Label(top,text="FULL STOCK / ALL ITEM BALANCES",font=("Segoe UI",15,"bold")).pack(side="left")
4221:         ttk.Button(top,text="FILTERS",style="Accent.TButton",command=lambda:reopen_filters()).pack(side="left",padx=8)
4222:         ttk.Button(top,text="EXPORT / PREVIEW",style="Success.TButton",command=lambda:self.preview_tree("Stock Balance",tr,header_summary())).pack(side="left",padx=4)
4223:         tr=self.make_tree(self.body,("Code","Description","UOM","Opening","GRN In","Issue Out","Current Balance","Minimum","Status"),[150,430,75,100,100,100,135,90,100])
```
```text
4233:             for typ,qty in self.conn.execute(q,params):
4234:                 if typ=="GRR":gr+=float(qty or 0)
4235:                 elif typ=="ISSUE":iss+=float(qty or 0)
4236:             return opening_before,gr,iss,opening_before+gr-iss
4237:         def header_summary():
4238:             return [f"Item Code: {from_code.get() or 'FIRST'} to {to_code.get() or 'LAST'}",f"Date: {from_date.get() or 'ALL'} to {to_date.get() or 'TODAY'}",f"Zero Balance: {'Included' if zero_mode.get()=='include' else 'Excluded'}"]
4239:         def load():
4240:             for i in tr.get_children():tr.delete(i)
4241:             sql="SELECT code,description,uom,opening_qty,min_level FROM items WHERE 1=1";params=[]
4242:             if from_code.get():sql+=" AND code>=?";params.append(from_code.get())
4243:             if to_code.get():sql+=" AND code<=?";params.append(to_code.get())
4244:             sql+=" ORDER BY code"
4245:             for r in self.conn.execute(sql,params):
4246:                 op,gr,iss,cur=period(r[0],r[3])
4247:                 if zero_mode.get()=="exclude" and abs(cur)<1e-12:continue
4248:                 tr.insert("","end",values=(r[0],r[1],r[2],fmt_num(op),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=float(r[4] or 0) else "OK"))
4249:         def reopen_filters():
4250:             initial2=self._ask_stock_balance_filters()
4251:             if initial2.get("cancelled"):return
4252:             for var,key in ((from_code,"from_code"),(to_code,"to_code"),(from_date,"from_date"),(to_date,"to_date"),(zero_mode,"zero_mode")):var.set(initial2[key])
4253:             load()
```
```text
4291:         """
4292:         if typ=="demand": self.demand()
4293:         elif typ=="grr": self.grr()
4294:         else: self.issue()
4295:         loader=getattr(self,"_active_form_loader",None)
4296:         if loader: loader(str(no))
4297: 
4298:     def _edit_from_selector(self, typ, var, loader):
4299:         """Top Edit action: load the saved document directly into the current form.
4300:         If nothing is selected, use the newest saved document; never open a popup.
4301:         """
4302:         text=var.get().strip()
4303:         if text:
4304:             no=text.split(" -> ",1)[0].strip()
4305:         else:
4306:             table={"demand":"demands","grr":"grr","issue":"issues"}[typ]
4307:             col={"demand":"demand_no","grr":"grr_no","issue":"issue_no"}[typ]
4308:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4309:             if not r:
4310:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4311:                 return
```
```text
4308:             r=self.conn.execute(f"SELECT {col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
4309:             if not r:
4310:                 messagebox.showwarning("Edit", "No saved record is available to edit.")
4311:                 return
4312:             no=str(r[0])
4313:             var.set(no)
4314:         loader(no)
4315: 
4316:     def show_saved_records(self,typ):
4317:         win=tk.Toplevel(self);win.title({"demand":"Saved Purchase Demands","grr":"Saved GRNs / Receipts","issue":"Saved Material Issues"}[typ]);win.geometry("1100x620")
4318:         if typ=="demand":
4319:             cols=("Demand No","Date","Department","Required For","Urgency","Status","Total Qty")
4320:             tr=self.make_tree(win,cols,[150,110,190,190,110,130,100])
4321:             rows=self.conn.execute("SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC")
4322:             for r in rows:
4323:                 total=self.conn.execute("SELECT COALESCE(SUM(demand_qty),0) FROM demand_lines WHERE demand_no=?",(r[0],)).fetchone()[0]
4324:                 r=list(r); r[1]=to_display_date(r[1])
4325:                 tr.insert("", "end", values=(*r,fmt_num(total)))
4326:         elif typ=="grr":
4327:             cols=("GRN No","Date","Department","Supplier","Invoice","PO","Total Value")
4328:             tr=self.make_tree(win,cols,[130,110,160,230,130,110,120])
```
```text
4339:         def view():
4340:             a=tr.selection()
4341:             if not a:return
4342:             no=tr.item(a[0])["values"][0]
4343:             win.destroy();self.open_document_editor(typ,no)
4344:         bar=ttk.Frame(win);bar.pack(fill="x",pady=8)
4345:         ttk.Button(bar,text="EDIT",command=view).pack(side="left",padx=5)
4346:         ttk.Button(bar,text="PREVIEW / PRINT",command=lambda:self.doc_print_selected(typ,tr)).pack(side="left",padx=5)
4347:         ttk.Button(bar,text="REFRESH",command=lambda:(win.destroy(),self.show_saved_records(typ))).pack(side="left",padx=5)
4348: 
4349:     def documents(self):
4350:         self.clearbody()
4351:         nb=ttk.Notebook(self.body);nb.pack(fill="both",expand=True)
4352:         specs=[
4353:             ("Demands","demand",("No","Date","Department","Required For","Urgency","Status"),
4354:              "SELECT demand_no,demand_date,department,required_for,urgency,status FROM demands ORDER BY rowid DESC"),
4355:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4356:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4357:             ("Material Issues","issue",("No","Date","Department"),
4358:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4359:         ]
```
```text
4355:             ("GRNs","grr",("No","Date","Department","Supplier","Invoice","PO","Total Value"),
4356:              "SELECT grr_no,grr_date,department,supplier,invoice_no,po_no,total_value FROM grr ORDER BY rowid DESC"),
4357:             ("Material Issues","issue",("No","Date","Department"),
4358:              "SELECT issue_no,issue_date,department FROM issues ORDER BY rowid DESC")
4359:         ]
4360:         for title,typ,cols,query in specs:
4361:             fr=ttk.Frame(nb,padding=8);nb.add(fr,text=title)
4362:             count=self.conn.execute({"demand":"SELECT COUNT(*) FROM demands","grr":"SELECT COUNT(*) FROM grr","issue":"SELECT COUNT(*) FROM issues"}[typ]).fetchone()[0]
4363:             ttk.Label(fr,text=f"Saved {title}: {count}",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
4364:             bar=ttk.Frame(fr);bar.pack(fill="x",pady=(0,7))
4365:             tr=self.make_tree(fr,cols,[150,110,180,190,120,120,120])
4366:             for r in self.conn.execute(query):
4367:                 r=list(r); r[1]=to_display_date(r[1]); tr.insert("", "end",values=r)
4368:             def edit_selected(t=tr,k=typ):
4369:                 a=t.selection()
4370:                 if not a:
4371:                     messagebox.showwarning("Edit", "Select a saved record first.")
4372:                     return
4373:                 no=t.item(a[0])["values"][0]
4374:                 self.open_document_editor(k,no)
4375:             def delete_selected(t=tr,k=typ):
```
```text
4370:                 if not a:
4371:                     messagebox.showwarning("Edit", "Select a saved record first.")
4372:                     return
4373:                 no=t.item(a[0])["values"][0]
4374:                 self.open_document_editor(k,no)
4375:             def delete_selected(t=tr,k=typ):
4376:                 a=t.selection()
4377:                 if not a:
4378:                     messagebox.showwarning("Delete", "Select a saved record first.")
4379:                     return
4380:                 no=t.item(a[0])["values"][0]
4381:                 if k=="demand":
4382:                     self.conn.execute("DELETE FROM demand_lines WHERE demand_no=?",(no,));self.conn.execute("DELETE FROM demands WHERE demand_no=?",(no,))
4383:                 elif k=="grr":
4384:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4385:                 else:
4386:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4387:                 self.conn.commit();backup_database();self.documents()
4388:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4389:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4390:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
```
```text
4384:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='GRR' AND doc_no=?",(no,));self.conn.execute("DELETE FROM grr_lines WHERE grr_no=?",(no,));self.conn.execute("DELETE FROM grr WHERE grr_no=?",(no,))
4385:                 else:
4386:                     self.conn.execute("DELETE FROM transactions WHERE doc_type='ISSUE' AND doc_no=?",(no,));self.conn.execute("DELETE FROM issue_lines WHERE issue_no=?",(no,));self.conn.execute("DELETE FROM issues WHERE issue_no=?",(no,))
4387:                 self.conn.commit();backup_database();self.documents()
4388:             b=ttk.Button(bar,text="EDIT",command=edit_selected);b.pack(side="left",padx=4)
4389:             ttk.Button(bar,text="DELETE",command=delete_selected).pack(side="left",padx=4)
4390:             ttk.Button(bar,text="PREVIEW SELECTED",command=lambda t=tr,k=typ:self.doc_preview_selected(k,t)).pack(side="left",padx=4)
4391:             ttk.Button(bar,text="PREVIEW CURRENT",command=lambda t=tr,tt=title:self.preview_tree(tt + " - Current List",t)).pack(side="left",padx=4)
4392:             ttk.Button(bar,text="EXPORT PDF",command=lambda t=tr,k=typ:self.doc_print_selected(k,t)).pack(side="left",padx=4)
4393:             ttk.Button(bar,text="EXPORT WORD",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"word")).pack(side="left",padx=4)
4394:             ttk.Button(bar,text="EXPORT EXCEL",command=lambda t=tr,k=typ:self.doc_export_selected(k,t,"excel")).pack(side="left",padx=4)
4395: 
4396:     def doc_export_selected(self,typ,tr,fmt):
4397:         a=tr.selection()
4398:         if not a:
4399:             messagebox.showwarning("Export","Select a saved record first."); return
4400:         no=tr.item(a[0])["values"][0]
4401:         if fmt=="word": self.export_word(typ,no)
4402:         else: self.export_excel(typ,no)
4403: 
4404:     def doc_preview_selected(self,typ,tr):
```
```text
4399:             messagebox.showwarning("Export","Select a saved record first."); return
4400:         no=tr.item(a[0])["values"][0]
4401:         if fmt=="word": self.export_word(typ,no)
4402:         else: self.export_excel(typ,no)
4403: 
4404:     def doc_preview_selected(self,typ,tr):
4405:         a=tr.selection()
4406:         if not a:
4407:             messagebox.showwarning("Preview","Select a saved record first."); return
4408:         no=tr.item(a[0])["values"][0]
4409:         data=self._get_doc_data(typ,no)
4410:         if not data:
4411:             messagebox.showwarning("Preview","Document not found."); return
4412:         title,header,cols,rows=data
4413:         header_lines=header
4414:         self.show_preview_window(title,header_lines,cols,rows)
4415: 
4416:     def doc_print_selected(self,typ,tr):
4417:         a=tr.selection()
4418:         if not a: return
4419:         no=tr.item(a[0])["values"][0]
```
```text
4450:         def _print_loaded_document():
4451:             data=self._get_doc_data(typ,no)
4452:             if not data:
4453:                 messagebox.showwarning("Document","Document not found."); return
4454:             title,header,cols,rows=data
4455:             self._open_direct_printer(title,header,cols,rows,landscape(A4) if typ=="grr" else A4)
4456:         ttk.Button(win,text="PREVIEW / PRINT",command=_print_loaded_document).pack(pady=8)
4457: 
4458:     def _report_filter_popup(self, title, include_party=False):
4459:         result={"cancelled":False,"from_code":"","to_code":"","from_date":"","to_date":"","party":"ALL"}
4460:         win,winbody=self._internal_window(title,"520x420")
4461:         done=tk.BooleanVar(value=False)
4462:         box=ttk.Frame(winbody,padding=20);box.pack(fill="both",expand=True)
4463:         ttk.Label(box,text=title.upper(),font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,14))
4464:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4465:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4466:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4467:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4468:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4469:         if include_party:
4470:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
```
```text
4464:         fc=tk.StringVar();tc=tk.StringVar();fd=tk.StringVar();td=tk.StringVar();party=tk.StringVar(value="ALL")
4465:         ttk.Label(box,text="Item Code From").grid(row=1,column=0,sticky="w",pady=6);e=ttk.Entry(box,textvariable=fc,width=18);e.grid(row=1,column=1,sticky="w",pady=6);attach_code_mask(e,fc)
4466:         ttk.Label(box,text="Item Code To").grid(row=2,column=0,sticky="w",pady=6);e2=ttk.Entry(box,textvariable=tc,width=18);e2.grid(row=2,column=1,sticky="w",pady=6);attach_code_mask(e2,tc)
4467:         ttk.Label(box,text="Date From (DD/MM/YYYY)").grid(row=3,column=0,sticky="w",pady=6);self.make_date_field(box,fd,16).grid(row=3,column=1,sticky="w",pady=6)
4468:         ttk.Label(box,text="Date To (DD/MM/YYYY)").grid(row=4,column=0,sticky="w",pady=6);self.make_date_field(box,td,16).grid(row=4,column=1,sticky="w",pady=6)
4469:         if include_party:
4470:             ttk.Label(box,text="Party").grid(row=5,column=0,sticky="w",pady=6);ttk.Combobox(box,textvariable=party,values=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")],state="readonly",width=35).grid(row=5,column=1,sticky="w",pady=6)
4471:         def ok():
4472:             result.update(from_code=fc.get().strip(),to_code=tc.get().strip(),from_date=fd.get().strip(),to_date=td.get().strip(),party=party.get());done.set(True);win._internal_close()
4473:         def cancel():result["cancelled"]=True;done.set(True);win._internal_close()
4474:         bf=ttk.Frame(box);bf.grid(row=6,column=0,columnspan=2,pady=(14,0));ttk.Button(bf,text="OPEN REPORT",style="Success.TButton",command=ok).pack(side="left",padx=5);ttk.Button(bf,text="CANCEL",style="Muted.TButton",command=cancel).pack(side="left",padx=5)
4475:         win.bind("<Return>",lambda e:ok());win.bind("<Escape>",lambda e:cancel());e.focus_set();self.wait_variable(done);return result
4476: 
4477:     def _report_window(self,title,kind,headers,query,params_builder,include_party=False):
4478:         self.clearbody()
4479:         # Report sub-sections use their own report toolbar; remove only the
4480:         # generic Save/Edit/Delete/Cancel/Print action strip created by clearbody.
4481:         children=self.body.winfo_children()
4482:         if children:
4483:             children[0].destroy()
4484:         f=getattr(self,"_pending_report_filters",None) or self._report_filter_popup(f"{title} - Filters",include_party)
```
```text
4485:         if f.get("cancelled"):
4486:             self.dashboard();return
4487:         bar=ttk.Frame(self.body);bar.pack(fill="x",pady=(0,8))
4488:         ttk.Label(bar,text=title,font=("Segoe UI",15,"bold")).pack(side="left")
4489:         tr=self.make_tree(self.body,headers,[max(90,min(320,10*len(str(h))+35)) for h in headers])
4490:         def load():
4491:             for i in tr.get_children():tr.delete(i)
4492:             params,where=params_builder(f)
4493:             sql=query+(" WHERE "+" AND ".join(where) if where else "")
4494:             for r in self.conn.execute(sql,params):
4495:                 vals=list(r)
4496:                 if vals and isinstance(vals[0],str):vals[0]=to_display_date(vals[0])
4497:                 tr.insert("","end",values=vals)
4498:         def hdr():return [f"Item Code: {f['from_code'] or 'FIRST'} to {f['to_code'] or 'LAST'}",f"Date: {f['from_date'] or 'ALL'} to {f['to_date'] or 'TODAY'}"]
4499:         ttk.Button(bar,text="REFRESH",style="Muted.TButton",command=load).pack(side="left",padx=6)
4500:         ttk.Button(bar,text="PDF",style="Primary.TButton",command=lambda:self.export_preview_pdf(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4501:         ttk.Button(bar,text="EXCEL",style="Success.TButton",command=lambda:self.export_preview_excel(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4502:         ttk.Button(bar,text="WORD",style="Warning.TButton",command=lambda:self.export_preview_word(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()])).pack(side="left",padx=3)
4503:         ttk.Button(bar,text="PREVIEW",style="Muted.TButton",command=lambda:self.preview_tree(title,tr,hdr())).pack(side="left",padx=3)
4504:         def open_find_report():
4505:             state_find={"index":-1}
```
```text
4511:                 order=children[start:]+children[:start]
4512:                 for iid in order:
4513:                     vals=tr.item(iid,"values")
4514:                     if any(text in str(v).lower() for v in vals):
4515:                         state_find["index"]=children.index(iid)
4516:                         tr.selection_set(iid); tr.focus(iid); tr.see(iid); return True
4517:                 return False
4518:             self._open_exact_find_text_popup(search_fn)
4519:         self._item_master_find_callback=open_find_report
4520:         load()
4521:         self.set_page_actions(preview=lambda:self.preview_tree(title,tr,hdr()),print=lambda:self.print_preview_window(title,hdr(),headers,[tuple(tr.item(i,"values")) for i in tr.get_children()]))
4522: 
4523:     def report_grr(self):
4524:         q="""SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4525:         def pb(f):
4526:             w=[];p=[]
4527:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4528:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4529:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4530:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4531:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
```
```text
4526:             w=[];p=[]
4527:             if f.get('from_document'):w.append('g.grr_no>=?');p.append(f['from_document'])
4528:             if f.get('to_document'):w.append('g.grr_no<=?');p.append(f['to_document'])
4529:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4530:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4531:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4532:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4533:             return p,w
4534:         self._report_window("GRN DETAIL REPORT","grr",("Date","GRN No","Department","Party","Invoice","Item Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks"),q,pb)
4535: 
4536:     def report_demand(self):
4537:         q="""SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase,l.item_type FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"""
4538:         def pb(f):
4539:             w=[];p=[]
4540:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4541:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4542:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4543:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4544:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4545:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4546:             return p,w
```
```text
4539:             w=[];p=[]
4540:             if f.get('from_document'):w.append('d.demand_no>=?');p.append(f['from_document'])
4541:             if f.get('to_document'):w.append('d.demand_no<=?');p.append(f['to_document'])
4542:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4543:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4544:             if f['from_date']:w.append('d.demand_date>=?');p.append(to_iso_date(f['from_date']))
4545:             if f['to_date']:w.append('d.demand_date<=?');p.append(to_iso_date(f['to_date']))
4546:             return p,w
4547:         self._report_window("DEMAND DETAIL REPORT","demand",("Date","Demand No","Department","Required For","Remarks","Status","Item Code","Description","UOM","Demand Qty","Available","To Purchase","Type"),q,pb)
4548: 
4549:     def report_issue(self):
4550:         q="""SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"""
4551:         def pb(f):
4552:             w=[];p=[]
4553:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4554:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4555:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4556:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4557:             return p,w
4558:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4559: 
```
```text
4552:             w=[];p=[]
4553:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4554:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4555:             if f['from_date']:w.append('i.issue_date>=?');p.append(to_iso_date(f['from_date']))
4556:             if f['to_date']:w.append('i.issue_date<=?');p.append(to_iso_date(f['to_date']))
4557:             return p,w
4558:         self._report_window("MATERIAL ISSUE DETAIL REPORT","issue",("Date","Issue No","Department","Items Use For","Item Code","Description","UOM","Issue Qty","Type"),q,pb)
4559: 
4560:     def report_party(self):
4561:         q="""SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"""
4562:         def pb(f):
4563:             w=[];p=[]
4564:             if f['from_code']:w.append('l.code>=?');p.append(f['from_code'])
4565:             if f['to_code']:w.append('l.code<=?');p.append(f['to_code'])
4566:             if f['from_date']:w.append('g.grr_date>=?');p.append(to_iso_date(f['from_date']))
4567:             if f['to_date']:w.append('g.grr_date<=?');p.append(to_iso_date(f['to_date']))
4568:             if f['party'] and f['party']!='ALL':w.append('g.supplier=?');p.append(f['party'])
4569:             return p,w
4570:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4571: 
4572:     def reports(self):
```
```text
4570:         self._report_window("PARTY DETAIL REPORT","party",("Date","GRN No","Party","Department","Invoice","Item Code","Description","Qty","Rate","Amount"),q,pb,True)
4571: 
4572:     def reports(self):
4573:         self.clearbody()
4574:         nb=ttk.Notebook(self.body); nb.pack(fill="both",expand=True)
4575: 
4576:         # ================= GRN Details =================
4577:         grr_fr=ttk.Frame(nb,padding=4); nb.add(grr_fr,text="GRN Details")
4578:         ttk.Button(grr_fr,text="PRINT FULL GRN DETAILS",command=lambda:self.print_report("grr")).pack(anchor="w",pady=(0,4))
4579:         grr_nb=ttk.Notebook(grr_fr); grr_nb.pack(fill="both",expand=True)
4580:         grr_cols=("Date","GRN No","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Type","Remarks")
4581:         grr_widths=[85,100,120,190,100,120,290,55,75,75,75,65,85,60,190]
4582:         grr_sql="SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,l.item_type,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4583: 
4584:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Item Wise")
4585:         def load_grr_item(codev=None):
4586:             for i in tr.get_children(): tr.delete(i)
4587:             q=codev.get().strip() if codev else ""
4588:             sql=grr_sql+(" WHERE l.code=?" if q else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4589:             for r in self.conn.execute(sql,(q,) if q else ()):
4590:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
```
```text
4596:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Date Wise")
4597:         tr=self.make_tree(fr,grr_cols,grr_widths)
4598:         def load_grr_date(fdv=None,tdv=None,tr=tr):
4599:             for i in tr.get_children(): tr.delete(i)
4600:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4601:             conds=[];params=[]
4602:             if fd: conds.append("g.grr_date>=?");params.append(fd)
4603:             if td: conds.append("g.grr_date<=?");params.append(td)
4604:             sql=grr_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no"
4605:             for r in self.conn.execute(sql,params):
4606:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4607:         fdv,tdv=self._date_filter_bar(fr, lambda:load_grr_date(fdv,tdv))
4608:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Date Wise",tr)).pack(anchor="w",pady=4)
4609:         load_grr_date(fdv,tdv)
4610: 
4611:         fr=ttk.Frame(grr_nb,padding=6); grr_nb.add(fr,text="Party Wise")
4612:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4613:         party=tk.StringVar(value="ALL")
4614:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4615:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4616:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
```
```text
4612:         top=ttk.Frame(fr); top.pack(fill="x",pady=(0,6))
4613:         party=tk.StringVar(value="ALL")
4614:         parties=["ALL"]+[r[0] for r in self.conn.execute("SELECT name FROM parties ORDER BY name COLLATE NOCASE")]
4615:         ttk.Label(top,text="Party").pack(side="left",padx=4)
4616:         cb=ttk.Combobox(top,textvariable=party,values=parties,state="readonly",width=35);cb.pack(side="left",padx=4)
4617:         tr=self.make_tree(fr,("Date","GRN No","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"),[95,110,220,140,110,145,300,80,80,100])
4618:         def load_party(*_):
4619:             for i in tr.get_children(): tr.delete(i)
4620:             psql="SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no"
4621:             if party.get()=="ALL":
4622:                 rows=self.conn.execute(psql+" ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")
4623:             else:
4624:                 rows=self.conn.execute(psql+" WHERE g.supplier=? ORDER BY g.grr_date DESC,g.grr_no DESC",(party.get(),))
4625:             for r in rows:
4626:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4627:         cb.bind("<<ComboboxSelected>>",load_party); load_party()
4628:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4629: 
4630:         # ================= Demand Details =================
4631:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4632:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
```
```text
4628:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("GRN Details - Party Wise",tr)).pack(anchor="w",pady=4)
4629: 
4630:         # ================= Demand Details =================
4631:         dem_fr=ttk.Frame(nb,padding=4); nb.add(dem_fr,text="Demand Details")
4632:         ttk.Button(dem_fr,text="PRINT FULL DEMAND DETAILS",command=lambda:self.print_report("demand")).pack(anchor="w",pady=(0,4))
4633:         dem_nb=ttk.Notebook(dem_fr); dem_nb.pack(fill="both",expand=True)
4634:         dem_cols=("Date","Demand No","Department","Required For","Remarks","Status","Code","Description","UOM","Demand Qty","Available","To Purchase")
4635:         dem_widths=[85,105,120,160,190,110,120,290,55,80,80,90]
4636:         dem_sql="SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no"
4637: 
4638:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Item Wise")
4639:         def load_dem_item(codev=None):
4640:             for i in tr.get_children(): tr.delete(i)
4641:             q=codev.get().strip() if codev else ""
4642:             sql=dem_sql+(" WHERE l.code=?" if q else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4643:             for r in self.conn.execute(sql,(q,) if q else ()):
4644:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4645:         codev=self._item_filter_bar(fr, lambda:load_dem_item(codev))
4646:         tr=self.make_tree(fr,dem_cols,dem_widths)
4647:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Item Wise",tr)).pack(anchor="w",pady=4)
4648:         load_dem_item(codev)
```
```text
4650:         fr=ttk.Frame(dem_nb,padding=6); dem_nb.add(fr,text="Date Wise")
4651:         tr=self.make_tree(fr,dem_cols,dem_widths)
4652:         def load_dem_date(fdv=None,tdv=None,tr=tr):
4653:             for i in tr.get_children(): tr.delete(i)
4654:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4655:             conds=[];params=[]
4656:             if fd: conds.append("d.demand_date>=?");params.append(fd)
4657:             if td: conds.append("d.demand_date<=?");params.append(td)
4658:             sql=dem_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no"
4659:             for r in self.conn.execute(sql,params):
4660:                 r=list(r); r[0]=to_display_date(r[0]); tr.insert("", "end", values=r)
4661:         fdv,tdv=self._date_filter_bar(fr, lambda:load_dem_date(fdv,tdv))
4662:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Demand Details - Date Wise",tr)).pack(anchor="w",pady=4)
4663:         load_dem_date(fdv,tdv)
4664: 
4665:         # ================= Material Issue Details =================
4666:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4667:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4668:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4669:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4670:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
```
```text
4663:         load_dem_date(fdv,tdv)
4664: 
4665:         # ================= Material Issue Details =================
4666:         iss_fr=ttk.Frame(nb,padding=4); nb.add(iss_fr,text="Material Issue Details")
4667:         ttk.Button(iss_fr,text="PRINT FULL MATERIAL ISSUE DETAILS",command=lambda:self.print_report("issue")).pack(anchor="w",pady=(0,4))
4668:         iss_nb=ttk.Notebook(iss_fr); iss_nb.pack(fill="both",expand=True)
4669:         iss_cols=("Date","Issue No","Department","Items Use For","Code","Description","UOM","Issue Qty","Type","Balance After")
4670:         iss_widths=[85,105,140,220,120,290,55,80,60,100]
4671:         iss_sql="SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty,l.item_type FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no"
4672: 
4673:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Item Wise")
4674:         def load_iss_item(codev=None):
4675:             for i in tr.get_children(): tr.delete(i)
4676:             q=codev.get().strip() if codev else ""
4677:             sql=iss_sql+(" WHERE l.code=?" if q else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4678:             for r in self.conn.execute(sql,(q,) if q else ()):
4679:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4680:         codev=self._item_filter_bar(fr, lambda:load_iss_item(codev))
4681:         tr=self.make_tree(fr,iss_cols,iss_widths)
4682:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Item Wise",tr)).pack(anchor="w",pady=4)
4683:         load_iss_item(codev)
```
```text
4685:         fr=ttk.Frame(iss_nb,padding=6); iss_nb.add(fr,text="Date Wise")
4686:         tr=self.make_tree(fr,iss_cols,iss_widths)
4687:         def load_iss_date(fdv=None,tdv=None,tr=tr):
4688:             for i in tr.get_children(): tr.delete(i)
4689:             fd=to_iso_date(fdv.get().strip()) if fdv else ""; td=to_iso_date(tdv.get().strip()) if tdv else ""
4690:             conds=[];params=[]
4691:             if fd: conds.append("i.issue_date>=?");params.append(fd)
4692:             if td: conds.append("i.issue_date<=?");params.append(td)
4693:             sql=iss_sql+((" WHERE "+" AND ".join(conds)) if conds else "")+" ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no"
4694:             for r in self.conn.execute(sql,params):
4695:                 r=list(r); r[0]=to_display_date(r[0]); r.append(fmt_num(stock(self.conn,r[4]))); tr.insert("", "end", values=r)
4696:         fdv,tdv=self._date_filter_bar(fr, lambda:load_iss_date(fdv,tdv))
4697:         ttk.Button(fr,text="PREVIEW CURRENT",command=lambda:self.preview_tree("Material Issue Details - Date Wise",tr)).pack(anchor="w",pady=4)
4698:         load_iss_date(fdv,tdv)
4699: 
4700:         self.set_page_actions(print=lambda:self.print_report(("grr","demand","issue")[nb.index(nb.select())]))
4701: 
4702:     def print_item_master(self):
4703:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4704:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4705: 
```
```text
4702:     def print_item_master(self):
4703:         rows=self.conn.execute("SELECT code,description,uom,opening_qty FROM items ORDER BY code")
4704:         self._open_direct_printer("ITEM MASTER",[],["Code","Description","UOM","Opening"],rows,landscape(A4),[1,3.6,0.8,1])
4705: 
4706:     def print_party_master(self):
4707:         rows=self.conn.execute("SELECT name,contact,address,remarks FROM parties ORDER BY name COLLATE NOCASE")
4708:         self._open_direct_printer("PARTY MASTER",[],["Party Name","Contact","Address","Remarks"],rows,landscape(A4),[1.5,1,2,1.5])
4709: 
4710:     def print_report(self,kind):
4711:         titles={"grr":"GRN DETAILS REPORT","demand":"DEMAND DETAILS REPORT","issue":"MATERIAL ISSUE DETAILS REPORT","party":"PARTY WISE PURCHASE REPORT"}
4712:         if kind=="grr":
4713:             headers=["Date","GRN","Items","Department","Party","Invoice","Code","Description","UOM","Received","Rejected","Accepted","Rate","Amount","Remarks"]
4714:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM grr_lines WHERE grr_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.department,g.supplier,g.invoice_no,l.code,l.description,l.uom,l.received_qty,l.rejected_qty,l.accepted_qty,l.rate,l.amount,g.remarks FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.grr_date DESC,g.grr_no DESC,l.sr_no")]
4715:         elif kind=="demand":
4716:             headers=["Date","Demand","Items","Department","Required For","Remarks","Status","Code","Description","UOM","Qty","Available","To Purchase"]
4717:             rows=[(to_display_date(r[0]),r[1],self.conn.execute("SELECT COUNT(*) FROM demand_lines WHERE demand_no=?",(r[1],)).fetchone()[0],*r[2:]) for r in self.conn.execute("SELECT d.demand_date,d.demand_no,d.department,d.required_for,d.remarks,d.status,l.code,l.description,l.uom,l.demand_qty,l.available_qty,l.to_purchase FROM demands d JOIN demand_lines l ON l.demand_no=d.demand_no ORDER BY d.demand_date DESC,d.demand_no DESC,l.sr_no")]
4718:         elif kind=="issue":
4719:             headers=["Date","Issue","Department","Items Use For","Code","Description","UOM","Issue Qty","Balance"]
4720:             rows=[(to_display_date(r[0]),*r[1:],fmt_num(stock(self.conn,r[4]))) for r in self.conn.execute("SELECT i.issue_date,i.issue_no,i.department,i.items_use_for,l.code,l.description,l.uom,l.issue_qty FROM issues i JOIN issue_lines l ON l.issue_no=i.issue_no ORDER BY i.issue_date DESC,i.issue_no DESC,l.sr_no")]
4721:         else:
4722:             headers=["Date","GRN","Party","Department","Invoice","Code","Description","Qty","Rate","Amount"]
```
```text
4723:             rows=[(to_display_date(r[0]),*r[1:]) for r in self.conn.execute("SELECT g.grr_date,g.grr_no,g.supplier,g.department,g.invoice_no,l.code,l.description,l.accepted_qty,l.rate,l.amount FROM grr g JOIN grr_lines l ON l.grr_no=g.grr_no ORDER BY g.supplier COLLATE NOCASE,g.grr_date DESC,g.grr_no DESC")]
4724:         self._open_direct_printer(titles[kind],[],headers,rows,landscape(A4))
4725: 
4726:     def print_stock(self):
4727:         rows=[]
4728:         for r in self.conn.execute("SELECT code,description,uom,opening_qty,min_level FROM items ORDER BY code"):
4729:             code=r[0];gr=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='GRR' AND code=?",(code,)).fetchone()[0]);iss=float(self.conn.execute("SELECT COALESCE(SUM(qty),0) FROM transactions WHERE doc_type='ISSUE' AND code=?",(code,)).fetchone()[0]);cur=float(r[3] or 0)+gr-iss
4730:             rows.append([code,r[1],r[2],fmt_num(r[3]),fmt_num(gr),fmt_num(iss),fmt_num(cur),fmt_num(r[4]),"REORDER" if cur<=r[4] else "OK"])
4731:         self._open_direct_printer("FULL STOCK / ALL ITEM BALANCE REPORT",[],["Code","Description","UOM","Opening","GRN In","Issue Out","Balance","Minimum","Status"],rows,landscape(A4))
4732: 
4733:     def print_ledger(self):
4734:         rows=[]
4735:         for code in [r[0] for r in self.conn.execute("SELECT code FROM items ORDER BY code")]:
4736:             running=float(self.conn.execute("SELECT opening_qty FROM items WHERE code=?",(code,)).fetchone()[0] or 0)
4737:             for x in self.conn.execute("SELECT doc_date,doc_type,doc_no,qty,party,ref_no,a_c_unit,rate FROM transactions WHERE code=? ORDER BY id",(code,)):
4738:                 running += x[3] if x[1]=="GRR" else -x[3]
4739:                 rows.append([to_display_date(x[0]),*x[1:8],fmt_num(running)])
4740:         self._open_direct_printer("STOCK LEDGER",[],["Date","Type","Document","Code","Qty","Party/Dept","Reference","A/C Unit","Rate","Balance"],rows,landscape(A4))
4741: 
4742:     def _get_doc_data(self, typ, no):
4743:         """Header + line items for one saved document, used by the on-screen
```
```text
4809:             sig=doc.add_table(rows=2,cols=3)
4810:             labels=["Prepared By","Store Keeper","Store Incharge"]
4811:             for i,label in enumerate(labels):
4812:                 sig.cell(0,i).text="____________________"
4813:                 sig.cell(1,i).text=label
4814:                 for para in sig.cell(1,i).paragraphs:
4815:                     for run in para.runs: run.bold=True
4816:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4817:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.docx")
4818:         doc.save(path)
4819:         self.open_file(path)
4820: 
4821:     def export_excel(self, typ, no):
4822:         if not no or not no.strip():
4823:             return messagebox.showwarning("Excel Export","Select a document first.")
4824:         if not XLSX_AVAILABLE:
4825:             return messagebox.showwarning("Excel Export","Excel export needs the openpyxl package.\nRun BUILD_AND_INSTALL.bat again, or: pip install openpyxl")
4826:         data=self._get_doc_data(typ,no)
4827:         if not data:
4828:             return messagebox.showwarning("Excel Export","Document not found.")
4829:         title,header,cols,rows=data
```
```text
4851:             for col in range(1,4):
4852:                 ws.cell(row=sig_row,column=col).alignment=Alignment(horizontal="center")
4853:                 ws.cell(row=sig_row+1,column=col).alignment=Alignment(horizontal="center")
4854:                 ws.cell(row=sig_row+1,column=col).font=Font(bold=True)
4855:         for col_cells in ws.columns:
4856:             length=max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
4857:             ws.column_dimensions[col_cells[0].column_letter].width=min(max(length+2,10),50)
4858:         safe_no="".join(ch for ch in no if ch.isalnum() or ch in "-_") or "document"
4859:         path=os.path.join(REPORTS_DIR,f"{typ}_{safe_no}.xlsx")
4860:         wb.save(path)
4861:         self.open_file(path)
4862: 
4863:     def preview_pdf(self,typ,no):
4864:         if not no.strip():return messagebox.showwarning("Document","Enter/select a document number first.")
4865:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to enable Preview/Print.")
4866:         data=self._get_doc_data(typ,no)
4867:         if not data:return messagebox.showwarning("Document","Document not found.")
4868:         title,header,cols,rows=data
4869:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4870:         page_size = landscape(A4) if typ == "grr" else A4
4871:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
```
```text
4866:         data=self._get_doc_data(typ,no)
4867:         if not data:return messagebox.showwarning("Document","Document not found.")
4868:         title,header,cols,rows=data
4869:         path=os.path.join(BASE,f"{typ}_{''.join(ch for ch in no if ch.isalnum() or ch in '-_') or 'document'}.pdf")
4870:         page_size = landscape(A4) if typ == "grr" else A4
4871:         self._pdf_table_report(path,title,cols,rows,page_size,7,header_lines=header)
4872: 
4873:     def _open_direct_printer(self, title, header_lines, columns, rows, page_size=landscape(A4), col_widths=None):
4874:         """Open the print dialog with a real visual preview of the exact report.
4875: 
4876:         The report is rendered to a temporary PDF only in memory/on disk for the
4877:         duration of printing.  It is deleted after the print dialog closes, so
4878:         the Print button does not leave a PDF report behind.  Printing uses the
4879:         rendered report page itself rather than rebuilding rows as plain text;
4880:         this keeps the printed page identical to the application's report.
4881:         """
4882:         # Printing is always prepared as an A4 landscape page. This only affects
4883:         # the print path; the rest of the application's UI/report logic is unchanged.
4884:         page_size = landscape(A4)
4885:         if not REPORTLAB or not FITZ_AVAILABLE or not PIL_AVAILABLE:
4886:             messagebox.showwarning(
```
```text
4888:                 "The print preview/printing components are not available.\n\n"
4889:                 "Please run BUILD_AND_INSTALL.bat again to install the required printer components."
4890:             )
4891:             return
4892:         if not rows and not columns:
4893:             messagebox.showwarning("Print", "There is no data to print.")
4894:             return
4895:         try:
4896:             os.makedirs(REPORTS_DIR, exist_ok=True)
4897:             key=os.path.join(REPORTS_DIR, f".print_preview_{secrets.token_hex(12)}.pdf")
4898:             self._pdf_table_report(key,title,columns,rows,page_size,
4899:                                    7,col_widths=col_widths,header_lines=header_lines,auto_print=False)
4900:             self._print_jobs[os.path.abspath(key)]=(title, header_lines or [], tuple(columns), [tuple(r) for r in rows], page_size)
4901:             self._select_windows_printer_for_pdf(key)
4902:         except Exception as e:
4903:             messagebox.showerror("Print", f"Could not prepare the print preview.\n\n{e}")
4904: 
4905:     def _select_windows_printer_for_pdf(self, path):
4906:         """Print dialog with an actual page preview, printer selection and direct GDI output.
4907: 
4908:         The preview is rendered from the exact PDF produced by the application,
```
```text
4938:         job=getattr(self, "_print_jobs", {}).get(path)
4939:         if job:
4940:             title, header_lines, columns, rows, source_page_size = job
4941:         else:
4942:             title=os.path.splitext(os.path.basename(path))[0]
4943:             header_lines=[]; columns=(); rows=[]; source_page_size=landscape(A4)
4944: 
4945:         try:
4946:             doc=fitz.open(path)
4947:             total_pages=max(1,doc.page_count)
4948:         except Exception as e:
4949:             messagebox.showerror("Print Preview", f"Could not read the report for preview.\n\n{e}")
4950:             return
4951: 
4952:         win=tk.Toplevel(self)
4953:         win.title("Printing from Win32 application - Print")
4954:         win.geometry("900x620")
4955:         win.minsize(850,580)
4956:         win.transient(self)
4957:         win.configure(bg="#f0f0f0")
4958: 
```
```text
4964:             pass
4965: 
4966:         outer=tk.Frame(win,bg="#f0f0f0")
4967:         outer.pack(fill="both",expand=True)
4968:         outer.columnconfigure(1,weight=1)
4969:         outer.rowconfigure(0,weight=1)
4970: 
4971:         # Left side mirrors the familiar system printer dialog: printers and
4972:         # print options. Right side contains the actual report page preview.
4973:         left=tk.Frame(outer,bg="#f0f0f0",width=230)
4974:         left.grid(row=0,column=0,sticky="nsw",padx=(12,6),pady=12)
4975:         left.grid_propagate(False)
4976:         ttk.Label(left,text="Printer",style="NativePrintBold.TLabel").pack(anchor="w",pady=(0,4))
4977:         printer_list=tk.Listbox(left,height=7,exportselection=False,relief="solid",bd=1,font=("Segoe UI",9))
4978:         printer_list.pack(fill="x")
4979:         for pr in printers: printer_list.insert("end",pr)
4980:         try: printer_list.selection_set(printers.index(default_printer))
4981:         except Exception: printer_list.selection_set(0)
4982: 
4983:         ttk.Label(left,text="Copies",style="NativePrint.TLabel").pack(anchor="w",pady=(14,3))
4984:         copies=tk.IntVar(value=1)
```
```text
5057:         ttk.Label(nav,text="  Document Preview",style="NativePrintBold.TLabel").pack(side="left",padx=8)
5058: 
5059:         bottom=tk.Frame(win,bg="#f0f0f0")
5060:         # `outer` already uses pack() in `win`; using grid() for another direct
5061:         # child of the same toplevel raises TclError. Keep the action bar in the
5062:         # same geometry-manager family so Print/Cancel are always visible.
5063:         bottom.pack(fill="x",padx=12,pady=(0,12))
5064:         bottom.columnconfigure(0,weight=1)
5065:         ttk.Label(bottom,text="Preview is the exact report that will be sent to the selected printer.",style="NativePrint.TLabel").grid(row=0,column=0,sticky="w")
5066:         ttk.Button(bottom,text="Cancel",width=12).grid(row=0,column=1,padx=(8,0))
5067:         print_btn=ttk.Button(bottom,text="Print",width=12)
5068:         print_btn.grid(row=0,column=2,padx=(8,0))
5069: 
5070:         paper_ids={"Letter":1,"Legal":5,"Executive":7,"A3":8,"A4":9,"A5":11,"Statement":6,"Tabloid":3}
5071: 
5072:         def parse_page_selection(total):
5073:             if pages_mode.get()=="All pages": return list(range(total))
5074:             raw=page_range.get().strip()
5075:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5076:             selected=[]
5077:             for part in raw.split(","):
```
```text
5074:             raw=page_range.get().strip()
5075:             if not raw: raise ValueError("Enter a page range, for example 1-3 or 1,3,5.")
5076:             selected=[]
5077:             for part in raw.split(","):
5078:                 part=part.strip()
5079:                 if "-" in part:
5080:                     a,b=part.split("-",1); a=int(a); b=int(b)
5081:                     if a<1 or b<a: raise ValueError("Invalid page range.")
5082:                     if b>total: raise ValueError(f"Page {b} is outside the report.")
5083:                     selected.extend(range(a-1,b))
5084:                 else:
5085:                     n=int(part)
5086:                     if n<1 or n>total: raise ValueError(f"Page {n} is outside the report.")
5087:                     selected.append(n-1)
5088:             return list(dict.fromkeys(selected))
5089: 
5090:         def selected_printer():
5091:             sel=printer_list.curselection()
5092:             return printer_list.get(sel[0]) if sel else printers[0]
5093: 
5094:         def print_rendered_pages():
```
```text
5187:                 finally:
5188:                     if hprinter is not None:
5189:                         try: win32print.ClosePrinter(hprinter)
5190:                         except Exception: pass
5191:                     if hdc:
5192:                         try: ctypes.windll.gdi32.DeleteDC(hdc)
5193:                         except Exception: pass
5194: 
5195:                 # Print the exact rendered PDF page through the printer DC.
5196:                 printable_w=max(1,int(dc.GetDeviceCaps(win32con.HORZRES)))
5197:                 printable_h=max(1,int(dc.GetDeviceCaps(win32con.VERTRES)))
5198:                 off_x=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)))
5199:                 off_y=max(0,int(dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)))
5200: 
5201:                 for copy_no in range(count):
5202:                     dc.StartDoc(str(title)[:80])
5203:                     doc_ok=False
5204:                     try:
5205:                         for batch_start in range(0,len(chosen),cols_n*rows_n):
5206:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5207:                             dc.StartPage()
```
```text
5206:                             batch=chosen[batch_start:batch_start+cols_n*rows_n]
5207:                             dc.StartPage()
5208:                             page_ok=False
5209:                             try:
5210:                                 cell_w=printable_w/float(cols_n)
5211:                                 cell_h=printable_h/float(rows_n)
5212:                                 for j,page_index in enumerate(batch):
5213:                                     page=doc.load_page(page_index)
5214:                                     pdf_w=max(1.0,float(page.rect.width))
5215:                                     pdf_h=max(1.0,float(page.rect.height))
5216:                                     fit=min((cell_w*0.96)/pdf_w,(cell_h*0.96)/pdf_h)
5217:                                     fit=max(0.25,min(fit,8.0))
5218:                                     pix=page.get_pixmap(matrix=fitz.Matrix(fit,fit),alpha=False)
5219:                                     img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
5220:                                     target_w=max(1,int(cell_w*0.96))
5221:                                     target_h=max(1,int(cell_h*0.96))
5222:                                     ratio=min(target_w/img.width,target_h/img.height)
5223:                                     nw=max(1,int(img.width*ratio)); nh=max(1,int(img.height*ratio))
5224:                                     if (nw,nh)!=(img.width,img.height):
5225:                                         img=img.resize((nw,nh),Image.LANCZOS)
5226:                                     dib=ImageWin.Dib(img)
```
```text
5246: 
5247:                 status.set("Print job sent successfully")
5248:                 win.update_idletasks()
5249:                 win.after(500,close)
5250:             except Exception as e:
5251:                 status.set("Print failed: "+str(e))
5252:                 messagebox.showerror("Print", f"The selected printer could not accept the print job.\n\n{e}", parent=win)
5253: 
5254:         def close():
5255:             try: doc.close()
5256:             except Exception: pass
5257:             try: win.destroy()
5258:             except Exception: pass
5259:             # Only the temporary PDF created by the Print button is removed.
5260:             # Existing report PDFs passed through the legacy print path are preserved.
5261:             try:
5262:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5263:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5264:             except Exception: pass
5265: 
5266:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
```
```text
5262:                 if path in getattr(self,"_print_jobs",{}): self._print_jobs.pop(path,None)
5263:                 if is_temporary_preview and os.path.isfile(path): os.remove(path)
5264:             except Exception: pass
5265: 
5266:         pages_mode.trace_add("write",lambda *_:page_entry.configure(state="normal" if pages_mode.get()=="Custom" else "disabled"))
5267:         bottom.winfo_children()[1].configure(command=close)
5268:         print_btn.configure(command=print_rendered_pages)
5269:         win.protocol("WM_DELETE_WINDOW",close)
5270:         win.bind("<Escape>",lambda e:close())
5271:         win.grab_set()
5272:         # Keep the requested printer defaults visibly selected; no manual
5273:         # adjustment is required before pressing Print.
5274:         win.after(50,lambda:(layout_combo.current(1), paper_combo.current(0)))
5275:         win.after(120,lambda:render_preview(0))
5276:         win.focus_force()
5277: 
5278:     def print_pdf(self,path):
5279:         """Open a printer-selection window for a generated PDF."""
5280:         path=os.path.abspath(path)
5281:         if not os.path.exists(path):
5282:             messagebox.showwarning("Print", "The report file could not be found.")
```
```text
5278:     def print_pdf(self,path):
5279:         """Open a printer-selection window for a generated PDF."""
5280:         path=os.path.abspath(path)
5281:         if not os.path.exists(path):
5282:             messagebox.showwarning("Print", "The report file could not be found.")
5283:             return
5284: 
5285:         if sys.platform.startswith("win"):
5286:             self._select_windows_printer_for_pdf(path)
5287:             return
5288: 
5289:         try:
5290:             subprocess.run(["lp", path], check=True)
5291:         except Exception as e:
5292:             messagebox.showwarning(
5293:                 "Print",
5294:                 "The operating system could not start printing.\n\n"
5295:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5296:             )
5297: 
5298:     def open_file(self,path):
```
```text
5293:                 "Print",
5294:                 "The operating system could not start printing.\n\n"
5295:                 f"The report has been saved here:\n{path}\n\nDetails: {e}"
5296:             )
5297: 
5298:     def open_file(self,path):
5299:         try:
5300:             if sys.platform.startswith("win"): os.startfile(path)
5301:             elif sys.platform=="darwin": subprocess.Popen(["open",path])
5302:             else: subprocess.Popen(["xdg-open",path])
5303:         except Exception: webbrowser.open("file://"+os.path.abspath(path))
5304: 
5305:     def print_demand(self,no):
5306:         data=self._get_doc_data("demand",no)
5307:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5308:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5309:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5310:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5311: 
5312:     def print_grr(self,no):
5313:         data=self._get_doc_data("grr",no)
```
```text
5307:         if not data:return messagebox.showwarning("Document","Purchase Demand not found.")
5308:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5309:         title,header,cols,rows=data; path=os.path.join(BASE,f"Purchase_Demand_{no}.pdf")
5310:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
5311: 
5312:     def print_grr(self,no):
5313:         data=self._get_doc_data("grr",no)
5314:         if not data:return messagebox.showwarning("Document","GRN not found.")
5315:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5316:         title,header,cols,rows=data; path=os.path.join(BASE,f"GRN_{no}.pdf")
5317:         # GRN has a wide item table. Generate the PDF itself in landscape so
5318:         # the printer dialog and printer driver receive a landscape document
5319:         # instead of a portrait page with rotated/cropped content.
5320:         self._pdf_table_report(path,title,cols,rows,landscape(A4),7,header_lines=header)
5321: 
5322:     def print_issue(self,no):
5323:         data=self._get_doc_data("issue",no)
5324:         if not data:return messagebox.showwarning("Document","Material Issue not found.")
5325:         if not REPORTLAB:return messagebox.showwarning("PDF","Install reportlab to print PDF reports.")
5326:         title,header,cols,rows=data; path=os.path.join(BASE,f"Material_Issue_{no}.pdf")
5327:         self._pdf_table_report(path,title,cols,rows,A4,7,header_lines=header)
```

## updater.py

- Lines: 156
- Functions: _app_dir(21-24), _version_tuple(27-34), _load_config(37-42), _download(45-52), _sha256(55-60), _install_after_exit(63-70), _start_update_download(73-95), _show_update_check_popup(98-116), check_for_update(119-155)

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
