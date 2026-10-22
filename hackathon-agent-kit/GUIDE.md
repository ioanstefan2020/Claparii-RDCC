# Hackathon Agentic Setup — Complete Guide

Stack assumed: **Antigravity (`agy`) inside Zed** as the main engine, **Zed agent + DeepSeek** as the second brain.
Goal: high-quality, understandable, tested code, with agents that plan first, work in parallel, and **prove** things work before calling them done.

> Honesty note: Antigravity changes fast and its docs are thin. The layout below (`AGENTS.md`, `.agents/rules`, `.agents/skills/<name>/SKILL.md`, `.agents/agents/<name>/agent.md`) matches what current community write-ups report for the `agy` CLI. **Do the 20-minute dry run in Part 2 tonight** so any mismatch shows up before the event, not during it. Every file in this kit also works as plain "instructions the agent reads", so even if auto-discovery misbehaves, the workflow still holds.

---

## Part 1 — What you are building (the mental model)

```
AGENTS.md                      <- the constitution: always-on rules, phases, definition of done
.agents/rules/*.md             <- always-on rules (orchestration, testing gate)
.agents/agents/<role>/agent.md <- specialist subagents: architect, engineer, tester, reviewer, debugger, scout
.agents/skills/<name>/SKILL.md <- procedures loaded on demand: kickoff, plan, implement, tests, debug, review, parallel, contract, demo, ship
docs/PROJECT.md                <- WHAT we build (filled at kickoff)
docs/PLAN.md                   <- shared memory: status, tasks, contracts, backlog
docs/DECISIONS.md              <- why we chose things
docs/PROMPTS.md                <- copy-paste prompts
scripts/check.sh               <- THE quality gate (lint + tests + smoke). Agents must run it.
```

Why this works:
1. **Rules vs skills vs agents.** Rules are always on (keep them short). Skills are procedures loaded only when relevant (saves context). Subagents are isolated workers with their own context (better focus, can run in parallel).
2. **The gate makes "done" objective.** The single biggest source of wasted hours is an agent saying "done" when it is not. `scripts/check.sh` plus the rule "show evidence" removes that.
3. **Docs as memory.** Agents forget between threads. `docs/PLAN.md` is the memory they (and you and teammates) re-read.
4. **Separation of roles.** The agent that writes code should not be the only one that tests or reviews it.

---

## Part 2 — Tonight (about 45–60 minutes)

### Step 1: Update and verify tools
- Update `agy` to the latest version (subagent behavior was buggy in older releases; community notes say 1.3.4+ fixed major issues). Check `agy --version`, update with whatever method you installed it with.
- Update Zed to the latest stable.
- Confirm you are logged in to Antigravity with the student Pro account and can send a prompt from the agent thread in Zed.
- Confirm DeepSeek works in Zed's agent panel (key entered, a test message answers). Look in the model picker for which DeepSeek model supports tools/agent mode; use that one for edits and the reasoning one only for plain chat opinions.
- Confirm `git`, your language toolchains (Python/Node/etc.), and `pytest`/test runner are installed.

### Step 2: Install the kit into a throwaway repo
```bash
unzip hackathon-agent-kit.zip
cd hackathon-agent-kit
./install.sh ~/dry-run        # copies files, never overwrites, creates ~/.gemini/AGENTS.md if you have none
cd ~/dry-run && zed .
```

### Step 3: Dry run (this is the most important step of the night)
In the Antigravity thread inside Zed, paste **Prompt 1** from `docs/PROMPTS.md` (setup self-test). You are checking:
- [ ] It sees AGENTS.md, the rules, the skills and the six subagents (`/agents` in the CLI lists subagents).
- [ ] It really launches separate subagents (not just role-playing inline).
- [ ] `./scripts/check.sh` runs and the agent reports its real output.

Then give it a tiny real task to exercise the whole loop (10–15 min):
```
Implement feature: a CLI `todo` with add/list/done commands persisted in a JSON file.
Follow the full loop in AGENTS.md §3 and show evidence.
```
Watch for: spec written into `docs/PLAN.md`, tests written, gate run, real output shown, reviewer verdict. Note anything that does not trigger and apply the fixes in Part 9.

