"""Unit tests for deterministic Indian tax liability calculator (AY 2025-26)."""

from __future__ import annotations

import pytest
from verra_shared.tax import compute_tax_liability
from verra_shared.tax.models import Deductions, IncomeHeads, Regime, TaxpayerType


# fmt: off
@pytest.mark.parametrize(
    "salary, regime, expected_tax_before_rebate",
    [
        (300000, Regime.new, 0),          # below basic exemption
        (700000, Regime.new, 20_000),     # 5% of 4L; fully offset by rebate 87A
        (1000000, Regime.new, 50_000),    # 5% of 4L + 10% of 3L
        (1500000, Regime.new, 140_000),   # 20k + 30k + 30k + 60k
        (500000, Regime.old, 10_000),     # 5% of 2L; fully offset by rebate 87A
        (1000000, Regime.old, 102_500),   # after 50k std ded, taxable 950k -> 12.5k + 90k
    ],
)
# fmt: on
def test_tax_liability_no_surcharge(
    salary: int, regime: Regime, expected_tax_before_rebate: int
) -> None:
    result = compute_tax_liability(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        regime=regime,
        age=35,
        income=IncomeHeads(salary=float(salary)),
        deductions=(
            Deductions(standard_deduction=50000.0)
            if regime == Regime.old
            else Deductions()
        ),
    )
    assert result.tax_liability == pytest.approx(expected_tax_before_rebate, rel=1e-6)


def test_new_regime_rebate_87a() -> None:
    result = compute_tax_liability(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        regime=Regime.new,
        age=35,
        income=IncomeHeads(salary=700000.0),
        deductions=Deductions(),
    )
    assert result.tax_liability == pytest.approx(20_000.0, rel=1e-6)
    assert result.rebate_87a == pytest.approx(20_000.0, rel=1e-6)
    assert result.total_tax == pytest.approx(0.0, abs=1e-6)


def test_old_regime_deductions() -> None:
    result = compute_tax_liability(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        regime=Regime.old,
        age=35,
        income=IncomeHeads(salary=1_000_000.0),
        deductions=Deductions(
            standard_deduction=50000.0,
            section_80c=150000.0,
            section_80d=25000.0,
        ),
    )
    # taxable income = 10L - 50k - 1.5L - 25k = 775k
    # tax = 12.5k (2.5L-5L) + 55k (5L-7.75L) = 67.5k
    assert result.taxable_income == pytest.approx(775000.0, rel=1e-6)
    assert result.tax_liability == pytest.approx(67_500.0, rel=1e-6)


def test_cess_applied() -> None:
    result = compute_tax_liability(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        regime=Regime.new,
        age=35,
        income=IncomeHeads(salary=1_000_000.0),
        deductions=Deductions(),
    )
    assert result.cess == pytest.approx(result.tax_liability * 0.04, rel=1e-6)


def test_nri_no_rebate() -> None:
    result = compute_tax_liability(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.non_resident,
        regime=Regime.new,
        age=35,
        income=IncomeHeads(salary=700000.0),
        deductions=Deductions(),
    )
    assert result.rebate_87a == 0.0
    assert result.tax_liability == pytest.approx(20_000.0, rel=1e-6)


def test_net_tax_refund_due() -> None:
    result = compute_tax_liability(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        regime=Regime.new,
        age=35,
        income=IncomeHeads(salary=1_000_000.0),
        deductions=Deductions(),
        tds_tcs_credit=60_000.0,
    )
    assert result.net_tax_refund_due == pytest.approx(result.total_tax - 60_000.0, rel=1e-6)


def test_unsupported_assessment_year() -> None:
    with pytest.raises(ValueError, match="Only AY 2025-26"):
        compute_tax_liability(
            assessment_year="2024-25",
            taxpayer_type=TaxpayerType.resident_ordinarily,
            regime=Regime.new,
            age=35,
            income=IncomeHeads(),
            deductions=Deductions(),
        )


def test_new_regime_std_ded_capped_at_75k() -> None:
    """Finance Act 2024: standard deduction under new regime is ₹75,000 (not ₹50,000)."""
    result = compute_tax_liability(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        regime=Regime.new,
        age=35,
        income=IncomeHeads(salary=1_000_000.0),
        deductions=Deductions(standard_deduction=75_000.0),
    )
    assert result.total_deductions == pytest.approx(75_000.0)
    assert result.taxable_income == pytest.approx(925_000.0)


def test_new_regime_std_ded_capped_even_if_over_75k() -> None:
    """Standard deduction over ₹75,000 must be capped at ₹75,000 under new regime."""
    result = compute_tax_liability(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        regime=Regime.new,
        age=35,
        income=IncomeHeads(salary=1_000_000.0),
        deductions=Deductions(standard_deduction=100_000.0),  # over cap
    )
    assert result.total_deductions == pytest.approx(75_000.0)
    assert result.taxable_income == pytest.approx(925_000.0)


def test_new_regime_std_ded_citation_present() -> None:
    """Standard deduction citation must reference Finance Act 2024."""
    result = compute_tax_liability(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        regime=Regime.new,
        age=35,
        income=IncomeHeads(salary=800_000.0),
        deductions=Deductions(standard_deduction=75_000.0),
    )
    std_ded_citations = [c for c in result.citations if c.get("section") == "16(ia)"]
    assert len(std_ded_citations) == 1
    assert "Finance Act 2024" in std_ded_citations[0].get("source", "")
