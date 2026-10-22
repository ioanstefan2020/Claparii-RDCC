# Audit de Accesibilitate & Matricea QA (WCAG 2.2 AA & AAA) — PrimaZi

> Document creat și asumat de echipa PrimaZi (rol P2: Accessibility Engine & QA)  
> Data: 22–23 Octombrie 2026 | Hackathon AccessABILITY 2026  
> Conformitate țintă: **WCAG 2.2 Nivel AA** (integral) și **Nivel AAA** (pe contrast, spațiere, navigare și fără limită de timp).

---

## 1. Rezumat Executiv

Pentru persoanele cu dizabilități sau neurodivergente la primul loc de muncă, accesibilitatea nu este o simplă bifă tehnică, ci diferența dintre autonomie profesională și abandon. Aplicația **PrimaZi** a fost proiectată conform principiului *Accessible by Design*, combinând standardele internaționale WCAG 2.2 cu arhitectura vizuală confortabilă și odihnitoare („Focus Bubble” inspirată din Gemini), eliminând suprastimularea senzorială și garantând controlul deplin al utilizatorului.

---

## 2. Medii de Testare & Instrumente Utilizate

- **Sisteme de Operare:** Linux (Ubuntu 24.04 LTS), Windows 11 Pro, macOS Sonoma.
- **Cititoare de Ecran (Screen Readers):**
  - **Orca** (v46 pe Linux / GNOME)
  - **NVDA** (v2024.1 pe Windows / Firefox & Edge)
  - **VoiceOver** (macOS & iOS)
- **Motoare de Randare:** Chromium (Edge, Chrome), Gecko (Firefox), WebKit (Safari).
- **Instrumente Automate:** `tests/test_a11y_static.py`, `tests/web/test_contrast.py`, `tests/web/test_a11y_comprehensive.py`, axe-core linter static.
- **Instrumente de Simulare:** Emulare Color Vision Deficiency (Chrome DevTools), navigare exclusivă cu comutatoare și tastatură USB standard.

---

## 3. Matricea de Verificare pe 9 Dimensiuni de Accesibilitate

