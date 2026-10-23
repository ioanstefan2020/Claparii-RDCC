/**
 * blind-mode.js - Blind Mode & Romanian Voiceover / Screen Reader Controller
 * Project: Limpede (Hackathon 2026)
 *
 * Features:
 * - F9 hotkey: Blind Mode with pitch-black screen curtain (#blind-curtain)
 * - "Audio: Citește" button: Assisted Voiceover Mode WITHOUT black screen
 *   (ideal for low-vision users navigating with mouse or keyboard)
 * - Speaks element role, accessible label, and content in Romanian on:
 *   - Keyboard focus (Tab, Shift+Tab, Arrows)
 *   - Mouse hover & mouse click (with responsive debounce)
 *   - Mobile touch swipe (left/right)
 * - Emergency exit: F9 or Escape stops speech immediately
 * - Full state synchronization with header toolbar buttons
 */

import { voiceEngine } from "./voice-engine.js";

const BLIND_STORAGE_KEY = "limpede_blind_mode";
const VOICEOVER_STORAGE_KEY = "limpede_voiceover_active";

let isBlindActive = false;
let _voiceoverState = false;
let curtainEl = null;
let hoverTimer = null;
let lastHoveredTarget = null;

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
 * Checks if blind mode (black curtain) is active.
 * @returns {boolean}
 */
export function isBlindModeActive() {
  return isBlindActive;
}

/**
 * Checks if voiceover (screen reader) is active.
 * Always true if blind mode is active.
 * @returns {boolean}
 */
export function isVoiceoverActive() {
  return _voiceoverState || isBlindActive;
}

/**
 * Toggles Assisted Voiceover (Blind mode without black curtain).
 * Screen remains 100% visible, but every element under mouse or keyboard is spoken in Romanian.
 * @param {boolean} [forceState]
 */
export function toggleVoiceover(forceState) {
  if (typeof document === "undefined") return isVoiceoverActive();

  const nextState =
    typeof forceState === "boolean" ? forceState : !_voiceoverState;
  _voiceoverState = nextState;

  const root = document.documentElement;

  if (_voiceoverState) {
    root.setAttribute("data-voiceover", "active");

    try {
      localStorage.setItem(VOICEOVER_STORAGE_KEY, "true");
    } catch (_) {}

    voiceEngine.speak(
      "Citire vocală activată. Treceți cu mouse-ul sau folosiți tasta Tab pentru a asculta elementele.",
    );
    announceLive("Citire vocală activată.");
    updateVoiceoverButtons(true);

    // Speak initial active element if focused
    setTimeout(() => {
      const active = document.activeElement;
      if (
        active &&
        active !== document.body &&
        active !== document.documentElement
      ) {
        voiceEngine.speakElement(active);
      }
    }, 300);
  } else {
    root.removeAttribute("data-voiceover");

    try {
      localStorage.setItem(VOICEOVER_STORAGE_KEY, "false");
    } catch (_) {}

    voiceEngine.stop();
    announceLive("Citire vocală oprită.");
    updateVoiceoverButtons(false);
  }

  window.dispatchEvent(
    new CustomEvent("limpede:voiceover-changed", {
      detail: { active: isVoiceoverActive },
    }),
  );

  return isVoiceoverActive();
}

/**
 * Toggles Full Blind Mode (Pitch-black curtain + voiceover).
 * @param {boolean} [forceState]
 */
