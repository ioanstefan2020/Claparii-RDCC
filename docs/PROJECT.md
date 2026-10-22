# PROJECT — AccessABILITY Hackathon 2026 (owner: P3; changes agreed in the room)

## Event
- **Challenge:** First Job, Full Potential: AI for an Inclusive Start at Work (22–23 Oct 2026, Biblioteca POLITEHNICA București, 24h sprint, teams of 3–4)
- **Stop coding:** 23 Oct 12:00. Deliverables: working prototype on GitHub (history reviewed), project description, user need + validation, accessibility explanation, pitch deck + live/recorded demo, next steps. **Pitch: 6 min + Q&A.**
- **Team:** P1 — AI core + backend · P2 — employee experience + accessibility · P3 — employer side + content + evidence + pitch. (Names/strengths: fill in)
- **Judging (13 criteria, 1–5; extra weight on problem relevance and accessibility):** see mapping table below.

## Problem
People with disabilities face barriers from the job search to the first months at work: dense onboarding documents, vague task emails, fast meetings, unwritten rules, and hesitation to ask for adjustments (many do not want to disclose). Employers/HR often lack tools and know-how to make material accessible and to know which adjustments to offer. In Romania, easy-to-use Romanian-language support for this is scarce. *(Claims to validate in interviews: do not state numbers we have not verified.)*

## Solution (working title: **PrimaZi**)
A Romanian-language, privacy-first assistant that **adapts the workplace to the person**, with one side for employees/candidates and one for employers/HR, centred on **clarity and planning**:
- The employee describes their needs once, in their own words (stored only on their device), pastes or uploads a work document, email or meeting transcript, and gets back **what is asked, step by step, by when**, in plain Romanian shaped to their needs, readable aloud, and exportable to their calendar.
- The employee can generate a **request for workplace adjustments without disclosing any diagnosis**.
- The employer pastes an onboarding document or job ad and gets an **accessibility check, an easy-to-read version, and an adjustment checklist**.

## MVP (must work in the demo; each is an observable behavior)
| # | Feature | Owner | Observable behavior |
|---|---|---|---|
| F1 | Needs profile (device-only) | P2 | User sets reading level, steps format, text size/contrast, read-aloud, in own words; nothing sent to server except per request |
| F2 | Clarify a document | P1 (API) + P2 (UI) | Paste onboarding text → plain-Romanian summary, numbered steps, explained terms, questions to ask; each item can show its source quote |
| F3 | Plan from documents | P1 + P2 | Tasks with deadlines extracted (ambiguous ones flagged, never invented) → planner → download `.ics` |
| F4 | Meeting helper | P1 + P2 | Live Romanian transcript (browser speech) or pasted transcript → summary, decisions, action items → added to planner. Text only, no emotion inference |
| F5 | Adjustment request | P3 (API) + P2 (UI) | Pick needs from a curated catalog → drafted request to HR with no diagnosis |
| F6 | Employer accessibility check | P3 | Paste onboarding doc/job ad → readability stats (computed in code), jargon/issues with quotes, easy-read version, adjustment checklist |
| X | Cross-cutting accessibility | P2 | Keyboard-only, screen-reader tested, contrast modes, text zoom, read-aloud, simple mode |

**Stretch (only after M3):** S1 first-interview preparation (questions + which adjustments to request), S2 tone suggestion for messages (text-only, explicit uncertainty), S3 employer "adjustments overview" page.
**Cut order if time runs out:** S-items → live speech (keep paste) → F6 easy-read version (keep stats + issues) → F5 polish → F4.
**Non-goals:** a browser extension / "fix any site", sign-language recognition, haptics, motor/atypical-speech models, emotion detection, accounts/login, a database, job-board integration (roadmap only).

## Why this and not "just ChatGPT" / existing tools (be ready for this question)
Existing tools are strong at generic reformatting (e.g. browser reading tools), image description, English captions. Gaps we target (to confirm with interviews): **Romanian**, **workplace context** (onboarding docs, task emails, adjustments), **planning output** (deadlines → calendar), **privacy** (no disclosure, no storage), and an **employer side**. We do not claim to beat polished general tools at reformatting.

