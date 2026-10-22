# PrimaZi — Live Demo Script (3:00 min)

> **Hackathon:** AccessABILITY Hackathon 2026 — *"First Job, Full Potential"*  
> **Duration:** Exactly 3 minutes (180 seconds) during the 6-minute pitch.  
> **Persona:** **Ana**, 23 de ani, proaspătă absolventă cu profil neurodivergent (ADHD și anxietate socială), angajată în prima zi la o companie de tehnologie.  
> **Demo Host:** P2 (prezentare UI/a11y) & P3 (prezentare angajator/poveste).  
> **Primary URL:** `http://localhost:8000` (sau portul activ de prezentare).

---

## 1. Demo Timeline & Second-by-Second Runbook

| Timp | Ecran / Rută | Acțiune Demo (Ce face prezentatorul) | Ce spunem juriului (Spoken Script) |
|---|---|---|---|
| **0:00–0:15** | *Hero / Slides* | Deschide browserul pe `http://localhost:8000/welcome.html`. Mâinile vizibile pe tastatură. | „Faceți cunoștință cu Ana. Este la primul ei loc de muncă. Este entuziasmată, dar prima zi vine cu un munte de proceduri, termene vagi și frica de a cere adaptări. PrimaZi transformă această experiență.” |
| **0:15–0:35** | `/welcome.html` *(Configurare Confort)* | Apasă `Tab` și `Space` pentru a naviga prin cele 7 întrebări de confort. Bifează „Ritm liniștit” și „Spațiere generoasă”. Arată cum panoul din dreapta se adaptează instantaneu. | „În loc de formulare medicale invazive, Ana răspunde la 7 întrebări simple despre stilul de lucru. Nicio întrebare despre diagnostic! Preferințele se aplică instantaneu și sunt salvate exclusiv în browserul ei (`localStorage`).” |
| **0:35–1:05** | `/` *(Acasă - Clarificare)* | Navighează cu `Tab` și `Enter` la butonul „Ghid onboarding” din bara de mostre rapide. Apasă `Enter` pe „Clarifică documentul”. Se afișează pașii. Apasă pe «Arată în text» la Pasul 1. | „Ana primește ghidul de onboarding. Îl încarcă cu un singur click. Modelul extrage acțiunile clare în limbaj simplu. Iar pentru că AI-ul nu trebuie să halucineze, funcția «Arată în text» subliniază citatul exact din documentul original.” |
| **1:05–1:40** | `/employee/plan.html` *(Planificator)* | Clic pe „Planificator” în meniu. Clic pe „Încarcă e-mail exemplu”. Clic pe „Extrage sarcini”. Se observă badge-ul galben `[De confirmat]`. Selectează data manual din picker și apasă „Confirmă”. Clic pe „Descarcă în Calendar (.ics)”. | „Managerul îi trimite un e-mail cu o sarcină urgentă: «Am nevoie de raport cât mai repede». ChatGPT ar fi inventat o dată arbitrară. PrimaZi refuză să ghicească: marchează termenul ca «De confirmat». Ana alege data, confirmă, și descarcă un calendar standard `.ics` compatibil cu Google Calendar și Outlook.” |
| **1:40–2:15** | `/employee/meeting.html` *(Asistent Ședințe)* | Navigare la „Ședințe”. Clic pe „Încarcă transcriere exemplu”. Clic pe „Sintetizează ședința”. Se afișează deciziile și acțiunile cu responsabili (`who`). Clic pe „Adaugă în planificator”. | „Prima ședință de echipă este o avalanșă de informații. Asistentul extrage doar deciziile și sarcinile concrete asignate fiecărui coleg. Respectăm strict Directiva Europeană AI Act: zero clasificare emoțională din voce sau text. Cu un singur click, sarcinile trec direct în planificatorul personal.” |
| **2:15–2:40** | `/employee/adjustments.html` *(Adaptări)* | Navigare la „Adaptări”. Bifează „Instrucțiuni scrise” și „Timp suplimentar pentru sarcini noi”. Alege tonul „Prietenos”. Clic pe „Generează solicitarea”. Arată emailul gata redactat. | „Ana are nevoie de instrucțiuni scrise, dar nu știe cum să ceară fără stigmatizare. Selectează nevoile funcționale din catalogul nostru legal, iar PrimaZi redactează o cerere politicoasă și profesională către HR — fără nicio referire la diagnostic medical.” |
| **2:40–3:00** | `/employer/index.html` *(Zona Angajator)* | Navigare la „Zona Angajator”. Clic pe „Încarcă exemplu de onboarding”. Clic pe „Analizează documentul”. Prezintă Scorul de Lizibilitate (0-100), frazele lungi, versiunea Easy-to-Read și checklist-ul HR. | „Dar incluziunea este bilaterală. În portalul angajatorului, HR-ul auditează documentele interne: măsurăm lizibilitatea frazelor, detectăm jargonul și generăm o versiune Easy-to-Read cu recomandări proactive de adaptare. Astfel, locul de muncă se adaptează omului, nu invers.” |

---

## 2. Fail-Safe Runbook (Ce facem dacă ceva pică)

### Scenariul A: Wi-Fi-ul sălii sau conexiunea API pică
- **Soluție:** Aplicația rulează 100% offline în mod mock!
- **Comandă pornire locală:**
  ```bash
  LLM_PROVIDER=mock uvicorn app.main:app --port 8000
  ```
- **Argument pentru juriu:** „Sistemul este conceput offline-first, cu generare deterministică și caching local, garantând continuitatea activității chiar și fără acces la internet.”

### Scenariul B: Browserul are preferințe vechi sau date corupte
- **Soluție:** Resetare instantanee din consola browserului (`F12`):
  ```javascript
  localStorage.clear(); location.href = '/welcome.html';
  ```
- Sau click pe butonul dedicat din ecranul de setări: **„Resetează totul (Start over)”**.

### Scenariul C: Microfonul / Web Speech API nu este disponibil în browser
- **Soluție:** Pe pagina `/employee/meeting.html`, interfața detectează automat lipsa suportului audio și afișează butonul „Încarcă transcriere exemplu”. Nu depindem de microfonul sălii!

### Scenariul D: Sintetizatorul de voce (TTS) nu are pachetul `ro-RO` instalat pe laptop
- **Soluție:** Butoanele de redare audio au indicator vizual clar (`aria-pressed`). Dacă vocea lipsește, textul rămâne 100% lizibil pe ecran, conform principiului că sunetul este un canal secundar de accesibilitate.

### Scenariul E: Proiectorul sau conexiunea video a laptopului cedează complet
- **Soluție:** Backup video MP4 înregistrat cap-la-cap la 1080p60 cu subtitrări și cititor de ecran activat pe un stick USB și pe telefonul mobil.

---

## 3. Cheatsheet Comenzi Tastatură pentru Demo

Pentru a demonstra juriului conformitatea WCAG 2.2 AA Keyboard-Only:
- `Tab`: Navigare secvențială înainte între elementele interactive.
- `Shift + Tab`: Navigare înapoi.
- `Space`: Selectare opțiuni radio/checkbox, comutare tab-uri.
- `Enter`: Activare butoane primare și link-uri.
- `Tab` inițial la încărcarea paginii: Activează linkul invizibil **„Sari la conținutul principal”** (`.skip-link`). Apăsarea pe `Enter` mută focusul direct pe `<main id="main">`.

