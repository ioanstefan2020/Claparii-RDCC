"""Tests for web/employee/plan.html and web/employee/plan.js (owner: p2)."""
import json
import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_a11y_static import audit_html

ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_JS = ROOT / "web" / "employee" / "plan.js"
PLAN_HTML = ROOT / "web" / "employee" / "plan.html"
ICS_JS = ROOT / "web" / "shared" / "ics.js"


def run_plan_js(expression: str) -> dict:
    """Helper to evaluate JS expressions on plan.js using Node.js."""
    script = f"""
    import * as planMod from "{PLAN_JS.as_posix()}";
    import * as icsMod from "{ICS_JS.as_posix()}";
    const {{ generateIcs, escapeIcsText, formatIcsDate, downloadIcsFile }} = icsMod;
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


def test_plan_html_passes_static_a11y_audit():
    """Verify that plan.html passes static WCAG 2.2 AA audit."""
    assert PLAN_HTML.exists(), "web/employee/plan.html must exist"
    html_text = PLAN_HTML.read_text(encoding="utf-8")
    problems = audit_html(html_text)
    assert not problems, f"Static a11y audit failed for plan.html: {problems}"


def test_plan_html_landmarks_and_controls():
    """Verify essential landmarks, single h1, skip link, live region, and form controls."""
    assert PLAN_HTML.exists(), "web/employee/plan.html must exist"
    html_text = PLAN_HTML.read_text(encoding="utf-8")

    # Landmarks & Accessibility essentials
    assert '<a href="#main" class="skip-link">Sari la conținutul principal</a>' in html_text
    assert '<main id="main">' in html_text
    assert 'aria-live="polite"' in html_text
    assert html_text.count("<h1") == 1
    assert "Planificator de sarcini și termene limită" in html_text
    assert ('<header role="banner">' in html_text or '<header class="app-topbar" role="banner">' in html_text)
    assert ('<footer role="contentinfo">' in html_text or '<footer class="app-footer" role="contentinfo">' in html_text)

    # Navigation current page check
    assert 'href="/employee/plan.html" aria-current="page"' in html_text

    # Extraction input form & buttons
    assert 'id="plan-text"' in html_text
    assert 'for="plan-text"' in html_text
    assert 'id="btn-load-sample"' in html_text
    assert 'id="btn-extract-plan"' in html_text

    # Status & error banners
    assert 'id="error-banner"' in html_text
    assert 'id="status-live"' in html_text
    assert 'id="ai-notice"' in html_text
    assert 'id="warnings-container"' in html_text

    # Tasks section & toolbar controls
    assert 'id="tasks-section"' in html_text
    assert 'id="tasks-list"' in html_text
    assert 'id="btn-export-ics"' in html_text
    assert 'id="btn-clear-tasks"' in html_text
    assert 'id="btn-toggle-add"' in html_text

    # Manual add task form
    assert 'id="form-add-task"' in html_text
    assert 'id="new-task-title"' in html_text
    assert 'for="new-task-title"' in html_text
    assert 'id="new-task-due"' in html_text
    assert 'for="new-task-due"' in html_text
    assert 'id="new-task-priority"' in html_text
    assert 'for="new-task-priority"' in html_text
    assert 'id="btn-save-new-task"' in html_text
    assert 'id="btn-cancel-add-task"' in html_text


def test_plan_js_sample_task_email():
    """Verify SAMPLE_TASK_EMAIL is exported and contains realistic Romanian workplace task email."""
    sample = run_plan_js("return planMod.SAMPLE_TASK_EMAIL;")
    assert isinstance(sample, str)
    assert len(sample) > 100
    assert "Raport lunar clienți" in sample
    assert "CRM" in sample
    assert "până joi la prânz" in sample
    assert "Andrei" in sample


def test_plan_js_task_mutations():
    """Verify addTask, updateTask, toggleTaskCompletion, deleteTask pure mutation functions."""
    script = """
    let tasks = [];
    tasks = planMod.addTask(tasks, {
        title: "Test Task 1",
        due_iso: "2026-10-30",
        due_text: "vineri",
        needs_confirmation: false,
        priority: "high",
        steps: ["Pas 1", "Pas 2"],
        source_quote: "vineri să fie gata"
    });
    const t1Id = tasks[0].id;
    const initialCompleted = tasks[0].completed;

    tasks = planMod.toggleTaskCompletion(tasks, t1Id);
    const toggledCompleted = tasks[0].completed;

    tasks = planMod.updateTask(tasks, t1Id, { priority: "low", title: "Updated Task 1" });
    const updatedTitle = tasks[0].title;
    const updatedPriority = tasks[0].priority;

    tasks = planMod.deleteTask(tasks, t1Id);
    const finalLength = tasks.length;

    return { t1Id, initialCompleted, toggledCompleted, updatedTitle, updatedPriority, finalLength };
    """
    res = run_plan_js(script)
    assert bool(res["t1Id"]) is True
    assert res["initialCompleted"] is False
    assert res["toggledCompleted"] is True
    assert res["updatedTitle"] == "Updated Task 1"
    assert res["updatedPriority"] == "low"
    assert res["finalLength"] == 0


def test_plan_js_ambiguous_deadline_and_confirmation():
    """Verify that ambiguous deadlines require confirmation and confirmTaskDate resolves them."""
    script = """
    let tasks = [];
    tasks = planMod.addTask(tasks, {
        title: "Raport lunar clienți",
        due_iso: null,
        due_text: "cât mai repede, până joi la prânz",
        needs_confirmation: true,
        priority: "high"
    });
    const unconfirmed = tasks[0];

    // Confirm date manually
    tasks = planMod.confirmTaskDate(tasks, unconfirmed.id, "2026-10-29");
    const confirmed = tasks[0];

    return {
        initialDueIso: unconfirmed.due_iso,
        initialNeedsConf: unconfirmed.needs_confirmation,
        confirmedDueIso: confirmed.due_iso,
        confirmedNeedsConf: confirmed.needs_confirmation
    };
    """
    res = run_plan_js(script)
    assert res["initialDueIso"] is None
    assert res["initialNeedsConf"] is True
    assert res["confirmedDueIso"] == "2026-10-29"
    assert res["confirmedNeedsConf"] is False


def test_plan_js_storage_helpers():
    """Verify loadStoredTasks, saveStoredTasks, and clearStoredTasks with localStorage mock."""
    script = """
    const storage = {};
    globalThis.localStorage = {
        getItem: (k) => storage[k] || null,
        setItem: (k, v) => { storage[k] = String(v); },
        removeItem: (k) => { delete storage[k]; }
    };

    const initial = planMod.loadStoredTasks();
    const sample = [{ id: "t1", title: "Sarcină salvată", completed: false }];
    planMod.saveStoredTasks(sample);
    const loaded = planMod.loadStoredTasks();
    planMod.clearStoredTasks();
    const afterClear = planMod.loadStoredTasks();

    return { initial, loaded, afterClear };
    """
    res = run_plan_js(script)
    assert res["initial"] == []
    assert len(res["loaded"]) == 1
    assert res["loaded"][0]["title"] == "Sarcină salvată"
    assert res["afterClear"] == []


def test_plan_ics_export_generation():
    """Verify RFC 5545 ICS generation for confirmed vs unconfirmed planner tasks."""
    ics_js = ROOT / "web" / "shared" / "ics.js"
    script = f"""
    import {{ generateIcs }} from "{ics_js.as_posix()}";

    const tasks = [
        {{
            id: "t1",
            title: "Trimite raportul financiar",
            due_iso: "2026-10-28",
            due_text: "miercuri, 28 octombrie",
            needs_confirmation: false,
            steps: ["Deschide CRM", "Exportă xlsx"],
            source_quote: "Până pe 28 octombrie"
        }},
        {{
            id: "t2",
            title: "Verifică formulare",
            due_iso: null,
            due_text: "cât mai repede",
            needs_confirmation: true,
            steps: [],
            source_quote: "cât mai repede"
        }}
    ];

    const ics = generateIcs(tasks);
    process.stdout.write(JSON.stringify({{ ics }}));
    """
    res = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        check=True,
    )
    data = json.loads(res.stdout.decode("utf-8"))
    ics_str = data["ics"]

    # Check RFC 5545 structural requirements
    assert "BEGIN:VCALENDAR" in ics_str
    assert "END:VCALENDAR" in ics_str
    assert "\r\n" in ics_str
    assert "SUMMARY:Trimite raportul financiar" in ics_str
    assert "DTSTART;VALUE=DATE:20261028" in ics_str

    # Unconfirmed task must have [De confirmat] in summary
    assert "SUMMARY:[De confirmat] Verifică formulare" in ics_str
    assert '[NOTĂ]: Termen estimat în text: "cât mai repede" (necesită confirmare)' in ics_str


@pytest.mark.anyio
async def test_live_http_serving_plan_html():
    """Live HTTP serving test via ASGI: verify GET /employee/plan.html returns 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/employee/plan.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        html = response.text
        assert html.count("<h1") == 1
        assert '<a href="#main" class="skip-link">' in html
        assert '<main id="main">' in html
        assert 'id="plan-text"' in html
        assert 'id="btn-extract-plan"' in html
        assert 'id="tasks-section"' in html

        problems = audit_html(html)
        assert not problems, f"Static a11y audit failed on served page: {problems}"


