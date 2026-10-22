import pytest
from fastapi.testclient import TestClient

from app.annotate.deterministic import extract_deterministic_highlights
from app.main import app


def test_deterministic_highlights_extraction():
    text = (
        "Trebuie să trimiți raportul până vineri la ora 14:00 pentru proiectul F-12. "
        "Atenție, este obligatoriu să respecți bugetul de 500 EUR."
    )
    highlights = extract_deterministic_highlights(text)
    assert len(highlights) >= 3

    # Ensure all offsets slice cleanly
    for h in highlights:
        assert text[h["start"] : h["end"]] == h["text"]
        assert h["category"] in (
            "action",
            "deadline",
            "person",
            "number",
            "warning",
            "term",
        )

    # Ensure no overlaps
    for i in range(len(highlights) - 1):
        assert highlights[i]["end"] <= highlights[i + 1]["start"]


def test_annotate_endpoint_deterministic_only():
    client = TestClient(app)
    payload = {
        "text": "Trimite formularul până pe 15 noiembrie 2026. Atenție, este obligatoriu!",
        "layers": ["deterministic"],
        "highlight_mode": "strong",
    }
    res = client.post("/api/annotate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert len(data["data"]["highlights"]) >= 2
    assert data["data"]["annotations"] == []
    assert data["meta"]["provider"] == "deterministic"


def test_annotate_endpoint_empty_text():
    client = TestClient(app)
    res = client.post("/api/annotate", json={"text": ""})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["data"]["highlights"] == []


def test_annotate_endpoint_with_mock_llm():
    client = TestClient(app)
    payload = {
        "text": "Marți la ora 11:00 avem sesiune introductivă cu Radu. Ar fi frumos să arunci o privire pe document.",
        "layers": ["deterministic", "semantic", "tone", "glossary"],
        "highlight_mode": "strong",
        "profile": {"tone_notes": "on"},
    }
    res = client.post("/api/annotate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    # Offsets check
    for h in data["data"]["highlights"]:
        assert 0 <= h["start"] < h["end"]
        assert payload["text"][h["start"] : h["end"]].lower() == h["text"].lower()
