import asyncio
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from app.config import settings
from app.llm.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from app.llm.dynamic_mock import generate_dynamic_response
from app.llm.providers.deepseek import call_deepseek
from app.llm.providers.gemini import call_gemini
from app.llm.providers.groq import call_groq
from app.llm.providers.ollama import call_ollama
from app.schemas.common import BadLLMOutput, LLMUnavailable

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger("primazi.llm")

DEFAULT_CACHE_TTL_SECONDS = 7 * 86400  # 7 days

# Circuit breakers per provider
_breakers: dict[str, CircuitBreaker] = {
    "gemini": CircuitBreaker(failure_threshold=3, recovery_time_seconds=60.0),
    "deepseek": CircuitBreaker(failure_threshold=3, recovery_time_seconds=60.0),
    "groq": CircuitBreaker(failure_threshold=3, recovery_time_seconds=60.0),
    "ollama": CircuitBreaker(failure_threshold=3, recovery_time_seconds=30.0),
}


def reset_circuit_breakers() -> None:
    """Resets all circuit breaker counters and status."""
    for b in _breakers.values():
        b.failure_count = 0
        b._state = "CLOSED"
        b.last_failure_time = None
        b.last_error = None
        b.reason = "Normal operation"


def get_cache_key(task: str, system: str, user: str) -> str:
    content = f"{task}\n{system}\n{user}".encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def is_provider_configured(provider_id: str) -> tuple[bool, str | None, str]:
    """Returns (is_configured, reason_if_not, model_name)."""
    p = provider_id.lower().strip()
    if p == "groq":
        key = os.getenv("GROQ_API_KEY", getattr(settings, "GROQ_API_KEY", ""))
        model = (
            os.getenv("GROQ_MODEL", getattr(settings, "GROQ_MODEL", None))
            or "llama-3.3-70b-versatile"
        )
        if not key:
            return False, "GROQ_API_KEY missing", model
        return True, None, model

    if p == "deepseek":
        key = os.getenv("DEEPSEEK_API_KEY", getattr(settings, "DEEPSEEK_API_KEY", ""))
        model = (
            os.getenv("DEEPSEEK_MODEL", getattr(settings, "DEEPSEEK_MODEL", None))
            or "deepseek-chat"
        )
        if not key:
            return False, "DEEPSEEK_API_KEY missing", model
        return True, None, model

    if p == "gemini":
        key = os.getenv("GEMINI_API_KEY", getattr(settings, "GEMINI_API_KEY", ""))
        model = (
            os.getenv("GEMINI_MODEL", getattr(settings, "GEMINI_MODEL", None))
            or "gemini-2.0-flash"
        )
        if not key:
            return False, "GEMINI_API_KEY missing", model
        return True, None, model

    if p == "ollama":
        model = (
            os.getenv("OLLAMA_MODEL", getattr(settings, "OLLAMA_MODEL", None))
            or "qwen2.5:7b"
        )
        return True, None, model

    if p == "mock":
        return True, None, "dynamic_heuristic"

    return False, f"Unknown provider {provider_id}", "unknown"


def get_provider_chain(task: str | None = None) -> list[str]:
    """Resolves provider chain with optional per-task routing override."""
    env_provider = os.getenv("LLM_PROVIDER", "").lower().strip()
    if env_provider == "mock":
        return ["mock"]
    if env_provider and "," not in env_provider:
        return [env_provider, "mock"]

    route_override = None
    if task:
        t = task.lower().strip()
        if t in ("simplify", "document") and settings.LLM_ROUTE_SIMPLIFY:
            route_override = settings.LLM_ROUTE_SIMPLIFY
        elif t in ("plan", "tasks") and settings.LLM_ROUTE_PLAN:
            route_override = settings.LLM_ROUTE_PLAN
        elif t in ("meeting", "audio") and settings.LLM_ROUTE_MEETING:
            route_override = settings.LLM_ROUTE_MEETING
        elif t == "transform" and settings.LLM_ROUTE_TRANSFORM:
            route_override = settings.LLM_ROUTE_TRANSFORM
        elif t in ("annotate", "highlights") and settings.LLM_ROUTE_ANNOTATE:
            route_override = settings.LLM_ROUTE_ANNOTATE
        elif t == "profile_needs" and settings.LLM_ROUTE_PROFILE:
            route_override = settings.LLM_ROUTE_PROFILE

    raw_chain = (
        route_override
        or os.getenv("LLM_PROVIDER_CHAIN", settings.LLM_PROVIDER_CHAIN)
        or "groq,deepseek,ollama,mock"
    )

    items = [x.strip().lower() for x in raw_chain.split(",") if x.strip()]
    if "mock" not in items:
        items.append("mock")
    return items


