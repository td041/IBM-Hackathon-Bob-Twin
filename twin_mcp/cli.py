"""CLI fallback for Risk Mode A — same 4 functions invokable from terminal."""

import json
import sys


def _json_default(obj):
    """Fallback serializer for non-standard types from DeepDiff."""
    if isinstance(obj, type):
        return obj.__name__
    if isinstance(obj, set):
        return sorted(str(x) for x in obj)
    try:
        return str(obj)
    except Exception:
        return repr(obj)


def _print(data: dict) -> None:
    print(json.dumps(data, indent=2, default=_json_default))


def cmd_capture(args) -> None:
    from twin_mcp.capture import capture_baseline
    scenarios = args.scenarios if args.scenarios else []
    _print(capture_baseline(args.target, scenarios))


def cmd_replay(args) -> None:
    from twin_mcp.replay import replay_and_diff
    rules = None
    if args.rules:
        import yaml
        from pathlib import Path
        rules_path = Path(args.rules)
        if rules_path.exists():
            with open(rules_path) as f:
                rules = yaml.safe_load(f)
    _print(replay_and_diff(args.cassette, args.target, rules, args.url))


def cmd_drift(args) -> None:
    from twin_mcp.drift import compute_drift_metrics
    _print(compute_drift_metrics(args.target, args.ref))


def cmd_report(args) -> None:
    from twin_mcp.reports import generate_audit_report
    _print(generate_audit_report(args.run_id, args.format))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m twin_mcp.cli",
        description="Bob's Twin CLI — run MCP tools without Bob",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # capture
    p_cap = sub.add_parser("capture", help="Capture HTTP baseline into cassette")
    p_cap.add_argument("--target", required=True, help="Path to project root")
    p_cap.add_argument("--scenarios", nargs="+", help="Scenario scripts")

    # replay
    p_rep = sub.add_parser("replay", help="Replay cassette against migrated app")
    p_rep.add_argument("--cassette", required=True, help="Path to cassette YAML")
    p_rep.add_argument("--target", required=True, help="Path to project root")
    p_rep.add_argument("--rules", help="Path to tolerance-rules.yaml")
    p_rep.add_argument("--url", default="http://localhost:8001", help="Migrated app URL")

    # drift
    p_drft = sub.add_parser("drift", help="Compute drift metrics")
    p_drft.add_argument("--target", required=True, help="Path to project root")
    p_drft.add_argument("--ref", default="HEAD~1", help="Git baseline ref")

    # report
    p_rpt = sub.add_parser("report", help="Generate audit report")
    p_rpt.add_argument("--run-id", required=True, dest="run_id", help="Run ID")
    p_rpt.add_argument("--format", default="pdf", choices=["pdf", "markdown", "json"])

    args = parser.parse_args()

    dispatch = {
        "capture": cmd_capture,
        "replay": cmd_replay,
        "drift": cmd_drift,
        "report": cmd_report,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
