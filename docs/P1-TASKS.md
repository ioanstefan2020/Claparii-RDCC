# P1-TASKS.md: de la MVP la produs real (taskuri pentru P1)

Pune fișierul în `docs/P1-TASKS.md`, fă commit și anunță echipa. Căile și id-urile sunt presupuneri: nu am văzut repo-ul tău. Ajustează-le înainte să le dai agentului.

---

## 0. Ce înseamnă "produs real" aici

Diferența dintre demo și produs:

| Demo (acum) | Produs (țintă) |
|-------------|----------------|
| Eșantioane din `data/samples/`, fixtures | Orice document introdus de utilizator: lipit, .txt, .docx, .pdf, .eml, imagine |
| Un singur fel de output | Output adaptat nevoilor alese de utilizator |
| Valori hardcodate în răspuns | Totul calculat din documentul real, verificat în cod |
| "Merge pe laptopul meu" | Teste, evaluări, erori clare, deploy, limite, log fără date personale |

### Realitate despre timp
Un produs complet nu se termină în câteva ore. Fiecare task are un nivel:

- **A** = se face înainte de FREEZE. Face diferența dintre demo și produs real.
- **B** = dacă rămâne timp.
- **C** = roadmap post-hackathon. Îl pui în pitch ca "next steps", nu ca funcționalitate existentă.

**Regulă pentru pitch:** spui doar ce ai testat. Ce e în C este "planificat", nu "existent".

---

## 1. Decizii de produs (le luați împreună, 10 minute)

### 1.1 "Tipuri de dizabilități" devine "nevoi de acces"
Recomand cu tărie să **nu** construiți produsul pe etichete medicale ("autism", "dislexie", "surditate"), din trei motive:

1. Datele despre sănătate sunt categorie specială în GDPR (art. 9). Cât mai puțin de colectat, cu atât mai bine.
2. Oamenii cu același diagnostic au nevoi foarte diferite, iar oamenii fără diagnostic au aceleași nevoi.
3. Regula din AGENTS.md rămâne valabilă: fără inferență de diagnostic sau emoții.

Soluția: utilizatorul alege **ce îl ajută**, opțional, în limbaj simplu. Eticheta o poate alege sau nu, dar sistemul nu o cere și nu o deduce.

| Nevoie de acces (ce alege utilizatorul) | Exemple de adaptări în output |
|---|---|
| "Textul lung mă obosește" | Rezumat scurt întâi, apoi detalii; paragrafe de max 3 propoziții; nivel de simplificare 1 / 2 / 3 |
| "Am nevoie de pași clari" | Checklist numerotat, un singur lucru pe pas, estimare de timp |
| "Limbajul ambiguu mă încurcă" | Limbaj literal, fără idiomuri, termeni dificili explicați într-un glosar |
| "Citesc cu cititor de ecran / nu văd bine" | Structură semantică curată, fără tabele complicate, text alternativ, versiune audio (TTS) |
| "Nu aud / aud greu" | Totul în scris, rezumat de ședințe din transcript, alerte vizuale, fără apel telefonic ca pas obligatoriu |
| "Scrisul și tastatura mă obosesc" | Dictare, răspunsuri pregătite, ciorne de mesaje, pași puțini |
| "Mă obosesc repede / am energie limitată" | Task-uri împărțite în bucăți mici, prioritizare, "ce e cu adevărat urgent" |
| "Am nevoie de timp să decid" | Fără termene artificiale, "ce se întâmplă dacă aștept", ciornă salvată |

Aceste profiluri sunt **combinabile** și stau în `answers` / `prefs` (vezi CONTRACTS v2 de mai jos). Rămân în browser. Serverul primește doar flag-uri tehnice de adaptare (ex. `reading_level: 2`, `steps: true`), nu motivul pentru care le-a ales cineva.

### 1.2 Situații (module)
Ordinea de prioritate (A/B/C):

| Situație | Nivel | Exemple de input |
|---|---|---|
| Locul de muncă: onboarding, task-uri din email, ședințe | A | Existent la MVP, de făcut cu documente reale |
| Corespondență oficială: bancă, ANAF, primărie, asigurări | A | Scrisori, notificări, formulare |
| Contracte și regulamente | B | Contract de muncă, regulament intern |
| Școală / facultate | B | Cerințe de curs, regulamente, emailuri de la profesori |
| Instrucțiuni medicale (doar simplificare, fără sfaturi medicale) | C | Rețete, instrucțiuni de pregătire. Cere avertizare clară și revizuire de către un specialist înainte de lansare |
| Partea angajatorului: solicitare de ajustări rezonabile | A | Scrisoare/solicitare generată, catalog de ajustări |

