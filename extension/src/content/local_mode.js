/**
 * local_mode.js - Deterministic offline adaptation engine
 * Fallback when backend is unavailable or user activates "Keep text on device".
 * Does NOT call external APIs. Uses local heuristics, regexes, and rule-based shortening.
 */

const IMPORTANT_WORDS_RO = [
  "urgent", "termen", "termen limită", "până la", "vineri", "luni", "marți", "miercuri", "joi",
  "ora", "important", "obligatoriu", "formular", "raport", "completat", "trimite", "responsabil",
  "procedură", "ședință", "aprobare", "decizie", "termen:", "atenție", "cerință", "contact"
];

const NUMBER_DATE_REGEX = /\b(?:\d{1,2}[:.]\d{2}|\d{1,2}\s+(?:ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie)|\d+(?:[.,]\d+)?\s*(?:lei|ron|eur|euro|%|kg|km|zile|ore|minute)|F-\d+|\b\d+\b)/gi;

const FILLERS_RO = [
  /\bvă informăm că\b/gi,
  /\bvă aducem la cunoștință că\b/gi,
  /\bmenționăm faptul că\b/gi,
  /\bîn ceea ce privește\b/gi,
  /\beste de reținut faptul că\b/gi,
  /\bse solicită cu amabilitate\b/gi,
  /\bîn vederea asigurării\b/gi,
  /\bcu privire la\b/gi
];

/**
 * Split text into distinct sentences.
 */
export function splitSentences(text) {
  if (!text) return [];
  return text
    .split(/(?<=[.!?])\s+|\n+/)
    .map(s => s.trim())
    .filter(s => s.length > 0);
}

/**
 * Extract key phrases (dates, numbers, important operational terms)
 * that exist as EXACT substrings in the text.
 */
export function extractKeyPhrases(text) {
  if (!text) return [];
  const matches = new Set();

  // 1. Numbers, dates, currencies
  const numberMatches = text.match(NUMBER_DATE_REGEX) || [];
  for (const nm of numberMatches) {
    if (nm.trim().length > 1) {
      matches.add(nm.trim());
    }
  }

  // 2. Important words
  for (const word of IMPORTANT_WORDS_RO) {
    const regex = new RegExp(`\\b${word}\\b`, "i");
    const m = text.match(regex);
    if (m) {
      matches.add(m[0]);
    }
  }

  return Array.from(matches).slice(0, 8);
}

/**
 * Clean up wordy bureaucratic Romanian fillers
 */
export function cleanFillers(text) {
  let cleaned = text;
  for (const pattern of FILLERS_RO) {
    cleaned = cleaned.replace(pattern, "");
  }
  return cleaned.replace(/\s{2,}/g, " ").trim();
}

/**
 * Basic readability score (approximate Flesch-Kincaid based on sentence and word length)
 */
export function estimateReadability(text) {
  const sentences = splitSentences(text);
  if (sentences.length === 0) return 50.0;
  const words = text.split(/\s+/).filter(Boolean);
  if (words.length === 0) return 50.0;

  const wordsPerSentence = words.length / sentences.length;
  // Lower words per sentence yields higher ease score
  let score = 90 - (wordsPerSentence * 2.2);
  return Math.max(10, Math.min(95, Math.round(score * 10) / 10));
}

/**
 * Main local adaptation function conforming to EXTENSION.md §3.6
 */
export function adaptLocally(text, action = "simplify") {
  const raw = (text || "").trim();
  const sentences = splitSentences(raw);
  const beforeScore = estimateReadability(raw);

  let adaptedText = "";
  let bullets = [];

  if (action === "bullets") {
    bullets = sentences.map(s => {
      let cleaned = cleanFillers(s);
      return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
    });
    adaptedText = bullets.join("\n");
  } else if (action === "shorter") {
    // Keep first sentence and any sentences containing numbers/dates/terms
    const kept = [];
    for (let i = 0; i < sentences.length; i++) {
      const s = sentences[i];
      if (i === 0 || NUMBER_DATE_REGEX.test(s) || IMPORTANT_WORDS_RO.some(w => s.toLowerCase().includes(w))) {
        kept.push(cleanFillers(s));
      }
    }
    const finalSentences = kept.length > 0 ? kept : sentences.slice(0, 2);
    adaptedText = finalSentences.join(" ");
    bullets = finalSentences.map(s => s.trim());
  } else {
    // simplify
    const simplifiedSentences = sentences.map(s => {
      let cleaned = cleanFillers(s);
      return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
    });
    adaptedText = simplifiedSentences.join(" ");
    bullets = simplifiedSentences.slice(0, 5);
  }

  const keyPhrases = extractKeyPhrases(adaptedText);
  const afterScore = estimateReadability(adaptedText);

  return {
    request_id: `local-${Date.now()}`,
    language: "ro",
    text: adaptedText,
    key_phrases: keyPhrases,
    bullets: bullets,
    notes: [],
    warnings: [],
    metrics: {
      readability_before: beforeScore,
      readability_after: Math.max(beforeScore, afterScore)
    },
    mode: "local"
  };
}
