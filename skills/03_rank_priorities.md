# Skill: rank_priorities

Pipeline order: **3 / 4**

Severity-sort alerts and attach **recheck** tasks. Drop items missing evidence fields. Ranking MUST be **stable** (same input → same order).

> Implementation: **TODO** — Skills engineer fills the runtime later. This file is the stub contract.

## Trigger

- Called with the alert list from `flag_anomalies` (possibly empty).
- Empty list → empty ranked list, no invented tasks.

## Steps

1. Drop any item missing fields required for later evidence (`reading_id`, `sensor_or_point`, `metric`, `value`, `threshold`, `rule_id`, `timestamp`, `location_tag`). Dropped items are logged, not ranked.
2. Compute severity key: `value / threshold` (higher first). Tie-break: `metric` (`crack_mm` before `tilt_deg`), then `location_tag` lexicographic, then `reading_id`.
3. Assign rank `1..n` in that order.
4. Attach a recheck task per remaining item, e.g. `recheck:{location_tag}:{metric}`.
5. Pass the ranked list to `attach_evidence`.

## Tools (placeholders)

| Tool | Purpose |
| --- | --- |
| `require_evidence_fields` | Drop + log incomplete alerts |
| `sort_stable` | Deterministic severity sort |
| `open_recheck_task` | One recheck task per ranked item |

## Failure / retry

| Case | Action |
| --- | --- |
| Item missing `threshold` or `rule_id` | Drop from rank; do not guess; still visible in log |
| Empty input | Success with `[]` |
| Non-numeric `value` / `threshold` | Drop + fail that item loudly |

Do not retry ranking with filled-in fields.

## Success criteria

- G02: tilt alert is ranked and has a **recheck** task.
- G03: two over-threshold alerts; order is stable across repeats.
- G06-style incomplete items never appear in the ranked list.
- **0 SILENT_FAIL**: drops are counted and reported.
