/**
 * shell.js - Accessible App Shell Interactive Behavior & Header A11y Toolbar
 * Project: Limpede (formerly PrimaZi) (AccessABILITY Hackathon 2026)
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
 * - Internationalization (i18n) bootstrapping
 * - Dynamic User Profile Name & Avatar Binding
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
import { toggleBlindMode, isBlindModeActive, toggleVoiceover, isVoiceoverActive } from "../a11y/blind-mode.js";

const STORAGE_KEY = "wp.prefs.v1";
const PLANNER_STORAGE_KEY = "primazi_planner_tasks";

// Safe Internationalization Bootstrap
let applyI18n = null;
let getLanguage = () => {
  if (typeof document !== "undefined" && document.documentElement && document.documentElement.lang) {
    return document.documentElement.lang;
  }
  return "ro";
};

(async () => {
  try {
    const i18n = await import("../shared/i18n.js");
    if (i18n) {
      if (typeof i18n.applyI18n === "function") applyI18n = i18n.applyI18n;
      if (typeof i18n.getLanguage === "function") getLanguage = i18n.getLanguage;
      if (typeof document !== "undefined" && document.body && typeof applyI18n === "function") {
        applyI18n(document.body, getLanguage());
      }
      updateUserDisplay();
    }
  } catch (e) {
    // Graceful fallback when i18n is optional or in headless environment
  }
})();

/**
 * Updates all .user-name and .user-avatar-circle elements based on
 * localStorage("limpede_user_name") or default based on language.
 */
export function updateUserDisplay() {
  if (typeof document === "undefined") return;

  let userName = null;
  try {
    userName = localStorage.getItem("limpede_user_name");
  } catch (e) {}

  const currentLang = typeof getLanguage === "function" ? getLanguage() : (document.documentElement.lang || "ro");
  const isEn = String(currentLang).toLowerCase().startsWith("en");

  let displayName = "";
  let avatarChar = "L";

  if (userName && userName.trim()) {
    displayName = userName.trim();
    avatarChar = displayName.charAt(0).toUpperCase() || "L";
  } else {
    displayName = isEn ? "Limpede User" : "Utilizator Limpede";
    avatarChar = "L";
  }

  const nameEls = document.querySelectorAll(".user-name");
  nameEls.forEach((el) => {
    el.textContent = displayName;
  });

  const avatarEls = document.querySelectorAll(".user-avatar-circle");
  avatarEls.forEach((el) => {
    el.textContent = avatarChar;
  });

  const greetingEls = document.querySelectorAll(".gemini-greeting");
  greetingEls.forEach((el) => {
    if (userName && userName.trim()) {
      el.textContent = isEn
        ? `Hello, ${userName.trim()}! Where should we start?`
        : `Bună, ${userName.trim()}! De unde să începem?`;
    } else {
      el.textContent = isEn ? "Where should we start?" : "De unde să începem?";
    }
  });
}

// Storage listener & custom event listener for dynamic user name changes
if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (!e.key || e.key === "limpede_user_name" || e.key === "limpede_lang") {
      updateUserDisplay();
    }
  });

  window.addEventListener("limpede:user-name-changed", () => {
    updateUserDisplay();
  });

  window.addEventListener("limpede:lang-changed", (e) => {
    if (typeof applyI18n === "function" && document.body) {
      applyI18n(document.body, e.detail && e.detail.lang);
    }
    updateUserDisplay();
  });
}

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
          const msg = `Memento Limpede: Ai o sarcină cu termen astăzi: „${task.title}”!`;

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
              new Notification("Limpede: Memento sarcină", {
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

if (typeof document !== "undefined") {
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

  // 0. Apply i18n & User Profile display
  if (typeof applyI18n === "function" && document.body) {
    try {
      applyI18n(document.body, getLanguage());
    } catch (e) {}
  }
  updateUserDisplay();

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

  // Audio control: Screen Reader / Voiceover Mode Toggle (Blind mode without black curtain)
  if (btnAudio) {
    const span = btnAudio.querySelector("span");
    if (span) span.textContent = isVoiceoverActive() ? "Audio: Pornit" : "Audio: Citește";
    btnAudio.setAttribute("aria-pressed", isVoiceoverActive() ? "true" : "false");

    window.addEventListener("limpede:voiceover-changed", (e) => {
      const active = e.detail && e.detail.active;
      if (span) span.textContent = active ? "Audio: Pornit" : "Audio: Citește";
      btnAudio.setAttribute("aria-pressed", active ? "true" : "false");
      btnAudio.classList.toggle("is-active", Boolean(active));
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

  // 5. Blind Mode (Mod Orb / Ecran Negru F9) Toggle in Header Toolbar
  if (a11yToolbar && !document.getElementById("btn-header-blind")) {
    const btnBlind = document.createElement("button");
    btnBlind.type = "button";
    btnBlind.id = "btn-header-blind";
    btnBlind.className = "a11y-toolbar-btn btn-header-blind";
    btnBlind.setAttribute("aria-pressed", isBlindModeActive() ? "true" : "false");
    btnBlind.setAttribute("aria-label", "Comută modul pentru nevăzători: Ecran negru și citire vocală (Tasta F9)");
    btnBlind.innerHTML = `<span>${isBlindModeActive() ? "Mod Orb: Activat (F9)" : "Mod Orb (F9)"}</span>`;
    btnBlind.addEventListener("click", () => {
      toggleBlindMode();
    });
    a11yToolbar.appendChild(btnBlind);
  }
  });
}

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
