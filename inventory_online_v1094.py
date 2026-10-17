"""v1.0.94: isolate the clean 102-code online inventory from legacy sync.

Older installations still use Firebase /store_inventory/data.json and cannot
modify /store_inventory_v2/data.json. The first upgraded installation copies
only MTO, parties and users from legacy, seeds the 102 uploaded codes and
archives the pre-migration cloud/local data. After that, v2 is the only source
of truth; repeated launches NEVER repeat the 102-code wipe.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
import os
import sqlite3
import tempfile
import time
import uuid

from firebase_sync import snapshot_db
from inventory_reset_v1088 import read_codes, migrate_snapshot

NAMESPACE = "store_inventory_v2"
MARKER = "isolated-inventory-102-v1.0.94"
LEGACY_NAMESPACE = "store_inventory"
DOCUMENTS = ("demands", "demand_lines", "grr", "grr_lines",
             "issues", "issue_lines", "transactions")


def _backup_json(obj, directory, label):
    os.makedirs(directory, exist_ok=True)
    destination = os.path.join(directory, label + "_"
                               + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".json")
    fd, temporary = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(obj, output, ensure_ascii=False)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.isfile(temporary):
            os.unlink(temporary)
    return destination


def _backup_sqlite(conn, directory):
    os.makedirs(directory, exist_ok=True)
    name = "before_online_clean_v1094_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".db"
    destination = os.path.join(directory, name)
    db = sqlite3.connect(destination)
    try:
        conn.backup(db)
    finally:
        db.close()
    return destination


def _validated_cloud(snapshot):
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("tables"), dict):
        return False
    if snapshot.get("clean_inventory_namespace") != MARKER:
        raise RuntimeError(
            "The clean Firebase namespace exists but its safety marker is absent. "
            "The app will not overwrite it.")
    for table in ("items", "mto_items", "parties", "users", *DOCUMENTS):
        if table not in snapshot["tables"]:
            raise RuntimeError("The clean online database has no table: " + table)
    return True


def _fresh_clean_snapshot(legacy, uploaded_codes):
    # The old online marker alone cannot be trusted: older clients were able
    # to upload 2,480 rows again after the original v1.0.88 reset.
    old = deepcopy(legacy)
    old.pop("inventory_reset_id", None)
    clean = migrate_snapshot(old, uploaded_codes)
    clean["clean_inventory_namespace"] = MARKER
    clean["inventory_reset_id"] = "inventory-102-reset-v1.0.88"
    clean["schema"] = 1
    if len([r for r in clean["tables"]["items"]["rows"]
            if str(r.get("item_type") or "Local").upper() != "MTO"]) != 102:
        raise RuntimeError("Clean namespace seed verification failed: expected 102 codes.")
    for table in DOCUMENTS:
        if clean["tables"][table]["rows"]:
            raise RuntimeError("Unexpected legacy transaction records in clean namespace.")
    return clean


def _ready_to_sync(conn, sync, cloud, backup_dir):
    """Align stale local SQLite and new v2 snapshot without resurrecting v1 data.

    Pending v2 changes are honored only if their baseline belongs to v2.
    Otherwise the already confirmed remote clean snapshot takes precedence.
    """
    state = sync._load_json(sync.state_path)
    pending = sync._load_json(sync.pending_path)
    saved_baseline = pending.get("baseline") if isinstance(pending, dict) else None
    v2_pending = (isinstance(saved_baseline, dict)
                  and saved_baseline.get("clean_inventory_namespace") == MARKER
                  and isinstance(pending.get("snapshot"), dict))
    if v2_pending:
        # An offline save made by this version can be merged normally.
        sync.initialize(conn)
        return

    # A v1 snapshot, or any unexplained local difference, is never merged
    # into the clean v2 dataset. Back it up before discarding it.
    local = snapshot_db(conn)
    if not isinstance(state, dict) or state.get("clean_inventory_namespace") != MARKER or local != {
        "schema": 1, "tables": cloud["tables"]
    }:
        if local != {"schema": 1, "tables": cloud["tables"]}:
            _backup_sqlite(conn, backup_dir)
    sync.replace_local(conn, cloud)
    sync._save_state(cloud)
    sync._clear_pending()
    sync.pending_base = None
    sync.pending_error = None
    try:
        os.remove(sync.remote_cache_path)
    except FileNotFoundError:
        pass
    import durable_local
    durable_local.save(conn)


def ensure_clean_online(conn, sync, csv_path, backup_dir):
    """Make the clean v2 dataset authoritative before showing Inventory Codes.

    If the Internet is down on the very first v2 launch, fail safely rather
    than showing or pushing an obsolete local 2,480-code database.
    """
    state = sync._load_json(sync.state_path)
    if not sync.enabled:
        if isinstance(state, dict) and state.get("clean_inventory_namespace") == MARKER:
            return False  # Existing v2 dataset remains available offline.
        raise RuntimeError(
            "Connect this PC to the Internet to activate the clean 102-code inventory. "
            "The legacy 2,480-code cache has NOT been uploaded.")

    uploaded_codes = read_codes(csv_path)
    original_timeout = sync.timeout
    sync.timeout = max(original_timeout, 18)
    token = "bootstrap-v1094-" + uuid.uuid4().hex
    locked = False
    try:
        # Coordinate multiple updated PCs to initialize v2 exactly once.
        for _ in range(12):
            if sync._try_acquire_lock(token):
                locked = True
                break
            time.sleep(0.3)
        if not locked:
            raise RuntimeError("Clean online inventory is locked by another PC. Retry opening the app.")

        cloud = sync._get_snapshot()
        if not _validated_cloud(cloud):
            # Read the legacy online source for users, parties, MTO and archive;
            # never write to the legacy data path again.
            response = sync._request("GET", LEGACY_NAMESPACE + "/data.json")
            legacy = response.json()
            if not isinstance(legacy, dict) or "tables" not in legacy:
                # A brand-new installation may not have any old Firebase data.
                legacy = snapshot_db(conn)
            prepared = _fresh_clean_snapshot(legacy, uploaded_codes)

            # Create durable backups before new namespace initialization.
            _backup_json(legacy, backup_dir, "legacy_cloud_before_v1094")
            _backup_sqlite(conn, backup_dir)

            # Legacy users can keep using the original path as a historical
            # archive, but cannot pollute this new namespace.
            sync._request("PUT", NAMESPACE + "/data.json", json=prepared)
            sync._request("PUT", NAMESPACE + "/_meta/version.json",
                          json="v1.0.94-bootstrap-" + str(time.time_ns()))
            cloud = prepared

        _ready_to_sync(conn, sync, cloud, backup_dir)
        return True
    finally:
        if locked:
            sync._release_lock(token)
        sync.timeout = original_timeout