@pytest.mark.anyio
async def test_live_asgi_plan_extract_endpoint_contract():
    """Verify POST /api/plan/extract returns valid schema and conforms to CONTRACTS §2."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sample_path = ROOT / "data" / "samples" / "task_email_ro.txt"
        sample_text = sample_path.read_text(encoding="utf-8")

        payload = {
            "text": sample_text,
            "today_iso": "2026-10-22",
            "profile": {
                "reading_level": "simple",
                "format": "steps",
                "needs_notes": "Sarcini clare și termene limită",
                "max_sentence_words": 12,
            },
        }
        response = await client.post("/api/plan/extract", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        tasks = body["data"]["tasks"]
        assert isinstance(tasks, list)
        assert len(tasks) > 0

        # Verify task items structure
        for t in tasks:
            assert "id" in t
            assert "title" in t
            assert "due_text" in t
            assert "needs_confirmation" in t
            assert "priority" in t
            assert t["priority"] in ["high", "normal", "low"]
            assert "steps" in t
            assert "source_quote" in t

        # Verify at least one task requires confirmation due to vague deadline
        has_unconfirmed = any(t["needs_confirmation"] for t in tasks)
        assert has_unconfirmed, "Expected at least one task with ambiguous deadline requiring confirmation"
def test_plan_js_format_date_ro():
    """Verify formatDateRo formats ISO dates into Romanian localized weekday and month."""
    script = """
    return {
        d1: planMod.formatDateRo("2026-10-28"),
        d2: planMod.formatDateRo("2026-10-29"),
        empty: planMod.formatDateRo(""),
        nullish: planMod.formatDateRo(null)
    };
    """
    res = run_plan_js(script)
    assert "2026-10-28" in res["d1"]
    assert "miercuri" in res["d1"]
    assert "octombrie" in res["d1"]
    assert "joi" in res["d2"]
    assert res["empty"] == ""
    assert res["nullish"] == ""


def test_plan_js_escape_html():
    """Verify escapeHtml sanitizes script tags, quotes, and ampersands."""
    script = """
    const dirty = '<script>alert("xss & fun")</script>';
    return { clean: planMod.escapeHtml(dirty) };
    """
    res = run_plan_js(script)
    assert "<script>" not in res["clean"]
    assert "&lt;script&gt;" in res["clean"]
    assert "&quot;xss &amp; fun&quot;" in res["clean"]


def test_plan_js_add_task_defaults():
    """Verify addTask generates unique id, defaults completed to false, normalizes priority."""
    script = """
    let tasks = [];
    tasks = planMod.addTask(tasks, {
        title: "Test Task",
        priority: "invalid_prio"
    });
    const t = tasks[0];
    return {
        id: t.id,
        hasId: typeof t.id === "string" && t.id.length > 0,
        completed: t.completed,
        priority: t.priority,
        steps: t.steps,
        needs_confirmation: t.needs_confirmation
    };
    """
    res = run_plan_js(script)
    assert res["hasId"] is True
    assert res["completed"] is False
    assert res["priority"] == "normal"
    assert res["steps"] == []
    assert res["needs_confirmation"] is False


def test_client_api_plan_extract_empty_rejection():
    """Verify client extractPlan API in api.js rejects empty input without making network request."""
    api_js = ROOT / "web" / "shared" / "api.js"
    script = f"""
    import {{ extractPlan }} from "{api_js.as_posix()}";
    const res1 = await extractPlan("");
    const res2 = await extractPlan("   \\t\\n  ");
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



