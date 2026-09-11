# Golden cases G01–G08

Harness (layer ② runtime): `python3 -m skills.runtime.goldens` or `python3 tests/run_goldens.py`. These cases are the v0 acceptance list for layer ②. Fixtures: `data/mock/g01.json`–`g08.json`.

**Gate: 0 SILENT_FAIL.** Every reject, drop, unknown-metric, and BLOCK must be explicit. Invented readings, thresholds, or conclusions = fail. The harness prints `PASS` / `FAIL` / `SILENT_FAIL` (a `SILENT_FAIL` counts as a fail and violates the gate).

Default rules: `crack_mm > 3`, `tilt_deg > 0.5`.

| ID | Fixture | Expectation |
| --- | --- | --- |
| **G01** | `data/mock/g01.json` — A crack 4.2, B tilt 0.2, C crack 1.0 | **Only A** alerts. B and C must not appear in rank or evidence. |
| **G02** | `data/mock/g02.json` — single tilt 0.8 | **Only that tilt** alerts; ranked item includes a **recheck** task. |
| **G03** | `data/mock/g03.json` — two over-threshold | **Two** alerts. Rank order is **stable** across repeats (see mock README). |
| **G04** | `data/mock/g04.json` — empty batch `[]` | No downstream invent. No alerts, no evidence rows, no fake points. Ingest may succeed-with-empty; must **not** call flag/rank/attach with synthesized data. |
| **G05** | `data/mock/g05.json` — item **missing `value`**, plus valid sibling tilt 0.8 | Item **rejected** at ingest (`MISSING_VALUE`). Not flagged. Sibling valid items may proceed. |
| **G06** | `data/mock/g06.json` — over-threshold crack 4.5 | Fixture is a valid reading (healthy flag would alert). Harness feeds attach a **faulty** flag emission without `threshold`/`rule_id`. `attach_evidence` **BLOCKED**. No invented conclusion. |
| **G07** | `data/mock/g07.json` — unknown `metric` `temperature` | **No invented threshold**. Ingest may reject (schema enum) **or** flag records `UNKNOWN_METRIC` without an alert rule. Either way: zero fabricated rules. |
| **G08** | `data/mock/g08.json` — A 4.2 / B 0.2 / C 1.0, run twice | **Identical conclusions** (and identical rank). No drift, no extra wording. |

## SILENT_FAIL examples (all forbidden)

- Dropping a bad item without a rejection/BLOCK record
- Filling `threshold` / `rule_id` / `conclusion` to “keep the demo going”
- Alerting under-threshold points
- Calling ① decision from the engine path

## Fixture shapes (G05–G07)

G05: omit `value` on one object; keep other required fields. Sibling in the same array may still alert.

G06: a valid over-threshold `InspectionReading`. The harness (not ingest) simulates a **faulty** flag step that emits without `threshold`/`rule_id` — attach must still BLOCK. Do not “fix” it in attach. Running the healthy pipeline on `g06.json` is expected to attach (flag fills those fields).

G07: `"metric": "temperature"` (unknown; not `crack_mm` / `tilt_deg`). Must not become `> 3` or `> 0.5`.
