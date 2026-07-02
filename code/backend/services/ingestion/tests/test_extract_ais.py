"""Unit tests for AIS field extraction."""

from __future__ import annotations

from app.extract import extract_fields
from tests.samples import AIS_TEXT


def test_ais_header_fields() -> None:
    result = extract_fields("ais", AIS_TEXT)
    extracted = result["extracted"]
    assert extracted["pan"] == "ABCPS6789Q"
    assert extracted["assessmentYear"] == "2024-25"


def test_ais_tds_entries_and_salary_income() -> None:
    result = extract_fields("ais", AIS_TEXT)
    tds = result["extracted"]["tdsEntries"]
    assert len(tds) == 2
    assert tds[0]["deductorName"] == "ACME TECHNOLOGIES PRIVATE LIMITED"
    assert tds[0]["deductorTan"] == "BLRA12345B"
    assert tds[0]["section"] == "192"
    assert tds[0]["amountPaid"] == 2450000.0
    assert tds[0]["taxDeducted"] == 181500.0

    salary = result["extracted"]["salaryIncome"]
    assert len(salary) == 1
    assert salary[0]["amount"] == 2450000.0
    other = result["extracted"]["otherIncome"]
    assert len(other) == 1
    assert other[0]["amount"] == 42000.0


def test_ais_sft_entries() -> None:
    result = extract_fields("ais", AIS_TEXT)
    sft = result["extracted"]["sftEntries"]
    assert len(sft) == 1
    assert sft[0]["informationCategory"] == "SFT-005"
    assert sft[0]["amount"] == 500000.0


def test_ais_assessment_year_inferred_from_financial_year() -> None:
    text = AIS_TEXT.replace("Assessment Year: 2024-25\n", "")
    result = extract_fields("ais", text)
    assert result["extracted"]["assessmentYear"] == "2024-25"
    assert result["fieldMeta"]["assessmentYear"]["confidence"] == 0.5


def test_unsupported_doc_type_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        extract_fields("w2", "some text")
