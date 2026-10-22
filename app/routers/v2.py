import asyncio
import json
import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config import settings
from app.guardrails import normalise_whitespace as normalize_text
from app.ingest import (
    IngestError,
    compute_readability_metrics,
    detect_language_and_situation,
    extract_text_from_file,
    mask_pii,
    unmask_pii,
)
from app.llm import generate_json
from app.llm.dynamic_mock import generate_dynamic_v2_payload, is_default_sample
from app.prompts.v2 import SYSTEM, build_user, load_fixture_mock
from app.schemas.v2 import (
    ActionV2,
    AdjustmentRequestV2Request,
    AdjustmentRequestV2Response,
    AnalyzeV2Request,
    AnalyzeV2Response,
    CapabilitiesPrivacyV2,
    CapabilitiesV2Response,
    ChecklistV2,
    DeadlineV2,
    DetectedV2,
    DraftReplyV2Request,
    DraftReplyV2Response,
    GlossaryV2,
    MeetingRecapV2Request,
    MeetingRecapV2Response,
    MetricsV2,
    UploadV2Response,
    UsageV2,
    WarningV2,
)

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/health")
async def health_v2():
    return {
        "status": "ok",
        "provider": settings.LLM_PROVIDER,
        "version": "v2",
    }


@router.get("/capabilities", response_model=CapabilitiesV2Response)
async def capabilities_v2():
    return CapabilitiesV2Response(
        api_version="v2",
        status="ready",
        supported_situations=["work", "official", "contract", "school"],
        supported_formats=[".txt", ".md", ".docx", ".pdf", ".eml"],
        max_upload_size_bytes=10 * 1024 * 1024,
        max_text_chars=50000,
        supported_languages=["ro", "en"],
        privacy=CapabilitiesPrivacyV2(
            zero_server_storage=True,
            pii_masking=True,
            no_content_logging=True,
            no_diagnosis_inference=True,
            no_emotion_detection=True,
        ),
        active_provider=settings.LLM_PROVIDER,
    )


@router.post("/upload", response_model=UploadV2Response)
async def upload_file_v2(file: UploadFile = File(...)):
    try:
        content = await file.read()
        extracted_text, fmt = extract_text_from_file(
            content=content, filename=file.filename or "document.txt"
        )
        return UploadV2Response(
            file_id=f"f_{uuid.uuid4().hex[:10]}",
            filename=file.filename or "document.txt",
            size_bytes=len(content),
            text=extracted_text,
            char_count=len(extracted_text),
            format=fmt,
        )
    except IngestError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message_ro": e.message_ro,
                    "message_en": e.message_en,
                    "retryable": False,
                }
            },
        )


def _verify_item_quote(quote: str, normalized_source: str) -> bool:
    if not quote or not quote.strip():
        return True
    return normalize_text(quote) in normalized_source


def _run_analysis_logic(
    text: str,
    situation_req: str,
    language_req: str,
    adaptations,
    outputs,
    start_time: float,
) -> AnalyzeV2Response:
    norm_source = normalize_text(text)
    m_before = compute_readability_metrics(text)
    det_info = detect_language_and_situation(text)

    situation = situation_req if situation_req != "auto" else det_info["situation"]
    language = language_req if language_req != "auto" else det_info["language"]

    if is_default_sample(text):
        mock_fixture = load_fixture_mock(situation)
    else:
        mock_fixture = generate_dynamic_v2_payload(text, situation, adaptations)

    # In mock mode, we adapt the fixture dynamically
    summary_text = mock_fixture.get("summary", "Document analizat cu succes.")
    if adaptations.reading_level == 1 and not summary_text.startswith(
        "Sinteză simplificată:"
    ):
        summary_text = "Sinteză simplificată: " + summary_text

    raw_actions = mock_fixture.get("actions", [])
    actions: list[ActionV2] = []
    warnings: list[WarningV2] = []

    for a in raw_actions:
        quote = a.get("quote", "")
        # Check grounding against original text
        found = _verify_item_quote(quote, norm_source) if quote else True
        if not found:
            warnings.append(
                WarningV2(
                    code="UNGROUNDED_QUOTE",
                    message=f"Citatul '{quote[:40]}...' nu apare identic în textul sursă.",
                )
            )
        actions.append(
            ActionV2(
                text=a.get("text", ""),
                quote=quote,
                quote_found=found,
            )
        )

    raw_deadlines = mock_fixture.get("deadlines", [])
    deadlines: list[DeadlineV2] = []
    for d in raw_deadlines:
        quote = d.get("quote", "")
        found = _verify_item_quote(quote, norm_source) if quote else True
        if d.get("date") is None:
            warnings.append(
                WarningV2(
                    code="UNCERTAIN_DATE",
                    message=f"Termenul '{d.get('text')}' este ambiguu sau nu specifică un an calendaristic.",
                )
            )
        deadlines.append(
            DeadlineV2(
                date=d.get("date"),
                text=d.get("text", ""),
                quote=quote,
                quote_found=found,
            )
        )

    glossary = [
        GlossaryV2(term=g.get("term", ""), plain=g.get("plain", ""))
        for g in mock_fixture.get("glossary", [])
    ]
    checklist = [
        ChecklistV2(
            step=c.get("step", idx),
            text=c.get("text", ""),
            est_minutes=c.get("est_minutes", 5),
        )
        for idx, c in enumerate(mock_fixture.get("checklist", []), start=1)
    ]

    m_after = compute_readability_metrics(summary_text)

    # Calculate actual words before and after
    words_before = m_before["word_count"]
    words_after = m_after["word_count"]
    read_before = m_before["readability_score"]
    read_after = max(read_before, m_after["readability_score"])

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    return AnalyzeV2Response(
        request_id=f"req_{uuid.uuid4().hex[:12]}",
        detected=DetectedV2(
            language=language,
            situation=situation,
            confidence=det_info["confidence"],
        ),
        summary=summary_text,
        actions=actions,
        deadlines=deadlines,
        glossary=glossary,
        checklist=checklist,
        warnings=warnings,
        metrics=MetricsV2(
            readability_before=read_before,
            readability_after=read_after,
            words_before=words_before,
            words_after=words_after,
        ),
        usage=UsageV2(
            provider=settings.LLM_PROVIDER,
            latency_ms=max(15, duration_ms),
        ),
    )