## Jury criteria → our answer
| Criterion | Our answer | Evidence/artefact |
|---|---|---|
| Impact on people with disabilities | Autonomy at work: understand tasks, plan, ask for adjustments safely | Interviews, before/after demo |
| Theme adherence | First job, onboarding, adjustments, employer side | Demo story |
| Accessibility & inclusive design | WCAG 2.2 AA targets, 4 need-groups served | a11y statement, tests, live keyboard demo |
| UX | One primary action per screen, predictable layout, plain language | Demo |
| Scalability & sustainability | B2B licence for employers/HR; NGO/university/public-employment partners; grants | Business slide (draft below) |
| Feasibility & implementation | Boring stack, tested, runs offline in mock mode | Repo, README |
| Prototype functionality | F1–F6 working end to end | Smoke test + demo |
| Performance & efficiency | Caching, small inputs, fast mock fallback | Notes in README |
| Architectural complexity | Provider-agnostic LLM layer, guardrails, contract-first, parallel modules | `docs/ARCHITECTURE.md` |
| Innovation & originality | Verified-source extraction, disclosure-free adjustment requests, two-sided centralisation, Romanian focus | Pitch |
| Meaningful use of AI | Adapts content to the user, extracts structured tasks, uses calendar/speech tools, personalises | Demo |
| AI ethics, privacy & safety | Device-only profile, no storage, source-quote verification, no emotion/diagnosis inference, curated legal info | Responsible-AI statement + live guardrail demo |
| Pitch / demo / Q&A | 6-min script below, rehearsed twice, backup recording | Deck |

## Stack (default; change at kickoff only if the team unanimously prefers)
- Backend: Python 3.11+, FastAPI, Pydantic v2, httpx. LLM provider behind one interface (`mock` | `gemini` | `deepseek`), JSON output, caching.
- Frontend: semantic HTML + vanilla ES modules + one CSS token file, served by FastAPI from `web/`. No build step, no CDN.
- Speech: browser Web Speech API (`ro-RO`) for input, `speechSynthesis` for read-aloud. Calendar: `.ics` generated client-side.
- Run: `uvicorn app.main:app --reload` → http://localhost:8000 · Test: `./scripts/check.sh`

## Top risks and fallbacks
| Risk | Fallback |
|---|---|
| Romanian LLM quality / API key or quota problems | Bake-off in T1.2; switch provider by env var; cache; `mock` mode with realistic canned outputs for the demo |
| Wi-Fi dies during demo | Cached/mock mode, pre-recorded demo video |
| Web Speech `ro-RO` unavailable/flaky | Paste-transcript path is the primary demo; live speech is a bonus |
| Romanian TTS voice missing on the demo laptop | Check the demo machine early; say honestly; keep text UI complete |
| Legal/rights content wrong | Only curated, sourced catalog; "informativ, nu consultanță juridică" |
| Validation thin | Interviews start in hour 1; summarise honestly, plan a pilot |
| Merge conflicts | OWNERS + ship.sh |

## Demo story (target 3 min of the 6-minute pitch) — fictional persona "Ana", clearly labelled illustrative
1. **Hook (30 s):** one real quote from an interview + the problem in one sentence.
2. **Ana's first day:** she opens the app, sets her needs in her own words (device-only). Pastes the onboarding document → plain steps + deadlines + terms explained; "Arată în text" shows the verbatim source; read aloud; **keyboard-only** moment.
3. **Plan:** deadlines → planner → `.ics` into calendar. Task email with an ambiguous deadline → app flags it instead of guessing (**guardrail moment**).
4. **Meeting:** paste/live transcript → summary + action items assigned.
5. **Adjustments:** picks "written instructions, extra time" → request to HR drafted, no diagnosis.
6. **Employer side:** HR pastes the same onboarding document → accessibility report + easy-read version + checklist.
## Pitch outline (6:00)
0:00 problem + quote (validation) · 0:45 live demo (3:00) · 3:45 accessibility + responsible AI (45 s) · 4:30 business model + go-to-market (45 s) · 5:15 roadmap + ask (45 s). Q&A prep list in `docs/evidence/qa-prep.md`.

## Business model / go-to-market (DRAFT — validate with HR/NGO interviews)
Employers/HR teams (B2B licence per employee/seat or per organisation), universities and career centres, NGOs and public employment services (partnerships/grants, EU/national funding), integration with HR/onboarding platforms. Free for individual employees. Next steps: pilot with one NGO + one employer, Romanian-language evaluation set, accessibility audit with disabled testers, hosting with EU data residency, DPIA.

## Responsible-AI statement (draft for README/deck)
Device-only profile · nothing stored server-side · no diagnosis or emotion inference · every extracted fact verified against the source · AI output labelled · curated legal info · employer analysis scores documents, never people · limits stated honestly.

## Accessibility statement (draft; claim only what was tested)
Targets WCAG 2.2 AA. Serves cognitive (plain language, steps, simple mode), visual (screen reader, contrast, zoom, read-aloud), hearing (text transcripts, captions of speech), and motor (keyboard-only, voice input, large targets) needs. Tested with: automated HTML checks on every commit, keyboard-only walkthrough, screen reader pass (record which one). Known limits: _fill in honestly_.
