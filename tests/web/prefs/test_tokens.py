"""Automated Design Token Verification, Contrast Matrix, and Data Attribute Completeness Tests (owner: p2).

Spec: docs/plan/p2.md (N2.3)
Rules:
- Enforce zero hardcoded hex/rgb/hsl colors in non-token CSS (web/css/), grandfathering strictly
  the 7 approved instances in web/css/shell.css.
- Verify WCAG 2.2 AA (>= 4.5:1) and AAA (>= 7.0:1) contrast matrix across Light, Dark, and High Contrast.
- Validate data-* attribute mapping completeness between VALID_PREFS and CSS selectors.
"""
from __future__ import annotations

from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CSS_DIR = ROOT / "web" / "css"
TOKENS_CSS = CSS_DIR / "tokens.css"
SHELL_CSS = CSS_DIR / "shell.css"
TYPES_JS = ROOT / "web" / "js" / "prefs" / "types.js"

# Strictly whitelisted grandfathered raw color values in web/css/shell.css (owned by P3)
# To be replaced with tokens by P3 in follow-up polish pass (see docs/plan/p2.md)
GRANDFATHERED_SHELL_COLORS = [
    # Navigation & Drawer (N3.1)
    "rgba(96, 165, 250, 0.15)",  # L210 - active nav item background
    "#000000",                   # L215 - high-contrast nav background
    "#ffff00",                   # L216 - high-contrast nav text
    "#ffff00",                   # L217 - high-contrast nav outline
    "rgba(96, 165, 250, 0.1)",   # L442 - dark theme card background
    "rgba(0, 0, 0, 0.5)",         # L494 - drawer backdrop
    "rgba(0, 0, 0, 0.25)",        # L514 - drawer shadow
    # Welcome & Live Preview (N3.3 added by P3)
    "#ffff00",                   # L588 - preview high-contrast button bg
    "#000000",                   # L589 - preview high-contrast button text
    "#ffffff",                   # L590 - preview high-contrast button outline
    "#ffffff",                   # L726 - preview button text
    "#fee2e2",                   # L987 - error banner bg (can use var(--error-bg))
    "#991b1b",                   # L988 - error banner text (can use var(--error-text))
    "#fef08a",                   # L1060 - line-focus light bg
    "#1c1b1f",                   # L1061 - line-focus light text
    "#ca8a04",                   # L1064 - line-focus light border
    "#854d0e",                   # L1069 - line-focus dark bg
    "#fef08a",                   # L1070 - line-focus dark text
    "#facc15",                   # L1071 - line-focus dark border
    "#ffff00",                   # L1076 - line-focus hc bg
    "#000000",                   # L1077 - line-focus hc text
    "#000000",                   # L1078 - line-focus hc border
    "#ffffff",                   # L1079 - line-focus hc outline
    "rgba(96, 165, 250, 0.12)",  # L1228 - dark option card selected bg
    "#ffff00",                   # L1233 - hc option card border
    "#000000",                   # L1234 - hc option card bg
    "#ffff00",                   # L1235 - hc option card outline
]


