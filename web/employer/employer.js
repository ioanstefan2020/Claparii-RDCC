/**
 * employer.js - Employer Document Cognitive Accessibility Audit UI
 * Owner: p3
 * Contract: docs/CONTRACTS.md §3.6
 *
 * Capabilities:
 * - Loads sample onboarding text or uploads .txt documents.
 * - Live character counter (max 12.000 chars per CONTRACTS §1).
 * - Calls POST /api/employer/analyze with graceful fallback to fixture.json (?mock=1 or offline).
 * - Computes & renders Readability Dashboard (score, sentence metrics, expandable long sentences).
 * - Renders Clarity Issues with verbatim quote highlights and actionable fixes.
 * - Displays Easy-to-Read Romanian rewrite with copy, download, and Web Speech TTS.
 * - Displays Recommended Workplace Adjustments.
 * - Fully accessible: screen reader announcements (#status-live) and programmatic focus shift.
 */
import { applyA11yPrefs } from "/shared/profile.js";

// Embedded fallback sample in case data/samples/onboarding_ro.txt cannot be fetched
const FALLBACK_SAMPLE = `Bine ai venit în echipa Companie Exemplu SRL!

Prima ta săptămână

Luni, ora 09:00 – Te prezinți la recepția clădirii B și ceri cardul de acces. Persoana de contact este Mihaela Popescu din departamentul de Resurse Umane (HR).

Luni, ora 10:00 – Ședința de onboarding cu managerul tău direct, Andrei Ionescu. Vei primi laptopul și conturile de acces.

Până miercuri, 28 octombrie, trebuie să completezi în portalul intern formularul F-12 (date personale și bancare) și să semnezi digital politica de securitate a informației (SecInfo v3).

Joi, ora 14:00 – Training obligatoriu de securitate cibernetică, online. Link-ul de participare îți va fi trimis pe e-mail de către echipa IT.

Până vineri, 30 octombrie, trebuie să parcurgi cursul „Introducere în procesele interne" din platforma de e-learning și să trimiți managerului un rezumat de maximum o pagină.

În prima lună se așteaptă să atingi nivelul de autonomie operațională prevăzut în planul 30-60-90, în conformitate cu KPI-urile agreate cu managerul, având în vedere alinierea la cultura organizațională și la valorile companiei.

Dacă ai nevoie de adaptări ale mediului de lucru, te rugăm să le comunici către HR în termen de 14 zile de la data angajării, la adresa hr@exemplu.example.`;

const ISSUE_KIND_LABELS = {
  jargon: "Jargon corporatist",
  long_sentence: "Frază prea lungă",
  missing_deadline: "Termen lipsă",
  vague_instruction: "Instrucțiune vagă",
  missing_structure: "Structură deficitară"
};

const MAX_CHARS = 12000;

// DOM References
const form = document.getElementById("employer-form");
const docTypeSelect = document.getElementById("doc-type");
const fileInput = document.getElementById("file-upload");
const docTextArea = document.getElementById("document-text");
const btnLoadSample = document.getElementById("btn-load-sample");
const btnClear = document.getElementById("btn-clear");
const btnAnalyze = document.getElementById("btn-analyze");
const charCounter = document.getElementById("char-counter");
const statusLive = document.getElementById("status-live");
const statusBanner = document.getElementById("status-banner");

// Results DOM References
const resultsSection = document.getElementById("results-section");
const resultsHeading = document.getElementById("results-heading");
const aiNoticeText = document.getElementById("ai-notice-text");
const warningsContainer = document.getElementById("warnings-container");

const scoreValue = document.getElementById("score-value");
const scoreBadge = document.getElementById("score-badge");
const scoreCircle = document.getElementById("score-circle");
const scoreDescription = document.getElementById("score-description");
const metricSentenceCount = document.getElementById("metric-sentence-count");
const metricAvgWords = document.getElementById("metric-avg-words");
const metricLongCount = document.getElementById("metric-long-count");
const longSentencesWrapper = document.getElementById("long-sentences-wrapper");
const longSentencesSummaryCount = document.getElementById("long-sentences-summary-count");
const longSentencesList = document.getElementById("long-sentences-list");

const issuesContainer = document.getElementById("issues-container");
const issuesCounterBadge = document.getElementById("issues-counter-badge");

const easyReadContent = document.getElementById("easy-read-content");
const btnCopyEasy = document.getElementById("btn-copy-easy");
const btnDownloadEasy = document.getElementById("btn-download-easy");
const btnReadAloud = document.getElementById("btn-read-aloud");

