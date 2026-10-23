/**
 * blind-mode.js - Blind Mode & Romanian Voiceover / Screen Reader Controller
 * Project: Limpede (Hackathon 2026)
 *
 * Features:
 * - F9 hotkey: Blind Mode with pitch-black screen curtain (#blind-curtain)
 * - Tactile Mobile Controller (#blind-mobile-controller):
 *   3 giant round touch buttons (Anterior ◀, Selectează ✔, Următor ▶) with haptics
 * - Direct topbar "🕶️ Mod Orb" button for instant one-tap mobile access
 * - "Audio: Citește" button: Assisted Voiceover Mode WITHOUT black screen
 *   (for low-vision users navigating with mouse or keyboard)
 * - Speaks element role, accessible label, and content in Romanian on:
 *   - Keyboard focus (Tab, Shift+Tab, Arrows)
 *   - Mouse hover & mouse click (with responsive debounce)
 *   - Tactile mobile controller buttons & touch swipes
 * - Emergency exit: F9 or Escape stops speech immediately
 * - Full state synchronization with header toolbar buttons
 */

import { voiceEngine } from "./voice-engine.js";
import { formatElementAnnouncementRo } from "./voiceover-core.js";

const BLIND_STORAGE_KEY = "limpede_blind_mode";
const VOICEOVER_STORAGE_KEY = "limpede_voiceover_active";

let isBlindActive = false;
let _voiceoverState = false;
let curtainEl = null;
let controllerEl = null;
let hoverTimer = null;
let lastHoveredTarget = null;
let lastSelectedFocusTarget = null;

function triggerHaptic(pattern = 35) {
  if (
    typeof navigator !== "undefined" &&
    typeof navigator.vibrate === "function"
  ) {
    try {
      navigator.vibrate(pattern);
    } catch (_) {}
  }
}

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
 * Creates or retrieves the giant tactile mobile controller.
 */
function getOrCreateMobileController() {
  if (typeof document === "undefined") return null;
  let ctrl = document.getElementById("blind-mobile-controller");
  if (!ctrl) {
    ctrl = document.createElement("nav");
    ctrl.id = "blind-mobile-controller";
    ctrl.className = "blind-mobile-controller";
    ctrl.setAttribute("aria-label", "Control tactil pentru nevăzători");

    ctrl.innerHTML = `
      <div class="blind-controller-top">
        <button type="button" class="btn-controller-exit" id="btn-controller-exit" aria-label="Ieși din Modul Ecran Negru (F9)">
          <span aria-hidden="true">✕</span> Ieși din Mod Orb
        </button>
        <span class="blind-controller-hint" id="blind-controller-hint" aria-live="polite">Comenzi tactile cu vibrație</span>
      </div>
      <div class="blind-controller-buttons">
        <button type="button" class="btn-tactile btn-tactile-prev" id="btn-tactile-prev" aria-label="Elementul anterior (Shift + Tab)">
          <svg class="tactile-icon" viewBox="0 0 24 24" width="32" height="32" aria-hidden="true">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
          <span class="tactile-label">Anterior</span>
        </button>

        <button type="button" class="btn-tactile btn-tactile-select" id="btn-tactile-select" aria-label="Selectează sau apasă elementul curent (Enter)">
          <svg class="tactile-icon" viewBox="0 0 24 24" width="36" height="36" aria-hidden="true">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span class="tactile-label">Selectează</span>
        </button>

        <button type="button" class="btn-tactile btn-tactile-next" id="btn-tactile-next" aria-label="Elementul următor (Tab)">
          <svg class="tactile-icon" viewBox="0 0 24 24" width="32" height="32" aria-hidden="true">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
          <span class="tactile-label">Următor</span>
        </button>
      </div>
    `;
    document.body.appendChild(ctrl);
  }
  return ctrl;
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

    setTimeout(() => {
      const active = document.activeElement;
      if (
        active &&
        active !== document.body &&
        active !== document.documentElement
      ) {
        lastSelectedFocusTarget = active;
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
      detail: { active: isVoiceoverActive() },
    }),
  );

  return isVoiceoverActive();
}

/**
 * Toggles Full Blind Mode (Pitch-black curtain + voiceover + mobile tactile controller).
 * @param {boolean} [forceState]
 */
