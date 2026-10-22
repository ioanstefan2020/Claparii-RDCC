import re
from typing import Any


def normalise_whitespace(text: str) -> str:
    """Collapses consecutive whitespace characters into a single space and strips ends."""
    return re.sub(r"\s+", " ", text).strip()


def verify_quotes(
    items: list[dict[str, Any]], source_text: str, key: str = "source_quote"
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Returns (kept, dropped).
    Verifies that for each item in items, item[key] appears verbatim
    (whitespace-normalised) within source_text (whitespace-normalised).
    Items without the key or with an empty quote are kept as-is.
    """
    norm_source = normalise_whitespace(source_text)
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []

    for item in items:
        quote = item.get(key)
        if not quote:
            kept.append(item)
            continue

        norm_quote = normalise_whitespace(quote)
        if norm_quote and norm_quote in norm_source:
            kept.append(item)
        else:
            dropped.append(item)

    return kept, dropped
