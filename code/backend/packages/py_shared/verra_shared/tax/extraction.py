"""Pydantic models for extracting Indian tax documents into structured JSON."""

from __future__ import annotations

from datetime import date
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _ExtractBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Form16PartA(_ExtractBase):
    """Part A of Form 16 (certified by employer, usually from TRACES)."""

    employer_name: str | None = None
    employer_pan: str | None = None
    employer_tan: str | None = None
    employee_name: str | None = None
    employee_pan: str | None = None
    assessment_year: str | None = None
    period_from: date | None = None
    period_to: date | None = None
    gross_salary: float = 0.0
    exempt_allowances: float = 0.0
    professional_tax: float = 0.0
    income_from_salary: float = 0.0
    tds_deducted: float = 0.0


class Form16PartB(_ExtractBase):
    """Part B of Form 16 (annexure with deductions and tax computation)."""

    gross_salary: float = 0.0
    house_rent_allowance_exempt: float = 0.0
    leave_travel_allowance_exempt: float = 0.0
    other_exemptions: float = 0.0
    standard_deduction: float = 0.0
    professional_tax: float = 0.0
    income_chargeable_under_salaries: float = 0.0
    section_80c: float = 0.0
    section_80d: float = 0.0
    section_80ccd1b: float = 0.0
    section_80g: float = 0.0
    section_80e: float = 0.0
    section_24: float = 0.0
    other_deductions: float = 0.0
    relief_under_section_89: float = 0.0
    net_tax_payable: float = 0.0


class Form16(_ExtractBase):
    """Complete Form 16 extraction."""

    document_type: str = "form_16"
    assessment_year: str | None = None
    part_a: Form16PartA = Field(default_factory=Form16PartA)
    part_b: Form16PartB = Field(default_factory=Form16PartB)
    pages: list[int] = []
    confidence: float = 0.0


class Form26ASTDS(_ExtractBase):
    """A single TDS/TCS entry from Form 26AS."""

    deductor_collector_name: str | None = None
    deductor_collector_tan: str | None = None
    section_code: str | None = None
    date_of_credit: date | None = None
    date_of_deduction: date | None = None
    amount_paid_credited: float = 0.0
    tax_deducted: float = 0.0
    tax_deposited: float = 0.0


class Form26ASTaxPaid(_ExtractBase):
    """Advance tax / self-assessment tax paid."""

    challan_serial_number: str | None = None
    bsr_code: str | None = None
    date_of_deposit: date | None = None
    major_head: str | None = None
    minor_head: str | None = None
    tax: float = 0.0
    surcharge: float = 0.0
    cess: float = 0.0
    interest: float = 0.0
    penalty: float = 0.0
    others: float = 0.0
    total: float = 0.0


class Form26ASRefund(_ExtractBase):
    """Refund details from Form 26AS."""

    assessment_year: str | None = None
    date_of_issue: date | None = None
    refund_amount: float = 0.0
    interest: float = 0.0


class Form26AS(_ExtractBase):
    """Complete Form 26AS extraction."""

    document_type: str = "form_26as"
    assessment_year: str | None = None
    pan: str | None = None
    tds_entries: list[Form26ASTDS] = []
    tcs_entries: list[Form26ASTDS] = []
    tax_paid_entries: list[Form26ASTaxPaid] = []
    refunds: list[Form26ASRefund] = []
    air_entries: list[dict[str, Any]] = []
    pages: list[int] = []
    confidence: float = 0.0


class AISIncome(_ExtractBase):
    """An income entry from the Annual Information Statement."""

    information_category: str | None = None
    information_description: str | None = None
    information_source: str | None = None
    amount: float = 0.0
    feedback_status: str | None = None
    original_feedback: str | None = None


class AISTDS(_ExtractBase):
    """A TDS/TCS entry from AIS."""

    deductor_name: str | None = None
    deductor_tan: str | None = None
    section: str | None = None
    amount_paid: float = 0.0
    tax_deducted: float = 0.0


class AIS(_ExtractBase):
    """Complete Annual Information Statement extraction."""

    document_type: str = "ais"
    assessment_year: str | None = None
    pan: str | None = None
    salary_income: list[AISIncome] = []
    other_income: list[AISIncome] = []
    tds_entries: list[AISTDS] = []
    tcs_entries: list[AISTDS] = []
    sft_entries: list[AISIncome] = []
    pages: list[int] = []
    confidence: float = 0.0


def schema_for(name: str) -> dict[str, Any]:
    """Return the JSON schema for a named extraction model."""
    models = {
        "form_16": Form16,
        "form_26as": Form26AS,
        "ais": AIS,
    }
    model = models.get(name)
    if not model:
        raise ValueError(f"Unknown extraction schema: {name}")
    return cast(dict[str, Any], cast(Any, model).model_json_schema(by_alias=True))
