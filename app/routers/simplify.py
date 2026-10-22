from fastapi import APIRouter

from app.config import settings
from app.guardrails import verify_quotes
from app.llm import generate_json
from app.prompts.simplify import MOCK, SYSTEM, VERSION, build_user
from app.schemas.common import AppError, MetaInfo, SuccessEnvelope
from app.schemas.simplify import SimplifyData, SimplifyRequest

router = APIRouter(prefix="/api/simplify", tags=["simplify"])


@router.post("", response_model=SuccessEnvelope[SimplifyData])
async def simplify_text(payload: SimplifyRequest):
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

    user_prompt = build_user(text=text, profile=payload.profile)

    data_model, meta = await generate_json(
        task="simplify",
        system=SYSTEM,
        user=user_prompt,
        schema=SimplifyData,
        mock=MOCK,
        prompt_version=VERSION,
    )

    # Convert steps to dicts for quote verification guardrail
    raw_steps = [step.model_dump() for step in data_model.steps]
    kept_steps, dropped_steps = verify_quotes(raw_steps, text, key="source_quote")

    warnings = list(meta.get("warnings", []))
    if dropped_steps:
        count = len(dropped_steps)
        warnings.append(
            f"{count} {'element eliminat' if count == 1 else 'elemente eliminate'}: citatul nu apare în text."
        )

    # Re-number and re-build steps
    validated_steps = []
    for idx, s in enumerate(kept_steps, start=1):
        s["n"] = idx
        validated_steps.append(s)

    clean_data = SimplifyData(
        summary=data_model.summary,
        steps=validated_steps,
        key_terms=data_model.key_terms,
        questions_to_ask=data_model.questions_to_ask,
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
