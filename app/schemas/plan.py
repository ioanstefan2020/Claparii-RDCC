from typing import Literal, Optional

from pydantic import Field

from app.schemas.common import TolerantModel
from app.schemas.simplify import UserProfile


class PlanTask(TolerantModel):
    id: str
    title: str
    due_iso: Optional[str] = None  # Format: YYYY-MM-DD or None if ambiguous/missing
    due_text: Optional[str] = None
    needs_confirmation: bool = False
    priority: Literal["high", "normal", "low"] = "normal"
    steps: list[str] = Field(default_factory=list)
    source_quote: str


class PlanExtractData(TolerantModel):
    tasks: list[PlanTask] = Field(default_factory=list)


class PlanExtractRequest(TolerantModel):
    text: str
    today_iso: Optional[str] = None  # e.g. "2026-10-22"
    profile: Optional[UserProfile] = Field(default_factory=UserProfile)
