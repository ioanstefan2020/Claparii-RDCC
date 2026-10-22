from typing import Literal, Optional

from pydantic import Field, field_validator

from app.schemas.common import TolerantModel


class UserProfile(TolerantModel):
    reading_level: Literal["standard", "simple", "very_simple"] = "simple"
    format: Literal["steps", "short_paragraphs", "bullets"] = "steps"
    needs_notes: Optional[str] = Field(default=None, max_length=500)
    max_sentence_words: Optional[int] = Field(default=12, ge=4, le=50)

    @field_validator("reading_level", mode="before")
    @classmethod
    def normalize_reading_level(cls, v):
        if not v:
            return "simple"
        s = str(v).lower().strip()
        if s in ("standard", "detailed", "complex", "normal", "high"):
            return "standard"
        if s in (
            "very_simple",
            "very-simple",
            "minimal",
            "ultra_simple",
            "easy_read",
            "slow",
        ):
            return "very_simple"
        return "simple"

    @field_validator("format", mode="before")
    @classmethod
    def normalize_format(cls, v):
        if not v:
            return "steps"
        s = str(v).lower().strip()
        if s in ("paragraphs", "short_paragraphs", "paragraph", "text", "cursive"):
            return "short_paragraphs"
        if s in ("bullets", "bullet_points", "list", "buline"):
            return "bullets"
        return "steps"


class StepItem(TolerantModel):
    n: int
    text: str
    source_quote: str


class KeyTermItem(TolerantModel):
    term: str
    explanation: str


class SimplifyData(TolerantModel):
    summary: str
    steps: list[StepItem]
    key_terms: list[KeyTermItem] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)


class SimplifyRequest(TolerantModel):
    text: str
    profile: Optional[UserProfile] = Field(default_factory=UserProfile)
