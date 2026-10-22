/**
 * PrimaZi — Boot Script (Sync in <head>)
 * Runs synchronously before first paint to apply data-* attributes and CSS variables.
 * Guarantees zero flash of default style (FOUC) across page loads.
 * Ref: docs/SETTINGS-SPEC.md §0, §1, §2
 */
(() => {
  try {
    const STORAGE_KEY = "primazi.settings.v2";
    const root = document.documentElement;
    let s = null;

    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      s = JSON.parse(raw);
    } else {
      // Fast fallback from legacy keys if available
      const v1Raw = localStorage.getItem("primazi_prefs_v1");
      if (v1Raw) {
        const v1 = JSON.parse(v1Raw);
        s = {
          theme: v1.theme === "dark" ? "sapphire" : (v1.contrast === "high" ? "hc-dark" : "soft"),
          font_family: (v1.font === "dyslexic" || v1.font === "opendyslexic") ? "dyslexia" : (v1.font || "atkinson"),
          font_scale: v1.textSize === "large" ? 125 : (v1.textSize === "extra-large" ? 150 : 100),
          line_height: v1.spacing === "large" ? 1.8 : 1.6,
          sidebar: v1.sidebar || "expanded"
        };
      }
    }

    if (!s) {
      // OS media query defaults
      const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      const prefersContrast = window.matchMedia && window.matchMedia("(prefers-contrast: more)").matches;
      const prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      s = {
        theme: prefersContrast ? (prefersDark ? "hc-dark" : "hc-light") : (prefersDark ? "sapphire" : "soft"),
        font_family: "atkinson",
        font_scale: 100,
        line_height: 1.6,
        letter_spacing: 0.02,
        word_spacing: 0.05,
        paragraph_spacing: 1.0,
        measure: 68,
        font_weight: 400,
        saturation: 100,
        color_vision: "none",
        focus_ring: "normal",
        cursor_size: "normal",
        dim_overlay: 0,
        reduce_motion: prefersReducedMotion ? "on" : "auto",
        reduce_transparency: false,
        focus_level: 0,
        density: "comfortable",
        layout: "overview",
        sidebar: "expanded",
        target_size: 48,
        target_gap: 12
      };
    }

    // Apply data-* attributes
    if (s.theme) root.setAttribute("data-theme", s.theme);
    if (s.font_family) root.setAttribute("data-font", s.font_family);
    if (s.color_vision) root.setAttribute("data-cvd", s.color_vision);
    if (s.cursor_size) root.setAttribute("data-cursor", s.cursor_size);
    if (s.reduce_motion) root.setAttribute("data-motion", s.reduce_motion);
    if (typeof s.reduce_transparency !== "undefined") root.setAttribute("data-flat", s.reduce_transparency ? "true" : "false");
    if (typeof s.focus_level !== "undefined") root.setAttribute("data-focus", String(s.focus_level));
    if (s.density) root.setAttribute("data-density", s.density);
    if (s.layout) root.setAttribute("data-layout", s.layout);
    if (s.sidebar) root.setAttribute("data-sidebar", s.sidebar);

    // Apply CSS variables
    if (s.font_scale) root.style.setProperty("--font-scale", `${s.font_scale}%`);
    if (s.line_height) root.style.setProperty("--lh", String(s.line_height));
    if (typeof s.letter_spacing !== "undefined") root.style.setProperty("--ls", `${s.letter_spacing}em`);
    if (typeof s.word_spacing !== "undefined") root.style.setProperty("--ws", `${s.word_spacing}em`);
    if (typeof s.paragraph_spacing !== "undefined") root.style.setProperty("--ps", `${s.paragraph_spacing}em`);
    if (s.measure) root.style.setProperty("--measure", `${s.measure}ch`);
    if (s.font_weight) root.style.setProperty("--fw", String(s.font_weight));
    if (typeof s.saturation !== "undefined") root.style.setProperty("--sat", `${s.saturation}%`);

    const focusWidths = { normal: "3px", large: "5px", xlarge: "7px" };
    if (s.focus_ring) root.style.setProperty("--focus-w", focusWidths[s.focus_ring] || "3px");
    if (typeof s.dim_overlay !== "undefined") root.style.setProperty("--dim", `${s.dim_overlay}%`);
    if (s.target_size) root.style.setProperty("--target", `${s.target_size}px`);
    if (s.target_gap) root.style.setProperty("--gap", `${s.target_gap}px`);
  } catch (err) {
    // Fail safe to basic styles
  }
})();