### Step 4: Zed configuration
- Open the **Agent panel** and check how it reads rules: Zed reads a root `AGENTS.md` automatically for its own agent, so your Zed agent and DeepSeek follow the same constitution. Open a Zed agent thread and ask "which rules files did you load?" to confirm.
- In Zed's **Rules Library**, paste the contents of `global/AGENTS.md` as a default rule (personal style that applies everywhere).
- Keep the **Zed agent on "ask/approve" for destructive commands**. If the Antigravity thread has an auto-approve (yolo) mode, use it only inside the hackathon repo, never in a directory with other projects or personal data.
- Learn three shortcuts you will use all day: open agent panel, new thread, and `@`-mention a file in the prompt.

### Step 5: Prepare the machine
- [ ] Charger, hotspot data plan, second Wi-Fi option, mouse if you like one.
- [ ] Global git config set (name, email), SSH key or token for GitHub.
- [ ] Docker/Node/Python/Rust toolchains installed and tested; package manager mirrors reachable.
- [ ] A starter template repo for your usual stack (hello-world that builds and runs a test) so skeleton time is minutes.
- [ ] API keys in a password manager, not in a chat.
- [ ] Notes of your quota: Antigravity Pro has usage limits. Plan to spend the strong model on architect/debugger and a fast model on engineers.
- [ ] Sleep. Tired humans approve bad plans.

### Step 6: Customize the kit
- Read `AGENTS.md` once. **Delete anything that does not apply** to your event (e.g. if hardware-only, trim web notes). Shorter, sharper rules get followed better.
- Add 3–5 lines of personal style to `global/AGENTS.md` if you like.
- Leave `docs/PROJECT.md` empty; the kickoff skill fills it.

---

## Part 3 — Event morning, hour by hour

Let **T** be the total time. Adapt the table; the *order* matters more than the numbers.

| When | Phase | What you do |
|---|---|---|
| 0–5% of T | Kickoff | Read the theme with your team. Run **Prompt 2 (Kickoff)**. Approve MVP, stack, demo script. |
| 5–15% | Skeleton | **Prompt 3.** Repo, gate green, thinnest end-to-end slice, first commit, tag `good-1`. |
| 15–65% | Build loop | One feature at a time via **Prompt 4/5**. Highest demo value first. Commit + tag after each green feature. |
| 65–80% | Integrate + harden | Replace fake data where feasible, error handling on the demo path, fallbacks, `docs/ARCHITECTURE.md` (**Prompt 9**). |
| 80–100% | Freeze + demo | **Prompt 11.** No new features. Fresh-clone test, README, rehearsal x2, submission before the deadline. |

Example for a 24h event: kickoff to hour 1, skeleton by hour 3, features hours 3–15, integrate/harden hours 15–19, **freeze at hour 19**, demo prep hours 19–23, submit with 1 hour of slack. For a 12h event, freeze at hour 9.

### Kickoff details
1. Paste Prompt 2 with the theme, criteria, time, team, your role, and the stack you know best.
2. The agent asks at most 5 questions in one message and fills `docs/PROJECT.md`.
3. **You** decide the MVP. Cut hard: a complete 3-minute story beats a wide feature list. Ask yourself: what will the judges actually see, and what earns points on their criteria?
4. De-risk the scariest unknown (unfamiliar API, hardware bring-up, model quality) in the first hour, with the `scout` agent or a 20-minute spike. If it cannot work, you want to know at hour 1, not hour 15.
5. Commit the kit and `docs/` so teammates' agents follow the same rules.

### The build loop (repeat per feature)
Paste **Prompt 4**. What should happen, and what you should do at each step:
1. **Architect** writes the spec into `docs/PLAN.md`. *You*: read the 5-line summary and the acceptance criteria. This is the cheapest place to catch a wrong idea. Spend 2 minutes here.
2. **Contracts** are frozen if multiple components are involved.
3. **Engineers** implement (parallel only if files are disjoint), test-first.
4. **Tester** independently attacks the feature.
5. **Gate + end-to-end run** with pasted evidence.
6. **Reviewer** gives BLOCKER/SHOULD FIX/NIT and a verdict.
7. Commit, tick `docs/PLAN.md`, tag `good-N`.

Your jobs during the loop: define priorities, approve plans, run the demo path yourself every hour, and keep scope under control. The agents' job is execution plus proof.

---

## Part 4 — Using your three engines well

| Engine | Use it for | Avoid |
|---|---|---|
| **Antigravity (agy) thread in Zed** | Orchestrator + subagents: planning, parallel implementation, testing, reviewing. Your main workhorse. | Burning the strong model on trivial edits. |
| **Zed agent + a strong model** | Quick, targeted edits in the file you have open; explanations; README/docs; inline fixes. | Large multi-file features. |
| **Zed agent + DeepSeek** | Cheap bulk work: boilerplate, tests from a clear spec, docs, **independent second-opinion review** (Prompt 10). Different model family = different blind spots. | Anything needing long autonomous tool loops if the model's tool support is weak. |

