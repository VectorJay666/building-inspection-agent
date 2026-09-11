# Skill: ingest_readings

Pipeline order: **1 / 4**

Validate a JSON batch into `InspectionReading[]`. Illegal items are rejected. If the entire batch is rejected (or the batch is empty after validation), **do not call downstream skills**.

## Runtime

Python: `from skills.runtime import ingest_readings, run_pipeline, run_pipeline_from_path`

```python
from skills.runtime import ingest_readings, run_pipeline_from_path

ingest = ingest_readings(payload)  # parsed JSON value
# ingest["accepted"], ingest["rejected"], ingest["batch_error"]
# Non-array or illegal JSON → batch_error; accepted remains [].
# Empty accepted → run_pipeline does not call flag_anomalies.

result = run_pipeline_from_path("data/mock/g01.json")
```

CLI: `python3 demo/run_mock_loop.py data/mock/g01.json`  
Goldens: `python3 -m skills.runtime.goldens`

Implementation: `skills/runtime/ingest.py` (JSON Schema subset against `schemas/inspection-reading.schema.json`). Missing schema file fails the skill.

## Trigger

- Operator imports a JSON file (demo left panel), **or**
- Mock loop / test harness passes a path under `data/mock/`, **or**
- Future hardware adapter emits a JSON batch that already matches `InspectionReading`.

Input: raw JSON (array expected).  
Output: `{ accepted: InspectionReading[], rejected: Rejection[] }`  
Schema: `schemas/inspection-reading.schema.json`

## Steps

1. Parse JSON. Non-JSON → fail the batch (do not invent an array).
2. Require a JSON **array**. Object/scalar → reject entire payload.
3. Validate each element against `InspectionReading` (required fields, types, `metric` enum).
4. Collect `accepted` and `rejected` (include `reading_id` when present, plus reason).
5. If `accepted.length === 0`, **stop**. Do not call `flag_anomalies`.
6. Else pass **only** `accepted` downstream.

## Tools (placeholders)

| Tool | Purpose |
| --- | --- |
| `read_json_batch` | Load file or stdin as text (`run_pipeline_from_path` / `run_pipeline_from_text`) |
| `validate_inspection_reading` | JSON Schema check per item (`skills.runtime.validate`) |
| `emit_rejection_log` | Structured reject reasons (never silent) — `rejected[]` with `code` + `reason` |

## Failure / retry

| Case | Action |
| --- | --- |
| Unreadable file / invalid JSON | Fail loud; no retry unless operator re-imports |
| Empty array (`[]`) | Success-with-empty: no invent, no downstream |
| Item missing `value` / unknown `metric` / bad types | Reject that item; continue siblings |
| All items rejected | Stop pipeline; report rejections |
| Schema file missing | Fail the skill (do not skip validation) |

Retry: only on transient I/O. Do **not** retry by guessing fields.

## Success criteria

- Accepted items are a subset of the input and match the schema.
- Rejected items are listed with reasons. **0 SILENT_FAIL**.
- Empty or all-rejected batches never call `flag_anomalies`.
- No new readings are synthesized.
