# PrimaZi — Asistent Accesibil pentru Primul Loc de Muncă

[![Quality Gate](https://img.shields.io/badge/Gate-PASS-success)](scripts/check.sh)
[![Accessibility](https://img.shields.io/badge/Accessibility-WCAG%202.2%20AA%20Target-blue)](web/shared/a11y.css)
[![Responsible AI](https://img.shields.io/badge/Responsible%20AI-Grounding%20%2B%20Zero%20Diagnosis-purple)](app/safety.py)
[![Offline Capable](https://img.shields.io/badge/Demo-100%25%20Offline%20Safe-green)](web/shared/fixtures)

> **AccessABILITY Hackathon 2026** — *"First Job, Full Potential: AI for an Inclusive Start at Work"*  
> **Echipa:** P1 (AI Core & Backend) · P2 (Employee Experience & Accesibilitate) · P3 (Employer Side, Conținut, Dovezi & Prezentare)  
> **Limbă:** Română (ro) nativ pentru interfață și toate rezultatele AI.

---

## 1. Ce este PrimaZi?

Tranziția către primul loc de muncă este o etapă copleșitoare pentru tinerii cu dizabilități sau neurodivergență: ghiduri stufoase de onboarding pline de jargon corporatist, e-mailuri cu instrucțiuni ambigue, ședințe rapide și o teamă firească de a cere adaptări la locul de muncă (mulți tineri ezitând să își dezvăluie diagnosticul). În același timp, angajatorii și echipele de HR nu dispun adesea de instrumente practice pentru a audita materialele interne și pentru a ști ce adaptări funcționale să ofere.

**PrimaZi adaptează locul de muncă la persoană.**  
Este o platformă bivalentă (Angajat & Angajator), proiectată de la zero pentru **accesibilitate cognitivă, senzorială și motorie**, care simplifică comunicarea profesională fără a compromite confidențialitatea.

```
                            ┌───────────────────────────────────┐
                            │              PrimaZi              │
                            │   AI pentru un start incluziv     │
                            └─────────────────┬─────────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
     ┌─────────────────────────────┐                     ┌─────────────────────────────┐
     │      PENTRU ANGAJAȚI        │                     │      PENTRU ANGAJATORI      │
     ├─────────────────────────────┤                     ├─────────────────────────────┤
     │ • Profil nevoi (local)      │                     │ • Audit accesibilitate doc  │
     │ • Clarificare documente     │                     │ • Scor lizibilitate 0-100   │
     │ • Planificator + export .ICS│                     │ • Detecție jargon cu citat  │
     │ • Asistent ședințe (text)   │                     │ • Rescriere Easy-to-Read    │
     │ • Cerere adaptări de lucru  │                     │ • Checklist adaptări HR     │
     └─────────────────────────────┘                     └─────────────────────────────┘
```

---

## 2. Funcționalități Cheie (MVP)

### Pentru Angajați (Employee Experience)
- **F1. Profil de Nevoi și Confort (Device-Only):** Utilizatorul își setează preferințele de citire (nivel de simplitate, pași scurți, mărime text, contrast ridicat) și nevoile specifice *în propriile cuvinte*. **Fără câmpuri medicale sau diagnostice.** Datele rămân 100% locale în `localStorage`. Buton dedicat „Șterge datele mele”.
- **F2. Clarificarea Documentelor (`/employee/clarify.html`):** Lipește sau încarcă un ghid de onboarding/regulament → obține rezumat în limbaj clar, pași cronologici numerotați, glosar de termeni și întrebări de adresat managerului. Butonul **„Arată în text”** evidențiază instantaneu fragmentul original garantat prin citat exact. Lectură cu voce tare (TTS).
- **F3. Planificator și Export Calendar (`/employee/plan.html`):** Extrage automat sarcinile și termenele limită din e-mailuri sau instrucțiuni. Dacă un termen este vag („cât mai repede”), sistemul **nu inventează o dată**, ci marchează sarcina cu alertă de confirmare. Export direct în fișier calendar standard **`.ics`** (RFC 5545).
- **F4. Asistent pentru Ședințe (`/employee/meeting.html`):** Transcriere vocală live (`ro-RO`) sau lipire de text → extrage decizii, acțiuni cu persoană responsabilă (`who`) și puncte neclare. **Strict text-only: zero inferență de emoții din voce sau mimică** (conformitate strictă cu Regulamentul European privind Inteligența Artificială - EU AI Act).
- **F5. Solicitare de Adaptări Fără Diagnostic (`/employee/adjustments.html`):** Angajatul selectează nevoi funcționale (ex: instrucțiuni scrise, spațiu liniștit, program flexibil) dintr-un catalog curat legislativ și generează un e-mail politicos către HR/manager, **fără a menționa vreun diagnostic medical**.

### Interfață Unificată (Gemini Shell) & Confort Cognitiv
- **Chestionar de Bun Venit cu Previzualizare Activă (`/welcome.html`):** 7 întrebări prietenoase în limbaj natural; stilurile (culori, font, spațiere) se actualizează reactiv în timp real în panoul de previzualizare.
- **Panou de Control Confort (`/settings.html`):** Gestionare completă a preferințelor vizuale și cognitive, resetare parțială sau totală cu dialog de confirmare accesibil și export/import JSON offline pentru transfer fără server.
- **Bibliotecă Locală de Lucru (`/library.html`):** Stocare 100% în browser (`localStorage`) a documentelor și planurilor analizate, cu căutare live, filtrare, vizualizare modală cu citate ancorate și ștergere cu toast de anulare (undo de 7 secunde).

### Pentru Angajatori & HR (Employer Side)
- **F6. Audit de Accesibilitate Cognitivă a Documentelor (`/employer/index.html`):**
  - **Scor de lizibilitate determinist (0–100):** Calculat matematic în cod (număr fraze, medie cuvinte/frază, prag fraze lungi $\ge 25$ cuvinte, protecție abrevieri românești `str.`, `nr.`, `art.`, `et.`, `ap.` și numere zecimale). Evaluează **documentul, niciodată un om**.
  - **Identificare probleme cu citat exact (Grounding):** Evidențiază jargonul corporatist, frazele excesiv de lungi și instrucțiunile vagi, oferind reformulări concrete.
  - **Rescriere Easy-to-Read (Limbaj Simplificat):** Transformă textul dens într-un format aerisit, cu pași clari, diacritice și repere vizuale. Butoane de copiere, descărcare (`.txt`) și lectură vocală.
  - **Checklist de adaptări recomandate:** Sugestii concrete de organizare a muncii mapate pe catalogul de bune practici.

---

## 3. Pornire Rapidă (Local Setup)

Aplicația este construită pe o arhitectură simplă și robustă (FastAPI + Vanilla ES Modules), care **nu necesită build tools** (Webpack/Vite/Node) și **funcționează 100% offline** în modul demonstrativ implicit.

### 1. Clonare și creare mediu virtual
```bash
git clone https://github.com/ioanstefan2020/Claparii-RDCC.git hackathon
cd hackathon

# Creează și activează mediul virtual Python
python3 -m venv .venv
source .venv/bin/activate

# Instalează dependențele minimale
pip install -r requirements.txt
```

### 2. Configurare variabile de mediu
```bash
cp .env.example .env
```
*Notă:* Valoarea implicită `LLM_PROVIDER=mock` din `.env` permite rularea completă a tuturor fluxurilor din interfață și API **fără a avea nevoie de chei API comerciale**.

Dacă dorești conectarea la LLM-uri reale în limba română:
```bash
# În .env:
LLM_PROVIDER=gemini       # sau deepseek
GEMINI_API_KEY=cheia_ta   # sau DEEPSEEK_API_KEY
```

### 3. Pornire server de dezvoltare
```bash
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Deschide în browser: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 4. Testare și Porți de Calitate

Proiectul impune o poartă unică de verificare automată înainte de orice livrare:

```bash
# Rulează întreaga poartă de verificare:
# 1) Verificare linting & stil
# 2) Suita completă de teste pytest (backend, a11y, contracte, smoke)
# 3) Testul end-to-end pe port efemer (scripts/smoke.sh)
./scripts/check.sh
```

### Teste specifice:
```bash
# Teste statice de accesibilitate WCAG 2.2 AA (parcurge fiecare fișier HTML)
python3 -m pytest tests/test_a11y_static.py -v

# Testul de fum cap-la-cap (pornește uvicorn, verifică endpoint-urile și paginile HTML)
bash scripts/smoke.sh

# Teste backend (contracte, guardrails, evaluare lizibilitate, securitate)
python3 -m pytest tests/backend/ -v
```

---

## 5. Accesibilitate prin Design (WCAG 2.2 AA)

Accesibilitatea a fost integrată încă din prima linie de cod, conform standardelor WCAG 2.2 nivel AA:

| Categorie de Nevoi | Bariere uzuale la locul de muncă | Soluția PrimaZi | Verificare |
|---|---|---|---|
| **Cognitive & Neurodivergență** (ADHD, Spectru Autist, Dislexie) | Supraîncărcare de informație, fraze lungi și jargon, termene limită vagi | Nivel de lectură simplificat, descompunere în pași numerotați, evidențierea termenilor cheie, avertizări pentru date ambigue, modul „Simple mode”. | Teste de lizibilitate, inspecție vizuală, interviuri utilizatori. |
| **Vedere** (Nevăzători, Vedere scăzută, Daltonism) | Lipsă etichete cititor ecran, contrast slab, text greu scalabil | Marcaj semantic (`<main>`, `<nav>`, `<header>`), skip link direct la conținut, `aria-live` pentru rezultate dinamice, contrast $\ge 7:1$ (mod High-Contrast), scalare 200% fără orizontal scroll. | `tests/test_a11y_static.py`, navigare exclusivă cu tastatura, cititor de ecran. |
| **Auz** (Hipoacuzie, Surditate) | Ședințe verbale rapide, lipsă suport scris | Asistent de ședințe cu transcriere textuală, rezumat scris al deciziilor, catalog de adaptări (cereri pentru instrucțiuni scrise). | Teste mock/speech, validare format text. |
| **Motorie & Dexteritate** | Dificultate la click-uri fine, navigare imposibilă doar din tastatură | Ținte de atingere $\ge 44 \times 44\text{ px}$, ordine de tab logică, inel de focus vizibil (outline 3px), lipsă `tabindex` pozitiv, comenzi rapide. | Walkthrough complet fără mouse, verificare focus ring. |

### Limite asumate onest:
- Sinteza vocală (TTS) depinde de vocile de limbă română (`ro-RO`) instalate la nivelul sistemului de operare al utilizatorului.
- Recunoașterea vocală live folosește Web Speech API (disponibilă în browsere moderne bazate pe Chromium). Pentru browsere fără suport, există calea principală garantată: lipirea transcrierii text.

---

## 6. Inteligență Artificială Responsabilă (Responsible AI)

1. **Grounding Verificabil pe Citate Reale:**  
   Orice sarcină, termen limită sau problemă de jargon identificată include câmpul `source_quote`. Funcția [`app.guardrails.verify_quotes`](file:///home/kyuubi/Desktop/Claparii-RDCC/app/guardrails.py) verifică dacă citatul apare cuvânt cu cuvânt în textul original. Citatele inventate de AI sunt **eliminate automat**, iar utilizatorul primește o avertizare transparentă în `meta.warnings`.
2. **Confidențialitate Extremă a Datelor de Sănătate:**  
   Nu stocăm și nu cerem diagnostice medicale. Lista neagră [`DENY_DIAGNOSIS_TERMS`](file:///home/kyuubi/Desktop/Claparii-RDCC/app/safety.py) blochează generarea de etichete clinice.
3. **Fără Inferență de Emoții la Locul de Muncă (EU AI Act):**  
   Ședințele sunt procesate strict textual. Niciun semnal vocal sau vizual nu este folosit pentru a deduce starea emoțională a angajatului.
4. **Protecție Împotriva Prompt Injection:**  
   Textul documentelor încărcate este marcat explicit în prompturi ca date nesigure (`untrusted data`), prevenind instrucțiunile rău-intenționate mascate în text.
5. **Redactare În Jurnale (Zero Content Logging):**  
   Când `LOG_CONTENT=false`, conținutul documentelor încărcate nu este scris niciodată în jurnalele de sistem sau fișiere temporare.

---

## 7. Arhitectură Tehnică pe Scurt

Arhitectura completă și diagramele Mermaid detaliate sunt documentate în [`docs/ARCHITECTURE.md`](file:///home/kyuubi/Desktop/Claparii-RDCC/docs/ARCHITECTURE.md).

- **Backend:** FastAPI, Pydantic v2 (validare cu `extra="forbid"`), `httpx`.
- **Auto-Discovery Routers:** Modulele din `app/routers/*.py` exportă un `router` montat dinamic de `app/main.py`.
- **Frontend:** Vanilla HTML5 / ES Modules / CSS Tokens (`a11y.css`), servit direct de FastAPI.
- **Providers AI:** Abstractizare unificată `app/llm/generate_json` suportând `mock` (implicit), `gemini` (`gemini-2.5-flash`), și `deepseek` (`deepseek-chat`). Cache pe disc pe bază de hash SHA-256.

---

## 8. Structura Proiectului

```
├── app/                        # Backend FastAPI
│   ├── main.py                 # Punct de intrare, auto-discovery rutere, erori
│   ├── config.py               # Configurații și variabile de mediu
│   ├── guardrails.py           # Verificarea citatelor (grounding)
│   ├── safety.py               # Securitate, redactare loguri, filtru diagnostice
│   ├── llm/                    # Abstracție provideri LLM (mock, gemini, deepseek)
│   ├── routers/                # Rutere FastAPI (simplify, plan, meeting, adjustments, employer)
│   ├── schemas/                # Scheme Pydantic v2
│   └── prompts/                # Prompturi optimizate în limba română
├── web/                        # Frontend accesibil (Vanilla ES modules)
│   ├── index.html              # Hub-ul principal de navigare
│   ├── employee/               # Zona Angajat (profile, clarify, plan, meeting, adjustments)
│   ├── employer/               # Zona Angajator (audit de lizibilitate și accesibilitate)
│   ├── shared/                 # Tokeni CSS (a11y.css), calendar (ics.js), profil, audio
│   └── i18n/                   # Dicționare de texte în limba română
├── data/                       # Catalog adaptări (adjustments_ro.json) și mostre de test
├── docs/                       # Documentație pentru juriu, arhitectură și dovezi
│   ├── ARCHITECTURE.md         # Document detaliat de arhitectură software
│   ├── CONTRACTS.md            # Specificația înghețată a interfețelor API
│   ├── PROJECT.md              # Viziunea proiectului, problema și răspunsul la criterii
│   ├── PLAN.md                 # Planul comun de dezvoltare și etapele
│   └── evidence/               # Ghid de interviuri, sinteză și pregătire Q&A
├── scripts/                    # Scripturi de automatizare (check.sh, smoke.sh, ship.sh, sync.sh)
└── tests/                      # Suite de testare automată (backend, static a11y, smoke)
```

---

## 9. Validare cu Utilizatori Reali

Proiectul a fost fundamentat prin discuții și interviuri realizate în cadrul AccessABILITY Hackathon 2026 cu:
1. **Candidați și tineri angajați cu dizabilități (senzoriale și neurodivergenți):** confirmând nevoia critică de a ști *„ce am de făcut exact și până când”* și reținerea majoră în a cere adaptări de frica discriminării.
2. **Reprezentanți ONG / Asociații de profil:** subliniind importanța ancorării adaptărilor în bune practici funcționale și legislație (Legea 448/2006, Codul Muncii), nu în diagnostice medicale.
3. **Specialiști HR / Recrutori:** evidențiind lipsa de timp și instrumente pentru a rescrie procedurile interne într-un limbaj simplu și accesibil.

Sinteza completă a interviurilor și răspunsurile pentru juriu sunt disponibile în [`docs/evidence/summary.md`](file:///home/kyuubi/Desktop/Claparii-RDCC/docs/evidence/summary.md) și [`docs/evidence/qa-prep.md`](file:///home/kyuubi/Desktop/Claparii-RDCC/docs/evidence/qa-prep.md).

---

## 10. Licență și Mențiuni
Dezvoltat cu pasiune de echipa **Claparii** pentru **AccessABILITY Hackathon 2026**.  
*Toate informațiile juridice oferite în aplicație au rol informativ și de bune practici la locul de muncă și nu reprezintă consultanță juridică.*
