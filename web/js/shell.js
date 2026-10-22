/**
 * shell.js - Accessible App Shell Interactive Behavior & Header A11y Toolbar
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 *
 * Handles:
 * - Desktop sidebar collapse/expand with persistence to wp.prefs.v1
 * - Mobile drawer toggle (<768px) with backdrop, Escape key, and focus return
 * - 4-Control Accessibility Header Toolbar:
 *   1. Contrast Mode (Soft Cald -> Întunecat -> Luminos -> Soft Cald)
 *   2. Text Size (Mediu 17px -> Mare 20px -> Foarte mare 23px)
 *   3. Audio Control (Pauză / Continuă / Oprește via speech.js)
 *   4. Dyslexia Switch (OpenDyslexic font toggle)
 * - In-Browser Reminders / Task Deadlines Notification System
 * - Reading Ruler & Saccade Assist Initialization
 */

import {
  speakText,
  pauseSpeaking,
  resumeSpeaking,
  stopSpeaking,
  isSpeaking,
  isPaused,
} from "../shared/speech.js";
import { toggleReadingRuler } from "../shared/a11y-text.js";

const STORAGE_KEY = "wp.prefs.v1";
const PLANNER_STORAGE_KEY = "primazi_planner_tasks";

function readPrefs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: 1, prefs: { sidebar: "open" } };
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object"
      ? parsed
      : { version: 1, prefs: { sidebar: "open" } };
  } catch (err) {
    return { version: 1, prefs: { sidebar: "open" } };
  }
}

