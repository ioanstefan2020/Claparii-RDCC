from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ProfileNeedsRequest(BaseModel):
    user_words: str | None = Field(
        None,
        description="Descrierea nevoilor de lucru în cuvintele proprii ale utilizatorului",
        max_length=4000,
    )
    freeform_needs: str | None = Field(
        None,
        description="Alias compatibil pentru user_words",
        max_length=4000,
    )
    workplace_role: str | None = None
    current_prefs: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_content(self) -> ProfileNeedsRequest:
        text = (self.user_words or self.freeform_needs or "").strip()
        if not self.user_words and self.freeform_needs:
            self.user_words = self.freeform_needs
        return self


class RecommendedAdjustmentItem(BaseModel):
    id: str
    title: str
    description: str
    legal_basis_ro: str
    relevance_reason_ro: str
    reason_ro: str | None = None

    @model_validator(mode="after")
    def set_reason_alias(self) -> RecommendedAdjustmentItem:
        if not self.reason_ro:
            self.reason_ro = self.relevance_reason_ro
        return self


class RecommendedUIPrefs(BaseModel):
    textSize: str = "standard"  # standard | large | extra-large | m | l | xl | xxl
    font: str = (
        "system"  # system | opendyslexic | atkinson | lexend | readable | default
    )
    contrast: str = "standard"  # standard | high
    spacing: str = "standard"  # standard | relaxed | comfortable | roomy
    bionic: bool = False
    highlightKeyTerms: bool = True
    motion: str = "standard"  # standard | reduced
    readingLevel: str = "simple"  # very-simple | simple | standard
    format: str = "steps"  # steps | paragraphs
    audioSupport: bool = False


class ProfileNeedsRecommendation(BaseModel):
    summary_ro: str
    explanation_ro: str | None = None
    ui_prefs: RecommendedUIPrefs
    recommended_adjustments: list[RecommendedAdjustmentItem]
    workplace_adjustments: list[RecommendedAdjustmentItem] | None = None
    disclaimer_ro: str = (
        "Informativ: PrimaZi nu stochează pe server nevoile tale și nu formulează "
        "diagnostice medicale. Recomandările sunt exclusiv funcționale pentru confort la locul de muncă."
    )
    privacy_notice_ro: str | None = (
        "Nevoile tale sunt procesate confidențial și stocate doar în browserul tău (localStorage). "
        "Nu salvăm diagnostice medicale pe server."
    )

    @model_validator(mode="after")
    def sync_aliases(self) -> ProfileNeedsRecommendation:
        if not self.explanation_ro:
            self.explanation_ro = self.summary_ro
        if not self.workplace_adjustments:
            self.workplace_adjustments = self.recommended_adjustments
        return self