### 1.3 Ce rămâne local, ce ajunge pe server
- **Local (browser):** profil de nevoi, preferințe, bibliotecă.
- **Server:** doar textul documentului, pe durata unei cereri, **fără stocare**, fără text în loguri.
- **Către LLM:** text cu date personale mascate acolo unde se poate (vezi P1-12).
- Dacă ulterior vreți conturi și sincronizare, asta e o decizie separată (C), cu criptare și consimțământ.

---

## 2. CONTRACTS v2 (P1 face PRIMUL task, ca P2 și P3 să lucreze în paralel)

### P1-00 (nivel A, 45-60 min): contractul v2
Scrie în `docs/CONTRACTS.md` și livrează fixtures reale pentru fiecare endpoint nou. Anunță în chat când e pe main.

Cererea comună de analiză:

```json
POST /api/v2/analyze
{
  "text": "...",                 // sau "file_id" după upload
  "language": "auto | ro | en",
  "situation": "auto | work | official | contract | school | medical",
  "adaptations": {
    "reading_level": 1,          // 1 = foarte simplu, 2 = simplu, 3 = original curățat
    "length": "short | medium | full",
    "steps": true,
    "glossary": true,
    "literal_language": true,
    "tts_ready": false
  },
  "outputs": ["summary", "actions", "deadlines", "glossary", "checklist"]
}
```

Răspuns:

```json
{
  "request_id": "...",
  "detected": {"language": "ro", "situation": "official", "confidence": 0.82},
  "summary": "...",
  "actions": [{"text": "...", "quote": "...", "quote_found": true}],
  "deadlines": [{"date": "2026-11-05", "text": "...", "quote": "...", "quote_found": true}],
  "glossary": [{"term": "...", "plain": "..."}],
  "checklist": [{"step": 1, "text": "...", "est_minutes": 5}],
  "warnings": [{"code": "UNCERTAIN_DATE", "message": "..."}],
  "metrics": {"readability_before": 41.2, "readability_after": 78.5, "words_before": 840, "words_after": 190},
  "usage": {"provider": "...", "latency_ms": 2300}
}
```

Reguli de contract:
- Orice `quote` este verificat în cod că apare în textul original. Dacă nu apare, `quote_found: false` și UI-ul arată avertizare.
- `warnings` e mereu prezent (poate fi gol). Frontend-ul îl afișează.
- Erori: `{ "error": { "code": "...", "message_ro": "...", "message_en": "...", "retryable": true } }`. Mesaje în limbaj simplu, niciodată stack trace.
- Streaming: `POST /api/v2/analyze/stream` (SSE), evenimente `progress`, `partial`, `done`.

Alte endpoint-uri în contract:
`POST /api/v2/upload`, `POST /api/v2/draft-reply`, `POST /api/v2/meeting-recap`, `POST /api/v2/adjustment-request` (angajator), `GET /api/v2/health`, `GET /api/v2/capabilities` (ce formate și limbi sunt active).

---

## 3. Taskuri P1

Fiecare task: scrii testele întâi, ceri planul de 5 rânduri, spui "ok go", rulezi `./scripts/check.sh`, rulezi tu singur, abia apoi `ship.sh`.

### Faza 1: fundația reală (A)

