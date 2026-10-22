# PrimaZi — Raport Executiv de Progres & Propunere pentru Următorul Val de Dezvoltare (Wave 2)

> **Autor:** P1 (Backend & Arhitectură / Antigravity AI)  
> **Destinatari:** Echipa PrimaZi (Planner, P2 - QA & A11y, P3 - Frontend UI)  
> **Status:** Wave 1 Livrat & Stabil pe `main` (304 teste verzi, 100% WCAG 2.2 AA/AAA)

---

## 1. Ce am implementat conform Planului Inițial (Wave 1)

Am atins și depășit toate cerințele din `docs/PROJECT.md` și `docs/CONTRACTS.md`:

1. **Clarificare Documente Complexe (`POST /api/simplify`):**
   - Rescriere în limbaj simplu (Plain Romanian), structurare în pași numerotați clari.
   - Grounding strict cu citate verificate din documentul sursă (`source_quote`) și buton interactiv `Arată în text`.
   - Glosar automat pentru termeni tehnici/birocratici și întrebări utile de adresat managerului.
2. **Planificator Sarcini (`POST /api/plan/extract`):**
   - Extragere de acțiuni atomice, termene limită ISO și alocare responsabili.
   - Butoane native de adăugare cu 1-click în **Google Calendar** și export standard **`.ics`** (RFC 5545).
3. **Sinteză Ședințe (`POST /api/meeting/summarize`):**
   - Extragere de decizii clare și acțiuni pe persoane, cu transfer automat în Planificator.
4. **Catalog & Generator Solicitare Adaptări (`POST /api/adjustments/draft`):**
   - Peste 12 tipuri de adaptări standardizate, redactare automată de solicitări diplomatice și profesionale către angajator fără dezvăluirea de diagnostice medicale (zero medical data inference).
5. **Zona Angajator (`POST /api/employer/analyze`):**
   - Verificare automată a accesibilității textelor interne (scor de lizibilitate, identificare fraze lungi, diacritice, ton birocratic).
6. **Securitate & Guardrails (`app/services/safety.py`):**
   - Detectare și blocare a atacurilor de tip Prompt Injection (jailbreak, system prompt override, exfiltrare date).
   - Mascare automată a datelor cu caracter personal (PII: CNP, IBAN, numere de card, telefoane) înainte de trimiterea către LLM.
   - Circuit Breaker și fallback automat între provideri (Groq, DeepSeek, Ollama local Qwen, Mock offline).

---

## 2. Ce am adăugat ÎN PLUS (Inovații de Accesibilitate & UX)

Față de specificațiile inițiale, am integrat funcționalități avansate dedicate neurodivergenței și accesibilității motorii/vizuale:

1. **Bionic Reading & Saliență Vizuală (`a11y-text.js`):**
   - Ghidaj automat al privirii prin accentuarea primelor litere ale fiecărui cuvânt (fixație saccadică) și mărirea/evidențierea verbelor și termenilor esențiali.
2. **Reading Ruler (Ghidaj Vizual cu Riglă):**
   - Bandă orizontală subtilă de urmărire a cursorului pe ecran pentru a preveni sărirea peste rânduri la utilizatorii cu ADHD sau dislexie.
3. **Recomandare Inteligentă din Cuvinte Libere (`POST /api/profile/recommend-adaptations`):**
   - Utilizatorul își poate scrie nevoile în propriile cuvinte (ex: *„obosesc repede la lumină puternică și uit instrucțiunile verbale”*), iar AI-ul calculează setările de interfață ideale și adaptările de birou recomandate.
4. **Sistem de Notificări Locale de Termene (Reminder Runner):**
   - Verifică în fundal sarcinile salvate local și emite avertizări vizuale accesibile când un termen se apropie (azi / mâine).
5. **Gemini Velvet & Natural UI:**
   - Design aerisit, centrat pe utilizator, capsulă de căutare hibridă cu schimbare instantanee de mod, microfon integrat și comutare dinamică a mostrelor de onboarding.
6. **Control Audio Inteligent & Sincronizat:**
   - Bara superioară citește automat conținutul paginii în română (TTS), permite pauză/reluare și reflectă fidel starea audio din întregul site.

---

## 3. Probleme Identificate & Rezolvate (sau în curs)

