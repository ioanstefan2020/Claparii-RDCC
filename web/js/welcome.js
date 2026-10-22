/**
 * welcome.js - Interactive Welcome Questionnaire Wizard & Live Preview
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 * Owner: p3
 * Spec: docs/NEXT-STEPS.md (§1, §2) & docs/plan/p3.md (N3.3)
 */

import { QUESTIONNAIRE_RO } from "./prefs/questionnaire.js";
import { derivePrefs } from "./prefs/derive.js";
import { applyPrefs } from "./prefs/apply.js";
import { loadPrefs, savePrefs } from "./prefs/storage.js";
import { DEFAULT_ANSWERS, createDefaultState } from "./prefs/types.js";

// Wizard state
export const welcomeState = {
  currentStep: 0,
  totalSteps: QUESTIONNAIRE_RO.length,
  answers: { ...DEFAULT_ANSWERS },
  prefs: {}
};

/**
 * Escapes characters for safe DOM insertion.
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
 * Announces message to screen reader via live region.
 */
export function announce(message) {
  const live = document.getElementById("status-live");
  if (live) {
    live.textContent = "";
    setTimeout(() => { live.textContent = message; }, 40);
  }
}

/**
 * Updates the badges and sample document inside the Live Preview panel.
 */
export function updateLivePreview() {
  const derived = derivePrefs(welcomeState.answers);
  welcomeState.prefs = derived;
  applyPrefs(derived, document.documentElement);

  // Update badges
  const textBadge = document.getElementById("badge-pref-text");
  const spacingBadge = document.getElementById("badge-pref-spacing");
  const contrastBadge = document.getElementById("badge-pref-contrast");
  const formatBadge = document.getElementById("badge-pref-format");

  if (textBadge) {
    const sizeMap = { slow: "Mare (L)", medium: "Standard (M)", fast: "Compact" };
    textBadge.textContent = `Text: ${sizeMap[welcomeState.answers.readingPace] || "Standard"}`;
  }

  if (spacingBadge) {
    const spacingMap = { slow: "Aerisită / Generoasă", medium: "Confortabilă", fast: "Compactă" };
    spacingBadge.textContent = `Spațiere: ${spacingMap[welcomeState.answers.readingPace] || "Confortabilă"}`;
  }

  if (contrastBadge) {
    contrastBadge.textContent = `Contrast: ${welcomeState.answers.visualNoise === "low" ? "Înalt (AAA)" : "Normal"}`;
  }

  if (formatBadge) {
    formatBadge.textContent = `Format: ${welcomeState.answers.stepByStep ? "Pași numerotați" : "Text cursiv"}`;
  }

  // Update sample card content based on format & text amount
  const contentEl = document.getElementById("preview-sample-content");
  if (contentEl) {
    const isSteps = welcomeState.answers.stepByStep;
    const isShort = welcomeState.answers.textAmount === "short";

    if (isSteps) {
      contentEl.innerHTML = `
        <ol class="steps-list" style="margin: 0; padding-left: var(--space-lg);">
          <li><strong>Prezentarea la birou:</strong> Luni la 09:00 primești ecusonul și laptopul.</li>
          <li><strong>Documente administrative:</strong> Transmiți buletinul și formularul F-12 completat.</li>
          ${!isShort ? `<li><strong>Mentorul alocat:</strong> Marți configurezi mediul de lucru și conturile.</li>` : ""}
        </ol>
      `;
    } else {
      contentEl.innerHTML = `
        <p style="margin: 0 0 var(--space-xs) 0;">
          În prima zi (luni, ora 09:00), te prezinți la recepție pentru ecuson și echipamente.
        </p>
        <p style="margin: 0;">
          Până miercuri transmiți documentele scanate la HR, iar marți configurezi conturile cu mentorul tău.
        </p>
      `;
    }
  }
}

/**
 * Handles choosing an answer option.
 */
export function selectOption(questionId, value) {
  welcomeState.answers[questionId] = value;
  updateLivePreview();

  // Highlight selected card visually
  const options = document.querySelectorAll(".radio-card");
  options.forEach(card => {
    const input = card.querySelector("input");
    if (input) {
      const match = String(input.value) === String(value);
      card.classList.toggle("is-selected", match);
      input.checked = match;
    }
  });

  const question = QUESTIONNAIRE_RO[welcomeState.currentStep];
  const selectedOpt = question && question.options ? question.options.find(o => String(o.value) === String(value)) : null;
  const label = selectedOpt ? selectedOpt.label : String(value);
  announce(`Opțiunea „${label}” a fost selectată. Previzualizarea s-a actualizat.`);
}

/**
 * Renders the wizard question at the given step index.
 */
