# novatech-retrieval-benchmark-1.0.0

**FROZEN · dataset promotion APPROVED · 2026-09-14。Benchmark 未授权、未执行。**

Human 决定 `H-BC01-FREEZE-PROMOTION-1.0.0-2026-09-14`：

> 认可 freeze-review-1.0.0-rc1 审阅包及其 manifest 绑定的内容，批准生成并冻结正式数据集 novatech-retrieval-benchmark-1.0.0，批准 dataset promotion；沿用已批准范围和局限，不运行 Benchmark。

本版本按已批准审阅包生成。批准绑定的 RC manifest SHA-256 为 `51de201c1e65b9e27c163f6186d9b6510e07990ec39d5e52d2caffe9ce577265`，RC dataset SHA-256 为 `d3ff1c8720b0603fbb3614219b4b9f71219f05c58231c33493336e56099e85ae`；两份原文件保存在 approval-input/。原 RC 保持待审批时内容，以保留真实历史。

| 内容 | 冻结范围 |
|---|---|
| 题集 | BC01-Q001–Q040；32A+8U；不含六道 Pilot 题 |
| 语料 | 四份 NovaTech 原文、novatech-pilot-0.1、t2001-novatech-pilot-01 冻结 38 块 |
| 标注 | 1,520 项人工等级、40 题完整 coverage |
| 分组 | 20 个 family；Dev/Test 各 16A+4U |
| 来源 | 原文、快照、原建议和各轮真实批准证据保存在 evidence/ |
| 正式冻结 / promotion | 已批准并落盘；未改题目、等级、coverage、事实或 split |

[dataset.json](dataset.json) 为正式输入；[approval.json](approval.json) 记录实际 Human 决定；[manifest.json](manifest.json) 绑定发布文件 hash；[verification.json](verification.json) 记录全量数据校验。`purpose=benchmark` 及校验通过均不授予执行权限。

沿用全部已批局限：单一虚构组织合成政策、小样本和类别比例差异、不可回答题仅覆盖邻近政策缺值场景；共享 7 个正证据块和 2 条补充规则，Test 非盲测，不得反复调参。主指标只聚合可回答题，不能据此宣称生成拒答能力。模型/索引/Chroma 实时就绪未检查，包不含可移植向量库；重新入库会产生新的身份映射。完整局限保留于 dataset.provenance 与 evidence/size-corpus.json。

复核：项目根目录执行 `python docs/v2/evaluation/novatech-retrieval-benchmark-1.0.0/verify.py`。仅使用本地文件及纯数据 validator，无模型、检索或指标调用。核对原批准包内容一致、源文件/快照身份、全部 schema 和 review、family 隔离及文件 hash。

manifest 覆盖生成时全部发布文件（自身与随后生成的 verification.json 除外）；verification.json 记录 manifest hash 并由 verify.py 重算核对。发布内容冻结，不覆盖修改；需变更时创建新版本并按影响范围审阅。相关文件目前为工作区产物，不冒充已提交 Git 版本；Git HEAD 与工具 hash 见 manifest。

下一步为另行授权的 T2003 前实时环境/索引核对与 baseline 执行准备。**T2003 仍 TODO；本次冻结批准不授权运行 Benchmark。**
