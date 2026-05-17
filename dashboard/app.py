"""Streamlit live dashboard — polls audit_trail/*.jsonl every 2 seconds."""

import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

AUDIT_DIR = Path(os.environ.get("TWIN_AUDIT_DIR", "audit_trail"))
CASSETTE_DIR = Path(os.environ.get("TWIN_CASSETTE_DIR", "golden_cassettes"))
TARGET_DIR = str(Path("."))
POLL_INTERVAL = 2

# Add project root to sys.path so twin_mcp is importable
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

st.set_page_config(
    page_title="Bob's Twin",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #0e1117; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding: 1.5rem 2rem 2rem; max-width: 1400px; }

/* ── Score card ── */
.score-card {
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
    border: 1px solid #2d3561;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    text-align: center;
    margin-bottom: 1rem;
}
.score-number {
    font-size: 5rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -2px;
    font-family: 'SF Mono', monospace;
}
.score-label { color: #8892b0; font-size: 0.85rem; letter-spacing: 2px; text-transform: uppercase; margin-top: 0.5rem; }

/* ── Metric pill ── */
.metric-row { display: flex; gap: 1rem; margin: 1rem 0; }
.metric-pill {
    flex: 1;
    background: #1a1f2e;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    text-align: center;
    border: 1px solid #2d3561;
}
.metric-pill .val { font-size: 1.8rem; font-weight: 700; }
.metric-pill .lbl { font-size: 0.75rem; color: #8892b0; text-transform: uppercase; letter-spacing: 1px; }

/* ── Phase timeline ── */
.phase-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
}
.phase-done { background: #0d2818; border: 1px solid #1a5c36; color: #4ade80; }
.phase-pending { background: #1a1f2e; border: 1px solid #2d3561; color: #4a5568; }
.phase-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.phase-dot-done { background: #4ade80; box-shadow: 0 0 6px #4ade80; }
.phase-dot-pending { background: #4a5568; }
.phase-ts { font-size: 0.72rem; color: #4a5568; margin-left: auto; font-family: monospace; }

/* ── Endpoint row ── */
.ep-pass {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.45rem 0.75rem; border-radius: 6px; margin-bottom: 3px;
    background: #0a1f14; border-left: 3px solid #22c55e; font-size: 0.82rem;
}
.ep-fail {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.45rem 0.75rem; border-radius: 6px; margin-bottom: 3px;
    background: #1f0a0a; border-left: 3px solid #ef4444; font-size: 0.82rem;
}
.ep-name { font-family: 'SF Mono', monospace; color: #e2e8f0; }
.ep-diff { font-size: 0.72rem; color: #ef4444; margin-left: auto; }

/* ── Hash chain ── */
.hash-box {
    background: #0d1117;
    border: 1px solid #2d3561;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-family: monospace;
    font-size: 0.72rem;
    color: #4a9eff;
    line-height: 1.8;
}

/* ── Section header ── */
.section-title {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #4a9eff;
    margin-bottom: 0.75rem;
    border-bottom: 1px solid #1e2d4a;
    padding-bottom: 0.4rem;
}

/* ── Waiting state ── */
.waiting-box {
    background: #1a1f2e;
    border: 1px dashed #2d3561;
    border-radius: 12px;
    padding: 3rem;
    text-align: center;
    color: #4a5568;
}
.waiting-box .big { font-size: 3rem; margin-bottom: 1rem; }
.waiting-box p { font-size: 0.9rem; margin: 0.25rem 0; }

/* ── Top bar ── */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #1e2d4a;
}
.topbar-title { font-size: 1.4rem; font-weight: 700; color: #e2e8f0; }
.topbar-sub { font-size: 0.8rem; color: #4a5568; margin-top: 2px; }
.run-badge {
    background: #1a1f2e;
    border: 1px solid #2d3561;
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-family: monospace;
    font-size: 0.8rem;
    color: #4a9eff;
}
.live-dot {
    display: inline-block; width: 8px; height: 8px;
    background: #4ade80; border-radius: 50%;
    box-shadow: 0 0 6px #4ade80;
    margin-right: 6px;
    animation: pulse 1.5s infinite;
}
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }

/* ── Replay status banner ── */
.replay-running {
    background: #1a2a1a;
    border: 1px solid #22c55e;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
    color: #4ade80;
    margin-bottom: 0.75rem;
}
.replay-error {
    background: #2a1a1a;
    border: 1px solid #ef4444;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
    color: #ef4444;
    margin-bottom: 0.75rem;
}
</style>
""", unsafe_allow_html=True)


def _latest_cassette() -> str | None:
    """Return the most recently modified cassette path."""
    if not CASSETTE_DIR.exists():
        return None
    files = sorted(CASSETTE_DIR.glob("run_*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)
    return str(files[0]) if files else None


def _load_latest_run() -> tuple[str | None, list[dict]]:
    if not AUDIT_DIR.exists():
        return None, []
    files = sorted(AUDIT_DIR.glob("run_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None, []
    run_id = files[0].stem.replace("run_", "")
    entries = []
    with open(files[0], encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return run_id, entries


def _get_phase(entries, phase):
    for e in reversed(entries):
        if e.get("phase") == phase:
            return e
    return None


def _get_replay_for_url(entries, url_fragment: str):
    """Return the latest replay entry whose target_url contains url_fragment."""
    for e in reversed(entries):
        if e.get("phase") == "replay":
            if url_fragment in e.get("payload", {}).get("target_url", ""):
                return e
    return None


def _score_color(score: float) -> str:
    if score >= 0.95:
        return "#4ade80"
    if score >= 0.80:
        return "#fbbf24"
    return "#ef4444"


def _fmt_ts(ts: str) -> str:
    return ts[11:19] if len(ts) >= 19 else ts


def _diff_summary(diff: dict) -> str:
    if not diff:
        return ""
    if "status_code_changed" in diff:
        old = diff["status_code_changed"]["old_value"]
        new = diff["status_code_changed"]["new_value"]
        return f"{old} → {new}"
    if "type_changes" in diff:
        fields = list(diff["type_changes"].keys())
        f = fields[0].replace("root", "").strip("['']")
        chg = diff["type_changes"][fields[0]]
        return f"{f}: {chg['old_type']} → {chg['new_type']}"
    if "values_changed" in diff:
        fields = list(diff["values_changed"].keys())
        f = fields[0].replace("root", "").strip("['']")
        return f"{f} changed"
    keys = list(diff.keys())
    return keys[0] if keys else "diff"


def _render_score_card(label: str, entry, capture_entry):
    if entry:
        rp = entry["payload"]
        score = rp.get("equivalence_score", 0.0)
        passed = rp.get("passed", 0)
        failed = rp.get("failed", 0)
        total = rp.get("total", 0)
        color = _score_color(score)
        score_str = f"{score:.3f}".rstrip('0').rstrip('.')
        st.markdown(f"""
        <div class="score-card">
          <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:2px;color:#4a5568;margin-bottom:0.5rem">{label}</div>
          <div class="score-number" style="color:{color}">{score_str}</div>
          <div class="score-label">Equivalence Score</div>
        </div>
        <div class="metric-row">
          <div class="metric-pill">
            <div class="val" style="color:#4ade80">{passed}</div>
            <div class="lbl">Passed</div>
          </div>
          <div class="metric-pill">
            <div class="val" style="color:#ef4444">{failed}</div>
            <div class="lbl">Failed</div>
          </div>
          <div class="metric-pill">
            <div class="val" style="color:#94a3b8">{total}</div>
            <div class="lbl">Total</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(score)
    elif capture_entry:
        cp = capture_entry["payload"]
        n = cp.get("n_interactions", 0)
        st.markdown(f"""
        <div class="score-card">
          <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:2px;color:#4a5568;margin-bottom:0.5rem">{label}</div>
          <div class="score-number" style="color:#4a9eff">{n}</div>
          <div class="score-label">Interactions Captured</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="score-card">
          <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:2px;color:#4a5568;margin-bottom:0.5rem">{label}</div>
          <div class="score-number" style="color:#4a5568">—</div>
          <div class="score-label">Awaiting replay</div>
        </div>
        """, unsafe_allow_html=True)


def _render_endpoints(entry):
    if not entry:
        st.markdown("""
        <div class="waiting-box" style="margin-top:1rem;padding:1.5rem">
          <p>Awaiting <code>replay_and_diff</code>…</p>
        </div>
        """, unsafe_allow_html=True)
        return
    diffs = entry["payload"].get("diffs_per_endpoint", [])
    if not diffs:
        return
    seen_eps: dict[str, dict] = {}
    for d in diffs:
        ep = d["endpoint"]
        if ep not in seen_eps:
            seen_eps[ep] = {"pass": 0, "fail": 0, "diff": d.get("diff", {})}
        if d["status"] == "pass":
            seen_eps[ep]["pass"] += 1
        else:
            seen_eps[ep]["fail"] += 1
            seen_eps[ep]["diff"] = d.get("diff", {})

    pass_eps = {k: v for k, v in seen_eps.items() if v["fail"] == 0}
    fail_eps = {k: v for k, v in seen_eps.items() if v["fail"] > 0}

    st.markdown(f'<div class="section-title">{len(fail_eps)} failing / {len(pass_eps)} passing</div>', unsafe_allow_html=True)

    for ep, info in fail_eps.items():
        summary = _diff_summary(info["diff"])
        st.markdown(f"""
        <div class="ep-fail">
          <span style="color:#ef4444">✗</span>
          <span class="ep-name">{ep}</span>
          <span class="ep-diff">{summary}</span>
        </div>""", unsafe_allow_html=True)

    for ep, info in pass_eps.items():
        st.markdown(f"""
        <div class="ep-pass">
          <span style="color:#22c55e">✓</span>
          <span class="ep-name">{ep}</span>
          <span style="font-size:0.72rem;color:#22c55e;margin-left:auto">{info['pass']}× ok</span>
        </div>""", unsafe_allow_html=True)

    if fail_eps:
        with st.expander(f"Diff detail — {len(fail_eps)} endpoint(s)"):
            for ep, info in fail_eps.items():
                st.markdown(f"**`{ep}`**")
                st.json(info["diff"])


run_id, entries = _load_latest_run()
capture_entry = _get_phase(entries, "capture")
v1_entry = _get_replay_for_url(entries, "8001")
v2_entry = _get_replay_for_url(entries, "8002")

# ── Top bar ──────────────────────────────────────────────────────────────────
badge = f'<span class="run-badge">run: {run_id}</span>' if run_id else ""
st.markdown(f"""
<div class="topbar">
  <div>
    <div class="topbar-title">🧬 Bob's Twin</div>
    <div class="topbar-sub"><span class="live-dot"></span>Migration Equivalence Monitor</div>
  </div>
  {badge}
</div>
""", unsafe_allow_html=True)

# ── No data yet ───────────────────────────────────────────────────────────────
if not run_id:
    st.markdown("""
    <div class="waiting-box">
      <div class="big">🧬</div>
      <p style="color:#e2e8f0;font-size:1.1rem;font-weight:600;">Waiting for migration run</p>
      <p>Run <code>capture_baseline</code> to start</p>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(POLL_INTERVAL)
    st.rerun()
    st.stop()

# ── Main layout: v1 | v2 | timeline ──────────────────────────────────────────
col_v1, col_v2, col_right = st.columns([2, 2, 1], gap="large")

with col_v1:
    _render_score_card("v1 Legacy — Ground Truth", v1_entry, capture_entry)
    _render_endpoints(v1_entry)

with col_v2:
    _render_score_card("v2 Migrated — Under Test", v2_entry, capture_entry)
    _render_endpoints(v2_entry)

with col_right:
    # Phase timeline
    st.markdown('<div class="section-title">Phase Timeline</div>', unsafe_allow_html=True)
    phases_seen = {e["phase"]: e["timestamp"] for e in entries}
    phase_icons = {"capture": "①", "migrate": "②", "replay": "③", "drift": "④", "report": "⑤"}
    for phase in ["capture", "migrate", "replay", "drift", "report"]:
        if phase in phases_seen:
            ts = _fmt_ts(phases_seen[phase])
            st.markdown(f"""
            <div class="phase-item phase-done">
              <div class="phase-dot phase-dot-done"></div>
              <span>{phase_icons[phase]} <strong>{phase.upper()}</strong></span>
              <span class="phase-ts">{ts}</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="phase-item phase-pending">
              <div class="phase-dot phase-dot-pending"></div>
              <span>{phase_icons[phase]} {phase.upper()}</span>
            </div>""", unsafe_allow_html=True)

    # Hash chain
    if entries:
        st.markdown('<div class="section-title" style="margin-top:1.2rem">Audit Chain</div>', unsafe_allow_html=True)
        chain_lines = "\n".join(
            f"#{e['entry_index']} {e['phase']:8s} {e['this_hash'][7:21]}…"
            for e in entries[-5:]
        )
        st.markdown(f'<div class="hash-box">{chain_lines}</div>', unsafe_allow_html=True)

    # Capture info
    if capture_entry:
        cp = capture_entry["payload"]
        st.markdown('<div class="section-title" style="margin-top:1.2rem">Captured Endpoints</div>', unsafe_allow_html=True)
        for ep in cp.get("endpoints_covered", []):
            st.markdown(f"""
            <div class="ep-pass" style="font-size:0.72rem">
              <span style="color:#4a9eff">●</span>
              <span class="ep-name">{ep}</span>
            </div>""", unsafe_allow_html=True)

time.sleep(POLL_INTERVAL)
st.rerun()
