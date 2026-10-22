/**
 * Preferences Engine: Storage Management (owner: p2).
 * Persists state in localStorage with resilient in-memory fallback.
 * Never throws on storage quotas, private window restrictions, or disabled storage.
 */

import { STORAGE_KEY, createDefaultState } from "./types.js";
import { migrate } from "./migrate.js";

let memoryFallbackState = null;
let usingMemoryFallback = false;

/**
 * Safe check for localStorage availability.
 * @returns {boolean}
 */
function isLocalStorageWorking() {
  try {
    if (typeof globalThis.localStorage === "undefined" || globalThis.localStorage === null) {
      return false;
    }
    const testKey = "__wp_storage_probe__";
    globalThis.localStorage.setItem(testKey, "1");
    globalThis.localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/**
 * Checks whether the engine is currently using in-memory fallback storage.
 * @returns {boolean}
 */
export function isUsingMemoryFallback() {
  return usingMemoryFallback;
}

/**
 * Saves preference state to localStorage or in-memory fallback.
 *
 * @param {object} state - Preference state to save
 * @returns {object} The saved state
 */
export function savePrefs(state) {
  const safeState = migrate(state);
  safeState.updatedAt = new Date().toISOString();
  const serialized = JSON.stringify(safeState);

  if (!usingMemoryFallback && isLocalStorageWorking()) {
    try {
      globalThis.localStorage.setItem(STORAGE_KEY, serialized);
      return safeState;
    } catch {
      // Storage failed (e.g. QuotaExceededError or SecurityError) -> switch to memory fallback
      usingMemoryFallback = true;
      memoryFallbackState = safeState;
      return safeState;
    }
  }

  // Memory fallback path
  usingMemoryFallback = true;
  memoryFallbackState = safeState;
  return safeState;
}

/**
 * Loads preference state from localStorage or in-memory fallback.
 *
 * @returns {object} Validated preference state
 */
export function loadPrefs() {
  if (usingMemoryFallback) {
    return memoryFallbackState ? migrate(memoryFallbackState) : createDefaultState();
  }

  if (!isLocalStorageWorking()) {
    usingMemoryFallback = true;
    return memoryFallbackState ? migrate(memoryFallbackState) : createDefaultState();
  }

  let raw = null;
  try {
    raw = globalThis.localStorage.getItem(STORAGE_KEY);
  } catch {
    usingMemoryFallback = true;
    return memoryFallbackState ? migrate(memoryFallbackState) : createDefaultState();
  }

  if (!raw) {
    return createDefaultState();
  }

  try {
    const parsed = JSON.parse(raw);
    return migrate(parsed);
  } catch {
    // Corrupt JSON in storage: return defaults without permanently breaking localStorage
    return createDefaultState();
  }
}

/**
 * Clears stored preferences.
 */
export function clearPrefs() {
  memoryFallbackState = null;
  usingMemoryFallback = false;
  try {
    if (typeof globalThis.localStorage !== "undefined" && globalThis.localStorage !== null) {
      globalThis.localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // Ignore storage clear errors
  }
}

/**
 * Exports preference state as formatted JSON string.
 * @returns {string} JSON string
 */
export function exportPrefsJson() {
  const state = loadPrefs();
  return JSON.stringify(state, null, 2);
}

/**
 * Imports preference state from a JSON string.
 *
 * @param {string} jsonString - Formatted or raw JSON string
 * @returns {object} Imported and validated state
 */
export function importPrefsJson(jsonString) {
  if (typeof jsonString !== "string") {
    throw new TypeError("importPrefsJson expects a string argument");
  }
  const parsed = JSON.parse(jsonString);
  const migrated = migrate(parsed);
  return savePrefs(migrated);
}