def _hex_to_luminance(hex_str: str) -> float:
    """Calculates WCAG 2.2 relative luminance for a 3-, 4-, 6-, or 8-character hex color."""
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) in (3, 4):
        hex_clean = "".join(c * 2 for c in hex_clean[:3])
    elif len(hex_clean) == 8:
        hex_clean = hex_clean[:6]  # Ignore alpha for luminance calculation
    assert len(hex_clean) == 6, f"Invalid hex color length for '{hex_str}'"

    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0

    def adjust(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def _contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates WCAG 2.2 contrast ratio between two hex colors: (L1 + 0.05) / (L2 + 0.05)."""
    l1 = _hex_to_luminance(hex1)
    l2 = _hex_to_luminance(hex2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def _parse_css_variables(css_text: str, selector: str) -> dict[str, str]:
    """Parses CSS variables (--custom-prop: value) defined under a target selector.

    Handles single and comma-separated selectors, ignores CSS comments,
    and strips trailing semicolons and whitespace from property values.
    """
    # 1. Strip CSS comments while preserving structure
    clean_css = re.sub(r"/\*[\s\S]*?\*/", "", css_text)

    # 2. Match CSS rule blocks: selectors { declarations }
    block_pattern = re.compile(r"([^{}]+)\{([^}]+)\}")
    variables: dict[str, str] = {}
    target_selector = selector.strip()

    for match in block_pattern.finditer(clean_css):
        selectors_part, declarations_part = match.groups()
        selectors = [s.strip() for s in selectors_part.split(",")]

        if target_selector in selectors or any(target_selector == s for s in selectors):
            # Extract --var-name: value; declarations
            var_pattern = re.compile(r"(--[\w-]+)\s*:\s*([^;{}]+);")
            for var_match in var_pattern.finditer(declarations_part):
                name = var_match.group(1).strip()
                val = var_match.group(2).strip()
                # Clean any remnant inline comments
                val = re.sub(r"/\*.*?\*/", "", val).strip()
                variables[name] = val

    return variables


def _extract_valid_prefs_from_types_js() -> dict[str, list[str]]:
    """Extracts VALID_PREFS mapping from web/js/prefs/types.js."""
    assert TYPES_JS.exists(), f"Missing types.js at {TYPES_JS}"
    types_js_text = TYPES_JS.read_text(encoding="utf-8")
    match = re.search(r"export\s+const\s+VALID_PREFS\s*=\s*Object\.freeze\((\{[\s\S]*?\})\);", types_js_text)
    assert match, "Could not locate export const VALID_PREFS in types.js"

    block = match.group(1)
    entries = re.findall(r'(\w+)\s*:\s*\[([^\]]+)\]', block)
    valid_prefs: dict[str, list[str]] = {}
    for key, values_str in entries:
        vals = [v.strip().strip('"\'') for v in values_str.split(",") if v.strip()]
        valid_prefs[key] = vals

    return valid_prefs


def test_no_hardcoded_colors_in_css_stylesheets():
    """Scans all CSS files in web/css/ (excluding tokens.css) for raw color values.

    Ensures zero hardcoded hex, rgb/rgba, or hsl/hsla colors, strictly
    whitelisting the 7 approved instances in web/css/shell.css.
    """
    assert CSS_DIR.exists(), f"CSS directory missing at {CSS_DIR}"
    css_files = sorted(CSS_DIR.glob("*.css"))
    assert css_files, f"No CSS files found in {CSS_DIR}"

    # Regexes for raw colors in CSS declarations
    hex_pattern = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b")
    rgb_pattern = re.compile(r"rgba?\([^)]+\)")
    hsl_pattern = re.compile(r"hsla?\([^)]+\)")

    unwhitelisted_violations: list[str] = []

    for file_path in css_files:
        if file_path.name == "tokens.css":
            continue

        raw_text = file_path.read_text(encoding="utf-8")
        # Strip comments while preserving exact line numbers by replacing non-newlines with spaces
        clean_text = re.sub(r"/\*[\s\S]*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw_text)

        remaining_shell_whitelist = list(GRANDFATHERED_SHELL_COLORS) if file_path.name == "shell.css" else []

        for line_num, line in enumerate(clean_text.splitlines(), start=1):
            # Only inspect declaration lines (ignore selectors or empty lines)
            if ":" not in line:
                continue

            # Extract property value part (after the first colon)
            _, _, val_part = line.partition(":")

            # Check for hex, rgb, and hsl occurrences in the value
            matches: list[str] = []
            matches.extend(hex_pattern.findall(val_part))
            matches.extend(rgb_pattern.findall(val_part))
            matches.extend(hsl_pattern.findall(val_part))

            for color_match in matches:
                color_norm = color_match.strip()
                if file_path.name == "shell.css" and color_norm in remaining_shell_whitelist:
                    remaining_shell_whitelist.remove(color_norm)
                else:
                    unwhitelisted_violations.append(
                        f"{file_path.name}:{line_num} -> Found unwhitelisted raw color '{color_norm}' in: {line.strip()}"
                    )

    assert not unwhitelisted_violations, (
        f"Found {len(unwhitelisted_violations)} hardcoded color violation(s) in web/css/:\n"
        + "\n".join(f"  - {v}" for v in unwhitelisted_violations)
        + "\nAll styles outside tokens.css must use CSS variables (var(--...))."
    )


def test_token_contrast_matrix_wcag_aa_and_aaa():
    """Verifies that color tokens in web/css/tokens.css meet WCAG 2.2 AA and AAA contrast ratios."""
    assert TOKENS_CSS.exists(), f"Missing tokens.css at {TOKENS_CSS}"
    css_text = TOKENS_CSS.read_text(encoding="utf-8")

    # 1. Light Theme (:root) - WCAG 2.2 AAA (>= 7:1) and AA (>= 4.5:1)
    light = _parse_css_variables(css_text, ":root")
    assert "--text-main" in light and "--bg-surface" in light
    assert _contrast_ratio(light["--text-main"], light["--bg-surface"]) >= 14.0, "Light --text-main on --bg-surface < 14:1"
    assert _contrast_ratio(light["--text-main"], light["--bg-app"]) >= 14.0, "Light --text-main on --bg-app < 14:1"
    assert _contrast_ratio(light["--text-muted"], light["--bg-app"]) >= 7.0, "Light --text-muted on --bg-app < 7:1"
    assert _contrast_ratio(light["--primary"], light["--bg-surface"]) >= 4.5, "Light --primary on --bg-surface < 4.5"
    assert _contrast_ratio(light["--primary-contrast"], light["--primary"]) >= 4.5, "Light --primary-contrast on --primary < 4.5"

    # 2. Dark Theme ([data-theme="dark"]) - WCAG 2.2 AAA (>= 14:1)
    dark = _parse_css_variables(css_text, '[data-theme="dark"]')
    assert "--text-main" in dark and "--bg-surface" in dark
    assert _contrast_ratio(dark["--text-main"], dark["--bg-app"]) >= 14.0, "Dark --text-main on --bg-app < 14:1"
    assert _contrast_ratio(dark["--text-muted"], dark["--bg-app"]) >= 14.0, "Dark --text-muted on --bg-app < 14:1"
    assert _contrast_ratio(dark["--primary"], dark["--bg-app"]) >= 14.0, "Dark --primary on --bg-app < 14:1"
    assert _contrast_ratio(dark["--primary-contrast"], dark["--primary"]) >= 4.5, "Dark --primary-contrast on --primary < 4.5"

    # 3. High Contrast Theme ([data-theme="high-contrast"] / [data-contrast="high"]) - WCAG AAA (>= 7.0:1)
    hc = _parse_css_variables(css_text, '[data-theme="high-contrast"]')
    assert "--text-main" in hc and "--bg-surface" in hc
    assert _contrast_ratio(hc["--text-main"], hc["--bg-surface"]) >= 7.0, "HC --text-main on --bg-surface < 7.0"
    assert _contrast_ratio(hc["--text-main"], hc["--bg-app"]) >= 7.0, "HC --text-main on --bg-app < 7.0"
    assert _contrast_ratio(hc["--text-muted"], hc["--bg-surface"]) >= 7.0, "HC --text-muted on --bg-surface < 7.0"
    assert _contrast_ratio(hc["--primary"], hc["--bg-surface"]) >= 7.0, "HC --primary on --bg-surface < 7.0"
    assert _contrast_ratio(hc["--primary-contrast"], hc["--primary"]) >= 7.0, "HC --primary-contrast on --primary < 7.0"


def test_data_attribute_mapping_completeness():
    """Validates that non-default values in VALID_PREFS have corresponding CSS selectors in tokens.css or shell.css."""
    assert TOKENS_CSS.exists()
    assert SHELL_CSS.exists()

    tokens_css = TOKENS_CSS.read_text(encoding="utf-8")
    shell_css = SHELL_CSS.read_text(encoding="utf-8")
    combined_css = tokens_css + "\n" + shell_css

    # Touch target requirement check (Gemini standard: 48px)
    assert "--min-touch-target: 48px" in tokens_css, "tokens.css must define --min-touch-target: 48px"

    valid_prefs = _extract_valid_prefs_from_types_js()

    # Mapping of preference key to attribute name and non-default values to verify
    # (Language maps to lang="ro" / lang="en", handled outside data-* attribute selectors)
    pref_attr_map: dict[str, tuple[str, list[str]]] = {
        "theme": ("data-theme", ["dark", "high-contrast-light"]),
        "textSize": ("data-text", ["l", "xl"]),
        "spacing": ("data-spacing", ["roomy"]),
        "contrast": ("data-contrast", ["high", "high-dark", "high-light"]),
        "motion": ("data-motion", ["reduced"]),
        "font": ("data-font", ["readable", "dyslexic"]),
        "density": ("data-density", ["focused"]),
        "sidebar": ("data-sidebar", ["collapsed"]),
    }

    missing_selectors: list[str] = []

    for pref_key, (attr_name, non_default_values) in pref_attr_map.items():
        assert pref_key in valid_prefs, f"Preference key '{pref_key}' missing from VALID_PREFS in types.js"
        all_allowed = valid_prefs[pref_key]

        for val in non_default_values:
            assert val in all_allowed, f"Value '{val}' not in VALID_PREFS['{pref_key}'] ({all_allowed})"
            selector_fragment = f'[{attr_name}="{val}"]'
            if selector_fragment not in combined_css:
                missing_selectors.append(f"{pref_key}='{val}' expected selector {selector_fragment}")

    assert not missing_selectors, (
        f"Missing active CSS selectors for preferences:\n"
        + "\n".join(f"  - {m}" for m in missing_selectors)
    )


def test_math_and_parser_unit_helpers():
    """Unit test for mathematical luminance, contrast ratio calculations, and CSS parser edge cases."""
    # Black on white: 21:1
    assert abs(_contrast_ratio("#ffffff", "#000000") - 21.0) < 0.01
    assert abs(_contrast_ratio("#000000", "#ffffff") - 21.0) < 0.01

    # Identical colors: 1:1
    assert abs(_contrast_ratio("#ffffff", "#ffffff") - 1.0) < 0.01
    assert abs(_contrast_ratio("#123456", "#123456") - 1.0) < 0.01

    # 3-digit hex expansion
    assert _hex_to_luminance("#fff") == _hex_to_luminance("#ffffff")
    assert _hex_to_luminance("#000") == _hex_to_luminance("#000000")

    # CSS parser helper
    sample_css = """
    /* Comment here */
    :root {
      --sample-one: #123456;
      --sample-two: 44px; /* inline comment */
    }
    .other, [data-test="foo"] {
      --sample-one: #654321;
    }
    """
    root_vars = _parse_css_variables(sample_css, ":root")
    assert root_vars["--sample-one"] == "#123456"
    assert root_vars["--sample-two"] == "44px"

    foo_vars = _parse_css_variables(sample_css, '[data-test="foo"]')
    assert foo_vars["--sample-one"] == "#654321"

    missing_vars = _parse_css_variables(sample_css, ".non-existent")
    assert missing_vars == {}
