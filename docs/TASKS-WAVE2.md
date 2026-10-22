# TASKS-WAVE2 — finish strong: reliability, many more accessibility settings, natural audio, audio-file input, smarter prompts, Gemini-style frontend

Supersedes the open parts of `docs/TASKS.md` and the in-repo `NEXT_WAVE_PROPOSAL.md` (everything in it is covered below). Time is relative to **now = M2**. Freeze stays at hour 19 of the sprint.

## 0. Read this first
**Goal:** a product that really helps a person get through a first job: understand any work text, plan it, hear it in a natural voice, turn audio into text, and shape the whole site to their needs (blind, low vision, deaf/hard of hearing, motor, ADHD-style attention needs, cognitive/reading needs) — with settings that never reset by surprise.
**New docs (read in this order, 15 min):** `SETTINGS-SPEC.md` (all variables) → `DESIGN.md` (look + measured contrast) → `CONTRACTS-WAVE2.md` (new endpoints) → `PROMPT-SPEC.md` (prompts) → `RESEARCH-WAVE2.md` (what the evidence says + idea bank).
**Priority tags:** **[MUST]** done by C2 (≈ +7h) · **[SHOULD]** done by freeze · **[COULD]** only if ahead. Cut from the bottom of the list, never the top.

## 1. Ownership changes (applied by `scripts/apply-wave2.sh`, announced in the group chat)
| Who | Owns now |
|---|---|
| **P1** | `app/` (providers, prompts, guardrails, simplify/plan/meeting/transform/annotate/extract routers), `tests/backend/` (own files), `tests/eval/`, `requirements.txt`, `.env.example`, `Dockerfile`, `README.md`, `docs/ARCHITECTURE.md`, `docs/CONTRACTS*.md`, `docs/PROMPT-SPEC.md` |
| **P2** | `web/a11y/` + `web/shared/` (settings engine, TTS, highlighter, layouts, themes CSS, boot), `app/routers/profile*.py`, `app/routers/transcribe.py`, `app/routers/tts.py`, `app/tts/`, `tests/web/`, `tests/test_a11y_static.py`, `docs/SETTINGS-SPEC.md`, `docs/settings.schema.json`, `docs/evidence/` |
| **P3** | **all other `web/`** (shell, pages, design system, library, planner UI, audio page, settings studio, employer area, fonts), `data/`, `docs/DESIGN.md`, `docs/PROJECT.md`, `docs/PLAN.md`, deck/demo |
Pages can be handed over file-by-file if someone is overloaded: agree in the chat, edit `OWNERS` with `FORCE=1`, announce. Never edit the same file in parallel.

## 2. The first 20 minutes (everyone)
1. `./scripts/sync.sh`, then apply the Wave 2 kit (see message), then `./scripts/check.sh`.
2. Each person pastes **Prompt W0 (state audit)** from `PROMPTS-WAVE2.md` and reads the answer: which parts of this plan already exist in the code (e.g. Bionic reading, ruler, `recommend-adaptations`, circuit breaker, reminders) so nobody rebuilds them.
3. Agree the **settings schema** (`docs/settings.schema.json`) and `web/a11y/*.js` function names now (P2 posts the stub files within 45 minutes so P3 can code against them).

## 3. Milestones
| When | Checkpoint | Must be true |
|---|---|---|
| +3h | **C1** foundations | Provider chain works + `/api/llm/status`; no 422 from any profile; settings engine persists across reload and applies before paint; new shell renders with themes; transcribe skeleton returns text for a short file |
| +7h | **C2** features | `annotate`, `transform`, `transcribe`, natural TTS, highlights, layouts all work in the new UI on the demo path; real LLM 3 clean runs; cutover to new frontend decided |
| +10h | **Freeze (hour 19)** | bug fixes only; QA matrix done; fresh-clone test; deck + demo rehearsed twice |

---
# P1 — Backend reliability, prompts, text intelligence

