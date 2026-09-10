# Phase 20 — 检索评估基础：Task 学习素材

本文件积累 Task Learning Pass，供后续 Phase Learning Review 整合。当前仅包含检索评估数据集契约的学习记录，尚未形成最终 Phase 教材、Engineering Review 或 Phase Gate 结论。流程依据：[Workflow V2](templates/phase-learning-pass-workflow.md) 与 [学习模板 Part A](templates/phase-learning-template.md)。

## 检索评估数据集契约：先定义怎样判断，再测检索效果

Task reference：T2001；学习记录日期：2026-09-10。范围为已冻结的 Contract 0.3、Pilot Snapshot 01、Reviewed 0.2 和对应人工覆盖确认，并核对当前 V1 代码。本文解释已有决定，不修改定义或产生新的人工标签。

### 1. 新增了什么，为什么需要？

系统已经能检索文档，但“能返回结果”不等于“能证明返回了正确证据”。在讨论优化之前，需要先约定哪些问题可以回答、哪些块算相关、如何识别同一块、怎样计算分数，以及什么输入根本不具备评估资格。

此次新增的是可审阅、已冻结的**测量与数据契约**，并有小规模真实入库及人工审阅材料支撑可执行性。它没有新增应用函数，也没有交付 Runner 或检索质量结果。

研究问题（Research Question）是：能否为现有 V1 Hybrid Retrieval 建立可追溯、可人工审阅、定义明确的评估输入与测量规则？参考行为（Baseline）是已发布的 V1 检索流程；当前变化是建立评估协议与 Pilot 证据。Benchmark 发现仍未测量，不能声称质量提高或某种 Candidate 更优。

上游提供冻结语料、真实 chunk 映射与人工判断；下游获授权后才能实现指标与 Runner，再用正式数据集采集 Baseline。完整依赖和 AC 见 [V2 TASKS](../v2/TASKS.md)，评估目标见 [V2 SPEC 第 3–4 节](../v2/SPEC.md)。

### 2. 先理解六个概念

| 概念 | 在本项目中的意思 | 容易误解的地方 |
|---|---|---|
| Ground Truth（相关性真值） | 人工确认某个 query 与冻结快照中某个 chunk 的相关性等级 | Retriever 返回的结果或 LLM 建议不能自动成为真值 |
| Snapshot（快照） | 固定的一组 chunk 身份、文本和 metadata，绑定 corpus version | 相同文件重新入库后 UUID 不保证相同 |
| Graded / binary relevance | 原始等级为 0–3；Recall/MRR 将 grade ≥ 2 视为相关 | Grade 2 与 3 对 binary 指标贡献相同，但证据重要性不同 |
| Coverage review（覆盖审阅） | 对该 query 检查完整冻结快照，人工确认没有遗漏 Grade 1–3 | 阅读了 Retriever 的候选列表不等于检查了全语料 |
| Implicit Grade 0（隐式零级） | 满足全部覆盖条件后，未显式列出的 query–chunk 对可解释为 0 | 未列出本身不是 0，也不是新增一条显式人工标注 |
| Evidence family（证据家族） | 实质依赖同一核心事实或证据的一组 queries | 改写措辞后随机分到 Dev/Test，仍可能泄漏同一事实 |

Dev（开发集）用于研究、调参、错误分析及后续获授权的 Candidate comparison；Test（测试集）留出到 Candidate/config 决策后做最终评估，不得反复用于调参。如果同一核心事实的改写跨越两者，Dev 上的调参就可能间接利用 Test 的证据。因此，同一 evidence family 必须放在同一 split，不能仅按 query 随机分组。

对熟悉 TypeScript 的读者，可把 snapshot 想成一个版本固定的实体表，judgment 通过 `chunk_id` 引用表中对象。但这里引用的有效性还依赖 snapshot identity；只检查字符串 ID 的类型正确远远不够。

