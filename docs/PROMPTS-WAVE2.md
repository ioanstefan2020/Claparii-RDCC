# Prompts — Wave 2 (copy, paste, replace <…>). Start every thread with Prompt 0 from docs/PROMPTS.md, then:

## W0. State audit (everyone, first 10 minutes)
```
I am <me>. Read AGENTS.md, OWNERS, docs/TASKS-WAVE2.md, docs/SETTINGS-SPEC.md, docs/DESIGN.md, docs/CONTRACTS-WAVE2.md, docs/PROMPT-SPEC.md and docs/plan/NEXT_WAVE_PROPOSAL.md. Then inspect the code. For MY tasks in TASKS-WAVE2.md give me a table: task id | already exists (file:line) | partly exists (what is missing) | not started. Also list anything in the code that contradicts the specs (names, enums, endpoints). Do not change files.
```
## W1. Review prompt for the in-repo planner agent (paste once, any person)
```
Read docs/TASKS-WAVE2.md, SETTINGS-SPEC.md, DESIGN.md, CONTRACTS-WAVE2.md, PROMPT-SPEC.md, RESEARCH-WAVE2.md. Critique them against the real code: (1) tasks already done or mis-scoped, (2) file ownership conflicts with OWNERS, (3) contract mismatches with existing endpoints/schemas, (4) the 5 riskiest tasks for the time left and how to de-risk each, (5) missing tasks that would matter to blind, low-vision, deaf, motor, attention-related and cognitive/reading users. Output a short markdown patch list (edit X in file Y), do not rewrite the docs.
```
## W2. Ideas jam (any person, 15 min, then paste the best into the group chat)
```
Using docs/RESEARCH-WAVE2.md section 3 as the starting list, propose 15 additional ideas that would concretely help someone in their first months at work, for: blind, low vision, deaf/hard of hearing, motor, attention-related and cognitive/reading needs, and for employers. For each: the user need, the smallest implementable version (files), effort in hours, and the evidence or reasoning it helps. Mark any idea that would infer health data, emotions or personality (reject those). Do not claim benefits that research does not support.
```

## P1 prompts
### B1 provider reliability
```
I am p1. Do B1 from docs/TASKS-WAVE2.md. First reproduce "Groq in the config sometimes does nothing": show me exactly which env vars/config the code reads, what happens when the key is missing, when Groq returns 429/5xx/invalid JSON, and why the fallback chain didn't (or did) run. Then implement the chain, startup validation logging, per-provider circuit state, Retry-After backoff, /api/llm/status, per-task routing. Tests with fake providers for every failure mode. Show the status endpoint output.
```
### B2 tolerant I/O
```
I am p1. Do B2. Find every Pydantic model that can raise 422 on profile/enum input and every place the LLM output is parsed strictly. Implement normalize_profile with alias maps, extra=ignore, soft validation (coerce/clamp/drop+warning), JSON extraction/repair, Romanian diacritics normalisation (ş ţ vs ș ț) in quote verification. Write a fuzz test (100 random profiles/garbage values) proving no 422/500. Show the test output.
```
### B3 prompts v2
```
I am p1. Do B3 using docs/PROMPT-SPEC.md. Create app/prompts/base.py (BASE_SYSTEM_RO, EASY_READ_RULES_RO, adapt_block) and rewrite simplify/plan/meeting prompts with 2 Romanian few-shots each, <<<DOCUMENT delimiters, versions. Keep the existing response schemas. Run the golden set (B7) on the primary provider before and after, and show me the scorecard diff (schema-valid %, quote-valid %, invented dates, injection pass). Do not merge if the scorecard gets worse.
```
### B4 annotate
```
I am p1. Do B4. Start with the deterministic layer (Romanian dates/weekdays/months/times/amounts/emails/phones/IDs) with unit tests on data/samples incl. text without diacritics; verify text[start:end]==text. Then the semantic layer (action/person/warning/term + glossary) with density caps. Then, only if time allows, the tone layer from PROMPT-SPEC section 5, conservative, evidence-quoted, confidence low|medium only. Report precision on our labelled set, not accuracy.
```
### B5 transform
```
I am p1. Do B5. Implement /api/transform modes bullets|shorter|tldr|easy_read|steps|questions|glossary. Add a test that every date, amount and name in the input survives into bullets/shorter output on the samples. Contract + failure tests. Show real-provider outputs for onboarding_ro.txt in all modes.
```

