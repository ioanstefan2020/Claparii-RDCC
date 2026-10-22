/**
 * PrimaZi — Natural-Sounding TTS Engine (Wave 2)
 * Sentence-by-sentence reading, follow-along highlight, speed/pitch/pause control,
 * Romanian voice selection (prefers Edge Natural voices), and global stop.
 * Ref: docs/TASKS-WAVE2.md A3, docs/SETTINGS-SPEC.md §4
 */

import { normalizeRomanianForSpeech } from "./tts-normalize-ro.js";
import { getSetting } from "./settings.js";

let synth = typeof window !== "undefined" ? window.speechSynthesis : null;
let currentUtterance = null;
let sentences = [];
let currentIndex = -1;
let isPlaying = false;
let isPaused = false;
let activeHighlightEl = null;

const sentenceListeners = new Set();
const boundaryListeners = new Set();
const stateListeners = new Set();

/**
 * Splits text into sentences cleanly for Romanian prose.
 */
export function splitSentencesRo(text) {
  if (!text) return [];
  // Match sentence endings followed by space/quote, avoiding abbreviations like etc., art., etc.
  const raw = text.replace(/([.?!])\s+(?=[A-ZĂÂÎȘȚ0-9])/g, "$1\n").split("\n");
  return raw.map(s => s.trim()).filter(Boolean);
}

/**
 * Finds the best available Romanian voice.
 * Prefers natural/online voices (e.g. Microsoft Alina/Emil Natural in Edge).
 */
export function getBestRomanianVoice() {
  if (!synth) return null;
  const voices = synth.getVoices() || [];
  if (voices.length === 0) return null;

  // 1. Romanian voices with Natural or Online in name
  const naturalRo = voices.find(v => (v.lang === "ro-RO" || v.lang.startsWith("ro")) && /natural|online/i.test(v.name));
  if (naturalRo) return naturalRo;

  // 2. Any Romanian voice
  const roVoice = voices.find(v => v.lang === "ro-RO" || v.lang.startsWith("ro"));
  if (roVoice) return roVoice;

  // 3. Fallback to default
  return voices.find(v => v.default) || voices[0] || null;
}

export function getAvailableVoices() {
  if (!synth) return [];
  return synth.getVoices() || [];
}

export function getTTSState() {
  return {
    isPlaying,
    isPaused,
    currentIndex,
    totalSentences: sentences.length,
    currentSentence: currentIndex >= 0 && currentIndex < sentences.length ? sentences[currentIndex] : null
  };
}

function notifyState() {
  const state = getTTSState();
  stateListeners.forEach(cb => {
    try { cb(state); } catch (_) {}
  });
}

function clearHighlight() {
  if (activeHighlightEl) {
    activeHighlightEl.classList.remove("tts-reading-sentence");
    activeHighlightEl = null;
  }
  document.querySelectorAll(".tts-reading-sentence").forEach(el => {
    el.classList.remove("tts-reading-sentence");
  });
}

/**
 * Stops any active speech synthesis and resets reading position.
 */
export function stop() {
  if (synth) {
    try { synth.cancel(); } catch (_) {}
  }
  isPlaying = false;
  isPaused = false;
  currentIndex = -1;
  sentences = [];
  currentUtterance = null;
  clearHighlight();
  notifyState();
}

/**
 * Pauses active speech.
 */
export function pause() {
  if (synth && isPlaying && !isPaused) {
    try { synth.pause(); } catch (_) {}
    isPaused = true;
    notifyState();
  }
}

/**
 * Resumes speech if paused.
 */
export function resume() {
  if (synth && isPlaying && isPaused) {
    try { synth.resume(); } catch (_) {}
    isPaused = false;
    notifyState();
  } else if (!isPlaying && sentences.length > 0 && currentIndex >= 0) {
    playSentence(currentIndex);
  }
}

/**
 * Advances to next sentence.
 */
export function next() {
  if (currentIndex + 1 < sentences.length) {
    playSentence(currentIndex + 1);
  } else {
    stop();
  }
}

/**
 * Goes back to previous sentence.
 */
export function prev() {
  if (currentIndex > 0) {
    playSentence(currentIndex - 1);
  }
}

function playSentence(index) {
  if (!synth || index < 0 || index >= sentences.length) {
    stop();
    return;
  }

  try { synth.cancel(); } catch (_) {}

  currentIndex = index;
  const rawSentence = sentences[index];
  const spokenText = getSetting("tts_spoken_numbers") ? normalizeRomanianForSpeech(rawSentence) : rawSentence;

  const rate = getSetting("tts_rate") || 0.95;
  const pitch = getSetting("tts_pitch") || 1.0;
  const volume = getSetting("tts_volume") || 1.0;
  const voice = getBestRomanianVoice();

  const utt = new SpeechSynthesisUtterance(spokenText);
  if (voice) utt.voice = voice;
  utt.lang = voice ? voice.lang : "ro-RO";
  utt.rate = rate;
  utt.pitch = pitch;
  utt.volume = volume;

  utt.onstart = () => {
    isPlaying = true;
    isPaused = false;
    sentenceListeners.forEach(cb => {
      try { cb(rawSentence, index, sentences.length); } catch (_) {}
    });
    notifyState();
  };

  utt.onboundary = (e) => {
    boundaryListeners.forEach(cb => {
      try { cb(e); } catch (_) {}
    });
  };

  utt.onend = () => {
    const pauseMs = getSetting("tts_pause_ms") || 350;
    if (currentIndex + 1 < sentences.length && isPlaying) {
      setTimeout(() => {
        if (isPlaying && !isPaused) {
          playSentence(currentIndex + 1);
        }
      }, pauseMs);
    } else {
      stop();
    }
  };

  utt.onerror = () => {
    stop();
  };

  currentUtterance = utt;
  synth.speak(utt);
}

/**
 * Starts reading text or an element's textContent.
 * @param {string|HTMLElement} nodeOrText
 * @param {object} options
 */
export function speak(nodeOrText, options = {}) {
  stop();

  let text = "";
  if (typeof nodeOrText === "string") {
    text = nodeOrText;
  } else if (nodeOrText && nodeOrText.textContent) {
    text = nodeOrText.textContent;
    activeHighlightEl = nodeOrText;
  }

  text = text.trim();
  if (!text) return;

  sentences = splitSentencesRo(text);
  if (sentences.length === 0) return;

  playSentence(0);
}

export function onSentence(cb) {
  if (typeof cb === "function") {
    sentenceListeners.add(cb);
    return () => sentenceListeners.delete(cb);
  }
  return () => {};
}

export function onBoundary(cb) {
  if (typeof cb === "function") {
    boundaryListeners.add(cb);
    return () => boundaryListeners.delete(cb);
  }
  return () => {};
}

export function onTTSStateChange(cb) {
  if (typeof cb === "function") {
    stateListeners.add(cb);
    return () => stateListeners.delete(cb);
  }
  return () => {};
}

// Global escape listener to halt speech immediately
if (typeof document !== "undefined") {
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isPlaying) {
      stop();
    }
  });
}
