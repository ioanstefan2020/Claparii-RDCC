"""Employer document cognitive accessibility analysis router.

Endpoints:
- POST /api/employer/analyze: Analyzes onboarding guides, job ads, and internal policies
  for cognitive clarity, structure, and plain language compliance (CONTRACTS §3.6).
"""
from __future__ import annotations

import logging
import re

from fastapi import APIRouter

from app.config import settings
from app.guardrails import verify_quotes
from app.llm import generate_json
from app.prompts.adjustments import DENY_LIST_DIAGNOSES
from app.prompts.employer import MOCK, SYSTEM, build_user
from app.schemas.common import AppError, BadLLMOutput, MetaInfo
from app.schemas.employer import (
    AnalyzeRequest,
    AnalyzeResponse,
    DocumentIssue,
    EmployerAnalyzeData,
    EmployerAnalyzeLLMOutput,
    LongSentence,
    ReadabilityStats,
)

router = APIRouter(prefix="/api/employer", tags=["employer"])
logger = logging.getLogger(__name__)

# Known Romanian abbreviations ending in dot to protect during sentence splitting
_ROMANIAN_ABBREVIATIONS = (
    "str",
    "nr",
    "etc",
    "srl",
    "art",
    "alin",
    "hg",
    "sc",
    "s.c",
    "s.r.l",
    "d-na",
    "dl",
    "ing",
    "dr",
    "prof",
    "pct",
    "vol",
    "pag",
    "ex",
    "tel",
    "ap",
    "bl",
    "et",
    "jud",
    "mun",
    "v3",
)


def _count_words(sentence: str) -> int:
    """Counts words in a sentence, ignoring pure punctuation."""
    return len([w for w in sentence.split() if any(c.isalnum() for c in w)])


def _split_into_sentences(text: str) -> list[str]:
    """Splits text into sentences, protecting decimal numbers and common abbreviations."""
    if not text or not text.strip():
        return []

    # Protect decimal numbers (e.g., 1.5, 3.14)
    protected = re.sub(r"(\d+)\.(\d+)", r"\1__DOT__\2", text)

    # Protect Romanian abbreviations
    for abb in _ROMANIAN_ABBREVIATIONS:
        pattern = rf"\b({re.escape(abb)})\."
        protected = re.sub(pattern, r"\1__DOT__", protected, flags=re.IGNORECASE)

    # Protect single capital letter initials (e.g., "A. Ionescu")
    protected = re.sub(r"\b([A-ZĂÂÎȘȚ])\.", r"\1__DOT__", protected)

    # Split on sentence terminals ([.!?]) followed by space or newline, or double newlines
    raw_chunks = re.split(r"(?<=[.!?])\s+|\n+", protected)

    sentences: list[str] = []
    for chunk in raw_chunks:
        # Restore dots
        s = chunk.replace("__DOT__", ".").strip()
        # Strip leading bullet/list symbols (e.g., "- ", "• ", "* ")
        s = re.sub(r"^[-•*–—]\s*", "", s).strip()
        if s and _count_words(s) > 0:
            sentences.append(s)

    return sentences