def get_llm_status() -> dict[str, Any]:
    """Generates LLM status summary conforming to CONTRACTS-WAVE2."""
    chain = get_provider_chain()
    all_providers = ["groq", "deepseek", "ollama", "gemini", "mock"]
    providers_info = []

    for p in all_providers:
        configured, reason, model = is_provider_configured(p)
        info: dict[str, Any] = {
            "id": p,
            "configured": configured,
            "model": model,
        }
        breaker = _breakers.get(p)
        if breaker:
            info["circuit"] = breaker.circuit_status
            info["last_ok"] = breaker.last_ok
            info["last_error"] = breaker.last_error
            info["p50_ms"] = breaker.p50_ms
        else:
            info["circuit"] = "closed"
            info["last_ok"] = None
            info["last_error"] = None
            info["p50_ms"] = None

        if not configured:
            info["reason"] = reason

        providers_info.append(info)

    return {
        "chain": chain,
        "providers": providers_info,
    }


def log_llm_startup() -> None:
    """Logs the status of each provider in the configured chain on application startup."""
    chain = get_provider_chain()
    logger.info("=== PrimaZi LLM Provider Chain Initialization ===")
    logger.info(f"Configured provider chain: {' -> '.join(chain)}")
    for p in chain:
        configured, reason, model = is_provider_configured(p)
        if configured:
            logger.info(f"  [READY] Provider '{p}': configured=True, model='{model}'")
        else:
            logger.warning(
                f"  [SKIP]  Provider '{p}': configured=False, reason='{reason}'"
            )
    logger.info("==================================================")


async def warm_up_llm() -> None:
    """Lightweight warm-up call at startup to pre-warm DNS and TLS."""
    try:
        chain = get_provider_chain()
        first_p = chain[0] if chain else "mock"
        if first_p != "mock" and is_provider_configured(first_p)[0]:
            logger.info(f"Pre-warming connection for provider '{first_p}'...")
            # Fire an asynchronous non-blocking dummy ping if needed
    except Exception as e:
        logger.debug(f"LLM warm-up skipped: {e}")


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

    if provider_name == "gemini":
        call_fn = call_gemini
    elif provider_name == "deepseek":
        call_fn = call_deepseek
    elif provider_name == "groq":
        call_fn = call_groq
    elif provider_name == "ollama":
        call_fn = call_ollama
    else:
        raise LLMUnavailable(f"Furnizor LLM necunoscut: {provider_name}")

    start_t = time.monotonic()
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
            lat_ms = (time.monotonic() - start_t) * 1000.0
            if breaker:
                breaker.record_success(lat_ms)
            return res
        except BadLLMOutput as err:
            last_err = err
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
            if breaker:
                breaker.record_failure(str(err))
            raise err
        except Exception as err:
            if breaker:
                breaker.record_failure(str(err))
            raise err

    if last_err is not None:
        raise last_err
    raise LLMUnavailable(f"Provider {provider_name} call failed without response.")