人工等级与系统检索分数也要分开：`grade >= 2` 是指标的相关性映射；`MIN_RELEVANCE_SCORE = 0.30` 是检索结果的过滤阈值。二者的尺度、来源和职责不同，不能互相代替。

### 3. 哪些文档和代码承载它？

本 Task 的新增能力由文档契约承载；以下代码是被核对的既有实现，不是本 Task 新增或修改的代码。

| 文件 → 章节 / 符号 | 职责与重要行为 |
|---|---|
| [Dataset Contract](../v2/evaluation/retrieval-evaluation-dataset-contract.md) → 第 2–12 节 | 定义评估边界、身份、审阅、等级、指标、无效输入、split 与 provenance；第 14–16 节区分后续数据交付与本 Task 人工关闭 |
| [snapshot.json](../v2/evaluation/pilot-snapshot-01/snapshot.json) / [Chunk Inventory](../v2/evaluation/pilot-snapshot-01/chunk-inventory.md) | 保存真实入库时的 ID、正文、metadata 和执行上下文；用于把人工判断定位到块，不是向量索引备份 |
| [Reviewed 0.2](../v2/evaluation/pilot-snapshot-01-annotation-packet-draft.md) → 六题 Human grade 表及历史区 | 保存原建议、人工最终等级及修改理由；路径含 draft，但当前版本是 Reviewed 0.2 |
| [Coverage Gate](../v2/evaluation/pilot-snapshot-01/coverage-review-packet.md) → 逐题决定 / Overall Pilot Coverage Gate | 保存完整快照人工确认，赋予限定范围内未列项隐式 0 语义 |
| [ingest.py](../../backend/app/services/ingest.py) → `chunk_text()` | 标题切分、超长块递归切分、枚举顺序并为每块生成 UUID4；`chunk_index` 是顺序，不是页码 |
| [vector_store.py](../../backend/app/core/vector_store.py) → `ChromaVectorStore.list_chunks()` / `search()` | 读回冻结块及完整 metadata；向量查询输出 `similarity_score` |
| [qa.py](../../backend/app/services/qa.py) → `VectorRetriever.vector_search()` / `HybridRetriever.hybrid_search()` | 映射分数、合并两路候选、固定加权、排序、阈值过滤、Top-K；最终列表是本契约测量对象 |

**身份机制精读。** `chunk_text()` 对每个 `piece` 执行 `str(uuid.uuid4())`，通过 `enumerate(pieces)` 产生从 0 开始的 `chunk_index`。Python 的 `enumerate` 类似在 JS `map((piece, index) => ...)` 中取得位置，但位置相同不意味着对象身份相同。再次 ingest 会重新生成 UUID；旧 judgments 不能仅凭同名文件或同序号直接复用。PDF 的拼接、清洗与切分也没有建立可靠页码映射。

**请求深度机制精读。** Hybrid 内部先计算 `expanded_top_k = top_k * 2`，将其传给 keyword 和 vector 两路。Vector 内部又向 store 请求其接收参数的两倍，再切回接收参数的长度。因此 production 请求 5 时，两路接收 10、向量 store 请求 20；evaluation 请求 10 时，两路接收 20、向量 store 请求 40。这是代码参数推导的请求上限，不保证实际返回这么多条。

因此深度 10 列表的前 5 项不保证等于独立请求 5 的结果。契约保持 production default Top-K=5，冻结 evaluation_request_depth=10，并要求披露这一执行差异。`@10` 是较深检索诊断，不能称为 production Recall@10。

**输出机制精读。** Hybrid 按 `chunk_id` 合并；缺少一路分数时以 0 参与 `0.3 * keyword_score + 0.7 * vector_score`；降序后保留 `final_score >= 0.30`，最后切 Top-K。正常 keyword/vector 字典不透传完整 metadata，虽然 Hybrid 尝试接收 metadata，正常路径通常仍为 `{}`。人工追溯须查 snapshot，不能假设结果有 `chunk_index` 或 page。

### 4. 数据和控制怎样流动？

