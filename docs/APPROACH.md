# APPROACH.md — Bob's Twin

> **Tài liệu nội bộ cho team.** Mở khi cần align lại "tại sao chúng ta build cái này" hoặc khi onboard thành viên mới. Đọc cùng với `RISKS.md` và `TIMELINE.md`.

## TL;DR

Build **Bob's Twin** — một validator chứng minh code AI-modernized không thay đổi behavior so với code gốc. Demo cụ thể: Pydantic v1→v2 migration. Stack: VCR.py + DeepDiff + FastMCP + Streamlit, đóng gói thành Bob Skill + Custom Mode + Orchestrator pipeline.

**Pitch hook:** *"bump-pydantic fixes the 80%. Bob's Twin proves the 20%."*

**Target placement:** Top 3 (giải tiền $2K trở lên).

---

## 1. Tại sao chọn idea này (chứ không phải Bob's Mirror)

Đã có 4 vòng research trong đó 2 vòng độc lập (Phase 3 & 4) hoàn toàn không có context chéo, cả hai đều converge về Bob's Twin. Phase 4 final stress-test cho điểm 48/60 vs 34/60 cho Bob's Mirror. Lý do chính:

### 1.1 Winner archetype của lablab IBM hackathons
Mọi top project ở past lablab IBM hackathons (DORA Gatekeeper, NexusGuardAI, ORQON, Veritas, PayFlow, Sarra) đều có chung 5 đặc điểm:
- Compliance/audit/governance angle cho regulated industry
- Autonomous agentic workflow (không phải single-shot tool)
- Quantified ROI bằng số giờ hoặc đô-la
- Sử dụng exact vocabulary của IBM marketing
- Demo có emotional arc rõ (problem → autonomous fix → measurable outcome)

Bob's Twin trúng cả 5. Bob's Mirror chỉ trúng 2/5 (autonomous + measurable).

### 1.2 Narrative alignment với IBM hiện tại
IBM Think 2026 (4-7/5/2026, vừa kết thúc 2 ngày trước hackathon kickoff) công bố Bob là *"agentic SDLC partner that integrates orchestration, execution, and governance"* — đây là exact wording cho pitch của Bob's Twin. Timing đẹp đến mức gần như IBM viết kịch bản hộ.

EU AI Act Article 12 effective **2/8/2026** — chỉ 3 tháng sau hackathon. Hash-chained audit report của Bob's Twin có shape giống evidence package mà Article 12 yêu cầu. Đây là regulatory tailwind không tốn công thuyết phục judge.

### 1.3 Originality verification
Đã verify không có project nào public hiện tại làm chính xác cái này:
- IBM/mcp-context-forge: REST→MCP gateway, không validate behavior
- IBM/bob-demo (state ngày 7/5/2026): không có migration validation demo
- bump-pydantic: chỉ fix 80% syntax, **explicitly không validate behavior** — đây là setup line cho pitch
- LegacyLeap: behavioral parity nhưng proprietary, không phải Bob, single-framework
- BlastRadius (team đã đăng ký lablab): static/predictive analysis (PR risk graph), khác layer với dynamic/empirical record-replay
- Pytest VCR plugins (snowflake-vcrpy, pytest-recording): testing helpers, không phải migration validators

**Differentiator của ta vs BlastRadius:** BlastRadius dự đoán *what might break*; Twin chứng minh *what actually changed*. Có thể coexist trong production. Trong demo phải nói rõ điểm này nếu judge hỏi.

---

## 2. Architecture

### 2.1 Pipeline 4 phase

```
   Capture → Migrate → Replay → Diff/Audit
   (VCR.py)  (Bob)    (replay) (DeepDiff + Hash chain)
```

Mỗi phase commit Checkpoint vào shadow Git của Bob. Nếu Phase 3 fail (equivalence < 0.95), Bob auto-rollback về Checkpoint của Phase 2 và regenerate code path bị lỗi với constraint thêm vào prompt.

### 2.2 Bob integration

