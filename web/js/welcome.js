/**
 * welcome.js - Interactive Welcome Questionnaire Wizard & Live Preview
 * Project: Limpede (formerly PrimaZi) (AccessABILITY Hackathon 2026)
 * Owner: p2 / p3
 * Spec: docs/NEXT-STEPS.md (§1, §2) & docs/TASKS-WAVE2.md (T2.L3 & T2.L4)
 */

import { QUESTIONNAIRE_RO, getQuestionnaire } from "./prefs/questionnaire.js";
import { derivePrefs } from "./prefs/derive.js";
import { applyPrefs } from "./prefs/apply.js";
import { loadPrefs, savePrefs } from "./prefs/storage.js";
import { DEFAULT_ANSWERS } from "./prefs/types.js";

// Wizard state
export const welcomeState = {
  currentStep: 0,
  lang: "ro",
  get questionnaire() {
    return getQuestionnaire(this.lang);
  },
  get totalSteps() {
    return this.questionnaire.length;
  },
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
  const loaded = loadPrefs();
  const currentTheme = document.documentElement.getAttribute("data-theme") || (loaded && loaded.prefs && loaded.prefs.theme) || "light";
  
  // Notice: pass [] for overrides so that questionnaire answers ALWAYS derive the visual preferences directly
  const derived = derivePrefs(welcomeState.answers, loaded ? loaded.prefs : {}, []);
  derived.theme = currentTheme;
  if (loaded && loaded.prefs && loaded.prefs.sidebar) {
    derived.sidebar = loaded.prefs.sidebar;
  }
  
  welcomeState.prefs = derived;
  applyPrefs(derived, document.documentElement);
  document.documentElement.setAttribute("data-theme", currentTheme);

  // Update contrast styling on preview sample card
  const sampleCard = document.getElementById("preview-sample-card");
  const isLowNoise = welcomeState.answers.visualNoise === "low";
  if (sampleCard) {
    sampleCard.classList.toggle("is-high-contrast", isLowNoise);
  }

  // Update badges
  const textBadge = document.getElementById("badge-pref-text");
  const spacingBadge = document.getElementById("badge-pref-spacing");
  const densityBadge = document.getElementById("badge-pref-density");
  const formatBadge = document.getElementById("badge-pref-format");
  const contrastBadge = document.getElementById("badge-pref-contrast");
  const motionBadge = document.getElementById("badge-pref-motion");
  const langBadge = document.getElementById("badge-pref-lang");
  const timeBadge = document.getElementById("badge-pref-time");

  const isEn = welcomeState.lang === "en" || welcomeState.answers.language === "en";
  const pace = welcomeState.answers.readingPace;

  if (textBadge) {
    const textLabelRo = pace === "slow" ? "Text: Mare (20px)" : (pace === "fast" ? "Text: Compact (17px)" : "Text: Standard (17px)");
    const textLabelEn = pace === "slow" ? "Text: Large (20px)" : (pace === "fast" ? "Text: Compact (17px)" : "Text: Standard (17px)");
    textBadge.textContent = isEn ? textLabelEn : textLabelRo;
  }

  if (spacingBadge) {
    const spacingLabelRo = pace === "slow" ? "Spațiere: Aerisită (1.9x)" : (pace === "fast" ? "Spațiere: Densă (1.5x)" : "Spațiere: Confortabilă (1.6x)");
    const spacingLabelEn = pace === "slow" ? "Spacing: Airy (1.9x)" : (pace === "fast" ? "Spacing: Dense (1.5x)" : "Spacing: Comfortable (1.6x)");
    spacingBadge.textContent = isEn ? spacingLabelEn : spacingLabelRo;
  }

  if (densityBadge) {
    const amt = welcomeState.answers.textAmount;
    const amtLabelRo = amt === "short" ? "Conținut: Esențial" : (amt === "full" ? "Conținut: Detaliat" : "Conținut: Echilibrat");
    const amtLabelEn = amt === "short" ? "Content: Essential" : (amt === "full" ? "Content: Detailed" : "Content: Balanced");
    densityBadge.textContent = isEn ? amtLabelEn : amtLabelRo;
  }

  const isSteps = Boolean(welcomeState.answers.stepByStep);
  if (formatBadge) {
    if (isEn) {
      formatBadge.textContent = isSteps ? "Format: Numbered steps" : "Format: Flowing text";
    } else {
      formatBadge.textContent = isSteps ? "Format: Pași numerotați" : "Format: Text continuu";
    }
  }

  if (contrastBadge) {
    if (isEn) {
      contrastBadge.textContent = isLowNoise ? "Contrast: High (AAA)" : "Contrast: Normal";
    } else {
      contrastBadge.textContent = isLowNoise ? "Contrast: Ridicat (AAA)" : "Contrast: Normal";
    }
  }

  const isQuiet = welcomeState.answers.sensory === "quiet";
  if (motionBadge) {
    if (isEn) {
      motionBadge.textContent = isQuiet ? "Animations: Off (Calm)" : "Animations: Active";
    } else {
      motionBadge.textContent = isQuiet ? "Animații: Oprite (Calm)" : "Animații: Active";
    }
  }

  if (langBadge) {
    langBadge.textContent = isEn ? "Language: English 🇬🇧" : "Limbă: Română 🇷🇴";
  }

  const isNeedMoreTime = welcomeState.answers.timeToDecide === "need-more-time";
  if (timeBadge) {
    if (isEn) {
      timeBadge.textContent = isNeedMoreTime ? "Time: Unlimited pace ⏱️" : "Time: Standard";
    } else {
      timeBadge.textContent = isNeedMoreTime ? "Timp: Fără grabă ⏱️" : "Timp: Standard";
    }
  }

  // Highlight active step badge
  const allBadges = document.querySelectorAll(".pref-badge");
  allBadges.forEach(b => b.classList.remove("is-active-step"));
  const stepIndex = welcomeState.currentStep;
  if (stepIndex === 0) {
    if (textBadge) textBadge.classList.add("is-active-step");
    if (spacingBadge) spacingBadge.classList.add("is-active-step");
  } else if (stepIndex === 1) {
    if (densityBadge) densityBadge.classList.add("is-active-step");
  } else if (stepIndex === 2) {
    if (formatBadge) formatBadge.classList.add("is-active-step");
  } else if (stepIndex === 3) {
    if (contrastBadge) contrastBadge.classList.add("is-active-step");
  } else if (stepIndex === 4) {
    if (motionBadge) motionBadge.classList.add("is-active-step");
  } else if (stepIndex === 5) {
    if (langBadge) langBadge.classList.add("is-active-step");
  } else if (stepIndex === 6) {
    if (timeBadge) timeBadge.classList.add("is-active-step");
  }

  // Update sample card title & content
  const titleEl = document.getElementById("preview-sample-title");
  if (titleEl) {
    titleEl.textContent = isEn ? "Day 1 Guide: Essential Actions" : "Ghid de primă zi: Pași esențiali";
  }

  const contentEl = document.getElementById("preview-sample-content");
  if (contentEl) {
    const amt = welcomeState.answers.textAmount;

    if (isSteps) {
      if (isEn) {
        if (amt === "short") {
          contentEl.innerHTML = `
            <ol class="preview-steps-list">
              <li><strong>Office Arrival:</strong> Monday at 09:00 at reception for badge and work laptop.</li>
              <li><strong>HR Documents:</strong> Submit national ID and completed onboarding form.</li>
            </ol>
          `;
        } else if (amt === "full") {
          contentEl.innerHTML = `
            <ol class="preview-steps-list">
              <li><strong>Office Arrival:</strong> Monday at 09:00 at reception for badge, security card, and laptop.</li>
              <li><strong>HR Documents:</strong> Submit ID, paperwork, and signed employment agreements.</li>
              <li><strong>Mentor Meeting:</strong> Tuesday at 11:00 set up dev environment, credentials, and week 1 roadmap.</li>
              <li><strong>Team Intro:</strong> Wednesday at 14:00 meet teammates and review operational rhythm.</li>
            </ol>
          `;
        } else {
          contentEl.innerHTML = `
            <ol class="preview-steps-list">
              <li><strong>Office Arrival:</strong> Monday at 09:00 at reception for badge and work laptop.</li>
              <li><strong>HR Documents:</strong> Submit national ID and completed onboarding form.</li>
              <li><strong>Mentor Meeting:</strong> Tuesday at 11:00 set up accounts and first milestones.</li>
            </ol>
          `;
        }
      } else {
        if (amt === "short") {
          contentEl.innerHTML = `
            <ol class="preview-steps-list">
              <li><strong>Prezentarea la birou:</strong> Luni la ora 09:00 te prezinți la recepție pentru ecuson și laptop.</li>
              <li><strong>Documente HR:</strong> Transmiți buletinul și formularul F-12 completat.</li>
            </ol>
          `;
        } else if (amt === "full") {
          contentEl.innerHTML = `
            <ol class="preview-steps-list">
              <li><strong>Prezentarea la birou:</strong> Luni la ora 09:00 te prezinți la recepție pentru ecuson, cartelă și laptopul de lucru.</li>
              <li><strong>Documente HR:</strong> Transmiți buletinul și formularul F-12 semnat către departamentul de personal.</li>
              <li><strong>Întâlnirea cu mentorul:</strong> Marți la 11:00 configurezi mediul tehnic și discutați obiectivele din prima lună.</li>
              <li><strong>Sesiunea cu echipa:</strong> Miercuri la 14:00 faci cunoștință cu colegii din departament.</li>
            </ol>
          `;
        } else {
          contentEl.innerHTML = `
            <ol class="preview-steps-list">
              <li><strong>Prezentarea la birou:</strong> Luni la ora 09:00 te prezinți la recepție pentru ecuson și laptop.</li>
              <li><strong>Documente HR:</strong> Transmiți buletinul și formularul F-12 completat.</li>
              <li><strong>Întâlnirea cu mentorul:</strong> Marți la 11:00 configurezi conturile de lucru și primele sarcini.</li>
            </ol>
          `;
        }
      }
    } else {
      if (isEn) {
        if (amt === "short") {
          contentEl.innerHTML = `
            <p class="preview-paragraph">
              On your first day (Monday at 09:00), report to reception to collect your badge and laptop. Submit your ID and paperwork to HR by end of day.
            </p>
          `;
        } else if (amt === "full") {
          contentEl.innerHTML = `
            <p class="preview-paragraph">
              On your first day (Monday at 09:00), collect your badge, security card, and laptop from the main reception.
            </p>
            <p class="preview-paragraph">
              Submit your ID and signed administrative documents to HR by Wednesday.
            </p>
            <p class="preview-paragraph">
              On Tuesday at 11:00, join your dedicated 1-on-1 mentor session to configure accounts, communication channels, and first-month goals.
            </p>
          `;
        } else {
          contentEl.innerHTML = `
            <p class="preview-paragraph">
              On your first day (Monday at 09:00), arrive at reception to collect your badge and work computer.
            </p>
            <p class="preview-paragraph">
              Submit administrative documents to HR, and meet your mentor Tuesday at 11:00 to configure your accounts.
            </p>
          `;
        }
      } else {
        if (amt === "short") {
          contentEl.innerHTML = `
            <p class="preview-paragraph">
              În prima zi (luni, ora 09:00), te prezinți la recepție pentru ecuson și laptop. Până la sfârșitul zilei transmiți buletinul și formularul F-12 la HR.
            </p>
          `;
        } else if (amt === "full") {
          contentEl.innerHTML = `
            <p class="preview-paragraph">
              În prima zi (luni, ora 09:00), te prezinți la recepție pentru preluarea ecusonului, cartelei de acces și laptopului.
            </p>
            <p class="preview-paragraph">
              Până miercuri finalizezi transmiterea cărții de identitate și a formularelor administrative către departamentul HR.
            </p>
            <p class="preview-paragraph">
              Marți la 11:00 are loc sesiunea dedicată de acomodare cu mentorul tău pentru configurarea conturilor și a obiectivelor din prima lună.
            </p>
          `;
        } else {
          contentEl.innerHTML = `
            <p class="preview-paragraph">
              În prima zi (luni, ora 09:00), te prezinți la recepție pentru ecuson și laptopul de lucru.
            </p>
            <p class="preview-paragraph">
              Transmiți documentele la HR, iar marți la 11:00 ai prima întâlnire cu mentorul tău pentru configurarea conturilor și priorităților.
            </p>
          `;
        }
      }
    }
  }

  // Update preview hint
  const hintEl = document.getElementById("preview-hint");
  if (hintEl) {
    if (isNeedMoreTime) {
      hintEl.innerHTML = isEn
        ? "⏱️ <strong>Unlimited Pace Active:</strong> Automatic continuous saving with no countdowns or expiration timers. Your data stays safe on this device."
        : "⏱️ <strong>Mod fără grabă activat:</strong> Salvare automată continuă, fără cronometre sau limite de timp. Progresul tău este salvat pe acest dispozitiv.";
    } else {
      hintEl.innerHTML = isEn
        ? "💡 <em>Tip:</em> You can adjust these visual and cognitive comfort options at any time from the Comfort Settings button."
        : "💡 <em>Sfat:</em> Poți schimba oricând aceste setări ulterior din butonul „Setări confort”.";
    }
  }
}

