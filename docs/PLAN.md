# PLAN — shared board (owner: P3). Personal status lives in docs/plan/pN.md.

## Clock (assumed start Thu 22 Oct 12:00 — EDIT if different)
| Milestone | Hours | Clock | Meaning | Status |
|---|---|---|---|---|
| Kickoff done | 0:45 | 12:45 | contract frozen, roles/git set | [x] Complete |
| **M1** skeleton on main | 1:30 | 13:30 | app runs in mock mode, check.sh green on all machines | [x] Tagged `good-1` |
| **M2** features on main (mock) | 8:00 | 20:00 | clickable demo path with mock LLM, check.sh green | [x] Complete (All F1-F6 on main) |
| **M3** real-LLM integration | 14:00 | 02:00 | demo script passes with real LLM bake-off | [ ] In progress |
| **Harden done** | 19:00 | 07:00 | a11y audit, README, fresh-clone OK | [ ] Next |
| **FREEZE** | 19:00 | 07:00 | no new features | [ ] |
| Rehearsal x2 + recording | 19:00–22:00 | 07:00–10:00 | timed runs, backup video | [ ] |
| Submission slack | 22:00–23:00 | 10:00–11:00 | submit early | [ ] |
| Stop coding | 24:00 | 12:00 | hard stop | [ ] |

## Status
- Current phase: **3 INTEGRATE (M2 Complete -> M3 Real LLM Integration)**
- Last green tag on main: `good-1` (M2 ready for `good-2`)
- Blocking issues: None (145 tests passing + end-to-end smoke test passing)
- Next merge point: M3 real-provider demo path check

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

## Features Progress
- [x] **F1: Needs Profile (device-only)** — P2 (shipped in `dd79176`, `web/employee/profile.html`, `web/shared/profile.js`)
- [x] **F2: Clarify Document** — P1 + P2 (shipped in `5fb64cf` + `6ced970`, `/api/simplify` + `web/employee/clarify.html`)
- [x] **F3: Plan from Documents** — P1 (shipped in `b844995`, `/api/plan/extract`), P2 UI in progress
- [x] **F4: Meeting Helper** — P1 (shipped in `8f0e19f`, `/api/meeting/summarize`)
- [x] **F5: Adjustment Request** — P3 (shipped in `11d4a2a`, `/api/adjustments/catalog` & `/draft`)
- [x] **F6: Employer Accessibility Check** — P3 (shipped in `f71403b` + `709f9bc`, `/api/employer/analyze` & `web/employer/index.html`)
- [x] **Safety & Guardrails Layer** — P1 (shipped in `4acebf0`, `app/safety.py`)
- [x] **Smoke Test Suite** — P3 (shipped in `709f9bc`, `scripts/smoke.sh`, `tests/test_smoke.py`)
- [x] **System Architecture Documentation** — P3 (`docs/ARCHITECTURE.md`)
- [x] **README & Presentation Docs** — P3 (`README.md`, `docs/evidence/qa-prep.md`)

## Backlog (not in MVP)
- S1 interview prep · S2 tone suggestion (text-only, uncertain) · S3 employer adjustments overview · job-platform integration · accounts · hosting

## Done log (what / why / how to test)
- T1.1-T1.6 (P1): Shipped FastAPI skeleton, Gemini/DeepSeek providers, simplify, plan, meeting, and safety layer (`app/safety.py`). Verified with pytest.
- T2.1-T2.3 (P2): Shipped accessible shell, tokens (`a11y.css`), profile page, clarify page with quote highlighting and TTS. Verified with static a11y tests.
- T3.1-T3.6 (P3): Shipped adjustments catalog, drafts, employer analyze endpoint with deterministic readability engine, employer audit web UI, and end-to-end smoke test runner. Verified with `./scripts/check.sh`.