def test_plan_storage_corrupt_data_resilience():
    """Attack localStorage handling with corrupt JSON, primitives, and missing storage."""
    script = """
    const storage = {};
    globalThis.localStorage = {
        getItem: (k) => storage[k] !== undefined ? storage[k] : null,
        setItem: (k, v) => { storage[k] = String(v); },
        removeItem: (k) => { delete storage[k]; }
    };

    // 1. Corrupt JSON string
    storage[planMod.STORAGE_KEY] = "{malformed json syntax...";
    const resCorrupt = planMod.loadStoredTasks();

    // 2. Non-array JSON objects/primitives
    storage[planMod.STORAGE_KEY] = JSON.stringify({ not: "an array" });
    const resObj = planMod.loadStoredTasks();

    storage[planMod.STORAGE_KEY] = "12345";
    const resNum = planMod.loadStoredTasks();

    storage[planMod.STORAGE_KEY] = "true";
    const resBool = planMod.loadStoredTasks();

    storage[planMod.STORAGE_KEY] = "null";
    const resNull = planMod.loadStoredTasks();

    storage[planMod.STORAGE_KEY] = "";
    const resEmpty = planMod.loadStoredTasks();

    // 3. Storage completely undefined
    delete globalThis.localStorage;
    const resNoStorage = planMod.loadStoredTasks();
    const saveNoStorage = planMod.saveStoredTasks([{ id: "t1", title: "Test" }]);
    planMod.clearStoredTasks();

    return {
        resCorrupt,
        resObj,
        resNum,
        resBool,
        resNull,
        resEmpty,
        resNoStorage,
        saveNoStorage
    };
    """
    res = run_plan_js(script)
    assert res["resCorrupt"] == []
    assert res["resObj"] == []
    assert res["resNum"] == []
    assert res["resBool"] == []
    assert res["resNull"] == []
    assert res["resEmpty"] == []
    assert res["resNoStorage"] == []
    assert len(res["saveNoStorage"]) == 1


