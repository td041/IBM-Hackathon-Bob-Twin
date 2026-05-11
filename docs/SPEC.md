# SPEC.md — Technical specification

> **Purpose:** Khóa cứng API contracts, data schemas, file formats để 2 dev implement không lệch nhau. Đây là source-of-truth khi APPROACH.md và SKILL.md mâu thuẫn.

## 1. Module boundaries

```
twin_mcp/
├── server.py         FastMCP entry, registers 4 tools, routes to modules
├── capture.py        VCR.py wrapper, cassette I/O
├── replay.py         Replays cassette against running app
├── diff_engine.py    DeepDiff + tolerance rule application
├── audit.py          Hash-chained JSONL writer/reader
├── reports.py        Markdown + PDF rendering
└── cli.py            Standalone invocation (fallback for demo)
```

**Rule:** mỗi module có 1 public API surface. Không cross-import private functions. `server.py` chỉ orchestrate; logic ở các module riêng.

---

## 2. MCP tools — contracts

### 2.1 `capture_baseline`

**Signature:**
```python
@mcp.tool
def capture_baseline(target_dir: str, scenarios: list[str]) -> dict:
```

**Inputs:**
- `target_dir`: absolute path to project root (string)
- `scenarios`: list of paths — each path is either a pytest path (`tests/foo.py`) or a Python script (`scripts/seed_traffic.py`). Each scenario script must make HTTP calls to localhost.

**Returns (JSON):**
```json
{
  "ok": true,
  "run_id": "a3f8c2d1",
  "cassette_path": "golden_cassettes/run_a3f8c2d1.yaml",
  "n_interactions": 47,
  "endpoints_covered": ["/users", "/users/{id}", "/orders", ...],
  "captured_at": "2026-05-15T14:32:11Z",
  "errors": []
}
```

**Errors:** if scenarios produce 0 interactions, return `{"ok": false, "errors": ["no HTTP interactions captured"]}`. Do NOT raise.

**Side effects:**
- Writes `<cassette_path>` (YAML, append-only — error if file exists with different hash)
- Appends entry to `audit_trail/run_<run_id>.jsonl` with `phase: "capture"`
- Stamps cassette SHA-256 into audit entry

---

### 2.2 `replay_and_diff`

**Signature:**
```python
@mcp.tool
def replay_and_diff(
    cassette_path: str,
    target_dir: str,
    tolerance_rules: dict | None = None,
    target_url: str = "http://localhost:8001"
) -> dict:
```

