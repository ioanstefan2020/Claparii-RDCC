from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


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


class ErrorDetail(BaseModel):
    code: str
    message_ro: str


class ErrorEnvelope(BaseModel):
    ok: bool = False
    error: ErrorDetail


class MetaInfo(BaseModel):
    provider: str = "mock"
    cached: bool = False
    warnings: list[str] = Field(default_factory=list)
    ai_notice_ro: str = "Generat de AI — verifică datele importante."


class SuccessEnvelope(BaseModel, Generic[DataT]):
    ok: bool = True
    data: DataT
    meta: MetaInfo
