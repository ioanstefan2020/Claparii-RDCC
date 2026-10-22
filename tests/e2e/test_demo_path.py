"""End-to-End Demo Path & Accessibility Audit Test Suite (owner: p2).

Validates the full 6-step PrimaZi demonstration flow against ASGI server and preferences engine:
- Subprocess Node.js bridge to tests/e2e/test_prefs_persistence.mjs
- Step 1: Welcome & Onboarding Comfort Setup (/welcome.html)
- Step 2: Employee Clarify / Onboarding (POST /api/simplify)
- Step 3: Employee Planner with ambiguous deadline protection (POST /api/plan/extract)
- Step 4: Meeting Helper with zero emotion inference (POST /api/meeting/summarize)
- Step 5: Workplace Adjustments catalog & tailored draft (/api/adjustments/*)
- Step 6: Employer Document Cognitive Review (POST /api/employer/analyze)
- Accessibility & semantic landmark gate across all 9 served HTML routes (8 distinct pages).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app

ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = ROOT / "data" / "samples"
ONBOARDING_SAMPLE = SAMPLES_DIR / "onboarding_ro.txt"
TASK_EMAIL_SAMPLE = SAMPLES_DIR / "task_email_ro.txt"
MEETING_SAMPLE = SAMPLES_DIR / "meeting_transcript_ro.txt"


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Module-scoped FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture(scope="module")
def onboarding_text() -> str:
    """Reads the Romanian onboarding sample text."""
    assert ONBOARDING_SAMPLE.exists(), f"Sample missing: {ONBOARDING_SAMPLE}"
    return ONBOARDING_SAMPLE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def task_email_text() -> str:
    """Reads the Romanian task email sample text."""
    assert TASK_EMAIL_SAMPLE.exists(), f"Sample missing: {TASK_EMAIL_SAMPLE}"
    return TASK_EMAIL_SAMPLE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def meeting_text() -> str:
    """Reads the Romanian meeting transcript sample text."""
    assert MEETING_SAMPLE.exists(), f"Sample missing: {MEETING_SAMPLE}"
    return MEETING_SAMPLE.read_text(encoding="utf-8")


# ==============================================================================
# Test 1: Preference Persistence Node.js Lifecycle Bridge
# ==============================================================================


def test_e2e_node_prefs_persistence_lifecycle() -> None:
    """Bridges to tests/e2e/test_prefs_persistence.mjs via Node.js test runner."""
    script_path = ROOT / "tests" / "e2e" / "test_prefs_persistence.mjs"
    assert script_path.exists(), f"Persistence test script missing: {script_path}"

    result = subprocess.run(
        ["node", "--test", str(script_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Node preferences persistence suite failed (exit {result.returncode}):\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    assert "fail 0" in result.stdout


# ==============================================================================
# Test 2: Step 1 — Welcome & Onboarding Comfort Setup (/welcome.html)
# ==============================================================================


def test_e2e_step1_welcome_and_comfort(client: TestClient) -> None:
    """Step 1: Fetches /welcome.html, verifies anti-FOUC script, wizard card, and live preview."""
    res = client.get("/welcome.html")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.text

    # Anti-FOUC inline head script reading wp.prefs.v1
    assert "wp.prefs.v1" in html
    assert "document.documentElement" in html
    assert "setAttribute" in html

    # Wizard Card and Question Navigation Elements
    assert 'id="wizard-card"' in html
    assert 'id="wizard-form"' in html
    assert 'id="wizard-step-counter"' in html
    assert 'id="wizard-progress-bar"' in html
    assert 'id="question-prompt"' in html
    assert 'id="question-options"' in html
    assert 'id="btn-wizard-prev"' in html
    assert 'id="btn-wizard-next"' in html
    assert 'id="btn-wizard-save"' in html
    assert 'id="btn-wizard-save-now"' in html

    # Real-Time Live Preview Panel
    assert 'id="welcome-live-preview"' in html
    assert 'id="preview-badges"' in html
    assert 'id="preview-sample-card"' in html

    # Vanilla ES module script
    assert 'src="/js/welcome.js"' in html


# ==============================================================================
# Test 3: Step 2 — Employee Clarify / Onboarding (POST /api/simplify)
# ==============================================================================


def test_e2e_step2_clarify_onboarding(client: TestClient, onboarding_text: str) -> None:
    """Step 2: Calls POST /api/simplify, asserts summary, numbered steps with verbatim quotes."""
    payload = {
        "text": onboarding_text,
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

    # Plain Romanian summary
    assert "summary" in data and isinstance(data["summary"], str)
    assert len(data["summary"].strip()) > 0

    # Numbered steps
    assert "steps" in data and isinstance(data["steps"], list)
    assert len(data["steps"]) > 0
    for step in data["steps"]:
        assert "n" in step and isinstance(step["n"], int)
        assert "text" in step and len(step["text"].strip()) > 0
        assert "source_quote" in step
        # Grounding: verify source_quote exists verbatim in source document if non-empty
        quote = step["source_quote"].strip()
        if quote:
            assert quote.lower() in onboarding_text.lower(), (
                f"Source quote '{quote}' not found verbatim in onboarding document"
            )

    # Key terms explained
    assert "key_terms" in data and isinstance(data["key_terms"], list)
    for term_entry in data["key_terms"]:
        assert "term" in term_entry and len(term_entry["term"].strip()) > 0
        assert "explanation" in term_entry and len(term_entry["explanation"].strip()) > 0

    # Colleague/manager questions
    assert "questions_to_ask" in data and isinstance(data["questions_to_ask"], list)

    # Transparency meta notice
    meta = body["meta"]
    assert "ai_notice_ro" in meta
    assert "Generat de AI" in meta["ai_notice_ro"]


# ==============================================================================
# Test 4: Step 3 — Planner Screen with Ambiguous Deadline Protection
# ==============================================================================


def test_e2e_step3_planner(client: TestClient, task_email_text: str) -> None:
    """Step 3: Calls POST /api/plan/extract, verifies tasks, priorities, quotes, and ambiguous date guard."""
    payload = {
        "text": task_email_text,
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

    has_ambiguous_protected_task = False
    for task in data["tasks"]:
        assert "id" in task
        assert "title" in task and len(task["title"].strip()) > 0
        assert task["priority"] in {"high", "normal", "low"}
        assert "source_quote" in task

        # Grounding check: source_quote exists in input
        quote = task["source_quote"].strip()
        if quote:
            assert quote.lower() in task_email_text.lower(), (
                f"Planner source quote '{quote}' not found in task email text"
            )

        # Ambiguous deadline protection: needs_confirmation=True, due_iso is None
        if task.get("needs_confirmation") is True and task.get("due_iso") is None:
            has_ambiguous_protected_task = True
            assert "due_text" in task and len(task["due_text"].strip()) > 0

    assert has_ambiguous_protected_task, "Expected at least one task with ambiguous deadline guard (needs_confirmation=True, due_iso=None)"


# ==============================================================================
# Test 5: Step 4 — Meeting Helper Screen with Zero Emotion Inference
# ==============================================================================


def test_e2e_step4_meeting_helper(client: TestClient, meeting_text: str) -> None:
    """Step 4: Calls POST /api/meeting/summarize, verifies decisions, action items with who, and no emotion inference."""
    payload = {
        "transcript": meeting_text,
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
    for dec in data["decisions"]:
        assert "text" in dec and len(dec["text"].strip()) > 0
        assert "source_quote" in dec
        if dec["source_quote"].strip():
            assert dec["source_quote"].strip().lower() in meeting_text.lower()

    assert "action_items" in data and isinstance(data["action_items"], list)
    assert len(data["action_items"]) > 0
    for act in data["action_items"]:
        assert "task" in act and len(act["task"].strip()) > 0
        assert "who" in act and len(act["who"].strip()) > 0
        assert "source_quote" in act
        if act["source_quote"].strip():
            assert act["source_quote"].strip().lower() in meeting_text.lower()

    assert "unclear_points" in data and isinstance(data["unclear_points"], list)

    # EU AI Act Compliance: STRICT ZERO EMOTION INFERENCE in meeting analysis
    banned_emotion_words = [
        "furios", "nervos", "anxios", "fericit", "trist", "emoție",
        "sentiment", "frustrat", "agitat", "bucuros", "entuziasmat"
    ]
    raw_meeting_output = json.dumps(data, ensure_ascii=False).lower()
    for word in banned_emotion_words:
        assert word not in raw_meeting_output, (
            f"Prohibited emotion inference word '{word}' found in meeting summary output"
        )


# ==============================================================================
# Test 6: Step 5 — Workplace Adjustments Catalog & Draft
# ==============================================================================


def test_e2e_step5_workplace_adjustments(client: TestClient) -> None:
    """Step 5: Verifies catalog items (>= 12) with disclaimer, and tailored draft generation."""
    # 1. Fetch catalog
    cat_res = client.get("/api/adjustments/catalog")
    assert cat_res.status_code == 200
    cat_body = cat_res.json()
    assert cat_body["ok"] is True
    cat_data = cat_body["data"]
    assert "disclaimer_ro" in cat_data
    assert "nu reprezintă consultanță juridică" in cat_data["disclaimer_ro"].lower()
    assert len(cat_data["items"]) >= 12

    # Verify functional accommodation items
    item_ids = {i["id"] for i in cat_data["items"]}
    assert "written_instructions" in item_ids
    assert "extra_time" in item_ids

    # 2. Draft accommodation request email
    draft_res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions", "extra_time"],
            "context": "onboarding",
            "employer_name": "Tehnologie SRL",
            "tone": "friendly",
        },
    )
    assert draft_res.status_code == 200
    draft_body = draft_res.json()
    assert draft_body["ok"] is True
    draft_data = draft_body["data"]
    assert "subject" in draft_data and len(draft_data["subject"].strip()) > 0
    assert "body_ro" in draft_data and len(draft_data["body_ro"].strip()) > 0
    assert "checklist" in draft_data and len(draft_data["checklist"]) == 2

    # 3. Guardrail: Rejection of unknown adjustment IDs with HTTP 400
    bad_res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["unknown_fake_accommodation_id_9999"],
            "context": "onboarding",
        },
    )
    assert bad_res.status_code == 400
    bad_body = bad_res.json()
    assert bad_body["ok"] is False
    assert bad_body["error"]["code"] == "bad_request"


# ==============================================================================
# Test 7: Step 6 — Employer Document Cognitive Accessibility Review
# ==============================================================================


def test_e2e_step6_employer_review(client: TestClient, onboarding_text: str) -> None:
    """Step 6: Calls POST /api/employer/analyze, verifies readability score, issues with quotes, easy-read rewrite."""
    payload = {
        "text": onboarding_text,
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
    assert 0 <= readability["score_0_100"] <= 100
    assert readability["sentence_count"] > 0
    assert readability["avg_sentence_words"] > 0

    # Issues with verbatim quotes
    assert "issues" in data and isinstance(data["issues"], list)
    for issue in data["issues"]:
        assert "kind" in issue
        assert "quote" in issue
        assert "fix" in issue

    # Easy-read rewrite
    assert "easy_read_ro" in data and len(data["easy_read_ro"].strip()) > 0

    # Adjustment checklist recommendations
    assert "adjustment_checklist" in data and isinstance(data["adjustment_checklist"], list)


# ==============================================================================
# Test 8: All 8 Served HTML Routes Landmark & A11y Gate
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
def test_e2e_all_served_html_routes_a11y_and_landmarks(client: TestClient, route: str) -> None:
    """Audits all served HTML routes for HTTP 200, lang='ro', skip link, main id='main', aria-live, single h1, zero CDN."""
    res = client.get(route)
    assert res.status_code == 200, f"Route {route} returned HTTP {res.status_code}"
    html = res.text

    # 1. Romanian language attribute on <html>
    assert bool(re.search(r"<html\b[^>]*lang=[\"']ro[\"']", html, re.I)), (
        f"Route {route} missing <html lang='ro'>"
    )

    # 2. Skip link to main content
    assert bool(re.search(r"<a\b[^>]*href=[\"']#main[\"']", html, re.I)), (
        f"Route {route} missing skip link <a href='#main'>"
    )

    # 3. Main landmark with id="main"
    assert bool(re.search(r"<main\b[^>]*id=[\"']main[\"']", html, re.I)), (
        f"Route {route} missing <main id='main'>"
    )

    # 4. Live region for polite screen reader announcements
    assert 'aria-live="polite"' in html or 'role="status"' in html, (
        f"Route {route} missing aria-live='polite' region"
    )

    # 5. Exactly one <h1> heading (excluding HTML comments)
    clean_html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    h1_matches = re.findall(r"<h1\b", clean_html, re.I)
    assert len(h1_matches) == 1, (
        f"Route {route} expected exactly one <h1>, found {len(h1_matches)}"
    )

    # 6. Zero external CDN dependencies (offline-safe)
    cdn_links = re.findall(r"<(?:script|link)[^>]*(?:href|src)=[\"']https?://", clean_html, re.I)
    assert len(cdn_links) == 0, (
        f"Route {route} contains external CDN references: {cdn_links}"
    )


# ==============================================================================
# Test 9: Attack — Negative Inputs & Standard Error Envelopes (CONTRACTS §1)
# ==============================================================================


@pytest.mark.parametrize(
    "endpoint,payload,expected_code",
    [
        ("/api/simplify", {"text": "   "}, "empty_input"),
        ("/api/simplify", {"text": "A" * 12001}, "too_long"),
        ("/api/plan/extract", {"text": ""}, "empty_input"),
        ("/api/plan/extract", {"text": "B" * 12001}, "too_long"),
        ("/api/meeting/summarize", {"transcript": "   "}, "empty_input"),
        ("/api/meeting/summarize", {"transcript": "C" * 12001}, "too_long"),
        ("/api/adjustments/draft", {"need_ids": [], "context": "onboarding"}, "empty_input"),
        ("/api/employer/analyze", {"text": "   ", "doc_type": "onboarding"}, "empty_input"),
        ("/api/employer/analyze", {"text": "D" * 12001, "doc_type": "onboarding"}, "too_long"),
    ],
)
def test_e2e_negative_input_error_envelopes(
    client: TestClient, endpoint: str, payload: dict, expected_code: str
) -> None:
    """Attacks all demo POST endpoints with empty/oversized inputs; asserts HTTP 400 error envelope."""
    res = client.post(endpoint, json=payload)
    assert res.status_code == 400, f"Expected 400 for {endpoint}, got {res.status_code}: {res.text}"
    body = res.json()
    assert body.get("ok") is False
    assert "error" in body
    assert body["error"]["code"] == expected_code
    assert "message_ro" in body["error"] and len(body["error"]["message_ro"].strip()) > 0


# ==============================================================================
# Test 10: Step 3 Planner Calendar Export RFC 5545 Rules
# ==============================================================================


def test_e2e_step3_planner_calendar_export_contract(client: TestClient, task_email_text: str) -> None:
    """Verifies that extracted tasks conform to RFC 5545 calendar export rules."""
    res = client.post(
        "/api/plan/extract",
        json={"text": task_email_text, "today_iso": "2026-10-22"},
    )
    assert res.status_code == 200
    tasks = res.json()["data"]["tasks"]

    # Verify task properties needed for ics.js export
    for t in tasks:
        assert "id" in t
        assert "title" in t
        assert "priority" in t
        assert "needs_confirmation" in t
        if t["needs_confirmation"]:
            # Ambiguous tasks must not have confirmed ISO dates
            assert t.get("due_iso") is None
            assert "due_text" in t


# ==============================================================================
# Test 11: Route Metadata, Viewport, and Accessibility Title Gate
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
def test_e2e_all_routes_meta_viewport_and_titles(client: TestClient, route: str) -> None:
    """Audits all served HTML routes for valid <title> with PrimaZi and scalable viewport."""
    res = client.get(route)
    assert res.status_code == 200
    html = res.text

    # Title verification
    title_match = re.search(r"<title>(.*?)</title>", html, re.I | re.DOTALL)
    assert title_match is not None, f"Route {route} missing <title>"
    assert "PrimaZi" in title_match.group(1), f"Route {route} <title> does not mention PrimaZi"

    # Viewport verification without zoom blocking (WCAG 1.4.4)
    viewport_match = re.search(r"<meta\b[^>]*name=[\"']viewport[\"'][^>]*content=[\"']([^\"']+)[\"']", html, re.I)
    assert viewport_match is not None, f"Route {route} missing meta viewport"
    content = viewport_match.group(1).lower()
    assert "width=device-width" in content
    assert "user-scalable=no" not in content, f"Route {route} disables user scaling"
    assert "maximum-scale=1" not in content, f"Route {route} restricts maximum scale"

