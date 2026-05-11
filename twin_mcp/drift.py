"""Code quality drift metrics using radon and vulture."""

import subprocess
import sys
from pathlib import Path

from twin_mcp import audit


def _run_radon_cc(target_dir: str) -> float:
    """Return average cyclomatic complexity for target_dir."""
    result = subprocess.run(
        [sys.executable, "-m", "radon", "cc", target_dir, "--average", "-s"],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if "Average complexity" in line:
            try:
                return float(line.split("(")[-1].rstrip(")").strip())
            except (ValueError, IndexError):
                pass
    return 0.0


def _run_radon_mi(target_dir: str) -> float:
    """Return average maintainability index for target_dir."""
    result = subprocess.run(
        [sys.executable, "-m", "radon", "mi", target_dir, "--show"],
        capture_output=True,
        text=True,
    )
    values = []
    for line in result.stdout.splitlines():
        parts = line.strip().split(" - ")
        if len(parts) >= 2:
            try:
                values.append(float(parts[-1].strip()))
            except ValueError:
                pass
    return round(sum(values) / len(values), 2) if values else 0.0


def _run_vulture(target_dir: str) -> int:
    """Return count of dead code items found by vulture."""
    result = subprocess.run(
        [sys.executable, "-m", "vulture", target_dir, "--min-confidence", "80"],
        capture_output=True,
        text=True,
    )
    return len([l for l in result.stdout.splitlines() if l.strip()])


def _git_diff_stats(target_dir: str, baseline_ref: str) -> dict[str, int]:
    result = subprocess.run(
        ["git", "-C", target_dir, "diff", "--stat", baseline_ref],
        capture_output=True,
        text=True,
    )
    files_changed = 0
    lines_added = 0
    lines_removed = 0
    for line in result.stdout.splitlines():
        if "changed" in line:
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if "changed" in part:
                    try:
                        files_changed = int(part.split()[0])
                    except ValueError:
                        pass
                elif "insertion" in part:
                    try:
                        lines_added = int(part.split()[0])
                    except ValueError:
                        pass
                elif "deletion" in part:
                    try:
                        lines_removed = int(part.split()[0])
                    except ValueError:
                        pass
    return {"files_changed": files_changed, "lines_added": lines_added, "lines_removed": lines_removed}


def compute_drift_metrics(target_dir: str, baseline_ref: str = "HEAD~1") -> dict:
    """Compute code quality drift metrics between current state and a git baseline.

    Args:
        target_dir: Project root to analyze.
        baseline_ref: Git ref to compare against (default: previous commit).

    Returns:
        Dict with ok, cc_delta, mi_delta, dead_funcs_added, files_changed,
        lines_added, lines_removed.
    """
    # current metrics
    cc_current = _run_radon_cc(target_dir)
    mi_current = _run_radon_mi(target_dir)
    dead_current = _run_vulture(target_dir)

    # baseline metrics via git stash trick — safer: checkout baseline in temp worktree
    # For simplicity, compare against HEAD~1 by reading git show
    import tempfile
    import shutil

    cc_baseline = 0.0
    mi_baseline = 0.0
    dead_baseline = 0

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["git", "-C", target_dir, "worktree", "add", tmpdir, baseline_ref],
                capture_output=True,
                check=True,
            )
            cc_baseline = _run_radon_cc(tmpdir)
            mi_baseline = _run_radon_mi(tmpdir)
            dead_baseline = _run_vulture(tmpdir)
            subprocess.run(
                ["git", "-C", target_dir, "worktree", "remove", "--force", tmpdir],
                capture_output=True,
            )
    except subprocess.CalledProcessError:
        # No git history available — return zeros
        pass

    diff_stats = _git_diff_stats(target_dir, baseline_ref)

    # derive run_id from most recent audit entry if available
    run_id = "unknown"
    import os
    audit_dir = Path(os.environ.get("TWIN_AUDIT_DIR", "audit_trail"))
    jsonl_files = sorted(audit_dir.glob("run_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if jsonl_files:
        run_id = jsonl_files[0].stem.replace("run_", "")

    result = {
        "ok": True,
        "cc_delta": round(cc_current - cc_baseline, 2),
        "mi_delta": round(mi_current - mi_baseline, 2),
        "dead_funcs_added": max(0, dead_current - dead_baseline),
        **diff_stats,
    }

    if run_id != "unknown":
        audit.append(run_id, "drift", result)

    return result
