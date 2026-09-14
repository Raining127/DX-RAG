# T2001 — Retrieval Evaluation Dataset Contract

> 文档版本：0.3，2026-09-10；由 0.2（Closing Decisions）演进，本版记录 Human 确认的 metric/execution protocol。
> Status：**FROZEN**；Version：**0.3**；Freeze date：**2026-09-10**；Approval authority：**Human project owner**；T2001 Final Human Gate：**PASS**；T2001：**DONE**。
> 决策来源：`H20-APPROVAL-2026-09-09` 及同次指令的 Dataset Contract 设计决定，见 [docs/v2/SPEC.md 第 1.1 节](../SPEC.md)。
> 0.1 的初始授权只记录设计；后续 Pilot 入库与 Reviewed 0.2 标签已单独获授权并留证。0.2 记录 CD-1～CD-4；本次单独授权为记录 metric/execution protocol 和准备 Human coverage review packet，不生成数据集、运行结果或架构 ADR。Closing Decisions 来源为本轮 Human project owner 指令，记录日期 2026-09-10，不虚构 reviewer 姓名。

## 1. 权威与执行边界

本文细化 [docs/v2/SPEC.md](../SPEC.md) 的 EVAL-01 / EVAL-02，服从 `docs/v2/SPEC.md > docs/v2/TASKS.md > CLAUDE.md`。任务状态及 AC 归属见 [docs/v2/TASKS.md](../TASKS.md)。

Phase 20 当前范围已获批；0.1 初始执行授权仅限 T2001 开始和文档落盘，本次单独授权为 metric/execution protocol 与 Human coverage review evidence 整理。T2002/T2003 仍为 TODO，未获执行授权。不得实现 Evaluation Runner、运行 Benchmark、创建 Pilot 语料或修改产品行为。后续 SPEC 变更必须显式审阅批准。

## 2. 评估目标与单位

- 主要评估目标：**最终 V1 Hybrid Retrieval 输出**，即 merge → score → sort → relevance filter → Top-K 后的有序结果，不以单独 keyword/vector 分支或生成答案替代。
- 评估单位：Chunk。
- Phase 20 不得为了得到更好的 Baseline 而修改 V1 Retrieval。保留 `keyword_score * 0.3 + vector_score * 0.7`、现有 threshold、候选截断及 pipeline；Production Top-K 不变。
- 评估对象对应 `HybridRetriever.hybrid_search()` 的结果；generation 的 context 字符数截断属于后续步骤，不改变本契约的主评估边界。

## 3. 身份、快照与追溯

Ground Truth 与 Retrieval Result 的机器匹配使用**冻结 Evaluation Corpus / Index Snapshot 内的 `chunk_id`**。每份标注及结果必须能定位其 corpus version 和 index snapshot；不能将其他快照的 UUID 混入当前评估。

`chunk_id` 不承诺跨 re-ingestion 稳定。人工追溯使用 `file_name + chunk_index`，并以 `file_id` 作为快照内的补充证据；这些字段必须在明确的 corpus / collection 上下文中解释，不能替代机器匹配主键。

Page number 不作为必填项，因为当前 V1 metadata 无法可靠保留 page mapping。不得把 `chunk_index` 当作页码，也不得从 OCR warning 推造 chunk 页码。

重新 ingest 导致 IDs、内容或 chunk 边界变化时，必须创建新的 corpus / index version，并重新映射、审阅 relevance judgments。不得把旧 Ground Truth 无条件用于新索引。同一文件名或相同 chunk 顺序不构成跨版本等价证明。

## 4. Corpus 与 Pilot

Benchmark v1 使用**项目原创、可公开分发、企业知识库风格**的 Evaluation Corpus。记录来源及公开分发依据。已有 unit/integration test fixtures 不会自动成为正式 Benchmark 数据。

先进行小规模 Pilot，再形成正式 Benchmark v1。已存在的 [Pilot Snapshot 01](pilot-snapshot-01/README.md) 有四份原创源文档、38 个 chunks；[Reviewed 0.2](pilot-snapshot-01-annotation-packet-draft.md) 有六题人工批准的显式判断。CD-4 的规模目标见第 10 节；最终语料覆盖与版本仍需人工确认，本次不创建语料或查询。

Pilot 用于验证契约是否可执行、身份能否映射、标注是否明确、查询类别是否适用及规模安排是否合理。Pilot 的准备与验证需另行明确授权；它不授权提前实现 T2002 或执行 T2003。已获批的后续责任与流程见第 5 节；具体构建工作仍需单独执行授权。

## 5. Query 与人工标注

候选 query 类别如下；类别用于组织与分析，CD-4 的数量是建设目标而非硬配额。

