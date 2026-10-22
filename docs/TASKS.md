# TASKS — 3 people, disjoint files (frozen; tick your boxes in docs/plan/pN.md)

**How to use:** pick your role (P1 / P2 / P3), run `git config hackathon.me pN && git switch -c pN/work`, then work top to bottom in YOUR list. One task = one thread = one `./scripts/ship.sh`. Pull often (`./scripts/sync.sh`). Only edit files listed under *Owns* (they match `OWNERS`). Needing a change elsewhere → message the owner in the group chat.
Times are estimates with an agent doing the typing; you do the thinking, verifying and shipping.

## Pick your role
| | **P1 — AI core + backend** | **P2 — Employee experience + accessibility** | **P3 — Employer side + content + evidence + pitch** |
|---|---|---|---|
| Best if you like | APIs, prompts, testing, LLM quirks | UI, accessibility, UX details | product, writing, people, presenting, some backend |
| Owns | `app/` (except P3 files), `tests/`, `requirements.txt`, `.env.example`, `docs/CONTRACTS.md` | `web/` (except `web/employer/`), `tests/web/`, `tests/test_a11y_static.py` | `data/`, `app/routers|schemas|prompts` for employer + adjustments, `web/employer/`, `docs/PROJECT.md PLAN.md evidence/ ARCHITECTURE.md`, `README.md`, `scripts/smoke.sh`, deck |
| Ships first | M1 skeleton (hour 1:30) | shell + a11y.css + fixtures (hour 1:30) | samples + catalog + interviews started (hour 1:30) |

---
## Everyone — kickoff (0:00–0:45)
- [ ] K1 Read PROJECT / CONTRACTS / TASKS together; fix ambiguities; confirm MVP + cut list (use the `kickoff` skill)
- [ ] K2 Each: clone, `git config hackathon.me pN`, `git switch -c pN/work`, venv + `pip install -r requirements.txt`, `cp .env.example .env`, `./scripts/check.sh` runs
- [ ] K3 Agree group-chat rules: announce every ship, announce blockers immediately, nobody edits another's files

---
## P1 — AI core + backend
**T1.1 Skeleton (45 min) → M1.** Owns: `app/main.py app/config.py app/guardrails.py app/llm/** app/schemas/common.py`, `tests/backend/test_llm.py test_guardrails.py test_health.py`
- FastAPI app; **router auto-discovery** (every module in `app/routers/` exporting `router`); serves `web/` at `/`; error envelope + handlers; `GET /api/health`
- `generate_json(task, system, user, schema, mock)` exactly as in CONTRACTS §2 with the `mock` provider and the disk cache; `verify_quotes` in `guardrails.py`; `LLM_PROVIDER=mock` works with no keys; `LOG_CONTENT=false` honored
- Acceptance: `uvicorn app.main:app` runs; `/api/health` OK; `./scripts/check.sh` green with tests for the envelope, mock provider, and `verify_quotes` (fabricated quote dropped). **Ship early; P3 depends on it.**

**T1.2 Real providers + Romanian bake-off (1.5 h).** Owns: `app/llm/providers/**`, `tests/backend/test_providers.py`, `tests/eval/**`
- Gemini and DeepSeek via `httpx` (JSON output, timeout, 1 retry on invalid JSON, mapping to `LLMUnavailable`/`BadLLMOutput`); first check which API key actually works (the student Pro plan may not include API access — DeepSeek tokens are the fallback)
- Run the 3 samples in `data/samples/` through both providers; compare Romanian quality, quote fidelity, latency; pick the default and record it in `docs/decisions/p1.md`
- Acceptance: mock-based tests for error mapping; opt-in live test (`pytest -m live`); documented choice

**T1.3 `/api/simplify` (1.5 h).** Owns: `app/routers/simplify.py app/schemas/simplify.py app/prompts/simplify.py`, `tests/backend/test_simplify.py`
- Prompt (Romanian, plain language, profile-aware, document = untrusted data), schema, guardrail on `source_quote`, input limits
- Acceptance: contract test; fabricated quote dropped + warning; injection sample does not change schema; empty/too-long inputs → proper errors; works on `onboarding_ro.txt` with a real provider

**T1.4 `/api/plan/extract` (1.5 h).** Owns: `app/routers/plan.py app/schemas/plan.py app/prompts/plan.py`, `tests/backend/test_plan.py`
- Tasks + deadlines; ambiguous deadline → `due_iso=null`, `needs_confirmation=true`; relative dates resolved from `today_iso`
- Acceptance: `task_email_ro.txt` yields the vague deadline flagged, not invented; contract + guardrail tests green

**T1.5 `/api/meeting/summarize` (1.5 h).** Owns: `app/routers/meeting.py app/schemas/meeting.py app/prompts/meeting.py`, `tests/backend/test_meeting.py`
- Summary, decisions, action items with `who`, unclear points; text only
- Acceptance: `meeting_transcript_ro.txt` yields ≥ 4 action items with correct `who`; contract + guardrail tests

