import json
import os
from typing import Any, Type

import httpx
from pydantic import BaseModel

from app.config import settings
from app.schemas.common import BadLLMOutput, LLMUnavailable


async def call_gemini(
    system: str, user: str, schema: Type[BaseModel], model: str, timeout: int
) -> dict[str, Any]:
    """Calls Google Gemini GenerateContent API enforcing JSON output."""
    api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
    if not api_key:
        raise LLMUnavailable("GEMINI_API_KEY lipsește din configurare / mediu.")

    # Default to gemini-2.0-flash or gemini-1.5-flash which are the standard production endpoints
    model_name = model or settings.LLM_MODEL or "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema.model_json_schema(),
        },
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
    except httpx.TimeoutException:
        raise LLMUnavailable("Serviciul Gemini a depășit timpul limită (timeout).")
    except Exception as e:
        raise LLMUnavailable(f"Eroare de conectare la serviciul Gemini: {e}")

    if resp.status_code != 200:
        raise LLMUnavailable(
            f"Eroare API Gemini (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    try:
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)
    except Exception as e:
        raise BadLLMOutput(f"Răspunsul primit de la Gemini nu este JSON valid: {e}")