export function toggleBlindMode(forceState) {
  if (typeof document === "undefined") return isBlindActive;

  const nextState =
    typeof forceState === "boolean" ? forceState : !isBlindActive;
  isBlindActive = nextState;

  const curtain = getOrCreateCurtain();
  const root = document.documentElement;

  if (isBlindActive) {
    if (curtain) curtain.classList.add("is-active");
    root.setAttribute("data-blind-mode", "active");
    _voiceoverState = true;

    try {
      localStorage.setItem(BLIND_STORAGE_KEY, "true");
    } catch (_) {}

    // Announce activation
    voiceEngine.speak(
      "Modul ecran negru activat. Navigați folosind tasta Tab. Apăsați tasta F9 pentru a reveni la afișajul vizual.",
    );

    announceLive(
      "Modul ecran negru activat. Toate elementele sunt citite vocal.",
    );
    updateBlindButtons(true);
    updateVoiceoverButtons(true);

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
      localStorage.setItem(BLIND_STORAGE_KEY, "false");
    } catch (_) {}

    voiceEngine.speak("Modul ecran negru dezactivat.");
    announceLive("Modul ecran negru dezactivat.");
    updateBlindButtons(false);

    // Restore voiceover button state to saved pref
    const savedVO = localStorage.getItem(VOICEOVER_STORAGE_KEY) === "true";
    _voiceoverState = savedVO;
    updateVoiceoverButtons(savedVO);
  }

  window.dispatchEvent(
    new CustomEvent("limpede:blind-mode-changed", {
      detail: { active: isBlindActive },
    }),
  );

  return isBlindActive;
}

function updateBlindButtons(active) {
  const btns = document.querySelectorAll(
    "#btn-header-blind, .btn-blind-toggle, [data-action='toggle-blind']",
  );
  btns.forEach((btn) => {
    btn.setAttribute("aria-pressed", active ? "true" : "false");
    btn.classList.toggle("is-active", active);
    const label = active ? "Mod Orb: Activat (F9)" : "Mod Orb (F9)";
    const span = btn.querySelector("span");
    if (span) span.textContent = label;
  });
}

