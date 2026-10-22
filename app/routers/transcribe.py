"""app/routers/transcribe.py - Audio transcription endpoint producing text + captions."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from app.audio.transcriber import transcribe_audio
from app.schemas.common import AppError, SuccessEnvelope
from app.schemas.transcribe import TranscribeResponseData

router = APIRouter(prefix="/api/transcribe", tags=["transcribe"])

ALLOWED_EXTENSIONS = {
    "mp3",
    "mp4",
    "mpeg",
    "mpga",
    "m4a",
    "ogg",
    "wav",
    "webm",
    "flac",
    "aac",
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB hard ceiling


@router.post("", response_model=SuccessEnvelope[TranscribeResponseData])
@router.post("/", response_model=SuccessEnvelope[TranscribeResponseData], include_in_schema=False)
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form("ro"),
    timestamps: str = Form("true"),
):
    """Transcribe uploaded audio file into text, segments, and SRT/VTT subtitles.

    Privacy & A11y:
    - Audio is saved to a secure tempfile and deleted in finally.
    - No audio or user document data is permanently stored or logged.
    - Text only: no emotion or speaker personality inferences.
    """
    include_timestamps = str(timestamps).lower() not in ("false", "0", "no", "off")
    # 1. Validate file extension
    orig_name = file.filename or ""
    suffix = Path(orig_name).suffix.lower().lstrip(".")
    if not suffix or suffix not in ALLOWED_EXTENSIONS:
        raise AppError(
            code="invalid_audio_format",
            message_ro="Format audio neacceptat. Formate permise: mp3, wav, m4a, ogg, webm, flac, aac.",
            status_code=400,
        )

    # 2. Read contents & validate size
    contents = await file.read()
    if not contents or len(contents) == 0:
        raise AppError(
            code="empty_file",
            message_ro="Fișierul audio încărcat este gol.",
            status_code=400,
        )

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise AppError(
            code="file_too_large",
            message_ro="Fișierul depășește limita maximă de 50 MB permisă pentru încărcare.",
            status_code=400,
        )

    # 3. Save to temporary file, process, and clean up in finally
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(contents)
            tmp_path = Path(tmp.name)

        data, meta = await transcribe_audio(
            file_path=tmp_path,
            original_filename=orig_name,
            language=language,
            timestamps=include_timestamps,
        )
        return SuccessEnvelope(ok=True, data=data, meta=meta)
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