/**
 * Handles choosing an answer option.
 */
export function selectOption(questionId, value) {
  welcomeState.answers[questionId] = value;

  // Language toggle handling
  if (questionId === "language") {
    const newLang = value === "en" ? "en" : "ro";
    welcomeState.lang = newLang;
    try {
      localStorage.setItem("limpede_lang", newLang);
    } catch (e) {}
    document.documentElement.setAttribute("data-lang", newLang);
  }

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

  const question = welcomeState.questionnaire[welcomeState.currentStep];
  const selectedOpt = question && question.options ? question.options.find(o => String(o.value) === String(value)) : null;
  const label = selectedOpt ? selectedOpt.label : String(value);
  const isEn = welcomeState.lang === "en";
  announce(isEn ? `Option "${label}" selected. Live preview updated.` : `Opțiunea „${label}” a fost selectată. Previzualizarea s-a actualizat.`);

  // If language was just changed, re-render step to update bilingual labels & prompts immediately
  if (questionId === "language") {
    renderStep(welcomeState.currentStep);
  }
}

/**
 * Renders the wizard question at the given step index.
 */
export function renderStep(stepIndex) {
  const qList = welcomeState.questionnaire;
  if (stepIndex < 0 || stepIndex >= qList.length) return;
  welcomeState.currentStep = stepIndex;

  const question = qList[stepIndex];
  if (!question) return;

  const isEn = welcomeState.lang === "en";

  // Update step badge & progress bar
  const counterEl = document.getElementById("wizard-step-counter");
  const progressEl = document.getElementById("wizard-progress-bar");
  if (counterEl) {
    counterEl.textContent = isEn
      ? `Question ${stepIndex + 1} of ${qList.length}`
      : `Întrebarea ${stepIndex + 1} din ${qList.length}`;
  }
  if (progressEl) {
    const percent = Math.round(((stepIndex + 1) / qList.length) * 100);
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
        <label for="${optId}" class="radio-card ${isSelected ? 'is-selected' : ''}" tabindex="0">
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
    const cards = optionsContainer.querySelectorAll(".radio-card");
    cards.forEach((card) => {
      card.addEventListener("click", (e) => {
        const input = card.querySelector("input[type='radio']");
        if (input) {
          input.checked = true;
          let val = input.value;
          if (val === "true") val = true;
          else if (val === "false") val = false;
          selectOption(question.id, val);
        }
      });

      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          const input = card.querySelector("input[type='radio']");
          if (input) {
            input.checked = true;
            let val = input.value;
            if (val === "true") val = true;
            else if (val === "false") val = false;
            selectOption(question.id, val);
          }
        }
      });

      const input = card.querySelector("input[type='radio']");
      if (input) {
        input.addEventListener("change", (e) => {
          let val = e.target.value;
          if (val === "true") val = true;
          else if (val === "false") val = false;
          selectOption(question.id, val);
        });
      }
    });

      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          const input = card.querySelector("input[type='radio']");
          if (input) {
            input.checked = true;
            let val = input.value;
            if (val === "true") val = true;
            else if (val === "false") val = false;
            selectOption(question.id, val);
          }
        }
      });

      const input = card.querySelector("input[type='radio']");
      if (input) {
        input.addEventListener("change", (e) => {
          let val = e.target.value;
          if (val === "true") val = true;
          else if (val === "false") val = false;
          selectOption(question.id, val);
        });
      }
    });
  }

  // Update action buttons text & state
  const prevBtn = document.getElementById("btn-wizard-prev");
  const nextBtn = document.getElementById("btn-wizard-next");
  const saveBtn = document.getElementById("btn-wizard-save");
  const saveNowBtn = document.getElementById("btn-wizard-save-now");
  const skipBtn = document.getElementById("btn-wizard-skip");

  if (prevBtn) {
    prevBtn.disabled = (stepIndex === 0);
    prevBtn.textContent = isEn ? "← Back" : "← Înapoi";
  }

  const isLast = (stepIndex === qList.length - 1);
  if (nextBtn) {
    nextBtn.style.display = isLast ? "none" : "inline-flex";
    nextBtn.textContent = isEn ? "Next →" : "Următoarea →";
  }
  if (saveBtn) {
    saveBtn.style.display = isLast ? "inline-flex" : "none";
    saveBtn.textContent = isEn ? "Save and continue ✓" : "Salvează și continuă ✓";
  }
  if (saveNowBtn) {
    saveNowBtn.textContent = isEn ? "Finish now with these settings" : "Finalizează acum cu aceste setări";
  }
  if (skipBtn) {
    skipBtn.textContent = isEn ? "Skip questionnaire" : "Sari peste chestionar";
  }

  // Update user name field label if present
  const nameLabel = document.querySelector('label[for="wizard-user-name"]');
  const nameInput = document.getElementById("wizard-user-name");
  if (nameLabel) {
    nameLabel.textContent = isEn ? "What's your name? (optional)" : "Cum te numești? (opțional)";
  }
  if (nameInput) {
    nameInput.placeholder = isEn ? "e.g. Alex or Taylor" : "ex: Ana sau David";
  }

  // Re-sync live preview to highlight active step badge and refresh display
  updateLivePreview();

  announce(isEn ? `Question ${stepIndex + 1}: ${question.prompt}` : `Întrebarea ${stepIndex + 1}: ${question.prompt}`);
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
  // Read and persist user name
  const nameInput = document.getElementById("wizard-user-name");
  const rawName = nameInput ? nameInput.value : "";
  const trimmedName = rawName.trim();
  try {
    if (trimmedName) {
      localStorage.setItem("limpede_user_name", trimmedName);
    }
    localStorage.setItem("limpede.welcome.completed", "true");
    if (welcomeState.lang) {
      localStorage.setItem("limpede_lang", welcomeState.lang);
    }
  } catch (e) {}

  if (typeof window !== "undefined" && typeof CustomEvent === "function") {
    window.dispatchEvent(new CustomEvent("limpede:user-name-changed", { detail: { name: trimmedName } }));
  }

  const loaded = loadPrefs();
  const currentTheme = document.documentElement.getAttribute("data-theme") || (loaded && loaded.prefs && loaded.prefs.theme) || "light";
  
  // Directly derive preferences from user's explicit questionnaire answers
  const derived = derivePrefs(welcomeState.answers, loaded ? loaded.prefs : {}, []);
  derived.theme = currentTheme;
  if (loaded && loaded.prefs && loaded.prefs.sidebar) {
    derived.sidebar = loaded.prefs.sidebar;
  }

  const state = {
    version: 1,
    updatedAt: new Date().toISOString(),
    answers: { ...welcomeState.answers },
    prefs: derived,
    overrides: ["theme"] // keep theme override so user's light/dark choice stays preserved
  };

  savePrefs(state);
  applyPrefs(derived, document.documentElement);
  document.documentElement.setAttribute("data-theme", currentTheme);

  const isEn = welcomeState.lang === "en" || welcomeState.answers.language === "en";
  announce(isEn ? "Your preferences have been saved. Redirecting..." : "Preferințele tale au fost salvate. Te redirecționăm...");
  setTimeout(() => {
    window.location.href = "/";
  }, 250);
}

