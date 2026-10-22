import json
import re
from typing import Any

from app.schemas.common import BadLLMOutput


def repair_json_string(raw: str) -> str:
    """Cleans common LLM formatting artifacts from a JSON string."""
    text = raw.strip()

    # 1. Strip markdown fences if present
    fence_pattern = re.compile(r"^```(?:json)?\s*([\s\S]*?)\s*```$", re.MULTILINE)
    match = fence_pattern.search(text)
    if match:
        text = match.group(1).strip()
    else:
        # Also handle code fences embedded in explanatory text
        fences = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fences:
            text = fences[0].strip()

    # 2. Extract substring between first '{' and last '}'
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace : last_brace + 1]

    # 3. Strip trailing commas before closing braces/brackets
    text = re.sub(r",\s*([}\]])", r"\1", text)

    return text


def clean_and_parse_json(raw: str) -> dict[str, Any]:
    """Parses JSON produced by an LLM with tolerant cleanup."""
    if not raw or not raw.strip():
        raise BadLLMOutput("Răspunsul primit de la model este gol.")

    cleaned = repair_json_string(raw)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
        raise BadLLMOutput("Răspunsul JSON nu este un obiect dicționar.")
    except json.JSONDecodeError as err:
        # Attempt secondary fix: replace single quotes with double quotes on keys
        try:
            fixed_quotes = re.sub(r"(?<=[{,\s])'([a-zA-Z0-9_]+)':", r'"\1":', cleaned)
            data = json.loads(fixed_quotes)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        raise BadLLMOutput(
            f"Răspunsul primit de la AI nu este JSON valid ({err.msg} la linia {err.lineno})."
        )
