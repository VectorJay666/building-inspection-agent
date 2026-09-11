# Demo UI (layer ②)

Minimal four-pane UI for closed-loop **inspection → anomalies → priorities → evidence**.
It follows `demo/STORYBOARD.md` and reads mock batches `data/mock/g01.json`–`g03.json`.

v0 **does not run** layer ① (decision) or ③ (export). The ① control is a tease only.

## Open

Static files: `demo/index.html`, `demo/styles.css`, `demo/app.js`. No build step.

### Option A — no server

Open `demo/index.html` in a browser (`file://` is fine). G01–G03 are embedded as copies of `data/mock/` so the demo still runs if `fetch` is blocked.

### Option B — tiny local server (from repo root)

```bash
python3 -m http.server 8080
```

Then open http://localhost:8080/demo/

When served this way, G01–G03 load live from `data/mock/*.json` (embedded copies are fallback only).

Default source is **G01**. Switch G02 / G03 from the left panel. Use **Run ② ingest → flag → rank → attach** after each import (center stays quiet until flag, matching the storyboard).

## Layout

| Pane | Role |
| --- | --- |
| Left | Import JSON batch (G01–G03, empty `[]`, optional custom file) |
| Center | Plan marks — **only** over-threshold points light up |
| Right | Ranked repair list + recheck tasks (`recheck:{location}:{metric}`) |
| Bottom | Evidence drawer: full chain or **BLOCKED** / no conclusion |

Default rules (same as README / skills): `crack_mm > 3`, `tilt_deg > 0.5`. Equality does not alert. Unknown metrics get no invented threshold.

## Storyboard map (60–90s)

| t | Action in this UI | Expect |
| --- | --- | --- |
| 0–8s | Left: **G01** (auto-loaded). Do **not** press Run yet. | Left lists A 4.2 / B 0.2 / C 1.0. Center quiet. |
| 8–20s | **Run ②**. | Only **A** lights. B and C stay dark. Right list length **1**. |
| 20–35s | **G02** → Run ②. | Single **P1** mark. Right: tilt alert + `recheck:P1:tilt_deg`. |
| 35–50s | **G03** → Run ②. Run again. | Two marks. Right order **E-corner** then **N-wall** (stable). |
| 50–70s | Click A / top row (or G01 row). Drawer opens. Optional: **G06 BLOCK** → Run ② → click BLOCKED row. | Full chain fields from the reading + rule. Incomplete → **BLOCKED**, no conclusion. |
| 70–90s | Click **① 决策层（签字辅助）— v0 未启用**. | Overlay tease only. Fade out. Disclaimer stays on screen. |

### Must not happen

- Alert marks for G01 B (tilt 0.2) or C (crack 1.0)
- Empty batch (`Empty []`) spawning fake points
- Drawer conclusion without `threshold` / `rule_id` (that path is BLOCKED)
- Navigating into a real ① decision UI

## Evidence fields

Drawer always lists: `reading_id`, `sensor_or_point`, `metric`, `value`, `threshold`, `rule_id`, `timestamp`, `location_tag`, `conclusion`, `confidence`.

If any required field is missing, attach **BLOCKs**. The UI does not invent thresholds, rule ids, or conclusions.

**G06 BLOCK** is a demo-only faulty-flag path (over-threshold alert emitted without `threshold` / `rule_id`) so reviewers can open a blocked drawer without adding fixtures under `data/mock/` (those remain Test-owned).

## Notes

- This UI is a **static demo of the closed loop** for reviewers (storyboard / click-through). The executable Skills runtime lives in `skills/runtime/` and is unchanged by this UI.
- CLI (do not confuse with this page): `python3 demo/run_mock_loop.py data/mock/g01.json`
