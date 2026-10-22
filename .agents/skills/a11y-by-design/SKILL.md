---
name: a11y-by-design
description: Use when building or reviewing any UI (web/). WCAG 2.2 AA & AAA guidelines, Gemini-style restful ergonomics, tactile focus bubble architecture, and testing checklists for a multi-disability product.
---

# Accessibility by Design & Gemini-Style Ergonomics (WCAG 2.2 AA & AAA)

The jury scores accessibility twice (inclusive design + UX). Cover **cognitive, visual, hearing and motor** needs, and say so in the pitch.

Our design philosophy follows the **Gemini style**: generous spacing, airy cards, and structural simplicity, while strictly eliminating AI clichés (no violet-neon gradients, no sparkles ✨, no distracting continuous animations, and no pitch-black matte backgrounds). The UI inspires **calm, clarity, and institutional trust**, strictly meeting WCAG AAA contrast (minimum 7:1 for normal text, 4.5:1 for large text, 3:1 for interactive UI components).

---

## 1. Paleta de Culori: Caldă, Odihnitoare și Fără „Neon AI”
Albul pur (`#FFFFFF`) pe ecrane mari obosește privirea și provoacă halouri persoanelor cu astigmatism sau sensibilitate senzorială, iar negrul pur (`#000000`) creează un contrast prea tăios. Alege nuanțe organice, inspirate din hârtie de calitate și tonuri pământii/oceanice:

- **Fundal principal (Canvas):** `#F9F9F7` (un alb-ivoriu/crem foarte deschis, cald, odihnitor pentru ochi).
- **Suprafețe carduri / containere:** `#FFFFFF` cu o margine subtilă solidă de 1.5px (`#E3E2DE`) în loc de umbre difuze greu de distins.
- **Text primar (High Contrast):** `#1E2022` (un gri cărbune adânc, care oferă un contrast de peste **14:1** pe fundal crem — mult peste cerința AAA).
- **Text secundar (Labels, metadate):** `#4A4F55` (menține un contrast de peste **7:1** față de fundal).
- **Culoare de accent (Funcțională, nu decorativă):** `#1D4ED8` sau `#0F52BA` (un albastru regal cald, asociat cu profesionalismul și încrederea) ori `#1B4D3E` (un verde pin/salvie închis, extrem de calmant pentru stări de anxietate).
- **Focus outline (Tastatură):** `#005FB8` cu o grosime de 3px și offset de 2px, astfel încât utilizatorii care navighează exclusiv din taste să vadă instant selecția.

---

## 2. Tipografie: Lizibilitate înainte de orice
- **Fontul de bază:** Sans-serif curat, cu înălțime mare a literei mici (large x-height) și spațiere clară între caractere:
  - Recomandare: `Atkinson Hyperlegible` (creat de The Braille Institute special pentru a distinge caractere ușor de confundat precum I, l, 1 sau 0, O) sau `Inter`, urmat de stack-ul de sistem.
- **Comutator pentru Dislexie (Dyslexia Toggle):** Buton rapid în header care permite activarea modului dislexie (`data-font="dyslexic"` sau `data-dyslexia="true"`), comutând fontul la `OpenDyslexic` și crescând `letter-spacing` la `0.12em` și `line-height` la `1.6`.
- **Ierarhie strictă (3 mărimi de text în tot site-ul):**
  - **Heading 1:** 28px (`1.75rem`), `font-weight: 700`, `line-height: 1.25`.
  - **Subheading (H2 / H3 / Card Titles):** 20px (`1.25rem`), `font-weight: 600`, `line-height: 1.35`.
  - **Body / Controale:** 16px - 18px (`1rem` - `1.125rem`), `font-weight: 400` sau `500`, `line-height: 1.6`.
  - **Interzis:** Nu folosi fonturi subțiri (`font-weight: 300` e un coșmar de accesibilitate; interzis complet).

---

## 3. Arhitectura Vizuală (Lecțiile bune de la Gemini)
- **Zona centrală tip „Focus Bubble”:**
  - În loc de dashboard-uri înghesuite cu 10 tabele, păstrează centrul ecranului curat (lățime maximă 768px, `--max-content-width: 768px`), ca un dialog calm.
  - O singură casetă mare, prietenoasă de input cu butoane mari de acțiune: „Lipește textul / Trage o imagine”, urmată de pașii extrași în carduri clare, aerisite.
- **Carduri cu margini tactile:**
  - Cardurile de task-uri sau explicații nu trebuie să plutească ambiguu. O margine fină de 1.5px solidă (`#E3E2DE`) și colțuri rotunjite moderat (12px sau 16px, nu „pastile” ultra-rotunde) le face ușor de delimitat vizual de către persoanele cu vedere scăzută.
- **Target-uri de click/touch uriașe (Motor Accessibility):**
  - Orice buton sau zonă interactivă trebuie să aibă minimum **48x48px** zonă de acțiune (`--min-touch-target: 48px;`) și un spațiu de minim 12px între butoane, pentru utilizatorii cu tremur sau mobilitate redusă.

---

