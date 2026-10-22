# Pregătire Q&A cu Juriul (P3)

> Răspunsurile trebuie să reflecte 100% realitatea din acest repo. Fără exagerări, fără afirmații neacoperite de cod sau date. Dacă ceva nu a fost validat sau construit, spunem deschis.

---

### 1. De ce nu folosește utilizatorul direct ChatGPT sau Claude?
**R:** ChatGPT oferă răspunsuri generice de text, nu un flux de lucru complet pentru locul de muncă. PrimaZi oferă grounding cu citate sursă verificate direct în textul original, detectare de termene ambigue, export direct în calendar (.ics), catalog de adaptări specifice legislației din România și o latură dedicată angajatorului pentru auditul documentelor.

### 2. Cum protejați confidențialitatea și GDPR pentru datele despre dizabilități?
**R:** Respectăm principiul *privacy-by-design*: nu solicităm, nu stocăm și nu inferăm niciodată diagnostice medicale, iar profilul de nevoi funcționale este salvat exclusiv local în browserul utilizatorului (localStorage). Pe server nu există baze de date sau loguri cu conținutul documentelor încărcate (`LOG_CONTENT=false`).

### 3. Cum gestionați halucinațiile modelelor LLM pe documente de serviciu critice?
**R:** Folosim un strat strict de verificare (`verify_quotes` în `guardrails.py`): orice sarcină, termen sau decizie extrasă trebuie să conțină un `source_quote` verbatim verificat matematic ca substring în textul original. Dacă modelul inventează un detaliu fără corespondent exact în text, elementul este eliminat automat de server și se emite o avertizare.

### 4. Oferiți consultanță juridică privind drepturile angajaților cu dizabilități?
**R:** Nu. Aplicația specifică explicit că informațiile sunt strict informative și nu constituie consultanță juridică. În catalogul de adaptări cităm strict articole oficiale din legislația română (Legea 448/2006, Codul Muncii Legea 53/2003, Legea 81/2018) sau menționăm „bună practică generală”, fără interpretări speculative.

### 5. De ce NU ați inclus detecție de emoții din voce sau expresii faciale?
**R:** Am exclus deliberat detecția de emoții din motive etice și legale: EU AI Act interzice recunoașterea emoțiilor la locul de muncă și în educație, iar persoanele neurodivergente sau cu dizabilități sunt adesea etichetate eronat de aceste sisteme. Ne concentrăm strict pe text, acțiuni și planificare.

### 6. Cine plătește pentru această soluție (modelul de business)?
**R:** Utilizatorii individuali (angajați, candidați) au acces gratuit. Modelul comercial este B2B (licențiere pentru companii și departamente de HR pentru modulul de analiză și incluziune), parteneriate instituționale cu universități/centre de carieră și finanțări europene sau naționale pentru incluziune socială.

### 7. Cum scalați sistemul dincolo de prototip?
**R:** Arhitectura este modulară (FastAPI + ES modules independente), cu costuri de rulare minime prin caching deterministic pe hash de intrare și un strat agnostic de LLM care permite utilizarea oricărui model open-source sau comercial găzduit în UE. Nu avem o bază de date centralizată greoaie, scalarea orizontală fiind trivială.

### 8. Ce ați testat efectiv pe partea de accesibilitate (WCAG)?
**R:** Am verificat static structura semantică HTML pe fiecare commit (`test_a11y_static.py`), am asigurat navigare completă exclusiv din tastatură (focus vizibil, skip links, trap-uri evitate), moduri de contrast ridicat și compatibilitate cu mărirea textului până la 200%. [De completat după testul cu cititor de ecran: softul utilizat - Orca / NVDA].

### 9. Ce NU ați reușit să validați încă?
**R:** Nu am derulat încă un studiu longitudinal pe 3-6 luni privind impactul direct asupra ratei de retenție la locul de muncă. De asemenea, analiza de documente este testată pe fișiere text uzuale de onboarding, nu pe sisteme proprietare enterprise de gestionare a documentelor.

### 10. Ce face aplicația dacă documentul conține prompt injection sau instrucțiuni malițioase?
**R:** Documentul de intrare este tratat strict ca date pasive, niciodată ca instrucțiuni de sistem (`system prompt`). Structura de ieșire este constrânsă rigid prin JSON schema și Pydantic, iar tentativele de deturnare sunt respinse fără a altera formatul răspunsului.

### 11. Ce se întâmplă dacă utilizatorul nu are internet sau pică serverul de AI?
**R:** Aplicația include un mod de rezervă complet (`LLM_PROVIDER=mock`) și caching pe disc pentru exemplele demonstrative. În UI există stări clare de eroare în limba română (`aria-live="assertive"`) cu posibilitate de reîncercare și avertizare de sistem indisponibil.

### 12. De ce un scor pe documente și nu pe candidați în modulul de angajator?
**R:** Principiul nostru etic fundamental este adaptarea locului de muncă la persoană, nu trierea persoanei. Modulul de angajator măsoară accesibilitatea și claritatea textului scris (număr cuvinte/frază, jargon, fraze lungi), oferind sugestii pentru echipa HR de a deveni mai incluzivă.

### 13. Cum sunt rezolvate termenele limită vagi (ex: „cât mai repede”)?
**R:** Sistemul refuză să inventeze date calendaristice arbitrare (`due_iso=null`). Câmpul păstrează textul original („cât mai repede”), marchează sarcina cu `needs_confirmation=true`, iar în interfață utilizatorul este invitat să își aleagă sau confirme manual data în calendar.

### 14. Cum a fost implicată comunitatea persoanelor cu dizabilități în design?
**R:** Am demarat interviuri de validare direct la conferință/expoziție cu persoane cu experiență trăită și specialiști ONG. Pe baza feedback-ului, am eliminat orice solicitare de diagnostic medical și am simplificat interfața la o singură acțiune principală per ecran.

### 15. Care este următorul pas concret după hackathon?
**R:** Lansarea unui pilot de 3 luni cu o asociație non-guvernamentală și un angajator partener din România pentru 10 noi angajați, evaluarea formală a calității modelelor LLM pe terminologia administrativă românească și realizarea unui audit de accesibilitate cu utilizatori independenți.
