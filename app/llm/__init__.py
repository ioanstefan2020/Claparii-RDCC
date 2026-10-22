import hashlib
import json
import os
from pathlib import Path
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from app.config import settings
from app.schemas.common import BadLLMOutput, LLMUnavailable

T = TypeVar("T", bound=BaseModel)


def get_cache_key(task: str, system: str, user: str) -> str:
    content = f"{task}\n{system}\n{user}".encode("utf-8")
    return hashlib.sha256(content).hexdigest()


async def generate_json(
    task: str, system: str, user: str, schema: Type[T], mock: dict[str, Any]
) -> tuple[T, dict[str, Any]]:
    """
    Returns (validated_model, meta_dict).
    provider=mock returns `mock` validated against schema.
    Real providers: JSON output, timeout, 1 retry on invalid JSON, cache by hash(task+system+user).
    Raises LLMUnavailable / BadLLMOutput.
    """
    provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER)
    cache_dir_str = os.getenv("LLM_CACHE_DIR", settings.LLM_CACHE_DIR)
    no_cache = os.getenv("NO_CACHE", "0") == "1"

    cache_dir = Path(cache_dir_str)
    cache_key = get_cache_key(task, system, user)
    cache_file = cache_dir / f"{cache_key}.json"

    # Check cache first if caching is enabled
    if not no_cache and cache_file.exists():
        try:
            cached_raw = cache_file.read_text(encoding="utf-8")
            cached_data = json.loads(cached_raw)
            validated = schema.model_validate(cached_data)
            meta = {
                "provider": provider,
                "cached": True,
                "warnings": [],
                "ai_notice_ro": "Generat de AI — verifică datele importante.",
            }
            return validated, meta
        except Exception:
            # If cache is corrupt, ignore and re-generate
            pass

    # Handle mock provider
    if provider == "mock":
        try:
            validated = schema.model_validate(mock)
        except Exception as e:
            raise BadLLMOutput(f"Mock data invalid against schema: {e}")

        # Write to cache
        if not no_cache:
            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(
                    json.dumps(mock, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            except OSError:
                pass

        meta = {
            "provider": "mock",
            "cached": False,
            "warnings": [],
            "ai_notice_ro": "Generat de AI — verifică datele importante.",
        }
        return validated, meta

    # Placeholder for real providers (T1.2)
    raise LLMUnavailable(f"Provider {provider} not implemented yet.")
