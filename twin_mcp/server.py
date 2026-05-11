"""FastMCP entry point — registers the 4 Bob's Twin tools."""

from fastmcp import FastMCP

from twin_mcp import capture, drift, replay, reports

mcp = FastMCP("twin-mcp")


@mcp.tool
def capture_baseline(target_dir: str, scenarios: list[str]) -> dict:
    """Capture HTTP baseline interactions from scenario scripts into a cassette.

    Args:
        target_dir: Absolute path to the project root.
        scenarios: List of Python script paths that make HTTP calls to localhost.

    Returns:
        ok, run_id, cassette_path, n_interactions, endpoints_covered, captured_at, errors.
    """
    try:
        return capture.capture_baseline(target_dir, scenarios)
    except Exception as exc:
        return {"ok": False, "errors": [str(exc)]}


@mcp.tool
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


@mcp.tool
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


@mcp.tool
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
    mcp.run()
