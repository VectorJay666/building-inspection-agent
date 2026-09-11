"""Skill 1: ingest_readings — JSON batch → InspectionReading[] + explicit rejections."""

from __future__ import annotations

from typing import Any

from skills.runtime.validate import (
    SchemaMissingError,
    classify_reading_errors,
    reading_id_if_present,
    validate_inspection_reading,
)


def ingest_readings(payload: Any) -> dict[str, Any]:
    """Validate a parsed JSON value.

    Returns::

        {
          "accepted": [InspectionReading, ...],
          "rejected": [{index, reading_id?, code, reason}, ...],
          "batch_error": str | None,
        }

    Non-array payloads fail the batch (do not invent an array). Empty arrays
    succeed with accepted=[] — caller must not invoke downstream skills.
    """
    try:
        # Touch the schema up front so a missing file fails the skill, not items.
        from skills.runtime.validate import load_schema, READING_SCHEMA_NAME

        load_schema(READING_SCHEMA_NAME)
    except SchemaMissingError as exc:
        return {
            "accepted": [],
            "rejected": [],
            "batch_error": str(exc),
        }

    if not isinstance(payload, list):
        kind = type(payload).__name__
        return {
            "accepted": [],
            "rejected": [],
            "batch_error": (
                f"FAIL: batch must be a JSON array; entire payload rejected "
                f"(got {kind})"
            ),
        }

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for index, item in enumerate(payload):
        errors = validate_inspection_reading(item)
        if errors:
            rec: dict[str, Any] = {
                "index": index,
                "code": classify_reading_errors(item, errors),
                "reason": "; ".join(errors),
            }
            rid = reading_id_if_present(item)
            if rid is not None:
                rec["reading_id"] = rid
            rejected.append(rec)
            continue
        # Schema passed: copy so later skills cannot mutate the caller's batch.
        assert isinstance(item, dict)
        accepted.append(dict(item))

    return {
        "accepted": accepted,
        "rejected": rejected,
        "batch_error": None,
    }
