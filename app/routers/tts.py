"""FastAPI router for server-side TTS fallback.
Endpoint: POST /api/tts

Ref: docs/CONTRACTS-WAVE2.md, docs/TASKS-WAVE2.md A8
"""
from typing import Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel, ConfigDict

from app.schemas.common import AppError
from app.tts.engine import synthesize_speech
from app.tts.normalize_ro import normalize_ro_speech

router = APIRouter(prefix="/api", tags=["tts"])


class TTSRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: Optional[str] = None
    voice: str = "ro-mihai"
    rate: float = 1.0
    pause_ms: int = 350


@router.post("/tts")
async def tts_endpoint(payload: TTSRequest):
    """Generates spoken WAV audio from Romanian text.
    Normalizes dates, numbers, legal citations, and abbreviations.
    Returns audio/wav bytes with transparency headers.
    """
    if payload.text is None or not payload.text.strip():
        raise AppError(
            code="empty_input",
            message_ro="Textul pentru sinteză vocală nu poate fi gol.",
            status_code=400,
        )

    if len(payload.text) > 2000:
        raise AppError(
            code="too_long",
            message_ro="Textul depășește limita maximă de 2000 de caractere.",
            status_code=400,
        )

    # Clamping rate within sensible bounds (0.5 to 2.0)
    rate = max(0.5, min(2.0, float(payload.rate)))

    # 1. Normalize text for Romanian speech
    normalized = normalize_ro_speech(payload.text)

    # 2. Synthesize audio
    wav_bytes, engine_name = synthesize_speech(
        text=normalized,
        voice=payload.voice,
        rate=rate,
    )

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={
            "X-TTS-Engine": engine_name,
            "Cache-Control": "public, max-age=3600",
        },
    )

