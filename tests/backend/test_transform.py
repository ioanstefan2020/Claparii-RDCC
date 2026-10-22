import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_transform_empty_input_returns_400():
    client = TestClient(app)
    res = client.post("/api/transform", json={"text": "   ", "mode": "bullets"})
    assert res.status_code == 400
    data = res.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "empty_input"


@pytest.mark.parametrize(
    "mode,is_list",
    [
        ("bullets", True),
        ("steps", True),
        ("questions", True),
        ("glossary", True),
        ("shorter", False),
        ("tldr", False),
        ("easy_read", False),
    ],
)
def test_transform_all_modes(mode: str, is_list: bool):
    client = TestClient(app)
    payload = {
        "text": "Luni la 09:00 te prezinți la recepția clădirii B. Până miercuri, 28 octombrie, completezi formularul F-12.",
        "mode": mode,
        "max_items": 4,
        "target_pct": 35,
        "profile": {"reading_level": "simple", "format": "steps"},
    }
    res = client.post("/api/transform", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["data"]["mode"] == mode

    if is_list:
        assert isinstance(data["data"]["items"], list)
        assert len(data["data"]["items"]) > 0
        assert data["data"]["text"] is None
    else:
        assert isinstance(data["data"]["text"], str)
        assert len(data["data"]["text"]) > 0
        assert data["data"]["items"] is None


def test_transform_tolerant_to_unknown_fields():
    client = TestClient(app)
    payload = {
        "text": "Un scurt text de serviciu pentru test.",
        "mode": "tldr",
        "random_extra_param": 12345,
        "legacy_client_flag": True,
    }
    res = client.post("/api/transform", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
