from pathlib import Path
import builtins
import io
import os
import shutil
import sqlite3

INSTALL_ROOT = Path(r"C:\StoreInventoryManagement")
DATA_DIR = INSTALL_ROOT / "Data"
BACKUP_DIR = INSTALL_ROOT / "Backups"
REPORTS_DIR = INSTALL_ROOT / "Reports"

_DATA_ROOT = str(DATA_DIR).casefold()
_BACKUP_ROOT = str(BACKUP_DIR).casefold()
_REPORT_ROOT = str(REPORTS_DIR).casefold()
_INSTALL_ROOT = str(INSTALL_ROOT).casefold()


def _inside(path, root):
    try:
        return os.path.commonpath([str(path).casefold(), root]) == root
    except (ValueError, TypeError):
        return False


def _target(path, backup=False, report=False):
    p = Path(os.fspath(path))
    if p.is_absolute():
        s = str(p).casefold()
        if _inside(p, DATA_DIR) or _inside(p, BACKUP_DIR) or _inside(p, REPORTS_DIR):
            return p
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


def _is_write_mode(mode):
    return any(ch in mode for ch in ("w", "a", "x", "+"))


def _open(file, mode="r", *args, **kwargs):
    if _is_write_mode(mode):
        file = _target(file)
        Path(file).parent.mkdir(parents=True, exist_ok=True)
    return _ORIGINAL_OPEN(file, mode, *args, **kwargs)


def _io_open(file, mode="r", *args, **kwargs):
    if _is_write_mode(mode):
        file = _target(file)
        Path(file).parent.mkdir(parents=True, exist_ok=True)
    return _ORIGINAL_IO_OPEN(file, mode, *args, **kwargs)


def _sqlite_connect(database, *args, **kwargs):
    if isinstance(database, (str, os.PathLike)) and str(database) not in (":memory:", ""):
        database = _target(database)
        Path(database).parent.mkdir(parents=True, exist_ok=True)
    return _ORIGINAL_SQLITE_CONNECT(database, *args, **kwargs)


def _copy2(src, dst, *args, **kwargs):
    dst = _target(dst, backup="backup" in str(dst).casefold())
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    return _ORIGINAL_COPY2(src, dst, *args, **kwargs)


def _copyfile(src, dst, *args, **kwargs):
    dst = _target(dst, backup="backup" in str(dst).casefold())
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
