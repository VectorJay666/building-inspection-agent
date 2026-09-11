"""Skill 4: attach_evidence — full chain or BLOCK; no hallucinated conclusions."""

from __future__ import annotations

from typing import Any

from skills.runtime.rank import EVIDENCE_SOURCE_FIELDS
from skills.runtime.rules import grounded_conclusion
from skills.runtime.validate import (
    SchemaMissingError,
    is_json_number,
    is_nonempty_str,
    reading_id_if_present,
    validate_evidence_chain_item,
)

DETERMINISTIC_CONFIDENCE = 1.0


def _field_problems(item: Any) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    invalid: list[str] = []
    if not isinstance(item, dict):
        return list(EVIDENCE_SOURCE_FIELDS), ["<not an object>"]
    for field in EVIDENCE_SOURCE_FIELDS:
        if field not in item:
            missing.append(field)
            continue
        value = item[field]
        if field in {"value", "threshold"}:
            if not is_json_number(value):
                invalid.append(field)
        elif not is_nonempty_str(value):
            invalid.append(field)
    return missing, invalid


def _block_record(
    item: Any,
    *,
    reason: str,
    missing_fields: list[str] | None = None,
    invalid_fields: list[str] | None = None,
    schema_errors: list[str] | None = None,
    index: int | None = None,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "status": "blocked",
        "reason": reason,
    }
    if index is not None:
        rec["index"] = index
    rid = reading_id_if_present(item)
    if rid is not None:
        rec["reading_id"] = rid
    if missing_fields:
        rec["missing_fields"] = list(missing_fields)
    if invalid_fields:
        rec["invalid_fields"] = list(invalid_fields)
    if schema_errors:
        rec["schema_errors"] = list(schema_errors)
    return rec


def attach_evidence(ranked: list[dict[str, Any]]) -> dict[str, Any]:
    """Build evidence-chain rows. Missing any required source field → BLOCK.

    ``conclusion`` and ``confidence`` are written here from value, threshold,
    and rule_id (confidence 1.0 when the rule matched deterministically).
    They are not required on the input.

    Returns::

        {"attached": [EvidenceChainItem, ...], "blocked": [Block, ...]}
    """
    try:
        from skills.runtime.validate import EVIDENCE_SCHEMA_NAME, load_schema

        load_schema(EVIDENCE_SCHEMA_NAME)
    except SchemaMissingError as exc:
        return {
            "attached": [],
            "blocked": [
                {
                    "status": "blocked",
                    "reason": str(exc),
                    "code": "SCHEMA_FILE_MISSING",
                }
            ],
        }

    if not isinstance(ranked, list):
        return {
            "attached": [],
            "blocked": [
                _block_record(
                    None,
                    reason=(
                        "FAIL: attach_evidence requires a ranked list; "
                        f"got {type(ranked).__name__}"
                    ),
                )
            ],
        }

    attached: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for index, item in enumerate(ranked):
        missing, invalid = _field_problems(item)
        if missing or invalid:
            parts = ["BLOCK: required evidence field missing or invalid; conclusion not invented"]
            if missing:
                parts.append(f"missing={missing}")
            if invalid:
                parts.append(f"invalid={invalid}")
            blocked.append(
                _block_record(
                    item,
                    reason="; ".join(parts),
                    missing_fields=missing or None,
                    invalid_fields=invalid or None,
                    index=index,
                )
            )
            continue

        chain = {
            "reading_id": item["reading_id"],
            "sensor_or_point": item["sensor_or_point"],
            "metric": item["metric"],
            "value": item["value"],
            "threshold": item["threshold"],
            "rule_id": item["rule_id"],
            "timestamp": item["timestamp"],
            "location_tag": item["location_tag"],
            "conclusion": grounded_conclusion(
                item["metric"],
                item["value"],
                item["threshold"],
                item["rule_id"],
            ),
            "confidence": DETERMINISTIC_CONFIDENCE,
        }
        schema_errors = validate_evidence_chain_item(chain)
        if schema_errors:
            blocked.append(
                _block_record(
                    item,
                    reason=(
                        "BLOCK: produced chain failed evidence schema; "
                        "partial chain not attached"
                    ),
                    schema_errors=schema_errors,
                    index=index,
                )
            )
            continue
        attached.append(chain)

    return {"attached": attached, "blocked": blocked}
