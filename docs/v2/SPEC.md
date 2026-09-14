# DX-RAG V2 规格 — 评估驱动的 RAG 优化（Evaluation-Driven RAG Optimization）

> 版本：V2 Bootstrap 规格，2026-09-09；Phase 20 范围批准记录见第 1.1 节。
> 状态：**Phase 20 Evaluation Foundation 当前范围已获批；其余未来 V2 范围仍为 DRAFT，未自动冻结或批准。**
> 执行授权：T2001 已 DONE；2026-09-10 用户明确授权实现 T2002（见第 1.3 节）；T2003、检索 Experiment 和生产行为变更未获授权。

## 1. 权威层级与生命周期

当前 V2 权威层级：`docs/v2/SPEC.md` > `docs/v2/TASKS.md` > `CLAUDE.md`。

`docs/SPEC.md` v1.7 FROZEN 和 `docs/TASKS.md` 继续作为 V1 历史契约与任务记录，以 `v1.0.0`（`da8be59a60d7f35a2e3c1ab835624946c53d2a55`）为锚点。现有行为与契约继续沿用，直到明确获批的 V2 修订及对应 Task 授权变更。历史文档中关于唯一权威入口的声明适用于 V1。

生命周期：草案 → 人工审阅（Human Review）→ 冻结 / 批准（Freeze / Approve）→ 执行 Task → Test / Benchmark → 证据 → ADR / 人工决策（Human Decision）→ 必要时显式修订 SPEC。

执行 Task 前，必须在本文记录人工批准的日期、获批版本 / 范围及决策引用。实现 Agent 不得为了适应意外结果而擅自修改需求、指标定义或 Acceptance Criteria。发现冲突时，必须报告并阻塞受影响的工作。

### 1.1 Phase 20 人工批准记录

- 决策引用：`H20-APPROVAL-2026-09-09`，来源为项目负责人本次明确授权指令（Human decision），不是新建的架构 ADR。
- 批准日期：2026-09-09。
- 获批版本 / 范围：本次更新前的 2026-09-09 V2 Bootstrap 规格中，Phase 20 Evaluation Foundation 当前范围（第 4 节 EVAL-01–03 及适用的顺序、安全和验收约束）。
- 人工决定原文：

> 批准 DX-RAG V2 Phase 20 Evaluation Foundation 的当前 SPEC 范围，允许正式开始 T2001；这不代表 T2001 已完成，也不批准任何 Retrieval Candidate 或生产行为变更。

范围批准与任务执行授权分别记录：本次只授权 T2001 开始及已审阅 Dataset Contract 的文档落盘。T2002/T2003 仍需后续明确执行授权及满足依赖；不得推断本次批准了 Runner、Benchmark 执行、Pilot 语料创建、RRF、BM25、Reranker、Query Rewrite 或生产集成。

本次指令明确给出的 Dataset Contract 设计决定记录于 [T2001 Retrieval Evaluation Dataset Contract](evaluation/retrieval-evaluation-dataset-contract.md)。该文档细化 EVAL-01 / EVAL-02，不高于本文或 `docs/v2/TASKS.md`；初始批准时 Pilot 验证及最终人工审阅尚未完成，后续完成记录见下文。后续 SPEC 变更必须显式审阅批准，不得因实验结果自动改写需求。

### 1.2 T2001 Final Human Gate（2026-09-10）

Human project owner 明确批准 T2001 IN_PROGRESS → DONE、Dataset Contract 0.3 FROZEN、T2001 Final Human Gate PASS。AC-2001-1/2/3 均 SATISFIED，Pilot coverage 6/6 APPROVED、全部 readiness READY、无剩余契约/Pilot blocker；完整决定与冻结边界见 [Dataset Contract 第 16 节](evaluation/retrieval-evaluation-dataset-contract.md)。不虚构 reviewer 姓名；此批准仅适用于 T2001，不授权 T2002/T2003，也不等于 Phase 20 Gate PASS 或正式 Benchmark Dataset 已存在。

