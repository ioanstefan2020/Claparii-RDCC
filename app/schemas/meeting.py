from typing import Optional

from pydantic import Field

from app.schemas.common import TolerantModel
from app.schemas.simplify import UserProfile


class MeetingDecision(TolerantModel):
    text: str
    source_quote: str


class MeetingActionItem(TolerantModel):
    who: Optional[str] = None
    task: str
    due_iso: Optional[str] = None
    due_text: Optional[str] = None
    needs_confirmation: bool = False
    source_quote: str


class MeetingSummarizeData(TolerantModel):
    summary: str
    decisions: list[MeetingDecision] = Field(default_factory=list)
    action_items: list[MeetingActionItem] = Field(default_factory=list)
    unclear_points: list[str] = Field(default_factory=list)


class MeetingSummarizeRequest(TolerantModel):
    transcript: str
    today_iso: Optional[str] = None
    profile: Optional[UserProfile] = Field(default_factory=UserProfile)
