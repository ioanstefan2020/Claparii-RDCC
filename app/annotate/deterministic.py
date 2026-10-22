import re
from typing import Any

# Regex patterns for deterministic extraction on Romanian text
PATTERNS = [
    # 1. Deadlines with "până la / până în / până <zi>"
    (
        "deadline",
        re.compile(
            r"\bp[âa]n[ăa]\s+(?:la\s+|[îi]n\s+)?(?:\d{1,2}\s+[a-zăâîșț\.]+(?:\s+\d{4})?|[a-zăâîșț]+(?:\s+la\s+(?:ora\s+)?\d{1,2}(?::\d{2})?)?|\d{1,2}:\d{2})\b",
            re.IGNORECASE,
        ),
    ),
    # 2. Romanian Month dates e.g. "15 noiembrie 2026", "28 octombrie"
    (
        "deadline",
        re.compile(
            r"\b\d{1,2}\s+(?:ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie)(?:\s+\d{4})?\b",
            re.IGNORECASE,
        ),
    ),
    # 3. Romanian weekdays with optional hour e.g. "Luni la 09:00", "marți la ora 11:00"
    (
        "deadline",
        re.compile(
            r"\b(?:luni|mar[țţ]i|miercuri|joi|vineri|s[âa]mb[ăa]t[ăa]|duminic[ăa])(?:\s+(?:viitoare|trecut[ăa]|aceasta))?(?:\s+(?:la\s+)?(?:ora\s+)?\d{1,2}(?::\d{2})?)?\b",
            re.IGNORECASE,
        ),
    ),
    # 4. Specific clock times e.g. "ora 14:00", "09:30"
    (
        "deadline",
        re.compile(r"\b(?:ora\s+)?\d{1,2}:\d{2}\b", re.IGNORECASE),
    ),
    # 5. Amounts and numbers with currency / units e.g. "45 lei", "100 EUR", "12.000 caractere", "10%"
    (
        "number",
        re.compile(
            r"\b\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?\s*(?:lei|ron|eur|euro|usd|\$|%|procente|zile|ore|minute|caractere)\b",
            re.IGNORECASE,
        ),
    ),
    # 6. Form IDs and document codes e.g. "F-12", "F12", "SSM-01"
    (
        "number",
        re.compile(r"\b[A-Z]{1,4}-\d{1,4}\b"),
    ),
    # 7. Emails
    (
        "term",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
    # 8. Warnings & obligations
    (
        "warning",
        re.compile(
            r"\b(?:obligatoriu|imperativ|interzis|urgent|aten[țţ]ie|penalitat[ea]|penalit[ăa][țţ]i|sanc[țţ]iun[ei]|termen limit[ăa])\b",
            re.IGNORECASE,
        ),
    ),
]


def extract_deterministic_highlights(text: str) -> list[dict[str, Any]]:
    """Extracts deterministic highlights (dates, times, amounts, forms, warnings).

    Guarantees:
    - Zero overlapping intervals.
    - Verified text[start:end] == highlight['text'].
    - Sorted by start offset.
    """
    if not text:
        return []

    spans: list[dict[str, Any]] = []

    for category, pattern in PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            matched_text = text[start:end]
            # Double check exact slice
            if text[start:end] == matched_text:
                spans.append(
                    {
                        "start": start,
                        "end": end,
                        "category": category,
                        "text": matched_text,
                    }
                )

    # Sort spans by start asc, length desc to favor longer matches
    spans.sort(key=lambda s: (s["start"], -(s["end"] - s["start"])))

    # Remove overlapping spans
    clean_spans: list[dict[str, Any]] = []
    last_end = -1

    for s in spans:
        if s["start"] >= last_end:
            clean_spans.append(s)
            last_end = s["end"]

    return clean_spans
