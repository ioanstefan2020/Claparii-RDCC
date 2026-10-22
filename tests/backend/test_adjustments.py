"""Tests for the curated adjustments catalog and API endpoints.

Validates schema compliance with docs/CONTRACTS.md §3.4 and §3.5, presence of all 12
required adjustment IDs, valid applicability categories, and enforces the
responsible-AI deny-list to ensure no medical diagnoses appear.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.prompts.adjustments import DENY_LIST_DIAGNOSES
from app.schemas.adjustments import AdjustmentDraftData

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "adjustments_ro.json"

REQUIRED_IDS = {
    "written_instructions",
    "extra_time",
    "quiet_space",
    "flexible_schedule",
    "screen_reader_tools",
    "captions_transcripts",
    "plain_language_docs",
    "regular_checkins",
    "task_breakdown",
    "advance_agenda",
    "ergonomic_equipment",
    "remote_option",
}

VALID_APPLIES_TO = {"cognitive", "visual", "hearing", "motor", "any"}


@pytest.fixture(scope="module")
def catalog_data() -> dict:
    assert DATA_PATH.exists(), f"Adjustments file missing at {DATA_PATH}"
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_catalog_file_structure(catalog_data: dict) -> None:
    """Checks top-level envelope fields."""
    assert "disclaimer_ro" in catalog_data, "Missing disclaimer_ro"
    assert isinstance(catalog_data["disclaimer_ro"], str)
    assert len(catalog_data["disclaimer_ro"].strip()) > 0
    assert "nu reprezintă consultanță juridică" in catalog_data["disclaimer_ro"].lower()

    assert "items" in catalog_data, "Missing items list"
    assert isinstance(catalog_data["items"], list)
    assert len(catalog_data["items"]) >= len(REQUIRED_IDS)


def test_all_twelve_contract_ids_present(catalog_data: dict) -> None:
    """Verifies that all 12 required adjustment IDs from CONTRACTS §3.4 exist."""
    present_ids = {item["id"] for item in catalog_data["items"] if "id" in item}
    missing_ids = REQUIRED_IDS - present_ids
    assert not missing_ids, f"Missing required adjustment IDs: {missing_ids}"


def test_no_duplicate_ids(catalog_data: dict) -> None:
    """Verifies that all adjustment IDs are distinct."""
    ids = [item["id"] for item in catalog_data["items"] if "id" in item]
    assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"


def test_items_schema_and_types(catalog_data: dict) -> None:
    """Verifies each item has valid non-empty fields and valid applies_to categories."""
    for item in catalog_data["items"]:
        item_id = item.get("id")
        assert item_id, f"Item missing id: {item}"

        # title
        assert isinstance(item.get("title"), str) and item["title"].strip(), (
            f"Invalid title for {item_id}"
        )

        # description
        assert (
            isinstance(item.get("description"), str) and item["description"].strip()
        ), f"Invalid description for {item_id}"

        # applies_to
        applies_to = item.get("applies_to")
        assert isinstance(applies_to, list) and len(applies_to) > 0, (
            f"applies_to must be non-empty list for {item_id}"
        )
        for cat in applies_to:
            assert cat in VALID_APPLIES_TO, (
                f"Unknown category '{cat}' in {item_id}. Valid: {VALID_APPLIES_TO}"
            )

        # example_request
        assert (
            isinstance(item.get("example_request"), str)
            and item["example_request"].strip()
        ), f"Invalid example_request for {item_id}"

        # source
        source = item.get("source")
        assert isinstance(source, str) and source.strip(), (
            f"Invalid source for {item_id}"
        )
        assert (
            source == "bună practică generală"
            or source.startswith("http://")
            or source.startswith("https://")
            or "https://" in source
        ), f"Source must be 'bună practică generală' or cite official URL: {source}"


def test_no_diagnosis_or_clinical_words_in_catalog(catalog_data: dict) -> None:
    """Responsible-AI gate: Ensures user-facing text describes functional workplace
    needs without diagnosing or labeling medical conditions.
    """
    for item in catalog_data["items"]:
        item_id = item["id"]
        fields_to_check = {
            "title": item["title"],
            "description": item["description"],
            "example_request": item["example_request"],
        }
        for field_name, text in fields_to_check.items():
            lower_text = text.lower()
            for bad_word in DENY_LIST_DIAGNOSES:
                assert not re.search(
                    rf"\b{re.escape(bad_word)}\b", lower_text
                ), (
                    f"Forbidden diagnostic word '{bad_word}' found in {item_id}.{field_name}: '{text}'"
                )


# ==============================================================================
# Integration Tests: Endpoints (CONTRACTS §3.4 & §3.5)
# ==============================================================================


def test_api_catalog_endpoint_success(client: TestClient) -> None:
    """GET /api/adjustments/catalog returns 200, valid structure, disclaimer, and all 12 items."""
    res = client.get("/api/adjustments/catalog")
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("ok") is True
    assert "data" in payload
    data = payload["data"]

    assert "disclaimer_ro" in data
    assert "nu reprezintă consultanță juridică" in data["disclaimer_ro"].lower()
    assert "items" in data
    assert isinstance(data["items"], list)
    item_ids = {it["id"] for it in data["items"]}
    assert REQUIRED_IDS.issubset(item_ids)


def test_api_draft_success(client: TestClient) -> None:
    """POST /api/adjustments/draft returns 200, valid subject, body, checklist, and meta."""
    req_body = {
        "need_ids": ["written_instructions", "extra_time"],
        "context": "onboarding",
        "tone": "friendly",
    }
    res = client.post("/api/adjustments/draft", json=req_body)
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("ok") is True
    assert "data" in payload
    data = payload["data"]

    assert "subject" in data and len(data["subject"]) > 0
    assert "body_ro" in data and len(data["body_ro"]) > 0
    assert "checklist" in data and len(data["checklist"]) == 2

    chk_ids = [item["id"] for item in data["checklist"]]
    assert chk_ids == ["written_instructions", "extra_time"]
    for chk in data["checklist"]:
        assert "title" in chk and len(chk["title"]) > 0
        assert "why" in chk and len(chk["why"]) > 0

    assert "meta" in payload
    meta = payload["meta"]
    assert meta.get("provider") == "mock"
    assert "ai_notice_ro" in meta


def test_api_draft_empty_need_ids(client: TestClient) -> None:
    """Empty need_ids returns 400 with code 'empty_input'."""
    res = client.post("/api/adjustments/draft", json={"need_ids": []})
    assert res.status_code == 400
    payload = res.json()
    assert payload.get("ok") is False
    assert payload.get("error", {}).get("code") == "empty_input"
    assert "Selectează cel puțin o adaptare" in payload["error"]["message_ro"]


def test_api_draft_unknown_id(client: TestClient) -> None:
    """Unknown ID in need_ids returns 400 with code 'bad_request'."""
    res = client.post(
        "/api/adjustments/draft",
        json={"need_ids": ["written_instructions", "invalid_item_xyz"]},
    )
    assert res.status_code == 400
    payload = res.json()
    assert payload.get("ok") is False
    assert payload.get("error", {}).get("code") == "bad_request"
    assert "nu este valid" in payload["error"]["message_ro"]


def test_api_draft_extra_fields(client: TestClient) -> None:
    """Sending diagnosis or any forbidden extra field returns 422."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "diagnosis": "adhd",
        },
    )
    assert res.status_code == 422
    payload = res.json()
    assert payload.get("ok") is False
    assert payload.get("error", {}).get("code") == "bad_request"


