/**
 * profile.js - Device-Only Profile & Accessibility Preferences
 * Owner: p2
 *
 * Rules:
 * - Device-only storage (localStorage). No data sent to server except with explicit user requests.
 * - STRICT RESPONSIBLE AI RULE: No diagnosis fields. Needs are expressed in user's own words only.
 * - "Delete my data" button wipes everything cleanly.
 */

const PROFILE_KEY = "primazi_user_profile";
const A11Y_KEY = "primazi_a11y_prefs";

export const DEFAULT_PROFILE = {
  reading_level: "simple", // "standard" | "simple" | "very_simple"
  format: "steps",         // "steps" | "short_paragraphs"
  needs_notes: "",         // Free text in user's own words (<= 500 chars)
  max_sentence_words: 12,  // integer between 6 and 30
  read_aloud_default: false
};

export const DEFAULT_A11Y_PREFS = {
  theme: "light",          // "light" | "dark" | "high-contrast"
  textSize: "normal",      // "normal" | "large" | "xlarge"
  spacing: "normal",       // "normal" | "wide"
  simpleMode: false,       // boolean
  lineFocus: false         // boolean: reading guide / line focus for cognitive comfort
};

/**
 * Loads the user profile from localStorage, falling back to defaults.
 */
export function getProfile() {
  if (typeof localStorage === "undefined") return { ...DEFAULT_PROFILE };
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return { ...DEFAULT_PROFILE };
    const parsed = JSON.parse(raw);

    // Sanitize and enforce safe limits
    return {
      reading_level: ["standard", "simple", "very_simple"].includes(parsed.reading_level)
        ? parsed.reading_level
        : DEFAULT_PROFILE.reading_level,
      format: ["steps", "short_paragraphs"].includes(parsed.format)
        ? parsed.format
        : DEFAULT_PROFILE.format,
      needs_notes: typeof parsed.needs_notes === "string"
        ? parsed.needs_notes.slice(0, 500)
        : "",
      max_sentence_words: Number.isFinite(parsed.max_sentence_words)
        ? Math.min(Math.max(Math.round(parsed.max_sentence_words), 6), 30)
        : DEFAULT_PROFILE.max_sentence_words,
      read_aloud_default: typeof parsed.read_aloud_default === "boolean"
        ? parsed.read_aloud_default
        : DEFAULT_PROFILE.read_aloud_default
    };
  } catch {
    return { ...DEFAULT_PROFILE };
  }
}

/**
 * Saves profile updates to localStorage.
 */
export function saveProfile(updates = {}) {
  if (typeof localStorage === "undefined") return { ...DEFAULT_PROFILE, ...updates };
  const current = getProfile();
  const next = {
    reading_level: ["standard", "simple", "very_simple"].includes(updates.reading_level)
      ? updates.reading_level
      : current.reading_level,
    format: ["steps", "short_paragraphs"].includes(updates.format)
      ? updates.format
      : current.format,
    needs_notes: updates.needs_notes !== undefined
      ? String(updates.needs_notes).slice(0, 500)
      : current.needs_notes,
    max_sentence_words: Number.isFinite(updates.max_sentence_words)
      ? Math.min(Math.max(Math.round(updates.max_sentence_words), 6), 30)
      : current.max_sentence_words,
    read_aloud_default: updates.read_aloud_default !== undefined
      ? Boolean(updates.read_aloud_default)
      : current.read_aloud_default
  };
  localStorage.setItem(PROFILE_KEY, JSON.stringify(next));
  return next;
}

/**
 * Formats profile payload specifically for API requests (CONTRACTS §1).
 * Strips UI-only preferences like read_aloud_default.
 */
export function getApiProfile(profile = null) {
  const p = profile || getProfile();
  return {
    reading_level: ["standard", "simple", "very_simple"].includes(p?.reading_level)
      ? p.reading_level
      : DEFAULT_PROFILE.reading_level,
    format: ["steps", "short_paragraphs"].includes(p?.format)
      ? p.format
      : DEFAULT_PROFILE.format,
    needs_notes: typeof p?.needs_notes === "string"
      ? p.needs_notes.slice(0, 500)
      : "",
    max_sentence_words: Number.isFinite(p?.max_sentence_words)
      ? Math.min(Math.max(Math.round(p.max_sentence_words), 6), 30)
      : DEFAULT_PROFILE.max_sentence_words
  };
}

/**
 * Retrieves accessibility preferences.
 */
export function getA11yPrefs() {
  if (typeof localStorage === "undefined") return { ...DEFAULT_A11Y_PREFS };
  try {
    const raw = localStorage.getItem(A11Y_KEY);
    if (!raw) return { ...DEFAULT_A11Y_PREFS };
    return { ...DEFAULT_A11Y_PREFS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_A11Y_PREFS };
  }
}

/**
 * Saves and applies accessibility preferences directly to DOM root attributes.
 */
export function saveA11yPrefs(prefs) {
  if (typeof localStorage === "undefined") return { ...DEFAULT_A11Y_PREFS, ...prefs };
  const next = { ...getA11yPrefs(), ...prefs };
  localStorage.setItem(A11Y_KEY, JSON.stringify(next));
  applyA11yPrefs(next);
  return next;
}

/**
 * Applies preferences to document.documentElement for instant CSS variable response.
 */
export function applyA11yPrefs(prefs = null) {
  if (typeof document === "undefined") return;
  const p = prefs || getA11yPrefs();
  const root = document.documentElement;

  // Theme
  if (p.theme && p.theme !== "light") {
    root.setAttribute("data-theme", p.theme);
  } else {
    root.removeAttribute("data-theme");
  }

  // Text size
  if (p.textSize && p.textSize !== "normal") {
    root.setAttribute("data-text-size", p.textSize);
  } else {
    root.removeAttribute("data-text-size");
  }

  // Spacing
  if (p.spacing === "wide") {
    root.setAttribute("data-spacing", "wide");
  } else {
    root.removeAttribute("data-spacing");
  }

  // Simple mode
  if (p.simpleMode) {
    root.setAttribute("data-simple-mode", "true");
  } else {
    root.removeAttribute("data-simple-mode");
  }

  // Line focus mode (T2.8 reading guide)
  if (p.lineFocus) {
    root.setAttribute("data-line-focus", "true");
  } else {
    root.removeAttribute("data-line-focus");
  }
}

/**
 * Completely clears all local data ("Delete my data" button).
 * Returns true if successful.
 */
export function deleteAllUserData() {
  if (typeof localStorage === "undefined") return false;
  try {
    localStorage.removeItem(PROFILE_KEY);
    localStorage.removeItem(A11Y_KEY);
    localStorage.removeItem("primazi_planner_tasks");
    applyA11yPrefs(DEFAULT_A11Y_PREFS);
    return true;
  } catch (err) {
    console.error("Eroare la ștergerea datelor:", err);
    return false;
  }
}
