"""Automated WCAG 2.2 Contrast Ratio Verification for Themes (Task A5).
Ref: docs/DESIGN.md §2, docs/TASKS-WAVE2.md A5
"""
import re
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
THEMES_CSS = ROOT / "web" / "a11y" / "themes.css"


def hex_to_luminance(hex_str: str) -> float:
    """Calculates WCAG relative luminance."""
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    assert len(clean) == 6, f"Invalid hex color: {hex_str}"

    r = int(clean[0:2], 16) / 255.0
    g = int(clean[2:4], 16) / 255.0
    b = int(clean[4:6], 16) / 255.0

    def adjust(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates contrast ratio (L1 + 0.05) / (L2 + 0.05)."""
    l1 = hex_to_luminance(hex1)
    l2 = hex_to_luminance(hex2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def parse_theme_variables(css_text: str) -> dict[str, dict[str, str]]:
    """Parses CSS variables per theme selector block."""
    blocks = re.findall(r"([^{]+)\{([^}]+)\}", css_text)
    themes = {}

    for selector_str, decls_str in blocks:
        theme_names = []
        if 'data-theme="soft"' in selector_str or ":root" in selector_str:
            theme_names.append("soft")
        for m in re.finditer(r'data-theme="([^"]+)"', selector_str):
            theme_names.append(m.group(1))

        var_map = {}
        for decl in decls_str.split(";"):
            decl = decl.strip()
            if decl.startswith("--"):
                parts = decl.split(":", 1)
                if len(parts) == 2:
                    k, v = parts[0].strip(), parts[1].strip()
                    if v.startswith("#"):
                        var_map[k] = v

        for t in theme_names:
            if t not in themes:
                themes[t] = {}
            themes[t].update(var_map)

    return themes


@pytest.fixture(scope="module")
def themes():
    assert THEMES_CSS.exists(), f"Missing {THEMES_CSS}"
    text = THEMES_CSS.read_text(encoding="utf-8")
    return parse_theme_variables(text)


def test_theme_soft_contrast(themes):
    t = themes["soft"]
    bg = t["--bg-app"]
    assert contrast_ratio(t["--text-main"], bg) >= 7.0  # AAA requirement
    assert contrast_ratio(t["--text-muted"], bg) >= 7.0  # AAA requirement
    assert contrast_ratio(t["--primary"], bg) >= 7.0  # AAA text requirement
    assert contrast_ratio(t["--primary-contrast"], t["--primary"]) >= 7.0
    assert contrast_ratio(t["--border-color"], bg) >= 4.5  # Controls requirement
    assert contrast_ratio(t["--focus-ring"], bg) >= 3.0  # Focus ring requirement


def test_theme_amber_contrast(themes):
    t = themes["amber"]
    bg = t["--bg-app"]
    assert contrast_ratio(t["--text-main"], bg) >= 7.0
    assert contrast_ratio(t["--text-muted"], bg) >= 7.0
    assert contrast_ratio(t["--primary"], bg) >= 7.0
    assert contrast_ratio(t["--border-color"], bg) >= 4.5
    assert contrast_ratio(t["--focus-ring"], bg) >= 3.0


def test_theme_sapphire_contrast(themes):
    t = themes["sapphire"]
    bg = t["--bg-app"]
    assert contrast_ratio(t["--text-main"], bg) >= 7.0
    assert contrast_ratio(t["--text-muted"], bg) >= 7.0
    assert contrast_ratio(t["--primary"], bg) >= 7.0
    assert contrast_ratio(t["--border-color"], bg) >= 4.5
    assert contrast_ratio(t["--focus-ring"], bg) >= 3.0


def test_theme_hc_dark_contrast(themes):
    t = themes["hc-dark"]
    bg = t["--bg-app"]
    assert contrast_ratio(t["--text-main"], bg) >= 7.0
    assert contrast_ratio(t["--text-muted"], bg) >= 7.0
    assert contrast_ratio(t["--primary"], bg) >= 7.0


def test_theme_hc_light_contrast(themes):
    t = themes["hc-light"]
    bg = t["--bg-app"]
    assert contrast_ratio(t["--text-main"], bg) >= 7.0
    assert contrast_ratio(t["--text-muted"], bg) >= 7.0
    assert contrast_ratio(t["--primary"], bg) >= 7.0


def test_theme_night_contrast(themes):
    t = themes["night"]
    bg = t["--bg-app"]
    assert contrast_ratio(t["--text-main"], bg) >= 7.0
    assert contrast_ratio(t["--text-muted"], bg) >= 7.0
    assert contrast_ratio(t["--primary"], bg) >= 7.0
    assert contrast_ratio(t["--focus-ring"], bg) >= 3.0
