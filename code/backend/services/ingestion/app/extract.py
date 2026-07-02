"""Structured extraction dispatch, payload assembly, and schema validation."""

from __future__ import annotations

from typing import Any, NamedTuple

from pydantic import BaseModel, ValidationError
from pydantic.alias_generators import to_camel
from verra_shared.tax.extraction import AIS, Form16, Form26AS

from .extract_ais import extract_ais
from .extract_common import FieldHit, FieldPath
from .extract_form16 import extract_form16
from .extract_form26as import extract_form26as

_MODELS: dict[str, type[BaseModel]] = {
    "form16": Form16,
    "form26as": Form26AS,
    "ais": AIS,
}
_EXTRACTORS = {
    "form16": extract_form16,
    "form26as": extract_form26as,
    "ais": extract_ais,
}
_MAX_VALIDATION_RETRIES = 3


class ExtractionOutcome(NamedTuple):
    """Validated extraction output with per-field provenance metadata."""

    extracted: dict[str, Any]
    field_meta: dict[str, dict[str, Any]]
    hits: tuple[FieldHit, ...]
    flags: tuple[str, ...]


def camel_path(path: FieldPath) -> str:
    """Render a schema path as a camelCase dotted path, e.g. ``partA.grossSalary``."""
    parts: list[str] = []
    for segment in path:
        if isinstance(segment, int):
            parts = [*parts[:-1], f"{parts[-1]}[{segment}]"]
        else:
            parts = [*parts, to_camel(segment)]
    return ".".join(parts)


def _with_value(node: Any, path: FieldPath, value: object) -> Any:
    """Return a new nested structure with ``value`` set at ``path`` (no mutation)."""
    if not path:
        return value
    head, rest = path[0], path[1:]
    if isinstance(head, int):
        items = list(node) if isinstance(node, list) else []
        padded = items + [{} for _ in range(head + 1 - len(items))]
        return [
            _with_value(item, rest, value) if index == head else item
            for index, item in enumerate(padded)
        ]
    mapping = dict(node) if isinstance(node, dict) else {}
    return {**mapping, head: _with_value(mapping.get(head, {}), rest, value)}


def _without_path(node: Any, loc: tuple[Any, ...]) -> Any:
    """Return a copy of ``node`` with the value at ``loc`` removed."""
    if not loc:
        return node
    head = loc[0]
    if len(loc) == 1:
        if isinstance(node, dict):
            return {key: value for key, value in node.items() if key != head}
        if isinstance(node, list) and isinstance(head, int) and head < len(node):
            return [value for index, value in enumerate(node) if index != head]
        return node
    if isinstance(node, dict) and head in node:
        return {**node, head: _without_path(node[head], loc[1:])}
    if isinstance(node, list) and isinstance(head, int) and head < len(node):
        return [
            _without_path(value, loc[1:]) if index == head else value
            for index, value in enumerate(node)
        ]
    return node


def validate_payload(
    doc_type: str, payload: dict[str, Any]
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Validate against the doc-type schema; drop invalid fields and flag them.

    Returns the validated camelCase dump plus flags. If validation cannot be
    repaired the partial payload is returned with a ``schema_validation_failed``
    flag instead of raising.
    """
    model_cls = _MODELS.get(doc_type)
    if model_cls is None:
        raise ValueError(f"Unsupported doc type for extraction: {doc_type}")
    flags: tuple[str, ...] = ()
    working = payload
    for _ in range(_MAX_VALIDATION_RETRIES):
        try:
            model = model_cls.model_validate(working)
            return (model.model_dump(by_alias=True, mode="json"), flags)
        except ValidationError as exc:
            for error in exc.errors():
                loc = tuple(error["loc"])
                flags = (
                    *flags,
                    f"validation:{'.'.join(str(part) for part in loc)}:{error['type']}",
                )
                working = _without_path(working, loc)
    return (working, (*flags, "schema_validation_failed"))


def extract_document(doc_type: str, text: str) -> ExtractionOutcome:
    """Run the doc-type extractor and validate the assembled payload."""
    extractor = _EXTRACTORS.get(doc_type)
    if extractor is None:
        raise ValueError(f"Unsupported doc type for extraction: {doc_type}")
    hits, extractor_flags = extractor(text)
    payload: dict[str, Any] = {}
    for hit in hits:
        payload = _with_value(payload, hit.path, hit.value)
    if hits:
        mean_confidence = sum(hit.confidence for hit in hits) / len(hits)
        payload = {**payload, "confidence": round(mean_confidence, 3)}
    extracted, validation_flags = validate_payload(doc_type, payload)
    field_meta = {
        camel_path(hit.path): {"confidence": hit.confidence, "section": hit.section} for hit in hits
    }
    return ExtractionOutcome(
        extracted=extracted,
        field_meta=field_meta,
        hits=hits,
        flags=(*extractor_flags, *validation_flags),
    )


def extract_fields(doc_type: str, text: str) -> dict[str, Any]:
    """Public extraction API: validated fields + per-field confidence metadata."""
    outcome = extract_document(doc_type, text)
    return {
        "extracted": outcome.extracted,
        "fieldMeta": outcome.field_meta,
        "flags": list(outcome.flags),
    }
