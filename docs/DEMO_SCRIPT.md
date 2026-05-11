# DEMO_SCRIPT.md — Recording day playbook

> **Mở file này trong recording day, không sớm hơn.** Mục đích: bất kể gì xảy ra, có path để recover gracefully và vẫn ship video tốt.

## 1. Pre-demo checklist (làm trước khi bấm record)

### Environment
- [ ] Python venv activated, all deps installed (verify với `pip list | grep -E "vcr|deepdiff|fastmcp|streamlit"`)
- [ ] `demo_target/pydantic_v1_app/` git status clean, đang trên branch `demo-baseline`
- [ ] `golden_cassettes/` empty (sẽ generate trong demo)
- [ ] `audit_trail/` empty
- [ ] Bob trial active, Bobcoin balance ≥ 30 (kiểm tra Bobalytics)
- [ ] Bob mode dropdown đã sẵn `🔮 Modernize with Twin` ở top

### Services running (3 terminal windows pre-opened)
```bash
# Terminal 1 — legacy app on :8001
cd demo_target/pydantic_v1_app && uvicorn main:app --port 8001 --reload

# Terminal 2 — Streamlit dashboard on :8501
cd dashboard && streamlit run app.py

# Terminal 3 — empty, for ad-hoc git/inspection commands
```

### Recording setup
- [ ] OBS Studio open, scene "Demo Recording" loaded
- [ ] Resolution 1920x1080, 30fps
- [ ] Mic levels tested, no echo, no fan noise
- [ ] Browser windows closed except needed (avoid notification bars)
- [ ] Discord/Slack/email **muted hoàn toàn**
- [ ] Phone airplane mode
- [ ] System sound off (avoid email ding mid-demo)
- [ ] VS Code zoom level 110% (judge xem trên laptop sẽ thấy code rõ)

### Practice run
- [ ] **Run full demo flow LIVE 1 lần ngay trước recording.** Không record. Verify mọi thứ work.
- [ ] Reset state: `git checkout demo-baseline`, clear cassettes/audit_trail, restart services.

---

## 2. The exact Bob prompts (sequence)

### Prompt 1 — Activate mode + initial directive

**Type into Bob chat:**
```
I need to migrate this FastAPI app from Pydantic v1 to v2.
Use the modernize-with-twin workflow. Start with Phase 1 (capture baseline).
The app is running on localhost:8001. Use scripts/seed_demo_traffic.py
for the scenario list.
```

**Expected Bob response (within ~10 seconds):**
- Bob acknowledges modernize-with-twin mode
- Calls `twin-mcp.capture_baseline` with `target_dir="."`, `scenarios=["scripts/seed_demo_traffic.py"]`
- Returns: `{cassette_path: "golden_cassettes/run_<id>.yaml", n_interactions: 47, run_id: "<id>"}`

**If Bob doesn't auto-call the tool:** Add follow-up prompt:
```
Call the twin-mcp.capture_baseline tool now.
```

**If `n_interactions` < 30:** Re-seed traffic, re-capture. (Add this as fallback in seed script.)

---

### Prompt 2 — Migrate phase

**Type into Bob chat:**
```
Phase 2: migrate. Run bump-pydantic first to handle the mechanical changes.
Then handle the patterns it leaves behind. Create a Bob Checkpoint after
each major step.
```

**Expected Bob behavior (~30-60 seconds):**
- Bob runs `bump-pydantic .` via command tool
- Bob reviews remaining patterns (will find Enum, Decimal, each_item, __root__)
- Bob makes commits, creates Checkpoints
- Bob says "ready for Phase 3 replay"

**Critical timing:** This is the longest phase. Trong recording, **cut hoặc speed up** post-prod. Không quay full 60 giây Bob đang typing.

---

### Prompt 3 — Replay + diff (the magic moment)

**Type into Bob chat:**
```
Phase 3: replay and diff. Use the cassette from Phase 1 and the strict
tolerance rules.
```

**Expected Bob behavior:**
- Bob calls `twin-mcp.replay_and_diff`
- Tool returns equivalence_score < 0.95 với 2 endpoints failing (Enum + Decimal)
- Bob displays the diffs clearly
- Streamlit dashboard updates: 2 red panels visible

**THIS IS THE EMOTIONAL PEAK OF THE DEMO.** Hold camera on dashboard for 2-3 seconds. Don't rush past the red.

---

### Prompt 4 — Self-correction loop

**Type into Bob chat:**
```
Phase 4: rollback to the last green checkpoint and regenerate the failing
endpoints. For the enum endpoint, add the constraint "preserve enum
serialization shape (use_enum_values=True)". For the Decimal endpoint,
add "preserve Decimal as float in JSON output".
```

**Expected Bob behavior:**
- Bob restores Checkpoint
- Bob regenerates only those 2 endpoints
- Re-runs replay_and_diff automatically
- equivalence_score = 1.0
- Dashboard: all green