| 类别 | 目的 |
|---|---|
| Direct Fact | 查询文档中明确陈述的事实 |
| Paraphrase | 使用不同表述查询同一知识 |
| Distractor | 在存在容易混淆的内容时检验相关性判断 |
| Multi-chunk | 问题所需证据涉及多个 chunks |

同时纳入 Answerable 和具有合理业务语境的 Unanswerable queries。不得用明显荒谬、完全无关的问题充数，以制造更高的 Unanswerable 覆盖。

LLM 可以辅助生成候选 query 和标注建议，但 query 进入正式数据集前必须经过人工审阅；最终 Ground Truth relevance judgments 必须由人工确认。LLM 输出不得自动成为 Ground Truth。

必须记录标注方法、审阅者 / 确认记录及其对应的数据版本。缺少人工确认的条目只能作为待审材料，不能混入正式评估。相关性判断针对冻结语料中的 chunks，不得只把当前 Retriever 返回的内容认定为全部 Ground Truth。

### 5.1 CD-1 — Annotation coverage semantics

Ground Truth 不要求物化 `Query × every chunk` 全矩阵。可显式保存全部 Grade 1–3 judgments、选定的 explicit Grade 0 hard negatives / reviewed controls，以及 provenance / reviewer metadata。

冻结快照中未列出的 chunk 只有在以下条件全部满足后才能解释为 implicit Grade 0：

1. Candidate screening 覆盖完整 frozen snapshot。
2. Human 完成 full-snapshot coverage review。
3. Human 明确确认没有遗漏的 positive evidence。
4. `coverage_reviewed = true`。
5. snapshot identity/version 已记录。
6. reviewer metadata 已记录。

`LLM did not list the chunk` 不等于 `Human Ground Truth = Grade 0`。只有 Human coverage confirmation 才赋予未列块 implicit Grade-0 semantics；覆盖确认必须针对具体 Query 及绑定快照，可用明确列举 Query 的批量确认记录。

Reviewed 0.2 的 30 项显式 Human judgments 保持有效且不变。2026-09-10 Human project owner 明确完成六题完整快照覆盖确认，见 [Human Coverage Gate：6/6 APPROVED](pilot-snapshot-01/coverage-review-packet.md)。仅对 PILOT-CQ-001～006、Reviewed 0.2、corpus novatech-pilot-0.1、snapshot t2001-novatech-pilot-01（38 chunks）记录 `coverage_reviewed=true`；198 对未列项现依据 CD-1 具有 implicit Grade-0 semantics，不转为显式标签。该确认来自 Human 指令而非 Codex 阅读推断，MUST NOT 扩展到未来 Queries、corpus versions、重建快照或未来 48-query dataset。

### 5.2 CD-3 — Ownership 与 annotation workflow

Frozen Corpus / Snapshot → LLM-assisted Candidate Query Generation → Human Query Review → LLM-assisted Candidate Chunk Screening over full frozen snapshot → Human Full-Snapshot Coverage Review → Human Relevance Judgment → Human Final Approval → Versioned Ground Truth。

LLM 可辅助生成 Candidate Query、全快照 Candidate chunk screening、建议等级、理由草稿和一致性检查。Human 对 Query wording、category、Answerable/Unanswerable、full-snapshot coverage、最终等级、Benchmark promotion 和未决判断拥有权威。

**LLM-generated or LLM-suggested judgments MUST NOT become final Ground Truth without Human Review.** 保留适用的 `suggested_grade`、`human_grade` 和 modification rationale；LLM 不是另一位权威标注员。

Benchmark v1 primary reviewer 为 **Human project owner**。Second independent annotator：**Not required for benchmark v1**。单人审阅可能产生主观 annotation bias；独立双人标注和 inter-annotator agreement 延后，不声称已完成，也不虚构姓名。

| 责任 / 工作项 | Owner 与授权边界 |
|---|---|
| 原创 corpus 获取、来源与可公开分发审阅 | Human project owner 对来源、访问限制、覆盖与冻结版本负责；LLM 可在单独授权下辅助创作和整理，不能自行批准来源或最终版本。 |
| Candidate Query / chunk screening | LLM 辅助；Human project owner 审阅措辞、类别和完整覆盖。 |
| Annotation / 判断冲突 | Human project owner 决定最终等级、可回答性、覆盖确认及未决项处理；Codex 记录 provenance。 |
| Split、泄漏核查与 promotion | Human project owner 批准 evidence-family 分组、Dev/Test 分配及最终数据集；构建执行须单独授权。 |

未解决判断支持 `NEEDS_REVIEW`。任何 Query 存在未决 annotation 或缺失必要 review，MUST NOT 进入冻结 Benchmark。

