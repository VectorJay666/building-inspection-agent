"""Minimal JSON Schema checks for the two v0 contracts.

Implements the subset used by ``inspection-reading`` and ``evidence-chain-item``
(Draft 2020-12: type, required, properties, additionalProperties, enum,
minLength, minimum/maximum, format date-time). Schema files are loaded from
``schemas/``; missing files fail the skill instead of skipping validation.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

READING_SCHEMA_NAME = "inspection-reading.schema.json"
EVIDENCE_SCHEMA_NAME = "evidence-chain-item.schema.json"

KNOWN_METRICS = ("crack_mm", "tilt_deg")

_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}


class SchemaMissingError(RuntimeError):
    """Raised when a required schema file cannot be read. Fail the skill."""


def repo_root() -> Path:
    """Repository root (parent of ``skills/``)."""
    return Path(__file__).resolve().parents[2]


def schemas_dir() -> Path:
    return repo_root() / "schemas"


def load_schema(name: str) -> dict[str, Any]:
    if name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[name]
    path = schemas_dir() / name
    if not path.is_file():
        raise SchemaMissingError(
            f"FAIL: schema file missing: {path} (do not skip validation)"
        )
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaMissingError(
            f"FAIL: schema file is not valid JSON: {path}: {exc}"
        ) from exc
    if not isinstance(schema, dict):
        raise SchemaMissingError(f"FAIL: schema file is not an object: {path}")
    _SCHEMA_CACHE[name] = schema
    return schema


def is_json_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and len(value) >= 1


def is_date_time(value: str) -> bool:
    """Accept ISO-8601 timestamps as used by the mock batches (``...Z`` or offset)."""
    text = value.strip()
    if not text:
        return False
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        datetime.fromisoformat(text)
    except ValueError:
        return False
    return True


def _type_ok(instance: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "number":
        return is_json_number(instance)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    return False


def validate_instance(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Return error strings; empty list means the instance matches ``schema``."""
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_type_ok(instance, t) for t in allowed):
            got = type(instance).__name__
            errors.append(f"{path}: expected type {expected_type}, got {got}")
            return errors

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not in enum {schema['enum']}")

    if expected_type == "string" or (expected_type is None and isinstance(instance, str)):
        min_len = schema.get("minLength")
        if min_len is not None and len(instance) < min_len:
            errors.append(f"{path}: string shorter than minLength {min_len}")
        if schema.get("format") == "date-time" and not is_date_time(instance):
            errors.append(f"{path}: not a valid date-time (ISO-8601)")

    if expected_type == "number" or (expected_type is None and is_json_number(instance)):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} > maximum {schema['maximum']}")

    if expected_type == "object" or (expected_type is None and isinstance(instance, dict)):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property '{key}'")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            child = f"{path}.{key}"
            if key in properties:
                errors.extend(validate_instance(value, properties[key], child))
            elif additional is False:
                errors.append(f"{path}: additional property not allowed: '{key}'")

    return errors


def validate_inspection_reading(item: Any) -> list[str]:
    return validate_instance(item, load_schema(READING_SCHEMA_NAME))


def validate_evidence_chain_item(item: Any) -> list[str]:
    return validate_instance(item, load_schema(EVIDENCE_SCHEMA_NAME))


def reading_id_if_present(item: Any) -> str | None:
    if isinstance(item, dict):
        rid = item.get("reading_id")
        if is_nonempty_str(rid):
            return rid
    return None


def classify_reading_errors(item: Any, errors: list[str]) -> str:
    """Stable rejection code. Unknown metrics and missing value are explicit."""
    metric = item.get("metric") if isinstance(item, dict) else None
    if isinstance(metric, str) and metric not in KNOWN_METRICS:
        return "UNKNOWN_METRIC"
    if any("missing required property 'value'" in e for e in errors):
        return "MISSING_VALUE"
    if any("additional property" in e for e in errors):
        return "ADDITIONAL_PROPERTY"
    if any("expected type" in e for e in errors):
        return "BAD_TYPE"
    return "SCHEMA_INVALID"
