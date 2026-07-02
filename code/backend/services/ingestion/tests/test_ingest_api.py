"""Integration tests for POST /v1/ingest and its internal alias."""

from __future__ import annotations

import json
from typing import Any

import pytest
from app.main import app
from fastapi.testclient import TestClient
from tests.samples import (
    FORM16_HEADER_ONLY_TEXT,
    FORM16_TEXT,
    FORM26AS_TEXT,
    GARBLED_TEXT,
    UNKNOWN_TEXT,
)

client = TestClient(app)


def _ingest(payload: dict[str, Any], path: str = "/v1/ingest") -> Any:
    return client.post(path, json=payload)


def test_form16_text_is_parsed() -> None:
    r = _ingest({"documentId": "doc-1", "tenantId": "t-1", "content": FORM16_TEXT})
    assert r.status_code == 200
    body = r.json()
    assert body["documentId"] == "doc-1"
    assert body["docType"] == "form16"
    assert body["classificationConfidence"] >= 0.9
    assert body["status"] == "parsed"
    assert body["extracted"]["partA"]["employerPan"] == "AAACA1234F"
    assert body["extracted"]["partB"]["grossSalary"] == 2450000.0
    assert body["lowConfidenceFields"] == []
    assert body["flags"] == []


def test_internal_ingest_alias_matches_public_route() -> None:
    payload = {"documentId": "doc-alias", "content": FORM26AS_TEXT}
    public = _ingest(payload, path="/v1/ingest")
    internal = _ingest(payload, path="/internal/ingest")
    assert public.status_code == internal.status_code == 200
    assert public.json() == internal.json()
    assert internal.json()["docType"] == "form26as"


def test_garbled_text_needs_review() -> None:
    r = _ingest({"content": GARBLED_TEXT})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "needs_review"
    assert body["classificationConfidence"] < 0.6


def test_missing_required_money_fields_needs_review() -> None:
    r = _ingest({"content": FORM16_HEADER_ONLY_TEXT})
    assert r.status_code == 200
    body = r.json()
    assert body["docType"] == "form16"
    assert body["classificationConfidence"] >= 0.6
    assert body["status"] == "needs_review"


def test_unknown_document_is_unsupported() -> None:
    r = _ingest({"content": UNKNOWN_TEXT})
    assert r.status_code == 200
    body = r.json()
    assert body["docType"] == "unknown"
    assert body["status"] == "unsupported"
    assert body["extracted"] == {}


def test_explicit_unsupported_doc_type() -> None:
    r = _ingest({"content": "anything", "docType": "w2"})
    body = r.json()
    assert body["status"] == "unsupported"
    assert any(f.startswith("unsupported_doc_type") for f in body["flags"])


def test_json_passthrough_validates_against_schema() -> None:
    content = json.dumps(
        {
            "documentType": "form_16",
            "assessmentYear": "2024-25",
            "partA": {"grossSalary": 2450000.0, "tdsDeducted": 181500.0},
            "confidence": 0.9,
        }
    )
    r = _ingest({"content": content, "contentType": "json", "docType": "form16"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "parsed"
    assert body["classificationConfidence"] == 1.0
    assert body["extracted"]["assessmentYear"] == "2024-25"
    assert body["extracted"]["partA"]["tdsDeducted"] == 181500.0


def test_json_passthrough_infers_doc_type_from_payload() -> None:
    content = json.dumps({"documentType": "ais", "pan": "ABCPS6789Q"})
    r = _ingest({"content": content, "contentType": "json"})
    body = r.json()
    assert body["docType"] == "ais"
    assert body["status"] == "parsed"


def test_json_passthrough_invalid_field_needs_review() -> None:
    content = json.dumps({"documentType": "form_16", "partA": {"grossSalary": "not-a-number"}})
    r = _ingest({"content": content, "contentType": "json", "docType": "form16"})
    body = r.json()
    assert body["status"] == "needs_review"
    assert any(f.startswith("validation:") for f in body["flags"])
    # Offending field dropped, schema default retained; nothing invented.
    assert body["extracted"]["partA"]["grossSalary"] == 0.0


def test_invalid_json_content_is_rejected() -> None:
    r = _ingest({"content": "{not json", "contentType": "json", "docType": "form16"})
    assert r.status_code == 422


@pytest.mark.parametrize("payload", [{}, {"content": ""}, {"content": "x", "contentType": "pdf"}])
def test_invalid_request_shape_is_rejected(payload: dict[str, Any]) -> None:
    assert _ingest(payload).status_code == 422


def test_document_id_generated_when_absent() -> None:
    r = _ingest({"content": FORM16_TEXT})
    assert r.json()["documentId"]