| Id | Task | Gata când |
|----|------|-----------|
| P1-01 | **Strat de provideri LLM**: interfață unică, provider principal + fallback (ex. DeepSeek), timeout, retry cu backoff, circuit breaker simplu, `LLM_PROVIDER=mock` rămâne pentru teste | Test cu provider picat: cererea trece pe fallback. Cheia se citește doar din `.env` |
| P1-02 | **Ingestie de documente reale**: lipire text, `.txt`, `.md`, `.docx`, `.pdf` cu text, `.eml`. Limită de mărime, validare tip real (nu doar extensie), fără execuție de macro-uri | Teste cu fișiere reale mici, inclusiv fișier corupt și fișier prea mare. Erori clare |
| P1-03 | **Detectare limbă + tip de situație** (ro/en, work/official/contract/school) cu scor de încredere. Dacă încrederea e mică, răspunsul spune asta | Evaluat pe 20 de documente cu etichete. Raport cu acuratețea reală |
| P1-04 | **Pipeline de analiză pentru documente lungi**: împărțire în bucăți, rezumat pe bucăți, apoi sinteză, păstrând legătura cu citatele originale | Un document de 15 pagini produce rezultat coerent, fără pierdere de termene |
| P1-05 | **Extracție structurată cu validare de schemă**: acțiuni, termene, persoane, sume. Output JSON validat, un retry dacă e invalid | 100% din răspunsuri respectă schema în evals sau eșuează controlat |
| P1-06 | **Ancorare în sursă**: fiecare acțiune și termen are citat verificat în cod. Datele se normalizează în ISO și se verifică (ex. "15 noiembrie" fără an: avertizare) | Test: citat inventat de model este respins și marcat |
| P1-07 | **Verificator de fidelitate**: numere, date, sume și nume din rezumat trebuie să existe în sursă. Ce nu există dispare sau primește avertizare | Test cu rezumat care "inventează" o sumă: prins |
| P1-08 | **Adaptări după nevoi** (secțiunea 1.1): `reading_level`, `steps`, `glossary`, `literal_language`, `tts_ready` ca parametri reali de prompt + post-procesare | Același document, 3 niveluri, diferențe măsurabile |
| P1-09 | **Scor de lizibilitate în cod** (nu "pe încredere" din LLM), adaptat pentru română. Metrici: lungime medie propoziție, cuvinte lungi, procent de cuvinte rare. `readability_after` trebuie să fie mai bun decât `before`, altfel avertizare | Test pe texte cunoscute. Documentați formula folosită, nu pretindeți un standard dacă nu e unul |
| P1-10 | **Erori în limbaj simplu** (RO/EN) pentru toate cazurile: fișier gol, prea mare, nesuportat, model indisponibil, timeout | UI-ul nu arată niciodată text tehnic |

### Faza 2: siguranță, intimitate, fiabilitate (A)

| Id | Task | Gata când |
|----|------|-----------|
| P1-11 | **Streaming SSE** + mesaje de progres reale ("Citesc documentul...", "Caut termene...") | Primul răspuns vizibil în 2-3 secunde pe un document mediu |
| P1-12 | **Mascare date personale** înainte de LLM și înainte de orice log: CNP (cu cifră de control), IBAN, telefon, email, adrese evidente. Demascare în răspuns | Teste cu date inventate. Loguri verificate automat: nu conțin text de document |
| P1-13 | **Apărare prompt-injection extinsă**: documentul este întotdeauna *date*, nu instrucțiuni. Teste cu 10+ variante (inclusiv în română, în HTML ascuns, în metadate de fișier) | Niciun test nu face modelul să urmeze instrucțiunea din document |
| P1-14 | **Sanitizare output** (fără HTML/JS executabil în răspuns) | Test XSS pe toate câmpurile text |
| P1-15 | **Limite și protecții**: rate limiting pe IP, mărime maximă, timeout global, CORS strict, antete de securitate | Test de încărcare simplu, serverul nu cade |
| P1-16 | **Guardrail "fără diagnostic / fără emoții / fără sfat medical sau juridic"**: test automat pe 30 de documente, inclusiv unele care provoacă modelul | 0 încălcări în raport |
| P1-17 | **Log fără conținut**: doar `request_id`, durată, provider, cod eroare, mărime. Fără text | Test: scanare log după rulare, nicio frază din document |
| P1-18 | **Cache opțional** în memorie pe hash de conținut (doar în proces, fără disc, ștergere la repornire) | Aceeași cerere a doua oară e instantanee. Documentat |

### Faza 3: situațiile (A/B)

