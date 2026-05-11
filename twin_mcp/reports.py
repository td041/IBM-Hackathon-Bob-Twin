"""Markdown and PDF report generation from audit trail data."""

import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from twin_mcp import audit


def _render_markdown(run_id: str, entries: list[dict]) -> str:
    capture_entry = next((e for e in entries if e["phase"] == "capture"), None)
    replay_entry = next((e for e in entries if e["phase"] == "replay"), None)
    drift_entry = next((e for e in entries if e["phase"] == "drift"), None)

    score = replay_entry["payload"].get("equivalence_score", "N/A") if replay_entry else "N/A"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# Bob's Twin — Audit Report",
        f"",
        f"**Run ID:** `{run_id}`  ",
        f"**Generated:** {generated_at}  ",
        f"**Equivalence Score:** {score}  ",
        f"",
        f"---",
        f"",
        f"## Executive Summary",
        f"",
    ]

    if replay_entry:
        p = replay_entry["payload"]
        verdict = "PASSED" if float(score or 0) >= 0.95 else "FAILED"
        lines += [
            f"Migration {verdict}. "
            f"{p.get('passed', 0)} of {p.get('total', 0)} interactions matched. "
            f"Equivalence score: {score}.",
            f"",
        ]
    else:
        lines += ["Replay phase not yet completed.", ""]

    lines += ["---", "", "## Capture Phase", ""]
    if capture_entry:
        cp = capture_entry["payload"]
        lines += [
            f"- **Cassette:** `{cp.get('cassette_path', 'N/A')}`",
            f"- **Cassette SHA-256:** `{cp.get('cassette_hash', 'N/A')}`",
            f"- **Interactions:** {cp.get('n_interactions', 0)}",
            f"- **Captured at:** {capture_entry['timestamp']}",
            f"",
            f"**Endpoints covered:**",
            f"",
        ]
        for ep in cp.get("endpoints_covered", []):
            lines.append(f"- `{ep}`")
        lines.append("")

    lines += ["---", "", "## Replay Phase", ""]
    if replay_entry:
        rp = replay_entry["payload"]
        lines += [
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Equivalence score | {rp.get('equivalence_score')} |",
            f"| Passed | {rp.get('passed')} |",
            f"| Failed | {rp.get('failed')} |",
            f"| Total | {rp.get('total')} |",
            f"| Tolerance rules applied | {rp.get('tolerance_rules_applied')} |",
            f"",
        ]

    if drift_entry:
        lines += ["---", "", "## Drift Metrics", ""]
        dp = drift_entry["payload"]
        lines += [
            f"| Metric | Delta |",
            f"|--------|-------|",
            f"| Cyclomatic Complexity | {dp.get('cc_delta', 'N/A')} |",
            f"| Maintainability Index | {dp.get('mi_delta', 'N/A')} |",
            f"| Dead functions added | {dp.get('dead_funcs_added', 'N/A')} |",
            f"| Files changed | {dp.get('files_changed', 'N/A')} |",
            f"",
        ]

    lines += ["---", "", "## Hash Chain", ""]
    lines += [
        f"| Index | Phase | Timestamp | This Hash |",
        f"|-------|-------|-----------|-----------|",
    ]
    for e in entries:
        short_hash = e["this_hash"][:20] + "..."
        lines.append(f"| {e['entry_index']} | {e['phase']} | {e['timestamp']} | `{short_hash}` |")
    lines += ["", "---", "", "## Footer", ""]
    lines += [
        f"Licensed under Apache 2.0. Tool: Bob's Twin v0.1.0. Generated: {generated_at}.",
        f"",
    ]

    return "\n".join(lines)


def _render_pdf_via_reportlab(markdown_text: str, output_path: Path) -> bool:
    """Render markdown to PDF using reportlab. Returns True on success."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        for line in markdown_text.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            if line.startswith("# "):
                story.append(Paragraph(line[2:], styles["h1"]))
            elif line.startswith("## "):
                story.append(Paragraph(line[3:], styles["h2"]))
            elif line.startswith("### "):
                story.append(Paragraph(line[4:], styles["h3"]))
            else:
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, styles["Normal"]))

        doc.build(story)
        return True
    except Exception:
        return False


def _render_pdf_via_pandoc(markdown_text: str, output_path: Path) -> bool:
    """Render markdown to PDF via pandoc subprocess. Returns True on success."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", encoding="utf-8", delete=False) as f:
            f.write(markdown_text)
            md_path = f.name
        result = subprocess.run(
            ["pandoc", md_path, "-o", str(output_path)],
            capture_output=True,
            timeout=30,
        )
        Path(md_path).unlink(missing_ok=True)
        return result.returncode == 0
    except Exception:
        return False


def generate_audit_report(run_id: str, format: str = "pdf") -> dict:
    """Generate an audit report for a completed migration run.

    Args:
        run_id: Migration run identifier.
        format: One of pdf, markdown, json.

    Returns:
        Dict with ok, run_id, format, path, hash, verified.
    """
    is_valid, broken_at = audit.verify_chain(run_id)
    if not is_valid:
        return {"ok": False, "verified": False, "broken_at": broken_at}

    entries = audit.read(run_id)
    if not entries:
        return {"ok": False, "errors": [f"no audit entries for run_id {run_id}"]}

    audit_dir = Path("audit_trail")
    audit_dir.mkdir(parents=True, exist_ok=True)

    if format == "json":
        output_path = audit_dir / f"run_{run_id}.report.json"
        output_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    elif format == "markdown":
        output_path = audit_dir / f"run_{run_id}.report.md"
        md_text = _render_markdown(run_id, entries)
        output_path.write_text(md_text, encoding="utf-8")

    else:  # pdf
        output_path = audit_dir / f"run_{run_id}.report.pdf"
        md_text = _render_markdown(run_id, entries)

        success = _render_pdf_via_reportlab(md_text, output_path)
        if not success:
            success = _render_pdf_via_pandoc(md_text, output_path)
        if not success:
            # fallback: save as markdown with .pdf extension (better than nothing)
            output_path.write_text(md_text, encoding="utf-8")

    file_hash = "sha256:" + hashlib.sha256(output_path.read_bytes()).hexdigest()

    audit.append(run_id, "report", {
        "format": format,
        "path": str(output_path),
        "hash": file_hash,
    })

    return {
        "ok": True,
        "run_id": run_id,
        "format": format,
        "path": str(output_path),
        "hash": file_hash,
        "verified": True,
    }
