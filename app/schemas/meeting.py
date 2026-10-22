from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.simplify import UserProfile


class MeetingDecision(BaseModel):
    text: str
    source_quote: str


class MeetingActionItem(BaseModel):
    who: Optional[str] = None
    task: str
    due_iso: Optional[str] = None
    due_text: Optional[str] = None
    needs_confirmation: bool = False
    source_quote: str


class MeetingSummarizeData(BaseModel):
    summary: str
    decisions: list[MeetingDecision] = Field(default_factory=list)
    action_items: list[MeetingActionItem] = Field(default_factory=list)
    unclear_points: list[str] = Field(default_factory=list)


class MeetingSummarizeRequest(BaseModel):
    transcript: str
    today_iso: Optional[str] = None
    profile: Optional[UserProfile] = Field(default_factory=UserProfile)
