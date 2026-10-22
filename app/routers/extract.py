import io
import re
import time
from typing import Any

from fastapi import APIRouter, File, UploadFile

from app.ingest import IngestError, extract_text_from_file
from app.schemas.common import ApiResponse, AppError, MetaInfo
from app.schemas.extract import ExtractTextData

router = APIRouter(prefix="/api", tags=["extract"])

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def _clean_html(raw_html: str) -> str:
    # Remove script and style tags
    clean = re.sub(
        r"<(script|style)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE
    )
    # Remove all HTML tags
    clean = re.sub(r"<[^>]+>", " ", clean)
    # Normalize whitespaces
    clean = re.sub(r"[ \t]+", " ", clean)
    clean = re.sub(r"\n\s*\n", "\n\n", clean)
    return clean.strip()


@router.post("/extract-text", response_model=ApiResponse[ExtractTextData])
async def extract_text(file: UploadFile = File(...)) -> ApiResponse[ExtractTextData]:
    """In-memory extraction for PDF, DOCX, TXT, MD, and HTML files (≤ 10 MB).

    Never writes to disk. Detects scanned PDFs requiring OCR.
    Conforms to CONTRACTS-WAVE2 specifications.
    """
    start_time = time.monotonic()
    filename = file.filename or "document.txt"
    content = await file.read()

    if len(content) > MAX_UPLOAD_SIZE:
        raise AppError(
            code="too_large",
            message_ro="Fișierul depășește limita maximă permisă de 10 MB.",
            status_code=400,
        )

    if not content or len(content.strip()) == 0:
        raise AppError(
            code="empty_input",
            message_ro="Fișierul încărcat este gol.",
            status_code=400,
        )

    lower_name = filename.lower()
    text = ""
    pages = 1
    needs_ocr = False
    fmt = "txt"

    try:
        # 1. HTML
        if lower_name.endswith(".html") or lower_name.endswith(".htm"):
            fmt = "html"
            for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1250"):
                try:
                    decoded = content.decode(enc)
                    text = _clean_html(decoded)
                    break
                except UnicodeDecodeError:
                    continue
            if not text:
                text = _clean_html(content.decode("utf-8", errors="replace"))

        # 2. PDF
        elif lower_name.endswith(".pdf") or content.startswith(b"%PDF-"):
            fmt = "pdf"
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(content))
            pages = max(1, len(reader.pages))
            page_chunks: list[str] = []
            for p in reader.pages:
                t = p.extract_text()
                if t and t.strip():
                    page_chunks.append(t.strip())
            text = "\n\n".join(page_chunks).strip()
            if not text:
                # Scanned image PDF without selectable text
                needs_ocr = True
                text = ""

        # 3. DOCX, TXT, MD, EML via ingest engine
        else:
            try:
                extracted, detected_fmt = extract_text_from_file(content, filename)
                text = extracted
                fmt = detected_fmt
            except IngestError as ie:
                if ie.code == "empty_input" and fmt == "pdf":
                    needs_ocr = True
                    text = ""
                else:
                    code_mapped = (
                        "too_large" if ie.code == "file_too_large" else ie.code
                    )
                    raise AppError(
                        code=code_mapped,
                        message_ro=ie.message_ro,
                        status_code=400,
                    )

    except AppError:
        raise
    except Exception as e:
        raise AppError(
            code="corrupted_file",
            message_ro=f"Eroare la parsarea fișierului '{filename}': {str(e)[:100]}",
            status_code=400,
        )

    latency_ms = int((time.monotonic() - start_time) * 1000)

    return ApiResponse(
        ok=True,
        data=ExtractTextData(
            text=text,
            pages=pages,
            truncated=False,
            format=fmt,
            needs_ocr=needs_ocr,
        ),
        meta=MetaInfo(
            provider="local_extractor",
            cached=False,
            warnings=["Documentul scanat necesită OCR pentru extragerea textului."]
            if needs_ocr
            else [],
            ai_notice_ro="Generat de AI — verifică datele importante.",
            latency_ms=latency_ms,
            prompt_version="2.0",
            provider_chain_tried=["local_extractor"],
        ),
    )
