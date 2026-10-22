"""Tests for web/employee/meeting.html and web/employee/meeting.js (owner: p2)."""
import json
import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_a11y_static import audit_html

ROOT = Path(__file__).resolve().parent.parent.parent
MEETING_JS = ROOT / "web" / "employee" / "meeting.js"
MEETING_HTML = ROOT / "web" / "employee" / "meeting.html"
SAMPLE_FILE = ROOT / "data" / "samples" / "meeting_transcript_ro.txt"


def run_meeting_js(expression: str) -> dict:
    """Helper to evaluate JS expressions on meeting.js using Node.js."""
    script = f"""
    import * as meetingMod from "{MEETING_JS.as_posix()}";
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


def test_meeting_html_passes_static_a11y_audit():
    """Verify that meeting.html passes static WCAG 2.2 AA audit with 0 issues."""
    assert MEETING_HTML.exists(), "web/employee/meeting.html must exist"
    html_text = MEETING_HTML.read_text(encoding="utf-8")
    problems = audit_html(html_text)
    assert not problems, f"Static a11y audit failed for meeting.html: {problems}"


def test_meeting_html_landmarks_and_controls():
    """Verify essential landmarks, single h1, skip link, live region, and form controls."""
    assert MEETING_HTML.exists(), "web/employee/meeting.html must exist"
    html_text = MEETING_HTML.read_text(encoding="utf-8")

    # Landmarks & Accessibility essentials
    assert '<a href="#main" class="skip-link">Sari la conținutul principal</a>' in html_text
    assert '<main id="main">' in html_text
    assert 'aria-live="polite"' in html_text
    assert html_text.count("<h1") == 1
    assert "Asistent pentru ședințe de lucru și discuții de echipă" in html_text
    assert ('<header role="banner">' in html_text or '<header class="app-topbar" role="banner">' in html_text)
    assert ('<footer role="contentinfo">' in html_text or '<footer class="app-footer" role="contentinfo">' in html_text)

    # Navigation current page check
    assert 'href="/employee/meeting.html" aria-current="page"' in html_text

    # Transcript input form & buttons
    assert 'id="transcript-text"' in html_text
    assert 'for="transcript-text"' in html_text
    assert 'id="btn-submit"' in html_text
    assert 'id="btn-toggle-speech"' in html_text
    assert 'id="btn-load-sample"' in html_text
    assert 'id="btn-clear-transcript"' in html_text
    assert 'id="speech-support-note"' in html_text

    # Status & error banners
    assert 'id="error-banner"' in html_text
    assert 'id="status-live"' in html_text
    assert 'id="ai-notice"' in html_text
    assert 'id="warnings-container"' in html_text

    # Results cards
    assert 'id="results-section"' in html_text
    assert 'id="summary-card"' in html_text
    assert 'id="summary-content"' in html_text
    assert 'id="btn-speak-summary"' in html_text
    assert 'id="decisions-card"' in html_text
    assert 'id="decisions-list"' in html_text
    assert 'id="actions-card"' in html_text
    assert 'id="actions-list"' in html_text
    assert 'id="unclear-card"' in html_text
    assert 'id="unclear-list"' in html_text


def test_meeting_js_sample_transcript():
    """Verify SAMPLE_TRANSCRIPT is exported and matches data/samples/meeting_transcript_ro.txt."""
    sample = run_meeting_js("return meetingMod.SAMPLE_TRANSCRIPT;")
    assert isinstance(sample, str)
    assert len(sample) > 100
    assert "Andrei: Bun, să începem." in sample
    assert "Ioana" in sample
    assert "Radu" in sample
    assert "Mihai" in sample
    assert "lansăm vineri, 6 noiembrie" in sample

    if SAMPLE_FILE.exists():
        expected = SAMPLE_FILE.read_text(encoding="utf-8").strip()
        assert sample.strip() == expected


def test_meeting_js_escape_html():
    """Verify escapeHtml sanitizes script tags, quotes, and ampersands."""
    script = """
    const dirty = '<script>alert("xss & fun")</script>';
    return { clean: meetingMod.escapeHtml(dirty) };
    """
    res = run_meeting_js(script)
    assert "<script>" not in res["clean"]
    assert "&lt;script&gt;" in res["clean"]
    assert "&quot;xss &amp; fun&quot;" in res["clean"]


def test_meeting_js_add_action_item_to_planner():
    """Verify addActionItemToPlanner adds action items into localStorage with planner compatibility."""
    script = """
    const storage = {};
    globalThis.localStorage = {
        getItem: (k) => storage[k] || null,
        setItem: (k, v) => { storage[k] = String(v); },
        removeItem: (k) => { delete storage[k]; }
    };

    const action1 = {
        who: "Ioana",
        task: "Integrează textele finale",
        due_iso: null,
        due_text: "miercuri",
        needs_confirmation: true,
        source_quote: "tu integrezi textele miercuri"
    };

    const action2 = {
        who: null,
        task: "Verifică setările de securitate",
        due_iso: "2026-11-05",
        due_text: "joi",
        needs_confirmation: false,
        source_quote: "setările de securitate joi"
    };

    const after1 = meetingMod.addActionItemToPlanner(action1);
    const after2 = meetingMod.addActionItemToPlanner(action2);
    const rawStored = JSON.parse(storage["primazi_planner_tasks"]);

    return {
        len1: after1.length,
        len2: after2.length,
        storedLen: rawStored.length,
        task1: rawStored[0],
        task2: rawStored[1]
    };
    """
    res = run_meeting_js(script)
    assert res["len1"] == 1
    assert res["len2"] == 2
    assert res["storedLen"] == 2

    t1 = res["task1"]
    assert t1["title"] == "Integrează textele finale"
    assert t1["due_iso"] is None
    assert t1["due_text"] == "miercuri"
    assert t1["needs_confirmation"] is True
    assert t1["priority"] == "normal"
    assert t1["steps"] == ["Asignat către: Ioana"]
    assert t1["source_quote"] == "tu integrezi textele miercuri"
    assert t1["completed"] is False
    assert t1["id"].startswith("task_")

    t2 = res["task2"]
    assert t2["title"] == "Verifică setările de securitate"
    assert t2["due_iso"] == "2026-11-05"
    assert t2["due_text"] == "joi"
    assert t2["needs_confirmation"] is False
    assert t2["steps"] == []
    assert t2["completed"] is False


def test_meeting_js_render_meeting_results():
    """Verify renderMeetingResults renders summary, decisions with quotes, action items, and unclear points."""
    script = """
    const container = { innerHTML: "" };
    const sampleData = {
        summary: "Echipa lansează pagina de produs vineri.",
        decisions: [
            { text: "Lansăm vineri, 6 noiembrie.", source_quote: "lansăm vineri, 6 noiembrie" }
        ],
        action_items: [
            {
                who: "Ioana",
                task: "Integrează textele finale",
                due_iso: null,
                due_text: "miercuri",
                needs_confirmation: true,
                source_quote: "tu integrezi textele miercuri"
            }
        ],
        unclear_points: [
            "Nu e clar cine anunță clientul despre termen."
        ]
    };

    meetingMod.renderMeetingResults(sampleData, container);
    return { html: container.innerHTML };
    """
    res = run_meeting_js(script)
    html = res["html"]
    assert "Echipa lansează pagina de produs vineri." in html
    assert "Lansăm vineri, 6 noiembrie." in html
    assert "lansăm vineri, 6 noiembrie" in html
    assert "Ioana" in html
    assert "Integrează textele finale" in html
    assert "[+ Adaugă în Planificator]" in html
    assert "Nu e clar cine anunță clientul despre termen." in html


@pytest.mark.anyio
async def test_live_http_serving_meeting_html():
    """Live HTTP serving test via ASGI: verify GET /employee/meeting.html returns 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/employee/meeting.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        html = response.text
        assert html.count("<h1") == 1
        assert '<a href="#main" class="skip-link">' in html
        assert '<main id="main">' in html
        assert 'id="transcript-text"' in html
        assert 'id="btn-submit"' in html
        assert 'id="results-section"' in html

        problems = audit_html(html)
        assert not problems, f"Static a11y audit failed on served meeting page: {problems}"


