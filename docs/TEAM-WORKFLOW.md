# Team workflow — 3 people, one repo, zero merge conflicts

## Rules in one breath
1. Everyone owns different files (`OWNERS`). Edit only yours. Need a change elsewhere → ask the owner in the group chat.
2. Work on your own branch (`pN/work`). Never on `main`.
3. Ship small and often with `./scripts/ship.sh "type: message"`. It commits, rebases on main, checks ownership, runs the gate, pushes.
4. Sync with `./scripts/sync.sh` before every new task and after teammates announce a ship.
5. Never push red. Never force-push. Never commit `.env`.

## One-time setup (each person)
```bash
git clone <REPO_URL> hackathon && cd hackathon
git config hackathon.me p1            # p1, p2 or p3
git config user.name "Your Name" && git config user.email "you@example.com"
git switch -c p1/work
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                  # LLM_PROVIDER=mock works without keys
./scripts/check.sh
```
## Daily loop
```bash
./scripts/sync.sh                     # get teammates' work
# ... work with the agent, only in your files ...
./scripts/check.sh                    # gate
./scripts/ship.sh "feat(simplify): endpoint + guardrail"
```
## When things go wrong
| Message | Meaning | Do |
|---|---|---|
| `Set who you are first` | no `hackathon.me` | `git config hackathon.me p1` |
| `OWNERS... OWNERSHIP PROBLEM` | you changed someone else's file | follow the printed undo steps, then `git commit --amend --no-edit && ./scripts/ship.sh` |
| `push rejected` | someone shipped while you were checking | run `./scripts/ship.sh` again |
| `REBASE CONFLICT` | two people edited the same file (ownership broken) | `git rebase --abort`, tell the group chat which file, agree who keeps what |
| `GATE: FAIL` before your change | main is red | tell the group chat; do not fix others' files |
| Everything is broken at the end | | `git switch main && git pull && git reset --hard good-<n>`-style rollback by P3 on agreement |

## Group chat protocol
- `P1 shipped: <what>. P2/P3 can now …` (every ship, one line)
- `BLOCKED: need <exact thing> from <person>`
- `CONTRACT CHANGE?: <proposal>` → all three reply OK before P1 edits `docs/CONTRACTS.md`
- Every full hour: 30-second status each (done / next / blocked).

## Tags (P3 runs these on main after pulling)
```bash
git switch main && git pull && git tag good-1 && git push origin good-1     # also good-2, good-3, good-freeze, submission
git switch p3/work
```
## Using agents without stepping on each other
- Each person has their own agent thread(s) on their own branch/checkout. Agents never touch files outside the owner's list (rule in `.agents/rules/team-mode.md`).
- If your agent says "I need to change X in someone else's file", it must write a request; you paste it to the group chat.
- Two people prompting at the same time is fine: ownership keeps edits apart and rebases are trivial.
