# TIMELINE.md — Bob's Twin

> **Cách dùng:** mỗi sáng mở file này, đánh dấu ✅ vào item của ngày. Cuối ngày update STATUS section dưới cùng.

## Hai giai đoạn

1. **Pre-hackathon** — 7/5 → 14/5 (8 ngày, prep + de-risk)
2. **Hackathon** — 15/5 → 17/5 (48 giờ, build + record + submit)
3. **Post-submission** — 18/5 → 24/5 (judging period)

---

## Pre-hackathon: 7/5 → 14/5

### Day 1 — 7/5 (Thứ 4) — TODAY

**Tech team (cả 2 dev):**
- [ ] Đăng ký IBM Bob trial tại `bob.ibm.com/trial`. Confirm 40 Bobcoins, no credit card.
- [ ] Cài Bob extension vào VS Code, login, verify Advanced mode + Custom Modes hiển thị.
- [ ] `pip install bump-pydantic fastapi pydantic==1.10.21` trong fresh venv.
- [ ] Clone `tiangolo/full-stack-fastapi-template`. Run `bump-pydantic .` rồi quan sát: cái nào auto-fix, cái nào skip. Ghi vào `docs/observations.md`.
- [ ] Watch GitHub repo `IBM/bob-demo` → All Activity (early-warning Trigger 1).

**Business team (cả 2):**
- [ ] Đọc `APPROACH.md` từ đầu đến cuối.
- [ ] Đăng ký account lablab.ai + Discord.
- [ ] Note: pitch sẽ bằng English. Bắt đầu warm-up English speaking. Giọng tốt > grammar perfect.

**Cuối ngày:** team sync 30 phút (Discord voice). Confirm trial accounts work cho cả tech team.

---

### Day 2 — 8/5 (Thứ 5)

**Tech Dev A (MCP server):**
- [ ] Tạo project skeleton với `pyproject.toml` + pinned versions từ APPROACH.md §2.3.
- [ ] FastMCP server boilerplate, 4 tools với pass-through implementation.
- [ ] `capture_baseline` tool: integrate VCR.py, output cassette path + interaction count.
- [ ] Test: capture 5 endpoints từ một FastAPI hello-world. Verify cassette YAML readable.

**Tech Dev B (demo target):**
- [ ] Tạo `demo_target/pydantic_v1_app/`: FastAPI 0.95 + Pydantic 1.10 base structure.
- [ ] Implement 5 endpoints với 5 patterns ở APPROACH.md §3.2 (Enum, each_item, Decimal, __root__, Optional).
- [ ] Pytest harness có test pass cho cả 5 endpoints.
- [ ] Seed data fixtures.

**Business team:**
- [ ] Draft pitch hook (10s opener) bằng English, 3 versions, vote chọn.
- [ ] Outline 5-slide deck — chỉ cần bullet points, chưa cần design.

---

### Day 3 — 9/5 (Thứ 6)

**Tech Dev A:**
- [ ] `replay_and_diff` tool: integrate DeepDiff với 5 tolerance kinds (regex_ignore, any_uuid, any_iso_datetime, ignore_order, numeric_tolerance).
- [ ] Output schema: `{equivalence_score, passed, failed, diffs_per_endpoint}`.
- [ ] Test với cassette từ Day 2: cố tình thay đổi 1 endpoint trong demo target → verify diff bắt được.

**Tech Dev B:**
- [ ] Build Streamlit dashboard skeleton: 2 panels (timeline + per-endpoint pass/fail), poll JSONL file mỗi 2s.
- [ ] Hard-code 1 sample run JSONL → verify dashboard render đẹp.

**Business team:**
- [ ] Slide 1 (Problem) draft: bao gồm 96% Stack Overflow stat + bump-pydantic 80% framing.
- [ ] Slide 2 (Solution) draft: 4-phase pipeline diagram (lấy từ README ASCII).

**End of day check:** End-to-end thread (capture → diff) chạy được trên 1 endpoint. **Nếu chưa được, dừng polish, focus thread.**

---

