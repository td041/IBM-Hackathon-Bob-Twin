"""DeepDiff-based response comparison with tolerance rule application."""

import json
import re
from datetime import datetime
from urllib.parse import urlparse

from deepdiff import DeepDiff
from jsonpath_ng import parse as jsonpath_parse


def _load_tolerance_rules(rules_dict: dict | None) -> list[dict]:
    if not rules_dict:
        return []
    return rules_dict.get("rules", [])


def _jsonpath_matches(path_expr: str, data: dict) -> list:
    """Return all values matching a JSONPath expression in data."""
    try:
        expr = jsonpath_parse(path_expr)
        return [match.value for match in expr.find(data)]
    except Exception:
        return []


def _apply_tolerance_rule(rule: dict, expected: dict, actual: dict) -> tuple[dict, dict, bool]:
    """Apply a single tolerance rule, returning modified copies and whether it matched."""
    kind = rule.get("kind", "")
    path = rule.get("path", "")

    expected_vals = _jsonpath_matches(path, expected)
    actual_vals = _jsonpath_matches(path, actual)

    if not expected_vals and not actual_vals:
        return expected, actual, False

    import copy
    e = copy.deepcopy(expected)
    a = copy.deepcopy(actual)

    matched = False

    if kind == "any_uuid":
        # replace both sides with a fixed sentinel so DeepDiff ignores
        for val in expected_vals + actual_vals:
            e = _replace_value(e, val, "__UUID__")
            a = _replace_value(a, val, "__UUID__")
        matched = True

    elif kind == "any_iso_datetime":
        for val in expected_vals + actual_vals:
            try:
                datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                e = _replace_value(e, val, "__DATETIME__")
                a = _replace_value(a, val, "__DATETIME__")
                matched = True
            except ValueError:
                pass

    elif kind == "regex_ignore":
        pattern = rule.get("pattern", "")
        for val in expected_vals + actual_vals:
            if re.match(pattern, str(val)):
                e = _replace_value(e, val, "__IGNORED__")
                a = _replace_value(a, val, "__IGNORED__")
                matched = True

    elif kind == "ignore_order":
        # DeepDiff handles order via ignore_order param — mark as matched
        matched = bool(expected_vals or actual_vals)

    elif kind == "numeric_tolerance":
        epsilon = rule.get("epsilon", 0.001)
        for ev, av in zip(expected_vals, actual_vals):
            try:
                if abs(float(ev) - float(av)) <= epsilon:
                    e = _replace_value(e, ev, "__NUMERIC_OK__")
                    a = _replace_value(a, av, "__NUMERIC_OK__")
                    matched = True
            except (TypeError, ValueError):
                pass

    elif kind == "enum_value_remap":
        mapping = rule.get("map", {})
        for val in actual_vals:
            remapped = mapping.get(str(val))
            if remapped is not None:
                a = _replace_value(a, val, remapped)
                matched = True

    elif kind in ("field_optional", "schema_relaxed"):
        key = path.split(".")[-1].strip("'\"")
        a = _remove_key(a, key)
        e = _remove_key(e, key)
        matched = True

    return e, a, matched


def _remove_key(data, key: str):
    if isinstance(data, dict):
        return {k: _remove_key(v, key) for k, v in data.items() if k != key}
    if isinstance(data, list):
        return [_remove_key(item, key) for item in data]
    return data


def _replace_value(data, old_val, new_val):
    """Recursively replace old_val with new_val in a nested dict/list."""
    if isinstance(data, dict):
        return {k: _replace_value(v, old_val, new_val) for k, v in data.items()}
    if isinstance(data, list):
        return [_replace_value(item, old_val, new_val) for item in data]
    if data == old_val:
        return new_val
    return data


def compare(
    expected: dict,
    actual: dict,
    endpoint_label: str,
    tolerance_rules: list[dict] | None = None,
) -> dict:
    """Compare expected vs actual response, applying tolerance rules.

    Args:
        expected: Response body from the golden cassette.
        actual: Response body from the migrated app.
        endpoint_label: Human-readable label like 'GET /users/1'.
        tolerance_rules: List of rule dicts from tolerance-rules.yaml.

    Returns:
        Dict with endpoint, status (pass/fail), diff, and matched_rules.
    """
    rules = tolerance_rules or []
    e, a = expected, actual
    matched_rule_names = []

    ignore_order = False
    for rule in rules:
        e, a, hit = _apply_tolerance_rule(rule, e, a)
        if hit:
            matched_rule_names.append(rule.get("path", rule.get("kind", "unknown")))
        if rule.get("kind") == "ignore_order":
            ignore_order = True

    diff = DeepDiff(e, a, ignore_order=ignore_order, verbose_level=2)
    diff_dict = diff.to_dict() if diff else {}

    return {
        "endpoint": endpoint_label,
        "status": "pass" if not diff_dict else "fail",
        "diff": diff_dict,
        "matched_rules": matched_rule_names,
    }


def batch_compare(
    interactions: list[tuple[dict, dict, str]],
    tolerance_rules: list[dict] | None = None,
) -> list[dict]:
    """Compare a list of (expected, actual, label) tuples.

    Args:
        interactions: List of (expected_response, actual_response, endpoint_label).
        tolerance_rules: List of rule dicts.

    Returns:
        List of comparison result dicts.
    """
    return [compare(exp, act, label, tolerance_rules) for exp, act, label in interactions]
