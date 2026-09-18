# DX-RAG V2 任务计划

> 状态：T2001 DONE；T2002 DONE；T2003 DONE（2026-09-14，AC-2003-1～4 PASS，执行授权见 SPEC §1.10）。Phase 20 独立 Gate 已于 2026-09-18 PASS（[正式报告](../verification/PHASE-20-GATE-REVIEW.md)）；Phase 21 未启动。
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

**状态：** DONE
**类型：** Evaluation Task  
**依赖：** T2001 DONE，且数据集 / 指标契约已经审阅。  
**SPEC 引用：** `docs/v2/SPEC.md` 第 4 节（EVAL-01、EVAL-02）、第 6 节（SAFE-01）。

**目标：** 围绕保持不变的 V1 Retrieval，实现可复现的测量。

**范围 / 预期位置：** 评估工具位置在 Task 计划中确定，协议存放于 `docs/v2/evaluation/`。遵循获批契约，计算指标，提供可重复执行的调用方式，并持久化逐查询 / 聚合输出及来源信息。

**执行计划（2026-09-10）：** `backend/evaluation/` 放独立 validator、metrics、Runner/CLI 与 V1 adapter；`backend/tests/test_evaluation.py` 和明确标注的 synthetic fixtures 验证手算值、fail-fast、跨进程重复性及 V1 调用边界；协议/AC 证据存于 `docs/v2/evaluation/t2002-runner.md`，完成后追加 Phase 20 Task Learning Pass。无新增依赖，无生产代码改动。

**验收 / 验证：**

- AC-2002-1：使用可手算且明确标注的 test fixtures，验证指标计算及契约边界情况。
- AC-2002-2：无效输入必须明确报错；输出标明数据集、配置、Runner 版本及测量范围。
- AC-2002-3：在声明的条件下检查可重复性；报告波动，不得隐瞒。
- AC-2002-4：相关回归检查确认检索 / 产品行为未改变；执行说明能够支持复现。

**完成证据（2026-09-11）：** [Runner 0.1.0 协议与 AC ledger](evaluation/t2002-runner.md)。AC-2002-1～4 PASS；评估测试 8/8、V1 QA 回归 50/50、Query API 回归 10/10。三进程合成 fixture 输出稳定；实际 V1 Keyword/Hybrid + 替代 store/vector 的同分样例观察到跨 hash seed 排名/指标波动，按原序保留并报告。产品源码与 V1 tag 无差异。无真实 Benchmark、模型/索引测量或质量提升声明；T2003 仍需真实已审阅版本化数据及单独授权。Task Learning Pass 已追加至 [Phase 20 素材](../learning/phase-20-evaluation-foundation.md)，其独立 reader test 为 PENDING，不替代或改变 Task AC 结论。

**范围外：** 检索优化、生产策略变更，以及根据 test fixtures 宣称有代表性的质量结论。

### T2003 — 采集 V1 Retrieval Baseline

**状态：** DONE
**类型：** Evaluation Task  
**依赖：** T2002 DONE；版本化数据集已可用，并按 T2001 契约完成审阅；所需模型 / 索引 / 环境可用。  
**SPEC 引用：** `docs/v2/SPEC.md` 第 4 节（EVAL-03）、第 5 节（EXP-01）、第 6 节（SAFE-01）。

**目标：** 在检索 Experiment 前，建立真实的 V1 Benchmark 证据。

**执行计划（2026-09-14）：** 按 SPEC §1.10 授权，在 `docs/v2/benchmarks/t2003-v1-baseline-1.0/` 保存采集脚本、运行前后身份/完整逻辑快照核对、Runner 原始报告、验证与分析。使用现有深度 10 协议、独立进程 seeds 1/2/3；重跑评估工具及相关 QA/query 回归，核对 AC-2003-1～4，随后记录 Task Learning Pass。产品、Runner、冻结数据及指标定义保持不变。