**T1.6 Safety and robustness layer (1 h).** Owns: `app/safety.py` (new), `tests/backend/test_safety.py`
- Input limits, no content logging (assert logs contain no document text), friendly Romanian errors, prompt-injection regression tests, optional `NO_CACHE=1`
- Acceptance: tests for each rule; `responsible-ai` checklist run on your endpoints

**T1.7 Real-LLM eval + prompt tuning (2 h, M3).** Owns: `tests/eval/**`
- Script runs the samples through real endpoints, prints a pass/fail table (quote fidelity, schema validity, latency). Tune prompts until the demo path is reliable (3 clean runs in a row).

**T1.8 Support / integration (rest of time).** Fix backend bugs reported by P2/P3, keep `check.sh` green on main, help P3 with `scripts/smoke.sh` wiring (they own the file), own the run instructions in `README` content (send text to P3).
**Stretch S2:** `/api/tone/suggest` (text-only, with stated uncertainty) in `app/routers/tone.py` + schema + prompt.

---
## P2 — Employee experience + accessibility
**T2.1 Shell + design tokens + shared modules (1.5 h) → M1.** Owns: `web/index.html web/shared/**` (`a11y.css api.js profile.js speech.js ics.js fixtures/*.json`), `web/i18n/ro.employee.json`
- Hub page with two entries (employee / employer), skip link, landmarks, `lang="ro"`; CSS variables (light, dark, high-contrast), focus styles, text-size/spacing controls, reduced motion; `api.js` with `?mock=1` fixtures shaped exactly like CONTRACTS; `profile.js` (localStorage + "delete my data"); `ics.js`
- Acceptance: `check.sh` green incl. a11y static test; keyboard-only works; P3 can import `a11y.css`

**T2.2 Needs profile + AI notice (1 h).** Owns: `web/employee/profile.html profile.js`
- Reading level, format, text size/contrast, read-aloud default, own-words needs box (max 500 chars, **no diagnosis fields**), transparency notice in plain Romanian
- Acceptance: persists after reload; clear button wipes it; screen-reader pass

**T2.3 Clarify screen (2 h).** Owns: `web/employee/clarify.html clarify.js`
- Paste or upload `.txt` → call `/api/simplify` → summary, ordered steps, terms, questions; "Arată în text" highlights the `source_quote` in the original; read-aloud button; `aria-live` status; error + retry
- Acceptance: works with fixtures (`?mock=1`) and with the real endpoint; keyboard-only flow; 200% zoom OK

**T2.4 Planner (2 h).** Owns: `web/employee/plan.html plan.js`
- Extract tasks via `/api/plan/extract`; list with due dates; items with `needs_confirmation` show a date picker and a clear flag; check off, edit title; **download `.ics`** (valid file; opens in a calendar); in-memory + localStorage only
- Acceptance: ICS imported into a real calendar app once; ambiguous deadline never shown as a real date

**T2.5 Meeting helper (2 h).** Owns: `web/employee/meeting.html meeting.js`
- Live transcript with Web Speech API (`ro-RO`) when supported; always a paste/typing fallback; summarize via `/api/meeting/summarize`; add action items to the planner; text only
- Acceptance: paste path works end to end; live path degrades gracefully when unsupported (explain why)

**T2.6 Adjustments screen (1 h).** Owns: `web/employee/adjustments.html adjustments.js`
- Load catalog (P3) → select needs (checkbox group) → draft via `/api/adjustments/draft` → copy / `mailto:` / download; disclaimer visible; no diagnosis anywhere
- Acceptance: works with fixtures first; keyboard + screen-reader pass

**T2.7 Accessibility audit and fixes (2 h, ongoing, M3 + harden).** Owns: `tests/test_a11y_static.py tests/web/**`
- Keyboard-only walkthrough, screen reader pass (Orca/NVDA), 200% zoom, 320 px, contrast, reduced motion; axe if a browser is available; fix list for your pages and a list for P3's employer pages (send to P3). Write the accessibility statement text (send to P3 for README/deck: only what you tested).

**T2.8 Simple mode + reading comfort (1 h, can fold into T2.1).** Owns: `web/shared/a11y.css` (same file)
- One toggle: larger text, more spacing, fewer UI elements; line-focus option; applies across employee pages.

**T2.9 Demo polish (harden).** Make the demo path smooth: loading states, empty states, sample-document buttons ("Încearcă cu un exemplu" loading from `data/samples` copies in `web/shared/samples/` — P3 sends final text).
**Stretch S1 (UI part):** interview-prep screen.

---
## P3 — Employer side + content + evidence + pitch
**T3.1 Validation interviews (start hour 0:30, continuous).** Owns: `docs/evidence/**`
- Use the `validation-evidence` skill. Target ≥ 5–6 real conversations at the Expo (people with disabilities, NGO/association staff, HR). P1 and P2 each do 1–2 when they are waiting on something. **Real feedback only, never invented.** Keep `docs/evidence/interviews.md` and `summary.md` current; update `docs/PROJECT.md` with what you learn (e.g. kill or add features).