def compute_readability(text: str) -> ReadabilityStats:
    """Computes deterministic readability statistics for a document.

    Evaluates and scores the document, never an individual.
    - Sentences are detected taking abbreviations and numbers into account.
    - Long sentences are defined as >= 25 words.
    - Readability score (0-100) rewards clear, accessible lengths and penalizes
      unnecessarily dense or tangled prose.
    """
    sentences = _split_into_sentences(text)
    if not sentences:
        return ReadabilityStats(
            sentence_count=0,
            avg_sentence_words=0.0,
            long_sentences=[],
            score_0_100=100,
        )

    sentence_count = len(sentences)
    word_counts = [_count_words(s) for s in sentences]
    total_words = sum(word_counts)
    avg_sentence_words = round(total_words / sentence_count, 1)

    long_sentences: list[LongSentence] = [
        LongSentence(text=s, words=wc)
        for s, wc in zip(sentences, word_counts)
        if wc >= 25
    ]

    # Deterministic scoring formula (0 to 100):
    # - Base: 100
    # - Avg sentence length penalty: deduct 2.0 pts per word above 15 words
    # - Long sentence penalty (>= 25 words): deduct 8.0 pts per long sentence
    # - Extreme sentence penalty (>= 35 words): deduct extra 5.0 pts
    penalty = max(0.0, (avg_sentence_words - 15.0) * 2.0)
    penalty += len(long_sentences) * 8.0
    penalty += sum(5.0 for ls in long_sentences if ls.words >= 35)

    score_0_100 = max(0, min(100, int(round(100.0 - penalty))))

    return ReadabilityStats(
        sentence_count=sentence_count,
        avg_sentence_words=avg_sentence_words,
        long_sentences=long_sentences,
        score_0_100=score_0_100,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_employer_document(req: AnalyzeRequest) -> AnalyzeResponse:
    """Analyzes employer documents for cognitive accessibility, clarity, and accommodations.

    Rejects empty documents or texts exceeding 12,000 characters.
    Enforces verbatim quote verification guardrail on detected issues.
    """
    cleaned_text = req.text.strip()
    if not cleaned_text:
        raise AppError(
            code="empty_input",
            message_ro="Textul este gol. Lipește sau scrie ceva.",
            status_code=400,
        )

    if len(req.text) > settings.MAX_INPUT_CHARS:
        raise AppError(
            code="too_long",
            message_ro="Textul depășește limita maximă de 12.000 caractere.",
            status_code=400,
        )

    # 1. Deterministic readability metrics (code-only, fully tested)
    readability = compute_readability(req.text)

    # 2. LLM document analysis (clarity issues, easy-read rewrite, adjustments)
    user_prompt = build_user(text=req.text, doc_type=req.doc_type)
    validated_llm, meta_dict = await generate_json(
        task="employer_analyze",
        system=SYSTEM,
        user=user_prompt,
        schema=EmployerAnalyzeLLMOutput,
        mock=MOCK,
    )

    # Defense-in-depth: Ensure easy_read_ro and fixes contain no medical diagnoses
    text_to_scan = [validated_llm.easy_read_ro] + [issue.fix for issue in validated_llm.issues]
    for text_fragment in text_to_scan:
        lower_frag = text_fragment.lower()
        for bad_word in DENY_LIST_DIAGNOSES:
            if re.search(rf"\b{re.escape(bad_word)}\b", lower_frag):
                raise BadLLMOutput(
                    message_ro="Răspunsul primit conține termeni nepermiși din zona medicală sau diagnostic."
                )

    # 3. Guardrail: Grounding check (all issue quotes must be verbatim in input)
    issue_dicts = [issue.model_dump() for issue in validated_llm.issues]
    kept_issues, dropped_issues = verify_quotes(issue_dicts, req.text, key="quote")

    warnings: list[str] = list(meta_dict.get("warnings", []))
    if dropped_issues:
        count = len(dropped_issues)
        logger.warning(
            "Dropped %d ungrounded issues from employer analysis LLM output", count
        )
        warning_msg = (
            f"{count} problemă eliminată: citatul nu apare în text."
            if count == 1
            else f"{count} probleme eliminate: citatul nu apare în text."
        )
        warnings.append(warning_msg)

    final_issues = [DocumentIssue.model_validate(it) for it in kept_issues]

    data = EmployerAnalyzeData(
        readability=readability,
        issues=final_issues,
        easy_read_ro=validated_llm.easy_read_ro,
        adjustment_checklist=validated_llm.adjustment_checklist,
    )

    meta = MetaInfo(
        provider=meta_dict.get("provider", "mock"),
        cached=meta_dict.get("cached", False),
        warnings=warnings,
        ai_notice_ro=meta_dict.get(
            "ai_notice_ro", "Generat de AI — verifică datele importante."
        ),
    )

    return AnalyzeResponse(ok=True, data=data, meta=meta)
