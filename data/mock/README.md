# Mock batches

JSON arrays of `InspectionReading` (`schemas/inspection-reading.schema.json`).  
Default rules: `crack_mm > 3`, `tilt_deg > 0.5`.

Harness: `python3 -m skills.runtime.goldens` (G01–G08).

## g01.json

| Point | Metric | Value | Over threshold? |
| --- | --- | --- | --- |
| A | `crack_mm` | 4.2 | **yes** (4.2 > 3) |
| B | `tilt_deg` | 0.2 | no (0.2 ≤ 0.5) |
| C | `crack_mm` | 1.0 | no (1.0 ≤ 3) |

**Expected:** only **A** alerts. B and C stay quiet. Ranked list length 1. Evidence attaches for A.

## g02.json

| Point | Metric | Value | Over threshold? |
| --- | --- | --- | --- |
| P1 | `tilt_deg` | 0.8 | **yes** (0.8 > 0.5) |

**Expected:** only that tilt point alerts, and `rank_priorities` opens a **recheck** task (`recheck:P1:tilt_deg`). Evidence attaches for P1.

## g03.json

| Point | Metric | Value | ratio `value/threshold` |
| --- | --- | --- | --- |
| N-wall | `crack_mm` | 5.1 | 5.1 / 3 ≈ 1.70 |
| E-corner | `tilt_deg` | 0.9 | 0.9 / 0.5 = 1.80 |

**Expected:** **two** alerts. Stable rank (repeat runs identical):

1. `E-corner` (higher ratio)
2. `N-wall`

Tie-break (if ratios equal): `crack_mm` before `tilt_deg`, then `location_tag`, then `reading_id`.

## g04.json

Empty batch `[]`.

**Expected:** ingest succeeds-with-empty. flag / rank / attach are **not** called. No alerts, no evidence rows, no fabricated points.

## g05.json

| Point | Metric | Value | Notes |
| --- | --- | --- | --- |
| BAD | `crack_mm` | *(omitted)* | ingest **reject** `MISSING_VALUE` |
| OK | `tilt_deg` | 0.8 | sibling proceeds; alerts (0.8 > 0.5) |

**Expected:** missing-value item is rejected and not flagged. Sibling still alerts.

## g06.json

| Point | Metric | Value | Over threshold? |
| --- | --- | --- | --- |
| X | `crack_mm` | 4.5 | **yes** (4.5 > 3) |

This is a valid `InspectionReading`. A healthy flag step would attach `threshold` / `rule_id` and evidence would attach.

**G06 harness path:** simulate a **faulty** flag emission (same reading, `threshold` and `rule_id` omitted) and call `attach_evidence`. **Expected:** explicit **BLOCK**, no invented conclusion. Rank drops the incomplete alert with an explicit drop record.

## g07.json

| Point | Metric | Value | Rule? |
| --- | --- | --- | --- |
| T1 | `temperature` | 25.0 | **none** (unknown metric) |

**Expected:** ingest rejects (`UNKNOWN_METRIC`, schema enum) **or** flag records `UNKNOWN_METRIC` with no alert. Do **not** invent `> 3` / `> 0.5` or any other threshold.

## g08.json

Same three-point mix as G01 (A crack 4.2, B tilt 0.2, C crack 1.0) with G08 ids.

**Expected:** run twice → identical rank and identical conclusion set (`crack_mm 4.2 > 3 (rule.crack_mm.gt_3)`). No drift.