const adjustmentsList = document.getElementById("adjustments-list");

let currentEasyReadText = "";
let isReadingAloud = false;
let currentUtterance = null;

/**
 * Announces text to screen readers via aria-live polite container.
 */
function announce(message) {
  if (!statusLive) return;
  statusLive.textContent = "";
  setTimeout(() => {
    statusLive.textContent = message;
  }, 50);
}

/**
 * Displays visible notification banner.
 */
function showBanner(message, type = "info") {
  if (!statusBanner) return;
  statusBanner.className = `status-message status-${type}`;
  statusBanner.textContent = message;
  statusBanner.style.display = "block";
}

function hideBanner() {
  if (!statusBanner) return;
  statusBanner.style.display = "none";
  statusBanner.textContent = "";
}

/**
 * Updates live character counter.
 */
function updateCharCounter() {
  const count = docTextArea.value.length;
  charCounter.textContent = `${count.toLocaleString("ro-RO")} / ${MAX_CHARS.toLocaleString("ro-RO")} caractere`;
  if (count > MAX_CHARS) {
    charCounter.style.color = "var(--error-text)";
    charCounter.style.fontWeight = "700";
  } else {
    charCounter.style.color = "inherit";
    charCounter.style.fontWeight = "normal";
  }
}

/**
 * Evaluates score tier metadata.
 */
function getScoreTier(score) {
  if (score >= 80) {
    return {
      label: "Accesibilitate excelentă",
      desc: "Documentul este clar, concis și ușor de parcurs pentru orice nou angajat.",
      badgeClass: "status-success",
      color: "var(--success-border)"
    };
  }
  if (score >= 50) {
    return {
      label: "Accesibilitate moderată — recomandăm simplificări",
      desc: "Documentul conține pasaje sau fraze care pot îngreuna parcurgerea rapidă a sarcinilor.",
      badgeClass: "status-warning",
      color: "var(--warning-border)"
    };
  }
  return {
    label: "Accesibilitate dificilă — necesită restructurare",
    desc: "Documentul este dens, conține fraze excesiv de lungi sau formulări neclare.",
    badgeClass: "status-error",
    color: "var(--error-border)"
  };
}

/**
 * Renders analysis results to the DOM.
 */
