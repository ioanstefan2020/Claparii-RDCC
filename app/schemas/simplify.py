from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class UserProfile(BaseModel):
    reading_level: Literal["standard", "simple", "very_simple"] = "simple"
    format: Literal["steps", "short_paragraphs"] = "steps"
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
        if s in ("very_simple", "very-simple", "minimal", "ultra_simple"):
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
        return "steps"


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
