/**
 * clarify.js - Clarify Screen Logic (T2.3 - F2)
 * Owner: p2
 * Conforms to docs/CONTRACTS.md §1 & §3.1 and WCAG 2.2 AA
 *
 * Capabilities:
 * - Load realistic Romanian onboarding sample text (SAMPLE_ONBOARDING_TEXT)
 * - Load text from .txt file uploads via FileReader
 * - Character count validation (<= 12000 chars)
 * - Call POST /api/simplify via simplifyDocument(text, getApiProfile())
 * - Render AI summary, steps with quote buttons, key terms, questions, and warnings
 * - Interactive whitespace-normalized quote highlighting in the original text viewer
 * - Toggle quote highlighting on/off per step
 * - Speech synthesis (TTS) toggle via speakText/stopSpeaking
 * - Responsive error handling with retry capability
 */

import { simplifyDocument } from "../shared/api.js";
import { getProfile, getApiProfile, getA11yPrefs, applyA11yPrefs } from "../shared/profile.js";
import { speakText, stopSpeaking, isSynthesisSupported } from "../shared/speech.js";

/**
 * Embedded realistic Romanian onboarding document for instant demo.
 * Sourced directly from data/samples/onboarding_ro.txt.
 */
export const SAMPLE_ONBOARDING_TEXT = `Bine ai venit în echipa Companie Exemplu SRL!

Prima ta săptămână

Luni, ora 09:00 – Te prezinți la recepția clădirii B și ceri cardul de acces. Persoana de contact este Mihaela Popescu din departamentul de Resurse Umane (HR).

Luni, ora 10:00 – Ședința de onboarding cu managerul tău direct, Andrei Ionescu. Vei primi laptopul și conturile de acces.

Până miercuri, 28 octombrie, trebuie să completezi în portalul intern formularul F-12 (date personale și bancare) și să semnezi digital politica de securitate a informației (SecInfo v3).

Joi, ora 14:00 – Training obligatoriu de securitate cibernetică, online. Link-ul de participare îți va fi trimis pe e-mail de către echipa IT.

Până vineri, 30 octombrie, trebuie să parcurgi cursul „Introducere în procesele interne" din platforma de e-learning și să trimiți managerului un rezumat de maximum o pagină.

În prima lună se așteaptă să atingi nivelul de autonomie operațională prevăzut în planul 30-60-90, în conformitate cu KPI-urile agreate cu managerul, având în vedere alinierea la cultura organizațională și la valorile companiei.

Dacă ai nevoie de adaptări ale mediului de lucru, te rugăm să le comunici către HR în termen de 14 zile de la data angajării, la adresa hr@exemplu.example.`;

/**
 * Safely escape HTML characters to prevent XSS vulnerabilities.
 */