---

### Prompt 5 — Generate audit report

**Type into Bob chat:**
```
Generate the final audit report in PDF format.
```

**Expected Bob behavior:**
- Bob calls `twin-mcp.generate_audit_report`
- PDF saved to `audit_trail/run_<id>.report.pdf`
- Bob commits final summary

**Open the PDF on screen for the closer shot.** This is the "evidence" moment that justifies the EU AI Act framing.

---

## 3. Three fallback paths

### Fallback A — Bob doesn't call tools automatically

**Symptom:** Bob explains what it would do but doesn't actually invoke MCP tools.

**Recovery:**
1. Switch from Code mode to **Advanced** mode (more autonomy with tools)
2. Re-prompt with explicit tool name: `Call twin-mcp.capture_baseline now with these parameters: ...`
3. If still fails: switch to **manual MCP CLI mode** — invoke tools directly from Terminal 3:
   ```bash
   python -m twin_mcp.cli capture --target . --scenarios scripts/seed_demo_traffic.py
   ```
   Narrate as: *"For demo speed, we're invoking the MCP server directly. In normal use, Bob orchestrates this end-to-end."*

### Fallback B — Live demo fails mid-recording

**Symptom:** Bob crashes, MCP server errors, dashboard freezes.

**Recovery:**
1. Stop recording, do NOT panic-narrate.
2. Use the pre-recorded backup video (made on Day 6 — 12/5).
3. Edit: stitch live opening (you on camera, slides 1-2) + backup video (slides 3-4) + live closing (you on camera, slide 5).
4. Mention nowhere that this happened. Edit invisibly.

### Fallback C — Time runs over 5 minutes

**Symptom:** Final cut > 5:00.

**Recovery in priority order:**
1. Cut Phase 2 (migrate) to a 5-second time-lapse + voice over: *"Bob runs bump-pydantic, then handles the long-tail in about a minute."*
2. Cut Slide 3 transition to a hard cut (no animation).
3. Speed up dashboard "all green" reveal from 3 seconds to 1 second.
4. Tighten Slide 1 hook from 15 seconds to 10 seconds — drop the "only 48% verify" sub-stat if needed.

---

## 4. Recording shot list

In order:

| # | Shot | Source | Duration |
|---|---|---|---|
| 1 | Title slide | Slide deck | 0:00 – 0:05 |
| 2 | Hook stat slide | Slide deck | 0:05 – 0:15 |
| 3 | 80/20 setup slide | Slide deck | 0:15 – 0:30 |
| 4 | VS Code + Bob — type Prompt 1 | Live screen capture | 0:30 – 0:40 |
| 5 | Cassettes generating | Live screen capture | 0:40 – 0:45 |
| 6 | Bob running bump-pydantic + handling rest (compressed time-lapse) | Edit | 0:45 – 0:55 |
| 7 | Dashboard turning red on 2 endpoints | Live screen capture | 0:55 – 1:00 |
| 8 | Hold on red — emphasis | Live screen capture | 1:00 – 1:05 |
| 9 | Bob auto-rollback + regenerate | Live screen capture | 1:05 – 1:15 |
| 10 | Dashboard all green | Live screen capture | 1:15 – 1:20 |
| 11 | PDF audit report scrolling | Live screen capture | 1:20 – 1:25 |
| 12 | Closer slide with GitHub URL | Slide deck | 1:25 – 1:30 |

Total: 1:30. Add 30s for slide-to-screen transitions = ~2 min final demo.

If using full 5 min budget: extend to 2x the times above + add a 1-min "what is Bob's Twin" intro before Slide 1.

---

## 5. Editing checklist (post-recording)

- [ ] Trim dead air at start/end
- [ ] Add subtitle (English) — auto-generate via YouTube/Whisper, then proof-read
- [ ] Add intro card (5s): "Bob's Twin — Behavioral equivalence for AI-driven Python migrations"
- [ ] Add outro card (5s): "Built for IBM Bob Hackathon 2026 | github.com/<team>/bobs-twin | Apache 2.0"
- [ ] Background music (optional, low volume): use royalty-free from YouTube Audio Library, ambient/electronic
- [ ] Final length ≤ 5:00, file size ≤ 300 MB (export H.264, 1080p, 5 Mbps bitrate)
- [ ] Test playback on different devices (phone, laptop) — readability check
- [ ] Upload as YouTube **Unlisted** + Loom backup link

---

## 6. Day-of recording emotional checklist

- [ ] Coffee/water within reach but off-camera
- [ ] Bathroom break BEFORE recording
- [ ] Dress: clean shirt, neutral background (or virtual blur)
- [ ] Remind self: judge is human, just trying to find good projects. Not adversarial.
- [ ] If a take goes wrong: smile, take a breath, restart. Don't apologize on camera.
- [ ] After successful take: 5-minute break before reviewing. Don't critique fresh.

Good luck. The work is already done — recording is just the showcase.
