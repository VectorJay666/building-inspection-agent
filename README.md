# building-inspection-agent

智能无人房屋安全检测系统 — **v0 只锁定层 ②（引擎）**：把检测 JSON 变成可复核的证据链。Skills runtime 在 `skills/runtime/`，由 `demo/run_mock_loop.py` 编排。

**辅助决策，不替代签字工程师。**

## 背景痛点

房屋安全巡检今天仍大量依赖纸面记录、口头阈值和事后补写结论：

- 裂缝（mm）与倾斜（deg）混在同一本子里，超限规则说不清、复核不了。
- 未超限的点与超限的点一起「看起来都有问题」，现场无法排序复测。
- 结论往往在报告阶段才被写圆，缺阈值、缺规则编号时仍会生成一段话 —— 这是 **SILENT_FAIL**。
- 硬件（传感器 / 无人机）一旦接入，若没有同一套读数 Schema，引擎与报告会再次分叉。

v0 先把契约钉死：**非法读数拒绝、只告超阈值、缺证据就 BLOCK、零静默失败**。

## 三层：① 决策 · ② 引擎 · ③ 导出

编号是产品层 id，流水线顺序是 **② → ① → ③**。详见 `docs/ARCHITECTURE.md`。

| 层 | 名称 | v0 |
| --- | --- | --- |
| **②** | 引擎（Skills）ingest → flag → rank → attach | **锁定**：本仓库唯一实现范围（`skills/runtime/`） |
| **①** | 决策（签字辅助） | 不运行；Demo 只 tease |
| **③** | 导出（报告 / 工单 / 归档） | 不运行；沿用同一套 Schema |

```
JSON 批次 ──► ② 引擎 ──► 证据链或 BLOCK ──► ① 决策（后）──► ③ 导出（后）
```

## 如何跑 Mock 环

环境：Python 3，无额外框架。

```bash
python3 demo/run_mock_loop.py data/mock/g01.json
python3 demo/run_mock_loop.py data/mock/g02.json
python3 demo/run_mock_loop.py data/mock/g03.json
python3 -m skills.runtime.goldens
python3 tests/run_goldens.py
```

脚本调用真实 pipeline（ingest → flag → rank → attach）并打印 accepted/rejected、alerts、ranked+recheck、attached/blocked。空数组或非法 JSON 停在 ingest，不编造读数。

同一入口保持：

1. `ingest_readings` — 校验为 `InspectionReading[]`；非法拒绝；**全部拒绝则不调用下游**
2. `flag_anomalies` — 默认规则见下；只输出超限 + 位置
3. `rank_priorities` — 严重度排序 + 复测任务；缺证据字段则丢弃（记日志）
4. `attach_evidence` — 完整证据链；缺任一必填字段 → **BLOCK**

不要在 mock 环里启动 ① 或 ③。

## 证据契约

Schema：`schemas/evidence-chain-item.schema.json`。

**必填字段：** `reading_id`, `sensor_or_point`, `metric`, `value`, `threshold`, `rule_id`, `timestamp`, `location_tag`, `conclusion`, `confidence`

缺任何一个：`attach_evidence` **必须 BLOCK**，禁止编造 `threshold` / `rule_id` / `conclusion` / `confidence`。  
`rank_priorities` 遇到缺字段的告警应丢弃并显式记录，而不是排进列表。

验收总闸：**0 SILENT_FAIL**（`tests/GOLDEN_CASES.md`）。

## 默认阈值

| metric | 告警条件 | `rule_id` | threshold |
| --- | --- | --- | --- |
| `crack_mm` | `value > 3` | `rule.crack_mm.gt_3` | 3 |
| `tilt_deg` | `value > 0.5` | `rule.tilt_deg.gt_0_5` | 0.5 |

等于阈值不告警。未知 metric **禁止编造阈值**（G07）。

## 仓库布局

```
README.md
docs/
  ARCHITECTURE.md      # ② → ① → ③；v0 只锁 ②
  NARRATIVE.md         # 一句话 + Crea 占位 + 免责声明
skills/
  01_ingest_readings.md … 04_attach_evidence.md
  runtime/                 # executable v0 skills + goldens
schemas/
  inspection-reading.schema.json
  evidence-chain-item.schema.json
data/mock/
  g01.json … g08.json          # 预期见该目录 README；G04–G08 金样 fixture
tests/
  GOLDEN_CASES.md      # G01–G08
  run_goldens.py       # python3 tests/run_goldens.py
demo/
  STORYBOARD.md        # 60–90s：导入→异常→优先级→证据抽屉→tease ①
  run_mock_loop.py     # layer ② pipeline CLI
```

## 团队角色

| 角色 | 负责 |
| --- | --- |
| **Cons** | 痛点、阈值与「辅助不替代签字」边界 |
| **Skills** | 四个 Skill 的 runtime（`skills/runtime/`） |
| **Test** | G01–G08 金样与 0 SILENT_FAIL 闸门 |
| **Demo** | 左导入 / 中标记 / 右列表 / 底抽屉；按 storyboard 录 60–90s |
| **Crea** | `docs/NARRATIVE.md` 口播与视觉；不改判定 |
| **Vector** | 仓库与层划分；后续硬件仍走同一 Schema |

## 免责声明

本系统用于 **辅助决策，不替代签字工程师**。层 ② 的告警、排序与证据链不是竣工验收、结构鉴定或法定签字结论。不得在 v0 演示中运行 ① 决策层并假装已签字。

## 路线图

- **v0（当前）**：Schema、Skill 契约、g01–g08 金样 fixture、storyboard、**executable layer ② runtime**。
- **v0.1**：Demo UI。
- **Demo UI**：四栏布局，不接入 ①。
- **硬件后期**：裂缝仪 / 倾角 / 影像量测 / 无人机 写入同一 `InspectionReading`（`metric` + `value` + `unit` + `location_tag` + 可选 `building_id`），不另起数据模型。
- **① / ③**：证据链稳定后再做决策辅助与导出。
