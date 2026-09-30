# 规模与最终语料人工批准

**SC01 / SC02 已批准；正式版本冻结与 promotion 仍 PENDING。**

决定引用：`H-BC01-SIZE-CORPUS-SC01-SC02-2026-09-14`；日期：2026-09-14；审阅人：Human project owner（未提供姓名）。

> SC01、SC02 按建议通过：接受本次 32A+8U 规模、各 split 类别缺口及已列明的适用范围局限；选择现有四份原文和冻结的 38 块作为本次最终语料，题集仅保留 Q001–Q040，不并入六道 Pilot 题；正式版本冻结与 promotion 暂不确认，不运行 Benchmark。

批准绑定原 [review.json](review.json)，SHA-256：`49e3a0d77f4205269b56a625fde885fbb459e1a972ea52ccfefa8f216660a909`。当前机器可读决定见 [reviewed-decisions-0.1.json](reviewed-decisions-0.1.json)。原建议、历史批准文件及快照不回写；以本记录确认这两个维度的后续状态。

| 维度 | 本次决定 |
|---|---|
| SC01：32A+8U，少于质量目标的 8 道可回答题 | APPROVED；接受本次规模差额，契约目标不改 |
| Dev/Test 各 16A+4U；类别分别为 4/3/5/4 与 4/5/3/4 | APPROVED；类别顺序为 Direct Fact / Paraphrase / Distractor / Multi-chunk |
| SC02：四份现有原文和冻结 38 块 | APPROVED；novatech-pilot-0.1 / t2001-novatech-pilot-01 |
| 当前题集 | 仅 BC01-Q001–Q040；不并入 PILOT-CQ-001–006 |
| 小样本、合成政策、类别不均衡、不可回答题覆盖有限、共享证据与非盲测等已披露局限 | ACCEPTED；不扩大效果结论 |
| 正式版本冻结与 promotion | PENDING |
| Benchmark 执行 | 未授权；未运行 |

所选四份原文为 employee_handbook.md、travel_policy.md、expense_policy.md、it_security_policy.md，完整逐文件 hash 见原审阅材料。snapshot SHA-256：`a2d314a9a284a1782c77376e53702a610b22ae9a3160a213ca338a55637ddd80`。

核验通过：原审阅材料及其绑定的契约、标注、split、去重、快照 hash 一致；四份源文件 hash 与快照一致；批准副本只新增 Human 决定及状态，语料/题集/计数/局限不变。既有 40 题、1,520 项等级、coverage、分组及 Dev/Test 未修改。

下一步可准备正式版本冻结审阅包（版本文件、来源清单、校验结果及最终批准范围）；本记录不批准冻结、promotion 或 T2003。实时模型/索引/存储就绪仍未检查，不把本地文件核验当作运行就绪。
