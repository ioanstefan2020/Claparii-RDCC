/**
 * Unit test suite for Preferences Engine in web/js/prefs/ (owner: p2).
 * Runs via standard Node.js test runner: node --test tests/web/prefs/test_prefs.mjs
 */

import test from "node:test";
import assert from "node:assert/strict";

import {
  STORAGE_KEY,
  SCHEMA_VERSION,
  DEFAULT_ANSWERS,
  DEFAULT_PREFS,
  VALID_ANSWERS,
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
  applyPrefs,
  getInlineHeadScript,
  QUESTIONNAIRE_RO,
  QUESTIONNAIRE_EN,
  getQuestionnaire,
} from "../../../web/js/prefs/index.js";

// Helper to create a fake localStorage
function createMockLocalStorage(options = {}) {
  const store = new Map();
  return {
    getItem: (k) => {
      if (options.throwOnGet) throw new Error("SecurityError: localStorage blocked");
      return store.has(k) ? store.get(k) : null;
    },
    setItem: (k, v) => {
      if (options.throwOnSet) throw new Error("QuotaExceededError: storage full");
      store.set(k, String(v));
    },
    removeItem: (k) => store.delete(k),
    clear: () => store.clear(),
  };
}

// Helper to create a fake DOM element
function createMockElement() {
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
  };
}

test("test_derive: maps comfort answers into UI preferences", () => {
  // 1. Slow reading pace -> large text, roomy spacing
  const slowPace = derivePrefs({ readingPace: "slow" });
  assert.equal(slowPace.textSize, "l");
  assert.equal(slowPace.spacing, "roomy");

  // 2. Fast reading pace -> medium text, comfortable spacing
  const fastPace = derivePrefs({ readingPace: "fast" });
  assert.equal(fastPace.textSize, "m");
  assert.equal(fastPace.spacing, "comfortable");

  // 3. Low visual noise -> high contrast, readable font, reduced motion
  const lowNoise = derivePrefs({ visualNoise: "low" });
  assert.equal(lowNoise.contrast, "high");
  assert.equal(lowNoise.font, "readable");
  assert.equal(lowNoise.motion, "reduced");

  // 4. Quiet sensory -> reduced motion
  const quietSensory = derivePrefs({ sensory: "quiet" });
  assert.equal(quietSensory.motion, "reduced");

  // 5. Short text amount -> focused density
  const shortText = derivePrefs({ textAmount: "short" });
  assert.equal(shortText.density, "focused");

  // 6. Language selection
  const enLang = derivePrefs({ language: "en" });
  assert.equal(enLang.language, "en");
  const roLang = derivePrefs({ language: "ro" });
  assert.equal(roLang.language, "ro");

  // 7. Defaults check
  const defaults = derivePrefs({});
  assert.equal(defaults.language, "ro");
  assert.equal(defaults.textSize, "m");
  assert.equal(defaults.spacing, "comfortable");
  assert.equal(defaults.contrast, "normal");
  assert.equal(defaults.motion, "full");
  assert.equal(defaults.font, "default");
  assert.equal(defaults.density, "full");
  assert.equal(defaults.theme, "system");
  assert.equal(defaults.sidebar, "open");
});

test("test_overrides_kept: manual user overrides are preserved during re-derivation", () => {
  const answers = { readingPace: "slow" }; // would derive textSize: "l"
  const currentPrefs = { textSize: "xl" };
  const overrides = ["textSize"];

  const derived = derivePrefs(answers, currentPrefs, overrides);
  // textSize should stay "xl" from overrides, while spacing is updated to "roomy"
  assert.equal(derived.textSize, "xl");
  assert.equal(derived.spacing, "roomy");
});

test("test_migrate_corrupt: returns valid schema defaults on invalid or unknown data", () => {
  const fromNull = migrate(null);
  assert.equal(fromNull.version, SCHEMA_VERSION);
  assert.deepEqual(fromNull.answers, DEFAULT_ANSWERS);
  assert.deepEqual(fromNull.prefs, DEFAULT_PREFS);
  assert.deepEqual(fromNull.overrides, []);

  const fromString = migrate("corrupt payload");
  assert.equal(fromString.version, SCHEMA_VERSION);
  assert.deepEqual(fromString.answers, DEFAULT_ANSWERS);

  const fromWrongVersion = migrate({ version: 99, answers: { readingPace: "slow" } });
  assert.equal(fromWrongVersion.version, SCHEMA_VERSION);
  assert.deepEqual(fromWrongVersion.answers, DEFAULT_ANSWERS);
});

