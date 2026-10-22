from __future__ import annotations

import re
from typing import Any

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
    SettingReasonItem,
)

router = APIRouter(prefix="/api/profile", tags=["profile"])

CLINICAL_SCRUB_PATTERNS: list[tuple[str, str]] = [
    # Autism / Asperger / Spectrum
    (r"\bautis[mt][a-zăâîșț]*\b", "nevoi de predictibilitate și confort"),
    (r"\basperger\b", "nevoi de comunicare structurată"),
    (r"\bspectru\b", "profil de lucru"),
    # ADHD / Attention Deficit
    (r"\badhd\b", "nevoi de concentrare și ritm"),
    (r"\bdeficit de aten[țt]ie\b", "nevoi de focalizare"),
    # Dyslexia / Dyscalculia / Dysgraphia
    (r"\bdislexi[a-zăâîșț]*\b", "nevoi de lizibilitate și confort vizual"),
    (r"\bdiscalculi[a-zăâîșț]*\b", "nevoi de claritate numerică"),
    (r"\bdisgrafi[a-zăâîșț]*\b", "nevoi de redactare asistată"),
    # Depression / Anxiety
    (r"\bdepresi[a-zăâîșț]*\b", "nevoi de gestionare a energiei"),
    (r"\banxietate clinic[aă]\b", "nevoi de confort emoțional"),
    (r"\banxietate\b", "stres sau ritm intens"),
    # Schizophrenia / Bipolar
    (r"\bschizofreni[a-zăâîșț]*\b", "particularități de lucru"),
    (r"\bbipolar[a-zăâîșț]*\b", "variații de ritm"),
    # General medical/clinical diagnostic terms
    (r"\bdiagnosticat[a-zăâîșț]*\b", "cu nevoi identificate"),
    (r"\bdiagnostic[a-zăâîșț]*\b", "profil funcțional"),
    (r"\btulburar[a-zăâîșț]*\b", "particularitate"),
    (r"\btulburare\b", "particularitate"),
    (r"\bboal[aă]\b", "stare"),
    (r"\bboli\b", "nevoi"),
    (r"\bsindrom[a-zăâîșț]*\b", "profil specific"),
    (r"\bpacient[a-zăâîșț]*\b", "angajat"),
    (r"\bhandicap[a-zăâîșț]*\b", "dizabilitate sau nevoi de accesibilitate"),
]


def scrub_clinical_terms(text: str) -> str:
    """Removes medical/clinical labels and normalizes to workplace-need phrases."""
    if not text:
        return text
    result = text
    for pattern, replacement in CLINICAL_SCRUB_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


DEFAULT_SETTINGS_V2: dict[str, Any] = {
    "version": 2,
    "theme": "soft",
    "font_family": "atkinson",
    "font_scale": 100,
    "line_height": 1.6,
    "letter_spacing": 0.02,
    "word_spacing": 0.05,
    "paragraph_spacing": 1.0,
    "measure": 68,
    "font_weight": 400,
    "link_style": "underline-always",
    "saturation": 100,
    "color_vision": "none",
    "focus_ring": "normal",
    "cursor_size": "normal",
    "dim_overlay": 0,
    "reduce_motion": "auto",
    "reduce_transparency": False,
    "focus_level": 0,
    "density": "comfortable",
    "layout": "overview",
    "sidebar": "expanded",
    "summary_first": True,
    "chunk_size": "all",
    "progressive_disclosure": False,
    "glossary_inline": "hover/tap",
    "reading_ruler": "off",
    "ruler_height": 32,
    "ruler_color": "rgba(255, 235, 59, 0.25)",
    "focus_paragraph": False,
    "bionic": False,
    "reading_level": "simple",
    "format": "steps",
    "tone_notes": "off",
    "break_reminders": "off",
    "confirm_actions": True,
    "calm_mode": False,
    "tts_engine": "auto",
    "tts_voice": "auto",
    "tts_rate": 0.95,
    "tts_pitch": 1.0,
    "tts_volume": 1.0,
    "tts_pause_ms": 350,
    "tts_follow": "sentence",
    "tts_autoread": "off",
    "tts_spoken_numbers": True,
    "captions_default": True,
    "transcript_always": True,
    "visual_alerts": True,
    "vibration_alerts": False,
    "sound_effects": "off",
    "highlight_mode": "light",
    "highlight_categories": ["action", "deadline", "warning"],
    "highlight_style": "combo",
    "highlight_scale": 110,
    "highlight_palette": "multi",
    "target_size": 48,
    "target_gap": 12,
    "keyboard_shortcuts": True,
    "single_key_shortcuts": False,
    "voice_commands": False,
    "tooltips_on_focus_click": True,
    "no_drag": True,
    "sr_mode": False,
    "announce_level": "polite",
    "describe_images": "ask",
    "magnify_focus": False,
    "ui_language": "ro",
}