**T3.2 Curated adjustments catalog + samples (1.5 h) → M1.** Owns: `data/adjustments_ro.json`, `data/samples/**`
- ≥ 12 items matching CONTRACTS ids, each with `applies_to`, plain-language description, example request, and a `source` (verify any legal/rights statement with the `scout` agent against official Romanian sources; if you cannot verify it, label it "bună practică generală", do not cite law). Samples are provided (`onboarding_ro.txt`, `task_email_ro.txt`, `meeting_transcript_ro.txt`): review/extend; add one prompt-injection sample.
- Acceptance: JSON validates against a test; no diagnosis words anywhere in the catalog

**T3.3 `/api/adjustments/catalog` + `/draft` (1.5 h).** Owns: `app/routers/adjustments.py app/schemas/adjustments.py app/prompts/adjustments.py`, `tests/backend/test_adjustments.py`
- Catalog served from the JSON; draft accepts only catalog ids; deny-list test for diagnosis words; Romanian, polite, short
- Acceptance: contract tests; unknown id → `bad_request`; mock + real-provider check

**T3.4 `/api/employer/analyze` (2 h).** Owns: `app/routers/employer.py app/schemas/employer.py app/prompts/employer.py`, `tests/backend/test_employer.py`
- Readability stats **in code** (sentence count, average sentence words, long sentences, simple score), issues with quotes via LLM + `verify_quotes`, easy-read rewrite, checklist mapped to catalog ids; scores documents, never people
- Acceptance: deterministic stats unit-tested; guardrail test; works on `onboarding_ro.txt`

**T3.5 Employer page (2 h).** Owns: `web/employer/**`, `web/i18n/ro.employer.json`
- Paste/upload → results (stats, issues with quotes, easy-read text with copy/download, checklist); imports `web/shared/a11y.css` read-only; follows the `a11y-by-design` skill; passes `tests/test_a11y_static.py`
- Acceptance: keyboard-only flow; works with `?mock=1` first

**T3.6 Smoke test (1 h) → before M2.** Owns: `scripts/smoke.sh`, `tests/test_smoke.py`
- Starts the app in mock mode, calls every endpoint with the samples, checks envelope/shape, fetches `/` and each HTML page; exits non-zero on any failure (copy from `scripts/smoke.sh.example` if present)

**T3.7 Docs for judges (2 h, harden).** Owns: `README.md docs/ARCHITECTURE.md docs/evidence/qa-prep.md`
- README (pitch, screenshots, run, test, architecture, accessibility + responsible-AI statements, limits), architecture diagram, Q&A prep (why not ChatGPT, privacy, hallucinations, legal, business model, scaling), next steps

**T3.8 Pitch and demo (freeze → end, 3 h).** Owns: `docs/evidence/**` (+ deck files outside git if large)
- Deck (≤ 8 slides for 6 min), demo script, backup screen recording, two timed rehearsals with the whole team, submission checklist (repo link, description, validation, accessibility, deck, next steps)
- Also: tag `good-1` at M1, `good-2` at M2, `good-3` at M3, `good-freeze`, `submission` (run `git tag … && git push origin --tags`).
**Stretch S1 (backend part):** interview-prep content/endpoint; S3 employer adjustments overview.

---
## Cross-person dependencies (announce in the group chat when each is shipped)
| Needed by | Needs | From | By |
|---|---|---|---|
| P3 T3.3, T3.4 | `generate_json`, `verify_quotes`, router auto-discovery, `schemas/common.py` | P1 T1.1 | M1 (1:30) |
| P3 T3.5 | `web/shared/a11y.css` | P2 T2.1 | M1 (1:30) |
| P2 T2.3–T2.5 | endpoints (use `?mock=1` fixtures until then) | P1 T1.3–T1.5 | 4:00–6:00 |
| P2 T2.6 | catalog + draft endpoints | P3 T3.3 | 4:00 |
| P3 T3.6 | all endpoints + pages | P1, P2, P3 | M2 (8:00) |
| P1 T1.2 | `data/samples/*.txt` | P3 T3.2 (provided in repo) | now |
| P3 T3.7 | accessibility statement text | P2 T2.7 | harden |
| P3 T3.7 | run/limits text | P1 T1.8 | harden |

## Integration moments (everyone, ~20 min each)
- **M1 (1:30):** sync, `check.sh` green on all machines, tag `good-1`.
- **M2 (8:00):** run the whole demo path in mock mode together; list bugs by owner.
- **M3 (14:00):** same with the real LLM; 3 clean runs in a row; tag `good-3`.
- **FREEZE (19:00):** no features. Everyone: bug fixes in own files, then rehearsals.

## Cut list (in order, decided by the team in the room)
Stretch → live speech (keep paste) → easy-read rewrite (keep stats + issues) → upload (keep paste) → polish of adjustments → meeting helper. **Never cut:** F2, F3, F5, F6 core, accessibility, privacy/guardrail demo, validation evidence.
