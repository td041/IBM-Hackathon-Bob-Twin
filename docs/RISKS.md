# RISKS.md — Bob's Twin

> **Mục đích:** không phải để đọc thường xuyên — mà để khi things go wrong, mở ra, thấy "đã có plan", và không panic-pivot.

## 1. Pivot triggers (existential — đổi idea)

### Trigger 1 — IBM officializes the same pattern

**Signal:** A new commit/PR/branch on `IBM/bob-demo` lands a demo with name matching:
- `legacy-to-mcp` (this was a removed/draft demo earlier — could come back)
- `migration-validator` / `behavior-validator` / `equivalence-checker`
- `twin-mode` / `golden-replay` / `migration-audit`
- Anything in `*.taikai` folder mentioning behavior testing during migration

**Probability:** 10%. IBM/bob-demo only had 40 commits as of 7/5; pace ~1 commit/day. They focus on Java + DevOps recently. But not zero.

**Monitoring:**
- GitHub watch on `IBM/bob-demo` → All Activity (Action 1 in TIMELINE.md Day 1)
- Daily glance at `https://github.com/IBM/bob-demo/commits/main` from Day 7 on (13/5)
- Twitter search for `from:ibmdev "bob" demo migration` weekly

**Action if fires:**
1. Emergency Discord call within 4 hours
2. Read the new IBM demo carefully — what exactly do they ship?
3. **If 70%+ overlap:** pivot to **Bob's OnCall** (idea #2 from Phase 3 ranking — incident triage agent with self-documenting BobShell trails)
4. **If <70% overlap:** stay on Twin, sharpen differentiation in pitch

**Pre-condition for pivot to OnCall:**
- 11 days of pre-work salvage: keep MCP server architecture (FastMCP boilerplate reusable), reuse Streamlit dashboard (just different data feed), reuse Skill format
- Lose: Pydantic watch list (becomes irrelevant), VCR.py integration (becomes optional)
- New demo target needs ~2 days build: a simulated alert source + service logs
- **Pivot cost:** ~6 person-days of pre-work wasted, 4 person-days of new work needed. Doable if Trigger 1 fires before 12/5. Not doable if fires after.

### Trigger 2 — Kickoff stream announces overlapping Bob feature

**Signal:** During lablab kickoff stream (15/5), IBM announces:
- A built-in Bob "behavior validator" or "migration verifier" feature
- A "golden cassette" or record-replay feature embedded in Bob
- Anything that makes Twin's value-prop look redundant

**Probability:** 5%. IBM Think 2026 just ended (4-7/5) and didn't announce this; surprise launch in 8 days unlikely.

**Monitoring:** Watch kickoff stream live on `twitch.tv/lablabai` 15/5.

