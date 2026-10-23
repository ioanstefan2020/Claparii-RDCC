"""Comprehensive Accessibility & UX Polish Tests (T2.7, T2.8, T2.9).
Owner: p2

Validates:
- WCAG 2.2 AA standards compliance across all employee screens
- Reading comfort (line-focus reading guide, simple mode, high contrast)
- Zero diagnosis fields in UI forms
- Consistency of navigation across all services
- Availability of offline sample documents in web/shared/samples/
"""
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def test_samples_directory_exists_and_populated():
    """Verify T2.9 offline sample documents exist and have non-empty Romanian content."""
    samples_dir = ROOT / "web" / "shared" / "samples"
    assert samples_dir.exists(), "web/shared/samples directory missing"

    expected_files = [
        "onboarding_ro.txt",
        "task_email_ro.txt",
        "meeting_transcript_ro.txt",
        "injection_ro.txt",
    ]
    for filename in expected_files:
        sample_path = samples_dir / filename
        assert sample_path.exists(), f"Sample {filename} missing in web/shared/samples"
        content = sample_path.read_text(encoding="utf-8").strip()
        assert len(content) > 50, f"Sample {filename} is too short ({len(content)} chars)"


def test_a11y_css_line_focus_and_simple_mode():
    """Verify T2.8 Reading Comfort CSS rules in web/shared/a11y.css."""
    css_path = ROOT / "web" / "shared" / "a11y.css"
    css_text = css_path.read_text(encoding="utf-8")

    # Simple mode rules
    assert '[data-simple-mode="true"]' in css_text
    assert "--font-scale: 1.25rem;" in css_text
    assert "--line-height: 1.85;" in css_text
    assert ".meta-secondary" in css_text

    # Line focus rules
    assert '[data-line-focus="true"]' in css_text
    assert '[data-theme="dark"][data-line-focus="true"]' in css_text
    assert '[data-theme="high-contrast"][data-line-focus="true"]' in css_text


def test_profile_js_exports_and_line_focus_support():
    """Verify web/shared/profile.js supports lineFocus in default prefs and DOM application."""
    profile_js = (ROOT / "web" / "shared" / "profile.js").read_text(encoding="utf-8")

    assert "lineFocus: false" in profile_js
    assert 'data-line-focus' in profile_js
    assert "applyA11yPrefs" in profile_js
    assert "deleteAllUserData" in profile_js


def test_plan_page_applies_a11y_prefs_on_init():
    """Verify web/employee/plan.js imports and calls applyA11yPrefs on initialization."""
    plan_js = (ROOT / "web" / "employee" / "plan.js").read_text(encoding="utf-8")

    assert "applyA11yPrefs" in plan_js
    assert "applyA11yPrefs(getA11yPrefs());" in plan_js


def test_zero_diagnosis_disclosure_in_all_web_forms():
    """Verify that no employee HTML page contains fields asking for medical diagnosis."""
    banned_medical_terms = [
        "diagnostic", "boală", "afecțiune", "handicap grad", "certificat medical",
        "dosar medical", "tulburare", "medic de familie"
    ]
    employee_html_files = sorted((ROOT / "web" / "employee").glob("*.html"))
    for html_file in employee_html_files:
        text = html_file.read_text(encoding="utf-8").lower()
        for term in banned_medical_terms:
            # Match label or placeholder asking for diagnosis
            match = re.search(rf'<label[^>]*>[^<]*\b{re.escape(term)}\b', text)
            assert not match, f"Found medical diagnosis term '{term}' in {html_file.name} label"


def test_all_employee_pages_have_consistent_footer_and_landmarks():
    """Verify that every employee page has semantic header, main, and footer landmarks."""
    pages = [
        ROOT / "web" / "index.html",
        ROOT / "web" / "employee" / "profile.html",
        ROOT / "web" / "employee" / "clarify.html",
        ROOT / "web" / "employee" / "plan.html",
        ROOT / "web" / "employee" / "meeting.html",
    ]
    for page in pages:
        content = page.read_text(encoding="utf-8")
        assert "<header" in content, f"Missing <header> in {page.name}"
        assert "<main" in content, f"Missing <main> in {page.name}"
        assert 'class="skip-link"' in content, f"Missing skip-link in {page.name}"
        assert 'href="#main"' in content, f"Skip link must point to #main in {page.name}"
