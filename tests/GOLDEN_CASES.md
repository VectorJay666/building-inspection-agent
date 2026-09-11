# Golden cases G01–G08

Harness (layer ② runtime): `python3 -m skills.runtime.goldens` or `python3 tests/run_goldens.py`. These cases are the v0 acceptance list for layer ②. Fixture JSON for G04–G08 still belongs to Test; the runtime goldens cover G01–G03 files plus inline G04–G08 shapes.

**Gate: 0 SILENT_FAIL.** Every reject, drop, unknown-metric, and BLOCK must be explicit. Invented readings, thresholds, or conclusions = fail.

Default rules: `crack_mm > 3`, `tilt_deg > 0.5`.

| ID | Fixture | Expectation |
| --- | --- | --- |
| **G01** | `data/mock/g01.json` — A crack 4.2, B tilt 0.2, C crack 1.0 | **Only A** alerts. B and C must not appear in rank or evidence. |
| **G02** | `data/mock/g02.json` — single tilt 0.8 | **Only that tilt** alerts; ranked item includes a **recheck** task. |
| **G03** | `data/mock/g03.json` — two over-threshold | **Two** alerts. Rank order is **stable** across repeats (see mock README). |
| **G04** | Empty batch `[]` | No downstream invent. No alerts, no evidence rows, no fake points. Ingest may succeed-with-empty; must **not** call flag/rank/attach with synthesized data. |
| **G05** | Batch item **missing `value`** | Item **rejected** at ingest. Not flagged. Sibling valid items may proceed. |
| **G06** | Over-threshold reading but **missing `threshold` and/or `rule_id`** when entering attach | `attach_evidence` **BLOCKED**. No invented conclusion. |
| **G07** | Unknown `metric` (not `crack_mm` / `tilt_deg`) | **No invented threshold**. Ingest may reject (schema enum) **or** flag records `UNKNOWN_METRIC` without an alert rule. Either way: zero fabricated rules. |
| **G08** | Run G01 (or G03) twice on the same input | **Identical conclusions** (and identical rank). No drift, no extra wording. |

## SILENT_FAIL examples (all forbidden)

- Dropping a bad item without a rejection/BLOCK record
- Filling `threshold` / `rule_id` / `conclusion` to “keep the demo going”
- Alerting under-threshold points
- Calling ① decision from the engine path

## Suggested G05–G07 shapes (when adding files)

G05 item: omit `value` on one object; keep other required fields.

G06: a valid over-threshold `InspectionReading` that a **faulty** flag step emits without `threshold`/`rule_id` — attach must still BLOCK. Do not “fix” it in attach.

G07: `"metric": "humidity_pct"` (or similar). Must not become `> 3` or `> 0.5`.
