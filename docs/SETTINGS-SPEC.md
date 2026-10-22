# SETTINGS-SPEC v2 — every adjustable thing, how it is stored, how it reaches the page (owner: P2; P3 and P1 implement against it)

## 0. Principles
1. **Needs, not diagnoses.** Settings and presets are named after what the person wants ("Fără distragere", "Text mare"), never a condition. We never infer or store a diagnosis. The free-text "in my own words" box stays on the device.
2. **Never resets by surprise.** Settings live in `localStorage` key `primazi.settings.v2` (JSON, versioned, migrated). Only an explicit "Resetează la implicit" (inline confirm) changes them back. Changes apply instantly and survive reload, new tabs (sync via `storage` event) and browser restarts. Export/import as a `.json` file (backup, new device).
3. **Applied before first paint.** `web/a11y/boot.js` is a tiny synchronous script in `<head>` of every page: reads settings, sets `data-*` attributes and CSS variables on `<html>`. No flash of default style.
4. **OS defaults only as initial values.** `prefers-reduced-motion`, `prefers-color-scheme`, `prefers-contrast`, `forced-colors` seed the defaults on first run; the user's saved choice always wins.
5. **Server never rejects settings.** The API receives a loose `profile` object and normalises it (unknown/old values mapped to the nearest valid one, warning in `meta.warnings`, never HTTP 422). Root cause of the earlier 422: UI enum ≠ server enum. There is now ONE source of truth: `docs/settings.schema.json` (P2) used by JS tests and by P1's `normalize_profile()` tests.
6. Presets set several variables at once and remain editable; the live preview shows a sample paragraph + a sample result card.

## 1. Visual (CSS variables / data attributes on `<html>`)
| Key | Values (default) | Applied as |
|---|---|---|
| `theme` | soft · amber · sapphire · hc-dark · hc-light · mono · night (soft) | `data-theme` |
| `font_family` | atkinson · system · dyslexia · serif-readable (atkinson) | `data-font` |
| `font_scale` | 70–200 % slider (100) | `--font-scale` |
| `line_height` | 1.2–2.4 (1.6) | `--lh` |
| `letter_spacing` | 0–0.2 em (0.02) | `--ls` |
| `word_spacing` | 0–0.5 em (0.05) | `--ws` |
| `paragraph_spacing` | 0.5–3 em (1) | `--ps` |
| `measure` | 40–100 ch (68) | `--measure` |
| `font_weight` | 400 · 500 · 600 · 700 (400) | `--fw` |
| `link_style` | underline-always (fixed) | — |
| `saturation` | 0–100 % (100) | `--sat` |
| `color_vision` | none · protan · deutan · tritan (none) | `data-cvd` (palette variants + extra pattern cues) |
| `focus_ring` | normal · large · xlarge (normal) | `--focus-w` 3/5/7px |
| `cursor_size` | normal · large · xlarge | `data-cursor` |
| `dim_overlay` | 0–60 % (0) | `--dim` (soft dimming layer, helps photophobia/glare) |
| `reduce_motion` | auto · on (auto) | `data-motion` |
| `reduce_transparency` | bool (false) | `data-flat` |

## 2. Cognitive / focus / layout
| Key | Values (default) | Effect |
|---|---|---|
| `focus_level` | 0 Standard · 1 Ușor · 2 Mediu · 3 Maxim (0) | `data-focus` — see §3 |
| `density` | compact · comfortable · spacious (comfortable) | `data-density` (padding/gaps) |
| `layout` | overview · guided · card (overview) | `data-layout`: all results visible / one step at a time with Next-Prev / one sentence-or-step full width |
| `sidebar` | expanded · collapsed · auto-hide (expanded) | `data-sidebar` |
| `summary_first` | bool (true) | summary card on top, rest collapsed |
| `chunk_size` | 3 · 5 · 7 · all (all) | items shown per view |
| `progressive_disclosure` | bool (false) | secondary details collapsed |
| `glossary_inline` | off · hover/tap · always (hover/tap) | hard terms get a dotted underline + definition |
| `reading_ruler` | off · line · band (off) + `ruler_height`, `ruler_color` | follows pointer/focus |
| `focus_paragraph` | bool (false) | dims all paragraphs except the current one |
| `bionic` | bool (false) | **optional style only; no benefit claims** (see RESEARCH) |
| `reading_level` | standard · simple · very_simple (simple) | sent to server |
| `format` | steps · short_paragraphs · bullets (steps) | sent to server |
| `tone_notes` | off · on (off) | show tentative tone notes in parentheses |
| `break_reminders` | off · 25 · 45 min (off) | gentle visual reminder (no sound unless enabled) |
| `confirm_actions` | bool (true) | inline confirmation before delete/send |
| `calm_mode` | bool (false) | no animation/sound, muted palette, fewer UI elements |

## 3. Focus levels (what changes) — ADHD-friendly without naming a condition
| Level | Layout | Behaviour |
|---|---|---|
| 0 Standard | sidebar + all cards | — |
| 1 Ușor | sidebar collapsed, secondary panels hidden | summary first, steps list capped (`chunk_size` 5) with "Arată mai multe", highlight light |
| 2 Mediu | single column, **one step card at a time** with Next/Prev, progress "Pasul 2 din 6" | non-essential UI hidden, current step emphasised, optional break reminder, calm mode on |
| 3 Maxim | **card layout, one sentence/step full width**, large text | big Prev / Next / Ascultă / Gata, auto-read optional, Esc exits, timer optional |
Rule: changing level never moves things unpredictably during a task; it applies on the next render with an announcement ("Mod concentrare: Mediu").

