/**
 * library.js - Library Screen Interactive Controller
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 * Owner: p3
 * Spec: docs/plan/p3.md (Task N3.5)
 *
 * Rules:
 * - Dynamic list rendering, searching and filtering
 * - Quote grounding in original source text viewer
 * - TTS read-aloud and RFC 5545 calendar .ics export for plan items
 * - 7-second accessible undo toast on delete
 * - Full WCAG 2.2 AA compliance and focus management
 */

import {
  getLibraryItems,
  deleteLibraryItem,
  restoreLibraryItem,
  clearLibrary,
  isLibraryMemoryFallback
} from "/js/library-storage.js";
import { speakText, stopSpeaking, isSynthesisSupported } from "/shared/speech.js";
import { generateIcs, downloadIcsFile } from "/shared/ics.js";

// State
let allLibraryItems = [];
let currentSearchQuery = "";
let currentFilterMode = "all";
let activeModalItem = null;
let lastDeletedItem = null;
let undoTimerId = null;
let isSpeaking = false;
let currentSummaryForTTS = "";
let lastFocusedElement = null;

/**
 * Escapes HTML characters for safe template rendering.
 */
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Announces a message to the accessible live region.
 */
function announceToLiveRegion(message) {
  const live = document.getElementById("status-live");
  if (live) {
    live.textContent = "";
    setTimeout(() => {
      live.textContent = message;
    }, 40);
  }
}

/**
 * Formats an ISO 8601 string to a friendly Romanian date.
 */
function formatLocalizedDate(isoString) {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleDateString("ro-RO", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch {
    return isoString;
  }
}

/**
 * Maps mode to human-readable Romanian label.
 */
function getModeLabel(mode) {
  if (mode === "simplify") return "Clarificare";
  if (mode === "plan") return "Plan de sarcini";
  if (mode === "meeting") return "Sinteză ședință";
  return "Document";
}

/**
 * Extracts a concise preview string from item's structured data.
 */
function extractItemPreview(item) {
  if (!item || !item.resultData) {
    return item.sourceText ? item.sourceText.slice(0, 140) + "..." : "";
  }
  const data = item.resultData;
  if (data.summary) {
    return data.summary.slice(0, 160) + (data.summary.length > 160 ? "..." : "");
  }
  if (Array.isArray(data.tasks) && data.tasks.length > 0) {
    const taskCount = data.tasks.length;
    const ambiguousCount = data.tasks.filter(t => t.needs_confirmation).length;
    return `${taskCount} sarcini extrase${ambiguousCount > 0 ? ` (${ambiguousCount} cu termen ambiguu)` : ""}.`;
  }
  if (Array.isArray(data.decisions) && data.decisions.length > 0) {
    return `${data.decisions.length} decizii cheie și ${Array.isArray(data.action_items) ? data.action_items.length : 0} acțiuni extrase.`;
  }
  return item.sourceText ? item.sourceText.slice(0, 140) + "..." : "";
}

/**
 * Renders the list of cards matching search query and filter mode.
 */
export function renderCardList() {
  const container = document.getElementById("library-items-list");
  const emptyState = document.getElementById("library-empty-state");
  const countBadge = document.getElementById("library-count-badge");
  if (!container) return;

  const query = currentSearchQuery.trim().toLowerCase();
  const filtered = allLibraryItems.filter(item => {
    // Mode match
    if (currentFilterMode !== "all" && item.mode !== currentFilterMode) {
      return false;
    }
    // Search query match
    if (query) {
      const titleMatch = (item.title || "").toLowerCase().includes(query);
      const sourceMatch = (item.sourceText || "").toLowerCase().includes(query);
      const summaryMatch = (item.resultData && item.resultData.summary ? item.resultData.summary : "").toLowerCase().includes(query);
      const tagMatch = Array.isArray(item.tags) && item.tags.some(t => t.toLowerCase().includes(query));
      if (!titleMatch && !sourceMatch && !summaryMatch && !tagMatch) {
        return false;
      }
    }
    return true;
  });

  if (countBadge) {
    countBadge.textContent = `${filtered.length} ${filtered.length === 1 ? "document" : "documente"}`;
  }

  if (filtered.length === 0) {
    container.innerHTML = "";
    container.style.display = "none";
    if (emptyState) emptyState.style.display = "flex";
    return;
  }

  if (emptyState) emptyState.style.display = "none";
  container.style.display = "flex";

  container.innerHTML = filtered.map(item => {
    const modeLabel = getModeLabel(item.mode);
    const dateFormatted = formatLocalizedDate(item.createdAt);
    const preview = extractItemPreview(item);
    const badgeClass = `badge-${item.mode || "simplify"}`;

    return `
      <article class="library-card" data-id="${escapeHtml(item.id)}">
        <div class="library-card-header">
          <span class="library-card-badge ${badgeClass}">${escapeHtml(modeLabel)}</span>
          <time class="library-card-date" datetime="${escapeHtml(item.createdAt)}">${escapeHtml(dateFormatted)}</time>
        </div>
        <h3 class="library-card-title">${escapeHtml(item.title)}</h3>
        <p class="library-card-preview">${escapeHtml(preview)}</p>
        <div class="library-card-actions">
          <button type="button" class="btn btn-primary btn-open-item" data-id="${escapeHtml(item.id)}" aria-label="Deschide detaliile pentru ${escapeHtml(item.title)}">
            Deschide detaliile
          </button>
          <button type="button" class="btn btn-secondary btn-delete-item" data-id="${escapeHtml(item.id)}" aria-label="Șterge ${escapeHtml(item.title)}">
            Șterge
          </button>
        </div>
      </article>
    `;
  }).join("");

  // Attach event listeners to card action buttons
  container.querySelectorAll(".btn-open-item").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const item = allLibraryItems.find(it => it.id === id);
      if (item) {
        lastFocusedElement = btn;
        openDetailModal(item);
      }
    });
  });

  container.querySelectorAll(".btn-delete-item").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      handleDeleteItem(id);
    });
  });
}

