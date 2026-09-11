"""Locked v0 default rules. Do not add metrics or change thresholds here.

Equality is not an alert (strict ``value > threshold``).
"""

from __future__ import annotations

from typing import Any, TypedDict

from skills.runtime.validate import is_json_number


class DefaultRule(TypedDict):
    metric: str
    threshold: float
    rule_id: str
    condition: str


# Inline table from skills/02_flag_anomalies.md — v0 may inline; MUST NOT add extras.
DEFAULT_RULES: dict[str, DefaultRule] = {
    "crack_mm": {
        "metric": "crack_mm",
        "threshold": 3,
        "rule_id": "rule.crack_mm.gt_3",
        "condition": "value > 3",
    },
    "tilt_deg": {
        "metric": "tilt_deg",
        "threshold": 0.5,
        "rule_id": "rule.tilt_deg.gt_0_5",
        "condition": "value > 0.5",
    },
}

METRIC_TIEBREAK = {"crack_mm": 0, "tilt_deg": 1}


def load_default_rules() -> dict[str, DefaultRule]:
    """Return a copy of the two locked rules."""
    return {k: dict(v) for k, v in DEFAULT_RULES.items()}  # type: ignore[misc]


def lookup_rule(metric: Any) -> DefaultRule | None:
    if not isinstance(metric, str):
        return None
    rule = DEFAULT_RULES.get(metric)
    if rule is None:
        return None
    return dict(rule)  # type: ignore[return-value]


def compare_threshold(value: Any, threshold: Any) -> bool:
    """Strict greater-than. Equality does not alert."""
    if not is_json_number(value) or not is_json_number(threshold):
        return False
    return value > threshold


def format_number(value: float | int) -> str:
    """Stable, locale-free number text for conclusions (G08 identity)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("format_number requires a JSON number")
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
        return str(int(value))
    return format(value, ".15g")


def grounded_conclusion(metric: str, value: float, threshold: float, rule_id: str) -> str:
    """Conclusion derived only from value, threshold, and rule_id. Never free-write."""
    return (
        f"{metric} {format_number(value)} > {format_number(threshold)} ({rule_id})"
    )
