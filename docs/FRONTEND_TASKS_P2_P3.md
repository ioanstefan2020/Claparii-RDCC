# Specificații și Taskuri Frontend pentru P2 și P3: Adaptări Complete de Accesibilitate & Integrare Calendar

> **Destinatari:** P2 (QA & Nevoi Utilizator) și P3 (Dezvoltare Frontend & UI)  
> **Autor:** P1 (Backend & Arhitectură)  
> **Status:** Gata de implementare. Backend-ul are toate endpoint-urile active, testate și documentate.

---

## 1. Rezumat Executiv & Obiectiv de Produs

Vrem ca **PrimaZi** să nu fie un simplu utilitar AI de rescriere a textelor, ci un **mediu de lucru sigur, cald și profund adaptiv** pentru angajați cu toate tipurile de dizabilități și nevoi neurodivergente:
1. **Cognitiv / Neurodivergență (ADHD, Dislexie, Autism):**
   - **Bionic Reading & Evidențiere Cheie:** În propoziții, cuvintele cheie operaționale (verbe de acțiune, termeni tehnici, date limită) primesc accent vizual și font mărit pentru ghidarea automată a privirii (saccades) și reducerea oboselii mentale.
   - **Fonturi dedicate:** Suport pentru `OpenDyslexic` și `Lexend` (proiectat special pentru fluența citirii).
   - **Ghidaj vizual de citire (Reading Ruler):** O linie orizontală subtilă care urmărește cursorul pentru a preveni sărirea peste rânduri.
   - **Focus Mode (Zen):** Ascunderea/diminuarea elementelor periferice pentru a elimina zgomotul vizual.
2. **Văz (Vedere scăzută, Fotofobie, Daltonism):**
   - Contrast înalt (WCAG 2.2 AAA: 7:1) cu temă întunecată profundă sau galben-pe-negru.
   - Scalare dinamică a fonturilor (M, L, XL, XXL) fără a rupe layout-ul flexbox/grid.
   - Butoane mari (minim 48x48px țintă tactilă) cu contururi clare de focus.
3. **Auz (Hipoacuzie, Surditate):**
   - Transcriere structurată pas cu pas pentru orice ședință, cu etichete clare de vorbitor și butoane rapide de copiere.
   - Nicio notificare exclusiv sonoră: toate alertele au echivalent vizual în `aria-live`.
4. **Motor (Tremor, Mobilitate redusă, Switch Access):**
   - Navigare 100% din tastatură (`Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape`).
   - Inele de focus ultra-vizibile (`outline: 3px solid #2563eb; outline-offset: 2px`).
   - Spațiere generoasă între butoane (minim 12px) pentru a preveni click-urile greșite.

---

## 2. Arhitectura de Date Locale (`localStorage`)

Toate preferințele și nevoile utilizatorului se salvează **exclusiv în browserul local** sub cheia `wp.prefs.v1`. Serverul nu stochează date medicale sau diagnostice.

### Structura completă a obiectului `wp.prefs.v1`:

```typescript
interface UserComfortPrefs {
  version: 1;
  updatedAt: string; // ISO 8601
  answers: {
    freeformNeeds?: string; // Textul liber introdus de utilizator
    readingPace: 'slow' | 'medium' | 'fast';
    textAmount: 'short' | 'medium' | 'full';
    stepByStep: boolean;
    visualNoise: 'low' | 'normal';
    sensory: 'quiet' | 'normal';
    timeToDecide: 'need-more-time' | 'normal';
  };
  prefs: {
    theme: 'light' | 'dark' | 'system' | 'yellow-on-black';
    textSize: 'm' | 'l' | 'xl' | 'xxl';
    spacing: 'comfortable' | 'roomy' | 'compact';
    contrast: 'normal' | 'high';
    motion: 'reduced' | 'full';
    font: 'default' | 'opendyslexic' | 'lexend' | 'readable';
    density: 'focused' | 'full';
    bionic: boolean;              // Bionic reading (accentuează primele litere)
    highlightKeyTerms: boolean;   // Cuvintele cheie mai mari și boldate
    readingRuler: boolean;        // Linie orizontală ghid de citire
    audioSupport: boolean;
  };
  workplaceAdjustments: Array<{
    id: string;
    title: string;
    reason_ro: string;
  }>;
}
```

---

## 3. Task 1 (P3): Modulul „Nevoile Mele de Lucru în Cuvintele Mele”

### Unde se pune:
În `web/profile.html` și în modalul de setări / onboarding confort (`web/settings.html`).

### Comportament:
1. Utilizatorul are un câmp de text generos:  
   *„Scrie în cuvintele tale ce te ajută la muncă (ex: am nevoie de font mare, instrucțiuni pas cu pas, mă deranjează lumina puternică sau zgomotul, am ADHD și mă pierd la texte lungi).”*
