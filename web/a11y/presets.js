/**
 * PrimaZi — Accessibility Presets (Wave 2)
 * Need-based suggestions that the user can pick and further customize.
 * Ref: docs/SETTINGS-SPEC.md §9
 */

export const PRESETS = {
  "citire-usoara": {
    id: "citire-usoara",
    label: "Citire ușoară",
    description: "Propoziții scurte, pași clari, spațiere aerisită și explicații automate pentru termeni dificili.",
    values: {
      reading_level: "very_simple",
      format: "steps",
      summary_first: true,
      glossary_inline: "always",
      line_height: 1.8,
      letter_spacing: 0.04,
      word_spacing: 0.08,
      paragraph_spacing: 1.4,
      highlight_mode: "light",
      tone_notes: "on"
    }
  },
  "fara-distragere": {
    id: "fara-distragere",
    label: "Fără distragere",
    description: "Un singur pas pe ecran, panouri secundare ascunse, pauze regulate și calm vizual.",
    values: {
      focus_level: 2,
      layout: "guided",
      calm_mode: true,
      chunk_size: "3",
      break_reminders: "25",
      sidebar: "collapsed"
    }
  },
  "text-mare": {
    id: "text-mare",
    label: "Text mare și contrast",
    description: "Text mărit la 150%, fundal cald fără reflexii orbitoare, butoane mărite și inel de focalizare pronunțat.",
    values: {
      font_scale: 150,
      theme: "amber",
      target_size: 56,
      target_gap: 16,
      focus_ring: "large"
    }
  },
  "cititor-ecran": {
    id: "cititor-ecran",
    label: "Cu cititor de ecran",
    description: "Structură simplificată, etichete explicite, fără decorațiuni vizuale zgomotoase și anunțuri live optime.",
    values: {
      sr_mode: true,
      announce_level: "polite",
      describe_images: "auto",
      layout: "overview",
      tooltips_on_focus_click: true
    }
  },
  "audio-in-text": {
    id: "audio-in-text",
    label: "Audio în text",
    description: "Subtitrări automate implicite, transcrieri complete pentru orice audio și alerte vizuale în loc de sunete.",
    values: {
      captions_default: true,
      transcript_always: true,
      visual_alerts: true,
      vibration_alerts: true
    }
  },
  "control-usor": {
    id: "control-usor",
    label: "Control ușor (tastatură/voce)",
    description: "Ținte tactile mari (64px), distanțiere generoase, scurtături de tastatură și comenzi vocale opționale.",
    values: {
      target_size: 64,
      target_gap: 16,
      keyboard_shortcuts: true,
      voice_commands: true
    }
  },
  "ascult-mai-mult": {
    id: "ascult-mai-mult",
    label: "Aud în loc să citesc",
    description: "Redare vocală automată a rezultatelor, evidențiere cuvânt cu cuvânt și pronunțare naturală a numerelor și datelor.",
    values: {
      tts_autoread: "result",
      tts_follow: "word",
      tts_rate: 0.9,
      tts_spoken_numbers: true
    }
  }
};

/**
 * Returns merged settings with the target preset applied.
 * @param {string} presetId
 * @param {object} currentSettings
 * @returns {object}
 */
export function applyPresetValues(presetId, currentSettings = {}) {
  const preset = PRESETS[presetId];
  if (!preset) return { ...currentSettings };
  return {
    ...currentSettings,
    ...preset.values
  };
}
