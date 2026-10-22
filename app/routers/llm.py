from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.llm import get_llm_status

router = APIRouter(prefix="/api/llm", tags=["llm"])


class ProviderStatusItem(BaseModel):
    id: str
    configured: bool
    model: str | None = None
    circuit: str = "closed"
    last_ok: str | None = None
    last_error: str | None = None
    p50_ms: int | None = None
    reason: str | None = None


class LLMStatusData(BaseModel):
    chain: list[str]
    providers: list[ProviderStatusItem]


class LLMStatusEnvelope(BaseModel):
    ok: bool = True
    data: LLMStatusData


@router.get("/status", response_model=LLMStatusEnvelope)
async def get_status() -> dict[str, Any]:
    """Returns the operational status of the LLM provider fallback chain and circuits."""
    data = get_llm_status()
    return {"ok": True, "data": data}
