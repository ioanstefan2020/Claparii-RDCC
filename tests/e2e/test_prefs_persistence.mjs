/**
 * E2E Preference Persistence Across Reload & Private Browsing Lifecycle (owner: p2).
 * Verifies the full user questionnaire submission, anti-FOUC inline head script execution,
 * quota/private window fallback resilience, corrupt storage healing, manual overrides preservation,
 * and JSON import/export cycles.
 *
 * Runs via standard Node.js test runner:
 *   node --test tests/e2e/test_prefs_persistence.mjs
 */

import test from "node:test";
import assert from "node:assert/strict";

import {
  STORAGE_KEY,
  SCHEMA_VERSION,
  DEFAULT_ANSWERS,
  DEFAULT_PREFS,
  createDefaultState,
  derivePrefs,
  migrate,
  resetToAnswers,
  resetAll,
  isUsingMemoryFallback,
  savePrefs,
  loadPrefs,
  clearPrefs,
  exportPrefsJson,
  importPrefsJson,
  getInlineHeadScript,
} from "../../web/js/prefs/index.js";

// In-memory mock localStorage factory
function createMockLocalStorage(options = {}) {
  const store = new Map();
  return {
    getItem: (key) => {
      if (options.throwOnGet) {
        const err = new Error("SecurityError: The operation is insecure or blocked in private browsing mode.");
        err.name = "SecurityError";
        throw err;
      }
      return store.has(key) ? store.get(key) : null;
    },
    setItem: (key, val) => {
      if (options.throwOnSet) {
        const err = new Error("QuotaExceededError: The quota has been exceeded for this storage origin.");
        err.name = "QuotaExceededError";
        throw err;
      }
      store.set(key, String(val));
    },
    removeItem: (key) => store.delete(key),
    clear: () => store.clear(),
    get _store() {
      return store;
    },
  };
}

// Unstyled DOM root element representation
function createMockRootElement() {
  const attributes = new Map();
  return {
    attributes,
    lang: "",
    setAttribute(name, val) {
      attributes.set(name, String(val));
    },
    getAttribute(name) {
      return attributes.get(name) || null;
    },
    removeAttribute(name) {
      attributes.delete(name);
    },
  };
}

test("Test 1: Full questionnaire submission -> derivePrefs -> savePrefs in localStorage key wp.prefs.v1", () => {
  globalThis.localStorage = createMockLocalStorage();
  clearPrefs();

  // 1. User answers all 7 comfort questions
  const userAnswers = {
    readingPace: "slow",
    textAmount: "short",
    stepByStep: true,
    visualNoise: "low",
    sensory: "quiet",
    language: "ro",
    timeToDecide: "need-more-time",
  };

  // 2. Preferences derived client-side
  const derived = derivePrefs(userAnswers);
  assert.equal(derived.textSize, "l", "slow reading pace must derive large text");
  assert.equal(derived.spacing, "roomy", "slow reading pace must derive roomy spacing");
  assert.equal(derived.contrast, "high", "low visual noise must derive high contrast");
  assert.equal(derived.font, "readable", "low visual noise must derive readable font");
  assert.equal(derived.motion, "reduced", "quiet sensory must derive reduced motion");
  assert.equal(derived.density, "focused", "short text amount must derive focused density");
  assert.equal(derived.language, "ro", "language must derive ro");

  // 3. Save state to localStorage
  const state = {
    version: 1,
    updatedAt: new Date().toISOString(),
    answers: userAnswers,
    prefs: derived,
    overrides: [],
  };
  savePrefs(state);

  // 4. Verify raw content in localStorage under key "wp.prefs.v1"
  const rawStored = globalThis.localStorage.getItem(STORAGE_KEY);
  assert.ok(rawStored, `Expected localStorage to contain key '${STORAGE_KEY}'`);
  const parsed = JSON.parse(rawStored);
  assert.equal(parsed.version, 1);
  assert.equal(parsed.prefs.textSize, "l");
  assert.equal(parsed.prefs.contrast, "high");

  clearPrefs();
});

