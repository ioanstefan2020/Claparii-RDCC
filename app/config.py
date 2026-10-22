import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Config:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    LLM_CACHE_DIR: str = os.getenv("LLM_CACHE_DIR", ".cache/llm")
    MAX_INPUT_CHARS: int = int(os.getenv("MAX_INPUT_CHARS", "12000"))
    LOG_CONTENT: bool = os.getenv("LOG_CONTENT", "false").lower() in (
        "true",
        "1",
        "yes",
    )


settings = Config()
