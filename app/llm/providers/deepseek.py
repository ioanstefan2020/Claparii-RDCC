import json
import os
from typing import Any, Type

import httpx
from pydantic import BaseModel

from app.config import settings
from app.llm.json_repair import clean_and_parse_json
from app.schemas.common import BadLLMOutput, LLMUnavailable


async def call_deepseek(
    system: str, user: str, schema: Type[BaseModel], model: str, timeout: int
) -> dict[str, Any]:
    """Calls DeepSeek OpenAI-compatible chat completions API enforcing JSON output."""
    api_key = os.getenv("DEEPSEEK_API_KEY", settings.DEEPSEEK_API_KEY)
    if not api_key:
        raise LLMUnavailable("DEEPSEEK_API_KEY lipsește din configurare / mediu.")

    base_url = os.getenv("DEEPSEEK_BASE_URL", settings.DEEPSEEK_BASE_URL).rstrip("/")
    url = f"{base_url}/chat/completions"
    model_name = model or settings.LLM_MODEL or "deepseek-chat"

    json_schema_prompt = (
        f"{system}\n\nIMPORTANT: You must respond ONLY with a JSON object strictly "
        f"matching this JSON Schema:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
    )

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": json_schema_prompt},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException:
        raise LLMUnavailable("Serviciul DeepSeek a depășit timpul limită (timeout).")
    except Exception as e:
        raise LLMUnavailable(f"Eroare de conectare la serviciul DeepSeek: {e}")

    if resp.status_code == 429:
        retry_after = resp.headers.get("retry-after", "5")
        raise LLMUnavailable(
            f"DeepSeek API rate limit (HTTP 429, retry-after: {retry_after}s): {resp.text[:120]}"
        )

    if resp.status_code != 200:
        raise LLMUnavailable(
            f"Eroare API DeepSeek (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    try:
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"]
        return clean_and_parse_json(raw_text)
    except KeyError as e:
        raise BadLLMOutput(
            f"Răspunsul primit de la DeepSeek are structură neașteptată: {e}"
        )
    except Exception as e:
        raise BadLLMOutput(f"Răspunsul primit de la DeepSeek nu este JSON valid: {e}")