### Day 4 — 10/5 (Thứ 7)

**Tech Dev A:**
- [ ] `compute_drift_metrics` tool: radon CC + MI delta, vulture dead code count.
- [ ] `generate_audit_report` tool: hash-chained JSONL + markdown export. PDF dùng `pandoc` từ markdown (không tự build template).

**Tech Dev B:**
- [ ] Verify `.bob/custom_modes.yaml` + `SKILL.md` (đã có sẵn trong repo) load đúng vào Bob. Test prompt `What's in your twin-validator skill?` để confirm Bob đã đọc skill.
- [ ] Test full flow manual với Bob: prompt "upgrade to pydantic v2" trong Advanced mode + modernize-with-twin. Đo Bobcoin consumption.

**Business team:**
- [ ] Slide 3 (Architecture) — sử dụng diagram từ README.
- [ ] Slide 4 (Demo screenshot) — placeholder, sẽ replace sau Day 11.
- [ ] Slide 5 (Skill packaging + EU AI Act callout).

---

### Day 5 — 11/5 (Chủ nhật)

**Critical day — full integration test.**

**Cả tech team:**
- [ ] Run full pipeline end-to-end với demo target. Lúc này tất cả pieces phải liên kết.
- [ ] Time the full run. Mục tiêu: < 90 giây từ capture → audit report.
- [ ] Verify: dashboard update real-time, 2 endpoints fail, auto-rollback trigger, regenerate, all green.

**Nếu pipeline chưa work end-to-end:**
- [ ] Switch sang Minimum Viable Demo plan (RISKS.md §3): 1 MCP tool `validate_migration()` thay vì 4. Vẫn top-3 capable.

**Business team:**
- [ ] Pitch script v1 đầy đủ 90 giây. Time it. Cut nếu > 90s.
- [ ] Practice presenting solo, record bằng phone, listen back, identify mumble points.

---

### Day 6 — 12/5 (Thứ 2)

**Tech team:**
- [ ] **Pre-record backup demo video.** Quay lại cả flow trong điều kiện perfect (không network issue, Bob behaving). Đây là parachute nếu Day 16 demo fail.
- [ ] Generate 1 sample audit report PDF, commit vào repo. Judge mở repo có thể view ngay.

**Business team:**
- [ ] Pitch rehearsal với cả team (Discord voice). 2 takes. Phản hồi: clarity, energy, tốc độ, eye contact (nếu on camera).
- [ ] Polish slide design (Canva hoặc Google Slides). Consistent font, IBM color palette (blue + dark mode).

---

### Day 7 — 13/5 (Thứ 3)

**Buffer day — bug fixes + polish.**

- [ ] List bugs còn pending. Fix theo priority.
- [ ] Test demo flow thêm 2 lần. Đảm bảo timing < 90s consistent.
- [ ] README quick-start: confirm clone-to-running < 5 phút trên một laptop fresh.
- [ ] Pitch deck final review.

**Trigger 1 check:** Verify IBM/bob-demo `main` chưa có migration validation demo mới.

---

### Day 8 — 14/5 (Thứ 4)

**Day before kickoff — prep mode.**

- [ ] Đọc lại RISKS.md. Confirm cả 2 pivot path (full Twin → MVP, Twin → OnCall) đều khả thi.
- [ ] Charge laptop, verify webcam + mic working.
- [ ] Quiet room cho recording. Test ánh sáng.
- [ ] Final commit demo target với 4 patterns đã được kiểm tra.
- [ ] Đăng ký team trên lablab.ai dashboard, confirm tất cả members thấy event.
- [ ] Đi ngủ sớm. Hackathon kickoff ngày mai.

---

## Hackathon: 15/5 → 17/5 (48 giờ)

**Lưu ý timezone:** lablab.ai default 6:00 PM CET (Berlin) = 11:00 PM giờ Việt Nam. Confirm exact start time tại kickoff stream announcement.

### Hour 0–4 (15/5, evening Vietnam time): Kickoff + decision lock