test("Test 2: Simulated page reload: executes anti-FOUC script and sets data-* tokens and lang on root element", () => {
  const mockStorage = createMockLocalStorage();
  globalThis.localStorage = mockStorage;
  clearPrefs();

  // Populate persistent storage with custom user preferences
  const storedState = {
    version: 1,
    updatedAt: new Date().toISOString(),
    answers: { readingPace: "slow", visualNoise: "low" },
    prefs: {
      theme: "dark",
      textSize: "xl",
      spacing: "roomy",
      contrast: "high",
      motion: "reduced",
      font: "readable",
      density: "focused",
      language: "ro",
      sidebar: "collapsed",
    },
    overrides: ["textSize"],
  };
  mockStorage.setItem(STORAGE_KEY, JSON.stringify(storedState));

  // Simulate clean page reload: blank unstyled root element before body rendering
  const mockRoot = createMockRootElement();
  globalThis.document = {
    documentElement: mockRoot,
  };

  // Retrieve anti-FOUC snippet and execute it in fresh document environment
  const snippet = getInlineHeadScript();
  assert.ok(snippet && snippet.length > 50, "Inline head script must not be empty");

  // Execute snippet via new Function (isolated scope, synchronous execution)
  const executeSnippet = new Function(snippet);
  assert.doesNotThrow(() => {
    executeSnippet();
  }, "Inline head script must execute cleanly without runtime error");

  // Verify all data-* attributes stamped instantaneously onto rootElement
  assert.equal(mockRoot.getAttribute("data-theme"), "dark");
  assert.equal(mockRoot.getAttribute("data-text"), "xl");
  assert.equal(mockRoot.getAttribute("data-spacing"), "roomy");
  assert.equal(mockRoot.getAttribute("data-contrast"), "high");
  assert.equal(mockRoot.getAttribute("data-motion"), "reduced");
  assert.equal(mockRoot.getAttribute("data-font"), "readable");
  assert.equal(mockRoot.getAttribute("data-density"), "focused");
  assert.equal(mockRoot.getAttribute("data-sidebar"), "collapsed");
  assert.equal(mockRoot.getAttribute("lang"), "ro");

  clearPrefs();
});

test("Test 3: Private window QuotaExceededError transparently falls back to in-memory store without unhandled error", () => {
  // Set up mock localStorage that throws QuotaExceededError on setItem
  const quotaStorage = createMockLocalStorage({ throwOnSet: true });
  globalThis.localStorage = quotaStorage;
  clearPrefs();

  const customState = {
    version: 1,
    updatedAt: new Date().toISOString(),
    answers: { readingPace: "slow" },
    prefs: { ...DEFAULT_PREFS, textSize: "l", spacing: "roomy" },
    overrides: [],
  };

  // savePrefs must not throw QuotaExceededError
  assert.doesNotThrow(() => {
    savePrefs(customState);
  }, "savePrefs must catch QuotaExceededError transparently");

  // Should have cleanly transitioned to memory fallback
  assert.equal(isUsingMemoryFallback(), true, "Must activate memory fallback mode on storage exception");

  // loadPrefs must read from memory fallback without throwing
  const loadedFromMemory = loadPrefs();
  assert.equal(loadedFromMemory.answers.readingPace, "slow");
  assert.equal(loadedFromMemory.prefs.textSize, "l");
  assert.equal(loadedFromMemory.prefs.spacing, "roomy");

  // Subsequent updates to memory fallback must work seamlessly
  loadedFromMemory.prefs.theme = "dark";
  savePrefs(loadedFromMemory);
  const reloadedFromMemory = loadPrefs();
  assert.equal(reloadedFromMemory.prefs.theme, "dark");

  clearPrefs();
});

