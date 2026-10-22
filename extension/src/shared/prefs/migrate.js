/**
 * Preferences Engine: Migration and State Reset (owner: p2).
 * Defensively migrates and sanitizes raw storage data against corruption or schema changes.
 */

import {
  SCHEMA_VERSION,
  DEFAULT_ANSWERS,
  DEFAULT_PREFS,
  VALID_ANSWERS,
  VALID_PREFS,
  createDefaultState,
} from "./types.js";
import { derivePrefs } from "./derive.js";

/**
 * Sanitizes and migrates any raw payload into a valid v1 state.
 * Any missing or corrupt fields are safely replaced with defaults.
 *
 * @param {any} raw - Parsed JSON object from storage or import
 * @returns {object} Validated, clean preference state
 */
export function migrate(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return createDefaultState();
  }

  // Schema version check: only version 1 supported; unknown versions return default state
  if (raw.version !== SCHEMA_VERSION) {
    return createDefaultState();
  }

  // Validate answers
  const rawAnswers =
    raw.answers &&
    typeof raw.answers === "object" &&
    !Array.isArray(raw.answers)
      ? raw.answers
      : {};
  const cleanAnswers = { ...DEFAULT_ANSWERS };

  for (const [key, allowed] of Object.entries(VALID_ANSWERS)) {
    if (Object.prototype.hasOwnProperty.call(rawAnswers, key)) {
      const val = rawAnswers[key];
      if (allowed.includes(val)) {
        cleanAnswers[key] = val;
      }
    }
  }

  // Validate overrides (deduplicated)
  const rawOverrides = Array.isArray(raw.overrides) ? raw.overrides : [];
  const cleanOverrides = Array.from(
    new Set(
      rawOverrides.filter(
        (k) =>
          typeof k === "string" &&
          Object.prototype.hasOwnProperty.call(VALID_PREFS, k),
      ),
    ),
  );

  // Validate or derive prefs
  const rawPrefs =
    raw.prefs && typeof raw.prefs === "object" && !Array.isArray(raw.prefs)
      ? raw.prefs
      : null;

  let cleanPrefs;
  if (!rawPrefs || Object.keys(rawPrefs).length === 0) {
    cleanPrefs = derivePrefs(cleanAnswers, {}, cleanOverrides);
  } else {
    cleanPrefs = { ...DEFAULT_PREFS };
    for (const [key, allowed] of Object.entries(VALID_PREFS)) {
      if (Object.prototype.hasOwnProperty.call(rawPrefs, key)) {
        const val = rawPrefs[key];
        if (allowed.includes(val)) {
          cleanPrefs[key] = val;
        }
      }
    }
    if (typeof rawPrefs.bionic === "boolean")
      cleanPrefs.bionic = rawPrefs.bionic;
    if (typeof rawPrefs.highlightKeyTerms === "boolean")
      cleanPrefs.highlightKeyTerms = rawPrefs.highlightKeyTerms;
    if (typeof rawPrefs.readingRuler === "boolean")
      cleanPrefs.readingRuler = rawPrefs.readingRuler;
  }

  // Validate updatedAt
  let updatedAt = typeof raw.updatedAt === "string" ? raw.updatedAt : null;
  if (!updatedAt || Number.isNaN(Date.parse(updatedAt))) {
    updatedAt = new Date().toISOString();
  }

  return {
    version: SCHEMA_VERSION,
    updatedAt,
    answers: cleanAnswers,
    prefs: cleanPrefs,
    overrides: cleanOverrides,
  };
}

/**
 * Resets preferences to user answers by clearing all manual overrides and re-deriving prefs.
 *
 * @param {object} state - Current preference state
 * @returns {object} Fresh state with overrides = [] and re-derived prefs
 */
export function resetToAnswers(state) {
  const safeState = migrate(state);
  const rederivedPrefs = derivePrefs(safeState.answers, safeState.prefs, []);
  return {
    ...safeState,
    updatedAt: new Date().toISOString(),
    prefs: rederivedPrefs,
    overrides: [],
  };
}

/**
 * Factory reset: clears all settings and returns fresh default state.
 *
 * @returns {object} Factory default state
 */
export function resetAll() {
  return createDefaultState();
}
