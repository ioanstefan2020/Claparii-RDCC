import io

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize("purpose", ["alt_text", "read_text", "chart", "document"])
def test_describe_image_purposes(purpose: str):
    client = TestClient(app)
    # 100 bytes dummy JPEG
    fake_jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 50
    )
    files = {"file": ("birou.jpg", io.BytesIO(fake_jpeg), "image/jpeg")}
    data = {"purpose": purpose}
    res = client.post("/api/describe-image", files=files, data=data)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["data"]["purpose"] == purpose
    assert len(body["data"]["description_ro"]) > 10
    assert "verifică" in body["data"]["confidence_note"].lower()


def test_describe_image_file_too_large():
    client = TestClient(app)
    oversized = b"\xff\xd8" + b"x" * (5 * 1024 * 1024 + 10)
    files = {"file": ("mare.jpg", io.BytesIO(oversized), "image/jpeg")}
    res = client.post("/api/describe-image", files=files)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "too_large"


def test_describe_image_unsupported_format():
    client = TestClient(app)
    files = {"file": ("fisier.exe", io.BytesIO(b"binary"), "application/octet-stream")}
    res = client.post("/api/describe-image", files=files)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "unsupported_type"
