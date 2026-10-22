import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_profile_recommendations_empty_input():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/profile/recommend-adaptations", json={"user_words": "   "}
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "empty_input"


@pytest.mark.anyio
async def test_profile_recommendations_heuristics_offline(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/profile/recommend-adaptations",
            json={
                "user_words": (
                    "Mă distrage zgomotul din birou și am nevoie de căști sau liniște. "
                    "Văd greu literele mici, am nevoie de font mare și instrucțiuni scrise pas cu pas."
                )
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]

        # UI prefs assertions
        assert data["ui_prefs"]["textSize"] in ("large", "extra-large")
        assert data["ui_prefs"]["format"] == "steps"

        # Workplace adjustments assertions
        ids = [adj["id"] for adj in data["recommended_adjustments"]]
        assert "quiet_space" in ids
        assert "written_instructions" in ids
        assert "disclaimer_ro" in data


@pytest.mark.anyio
async def test_profile_recommendations_strips_clinical_terms(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/profile/recommend-adaptations",
            json={
                "user_words": "Am fost diagnosticat cu autism și adhd, mă simt copleșit de aglomerație."
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]

        # Ensure clinical disease words do not appear in output summary or reasons
        forbidden = ["autism", "adhd", "diagnosticat"]
        summary_low = data["summary_ro"].lower()
        for f in forbidden:
            assert f not in summary_low
        for adj in data["recommended_adjustments"]:
            assert f not in adj["relevance_reason_ro"].lower()


@pytest.mark.anyio
async def test_plan_calendar_link_timed_event():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/plan/calendar-link",
            json={
                "title": "Ședință onboarding IT",
                "date_iso": "2026-10-27",
                "time_start": "10:30",
                "duration_minutes": 45,
                "details": "Preluare echipamente și conturi de acces",
                "location": "Sediul Central, sala 301",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]

        # Verify Google Calendar URL
        gcal = data["google_calendar_url"]
        assert "calendar.google.com/calendar/render" in gcal
        assert "20261027T103000" in gcal
        assert "20261027T111500" in gcal

        # Verify iCal RFC 5545 format
        ics = data["ics_content"]
        assert "BEGIN:VCALENDAR" in ics
        assert "BEGIN:VEVENT" in ics
        assert "DTSTART:20261027T103000" in ics
        assert "DTEND:20261027T111500" in ics
        assert "SUMMARY:Ședință onboarding IT" in ics
        assert "TRIGGER:-PT60M" in ics
        assert "END:VCALENDAR" in ics


@pytest.mark.anyio
async def test_plan_calendar_link_all_day_event():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/plan/calendar-link",
            json={
                "title": "Termen limită depunere dosar",
                "date_iso": "2026-10-30",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]

        gcal = data["google_calendar_url"]
        assert "20261030" in gcal
        ics = data["ics_content"]
        assert "DTSTART;VALUE=DATE:20261030" in ics
        assert "END:VCALENDAR" in ics
