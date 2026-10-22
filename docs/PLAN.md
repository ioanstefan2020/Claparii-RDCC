# PLAN — shared board (owner: P3). Personal status lives in docs/plan/pN.md.

## Clock (assumed start Thu 22 Oct 12:00 — EDIT if different)
| Milestone | Hours | Clock | Meaning |
|---|---|---|---|
| Kickoff done | 0:45 | 12:45 | contract frozen, roles/git set |
| **M1** skeleton on main | 1:30 | 13:30 | app runs in mock mode, check.sh green on all machines |
| **M2** features on main (mock) | 8:00 | 20:00 | clickable demo path with mock LLM |
| **M3** real-LLM integration | 14:00 | 02:00 | demo script passes with real LLM |
| **Harden done** | 19:00 | 07:00 | a11y audit, README, fresh-clone OK |
| **FREEZE** | 19:00 | 07:00 | no new features |
| Rehearsal x2 + recording | 19:00–22:00 | 07:00–10:00 | |
| Submission slack | 22:00–23:00 | 10:00–11:00 | submit early |
| Stop coding | 24:00 | 12:00 | hard stop |
Sleep in shifts (2–3 h each) but never all at once; whoever is awake owns the group chat. No big new work after hour 17.

## Status
- Current phase: 0 KICKOFF
- Last green tag on main:
- Blocking issues:
- Next merge point:

## Architecture
```
Browser (web/, vanilla ES modules)                         FastAPI (app/)
┌──────────────────────────────┐   JSON    ┌────────────────────────────────────────────┐
│ Hub  ├ Employee: profile,    │ ───────▶ │ routers/ (auto-discovered)                  │
│      │  clarify, plan, meeting│          │  simplify · plan · meeting   (P1)           │
│      │  adjustments           │ ◀─────── │  adjustments · employer      (P3)           │
│      └ Employer: analyze     │  envelope │ guardrails.py (source-quote verify)         │
│ localStorage: profile only   │           │ llm/ generate_json(task, system, user,      │
│ Web Speech in / TTS out      │           │      schema, mock) → mock | gemini | deepseek│
│ ICS built in the browser     │           │ cache (hash → response)   no content logs   │
└──────────────────────────────┘           └────────────────────────────────────────────┘
```
## Repository layout and owners (see OWNERS for the authoritative list)
```
app/                  P1   main.py (router auto-discovery), config.py, guardrails.py, llm/, routers/, schemas/, prompts/
  routers/employer.py, adjustments.py        P3 (+ their schemas/ and prompts/ files)
web/                  P2   index.html (hub), employee/, shared/ (a11y.css, api.js, profile.js, speech.js, ics.js), i18n/ro.employee.json
  web/employer/, i18n/ro.employer.json       P3
data/                 P3   adjustments_ro.json, samples/*.txt
tests/                P1   tests/backend/ (each owner has their own test files), test_a11y_static.py (P2), test_smoke.py (P3)
docs/                 CONTRACTS (P1) · PROJECT/PLAN/evidence/ARCHITECTURE (P3) · plan/ decisions/ per person
scripts/              frozen: check.sh ship.sh sync.sh ownership.py · smoke.sh (P3)
```
Conventions: new router = new file in `app/routers/` exporting `router` (no edits to `main.py`); each task has `app/prompts/<task>.py` exporting `SYSTEM`, `build_user(...)`, `MOCK`; UI strings in per-owner i18n JSON files; employer UI never edits shared CSS (it imports `web/shared/a11y.css` read-only).

## Features
Tracked in docs/TASKS.md (checkboxes are ticked by each owner in their own docs/plan/pN.md; P3 consolidates here at milestones).

## Backlog (not in MVP)
- S1 interview prep · S2 tone suggestion (text-only, uncertain) · S3 employer adjustments overview · job-platform integration · accounts · hosting

## Done log (what / why / how to test)
-
