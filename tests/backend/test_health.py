import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_health_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"ok": True, "provider": "mock"}
        # Verify metrics header added by middleware
        assert "x-response-time" in response.headers
        # Verify security headers added by middleware (P1-15)
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"


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
