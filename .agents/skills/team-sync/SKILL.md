---
name: team-sync
description: Use at the start of a session, before starting a new task, after a teammate ships, and when shipping. The exact git routine for 3 people owning disjoint files.
---

# Team sync routine

## One-time (already done at kickoff; re-check)
```
git config --get hackathon.me      # must print p1, p2 or p3
git branch --show-current          # must be <me>/work
```

## Start of every task
```
./scripts/sync.sh                  # rebase your branch on origin/main (needs a clean tree)
./scripts/check.sh                 # confirm you start green
```
If `check.sh` is red BEFORE you changed anything, tell the group chat (someone shipped something broken) — do not fix files you do not own.

## While working
- Commit locally whenever you like (`git add -A && git commit -m "wip"`), but only `ship.sh` pushes.
- Only touch files you own (`OWNERS`). `python3 scripts/ownership.py <me> $(git diff --name-only origin/main...HEAD)` shows violations early.

## Ship (after the gate is green and you ran the feature)
```
./scripts/ship.sh "feat(simplify): endpoint + guardrail"
```
It commits, rebases on `origin/main`, checks ownership, runs the gate, and pushes to `main`.
- "push rejected": someone shipped meanwhile → run `./scripts/ship.sh` again.
- "REBASE CONFLICT": ownership was violated somewhere. Stop, tell the group chat, `git rebase --abort`, and ask which file collided.
- "OWNERSHIP PROBLEM": undo the listed file changes as the message says, then re-ship.

## After a teammate announces a ship
Run `./scripts/sync.sh` at the next natural pause (not mid-edit), then re-run the gate.

## Group chat messages (short)
- `P2 shipped: planner screen + ICS export. Needs from P1: /api/plan/extract returns due_iso (T1.4).`
- `P1 blocked: need employer prompt in app/prompts/employer.py to be exported as PROMPT. @P3`
- `Contract change proposal: …` (all three must agree before P1 edits `docs/CONTRACTS.md`)
