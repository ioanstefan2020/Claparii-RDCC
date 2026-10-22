from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    reading_level: Literal["standard", "simple", "very_simple"] = "simple"
    format: Literal["steps", "short_paragraphs"] = "steps"
    needs_notes: Optional[str] = Field(default=None, max_length=500)
    max_sentence_words: Optional[int] = Field(default=12, ge=4, le=50)


class StepItem(BaseModel):
    n: int
    text: str
    source_quote: str


class KeyTermItem(BaseModel):
    term: str
    explanation: str


class SimplifyData(BaseModel):
    summary: str
    steps: list[StepItem]
    key_terms: list[KeyTermItem] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)


class SimplifyRequest(BaseModel):
    text: str
    profile: Optional[UserProfile] = Field(default_factory=UserProfile)
