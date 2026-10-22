from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.simplify import UserProfile


class ToneSuggestRequest(BaseModel):
    text: str = Field(..., max_length=2000)
    context: Literal["clarification", "followup", "deadline", "feedback"] = (
        "clarification"
    )
    tone_goal: Literal["polite", "direct", "friendly"] = "polite"
    profile: Optional[UserProfile] = Field(default_factory=UserProfile)


class ToneSuggestData(BaseModel):
    suggested_text: str
    alternative_phrasings: list[str] = Field(default_factory=list)
    uncertainty_notice_ro: str = "Sugestie pur orientativă. Comunicarea umană depinde de relația cu interlocutorul."
