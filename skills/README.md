# Skills (layer ② engine)

v0 locks this pipeline only. The four skills are executable Python functions in `skills/runtime/`.

```
ingest_readings → flag_anomalies → rank_priorities → attach_evidence
     (1)                (2)               (3)                (4)
```

| Order | Contract | Runtime |
| --- | --- | --- |
| 1 | `01_ingest_readings.md` | `skills.runtime.ingest_readings` |
| 2 | `02_flag_anomalies.md` | `skills.runtime.flag_anomalies` |
| 3 | `03_rank_priorities.md` | `skills.runtime.rank_priorities` |
| 4 | `04_attach_evidence.md` | `skills.runtime.attach_evidence` |

Do not call ① decision or ③ export from this runtime.

Gate: **0 SILENT_FAIL**.

## How to call

From repo root (no extra packages; stdlib only):

```bash
python3 demo/run_mock_loop.py data/mock/g01.json
python3 demo/run_mock_loop.py data/mock/g02.json
python3 demo/run_mock_loop.py data/mock/g03.json
python3 demo/run_mock_loop.py /dev/stdin <<< '[]'
```

Programmatic:

```python
from pathlib import Path
from skills.runtime import (
    ingest_readings,
    flag_anomalies,
    rank_priorities,
    attach_evidence,
    run_pipeline,
    run_pipeline_from_path,
)

# Full pipeline (skips flag/rank/attach when accepted is empty)
result = run_pipeline_from_path(Path("data/mock/g01.json"))

# Or each skill:
ingest = ingest_readings([{...}, ...])          # {accepted, rejected, batch_error}
if ingest["accepted"]:
    flag = flag_anomalies(ingest["accepted"])   # {alerts, notices}
    rank = rank_priorities(flag["alerts"])      # {ranked, dropped}
    attach = attach_evidence(rank["ranked"])    # {attached, blocked}
```

Goldens (G01–G08 fixtures in `data/mock/`):

```bash
python3 -m skills.runtime.goldens
python3 tests/run_goldens.py
```

Markdown files in this directory remain the **behavior contract**. The package must not invent readings, thresholds, `rule_id`, or conclusions.