```text
原创政策语料 → 真实 V1 入库 → 冻结 snapshot（ID / 文本 / metadata）
                                     ↓
候选 query → Human 审阅措辞、类别、可回答性
                                     ↓
全快照辅助 screening → Human 覆盖审阅与 relevance judgment
                                     ↓
                           绑定版本的人工 Pilot labels
                                     ↓ 后续需单独授权与 promotion
                正式版本化数据（split / evidence family / provenance）
                                     ↓ 后续 Runner，尚未实现
                校验输入 → 最终 Hybrid 列表 → 去重 → 各 K 指标
                    └ 无效数据：阻止 official benchmark，不能伪装成零分
```

当前已存在 Pilot 和人工标签；正式数据集与 Runner 属于图中的未来节点。生成层的 `assemble_context()` 和模型回答位于主检索测量边界之后，context 字符截断或回答正确性不是此次测量对象。

用已存在的协作时段问题走一遍身份链：`PILOT-CQ-001` 询问每天共同协作时间；在绑定的 `t2001-novatech-pilot-01` / `novatech-pilot-0.1` 中，`employee_handbook.md` 的 index 2 对应 `392ae2da-31b8-4baa-b7dc-03020e492488`。该块直接给出 10–12 点、14–17 点及适用例外，人工为 Grade 3；index 5 只提及遵守协作时段，人工从建议的 2 改为 1。前者进入 binary relevant set，后者不进入。这是现有标注与映射的解释，没有运行这个 query 或构造检索排名。

### 5. 指标实际回答什么？

Evaluation K 为 `[1, 3, 5, 10]`，未来消费同一次深度 10 请求的列表前缀。先保留重复 chunk_id 的第一次出现，记录后续重复位置和数量，不重新检索补足；同分保留 V1 实际顺序，不能按 ID 二次排序。

| 指标 | 冻结定义的直观解释 | 解释边界 |
|---|---|---|
| Recall@K | 前 K 项命中了完整人工相关集合的多少：命中去重数 / 全部 grade ≥ 2 块数 | 分母不能只用 Retriever 命中的相关块；不区分 2 与 3 |
| RR@K / MRR@K | 截断内第一个相关块在 rank r，则该题为 1/r，否则为 0；合格题目算术平均 | 只关注首个 substantive evidence，不能证明必要证据全部到齐；必须标明 K |
| nDCG@K | 将等级变为 gain 0/1/3/7，每项乘以 `1/log2(rank+1)`，将前 K 个位置的折扣 gain 求和得到 DCG@K；再将完整有效真值按等级降序理想排列，对前 K 个位置做相同的折扣求和得到 IDCG@K；两者相除得到 nDCG@K | 保留等级信息，但仍需逐题分析；理想排序不授权重排实际检索结果 |

主聚合是合格 Answerable queries 的逐题算术平均，按 K、split、dataset version 分开，并报告分母、排除与无效数量、query-type breakdown。没有合格题目的分组没有可用均值。合法 Unanswerable 单列数量、返回情况及误召回分析，不混入主 relevance 均值，也不证明生成层能正确拒答。

### 6. 为什么这样设计？

| 决定及依据性质 | 理由与接受的成本 |
|---|---|
| 冻结快照内用 chunk_id 匹配（Documented：契约第 3、11 节；UUID 机制经源码核对） | 使判断和结果有精确实体对应；代价是重新入库必须新建版本并重映射、重审 |
| 稀疏保存 judgments，隐式 0 以人工覆盖为前提（Documented：CD-1） | 无需物化完整 query × chunk 矩阵；节省记录量却不能省略全快照审阅，规模扩大后人工成本仍存在 |
| 保留 grade ≥ 2 映射和 CQ-005 五块相关集合（Documented：CD-2） | 接受 substantive evidence coverage 的含义，同时用 graded nDCG 和逐题证据分析解释重要性损失；未证明该映射最优 |
| Human project owner 为最终权威，v1 不要求第二标注员（Documented：CD-3） | LLM 可辅助、不可自批 Ground Truth；接受单人审阅偏差，未做 inter-annotator agreement |
| 质量优先、按 evidence family 隔离 Dev/Test（Documented：CD-4） | 避免凑数量和同一事实的改写泄漏；目标可能达不到，须记录覆盖缺口并获最终人工批准 |
| 保持 V1 顺序及行为，披露 depth 差异（Documented：第 7 节） | 保留待测对象的真实性；代价是暴露同分复现风险及评估与生产请求轨迹差异 |

