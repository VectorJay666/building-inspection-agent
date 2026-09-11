# Mock batches

JSON arrays of `InspectionReading` (`schemas/inspection-reading.schema.json`).  
Default rules: `crack_mm > 3`, `tilt_deg > 0.5`.

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

## G04–G08

Fixtures live in `tests/GOLDEN_CASES.md` (empty batch, missing value, blocked attach, unknown metric, repeat identity). Add JSON under `data/mock/` when Test implements the harness.
