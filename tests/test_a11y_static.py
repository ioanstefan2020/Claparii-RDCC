"""Static accessibility gate for every HTML file under web/ (owner: p2).
Catches the cheap, common failures on every check.sh run. It does NOT replace a keyboard-only
walkthrough and a screen-reader pass (see .agents/skills/a11y-by-design)."""
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HTML_FILES = sorted((ROOT / "web").rglob("*.html")) if (ROOT / "web").exists() else []

FORM_TAGS = {"input", "select", "textarea"}
SKIP_INPUT_TYPES = {"hidden", "submit", "button", "reset", "image"}


class _Audit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.html_lang = None
        self.title_text = ""
        self.h1_count = 0
        self.has_main = False
        self.skip_link = False
        self.viewport = None
        self.problems = []
        self._in_title = False
        self._label_depth = 0
        self._label_for = set()
        self._form_controls = []  # (tag, id, has_aria_name, inside_label)
        self._button_stack = []
        self._anchor_stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main" or a.get("role") == "main":
            self.has_main = True
        elif tag == "meta" and a.get("name") == "viewport":
            self.viewport = a.get("content", "")
        elif tag == "label":
            self._label_depth += 1
            if a.get("for"):
                self._label_for.add(a["for"])
        elif tag == "img" and "alt" not in a:
            self.problems.append("<img> without alt attribute")
        elif tag in FORM_TAGS:
            if not (tag == "input" and a.get("type", "text") in SKIP_INPUT_TYPES):
                named = bool(a.get("aria-label") or a.get("aria-labelledby"))
                self._form_controls.append((tag, a.get("id"), named, self._label_depth > 0))
        elif tag == "button":
            self._button_stack.append({"text": "", "named": bool(a.get("aria-label") or a.get("aria-labelledby") or a.get("title"))})
        elif tag == "a":
            href = a.get("href", "")
            self._anchor_stack.append({"href": href, "text": ""})
        if a.get("tabindex") and a["tabindex"].lstrip("-").isdigit() and int(a["tabindex"]) > 0:
            self.problems.append(f"positive tabindex on <{tag}> (breaks keyboard order)")
        if "onclick" in a and tag in {"div", "span", "p", "li"}:
            self.problems.append(f"onclick on non-interactive <{tag}> (use <button>)")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "label":
            self._label_depth = max(0, self._label_depth - 1)
        elif tag == "button" and self._button_stack:
            b = self._button_stack.pop()
            if not (b["text"].strip() or b["named"]):
                self.problems.append("<button> without accessible name")
        elif tag == "a" and self._anchor_stack:
            link = self._anchor_stack.pop()
            if link["href"].startswith("#") and len(link["href"]) > 1 and re.search(r"conținut|continut|skip|main", link["text"], re.I):
                self.skip_link = True

    def handle_data(self, data):
        if self._in_title:
            self.title_text += data
        if self._button_stack:
            self._button_stack[-1]["text"] += data
        if self._anchor_stack:
            self._anchor_stack[-1]["text"] += data


