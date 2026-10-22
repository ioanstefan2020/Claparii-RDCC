import hashlib
import json
import os
from pathlib import Path
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from app.config import settings
from app.llm.providers.deepseek import call_deepseek
from app.llm.providers.gemini import call_gemini
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
    Real providers (gemini / deepseek): JSON output, timeout, 1 retry on invalid JSON,
    cached by hash(task+system+user).
    Raises LLMUnavailable / BadLLMOutput.
    """
    provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER).lower()
    cache_dir_str = os.getenv("LLM_CACHE_DIR", settings.LLM_CACHE_DIR)
    no_cache = os.getenv("NO_CACHE", "0") == "1"
    timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", str(settings.LLM_TIMEOUT_SECONDS)))
    model_override = os.getenv("LLM_MODEL", settings.LLM_MODEL)

    cache_dir = Path(cache_dir_str)
    cache_key = get_cache_key(task, system, user)
    cache_file = cache_dir / f"{cache_key}.json"

    # Check disk cache first
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
            # If cache file is invalid, ignore and re-call provider
            pass

    # 1. Mock provider
    if provider == "mock":
        try:
            validated = schema.model_validate(mock)
        except Exception as e:
            raise BadLLMOutput(f"Mock data invalid against schema: {e}")

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

    # 2. Real providers with 1 retry on BadLLMOutput / Invalid JSON
    if provider not in ("gemini", "deepseek"):
        raise LLMUnavailable(
            f"Furnizorul AI '{provider}' nu este suportat (alege mock, gemini sau deepseek)."
        )

    call_fn = call_gemini if provider == "gemini" else call_deepseek
    last_err: Exception | None = None
    raw_dict: dict[str, Any] | None = None

    for attempt in range(2):
        try:
            raw_dict = await call_fn(
                system=system,
                user=user,
                schema=schema,
                model=model_override,
                timeout=timeout,
            )
            break
        except BadLLMOutput as err:
            last_err = err
            if attempt == 0:
                continue
            raise err
        except LLMUnavailable:
            # Do not retry network failures or missing credentials
            raise

    if raw_dict is None and last_err is not None:
        raise last_err

    try:
        validated = schema.model_validate(raw_dict)
    except Exception as e:
        raise BadLLMOutput(f"Schema output validation failed: {e}")

    # Write successful result to cache
    if not no_cache:
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(
                json.dumps(raw_dict, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    meta = {
        "provider": provider,
        "cached": False,
        "warnings": [],
        "ai_notice_ro": "Generat de AI — verifică datele importante.",
    }
    return validated, meta
