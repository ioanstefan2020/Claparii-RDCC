import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_tone_suggest_empty_input():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/tone/suggest", json={"text": "   "})
        assert resp.status_code == 400
        data = resp.json()
        assert data["ok"] is False
        assert data["error"]["code"] == "empty_input"


@pytest.mark.anyio
async def test_tone_suggest_happy_path(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/tone/suggest",
            json={
                "text": "Nu stiu ce sa fac mai intai.",
                "context": "clarification",
                "tone_goal": "polite",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        res = data["data"]
        assert "suggested_text" in res
        assert len(res["alternative_phrasings"]) >= 1
        assert "orientativă" in res["uncertainty_notice_ro"]