function renderResults(payload) {
  const { data, meta } = payload;
  const { readability, issues, easy_read_ro, adjustment_checklist } = data;

  // 1. Transparency & Warnings
  if (meta?.ai_notice_ro) {
    aiNoticeText.textContent = meta.ai_notice_ro;
  }
  if (meta?.warnings && meta.warnings.length > 0) {
    warningsContainer.innerHTML = "";
    meta.warnings.forEach(w => {
      const p = document.createElement("div");
      p.className = "status-message status-warning";
      p.style.marginBottom = "0.5rem";
      p.textContent = `Atenționare: ${w}`;
      warningsContainer.appendChild(p);
    });
    warningsContainer.style.display = "block";
  } else {
    warningsContainer.style.display = "none";
    warningsContainer.innerHTML = "";
  }

  // 2. Readability Dashboard
  const score = readability.score_0_100;
  scoreValue.textContent = score;
  const tier = getScoreTier(score);
  scoreBadge.textContent = tier.label;
  scoreBadge.className = `badge ${tier.badgeClass}`;
  scoreCircle.style.color = tier.color;
  scoreDescription.textContent = tier.desc;

  metricSentenceCount.textContent = readability.sentence_count;
  metricAvgWords.textContent = Number(readability.avg_sentence_words).toLocaleString("ro-RO", { minimumFractionDigits: 1 });
  metricLongCount.textContent = readability.long_sentences.length;

  if (readability.long_sentences.length > 0) {
    longSentencesList.innerHTML = "";
    readability.long_sentences.forEach(item => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${item.words} cuvinte:</strong> <span class="source-quote" style="display: inline-block; margin: 0.25rem 0;">„${escapeHtml(item.text)}”</span>`;
      longSentencesList.appendChild(li);
    });
    longSentencesSummaryCount.textContent = readability.long_sentences.length;
    longSentencesWrapper.style.display = "block";
  } else {
    longSentencesWrapper.style.display = "none";
  }

  // 3. Issues
  issuesContainer.innerHTML = "";
  const issueCount = issues ? issues.length : 0;
  issuesCounterBadge.textContent = `${issueCount} ${issueCount === 1 ? "problemă identificată" : "probleme identificate"}`;

  if (issueCount === 0) {
    const emptyNotice = document.createElement("p");
    emptyNotice.style.fontStyle = "italic";
    emptyNotice.style.color = "var(--text-muted)";
    emptyNotice.textContent = "Nu au fost identificate probleme majore de jargon sau ambiguitate. Textul respectă principiile comunicării clare.";
    issuesContainer.appendChild(emptyNotice);
  } else {
    issues.forEach(issue => {
      const card = document.createElement("div");
      card.className = `issue-card issue-${issue.kind}`;

      const header = document.createElement("div");
      header.style.display = "flex";
      header.style.justifyContent = "space-between";
      header.style.alignItems = "center";
      header.style.marginBottom = "0.5rem";

      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = ISSUE_KIND_LABELS[issue.kind] || issue.kind;
      header.appendChild(badge);
      card.appendChild(header);

      const quoteEl = document.createElement("blockquote");
      quoteEl.className = "source-quote";
      quoteEl.textContent = `„${issue.quote}”`;
      card.appendChild(quoteEl);

      const fixEl = document.createElement("p");
      fixEl.style.margin = "0.5rem 0 0";
      fixEl.innerHTML = `<strong>Sugestie de simplificare:</strong> ${escapeHtml(issue.fix)}`;
      card.appendChild(fixEl);

      issuesContainer.appendChild(card);
    });
  }

  // 4. Easy-Read Plain Romanian Rewrite
  currentEasyReadText = easy_read_ro || "";
  easyReadContent.textContent = currentEasyReadText;

  // 5. Recommended Adjustments
  adjustmentsList.innerHTML = "";
  if (adjustment_checklist && adjustment_checklist.length > 0) {
    adjustment_checklist.forEach(adj => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${escapeHtml(adj.title)}</strong> <span class="badge" style="margin-left: 0.5rem; font-size: 0.8rem;">Catalog: ${escapeHtml(adj.id)}</span>`;
      adjustmentsList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "Toate adaptările standard din ghid sunt suficiente.";
    adjustmentsList.appendChild(li);
  }

  // Show results and shift focus smoothly
  resultsSection.style.display = "block";
  resultsHeading.focus();
  announce("Analiza a fost finalizată cu succes. Rezultatele sunt afișate mai jos.");
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Loads sample text into textarea.
 */
function loadSampleText() {
  hideBanner();
  docTextArea.value = FALLBACK_SAMPLE;
  docTypeSelect.value = "onboarding";
  updateCharCounter();
  docTextArea.focus();
  announce("Exemplul de ghid de onboarding a fost încărcat în formular.");
}

/**
 * Handles .txt file upload.
 */
function handleFileUpload(e) {
  hideBanner();
  const file = e.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (event) => {
    docTextArea.value = event.target.result;
    updateCharCounter();
    announce(`Fișierul ${file.name} a fost încărcat cu succes.`);
  };
  reader.onerror = () => {
    showBanner("Eroare la citirea fișierului. Vă rugăm încercați din nou.", "error");
    announce("Eroare la citirea fișierului.");
  };
  reader.readAsText(file, "UTF-8");
}

/**
 * Submits document to /api/employer/analyze or mock fixture.
 */
async function handleAnalyze(e) {
  e.preventDefault();
  hideBanner();

  const text = docTextArea.value.trim();
  const docType = docTypeSelect.value;

  if (!text) {
    showBanner("Te rugăm să introduci sau să încarci un text pentru analiză.", "error");
    docTextArea.focus();
    announce("Te rugăm să introduci sau să încarci un text pentru analiză.");
    return;
  }

  if (text.length > MAX_CHARS) {
    showBanner(`Textul are ${text.length} caractere și depășește limita de ${MAX_CHARS}. Te rugăm scurtează documentul.`, "error");
    docTextArea.focus();
    announce("Textul depășește limita maximă de caractere.");
    return;
  }

  // Set loading state
  btnAnalyze.disabled = true;
  btnAnalyze.setAttribute("aria-busy", "true");
  btnAnalyze.textContent = "Se analizează...";
  announce("Se analizează documentul pentru accesibilitate cognitivă...");

  const isMockMode = new URLSearchParams(window.location.search).get("mock") === "1";

  try {
    let payload = null;

    if (isMockMode) {
      const fixtureRes = await fetch("/employer/fixture.json");
      if (!fixtureRes.ok) throw new Error("Fixture unavailable");
      payload = await fixtureRes.json();
    } else {
      try {
        const apiRes = await fetch("/api/employer/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, doc_type: docType })
        });
        payload = await apiRes.json();
      } catch {
        // Fallback gracefully to fixture if API server is offline
        const fallbackRes = await fetch("/employer/fixture.json");
        payload = await fallbackRes.json();
        showBanner("Notă: Serverul a fost indisponibil, s-a utilizat fișa demonstrativă offline.", "warning");
      }
    }

    if (payload && payload.ok) {
      renderResults(payload);
    } else {
      const errMsg = payload?.error?.message_ro || "A apărut o problemă la analiza documentului.";
      showBanner(errMsg, "error");
      announce(errMsg);
    }
  } catch {
    showBanner("A apărut o eroare neașteptată. Te rugăm să încerci din nou.", "error");
    announce("A apărut o eroare neașteptată.");
  } finally {
    btnAnalyze.disabled = false;
    btnAnalyze.removeAttribute("aria-busy");
    btnAnalyze.textContent = "Analizează documentul";
  }
}

/**
 * Copies plain text rewrite to clipboard.
 */
async function copyEasyReadText() {
  if (!currentEasyReadText) return;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(currentEasyReadText);
    } else {
      const ta = document.createElement("textarea");
      ta.value = currentEasyReadText;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    const originalText = btnCopyEasy.textContent;
    btnCopyEasy.textContent = "Copiat!";
    announce("Textul rescris a fost copiat în clipboard.");
    setTimeout(() => {
      btnCopyEasy.textContent = originalText;
    }, 2000);
  } catch {
    announce("Nu s-a putut copia textul în clipboard.");
  }
}

