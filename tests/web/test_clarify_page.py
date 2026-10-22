"""Tests for web/employee/clarify.html and web/employee/clarify.js (owner: p2)."""
import json
import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_a11y_static import audit_html

ROOT = Path(__file__).resolve().parent.parent.parent
CLARIFY_JS = ROOT / "web" / "employee" / "clarify.js"
CLARIFY_HTML = ROOT / "web" / "employee" / "clarify.html"


def run_clarify_js(expression: str) -> dict:
    """Helper to evaluate JS expressions on clarify.js using Node.js."""
    script = f"""
    import * as clarifyMod from "{CLARIFY_JS.as_posix()}";
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


def test_clarify_html_passes_static_a11y_audit():
    """Verify that clarify.html passes static WCAG 2.2 AA audit."""
    assert CLARIFY_HTML.exists(), "web/employee/clarify.html must exist"
    html_text = CLARIFY_HTML.read_text(encoding="utf-8")
    problems = audit_html(html_text)
    assert not problems, f"Static a11y audit failed for clarify.html: {problems}"


def test_clarify_html_landmarks_and_controls():
    """Verify essential landmarks, single h1, skip link, live region, and form controls."""
    html_text = CLARIFY_HTML.read_text(encoding="utf-8")

    # Landmarks & Accessibility essentials
    assert '<a href="#main" class="skip-link">Sari la conținutul principal</a>' in html_text
    assert '<main id="main">' in html_text
    assert 'aria-live="polite"' in html_text
    assert html_text.count("<h1") == 1
    assert "</h1>" in html_text

    # Inputs & Labels
    assert 'id="file-upload"' in html_text
    assert 'for="file-upload"' in html_text
    assert 'id="doc-text"' in html_text
    assert 'for="doc-text"' in html_text
    assert 'id="char-counter"' in html_text

    # Action buttons
    assert 'id="btn-clarify"' in html_text
    assert 'id="btn-load-sample"' in html_text
    assert 'id="btn-clear-text"' in html_text
    assert 'id="btn-tts-toggle"' in html_text

    # Source viewer with accessible region role
    assert 'id="source-viewer"' in html_text
    assert 'role="region"' in html_text

    # Planner CTA link
    assert 'href="/employee/plan.html"' in html_text


def test_clarify_js_sample_onboarding_text():
    """Verify SAMPLE_ONBOARDING_TEXT is exported and matches Romanian onboarding reality."""
    sample = run_clarify_js("return clarifyMod.SAMPLE_ONBOARDING_TEXT;")
    assert isinstance(sample, str)
    assert len(sample) > 300
    assert "Companie Exemplu SRL" in sample
    assert "Mihaela Popescu" in sample
    assert "F-12" in sample
    assert "SecInfo v3" in sample
    assert "hr@exemplu.example" in sample


def test_normalize_whitespace():
    """Verify whitespace normalization collapses tabs, newlines, and multiple spaces."""
    script = """
    return {
        collapsed: clarifyMod.normalizeWhitespace("  Luni,   ora  09:00 \\n\\n\\t  Te prezinți   "),
        empty: clarifyMod.normalizeWhitespace(""),
        nullish: clarifyMod.normalizeWhitespace(null)
    };
    """
    res = run_clarify_js(script)
    assert res["collapsed"] == "Luni, ora 09:00 Te prezinți"
    assert res["empty"] == ""
    assert res["nullish"] == ""


def test_highlight_quote_exact_match():
    """Verify highlightQuoteInContainer marks the quote and returns true."""
    script = """
    const container = { innerHTML: "" };
    const text = "Luni, ora 09:00 – Te prezinți la recepție și ceri cardul de acces.";
    const quote = "Te prezinți la recepție";
    const matched = clarifyMod.highlightQuoteInContainer(container, text, quote);
    return { matched, html: container.innerHTML };
    """
    res = run_clarify_js(script)
    assert res["matched"] is True
    assert '<mark class="quote-highlight" id="active-quote">Te prezinți la recepție</mark>' in res["html"]
    assert res["html"].startswith("Luni, ora 09:00 – ")
    assert res["html"].endswith(" și ceri cardul de acces.")


def test_highlight_quote_whitespace_tolerant():
    """Verify quote highlighting succeeds when text has newlines and quote has single space."""
    script = """
    const container = { innerHTML: "" };
    const text = "Până miercuri,\\n28 octombrie,\\ntrebuie să completezi formularul.";
    const quote = "Până miercuri, 28 octombrie, trebuie";
    const matched = clarifyMod.highlightQuoteInContainer(container, text, quote);
    return { matched, html: container.innerHTML };
    """
    res = run_clarify_js(script)
    assert res["matched"] is True
    assert '<mark class="quote-highlight" id="active-quote">' in res["html"]
    assert "Până miercuri,\n28 octombrie,\ntrebuie" in res["html"]


def test_highlight_quote_not_found_or_cleared():
    """Verify behavior when quote is not in the text or quote is null/empty."""
    script = """
    const container = { innerHTML: "" };
    const text = "Textul original simplu.";
    const notFound = clarifyMod.highlightQuoteInContainer(container, text, "Fraza inexistentă");
    const htmlNotFound = container.innerHTML;

    const cleared = clarifyMod.highlightQuoteInContainer(container, text, null);
    const htmlCleared = container.innerHTML;

    return { notFound, htmlNotFound, cleared, htmlCleared };
    """
    res = run_clarify_js(script)
    assert res["notFound"] is False
    assert "<mark" not in res["htmlNotFound"]
    assert res["htmlNotFound"] == "Textul original simplu."

    assert res["cleared"] is False
    assert "<mark" not in res["htmlCleared"]
    assert res["htmlCleared"] == "Textul original simplu."


def test_highlight_quote_xss_protection():
    """Verify that malicious quotes or document texts are safely escaped in output."""
    script = """
    const container = { innerHTML: "" };
    const maliciousText = "Inceput <script>alert('pwn')</script> mijloc sfarsit";
    const quote = "<script>alert('pwn')</script>";
    const matched = clarifyMod.highlightQuoteInContainer(container, maliciousText, quote);
    return { matched, html: container.innerHTML };
    """
    res = run_clarify_js(script)
    assert res["matched"] is True
    assert "<script>" not in res["html"]
    assert "&lt;script&gt;alert(&#039;pwn&#039;)&lt;/script&gt;" in res["html"]


def test_highlight_quote_special_regex_characters():
    """Verify quote highlighting works when quotes contain regex special characters.
    Ensures brackets, parentheses, asterisks, dots, slashes, pluses, etc. are properly escaped.
    """
    script = r"""
    const container = { innerHTML: "" };
    const text = "Formularul [F-12] (date personale) costa $0.00 la C:\\\\path\\\\docs *important* {v1} a+b | c?";

    // Test brackets and parentheses
    const m1 = clarifyMod.highlightQuoteInContainer(container, text, "[F-12] (date personale)");
    const h1 = container.innerHTML;

    // Test asterisks and dots and backslash
    const m2 = clarifyMod.highlightQuoteInContainer(container, text, "$0.00 la C:\\\\path\\\\docs *important*");
    const h2 = container.innerHTML;

    // Test braces, plus, pipe, question mark
    const m3 = clarifyMod.highlightQuoteInContainer(container, text, "{v1} a+b | c?");
    const h3 = container.innerHTML;

    return { m1, h1, m2, h2, m3, h3 };
    """
    res = run_clarify_js(script)
    assert res["m1"] is True
    assert '<mark class="quote-highlight" id="active-quote">[F-12] (date personale)</mark>' in res["h1"]

    assert res["m2"] is True
    assert '<mark class="quote-highlight" id="active-quote">$0.00 la C:\\\\path\\\\docs *important*</mark>' in res["h2"]

    assert res["m3"] is True
    assert '<mark class="quote-highlight" id="active-quote">{v1} a+b | c?</mark>' in res["h3"]


def test_highlight_quote_repeated_in_document():
    """Verify quote highlighting when quote appears multiple times in the document.
    Should highlight the first match, leave subsequent instances intact and valid,
    and preserve document integrity without duplicate active-quote IDs.
    """
    script = """
    const container = { innerHTML: "" };
    const text = "Mihaela Popescu este la HR. Întreab-o pe Mihaela Popescu despre acces.";
    const quote = "Mihaela Popescu";
    const matched = clarifyMod.highlightQuoteInContainer(container, text, quote);
    return { matched, html: container.innerHTML };
    """
    res = run_clarify_js(script)
    assert res["matched"] is True
    html = res["html"]
    # Only one mark tag with id="active-quote"
    assert html.count('<mark class="quote-highlight" id="active-quote">') == 1
    assert '<mark class="quote-highlight" id="active-quote">Mihaela Popescu</mark>' in html
    # Second instance remains in text after the mark
    assert "Întreab-o pe Mihaela Popescu despre acces." in html


def test_highlight_quote_edge_cases_null_and_empty():
    """Verify highlightQuoteInContainer handles null container, empty text, or whitespace quote."""
    script = """
    return {
        nullContainer: clarifyMod.highlightQuoteInContainer(null, "some text", "quote"),
        emptyText: (function() {
            const c = { innerHTML: "initial" };
            const res = clarifyMod.highlightQuoteInContainer(c, "", "quote");
            return { res, html: c.innerHTML };
        })(),
        whitespaceQuote: (function() {
            const c = { innerHTML: "initial" };
            const res = clarifyMod.highlightQuoteInContainer(c, "Some text here", "   \\t\\n  ");
            return { res, html: c.innerHTML };
        })()
    };
    """
    res = run_clarify_js(script)
    assert res["nullContainer"] is False
    assert res["emptyText"]["res"] is False
    assert res["emptyText"]["html"] == ""
    assert res["whitespaceQuote"]["res"] is False
    assert res["whitespaceQuote"]["html"] == "Some text here"


def test_render_warnings_and_summary():
    """Verify warning banners and summary paragraphs rendering."""
    script = """
    const warnContainer = { innerHTML: "", style: {}, className: "", setAttribute: () => {} };
    clarifyMod.renderWarnings(warnContainer, ["1 element eliminat: citatul nu apare în text."]);
    const warnHtml = warnContainer.innerHTML;

    const summaryContainer = { innerHTML: "" };
    clarifyMod.renderSummary(summaryContainer, "Începi luni la ora 09:00.");
    const summaryHtml = summaryContainer.innerHTML;

    return { warnHtml, summaryHtml };
    """
    res = run_clarify_js(script)
    assert "1 element eliminat: citatul nu apare în text." in res["warnHtml"]
    assert "status-warning" in res["warnHtml"] or "Atenționări" in res["warnHtml"]
    assert "Începi luni la ora 09:00." in res["summaryHtml"]


def test_render_steps_key_terms_and_questions():
    """Verify rendering of structured steps, key terms, and suggested questions."""
    script = """
    const stepsContainer = { innerHTML: "" };
    const steps = [
        { n: 1, text: "Mergi la recepție", source_quote: "Te prezinți la recepția clădirii B" },
        { n: 2, text: "Completează formularul F-12", source_quote: "formularul F-12" }
    ];
    clarifyMod.renderSteps(stepsContainer, steps);

    const termsContainer = { innerHTML: "" };
    const terms = [{ term: "onboarding", explanation: "Perioada inițială de integrare." }];
    clarifyMod.renderKeyTerms(termsContainer, terms);

    const qContainer = { innerHTML: "" };
    const questions = ["Pot primi instrucțiunile și în scris?"];
    clarifyMod.renderQuestions(qContainer, questions);

    return {
        stepsHtml: stepsContainer.innerHTML,
        termsHtml: termsContainer.innerHTML,
        qHtml: qContainer.innerHTML
    };
    """
    res = run_clarify_js(script)
    assert "Mergi la recepție" in res["stepsHtml"]
    assert "Arată în text" in res["stepsHtml"]
    assert "Te prezinți la recepția clădirii B" in res["stepsHtml"]

    assert "onboarding" in res["termsHtml"]
    assert "Perioada inițială de integrare." in res["termsHtml"]

    assert "Pot primi instrucțiunile și în scris?" in res["qHtml"]


def test_client_api_empty_text_rejection():
    """Verify clarify client API (api.js simplifyDocument) rejects empty text immediately without network call."""
    api_js = ROOT / "web" / "shared" / "api.js"
    script = f"""
    import {{ simplifyDocument }} from "{api_js.as_posix()}";
    const res1 = await simplifyDocument("");
    const res2 = await simplifyDocument("   \\t\\n  ");
    process.stdout.write(JSON.stringify({{ res1, res2 }}));
    """
    res = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        check=True,
    )
    data = json.loads(res.stdout.decode("utf-8"))
    assert data["res1"]["ok"] is False
    assert data["res1"]["error"]["code"] == "empty_input"
    assert data["res2"]["ok"] is False
    assert data["res2"]["error"]["code"] == "empty_input"


@pytest.mark.anyio
async def test_live_http_serving_clarify_html():
    """Live HTTP serving test via ASGI: verify GET /employee/clarify.html returns 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/employee/clarify.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        html = response.text
        assert html.count("<h1") == 1
        assert '<a href="#main" class="skip-link">' in html
        assert '<main id="main">' in html
        assert 'id="source-viewer"' in html
        assert 'id="btn-clarify"' in html

        problems = audit_html(html)
        assert not problems, f"Static a11y audit failed on served page: {problems}"


