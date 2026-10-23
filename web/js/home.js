/**
 * home.js - Interactive Home Screen Logic & API Integration
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 * Owner: p3
 *
 * Implements Task N3.2 per docs/NEXT-STEPS.md:
 * - Unified Gemini-style input with mode switching (Clarify, Plan, Meeting)
 * - Quick sample loaders (Onboarding, Task email, Meeting transcript)
 * - Integration with /api/simplify, /api/plan/extract, /api/meeting/summarize via web/shared/api.js
 * - Verbatim quote grounding ("Arată în text") with highlight in source viewer
 * - Read-aloud (TTS) using web/shared/speech.js
 * - One-click clipboard copy with screen-reader announcement
 * - Calendar (.ics) download using web/shared/ics.js for task plans
 */

import { simplifyDocument, extractPlan, summarizeMeeting } from "/shared/api.js";
import { speakText, stopSpeaking, isSynthesisSupported } from "/shared/speech.js";
import { generateIcs, downloadIcsFile } from "/shared/ics.js";
import { saveLibraryItem } from "/js/library-storage.js";
import { transformText, sendTasksToPlanner } from "/js/actions.js";
import { getProfile, getApiProfile } from "/shared/profile.js";

// Embedded sample texts for instant, offline-safe execution
export const SAMPLES = {
  onboarding: `GHID DE ONBOARDING - PRIMA SĂPTĂMÂNĂ LA SC TECH SOLUTIONS SRL

1. Prezentarea la sediu
În prima zi (luni, ora 09:00), te prezinți la recepția clădirii B, etajul 2. Vei fi întâmpinat de colega noastră de la People Operations, Elena, care îți va înmâna ecusonul de acces provizoriu și laptopul de serviciu.

2. Documente administrative obligatorii
Până miercuri, ora 14:00, trebuie să transmiți la HR următoarele documente scanate:
- Copie după cartea de identitate (CI)
- Adeverință medicală de medicina muncii (dacă nu a fost deja trimisă)
- Extras de cont pentru virarea salariului (IBAN)
- Formularul F-12 completat și semnat olograf sau electronic.

3. Întâlnirea cu mentorul (Buddy)
Marți, la ora 11:00, vei avea o sesiune introductivă de 45 de minute cu mentorul tău alocat, Radu. Împreună veți configura mediul de lucru (VPN, acces Jira, Slack) și veți discuta obiectivele pentru primele 30 de zile.

4. Procedura de solicitare a echipamentelor suplimentare
Dacă ai nevoie de adaptări ale spațiului de lucru (tastatură ergonomică, monitor suplimentar, scaun ergonomic sau software specializat), trimite un e-mail către it-support@techsolutions.ro cu titlul „Solicitare echipament ergonomic - Onboarding”, menționând biroul la care ești alocat.`,

  email: `De la: Mihai Georgescu <mihai.georgescu@techsolutions.ro>
Către: Ana Popescu <ana.popescu@techsolutions.ro>
Data: 22 octombrie 2026, 14:30
Subiect: Sarcini urgente pentru săptămâna în curs - Proiectul Alpha

Bună, Ana!

Bine ai venit în echipă! Ca să intrăm direct în ritm, te rog să te ocupi de următoarele lucruri în zilele următoare:

1. Până mâine, 23 octombrie, la ora 17:00, trimite-mi pe Slack lista conturilor pe care ai reușit să le configurezi (VPN, Jira, GitLab). Dacă ai blocaje, dă-mi un semn imediat.

2. Până vineri, 24 octombrie, te rog să citești documentația tehnică a proiectului Alpha din Confluence și să notezi într-un document Google Doc orice termen sau procedură neclară.

3. Completează formularul de securitate IT și semnează politica de confidențialitate cât mai repede, până joi la prânz dacă este posibil, dar cel târziu până la finalul săptămânii viitoare.

4. De asemenea, pregătește un scurt rezumat de 1 pagină despre propunerile tale de îmbunătățire a procesului de testare și trimite-l echipei până miercurea viitoare.

Spor la treabă și dacă ai orice întrebare, suntem aici!

Mihai`,

  meeting: `Transcrierea ședinței de aliniere - Echipa Operațiuni (22 Octombrie 2026)

Participanți: Mihai (Manager), Ana (Asistent Operațiuni), Radu (Senior Dev), Ioana (HR).

Mihai: Bună tuturor! Deschidem ședința scurtă de sincronizare. Avem trei subiecte mari: configurarea echipamentelor Anei, termenul pentru raportul Alpha și organizarea atelierului de săptămâna viitoare.

Ioana: Legat de echipamente, am aprobat cererea Anei pentru monitorul suplimentar. IT-ul îl livrează joi dimineață. Ana, te rog să fii la birou la 10:00 ca să te ajute tehnicianul cu montarea.

Ana: Înțeles, joi la 10:00 voi fi la birou la recepție.

Mihai: Perfect. Decizia luată este că lansăm versiunea internă a raportului vineri, 24 octombrie, la ora 16:00. Radu, tu verifici secțiunea de performanță tehnică până joi la ora 18:00.

Radu: Da, mă ocup eu de secțiunea tehnică și trimit observațiile pe canalul #alpha-ops.

Mihai: Ana, te rog pe tine să preiei tabelul de inventar din anexa 2 și să verifici dacă datele corespund cu livrările din septembrie. Termenul tău este vineri la ora 12:00.

Ana: Sigur, preiau tabelul și îl trimit până vineri la 12:00.

Ioana: În ceea ce privește atelierul de onboarding de luna viitoare, încă nu este clar cine va redacta prezentarea introductivă. Rămâne să stabilim asta în ședința de luni.`
};

// State variables
let currentMode = "simplify";
let currentOriginalText = "";
let currentResultData = null;
let currentPlanTasks = [];
let currentSummaryForTTS = "";
let isSpeaking = false;

/**
 * Escapes HTML characters for safe rendering.
 */
export function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Normalizes text whitespace for quote matching.
 */
export function normalizeWhitespace(str) {
  if (!str) return "";
  return String(str).replace(/\s+/g, " ").trim();
}

