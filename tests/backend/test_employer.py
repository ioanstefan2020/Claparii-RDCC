"""Tests for employer document cognitive accessibility analysis.

Validates schema compliance with docs/CONTRACTS.md §3.6,
readability computation metrics and abbreviation handling,
grounding guardrails (dropping fabricated quotes),
and error envelopes.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.routers.employer import _split_into_sentences, compute_readability
from app.schemas.employer import (
    AdjustmentChecklistItem,
    DocumentIssue,
    EmployerAnalyzeLLMOutput,
)

SAMPLE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "samples" / "onboarding_ro.txt"
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def onboarding_text() -> str:
    assert SAMPLE_PATH.exists(), f"Sample file missing at {SAMPLE_PATH}"
    return SAMPLE_PATH.read_text(encoding="utf-8")


# ==============================================================================
# Unit Tests: Readability Engine
# ==============================================================================


def test_compute_readability_empty() -> None:
    """Empty or whitespace text yields zero counts and 100 score."""
    stats = compute_readability("")
    assert stats.sentence_count == 0
    assert stats.avg_sentence_words == 0.0
    assert stats.long_sentences == []
    assert stats.score_0_100 == 100

    stats_ws = compute_readability("   \n\t  ")
    assert stats_ws.sentence_count == 0


def test_compute_readability_single_short_sentence() -> None:
    """A single short sentence gives 1 sentence and perfect score."""
    stats = compute_readability("Bun venit în echipă!")
    assert stats.sentence_count == 1
    assert stats.avg_sentence_words == 4.0
    assert len(stats.long_sentences) == 0
    assert stats.score_0_100 == 100


def test_compute_readability_numbers_and_abbreviations() -> None:
    """Splitting protects Romanian abbreviations and decimal numbers."""
    text = (
        "Sediul se află pe str. Victoriei nr. 14, et. 2, ap. 5. "
        "Conform art. 118 din Codul Muncii, programul este flexibil. "
        "Salariul crește cu 2.5% anual conform planului 30-60-90."
    )
    sentences = _split_into_sentences(text)
    # Should be exactly 3 sentences, not split at str., nr., et., ap., art., or 2.5
    assert len(sentences) == 3
    assert "str. Victoriei" in sentences[0]
    assert "art. 118" in sentences[1]
    assert "2.5%" in sentences[2]

    stats = compute_readability(text)
    assert stats.sentence_count == 3


def test_compute_readability_long_sentence_threshold() -> None:
    """Sentences with >= 25 words are flagged as long sentences."""
    # 26 words
    long_sent = (
        "Aceasta este o frază demonstrativă foarte lungă scrisă special pentru a testa "
        "dacă pragul de douăzeci și cinci de cuvinte funcționează corect și fără erori "
        "în modulul de accesibilitate."
    )
    # 10 words
    short_sent = "Iar aceasta este o frază mult mai scurtă și clară."

    stats = compute_readability(f"{long_sent} {short_sent}")
    assert stats.sentence_count == 2
    assert len(stats.long_sentences) == 1
    assert stats.long_sentences[0].words >= 25
    assert stats.long_sentences[0].text == long_sent
    assert stats.score_0_100 < 100


def test_compute_readability_deterministic_score() -> None:
    """Score computation is fully deterministic and degrades on difficult prose."""
    easy_text = "Primul pas este simplu. Al doilea pas este clar. Spor la treabă!"
    hard_text = (
        "În vederea operaționalizării procesului trans-departamental de optimizare a fluxurilor, "
        "se impune implementarea imediată a tuturor mecanismelor de control și conformitate "
        "stabilite conform normelor metodologice aplicabile în primul trimestru al anului curent. "
        "De asemenea, este necesară urmărirea strictă a indicatorilor cheie de performanță "
        "pentru a garanta sustenabilitatea pe termen mediu și lung a procedurilor adoptate."
    )
    stats_easy = compute_readability(easy_text)
    stats_hard = compute_readability(hard_text)

    # Identical runs produce identical scores
    assert stats_easy.score_0_100 == compute_readability(easy_text).score_0_100
    assert stats_hard.score_0_100 == compute_readability(hard_text).score_0_100

    # Hard text has lower readability score
    assert stats_hard.score_0_100 < stats_easy.score_0_100


def test_compute_readability_onboarding_sample(onboarding_text: str) -> None:
    """Onboarding sample has realistic stats and identifies long sentences."""
    stats = compute_readability(onboarding_text)
    assert stats.sentence_count >= 10
    assert stats.avg_sentence_words > 10.0
    assert len(stats.long_sentences) >= 1
    assert 0 <= stats.score_0_100 <= 100


# ==============================================================================
# Integration Tests: POST /api/employer/analyze (CONTRACTS §3.6)
# ==============================================================================


def test_api_analyze_onboarding_sample(
    client: TestClient, onboarding_text: str
) -> None:
    """POST /api/employer/analyze returns 200, valid envelope, stats, issues, and checklist."""
    res = client.post(
        "/api/employer/analyze",
        json={"text": onboarding_text, "doc_type": "onboarding"},
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("ok") is True
    assert "data" in payload
    data = payload["data"]

    # 1. Readability
    assert "readability" in data
    readability = data["readability"]
    assert readability["sentence_count"] > 0
    assert readability["avg_sentence_words"] > 0
    assert isinstance(readability["long_sentences"], list)
    assert 0 <= readability["score_0_100"] <= 100

    # 2. Issues
    assert "issues" in data
    assert isinstance(data["issues"], list)
    assert len(data["issues"]) > 0
    valid_kinds = {
        "jargon",
        "long_sentence",
        "missing_deadline",
        "vague_instruction",
        "missing_structure",
    }
    for issue in data["issues"]:
        assert issue["kind"] in valid_kinds
        assert issue["quote"] in onboarding_text, (
            f"Quote '{issue['quote']}' must be verbatim in input text"
        )
        assert len(issue["fix"]) > 0

    # 3. Easy-read rewrite
    assert "easy_read_ro" in data
    assert len(data["easy_read_ro"]) > 50

    # 4. Adjustment checklist
    assert "adjustment_checklist" in data
    assert len(data["adjustment_checklist"]) > 0
    for item in data["adjustment_checklist"]:
        assert item["id"]
        assert item["title"]

    # 5. Meta
    assert "meta" in payload
    meta = payload["meta"]
    assert meta.get("provider") == "mock"
    assert "ai_notice_ro" in meta
    assert meta.get("warnings") == []


def test_api_analyze_empty_input(client: TestClient) -> None:
    """Empty or whitespace-only text returns 400 with 'empty_input' code."""
    res1 = client.post("/api/employer/analyze", json={"text": ""})
    assert res1.status_code == 400
    payload1 = res1.json()
    assert payload1.get("ok") is False
    assert payload1["error"]["code"] == "empty_input"
    assert "Textul este gol" in payload1["error"]["message_ro"]

    res2 = client.post("/api/employer/analyze", json={"text": "   \n\t  "})
    assert res2.status_code == 400
    payload2 = res2.json()
    assert payload2["error"]["code"] == "empty_input"


def test_api_analyze_too_long(client: TestClient) -> None:
    """Text exceeding 12,000 characters returns 400 with 'too_long' code."""
    long_text = "Aceasta este o propoziție de test repetată. " * 350
    assert len(long_text) > 12000

    res = client.post("/api/employer/analyze", json={"text": long_text})
    assert res.status_code == 400
    payload = res.json()
    assert payload.get("ok") is False
    assert payload["error"]["code"] == "too_long"
    assert "12.000 caractere" in payload["error"]["message_ro"]


def test_api_analyze_extra_fields(client: TestClient) -> None:
    """Extra fields in request return 422 bad_request."""
    res = client.post(
        "/api/employer/analyze",
        json={"text": "Text valid de test", "extra_unwanted_key": "val"},
    )
    assert res.status_code == 422
    payload = res.json()
    assert payload.get("ok") is False
    assert payload["error"]["code"] == "bad_request"


def test_api_analyze_guardrail_drops_fabricated_quote(client: TestClient) -> None:
    """Verifies that an issue with a quote not in the input is dropped and triggers a warning."""
    source_text = "Bine ai venit în echipă! Completarea se face online."

    mock_llm_output = EmployerAnalyzeLLMOutput(
        issues=[
            DocumentIssue(
                kind="jargon",
                quote="Completarea se face online",  # Verbatim in source_text
                fix="Spune exact adresa portalului.",
            ),
            DocumentIssue(
                kind="vague_instruction",
                quote="Acest text este inventat și nu există",  # Fabricated
                fix="Clarifică instrucțiunea.",
            ),
        ],
        easy_read_ro="Bun venit în echipă. Totul se face online.",
        adjustment_checklist=[
            AdjustmentChecklistItem(
                id="written_instructions", title="Instrucțiuni scrise"
            )
        ],
    )

    with patch(
        "app.routers.employer.generate_json",
        return_value=(
            mock_llm_output,
            {"provider": "mock", "cached": False, "warnings": []},
        ),
    ):
        res = client.post("/api/employer/analyze", json={"text": source_text})
        assert res.status_code == 200
        payload = res.json()
        assert payload.get("ok") is True

        data = payload["data"]
        # Only the grounded issue should remain
        assert len(data["issues"]) == 1
        assert data["issues"][0]["quote"] == "Completarea se face online"

        # Warning should record the dropped item
        meta = payload["meta"]
        assert len(meta["warnings"]) == 1
        assert (
            "1 problemă eliminată: citatul nu apare în text." in meta["warnings"][0]
        )


def test_api_analyze_all_doc_types(client: TestClient) -> None:
    """Accepts valid doc_type values: onboarding, job_ad, policy, other."""
    for dt in ["onboarding", "job_ad", "policy", "other"]:
        res = client.post(
            "/api/employer/analyze",
            json={"text": "Text scurt de test pentru verificare.", "doc_type": dt},
        )
        assert res.status_code == 200
        assert res.json().get("ok") is True


def test_api_analyze_default_doc_type(client: TestClient) -> None:
    """Omitting doc_type defaults cleanly to onboarding."""
    res = client.post(
        "/api/employer/analyze",
        json={"text": "Bine ai venit în echipă Companie Exemplu SRL!"},
    )
    assert res.status_code == 200
    assert res.json().get("ok") is True



def test_api_analyze_llm_unavailable_returns_503(client: TestClient) -> None:
    """When the LLM provider fails, returns HTTP 503 with llm_unavailable code."""
    from app.schemas.common import LLMUnavailable

    with patch(
        "app.routers.employer.generate_json",
        side_effect=LLMUnavailable("Serviciul AI nu este disponibil."),
    ):
        res = client.post(
            "/api/employer/analyze",
            json={"text": "Text valid pentru analiza de accesibilitate."},
        )
        assert res.status_code == 503
        payload = res.json()
        assert payload.get("ok") is False
        assert payload["error"]["code"] == "llm_unavailable"


def test_api_analyze_invalid_doc_type(client: TestClient) -> None:
    """Invalid doc_type literal is rejected with HTTP 422 bad_request."""
    res = client.post(
        "/api/employer/analyze",
        json={"text": "Text valid de test", "doc_type": "invalid_doc_type"},
    )
    assert res.status_code == 422
    payload = res.json()
    assert payload.get("ok") is False
    assert payload["error"]["code"] == "bad_request"