test("Test 4: Corrupt JSON recovery: sets malformed JSON in storage, verifies loadPrefs() migrates to safe defaults without throwing", () => {
  const store = createMockLocalStorage();
  globalThis.localStorage = store;
  clearPrefs();

  // Set malformed corrupted payload
  store.setItem(STORAGE_KEY, "INVALID_RAW_JSON_PAYLOAD_%%%{{{}}}}}");

  // loadPrefs must heal and return safe default state without crashing
  let state = null;
  assert.doesNotThrow(() => {
    state = loadPrefs();
  }, "loadPrefs must not throw SyntaxError on corrupt JSON");

  assert.ok(state !== null);
  assert.equal(state.version, SCHEMA_VERSION);
  assert.deepEqual(state.answers, DEFAULT_ANSWERS);
  assert.deepEqual(state.prefs, DEFAULT_PREFS);
  assert.deepEqual(state.overrides, []);
  assert.equal(isUsingMemoryFallback(), false, "Corrupt JSON should not disable working localStorage");

  // Subsequent save heals the storage with clean, valid JSON
  savePrefs(state);
  const rawAfterHeal = store.getItem(STORAGE_KEY);
  assert.doesNotThrow(() => {
    JSON.parse(rawAfterHeal);
  }, "Storage must now contain valid serialized JSON");

  clearPrefs();
});

test("Test 5: Manual overrides preservation: sets manual override (e.g. textSize: xl), triggers re-derivation, verifies override is strictly preserved", () => {
  globalThis.localStorage = createMockLocalStorage();
  clearPrefs();

  // User initially completed questionnaire with slow pace (derives textSize: "l", spacing: "roomy")
  const initialAnswers = { readingPace: "slow", visualNoise: "normal" };
  const initialPrefs = derivePrefs(initialAnswers);
  assert.equal(initialPrefs.textSize, "l");

  // Later, user explicitly changes font size slider to "xl" in settings (manual override)
  const currentPrefs = { ...initialPrefs, textSize: "xl" };
  const overrides = ["textSize"];

  // Now, user updates questionnaire with fast pace and low visual noise
  const newAnswers = { readingPace: "fast", visualNoise: "low" };

  // Re-derivation with overrides parameter
  const rederived = derivePrefs(newAnswers, currentPrefs, overrides);

  // textSize MUST stay "xl" (preserved by override)
  assert.equal(rederived.textSize, "xl", "Manual textSize override 'xl' must be preserved");
  // Non-overridden preferences MUST update according to new answers
  assert.equal(rederived.spacing, "comfortable", "Spacing must update to fast pace default");
  assert.equal(rederived.contrast, "high", "Contrast must update to low visual noise default");
  assert.equal(rederived.font, "readable", "Font must update to low visual noise default");

  // Save to persistent storage with override recorded
  const state = {
    version: 1,
    answers: newAnswers,
    prefs: rederived,
    overrides: ["textSize"],
  };
  savePrefs(state);

  // Reload from storage
  const reloaded = loadPrefs();
  assert.deepEqual(reloaded.overrides, ["textSize"]);
  assert.equal(reloaded.prefs.textSize, "xl");
  assert.equal(reloaded.prefs.spacing, "comfortable");

  clearPrefs();
});

test("Test 6: Private window read restrictions (getItem throws SecurityError) & undefined localStorage", () => {
  // 1. Simulate strict read lockout (getItem throws SecurityError)
  const lockedStorage = createMockLocalStorage({ throwOnGet: true });
  globalThis.localStorage = lockedStorage;
  clearPrefs();

  let loaded = null;
  assert.doesNotThrow(() => {
    loaded = loadPrefs();
  }, "loadPrefs must not throw when getItem throws SecurityError");
  assert.equal(isUsingMemoryFallback(), true, "Must switch to memory fallback when reading throws");
  assert.equal(loaded.version, SCHEMA_VERSION);

  // 2. Simulate complete absence of localStorage (SSR / restricted environment)
  globalThis.localStorage = undefined;
  clearPrefs();

  const state = createDefaultState();
  state.answers.readingPace = "slow";
  state.prefs.textSize = "l";

  assert.doesNotThrow(() => {
    savePrefs(state);
  }, "savePrefs must not throw when localStorage is undefined");
  assert.equal(isUsingMemoryFallback(), true);

  const reloaded = loadPrefs();
  assert.equal(reloaded.answers.readingPace, "slow");
  assert.equal(reloaded.prefs.textSize, "l");

  clearPrefs();
});

