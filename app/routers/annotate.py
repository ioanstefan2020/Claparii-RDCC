import time
from typing import Any

from fastapi import APIRouter, HTTPException

from app.annotate.deterministic import extract_deterministic_highlights
from app.llm import generate_json
from app.prompts import annotate as annotate_prompt
from app.schemas.annotate import (
    AnnotateData,
    AnnotateRequest,
    AnnotationItem,
    GlossaryItem,
    HighlightItem,
)
from app.schemas.common import ApiResponse, MetaInfo
from app.schemas.profile_norm import normalize_profile

router = APIRouter(prefix="/api", tags=["annotate"])

CATEGORY_PRIORITY = {
    "deadline": 1,
    "warning": 2,
    "action": 3,
    "person": 4,
    "number": 5,
    "term": 6,
}


def _cap_highlights(
    highlights: list[HighlightItem], text: str, mode: str
) -> list[HighlightItem]:
    """Caps highlights density according to SETTINGS-SPEC §5."""
    if mode == "off":
        return []

    words = [w for w in text.split() if w.strip()]
    word_count = len(words)
    if word_count == 0:
        return []

    if mode == "light":
        max_allowed = max(2, int(word_count * 0.05))
    elif mode == "medium":
        max_allowed = max(3, int(word_count * 0.10))
    elif mode == "strong":
        max_allowed = max(5, int(word_count * 0.15))
    else:
        max_allowed = len(highlights)

    if len(highlights) <= max_allowed:
        return highlights

    # Prioritize deadlines, warnings, and actions, then sort back by offset
    prioritized = sorted(
        highlights,
        key=lambda h: (CATEGORY_PRIORITY.get(h.category, 99), h.start),
    )
    selected = prioritized[:max_allowed]
    selected.sort(key=lambda h: h.start)
    return selected


@router.post("/annotate", response_model=ApiResponse[AnnotateData])
async def annotate_text(req: AnnotateRequest) -> ApiResponse[AnnotateData]:
    """Extracts deterministic + semantic highlights, tone notes, and glossary.

    Conforms to CONTRACTS-WAVE2 and SETTINGS-SPEC §5.
    """
    start_time = time.monotonic()
    text = req.text or ""
    if not text.strip():
        return ApiResponse(
            ok=True,
            data=AnnotateData(highlights=[], annotations=[], glossary=[]),
            meta=MetaInfo(
                provider="deterministic",
                cached=False,
                warnings=["Text gol trimis pentru adnotare."],
                ai_notice_ro="Generat de AI — verifică datele importante.",
                latency_ms=0,
                prompt_version=annotate_prompt.VERSION,
                provider_chain_tried=["deterministic"],
            ),
        )

    norm_profile = normalize_profile(req.profile)
    prof_warnings = norm_profile.warnings
    effective_mode = req.highlight_mode

    layers = req.layers or ["deterministic", "semantic", "tone", "glossary"]

    all_highlights: list[HighlightItem] = []
    annotations: list[AnnotationItem] = []
    glossary: list[GlossaryItem] = []
    warnings: list[str] = list(prof_warnings)
    provider_used = "deterministic"
    chain_tried = ["deterministic"]
    prompt_ver = annotate_prompt.VERSION

    # 1. Deterministic layer
    if "deterministic" in layers:
        det_matches = extract_deterministic_highlights(text)
        for m in det_matches:
            all_highlights.append(
                HighlightItem(
                    start=m["start"],
                    end=m["end"],
                    category=m["category"],
                    text=m["text"],
                )
            )

    # 2. Semantic, Tone, Glossary layers via LLM
    needs_llm = any(l in layers for l in ("semantic", "tone", "glossary"))
    if needs_llm:
        try:
            llm_result, meta_dict = await generate_json(
                task="annotate",
                system=annotate_prompt.SYSTEM,
                user=annotate_prompt.build_user(text, layers),
                schema=AnnotateData,
                mock=annotate_prompt.MOCK,
                prompt_version=annotate_prompt.VERSION,
            )
            provider_used = meta_dict.get("provider", "mock")
            chain_tried = meta_dict.get("provider_chain_tried", [provider_used])
            prompt_ver = meta_dict.get("prompt_version", annotate_prompt.VERSION)
            warnings.extend(meta_dict.get("warnings", []))

            # Merge semantic highlights
            if "semantic" in layers and llm_result.highlights:
                # Existing covered intervals from deterministic
                existing_intervals = [(h.start, h.end) for h in all_highlights]

                for h in llm_result.highlights:
                    # Validate offsets
                    if not (0 <= h.start < h.end <= len(text)):
                        continue
                    # Check text matches
                    actual_slice = text[h.start : h.end]
                    if actual_slice != h.text:
                        # Try case-insensitive or stripped match
                        if actual_slice.strip().lower() == h.text.strip().lower():
                            h.text = actual_slice
                        else:
                            continue

                    # Check collision with deterministic highlights
                    collision = any(
                        not (h.end <= start or h.start >= end)
                        for start, end in existing_intervals
                    )
                    if not collision:
                        all_highlights.append(h)
                        existing_intervals.append((h.start, h.end))

            # Tone annotations
            if "tone" in layers and llm_result.annotations:
                for a in llm_result.annotations:
                    if not (0 <= a.start < a.end <= len(text)):
                        continue
                    # Double-check evidence_quote presence
                    if a.evidence_quote and a.evidence_quote not in text:
                        continue
                    # Ensure confidence is low or medium
                    if a.confidence not in ("low", "medium"):
                        a.confidence = "medium"
                    # Enforce "posibil... — nesigur" on joke/irony
                    if (
                        a.kind in ("joke", "irony")
                        and "nesigur" not in a.note_ro.lower()
                    ):
                        prefix = (
                            "posibilă glumă — nesigur"
                            if a.kind == "joke"
                            else "posibilă ironie — nesigur"
                        )
                        a.note_ro = f"({prefix}: {a.note_ro.strip('()')})"
                    annotations.append(a)

            # Glossary
            if "glossary" in layers and llm_result.glossary:
                glossary = llm_result.glossary

        except Exception as e:
            warnings.append(
                f"Adnotarea semantică AI nu a fost disponibilă: {str(e)[:100]}"
            )

    # Sort all highlights by start
    all_highlights.sort(key=lambda h: h.start)

    # 3. Apply density caps
    final_highlights = _cap_highlights(all_highlights, text, effective_mode)

    latency_ms = int((time.monotonic() - start_time) * 1000)

    return ApiResponse(
        ok=True,
        data=AnnotateData(
            highlights=final_highlights,
            annotations=annotations,
            glossary=glossary,
        ),
        meta=MetaInfo(
            provider=provider_used,
            cached=False,
            warnings=warnings,
            ai_notice_ro="Generat de AI — verifică datele importante.",
            latency_ms=latency_ms,
            prompt_version=prompt_ver,
            provider_chain_tried=chain_tried,
        ),
    )
