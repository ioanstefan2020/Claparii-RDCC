import os
import re
import time
import uuid
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import Field

from app.annotate.deterministic import extract_deterministic_highlights
from app.config import settings
from app.ingest import compute_readability_metrics
from app.llm import generate_json
from app.prompts.base import (
    BASE_SYSTEM_RO,
    EASY_READ_RULES_RO,
    adapt_block,
    apply_custom_decorations,
    scrub_diagnosis_words,
    wrap_document,
)
from app.schemas.common import TolerantModel
from app.schemas.extension import (
    ExtensionAdaptRequest,
    ExtensionAdaptResponse,
    ExtensionMetrics,
    ExtensionNoteItem,
    ExtensionWarningItem,
)

router = APIRouter(prefix="/api/v1", tags=["extension"])

DEFAULT_EXT_TOKEN = "primazi-demo-2026"
MAX_SELECTION_CHARS = 3000

# Simple in-memory rate limiter: max 40 requests per minute per IP
_rate_limits: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX_CALLS = 40
RATE_LIMIT_WINDOW_SECONDS = 60.0

SYSTEM_EXT_PROMPT = f"""{BASE_SYSTEM_RO}

{EASY_READ_RULES_RO}

SARCINĂ EXTENSIE BROWSER „FĂ CLAR”:
Ești asistentul browser PrimaZi. Sarcina ta este să adaptezi textul selectat de utilizator pe o pagină web pentru a fi cât mai clar, accesibil și ușor de înțeles.

OPȚIUNI DE ACȚIUNE:
- `simplify`: rescrie textul în mod clar și cursiv, respectând nivelul cerut (1=foarte simplu / Easy-to-Read, 2=simplu și direct, 3=text original curățat de ambiguități).
- `bullets`: extrage ideile cheie ca o listă scurtă de buline (câte o idee pe rând, verbe la început, sub 15 cuvinte per bulină).
- `shorter`: comprimă textul la esențial (30-40% din lungime), păstrând datele, sumele, persoanele și instrucțiunile critice.

REGULI STRICTE:
1. Păstrează fidel toate datele concrete: zile, ore, sume de bani, procente, nume și cerințe operaționale.
2. `key_phrases`: extrage cuvinte sau expresii importante care apar EXACT cuvânt cu cuvânt în textul adaptat generat.
3. `notes`: identifică doar cereri politicoase indirecte („ar fi frumos să...”), expresii figurate / idiomuri sau posibile glume.
   Pentru orice glumă sau ironie, adaugă obligatoriu eticheta „posibilă glumă — nesigur” sau „posibilă ironie — nesigur”. Citatul `quote` TREBUIE să fie o secvență EXACTĂ din documentul sursă.
4. Respectă cu strictețe maximă orice preferință sau instrucțiune specială cerută de utilizator în profilul său.
5. Ieșire STRICT JSON conform schemei:
{{
  "text": "textul adaptat complet",
  "key_phrases": ["expresie1", "termen2"],
  "bullets": ["bulina 1", "bulina 2"],
  "notes": [{{"quote": "citat exact din sursă", "note": "explicație", "kind": "idiom | indirect_request | possible_joke"}}],
  "warnings": []
}}
"""

MOCK_EXT_RESPONSE: dict[str, Any] = {
    "text": "Luni la ora 09:00 te prezinți la recepția clădirii B. Până miercuri, 28 octombrie, completezi formularul intern F-12 în portal.",
    "key_phrases": [
        "Luni",
        "ora 09:00",
        "recepția clădirii B",
        "28 octombrie",
        "formularul intern F-12",
    ],
    "bullets": [
        "Prezintă-te luni la recepția clădirii B la ora 09:00.",
        "Completează formularul F-12 până miercuri, 28 octombrie.",
    ],
    "notes": [
        {
            "quote": "Luni la ora 09:00",
            "note": "(termen concret stabilit)",
            "kind": "indirect_request",
        }
    ],
    "warnings": [],
}


def _check_rate_limit(client_ip: str) -> bool:
    now = time.monotonic()
    calls = _rate_limits[client_ip]
    # Prune old calls
    _rate_limits[client_ip] = [
        t for t in calls if (now - t) < RATE_LIMIT_WINDOW_SECONDS
    ]
    if len(_rate_limits[client_ip]) >= RATE_LIMIT_MAX_CALLS:
        return False
    _rate_limits[client_ip].append(now)
    return True


@router.get("/health")
async def extension_health():
    """Lightweight health check for extension verification."""
    return {"ok": True, "version": "0.1.0"}


