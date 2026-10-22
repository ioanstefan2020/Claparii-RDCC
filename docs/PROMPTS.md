# Prompt library (copy, paste, replace <…>)

Tip: reference files with `@` in your tool (e.g. `@docs/PLAN.md`). One task per thread. Start every new thread with prompt 0.

## 0. Resume / fresh thread
```
Read AGENTS.md, docs/PROJECT.md, docs/PLAN.md, then run `git log --oneline -15` and `git status`.
Summarize in 5 lines: current phase, what is done, what is in progress, what is broken, and the single most valuable next step. Do not change any files yet.
```

## 1. Setup self-test (tonight, in a throwaway repo)
```
List the rules, skills and custom subagents you can see in this workspace (names only). Then:
1. Delegate to the `scout` subagent: "Report the Python version, whether pytest is installed, and the OS."
2. Delegate to the `architect` subagent: "Write a 5-line plan for a CLI that adds two numbers, with one acceptance criterion."
3. Run ./scripts/check.sh and tell me exactly what it reported.
Tell me which delegations really launched a separate subagent and which you did inline.
```

## 2. Kickoff (first 30 minutes)
```
Run the `kickoff` skill. Here is everything I know:
- Theme / problem statement: <paste>
- Judging criteria: <paste>
- Time: <start> to <deadline>, freeze at <time>
- Team and roles: <names, what each does>. My role: <role>
- Mandatory tech / sponsors / hardware: <paste>
- Stack I know best: <languages/frameworks>
Ask me at most 5 clarifying questions in ONE message, then fill docs/PROJECT.md, propose the MVP + demo script, and write Phase 1 tasks in docs/PLAN.md. Wait for my approval before writing any code.
```

## 3. Skeleton (thinnest end-to-end slice)
```
Phase 1. Build the thinnest end-to-end vertical slice of the MVP (fake data is fine) following the tasks in docs/PLAN.md.
Requirements: scripts/check.sh green, one smoke test for the whole path, README with run/test commands, first commit, tag good-1.
Use the architect for the contracts, then engineers per the parallel-work skill if the tasks are independent. Report with evidence.
```

## 4. New feature (the main loop)
```
Implement feature: <one sentence of user-visible behavior>.
Follow the full loop in AGENTS.md §3: architect writes the spec in docs/PLAN.md (interfaces, tasks with file ownership, acceptance criteria) -> show me a 5-line summary -> engineers implement (parallel only if files are disjoint) -> tester independently verifies -> reviewer reviews the diff -> you run ./scripts/check.sh and the feature end to end.
Do not report done without pasted evidence. Anything out of scope goes to the Backlog.
```

## 5. Parallel build of an approved plan
```
The plan for <feature> in docs/PLAN.md is approved. Use the parallel-work skill: freeze the contracts and commit stubs first, then launch up to 3 engineers on the disjoint tasks with self-contained briefs, tester in parallel on the acceptance criteria. When they report, integrate yourself, run the gate, run the feature end to end, then launch the reviewer. State which specialist/model you launched for each task.
```

## 6. Bug / failing test
```
<paste the exact command and the full error output>
Use the debug-systematically skill. Reproduce first, write a failing regression test, find the ROOT CAUSE (explain it in one sentence), fix, then run ./scripts/check.sh. If you are not making progress after 15 minutes, stop and give me 2 alternatives.
```

## 7. Review before merge
```
Launch the reviewer on `git diff <good-tag>..HEAD` using the code-review skill. Run ./scripts/check.sh yourself. Give me BLOCKER / SHOULD FIX / NIT findings and a verdict. Fix the blockers, then re-run the gate.
```

## 8. "Prove it" (when an agent says done)
```
You said this is done. Prove it: run ./scripts/check.sh and show the output, run the feature end to end the way a judge would and show what happened, and list anything you did NOT verify. Then try to break it with 5 edge cases.
```

## 9. Understandability pass (so you can explain it to judges)
```
Without changing behavior: add a module header to each file (purpose, inputs, outputs), rename anything unclear, and write docs/ARCHITECTURE.md: a 10-line overview, a diagram (Mermaid or ASCII), the data flow of the demo path, and the 5 design decisions a judge is most likely to ask about, each with a one-sentence "why". Run the gate after.
```

## 10. Independent second opinion (use the OTHER model, e.g. DeepSeek in Zed agent)
```
You are an independent reviewer. Read AGENTS.md and docs/PLAN.md, then review `git diff <good-tag>..HEAD`. Look for bugs the original author would miss: wrong assumptions, edge cases, security issues, tests that would pass even if the feature were broken. Do not edit files. List findings with file:line and severity.
```

## 11. Freeze and demo prep
```
We are at feature freeze. Run the demo-prep and ship-checklist skills. Write the demo script in docs/PROJECT.md, add mock/cached fallbacks for every external call on the demo path (switchable by env var), write the README, test a fresh clone in /tmp, and tag good-freeze. Report what could still fail during the demo.
```

## 12. Cut scope (when time is running out)
```
We have <N> hours left. Given docs/PROJECT.md and the current state in docs/PLAN.md, propose the smallest set of work that gives a complete, demoable story. List what to cut, what to fake (with an honest label), and what to finish. Do not write code until I approve.
```
