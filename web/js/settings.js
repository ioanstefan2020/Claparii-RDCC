/**
 * Settings & Comfort Page Controller (Task N3.4)
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 * Owner: p3
 * Spec: docs/plan/p3.md & docs/NEXT-STEPS.md (§1, §2)
 *
 * Provides real-time reactive preference management:
 * - Direct two-way binding with wp.prefs.v1 in localStorage
 * - Tracks manual overrides against questionnaire answers
 * - Dual resets: "Re-apply answers" and "Reset all" with alertdialog
 * - Offline JSON backup export & validated import via migrate()
 * - Resilient memory fallback notice in private browsing mode
 */

import { getProfile, saveProfile } from "/shared/profile.js";
import {
  loadPrefs,
  savePrefs,
  applyPrefs,
  resetToAnswers,
  resetAll,
  exportPrefsJson,
  importPrefsJson,
  isUsingMemoryFallback,
  VALID_PREFS,
} from "./prefs/index.js";

const PREF_SELECT_MAP = {
  "pref-theme": "theme",
  "pref-contrast": "contrast",
  "pref-text-size": "textSize",
  "pref-spacing": "spacing",
  "pref-font": "font",
  "pref-motion": "motion",
  "pref-density": "density",
  "pref-language": "language",
  "pref-sidebar": "sidebar",
};

const THEME_LABELS = {
  system: "Temă: Sistem",
  light: "Temă: Luminos",
  dark: "Temă: Întunecat",
};

const CONTRAST_LABELS = {
  normal: "Contrast: Normal",
  high: "Contrast: Ridicat (AAA)",
};

const TEXT_LABELS = {
  m: "Text: Mediu (18px)",
  l: "Text: Mare (20px)",
  xl: "Text: Foarte mare (22px)",
};

const SPACING_LABELS = {
  comfortable: "Spațiere: Confortabil",
  roomy: "Spațiere: Generos",
};

let currentState = null;
let toastTimeout = null;

function announce(text) {
  const live = document.getElementById("status-live");
  if (live) {
    live.textContent = "";
    setTimeout(() => {
      live.textContent = text;
    }, 50);
  }
}

function showToast(message, isError = false) {
  const toast = document.getElementById("status-toast");
  if (!toast) return;

  if (toastTimeout) {
    clearTimeout(toastTimeout);
  }

  toast.textContent = message;
  toast.className = `status-toast ${isError ? "is-error" : "is-success"}`;
  toast.style.display = "block";

  toastTimeout = setTimeout(() => {
    toast.style.display = "none";
  }, 4000);
}

function updatePreview(state) {
  const overridesBadge = document.getElementById("preview-overrides-badge");
  if (overridesBadge) {
    const overrides = Array.isArray(state.overrides) ? state.overrides : [];
    const count = overrides.length;
    if (count === 0) {
      overridesBadge.textContent = "Toate setările provin din chestionar";
      overridesBadge.className = "badge-status badge-status-synced";
    } else {
      const label = count === 1 ? "1 setare personalizată manual" : `${count} setări personalizate manual`;
      overridesBadge.textContent = label;
      overridesBadge.className = "badge-status badge-status-override";
    }
  }

  const p = state.prefs || {};
  const bTheme = document.getElementById("badge-theme");
  if (bTheme) bTheme.textContent = THEME_LABELS[p.theme] || `Temă: ${p.theme}`;

  const bContrast = document.getElementById("badge-contrast");
  if (bContrast) bContrast.textContent = CONTRAST_LABELS[p.contrast] || `Contrast: ${p.contrast}`;

  const bText = document.getElementById("badge-text");
  if (bText) bText.textContent = TEXT_LABELS[p.textSize] || `Text: ${p.textSize}`;

  const bSpacing = document.getElementById("badge-spacing");
  if (bSpacing) bSpacing.textContent = SPACING_LABELS[p.spacing] || `Spațiere: ${p.spacing}`;
}