/**
 * Reads user preferences from local storage if available.
 */
function getStoredProfile() {
  try {
    return getApiProfile();
  } catch (_) {
    return { reading_level: "simple", format: "steps", needs_notes: "" };
  }
}

/**
 * Switches the active mode tab.
 */
export function setMode(mode) {
  currentMode = mode;
  const tabs = document.querySelectorAll(".mode-tab");
  tabs.forEach(tab => {
    const isActive = tab.getAttribute("data-mode") === mode;
    tab.classList.toggle("is-selected", isActive);
    tab.classList.toggle("is-active", isActive);
    tab.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  const textarea = document.getElementById("home-input-text");
  const label = document.getElementById("home-input-label");
  const submitBtn = document.getElementById("btn-home-execute");
  const icsBtn = document.getElementById("btn-home-ics");
  const modeLabel = document.getElementById("current-mode-label");
  const modeMenu = document.getElementById("mode-dropdown-menu");
  const modeDropdownBtn = document.getElementById("btn-mode-dropdown");

  if (icsBtn) {
    icsBtn.style.display = mode === "plan" ? "inline-flex" : "none";
  }

  // Close mode dropdown menu
  if (modeMenu) modeMenu.style.display = "none";
  if (modeDropdownBtn) modeDropdownBtn.setAttribute("aria-expanded", "false");

  if (mode === "simplify") {
    if (label) label.textContent = "Lipește documentul sau instrucțiunile de simplificat:";
    if (textarea) textarea.placeholder = "Introdu textul sau instrucțiunile de la manager...";
    if (submitBtn) submitBtn.setAttribute("aria-label", "Clarifică documentul");
    if (modeLabel) modeLabel.textContent = "Clarificare";
  } else if (mode === "rewrite") {
    if (label) label.textContent = "Lipește documentul sau atașează PDF-ul pentru rescriere integrală:";
    if (textarea) textarea.placeholder = "Introdu textul sau atașează un fișier PDF (+) pentru rescriere completă fără omisiuni...";
    if (submitBtn) submitBtn.setAttribute("aria-label", "Rescrie tot documentul");
    if (modeLabel) modeLabel.textContent = "Rescriere";
  } else if (mode === "plan") {
    if (label) label.textContent = "Lipește e-mailul sau mesajul cu sarcini și termene:";
    if (textarea) textarea.placeholder = "Lipește aici mesajul cu sarcini și termene...";
    if (submitBtn) submitBtn.setAttribute("aria-label", "Extrage sarcinile și termenele");
    if (modeLabel) modeLabel.textContent = "Planificator";
  } else if (mode === "meeting") {
    if (label) label.textContent = "Lipește transcrierea sau notițele din ședință:";
    if (textarea) textarea.placeholder = "Lipește aici transcrierea ședinței de lucru...";
    if (submitBtn) submitBtn.setAttribute("aria-label", "Rezumă ședința");
    if (modeLabel) modeLabel.textContent = "Ședințe";
  }

  const btnFileSimp = document.getElementById("btn-file-simplify");
  const btnFileRew = document.getElementById("btn-file-rewrite");
  if (btnFileSimp) {
    const isSimp = mode === "simplify";
    btnFileSimp.classList.toggle("is-active", isSimp);
    btnFileSimp.setAttribute("aria-pressed", isSimp ? "true" : "false");
  }
  if (btnFileRew) {
    const isRew = mode === "rewrite";
    btnFileRew.classList.toggle("is-active", isRew);
    btnFileRew.setAttribute("aria-pressed", isRew ? "true" : "false");
  }
}

/**
 * Loads one of the sample texts into the textarea.
 */
export function loadSample(sampleKey) {
  const text = SAMPLES[sampleKey];
  if (!text) return;

  const textarea = document.getElementById("home-input-text");
  if (textarea) {
    textarea.value = text;
    updateCharCounter();
    textarea.focus();
  }

  // Auto-switch mode according to sample
  if (sampleKey === "onboarding") setMode("simplify");
  else if (sampleKey === "email") setMode("plan");
  else if (sampleKey === "meeting") setMode("meeting");

  announceToLiveRegion(`Exemplul ${sampleKey} a fost încărcat.`);
}

/**
 * Updates the character counter and auto-resizes the input.
 */
function updateCharCounter() {
  const textarea = document.getElementById("home-input-text");
  const counter = document.getElementById("home-char-counter");
  const clearBtn = document.getElementById("btn-home-clear");
  if (!textarea) return;

  const count = textarea.value.length;
  if (counter) {
    counter.textContent = `${count.toLocaleString("ro-RO")} / 12.000 caractere`;
  }

  if (clearBtn) {
    clearBtn.style.display = count > 0 ? "inline-flex" : "none";
  }

  // Auto-resize textarea height
  textarea.style.height = "auto";
  if (textarea.scrollHeight > 32) {
    textarea.style.height = Math.min(textarea.scrollHeight, 220) + "px";
  }
}

/**
 * Announces a message to the accessible live region.
 */
function announceToLiveRegion(message) {
  const live = document.getElementById("status-live");
  if (live) {
    live.textContent = "";
    setTimeout(() => { live.textContent = message; }, 40);
  }
}

/**
 * Shows or hides the loading spinner.
 */
export function setLoading(isLoading, message = "Se procesează documentul...") {
  const loadingEl = document.getElementById("home-loading");
  const loadingText = document.getElementById("home-loading-text");
  const submitBtn = document.getElementById("btn-home-execute");

  if (loadingEl) loadingEl.style.display = isLoading ? "flex" : "none";
  if (loadingText) loadingText.textContent = message;
  if (submitBtn) submitBtn.disabled = isLoading;

  if (isLoading) {
    announceToLiveRegion(message);
  }
}

/**
 * Shows an error banner.
 */
export function showError(message) {
  const errBanner = document.getElementById("home-error-banner");
  const errMsg = document.getElementById("home-error-message");
  if (errBanner && errMsg) {
    errMsg.textContent = message;
    errBanner.style.display = "flex";
    errBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  announceToLiveRegion(`Eroare: ${message}`);
}

/**
 * Clears any active error banner.
 */
export function clearError() {
  const errBanner = document.getElementById("home-error-banner");
  if (errBanner) errBanner.style.display = "none";
}

/**
 * Highlights a verbatim quote in the original text viewer.
 */
export function highlightQuoteInViewer(quote) {
  const viewer = document.getElementById("home-source-viewer");
  if (!viewer || !currentOriginalText) return false;

  if (!quote || !quote.trim()) {
    viewer.textContent = currentOriginalText;
    return false;
  }

  const rawText = currentOriginalText;
  const target = quote.trim();
  const idx = rawText.indexOf(target);

  if (idx === -1) {
    // Try normalized match
    viewer.textContent = rawText;
    return false;
  }

  const before = escapeHtml(rawText.substring(0, idx));
  const matched = escapeHtml(rawText.substring(idx, idx + target.length));
  const after = escapeHtml(rawText.substring(idx + target.length));

  viewer.innerHTML = `${before}<mark class="quote-highlight" id="active-quote">${matched}</mark>${after}`;

  const markEl = document.getElementById("active-quote");
  if (markEl) {
    markEl.scrollIntoView({ behavior: "smooth", block: "center" });
    announceToLiveRegion(`Citat evidențiat în textul sursă: „${target}”`);
    return true;
  }

  return false;
}

/**
 * Renders the Simplify result.
 */
/**
 * Formats text with accessible bold highlights and prominent key concepts.
 */
export function formatTextWithHighlights(rawText, keyTerms = [], needsProminence = false) {
  if (!rawText) return "";
  let formatted = escapeHtml(rawText);

  // Convert markdown bold **word** to prominent badges
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, (match, p1) => {
    return `<mark class="keyword-prominent">${p1}</mark>`;
  });

  if (needsProminence) {
    // Highlight specific key terms
    if (Array.isArray(keyTerms)) {
      keyTerms.forEach(kt => {
        const term = typeof kt === "string" ? kt : kt?.term;
        if (term && term.length > 2) {
          const escapedTerm = escapeHtml(term);
          const regex = new RegExp(`(?<!<[^>]*)\\b(${escapedTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})\\b(?![^<]*>)`, "gi");
          formatted = formatted.replace(regex, `<mark class="keyword-prominent">$1</mark>`);
        }
      });
    }

    // Highlight times, dates, and deadlines
    const timeDateRegex = /(?<!<[^>]*)\\b(\\d{1,2}:\\d{2}|luni|marți|miercuri|joi|vineri|\\d{1,2}\\s+(?:ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie))\\b(?![^<]*>)/gi;
    formatted = formatted.replace(timeDateRegex, `<mark class="keyword-prominent">$1</mark>`);
  }

  return formatted;
}

export function renderSimplifyResult(data, meta = {}) {
  const container = document.getElementById("home-result-body");
  if (!container) return;

  currentSummaryForTTS = data.summary || "";

  const profile = getStoredProfile();
  const notesLow = (profile?.needs_notes || "").toLowerCase();
  const isMemoryNeed = /uit|memorie|amintesc|reținere|retinere|checklist|remember|recall/i.test(notesLow);
  const isVisionNeed = /veder|ochi|vizibil|text mare|font mare|litere mari|nu vad|vision|sight/i.test(notesLow);
  const needsProminence = isMemoryNeed || isVisionNeed || document.documentElement.getAttribute("data-highlight-terms") === "true";

  let html = "";

  // Dedicated Memento Card for users with memory/recall needs
  if (isMemoryNeed && data.steps && data.steps.length > 0) {
    const topStep = data.steps[0];
    html += `
      <div class="memory-memento-card" role="region" aria-label="Memento rapid pentru memorie">
        <div class="memento-icon" aria-hidden="true">📌</div>
        <div class="memento-content">
          <h4 class="memory-memento-title">De reținut imediat</h4>
          <p class="memory-memento-body"><strong>Prioritate 1:</strong> ${formatTextWithHighlights(topStep.text, data.key_terms, true)}</p>
        </div>
      </div>
    `;
  }

  html += `
    <div class="result-card" tabindex="0" role="region" aria-label="Rezumatul documentului">
      <h3 class="result-subtitle">Rezumatul documentului</h3>
      <p class="result-summary-text">${formatTextWithHighlights(data.summary, data.key_terms, needsProminence)}</p>
    </div>
  `;

  if (data.steps && data.steps.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Pași concreți de urmat</h3>
        <ol class="steps-list">
    `;
    data.steps.forEach((step, idx) => {
      const stepQuote = step.source_quote ? escapeHtml(step.source_quote) : "";
      html += `
        <li class="step-item" id="step-${idx + 1}">
          <div class="step-content">
            <span class="step-number">${step.n || idx + 1}.</span>
            <span class="step-text">${formatTextWithHighlights(step.text, data.key_terms, needsProminence)}</span>
          </div>
          ${stepQuote ? `
            <div class="step-quote-action">
              <button type="button" class="btn-quote" data-quote="${stepQuote}" aria-label="Arată citatul pentru pasul ${step.n || idx + 1} în textul original">
                <svg class="btn-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span>Arată în text</span>
              </button>
            </div>
          ` : ""}
        </li>
      `;
    });
    html += `</ol></div>`;
  }

  if (data.key_terms && data.key_terms.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Termeni și concepte explicate</h3>
        <dl class="terms-list">
    `;
    data.key_terms.forEach(term => {
      html += `
        <dt class="term-title">${escapeHtml(term.term)}</dt>
        <dd class="term-desc">${escapeHtml(term.explanation)}</dd>
      `;
    });
    html += `</dl></div>`;
  }

  if (data.questions_to_ask && data.questions_to_ask.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Întrebări utile de pus managerului sau colegilor</h3>
        <ul class="questions-list">
    `;
    data.questions_to_ask.forEach(q => {
      html += `<li>${escapeHtml(q)}</li>`;
    });
    html += `</ul></div>`;
  }

  container.innerHTML = html;
  attachQuoteButtons(container);
}

/**
 * Renders the full Rewrite result (without omissions).
 */
export function renderRewriteResult(data, meta = {}) {
  const container = document.getElementById("home-result-body");
  if (!container) return;

  const rewrittenText = data.text || (Array.isArray(data.items) ? data.items.join("\n\n") : "");
  currentSummaryForTTS = rewrittenText;

  // Split into clean paragraphs
  const paragraphs = rewrittenText.split(/\n\s*\n/).filter(p => p.trim());
  const profile = getStoredProfile();
  const notesLow = (profile?.needs_notes || "").toLowerCase();
  const isMemoryNeed = /uit|memorie|amintesc|reținere|retinere|checklist|remember|recall/i.test(notesLow);
  const isVisionNeed = /veder|ochi|vizibil|text mare|font mare|litere mari|nu vad|vision|sight/i.test(notesLow);
  const needsProminence = isMemoryNeed || isVisionNeed || document.documentElement.getAttribute("data-highlight-terms") === "true";
  const paragraphsHtml = paragraphs.map(p => `<p class="result-summary-text" style="margin-bottom: var(--space-md); font-size: 1.05rem; line-height: 1.6;">${formatTextWithHighlights(p, [], needsProminence)}</p>`).join("");

  let html = `
    <div class="result-card">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-sm); flex-wrap: wrap; gap: var(--space-xs);">
        <h3 class="result-subtitle" style="margin: 0;">Rescriere integrală (fără omisiuni)</h3>
        <span style="font-size: 0.85rem; color: var(--gemini-text-muted); background: var(--bg-surface-hover); padding: 2px 8px; border-radius: var(--radius-full);">Text adaptat integral</span>
      </div>
      <div class="rewrite-content">
        ${paragraphsHtml || `<p class="result-summary-text">${escapeHtml(rewrittenText)}</p>`}
      </div>
    </div>
  `;

  container.innerHTML = html;
}

/**
 * Renders the Plan result.
 */
export function renderPlanResult(data, meta = {}) {
  const container = document.getElementById("home-result-body");
  if (!container) return;

  currentPlanTasks = data.tasks || [];
  const icsBtn = document.getElementById("btn-home-ics");
  if (icsBtn) icsBtn.style.display = "inline-flex";

  const taskCount = currentPlanTasks.length;
  currentSummaryForTTS = `Au fost identificate ${taskCount} sarcini și termene limită.`;

  let html = `
    <div class="result-card">
      <h3 class="result-subtitle">Sarcini și termene identificate (${taskCount})</h3>
      <div class="tasks-grid">
  `;

  if (!currentPlanTasks.length) {
    html += `<p class="result-summary-text">Nu au fost detectate sarcini concrete în textul furnizat.</p>`;
  } else {
    currentPlanTasks.forEach((task, idx) => {
      const isAmbiguous = task.needs_confirmation === true || !task.due_iso;
      const quoteAttr = task.source_quote ? escapeHtml(task.source_quote) : "";

      html += `
        <article class="task-card ${isAmbiguous ? 'is-ambiguous' : ''}" id="task-${task.id || idx}">
          <div class="task-header">
            <h4 class="task-title">${escapeHtml(task.title)}</h4>
            ${task.priority ? `<span class="priority-tag priority-${escapeHtml(task.priority)}">${escapeHtml(task.priority)}</span>` : ''}
          </div>

          <div class="task-due-info">
            <strong>Termen:</strong> ${escapeHtml(task.due_text || "Nespecificat")}
            ${isAmbiguous ? `
              <span class="badge-warning" role="status">
                ⚠️ Necesită confirmare: termen ambiguu
              </span>
            ` : ""}
          </div>

          ${task.steps && task.steps.length > 0 ? `
            <div class="task-substeps">
              <strong>Sub-pași:</strong>
              <ul>
                ${task.steps.map(s => `<li>${escapeHtml(s)}</li>`).join("")}
              </ul>
            </div>
          ` : ""}

          ${quoteAttr ? `
            <div class="task-quote-action">
              <button type="button" class="btn-quote" data-quote="${quoteAttr}" aria-label="Arată citatul pentru sarcina «${escapeHtml(task.title)}»">
                <svg class="btn-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span>Arată în text</span>
              </button>
            </div>
          ` : ""}
        </article>
      `;
    });
  }

  html += `</div></div>`;
  container.innerHTML = html;
  attachQuoteButtons(container);
}

/**
 * Renders the Meeting result.
 */
export function renderMeetingResult(data, meta = {}) {
  const container = document.getElementById("home-result-body");
  if (!container) return;

  currentSummaryForTTS = data.summary || "";

  let html = `
    <div class="result-card">
      <h3 class="result-subtitle">Sinteza discuției</h3>
      <p class="result-summary-text">${escapeHtml(data.summary)}</p>
    </div>
  `;

  if (data.decisions && data.decisions.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Decizii luate</h3>
        <ul class="decisions-list">
    `;
    data.decisions.forEach(d => {
      const q = d.source_quote ? escapeHtml(d.source_quote) : "";
      html += `
        <li>
          <span>${escapeHtml(d.text)}</span>
          ${q ? `
            <button type="button" class="btn-quote btn-quote-inline" data-quote="${q}" aria-label="Arată citatul deciziei în transcriere">
              <span>Arată citat</span>
            </button>
          ` : ""}
        </li>
      `;
    });
    html += `</ul></div>`;
  }

  if (data.action_items && data.action_items.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Plan de acțiuni și responsabili</h3>
        <div class="tasks-grid">
    `;
    data.action_items.forEach((item, idx) => {
      const q = item.source_quote ? escapeHtml(item.source_quote) : "";
      html += `
        <article class="task-card">
          <div class="task-header">
            <h4 class="task-title">${escapeHtml(item.task)}</h4>
            ${item.who ? `<span class="badge-person">Responsabil: ${escapeHtml(item.who)}</span>` : '<span class="badge-person">Nealocat</span>'}
          </div>
          ${item.due_text ? `<div class="task-due-info"><strong>Termen:</strong> ${escapeHtml(item.due_text)}</div>` : ""}
          ${q ? `
            <div class="task-quote-action">
              <button type="button" class="btn-quote" data-quote="${q}" aria-label="Arată citatul pentru acțiunea «${escapeHtml(item.task)}»">
                <svg class="btn-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span>Arată în text</span>
              </button>
            </div>
          ` : ""}
        </article>
      `;
    });
    html += `</div></div>`;
  }

  if (data.unclear_points && data.unclear_points.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Puncte rămase neclare sau de confirmat</h3>
        <ul class="unclear-list">
          ${data.unclear_points.map(p => `<li>⚠️ ${escapeHtml(p)}</li>`).join("")}
        </ul>
      </div>
    `;
  }

  container.innerHTML = html;
  attachQuoteButtons(container);
}

/**
 * Attaches click event listeners to all "Arată în text" buttons.
 */
function attachQuoteButtons(container) {
  const buttons = container.querySelectorAll(".btn-quote");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      const quote = btn.getAttribute("data-quote");
      if (quote) {
        highlightQuoteInViewer(quote);
      }
    });
  });
}