**B1 [MUST] Provider reliability (fixes "Groq sometimes does nothing") — 2h.** Owns: `app/llm/**`, `app/config.py`, `tests/backend/test_llm*.py`
- `LLM_PROVIDER_CHAIN=groq,deepseek,ollama,mock` honored exactly; at startup log one line per provider (configured? key present? model?); if `LLM_PROVIDER=groq` but no key → clear warning + skip, never silent
- Per-provider model/timeouts/retries; handle 429 with `Retry-After` backoff; circuit breaker per provider with reason; JSON mode flags per provider (Groq needs "JSON" in the prompt)
- `GET /api/llm/status` (CONTRACTS-WAVE2); `meta.provider_chain_tried`, `meta.latency_ms`; per-task routing `LLM_ROUTE_<TASK>`
- Acceptance: tests with fake providers: first fails → second used; all fail → mock + warning; missing key → skipped with reason; status endpoint shows circuit state

**B2 [MUST] Tolerant input and soft output (fixes the "only accepts a certain format" class) — 1.5h.** Owns: `app/schemas/common.py`, `app/schemas/profile_norm.py` (new), changes to `app/schemas/*` only where you own them
- `normalize_profile(dict) -> Profile` with alias maps (e.g. `detailed→standard`, `paragraphs→short_paragraphs`, any unknown → default + warning); all request models `extra="ignore"`; **no HTTP 422 for profile problems, ever**
- Tolerant JSON from LLMs: strip code fences, extract the first JSON object, fix trailing commas, coerce enums/numbers, clamp ranges, drop invalid items with a warning; one `repair` retry; only then `bad_llm_output`
- Accept text as JSON or form; trim/normalise whitespace, Unicode (diacritics ş/ș, ţ/ț variants → comma-below), CRLF
- Acceptance: fuzz test of 100 random profile/enums/garbage never yields 422/500; model output with fences/trailing commas parses; Romanian cedilla vs comma diacritics handled in quote verification

**B3 [MUST] Prompt architecture v2 — 3h.** Owns: `app/prompts/base.py simplify.py plan.py meeting.py transform.py annotate.py repair.py versions.py`, `tests/backend/test_prompts*.py`
- Implement `PROMPT-SPEC.md` §0–§4: base system, easy-read rules, adaptation matrix, 2 Romanian few-shots per task, document delimiters, versions in `meta.prompt_version`
- Acceptance: golden set runs (B7) show schema-valid ≥ 95% and quote-valid ≥ 90% before guardrail on the primary provider; injection sample passes; ambiguous deadline never invented

**B4 [MUST] `/api/annotate` — highlights now, tone notes next — 3h.** Owns: `app/routers/annotate.py app/schemas/annotate.py app/annotate/**` (deterministic extractors), `tests/backend/test_annotate.py`
- Deterministic layer first (no LLM): Romanian dates/weekdays/months, times, `până la/până în`, amounts (lei/RON/EUR/%), emails/phones, IDs like `F-12` → offsets verified `text[start:end]`
- Semantic layer (LLM, fast model): `action`, `person`, `warning`, `term` + `glossary`; density cap by `highlight_mode`
- **[SHOULD]** Tone layer per `PROMPT-SPEC.md` §5 (`indirect_request`, `figurative`, `urgency`, tentative `joke|irony`), conservative, evidence-quoted, off unless requested; needs the 40-line labelled set (team writes it together, 30 min)
- Acceptance: deterministic layer unit-tested on samples (including diacritic-less text); offsets always valid; tone layer returns nothing on neutral lines; no `high` confidence; precision reported on the labelled set

**B5 [MUST] `/api/transform` — 1.5h.** Owns: `app/routers/transform.py app/schemas/transform.py`, `tests/backend/test_transform.py`
- Modes `bullets|shorter|tldr|easy_read|steps|questions|glossary`; keeps deadlines/names/amounts; `target_pct` and `max_items` respected
- Acceptance: every date/amount/name in the input appears in `shorter`/`bullets` output on the samples (test); contract tests; works on transcript text from `/api/transcribe`

