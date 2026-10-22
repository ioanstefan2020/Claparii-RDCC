"""Automated Regression Suite for Limpede Rebrand, Onboarding, i18n & Home Search (owner: p2).

Validates:
- All served HTML routes feature 'Limpede' in <title> and brand badges
- Water drop SVG icon with d='M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z'
- First-visit onboarding redirection script in web/index.html
- Wizard user name input (#wizard-user-name) and label pairing in web/welcome.html
- Execution of Node.js i18n test suite (tests/web/test_i18n.mjs)
- Execution of Node.js preferences test suite (tests/web/prefs/test_prefs.mjs)
- Dynamic user profile name & single-letter avatar binding in shell.js
- Canonical planner task schema persistence into primazi_planner_tasks and wp.planner.tasks
- Mode switching and Enter key handling in web/js/home.js
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from fastapi.testclient import TestClient
import pytest

from app.main import app

ROOT = Path(__file__).resolve().parent.parent.parent
WEB_DIR = ROOT / "web"

SERVED_ROUTES = [
    "/",
    "/index.html",
    "/welcome.html",
    "/settings.html",
    "/library.html",
    "/audio.html",
    "/employee/clarify.html",
    "/employee/plan.html",
    "/employee/meeting.html",
    "/employee/adjustments.html",
    "/employee/profile.html",
    "/employer/index.html",
]


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_rebrand_titles_and_brand_elements(client: TestClient) -> None:
    """Verifies that all served HTML routes feature 'Limpede' in title and sidebar brand."""
    for route in SERVED_ROUTES:
        res = client.get(route)
        assert res.status_code == 200, f"Route {route} returned HTTP {res.status_code}"
        html = res.text

        # 1. Title verification
        title_match = re.search(r"<title>(.*?)</title>", html, re.I | re.DOTALL)
        assert title_match is not None, f"Route {route} missing <title>"
        title_text = title_match.group(1).strip()
        assert title_text.startswith("Limpede"), f"Route {route} <title> should start with 'Limpede', got: '{title_text}'"
        assert "PrimaZi" in title_text, f"Route {route} <title> must retain '(PrimaZi)' for backward compatibility"

        # 2. Sidebar brand text verification
        assert "Limpede" in html, f"Route {route} missing brand text 'Limpede'"


def test_water_drop_svg_badge_present_on_all_routes(client: TestClient) -> None:
    """Verifies the water drop SVG icon with exact path is present on all routes."""
    water_drop_path = 'd="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"'
    for route in SERVED_ROUTES:
        res = client.get(route)
        assert res.status_code == 200
        assert water_drop_path in res.text, (
            f"Route {route} missing water drop SVG icon with path {water_drop_path}"
        )


def test_first_visit_onboarding_redirection_script() -> None:
    """Verifies that index.html contains inline script checking wp.prefs.v1, primazi.settings.v2, limpede.welcome.completed."""
    index_html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    assert "wp.prefs.v1" in index_html
    assert "primazi.settings.v2" in index_html
    assert "limpede.welcome.completed" in index_html
    assert "window.location.replace('/welcome.html')" in index_html
    assert "nowelcome" in index_html


def test_welcome_wizard_user_name_input_and_label() -> None:
    """Verifies that web/welcome.html contains #wizard-user-name input paired with <label for='wizard-user-name'>."""
    welcome_html = (WEB_DIR / "welcome.html").read_text(encoding="utf-8")
    assert 'id="wizard-user-name"' in welcome_html
    assert 'for="wizard-user-name"' in welcome_html


