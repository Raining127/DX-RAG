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

V2 SPEC 的 **Phase 20 Evaluation Foundation 当前范围已获人工批准**；其余未来 V2 范围仍为 DRAFT。T2001 DONE、[Dataset Contract 0.3](evaluation/retrieval-evaluation-dataset-contract.md) FROZEN；T2002 DONE，交付 [Runner 0.1.0](evaluation/t2002-runner.md)。T2003 按 [SPEC §1.10](SPEC.md) 获授权，2026-09-14 DONE，交付 [完整 V1 Hybrid Baseline](benchmarks/t2003-v1-baseline-1.0/README.md)：三轮各 40 题、AC-2003-1～4 PASS。5 题排名变化、1 题指标变化已保留；公开逻辑数据一致，未证明向量逐位完整性。**2026-09-18 独立 [Phase 20 Gate](../verification/PHASE-20-GATE-REVIEW.md)：PHASE_20_PASS — READY_FOR_PHASE_21；未启动 Phase 21。** Gate 仅建立 readiness，不批准 Candidate；协议、Task 和执行授权仍须单独明确。

2026-09-09 的 Bootstrap 检查以本地 Git 为依据：分支为 `v2/evaluation`，HEAD 为 `f9817817a602caf24ad95e500fe08e44224ffc2d`，检查开始时工作树干净。V1 tag 之后的两个提交只修改了 README、治理、复盘和学习文档。V1 产品实现及历史规格 / 任务文件与 tag 中的版本一致。这是 Bootstrap 时的状态快照，不代表未来所有 HEAD 的状态。

**历史候选阶段（2026-09-11，以下为当时状态）：** 按 [SPEC §1.4](SPEC.md) 的后续用户授权，已准备 [Benchmark 候选审阅包 0.1](evaluation/archives/README.md#benchmark-candidate-0.1)：40 道候选题、1,520 行 LLM 建议和 4 批人工审阅材料。全部新 Human decisions 为 PENDING；保守 family 划分存在明显 Test 规模/类别缺口，正式数据尚未冻结，T2003 未启动。

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

**当前入口（2026-09-18）：** [正式数据集 1.0.0](evaluation/novatech-retrieval-benchmark-1.0.0/README.md)保持冻结；[历史审阅材料](evaluation/archives/README.md)已归档；[T2003 基线与验收证据](benchmarks/t2003-v1-baseline-1.0/README.md)已完成。[Gate 报告](../verification/PHASE-20-GATE-REVIEW.md)已保存；[Phase Learning Review](../learning/phase-20-evaluation-foundation.md)已整合，读者/验证状态见附录 C。后续独立 [Engineering Review](../learning/engineering-review/phase-20-engineering-review.md)已形成，读者/文档检查见其附录 D；Interview synthesis 尚未执行。保留全部验证边界，不自动启动后续工作。
