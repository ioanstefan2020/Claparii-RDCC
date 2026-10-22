import re
from typing import Iterable

from app.schemas.common import AppError

# Terms representing medical diagnoses or clinical labeling
DENY_DIAGNOSIS_TERMS = {
    "adhd",
    "autism",
    "autist",
    "asperger",
    "depresie",
    "anxietate",
    "bipolar",
    "schizofrenie",
    "retard",
    "dizabilitate psihica",
    "handicap",
    "deficienta mintala",
    "dislexie",
    "discalculie",
    "epilepsie",
}

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+)?instructions",
    r"disregard\s+(all\s+)?prior",
    r"system\s+override",
    r"jailbreak",
    r"print\s+(the\s+)?(system\s+)?prompt",
    r"uit[aă]\s+instruc[tț]iunile\s+anterioare",
    r"ignor[aă]\s+(toate\s+)?instruc[tț]iunile",
]


def validate_input_limits(text: str, max_chars: int) -> str:
    """Validates that input text is non-empty after trimming and within max_chars."""
    trimmed = text.strip()
    if not trimmed:
        raise AppError(
            code="empty_input",
            message_ro="Textul este gol. Lipește sau scrie ceva.",
            status_code=400,
        )
    if len(trimmed) > max_chars:
        raise AppError(
            code="too_long",
            message_ro=f"Textul depășește limita permisă de {max_chars} caractere.",
            status_code=400,
        )
    return trimmed


def contains_diagnosis_terms(text: str) -> list[str]:
    """Checks if text contains clinical or diagnostic labeling words."""
    found = []
    lower = text.lower()
    for term in DENY_DIAGNOSIS_TERMS:
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, lower):
            found.append(term)
    return found


def contains_prompt_injection(text: str) -> bool:
    """Checks for known prompt-injection attempt patterns with diacritic resilience."""
    lower = text.lower()
    for pat in INJECTION_PATTERNS:
        if re.search(pat, lower, re.IGNORECASE):
            return True
    return False


def sanitize_log_message(msg: str, user_content: str | None = None) -> str:
    """Redacts user content from logging output when LOG_CONTENT is false."""
    if not user_content:
        return msg
    norm_content = user_content.strip()
    if norm_content and norm_content in msg:
        return msg.replace(norm_content, "[CONTENT_REDACTED]")
    return msg