def test_api_draft_output_no_diagnosis_words(client: TestClient) -> None:
    """Responsible-AI gate: generated draft output must contain zero diagnostic words."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions", "extra_time", "quiet_space"],
            "context": "onboarding",
            "tone": "friendly",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]

    full_text = f"{data['subject']} {data['body_ro']} " + " ".join(
        f"{c['title']} {c['why']}" for c in data["checklist"]
    )
    lower_full_text = full_text.lower()
    for bad_word in DENY_LIST_DIAGNOSES:
        assert not re.search(
            rf"\b{re.escape(bad_word)}\b", lower_full_text
        ), f"Diagnostic term '{bad_word}' detected in generated draft response."


def test_api_draft_with_employer_name(client: TestClient) -> None:
    """Draft generation respects employer_name and formal tone."""
    employer = "Compania Exemplu SRL"
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["flexible_schedule"],
            "context": "interview",
            "employer_name": employer,
            "tone": "formal",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert employer in data["body_ro"]
    assert "interviu" in data["subject"].lower()


def test_api_draft_guardrail_catches_bad_llm_output() -> None:
    """If LLM hypothetically produces a diagnostic word, guardrail raises BadLLMOutput (502)."""
    corrupted_output = AdjustmentDraftData(
        subject="Solicitare medicală",
        body_ro="Am un diagnostic de autism și solicit adaptări.",
        checklist=[
            {
                "id": "written_instructions",
                "title": "Instrucțiuni",
                "why": "Necesar pentru pacient.",
            }
        ],
    )
    test_client = TestClient(app)
    with patch(
        "app.routers.adjustments.generate_json",
        return_value=(corrupted_output, {"provider": "mock", "cached": False}),
    ):
        res = test_client.post(
            "/api/adjustments/draft",
            json={"need_ids": ["written_instructions"]},
        )
        assert res.status_code == 502
        payload = res.json()
        assert payload.get("ok") is False
        assert payload.get("error", {}).get("code") == "bad_llm_output"


# ==============================================================================
# QA Attack & Edge Case Tests
# ==============================================================================


def test_api_draft_duplicate_need_ids(client: TestClient) -> None:
    """Duplicate IDs in need_ids should be cleanly deduplicated while preserving order."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": [
                "written_instructions",
                "written_instructions",
                "extra_time",
                "written_instructions",
            ],
            "context": "onboarding",
            "tone": "friendly",
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("ok") is True
    checklist = payload["data"]["checklist"]
    assert len(checklist) == 2
    assert [item["id"] for item in checklist] == [
        "written_instructions",
        "extra_time",
    ]


