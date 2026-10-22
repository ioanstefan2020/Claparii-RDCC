/**
 * PrimaZi — Safe Highlight & Annotation Renderer (Wave 2)
 * Builds secure DOM without raw innerHTML, applies multi-modal cues (never color alone),
 * supports density caps, inline glossary popovers, and tentative tone notes in parentheses.
 * Ref: docs/TASKS-WAVE2.md A6, docs/SETTINGS-SPEC.md §5, docs/DESIGN.md §4
 */

import { getSetting } from "./settings.js";

/**
 * Escapes text for text node creation.
 */
function createText(str) {
  return document.createTextNode(str);
}

/**
 * Renders rich text into a target DOM container element.
 * @param {HTMLElement} container
 * @param {string} rawText
 * @param {object} params
 * @param {Array} [params.highlights] - [{ start, end, category, text }]
 * @param {Array} [params.annotations] - [{ start, end, kind, evidence_quote, note_ro, confidence }]
 * @param {Array} [params.glossary] - [{ term, explanation }]
 * @param {object} [params.options]
 */
export function renderRich(container, rawText, { highlights = [], annotations = [], glossary = [], options = {} } = {}) {
  if (!container) return;
  container.textContent = ""; // Clean container

  if (!rawText) return;

  const highlightMode = getSetting("highlight_mode") || "light";
  if (highlightMode === "off" || options.disableHighlights) {
    container.textContent = rawText;
    return;
  }

  // Calculate density cap based on word count
  const words = rawText.split(/\s+/).filter(Boolean);
  const wordCount = words.length;
  let maxHighlights = 999;
  if (highlightMode === "light") maxHighlights = Math.max(3, Math.floor(wordCount * 0.05));
  else if (highlightMode === "medium") maxHighlights = Math.max(6, Math.floor(wordCount * 0.10));
  else if (highlightMode === "strong") maxHighlights = Math.max(10, Math.floor(wordCount * 0.15));

  const allowedCategories = getSetting("highlight_categories") || ["action", "deadline", "warning"];

  // Filter and sort spans
  const validHighlights = (highlights || [])
    .filter(h => allowedCategories.includes(h.category) && typeof h.start === "number" && typeof h.end === "number" && h.start < h.end)
    .slice(0, maxHighlights);

  // Combine highlights and annotations into non-overlapping events
  const spans = [];

  validHighlights.forEach(h => {
    spans.push({
      start: h.start,
      end: h.end,
      type: "highlight",
      category: h.category,
      label: h.text || rawText.slice(h.start, h.end)
    });
  });

  const showToneNotes = getSetting("tone_notes") === "on";
  if (showToneNotes) {
    (annotations || []).forEach(a => {
      if (typeof a.start === "number" && typeof a.end === "number" && a.start < a.end) {
        spans.push({
          start: a.start,
          end: a.end,
          type: "annotation",
          kind: a.kind,
          note_ro: a.note_ro,
          confidence: a.confidence,
          evidence: a.evidence_quote
        });
      }
    });
  }

  // Sort spans by start offset
  spans.sort((a, b) => a.start - b.start || b.end - a.end);

  // Build DOM segments cleanly
  let cursor = 0;
  const len = rawText.length;

  for (const span of spans) {
    if (span.start < cursor) {
      // Overlapping span: skip to preserve clean layout
      continue;
    }

    if (span.start > cursor) {
      // Append non-highlighted plain text before span
      const chunk = rawText.slice(cursor, span.start);
      container.appendChild(createText(chunk));
      cursor = span.start;
    }

    const spanText = rawText.slice(span.start, Math.min(span.end, len));
    cursor = Math.min(span.end, len);

    if (span.type === "highlight") {
      const mark = document.createElement("mark");
      mark.className = `a11y-highlight a11y-cat-${span.category}`;
      mark.setAttribute("data-category", span.category);
      mark.appendChild(createText(spanText));

      // Append accessible category cue icon/badge
      if (span.category === "deadline") {
        const badge = document.createElement("span");
        badge.className = "a11y-cue-badge";
        badge.setAttribute("aria-hidden", "true");
        badge.textContent = " ⏱";
        mark.appendChild(badge);
      } else if (span.category === "warning") {
        const badge = document.createElement("span");
        badge.className = "a11y-cue-badge";
        badge.setAttribute("aria-hidden", "true");
        badge.textContent = " ⚠";
        mark.appendChild(badge);
      }

      container.appendChild(mark);
    } else if (span.type === "annotation") {
      // Inline tentative tone note
      const wrapper = document.createElement("span");
      wrapper.className = `a11y-tone-wrapper tone-${span.kind}`;
      wrapper.appendChild(createText(spanText));

      const note = document.createElement("span");
      note.className = "a11y-tone-note";
      note.setAttribute("role", "note");
      note.setAttribute("title", `Indiciu: "${span.evidence || spanText}" (încredere ${span.confidence || 'medie'})`);
      note.textContent = ` ${span.note_ro || `(posibil ${span.kind} — nesigur)`}`;

      wrapper.appendChild(note);
      container.appendChild(wrapper);
    }
  }

  // Append remaining text after last span
  if (cursor < len) {
    container.appendChild(createText(rawText.slice(cursor, len)));
  }

  // Handle inline glossary if enabled
  const glossaryMode = getSetting("glossary_inline") || "hover/tap";
  if (glossaryMode !== "off" && glossary && glossary.length > 0) {
    attachGlossary(container, glossary);
  }
}

/**
 * Safely attaches glossary terms with definition tooltips/popovers.
 */
function attachGlossary(container, glossary) {
  // Safe text replacement over leaf text nodes
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null);
  const textNodes = [];
  while (walker.nextNode()) {
    if (!walker.currentNode.parentElement.closest(".a11y-glossary-term")) {
      textNodes.push(walker.currentNode);
    }
  }

  for (const item of glossary) {
    if (!item.term || !item.explanation) continue;
    const regex = new RegExp(`\\b(${escapeRegex(item.term)})\\b`, "i");

    for (const node of textNodes) {
      const val = node.nodeValue;
      const match = regex.exec(val);
      if (match) {
        const span = document.createElement("span");
        span.className = "a11y-glossary-term";
        span.tabIndex = 0;
        span.setAttribute("role", "button");
        span.setAttribute("aria-label", `${match[1]}: ${item.explanation}`);

        const termText = match[1];
        span.appendChild(createText(termText));

        const tip = document.createElement("span");
        tip.className = "a11y-glossary-tooltip";
        tip.setAttribute("role", "tooltip");
        tip.textContent = item.explanation;
        span.appendChild(tip);

        const before = createText(val.slice(0, match.index));
        const after = createText(val.slice(match.index + termText.length));

        const parent = node.parentNode;
        if (parent) {
          parent.insertBefore(before, node);
          parent.insertBefore(span, node);
          parent.insertBefore(after, node);
          parent.removeChild(node);
        }
        break;
      }
    }
  }
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function clearHighlights(el) {
  if (!el) return;
  const raw = el.textContent || "";
  el.textContent = raw;
}
