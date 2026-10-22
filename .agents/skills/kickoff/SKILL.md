---
name: kickoff
description: Use at the very start of the hackathon, or whenever docs/PROJECT.md is empty. Turns the theme, role and constraints into an MVP, stack choice, demo story and a first vertical-slice plan.
---

# Kickoff (first 30 minutes)

Goal: leave this phase with a filled `docs/PROJECT.md`, a skeleton plan in `docs/PLAN.md`, and the human's approval of the MVP.

## Steps
1. **Collect inputs** from the human (ask in ONE message, not one at a time): theme/problem statement, judging criteria, time available, team size and who does what, the human's role, required tech/sponsor APIs, hardware available, what must be demoed and to whom.
2. **Define the problem and the user** in 2–3 sentences: who has the pain, what is the pain, why now.
3. **Define the MVP** as the smallest thing that tells a complete story in a 3-minute demo. List 3–5 must-have features, each phrased as an observable behavior. Put everything else under "Nice to have" and "Non-goals".
4. **Map to judging criteria**: for each criterion, name the feature or artifact that earns the points (innovation, technical depth, impact, UX, completeness, demo).
5. **Choose the stack**: the one the human already knows best, boring and well-documented. Justify in 3 lines. Prefer one language, one repo, one run command. Log in `docs/DECISIONS.md`.
6. **Identify the top 3 risks** (unfamiliar API, hardware, model quality, Wi-Fi, data) and a fallback for each. De-risk the scariest one FIRST with a spike (`scout` agent or 20-minute experiment).
7. **Write the demo story**: a numbered script of what the judges will see, in order. Build backwards from it.
8. **Plan the skeleton**: the thinnest end-to-end slice (input → processing → output) using fake data if needed. Write it as tasks in `docs/PLAN.md` under Phase 1.
9. **Set up the repo**: git init, `.gitignore`, `.env.example`, `scripts/check.sh` working, first commit with this kit. Create a first smoke test so the gate starts green.
10. **Confirm with the human**: show the MVP + demo script + stack, get a yes/edit, then start Phase 1.

## Output checklist
- [ ] `docs/PROJECT.md` filled (no template placeholders left)
- [ ] Demo script written
- [ ] Stack decision logged
- [ ] Top risks + fallbacks listed
- [ ] Phase 1 tasks in `docs/PLAN.md`
- [ ] Repo initialized, gate runnable, first commit done
