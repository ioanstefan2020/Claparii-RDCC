/**
 * blind-mode.js - Blind Mode & Pitch Black Screen Curtain Controller
 * Project: Limpede (Hackathon 2026)
 *
 * Features:
 * - Hotkey F9 or Alt+B toggles pitch black screen curtain (#blind-curtain)
 * - Underneath, the entire site stays 100% interactive and focusable
 * - Automatically reads aloud focused elements in natural Romanian on Tab/Arrow/Touch
 * - Tactile swipe navigation for mobile phones
 * - Emergency exit with F9 or Escape
 * - Live announcements and state persistence
 */

import { voiceEngine } from "./voice-engine.js";

const STORAGE_KEY = "limpede_blind_mode";
let isBlindActive = false;
let curtainEl = null;

/**
 * Creates or retrieves the pitch-black curtain element.
 */
function getOrCreateCurtain() {
  if (typeof document === "undefined") return null;
  let curtain = document.getElementById("blind-curtain");
  if (!curtain) {
    curtain = document.createElement("div");
    curtain.id = "blind-curtain";
    curtain.setAttribute("aria-hidden", "true");
    curtain.className = "blind-curtain";
    document.body.appendChild(curtain);
  }
  return curtain;
}

/**
 * Checks if blind mode is currently active.
 * @returns {boolean}
 */
export function isBlindModeActive() {
  return isBlindActive;
}

/**
 * Toggles Blind Mode on or off.
 * @param {boolean} [forceState]
 */
export function toggleBlindMode(forceState) {
  if (typeof document === "undefined") return isBlindActive;

  const nextState = typeof forceState === "boolean" ? forceState : !isBlindActive;
  isBlindActive = nextState;

  const curtain = getOrCreateCurtain();
  const root = document.documentElement;

  if (isBlindActive) {
    if (curtain) curtain.classList.add("is-active");
    root.setAttribute("data-blind-mode", "active");

    try {
      localStorage.setItem(STORAGE_KEY, "true");
    } catch (_) {}

    // Announce activation
    voiceEngine.speak(
      "Modul ecran negru activat. Navigați folosind tasta Tab. Apăsați tasta F9 pentru a reveni la afișajul vizual."
    );

    // Announce to aria-live region if present
    announceLive("Modul ecran negru activat. Toate elementele sunt citite vocal.");

    // Update any UI toggle buttons
    updateToggleButtons(true);

    // Speak initial active element after brief pause
    setTimeout(() => {
      const active = document.activeElement;
      if (active && active !== document.body) {
        voiceEngine.speakElement(active);
      }
    }, 400);
  } else {
    if (curtain) curtain.classList.remove("is-active");
    root.removeAttribute("data-blind-mode");

    try {
      localStorage.setItem(STORAGE_KEY, "false");
    } catch (_) {}

    voiceEngine.speak("Modul ecran negru dezactivat.");
    announceLive("Modul ecran negru dezactivat.");
    updateToggleButtons(false);
  }

  // Dispatch custom event for telemetry or page sync
  window.dispatchEvent(new CustomEvent("limpede:blind-mode-changed", { detail: { active: isBlindActive } }));

  return isBlindActive;
}

function updateToggleButtons(active) {
  const btns = document.querySelectorAll("#btn-header-blind, .btn-blind-toggle, [data-action='toggle-blind']");
  btns.forEach(btn => {
    btn.setAttribute("aria-pressed", active ? "true" : "false");
    btn.classList.toggle("is-active", active);
    const label = active ? "Mod Orb: Activat (F9)" : "Mod Orb (F9)";
    const span = btn.querySelector("span");
    if (span) span.textContent = label;
  });
}

function announceLive(msg) {
  if (typeof document === "undefined") return;
  const live = document.getElementById("status-live");
  if (live) {
    live.textContent = "";
    setTimeout(() => {
      live.textContent = msg;
    }, 50);
  }
}

/**
 * Sets up global listeners for Tab/Shift+Tab focus reading and hotkeys.
 */
export function initBlindMode() {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  // Restore stored state if previously enabled
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "true") {
      toggleBlindMode(true);
    }
  } catch (_) {}

  // 1. Hotkey listeners: F9 or Alt+B
  window.addEventListener("keydown", (e) => {
    // F9 toggle
    if (e.key === "F9") {
      e.preventDefault();
      toggleBlindMode();
      return;
    }

    // Alt+B toggle (laptop fallback)
    if (e.altKey && (e.key === "b" || e.key === "B" || e.key === "â" || e.key === "Â")) {
      e.preventDefault();
      toggleBlindMode();
      return;
    }

    // Escape halts speech
    if (e.key === "Escape" && isBlindActive) {
      voiceEngine.stop();
    }
  });

  // 2. Focusin listener: reads elements aloud when blind mode is active
  document.addEventListener("focusin", (e) => {
    if (!isBlindActive) return;
    const target = e.target;
    if (!target || target === document.body || target === document.documentElement) return;

    voiceEngine.speakElement(target);
  });

  // 3. Mobile touch gesture support
  setupTouchNavigation();

  // 4. Bind any existing toggle buttons
  updateToggleButtons(isBlindActive);
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("#btn-header-blind, .btn-blind-toggle, [data-action='toggle-blind']");
    if (btn) {
      e.preventDefault();
      toggleBlindMode();
    }
  });
}

/**
 * Enables swipe left/right to move focus between interactive elements on mobile.
 */
function setupTouchNavigation() {
  if (typeof window === "undefined") return;

  let touchStartX = 0;
  let touchStartY = 0;

  window.addEventListener(
    "touchstart",
    (e) => {
      if (!isBlindActive || !e.touches || e.touches.length !== 1) return;
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    },
    { passive: true }
  );

  window.addEventListener(
    "touchend",
    (e) => {
      if (!isBlindActive || !e.changedTouches || e.changedTouches.length !== 1) return;
      const dx = e.changedTouches[0].clientX - touchStartX;
      const dy = e.changedTouches[0].clientY - touchStartY;

      // Horizontal swipe threshold: 50px, mostly horizontal
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        moveFocus(dx > 0 ? 1 : -1);
      }
    },
    { passive: true }
  );
}

/**
 * Moves focus to the next or previous interactive element.
 * @param {number} direction 1 for next, -1 for previous
 */
function moveFocus(direction) {
  const focusables = Array.from(
    document.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )
  ).filter((el) => el.offsetParent !== null || isBlindActive);

  if (focusables.length === 0) return;

  const currentIdx = focusables.indexOf(document.activeElement);
  let nextIdx = currentIdx + direction;

  if (nextIdx < 0) nextIdx = focusables.length - 1;
  if (nextIdx >= focusables.length) nextIdx = 0;

  focusables[nextIdx].focus();
}

// Auto-initialize when loaded
if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBlindMode);
  } else {
    initBlindMode();
  }
}

// Export to global scope
if (typeof window !== "undefined") {
  window.LimpedeBlindMode = {
    toggle: toggleBlindMode,
    isActive: isBlindModeActive,
  };
}
