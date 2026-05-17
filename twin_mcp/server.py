"""FastMCP entry point — registers the 6 Bob's Twin tools."""

from fastmcp import FastMCP

from twin_mcp import capture, drift, replay, reports

mcp = FastMCP("twin-mcp")


@mcp.tool()
def reset_apps(
    v1_url: str = "http://localhost:8001",
    v2_url: str = "http://localhost:8002",
) -> dict:
    """Reset both v1 and v2 apps to clean initial state before capture.

    Args:
        v1_url: Base URL of the v1 legacy app.
        v2_url: Base URL of the v2 migrated app.

    Returns:
        ok, v1_reset, v2_reset, message.
    """
    import requests as _requests

    results = {}
    for label, url in [("v1", v1_url), ("v2", v2_url)]:
        try:
            r = _requests.post(f"{url}/admin/reset", timeout=10)
            results[f"{label}_reset"] = r.status_code in (200, 204)
        except Exception as exc:
            results[f"{label}_reset"] = False
            results[f"{label}_error"] = str(exc)

    ok = results.get("v1_reset", False) and results.get("v2_reset", False)
    return {"ok": ok, "message": "both apps reset" if ok else "one or more resets failed", **results}


@mcp.tool()
def capture_baseline(target_dir: str, scenarios: list[str]) -> dict:
    """Start capturing HTTP baseline interactions in the background. Returns immediately.

    Args:
        target_dir: Absolute path to the project root.
        scenarios: List of Python script paths that make HTTP calls to localhost.

    Returns:
        ok, run_id, cassette_path, status="started", estimated_seconds, next_step.
        Call capture_status(run_id, wait=true) to poll until complete.
    """
    try:
        return capture.capture_baseline(target_dir, scenarios)
    except Exception as exc:
        return {"ok": False, "errors": [str(exc)]}


@mcp.tool()
def capture_status(run_id: str, wait: bool = True) -> dict:
    """Poll the status of a background capture job.

    Args:
        run_id: The run_id returned by capture_baseline.
        wait: If True, blocks until complete (polls every 2s, max 120s).

    Returns:
        status (pending/complete/error), and when complete: n_interactions,
        endpoints_covered, cassette_path.
    """
    try:
        return capture.capture_status(run_id, wait)
    except Exception as exc:
        return {"ok": False, "errors": [str(exc)]}


@mcp.tool()
def replay_and_diff(
    cassette_path: str,
    target_dir: str,
    tolerance_rules: dict | None = None,
    target_url: str = "http://localhost:8001",
) -> dict:
    """Replay a cassette against the migrated app and compute equivalence score.

    Args:
        cassette_path: Path to the VCR.py YAML cassette from capture_baseline.
        target_dir: Project root of the migrated app.
        tolerance_rules: Parsed tolerance rules dict, or None to auto-load from .bob/.
        target_url: Base URL where the migrated app is running.

    Returns:
        ok, run_id, equivalence_score, passed, failed, total, diffs_per_endpoint,
        tolerance_rules_applied, replayed_at.
    """
    try:
        return replay.replay_and_diff(cassette_path, target_dir, tolerance_rules, target_url)
    except Exception as exc:
        return {"ok": False, "errors": [str(exc)]}


@mcp.tool()
def compute_drift_metrics(target_dir: str, baseline_ref: str = "HEAD~1") -> dict:
    """Compute code quality drift metrics between current state and a git baseline.

    Args:
        target_dir: Project root to analyze.
        baseline_ref: Git ref to compare against (default: HEAD~1).

    Returns:
        ok, cc_delta, mi_delta, dead_funcs_added, files_changed, lines_added, lines_removed.
    """
    try:
        return drift.compute_drift_metrics(target_dir, baseline_ref)
    except Exception as exc:
        return {"ok": False, "errors": [str(exc)]}


@mcp.tool()
def generate_audit_report(run_id: str, format: str = "pdf") -> dict:
    """Generate a signed audit report for a completed migration run.

    Args:
        run_id: Migration run identifier from capture_baseline.
        format: Output format — pdf, markdown, or json.

    Returns:
        ok, run_id, format, path, hash, verified.
    """
    try:
        return reports.generate_audit_report(run_id, format)
    except Exception as exc:
        return {"ok": False, "errors": [str(exc)]}


if __name__ == "__main__":
    mcp.run(transport="stdio")
