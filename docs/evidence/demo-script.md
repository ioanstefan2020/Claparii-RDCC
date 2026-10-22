# PrimaZi — Scenariu Demonstrativ Live (3 Minute)

> **Destinat:** Prezentare Live Juriu — AccessABILITY Hackathon 2026  
> **Durată demo:** Exact 3:00 minute (în cadrul pitch-ului de 6:00 minute)  
> **Roluri:** 1 Prezentator (Speaker) + 1 Operator (Driver) la laptop.  
> **Persoană ilustrativă:** „Ana” — tânără absolventă neurodivergentă (ADHD / anxietate de comunicare), în prima ei zi ca asistent operațiuni.

---

## Pregătire Înainte de Intrare (Checklist Tehnic)

1. **Pornire server local:**
   ```bash
   python3 -m uvicorn app.main:app --port 8000 --host 127.0.0.1
   ```
2. **Deschidere tab-uri în browser:**
   - Tab 1: `http://localhost:8000/index.html` (Hub Principal)
   - Tab 2: `http://localhost:8000/employee/profile.html` (Profil & Confort)
   - Tab 3: `http://localhost:8000/employee/clarify.html` (Clarificare Document)
   - Tab 4: `http://localhost:8000/employee/adjustments.html` (Cerere Adaptări)
   - Tab 5: `http://localhost:8000/employer/index.html` (Audit Angajator)
3. **Stare inițială curată:**
   - Click pe butonul „Șterge toate datele mele” în `profile.html` pentru a porni de la zero.
4. **Plan B (Dacă pică conexiunea sau browserul):**
   - Aplicația rulează cu `LLM_PROVIDER=mock`, fiind 100% offline-safe.
   - Păstrați deschis folderul cu înregistrarea video de backup.

---

## Desfășurător Pas cu Pas (Cronometrat)

### Minutul 0:00 – 0:30 | Pasul 1: Profilul de Confort și Nevoi (Device-Only)
- **Acțiune Operator:**
  1. Pornește din Hub (`/index.html`), navighează la **„Profil & Nevoi”** (`/employee/profile.html`).
  2. Selectează:
     - Nivel de citire: **„Simplu (recomandat)”**
     - Format: **„Pași numerotați”**
     - Comută tema pe **„Contrast ridicat”** pentru 3 secunde pentru a demonstra suportul vizual, apoi revine pe modul dorit.
  3. În caseta de nevoi proprii scrie: *„Am nevoie de instrucțiuni scrise, fără noțiuni ambigue.”*
  4. Salvează profilul.
- **Discurs Speaker:**
  > *„Ana este în prima ei zi de muncă. În loc de formulare medicale invazive, Ana își configurează nevoile de lucru în propriile ei cuvinte, exclusiv pe laptopul personal. Nicio informație de diagnostic nu părăsește dispozitivul.”*

---

### Minutul 0:30 – 1:15 | Pasul 2: Ghidul de Onboarding și Funcția „Arată în text”
- **Acțiune Operator:**
  1. Trece pe ecranul **„Clarificare”** (`/employee/clarify.html`).
  2. Apasă butonul **„Încarcă exemplu”** (încarcă instant `data/samples/onboarding_ro.txt`).
  3. Apasă **„Simplifică documentul”**.
  4. La afișarea rezultatelor:
     - Arată sinteza clară și pașii numerotați.
     - Dă click pe butonul **„Arată în text”** de la Pasul 1 → ecranul derulează lin și evidențiază cu galben citatul exact din textul original.
     - Pornește 3 secunde sinteza vocală (TTS) pe butonul **„Citește cu voce tare”**.
- **Discurs Speaker:**
  > *„Ana primește un ghid stufos de 4 pagini plin de acronime. PrimaZi îl transformă în 5 pași concreți. Observați funcția noastră cheie de încredere: butonul «Arată în text» îi demonstrează Anei că fiecare pas este ancorat matematic într-un citat real din document. Fără halucinații, fără presupuneri.”*

---

