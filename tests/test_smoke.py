"""End-to-end smoke test suite for the complete API stack and web pages.

Validates the full application stack using FastAPI TestClient:
- Health check (/api/health)
- Document simplification (/api/simplify)
- Action plan extraction (/api/plan/extract)
- Reasonable adjustments catalog & draft (/api/adjustments/catalog, /api/adjustments/draft)
- Employer document cognitive accessibility analysis (/api/employer/analyze)
- Negative error envelope handling (400, 422, 404)
- Web page serving for all static routes (/, /index.html, /employee/profile.html, /employer/index.html)
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "data" / "samples"
ONBOARDING_SAMPLE = SAMPLES_DIR / "onboarding_ro.txt"
TASK_EMAIL_SAMPLE = SAMPLES_DIR / "task_email_ro.txt"
WEB_DIR = ROOT / "web"


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Module-scoped TestClient running against the FastAPI app."""
    return TestClient(app)


@pytest.fixture(scope="module")
def onboarding_sample_text() -> str:
    """Reads the Romanian onboarding sample document."""
    assert ONBOARDING_SAMPLE.exists(), f"Sample missing: {ONBOARDING_SAMPLE}"
    return ONBOARDING_SAMPLE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def task_email_sample_text() -> str:
    """Reads the Romanian task email sample document."""
    assert TASK_EMAIL_SAMPLE.exists(), f"Sample missing: {TASK_EMAIL_SAMPLE}"
    return TASK_EMAIL_SAMPLE.read_text(encoding="utf-8")


# ==============================================================================
# Health Check Endpoint
# ==============================================================================


