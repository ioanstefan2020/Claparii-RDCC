/**
 * PrimaZi — Unified Settings Engine (Wave 2)
 * Persists in localStorage (key: primazi.settings.v2), clamps values, handles cross-tab sync,
 * migrations, presets, and export/import.
 * Ref: docs/SETTINGS-SPEC.md §0, §1, §2, §4, §5, §6, §7, §8, §10
 */

import { PRESETS, applyPresetValues } from "./presets.js";

export const STORAGE_KEY = "primazi.settings.v2";
export { PRESETS };

export const DEFAULTS = Object.freeze({
  version: 2,
  // 1. Visual
  theme: "soft", // soft | amber | sapphire | hc-dark | hc-light | mono | night
  font_family: "atkinson", // atkinson | system | dyslexia | serif-readable
  font_scale: 100, // 70 - 200 %
  line_height: 1.6, // 1.2 - 2.4
  letter_spacing: 0.02, // 0 - 0.2 em
  word_spacing: 0.05, // 0 - 0.5 em
  paragraph_spacing: 1.0, // 0.5 - 3.0 em
  measure: 68, // 40 - 100 ch
  font_weight: 400, // 400 | 500 | 600 | 700
  link_style: "underline-always",
  saturation: 100, // 0 - 100 %
  color_vision: "none", // none | protan | deutan | tritan
  focus_ring: "normal", // normal | large | xlarge
  cursor_size: "normal", // normal | large | xlarge
  dim_overlay: 0, // 0 - 60 %
  reduce_motion: "auto", // auto | on
  reduce_transparency: false,

  // 2. Cognitive / Focus / Layout
  focus_level: 0, // 0 Standard | 1 Ușor | 2 Mediu | 3 Maxim
  density: "comfortable", // compact | comfortable | spacious
  layout: "overview", // overview | guided | card
  sidebar: "expanded", // expanded | collapsed | auto-hide
  summary_first: true,
  chunk_size: "all", // 3 | 5 | 7 | all
  progressive_disclosure: false,
  glossary_inline: "hover/tap", // off | hover/tap | always
  reading_ruler: "off", // off | line | band
  ruler_height: 32, // px
  ruler_color: "rgba(255, 235, 59, 0.25)",
  focus_paragraph: false,
  bionic: false,
  reading_level: "simple", // standard | simple | very_simple
  format: "steps", // steps | short_paragraphs | bullets
  tone_notes: "off", // off | on
  break_reminders: "off", // off | 25 | 45
  confirm_actions: true,
  calm_mode: false,

  // 4. Audio
  tts_engine: "auto", // auto | browser | server
  tts_voice: "auto",
  tts_rate: 0.95, // 0.5 - 2.0
  tts_pitch: 1.0, // 0.8 - 1.2
  tts_volume: 1.0, // 0 - 1.0
  tts_pause_ms: 350, // 0 - 1500 ms
  tts_follow: "sentence", // none | sentence | word
  tts_autoread: "off", // off | result | page
  tts_spoken_numbers: true,
  captions_default: true,
  transcript_always: true,
  visual_alerts: true,
  vibration_alerts: false,
  sound_effects: "off",

  // 5. Highlighting
  highlight_mode: "light", // off | light | medium | strong
  highlight_categories: ["action", "deadline", "warning"],
  highlight_style: "combo", // combo | background | underline | bold | larger
  highlight_scale: 110, // 100 - 140 %
  highlight_palette: "multi", // yellow | multi | mono

  // 6. Motor / Input
  target_size: 48, // 44 | 48 | 56 | 64 px
  target_gap: 12, // 8 | 12 | 16 | 24 px
  keyboard_shortcuts: true,
  single_key_shortcuts: false,
  voice_commands: false,
  tooltips_on_focus_click: true,
  no_drag: true,

  // 7. Screen Reader
  sr_mode: false,
  announce_level: "polite", // minimal | polite | assertive
  describe_images: "ask", // auto | ask | off
  magnify_focus: false,

  // 8. Language
  ui_language: "ro"
});