Practical rules:
- **One agent edits a given file at a time.** If Antigravity is running a build, do not have the Zed agent edit the same files. Use DeepSeek for read-only review while the main agent builds.
- **Model by role.** Strong model for architect, debugger, reviewer. Fast model for engineers/scout on well-specified tasks. Escalate to the strong model if a task fails twice.
- All three tools read the same `AGENTS.md`. If a tool does not auto-load skills, add to the prompt: "Read `.agents/skills/<name>/SKILL.md` and follow it."
- Save quota: do not ask the agent to "explore the whole repo" every thread. Point it at `docs/PLAN.md` and specific files.

---

## Part 5 — Parallel agents without chaos

- Parallelize **only after** the plan is approved and interfaces are frozen.
- Max **3** engineers at once; each **owns different files**; shared files (config, route registry, manifests, README) belong to the orchestrator.
- Start from a committed stub of every contract so each side can test without the others.
- Integration is **your orchestrator's job** (and yours): merge, run the gate, run end to end.
- Use the `tester` in parallel with engineers: it writes tests against the acceptance criteria.
- Never parallelize debugging, schema/migration work, or tasks under ~20 minutes.
- If agents share one folder, file ownership is your isolation. For stronger isolation: `git worktree add ../wt-feature -b task/feature`.

---

## Part 6 — Testing strategy that saves your night

The rule: **an agent may not call something done until the gate is green and the feature was run end to end.**

1. **`scripts/check.sh`** auto-detects Python/Node/Rust/Go/Make and runs lint + tests + `scripts/smoke.sh`. It fails when no tests exist, on purpose. For monorepos, create `scripts/check.local.sh` (it replaces autodetection).
2. **Smoke test** (`scripts/smoke.sh`, start from `smoke.sh.example`): launches the app in test mode, pushes one realistic input through the entire demo path, asserts the output. It must fail if the system is really broken. Create it during the skeleton phase.
3. **Unit tests** for logic with happy/edge/error cases. **Contract tests** at component boundaries.
4. **Bug = failing test first**, then fix. Your bug count then only goes down.
5. **Mutation sanity check** (from the `write-tests` skill): break the code on purpose; the test must fail. This catches decorative tests.
6. **Fallbacks for flaky externals**: mock/cached response for every API/LLM/hardware call on the demo path, switchable by an env var, so Wi-Fi or rate limits cannot kill the demo.
7. **Fresh-clone test** before submission: clone to `/tmp`, follow the README, run the gate.
8. **Hardware/ML**: simulation + self-checking testbenches, golden-model comparisons, recorded serial captures, fixed-seed sanity runs, and a metric threshold test on a small held-out set. Mark what can only be verified on the physical board.
9. **Your own 60-second check** every hour: run the demo script yourself. Agents do not replace your eyes on the real thing.

---

## Part 7 — Best practices checklist (agents and you)

**Prompting**
- Give the goal, the *why*, constraints, and acceptance criteria. "Implement X so that Y is observable" beats "make X".
- Ask for the plan first on anything non-trivial; approve before code.
- One task per thread; start fresh threads with **Prompt 0**.
- Use `@file` references instead of pasting large code; paste the **exact command and full error** for bugs.
- Say what NOT to touch. Tell it the files it owns.
- Ask for evidence: "show the command and output."
- When output drifts, re-anchor: "re-read AGENTS.md §1 and docs/PLAN.md."

**Quality**
- Boring stack you know. Fewer dependencies. One run command.
- Pure logic in the middle, I/O at the edges (testable and explainable).
- Module headers and why-comments; run **Prompt 9** once mid-event so the code is explainable to judges.
- Review every diff yourself at least skimming the summary; agents are fast but you are accountable.

**Process**
- Vertical slices over horizontal layers.
- Commit after every green step; tag `good-N`; roll back instead of patching under pressure.
- 15-minute rule: stuck → debugger agent → alternatives → cut scope.
- Freeze early. Most hackathon failures come from late features.
- Keep `docs/PLAN.md` updated; it is also your standup notes with teammates.

**Team**
- Commit AGENTS.md, `.agents/`, `docs/` so every teammate's agent follows the same rules.
- Assign directory ownership per person; branch per feature; small frequent merges; gate before push.

---

## Part 8 — Customizing for the theme and your role

