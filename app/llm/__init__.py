import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from app.config import settings
from app.llm.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from app.llm.providers.deepseek import call_deepseek
from app.llm.providers.gemini import call_gemini
from app.schemas.common import BadLLMOutput, LLMUnavailable

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger("primazi.llm")

# Circuit breakers per provider
_breakers: dict[str, CircuitBreaker] = {
    "gemini": CircuitBreaker(failure_threshold=3, recovery_time_seconds=60.0),
    "deepseek": CircuitBreaker(failure_threshold=3, recovery_time_seconds=60.0),
}


def get_cache_key(task: str, system: str, user: str) -> str:
    content = f"{task}\n{system}\n{user}".encode("utf-8")
    return hashlib.sha256(content).hexdigest()


async def _execute_provider_call(
    provider_name: str,
    system: str,
    user: str,
    schema: Type[T],
    model: str,
    timeout: int,
) -> dict[str, Any]:
    breaker = _breakers.get(provider_name)
    if breaker:
        breaker.check_available()

    call_fn = call_gemini if provider_name == "gemini" else call_deepseek
    last_err: Exception | None = None

    for attempt in range(2):
        try:
            res = await call_fn(
                system=system,
                user=user,
                schema=schema,
                model=model,
                timeout=timeout,
            )
            if breaker:
                breaker.record_success()
            return res
        except BadLLMOutput as err:
            last_err = err
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
            raise err
        except Exception as err:
            if breaker:
                breaker.record_failure()
            raise err

    if last_err is not None:
        raise last_err
    raise LLMUnavailable(f"Provider {provider_name} call failed without response.")


async def generate_json(
    task: str, system: str, user: str, schema: Type[T], mock: dict[str, Any]
) -> tuple[T, dict[str, Any]]:
    """
    Unified LLM abstraction supporting provider fallback, timeout, exponential retry,
    circuit breaker, and local cache.
    """
    provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER).lower()
    fallback_provider = os.getenv("LLM_FALLBACK_PROVIDER", "").lower()
    cache_dir_str = os.getenv("LLM_CACHE_DIR", settings.LLM_CACHE_DIR)
    no_cache = os.getenv("NO_CACHE", "0") == "1"
    timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", str(settings.LLM_TIMEOUT_SECONDS)))
    model_override = os.getenv("LLM_MODEL", settings.LLM_MODEL) or ""

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

    # 2. Real provider with automatic fallback
    providers_to_try = [provider]
    if fallback_provider and fallback_provider != provider:
        providers_to_try.append(fallback_provider)
    elif provider != "mock":
        # Safe default fallback
        alt = "deepseek" if provider == "gemini" else "gemini"
        providers_to_try.append(alt)

    raw_dict: dict[str, Any] | None = None
    successful_provider = provider
    primary_error: Exception | None = None

    for active_p in providers_to_try:
        try:
            raw_dict = await _execute_provider_call(
                provider_name=active_p,
                system=system,
                user=user,
                schema=schema,
                model=model_override,
                timeout=timeout,
            )
            successful_provider = active_p
            break
        except (LLMUnavailable, CircuitBreakerOpenException, Exception) as exc:
            logger.warning(f"Provider '{active_p}' failed ({exc}). Trying fallback...")
            if primary_error is None:
                primary_error = exc
            continue

    if raw_dict is None:
        if primary_error:
            raise primary_error
        raise LLMUnavailable(f"All configured providers failed for task '{task}'.")

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
        "provider": successful_provider,
        "cached": False,
        "warnings": [],
        "ai_notice_ro": "Generat de AI — verifică datele importante.",
    }
    return validated, meta