test("Test 7: getInlineHeadScript() resilience under throwing storage and corrupt payload", () => {
  // 1. Throws SecurityError during inline head execution
  globalThis.localStorage = createMockLocalStorage({ throwOnGet: true });
  const mockRoot = createMockRootElement();
  globalThis.document = { documentElement: mockRoot };

  const snippet = getInlineHeadScript();
  const executeSnippet = new Function(snippet);

  assert.doesNotThrow(() => {
    executeSnippet();
  }, "Inline head script must catch storage access exceptions silently");

  // 2. Corrupt JSON in storage during inline head execution
  const corruptStore = createMockLocalStorage();
  corruptStore.setItem(STORAGE_KEY, "CORRUPT_{{{[[");
  globalThis.localStorage = corruptStore;

  assert.doesNotThrow(() => {
    executeSnippet();
  }, "Inline head script must catch JSON parse errors silently");

  // 3. Null prefs in storage during inline head execution
  corruptStore.setItem(STORAGE_KEY, JSON.stringify({ version: 1, prefs: null }));
  assert.doesNotThrow(() => {
    executeSnippet();
  }, "Inline head script must handle null prefs safely");

  clearPrefs();
});

test("Test 8: resetToAnswers clears manual overrides and resetAll restores factory defaults", () => {
  globalThis.localStorage = createMockLocalStorage();
  clearPrefs();

  // Initial custom state with override
  const customState = {
    version: SCHEMA_VERSION,
    updatedAt: new Date().toISOString(),
    answers: { ...DEFAULT_ANSWERS, readingPace: "slow" },
    prefs: { ...DEFAULT_PREFS, textSize: "xl" }, // manual override
    overrides: ["textSize"],
  };
  savePrefs(customState);

  // 1. resetToAnswers: clears overrides array, re-derives textSize to "l" from slow reading pace
  const resetState = resetToAnswers(loadPrefs());
  assert.deepEqual(resetState.overrides, []);
  assert.equal(resetState.prefs.textSize, "l", "textSize should revert to derived pace value");

  // 2. resetAll: restores factory defaults
  const factoryState = resetAll();
  assert.deepEqual(factoryState.answers, DEFAULT_ANSWERS);
  assert.deepEqual(factoryState.prefs, DEFAULT_PREFS);
  assert.deepEqual(factoryState.overrides, []);

  clearPrefs();
});

test("Test 9: Export and import JSON roundtrip lifecycle with schema sanitization", () => {
  globalThis.localStorage = createMockLocalStorage();
  clearPrefs();

  const originalState = {
    version: SCHEMA_VERSION,
    updatedAt: "2026-10-22T14:00:00.000Z",
    answers: { ...DEFAULT_ANSWERS, readingPace: "fast" },
    prefs: { ...DEFAULT_PREFS, density: "focused" },
    overrides: ["density"],
  };
  savePrefs(originalState);

  // Export
  const exportedJson = exportPrefsJson();
  assert.ok(typeof exportedJson === "string" && exportedJson.length > 50);

  // Clear and re-import
  clearPrefs();
  const importedState = importPrefsJson(exportedJson);
  assert.equal(importedState.answers.readingPace, "fast");
  assert.equal(importedState.prefs.density, "focused");
  assert.deepEqual(importedState.overrides, ["density"]);

  // Attack importPrefsJson with invalid argument
  assert.throws(() => {
    importPrefsJson(12345);
  }, TypeError);

  clearPrefs();
});
