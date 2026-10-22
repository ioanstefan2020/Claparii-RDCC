/**
 * i18n.js - Lightweight, Offline-Safe Internationalization Module
 * Project: Limpede (AccessABILITY Hackathon 2026)
 * Owner: p2
 * Spec: docs/plan/p2.md (§3.1)
 *
 * Provides:
 * - Complete Romanian (ro) and English (en) dictionaries for all UI text
 * - Language getter & setter with persistence to localStorage['limpede_lang']
 * - Attribute applicator for [data-i18n], [data-i18n-placeholder], [data-i18n-aria-label]
 * - Graceful fallback: requested lang -> ro -> en -> key
 */

export const DICTIONARY = Object.freeze({
  ro: {
    // Brand & Identity
    brand_name: "Limpede",
    brand_tagline: "Asistent Accesibil pentru Primul Loc de Muncă",
    topbar_title: "Limpede AI",

    // Navigation Landmark
    nav_home: "Acasă",
    nav_library: "Bibliotecă",
    nav_audio: "Audio → text",
    nav_clarify: "Clarificare",
    nav_plan: "Planificator",
    nav_meeting: "Ședințe",
    nav_adjustments: "Adaptări",
    nav_profile: "Profil & Nevoi",
    nav_employer: "Zona Angajator",
    nav_settings: "Setări Confort",

    // Sidebar
    sidebar_new: "Conversație nouă",
    sidebar_privacy_badge: "Stocare Locală · 100% Confidențial",
    sidebar_user_tier: "Spațiu Personal · Confidențial",
    user_default_name: "Utilizator Limpede",
    welcome_name_label: "Cum te numești? (opțional)",
    welcome_name_placeholder: "ex: Ana sau David",

    // Topbar & Comfort
    topbar_menu: "Meniu",
    topbar_comfort: "Confort",
    topbar_questionnaire: "Chestionar",
    topbar_settings: "Setări",
    mode_contrast_light: "Mod: Luminos",
    mode_contrast_dark: "Mod: Întunecat",
    text_size_m: "Text: Mediu",
    text_size_l: "Text: Mare",
    text_size_xl: "Text: Foarte mare",
    audio_play: "Audio: Citește",
    audio_pause: "Audio: Pauză",
    audio_resume: "Audio: Continuă",
    dyslexia_off: "Dislexie: Oprită",
    dyslexia_on: "Dislexie: Activată",

    // Hero & Input Capsule
    hero_greeting: "De unde să începem?",
    capsule_placeholder_simplify: "Introdu textul sau instrucțiunile de la manager...",
    capsule_placeholder_plan: "Introdu emailul sau lista de sarcini...",
    capsule_placeholder_meeting: "Introdu transcrierea sau notele de la ședință...",

    // Modes & Descriptions
    mode_simplify: "Clarificare",
    mode_plan: "Planificator",
    mode_meeting: "Ședințe",
    mode_simplify_desc: "Explică pașii simplu cu citate sursă",
    mode_plan_desc: "Extrage termene și exportă în .ics",
    mode_meeting_desc: "Extrage decizii și acțiuni clare",

    // Action Chips
    chip_clarify: "Clarifică fișa postului",
    chip_plan: "Planifică termene limită",
    chip_meeting: "Sinteză ședință operațională",
    chip_adjustments: "Solicită adaptări de muncă",

    // Action Buttons
    btn_listen: "Ascultă",
    btn_shorter: "Mai scurt",
    btn_bullets: "Puncte",
    btn_steps: "Pe pași",
    btn_explain: "Explică simplu",
    btn_add_to_plan: "Adaugă în plan",
    btn_saved_to_plan: "Adăugat în plan",
    btn_save_library: "Salvează",
    btn_copy: "Copiază",
    btn_ics: "Calendar (.ics)",
    btn_show_in_text: "Arată în text",

    // Results & Source Section
    results_title: "Rezultat analiză",
    source_title: "Text original cu evidențiere citate",
    source_desc: "Apasă pe butonul «Arată în text» de la oricare pas sau sarcină pentru a verifica citatul exact în textul original.",
    ai_notice: "Generat de AI — verifică datele importante.",
    footer_text: "Limpede — AccessABILITY Hackathon 2026. Conform standardelor WCAG 2.2 AA. Fără conturi, fără stocare pe server.",
  },
  en: {
    // Brand & Identity
    brand_name: "Limpede",
    brand_tagline: "Accessible Assistant for Your First Job",
    topbar_title: "Limpede AI",

    // Navigation Landmark
    nav_home: "Home",
    nav_library: "Library",
    nav_audio: "Audio → text",
    nav_clarify: "Clarify",
    nav_plan: "Planner",
    nav_meeting: "Meetings",
    nav_adjustments: "Adjustments",
    nav_profile: "Profile & Needs",
    nav_employer: "Employer Zone",
    nav_settings: "Comfort Settings",

    // Sidebar
    sidebar_new: "New conversation",
    sidebar_privacy_badge: "Local Storage · 100% Private",
    sidebar_user_tier: "Personal Space · Private",
    user_default_name: "Limpede User",
    welcome_name_label: "What is your name? (optional)",
    welcome_name_placeholder: "e.g., Ana or David",

    // Topbar & Comfort
    topbar_menu: "Menu",
    topbar_comfort: "Comfort",
    topbar_questionnaire: "Questionnaire",
    topbar_settings: "Settings",
    mode_contrast_light: "Mode: Light",
    mode_contrast_dark: "Mode: Dark",
    text_size_m: "Text: Medium",
    text_size_l: "Text: Large",
    text_size_xl: "Text: Extra large",
    audio_play: "Audio: Read",
    audio_pause: "Audio: Pause",
    audio_resume: "Audio: Resume",
    dyslexia_off: "Dyslexia: Off",
    dyslexia_on: "Dyslexia: On",

    // Hero & Input Capsule
    hero_greeting: "Where should we start?",
    capsule_placeholder_simplify: "Enter workplace text or manager instructions...",
    capsule_placeholder_plan: "Enter email or task list...",
    capsule_placeholder_meeting: "Enter transcript or meeting notes...",

    // Modes & Descriptions
    mode_simplify: "Clarify",
    mode_plan: "Planner",
    mode_meeting: "Meetings",
    mode_simplify_desc: "Explain steps simply with source quotes",
    mode_plan_desc: "Extract deadlines and export to .ics",
    mode_meeting_desc: "Extract clear decisions and action items",

    // Action Chips
    chip_clarify: "Clarify job description",
    chip_plan: "Plan deadlines",
    chip_meeting: "Summarize meeting",
    chip_adjustments: "Request workplace adjustments",

    // Action Buttons
    btn_listen: "Listen",
    btn_shorter: "Shorter",
    btn_bullets: "Bullets",
    btn_steps: "Steps",
    btn_explain: "Explain simply",
    btn_add_to_plan: "Add to plan",
    btn_saved_to_plan: "Saved to plan",
    btn_save_library: "Save",
    btn_copy: "Copy",
    btn_ics: "Calendar (.ics)",
    btn_show_in_text: "Show in text",

    // Results & Source Section
    results_title: "Analysis result",
    source_title: "Original text with quote highlights",
    source_desc: "Click the «Show in text» button on any step or task to verify the exact quote in the original text.",
    ai_notice: "AI generated — verify important information.",
    footer_text: "Limpede — AccessABILITY Hackathon 2026. WCAG 2.2 AA compliant. No accounts, no server storage.",
  },
});

