# DX-RAG V2 — 评估驱动的 RAG 优化（Evaluation-Driven RAG Optimization）

V1 目标：构建完整的端到端 RAG 系统。

V2 目标：衡量、理解并系统性改善检索与回答质量。

## 契约与状态

| 角色 | 来源 |
|---|---|
| V1 历史基线（Baseline） | Tag `v1.0.0` → `da8be59a60d7f35a2e3c1ab835624946c53d2a55` |
| V1 冻结规格 / 任务历史 | [docs/SPEC.md](../SPEC.md)、[docs/TASKS.md](../TASKS.md) |
| 当前 V2 契约 | [docs/v2/SPEC.md](SPEC.md) > [docs/v2/TASKS.md](TASKS.md) |
| 当前 Agent 操作规范 | [CLAUDE.md](../../CLAUDE.md) |

V2 SPEC 的 **Phase 20 Evaluation Foundation 当前范围已获人工批准**，T2001 已单独获 Human Final Gate 完成批准；其余未来 V2 范围仍为 DRAFT，未自动冻结或批准。批准记录见 [docs/v2/SPEC.md 第 1.1 节](SPEC.md)。T2001 为 DONE（2026-09-10 Final Human Gate PASS），T2002/T2003 仍为 TODO，未获本次执行授权。[Dataset Contract 0.3](evaluation/retrieval-evaluation-dataset-contract.md) 已由 Human project owner 批准 FROZEN，但尚未交付评估数据集、评估执行器（Runner）、Benchmark 结果或检索候选方案（Candidate）。

2026-09-09 的 Bootstrap 检查以本地 Git 为依据：分支为 `v2/evaluation`，HEAD 为 `f9817817a602caf24ad95e500fe08e44224ffc2d`，检查开始时工作树干净。V1 tag 之后的两个提交只修改了 README、治理、复盘和学习文档。V1 产品实现及历史规格 / 任务文件与 tag 中的版本一致。这是 Bootstrap 时的状态快照，不代表未来所有 HEAD 的状态。

## 开发顺序

当前 V1 Retrieval → 评估数据集 → Evaluation Runner → V1 Baseline Benchmark → 此后才可开展检索实验（Experiment）。

**T2001 — 定义检索评估数据集契约** 已完成契约定义、Pilot 验证及 Human Final Gate，状态 DONE。该完成不自动授权 T2002，也不表示已构建正式 Benchmark Dataset；T2003 前必须有真实版本化、Human-reviewed evaluation dataset。后续的融合、重排序（Reranking）和查询理解属于研究方向，并非已采用的架构。

## 文档命名空间

- [evaluation/](evaluation/README.md)：数据集契约与评估协议。
- [benchmarks/](benchmarks/README.md)：可复现的运行证据与分析。
- [adr/](adr/README.md)：关联证据的架构决策。

这些目录说明用于明确资料存放规则，不是占位数据集或实验结果。

## 历史与工作流保留

保持 [V1 Gate 闭环记录](../verification/PHASE-12-GATE-CLOSURE.md)、[V1 复盘](../DX-RAG-V1-DEVELOPMENT-RETROSPECTIVE.md)、既有验证及学习记录不变。V1 验收证据不等于检索质量 Benchmark。

保留 [Learning & Engineering Workflow V2](../learning/templates/phase-learning-pass-workflow.md)：Task DONE → Task Learning Pass → Phase Gate → Phase Learning Review → Engineering Review → 独立 Interview synthesis。其中的 “V2” 指工作流版本，不代表产品 V2 已实现。历史文档无需迁移到新模板。
