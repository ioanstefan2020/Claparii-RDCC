# NEXT-STEPS.md: after M2 (all features on main with mock LLM)

Put this file in `docs/NEXT-STEPS.md`, commit it, and read it together for 10 minutes before anyone starts.
I could not see your repo from here, so task ids use a new prefix (N) and paths are my best guess from the earlier setup. Fix any path that differs (one `sed` or a quick edit in OWNERS).

---

## 0. What changes now

1. **The frontend is rebuilt from scratch, and P3 owns all of it.** Gemini-web layout, but warmer, clearer and more inclusive.
2. **Site comfort settings come from the user's own answers** ("how do you like things?"), are saved in `localStorage`, and survive reload, tab close and "reset".
3. **P2 is freed from screens.** P2 becomes the owner of the preferences engine (pure logic + tests), accessibility/QA gates, and pitch/demo script. This keeps P3 from drowning.
4. **P1 goes to real LLM quality, evals, streaming, and deployment.**

Hard rule, same as before: nobody edits another person's files. If you need a change in someone else's area, announce it in the chat and wait for them to ship it.

### OWNERS changes (edit the OWNERS file)

```
web/**                      p3
web/js/prefs/**             p2      # pure logic, no DOM, fully unit tested
tests/web/prefs/**          p2
tests/e2e/**                p2
tests/test_a11y_static.py   p2
docs/DEMO-SCRIPT.md         p2
docs/PITCH.md               p2
app/**                      p1
tests/api/**                p1
evals/**                    p1
docs/CONTRACTS.md           p1      # P2 and P3 propose changes in chat, P1 ships them
data/evidence/**            p3
```

Commit this first (P1 does it, 2 minutes), then everyone runs `./scripts/sync.sh`.

---

## 1. Shared contract: the preferences object (add to CONTRACTS.md)

Stored in the browser only. **Never sent to the server.** This is also a pitch point: the comfort profile is private by design.

- Storage key: `wp.prefs.v1`
- Written on every change, read before first paint
- If `localStorage` throws (private window, blocked), fall back to in-memory and show a small notice, never crash

```json
{
  "version": 1,
  "updatedAt": "2026-10-22T18:00:00Z",
  "answers": {
    "readingPace": "slow | medium | fast",
    "textAmount": "short | medium | full",
    "stepByStep": true,
    "visualNoise": "low | normal",
    "sensory": "quiet | normal",
    "language": "ro | en",
    "timeToDecide": "need-more-time | normal"
  },
  "prefs": {
    "theme": "light | dark | system",
    "textSize": "m | l | xl",
    "spacing": "comfortable | roomy",
    "contrast": "normal | high",
    "motion": "reduced | full",
    "font": "default | readable",
    "density": "focused | full",
    "language": "ro | en",
    "sidebar": "open | collapsed"
  },
  "overrides": ["textSize"]
}
```

Rules:

- `answers` are **how the person likes things**, never "do you have X". No diagnosis, no inferred conditions or emotions. This matches the theme rules in AGENTS.md.
- `prefs` is derived from `answers` by one pure function: `derivePrefs(answers) -> prefs` (P2 owns it).
- Anything the user changes by hand is recorded in `overrides`, and re-deriving never overwrites it.
- "Reset" has two separate buttons, clearly labelled: **"Re-apply my answers"** (clears overrides) and **"Start over"** (clears everything, asks for confirmation).
- Export / import as a JSON file (backup for the demo laptop and a nice trust feature).
- Applied as `data-*` attributes on `<html>` (`data-theme`, `data-text`, `data-spacing`, `data-contrast`, `data-motion`, `data-font`, `data-density`). CSS reads only those attributes plus design tokens.
- An **inline script in `<head>`** reads storage and sets the attributes before first paint, so there is no flash of default style on reload.

Module API (P2 ships this in task N2.1, P3 imports it):

```
derivePrefs(answers)            -> prefs
loadPrefs() / savePrefs(state)  -> state
applyPrefs(prefs, rootElement)  -> void
resetToAnswers(state)           -> state
migrate(raw)                    -> state   (unknown/corrupt data returns safe defaults)
```

---

## 2. Frontend spec for P3 (Gemini-like structure, our own look)

### Borrow from Gemini
- Generous spacing, big breathing room, one centered content column (max about 720px)
- Airy cards with soft corners and light borders, no heavy shadows
- Structural simplicity: left sidebar + main area + one prominent input/action

