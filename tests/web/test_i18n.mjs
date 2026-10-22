/**
 * Unit test suite for lightweight i18n module in web/shared/i18n.js (owner: p2).
 * Runs via standard Node.js test runner: node --test tests/web/test_i18n.mjs
 */

import test from "node:test";
import assert from "node:assert/strict";

import {
  DICTIONARY,
  getLanguage,
  setLanguage,
  t,
  applyI18n,
} from "../../web/shared/i18n.js";

// Helper to create a fake localStorage
function createMockLocalStorage() {
  const store = new Map();
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
    clear: () => store.clear(),
  };
}

// Helper to create a fake DOM Element
function createMockElement(tagName = "div", attrs = {}) {
  const attributes = new Map(Object.entries(attrs));
  const children = [];
  const el = {
    tagName: tagName.toUpperCase(),
    textContent: "",
    placeholder: "",
    attributes,
    children,
    getAttribute(name) {
      return attributes.has(name) ? attributes.get(name) : null;
    },
    setAttribute(name, val) {
      attributes.set(name, String(val));
    },
    removeAttribute(name) {
      attributes.delete(name);
    },
    appendChild(child) {
      children.push(child);
      return child;
    },
    querySelectorAll(selector) {
      const results = [];
      const matchAttr = selector.replace(/[\[\]]/g, "");
      function traverse(node) {
        for (const child of node.children) {
          if (child.getAttribute(matchAttr) !== null) {
            results.push(child);
          }
          traverse(child);
        }
      }
      traverse(this);
      return results;
    },
  };
  return el;
}

test("i18n: Dictionary integrity and symmetry", () => {
  assert.ok(DICTIONARY.ro, "DICTIONARY must have 'ro'");
  assert.ok(DICTIONARY.en, "DICTIONARY must have 'en'");

  const roKeys = Object.keys(DICTIONARY.ro).sort();
  const enKeys = Object.keys(DICTIONARY.en).sort();

  // 1. Every RO key has an EN counterpart
  for (const key of roKeys) {
    assert.ok(
      key in DICTIONARY.en,
      `Key '${key}' exists in RO dictionary but is missing in EN dictionary`
    );
    assert.strictEqual(
      typeof DICTIONARY.ro[key],
      "string",
      `RO key '${key}' must be a string`
    );
    assert.ok(
      DICTIONARY.ro[key].trim().length > 0,
      `RO key '${key}' cannot be empty`
    );
  }

  // 2. Every EN key has a RO counterpart
  for (const key of enKeys) {
    assert.ok(
      key in DICTIONARY.ro,
      `Key '${key}' exists in EN dictionary but is missing in RO dictionary`
    );
    assert.strictEqual(
      typeof DICTIONARY.en[key],
      "string",
      `EN key '${key}' must be a string`
    );
    assert.ok(
      DICTIONARY.en[key].trim().length > 0,
      `EN key '${key}' cannot be empty`
    );
  }

  // 3. Required specification keys presence
  const requiredKeys = [
    "brand_name",
    "brand_tagline",
    "nav_home",
    "nav_library",
    "nav_audio",
    "nav_clarify",
    "nav_plan",
    "nav_meeting",
    "nav_adjustments",
    "nav_profile",
    "nav_employer",
    "nav_settings",
    "sidebar_new",
    "sidebar_privacy_badge",
    "sidebar_user_tier",
    "user_default_name",
    "welcome_name_label",
    "welcome_name_placeholder",
    "hero_greeting",
    "capsule_placeholder_simplify",
    "capsule_placeholder_plan",
    "capsule_placeholder_meeting",
    "mode_simplify",
    "mode_plan",
    "mode_meeting",
    "mode_simplify_desc",
    "mode_plan_desc",
    "mode_meeting_desc",
    "chip_clarify",
    "chip_plan",
    "chip_meeting",
    "chip_adjustments",
    "btn_listen",
    "btn_shorter",
    "btn_bullets",
    "btn_steps",
    "btn_explain",
    "btn_add_to_plan",
    "btn_saved_to_plan",
    "btn_save_library",
    "btn_copy",
    "btn_ics",
    "btn_show_in_text",
    "results_title",
    "source_title",
    "source_desc",
    "ai_notice",
    "footer_text",
  ];

  for (const key of requiredKeys) {
    assert.ok(key in DICTIONARY.ro, `Required spec key '${key}' missing in RO`);
    assert.ok(key in DICTIONARY.en, `Required spec key '${key}' missing in EN`);
  }
});

