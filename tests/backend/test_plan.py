import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_plan_extract_empty_input():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/plan/extract", json={"text": "   "})
        assert resp.status_code == 400
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "empty_input"


@pytest.mark.anyio
async def test_plan_extract_too_long(monkeypatch):
    monkeypatch.setattr("app.config.settings.MAX_INPUT_CHARS", 30)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/plan/extract", json={"text": "A" * 50})
        assert resp.status_code == 400
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "too_long"


@pytest.mark.anyio
async def test_plan_extract_happy_path_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    source_text = (
        "Până miercuri, 28 octombrie, trebuie să completezi în portalul intern formularul F-12. "
        "De asemenea, până joi la prânz trimite raportul."
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/plan/extract", json={"text": source_text, "today_iso": "2026-10-22"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        tasks = body["data"]["tasks"]
        assert len(tasks) == 2

        # Task 1: exact deadline
        assert tasks[0]["id"] == "t1"
        assert tasks[0]["due_iso"] == "2026-10-28"
        assert tasks[0]["needs_confirmation"] is False

        # Task 2: ambiguous deadline
        assert tasks[1]["id"] == "t2"
        assert tasks[1]["due_iso"] is None
        assert tasks[1]["due_text"] is not None
        assert tasks[1]["needs_confirmation"] is True


@pytest.mark.anyio
async def test_plan_extract_drops_fabricated_quotes(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    # Only include the quote for task 2; task 1 quote will be missing
    source_text = "Te rog să trimiți până joi la prânz raportul."

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/plan/extract", json={"text": source_text})
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        tasks = body["data"]["tasks"]
        # Only task 2 survived; re-indexed to t1
        assert len(tasks) == 1
        assert tasks[0]["id"] == "t1"
        assert tasks[0]["source_quote"] == "până joi la prânz"
        assert len(body["meta"]["warnings"]) == 1
        assert "citatul nu apare în text" in body["meta"]["warnings"][0]