## 4. Ce să NU pui (Anti-Patterns de AI)
1. **Fără steluțe „sparkles” (✨):** Au devenit clișeul generatoarelor de text superficiale. Folosește pictograme funcționale concrete:
   - 🔍 Lupă pentru Clarificare / Căutare citate în text
   - 📅 Calendar pentru Termene / Export .ics
   - 🔊 Difuzor pentru Ascultă / Sinteză vocală
   - 📋 Checklist pentru Sarcini / Adaptări
   - 🏢 Clădire pentru Portalul Angajatorului
2. **Fără text gri-deschis pe alb:** Cel mai frecvent defect în UI-ul modern; contrastul trebuie să fie minim 7:1 pe text normal și 4.5:1 pe text mare.
3. **Fără animații continue sau glowing borders:** Pentru cineva cu ADHD sau autism, elementele pulsatorii sau fundalurile în mișcare creează suprastimulare senzorială și distragere involuntară. Orice tranziție trebuie să respecte `@media (prefers-reduced-motion: reduce)` și `[data-motion="reduced"]`.
4. **Fără modali (pop-up-uri) agresivi:** Păstrează tot fluxul în pagină sau într-un panou lateral glisant simplu; modalurile blochează adesea cititoarele de ecran.

---

## 5. Controalele esențiale din Header (Accessibility Toolbar)
Plasează în colțul din dreapta-sus un *Accessibility Toolbar* minimalist (butoane clare cu etichetă text, nu doar iconițe):
1. **Contrast:** Comutator între modul Soft/Natural (crem-cărbune `#F9F9F7` / `#1E2022`), High-Contrast Dark (fundal `#121212`, text galben `#FFE600` sau alb pur `#FFFFFF`) și High-Contrast Light (`#FFFFFF` / `#000000`).
2. **Text:** Mărime text (Normal / Mare / Foarte Mare).
3. **Audio:** Buton global de „Pauză / Oprește citirea”.
4. **Dislexie:** Comutator dedicat pentru modul de dislexie (OpenDyslexic, spațiere 0.12em).

---

## 6. Build rules (every page)
- `<html lang="ro">`, un singur `<h1>`, ordine logică a titlurilor, repere semantice (`header`, `nav`, `main`, `footer`), un **skip link** primul element în body.
- Elemente native: `<button>` pentru acțiuni, `<a>` pentru linkuri de navigare, `<label for>` pentru fiecare input, `<fieldset><legend>` pentru grupuri de opțiuni. Niciodată `div onclick`.
- **Keyboard**: totul accesibil și operabil din Tab / Shift+Tab / Enter / Space / Esc; indicator de focus vizibil (3px solid `#005FB8`, offset 2px); fără capcane de tastatură (no traps); fără `tabindex` pozitiv.
- **Screen reader**: nume accesibile semnificative, regiune `aria-live="polite"` pentru rezultate asincrone și erori (anunță „Se procesează…” apoi rezultatul), `aria-busy` în timpul încărcării, focus deplasat la titlul rezultatului după generare. Native first, fără exces de ARIA.
- **Contrast**: text normal ≥ 7:1 (AAA), text mare ≥ 4.5:1 (AAA), elemente UI interactive ≥ 3:1; nu te baza doar pe culoare. Furnizează modurile de contrast prin variabile CSS în `web/css/tokens.css` și `web/shared/a11y.css`.
- **Zoom / reflow**: complet utilizabil la 200% zoom text și la lățime de 320px; folosește `rem`, fără înălțimi fixe pe text, fără scroll orizontal pe conținutul principal; viewport-ul nu dezactivează niciodată zoom-ul.
- **Targets**: ținte interactive ≥ 48×48px, cu cel puțin 12px spațiu între ele.
- **Motion**: respectă `prefers-reduced-motion`; fără autoplay; fără limite forțate de timp.
- **Cognitive load**: română clară, fraze scurte, o singură acțiune principală pe ecran, layout predictibil care **nu se rearanjează singur**, mesaje de eroare clare cu pași de remediere, confirmare înainte de acțiuni distructive.
- **Reading support**: mărime text ajustabilă, înălțime de linie și spațiere caractere configurabile, citire cu voce tare via `speechSynthesis` (ro-RO).
- **Voice / hearing**: recunoaștere vocală via Web Speech API (`ro-RO`) cu fallback la tastare/lipire; transcrieri ca text; fără inferențe de emoție din voce sau față.
- **Forms**: etichete vizibile asociate explicit (`label[for]`), mesaje de eroare legate prin `aria-describedby`.
- **Fără CDN-uri externe**: aplicația este 100% offline-safe, autonomă și respectă intimitatea utilizatorului.

---

## 7. Test every UI task (evidence required in your report)
1. `./scripts/check.sh` (include `tests/test_a11y_static.py` și `tests/web/prefs/test_tokens.py`).
2. **Keyboard-only pass**: parcurge întregul flux exclusiv din tastatură; notează ordinea de tab și verifică vizibilitatea inelului de focus.
3. **Screen reader pass** (Orca pe Linux, NVDA pe Windows, VoiceOver pe macOS): testează fluxul cu ochii închiși 3 minute; asigură-te că toate acțiunile sunt anunțate.
4. **Zoom/contrast pass**: 200% zoom browser, comutare contrast (Soft, Dark, Light), testare la lățime de 320px.
5. Verifică absența completă a steluțelor ✨ și a font-weight 300.
