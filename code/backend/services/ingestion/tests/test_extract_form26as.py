"""Unit tests for Form 26AS field extraction."""

from __future__ import annotations

from app.extract import extract_fields
from tests.samples import FORM26AS_TEXT


def test_form26as_header_fields() -> None:
    result = extract_fields("form26as", FORM26AS_TEXT)
    extracted = result["extracted"]
    assert extracted["pan"] == "ABCPS6789Q"
    assert extracted["assessmentYear"] == "2024-25"


def test_form26as_tds_entries() -> None:
    result = extract_fields("form26as", FORM26AS_TEXT)
    entries = result["extracted"]["tdsEntries"]
    assert len(entries) == 2
    first, second = entries
    assert first["deductorCollectorName"] == "ACME TECHNOLOGIES PRIVATE LIMITED"
    assert first["deductorCollectorTan"] == "BLRA12345B"
    assert first["sectionCode"] == "192"
    assert first["amountPaidCredited"] == 2450000.0
    assert first["taxDeducted"] == 181500.0
    assert first["taxDeposited"] == 181500.0
    assert second["deductorCollectorTan"] == "MUMH03189E"
    assert second["sectionCode"] == "194A"
    assert second["taxDeducted"] == 4200.0
    assert result["fieldMeta"]["tdsEntries[0]"]["confidence"] == 0.95
    assert result["fieldMeta"]["tdsEntries[0]"]["section"] == "Part A"


def test_form26as_tax_paid_entries() -> None:
    result = extract_fields("form26as", FORM26AS_TEXT)
    entries = result["extracted"]["taxPaidEntries"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["majorHead"] == "0021"
    assert entry["minorHead"] == "300"
    assert entry["tax"] == 25000.0
    assert entry["total"] == 25000.0
    assert entry["bsrCode"] == "0510308"
    assert entry["dateOfDeposit"] == "2024-03-15"
    assert entry["challanSerialNumber"] == "04567"