test("i18n: getLanguage and setLanguage lifecycle", () => {
  const originalLocalStorage = globalThis.localStorage;
  const originalDocument = globalThis.document;

  const mockStorage = createMockLocalStorage();
  const mockDocRoot = createMockElement("html");

  globalThis.localStorage = mockStorage;
  globalThis.document = { documentElement: mockDocRoot };

  try {
    // 1. Defaults to 'ro' when empty
    assert.strictEqual(getLanguage(), "ro");

    // 2. Set to 'en'
    setLanguage("en");
    assert.strictEqual(getLanguage(), "en");
    assert.strictEqual(mockStorage.getItem("limpede_lang"), "en");
    assert.strictEqual(mockDocRoot.getAttribute("data-lang"), "en");
    assert.strictEqual(mockDocRoot.getAttribute("lang"), "en");

    // 3. Set to 'ro'
    setLanguage("ro");
    assert.strictEqual(getLanguage(), "ro");
    assert.strictEqual(mockStorage.getItem("limpede_lang"), "ro");
    assert.strictEqual(mockDocRoot.getAttribute("data-lang"), "ro");
    assert.strictEqual(mockDocRoot.getAttribute("lang"), "ro");

    // 4. Invalid language falls back to 'ro'
    setLanguage("unknown-lang");
    assert.strictEqual(getLanguage(), "ro");
  } finally {
    globalThis.localStorage = originalLocalStorage;
    globalThis.document = originalDocument;
  }
});

test("i18n: t() helper translation and fallbacks", () => {
  // Direct language parameter
  assert.strictEqual(t("brand_name", "ro"), "Limpede");
  assert.strictEqual(t("brand_name", "en"), "Limpede");
  assert.strictEqual(t("nav_home", "ro"), "Acasă");
  assert.strictEqual(t("nav_home", "en"), "Home");
  assert.strictEqual(t("hero_greeting", "ro"), "De unde să începem?");
  assert.strictEqual(t("hero_greeting", "en"), "Where should we start?");

  // Fallback on missing key: returns the key itself
  assert.strictEqual(t("non_existent_key_xyz", "ro"), "non_existent_key_xyz");
  assert.strictEqual(t("", "ro"), "");
});

test("i18n: applyI18n DOM translation", () => {
  const container = createMockElement("div");

  const title = createMockElement("h1", { "data-i18n": "hero_greeting" });
  const input = createMockElement("textarea", {
    "data-i18n-placeholder": "capsule_placeholder_simplify",
  });
  const btn = createMockElement("button", {
    "data-i18n": "btn_explain",
    "data-i18n-aria-label": "btn_explain",
  });

  container.appendChild(title);
  container.appendChild(input);
  container.appendChild(btn);

  // Apply Romanian
  applyI18n(container, "ro");
  assert.strictEqual(title.textContent, "De unde să începem?");
  assert.strictEqual(input.placeholder, "Introdu textul sau instrucțiunile de la manager...");
  assert.strictEqual(btn.textContent, "Explică simplu");
  assert.strictEqual(btn.getAttribute("aria-label"), "Explică simplu");

  // Apply English
  applyI18n(container, "en");
  assert.strictEqual(title.textContent, "Where should we start?");
  assert.strictEqual(input.placeholder, "Enter workplace text or manager instructions...");
  assert.strictEqual(btn.textContent, "Explain simply");
  assert.strictEqual(btn.getAttribute("aria-label"), "Explain simply");
});