**Promotion Gate：** 仅当以下十项全部满足时，Candidate Query 才可进入 versioned Benchmark：Human 批准 wording；Human 批准 category；冻结 snapshot 绑定明确；Human 批准 Answerable/Unanswerable；full-snapshot coverage 完成；显式 judgments 获 Human 批准；不存在 `NEEDS_REVIEW` 或缺失/无效必要标注；provenance 完整；Dev/Test assignment 存在；leakage/evidence-family check 通过。Pilot 标签已获批不自动满足此门槛。

### 5.3 Unanswerable semantics

Unanswerable 是合理业务域内但语料不支持的问题，由 Human 确认 `answerable=false` 且无 relevant ground-truth chunks。条目保留于数据集，排除在主 Answerable Recall/MRR/nDCG 聚合之外并单独报告。无二值相关项但仍有弱相关的异常边界继续按第 8 节处理，不自动变成合法 Unanswerable。生成拒答能力属于后续 generation evaluation，不是 T2001/T2002 Retrieval scoring；本次不另造 Unanswerable 指标。

## 6. Relevance grades

| Grade | 术语 | 含义 |
|---|---|---|
| 3 | Highly Relevant | 高度相关 |
| 2 | Relevant | 相关 |
| 1 | Weakly Relevant | 弱相关 |
| 0 | Irrelevant | 不相关 |

Recall@K 和 MRR 使用 `relevance >= 2` 作为 binary Relevant；nDCG@K 保留完整 `0/1/2/3` graded relevance。Pilot 操作性判例已记录于 Reviewed 0.2；CD-2 保持此映射，最终契约验收已获 2026-09-10 Human Final Gate PASS。

### 6.1 CD-2 — Binary relevance 与 measurement boundary

Recall@K / MRR 保持 `grade >= 2 → relevant`，`grade 0 or 1 → not relevant`；nDCG@K 继续使用完整 0/1/2/3 grades。CQ-005 五个 grade >= 2 chunks 保持不变，**这不是 annotation error**，不得为缩小集合而改 Human grades。

Binary Recall/MRR 丢失 Grade 3 与 Grade 2 的 evidence-importance 差异。Recall@K 主要解释为 substantive relevant evidence coverage，MRR 主要解释为 first substantive relevant evidence rank；二者不能单独证明 core evidence 已成功检索。实验解释必须结合 graded nDCG 和 per-query evidence analysis。

`Grade-3 / Core-Evidence Recall@K` 仅为未来 T2002 可评估是否有用的 **candidate diagnostic**：NOT a required metric yet；NOT approved for implementation in this task。当前 EVAL-02 required metrics 仍为 Recall@K、MRR、nDCG@K。本次不实现任何指标；提及该诊断不授权启动 T2002。

## 7. Evaluation K 与 Human-approved metric/execution protocol

以下定义由本轮 Human 指令确认（记录日期 2026-09-10），只落盘协议，未实现、执行或验证 Runner，不授权启动 T2002/T2003。

### 7.1 指标定义

Evaluation K 固定为 **`[1, 3, 5, 10]`**。Recall@K / MRR 保持 `grade >= 2 → relevant`、`grade 0 or 1 → not relevant`；nDCG@K 保留完整 0/1/2/3 grades。Required metrics 仍仅为 Recall@K、MRR、nDCG@K；Grade-3 / Core-Evidence Recall@K 仍是第 6.1 节的 future candidate diagnostic。

所有计算消费按第 8 节去重后的实际返回顺序。对 query `q`，`R_q` 为绑定快照中全部 Human-approved grade >= 2 chunk IDs，`L_q` 为该快照实际有序 Retrieval Result。

- **Recall@K：** `|set(L_q[:K]) ∩ R_q| / |R_q|`；分母不能只取检索命中的相关块。
- **RR / MRR：** 首个 binary Relevant 的 rank 为 `r`，RR 为 `1/r`；声明截断内未命中为 `0`。按 K 报告 RR@K，对相同合格 Query 集合取算术平均为 MRR@K；不得把截断结果写成未注明深度的 MRR。
- **nDCG gain：** `gain(rel) = 2^rel - 1`，Grade 0/1/2/3 对应 0/1/3/7。
- **nDCG discount：** `discount(rank) = 1 / log2(rank + 1)`，rank 从 1 开始。本版用乘法折扣命名，和旧版以 log2 为分母的公式数值一致。
- **DCG / IDCG：** `DCG@K = Σ((2^rel_i - 1) / log2(i + 1))`；IDCG@K 按同一 Query 的完整有效 Ground Truth grades 理想降序排列计算；`nDCG@K = DCG@K / IDCG@K`。
- **Aggregation：** 主 relevance aggregate 对合格 Answerable Queries 做 per-query 算术平均并报告分母；不同 K、split 和 dataset version 分开统计。

