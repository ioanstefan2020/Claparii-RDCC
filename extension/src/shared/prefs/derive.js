/**
 * Preferences Engine: Pure derivation logic (owner: p2).
 * Maps plain-language comfort answers into UI comfort preferences.
 * Preserves explicit manual user overrides.
 */

import { DEFAULT_ANSWERS, DEFAULT_PREFS, VALID_PREFS } from "./types.js";

/**
 * Pure function deriving CSS and UI preferences from user comfort answers.
 * Preserves user overrides from currentPrefs.
 *
 * @param {object} answers - Comfort answers object
 * @param {object} [currentPrefs={}] - Existing preferences (for override values)
 * @param {Array<string>} [overrides=[]] - List of keys manually overridden by user
 * @returns {object} Derived preferences object
 */
export function derivePrefs(answers = {}, currentPrefs = {}, overrides = []) {
  const safeAnswers = { ...DEFAULT_ANSWERS, ...(answers || {}) };
  const derived = { ...DEFAULT_PREFS };

  // Language mapping
  if (safeAnswers.language === "en") {
    derived.language = "en";
  } else {
    derived.language = "ro";
  }

  // Reading pace -> text size & spacing
  if (safeAnswers.readingPace === "slow") {
    derived.textSize = "l";
    derived.spacing = "roomy";
  } else if (safeAnswers.readingPace === "fast") {
    derived.textSize = "m";
    derived.spacing = "comfortable";
  } else {
    derived.textSize = "m";
    derived.spacing = "comfortable";
  }

  // Text amount -> density
  if (safeAnswers.textAmount === "short") {
    derived.density = "focused";
  } else {
    derived.density = "full";
  }

  // Visual noise -> contrast, font, motion
  if (safeAnswers.visualNoise === "low") {
    derived.contrast = "high";
    derived.font = "readable";
    derived.motion = "reduced";
  }

  // Sensory -> motion
  if (safeAnswers.sensory === "quiet") {
    derived.motion = "reduced";
  }

  // Strictly preserve manual user overrides
  if (Array.isArray(overrides) && currentPrefs && typeof currentPrefs === "object") {
    for (const key of overrides) {
      if (
        Object.prototype.hasOwnProperty.call(currentPrefs, key) &&
        VALID_PREFS[key]?.includes(currentPrefs[key])
      ) {
        derived[key] = currentPrefs[key];
      }
    }
  }

  return derived;
}