### Do NOT copy (the "AI site in 5 minutes" cliches)
- Purple/neon gradients
- Sparkle emoji or star icons used as decoration
- Distracting animations, shimmer, typing effects for decoration
- Full matte-black background as the only look. Default is a warm off-white; dark mode is dark grey/navy, never pure black on pure white or the reverse.

### Layout
```
+-----------+------------------------------------------+
| Sidebar   |  Top bar: page title        [Comfort]    |
|           |------------------------------------------|
| + New     |                                          |
| Home      |        Centered column (max 720px)       |
| Library   |        "What do you need help with?"     |
| Employer  |        [ card ] [ card ]                 |
| Settings  |        [ card ] [ card ]                 |
|           |        Input / paste area                |
| Recent    |                                          |
+-----------+------------------------------------------+
```
- Sidebar collapsible, state saved in prefs. On mobile it becomes a drawer opened by a button labelled "Menu" (text, not just an icon).
- Every icon has a visible text label. No icon-only buttons for primary actions.
- One primary action per screen, clearly the biggest button.

### Screens
1. **Welcome / "How do you like things?"** (first run): 5 to 7 plain-language questions, one at a time, large options, **live preview** of the result on the right (or above on mobile). The user confirms. Skippable.
2. **Home**: cards for the main features (simplify a document, tasks from an email, meeting recap, ask for an adjustment). Each card: title, one-line plain description, one button.
3. **Result view**: the output with quote evidence for any extracted deadline, copy button, "Save to library".
4. **Library**: saved results, search, stored **in the browser only** (localStorage or IndexedDB), delete with undo.
5. **Employer view**: same shell, same components, different cards.
6. **Settings / Comfort**: all prefs from section 1, a preview block, "Re-apply my answers", "Start over", export/import.

### Inclusive-design requirements (all of these get tested)
- Base text 18px or more, line height 1.6 or more, line length max about 70 characters
- Touch targets at least 44x44px
- Visible focus ring on every interactive element (3px, high contrast)
- Full keyboard path through the demo, skip link, landmarks (`header`, `nav`, `main`)
- Color is never the only signal (status has text + icon)
- Contrast at least 4.5:1 for text in every theme/contrast combination (P2 tests the matrix)
- `prefers-reduced-motion` respected by default, plus the manual setting
- Plain language, short sentences, no jargon in UI copy. Romanian first, English second.
- No timeouts that erase work, no surprise popups, destructive actions have confirm or undo
- Loading states say what is happening in words ("Reading your document...")

### Design tokens
All colors, sizes, radii, spacing live as CSS variables in one file (`web/css/tokens.css`). **No hardcoded colors or pixel sizes anywhere else.** P2 adds a lint test for this, so the agent can't cheat.

### Technical constraints (keep it demo-safe)
- No build step if the current frontend has none. Plain HTML/CSS/JS modules is fine and easier to debug at 3 AM.
- Use the existing API contracts untouched. Develop against fixtures first, switch to the real API second.
- Keep the old frontend in `web_old/` until the new one passes the demo path, then delete it.

---

## 3. Tasks per person

Order matters. Times are hours after start (we are at about 8:00).

### P3 (frontend + evidence)

| Id | Task | Done when |
|----|------|-----------|
| N3.1 | `tokens.css` + base styles + app shell (sidebar, top bar, main column), all driven by `data-*` attributes | Shell renders in all themes, keyboard works, a11y test green |
| N3.2 | Home screen with feature cards, wired to the existing API | Full demo path works in the new UI with mock LLM |
| N3.3 | Welcome questionnaire + live preview, using P2's prefs module (until N2.1 ships, use a temporary stub with the same API) | Refresh keeps everything |
| N3.4 | Settings/Comfort page | Both reset buttons work, export/import works |
| N3.5 | Library (browser-only) | Save, search, delete with undo, survives reload |
| N3.6 | Employer view in the new shell | Demo path for employer works |
| N3.7 | Polish pass with 2 real people (see below) | Findings written down in `data/evidence/` |

**Keep doing interviews in parallel**, even short ones. Real feedback on the new UI is the best evidence we can get. Record only what people really said.

Target: N3.1 shipped by 11:00 (everyone else needs the shell), N3.2 to N3.4 by 14:00, N3.5 and N3.6 by 17:00.

