import json
import os
from typing import Any, Type

import httpx
from pydantic import BaseModel

from app.config import settings
from app.schemas.common import BadLLMOutput, LLMUnavailable


async def call_groq(
    system: str, user: str, schema: Type[BaseModel], model: str, timeout: int
) -> dict[str, Any]:
    """Calls Groq OpenAI-compatible chat completions API enforcing JSON output."""
    api_key = os.getenv("GROQ_API_KEY", settings.GROQ_API_KEY)
    if not api_key:
        raise LLMUnavailable("GROQ_API_KEY lipsește din configurare / mediu.")

    base_url = os.getenv("GROQ_BASE_URL", settings.GROQ_BASE_URL).rstrip("/")
    url = f"{base_url}/chat/completions"
    model_name = model or settings.GROQ_MODEL or "llama-3.3-70b-versatile"

    json_schema_prompt = (
        f"{system}\n\nIMPORTANT: You must respond ONLY with a valid JSON object strictly "
        f"matching this JSON Schema:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": json_schema_prompt},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException:
        raise LLMUnavailable("Serviciul Groq a depășit timpul limită (timeout).")
    except Exception as e:
        raise LLMUnavailable(f"Eroare de conectare la serviciul Groq: {e}")

    if resp.status_code != 200:
        raise LLMUnavailable(
            f"Eroare API Groq (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    try:
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"]
        return json.loads(raw_text)
    except Exception as e:
        raise BadLLMOutput(f"Răspunsul primit de la Groq nu este JSON valid: {e}")