**范围 / 预期位置：** 针对已发布的 V1 行为运行经过验证的评估，将证据 / 分析存放于 `docs/v2/benchmarks/`。检查实际测量的 checkout 与 tag 的差异，不改变 Git 历史。

**验收 / 验证：**

- AC-2003-1：记录准确的 V1 参考版本、实际测量的实现 / 工具版本、数据集 / 语料 / 索引 / 模型 / 配置及命令。
- AC-2003-2：保留真实的逐查询及聚合 Recall@K、MRR 和 nDCG@K 结果，并附失败情况、局限和证据类型；不得伪造结果。
- AC-2003-3：依据声明的容差 / 条件检查复现情况；测量 latency / cost 时说明方法，否则明确标为未测量。
- AC-2003-4：Baseline 仍可复现，已验证检索行为未改变，比较局限明确。缺少前置证据时，不得完成本 Task。

**范围外：** 任何 Candidate 检索策略、效果提升声明，以及生成质量评估。

**完成证据（2026-09-14）：** [完整 V1 Hybrid Baseline](benchmarks/t2003-v1-baseline-1.0/README.md)。一次 Runner、seeds 1/2/3 独立进程、每轮全部 40 题，真实本地 BGE/Chroma、无 mock/LLM。Dev/Test 各纳入 16A、排除 4U；Recall@5 分别 0.9125 / 0.90625。5 题排名变化、6 题分数映射变化、Q014 一题指标变化；Test nDCG@5 为 0.894758～0.896220，不跨轮平均。Q013 正证据位于 rank 9，8U 全有主题邻近返回；无生成质量结论。前后完整公开逻辑 inventory、模型/release/产品/Runner hash 一致；持久化字节有变化、原因未定，不声明向量逐位审计。8+50+10 项回归、pip check 和离线 1,152 个逐题指标值复算通过；AC-2003-1～4 PASS。产品与 V1 tag 无差异；latency/cost 未测量。Task Learning Pass 归入 Phase 20 素材；下一步为独立 Phase 20 Gate，未自动启动。

### T2003 前数据构建检查点 — 历史记录

以下按各次事件保留当时 TODO/PENDING/未授权状态；最新执行与完成结论见上面的 T2003 条目及 SPEC §1.10。

**授权：** 2026-09-11 用户要求准备正式 Benchmark 数据集构建工作，先生成候选数据与人工审阅材料；见 SPEC §1.4。本检查点沿用 Contract §14，不新增 Task，不将 T2003 改为 IN_PROGRESS。