test("test_migrate_partial: keeps valid partial fields and fills missing ones with defaults", () => {
  const partial = {
    version: 1,
    answers: { readingPace: "fast" },
    prefs: { theme: "dark" },
    overrides: ["theme"],
  };

  const migrated = migrate(partial);
  assert.equal(migrated.version, 1);
  assert.equal(migrated.answers.readingPace, "fast");
  assert.equal(migrated.answers.visualNoise, "normal"); // filled from default
  assert.equal(migrated.prefs.theme, "dark");
  assert.equal(migrated.prefs.textSize, "m"); // filled from default
  assert.deepEqual(migrated.overrides, ["theme"]);
});

test("test_storage_roundtrip: saves and loads preferences correctly", () => {
  globalThis.localStorage = createMockLocalStorage();
  clearPrefs();

  const state = createDefaultState();
  state.answers.readingPace = "slow";
  state.prefs.textSize = "l";
  state.prefs.spacing = "roomy";

  savePrefs(state);
  const loaded = loadPrefs();

  assert.equal(loaded.version, SCHEMA_VERSION);
  assert.equal(loaded.answers.readingPace, "slow");
  assert.equal(loaded.prefs.textSize, "l");
  assert.equal(loaded.prefs.spacing, "roomy");
  assert.equal(isUsingMemoryFallback(), false);

  clearPrefs();
});

test("test_storage_fallback: gracefully handles localStorage exceptions using in-memory store", () => {
  // Simulate private browsing or quota exceeded
  globalThis.localStorage = createMockLocalStorage({ throwOnSet: true });
  clearPrefs();

  const state = createDefaultState();
  state.answers.readingPace = "slow";
  state.prefs.textSize = "l";

  // savePrefs must not throw
  assert.doesNotThrow(() => {
    savePrefs(state);
  });

  // isUsingMemoryFallback should be true
  assert.equal(isUsingMemoryFallback(), true);

  // loadPrefs retrieves from memory store
  const loaded = loadPrefs();
  assert.equal(loaded.answers.readingPace, "slow");
  assert.equal(loaded.prefs.textSize, "l");

  clearPrefs();
});

test("test_reset_to_answers: empties overrides and re-derives prefs from answers", () => {
  const state = {
    version: 1,
    updatedAt: "2026-10-22T10:00:00Z",
    answers: {
      ...DEFAULT_ANSWERS,
      readingPace: "slow",
    },
    prefs: {
      ...DEFAULT_PREFS,
      textSize: "xl", // manual override
    },
    overrides: ["textSize"],
  };

  const resetState = resetToAnswers(state);
  assert.deepEqual(resetState.overrides, []);
  assert.equal(resetState.answers.readingPace, "slow");
  // With overrides cleared, slow pace maps to "l"
  assert.equal(resetState.prefs.textSize, "l");
  assert.equal(resetState.prefs.spacing, "roomy");
});

test("test_reset_all: returns factory default state", () => {
  const factory = resetAll();
  assert.equal(factory.version, SCHEMA_VERSION);
  assert.deepEqual(factory.answers, DEFAULT_ANSWERS);
  assert.deepEqual(factory.prefs, DEFAULT_PREFS);
  assert.deepEqual(factory.overrides, []);
});

test("test_apply_prefs: stamps all data-* attributes and lang on root element", () => {
  const mockEl = createMockElement();
  const testPrefs = {
    theme: "dark",
    textSize: "xl",
    spacing: "roomy",
    contrast: "high",
    motion: "reduced",
    font: "readable",
    density: "focused",
    sidebar: "collapsed",
    language: "en",
  };

  applyPrefs(testPrefs, mockEl);

  assert.equal(mockEl.getAttribute("data-theme"), "dark");
  assert.equal(mockEl.getAttribute("data-text"), "xl");
  assert.equal(mockEl.getAttribute("data-spacing"), "roomy");
  assert.equal(mockEl.getAttribute("data-contrast"), "high");
  assert.equal(mockEl.getAttribute("data-motion"), "reduced");
  assert.equal(mockEl.getAttribute("data-font"), "readable");
  assert.equal(mockEl.getAttribute("data-density"), "focused");
  assert.equal(mockEl.getAttribute("data-sidebar"), "collapsed");
  assert.equal(mockEl.getAttribute("lang"), "en");
});

test("test_fouc_script: produces valid executable JavaScript for <head>", () => {
  const script = getInlineHeadScript();
  assert.ok(typeof script === "string" && script.length > 50);
  assert.ok(script.includes(STORAGE_KEY));
  assert.ok(script.includes("data-theme"));
  assert.ok(script.includes("data-text"));

  // Verify it parses as valid JavaScript without syntax errors
  assert.doesNotThrow(() => {
    // eslint-disable-next-line no-new-func
    new Function(script);
  });
});