**B6 [SHOULD] `/api/extract-text` (PDF/DOCX/TXT/HTML) — 1.5h.** Owns: `app/routers/extract.py app/schemas/extract.py app/extract/**`
- In-memory parsing (pypdf, python-docx), size/page limits, `needs_ocr` flag, temp files removed in `finally`, no content logged
- Acceptance: sample PDF + DOCX parsed; 11 MB file rejected with friendly error; corrupt file handled

**B7 [MUST→SHOULD] Eval harness and golden set — 1.5h.** Owns: `tests/eval/**`, `data/eval/**` (ask P3 for the dir or use `tests/eval/data/`)
- 15 Romanian docs (emails, onboarding, job ads, meeting notes; diacritics/no diacritics/typos/long/short/injection/mixed RO-EN); scorecard per `PROMPT-SPEC.md` §6; table written to `docs/evidence/eval.md` by P2 (they own the dir) from your output
- Acceptance: one command prints the table for any provider; numbers are real

**B8 [SHOULD] Latency and efficiency — 2h.** Cache by hash with TTL, parallelise independent calls (e.g. annotate layers), trim prompts, timeouts, optional SSE progress events (`event: status`) for long jobs, warm-up on startup. Acceptance: p50 simplify on the sample < 6s on primary provider (measure and report; no promises)

**B9 [SHOULD] Security, privacy, run-anywhere — 1.5h + docs 1h.** Owns: `app/safety.py`, `Dockerfile`, `README.md`, `docs/ARCHITECTURE.md`
- Rate limit per IP, security headers, upload limits, `needs_notes` scrubber (diagnosis words) before any LLM call, test that logs contain no document text, `Dockerfile` + one-command run; README + architecture diagram (accurate to the code)
- Acceptance: tests for each rule; fresh clone runs with `docker run` or `uvicorn`

**B10 [COULD] `/api/describe-image`** (vision provider) — 2h, for blind/low-vision users (photo of a printed page, chart).

---
# P2 — Accessibility engine, natural audio, audio-to-text

**A1 [MUST] Settings engine v2 — 3h.** Owns: `web/a11y/settings.js boot.js presets.js`, `docs/settings.schema.json`, `tests/web/`
- Implement `SETTINGS-SPEC.md`: defaults, validation/clamping, versioned localStorage (`primazi.settings.v2`) + migration from the old keys (welcome questionnaire, `getStoredProfile`), `boot.js` applies before first paint, cross-tab sync, export/import JSON, `resetAll()` only on explicit call, `onChange`
- **Post stubs with the final function names within 45 min** so P3 can integrate
- Acceptance: `node --test` tests (wrapped by a pytest test so `check.sh` runs them): persistence across reload simulation, migration, clamping, preset application, reset only explicit

**A2 [MUST] Profile → settings v2 (extend `recommend-adaptations`) — 2h.** Owns: `app/routers/profile*.py`, matching schemas/prompts/tests
- Returns a settings diff + a reason per change using the full key set; values clamped to the schema; diagnosis words scrubbed and never echoed; heuristic fallback (keywords → settings) when the LLM is down; shows progress state in the response (`meta.provider`)
- Acceptance: "obosesc la lumină tare și uit instrucțiunile verbale" → warm theme/dim, steps format, written-instructions adaptation, with reasons; garbage input → safe defaults, no 422

