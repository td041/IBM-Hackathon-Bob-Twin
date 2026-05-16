# Rule 02 — Session Logging

These constraints apply ONLY when the active mode is `modernize-with-twin`.

The folder `internal-monologue/` is the team's per-session engineering log.
It exists to make Bob's reasoning auditable to humans reviewing the
migration after the fact, and to give the team a flat-file trail of
decisions, deferrals, and trade-offs separate from git history.

## R02.1 — One note per non-trivial session

When Bob is engaged for a task that involves code changes, design
decisions, or trade-off discussion, write a single markdown file into
`internal-monologue/` summarizing the session. Trivial follow-ups
(typo fixes, one-line tweaks already discussed in a recent note) may be
appended to the most recent relevant note instead of creating a new
file.

## R02.2 — File naming

File names start with an ISO-style timestamp followed by a concise
kebab-case description of the task:

```
YYYY-MM-DD_HHMM_<short-task-description>.md
```

Examples:

```
2026-05-15_0930_fix-trap-1-enum-serialization.md
2026-05-15_1410_add-tolerance-rule-status-code-changed.md
2026-05-16_0815_refactor-diff-engine-nested-types.md
```

The timestamp reflects when the session started, not when the note was
written.

## R02.3 — Required note content

Each note SHOULD contain, at minimum, the following sections:

1. **Task** — one-paragraph statement of what the user asked for.
2. **Approach** — the path chosen and, briefly, the alternatives
   considered and rejected.
3. **Files touched** — bullet list of paths that were modified, created,
   or deleted.
4. **Decisions and trade-offs** — anything non-obvious, including any
   tolerance rules introduced, validation rules relaxed, or behaviors
   intentionally left mismatched.
5. **Deferred** — work that was identified during the session but
   postponed, with enough context for a future reader to pick it up.

A note can be short — five sentences is fine — but each of the five
sections should be at least present, even if the answer is "none."

## R02.4 — Append-only

Existing notes in `internal-monologue/` MUST NOT be edited or deleted
during the run. If a later session reverses a decision recorded in an
earlier note, write a new note that explicitly references the old one
(by filename) and explains the reversal. Mirror the audit chain
philosophy from Rule 01: history is evidence, not draft material.

## R02.5 — Scope

Session notes record what happened in the session. They are not the
authoritative migration report, the audit trail (`audit_trail/`), or
the regulatory cassette (`golden_cassettes/`) — those are produced by
the MCP server and remain the source of truth for the migration
outcome. The session notes complement them with the human-readable
"why."