**Answerable validation boundary：** `answerable=true` 但 Human-approved Ground Truth 没有任何 grade >= 2 judgment，属于 dataset validation failure，MUST 阻止 official benchmark，不能转成合法 retrieval zero score。即使存在 Grade 1、数学上可能有正 IDCG，也不满足当前契约；更不能静默对无有效分母的 nDCG 计分。合法 Unanswerable 按第 5.3 / 8 节单独报告，不进入主聚合。

### 7.2 Evaluation request depth 与 Production Top-K

V1 **production default Top-K = 5** 保持不变；T2002/T2003 evaluation protocol 的请求深度候选冻结为 **`evaluation_request_depth = 10`**。评估协议在此声明深度 10，未来消费这一请求实际返回列表的前 K 项，不将各 K 独立请求混称为同一次评估。

V1 HybridRetriever 的内部 branch candidate depth 依赖请求参数 `top_k`。因此 `top_k=10` 的内部候选深度与 production `top_k=5` 不同，执行轨迹并不完全相同；从深度 10 列表取前 5，也不保证等同于独立 production top_k=5 的结果。

`@1`、`@3`、`@5` 是位于 production Top-K boundary 内的主要可解释 Retrieval metrics，但仍需披露它们来自深度 10 的评估执行。`@10` 必须解释为 **deeper retrieval diagnostic under evaluation request depth 10**，不得称为 `production Recall@10`。

正式 Benchmark metadata MUST 记录 production default Top-K、evaluation request depth、V1 internal candidate-depth dependency，以及由此产生的 execution difference / confounder。不得为消除差异修改 V1 Retriever、默认 Top-K、threshold 或 fusion weights。

### 7.3 Tie handling 与 repeatability

Evaluation Runner MUST 消费 V1 实际返回顺序，MUST NOT 新增 secondary sort、按 chunk_id 重排、修改 score tie 行为或为稳定 Benchmark 改动 V1。IDCG 的理想排序仅用于指标定义，不是对实际 Retrieval Result 的重排。

既有 investigation 指出相同 score 排名可能存在跨进程不稳定风险；这是静态风险，不是本轮测量发现。**T2002 MUST 提供 ranking repeatability / instability check**，以检查这一风险。建议 diagnostics 包括 query_id、repeated run count、ranked chunk_id order 是否变化、受影响位置及适用时的指标变化。具体重复次数不在本轮虚构；本轮不实现 check 或修复。

若后续发现不稳定，必须报告并保留 evidence，不在 Phase 20 Baseline 前自动修复 V1，不通过评估层排序掩盖变化。

## 8. Fail-fast dataset / protocol validation 与合法空结果

### 8.1 Official benchmark 的执行前阻止条件

以下任何一项出现，MUST 在 official benchmark 执行前报告 dataset/protocol validation failure 并阻止本次 official benchmark；不得静默跳过坏 Query 后仍宣称该输入版本的正式结果有效，也不得将错误计为检索零分：

1. duplicate `query_id`。
2. missing corpus/snapshot binding。
3. judgment `chunk_id` 不存在于绑定 snapshot。
4. `file_name / chunk_index / chunk_id` 映射与 snapshot 冲突。
5. relevance grade 不属于 `{0,1,2,3}`。
6. `answerable=true` 但没有任何 Human-approved grade >= 2 Ground Truth。
7. required `coverage_reviewed != true`（含缺失或 pending）。
8. required review status 不是 `APPROVED`。
9. unresolved `NEEDS_REVIEW`。
10. missing/invalid split（正式数据必须为 Dev 或 Test）。
11. 同一 `evidence_family_id` 跨 Dev/Test。
12. 同一 `(query_id, chunk_id)` 存在冲突 Human judgments。
13. required provenance/version metadata 缺失，含必要 evidence-family 归属及 reviewer provenance。
14. query category 超出批准 schema（Direct Fact / Paraphrase / Distractor / Multi-chunk）。
15. dataset 引用的 snapshot version 缺失或不兼容。

适用本契约的其余必要 schema/approval 条件同样必须有效；LLM 建议不能冒充 APPROVED。未列块仅在 CD-1 全部条件满足后具有 implicit Grade-0 semantics。`answerable=true` 与无 binary Relevant 的冲突 MUST 送回审阅，不能自动改成 Unanswerable。

### 8.2 合法 Retrieval observation 与边界

