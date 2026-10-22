/**
 * PrimaZi — Reading Ruler / Visual Line-Focus Engine (Wave 2)
 * Renders a subtle horizontal band or guideline that follows the pointer or focus,
 * preventing row skipping for ADHD and dyslexia reading comfort.
 * Ref: docs/SETTINGS-SPEC.md §2, docs/TASKS-WAVE2.md A6
 */

import { getSetting } from "./settings.js";

let rulerEl = null;
let isInitialized = false;

function createRulerDOM() {
  if (rulerEl || typeof document === "undefined") return;
  rulerEl = document.createElement("div");
  rulerEl.id = "a11y-reading-ruler";
  rulerEl.className = "a11y-reading-ruler";
  rulerEl.setAttribute("aria-hidden", "true");
  document.body.appendChild(rulerEl);
}

function handlePointerMove(e) {
  if (!rulerEl) return;
  const y = e.clientY;
  rulerEl.style.top = `${y}px`;
}

function handleFocusChange(e) {
  if (!rulerEl || !e.target) return;
  const rect = e.target.getBoundingClientRect();
  if (rect && rect.top) {
    rulerEl.style.top = `${rect.top + rect.height / 2}px`;
  }
}

export function updateRuler() {
  const mode = getSetting("reading_ruler") || "off";
  if (mode === "off") {
    if (rulerEl) rulerEl.style.display = "none";
    return;
  }

  createRulerDOM();
  if (!rulerEl) return;

  rulerEl.style.display = "block";
  const height = getSetting("ruler_height") || 32;
  const color = getSetting("ruler_color") || "rgba(255, 235, 59, 0.25)";

  if (mode === "line") {
    rulerEl.style.height = "3px";
    rulerEl.style.backgroundColor = "var(--primary, #1e40af)";
    rulerEl.style.boxShadow = "none";
  } else {
    // Band
    rulerEl.style.height = `${height}px`;
    rulerEl.style.backgroundColor = color;
    rulerEl.style.boxShadow = "0 0 12px rgba(0, 0, 0, 0.15)";
  }
}

export function initReadingRuler() {
  if (isInitialized || typeof window === "undefined") return;

  window.addEventListener("pointermove", handlePointerMove, { passive: true });
  document.addEventListener("focusin", handleFocusChange, { passive: true });

  updateRuler();
  isInitialized = true;
}

export function destroyReadingRuler() {
  if (typeof window !== "undefined") {
    window.removeEventListener("pointermove", handlePointerMove);
    document.removeEventListener("focusin", handleFocusChange);
  }
  if (rulerEl && rulerEl.parentNode) {
    rulerEl.parentNode.removeChild(rulerEl);
  }
  rulerEl = null;
  isInitialized = false;
}