**当前状态：** 候选材料已交付，等待 Human Review（2026-09-11）。[候选审阅包 0.1](evaluation/archives/README.md#benchmark-candidate-0.1) 包含 32 Answerable +8 Unanswerable、绑定冻结 38 chunks 的 1,520 行建议、4 批人工审阅材料、完整正文、family/split 建议和待填决定表；结构/hash/派生文档核验通过，见 [verification](evaluation/archives/README.md#benchmark-candidate-0.1)。全部新 Human query/grade/coverage 为 PENDING。保守分组产生 30 题大组，拟议 Dev 27A+4U / Test 5A+4U，Test 缺可回答 Paraphrase/Multi-chunk；规模、家族和代表性缺口必须审阅。候选材料交付不满足 versioned dataset readiness；正式 corpus 选择、措辞/类别/可回答性、coverage、等级、split、质量目标缺口和 promotion 均需 Human 确认。

**后续 Human Review 进度（2026-09-11）：** [人工决定表](evaluation/archives/README.md#benchmark-candidate-0.1) 已记录第一轮 40/40 通过，32 Answerable /8 Unanswerable，7 题改写；此前“全部新 Human query 为 PENDING”为候选生成时的历史状态。全部等级、完整 coverage、family/split、最终去重及 promotion 仍待审。已准备 [第二轮 Q001–Q004 完整矩阵](evaluation/archives/README.md#benchmark-candidate-0.1)，不启动 T2003。

**后续等级审阅完成（2026-09-11）：** Q001～Q040 的 1,520 项显式 Human grades 已批准，包含 19 项相对原候选的调整；32 Answerable /8 Unanswerable 与人工证据一致。见 [人工标注汇总及核验入口](evaluation/archives/README.md#benchmark-candidate-0.1)。全部 40 题 Human coverage 仍明确 PENDING；family/split、去重、语料/质量目标差额及最终 promotion 未批准，正式数据集未冻结，T2003 不启动。

**后续完整覆盖通过（2026-09-11）：** Human 对 Q001–Q040 的完整冻结 38 块审阅确认「确认」，已记录 40/40 coverage APPROVED、无遗漏正证据；等级不变，见 [标注汇总 0.2](evaluation/archives/README.md#benchmark-candidate-0.1)。[分组重算分析](evaluation/archives/README.md#benchmark-candidate-0.1)为 9 个保守连通组、最大组 25 题，非最终 family/split。去重、核心事实分组、Dev/Test、最终语料复用/规模差额及 promotion 仍待决定；T2003 仍 TODO。

**核心事实划分草案交付（2026-09-14）：** 按 SPEC §1.5 授权完成 [fact-split-draft-0.1](evaluation/archives/README.md#fact-split-draft-0.1)：48 个政策事实单元、40 题逐题证据归因、20 个 family（最大 8 题），建议 Dev/Test 各 16A+4U。核心/前提事实在本次映射下不跨侧；仍共享 7 个正证据块及 2 条仅补充规则，Pilot 原文暴露与语义边界见 [重叠审阅](evaluation/archives/README.md#fact-split-draft-0.1)。来源/hash/逐字引用/全题归属与原标签一致性核验通过；事实边界、family/split、语义去重、规模差额及 promotion 均待 Human 决定。保留全部已批准问法、1,520 项等级及 coverage；未扩充语料，未运行 Retrieval/Benchmark，T2003 仍 TODO。

**分组与划分 Human 批准（2026-09-14）：** `H-BC01-FACT-SPLIT-2026-09-14`，见 [批准记录](evaluation/archives/README.md#fact-split-draft-0.1)。核心事实、20 个分组及 Dev/Test 各 16A+4U 获批；7 个共享正证据块、2 条跨侧补充规则及非盲测局限已接受。语义去重、规模差额、最终语料、正式冻结及 promotion 仍 PENDING；不扩充语料、不运行 Benchmark，T2003 仍 TODO。

**语义去重审阅启动（2026-09-14）：** Human 要求「开始语义去重审阅」。已准备 [相近题组对照](evaluation/archives/README.md#semantic-dedup-review-0.1)：40 题覆盖 20 个对照/筛查组，先审 SD01–SD03；全部去重决定 PENDING，不改问法、标签、已批分组或划分。规模差额、最终语料和冻结仍待定，不运行 Benchmark。

**语义去重第一批通过（2026-09-14）：** `H-BC01-DEDUP-SD01-SD03-2026-09-14`，Human 批准 SD01–SD03 全部保留；3/20 对照组通过，SD04–SD20 仍 PENDING，下一批 SD04–SD06。见 [人工决定](evaluation/archives/README.md#semantic-dedup-review-0.1)。不将指定对照组批准扩大为全部题目去重通过；规模差额、最终语料和冻结继续待定，不运行 Benchmark。

**语义去重第二批通过（2026-09-14）：** `H-BC01-DEDUP-SD04-SD06-2026-09-14`，Human 批准 SD04–SD06 全部保留；累计 6/20 对照组通过，SD07–SD20 仍 PENDING，下一批 SD07–SD09。见 [人工决定](evaluation/archives/README.md#semantic-dedup-review-0.1)。规模差额、最终语料和冻结继续待定，不修改题目或已批标签，不运行 Benchmark。

**语义去重第三批通过（2026-09-14）：** `H-BC01-DEDUP-SD07-SD09-2026-09-14`，Human 批准 SD07–SD09 全部保留；累计 9/20 对照组通过，SD10–SD20 仍 PENDING，下一批 SD10–SD12。见 [人工决定](evaluation/archives/README.md#semantic-dedup-review-0.1)。规模差额、最终语料和冻结继续待定，不修改题目或已批标签，不运行 Benchmark。

**语义去重第四批通过（2026-09-14）：** `H-BC01-DEDUP-SD10-SD12-2026-09-14`，Human 批准 SD10–SD12 全部保留；累计 12/20 对照组通过，SD13–SD20 仍 PENDING，下一批 SD13–SD15。见 [人工决定](evaluation/archives/README.md#semantic-dedup-review-0.1)。规模差额、最终语料和冻结继续待定，不修改题目或已批标签，不运行 Benchmark。

**语义去重第五批通过（2026-09-14）：** `H-BC01-DEDUP-SD13-SD15-2026-09-14`，Human 批准 SD13–SD15 全部保留；累计 15/20 对照组通过，SD16–SD20 仍 PENDING，下一批 SD16–SD18。见 [人工决定](evaluation/archives/README.md#semantic-dedup-review-0.1)。规模差额、最终语料和冻结继续待定，不修改题目或已批标签，不运行 Benchmark。

**语义去重第六批通过（2026-09-14）：** `H-BC01-DEDUP-SD16-SD18-2026-09-14`，Human 批准 SD16–SD18 全部保留；累计 18/20 对照组通过，SD19–SD20 仍 PENDING，下一批为最后两组。见 [人工决定](evaluation/archives/README.md#semantic-dedup-review-0.1)。规模差额、最终语料和冻结继续待定，不修改题目或已批标签，不运行 Benchmark。

**本轮语义去重完成（2026-09-14）：** `H-BC01-DEDUP-SD19-SD20-2026-09-14`，Human 批准 SD19–SD20 全部保留；累计 20/20 对照/筛查组通过，当前 40 题全部保留，无删除/合并/改写，Dev/Test 仍各 16A+4U。见 [人工决定](evaluation/archives/README.md#semantic-dedup-review-0.1)。结论限于当前候选题集，不自动覆盖未来并入 Pilot 的题集；规模差额、最终语料和正式冻结/promotion 仍待定，不运行 Benchmark，T2003 仍 TODO。

**规模与语料审阅材料就绪（2026-09-14）：** Human 要求「审阅规模差额和最终语料选择」。已准备 [SC01 / SC02 审阅材料](evaluation/archives/README.md#size-corpus-review-0.1)：建议接受 32A+8U 及类别缺口，选择原四份政策/冻结 38 块，题集仅当前 40 题、不并入六道 Pilot 题。四份原文 hash 与快照一致，规模按已批 split 重算；合成来源、小样本、弱相关不可回答题、非盲测局限均披露。两项 Human 决定 PENDING，正式冻结/promotion 仍待定；不扩充语料、不运行 Benchmark，T2003 仍 TODO。

**规模与最终语料 Human 批准（2026-09-14）：** `H-BC01-SIZE-CORPUS-SC01-SC02-2026-09-14`，见 [批准记录](evaluation/archives/README.md#size-corpus-review-0.1)。SC01/SC02 通过：接受 32A+8U、各 split 类别缺口及已披露局限；选择原四份文档和冻结 38 块作为本次语料，题集仅 BC01-Q001–Q040，不并入六道 Pilot 题。来源 hash 与范围核验通过；正式版本冻结及 promotion 仍 PENDING，不运行 Benchmark，T2003 仍 TODO。

**正式版本冻结审阅包交付（2026-09-14）：** 按 Human「准备正式版本冻结审阅包」及 SPEC §1.6，交付 [1.0.0-rc1 审阅包](evaluation/archives/README.md#freeze-review-1.0.0-rc1)：候选 dataset.json、原文/快照/批准证据副本、文件 hash manifest 与 verification.json。40 题/1,520 项等级及上游来源映射核验 PASS；现有纯数据校验器按预期拒绝 dataset promotion PENDING，未伪造最终批准。正式版本冻结/promotion 仍 PENDING；未运行 Retrieval/Benchmark，未检查实时模型/索引，T2003 仍 TODO。

**正式数据集 1.0.0 冻结完成（2026-09-14）：** 按 SPEC §1.7 与 `H-BC01-FREEZE-PROMOTION-1.0.0-2026-09-14`，已生成 [novatech-retrieval-benchmark-1.0.0](evaluation/novatech-retrieval-benchmark-1.0.0/README.md)，状态 FROZEN、promotion APPROVED。发布文件 hash、RC 内容一致性和完整现有数据 validator 均 PASS；仅更新版本/最终批准元数据。40 题、1,520 项等级、38 块、20 family 和 Dev/Test 各 16A+4U 不变；正式发布文件仍为工作区产物，未冒充已提交版本。未运行检索或 Benchmark，实时模型/索引就绪未检查，T2003 仍 TODO 且未获执行授权。

**T2003 前预检完成（2026-09-14）：** 按 SPEC §1.8 完成 [环境与索引就绪报告](evaluation/t2003-preflight-0.1/README.md)。冻结数据 validator、依赖/配置、29 项模型文件 hash、离线模型加载（CPU/512维）、实际 4 文件/38 块 ID/文本/映射及 V1/工具身份均 PASS。公开读取期间 Chroma 持久化文件 hash 有变化，原因未定；不声称向量逐位一致或搜索已验证。首次脚本计数方法名错误及修正复核均保留。未执行 encode/检索/Benchmark，T2003 仍 TODO 且未获执行授权。

**最小向量检索冒烟完成（2026-09-14）：** 按 SPEC §1.9 完成 [冒烟检查](evaluation/t2003-smoke-0.1/README.md)，PASS。使用一条非 Benchmark 中性文本，1 次 encode 输出有效归一化 512 维向量，1 次公开 VectorStore.search(top_k=1) 成功返回冻结 ID/正文；前后 38 块完整公开逻辑数据一致，模型文件/正式数据集不变。持久化文件仍有字节变化，原因未确定，不等同于完整向量逐位审计。未运行 Hybrid/完整 Benchmark 或指标，T2003 仍 TODO 且需独立执行授权。

**历史材料归档（2026-09-14）：** 按 Human「按照你的推荐做法执行」，五个历史审阅目录 74 个文件已 ZIP 归档并逐项核对 SHA-256/CRC。永久删除被自动审批策略拒绝，改为可恢复移动至 Git 忽略的 tmp/benchmark-review-backup-2026-09-14/；散落目录已移出 evaluation，未宣称永久删除或释放本地备份空间。见 [归档入口](evaluation/archives/README.md)。正式数据集、工具/测试及预检/冒烟证据未改，未运行 Benchmark。

### Phase 20 出口门禁

**当前 Gate（2026-09-18）：PHASE_20_PASS — READY_FOR_PHASE_21。** [独立报告](../verification/PHASE-20-GATE-REVIEW.md)核对 11 项 AC 均 PASS，无 BLOCKER/MAJOR/MINOR，4 项 INFO；本轮 67 项测试与离线证据验证，不包含新 live Benchmark 或写文件 CLI 测试。历史真实三轮、波动、持久化边界及未测量项完整保留。[Phase Learning Review](../learning/phase-20-evaluation-foundation.md)已按概念整合，读者/文档检查见其附录 C；原 Task 素材已保留。Engineering Review 和 Interview synthesis 尚未执行。Task 状态保持 DONE，路线图不变；Phase 21 仍需单独协议、Task 批准与执行授权，未启动。

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
