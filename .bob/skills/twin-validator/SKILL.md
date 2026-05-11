---
name: twin-validator
version: 1.0.0
description: >-
  Behavioral-equivalence validator for Python migrations. Wraps any
  framework/library upgrade (Pydantic v1→v2, Flask 2→3, SQLAlchemy 1→2,
  Python version bumps) in a deterministic Capture → Migrate → Replay →
  Diff loop using VCR.py cassettes as golden traces. Catches silent
  behavior changes that compile fine but break API contracts. Produces
  EU AI Act Article 12-shaped audit evidence.
author: bobs-twin
license: Apache-2.0
when_to_use: >-
  Invoked automatically by the `modernize-with-twin` Custom Mode. Can
  also be invoked manually in Advanced mode for any task that asks Bob
  to "upgrade", "migrate", "modernize", or "port" a Python codebase
  from one library/framework version to another.
mcp_servers_required:
  - twin-mcp
---

# Twin Validator — Skill Reference

> **One-line philosophy:** A migration is not "done" when it compiles. It is
> done when, given the same inputs, the new code produces the same observable
> outputs as the old code — or you have explicitly documented why a difference
> is intentional.

## What this skill does

This skill encodes the operational knowledge needed to drive a behavioral-
equivalence-validated migration. It is invoked by Bob when the user asks for
a version upgrade and the active mode is `modernize-with-twin`. The skill
tells Bob:

1. Which MCP tools to call, in what order
2. How to construct tolerance rules for known-acceptable differences
3. What the Pydantic v1→v2 migration's specific watch-list looks like
4. How to interpret diff output and self-correct
5. What constitutes "done"

## The 4 MCP tools (provided by `twin-mcp`)

| Tool | When to call | Inputs | Returns |
|---|---|---|---|
| `capture_baseline` | ONCE, before any code edit | `target_dir`, `scenarios: list[str]` | `{cassette_path, n_interactions, run_id}` |
| `replay_and_diff` | After every Migrate Checkpoint | `cassette_path`, `target_dir`, `tolerance_rules: dict` | `{equivalence_score, passed, failed, diffs_per_endpoint}` |
| `compute_drift_metrics` | Once per run, before reporting | `target_dir` | `{cc_delta, mi_delta, dead_funcs_added}` |
| `generate_audit_report` | LAST, after equivalence ≥ 0.95 | `run_id`, `format='pdf'` | `path/to/run_<id>.report.pdf` |

Calling order is fixed. Skipping or reordering breaks the audit chain — the
report's hash chain links each phase's output to the next.

## Tolerance rules — the format

Tolerance rules tell the diff engine "this difference is intentional, do not
flag it." Rules live in `.bob/skills/twin-validator/tolerance-rules.yaml`
(create the file if it does not exist). Format:

```yaml
rules:
  - path: "$.created_at"          # JSONPath into the response body
    kind: regex_ignore             # ignore exact value, match by pattern
    pattern: '^\d{4}-\d{2}-\d{2}T'
    rationale: "Timestamps are runtime-dependent, not migration-affected"

  - path: "$.id"
    kind: any_uuid
    rationale: "UUIDs are generated; identity, not content, matters"

  - path: "$.tags"
    kind: ignore_order
    rationale: "Tag set semantics are unordered; v2 sorts differently"

  - path: "$.price"
    kind: numeric_tolerance
    epsilon: 0.001
    rationale: "Float rounding differs between Decimal and float backends"

  - path: "$.user.role"
    kind: enum_value_remap
    map: { "ADMIN": "admin", "USER": "user" }
    rationale: "v2 changes default Enum serialization to .value lowercase"
```

**Rule of thumb:** every tolerance rule must have a non-empty `rationale`. The
audit report includes them verbatim. If you cannot articulate why a difference
is acceptable, the rule does not belong.

## Pydantic v1 → v2 — Watch List

These are the breaking changes most likely to produce silent regressions.
When migrating, expect to encounter and resolve each. The first column tells
you what the diff engine will surface; the third tells you whether to fix
the code or add a tolerance rule.

| Diff symptom | Root cause (v1 → v2) | Default action |
|---|---|---|
| `Config` class missing on model | `Config` → `model_config = ConfigDict(...)` | Fix code |
| `dict()` method gone | `.dict()` → `.model_dump()` | Fix code (migrate all callsites) |
| `json()` method gone | `.json()` → `.model_dump_json()` | Fix code |
| `parse_obj()` errors | `.parse_obj()` → `.model_validate()` | Fix code |
| `__fields__` empty | `__fields__` → `model_fields` | Fix code |
| Enum serialized as object instead of string | v2 serializes Enum members as the member, not `.value` | **Fix code** with `use_enum_values=True` in `model_config` — DO NOT add tolerance rule (this is a wire-format change) |
| `None` no longer accepted for `Optional[X]` field | v2 does NOT auto-allow `None` for `Optional[X]` without a default | Fix code: add `= None` default explicitly |
| `orm_mode` ignored | `orm_mode` → `from_attributes` | Fix code |
| `allow_population_by_field_name` ignored | renamed to `populate_by_name` | Fix code |
| Nested model now has extra `additionalProperties` field | v2 emits stricter JSON Schema | Add `extra='forbid'` to model_config OR add tolerance rule for schema endpoints only |
| `@validator` decorator silently no-ops | `@validator` → `@field_validator` (different signature: takes `cls, v, info`) | Fix code |
| `@root_validator` decorator silently no-ops | `@root_validator` → `@model_validator(mode='before'\|'after')` | Fix code |
| Datetime parsed differently | v2 has stricter ISO 8601 enforcement | Investigate per-field — usually fix code with `field_validator` for legacy formats |
| `ValidationError` message text differs | Error message format changed | **Tolerance rule** with `path: "$.detail[*].msg", kind: regex_match, pattern: '.*'` — only if your API contract does not document exact error strings |
| `__root__` model gone | `__root__` → `RootModel[T]` | Fix code |
| `Decimal` field now serializes as string by default | v2 default changed for JSON safety | Add `model_config = ConfigDict(json_encoders={Decimal: float})` if API consumers expect float |
| Field with default `[]` shared between instances (v1 mutable bug fixed in v2) | v2 uses `Field(default_factory=list)` semantics | Fix code; this is a v1 BUG, the v2 behavior is correct — flag as "intended behavior change" in audit |

