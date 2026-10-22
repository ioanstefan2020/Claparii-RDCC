/**
 * options.js - Full Settings & Onboarding Controller
 * Handles the 7 plain-language comfort questions, live preview,
 * free-text box, export/import JSON, and connection parameters.
 */

import { QUESTIONNAIRE_RO } from "../shared/prefs/questionnaire.js";
import { derivePrefs } from "../shared/prefs/derive.js";

const DEFAULT_CONFIG = {
  backendUrl: "http://localhost:8000",
  token: "primazi-demo-2026",
  siteOrigins: ["http://localhost:8000", "http://127.0.0.1:8000"],
  localOnly: false,
  disabledSites: []
};

let currentAnswers = {};
let currentPrefs = {};
let currentConfig = { ...DEFAULT_CONFIG };
let currentFreeText = "";

document.addEventListener("DOMContentLoaded", async () => {
  await loadStoredData();
  renderQuestions();
  setupEventListeners();
  updateLivePreview();
});

async function loadStoredData() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type: "PREFS_GET" }, (res) => {
      if (res) {
        const storedPrefs = res.prefs || {};
        currentAnswers = storedPrefs.answers || {};
        currentPrefs = storedPrefs.prefs || {};
        currentFreeText = storedPrefs.freeText || "";
        currentConfig = { ...DEFAULT_CONFIG, ...(res.config || {}) };

        // Populate form inputs
        const freeTextInput = document.getElementById("freeTextInput");
        if (freeTextInput) {
          freeTextInput.value = currentFreeText;
          updateCharCount(currentFreeText);
        }

        const backendUrlInput = document.getElementById("backendUrlInput");
        if (backendUrlInput) backendUrlInput.value = currentConfig.backendUrl || "http://localhost:8000";

        const tokenInput = document.getElementById("tokenInput");
        if (tokenInput) tokenInput.value = currentConfig.token || "primazi-demo-2026";

        const localOnlyCheckbox = document.getElementById("localOnlyCheckbox");
        if (localOnlyCheckbox) localOnlyCheckbox.checked = !!currentConfig.localOnly;
      }
      resolve();
    });
  });
}

function renderQuestions() {
  const container = document.getElementById("questionsContainer");
  if (!container) return;
  container.innerHTML = "";

  for (const q of QUESTIONNAIRE_RO) {
    const block = document.createElement("fieldset");
    block.className = "question-block";
    block.style.border = "none";
    block.style.padding = "0";

    const legend = document.createElement("legend");
    legend.className = "question-prompt";
    legend.textContent = q.prompt;
    block.appendChild(legend);

    if (q.helpText) {
      const help = document.createElement("div");
      help.className = "question-help";
      help.textContent = q.helpText;
      block.appendChild(help);
    }

    const grid = document.createElement("div");
    grid.className = "options-grid";

    for (const opt of q.options) {
      const card = document.createElement("label");
      const isChecked = currentAnswers[q.id] === opt.value;
      card.className = `radio-card ${isChecked ? "selected" : ""}`;

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = q.id;
      radio.value = String(opt.value);
      radio.checked = isChecked;

      radio.addEventListener("change", () => {
        // Update selection class on siblings
        const allCards = grid.querySelectorAll(".radio-card");
        allCards.forEach(c => c.classList.remove("selected"));
        card.classList.add("selected");

        // Parse boolean if needed
        let val = opt.value;
        if (val === true || val === false) {
          val = radio.value === "true";
        }
        currentAnswers[q.id] = val;

        // Re-derive UI preferences
        currentPrefs = derivePrefs(currentAnswers, currentPrefs);
        updateLivePreview();
      });

      const labelWrap = document.createElement("div");
      const titleSpan = document.createElement("span");
      titleSpan.className = "radio-label";
      titleSpan.textContent = opt.label;

      const descSpan = document.createElement("span");
      descSpan.className = "radio-desc";
      descSpan.textContent = opt.description;

      labelWrap.appendChild(titleSpan);
      labelWrap.appendChild(descSpan);

      card.appendChild(radio);
      card.appendChild(labelWrap);
      grid.appendChild(card);
    }

    block.appendChild(grid);
    container.appendChild(block);
  }
}

function updateCharCount(text) {
  const counter = document.getElementById("charCount");
  if (counter) {
    counter.textContent = `${(text || "").length} / 300`;
  }
}