def test_api_draft_all_twelve_ids(client: TestClient) -> None:
    """Requesting all 12 catalog IDs produces a comprehensive 12-item checklist without diagnosis words."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": list(REQUIRED_IDS),
            "context": "onboarding",
            "tone": "formal",
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("ok") is True
    data = payload["data"]
    assert len(data["checklist"]) == 12
    returned_ids = {item["id"] for item in data["checklist"]}
    assert returned_ids == REQUIRED_IDS
    for item in data["checklist"]:
        assert item["title"] and item["why"]


def test_api_draft_single_id(client: TestClient) -> None:
    """Requesting a single ID produces exactly 1 checklist entry and valid draft."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "context": "onboarding",
            "tone": "friendly",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["checklist"]) == 1
    assert data["checklist"][0]["id"] == "written_instructions"
    assert data["checklist"][0]["title"] == "Instrucțiuni scrise, pas cu pas"
    assert len(data["checklist"][0]["why"]) > 0


def test_api_draft_romanian_diacritics_employer_name(client: TestClient) -> None:
    """Romanian diacritics in employer_name are preserved accurately without triggering guardrails."""
    employer = "S.C. Soluții Ștefan & Însoțitorii S.R.L."
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "context": "onboarding",
            "employer_name": employer,
            "tone": "friendly",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert employer in data["body_ro"]
    assert f"Bună ziua, echipa {employer}," in data["body_ro"]


