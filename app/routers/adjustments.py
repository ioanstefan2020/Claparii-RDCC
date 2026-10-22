"""Adjustments router providing catalog and draft generation endpoints.

Endpoints:
- GET /api/adjustments/catalog: Curated workplace adjustments catalog (CONTRACTS §3.4)
- POST /api/adjustments/draft: Generates accommodation draft letters without medical diagnoses (CONTRACTS §3.5)
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from fastapi import APIRouter

from app.llm import generate_json
from app.prompts.adjustments import (
    DENY_LIST_DIAGNOSES,
    SYSTEM,
    build_mock,
    build_user,
)
from app.schemas.adjustments import (
    AdjustmentDraftData,
    CatalogData,
    CatalogEnvelope,
    DraftRequest,
    DraftResponse,
)
from app.schemas.common import AppError, BadLLMOutput, MetaInfo

router = APIRouter(prefix="/api/adjustments", tags=["adjustments"])

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "adjustments_ro.json"
_cached_catalog_data: CatalogData | None = None
_cached_catalog_map: dict[str, dict[str, Any]] | None = None


def get_catalog() -> tuple[CatalogData, dict[str, dict[str, Any]]]:
    """Loads and caches the adjustments catalog in memory."""
    global _cached_catalog_data, _cached_catalog_map
    if _cached_catalog_data is None or _cached_catalog_map is None:
        if not CATALOG_PATH.exists():
            raise AppError(
                code="internal",
                message_ro="Fișierul catalogului de adaptări lipsește.",
                status_code=500,
            )
        with open(CATALOG_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        catalog_obj = CatalogData.model_validate(raw)
        catalog_map = {item.id: item.model_dump() for item in catalog_obj.items}
        _cached_catalog_data = catalog_obj
        _cached_catalog_map = catalog_map
    return _cached_catalog_data, _cached_catalog_map


def check_for_diagnoses(text: str) -> None:
    """Responsible-AI Guardrail: rejects any text mentioning medical or clinical terms."""
    lower_text = text.lower()
    for bad_word in DENY_LIST_DIAGNOSES:
        if re.search(rf"\b{re.escape(bad_word)}\b", lower_text):
            raise BadLLMOutput(
                message_ro="Răspunsul primit conține termeni nepermiși din zona medicală sau diagnostic."
            )


@router.get("/catalog", response_model=CatalogEnvelope)
async def get_adjustments_catalog() -> CatalogEnvelope:
    """Returns the curated catalog of workplace adjustments with legal and practice citations."""
    catalog_data, _ = get_catalog()
    return CatalogEnvelope(ok=True, data=catalog_data)


@router.post("/draft", response_model=DraftResponse)
async def generate_adjustments_draft(req: DraftRequest) -> DraftResponse:
    """Generates a structured accommodation request letter and checklist tailored by context.

    Rejects empty requests or unknown catalog IDs.
    Applies strict responsible-AI guardrail against medical or clinical diagnoses.
    """
    if not req.need_ids:
        raise AppError(
            code="empty_input",
            message_ro="Selectează cel puțin o adaptare din catalog.",
            status_code=400,
        )

    _, catalog_map = get_catalog()

    # Validate all requested IDs exist in catalog and collect items
    selected_items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item_id in req.need_ids:
        if item_id not in catalog_map:
            raise AppError(
                code="bad_request",
                message_ro=f"ID-ul '{item_id}' nu este valid în catalogul de adaptări.",
                status_code=400,
            )
        if item_id not in seen_ids:
            seen_ids.add(item_id)
            selected_items.append(catalog_map[item_id])

    employer_name = (
        req.employer_name.strip()
        if req.employer_name and req.employer_name.strip()
        else None
    )
    if employer_name:
        lower_emp = employer_name.lower()
        for bad_word in DENY_LIST_DIAGNOSES:
            if re.search(rf"\b{re.escape(bad_word)}\b", lower_emp):
                raise AppError(
                    code="bad_request",
                    message_ro="Numele angajatorului nu poate conține termeni medicali sau diagnostice.",
                    status_code=400,
                )

    user_prompt = build_user(
        items=selected_items,
        context=req.context,
        employer_name=employer_name,
        tone=req.tone,
    )
    mock_data = build_mock(
        items=selected_items,
        context=req.context,
        employer_name=employer_name,
        tone=req.tone,
    )

    validated_model, meta_dict = await generate_json(
        task="adjustments_draft",
        system=SYSTEM,
        user=user_prompt,
        schema=AdjustmentDraftData,
        mock=mock_data,
    )

    # Responsible-AI Guardrail: check output text against deny-list
    check_for_diagnoses(validated_model.subject)
    check_for_diagnoses(validated_model.body_ro)
    for check_item in validated_model.checklist:
        check_for_diagnoses(check_item.title)
        check_for_diagnoses(check_item.why)

    meta = MetaInfo.model_validate(meta_dict)
    return DraftResponse(ok=True, data=validated_model, meta=meta)
