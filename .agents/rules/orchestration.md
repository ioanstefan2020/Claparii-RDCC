---
trigger: always_on
---
# Orchestration rules (root agent = Master Orchestrator)

The main thread coordinates; specialists do focused work in isolated context. This keeps quality high and lets work run in parallel.

## Delegation method (Direct Injection) — use this every time
When delegating to a specialist from `.agents/agents/`:
1. Read the specialist's file in full (e.g. `.agents/agents/architect/agent.md`; global fallback `~/.gemini/config/agents/<name>/agent.md`).
2. Launch a subagent with `Role` set to the specialist name (e.g. "Technical Architect", "Software Engineer", "QA Tester").
3. Put the **entire verbatim contents** of that file at the top of the subagent prompt, followed by a self-contained task brief:
   - Goal and why it matters
   - Files it OWNS (may edit) and files it may only READ
   - Interfaces/contracts it must respect (point to the section of `docs/plan/<me>.md`)
   - Acceptance criteria and the exact test command(s)
   - What it must NOT touch
4. State in the user-facing message which specialist you launched, on which task, and with which model.

## Model selection
- Architect / debugger / reviewer: the strongest reasoning model available.
- Engineer / tester / scout: a fast model is fine for well-specified tasks. Escalate to a stronger model if a task fails twice.

## Flow
1. **Design first.** For any non-trivial feature, the architect writes the spec into `docs/plan/<me>.md` BEFORE any implementation. Jumping straight to code is not allowed.
2. **Review the spec yourself** (completeness, scope, interfaces). Split into non-overlapping tasks.
3. **Implement in parallel** — up to 3 engineers, disjoint files (see `parallel-work` skill).
4. **Integrate** — merge results, run `./scripts/check.sh`, run the feature end to end.
5. **Test independently** — launch the tester on the acceptance criteria.
6. **Review** — launch the reviewer on the diff. Send failures back to the right engineer with the exact error output.
7. **Report** using the format in `AGENTS.md` §10, with evidence.

Never trust a subagent's claim of success: re-run the gate yourself and look at the result before reporting.

## Team mode
Every brief you write for a subagent lists the files it owns, and that list must be a subset of the files the human you work for owns (see `OWNERS`). Subagents never edit `docs/CONTRACTS.md`, `AGENTS.md`, `scripts/`, or other people's files, and never run `git push`.