def test_plan_xss_injection_and_sanitization():
    """Attack escapeHtml with malicious script tags, attribute escapes, and special characters."""
    script = """
    const xssPayloads = [
        '<script>alert("xss")</script>',
        '<img src="x" onerror="stealCookies()">',
        '<a href="javascript:alert(1)">click</a>',
        '"><script>alert(1)</script>',
        "test ' onfocus='alert(1)'",
        "Raport & Sinteză <2026> \\"Final\\""
    ];

    const escaped = xssPayloads.map(p => planMod.escapeHtml(p));

    // Verify task title with XSS payload is stored safely without mutation
    let tasks = [];
    tasks = planMod.addTask(tasks, {
        title: '<script>alert("XSS")</script>',
        source_quote: '"><img src=x onerror=alert(1)>'
    });

    return {
        escaped,
        storedTitle: tasks[0].title,
        storedQuote: tasks[0].source_quote
    };
    """
    res = run_plan_js(script)
    for esc in res["escaped"]:
        assert "<script>" not in esc
        assert "</script>" not in esc
        assert "<img" not in esc
        assert "<a href" not in esc
        assert '"' not in esc
        assert "'" not in esc

    assert res["storedTitle"] == '<script>alert("XSS")</script>'
    assert res["storedQuote"] == '"><img src=x onerror=alert(1)>'