/**
 * Highlights a verbatim quote in the modal's source viewer.
 */
export function highlightQuoteInModal(quote) {
  const viewer = document.getElementById("detail-source-viewer");
  if (!viewer || !activeModalItem || !activeModalItem.sourceText) return false;

  const rawText = activeModalItem.sourceText;
  if (!quote || !quote.trim()) {
    viewer.textContent = rawText;
    return false;
  }

  const target = quote.trim();
  const idx = rawText.indexOf(target);

  if (idx === -1) {
    viewer.textContent = rawText;
    return false;
  }

  const before = escapeHtml(rawText.substring(0, idx));
  const matched = escapeHtml(rawText.substring(idx, idx + target.length));
  const after = escapeHtml(rawText.substring(idx + target.length));

  viewer.innerHTML = `${before}<mark class="quote-highlight" id="modal-active-quote">${matched}</mark>${after}`;

  const markEl = document.getElementById("modal-active-quote");
  if (markEl) {
    markEl.scrollIntoView({ behavior: "smooth", block: "center" });
    announceToLiveRegion(`Citat evidențiat în textul original: „${target}”`);
    return true;
  }

  return false;
}

/**
 * Renders structured content into the modal body based on item mode.
 */
function renderModalContentBody(item) {
  const body = document.getElementById("detail-content-body");
  if (!body) return;

  const data = item.resultData || {};
  let html = "";

  if (data.summary) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Rezumatul documentului</h3>
        <p class="result-summary-text">${escapeHtml(data.summary)}</p>
      </div>
    `;
  }

  // 1. Simplify Steps & Key Terms
  if (Array.isArray(data.steps) && data.steps.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Pași concreți de urmat</h3>
        <ol class="steps-list">
    `;
    data.steps.forEach((step, idx) => {
      const stepQuote = step.source_quote ? escapeHtml(step.source_quote) : "";
      html += `
        <li class="step-item">
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

  if (Array.isArray(data.key_terms) && data.key_terms.length > 0) {
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

  if (Array.isArray(data.questions_to_ask) && data.questions_to_ask.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Întrebări utile de pus</h3>
        <ul class="questions-list">
    `;
    data.questions_to_ask.forEach(q => {
      html += `<li>${escapeHtml(q)}</li>`;
    });
    html += `</ul></div>`;
  }

  // 2. Plan Tasks
  if (Array.isArray(data.tasks) && data.tasks.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Sarcini extrase (${data.tasks.length})</h3>
        <div class="tasks-grid">
    `;
    data.tasks.forEach(task => {
      const priorityClass = task.priority === "high" ? "priority-high" : "";
      const isAmbiguous = Boolean(task.needs_confirmation);
      const quoteAttr = task.source_quote ? escapeHtml(task.source_quote) : "";

      html += `
        <article class="task-card ${isAmbiguous ? "is-ambiguous" : ""}">
          <div class="task-header">
            <h4 class="task-title">${escapeHtml(task.title)}</h4>
            <span class="priority-tag ${priorityClass}">${escapeHtml(task.priority || "normal")}</span>
          </div>
          ${task.due_text ? `
            <div class="task-due-info">
              <span>Termen: <strong>${escapeHtml(task.due_text)}</strong></span>
              ${isAmbiguous ? `<span class="badge-warning" role="note">⚠️ Necesită confirmare</span>` : ""}
            </div>
          ` : ""}
          ${Array.isArray(task.steps) && task.steps.length > 0 ? `
            <div class="task-substeps">
              <ul>${task.steps.map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
            </div>
          ` : ""}
          ${quoteAttr ? `
            <div class="task-action-bar">
              <button type="button" class="btn-quote" data-quote="${quoteAttr}" aria-label="Arată citatul pentru sarcină în textul original">
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

  // 3. Meeting Decisions & Action Items
  if (Array.isArray(data.decisions) && data.decisions.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Decizii luate în ședință</h3>
        <ul class="decisions-list">
    `;
    data.decisions.forEach(dec => {
      const quoteAttr = dec.source_quote ? escapeHtml(dec.source_quote) : "";
      html += `
        <li>
          <span>${escapeHtml(dec.text)}</span>
          ${quoteAttr ? `
            <button type="button" class="btn-quote btn-quote-inline" data-quote="${quoteAttr}">Arată în text</button>
          ` : ""}
        </li>
      `;
    });
    html += `</ul></div>`;
  }

  if (Array.isArray(data.action_items) && data.action_items.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Plan de acțiuni asignate</h3>
        <div class="tasks-grid">
    `;
    data.action_items.forEach(act => {
      const quoteAttr = act.source_quote ? escapeHtml(act.source_quote) : "";
      html += `
        <article class="task-card">
          <div class="task-header">
            <h4 class="task-title">${escapeHtml(act.task)}</h4>
            ${act.who ? `<span class="priority-tag">${escapeHtml(act.who)}</span>` : ""}
          </div>
          ${act.due_text ? `
            <div class="task-due-info">
              <span>Termen: <strong>${escapeHtml(act.due_text)}</strong></span>
              ${act.needs_confirmation ? `<span class="badge-warning">⚠️ De confirmat</span>` : ""}
            </div>
          ` : ""}
          ${quoteAttr ? `
            <div class="task-action-bar">
              <button type="button" class="btn-quote" data-quote="${quoteAttr}">Arată în text</button>
            </div>
          ` : ""}
        </article>
      `;
    });
    html += `</div></div>`;
  }

  if (Array.isArray(data.unclear_points) && data.unclear_points.length > 0) {
    html += `
      <div class="result-card">
        <h3 class="result-subtitle">Puncte neclare de clarificat ulterior</h3>
        <ul class="unclear-list">
    `;
    data.unclear_points.forEach(point => {
      html += `<li>${escapeHtml(point)}</li>`;
    });
    html += `</ul></div>`;
  }

  body.innerHTML = html;

  // Attach quote button click listeners
  body.querySelectorAll(".btn-quote").forEach(btn => {
    btn.addEventListener("click", () => {
      const quote = btn.getAttribute("data-quote");
      highlightQuoteInModal(quote);
    });
  });
}

/**
 * Opens the item detail modal dialog.
 */
export function openDetailModal(item) {
  if (!item) return;
  activeModalItem = item;
  currentSummaryForTTS = item.resultData && item.resultData.summary ? item.resultData.summary : "";

  const modal = document.getElementById("library-detail-modal");
  const titleEl = document.getElementById("detail-modal-title");
  const metaBar = document.getElementById("detail-meta-bar");
  const icsBtn = document.getElementById("btn-detail-ics");
  const ttsBtn = document.getElementById("btn-detail-tts");
  const sourceViewer = document.getElementById("detail-source-viewer");
  const closeBtn = document.getElementById("btn-close-detail");

  if (!modal) return;

  if (titleEl) titleEl.textContent = item.title;
  if (metaBar) {
    const modeLabel = getModeLabel(item.mode);
    const dateFormatted = formatLocalizedDate(item.createdAt);
    metaBar.innerHTML = `<span><strong>Tip:</strong> ${escapeHtml(modeLabel)}</span> • <span><strong>Salvat:</strong> ${escapeHtml(dateFormatted)}</span>`;
  }

  // Show or hide calendar export button
  if (icsBtn) {
    const hasTasks = item.mode === "plan" && item.resultData && Array.isArray(item.resultData.tasks) && item.resultData.tasks.length > 0;
    icsBtn.style.display = hasTasks ? "inline-flex" : "none";
  }

  // Reset TTS button
  if (ttsBtn) {
    ttsBtn.textContent = "Ascultă rezumatul";
    ttsBtn.setAttribute("aria-pressed", "false");
  }

  // Render structured body
  renderModalContentBody(item);

  // Set original source text
  if (sourceViewer) {
    sourceViewer.textContent = item.sourceText || "(Fără text original salvat)";
  }

  modal.style.display = "flex";
  document.body.style.overflow = "hidden";

  if (closeBtn) closeBtn.focus();
  announceToLiveRegion(`S-au deschis detaliile pentru ${item.title}`);
}

/**
 * Closes the item detail modal dialog.
 */
export function closeDetailModal() {
  const modal = document.getElementById("library-detail-modal");
  if (!modal) return;

  if (isSpeaking) {
    stopSpeaking();
    isSpeaking = false;
  }

  modal.style.display = "none";
  document.body.style.overflow = "";
  activeModalItem = null;

  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
}

/**
 * Handles deletion of an item with a 7-second accessible undo toast.
 */
export function handleDeleteItem(id) {
  if (!id) return;
  const deleted = deleteLibraryItem(id);
  if (!deleted) return;

  lastDeletedItem = deleted;
  allLibraryItems = getLibraryItems();
  renderCardList();

  // If modal was open with this item, close it
  if (activeModalItem && activeModalItem.id === id) {
    closeDetailModal();
  }

  // Show undo toast
  const toast = document.getElementById("library-undo-toast");
  const msg = document.getElementById("undo-toast-message");
  if (toast && msg) {
    msg.textContent = `Documentul «${deleted.title}» a fost șters.`;
    toast.style.display = "flex";

    if (undoTimerId) clearTimeout(undoTimerId);
    undoTimerId = setTimeout(() => {
      toast.style.display = "none";
      lastDeletedItem = null;
    }, 7000);
  }

  announceToLiveRegion(`Documentul ${deleted.title} a fost șters.`);
}

/**
 * Restores the most recently deleted item.
 */
export function handleUndoDelete() {
  if (!lastDeletedItem) return;

  restoreLibraryItem(lastDeletedItem);
  const restoredTitle = lastDeletedItem.title;
  lastDeletedItem = null;

  if (undoTimerId) {
    clearTimeout(undoTimerId);
    undoTimerId = null;
  }

  const toast = document.getElementById("library-undo-toast");
  if (toast) toast.style.display = "none";

  allLibraryItems = getLibraryItems();
  renderCardList();
  announceToLiveRegion(`Ștergerea a fost anulată. Documentul «${restoredTitle}» a fost restaurat.`);
}

/**
 * Toggles TTS speech synthesis for modal summary.
 */
function toggleModalTTS() {
  const ttsBtn = document.getElementById("btn-detail-tts");

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
    announceToLiveRegion("Sinteza vocală nu este suportată pe acest browser.");
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
 * Copies the modal structured result to the clipboard.
 */
async function copyModalResult() {
  const body = document.getElementById("detail-content-body");
  if (!body) return;

  const textToCopy = body.innerText || body.textContent || "";
  if (!textToCopy) return;

  try {
    await navigator.clipboard.writeText(textToCopy);
    const copyBtn = document.getElementById("btn-detail-copy");
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
    announceToLiveRegion("Copierea automată nu este permisă de browser.");
  }
}

/**
 * Downloads calendar .ics for the active modal plan.
 */
function downloadModalIcs() {
  if (!activeModalItem || !activeModalItem.resultData || !Array.isArray(activeModalItem.resultData.tasks)) {
    return;
  }
  const icsContent = generateIcs(activeModalItem.resultData.tasks);
  downloadIcsFile(`primazi-plan-${activeModalItem.id}.ics`, icsContent);
  announceToLiveRegion("Fișierul calendar a fost descărcat.");
}

/**
 * Initializes the Library page controller.
 */
export function initLibraryPage() {
  allLibraryItems = getLibraryItems();

  // Private fallback alert
  const fallbackNotice = document.getElementById("memory-fallback-notice");
  if (fallbackNotice && isLibraryMemoryFallback()) {
    fallbackNotice.style.display = "block";
  }

  // Initial render
  renderCardList();

  // Search input
  const searchInput = document.getElementById("library-search");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      currentSearchQuery = searchInput.value;
      renderCardList();
    });
  }

  // Filter mode select
  const filterSelect = document.getElementById("library-filter-mode");
  if (filterSelect) {
    filterSelect.addEventListener("change", () => {
      currentFilterMode = filterSelect.value;
      renderCardList();
    });
  }

  // Clear all button & confirmation dialog
  const clearAllBtn = document.getElementById("btn-library-clear-all");
  const confirmBox = document.getElementById("confirm-clear-box");
  const confirmClearBtn = document.getElementById("btn-confirm-clear");
  const cancelClearBtn = document.getElementById("btn-cancel-clear");

  if (clearAllBtn && confirmBox) {
    clearAllBtn.addEventListener("click", () => {
      confirmBox.style.display = "block";
      if (cancelClearBtn) cancelClearBtn.focus();
    });
  }

  if (cancelClearBtn && confirmBox) {
    cancelClearBtn.addEventListener("click", () => {
      confirmBox.style.display = "none";
      if (clearAllBtn) clearAllBtn.focus();
    });
  }

  if (confirmClearBtn && confirmBox) {
    confirmClearBtn.addEventListener("click", () => {
      clearLibrary();
      allLibraryItems = [];
      confirmBox.style.display = "none";
      renderCardList();
      announceToLiveRegion("Toate documentele au fost șterse din bibliotecă.");
      if (clearAllBtn) clearAllBtn.focus();
    });
  }

  // Undo button in toast
  const undoBtn = document.getElementById("btn-undo-delete");
  if (undoBtn) {
    undoBtn.addEventListener("click", handleUndoDelete);
  }

  // Modal close button
  const closeDetailBtn = document.getElementById("btn-close-detail");
  if (closeDetailBtn) {
    closeDetailBtn.addEventListener("click", closeDetailModal);
  }

  // Modal actions
  const detailCopyBtn = document.getElementById("btn-detail-copy");
  const detailTtsBtn = document.getElementById("btn-detail-tts");
  const detailIcsBtn = document.getElementById("btn-detail-ics");
  const detailDeleteBtn = document.getElementById("btn-detail-delete");

  if (detailCopyBtn) detailCopyBtn.addEventListener("click", copyModalResult);
  if (detailTtsBtn) detailTtsBtn.addEventListener("click", toggleModalTTS);
  if (detailIcsBtn) detailIcsBtn.addEventListener("click", downloadModalIcs);
  if (detailDeleteBtn) {
    detailDeleteBtn.addEventListener("click", () => {
      if (activeModalItem) {
        handleDeleteItem(activeModalItem.id);
      }
    });
  }

  // Modal backdrop click to close
  const modal = document.getElementById("library-detail-modal");
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        closeDetailModal();
      }
    });
  }

  // Global Escape key handler
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (modal && modal.style.display === "flex") {
        closeDetailModal();
      } else if (confirmBox && confirmBox.style.display === "block") {
        confirmBox.style.display = "none";
        if (clearAllBtn) clearAllBtn.focus();
      }
    }
  });
}

// Auto-initialize when DOM is loaded
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initLibraryPage);
}