### P2 (preferences engine, QA, pitch)

| Id | Task | Done when |
|----|------|-----------|
| N2.1 | `web/js/prefs/` module (section 1 API) with unit tests (node test runner or whatever the repo uses) | Tests cover: derive, overrides kept, corrupt storage, storage blocked, migration, unknown version. Ship by 10:30, announce in chat |
| N2.2 | Questionnaire content: the questions, answer options, the mapping table `answers -> prefs`. Plain Romanian + English | Reviewed by P3 for tone and by one real person |
| N2.3 | Tests: no hardcoded colors, contrast matrix (every theme x contrast combination), tokens exist for every `data-*` value | `./scripts/check.sh` fails if someone breaks them |
| N2.4 | E2E demo-path test (Playwright if it installs, otherwise a scripted checklist + HTTP smoke test) including "set prefs, reload, prefs still there" | Runs in check.sh or `./scripts/e2e.sh` |
| N2.5 | Manual a11y audit: keyboard-only run, zoom 200%, a screen reader pass (VoiceOver or NVDA), mobile width. Written as a checklist with results | Issues sent to P3 in chat with exact page + step |
| N2.6 | `docs/DEMO-SCRIPT.md` (the exact click path, timing, what to say) and `docs/PITCH.md` slide outline | Rehearsed twice with a timer |

P2 also becomes the **second pair of eyes**: after each P3 ship, run the demo path yourself and report in the chat.

### P1 (AI, backend, deployment)

| Id | Task | Done when |
|----|------|-----------|
| N1.1 | Switch to the real LLM provider behind the existing interface, mock stays as fallback via env var | 3 clean runs of every feature with the real model |
| N1.2 | `evals/` folder: 15 to 25 cases from `data/samples/` (including the injection sample) with expected properties, runnable as `python evals/run.py` | Prints pass/fail per case, saved to a report file |
| N1.3 | Hardening: structured-output validation with one retry, quote-must-exist-in-source check on every deadline, no-diagnosis/no-emotion guardrail test, prompt-injection test, size limits, friendly error messages (plain language, never a stack trace) | Tests green, errors shown by the UI make sense |
| N1.4 | Streaming or progress responses so the UI is never a blank wait (agree format with P3 in chat, add to CONTRACTS.md) | Result starts appearing within 2 to 3 seconds |
| N1.5 | Stretch features in cut order from PROJECT.md (tone suggestion, interview prep, employer adjustments overview). Contract first, then build | Each has tests + fixture for P3 |
| N1.6 | Deploy a public URL (any simple host you can get working in 30 min) + `/api/health`. Backup plan: run locally and record a video | URL works from a phone on mobile data |
| N1.7 | Simple request log (no personal text stored) so we can see latency and failure rate | Visible in terminal |

Target: N1.1 by 11:00, N1.2 and N1.3 by 14:00 (this is M3), N1.6 by 16:00.

---

## 4. Milestones from here (edit to your real clock)

| Time | Milestone |
|------|-----------|
| 10:30 | N2.1 prefs module shipped. P1 commits OWNERS change |
| 11:00 | N3.1 new shell on main. N1.1 real LLM works |
| 14:00 | M3: new Home + questionnaire + settings, real LLM, 3 clean demo runs in a row. Tag `good-3` |
| 17:00 | Library + employer view done, deployed URL |
| 19:00 | **FREEZE**: bug fixes only, a11y audit done |
| 19:00-22:00 | Rehearse x2, backup recording, fresh-clone test |
| 22:00-23:00 | Submit with slack |

If N3.1 slips past 12:00, drop the Library and keep the shell + Home + Settings. A polished small thing beats a big broken one.

---

## 5. Further optimizations to the agent setup

Add to **AGENTS.md** (everyone pulls it after P1 or whoever owns it ships):

```
## Frontend rules (added after M2)
- All colors, spacing, radii, font sizes come from web/css/tokens.css variables. Never hardcode.
- UI state that depends on user preferences is read from data-* attributes on <html>, never from JS conditionals in components.
- Every interactive element: visible text label, visible focus, 44px target, keyboard reachable.
- Never store or send the preferences object or document text to the server.
- UI copy: plain language, short sentences, Romanian first. No emoji decoration, no sparkle icons, no gradients.
- Before saying done: run ./scripts/check.sh, open the page, use it with keyboard only, reload and confirm prefs persist.
```

