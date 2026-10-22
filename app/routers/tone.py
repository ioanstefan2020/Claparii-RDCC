from fastapi import APIRouter

from app.config import settings
from app.llm import generate_json
from app.prompts.tone import MOCK, SYSTEM, build_user
from app.safety import validate_input_limits
from app.schemas.common import MetaInfo, SuccessEnvelope
from app.schemas.tone import ToneSuggestData, ToneSuggestRequest

router = APIRouter(prefix="/api/tone/suggest", tags=["tone"])


@router.post("", response_model=SuccessEnvelope[ToneSuggestData])
async def suggest_tone(payload: ToneSuggestRequest):
    text = validate_input_limits(payload.text, max_chars=2000)

    user_prompt = build_user(
        text=text,
        context=payload.context,
        tone_goal=payload.tone_goal,
        profile=payload.profile,
    )

    data_model, meta = await generate_json(
        task="tone_suggest",
        system=SYSTEM,
        user=user_prompt,
        schema=ToneSuggestData,
        mock=MOCK,
    )

    meta_info = MetaInfo(
        provider=meta.get("provider", "mock"),
        cached=meta.get("cached", False),
        warnings=meta.get("warnings", []),
        ai_notice_ro=meta.get(
            "ai_notice_ro", "Generat de AI — sugestie orientativă de ton."
        ),
    )

    return SuccessEnvelope(ok=True, data=data_model, meta=meta_info)
