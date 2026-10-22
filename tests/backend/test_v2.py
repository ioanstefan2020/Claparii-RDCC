import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_v2_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v2/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "v2"


@pytest.mark.anyio
async def test_v2_capabilities():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v2/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert "work" in data["supported_situations"]
        assert ".docx" in data["supported_formats"]
        assert data["privacy"]["zero_server_storage"] is True


@pytest.mark.anyio
async def test_v2_analyze_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    sample_text = (
        "Către Primăria Sector 3. Vă solicităm să transmiteți la registratura@primarie.ro "
        "copia contractului de comodat până la data de 15 noiembrie 2026. "
        "Taxa de timbru în cuantum de 45 lei se achită prin Ghiseul.ro."
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/v2/analyze",
            json={
                "text": sample_text,
                "language": "ro",
                "situation": "official",
                "adaptations": {
                    "reading_level": 1,
                    "length": "short",
                    "steps": True,
                    "glossary": True,
                    "literal_language": True,
                    "tts_ready": False,
                },
                "outputs": ["summary", "actions", "deadlines", "glossary", "checklist"],
            },
        )
        assert resp.status_code == 200
        res = resp.json()
        assert "request_id" in res
        assert "detected" in res
        assert "summary" in res
        assert "actions" in res
        assert "deadlines" in res
        assert "metrics" in res
        assert (
            res["metrics"]["readability_after"] >= res["metrics"]["readability_before"]
        )


@pytest.mark.anyio
async def test_v2_upload_text():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        files = {
            "file": (
                "notificare.txt",
                b"Continutul notificarii oficiale.",
                "text/plain",
            )
        }
        resp = await client.post("/api/v2/upload", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "notificare.txt"
        assert "Continutul notificarii" in data["text"]
        assert data["size_bytes"] > 0


@pytest.mark.anyio
async def test_v2_draft_reply():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/v2/draft-reply",
            json={
                "context": "Am primit o notificare privind plata unei taxe de 45 lei.",
                "tone": "polite",
                "goal": "Confirm că am plătit taxa și transmit chitanța.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "subject_ro" in data
        assert "body_ro" in data
        assert len(data["alternatives"]) >= 1


@pytest.mark.anyio
async def test_v2_meeting_recap():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/v2/meeting-recap",
            json={
                "transcript": "Ioana: Lansăm vineri 6 noiembrie. Andrei se ocupă de teste.",
                "today_iso": "2026-10-22",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "decisions" in data
        assert "actions" in data


@pytest.mark.anyio
async def test_v2_adjustment_request():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/v2/adjustment-request",
            json={
                "need_ids": ["written_instructions", "extra_time"],
                "tone": "friendly",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "subject_ro" in data
        assert "body_ro" in data
        assert "checklist" in data


@pytest.mark.anyio
async def test_v2_analyze_stream(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/v2/analyze/stream",
            json={
                "text": "Acesta este un document oficial pentru testare stream.",
                "situation": "official",
            },
        )
        assert resp.status_code == 200
        content = resp.text
        assert "event: progress" in content
        assert "event: done" in content
