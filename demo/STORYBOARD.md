# Demo storyboard (60–90s)

Layer ② only. **Tease** decision layer ① in the last beat — **do not run it**.

## Layout (locked)

```
┌─────────────┬──────────────────────────┬─────────────────┐
│ LEFT        │ CENTER                   │ RIGHT           │
│ Import      │ Marks on plan / points   │ Ranked list     │
│ JSON batch  │ (A / P1 / N-wall …)      │ + recheck hints │
├─────────────┴──────────────────────────┴─────────────────┤
│ BOTTOM: Evidence drawer (chain or BLOCK reason)          │
└──────────────────────────────────────────────────────────┘
```

- **Left:** import `data/mock/g0*.json`
- **Center:** location marks (only over-threshold points light up)
- **Right:** ranked alert list
- **Bottom:** evidence drawer (full chain; never a guessed story)

## Beats

| t | Voice / action | On screen |
| --- | --- | --- |
| 0–8s | “导入检测读数。” Import `g01.json`. | Left shows 3 readings (A 4.2 / B 0.2 / C 1.0). Center still quiet. |
| 8–20s | “超阈值才告警。” Run ingest → flag. | **Only A** lights on the plan. B, C stay dark. Right list length 1. |
| 20–35s | Switch to `g02.json`. “倾斜超 0.5，排优先级并生成复测。” | Single P1 mark. Right: tilt alert + **recheck** task. |
| 35–50s | Switch to `g03.json`. “两处超限，排序稳定。” | Two marks. Right: E-corner then N-wall (stable). Re-import: **same order**. |
| 50–70s | Click A or top row. Open **bottom drawer**. | Evidence chain: reading, metric, value, threshold, `rule_id`, conclusion, confidence. Say: 缺字段会 **BLOCK**，不会编结论。 |
| 70–90s | **Tease ①** only. Do not navigate into a decision UI. | Overlay / disabled control: “① 决策层（签字辅助）— v0 未启用”. Disclaimer: **辅助决策，不替代签字工程师**. Fade out. |

## Must not happen on camera

- Marks for under-threshold B / C on G01
- Empty batch spawning fake points (G04)
- Drawer text without `threshold` / `rule_id`
- Actually running layer ① or ③

## Demo engineer notes

Four-pane UI: open `demo/index.html` (see `demo/README.md`). This storyboard is the recording contract. Default path is mock G01–G03; do not invent extra thresholds for the take.
