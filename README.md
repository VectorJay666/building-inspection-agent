# building-inspection-agent

给巡检员和业主用的辅助工具：把现场量到的**裂缝宽度**和**房屋倾斜**，整理成一份能拿出来对账的证据——超标才报警，材料不全就卡住，方便复看、复测。**不替持证工程师签字。**

当前版本（v0）只做「体检引擎」：读入检测 JSON，标出超线的点，按紧急程度排序，并挂上完整证据链。

## 这是什么 / 不是什么

**是什么：** 你把裂缝（毫米）和倾斜（度）的读数丢进去，它告诉你三件事——哪些点真的超了线、该先复测哪一处、每一条告警凭什么成立。

**不是什么：** 它不是竣工验收，不是结构鉴定报告，也不是法定签字结论。签字辅助（层 ①）和出报告（层 ③）在 v0 **没有运行**；Demo 里最多亮一下「尚未启用」。

人话版免责：**机器可以帮你把证据摆齐，最后仍须持证工程师判断和签字。** 辅助决策，不替代签字工程师。

## 为什么做

今天很多房屋安全巡检，还是人爬危楼、本子记一笔、回去再把结论「写圆」：

- **人上危楼**：裂缝几毫米、楼歪了几度，记在同一本子里。过后对不上数，也说不清当时用的是哪条线。
- **本子记不清**：没超标的点和超标的点混在一起，「看起来都有问题」，现场排不出先复测哪一处。
- **结论事后补圆**：报告阶段才补阈值、补规则编号、补一段话。系统若在缺材料时仍生成漂亮结论，就是在掩盖问题。

v0 先把规矩钉死：非法读数直接拒绝、只告超阈值、缺证据就卡住、不允许静默失败。传感器或无人机以后接入，也必须走同一套读数格式，避免引擎和报告各说各话。

## 三层怎么理解

把整套系统想成一次体检：**先量、再看、再出单**。编号是产品层 id，不是流水线顺序。真正的处理顺序是 **② → ① → ③**。详见 `docs/ARCHITECTURE.md`。

| 层 | 类比 | 实际做什么 | v0 |
| --- | --- | --- | --- |
| **② 引擎** | **体检**：量血压、量体温，超线才标红 | ingest → flag → rank → attach | **锁定**：本仓库唯一实现范围（`skills/runtime/`） |
| **① 决策** | **诊断**：医生看完体检单，给出建议并签字 | 签字辅助 / 复核建议 | **不运行**；Demo 只 tease |
| **③ 导出** | **出报告**：写成可归档的报告、工单 | 报告 / 工单 / 归档 | **不运行**；沿用同一套 Schema |

```
JSON 批次 ──► ② 引擎（体检）──► 证据链或 BLOCK ──► ① 决策（后）──► ③ 导出（后）
```

v0 停在体检：给出证据链，或明确卡住。① / ③ 尚未启用，Demo 不得把它们跑起来并假装已经签字。

## 怎么跑

环境：Python 3，无额外框架。下面三条命令分别演示「只有超标的点会响」「倾斜超限会排复测」「两处超限谁更急」；最后一条用来核对系统不会偷偷补数据。

```bash
python3 demo/run_mock_loop.py data/mock/g01.json
python3 demo/run_mock_loop.py data/mock/g02.json
python3 demo/run_mock_loop.py data/mock/g03.json
python3 -m skills.runtime.goldens
python3 tests/run_goldens.py
```

| 入口 | Demo 在演示什么 |
| --- | --- |
| `g01.json` | 三点里只有裂缝 4.2 mm 的 A 超线；B、C 低于阈值，保持安静 |
| `g02.json` | 倾斜 0.8° 超 0.5°，排出优先级并生成复测任务 |
| `g03.json` | 两处超限，排序稳定（同一批再跑一遍，顺序不变） |
| `goldens` | G01–G08：拒绝、丢弃、未知指标、BLOCK 都必须明说，禁止静默补全 |

脚本调用真实 pipeline（ingest → flag → rank → attach）并打印 accepted/rejected、alerts、ranked+recheck、attached/blocked。空数组或非法 JSON 停在 ingest，不编造读数。

同一入口保持：

1. `ingest_readings` — 校验为 `InspectionReading[]`；非法拒绝；**全部拒绝则不调用下游**
2. `flag_anomalies` — 默认规则见下；只输出超限 + 位置
3. `rank_priorities` — 严重度排序 + 复测任务；缺证据字段则丢弃（记日志）
4. `attach_evidence` — 完整证据链；缺任一必填字段 → **BLOCK**

不要在 mock 环里启动 ① 或 ③。金样也可：`python3 tests/run_goldens.py`。

## Demo UI

四栏静态页（无需构建）：打开 `demo/index.html`，或在仓库根目录执行 `python3 -m http.server 8080` 后访问 http://localhost:8080/demo/ 。默认 G01；先导入再点 **Run ②**。步骤对照见 `demo/README.md` 与 `demo/STORYBOARD.md`。

## 证据契约

挂证据是为了事后能复核：这条告警量的是什么、超了哪条线、按哪条规则、结论从哪来。缺任何一项，就不能交出去一份「看起来完整」的结论。

Schema：`schemas/evidence-chain-item.schema.json`。

**必填字段：** `reading_id`, `sensor_or_point`, `metric`, `value`, `threshold`, `rule_id`, `timestamp`, `location_tag`, `conclusion`, `confidence`

缺任何一个：`attach_evidence` **必须 BLOCK**，禁止编造 `threshold` / `rule_id` / `conclusion` / `confidence`。  
`rank_priorities` 遇到缺字段的告警应丢弃并显式记录，而不是排进列表。

| 术语 | 定义 |
| --- | --- |
| **BLOCK** | `attach_evidence` 因缺任一必填字段而拒绝挂链；记录原因，不附部分证据、不编造字段 |
| **SILENT_FAIL** | 把坏数据丢掉却不记账，或偷偷补 `threshold` / `rule_id` / `conclusion` 让流水线「看起来成功」。**禁止** |

验收总闸：**0 SILENT_FAIL**（`tests/GOLDEN_CASES.md`）。

## 默认阈值

告警线是产品锁定值，不是现场口头约定。等于阈值不告警；表里没有的指标，禁止临时编一条线。

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
  NARRATIVE.md         # 口播 / 演示脚本（pitch / script）与免责声明
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
  index.html           # 四栏最小 UI（左导入 / 中标记 / 右列表 / 底抽屉）
  README.md            # 如何打开 UI，并对照 storyboard
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

人话版：它可以帮你把「哪条裂缝超了 3 毫米、哪处倾斜超了 0.5 度、凭哪条规则」摆清楚，方便复测和复核；**不能**当成已经验收合格，也**不能**代替持证工程师签字。

## 路线图

- **v0（当前）**：Schema、Skill 契约、g01–g08 金样 fixture、storyboard、**executable layer ② runtime**。
- **Demo UI**：`demo/index.html` 四栏布局，不接入 ①。
- **硬件后期**：裂缝仪 / 倾角 / 影像量测 / 无人机 写入同一 `InspectionReading`（`metric` + `value` + `unit` + `location_tag` + 可选 `building_id`），不另起数据模型。
- **① / ③**：证据链稳定后再做决策辅助与导出。
