/**
 * content.js - Content Script for PrimaZi Extension
 * Bundled via esbuild into dist/content.js (IIFE format).
 *
 * Features:
 *  - Selection listener with 3000 chars sentence boundary truncation
 *  - Password field detection & bypass (security rule)
 *  - Closed Shadow DOM button & dialog via CardManager
 *  - Site preferences auto-import from website origin
 *  - Message routing with service worker and local fallback
 */

import { CardManager } from "./card.js";
import { adaptLocally, splitSentences } from "./local_mode.js";

const MAX_SELECTION_CHARS = 3000;

class PrimaZiContentScript {
  constructor() {
    this.userPrefs = null;
    this.config = null;
    this.cardManager = new CardManager((action, text, mode) => {
      this.handleAdaptAction(action, text, mode);
    });

    this.init();
  }

  async init() {
    // 1. Fetch current preferences and config from background service worker
    chrome.runtime.sendMessage({ type: "PREFS_GET" }, (res) => {
      if (res && res.prefs) {
        this.userPrefs = res.prefs;
        this.config = res.config;
        this.cardManager.setUserPrefs(this.userPrefs);
      }
    });

    // 2. Check site auto-import if running on website origin
    this.checkSiteOriginSync();

    // 3. Attach selection event listeners
    document.addEventListener("mouseup", (e) => this.onSelectionChange(e));
    document.addEventListener("keyup", (e) => {
      if (e.key === "Shift" || e.key === "ArrowLeft" || e.key === "ArrowRight") {
        this.onSelectionChange(e);
      }
    });

    // 4. Listen for trigger events from background (context menu / keyboard shortcut)
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
      if (msg.type === "TRIGGER_SELECTION") {
        this.triggerFromShortcutOrMenu(msg.selectedText);
        sendResponse({ ok: true });
      }
    });
  }

  /**
   * If current origin is in siteOrigins, read site's localStorage and sync
   */
  checkSiteOriginSync() {
    try {
      const siteStorageKey = "primazi.settings.v2";
      const raw = localStorage.getItem(siteStorageKey) || localStorage.getItem("wp.prefs.v1");
      if (raw) {
        const parsed = JSON.parse(raw);
        chrome.runtime.sendMessage({
          type: "PREFS_FROM_SITE",
          prefs: parsed,
          updatedAt: parsed.updatedAt || new Date().toISOString()
        });
      }
    } catch (_) {
      // LocalStorage access may be restricted on some third-party frames
    }
  }

  /**
   * Check if element is a sensitive field (password)
   */
  isSensitiveElement(el) {
    if (!el) return false;
    if (el.tagName === "INPUT" && el.type === "password") return true;
    const parentPassword = el.closest && el.closest("input[type=password]");
    return !!parentPassword;
  }

  /**
   * Truncate text cleanly at sentence boundary if longer than MAX_SELECTION_CHARS
   */
  sanitizeAndTruncate(text) {
    if (!text) return "";
    let trimmed = text.trim();
    if (trimmed.length <= MAX_SELECTION_CHARS) return trimmed;

    // Split sentences and accumulate up to MAX_SELECTION_CHARS
    const sentences = splitSentences(trimmed);
    let result = "";
    for (const s of sentences) {
      if ((result + " " + s).trim().length > MAX_SELECTION_CHARS) {
        break;
      }
      result = (result + " " + s).trim();
    }

    return result.length > 0 ? result : trimmed.slice(0, MAX_SELECTION_CHARS);
  }

  onSelectionChange(e) {
    // If clicking inside the shadow DOM itself, ignore
    if (e.target && e.target.id === "primazi-ext-root") return;

    // Check active site disabled list
    if (this.config && this.config.disabledSites && this.config.disabledSites.includes(window.location.hostname)) {
      this.cardManager.hideFloatingButton();
      return;
    }

    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) {
      this.cardManager.hideFloatingButton();
      return;
    }

    const text = sel.toString().trim();
    if (text.length < 5) {
      this.cardManager.hideFloatingButton();
      return;
    }

    // Check if selection is inside a password field
    const anchorNode = sel.anchorNode;
    const focusNode = sel.focusNode;
    const anchorEl = anchorNode?.nodeType === Node.ELEMENT_NODE ? anchorNode : anchorNode?.parentElement;
    const focusEl = focusNode?.nodeType === Node.ELEMENT_NODE ? focusNode : focusNode?.parentElement;

    if (this.isSensitiveElement(anchorEl) || this.isSensitiveElement(focusEl)) {
      this.cardManager.hideFloatingButton();
      return;
    }

    // Calculate position from selection bounding rect
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    if (rect.width === 0 && rect.height === 0) {
      this.cardManager.hideFloatingButton();
      return;
    }

    const posX = rect.right + 8;
    const posY = rect.bottom + 4;
    const sanitizedText = this.sanitizeAndTruncate(text);

    this.cardManager.showFloatingButton(posX, posY, sanitizedText);
  }

  triggerFromShortcutOrMenu(selectedText) {
    let text = (selectedText || "").trim();
    if (!text) {
      const sel = window.getSelection();
      if (sel && !sel.isCollapsed) {
        text = sel.toString().trim();
      }
    }

    if (!text) return;
    const sanitizedText = this.sanitizeAndTruncate(text);
    this.handleAdaptAction("adapt", sanitizedText, "simplify");
  }

  handleAdaptAction(actionType, text, mode = "simplify") {
    const requestId = `req-${Date.now()}`;
    const truncatedText = this.sanitizeAndTruncate(text);

    chrome.runtime.sendMessage(
      {
        type: "ADAPT",
        requestId: requestId,
        text: truncatedText,
        action: mode
      },
      (res) => {
        if (chrome.runtime.lastError || !res || res.type === "ERROR") {
          // Fallback seamlessly to local deterministic engine!
          const localData = adaptLocally(truncatedText, mode);
          this.cardManager.showCard(localData, truncatedText);
          return;
        }

        if (res.type === "RESULT" && res.data) {
          this.cardManager.showCard(res.data, truncatedText);
        } else {
          const localData = adaptLocally(truncatedText, mode);
          this.cardManager.showCard(localData, truncatedText);
        }
      }
    );
  }
}

// Instantiate on document load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => new PrimaZiContentScript());
} else {
  new PrimaZiContentScript();
}
