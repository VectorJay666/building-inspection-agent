"""Skill 3: rank_priorities — stable severity sort + recheck; drop incomplete evidence."""

from __future__ import annotations

from typing import Any

from skills.runtime.rules import METRIC_TIEBREAK
from skills.runtime.validate import is_json_number, is_nonempty_str, reading_id_if_present

EVIDENCE_SOURCE_FIELDS = (
    "reading_id",
    "sensor_or_point",
    "metric",
    "value",
    "threshold",
    "rule_id",
    "timestamp",
    "location_tag",
)

_NUMERIC_FIELDS = frozenset({"value", "threshold"})


def _missing_or_invalid_fields(item: Any) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    invalid: list[str] = []
    if not isinstance(item, dict):
        return list(EVIDENCE_SOURCE_FIELDS), ["<not an object>"]
    for field in EVIDENCE_SOURCE_FIELDS:
        if field not in item:
            missing.append(field)
            continue
        value = item[field]
        if field in _NUMERIC_FIELDS:
            if not is_json_number(value):
                invalid.append(field)
        elif not is_nonempty_str(value):
            invalid.append(field)
    return missing, invalid


def rank_priorities(alerts: list[dict[str, Any]]) -> dict[str, Any]:
    """Severity-sort complete alerts and attach ``recheck:{location}:{metric}``.

    Sort key (stable / fully determined):
      1. ``value / threshold`` descending
      2. metric: ``crack_mm`` before ``tilt_deg``
      3. ``location_tag`` lexicographic
      4. ``reading_id``

    Returns::

        {"ranked": [...], "dropped": [{code, reason, missing_fields, ...}, ...]}
    """
    if not isinstance(alerts, list):
        return {
            "ranked": [],
            "dropped": [
                {
                    "code": "BAD_INPUT",
                    "reason": (
                        "FAIL: rank_priorities requires an alert list; "
                        f"got {type(alerts).__name__}"
                    ),
                }
            ],
        }

    dropped: list[dict[str, Any]] = []
    complete: list[dict[str, Any]] = []

    for index, alert in enumerate(alerts):
        missing, invalid = _missing_or_invalid_fields(alert)
        if missing or invalid:
            rec: dict[str, Any] = {
                "code": "DROP_INCOMPLETE",
                "index": index,
                "reason": "dropped from rank; fields not guessed",
            }
            if missing:
                rec["missing_fields"] = missing
                rec["reason"] += f"; missing={missing}"
            if invalid:
                rec["invalid_fields"] = invalid
                rec["reason"] += f"; invalid={invalid}"
            rid = reading_id_if_present(alert)
            if rid is not None:
                rec["reading_id"] = rid
            dropped.append(rec)
            continue

        threshold = alert["threshold"]
        if threshold == 0:
            rec = {
                "code": "DROP_INCOMPLETE",
                "index": index,
                "invalid_fields": ["threshold"],
                "reason": "threshold is 0; cannot compute severity; not guessed",
            }
            rid = reading_id_if_present(alert)
            if rid is not None:
                rec["reading_id"] = rid
            dropped.append(rec)
            continue

        complete.append(dict(alert))

    def sort_key(alert: dict[str, Any]) -> tuple[Any, ...]:
        severity = alert["value"] / alert["threshold"]
        metric = alert["metric"]
        metric_rank = METRIC_TIEBREAK.get(metric, 99)
        return (-severity, metric_rank, alert["location_tag"], alert["reading_id"])

    complete.sort(key=sort_key)

    ranked: list[dict[str, Any]] = []
    for rank, alert in enumerate(complete, start=1):
        item = dict(alert)
        item["rank"] = rank
        item["severity"] = item["value"] / item["threshold"]
        item["recheck_task"] = f"recheck:{item['location_tag']}:{item['metric']}"
        ranked.append(item)

    return {"ranked": ranked, "dropped": dropped}