| Bob feature | Vai trò |
|---|---|
| Custom Mode `modernize-with-twin` | Persona gate cho 4 phases, restrict file edit qua regex |
| Orchestrator mode | Chain 4 phases thành single managed sequence |
| Skills (`SKILL.md`) | Pydantic watch list, tolerance rule format, failure mode playbook — redistributable |
| Checkpoints | Auto-rollback khi equivalence fail |
| MCP server creation | `twin-mcp` server với 4 tools, registered qua `.bob/mcp.json` |
| BobShell | Optional CLI driver cho CI/CD integration post-hackathon |

### 2.3 Tech stack — pinned versions

```
python = "3.11.x or 3.12.x"     # tránh 3.13 (pydantic.v1 không support)
fastmcp = "2.0.x"
vcrpy = "8.1.0"                 # latest stable, Jan 2026
deepdiff = "8.0.x"
pydantic = "2.6.x"              # cho twin_mcp itself
radon = "6.0.x"
vulture = "2.11.x"
streamlit = "1.30.x"
fastapi = "0.110.x"             # cho demo_target migrated app
pyyaml = "6.0.x"
reportlab = "4.0.x"             # PDF report generation
```

**Quan trọng:** lock versions trong `pyproject.toml` ngay từ ngày đầu. Một lần `pip install` không pin = 2 giờ debug versions trong hackathon.

### 2.4 Repo layout
Đã document trong README.md. Key directories:
- `.bob/` — configuration Bob load tự động khi mở repo
- `twin_mcp/` — MCP server core
- `dashboard/` — Streamlit live dashboard (1 file)
- `demo_target/pydantic_v1_app/` — codebase Bob sẽ migrate
- `golden_cassettes/` — append-only YAML
- `audit_trail/` — hash-chained JSONL

---

## 3. Demo target — Pydantic v1 → v2 watch list

Đây là **moat** của team. Một team khác đọc report này vẫn không reach được watch list này trong 48h vì cần trial-and-error against bump-pydantic.

### 3.1 Patterns mà bump-pydantic AUTO-FIX (không cần show trong demo)
- `Config` class → `model_config = ConfigDict(...)`
- `.dict()` → `.model_dump()`, `.json()` → `.model_dump_json()`
- `.parse_obj()` → `.model_validate()`
- `__fields__` → `model_fields`
- `orm_mode` → `from_attributes`
- `allow_population_by_field_name` → `populate_by_name`
- `@validator` → `@field_validator` (basic cases)
- `@root_validator` → `@model_validator` (basic cases)

### 3.2 Patterns mà bump-pydantic KHÔNG fix — đây là demo material
Mỗi pattern trong list này là một "moment" trong demo có thể trigger 1 red diff trên dashboard:

1. **Enum serialization shape**
   v1 default: serialize Enum as `.value` string. v2 default: serialize Enum object dict. Wire format thay đổi → API consumers downstream break silently. Fix: thêm `use_enum_values=True` vào `model_config`.

2. **`each_item=True` validators**
   v1 cho phép validator chạy per-item trong list field. v2 không có equivalent direct. Fix: dùng nested `field_validator` hoặc tách thành sub-model. **bump-pydantic không tự làm việc này** — code compiles nhưng validator no-op silently.

3. **`Decimal` JSON encoding**
   v1 default: serialize Decimal as float. v2 default: serialize as string (cho JSON safety). Downstream parsers expect float → break. Fix: `model_config = ConfigDict(json_encoders={Decimal: float})`.

4. **`__root__` model**
   v1: `class Tags(BaseModel): __root__: list[str]`. v2: `Tags = RootModel[list[str]]`. **bump-pydantic skip pattern này hoàn toàn.** Code import error.

5. **(Bonus) Optional[X] không có default**
   v1: tự cho phép `None` khi field là `Optional[X]`. v2: yêu cầu explicit default `= None`. Validation error mà tests cũ không assert.

6. **(Bonus) ValidationError message format**
   Text format error message thay đổi. Nếu API contract document exact strings → break. Tolerance rule case (intentional change).

### 3.3 Demo flow 90 giây