@pytest.mark.anyio
async def test_live_asgi_meeting_summarize_contract():
    """Verify POST /api/meeting/summarize returns valid schema with decisions, action items, and quotes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sample_text = SAMPLE_FILE.read_text(encoding="utf-8") if SAMPLE_FILE.exists() else "Andrei: Lansăm vineri."
        payload = {
            "transcript": sample_text,
            "today_iso": "2026-10-22",
            "profile": {
                "reading_level": "simple",
                "format": "steps",
                "needs_notes": "Extrage decizii clare și acțiuni",
                "max_sentence_words": 12,
            },
        }
        response = await client.post("/api/meeting/summarize", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        data = body["data"]

        assert "summary" in data and len(data["summary"].strip()) > 0
        assert "decisions" in data and isinstance(data["decisions"], list)
        assert "action_items" in data and isinstance(data["action_items"], list)
        assert "unclear_points" in data and isinstance(data["unclear_points"], list)

        # In mock mode, MOCK returns >= 1; with live LLM it extracts >= 4 action items
        meta = body.get("meta", {})
        if meta.get("provider") != "mock":
            assert len(data["action_items"]) >= 4, "Live LLM expected to extract >= 4 action items"
        else:
            assert len(data["action_items"]) >= 1, "Mock expected to extract >= 1 action item"

        for dec in data["decisions"]:
            assert "text" in dec
            assert "source_quote" in dec
            assert dec["source_quote"] in sample_text

        for act in data["action_items"]:
            assert "task" in act
            assert "source_quote" in act
            assert act["source_quote"] in sample_text


def test_meeting_action_items_planner_bridge_contract():
    """Verify that all 4 action items from the meeting transcript can be safely added to planner storage."""
    script = """
    const storage = {};
    globalThis.localStorage = {
        getItem: (k) => storage[k] || null,
        setItem: (k, v) => { storage[k] = String(v); },
        removeItem: (k) => { delete storage[k]; }
    };

    const actionItems = [
        { who: "Radu", task: "Trimite textele pe e-mail", due_iso: null, due_text: "până marți", needs_confirmation: true, source_quote: "Textele vor fi gata până marți, le trimit eu pe e-mail." },
        { who: "Ioana", task: "Integrează textele finale", due_iso: null, due_text: "miercuri", needs_confirmation: true, source_quote: "tu integrezi textele miercuri" },
        { who: "Mihai", task: "Verifică partea de testare și afișarea pe telefon", due_iso: null, due_text: "joi dimineață", needs_confirmation: true, source_quote: "Eu verific partea de testare joi dimineață." },
        { who: "Andrei", task: "Scrie clientului despre noul termen", due_iso: null, due_text: "azi", needs_confirmation: true, source_quote: "Rămâne la mine, îi scriu azi." }
    ];

    let tasks = [];
    for (const act of actionItems) {
        tasks = meetingMod.addActionItemToPlanner(act);
    }

    return {
        taskCount: tasks.length,
        assignees: tasks.map(t => t.steps[0]),
        allUncompleted: tasks.every(t => t.completed === false)
    };
    """
    res = run_meeting_js(script)
    assert res["taskCount"] == 4
    assert res["allUncompleted"] is True
    assert "Asignat către: Radu" in res["assignees"]
    assert "Asignat către: Ioana" in res["assignees"]
    assert "Asignat către: Mihai" in res["assignees"]
    assert "Asignat către: Andrei" in res["assignees"]


def test_client_api_empty_transcript_rejection():
    """Verify client summarizeMeeting in api.js rejects empty input without making network request."""
    api_js = ROOT / "web" / "shared" / "api.js"
    script = f"""
    import {{ summarizeMeeting }} from "{api_js.as_posix()}";
    const res1 = await summarizeMeeting("");
    const res2 = await summarizeMeeting("   \\t\\n  ");
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
async def test_api_meeting_summarize_boundary_limits():
    """Attack input boundary limits on POST /api/meeting/summarize: empty and over 12000 chars."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Empty string
        res_empty = await client.post("/api/meeting/summarize", json={"transcript": ""})
        assert res_empty.status_code == 400
        assert res_empty.json()["error"]["code"] == "empty_input"

        # Over 12000 characters
        too_long_text = "Discutie sedinta... " * 800
        assert len(too_long_text) > 12000
        res_long = await client.post("/api/meeting/summarize", json={"transcript": too_long_text})
        assert res_long.status_code == 400
        assert res_long.json()["error"]["code"] == "too_long"

