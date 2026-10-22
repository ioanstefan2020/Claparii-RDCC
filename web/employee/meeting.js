/**
 * meeting.js - Meeting Helper Screen Module (F4)
 * Owner: p2
 * Conforms to docs/CONTRACTS.md §3.3 and WCAG 2.2 AA
 *
 * Rules:
 * - Text-only; strictly NO emotion inference from voice or text (EU AI Act)
 * - Grounding: decisions & action items anchored with verbatim source_quote
 * - Web Speech API (ro-RO) dictation with graceful fallback when unsupported
 * - Text-to-speech (TTS) read-aloud for meeting summary
 * - One-click export of action items into localStorage ("primazi_planner_tasks")
 * - Zero window.alert() calls; uses status-live aria-live regions & error banners
 */

import { summarizeMeeting } from "../shared/api.js";
import { getApiProfile, getA11yPrefs, applyA11yPrefs } from "../shared/profile.js";
import {
  isRecognitionSupported,
  createSpeechRecognizer,
  speakText,
  stopSpeaking,
  isSynthesisSupported
} from "../shared/speech.js";

/**
 * Embedded realistic Romanian meeting transcript for one-click demo.
 * Sourced directly from data/samples/meeting_transcript_ro.txt.
 */
export const SAMPLE_TRANSCRIPT = `Andrei: Bun, să începem. Subiectul de azi este lansarea noii pagini de produs.
Ioana: Eu am terminat designul, dar mai am nevoie de textele finale de la marketing.
Radu: Textele vor fi gata până marți, le trimit eu pe e-mail.
Andrei: Perfect. Atunci, Ioana, tu integrezi textele miercuri și îmi dai un semn când e gata de verificare.
Mihai: Eu verific partea de testare joi dimineață. Ar trebui să vedem și cum arată pe telefon.
Andrei: Da, și să nu uităm de decizia de ieri: lansăm vineri, 6 noiembrie, nu mai amânăm.
Ioana: Am o întrebare: cine vorbește cu clientul despre noul termen?
Andrei: Rămâne la mine, îi scriu azi.
Andrei: Altceva? Nu. Mulțumesc, la revedere.`;

/**
 * Safely escapes HTML special characters to prevent XSS vulnerabilities.
 */
export function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Adds an extracted action item into the Planner storage (primazi_planner_tasks).
 * Compatible with the task schema defined in web/employee/plan.js.
 *
 * @param {object} actionItem - Action item from /api/meeting/summarize
 * @returns {Array<object>} - Updated tasks array
 */
