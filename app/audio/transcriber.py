"""app/audio/transcriber.py - Speech-to-text transcription engine.

Supports:
- Groq Whisper (whisper-large-v3-turbo) via OpenAI-compatible audio API.
- Local ffmpeg downsampling to 16 kHz mono mp3 when files exceed 25 MB.
- Deterministic mock provider for tests and offline/mock mode.
- Disability safety: Text only, zero emotion/voice trait inference.
- Privacy: All temporary files deleted in finally blocks.
"""

import asyncio
import logging
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Tuple

import httpx

from app.audio.captions import segments_to_srt, segments_to_vtt
from app.config import settings
from app.schemas.common import AppError, MetaInfo
from app.schemas.transcribe import (
    TranscribeCaptions,
    TranscribeResponseData,
    TranscribeSegment,
)

logger = logging.getLogger("primazi.audio")

# Deterministic Romanian mock transcript
MOCK_SEGMENTS = [
    TranscribeSegment(
        start=0.0,
        end=4.5,
        text="Bun găsit tuturor, începem ședința de organizare pentru prima zi de lucru.",
    ),
    TranscribeSegment(
        start=4.5,
        end=9.8,
        text="Avem de finalizat completarea fișei de acces până miercuri la prânz.",
    ),
    TranscribeSegment(
        start=9.8,
        end=14.5,
        text="Vă rugăm să trimiteți confirmarea pe email direct coordonatorului de echipă.",
    ),
]
MOCK_DURATION = 15.0
MOCK_LANGUAGE = "ro"
MOCK_FULL_TEXT = " ".join(seg.text for seg in MOCK_SEGMENTS)


