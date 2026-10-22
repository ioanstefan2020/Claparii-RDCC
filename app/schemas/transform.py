from typing import Any, Literal, Optional

from pydantic import Field

from app.schemas.common import TolerantModel

TransformMode = Literal[
    "bullets", "shorter", "tldr", "easy_read", "steps", "questions", "glossary"
]


class TransformRequest(TolerantModel):
    text: str = Field(..., description="Textul de intrare pentru transformare")
    mode: TransformMode = Field(
        default="bullets",
        description="Modul de transformare dorit",
    )
    max_items: int = Field(
        default=6,
        ge=1,
        le=30,
        description="Număr maxim de elemente pentru modurile tip listă",
    )
    target_pct: int = Field(
        default=40,
        ge=10,
        le=90,
        description="Procentul țintă de lungime pentru modul shorter",
    )
    profile: Optional[Any] = None


class TransformData(TolerantModel):
    mode: str
    items: Optional[list[str]] = None
    text: Optional[str] = None
