"""Pydantic schemas for the workplace adjustments catalog and draft generation.

Follows docs/CONTRACTS.md §3.4 and §3.5.
Responsible-AI requirement: strictly functional workplace accommodation needs;
no medical diagnoses, symptoms, or clinical terms.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import SuccessEnvelope


class AdjustmentItem(BaseModel):
    """A functional workplace adjustment item from the curated catalog."""

    id: str
    title: str
    description: str
    applies_to: list[str]
    example_request: str
    source: str


class CatalogData(BaseModel):
    """Adjustments catalog payload with legal notice and curated items."""

    disclaimer_ro: str
    items: list[AdjustmentItem]


class CatalogEnvelope(BaseModel):
    """API envelope for GET /api/adjustments/catalog per CONTRACTS §3.4."""

    ok: bool = True
    data: CatalogData


class DraftRequest(BaseModel):
    """Request payload for POST /api/adjustments/draft.

    Extra fields are strictly forbidden to reject any diagnostic or clinical input.
    """

    model_config = ConfigDict(extra="forbid")

    need_ids: list[str] = Field(
        ...,
        description="List of adjustment IDs from the catalog. Must not be empty.",
    )
    context: Literal["interview", "onboarding", "ongoing"] = "onboarding"
    employer_name: str | None = Field(default=None, max_length=200)
    tone: Literal["formal", "friendly"] = "friendly"


class ChecklistItem(BaseModel):
    """An adjustment checklist item explaining the functional workplace rationale."""

    id: str
    title: str
    why: str


class AdjustmentDraftData(BaseModel):
    """Generated accommodation request draft data per CONTRACTS §3.5."""

    subject: str
    body_ro: str
    checklist: list[ChecklistItem]


DraftResponse = SuccessEnvelope[AdjustmentDraftData]
