from typing import Any, Literal

from pydantic import BaseModel, Field


class AdaptationsV2(BaseModel):
    reading_level: int = Field(default=2, ge=1, le=3)
    length: Literal["short", "medium", "full"] = "short"
    steps: bool = True
    glossary: bool = True
    literal_language: bool = True
    tts_ready: bool = False


class DetectedV2(BaseModel):
    language: str
    situation: str
    confidence: float


class ActionV2(BaseModel):
    text: str
    quote: str
    quote_found: bool = True


class DeadlineV2(BaseModel):
    date: str | None = None
    text: str
    quote: str
    quote_found: bool = True


class GlossaryV2(BaseModel):
    term: str
    plain: str


class ChecklistV2(BaseModel):
    step: int
    text: str
    est_minutes: int = 5


class WarningV2(BaseModel):
    code: str
    message: str


class MetricsV2(BaseModel):
    readability_before: float
    readability_after: float
    words_before: int
    words_after: int


class UsageV2(BaseModel):
    provider: str
    latency_ms: int


class AnalyzeV2Request(BaseModel):
    text: str = ""
    file_id: str | None = None
    language: Literal["auto", "ro", "en"] = "auto"
    situation: Literal["auto", "work", "official", "contract", "school", "medical"] = (
        "auto"
    )
    adaptations: AdaptationsV2 = Field(default_factory=AdaptationsV2)
    outputs: list[str] = Field(
        default_factory=lambda: [
            "summary",
            "actions",
            "deadlines",
            "glossary",
            "checklist",
        ]
    )


class AnalyzeV2Response(BaseModel):
    request_id: str
    detected: DetectedV2
    summary: str
    actions: list[ActionV2] = Field(default_factory=list)
    deadlines: list[DeadlineV2] = Field(default_factory=list)
    glossary: list[GlossaryV2] = Field(default_factory=list)
    checklist: list[ChecklistV2] = Field(default_factory=list)
    warnings: list[WarningV2] = Field(default_factory=list)
    metrics: MetricsV2
    usage: UsageV2


class UploadV2Response(BaseModel):
    file_id: str
    filename: str
    size_bytes: int
    text: str
    char_count: int
    format: str


class DraftReplyV2Request(BaseModel):
    context: str = Field(..., min_length=5, max_length=10000)
    tone: Literal["polite", "direct", "friendly"] = "polite"
    goal: str = Field(..., min_length=2, max_length=1000)


class DraftReplyV2Response(BaseModel):
    request_id: str
    subject_ro: str
    body_ro: str
    alternatives: list[str] = Field(default_factory=list)
    checklist_before_sending: list[str] = Field(default_factory=list)
    usage: UsageV2


class MeetingRecapDecisionV2(BaseModel):
    text: str
    quote: str
    quote_found: bool = True


class MeetingRecapActionV2(BaseModel):
    who: str | None = None
    task: str
    deadline: str | None = None
    quote: str
    quote_found: bool = True


class MeetingRecapV2Request(BaseModel):
    transcript: str = Field(..., min_length=10, max_length=50000)
    today_iso: str | None = None


class MeetingRecapV2Response(BaseModel):
    request_id: str
    summary: str
    decisions: list[MeetingRecapDecisionV2] = Field(default_factory=list)
    actions: list[MeetingRecapActionV2] = Field(default_factory=list)
    unclear: list[str] = Field(default_factory=list)
    usage: UsageV2


class AdjustmentChecklistItemV2(BaseModel):
    id: str
    title: str
    legal_basis_ro: str


class AdjustmentRequestV2Request(BaseModel):
    need_ids: list[str] = Field(..., min_length=1)
    tone: Literal["formal", "friendly"] = "friendly"
    context: Literal["interview", "onboarding", "ongoing"] = "onboarding"


class AdjustmentRequestV2Response(BaseModel):
    request_id: str
    subject_ro: str
    body_ro: str
    checklist: list[AdjustmentChecklistItemV2] = Field(default_factory=list)
    usage: UsageV2


class CapabilitiesPrivacyV2(BaseModel):
    zero_server_storage: bool = True
    pii_masking: bool = True
    no_content_logging: bool = True
    no_diagnosis_inference: bool = True
    no_emotion_detection: bool = True


class CapabilitiesV2Response(BaseModel):
    api_version: str = "v2"
    status: str = "ready"
    supported_situations: list[str]
    supported_formats: list[str]
    max_upload_size_bytes: int
    max_text_chars: int
    supported_languages: list[str]
    privacy: CapabilitiesPrivacyV2
    active_provider: str


class V2ErrorDetail(BaseModel):
    code: str
    message_ro: str
    message_en: str
    retryable: bool = False


class V2ErrorEnvelope(BaseModel):
    error: V2ErrorDetail