VALID_ENUMS: dict[str, set[Any]] = {
    "theme": {"soft", "amber", "sapphire", "hc-dark", "hc-light", "mono", "night"},
    "font_family": {"atkinson", "system", "dyslexia", "serif-readable"},
    "font_weight": {400, 500, 600, 700},
    "color_vision": {"none", "protan", "deutan", "tritan"},
    "focus_ring": {"normal", "large", "xlarge"},
    "cursor_size": {"normal", "large", "xlarge"},
    "reduce_motion": {"auto", "on"},
    "focus_level": {0, 1, 2, 3},
    "density": {"compact", "comfortable", "spacious"},
    "layout": {"overview", "guided", "card"},
    "sidebar": {"expanded", "collapsed", "auto-hide"},
    "chunk_size": {"3", "5", "7", "all"},
    "glossary_inline": {"off", "hover/tap", "always"},
    "reading_ruler": {"off", "line", "band"},
    "reading_level": {"standard", "simple", "very_simple"},
    "format": {"steps", "short_paragraphs", "bullets"},
    "tone_notes": {"off", "on"},
    "break_reminders": {"off", "25", "45"},
    "tts_engine": {"auto", "browser", "server"},
    "tts_follow": {"none", "sentence", "word"},
    "tts_autoread": {"off", "result", "page"},
    "sound_effects": {"off", "on"},
    "highlight_mode": {"off", "light", "medium", "strong"},
    "highlight_style": {"combo", "background", "underline", "bold", "larger"},
    "highlight_palette": {"yellow", "multi", "mono"},
    "target_size": {44, 48, 56, 64},
    "target_gap": {8, 12, 16, 24},
    "announce_level": {"minimal", "polite", "assertive"},
    "describe_images": {"auto", "ask", "off"},
    "ui_language": {"ro", "en"},
}

NUMERIC_RANGES: dict[str, tuple[float, float, type]] = {
    "font_scale": (70, 200, int),
    "line_height": (1.2, 2.4, float),
    "letter_spacing": (0.0, 0.2, float),
    "word_spacing": (0.0, 0.5, float),
    "paragraph_spacing": (0.5, 3.0, float),
    "measure": (40, 100, int),
    "saturation": (0, 100, int),
    "dim_overlay": (0, 60, int),
    "ruler_height": (16, 120, int),
    "tts_rate": (0.5, 2.0, float),
    "tts_pitch": (0.8, 1.2, float),
    "tts_volume": (0.0, 1.0, float),
    "tts_pause_ms": (0, 1500, int),
    "highlight_scale": (100, 140, int),
}

BOOLEAN_KEYS: set[str] = {
    "reduce_transparency",
    "summary_first",
    "progressive_disclosure",
    "focus_paragraph",
    "bionic",
    "confirm_actions",
    "calm_mode",
    "tts_spoken_numbers",
    "captions_default",
    "transcript_always",
    "visual_alerts",
    "vibration_alerts",
    "keyboard_shortcuts",
    "single_key_shortcuts",
    "voice_commands",
    "tooltips_on_focus_click",
    "no_drag",
    "sr_mode",
    "magnify_focus",
}


