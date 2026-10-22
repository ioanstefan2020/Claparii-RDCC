---
name: ship-checklist
description: Use before every push to the shared repo and before final submission. A fast pre-push and pre-submit checklist.
---

# Ship checklist

## Before every push (2 minutes)
- [ ] `./scripts/check.sh` green (read the output, not just the exit code)
- [ ] The feature was run end to end at least once since the last change
- [ ] `git status` clean of junk: no `.env`, keys, `node_modules`, build output, large files, editor files
- [ ] `git diff --stat` matches what you intended (no surprise files)
- [ ] Commit message is clear; `docs/PLAN.md` ticked and notes added
- [ ] Pull/rebase first if others push to the same branch; re-run the gate after merging

## Before final submission
- [ ] Fresh clone in a new directory: install, run and test per README with no extra steps
- [ ] `.env.example` lists every variable; mock/fallback mode works without keys
- [ ] README has pitch, run, test and architecture sections; screenshots/GIF added
- [ ] Demo rehearsed twice; fallback recording available
- [ ] Repo is public/shared as required; license and team names added if required
- [ ] Tag the submission: `git tag submission`

## If something is red at the last minute
- Roll back to the last `good-*` tag rather than patching under pressure. A smaller working demo beats a larger broken one.