- [ ] Watch kickoff stream Twitch `twitch.tv/lablabai`.
- [ ] **Trigger 2 check:** IBM có announce feature Bob built-in nào overlap không?
- [ ] Nếu Trigger 2 fire → emergency meeting 30 phút, quyết định pivot sang Bob's OnCall.
- [ ] Nếu không fire → confirm Bob's Twin, lock idea.
- [ ] Pull main branch, freeze pre-built code, tag `v0.1-prework`.

### Hour 4–12: Capture + Migrate phases solid

**Tech Dev A:**
- [ ] Polish `capture_baseline` cho production: handle edge cases (timeout, partial cassette, write conflicts).
- [ ] Verify VCR.py records FastAPI endpoints chính xác (httpx, requests, urllib3 đều intercept được).

**Tech Dev B:**
- [ ] Test full Bob `modernize-with-twin` flow lần thứ 5. Tune Custom Mode prompts nếu Bob hay đi sai phase.
- [ ] Test với cả 2 model routing options (Granite vs Claude vs Mistral) trong Bob — xem cái nào ít hallucination hơn.

**Sleep window 1:** 0:00 → 6:00 sáng, ưu tiên ngủ. Tired devs ship bugs.

### Hour 12–24: Replay + Diff + Audit phases

- [ ] DeepDiff tolerance rules engine: thử 10 case khác nhau, tune false-positive rate.
- [ ] Hash chain: verify integrity check (sửa 1 line trong audit JSONL → chain validation fail).
- [ ] PDF report: render đẹp, có logo, có run_id, có timestamp.
- [ ] Streamlit dashboard: handle live updates không lag, không flicker.

### Hour 24–36: Demo polish + first record

**Tech team:**
- [ ] Demo target final: 4 endpoints với 4 patterns, 6 endpoints "control" (correctly migrated). Total 10 endpoints.
- [ ] Run demo flow 5 lần liên tiếp để tìm flaky behavior.

**Business team (coordinate với tech):**
- [ ] First demo recording attempt. OBS Studio, 1080p, 30fps đủ.
- [ ] Voice over English bằng good mic. Subtitle bật on để judge non-native vẫn hiểu.
- [ ] Edit thô (cut dead air, add intro/outro slide). Target: 4 phút clip ≤ 5 phút.

### Hour 36–46: Final record + submission package

- [ ] Demo recording final. Multiple takes nếu cần.
- [ ] Slide deck PDF export.
- [ ] README final pass: ai click link cũng phải hiểu trong 30s.
- [ ] Audit report PDF mẫu commit vào repo.
- [ ] Sample cassette commit vào repo.
- [ ] LICENSE file (Apache 2.0).
- [ ] CHANGELOG ngắn cho v0.1.0.
- [ ] Tag release `v1.0-hackathon`.

### Hour 46–48: Submission + buffer

- [ ] Submit form lablab.ai dashboard:
  - GitHub URL
  - Video URL (upload YouTube unlisted hoặc Loom hoặc lablab native)
  - Pitch deck URL (Google Drive public link)
  - Demo Application URL: `localhost` placeholder hoặc Streamlit Cloud URL nếu kịp deploy
  - Description: 200 từ tóm tắt
- [ ] **2-hour buffer trước deadline.** Submit early, đừng đợi phút 47:59.
- [ ] Screenshot submission confirmation. Lưu lại.
- [ ] Celebrate. Eat. Sleep.

---

## Post-submission: 18/5 → 24/5 (judging week)

- [ ] Voting period (nếu có public vote thành phần): share repo trên Twitter/LinkedIn với hashtag #IBMBobHackathon.
- [ ] Đính kèm pitch video trên LinkedIn personal profile của team lead — đây là asset career-long.
- [ ] Watch winners stream announcement.
- [ ] Bất kể kết quả, viết blog post "Lessons from building Bob's Twin in 48h" — content marketing cho profile của team.

---

## STATUS log

> Update mỗi cuối ngày. Format: `[YYYY-MM-DD] Tóm tắt 1 câu + blocker nếu có.`

```
[2026-05-07] Setup ngày — chưa start
```
