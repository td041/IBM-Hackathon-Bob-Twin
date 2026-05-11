"""Integration tests for capture.py — requires demo_target running on :8001.

These tests are marked with @pytest.mark.integration and are skipped unless
the demo app is reachable. Run with: pytest tests/test_capture.py -m integration
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

import twin_mcp.capture as capture_mod
import twin_mcp.audit as audit_mod


@pytest.fixture(autouse=True)
def tmp_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(capture_mod, "_CASSETTE_DIR", tmp_path / "cassettes")
    monkeypatch.setattr(audit_mod, "_AUDIT_DIR", tmp_path / "audit")
    return tmp_path


# ── Unit tests (no live server needed) ───────────────────────────────────────

def test_capture_returns_ok_false_when_no_interactions(tmp_path):
    # Patch _run_scenario to produce no cassette file
    with patch.object(capture_mod, "_run_scenario", return_value={"ok": True}):
        result = capture_mod.capture_baseline(str(tmp_path), ["scripts/seed_demo_traffic.py"])
    assert result["ok"] is False
    assert "no HTTP interactions captured" in result["errors"][0]


def test_capture_returns_error_when_scenario_fails(tmp_path):
    with patch.object(capture_mod, "_run_scenario", return_value={"ok": False, "error": "timeout"}):
        result = capture_mod.capture_baseline(str(tmp_path), ["bad_script.py"])
    assert result["ok"] is False
    assert any("timeout" in e for e in result["errors"])


def test_capture_writes_cassette_and_audit_on_success(tmp_path):
    # Simulate a scenario that writes a minimal cassette
    def fake_run(scenario, cassette_path):
        cassette_path.parent.mkdir(parents=True, exist_ok=True)
        cassette_data = {
            "interactions": [
                {
                    "request": {"method": "GET", "uri": "http://localhost:8001/health", "body": None, "headers": {}},
                    "response": {"body": {"string": '{"status":"ok"}'}, "headers": {}, "status": {"code": 200, "message": "OK"}},
                }
            ],
            "version": 1,
        }
        with open(cassette_path, "w") as f:
            yaml.dump(cassette_data, f)
        return {"ok": True}

    with patch.object(capture_mod, "_run_scenario", side_effect=fake_run):
        result = capture_mod.capture_baseline(str(tmp_path), ["scripts/seed_demo_traffic.py"])

    assert result["ok"] is True
    assert result["n_interactions"] == 1
    assert len(result["run_id"]) == 8
    assert Path(result["cassette_path"]).exists()

    # audit entry should be present
    entries = audit_mod.read(result["run_id"])
    assert len(entries) == 1
    assert entries[0]["phase"] == "capture"


def test_capture_run_id_is_unique_across_calls(tmp_path):
    def fake_run(scenario, cassette_path):
        cassette_path.parent.mkdir(parents=True, exist_ok=True)
        cassette_data = {
            "interactions": [
                {
                    "request": {"method": "GET", "uri": "http://localhost:8001/health", "body": None, "headers": {}},
                    "response": {"body": {"string": '{"status":"ok"}'}, "headers": {}, "status": {"code": 200, "message": "OK"}},
                }
            ],
            "version": 1,
        }
        with open(cassette_path, "w") as f:
            yaml.dump(cassette_data, f)
        return {"ok": True}

    with patch.object(capture_mod, "_run_scenario", side_effect=fake_run):
        r1 = capture_mod.capture_baseline(str(tmp_path), ["s1.py"])
    with patch.object(capture_mod, "_run_scenario", side_effect=fake_run):
        r2 = capture_mod.capture_baseline(str(tmp_path), ["s1.py"])

    assert r1["run_id"] != r2["run_id"]


def test_count_interactions_returns_zero_for_missing_file(tmp_path):
    count = capture_mod._count_interactions(tmp_path / "nonexistent.yaml")
    assert count == 0


def test_list_endpoints_deduplicates(tmp_path):
    cassette_path = tmp_path / "test.yaml"
    cassette_data = {
        "interactions": [
            {"request": {"method": "GET", "uri": "http://localhost:8001/users", "body": None, "headers": {}}, "response": {}},
            {"request": {"method": "GET", "uri": "http://localhost:8001/users", "body": None, "headers": {}}, "response": {}},
            {"request": {"method": "POST", "uri": "http://localhost:8001/users", "body": None, "headers": {}}, "response": {}},
        ],
        "version": 1,
    }
    with open(cassette_path, "w") as f:
        yaml.dump(cassette_data, f)
    endpoints = capture_mod._list_endpoints(cassette_path)
    assert len(endpoints) == 2
    assert "GET /users" in endpoints
    assert "POST /users" in endpoints


# ── Integration tests (require live demo_target on :8001) ────────────────────

@pytest.mark.integration
def test_integration_capture_hits_live_app(tmp_path):
    """Requires: uvicorn demo_target.pydantic_v1_app.main:app --port 8001"""
    result = capture_mod.capture_baseline(
        str(Path(".").resolve()),
        ["scripts/seed_demo_traffic.py"],
    )
    assert result["ok"] is True
    assert result["n_interactions"] >= 30
    assert len(result["endpoints_covered"]) >= 10