export function addActionItemToPlanner(actionItem) {
  if (!actionItem) return [];

  let tasks = [];
  try {
    if (typeof localStorage !== "undefined") {
      const raw = localStorage.getItem("primazi_planner_tasks");
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          tasks = parsed.filter(t => t && typeof t === "object");
        }
      }
    }
  } catch (err) {
    console.warn("Eroare la citirea sarcinilor din planificator:", err);
    tasks = [];
  }

  const newTask = {
    id: `task_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    title: (actionItem.task || "Sarcină din ședință").trim(),
    due_iso: actionItem.due_iso || null,
    due_text: actionItem.due_text || null,
    needs_confirmation: Boolean(actionItem.needs_confirmation),
    priority: "normal",
    steps: actionItem.who ? [`Asignat către: ${actionItem.who}`] : [],
    source_quote: actionItem.source_quote || null,
    completed: false
  };

  tasks.push(newTask);

  try {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("primazi_planner_tasks", JSON.stringify(tasks));
    }
  } catch (err) {
    console.error("Eroare la salvarea sarcinii în planificator:", err);
  }

  return tasks;
}

/**
 * Renders the structured meeting results into the UI containers.
 * Supports both full DOM trees and lightweight test containers.
 *
 * @param {object} data - Meeting data ({ summary, decisions, action_items, unclear_points })
 * @param {HTMLElement|object} container - Root results container or mock element
 * @param {object} callbacks - Optional event callbacks (e.g. onAddToPlan)
 */
export function renderMeetingResults(data, container, callbacks = {}) {
  if (!container || !data) return;

  const summary = data.summary || "";
  const decisions = Array.isArray(data.decisions) ? data.decisions : [];
  const actionItems = Array.isArray(data.action_items) ? data.action_items : [];
  const unclearPoints = Array.isArray(data.unclear_points) ? data.unclear_points : [];

  // 1. Render Summary
  const summaryCont = container.querySelector ? container.querySelector("#summary-content") : null;
  const summaryHtml = `<p style="margin: 0; line-height: 1.6;">${escapeHtml(summary || "Fără rezumat.")}</p>`;
  if (summaryCont) {
    summaryCont.innerHTML = summaryHtml;
  }

  // 2. Render Decisions
  const decisionsCont = container.querySelector ? container.querySelector("#decisions-list") : null;
  let decisionsHtml = "";
  if (decisions.length === 0) {
    decisionsHtml = `<p class="meta-secondary" style="color: var(--text-muted); font-size: 0.95rem;">Nu au fost identificate decizii explicite în această ședință.</p>`;
  } else {
    decisionsHtml = decisions
      .map(
        d => `
        <div class="decision-item">
          <div style="font-weight: 600; color: var(--text-main); font-size: 1rem;">${escapeHtml(d.text)}</div>
          ${
            d.source_quote
              ? `<div class="meta-secondary" style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.35rem;">
                   Citat verbatim: <em>„${escapeHtml(d.source_quote)}”</em>
                 </div>`
              : ""
          }
        </div>`
      )
      .join("");
  }
  if (decisionsCont) {
    decisionsCont.innerHTML = decisionsHtml;
  }

  // 3. Render Action Items
  const actionsCont = container.querySelector ? container.querySelector("#actions-list") : null;
  let actionsHtml = "";
  if (actionItems.length === 0) {
    actionsHtml = `<p class="meta-secondary" style="color: var(--text-muted); font-size: 0.95rem;">Nu au fost identificate sarcini de acțiune în această ședință.</p>`;
  } else {
    actionsHtml = actionItems
      .map((item, idx) => {
        const whoBadge = item.who
          ? `<span class="action-who-badge">Responsabil: ${escapeHtml(item.who)}</span>`
          : `<span class="action-who-badge" style="background-color: var(--bg-surface); color: var(--text-muted);">Responsabil nespecificat</span>`;

        const dueNote = item.due_text
          ? `<span class="meta-secondary" style="font-size: 0.9rem; color: var(--text-muted);">
               Termen: <strong>${escapeHtml(item.due_text)}</strong>
               ${item.needs_confirmation ? '<span style="color: var(--error-text); margin-left: 0.25rem;">(de confirmat)</span>' : ""}
             </span>`
          : "";

        return `
          <div class="action-item-card" data-action-idx="${idx}">
            <div class="action-item-header">
              ${whoBadge}
              ${dueNote}
            </div>
            <div style="font-size: 1.05rem; font-weight: 600; color: var(--text-main); margin-top: 0.25rem;">
              ${escapeHtml(item.task)}
            </div>
            ${
              item.source_quote
                ? `<div class="meta-secondary" style="font-size: 0.85rem; color: var(--text-muted);">
                     Citat verbatim: <em>„${escapeHtml(item.source_quote)}”</em>
                   </div>`
                : ""
            }
            <div style="margin-top: 0.5rem; display: flex; justify-content: flex-end;">
              <button type="button" class="btn btn-secondary btn-add-to-plan" data-action-idx="${idx}" aria-label="Adaugă sarcina „${escapeHtml(item.task)}” în planificator">
                [+ Adaugă în Planificator]
              </button>
            </div>
          </div>`;
      })
      .join("");
  }
  if (actionsCont) {
    actionsCont.innerHTML = actionsHtml;
  }

  // 4. Render Unclear Points
  const unclearCont = container.querySelector ? container.querySelector("#unclear-list") : null;
  let unclearHtml = "";
  if (unclearPoints.length === 0) {
    unclearHtml = `<p class="meta-secondary" style="color: var(--text-muted); font-size: 0.95rem;">Nu există aspecte neclare semnalate.</p>`;
  } else {
    unclearHtml = unclearPoints
      .map(
        pt => `
        <div class="unclear-item">
          <div style="color: var(--text-main); font-size: 0.98rem;">${escapeHtml(pt)}</div>
        </div>`
      )
      .join("");
  }
  if (unclearCont) {
    unclearCont.innerHTML = unclearHtml;
  }

  // Fallback for simple container without querySelector sub-targets (e.g. Node tests)
  if (!container.querySelector) {
    container.innerHTML = `
      <div class="summary-rendered">${summaryHtml}</div>
      <div class="decisions-rendered">${decisionsHtml}</div>
      <div class="actions-rendered">${actionsHtml}</div>
      <div class="unclear-rendered">${unclearHtml}</div>
    `;
  }
}

/**
 * Initializes the Meeting Helper page interactive logic.
 */
export function initMeetingPage() {
  if (typeof document === "undefined") return;

  // Apply user visual accessibility preferences
  applyA11yPrefs(getA11yPrefs());

  // DOM Elements
  const form = document.getElementById("meeting-form");
  const transcriptInput = document.getElementById("transcript-text");
  const charCounter = document.getElementById("char-counter");
  const btnSubmit = document.getElementById("btn-submit");
  const btnSpeech = document.getElementById("btn-toggle-speech");
  const btnLoadSample = document.getElementById("btn-load-sample");
  const btnClear = document.getElementById("btn-clear-transcript");
  const speechNote = document.getElementById("speech-support-note");
  const liveRegion = document.getElementById("status-live");
  const errorBanner = document.getElementById("error-banner");
  const resultsSection = document.getElementById("results-section");
  const warningsContainer = document.getElementById("warnings-container");
  const aiNotice = document.getElementById("ai-notice");
  const btnSpeakSummary = document.getElementById("btn-speak-summary");

  let currentSummaryText = "";
  let isSpeaking = false;
  let isListening = false;
  let speechRecognizer = null;
  let lastSummarizeData = null;

  function announce(message) {
    if (liveRegion) {
      liveRegion.textContent = "";
      setTimeout(() => {
        liveRegion.textContent = message;
      }, 50);
    }
  }

  function showError(message) {
    if (errorBanner) {
      errorBanner.textContent = message;
      errorBanner.style.display = "block";
      errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    announce(`Eroare: ${message}`);
  }

  function clearError() {
    if (errorBanner) {
      errorBanner.textContent = "";
      errorBanner.style.display = "none";
    }
  }

  function updateCharCount() {
    if (!transcriptInput || !charCounter) return;
    const len = transcriptInput.value.length;
    charCounter.textContent = `${len.toLocaleString("ro-RO")} / 12.000 caractere`;
    if (len > 12000) {
      charCounter.style.color = "var(--error-text)";
      charCounter.style.fontWeight = "bold";
    } else {
      charCounter.style.color = "var(--text-muted)";
      charCounter.style.fontWeight = "normal";
    }
  }

  if (transcriptInput) {
    transcriptInput.addEventListener("input", updateCharCount);
  }

  // Load sample transcript
  if (btnLoadSample && transcriptInput) {
    btnLoadSample.addEventListener("click", () => {
      transcriptInput.value = SAMPLE_TRANSCRIPT;
      updateCharCount();
      clearError();
      transcriptInput.focus();
      announce("Exemplul de transcriere a ședinței a fost încărcat în formular.");
    });
  }

  // Clear transcript
  if (btnClear && transcriptInput) {
    btnClear.addEventListener("click", () => {
      transcriptInput.value = "";
      updateCharCount();
      clearError();
      if (resultsSection) resultsSection.style.display = "none";
      transcriptInput.focus();
      announce("Textul transcrierii a fost șters.");
    });
  }

  // Speech Recognition (Dictation) Setup
  const hasRecognition = isRecognitionSupported();
  if (speechNote) {
    if (hasRecognition) {
      speechNote.textContent = "Dictarea vocală este disponibilă în acest browser (ro-RO). Apasă pe microfon pentru a începe.";
    } else {
      speechNote.textContent = "Recunoașterea vocală automată nu este suportată în acest browser. Puteți introduce textul manual sau lipi transcrierea.";
    }
  }

  if (hasRecognition && btnSpeech && transcriptInput) {
    speechRecognizer = createSpeechRecognizer({
      onStart: () => {
        isListening = true;
        btnSpeech.setAttribute("aria-pressed", "true");
        btnSpeech.classList.add("btn-primary");
        btnSpeech.textContent = "Oprește dictarea";
        announce("Dictare vocală activată. Vorbiți la microfon...");
      },
      onEnd: () => {
        isListening = false;
        btnSpeech.setAttribute("aria-pressed", "false");
        btnSpeech.classList.remove("btn-primary");
        btnSpeech.textContent = "Dictare vocală (Microfon)";
        announce("Dictare vocală oprită.");
      },
      onError: (err) => {
        isListening = false;
        btnSpeech.setAttribute("aria-pressed", "false");
        btnSpeech.classList.remove("btn-primary");
        btnSpeech.textContent = "Dictare vocală (Microfon)";
        showError(`Microfon indisponibil: ${err}`);
      },
      onResult: (transcript, isFinal) => {
        if (!transcript) return;
        const current = transcriptInput.value;
        const separator = current && !current.endsWith("\n") && !current.endsWith(" ") ? " " : "";
        transcriptInput.value = current + separator + transcript;
        updateCharCount();
      }
    });

    btnSpeech.addEventListener("click", () => {
      if (isListening) {
        speechRecognizer.stop();
      } else {
        clearError();
        speechRecognizer.start();
      }
    });
  } else if (btnSpeech) {
    btnSpeech.addEventListener("click", () => {
      showError("Recunoașterea vocală automată nu este disponibilă pe acest dispozitiv/browser.");
    });
  }

  // Speech Synthesis (TTS Read-Aloud for Summary)
  if (btnSpeakSummary) {
    btnSpeakSummary.addEventListener("click", () => {
      if (!isSynthesisSupported()) {
        showError("Sinteza vocală nu este suportată de browserul tău.");
        return;
      }

      if (isSpeaking) {
        stopSpeaking();
        isSpeaking = false;
        btnSpeakSummary.textContent = "Ascultă rezumatul";
        btnSpeakSummary.setAttribute("aria-pressed", "false");
        announce("Redarea audio a fost oprită.");
        return;
      }

      if (!currentSummaryText) return;

      speakText(currentSummaryText, {
        onStart: () => {
          isSpeaking = true;
          btnSpeakSummary.textContent = "Oprește lectura";
          btnSpeakSummary.setAttribute("aria-pressed", "true");
          announce("Se citește rezumatul ședinței...");
        },
        onEnd: () => {
          isSpeaking = false;
          btnSpeakSummary.textContent = "Ascultă rezumatul";
          btnSpeakSummary.setAttribute("aria-pressed", "false");
        },
        onError: () => {
          isSpeaking = false;
          btnSpeakSummary.textContent = "Ascultă rezumatul";
          btnSpeakSummary.setAttribute("aria-pressed", "false");
          showError("A apărut o problemă la redarea audio.");
        }
      });
    });
  }

  // Form Submission
  if (form && transcriptInput) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearError();

      const text = transcriptInput.value.trim();
      if (!text) {
        showError("Transcrierii îi lipsește conținutul. Scrie sau lipește discuția din ședință.");
        transcriptInput.focus();
        return;
      }

      if (text.length > 12000) {
        showError("Textul depășește limita permisă de 12.000 de caractere.");
        transcriptInput.focus();
        return;
      }

      // Set Loading State
      if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.textContent = "Se sintetizează...";
      }
      announce("Se sintetizează ședința, vă rugăm așteptați...");

      try {
        const todayIso = new Date().toISOString().slice(0, 10);
        const profile = getApiProfile();
        const res = await summarizeMeeting(text, todayIso, profile);

        if (!res.ok) {
          const msg = (res.error && res.error.message_ro) || "Nu s-a putut sintetiza ședința. Vă rugăm încercați din nou.";
          showError(msg);
          return;
        }

        const data = res.data;
        const meta = res.meta || {};
        lastSummarizeData = data;
        currentSummaryText = data.summary || "";

        // Show AI notice
        if (aiNotice) {
          aiNotice.textContent = meta.ai_notice_ro || "Generat de AI — verifică datele importante.";
          aiNotice.style.display = "block";
        }

        // Show Guardrail Warnings (if any)
        if (warningsContainer) {
          if (meta.warnings && meta.warnings.length > 0) {
            warningsContainer.innerHTML = meta.warnings
              .map(
                w => `
                <div class="status-message status-warning" role="alert" style="margin-bottom: 0.5rem;">
                  <strong>Atenționare integritate:</strong> ${escapeHtml(w)}
                </div>`
              )
              .join("");
            warningsContainer.style.display = "block";
          } else {
            warningsContainer.innerHTML = "";
            warningsContainer.style.display = "none";
          }
        }

        // Render Cards
        if (resultsSection) {
          renderMeetingResults(data, resultsSection);
          resultsSection.style.display = "block";

          // Wire Add-to-Plan buttons
          const addButtons = resultsSection.querySelectorAll(".btn-add-to-plan");
          addButtons.forEach(btn => {
            btn.addEventListener("click", () => {
              const idx = parseInt(btn.getAttribute("data-action-idx"), 10);
              const actionItem = data.action_items && data.action_items[idx];
              if (actionItem) {
                addActionItemToPlanner(actionItem);
                btn.disabled = true;
                btn.textContent = "✓ Adăugată în Planificator";
                btn.classList.remove("btn-secondary");
                announce(`Sarcina „${actionItem.task}” a fost adăugată în Planificator.`);
              }
            });
          });

          resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }

        announce("Sinteza ședinței a fost generată cu succes.");
      } catch (err) {
        showError("A apărut o eroare neașteptată la comunicarea cu serverul.");
      } finally {
        if (btnSubmit) {
          btnSubmit.disabled = false;
          btnSubmit.textContent = "Sintetizează ședința";
        }
      }
    });
  }
}

