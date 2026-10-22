/**
 * Preferences Engine: Types, Constants, and Defaults (owner: p2).
 * Storage key wp.prefs.v1, schema version 1.
 * Strict privacy: comfort questions only, no health/diagnosis data.
 */

export const STORAGE_KEY = "wp.prefs.v1";
export const SCHEMA_VERSION = 1;

export const DEFAULT_ANSWERS = Object.freeze({
  readingPace: "medium", // "slow" | "medium" | "fast"
  textAmount: "medium", // "short" | "medium" | "full"
  stepByStep: true, // boolean
  visualNoise: "normal", // "low" | "normal"
  sensory: "normal", // "quiet" | "normal"
  language: "ro", // "ro" | "en"
  timeToDecide: "normal", // "need-more-time" | "normal"
});

export const DEFAULT_PREFS = Object.freeze({
  theme: "system", // "light" | "dark" | "high-contrast-light" | "system" | "high-contrast"
  textSize: "m", // "m" | "l" | "xl" | "xxl"
  spacing: "comfortable", // "comfortable" | "roomy"
  contrast: "normal", // "normal" | "high" | "high-dark" | "high-light"
  motion: "full", // "reduced" | "full"
  font: "default", // "default" | "readable" | "dyslexic" | "opendyslexic" | "lexend"
  density: "full", // "focused" | "full"
  language: "ro", // "ro" | "en"
  sidebar: "open", // "open" | "collapsed"
  bionic: false,
  highlightKeyTerms: false,
  readingRuler: false,
});

export const VALID_ANSWERS = Object.freeze({
  readingPace: ["slow", "medium", "fast"],
  textAmount: ["short", "medium", "full"],
  stepByStep: [true, false],
  visualNoise: ["low", "normal"],
  sensory: ["quiet", "normal"],
  language: ["ro", "en"],
  timeToDecide: ["need-more-time", "normal"],
});

export const VALID_PREFS = Object.freeze({
  theme: ["light", "dark", "high-contrast-light", "system", "high-contrast"],
  textSize: ["m", "l", "xl", "xxl"],
  spacing: ["comfortable", "roomy"],
  contrast: ["normal", "high", "high-dark", "high-light"],
  motion: ["reduced", "full"],
  font: ["default", "readable", "dyslexic", "opendyslexic", "lexend"],
  density: ["focused", "full"],
  language: ["ro", "en"],
  sidebar: ["open", "collapsed"],
});

/**
 * Creates a fresh default state object.
 * @returns {object} Full preference state
 */
export function createDefaultState() {
  return {
    version: SCHEMA_VERSION,
    updatedAt: new Date().toISOString(),
    answers: { ...DEFAULT_ANSWERS },
    prefs: { ...DEFAULT_PREFS },
    overrides: [],
  };
}