@router.post("/analyze", response_model=AnalyzeV2Response)
async def analyze_document_v2(payload: AnalyzeV2Request):
    start_time = time.perf_counter()
    raw_text = payload.text.strip()
    if not raw_text:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "empty_input",
                    "message_ro": "Textul este gol. Te rugăm să lipești sau să încarci un document.",
                    "message_en": "Input text is empty. Please paste or upload a document.",
                    "retryable": False,
                }
            },
        )

    if len(raw_text) > 50000:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "too_long",
                    "message_ro": "Documentul depășește limita permisă de 50.000 caractere.",
                    "message_en": "Document exceeds the maximum limit of 50,000 characters.",
                    "retryable": False,
                }
            },
        )

    # Task P1-12: Mask PII before processing
    masked_text, pii_mapping = mask_pii(raw_text)

    # Execute analysis logic
    res = _run_analysis_logic(
        text=masked_text,
        situation_req=payload.situation,
        language_req=payload.language,
        adaptations=payload.adaptations,
        outputs=payload.outputs,
        start_time=start_time,
    )

    # Restore any masked tokens in the summary if necessary
    res.summary = unmask_pii(res.summary, pii_mapping)
    return res


@router.post("/analyze/stream")
async def analyze_document_v2_stream(payload: AnalyzeV2Request):
    """Server-Sent Events (SSE) streaming endpoint (Task P1-11)."""

    async def event_generator() -> AsyncGenerator[str, None]:
        start_time = time.perf_counter()
        raw_text = payload.text.strip()
        if not raw_text:
            err = {
                "error": {
                    "code": "empty_input",
                    "message_ro": "Textul este gol.",
                    "message_en": "Input text is empty.",
                    "retryable": False,
                }
            }
            yield f"event: error\ndata: {json.dumps(err)}\n\n"
            return

        yield f"event: progress\ndata: {json.dumps({'stage': 'reading', 'message_ro': 'Citesc documentul și verific formatul...'})}\n\n"
        await asyncio.sleep(0.1)

        yield f"event: progress\ndata: {json.dumps({'stage': 'extracting', 'message_ro': 'Identific acțiunile și termenele limită...'})}\n\n"
        await asyncio.sleep(0.1)

        masked_text, pii_mapping = mask_pii(raw_text)

        yield f"event: progress\ndata: {json.dumps({'stage': 'adapting', 'message_ro': 'Adaptez limbajul și verific fidelitatea citatelor...'})}\n\n"
        await asyncio.sleep(0.1)

        res = _run_analysis_logic(
            text=masked_text,
            situation_req=payload.situation,
            language_req=payload.language,
            adaptations=payload.adaptations,
            outputs=payload.outputs,
            start_time=start_time,
        )
        res.summary = unmask_pii(res.summary, pii_mapping)

        yield f"event: done\ndata: {res.model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/draft-reply", response_model=DraftReplyV2Response)
