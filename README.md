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
explicitly identified _reward hacking_, where agents claim a migration is done
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

_The Streamlit dashboard shows real-time equivalence tracking as Bob commits each migration step. Red endpoints indicate behavioral divergence — in this case, Enum serialization and Decimal encoding changed wire format between v1 and v2, caught before deployment._

### 2. Bob in Action — Custom Mode Active

![Bob VS Code Panel](docs/screenshots/bob-modernize-mode.png)

_Bob's VS Code panel with the `modernize-with-twin` Custom Mode active. The mode orchestrates the 4-phase pipeline (Capture → Migrate → Replay → Audit) and enforces behavioral equivalence checks via Checkpoints — if equivalence drops below 0.95, Bob auto-rolls back and regenerates with constraints._

### 3. Audit Report — Signed Evidence Package

![PDF Audit Report](docs/screenshots/audit-report-cover.png)

_The hash-chained PDF audit report with prominent equivalence score display. Each phase (capture, migrate, replay, drift) is linked via SHA-256 hashes to prevent tampering. The report format matches EU AI Act Article 12 evidence requirements (effective August 2, 2026) for AI-modified production code._

---

## The 4 MCP tools

The `twin-mcp` server exposes 4 tools, callable from any MCP client (Bob,
Claude Desktop, Cursor):

| Tool                    | Inputs                                           | Returns                                                   |
| ----------------------- | ------------------------------------------------ | --------------------------------------------------------- |
| `capture_baseline`      | `target_dir`, `scenarios`                        | `{cassette_path, n_interactions, run_id}`                 |
| `replay_and_diff`       | `cassette_path`, `target_dir`, `tolerance_rules` | `{equivalence_score, passed, failed, diffs_per_endpoint}` |
| `compute_drift_metrics` | `target_dir`                                     | `{cc_delta, mi_delta, dead_funcs_added}`                  |
| `generate_audit_report` | `run_id`, `format`                               | path to signed PDF + JSONL chain                          |

Calling order is enforced — the audit report's hash chain links each phase's
output to the next. Skipping or reordering breaks integrity verification.

---

## Quick start

### Prerequisites

