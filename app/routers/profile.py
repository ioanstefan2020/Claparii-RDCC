from __future__ import annotations

import re

from fastapi import APIRouter

from app.config import settings
from app.llm import generate_json
from app.prompts.profile import MOCK, SYSTEM, build_user
from app.schemas.common import AppError, MetaInfo, SuccessEnvelope
from app.schemas.profile import (
    ProfileNeedsRecommendation,
    ProfileNeedsRequest,
    RecommendedAdjustmentItem,
    RecommendedUIPrefs,
)

router = APIRouter(prefix="/api/profile", tags=["profile"])


def build_heuristic_profile_recommendation(
    user_words: str,
) -> ProfileNeedsRecommendation:
    """Fallback deterministic recommendation engine based on user keywords."""
    low = user_words.lower()

    # UI preferences heuristics
    text_size = "standard"
    if any(k in low for k in ["mare", "vedere", "ochi", "mic", "greu de citit"]):
        text_size = (
            "extra-large"
            if any(k in low for k in ["foarte mare", "slabă", "ecran mare"])
            else "large"
        )

    font = "system"
    if any(
        k in low
        for k in [
            "dislexie",
            "amestec",
            "sărite",
            "dansează",
            "inversate",
            "linii",
        ]
    ):
        font = "opendyslexic"
    elif any(k in low for k in ["clar", "oboseală", "contrast"]):
        font = "atkinson"

    contrast = (
        "high"
        if any(k in low for k in ["contrast", "lumină", "întuneric", "strălucire"])
        else "standard"
    )
    spacing = (
        "relaxed"
        if any(
            k in low
            for k in [
                "aglomerat",
                "spațiu",
                "aerisit",
                "rânduri",
                "rătăcesc",
                "obosesc",
            ]
        )
        else "standard"
    )
    bionic = any(
        k in low
        for k in [
            "atenție",
            "concentrare",
            "adhd",
            "pierd șirul",
            "distrag",
            "bionic",
            "focalizare",
        ]
    )
    highlight_key = True
    motion = (
        "reduced"
        if any(
            k in low for k in ["mișcare", "animații", "amețeală", "distrage", "static"]
        )
        else "standard"
    )
    reading_level = (
        "very-simple"
        if any(
            k in low
            for k in [
                "foarte simplu",
                "fără termeni grei",
                "ușor de tot",
                "copii",
            ]
        )
        else "simple"
    )
    audio_support = any(
        k in low
        for k in [
            "audio",
            "voce",
            "ascult",
            "să aud",
            "citire cu voce",
            "obosesc ochii",
        ]
    )

    ui_prefs = RecommendedUIPrefs(
        textSize=text_size,
        font=font,
        contrast=contrast,
        spacing=spacing,
        bionic=bionic,
        highlightKeyTerms=highlight_key,
        motion=motion,
        readingLevel=reading_level,
        format="steps",
        audioSupport=audio_support,
    )

    # Workplace adjustments heuristics
    adjustments: list[RecommendedAdjustmentItem] = []

    # 1. Written instructions
    if (
        any(
            k in low
            for k in [
                "scris",
                "uit",
                "memorie",
                "verbal",
                "pași",
                "instrucțiuni",
                "clar",
            ]
        )
        or not adjustments
    ):
        adjustments.append(
            RecommendedAdjustmentItem(
                id="written_instructions",
                title="Instrucțiuni scrise, pas cu pas",
                description="Sarcinile noi sau complexe sunt transmise și în format scris, structurate în etape scurte și clare.",
                legal_basis_ro="Art. 78 Legea 448/2006 și bună practică",
                relevance_reason_ro="Îți permite să consulți sarcinile în propriul ritm și să bifezi fiecare pas finalizat.",
            )
        )

    # 2. Quiet space / headphones
    if any(
        k in low
        for k in [
            "zgomot",
            "liniște",
            "căști",
            "gălăgie",
            "birou aglomerat",
            "distragere",
            "sunete",
        ]
    ):
        adjustments.append(
            RecommendedAdjustmentItem(
                id="quiet_space",
                title="Spațiu de lucru liniștit și reducerea zgomotului",
                description="Amplasarea biroului într-o zonă ferită de zgomot intens sau posibilitatea de a utiliza căști antifonice.",
                legal_basis_ro="Bună practică de ergonomie",
                relevance_reason_ro="Elimină stimulii auditivi perturbatori și sprijină starea de concentrare calmă.",
            )
        )

    # 3. Extra time / flexible schedule
    if any(
        k in low
        for k in [
            "timp",
            "oboseală",
            "ritm",
            "pauze",
            "asimilare",
            "presiune",
            "stres",
        ]
    ):
        adjustments.append(
            RecommendedAdjustmentItem(
                id="extra_time",
                title="Timp suplimentar pentru asimilarea procedurilor noi",
                description="Intervale de lucru extinse pentru parcurgerea materialelor noi de lucru și a documentației interne.",
                legal_basis_ro="Bună practică generală",
                relevance_reason_ro="Oferă o perioadă de acomodare relaxată și temeinică fără termene urgente artificiale.",
            )
        )

    if any(
        k in low
        for k in ["program", "ore", "flexibil", "dimineața", "transport", "energie"]
    ):
        adjustments.append(
            RecommendedAdjustmentItem(
                id="flexible_schedule",
                title="Program de lucru flexibil",
                description="Ore flexibile de sosire și plecare pentru o gestionare predictibilă a energiei de lucru.",
                legal_basis_ro="Art. 118 Codul Muncii (Legea 53/2003)",
                relevance_reason_ro="Permite alinierea programului zilnic cu orele tale de productivitate maximă.",
            )
        )

    if any(
        k in low
        for k in [
            "subtitrări",
            "ședințe",
            "audio",
            "auz",
            "sunet",
            "video",
            "recapitulare",
        ]
    ):
        adjustments.append(
            RecommendedAdjustmentItem(
                id="captions_transcripts",
                title="Subtitrări și sinteze scrise pentru întâlniri",
                description="Activarea subtitrărilor automate în convorbirile audio-video și transmiterea în scris a deciziilor.",
                legal_basis_ro="Bună practică generală",
                relevance_reason_ro="Garantează accesul complet la toate deciziile de echipă fără a pierde informații verbale.",
            )
        )

    if len(adjustments) < 2:
        adjustments.append(
            RecommendedAdjustmentItem(
                id="plain_language_docs",
                title="Ghiduri și documente în limbaj simplu",
                description="Materiale de instruire și proceduri de lucru formulate concis, cu explicații directe.",
                legal_basis_ro="Bună practică generală",
                relevance_reason_ro="Facilitează înțelegerea autonomă a documentelor interne fără jargon administrativ complicat.",
            )
        )

    summary_ro = (
        "Pe baza descrierii tale, am configurat o experiență adaptată confortului tău: "
        f"text {text_size}, font {font}, spațiere {spacing} și "
        f"{'evidențiere bionică activată' if bionic else 'evidențiere a termenilor cheie'}. "
        "Am pregătit mai jos adaptările de lucru pe care le poți propune angajatorului."
    )

    return ProfileNeedsRecommendation(
        summary_ro=summary_ro,
        ui_prefs=ui_prefs,
        recommended_adjustments=adjustments[:4],
    )


