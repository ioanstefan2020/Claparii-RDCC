from typing import Any, Literal, Optional

from pydantic import Field

from app.schemas.common import TolerantModel


class HighlightItem(TolerantModel):
    start: int
    end: int
    category: Literal["action", "deadline", "person", "number", "warning", "term"]
    text: str


class AnnotationItem(TolerantModel):
    start: int
    end: int
    kind: Literal[
        "joke", "irony", "figurative", "indirect_request", "urgency", "softener"
    ]
    evidence_quote: str
    note_ro: str
    confidence: Literal["low", "medium"] = "medium"


class GlossaryItem(TolerantModel):
    term: str
    explanation: str


class AnnotateData(TolerantModel):
    highlights: list[HighlightItem] = Field(default_factory=list)
    annotations: list[AnnotationItem] = Field(default_factory=list)
    glossary: list[GlossaryItem] = Field(default_factory=list)


class AnnotateRequest(TolerantModel):
    text: str
    layers: list[str] = Field(
        default_factory=lambda: ["deterministic", "semantic", "tone", "glossary"]
    )
    profile: Optional[Any] = None
    today_iso: Optional[str] = None
    highlight_mode: Literal["off", "light", "medium", "strong"] = "light"
