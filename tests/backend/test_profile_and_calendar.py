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


@pytest.mark.anyio
async def test_recommend_adaptations_wave2_schema(monkeypatch):
    """Verifies settings, reasons, adaptations presence and types per docs/CONTRACTS-WAVE2.md."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/profile/recommend-adaptations",
            json={"needs_notes": "Am nevoie de ecran cald și instrucțiuni scrise clar."},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]

        # Wave 2 fields
        assert "settings" in data
        assert isinstance(data["settings"], dict)
        assert "theme" in data["settings"]
        assert "font_scale" in data["settings"]
        assert "format" in data["settings"]

        assert "reasons" in data
        assert isinstance(data["reasons"], list)
        assert len(data["reasons"]) > 0
        for item in data["reasons"]:
            assert "key" in item
            assert "reason_ro" in item

        assert "adaptations" in data
        assert isinstance(data["adaptations"], list)
        assert len(data["adaptations"]) > 0
        assert all(isinstance(a, str) for a in data["adaptations"])

        # Backwards-compatible fields
        assert "ui_prefs" in data
        assert "recommended_adjustments" in data
        assert "summary_ro" in data
        assert "disclaimer_ro" in data


@pytest.mark.anyio
async def test_recommend_adaptations_acceptance_scenario(monkeypatch):
    """Acceptance test: 'obosesc la lumină tare și uit instrucțiunile verbale' ->
    warm theme/dim, steps format, written-instructions adaptation, with reasons.
    """
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/profile/recommend-adaptations",
            json={"needs_notes": "obosesc la lumină tare și uit instrucțiunile verbale"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]

        # Warm theme / dim
        assert data["settings"]["theme"] in ("amber", "soft")
        assert data["settings"]["dim_overlay"] > 0

        # Steps format
        assert data["settings"]["format"] == "steps"

        # Written instructions adaptation
        assert "written_instructions" in data["adaptations"]

        # Reasons present
        reasons_keys = [r["key"] for r in data["reasons"]]
        assert "theme" in reasons_keys or "dim_overlay" in reasons_keys
        assert "format" in reasons_keys


@pytest.mark.anyio
async def test_recommend_adaptations_chips_input(monkeypatch):
    """Verifies request with chips=['text_mare', 'pasi_scurti'] without user_words."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/profile/recommend-adaptations",
            json={"chips": ["text_mare", "pasi_scurti"]},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]

        # Scale >= 125 and steps format
        assert data["settings"]["font_scale"] >= 125 or data["settings"]["scale"] >= 125
        assert data["settings"]["format"] == "steps"
        assert "written_instructions" in data["adaptations"]


@pytest.mark.anyio
async def test_recommend_adaptations_scrubs_diagnosis_input(monkeypatch):
    """Tests clinical diagnosis words are scrubbed and never echoed."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/profile/recommend-adaptations",
            json={
                "needs_notes": "Am fost diagnosticat cu autism, adhd, sindrom asperger și depresie clinică."
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]

        forbidden = ["autism", "adhd", "asperger", "depresie", "diagnosticat", "sindrom"]
        summary_low = data["summary_ro"].lower()
        for word in forbidden:
            assert word not in summary_low
        for r in data["reasons"]:
            for word in forbidden:
                assert word not in r["reason_ro"].lower()


@pytest.mark.anyio
async def test_recommend_adaptations_garbage_input_safe_defaults(monkeypatch):
    """Garbage input returns safe defaults, never HTTP 422."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/profile/recommend-adaptations",
            json={"needs_notes": "asdf1234!@#$ ??? ... ---"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "settings" in data
        assert data["settings"]["version"] == 2
        assert data["settings"]["theme"] in ("soft", "amber", "sapphire", "hc-dark", "hc-light", "mono", "night")
