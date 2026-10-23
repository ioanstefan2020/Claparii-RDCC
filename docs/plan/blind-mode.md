# Plan: Blind Mode (Ecran Negru) & Romanian Voiceover Navigation

## Feature: Blind Mode & Romanian TTS Screen Reader
**Goal:** Enable a blind user or judge to navigate and use the entire Limpede application with only keyboard (Tab/Shift+Tab/Enter) or mobile touch, guided by a natural Romanian voice that reads roles and labels aloud, with an F9 hotkey that activates a pitch-black screen curtain to demonstrate 100% blind usability.

**Non-goals:**
- Third-party desktop screen reader integration (users can still use NVDA/Orca/VoiceOver if they wish; this is a built-in zero-dependency voiceover).
- Cloud subscription TTS requirements (works fully client-side offline via Web Speech API with server fallback).

**Design:**
- `web/a11y/voiceover-core.js`: Pure helpers computing accessible Romanian labels, role names (buton, casetă de text, link, etc.), states (bifat, extins), and sentence normalization.
- `web/a11y/voice-engine.js`: Robust speech coordinator prioritizing natural Romanian voices (`ro-RO`), cancelling speech on focus shift, and unlocking mobile audio.
- `web/a11y/blind-mode.js`: Manages `#blind-curtain` (pitch black screen overlay), listens to `F9` / `Alt+B`, toolbar toggle button, intercepts `focusin` to read elements aloud, handles touch gestures, and announces live mode changes.
- Removal of `/employee/adjustments.html` and references across menus, smoke script, and automated tests.

**Interfaces:**
- `F9` / `Alt+B`: Toggle blind mode overlay on/off.
- `window.LimpedeBlindMode`:
  - `toggle(forceState?: boolean): boolean`
  - `isActive(): boolean`
  - `speakCurrentFocus(): void`
- `window.LimpedeVoiceEngine`:
  - `speak(text: string, options?: object): void`
  - `speakElement(el: HTMLElement): void`
  - `stop(): void`

**Tasks:**
- [ ] T1: Pure Romanian Voiceover Core (`web/a11y/voiceover-core.js`) — tests: `tests/web/test_voiceover_core.py`
- [ ] T2: Voice Engine (`web/a11y/voice-engine.js`) — tests: audio state & voice scoring tests
- [ ] T3: Blind Mode Controller & Black Screen Curtain (`web/a11y/blind-mode.js`, `web/css/shell.css`, header toolbar integration in `web/js/shell.js`) — tests: `tests/web/test_blind_mode.py`
- [ ] T4: Remove Adjustments Page (`web/employee/adjustments.html`) — update all HTML navbars, `scripts/smoke.sh`, and pytest test suites
- [ ] T5: Quality Gate & 1-Person Demo Runbook (`docs/DEMO-BLIND-MODE.md`) — verify `./scripts/check.sh` passes 100%

**Acceptance criteria:**
1. Pressing `F9` turns the screen completely black (`#blind-curtain`), announces *"Modul ecran negru activat"* in Romanian, and tabbing through elements announces each element's role and label clearly.
2. Pressing `F9` again removes the curtain and announces *"Modul ecran negru dezactivat"*.
3. Header accessibility toolbar contains a "Mod Orb (F9)" button so mobile users can activate it without a physical keyboard.
4. `/employee/adjustments.html` is completely unlinked and removed, and `./scripts/check.sh` passes 100% (`GATE: PASS`).
5. `docs/DEMO-BLIND-MODE.md` gives a clear 1-person step-by-step rehearsal guide for the hackathon demo.