2. Buton de acțiune: **„✨ Adaptează site-ul pentru nevoile mele”**.
3. La click, frontend-ul trimite un request către backend:
   ```javascript
   const response = await fetch('/api/profile/recommend-adaptations', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       freeform_needs: textareaInput.value,
       workplace_role: userRoleInput.value || null,
       current_prefs: getCurrentLocalPrefs()
     })
   });
   const result = await response.json();
   ```
4. Răspunsul întoarce:
   - `data.ui_prefs`: noile valori pentru `textSize`, `font`, `contrast`, `spacing`, `bionic`, `highlightKeyTerms`, etc.
   - `data.workplace_adjustments`: adaptările recomandate din catalog (ex: `written_instructions`, `task_breakdown`).
   - `data.explanation_ro`: mesaj cald și transparent explicând ce modificări au fost aplicate.
5. Se salvează în `localStorage.setItem('wp.prefs.v1', JSON.stringify(updatedPrefs))`.
6. Se apelează imediat `applyGlobalPreferences(updatedPrefs.prefs)` pentru a reflecta instantaneu stilul pe tot site-ul.

---

## 4. Task 2 (P3): Funcția Globală de Aplicare a Stilurilor (`applyGlobalPreferences`)

Trebuie inclusă în `web/js/theme.js` sau `web/js/app.js` și apelată pe **fiecare pagină** la `DOMContentLoaded`:

```javascript
function applyGlobalPreferences(prefs) {
  if (!prefs) return;
  const root = document.documentElement;

  // Teme și Contrast
  root.setAttribute('data-theme', prefs.theme || 'light');
  root.setAttribute('data-contrast', prefs.contrast || 'normal');

  // Tipografie și Scalare
  root.setAttribute('data-text-size', prefs.textSize || 'm');
  root.setAttribute('data-font', prefs.font || 'default');
  root.setAttribute('data-spacing', prefs.spacing || 'comfortable');

  // Neurodivergență și ADHD
  root.setAttribute('data-bionic', prefs.bionic ? 'true' : 'false');
  root.setAttribute('data-highlight-terms', prefs.highlightKeyTerms ? 'true' : 'false');
  root.setAttribute('data-motion', prefs.motion || 'full');

  // Toggle Reading Ruler dacă e activat
  toggleReadingRuler(prefs.readingRuler);
}
```

### Reguli CSS de adăugat în `web/css/styles.css` (sau `a11y.css`):

```css
/* Scalare Font */
[data-text-size="l"] { font-size: 112.5%; }
[data-text-size="xl"] { font-size: 125%; }
[data-text-size="xxl"] { font-size: 140%; }

/* Fonturi Dislexie & Lizibilitate */
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&display=swap');

[data-font="lexend"] body, 
[data-font="readable"] body {
  font-family: 'Lexend', -apple-system, BlinkMacSystemFont, sans-serif !important;
  letter-spacing: 0.02em;
  word-spacing: 0.05em;
  line-height: 1.7;
}

[data-font="opendyslexic"] body {
  font-family: 'OpenDyslexic', 'Lexend', sans-serif !important;
  letter-spacing: 0.03em;
  line-height: 1.8;
}

/* Contrast Ridicat (WCAG AAA) */
[data-contrast="high"] {
  --color-bg: #000000;
  --color-text: #ffffff;
  --color-border: #ffffff;
  --color-primary: #ffd700; /* Galben de înaltă vizibilitate */
  --color-primary-text: #000000;
}
[data-contrast="high"] button, 
[data-contrast="high"] .btn {
  border: 2px solid #ffffff !important;
  font-weight: 700 !important;
}

/* Reducere Mișcare */
@media (prefers-reduced-motion: reduce), [data-motion="reduced"] {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}
```

---

## 5. Task 3 (P3): Algoritmul de Citire Bionică & Evidențiere Vizuală pentru ADHD

Pentru textele generate (sinteze, sarcini, explicații), aplică funcția de transformare vizuală când `prefs.bionic === true` sau `prefs.highlightKeyTerms === true`:

