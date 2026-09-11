# Skill: flag_anomalies

Pipeline order: **2 / 4**

Compare accepted readings to **default rules**. Emit **only** over-threshold items, each tagged with location. Never invent thresholds for unknown metrics.

> Implementation: **TODO** — Skills engineer fills the runtime later. This file is the stub contract.

## Trigger

- Called only with `InspectionReading[]` from `ingest_readings` (`accepted.length > 0`).
- Must not run on raw / unvalidated JSON.

## Default rules (v0, locked)

| metric | condition | `rule_id` | `threshold` |
| --- | --- | --- | --- |
| `crack_mm` | `value > 3` | `rule.crack_mm.gt_3` | `3` |
| `tilt_deg` | `value > 0.5` | `rule.tilt_deg.gt_0_5` | `0.5` |

Equality is **not** an alert (`3` crack / `0.5` tilt stay quiet).

Unknown `metric`: **do not invent a threshold**. Skip-with-explicit-notice or treat as non-alerting; never fabricate a rule.

## Steps

1. For each reading, look up the default rule by `metric`.
2. If no rule exists → do not alert; record `UNKNOWN_METRIC` (visible, not silent).
3. If `value` is not over threshold → drop (no alert object).
4. If over threshold → emit alert with at least: `reading_id`, `sensor_or_point`, `metric`, `value`, `threshold`, `rule_id`, `timestamp`, `location_tag`.
5. Pass the alert list to `rank_priorities`. Empty list is valid (no invent).

## Tools (placeholders)

| Tool | Purpose |
| --- | --- |
| `load_default_rules` | Return the two locked rules above |
| `compare_threshold` | Strict `value > threshold` |
| `emit_alert` | Alert object with location; no extra narrative |

## Failure / retry

| Case | Action |
| --- | --- |
| Missing `value` (should have been ingested) | Do not flag; send back / fail item visibly |
| Unknown metric | No invented threshold; explicit `UNKNOWN_METRIC` |
| Rule table unavailable | Fail the skill; do not guess 3 / 0.5 from memory if config is required to be loaded — v0 may inline the table above, but MUST NOT add extra metrics |

No retry that changes thresholds.

## Success criteria

- G01: only point A alerts; B (`tilt 0.2`) and C (`crack 1.0`) do not.
- G02: the single `tilt 0.8` point alerts.
- G07: unknown metric produces **no** invented threshold.
- Alerts always include `location_tag`.
- **0 SILENT_FAIL**.
