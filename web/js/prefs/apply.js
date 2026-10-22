/**
 * Preferences Engine: DOM Application & FOUC Prevention (owner: p2).
 * Applies preference tokens as data-* attributes and language tag on the root element.
 * Provides inline <head> script snippet to prevent Flash of Unstyled Content (FOUC).
 */

import { STORAGE_KEY } from "./types.js";

/**
 * Applies preferences to the root DOM element (usually <html>).
 * Sets data-theme, data-text, data-spacing, data-contrast, data-motion,
 * data-font, data-density, data-sidebar, and lang.
 *
 * @param {object} prefs - Preferences dictionary
 * @param {HTMLElement|null} [rootElement=null] - Target root element (default document.documentElement)
 */
export function applyPrefs(prefs, rootElement = null) {
  const root = rootElement || (typeof globalThis.document !== "undefined" ? globalThis.document.documentElement : null);
  if (!root || typeof root.setAttribute !== "function") {
    return;
  }

  if (!prefs || typeof prefs !== "object") {
    return;
  }

  // Defensively support passing either state or state.prefs
  const targetPrefs = (prefs.prefs && typeof prefs.prefs === "object") ? prefs.prefs : prefs;

  const mapping = {
    "data-theme": targetPrefs.theme,
    "data-text": targetPrefs.textSize,
    "data-spacing": targetPrefs.spacing,
    "data-contrast": targetPrefs.contrast,
    "data-motion": targetPrefs.motion,
    "data-font": targetPrefs.font,
    "data-density": targetPrefs.density,
    "data-sidebar": targetPrefs.sidebar,
  };

  for (const [attr, val] of Object.entries(mapping)) {
    if (typeof val === "string" && val.length > 0) {
      root.setAttribute(attr, val);
    }
  }

  if (typeof targetPrefs.language === "string" && targetPrefs.language.length > 0) {
    root.setAttribute("lang", targetPrefs.language);
    if ("lang" in root) {
      try {
        root.lang = targetPrefs.language;
      } catch {
        // Ignore if read-only
      }
    }
  }
}

/**
 * Generates an inline, self-executing JavaScript snippet for the <head> tag.
 * Reads storage and sets data-* attributes immediately before first paint to prevent FOUC.
 *
 * @returns {string} Inline script code (without <script> tags)
 */
export function getInlineHeadScript() {
  return `(function() {
  try {
    var raw = localStorage.getItem("${STORAGE_KEY}");
    if (!raw) return;
    var data = JSON.parse(raw);
    var p = data && data.prefs;
    if (!p) return;
    var doc = document.documentElement;
    if (p.theme) doc.setAttribute("data-theme", p.theme);
    if (p.textSize) doc.setAttribute("data-text", p.textSize);
    if (p.spacing) doc.setAttribute("data-spacing", p.spacing);
    if (p.contrast) doc.setAttribute("data-contrast", p.contrast);
    if (p.motion) doc.setAttribute("data-motion", p.motion);
    if (p.font) doc.setAttribute("data-font", p.font);
    if (p.density) doc.setAttribute("data-density", p.density);
    if (p.sidebar) doc.setAttribute("data-sidebar", p.sidebar);
    if (p.language) {
      doc.setAttribute("lang", p.language);
      doc.lang = p.language;
    }
  } catch (e) {
    // Storage inaccessible or corrupt; silent fallback to default styles
  }
})();`;
}