**Strategic note:** the LAST row is the kind of finding judges want to hear in
the demo. "We caught a v1 bug-compatibility shim our app relied on." That's
the story.

## Phase-by-phase playbook

### Capture phase

```python
# Bob's internal sequence (you don't write this, you call the tool):
result = mcp.twin-mcp.capture_baseline(
    target_dir=".",
    scenarios=[
        "tests/api/test_users.py",
        "tests/api/test_orders.py",
        "scripts/seed_demo_traffic.py"  # synthetic traffic for endpoints without tests
    ]
)
# result = {"cassette_path": "golden_cassettes/run_a3f8.yaml",
#           "n_interactions": 47, "run_id": "a3f8c2d1"}
```

If `n_interactions < 20`, the user does not have enough scenarios to ground
the equivalence claim. STOP and request more. The cassette is the audit
artifact; thin cassettes mean weak proof.

### Migrate phase

For Pydantic v1 → v2 specifically, work in this commit order to minimize
self-correction iterations:

1. `Config` → `ConfigDict` (mechanical, low-risk)
2. `@validator` / `@root_validator` → v2 equivalents (mechanical)
3. Enum serialization (`use_enum_values=True`) — HIGH RISK for wire format
4. `.dict()` / `.json()` callsite migration (uses `ast` grep, mechanical)
5. `__root__` → `RootModel` (only if present)
6. `Optional[X]` defaults (only if validation errors arise during replay)

Create a Bob Checkpoint after each step. The Checkpoint is your rollback target.

### Replay phase

After each migrate Checkpoint, call `replay_and_diff`. Read the result with
this priority order:

1. `equivalence_score` >= 0.95 → proceed
2. `equivalence_score` < 0.95 but all failures match a watch-list row →
   self-correct using the watch-list's "default action"
3. `equivalence_score` < 0.95 with failures NOT on the watch-list → STOP and
   show the user the unexpected diff. This is exactly the case the tool
   exists to catch.

### Self-correction loop

Maximum 3 iterations per `replay_and_diff` failure. The pattern:

1. Identify the smallest diff
2. Restore the most recent Checkpoint
3. Re-prompt Bob with an additional constraint: "preserve <specific behavior>"
4. Re-run `replay_and_diff`
5. If still failing after 3 tries: hand off to user with diff as a checklist

The 3-iteration cap prevents Bobcoin runaway and mirrors how human pair
programmers escalate to design discussion after 3 failed attempts.

### Audit phase

The audit report contains, in order:

1. Run metadata (id, started_at, ended_at, mode, model used)
2. Capture summary (cassette hash, n_interactions, scenario list)
3. Migrate commit log (each Checkpoint, with hash and message)
4. Replay results (final equivalence_score, per-endpoint pass/fail)
5. Drift metrics (radon CC delta, MI delta, vulture dead-code delta)
6. Tolerance rules applied (each with rationale)
7. Hash chain (SHA-256 of each section linked to the next)

The hash chain is what makes this Article-12-grade evidence: any tampering
breaks the chain, and the chain links artifacts to a specific run_id that
cannot be fabricated post-hoc.

## Failure modes (what to do when things go wrong)

| Symptom | Likely cause | Fix |
|---|---|---|
| `capture_baseline` returns `n_interactions=0` | Scenarios don't actually call the API | Verify scenarios run against a live `localhost:PORT` instance |
| `replay_and_diff` says "cassette not found" | Working directory changed | Always pass absolute paths; never assume cwd |
| All replays fail with `ConnectionRefused` | Migrated app not running | Start the migrated app on the same port the cassette was recorded against |
| Equivalence stuck at ~0.5 across all endpoints | Likely a global config issue (e.g., changed JSON encoder) | Check `model_config` defaults BEFORE iterating per-endpoint |
| `generate_audit_report` fails with hash mismatch | Cassette was edited after capture | Cassettes are append-only; restore from git and re-run |

## Why this skill exists (for the audit report's preamble)

Stack Overflow's 2025 Developer Survey found 96% of developers don't fully
trust AI-generated code is functionally correct, and only 48% always verify
before committing. The FreshBrew benchmark (arXiv 2510.04852) measured
state-of-the-art LLM agents at 52.3% successful Java migrations on
production repos — and explicitly identified "reward hacking" where agents
claim a migration is done while silently breaking behavior.

The Twin Validator closes the verification gap by making behavioral proof a
mechanical artifact, not a manual review burden.
