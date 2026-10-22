# PrimaZi — Asistent Accesibil pentru Primul Loc de Muncă

[![Quality Gate](https://img.shields.io/badge/Gate-PASS-success)](scripts/check.sh)
[![Accessibility](https://img.shields.io/badge/Accessibility-WCAG%202.2%20AA%20%2F%20AAA-blue)](docs/SETTINGS-SPEC.md)
[![Responsible AI](https://img.shields.io/badge/Responsible%20AI-Grounding%20%2B%20Zero%20Diagnosis-purple)](app/safety.py)
[![Offline Capable](https://img.shields.io/badge/Demo-100%25%20Offline%20Safe-green)](data/samples/)

> **AccessABILITY Hackathon 2026** — _"First Job, Full Potential: AI for an Inclusive Start at Work"_  
> **Echipa:** P1 (AI Core & Backend) · P2 (Employee Experience & Accesibilitate) · P3 (Frontend UI Gemini-Style & Prezentare)  
> **Limbă:** Română (`ro-RO`) nativ pentru interfață, voce și toate rezultatele AI.

---

## 1. Ce este PrimaZi?

Tranziția către primul loc de muncă este o etapă copleșitoare pentru tinerii cu dizabilități sau neurodivergență: ghiduri stufoase de onboarding pline de jargon corporatist, e-mailuri cu instrucțiuni ambigue, ședințe rapide și o teamă firească de a cere adaptări la locul de muncă (mulți tineri ezitând să își dezvăluie diagnosticul). În același timp, angajatorii și echipele de HR nu dispun adesea de instrumente practice pentru a audita materialele interne și pentru a ști ce adaptări funcționale să ofere.

**PrimaZi adaptează locul de muncă la persoană.**  
Este o platformă incluzivă bivalentă (Angajat & Angajator), proiectată de la zero pentru **accesibilitate cognitivă, senzorială și motorie**, care simplifică comunicarea profesională fără a compromite confidențialitatea.

---

## 2. Funcționalități Cheie (Wave 2)

### Pentru Angajați (Employee Experience)

- **Clarificarea Documentelor (`/employee/clarify.html`):** Rescriere în limbaj clar conform standardelor _Easy-to-Read_ (Inclusion Europe), pași cronologici numerotați, glosar de termeni și întrebări de adresat managerului. Butonul **„Arată în text”** evidențiază instantaneu fragmentul original garantat prin citat exact.
- **Saliență Vizuală & Adnotare Semantică (`POST /api/annotate`):**
  - Strat determinist (rapid, gratuit): date, ore, sume (RON, EUR, %), ID-uri de formulare (`F-12`), atenționări.
  - Strat semantic: verbe de acțiune, roluri și persoane, termeni tehnici.
  - Strat pragmatic de ton: detectează cereri politicoase indirecte (`ar fi frumos să...`), expresii figurate și atenuează anxietatea. Ironia și glumele sunt etichetate prudent: `(posibilă glumă / ironie — nesigur)` cu încredere limitată la low/medium, respectând reglementările EU AI Act.
- **Transformare Multi-Modală (`POST /api/transform`):**
  - Moduri listă: `bullets` (≤ 15 cuvinte), `steps` (pași numerotați), `questions` (întrebări de clarificare), `glossary` (termeni explicați simplu).
  - Moduri text: `shorter` (comprimare la % țintă păstrând datele și sumele), `tldr` (1–2 fraze), `easy_read` (ușor de citit).
- **Planificator & Export Calendar (`POST /api/plan/extract`):** Extrage sarcini, acțiuni operaționale și termene relative rezolvate calendaristic. Termenele ambigue sunt semnalate obligatoriu pentru confirmare. Export `.ics` (RFC 5545).
- **Încărcare Documente în Memorie (`POST /api/extract-text`):** Parsare sigură fără scriere pe disc pentru fișiere PDF, DOCX, TXT, MD și HTML (până la 10 MB). Detectează automat PDF-urile scanate și semnalează `needs_ocr: true`.
- **Descriere Imagini & Grafice (`POST /api/describe-image`):** Suport pentru `alt_text`, extragere text (`read_text`), explicare grafice (`chart`) și formulare (`document`) prin modele de viziune (Gemini 2.0 Flash) cu avertizări de verificare.

### Pentru Angajatori & HR

- **Audit de Accesibilitate Cognitivă a Documentelor (`/employer/index.html`):**
  - **Scor de lizibilitate determinist (0–100):** Calculat matematic în cod (număr fraze, medie cuvinte/frază, prag fraze lungi $\ge 25$ cuvinte). Evaluează **documentul, niciodată o persoană**.
  - **Identificare probleme cu citat exact (Grounding):** Evidențiază jargonul corporatist, frazele excesiv de lungi și instrucțiunile vagi, oferind reformulări concrete.
  - **Checklist adaptări HR:** Sugestii concrete de organizare a muncii mapate pe catalogul de bune practici.

---

## 3. Pornire Rapidă (Local Setup)

### Varianta A: Rulare directă cu Python (Fără build step)

```bash
git clone https://github.com/ioanstefan2020/Claparii-RDCC.git hackathon
cd hackathon

# Creează și activează mediul virtual Python
python3 -m venv .venv
source .venv/bin/activate

# Instalează dependențele minimale
pip install -r requirements.txt

# Copiază configurarea implicită
cp .env.example .env

# Pornește serverul
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Deschide în browser: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### Varianta B: Rulare în Container Docker

```bash
# Construiește imaginea Docker
docker build -t primazi .

# Rulează containerul
docker run -p 8000:8000 --env-file .env primazi
```

---

## 4. Arhitectură Multi-Provider & Reziliență LLM

PrimaZi include un lanț de rezervă inteligent (fallback chain) cu monitorizare a disponibilității prin **Circuit Breakers**:

```bash
# Lanțul configurat în .env (încearcă furnizorii în ordine până la primul răspuns valid):
LLM_PROVIDER_CHAIN=groq,deepseek,ollama,mock

# Sau forțare furnizor specific:
LLM_PROVIDER=groq
```

- **Verificare Stare Furnizori:** `GET /api/llm/status` returnează starea fiecărui provider (`closed`, `open`, `half-open`), latența mediană $p50$, starea cheilor API și modelul activ.
- **Modelul Offline Mock:** Permite rularea aplicației și susținerea prezentării 100% offline, fără conexiune la internet sau chei API comerciale.

---

## 5. Testare și Porți de Calitate

Proiectul impune o poartă strictă de verificare automată înainte de orice livrare:

```bash
# Rulează întreaga poartă de verificare:
# 1) Verificare linting & stil
# 2) Suita completă de teste pytest (backend, a11y, contracte, wave 2)
# 3) Testul end-to-end pe port efemer (scripts/smoke.sh)
./scripts/check.sh
```

### Comenzi de test specifice:

```bash
# Teste backend (contracte, adnotare, transformare, ingestie, securitate)
PYTHONPATH=. pytest tests/backend/ -v

# Evaluare automată prompturi pe setul de date etalon românesc
PYTHONPATH=. pytest tests/eval/test_wave2_eval.py -v

# Teste statice de accesibilitate WCAG 2.2 AA pe fișierele HTML
python3 -m pytest tests/test_a11y_static.py -v
```

Raportul detaliat de evaluare a performanței și acurateței este disponibil în [`docs/evidence/eval.md`](docs/evidence/eval.md).

---

## 6. Inteligență Artificială Responsabilă (Responsible AI)

1. **Grounding Verificabil pe Citate Reale:** Orice sarcină, termen limită sau problemă de jargon identificată include câmpul `source_quote`. Citatele inventate de AI sunt **eliminate automat**, iar utilizatorul primește o avertizare transparentă în `meta.warnings`.
2. **Confidențialitate Extremă a Datelor de Sănătate:** Nu stocăm și nu cerem diagnostice medicale. `DENY_DIAGNOSIS_TERMS` curăță automat termenii clinici înainte de procesare.
3. **Fără Inferență de Emoții la Locul de Muncă (EU AI Act):** Ședințele sunt procesate strict textual. Niciun semnal vocal sau vizual nu este folosit pentru a deduce starea emoțională a angajatului.
4. **Protecție Împotriva Prompt Injection:** Delimitarea strictă `<<<DOCUMENT ... DOCUMENT>>>` izolează textul utilizatorului de instrucțiunile de sistem.

---

## 7. Licență și Mențiuni

Dezvoltat de echipa **Claparii** pentru **AccessABILITY Hackathon 2026**.  
_Toate informațiile juridice oferite în aplicație au rol informativ și de bune practici la locul de muncă și nu reprezintă consultanță juridică._