function escapeHtml(str) {
  if (typeof str !== "string") return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Normalizes runs of whitespace (spaces, tabs, newlines) into single spaces.
 */
export function normalizeWhitespace(str) {
  if (typeof str !== "string") return "";
  return str.replace(/\s+/g, " ").trim();
}

/**
 * Highlights a verbatim quote inside the container displaying fullText.
 * Handles whitespace discrepancies between quote and source document text.
 * Wraps match in `<mark class="quote-highlight" id="active-quote">` and scrolls it into view.
 *
 * @param {HTMLElement|object} container - The element holding the original text
 * @param {string} fullText - The full original document string
 * @param {string|null} quote - The quote to highlight, or null to clear highlight
 * @returns {boolean} - true if matched and highlighted, false otherwise
 */
export function highlightQuoteInContainer(container, fullText, quote) {
  if (!container) return false;
  const rawText = typeof fullText === "string" ? fullText : "";
  if (!rawText) {
    container.innerHTML = "";
    return false;
  }

  if (!quote || typeof quote !== "string" || !quote.trim()) {
    container.innerHTML = escapeHtml(rawText);
    return false;
  }

  const words = quote
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

  if (words.length === 0) {
    container.innerHTML = escapeHtml(rawText);
    return false;
  }

  const regex = new RegExp(words.join("\\s+"), "iu");
  const match = rawText.match(regex);

  if (!match || match.index === undefined) {
    container.innerHTML = escapeHtml(rawText);
    return false;
  }

  const start = match.index;
  const matchedText = match[0];
  const end = start + matchedText.length;

  const before = rawText.slice(0, start);
  const after = rawText.slice(end);

  container.innerHTML = `${escapeHtml(before)}<mark class="quote-highlight" id="active-quote">${escapeHtml(matchedText)}</mark>${escapeHtml(after)}`;

  if (typeof container.querySelector === "function") {
    const mark = container.querySelector("#active-quote");
    if (mark && typeof mark.scrollIntoView === "function") {
      const prefersReduced = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
      mark.scrollIntoView({ behavior: prefersReduced ? "auto" : "smooth", block: "center" });
    }
  }

  return true;
}

/**
 * Renders warning banners if server guardrails detected issues.
 */
export function renderWarnings(container, warnings) {
  if (!container) return;
  if (!Array.isArray(warnings) || warnings.length === 0) {
    container.innerHTML = "";
    container.style.display = "none";
    return;
  }

  let html = '<strong>Atenționări privind verificarea conținutului:</strong><ul style="margin: 0.5rem 0 0 1.25rem; padding: 0;">';
  for (const w of warnings) {
    html += `<li>${escapeHtml(String(w))}</li>`;
  }
  html += '</ul>';

  container.innerHTML = html;
  container.className = "status-message status-warning";
  container.setAttribute("role", "alert");
  container.style.display = "block";
}

/**
 * Renders the high-level summary paragraph.
 */
export function renderSummary(container, summary) {
  if (!container) return;
  if (!summary || typeof summary !== "string") {
    container.innerHTML = "";
    return;
  }
  container.innerHTML = `<p class="summary-text" style="font-size: 1.15rem; line-height: 1.6; margin: 0; font-weight: 500;">${escapeHtml(summary)}</p>`;
}

/**
 * Renders sequential steps with interactive quote highlighting buttons.
 */
export function renderSteps(container, steps, onShowQuote = null) {
  if (!container) return;
  if (!Array.isArray(steps) || steps.length === 0) {
    container.innerHTML = "<p>Nu au fost identificați pași obligatorii.</p>";
    return;
  }

  let html = '<ol class="steps-list" style="margin: 0; padding-left: 1.5rem; display: flex; flex-direction: column; gap: 1.25rem;">';
  steps.forEach((step, idx) => {
    const stepNum = Number.isFinite(step.n) ? step.n : idx + 1;
    const stepText = escapeHtml(step.text || "");
    const quote = step.source_quote ? escapeHtml(step.source_quote) : "";

    html += `
      <li class="step-item" style="line-height: 1.6;">
        <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.35rem;">
          ${stepText}
        </div>`;

    if (quote) {
      html += `
        <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; margin-top: 0.5rem;">
          <button type="button" class="btn btn-secondary btn-show-quote" data-quote="${quote}" data-step="${stepNum}" aria-pressed="false" style="font-size: 0.85rem; padding: 0.35rem 0.75rem; min-height: 38px;">
            Arată în text
          </button>
          <span class="meta-secondary" style="font-size: 0.85rem; color: var(--text-muted); font-style: italic;">
            Citat: „${quote}”
          </span>
        </div>`;
    }

    html += '</li>';
  });
  html += '</ol>';

  container.innerHTML = html;

  if (typeof container.querySelectorAll === "function" && onShowQuote) {
    const buttons = container.querySelectorAll(".btn-show-quote");
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const quote = btn.getAttribute("data-quote");
        onShowQuote(quote, btn);
      });
    });
  }
}

/**
 * Renders key terms with explanations in a definition list grid.
 */
