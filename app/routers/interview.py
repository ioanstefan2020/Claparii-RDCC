from fastapi import APIRouter

from app.llm import generate_json
from app.prompts.interview import MOCK, SYSTEM, build_user
from app.safety import contains_diagnosis_terms, validate_input_limits
from app.schemas.common import MetaInfo, SuccessEnvelope
from app.schemas.interview import InterviewPrepData, InterviewPrepRequest

router = APIRouter(prefix="/api/interview/prep", tags=["interview"])


@router.post("", response_model=SuccessEnvelope[InterviewPrepData])
async def prepare_interview(payload: InterviewPrepRequest):
    job_title = validate_input_limits(payload.job_title, max_chars=200)
    job_description = validate_input_limits(payload.job_description, max_chars=10000)

    warnings = []
    diag_terms = contains_diagnosis_terms(job_description)
    if diag_terms:
        warnings.append(
            "Recomandare etică: Evită includerea de termeni medicali sau diagnostice clinice. "
            "Pregătirea se concentrează exclusiv pe adaptări funcționale la locul de muncă."
        )

    user_prompt = build_user(
        job_title=job_title,
        job_description=job_description,
        profile=payload.profile,
    )

    data_model, meta = await generate_json(
        task="interview_prep",
        system=SYSTEM,
        user=user_prompt,
        schema=InterviewPrepData,
        mock=MOCK,
    )

    meta_warnings = list(meta.get("warnings", [])) + warnings

    meta_info = MetaInfo(
        provider=meta.get("provider", "mock"),
        cached=meta.get("cached", False),
        warnings=meta_warnings,
        ai_notice_ro=meta.get(
            "ai_notice_ro",
            "Ghid generat prin asistență AI pentru pregătirea interviului. Răspunsurile sunt orientative.",
        ),
    )

    return SuccessEnvelope(ok=True, data=data_model, meta=meta_info)