function updateLivePreview() {
  const box = document.getElementById("previewBox");
  if (!box) return;

  const p = currentPrefs || {};

  // Font scale
  if (p.textSize === "l") {
    box.style.fontSize = "18px";
  } else if (p.textSize === "xl") {
    box.style.fontSize = "20px";
  } else {
    box.style.fontSize = "16px";
  }

  // Spacing
  if (p.spacing === "roomy") {
    box.style.lineHeight = "2.0";
    box.style.letterSpacing = "0.02em";
  } else {
    box.style.lineHeight = "1.7";
    box.style.letterSpacing = "normal";
  }

  // Contrast / theme
  if (p.contrast === "high") {
    box.style.background = "#000000";
    box.style.color = "#ffff00";
    box.style.border = "3px solid #ffff00";
  } else {
    box.style.background = "#fafafa";
    box.style.color = "#0f172a";
    box.style.border = "2px dashed var(--primary)";
  }
}

function showToast(message) {
  const toast = document.getElementById("statusToast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

function setupEventListeners() {
  const freeTextInput = document.getElementById("freeTextInput");
  if (freeTextInput) {
    freeTextInput.addEventListener("input", (e) => {
      currentFreeText = e.target.value.slice(0, 300);
      updateCharCount(currentFreeText);
    });
  }

  // Save Settings
  const saveBtn = document.getElementById("saveBtn");
  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      const backendUrl = (document.getElementById("backendUrlInput")?.value || "http://localhost:8000").trim();
      const token = (document.getElementById("tokenInput")?.value || "primazi-demo-2026").trim();
      const localOnly = !!document.getElementById("localOnlyCheckbox")?.checked;

      // Update config
      currentConfig.backendUrl = backendUrl;
      currentConfig.token = token;
      currentConfig.localOnly = localOnly;

      chrome.runtime.sendMessage({
        type: "CONFIG_SET",
        config: currentConfig
      });

      // Update prefs
      const payload = {
        version: 1,
        source: "extension_manual",
        updatedAt: new Date().toISOString(),
        answers: currentAnswers,
        prefs: currentPrefs,
        overrides: Object.keys(currentPrefs || {}),
        freeText: currentFreeText
      };

      chrome.runtime.sendMessage({
        type: "PREFS_SET",
        prefs: payload
      }, () => {
        showToast("✓ Toate preferințele și conexiunea au fost salvate cu succes!");
      });
    });
  }

  // Export JSON
  const exportBtn = document.getElementById("exportBtn");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      const exportData = {
        version: 1,
        source: "extension",
        exportedAt: new Date().toISOString(),
        answers: currentAnswers,
        prefs: currentPrefs,
        freeText: currentFreeText,
        config: {
          backendUrl: currentConfig.backendUrl,
          localOnly: currentConfig.localOnly
        }
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `primazi-setari-extensie-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      showToast("✓ Setările au fost descărcate în format JSON.");
    });
  }

  // Import JSON
  const importBtn = document.getElementById("importBtn");
  const fileInput = document.getElementById("importFileInput");
  if (importBtn && fileInput) {
    importBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const parsed = JSON.parse(event.target.result);
          if (parsed.answers) currentAnswers = parsed.answers;
          if (parsed.prefs) currentPrefs = parsed.prefs;
          if (parsed.freeText) currentFreeText = parsed.freeText;
          if (parsed.config) currentConfig = { ...currentConfig, ...parsed.config };

          renderQuestions();
          if (freeTextInput) freeTextInput.value = currentFreeText;
          updateCharCount(currentFreeText);
          updateLivePreview();
          showToast("✓ Setările au fost importate cu succes! Apasă 'Salvează setările'.");
        } catch (err) {
          showToast("❌ Fișierul selectat nu este un JSON valid.");
        }
      };
      reader.readAsText(file);
    });
  }

  // Reset
  const resetBtn = document.getElementById("resetBtn");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (confirm("Sigur dorești să resetezi toate preferințele la setările inițiale?")) {
        currentAnswers = {};
        currentPrefs = derivePrefs({});
        currentFreeText = "";
        currentConfig = { ...DEFAULT_CONFIG };

        renderQuestions();
        if (freeTextInput) freeTextInput.value = "";
        updateCharCount("");
        updateLivePreview();
        showToast("Setările au fost resetate la valorile implicite.");
      }
    });
  }
}
