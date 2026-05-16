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


_REPORT_CSS = """
@page {
    size: A4;
    margin: 1.8cm 1.6cm;
    @bottom-right {
        content: "Bob's Twin Audit Report — Page " counter(page) " of " counter(pages);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, sans-serif;
        font-size: 8pt;
        color: #6f6f6f;
    }
}
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, sans-serif;
    color: #161616;
    line-height: 1.45;
    font-size: 10pt;
}
h1 {
    color: #0f62fe;
    border-bottom: 3px solid #0f62fe;
    padding-bottom: 0.3em;
    margin-top: 0;
    font-size: 24pt;
    font-weight: 600;
}
h2 {
    color: #161616;
    font-size: 14pt;
    margin-top: 1.6em;
    margin-bottom: 0.4em;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 0.2em;
}
h3 { color: #393939; font-size: 12pt; margin-top: 1.2em; }
p, li { margin: 0.4em 0; }
strong { color: #161616; }
hr { display: none; }  /* markdown --- separators are noisy in PDF */

table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.8em 0;
    font-size: 9.5pt;
}
th, td {
    border: 1px solid #d0d0d0;
    padding: 6px 10px;
    text-align: left;
    vertical-align: top;
}
th {
    background: #f4f4f4;
    font-weight: 600;
    color: #161616;
}
tr:nth-child(even) td { background: #fafafa; }

code, pre {
    font-family: "SF Mono", Menlo, Monaco, Consolas, "Courier New", monospace;
    font-size: 9pt;
    background: #f4f4f4;
    color: #393939;
    padding: 1px 4px;
    border-radius: 2px;
    word-break: break-all;
}
pre { padding: 10px; line-height: 1.35; }

/* Hero score banner injected before Executive Summary */
.score-hero {
    text-align: center;
    margin: 1.2em 0 1.8em 0;
    padding: 1.2em;
    background: linear-gradient(135deg, #f4f4f4 0%, #e8e8e8 100%);
    border-left: 6px solid #0f62fe;
}
.score-hero .label {
    font-size: 9pt;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #6f6f6f;
    margin-bottom: 0.2em;
}
.score-hero .value {
    font-size: 56pt;
    font-weight: 300;
    color: #0f62fe;
    line-height: 1;
    margin: 0.1em 0;
}
.score-hero .verdict {
    font-size: 11pt;
    color: #161616;
    margin-top: 0.4em;
}
.score-hero.fail .value { color: #da1e28; }
.score-hero.pass .value { color: #198038; }
"""


def _build_hero_banner(replay_entry: dict | None) -> str:
    """HTML hero banner with prominent equivalence score; injected after H1."""
    if replay_entry is None:
        return ""
    p = replay_entry["payload"]
    score = p.get("equivalence_score", 0.0)
    passed = p.get("passed", 0)
    total = p.get("total", 0)
    is_pass = float(score or 0) >= 0.95
    state = "pass" if is_pass else "fail"
    verdict = "PASSED" if is_pass else "FAILED"
    return (
        f'<div class="score-hero {state}">'
        f'<div class="label">Equivalence Score</div>'
        f'<div class="value">{score}</div>'
        f'<div class="verdict">Migration {verdict} — {passed} of {total} interactions matched</div>'
        f'</div>'
    )


def _render_pdf_via_weasyprint(
    markdown_text: str,
    output_path: Path,
    replay_entry: dict | None,
) -> bool:
    """Render markdown to a styled PDF via weasyprint. Returns True on success.

    Markdown is converted to HTML with markdown2 (tables + fenced-code extras),
    a hero score banner is injected after the title, and the whole document is
    styled with print-quality CSS before weasyprint renders to PDF.
    """
    try:
        import markdown2
        from weasyprint import HTML

        html_body = markdown2.markdown(
            markdown_text,
            extras=["tables", "fenced-code-blocks", "cuddled-lists"],
        )

        # Inject hero banner immediately after the first </h1>
        hero = _build_hero_banner(replay_entry)
        if hero and "</h1>" in html_body:
            html_body = html_body.replace("</h1>", "</h1>" + hero, 1)

        full_html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>{_REPORT_CSS}</style></head><body>{html_body}</body></html>"
        )
        HTML(string=full_html).write_pdf(str(output_path))
        return True
    except Exception:
        return False


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
        replay_entry = next((e for e in entries if e["phase"] == "replay"), None)

        # Primary: weasyprint with styled CSS (handles tables + monospace cleanly)
        success = _render_pdf_via_weasyprint(md_text, output_path, replay_entry)
        if not success:
            # Secondary: bare reportlab (only headers + plain paragraphs — ugly tables)
            success = _render_pdf_via_reportlab(md_text, output_path)
        if not success:
            # Tertiary: pandoc subprocess if available
            success = _render_pdf_via_pandoc(md_text, output_path)
        if not success:
            # Last resort: save markdown source with .pdf extension
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