| Id | Task | Nivel | Gata când |
|----|------|-------|-----------|
| P1-19 | **Scrisori oficiale**: banca, ANAF, primărie, asigurări. "Ce trebuie să fac, până când, ce se întâmplă dacă nu" | A | Evaluat pe 10 scrisori reale sau scrise de voi în stil real |
| P1-20 | **Ciornă de răspuns** (`/draft-reply`): ton ales de utilizator, persoana revizuiește, nimic nu se trimite singur | A | Test: nu inventează fapte care nu sunt în context |
| P1-21 | **Rezumat de ședință din transcript** (text lipit sau din dictare în browser): decizii, sarcini, cine face ce, termene, cu citate | A | Evaluat pe 5 transcripturi |
| P1-22 | **Motor de ajustări pentru angajator**: catalog verificat (fișiere curate de P3) + generare de solicitare personalizată. Fără mențiuni legale nevalidate: fiecare afirmație juridică are sursă oficială sau e etichetată "bune practici" | A | Cererea conține doar ajustări din catalog. Verificați orice trimitere la lege pe surse oficiale (ex. legislatie.just.ro) |
| P1-23 | **Contracte și regulamente**: clauze importante, obligații, termene, ce e neobișnuit, **fără** a spune "e legal / nu e legal". Avertizare: nu e consultanță juridică | B | Test pe 3 contracte-model |
| P1-24 | **Școală/facultate**: cerințe, termene, criterii din syllabus | B | Test pe 3 documente |
| P1-25 | **Export**: `.ics` pentru termene (calendar), `.docx` cu titluri reale, HTML accesibil, text curat pentru cititor de ecran | A pentru .ics, B pentru restul | Se deschid corect în Google Calendar / Word |
| P1-26 | **OCR pentru imagini** (Tesseract cu limba română, dacă se instalează rapid), cu avertizare când calitatea e slabă | B | Test pe o fotografie de scrisoare. Dacă nu merge în 30 min, treci în C |
| P1-27 | **Preluare din URL** (pagină web → text) cu protecție SSRF (fără rețele interne, fără redirecturi periculoase) | C | Teste de securitate |
| P1-28 | **Instrucțiuni medicale**: doar simplificare, avertizare, fără recomandări | C | Nu se lansează fără revizuire de specialist |

### Faza 4: calitate, evaluare, livrare (A)

| Id | Task | Gata când |
|----|------|-----------|
| P1-29 | **Corpus de evaluare extins** în `evals/`: 40+ documente (scrise de voi sau cu permisiune, fără date personale reale), cu proprietăți așteptate. Rulezi cu `python evals/run.py` | Raport cu rate de trecere pe categorie, salvat în `evals/report.md` |
| P1-30 | **Poartă de regresie**: `check.sh` rulează un subset rapid de evaluări cu provider mock; evaluarea completă se rulează manual înainte de fiecare tag | O schimbare care strică un termen e prinsă |
| P1-31 | **Judecător LLM (opțional) + verificare umană pe 10 cazuri** pentru calitatea simplificării. Nu declarați scoruri LLM ca adevăr | Notițe cu ce a spus judecătorul vs ce ați văzut voi |
| P1-32 | **OpenAPI/Swagger** generat și curat, versiune `v2` | `/docs` funcționează |
| P1-33 | **Docker + deploy + CI** (GitHub Actions rulează `check.sh`), `.env.example` complet, `/api/v2/health` | URL public, funcționează de pe telefon |
| P1-34 | **Test de clonă proaspătă**: clonezi repo-ul într-un folder nou, urmezi README-ul, totul pornește | Rulat de altcineva decât tine |
| P1-35 | **Document `docs/LIMITS.md`**: ce NU face produsul, unde greșește, ce a fost testat și ce nu. Util și în pitch | Onest, fără exagerări |

---

## 4. Ordinea recomandată pentru P1

1. **P1-00** (contract) → anunț în chat
2. P1-01, P1-02, P1-10 (fundația, în paralel cu subagenți dacă fișierele sunt diferite)
3. P1-03, P1-05, P1-06, P1-07 (nucleul de analiză reală)
4. P1-08, P1-09 (adaptările pe nevoi)
5. P1-11, P1-12, P1-13, P1-17 (streaming + intimitate + siguranță)
6. P1-19, P1-20, P1-21, P1-22, P1-25 (situațiile și exportul)
7. P1-29, P1-30 (evaluări) și P1-33 (deploy)
8. Restul A/B în ordinea valorii, până la FREEZE

Dacă ai de ales între "încă o situație" și "evaluare + fidelitate", alege evaluarea și fidelitatea. Un produs care inventează un termen este mai rău decât unul care face mai puține lucruri.

---

## 5. Taskuri de rezervă pentru P2 și P3 (când își termină ce au)

