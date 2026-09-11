# Architecture

v0 **locks layer ② (engine) only**. Layers ① and ③ are named so the demo can tease them; they MUST NOT run.

```
                    ┌──────────────────────────┐
   JSON / hardware  │  ② ENGINE (v0)           │
   ───────────────► │  ingest → flag → rank    │
                    │           → attach       │
                    └────────────┬─────────────┘
                                 │ evidence chain
                                 │ (or BLOCK)
                                 ▼
                    ┌──────────────────────────┐
                    │  ① DECISION (later)      │
                    │  签字辅助 / 复核建议      │
                    │  tease only in v0        │
                    └────────────┬─────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │  ③ EXPORT (later)        │
                    │  报告 / 工单 / 归档       │
                    └──────────────────────────┘
```

Numbering is product-layer ids, not pipeline order: **② engine → ① decision → ③ export**.

## ② Engine (this repo, v0)

| Skill | Contract |
| --- | --- |
| `ingest_readings` | JSON batch → `InspectionReading[]`; illegal → rejected; all rejected / empty → no downstream |
| `flag_anomalies` | `crack_mm > 3`, `tilt_deg > 0.5`; emit over-threshold + location; never invent thresholds |
| `rank_priorities` | Stable severity sort + recheck tasks; drop items missing evidence fields |
| `attach_evidence` | Full chain or **BLOCK**; no hallucination |

Schemas: `schemas/`. Skills: `skills/` (contracts) + `skills/runtime/` (executable). Mocks: `data/mock/`. Goldens: `tests/GOLDEN_CASES.md`.

## ① Decision (out of v0)

Human-in-the-loop assistance for a licensed engineer. The engine must not auto-approve, sign, or close a building. Demo may show a disabled “①” control only.

## ③ Export (out of v0)

Export of attached evidence (and later, signed decisions) to report / ticket / archive. Same `InspectionReading` / evidence schemas; no parallel data model.

## Hardware later

Cameras, crack gauges, inclinometers, and drones SHOULD map into `InspectionReading` (`metric`, `value`, `unit`, `location_tag`, optional `building_id`). Do not fork a second reading type for v1 hardware.

## Failure philosophy

**0 SILENT_FAIL.** Reject, drop, BLOCK, or fail the skill in the open. Never invent readings, thresholds, `rule_id`, or conclusions to keep the pipeline green.
