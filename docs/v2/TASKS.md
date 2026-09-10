# DX-RAG V2 任务计划

> 状态：T2001 DONE（2026-09-10 Human Final Gate PASS）；T2002/T2003 TODO，未获本次执行授权。
> 产品权威入口：`docs/v2/SPEC.md`（Phase 20 当前范围已获批；未来范围仍为 DRAFT）。执行授权边界见其第 1.1 节。
> V1 历史：`docs/TASKS.md` 保持不变。

## 执行规则

适用的 `docs/v2/SPEC.md` 范围获得人工批准、依赖满足后，每次只执行一个 Task。TODO 不代表已获批准。状态按 TODO → IN_PROGRESS → DONE 推进，所有分配的 AC 验证通过后才能标为 DONE；依赖未解决或规格冲突时记录为 BLOCKED。记录证据、审阅 diff、完成 Task Learning Pass 并报告，不得自动启动下一个 Task。

评估任务（Evaluation Task）建立测量能力。实验任务（Experiment Task）依据获批协议比较 Candidate。实现任务（Implementation Task）集成单独获批的决策。负向或无法得出结论的 Experiment，只要满足协议和证据相关 AC，也可以完成 Task；这不代表批准生产采用。

## Phase 20 — 评估基础（Evaluation Foundation）

当前 V1 Retrieval → 评估数据集 → Evaluation Runner → V1 Baseline Benchmark → 此后才可开展检索 Experiment。

### T2001 — 定义检索评估数据集契约

**状态：** DONE  
**类型：** Evaluation Task  
**依赖：** 适用的 V2 SPEC 范围获得人工审阅 / 批准；检查当前 V1 Retrieval 与历史 Baseline。  
**SPEC 引用：** `docs/v2/SPEC.md` 第 3–4 节（EVAL-01、EVAL-02 中的指标约定）。

**目标：** 在实现 Runner 前，定义可供审阅的数据集与测量契约。

**范围 / 预期位置：** 在 `docs/v2/evaluation/` 定义契约，涵盖语料 / 查询标识及版本、相关性粒度 / 等级、来源、标注 / 审阅、可回答性覆盖、数据划分 / 泄漏控制、指标约定，以及获取正当来源评估数据的计划。具体 schema 在本 Task 中确定。

**验收 / 验证（Acceptance Criteria / AC）：**

- AC-2001-1：上述契约维度均有明确定义、内部一致，并关联 V1 Retrieval 的输入 / 输出。
- AC-2001-2：Recall@K、MRR 和 nDCG@K 的约定涵盖 K、相关性映射、聚合、并列分数 / 重复项，以及缺失标注 / 无相关项的处理。
- AC-2001-3：明确指定数据获取 / 标注负责人、获授权的工作项，以及 T2003 之前的交付检查点，并记录访问限制、代表性和审阅职责。如需新增 Task，必须获得明确批准，并安排在 Baseline 采集之前；不得在 T2001 中擅自实施。标记 DONE 前，未解决的阻塞性选择必须经人工审阅解决。

**当前产物：** [Retrieval Evaluation Dataset Contract](evaluation/retrieval-evaluation-dataset-contract.md)。2026-09-09 按 `H20-APPROVAL-2026-09-09` 启动；2026-09-10 Human project owner 明确批准 T2001 IN_PROGRESS → DONE、Final Human Gate PASS 和 Dataset Contract 0.3 FROZEN。AC-2001-1/2/3 均 SATISFIED；依据包括真实 Pilot、6/6 Human Coverage APPROVED、全部 readiness READY 及无剩余契约/Pilot blocker，详见契约第 16 节。该批准仅适用于 T2001，不授权 T2002/T2003，不代表 Phase 20 Gate PASS 或正式 Benchmark Dataset 已建成。

**范围外：** Runner、伪造数据集 / 结果、检索变更或 Candidate 采用。本次文档授权不包含 Pilot 语料创建或 Benchmark 执行。

### T2002 — 实现检索评估指标与 Runner

**状态：** TODO  
**类型：** Evaluation Task  
**依赖：** T2001 DONE，且数据集 / 指标契约已经审阅。  
**SPEC 引用：** `docs/v2/SPEC.md` 第 4 节（EVAL-01、EVAL-02）、第 6 节（SAFE-01）。

