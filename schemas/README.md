# Schemas

v0 contracts for layer ② (engine). Hardware ingest later MUST reuse the same shapes.

| File | Type |
| --- | --- |
| `inspection-reading.schema.json` | Batch item accepted by `ingest_readings` |
| `evidence-chain-item.schema.json` | One row in the evidence chain |

## Evidence contract (hard gate)

`attach_evidence` required fields:

`reading_id`, `sensor_or_point`, `metric`, `value`, `threshold`, `rule_id`, `timestamp`, `location_tag`, `conclusion`, `confidence`

If **any** required field is missing, empty, or not of the declared type:

1. `attach_evidence` **MUST BLOCK** that item (and MUST NOT attach a partial chain).
2. It MUST NOT invent `threshold`, `rule_id`, `conclusion`, or `confidence`.
3. The failure MUST be explicit. **SILENT_FAIL = 0** — never drop, fill, or “helpfully complete” evidence.

`rank_priorities` MUST drop items that already lack evidence fields rather than ranking them.

Unknown `metric` values MUST NOT receive an invented threshold. Default rules exist only for `crack_mm` and `tilt_deg` (see README).
