"""
Bake-off evaluation runner for Romanian language samples.
Compares Gemini vs DeepSeek on Romanian quality, latency, and quote fidelity.
Run with: pytest -m live tests/eval/test_bakeoff.py
"""

import os
import time
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from app.guardrails import verify_quotes
from app.llm import generate_json

ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = ROOT / "data" / "samples"


class SimpleTaskSchema(BaseModel):
    summary: str
    steps: list[str]
    quotes: list[str] = Field(default_factory=list)


@pytest.mark.live
@pytest.mark.anyio
@pytest.mark.parametrize("provider", ["gemini", "deepseek"])
async def test_bakeoff_sample_onboarding(provider, monkeypatch, tmp_path):
    api_key_var = "GEMINI_API_KEY" if provider == "gemini" else "DEEPSEEK_API_KEY"
    if not os.getenv(api_key_var):
        pytest.skip(f"{api_key_var} not set; skipping live test for {provider}")

    sample_file = SAMPLES_DIR / "onboarding_ro.txt"
    if not sample_file.exists():
        pytest.skip("data/samples/onboarding_ro.txt not found")

    text = sample_file.read_text(encoding="utf-8")
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("NO_CACHE", "1")

    system_prompt = (
        "Ești un asistent util. Extrage pașii principali din textul de onboarding în limba română simplă. "
        "Pentru fiecare pas, include citatul exact din text în câmpul 'quotes'."
    )
    user_prompt = f"Text:\n{text}"

    start_time = time.perf_counter()
    res, meta = await generate_json(
        task="bakeoff_onboarding",
        system=system_prompt,
        user=user_prompt,
        schema=SimpleTaskSchema,
        mock={"summary": "", "steps": [], "quotes": []},
    )
    elapsed = time.perf_counter() - start_time

    assert res.summary
    assert len(res.steps) >= 1

    # Verify Romanian quote fidelity
    quote_items = [{"source_quote": q} for q in res.quotes]
    kept, dropped = verify_quotes(quote_items, text, key="source_quote")

    print(
        f"\n[{provider.upper()}] Elapsed: {elapsed:.2f}s | Steps: {len(res.steps)} | Quotes verified: {len(kept)}/{len(quote_items)}"
    )
