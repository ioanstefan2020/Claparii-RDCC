"""Tests for web/shared/fixtures/ and i18n JSON conformity (owner: p2)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = ROOT / "web" / "shared" / "fixtures"
I18N_FILE = ROOT / "web" / "i18n" / "ro.employee.json"

REQUIRED_ADJUSTMENT_IDS = {
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
}


def test_simplify_fixture():
    f = FIXTURES_DIR / "simplify.json"
    assert f.exists()
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["provider"] == "mock"
    assert "ai_notice_ro" in data["meta"]

    d = data["data"]
    assert "summary" in d and isinstance(d["summary"], str)
    assert "steps" in d and len(d["steps"]) > 0
    assert "key_terms" in d
    assert "questions_to_ask" in d
    for step in d["steps"]:
        assert "n" in step and "text" in step and "source_quote" in step


def test_plan_extract_fixture():
    f = FIXTURES_DIR / "plan_extract.json"
    assert f.exists()
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert "tasks" in data["data"]

    tasks = data["data"]["tasks"]
    assert len(tasks) >= 2
    # At least one with confirmed date and one unconfirmed
    has_confirmed = any(t["due_iso"] is not None and not t["needs_confirmation"] for t in tasks)
    has_unconfirmed = any(t["due_iso"] is None and t["needs_confirmation"] for t in tasks)
    assert has_confirmed, "plan_extract fixture should have a task with confirmed due_iso"
    assert has_unconfirmed, "plan_extract fixture should have a task with needs_confirmation=True"


def test_meeting_summarize_fixture():
    f = FIXTURES_DIR / "meeting_summarize.json"
    assert f.exists()
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["ok"] is True
    d = data["data"]
    assert "summary" in d
    assert "decisions" in d
    assert "action_items" in d
    assert "unclear_points" in d
    assert any("who" in item for item in d["action_items"])


def test_adjustments_catalog_fixture():
    f = FIXTURES_DIR / "adjustments_catalog.json"
    assert f.exists()
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["ok"] is True
    d = data["data"]
    assert "disclaimer_ro" in d
    items = d["items"]
    catalog_ids = {it["id"] for it in items}
    missing = REQUIRED_ADJUSTMENT_IDS - catalog_ids
    assert not missing, f"Missing required adjustment IDs in fixture: {missing}"

    # Verify no diagnosis fields exist
    for it in items:
        assert "diagnosis" not in it
        assert "medical" not in it
        assert "applies_to" in it
        assert "example_request" in it


def test_adjustments_draft_fixture():
    f = FIXTURES_DIR / "adjustments_draft.json"
    assert f.exists()
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["ok"] is True
    d = data["data"]
    assert "subject" in d
    assert "body_ro" in d
    assert "checklist" in d


def test_i18n_ro_employee():
    assert I18N_FILE.exists()
    content = I18N_FILE.read_text(encoding="utf-8")
    data = json.loads(content)
    assert "app_name" in data
    assert "a11y_toolbar" in data
    assert "profile" in data
    # Check diacritics presence in Romanian strings
    assert any(c in content for c in ["ă", "â", "î", "ș", "ț"])
