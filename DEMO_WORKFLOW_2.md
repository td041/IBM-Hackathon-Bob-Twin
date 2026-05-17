# Demo Workflow 2 — Bob Orchestration (Recommended)

> **Mục đích:** Show Bob's Twin's **real value** — Bob AI tự reason, fix, replay, self-correct theo Custom Mode `modernize-with-twin`. Audience thấy Bob là **engineer**, không phải runner.
>
> **Thời lượng:** ~6-10 phút (depending on Bob's speed)
>
> **Cần Bob IDE** + MCP `twin-mcp` Connected

---

## Khi nào dùng

- Live demo trước audience/judge/IBM evaluator
- Show autonomous reasoning của Bob
- Highlight Custom Mode + 6 MCP tools + dashboard live update
- Demo "AI autonomy with hard constraints" narrative

---

## Pre-flight checklist

- [ ] Workflow 1 đã chạy thành công 1 lần (để verify môi trường)
- [ ] Bob IDE installed (https://bob.ibm.com/trial)
- [ ] Bob MCP panel: `twin-mcp` shows **Connected** (6 tools)
- [ ] `.bob/mcp.json` có đủ 6 tools trong `alwaysAllow`:
  - `reset_apps`, `capture_baseline`, `capture_status`
  - `replay_and_diff`, `compute_drift_metrics`, `generate_audit_report`
- [ ] Bob Auto-approve **master switch ON** (toggle ở Auto-approve panel)
- [ ] Auto-approve request limit ≥ 100
- [ ] Bob Settings → tất cả toggle ON: Read, Write, Execute, MCP, Mode, Subtasks, Question, Skills
- [ ] Custom Mode picker → **🔮 Modernize with Twin** selected
- [ ] Git status clean
- [ ] Dashboard mở fullscreen ở second monitor (nếu có)

---

## Setup steps

### Bước 1: Start services

```powershell
cd d:\coding\IBM-Hackathon-Bob-Twin
.venv\Scripts\python demo_run.py
```

Đợi đến khi thấy 3 services up:
- v1 app: http://localhost:8001
- v2 naive: http://localhost:8002
- Dashboard: http://localhost:8501

### Bước 2: Reset về broken state

```powershell
make reset-demo
```

Quan trọng — đảm bảo:
- v2 naive ở broken state (4 traps unfixed)
- `audit_trail/` và `golden_cassettes/` rỗng → dashboard hiện "Waiting for migration run"

### Bước 3: Verify Bob ready

1. Mở Bob IDE với repo `d:\coding\IBM-Hackathon-Bob-Twin`
2. MCP panel → `twin-mcp` = **Connected**
3. Mode picker → **🔮 Modernize with Twin**
4. Auto-approve panel → **master switch ON** (toggle xanh)

---

## THE PROMPT (paste 1 lần duy nhất)

```
Migrate this codebase from Pydantic v1 to v2.

- v1: http://localhost:8001
- v2: http://localhost:8002
- Scenario: scripts/seed_demo_traffic.py

Follow the modernize-with-twin Custom Mode.
```

**That's it.** 4 dòng. Bob tự làm mọi thứ.

---

## What Bob does autonomously

Custom Mode `modernize-with-twin` enforce flow này, Bob phải tuân thủ:

### Phase 1 — Capture & Baseline (~2 phút)

| Step | Bob action | Dashboard |
|------|-----------|-----------|
| 1.1 | `git status` clean check | — |
| 1.2 | Bob Checkpoint `pre-migration baseline` | — |
| 1.3 | `capture_baseline` (async, returns immediately) | — |
| 1.4 | `capture_status` poll until complete (~30-90s) | "37 INTERACTIONS CAPTURED" |
| 1.5 | Commit cassette | — |
| 1.6 | `replay_and_diff` vs v1 → **MUST = 1.0** | **Cột v1 → 1.0 (xanh)** |
| 1.7 | `replay_and_diff` vs v2 → baseline broken score | **Cột v2 → 0.595 (đỏ)** |

### Phase 2 — Migrate (ONE fix per commit) (~3-5 phút)

Strict per-fix loop — Bob lặp cho từng trap:

| Step | Bob action | Dashboard |
|------|-----------|-----------|
| 2a | Apply fix CHỈ cho TRAP N | — |
| 2b | `git commit -m "Fix TRAP N — ..."` | — |
| 2c | Bob Checkpoint cùng tên | — |
| 2d | `replay_and_diff` vs v2 | Cột v2 climb |
| 2e | So sánh score với lần trước | — |

**Per-trap progression:**
- TRAP 1 (Enum): `model_config = ConfigDict(use_enum_values=True)` → score ~**0.676**
- TRAP 2 (Decimal): `@field_serializer` cho Decimal fields → score ~**0.757**
- TRAP 3 (`__root__`): `RootModel[List[str]]` + `list(body.root)` → score ~**0.892**
- TRAP 4 (validator): per-item `@field_validator` → score ~**1.0**

**Self-correction:** Nếu score không climb sau fix → Bob auto-rollback Checkpoint + regenerate với constraint, max 3 attempts.

### Phase 3 + 4 — Tolerance Rules (nếu cần) (~1 phút)

Nếu sau fix hết 4 trap score vẫn 0.95-1.0 (do intentional v2 changes):
- Bob hỏi human: "Diff này intentional hay regression?"
- Nếu intentional → Bob append rule vào `tolerance-rules.yaml` với `rationale` field
- Re-replay để verify

### Phase 5 — Audit & Report (~30s)

| Step | Bob action | Dashboard |
|------|-----------|-----------|
| 5.1 | `compute_drift_metrics` | Timeline: DRIFT ✓ |
| 5.2 | `generate_audit_report` (PDF) | Timeline: REPORT ✓ |
| 5.3 | Final commit theo format Custom Mode | — |

---

## Talking points cho live demo

### [0:00] Paste prompt
> *"Tôi chỉ nói mục tiêu — 4 dòng. Custom Mode `modernize-with-twin` định nghĩa quy trình. Bob đọc nó và biết phải làm gì."*

### [0:30] Bob bắt đầu capture
> *"Thấy không? Bob KHÔNG sửa code ngay. Bob check git clean, tạo Checkpoint, rồi capture baseline trước. Đây là enforce-by-design."*

### [1:30] Capture xong, replay v1 = 1.0
> *"Bob tự replay vs v1 để verify cassette không corrupt. 1.0 nghĩa là ground truth được record chính xác."*

### [2:00] Replay v2 = 0.595
> *"Bob tự phát hiện 4 endpoints fail. Không phải tôi chỉ. Đây là behavioral diff mà `bump-pydantic` không catch được."*

### [3:00] Bob fix TRAP 1, score lên 0.676
> *"Score tăng. Bob tự commit Checkpoint, tự replay verify. Nếu score giảm sau fix tiếp, Bob sẽ tự rollback Checkpoint."*

### [4:30] Bob fix TRAP 3 (có thể stuck nếu chỉ fix models.py)
> *"Score không climb như expected. Watch this — Bob sẽ tự rollback và regenerate với constraint mới."*

[Sau khi Bob fix routes.py luôn]
> *"Đó là self-correction loop. Không phải tôi nhắc."*

### [6:00] Score = 1.0
> *"Bob verify hash chain trước khi gen PDF. Nếu chain broken → Bob refuse."*

### [6:30] PDF generated
> *"Evidence package. Signed. Hash-chained. EU AI Act Article 12 ready. Ai cũng verify được độc lập."*

---

## Backup prompts (nếu Bob bị stuck)

### Bob skip Phase 1 (capture)
```
You must complete Phase 1 (Capture) before any code change. Read .bob/custom_modes.yaml mode "modernize-with-twin" for the required pipeline order.
```

### Bob bulk-rewrite cả file (vi phạm "one fix per commit")
```
Apply migration in small commit-sized steps, ONE trap per commit. After each fix, create a Checkpoint and re-run replay_and_diff before moving to the next trap. The mode requires per-fix replay for rollback granularity.
```

### Bob skip replay vs v1 (Phase 1.6)
```
Custom Mode Phase 1 step 6 requires replay_and_diff vs the legacy app (http://localhost:8001) before Phase 2. This populates the v1 column on the dashboard.
```

### Bob ignore equivalence threshold
```
Equivalence score is currently <X>. Custom Mode hard rule requires ≥ 0.95 before marking complete. Either fix the remaining diffs or document them as tolerance rules with rationale.
```

### Bob quên audit report
```
Migration is not complete without a signed audit report. Call generate_audit_report (format=pdf) and verify the hash chain.
```

---

## Bob auto features sẽ show được

1. **Enforce-by-design pipeline** — Custom Mode bắt buộc Phase 1 trước Phase 2
2. **Async tool handling** — Bob tự biết `capture_baseline` returns immediately, phải poll `capture_status`
3. **Decision making** — Bob tự phân tích `diffs_per_endpoint`, tự quyết định fix trap nào trước
4. **Self-correction loop** — auto-rollback Checkpoint khi score không climb
5. **Tolerance rule generation** — Bob hỏi human khi gặp intentional diff
6. **Hard rule enforcement** — Bob refuse mark-complete nếu score < 0.95
7. **Hash chain verification** — Bob verify chain trước khi gen PDF

---

## Reset sau demo

```powershell
# Reset v2 về broken + xóa cassettes/audit
make reset-demo

# Bob's Checkpoints cũng bị reset khi git checkout
```

---

## So sánh với Workflow 1

| Aspect | Workflow 1 (One-shot) | Workflow 2 (Bob) |
|--------|----------------------|------------------|
| Lines paste | 0 (chạy script) | 4 |
| Bob autonomy | N/A | Tự quyết định |
| Audience perception | "Script chạy ok" | "Bob là engineer" |
| Show self-correction | ❌ | ✅ Rollback live |
| Show tolerance rule gen | ❌ | ✅ Bob hỏi user |
| Show Custom Mode value | ❌ | ✅ Tâm điểm |
| Show 6 MCP tools | Hidden | ✅ Visible trong Bob panel |
| Time | ~3-5 phút | ~6-10 phút |