def test_api_draft_empty_body_and_null_payloads(client: TestClient) -> None:
    """Empty body, missing need_ids, null need_ids, and non-list types return 422 bad_request."""
    # Empty JSON object
    res = client.post("/api/adjustments/draft", json={})
    assert res.status_code == 422
    assert res.json().get("ok") is False
    assert res.json().get("error", {}).get("code") == "bad_request"

    # Missing/null need_ids
    res = client.post("/api/adjustments/draft", json={"need_ids": None})
    assert res.status_code == 422
    assert res.json().get("ok") is False

    # Non-list need_ids (string)
    res = client.post(
        "/api/adjustments/draft", json={"need_ids": "written_instructions"}
    )
    assert res.status_code == 422
    assert res.json().get("ok") is False

    # Raw empty payload
    res = client.post(
        "/api/adjustments/draft",
        content=b"",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 422
    assert res.json().get("ok") is False


def test_api_draft_invalid_context_and_tone(client: TestClient) -> None:
    """Invalid literal values for context or tone are rejected with 422 bad_request."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "context": "vacation",
        },
    )
    assert res.status_code == 422
    assert res.json().get("error", {}).get("code") == "bad_request"

    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "tone": "aggressive",
        },
    )
    assert res.status_code == 422
    assert res.json().get("error", {}).get("code") == "bad_request"


def test_adjustments_smoke_integration_flow(client: TestClient) -> None:
    """Smoke test exercising the entire user flow: catalog fetch -> selection -> draft generation."""
    # 1. Fetch catalog
    cat_res = client.get("/api/adjustments/catalog")
    assert cat_res.status_code == 200
    cat_data = cat_res.json()["data"]
    assert len(cat_data["items"]) >= 12
    selected_ids = [cat_data["items"][0]["id"], cat_data["items"][1]["id"]]

    # 2. Generate accommodation request draft
    draft_res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": selected_ids,
            "context": "onboarding",
            "employer_name": "Tehnologii Incluzive S.R.L.",
            "tone": "friendly",
        },
    )
    assert draft_res.status_code == 200
    draft_payload = draft_res.json()
    assert draft_payload["ok"] is True
    assert "Tehnologii Incluzive S.R.L." in draft_payload["data"]["body_ro"]
    assert len(draft_payload["data"]["checklist"]) == 2
    assert [item["id"] for item in draft_payload["data"]["checklist"]] == selected_ids
    assert draft_payload["meta"]["provider"] == "mock"



# ==============================================================================
# Integration Tests: Endpoints (CONTRACTS §3.4 & §3.5)
# ==============================================================================


from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.adjustments import AdjustmentDraftData


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_api_catalog_endpoint_success(client: TestClient) -> None:
    """GET /api/adjustments/catalog returns 200, valid structure, disclaimer, and all 12 items."""
    res = client.get("/api/adjustments/catalog")
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("ok") is True
    assert "data" in payload
    data = payload["data"]

    assert "disclaimer_ro" in data
    assert "nu reprezintă consultanță juridică" in data["disclaimer_ro"].lower()
    assert "items" in data
    assert isinstance(data["items"], list)
    item_ids = {it["id"] for it in data["items"]}
    assert REQUIRED_IDS.issubset(item_ids)


def test_api_draft_success(client: TestClient) -> None:
    """POST /api/adjustments/draft returns 200, valid subject, body, checklist, and meta."""
    req_body = {
        "need_ids": ["written_instructions", "extra_time"],
        "context": "onboarding",
        "tone": "friendly",
    }
    res = client.post("/api/adjustments/draft", json=req_body)
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("ok") is True
    assert "data" in payload
    data = payload["data"]

    assert "subject" in data and len(data["subject"]) > 0
    assert "body_ro" in data and len(data["body_ro"]) > 0
    assert "checklist" in data and len(data["checklist"]) == 2

    chk_ids = [item["id"] for item in data["checklist"]]
    assert chk_ids == ["written_instructions", "extra_time"]
    for chk in data["checklist"]:
        assert "title" in chk and len(chk["title"]) > 0
        assert "why" in chk and len(chk["why"]) > 0

    assert "meta" in payload
    meta = payload["meta"]
    assert meta.get("provider") == "mock"
    assert "ai_notice_ro" in meta


def test_api_draft_empty_need_ids(client: TestClient) -> None:
    """Empty need_ids returns 400 with code 'empty_input'."""
    res = client.post("/api/adjustments/draft", json={"need_ids": []})
    assert res.status_code == 400
    payload = res.json()
    assert payload.get("ok") is False
    assert payload.get("error", {}).get("code") == "empty_input"
    assert "Selectează cel puțin o adaptare" in payload["error"]["message_ro"]


def test_api_draft_unknown_id(client: TestClient) -> None:
    """Unknown ID in need_ids returns 400 with code 'bad_request'."""
    res = client.post(
        "/api/adjustments/draft",
        json={"need_ids": ["written_instructions", "invalid_item_xyz"]},
    )
    assert res.status_code == 400
    payload = res.json()
    assert payload.get("ok") is False
    assert payload.get("error", {}).get("code") == "bad_request"
    assert "nu este valid" in payload["error"]["message_ro"]


def test_api_draft_extra_fields(client: TestClient) -> None:
    """Sending diagnosis or any forbidden extra field returns 422."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "diagnosis": "adhd",
        },
    )
    assert res.status_code == 422
    payload = res.json()
    assert payload.get("ok") is False
    assert payload.get("error", {}).get("code") == "bad_request"