### Minutul 1:15 – 1:50 | Pasul 3: Momentul de Siguranță AI (Termen Limită Ambiguu)
- **Acțiune Operator:**
  1. Trece în Planificator (`/employee/plan.html`) sau prezintă analiza pe e-mailul de sarcini.
  2. Arată sarcina extrasă din e-mailul cu textul: *„Trimite raportul cât mai repede, până joi la prânz.”*
  3. Evidențiază insigna galbenă: **„Necesită confirmare: Termen ambiguu detectat”**.
  4. Apasă butonul **„Descarcă fișier calendar (.ics)”**.
- **Discurs Speaker:**
  > *„Iată un moment critic de AI Responsabil: un e-mail spune «trimite raportul cât mai repede». Alte unelte AI inventează o dată la întâmplare, creând panică. PrimaZi refuză să ghicească: marchează termenul ca ambiguu, cere confirmarea Anei și exportă totul direct în calendarul ei prin fișier standard ICS.”*

---

### Minutul 1:50 – 2:25 | Pasul 4: Solicitarea de Adaptări Fără Diagnostic
- **Acțiune Operator:**
  1. Navighează la ecranul **„Adaptări”** (`/employee/adjustments.html`).
  2. Bifează din catalogul legislativ două opțiuni:
     - `[x] Instrucțiuni scrise, pas cu pas`
     - `[x] Timp suplimentar la sarcini noi`
  3. Apasă **„Generează cererea”**.
  4. Rezultat: apare scrisoarea oficială, redactată respectuos și profesionist către HR/manager.
  5. Apasă **„Copiază textul”** sau **„Trimite pe e-mail (mailto)”**.
- **Discurs Speaker:**
  > *„Ana vrea să ceară sprijin, dar îi este teamă de discriminare. În loc să fie forțată să spună «am ADHD», PrimaZi selectează adaptări funcționale din legislația română și îi generează o cerere politicoasă și asertivă, fără niciun stigmat medical.”*

---

### Minutul 2:25 – 3:00 | Pasul 5: Zona Angajator — Închiderea Cercului de Incluziune
- **Acțiune Operator:**
  1. Intră în **„Zona Angajator”** (`/employer/index.html`).
  2. Apasă **„Încarcă exemplu de onboarding”** și apasă **„Analizează documentul”**.
  3. Arată:
     - **Scorul de lizibilitate:** *68/100 (Accesibilitate moderată)* calculat determinist.
     - **Problemele identificate:** Jargon corporatist (*„autonomie operațională”*), fraze de 34 de cuvinte.
     - **Rescrierea Easy-to-Read:** versiune simplificată gata de trimis noilor colegi.
     - **Checklist-ul de adaptări recomandate pentru HR**.
- **Discurs Speaker:**
  > *„Soluția este completă doar când ajutăm și angajatorul. HR-ul trece același document prin PrimaZi: primește un audit obiectiv de lizibilitate, identifică jargonul cu citate exacte și descarcă o versiune Easy-to-Read gata de oferit oricărui nou angajat. În 3 minute, am transformat o barieră într-o punte de comunicare incluzivă.”*

---

## Plan de Rezervă În Caz de Probleme Tehnice

| Problemă | Acțiune Imediată a Operatorului | Ce spune Speakerul |
|---|---|---|
| **Pica serverul local uvicorn** | Treci pe tab-ul deschis cu `?mock=1` (fixtures locale statice). | *„Aplicația funcționează complet offline, utilizând fișele de test integrate în browser.”* |
| **Nu funcționează vocea TTS pe laptop** | Menționează că sinteza depinde de motorul OS și arată textul transcris. | *„Textul este structurat cu contrast optim pentru a asigura parcurgerea vizuală facilă.”* |
| **Mouse-ul sau trackpad-ul nu răspunde** | Folosește exclusiv tastatura: `Tab`, `Shift+Tab`, `Enter`, `Space`. | *„Observați navigarea exclusivă din tastatură, respectând WCAG 2.2 AA.”* |