上述是有文档来源的接受理由，不是本次新 ADR。Candidate 检索策略的效果、最优等级阈值、实际同分波动幅度均为 Unknown / 未测量。将“测量条件也属于可复现对象”作为通用工程启发，是本次学习推论（Inferred），不代表已有实验结论。

### 7. 哪些地方确实困难，哪些只是风险？

真实发生的困难主要在标注语义：[Reviewed 0.2](../v2/evaluation/pilot-snapshot-01-annotation-packet-draft.md) 保存 30 项判断，14 项修改、16 项接受原建议。一般联系渠道、共享关键词或通用审批流程不自动贡献证据。全文包含干扰数字也不能机械判 0：CQ-005 的差旅住宿块虽有 500 元，却明确排除其对外部培训的适用，因此人工保持 Grade 2。

CQ-005 的核心培训金额块为 Grade 3，另外四块为 Grade 2。binary 指标把五块都视为相关，这暴露的是测量信息损失；CD-2 已明确不是 annotation error，不可为让结果好看而缩小真值集合。CQ-006 则说明：一个块完整回答必要子问，可以为 Grade 3，即使整个问题需要另一块补齐。

当前 keyword index 使用 `set` 遍历候选，Python `sort` 虽稳定地保留同分输入顺序，却不能保证此前的集合遍历跨进程一致。因此存在排名复现风险。这是 STATIC 推导，不是本次观察到的不稳定；后续检查归 T2002，不能靠评估层排序掩盖。

输入失败与检索失败要区别处理，具体 15 项 fail-fast 规则以契约第 8 节为准：

| 情形 | 契约要求与处理责任 |
|---|---|
| 未知 chunk_id、映射/版本冲突、缺失覆盖或审批、无效 split / evidence-family 泄漏 | 后续 Runner 的校验须阻止 official benchmark；数据问题返回构建/人工审阅处理，不静默跳过坏题 |
| answerable=true，却没有人工 grade ≥ 2 | 无效数据，即使有 Grade 1 和正 IDCG 也不成立；返回审阅，不能自动改成 Unanswerable |
| 有效 Answerable 有相关真值，但实际返回空列表 | 合法零分观察，保留在主聚合；后续检索分析解释原因，不能删除困难题 |
| 返回少于 K | 使用实际列表，缺失位置不贡献命中或 gain，不补造结果 |

Pilot 入库记录未发现入库异常；本文不虚构调试事故。页面追溯不足、单人偏差和潜在同分波动分别是现有机制限制、审阅限制与尚待测量风险。

### 8. 已有什么证据，分别证明到哪里？

