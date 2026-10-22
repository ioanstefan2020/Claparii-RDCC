import json
import os
from typing import Any, Type

import httpx
from pydantic import BaseModel

from app.config import settings
from app.llm.json_repair import clean_and_parse_json
from app.schemas.common import BadLLMOutput, LLMUnavailable


async def call_ollama(
    system: str, user: str, schema: Type[BaseModel], model: str, timeout: int
) -> dict[str, Any]:
    """Calls local Ollama OpenAI-compatible chat completions API enforcing JSON output."""
    base_url = os.getenv("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
    url = f"{base_url}/chat/completions"
    model_name = (
        model
        if model and not model.startswith("deepseek")
        else settings.OLLAMA_MODEL or "qwen2.5:7b"
    )
    effective_timeout = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", str(max(timeout, 90))))

    json_schema_prompt = (
        f"{system}\n\nIMPORTANT: You must respond ONLY with a valid JSON object strictly "
        f"matching this JSON Schema:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
    )

    headers = {"Content-Type": "application/json"}

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": json_schema_prompt},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=effective_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException:
        raise LLMUnavailable(
            f"Modelul local Ollama ({model_name}) a depășit timpul limită (timeout)."
        )
    except Exception as e:
        raise LLMUnavailable(f"Serviciul local Ollama nu răspunde la {url}: {e}")

    if resp.status_code != 200:
        raise LLMUnavailable(
            f"Eroare API Ollama (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    try:
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"]
        return clean_and_parse_json(raw_text)
    except KeyError as e:
        raise BadLLMOutput(
            f"Răspunsul primit de la Ollama are structură neașteptată: {e}"
        )
    except Exception as e:
        raise BadLLMOutput(f"Răspunsul primit de la Ollama nu este JSON valid: {e}")
