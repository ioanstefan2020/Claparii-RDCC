"""Pydantic schemas for employer document accessibility analysis.

Follows docs/CONTRACTS.md §3.6.
Responsible-AI requirement: analyzes and scores the document, never a person.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import SuccessEnvelope

DocType = Literal["onboarding", "job_ad", "policy", "other"]
IssueKind = Literal[
    "jargon",
    "long_sentence",
    "missing_deadline",
    "vague_instruction",
    "missing_structure",
]


class AnalyzeRequest(BaseModel):
    """Request payload for POST /api/employer/analyze."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="Document text to analyze. Max 12000 chars.")
    doc_type: DocType = Field(
        default="onboarding",
        description="Type of workplace document being analyzed.",
    )


class LongSentence(BaseModel):
    """Sentence identified as too long (>= 25 words)."""

    text: str
    words: int


class ReadabilityStats(BaseModel):
    """Deterministic readability metrics for the document."""

    sentence_count: int
    avg_sentence_words: float
    long_sentences: list[LongSentence]
    score_0_100: int


class DocumentIssue(BaseModel):
    """Clarity or cognitive accessibility issue detected in the document."""

    kind: IssueKind
    quote: str
    fix: str


class AdjustmentChecklistItem(BaseModel):
    """Workplace adjustment recommendation mapped to catalog IDs."""

    id: str
    title: str


class EmployerAnalyzeLLMOutput(BaseModel):
    """Structured LLM output for document analysis."""

    issues: list[DocumentIssue]
    easy_read_ro: str
    adjustment_checklist: list[AdjustmentChecklistItem]


class EmployerAnalyzeData(BaseModel):
    """Complete response payload for POST /api/employer/analyze per CONTRACTS §3.6."""

    readability: ReadabilityStats
    issues: list[DocumentIssue]
    easy_read_ro: str
    adjustment_checklist: list[AdjustmentChecklistItem]


AnalyzeResponse = SuccessEnvelope[EmployerAnalyzeData]
