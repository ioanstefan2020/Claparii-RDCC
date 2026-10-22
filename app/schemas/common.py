from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

DataT = TypeVar("DataT")


class TolerantModel(BaseModel):
    """Base model that ignores extra fields and tolerates client schema extensions."""

    model_config = ConfigDict(extra="ignore")


class AppError(Exception):
    def __init__(self, code: str, message_ro: str, status_code: int = 400):
        super().__init__(message_ro)
        self.code = code
        self.message_ro = message_ro
        self.status_code = status_code


class LLMUnavailable(AppError):
    def __init__(
        self,
        message_ro: str = "Serviciul AI nu este disponibil momentan. Încearcă din nou.",
    ):
        super().__init__(code="llm_unavailable", message_ro=message_ro, status_code=503)


class BadLLMOutput(AppError):
    def __init__(
        self, message_ro: str = "Răspunsul primit de la AI nu are formatul valid."
    ):
        super().__init__(code="bad_llm_output", message_ro=message_ro, status_code=502)


class ErrorDetail(TolerantModel):
    code: str
    message_ro: str


class ErrorEnvelope(TolerantModel):
    ok: bool = False
    error: ErrorDetail


class MetaInfo(TolerantModel):
    provider: str = "mock"
    cached: bool = False
    warnings: list[str] = Field(default_factory=list)
    ai_notice_ro: str = "Generat de AI — verifică datele importante."
    latency_ms: int | None = None
    prompt_version: str | None = None
    provider_chain_tried: list[str] = Field(default_factory=list)


class SuccessEnvelope(TolerantModel, Generic[DataT]):
    ok: bool = True
    data: DataT
    meta: MetaInfo


# Alias for backward-compat and ergonomics across routers
ApiResponse = SuccessEnvelope
