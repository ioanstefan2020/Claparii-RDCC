import base64
import os
import time
from typing import Any

import httpx
from fastapi import APIRouter, File, Form, UploadFile

from app.config import settings
from app.prompts import describe_image as prompt_mod
from app.schemas.common import ApiResponse, AppError, MetaInfo
from app.schemas.describe_image import DescribeImageData, DescribeImagePurpose

router = APIRouter(prefix="/api", tags=["describe-image"])

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}


async def _call_gemini_vision(
    image_bytes: bytes, mime_type: str, purpose: str
) -> dict[str, Any] | None:
    api_key = os.getenv("GEMINI_API_KEY", getattr(settings, "GEMINI_API_KEY", ""))
    if not api_key:
        return None

    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    user_instructions = (
        f"Scopul analizei imaginii: {purpose}. Respectă schema JSON cerută."
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{prompt_mod.SYSTEM}\n\n{user_instructions}"},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_data,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                import json

                result = resp.json()
                text_part = (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                if text_part:
                    return json.loads(text_part)
    except Exception:
        pass
    return None


@router.post("/describe-image", response_model=ApiResponse[DescribeImageData])
async def describe_image(
    file: UploadFile = File(...),
    purpose: DescribeImagePurpose = Form("alt_text"),
) -> ApiResponse[DescribeImageData]:
    """Describes images and extracts visual text for accessibility.

    Supports alt_text, read_text, chart, and document modes (≤ 5 MB).
    Conforms to CONTRACTS-WAVE2 specifications.
    """
    start_time = time.monotonic()
    content = await file.read()

    if len(content) > MAX_IMAGE_SIZE:
        raise AppError(
            code="too_large",
            message_ro="Imaginea depășește limita maximă permisă de 5 MB.",
            status_code=400,
        )

    if not content or len(content.strip()) == 0:
        raise AppError(
            code="empty_input",
            message_ro="Fișierul imagine este gol.",
            status_code=400,
        )

    mime_type = file.content_type or "image/jpeg"
    if mime_type not in ALLOWED_TYPES and not file.filename.lower().endswith(
        (".jpg", ".jpeg", ".png", ".webp")
    ):
        raise AppError(
            code="unsupported_type",
            message_ro="Format imagine nesuportat. Formate acceptate: JPG, PNG, WEBP.",
            status_code=400,
        )

    effective_purpose = (
        purpose
        if purpose in ("alt_text", "read_text", "chart", "document")
        else "alt_text"
    )

    provider_used = "mock"
    chain_tried = []
    vision_result = None

    # Try Gemini vision if configured and not mock forced
    if os.getenv("LLM_PROVIDER") != "mock":
        chain_tried.append("gemini_vision")
        vision_result = await _call_gemini_vision(content, mime_type, effective_purpose)
        if vision_result:
            provider_used = "gemini_vision"

    if not vision_result:
        chain_tried.append("mock")
        mock_data = prompt_mod.MOCK_DESCRIPTIONS.get(
            effective_purpose, prompt_mod.MOCK_DESCRIPTIONS["alt_text"]
        )
        vision_result = dict(mock_data)

    desc_ro = vision_result.get(
        "description_ro", "Descrierea imaginii a fost procesată."
    )
    text_found = vision_result.get("text_found")
    conf_note = vision_result.get(
        "confidence_note",
        "Descriere generată de AI — verifică datele sau textul important cu o persoană de sprijin.",
    )

    latency_ms = int((time.monotonic() - start_time) * 1000)

    return ApiResponse(
        ok=True,
        data=DescribeImageData(
            description_ro=desc_ro,
            text_found=text_found,
            confidence_note=conf_note,
            purpose=effective_purpose,
        ),
        meta=MetaInfo(
            provider=provider_used,
            cached=False,
            warnings=[],
            ai_notice_ro="Generat de AI — verifică datele importante.",
            latency_ms=latency_ms,
            prompt_version=prompt_mod.VERSION,
            provider_chain_tried=chain_tried,
        ),
    )
