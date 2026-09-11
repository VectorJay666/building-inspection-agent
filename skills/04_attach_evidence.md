# Skill: attach_evidence

Pipeline order: **4 / 4**

Build the **full evidence chain** for ranked alerts. Missing **any** required evidence field → **BLOCK**. No hallucination: conclusions only from value, threshold, and `rule_id`.

## Runtime

Python: `from skills.runtime import attach_evidence`

```python
from skills.runtime import attach_evidence

out = attach_evidence(ranked_items)
# out["attached"] — EvidenceChainItem[] (schema-valid)
# out["blocked"]  — explicit BLOCK records listing missing/invalid fields
```

`conclusion` is written only as `{metric} {value} > {threshold} ({rule_id})`.  
`confidence` is `1.0` when the rule matched deterministically. Same input → identical text (G08).

Implementation: `skills/runtime/attach.py`. Schema: `schemas/evidence-chain-item.schema.json`.

CLI: `python3 demo/run_mock_loop.py data/mock/g01.json`  
Goldens: `python3 -m skills.runtime.goldens` (G06 calls this skill directly with a faulty alert missing `threshold` / `rule_id`).

This skill **must not** invoke layer ① decision or ③ export.

## Trigger

- Called with the ranked list from `rank_priorities`.
- Demo: selecting a mark / list row opens the **bottom evidence drawer**.
- Must not run the decision layer ①.

## Required evidence fields

See `schemas/evidence-chain-item.schema.json`:

`reading_id`, `sensor_or_point`, `metric`, `value`, `threshold`, `rule_id`, `timestamp`, `location_tag`, `conclusion`, `confidence`

**If any required field is missing → BLOCK.** Do not invent conclusions. Do not attach a partial chain.

On input, `conclusion` and `confidence` are produced by this skill from `value`, `threshold`, and `rule_id`. The other listed fields must already be present and typed correctly.

## Steps

1. For each ranked item, check every required field (presence + type).
2. Incomplete → `status: blocked`, reason listing missing fields; skip drawer attach for that item.
3. Complete → write `conclusion` only from the fired rule (e.g. `crack_mm 4.2 > 3 (rule.crack_mm.gt_3)`). `confidence` from the rule engine (placeholder: `1.0` when rule matched deterministically).
4. Repeat input MUST yield **identical** conclusions (G08).
5. Return `{ attached: EvidenceChainItem[], blocked: Block[] }`.
6. Stop. Tease layer ① in the UI copy only — **do not run it**.

## Tools (placeholders)

| Tool | Purpose |
| --- | --- |
| `validate_evidence_item` | Schema + required-field gate |
| `block_attach` | Explicit BLOCK record, no filler text |
| `write_evidence_chain` | Persist / emit attached rows |
| `render_evidence_drawer` | Demo bottom drawer (Demo engineer) |

## Failure / retry

| Case | Action |
| --- | --- |
| Missing `threshold` or `rule_id` (G06) | **BLOCK**; no conclusion |
| Missing `conclusion` source facts | **BLOCK**; never free-write |
| Schema invalid | **BLOCK** that item |
| Downstream ① / ③ called | Out of scope for v0 — refuse |

No retry that fabricates fields. Operator may fix the upstream alert and re-run the pipeline.

## Success criteria

- Complete items get a full chain matching the schema.
- G06: over-threshold but missing `threshold` / `rule_id` → attach **blocked**.
- G08: same batch twice → identical conclusions.
- Drawer shows chain or BLOCK reason, never a guessed story.
- **0 SILENT_FAIL**.