Other habits that pay off now:
- **One task per thread.** New thread for every N-task, start with Prompt 0.
- **Plan first, then "ok go".** Never let the agent build before you read its 5-line plan.
- **Ask the agent to write the failing test first**, then the code. Especially for prefs and the guardrails.
- **After every agent "done": Prompt 10 (prove it)**, then you run it yourself.
- **Use subagents for independent work only**, e.g. "one agent writes tests for the prefs module, another writes the questionnaire copy". Never two agents editing the same file.
- **Commit small and ship often** with `./scripts/ship.sh`. A broken main at hour 20 is the biggest risk.
- **Tag known-good states** (`good-3` etc.) so you can roll back in 30 seconds.
- **Don't let the agent add libraries** without telling you. Every new dependency is a new way to fail on a fresh clone.

---

## 6. Prompts to paste (after Prompt 0 in a fresh thread)

### P3: shell and design system (N3.1)

```
Task N3.1. Rebuild the frontend shell from scratch in web/ (keep the old one in web_old/).
Read docs/NEXT-STEPS.md section 1 and 2 first, and CONTRACTS.md.

Goal: a Gemini-web-like structure (collapsible left sidebar with New / Home / Library / Employer / Settings,
top bar, one centered content column max 720px, airy cards) but warmer and more inclusive.
No purple/neon gradients, no sparkle icons, no decorative animation, no pure black background.
Default theme: warm off-white. Also provide dark (dark grey/navy) and high contrast.

Requirements:
- web/css/tokens.css holds ALL colors, spacing, radii, font sizes as CSS variables.
  Themes/sizes switch via data-* attributes on <html> (theme, text, spacing, contrast, motion, font, density).
- An inline script in <head> reads localStorage key wp.prefs.v1 and sets those attributes before first paint.
  Wrap storage in try/catch.
- Sidebar items have icon + text label. Mobile: drawer opened by a button labelled "Menu".
- Skip link, landmarks, visible focus ring, 44px targets, base font 18px, line-height 1.6.
- Respect prefers-reduced-motion.
- No build step. Plain HTML/CSS/JS modules.

First write a 5-line plan and wait for my "ok go".
Then build, run ./scripts/check.sh, open the page, tab through the whole shell with keyboard only,
reload with a changed data-theme saved in localStorage and confirm no flash of default style.
Show me the evidence before saying done.
```

### P2: prefs engine (N2.1)

```
Task N2.1. Build web/js/prefs/ exactly per docs/NEXT-STEPS.md section 1 (the preferences object and the module API).
Pure logic, no DOM except applyPrefs. Write the tests FIRST and show them failing, then implement.

Tests must cover: derivePrefs for every answer combination in the mapping table, overrides are kept on re-derive,
corrupt JSON in storage returns safe defaults, storage that throws falls back to memory,
unknown version is migrated or defaulted, resetToAnswers clears overrides only,
and a round trip save -> load returns identical state.

Rules: answers describe how the person likes things, never conditions or diagnoses. Do not infer emotions.
No new dependencies. Plan in 5 lines first, wait for my "ok go".
```

### P1: real LLM + evals (N1.1, N1.2)

```
Task N1.1 then N1.2. Switch the LLM provider to the real one behind the existing interface (mock stays via LLM_PROVIDER=mock).
Then create evals/run.py with 15 to 25 cases from data/samples/ including the prompt-injection sample.
Each case checks properties, not exact text: valid schema, every deadline quote exists verbatim in the source,
no diagnosis or emotion inference, injection text is not obeyed, response under N seconds.
Print pass/fail per case and write evals/report.md.
Plan first (5 lines), wait for my "ok go". Tell me which API key actually worked and what latency you measured.
```

---

## 7. Things I could not verify

- I have not seen your current repo, so file paths, task ids and the existing test runner are assumptions. Adjust them before pasting prompts.
- The agent files and scripts have never been run against a real Antigravity session. Watch the first N3.1 run and correct AGENTS.md if the agent ignores a rule.
- Screen reader behavior must be checked by a human (N2.5). Automated checks catch structure, not experience.
- Accessibility claims in the pitch ("inclusive", "works for everyone") must be backed by what you actually tested and what real people told you. Say "we tested X with Y people" and nothing bigger.
