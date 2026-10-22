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