- Python 3.11 or 3.12
- Git
- IBM Bob (free trial: <https://bob.ibm.com/trial>)

### Install & run (Windows)

```bash
git clone https://github.com/td041/IBM-Hackathon-Bob-Twin
cd IBM-Hackathon-Bob-Twin

# 1. Create virtual environments and install dependencies
setup.bat

# 2. Run the full demo in one command
python demo_run.py
```

`demo_run.py` automatically:
1. Starts v1 app (port 8001), v2 naive app (port 8002), and dashboard (port 8501)
2. Seeds traffic into the v1 app (skips if already seeded)
3. Captures a golden cassette via VCR.py
4. Replays against v1 → expect score **1.0**
5. Replays against v2 naive → expect score **~0.595** (4 traps detected)
6. Generates a PDF audit report
7. Opens the dashboard automatically in your browser

**Dashboard features:**

- Real-time equivalence score with color-coded status
- Per-endpoint pass/fail indicators with diff detail
- Phase timeline (capture → migrate → replay → audit)
- Hash chain integrity visualization
- Toggle to compare v1 vs v2 app responses

---

## CLI usage (without Bob)

For environments where Bob is unavailable, use the CLI directly:

```bash
# Capture baseline from legacy app
python -m twin_mcp.cli capture \
  --target . \
  --scenarios scripts/seed_demo_traffic.py

# Replay against migrated app
python -m twin_mcp.cli replay \
  --cassette golden_cassettes/run_<run_id>.yaml \
  --target . \
  --url http://localhost:8001

# Compute code quality drift
python -m twin_mcp.cli drift \
  --target . \
  --ref HEAD~1

# Generate audit report
python -m twin_mcp.cli report \
  --run-id <run_id> \
  --format pdf
```

---

## Tolerance rules

When behavioral differences are **intentional** (e.g., Pydantic v2's improved
enum serialization), add tolerance rules to
`.bob/skills/twin-validator/tolerance-rules.yaml`:

```yaml
rules:
  - kind: any_uuid
    path: $.id
    reason: UUIDs differ per run

  - kind: any_iso_datetime
    path: $.created_at
    reason: Timestamps differ per run

  - kind: numeric_tolerance
    path: $.price
    epsilon: 0.01
    reason: Floating-point rounding acceptable

  - kind: enum_value_remap
    path: $.status
    map:
      PENDING: pending
      ACTIVE: active
    reason: Enum case normalization in v2

  - kind: ignore_order
    path: $.items
    reason: List order not semantically significant

  - kind: regex_ignore
    path: $.trace_id
    pattern: "^[0-9a-f]{32}$"
    reason: Trace IDs are ephemeral

  - kind: field_optional
    path: $.metadata
    reason: Field added in v2, absent in v1
```

Each rule requires a `reason` field for audit traceability. The audit report
will list all applied rules.

---

## Audit chain verification

The audit trail is hash-chained to prevent tampering. Verify integrity:

```python
from twin_mcp.audit import verify_chain

is_valid, broken_at = verify_chain("<run_id>")
if is_valid:
    print("✓ Audit chain intact")
else:
    print(f"✗ Chain broken at entry {broken_at}")
```

Each entry links to the previous via SHA-256 hash. Modifying any entry breaks
the chain, making tampering detectable.

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

## The 4 trap patterns (demo scenarios)

Bob's Twin catches behavioral changes that `bump-pydantic` and standard test
suites miss. The demo includes 4 real-world traps:

### TRAP 1: Enum serialization

```python
# Pydantic v1: enums serialize as strings
{"role": "ADMIN"}

# Pydantic v2 (naive): enums serialize as objects
{"role": {"name": "ADMIN", "value": "ADMIN"}}
```

**Impact:** API consumers expecting strings will break. Bob's Twin detects
this via DeepDiff and flags the endpoint as failed.

### TRAP 2: Decimal serialization

```python
# Pydantic v1: Decimal serializes as float
{"total": 19.98}

# Pydantic v2 (naive): Decimal serializes as string
{"total": "19.98"}
```

**Impact:** Downstream parsers expecting `float` will break. Caught by
equivalence replay.

### TRAP 3: `__root__` model removal

```python
# Pydantic v1: __root__ models accept raw lists
class Tags(BaseModel):
    __root__: List[str]

# Pydantic v2: __root__ removed, requires RootModel
class Tags(RootModel[List[str]]):
    root: List[str]
```

**Impact:** Endpoint completely broken if not migrated. Bob's Twin detects
422 errors during replay.

### TRAP 4: `@validator` → `@field_validator` behavior change

```python
# Pydantic v1: each_item=True validates list items
@validator("reviews", each_item=True)
def check_rating(cls, v):
    assert 1 <= v.rating <= 5
    return v

# Pydantic v2 (naive): field_validator without mode="after" is no-op
@field_validator("reviews")
def check_rating(cls, v):
    # Never called! Validation silently disappears.
    return v
```

**Impact:** Data validation silently disabled. Bob's Twin catches this by
replaying invalid inputs that should fail but don't.

---

## Troubleshooting

### Port already in use

```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8001 | xargs kill -9
```

### Module not found

```bash
# Verify venv activated
which python  # should show .venv/bin/python

# Reinstall
pip install -e .
```

### Dashboard not updating

```bash
# Restart with file watcher
streamlit run dashboard/app.py --server.fileWatcherType poll
```

### PDF generation fails

The report generator tries 3 fallbacks in order:

1. **weasyprint** (best quality, handles tables/monospace)
2. **reportlab** (basic, plain paragraphs only)
3. **pandoc** (requires external install)

If all fail, the markdown source is saved with `.pdf` extension. Install
weasyprint for best results:

```bash
pip install weasyprint
```

---

## Status

Built for the
[IBM Bob Hackathon](https://lablab.ai/ai-hackathons/ibm-bob-hackathon)
(May 15–17, 2026). This is a proof-of-concept; production hardening is on the
post-hackathon roadmap.

See [DEMO_GUIDE.md](DEMO_GUIDE.md) for detailed step-by-step demo instructions.

## License

Apache 2.0. See [LICENSE](LICENSE).

## Team

See [docs/APPROACH.md](docs/APPROACH.md) for our approach,
[docs/TIMELINE.md](docs/TIMELINE.md) for our build plan.
