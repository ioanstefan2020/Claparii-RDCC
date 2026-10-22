import random
import string

import pytest
from fastapi.testclient import TestClient

from app.llm.json_repair import clean_and_parse_json
from app.main import app
from app.schemas.profile_norm import (
    normalize_profile,
    normalize_romanian_text,
    quotes_match_tolerant,
)

client = TestClient(app)


def test_normalize_romanian_text():
    # Romanian cedilla to comma-below
    cedilla = "Acesaţi şi citiţi instrucţiunile."
    comma = "Accesați și citiți instrucțiunile."
    assert normalize_romanian_text(cedilla) == "Acesați și citiți instrucțiunile."
    assert normalize_romanian_text("CRLF\r\nLine2\rLine3") == "CRLF\nLine2\nLine3"


def test_quotes_match_tolerant():
    source = "Vă rugăm să transmiteți documentele scanate până la 15 noiembrie."
    # Quote with old cedillas and different case
    quote = "VĂ RUGĂM SĂ TRANSMITEŢI DOCUMENTELE"
    assert quotes_match_tolerant(quote, source) is True


def test_clean_and_parse_json():
    # 1. Code fence with json
    fenced = '```json\n{"summary": "Test", "steps": []}\n```'
    assert clean_and_parse_json(fenced) == {"summary": "Test", "steps": []}

    # 2. Trailing commas
    trailing = '{"a": 1, "b": [2, 3, ], }'
    assert clean_and_parse_json(trailing) == {"a": 1, "b": [2, 3]}

    # 3. Explanatory text around JSON
    wrapped = 'Here is the response:\n{"result": true}\nHope this helps!'
    assert clean_and_parse_json(wrapped) == {"result": True}


def test_profile_normalization_fuzz_100_runs():
    """Fuzz test proving that 100 random profile inputs never raise 422 or crash."""
    random.seed(42)

    garbage_pool = [
        "detailed",
        "paragraphs",
        "unknown",
        "VERY_SIMPLE",
        "ultra",
        "123",
        "",
        None,
        {"foo": "bar", "deep": [1, 2, 3]},
        [],
        -5,
        999999,
        "şşş",
        "ţţţ",
    ]

    for _ in range(100):
        fuzz_dict = {
            "reading_level": random.choice(garbage_pool),
            "format": random.choice(garbage_pool),
            "focus_level": random.choice([None, -10, 0, 1, 2, 3, 4, 100, "abc"]),
            "max_sentence_words": random.choice([None, 0, 3, 12, 100, "invalid"]),
            "needs_notes": "".join(
                random.choices(string.ascii_letters, k=random.randint(0, 700))
            ),
            "random_junk_key_" + str(random.randint(1, 50)): random.choice(
                garbage_pool
            ),
        }

        # Must never raise an uncaught exception
        norm = normalize_profile(fuzz_dict)
        assert norm.reading_level in ("standard", "simple", "very_simple")
        assert norm.format in ("steps", "short_paragraphs", "bullets")
        assert 0 <= norm.focus_level <= 3
        assert 4 <= norm.max_sentence_words <= 50


def test_simplify_with_garbage_profile_never_returns_422():
    """Prove that sending arbitrary/legacy questionnaire answers never returns HTTP 422."""
    payload = {
        "text": "Acesta este un document de test pentru verificarea rezistenței la erori de schemă.",
        "profile": {
            "reading_level": "detailed",
            "format": "paragraphs",
            "extra_field_unknown": "should be ignored",
            "answers": {"visualNoise": "low", "readingPace": "slow"},
        },
    }
    resp = client.post("/api/simplify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