/**
 * Executes the currently selected task against the API.
 */
export async function executeCurrentTask() {
  clearError();
  const textarea = document.getElementById("home-input-text");
  if (!textarea) return;

  const text = textarea.value.trim();
  if (!text) {
    showError("Te rugăm să lipești sau să scrii un text înainte de a lansa analiza.");
    textarea.focus();
    return;
  }

  currentOriginalText = text;
  const profile = getStoredProfile();

  // Populate original source viewer
  const viewer = document.getElementById("home-source-viewer");
  if (viewer) {
    viewer.textContent = currentOriginalText;
  }

  setLoading(true, currentMode === "simplify" ? "Se simplifică documentul..." : (currentMode === "rewrite" ? "Se rescrie documentul integral..." : (currentMode === "plan" ? "Se extrag sarcinile și termenele..." : "Se sintetizează ședința...")));

  try {
    let res;
    if (currentMode === "simplify") {
      res = await simplifyDocument(text, profile);
    } else if (currentMode === "rewrite") {
      res = await transformText(text, "rewrite", profile);
    } else if (currentMode === "plan") {
      res = await extractPlan(text, null, profile);
    } else if (currentMode === "meeting") {
      res = await summarizeMeeting(text, null, profile);
    }

    setLoading(false);

    if (!res || !res.ok) {
      const errMsg = (res && res.error && res.error.message_ro) || "Nu s-a putut procesa documentul. Te rugăm să reîncerci.";
      showError(errMsg);
      return;
    }

    currentResultData = res.data;

    // Reset save to library button state
    const saveBtn = document.getElementById("btn-home-save-library");
    if (saveBtn) {
      saveBtn.textContent = "Salvează în bibliotecă";
      saveBtn.classList.remove("btn-success");
      saveBtn.disabled = false;
    }

    // Display AI notice and warnings
    const noticeEl = document.getElementById("home-ai-notice");
    if (noticeEl && res.meta && res.meta.ai_notice_ro) {
      noticeEl.textContent = res.meta.ai_notice_ro;
    }

    const warnContainer = document.getElementById("home-warnings-container");
    if (warnContainer) {
      if (res.meta && res.meta.warnings && res.meta.warnings.length > 0) {
        warnContainer.innerHTML = res.meta.warnings.map(w => `<p>⚠️ ${escapeHtml(w)}</p>`).join("");
        warnContainer.style.display = "block";
      } else {
        warnContainer.style.display = "none";
      }
    }

    // Render structured results
    if (currentMode === "simplify") {
      renderSimplifyResult(res.data, res.meta);
    } else if (currentMode === "rewrite") {
      renderRewriteResult(res.data, res.meta);
    } else if (currentMode === "plan") {
      renderPlanResult(res.data, res.meta);
    } else if (currentMode === "meeting") {
      renderMeetingResult(res.data, res.meta);
    }

    const resultsSection = document.getElementById("home-results-section");
    if (resultsSection) {
      resultsSection.style.display = "block";
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    announceToLiveRegion("Rezultatele au fost generate cu succes.");
  } catch (err) {
    setLoading(false);
    showError("A apărut o problemă la procesare. Te rugăm să verifici conexiunea și să reîncerci.");
  }
}

/**
 * Copies the current structured results to the clipboard.
 */
export async function copyResultToClipboard() {
  const container = document.getElementById("home-result-body");
  if (!container) return;

  const textToCopy = container.innerText || container.textContent || "";
  if (!textToCopy) return;

  try {
    await navigator.clipboard.writeText(textToCopy);
    const copyBtn = document.getElementById("btn-home-copy");
    if (copyBtn) {
      const originalText = copyBtn.textContent;
      copyBtn.textContent = "Copiat! ✓";
      copyBtn.classList.add("btn-success");
      setTimeout(() => {
        copyBtn.textContent = originalText;
        copyBtn.classList.remove("btn-success");
      }, 2000);
    }
    announceToLiveRegion("Rezultatul a fost copiat în clipboard.");
  } catch {
    showError("Copierea automată nu este permisă de browser. Selectează textul manual.");
  }
}

/**
 * Toggles Text to Speech read-aloud.
 */
export function toggleTTS() {
  const ttsBtn = document.getElementById("btn-home-tts");

  if (isSpeaking) {
    stopSpeaking();
    isSpeaking = false;
    if (ttsBtn) {
      ttsBtn.textContent = "Ascultă rezumatul";
      ttsBtn.setAttribute("aria-pressed", "false");
    }
    announceToLiveRegion("Redarea audio a fost oprită.");
    window.dispatchEvent(new CustomEvent("primazi:speech-state", { detail: { state: "idle" } }));
    return;
  }

  if (!currentSummaryForTTS) {
    announceToLiveRegion("Nu există un rezumat disponibil pentru citire.");
    return;
  }

  if (!isSynthesisSupported()) {
    showError("Sinteza vocală nu este suportată pe acest browser/dispozitiv.");
    return;
  }

  isSpeaking = true;
  if (ttsBtn) {
    ttsBtn.textContent = "Oprește audio";
    ttsBtn.setAttribute("aria-pressed", "true");
  }
  window.dispatchEvent(new CustomEvent("primazi:speech-state", { detail: { state: "speaking" } }));

  speakText(currentSummaryForTTS, {
    onEnd: () => {
      isSpeaking = false;
      if (ttsBtn) {
        ttsBtn.textContent = "Ascultă rezumatul";
        ttsBtn.setAttribute("aria-pressed", "false");
      }
      announceToLiveRegion("Redarea audio s-a finalizat.");
      window.dispatchEvent(new CustomEvent("primazi:speech-state", { detail: { state: "idle" } }));
    },
    onError: () => {
      isSpeaking = false;
      if (ttsBtn) {
        ttsBtn.textContent = "Ascultă rezumatul";
        ttsBtn.setAttribute("aria-pressed", "false");
      }
      window.dispatchEvent(new CustomEvent("primazi:speech-state", { detail: { state: "idle" } }));
    }
  });
}

/**
 * Downloads the calendar .ics file for plan tasks.
 */
export function downloadPlanIcs() {
  if (!currentPlanTasks || !currentPlanTasks.length) {
    showError("Nu există sarcini disponibile pentru descărcare în calendar.");
    return;
  }

  const icsContent = generateIcs(currentPlanTasks);
  downloadIcsFile("primazi-plan.ics", icsContent);
  announceToLiveRegion("Fișierul calendar primazi-plan.ics a fost descărcat.");
}

/**
 * Saves the current result and source text into browser-only storage (wp.library.v1).
 */
export function saveCurrentResultToLibrary() {
  if (!currentResultData) {
    showError("Nu există un rezultat disponibil pentru salvare.");
    return;
  }

  // Derive title from text or summary
  let title = "";
  if (currentOriginalText) {
    const firstLine = currentOriginalText.split("\n")[0].trim();
    if (firstLine.length > 5) {
      title = firstLine.slice(0, 80);
    }
  }
  if (!title && currentResultData.summary) {
    title = currentResultData.summary.slice(0, 80);
  }
  if (!title) {
    title = currentMode === "simplify" ? "Clarificare document" : currentMode === "plan" ? "Plan de sarcini" : "Sinteză ședință";
  }

  const itemToSave = {
    mode: currentMode,
    title: title,
    createdAt: new Date().toISOString(),
    sourceText: currentOriginalText,
    resultData: currentResultData,
    tags: [currentMode]
  };

  try {
    saveLibraryItem(itemToSave);
    const saveBtn = document.getElementById("btn-home-save-library");
    if (saveBtn) {
      saveBtn.textContent = "Salvat în bibliotecă! ✓";
      saveBtn.classList.add("btn-success");
    }
    announceToLiveRegion("Documentul a fost salvat în biblioteca locală.");
  } catch {
    showError("Nu s-a putut salva documentul în bibliotecă.");
  }
}

/**
 * Populates dynamic saved items in the sidebar under Blocnotesuri.
 */
function populateSidebarNotebooks() {
  const list = document.getElementById("sidebar-notebooks-list");
  if (!list) return;

  try {
    const raw = localStorage.getItem("wp.library.v1");
    if (!raw) return;
    const items = JSON.parse(raw);
    if (!Array.isArray(items) || items.length === 0) return;

    list.innerHTML = "";
    items.slice(0, 5).forEach(item => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = "#";
      a.className = "sidebar-item-link";
      a.innerHTML = `
        <svg class="nav-icon" style="width: 14px; height: 14px;" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
        <span>${escapeHtml(item.title || "Document salvat")}</span>
      `;
      a.addEventListener("click", (e) => {
        e.preventDefault();
        const textarea = document.getElementById("home-input-text");
        if (textarea && item.source_text) {
          textarea.value = item.source_text;
          if (item.mode) setMode(item.mode);
          updateCharCounter();
          executeCurrentTask();
        }
      });
      li.appendChild(a);
      list.appendChild(li);
    });
  } catch {}
}

