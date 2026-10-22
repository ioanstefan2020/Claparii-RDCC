# AGENTS.md — Project Operating Manual

> Read this fully at the start of every session and after any long pause.
> HOW we work lives here. WHAT we build lives in `docs/PROJECT.md`. Progress lives in `docs/PLAN.md`.
> If `docs/PROJECT.md` is still the empty template, STOP and run the `kickoff` skill first.

## 0. Context
- This is a **time-boxed hackathon**. Priority order: (1) it works and can be demoed, (2) the code is understandable and easy to extend, (3) tests prove it works, (4) speed, (5) polish.
- The human must be able to **explain every part of the code** to judges and teammates. Prefer boring, readable code over clever code.
- Theme, role, judging criteria, MVP scope: see `docs/PROJECT.md`.

## 1. Non-negotiables
1. **Never say "done" without evidence.** "Done" = `./scripts/check.sh` exits 0 AND you show the relevant output AND you ran the feature end to end at least once. If you did not run it, say "not verified".
2. **Plan before code** for anything touching more than 1 file or taking more than ~30 minutes. Write the plan to `docs/PLAN.md` first.
3. **Tests ship with the code**, in the same change. No test = not finished.
4. **Small steps, each green.** Never stack a new change on a failing test.
5. **Do not invent APIs, flags, function names or package versions.** If unsure: read the docs/source, run `--help`, or run a 10-line experiment. State what you verified vs. what you assumed.
6. **No scope creep.** Anything outside the MVP goes to the Backlog in `docs/PLAN.md`, not into the code.
7. **Touch only what the task needs.** No drive-by refactors, no reformatting unrelated files, no deleting code you do not understand.
8. **Secrets never go in git.** Use `.env` (gitignored) and keep `.env.example` current.
9. **Decide, don't stall.** Ask the human only when blocked by a decision that is expensive to reverse. Otherwise pick the simplest option, log it in `docs/DECISIONS.md` (1–3 lines), and continue.
10. **Never fake green.** Do not delete/skip/loosen tests, mock away the thing under test, hard-code expected outputs, or catch-and-ignore errors to make a gate pass. If a test is wrong, say why and fix the test honestly.

## 2. Phases (always know which one you are in)
| Phase | Goal | Exit criterion |
|---|---|---|
| 0 KICKOFF | `docs/PROJECT.md` filled: problem, user, MVP, non-goals, stack, demo story | Human approves MVP |
| 1 SKELETON | Thinnest end-to-end vertical slice running (even with fake data) + first test + `check.sh` green + first commit | Demo path runs end to end |
| 2 BUILD | Feature loop (see §3), one vertical slice at a time, highest demo value first | Each feature merged green |
| 3 INTEGRATE | Everything works together; remove mock data where real data is feasible | Full demo script passes |
| 4 HARDEN | Error handling on the demo path, fallbacks, README, `.env.example`, clean clone test | Fresh clone runs |
| 5 FREEZE | Last ~20% of time: **bug fixes and demo prep only, no new features** | Demo rehearsed twice |

## 3. The feature loop (Plan → Build → Test → Review → Merge)
1. **Plan** — `plan-feature` skill / `architect` agent writes a spec into `docs/PLAN.md` (files, interfaces, tests, acceptance criteria, risks).
2. **Contracts first** — for anything with 2+ components, `api-contract` skill: define the interface (types, endpoints, message formats) BEFORE building either side.
3. **Build** — `implement-feature` skill / `engineer` agent(s). Red → Green → Refactor where logic is non-trivial.
4. **Test** — `tester` agent writes/extends tests from the acceptance criteria, independently from the engineer when possible.
5. **Gate** — run `./scripts/check.sh`. Fix until green. Then exercise the real feature manually (curl / CLI / UI / serial) and record what you saw.
6. **Review** — `reviewer` agent runs `code-review` skill on the diff (correctness, tests, readability, security). Fix blockers.
7. **Merge** — commit with a clear message, tick the box in `docs/PLAN.md`, add a 3-line note: *what / why / how to test*.