## P2 prompts
### A1 settings engine
```
I am p2. Do A1 using docs/SETTINGS-SPEC.md. First (within 45 minutes) ship stub modules web/a11y/settings.js, boot.js, tts.js, highlight.js, layouts.js with the final exported function names from SETTINGS-SPEC section 10 so p3 can integrate. Then implement the real settings engine: defaults, validation/clamping, versioned localStorage key primazi.settings.v2, migration from the old welcome/profile keys, boot.js applying data-* attributes and CSS variables before first paint, cross-tab sync, export/import, reset only on explicit call. Write docs/settings.schema.json and node --test tests wrapped by a pytest test. Prove: change a setting, reload, it persists; clear nothing else.
```
### A2 profile derive v2
```
I am p2. Do A2. Extend the existing POST /api/profile/recommend-adaptations to return {settings, reasons, adaptations} using the full key set in SETTINGS-SPEC, clamped to the allowed values, with diagnosis words scrubbed (never echoed) and a heuristic fallback. Test: "obosesc la lumină tare și uit instrucțiunile verbale" and 10 other phrasings in Romanian, plus garbage. No 422 ever.
```
### A3 natural TTS
```
I am p2. Do A3. Build web/a11y/tts.js: pick the best Romanian voice (prefer names containing Natural/Online), speak sentence by sentence with pause, rate, pitch, follow-along highlight, pause/resume/stop/prev/next, global Stop, and tts-normalize-ro.js (dates, times, amounts, F-12, abbreviations, ordinals spoken correctly). Unit-test the normalisation with at least 20 Romanian cases. Tell me honestly which voices were found in this browser and how the result sounds; do not claim a voice you did not test.
```
### A4 transcribe
```
I am p2. Do A4 per docs/CONTRACTS-WAVE2.md: /api/transcribe with Groq whisper-large-v3-turbo (language ro, verbose_json), ffmpeg shrink to 16 kHz mono and chunking above 25 MB, SRT/VTT generated from segments, local faster-whisper fallback if installed, friendly errors, temp files deleted, nothing logged. Text only. Test with a 30-60 s Romanian recording; also mock mode. Show the SRT output.
```
### A5/A6 CSS + renderer
```
I am p2. Do A5 and A6. Implement themes.css/typography.css for every variable in SETTINGS-SPEC section 1 using web/fonts/fonts.css, and tests/web/test_contrast.py that computes WCAG ratios for every token pair per theme and fails under the targets in DESIGN.md. Then highlight.js: renderRich with safe DOM building (no innerHTML of user text), category styles with non-colour cues, density cap, legend, tone notes in parentheses, glossary, ruler. Unit tests including XSS strings and overlapping spans.
```

## P3 prompts
### F1 shell
```
I am p3. Do F1 using docs/DESIGN.md and docs/SETTINGS-SPEC.md. Build the Gemini-style shell: collapsible sidebar (drawer on mobile), top bar with three labelled controls (Contrast, Text, Audio-Stop), skip link, landmarks, an <app-shell> web component included by separate .html pages, tokens reading the data-* attributes and CSS variables. No sparkles, no gradients, no animation, no modals, targets >= 48px. Import /a11y/boot.js in <head> and web/fonts/fonts.css. Run ./scripts/check.sh and do a keyboard-only pass and a 200% zoom + 320px pass; describe what you saw.
```
### F4 studio
```
I am p3. Do F4. Build the Accessibility Studio page covering EVERY variable in SETTINGS-SPEC (grouped, searchable), presets with one-line explanations, live preview, reset with inline confirm, export/import, delete-all-data, and the onboarding flow using recommend-adaptations (propose -> user accepts/edits -> save; never apply silently). Prove persistence: change settings, reload, open a new tab, restart the browser. Then run the a11y checks.
```
### F5 audio page
```
I am p3. Do F5. Build the audio-to-text page against /api/transcribe: keyboard-friendly upload, progress status, transcript with clickable timestamps, download .srt/.vtt/.txt, buttons Rezumat / Puncte / Mai scurt / Ce am de făcut (use /api/meeting/summarize and /api/transform), visual alert on completion, privacy note. Test with a real 30-60 s Romanian file and with a wrong-format file.
```

## QA prompts (P2 leads, everyone)
### Q1 a11y group matrix
```
Use the a11y-by-design skill. For <page(s)> produce a pass/fail table for: keyboard-only, screen reader (describe what is announced per step), 200% zoom + 320px, forced-colors/high contrast, reduced motion, colour-blind simulation, captions/transcript path, motor (no mouse), cognitive (focus levels, plain language). Fix only my files; for others write exact change requests. Do not claim anything you did not test.
```
### Q2 real-LLM reliability (P1)
```
With LLM_PROVIDER_CHAIN as configured, run the demo path 5 times (clarify, plan, meeting, transform, annotate). Report per run: provider used, latency, schema-valid, quotes dropped, invented dates, any 4xx/5xx. List every failure with its cause and the fix.
```