/**
 * Record welcome completed when skipping questionnaire.
 */
export function handleSkip() {
  try {
    localStorage.setItem("limpede.welcome.completed", "true");
  } catch (e) {}
}

/**
 * Initializes the Welcome Questionnaire page.
 */
export function initWelcome() {
  // Check language preference
  try {
    const savedLang = localStorage.getItem("limpede_lang");
    if (savedLang === "en") {
      welcomeState.lang = "en";
      welcomeState.answers.language = "en";
      document.documentElement.setAttribute("data-lang", "en");
    }
  } catch (e) {}

  // Populate user name if previously saved
  try {
    const savedName = localStorage.getItem("limpede_user_name");
    const nameInput = document.getElementById("wizard-user-name");
    if (savedName && nameInput) {
      nameInput.value = savedName;
    }
  } catch (e) {}

  // Load saved state or create default
  const loaded = loadPrefs();
  if (loaded && loaded.answers) {
    welcomeState.answers = { ...welcomeState.answers, ...loaded.answers };
    if (loaded.answers.language === "en") {
      welcomeState.lang = "en";
      document.documentElement.setAttribute("data-lang", "en");
    }
  }
  const currentTheme = (loaded && loaded.prefs && loaded.prefs.theme) || document.documentElement.getAttribute("data-theme") || "light";
  document.documentElement.setAttribute("data-theme", currentTheme);

  // Render question 1 (which automatically triggers initial updateLivePreview)
  renderStep(0);

  // Wire buttons
  const nextBtn = document.getElementById("btn-wizard-next");
  const prevBtn = document.getElementById("btn-wizard-prev");
  const saveBtn = document.getElementById("btn-wizard-save");
  const saveNowBtn = document.getElementById("btn-wizard-save-now");
  const skipBtn = document.getElementById("btn-wizard-skip");
  const topSkipLinks = document.querySelectorAll('a[href="/"].btn-comfort');

  if (nextBtn) nextBtn.addEventListener("click", nextStep);
  if (prevBtn) prevBtn.addEventListener("click", prevStep);
  if (saveBtn) saveBtn.addEventListener("click", saveAndContinue);
  if (saveNowBtn) saveNowBtn.addEventListener("click", saveAndContinue);
  if (skipBtn) skipBtn.addEventListener("click", handleSkip);
  topSkipLinks.forEach(link => link.addEventListener("click", handleSkip));

  // Wire interactive live preview badges to jump directly to questions
  const badgeMap = [
    { id: "badge-pref-text", step: 0 },
    { id: "badge-pref-spacing", step: 0 },
    { id: "badge-pref-density", step: 1 },
    { id: "badge-pref-format", step: 2 },
    { id: "badge-pref-contrast", step: 3 },
    { id: "badge-pref-motion", step: 4 },
    { id: "badge-pref-lang", step: 5 },
    { id: "badge-pref-time", step: 6 },
  ];

  badgeMap.forEach(({ id, step }) => {
    const badge = document.getElementById(id);
    if (badge) {
      badge.addEventListener("click", () => {
        renderStep(step);
        const legend = document.getElementById("question-prompt");
        if (legend) legend.focus();
      });
    }
  });

  // Re-sync live preview whenever topbar header controls change preferences
  window.addEventListener("primazi:pref-changed", () => {
    updateLivePreview();
  });

  const btnContrast = document.getElementById("btn-header-contrast");
  const btnText = document.getElementById("btn-header-text");
  const btnDyslexia = document.getElementById("btn-header-dyslexia");

  if (btnContrast) btnContrast.addEventListener("click", () => setTimeout(updateLivePreview, 50));
  if (btnText) btnText.addEventListener("click", () => setTimeout(updateLivePreview, 50));
  if (btnDyslexia) btnDyslexia.addEventListener("click", () => setTimeout(updateLivePreview, 50));
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
