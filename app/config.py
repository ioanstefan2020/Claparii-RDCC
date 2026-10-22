import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Config:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    LLM_FALLBACK_PROVIDER: str = os.getenv("LLM_FALLBACK_PROVIDER", "")
    LLM_PROVIDER_CHAIN: str = os.getenv(
        "LLM_PROVIDER_CHAIN", "groq,deepseek,ollama,mock"
    )
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

    # Per-task routing overrides (B1)
    LLM_ROUTE_SIMPLIFY: str = os.getenv("LLM_ROUTE_SIMPLIFY", "")
    LLM_ROUTE_PLAN: str = os.getenv("LLM_ROUTE_PLAN", "")
    LLM_ROUTE_MEETING: str = os.getenv("LLM_ROUTE_MEETING", "")
    LLM_ROUTE_TRANSFORM: str = os.getenv("LLM_ROUTE_TRANSFORM", "")
    LLM_ROUTE_ANNOTATE: str = os.getenv("LLM_ROUTE_ANNOTATE", "")
    LLM_ROUTE_PROFILE: str = os.getenv("LLM_ROUTE_PROFILE", "")

    # DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # Groq (Free fast inference)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Local Ollama (Offline / Privacy)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    LLM_CACHE_DIR: str = os.getenv("LLM_CACHE_DIR", ".cache/llm")
    MAX_INPUT_CHARS: int = int(os.getenv("MAX_INPUT_CHARS", "12000"))
    LOG_CONTENT: bool = os.getenv("LOG_CONTENT", "false").lower() in (
        "true",
        "1",
        "yes",
    )


settings = Config()
