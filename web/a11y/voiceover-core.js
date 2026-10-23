/**
 * voiceover-core.js - Accessible Label Resolution & Romanian Role Formatting
 * Project: Limpede (Hackathon 2026)
 *
 * Pure functions:
 * - Computes accessible name / label according to W3C AccName 1.2
 * - Translates ARIA & HTML roles into natural Romanian voiceover announcements
 * - Formats element state (bifat/debifat, extins/restrâns, activat/dezactivat)
 * - Normalizes numbers and abbreviations for speech via tts-normalize-ro.js
 */

import { normalizeRomanianForSpeech, numberToWordsRo } from "./tts-normalize-ro.js";

const ROLE_NAMES_RO = {
  button: "Buton",
  link: "Link",
  textbox: "Casetă de text",
  checkbox: "Bifă",
  radio: "Opțiune radio",
  combobox: "Listă derulantă",
  listbox: "Listă de opțiuni",
  option: "Opțiune",
  heading: "Antet",
  navigation: "Navigare",
  main: "Conținut principal",
  banner: "Antet pagină",
  contentinfo: "Subsol",
  region: "Secțiune",
  search: "Căutare",
  slider: "Glisor",
  switch: "Comutator",
  tab: "Filă",
  tabpanel: "Panou filă",
  alert: "Avertisment",
  status: "Stare",
  dialog: "Fereastră de dialog",
};

/**
 * Determines the accessible role name in Romanian.
 * @param {HTMLElement} el
 * @returns {{ role: string, level?: number }}
 */
export function getElementRoleRo(el) {
  if (!el || !el.tagName) return { role: "Element" };

  const explicitRole = el.getAttribute("role");
  if (explicitRole && ROLE_NAMES_RO[explicitRole.toLowerCase()]) {
    const res = { role: ROLE_NAMES_RO[explicitRole.toLowerCase()] };
    if (explicitRole.toLowerCase() === "heading") {
      const ariaLevel = parseInt(el.getAttribute("aria-level"), 10);
      if (!Number.isNaN(ariaLevel)) res.level = ariaLevel;
    }
    return res;
  }

  const tag = el.tagName.toLowerCase();

  if (tag === "button") return { role: "Buton" };
  if (tag === "a" && (el.hasAttribute("href") || el.getAttribute("role") === "link")) {
    return { role: "Link" };
  }
  if (tag === "input") {
    const type = (el.getAttribute("type") || "text").toLowerCase();
    if (type === "button" || type === "submit" || type === "reset") return { role: "Buton" };
    if (type === "checkbox") return { role: "Bifă" };
    if (type === "radio") return { role: "Opțiune radio" };
    if (type === "range") return { role: "Glisor" };
    if (type === "search") return { role: "Casetă de căutare" };
    return { role: "Casetă de text" };
  }
  if (tag === "textarea") return { role: "Zonă de text" };
  if (tag === "select") return { role: "Listă derulantă" };

  if (/^h[1-6]$/.test(tag)) {
    const level = parseInt(tag.charAt(1), 10);
    return { role: "Antet", level };
  }

  if (tag === "nav") return { role: "Navigare" };
  if (tag === "main") return { role: "Conținut principal" };
  if (tag === "header") return { role: "Antet pagină" };
  if (tag === "footer") return { role: "Subsol" };

  return { role: explicitRole ? explicitRole : "" };
}

/**
 * Resolves accessible name/label according to W3C AccName precedence.
 * @param {HTMLElement} el
 * @returns {string}
 */
export function getAccessibleLabel(el) {
  if (!el || typeof el !== "object") return "";

  // 1. aria-labelledby
  const labelledBy = el.getAttribute ? el.getAttribute("aria-labelledby") : null;
  if (labelledBy && typeof document !== "undefined") {
    const ids = labelledBy.split(/\s+/).filter(Boolean);
    const texts = ids
      .map(id => {
        const target = document.getElementById(id);
        return target ? (target.innerText || target.textContent || "").trim() : "";
      })
      .filter(Boolean);
    if (texts.length > 0) return texts.join(" ");
  }

  // 2. aria-label
  if (el.getAttribute && el.getAttribute("aria-label")) {
    const ariaLabel = el.getAttribute("aria-label").trim();
    if (ariaLabel) return ariaLabel;
  }

  // 3. For form elements: linked <label for="..."> or wrapping <label>
  if (el.id && typeof document !== "undefined") {
    try {
      const explicitLabel = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (explicitLabel) {
        const text = (explicitLabel.innerText || explicitLabel.textContent || "").trim();
        if (text) return text;
      }
    } catch (_) {}
  }
  if (el.closest) {
    const parentLabel = el.closest("label");
    if (parentLabel) {
      // Clone label and remove this input to avoid duplication
      const clone = parentLabel.cloneNode(true);
      const inputs = clone.querySelectorAll("input, select, textarea, button");
      inputs.forEach(i => i.remove());
      const text = (clone.innerText || clone.textContent || "").trim();
      if (text) return text;
    }
  }

  // 4. alt attribute (for images)
  if (el.getAttribute && el.getAttribute("alt")) {
    return el.getAttribute("alt").trim();
  }

  // 5. placeholder attribute
  if (el.getAttribute && el.getAttribute("placeholder")) {
    return el.getAttribute("placeholder").trim();
  }

  // 6. Direct text content for interactive buttons/links
  const tag = (el.tagName || "").toLowerCase();
  if (["button", "a", "h1", "h2", "h3", "h4", "h5", "h6", "summary", "legend"].includes(tag) || el.getAttribute?.("role") === "button") {
    const text = (el.innerText || el.textContent || "").trim();
    if (text) return text;
  }

  // 7. title attribute
  if (el.getAttribute && el.getAttribute("title")) {
    return el.getAttribute("title").trim();
  }

  return "";
}

