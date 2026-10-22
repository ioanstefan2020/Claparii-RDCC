from fastapi import APIRouter

from app.config import settings
from app.guardrails import verify_quotes
from app.llm import generate_json
from app.prompts.meeting import MOCK, SYSTEM, VERSION, build_user
from app.schemas.common import AppError, MetaInfo, SuccessEnvelope
from app.schemas.meeting import (
    MeetingActionItem,
    MeetingDecision,
    MeetingSummarizeData,
    MeetingSummarizeRequest,
)

router = APIRouter(prefix="/api/meeting/summarize", tags=["meeting"])


@router.post("", response_model=SuccessEnvelope[MeetingSummarizeData])
async def summarize_meeting(payload: MeetingSummarizeRequest):
    transcript = payload.transcript.strip()
    if not transcript:
        raise AppError(
            code="empty_input",
            message_ro="Transcrierii îi lipsește conținutul.",
            status_code=400,
        )

    if len(transcript) > settings.MAX_INPUT_CHARS:
        raise AppError(
            code="too_long",
            message_ro=f"Textul depășește limita permisă de {settings.MAX_INPUT_CHARS} caractere.",
            status_code=400,
        )

    user_prompt = build_user(
        transcript=transcript, today_iso=payload.today_iso, profile=payload.profile
    )

    data_model, meta = await generate_json(
        task="meeting_summarize",
        system=SYSTEM,
        user=user_prompt,
        schema=MeetingSummarizeData,
        mock=MOCK,
        prompt_version=VERSION,
    )

    # 1. Verify quotes on decisions
    raw_decisions = [d.model_dump() for d in data_model.decisions]
    kept_decisions, dropped_decisions = verify_quotes(
        raw_decisions, transcript, key="source_quote"
    )

    # 2. Verify quotes on action items
    raw_actions = [a.model_dump() for a in data_model.action_items]
    kept_actions, dropped_actions = verify_quotes(
        raw_actions, transcript, key="source_quote"
    )

    warnings = list(meta.get("warnings", []))
    total_dropped = len(dropped_decisions) + len(dropped_actions)
    if total_dropped > 0:
        warnings.append(
            f"{total_dropped} {'element eliminat' if total_dropped == 1 else 'elemente eliminate'}: citatul nu apare în transcriere."
        )

    clean_data = MeetingSummarizeData(
        summary=data_model.summary,
        decisions=[MeetingDecision.model_validate(d) for d in kept_decisions],
        action_items=[MeetingActionItem.model_validate(a) for a in kept_actions],
        unclear_points=data_model.unclear_points,
    )

    meta_info = MetaInfo(
        provider=meta.get("provider", "mock"),
        cached=meta.get("cached", False),
        warnings=warnings,
        ai_notice_ro=meta.get(
            "ai_notice_ro", "Generat de AI — verifică datele importante."
        ),
        latency_ms=meta.get("latency_ms"),
        prompt_version=meta.get("prompt_version", VERSION),
        provider_chain_tried=meta.get("provider_chain_tried", []),
    )

    return SuccessEnvelope(ok=True, data=clean_data, meta=meta_info)