| 情况 | 处理 |
|---|---|
| Dataset 合法，Answerable Query 有有效 Ground Truth，但 Retriever 返回 0 results | 是合法 benchmark observation；按定义在各适用 K 下记录 Recall/RR/nDCG 为 0，保留 Query 于主聚合。不是 dataset validation failure。 |
| Human-approved、覆盖审阅完整的合法 Unanswerable | answerable=false，保留条目但排除主 Answerable Recall/MRR/nDCG aggregate；单独报告数量、返回情况和误召回分析，不另造指标，不宣称生成层正确拒答。 |
| 无 binary Relevant 但存在 Grade 1 | 若 answerable=true，按第 8.1 节阻止执行；不得用“排除聚合”绕过无效 Answerable。非此类有效性冲突的条目保留 graded annotation 并单独报告，不产生有效主 relevance aggregate。 |
| 重复 Retrieval chunk_id | 保留第一次出现，删除后续重复；记录重复数量和位置，不重新检索补足。与冲突 Ground Truth 的 fail-fast 不同。 |
| 同分 | 保持 V1 实际返回顺序；按第 7.3 节检查与报告 repeatability，不添加 secondary sort。 |
| 返回少于 K | 使用实际列表，缺失名次不贡献 gain 或命中，不补造结果。 |
| IDCG 为零 | 不产生有效主 nDCG 值；有效无相关项按 Unanswerable/无相关项规则单列，无效 Answerable 必须 fail-fast，不能作为正常零分。 |

有效无相关项是 Human 明确确认的判断，不等于遗漏标注；合法空 Retrieval Result 也不等于无效 Ground Truth。本节只定义执行边界，不实现 validator 或运行指标。

## 9. 输出要求

后续获授权的评估输出必须包含：

- **Per-query**：query 标识、类别、Answerable 状态、split、数据版本 / snapshot、实际 Retrieval 顺序及分数、匹配的 chunk IDs、各 K 的指标或排除原因、去重及验证 diagnostics。
- **Aggregate**：各 K 的 Recall、MRR、nDCG，纳入 / 排除 / 无效 query 数量与分母，数据及配置引用。
- **Query-type breakdown**：按查询类型分别报告相同指标及样本数；Unanswerable / 无相关项单列，不混入主 relevance aggregate。

无合格 query 的分组应标为无可用聚合，而不是给出虚构均值。任何 latency / cost 未测量时必须明确写未测量。本次只定义这些输出要求，不创建输出文件或数值。

## 10. CD-4 — Benchmark v1 target 与 Development / Test

当前建设目标为 40 个 Answerable（Direct Fact / Paraphrase / Distractor / Multi-chunk 各 10）及 8 个 Unanswerable，总目标 48。Dev 和 Test 各以 20 Answerable + 4 Unanswerable 为目标；各 split 的 Answerable 四类分别以 5 个为目标。

这是质量导向的 target，不是 synthetic quota。不得为凑数重复核心证据或制造低质量改写。若高质量覆盖不足，可以低于目标，但必须记录缺口、明确覆盖局限，并由 Human 批准最终数据集版本。本次不生成 48 题、不补充 Query 或 Unanswerable，也不分配尚不存在条目的实际 evidence-family IDs。

Dev 用于研究、调参、错误分析及后续获授权 Phase 的 Candidate comparison。Test 是 Candidate/config 决策后的 held-out 最终评估集，MUST NOT 被反复用于调参。

**Evidence-family leakage control：** 实质依赖同一核心政策事实/核心证据的 Queries 属于同一 `evidence_family_id`。同一 evidence family MUST NOT 跨 Dev/Test；不能只依赖随机 Query split。多个依赖同一外部培训住宿上限事实的改写或 Distractor 必须同属一 split。构建时按核心证据审阅分组，不能靠更换 Query 措辞绕过隔离规则。

## 11. Provenance 与已知局限

以下是契约需要的信息，不是已经存在的数据记录，也不强制指定 JSON 等序列化实现：

| 信息 | 要求 |
|---|---|
| Dataset version | 标识 query、relevance、split 及审阅记录的版本 |
| Corpus version | 标识源文件集合及内容版本，说明变更与公开分发来源 |
| Index snapshot | 标识冻结索引及其 chunk ID / 文本 / metadata 映射，绑定 corpus version |
| Source provenance | 项目原创来源、作者 / 维护归属及可公开分发依据 |
| Annotation / review method | LLM 辅助范围、人工标注 / 复核方法、确认记录及未决问题 |
| Git revision | 产品实现、评估工具（存在后）及相关契约的版本，不把未提交文件冒充已提交版本 |
| Ingestion configuration | parser / chunking 配置、embedding 模型与相关版本、OCR 条件及失败边界 |
| Retrieval configuration | fusion weights、threshold、production default Top-K=5、evaluation_request_depth=10、Evaluation K、V1 internal candidate-depth dependency 及 execution difference/confounder；记录实际生效配置 |
| Known limitations | 快照身份、页级追溯、metadata 透传、并列排序及数据覆盖等限制 |

当前代码依据及局限：

