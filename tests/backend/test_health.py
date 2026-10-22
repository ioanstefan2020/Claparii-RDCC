import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_health_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"ok": True, "provider": "mock"}


@pytest.mark.anyio
async def test_error_envelope_404():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/nonexistent_endpoint")
        assert response.status_code == 404
        data = response.json()
        assert data["ok"] is False
        assert "error" in data
        assert "code" in data["error"]
        assert "message_ro" in data["error"]
