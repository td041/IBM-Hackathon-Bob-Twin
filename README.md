# Bob's Twin

> **`bump-pydantic` fixes the 80%. Bob's Twin proves the 20%.**

A behavioral-equivalence validator for AI-driven Python migrations. Wraps any
framework or library upgrade — Pydantic v1→v2, Flask 2→3, SQLAlchemy 1→2 —
in a deterministic **Capture → Migrate → Replay → Diff → Audit** loop, so
silent behavior changes are caught before they ship.

Built on IBM Bob's MCP, Custom Modes, Skills, and Orchestrator features.

---

## The problem

[Stack Overflow's 2025 Developer Survey](https://survey.stackoverflow.co/2025/)
found that 96% of developers don't fully trust AI-generated code is correct,
and only 48% always verify before committing. The
[FreshBrew benchmark](https://arxiv.org/abs/2510.04852) measured frontier LLM
agents at **52.3% successful Java migrations** on production repos — and
explicitly identified *reward hacking*, where agents claim a migration is done
while silently breaking behavior.

For Pydantic v1→v2 specifically, the official
[`bump-pydantic`](https://github.com/pydantic/bump-pydantic) tool handles
~80% of mechanical syntax changes and explicitly leaves behavior validation
to the developer. The remaining 20% is where production regressions hide:
Enum serialization shifts, `Decimal` JSON encoding changes, error-message
format flips, `__root__` model shape changes — none of which `bump-pydantic`
catches and most of which existing test suites do not assert against.

**Bob's Twin closes that gap by making behavioral proof a mechanical
artifact, not a manual review burden.**

---

## How it works

```
   ┌──────────────────────────────────────────────────────────────┐
   │  Phase 1 — CAPTURE   (before any code change)                │
   │  VCR.py records HTTP request/response pairs from the legacy  │
   │  app into golden cassettes. Cassettes are append-only        │
   │  evidence, hashed and committed.                             │
   └────────────────────────┬─────────────────────────────────────┘
                            ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  Phase 2 — MIGRATE   (Bob does the work)                     │
   │  Bob's Custom Mode `modernize-with-twin` walks Bob through   │
   │  the migration in commit-sized steps with a Checkpoint after │
   │  each — `bump-pydantic` runs first, then Bob handles the     │
   │  long-tail patterns the tool can't.                          │
   └────────────────────────┬─────────────────────────────────────┘
                            ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  Phase 3 — REPLAY    (deterministic comparison)              │
   │  The migrated app receives the same recorded inputs.         │
   │  DeepDiff with semantic tolerance rules surfaces every       │
   │  diff: which endpoint, which field, what changed.            │
   └────────────────────────┬─────────────────────────────────────┘
                            ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  Phase 4 — AUDIT     (signed evidence package)               │
   │  Hash-chained JSONL audit trail + PDF report. Same shape     │
   │  regulators expect under EU AI Act Article 12 (effective     │
   │  Aug 2, 2026).                                               │
   └──────────────────────────────────────────────────────────────┘
```

---

## Screenshots

### 1. Live Dashboard — Behavioral Diffs Detected

![Streamlit Dashboard](docs/screenshots/dashboard-red-endpoints.png)

*The Streamlit dashboard shows real-time equivalence tracking as Bob commits each migration step. Red endpoints indicate behavioral divergence — in this case, Enum serialization and Decimal encoding changed wire format between v1 and v2, caught before deployment.*

### 2. Bob in Action — Custom Mode Active

![Bob VS Code Panel](docs/screenshots/bob-modernize-mode.png)

*Bob's VS Code panel with the `modernize-with-twin` Custom Mode active. The mode orchestrates the 4-phase pipeline (Capture → Migrate → Replay → Audit) and enforces behavioral equivalence checks via Checkpoints — if equivalence drops below 0.95, Bob auto-rolls back and regenerates with constraints.*

### 3. Audit Report — Signed Evidence Package

![PDF Audit Report](docs/screenshots/audit-report-cover.png)

*The hash-chained PDF audit report with prominent equivalence score display. Each phase (capture, migrate, replay, drift) is linked via SHA-256 hashes to prevent tampering. The report format matches EU AI Act Article 12 evidence requirements (effective August 2, 2026) for AI-modified production code.*

---

## The 4 MCP tools

The `twin-mcp` server exposes 4 tools, callable from any MCP client (Bob,
Claude Desktop, Cursor):

| Tool | Inputs | Returns |
|---|---|---|
| `capture_baseline` | `target_dir`, `scenarios` | `{cassette_path, n_interactions, run_id}` |
| `replay_and_diff` | `cassette_path`, `target_dir`, `tolerance_rules` | `{equivalence_score, passed, failed, diffs_per_endpoint}` |
| `compute_drift_metrics` | `target_dir` | `{cc_delta, mi_delta, dead_funcs_added}` |
| `generate_audit_report` | `run_id`, `format` | path to signed PDF + JSONL chain |

Calling order is enforced — the audit report's hash chain links each phase's
output to the next. Skipping or reordering breaks integrity verification.

---

## Quick start

### Prerequisites

- Python 3.11 or 3.12
- IBM Bob (free trial: <https://bob.ibm.com/trial>)
- Git

### Install

```bash
git clone https://github.com/<your-org>/bobs-twin
cd bobs-twin
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### Run the demo

```bash
# 1. Start the legacy app (Pydantic v1)
cd demo_target/pydantic_v1_app
uvicorn main:app --port 8001 &

# 2. From the bobs-twin root, with Bob open in VS Code:
#    Switch Bob mode to "🔮 Modernize with Twin" and prompt:
#    "Upgrade this app from Pydantic v1 to v2."

# 3. Watch the dashboard
streamlit run dashboard/app.py
```

The dashboard streams equivalence updates as Bob commits each migration step.

---

## Repo layout

```
bobs-twin/
├── .bob/                       Bob configuration (loaded automatically)
│   ├── custom_modes.yaml       The modernize-with-twin Custom Mode
│   ├── mcp.json                Registers the twin-mcp server
│   ├── skills/twin-validator/  Skill instructions + Pydantic watch list
│   └── rules-modernize-with-twin/   Audit-chain integrity rules
├── twin_mcp/                   The MCP server (FastMCP)
├── dashboard/                  Streamlit live dashboard
├── demo_target/                Pydantic v1 → v2 demo codebase
├── golden_cassettes/           VCR.py cassettes (append-only)
├── audit_trail/                Hash-chained JSONL evidence
└── docs/                       APPROACH, TIMELINE, PITCH, etc.
```

---

## Why this needs IBM Bob specifically

Bob's Twin uses **four** Bob-specific features as load-bearing components:

1. **Custom Modes** gate each migration phase with a deterministic prompt persona
2. **Orchestrator mode** chains capture → migrate → replay → diff as a managed sequence
3. **Skills (`SKILL.md`)** package the workflow + Pydantic watch list as a redistributable team asset
4. **Checkpoints** (Bob's shadow-Git layer) provide automatic rollback when equivalence drops below threshold

A reimplementation on Cursor or Claude Code would require manually scripting
all four layers. The Skill + Custom Mode together mean any team can install
`twin-validator` and get the workflow turnkey — that's the long-tail value.

---

## Status

Built for the
[IBM Bob Hackathon](https://lablab.ai/ai-hackathons/ibm-bob-hackathon)
(May 15–17, 2026). This is a proof-of-concept; production hardening is on the
post-hackathon roadmap.

## License

Apache 2.0. See [LICENSE](LICENSE).

## Team

See [docs/APPROACH.md](docs/APPROACH.md) for our approach,
[docs/TIMELINE.md](docs/TIMELINE.md) for our build plan.
