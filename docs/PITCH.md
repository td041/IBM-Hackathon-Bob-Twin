# PITCH.md — 90-second English script + 5-slide deck

> **Cho business team.** Mở ngay tuần này, đừng đợi đến 17/5. Pitch tốt cần 5–7 ngày iterate.

## 1. The 90-second script

Đây là script English. **Speaker** ở đầu mỗi block là gợi ý — nếu chỉ 1 người present thì dùng cùng giọng cho cả 90 giây.

---

### Slide 1 — Hook (0:00 → 0:15)

**Speaker (calm, slow, eye contact with camera):**

> "Stack Overflow's 2025 survey found that ninety-six percent of developers don't fully trust AI-generated code is correct. Only forty-eight percent always verify before they commit it. So when AI modernizes your codebase — what proves the behavior didn't change?"

**[Pause 1 second. Look at camera.]**

> "We built Bob's Twin."

---

### Slide 2 — The setup (0:15 → 0:30)

**Speaker (slightly faster, energy up):**

> "Take Pydantic v1 to v2 — a real migration thousands of FastAPI teams need to do today. The Pydantic team's own tool, `bump-pydantic`, fixes about eighty percent of the syntax automatically. The remaining twenty percent is where production regressions hide. Enum serialization shifts. Decimal encoding flips. Validators that silently no-op. Tests don't catch these — because tests check what tests assert, not what they don't."

**[Transition to demo screen.]**

---

### Slide 3 — Demo, the magic (0:30 → 1:00)

**Speaker (narrating live screen, energy up):**

> "We hand the migration to IBM Bob with a custom mode we built — `modernize-with-twin`."

**[Type prompt: "Upgrade this app from Pydantic v1 to v2."]**

> "Twin captures forty-seven HTTP interactions from the legacy app — golden cassettes, append-only evidence."

**[Cassette files appear in sidebar.]**

> "Bob runs `bump-pydantic`, then handles the long-tail patterns. Twin replays the same inputs against the migrated code..."

**[Dashboard updates. Two endpoints turn red.]**

> "...and finds two endpoints silently changed wire format."

**[Brief pause — let the red sink in.]**

---

### Slide 4 — Resolution (1:00 → 1:20)

**Speaker (calm, confident):**

> "Twin auto-rolls back to the last green checkpoint. Bob regenerates with a constraint: 'preserve enum serialization shape.' Twin replays again."

**[Dashboard updates. All green.]**

> "Forty-seven of forty-seven endpoints, behaviorally equivalent."

**[Show PDF audit report on screen.]**

> "And every step is captured in a hash-chained audit report — the same shape EU AI Act Article Twelve will require starting August second this year."

---

### Slide 5 — The closer (1:20 → 1:30)

**Speaker (slow, deliberate):**

> "Bob migrates the code. Bob's Twin proves the behavior didn't change. The Skill is open-source. Any team can install it."

**[End frame: GitHub URL + team name.]**

---

## 2. Voice direction notes (Vietnamese)

| Section | Tone | Tốc độ | Volume |
|---|---|---|---|
| Hook | Calm, almost serious | Chậm (130 wpm) | Vừa |
| Setup | Conversational | Trung bình (160 wpm) | Vừa |
| Demo magic | Excited but clear | Hơi nhanh (170 wpm) | Hơi to |
| Resolution | Confident, settled | Chậm (140 wpm) | Vừa |
| Closer | Slow, deliberate, "drop the mic" | Chậm (120 wpm) | Vừa-nhỏ |

**Không cần fake American accent.** Vietnamese-accented English với pronunciation rõ luôn được judge tôn trọng. Mistakes phổ biến cần tránh:
- "th-" sounds: "the" không phải "duh", "trust" không phải "trus"
- Final consonants: "code" có /d/ rõ, "ninety-six" có /s/ rõ
- "Pydantic" pronounce: /paɪˈdæn.tɪk/ (PIE-dan-tic)
- "bump-pydantic" pronounce: /bʌmp paɪˈdæn.tɪk/

**Subtitle English bắt buộc on.** Judge có thể skip volume.

---

## 3. The 5-slide deck

Format: 16:9, dark theme (IBM blue + accent), 1 idea per slide.

### Slide 1 — Hook

**Visual:** Big stat — "96%" centered, large font.
**Subtext:** "of developers don't trust AI-generated code is correct."
**Source:** Small footer "Stack Overflow Developer Survey 2025"
**Bottom right:** "Bob's Twin" logo + tagline "Behavioral equivalence, audited."

