/**
 * a11y-text.js - Accessible Text Transformation & Neurodivergent Saccade Assistance
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 *
 * Implements:
 * - Bionic Reading (visual fixation anchors for ADHD / cognitive fatigue)
 * - Key Operational Terms Highlighting (deadlines, action verbs, urgencies)
 * - Reading Ruler Guide (follow-along reading line for dyslexia/visual tracking)
 */

export const KEY_TERMS_REGEX = /\b(termen|dată|ora|urgent|important|semnează|trimite|descarcă|confirmă|completat|depus|obligatoriu|prioritate|atenție|recomandat|ședință|echipă|luni|marți|miercuri|joi|vineri|sâmbătă|duminică|deadline|raport|contract|formular|acces|card)\b/gi;

/**
 * Escapes HTML characters safely.
 */
function escapeHtml(str) {
  if (typeof str !== "string") return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Reads active preferences from localStorage.
 */
export function getActiveTextPrefs() {
  try {
    const raw = localStorage.getItem("wp.prefs.v1");
    if (!raw) return { bionic: false, highlightKeyTerms: false, readingRuler: false };
    const parsed = JSON.parse(raw);
    const p = parsed && parsed.prefs ? parsed.prefs : {};
    return {
      bionic: Boolean(p.bionic),
      highlightKeyTerms: Boolean(p.highlightKeyTerms),
      readingRuler: Boolean(p.readingRuler)
    };
  } catch {
    return { bionic: false, highlightKeyTerms: false, readingRuler: false };
  }
}

/**
 * Transforms plain text into accessible HTML with Bionic Reading and/or Key Term Highlighting.
 *
 * @param {string} text - Raw text to format
 * @param {object} [customOptions] - Optional override of preferences
 * @returns {string} - Accessible HTML string
 */
export function renderAccessibleText(text, customOptions = null) {
  if (!text || typeof text !== "string") return "";
  const opts = customOptions || getActiveTextPrefs();

  // If neither feature is active, return safely escaped plain text
  if (!opts.bionic && !opts.highlightKeyTerms) {
    return escapeHtml(text);
  }

  // Preserve line breaks
  const paragraphs = text.split(/\r?\n/);

  return paragraphs
    .map(para => {
      if (!para.trim()) return "";
      const tokens = para.split(/(\s+)/);

      const transformed = tokens.map(token => {
        if (/^\s+$/.test(token)) return token;

        // Clean punctuation for matching
        const cleanWord = token.replace(/^[.,:;!?"'«»()\[\]{}]+|[.,:;!?"'«»()\[\]{}]+$/g, "");
        const isKeyTerm = opts.highlightKeyTerms && KEY_TERMS_REGEX.test(cleanWord);

        if (isKeyTerm) {
          // Highlight key term
          return `<strong class="a11y-key-term" style="font-weight: 700; background-color: rgba(254, 240, 138, 0.35); padding: 0.1em 0.3em; border-radius: 4px; border-bottom: 2px solid var(--primary);">${escapeHtml(token)}</strong>`;
        }

        if (opts.bionic && cleanWord.length >= 3) {
          const splitIdx = Math.ceil(token.length * 0.45);
          const fixation = escapeHtml(token.slice(0, splitIdx));
          const rest = escapeHtml(token.slice(splitIdx));
          return `<b class="bionic-fixation" style="font-weight: 700; opacity: 0.96;">${fixation}</b>${rest}`;
        }

        return escapeHtml(token);
      });

      return transformed.join("");
    })
    .join("<br>");
}

/**
 * Toggles or updates the visual Reading Ruler guide on the screen.
 */
let rulerElement = null;
let rulerMoveHandler = null;

export function toggleReadingRuler(enabled) {
  if (typeof document === "undefined") return;

  if (rulerElement && !enabled) {
    if (rulerMoveHandler) {
      document.removeEventListener("mousemove", rulerMoveHandler);
      rulerMoveHandler = null;
    }
    rulerElement.remove();
    rulerElement = null;
    return;
  }

  if (enabled && !rulerElement) {
    rulerElement = document.createElement("div");
    rulerElement.id = "reading-ruler-guide";
    rulerElement.setAttribute("aria-hidden", "true");
    rulerElement.style.position = "fixed";
    rulerElement.style.left = "0";
    rulerElement.style.right = "0";
    rulerElement.style.height = "36px";
    rulerElement.style.backgroundColor = "rgba(255, 230, 0, 0.12)";
    rulerElement.style.borderTop = "1.5px solid rgba(255, 200, 0, 0.6)";
    rulerElement.style.borderBottom = "1.5px solid rgba(255, 200, 0, 0.6)";
    rulerElement.style.pointerEvents = "none";
    rulerElement.style.zIndex = "9999";
    rulerElement.style.transform = "translateY(-50%)";
    rulerElement.style.display = "block";
    document.body.appendChild(rulerElement);

    rulerMoveHandler = (e) => {
      if (rulerElement) {
        rulerElement.style.top = `${e.clientY}px`;
      }
    };
    document.addEventListener("mousemove", rulerMoveHandler, { passive: true });
  }
}