| Time | Visual | Voice-over |
|---|---|---|
| 0:00–0:10 | Title slide với hook | "96% of developers don't trust AI-generated code is correct..." |
| 0:10–0:20 | Stat: bump-pydantic 80% / 20% gap | "...and the official Pydantic team's own migration tool fixes 80% — leaving the 20% where regressions hide." |
| 0:20–0:30 | VS Code mở, Bob mode `modernize-with-twin`, prompt `Upgrade to Pydantic v2` | "We hand the migration to IBM Bob with a custom mode we built. Watch what happens." |
| 0:30–0:55 | Capture phase records 47 interactions, then bump-pydantic auto-fix, then Bob handles long-tail. Dashboard: 2 endpoints turn red — Enum + Decimal | "Bob runs bump-pydantic, then handles the rest. Twin replays — and finds two endpoints silently changed wire format." |
| 0:55–1:15 | Auto-rollback animation, Bob regenerates with constraint, dashboard: all green | "Twin auto-rolls back to the last green checkpoint. Bob regenerates with the constraint 'preserve enum serialization shape'. All 47 endpoints green." |
| 1:15–1:30 | PDF audit report on screen, hash chain visible | "Signed audit report — same shape EU AI Act Article 12 will require in August. The Skill is open-source — any team can install it." |

90 giây nhưng có 4 emotional beats: setup, surprise, resolution, closer.

---

## 4. Cost discipline (Bobcoin awareness)

Free trial = 40 Bobcoins ≈ 80–200 actions. Phải coin-thrifty:

- **Plan mode trước khi Code mode.** Plan mode FREE. Outline migration steps in Plan mode, switch sang Code mode chỉ khi execute.
- **Capture phase chạy local Python**, không gọi Bob (Bob không cần biết VCR.py recorded gì).
- **Diff phase chạy local DeepDiff**, không gọi Bob (deterministic computation).
- **Bob chỉ được gọi cho:** Phase 2 migration prompts (~5–8 prompts per migration), Phase 4 self-correction (max 3 iterations).
- **Cap `replay_and_diff` tại 4 calls per migration.** Sau đó là design issue, không phải code issue.

Estimated total: 25–35 Bobcoins per full demo run. Có buffer cho 1 demo recording + 1 rehearsal.

---

## 5. Deliverables checklist (cho lablab.ai submission)

Required:
- [ ] GitHub repo public, MIT-compliant license
- [ ] Working prototype (locally runnable, instructions trong README)
- [ ] Video presentation max 5 phút, max 300MB, English audio
- [ ] Pitch deck (PDF, 5–10 slides)
- [ ] Submission form trên lablab.ai dashboard

Quality bar:
- [ ] Demo video ghép đẹp, có subtitle English (a11y + judge có thể không nghe rõ Vietnamese-accented English)
- [ ] README có Quick Start chạy được trong < 5 phút từ clone
- [ ] Audit report PDF mẫu commit sẵn vào repo (ai cũng xem được)
- [ ] Cassette mẫu commit sẵn (proof of concept)
- [ ] Pre-recorded demo video làm backup nếu live demo fail

Stretch:
- [ ] Deploy Streamlit dashboard lên `share.streamlit.io` (free) → có URL "live demo" để fill vào lablab form
- [ ] Bob Skill packaged as installable ZIP với `install.sh`
- [ ] CI workflow chạy full pipeline để prove reproducibility

---

## 6. Pivot triggers (gắn với RISKS.md)

Nếu một trong 2 trigger này fire trước hoặc trong hackathon, team chuyển sang backup idea (Bob's OnCall — incident triage agent, đã được vetted ở Phase 3 ranking #2):

- **Trigger 1:** IBM/bob-demo merge một PR/branch demo "behavioral validation" hoặc "migration verification" trước 14/5
- **Trigger 2:** Kickoff stream 15/5 IBM announce một feature Bob built-in cho behavioral validation

Cả 2 triggers đều có monitoring plan trong `RISKS.md`.

---

## 7. Tài liệu liên quan

- `README.md` — public-facing, English, cho judges
- `TIMELINE.md` — daily plan May 7–14 + 48h hour-by-hour
- `PITCH.md` — 90-second English script + 5-slide deck outline
- `DEMO_SCRIPT.md` — exact Bob prompts + fallback paths
- `RISKS.md` — pivot triggers + demo failure modes + mitigations
- `.bob/skills/twin-validator/SKILL.md` — chi tiết technical phase-by-phase
- `.bob/custom_modes.yaml` — Custom Mode definition