/**
 * Returns the currently active language ("ro" or "en").
 * Checks localStorage first, then document.documentElement attributes, defaulting to "ro".
 *
 * @returns {"ro" | "en"}
 */
export function getLanguage() {
  try {
    if (typeof localStorage !== "undefined") {
      const stored = localStorage.getItem("limpede_lang");
      if (stored === "ro" || stored === "en") return stored;
    }
  } catch (e) {
    // localStorage might throw in restricted/private browsing modes
  }
  if (typeof document !== "undefined" && document.documentElement) {
    const dataLang = document.documentElement.getAttribute("data-lang");
    if (dataLang === "ro" || dataLang === "en") return dataLang;
    const htmlLang = document.documentElement.getAttribute("lang");
    if (htmlLang === "ro" || htmlLang === "en") return htmlLang;
  }
  return "ro";
}

/**
 * Sets the active language and updates localStorage and document root attributes.
 *
 * @param {"ro" | "en"} lang
 * @returns {"ro" | "en"}
 */
export function setLanguage(lang) {
  const target = lang === "en" ? "en" : "ro";
  try {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("limpede_lang", target);
    }
  } catch (e) {
    // Ignore storage quota or security errors
  }
  if (typeof document !== "undefined" && document.documentElement) {
    document.documentElement.setAttribute("data-lang", target);
    document.documentElement.setAttribute("lang", target);
  }
  if (typeof window !== "undefined" && typeof CustomEvent !== "undefined") {
    try {
      window.dispatchEvent(
        new CustomEvent("limpede:lang-changed", { detail: { lang: target } })
      );
    } catch (e) {
      // Ignore event dispatch errors
    }
  }
  return target;
}

