"""Constants for Indian income tax, AY 2025-26 (FY 2024-25)."""

from __future__ import annotations

# Health and education cess
CESS_RATE = 0.04

# Rebate under Section 87A
REBATE_87A = {
    "max_amount": 25000.0,
    "old_regime_threshold": 500000.0,
    "new_regime_threshold": 700000.0,
}

# Income-tax slabs for resident individual below 60 years
# Format: (min_inclusive, max_inclusive, rate) where max_inclusive=None means unbounded.
OLD_REGIME_SLABS: list[tuple[float, float | None, float]] = [
    (0.0, 250000.0, 0.0),
    (250000.0, 500000.0, 0.05),
    (500000.0, 1000000.0, 0.20),
    (1000000.0, None, 0.30),
]

NEW_REGIME_SLABS: list[tuple[float, float | None, float]] = [
    (0.0, 300000.0, 0.0),
    (300000.0, 700000.0, 0.05),
    (700000.0, 1000000.0, 0.10),
    (1000000.0, 1200000.0, 0.15),
    (1200000.0, 1500000.0, 0.20),
    (1500000.0, None, 0.30),
]

# Surcharge brackets for AY 2025-26 (total income, common for both regimes)
SURCHARGE_BRACKETS: list[tuple[float, float | None, float]] = [
    (5000000.0, 10000000.0, 0.10),
    (10000000.0, 20000000.0, 0.15),
    (20000000.0, 50000000.0, 0.25),
    (50000000.0, None, 0.37),
]

# Deduction caps (INR)
# standard_deduction_new_regime raised to 75,000 by Finance Act 2024 (effective AY 2025-26).
DEDUCTION_CAPS: dict[str, float] = {
    "standard_deduction": 50000.0,  # old regime, Section 16(ia)
    "standard_deduction_new_regime": 75000.0,  # new regime, Finance Act 2024
    "80c": 150000.0,
    "80d_self": 25000.0,
    "80d_self_senior": 50000.0,
    "80d_parents": 25000.0,
    "80d_parents_senior": 50000.0,
    "80ccd1b": 50000.0,
    "24": 200000.0,
    "80tta": 10000.0,
    "80ttb": 50000.0,  # Section 80TTB for senior citizens
    # Section 80E (education-loan interest) has no monetary cap and is applied as-is.
}

# HRA calculation constants (Section 10(13A), Rule 2A)
# Metro cities where 50% of basic is used (vs 40% for non-metro).
HRA_METRO_CITIES: frozenset[str] = frozenset({"delhi", "mumbai", "kolkata", "chennai"})

# Advance tax instalment schedule (Section 211, FY 2024-25)
# Each tuple: (due_date_label, cumulative_percentage_of_liability)
ADVANCE_TAX_INSTALMENTS: list[tuple[str, float]] = [
    ("15 Jun 2024", 0.15),
    ("15 Sep 2024", 0.45),
    ("15 Dec 2024", 0.75),
    ("15 Mar 2025", 1.00),
]

# Section 234B/234C: simple interest rate per month or part thereof
INTEREST_RATE_234B = 0.01  # 1% per month — default in advance tax payment
INTEREST_RATE_234C = 0.01  # 1% per month — deferment of instalment
