"""Unit tests for deterministic document classification."""

from __future__ import annotations

from app.classify import classify_document
from tests.samples import (
    AIS_TEXT,
    FORM16_TEXT,
    FORM26AS_TEXT,
    GARBLED_TEXT,
    UNKNOWN_TEXT,
)


def test_classifies_form16_with_high_confidence() -> None:
    doc_type, confidence = classify_document(FORM16_TEXT)
    assert doc_type == "form16"
    assert confidence >= 0.9


def test_classifies_form26as_with_high_confidence() -> None:
    doc_type, confidence = classify_document(FORM26AS_TEXT)
    assert doc_type == "form26as"
    assert confidence >= 0.9


def test_classifies_ais_with_high_confidence() -> None:
    doc_type, confidence = classify_document(AIS_TEXT)
    assert doc_type == "ais"
    assert confidence >= 0.9


def test_garbled_text_yields_low_confidence() -> None:
    doc_type, confidence = classify_document(GARBLED_TEXT)
    assert doc_type == "form16"
    assert confidence < 0.6


def test_unrelated_text_is_unknown() -> None:
    assert classify_document(UNKNOWN_TEXT) == ("unknown", 0.0)


def test_empty_text_is_unknown() -> None:
    assert classify_document("   \n  ") == ("unknown", 0.0)
