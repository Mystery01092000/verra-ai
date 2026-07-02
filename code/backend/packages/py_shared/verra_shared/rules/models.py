"""Typed, immutable models for Verra's regulatory rules store.

Rules are plain-language, conservatively-worded summaries of Indian regulatory
provisions. Every rule carries an official citation in `source`; summaries are
honest paraphrases and must never invent specifics not in the cited text.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Regulator(StrEnum):
    """Regulatory body / framework a rule belongs to."""

    income_tax = "income_tax"
    sebi = "sebi"
    rbi_fema = "rbi_fema"
    irdai = "irdai"
    gst = "gst"
    mca = "mca"


class AppliesTo(StrEnum):
    """Taxpayer population a rule applies to."""

    resident = "resident"
    nri = "nri"
    all = "all"


class RegulatoryRule(BaseModel):
    """One versioned regulatory rule with an official citation (immutable)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        frozen=True,
    )

    id: str = Field(min_length=1, examples=["it-87a", "sebi-mf-riskometer"])
    regulator: Regulator
    section: str = Field(min_length=1, examples=["87A", "SEBI/HO/IMD/DF3/CIR/P/2020/197"])
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    applies_to: AppliesTo
    tags: list[str] = Field(min_length=1)
    assessment_year: str | None = None
    source: str = Field(
        min_length=1,
        examples=["Income-tax Act 1961, s.87A as amended by Finance Act 2024"],
    )