def test_plan_ics_rfc5545_strict_compliance():
    """Verify strict RFC 5545 syntax: CRLF endings, VCALENDAR/VEVENT headers, UID format, DTSTAMP, character escaping."""
    script = """
    // Test text escaping: backslashes, semicolons, commas, newlines
    const rawText = "Raport: clienți; vânzări, & \\\\ backup\\nLinia 2\\r\\nLinia 3";
    const escapedText = escapeIcsText(rawText);

    const tasks = [
        {
            id: "task-abc-123",
            title: "Planificare & Buget; Q4, 2026",
            due_iso: "2026-11-15",
            due_text: "duminică, 15 noiembrie",
            needs_confirmation: false,
            steps: ["Verifică CRM; baze de date", "Trimite mail, către manager"],
            source_quote: "Până pe 15 noiembrie, fără întârziere."
        }
    ];

    const icsContent = generateIcs(tasks, {
        prodId: "-//PrimaZi//Test Calendar//RO",
        calName: "Calendar Test"
    });

    return {
        escapedText,
        icsContent,
        d1: formatIcsDate("2026-11-15"),
        dEmpty: formatIcsDate("")
    };
    """
    res = run_plan_js(script)
    escaped = res["escapedText"]
    ics = res["icsContent"]

    # Test escaping rules: semicolons, commas, backslashes, newlines
    assert "\\;" in escaped
    assert "\\," in escaped
    assert "\\\\" in escaped
    assert "\\n" in escaped
    assert "\r" not in escaped
    assert "\nLinia 2" not in escaped

    # Strict RFC 5545 assertions
    assert ics.startswith("BEGIN:VCALENDAR\r\n")
    assert ics.endswith("END:VCALENDAR\r\n")

    # Verify every line terminates with CRLF
    raw_lines = ics.split("\r\n")
    assert raw_lines[-1] == ""
    for line in raw_lines[:-1]:
        assert "\n" not in line, f"Line contains lone LF: {line}"
        assert "\r" not in line, f"Line contains lone CR: {line}"

    # Verify structural properties
    assert "VERSION:2.0" in ics
    assert "PRODID:-//PrimaZi//Test Calendar//RO" in ics
    assert "CALSCALE:GREGORIAN" in ics
    assert "METHOD:PUBLISH" in ics
    assert "X-WR-CALNAME:Calendar Test" in ics

    assert "BEGIN:VEVENT" in ics
    assert "UID:primazi-task-abc-123@primazi.ro" in ics
    assert "DTSTART;VALUE=DATE:20261115" in ics
    assert "STATUS:CONFIRMED" in ics
    assert "END:VEVENT" in ics

    import re
    assert re.search(r"DTSTAMP:\d{8}T\d{6}Z", ics) is not None

    # Summary and description with escaped characters
    assert "SUMMARY:Planificare & Buget\\; Q4\\, 2026" in ics
    assert "Verifică CRM\\; baze de date" in ics
    assert "Trimite mail\\, către manager" in ics


def test_plan_ics_unconfirmed_vs_confirmed_lifecycle():
    """Verify ambiguous deadline generates [De confirmat] summary/note, and confirmation updates state and removes tag."""
    script = """
    let tasks = [];
    tasks = planMod.addTask(tasks, {
        id: "t_vague",
        title: "Trimite raportul trimestrial",
        due_iso: null,
        due_text: "cât mai repede, până la sfârșitul săptămânii",
        needs_confirmation: true,
        priority: "high",
        steps: ["Colectează datele"],
        source_quote: "cât mai repede posibil"
    });

    // 1. Export unconfirmed task
    const icsUnconfirmed = generateIcs(tasks);

    // 2. Confirm date
    tasks = planMod.confirmTaskDate(tasks, "t_vague", "2026-11-20");

    // 3. Export confirmed task
    const icsConfirmed = generateIcs(tasks);

    return {
        icsUnconfirmed,
        icsConfirmed,
        confirmedTask: tasks[0]
    };
    """
    res = run_plan_js(script)
    unconf = res["icsUnconfirmed"]
    conf = res["icsConfirmed"]
    t = res["confirmedTask"]

    # State checks after confirmation
    assert t["due_iso"] == "2026-11-20"
    assert t["needs_confirmation"] is False

    # Unconfirmed ICS checks
    assert "SUMMARY:[De confirmat] Trimite raportul trimestrial" in unconf
    assert r'[NOTĂ]: Termen estimat în text: "cât mai repede\, până la sfârșitul săptămânii" (necesită confirmare)' in unconf

    # Confirmed ICS checks
    assert "SUMMARY:Trimite raportul trimestrial" in conf
    assert "[De confirmat]" not in conf
    assert "[NOTĂ]" not in conf
    assert "DTSTART;VALUE=DATE:20261120" in conf
    assert "STATUS:CONFIRMED" in conf