def test_api_draft_output_no_diagnosis_words(client: TestClient) -> None:
    """Responsible-AI gate: generated draft output must contain zero diagnostic words."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions", "extra_time", "quiet_space"],
            "context": "onboarding",
            "tone": "friendly",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]

    full_text = f"{data['subject']} {data['body_ro']} " + " ".join(
        f"{c['title']} {c['why']}" for c in data["checklist"]
    )
    lower_full_text = full_text.lower()
    for bad_word in DENY_LIST_DIAGNOSES:
        assert not re.search(
            rf"\b{re.escape(bad_word)}\b", lower_full_text
        ), f"Diagnostic term '{bad_word}' detected in generated draft response."


def test_api_draft_with_employer_name(client: TestClient) -> None:
    """Draft generation respects employer_name and formal tone."""
    employer = "Compania Exemplu SRL"
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["flexible_schedule"],
            "context": "interview",
            "employer_name": employer,
            "tone": "formal",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert employer in data["body_ro"]
    assert "interviu" in data["subject"].lower()


def test_api_draft_guardrail_catches_bad_llm_output() -> None:
    """If LLM hypothetically produces a diagnostic word, guardrail raises BadLLMOutput (502)."""
    corrupted_output = AdjustmentDraftData(
        subject="Solicitare medicală",
        body_ro="Am un diagnostic de autism și solicit adaptări.",
        checklist=[
            {
                "id": "written_instructions",
                "title": "Instrucțiuni",
                "why": "Necesar pentru pacient.",
            }
        ],
    )
    test_client = TestClient(app)
    with patch(
        "app.routers.adjustments.generate_json",
        return_value=(corrupted_output, {"provider": "mock", "cached": False}),
    ):
        res = test_client.post(
            "/api/adjustments/draft",
            json={"need_ids": ["written_instructions"]},
        )
        assert res.status_code == 502
        payload = res.json()
        assert payload.get("ok") is False
        assert payload.get("error", {}).get("code") == "bad_llm_output"


# ==============================================================================
# QA Attack & Edge Case Tests
# ==============================================================================


def test_api_draft_duplicate_need_ids(client: TestClient) -> None:
    """Duplicate IDs in need_ids should be cleanly deduplicated while preserving order."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": [
                "written_instructions",
                "written_instructions",
                "extra_time",
                "written_instructions",
            ],
            "context": "onboarding",
            "tone": "friendly",
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("ok") is True
    checklist = payload["data"]["checklist"]
    assert len(checklist) == 2
    assert [item["id"] for item in checklist] == [
        "written_instructions",
        "extra_time",
    ]