**Inputs:**
- `cassette_path`: path to YAML cassette from `capture_baseline`
- `target_dir`: project root of the MIGRATED app (may equal capture's `target_dir`)
- `tolerance_rules`: parsed YAML rules dict, or None (load from `.bob/skills/twin-validator/tolerance-rules.yaml` if None)
- `target_url`: where the migrated app is running

**Returns:**
```json
{
  "ok": true,
  "run_id": "a3f8c2d1",
  "equivalence_score": 0.957,
  "passed": 45,
  "failed": 2,
  "total": 47,
  "diffs_per_endpoint": [
    {
      "endpoint": "GET /users/1",
      "status": "fail",
      "diff": {
        "values_changed": {
          "root['role']": {
            "old_value": "ADMIN",
            "new_value": {"name": "ADMIN", "value": "ADMIN"}
          }
        }
      },
      "matched_rules": []
    }
  ],
  "tolerance_rules_applied": 5,
  "replayed_at": "2026-05-15T14:35:22Z"
}
```

**`equivalence_score` formula:** `passed / total`. Float, 3 decimals.

**Side effects:**
- Appends to `audit_trail/run_<run_id>.jsonl` with `phase: "replay"`

---

### 2.3 `compute_drift_metrics`

**Signature:**
```python
@mcp.tool
def compute_drift_metrics(target_dir: str, baseline_ref: str = "HEAD~1") -> dict:
```

**Inputs:**
- `target_dir`: project root
- `baseline_ref`: git ref to compare against (default: previous commit)

**Returns:**
```json
{
  "ok": true,
  "cc_delta": 2.4,
  "mi_delta": -3.1,
  "dead_funcs_added": 1,
  "files_changed": 8,
  "lines_added": 142,
  "lines_removed": 98
}
```

**Notes:** Uses `radon cc --average` and `radon mi --average` on both refs, computes delta. `vulture` on current ref only (compared by count, not identity).

---

### 2.4 `generate_audit_report`

**Signature:**
```python
@mcp.tool
def generate_audit_report(run_id: str, format: str = "pdf") -> dict:
```

**Inputs:**
- `run_id`: from previous tool calls
- `format`: `"pdf"` | `"markdown"` | `"json"`

**Returns:**
```json
{
  "ok": true,
  "run_id": "a3f8c2d1",
  "format": "pdf",
  "path": "audit_trail/run_a3f8c2d1.report.pdf",
  "hash": "sha256:9f8a...",
  "verified": true
}
```

**Verification:** before generating, re-walk the audit JSONL and re-compute hash chain. If broken, return `{"ok": false, "verified": false, "broken_at": <entry_index>}`.

---

## 3. Data schemas

### 3.1 Cassette (YAML — VCR.py 8.x format)

VCR.py controls this schema; we don't modify it. The format VCR.py 8.1 produces:

```yaml
interactions:
  - request:
      body: null
      headers:
        accept: ['*/*']
        host: ['localhost:8001']
      method: GET
      uri: http://localhost:8001/users/1
    response:
      body:
        string: '{"id":1,"name":"Alice","role":"ADMIN"}'
      headers:
        content-type: [application/json]
      status:
        code: 200
        message: OK
version: 1
```

**Critical:** keep `record_mode='once'` to avoid silent overwrites.

### 3.2 Tolerance rule schema (YAML)

```yaml
rules:
  - path: "$.field_path"          # JSONPath syntax
    kind: "regex_ignore" | "any_uuid" | "any_iso_datetime" |
          "ignore_order" | "numeric_tolerance" | "enum_value_remap" |
          "field_optional" | "schema_relaxed"
    pattern: "<regex>"             # required for regex_ignore, regex_match
    epsilon: 0.001                 # required for numeric_tolerance
    map: {"OLD": "new"}            # required for enum_value_remap
    rationale: "Why this is acceptable"  # REQUIRED ALWAYS
```

Validation: empty `rationale` → reject. No default tolerance — every rule must be explicit.

### 3.3 Audit trail JSONL schema

One JSON object per line. Each entry:

```json
{
  "run_id": "a3f8c2d1",
  "entry_index": 0,
  "phase": "capture" | "migrate" | "replay" | "drift" | "report" | "override",
  "timestamp": "2026-05-15T14:32:11.234Z",
  "payload": { /* phase-specific */ },
  "prev_hash": "sha256:0000...",
  "this_hash": "sha256:abc123..."
}
```

**Hash computation:** `this_hash = sha256(prev_hash + canonical_json(payload) + timestamp + entry_index)`. Use `json.dumps(payload, sort_keys=True, separators=(',', ':'))` for canonicalization.

**First entry:** `prev_hash = "sha256:" + "0" * 64`.

### 3.4 PDF report sections (in order)

1. **Cover page:** run_id, project, dates, equivalence score (large)
2. **Executive summary:** 3-sentence outcome
3. **Capture phase:** cassette hash, n_interactions, endpoints list
4. **Migrate phase:** commit log (each commit message + hash)
5. **Replay phase:** per-endpoint pass/fail table
6. **Drift metrics:** CC/MI/dead-code deltas
7. **Tolerance rules applied:** each rule + rationale verbatim
8. **Hash chain:** entry sequence with hashes
9. **Footer:** Apache-2.0 notice, tool version, generation timestamp

---

## 4. File system contracts

**Cassettes are append-only.** Code must:
- Refuse to write if file exists and hash differs
- Refuse to delete via the MCP server (force user to do it explicitly outside Bob)

**Audit trail is append-only.** Code must:
- Open with `mode="a"` only
- Verify hash chain before each append (reject if broken)

**`golden_cassettes/` and `audit_trail/` are committed to git.** They are the evidence. .gitignore should exclude `*.tmp` and `__pycache__` only.

---

## 5. Demo target — `demo_target/pydantic_v1_app/`

A FastAPI 0.95 + Pydantic 1.10 application with **exactly 10 endpoints**:
- 6 "control" endpoints (`bump-pydantic` handles cleanly, equivalence after migration)
- 4 "trap" endpoints (the patterns `bump-pydantic` leaves behind)

### The 4 trap endpoints

| Endpoint | Pattern | Visible diff after naive migration |
|---|---|---|
| `GET /users/{id}` | Enum field `role` | Serializes as object instead of string |
| `POST /orders/calculate` | `Decimal` field `total` | Serializes as string instead of float |
| `POST /products/tags` | `__root__: list[str]` model | Import error / model shape changes |
| `POST /reviews/bulk` | `@validator(..., each_item=True)` | Validator silently no-ops; invalid data passes through |

### The 6 control endpoints (just need to exist)

- `GET /health`
- `GET /users` (list, simple model)
- `GET /users/{id}/orders`
- `POST /users` (create with simple validation)
- `PUT /users/{id}` (update)
- `DELETE /users/{id}`

### `scripts/seed_demo_traffic.py`

Hits every endpoint at least 3× with varied inputs. Total ~30–50 HTTP interactions. Imports `httpx` (synchronous mode), calls localhost:8001, no fancy logic — just deterministic traffic.

---

## 6. Pinned dependencies (`pyproject.toml`)

```toml
[project]
name = "bobs-twin"
version = "0.1.0"
requires-python = ">=3.11,<3.13"

dependencies = [
    "fastmcp>=2.0,<3.0",
    "vcrpy==8.1.0",
    "deepdiff==8.0.1",
    "pydantic==2.6.4",          # for twin_mcp ITSELF
    "radon==6.0.1",
    "vulture==2.11",
    "streamlit==1.30.0",
    "fastapi==0.110.0",          # for demo_target migrated app
    "httpx==0.27.0",
    "pyyaml==6.0.1",
    "reportlab==4.0.9",
    "jsonpath-ng==1.6.1",        # for tolerance rule path matching
    "uvicorn[standard]==0.27.1",
]

[project.optional-dependencies]
dev = [
    "pytest==8.0.0",
    "pytest-cov==4.1.0",
    "ruff==0.2.0",
]

# Demo target installed separately to avoid Pydantic v1/v2 conflict
[tool.uv]
package = false
```

**Critical conflict:** main `twin_mcp` uses Pydantic v2; demo_target uses Pydantic v1. Two options:

1. **Separate venvs:** `.venv-twin/` for twin_mcp, `.venv-demo-v1/` for demo_target pre-migration. Document in README.
2. **Docker isolation:** `demo_target/Dockerfile` runs the v1 app in a container on port 8001. twin_mcp talks to it over HTTP. Cleaner but adds Docker dep.

**Recommendation:** option 1 (venvs). Docker can choke during demo. Document the 2-venv setup in README Quick Start.

---

## 7. Test plan (`tests/`)

### `test_capture.py`
- Capture a known endpoint, verify cassette structure
- Capture with 0 interactions → returns `{"ok": false}`
- Capture twice with same scenario → second call rejects (append-only)

### `test_diff_engine.py`
- Identical responses → score 1.0
- One field changed → score < 1.0, diff present
- Tolerance rule matches → field excluded from diff
- Numeric tolerance: 0.5 vs 0.5001 with ε=0.001 → pass
- Enum remap: ADMIN ↔ admin with map → pass

### `test_audit_chain.py`
- Empty audit file + first entry → first hash valid
- Append 3 entries → chain intact
- Tamper with middle entry → chain validation fails at correct index
- Read-back: regenerate hashes, verify match

**Total tests target: 20–25.** Goal is regression safety during 48h, not 100% coverage.

---

## 8. Interface contracts between modules

### `capture.py` → `replay.py`
- Cassette path is the only handoff
- Cassette format is VCR-controlled; replay just opens and iterates

### `replay.py` → `diff_engine.py`
- Pass tuple `(expected_response_dict, actual_response_dict, endpoint_label)`
- `diff_engine` is pure function: deterministic, no I/O

### `diff_engine.py` → `audit.py`
- Pass full diff result dict, `audit.append(run_id, phase, payload)`
- `audit.py` handles hash chain logic; caller doesn't touch hashes

### All modules → `server.py`
- Each module exposes 1 public function
- `server.py` only handles MCP tool registration + JSON shape conversion
- Module functions raise exceptions; server.py catches and returns `{"ok": false, "errors": [...]}`

---

## 9. CLI fallback (`twin_mcp/cli.py`)

For Risk Mode A in RISKS.md. Same 4 functions, invokable from terminal:

```bash
python -m twin_mcp.cli capture --target . --scenarios scripts/seed_demo_traffic.py
python -m twin_mcp.cli replay --cassette golden_cassettes/run_a3f8.yaml --target . --rules .bob/skills/twin-validator/tolerance-rules.yaml
python -m twin_mcp.cli drift --target .
python -m twin_mcp.cli report --run-id a3f8c2d1 --format pdf
```

Each command output is identical to MCP tool JSON return, printed to stdout. Enables demo to continue even if Bob fails to call tools.

---

## 10. Open implementation questions (resolve on Day 2)

1. **Concurrent HTTP capture:** does VCR.py handle parallel test runs? → run scenarios sequentially in v1.
2. **PDF generation library:** `reportlab` (high-effort) vs `pandoc` shelling out (low-effort, requires pandoc binary). → start with `pandoc` for v1; switch to `reportlab` if pandoc unavailable in hackathon env.
3. **Streamlit auto-refresh:** poll JSONL file vs websocket. → poll every 2 seconds via `st.experimental_rerun()` with sleep. Simpler.
4. **Bob auto-approve list:** all 4 tools in `mcp.json` alwaysAllow? → yes (already configured). Risk: Bob runs without confirmation. Acceptable for hackathon; rule for prod.