**Action if fires:**
1. 30-minute team huddle within 1 hour after stream
2. **If feature is live and works:** pivot to OnCall (Bob's Twin loses originality completely)
3. **If feature is announced but in roadmap:** stay on Twin — frame our project as "the OSS implementation of what IBM will ship" (this is actually GOOD, judges may favor it)

---

## 2. Demo failure modes (during recording / live)

### Mode A — DeepDiff tolerance edge cases produce false reds

**Probability:** 35% during first attempts; 10% after Day 5 testing.

**Symptom:** Replay shows a "diff" that's just normal serialization variation (timestamp format, float precision), not a real behavior change.

**Pre-mitigation:**
- Test 10 known-equivalent scenarios on Day 3, tune tolerance rules until 100% pass rate
- Hardcode 5 standard tolerance rules (timestamps, UUIDs, float ε=0.001, list ordering, schema additionalProperties) into `tolerance-rules.yaml` template
- Have a 6th "regex-match-anything" fallback rule for problem fields

**During recording:**
- Use a frozen, pre-tuned `tolerance-rules.yaml` committed to repo
- If Bob suggests adding a new rule mid-demo, accept it (this is actually a great moment to narrate: "we add the rule, document why")

### Mode B — Bob doesn't auto-trigger Orchestrator phases

**Probability:** 25%. Bob's Custom Mode behavior may differ from the SKILL.md plan, especially with limited Bobcoin budget.

**Symptom:** Bob explains the workflow but doesn't actually call tools, OR calls them in wrong order.

**Pre-mitigation:**
- 3 dry runs in Days 5–7 to tune the SKILL.md customInstructions
- Build a `manual_mode.sh` script that invokes the MCP server directly from CLI as fallback
- Practice both flows: full Orchestrator + semi-manual

**During recording:**
- If Bob fails to auto-call: switch narration to *"For demo speed, we're invoking the MCP tools directly here — in normal use, Bob's Orchestrator handles this end-to-end."*
- The semi-manual demo still shows the value prop. Judge cares about RESULT, not orchestration purity.

### Mode C — Live network/Streamlit dashboard crashes

**Probability:** 15%. Streamlit is generally reliable but file-watcher can choke under rapid updates.

**Symptom:** Dashboard frozen, doesn't update, shows error.

**Pre-mitigation:**
- Run dashboard on `localhost:8501` ONLY. Never depend on `share.streamlit.io` for live demo.
- Set Streamlit `--server.fileWatcherType=poll` to avoid watchdog issues
- Test under rapid JSONL writes (10 updates in 5 seconds) on Day 5

**During recording:**
- Pre-render audit-report PDF as a file on disk. Show that as the closer instead of dashboard if dashboard fails.
- Have the cassette diff visualized in markdown as backup (just open the markdown file in VS Code, syntax-highlighted).

### Mode D — Bobcoin runs out mid-demo

**Probability:** 10%. Estimated 25-35 coins per full demo run, budget 40. Tight but feasible.

**Symptom:** Bob refuses to take action, prompts for upgrade.

**Pre-mitigation:**
- Use Plan mode (free) for any "thinking" prompts
- Cap `replay_and_diff` calls at 4 (encoded in SKILL.md Hard Rules)
- Pre-record successful run on Day 6 BEFORE running additional rehearsals
- Stretch: contact lablab.ai support pre-event to confirm whether IBM will grant additional credits

**During recording:**
- If hits limit during recording: cut to backup pre-recorded video for the remaining phases
- Edit invisibly. Don't mention the limit.

---

## 3. Tech debt risks (slow-burn)

### Risk T1 — Version conflicts between FastMCP, VCR.py, and Pydantic

**Probability:** 30% of dev time wasted if not pinned early.

**Mitigation:** Lock all versions in `pyproject.toml` on Day 2. Test fresh install on Day 3 in a clean Docker container.

### Risk T2 — Bob doesn't honor `groups.edit.fileRegex`

**Probability:** 15%. Custom Mode file regex is documented but new feature.

**Mitigation:** Test on Day 4. If fails, accept the risk and add manual `git diff` check before each commit. Don't block demo on this.

### Risk T3 — VCR.py struggles with httpx async clients

**Probability:** 20%. FastAPI uses httpx by default; VCR support added in 8.0+ but has edge cases.

**Mitigation:** Pin `vcrpy=8.1.0`. If issues persist, use `requests` library in seed traffic script (synchronous, fully supported).

---

## 4. Communication risks (team coordination)

### Risk C1 — Tech and business out of sync on demo timing

**Probability:** 40%. Each side has different mental model of "what the demo shows."

**Mitigation:** End of Day 5 (11/5): full team watches a dry run together. Business team sees actual screen, can write pitch line that matches actual visual. Tech team hears business team's framing, can tune dashboard moments.

### Risk C2 — Recording day chaos

**Probability:** 30%. 4 people, 1 recording session, multiple takes — coordination overhead.

**Mitigation:** Day 6 (12/5) practice recording. Same people, same setup. Iron out workflow. Day 16 (real recording) follows the same rhythm.

### Risk C3 — Submission form filled incorrectly on lablab.ai

**Probability:** 15%. Past lablab events had occasional submission form complaints (per Product Hunt reviews).

**Mitigation:**
- Submit at hour 46 (2-hour buffer before deadline)
- One person responsible: team lead opens form, screen-shares, all 4 review fields together before submit click
- Screenshot every page of submission flow as evidence

---

## 5. The single biggest risk

**If the team had to bet on one thing failing, it's:** *Bob's Custom Mode + Skill not behaving as documented during the actual hackathon.* IBM Bob is GA only since 28/4 — 17 days before kickoff. The Custom Mode + Skill features are barely battle-tested. Documentation may be ahead of implementation in places.

**Mitigation strategy across all triggers:** Always have a CLI fallback (`twin_mcp.cli` module) that invokes the MCP server directly without Bob orchestration. This means even if Bob completely fails, the team can ship a demo of the validator working as a standalone tool — just minus the Bob narrative emphasis.

This fallback is **mandatory** for Day 5 deliverable.