export function renderKeyTerms(container, keyTerms) {
  if (!container) return;
  if (!Array.isArray(keyTerms) || keyTerms.length === 0) {
    container.innerHTML = "<p>Nu au fost identificați termeni tehnici sau acronime complexe.</p>";
    return;
  }

  let html = '<dl class="terms-grid" style="display: grid; gap: 0.85rem; margin: 0;">';
  for (const item of keyTerms) {
    const term = escapeHtml(item.term || "");
    const explanation = escapeHtml(item.explanation || "");
    html += `
      <div class="term-card" style="padding: 0.75rem 1rem; background-color: var(--bg-surface-alt); border-radius: var(--radius-md); border-left: 4px solid var(--primary);">
        <dt style="font-weight: 700; color: var(--primary); font-size: 1.05rem;">${term}</dt>
        <dd style="margin: 0.25rem 0 0 0; color: var(--text-main); font-size: 0.95rem; line-height: 1.5;">${explanation}</dd>
      </div>`;
  }
  html += '</dl>';

  container.innerHTML = html;
}

/**
 * Renders suggested questions for the employee to ask colleagues or manager.
 */
export function renderQuestions(container, questions) {
  if (!container) return;
  if (!Array.isArray(questions) || questions.length === 0) {
    container.innerHTML = "<p>Nu au fost generate întrebări sugerate.</p>";
    return;
  }

  let html = '<ul style="margin: 0; padding-left: 1.25rem; display: flex; flex-direction: column; gap: 0.6rem;">';
  for (const q of questions) {
    html += `<li style="font-size: 1rem; color: var(--text-main); line-height: 1.5;">„${escapeHtml(String(q))}”</li>`;
  }
  html += '</ul>';

  container.innerHTML = html;
}

/**
 * Initializes the clarify page, wiring all inputs, buttons, and listeners.
 */
