# Ghid Reconstituire Demo: Modul pentru Nevăzători (Ecran Negru & TTS Română)
**Destinat:** Prezentator unic (1 persoană) la jurizarea AccessABILITY Hackathon 2026  
**Jurat țintă:** Jurat nevăzător / jurat axat pe accesibilitate extremă  

---

## 🎯 Ce demonstrăm juriului (Mesajul Cheie)
> „*Limpede nu este doar o aplicație cu butoane mari — este o platformă complet utilizabilă fără vedere.*  
> *Pentru a dovedi că nu ne bazăm deloc pe indicii vizuale, vom opri complet ecranul (Mod Ecran Negru) și vom naviga exclusiv din taste și comenzi tactile, asistați de vocea neutră în limba română.*”

---

## ⌨️ Comenzile Rapide (Cheat Sheet)
| Acțiune | Tastatură Desktop / Laptop | Dispozitiv Mobil (Telefon/Tabletă) | Ce se întâmplă |
| :--- | :--- | :--- | :--- |
| **Comutare Ecran Negru** | **`F9`** (sau `Alt + B`) | Butonul **„Mod Orb (F9)”** din bara de confort | Ecranul devine 100% negru (`#000000`). Se aude: *„Modul ecran negru activat...”* |
| **Navigare Înainte** | `Tab` sau `Săgeată Jos` | Glisare cu degetul spre dreapta (`Swipe Right`) | Sare la următorul element și citește rolul + textul în română |
| **Navigare Înapoi** | `Shift + Tab` sau `Săgeată Sus` | Glisare cu degetul spre stânga (`Swipe Left`) | Sare la elementul anterior și îl citește cu voce tare |
| **Activare / Clic** | `Enter` sau `Space` | Atingere dublă (`Double Tap`) | Activează butonul / selectează opțiunea |
| **Oprire Imediată Vorbire**| `Escape` | Atingere simplă | Oprește lectura vocală curentă |
| **Revenire la Ecran Normal**| **`F9`** (sau `Alt + B`) | Butonul de ieșire / F9 | Ecranul revine vizual. Se aude: *„Modul ecran negru dezactivat.”* |

---

## 🎬 Scenariul de Demo Pas cu Pas (Durată: 2 minute)

### Pasul 1: Introducerea modului în fața juratului (15 secunde)
1. Ești pe pagina principală `https://curves-relates-kenneth-pen.trycloudflare.com` (sau `http://localhost:8000`).
2. Spui juriului:
   > *„Pentru colegii nevăzători, site-urile standard sunt adesea capcane vizuale. La Limpede, am construit un cititor vocal dedicat în limba română și am adăugat o funcție de testare extremă: tasta F9, care stinge complet afișajul grafic, lăsând întreaga aplicație funcțională sub ecranul negru.”*

### Pasul 2: Stingerea ecranului (15 secunde)
1. **Apasă tasta `F9`** (pe Mac sau laptopuri cu Fn lock poți folosi și `Alt + B`).
2. **Ce se vede pe videoproiector/laptop:** Ecranul devine instantaneu **complet negru** (`#000000`). Nimic vizual nu mai este vizibil.
3. **Ce aude juratul în difuzoare:**
   > 🔊 *„Modul ecran negru activat. Navigați folosind tasta Tab. Apăsați tasta F9 pentru a reveni la afișajul vizual.”*

### Pasul 3: Navigarea oarbă pe pagină (45 secunde)
1. **Apasă tasta `Tab`**:
   - Vocea citește: 🔊 *„Link: Sari la conținutul principal”*
2. **Apasă din nou `Tab`**:
   - Vocea citește: 🔊 *„Buton: Meniu”*
3. **Apasă din nou `Tab`**:
   - Vocea citește: 🔊 *„Buton: Mod: Luminos”*
4. **Continuă să apeși `Tab`** până la caseta de introducere sau sugestii:
   - Vocea citește: 🔊 *„Casetă de text: Introdu textul, lipește instrucțiunile sau atașează un fișier PDF...”*
5. **Apasă `Tab`** pe chipurile rapide:
   - Vocea citește: 🔊 *„Buton: Clarifică fișa postului”*
6. **Apasă `Enter`**:
   - Documentul demonstrativ se încarcă și începe automat procesarea.
   - Live region-ul anunță: 🔊 *„Se procesează documentul...”*
   - Câteva secunde mai târziu: 🔊 *„Documentul a fost analizat cu succes.”*

### Pasul 4: Ascultarea rezultatului (30 secunde)
1. Apasă `Tab` până la butonul *„Ascultă”*:
   - Vocea citește: 🔊 *„Buton: Ascultă rezumatul în limba română”*
2. Apasă `Enter`:
   - Vocea românească începe să citească rezumatul clar și pașii de urmat, cu pronunția corectă a orelor, numerelor și termenilor legali (datorită normalizatorului vocal inclus).

### Pasul 5: Revenirea la ecranul vizual (15 secunde)
1. **Apasă tasta `F9`**:
   - Ecranul negru dispare instant, dezvăluind rezultatul structurat pe ecran exact în starea în care l-ai lăsat.
   - Vocea confirmă: 🔊 *„Modul ecran negru dezactivat.”*
2. Încheie cu fraza de impact:
   > *„Așa cum ați auzit, am realizat un flux complet de lucru — de la primirea sarcinii până la execuție — cu ecranul 100% stins, bazându-ne exclusiv pe ergonomia sonoră și pe ordinea firească a tastelor.”*

---

## 📱 Cum testezi / arăți pe Telefonul Mobil
1. Deschide adresa site-ului pe telefon.
2. În colțul din dreapta-sus, apasă pe meniul **„Confort ▾”**.
3. Apasă pe **„Mod Orb (F9)”**.
4. Ecranul telefonului devine negru.
5. Fă swipe cu degetul spre dreapta (`👉`) oriunde pe ecran: telefonul citește elementele consecutiv.
6. Atinge ecranul de două ori (`double tap`) pentru a declanșa butonul selectat.
7. Apasă din nou pe butonul Mod Orb pentru a ieși.

---

## 🛠️ Detalii Tehnice pentru Juriul Tehnic
- **W3C Accessible Name Resolution**: `web/a11y/voiceover-core.js` calculează eticheta accesibilă respectând ierarhia standard (`aria-labelledby` > `aria-label` > `label[for]` > `alt` > `placeholder` > `innerText`).
- **Normalizare Vocală Românească**: Numerele (`14:00` devine *„ora paisprezece”*, `art. 78` devine *„articolul șaptezeci și opt”*, `500 lei` devine *„cinci sute de lei”*) sunt convertite automat în cuvinte românești fonetice înainte de sinteză.
- **Zero Audio Lagging / Cancel on Tab**: La fiecare apăsare de `Tab`, sinteza vocală anterioară este anulată instantaneu (`synth.cancel()`), eliminând complet coada de sunete întârziate la navigare rapidă.
- **Ecran Negru Nativity**: Suprapunerea `#blind-curtain` folosește `z-index: 2147483647` și `pointer-events: none;`, lăsând focusul nativ al browserului și evenimentele de tastatură 100% neatinse.