@pytest.mark.anyio
async def test_api_simplify_mock_e2e_shape():
    """Verify POST /api/simplify returns the exact schema clarify.js depends on."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "Bine ai venit! Luni la 09:00 te prezinți la recepție.",
            "profile": {
                "reading_level": "simple",
                "format": "steps",
                "needs_notes": "Sarcini clare.",
                "max_sentence_words": 12,
            },
        }
        response = await client.post("/api/simplify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "summary" in data["data"]
        assert "steps" in data["data"]
        assert "key_terms" in data["data"]
        assert "questions_to_ask" in data["data"]
        assert "meta" in data


@pytest.mark.anyio
async def test_api_simplify_input_boundary_limits():
    """Attack input boundary limits on POST /api/simplify:
    - empty string -> 400 empty_input
    - whitespace only -> 400 empty_input
    - exactly 12000 chars -> 200 OK
    - 12001 chars (> 12000) -> 400 too_long
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Empty string
        res_empty = await client.post("/api/simplify", json={"text": ""})
        assert res_empty.status_code == 400
        data_empty = res_empty.json()
        assert data_empty["ok"] is False
        assert data_empty["error"]["code"] == "empty_input"
        assert "gol" in data_empty["error"]["message_ro"]

        # 2. Whitespace only
        res_ws = await client.post("/api/simplify", json={"text": "   \n\t  \r\n   "})
        assert res_ws.status_code == 400
        data_ws = res_ws.json()
        assert data_ws["ok"] is False
        assert data_ws["error"]["code"] == "empty_input"

        # 3. Exactly 12000 characters
        exact_text = "Luni, ora 09:00 – Te prezinți la recepția clădirii B" + ("." * (12000 - 52))
        assert len(exact_text) == 12000
        res_exact = await client.post("/api/simplify", json={"text": exact_text})
        assert res_exact.status_code == 200
        data_exact = res_exact.json()
        assert data_exact["ok"] is True
        assert "summary" in data_exact["data"]

        # 4. Over 12000 characters (12001 chars)
        too_long_text = "A" * 12001
        res_long = await client.post("/api/simplify", json={"text": too_long_text})
        assert res_long.status_code == 400
        data_long = res_long.json()
        assert data_long["ok"] is False
        assert data_long["error"]["code"] == "too_long"
        assert "12000" in data_long["error"]["message_ro"] or "12.000" in data_long["error"]["message_ro"]