function updatePref(key, value) {
  try {
    const state = readPrefs();
    if (!state.prefs) state.prefs = {};
    state.prefs[key] = value;
    if (key !== "sidebar") {
      if (!Array.isArray(state.overrides)) state.overrides = [];
      if (!state.overrides.includes(key)) state.overrides.push(key);
    }
    state.updatedAt = new Date().toISOString();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (err) {
    // Ignore storage errors in private mode
  }
}

/**
 * Periodically checks for pending tasks due today and alerts the user.
 */
function startTaskReminderRunner(announce) {
  let notifiedTaskIds = new Set();

  function checkDeadlines() {
    try {
      const raw = localStorage.getItem(PLANNER_STORAGE_KEY);
      if (!raw) return;
      const tasks = JSON.parse(raw);
      if (!Array.isArray(tasks) || tasks.length === 0) return;

      const todayStr = new Date().toISOString().slice(0, 10);
      const pendingToday = tasks.filter(
        (t) => t && t.due_iso === todayStr && !t.completed,
      );

      pendingToday.forEach((task) => {
        if (!notifiedTaskIds.has(task.id)) {
          notifiedTaskIds.add(task.id);

          const banner =
            document.getElementById("status-banner") ||
            document.getElementById("status-toast");
          const msg = `Memento PrimaZi: Ai o sarcină cu termen astăzi: „${task.title}”!`;

          if (banner) {
            banner.className = "status-message status-warning";
            banner.textContent = msg;
            banner.style.display = "block";
          }
          announce(msg);

          if (
            typeof window !== "undefined" &&
            "Notification" in window &&
            Notification.permission === "granted"
          ) {
            try {
              new Notification("PrimaZi: Memento sarcină", {
                body: `${task.title} are termen astăzi!`,
                icon: "/favicon.ico",
              });
            } catch (e) {
              // Ignore notification errors
            }
          }
        }
      });
    } catch (err) {
      // Ignore check errors
    }
  }

  // Initial check after 3 seconds, then every 60 seconds
  setTimeout(checkDeadlines, 3000);
  setInterval(checkDeadlines, 60000);
}

document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const menuToggle = document.getElementById("btn-menu-toggle");
  const sidebarCollapseButtons = document.querySelectorAll(
    "#btn-sidebar-collapse, .btn-sidebar-toggle",
  );
  const sidebar = document.getElementById("app-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const liveRegion = document.getElementById("status-live");

  function announce(msg) {
    if (liveRegion) {
      liveRegion.textContent = "";
      setTimeout(() => {
        liveRegion.textContent = msg;
      }, 50);
    }
  }

  // Apply stored reading ruler, theme and cognitive attributes
  const currentPrefs = readPrefs().prefs || {};
  if (currentPrefs.theme) {
    root.setAttribute("data-theme", currentPrefs.theme);
  }
  if (currentPrefs.readingRuler) {
    toggleReadingRuler(true);
  }
  if (typeof currentPrefs.bionic !== "undefined") {
    root.setAttribute("data-bionic", currentPrefs.bionic ? "true" : "false");
  }
  if (typeof currentPrefs.highlightKeyTerms !== "undefined") {
    root.setAttribute(
      "data-highlight-terms",
      currentPrefs.highlightKeyTerms ? "true" : "false",
    );
  }

  // Start background task reminders
  startTaskReminderRunner(announce);

  // 1. Mobile Drawer Toggle (<768px)
  function openDrawer() {
    if (!sidebar) return;
    sidebar.classList.add("is-drawer-open");
    if (backdrop) backdrop.classList.add("is-active");
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", "true");
    }
    const firstFocusable = sidebar.querySelector("a, button");
    if (firstFocusable) firstFocusable.focus();
    announce("Meniul de navigare a fost deschis.");
  }

  function closeDrawer() {
    if (!sidebar) return;
    sidebar.classList.remove("is-drawer-open");
    if (backdrop) backdrop.classList.remove("is-active");
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", "false");
      menuToggle.focus();
    }
    announce("Meniul de navigare a fost închis.");
  }

  function toggleSidebarCollapse() {
    if (window.innerWidth <= 768) {
      const isOpen = sidebar && sidebar.classList.contains("is-drawer-open");
      if (isOpen) {
        closeDrawer();
      } else {
        openDrawer();
      }
      return;
    }
    const isCurrentlyCollapsed =
      root.getAttribute("data-sidebar") === "collapsed";
    const nextState = isCurrentlyCollapsed ? "open" : "collapsed";
    root.setAttribute("data-sidebar", nextState);
    sidebarCollapseButtons.forEach((btn) => {
      btn.setAttribute(
        "aria-expanded",
        nextState === "open" ? "true" : "false",
      );
    });
    if (menuToggle)
      menuToggle.setAttribute(
        "aria-expanded",
        nextState === "open" ? "true" : "false",
      );
    updatePref("sidebar", nextState);
    announce(
      nextState === "collapsed"
        ? "Bara laterală a fost restrânsă."
        : "Bara laterală a fost extinsă.",
    );
  }

  if (menuToggle) {
    menuToggle.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        const isOpen = sidebar && sidebar.classList.contains("is-drawer-open");
        if (isOpen) {
          closeDrawer();
        } else {
          openDrawer();
        }
      } else {
        toggleSidebarCollapse();
      }
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeDrawer);
  }

  // Close drawer on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (sidebar && sidebar.classList.contains("is-drawer-open")) {
        closeDrawer();
      }
    }
  });

  // 2. Desktop Sidebar Collapse Toggle
  sidebarCollapseButtons.forEach((btn) => {
    btn.addEventListener("click", toggleSidebarCollapse);
  });

  // 3. Persistent Accessibility Header Toolbar Wiring
  const btnContrast = document.getElementById("btn-header-contrast");
  const btnText = document.getElementById("btn-header-text");
  const btnAudio = document.getElementById("btn-header-audio");
  const btnDyslexia = document.getElementById("btn-header-dyslexia");
  const btnA11yMenu = document.getElementById("btn-header-a11y-menu");
  const a11yToolbar = document.querySelector(".a11y-header-toolbar");

  // Mobile accessibility dropdown menu toggle
  if (btnA11yMenu && a11yToolbar) {
    btnA11yMenu.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = a11yToolbar.classList.toggle("is-dropdown-open");
      btnA11yMenu.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    document.addEventListener("click", (e) => {
      if (!a11yToolbar.contains(e.target) && !btnA11yMenu.contains(e.target)) {
        if (a11yToolbar.classList.contains("is-dropdown-open")) {
          a11yToolbar.classList.remove("is-dropdown-open");
          btnA11yMenu.setAttribute("aria-expanded", "false");
        }
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && a11yToolbar.classList.contains("is-dropdown-open")) {
        a11yToolbar.classList.remove("is-dropdown-open");
        btnA11yMenu.setAttribute("aria-expanded", "false");
        btnA11yMenu.focus();
      }
    });
  }

  // Theme toggle: exactly 2 modes: Luminos (warm default) <-> Întunecat (relaxing navy)
  if (btnContrast) {
    // Initial sync based on active theme
    const activeTheme = currentPrefs.theme || root.getAttribute("data-theme") || "light";
    root.setAttribute("data-theme", activeTheme);
    const initialLabel = activeTheme === "dark" ? "Mod: Întunecat" : "Mod: Luminos";
    const initialSpan = btnContrast.querySelector("span");
    if (initialSpan) initialSpan.textContent = initialLabel;
    btnContrast.setAttribute("aria-label", `Comută tema: ${initialLabel}`);

    btnContrast.addEventListener("click", () => {
      const currentTheme = root.getAttribute("data-theme") || "light";
      const isDark = currentTheme === "dark";
      const nextTheme = isDark ? "light" : "dark";
      const label = isDark ? "Mod: Luminos" : "Mod: Întunecat";

      root.setAttribute("data-theme", nextTheme);
      root.removeAttribute("data-contrast"); // remove high-contrast yellow lines

      const span = btnContrast.querySelector("span");
      if (span) span.textContent = label;
      btnContrast.setAttribute("aria-label", `Comută tema: ${label}`);

      updatePref("theme", nextTheme);
      updatePref("contrast", "normal");
      window.dispatchEvent(new CustomEvent("primazi:pref-changed", { detail: { key: "theme", value: nextTheme } }));
      announce(
        isDark
          ? "Tema luminoasă relaxantă a fost activată."
          : "Tema întunecată pe fond bleumarin a fost activată.",
      );
    });
  }

  // Cross-tab and cross-page synchronization for theme changes
  window.addEventListener("storage", (e) => {
    if (e.key === STORAGE_KEY && e.newValue) {
      try {
        const data = JSON.parse(e.newValue);
        if (data && data.prefs && data.prefs.theme) {
          const t = data.prefs.theme;
          root.setAttribute("data-theme", t);
          if (btnContrast) {
            const lbl = t === "dark" ? "Mod: Întunecat" : "Mod: Luminos";
            const span = btnContrast.querySelector("span");
            if (span) span.textContent = lbl;
            btnContrast.setAttribute("aria-label", `Comută tema: ${lbl}`);
          }
        }
      } catch {}
    }
  });

  // Text size cycle: Normal (m) -> Mare (l) -> Foarte Mare (xl) -> Normal (m)
  if (btnText) {
    btnText.addEventListener("click", () => {
      const currentSize = root.getAttribute("data-text") || "m";
      let nextSize = "m";
      let label = "Text: Mediu";

      if (currentSize === "m") {
        nextSize = "l";
        label = "Text: Mare";
      } else if (currentSize === "l") {
        nextSize = "xl";
        label = "Text: Foarte mare";
      } else {
        nextSize = "m";
        label = "Text: Mediu";
      }

      root.setAttribute("data-text", nextSize);
      const span = btnText.querySelector("span");
      if (span) span.textContent = label;
      updatePref("textSize", nextSize);
      window.dispatchEvent(new CustomEvent("primazi:pref-changed", { detail: { key: "textSize", value: nextSize } }));
      announce(`Dimensiunea textului a fost setată la ${label}.`);
    });
  }

  // Audio control: Smart Read aloud / Pause / Resume / Stop via speech.js
  if (btnAudio) {
    const span = btnAudio.querySelector("span");
    if (span) span.textContent = "Audio: Citește";

    window.addEventListener("primazi:speech-state", (e) => {
      if (!span) return;
      const state = e.detail && e.detail.state;
      if (state === "speaking") {
        span.textContent = "Audio: Pauză";
        btnAudio.setAttribute("aria-label", "Pauză redare audio");
        btnAudio.classList.add("is-speaking");
      } else if (state === "paused") {
        span.textContent = "Audio: Continuă";
        btnAudio.setAttribute("aria-label", "Continuă redarea audio");
        btnAudio.classList.remove("is-speaking");
      } else {
        span.textContent = "Audio: Citește";
        btnAudio.setAttribute("aria-label", "Citește cu voce tare");
        btnAudio.classList.remove("is-speaking");
      }
    });

    btnAudio.addEventListener("click", () => {
      if (isSpeaking()) {
        if (isPaused()) {
          resumeSpeaking();
          if (span) span.textContent = "Audio: Pauză";
          btnAudio.classList.add("is-speaking");
          announce("Redarea audio a continuat.");
          window.dispatchEvent(new CustomEvent("primazi:speech-state", { detail: { state: "speaking" } }));
        } else {
          pauseSpeaking();
          if (span) span.textContent = "Audio: Continuă";
          btnAudio.classList.remove("is-speaking");
          announce("Redarea audio a fost pusă pe pauză.");
          window.dispatchEvent(new CustomEvent("primazi:speech-state", { detail: { state: "paused" } }));
        }
      } else {
        // Find readable content on current page
        let textToRead = "";
        const questionPrompt = document.getElementById("question-prompt");
        const resultBody = document.getElementById("home-result-body");
        const summaryCard = document.querySelector(".summary-card, .results-content, .card-summary, .results-body, .output-card");
        const mainEl = document.getElementById("main");

        if (questionPrompt && questionPrompt.innerText.trim()) {
          const parts = [];
          const stepCounter = document.getElementById("wizard-step-counter");
          if (stepCounter && stepCounter.innerText.trim()) {
            parts.push(stepCounter.innerText.trim());
          }
          parts.push(questionPrompt.innerText.trim());
          const help = document.getElementById("question-help");
          if (help && help.innerText.trim()) {
            parts.push(help.innerText.trim());
          }
          const options = document.querySelectorAll("#question-options .radio-card");
          options.forEach((opt, idx) => {
            const title = opt.querySelector(".radio-title");
            const desc = opt.querySelector(".radio-desc");
            const isSel = opt.classList.contains("is-selected") || Boolean(opt.querySelector("input:checked"));
            const prefix = isSel ? "Opțiunea selectată" : `Opțiunea ${idx + 1}`;
            const tText = title ? title.innerText.trim() : "";
            const dText = desc ? desc.innerText.trim() : "";
            parts.push(`${prefix}: ${tText}. ${dText}`);
          });
          textToRead = parts.join(". ");
        } else if (resultBody && resultBody.offsetParent !== null && resultBody.innerText.trim()) {
          textToRead = resultBody.innerText.trim();
        } else if (summaryCard && summaryCard.innerText.trim()) {
          textToRead = summaryCard.innerText.trim();
        } else if (mainEl) {
          const h1 = mainEl.querySelector("h1");
          const lead = mainEl.querySelector(".hero-lead, .gemini-greeting, p");
          const parts = [];
          if (h1 && h1.innerText) parts.push(h1.innerText.trim());
          if (lead && lead.innerText) parts.push(lead.innerText.trim());
          textToRead = parts.join(". ");
        }

        if (textToRead) {
          speakText(textToRead, {
            onStart: () => {
              if (span) span.textContent = "Audio: Pauză";
              btnAudio.classList.add("is-speaking");
              announce("Lectura audio a pornit.");
              window.dispatchEvent(new CustomEvent("primazi:speech-state", { detail: { state: "speaking" } }));
            },
            onEnd: () => {
              if (span) span.textContent = "Audio: Citește";
              btnAudio.classList.remove("is-speaking");
              announce("Lectura audio s-a încheiat.");
              window.dispatchEvent(new CustomEvent("primazi:speech-state", { detail: { state: "idle" } }));
            },
            onError: (err) => {
              if (span) span.textContent = "Audio: Citește";
              btnAudio.classList.remove("is-speaking");
              announce(typeof err === "string" ? err : "Eroare la redarea audio.");
              window.dispatchEvent(new CustomEvent("primazi:speech-state", { detail: { state: "idle" } }));
            }
          });
        } else {
          announce("Niciun text disponibil pentru citire audio pe această pagină.");
        }
      }
    });
  }

  // Dyslexia mode toggle: default <-> dyslexic
  if (btnDyslexia) {
    btnDyslexia.addEventListener("click", () => {
      const currentFont = root.getAttribute("data-font") || "default";
      const isDyslexic = currentFont === "dyslexic";
      const nextFont = isDyslexic ? "default" : "dyslexic";
      const label = isDyslexic ? "Dislexie: Oprită" : "Dislexie: Activată";

      root.setAttribute("data-font", nextFont);
      const span = btnDyslexia.querySelector("span");
      if (span) span.textContent = label;
      btnDyslexia.setAttribute("aria-pressed", isDyslexic ? "false" : "true");
      updatePref("font", nextFont);
      window.dispatchEvent(new CustomEvent("primazi:pref-changed", { detail: { key: "font", value: nextFont } }));
      announce(
        isDyslexic
          ? "Fontul pentru dislexie a fost dezactivat."
          : "Fontul pentru dislexie a fost activat.",
      );
    });
  }
});

// Global focus mode tracking: eliminate outlines on mouse clicks everywhere, preserve for keyboard
if (typeof document !== "undefined") {
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

