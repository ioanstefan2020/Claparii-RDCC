import re
import time
from typing import Any

from fastapi import APIRouter

from app.llm import generate_json
from app.prompts import transform as transform_prompt
from app.prompts.base import apply_custom_decorations
from app.schemas.common import ApiResponse, AppError, MetaInfo
from app.schemas.profile_norm import normalize_profile
from app.schemas.transform import TransformData, TransformRequest

router = APIRouter(prefix="/api", tags=["transform"])

LIST_MODES = {"bullets", "steps", "questions", "glossary"}
PROSE_MODES = {"shorter", "tldr", "easy_read", "rewrite"}


@router.post("/transform", response_model=ApiResponse[TransformData])
async def transform_text(req: TransformRequest) -> ApiResponse[TransformData]:
    """Transforms text into bullets, steps, questions, glossary, shorter, tldr, easy_read, or rewrite.

    Conforms to CONTRACTS-WAVE2 specifications.
    """
    start_time = time.monotonic()
    text = (req.text or "").strip()
    if not text:
        raise AppError(
            code="empty_input",
            message_ro="Textul trimis pentru transformare este gol.",
            status_code=400,
        )

    norm_profile = normalize_profile(req.profile)
    prof_warnings = list(norm_profile.warnings)

    mode = req.mode if req.mode in (LIST_MODES | PROSE_MODES) else "bullets"
    mock_payload = transform_prompt.MOCKS.get(mode, transform_prompt.MOCKS["bullets"])

    user_prompt = transform_prompt.build_user(
        text=text,
        mode=mode,
        max_items=req.max_items,
        target_pct=req.target_pct,
        profile=req.profile,
    )

    validated_model, meta_dict = await generate_json(
        task="transform",
        system=transform_prompt.SYSTEM,
        user=user_prompt,
        schema=TransformData,
        mock=mock_payload,
        prompt_version=transform_prompt.VERSION,
    )

    items = validated_model.items
    out_text = validated_model.text
    warnings = prof_warnings + list(meta_dict.get("warnings", []))

    # Clean and enforce shape based on mode
    if mode in LIST_MODES:
        if not items and out_text:
            lines = [
                re.sub(r"^[\s\d\.\-\*•]+", "", l).strip()
                for l in out_text.split("\n")
                if l.strip()
            ]
            items = lines or [out_text.strip()]
        elif not items:
            items = ["Informația din text a fost procesată."]

        if req.max_items and len(items) > req.max_items:
            items = items[: req.max_items]

        if norm_profile.needs_notes and items:
            items = [
                apply_custom_decorations(it, norm_profile.needs_notes) for it in items
            ]

        out_text = None
    else:
        # Prose mode
        if not out_text and items:
            out_text = " ".join(items)
        elif not out_text:
            out_text = text

        if norm_profile.needs_notes and out_text:
            out_text = apply_custom_decorations(out_text, norm_profile.needs_notes)

        items = None

    latency_ms = int((time.monotonic() - start_time) * 1000)

    return ApiResponse(
        ok=True,
        data=TransformData(
            mode=mode,
            items=items,
            text=out_text,
        ),
        meta=MetaInfo(
            provider=meta_dict.get("provider", "mock"),
            cached=meta_dict.get("cached", False),
            warnings=warnings,
            ai_notice_ro="Generat de AI — verifică datele importante.",
            latency_ms=latency_ms,
            prompt_version=transform_prompt.VERSION,
            provider_chain_tried=meta_dict.get("provider_chain_tried", ["mock"]),
        ),
    )
