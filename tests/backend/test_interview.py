import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_interview_prep_empty_input():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Empty title
        resp = await client.post(
            "/api/interview/prep",
            json={"job_title": "  ", "job_description": "Descriere de rol validă."},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["ok"] is False
        assert data["error"]["code"] == "empty_input"

        # Empty description
        resp2 = await client.post(
            "/api/interview/prep",
            json={"job_title": "Developer", "job_description": "   "},
        )
        assert resp2.status_code == 400
        data2 = resp2.json()
        assert data2["ok"] is False
        assert data2["error"]["code"] == "empty_input"


@pytest.mark.anyio
async def test_interview_prep_too_long():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        long_desc = "x" * 10001
        resp = await client.post(
            "/api/interview/prep",
            json={"job_title": "Developer", "job_description": long_desc},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["ok"] is False
        assert data["error"]["code"] == "too_long"


@pytest.mark.anyio
async def test_interview_prep_happy_path(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/interview/prep",
            json={
                "job_title": "Junior Front-End Developer",
                "job_description": "Căutăm coleg pasionat de web development și învățare continuă.",
                "profile": {
                    "reading_level": "simple",
                    "step_by_step": True,
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        res = data["data"]
        assert "overview_ro" in res
        assert len(res["common_questions"]) >= 2
        for q in res["common_questions"]:
            assert "question_ro" in q
            assert "why_asked_ro" in q
            assert "suggested_approach_ro" in q
        assert len(res["suggested_adjustments"]) >= 1
        for adj in res["suggested_adjustments"]:
            assert "id" in adj
            assert "title" in adj
            assert "talking_point_ro" in adj
        assert len(res["questions_to_ask_employer"]) >= 2
        assert data["meta"]["ai_notice_ro"] != ""


@pytest.mark.anyio
async def test_interview_prep_diagnosis_warning(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/interview/prep",
            json={
                "job_title": "Junior QA Analyst",
                "job_description": "Candidat cu adhd și atenție la detalii pentru testare software.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        # Must include ethical warning regarding clinical terms
        warnings = data["meta"]["warnings"]
        assert any("termeni medicali" in w or "etică" in w for w in warnings)
