from pathlib import Path
import builtins
import io
import os
import shutil
import sqlite3
import sys

INSTALL_ROOT = Path(r"C:\StoreInventoryManagement")
DATA_DIR = INSTALL_ROOT / "Data"
BACKUP_DIR = INSTALL_ROOT / "Backups"
REPORTS_DIR = INSTALL_ROOT / "Reports"

_CONFIG_FILES = {"firebase_database_url.txt", "update_config.json", "firebase_rules_url_only.json"}
_RESOURCE_FILES = {"inventory_seed.csv", "company_logo.png"}
_DB_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".db3"}


def _inside(path, root):
    try:
        return os.path.commonpath([str(path).casefold(), str(root).casefold()]) == str(root).casefold()
    except (ValueError, TypeError):
        return False


def _runtime_temp_root():
    value = getattr(sys, "_MEIPASS", "")
    return Path(value) if value else None


def _is_runtime_temp(path):
    temp_root = _runtime_temp_root()
    return bool(temp_root and _inside(path, temp_root))


def _is_database_path(path):
    return Path(os.fspath(path)).suffix.casefold() in _DB_SUFFIXES


def _permanent_db_target(p):
    return DATA_DIR / p.name


def _write_target(path, backup=False, report=False):
    p = Path(os.fspath(path))
    if p.is_absolute():
        if _inside(p, DATA_DIR) or _inside(p, BACKUP_DIR) or _inside(p, REPORTS_DIR):
            return p
        if _is_database_path(p) and (_is_runtime_temp(p) or _inside(p, INSTALL_ROOT) or _inside(p, Path(sys.executable).parent)):
            return _permanent_db_target(p)
        if _inside(p, INSTALL_ROOT):
            root = BACKUP_DIR if backup else REPORTS_DIR if report else DATA_DIR
            return root / p.relative_to(INSTALL_ROOT)
        return p
    name = p.name.casefold()
    parts = {x.casefold() for x in p.parts}
    if backup or "backup" in name or "backups" in parts:
        return BACKUP_DIR / p
    if report or "report" in name or "reports" in parts:
        return REPORTS_DIR / p
    return DATA_DIR / p


def _read_target(path):
    p = Path(os.fspath(path))
    if p.is_absolute():
        if _is_database_path(p) and (_inside(p, INSTALL_ROOT) or _inside(p, Path(sys.executable).parent) or _is_runtime_temp(p)):
            candidate = _permanent_db_target(p)
            if candidate.exists():
                return candidate
        return p
    name = p.name.casefold()
    if name in _CONFIG_FILES or name in _RESOURCE_FILES:
        return p
    backup = BACKUP_DIR / p
    data = DATA_DIR / p
    report = REPORTS_DIR / p
    if backup.exists():
        return backup
    if data.exists():
        return data
    if report.exists():
        return report
    return p


def _is_write_mode(mode):
    return any(ch in mode for ch in ("w", "a", "x", "+"))


def _open(file, mode="r", *args, **kwargs):
    if _is_write_mode(mode):
        file = _write_target(file)
        Path(file).parent.mkdir(parents=True, exist_ok=True)
    else:
        file = _read_target(file)
    return _ORIGINAL_OPEN(file, mode, *args, **kwargs)


def _io_open(file, mode="r", *args, **kwargs):
    if _is_write_mode(mode):
        file = _write_target(file)
        Path(file).parent.mkdir(parents=True, exist_ok=True)
    else:
        file = _read_target(file)
    return _ORIGINAL_IO_OPEN(file, mode, *args, **kwargs)


def _sqlite_connect(database, *args, **kwargs):
    if isinstance(database, (str, os.PathLike)) and str(database) not in (":memory:", ""):
        original = Path(os.fspath(database))
        target = _write_target(original)
        target.parent.mkdir(parents=True, exist_ok=True)

        # Preserve any database created by an older build before redirecting it
        # into permanent storage. Also carry SQLite WAL/SHM sidecars when present.
        if original.is_absolute() and original != target and original.exists() and not target.exists():
            try:
                shutil.copy2(original, target)
                for suffix in ("-wal", "-shm"):
                    sidecar = Path(str(original) + suffix)
                    if sidecar.exists():
                        shutil.copy2(sidecar, Path(str(target) + suffix))
            except OSError:
                pass
        database = str(target)
    return _ORIGINAL_SQLITE_CONNECT(database, *args, **kwargs)


def _copy2(src, dst, *args, **kwargs):
    dst = _write_target(dst, backup="backup" in str(dst).casefold())
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    return _ORIGINAL_COPY2(src, dst, *args, **kwargs)


def _copyfile(src, dst, *args, **kwargs):
    dst = _write_target(dst, backup="backup" in str(dst).casefold())
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    return _ORIGINAL_COPYFILE(src, dst, *args, **kwargs)


_ORIGINAL_OPEN = builtins.open
_ORIGINAL_IO_OPEN = io.open
_ORIGINAL_SQLITE_CONNECT = sqlite3.connect
_ORIGINAL_COPY2 = shutil.copy2
_ORIGINAL_COPYFILE = shutil.copyfile


def install():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    builtins.open = _open
    io.open = _io_open
    sqlite3.connect = _sqlite_connect
    shutil.copy2 = _copy2
    shutil.copyfile = _copyfile


install()
