from typing import Any, Literal, Optional

from pydantic import Field

from app.schemas.common import TolerantModel


class ExtensionStyleConfig(TolerantModel):
    reading_level: int = Field(
        default=2, ge=1, le=3, description="1=very simple, 2=simple, 3=cleaned original"
    )
    steps: bool = False
    glossary: bool = True
    literal_language: bool = True
    length: Literal["short", "medium", "full"] = "medium"
    bullets: bool = False


class ExtensionClientInfo(TolerantModel):
    name: str = "extension"
    version: str = "0.1.0"


class ExtensionAdaptRequest(TolerantModel):
    text: str = Field(
        ..., max_length=5000, description="Textul selectat (maxim 3000 caractere)"
    )
    language: Literal["auto", "ro", "en"] = "auto"
    action: Literal["simplify", "bullets", "shorter"] = "simplify"
    style: ExtensionStyleConfig = Field(default_factory=ExtensionStyleConfig)
    preference_text: Optional[str] = Field(default=None, max_length=300)
    client: ExtensionClientInfo = Field(default_factory=ExtensionClientInfo)


class ExtensionNoteItem(TolerantModel):
    quote: str
    note: str
    kind: Literal[
        "idiom",
        "indirect_request",
        "possible_joke",
        "figurative",
        "urgency",
        "softener",
    ]


class ExtensionWarningItem(TolerantModel):
    code: str
    message_ro: str
    message_en: str


class ExtensionMetrics(TolerantModel):
    readability_before: float
    readability_after: float


class ExtensionAdaptResponse(TolerantModel):
    request_id: str
    language: str = "ro"
    text: str
    key_phrases: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    notes: list[ExtensionNoteItem] = Field(default_factory=list)
    warnings: list[ExtensionWarningItem] = Field(default_factory=list)
    metrics: ExtensionMetrics
    mode: Literal["llm", "local", "mock"] = "llm"