- [chunk_text / IngestService](../../../backend/app/services/ingest.py) 使用随机 UUID4；重新 ingest 不保证身份稳定。PDF 文本拼接与清洗后切分，没有可靠 page mapping。
- [ChromaVectorStore](../../../backend/app/core/vector_store.py) 保留 chunk metadata，`file_name + chunk_index` 可用于快照内人工定位；文件名和 collection 名称不是跨版本不变标识。
- [Keyword / Vector / Hybrid Retriever](../../../backend/app/services/qa.py) 的正常两路结果没有透传完整 metadata，Hybrid 的 `metadata` 通常为 `{}`。需要追溯字段时，应依据冻结 snapshot 的 chunk 映射核对，不假设结果携带 page / chunk_index。
- Keyword 候选顺序涉及 set 遍历，排序没有显式次级键，因此存在 tied-score repeatability 风险。这是**静态代码分析发现的风险，未经本次运行确认**。记录实际顺序和环境，不为改善复现性而改写 V1 排序。

## 12. Versioned dataset 最小 schema 要求

这是契约级字段定义，不实施 JSON/Pydantic schema 或 Runner。字段可按等价结构表示，但须覆盖以下语义；不为尚未构建的正式查询分配 ID。

| Query-level 字段 | 必须表达的含义 |
|---|---|
| `query_id`, `query_text`, `query_category` | 数据版本内可识别 Query、原文、人工批准类别；Pilot `PILOT-CQ-*` 不自动变成最终 Benchmark ID。 |
| `answerable` | Human-approved boolean；false 遵守第 5.3 节，不能由 LLM 或缺失标签推断。 |
| `corpus_version`, `snapshot_id`, snapshot version/identity | 绑定冻结来源与索引；identity/version 必须足以唯一确定该快照，不要求额外冗余版本号。 |
| `split`, `evidence_family_id` | Dev/Test 分配与核心证据家族；同一家族不跨 split。 |
| `coverage_reviewed` | 仅在 CD-1 全部条件满足时为 true；pending 不能伪装成 true。 |
| `review_status` | 能表达待审、`NEEDS_REVIEW` 与 Human `APPROVED`，未完成 review 不进入 frozen dataset。 |
| reviewer role / review provenance | 记录 Human project owner 角色、审阅日期、明确决定来源；coverage 确认、措辞、类别及 answerability 批准可追溯，姓名仅在实际提供时记录。 |
| dataset version / provenance | 源语料来源、数据版本、生成/修改方法、Git context、最终批准记录与已知局限，可放在 dataset-level 并由 Query 引用。 |

| Judgment-level 字段 | 必须表达的含义 |
|---|---|
| `chunk_id`, `file_name`, `chunk_index` | 冻结快照精确身份与人工追溯映射；`file_id` 可作补充，不替代 chunk_id。 |
| `relevance_grade` / `human_grade` | 人工最终 0–3 等级；可使用一个最终等级字段，不要求复制两份同义值。 |
| `suggested_grade`（适用时） | 保留原 LLM 建议，不能冒充 Human grade。 |
| human review status / provenance | 明确此判断是否经 Human 批准、何时、依据何记录，并继承对应 Query/snapshot binding。 |
| rationale（需要时） | 修改理由、争议/特殊语境判例；发生建议与最终等级不同或 unresolved 判断时保留理由。 |

Query 与 judgment 的关联必须明确。未知 chunk_id、映射/快照不匹配、无效等级、冲突判断、缺失必要审阅或未满足覆盖语义均需显式验证，不能以 implicit Grade 0 掩盖错误。

## 13. T2001 Closing Checklist — Human Final Gate PASS

历史 readiness 中 AC-2001-2/3 为 SATISFIED BY CONTRACT；2026-09-10 Human Final Gate 已确认 AC-2001-1/2/3 均 SATISFIED 并批准 T2001 DONE。该 Task Gate 不等于 Phase 20 Gate PASS，后续实现/运行并未执行。

| AC | 状态 | 定义与证据映射 | 剩余确认 |
|---|---|---|---|
| AC-2001-1 | SATISFIED | 第 2–6、10–12 节定义契约维度，冻结 Pilot 与 Reviewed 0.2 支持身份/标签映射；[Human Coverage Gate](pilot-snapshot-01/coverage-review-packet.md) 已 6/6 APPROVED，CD-1 已由 Pilot 完整人工覆盖确认验证。 | Human project owner 于 2026-09-10 Final Gate 确认通过；后续任务/数据构建仍受独立授权约束。 |
| AC-2001-2 | SATISFIED | 第 6–9 节明确 K、binary/graded mapping、gain/discount、aggregation、depth=10 与 production Top-K=5 差异、tie/repeatability、15 项 fail-fast 条件、合法空结果及 Unanswerable 处理。 | Human project owner 于 2026-09-10 Final Gate 确认通过；后续任务/数据构建仍受独立授权约束。 |
| AC-2001-3 | SATISFIED | 第 4–5、10–14 节定义 corpus 来源与获取责任、Candidate generation、标注权威、coverage、promotion、48 题质量目标、Dev/Test、evidence-family 隔离、T2003 前检查点及单审阅者局限。 | Human project owner 于 2026-09-10 Final Gate 确认通过；后续任务/数据构建仍受独立授权约束。 |

