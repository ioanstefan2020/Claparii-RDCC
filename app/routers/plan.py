from fastapi import APIRouter

from app.config import settings
from app.guardrails import verify_quotes
from app.llm import generate_json
from app.prompts.plan import MOCK, SYSTEM, build_user
from app.schemas.common import AppError, MetaInfo, SuccessEnvelope
from app.schemas.plan import PlanExtractData, PlanExtractRequest, PlanTask

router = APIRouter(prefix="/api/plan/extract", tags=["plan"])


@router.post("", response_model=SuccessEnvelope[PlanExtractData])
async def extract_plan(payload: PlanExtractRequest):
    text = payload.text.strip()
    if not text:
        raise AppError(
            code="empty_input",
            message_ro="Textul este gol. Lipește sau scrie ceva.",
            status_code=400,
        )

    if len(text) > settings.MAX_INPUT_CHARS:
        raise AppError(
            code="too_long",
            message_ro=f"Textul depășește limita permisă de {settings.MAX_INPUT_CHARS} caractere.",
            status_code=400,
        )

    user_prompt = build_user(
        text=text, today_iso=payload.today_iso, profile=payload.profile
    )

    data_model, meta = await generate_json(
        task="plan_extract",
        system=SYSTEM,
        user=user_prompt,
        schema=PlanExtractData,
        mock=MOCK,
    )

    # Convert tasks to dicts for quote verification guardrail
    raw_tasks = [task.model_dump() for task in data_model.tasks]
    kept_tasks, dropped_tasks = verify_quotes(raw_tasks, text, key="source_quote")

    warnings = list(meta.get("warnings", []))
    if dropped_tasks:
        count = len(dropped_tasks)
        warnings.append(
            f"{count} {'sarcină eliminată' if count == 1 else 'sarcini eliminate'}: citatul nu apare în text."
        )

    # Re-key IDs t1..tn
    validated_tasks: list[PlanTask] = []
    for idx, t in enumerate(kept_tasks, start=1):
        t["id"] = f"t{idx}"
        validated_tasks.append(PlanTask.model_validate(t))

    clean_data = PlanExtractData(tasks=validated_tasks)

    meta_info = MetaInfo(
        provider=meta.get("provider", "mock"),
        cached=meta.get("cached", False),
        warnings=warnings,
        ai_notice_ro=meta.get(
            "ai_notice_ro", "Generat de AI — verifică datele importante."
        ),
    )

    return SuccessEnvelope(ok=True, data=clean_data, meta=meta_info)