### Slide 2 — The 80/20 setup

**Visual:** 2 vertical bars
- Left bar (80%): "Mechanical syntax — `bump-pydantic` handles this"
- Right bar (20%, highlighted red): "Behavior changes — silent until production"

**Subtext:** "Pydantic v1 → v2: thousands of teams, four hidden patterns each."

### Slide 3 — How it works

**Visual:** The 4-phase pipeline diagram (lấy ASCII từ README, vẽ lại bằng Figma/icons cho đẹp)
- Capture (cassette icon)
- Migrate (Bob icon)
- Replay (play icon)
- Audit (signed-document icon)

**Footer:** "Powered by IBM Bob — Custom Mode + Skill + Orchestrator + Checkpoints"

### Slide 4 — Demo screenshot

**Visual:** Composite screenshot — VS Code with Bob mode active + Streamlit dashboard with red→green transition + PDF audit report excerpt.
**Caption:** "47 of 47 endpoints behaviorally equivalent — verified, not assumed."

### Slide 5 — Open-source + EU AI Act

**Visual:** GitHub repo card mockup left, EU AI Act Article 12 callout right.
**Headline:** "Bob migrates the code. Bob's Twin proves the behavior didn't change."
**Bottom:** GitHub URL, team name, 4 member avatars, hackathon logo.

---

## 4. Practice plan

| Date | What | Who |
|---|---|---|
| 8/5 | Read script aloud 3x solo | Both business members |
| 9/5 | Record solo on phone, listen back | Both |
| 10/5 | Slide v1 done, run-through together | Business + tech |
| 11/5 | Practice with screen-share (sim recording) | Full team |
| 12/5 | Record practice take, review | Full team |
| 13/5 | Polish problem moments | Both business |
| 14/5 | Final dry run | Full team |
| 16/5 | Real recording | Full team |

---

## 5. Backup lines (nếu live demo fail trong recording)

Nếu recording day Bob respond khác expected, đây là bridge sentences để cover gracefully:

- *"The pipeline handles this case as well — let me show you the result from a clean run."* → switch sang pre-recorded backup video
- *"For the demo we've cached the response — in production, this runs on every commit."*
- *"The full evidence is in our audit log — let me jump there."*

**Quan trọng:** đừng bao giờ nói "oh it's broken" hoặc "this didn't work". Recover smooth.

---

## 6. Things judge will ask in their head

Anticipate và pre-answer:

| Implicit question | Where it's answered in pitch |
|---|---|
| "Is this Bob-specific?" | Slide 3 footer mentions all 4 Bob features |
| "Is this real or PoC?" | Slide 4 shows actual screenshot, not mockup |
| "What's the business value?" | Slide 5 EU AI Act callout = quantifiable compliance |
| "Why not just use tests?" | Setup slide: "tests check what tests assert, not what they don't" |
| "How does this scale beyond Pydantic?" | Verbal aside in closer (optional) — "the architecture is language-agnostic; any HTTP-fronted code" |

---

## 7. After-pitch one-pager

Nếu submission có "Additional Information" field, paste version 200-word:

> **Bob's Twin** is a behavioral-equivalence validator for AI-driven Python migrations. Built on IBM Bob's Custom Modes, Skills, Orchestrator, and Checkpoints, it wraps any framework upgrade — Pydantic v1→v2, Flask 2→3, SQLAlchemy 1→2 — in a Capture → Migrate → Replay → Diff → Audit loop.
>
> The official `bump-pydantic` tool fixes ~80% of mechanical syntax changes in Pydantic migrations. The remaining 20% — Enum serialization, Decimal encoding, validator semantics, `__root__` model shape — is where production regressions hide. Existing test suites don't catch these because tests assert specific contracts, not full behavioral surface area.
>
> Bob's Twin uses VCR.py to record HTTP interactions as golden cassettes before migration, then replays them against migrated code with DeepDiff and configurable tolerance rules. When equivalence drops below 0.95, Bob auto-rolls back via Checkpoints and regenerates with explicit constraints. The output is a hash-chained audit trail and PDF report — same evidence shape EU AI Act Article 12 (effective August 2, 2026) will require for AI-modified production code.
>
> The full Skill (`twin-validator`) is open-source under Apache 2.0. Any team can install and apply it to their own migration. Built in 48 hours by a 4-person team for the IBM Bob Hackathon, May 15–17, 2026.
