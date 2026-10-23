(() => {
  // extension/src/shared/tts-normalize-ro.js
  var DIGITS_RO = {
    0: "zero",
    1: "unu",
    2: "doi",
    3: "trei",
    4: "patru",
    5: "cinci",
    6: "\u0219ase",
    7: "\u0219apte",
    8: "opt",
    9: "nou\u0103",
    10: "zece",
    11: "unsprezece",
    12: "doisprezece",
    13: "treisprezece",
    14: "paisprezece",
    15: "cincisprezece",
    16: "\u0219aisprezece",
    17: "\u0219aptesprezece",
    18: "optsprezece",
    19: "nou\u0103sprezece",
    20: "dou\u0103zeci",
    30: "treizeci",
    40: "patruzeci",
    50: "cincizeci",
    60: "\u0219aizeci",
    70: "\u0219aptezeci",
    80: "optzeci",
    90: "nou\u0103zeci"
  };
  var HUNDREDS_RO = {
    100: "o sut\u0103",
    200: "dou\u0103 sute",
    300: "trei sute",
    400: "patru sute",
    500: "cinci sute",
    600: "\u0219ase sute",
    700: "\u0219apte sute",
    800: "opt sute",
    900: "nou\u0103 sute"
  };
  var MONTHS_RO = {
    "01": "ianuarie",
    "1": "ianuarie",
    "ian": "ianuarie",
    "02": "februarie",
    "2": "februarie",
    "feb": "februarie",
    "03": "martie",
    "3": "martie",
    "mar": "martie",
    "04": "aprilie",
    "4": "aprilie",
    "apr": "aprilie",
    "05": "mai",
    "5": "mai",
    "06": "iunie",
    "6": "iunie",
    "iun": "iunie",
    "07": "iulie",
    "7": "iulie",
    "iul": "iulie",
    "08": "august",
    "8": "august",
    "aug": "august",
    "09": "septembrie",
    "9": "septembrie",
    "sep": "septembrie",
    "sept": "septembrie",
    "10": "octombrie",
    "oct": "octombrie",
    "11": "noiembrie",
    "nov": "noiembrie",
    "12": "decembrie",
    "dec": "decembrie"
  };
  function numberToWordsRo(n) {
    const num = parseInt(n, 10);
    if (Number.isNaN(num)) return String(n);
    if (DIGITS_RO[num]) return DIGITS_RO[num];
    if (num < 100) {
      const tens = Math.floor(num / 10) * 10;
      const units = num % 10;
      return `${DIGITS_RO[tens]} \u0219i ${DIGITS_RO[units]}`;
    }
    if (num < 1e3) {
      const h = Math.floor(num / 100) * 100;
      const rest = num % 100;
      const hStr = HUNDREDS_RO[h] || `${numberToWordsRo(Math.floor(num / 100))} sute`;
      return rest === 0 ? hStr : `${hStr} ${numberToWordsRo(rest)}`;
    }
    return String(num);
  }
  function normalizeRomanianForSpeech(text) {
    if (!text || typeof text !== "string") return "";
    let res = text;
    res = res.replace(/\b[Aa]rt\.\s*(\d+)/g, (_, n) => `articolul ${numberToWordsRo(n)}`);
    res = res.replace(/\b[Aa]lin\.\s*(\d+)/g, (_, n) => `alineatul ${numberToWordsRo(n)}`);
    res = res.replace(/\b[Nn]r\.\s*(\d+)/g, (_, n) => `num\u0103rul ${n}`);
    res = res.replace(/\b[Ll]egea\s*(\d+)\/(\d+)/g, (_, n, y) => `Legea ${n} din ${y}`);
    res = res.replace(/\b[Ee]x\.:/g, "de exemplu:");
    res = res.replace(/\b[Ee]x\.\s+/g, "de exemplu ");
    res = res.replace(/\betc\./gi, "\u0219i a\u0219a mai departe.");
    res = res.replace(/\bvs\./gi, "fa\u021B\u0103 de");
    res = res.replace(/\baprox\./gi, "aproximativ");
    res = res.replace(/\bpt\./gi, "pentru");
    res = res.replace(/\bstr\./gi, "strada");
    res = res.replace(/\b([A-Za-z])-(\d+)\b/g, (_, letter, num) => `${letter.toUpperCase()} ${numberToWordsRo(num)}`);
    function formatHourRo(hour) {
      if (hour === 1) return "unu";
      if (hour === 2) return "dou\u0103";
      if (hour === 12) return "dou\u0103sprezece";
      if (hour === 21) return "dou\u0103zeci \u0219i unu";
      if (hour === 22) return "dou\u0103zeci \u0219i dou\u0103";
      return numberToWordsRo(hour);
    }
    res = res.replace(/(?:ora\s+)?\b(\d{1,2}):00\b/gi, (_, h) => {
      const hour = parseInt(h, 10);
      return `ora ${formatHourRo(hour)}`;
    });
    res = res.replace(/(?:ora\s+)?\b(\d{1,2}):(\d{2})\b/gi, (_, h, m) => {
      const hour = parseInt(h, 10);
      const min = parseInt(m, 10);
      const hourWords = formatHourRo(hour);
      if (min === 30) return `ora ${hourWords} \u0219i jum\u0103tate`;
      if (min === 15) return `ora ${hourWords} \u0219i un sfert`;
      return `ora ${hourWords} \u0219i ${numberToWordsRo(min)} minute`;
    });
    res = res.replace(/\b(\d{1,2})[\.\/](\d{1,2})[\.\/](\d{4})\b/g, (_, d, m, y) => {
      const day = parseInt(d, 10);
      const month = MONTHS_RO[m] || m;
      return `${day} ${month} ${y}`;
    });
    res = res.replace(/\b(\d{4})-(\d{2})-(\d{2})\b/g, (_, y, m, d) => {
      const day = parseInt(d, 10);
      const month = MONTHS_RO[m] || m;
      return `${day} ${month} ${y}`;
    });
    res = res.replace(/\b(\d+)\s*(?:lei|RON)\b/gi, (_, amount) => {
      const n = parseInt(amount, 10);
      const mod100 = n % 100;
      const needsDe = n >= 20 && (mod100 === 0 || mod100 >= 20);
      const prep = needsDe ? " de lei" : n === 1 ? " leu" : " lei";
      return `${numberToWordsRo(n)}${prep}`;
    });
    res = res.replace(/\b(\d+)\s*(?:EUR|euro)\b/gi, (_, amount) => {
      const n = parseInt(amount, 10);
      const mod100 = n % 100;
      const needsDe = n >= 20 && (mod100 === 0 || mod100 >= 20);
      const prep = needsDe ? " de euro" : " euro";
      return `${numberToWordsRo(n)}${prep}`;
    });
    res = res.replace(/\bal\s*1-lea\b/gi, "primul");
    res = res.replace(/\ba\s*1-a\b/gi, "prima");
    res = res.replace(/\bal\s*2-lea\b/gi, "al doilea");
    res = res.replace(/\ba\s*2-a\b/gi, "a doua");
    res = res.replace(/\bal\s*3-lea\b/gi, "al treilea");
    res = res.replace(/\ba\s*3-a\b/gi, "a treia");
    res = res.replace(/\s{2,}/g, " ").trim();
    return res;
  }

  // extension/src/shared/presets.js
  var PRESETS = {
    "citire-usoara": {
      id: "citire-usoara",
      label: "Citire u\u0219oar\u0103",
      description: "Propozi\u021Bii scurte, pa\u0219i clari, spa\u021Biere aerisit\u0103 \u0219i explica\u021Bii automate pentru termeni dificili.",
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
      label: "F\u0103r\u0103 distragere",
      description: "Un singur pas pe ecran, panouri secundare ascunse, pauze regulate \u0219i calm vizual.",
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
      label: "Text mare \u0219i contrast",
      description: "Text m\u0103rit la 150%, fundal cald f\u0103r\u0103 reflexii orbitoare, butoane m\u0103rite \u0219i inel de focalizare pronun\u021Bat.",
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
      description: "Structur\u0103 simplificat\u0103, etichete explicite, f\u0103r\u0103 decora\u021Biuni vizuale zgomotoase \u0219i anun\u021Buri live optime.",
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
      label: "Audio \xEEn text",
      description: "Subtitr\u0103ri automate implicite, transcrieri complete pentru orice audio \u0219i alerte vizuale \xEEn loc de sunete.",
      values: {
        captions_default: true,
        transcript_always: true,
        visual_alerts: true,
        vibration_alerts: true
      }
    },
    "control-usor": {
      id: "control-usor",
      label: "Control u\u0219or (tastatur\u0103/voce)",
      description: "\u021Ainte tactile mari (64px), distan\u021Biere generoase, scurt\u0103turi de tastatur\u0103 \u0219i comenzi vocale op\u021Bionale.",
      values: {
        target_size: 64,
        target_gap: 16,
        keyboard_shortcuts: true,
        voice_commands: true
      }
    },
    "ascult-mai-mult": {
      id: "ascult-mai-mult",
      label: "Aud \xEEn loc s\u0103 citesc",
      description: "Redare vocal\u0103 automat\u0103 a rezultatelor, eviden\u021Biere cuv\xE2nt cu cuv\xE2nt \u0219i pronun\u021Bare natural\u0103 a numerelor \u0219i datelor.",
      values: {
        tts_autoread: "result",
        tts_follow: "word",
        tts_rate: 0.9,
        tts_spoken_numbers: true
      }
    }
  };

  // extension/src/shared/settings.js
  var STORAGE_KEY = "primazi.settings.v2";
  var DEFAULTS = Object.freeze({
    version: 2,
    // 1. Visual
    theme: "soft",
    // soft | amber | sapphire | hc-dark | hc-light | mono | night
    font_family: "atkinson",
    // atkinson | system | dyslexia | serif-readable
    font_scale: 100,
    // 70 - 200 %
    line_height: 1.6,
    // 1.2 - 2.4
    letter_spacing: 0.02,
    // 0 - 0.2 em
    word_spacing: 0.05,
    // 0 - 0.5 em
    paragraph_spacing: 1,
    // 0.5 - 3.0 em
    measure: 68,
    // 40 - 100 ch
    font_weight: 400,
    // 400 | 500 | 600 | 700
    link_style: "underline-always",
    saturation: 100,
    // 0 - 100 %
    color_vision: "none",
    // none | protan | deutan | tritan
    focus_ring: "normal",
    // normal | large | xlarge
    cursor_size: "normal",
    // normal | large | xlarge
    dim_overlay: 0,
    // 0 - 60 %
    reduce_motion: "auto",
    // auto | on
    reduce_transparency: false,
    // 2. Cognitive / Focus / Layout
    focus_level: 0,
    // 0 Standard | 1 Ușor | 2 Mediu | 3 Maxim
    density: "comfortable",
    // compact | comfortable | spacious
    layout: "overview",
    // overview | guided | card
    sidebar: "expanded",
    // expanded | collapsed | auto-hide
    summary_first: true,
    chunk_size: "all",
    // 3 | 5 | 7 | all
    progressive_disclosure: false,
    glossary_inline: "hover/tap",
    // off | hover/tap | always
    reading_ruler: "off",
    // off | line | band
    ruler_height: 32,
    // px
    ruler_color: "rgba(255, 235, 59, 0.25)",
    focus_paragraph: false,
    bionic: false,
    reading_level: "simple",
    // standard | simple | very_simple
    format: "steps",
    // steps | short_paragraphs | bullets
    tone_notes: "off",
    // off | on
    break_reminders: "off",
    // off | 25 | 45
    confirm_actions: true,
    calm_mode: false,
    // 4. Audio
    tts_engine: "auto",
    // auto | browser | server
    tts_voice: "auto",
    tts_rate: 0.95,
    // 0.5 - 2.0
    tts_pitch: 1,
    // 0.8 - 1.2
    tts_volume: 1,
    // 0 - 1.0
    tts_pause_ms: 350,
    // 0 - 1500 ms
    tts_follow: "sentence",
    // none | sentence | word
    tts_autoread: "off",
    // off | result | page
    tts_spoken_numbers: true,
    captions_default: true,
    transcript_always: true,
    visual_alerts: true,
    vibration_alerts: false,
    sound_effects: "off",
    // 5. Highlighting
    highlight_mode: "light",
    // off | light | medium | strong
    highlight_categories: ["action", "deadline", "warning"],
    highlight_style: "combo",
    // combo | background | underline | bold | larger
    highlight_scale: 110,
    // 100 - 140 %
    highlight_palette: "multi",
    // yellow | multi | mono
    // 6. Motor / Input
    target_size: 48,
    // 44 | 48 | 56 | 64 px
    target_gap: 12,
    // 8 | 12 | 16 | 24 px
    keyboard_shortcuts: true,
    single_key_shortcuts: false,
    voice_commands: false,
    tooltips_on_focus_click: true,
    no_drag: true,
    // 7. Screen Reader
    sr_mode: false,
    announce_level: "polite",
    // minimal | polite | assertive
    describe_images: "ask",
    // auto | ask | off
    magnify_focus: false,
    // 8. Language
    ui_language: "ro"
  });
  var VALID_ENUMS = {
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
  var NUMERIC_RANGES = {
    font_scale: [70, 200],
    line_height: [1.2, 2.4],
    letter_spacing: [0, 0.2],
    word_spacing: [0, 0.5],
    paragraph_spacing: [0.5, 3],
    measure: [40, 100],
    saturation: [0, 100],
    dim_overlay: [0, 60],
    ruler_height: [16, 120],
    tts_rate: [0.5, 2],
    tts_pitch: [0.8, 1.2],
    tts_volume: [0, 1],
    tts_pause_ms: [0, 1500],
    highlight_scale: [100, 140]
  };
  function normalizeSetting(key, val) {
    if (val === void 0 || val === null) return DEFAULTS[key];
    if (key in VALID_ENUMS) {
      const allowed = VALID_ENUMS[key];
      const coerced = typeof val === "string" ? val.trim() : val;
      if (allowed.includes(coerced)) return coerced;
      if (typeof coerced === "string") {
        const lower = coerced.toLowerCase();
        const match = allowed.find((a) => String(a).toLowerCase() === lower);
        if (match !== void 0) return match;
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
      const filtered = val.filter((c) => allowedCats.includes(c));
      return filtered.length > 0 ? filtered : DEFAULTS.highlight_categories;
    }
    return val;
  }
  function migrateLegacySettings() {
    const migrated = { ...DEFAULTS };
    if (typeof localStorage === "undefined") return migrated;
    try {
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
      const welcomeRaw = localStorage.getItem("primazi_welcome_v1");
      if (welcomeRaw) {
        const welcome = JSON.parse(welcomeRaw);
        if (welcome.preset && PRESETS[welcome.preset]) {
          Object.assign(migrated, PRESETS[welcome.preset].values);
        }
      }
    } catch (err) {
    }
    return migrated;
  }
  var currentSettings = { ...DEFAULTS };
  var listeners = /* @__PURE__ */ new Set();
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
    }
  }
  function applyDOMAttributes(s, root = typeof document !== "undefined" ? document.documentElement : null) {
    if (!root) return;
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
  currentSettings = loadInitialSettings();
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
          listeners.forEach((cb) => {
            try {
              cb("*", currentSettings, currentSettings);
            } catch (_) {
            }
          });
        } catch (_) {
        }
      }
    });
  }
  var settings = new Proxy(currentSettings, {
    get(target, prop) {
      if (prop in target) return target[prop];
      return DEFAULTS[prop];
    },
    set() {
      throw new Error("Use setSetting(key, val) or setMany(partial) to mutate settings.");
    }
  });

  // extension/src/shared/tts.js
  var synth = typeof window !== "undefined" ? window.speechSynthesis : null;
  var currentUtterance = null;
  var sentences = [];
  var currentIndex = -1;
  var isPlaying = false;
  var isPaused = false;
  var activeHighlightEl = null;
  var stateListeners = /* @__PURE__ */ new Set();
  function splitSentencesRo(text) {
    if (!text) return [];
    const raw = text.replace(/([.?!])\s+(?=[A-ZĂÂÎȘȚ0-9])/g, "$1\n").split("\n");
    return raw.map((s) => s.trim()).filter(Boolean);
  }
  function getTTSState() {
    return {
      isPlaying,
      isPaused,
      currentIndex,
      totalSentences: sentences.length,
      currentSentence: currentIndex >= 0 && currentIndex < sentences.length ? sentences[currentIndex] : null
    };
  }
  function notifyState() {
    const state = getTTSState();
    stateListeners.forEach((cb) => {
      try {
        cb(state);
      } catch (_) {
      }
    });
  }
  function clearHighlight() {
    if (activeHighlightEl) {
      activeHighlightEl.classList.remove("tts-reading-sentence");
      activeHighlightEl = null;
    }
    document.querySelectorAll(".tts-reading-sentence").forEach((el) => {
      el.classList.remove("tts-reading-sentence");
    });
  }
  function stop() {
    if (synth) {
      try {
        synth.cancel();
      } catch (_) {
      }
    }
    isPlaying = false;
    isPaused = false;
    currentIndex = -1;
    sentences = [];
    currentUtterance = null;
    clearHighlight();
    notifyState();
  }
  if (typeof document !== "undefined") {
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && isPlaying) {
        stop();
      }
    });
  }

  // extension/src/content/local_mode.js
  var IMPORTANT_WORDS_RO = [
    "urgent",
    "termen",
    "termen limit\u0103",
    "p\xE2n\u0103 la",
    "vineri",
    "luni",
    "mar\u021Bi",
    "miercuri",
    "joi",
    "ora",
    "important",
    "obligatoriu",
    "formular",
    "raport",
    "completat",
    "trimite",
    "responsabil",
    "procedur\u0103",
    "\u0219edin\u021B\u0103",
    "aprobare",
    "decizie",
    "termen:",
    "aten\u021Bie",
    "cerin\u021B\u0103",
    "contact"
  ];
  var NUMBER_DATE_REGEX = /\b(?:\d{1,2}[:.]\d{2}|\d{1,2}\s+(?:ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie)|\d+(?:[.,]\d+)?\s*(?:lei|ron|eur|euro|%|kg|km|zile|ore|minute)|F-\d+|\b\d+\b)/gi;
  var FILLERS_RO = [
    /\bvă informăm că\b/gi,
    /\bvă aducem la cunoștință că\b/gi,
    /\bmenționăm faptul că\b/gi,
    /\bîn ceea ce privește\b/gi,
    /\beste de reținut faptul că\b/gi,
    /\bse solicită cu amabilitate\b/gi,
    /\bîn vederea asigurării\b/gi,
    /\bcu privire la\b/gi,
    /\bîn mod deosebit\b/gi,
    /\bdupă cum urmează\b/gi
  ];
  function splitSentences(text) {
    if (!text) return [];
    return text.split(/(?<=[.!?])\s+|\n+/).map((s) => s.trim()).filter((s) => s.length > 0);
  }
  function extractKeyPhrases(text) {
    if (!text) return [];
    const matches = /* @__PURE__ */ new Set();
    const numberMatches = text.match(NUMBER_DATE_REGEX) || [];
    for (const nm of numberMatches) {
      if (nm.trim().length > 1) {
        matches.add(nm.trim());
      }
    }
    for (const word of IMPORTANT_WORDS_RO) {
      const regex = new RegExp(`\\b${word}\\b`, "i");
      const m = text.match(regex);
      if (m) {
        matches.add(m[0]);
      }
    }
    return Array.from(matches).slice(0, 8);
  }
  function cleanFillers(text) {
    let cleaned = text;
    for (const pattern of FILLERS_RO) {
      cleaned = cleaned.replace(pattern, "");
    }
    return cleaned.replace(/\s{2,}/g, " ").trim();
  }
  function condenseSentence(sentence) {
    let s = cleanFillers(sentence);
    const patterns = [
      [
        /^Compania\s+(?:a\s+stabilit|anunță|solicită)\s+(?:procedura\s+obligatorie\s+pentru\s+)?/i,
        ""
      ],
      [/^Conducerea\s+(?:a\s+stabilit|anunță|solicită)\s+/i, ""],
      [
        /^Toți\s+angajații\s+(?:trebuie\s+să|sunt\s+rugați\s+să|au\s+obligația\s+să)\s+/i,
        ""
      ],
      [/^Este\s+(?:necesar|obligatoriu)\s+să\s+/i, ""],
      [
        /^Ar\s+fi\s+(?:foarte\s+)?(?:frumos|bine)\s+dacă\s+(?:ai\s+putea\s+)?/i,
        ""
      ],
      [/^Vă\s+rugăm\s+să\s+/i, ""],
      [/^Se\s+aduce\s+la\s+cunoștință\s+că\s+/i, ""],
      [/^Plafonul\s+maxim\s+aprobat\s+este\s+de\s+/i, "Plafon: "],
      [/,?\s*iar\s+sumele\s+se\s+virează\s+în\s+cont\s+în\s+/i, ". Plata \xEEn "],
      [/,?\s*la\s+departamentul\s+financiar\s+din\s+/i, " ("]
    ];
    for (const [re, rep] of patterns) {
      s = s.replace(re, rep);
    }
    s = s.replace(/\bdepun[ăa]\b/gi, "depune");
    s = s.replace(/\barunca\b/gi, "arunc\u0103");
    s = s.trim();
    if (s.includes("(") && !s.includes(")")) s += ")";
    if (s.length > 0) {
      s = s.charAt(0).toUpperCase() + s.slice(1);
      if (!/[.!?]$/.test(s)) s += ".";
    }
    return s;
  }
  function estimateReadability(text) {
    const sentences2 = splitSentences(text);
    if (sentences2.length === 0) return 50;
    const words = text.split(/\s+/).filter(Boolean);
    if (words.length === 0) return 50;
    const wordsPerSentence = words.length / sentences2.length;
    let score = 90 - wordsPerSentence * 2.2;
    return Math.max(10, Math.min(95, Math.round(score * 10) / 10));
  }
  function adaptLocally(text, action = "simplify") {
    const raw = (text || "").trim();
    const sentences2 = splitSentences(raw);
    const beforeScore = estimateReadability(raw);
    let adaptedText = "";
    let bullets = [];
    if (action === "bullets") {
      bullets = sentences2.map((s) => {
        let cleaned = cleanFillers(s);
        return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
      });
      adaptedText = bullets.join("\n");
    } else if (action === "shorter") {
      const condensed = sentences2.map((s) => condenseSentence(s));
      if (condensed.length > 2) {
        const kept = [];
        for (const s of condensed) {
          if (NUMBER_DATE_REGEX.test(s) || IMPORTANT_WORDS_RO.some((w) => s.toLowerCase().includes(w))) {
            kept.push(s);
          }
        }
        adaptedText = (kept.length > 0 ? kept : condensed.slice(0, 2)).join(" ");
      } else {
        adaptedText = condensed.join(" ");
      }
      bullets = splitSentences(adaptedText);
    } else {
      const simplifiedSentences = sentences2.map((s) => {
        let cleaned = cleanFillers(s);
        return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
      });
      adaptedText = simplifiedSentences.join(" ");
      bullets = simplifiedSentences.slice(0, 5);
    }
    const keyPhrases = extractKeyPhrases(adaptedText);
    const afterScore = estimateReadability(adaptedText);
    return {
      request_id: `local-${Date.now()}`,
      language: "ro",
      text: adaptedText,
      key_phrases: keyPhrases,
      bullets,
      notes: [],
      warnings: [],
      metrics: {
        readability_before: beforeScore,
        readability_after: Math.max(beforeScore, afterScore)
      },
      mode: "local"
    };
  }

  // extension/src/content/card.js
  var CARD_STYLES = `
  :host {
    all: initial;
    font-family: 'Lexend', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: #1e293b;
    box-sizing: border-box;
    z-index: 2147483647;
  }
  *, *::before, *::after {
    box-sizing: border-box;
  }

  /* Floating trigger button */
  .primazi-floating-btn {
    position: absolute;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    min-height: 44px;
    background: #0d9488;
    color: #ffffff;
    font-size: 15px;
    font-weight: 600;
    border: none;
    border-radius: 9999px;
    box-shadow: 0 4px 14px rgba(13, 148, 136, 0.4), 0 2px 6px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: transform 0.15s ease, background-color 0.15s ease;
    z-index: 2147483647;
    outline: none;
  }
  .primazi-floating-btn:hover {
    background: #0f766e;
    transform: translateY(-2px);
  }
  .primazi-floating-btn:focus-visible {
    outline: 3px solid #f59e0b;
    outline-offset: 2px;
  }
  .primazi-floating-btn svg {
    width: 18px;
    height: 18px;
    fill: currentColor;
  }

  /* Card overlay backdrop */
  .primazi-overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    z-index: 2147483647;
  }

  /* Accessible Card */
  .primazi-card {
    background: #ffffff;
    color: #1e293b;
    border: 2px solid #0d9488;
    border-radius: 16px;
    width: 100%;
    max-width: 640px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    animation: primaziFadeIn 0.2s ease-out;
  }

  @keyframes primaziFadeIn {
    from { opacity: 0; transform: scale(0.96); }
    to { opacity: 1; transform: scale(1); }
  }

  @keyframes primaziPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.55; }
  }

  /* Theme overrides */
  .primazi-card.theme-dark {
    background: #0f172a;
    color: #f8fafc;
    border-color: #38bdf8;
  }
  .primazi-card.theme-high-contrast {
    background: #000000;
    color: #ffff00;
    border: 3px solid #ffff00;
  }
  .primazi-card.theme-soft-dark {
    background: #1e293b;
    color: #f1f5f9;
    border-color: #0d9488;
  }

  /* Header */
  .primazi-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    background: rgba(13, 148, 136, 0.06);
  }
  .primazi-card.theme-dark .primazi-header,
  .primazi-card.theme-high-contrast .primazi-header {
    border-bottom: 1px solid currentColor;
    background: transparent;
  }

  .primazi-title-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .primazi-title {
    font-size: 18px;
    font-weight: 700;
    margin: 0;
  }
  .primazi-badge {
    font-size: 12px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 999px;
    background: #0d9488;
    color: #ffffff;
  }
  .primazi-badge.local {
    background: #e2e8f0;
    color: #475569;
    border: 1px solid #cbd5e1;
  }
  .primazi-badge.loading {
    background: #0284c7;
    color: #ffffff;
    animation: primaziPulse 1.4s infinite;
  }
  .primazi-card.theme-high-contrast .primazi-badge {
    background: #000000;
    color: #ffff00;
    border: 1px solid #ffff00;
  }

  /* Action Buttons bar */
  .primazi-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 20px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
    background: rgba(248, 250, 252, 0.8);
  }
  .primazi-card.theme-dark .primazi-actions,
  .primazi-card.theme-high-contrast .primazi-actions {
    background: transparent;
    border-bottom: 1px solid currentColor;
  }

  .primazi-btn {
    min-height: 44px;
    min-width: 44px;
    padding: 8px 14px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    border-radius: 8px;
    border: 1.5px solid #cbd5e1;
    background: #ffffff;
    color: #334155;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .primazi-btn:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }
  .primazi-btn:focus-visible {
    outline: 3px solid #0d9488;
    outline-offset: 2px;
  }
  .primazi-btn.active {
    background: #0d9488;
    color: #ffffff;
    border-color: #0d9488;
  }
  .primazi-card.theme-dark .primazi-btn {
    background: #1e293b;
    color: #f8fafc;
    border-color: #475569;
  }
  .primazi-card.theme-dark .primazi-btn:hover {
    background: #334155;
  }
  .primazi-card.theme-high-contrast .primazi-btn {
    background: #000000;
    color: #ffff00;
    border-color: #ffff00;
  }
  .primazi-card.theme-high-contrast .primazi-btn:hover,
  .primazi-card.theme-high-contrast .primazi-btn.active {
    background: #ffff00;
    color: #000000;
  }

  .primazi-btn-close {
    background: transparent;
    border: none;
    font-size: 20px;
    line-height: 1;
    padding: 8px 12px;
    cursor: pointer;
    color: inherit;
    border-radius: 6px;
  }
  .primazi-btn-close:focus-visible {
    outline: 3px solid #0d9488;
  }

  /* Body Content */
  .primazi-body {
    padding: 20px;
    overflow-y: auto;
    flex: 1;
  }
  .primazi-text {
    font-size: 1.05rem;
    line-height: 1.7;
    margin: 0;
    white-space: pre-line;
  }
  .primazi-bullets-list {
    margin: 0;
    padding-left: 24px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .primazi-bullets-list li {
    line-height: 1.6;
  }

  /* Highlights */
  mark.primazi-highlight {
    background-color: #fef08a;
    color: #854d0e;
    padding: 2px 4px;
    border-radius: 4px;
    font-weight: 600;
  }
  .primazi-card.theme-dark mark.primazi-highlight {
    background-color: #854d0e;
    color: #fef08a;
  }
  .primazi-card.theme-high-contrast mark.primazi-highlight {
    background-color: #ffffff;
    color: #000000;
    outline: 2px solid #ffff00;
  }

  /* Notes */
  .primazi-notes {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .primazi-note-card {
    padding: 10px 14px;
    background: #f8fafc;
    border-left: 4px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    font-size: 14px;
  }
  .primazi-card.theme-dark .primazi-note-card {
    background: #1e293b;
    border-color: #38bdf8;
  }
  .primazi-card.theme-high-contrast .primazi-note-card {
    background: #000000;
    border: 1px solid #ffff00;
    color: #ffff00;
  }
  .primazi-note-badge {
    font-weight: 700;
    color: #2563eb;
    margin-right: 6px;
  }
  .primazi-card.theme-dark .primazi-note-badge {
    color: #38bdf8;
  }
  .primazi-card.theme-high-contrast .primazi-note-badge {
    color: #ffff00;
  }

  /* Footer */
  .primazi-footer {
    padding: 12px 20px;
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: #64748b;
  }
  .primazi-card.theme-dark .primazi-footer {
    color: #94a3b8;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  .primazi-card.theme-high-contrast .primazi-footer {
    color: #ffff00;
    border-top: 1px solid #ffff00;
  }

  /* Screen reader only */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }
`;
  var CardManager = class {
    constructor(onActionCallback) {
      this.onActionCallback = onActionCallback;
      this.shadowRoot = null;
      this.hostElement = null;
      this.floatingBtn = null;
      this.overlay = null;
      this.bodyContainer = null;
      this.lastActiveElement = null;
      this.currentData = null;
      this.originalText = "";
      this.showingOriginal = false;
      this.viewMode = "text";
      this.isSpeaking = false;
      this.currentUtterance = null;
      this.ttsSentences = [];
      this.ttsIndex = 0;
      this.ttsBtn = null;
      this.userPrefs = {};
      this.initShadowHost();
      this.initSpeechVoices();
    }
    initSpeechVoices() {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.getVoices();
        window.speechSynthesis.onvoiceschanged = () => {
          if (window.speechSynthesis) window.speechSynthesis.getVoices();
        };
      }
    }
    initShadowHost() {
      let host = document.getElementById("primazi-ext-root");
      if (!host) {
        host = document.createElement("div");
        host.id = "primazi-ext-root";
        document.documentElement.appendChild(host);
      }
      this.hostElement = host;
      this.shadowRoot = host.attachShadow({ mode: "closed" });
      const styleEl = document.createElement("style");
      styleEl.textContent = CARD_STYLES;
      this.shadowRoot.appendChild(styleEl);
      this.liveRegion = document.createElement("div");
      this.liveRegion.className = "sr-only";
      this.liveRegion.setAttribute("aria-live", "polite");
      this.liveRegion.setAttribute("aria-atomic", "true");
      this.shadowRoot.appendChild(this.liveRegion);
    }
    announce(message) {
      if (this.liveRegion) {
        this.liveRegion.textContent = "";
        setTimeout(() => {
          this.liveRegion.textContent = message;
        }, 50);
      }
    }
    setUserPrefs(prefs) {
      this.userPrefs = prefs || {};
    }
    /**
     * Shows floating trigger button near user's selection
     */
    showFloatingButton(x, y, selectedText) {
      this.hideFloatingButton();
      this.originalText = selectedText;
      const btn = document.createElement("button");
      btn.className = "primazi-floating-btn";
      btn.setAttribute("type", "button");
      btn.setAttribute("aria-label", "F\u0103 clar selec\u021Bia curent\u0103 cu PrimaZi");
      btn.innerHTML = `
      <svg viewBox="0 0 24 24">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
      </svg>
      <span>F\u0103 clar</span>
    `;
      const clampedX = Math.max(10, Math.min(window.innerWidth - 130, x));
      const clampedY = Math.max(10, y + window.scrollY + 10);
      btn.style.left = `${clampedX}px`;
      btn.style.top = `${clampedY}px`;
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        this.hideFloatingButton();
        if (this.onActionCallback) {
          this.onActionCallback("adapt", this.originalText, "simplify");
        }
      });
      this.shadowRoot.appendChild(btn);
      this.floatingBtn = btn;
    }
    hideFloatingButton() {
      if (this.floatingBtn) {
        this.floatingBtn.remove();
        this.floatingBtn = null;
      }
    }
    /**
     * Shows immediate loading card so the user sees instant feedback.
     */
    showLoadingCard(selectedText) {
      this.hideFloatingButton();
      this.closeCard();
      this.originalText = selectedText || this.originalText;
      this.lastActiveElement = document.activeElement;
      const overlay = document.createElement("div");
      overlay.className = "primazi-overlay";
      const card = document.createElement("div");
      card.className = "primazi-card";
      card.setAttribute("role", "dialog");
      card.setAttribute("aria-modal", "true");
      card.setAttribute("aria-labelledby", "primazi-card-title");
      const p = this.userPrefs?.prefs || {};
      if (p.theme === "dark" || p.theme === "soft_dark") {
        card.classList.add("theme-dark");
      } else if (p.theme === "high_contrast") {
        card.classList.add("theme-high-contrast");
      }
      if (p.font_scale) {
        card.style.fontSize = `${16 * Number(p.font_scale)}px`;
      }
      const header = document.createElement("header");
      header.className = "primazi-header";
      const titleRow = document.createElement("div");
      titleRow.className = "primazi-title-row";
      const title = document.createElement("h2");
      title.id = "primazi-card-title";
      title.className = "primazi-title";
      title.textContent = "PrimaZi Claritate";
      const badge = document.createElement("span");
      badge.className = "primazi-badge loading";
      badge.textContent = "Se adapteaz\u0103...";
      titleRow.appendChild(title);
      titleRow.appendChild(badge);
      const closeBtn = document.createElement("button");
      closeBtn.className = "primazi-btn-close";
      closeBtn.setAttribute("type", "button");
      closeBtn.setAttribute("aria-label", "\xCEnchide dialogul (Esc)");
      closeBtn.textContent = "\u2715";
      closeBtn.addEventListener("click", () => this.closeCard());
      header.appendChild(titleRow);
      header.appendChild(closeBtn);
      const bodyContainer = document.createElement("div");
      bodyContainer.className = "primazi-body";
      const loadingText = document.createElement("p");
      loadingText.className = "primazi-text";
      loadingText.style.fontStyle = "italic";
      loadingText.textContent = "\u2728 Se adapteaz\u0103 textul conform profilului t\u0103u de confort...";
      bodyContainer.appendChild(loadingText);
      const footer = document.createElement("footer");
      footer.className = "primazi-footer";
      const disclaimer = document.createElement("span");
      disclaimer.textContent = "Procesare text cu asisten\u021B\u0103 de accesibilitate...";
      footer.appendChild(disclaimer);
      card.appendChild(header);
      card.appendChild(bodyContainer);
      card.appendChild(footer);
      overlay.appendChild(card);
      const keyHandler = (e) => {
        if (e.key === "Escape") {
          e.preventDefault();
          this.closeCard();
        }
      };
      this.overlayKeyHandler = keyHandler;
      window.addEventListener("keydown", keyHandler);
      this.shadowRoot.appendChild(overlay);
      this.overlay = overlay;
      this.announce("Se adapteaz\u0103 textul...");
    }
    /**
     * Updates shorter text in-place when received asynchronously.
     */
    updateShorterData(data) {
      if (!this.currentData) this.currentData = {};
      if (data && data.text) {
        this.currentData.shorterText = data.text;
        if (data.key_phrases?.length) {
          this.currentData.shorterKeyPhrases = data.key_phrases;
        }
        if (this.viewMode === "shorter" && this.bodyContainer) {
          this.renderBodyContent(this.bodyContainer);
        }
      }
    }
    /**
     * Renders the accessible dialog card with result data
     */
    showCard(data, originalText, initialMode = "text") {
      this.hideFloatingButton();
      this.closeCard();
      this.currentData = data;
      this.originalText = originalText || this.originalText;
      this.lastActiveElement = document.activeElement;
      this.showingOriginal = false;
      this.viewMode = initialMode === "shorter" ? "shorter" : initialMode === "bullets" ? "bullets" : data.bullets && data.bullets.length > 0 && !data.text ? "bullets" : "text";
      const overlay = document.createElement("div");
      overlay.className = "primazi-overlay";
      const card = document.createElement("div");
      card.className = "primazi-card";
      card.setAttribute("role", "dialog");
      card.setAttribute("aria-modal", "true");
      card.setAttribute("aria-labelledby", "primazi-card-title");
      const p = this.userPrefs?.prefs || {};
      if (p.theme === "dark" || p.theme === "soft_dark") {
        card.classList.add("theme-dark");
      } else if (p.theme === "high_contrast") {
        card.classList.add("theme-high-contrast");
      }
      if (p.font_scale) {
        card.style.fontSize = `${16 * Number(p.font_scale)}px`;
      }
      const header = document.createElement("header");
      header.className = "primazi-header";
      const titleRow = document.createElement("div");
      titleRow.className = "primazi-title-row";
      const title = document.createElement("h2");
      title.id = "primazi-card-title";
      title.className = "primazi-title";
      title.textContent = "PrimaZi Claritate";
      const badge = document.createElement("span");
      const isLocal = data.mode === "local";
      badge.className = `primazi-badge ${isLocal ? "local" : ""}`;
      badge.textContent = isLocal ? "Mod de baz\u0103 (offline)" : "AI";
      titleRow.appendChild(title);
      titleRow.appendChild(badge);
      const closeBtn = document.createElement("button");
      closeBtn.className = "primazi-btn-close";
      closeBtn.setAttribute("type", "button");
      closeBtn.setAttribute("aria-label", "\xCEnchide dialogul (Esc)");
      closeBtn.textContent = "\u2715";
      closeBtn.addEventListener("click", () => this.closeCard());
      header.appendChild(titleRow);
      header.appendChild(closeBtn);
      const actions = document.createElement("nav");
      actions.className = "primazi-actions";
      actions.setAttribute("aria-label", "Op\u021Biuni de adaptare");
      const listenBtn = document.createElement("button");
      listenBtn.className = "primazi-btn";
      listenBtn.setAttribute("type", "button");
      listenBtn.textContent = "\u{1F50A} Ascult\u0103";
      listenBtn.addEventListener("click", () => this.toggleReadAloud(listenBtn));
      actions.appendChild(listenBtn);
      const bulletsBtn = document.createElement("button");
      bulletsBtn.className = `primazi-btn ${this.viewMode === "bullets" ? "active" : ""}`;
      bulletsBtn.setAttribute("type", "button");
      bulletsBtn.textContent = "\u2022 Buline";
      bulletsBtn.addEventListener("click", () => {
        this.viewMode = this.viewMode === "bullets" ? "text" : "bullets";
        bulletsBtn.classList.toggle("active", this.viewMode === "bullets");
        if (this.viewMode === "bullets") {
          shorterBtn.classList.remove("active");
          origBtn.classList.remove("active");
          this.showingOriginal = false;
        }
        this.renderBodyContent(bodyContainer);
        this.announce(
          this.viewMode === "bullets" ? "Afi\u0219at ca list\u0103 de buline." : "Afi\u0219at ca text continuu."
        );
      });
      actions.appendChild(bulletsBtn);
      const shorterBtn = document.createElement("button");
      shorterBtn.className = `primazi-btn ${this.viewMode === "shorter" ? "active" : ""}`;
      shorterBtn.setAttribute("type", "button");
      shorterBtn.textContent = "\u2702\uFE0F Mai scurt";
      shorterBtn.addEventListener("click", () => {
        this.viewMode = this.viewMode === "shorter" ? "text" : "shorter";
        shorterBtn.classList.toggle("active", this.viewMode === "shorter");
        if (this.viewMode === "shorter") {
          bulletsBtn.classList.remove("active");
          origBtn.classList.remove("active");
          this.showingOriginal = false;
          if (!this.currentData.shorterText) {
            const localShorter = adaptLocally(this.originalText, "shorter");
            this.currentData.shorterText = localShorter.text;
            this.currentData.shorterKeyPhrases = localShorter.key_phrases;
            if (this.onActionCallback) {
              this.onActionCallback(
                "adapt_in_place",
                this.originalText,
                "shorter"
              );
            }
          }
        }
        this.renderBodyContent(bodyContainer);
        this.announce(
          this.viewMode === "shorter" ? "Afi\u0219at \xEEn format mai scurt \u0219i comprimat." : "Afi\u0219at ca text continuu."
        );
      });
      actions.appendChild(shorterBtn);
      const copyBtn = document.createElement("button");
      copyBtn.className = "primazi-btn";
      copyBtn.setAttribute("type", "button");
      copyBtn.textContent = "\u{1F4CB} Copiaz\u0103";
      copyBtn.addEventListener("click", () => {
        let textToCopy = "";
        if (this.showingOriginal) {
          textToCopy = this.originalText;
        } else if (this.viewMode === "shorter") {
          textToCopy = this.currentData?.shorterText || adaptLocally(this.originalText, "shorter").text;
        } else if (this.viewMode === "bullets" && this.currentData?.bullets?.length) {
          textToCopy = this.currentData.bullets.join("\n");
        } else {
          textToCopy = this.currentData?.text || this.originalText;
        }
        navigator.clipboard.writeText(textToCopy).then(() => {
          copyBtn.textContent = "\u2713 Copiat!";
          setTimeout(() => {
            copyBtn.textContent = "\u{1F4CB} Copiaz\u0103";
          }, 2e3);
          this.announce("Textul a fost copiat \xEEn clipboard.");
        });
      });
      actions.appendChild(copyBtn);
      const origBtn = document.createElement("button");
      origBtn.className = "primazi-btn";
      origBtn.setAttribute("type", "button");
      origBtn.textContent = "\u{1F441}\uFE0F Original";
      origBtn.addEventListener("click", () => {
        this.showingOriginal = !this.showingOriginal;
        origBtn.classList.toggle("active", this.showingOriginal);
        this.renderBodyContent(bodyContainer);
        this.announce(
          this.showingOriginal ? "Se afi\u0219eaz\u0103 textul original neschimbat." : "Se afi\u0219eaz\u0103 textul adaptat."
        );
      });
      actions.appendChild(origBtn);
      const bodyContainer = document.createElement("div");
      bodyContainer.className = "primazi-body";
      this.bodyContainer = bodyContainer;
      this.renderBodyContent(bodyContainer);
      const footer = document.createElement("footer");
      footer.className = "primazi-footer";
      const disclaimer = document.createElement("span");
      disclaimer.textContent = isLocal ? "Formatat local pe dispozitiv. Verific\u0103 detaliile \xEEn original." : "Adaptat cu asisten\u021B\u0103 AI. Verific\u0103 detaliile importante \xEEn original.";
      const metricsSpan = document.createElement("span");
      if (data.metrics) {
        metricsSpan.textContent = `Claritate: ${Math.round(data.metrics.readability_before)}% \u2192 ${Math.round(data.metrics.readability_after)}%`;
      }
      footer.appendChild(disclaimer);
      footer.appendChild(metricsSpan);
      card.appendChild(header);
      card.appendChild(actions);
      card.appendChild(bodyContainer);
      card.appendChild(footer);
      overlay.appendChild(card);
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) this.closeCard();
      });
      const keyHandler = (e) => {
        if (e.key === "Escape") {
          e.preventDefault();
          this.closeCard();
        } else if (e.key === "Tab") {
          this.trapFocus(e, card);
        }
      };
      this.overlayKeyHandler = keyHandler;
      window.addEventListener("keydown", keyHandler);
      this.shadowRoot.appendChild(overlay);
      this.overlay = overlay;
      listenBtn.focus();
      this.announce(
        `Textul a fost clarificat. ${data.key_phrases?.length || 0} concepte importante eviden\u021Biate.`
      );
    }
    /**
     * Safely renders body content using DOM elements and text nodes (NO innerHTML with AI text)
     */
    renderBodyContent(container) {
      container.innerHTML = "";
      if (this.showingOriginal) {
        const p = document.createElement("p");
        p.className = "primazi-text";
        p.textContent = this.originalText;
        container.appendChild(p);
        return;
      }
      const data = this.currentData;
      if (!data) return;
      if (this.viewMode === "shorter") {
        const p = document.createElement("p");
        p.className = "primazi-text";
        const shorterText = data.shorterText || adaptLocally(this.originalText, "shorter").text;
        const keyPhrases = data.shorterKeyPhrases?.length ? data.shorterKeyPhrases : data.key_phrases?.length ? data.key_phrases : extractKeyPhrases(shorterText);
        this.renderTextWithHighlights(p, shorterText, keyPhrases);
        container.appendChild(p);
      } else if (this.viewMode === "bullets" && data.bullets && data.bullets.length > 0) {
        const ul = document.createElement("ul");
        ul.className = "primazi-bullets-list";
        for (const bullet of data.bullets) {
          const li = document.createElement("li");
          this.renderTextWithHighlights(li, bullet, data.key_phrases);
          ul.appendChild(li);
        }
        container.appendChild(ul);
      } else {
        const p = document.createElement("p");
        p.className = "primazi-text";
        const fullText = data.text || (data.bullets || []).join("\n");
        this.renderTextWithHighlights(p, fullText, data.key_phrases);
        container.appendChild(p);
      }
      if (data.notes && data.notes.length > 0) {
        const notesContainer = document.createElement("div");
        notesContainer.className = "primazi-notes";
        for (const noteItem of data.notes) {
          const noteBox = document.createElement("div");
          noteBox.className = "primazi-note-card";
          const badge = document.createElement("span");
          badge.className = "primazi-note-badge";
          const kindLabel = {
            indirect_request: "Cerere politicoas\u0103:",
            possible_joke: "Posibil\u0103 glum\u0103 (nesigur):",
            idiom: "Expresie figurat\u0103:",
            urgency: "Urgen\u021B\u0103:",
            softener: "Nuan\u021B\u0103:"
          }[noteItem.kind] || "Not\u0103:";
          badge.textContent = kindLabel;
          const noteText = document.createTextNode(
            ` \u201E${noteItem.quote}\u201D \u2014 ${noteItem.note}`
          );
          noteBox.appendChild(badge);
          noteBox.appendChild(noteText);
          notesContainer.appendChild(noteBox);
        }
        container.appendChild(notesContainer);
      }
    }
    /**
     * Slices text into text nodes and <mark> elements for exact key phrases substrings.
     * Completely safe against XSS; zero innerHTML.
     */
    renderTextWithHighlights(targetNode, text, keyPhrases = []) {
      if (!keyPhrases || keyPhrases.length === 0) {
        targetNode.appendChild(document.createTextNode(text));
        return;
      }
      const sorted = [...new Set(keyPhrases)].filter((p) => p && p.trim().length > 1).sort((a, b) => b.length - a.length);
      if (sorted.length === 0) {
        targetNode.appendChild(document.createTextNode(text));
        return;
      }
      const pattern = sorted.map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|");
      const regex = new RegExp(`(${pattern})`, "gi");
      const parts = text.split(regex);
      for (const part of parts) {
        if (!part) continue;
        const isMatch = sorted.some(
          (k) => k.toLowerCase() === part.toLowerCase()
        );
        if (isMatch) {
          const mark = document.createElement("mark");
          mark.className = "primazi-highlight";
          mark.appendChild(document.createTextNode(part));
          targetNode.appendChild(mark);
        } else {
          targetNode.appendChild(document.createTextNode(part));
        }
      }
    }
    /**
     * Trap Tab focus inside the active card
     */
    trapFocus(e, card) {
      const focusable = card.querySelectorAll(
        "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const activeEl = this.shadowRoot?.activeElement || document.activeElement;
      if (e.shiftKey && activeEl === first) {
        last.focus();
        e.preventDefault();
      } else if (!e.shiftKey && activeEl === last) {
        first.focus();
        e.preventDefault();
      }
    }
    /**
     * Natural sentence-by-sentence Romanian TTS with reliable speech synthesis
     */
    toggleReadAloud(btn) {
      if (this.isSpeaking) {
        this.stopReadAloud(btn);
        this.announce("Redarea vocal\u0103 a fost oprit\u0103.");
        return;
      }
      if (typeof window === "undefined" || !window.speechSynthesis) {
        this.announce("Sinteza vocal\u0103 nu este suportat\u0103 \xEEn acest browser.");
        return;
      }
      let textToRead = "";
      if (this.showingOriginal) {
        textToRead = this.originalText;
      } else if (this.viewMode === "shorter") {
        textToRead = this.currentData?.shorterText || adaptLocally(this.originalText, "shorter").text;
      } else if (this.viewMode === "bullets" && this.currentData?.bullets?.length) {
        textToRead = this.currentData.bullets.join(". ");
      } else {
        textToRead = this.currentData?.text || this.originalText;
      }
      if (!textToRead) return;
      const sentences2 = splitSentencesRo(textToRead);
      if (!sentences2.length) return;
      this.isSpeaking = true;
      this.ttsIndex = 0;
      this.ttsSentences = sentences2;
      this.ttsBtn = btn;
      btn.textContent = "\u23F9\uFE0F Opre\u0219te";
      btn.classList.add("active");
      this.playNextTtsSentence();
      this.announce("Se cite\u0219te textul cu voce tare.");
    }
    playNextTtsSentence() {
      if (!this.isSpeaking || !window.speechSynthesis) return;
      if (this.ttsIndex >= this.ttsSentences.length) {
        this.stopReadAloud(this.ttsBtn);
        return;
      }
      const raw = this.ttsSentences[this.ttsIndex];
      const normalized = normalizeRomanianForSpeech(raw);
      const utt = new SpeechSynthesisUtterance(normalized);
      utt.rate = Number(this.userPrefs?.prefs?.speech_rate) || 0.95;
      const voices = window.speechSynthesis.getVoices() || [];
      const roVoice = voices.find(
        (v) => v.lang && (v.lang === "ro-RO" || v.lang.startsWith("ro")) || /romanian|alina|emil/i.test(v.name)
      );
      if (roVoice) {
        utt.voice = roVoice;
        utt.lang = roVoice.lang;
      } else {
        utt.lang = "ro-RO";
        const defaultVoice = voices.find((v) => v.default);
        if (defaultVoice) utt.voice = defaultVoice;
      }
      utt.onend = () => {
        if (this.isSpeaking) {
          this.ttsIndex++;
          setTimeout(() => this.playNextTtsSentence(), 200);
        }
      };
      utt.onerror = (e) => {
        if (e.error !== "canceled" && e.error !== "interrupted") {
          console.warn("TTS sentence error:", e);
          if (this.isSpeaking) {
            this.ttsIndex++;
            this.playNextTtsSentence();
          }
        }
      };
      this.currentUtterance = utt;
      try {
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utt);
      } catch (err) {
        console.warn("speechSynthesis speak failed:", err);
        this.stopReadAloud(this.ttsBtn);
      }
    }
    stopReadAloud(btn) {
      this.isSpeaking = false;
      this.currentUtterance = null;
      this.ttsSentences = [];
      this.ttsIndex = 0;
      if (typeof window !== "undefined" && window.speechSynthesis) {
        try {
          window.speechSynthesis.cancel();
        } catch (_) {
        }
      }
      const b = btn || this.ttsBtn;
      if (b) {
        b.textContent = "\u{1F50A} Ascult\u0103";
        b.classList.remove("active");
      }
    }
    closeCard() {
      this.stopReadAloud();
      if (this.overlayKeyHandler) {
        window.removeEventListener("keydown", this.overlayKeyHandler);
        this.overlayKeyHandler = null;
      }
      if (this.overlay) {
        this.overlay.remove();
        this.overlay = null;
      }
      this.bodyContainer = null;
      if (this.lastActiveElement && typeof this.lastActiveElement.focus === "function") {
        this.lastActiveElement.focus();
      }
    }
  };

  // extension/src/content/content.js
  var MAX_SELECTION_CHARS = 3e3;
  var PrimaZiContentScript = class {
    constructor() {
      this.userPrefs = null;
      this.config = null;
      this.cardManager = new CardManager((action, text, mode) => {
        this.handleAdaptAction(action, text, mode);
      });
      this.init();
    }
    async init() {
      try {
        const stored = await chrome.storage.local.get([
          "wp.ext.prefs.v1",
          "wp.ext.config"
        ]);
        if (stored["wp.ext.prefs.v1"]) {
          this.userPrefs = stored["wp.ext.prefs.v1"];
          this.cardManager.setUserPrefs(this.userPrefs);
        }
        if (stored["wp.ext.config"]) {
          this.config = stored["wp.ext.config"];
        }
      } catch (_) {
      }
      if (chrome.storage && chrome.storage.onChanged) {
        chrome.storage.onChanged.addListener((changes, area) => {
          if (area === "local") {
            if (changes["wp.ext.prefs.v1"]?.newValue) {
              this.userPrefs = changes["wp.ext.prefs.v1"].newValue;
              this.cardManager.setUserPrefs(this.userPrefs);
            }
            if (changes["wp.ext.config"]?.newValue) {
              this.config = changes["wp.ext.config"].newValue;
            }
          }
        });
      }
      this.checkSiteOriginSync();
      document.addEventListener("mouseup", (e) => this.onSelectionChange(e));
      document.addEventListener("keyup", (e) => {
        if (e.key === "Shift" || e.key === "ArrowLeft" || e.key === "ArrowRight") {
          this.onSelectionChange(e);
        }
      });
      chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
        if (msg.type === "TRIGGER_SELECTION") {
          this.triggerFromShortcutOrMenu(msg.selectedText);
          sendResponse({ ok: true });
        }
      });
    }
    /**
     * If current origin is in siteOrigins, read site's localStorage and sync
     */
    checkSiteOriginSync() {
      try {
        const siteStorageKey = "primazi.settings.v2";
        const raw = localStorage.getItem(siteStorageKey) || localStorage.getItem("wp.ext.prefs.v1") || localStorage.getItem("wp.prefs.v1");
        const userProfileRaw = localStorage.getItem("primazi_user_profile");
        let freeText = "";
        if (userProfileRaw) {
          try {
            const up = JSON.parse(userProfileRaw);
            if (up.needs_notes) freeText = up.needs_notes;
          } catch (_) {
          }
        }
        if (raw) {
          const parsed = JSON.parse(raw);
          if (freeText && !parsed.freeText) {
            parsed.freeText = freeText;
          }
          chrome.runtime.sendMessage({
            type: "PREFS_FROM_SITE",
            prefs: parsed,
            updatedAt: parsed.updatedAt || (/* @__PURE__ */ new Date()).toISOString()
          });
        }
      } catch (_) {
      }
    }
    /**
     * Check if element is a sensitive field (password)
     */
    isSensitiveElement(el) {
      if (!el) return false;
      if (el.tagName === "INPUT" && el.type === "password") return true;
      const parentPassword = el.closest && el.closest("input[type=password]");
      return !!parentPassword;
    }
    /**
     * Truncate text cleanly at sentence boundary if longer than MAX_SELECTION_CHARS
     */
    sanitizeAndTruncate(text) {
      if (!text) return "";
      let trimmed = text.trim();
      if (trimmed.length <= MAX_SELECTION_CHARS) return trimmed;
      const sentences2 = splitSentences(trimmed);
      let result = "";
      for (const s of sentences2) {
        if ((result + " " + s).trim().length > MAX_SELECTION_CHARS) {
          break;
        }
        result = (result + " " + s).trim();
      }
      return result.length > 0 ? result : trimmed.slice(0, MAX_SELECTION_CHARS);
    }
    onSelectionChange(e) {
      if (e.target && e.target.id === "primazi-ext-root") return;
      if (this.config && this.config.disabledSites && this.config.disabledSites.includes(window.location.hostname)) {
        this.cardManager.hideFloatingButton();
        return;
      }
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || !sel.rangeCount) {
        this.cardManager.hideFloatingButton();
        return;
      }
      const text = sel.toString().trim();
      if (text.length < 5) {
        this.cardManager.hideFloatingButton();
        return;
      }
      const anchorNode = sel.anchorNode;
      const focusNode = sel.focusNode;
      const anchorEl = anchorNode?.nodeType === Node.ELEMENT_NODE ? anchorNode : anchorNode?.parentElement;
      const focusEl = focusNode?.nodeType === Node.ELEMENT_NODE ? focusNode : focusNode?.parentElement;
      if (this.isSensitiveElement(anchorEl) || this.isSensitiveElement(focusEl)) {
        this.cardManager.hideFloatingButton();
        return;
      }
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) {
        this.cardManager.hideFloatingButton();
        return;
      }
      const posX = rect.right + 8;
      const posY = rect.bottom + 4;
      const sanitizedText = this.sanitizeAndTruncate(text);
      this.cardManager.showFloatingButton(posX, posY, sanitizedText);
    }
    triggerFromShortcutOrMenu(selectedText) {
      let text = (selectedText || "").trim();
      if (!text) {
        const sel = window.getSelection();
        if (sel && !sel.isCollapsed) {
          text = sel.toString().trim();
        }
      }
      if (!text) return;
      const sanitizedText = this.sanitizeAndTruncate(text);
      this.handleAdaptAction("adapt", sanitizedText, "simplify");
    }
    handleAdaptAction(actionType, text, mode = "simplify") {
      const requestId = `req-${Date.now()}`;
      const truncatedText = this.sanitizeAndTruncate(text);
      if (this.config && this.config.localOnly) {
        const localData = adaptLocally(truncatedText, mode);
        if (actionType === "adapt_in_place") {
          this.cardManager.updateShorterData(localData);
        } else {
          this.cardManager.showCard(localData, truncatedText, mode);
        }
        return;
      }
      if (actionType !== "adapt_in_place") {
        this.cardManager.showLoadingCard(truncatedText);
      }
      chrome.runtime.sendMessage(
        {
          type: "ADAPT",
          requestId,
          text: truncatedText,
          action: mode
        },
        (res) => {
          if (chrome.runtime.lastError || !res || res.type === "ERROR") {
            const localData = adaptLocally(truncatedText, mode);
            if (actionType === "adapt_in_place") {
              this.cardManager.updateShorterData(localData);
            } else {
              this.cardManager.showCard(localData, truncatedText, mode);
            }
            return;
          }
          if (res.type === "RESULT" && res.data) {
            if (actionType === "adapt_in_place") {
              this.cardManager.updateShorterData(res.data);
            } else {
              this.cardManager.showCard(res.data, truncatedText, mode);
            }
          } else {
            const localData = adaptLocally(truncatedText, mode);
            if (actionType === "adapt_in_place") {
              this.cardManager.updateShorterData(localData);
            } else {
              this.cardManager.showCard(localData, truncatedText, mode);
            }
          }
        }
      );
    }
  };
  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      () => new PrimaZiContentScript()
    );
  } else {
    new PrimaZiContentScript();
  }
})();
