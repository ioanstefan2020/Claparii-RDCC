"""
Bake-off evaluation runner for Romanian language samples across all core endpoints.
Compares Gemini vs DeepSeek on Romanian quality, latency, and quote fidelity.
Run with: pytest -m live tests/eval/test_bakeoff.py -s
"""

import os
import time
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from app.guardrails import verify_quotes
from app.llm import generate_json
from app.prompts.meeting import SYSTEM as MEETING_SYS
from app.prompts.meeting import build_user as build_meeting_user
from app.prompts.plan import SYSTEM as PLAN_SYS
from app.prompts.plan import build_user as build_plan_user
from app.prompts.simplify import SYSTEM as SIMPLIFY_SYS
from app.prompts.simplify import build_user as build_simplify_user
from app.schemas.meeting import MeetingSummarizeData
from app.schemas.plan import PlanExtractData
from app.schemas.simplify import SimplifyData, SimplifyRequest

ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = ROOT / "data" / "samples"


def check_provider_key(provider: str):
    key_var = "GEMINI_API_KEY" if provider == "gemini" else "DEEPSEEK_API_KEY"
    if not os.getenv(key_var):
        pytest.skip(
            f"{key_var} not configured in environment or .env; skipping live check for {provider}"
        )


@pytest.mark.live
@pytest.mark.anyio
@pytest.mark.parametrize("provider", ["gemini", "deepseek"])
async def test_bakeoff_sample_onboarding(provider, monkeypatch, tmp_path):
    check_provider_key(provider)
    sample_file = SAMPLES_DIR / "onboarding_ro.txt"
    text = sample_file.read_text(encoding="utf-8")

    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("NO_CACHE", "1")

    user_prompt = build_simplify_user(text=text)
    start_time = time.perf_counter()
    res, meta = await generate_json(
        task="bakeoff_simplify",
        system=SIMPLIFY_SYS,
        user=user_prompt,
        schema=SimplifyData,
        mock={"summary": "", "steps": [], "key_terms": [], "questions_to_ask": []},
    )
    elapsed = time.perf_counter() - start_time

    assert res.summary
    assert len(res.steps) >= 1

    # Verify quote fidelity
    raw_steps = [s.model_dump() for s in res.steps]
    kept, dropped = verify_quotes(raw_steps, text, key="source_quote")
    fidelity = (len(kept) / len(raw_steps)) * 100 if raw_steps else 0

    print(
        f"\n[{provider.upper()} - SIMPLIFY] Time: {elapsed:.2f}s | Steps: {len(res.steps)} | "
        f"Quote Fidelity: {len(kept)}/{len(raw_steps)} ({fidelity:.1f}%)"
    )


@pytest.mark.live
@pytest.mark.anyio
@pytest.mark.parametrize("provider", ["gemini", "deepseek"])
async def test_bakeoff_sample_plan(provider, monkeypatch, tmp_path):
    check_provider_key(provider)
    sample_file = SAMPLES_DIR / "task_email_ro.txt"
    text = sample_file.read_text(encoding="utf-8")

    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("NO_CACHE", "1")

    user_prompt = build_plan_user(text=text, today_iso="2026-10-22")
    start_time = time.perf_counter()
    res, meta = await generate_json(
        task="bakeoff_plan",
        system=PLAN_SYS,
        user=user_prompt,
        schema=PlanExtractData,
        mock={"tasks": []},
    )
    elapsed = time.perf_counter() - start_time

    assert len(res.tasks) >= 1

    raw_tasks = [t.model_dump() for t in res.tasks]
    kept, dropped = verify_quotes(raw_tasks, text, key="source_quote")

    # Ambiguous date detection: check that at least one task requires confirmation
    vague_found = any(t.needs_confirmation for t in res.tasks)
    print(
        f"\n[{provider.upper()} - PLAN] Time: {elapsed:.2f}s | Tasks: {len(res.tasks)} | "
        f"Vague date flagged: {vague_found} | Quote verified: {len(kept)}/{len(raw_tasks)}"
    )


@pytest.mark.live
@pytest.mark.anyio
@pytest.mark.parametrize("provider", ["gemini", "deepseek"])
async def test_bakeoff_sample_meeting(provider, monkeypatch, tmp_path):
    check_provider_key(provider)
    sample_file = SAMPLES_DIR / "meeting_transcript_ro.txt"
    text = sample_file.read_text(encoding="utf-8")

    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("NO_CACHE", "1")

    user_prompt = build_meeting_user(transcript=text, today_iso="2026-10-22")
    start_time = time.perf_counter()
    res, meta = await generate_json(
        task="bakeoff_meeting",
        system=MEETING_SYS,
        user=user_prompt,
        schema=MeetingSummarizeData,
        mock={"summary": "", "decisions": [], "action_items": [], "unclear_points": []},
    )
    elapsed = time.perf_counter() - start_time

    assert res.summary
    print(
        f"\n[{provider.upper()} - MEETING] Time: {elapsed:.2f}s | Decisions: {len(res.decisions)} | "
        f"Action Items: {len(res.action_items)} | Unclear points: {len(res.unclear_points)}"
    )
