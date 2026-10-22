/**
 * speech.js - Browser Speech Synthesis (TTS) & Recognition Wrapper
 * Owner: p2
 *
 * Rules:
 * - Uses browser Web Speech API (ro-RO)
 * - Graceful fallback when speech synthesis or recognition is unsupported
 * - Text-only; NO emotion inference
 */

/**
 * Checks if Speech Synthesis (Text to Speech) is available.
 */
export function isSynthesisSupported() {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

/**
 * Finds a Romanian voice (ro-RO) or falls back to standard voice.
 */
function getRomanianVoice() {
  if (!isSynthesisSupported()) return null;
  const voices = window.speechSynthesis.getVoices();
  const roVoice = voices.find(v => v.lang.startsWith("ro"));
  return roVoice || null;
}

/**
 * Reads text aloud using speech synthesis.
 */
export function speakText(text, options = {}) {
  if (!isSynthesisSupported() || !text) {
    if (options.onError) options.onError("Sinteza vocală nu este suportată pe acest dispozitiv.");
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "ro-RO";
  utterance.rate = options.rate || 0.95; // Slightly slower for better clarity
  utterance.pitch = 1.0;

  const voice = getRomanianVoice();
  if (voice) {
    utterance.voice = voice;
  }

  if (options.onStart) utterance.onstart = options.onStart;
  if (options.onEnd) utterance.onend = options.onEnd;
  if (options.onError) utterance.onerror = options.onError;

  window.speechSynthesis.speak(utterance);
}

/**
 * Stops any active speech synthesis.
 */
export function stopSpeaking() {
  if (isSynthesisSupported()) {
    window.speechSynthesis.cancel();
  }
}

/**
 * Pauses active speech synthesis.
 */
export function pauseSpeaking() {
  if (isSynthesisSupported() && window.speechSynthesis.speaking) {
    window.speechSynthesis.pause();
  }
}

/**
 * Resumes paused speech synthesis.
 */
export function resumeSpeaking() {
  if (isSynthesisSupported() && window.speechSynthesis.paused) {
    window.speechSynthesis.resume();
  }
}

/**
 * Checks if speech synthesis is currently active (speaking or paused).
 * @returns {boolean}
 */
export function isSpeaking() {
  return isSynthesisSupported() && window.speechSynthesis.speaking;
}

/**
 * Checks if speech synthesis is currently paused.
 * @returns {boolean}
 */
export function isPaused() {
  return isSynthesisSupported() && window.speechSynthesis.paused;
}

/**
 * Checks if Web Speech Recognition (voice-to-text) is supported.
 */
export function isRecognitionSupported() {
  if (typeof window === "undefined") return false;
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
}

/**
 * Creates and starts a speech recognizer.
 */
export function createSpeechRecognizer({ onResult, onError, onEnd, onStart }) {
  if (!isRecognitionSupported()) {
    return {
      start: () => {
        if (onError) onError("Recunoașterea vocală nu este suportată de acest browser. Puteți introduce textul manual.");
      },
      stop: () => {}
    };
  }

  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognizer = new SpeechRec();
  recognizer.lang = "ro-RO";
  recognizer.continuous = true;
  recognizer.interimResults = true;

  if (onStart) recognizer.onstart = onStart;
  if (onEnd) recognizer.onend = onEnd;

  recognizer.onerror = (event) => {
    if (onError) onError(`Eroare microfon: ${event.error}`);
  };

  recognizer.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      transcript += event.results[i][0].transcript;
    }
    if (onResult) onResult(transcript, event.results[event.results.length - 1].isFinal);
  };

  return {
    start: () => recognizer.start(),
    stop: () => recognizer.stop()
  };
}