/**
 * Computes the element's interactive state in Romanian.
 * @param {HTMLElement} el
 * @returns {string[]}
 */
export function getElementStateRo(el) {
  if (!el || !el.getAttribute) return [];
  const states = [];

  const type = (el.getAttribute("type") || "").toLowerCase();
  if (type === "checkbox" || el.getAttribute("role") === "checkbox" || el.getAttribute("role") === "switch") {
    if (el.checked || el.getAttribute("aria-checked") === "true") {
      states.push("bifat");
    } else {
      states.push("nebifat");
    }
  }

  if (type === "radio" || el.getAttribute("role") === "radio") {
    if (el.checked || el.getAttribute("aria-checked") === "true") {
      states.push("selectat");
    }
  }

  if (el.getAttribute("aria-expanded") === "true") states.push("extins");
  if (el.getAttribute("aria-expanded") === "false") states.push("restrâns");

  if (el.getAttribute("aria-pressed") === "true") states.push("activat");
  if (el.getAttribute("aria-pressed") === "false") states.push("dezactivat");

  if (el.getAttribute("aria-selected") === "true") states.push("selectat");

  if (el.disabled || el.getAttribute("aria-disabled") === "true") states.push("indisponibil");
  if (el.getAttribute("aria-invalid") === "true") states.push("conține erori");

  return states;
}

/**
 * Formats full spoken announcement for an element in natural Romanian.
 * E.g., "Buton: Clarifică documentul." or "Antet nivel doi: Planul tău zilnic."
 * @param {HTMLElement} el
 * @returns {string}
 */
export function formatElementAnnouncementRo(el) {
  if (!el) return "";

  const roleInfo = getElementRoleRo(el);
  const label = getAccessibleLabel(el);
  const states = getElementStateRo(el);

  const parts = [];

  // Prefix with role
  if (roleInfo.role) {
    if (roleInfo.role === "Antet" && roleInfo.level) {
      const levelWord = numberToWordsRo(roleInfo.level);
      parts.push(`Antet nivel ${levelWord}`);
    } else {
      parts.push(roleInfo.role);
    }
  }

  // Add accessible label
  if (label) {
    parts.push(label);
  } else if (!roleInfo.role) {
    const content = (el.innerText || el.textContent || "").trim();
    if (content) parts.push(content.slice(0, 150));
  }

  // Add states (e.g. bifat, extins)
  if (states.length > 0) {
    parts.push(states.join(", "));
  }

  // Additional value info for inputs or range
  const tag = (el.tagName || "").toLowerCase();
  if (tag === "input" && el.value && el.type !== "password") {
    const type = (el.type || "").toLowerCase();
    if (type === "range") {
      parts.push(`valoare: ${el.value}`);
    }
  }

  const raw = parts.filter(Boolean).join(": ");
  return normalizeRomanianForSpeech(raw);
}

/**
 * Scores a SpeechSynthesisVoice for Romanian TTS preference.
 * Edge Natural voices (Alina / Emil) score highest.
 * @param {SpeechSynthesisVoice} voice
 * @returns {number} 0-100 score
 */
export function scoreVoice(voice) {
  if (!voice) return 0;
  const lang = (voice.lang || "").toLowerCase();
  const name = (voice.name || "").toLowerCase();

  const isRo = lang.startsWith("ro");
  if (!isRo) {
    // Non-Romanian voices get low score unless default
    return voice.default ? 5 : 0;
  }

  // Romanian voice scoring:
  if (/natural|online/i.test(name)) return 100;
  if (/alina|emil/i.test(name)) return 95;
  if (/google|microsoft/i.test(name)) return 90;
  if (voice.localService) return 85;
  return 80;
}
