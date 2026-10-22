"""Tests for the curated adjustments catalog (data/adjustments_ro.json).

Validates schema compliance with docs/CONTRACTS.md §3.4, presence of all 12
required adjustment IDs, valid applicability categories, and enforces the
responsible-AI deny-list to ensure no medical diagnoses appear.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

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

# Responsible-AI deny-list: functional workplace adjustments must NEVER label
# users with medical conditions, clinical terms, or diagnoses.
DENY_LIST_DIAGNOSES = [
    "diagnostic",
    "boală",
    "boala",
    "boli",
    "afecțiune",
    "afectiune",
    "afecțiuni",
    "afectiuni",
    "sindrom",
    "pacient",
    "pacientă",
    "medical",
    "medicală",
    "medicale",
    "handicap",
    "dizabilitate",
    "dizabilități",
    "adhd",
    "autism",
    "depresie",
    "anxietate",
    "orb",
    "surd",
    "paralizie",
    "retard",
    "demență",
    "dementa",
    "patologie",
    "clinic",
    "clinică",
]


@pytest.fixture(scope="module")
def catalog_data() -> dict:
    assert DATA_PATH.exists(), f"Adjustments file missing at {DATA_PATH}"
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


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
        # Check title, description, and example_request
        fields_to_check = {
            "title": item["title"],
            "description": item["description"],
            "example_request": item["example_request"],
        }
        for field_name, text in fields_to_check.items():
            lower_text = text.lower()
            for bad_word in DENY_LIST_DIAGNOSES:
                # Whole word match using regex boundary
                assert not re.search(
                    rf"\b{re.escape(bad_word)}\b", lower_text
                ), (
                    f"Forbidden diagnostic word '{bad_word}' found in {item_id}.{field_name}: '{text}'"
                )