**A3 [MUST] Natural-sounding TTS (client) — 3h.** Owns: `web/a11y/tts.js tts-normalize-ro.js`
- Voice picker: prefer Romanian voices whose name contains "Natural"/"Online" (Edge), then other ro-RO; if none, say so honestly in the UI and fall back to server TTS (A8)
- Speak **sentence by sentence** with configurable pause, rate 0.5–2, pitch, volume; follow-along highlight (sentence, optional word via boundary events); pause/resume/stop/prev/next; Esc and a global "Oprește" always work; auto-read option; works with highlights/annotations text
- `tts-normalize-ro`: dates/times/amounts/`F-12`/abbreviations/ordinals → spoken Romanian (pure function, unit-tested)
- Acceptance: unit tests for normalization (≥ 20 cases); manual check on Edge + Chrome; stop works instantly; keeps reading position after pause

**A4 [MUST] `/api/transcribe` audio → text + captions — 2.5h.** Owns: `app/routers/transcribe.py app/schemas/transcribe.py app/audio/**`, `tests/backend/test_transcribe.py`
- Per `CONTRACTS-WAVE2.md`: Groq Whisper (`whisper-large-v3-turbo`, `language=ro`, `verbose_json`), ffmpeg shrink to 16 kHz mono + chunking with overlap over 25 MB, SRT/VTT built from segments, local faster-whisper fallback if installed, friendly errors (format, size, 429 queue), temp files deleted, nothing stored
- Text only: no emotion/speaker-trait inference
- Acceptance: a 30–60 s Romanian sample returns text + valid SRT/VTT; mock mode returns canned transcript; too-large/unsupported file rejected kindly

**A5 [MUST] Themes, typography, spacing (CSS) — 2h.** Owns: `web/a11y/themes.css typography.css`, `tests/web/test_contrast.py`
- Implement every `data-*`/CSS variable in SETTINGS-SPEC §1 (7 themes, scale slider 70–200%, spacing, measure, weight, focus ring, cursor, dim, flat, cvd cues) using `web/fonts/fonts.css`; **test_contrast.py** computes ratios for each token pair per theme and fails under the targets in `DESIGN.md`
- Acceptance: contrast test green (soft text ≥ 7:1, controls ≥ 4.5:1 here, focus ≥ 3:1); 200% zoom and 320 px reflow screenshot check

**A6 [MUST] Highlight and annotation renderer — 2.5h.** Owns: `web/a11y/highlight.js ruler.js glossary.js`
- `renderRich(el, text, {highlights, annotations, glossary})`: builds safe DOM (no `innerHTML` with user text), category styles per spec with non-colour cues, density cap, legend, "Fără evidențieri" toggle; tone notes inline in parentheses, muted, with evidence tooltip; glossary hover/tap/focus; client fallback uses the deterministic rules when the server gives none; reading ruler/band; focus-paragraph dimming; bionic kept optional
- Acceptance: unit tests (overlapping spans, diacritics, XSS strings); screen-reader reads highlights without noise (use `aria-hidden` on decorative icons, `<mark>` where meaningful)

**A7 [SHOULD→MUST for the ADHD story] Layout and focus modes — 2h.** Owns: `web/a11y/layouts.js layouts.css`
- `mountResults(container, items, {layout, focus})` for overview/guided/card, focus levels 0–3 behaviour from SETTINGS-SPEC §3 (progress "Pasul 2 din 6", Prev/Next, Esc exits, break reminder visual), no layout jumps, announcements via live region
- Acceptance: keyboard-only complete flow in each mode; screen-reader announces step changes once

**A8 [SHOULD] Server TTS fallback (Piper) — 2h.** Owns: `app/routers/tts.py app/tts/**`
- Piper `ro_RO-mihai-medium` (CPU, offline) behind `/api/tts` after `tts_normalize_ro` (Python mirror of A3 rules, shared test cases); cache by hash; optional cloud voice via env key
- Acceptance: returns playable WAV < 3s for a sentence; model download documented; degrades to "no server voice" message if Piper isn't installed

