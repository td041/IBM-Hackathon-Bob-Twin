"""Replay a VCR.py cassette against a running app and collect diffs."""

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

from twin_mcp import audit, diff_engine


def _load_cassette(cassette_path: str) -> list[dict]:
    path = Path(cassette_path)
    if not path.exists():
        raise FileNotFoundError(f"Cassette not found: {cassette_path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("interactions", [])


def _parse_body(body_str: str | None) -> dict | str | None:
    if body_str is None:
        return None
    try:
        return json.loads(body_str)
    except (json.JSONDecodeError, TypeError):
        return body_str


def _load_tolerance_rules(rules_path: str) -> dict | None:
    path = Path(rules_path)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def replay_and_diff(
    cassette_path: str,
    target_dir: str,
    tolerance_rules: dict | None = None,
    target_url: str = "http://localhost:8001",
) -> dict:
    """Replay all interactions from a cassette against the migrated app and diff.

    Args:
        cassette_path: Path to the VCR.py YAML cassette.
        target_dir: Project root of the migrated app.
        tolerance_rules: Parsed tolerance rules dict, or None to auto-load.
        target_url: Base URL where the migrated app is running.

    Returns:
        Dict with ok, run_id, equivalence_score, passed, failed, total,
        diffs_per_endpoint, tolerance_rules_applied, replayed_at.
    """
    from urllib.parse import urlparse

    if tolerance_rules is None:
        default_rules_path = str(
            Path(target_dir) / ".bob" / "skills" / "twin-validator" / "tolerance-rules.yaml"
        )
        tolerance_rules = _load_tolerance_rules(default_rules_path)

    rules_list = (tolerance_rules or {}).get("rules", [])

    interactions = _load_cassette(cassette_path)
    if not interactions:
        return {"ok": False, "errors": ["cassette has no interactions"]}

    # derive run_id from cassette filename: run_<run_id>.yaml
    stem = Path(cassette_path).stem
    run_id = stem.replace("run_", "") if stem.startswith("run_") else stem

    replayed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    diffs_per_endpoint = []

    with httpx.Client(base_url=target_url, timeout=10.0) as client:
        for interaction in interactions:
            req = interaction.get("request", {})
            resp = interaction.get("response", {})

            method = req.get("method", "GET").upper()
            uri = req.get("uri", "")
            parsed = urlparse(uri)
            path = parsed.path
            if parsed.query:
                path = f"{path}?{parsed.query}"

            req_body = req.get("body")
            if isinstance(req_body, dict):
                req_body = req_body.get("string")

            expected_body = _parse_body(
                resp.get("body", {}).get("string") if isinstance(resp.get("body"), dict) else resp.get("body")
            )
            expected_status = resp.get("status", {}).get("code", 200)

            try:
                kwargs: dict = {}
                if req_body:
                    kwargs["content"] = req_body.encode() if isinstance(req_body, str) else req_body
                    kwargs["headers"] = {"Content-Type": "application/json"}

                actual_resp = client.request(method, path, **kwargs)
                actual_status = actual_resp.status_code
                actual_body = _parse_body(actual_resp.text)
            except Exception as exc:
                diffs_per_endpoint.append({
                    "endpoint": f"{method} {parsed.path}",
                    "status": "fail",
                    "diff": {"connection_error": str(exc)},
                    "matched_rules": [],
                })
                continue

            label = f"{method} {parsed.path}"

            # status code mismatch is always a fail
            if actual_status != expected_status:
                diffs_per_endpoint.append({
                    "endpoint": label,
                    "status": "fail",
                    "diff": {
                        "status_code_changed": {
                            "old_value": expected_status,
                            "new_value": actual_status,
                        }
                    },
                    "matched_rules": [],
                })
                continue

            result = diff_engine.compare(
                expected_body or {},
                actual_body or {},
                label,
                rules_list,
            )
            diffs_per_endpoint.append(result)

    total = len(diffs_per_endpoint)
    passed = sum(1 for r in diffs_per_endpoint if r["status"] == "pass")
    failed = total - passed
    score = round(passed / total, 3) if total > 0 else 0.0

    def _safe_serialize(obj):
        if isinstance(obj, type):
            return obj.__name__
        if isinstance(obj, set):
            return sorted(str(x) for x in obj)
        return str(obj)

    safe_diffs = json.loads(json.dumps(diffs_per_endpoint, default=_safe_serialize))

    audit.append(run_id, "replay", {
        "cassette_path": cassette_path,
        "target_url": target_url,
        "equivalence_score": score,
        "passed": passed,
        "failed": failed,
        "total": total,
        "tolerance_rules_applied": len(rules_list),
        "diffs_per_endpoint": safe_diffs,
    })

    return {
        "ok": True,
        "run_id": run_id,
        "equivalence_score": score,
        "passed": passed,
        "failed": failed,
        "total": total,
        "diffs_per_endpoint": diffs_per_endpoint,
        "tolerance_rules_applied": len(rules_list),
        "replayed_at": replayed_at,
    }