def test_plan_edge_cases_empty_and_null_inputs():
    """Attack addTask, formatDateRo, and generateIcs with empty, null, and boundary values."""
    script = """
    // 1. Task with empty/whitespace title -> default title
    let tasks = [];
    tasks = planMod.addTask(tasks, { title: "   " });
    const defaultTitle = tasks[0].title;

    // 2. Task with invalid priority -> normal
    tasks = planMod.addTask(tasks, { title: "Prio Test", priority: "critical_unknown" });
    const fallbackPrio = tasks[1].priority;

    // 3. Task with null/missing steps -> empty array
    tasks = planMod.addTask(tasks, { title: "Steps Test", steps: null });
    const fallbackSteps = tasks[2].steps;

    // 4. formatDateRo with edge inputs
    const dInvalid = planMod.formatDateRo("invalid-date-string");
    const dPartial = planMod.formatDateRo("2026-10");
    const dEmpty = planMod.formatDateRo("");
    const dNull = planMod.formatDateRo(null);

    // 5. Empty task list export to ICS
    const emptyIcs = generateIcs([]);

    // 6. Task list with null items
    const nullItemsIcs = generateIcs([null, undefined, tasks[0]]);

    return {
        defaultTitle,
        fallbackPrio,
        fallbackSteps,
        dInvalid,
        dPartial,
        dEmpty,
        dNull,
        emptyIcs,
        nullItemsIcs
    };
    """
    res = run_plan_js(script)
    assert res["defaultTitle"] == "Sarcină nouă"
    assert res["fallbackPrio"] == "normal"
    assert res["fallbackSteps"] == []
    assert res["dInvalid"] == "invalid-date-string"
    assert res["dPartial"] == "2026-10"
    assert res["dEmpty"] == ""
    assert res["dNull"] == ""

    assert res["emptyIcs"].startswith("BEGIN:VCALENDAR\r\n")
    assert res["emptyIcs"].endswith("END:VCALENDAR\r\n")
    assert "BEGIN:VEVENT" not in res["emptyIcs"]

    assert "BEGIN:VTODO" in res["nullItemsIcs"]
    assert "SUMMARY:Sarcină nouă" in res["nullItemsIcs"]
    assert "STATUS:NEEDS-ACTION" in res["nullItemsIcs"]


def test_plan_stress_large_input_and_batch_export():
    """Stress test with 10,000 char strings, multiple steps, and batch export of 10 tasks."""
    script = """
    const bigTitle = "Titlu Mare ".repeat(1000);
    const bigQuote = "Extras Document ".repeat(600);
    const steps50 = Array.from({ length: 50 }, (_, i) => `Pasul numarul ${i + 1} de urmat`);

    let tasks = [];
    tasks = planMod.addTask(tasks, {
        title: bigTitle,
        source_quote: bigQuote,
        steps: steps50,
        due_iso: "2026-12-31"
    });

    for (let i = 2; i <= 10; i++) {
        tasks = planMod.addTask(tasks, {
            title: `Sarcină multiplă #${i}`,
            due_iso: i % 2 === 0 ? `2026-11-0${i}` : null,
            needs_confirmation: i % 2 !== 0,
            priority: i % 3 === 0 ? "high" : (i % 3 === 1 ? "low" : "normal")
        });
    }

    const batchIcs = generateIcs(tasks);

    return {
        taskCount: tasks.length,
        hasBigTitle: tasks[0].title.length > 5000,
        stepsCount: tasks[0].steps.length,
        batchIcsLength: batchIcs.length,
        batchIcs
    };
    """
    res = run_plan_js(script)
    assert res["taskCount"] == 10
    assert res["hasBigTitle"] is True
    assert res["stepsCount"] == 50
    assert res["batchIcsLength"] > 1000

    ics = res["batchIcs"]
    # 6 tasks have explicit due_iso (VEVENT), 4 tasks have null due_iso (VTODO)
    assert ics.count("BEGIN:VEVENT") == 6
    assert ics.count("BEGIN:VTODO") == 4
    assert ics.count("END:VEVENT") == 6
    assert ics.count("END:VTODO") == 4
    assert ics.startswith("BEGIN:VCALENDAR\r\n")
    assert ics.endswith("END:VCALENDAR\r\n")


