---
name: code-review
description: Use to review a diff before merge. Checklist for correctness, tests, readability, security and scope, with severity levels and a verdict.
---

# Code review checklist

Get the diff: `git diff` (unstaged), `git diff --staged`, or `git diff <good-tag>..HEAD`.

## Correctness
- Does it meet every acceptance criterion in `docs/TASKS.md`, `docs/CONTRACTS.md` and the author's `docs/plan/<me>.md`?
- Off-by-one, None/empty handling, wrong types, mutable defaults, async/await mistakes, resource leaks, race conditions.
- Error handling: are failures surfaced with useful messages, or swallowed?

## Tests
- Is every behavior on the demo path covered? Would the tests FAIL if the feature broke?
- Any skipped, weakened, deleted or hard-coded-to-pass tests?
- Are mocks only at boundaries?

## Readability / understandability
- Names clear? Functions small? Module header present? Comments explain why?
- Could a teammate explain this to a judge in 60 seconds?
- Duplication that will hurt in the next 2 hours?

## Scope & hygiene
- Unrelated changes, formatting churn, new dependencies without justification, dead/commented code, leftover debug output.
- README / `.env.example` updated if usage changed.

## Security basics
- No secrets in code or git history. Inputs validated. No SQL/command injection. No `eval`/unsafe deserialization of untrusted data. CORS/ports/debug flags appropriate for a demo that may be on shared Wi-Fi.

## Output format
List findings as `BLOCKER | SHOULD FIX | NIT` — `file:line` — problem — why it matters — suggested fix. End with `APPROVE` or `CHANGES REQUESTED`. Run `./scripts/check.sh` before the verdict.