/**
 * Downloads plain text rewrite as a .txt file.
 */
function downloadEasyReadText() {
  if (!currentEasyReadText) return;
  const blob = new Blob([currentEasyReadText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "document_simplificat_primazi.txt";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  announce("Descărcarea documentului a început.");
}

/**
 * Reads easy-read text aloud using Web Speech API in Romanian (ro-RO).
 */
function toggleReadAloud() {
  if (!("speechSynthesis" in window)) {
    announce("Sinteza vocală nu este suportată de browserul dumneavoastră.");
    showBanner("Sinteza vocală nu este suportată în acest browser.", "warning");
    return;
  }

  if (isReadingAloud) {
    window.speechSynthesis.cancel();
    isReadingAloud = false;
    btnReadAloud.textContent = "Citește cu voce tare";
    announce("Lectura vocală a fost oprită.");
    return;
  }

  if (!currentEasyReadText) return;

  window.speechSynthesis.cancel();
  currentUtterance = new SpeechSynthesisUtterance(currentEasyReadText);
  currentUtterance.lang = "ro-RO";

  const voices = window.speechSynthesis.getVoices();
  const roVoice = voices.find(v => v.lang === "ro-RO" || v.lang.startsWith("ro"));
  if (roVoice) {
    currentUtterance.voice = roVoice;
  }

  currentUtterance.onstart = () => {
    isReadingAloud = true;
    btnReadAloud.textContent = "Oprește lectura";
    announce("Se citește textul simplificat cu voce tare.");
  };

  currentUtterance.onend = () => {
    isReadingAloud = false;
    btnReadAloud.textContent = "Citește cu voce tare";
  };

  currentUtterance.onerror = () => {
    isReadingAloud = false;
    btnReadAloud.textContent = "Citește cu voce tare";
  };

  window.speechSynthesis.speak(currentUtterance);
}

/**
 * Resets form and hides results.
 */
function handleClear() {
  docTextArea.value = "";
  fileInput.value = "";
  updateCharCounter();
  hideBanner();
  resultsSection.style.display = "none";
  if (isReadingAloud && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    isReadingAloud = false;
    btnReadAloud.textContent = "Citește cu voce tare";
  }
  docTextArea.focus();
  announce("Formularul a fost golit.");
}

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  applyA11yPrefs();
  updateCharCounter();

  // Event Listeners
  docTextArea.addEventListener("input", updateCharCounter);
  btnLoadSample.addEventListener("click", loadSampleText);
  fileInput.addEventListener("change", handleFileUpload);
  btnClear.addEventListener("click", handleClear);
  form.addEventListener("submit", handleAnalyze);

  btnCopyEasy.addEventListener("click", copyEasyReadText);
  btnDownloadEasy.addEventListener("click", downloadEasyReadText);
  btnReadAloud.addEventListener("click", toggleReadAloud);
});

