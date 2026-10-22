import pytest
from pydantic import BaseModel

from app.llm import generate_json


class SampleSchema(BaseModel):
    message: str
    count: int


@pytest.mark.anyio
async def test_generate_json_mock_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    mock_data = {"message": "Salut", "count": 3}
    model, meta = await generate_json(
        task="test_task",
        system="System prompt",
        user="User input text",
        schema=SampleSchema,
        mock=mock_data,
    )

    assert isinstance(model, SampleSchema)
    assert model.message == "Salut"
    assert model.count == 3
    assert meta["provider"] == "mock"
    assert "warnings" in meta
    assert "ai_notice_ro" in meta


@pytest.mark.anyio
async def test_generate_json_disk_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("LLM_CACHE_DIR", str(cache_dir))

    mock_data = {"message": "Cached response", "count": 1}
    # First call: writes cache
    model1, meta1 = await generate_json(
        task="cache_test",
        system="System",
        user="User prompt",
        schema=SampleSchema,
        mock=mock_data,
    )
    assert meta1["cached"] is False

    # Second call with same inputs: loads from cache
    model2, meta2 = await generate_json(
        task="cache_test",
        system="System",
        user="User prompt",
        schema=SampleSchema,
        mock={"message": "Different", "count": 99},
    )
    assert meta2["cached"] is True
    assert model2.message == "Cached response"