| # | Dimensiune WCAG | Criterii Verificate | Rezultat | Note & Remedieri Aplicate |
|---|---|---|---|---|
| **D1** | **Navigare Exclusiv din Tastatură** | 2.1.1 (Tastatură), 2.1.2 (Fără Capcane), 2.4.3 (Ordine Focus), 2.4.7 (Focus Vizibil) | **ADMIS (PASS)** | Skip-link prezent pe toate ecranele; inel de focus de 3px solid cu offset 2px (`#005fb8` / `#e89250`), zero capcane tastatură (`Escape` închide orice sertar/meniu). |
| **D2** | **Cititor de Ecran (Screen Reader)** | 1.3.1 (Informație & Relații), 4.1.2 (Nume/Rol/Valoare), 4.1.3 (Mesaje de Stare) | **ADMIS (PASS)** | Rădăcină `<html lang="ro">` pe 100% din pagini; un singur `<h1>` semantic per ecran; regiune `aria-live="polite"` pentru operațiuni asincrone; iconițe decorative marcate cu `aria-hidden="true"`. |
| **D3** | **Zoom 200% & Reflow la 320px** | 1.4.4 (Redimensionare Text), 1.4.10 (Reflow Fără Defilare Orizontală) | **ADMIS (PASS)** | Scalare fluidă la 200% fără trunchiere de text; la 320px lățime toate grilele se transformă într-o singură coloană verticală; bara laterală devine un sertar accesibil cu buton dedicat. |
| **D4** | **Contrast Ridicat & Teme Calde** | 1.4.3 (Contrast Minim AA 4.5:1), 1.4.6 (Contrast Îmbunătățit AAA 7:1) | **ADMIS (PASS)** | 7 teme măsurate matematic (`soft`, `amber`, `sapphire`, `hc-dark`, `hc-light`, `mono`, `night`). Textul depășește 10:1 (până la 19.5:1 în High Contrast). Controalele depășesc 4.5:1. |
| **D5** | **Mișcare Redusă & Calmare Senzorială** | 2.2.2 (Pauză/Oprire/Ascundere), 2.3.3 (Animații din Interacțiune) | **ADMIS (PASS)** | Suport complet `@media (prefers-reduced-motion: reduce)` și `[data-motion="reduced"]`. Toate tranzițiile devin instantanee (0.001ms), fără animații continue, fără fundaluri pulsatorii, fără steluțe AI (✨). |
| **D6** | **Simulare Discromatopsie (CVD)** | 1.4.1 (Utilizarea Culorii) | **ADMIS (PASS)** | Categoriile de evidențiere nu se bazează doar pe culoare: folosesc iconițe distincte, prefixe textuale și stiluri de subliniere diferite (linie dublă pentru acțiuni, punctată pentru atenționări). Verificat pentru Protanopie, Deuteranopie, Tritanopie. |
| **D7** | **Persoane Hipoacuzice & Surde** | 1.2.1, 1.2.2 (Subtitrări și Transcriere Text) | **ADMIS (PASS)** | Modulul de transcriere audio (`/api/transcribe`) generează automat atât text integral, cât și subtitrări sincronizate `.srt` și `.vtt` cu marcaje temporale fidele. Ședințele oferă sinteză text a deciziilor fără pierderea informației verbale. |
| **D8** | **Accesibilitate Motorie & Ținte Tactile** | 2.5.5 (Dimensiune Țintă 44px+), 2.5.8 (Spațiere Între Ținte) | **ADMIS (PASS)** | Toate butoanele și câmpurile interactive respectă dimensiunea minimă de 48×48px (`--min-touch-target: 48px`), cu spațiere de siguranță de minim 12px între elemente alăturate, prevenind apăsările accidentale. |
| **D9** | **Cognitiv & Neurodiversitate (ADHD/Autism)** | 2.2.1 (Timp Ajustabil), 3.1.5 (Nivel de Citire Simplu) | **ADMIS (PASS)** | Modurile de concentrare 0–3 permit afișare pas cu pas ("Pasul 2 din 6"), riglă vizuală de lectură (`ruler.js`), delimitare vizuală a paragrafelor, fără expirări de sesiune, fără cronometre stresante. |

---

## 4. Raport Detaliat pe Categorii de Utilizatori

### 4.1. Utilizatori Nevăzători și Slab-Văzători (Cititor de Ecran & Contrast)
- **Comportament Verificat:**
  - Navigarea prin tastele `H` (Headings) în NVDA și Orca relevă o structură ierarhică impecabilă: `h1` (titlu pagină) urmat de `h2` pentru secțiuni logice.
  - Formularele au etichete explicite conectate prin `for="..."` / `id="..."`.
  - Nu există butoane oarbe („button”, „click here”). Butoanele de redare audio au etichete clare dinamice: „Ascultă instrucțiunile”, „Pauză redare”, „Oprește lectura”.
  - Anunțurile de sistem (ex: „Document analizat cu succes — 4 pași generați”) sunt transmise prin `#status-live` cu `aria-live="polite"`.
- **Contrast Măsurat pe Teme (verificat în `test_contrast.py`):**
  - **Soft (Crem/Cărbune):** Text `#1e2022` pe fundal `#f9f9f7` -> **14.8:1** (Depășește pragul AAA de 7:1).
  - **High-Contrast Dark:** Galben `#ffff00` pe negru `#000000` -> **19.5:1** (AAA).
  - **High-Contrast Light:** Text `#000000` pe alb `#ffffff` -> **21.0:1** (AAA maxim).
  - **Night (Velvet Dark):** Text `#f0ede6` pe fundal `#131314` -> **15.2:1** (AAA).

### 4.2. Persoane cu Dislexie și Dificultăți de Procesare a Textului
- **Tipografie Confortabilă:**
  - Integrarea fontului *Atkinson Hyperlegible* (Braille Institute) elimină confuziile clasice de caractere (I mare vs. l mic vs. cifra 1; cifra 0 vs. litera O).
  - Comutator rapid pentru fontul *OpenDyslexic*, cu mărirea automată a spațierii dintre litere (`letter-spacing: 0.12em`) și a înălțimii de rând (`line-height: 1.6`).
  - Riglă vizuală de ghidaj pe orizontală (`ruler.js`) pentru utilizatorii care pierd rândul la citit.

