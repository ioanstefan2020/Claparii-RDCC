---
trigger: always_on
---
# Team mode rules (3 people, one repo)

1. Run `git config --get hackathon.me` at the start of every session. You are that person (p1/p2/p3). If empty, ask the human.
2. Read `OWNERS`. You may create/edit only paths owned by you. Everything else is read-only, including `AGENTS.md`, `scripts/`, `.agents/`, `docs/CONTRACTS.md` (unless you are p1 and the group agreed) and other people's docs.
3. Never run `git push` directly and never work on `main`. Ship with `./scripts/ship.sh "type: message"`. Sync with `./scripts/sync.sh`.
4. If you need a change in a file you do not own, write it as a request in your report: file, exact change, why, who owns it. Do not edit it "just this once".
5. Subagents you launch must be given a file-ownership list that is a subset of your own files.
6. Never rewrite history on shared branches. If a rebase conflicts, stop and tell the human: a conflict means ownership was violated.
7. Disability data is sensitive: never store, log, or infer diagnoses. Details in the `responsible-ai` skill.
