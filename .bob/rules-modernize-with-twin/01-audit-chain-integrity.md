# Rule 01 — Audit Chain Integrity

These constraints apply ONLY when the active mode is `modernize-with-twin`.

## R01.1 — Cassettes are append-only

Files matching `golden_cassettes/**/*.yaml` MUST NEVER be edited or deleted
during a migration. They are the regulatory evidence baseline.

If a cassette appears wrong (e.g., recorded against the wrong server,
incomplete coverage), the correct action is:

1. Discard the entire run by tagging it `aborted-<reason>` in the audit trail
2. Start a fresh run with a new `run_id`
3. Capture a new cassette

Never silently re-record over an existing cassette. The diff engine and
audit chain depend on cassette immutability.

## R01.2 — Audit trail files are append-only

Files matching `audit_trail/**/*.jsonl` MUST NEVER be opened in write mode
that would truncate them. The hash chain links each entry to the previous;
truncation breaks integrity verification.

The MCP server is the only authorized writer for these files. If Bob needs
to inspect them, use `read` only.

## R01.3 — No history rewriting during a run

While in `modernize-with-twin` mode, the following git operations are
PROHIBITED:

- `git push --force`
- `git push --force-with-lease`
- `git rebase` against any commit that contains a Checkpoint
- `git commit --amend` against a commit that captured a cassette or audit entry
- `git reset --hard` to a commit before the run started

Allowed: regular `git commit`, `git checkout` to a Checkpoint (which Bob's
own Checkpoints feature handles natively), and `git push` (without force).

## R01.4 — One run, one branch

Each migration run should occur on its own branch. The branch name should
include the run_id from `capture_baseline` for traceability:

```
feature/migrate-pydantic-v2-<run_id>
```

This makes the audit report self-contained: the branch name, the run_id,
the cassette filename, and the audit JSONL all match.

## R01.5 — Override requires explicit user statement

If the user instructs Bob to mark a migration complete with
`equivalence_score < 0.95`, Bob must:

1. ASK the user to provide a free-form rationale string (one sentence
   minimum) explaining why the override is acceptable.
2. RECORD that rationale in the audit report's "Manual Override" section.
3. Set the report's `human_override` field to `true`.

This is not a hindrance — it is the audit value proposition. The override
record is what allows future regulators to distinguish "tool failure" from
"informed business decision."
