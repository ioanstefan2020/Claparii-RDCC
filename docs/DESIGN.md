# DESIGN — visual system for the Gemini-style rebuild (owner: P3)

Goal: calm, clear, institutional. Borrow from Gemini: generous spacing, airy cards, one main focus area, a left library sidebar, a big composer. Drop the "AI-generated site" clichés. Every colour pair below was **measured** (WCAG relative luminance); keep it that way: P2's `tests/web/test_contrast.py` reads the token file and fails the gate if a pair drops under its target.

## 1. Layout (Gemini-like, but more inclusive)
```
┌ top bar: [☰ menu] page title ········· [Contrast] [Text] [Audio ■ Stop] [Profil] ┐   (3 labelled buttons, text not icon-only)
├ sidebar (280px, collapsible, drawer on mobile) ┬ main (centered) ─────────────────┤
│ [+ Sarcină nouă]                               │  greeting: "Bună! Cu ce te ajutăm azi?"
│ Sunt: (•) angajat ( ) angajator                │  4 big action cards: Explică un document · Fă-mi un plan ·
│ Clarifică · Planificator · Ședință · Adaptări  │      Rezumă o ședință/audio · Cere adaptări
│ Audio → text · Interviu (when ready)           │  composer card: big textarea + [Lipește] [Încarcă fișier]
│ BIBLIOTECĂ (search, grouped Azi/Ieri/Săptămâna)│      [Vorbește] [Încearcă un exemplu]
│ ─────────                                      │  result cards (summary first, steps, terms, questions) with
│ Setări & accesibilitate · Confidențialitate    │      action bar: Ascultă · Mai scurt · Puncte · Pe pași · Salvează
└────────────────────────────────────────────────┴──────────────────────────────────┘
```
- Reading column (`--measure`, default 68ch) inside a wider container (max 1180px). The text never gets wider than the user's measure setting.
- Layout NEVER rearranges by itself; changes happen only when the user changes a setting. Sidebar open/closed state is remembered.
- No modals. Settings open as a page or an in-page panel. Confirmation = inline "Sigur? Da / Nu" row.
- Mobile: sidebar becomes a drawer opened by a labelled "Meniu" button; composer sticks to the bottom; targets ≥ 48 px.

## 2. Themes (default = Soft). All numbers measured
| Theme (`data-theme`) | Background | Card | Text | Text 2 | Accent | Border (controls) | Focus ring |
|---|---|---|---|---|---|---|---|
| `soft` (default) | `#F9F9F7` | `#FFFFFF` | `#1E2022` (15.5:1) | `#4A4F55` (7.84:1) | `#1E40AF` (8.27:1; white on it 8.72:1) | `#6B7075` (4.74:1) | `#005FB8` 3px + 2px offset (5.98:1) |
| `amber` (warm, low glare) | `#FDF6E3` | `#FFFBEF` | `#433422` (11.11:1) | `#5C4A32` (7.85:1) | `#8A3B00` (7.19:1) | `#7A6A55` (4.84:1) | `#005FB8` |
| `sapphire` (dark, soft) | `#0B132B` | `#131C3D` | `#E0E7FF` (14.92:1) | `#B4C0E8` (10.20:1) | `#93B4FF` (8.94:1) | `#6F7DB0` (4.58:1) | `#FFD166` (12.75:1) |
| `hc-dark` | `#121212` | `#1B1B1B` | `#FFFFFF` (18.73:1) | `#FFE600` (14.78:1) | `#FFE600` | `#FFFFFF` | `#FFE600` |
| `hc-light` | `#FFFFFF` | `#FFFFFF` | `#000000` (21:1) | `#1A1A1A` | `#0000CC` (11.22:1) | `#000000` | `#0000CC` |
| `mono` (no colour) | grayscale version of `soft` via `filter: grayscale(1)` on `<html>`; meaning never depends on colour |
| `night` (low blue light) | warm dark `#1A1410` / text `#F2E6D5` (verify with the contrast test before shipping) |
Errors `#9B1C1C` on soft (7.73:1); warning text `#7A4B00` (7.03:1). Notes on the original brief: `#1D4ED8` as text/links is only 6.36:1 (AA, **not AAA**); use `#1E40AF` (8.27:1). The brief's card border `#E3E2DE` is 1.23:1: fine for decorative card edges, **not** for inputs/buttons (WCAG non-text contrast needs 3:1) → controls use the "Border (controls)" colour above.
Follow the OS by default (`prefers-color-scheme`, `forced-colors`, `prefers-reduced-motion`, `prefers-contrast`), but the user's explicit saved choice always wins and is never overwritten.

