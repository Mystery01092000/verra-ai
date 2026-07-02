"""Deterministic Indian tax calculators and extraction schemas."""

from .advance_tax import AdvanceTaxInput, AdvanceTaxResult, compute_advance_tax
from .compare import RegimeComparison, compare_regimes
from .extraction import AIS, Form16, Form26AS, schema_for
from .liability import compute_tax_liability, compute_tax_liability_from_input
from .models import Deductions, IncomeHeads, Regime, TaxComputationResult, TaxInput, TaxpayerType
from .reconcile import ReconciliationResult, TDSEntry, reconcile_tds
from .salary import (
    HRAInput,
    HRAResult,
    LTAInput,
    LTAResult,
    SalaryExemptionsInput,
    SalaryExemptionsResult,
    compute_hra_exemption,
    compute_lta_exemption,
    compute_salary_exemptions,
)

__all__ = [
    # Core liability
    "compute_tax_liability",
    "compute_tax_liability_from_input",
    "TaxComputationResult",
    "TaxInput",
    "IncomeHeads",
    "Deductions",
    "Regime",
    "TaxpayerType",
    # Regime comparison
    "compare_regimes",
    "RegimeComparison",
    # Salary exemptions
    "compute_hra_exemption",
    "compute_lta_exemption",
    "compute_salary_exemptions",
    "HRAInput",
    "HRAResult",
    "LTAInput",
    "LTAResult",
    "SalaryExemptionsInput",
    "SalaryExemptionsResult",
    # TDS reconciliation
    "reconcile_tds",
    "ReconciliationResult",
    "TDSEntry",
    # Advance tax
    "compute_advance_tax",
    "AdvanceTaxInput",
    "AdvanceTaxResult",
    # Extraction schemas
    "Form16",
    "Form26AS",
    "AIS",
    "schema_for",
]
