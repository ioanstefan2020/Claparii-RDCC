"""Tests for web/employee/adjustments.html and web/employee/adjustments.js (owner: p2)."""
import json
import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_a11y_static import audit_html

ROOT = Path(__file__).resolve().parent.parent.parent
ADJUSTMENTS_JS = ROOT / "web" / "employee" / "adjustments.js"
ADJUSTMENTS_HTML = ROOT / "web" / "employee" / "adjustments.html"


def run_adjustments_js(expression: str) -> dict:
    """Helper to evaluate JS expressions on adjustments.js using Node.js."""
    script = f"""
    import * as adjMod from "{ADJUSTMENTS_JS.as_posix()}";
    const result = (function() {{
        {expression}
    }})();
    process.stdout.write(JSON.stringify(result));
    """
    res = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        check=True,
    )
    return json.loads(res.stdout.decode("utf-8"))


def test_adjustments_html_passes_static_a11y_audit():
    """Verify that adjustments.html passes static WCAG 2.2 AA audit with 0 issues."""
    assert ADJUSTMENTS_HTML.exists(), "web/employee/adjustments.html must exist"
    html_text = ADJUSTMENTS_HTML.read_text(encoding="utf-8")
    problems = audit_html(html_text)
    assert not problems, f"Static a11y audit failed for adjustments.html: {problems}"


def test_adjustments_html_landmarks_and_controls():
    """Verify essential landmarks, single h1, skip link, live region, and form controls."""
    assert ADJUSTMENTS_HTML.exists(), "web/employee/adjustments.html must exist"
    html_text = ADJUSTMENTS_HTML.read_text(encoding="utf-8")

    # Landmarks & Accessibility essentials
    assert '<a href="#main" class="skip-link">Sari la conținutul principal</a>' in html_text
    assert '<main id="main">' in html_text
    assert 'aria-live="polite"' in html_text
    assert html_text.count("<h1") == 1
    assert "Solicitare de adaptări rezonabile la locul de muncă" in html_text
    assert ('<header role="banner">' in html_text or '<header class="app-topbar" role="banner">' in html_text)
    assert ('<footer role="contentinfo">' in html_text or '<footer class="app-footer" role="contentinfo">' in html_text)

    # Navigation current page check
    assert 'href="/employee/adjustments.html" aria-current="page"' in html_text

    # Adjustments form & controls
    assert 'id="adjustments-form"' in html_text
    assert 'id="catalog-container"' in html_text
    assert 'id="context-select"' in html_text
    assert 'for="context-select"' in html_text
    assert 'id="tone-select"' in html_text
    assert 'for="tone-select"' in html_text
    assert 'id="employer-name"' in html_text
    assert 'for="employer-name"' in html_text
    assert 'id="btn-submit"' in html_text

    # Status & error banners
    assert 'id="error-banner"' in html_text
    assert 'id="status-live"' in html_text
    assert 'id="disclaimer-banner"' in html_text
    assert 'id="ai-notice"' in html_text

    # Draft section & actions
    assert 'id="draft-section"' in html_text
    assert 'id="draft-subject"' in html_text
    assert 'id="draft-body"' in html_text
    assert 'for="draft-body"' in html_text
    assert 'id="btn-copy"' in html_text
    assert 'id="btn-mailto"' in html_text
    assert 'id="btn-download"' in html_text
    assert 'id="checklist-card"' in html_text
    assert 'id="checklist-list"' in html_text


def test_adjustments_js_escape_html():
    """Verify escapeHtml sanitizes script tags, quotes, and ampersands."""
    script = """
    const dirty = '<script>alert("xss & fun")</script>';
    return { clean: adjMod.escapeHtml(dirty) };
    """
    res = run_adjustments_js(script)
    assert "<script>" not in res["clean"]
    assert "&lt;script&gt;" in res["clean"]
    assert "&quot;xss &amp; fun&quot;" in res["clean"]