async def _shrink_audio_if_needed(file_path: Path) -> Path:
    """Downsample audio to 16 kHz mono mp3 using ffmpeg if size > 25 MB."""
    file_size = file_path.stat().st_size
    max_groq_size = 25 * 1024 * 1024  # 25 MB

    if file_size <= max_groq_size:
        return file_path

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise AppError(
            code="file_too_large",
            message_ro="Fișierul depășește limita de 25 MB, iar utilitarul ffmpeg pentru comprimare nu este disponibil.",
            status_code=400,
        )

    shrunk_path = file_path.with_name(f"{file_path.stem}_shrunk.mp3")
    try:
        proc = await asyncio.create_subprocess_exec(
            ffmpeg_bin,
            "-y",
            "-i",
            str(file_path),
            "-ar",
            "16000",
            "-ac",
            "1",
            "-b:a",
            "48k",
            str(shrunk_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, _ = await proc.communicate()
        if proc.returncode != 0 or not shrunk_path.exists():
            raise AppError(
                code="audio_compression_failed",
                message_ro="Comprimarea fișierului audio a eșuat.",
                status_code=400,
            )

        if shrunk_path.stat().st_size > max_groq_size:
            shrunk_path.unlink(missing_ok=True)
            raise AppError(
                code="file_too_large",
                message_ro="Chiar și după comprimare, fișierul audio depășește limita permisă de 25 MB.",
                status_code=400,
            )

        return shrunk_path
    except Exception as exc:
        if isinstance(exc, AppError):
            raise exc
        raise AppError(
            code="audio_compression_failed",
            message_ro=f"Eroare la procesarea audio: {str(exc)}",
            status_code=400,
        )


async def transcribe_audio(
    file_path: Path,
    original_filename: str,
    language: str = "ro",
    timestamps: bool = True,
) -> Tuple[TranscribeResponseData, MetaInfo]:
    """Transcribe audio file into text and SRT/VTT subtitles.

    Args:
        file_path: Path to temporary audio file on disk.
        original_filename: Name of the uploaded file for logging/mimetype.
        language: ISO language code (default 'ro').
        timestamps: Whether timestamped segments are requested.

    Returns:
        Tuple of (TranscribeResponseData, MetaInfo).
    """
    provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER).lower()
    has_groq = bool(settings.GROQ_API_KEY.strip())

    # Mock mode or missing Groq API credentials
    if provider == "mock" or not has_groq:
        srt = segments_to_srt(MOCK_SEGMENTS)
        vtt = segments_to_vtt(MOCK_SEGMENTS)
        captions = TranscribeCaptions(srt=srt, vtt=vtt)
        data = TranscribeResponseData(
            language=MOCK_LANGUAGE,
            duration_s=MOCK_DURATION,
            text=MOCK_FULL_TEXT,
            segments=MOCK_SEGMENTS if timestamps else [],
            captions=captions,
        )
        meta = MetaInfo(
            provider="mock",
            cached=False,
            warnings=[],
            ai_notice_ro="Transcriere mock generată pentru testare și dezvoltare.",
        )
        return data, meta

    # Groq Whisper API execution
    shrunk_file_path: Path | None = None
    try:
        effective_path = await _shrink_audio_if_needed(file_path)
        if effective_path != file_path:
            shrunk_file_path = effective_path

        base_url = settings.GROQ_BASE_URL.rstrip("/")
        endpoint_url = f"{base_url}/audio/transcriptions"

        mime_type = mimetypes.guess_type(effective_path.name)[0] or "audio/mpeg"
        async with httpx.AsyncClient(timeout=float(settings.LLM_TIMEOUT_SECONDS * 2)) as client:
            with open(effective_path, "rb") as audio_file:
                files = {
                    "file": (
                        effective_path.name,
                        audio_file,
                        mime_type,
                    )
                }
                form_data = {
                    "model": "whisper-large-v3-turbo",
                    "language": language or "ro",
                    "response_format": "verbose_json",
                }
                headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}

                response = await client.post(
                    endpoint_url,
                    headers=headers,
                    data=form_data,
                    files=files,
                )

        if response.status_code == 429:
            raise AppError(
                code="transcribe_rate_limited",
                message_ro="Serviciul de transcriere este temporar suprasolicitat. Te rugăm să încerci din nou în câteva momente.",
                status_code=429,
            )

        if response.status_code != 200:
            logger.error(f"[TRANSCRIBE ERROR] Groq API returned {response.status_code}: {response.text}")
            raise AppError(
                code="transcribe_failed",
                message_ro="A apărut o eroare la transcrierea fișierului audio.",
                status_code=502,
            )

        payload = response.json()
        raw_text = payload.get("text", "").strip()
        duration_s = float(payload.get("duration", 0.0))
        detected_lang = payload.get("language", language or "ro")
        raw_segments = payload.get("segments", [])

        parsed_segments: list[TranscribeSegment] = []
        for seg in raw_segments:
            parsed_segments.append(
                TranscribeSegment(
                    start=float(seg.get("start", 0.0)),
                    end=float(seg.get("end", 0.0)),
                    text=str(seg.get("text", "")).strip(),
                )
            )

        if not parsed_segments and raw_text:
            parsed_segments.append(
                TranscribeSegment(
                    start=0.0,
                    end=max(duration_s, 1.0),
                    text=raw_text,
                )
            )

        srt = segments_to_srt(parsed_segments)
        vtt = segments_to_vtt(parsed_segments)
        captions = TranscribeCaptions(srt=srt, vtt=vtt)

        data = TranscribeResponseData(
            language=detected_lang,
            duration_s=duration_s,
            text=raw_text,
            segments=parsed_segments if timestamps else [],
            captions=captions,
        )
        meta = MetaInfo(
            provider="groq",
            cached=False,
            warnings=[],
            ai_notice_ro="Generat prin Groq Whisper v3 — verifică datele importante.",
        )
        return data, meta
    finally:
        if shrunk_file_path and shrunk_file_path.exists():
            try:
                shrunk_file_path.unlink(missing_ok=True)
            except Exception:
                pass

