"""Tests for audit.py hash-chain integrity."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import twin_mcp.audit as audit_mod


@pytest.fixture(autouse=True)
def tmp_audit_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_mod, "_AUDIT_DIR", tmp_path)
    return tmp_path


def test_first_entry_uses_zero_hash():
    entry = audit_mod.append("run001", "capture", {"cassette": "test.yaml"})
    assert entry["prev_hash"] == audit_mod._ZERO_HASH
    assert entry["entry_index"] == 0


def test_second_entry_links_to_first():
    e1 = audit_mod.append("run002", "capture", {"cassette": "c.yaml"})
    e2 = audit_mod.append("run002", "replay", {"score": 0.97})
    assert e2["prev_hash"] == e1["this_hash"]
    assert e2["entry_index"] == 1


def test_three_entries_chain_intact():
    for phase in ["capture", "migrate", "replay"]:
        audit_mod.append("run003", phase, {"phase": phase})
    is_valid, broken_at = audit_mod.verify_chain("run003")
    assert is_valid is True
    assert broken_at is None


def test_tampered_middle_entry_fails_chain(tmp_path):
    audit_mod.append("run004", "capture", {"x": 1})
    audit_mod.append("run004", "migrate", {"x": 2})
    audit_mod.append("run004", "replay", {"x": 3})

    path = tmp_path / "run_run004.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[1])
    entry["payload"]["x"] = 999  # tamper
    lines[1] = json.dumps(entry)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    is_valid, broken_at = audit_mod.verify_chain("run004")
    assert is_valid is False
    assert broken_at == 1


def test_read_returns_empty_for_missing_run():
    entries = audit_mod.read("nonexistent_run")
    assert entries == []


def test_verify_empty_run_is_valid():
    is_valid, broken_at = audit_mod.verify_chain("empty_run")
    assert is_valid is True
    assert broken_at is None


def test_hash_is_deterministic():
    h1 = audit_mod._compute_hash("prev", {"k": "v"}, "2026-05-15T00:00:00.000Z", 0)
    h2 = audit_mod._compute_hash("prev", {"k": "v"}, "2026-05-15T00:00:00.000Z", 0)
    assert h1 == h2


def test_different_payloads_produce_different_hashes():
    h1 = audit_mod._compute_hash("prev", {"k": "v1"}, "2026-05-15T00:00:00.000Z", 0)
    h2 = audit_mod._compute_hash("prev", {"k": "v2"}, "2026-05-15T00:00:00.000Z", 0)
    assert h1 != h2


def test_read_back_regenerates_matching_hashes():
    audit_mod.append("run005", "capture", {"n": 10})
    audit_mod.append("run005", "replay", {"score": 0.95})
    entries = audit_mod.read("run005")
    for entry in entries:
        prev = audit_mod._ZERO_HASH if entry["entry_index"] == 0 else entries[entry["entry_index"] - 1]["this_hash"]
        expected = audit_mod._compute_hash(
            prev, entry["payload"], entry["timestamp"], entry["entry_index"]
        )
        assert entry["this_hash"] == expected