def test_smoke_health(client: TestClient) -> None:
    """GET /api/health returns ok: true and the active LLM provider."""
    res = client.get("/api/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    body = res.json()
    assert body.get("ok") is True
    assert "provider" in body
    assert isinstance(body["provider"], str)


# ==============================================================================
# Simplify Endpoint (CONTRACTS §3.1)
# ==============================================================================


def test_smoke_simplify(client: TestClient, onboarding_sample_text: str) -> None:
    """POST /api/simplify produces summary, steps, key_terms, and meta envelope."""
    payload = {
        "text": onboarding_sample_text,
        "profile": {
            "reading_level": "simple",
            "format": "steps",
            "needs_notes": "Instrucțiuni pas cu pas",
        },
    }
    res = client.post("/api/simplify", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["ok"] is True
    data = body["data"]
    assert "summary" in data and isinstance(data["summary"], str)
    assert len(data["summary"].strip()) > 0
    assert "steps" in data and isinstance(data["steps"], list)
    assert len(data["steps"]) > 0
    for step in data["steps"]:
        assert "n" in step
        assert "text" in step
        assert "source_quote" in step

    meta = body["meta"]
    assert meta["provider"] == "mock"
    assert "ai_notice_ro" in meta
    assert "Generat de AI" in meta["ai_notice_ro"]


# ==============================================================================
# Plan Extraction Endpoint (CONTRACTS §3.2)
# ==============================================================================


def test_smoke_plan_extract(client: TestClient, task_email_sample_text: str) -> None:
    """POST /api/plan/extract extracts actionable tasks with priorities and quotes."""
    payload = {
        "text": task_email_sample_text,
        "today_iso": "2026-10-22",
        "profile": {"reading_level": "simple", "format": "steps"},
    }
    res = client.post("/api/plan/extract", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["ok"] is True
    data = body["data"]
    assert "tasks" in data and isinstance(data["tasks"], list)
    assert len(data["tasks"]) > 0
    for task in data["tasks"]:
        assert "id" in task
        assert "title" in task
        assert "priority" in task
        assert task["priority"] in {"high", "normal", "low"}
        assert "source_quote" in task

    meta = body["meta"]
    assert meta["provider"] == "mock"
    assert "ai_notice_ro" in meta


# ==============================================================================
# Meeting Summarize Endpoint (CONTRACTS §3.3)
# ==============================================================================


def test_smoke_meeting_summarize(client: TestClient) -> None:
    """POST /api/meeting/summarize extracts summary, decisions, action items without emotion."""
    meeting_sample = SAMPLES_DIR / "meeting_transcript_ro.txt"
    assert meeting_sample.exists()
    transcript_text = meeting_sample.read_text(encoding="utf-8")

    payload = {
        "transcript": transcript_text,
        "today_iso": "2026-10-22",
        "profile": {"reading_level": "simple", "format": "steps"},
    }
    res = client.post("/api/meeting/summarize", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["ok"] is True
    data = body["data"]
    assert "summary" in data and len(data["summary"].strip()) > 0
    assert "decisions" in data and isinstance(data["decisions"], list)
    assert "action_items" in data and isinstance(data["action_items"], list)
    assert len(data["action_items"]) > 0
    for act in data["action_items"]:
        assert "task" in act
        assert "source_quote" in act


# ==============================================================================
# Adjustments Catalog & Draft Endpoints (CONTRACTS §3.4 & §3.5)
# ==============================================================================


def test_smoke_adjustments_catalog(client: TestClient) -> None:
    """GET /api/adjustments/catalog returns >= 12 workplace adjustments and disclaimer."""
    res = client.get("/api/adjustments/catalog")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["ok"] is True
    data = body["data"]
    assert "disclaimer_ro" in data
    assert "nu reprezintă consultanță juridică" in data["disclaimer_ro"].lower()
    assert "items" in data and isinstance(data["items"], list)
    assert len(data["items"]) >= 12

    # Verify presence of core catalog keys
    ids = {item["id"] for item in data["items"]}
    assert "written_instructions" in ids
    assert "extra_time" in ids


def test_smoke_adjustments_draft(client: TestClient) -> None:
    """POST /api/adjustments/draft generates a personalized formal request letter."""
    payload = {
        "need_ids": ["written_instructions", "extra_time"],
        "context": "onboarding",
        "employer_name": "Companie Exemplu SRL",
        "tone": "friendly",
    }
    res = client.post("/api/adjustments/draft", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["ok"] is True
    data = body["data"]
    assert "subject" in data and len(data["subject"].strip()) > 0
    assert "body_ro" in data and len(data["body_ro"].strip()) > 0
    assert "checklist" in data and isinstance(data["checklist"], list)
    assert len(data["checklist"]) == 2

    meta = body["meta"]
    assert meta["provider"] == "mock"
    assert "ai_notice_ro" in meta


# ==============================================================================
# Employer Document Cognitive Accessibility Analysis (CONTRACTS §3.6)
# ==============================================================================


def test_smoke_employer_analyze(client: TestClient, onboarding_sample_text: str) -> None:
    """POST /api/employer/analyze computes readability score and detects clarity issues."""
    payload = {
        "text": onboarding_sample_text,
        "doc_type": "onboarding",
    }
    res = client.post("/api/employer/analyze", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["ok"] is True
    data = body["data"]

    # Readability section
    assert "readability" in data
    readability = data["readability"]
    assert isinstance(readability["score_0_100"], int)
    assert 0 <= readability["score_0_100"] <= 100
    assert isinstance(readability["sentence_count"], int)
    assert readability["sentence_count"] > 0
    assert isinstance(readability["avg_sentence_words"], (int, float))

    # Issues section
    assert "issues" in data and isinstance(data["issues"], list)
    for issue in data["issues"]:
        assert "kind" in issue
        assert "quote" in issue
        assert "fix" in issue

    # Easy-read rewrite
    assert "easy_read_ro" in data and isinstance(data["easy_read_ro"], str)
    assert len(data["easy_read_ro"].strip()) > 0

    # Adjustment checklist
    assert "adjustment_checklist" in data and isinstance(data["adjustment_checklist"], list)

    # Meta envelope
    meta = body["meta"]
    assert meta["provider"] == "mock"
    assert "ai_notice_ro" in meta


def test_smoke_employer_analyze_empty_input(client: TestClient) -> None:
    """POST /api/employer/analyze returns HTTP 400 empty_input envelope on blank text."""
    payload = {"text": "   \n\t  ", "doc_type": "onboarding"}
    res = client.post("/api/employer/analyze", json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert "error" in body
    assert body["error"]["code"] == "empty_input"
    assert "message_ro" in body["error"]
    assert len(body["error"]["message_ro"]) > 0


# ==============================================================================
# Error Envelopes & Input Validation
# ==============================================================================


def test_smoke_validation_error_envelope(client: TestClient) -> None:
    """Invalid payload schemas return HTTP 422 with bad_request error envelope."""
    # Missing required 'text' field
    res = client.post("/api/simplify", json={})
    assert res.status_code == 422
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "bad_request"
    assert "message_ro" in body["error"]


def test_smoke_not_found_envelope(client: TestClient) -> None:
    """Accessing non-existent API endpoints returns HTTP 404 with error envelope."""
    res = client.get("/api/non_existent_endpoint_xyz")
    assert res.status_code == 404
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "not_found"
    assert "message_ro" in body["error"]


# ==============================================================================
# Web Route & Static Page Serving
# ==============================================================================


@pytest.mark.parametrize(
    "route",
    [
        "/",
        "/index.html",
        "/welcome.html",
        "/settings.html",
        "/library.html",
        "/audio.html",
        "/employee/profile.html",
        "/employee/clarify.html",
        "/employee/plan.html",
        "/employee/meeting.html",
        "/employee/adjustments.html",
        "/employer/index.html",
    ],
)
def test_smoke_static_web_pages(client: TestClient, route: str) -> None:
    """Verifies that core HTML pages are served with HTTP 200 and HTML markup."""
    res = client.get(route)
    assert res.status_code == 200, f"Failed route {route}: {res.status_code}"
    assert "text/html" in res.headers.get("content-type", "")
    assert "<html" in res.text.lower()
    assert "<main" in res.text.lower()


def test_smoke_all_html_files_served(client: TestClient) -> None:
    """Ensures every single HTML file under web/ is mounted and accessible."""
    if not WEB_DIR.exists():
        pytest.skip("web directory not found")

    html_files = sorted(WEB_DIR.rglob("*.html"))
    assert len(html_files) > 0, "No HTML files found in web/"

    for path in html_files:
        rel_path = path.relative_to(WEB_DIR).as_posix()
        url = f"/{rel_path}"
        res = client.get(url)
        assert res.status_code == 200, f"Failed to serve {url}: {res.status_code}"
        assert "<html" in res.text.lower(), f"{url} does not contain <html tag"


def test_smoke_static_assets_served(client: TestClient) -> None:
    """Essential non-HTML assets (CSS, JS, fixtures, i18n) are served with HTTP 200."""
    assets = [
        ("/shared/a11y.css", "text/css"),
        ("/css/tokens.css", "text/css"),
        ("/css/shell.css", "text/css"),
        ("/js/shell.js", "javascript"),
        ("/js/home.js", "javascript"),
        ("/js/welcome.js", "javascript"),
        ("/js/settings.js", "javascript"),
        ("/js/library.js", "javascript"),
        ("/js/library-storage.js", "javascript"),
        ("/employer/fixture.json", "application/json"),
        ("/i18n/ro.employer.json", "application/json"),
        ("/employer/employer.js", "javascript"),
    ]
    for url, mime_substr in assets:
        res = client.get(url)
        assert res.status_code == 200, f"Failed to serve asset {url}: {res.status_code}"
        assert mime_substr in res.headers.get("content-type", ""), (
            f"Expected {mime_substr} for {url}, got {res.headers.get('content-type')}"
        )


def test_smoke_welcome_page_elements(client: TestClient) -> None:
    """Verifies that /welcome.html contains all wizard & live preview elements for Task N3.3."""
    res = client.get("/welcome.html")
    assert res.status_code == 200
    html = res.text

    # Wizard card and controls
    assert 'id="wizard-card"' in html
    assert 'id="wizard-step-counter"' in html
    assert 'id="wizard-progress-bar"' in html
    assert 'id="question-prompt"' in html
    assert 'id="question-options"' in html
    assert 'id="btn-wizard-prev"' in html
    assert 'id="btn-wizard-next"' in html
    assert 'id="btn-wizard-save"' in html
    assert 'id="btn-wizard-save-now"' in html

    # Live preview container
    assert 'id="welcome-live-preview"' in html
    assert 'id="preview-badges"' in html
    assert 'id="preview-sample-card"' in html

    # Module script
    assert 'src="/js/welcome.js"' in html


def test_smoke_settings_page_elements(client: TestClient) -> None:
    """Verifies that /settings.html contains all 9 preference controls, dual resets, export/import, and live preview."""
    res = client.get("/settings.html")
    assert res.status_code == 200
    html = res.text

    # 9 preference selects
    for pref_id in [
        "pref-theme",
        "pref-contrast",
        "pref-text-size",
        "pref-spacing",
        "pref-font",
        "pref-motion",
        "pref-density",
        "pref-language",
        "pref-sidebar",
    ]:
        assert f'id="{pref_id}"' in html, f"Missing select {pref_id}"

    # Resets & Confirmation dialog
    assert 'id="btn-reset-answers"' in html
    assert 'id="btn-reset-all"' in html
    assert 'id="confirm-reset-box"' in html
    assert 'id="btn-confirm-reset"' in html
    assert 'id="btn-cancel-reset"' in html

    # Backup & Transfer (JSON)
    assert 'id="btn-export-json"' in html
    assert 'id="btn-import-json-trigger"' in html
    assert 'id="input-import-json"' in html

    # Live Preview Aside
    assert 'id="settings-live-preview"' in html
    assert 'id="preview-overrides-badge"' in html
    assert 'id="preview-sample-card"' in html

    # Module scripts
    assert 'src="/js/settings.js"' in html
    assert 'src="/js/shell.js"' in html


def test_smoke_settings_select_options_match_schema(client: TestClient) -> None:
    """Verifies that all 9 <select> inputs in /settings.html define options exactly matching VALID_PREFS."""
    res = client.get("/settings.html")
    assert res.status_code == 200
    html = res.text

    expected_options = {
        "pref-theme": ["system", "light", "dark"],
        "pref-contrast": ["normal", "high"],
        "pref-text-size": ["m", "l", "xl"],
        "pref-spacing": ["comfortable", "roomy"],
        "pref-font": ["default", "readable"],
        "pref-motion": ["full", "reduced"],
        "pref-density": ["full", "focused"],
        "pref-language": ["ro", "en"],
        "pref-sidebar": ["open", "collapsed"],
    }
    for select_id, values in expected_options.items():
        assert f'id="{select_id}"' in html, f"Missing select {select_id}"
        for val in values:
            assert f'value="{val}"' in html, f"Missing option value {val} in select {select_id}"

    # Also verify fallback, live announcement, and toast containers
    assert 'id="memory-fallback-notice"' in html
    assert 'id="status-live"' in html
    assert 'id="status-toast"' in html


def test_smoke_home_screen_interactive_elements(client: TestClient) -> None:
    """Verifies that the Home screen (/index.html) contains all interactive elements for Task N3.2."""
    res = client.get("/index.html")
    assert res.status_code == 200
    html = res.text

    # Mode tabs & prompt form
    assert 'id="home-prompt-section"' in html
    assert 'data-mode="simplify"' in html
    assert 'data-mode="plan"' in html
    assert 'data-mode="meeting"' in html
    assert 'id="home-input-text"' in html
    assert 'id="btn-home-execute"' in html

    # Sample chips
    assert 'data-sample="onboarding"' in html
    assert 'data-sample="email"' in html
    assert 'data-sample="meeting"' in html

    # Results & source viewer
    assert 'id="home-results-section"' in html
    assert 'id="home-source-viewer"' in html
    assert 'id="btn-home-copy"' in html
    assert 'id="btn-home-tts"' in html
    assert 'id="btn-home-ics"' in html

    # Module script imports
    assert 'src="/js/shell.js"' in html
    assert 'src="/js/home.js"' in html


def test_smoke_adjustments_draft_unknown_id_400(client: TestClient) -> None:
    """POST /api/adjustments/draft with an unknown id returns HTTP 400 bad_request."""
    payload = {
        "need_ids": ["invalid_unknown_need_id_12345"],
        "context": "onboarding",
    }
    res = client.post("/api/adjustments/draft", json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "bad_request"


def test_smoke_library_page_elements(client: TestClient) -> None:
    """Verifies that /library.html is served and contains all required UI elements for Task N3.5."""
    res = client.get("/library.html")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.text

    # Basic accessibility markers
    assert '<html lang="ro">' in html
    assert '<main id="main"' in html
    assert 'class="skip-link"' in html
    assert '<h1 class="page-title">Biblioteca ta de lucru</h1>' in html

    # Toolbar and search controls
    assert 'id="library-search"' in html
    assert 'id="library-filter-mode"' in html
    assert 'id="library-count-badge"' in html
    assert 'id="btn-library-clear-all"' in html
    assert 'id="confirm-clear-box"' in html
    assert 'id="btn-confirm-clear"' in html
    assert 'id="btn-cancel-clear"' in html

    # Cards list and empty state
    assert 'id="library-items-list"' in html
    assert 'id="library-empty-state"' in html

    # Detail modal dialog
    assert 'id="library-detail-modal"' in html
    assert 'id="detail-modal-title"' in html
    assert 'id="btn-close-detail"' in html
    assert 'id="btn-detail-copy"' in html
    assert 'id="btn-detail-tts"' in html
    assert 'id="btn-detail-ics"' in html
    assert 'id="btn-detail-delete"' in html
    assert 'id="detail-content-body"' in html
    assert 'id="detail-source-viewer"' in html

    # Undo toast
    assert 'id="library-undo-toast"' in html
    assert 'id="undo-toast-message"' in html
    assert 'id="btn-undo-delete"' in html

    # Screen reader live region
    assert 'id="status-live"' in html

    # Module script imports
    assert 'src="/js/shell.js"' in html
    assert 'src="/js/library.js"' in html


def test_smoke_home_save_library_button(client: TestClient) -> None:
    """Verifies that /index.html contains #btn-home-save-library in results section and library nav link."""
    res = client.get("/index.html")
    assert res.status_code == 200
    html = res.text
    assert 'id="btn-home-save-library"' in html
    assert 'href="/library.html"' in html


def test_smoke_library_filter_mode_options(client: TestClient) -> None:
    """Verifies that #library-filter-mode in /library.html defines all 4 required mode options."""
    res = client.get("/library.html")
    assert res.status_code == 200
    html = res.text
    for val in ["all", "simplify", "plan", "meeting"]:
        assert f'value="{val}"' in html, f"Missing mode option {val} in #library-filter-mode"


def test_smoke_employer_page_elements(client: TestClient) -> None:
    """Verifies that /employer/index.html is served and contains all required UI elements for Task N3.6."""
    res = client.get("/employer/index.html")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.text

    # Basic accessibility markers & shell
    assert '<html lang="ro">' in html
    assert '<main id="main"' in html
    assert 'class="skip-link"' in html
    assert '<h1 class="page-title">Audit de accesibilitate a documentelor</h1>' in html

    # Core Form elements
    assert 'id="employer-form"' in html
    assert 'id="doc-type"' in html
    assert 'id="file-upload"' in html
    assert 'id="btn-load-sample"' in html
    assert 'id="document-text"' in html
    assert 'id="char-counter"' in html
    assert 'id="btn-clear"' in html
    assert 'id="btn-analyze"' in html

    # Results Section & AI transparency
    assert 'id="results-section"' in html
    assert 'id="results-heading"' in html
    assert 'id="ai-notice-container"' in html
    assert 'id="ai-notice-text"' in html
    assert 'id="warnings-container"' in html

    # Card 1: Readability Metrics & Score circle
    assert 'id="score-circle"' in html
    assert 'id="score-value"' in html
    assert 'id="score-badge"' in html
    assert 'id="score-description"' in html
    assert 'id="metric-sentence-count"' in html
    assert 'id="metric-avg-words"' in html
    assert 'id="metric-long-count"' in html
    assert 'id="long-sentences-wrapper"' in html
    assert 'id="long-sentences-summary-count"' in html
    assert 'id="long-sentences-list"' in html

    # Card 2: Clarity & Jargon Issues
    assert 'id="issues-container"' in html
    assert 'id="issues-counter-badge"' in html

    # Card 3: Easy-to-Read Rewrite
    assert 'id="easy-read-content"' in html
    assert 'id="btn-copy-easy"' in html
    assert 'id="btn-download-easy"' in html
    assert 'id="btn-read-aloud"' in html

    # Card 4: Adjustments checklist
    assert 'id="adjustments-list"' in html

    # Live region and notification banner
    assert 'id="status-live"' in html
    assert 'id="status-banner"' in html

    # Module script imports
    assert 'src="/js/shell.js"' in html
    assert 'src="/employer/employer.js"' in html


def test_smoke_employer_doc_type_options(client: TestClient) -> None:
    """Verifies that #doc-type in /employer/index.html defines all 4 contract doc_type options."""
    res = client.get("/employer/index.html")
    assert res.status_code == 200
    html = res.text
    for doc_type in ["onboarding", "job_ad", "policy", "other"]:
        assert f'value="{doc_type}"' in html, f"Missing doc_type option {doc_type} in #doc-type"


def test_smoke_employer_fixture_contract(client: TestClient) -> None:
    """Verifies that /employer/fixture.json matches the CONTRACTS §3.6 schema."""
    res = client.get("/employer/fixture.json")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.json()
    assert body.get("ok") is True
    assert "data" in body
    data = body["data"]

    # Readability
    assert "readability" in data
    readability = data["readability"]
    assert isinstance(readability["score_0_100"], int)
    assert 0 <= readability["score_0_100"] <= 100
    assert readability["sentence_count"] > 0
    assert readability["avg_sentence_words"] > 0
    assert isinstance(readability["long_sentences"], list)
    assert len(readability["long_sentences"]) > 0

    # Issues
    assert "issues" in data and isinstance(data["issues"], list)
    valid_kinds = {"jargon", "long_sentence", "missing_deadline", "vague_instruction", "missing_structure"}
    for issue in data["issues"]:
        assert issue["kind"] in valid_kinds
        assert len(issue["quote"]) > 0
        assert len(issue["fix"]) > 0

    # Easy-read plain Romanian rewrite
    assert "easy_read_ro" in data
    assert len(data["easy_read_ro"]) > 50

    # Adjustments checklist
    assert "adjustment_checklist" in data and isinstance(data["adjustment_checklist"], list)
    assert len(data["adjustment_checklist"]) >= 3
    for adj in data["adjustment_checklist"]:
        assert "id" in adj
        assert "title" in adj

    # Meta
    assert "meta" in body
    assert body["meta"].get("provider") == "mock"
    assert "ai_notice_ro" in body["meta"]


def test_smoke_employer_headings_and_landmarks(client: TestClient) -> None:
    """Verifies semantic landmarks, accessible card labelledby references, and heading structure."""
    res = client.get("/employer/index.html")
    assert res.status_code == 200
    html = res.text

    # Semantic landmarks
    assert '<header class="app-topbar" role="banner">' in html
    assert '<main id="main" class="app-main-content">' in html
    assert '<aside id="app-sidebar"' in html
    assert '<nav aria-label="Navigare principală">' in html
    assert '<footer class="app-footer" role="contentinfo">' in html

    # Accessible aria-labelledby card relationships
    assert 'aria-labelledby="transparency-notice-heading"' in html
    assert 'id="transparency-notice-heading"' in html

    assert 'aria-labelledby="readability-heading"' in html
    assert 'id="readability-heading"' in html

    assert 'aria-labelledby="issues-heading"' in html
    assert 'id="issues-heading"' in html

    assert 'aria-labelledby="easy-read-heading"' in html
    assert 'id="easy-read-heading"' in html

    assert 'aria-labelledby="adjustments-heading"' in html
    assert 'id="adjustments-heading"' in html

    # Accessible scrollable region with label
    assert 'id="easy-read-content"' in html
    assert 'role="region"' in html
    assert 'aria-label="Conținut rescris în limbaj simplu"' in html
    assert 'tabindex="0"' in html

    # Programmatic focus receiver on results
    assert 'id="results-heading"' in html
    assert 'tabindex="-1"' in html


def test_smoke_audio_page_structure(client: TestClient) -> None:
    """Verifies that /audio.html contains the necessary Wave 2 audio transcription elements."""
    res = client.get("/audio.html")
    assert res.status_code == 200
    html = res.text

    # Landmark and core elements
    assert "<main" in html
    assert 'id="main"' in html
    assert 'id="skip-link"' in html
    assert 'id="audio-upload-form"' in html
    assert 'id="audio-file-input"' in html
    assert 'id="btn-audio-submit"' in html
    assert 'id="btn-audio-sample"' in html
    assert 'id="btn-audio-record"' in html
    assert 'id="audio-status-container"' in html
    assert 'id="audio-result-section"' in html
    assert 'id="audio-playback"' in html
    assert 'id="audio-transcript-container"' in html
    assert 'id="btn-export-srt"' in html
    assert 'id="btn-export-vtt"' in html
    assert 'id="btn-export-txt"' in html
    assert 'id="btn-audio-summarize"' in html
    assert 'id="btn-audio-bullets"' in html
    assert 'id="btn-audio-plan"' in html
    assert 'id="btn-audio-save-library"' in html