export function initClarifyPage() {
  // Apply accessibility settings immediately
  applyA11yPrefs(getA11yPrefs());

  const docTextInput = document.getElementById("doc-text");
  const fileUploadInput = document.getElementById("file-upload");
  const btnLoadSample = document.getElementById("btn-load-sample");
  const btnClearText = document.getElementById("btn-clear-text");
  const btnClarify = document.getElementById("btn-clarify");
  const clarifyForm = document.getElementById("clarify-form");
  const charCounter = document.getElementById("char-counter");
  const sourceViewer = document.getElementById("source-viewer");
  const statusLive = document.getElementById("status-live");
  const errorBanner = document.getElementById("error-banner");

  const resultsSection = document.getElementById("results-section");
  const warningsContainer = document.getElementById("warnings-container");
  const aiNoticeEl = document.getElementById("ai-notice");
  const summaryContainer = document.getElementById("summary-content");
  const stepsContainer = document.getElementById("steps-content");
  const termsContainer = document.getElementById("terms-content");
  const questionsContainer = document.getElementById("questions-content");
  const btnTtsToggle = document.getElementById("btn-tts-toggle");

  let currentActiveQuote = null;
  let isSpeaking = false;
  let currentSummaryText = "";

  function announce(msg) {
    if (statusLive) {
      statusLive.textContent = "";
      setTimeout(() => {
        statusLive.textContent = msg;
      }, 50);
    }
  }

  function updateCounter() {
    if (!docTextInput || !charCounter) return;
    const len = docTextInput.value.length;
    charCounter.textContent = `${len.toLocaleString("ro-RO")} / 12.000 caractere`;
    if (len > 12000) {
      charCounter.style.color = "var(--error-border)";
      charCounter.style.fontWeight = "700";
    } else {
      charCounter.style.color = "var(--text-muted)";
      charCounter.style.fontWeight = "normal";
    }
  }

  function updateSourceViewer(highlightQuote = null) {
    if (!sourceViewer) return;
    const text = docTextInput ? docTextInput.value : "";
    if (!text.trim()) {
      sourceViewer.innerHTML = "(Textul original va apărea aici după încărcare sau introducere)";
      return;
    }
    highlightQuoteInContainer(sourceViewer, text, highlightQuote);
  }

  function showError(msg, showRetry = false) {
    if (!errorBanner) return;
    errorBanner.style.display = "block";
    let content = `<span>${escapeHtml(msg)}</span>`;
    if (showRetry) {
      content += ` <button type="button" id="btn-retry-clarify" class="btn btn-secondary" style="margin-left: 0.75rem; padding: 0.25rem 0.65rem; font-size: 0.9rem;">Reîncearcă</button>`;
    }
    errorBanner.innerHTML = content;
    announce(msg);

    if (showRetry) {
      const retryBtn = document.getElementById("btn-retry-clarify");
      if (retryBtn) {
        retryBtn.addEventListener("click", () => {
          handleClarify();
        });
      }
    }
  }

  function hideError() {
    if (errorBanner) {
      errorBanner.style.display = "none";
      errorBanner.innerHTML = "";
    }
  }

  function handleShowQuote(quote, clickedBtn) {
    const allButtons = document.querySelectorAll(".btn-show-quote");

    if (currentActiveQuote === quote) {
      // Toggle off active quote
      currentActiveQuote = null;
      updateSourceViewer(null);
      allButtons.forEach((b) => {
        b.textContent = "Arată în text";
        b.setAttribute("aria-pressed", "false");
      });
      announce("Evidențierea citatului a fost eliminată.");
    } else {
      // Highlight requested quote
      currentActiveQuote = quote;
      allButtons.forEach((b) => {
        b.textContent = "Arată în text";
        b.setAttribute("aria-pressed", "false");
      });

      const success = highlightQuoteInContainer(sourceViewer, docTextInput ? docTextInput.value : "", quote);
      if (success) {
        clickedBtn.textContent = "Ascunde evidențierea";
        clickedBtn.setAttribute("aria-pressed", "true");
        announce("Citatul pasului a fost evidențiat în textul original din stânga.");
      } else {
        announce("Citatul nu a fost găsit în textul original.");
      }
    }
  }

  function stopActiveSpeech() {
    if (isSpeaking) {
      stopSpeaking();
      isSpeaking = false;
      if (btnTtsToggle) {
        btnTtsToggle.innerHTML = "<span>Ascultă rezumatul</span>";
        btnTtsToggle.setAttribute("aria-pressed", "false");
      }
    }
  }

  // Load realistic sample onboarding text
  if (btnLoadSample) {
    btnLoadSample.addEventListener("click", () => {
      stopActiveSpeech();
      if (docTextInput) {
        docTextInput.value = SAMPLE_ONBOARDING_TEXT;
        updateCounter();
        updateSourceViewer(null);
        currentActiveQuote = null;
        hideError();
        announce("Textul demonstrativ de onboarding a fost încărcat în formular.");
        docTextInput.focus();
      }
    });
  }

  // Clear text
  if (btnClearText) {
    btnClearText.addEventListener("click", () => {
      stopActiveSpeech();
      if (docTextInput) {
        docTextInput.value = "";
      }
      if (fileUploadInput) {
        fileUploadInput.value = "";
      }
      updateCounter();
      updateSourceViewer(null);
      currentActiveQuote = null;
      hideError();
      if (resultsSection) {
        resultsSection.style.display = "none";
      }
      announce("Textul documentului a fost golit.");
      if (docTextInput) docTextInput.focus();
    });
  }

  // Handle .txt file upload via FileReader
  if (fileUploadInput) {
    fileUploadInput.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      if (!file.name.toLowerCase().endsWith(".txt") && file.type && !file.type.startsWith("text/")) {
        showError("Sunt acceptate doar fișiere text simple (.txt).");
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target.result;
        if (typeof content === "string") {
          if (docTextInput) docTextInput.value = content;
          updateCounter();
          updateSourceViewer(null);
          currentActiveQuote = null;
          hideError();
          announce(`Fișierul „${file.name}” a fost încărcat cu succes.`);
        }
      };
      reader.onerror = () => {
        showError("Eroare la citirea fișierului de pe disc. Vă rugăm încercați din nou.");
      };
      reader.readAsText(file, "UTF-8");
    });
  }

  // Real-time counter and source viewer sync
  if (docTextInput) {
    docTextInput.addEventListener("input", () => {
      updateCounter();
      updateSourceViewer(null);
      currentActiveQuote = null;
    });
  }

  // TTS read aloud toggle
  if (btnTtsToggle) {
    if (!isSynthesisSupported()) {
      btnTtsToggle.style.display = "none";
    } else {
      btnTtsToggle.addEventListener("click", () => {
        if (isSpeaking) {
          stopSpeaking();
          isSpeaking = false;
          btnTtsToggle.innerHTML = "<span>Ascultă rezumatul</span>";
          btnTtsToggle.setAttribute("aria-pressed", "false");
          announce("Citirea vocală a fost oprită.");
        } else {
          if (!currentSummaryText) return;
          isSpeaking = true;
          btnTtsToggle.innerHTML = "<span>Oprește citirea</span>";
          btnTtsToggle.setAttribute("aria-pressed", "true");
          announce("A început citirea vocală a rezumatului.");

          speakText(currentSummaryText, {
            onEnd: () => {
              isSpeaking = false;
              btnTtsToggle.innerHTML = "<span>Ascultă rezumatul</span>";
              btnTtsToggle.setAttribute("aria-pressed", "false");
            },
            onError: () => {
              isSpeaking = false;
              btnTtsToggle.innerHTML = "<span>Ascultă rezumatul</span>";
              btnTtsToggle.setAttribute("aria-pressed", "false");
            }
          });
        }
      });
    }
  }

  // Form submission and simplify API processing
  async function handleClarify(e) {
    if (e) e.preventDefault();
    hideError();
    stopActiveSpeech();

    const text = (docTextInput?.value || "").trim();
    if (!text) {
      showError("Textul este gol. Lipește textul documentului sau încarcă un fișier .txt.");
      if (docTextInput) docTextInput.focus();
      return;
    }

    if (text.length > 12000) {
      showError("Documentul depășește limita maximă de 12.000 caractere. Te rugăm să trimiți o secțiune mai scurtă.");
      if (docTextInput) docTextInput.focus();
      return;
    }

    // Set loading state
    if (btnClarify) {
      btnClarify.disabled = true;
      btnClarify.setAttribute("aria-busy", "true");
      btnClarify.textContent = "Se procesează...";
    }
    if (resultsSection) {
      resultsSection.setAttribute("aria-busy", "true");
    }
    announce("Se simplifică documentul. Vă rugăm așteptați...");

    try {
      const userProfile = getProfile();
      const apiProfile = getApiProfile(userProfile);
      const result = await simplifyDocument(text, apiProfile);

      if (!result.ok) {
        const errMsg = result.error?.message_ro || "Nu s-a putut simplifica documentul. Verificați conexiunea.";
        showError(errMsg, true);
        announce(`Eroare: ${errMsg}`);
        return;
      }

      const { data, meta } = result;

      // Update and render sections
      currentSummaryText = data.summary || "";
      renderWarnings(warningsContainer, meta?.warnings);
      renderSummary(summaryContainer, data.summary);
      renderSteps(stepsContainer, data.steps, handleShowQuote);
      renderKeyTerms(termsContainer, data.key_terms);
      renderQuestions(questionsContainer, data.questions_to_ask);

      if (aiNoticeEl) {
        aiNoticeEl.textContent = meta?.ai_notice_ro || "Generat de AI — verifică datele importante.";
      }

      if (resultsSection) {
        resultsSection.style.display = "block";
        resultsSection.removeAttribute("aria-busy");
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
        const summaryHeading = document.getElementById("summary-heading");
        if (summaryHeading) {
          summaryHeading.focus();
        }
      }

      announce("Documentul a fost simplificat cu succes. Rezultatele sunt afișate pe ecran.");

      // Automatic TTS if enabled in user profile
      if (userProfile.read_aloud_default && isSynthesisSupported() && currentSummaryText) {
        setTimeout(() => {
          if (btnTtsToggle && !isSpeaking) btnTtsToggle.click();
        }, 300);
      }
    } catch (err) {
      console.error("Clarify API error:", err);
      showError("A apărut o problemă neașteptată de rețea. Vă rugăm reîncercați.", true);
    } finally {
      if (btnClarify) {
        btnClarify.disabled = false;
        btnClarify.removeAttribute("aria-busy");
        btnClarify.textContent = "Clarifică documentul";
      }
      if (resultsSection) {
        resultsSection.removeAttribute("aria-busy");
      }
    }
  }

  if (clarifyForm) {
    clarifyForm.addEventListener("submit", handleClarify);
  }
}