const VALID_ENUMS = {
  theme: ["soft", "amber", "sapphire", "hc-dark", "hc-light", "mono", "night"],
  font_family: ["atkinson", "system", "dyslexia", "serif-readable"],
  font_weight: [400, 500, 600, 700],
  color_vision: ["none", "protan", "deutan", "tritan"],
  focus_ring: ["normal", "large", "xlarge"],
  cursor_size: ["normal", "large", "xlarge"],
  reduce_motion: ["auto", "on"],
  focus_level: [0, 1, 2, 3],
  density: ["compact", "comfortable", "spacious"],
  layout: ["overview", "guided", "card"],
  sidebar: ["expanded", "collapsed", "auto-hide"],
  chunk_size: ["3", "5", "7", "all"],
  glossary_inline: ["off", "hover/tap", "always"],
  reading_ruler: ["off", "line", "band"],
  reading_level: ["standard", "simple", "very_simple"],
  format: ["steps", "short_paragraphs", "bullets"],
  tone_notes: ["off", "on"],
  break_reminders: ["off", "25", "45"],
  tts_engine: ["auto", "browser", "server"],
  tts_follow: ["none", "sentence", "word"],
  tts_autoread: ["off", "result", "page"],
  sound_effects: ["off", "on"],
  highlight_mode: ["off", "light", "medium", "strong"],
  highlight_style: ["combo", "background", "underline", "bold", "larger"],
  highlight_palette: ["yellow", "multi", "mono"],
  target_size: [44, 48, 56, 64],
  target_gap: [8, 12, 16, 24],
  announce_level: ["minimal", "polite", "assertive"],
  describe_images: ["auto", "ask", "off"],
  ui_language: ["ro", "en"]
};

const NUMERIC_RANGES = {
  font_scale: [70, 200],
  line_height: [1.2, 2.4],
  letter_spacing: [0.0, 0.2],
  word_spacing: [0.0, 0.5],
  paragraph_spacing: [0.5, 3.0],
  measure: [40, 100],
  saturation: [0, 100],
  dim_overlay: [0, 60],
  ruler_height: [16, 120],
  tts_rate: [0.5, 2.0],
  tts_pitch: [0.8, 1.2],
  tts_volume: [0.0, 1.0],
  tts_pause_ms: [0, 1500],
  highlight_scale: [100, 140]
};

/**
 * Normalises and clamps a single setting key-value pair.
 */
export function normalizeSetting(key, val) {
  if (val === undefined || val === null) return DEFAULTS[key];

  if (key in VALID_ENUMS) {
    const allowed = VALID_ENUMS[key];
    const coerced = typeof val === "string" ? val.trim() : val;
    if (allowed.includes(coerced)) return coerced;
    if (typeof coerced === "string") {
      const lower = coerced.toLowerCase();
      const match = allowed.find(a => String(a).toLowerCase() === lower);
      if (match !== undefined) return match;
    }
    return DEFAULTS[key];
  }

  if (key in NUMERIC_RANGES) {
    const [min, max] = NUMERIC_RANGES[key];
    const num = Number(val);
    if (Number.isNaN(num)) return DEFAULTS[key];
    return Math.min(Math.max(num, min), max);
  }

  if (typeof DEFAULTS[key] === "boolean") {
    if (typeof val === "boolean") return val;
    if (val === "true" || val === 1 || val === "1") return true;
    if (val === "false" || val === 0 || val === "0") return false;
    return DEFAULTS[key];
  }

  if (key === "highlight_categories") {
    if (!Array.isArray(val)) return DEFAULTS.highlight_categories;
    const allowedCats = ["action", "deadline", "person", "number", "warning", "term"];
    const filtered = val.filter(c => allowedCats.includes(c));
    return filtered.length > 0 ? filtered : DEFAULTS.highlight_categories;
  }

  return val;
}