After the theme is announced, spend 10 minutes tailoring:
1. Add a "Domain notes" section to `docs/PROJECT.md` (glossary, data formats, API links, constraints).
2. Add a **stack skill** if useful: `.agents/skills/<stack>/SKILL.md` with commands, project layout, test runner, lint config, common pitfalls (see template below).
3. Trim `AGENTS.md` rules that do not apply; add 2–3 rules specific to the theme (e.g. "all model calls go through `llm.py` with caching").
4. Adjust subagents: add a `data-engineer` or `frontend` or `hardware` agent by copying `engineer/agent.md` and changing the focus.

Role flavors:
- **Team lead / PM**: you own `docs/PROJECT.md`, `docs/PLAN.md`, priorities and the demo script. Use agents for planning, cutting scope (Prompt 12), integration and the README.
- **Backend / systems**: strongest in contracts, tests, smoke script. Own `api-contract` and the gate.
- **Frontend / UX**: ask for a design pass with a mock-data layer first so UI is demoable before the backend is ready.
- **Hardware / embedded / FPGA**: add testbench + simulation to `check.sh` via `check.local.sh`; separate pure logic from register access; keep a host-side mock of the device so the rest of the team is unblocked.
- **ML / edge**: golden inputs/outputs, fixed seeds, metric threshold tests, cached model outputs for the demo, quantization/latency numbers recorded in the README.

Stack skill template:
```markdown
---
name: stack-<name>
description: Use when working on <stack>. Commands, layout, testing and pitfalls for this project.
---
# <Stack> playbook
- Run: `<cmd>`   Test: `<cmd>`   Lint: `<cmd>`
- Layout: `<dirs and what lives where>`
- Conventions: <naming, error handling, config>
- Pitfalls: <the 5 mistakes agents make in this stack>
```

---

## Part 9 — When things go wrong

| Symptom | Fix |
|---|---|
| Subagents do not show up / are not used | Update `agy`; run `/agents`; keep files at `.agents/agents/<name>/agent.md`; the orchestration rule makes the main agent read the file and inject it into a subagent prompt, so tell it: "use the orchestration rule, delegate to the architect via direct injection". |
| Subagent cannot edit files or run commands | Check its frontmatter against the agy subagent docs (some versions use a `tools:` list); fall back to the direct-injection method, which does not depend on frontmatter. |
| Agent says "done" but it is broken | Prompt 8 ("prove it"). If it keeps happening, add the exact failure to `AGENTS.md` §1 as a rule. |
| Agent weakens tests to go green | Rule 10 in AGENTS.md; reviewer checks for it. Revert the test change and re-brief. |
| Same error 3 times | Stop. Debugger agent (Prompt 6), strongest model, fresh thread with only the failing command and relevant files. |
| Context drift / agent forgets rules | Fresh thread + Prompt 0. Summarize state into `docs/PLAN.md` first. |
| Scope creep | Backlog it. Prompt 12 to cut. Feature freeze at 80%. |
| Merge conflicts between agents | Ownership was violated. Revert the offending edits; re-brief with a "do not touch" list; integrate sequentially. |
| Hallucinated API / package | Use the `scout` to verify against docs/source/`--help`; pin versions; add to DECISIONS. |
| Quota/rate limit hit | Switch engineers to the fast model; move review and docs to DeepSeek in Zed; cut thread length; stop broad "explore" prompts. |
| Wi-Fi/API dies in the demo | Mock/cached mode via env var; recorded video backup. |
| Late-night red gate | Roll back to the last `good-*` tag. Smaller and working beats bigger and broken. |

---

## Part 10 — Cheat sheet

```
New thread        -> Prompt 0 (resume)
First 30 min      -> Prompt 2 (kickoff)
First slice       -> Prompt 3 (skeleton)
Every feature     -> Prompt 4 (full loop) / 5 (parallel)
Something broke   -> Prompt 6 (debug)
Before merging    -> Prompt 7 (review) + gate
"It's done"       -> Prompt 8 (prove it)
Explainability    -> Prompt 9
Second opinion    -> Prompt 10 (DeepSeek, read-only)
Last 20% of time  -> Prompt 11 (freeze + demo)
Running out       -> Prompt 12 (cut scope)

Gate:   ./scripts/check.sh
Tag:    git tag good-N
Resume: read AGENTS.md, docs/PROJECT.md, docs/PLAN.md, git log
```

Remember: you are the architect of the outcome. Agents are fast; your job is to choose the right thing to build, keep scope small, verify with your own eyes, and be able to explain every part on stage.
