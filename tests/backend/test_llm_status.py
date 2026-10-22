import pytest
from fastapi.testclient import TestClient

from app.llm import get_llm_status, get_provider_chain, is_provider_configured
from app.llm.circuit_breaker import CircuitBreaker
from app.main import app


def test_llm_status_endpoint():
    client = TestClient(app)
    resp = client.get("/api/llm/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "data" in data
    assert "chain" in data["data"]
    assert "providers" in data["data"]
    assert isinstance(data["data"]["chain"], list)
    assert len(data["data"]["chain"]) > 0

    providers = {p["id"]: p for p in data["data"]["providers"]}
    assert "groq" in providers
    assert "deepseek" in providers
    assert "ollama" in providers
    assert "mock" in providers
    assert providers["mock"]["configured"] is True
    assert providers["mock"]["circuit"] == "closed"


def test_circuit_breaker_metrics():
    cb = CircuitBreaker(failure_threshold=2, recovery_time_seconds=1.0)
    assert cb.circuit_status == "closed"
    assert cb.p50_ms is None

    cb.record_success(latency_ms=100.0)
    cb.record_success(latency_ms=200.0)
    cb.record_success(latency_ms=300.0)
    assert cb.p50_ms == 200
    assert cb.last_ok is not None

    cb.record_failure("Network timeout 504")
    assert cb.circuit_status == "closed"
    assert cb.last_error == "Network timeout 504"

    cb.record_failure("Rate limit 429")
    assert cb.circuit_status == "open"
    assert "Tripped" in cb.reason
    assert not cb.can_execute()


def test_provider_chain_routing():
    chain = get_provider_chain()
    assert "mock" in chain
    assert isinstance(chain, list)


def test_provider_configured_check():
    configured, reason, model = is_provider_configured("mock")
    assert configured is True
    assert reason is None

    configured_unknown, reason_unknown, _ = is_provider_configured("unknown_prov")
    assert configured_unknown is False
    assert "Unknown" in reason_unknown