| 行为 / 结论 | 来源与证据范围 | 时点、结果与本次边界 |
|---|---|---|
| 原创政策可经过现有摄入链并保持存储回读映射 | [Pilot README](../v2/evaluation/pilot-snapshot-01/README.md) 与 snapshot.json；进程内 API integration + REAL parser / embedding / Chroma，无 mock | 历史执行 2026-09-09：创建 201，四次上传均 200 / SUCCESS；另一进程回读 38 块 ID/正文/metadata 相等。本次只读证据，未重新入库；不是浏览器/TCP E2E、外部 provider LIVE 或 Retrieval Benchmark |
| 人工标签及其修改来源明确 | Reviewed 0.2；Human review provenance | 2026-09-09：六题，30 显式 judgments，Grade 3/2/1/0 = 7/7/3/13；类别 2 Direct Fact / 2 Paraphrase / 1 Distractor / 1 Multi-chunk。本次未改变标签 |
| 未列块可解释为 implicit Grade 0 | Coverage Gate；Human full-snapshot confirmation | 2026-09-10：6/6 APPROVED；仅绑定六题、Reviewed 0.2 与确切 corpus/snapshot。6 × 38 − 30 = 198 对是覆盖记账，不是检索指标，也未物化为显式标签 |
| 本 Task 契约与责任选择已人工关闭 | Contract 第 13–16 节、V2 SPEC 第 1.2 节、T2001 AC-2001-1/2/3 | 2026-09-10 Human Final Gate PASS，三项 AC SATISFIED，25 项 readiness READY，T2001 DONE / Contract 0.3 FROZEN；引用既有决定，不重新签发 Gate，也不等于 Phase 20 PASS |
| 当前身份、候选深度、score/filter/Top-K、metadata 机制 | ingest.py / qa.py / vector_store.py；本次 CODE / STATIC 阅读 | 核对代码机制，不宣称执行了查询或证明检索质量 |
| 既有检索机械行为覆盖 | [test_qa.py](../../backend/tests/test_qa.py) 中 `test_expanded_recall_is_truncated_to_top_k`、`test_relevance_filter_runs_before_top_k` 等；UNIT，替代输入/依赖 | Existing coverage / not independently rerun。本次阅读断言，不将已有测试当作新执行，更不当作真实语义 Benchmark |
| 指标实现、repeatability、正式 V1 Benchmark、latency/cost | T2002 / T2003 及另行获授权的数据构建 | DEFERRED 至对应后续工作；当前未实现/未测量。本次未运行 metrics、fixtures、Retriever、provider 或完整测试 suite |

注意历史状态：[Pilot README](../v2/evaluation/pilot-snapshot-01/README.md) 的“T2001 IN_PROGRESS / Ground Truth 尚未创建”与 snapshot.json 的 `ground_truth_created=false` 描述入库取证时点。之后的标签、Coverage Gate 和 Final Gate 独立记录后续事实。学习文档连接这些时点，不回写冻结证据。

### 9. 当前还缺什么，结论何时有效？

当前可得结论是：契约已冻结，真实小规模 Pilot 支持其身份与人工标注流程，人工完成本 Task 的最终批准。该结论只对已声明的版本与证据范围成立，不证明政策语料对真实企业查询的代表性，也不证明检索或生成质量。

正式 Benchmark Dataset 尚未交付。40 Answerable + 8 Unanswerable、Dev/Test 各 20+4 是质量目标，不是已存在的 48 条数据或必须凑足的配额。已有六题 Pilot 未自动通过正式 promotion；后续构建由 Human project owner 单独授权并批准来源、覆盖、实际 split/evidence families、必要审阅和最终版本。

指标与 Runner、排名重复性检查归 T2002；正式 Baseline 归 T2003，且必须先有真实版本化、Human-reviewed dataset、T2002 DONE、可用模型/索引/环境和明确执行授权。Core-Evidence Recall 只是未批准的候选诊断，不能在学习阶段添加实现。

下一步研究方向是：在后续授权满足时验证测量实现并采集保留 V1 行为的参考结果，再讨论 Candidate。当前没有启动该工作，也没有批准任何检索 Experiment。未来如果发现真实契约缺陷，应提交明确人工审阅的版本修订；不得为适配实现或结果而静默修改冻结定义。

### 10. 留给 Phase Learning Review 的整合素材

| 素材类型 | 后续应融入概念主线的内容 |
|---|---|
| Core concept | 评估真值与检索分数的区别；snapshot-bound identity；稀疏标签依赖覆盖审阅 |
| 关键 flow | 语料 → 冻结块 → 人工 judgment / coverage → 正式 promotion → 校验 → 最终检索列表 → 指标与逐题分析 |
| Engineering decision | 保留 V1 待测行为、显式披露 depth confounder；保留 binary mapping 同时说明证据信息损失 |
| Failure lesson | 通用流程不等于相关证据；未标注不等于零；坏数据不能伪装成合法检索零分 |
| 证据边界 | 真实入库、人工批准、源码核对、指标测试、Benchmark 分别回答不同问题 |