def test_adjustments_js_render_catalog_items():
    """Verify renderCatalogItems builds accessible checkboxes with labels, descriptions, and tags."""
    script = """
    const container = { innerHTML: "" };
    const items = [
        {
            id: "written_instructions",
            title: "Instrucțiuni scrise, pas cu pas",
            description: "Sarcinile îți sunt date și în format scris.",
            applies_to: ["cognitive", "hearing"],
            example_request: "Aș dori sarcinile în scris."
        },
        {
            id: "flexible_schedule",
            title: "Program flexibil",
            description: "Ajustarea orelor de lucru.",
            applies_to: ["any"],
            example_request: "Aș dori program flexibil."
        }
    ];

    adjMod.renderCatalogItems(items, container);
    return { html: container.innerHTML };
    """
    res = run_adjustments_js(script)
    html = res["html"]
    assert "written_instructions" in html
    assert "Instrucțiuni scrise, pas cu pas" in html
    assert "Sarcinile îți sunt date și în format scris." in html
    assert "flexible_schedule" in html
    assert "Program flexibil" in html
    assert "Cognitiv / Ritm de lucru" in html


def test_adjustments_js_render_draft_result():
    """Verify renderDraftResult populates subject, body, and checklist items."""
    script = """
    const container = { innerHTML: "" };
    const draftData = {
        subject: "Solicitare adaptări început de drum",
        body_ro: "Bună ziua, aș dori să discutăm următoarele adaptări...",
        checklist: [
            { id: "written_instructions", title: "Instrucțiuni scrise", why: "Reduce efortul de memorare orală." }
        ]
    };

    adjMod.renderDraftResult(draftData, container);
    return { html: container.innerHTML };
    """
    res = run_adjustments_js(script)
    html = res["html"]
    assert "Solicitare adaptări început de drum" in html
    assert "Bună ziua, aș dori să discutăm" in html
    assert "1" in html


@pytest.mark.anyio
async def test_live_http_serving_adjustments_html():
    """Live HTTP serving test via ASGI: verify GET /employee/adjustments.html returns 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/employee/adjustments.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        html = response.text
        assert html.count("<h1") == 1
        assert '<a href="#main" class="skip-link">' in html
        assert '<main id="main">' in html
        assert 'id="adjustments-form"' in html
        assert 'id="draft-section"' in html

        problems = audit_html(html)
        assert not problems, f"Static a11y audit failed on served adjustments page: {problems}"


@pytest.mark.anyio
async def test_live_asgi_adjustments_catalog_contract():
    """Verify GET /api/adjustments/catalog returns >= 12 items and disclaimer."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/adjustments/catalog")
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        data = body["data"]

        assert "disclaimer_ro" in data
        assert "nu reprezintă consultanță juridică" in data["disclaimer_ro"].lower()
        items = data["items"]
        assert len(items) >= 12, f"Expected at least 12 catalog items, found {len(items)}"

        ids = [it["id"] for it in items]
        required_minimum = [
            "written_instructions",
            "extra_time",
            "quiet_space",
            "flexible_schedule",
            "screen_reader_tools",
            "captions_transcripts",
            "plain_language_docs",
            "regular_checkins",
            "task_breakdown",
            "advance_agenda",
            "ergonomic_equipment",
            "remote_option",
        ]
        for req_id in required_minimum:
            assert req_id in ids, f"Catalog item '{req_id}' missing from catalog"


@pytest.mark.anyio
async def test_live_asgi_adjustments_draft_contract():
    """Verify POST /api/adjustments/draft returns subject, body, checklist for valid need_ids."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "need_ids": ["written_instructions", "extra_time"],
            "context": "onboarding",
            "employer_name": "S.C. Exemplu S.R.L.",
            "tone": "friendly",
        }
        response = await client.post("/api/adjustments/draft", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        data = body["data"]

        assert "subject" in data and len(data["subject"]) > 0
        assert "body_ro" in data and len(data["body_ro"]) > 50
        assert "checklist" in data and isinstance(data["checklist"], list)
        assert len(data["checklist"]) == 2

        chk_ids = [c["id"] for c in data["checklist"]]
        assert "written_instructions" in chk_ids
        assert "extra_time" in chk_ids


def test_client_api_adjustments_draft_empty_rejection():
    """Verify client draftAdjustments in api.js rejects empty needIds without network call."""
    api_js = ROOT / "web" / "shared" / "api.js"
    script = f"""
    import {{ draftAdjustments }} from "{api_js.as_posix()}";
    const res1 = await draftAdjustments([]);
    const res2 = await draftAdjustments(null);
    process.stdout.write(JSON.stringify({{ res1, res2 }}));
    """
    res = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        check=True,
    )
    data = json.loads(res.stdout.decode("utf-8"))
    assert data["res1"]["ok"] is False
    assert data["res1"]["error"]["code"] == "bad_request"
    assert data["res2"]["ok"] is False
    assert data["res2"]["error"]["code"] == "bad_request"