def test_plan_mutations_advanced_integrity():
    """Verify state mutation purity, bidirectional completion toggling, and non-existent id no-ops."""
    script = """
    let tasks = [];
    tasks = planMod.addTask(tasks, { title: "T1", priority: "normal" });
    tasks = planMod.addTask(tasks, { title: "T2", priority: "high" });
    const id1 = tasks[0].id;
    const id2 = tasks[1].id;

    const distinctIds = id1 !== id2;

    // Bidirectional completion toggle
    tasks = planMod.toggleTaskCompletion(tasks, id1);
    const toggledTrue = tasks[0].completed;
    tasks = planMod.toggleTaskCompletion(tasks, id1);
    const toggledFalse = tasks[0].completed;

    // No-op mutations with non-existent ID
    const beforeLen = tasks.length;
    tasks = planMod.deleteTask(tasks, "non_existent_id");
    tasks = planMod.updateTask(tasks, "non_existent_id", { title: "Ghost" });
    tasks = planMod.confirmTaskDate(tasks, "non_existent_id", "2026-12-12");
    tasks = planMod.toggleTaskCompletion(tasks, "non_existent_id");
    const afterLen = tasks.length;

    return {
        distinctIds,
        toggledTrue,
        toggledFalse,
        lenMatches: beforeLen === afterLen
    };
    """
    res = run_plan_js(script)
    assert res["distinctIds"] is True
    assert res["toggledTrue"] is True
    assert res["toggledFalse"] is False
    assert res["lenMatches"] is True


@pytest.mark.anyio
async def test_live_asgi_e2e_plan_extraction_and_ics_pipeline():
    """End-to-end integration test: Extract tasks from sample task email via ASGI,
    confirm ambiguous deadline, and generate valid RFC 5545 ICS calendar export.
    """
    sample_path = ROOT / "data" / "samples" / "task_email_ro.txt"
    assert sample_path.exists(), "Sample task email must exist"
    sample_text = sample_path.read_text(encoding="utf-8")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": sample_text,
            "today_iso": "2026-10-22",
            "profile": {
                "reading_level": "simple",
                "format": "steps",
                "needs_notes": "Sarcini clare și termene limită",
                "max_sentence_words": 12,
            },
        }
        response = await client.post("/api/plan/extract", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        tasks_data = body["data"]["tasks"]
        assert len(tasks_data) >= 1

        script = f"""
        const rawTasks = {json.dumps(tasks_data)};
        let tasks = [];
        for (const t of rawTasks) {{
            tasks = planMod.addTask(tasks, t);
        }}

        const unconfirmed = tasks.find(t => t.needs_confirmation);
        const hadUnconfirmed = Boolean(unconfirmed);
        if (unconfirmed) {{
            tasks = planMod.confirmTaskDate(tasks, unconfirmed.id, "2026-10-29");
        }}

        const icsContent = generateIcs(tasks);

        return {{
            hadUnconfirmed,
            tasksCount: tasks.length,
            allConfirmed: tasks.every(t => !t.needs_confirmation),
            icsContent
        }};
        """
        res = run_plan_js(script)
        assert res["hadUnconfirmed"] is True
        assert res["allConfirmed"] is True
        assert res["tasksCount"] >= 1

        ics = res["icsContent"]
        assert ics.startswith("BEGIN:VCALENDAR\r\n")
        assert ics.endswith("END:VCALENDAR\r\n")
        assert "BEGIN:VEVENT" in ics
        assert "STATUS:CONFIRMED" in ics
        assert "[De confirmat]" not in ics
        assert "DTSTART;VALUE=DATE:20261029" in ics