```javascript
/**
 * Accentuează cuvintele cheie operaționale și aplică Bionic Reading.
 */
function renderAccessibleText(text, options = { bionic: true, highlightTerms: true }) {
  if (!text) return '';

  // Cuvinte cheie operaționale comune în documente de muncă
  const KEY_TERMS_REGEX = /\b(termen|ora|urgent|important|semnează|trimite|descarcă|confirmă|completat|depus|obligatoriu|prioritate|atenție|recomandat|ședință|echipă|luni|marți|miercuri|joi|vineri)\b/gi;

  const words = text.split(/\s+/);
  return words.map(word => {
    // Curățare semne de punctuație pentru verificare
    const cleanWord = word.replace(/[.,:;!?()\[\]]/g, '');
    const isKeyTerm = options.highlightTerms && KEY_TERMS_REGEX.test(cleanWord);

    if (isKeyTerm) {
      return `<strong class="a11y-key-term" style="font-size: 1.08em; text-decoration: underline decoration-color: var(--color-primary);">${word}</strong>`;
    }

    if (options.bionic && cleanWord.length > 3) {
      const splitIdx = Math.ceil(word.length * 0.45);
      const boldPart = word.slice(0, splitIdx);
      const restPart = word.slice(splitIdx);
      return `<b class="bionic-fixation">${boldPart}</b>${restPart}`;
    }

    return word;
  }).join(' ');
}
```

### Stil CSS pentru cuvinte cheie și Bionic Reading:
```css
.a11y-key-term {
  background-color: rgba(254, 240, 138, 0.25);
  padding: 0 3px;
  border-radius: 3px;
  font-weight: 700;
  display: inline-block;
}
.bionic-fixation {
  font-weight: 700;
  opacity: 0.95;
}
```

---

## 6. Task 4 (P3 & P2): Integrare Calendar (Google Calendar & Descarcă .ics)

În ecranele de **Planificator Sarcini (`plan.html`)** și **Sinteză Ședință (`meeting.html`)**, fiecare sarcină extrasă cu dată sau ședință trebuie să aibă 2 acțiuni rapide:

1. **Butonul „📅 Salvează în Google Calendar”**
2. **Butonul „📥 Descarcă fișier (.ics)”**

### Cum se integrează cu Backend-ul:
La click pe butonul de calendar al unui card de sarcină:

```javascript
async function exportTaskToCalendar(task) {
  const payload = {
    title: task.title,
    due_iso: task.due_iso || new Date().toISOString().split('T')[0],
    due_time: "10:00",
    duration_minutes: 30,
    description: task.steps ? task.steps.join('\n') : (task.source_quote || ''),
    location: "Online / Spațiul de lucru"
  };

  const res = await fetch('/api/plan/calendar-link', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const json = await res.json();

  if (json.ok && json.data) {
    // 1. Deschide Google Calendar în tab nou
    window.open(json.data.google_calendar_url, '_blank', 'noopener,noreferrer');

    // 2. Oferă opțiunea de descărcare .ics dacă dorește
    setupIcsDownload(json.data.ics_filename, json.data.ics_content);
  }
}

function setupIcsDownload(filename, icsContent) {
  const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
```

---

## 7. Task 5 (P3): Notificări și Memento-uri în Browser (Browser Notifications)

Utilizatorul a solicitat ca dacă lasă site-ul deschis, acesta să îi **amintească** de sarcinile urgente:

1. **Cerere de permisiune:**
   ```javascript
   async function requestNotificationPermission() {
     if ('Notification' in window && Notification.permission !== 'granted') {
       await Notification.requestPermission();
     }
   }
   ```
2. **Timer de verificare periodică (la fiecare 5 minute):**
   ```javascript
   function startReminderCheck() {
     setInterval(() => {
       const storedTasks = JSON.parse(localStorage.getItem('wp.tasks.v1') || '[]');
       const todayStr = new Date().toISOString().split('T')[0];

       storedTasks.forEach(task => {
         if (task.due_iso === todayStr && !task.notified && !task.done) {
           if (Notification.permission === 'granted') {
             new Notification('Memento PrimaZi: Sarcină azi', {
               body: `${task.title} are termen astăzi!`,
               icon: '/favicon.ico'
             });
             task.notified = true;
           }
         }
       });
       localStorage.setItem('wp.tasks.v1', JSON.stringify(storedTasks));
     }, 5 * 60 * 1000);
   }
   ```
3. **Banner accesibil în pagină (`aria-live="polite"`):**
   Dacă notificările native sunt blocate, afișează un toast vizual discret în partea de sus a ecranului.

---

## 8. Checklist de Verificare pentru P2 (QA & Dovezi)

- [ ] Formularul cu text liber funcționează și nu crapă dacă utilizatorul scrie 500 de caractere.
- [ ] Răspunsul recomandă setări logice (text mărit pentru vedere slabă, bionic/lexend pentru ADHD/dislexie).
- [ ] Setările persistă după reîncărcarea paginii (`F5`) și se propagă pe toate paginile.
- [ ] Butonul de Google Calendar deschide formularul precompletat corect cu titlul și descrierea sarcinii.
- [ ] Fișierul `.ics` descărcat se poate importa direct în Outlook / Apple Calendar.
- [ ] Contrastul culorilor respectă raportul de minim 4.5:1 (sau 7:1 pe high contrast) verificat cu Lighthouse.
- [ ] Niciun diagnostic medical nu apare pe ecran sau în rețea în clar.