def test_node_i18n_test_suite_passes() -> None:
    """Runs tests/web/test_i18n.mjs via Node.js test runner."""
    script_path = ROOT / "tests" / "web" / "test_i18n.mjs"
    assert script_path.exists(), f"Missing i18n test script: {script_path}"
    res = subprocess.run(
        ["node", "--test", str(script_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        f"Node i18n test suite failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    )
    assert "fail 0" in res.stdout


def test_node_prefs_engine_test_suite_passes() -> None:
    """Runs tests/web/prefs/test_prefs.mjs via Node.js test runner."""
    script_path = ROOT / "tests" / "web" / "prefs" / "test_prefs.mjs"
    assert script_path.exists(), f"Missing prefs test script: {script_path}"
    res = subprocess.run(
        ["node", "--test", str(script_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        f"Node preferences test suite failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    )
    assert "fail 0" in res.stdout


def test_shell_user_display_logic_via_node() -> None:
    """Evaluates updateUserDisplay logic in Node.js across RO, EN, and custom names."""
    shell_js_path = WEB_DIR / "js" / "shell.js"
    assert shell_js_path.exists()

    js_code = f"""
    import {{ updateUserDisplay }} from "{shell_js_path.as_posix()}";

    // Mock DOM and localStorage
    const store = new Map();
    globalThis.localStorage = {{
      getItem: (k) => store.get(k) || null,
      setItem: (k, v) => store.set(k, String(v)),
    }};

    let nameText = "";
    let avatarText = "";
    globalThis.document = {{
      documentElement: {{ lang: "ro" }},
      querySelectorAll: (sel) => {{
        if (sel === ".user-name") return [{{ set textContent(v) {{ nameText = v; }} }}];
        if (sel === ".user-avatar-circle") return [{{ set textContent(v) {{ avatarText = v; }} }}];
        return [];
      }}
    }};

    // Case 1: Default Romanian
    updateUserDisplay();
    if (nameText !== "Utilizator Limpede" || avatarText !== "L") {{
      throw new Error("Default RO mismatch: " + nameText + ", " + avatarText);
    }}

    // Case 2: Default English
    document.documentElement.lang = "en";
    updateUserDisplay();
    if (nameText !== "Limpede User" || avatarText !== "L") {{
      throw new Error("Default EN mismatch: " + nameText + ", " + avatarText);
    }}

    // Case 3: Custom user name "Ana Popescu"
    localStorage.setItem("limpede_user_name", "Ana Popescu");
    updateUserDisplay();
    if (nameText !== "Ana Popescu" || avatarText !== "A") {{
      throw new Error("Custom name mismatch: " + nameText + ", " + avatarText);
    }}

    // Case 4: Lowercase and leading whitespace "  david"
    localStorage.setItem("limpede_user_name", "  david");
    updateUserDisplay();
    if (nameText !== "david" || avatarText !== "D") {{
      throw new Error("Initial uppercase mismatch: " + nameText + ", " + avatarText);
    }}

    process.stdout.write(JSON.stringify({{ ok: true }}));
    """

    res = subprocess.run(
        ["node", "--input-type=module", "-e", js_code],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Node updateUserDisplay test failed:\n{res.stderr}"
    data = json.loads(res.stdout)
    assert data["ok"] is True


def test_actions_send_tasks_to_planner_canonical_schema_via_node() -> None:
    """Verifies that sendTasksToPlanner writes canonical schema into both storage keys."""
    actions_js_path = WEB_DIR / "js" / "actions.js"
    assert actions_js_path.exists()

    js_code = f"""
    import {{ sendTasksToPlanner }} from "{actions_js_path.as_posix()}";

    const store = new Map();
    globalThis.localStorage = {{
      getItem: (k) => store.get(k) || null,
      setItem: (k, v) => store.set(k, String(v)),
    }};

    const sampleTasks = [
      {{
        title: "Test Task 1",
        due_iso: "2026-10-28",
        due_text: "28 octombrie",
        priority: "high",
        steps: ["Step 1", "Step 2"],
        source_quote: "Quote from source",
        needs_confirmation: false,
        completed: false
      }},
      {{
        task: "Meeting Task 2",
        due_text: "vineri",
        needs_confirmation: true,
        who: "Radu"
      }}
    ];

    const result = sendTasksToPlanner(sampleTasks);
    if (!result) throw new Error("sendTasksToPlanner returned false");

    const rawPrimazi = localStorage.getItem("primazi_planner_tasks");
    const rawWp = localStorage.getItem("wp.planner.tasks");
    if (!rawPrimazi || !rawWp) throw new Error("Missing dual storage keys");
    if (rawPrimazi !== rawWp) throw new Error("Dual keys differ");

    const tasks = JSON.parse(rawPrimazi);
    if (tasks.length !== 2) throw new Error("Expected 2 tasks, got " + tasks.length);

    const requiredKeys = ["id", "title", "due_iso", "due_text", "needs_confirmation", "priority", "steps", "source_quote", "completed"];
    for (const t of tasks) {{
      for (const k of requiredKeys) {{
        if (!(k in t)) throw new Error("Task missing canonical key: " + k);
      }}
    }}

    process.stdout.write(JSON.stringify({{ ok: true, taskCount: tasks.length }}));
    """

    res = subprocess.run(
        ["node", "--input-type=module", "-e", js_code],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Node sendTasksToPlanner test failed:\n{res.stderr}"
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["taskCount"] == 2


def test_welcome_js_syntax_integrity() -> None:
    """Verifies that web/js/welcome.js has valid syntax and no dangling brackets."""
    welcome_js = WEB_DIR / "js" / "welcome.js"
    assert welcome_js.exists()
    res = subprocess.run(["node", "-c", str(welcome_js)], capture_output=True, text=True)
    assert res.returncode == 0, f"welcome.js syntax error:\n{res.stderr}"


def test_home_search_actions_key_and_modes() -> None:
    """Verifies that home.js wires Enter submit, Shift+Enter newline, and execute button."""
    home_js = (WEB_DIR / "js" / "home.js").read_text(encoding="utf-8")
    assert 'e.key === "Enter" && !e.shiftKey' in home_js
    assert "btn-home-execute" in home_js
    assert "executeCurrentTask" in home_js
    assert "setMode" in home_js
    assert "btn-home-ics" in home_js


def test_shell_hero_greeting_personalization() -> None:
    """Verifies that shell.js personalizes hero greetings when user name is provided."""
    shell_js_path = WEB_DIR / "js" / "shell.js"
    assert shell_js_path.exists()

    js_code = f"""
    import {{ updateUserDisplay }} from "{shell_js_path.as_posix()}";

    const store = new Map();
    globalThis.localStorage = {{
      getItem: (k) => store.get(k) || null,
      setItem: (k, v) => store.set(k, String(v)),
    }};

    let greetingText = "";
    globalThis.document = {{
      documentElement: {{ lang: "ro" }},
      querySelectorAll: (sel) => {{
        if (sel === ".user-name") return [{{ set textContent(v) {{}} }}];
        if (sel === ".user-avatar-circle") return [{{ set textContent(v) {{}} }}];
        if (sel === ".gemini-greeting") return [{{ set textContent(v) {{ greetingText = v; }} }}];
        return [];
      }}
    }};

    // Case 1: Anonymous
    updateUserDisplay();
    if (greetingText !== "De unde să începem?") throw new Error("Anonymous greeting mismatch: " + greetingText);

    // Case 2: Personalized Romanian
    localStorage.setItem("limpede_user_name", "Elena");
    updateUserDisplay();
    if (greetingText !== "Bună, Elena! De unde să începem?") throw new Error("Personalized RO greeting mismatch: " + greetingText);

    // Case 3: Personalized English
    document.documentElement.lang = "en";
    updateUserDisplay();
    if (greetingText !== "Hello, Elena! Where should we start?") throw new Error("Personalized EN greeting mismatch: " + greetingText);

    process.stdout.write(JSON.stringify({{ ok: true }}));
    """

    res = subprocess.run(
        ["node", "--input-type=module", "-e", js_code],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Node greeting test failed:\n{res.stderr}"
    data = json.loads(res.stdout)
    assert data["ok"] is True