/**
 * Handles quick text transformation on the active result.
 * @param {string} mode - "shorter" | "bullets" | "steps" | "easy_read"
 * @param {string} labelRo - Human-friendly Romanian mode label
 */
export async function handleTransform(mode, labelRo) {
  if (!currentOriginalText) return;
  const banner = document.getElementById("home-transform-banner");
  const textEl = document.getElementById("home-transform-text");
  const container = document.getElementById("home-result-body");
  if (!container) return;

  announceToLiveRegion(`Se transformă textul: ${labelRo}...`);
  if (banner && textEl) {
    textEl.textContent = `Se transformă: ${labelRo}...`;
    banner.style.display = "flex";
  }

  const res = await transformText(currentOriginalText, mode, getStoredProfile());
  if (res && res.ok && res.data) {
    if (banner && textEl) {
      textEl.textContent = `Versiune transformată: ${labelRo}`;
      banner.style.display = "flex";
    }
    renderTransformedResult(res.data, labelRo);
    announceToLiveRegion(`Transformare finalizată: ${labelRo}`);
  } else {
    showError("Transformarea nu a putut fi aplicată.");
    if (banner) banner.style.display = "none";
  }
}

/**
 * Renders transformed text or bullets into the result body.
 */
export function renderTransformedResult(data, label) {
  const container = document.getElementById("home-result-body");
  if (!container) return;

  if (data.items && Array.isArray(data.items)) {
    currentSummaryForTTS = data.items.join(". ");
    let html = `
      <div class="result-card">
        <h3 class="result-subtitle">${escapeHtml(label)}</h3>
        <ul class="transformed-list" style="padding-left: 20px; line-height: 1.8; margin-top: var(--space-sm);">
          ${data.items.map(it => `<li style="margin-bottom: var(--space-xs);">${escapeHtml(it)}</li>`).join("")}
        </ul>
      </div>
    `;
    container.innerHTML = html;
  } else if (data.text) {
    currentSummaryForTTS = data.text;
    container.innerHTML = `
      <div class="result-card">
        <h3 class="result-subtitle">${escapeHtml(label)}</h3>
        <p class="result-summary-text">${escapeHtml(data.text)}</p>
      </div>
    `;
  }
}