test("test_export_import_json: round-trips state through JSON file strings", () => {
  globalThis.localStorage = createMockLocalStorage();
  clearPrefs();

  const state = createDefaultState();
  state.answers.readingPace = "slow";
  savePrefs(state);

  const exported = exportPrefsJson();
  assert.ok(typeof exported === "string");
  const parsed = JSON.parse(exported);
  assert.equal(parsed.answers.readingPace, "slow");

  // Modify and re-import
  parsed.answers.readingPace = "fast";
  const imported = importPrefsJson(JSON.stringify(parsed));
  assert.equal(imported.answers.readingPace, "fast");

  const reloaded = loadPrefs();
  assert.equal(reloaded.answers.readingPace, "fast");

  clearPrefs();
});

test("test_apply_prefs_defensive_state: supports passing full state object directly", () => {
  const mockEl = createMockElement();
  const fullState = {
    version: 1,
    answers: { ...DEFAULT_ANSWERS },
    prefs: {
      ...DEFAULT_PREFS,
      theme: "dark",
      textSize: "xl",
    },
    overrides: [],
  };

  applyPrefs(fullState, mockEl);
  assert.equal(mockEl.getAttribute("data-theme"), "dark");
  assert.equal(mockEl.getAttribute("data-text"), "xl");
});

test("test_storage_read_throw: recovers cleanly if getItem throws SecurityError", () => {
  globalThis.localStorage = createMockLocalStorage({ throwOnGet: true });
  clearPrefs();

  const loaded = loadPrefs();
  assert.equal(loaded.version, SCHEMA_VERSION);
  assert.equal(isUsingMemoryFallback(), true);

  clearPrefs();
});

test("test_storage_corrupt_json: heals corrupt JSON without permanently disabling storage", () => {
  const store = createMockLocalStorage();
  globalThis.localStorage = store;
  clearPrefs();

  store.setItem(STORAGE_KEY, "{ not valid json %%%");
  const loaded = loadPrefs();
  assert.equal(loaded.version, SCHEMA_VERSION);
  assert.equal(isUsingMemoryFallback(), false);

  // Subsequent save successfully writes clean JSON
  savePrefs(createDefaultState());
  assert.ok(store.getItem(STORAGE_KEY).includes('"version":1'));

  clearPrefs();
});

test("test_questionnaire_structure: validates all 7 questions and options against VALID_ANSWERS", () => {
  assert.ok(Array.isArray(QUESTIONNAIRE_RO), "QUESTIONNAIRE_RO must be an array");
  assert.equal(QUESTIONNAIRE_RO.length, 7, "Must have exactly 7 questions");

  const expectedIds = Object.keys(DEFAULT_ANSWERS);
  for (const q of QUESTIONNAIRE_RO) {
    assert.ok(expectedIds.includes(q.id), `Unexpected question id: ${q.id}`);
    assert.ok(typeof q.prompt === "string" && q.prompt.length > 5, `Question ${q.id} prompt too short`);
    assert.ok(typeof q.helpText === "string", `Question ${q.id} missing helpText`);
    assert.ok(Array.isArray(q.options) && q.options.length >= 2, `Question ${q.id} must have >= 2 options`);

    const allowed = VALID_ANSWERS[q.id];
    for (const opt of q.options) {
      assert.ok(allowed.includes(opt.value), `Invalid option value '${opt.value}' for question ${q.id}`);
      assert.ok(typeof opt.label === "string" && opt.label.length > 0, "Option label missing");
      assert.ok(typeof opt.description === "string", "Option description missing");
    }
  }
});

test("test_questionnaire_bilingual: ensures EN questions match RO IDs and getQuestionnaire works", () => {
  assert.ok(Array.isArray(QUESTIONNAIRE_EN), "QUESTIONNAIRE_EN must be an array");
  assert.equal(QUESTIONNAIRE_EN.length, 7, "Must have 7 English questions");

  const roIds = QUESTIONNAIRE_RO.map((q) => q.id);
  const enIds = QUESTIONNAIRE_EN.map((q) => q.id);
  assert.deepEqual(roIds, enIds, "RO and EN questionnaire IDs must match in order");

  assert.equal(getQuestionnaire("ro"), QUESTIONNAIRE_RO);
  assert.equal(getQuestionnaire("en"), QUESTIONNAIRE_EN);
  assert.equal(getQuestionnaire("unknown"), QUESTIONNAIRE_RO);
});

test("test_questionnaire_zero_diagnosis: strictly no medical/diagnosis terms in questions", () => {
  const bannedTerms = [
    "diagnostic", "boală", "afecțiune", "handicap", "medical",
    "disease", "disability", "disorder", "syndrome", "illness", "pacient", "tratament"
  ];

  const fullTextRo = JSON.stringify(QUESTIONNAIRE_RO).toLowerCase();
  const fullTextEn = JSON.stringify(QUESTIONNAIRE_EN).toLowerCase();

  for (const term of bannedTerms) {
    assert.ok(!fullTextRo.includes(term), `Banned medical term '${term}' found in Romanian questionnaire`);
    assert.ok(!fullTextEn.includes(term), `Banned medical term '${term}' found in English questionnaire`);
  }
});