export function toggleBlindMode(forceState) {
  if (typeof document === "undefined") return isBlindActive;

  const nextState =
    typeof forceState === "boolean" ? forceState : !isBlindActive;
  isBlindActive = nextState;

  const curtain = getOrCreateCurtain();
  const ctrl = getOrCreateMobileController();
  const root = document.documentElement;

  if (isBlindActive) {
    if (curtain) curtain.classList.add("is-active");
    if (ctrl) ctrl.classList.add("is-active");
    root.setAttribute("data-blind-mode", "active");
    _voiceoverState = true;

    try {
      localStorage.setItem(BLIND_STORAGE_KEY, "true");
    } catch (_) {}

    voiceEngine.speak(
      "Modul ecran negru activat. Navigați folosind butoanele tactile de jos sau tasta Tab. Apăsați F9 pentru a reveni.",
    );

    announceLive(
      "Modul ecran negru activat. Toate elementele sunt citite vocal.",
    );
    updateBlindButtons(true);
    updateVoiceoverButtons(true);

    // Initial focus on first interactive element
    setTimeout(() => {
      const focusables = getFocusableElements();
      if (focusables.length > 0) {
        lastSelectedFocusTarget = focusables[0];
        try {
          focusables[0].focus();
        } catch (_) {}
        voiceEngine.speakElement(focusables[0]);
      }
    }, 400);
  } else {
    if (curtain) curtain.classList.remove("is-active");
    if (ctrl) ctrl.classList.remove("is-active");
    root.removeAttribute("data-blind-mode");

    try {
      localStorage.setItem(BLIND_STORAGE_KEY, "false");
    } catch (_) {}

    voiceEngine.speak("Modul ecran negru dezactivat.");
    announceLive("Modul ecran negru dezactivat.");
    updateBlindButtons(false);

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
    "#btn-header-blind, #btn-topbar-blind-mobile, .btn-blind-toggle, [data-action='toggle-blind']",
  );
  btns.forEach((btn) => {
    btn.setAttribute("aria-pressed", active ? "true" : "false");
    btn.classList.toggle("is-active", active);
    const label = active ? "Mod Orb: Activ" : "Mod Orb (F9)";
    const span =
      btn.querySelector("span:not([aria-hidden])") || btn.querySelector("span");
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
 * Returns meaningful focusable elements, excluding the controller itself.
 */
function getFocusableElements() {
  if (typeof document === "undefined") return [];
  return Array.from(
    document.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((el) => {
    if (el.closest("#blind-mobile-controller")) return false;
    if (el.closest("[aria-hidden='true']") && el.id !== "blind-curtain")
      return false;
    if (el.id === "btn-controller-exit") return false;
    return true;
  });
}

/**
 * Moves focus forward (+1) or backward (-1) and reads the target immediately.
 */
function moveFocus(direction) {
  const focusables = getFocusableElements();
  if (!focusables.length) return;

  let currentIdx = focusables.indexOf(
    lastSelectedFocusTarget || document.activeElement,
  );
  let nextIdx = currentIdx + direction;

  if (nextIdx < 0) nextIdx = focusables.length - 1;
  if (nextIdx >= focusables.length) nextIdx = 0;

  const target = focusables[nextIdx];
  lastSelectedFocusTarget = target;

  try {
    target.focus({ preventScroll: false });
  } catch (_) {}

  voiceEngine.speakElement(target);
  triggerHaptic(35);
}

/**
 * Activates or clicks the currently selected focus element.
 */
function activateSelectedElement() {
  triggerHaptic([40, 30, 60]);
  const focusables = getFocusableElements();
  const target = lastSelectedFocusTarget || document.activeElement;

  if (
    !target ||
    target === document.body ||
    target.closest("#blind-mobile-controller")
  ) {
    if (focusables.length > 0) {
      lastSelectedFocusTarget = focusables[0];
      focusables[0].focus();
      voiceEngine.speakElement(focusables[0]);
    }
    return;
  }

  const roleText = formatElementAnnouncementRo(target);
  voiceEngine.speak("Apasă: " + roleText);

  setTimeout(() => {
    try {
      target.click();
    } catch (_) {}
  }, 120);
}

/**
 * Injects a direct "Mod Orb" button in the mobile topbar for quick one-tap activation.
 */
function ensureMobileTopbarButton() {
  if (typeof document === "undefined") return;
  const topbarRight = document.querySelector(".topbar-right");
  if (topbarRight && !document.getElementById("btn-topbar-blind-mobile")) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.id = "btn-topbar-blind-mobile";
    btn.className = "btn-topbar-blind-mobile";
    btn.setAttribute("aria-label", "Comută Modul Ecran Negru (Tasta F9)");
    btn.setAttribute("aria-pressed", isBlindActive ? "true" : "false");
    btn.innerHTML = `<span aria-hidden="true">🕶️</span> <span>${isBlindActive ? "Activ" : "Mod Orb"}</span>`;
    topbarRight.insertBefore(btn, topbarRight.firstChild);
  }
}

/**
 * Initializes global event listeners for Voiceover, Blind Mode, Controller, and Hotkeys.
 */
export function initBlindMode() {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  // Mount mobile topbar button
  ensureMobileTopbarButton();

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
      triggerHaptic(40);
      toggleBlindMode();
      return;
    }

    // Alt+B toggle (laptop fallback)
    if (
      e.altKey &&
      (e.key === "b" || e.key === "B" || e.key === "â" || e.key === "Â")
    ) {
      e.preventDefault();
      triggerHaptic(40);
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
    if (
      target.closest("#blind-mobile-controller") ||
      target.id === "blind-curtain"
    )
      return;

    lastSelectedFocusTarget = target;
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
      if (
        target.closest("#blind-mobile-controller") ||
        target.id === "blind-curtain"
      )
        return;

      const readable =
        target.closest(
          'button, a, input, textarea, select, h1, h2, h3, h4, h5, h6, [role="button"], [role="link"], [role="checkbox"], [role="tab"], p, li, label, .gemini-action-chip, .file-action-pill, .step-item, .card-summary, .task-card, .memory-memento-card',
        ) || target;

      if (readable === lastHoveredTarget) return;
      lastHoveredTarget = readable;

      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => {
        if (isVoiceoverActive() && readable) {
          lastSelectedFocusTarget = readable;
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
          "#btn-header-audio, #btn-header-blind, #btn-topbar-blind-mobile, .btn-blind-toggle, #blind-mobile-controller",
        )
      ) {
        return;
      }

      const readable =
        target.closest(
          'button, a, input, textarea, select, h1, h2, h3, h4, h5, h6, [role="button"], [role="link"], [role="checkbox"], [role="tab"], p, li, label, .gemini-action-chip, .file-action-pill, .step-item, .card-summary, .task-card, .memory-memento-card',
        ) || target;

      if (readable && readable !== document.body) {
        lastSelectedFocusTarget = readable;
        voiceEngine.speakElement(readable);
      }
    },
    { passive: true },
  );

  // 5. Mobile Touch swipe navigation support
  setupTouchNavigation();

  // 6. Centralized Click Delegation (SINGLE handler to prevent double-toggle bugs!)
  document.addEventListener("click", (e) => {
    // Tactile controller previous
    const prevBtn = e.target.closest("#btn-tactile-prev");
    if (prevBtn) {
      e.preventDefault();
      e.stopPropagation();
      moveFocus(-1);
      return;
    }

    // Tactile controller next
    const nextBtn = e.target.closest("#btn-tactile-next");
    if (nextBtn) {
      e.preventDefault();
      e.stopPropagation();
      moveFocus(1);
      return;
    }

    // Tactile controller select
    const selectBtn = e.target.closest("#btn-tactile-select");
    if (selectBtn) {
      e.preventDefault();
      e.stopPropagation();
      activateSelectedElement();
      return;
    }

    // Controller exit
    const exitBtn = e.target.closest("#btn-controller-exit");
    if (exitBtn) {
      e.preventDefault();
      e.stopPropagation();
      triggerHaptic(50);
      toggleBlindMode(false);
      return;
    }

    // Blind mode toggle buttons (Desktop toolbar + Mobile topbar)
    const blindBtn = e.target.closest(
      "#btn-header-blind, #btn-topbar-blind-mobile, .btn-blind-toggle, [data-action='toggle-blind']",
    );
    if (blindBtn) {
      e.preventDefault();
      e.stopPropagation();
      triggerHaptic(40);
      toggleBlindMode();
      return;
    }

    // Voiceover toggle buttons (Desktop audio button)
    const audioBtn = e.target.closest(
      "#btn-header-audio, .btn-audio-toggle, [data-action='toggle-voiceover']",
    );
    if (audioBtn) {
      e.preventDefault();
      e.stopPropagation();
      triggerHaptic(30);
      toggleVoiceover();
    }
  });

  // Initial UI button sync
  updateBlindButtons(isBlindActive);
  updateVoiceoverButtons(isVoiceoverActive());
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
        (!isBlindActive && !isVoiceoverActive()) ||
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
        (!isBlindActive && !isVoiceoverActive()) ||
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
    moveFocus,
    activate: activateSelectedElement,
  };
  window.LimpedeVoiceover = {
    toggle: toggleVoiceover,
    isActive: isVoiceoverActive,
  };
}