/**
 * Migrate legacy settings from localStorage (welcome questionnaire, v1 prefs, profile)
 */
export function migrateLegacySettings() {
  const migrated = { ...DEFAULTS };
  if (typeof localStorage === "undefined") return migrated;

  try {
    // 1. Check legacy primazi_prefs_v1
    const v1Raw = localStorage.getItem("primazi_prefs_v1");
    if (v1Raw) {
      const v1 = JSON.parse(v1Raw);
      if (v1.theme === "dark") migrated.theme = "sapphire";
      else if (v1.theme === "light") migrated.theme = "soft";
      if (v1.contrast === "high") migrated.theme = "hc-dark";

      if (v1.font === "dyslexic" || v1.font === "opendyslexic") migrated.font_family = "dyslexia";
      else if (v1.font === "atkinson") migrated.font_family = "atkinson";
      else if (v1.font === "system") migrated.font_family = "system";

      if (v1.textSize === "large") migrated.font_scale = 125;
      else if (v1.textSize === "extra-large") migrated.font_scale = 150;
      else if (v1.textSize === "standard") migrated.font_scale = 100;

      if (v1.spacing === "large") {
        migrated.line_height = 1.8;
        migrated.letter_spacing = 0.04;
        migrated.word_spacing = 0.08;
      }
      if (typeof v1.bionic === "boolean") migrated.bionic = v1.bionic;
      if (typeof v1.focusRuler === "boolean" && v1.focusRuler) migrated.reading_ruler = "line";
      if (typeof v1.focus_level === "number") migrated.focus_level = v1.focus_level;
      if (v1.sidebar) migrated.sidebar = v1.sidebar;
    }

    // 2. Check welcome questionnaire
    const welcomeRaw = localStorage.getItem("primazi_welcome_v1");
    if (welcomeRaw) {
      const welcome = JSON.parse(welcomeRaw);
      if (welcome.preset && PRESETS[welcome.preset]) {
        Object.assign(migrated, PRESETS[welcome.preset].values);
      }
    }
  } catch (err) {
    // Ignore migration parse errors
  }

  return migrated;
}

// In-memory state & reactive listeners
let currentSettings = { ...DEFAULTS };
const listeners = new Set();

/**
 * Loads current settings from localStorage, migrating if absent.
 */
function loadInitialSettings() {
  if (typeof localStorage === "undefined") return { ...DEFAULTS };

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const migrated = migrateLegacySettings();
      saveToStorage(migrated);
      return migrated;
    }
    const parsed = JSON.parse(raw);
    const cleaned = { ...DEFAULTS };
    for (const k of Object.keys(DEFAULTS)) {
      if (k in parsed) {
        cleaned[k] = normalizeSetting(k, parsed[k]);
      }
    }
    cleaned.version = 2;
    return cleaned;
  } catch (e) {
    return { ...DEFAULTS };
  }
}

function saveToStorage(next) {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch (err) {
    // Private mode fallback
  }
}

export function applyDOMAttributes(s, root = typeof document !== "undefined" ? document.documentElement : null) {
  if (!root) return;

  // 1. Data attributes
  root.setAttribute("data-theme", s.theme);
  root.setAttribute("data-font", s.font_family);
  root.setAttribute("data-cvd", s.color_vision);
  root.setAttribute("data-cursor", s.cursor_size);
  root.setAttribute("data-motion", s.reduce_motion);
  root.setAttribute("data-flat", s.reduce_transparency ? "true" : "false");
  root.setAttribute("data-focus", String(s.focus_level));
  root.setAttribute("data-density", s.density);
  root.setAttribute("data-layout", s.layout);
  root.setAttribute("data-sidebar", s.sidebar);

  // 2. CSS variables
  root.style.setProperty("--font-scale", `${s.font_scale}%`);
  root.style.setProperty("--lh", String(s.line_height));
  root.style.setProperty("--ls", `${s.letter_spacing}em`);
  root.style.setProperty("--ws", `${s.word_spacing}em`);
  root.style.setProperty("--ps", `${s.paragraph_spacing}em`);
  root.style.setProperty("--measure", `${s.measure}ch`);
  root.style.setProperty("--fw", String(s.font_weight));
  root.style.setProperty("--sat", `${s.saturation}%`);

  const focusWidths = { normal: "3px", large: "5px", xlarge: "7px" };
  root.style.setProperty("--focus-w", focusWidths[s.focus_ring] || "3px");
  root.style.setProperty("--dim", `${s.dim_overlay}%`);
  root.style.setProperty("--target", `${s.target_size}px`);
  root.style.setProperty("--gap", `${s.target_gap}px`);
}

