"""Hash-chained JSONL audit trail writer and reader."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_AUDIT_DIR = Path(os.environ.get("TWIN_AUDIT_DIR", "audit_trail"))
_ZERO_HASH = "sha256:" + "0" * 64


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _compute_hash(prev_hash: str, payload: dict, timestamp: str, entry_index: int) -> str:
    data = prev_hash + _canonical_json(payload) + timestamp + str(entry_index)
    digest = hashlib.sha256(data.encode()).hexdigest()
    return f"sha256:{digest}"


def _audit_path(run_id: str) -> Path:
    _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    return _AUDIT_DIR / f"run_{run_id}.jsonl"


def append(run_id: str, phase: str, payload: dict) -> dict:
    """Append a hash-chained entry to the audit trail for run_id.

    Args:
        run_id: Unique identifier for the migration run.
        phase: One of capture/migrate/replay/drift/report/override.
        payload: Phase-specific data dict.

    Returns:
        The written entry dict including this_hash.
    """
    path = _audit_path(run_id)
    existing = read(run_id)

    if existing:
        prev_hash = existing[-1]["this_hash"]
        entry_index = len(existing)
    else:
        prev_hash = _ZERO_HASH
        entry_index = 0

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    this_hash = _compute_hash(prev_hash, payload, timestamp, entry_index)

    entry = {
        "run_id": run_id,
        "entry_index": entry_index,
        "phase": phase,
        "timestamp": timestamp,
        "payload": payload,
        "prev_hash": prev_hash,
        "this_hash": this_hash,
    }

    with open(path, mode="a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def read(run_id: str) -> list[dict]:
    """Read all audit entries for a run_id.

    Args:
        run_id: Unique identifier for the migration run.

    Returns:
        List of entry dicts in order, empty list if no file exists.
    """
    path = _audit_path(run_id)
    if not path.exists():
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def verify_chain(run_id: str) -> tuple[bool, int | None]:
    """Verify the hash chain integrity for a run_id.

    Args:
        run_id: Unique identifier for the migration run.

    Returns:
        Tuple of (is_valid, broken_at_index). broken_at_index is None if valid.
    """
    entries = read(run_id)
    if not entries:
        return True, None

    for i, entry in enumerate(entries):
        expected_prev = _ZERO_HASH if i == 0 else entries[i - 1]["this_hash"]
        if entry["prev_hash"] != expected_prev:
            return False, i

        expected_hash = _compute_hash(
            entry["prev_hash"],
            entry["payload"],
            entry["timestamp"],
            entry["entry_index"],
        )
        if entry["this_hash"] != expected_hash:
            return False, i

    return True, None
