"""Unit tests for Form 16 field extraction."""

from __future__ import annotations

from app.extract import extract_fields

from tests.samples import FORM16_TEXT


def test_form16_part_a_identity_fields() -> None:
    result = extract_fields("form16", FORM16_TEXT)
    part_a = result["extracted"]["partA"]
    assert part_a["employerName"] == "ACME TECHNOLOGIES PRIVATE LIMITED"
    assert part_a["employeeName"] == "RAHUL SHARMA"
    assert part_a["employerPan"] == "AAACA1234F"
    assert part_a["employerTan"] == "BLRA12345B"
    assert part_a["employeePan"] == "ABCPS6789Q"
    assert part_a["assessmentYear"] == "2024-25"
    assert part_a["periodFrom"] == "2023-04-01"
    assert part_a["periodTo"] == "2024-03-31"
    assert result["extracted"]["assessmentYear"] == "2024-25"


def test_form16_money_fields() -> None:
    result = extract_fields("form16", FORM16_TEXT)
    part_a = result["extracted"]["partA"]
    part_b = result["extracted"]["partB"]
    assert part_a["tdsDeducted"] == 181500.0
    assert part_b["grossSalary"] == 2450000.0
    assert part_b["houseRentAllowanceExempt"] == 180000.0
    assert part_b["leaveTravelAllowanceExempt"] == 50000.0
    assert part_b["standardDeduction"] == 50000.0
    assert part_b["professionalTax"] == 2400.0
    assert part_b["incomeChargeableUnderSalaries"] == 2167600.0
    assert part_b["section80C"] == 150000.0
    assert part_b["section80D"] == 25000.0
    assert part_b["section80Ccd1B"] == 50000.0
    assert part_b["section80G"] == 10000.0
    assert part_b["netTaxPayable"] == 181500.0


def test_form16_field_confidence_and_section_provenance() -> None:
    result = extract_fields("form16", FORM16_TEXT)
    meta = result["fieldMeta"]
    assert meta["partB.grossSalary"]["confidence"] == 0.95
    assert meta["partB.grossSalary"]["section"] == "Part B"
    assert meta["partA.employerPan"]["confidence"] == 0.95
    assert meta["partA.employerPan"]["section"] == "Part A"
    assert result["extracted"]["confidence"] > 0.9
    assert result["flags"] == []


def test_form16_tds_total_falls_back_to_quarter_sum() -> None:
    text = FORM16_TEXT.replace("Total (Rs.) 1,81,500.00\n", "")
    result = extract_fields("form16", text)
    assert result["extracted"]["partA"]["tdsDeducted"] == 181500.0
    assert result["fieldMeta"]["partA.tdsDeducted"]["confidence"] == 0.7


def test_form16_quarter_total_mismatch_is_flagged() -> None:
    text = FORM16_TEXT.replace("Total (Rs.) 1,81,500.00", "Total (Rs.) 1,99,999.00")
    result = extract_fields("form16", text)
    assert "form16:tds_quarter_total_mismatch" in result["flags"]


def test_form16_missing_fields_are_omitted_not_invented() -> None:
    result = extract_fields("form16", FORM16_TEXT)
    # No 80E line in the sample text -> no hit recorded for it.
    assert "partB.section80E" not in result["fieldMeta"]


FORM16_NARRATIVE_TEXT = """FORM NO. 16
PART A
Certificate under section 203 of the Income-tax Act, 1961
Name of Employer: Acme Technologies Pvt Ltd
TAN of Employer: BLRA12345E
Name of Employee: Rahul Sharma
PAN of Employee: ABCDE1234F
Assessment Year: 2025-26
Quarter Q1 Amount of tax deducted: Rs. 37500
Quarter Q2 Amount of tax deducted: Rs. 37500
Quarter Q3 Amount of tax deducted: Rs. 37500
Quarter Q4 Amount of tax deducted: Rs. 37500
Total (Rs.): 150000

PART B
1. Gross Salary: Rs. 1800000
2. Exemption under section 10(13A) House Rent Allowance: Rs. 120000
3. Standard deduction under section 16(ia): Rs. 75000
4. Deduction under section 80C: Rs. 150000
5. Deduction under section 80D: Rs. 25000
Net tax payable: Rs. 150000
"""


def test_form16_narrative_labeled_format_extracts_amounts() -> None:
    """Real-world exports label amounts with 'Rs.' and inline 'Name of X:' labels."""
    result = extract_fields("form16", FORM16_NARRATIVE_TEXT)
    part_b = result["extracted"]["partB"]
    assert part_b["grossSalary"] == 1800000.0
    assert part_b["houseRentAllowanceExempt"] == 120000.0
    assert part_b["standardDeduction"] == 75000.0
    assert part_b["section80C"] == 150000.0
    assert part_b["section80D"] == 25000.0
    part_a = result["extracted"]["partA"]
    assert part_a["employerTan"] == "BLRA12345E"
    assert part_a["employeePan"] == "ABCDE1234F"
    assert part_a["employerName"] == "Acme Technologies Pvt Ltd"
    assert part_a["tdsDeducted"] == 150000.0
    assert result["flags"] == []
