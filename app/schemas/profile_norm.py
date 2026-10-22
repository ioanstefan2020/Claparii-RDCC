import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def normalize_romanian_text(text: str) -> str:
    """Normalizes Romanian diacritics (cedilla to comma-below) and cleans line endings."""
    if not text:
        return ""
    # Map cedillas to proper standard comma-below diacritics
    # \u015e (Ş) -> \u0218 (Ș), \u015f (ş) -> \u0219 (ș)
    # \u0162 (Ţ) -> \u021a (Ț), \u0163 (ţ) -> \u021b (ț)
    t = text.replace("\u015e", "\u0218").replace("\u015f", "\u0219")
    t = t.replace("\u0162", "\u021a").replace("\u0163", "\u021b")
    # Normalize CRLF to LF
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    return t


def quotes_match_tolerant(quote: str, source: str) -> bool:
    """Tolerantly matches quotes accounting for Romanian diacritic variants and whitespace."""
    if not quote or not source:
        return False
    norm_q = normalize_romanian_text(quote).strip().lower()
    norm_s = normalize_romanian_text(source).strip().lower()

    if norm_q in norm_s:
        return True

    # Secondary check: collapsing all whitespace
    collapse_q = re.sub(r"\s+", " ", norm_q)
    collapse_s = re.sub(r"\s+", " ", norm_s)
    return collapse_q in collapse_s


class NormalizedProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reading_level: Literal["standard", "simple", "very_simple"] = "simple"
    format: Literal["steps", "short_paragraphs", "bullets"] = "steps"
    focus_level: int = Field(default=0, ge=0, le=3)
    needs_notes: str | None = None
    max_sentence_words: int = Field(default=12, ge=4, le=50)
    bionic: bool = False
    reading_ruler: bool = False
    warnings: list[str] = Field(default_factory=list)


def normalize_profile(raw: Any) -> NormalizedProfile:
    """Normalizes any user profile dict or object with alias maps.

    Never raises an HTTP 422 error. Unknown values are cleanly mapped to defaults
    with an explanatory warning.
    """
    if raw is None:
        return NormalizedProfile()

    if isinstance(raw, NormalizedProfile):
        return raw

    warnings: list[str] = []
    data: dict[str, Any] = {}

    if hasattr(raw, "model_dump"):
        data = raw.model_dump()
    elif isinstance(raw, dict):
        data = dict(raw)
    else:
        warnings.append(
            f"Format profil necunoscut ({type(raw).__name__}); s-au aplicat valorile implicite."
        )
        return NormalizedProfile(warnings=warnings)

    # 1. Reading level normalization
    raw_level = (
        data.get("reading_level") or data.get("level") or data.get("readingPace")
    )
    reading_level: Literal["standard", "simple", "very_simple"] = "simple"
    if raw_level:
        s = str(raw_level).lower().strip()
        if s in ("standard", "detailed", "complex", "high", "normal", "fast"):
            reading_level = "standard"
            if s not in ("standard",):
                warnings.append(f"Nivel citire '{s}' mapat la 'standard'.")
        elif s in (
            "very_simple",
            "very-simple",
            "minimal",
            "ultra_simple",
            "easy_read",
            "easy-read",
            "slow",
        ):
            reading_level = "very_simple"
            if s not in ("very_simple",):
                warnings.append(f"Nivel citire '{s}' mapat la 'very_simple'.")
        elif s in ("simple", "medium", "standard_simple"):
            reading_level = "simple"
        else:
            warnings.append(f"Nivel citire nerecunoscut '{s}'; s-a folosit 'simple'.")

    # 2. Format normalization
    raw_format = data.get("format") or data.get("text_format")
    format_mode: Literal["steps", "short_paragraphs", "bullets"] = "steps"
    if raw_format:
        f = str(raw_format).lower().strip()
        if f in (
            "paragraphs",
            "short_paragraphs",
            "short-paragraphs",
            "paragraph",
            "cursive",
            "text",
        ):
            format_mode = "short_paragraphs"
            if f not in ("short_paragraphs",):
                warnings.append(f"Format '{f}' mapat la 'short_paragraphs'.")
        elif f in ("bullets", "bullet_points", "list", "buline"):
            format_mode = "bullets"
            if f not in ("bullets",):
                warnings.append(f"Format '{f}' mapat la 'bullets'.")
        elif f in ("steps", "step_by_step", "step-by-step", "pasi"):
            format_mode = "steps"
        else:
            warnings.append(f"Format nerecunoscut '{f}'; s-a folosit 'steps'.")

    # 3. Focus level
    raw_focus = data.get("focus_level") or data.get("focus") or 0
    try:
        focus_level = max(0, min(3, int(raw_focus)))
    except (ValueError, TypeError):
        focus_level = 0
        warnings.append("Focus level invalid; resetat la 0.")

    # 4. Max sentence words
    raw_words = data.get("max_sentence_words") or 12
    try:
        max_words = max(4, min(50, int(raw_words)))
    except (ValueError, TypeError):
        max_words = 12

    # 5. Needs notes (clean and clamp)
    raw_notes = (
        data.get("needs_notes")
        or data.get("notes")
        or data.get("user_words")
        or data.get("freeform_needs")
    )
    needs_notes = str(raw_notes).strip()[:500] if raw_notes else None

    # 6. Booleans
    bionic = bool(data.get("bionic", False))
    ruler = bool(data.get("reading_ruler", False))

    return NormalizedProfile(
        reading_level=reading_level,
        format=format_mode,
        focus_level=focus_level,
        needs_notes=needs_notes,
        max_sentence_words=max_words,
        bionic=bionic,
        reading_ruler=ruler,
        warnings=warnings,
    )