### 4.3. Persoane cu ADHD, Autism sau Sensibilitate Senzorială
- **Calm Senzorial:**
  - Zero elemente pulsatorii, zero „glow” sau neon violet.
  - Centrare calmă în „Focus Bubble” (lățime maximă 768px), prevenind oboseala cauzată de parcurgerea ochilor pe ecrane ultrawide.
  - Modul de defalcare „Pe pași mici” transformă documentele stufoase în sarcini unitare afișate una câte una, cu indicator clar de progres („Pasul 1 din 4”) și butoane mari „Pasul următor”.

### 4.4. Persoane cu Dizabilități Auditive (Surzi sau Hipoacuzici)
- **Canale Alternative Vizuale:**
  - Orice înregistrare audio sau discuție de la locul de muncă este transcrisă cu fidelitate text prin `/api/transcribe`.
  - Subtitrări standard `.srt` și `.vtt` generate sincronizat, permițând importul în orice player video sau platformă de instruire internă.
  - Deciziile și sarcinile de echipă sunt extrase structurat în scris, cu persoana responsabilă și termenul limită menționate explicit.

### 4.5. Persoane cu Tremur sau Dificultăți Motorii
- **Tinte de Apăsare Generoase:**
  - Butoanele au o zonă minimă de atingere de 48×48 pixeli.
  - Spațiu de 12–16 pixeli între controale pentru a preveni activarea eronată.
  - Scurtături de tastatură globale accesibile prin tasta `?` (fără scurtături pe o singură tastă fără modificator în câmpurile de text).
  - Buton explicit de „Anulare” (Undo) pentru acțiunile de ștergere din planificator.

---

## 5. Remedieri și Îmbunătățiri Aplicate în Cod

1. **Eliminarea Font-Weight 300:** Înlocuit cu minimum `400` / `500` pentru a preveni subțierea literelor pe ecrane non-retina.
2. **Corectarea Contrastului pe Accentul Albastru:** Trecerea de la `#1D4ED8` (6.36:1) la `#1E40AF` (8.27:1) pentru a satisface fără echivoc standardul WCAG AAA pentru text.
3. **Păstrarea Focusului Vizibil la Navigarea din Tastatură:** Toate containerele și butoanele au fost stilizate cu `:focus-visible { outline: 3px solid var(--focus-ring); outline-offset: 2px; }`.
4. **Scrubbing Termeni Clinici:** Implementat filtru regex atât în client cât și pe server (`profile.py`) pentru a preveni etichetarea sau afișarea diagnosticelor medicale.
5. **Prevenirea Flash-ului de Conținut Nestilizat (Anti-FOUC):** Scriptul `boot.js` din `<head>` aplică atributele `data-*` înainte de randarea corpului paginii.

---

## 6. Limite Cunoscute și Asumate Onest (Known Limitations)

1. **Variația Calității Vocilor de Sinteză TTS:**
   - Sinteza vocală nativă în browser oferă o calitate excepțională pe Microsoft Edge (vocile „Online (Natural) Emil / Alina”), dar pe anumite distribuții Linux sau versiuni vechi de Chrome, sinteza browserului poate suna metalic. Pentru acestea, oferim fallback-ul pe server cu modelul offline Piper (`ro_RO-mihai-medium`).
2. **Documente PDF Scanate Fără Strat Text (OCR):**
   - Fișierele PDF pur imagine necesită un modul suplimentar de OCR pe server; aplicația informează utilizatorul prietenos și sugerează descrierea prin modulul vizual sau copierea textului direct.
3. **Nuanțe de Ton (Umor / Ironie):**
   - Conform cercetărilor recente (ACL 2026), modelele AI au o rată de eroare ridicată la detectarea umorului și sarcasmului. Din acest motiv, notele de ton din PrimaZi sunt pur indicative („posibilă glumă — nesigur”), dezactivate implicit și bazate strict pe citate textuale, fără a deduce stări emoționale din voce (conformitate strictă cu Regulamentul European privind Inteligența Artificială - EU AI Act).

