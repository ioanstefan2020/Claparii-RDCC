---
name: kickoff
description: Use at the very start. The theme, product and MVP are pre-filled in docs/PROJECT.md; this skill confirms them with the team, freezes the contract, and gets everyone set up in 45 minutes.
---

# Kickoff (team of 3, ~45 minutes)

`docs/PROJECT.md` is already drafted for the AccessABILITY challenge. Do NOT restart from scratch: verify and refine.

## Steps
1. **Read** `docs/PROJECT.md`, `docs/PLAN.md`, `docs/CONTRACTS.md`, `docs/TASKS.md` aloud as a team (10 min). List disagreements; the team decides in the room, P3 records the outcome in `docs/PROJECT.md`.
2. **Confirm the MVP** (3–5 observable features) and the cut list. Check each feature against the jury criteria table in `docs/PROJECT.md`. Remove anything the team cannot finish and demo in 24h.
3. **Pick roles** (P1 AI core + backend, P2 employee experience + accessibility, P3 employer side + content + evidence + pitch). Each person runs `git config hackathon.me pN` and `git switch -c pN/work`.
4. **Freeze the contract**: read `docs/CONTRACTS.md` together, fix anything ambiguous NOW, then nobody changes it without all three agreeing.
5. **Set up environments**: venv, `pip install -r requirements.txt`, `.env` from `.env.example`, `./scripts/check.sh` runs on every machine.
6. **Assign first tasks** (T1.1, T2.1, T3.1/T3.2) and agree the first merge point (M1) time.
7. **Interview plan**: P3 leads; agree who talks to whom at the Expo and when (see `validation-evidence`).
8. Post the plan in the group chat. Start.