## 4. Code quality standards
- Small functions, one job each, descriptive names. Type hints / types on public functions.
- Modules with clear responsibilities; no circular dependencies; I/O at the edges, pure logic in the middle (so it is testable).
- Comments explain **why**, not what. Each module starts with a 2–3 line docstring/header: purpose, inputs, outputs.
- Fail loudly and early with useful error messages. Validate inputs at boundaries.
- No dead code, no commented-out code, no TODO without an entry in the Backlog.
- Config via env vars / one config module. No magic numbers; name constants.
- Prefer the standard library and well-known libraries already in the project. Adding a dependency requires a one-line justification in `docs/DECISIONS.md`.
- Keep a `README.md` current: what it is, how to install, how to run, how to test, architecture in 10 lines.

## 5. Testing policy
- Every behavior on the **demo path** has at least one automated test. Logic-heavy code gets unit tests (happy path + edge cases + error cases).
- At least one **integration/smoke test** exercises the whole pipeline (`scripts/smoke.sh` or a test file). It must fail if the system is actually broken.
- Test names describe behavior: `test_rejects_empty_input`, not `test_1`.
- Tests are deterministic: fix seeds, mock the network/LLM/time/hardware at the boundary, never mock the unit under test.
- Bug found? **Reproduce with a failing test first**, then fix, then keep the test.
- External services/LLM calls on the demo path need a **cached/mock fallback** so the demo cannot die from Wi-Fi or rate limits.
- Hardware / FPGA / embedded / ML: use simulation or testbenches, golden-model comparison, recorded fixtures, and a serial/protocol mock. State clearly what could only be verified on real hardware.

## 6. Agents, skills and parallelism
- Subagents live in `.agents/agents/<name>/agent.md`. Skills live in `.agents/skills/<name>/SKILL.md`. If your tool does not auto-load them, **read the file yourself when its trigger applies** (this works in every tool).

| Need | Agent | Skill |
|---|---|---|
| Understand codebase / research a library or API | `scout` | — |
| Design + spec + task breakdown | `architect` | `plan-feature`, `api-contract` |
| Implement a scoped task | `engineer` | `implement-feature` |
| Write/extend tests, break the feature | `tester` | `write-tests` |
| Inspect diff before merge | `reviewer` | `code-review` |
| Something fails and the cause is unclear | `debugger` | `debug-systematically` |
| Split work across agents safely | (orchestrator) | `parallel-work` |
| First 30 min of the event | (orchestrator) | `kickoff` |
| Final hour, README, pitch, demo script | (orchestrator) | `demo-prep`, `ship-checklist` |

- **Parallel rules** (see `parallel-work`): max 3 engineers at once; each owns a disjoint set of files; interfaces are fixed in `docs/PLAN.md` before they start; the orchestrator integrates and runs the gate. Never let two agents edit the same file.
- Delegate with a **self-contained brief**: goal, files owned, interfaces, acceptance criteria, how to test, what NOT to touch. Subagents do not see this conversation.

## 7. Context hygiene
- `docs/PLAN.md` is the shared memory. Update it as you go: current phase, what is done, what is next, known issues, backlog.
- Starting a fresh thread? First read: `AGENTS.md`, `docs/PROJECT.md`, `docs/PLAN.md`, `git log --oneline -15`, `git status`.
- One thread per feature. Long, wandering threads degrade quality; summarize into `docs/PLAN.md` and start fresh.

## 8. Git
- Commit after every green step: `feat: …`, `fix: …`, `test: …`, `docs: …`. Never commit a red `check.sh` to `main` (use a branch per feature if more than one person is working).
- Tag known-good states: `git tag good-<n>` — the rollback point if the final hour goes wrong.
- Never force-push shared branches. Never commit `.env`, keys, large binaries or model weights.

## 9. When stuck (hard 15-minute rule)
- Same error 3 times or 15 minutes without progress → STOP. Switch to the `debugger` agent / `debug-systematically` skill: reproduce, isolate, hypothesize, test one hypothesis at a time.
- Still stuck → write down what you know, what you tried, and propose 2 alternatives (including a simpler design or cutting the feature). Let the human decide.

## 10. How to report
Every report to the human uses this shape, short and honest:
- **Done:** what changed (files, behavior)
- **Evidence:** commands run + actual results (paste the key lines)
- **Not verified / risks:** be explicit
- **Next:** the single most valuable next step