function populateForm(state) {
  const prefs = state.prefs || {};
  for (const [id, key] of Object.entries(PREF_SELECT_MAP)) {
    const el = document.getElementById(id);
    if (el && prefs[key]) {
      el.value = prefs[key];
    }
  }
  const freeformNeeds = document.getElementById("pref-freeform-needs");
  if (freeformNeeds) {
    const prof = getProfile();
    freeformNeeds.value = prof.needs_notes || "";
  }
}

function initSettings() {
  currentState = loadPrefs();

  // 1. Check in-memory private browsing mode fallback
  if (isUsingMemoryFallback()) {
    const memNotice = document.getElementById("memory-fallback-notice");
    if (memNotice) {
      memNotice.style.display = "block";
    }
  }

  // 2. Populate form selects & live preview
  populateForm(currentState);
  updatePreview(currentState);

  // 3. Wire change events on all 9 selects
  for (const [id, key] of Object.entries(PREF_SELECT_MAP)) {
    const el = document.getElementById(id);
    if (!el) continue;

    el.addEventListener("change", (e) => {
      const val = e.target.value;
      if (!VALID_PREFS[key] || !VALID_PREFS[key].includes(val)) return;

      currentState.prefs[key] = val;

      if (!Array.isArray(currentState.overrides)) {
        currentState.overrides = [];
      }
      if (!currentState.overrides.includes(key)) {
        currentState.overrides.push(key);
      }

      currentState = savePrefs(currentState);
      applyPrefs(currentState.prefs, document.documentElement);
      updatePreview(currentState);
      announce(`Setarea a fost actualizată.`);
    });
  }

  // Sync sidebar select if user clicks the sidebar toggle button
  const sidebarBtn = document.getElementById("btn-sidebar-collapse");
  if (sidebarBtn) {
    sidebarBtn.addEventListener("click", () => {
      setTimeout(() => {
        const currentSidebar = document.documentElement.getAttribute("data-sidebar") || "open";
        if (currentState && currentState.prefs) {
          currentState.prefs.sidebar = currentSidebar;
        }
        const selectEl = document.getElementById("pref-sidebar");
        if (selectEl) selectEl.value = currentSidebar;
      }, 50);
    });
  }

  // 4. Wire Reset to Questionnaire Answers button
  const btnResetAnswers = document.getElementById("btn-reset-answers");
  if (btnResetAnswers) {
    btnResetAnswers.addEventListener("click", () => {
      currentState = resetToAnswers(currentState);
      currentState = savePrefs(currentState);
      applyPrefs(currentState.prefs, document.documentElement);
      populateForm(currentState);
      updatePreview(currentState);
      showToast("Răspunsurile din chestionar au fost reaplicate.");
      announce("Setările au fost resincronizate cu răspunsurile din chestionar.");
    });
  }

  // 5. Wire Factory Reset & Confirmation Dialog
  const btnResetAll = document.getElementById("btn-reset-all");
  const confirmBox = document.getElementById("confirm-reset-box");
  const btnCancelReset = document.getElementById("btn-cancel-reset");
  const btnConfirmReset = document.getElementById("btn-confirm-reset");

  if (btnResetAll && confirmBox && btnCancelReset && btnConfirmReset) {
    btnResetAll.addEventListener("click", () => {
      confirmBox.style.display = "block";
      btnCancelReset.focus();
      announce("Atenție: a apărut caseta de confirmare pentru resetare completă.");
    });

    btnCancelReset.addEventListener("click", () => {
      confirmBox.style.display = "none";
      btnResetAll.focus();
      announce("Resetarea a fost anulată.");
    });

    btnConfirmReset.addEventListener("click", () => {
      currentState = resetAll();
      currentState = savePrefs(currentState);
      applyPrefs(currentState.prefs, document.documentElement);
      populateForm(currentState);
      updatePreview(currentState);
      confirmBox.style.display = "none";
      btnResetAll.focus();
      showToast("Toate setările au fost resetate la valorile inițiale.");
      announce("Toate setările au fost resetate la valorile implicite din fabrică.");
    });
  }

  // 6. Wire JSON Export
  const btnExport = document.getElementById("btn-export-json");
  if (btnExport) {
    btnExport.addEventListener("click", () => {
      try {
        const jsonStr = exportPrefsJson();
        const blob = new Blob([jsonStr], { type: "application/json;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "primazi-preferinte.json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast("Fișierul JSON a fost descărcat cu succes.");
        announce("Fișierul JSON cu preferințele tale a fost descărcat.");
      } catch {
        showToast("Eroare la exportul fișierului JSON.", true);
        announce("Eroare la exportul fișierului JSON.");
      }
    });
  }

  // 7. Wire JSON Import
  const btnImportTrigger = document.getElementById("btn-import-json-trigger");
  const inputImport = document.getElementById("input-import-json");

  if (btnImportTrigger && inputImport) {
    btnImportTrigger.addEventListener("click", () => {
      inputImport.click();
    });

    inputImport.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const content = event.target.result;
          currentState = importPrefsJson(content);
          applyPrefs(currentState.prefs, document.documentElement);
          populateForm(currentState);
          updatePreview(currentState);
          showToast("Preferințele au fost importate cu succes.");
          announce("Preferințele au fost importate și aplicate pe ecran.");
        } catch {
          showToast("Fișierul selectat nu este un JSON valid de preferințe.", true);
          announce("Eroare: Fișierul selectat nu este un JSON valid de preferințe.");
        } finally {
          inputImport.value = "";
        }
      };

      reader.onerror = () => {
        showToast("Eroare la citirea fișierului de pe disc.", true);
        inputImport.value = "";
      };

      reader.readAsText(file);
    });
  }

  // 8. Wire AI Auto-Adaptation from Freeform Needs
  const btnAiAuto = document.getElementById("btn-ai-auto-adapt");
  const freeformNeeds = document.getElementById("pref-freeform-needs");
  const aiFeedback = document.getElementById("ai-adapt-feedback");

  if (btnAiAuto && freeformNeeds) {
    btnAiAuto.addEventListener("click", async () => {
      const text = freeformNeeds.value.trim();
      if (!text) {
        showToast("Scrie câteva cuvinte despre nevoile tale înainte de adaptare.", true);
        freeformNeeds.focus();
        return;
      }

      btnAiAuto.disabled = true;
      btnAiAuto.textContent = "Se analizează nevoile...";
      announce("Se calculează adaptările ergonomice optime...");

      try {
        saveProfile({ needs_notes: text });
        const res = await fetch("/api/profile/recommend-adaptations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            freeform_needs: text,
            current_prefs: currentState.prefs
          })
        });
        const json = await res.json();
        if (json.ok && json.data) {
          const ui = json.data.ui_prefs || {};

          // Apply to currentState
          if (ui.theme) currentState.prefs.theme = ui.theme;
          if (ui.textSize) currentState.prefs.textSize = ui.textSize;
          if (ui.font) currentState.prefs.font = ui.font;
          if (ui.contrast && ui.contrast === "high") currentState.prefs.contrast = "high";
          if (ui.spacing) currentState.prefs.spacing = ui.spacing;
          if (typeof ui.bionic !== "undefined") currentState.prefs.bionic = Boolean(ui.bionic);
          if (typeof ui.highlightKeyTerms !== "undefined") currentState.prefs.highlightKeyTerms = Boolean(ui.highlightKeyTerms);

          currentState = savePrefs(currentState);
          applyPrefs(currentState.prefs, document.documentElement);
          populateForm(currentState);
          updatePreview(currentState);

          if (aiFeedback) {
            aiFeedback.textContent = json.data.explanation_ro || "Adaptările au fost aplicate cu succes!";
            aiFeedback.style.display = "block";
          }
          showToast("Adaptările au fost configurate și aplicate!");
          announce("Setările au fost optimizate automat pe baza nevoilor tale.");
        }
      } catch (err) {
        console.error(err);
        showToast("Eroare la recomandarea adaptărilor.", true);
      } finally {
        btnAiAuto.disabled = false;
        btnAiAuto.textContent = "✨ Adaptează site-ul automat din textul meu";
      }
    });
  }
}

if (document.readyState === "loading") {

  document.addEventListener("DOMContentLoaded", initSettings);
} else {
  initSettings();
}

