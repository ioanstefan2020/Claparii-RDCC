/**
 * options.js - Full Settings & Onboarding Controller
 * Handles the 7 plain-language comfort questions, live preview,
 * free-text box, export/import JSON, local storage sync, and connection parameters.
 */

import { QUESTIONNAIRE_RO } from "../shared/prefs/questionnaire.js";
import { derivePrefs } from "../shared/prefs/derive.js";
import { DEFAULT_ANSWERS } from "../shared/prefs/types.js";

const DEFAULT_CONFIG = {
  backendUrl: "https://curves-relates-kenneth-pen.trycloudflare.com",
  token: "primazi-demo-2026",
  siteOrigins: [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://curves-relates-kenneth-pen.trycloudflare.com",
  ],
  localOnly: false,
  disabledSites: [],
};

let currentAnswers = { ...DEFAULT_ANSWERS };
let currentPrefs = derivePrefs(currentAnswers);
let currentConfig = { ...DEFAULT_CONFIG };
let currentFreeText = "";

document.addEventListener("DOMContentLoaded", async () => {
  await loadStoredData();
  renderQuestions();
  setupEventListeners();
  updateLivePreview();
});

async function loadStoredData() {
  try {
    let storedPrefs = {};
    if (
      typeof chrome !== "undefined" &&
      chrome.storage &&
      chrome.storage.local
    ) {
      const stored = await chrome.storage.local.get([
        "wp.ext.prefs.v1",
        "wp.ext.config",
      ]);
      storedPrefs = stored["wp.ext.prefs.v1"] || {};
      currentConfig = {
        ...DEFAULT_CONFIG,
        ...(stored["wp.ext.config"] || {}),
      };
    }

    // Single source of truth / fallback sync with localStorage
    let localFreeText = "";
    let localAnswers = null;
    let localPrefs = null;
    try {
      const userProfileRaw = localStorage.getItem("primazi_user_profile");
      if (userProfileRaw) {
        const up = JSON.parse(userProfileRaw);
        if (up.needs_notes) localFreeText = up.needs_notes;
      }

      const extPrefsRaw =
        localStorage.getItem("wp.ext.prefs.v1") ||
        localStorage.getItem("wp.prefs.v1");
      if (extPrefsRaw) {
        const ep = JSON.parse(extPrefsRaw);
        if (!localFreeText && ep.freeText) localFreeText = ep.freeText;
        if (!localFreeText && ep.answers?.needs_notes)
          localFreeText = ep.answers.needs_notes;
        if (ep.answers) localAnswers = ep.answers;
        if (ep.prefs) localPrefs = ep.prefs;
      }
    } catch (_) {}

    currentAnswers = {
      ...DEFAULT_ANSWERS,
      ...(localAnswers || {}),
      ...(storedPrefs.answers || {}),
    };
    currentPrefs =
      storedPrefs.prefs || localPrefs || derivePrefs(currentAnswers);
    currentFreeText = storedPrefs.freeText || localFreeText || "";

    // Populate form inputs
    const freeTextInput = document.getElementById("freeTextInput");
    if (freeTextInput) {
      freeTextInput.value = currentFreeText;
      updateCharCount(currentFreeText);
    }

    const backendUrlInput = document.getElementById("backendUrlInput");
    if (backendUrlInput) {
      backendUrlInput.value =
        currentConfig.backendUrl || DEFAULT_CONFIG.backendUrl;
    }

    const tokenInput = document.getElementById("tokenInput");
    if (tokenInput) {
      tokenInput.value = currentConfig.token || "primazi-demo-2026";
    }

    const localOnlyCheckbox = document.getElementById("localOnlyCheckbox");
    if (localOnlyCheckbox) {
      localOnlyCheckbox.checked = !!currentConfig.localOnly;
    }
  } catch (err) {
    console.error("Error loading settings from storage:", err);
  }
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
      const isChecked = String(currentAnswers[q.id]) === String(opt.value);
      card.className = `radio-card ${isChecked ? "selected" : ""}`;

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = q.id;
      radio.value = String(opt.value);
      radio.checked = isChecked;

      radio.addEventListener("change", () => {
        // Update visual selection on sibling cards
        const allCards = grid.querySelectorAll(".radio-card");
        allCards.forEach((c) => c.classList.remove("selected"));
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
    counter.textContent = `${(text || "").length} / 500`;
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
      currentFreeText = e.target.value.slice(0, 500);
      updateCharCount(currentFreeText);
    });
  }

  // Save Settings directly into chrome.storage.local and localStorage
  const saveBtn = document.getElementById("saveBtn");
  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const backendUrl = (
        document.getElementById("backendUrlInput")?.value ||
        DEFAULT_CONFIG.backendUrl
      ).trim();
      const token = (
        document.getElementById("tokenInput")?.value || "primazi-demo-2026"
      ).trim();
      const localOnly = !!document.getElementById("localOnlyCheckbox")?.checked;

      // Update config
      currentConfig.backendUrl = backendUrl;
      currentConfig.token = token;
      currentConfig.localOnly = localOnly;

      // Update prefs payload
      const payload = {
        version: 1,
        source: "extension_manual",
        updatedAt: new Date().toISOString(),
        answers: currentAnswers,
        prefs: currentPrefs,
        overrides: Object.keys(currentPrefs || {}),
        freeText: currentFreeText,
      };

      try {
        // 1. Save to chrome.storage.local
        if (
          typeof chrome !== "undefined" &&
          chrome.storage &&
          chrome.storage.local
        ) {
          await chrome.storage.local.set({
            "wp.ext.config": currentConfig,
            "wp.ext.prefs.v1": payload,
          });
        }

        // 2. Save persistently to localStorage for single source of truth
        try {
          localStorage.setItem("wp.ext.prefs.v1", JSON.stringify(payload));
          localStorage.setItem("wp.prefs.v1", JSON.stringify(payload));
          localStorage.setItem(
            "primazi_user_profile",
            JSON.stringify({
              needs_notes: currentFreeText,
              reading_level: currentPrefs.reading_level || "simple",
              format: currentPrefs.format || "steps",
              updated_at: new Date().toISOString(),
            }),
          );
        } catch (_) {}

        showToast(
          "✓ Toate preferințele au fost salvate cu succes! Se revine la pagina de lucru...",
        );

        try {
          if (typeof chrome !== "undefined" && chrome.runtime) {
            chrome.runtime.sendMessage({
              type: "PREFS_SET",
              prefs: payload,
            });
          }
        } catch (_) {}

        // 3. Smoothly close the settings tab to return seamlessly to previous tab
        setTimeout(() => {
          if (
            typeof chrome !== "undefined" &&
            chrome.tabs &&
            chrome.tabs.getCurrent
          ) {
            chrome.tabs.getCurrent((tab) => {
              if (tab && tab.id) {
                chrome.tabs.remove(tab.id);
              } else {
                window.close();
              }
            });
          } else {
            window.close();
          }
        }, 450);
      } catch (err) {
        console.error("Save error:", err);
        showToast("❌ Eroare la salvarea setărilor în memorie.");
      }
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
          localOnly: currentConfig.localOnly,
        },
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      });
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
      reader.onload = async (event) => {
        try {
          const parsed = JSON.parse(event.target.result);
          if (parsed.answers)
            currentAnswers = { ...DEFAULT_ANSWERS, ...parsed.answers };
          if (parsed.prefs) currentPrefs = parsed.prefs;
          if (parsed.freeText) currentFreeText = parsed.freeText;
          if (parsed.config)
            currentConfig = { ...currentConfig, ...parsed.config };

          renderQuestions();
          if (freeTextInput) freeTextInput.value = currentFreeText;
          updateCharCount(currentFreeText);
          updateLivePreview();

          // Auto-persist imported configuration
          const payload = {
            version: 1,
            source: "imported",
            updatedAt: new Date().toISOString(),
            answers: currentAnswers,
            prefs: currentPrefs,
            freeText: currentFreeText,
          };

          if (
            typeof chrome !== "undefined" &&
            chrome.storage &&
            chrome.storage.local
          ) {
            await chrome.storage.local.set({
              "wp.ext.config": currentConfig,
              "wp.ext.prefs.v1": payload,
            });
          }

          try {
            localStorage.setItem("wp.ext.prefs.v1", JSON.stringify(payload));
            localStorage.setItem(
              "primazi_user_profile",
              JSON.stringify({
                needs_notes: currentFreeText,
                updated_at: new Date().toISOString(),
              }),
            );
          } catch (_) {}

          showToast("✓ Setările au fost importate și salvate cu succes!");
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
    resetBtn.addEventListener("click", async () => {
      if (
        confirm(
          "Sigur dorești să resetezi toate preferințele la setările inițiale?",
        )
      ) {
        currentAnswers = { ...DEFAULT_ANSWERS };
        currentPrefs = derivePrefs(currentAnswers);
        currentFreeText = "";
        currentConfig = { ...DEFAULT_CONFIG };

        const payload = {
          version: 1,
          source: "default",
          updatedAt: new Date().toISOString(),
          answers: currentAnswers,
          prefs: currentPrefs,
          freeText: "",
        };

        if (
          typeof chrome !== "undefined" &&
          chrome.storage &&
          chrome.storage.local
        ) {
          await chrome.storage.local.set({
            "wp.ext.config": currentConfig,
            "wp.ext.prefs.v1": payload,
          });
        }

        try {
          localStorage.removeItem("wp.ext.prefs.v1");
          localStorage.removeItem("wp.prefs.v1");
          localStorage.removeItem("primazi_user_profile");
        } catch (_) {}

        renderQuestions();
        if (freeTextInput) freeTextInput.value = "";
        updateCharCount("");
        updateLivePreview();
        showToast("Setările au fost resetate la valorile implicite.");
      }
    });
  }
}