## 4. Audio / hearing
| Key | Values (default) |
|---|---|
| `tts_engine` | auto · browser · server (auto: prefer natural browser voice, else server Piper) |
| `tts_voice` | voiceURI or `server:ro-mihai` (auto-pick best Romanian voice; prefer "Online (Natural)") |
| `tts_rate` | 0.5–2.0 (0.95) · `tts_pitch` 0.8–1.2 (1.0) · `tts_volume` 0–1 (1) |
| `tts_pause_ms` | 0–1500 between sentences (350) |
| `tts_follow` | none · sentence · word (sentence) — highlights what is being read |
| `tts_autoread` | off · result · page (off) |
| `tts_spoken_numbers` | bool (true) — dates, times, amounts, "F-12", abbreviations spoken correctly in Romanian |
| `captions_default` | bool (true) · `transcript_always` (true) |
| `visual_alerts` | bool (true) — border flash/toast instead of sounds · `vibration_alerts` bool |
| `sound_effects` | off (fixed default) |

## 5. Highlighting ("important words")
| Key | Values (default) |
|---|---|
| `highlight_mode` | off · light · medium · strong (light) — caps density: ≤ 5% / 10% / 15% of words |
| `highlight_categories` | subset of `action`, `deadline`, `person`, `number`, `warning`, `term` (action, deadline, warning) |
| `highlight_style` | combo · background · underline · bold · larger (combo) |
| `highlight_scale` | 100–140 % size boost for highlighted words (110) |
| `highlight_palette` | yellow · multi · mono (multi) |
Category cues (never colour alone): `action` = bold + solid underline; `deadline` = yellow background + clock icon; `person` = dotted underline + small badge; `number` = bold + tabular figures; `warning` = left marker with "!" icon + bold; `term` = dashed underline + definition on hover/tap/focus.
Rule: highlights are **few and meaningful** (over-highlighting hurts comprehension), always with a legend ("Ce înseamnă culorile/stilurile") and a one-click "Fără evidențieri".

## 6. Motor / input
| Key | Values (default) |
|---|---|
| `target_size` | 44 · 48 · 56 · 64 px (48) → `--target` |
| `target_gap` | 8–24 px (12) → `--gap` |
| `keyboard_shortcuts` | on · off (on, with "?" help) · `single_key_shortcuts` off (WCAG 2.1.4: single-key shortcuts must be off or remappable) |
| `voice_commands` | off · on (off): "următorul", "înapoi", "citește", "oprește", "salvează" (Web Speech, `ro-RO`) |
| `tooltips_on_focus_click` | bool (true) — no hover-only content |
| `no_drag` | fixed true — every drag interaction has a button alternative |
| timeouts | none anywhere (fixed) |

## 7. Screen reader / blind / low vision
| Key | Values (default) |
|---|---|
| `sr_mode` | bool (false) — verbose labels, less decoration, results announced once, headings-first structure, skip links expanded |
| `announce_level` | minimal · polite · assertive (polite) |
| `describe_images` | auto · ask · off (ask) — uses the image-description endpoint |
| `magnify_focus` | bool (false) — enlarges the focused element |
| zoom/reflow | must work to 200% and 320 px (tested) |

## 8. Language
`ui_language` ro · en (ro) · TTS/STT language `ro-RO`.

## 9. Presets (need-based; P2 implements, user can edit)
| id | Label | Sets |
|---|---|---|
| `citire-usoara` | Citire ușoară | reading_level very_simple, format steps, summary_first, glossary always, line_height 1.8, spacing up, highlight light, tone_notes on |
| `fara-distragere` | Fără distragere | focus_level 2, layout guided, calm_mode, chunk 3, break_reminders 25, sidebar collapsed |
| `text-mare` | Text mare și contrast | font_scale 150, theme amber or hc-light, target 56, focus_ring large |
| `cititor-ecran` | Cu cititor de ecran | sr_mode, announce polite, describe_images auto, layout overview, no hover content |
| `audio-in-text` | Audio în text | captions_default, transcript_always, visual_alerts, vibration_alerts |
| `control-usor` | Control ușor (tastatură/voce) | target 64, gap 16, shortcuts on, voice_commands on |
| `ascult-mai-mult` | Aud în loc să citesc | tts_autoread result, tts_follow word, rate 0.9, spoken numbers |
Presets are **suggestions the person picks**, not labels applied to them. "Derive from my words" (`POST /api/profile/recommend-adaptations`, extended in A2) proposes a settings diff with a one-line reason per change; the person accepts/edits; nothing is applied silently and no condition is named or stored.

## 10. JS API (`web/a11y/settings.js`, P2) — what P3's UI imports
```js
import { settings, getSetting, setSetting, setMany, applyPreset, resetAll, exportJSON, importJSON, onChange, PRESETS, DEFAULTS } from '/a11y/settings.js';
getSetting('font_scale'); setSetting('theme','amber'); onChange((key, value, all) => {}); // fires on change + cross-tab
```
Also: `web/a11y/boot.js` (head, sync), `web/a11y/tts.js` (`speak(nodeOrText)`, `pause()`, `resume()`, `stop()`, `next()`, `prev()`, events `onSentence`), `web/a11y/highlight.js` (`renderRich(el, text, {highlights, annotations, glossary})`), `web/a11y/ruler.js`, `web/a11y/layouts.js` (`mountResults(container, items, {layout, focus})`). Signatures are frozen at the start of Wave 2A; P2 ships stubs first.
