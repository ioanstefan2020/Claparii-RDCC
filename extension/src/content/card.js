/**
 * card.js - Accessible Shadow DOM Result Card & Floating Action Button
 * Conforms to WCAG 2.2 AAA & EXTENSION.md §3.4, §3.5
 *
 * Rules:
 *  - Closed Shadow DOM (page CSS cannot break extension; extension CSS cannot leak)
 *  - Plain text node rendering (Zero innerHTML for AI/user text)
 *  - 44px min touch/click targets
 *  - Full keyboard navigation (focus trap, Esc to close, focus restoration)
 *  - Screen reader announcements via aria-live
 */

import { normalizeRomanianForSpeech } from "../shared/tts-normalize-ro.js";
import { splitSentencesRo } from "../shared/tts.js";
import { adaptLocally, extractKeyPhrases } from "./local_mode.js";

const CARD_STYLES = `
  :host {
    all: initial;
    font-family: 'Lexend', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: #1e293b;
    box-sizing: border-box;
    z-index: 2147483647;
  }
  *, *::before, *::after {
    box-sizing: border-box;
  }

  /* Floating trigger button */
  .primazi-floating-btn {
    position: absolute;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    min-height: 44px;
    background: #0d9488;
    color: #ffffff;
    font-size: 15px;
    font-weight: 600;
    border: none;
    border-radius: 9999px;
    box-shadow: 0 4px 14px rgba(13, 148, 136, 0.4), 0 2px 6px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: transform 0.15s ease, background-color 0.15s ease;
    z-index: 2147483647;
    outline: none;
  }
  .primazi-floating-btn:hover {
    background: #0f766e;
    transform: translateY(-2px);
  }
  .primazi-floating-btn:focus-visible {
    outline: 3px solid #f59e0b;
    outline-offset: 2px;
  }
  .primazi-floating-btn svg {
    width: 18px;
    height: 18px;
    fill: currentColor;
  }

  /* Card overlay backdrop */
  .primazi-overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    z-index: 2147483647;
  }

  /* Accessible Card */
  .primazi-card {
    background: #ffffff;
    color: #1e293b;
    border: 2px solid #0d9488;
    border-radius: 16px;
    width: 100%;
    max-width: 640px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    animation: primaziFadeIn 0.2s ease-out;
  }

  @keyframes primaziFadeIn {
    from { opacity: 0; transform: scale(0.96); }
    to { opacity: 1; transform: scale(1); }
  }

  @keyframes primaziPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.55; }
  }

  /* Theme overrides */
  .primazi-card.theme-dark {
    background: #0f172a;
    color: #f8fafc;
    border-color: #38bdf8;
  }
  .primazi-card.theme-high-contrast {
    background: #000000;
    color: #ffff00;
    border: 3px solid #ffff00;
  }
  .primazi-card.theme-soft-dark {
    background: #1e293b;
    color: #f1f5f9;
    border-color: #0d9488;
  }

  /* Header */
  .primazi-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    background: rgba(13, 148, 136, 0.06);
  }
  .primazi-card.theme-dark .primazi-header,\n  .primazi-card.theme-high-contrast .primazi-header {
    border-bottom: 1px solid currentColor;
    background: transparent;
  }

  .primazi-title-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .primazi-title {
    font-size: 18px;
    font-weight: 700;
    margin: 0;
  }
  .primazi-badge {
    font-size: 12px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 999px;
    background: #0d9488;
    color: #ffffff;
  }
  .primazi-badge.local {
    background: #e2e8f0;
    color: #475569;
    border: 1px solid #cbd5e1;
  }
  .primazi-badge.loading {
    background: #0284c7;
    color: #ffffff;
    animation: primaziPulse 1.4s infinite;
  }
  .primazi-card.theme-high-contrast .primazi-badge {
    background: #000000;
    color: #ffff00;
    border: 1px solid #ffff00;
  }

  /* Action Buttons bar */
  .primazi-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 20px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
    background: rgba(248, 250, 252, 0.8);
  }
  .primazi-card.theme-dark .primazi-actions,
  .primazi-card.theme-high-contrast .primazi-actions {
    background: transparent;
    border-bottom: 1px solid currentColor;
  }

  .primazi-btn {
    min-height: 44px;
    min-width: 44px;
    padding: 8px 14px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    border-radius: 8px;
    border: 1.5px solid #cbd5e1;
    background: #ffffff;
    color: #334155;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .primazi-btn:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }
  .primazi-btn:focus-visible {
    outline: 3px solid #0d9488;
    outline-offset: 2px;
  }
  .primazi-btn.active {
    background: #0d9488;
    color: #ffffff;
    border-color: #0d9488;
  }
  .primazi-card.theme-dark .primazi-btn {
    background: #1e293b;
    color: #f8fafc;
    border-color: #475569;
  }
  .primazi-card.theme-dark .primazi-btn:hover {
    background: #334155;
  }
  .primazi-card.theme-high-contrast .primazi-btn {
    background: #000000;
    color: #ffff00;
    border-color: #ffff00;
  }
  .primazi-card.theme-high-contrast .primazi-btn:hover,
  .primazi-card.theme-high-contrast .primazi-btn.active {
    background: #ffff00;
    color: #000000;
  }

  .primazi-btn-close {
    background: transparent;
    border: none;
    font-size: 20px;
    line-height: 1;
    padding: 8px 12px;
    cursor: pointer;
    color: inherit;
    border-radius: 6px;
  }
  .primazi-btn-close:focus-visible {
    outline: 3px solid #0d9488;
  }

  /* Body Content */
  .primazi-body {
    padding: 20px;
    overflow-y: auto;
    flex: 1;
  }
  .primazi-text {
    font-size: 1.05rem;
    line-height: 1.7;
    margin: 0;
    white-space: pre-line;
  }
  .primazi-bullets-list {
    margin: 0;
    padding-left: 24px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .primazi-bullets-list li {
    line-height: 1.6;
  }

  /* Highlights */
  mark.primazi-highlight {
    background-color: #fef08a;
    color: #854d0e;
    padding: 2px 4px;
    border-radius: 4px;
    font-weight: 600;
  }
  .primazi-card.theme-dark mark.primazi-highlight {
    background-color: #854d0e;
    color: #fef08a;
  }
  .primazi-card.theme-high-contrast mark.primazi-highlight {
    background-color: #ffffff;
    color: #000000;
    outline: 2px solid #ffff00;
  }

  /* Notes */
  .primazi-notes {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .primazi-note-card {
    padding: 10px 14px;
    background: #f8fafc;
    border-left: 4px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    font-size: 14px;
  }
  .primazi-card.theme-dark .primazi-note-card {
    background: #1e293b;
    border-color: #38bdf8;
  }
  .primazi-card.theme-high-contrast .primazi-note-card {
    background: #000000;
    border: 1px solid #ffff00;
    color: #ffff00;
  }
  .primazi-note-badge {
    font-weight: 700;
    color: #2563eb;
    margin-right: 6px;
  }
  .primazi-card.theme-dark .primazi-note-badge {
    color: #38bdf8;
  }
  .primazi-card.theme-high-contrast .primazi-note-badge {
    color: #ffff00;
  }

  /* Footer */
  .primazi-footer {
    padding: 12px 20px;
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: #64748b;
  }
  .primazi-card.theme-dark .primazi-footer {
    color: #94a3b8;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  .primazi-card.theme-high-contrast .primazi-footer {
    color: #ffff00;
    border-top: 1px solid #ffff00;
  }

  /* Screen reader only */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }
`;