**目标：** 围绕保持不变的 V1 Retrieval，实现可复现的测量。

**范围 / 预期位置：** 评估工具位置在 Task 计划中确定，协议存放于 `docs/v2/evaluation/`。遵循获批契约，计算指标，提供可重复执行的调用方式，并持久化逐查询 / 聚合输出及来源信息。

**验收 / 验证：**

- AC-2002-1：使用可手算且明确标注的 test fixtures，验证指标计算及契约边界情况。
- AC-2002-2：无效输入必须明确报错；输出标明数据集、配置、Runner 版本及测量范围。
- AC-2002-3：在声明的条件下检查可重复性；报告波动，不得隐瞒。
- AC-2002-4：相关回归检查确认检索 / 产品行为未改变；执行说明能够支持复现。

**范围外：** 检索优化、生产策略变更，以及根据 test fixtures 宣称有代表性的质量结论。

### T2003 — 采集 V1 Retrieval Baseline

**状态：** TODO  
**类型：** Evaluation Task  
**依赖：** T2002 DONE；版本化数据集已可用，并按 T2001 契约完成审阅；所需模型 / 索引 / 环境可用。  
**SPEC 引用：** `docs/v2/SPEC.md` 第 4 节（EVAL-03）、第 5 节（EXP-01）、第 6 节（SAFE-01）。

**目标：** 在检索 Experiment 前，建立真实的 V1 Benchmark 证据。

**范围 / 预期位置：** 针对已发布的 V1 行为运行经过验证的评估，将证据 / 分析存放于 `docs/v2/benchmarks/`。检查实际测量的 checkout 与 tag 的差异，不改变 Git 历史。

**验收 / 验证：**

- AC-2003-1：记录准确的 V1 参考版本、实际测量的实现 / 工具版本、数据集 / 语料 / 索引 / 模型 / 配置及命令。
- AC-2003-2：保留真实的逐查询及聚合 Recall@K、MRR 和 nDCG@K 结果，并附失败情况、局限和证据类型；不得伪造结果。
- AC-2003-3：依据声明的容差 / 条件检查复现情况；测量 latency / cost 时说明方法，否则明确标为未测量。
- AC-2003-4：Baseline 仍可复现，已验证检索行为未改变，比较局限明确。缺少前置证据时，不得完成本 Task。

**范围外：** 任何 Candidate 检索策略、效果提升声明，以及生成质量评估。

### Phase 20 出口门禁

三个 Task 均为 DONE 且具备 AC 证据后，使用 `docs/learning/templates/phase-gate-review-template.md` 开展独立 Phase Gate。检索 Experiment 必须以 Gate PASS 为前提，但 PASS 不授权自动启动未来 Phase。随后按保留的工作流完成 Phase Learning Review、Engineering Review 和独立 Interview synthesis。本次 Bootstrap 不作出任何 Gate 裁决。

## 后续路线图 — 仅为纲要，不是可执行 Task

| Phase | 研究 / 工程方向 | 进入条件 |
|---|---|---|
| 21 — 检索融合实验（Retrieval Fusion Experiments） | 比较明确选定的融合 Candidate；RRF 只是可能的 Candidate | Phase 20 PASS；协议和 Task 已获批 |
| 22 — 重排序（Reranking） | 研究相关性、latency 与 cost 的权衡 | Baseline 证据；明确的 SPEC 范围和 Task |
| 23 — 查询理解（Query Understanding） | 研究查询处理，仅在选定后评估 Query Rewrite | Baseline 证据；明确的 SPEC 范围和 Task |
| 24 — 生成质量评估（Generation Evaluation） | Faithfulness、回答 / 引用正确性、可回答性 / 拒答 | 生成评估协议和 Task 已获批 |
| 25 — 可观测性（Observability） | 根据证据识别测量缺口 | 范围和 Task 已获批 |
| 26 — 工程加固（Engineering Hardening） | 处理有证据支持的回归 / 可靠性风险 | 范围和 Task 已获批 |
| 27 — V2 最终验收（Final V2 Acceptance） | 审计获批契约及证据 | 必要的前置工作完成；验收标准已获批 |

未来依赖、Candidate 及采用标准必须在执行前定义。这些标题不代表采用相关技术，也不将 Experiment 标为 PASS。
