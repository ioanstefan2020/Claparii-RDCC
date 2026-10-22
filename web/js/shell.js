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
 */

import { pauseSpeaking, resumeSpeaking, stopSpeaking, isSpeaking, isPaused } from "../shared/speech.js";

const STORAGE_KEY = "wp.prefs.v1";

function readPrefs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: 1, prefs: { sidebar: "open" } };
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : { version: 1, prefs: { sidebar: "open" } };
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

document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const menuToggle = document.getElementById("btn-menu-toggle");
  const sidebarCollapseButtons = document.querySelectorAll("#btn-sidebar-collapse, .btn-sidebar-toggle");
  const sidebar = document.getElementById("app-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const liveRegion = document.getElementById("status-live");

  function announce(msg) {
    if (liveRegion) {
      liveRegion.textContent = "";
      setTimeout(() => { liveRegion.textContent = msg; }, 50);
    }
  }

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
    const isCurrentlyCollapsed = root.getAttribute("data-sidebar") === "collapsed";
    const nextState = isCurrentlyCollapsed ? "open" : "collapsed";
    root.setAttribute("data-sidebar", nextState);
    sidebarCollapseButtons.forEach(btn => {
      btn.setAttribute("aria-expanded", nextState === "open" ? "true" : "false");
    });
    if (menuToggle) menuToggle.setAttribute("aria-expanded", nextState === "open" ? "true" : "false");
    updatePref("sidebar", nextState);
    announce(nextState === "collapsed" ? "Bara laterală a fost restrânsă." : "Bara laterală a fost extinsă.");
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
  sidebarCollapseButtons.forEach(btn => {
    btn.addEventListener("click", toggleSidebarCollapse);
  });

  // 3. Persistent Accessibility Header Toolbar Wiring
  const btnContrast = document.getElementById("btn-header-contrast");
  const btnText = document.getElementById("btn-header-text");
  const btnAudio = document.getElementById("btn-header-audio");
  const btnDyslexia = document.getElementById("btn-header-dyslexia");

  // Contrast mode cycle: Soft/Natural -> Dark -> High-Contrast Light -> Soft/Natural
  if (btnContrast) {
    btnContrast.addEventListener("click", () => {
      const currentTheme = root.getAttribute("data-theme") || "light";
      let nextTheme = "light";
      let nextContrast = "normal";
      let label = "Contrast: Cald";

      if (currentTheme === "light" || currentTheme === "system") {
        nextTheme = "dark";
        nextContrast = "high-dark";
        label = "Contrast: Întunecat";
      } else if (currentTheme === "dark") {
        nextTheme = "high-contrast-light";
        nextContrast = "high-light";
        label = "Contrast: Luminos";
      } else {
        nextTheme = "light";
        nextContrast = "normal";
        label = "Contrast: Cald";
      }

      root.setAttribute("data-theme", nextTheme);
      root.setAttribute("data-contrast", nextContrast);
      const span = btnContrast.querySelector("span");
      if (span) span.textContent = label;
      updatePref("theme", nextTheme);
      updatePref("contrast", nextContrast);
      announce(`Tema a fost schimbată la ${label}.`);
    });
  }

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
      announce(`Dimensiunea textului a fost setată la ${label}.`);
    });
  }

  // Audio control: Pause / Resume / Stop via speech.js
  if (btnAudio) {
    btnAudio.addEventListener("click", () => {
      if (isSpeaking()) {
        if (isPaused()) {
          resumeSpeaking();
          const span = btnAudio.querySelector("span");
          if (span) span.textContent = "Audio: Pauză";
          announce("Redarea audio a continuat.");
        } else {
          pauseSpeaking();
          const span = btnAudio.querySelector("span");
          if (span) span.textContent = "Audio: Continuă";
          announce("Redarea audio a fost pusă pe pauză.");
        }
      } else {
        stopSpeaking();
        announce("Niciun text în redare. Apasă pe «Ascultă» la orice secțiune pentru a porni lectura.");
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
      announce(isDyslexic ? "Fontul pentru dislexie a fost dezactivat." : "Fontul pentru dislexie a fost activat.");
    });
  }
});
