---
name: a11y-by-design
description: Use when building or reviewing any UI (web/). WCAG 2.2 AA checklist for a multi-disability product - keyboard, screen reader, contrast, cognitive load, voice, captions - with how to test each item.
---

# Accessibility by design (target: WCAG 2.2 AA)

The jury scores accessibility twice (inclusive design + UX). Cover **cognitive, visual, hearing and motor** needs, and say so in the pitch.

## Build rules (every page)
- `<html lang="ro">`, one `<h1>`, logical heading order, landmarks (`header`, `nav`, `main`, `footer`), a **skip link** first in the body.
- Real elements: `<button>` for actions, `<a>` for navigation, `<label for>` for every input, `<fieldset><legend>` for groups. No `div onclick`.
- **Keyboard**: everything reachable and operable with Tab/Shift+Tab/Enter/Space/Esc; visible focus (≥ 3:1 contrast, 2 px+ outline); no keyboard traps; no positive `tabindex`.
- **Screen reader**: meaningful names, `aria-live="polite"` region for async results and errors (announce "Se procesează…" then the result), `aria-busy` while loading, focus moved to the result heading after generation. Do not overuse ARIA; native first.
- **Contrast**: text ≥ 4.5:1, large text and UI parts ≥ 3:1; do not rely on colour alone. Provide a **high-contrast mode** and dark mode via CSS variables (design tokens in `web/shared/a11y.css`).
- **Zoom / reflow**: usable at 200% text zoom and 320 px width; use `rem`, no fixed heights, no horizontal scroll; viewport must NOT disable zoom.
- **Targets**: interactive targets ≥ 44×44 px where possible (min 24×24), spacing between them.
- **Motion**: respect `prefers-reduced-motion`; no autoplay; no time limits (or let users extend them).
- **Cognitive load**: plain Romanian, short sentences, one primary action per screen, predictable layout that **never rearranges itself**, clear error messages that say how to fix, progress shown, confirmation before destructive actions, "simple mode" toggle (fewer elements, larger text, more spacing).
- **Reading support**: adjustable text size, line height, letter/word spacing, width; reading aloud with `speechSynthesis` (ro-RO if a voice exists, else say so); steps rendered as an ordered list.
- **Voice / hearing**: voice input via Web Speech API (`ro-RO`) with a typing/pasting fallback; transcripts are text; label non-speech sounds as text; no emotion inference from voice.
- **Forms**: labels visible (not placeholder-only), `autocomplete` where relevant, errors linked with `aria-describedby`.
- **Files**: downloads (ICS, text) have descriptive names; do not open new windows silently.
- **Language**: set `lang` on any non-Romanian fragment.
- **No external CDNs** (offline-safe, privacy-friendly); system font stack.

## Test every UI task (evidence required in your report)
1. `./scripts/check.sh` (includes `tests/test_a11y_static.py`).
2. **Keyboard-only pass**: unplug the mouse mentally; complete the whole flow with the keyboard; note the order and any trap.
3. **Screen reader pass** (Orca on Linux, NVDA on Windows, VoiceOver on Mac): complete the flow with eyes closed for 3 minutes; note anything unlabeled or silent.
4. **Zoom/contrast pass**: 200% browser zoom, then high-contrast mode, then 320 px width.
5. If a browser is available: run axe (browser extension or `npx @axe-core/cli http://localhost:8000`) and fix serious/critical findings. Report what you could not run.

## Pitch-ready statements (only claim what you tested)
- "Built to WCAG 2.2 AA targets; automated checks on every commit + manual keyboard and screen-reader testing."
- Name the four need-groups and the exact feature that serves each.
- Be honest about limits (e.g. Romanian TTS voice availability depends on the device).
