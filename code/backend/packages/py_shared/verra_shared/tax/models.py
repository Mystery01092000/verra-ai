"""Pydantic models for Indian tax calculators."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _TaxBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TaxpayerType(StrEnum):
    resident_ordinarily = "resident_ordinarily"
    resident_not_ordinarily = "resident_not_ordinarily"
    non_resident = "non_resident"


class Regime(StrEnum):
    old = "old"
    new = "new"


class IncomeHeads(_TaxBase):
    salary: float = 0.0
    house_property: float = 0.0
    capital_gains: float = 0.0
    business: float = 0.0
    other_sources: float = 0.0
    foreign: float = 0.0


class Deductions(_TaxBase):
    standard_deduction: float = Field(default=0.0, ge=0)
    section_80c: float = Field(default=0.0, ge=0)
    section_80d: float = Field(default=0.0, ge=0)
    section_80ccd1b: float = Field(default=0.0, ge=0)
    section_80g: float = Field(default=0.0, ge=0)
    section_24: float = Field(default=0.0, ge=0)
    section_80e: float = Field(default=0.0, ge=0)
    section_80tta: float = Field(default=0.0, ge=0)
    other: float = Field(default=0.0, ge=0)

    @property
    def total(self) -> float:
        return float(sum(self.model_dump().values()))


class TaxInput(_TaxBase):
    assessment_year: str
    taxpayer_type: TaxpayerType
    regime: Regime
    age: int = Field(0, ge=0)
    income: IncomeHeads = IncomeHeads()
    deductions: Deductions = Deductions()
    tds_tcs_credit: float = 0.0
    advance_tax_paid: float = 0.0
    foreign_tax_credit: float = 0.0


class TaxComputationResult(_TaxBase):
    assessment_year: str
    taxpayer_type: TaxpayerType
    regime: Regime
    gross_total_income: float
    total_deductions: float
    taxable_income: float
    tax_liability: float
    surcharge: float
    cess: float
    rebate_87a: float
    total_tax: float
    tds_tcs_credit: float
    advance_tax_paid: float
    foreign_tax_credit: float
    net_tax_refund_due: float
    effective_tax_rate: float
    citations: list[dict[str, Any]] = []
