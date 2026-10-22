def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live: marks tests as requiring real LLM provider API keys"
    )