### 1.3 T2002 执行授权（2026-09-10）

决策来源：Human project owner 本次指令 `implement T2002`。依赖 T2001 DONE、Contract 0.3 FROZEN 已满足；授权实现并验证 T2002 指标、输入校验、Runner、合成 test fixtures 和 repeatability check，记录执行协议及 Task Learning Pass。沿用已批准的 EVAL-01/02、SAFE-01 和冻结 Contract 0.3，不变更指标定义。此授权不包含 T2003 正式 Benchmark、正式数据集构建或生产策略变更。此前“不授权 T2002”的段落保留为各次历史批准的边界。

### 1.4 Benchmark 候选数据与人工审阅材料授权（2026-09-11）

决策来源：Human project owner 指令「准备正式 Benchmark 数据集构建工作，先生成候选数据与人工审阅材料。」授权按冻结 Contract 0.3 准备候选 queries、LLM 建议标注、完整快照 screening、拟议 evidence-family / Dev-Test 划分及人工审阅材料。作为第 7 节及 Contract 第 14 节的 T2003 前数据构建检查点执行，不新增 Task ID，不启动 T2003。以现有冻结 Pilot corpus/snapshot 准备首批材料；复用建议不等于批准其为最终 Benchmark corpus。Human 最终等级、coverage confirmation、split 和 dataset promotion 仍待实际人工决定。本次不运行 Retrieval / Benchmark、不更改产品或冻结指标定义；此前未授权数据构建的文字保留各次历史授权边界。产物及待决事项见 [候选审阅包 0.1](evaluation/archives/README.md#benchmark-candidate-0.1)。

### 1.5 核心事实分组与 Dev/Test 草案授权（2026-09-11）

Human project owner 指令：「按核心政策事实细化分组，准备 Dev/Test 划分草案；先不扩充语料、不运行 Benchmark。」本轮沿用第 1.4 节的 T2003 前数据构建检查点，以已批准的 40 题问法、1,520 项等级及 full-snapshot coverage 为输入，准备核心事实映射、evidence-family / split 草案、Pilot 暴露及重叠检查；不改变人工标签，不新增语料或快照，不执行 Retrieval/Benchmark，不自动批准分组、去重或最终数据集。草案路径为 `docs/v2/evaluation/fact-split-draft-0.1/`。

### 1.6 正式版本冻结审阅包准备（2026-09-14）

Human project owner 指令：「准备正式版本冻结审阅包」。在已获批问法、等级、coverage、核心事实/划分、SD01–SD20 去重及 SC01/SC02 规模与最终语料选择的范围内，准备版本候选文件、来源/批准记录清单和本地校验结果。交付路径为 `docs/v2/evaluation/freeze-review-1.0.0-rc1/`。只授权审阅材料准备；正式冻结、dataset promotion 仍需真实最终决定，不授权 T2003、Retrieval/Benchmark、重建快照或生产变更。

### 1.7 正式数据集 1.0.0 冻结与 promotion 批准（2026-09-14）

Human project owner 原文：「认可 freeze-review-1.0.0-rc1 审阅包及其 manifest 绑定的内容，批准生成并冻结正式数据集 novatech-retrieval-benchmark-1.0.0，批准 dataset promotion；沿用已批准范围和局限，不运行 Benchmark。」决定引用 `H-BC01-FREEZE-PROMOTION-1.0.0-2026-09-14`。已核对获批 RC manifest 与文件 hash，正式版本仅更新发布身份和最终批准元数据，内容沿用已批 40 题、1,520 项等级、20 个 family、四份原文/38 块及 Dev/Test 各 16A+4U；不含六道 Pilot 题。发布文件、来源 hash 和实际批准原文见 [正式版本](evaluation/novatech-retrieval-benchmark-1.0.0/README.md)。本次批准正式冻结及 dataset promotion，不授权 Benchmark 或 T2003；模型/索引/存储实时就绪另行核对。原审阅包及此前 pending 记录保留历史状态。

### 1.8 T2003 前环境与索引就绪检查（2026-09-14）

Human project owner 要求「T2003 前的环境与索引就绪检查」。授权读取当前有效非敏感配置、核查依赖和模型文件身份、离线加载本地模型、通过现有 VectorStore 公开读取接口核对冻结 collection 的 chunk 身份/文本/文件映射，以及校验 V1/工具版本。报告在 `docs/v2/evaluation/t2003-preflight-0.1/`。此项是 T2003 前检查，不执行查询、embedding encode、检索/指标或 Benchmark，不创建/重建 collection，不改变产品或冻结数据集，不构成 T2003 执行授权。

### 1.9 最小 embedding / 向量检索冒烟授权（2026-09-14）

Human project owner 原文：「授权最小 embedding 与向量检索冒烟检查，使用非 Benchmark 查询；不修改语料、不重建索引、不运行完整 Benchmark。」仅使用一条中性、非 BC01/Pilot 查询，经现有 embedding 接口产生一次向量，再通过 VectorStore 公开 search 接口进行一次 top_k=1 搜索，核对向量有效性、返回身份和检查前后逻辑数据一致性；记录持久化文件变化。证据位于 `docs/v2/evaluation/t2003-smoke-0.1/`。该授权不包含 Hybrid baseline、指标计算、重建索引或完整 T2003 Benchmark；正式数据集内容不变。

## 2. 目标与范围

- 在改变检索行为前，建立可复现的检索评估（Retrieval Evaluation）和可量化的 V1 Baseline。
- 开展受控检索实验，以证据支持架构决策。
- 将检索质量评估与生成质量评估作为不同职责。
- 保障回归安全，并在适用时关注延迟（latency）与成本（cost）。

Bootstrap 仅建立治理。Phase 20 必须先建立评估，再允许任何检索行为变更。当前未强制采用或批准采用 RRF、BM25、Reranker 或 Query Rewrite。Candidate 选择、集成及后续功能均需要明确获批的范围和 Task；路线图标题不构成执行授权。

V1 范围外的功能继续排除，除非被明确引入。本次 Bootstrap 不改变权重、阈值、Top-K、chunk / overlap、模型 / provider、embedding、向量存储、OCR、API 或前端行为，也不引入 Agents / Multi-Agent 系统、MCP 或无关基础设施。

## 3. 评估术语

| 术语 | 含义 |
|---|---|
| Baseline | 身份明确的参考实现 / 配置，使用版本化数据集进行评估；初始参考为已发布的 V1 Retrieval |
| Research Question | 希望通过比较回答的具体研究问题 |
| Candidate | 待评估的替代方案，不会自动成为生产行为 |
| Dataset | 版本化的语料、查询及相关性判断，包含来源、覆盖范围和明确的局限 |
| Metrics | 约定的指标定义、聚合方式及边界情况处理规则 |
| Experiment | 固定输入、声明变更变量，并遵循可复现协议的受控比较 |
| Result | 实际观测到的测量值、错误和局限，包括负向或无法得出结论的结果 |
| Decision | 基于证据作出的接受、拒绝、暂缓或继续调查结论，包含权衡与授权 |

失败的 Experiment 也是有效结果。成功意味着忠实执行获批协议并保留可解释的证据，不意味着 Candidate 必须优于 Baseline。

## 4. 评估基础要求

**EVAL-01 — 数据集契约。** 实现 Runner 前，定义可追溯的语料 / 查询标识、相关性判断、来源 / 版本、可回答与不可回答问题的覆盖、标注 / 审阅流程、数据划分 / 泄漏控制及局限。具体 schema、相关性粒度、采样方式和指标边界情况由 T2001 确定；不得在 Bootstrap 中伪造 Benchmark 数据。

**EVAL-02 — Metrics 与 Runner。** 为 Recall@K、MRR 和 nDCG@K 建立评估能力。指标定义必须明确相关性映射、K / 截断约定、聚合方式、并列分数 / 重复项、缺失标注，以及无相关项 / 无返回结果的处理。使用明确标注的测试样例（test fixtures）验证指标计算；这些样例不构成有代表性的 Benchmark。保留逐查询及聚合输出，并记录可复现的调用方式和环境元数据。具体工具由后续 Task 决定。

**EVAL-03 — V1 Baseline。** 任何检索 Experiment 开始前，必须使用经过审阅的数据集和经过验证的 Runner，采集已发布 V1 Retrieval 的 Baseline。保留 `keyword_score * 0.3 + vector_score * 0.7`、`MIN_RELEVANCE_SCORE = 0.30`、Retrieve → Merge → Calculate final_score → Sort DESC → Relevance Filter → Top-K，以及现有配置 / pipeline。记录 tag / commit、实际测量的 checkout 和评估工具版本，并解释差异。不得为测量 Baseline 而 reset 工作区或移动 tag。

Baseline 记录必须明确语料 / 数据集版本、稳定的标识映射或可复现的重建方式、索引 / 模型 / 配置、完整命令、环境、指标定义、逐查询及聚合结果、失败情况和证据边界。测量 latency / cost 时必须记录测量条件，否则明确标为未测量。仅有历史 V1 验收测试不能满足此要求。

## 5. 受控实验与决策

**EXP-01。** 必须先完成 T2001 → T2002 → T2003 及 Phase 20 Gate，再开展检索 Experiment。首次运行后仍需保留可复现的 V1 参考，以支持后续比较。

每个拟开展的 Experiment 都要在执行前说明 Research Question、Baseline、Candidate、Dataset、Metrics、变更变量、控制条件、比较协议、回归检查及决策标准。在匹配的条件下比较，并披露混杂因素、波动及不足以支持决策的证据。不得在未声明数据污染、未显式修订评估计划的情况下，使用留出的评估数据调参。

**EXP-02。** Research Question → Baseline → Candidate → Controlled Experiment → Benchmark → 分析 → ADR / Decision → 生产集成。架构决策存放于 `docs/v2/adr/`，包含背景（Context）、决策（Decision）、替代方案（Alternatives）、证据（Evidence）、权衡（Trade-offs）和后果（Consequences）。生产集成必须具备已记录的人工决策，以及明确授权的实现 Task。仅有实验代码不会改变默认策略。

## 6. 生成质量与运行安全

**GEN-01。** 分别为忠实度（Faithfulness）、回答正确性（Answer correctness）、引用正确性（Citation correctness）及可回答性 / 拒答（Answerability / refusal）准备评估。后续获批的 Phase 24 协议必须定义评分准则、ground truth、评判器 / 人工审阅边界、版本管理和不确定性。检索质量不能代替回答质量；V1 返回的检索来源本身不能证明逐句引用正确。Bootstrap 和 Phase 20 均不实现生成质量评估器。

**SAFE-01。** 除非显式修订，否则必须保护现有 API、摄入、存储、安全及前端契约。未来发生实现变更时，运行相关回归检查。记录 latency 和 cost，并在适用时包含外部服务 / 模型条件；不得虚构 SLA、预算阈值或改善幅度。未测量的维度必须明确说明。

## 7. 验收与待决事项

Phase 20 的验收内容为：可追溯的数据集契约、经过验证的 Runner、可复现的 V1 证据，以及独立 Gate 评估；不设置效果提升目标。具体 AC 归属见 `docs/v2/TASKS.md`。未来 Phase 的验收要求必须在执行前定义并获批。

Phase 20 范围已按第 1.1 节获批；T2001 已按第 1.2 节 Human Final Gate 完成，Dataset Contract 0.3 FROZEN。后续正式数据构建仍按契约的质量目标、覆盖审阅与 Dev/Test evidence-family 隔离规则单独授权；T2003 前必须存在真实版本化、Human-reviewed evaluation dataset。未来 Candidate 选择、生成质量评分准则、集成权衡及运行预算未获自动批准。本文未声明任何数值化 Benchmark 结果或改善幅度。
