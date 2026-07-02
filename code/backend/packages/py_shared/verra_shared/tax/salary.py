"""Salary income exemption calculators (Section 10(13A), 10(5), 16(ia))."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .constants import DEDUCTION_CAPS, HRA_METRO_CITIES
from .models import Regime, _TaxBase


class HRAInput(_TaxBase):
    """Inputs for HRA exemption calculation (Section 10(13A), Rule 2A)."""

    basic_salary: float = Field(ge=0)
    hra_received: float = Field(ge=0)
    rent_paid: float = Field(ge=0)
    city: str = "other"  # 'delhi'|'mumbai'|'kolkata'|'chennai' → 50% rate, else 40%


class HRAResult(_TaxBase):
    hra_received: float
    hra_exempt: float
    hra_taxable: float
    metro: bool
    citations: list[dict[str, Any]]


class LTAInput(_TaxBase):
    """Inputs for Leave Travel Allowance exemption (Section 10(5))."""

    lta_received: float = Field(ge=0)
    actual_travel_cost: float = Field(ge=0)


class LTAResult(_TaxBase):
    lta_received: float
    lta_exempt: float
    lta_taxable: float
    citations: list[dict[str, Any]]


class SalaryExemptionsInput(_TaxBase):
    """Aggregate input for all salary exemptions."""

    basic_salary: float = Field(ge=0)
    hra_received: float = 0.0
    rent_paid: float = 0.0
    city: str = "other"
    lta_received: float = 0.0
    actual_travel_cost: float = 0.0
    regime: Regime = Regime.new


class SalaryExemptionsResult(_TaxBase):
    standard_deduction: float
    hra_exempt: float
    lta_exempt: float
    total_exempt_from_salary: float
    citations: list[dict[str, Any]]


def compute_hra_exemption(inp: HRAInput) -> HRAResult:
    """Compute HRA exemption under Section 10(13A) (old regime only).

    Exempt amount = minimum of:
      1. HRA actually received
      2. 50% of basic (metro cities) or 40% of basic (non-metro)
      3. Actual rent paid − 10% of basic salary
    """
    is_metro = inp.city.strip().lower() in HRA_METRO_CITIES
    basic_pct = 0.50 if is_metro else 0.40

    condition_1 = inp.hra_received
    condition_2 = basic_pct * inp.basic_salary
    condition_3 = max(inp.rent_paid - 0.10 * inp.basic_salary, 0.0)

    exempt = min(condition_1, condition_2, condition_3)
    taxable = max(inp.hra_received - exempt, 0.0)

    citations: list[dict[str, Any]] = [
        {
            "section": "10(13A)",
            "rule": "Rule 2A",
            "condition_1_hra_received": condition_1,
            "condition_2_basic_pct": f"{int(basic_pct * 100)}% of basic = {condition_2:,.2f}",
            "condition_3_rent_minus_10pct": condition_3,
            "exempt_amount": exempt,
            "source_citation": "Income Tax Act, 1961, Section 10(13A) read with Rule 2A",
        }
    ]

    return HRAResult(
        hra_received=inp.hra_received,
        hra_exempt=exempt,
        hra_taxable=taxable,
        metro=is_metro,
        citations=citations,
    )


def compute_lta_exemption(inp: LTAInput) -> LTAResult:
    """Compute LTA exemption under Section 10(5).

    Exempt = lower of LTA received and actual travel cost (economy class
    air / 1st class AC train, shortest route). Assumes the claimant is
    within the 2022–2025 block and journeys are available.
    """
    exempt = min(inp.lta_received, inp.actual_travel_cost)
    taxable = max(inp.lta_received - exempt, 0.0)

    citations: list[dict[str, Any]] = [
        {
            "section": "10(5)",
            "lta_received": inp.lta_received,
            "actual_travel_cost": inp.actual_travel_cost,
            "exempt_amount": exempt,
            "source_citation": "Income Tax Act, 1961, Section 10(5); block 2022–2025",
        }
    ]

    return LTAResult(
        lta_received=inp.lta_received,
        lta_exempt=exempt,
        lta_taxable=taxable,
        citations=citations,
    )


def compute_salary_exemptions(inp: SalaryExemptionsInput) -> SalaryExemptionsResult:
    """Aggregate salary exemptions: standard deduction, HRA, LTA.

    HRA and LTA exemptions are only available under the old regime.
    Standard deduction is available under both regimes (different caps).
    """
    # Standard deduction (Section 16(ia))
    if inp.regime == Regime.new:
        std_ded = min(inp.basic_salary, DEDUCTION_CAPS["standard_deduction_new_regime"])
        std_ded_cap = DEDUCTION_CAPS["standard_deduction_new_regime"]
        std_ded_source = "Finance Act 2024, Section 16(ia) — ₹75,000 under new regime"
    else:
        std_ded = min(inp.basic_salary, DEDUCTION_CAPS["standard_deduction"])
        std_ded_cap = DEDUCTION_CAPS["standard_deduction"]
        std_ded_source = "Income Tax Act, 1961, Section 16(ia) — ₹50,000 under old regime"

    citations: list[dict[str, Any]] = [
        {
            "section": "16(ia)",
            "standard_deduction": std_ded,
            "cap": std_ded_cap,
            "source_citation": std_ded_source,
        }
    ]

    hra_exempt = 0.0
    lta_exempt = 0.0

    if inp.regime == Regime.old:
        if inp.hra_received > 0:
            hra_result = compute_hra_exemption(
                HRAInput(
                    basic_salary=inp.basic_salary,
                    hra_received=inp.hra_received,
                    rent_paid=inp.rent_paid,
                    city=inp.city,
                )
            )
            hra_exempt = hra_result.hra_exempt
            citations.extend(hra_result.citations)

        if inp.lta_received > 0:
            lta_result = compute_lta_exemption(
                LTAInput(
                    lta_received=inp.lta_received,
                    actual_travel_cost=inp.actual_travel_cost,
                )
            )
            lta_exempt = lta_result.lta_exempt
            citations.extend(lta_result.citations)

    return SalaryExemptionsResult(
        standard_deduction=std_ded,
        hra_exempt=hra_exempt,
        lta_exempt=lta_exempt,
        total_exempt_from_salary=std_ded + hra_exempt + lta_exempt,
        citations=citations,
    )
