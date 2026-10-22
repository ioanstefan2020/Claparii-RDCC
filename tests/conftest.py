import pytest

from app.config import settings


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live: marks tests as requiring real LLM provider API keys"
    )


def pytest_collection_modifyitems(config, items):
    """Skips @pytest.mark.live tests unless '-m live' is explicitly requested."""
    markexpr = config.getoption("-m", default="")
    if "live" not in markexpr:
        skip_live = pytest.mark.skip(
            reason="Live API test skipped during regular gate. Run with: pytest -m live"
        )
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)


@pytest.fixture(autouse=True)
def ensure_mock_provider(monkeypatch, request):
    """Enforces mock mode for non-live unit tests regardless of .env configuration."""
    if "live" not in request.keywords:
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