export class CardManager {
  constructor(onActionCallback) {
    this.onActionCallback = onActionCallback;
    this.shadowRoot = null;
    this.hostElement = null;
    this.floatingBtn = null;
    this.overlay = null;
    this.bodyContainer = null;
    this.lastActiveElement = null;
    this.currentData = null;
    this.originalText = "";
    this.showingOriginal = false;
    this.viewMode = "text"; // "text" | "bullets" | "shorter"
    this.isSpeaking = false;
    this.currentUtterance = null;
    this.ttsSentences = [];
    this.ttsIndex = 0;
    this.ttsBtn = null;
    this.userPrefs = {};

    this.initShadowHost();
    this.initSpeechVoices();
  }

  initSpeechVoices() {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        if (window.speechSynthesis) window.speechSynthesis.getVoices();
      };
    }
  }

  initShadowHost() {
    let host = document.getElementById("primazi-ext-root");
    if (!host) {
      host = document.createElement("div");
      host.id = "primazi-ext-root";
      document.documentElement.appendChild(host);
    }
    this.hostElement = host;
    this.shadowRoot = host.attachShadow({ mode: "closed" });

    // Inject styles
    const styleEl = document.createElement("style");
    styleEl.textContent = CARD_STYLES;
    this.shadowRoot.appendChild(styleEl);

    // Live region for screen readers
    this.liveRegion = document.createElement("div");
    this.liveRegion.className = "sr-only";
    this.liveRegion.setAttribute("aria-live", "polite");
    this.liveRegion.setAttribute("aria-atomic", "true");
    this.shadowRoot.appendChild(this.liveRegion);
  }

  announce(message) {
    if (this.liveRegion) {
      this.liveRegion.textContent = "";
      setTimeout(() => {
        this.liveRegion.textContent = message;
      }, 50);
    }
  }

  setUserPrefs(prefs) {
    this.userPrefs = prefs || {};
  }

  /**
   * Shows floating trigger button near user's selection
   */
  showFloatingButton(x, y, selectedText) {
    this.hideFloatingButton();
    this.originalText = selectedText;

    const btn = document.createElement("button");
    btn.className = "primazi-floating-btn";
    btn.setAttribute("type", "button");
    btn.setAttribute("aria-label", "Fă clar selecția curentă cu PrimaZi");

    // Icon + Label
    btn.innerHTML = `
      <svg viewBox="0 0 24 24">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
      </svg>
      <span>Fă clar</span>
    `;

    // Position securely within viewport
    const clampedX = Math.max(10, Math.min(window.innerWidth - 130, x));
    const clampedY = Math.max(10, y + window.scrollY + 10);

    btn.style.left = `${clampedX}px`;
    btn.style.top = `${clampedY}px`;

    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.hideFloatingButton();
      if (this.onActionCallback) {
        this.onActionCallback("adapt", this.originalText, "simplify");
      }
    });

    this.shadowRoot.appendChild(btn);
    this.floatingBtn = btn;
  }

  hideFloatingButton() {
    if (this.floatingBtn) {
      this.floatingBtn.remove();
      this.floatingBtn = null;
    }
  }

  /**
   * Shows immediate loading card so the user sees instant feedback.
   */
  showLoadingCard(selectedText) {
    this.hideFloatingButton();
    this.closeCard();

    this.originalText = selectedText || this.originalText;
    this.lastActiveElement = document.activeElement;

    const overlay = document.createElement("div");
    overlay.className = "primazi-overlay";

    const card = document.createElement("div");
    card.className = "primazi-card";
    card.setAttribute("role", "dialog");
    card.setAttribute("aria-modal", "true");
    card.setAttribute("aria-labelledby", "primazi-card-title");

    // Apply visual preferences
    const p = this.userPrefs?.prefs || {};
    if (p.theme === "dark" || p.theme === "soft_dark") {
      card.classList.add("theme-dark");
    } else if (p.theme === "high_contrast") {
      card.classList.add("theme-high-contrast");
    }
    if (p.font_scale) {
      card.style.fontSize = `${16 * Number(p.font_scale)}px`;
    }

    const header = document.createElement("header");
    header.className = "primazi-header";

    const titleRow = document.createElement("div");
    titleRow.className = "primazi-title-row";

    const title = document.createElement("h2");
    title.id = "primazi-card-title";
    title.className = "primazi-title";
    title.textContent = "PrimaZi Claritate";

    const badge = document.createElement("span");
    badge.className = "primazi-badge loading";
    badge.textContent = "Se adaptează...";

    titleRow.appendChild(title);
    titleRow.appendChild(badge);

    const closeBtn = document.createElement("button");
    closeBtn.className = "primazi-btn-close";
    closeBtn.setAttribute("type", "button");
    closeBtn.setAttribute("aria-label", "Închide dialogul (Esc)");
    closeBtn.textContent = "✕";
    closeBtn.addEventListener("click", () => this.closeCard());

    header.appendChild(titleRow);
    header.appendChild(closeBtn);

    const bodyContainer = document.createElement("div");
    bodyContainer.className = "primazi-body";

    const loadingText = document.createElement("p");
    loadingText.className = "primazi-text";
    loadingText.style.fontStyle = "italic";
    loadingText.textContent =
      "✨ Se adaptează textul conform profilului tău de confort...";
    bodyContainer.appendChild(loadingText);

    const footer = document.createElement("footer");
    footer.className = "primazi-footer";
    const disclaimer = document.createElement("span");
    disclaimer.textContent = "Procesare text cu asistență de accesibilitate...";
    footer.appendChild(disclaimer);

    card.appendChild(header);
    card.appendChild(bodyContainer);
    card.appendChild(footer);
    overlay.appendChild(card);

    const keyHandler = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        this.closeCard();
      }
    };
    this.overlayKeyHandler = keyHandler;
    window.addEventListener("keydown", keyHandler);

    this.shadowRoot.appendChild(overlay);
    this.overlay = overlay;
    this.announce("Se adaptează textul...");
  }

  /**
   * Updates shorter text in-place when received asynchronously.
   */
  updateShorterData(data) {
    if (!this.currentData) this.currentData = {};
    if (data && data.text) {
      this.currentData.shorterText = data.text;
      if (data.key_phrases?.length) {
        this.currentData.shorterKeyPhrases = data.key_phrases;
      }
      if (this.viewMode === "shorter" && this.bodyContainer) {
        this.renderBodyContent(this.bodyContainer);
      }
    }
  }

  /**
   * Renders the accessible dialog card with result data
   */
  showCard(data, originalText, initialMode = "text") {
    this.hideFloatingButton();
    this.closeCard();

    this.currentData = data;
    this.originalText = originalText || this.originalText;
    this.lastActiveElement = document.activeElement;
    this.showingOriginal = false;
    this.viewMode =
      initialMode === "shorter"
        ? "shorter"
        : initialMode === "bullets"
          ? "bullets"
          : data.bullets && data.bullets.length > 0 && !data.text
            ? "bullets"
            : "text";

    const overlay = document.createElement("div");
    overlay.className = "primazi-overlay";

    const card = document.createElement("div");
    card.className = "primazi-card";
    card.setAttribute("role", "dialog");
    card.setAttribute("aria-modal", "true");
    card.setAttribute("aria-labelledby", "primazi-card-title");

    // Apply visual preferences
    const p = this.userPrefs?.prefs || {};
    if (p.theme === "dark" || p.theme === "soft_dark") {
      card.classList.add("theme-dark");
    } else if (p.theme === "high_contrast") {
      card.classList.add("theme-high-contrast");
    }
    if (p.font_scale) {
      card.style.fontSize = `${16 * Number(p.font_scale)}px`;
    }

    // 1. Header
    const header = document.createElement("header");
    header.className = "primazi-header";

    const titleRow = document.createElement("div");
    titleRow.className = "primazi-title-row";

    const title = document.createElement("h2");
    title.id = "primazi-card-title";
    title.className = "primazi-title";
    title.textContent = "PrimaZi Claritate";

    const badge = document.createElement("span");
    const isLocal = data.mode === "local";
    badge.className = `primazi-badge ${isLocal ? "local" : ""}`;
    badge.textContent = isLocal ? "Mod de bază (offline)" : "AI";

    titleRow.appendChild(title);
    titleRow.appendChild(badge);

    const closeBtn = document.createElement("button");
    closeBtn.className = "primazi-btn-close";
    closeBtn.setAttribute("type", "button");
    closeBtn.setAttribute("aria-label", "Închide dialogul (Esc)");
    closeBtn.textContent = "✕";
    closeBtn.addEventListener("click", () => this.closeCard());

    header.appendChild(titleRow);
    header.appendChild(closeBtn);

    // 2. Action buttons bar
    const actions = document.createElement("nav");
    actions.className = "primazi-actions";
    actions.setAttribute("aria-label", "Opțiuni de adaptare");

    // Listen Button
    const listenBtn = document.createElement("button");
    listenBtn.className = "primazi-btn";
    listenBtn.setAttribute("type", "button");
    listenBtn.textContent = "🔊 Ascultă";
    listenBtn.addEventListener("click", () => this.toggleReadAloud(listenBtn));
    actions.appendChild(listenBtn);

    // Bullets Button
    const bulletsBtn = document.createElement("button");
    bulletsBtn.className = `primazi-btn ${this.viewMode === "bullets" ? "active" : ""}`;
    bulletsBtn.setAttribute("type", "button");
    bulletsBtn.textContent = "• Buline";
    bulletsBtn.addEventListener("click", () => {
      this.viewMode = this.viewMode === "bullets" ? "text" : "bullets";
      bulletsBtn.classList.toggle("active", this.viewMode === "bullets");
      if (this.viewMode === "bullets") {
        shorterBtn.classList.remove("active");
        origBtn.classList.remove("active");
        this.showingOriginal = false;
      }
      this.renderBodyContent(bodyContainer);
      this.announce(
        this.viewMode === "bullets"
          ? "Afișat ca listă de buline."
          : "Afișat ca text continuu.",
      );
    });
    actions.appendChild(bulletsBtn);

    // Shorter Button (toggles compressed view smoothly without dialog recreation!)
    const shorterBtn = document.createElement("button");
    shorterBtn.className = `primazi-btn ${this.viewMode === "shorter" ? "active" : ""}`;
    shorterBtn.setAttribute("type", "button");
    shorterBtn.textContent = "✂️ Mai scurt";
    shorterBtn.addEventListener("click", () => {
      this.viewMode = this.viewMode === "shorter" ? "text" : "shorter";
      shorterBtn.classList.toggle("active", this.viewMode === "shorter");
      if (this.viewMode === "shorter") {
        bulletsBtn.classList.remove("active");
        origBtn.classList.remove("active");
        this.showingOriginal = false;

        // Provide instantaneous shorter text if not yet loaded
        if (!this.currentData.shorterText) {
          const localShorter = adaptLocally(this.originalText, "shorter");
          this.currentData.shorterText = localShorter.text;
          this.currentData.shorterKeyPhrases = localShorter.key_phrases;

          if (this.onActionCallback) {
            this.onActionCallback(
              "adapt_in_place",
              this.originalText,
              "shorter",
            );
          }
        }
      }
      this.renderBodyContent(bodyContainer);
      this.announce(
        this.viewMode === "shorter"
          ? "Afișat în format mai scurt și comprimat."
          : "Afișat ca text continuu.",
      );
    });
    actions.appendChild(shorterBtn);

    // Copy Button
    const copyBtn = document.createElement("button");
    copyBtn.className = "primazi-btn";
    copyBtn.setAttribute("type", "button");
    copyBtn.textContent = "📋 Copiază";
    copyBtn.addEventListener("click", () => {
      let textToCopy = "";
      if (this.showingOriginal) {
        textToCopy = this.originalText;
      } else if (this.viewMode === "shorter") {
        textToCopy =
          this.currentData?.shorterText ||
          adaptLocally(this.originalText, "shorter").text;
      } else if (
        this.viewMode === "bullets" &&
        this.currentData?.bullets?.length
      ) {
        textToCopy = this.currentData.bullets.join("\n");
      } else {
        textToCopy = this.currentData?.text || this.originalText;
      }

      navigator.clipboard.writeText(textToCopy).then(() => {
        copyBtn.textContent = "✓ Copiat!";
        setTimeout(() => {
          copyBtn.textContent = "📋 Copiază";
        }, 2000);
        this.announce("Textul a fost copiat în clipboard.");
      });
    });
    actions.appendChild(copyBtn);

    // Show Original Toggle
    const origBtn = document.createElement("button");
    origBtn.className = "primazi-btn";
    origBtn.setAttribute("type", "button");
    origBtn.textContent = "👁️ Original";
    origBtn.addEventListener("click", () => {
      this.showingOriginal = !this.showingOriginal;
      origBtn.classList.toggle("active", this.showingOriginal);
      this.renderBodyContent(bodyContainer);
      this.announce(
        this.showingOriginal
          ? "Se afișează textul original neschimbat."
          : "Se afișează textul adaptat.",
      );
    });
    actions.appendChild(origBtn);

    // 3. Body
    const bodyContainer = document.createElement("div");
    bodyContainer.className = "primazi-body";
    this.bodyContainer = bodyContainer;
    this.renderBodyContent(bodyContainer);

    // 4. Footer
    const footer = document.createElement("footer");
    footer.className = "primazi-footer";

    const disclaimer = document.createElement("span");
    disclaimer.textContent = isLocal
      ? "Formatat local pe dispozitiv. Verifică detaliile în original."
      : "Adaptat cu asistență AI. Verifică detaliile importante în original.";

    const metricsSpan = document.createElement("span");
    if (data.metrics) {
      metricsSpan.textContent = `Claritate: ${Math.round(data.metrics.readability_before)}% → ${Math.round(data.metrics.readability_after)}%`;
    }

    footer.appendChild(disclaimer);
    footer.appendChild(metricsSpan);

    // Assemble Card
    card.appendChild(header);
    card.appendChild(actions);
    card.appendChild(bodyContainer);
    card.appendChild(footer);
    overlay.appendChild(card);

    // Event listeners: click outside to close, Esc key
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) this.closeCard();
    });

    const keyHandler = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        this.closeCard();
      } else if (e.key === "Tab") {
        this.trapFocus(e, card);
      }
    };
    this.overlayKeyHandler = keyHandler;
    window.addEventListener("keydown", keyHandler);

    this.shadowRoot.appendChild(overlay);
    this.overlay = overlay;

    // Focus first action button
    listenBtn.focus();
    this.announce(
      `Textul a fost clarificat. ${data.key_phrases?.length || 0} concepte importante evidențiate.`,
    );
  }

  /**
   * Safely renders body content using DOM elements and text nodes (NO innerHTML with AI text)
   */
  renderBodyContent(container) {
    container.innerHTML = "";

    if (this.showingOriginal) {
      const p = document.createElement("p");
      p.className = "primazi-text";
      p.textContent = this.originalText;
      container.appendChild(p);
      return;
    }

    const data = this.currentData;
    if (!data) return;

    if (this.viewMode === "shorter") {
      // Shorter condensed view
      const p = document.createElement("p");
      p.className = "primazi-text";
      const shorterText =
        data.shorterText || adaptLocally(this.originalText, "shorter").text;
      const keyPhrases = data.shorterKeyPhrases?.length
        ? data.shorterKeyPhrases
        : data.key_phrases?.length
          ? data.key_phrases
          : extractKeyPhrases(shorterText);
      this.renderTextWithHighlights(p, shorterText, keyPhrases);
      container.appendChild(p);
    } else if (
      this.viewMode === "bullets" &&
      data.bullets &&
      data.bullets.length > 0
    ) {
      const ul = document.createElement("ul");
      ul.className = "primazi-bullets-list";
      for (const bullet of data.bullets) {
        const li = document.createElement("li");
        this.renderTextWithHighlights(li, bullet, data.key_phrases);
        ul.appendChild(li);
      }
      container.appendChild(ul);
    } else {
      const p = document.createElement("p");
      p.className = "primazi-text";
      const fullText = data.text || (data.bullets || []).join("\n");
      this.renderTextWithHighlights(p, fullText, data.key_phrases);
      container.appendChild(p);
    }

    // Render pragmatic notes (indirect requests, jokes, idioms)
    if (data.notes && data.notes.length > 0) {
      const notesContainer = document.createElement("div");
      notesContainer.className = "primazi-notes";

      for (const noteItem of data.notes) {
        const noteBox = document.createElement("div");
        noteBox.className = "primazi-note-card";

        const badge = document.createElement("span");
        badge.className = "primazi-note-badge";
        const kindLabel =
          {
            indirect_request: "Cerere politicoasă:",
            possible_joke: "Posibilă glumă (nesigur):",
            idiom: "Expresie figurată:",
            urgency: "Urgență:",
            softener: "Nuanță:",
          }[noteItem.kind] || "Notă:";
        badge.textContent = kindLabel;

        const noteText = document.createTextNode(
          ` „${noteItem.quote}” — ${noteItem.note}`,
        );
        noteBox.appendChild(badge);
        noteBox.appendChild(noteText);
        notesContainer.appendChild(noteBox);
      }
      container.appendChild(notesContainer);
    }
  }

  /**
   * Slices text into text nodes and <mark> elements for exact key phrases substrings.
   * Completely safe against XSS; zero innerHTML.
   */
  renderTextWithHighlights(targetNode, text, keyPhrases = []) {
    if (!keyPhrases || keyPhrases.length === 0) {
      targetNode.appendChild(document.createTextNode(text));
      return;
    }

    const sorted = [...new Set(keyPhrases)]
      .filter((p) => p && p.trim().length > 1)
      .sort((a, b) => b.length - a.length);

    if (sorted.length === 0) {
      targetNode.appendChild(document.createTextNode(text));
      return;
    }

    const pattern = sorted
      .map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join("|");
    const regex = new RegExp(`(${pattern})`, "gi");

    const parts = text.split(regex);
    for (const part of parts) {
      if (!part) continue;
      const isMatch = sorted.some(
        (k) => k.toLowerCase() === part.toLowerCase(),
      );
      if (isMatch) {
        const mark = document.createElement("mark");
        mark.className = "primazi-highlight";
        mark.appendChild(document.createTextNode(part));
        targetNode.appendChild(mark);
      } else {
        targetNode.appendChild(document.createTextNode(part));
      }
    }
  }

  /**
   * Trap Tab focus inside the active card
   */
  trapFocus(e, card) {
    const focusable = card.querySelectorAll(
      "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])",
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    const activeEl = this.shadowRoot?.activeElement || document.activeElement;
    if (e.shiftKey && activeEl === first) {
      last.focus();
      e.preventDefault();
    } else if (!e.shiftKey && activeEl === last) {
      first.focus();
      e.preventDefault();
    }
  }

  /**
   * Natural sentence-by-sentence Romanian TTS with reliable speech synthesis
   */
  toggleReadAloud(btn) {
    if (this.isSpeaking) {
      this.stopReadAloud(btn);
      this.announce("Redarea vocală a fost oprită.");
      return;
    }

    if (typeof window === "undefined" || !window.speechSynthesis) {
      this.announce("Sinteza vocală nu este suportată în acest browser.");
      return;
    }

    let textToRead = "";
    if (this.showingOriginal) {
      textToRead = this.originalText;
    } else if (this.viewMode === "shorter") {
      textToRead =
        this.currentData?.shorterText ||
        adaptLocally(this.originalText, "shorter").text;
    } else if (
      this.viewMode === "bullets" &&
      this.currentData?.bullets?.length
    ) {
      textToRead = this.currentData.bullets.join(". ");
    } else {
      textToRead = this.currentData?.text || this.originalText;
    }

    if (!textToRead) return;

    const sentences = splitSentencesRo(textToRead);
    if (!sentences.length) return;

    this.isSpeaking = true;
    this.ttsIndex = 0;
    this.ttsSentences = sentences;
    this.ttsBtn = btn;
    btn.textContent = "⏹️ Oprește";
    btn.classList.add("active");

    this.playNextTtsSentence();
    this.announce("Se citește textul cu voce tare.");
  }

  playNextTtsSentence() {
    if (!this.isSpeaking || !window.speechSynthesis) return;

    if (this.ttsIndex >= this.ttsSentences.length) {
      this.stopReadAloud(this.ttsBtn);
      return;
    }

    const raw = this.ttsSentences[this.ttsIndex];
    const normalized = normalizeRomanianForSpeech(raw);

    const utt = new SpeechSynthesisUtterance(normalized);
    utt.rate = Number(this.userPrefs?.prefs?.speech_rate) || 0.95;

    // Pick voice
    const voices = window.speechSynthesis.getVoices() || [];
    const roVoice = voices.find(
      (v) =>
        (v.lang && (v.lang === "ro-RO" || v.lang.startsWith("ro"))) ||
        /romanian|alina|emil/i.test(v.name),
    );

    if (roVoice) {
      utt.voice = roVoice;
      utt.lang = roVoice.lang;
    } else {
      utt.lang = "ro-RO";
      const defaultVoice = voices.find((v) => v.default);
      if (defaultVoice) utt.voice = defaultVoice;
    }

    utt.onend = () => {
      if (this.isSpeaking) {
        this.ttsIndex++;
        setTimeout(() => this.playNextTtsSentence(), 200);
      }
    };

    utt.onerror = (e) => {
      if (e.error !== "canceled" && e.error !== "interrupted") {
        console.warn("TTS sentence error:", e);
        if (this.isSpeaking) {
          this.ttsIndex++;
          this.playNextTtsSentence();
        }
      }
    };

    this.currentUtterance = utt;
    try {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utt);
    } catch (err) {
      console.warn("speechSynthesis speak failed:", err);
      this.stopReadAloud(this.ttsBtn);
    }
  }

  stopReadAloud(btn) {
    this.isSpeaking = false;
    this.currentUtterance = null;
    this.ttsSentences = [];
    this.ttsIndex = 0;
    if (typeof window !== "undefined" && window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel();
      } catch (_) {}
    }
    const b = btn || this.ttsBtn;
    if (b) {
      b.textContent = "🔊 Ascultă";
      b.classList.remove("active");
    }
  }

  closeCard() {
    this.stopReadAloud();
    if (this.overlayKeyHandler) {
      window.removeEventListener("keydown", this.overlayKeyHandler);
      this.overlayKeyHandler = null;
    }
    if (this.overlay) {
      this.overlay.remove();
      this.overlay = null;
    }
    this.bodyContainer = null;
    if (
      this.lastActiveElement &&
      typeof this.lastActiveElement.focus === "function"
    ) {
      this.lastActiveElement.focus();
    }
  }
}