@pytest.mark.anyio
async def test_live_asgi_onboarding_sample_document_e2e_binding():
    """Attack live ASGI request with realistic sample document (data/samples/onboarding_ro.txt)
    against /api/simplify and ensure response binds cleanly into clarify UI rendering functions.
    """
    sample_path = ROOT / "data" / "samples" / "onboarding_ro.txt"
    assert sample_path.exists(), "Sample document data/samples/onboarding_ro.txt must exist"
    sample_text = sample_path.read_text(encoding="utf-8")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": sample_text,
            "profile": {
                "reading_level": "simple",
                "format": "steps",
                "needs_notes": "Instrucțiuni pas cu pas pentru prima săptămână.",
                "max_sentence_words": 14,
            },
        }
        response = await client.post("/api/simplify", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        data = body["data"]
        meta = body["meta"]

        # Ensure summary, steps, key_terms, questions exist and have content
        assert isinstance(data["summary"], str) and len(data["summary"]) > 0
        assert isinstance(data["steps"], list) and len(data["steps"]) >= 2
        assert isinstance(data["key_terms"], list) and len(data["key_terms"]) >= 1
        assert isinstance(data["questions_to_ask"], list) and len(data["questions_to_ask"]) >= 1
        assert meta["provider"] == "mock"
        assert meta["warnings"] == []  # All quotes match sample text, zero dropped

        # Verify that all steps have source_quote and highlightQuoteInContainer succeeds
        for step in data["steps"]:
            assert "source_quote" in step and step["source_quote"]
            quote = step["source_quote"]
            script = f"""
            const container = {{ innerHTML: "" }};
            const text = {json.dumps(sample_text)};
            const quote = {json.dumps(quote)};
            const matched = clarifyMod.highlightQuoteInContainer(container, text, quote);
            return {{ matched, hasMark: container.innerHTML.includes('<mark class="quote-highlight" id="active-quote">') }};
            """
            hl_res = run_clarify_js(script)
            assert hl_res["matched"] is True, f"Failed to highlight quote '{quote}' in sample text"
            assert hl_res["hasMark"] is True

        # Verify UI rendering functions bind cleanly with this response payload
        render_script = f"""
        const summaryCont = {{ innerHTML: "" }};
        const stepsCont = {{ innerHTML: "" }};
        const termsCont = {{ innerHTML: "" }};
        const qCont = {{ innerHTML: "" }};
        const warnCont = {{ innerHTML: "", style: {{}}, setAttribute: () => {{}} }};

        const data = {json.dumps(data)};
        const meta = {json.dumps(meta)};

        clarifyMod.renderSummary(summaryCont, data.summary);
        clarifyMod.renderSteps(stepsCont, data.steps);
        clarifyMod.renderKeyTerms(termsCont, data.key_terms);
        clarifyMod.renderQuestions(qCont, data.questions_to_ask);
        clarifyMod.renderWarnings(warnCont, meta.warnings);

        return {{
            summaryHtml: summaryCont.innerHTML,
            stepsHtml: stepsCont.innerHTML,
            termsHtml: termsCont.innerHTML,
            qHtml: qCont.innerHTML,
            warnDisplay: warnCont.style.display
        }};
        """
        ui_res = run_clarify_js(render_script)
        assert data["summary"] in ui_res["summaryHtml"]
        assert "Arată în text" in ui_res["stepsHtml"]
        assert data["steps"][0]["source_quote"] in ui_res["stepsHtml"]
        assert data["key_terms"][0]["term"] in ui_res["termsHtml"]
        assert data["questions_to_ask"][0] in ui_res["qHtml"]
        assert ui_res["warnDisplay"] == "none"  # No warnings