/**
 * Restores original analysis result.
 */
export function restoreOriginalResult() {
  const banner = document.getElementById("home-transform-banner");
  if (banner) banner.style.display = "none";
  if (!currentResultData) return;

  if (currentMode === "simplify") {
    renderSimplifyResult(currentResultData);
  } else if (currentMode === "plan") {
    renderPlanResult(currentResultData);
  } else if (currentMode === "meeting") {
    renderMeetingResult(currentResultData);
  }
  announceToLiveRegion("S-a revenit la rezultatul inițial.");
}

/**
 * Initializes the Home page interactions.
 */
export function initHomePage() {
  // Mode switcher tabs
  const tabs = document.querySelectorAll(".mode-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const mode = tab.getAttribute("data-mode");
      if (mode) {
        setMode(mode);
        const modeMenu = document.getElementById("mode-dropdown-menu");
        if (modeMenu) modeMenu.style.display = "none";
        const modeBtn = document.getElementById("btn-mode-dropdown");
        if (modeBtn) modeBtn.setAttribute("aria-expanded", "false");
      }
    });
  });

  // Capsule attachment: direct PDF / Document upload
  const attachBtn = document.getElementById("btn-capsule-attach");
  const fileInput = document.getElementById("home-file-input");
  const fileChip = document.getElementById("capsule-file-chip");
  const fileNameSpan = document.getElementById("capsule-file-name");
  const removeFileBtn = document.getElementById("btn-remove-file");

  if (attachBtn && fileInput) {
    attachBtn.addEventListener("click", (e) => {
      e.preventDefault();
      fileInput.click();
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      if (fileChip && fileNameSpan) {
        fileNameSpan.textContent = `Se extrage: ${file.name}...`;
        fileChip.style.display = "inline-flex";
      }

      announceToLiveRegion(`Se extrage textul din ${file.name}...`);

      try {
        if (file.name.endsWith(".txt") || file.name.endsWith(".md")) {
          const reader = new FileReader();
          reader.onload = (evt) => {
            const content = evt.target.result;
            const textarea = document.getElementById("home-input-text");
            if (textarea) {
              textarea.value = content;
              updateCharCounter();
              textarea.focus();
            }
            if (fileNameSpan) fileNameSpan.textContent = file.name;
            const fileActionPills = document.getElementById("file-action-pills");
            if (fileActionPills) fileActionPills.style.display = "flex";
            announceToLiveRegion(`Fișierul ${file.name} a fost încărcat.`);
          };
          reader.readAsText(file);
        } else {
          const formData = new FormData();
          formData.append("file", file);

          const res = await fetch("/api/extract-text", {
            method: "POST",
            body: formData
          });

          if (!res.ok) {
            let errJson = null;
            try { errJson = await res.json(); } catch (_) {}
            const msg = errJson?.error?.message_ro || `Eroare la extragerea textului (${res.status}).`;
            alert(msg);
            if (fileChip) fileChip.style.display = "none";
            return;
          }

          const result = await res.json();
          const extractedText = result.data?.text || "";

          if (!extractedText.trim()) {
            if (result.data?.needs_ocr) {
              alert("Fișierul PDF este o imagine scanată fără text selectabil (necesită OCR).");
            } else {
              alert("Nu s-a putut extrage text din acest fișier PDF.");
            }
            if (fileChip) fileChip.style.display = "none";
            return;
          }

          const textarea = document.getElementById("home-input-text");
          if (textarea) {
            textarea.value = extractedText;
            updateCharCounter();
            textarea.focus();
          }

          if (fileNameSpan) {
            const pageInfo = result.data.pages ? ` (${result.data.pages} pag.)` : "";
            fileNameSpan.textContent = `${file.name}${pageInfo}`;
          }

          const fileActionPills = document.getElementById("file-action-pills");
          if (fileActionPills) fileActionPills.style.display = "flex";
          announceToLiveRegion(`Documentul ${file.name} a fost extras cu succes.`);
        }
      } catch (err) {
        console.error("File extraction error:", err);
        alert("A apărut o problemă la procesarea fișierului PDF.");
        if (fileChip) fileChip.style.display = "none";
      }
    });
  }

  if (removeFileBtn) {
    removeFileBtn.addEventListener("click", () => {
      if (fileInput) fileInput.value = "";
      if (fileChip) fileChip.style.display = "none";
      const fileActionPills = document.getElementById("file-action-pills");
      if (fileActionPills) fileActionPills.style.display = "none";
      const textarea = document.getElementById("home-input-text");
      if (textarea) {
        textarea.value = "";
        updateCharCounter();
      }
      announceToLiveRegion("Fișierul atașat a fost eliminat.");
    });
  }

  // Capsule mode dropdown toggle
  const modeBtn = document.getElementById("btn-mode-dropdown");
  const modeMenu = document.getElementById("mode-dropdown-menu");
  if (modeBtn && modeMenu) {
    modeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = modeMenu.style.display === "flex";
      modeMenu.style.display = isOpen ? "none" : "flex";
      modeBtn.setAttribute("aria-expanded", isOpen ? "false" : "true");
    });
  }

  // File action choice buttons (Simplifică vs Rescrie)
  const btnFileSimplify = document.getElementById("btn-file-simplify");
  const btnFileRewrite = document.getElementById("btn-file-rewrite");
  if (btnFileSimplify) {
    btnFileSimplify.addEventListener("click", () => {
      setMode("simplify");
    });
  }
  if (btnFileRewrite) {
    btnFileRewrite.addEventListener("click", () => {
      setMode("rewrite");
    });
  }

  // Quick suggestion action chips
  document.querySelectorAll(".gemini-action-chip").forEach(chip => {
    if (chip.tagName.toLowerCase() === "a") return;
    chip.addEventListener("click", () => {
      const sample = chip.getAttribute("data-sample");
      const mode = chip.getAttribute("data-mode");
      if (mode) setMode(mode);
      if (sample) loadSample(sample);
      if (sample || mode) {
        executeCurrentTask();
      }
    });
  });

  // Speech dictation on mic button
  const micBtn = document.getElementById("btn-capsule-mic");
  if (micBtn && typeof window !== "undefined") {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.lang = "ro-RO";
      recognition.continuous = false;
      recognition.interimResults = false;

      let isListening = false;
      recognition.onstart = () => {
        isListening = true;
        micBtn.style.color = "var(--primary)";
        announceToLiveRegion("Ascult... Vorbește acum.");
      };
      recognition.onend = () => {
        isListening = false;
        micBtn.style.color = "";
      };
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const textarea = document.getElementById("home-input-text");
        if (textarea) {
          textarea.value = (textarea.value + " " + transcript).trim();
          updateCharCounter();
          textarea.focus();
        }
      };
      recognition.onerror = () => {
        isListening = false;
        micBtn.style.color = "";
      };

      micBtn.addEventListener("click", () => {
        if (!isListening) {
          try { recognition.start(); } catch {}
        } else {
          try { recognition.stop(); } catch {}
        }
      });
    } else {
      micBtn.title = "Dictarea vocală nu este suportată în acest browser";
    }
  }

  // Close menus when clicking outside
  document.addEventListener("click", (e) => {
    if (attachMenu && !attachMenu.contains(e.target) && e.target !== attachBtn) {
      attachMenu.style.display = "none";
      if (attachBtn) attachBtn.setAttribute("aria-expanded", "false");
    }
    if (modeMenu && !modeMenu.contains(e.target) && e.target !== modeBtn) {
      modeMenu.style.display = "none";
      if (modeBtn) modeBtn.setAttribute("aria-expanded", "false");
    }
  });

  // Textarea input character counter and Enter-to-execute
  const textarea = document.getElementById("home-input-text");
  if (textarea) {
    textarea.addEventListener("input", updateCharCounter);
    textarea.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        executeCurrentTask();
      }
    });
  }

  // Clear button
  const clearBtn = document.getElementById("btn-home-clear");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (textarea) {
        textarea.value = "";
        updateCharCounter();
        textarea.focus();
      }
      clearError();
      announceToLiveRegion("Câmpul de text a fost golit.");
    });
  }

  // Form submit
  const form = document.getElementById("home-input-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      executeCurrentTask();
    });
  }

  // Submit / Send Arrow Button explicit click
  const submitBtn = document.getElementById("btn-home-execute");
  if (submitBtn) {
    submitBtn.addEventListener("click", (e) => {
      e.preventDefault();
      executeCurrentTask();
    });
  }

  // Action buttons
  const saveLibraryBtn = document.getElementById("btn-home-save-library");
  const copyBtn = document.getElementById("btn-home-copy");
  const ttsBtn = document.getElementById("btn-home-tts");
  const ttsActionBtn = document.getElementById("btn-action-tts");
  const icsBtn = document.getElementById("btn-home-ics");
  const retryBtn = document.getElementById("btn-home-retry");

  // Wave 2 F3 Result Action Bar buttons
  const shorterBtn = document.getElementById("btn-action-shorter");
  const bulletsBtn = document.getElementById("btn-action-bullets");
  const stepsBtn = document.getElementById("btn-action-steps");
  const easyReadBtn = document.getElementById("btn-action-easyread");
  const planBtn = document.getElementById("btn-action-plan");
  const resetTransformBtn = document.getElementById("btn-transform-reset");

  if (saveLibraryBtn) saveLibraryBtn.addEventListener("click", saveCurrentResultToLibrary);
  if (copyBtn) copyBtn.addEventListener("click", copyResultToClipboard);
  if (ttsBtn) ttsBtn.addEventListener("click", toggleTTS);
  if (ttsActionBtn) ttsActionBtn.addEventListener("click", toggleTTS);
  if (icsBtn) icsBtn.addEventListener("click", downloadPlanIcs);
  if (retryBtn) retryBtn.addEventListener("click", executeCurrentTask);

  if (shorterBtn) shorterBtn.addEventListener("click", () => handleTransform("shorter", "Versiune mai scurtă"));
  if (bulletsBtn) bulletsBtn.addEventListener("click", () => handleTransform("bullets", "Puncte cheie"));
  if (stepsBtn) stepsBtn.addEventListener("click", () => handleTransform("steps", "Pași concreți"));
  if (easyReadBtn) easyReadBtn.addEventListener("click", () => handleTransform("easy_read", "Explicare simplă"));
  if (resetTransformBtn) resetTransformBtn.addEventListener("click", restoreOriginalResult);

  if (planBtn) {
    planBtn.addEventListener("click", () => {
      let tasksToSend = [];
      if (currentPlanTasks && currentPlanTasks.length > 0) {
        tasksToSend = currentPlanTasks;
      } else if (currentResultData && Array.isArray(currentResultData.action_items) && currentResultData.action_items.length > 0) {
        tasksToSend = currentResultData.action_items.map((item, idx) => ({
          id: "task_" + Date.now() + "_" + idx,
          title: item.task || "Sarcină din ședință",
          due_iso: item.due_iso || null,
          due_text: item.due_text || null,
          needs_confirmation: Boolean(item.needs_confirmation),
          priority: "normal",
          steps: item.who ? ["Responsabil: " + item.who] : [],
          source_quote: item.source_quote || null,
          completed: false
        }));
      } else if (currentResultData && Array.isArray(currentResultData.steps) && currentResultData.steps.length > 0) {
        tasksToSend = currentResultData.steps;
      }

      if (tasksToSend.length > 0) {
        sendTasksToPlanner(tasksToSend);
        announceToLiveRegion("Sarcinile au fost salvate în Planificator.");
        const originalContent = planBtn.innerHTML;
        planBtn.innerHTML = `
          <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Salvat în plan!</span>
        `;
        setTimeout(() => {
          planBtn.innerHTML = originalContent;
        }, 3000);
      } else {
        announceToLiveRegion("Nu există sarcini identificate pentru adăugat în plan.");
      }
    });
  }

  // Populate dynamic Notebooks from Library storage
  populateSidebarNotebooks();
}

// Auto-initialize when DOM is ready
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initHomePage);
}