export function renderStep(stepIndex) {
  if (stepIndex < 0 || stepIndex >= welcomeState.totalSteps) return;
  welcomeState.currentStep = stepIndex;

  const question = QUESTIONNAIRE_RO[stepIndex];
  if (!question) return;

  // Update step badge & progress bar
  const counterEl = document.getElementById("wizard-step-counter");
  const progressEl = document.getElementById("wizard-progress-bar");
  if (counterEl) counterEl.textContent = `Întrebarea ${stepIndex + 1} din ${welcomeState.totalSteps}`;
  if (progressEl) {
    const percent = Math.round(((stepIndex + 1) / welcomeState.totalSteps) * 100);
    progressEl.style.width = `${percent}%`;
  }

  // Update prompt & help text
  const promptEl = document.getElementById("question-prompt");
  const helpEl = document.getElementById("question-help");
  if (promptEl) promptEl.textContent = question.prompt;
  if (helpEl) helpEl.textContent = question.helpText || "";

  // Render options
  const optionsContainer = document.getElementById("question-options");
  if (optionsContainer) {
    const currentVal = welcomeState.answers[question.id];
    let html = "";

    question.options.forEach((opt, idx) => {
      const isSelected = String(currentVal) === String(opt.value);
      const optId = `opt-${question.id}-${idx}`;

      html += `
        <label for="${optId}" class="radio-card ${isSelected ? 'is-selected' : ''}">
          <input type="radio" id="${optId}" name="${question.id}" value="${escapeHtml(String(opt.value))}" ${isSelected ? 'checked' : ''} class="radio-input">
          <div class="radio-label-group">
            <span class="radio-title">${escapeHtml(opt.label)}</span>
            <span class="radio-desc">${escapeHtml(opt.description || "")}</span>
          </div>
        </label>
      `;
    });

    optionsContainer.innerHTML = html;

    // Attach click and change listeners
    const inputs = optionsContainer.querySelectorAll("input[type='radio']");
    inputs.forEach((input, idx) => {
      input.addEventListener("change", (e) => {
        let val = e.target.value;
        if (val === "true") val = true;
        else if (val === "false") val = false;
        selectOption(question.id, val);
      });
    });
  }

  // Update action buttons
  const prevBtn = document.getElementById("btn-wizard-prev");
  const nextBtn = document.getElementById("btn-wizard-next");
  const saveBtn = document.getElementById("btn-wizard-save");

  if (prevBtn) prevBtn.disabled = (stepIndex === 0);

  const isLast = (stepIndex === welcomeState.totalSteps - 1);
  if (nextBtn) nextBtn.style.display = isLast ? "none" : "inline-flex";
  if (saveBtn) saveBtn.style.display = isLast ? "inline-flex" : "none";

  announce(`Întrebarea ${stepIndex + 1}: ${question.prompt}`);
}

/**
 * Navigates to next step.
 */
export function nextStep() {
  if (welcomeState.currentStep < welcomeState.totalSteps - 1) {
    renderStep(welcomeState.currentStep + 1);
    const legend = document.getElementById("question-prompt");
    if (legend) legend.focus();
  }
}

/**
 * Navigates to previous step.
 */
export function prevStep() {
  if (welcomeState.currentStep > 0) {
    renderStep(welcomeState.currentStep - 1);
    const legend = document.getElementById("question-prompt");
    if (legend) legend.focus();
  }
}

/**
 * Saves current preferences state and redirects to Home.
 */
export function saveAndContinue() {
  const derived = derivePrefs(welcomeState.answers);
  const state = {
    version: 1,
    updatedAt: new Date().toISOString(),
    answers: { ...welcomeState.answers },
    prefs: derived,
    overrides: []
  };

  savePrefs(state);
  announce("Preferințele tale au fost salvate. Te redirecționăm...");
  setTimeout(() => {
    window.location.href = "/";
  }, 250);
}

/**
 * Initializes the Welcome Questionnaire page.
 */
export function initWelcome() {
  // Load saved state or create default
  const loaded = loadPrefs();
  if (loaded && loaded.answers) {
    welcomeState.answers = { ...welcomeState.answers, ...loaded.answers };
  }

  // Initial live preview sync
  updateLivePreview();

  // Render question 1
  renderStep(0);

  // Wire buttons
  const nextBtn = document.getElementById("btn-wizard-next");
  const prevBtn = document.getElementById("btn-wizard-prev");
  const saveBtn = document.getElementById("btn-wizard-save");
  const saveNowBtn = document.getElementById("btn-wizard-save-now");

  if (nextBtn) nextBtn.addEventListener("click", nextStep);
  if (prevBtn) prevBtn.addEventListener("click", prevStep);
  if (saveBtn) saveBtn.addEventListener("click", saveAndContinue);
  if (saveNowBtn) saveNowBtn.addEventListener("click", saveAndContinue);
}

// Auto-init
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initWelcome);

  // Global focus mode tracking: eliminate outlines on mouse clicks everywhere, preserve for keyboard
  document.addEventListener(
    "pointerdown",
    () => {
      document.documentElement.setAttribute("data-focus-mode", "mouse");
    },
    true,
  );
  document.addEventListener(
    "keydown",
    (e) => {
      if (e.key === "Tab" || (e.key && e.key.startsWith("Arrow"))) {
        document.documentElement.setAttribute("data-focus-mode", "keyboard");
      }
    },
    true,
  );
}
