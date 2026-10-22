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
    const raw = localStorage.getItem("primazi_profile") || localStorage.getItem("wp.prefs.v1");
    if (!raw) return { reading_level: "simple", format: "steps" };
    const parsed = JSON.parse(raw);
    if (parsed.answers) {
      return {
        reading_level: parsed.answers.textAmount === "short" ? "simple" : "detailed",
        format: parsed.answers.stepByStep ? "steps" : "paragraphs"
      };
    }
    return parsed.profile || { reading_level: "simple", format: "steps" };
  } catch {
    return { reading_level: "simple", format: "steps" };
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
    tab.classList.toggle("is-active", isActive);
    tab.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  const textarea = document.getElementById("home-input-text");
  const label = document.getElementById("home-input-label");
  const submitBtn = document.getElementById("btn-home-execute");
  const icsBtn = document.getElementById("btn-home-ics");

  if (icsBtn) {
    icsBtn.style.display = mode === "plan" ? "inline-flex" : "none";
  }

  if (mode === "simplify") {
    if (label) label.textContent = "Lipește documentul sau instrucțiunile de simplificat:";
    if (textarea) textarea.placeholder = "Lipește aici proceduri, ghiduri de lucru, fișe de post sau e-mailuri...";
    if (submitBtn) submitBtn.textContent = "Clarifică documentul";
  } else if (mode === "plan") {
    if (label) label.textContent = "Lipește e-mailul sau mesajul cu sarcini și termene:";
    if (textarea) textarea.placeholder = "Lipește aici mesajul primit de la manager sau colegi...";
    if (submitBtn) submitBtn.textContent = "Extrage sarcinile și termenele";
  } else if (mode === "meeting") {
    if (label) label.textContent = "Lipește transcrierea sau notițele din ședință:";
    if (textarea) textarea.placeholder = "Lipește aici discuția sau transcrierea ședinței de lucru...";
    if (submitBtn) submitBtn.textContent = "Rezumă ședința";
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
 * Updates the character counter.
 */
function updateCharCounter() {
  const textarea = document.getElementById("home-input-text");
  const counter = document.getElementById("home-char-counter");
  if (!textarea || !counter) return;
  const count = textarea.value.length;
  counter.textContent = `${count.toLocaleString("ro-RO")} / 12.000 caractere`;
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
export function renderSimplifyResult(data, meta = {}) {
  const container = document.getElementById("home-result-body");
  if (!container) return;

  currentSummaryForTTS = data.summary || "";

  let html = `
    <div class="result-card">
      <h3 class="result-subtitle">Rezumatul documentului</h3>
      <p class="result-summary-text">${escapeHtml(data.summary)}</p>
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
            <span class="step-text">${escapeHtml(step.text)}</span>
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

  setLoading(true, currentMode === "simplify" ? "Se simplifică documentul..." : (currentMode === "plan" ? "Se extrag sarcinile și termenele..." : "Se sintetizează ședința..."));

  try {
    let res;
    if (currentMode === "simplify") {
      res = await simplifyDocument(text, profile);
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

  speakText(currentSummaryForTTS, {
    onEnd: () => {
      isSpeaking = false;
      if (ttsBtn) {
        ttsBtn.textContent = "Ascultă rezumatul";
        ttsBtn.setAttribute("aria-pressed", "false");
      }
      announceToLiveRegion("Redarea audio s-a finalizat.");
    },
    onError: () => {
      isSpeaking = false;
      if (ttsBtn) {
        ttsBtn.textContent = "Ascultă rezumatul";
        ttsBtn.setAttribute("aria-pressed", "false");
      }
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
 * Initializes the Home page interactions.
 */
export function initHomePage() {
  // Mode switcher tabs
  const tabs = document.querySelectorAll(".mode-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const mode = tab.getAttribute("data-mode");
      if (mode) setMode(mode);
    });
  });

  // Quick sample buttons
  const onboardingBtn = document.getElementById("btn-sample-onboarding");
  const emailBtn = document.getElementById("btn-sample-email");
  const meetingBtn = document.getElementById("btn-sample-meeting");

  if (onboardingBtn) onboardingBtn.addEventListener("click", () => loadSample("onboarding"));
  if (emailBtn) emailBtn.addEventListener("click", () => loadSample("email"));
  if (meetingBtn) meetingBtn.addEventListener("click", () => loadSample("meeting"));

  // Textarea input character counter
  const textarea = document.getElementById("home-input-text");
  if (textarea) {
    textarea.addEventListener("input", updateCharCounter);
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

  // Action buttons
  const copyBtn = document.getElementById("btn-home-copy");
  const ttsBtn = document.getElementById("btn-home-tts");
  const icsBtn = document.getElementById("btn-home-ics");
  const retryBtn = document.getElementById("btn-home-retry");

  if (copyBtn) copyBtn.addEventListener("click", copyResultToClipboard);
  if (ttsBtn) ttsBtn.addEventListener("click", toggleTTS);
  if (icsBtn) icsBtn.addEventListener("click", downloadPlanIcs);
  if (retryBtn) retryBtn.addEventListener("click", executeCurrentTask);
}

// Auto-initialize when DOM is ready
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initHomePage);
}

