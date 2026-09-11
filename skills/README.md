# Skills (layer ② engine)

v0 locks this pipeline only. Implementation of each skill is **TODO**.

```
ingest_readings → flag_anomalies → rank_priorities → attach_evidence
     (1)                (2)               (3)                (4)
```

| Order | Stub | Role |
| --- | --- | --- |
| 1 | `01_ingest_readings.md` | Validate JSON batch → `InspectionReading[]` |
| 2 | `02_flag_anomalies.md` | Default thresholds; over-threshold + location only |
| 3 | `03_rank_priorities.md` | Stable severity sort + recheck; drop incomplete evidence |
| 4 | `04_attach_evidence.md` | Full chain or **BLOCK**; no hallucination |

Do not call ① decision or ③ export from these stubs.

Gate: **0 SILENT_FAIL**.
