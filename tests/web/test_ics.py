"""Tests for web/shared/ics.js RFC 5545 compliance (owner: p2)."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ICS_JS = ROOT / "web" / "shared" / "ics.js"


def run_ics_js(tasks: list[dict], options: dict = None) -> str:
    """Helper to run generateIcs from Node.js preserving RFC CRLF line endings."""
    script = f"""
    import {{ generateIcs }} from "{ICS_JS.as_posix()}";
    const tasks = {json.dumps(tasks)};
    const options = {json.dumps(options or {})};
    const output = generateIcs(tasks, options);
    process.stdout.write(output);
    """
    res = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        check=True
    )
    # decode without universal newline translation
    return res.stdout.decode("utf-8")


def test_ics_empty_tasks():
    output = run_ics_js([])
    assert output.startswith("BEGIN:VCALENDAR\r\n")
    assert output.endswith("END:VCALENDAR\r\n")
    assert "VERSION:2.0\r\n" in output
    assert "PRODID:-//PrimaZi//Planificator Accesibil RO//RO\r\n" in output
    assert "BEGIN:VEVENT" not in output


def test_ics_valid_task_structure():
    tasks = [
        {
            "id": "t1",
            "title": "Completează formularul F-12",
            "due_iso": "2026-10-28",
            "due_text": "miercuri, 28 octombrie",
            "needs_confirmation": False,
            "priority": "high",
            "steps": ["Pas 1", "Pas 2"],
            "source_quote": "Până miercuri formularul F-12"
        }
    ]
    output = run_ics_js(tasks)

    # Basic RFC 5545 requirements
    assert "BEGIN:VCALENDAR\r\n" in output
    assert "END:VCALENDAR\r\n" in output
    assert "BEGIN:VEVENT\r\n" in output
    assert "END:VEVENT\r\n" in output
    assert "UID:primazi-t1@primazi.ro\r\n" in output
    assert "SUMMARY:Completează formularul F-12\r\n" in output
    assert "DTSTART;VALUE=DATE:20261028\r\n" in output
    assert "DTEND;VALUE=DATE:20261028\r\n" in output
    assert "STATUS:CONFIRMED\r\n" in output
    # Description contains steps and source quote
    assert "Pas 1" in output
    assert "Pas 2" in output
    assert "Extras din document" in output


def test_ics_unconfirmed_deadline_flag():
    tasks = [
        {
            "id": "t2",
            "title": "Trimite raport",
            "due_iso": None,
            "due_text": "cât mai repede",
            "needs_confirmation": True,
            "priority": "normal",
            "steps": []
        }
    ]
    output = run_ics_js(tasks)
    assert "SUMMARY:[De confirmat] Trimite raport\r\n" in output
    assert "necesită confirmare" in output


def test_ics_escaping_special_characters():
    tasks = [
        {
            "id": "t3",
            "title": "Task, with comma; and semicolon & newline\nSecond line",
            "due_iso": "2026-11-01",
            "needs_confirmation": False
        }
    ]
    output = run_ics_js(tasks)
    # Check that comma, semicolon and newline are properly escaped
    assert "Task\\, with comma\\; and semicolon & newline\\nSecond line" in output