**A9 [SHOULD] Motor and input options — 1.5h.** Owns: `web/a11y/input.js`
- Target size/gap variables, keyboard shortcuts with `?` help (no single-key by default), optional Romanian voice commands (Web Speech), no hover-only/drag-only, undo toast for destructive actions
- Acceptance: whole demo path with keyboard only; shortcuts listed; voice commands off by default

**A10 [MUST, continuous] Accessibility QA matrix — 2h + ongoing.** Owns: `tests/web/**`, `docs/evidence/a11y-audit.md`
- For each user group run the checklist and record real results: **keyboard-only**, **screen reader** (Orca/NVDA/VoiceOver), **200% zoom + 320 px**, **forced-colors/high contrast**, **reduced motion**, **colour-blind simulation**, **captions/transcript path for deaf users**, **motor (no mouse)**, **cognitive (focus levels, plain language) with a non-technical tester**. Extend `test_a11y_static.py` for new pages; run axe if a browser is available
- Acceptance: audit doc with pass/fail per item and the fixes made; list of known limits (honest)

**A11 [SHOULD] Evidence and user sessions — 1.5h.** Owns: `docs/evidence/**`. Run the 15-minute sessions from `RESEARCH-WAVE2.md` §4 with P3's help; keep `interviews.md`, `summary.md`, `eval.md` current (real data only).

---
# P3 — The new frontend (Gemini-style, inclusive) + pitch

