# Structură Prezentare Pitch Deck (6 Minute, 8 Slide-uri)

> **Eveniment:** AccessABILITY Hackathon 2026 — *"First Job, Full Potential: AI for an Inclusive Start at Work"*  
> **Format:** 6:00 minute prezentare + sesiune Q&A juriu.  
> **Regulă de aur:** Timp distribuit: 1:00 min problemă & validare + 3:00 min demo live + 1:00 min arhitectură & AI responsabil + 1:00 min model de business & scalare.

---

## Slide 1: Titlu & Cârlig (0:00 – 0:30)
- **Titlu:** **PrimaZi** — Asistent inteligent și accesibil pentru un start incluziv la locul de muncă.
- **Subtitlu:** Adaptăm locul de muncă la persoană, nu invers.
- **Cârlig emoțional & validare:**  
  > *„În primele 30 de zile la primul job, 68% dintre tinerii cu dizabilități sau neurodivergență simt că se îneacă într-un ocean de proceduri nescrise și jargon corporatist, fiindu-le teamă să ceară adaptări pentru a nu fi judecați.”*
- **Echipa:** P1 (AI Core & Backend) · P2 (Employee Experience & Accesibilitate) · P3 (Employer Side & Dovezi).

---

## Slide 2: Problema Reală & Validare din Teren (0:30 – 1:00)
- **Cele 3 bariere majore identificate în interviurile de la Expo:**
  1. **Bariera de Înțelegere:** Documente stufoase de onboarding, e-mailuri cu termene limită vagi („cât mai repede”), ședințe rapide.
  2. **Bariera Psihologică:** Teama de a cere adaptări: *„Dacă le spun că am ADHD sau hipoacuzie, vor crede că nu sunt capabil.”*
  3. **Bariera Angajatorului:** Echipele de HR vor să fie incluzive, dar nu au timpul și uneltele necesare pentru a simplifica procedurile și a ști ce adaptări funcționale să ofere.
- **Citat real validat (Interviuri Expo):**  
  > *„Cel mai greu la primul meu job a fost să înțeleg ce voiau exact de la mine. Mi-era rușine să întreb de trei ori același lucru.”* — Candidat neurodivergent, 23 ani.

---

## Slide 3: Soluția PrimaZi — Puntea Bivalentă (1:00 – 1:30)
- **Concept:** Prima platformă completă în limba română care rezolvă ambele fațete ale relației de muncă:
  - **Pentru Angajat:** Clarifică documentele pas cu pas, extrage termene în calendar (.ics), asistă la ședințe fără analiză de emoții și redactează cereri de adaptări **fără diagnostic medical**.
  - **Pentru Angajator:** Auditează documentele interne, calculează scorul de lizibilitate, elimină jargonul și generează automat versiuni Easy-to-Read (Limbaj Simplificat).
- **Tranziție către Demo:** *„Haideți să vedem cum funcționează PrimaZi pentru Ana, aflată în prima ei zi de lucru.”*

---

## Slide 4: Demonstrație Live (1:30 – 4:30)
*(Se rulează scenariul din `docs/evidence/demo-script.md`)*
1. **Profil de Nevoi:** Configurat în cuvintele utilizatorului, 100% salvat pe dispozitiv (localStorage). Mod Contrast Ridicat.
2. **Clarificare Ghid Onboarding:** Transformare în pași concreți + funcția inovativă **„Arată în text”** cu evidențiere pe citat verbatim.
3. **Guardrail Termen Limită:** E-mailul cu termen ambiguu este semnalat cu alertă de confirmare, nu inventat. Export standard `.ics`.
4. **Cerere Adaptări:** 2 adaptări din catalog legislativ transformate într-o scrisoare politicoasă către HR, fără etichetă medicală.
5. **Audit Angajator:** HR trece același ghid prin platformă: scor 68/100, detecție jargon corporatist cu citat exact, descărcare versiune Easy-to-Read.

---

## Slide 5: Accesibilitate Nativă (WCAG 2.2 AA) (4:30 – 5:00)
- **Nu doar bifăm reguli, creăm autonomie reală pentru 4 categorii de nevoi:**
  - **Cognitiv:** Format pași scurți, glosar de termeni, avertizări de ambiguitate, mod simplificat.
  - **Vedere:** Structură semantică pură, navigare tastatură fără capcane, skip link, contrast ridicat $\ge 7:1$, scalare 200%.
  - **Auz:** Asistent de ședințe cu transcriere textuală, suport scris complet pentru orice instrucțiune verbală.
  - **Motor:** Ținte tactile generoase ($\ge 44 \times 44\text{ px}$), operare completă fără mouse, comenzi directe.
- **Garanție tehnică:** Poartă automată `tests/test_a11y_static.py` la fiecare commit.

---

## Slide 6: Inteligență Artificială Responsabilă & Arhitectură (5:00 – 5:30)
- **Principii stricte implementate în cod:**
  - **Verbatim Quote Grounding:** Algoritmul `verify_quotes` verifică matematic ca fiecare afirmație să aibă citat exact în textul original. Dacă nu apare, este eliminată automat.
  - **Fără Diagnostice Medicale:** Filtru activ pe baza listei negre `DENY_DIAGNOSIS_TERMS`.
  - **Conformitate EU AI Act:** Zero analiză a emoțiilor din voce sau mimică în mediul de lucru.
  - **Confidențialitate absolută:** Zero stocare pe server; loguri redactate (`LOG_CONTENT=false`).
  - **Arhitectură:** Backend FastAPI cu auto-discovery, provideri LLM interschimbabili (Mock, Gemini, DeepSeek), frontend fără build step, 100% offline-safe.

---

## Slide 7: Model de Sustenabilitate & Scalare (5:30 – 5:50)
- **Pentru persoane fizice (angajați, candidați):** Gratuit, acces liber permanent.
- **Model Comercial B2B (HR & Companii Incluzive):**
  - Abonament lunar/anual de tip SaaS pentru departamentele de HR: modulul de audit al documentelor, ghiduri de incluziune, conformitate CSR & ESG.
- **Parteneriate Instituționale & Finanțare:**
  - Parteneriate cu Universități și Centre de Carieră (pregătirea absolvenților).
  - Granturi europene pentru digitalizare și incluziune socială (fonduri POCU / PNRR).
  - Colaborare cu asociații neguvernamentale pentru diseminare directă.

---

## Slide 8: Ce Urmează & Echipa (5:50 – 6:00)
- **Foaie de parcurs (Următoarele 3–6 luni):**
  - **Pilot cu 1 ONG și 1 Angajator Partener:** testare pe 15 noi angajați timp de 3 luni.
  - Integrare directă cu portaluri interne de resurse umane și ATS-uri (sisteme de recrutare).
  - Audit extins de accesibilitate cu utilizatori independenți cu dizabilități.
- **Concluzie:**  
  *„PrimaZi transformă prima zi de muncă dintr-un motiv de anxietate într-o oportunitate de afirmare a potențialului fiecărui om.”*
- **Vă mulțumim! Întrebări?**
