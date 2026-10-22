/**
 * PrimaZi — Motor & Input Accessibility Engine (Wave 2)
 * Keyboard shortcuts (? for help dialog, no single-key by default), target sizes/gaps,
 * and optional Romanian voice commands via Web Speech API.
 * Ref: docs/TASKS-WAVE2.md A9, docs/SETTINGS-SPEC.md §6
 */

import { getSetting } from "./settings.js";

let voiceRecognition = null;
let isVoiceListening = false;

export function initKeyboardShortcuts(shortcuts = {}) {
  if (typeof document === "undefined") return;

  document.addEventListener("keydown", (e) => {
    // If typing in input or textarea, ignore shortcuts
    const tag = e.target.tagName.toLowerCase();
    if (tag === "input" || tag === "textarea" || e.target.isContentEditable) {
      return;
    }

    // '?' opens shortcuts help dialog
    if (e.key === "?" || (e.shiftKey && e.key === "/")) {
      showShortcutsDialog(shortcuts);
      return;
    }

    // Multi-key shortcuts (Alt+Key or Ctrl+Key or registered callback)
    const key = e.key.toLowerCase();
    if (shortcuts[key] && (e.altKey || e.ctrlKey || getSetting("single_key_shortcuts"))) {
      e.preventDefault();
      try { shortcuts[key](); } catch (_) {}
    }
  });
}

export function showShortcutsDialog(shortcuts = {}) {
  let modal = document.getElementById("a11y-shortcuts-dialog");
  if (!modal) {
    modal = document.createElement("dialog");
    modal.id = "a11y-shortcuts-dialog";
    modal.className = "a11y-dialog";
    modal.setAttribute("aria-label", "Scurtături de tastatură");

    const header = document.createElement("h2");
    header.textContent = "Scurtături de tastatură";
    modal.appendChild(header);

    const list = document.createElement("ul");
    list.innerHTML = `
      <li><kbd>?</kbd> — Deschide acest ghid de scurtături</li>
      <li><kbd>Esc</kbd> — Oprește citirea vocală sau închide panourile</li>
      <li><kbd>Alt</kbd> + <kbd>→</kbd> — Următorul pas (în modul ghidat)</li>
      <li><kbd>Alt</kbd> + <kbd>←</kbd> — Pasul anterior</li>
      <li><kbd>Alt</kbd> + <kbd>S</kbd> — Salvează / exportă</li>
    `;
    modal.appendChild(list);

    const btnClose = document.createElement("button");
    btnClose.type = "button";
    btnClose.className = "btn btn-primary";
    btnClose.textContent = "Am înțeles";
    btnClose.onclick = () => modal.close();
    modal.appendChild(btnClose);

    document.body.appendChild(modal);
  }

  modal.showModal();
}

/**
 * Optional Romanian voice commands via Web Speech API (off by default).
 */
export function initVoiceCommands(handlers = {}) {
  const SpeechRecognition = typeof window !== "undefined" ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;
  if (!SpeechRecognition) return null;

  try {
    const recognition = new SpeechRecognition();
    recognition.lang = "ro-RO";
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onresult = (e) => {
      const last = e.results[e.results.length - 1];
      if (last && last[0]) {
        const transcript = last[0].transcript.trim().toLowerCase();

        if (transcript.includes("următorul") && handlers.next) handlers.next();
        else if (transcript.includes("înapoi") && handlers.prev) handlers.prev();
        else if (transcript.includes("citește") && handlers.read) handlers.read();
        else if (transcript.includes("oprește") && handlers.stop) handlers.stop();
        else if (transcript.includes("salvează") && handlers.save) handlers.save();
      }
    };

    voiceRecognition = recognition;
    return recognition;
  } catch (err) {
    return null;
  }
}

export function startVoiceCommands() {
  if (voiceRecognition && !isVoiceListening) {
    try {
      voiceRecognition.start();
      isVoiceListening = true;
    } catch (_) {}
  }
}

export function stopVoiceCommands() {
  if (voiceRecognition && isVoiceListening) {
    try {
      voiceRecognition.stop();
      isVoiceListening = false;
    } catch (_) {}
  }
}
