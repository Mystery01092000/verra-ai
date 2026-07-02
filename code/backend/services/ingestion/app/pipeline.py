"""Ingestion pipeline: classify -> extract -> validate -> review gate."""

from __future__ import annotations

import json
from typing import Any, Final
from uuid import uuid4

from .classify import DOC_TYPE_UNKNOWN, classify_document
from .extract import camel_path, extract_document, validate_payload
from .extract_common import FieldHit, FieldPath
from .schemas import FieldMeta, IngestRequest, IngestResponse, IngestStatus

# PRD human-review gate thresholds.
CLASSIFICATION_REVIEW_THRESHOLD: Final = 0.6
FIELD_REVIEW_THRESHOLD: Final = 0.7

_DOC_TYPE_ALIASES: Final[dict[str, str]] = {
    "form16": "form16",
    "form_16": "form16",
    "form-16": "form16",
    "form26as": "form26as",
    "form_26as": "form26as",
    "form-26as": "form26as",
    "26as": "form26as",
    "ais": "ais",
}

# Money fields that must be present with confidence >= FIELD_REVIEW_THRESHOLD.
_REQUIRED_MONEY_FIELDS: Final[dict[str, tuple[FieldPath, ...]]] = {
    "form16": (("part_b", "gross_salary"), ("part_a", "tds_deducted")),
    "form26as": (("tds_entries",),),
    "ais": (("tds_entries",),),
}


def _normalize_doc_type(raw: str | None) -> str | None:
    if raw is None:
        return None
    return _DOC_TYPE_ALIASES.get(raw.strip().lower().replace(" ", "_"))


def _requires_money_field_review(doc_type: str, hits: tuple[FieldHit, ...]) -> bool:
    for prefix in _REQUIRED_MONEY_FIELDS.get(doc_type, ()):
        matching = tuple(hit for hit in hits if hit.path[: len(prefix)] == prefix)
        if not matching:
            return True
        if min(hit.confidence for hit in matching) < FIELD_REVIEW_THRESHOLD:
            return True
    return False


def _unsupported_response(
    document_id: str, doc_type: str, flags: tuple[str, ...]
) -> IngestResponse:
    return IngestResponse(
        document_id=document_id,
        doc_type=doc_type,
        classification_confidence=0.0,
        extracted={},
        status="unsupported",
        flags=list(flags),
    )


def _ingest_json(request: IngestRequest, document_id: str) -> IngestResponse:
    """Validate pre-extracted JSON content directly against the schema."""
    try:
        payload: Any = json.loads(request.content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"content is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON content must be an object")
    doc_type = _normalize_doc_type(request.doc_type) or _normalize_doc_type(
        payload.get("documentType") if isinstance(payload.get("documentType"), str) else None
    )
    if doc_type is None:
        raw = request.doc_type or payload.get("documentType") or "missing"
        return _unsupported_response(
            document_id, DOC_TYPE_UNKNOWN, (f"unsupported_doc_type:{raw}",)
        )
    extracted, flags = validate_payload(doc_type, payload)
    status: IngestStatus = "needs_review" if flags else "parsed"
    return IngestResponse(
        document_id=document_id,
        doc_type=doc_type,
        classification_confidence=1.0,
        extracted=extracted,
        status=status,
        flags=list(flags),
    )


def _ingest_text(request: IngestRequest, document_id: str) -> IngestResponse:
    """Classify (when needed), extract, and apply the human-review gate."""
    doc_type = _normalize_doc_type(request.doc_type)
    if request.doc_type is not None and doc_type is None:
        return _unsupported_response(
            document_id, DOC_TYPE_UNKNOWN, (f"unsupported_doc_type:{request.doc_type}",)
        )
    confidence = 1.0
    if doc_type is None:
        doc_type, confidence = classify_document(request.content)
    if doc_type == DOC_TYPE_UNKNOWN:
        return _unsupported_response(document_id, DOC_TYPE_UNKNOWN, ("unclassified_document",))

    outcome = extract_document(doc_type, request.content)
    low_confidence = [
        camel_path(hit.path) for hit in outcome.hits if hit.confidence < FIELD_REVIEW_THRESHOLD
    ]
    needs_review = (
        confidence < CLASSIFICATION_REVIEW_THRESHOLD
        or _requires_money_field_review(doc_type, outcome.hits)
        or any(
            flag.startswith("validation:") or flag == "schema_validation_failed"
            for flag in outcome.flags
        )
    )
    return IngestResponse(
        document_id=document_id,
        doc_type=doc_type,
        classification_confidence=confidence,
        extracted=outcome.extracted,
        field_meta={
            path: FieldMeta(confidence=meta["confidence"], section=meta["section"])
            for path, meta in outcome.field_meta.items()
        },
        low_confidence_fields=low_confidence,
        flags=list(outcome.flags),
        status="needs_review" if needs_review else "parsed",
    )


def ingest_document(request: IngestRequest) -> IngestResponse:
    """Process one ingest request; raises ValueError for malformed JSON content."""
    document_id = request.document_id or f"doc-{uuid4().hex[:12]}"
    if request.content_type == "json":
        return _ingest_json(request, document_id)
    return _ingest_text(request, document_id)
