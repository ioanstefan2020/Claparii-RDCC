import json

import httpx
import pytest
from pydantic import BaseModel

from app.llm import generate_json
from app.llm.providers.deepseek import call_deepseek
from app.llm.providers.gemini import call_gemini
from app.schemas.common import BadLLMOutput, LLMUnavailable


class DummyOutputSchema(BaseModel):
    summary: str
    points: list[str]


@pytest.mark.anyio
async def test_gemini_missing_api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with pytest.raises(LLMUnavailable) as exc:
        await call_gemini("sys", "usr", DummyOutputSchema, "gemini-2.0-flash", 10)
    assert "GEMINI_API_KEY lipsește" in str(exc.value)


@pytest.mark.anyio
async def test_deepseek_missing_api_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    with pytest.raises(LLMUnavailable) as exc:
        await call_deepseek("sys", "usr", DummyOutputSchema, "deepseek-chat", 10)
    assert "DEEPSEEK_API_KEY lipsește" in str(exc.value)


@pytest.mark.anyio
async def test_gemini_network_error_maps_to_llm_unavailable(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_key")

    def mock_post(*args, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(LLMUnavailable):
        await call_gemini("sys", "usr", DummyOutputSchema, "gemini-2.0-flash", 10)


@pytest.mark.anyio
async def test_deepseek_invalid_json_maps_to_bad_llm_output(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy_key")

    class MockResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "not a valid json string"}}]}

    async def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(BadLLMOutput):
        await call_deepseek("sys", "usr", DummyOutputSchema, "deepseek-chat", 10)


@pytest.mark.anyio
async def test_generate_json_retry_on_bad_json(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy_key")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    call_count = 0

    class MockBadResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "invalid json"}}]}

    class MockGoodResponse:
        status_code = 200

        def json(self):
            valid_payload = json.dumps({"summary": "succes", "points": ["p1"]})
            return {"choices": [{"message": {"content": valid_payload}}]}

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MockBadResponse()
        return MockGoodResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    model, meta = await generate_json(
        task="retry_test",
        system="sys",
        user="usr",
        schema=DummyOutputSchema,
        mock={"summary": "m", "points": []},
    )

    assert call_count == 2
    assert model.summary == "succes"
    assert model.points == ["p1"]
    assert meta["provider"] == "deepseek"
