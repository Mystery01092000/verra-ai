"""Tests for salary exemption calculators (HRA, LTA, standard deduction)."""

from __future__ import annotations

import pytest
from verra_shared.tax.models import Regime
from verra_shared.tax.salary import (
    HRAInput,
    LTAInput,
    SalaryExemptionsInput,
    compute_hra_exemption,
    compute_lta_exemption,
    compute_salary_exemptions,
)


class TestHRAExemption:
    def test_metro_uses_50_pct_basic(self) -> None:
        result = compute_hra_exemption(
            HRAInput(
                basic_salary=600_000.0, hra_received=200_000.0, rent_paid=240_000.0, city="mumbai"
            )
        )
        assert result.metro is True
        # condition 1: 200k, condition 2: 50%*600k=300k, condition 3: 240k-60k=180k
        assert result.hra_exempt == pytest.approx(180_000.0)

    def test_non_metro_uses_40_pct_basic(self) -> None:
        result = compute_hra_exemption(
            HRAInput(
                basic_salary=600_000.0, hra_received=200_000.0, rent_paid=240_000.0, city="pune"
            )
        )
        assert result.metro is False
        # condition 1: 200k, condition 2: 40%*600k=240k, condition 3: 240k-60k=180k
        assert result.hra_exempt == pytest.approx(180_000.0)

    def test_hra_received_is_binding_condition(self) -> None:
        """When HRA received is smallest, full HRA is exempt."""
        result = compute_hra_exemption(
            HRAInput(
                basic_salary=1_200_000.0, hra_received=50_000.0, rent_paid=300_000.0, city="delhi"
            )
        )
        # condition 1: 50k; condition 2: 600k; condition 3: 300k-120k=180k → min=50k
        assert result.hra_exempt == pytest.approx(50_000.0)
        assert result.hra_taxable == pytest.approx(0.0)

    def test_no_rent_paid_zero_exemption(self) -> None:
        result = compute_hra_exemption(
            HRAInput(basic_salary=600_000.0, hra_received=100_000.0, rent_paid=0.0, city="delhi")
        )
        # condition 3: max(0 - 60k, 0) = 0 → exempt = 0
        assert result.hra_exempt == pytest.approx(0.0)
        assert result.hra_taxable == pytest.approx(100_000.0)

    def test_citations_present(self) -> None:
        result = compute_hra_exemption(
            HRAInput(
                basic_salary=500_000.0, hra_received=100_000.0, rent_paid=150_000.0, city="chennai"
            )
        )
        assert len(result.citations) > 0
        assert result.citations[0]["section"] == "10(13A)"


class TestLTAExemption:
    def test_exempt_is_lower_of_received_and_cost(self) -> None:
        result = compute_lta_exemption(LTAInput(lta_received=50_000.0, actual_travel_cost=35_000.0))
        assert result.lta_exempt == pytest.approx(35_000.0)
        assert result.lta_taxable == pytest.approx(15_000.0)

    def test_full_exempt_when_cost_exceeds_received(self) -> None:
        result = compute_lta_exemption(LTAInput(lta_received=30_000.0, actual_travel_cost=50_000.0))
        assert result.lta_exempt == pytest.approx(30_000.0)
        assert result.lta_taxable == pytest.approx(0.0)


class TestSalaryExemptions:
    def test_new_regime_std_ded_capped_at_75k(self) -> None:
        result = compute_salary_exemptions(
            SalaryExemptionsInput(basic_salary=1_000_000.0, regime=Regime.new)
        )
        assert result.standard_deduction == pytest.approx(75_000.0)
        assert result.hra_exempt == pytest.approx(0.0)  # HRA not applicable under new regime
        assert result.lta_exempt == pytest.approx(0.0)

    def test_old_regime_std_ded_capped_at_50k(self) -> None:
        result = compute_salary_exemptions(
            SalaryExemptionsInput(basic_salary=1_000_000.0, regime=Regime.old)
        )
        assert result.standard_deduction == pytest.approx(50_000.0)

    def test_old_regime_includes_hra_and_lta(self) -> None:
        result = compute_salary_exemptions(
            SalaryExemptionsInput(
                basic_salary=600_000.0,
                hra_received=200_000.0,
                rent_paid=240_000.0,
                city="mumbai",
                lta_received=50_000.0,
                actual_travel_cost=40_000.0,
                regime=Regime.old,
            )
        )
        # std ded: 50k; hra: 180k; lta: 40k
        assert result.standard_deduction == pytest.approx(50_000.0)
        assert result.hra_exempt == pytest.approx(180_000.0)
        assert result.lta_exempt == pytest.approx(40_000.0)
        assert result.total_exempt_from_salary == pytest.approx(270_000.0)

    def test_new_regime_no_hra_lta_even_if_provided(self) -> None:
        result = compute_salary_exemptions(
            SalaryExemptionsInput(
                basic_salary=600_000.0,
                hra_received=200_000.0,
                rent_paid=240_000.0,
                city="delhi",
                lta_received=50_000.0,
                actual_travel_cost=40_000.0,
                regime=Regime.new,
            )
        )
        assert result.hra_exempt == pytest.approx(0.0)
        assert result.lta_exempt == pytest.approx(0.0)
        assert result.standard_deduction == pytest.approx(75_000.0)
