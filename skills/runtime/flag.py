"""Skill 2: flag_anomalies — over-threshold alerts only; never invent thresholds."""

from __future__ import annotations

from typing import Any

from skills.runtime.rules import compare_threshold, lookup_rule
from skills.runtime.validate import is_json_number, is_nonempty_str, reading_id_if_present

ALERT_FIELDS = (
    "reading_id",
    "sensor_or_point",
    "metric",
    "value",
    "threshold",
    "rule_id",
    "timestamp",
    "location_tag",
)


def flag_anomalies(readings: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare accepted readings to the locked default rules.

    Returns::

        {
          "alerts": [alert, ...],
          "notices": [{code, reading_id?, reason}, ...],
        }

    Under-threshold items are omitted (not alerts). Unknown metrics emit
    ``UNKNOWN_METRIC`` and produce no alert. Empty input yields empty alerts
    (no invented rows).
    """
    if not isinstance(readings, list):
        return {
            "alerts": [],
            "notices": [
                {
                    "code": "BAD_INPUT",
                    "reason": (
                        "FAIL: flag_anomalies requires InspectionReading[]; "
                        f"got {type(readings).__name__}"
                    ),
                }
            ],
        }

    alerts: list[dict[str, Any]] = []
    notices: list[dict[str, Any]] = []

    for index, reading in enumerate(readings):
        if not isinstance(reading, dict):
            notices.append(
                {
                    "code": "BAD_TYPE",
                    "index": index,
                    "reason": (
                        f"item {index} is not an object; not flagged "
                        f"(got {type(reading).__name__})"
                    ),
                }
            )
            continue

        rid = reading_id_if_present(reading)
        metric = reading.get("metric")
        value = reading.get("value")

        if "value" not in reading or not is_json_number(value):
            rec = {
                "code": "MISSING_VALUE",
                "index": index,
                "reason": (
                    "value missing or not numeric; not flagged "
                    "(should have been rejected at ingest)"
                ),
            }
            if rid is not None:
                rec["reading_id"] = rid
            notices.append(rec)
            continue

        rule = lookup_rule(metric)
        if rule is None:
            rec = {
                "code": "UNKNOWN_METRIC",
                "index": index,
                "reason": (
                    f"UNKNOWN_METRIC {metric!r}: no default rule; "
                    "threshold not invented; no alert"
                ),
            }
            if rid is not None:
                rec["reading_id"] = rid
            notices.append(rec)
            continue

        if not compare_threshold(value, rule["threshold"]):
            # Quiet by contract (equality is not an alert). Not a SILENT_FAIL.
            continue

        source = {
            "reading_id": reading.get("reading_id"),
            "sensor_or_point": reading.get("sensor_or_point"),
            "metric": metric,
            "value": value,
            "threshold": rule["threshold"],
            "rule_id": rule["rule_id"],
            "timestamp": reading.get("timestamp"),
            "location_tag": reading.get("location_tag"),
        }
        alert = {field: source[field] for field in ALERT_FIELDS}
        # location_tag is required on alerts; if somehow empty, notice instead of inventing.
        if not is_nonempty_str(alert.get("location_tag")):
            rec = {
                "code": "MISSING_LOCATION",
                "index": index,
                "reason": "over-threshold but location_tag missing; not alerted (not invented)",
            }
            if rid is not None:
                rec["reading_id"] = rid
            notices.append(rec)
            continue
        alerts.append(alert)

    return {"alerts": alerts, "notices": notices}
