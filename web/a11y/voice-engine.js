/**
 * voice-engine.js - Low-Latency Romanian Speech Synthesizer & Element Announcer
 * Project: Limpede (Hackathon 2026)
 *
 * Designed for Blind Mode and Keyboard/Touch Screen Reading:
 * - Immediate cancellation on rapid navigation (no speech backlog)
 * - Romanian voice preference scoring (Natural Alina / Emil)
 * - Mobile touch/gesture audio unlocking
 * - Natural cadence & normalization
 */

import { formatElementAnnouncementRo, scoreVoice } from "./voiceover-core.js";
import { normalizeRomanianForSpeech } from "./tts-normalize-ro.js";

class VoiceEngine {
  constructor() {
    this.synth = typeof window !== "undefined" ? window.speechSynthesis : null;
    this.currentUtterance = null;
    this.cachedVoice = null;
    this.isUnlocked = false;
    this.enabled = true;
    this.rate = 1.0;
    this.pitch = 1.0;
    this.volume = 1.0;

    if (this.synth) {
      if (typeof this.synth.onvoiceschanged !== "undefined") {
        this.synth.onvoiceschanged = () => {
          this.cachedVoice = null;
          this.getBestVoice();
        };
      }
    }

    this._setupMobileUnlock();
  }

  _setupMobileUnlock() {
    if (typeof window === "undefined") return;
    const unlock = () => {
      if (this.isUnlocked) return;
      this.isUnlocked = true;
      if (this.synth) {
        try {
          const silentUtt = new SpeechSynthesisUtterance("");
          silentUtt.volume = 0;
          this.synth.speak(silentUtt);
        } catch (_) {}
      }
      window.removeEventListener("touchstart", unlock, true);
      window.removeEventListener("keydown", unlock, true);
      window.removeEventListener("click", unlock, true);
    };

    window.addEventListener("touchstart", unlock, { once: true, capture: true, passive: true });
    window.addEventListener("keydown", unlock, { once: true, capture: true, passive: true });
    window.addEventListener("click", unlock, { once: true, capture: true, passive: true });
  }

  getBestVoice() {
    if (this.cachedVoice) return this.cachedVoice;
    if (!this.synth) return null;

    const voices = this.synth.getVoices() || [];
    if (!voices.length) return null;

    let best = null;
    let maxScore = -1;

    for (const v of voices) {
      const score = scoreVoice(v);
      if (score > maxScore) {
        maxScore = score;
        best = v;
      }
    }

    this.cachedVoice = best;
    return best;
  }

  /**
   * Immediately stops any current speech.
   */
  stop() {
    if (this.synth) {
      try {
        this.synth.cancel();
      } catch (_) {}
    }
    this.currentUtterance = null;
  }

  /**
   * Speaks given text in Romanian, immediately preempting previous speech.
   * @param {string} text
   * @param {object} [opts]
   */
  speak(text, opts = {}) {
    if (!text || !this.enabled) return;
    const cleanText = normalizeRomanianForSpeech(String(text).trim());
    if (!cleanText) return;

    if (!this.synth) {
      // Fallback to server audio if available
      this._speakServerFallback(cleanText);
      return;
    }

    // Cancel current speech immediately so rapid Tab navigation doesn't queue up
    try {
      this.synth.cancel();
    } catch (_) {}

    const utt = new SpeechSynthesisUtterance(cleanText);
    const voice = this.getBestVoice();
    if (voice) {
      utt.voice = voice;
      utt.lang = voice.lang;
    } else {
      utt.lang = "ro-RO";
    }

    utt.rate = typeof opts.rate === "number" ? opts.rate : this.rate;
    utt.pitch = typeof opts.pitch === "number" ? opts.pitch : this.pitch;
    utt.volume = typeof opts.volume === "number" ? opts.volume : this.volume;

    utt.onstart = () => {
      if (opts.onStart) opts.onStart();
    };
    utt.onend = () => {
      if (this.currentUtterance === utt) {
        this.currentUtterance = null;
      }
      if (opts.onEnd) opts.onEnd();
    };
    utt.onerror = (e) => {
      if (this.currentUtterance === utt) {
        this.currentUtterance = null;
      }
      if (opts.onError) opts.onError(e);
    };

    // Keep reference on instance to prevent garbage collection in Chrome/WebKit
    this.currentUtterance = utt;

    try {
      this.synth.speak(utt);
    } catch (e) {
      this._speakServerFallback(cleanText);
    }
  }

  /**
   * Formats and speaks an element's accessible name and role.
   * @param {HTMLElement} el
   */
  speakElement(el) {
    if (!el) return;
    const announcement = formatElementAnnouncementRo(el);
    if (announcement) {
      this.speak(announcement);
    }
  }

  /**
   * Fallback using /api/tts endpoint if browser SpeechSynthesis is not supported.
   */
  async _speakServerFallback(text) {
    if (typeof window === "undefined" || !window.fetch) return;
    try {
      const resp = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice: "ro-mihai", rate: this.rate }),
      });
      if (resp.ok) {
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play().catch(() => {});
      }
    } catch (_) {}
  }

  isSpeaking() {
    return Boolean(this.synth && this.synth.speaking);
  }
}

export const voiceEngine = new VoiceEngine();
if (typeof window !== "undefined") {
  window.LimpedeVoiceEngine = voiceEngine;
}