### OPEN / PENDING 清单

1. **已完成：Pilot full-snapshot Human coverage confirmation。** 2026-09-10 6/6 APPROVED，仅对已绑定 Pilot set 启用 coverage_reviewed=true；显式 30 项未变、隐式 198 对保持稀疏语义。
2. **已完成定义：metric/execution protocol。** 本版第 7–8 节已记录本轮 Human 决定，不再列为 contract-level PENDING；实际实现与验证留待后续单独授权，本轮未执行。
3. **已完成：T2001 Final Human Gate PASS。** Human project owner 于 2026-09-10 批准 T2001 DONE 和 Contract 0.3 FROZEN；Phase 20 Gate 未通过本决定获批。
4. **PENDING（后续交付，不强制本轮完成）：** 最终 corpus 覆盖/版本、质量目标缺口说明、实际 Dev/Test/evidence-family 构建、全部必要 Human approvals、versioned dataset 交付及单独工作授权。Pilot 的 wording/category 和显式等级已获批，不自动证明 benchmark promotion 各项完成。

CQ-005 binary breadth 的映射选择已由 CD-2 决定，不再作为未解决映射问题；保留的 measurement limitation 不是需要擅自“修复”的 annotation error。Grade-3 Recall 仍为未批准实现的候选诊断，不是 T2001 关闭的强制新增指标。

## 14. Contract completion 与 dataset construction / T2003 前检查点

T2001 定义 Dataset Contract 并以 Pilot 验证；不要求关闭时完整 Benchmark v1 已有 48 Queries。Contract 冻结后的 dataset 构建可以安排在另行获授权的工作项/检查点，但必须遵守 SPEC/TASKS 依赖，新增 Task 必须明确批准。

1. **Contract / T2001 Gate：** Pilot coverage 已获 Human 确认；独立 Human Final Gate 已于 2026-09-10 PASS，T2001 DONE；本轮仅记录该决定。
2. **Dataset construction authorization：** Human project owner 确认后续构建工作项、执行授权、来源与最终覆盖安排；LLM 辅助受第 5 节约束。本轮不授予该执行权限。
3. **Versioned dataset readiness（T2003 前）：** 实际存在冻结 corpus/snapshot、经 Human 批准的版本化 queries/judgments、完整 coverage/provenance、Dev/Test 与 evidence-family leakage 检查、质量目标差额说明及最终版本批准；所有 promotion 条件通过。
4. **T2003 readiness：** 上述真实数据必须已存在，且 T2002 DONE、模型/索引/环境可用并满足 SPEC/TASKS 的全部依赖与授权。只有目标、契约或 Pilot 草稿不够。T2003 MUST NOT 在缺少已审阅版本化数据集时运行。

T2001 已为 DONE；T2002/T2003 仍为 TODO，未获执行授权。以上阶段区别不授权本轮启动 T2002/T2003、运行 Retrieval/metrics/Benchmark 或创建更多 Queries。

## 15. T2001 Final Human Gate readiness evidence — 2026-09-10

下表保留 Final Gate 前的 readiness evidence，全部 READY；2026-09-10 Human project owner 已依据这些证据作出第 16 节 PASS / DONE / FROZEN 决定。READY 不表示 T2002 实现/测试已执行。