@router.post("/extension/adapt", response_model=ExtensionAdaptResponse)
async def extension_adapt(
    req: ExtensionAdaptRequest,
    request: Request,
    x_ext_token: str | None = Header(None, alias="X-Ext-Token"),
):
    """Adapts selected web page text for browser extension users.

    Conforms to docs/EXTENSION.md §5 specifications and applies multi-disability
    personalization rules.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    # 1. Rate limiting
    if not _check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "ok": False,
                "error": {
                    "code": "rate_limit",
                    "message_ro": "Prea multe cereri. Te rugăm să aștepți câteva secunde.",
                    "message_en": "Too many requests. Please wait a few seconds.",
                    "retryable": True,
                },
            },
        )

    # 2. Token check
    valid_token = os.getenv(
        "EXTENSION_TOKEN",
        settings.EXTENSION_TOKEN
        if hasattr(settings, "EXTENSION_TOKEN")
        else DEFAULT_EXT_TOKEN,
    )
    if not x_ext_token or x_ext_token.strip() != valid_token:
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "error": {
                    "code": "unauthorized",
                    "message_ro": "Token de extensie lipsă sau invalid.",
                    "message_en": "Missing or invalid extension token.",
                    "retryable": False,
                },
            },
        )

    # 3. Input size check
    raw_text = (req.text or "").strip()
    if not raw_text:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": {
                    "code": "empty_input",
                    "message_ro": "Textul selectat este gol.",
                    "message_en": "Selected text is empty.",
                    "retryable": False,
                },
            },
        )

    warnings: list[ExtensionWarningItem] = []
    if len(raw_text) > MAX_SELECTION_CHARS:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": {
                    "code": "too_long",
                    "message_ro": f"Textul selectat depășește limita de {MAX_SELECTION_CHARS} de caractere.",
                    "message_en": f"Selected text exceeds {MAX_SELECTION_CHARS} characters limit.",
                    "retryable": False,
                },
            },
        )

    # Compute initial readability
    metrics_before = compute_readability_metrics(raw_text)

    # 4. Build prompt with unified multi-disability adaptation engine
    doc_wrapped = wrap_document(raw_text)

    level_map = {
        1: "very_simple",
        2: "simple",
        3: "standard",
    }
    reading_level_key = level_map.get(req.style.reading_level, "simple")

    profile_dict = {
        "reading_level": reading_level_key,
        "format": "bullets" if req.action == "bullets" else "short_paragraphs",
        "focus_level": 2 if req.action == "shorter" else 1,
        "needs_notes": req.preference_text or "",
    }
    adapt_section = adapt_block(profile_dict)

    action_label = {
        "simplify": "Simplificare și clarificare text",
        "shorter": "Comprimare și scurtare la 30-40% din lungime (Mai scurt)",
        "bullets": "Extragere listă de buline scurte",
    }.get(req.action, "simplify")

    user_prompt = f"""ACȚIUNE CERUTĂ: {req.action} ({action_label})
INCLUDE BULINE: {"Da" if req.style.bullets or req.action == "bullets" else "Opțional"}
LUNGIME: {req.style.length}

ADAPTĂRI ȘI PREFERINȚE UTILIZATOR:
{adapt_section}

DOCUMENT SELECTAT:
{doc_wrapped}

Generează răspunsul JSON cu textul adaptat, expresiile cheie și notele pragmatice:"""

    request_id = str(uuid.uuid4())
    provider_used = "llm"

    # Contextual mock response matching action
    mock_payload = dict(MOCK_EXT_RESPONSE)
    if req.action == "shorter":
        mock_payload["text"] = "Prezintă-te luni la 09:00 la recepția clădirii B și trimite formularul F-12 până miercuri, 28 octombrie."
        mock_payload["bullets"] = [
            "Mergi luni la 09:00 la recepția clădirii B.",
            "Completează formularul F-12 până miercuri.",
        ]

    try:

        class ExtLLMPayload(TolerantModel):
            text: str
            key_phrases: list[str] = Field(default_factory=list)
            bullets: list[str] = Field(default_factory=list)
            notes: list[dict[str, Any]] = Field(default_factory=list)

        llm_data, meta_dict = await generate_json(
            task="extension_adapt",
            system=SYSTEM_EXT_PROMPT,
            user=user_prompt,
            schema=ExtLLMPayload,
            mock=mock_payload,
            prompt_version="2.0",
        )
        provider_used = "mock" if meta_dict.get("provider") == "mock" else "llm"
        out_text = llm_data.text.strip()
        raw_key_phrases = llm_data.key_phrases
        raw_bullets = llm_data.bullets
        raw_notes = llm_data.notes
    except Exception:
        # Fallback to local heuristic extraction
        provider_used = "local"
        out_text = raw_text
        raw_bullets = [s.strip() for s in re.split(r"[.?!]+", raw_text) if s.strip()][
            :5
        ]
        det = extract_deterministic_highlights(raw_text)
        raw_key_phrases = [d["text"] for d in det]
        raw_notes = []

    # Apply user custom repetitive decoration instructions (e.g. 'miau', word patterns)
    if req.preference_text and req.preference_text.strip():
        out_text = apply_custom_decorations(out_text, req.preference_text)
        raw_bullets = [
            apply_custom_decorations(b, req.preference_text) for b in raw_bullets
        ]

    # 5. Grounding Checks (Section 5)
    # Rule 1: Every key_phrase must be an exact substring of text, otherwise dropped
    valid_key_phrases = [
        kp.strip()
        for kp in raw_key_phrases
        if kp.strip() and kp.strip().lower() in out_text.lower()
    ]

    # Rule 2: Every note.quote must be an exact substring of the selected source text
    valid_notes: list[ExtensionNoteItem] = []
    for n in raw_notes:
        quote = str(n.get("quote", "")).strip()
        note_txt = str(n.get("note", "")).strip()
        kind = str(n.get("kind", "idiom")).strip().lower()
        if kind not in (
            "idiom",
            "indirect_request",
            "possible_joke",
            "figurative",
            "urgency",
            "softener",
        ):
            kind = "idiom"

        if quote and quote.lower() in raw_text.lower():
            if kind == "possible_joke" and "nesigur" not in note_txt.lower():
                note_txt = f"(posibilă glumă — nesigur: {note_txt.strip('()')})"
            valid_notes.append(ExtensionNoteItem(quote=quote, note=note_txt, kind=kind))

    # Compute final readability
    metrics_after = compute_readability_metrics(out_text)

    return ExtensionAdaptResponse(
        request_id=request_id,
        language="ro",
        text=out_text,
        key_phrases=valid_key_phrases,
        bullets=raw_bullets if req.action == "bullets" or raw_bullets else [],
        notes=valid_notes,
        warnings=warnings,
        metrics=ExtensionMetrics(
            readability_before=metrics_before["readability_score"],
            readability_after=metrics_after["readability_score"],
        ),
        mode=provider_used,
    )