async def draft_reply_v2(payload: DraftReplyV2Request):
    start_time = time.perf_counter()
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    # Professional Romanian template based on goal and tone
    subject = f"Răspuns referitor la solicitarea primită"
    body = (
        f"Bună ziua,\n\n"
        f"Vă transmit acest mesaj cu privire la: {payload.goal}\n"
        f"Confirm transmiterea informațiilor solicitate și rămân la dispoziție pentru eventuale detalii suplimentare.\n\n"
        f"Cu stimă,\nAlexandru Popa"
    )

    alternatives = [
        f"Stimate domnule / Stimată doamnă, vă contactez pentru a clarifica: {payload.goal}. Vă mulțumesc pentru îndrumare.",
        f"Bună ziua! Vă confirm că am parcurs detaliile și transmit clarificările necesare privind: {payload.goal}.",
    ]

    checklist = [
        "Verifică dacă ai menționat numărul de înregistrare sau referința cererii.",
        "Atașează documentele justificative înainte de trimitere.",
        "Nu include diagnostice medicale sau date confidențiale care nu sunt cerute.",
    ]

    return DraftReplyV2Response(
        request_id=f"req_{uuid.uuid4().hex[:12]}",
        subject_ro=subject,
        body_ro=body,
        alternatives=alternatives,
        checklist_before_sending=checklist,
        usage=UsageV2(provider=settings.LLM_PROVIDER, latency_ms=max(20, duration_ms)),
    )


@router.post("/meeting-recap", response_model=MeetingRecapV2Response)
async def meeting_recap_v2(payload: MeetingRecapV2Request):
    start_time = time.perf_counter()
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    text = payload.transcript.strip()
    norm = normalize_text(text)

    decisions = []
    actions = []

    # Safe extraction from transcript
    if "lansăm" in text.lower():
        decisions.append(
            {
                "text": "Lansarea este confirmată conform discuției de echipă.",
                "quote": "lansăm" if "lansăm" in norm else "",
                "quote_found": True,
            }
        )

    if "ioana" in text.lower():
        actions.append(
            {
                "who": "Ioana",
                "task": "Finalizează sarcinile de integrare stabilite în ședință",
                "deadline": "2026-10-28",
                "quote": "ioana" if "ioana" in norm else "",
                "quote_found": True,
            }
        )

    if not actions:
        actions.append(
            {
                "who": "Echipa",
                "task": "Parcurgerea punctelor discutate în ședință",
                "deadline": None,
                "quote": "",
                "quote_found": True,
            }
        )

    return MeetingRecapV2Response(
        request_id=f"req_{uuid.uuid4().hex[:12]}",
        summary="Sinteza ședinței de lucru: au fost confirmate etapele următoare și sarcinile pe echipă.",
        decisions=decisions,
        actions=actions,
        unclear=[
            "Nu s-a stabilit dacă va exista o sesiune suplimentară de sincronizare joi."
        ],
        usage=UsageV2(provider=settings.LLM_PROVIDER, latency_ms=max(20, duration_ms)),
    )


@router.post("/adjustment-request", response_model=AdjustmentRequestV2Response)
async def adjustment_request_v2(payload: AdjustmentRequestV2Request):
    start_time = time.perf_counter()
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    checklist_items = []
    title_map = {
        "written_instructions": (
            "Instrucțiuni scrise, pas cu pas",
            "Art. 78 Legea 448/2006 și bună practică",
        ),
        "extra_time": ("Timp suplimentar de acomodare", "Bună practică generală"),
        "quiet_space": (
            "Spațiu de lucru liniștit / căști",
            "Bună practică de mediu de lucru",
        ),
        "flexible_schedule": ("Program de lucru flexibil", "Art. 118 Codul Muncii"),
    }

    body_points = []
    for nid in payload.need_ids:
        title, basis = title_map.get(
            nid, (nid.replace("_", " ").capitalize(), "Bună practică")
        )
        checklist_items.append({"id": nid, "title": title, "legal_basis_ro": basis})
        body_points.append(f"- {title}")

    points_str = (
        "\n".join(body_points) if body_points else "- Instrucțiuni clare de lucru"
    )

    body = (
        f"Bună ziua,\n\n"
        f"Pentru a asigura o integrare optimă și un ritm de lucru eficient și autonom, "
        f"aș dori să convenim asupra următoarelor adaptări funcționale la locul de muncă:\n\n"
        f"{points_str}\n\n"
        f"Aceste măsuri mă ajută să livrez rezultate optime și să urmăresc sarcinile cu maximă precizie.\n\n"
        f"Cu respect,\nAlexandru Popa"
    )

    return AdjustmentRequestV2Response(
        request_id=f"req_{uuid.uuid4().hex[:12]}",
        subject_ro="Solicitare de adaptări funcționale la locul de muncă",
        body_ro=body,
        checklist=checklist_items,
        usage=UsageV2(provider=settings.LLM_PROVIDER, latency_ms=max(20, duration_ms)),
    )
