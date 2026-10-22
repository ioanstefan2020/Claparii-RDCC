/**
 * Preferences Engine: Public API (owner: p2).
 * Unified barrel module exporting types, derivation, migration, storage, and DOM application.
 */

export {
  STORAGE_KEY,
  SCHEMA_VERSION,
  DEFAULT_ANSWERS,
  DEFAULT_PREFS,
  VALID_ANSWERS,
  VALID_PREFS,
  createDefaultState,
} from "./types.js";

export {
  derivePrefs,
} from "./derive.js";

export {
  migrate,
  resetToAnswers,
  resetAll,
} from "./migrate.js";

export {
  isUsingMemoryFallback,
  savePrefs,
  loadPrefs,
  clearPrefs,
  exportPrefsJson,
  importPrefsJson,
} from "./storage.js";

export {
  applyPrefs,
  getInlineHeadScript,
} from "./apply.js";