/**
 * Translates a key for the given language with cascading fallbacks.
 *
 * @param {string} key
 * @param {"ro" | "en"} [lang]
 * @returns {string}
 */
export function t(key, lang) {
  if (!key) return "";
  const currentLang = lang || getLanguage();
  if (DICTIONARY[currentLang] && DICTIONARY[currentLang][key] !== undefined) {
    return DICTIONARY[currentLang][key];
  }
  if (DICTIONARY.ro && DICTIONARY.ro[key] !== undefined) {
    return DICTIONARY.ro[key];
  }
  if (DICTIONARY.en && DICTIONARY.en[key] !== undefined) {
    return DICTIONARY.en[key];
  }
  return String(key);
}

/**
 * Translates all DOM elements within the root element (and the root element itself)
 * that have data-i18n, data-i18n-placeholder, or data-i18n-aria-label attributes.
 *
 * @param {HTMLElement | Document} [rootElement]
 * @param {"ro" | "en"} [lang]
 */
export function applyI18n(rootElement, lang) {
  const currentLang = lang || getLanguage();
  const root =
    rootElement ||
    (typeof document !== "undefined" ? document.documentElement || document.body : null);
  if (!root) return;

  // Root element translation if it carries attributes
  if (typeof root.getAttribute === "function") {
    const key = root.getAttribute("data-i18n");
    if (key) root.textContent = t(key, currentLang);

    const placeholderKey = root.getAttribute("data-i18n-placeholder");
    if (placeholderKey) {
      if ("placeholder" in root) {
        root.placeholder = t(placeholderKey, currentLang);
      } else if (typeof root.setAttribute === "function") {
        root.setAttribute("placeholder", t(placeholderKey, currentLang));
      }
    }

    const ariaLabelKey = root.getAttribute("data-i18n-aria-label");
    if (ariaLabelKey && typeof root.setAttribute === "function") {
      root.setAttribute("aria-label", t(ariaLabelKey, currentLang));
    }
  }

  // Descendants translation
  if (typeof root.querySelectorAll === "function") {
    const textEls = root.querySelectorAll("[data-i18n]");
    textEls.forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (key) el.textContent = t(key, currentLang);
    });

    const placeholderEls = root.querySelectorAll("[data-i18n-placeholder]");
    placeholderEls.forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (key) {
        if ("placeholder" in el) {
          el.placeholder = t(key, currentLang);
        } else if (typeof el.setAttribute === "function") {
          el.setAttribute("placeholder", t(key, currentLang));
        }
      }
    });

    const ariaLabelEls = root.querySelectorAll("[data-i18n-aria-label]");
    ariaLabelEls.forEach((el) => {
      const key = el.getAttribute("data-i18n-aria-label");
      if (key && typeof el.setAttribute === "function") {
        el.setAttribute("aria-label", t(key, currentLang));
      }
    });
  }
}

