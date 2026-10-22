from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ProfileNeedsRequest(BaseModel):
    model_config = {"extra": "ignore"}

    needs_notes: str | None = Field(
        None,
        description="Descrierea nevoilor de lucru în cuvintele proprii ale utilizatorului (Wave 2)",
    )
    chips: list[str] | None = Field(
        default=None,
        description="Selecție opțională de etichete rapide de preferințe sau nevoi",
    )
    user_words: str | None = Field(
        None,
        description="Alias compatibil pentru needs_notes",
    )
    freeform_needs: str | None = Field(
        None,
        description="Alias compatibil pentru needs_notes",
    )
    workplace_role: str | None = None
    current_prefs: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_content(self) -> ProfileNeedsRequest:
        text = (self.needs_notes or self.user_words or self.freeform_needs or "").strip()
        if not text and self.chips:
            # If no text is provided, format prompt from chips so it succeeds
            text = ", ".join(str(c).strip() for c in self.chips if str(c).strip())

        self.needs_notes = text or None
        self.user_words = text or None
        self.freeform_needs = text or None
        return self


class SettingReasonItem(BaseModel):
    model_config = {"extra": "ignore"}

    key: str = Field(..., description="Cheia setării din primazi.settings.v2")
    reason_ro: str = Field(..., description="Explicația prietenoasă în limba română")


class RecommendedAdjustmentItem(BaseModel):
    model_config = {"extra": "ignore"}

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
    model_config = {"extra": "ignore"}

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
    model_config = {"extra": "ignore"}

    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Dicționar de setări conforme cu docs/settings.schema.json",
    )
    reasons: list[SettingReasonItem] = Field(
        default_factory=list,
        description="Motivele recomandării pentru fiecare setare configurată",
    )
    adaptations: list[str] = Field(
        default_factory=list,
        description="Listă cu ID-urile adaptărilor funcționale recomandate la locul de muncă",
    )
    summary_ro: str
    explanation_ro: str | None = None
    ui_prefs: RecommendedUIPrefs = Field(default_factory=RecommendedUIPrefs)
    recommended_adjustments: list[RecommendedAdjustmentItem] = Field(
        default_factory=list
    )
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
        if not self.adaptations and self.recommended_adjustments:
            self.adaptations = [adj.id for adj in self.recommended_adjustments]
        return self