// Initialise
currentSettings = loadInitialSettings();

// Cross-tab sync via storage event
if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === STORAGE_KEY && e.newValue) {
      try {
        const parsed = JSON.parse(e.newValue);
        const cleaned = { ...DEFAULTS };
        for (const k of Object.keys(DEFAULTS)) {
          if (k in parsed) cleaned[k] = normalizeSetting(k, parsed[k]);
        }
        currentSettings = cleaned;
        applyDOMAttributes(currentSettings);
        listeners.forEach(cb => {
          try { cb("*", currentSettings, currentSettings); } catch (_) {}
        });
      } catch (_) {}
    }
  });
}

// Exported public API
export const settings = new Proxy(currentSettings, {
  get(target, prop) {
    if (prop in target) return target[prop];
    return DEFAULTS[prop];
  },
  set() {
    throw new Error("Use setSetting(key, val) or setMany(partial) to mutate settings.");
  }
});

export function getSetting(key) {
  return currentSettings[key] !== undefined ? currentSettings[key] : DEFAULTS[key];
}

export function setSetting(key, value) {
  if (!(key in DEFAULTS) || key === "version") return;
  const normalized = normalizeSetting(key, value);
  if (currentSettings[key] === normalized) return;

  currentSettings = { ...currentSettings, [key]: normalized };
  saveToStorage(currentSettings);
  applyDOMAttributes(currentSettings);

  listeners.forEach(cb => {
    try { cb(key, normalized, currentSettings); } catch (_) {}
  });
}

export function setMany(partial) {
  if (!partial || typeof partial !== "object") return;
  let changed = false;
  const next = { ...currentSettings };

  for (const [k, v] of Object.entries(partial)) {
    if (k in DEFAULTS && k !== "version") {
      const norm = normalizeSetting(k, v);
      if (next[k] !== norm) {
        next[k] = norm;
        changed = true;
      }
    }
  }

  if (!changed) return;
  currentSettings = next;
  saveToStorage(currentSettings);
  applyDOMAttributes(currentSettings);

  listeners.forEach(cb => {
    try { cb("*", currentSettings, currentSettings); } catch (_) {}
  });
}

export function applyPreset(presetId) {
  const updated = applyPresetValues(presetId, currentSettings);
  setMany(updated);
}

export function resetAll() {
  currentSettings = { ...DEFAULTS };
  saveToStorage(currentSettings);
  applyDOMAttributes(currentSettings);

  listeners.forEach(cb => {
    try { cb("*", currentSettings, currentSettings); } catch (_) {}
  });
}

export function exportJSON() {
  return JSON.stringify(currentSettings, null, 2);
}

export function importJSON(jsonStr) {
  try {
    const parsed = typeof jsonStr === "string" ? JSON.parse(jsonStr) : jsonStr;
    const next = { ...DEFAULTS };
    for (const k of Object.keys(DEFAULTS)) {
      if (k in parsed) {
        next[k] = normalizeSetting(k, parsed[k]);
      }
    }
    setMany(next);
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

export function onChange(callback) {
  if (typeof callback === "function") {
    listeners.add(callback);
    return () => listeners.delete(callback);
  }
  return () => {};
}