### P3 (frontend)
| Id | Task |
|----|------|
| N3.8 | Ecran de încărcare fișiere (drag and drop + buton clasic), progres, erori în limbaj simplu |
| N3.9 | Selector de nevoi în limbaj simplu (secțiunea 1.1) cu previzualizare, salvat local |
| N3.10 | Afișare avertizări (`warnings`) și citate (clic pe termen → vezi citatul în text) |
| N3.11 | Citire cu voce (Web Speech API) și dictare, cu fallback dacă browserul nu le are |
| N3.12 | Export din UI (.ics, .docx, copiază) și bibliotecă cu căutare |
| N3.13 | Vedere angajator: solicitare de ajustări, revizuire înainte de trimitere |

### P2 (QA, nevoi, dovezi)
| Id | Task |
|----|------|
| N2.7 | Colectare de documente de test (scrise de voi sau cu permisiune) pentru corpusul din P1-29 |
| N2.8 | Testare cu persoane reale, în special cu persoane care folosesc cititor de ecran, cu nevoi cognitive sau motorii. Notezi doar ce au spus ei, cu acordul lor |
| N2.9 | Teste automate pentru fiecare combinație relevantă de preferințe + test cu tastatura |
| N2.10 | Textele din UI și din produs (RO/EN) în limbaj simplu, revizuite de cineva din afara echipei |
| N2.11 | Pitch și script de demo cu documente reale, nu cu eșantioane aranjate |

---

## 6. Prompturi gata de lipit (după Prompt 0, thread nou)

### P1-00 + P1-01 + P1-02 (prima sesiune)

```
Taskuri P1-00, apoi P1-01 și P1-02 din docs/P1-TASKS.md. Citește mai întâi secțiunile 1, 2 și 3.

P1-00: scrie CONTRACTS v2 exact ca în secțiunea 2 (POST /api/v2/analyze, upload, stream, erori, warnings)
și livrează fixtures pentru fiecare endpoint. Nu implementa încă logica.

P1-01: strat de provideri LLM cu fallback, timeout, retry, circuit breaker; mock rămâne pentru teste.
P1-02: ingestie de documente reale (.txt, .md, .docx, .pdf cu text, .eml), validare tip real, limită de mărime.

Reguli: nicio valoare hardcodată în răspunsuri. Totul se calculează din documentul primit.
Scrie testele întâi și arată-le picând. Folosește subagenți doar pentru fișiere diferite.
Dă-mi un plan de 5 rânduri și așteaptă "ok go". La final arată-mi dovezi rulate (teste verzi + un exemplu real cu un fișier).
```

### Nucleul de analiză (P1-03 până la P1-07)

```
Taskuri P1-03, P1-05, P1-06, P1-07. Nucleul de analiză reală.

Cerințe:
- Detectare limbă și situație cu scor de încredere (evaluat pe 20 de documente etichetate).
- Extracție structurată cu validare de schemă și un singur retry.
- Fiecare acțiune și termen are `quote` verificat în cod că apare în textul sursă. Dacă nu, quote_found=false.
- Verificator de fidelitate: orice număr, dată, sumă sau nume din rezumat trebuie să existe în sursă; altfel avertizare.
- Datele fără an sau ambigue primesc avertizare, nu presupunere.

Teste întâi. Plan de 5 rânduri, aștept "ok go". Apoi arată-mi un raport cu cazurile care au picat, nu doar cele care au trecut.
```

### Adaptări pe nevoi + lizibilitate (P1-08, P1-09)

```
Taskuri P1-08 și P1-09. Implementează adaptările din secțiunea 1.1 ca parametri reali:
reading_level (1-3), steps, glossary, literal_language, tts_ready.
Scorul de lizibilitate se calculează în cod, nu îl cere modelului. Documentează formula.
Regulă: nu deduci nevoia utilizatorului din text și nu menționa niciodată motivul adaptării în răspuns.
Test: același document, 3 niveluri; metricile trebuie să difere măsurabil și "after" să fie mai bun decât "before",
altfel apare avertizare. Plan scurt, aștept "ok go".
```

---

## 7. Ce nu am putut verifica

- Nu am văzut repo-ul, deci căile, id-urile existente și runner-ul de teste sunt presupuneri.
- Planul n-a fost rulat într-o sesiune reală Antigravity. Urmărește prima sesiune și corectează AGENTS.md dacă agentul ignoră regulile.
- Calitatea simplificării în română trebuie verificată de oameni vorbitori nativi, nu doar de metrici.
- Orice afirmație juridică din produs sau din pitch trebuie confirmată pe surse oficiale.
- Produsul nu înlocuiește consultanța medicală sau juridică, iar UI-ul trebuie să spună asta clar.