@router.post(
    "/recommend-adaptations",
    response_model=SuccessEnvelope[ProfileNeedsRecommendation],
)
async def recommend_adaptations(payload: ProfileNeedsRequest):
    user_words = (payload.user_words or payload.freeform_needs or "").strip()
    if not user_words:
        raise AppError(
            code="empty_input",
            message_ro="Te rugăm să descrii pe scurt nevoile sau preferințele tale de lucru.",
            status_code=400,
        )

    if len(user_words) > settings.MAX_INPUT_CHARS:
        raise AppError(
            code="too_long",
            message_ro=f"Textul depășește limita permisă de {settings.MAX_INPUT_CHARS} caractere.",
            status_code=400,
        )

    user_prompt = build_user(user_words)
    fallback_mock = build_heuristic_profile_recommendation(user_words).model_dump()

    try:
        data_model, meta = await generate_json(
            task="profile_needs",
            system=SYSTEM,
            user=user_prompt,
            schema=ProfileNeedsRecommendation,
            mock=fallback_mock,
        )
    except Exception:
        # Fallback to local heuristic engine
        data_model = build_heuristic_profile_recommendation(user_words)
        meta = {
            "provider": "heuristic",
            "cached": False,
            "warnings": [],
            "ai_notice_ro": "Generat prin motorul de adaptabilitate funcțională PrimaZi.",
        }

    # Ensure no clinical diagnosis terms leak into summary or relevance reasons
    deny_clinical = [
        "autism",
        "asperger",
        "adhd",
        "deficit de atenție",
        "dislexie",
        "discalculie",
        "depresie",
        "anxietate clinică",
        "schizofrenie",
        "bipolar",
        "tulburare",
        "boală",
        "sindrom",
        "pacient",
        "diagnosticat",
    ]
    for word in deny_clinical:
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        data_model.summary_ro = pattern.sub(
            "particularități de lucru", data_model.summary_ro
        )
        for adj in data_model.recommended_adjustments:
            adj.relevance_reason_ro = pattern.sub(
                "nevoile tale practice", adj.relevance_reason_ro
            )

    meta_info = MetaInfo(
        provider=meta.get("provider", "mock"),
        cached=meta.get("cached", False),
        warnings=list(meta.get("warnings", [])),
        ai_notice_ro=meta.get(
            "ai_notice_ro",
            "Generat de asistentul de adaptabilitate — verifică recomandările.",
        ),
    )

    return SuccessEnvelope(ok=True, data=data_model, meta=meta_info)