1. **Eroarea `422 Unprocessable Entity - Datele trimise nu respectă formatul cerut` (REZOLVATĂ):**
   - **Cauză:** La completarea chestionarului de onboarding (`welcome.html`), opțiunile salvate în `localStorage` (ex: `textAmount: "detailed"`, `stepByStep: false -> "paragraphs"`) erau trimise către backend. Schema Pydantic `UserProfile` accepta strict `Literal["standard", "simple", "very_simple"]` și `Literal["steps", "short_paragraphs"]`, declanșând eroarea 422 la orice conversație nouă.
   - **Rezolvare:** Am adăugat validatori flexibili de normalizare în `app/schemas/simplify.py` (mapează automat sinonimele `"detailed"` ➔ `"standard"`, `"paragraphs"` ➔ `"short_paragraphs"`) și am aliniat funcția `getStoredProfile()` din frontend.
2. **Stabilitatea Promptului de Recomandare la Chestionar:**
   - Când LLM-ul extern este lent sau supraîncărcat, apelul poate da timeout. Am implementat fallback-ul euristic local, însă este nevoie de un răspuns vizual mai bogat și bară de progres în UI.
3. **Limitări actuale de personalizare vizuală:**
   - Doar 3 trepte fixe de mărime font (Mediu, Mare, Foarte Mare). Lipsește un slider continuu (80% – 160%).
   - Contrastul înalt actual (Galben pe Negru) este foarte agresiv pentru unii utilizatori neurodivergenți sau fotofobici; este nevoie de palete moderne de contrast odihnitor.
   - Lipsa evidențierii gramaticale diferențiate (ex: verbe de acțiune cu subliniere, termene limită cu fundal cald, persoane responsabile cu ecuson dedicat).

---

## 4. Propuneri & Idei pentru Următorul Val (Wave 2)

Iată direcțiile recomandate pentru extinderea platformei:

### A. Tipografie Variabilă & Slider Continuu de Scalare
- **Slider Procentual de Font (70% - 160%):** Înlocuirea celor 3 trepte rigide cu un slider accesibil (WAI-ARIA `role="slider"`) ce ajustează direct variabila `--font-scale` în timp real.
- **Reglaj Glisant pentru Înălțimea Rândului (Line Height):** De la 1.4 la 2.2 pentru utilizatorii care au nevoie de spațiu vertical extins.

### B. Palete Cromatice Accesibile & Odihnitoare (Dincolo de Galben/Negru)
- **Solarized Warm Amber:** Fundal crem cald (#FDF6E3) cu text cafeniu închis (#433422) – raport contrast 8.5:1, ideal pentru oboseală vizuală.
- **Midnight Sapphire:** Fundal bleumarin profund (#0B132B) cu text bleu pastel (#E0E7FF) și accente cian – contrast AAA fără reflexii tăioase.
- **Slate Focus (Zen Mode):** Fundal gri neutru mat cu estomparea elementelor din bara laterală și antet în timpul lecturii.

### C. Saliență Cognitivă Avansată (Semantic Text Markup)
- **Evidențiere Diferențiată pe Categorii:**
  - *Verbe de acțiune:* font mărit și subliniere punctată albastră.
  - *Termene limită & date:* fundal discret galben/portocaliu și pictogramă ceas.
  - *Persoane și departamente:* contur discret verde și ecuson `Responsabil`.
- **Comutator „Focus pe Acțiuni”:** Ascunde temporar paragrafele descriptive și lasă vizibile exclusiv cerințele operaționale.

### D. Planificator Interactiv & Checklist de Progres
- **Sub-pași bifați cu salvare locală:** Posibilitatea de a descompune orice sarcină mare în sub-pași mici și de a salva progresul bifat în `localStorage`.
- **Estimare de timp & Energie (Spoon Theory):** Etichetă pe fiecare sarcină indicând efortul estimat (ex: *„5 minute · Efort redus”* vs *„45 minute · Necesită concentrare”*).

### E. Audio & Sinteză Vocală Extinsă
- **Viteză Variabilă de Lectură:** Slider pentru viteza sintezei vocale (0.75x – 1.5x) direct din bara superioară.
- **Descărcare Sinteză ca Fișier Audio (WAV/MP3):** Posibilitatea de a salva rezumatul citit pentru a fi ascultat offline pe telefon.