def audit_html(text: str, is_fragment: bool = False) -> list:
    p = _Audit()
    p.feed(text)
    problems = list(p.problems)
    if not is_fragment:
        if not p.html_lang:
            problems.append('<html> missing lang attribute (use lang="ro")')
        if not p.title_text.strip():
            problems.append("missing or empty <title>")
        if p.h1_count != 1:
            problems.append(f"expected exactly one <h1>, found {p.h1_count}")
        if not p.has_main:
            problems.append("missing <main> landmark")
        if not p.skip_link:
            problems.append('missing skip link (e.g. <a href="#main">Sari la conținut</a>)')
        if p.viewport is None:
            problems.append("missing viewport meta")
    if p.viewport and re.search(r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b", p.viewport):
        problems.append("viewport disables zoom")
    for tag, cid, named, inside in p._form_controls:
        if not (named or inside or (cid and cid in p._label_for)):
            problems.append(f"<{tag}{' id=' + cid if cid else ''}> has no label (label[for], wrapping label, or aria-label)")
    return problems


GOOD = """<!doctype html><html lang="ro"><head><meta charset="utf-8"><title>Test</title>
<meta name="viewport" content="width=device-width, initial-scale=1"></head><body>
<a href="#main">Sari la conținut</a><header><nav></nav></header>
<main id="main"><h1>Titlu</h1><label for="t">Text</label><textarea id="t"></textarea>
<button type="submit">Trimite</button><img src="x.png" alt="Logo"></main></body></html>"""

BAD = """<html><head><meta name="viewport" content="width=device-width, user-scalable=no"></head><body>
<div onclick="go()">Click</div><img src="x.png"><input id="q"><button></button>
<h1>A</h1><h1>B</h1></body></html>"""


def test_audit_accepts_good_page():
    assert audit_html(GOOD) == []


def test_audit_catches_bad_page():
    problems = " | ".join(audit_html(BAD))
    for expected in ["lang", "title", "h1", "main", "skip link", "alt", "no label", "accessible name", "onclick", "zoom"]:
        assert expected in problems, f"checker missed: {expected}\n{problems}"


@pytest.mark.parametrize("path", HTML_FILES, ids=[str(p.relative_to(ROOT)) for p in HTML_FILES])
def test_page_is_statically_accessible(path):
    problems = audit_html(path.read_text(encoding="utf-8"))
    assert not problems, f"{path.relative_to(ROOT)}:\n  - " + "\n  - ".join(problems)


def _hex_to_luminance(hex_str: str) -> float:
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0

    def adjust(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def _contrast_ratio(hex1: str, hex2: str) -> float:
    l1 = _hex_to_luminance(hex1)
    l2 = _hex_to_luminance(hex2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def test_wcag_contrast_tokens_in_css():
    """Verify that design tokens in web/shared/a11y.css meet WCAG 2.2 AA (>= 4.5:1) and AAA (>= 7:1 for HC)."""
    css_path = ROOT / "web" / "shared" / "a11y.css"
    assert css_path.exists(), "a11y.css missing"
    css_text = css_path.read_text(encoding="utf-8")

    # Verify light theme tokens (WCAG AAA >= 7:1)
    assert _contrast_ratio("#1e2022", "#f9f9f7") >= 7.0  # text-main on canvas (15.4:1)
    assert _contrast_ratio("#4a4f55", "#f9f9f7") >= 7.0  # text-muted on canvas (7.8:1)
    assert _contrast_ratio("#1d4ed8", "#ffffff") >= 4.5  # primary on white (6.7:1)

    # Verify high contrast tokens (>= 7:1)
    assert _contrast_ratio("#ffffff", "#000000") >= 7.0  # 21:1
    assert _contrast_ratio("#ffff00", "#000000") >= 7.0  # 19.5:1


def test_wcag_touch_targets_and_reduced_motion():
    """Verify that minimum touch targets (>= 48px) and reduced-motion query exist in a11y.css."""
    css_text = (ROOT / "web" / "shared" / "a11y.css").read_text(encoding="utf-8")
    assert "--min-touch-target: 48px" in css_text
    assert "@media (prefers-reduced-motion: reduce)" in css_text
    assert "animation-duration: 0.001ms !important" in css_text


def test_no_sparkles_in_html_files():
    """Verify that no AI hype sparkle emojis (✨) appear anywhere across served HTML files."""
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        assert "✨" not in content, f"AI anti-pattern sparkle emoji (✨) found in {html_file.name}"


def test_wcag_no_external_cdn_dependencies():
    """Verify that all web HTML files use zero external CDN links or scripts (offline-safe)."""
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        assert not re.search(r'<(?:script|link)[^>]*(?:href|src)=["\']https?://', content, re.I), (
            f"External CDN found in {html_file.name} (must be self-contained/offline-safe)"
        )


def test_employee_navigation_consistency():
    """Verify that all employee web pages contain full, accessible navigation links."""
    employee_pages = [
        ROOT / "web" / "index.html",
        ROOT / "web" / "employee" / "profile.html",
        ROOT / "web" / "employee" / "clarify.html",
        ROOT / "web" / "employee" / "plan.html",
        ROOT / "web" / "employee" / "meeting.html",
        ROOT / "web" / "employee" / "adjustments.html"
    ]
    for page in employee_pages:
        assert page.exists(), f"{page.name} missing"
        html = page.read_text(encoding="utf-8")
        assert '<nav aria-label="Navigare principală">' in html, f"Nav missing in {page.name}"
        assert 'href="/employee/clarify.html"' in html, f"Clarify link missing in {page.name}"
        assert 'href="/employee/plan.html"' in html, f"Plan link missing in {page.name}"
        assert 'href="/employee/meeting.html"' in html, f"Meeting link missing in {page.name}"
        assert 'href="/employee/adjustments.html"' in html, f"Adjustments link missing in {page.name}"
        assert 'href="/employee/profile.html"' in html, f"Profile link missing in {page.name}"


def test_live_region_presence_on_all_pages():
    """Verify that all HTML pages contain an aria-live='polite' region for screen reader announcements."""
    for html_file in HTML_FILES:
        content = html_file.read_text(encoding="utf-8")
        assert 'aria-live="polite"' in content or 'role="status"' in content, (
            f"Missing aria-live announcement region in {html_file.name}"
        )