| 审阅项 | 状态 | 契约 / evidence |
|---|---|---|
| Dataset identity/versioning | READY | 第 3、11–12 节：Query/dataset/corpus/index 版本与追溯。 |
| Frozen snapshot binding | READY | 第 3、5.1 节：Pilot 精确绑定 snapshot、corpus 和 Reviewed 0.2。 |
| Evaluation unit | READY | 第 2 节：Chunk；最终 V1 Hybrid Retrieval 输出。 |
| Query schema | READY | 第 12 节：Query identity、text、category、answerable、split/review/provenance。 |
| Relevance schema | READY | 第 6、12 节：0–3、chunk 身份映射、suggested/Human grade。 |
| Human authority | READY | 第 5.2 节：Human 最终权威、LLM 仅辅助、promotion 条件。 |
| Full-snapshot coverage semantics | READY | 第 5.1 节及 Coverage Gate：6/6 APPROVED；30 显式 + 198 隐式，限定快照/六题。 |
| Answerable/Unanswerable | READY | 第 5.3、8 节定义批准与无相关项处理；不伪造新 Unanswerable。 |
| Query categories | READY | 第 5 节四类；Pilot 保留 2/2/1/1。 |
| K | READY | 第 7.1 节：[1,3,5,10]。 |
| Recall | READY | 第 6.1、7.1 节：grade >= 2 映射与 coverage 解释。 |
| MRR | READY | 第 7.1 节：首个相关 rank、截断与聚合。 |
| nDCG | READY | 第 7.1 节：完整 graded gain、discount、IDCG。 |
| Edge cases | READY | 第 8.2 节：合法空结果、无相关项、重复及短结果。 |
| Fail-fast validation | READY | 第 8.1 节：15 项 official benchmark 阻止条件。 |
| Request depth boundary | READY | 第 7.2 节：production 5 / evaluation 10，候选深度依赖及 confounder。 |
| Tie/repeatability protocol | READY | 第 7.3 节：保持实际顺序；未来检查不等于本轮执行或修复。 |
| Aggregation | READY | 第 7.1、9 节：合格 Answerable 均值，分 K/split/version 并报告分母。 |
| Dev/Test semantics | READY | 第 10 节：Dev 研究/调参，Test held-out。 |
| Evidence-family leakage control | READY | 第 10 节：同核心证据家族 MUST NOT 跨 split。 |
| Provenance | READY | 第 11–12 节及 Pilot evidence：Human 角色、日期、决定来源、版本及修改历史。 |
| Limitations | READY | 第 6.1、7.2–7.3、11 节：binary 信息损失、depth confounder、单审阅者和同分风险。 |
| Pilot validation | READY | Snapshot 38 chunks、Reviewed 0.2 六题/30 显式判断、6/6 Human coverage approval。 |
| Future dataset construction checkpoint | READY | 第 14 节：另行授权构建，质量目标不等于强制完成 48 题。 |
| Pre-T2003 dataset requirement | READY | 第 14 节：T2003 MUST NOT 在真实版本化、Human-reviewed evaluation dataset 缺失时运行。 |

未发现剩余 T2001 Contract/Pilot evidence blocker。下方 Human Final Gate 已批准完成与冻结；完整 Benchmark 构建、实际 Dev/Test/evidence families、Runner/metrics 实现与测试、repeatability execution、Baseline 仍为后续单独授权工作，不是本次已执行的产物。

## 16. Human Final Gate decision 与 Freeze semantics

- Human decision：**APPROVED**。
- Review / freeze date：**2026-09-10**。
- Approval authority：**Human project owner**；未提供个人姓名，不虚构姓名。
- 决策来源：本轮 Human Final Gate 明确指令，批准 `T2001 IN_PROGRESS → DONE`、`Retrieval Evaluation Dataset Contract 0.3 = FROZEN`、`T2001 Final Human Gate = PASS`。
- Gate basis：AC-2001-1 SATISFIED、AC-2001-2 SATISFIED、AC-2001-3 SATISFIED；真实 Pilot 已验证契约；Human Full-Snapshot Coverage Gate = 6/6 APPROVED；全部 25 项 readiness = READY；无剩余 T2001 契约/Pilot 证据 blocker。

Contract **版本仍为 0.3**，仅状态变为 **FROZEN**；这是下游 Phase 20 工作的权威 T2001 measurement/data contract，仍服从 V2 SPEC/TASKS 治理层级。FROZEN 表示下游工作 **MUST NOT 为适应实现或结果而静默修改批准的定义**，至少包括：evaluation unit、snapshot binding、query schema、relevance grades、binary mapping、nDCG gain/discount、K、aggregation、Answerable/Unanswerable、implicit Grade-0 coverage semantics、fail-fast rules、evaluation request-depth boundary、tie-order handling、Dev/Test semantics、evidence-family leakage rule 和 Human Ground Truth authority。

未来若实现发现真实契约缺陷，不得静默修复，必须按 V2 governance 提交明确的 Human-reviewed contract revision / decision 并保留版本与批准记录。

批准仅适用于 **T2001**，不批准 Phase 20 Gate，也不授权 T2002/T2003。**T2002 = TODO；T2003 = TODO**。不得从完成依赖推断已获 Runner、metrics、fixtures、Retrieval、Benchmark、正式 Query 构建或 repeatability runs 的权限。

Pilot evidence 保持六题、冻结 38 chunks、30 explicit judgments（Grade 3/2/1/0 = 7/7/3/13）、198 implicit Grade-0 pairs、6/6 Coverage APPROVED；coverage_reviewed=true 仅限 Reviewed 0.2 六题及确切 Pilot snapshot/corpus，CQ-005 不变。当前六题 Pilot **不是自动获批的正式 V1 Baseline Dataset**。

Benchmark v1 仍以 40 Answerable + 8 Unanswerable 为 quality-over-count 目标，Dev/Test 按 evidence family 隔离。T2001 完成不表示目标数据已构建；**T2003 MUST NOT 在缺少真实版本化、Human-reviewed evaluation dataset 时运行**，并须满足 T2002 DONE、模型/索引/环境及明确执行授权等既有条件。本轮未开始任何后续工作。