## 3. Typography
- Default `Atkinson Hyperlegible` (self-hosted in `web/fonts/`, include `fonts.css`; needs BOTH latin and latin-ext files for ă ș ț), fallback `system-ui, 'Segoe UI', Roboto, sans-serif`. Dyslexia-friendly option = `OpenDyslexic` (covers all Romanian diacritics). Never `font-weight` < 400, never justified text, no all-caps paragraphs, no italics for long text.
- Three base sizes at 100% scale: H1 28px, H2/subheading 20px, body 18px (16px minimum). Everything is `rem`; user scale 70–200% via `--font-scale`; layout must survive 200% zoom and 320 px width.
- Line height 1.6, paragraph spacing 1em, letter spacing +0.02em by default; all user-adjustable (see `SETTINGS-SPEC.md`).

## 4. Components
- **Card:** 1.5px border, radius 12–16px, padding ≥ 20px, never floating on shadows alone.
- **Buttons:** min 48×48px, ≥ 12px gap, always a text label (icons support the label, never replace it). Primary = accent fill with white text; secondary = outlined; destructive asks inline for confirmation.
- **Inputs:** visible label above (not placeholder-only), 1.5px control border, error text linked via `aria-describedby`, example text under the field.
- **Composer:** one large textarea, helper line ("Lipește un e-mail, un document sau notițe de la ședință"), file button, voice button, "Încearcă un exemplu".
- **Result card set:** order = summary (≤ 2 sentences) → steps (ordered list) → deadlines (clock icon + date) → terms → questions to ask. Each item has "Arată în text" (source quote).
- **Audio bar (sticky, bottom):** Play/Pause, previous/next sentence, speed slider, voice, "Oprește" always visible while speaking.
- **Icons:** functional SVGs only (magnifier = Explică, calendar = Termene, speaker = Ascultă, microphone, file). **No sparkles, no gradients, no glow, no pulsing, no confetti, no chat-bubble gimmicks.**
- **States:** loading shows a text status ("Se procesează… poate dura câteva secunde") in an `aria-live` region and a static progress bar (no spinner animation under `reduce_motion`); empty states explain the next action; errors say how to fix.
- **Highlight styles** (see SETTINGS-SPEC §5): each category differs by **shape or icon, not colour alone** (underline style, background, icon, weight). Text on any highlight background must keep ≥ 7:1 (measured: `#1E2022` on `#FFF0A0` 14.18, `#D6E4FF` 12.76, `#D3F0DC` 13.44, `#FFD9B3` 12.32; dark themes: `#FFFFFF` on `#5C4B00` 8.53, `#E0E7FF` on `#4D4200` 8.14).
- **Sidebar library items:** title, type icon + label, date; keyboard: arrows move, Enter opens, Delete asks inline confirmation.

## 5. Things we do NOT do
Sparkle icons, purple/neon gradients, light-gray text on white, continuous animation or glowing borders, auto-playing audio, aggressive pop-ups, hover-only controls, timeouts, drag-only interactions, icon-only buttons, text in images, justified text, text smaller than 16px.

## 6. Handoff to engineering
P3 implements `web/` using the CSS variables and `data-*` attributes defined in `SETTINGS-SPEC.md` (P2's engine sets them; P3's CSS reads them). Token names are fixed there so both sides can work in parallel.