主动回忆问题（候选题，不附面试话术）：

1. 为什么随机 UUID 本身不能支持跨 re-ingestion 的真值复用？还要绑定哪些信息？
2. 人工确认 coverage 前后，“未列 chunk”的含义发生了什么变化？
3. 30 条显式判断加 198 对隐式 0，为什么不能描述为 228 条逐项人工标注？
4. `grade >= 2` 和 `MIN_RELEVANCE_SCORE = 0.30` 各在哪一步生效？
5. 不执行代码，只沿参数传递推导：Hybrid 请求 5 与 10 时，VectorStore 分别收到什么请求上限？为什么前缀不保证相同？
6. CQ-005 的 binary relevant set 为什么包含不直接给出 350 元的块？这使 Recall/MRR 少表达了什么？
7. 为什么“有效真值但空返回”可以计零，“Answerable 只有 Grade 1”却必须阻止运行？
8. 为什么稳定排序仍可能存在跨进程同分排名差异？评估层按 ID 排序会掩盖什么？
9. 同一政策事实的 Direct Fact 与 Paraphrase 分到不同 split，会产生什么泄漏？
10. 真实 Pilot、T2001 DONE 和 Contract FROZEN，分别还不能证明哪些后续条件？

### 本次学习文档交付边界

新增 Task 素材并最小同步学习索引；原契约、Pilot、源码、测试、SPEC/TASKS 和 Gate 历史保留，不删除历史或更新 ER/Interview。以下仅检查学习文档，不取代人工标签权威或运行验证。

- 自审：已按 Part A 核对十类内容，区分历史状态、当前机制、人工决定与未来工作；无原稿删减，无新标签或测量结果。
- 仓库检查（2026-09-10，Windows PowerShell，仓库根目录）：`git diff --check` 通过，exit 0；`git diff --cached --stat` 无输出，exit 0。Git 有既有 global ignore 读取权限及 LF/CRLF 提示，不是内容检查失败。
- 本地只读 Python 文档检查：两个学习文件共 79 个相对文件链接，缺失 0，exit 0。以写入前 SHA-256 为基准核对 185 个已有文档/应用/测试文件，只发现学习 README 改变；新增文件仅本文。12 个 `docs/v2/evaluation/` 文件（契约与 Pilot 材料）哈希全部保持一致。这是工作区静态完整性核对，不是重新验证 Pilot 运行结果。
- 独立 fresh-reader test：**PASS，附两项非阻断 clarity findings；两项已修订并定点自审复核**。来源为用户本轮提供的独立审阅报告：审阅未携带写作上下文，依据 Workflow V2 §A.5 与 Task Learning Pass 模板，确认主要解释、代码定位和证据边界可理解且与所查来源一致。此前 PENDING 是该报告到达前的状态。
  - Dev/Test 用途原先未解释：第 2 节现已补充 Dev 用于调参、Test 留出用于决策后的最终评估，并说明 evidence-family 隔离的原因。
  - nDCG 原先省略求和步骤：第 5 节现已明确前 K 个位置的折扣 gain 求和为 DCG@K，IDCG@K 在完整有效真值的理想排序上做相同计算。
  - 两项修订已对照冻结契约第 10、7.1 节复核。独立报告的原结论为 PASS with two non-blocking clarity findings；本次记录其结论并落实修订，不声称独立读者再次审阅过修改版。原报告记录 16 个学习文档链接可解析、`git diff --check` 通过；证据范围为 STATIC，未运行 ingestion、retrieval、metrics、providers 或 tests。
- T2002/T2003 未启动；未 commit、push，也未修改 Task/Gate 状态。
