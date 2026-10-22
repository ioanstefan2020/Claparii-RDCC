from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProfileNeedsRequest(BaseModel):
    user_words: str = Field(
        ...,
        description="Descrierea nevoilor de lucru în cuvintele proprii ale utilizatorului",
        max_length=4000,
    )


class RecommendedAdjustmentItem(BaseModel):
    id: str
    title: str
    description: str
    legal_basis_ro: str
    relevance_reason_ro: str


class RecommendedUIPrefs(BaseModel):
    textSize: str = "standard"  # standard | large | extra-large
    font: str = "system"  # system | opendyslexic | atkinson
    contrast: str = "standard"  # standard | high
    spacing: str = "standard"  # standard | relaxed
    bionic: bool = False
    highlightKeyTerms: bool = True
    motion: str = "standard"  # standard | reduced
    readingLevel: str = "simple"  # very-simple | simple | standard
    format: str = "steps"  # steps | paragraphs
    audioSupport: bool = False


class ProfileNeedsRecommendation(BaseModel):
    summary_ro: str
    ui_prefs: RecommendedUIPrefs
    recommended_adjustments: list[RecommendedAdjustmentItem]
    disclaimer_ro: str = (
        "Informativ: PrimaZi nu stochează pe server nevoile tale și nu formulează "
        "diagnostice medicale. Recomandările sunt exclusiv funcționale pentru confort la locul de muncă."
    )
