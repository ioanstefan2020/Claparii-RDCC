import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_meeting_summarize_empty_input():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/meeting/summarize", json={"transcript": "   "})
        assert resp.status_code == 400
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "empty_input"


@pytest.mark.anyio
async def test_meeting_summarize_too_long(monkeypatch):
    monkeypatch.setattr("app.config.settings.MAX_INPUT_CHARS", 40)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/meeting/summarize", json={"transcript": "M" * 50}
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "too_long"


@pytest.mark.anyio
async def test_meeting_summarize_happy_path_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    transcript = (
        "Andrei: Decizia este că lansăm vineri, 6 noiembrie. "
        "Ioana, tu integrezi textele miercuri și vedem cum arată."
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/meeting/summarize",
            json={"transcript": transcript, "today_iso": "2026-10-22"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]

        assert "summary" in data
        assert len(data["decisions"]) == 1
        assert data["decisions"][0]["source_quote"] == "lansăm vineri, 6 noiembrie"

        assert len(data["action_items"]) == 1
        assert data["action_items"][0]["who"] == "Ioana"
        assert data["action_items"][0]["needs_confirmation"] is True
        assert (
            data["action_items"][0]["source_quote"] == "tu integrezi textele miercuri"
        )

        assert len(data["unclear_points"]) == 1
        assert body["meta"]["warnings"] == []


@pytest.mark.anyio
async def test_meeting_summarize_drops_unverified_quote(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    # Only include decision quote in transcript; action item quote is omitted
    transcript = "Andrei: lansăm vineri, 6 noiembrie."

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/meeting/summarize", json={"transcript": transcript}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]

        # Decision kept
        assert len(data["decisions"]) == 1
        # Action item dropped
        assert len(data["action_items"]) == 0
        assert len(body["meta"]["warnings"]) == 1
        assert "citatul nu apare în transcriere" in body["meta"]["warnings"][0]
