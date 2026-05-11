"""VCR.py wrapper for capturing HTTP interactions as cassettes."""

import hashlib
import importlib.util
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import yaml

from twin_mcp import audit

_CASSETTE_DIR = Path(os.environ.get("TWIN_CASSETTE_DIR", "golden_cassettes"))


def _cassette_path(run_id: str) -> Path:
    _CASSETTE_DIR.mkdir(parents=True, exist_ok=True)
    return _CASSETTE_DIR / f"run_{run_id}.yaml"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _run_scenario(scenario: str, cassette_path: Path) -> dict:
    """Run a scenario script inside VCR.py context to record HTTP interactions.

    Args:
        scenario: Absolute path to a Python script that makes HTTP calls.
        cassette_path: Path where VCR.py writes the cassette YAML.

    Returns:
        Dict with ok and optional error string.
    """
    import vcr

    cassette_path.parent.mkdir(parents=True, exist_ok=True)
    my_vcr = vcr.VCR(
        record_mode="new_episodes",
        match_on=["method", "scheme", "host", "port", "path", "query"],
    )

    scenario_path = Path(scenario)
    if not scenario_path.exists():
        return {"ok": False, "error": f"scenario file not found: {scenario}"}

    # Load the scenario module spec so we can exec it in a fresh namespace
    spec = importlib.util.spec_from_file_location("_scenario_", str(scenario_path))
    if spec is None or spec.loader is None:
        return {"ok": False, "error": f"cannot load scenario: {scenario}"}

    module = importlib.util.module_from_spec(spec)

    try:
        with my_vcr.use_cassette(str(cassette_path)):
            spec.loader.exec_module(module)
            # call run() if the module exposes it (seed scripts define run())
            if hasattr(module, "run"):
                module.run()
    except SystemExit:
        pass  # seed scripts may call sys.exit — ignore
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    return {"ok": True}


def _count_interactions(cassette_path: Path) -> int:
    if not cassette_path.exists():
        return 0
    with open(cassette_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "interactions" not in data:
        return 0
    return len(data["interactions"])


def _list_endpoints(cassette_path: Path) -> list[str]:
    if not cassette_path.exists():
        return []
    with open(cassette_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "interactions" not in data:
        return []
    seen: list[str] = []
    for interaction in data["interactions"]:
        method = interaction.get("request", {}).get("method", "GET")
        uri = interaction.get("request", {}).get("uri", "")
        label = f"{method} {urlparse(uri).path}"
        if label not in seen:
            seen.append(label)
    return seen


def capture_baseline(target_dir: str, scenarios: list[str]) -> dict:
    """Capture HTTP interactions from scenario scripts into a VCR.py cassette.

    Args:
        target_dir: Absolute path to the project root.
        scenarios: List of Python script paths that make HTTP calls to localhost.

    Returns:
        Dict with ok, run_id, cassette_path, n_interactions, endpoints_covered,
        captured_at, and errors.
    """
    import uuid

    run_id = uuid.uuid4().hex[:8]
    cassette_path = _cassette_path(run_id)
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    errors: list[str] = []

    # Add target_dir to sys.path so scenario imports work
    target = str(Path(target_dir).resolve())
    if target not in sys.path:
        sys.path.insert(0, target)

    for scenario in scenarios:
        full = str(Path(target_dir) / scenario) if not Path(scenario).is_absolute() else scenario
        result = _run_scenario(full, cassette_path)
        if not result["ok"]:
            errors.append(f"{scenario}: {result['error']}")

    n_interactions = _count_interactions(cassette_path)

    if n_interactions == 0:
        return {"ok": False, "errors": errors or ["no HTTP interactions captured"]}

    cassette_hash = _sha256_file(cassette_path)
    endpoints = _list_endpoints(cassette_path)

    audit.append(run_id, "capture", {
        "cassette_path": str(cassette_path),
        "cassette_hash": cassette_hash,
        "n_interactions": n_interactions,
        "endpoints_covered": endpoints,
        "scenarios": scenarios,
    })

    return {
        "ok": True,
        "run_id": run_id,
        "cassette_path": str(cassette_path),
        "n_interactions": n_interactions,
        "endpoints_covered": endpoints,
        "captured_at": captured_at,
        "errors": errors,
    }