def clamp_and_enrich_settings(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Clamps dictionary to exact types/enums from docs/settings.schema.json and adds convenient aliases."""
    result = DEFAULT_SETTINGS_V2.copy()
    if not raw:
        raw = {}

    # Handle legacy / loose aliases in incoming dictionary
    mapped_raw = dict(raw)
    if "scale" in mapped_raw and "font_scale" not in mapped_raw:
        mapped_raw["font_scale"] = mapped_raw["scale"]
    if "font" in mapped_raw and "font_family" not in mapped_raw:
        mapped_raw["font_family"] = mapped_raw["font"]
    if "contrast" in mapped_raw and "theme" not in mapped_raw:
        c_val = str(mapped_raw["contrast"]).lower()
        if "high" in c_val or "ridicat" in c_val:
            mapped_raw["theme"] = "hc-dark"
    if "spacing" in mapped_raw:
        sp_val = str(mapped_raw["spacing"]).lower()
        if sp_val in ("relaxed", "aerisit", "roomy", "large"):
            mapped_raw["line_height"] = 1.8
            mapped_raw["letter_spacing"] = 0.04
            mapped_raw["word_spacing"] = 0.08
    if "focus" in mapped_raw and "focus_level" not in mapped_raw:
        mapped_raw["focus_level"] = mapped_raw["focus"]
    if "cursor" in mapped_raw and "cursor_size" not in mapped_raw:
        mapped_raw["cursor_size"] = mapped_raw["cursor"]
    if "screen_reader" in mapped_raw and "sr_mode" not in mapped_raw:
        mapped_raw["sr_mode"] = mapped_raw["screen_reader"]
    if mapped_raw.get("simple_mode") is True:
        mapped_raw["reading_level"] = "very_simple"
        mapped_raw["calm_mode"] = True

    for k, val in mapped_raw.items():
        if val is None:
            continue
        if k in VALID_ENUMS:
            allowed = VALID_ENUMS[k]
            if val in allowed:
                result[k] = val
            elif isinstance(val, str):
                v_low = val.lower().strip()
                match = next((item for item in allowed if str(item).lower() == v_low), None)
                if match is not None:
                    result[k] = match
        elif k in NUMERIC_RANGES:
            min_v, max_v, num_type = NUMERIC_RANGES[k]
            try:
                num = num_type(val)
                clamped = max(min_v, min(max_v, num))
                result[k] = round(clamped, 2) if num_type is float else int(clamped)
            except (ValueError, TypeError):
                pass
        elif k in BOOLEAN_KEYS:
            if isinstance(val, bool):
                result[k] = val
            elif isinstance(val, (int, str)):
                result[k] = str(val).lower() in ("true", "1", "yes", "da")
        elif k == "highlight_categories" and isinstance(val, list):
            allowed_cats = {"action", "deadline", "person", "number", "warning", "term"}
            filtered = [c for c in val if c in allowed_cats]
            if filtered:
                result[k] = filtered

    # Add reciprocal convenience aliases to the settings dictionary
    result["scale"] = result["font_scale"]
    result["font"] = result["font_family"]
    result["contrast"] = "high" if result["theme"] in ("hc-dark", "hc-light") else "standard"
    result["spacing"] = "relaxed" if result["line_height"] >= 1.8 else "standard"
    result["focus"] = result["focus_level"]
    result["cursor"] = result["cursor_size"]
    result["screen_reader"] = result["sr_mode"]
    result["simple_mode"] = (result["reading_level"] == "very_simple" or result["calm_mode"])

    return result


def generate_reasons_for_settings(settings_dict: dict[str, Any]) -> list[SettingReasonItem]:
    """Builds explanatory reason items for non-default settings."""
    reasons: list[SettingReasonItem] = []

    theme = settings_dict.get("theme")
    if theme == "amber":
        reasons.append(
            SettingReasonItem(
                key="theme",
                reason_ro="Temă caldă amber cu tonuri blânde pentru a reduce oboseala ochilor la lumină puternică.",
            )
        )
    elif theme in ("hc-dark", "hc-light"):
        reasons.append(
            SettingReasonItem(
                key="theme",
                reason_ro="Temă cu contrast ridicat pentru delimitarea clară a textului și a elementelor active.",
            )
        )

    dim = settings_dict.get("dim_overlay", 0)
    if dim > 0:
        reasons.append(
            SettingReasonItem(
                key="dim_overlay",
                reason_ro=f"Atenuare a luminozității ecranului ({dim}%) pentru prevenirea disconfortului ocular.",
            )
        )

    scale = settings_dict.get("font_scale", 100)
    if scale >= 120:
        reasons.append(
            SettingReasonItem(
                key="font_scale",
                reason_ro=f"Dimensiune mărită a textului la {scale}% pentru citire relaxată și confort vizual.",
            )
        )

    fmt = settings_dict.get("format")
    if fmt == "steps":
        reasons.append(
            SettingReasonItem(
                key="format",
                reason_ro="Organizare în pași clari și succesiuni logice pentru a ușura urmărirea sarcinilor.",
            )
        )

    if settings_dict.get("bionic"):
        reasons.append(
            SettingReasonItem(
                key="bionic",
                reason_ro="Evidențiere a primelor litere din cuvinte pentru a sprijini fixarea privirii.",
            )
        )

    if settings_dict.get("focus_level", 0) > 0:
        reasons.append(
            SettingReasonItem(
                key="focus_level",
                reason_ro="Interfață simplificată și panouri secundare ascunse pentru a preveni supraîncărcarea.",
            )
        )

    if settings_dict.get("reading_ruler") in ("line", "band"):
        reasons.append(
            SettingReasonItem(
                key="reading_ruler",
                reason_ro="Riglă de citire pentru ghidarea atenției pe rândul curent.",
            )
        )

    if settings_dict.get("sr_mode"):
        reasons.append(
            SettingReasonItem(
                key="sr_mode",
                reason_ro="Optimizări dedicate pentru tehnologiile de citire a ecranului.",
            )
        )

    return reasons


def build_heuristic_profile_recommendation(
    user_words: str, chips: list[str] | None = None
) -> ProfileNeedsRecommendation:
    """Fallback deterministic recommendation engine based on user keywords and chips."""
    low = (user_words or "").lower()
    chips_set = {str(c).lower().strip() for c in (chips or [])}

    # Visual & theme heuristics
    theme = "soft"
    dim_overlay = 0
    if any(k in low for k in ["lumină tare", "lumina tare", "obosesc la lumină", "obosesc la lumina", "orbitor", "strălucire", "stralucire", "fotofobie"]) or "fara_stralucire" in chips_set:
        theme = "amber"
        dim_overlay = 15
    elif any(k in low for k in ["contrast ridicat", "alb pe negru", "high contrast"]) or "contrast_ridicat" in chips_set:
        theme = "hc-dark"
    elif any(k in low for k in ["întuneric", "intuneric", "noapte", "dark"]) or "tema_inchisa" in chips_set:
        theme = "sapphire"

    # Font & scale heuristics
    font_scale = 100
    text_size = "standard"
    if any(k in low for k in ["foarte mare", "vedere slabă", "ecran mare", "150"]) or "text_foarte_mare" in chips_set:
        font_scale = 150
        text_size = "extra-large"
    elif any(k in low for k in ["mare", "vedere", "ochi", "mic", "greu de citit", "litere mari"]) or "text_mare" in chips_set or "text-mare" in chips_set:
        font_scale = 125
        text_size = "large"

    font_family = "atkinson"
    font = "system"
    if any(k in low for k in ["dislexie", "amestec", "sărite", "dansează", "inversate", "linii"]) or "font_dyslexia" in chips_set:
        font_family = "dyslexia"
        font = "opendyslexic"
    elif any(k in low for k in ["clar", "oboseală", "contrast"]):
        font_family = "atkinson"
        font = "atkinson"

    line_height = 1.6
    letter_spacing = 0.02
    word_spacing = 0.05
    spacing = "standard"
    if any(k in low for k in ["aglomerat", "spațiu", "aerisit", "rânduri", "rătăcesc", "obosesc"]) or "spatiere_aerisita" in chips_set:
        line_height = 1.8
        letter_spacing = 0.04
        word_spacing = 0.08
        spacing = "relaxed"

    bionic = any(k in low for k in ["atenție", "atentie", "concentrare", "pierd șirul", "distrag", "bionic", "focalizare"]) or "bionic" in chips_set
    focus_paragraph = bionic or any(k in low for k in ["paragraf", "rătăcesc"])

    focus_level = 0
    calm_mode = False
    if any(k in low for k in ["zgomot", "liniște", "liniste", "căști", "casti", "gălăgie", "birou aglomerat", "distragere", "sunete", "copleșit"]) or "fara_distragere" in chips_set or "fara-distragere" in chips_set:
        focus_level = 2
        calm_mode = True

    reading_level = "simple"
    if any(k in low for k in ["foarte simplu", "fără termeni grei", "ușor de tot", "copii"]) or "citire_usoara" in chips_set or "citire-usoara" in chips_set:
        reading_level = "very_simple"

    format_style = "steps"
    chunk_size = "all"
    if any(k in low for k in ["pași", "pasi", "etape", "instrucțiuni", "instructiuni", "uit"]) or "pasi_scurti" in chips_set:
        format_style = "steps"
        chunk_size = "5"

    audio_support = any(k in low for k in ["audio", "voce", "ascult", "să aud", "citire cu voce", "obosesc ochii"]) or "audio" in chips_set or "ascult-mai-mult" in chips_set
    sr_mode = any(k in low for k in ["cititor de ecran", "screen reader", "nevăzător", "orbi", "nvda", "jaws"]) or "cititor-ecran" in chips_set

    # Build clamped settings dictionary
    raw_settings = {
        "version": 2,
        "theme": theme,
        "font_family": font_family,
        "font_scale": font_scale,
        "line_height": line_height,
        "letter_spacing": letter_spacing,
        "word_spacing": word_spacing,
        "dim_overlay": dim_overlay,
        "bionic": bionic,
        "focus_paragraph": focus_paragraph,
        "focus_level": focus_level,
        "calm_mode": calm_mode,
        "reading_level": reading_level,
        "format": format_style,
        "chunk_size": chunk_size,
        "tts_autoread": "result" if audio_support else "off",
        "sr_mode": sr_mode,
        "sound_effects": "off" if calm_mode else "off",
        "target_size": 56 if font_scale >= 125 else 48,
        "focus_ring": "large" if font_scale >= 125 else "normal",
    }
    settings_data = clamp_and_enrich_settings(raw_settings)

    # Legacy ui_prefs object
    ui_prefs = RecommendedUIPrefs(
        textSize=text_size,
        font=font,
        contrast="high" if theme in ("hc-dark", "hc-light") else "standard",
        spacing=spacing,
        bionic=bionic,
        highlightKeyTerms=True,
        motion="reduced" if calm_mode else "standard",
        readingLevel=reading_level,
        format=format_style,
        audioSupport=audio_support,
    )

    # Workplace adjustments heuristics
    adjustments: list[RecommendedAdjustmentItem] = []

    # 1. Written instructions (critical for forgetting verbal instructions)
    if any(k in low for k in ["scris", "uit", "memorie", "verbal", "pași", "pasi", "instrucțiuni", "clar"]) or "pasi_scurti" in chips_set or not adjustments:
        adjustments.append(
            RecommendedAdjustmentItem(
                id="written_instructions",
                title="Instrucțiuni scrise, pas cu pas",
                description="Sarcinile noi sau complexe sunt transmise și în format scris, structurate în etape scurte și clare.",
                legal_basis_ro="Art. 78 Legea 448/2006 și bună practică",
                relevance_reason_ro="Îți permite să consulți sarcinile în propriul ritm și să bifezi fiecare pas finalizat, fără a depinde de memorarea instrucțiunilor verbale.",
            )
        )

    # 2. Quiet space / headphones
    if any(k in low for k in ["zgomot", "liniște", "liniste", "căști", "casti", "gălăgie", "birou aglomerat", "distragere", "sunete", "copleșit"]) or "fara_distragere" in chips_set or "fara-distragere" in chips_set:
        adjustments.append(
            RecommendedAdjustmentItem(
                id="quiet_space",
                title="Spațiu de lucru liniștit și reducerea zgomotului",
                description="Amplasarea biroului într-o zonă ferită de zgomot intens sau posibilitatea de a utiliza căști antifonice.",
                legal_basis_ro="Bună practică de ergonomie a muncii",
                relevance_reason_ro="Elimină stimulii auditivi perturbatori și sprijină starea de concentrare calmă.",
            )
        )

    # 3. Extra time / flexible schedule
    if any(k in low for k in ["timp", "oboseală", "ritm", "pauze", "asimilare", "presiune", "stres"]):
        adjustments.append(
            RecommendedAdjustmentItem(
                id="extra_time",
                title="Timp suplimentar pentru asimilarea procedurilor noi",
                description="Intervale de lucru extinse pentru parcurgerea materialelor noi de lucru și a documentației interne.",
                legal_basis_ro="Bună practică generală",
                relevance_reason_ro="Oferă o perioadă de acomodare relaxată și temeinică fără termene urgente artificiale.",
            )
        )

    if any(k in low for k in ["program", "ore", "flexibil", "dimineața", "transport", "energie"]):
        adjustments.append(
            RecommendedAdjustmentItem(
                id="flexible_schedule",
                title="Program de lucru flexibil",
                description="Ore flexibile de sosire și plecare pentru o gestionare predictibilă a energiei de lucru.",
                legal_basis_ro="Art. 118 Codul Muncii (Legea 53/2003)",
                relevance_reason_ro="Permite alinierea programului zilnic cu orele tale de productivitate maximă.",
            )
        )

    if any(k in low for k in ["subtitrări", "ședințe", "audio", "auz", "sunet", "video", "recapitulare"]) or "audio-in-text" in chips_set:
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

    reasons = generate_reasons_for_settings(settings_data)
    adaptations_list = [adj.id for adj in adjustments[:4]]

    summary_ro = (
        "Pe baza descrierii tale, am configurat o experiență adaptată confortului tău: "
        f"temă {theme}, text la {font_scale}%, format {format_style} și "
        f"{'atenuare a luminii ecranului' if dim_overlay > 0 else 'contrast adaptat'}. "
        "Am pregătit mai jos adaptările de lucru pe care le poți propune angajatorului."
    )

    return ProfileNeedsRecommendation(
        summary_ro=scrub_clinical_terms(summary_ro),
        settings=settings_data,
        reasons=reasons,
        adaptations=adaptations_list,
        ui_prefs=ui_prefs,
        recommended_adjustments=adjustments[:4],
    )


@router.post(
    "/recommend-adaptations",
    response_model=SuccessEnvelope[ProfileNeedsRecommendation],
)
async def recommend_adaptations(payload: ProfileNeedsRequest):
    user_words = (
        payload.needs_notes or payload.user_words or payload.freeform_needs or ""
    ).strip()
    chips = payload.chips or []

    if not user_words and not chips:
        raise AppError(
            code="empty_input",
            message_ro="Te rugăm să descrii pe scurt nevoile sau să selectezi cel puțin o preferință.",
            status_code=400,
        )

    if not user_words and chips:
        user_words = "Preferințe selectate: " + ", ".join(chips)

    if len(user_words) > settings.MAX_INPUT_CHARS:
        raise AppError(
            code="too_long",
            message_ro=f"Textul depășește limita permisă de {settings.MAX_INPUT_CHARS} caractere.",
            status_code=400,
        )

    # 1. Scrub clinical diagnosis terms from the user input BEFORE calling LLM
    scrubbed_user_words = scrub_clinical_terms(user_words)

    user_prompt = build_user(scrubbed_user_words, chips=chips)
    fallback_recommendation = build_heuristic_profile_recommendation(
        scrubbed_user_words, chips=chips
    )
    fallback_mock = fallback_recommendation.model_dump()

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
        data_model = fallback_recommendation
        meta = {
            "provider": "heuristic",
            "cached": False,
            "warnings": [],
            "ai_notice_ro": "Generat prin motorul de adaptabilitate funcțională PrimaZi.",
        }

    # Ensure settings are properly clamped and enriched with aliases
    data_model.settings = clamp_and_enrich_settings(data_model.settings)

    if not data_model.reasons and data_model.settings:
        data_model.reasons = generate_reasons_for_settings(data_model.settings)

    if not data_model.adaptations and data_model.recommended_adjustments:
        data_model.adaptations = [adj.id for adj in data_model.recommended_adjustments]

    # 2. Scrub clinical diagnosis terms from all output fields
    data_model.summary_ro = scrub_clinical_terms(data_model.summary_ro)
    if data_model.explanation_ro:
        data_model.explanation_ro = scrub_clinical_terms(data_model.explanation_ro)

    for r in data_model.reasons:
        r.reason_ro = scrub_clinical_terms(r.reason_ro)

    for adj in data_model.recommended_adjustments:
        adj.title = scrub_clinical_terms(adj.title)
        adj.description = scrub_clinical_terms(adj.description)
        adj.relevance_reason_ro = scrub_clinical_terms(adj.relevance_reason_ro)
        if adj.reason_ro:
            adj.reason_ro = scrub_clinical_terms(adj.reason_ro)

    if data_model.workplace_adjustments:
        for adj in data_model.workplace_adjustments:
            adj.title = scrub_clinical_terms(adj.title)
            adj.description = scrub_clinical_terms(adj.description)
            adj.relevance_reason_ro = scrub_clinical_terms(adj.relevance_reason_ro)
            if adj.reason_ro:
                adj.reason_ro = scrub_clinical_terms(adj.reason_ro)

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