**F1 [MUST] Design system + app shell — 3h.** Owns: `web/app/**` (new), `web/fonts/**`, `docs/DESIGN.md`
- Implement `DESIGN.md`: tokens read the `data-*`/CSS variables from `SETTINGS-SPEC.md` (P2's `themes.css` supplies theme values; you supply layout/components), sidebar (collapsible; drawer on mobile; state remembered), top bar with the 3 labelled controls (Contrast, Text, Audio-Stop) wired to the engine, skip link, landmarks, `<head>` includes `/a11y/boot.js` and `fonts.css`
- Pages are separate `.html` files that include the shell as a small web component (`<app-shell>`) so each page stays statically testable
- Acceptance: `check.sh` green incl. a11y static test; keyboard + 200% zoom + 320 px OK; themes switch live and persist after reload

**F2 [MUST] Home + composer + results host — 2h.** Owns: `web/app/index.html composer.js results.js`
- Greeting + 4 big action cards + composer (paste, file, voice, example); results rendered through `mountResults` (A7) and `renderRich` (A6); summary first; "Arată în text"
- Acceptance: whole clarify flow on real API and on `?mock=1`; no layout jump when results arrive; status in `aria-live`

**F3 [MUST] Result action bar — 1.5h.** Owns: `web/app/actions.js`
- Buttons on every result: **Ascultă** (A3), **Mai scurt**, **Puncte**, **Pe pași**, **Explică simplu**, **Salvează**, **Adaugă în plan** → `/api/transform`, `/api/annotate`; tone notes toggle; clear loading/error states
- Acceptance: each button works with the real endpoints; every button has a text label and ≥ target size

**F4 [MUST] Accessibility Studio + onboarding — 3h.** Owns: `web/app/settings.html studio.js welcome.html`
- Page for **all** variables in `SETTINGS-SPEC.md`, grouped (Aspect, Citire, Concentrare, Audio, Auz, Mișcare/control, Cititor de ecran, Limbă), search box, presets with one-line explanations, live preview (sample paragraph + sample result), "Resetează" with inline confirm, export/import, "Șterge toate datele"
- Onboarding: a few friendly chips + "spune în cuvintele tale" → `recommend-adaptations` → shows proposed changes with reasons → user accepts/edits → saved (never applied silently); skippable; shows privacy note
- Acceptance: change anything → applied instantly, survives reload, new tab, and browser restart; preset + manual tweak both persist

**F5 [MUST] Audio → text page — 2.5h.** Owns: `web/app/audio.html audio.js`
- Upload (drag-free button + keyboard) or record; progress status; transcript with clickable timestamps; download `.srt`/`.vtt`/`.txt`; buttons **Rezumat**, **Puncte**, **Mai scurt**, **Ce am de făcut** (→ meeting summarize + planner); visual alert when done; privacy note ("fișierul nu este salvat")
- Acceptance: 30–60 s sample end to end; works with keyboard + screen reader; error messages for wrong format/size

**F6 [SHOULD] Library (history) — 2h.** Owns: `web/app/library.html library.js`
- Local only, **opt-in** per item ("Salvează în bibliotecă pe acest dispozitiv"), results by default (original text only if ticked), search, grouped by date, open/delete with inline confirm, "Șterge tot", storage size shown, optional 30-day expiry; sidebar shows recent items
- Acceptance: persists; delete really deletes; nothing leaves the device (check network tab)

**F7 [SHOULD] Planner v2 — 2.5h.** Owns: `web/app/plan.html plan.js`
- Sub-step checklists with local persistence, countdown cards ("Mai sunt 2 zile"), urgency sort, "Împarte în pași mici" (transform steps), visual + vibration reminders, ICS + Google link (exists), break reminder hooks
- Acceptance: ambiguous deadlines still need confirmation; reminders fire visually; keyboard flow

**F8 [SHOULD] Employer area in the new shell — 1.5h.** Owns: `web/employer/**` — same look, readability stats + issues + easy-read version, role switch in sidebar.

**F9 [MUST] Cutover, mobile and visual QA — 2h.** Switch `/` to the new home, remove or redirect old pages (coordinate deletion of `web/employee/*` with P2's `web/shared/*`), mobile pass at 320/768/1280, 3 themes, screenshots for the deck. Acceptance: no dead links; smoke test updated; old routes redirect.

**F10 [MUST, last 3h] Pitch and demo.** Owns: `docs/DEMO.md`, deck. Update demo story for Wave 2 (see §5), backup recording with Edge natural voice, 2 timed rehearsals, submission checklist. Use only measured numbers (B7) and real quotes (A11).

---
## 4. Dependencies (post in the chat when shipped)
| Needed by | Needs | From | By |
|---|---|---|---|
| P3 F1–F4 | settings stubs + CSS variable names | P2 A1/A5 | +45 min |
| P3 F3 | `/api/transform`, `/api/annotate` (deterministic first) | P1 B4/B5 | +4h |
| P3 F5 | `/api/transcribe` | P2 A4 | +3h |
| P3 F4 | `recommend-adaptations` v2 | P2 A2 | +4h |
| P2 A6 | highlight offsets contract | P1 B4 | stub at +1h |
| P2 A3/A8 | normalisation test cases shared | P2 | +3h |
| everyone | provider chain stable | P1 B1 | +2h |

## 5. Demo story v2 (target for the 6-minute pitch)
1. Quote from a real interview + problem. 2. Ana opens the app; **settings were derived from her own words, stay after reload**; switch theme/scale/focus level live. 3. Paste onboarding → summary, steps, **important words highlighted**, tone note in parentheses on an indirect request; **listen in a natural Romanian voice with follow-along**. 4. Plan + .ics. 5. **Upload a voice recording → transcript + captions + bullets** (deaf/hard-of-hearing path). 6. Adjustment request without disclosure. 7. Employer side. 8. Guardrail moment (fabricated quote dropped) + privacy statement. 9. Roadmap + business model.

## 6. Definition of done for Wave 2
`check.sh` green on main · 3 clean real-LLM runs of the demo path · QA matrix filled honestly · fresh-clone test · every number in the deck traceable to `docs/evidence/` · known limits listed.

## 7. If we run out of time (cut order)
B10, B8 streaming, A8 server TTS, A9 voice commands, F8 restyle, F7 extras, F6 library, tone layer of B4, A7 level 3, A11. **Never cut:** B1, B2, B3, A1, A3, A4, A5, A6, F1–F5, F9, A10, F10.