function updateVoiceoverButtons(active) {
  const btns = document.querySelectorAll(
    "#btn-header-audio, .btn-audio-toggle, [data-action='toggle-voiceover']",
  );
  btns.forEach((btn) => {
    btn.setAttribute("aria-pressed", active ? "true" : "false");
    btn.classList.toggle("is-active", active);
    const span = btn.querySelector("span");
    if (span) {
      span.textContent = active ? "Audio: Pornit" : "Audio: Citește";
    }
    btn.setAttribute(
      "aria-label",
      active
        ? "Citire vocală asistată activă. Apasă pentru a opri."
        : "Activează citirea vocală asistată a elementelor",
    );
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
 * Initializes global event listeners for Voiceover, Blind Mode, and Hotkeys.
 */
export function initBlindMode() {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  // Restore stored state if previously enabled
  try {
    const savedBlind = localStorage.getItem(BLIND_STORAGE_KEY);
    if (savedBlind === "true") {
      toggleBlindMode(true);
    } else {
      const savedVO = localStorage.getItem(VOICEOVER_STORAGE_KEY);
      if (savedVO === "true") {
        toggleVoiceover(true);
      }
    }
  } catch (_) {}

  // 1. Hotkey listeners: F9 or Alt+B
  window.addEventListener("keydown", (e) => {
    // F9 toggle (Curtain on/off)
    if (e.key === "F9") {
      e.preventDefault();
      toggleBlindMode();
      return;
    }

    // Alt+B toggle (laptop fallback)
    if (
      e.altKey &&
      (e.key === "b" || e.key === "B" || e.key === "â" || e.key === "Â")
    ) {
      e.preventDefault();
      toggleBlindMode();
      return;
    }

    // Escape halts speech immediately
    if (e.key === "Escape" && (isBlindActive || isVoiceoverActive())) {
      voiceEngine.stop();
    }
  });

  // 2. Keyboard Focus listener: reads elements aloud on Tab / Arrow navigation
  document.addEventListener("focusin", (e) => {
    if (!isVoiceoverActive() && !isBlindActive) return;
    const target = e.target;
    if (
      !target ||
      target === document.body ||
      target === document.documentElement
    )
      return;
    if (target.id === "blind-curtain") return;

    voiceEngine.speakElement(target);
  });

  // 3. Mouse Hover listener: reads elements on hover for low-vision users
  document.addEventListener(
    "pointerover",
    (e) => {
      if (!isVoiceoverActive() && !isBlindActive) return;
      const target = e.target;
      if (
        !target ||
        target === document.body ||
        target === document.documentElement
      )
        return;
      if (target.id === "blind-curtain") return;

      const readable =
        target.closest(
          'button, a, input, textarea, select, h1, h2, h3, h4, h5, h6, [role="button"], [role="link"], [role="checkbox"], [role="tab"], p, li, label, .gemini-action-chip, .file-action-pill, .step-item, .card-summary, .task-card, .memory-memento-card',
        ) || target;

      if (readable === lastHoveredTarget) return;
      lastHoveredTarget = readable;

      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => {
        if (isVoiceoverActive() && readable) {
          voiceEngine.speakElement(readable);
        }
      }, 130);
    },
    { passive: true },
  );

  // 4. Mouse Click listener: immediately reads clicked element
  document.addEventListener(
    "click",
    (e) => {
      if (!isVoiceoverActive() && !isBlindActive) return;
      const target = e.target;
      if (!target) return;
      if (
        target.closest(
          "#btn-header-audio, #btn-header-blind, .btn-blind-toggle",
        )
      )
        return;

      const readable =
        target.closest(
          'button, a, input, textarea, select, h1, h2, h3, h4, h5, h6, [role="button"], [role="link"], [role="checkbox"], [role="tab"], p, li, label, .gemini-action-chip, .file-action-pill, .step-item, .card-summary, .task-card, .memory-memento-card',
        ) || target;

      if (readable && readable !== document.body) {
        voiceEngine.speakElement(readable);
      }
    },
    { passive: true },
  );

  // 5. Mobile Touch swipe navigation support
  setupTouchNavigation();

  // 6. Bind UI buttons
  updateBlindButtons(isBlindActive);
  updateVoiceoverButtons(isVoiceoverActive());

  document.addEventListener("click", (e) => {
    const blindBtn = e.target.closest(
      "#btn-header-blind, .btn-blind-toggle, [data-action='toggle-blind']",
    );
    if (blindBtn) {
      e.preventDefault();
      toggleBlindMode();
      return;
    }

    const audioBtn = e.target.closest(
      "#btn-header-audio, .btn-audio-toggle, [data-action='toggle-voiceover']",
    );
    if (audioBtn) {
      e.preventDefault();
      toggleVoiceover();
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
      if (
        (!isBlindActive && !isVoiceoverActive) ||
        !e.touches ||
        e.touches.length !== 1
      )
        return;
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    },
    { passive: true },
  );

  window.addEventListener(
    "touchend",
    (e) => {
      if (
        (!isBlindActive && !isVoiceoverActive) ||
        !e.changedTouches ||
        e.changedTouches.length !== 1
      )
        return;
      const dx = e.changedTouches[0].clientX - touchStartX;
      const dy = e.changedTouches[0].clientY - touchStartY;

      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        moveFocus(dx > 0 ? 1 : -1);
      }
    },
    { passive: true },
  );
}

function moveFocus(direction) {
  const focusables = Array.from(
    document.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((el) => el.offsetParent !== null || isBlindActive);

  if (focusables.length === 0) return;

  const currentIdx = focusables.indexOf(document.activeElement);
  let nextIdx = currentIdx + direction;

  if (nextIdx < 0) nextIdx = focusables.length - 1;
  if (nextIdx >= focusables.length) nextIdx = 0;

  focusables[nextIdx].focus();
}

// Auto-initialize when DOM is ready
if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBlindMode);
  } else {
    initBlindMode();
  }
}

// Global window exposure
if (typeof window !== "undefined") {
  window.LimpedeBlindMode = {
    toggle: toggleBlindMode,
    isActive: isBlindModeActive,
  };
  window.LimpedeVoiceover = {
    toggle: toggleVoiceover,
    isActive: isVoiceoverActive,
  };
}