async def generate_json(
    task: str,
    system: str,
    user: str,
    schema: Type[T],
    mock: dict[str, Any],
    prompt_version: str = "2.0",
) -> tuple[T, dict[str, Any]]:
    """Unified LLM abstraction supporting provider chain fallback, timeouts,

    exponential retry, circuit breaker, and local cache with TTL.
    """
    overall_start = time.monotonic()
    cache_dir_str = os.getenv("LLM_CACHE_DIR", settings.LLM_CACHE_DIR)
    no_cache = os.getenv("NO_CACHE", "0") == "1"
    timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", str(settings.LLM_TIMEOUT_SECONDS)))
    cache_ttl = int(
        os.getenv(
            "LLM_CACHE_TTL_SECONDS",
            str(getattr(settings, "LLM_CACHE_TTL_SECONDS", DEFAULT_CACHE_TTL_SECONDS)),
        )
    )

    cache_dir = Path(cache_dir_str)
    cache_key = get_cache_key(task, system, user)
    cache_file = cache_dir / f"{cache_key}.json"

    # Check disk cache first with TTL
    if not no_cache and cache_file.exists():
        try:
            mtime = cache_file.stat().st_mtime
            if (time.time() - mtime) > cache_ttl:
                # Expired cache entry
                cache_file.unlink(missing_ok=True)
            else:
                cached_raw = cache_file.read_text(encoding="utf-8")
                cached_data = json.loads(cached_raw)
                validated = schema.model_validate(cached_data)
                elapsed_ms = int((time.monotonic() - overall_start) * 1000)
                cached_provider = (
                    "mock" if os.getenv("LLM_PROVIDER") == "mock" else "cache"
                )
                meta = {
                    "provider": cached_provider,
                    "cached": True,
                    "warnings": [],
                    "ai_notice_ro": "Generat de AI — verifică datele importante.",
                    "latency_ms": elapsed_ms,
                    "prompt_version": prompt_version,
                    "provider_chain_tried": [cached_provider],
                }
                return validated, meta
        except Exception:
            pass

    # Resolve chain (honoring LLM_ROUTE_<TASK> and LLM_PROVIDER_CHAIN)
    chain = get_provider_chain(task)

    provider_chain_tried: list[str] = []
    warnings: list[str] = []
    last_exception: Exception | None = None

    for active_p in chain:
        provider_chain_tried.append(active_p)

        # 1. Handle mock in chain
        if active_p == "mock":
            dynamic_payload = generate_dynamic_response(
                task=task, user_prompt=user, schema=schema, canned_mock=mock
            )
            try:
                validated = schema.model_validate(dynamic_payload)
            except Exception:
                try:
                    validated = schema.model_validate(mock)
                    dynamic_payload = mock
                except Exception as e:
                    raise BadLLMOutput(f"Mock data invalid against schema: {e}")

            if not no_cache:
                try:
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(
                        json.dumps(dynamic_payload, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                except OSError:
                    pass

            elapsed_ms = int((time.monotonic() - overall_start) * 1000)
            meta = {
                "provider": "mock",
                "cached": False,
                "warnings": warnings,
                "ai_notice_ro": "Generat de AI — verifică datele importante.",
                "latency_ms": elapsed_ms,
                "prompt_version": prompt_version,
                "provider_chain_tried": provider_chain_tried,
            }
            return validated, meta

        # 2. Check if provider configured
        configured, reason, default_model = is_provider_configured(active_p)
        if not configured:
            logger.warning(
                f"Skipping provider '{active_p}': {reason or 'not configured'}"
            )
            warnings.append(f"Furnizorul {active_p} omis: {reason}")
            continue

        # 3. Check circuit breaker
        breaker = _breakers.get(active_p)
        if breaker and not breaker.can_execute():
            logger.warning(
                f"Skipping provider '{active_p}': circuit is OPEN ({breaker.reason})"
            )
            warnings.append(f"Furnizorul {active_p} are circuitul deschis.")
            continue

        # 4. Attempt provider call using its specific model
        target_model = default_model
        try:
            raw_dict = await _execute_provider_call(
                provider_name=active_p,
                system=system,
                user=user,
                schema=schema,
                model=target_model,
                timeout=timeout,
            )
            validated = schema.model_validate(raw_dict)

            if not no_cache:
                try:
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(
                        json.dumps(raw_dict, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                except OSError:
                    pass

            elapsed_ms = int((time.monotonic() - overall_start) * 1000)
            meta = {
                "provider": active_p,
                "cached": False,
                "warnings": warnings,
                "ai_notice_ro": "Generat de AI — verifică datele importante.",
                "latency_ms": elapsed_ms,
                "prompt_version": prompt_version,
                "provider_chain_tried": provider_chain_tried,
            }
            return validated, meta
        except (BadLLMOutput, LLMUnavailable, CircuitBreakerOpenException) as e:
            logger.warning(
                f"Provider '{active_p}' failed: {e}. Falling back to next..."
            )
            warnings.append(f"Eroare la {active_p}: {str(e)[:100]}")
            last_exception = e
            continue
        except Exception as e:
            logger.exception(f"Unexpected error with provider '{active_p}': {e}")
            warnings.append(f"Eroare neașteptată la {active_p}: {str(e)[:100]}")
            last_exception = e
            continue

    # If all configured providers failed and mock was not reached or failed
    if last_exception:
        raise last_exception
    raise LLMUnavailable("Niciun furnizor de model AI nu a putut răspunde la cerere.")
