"""Tests for diff_engine.py — DeepDiff comparison with tolerance rules."""

import pytest

from twin_mcp.diff_engine import compare, batch_compare


def test_identical_responses_score_pass():
    result = compare({"id": 1, "name": "Alice"}, {"id": 1, "name": "Alice"}, "GET /users/1")
    assert result["status"] == "pass"
    assert result["diff"] == {}


def test_changed_field_produces_fail():
    result = compare(
        {"id": 1, "role": "ADMIN"},
        {"id": 1, "role": {"name": "ADMIN", "value": "ADMIN"}},
        "GET /users/1",
    )
    assert result["status"] == "fail"
    assert result["diff"] != {}


def test_tolerance_rule_regex_ignore_makes_pass():
    rules = [{"path": "$.token", "kind": "regex_ignore", "pattern": ".*", "rationale": "token changes each run"}]
    result = compare(
        {"id": 1, "token": "abc123"},
        {"id": 1, "token": "xyz789"},
        "GET /auth",
        rules,
    )
    assert result["status"] == "pass"


def test_tolerance_rule_any_uuid_makes_pass():
    import uuid
    rules = [{"path": "$.request_id", "kind": "any_uuid", "rationale": "UUID changes per request"}]
    result = compare(
        {"status": "ok", "request_id": str(uuid.uuid4())},
        {"status": "ok", "request_id": str(uuid.uuid4())},
        "POST /orders",
        rules,
    )
    assert result["status"] == "pass"


def test_tolerance_rule_numeric_tolerance_within_epsilon():
    rules = [{"path": "$.total", "kind": "numeric_tolerance", "epsilon": 0.001, "rationale": "float rounding"}]
    result = compare(
        {"total": 0.5},
        {"total": 0.5001},
        "POST /orders/calculate",
        rules,
    )
    assert result["status"] == "pass"


def test_tolerance_rule_numeric_tolerance_exceeds_epsilon_fails():
    rules = [{"path": "$.total", "kind": "numeric_tolerance", "epsilon": 0.001, "rationale": "float rounding"}]
    result = compare(
        {"total": 0.5},
        {"total": 0.6},
        "POST /orders/calculate",
        rules,
    )
    assert result["status"] == "fail"


def test_tolerance_rule_enum_remap_admin():
    """The map translates candidate-side enum values back to the baseline string.

    Baseline (v1) returns "ADMIN". Candidate (v2) returns the legacy/renamed
    value "ADMIN_OBJECT". Without the rule these would diff and fail; the rule
    remaps "ADMIN_OBJECT" -> "ADMIN" on the actual side, producing equality.
    """
    rules = [{
        "path": "$.role",
        "kind": "enum_value_remap",
        "map": {"ADMIN_OBJECT": "ADMIN"},
        "rationale": "v2 emits renamed enum value; treat as equivalent to v1 ADMIN",
    }]
    result = compare({"role": "ADMIN"}, {"role": "ADMIN_OBJECT"}, "GET /users/1", rules)
    assert result["status"] == "pass"
    # Prove the rule actually fired — not a coincidence of equal payloads.
    assert len(result["matched_rules"]) == 1


def test_no_rules_enum_object_diff_fails():
    result = compare(
        {"role": "ADMIN"},
        {"role": {"name": "ADMIN", "value": "ADMIN"}},
        "GET /users/1",
    )
    assert result["status"] == "fail"


def test_matched_rules_reported_in_result():
    rules = [{"path": "$.ts", "kind": "any_iso_datetime", "rationale": "timestamp varies"}]
    result = compare(
        {"ts": "2026-05-15T10:00:00Z"},
        {"ts": "2026-05-15T11:00:00Z"},
        "GET /events",
        rules,
    )
    assert len(result["matched_rules"]) > 0


def test_batch_compare_returns_one_result_per_interaction():
    interactions = [
        ({"a": 1}, {"a": 1}, "GET /a"),
        ({"b": 2}, {"b": 3}, "GET /b"),
    ]
    results = batch_compare(interactions)
    assert len(results) == 2
    assert results[0]["status"] == "pass"
    assert results[1]["status"] == "fail"


def test_endpoint_label_preserved_in_result():
    result = compare({}, {}, "DELETE /users/42")
    assert result["endpoint"] == "DELETE /users/42"
