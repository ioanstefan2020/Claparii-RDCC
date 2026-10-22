# Extensia de Browser PrimaZi — „Selectează text, fă-l clar”

Extensie de browser Manifest V3 pentru accesibilitate cognitivă și neurodivergență (ADHD, dislexie, autism, vedere scăzută).
Permite selectarea oricărui text de pe o pagină web și transformarea lui instantanee într-un format simplificat, structurat în buline esențiale, cu evidențiere automată a numerelor, termenelor limită și citire naturală cu voce tare în limba română.

---

## 1. Ghid de Instalare pentru Demo (sub 1 minut)

1. Deschide Google Chrome, Brave sau Microsoft Edge.
2. Navighează la `chrome://extensions/` (sau `edge://extensions/`).
3. Activează comutatorul **„Developer mode”** (Mod dezvoltator) din colțul din dreapta-sus.
4. Apasă pe butonul **„Load unpacked”** (Încarcă extensie despachetată).
5. Selectează folderul `extension/` din acest depozit (sau dezarhivează `clar-extension.zip` și alege folderul rezultat).
6. Gata! Vei vedea iconița PrimaZi în bara de extensii a browserului.

---

## 2. Cum se folosește în Demo (Flux de 30 secunde)

1. **Selectează text:** Pe orice pagină web (articol, intranet, procedură internă, portal de știri), selectează 1-3 paragrafe.
2. **Apasă „Fă clar”:** 
   - Va apărea un buton plutitor cald „Fă clar” lângă selecție.
   - Alternativ, folosește comanda rapidă **`Alt + Shift + S`** sau click dreapta -> *„Fă clar (PrimaZi)”*.
3. **Cardul de claritate:** Se deschide o fereastră accesibilă (izolată în Shadow DOM pentru a nu afecta stilurile paginii).
   - Textul este reformulat direct și simplu.
   - Datele, orele, sumele și termenele limită sunt evidențiate vizual.
   - Ai butoane mari (44px ținte tactile):
     - **🔊 Ascultă**: Citește textul cu voce tare în limba română folosind sinteza vocală.
     - **• Buline**: Transformă conținutul într-o listă structurată pe pași.
     - **✂️ Mai scurt**: Condensează textul la 30-40% din lungime.
     - **📋 Copiază**: Copiază rezultatul în clipboard.
     - **👁️ Original**: Comută între textul original și cel adaptat.
     - **✕ / Esc**: Închide dialogul și returnează focusul pe pagină.

---

## 3. Mod Offline / Fallback Local

Dacă serverul backend este oprit sau dacă utilizatorul activează opțiunea *„Păstrează textul doar pe acest dispozitiv”*, extensia funcționează complet offline:
- Împarte automat propozițiile.
- Extrage datele, orele și cuvintele cheie prin regex local.
- Aplică fonturile și contrastul preferat.
- Utilizează vocea nativă din browser.
- Afișează eticheta transparentă: **„Mod de bază (offline)”**.

---

## 4. Reguli de Confidențialitate & Securitate (Zero Date Medicale)

- **Nu transmitem date fără acțiune:** Simpla selectare a textului NU trimite nimic către server.
- **Doar selecția curentă:** Nu trimitem adresa URL a paginii, titlul, cookie-urile sau alte informații din pagină.
- **Câmpuri de parolă ignorate:** Extensia nu se declanșează niciodată în câmpuri de tip `input[type="password"]`.
- **Fără termeni medicali:** Nu stocăm și nu cerem diagnostice medicale; doar preferințe ergonomice de lectură.

---

## 5. Limite Cunoscute (Known Limits)

1. **Canvas / WebGL:** Paginile care desenează text exclusiv pe un element `<canvas>` (cum ar fi noul motor de randare din Google Docs fără mod accesibilitate activat) nu permit selecția nativă a nodurilor DOM.
2. **Text peste 3000 de caractere:** Textele foarte lungi sunt tăiate automat la ultima graniță de propoziție sub 3000 de caractere pentru a preveni blocajele și costurile excesive.
3. **Imagini fără OCR:** Extensia procesează doar text selectabil, nu text încorporat în fișiere imagine statice (fără selecție text).