def test_api_draft_all_twelve_ids(client: TestClient) -> None:
    """Requesting all 12 catalog IDs produces a comprehensive 12-item checklist without diagnosis words."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": list(REQUIRED_IDS),
            "context": "onboarding",
            "tone": "formal",
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("ok") is True
    data = payload["data"]
    assert len(data["checklist"]) == 12
    returned_ids = {item["id"] for item in data["checklist"]}
    assert returned_ids == REQUIRED_IDS
    for item in data["checklist"]:
        assert item["title"] and item["why"]


def test_api_draft_single_id(client: TestClient) -> None:
    """Requesting a single ID produces exactly 1 checklist entry and valid draft."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "context": "onboarding",
            "tone": "friendly",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["checklist"]) == 1
    assert data["checklist"][0]["id"] == "written_instructions"
    assert data["checklist"][0]["title"] == "Instrucțiuni scrise, pas cu pas"
    assert len(data["checklist"][0]["why"]) > 0


def test_api_draft_romanian_diacritics_employer_name(client: TestClient) -> None:
    """Romanian diacritics in employer_name are preserved accurately without triggering guardrails."""
    employer = "S.C. Soluții Ștefan & Însoțitorii S.R.L."
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "context": "onboarding",
            "employer_name": employer,
            "tone": "friendly",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert employer in data["body_ro"]
    assert f"Bună ziua, echipa {employer}," in data["body_ro"]


def test_api_draft_empty_body_and_null_payloads(client: TestClient) -> None:
    """Empty body, missing need_ids, null need_ids, and non-list types return 422 bad_request."""
    # Empty JSON object
    res = client.post("/api/adjustments/draft", json={})
    assert res.status_code == 422
    assert res.json().get("ok") is False
    assert res.json().get("error", {}).get("code") == "bad_request"

    # Missing/null need_ids
    res = client.post("/api/adjustments/draft", json={"need_ids": None})
    assert res.status_code == 422
    assert res.json().get("ok") is False

    # Non-list need_ids (string)
    res = client.post(
        "/api/adjustments/draft", json={"need_ids": "written_instructions"}
    )
    assert res.status_code == 422
    assert res.json().get("ok") is False

    # Raw empty payload
    res = client.post(
        "/api/adjustments/draft",
        content=b"",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 422
    assert res.json().get("ok") is False


def test_api_draft_invalid_context_and_tone(client: TestClient) -> None:
    """Invalid literal values for context or tone are rejected with 422 bad_request."""
    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "context": "vacation",
        },
    )
    assert res.status_code == 422
    assert res.json().get("error", {}).get("code") == "bad_request"

    res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": ["written_instructions"],
            "tone": "aggressive",
        },
    )
    assert res.status_code == 422
    assert res.json().get("error", {}).get("code") == "bad_request"


def test_adjustments_smoke_integration_flow(client: TestClient) -> None:
    """Smoke test exercising the entire user flow: catalog fetch -> selection -> draft generation."""
    # 1. Fetch catalog
    cat_res = client.get("/api/adjustments/catalog")
    assert cat_res.status_code == 200
    cat_data = cat_res.json()["data"]
    assert len(cat_data["items"]) >= 12
    selected_ids = [cat_data["items"][0]["id"], cat_data["items"][1]["id"]]

    # 2. Generate accommodation request draft
    draft_res = client.post(
        "/api/adjustments/draft",
        json={
            "need_ids": selected_ids,
            "context": "onboarding",
            "employer_name": "Tehnologii Incluzive S.R.L.",
            "tone": "friendly",
        },
    )
    assert draft_res.status_code == 200
    draft_payload = draft_res.json()
    assert draft_payload["ok"] is True
    assert "Tehnologii Incluzive S.R.L." in draft_payload["data"]["body_ro"]
    assert len(draft_payload["data"]["checklist"]) == 2
    assert [item["id"] for item in draft_payload["data"]["checklist"]] == selected_ids
    assert draft_payload["meta"]["provider"] == "mock"
