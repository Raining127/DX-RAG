# Phase 20 — 检索评估基础：Task 学习素材

本文件积累 Task Learning Pass，供后续 Phase Learning Review 整合。当前包含检索评估数据集契约、独立评估 Runner 与完整真实 V1 基线的学习记录；T2001/T2002/T2003 已 DONE，尚未形成最终 Phase 教材、Engineering Review 或 Phase Gate 结论。各 Task 节保留其执行时点和证据边界。流程依据：[Workflow V2](templates/phase-learning-pass-workflow.md) 与 [学习模板 Part A](templates/phase-learning-template.md)。

当前读者检查状态（2026-09-16）：用户提供的独立 fresh-reader 报告对 T2002/T2003 及与 T2001 的衔接给出 **PASS WITH FINDINGS**，仅一项非阻断措辞歧义 F1；现已修订并定点自审，修改版尚未独立复审。下文 PENDING 保留为报告到达前的历史记录，完整处置见文末。

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

## 独立评估工具：把冻结的定义变成可检查的测量

Task reference：T2002；实现验证与首次 Learning Pass 补全日期均为 2026-09-11，但属于两次不同活动。2026-09-14 再次按 Part A 核对当前代码、冻结契约、测试断言及后续证据，补充报告阅读与 Python 机制；未重新执行实现验收。下面原有测试、调试和文档检查记录保留各自日期，后续状态见本节末尾。上面的 T2001 Learning Pass 和独立 reader 结论是历史材料，未改写；本节尚未接受独立 reader test。T2002 DONE，T2003 TODO，Phase 20 Gate 未启动。

### 为什么评估工具需要单独放置

原来只有测量契约，没有执行它的程序。[evaluation 包](../../backend/evaluation/__init__.py) 现在提供校验、计算、执行和报告。依赖方向是评估工具调用 V1，产品不导入评估工具，因此指标计算不会进入请求处理链。保留旧算法才能把以后观测到的差异归因于明确的实验变量。

这次研究问题是“计算是否忠实于人工批准协议，以及工具能否显示排名变化”，不是“检索质量是否足够好”。没有 Candidate，没有真实 Benchmark，也没有接受检索优化的决定。工具验收依靠手算和受控依赖，真实 Baseline 是后续工作。

### 新概念：先分清测量对象、计算和证据

| 概念 | 如何理解 | 本工具中的边界 |
|---|---|---|
| Runner（评估执行器） | 把输入校验、检索调用、计分与报告串起来的离线程序 | 独立于产品请求处理，不生成回答 |
| Fixture（受控测试样例） | 人为安排输入和预期结果，以便手算和断言 | 验证工具逻辑，不代表真实问题分布 |
| Recall / RR / MRR | Recall 问“应找回的相关块找到了多少”；RR 是首个相关结果名次的倒数；MRR 是多题 RR 的平均 | 都把 grade ≥ 2 视为相关，RR 在各 K 内截断 |
| DCG / IDCG / nDCG | DCG 对各名次的等级收益折扣求和；IDCG 是完整真值的理想排序得分；nDCG 是二者比值 | 保留 Grade 1 的弱相关收益，但不放宽 Answerable 校验 |
| Macro average（宏平均） | 先算每题分数，再对合格题目等权平均 | 一个问题拥有更多相关块，不会因此在聚合中获得更大权重 |
| Provenance（来源记录） | 记录输入、源码、配置与执行环境的身份，便于解释和重跑 | hash 能核对内容一致性，不能证明人工标签正确 |
| Hash seed / repeatability | Python 进程启动时的 hash seed 会影响字符串 set 的遍历顺序；重复性检查比较多轮观测 | 固定记录的 replay 稳定，不等于真实检索稳定 |

### 代码地图：谁负责哪一段

| File → Class / Function | 责任与重要行为 |
|---|---|
| [dataset.py](../../backend/evaluation/dataset.py) → `load_dataset` / `validate_dataset` | 解析 JSON 时拒绝重复键；全量校验版本、快照、审阅、真值与 split，返回按 chunk_id 索引的 inventory |
| [metrics.py](../../backend/evaluation/metrics.py) → `score_query` | 消费已验证真值与已去重排名，计算各 K 的 Recall、RR、nDCG；不负责检索或数据集校验 |
| [runner.py](../../backend/evaluation/runner.py) → `measure` / `aggregate` / `repeatability` | 每题请求一次深度 10，保留原始结果、去重诊断、分组均值及各轮差异 |
| [v1.py](../../backend/evaluation/v1.py) → `build_search` | 经公开 store 接口核对冻结快照，返回 V1 search callable 和实际配置；在调用时才导入产品依赖 |
| [__main__.py](../../backend/evaluation/__main__.py) → `main` / `worker` / `git_context` | 父进程调度独立 worker，收集输入与源码身份，最后以独占创建模式保存报告；fixture 分支不初始化真实检索依赖 |
| [test_evaluation.py](../../backend/tests/test_evaluation.py) → `EvaluationTests` | 使用 [hand-calculated.json](../../backend/tests/fixtures/evaluation/hand-calculated.json) 和替代依赖，检查手算、失败出口、进程与 adapter 边界 |

### 从输入到输出：有效性先于效果

```text
父进程：JSON → 全量校验 → 按 seed 启动独立 worker
worker：重新加载/校验 → V1 adapter 或 synthetic observations
                              ↓
                    每题一次 search(depth=10)
                              ↓
             原始 ID/score → 校验返回 → 首次出现去重 → 指标
                              ↓
                    每轮逐题/分组结果回到父进程
父进程：检查 dataset hash 一致 → 跨轮比较 → 新建 JSON 报告
失败出口：无效输入/返回或 worker 失败 → CLI exit 1，不生成成功聚合
```

[validate_dataset](../../backend/evaluation/dataset.py) 先检查全部 queries，随后才允许 search。坏 query 不能悄悄从均值分母消失。相反，真值有效但结果为空是合法低分，需要保留。函数抛出的 `ValueError` 类似前端在解析 API 数据时抛出的校验错误；它终止本次评估，不代表检索相关性为零。

两类 `APPROVED` 字段也不是相同权威：合成样例的 `SYNTHETIC_TEST` 只让单测表达 schema，正式数据要求 `Human project owner` 及真实决定来源。程序能验证必填字段、状态和格式，并要求 `decision_ref` 为非空字符串；不解析其引用，也不验证对应批准记录存在或人工确实完成审阅，更不能自己批准标签。

Python 里 `bool` 是 `int` 的子类，`isinstance(True, int)` 为真；因此 grade 和 chunk_index 用 `type(value) is int`，防止把 JSON `true` 当成等级 1。这与 TS 中 boolean 和 number 的类型分离不同。`families.setdefault(family, split)` 则记住该家族第一次出现的 split，再要求之后一致；它只能识别已填写的 family ID，不能发现人把同一事实误标成两个不同 family 的语义泄漏。

### 最小代码精读：集合用于匹配，列表保存排名

[score_query](../../backend/evaluation/metrics.py) 用 set 构造所有 `grade>=2` 的相关 IDs；集合求交适合统计命中，但没有排名语义。实际返回顺序始终保存在 list 中，RR 通过 `enumerate(prefix, 1)` 从 1 开始找第一个命中。这类似 JS 的数组遍历，显式起点避免把第一个名次误写成 0。IDCG 才对真值等级做理想排序；不能把这个排序拿来覆盖真实结果。

[measure](../../backend/evaluation/runner.py) 的 `seen` dict 保存每个 ID 第一次出现的原始位置。后续重复只追加诊断，结果列表不补足。因此原始 c,b,b,a,d 变成 c,b,a,d，第三个唯一结果是 a。合成真值 a=3,b=2,c=1 时，相关集合为 {a,b}，Recall@3=2/2，RR@3=1/2。Grade 1 的 c 不给 Recall 命中，却给 nDCG 一个 gain=1；这解释了两类指标为何可能得出不同的局部印象。

完整真值的理想 gain 序列为 7,3,1；实际前三项 gain 为 1,3,7，因此 nDCG@3 是 `(1+3/log2(3)+7/2)/(7+3/log2(3)+1/2)`。只返回 b 时，Recall 分母仍为 2，IDCG 仍包含未命中的 a 和 c，避免“只按找回来的内容给自己打分”。

主聚合对每题等权，不把命中数跨题相加后除以所有真值数。Dev/Test 分开，防止训练用途和留出用途混成一个数字；无合格样本的组使用 Python `None` → JSON `null`，表达没有均值而非均值为零。

把上面的机制对应到 `score_query` 的真实片段：

```python
prefix = ranked_ids[:k]
rank = next((i for i, cid in enumerate(prefix, 1) if cid in relevant), None)
```

`[:k]` 类似 JS 的 `slice(0, k)`，不足 K 项时直接取现有列表。括号内是生成器表达式：按需产出符合条件的名次；`next(..., None)` 取第一个，没找到就返回 `None`。因此无需创建所有命中名次的中间列表。它与 JS `findIndex` 的目的相近，但这里直接返回从 1 开始的名次，且未找到用 `None`，不是 `-1`。后面的 `1 / rank if rank else 0.0` 安全依赖于“合法名次从 1 开始”这个约定。

例如已有聚合测试在 Dev 中再添加一个有效但返回空列表的 Answerable：两题 Recall@3 为 1、0，均值为 0.5；RR@3 为 0.5、0，MRR@3 为 0.25。另有一个 Unanswerable 被排除，报告为 included=2、excluded=1、denominator=2。空检索降低均值；有效 Unanswerable 不进入该均值；无效输入则根本不能得到这份成功报告。

### 请求深度：为什么评估 @5 不等于生产 Top-K=5

根据 [冻结契约 §7.2](../v2/evaluation/retrieval-evaluation-dataset-contract.md)，`KS=(1,3,5,10)` 是同一次结果的计分截断点，`REQUEST_DEPTH=10` 才是调用参数。[V1 HybridRetriever](../../backend/app/services/qa.py) 将请求深度乘 2 交给 keyword/vector 分支，VectorRetriever 再乘 2 请求 store：评估路径为 10 → 20 → 40，生产默认路径为 5 → 10 → 20。

候选池大小参与最终融合，因此“请求 10 后取前 5”未必等于“独立请求 5”。报告把这一 execution difference 记为 confounder（影响解释的混杂因素）。`@10` 是更深检索诊断，不能称作 production Recall@10；`@1/@3/@5` 也必须说明来自深度 10。工具沿用 V1 的权重 0.3/0.7、阈值 0.30 和原始同分顺序，没有通过改算法消除这个差异。

### 为什么重复运行需要新进程

同一个进程中的 set 顺序通常保持一致，仅在循环里调用相同函数可能漏掉跨进程风险。[CLI](../../backend/evaluation/__main__.py) 用 `subprocess.run` 和独立 `PYTHONHASHSEED` 启动 worker，父进程保留每次原始结果及指标。seed 1/2/3 是可复现的探测条件，不是对所有运行稳定的证明。

实际 V1 Keyword/Hybrid 配合替代 store/vector 的同分测试中，三个进程分别返回 d,g,e,a,b,h,c,f；h,b,g,e,c,d,f,a；g,e,b,c,f,h,d,a。最终分数不变，rank 和指标变化。工程上拒绝在评估层按 chunk_id 排序来消除这个现象，因为那会评估一个改造过的算法。变化属于观测证据，工具仍可通过验收；是否及如何修复 V1 要等后续授权实验。

这里的三组顺序来自实现阶段的日志，本次只读核对。`repeatability` 按题比较排名位置、ID→score 映射和指标，指标容差为 0，保留各轮值而不跨轮求均值。`order_stable=false` 是成功记录的不稳定观察，不是 worker 执行失败。源码中的同分排序会保留上游顺序，keyword 的 set 遍历顺序才可能随进程变化；本测试没有把真实向量搜索带入因果链。

### 如何读一份报告，避免把成功保存当成全部稳定

先从 `scope`、`dataset`、`protocol` 和 `environment` 确认测量对象与条件，再到 `runs[*].per_query` 看原始结果、去重结果和该题指标，最后阅读 `aggregates` 与 `repeatability`。聚合里的 `query_category=null` 表示当前 split 的全部类别；它和 `metrics=null`（该组无合格题目）含义不同。只摘取某个均值会丢失分母、排除题目和运行条件。

`repeatability` 中三种变化独立报告。以下是从代码推导的阅读示例，不是新增运行观察：

| 变化 | 应怎样解释 |
|---|---|
| ID 顺序相同，但某个 ID 的 final_score 改变 | `order_stable` 仍可为 true，同时该题 `scores_changed=true`；指标只依赖排名和人工等级，因此可以不变 |
| 两个相同人工等级的结果交换位置 | `order_changed=true`，但 Recall/RR/nDCG 可以都不变；指标稳定不能反推完整排名稳定 |
| worker 正常完成并成功保存，发现名次变化 | CLI 仍可 exit 0；查看 `order_stable=false` 和 `affected_positions` 才能发现这次观测 |

因此顶层 `order_stable` 不是“分数、环境、数据与一切行为均稳定”的总开关。当前函数按各轮 `per_query` 的相同数组位置对齐查询，依赖 Runner 对同一输入保持 query 顺序；它不是能自动按 query_id 合并任意外部报告的通用比较器。这一边界来自 CODE，未在本次进行故障注入。

### 可追溯性和代价

[V1 adapter](../../backend/evaluation/v1.py) 通过公开 store 检查整个冻结 snapshot 的 IDs、文件映射与文本 hash 后调用 `hybrid_search`。这比只检查命中结果更早发现真值绑定错误，但每轮需要扫描全部 chunks。当前小规模评估接受这个成本，未测量 latency；如果语料扩大，不能在没有新证据时声称开销仍可忽略。

报告保存完整输入、实际源码 hash、Git dirty 状态、依赖版本和所有轮次。代码未提交时只写 HEAD 会错误标识 Runner；内容 hash 补充了这一缺口。公开 store 不返回 embedding，所以文本 hash 不等于向量/模型身份校验；冻结模型和索引的外部 provenance 仍不可省略。

### 设计理由：哪些有记录，哪些是推断

| 选择 | 理由来源与成本 |
|---|---|
| 全量校验后再 search；真值无效时不计零 | **Documented**：冻结契约 §7–8 明确要求。避免坏数据污染分母，代价是一题无效会阻止整次评估 |
| 首次去重、不补足、不另加 tie-breaker | **Documented**：冻结契约 §7.3/8.2。测量已存在的输出；代价是结果可能不足 K、同分波动继续可见 |
| 独立标准库包与独立进程 | **Documented**：[执行计划与协议](../v2/evaluation/t2002-runner.md) 记录隔离、无新增依赖与 seed 探测；代价是重复启动和每轮快照扫描 |
| `score_query` 与 search 分离 | **Inferred**：从函数边界与手算测试可推断，这样便于不依赖模型验证公式；不声称存在额外架构选型记录 |
| seed 默认 1/2/3 | **Documented**：协议将其限定为工具默认值；为何选择这三个具体数值的更深动机 **Unknown**，不能声称统计充分性 |

### 失败与易错边界：谁负责停止，谁负责保留

| 情况 | 当前行为与 owner | 证据性质 |
|---|---|---|
| Answerable 只有 Grade 1，或审阅/版本/映射不合法 | `validate_dataset` 抛 `ValueError`；`measure` 尚未调用 search | 现有 UNIT 断言；不是低质量检索观察 |
| 返回 snapshot 外 ID、NaN/boolean score 或超过深度 | `measure` 拒绝结果；CLI 报失败，不把它变成零分 | 现有 UNIT 断言 |
| 真值有效且 search 返回 `[]` | `score_query` 各 K 计零，`aggregate` 保留该题分母 | 现有 UNIT 断言 |
| `answerable=false` 且只有弱相关真值 | 保留逐题返回，`metrics=null`、原因 `unanswerable_weak_only`，主指标排除 | 现有 UNIT 断言；不自动生成新的人类可回答性判断 |
| V1 当前文本与冻结 hash 不同 | `build_search` 在检索前拒绝；完整 ID 集与 metadata 也由 adapter 检查 | 文本不匹配有 MOCKED 测试；其他核对机制为 CODE |
| worker 失败或各轮 dataset hash 不一致 | 父进程停止，不写成功报告；`main` 将所捕获错误映射为 exit 1 | CODE；本次不伪称做过故障注入 |
| 输出路径已存在 | `main` 拒绝覆盖；最终 `open("x")` 仍以独占方式创建 | 已有 CLI 测试覆盖重复执行；不是通用事务保证 |

写报告不是原子发布：父目录创建与 JSON 写入属于实际文件副作用；若磁盘在写入中失败，源码没有临时文件替换或清理半文件的逻辑。这是 **CODE 推导的限制，未观察到事故**。因此“不写成功聚合”不能被误读成“任何失败都绝无文件残留”。

### 验证证据与实际调试记录

[test_evaluation.py](../../backend/tests/test_evaluation.py) 的重要断言包括：去重后仍是 c,b,a,d；完整真值中未命中的相关块仍进入分母；每个非法 dataset 案例的 search `assert_not_called()`；三个 worker 的 PID 不同且 seeds 明确；adapter 接收到的请求深度均为 10。替代 store 的 V1 同分测试还断言 Runner 保留检索顺序、各 ID 分数不变，并让稳定性结论匹配实际观察，而不是硬编码必须出现波动。

下表为 **2026-09-11 实现阶段历史执行**，本次 Learning Pass 读取测试源码和现存日志核对，**未独立重跑**。环境据 [执行协议与 AC ledger](../v2/evaluation/t2002-runner.md) 为 Windows PowerShell、Python 3.14.6；命令工作目录为 `backend`。计数是 unittest test methods，不是 subTest 数或覆盖率。

| exact command | 历史结果与来源 | 范围与未证明内容 |
|---|---|---|
| `python -m unittest discover -s tests -p test_evaluation.py -v` | 8/8，日志 `tmp/t2002/evaluation-tests.txt` 末尾 `OK` | UNIT synthetic / MOCKED adapter；CLI 子进程到 JSON 的合成集成；实际 V1 Keyword/Hybrid + SUBSTITUTED store/vector。没有真实模型/Chroma 检索 |
| `python -m unittest discover -s tests -p test_qa.py -v` | 50/50，日志 `tmp/t2002/qa-regression.txt` 末尾 `OK` | 既有 UNIT/MOCKED 回归，不是业务质量 Benchmark |
| `python -m unittest discover -s tests -p test_query.py -v` | 10/10，日志 `tmp/t2002/query-regression.txt` 末尾 `OK` | 既有 Query API 受控依赖回归，不是 browser/TCP/provider E2E |
| `git diff v1.0.0 --stat -- backend/app frontend` | 执行协议记载无输出 | STATIC 产品差异检查，不证明真实检索效果 |

这些历史日志位于忽略目录，不保证其他 checkout 存在；持久化说明入口是执行协议。日志尾部显示通过计数，未单列 shell exit status，本次不补造历史退出码。已有 `tmp/t2002/fixture-report.json` 属于 synthetic artifact，不作为正式 Baseline。AC-2002-1～4 的既有结论仍归执行协议，本学习记录不重新发验收结论。

实际调试遇到 Windows 的 `Path` 默认反斜线：报告源码 hash key 与跨平台断言不符。改成 `.as_posix()` 后通过。另一个诊断易错点是“列表顺序变了”不等于“各 chunk 分数变了”；现分别比较 ranked IDs 和 ID→score 映射。

未执行真实 Chroma/模型检索、正式 Benchmark、生产质量或生成拒答评估；latency/cost 均未测量。未来数据构建与 Baseline 由后续单独授权工作承担。V1 同分样例的变化幅度不能推广到实际业务集。

### 尚未完成与后续条件

- **当前限制**：snapshot 的 ID/文本/映射检查不认证存储向量；全量扫描和新进程存在成本，写报告不保证原子性。
- **人工职责**：真实标注、coverage、evidence-family 语义和最终 dataset promotion 仍由 Human project owner 审阅；validator 不能代签。合成 fixture 不得通过改 reviewer 字段晋升为正式数据。
- **后续工作 owner**：正式数据构建需单独授权；T2003 在真实版本化且已审阅数据、模型/索引/环境就绪和独立授权后采集 Baseline。本次不创建数据或执行该任务。
- **Not yet measured**：业务语料的指标水平、同分波动频率、真实环境 repeatability、latency/cost；不得从八个测试推导质量改善或优化 Candidate 的接受决定。

### Phase consolidation 输入与读者检查

后续 Phase Review 应合并的概念：有效性与效果的分离、集合匹配与有序排名、宏平均分母、内容身份与版本标签、跨进程非确定性。候选自测：为什么有 Grade 1 gain 仍可能拒绝 Answerable？为何去重不补足？为何稳定的 replay 不能证明 V1 稳定？何时应拒绝“运行成功意味着排名稳定”的结论？

应保留的关键 flow 是“全量校验 → 保留实际顺序 → 逐题计分 → 分 split 聚合 → 逐轮诊断”；工程决定是尊重原始测量对象并披露请求深度差异；失败教训是把数据无效、合法低分、排名波动和文件写入失败分开。Windows 路径修正与最初观察到的同分顺序保留为历史，不改写成真实业务 Benchmark。

两道主动练习（不需运行检索或修改代码）：

1. 对真值 a=3,b=2,c=1 和原始结果 c,b,b,a,d，先写去重列表，再手算 Recall@1、RR@3、nDCG@3；解释为什么只返回 b 时 IDCG 不随之缩小。
2. 预测三种情况是否进入均值分母：有效 Answerable 返回空；Human-reviewed Unanswerable 返回弱相关块；Answerable 真值仅 Grade 1。再解释为什么对深度 10 的报告只取前 5 不能声称复现生产请求。

本次 loss audit 保留 T2001 正文与 reader 历史、T2002 手算与同分观察、Windows 修正、证据边界和 PENDING 状态；在既有 T2002 素材内补全概念、符号职责、失败出口、理由来源和自测，没有另建相互竞争的教程。学习 README 已指向本文并明确 reader PENDING，无需重复改索引。

本次文档验证（2026-09-11，仓库根目录 / Windows PowerShell）：`git diff --check` 与 `git diff --cached --check` 均 exit 0；只读 Python 内容检查 exit 0，确认本文 35 个本地文件链接可解析、代码围栏成对、T2001 正文逐字保留。相对于本轮起点捕获的 180 个现存文件 SHA-256，只有本文改变；没有新增非忽略文件。检查过程先修正了临时检查脚本的 PowerShell 中文管道匹配和 Git 路径列表过滤问题，再获得上述结果；这些不是产品缺陷。Git 的 global ignore 读取权限及 LF/CRLF 提示不影响内容检查结果。未重跑测试、provider、Pilot、Benchmark，未改 Task/SPEC/Gate、实现、测试或其他学习索引，未 commit/push。

本节已对照代码/测试自审；独立 fresh-reader test 为 **PENDING**，不继承上面 T2001 的 PASS。依据 [Workflow V2 §A.5](templates/phase-learning-pass-workflow.md)：“未执行则明确 pending，不能宣称完整 reader-test DoD 满足”。这项学习文档检查不替代运行验证，也不改变已验证的 T2002 AC。

### 2026-09-14 复核：后续证据与本 Task 的边界

上面“正式数据构建仍待进行、真实模型检索未执行”的记录描述 2026-09-11 的阶段边界。以下只读引用后来完成的工作，不追记为 T2002 原始验收能力，也不表示本次重新执行：

| 后续材料 | 已记录的事实 | 仍不能推出什么 |
|---|---|---|
| [正式数据集 1.0.0](../v2/evaluation/novatech-retrieval-benchmark-1.0.0/README.md) | 40 题（32A+8U）、1,520 项人工等级、38 块；20 个 family，Dev/Test 各 16A+4U；FROZEN / promotion APPROVED | 数据校验通过不等于测量已执行或有质量结论；Test 非盲测等局限继续保留 |
| [环境与索引预检](../v2/evaluation/t2003-preflight-0.1/README.md) | 已记录模型文件身份、离线加载和公开 38 块逻辑 inventory 匹配 | 不能认证所有存储向量或跨进程检索稳定性 |
| [最小向量冒烟](../v2/evaluation/t2003-smoke-0.1/README.md) | 一条非 Benchmark 中性文本，一次真实 encode 和一次 top_k=1 向量搜索成功 | 不覆盖 Hybrid、40 题指标、完整向量一致性或 latency/cost；持久化文件 hash 发生变化，原因未确认 |

当前需要继续区分三件事：数据经人工批准、环境在声明范围内可用、完整 Benchmark 获准执行。`validate_dataset` 校验 review 等结构，CLI 校验 mode/purpose，但代码没有强制检查 `benchmark_authorized` 字段；执行授权由项目工作流控制。这是现有工具边界，不能通过改冻结数据中的字段取得权限。T2003 仍 TODO，完整 Benchmark 未获授权。

补充主动练习：如果两轮返回完全相同的 ID 顺序、所有人工等级未变，只有 final_score 从 0.5 变成 0.6，预测 `order_stable`、`scores_changed` 和 `metrics_changed`，并说明各字段分别回答什么问题。

本轮 loss audit：原 T2001 正文、T2002 手算、历史测试数量、同分顺序、Windows 修正与原 reader PENDING 记录均保留；在原素材中补充代码精读和报告判读，仅在本小节说明后续状态。未改实现、测试、SPEC/TASKS、冻结数据、Gate、ER 或 Interview；未重跑测试、模型、检索或 Benchmark。证据类型为 CODE / STATIC 与已明确日期的历史记录，独立 fresh-reader test 仍 PENDING。

本轮文档检查（2026-09-14，Windows PowerShell，仓库根目录）：`git diff --check`、`git diff --cached --check` 均 exit 0；38 个本地文件链接全部可解析，6 个代码围栏成对。对照写入前 218 个 tracked/untracked 非忽略文件的 SHA-256，仅本文改变，无新增或删除文件。Git 的 LF/CRLF 提示不影响检查结果；未 commit/push。

## 真实检索基线：把工具正确与系统效果连接起来

Task reference：T2003；采集与首次素材日期：2026-09-14；Learning Pass 补全日期：2026-09-16。范围为冻结 NovaTech 40 题上的三轮真实 V1 Hybrid 检索。任务已经验收 DONE；完整结果与 AC 归属见 [基线报告](../v2/benchmarks/t2003-v1-baseline-1.0/README.md)。本次核对当前代码与保存的原始报告，并重新执行离线复核；没有重新检索。下文采集、测试和模型观察均指 2026-09-14 的历史执行，文末单列本轮检查；不重发 Phase Gate，也不覆盖前面 T2001/T2002 的历史记录。

### 新增能力与需要解决的问题

前两个任务已经说明“怎样评分”和“评分程序是否按公式工作”，但还没有回答现有检索系统在这套真实入库语料上表现怎样。本次把冻结问题、人工等级、实际本地模型与现有索引连接起来，交付可以逐题复核的起点。这里的“真实”指使用真实模型和持久化库执行；语料仍是合成政策，不能混称为真实企业业务分布。

新增的是采集脚本、证据和分析，产品及 Runner 没有修改。此后比较方案才有共同参考，能判断变化来自算法、输入变化还是运行波动。

### 先理解三种容易混淆的稳定性

- **内容身份稳定**：问题、人工等级、模型文件和 chunk 的 ID/正文/metadata 前后相同。这保证测量对象的可见部分没有换掉；不等于已认证全部存储向量。
- **排名稳定**：同一题各轮的有序 chunk ID 列表相同。即使内容身份相同，集合遍历、候选截断等仍可能影响顺序。
- **指标稳定**：各轮的 Recall/RR/nDCG 相同。两个同等级无关块交换名次，指标可以不变；相关块跨过 K 边界则可能改变指标。

三轮中 5 题排名变化，6 题 ID→score 映射变化，只有 Q014 一题指标变化。因此不能把一个 `order_stable` 字段当成所有层面的总开关。跨轮比较容差是 0；另一个离线脚本用 1e-12 复核独立公式的浮点计算，这两个容差服务不同问题。

### 代码怎样承载这次测量

| 文件与符号 | 职责 | 必须理解的行为 |
|---|---|---|
| [collect.py](../v2/benchmarks/t2003-v1-baseline-1.0/collect.py) → main / inventory | 记录授权、身份、检查与运行日志 | 新建目录拒绝覆盖；前后 inventory 在独立子进程中读取公开接口，退出后再进入下一阶段 |
| [evaluation/v1.py](../../backend/evaluation/v1.py) → build_search | 将冻结输入绑定当前存储，再返回现有 hybrid_search | 在任何题目检索前校验全部 ID、正文 hash 与文件映射；不重建 collection |
| [evaluation/__main__.py](../../backend/evaluation/__main__.py) → main / worker | 每个 hash seed 启动新的 Python 进程，再保存所有轮次 | `env={**os.environ, ...}` 给子进程传入覆盖项，类似 JS 对象展开合并；不修改磁盘 .env |
| [verify.py](../v2/benchmarks/t2003-v1-baseline-1.0/verify.py) → verify | 不检索，独立复算保存的指标并检查证据身份 | 回到完整人工真值计算分母和 IDCG；不是仅检查 JSON 能否打开 |

Python `subprocess.run(..., capture_output=True)` 等待子进程结束，返回退出码/stdout/stderr；它不是浏览器 fetch，也不表示服务端持续监听。模型的模块级单例只在一个 worker 内复用，新进程需要重新加载模型。运行时间包含测试与加载，不能直接除以题数冒充检索延迟。

### 数据、控制与副作用

```text
授权 + 冻结 release + 现有模型/索引
  → 校验文件 hash、配置、数据契约和产品版本
  → 工具/QA/API 回归 → 独立进程公开 inventory-before
  → Runner 父进程
      → seed 1 worker：校验全量快照 → 40 次 Hybrid → 逐题/分组指标
      → seed 2 worker：相同过程
      → seed 3 worker：相同过程
  → 原始报告 → inventory-after → 身份比较
  → 离线独立复算 → 分析/验收
```

采集脚本负责证据目录写入与错误日志；Runner 负责 fail-fast 和逐轮结果；产品负责实际检索。`try` 内被捕获的异常会尝试写 execution FAIL 并非零退出；已有目录在进入 `try` 前就拒绝覆盖，不承诺为这次拒绝写入 execution。成功返回空列表与执行异常依然不同：前者在有效 Answerable 上计零，后者不能伪装成正常低分。历史采集没有实际查询失败，不能虚构一次异常恢复经历。

精读 `collect.py` 的 `command`：它先保存 stdout/stderr，再把退出码追加到 record，最后 `assert process.returncode == 0`。因此正常捕获的子进程失败会留下排查线索；这不构成事务回滚。Runner 启动前保存的 `preconditions.json` 是前置检查记录，即使已经有 `report.json`，也还要看后置检查和 `execution.json` 是否 PASS。进程被强制终止、磁盘写入失败时，最终记录可能缺失或不完整；这是 CODE 推导的边界，并非本次观察到的事故。脚本大量使用 `assert`，复核和采集应使用记录中的普通 Python 命令，不能加会禁用断言的 `-O`。

Chroma 读取/搜索窗口内仍观察到三个持久化文件 hash 改变，而全部公开逻辑数据前后相同。内部维护与外部并发均不能仅凭这个现象排除；本次没有系统级锁，也没有逐位向量审计。读取接口是业务上不增删数据，不代表磁盘绝不写入。

### 从真实问题读懂指标

Q013 的问题是“跑完一趟客户行程，商家还没补开发票，我能一直等票齐了再报吗？”。它的唯一 Grade 3 证据在三轮中均为第 9 条。因此 @5 Recall/RR/nDCG 全为 0，@10 Recall=1、RR=1/9、nDCG≈0.30103。较深处找到了证据，并没有解决前五条缺失的问题。

Q025 是多条件的远程办公问题，@5 Recall=0.6、@10=0.8，而 RR 始终为 1。RR 回答“第一个相关结果有多靠前”，不能回答“所有需要的证据是否齐全”。Q020 首条 Grade 2、第三条 Grade 3，RR=1 但 nDCG@5≈0.73093，说明必须同时看二值相关与分级重要性。

八道不可回答题均检索到 Grade 0/1 片段，主指标保持 null 并单列；这只说明检索会放行主题相近材料。我们没有让 DeepSeek 回答，不能声称它正确拒答，也不能声称它发生幻觉。

### 沿一题走到总分：为什么小幅均值变化仍值得解释

在 [原始报告](../v2/benchmarks/t2003-v1-baseline-1.0/run-01/report.json) 的 `runs[*].per_query` 中按 `query_id=BC01-Q014` 定位，问题为“这笔钱已经刷公司卡付了，我还要报费用吗，能再打到我个人账户吗？”。读取 `matched_judgments` 可以把实际有序 IDs 映射回人工等级；以下来自保存的真实三轮结果，不是合成 fixture：

| 项目 | seed 1 / 3 | seed 2 |
|---|---|---|
| 前五条人工等级 | 3, 0, 2, 0, 0 | 3, 0, 0, 2, 0 |
| Recall@3 | 2/2 = 1 | 1/2 = 0.5 |
| RR@3 | 1 | 1 |
| Recall@5 | 1 | 1 |
| nDCG@5 | 0.9558305893 | 0.9324441895 |

这题完整真值的正 gain 为 7 和 3，故 `IDCG@5 = 7 + 3/log2(3)`。seed 1 的 `DCG@5 = 7 + 3/log2(4)`，seed 2 则为 `7 + 3/log2(5)`。第二块相关证据仍在前五条，所以 Recall@5 不动；但它位置更靠后，折扣更大，nDCG@5 下降。首条始终相关，RR 完全看不到这次变化。

Test 每轮有 16 道合格 Answerable，只有这题指标变化。因此 Test Recall@3 的变化量是 `(0.5 - 1)/16 = -0.03125`，即从约 0.885417 降至 0.854167；Test nDCG@5 下降约 `(0.9558305893 - 0.9324441895)/16 = 0.00146165`。聚合变化很小，不代表每题都同样稳定，也不意味着检索质量已经改善或恶化到具有统计意义。这里比较的是同一 Baseline 的运行波动，没有 Candidate。

这些均值对 query 等权，不对 family 等权。同一 family 的多道问题未必是独立样本，三个 hash seed 也不是三套独立抽样数据。因此三轮结果范围不能直接解释成置信区间，不能把 120 次 Hybrid 调用当成 120 个独立业务问题。

### 离线复核究竟重新证明了什么

`verify.py` 只读报告、冻结数据和源码文件，没有导入模型或调用检索。它不调用 Runner 的 `score_query`，而是从原始结果与完整真值重新写出公式，再比较保存的分数，降低“用同一段错误代码验证自己”的风险。独立公式依然不保证人工标注语义正确。

真实代码 `ids = list(dict.fromkeys(hit['chunk_id'] for hit in row['raw_results']))` 利用 Python dict 保留插入顺序的性质，留下每个 ID 的第一次出现，类似 JS 的 `[...new Set(ids)]`。这里不排序，因为顺序就是评分输入。随后 Unanswerable 走 `continue`，只检查排除状态；所以逐题重算值的数量是 `3 轮 × 32 道 Answerable × 4 个 K × 3 项指标 = 1,152`，不是把 40 题全部评分。

离线复核比较当前源码 hash 与采集时记录；如果将来代码已经变更，失败可能说明核对对象不再匹配，不能直接断言旧采集数学错误。可复核保存的结果、能在现有环境重新执行、能在另一台机器复现，是三种不同能力；本证据包没有携带可移植向量库，不能凭 verify PASS 宣称三者全部具备。

### 为什么保持测量对象不动

**Documented：** Contract 要求沿用深度 10、保持实际顺序，不为 Baseline 加次级排序或改权重。代价是报告必须承认不稳定，@5 也不能冒充独立生产 Top-K=5 的轨迹。好处是后续的比较对象身份明确。

**Inferred：** 真实 Q014 中某个无关块的 final_score 在一轮增加 0.024，超越相关块；这与 Keyword set 遍历、并列候选截断导致加分项进出相容。代码先分别截断候选再融合，所以不稳定可传播到最终非同分结果。Runner 没有记录全部分支分数，本次未做额外分支检索，不能把推断写成完整因果定位。

**Unknown：** 持久化文件为何变化、所有 seed 下波动范围、泛化到其他语料的效果、端到端回答质量及成本。这些都不是本次 Task 完成后自动得到的结论。

### 验证结果与边界

| 行为 | 本次证据/结果 | 不能证明什么 |
|---|---|---|
| 完整执行冻结问题 | 一次 CLI，3 个独立 worker，各 40 题；exit 0；真实 BGE/Chroma，120 次 Hybrid | 不是生成/浏览器/API 全链 E2E，不代表全部企业语料 |
| 指标与有效输入处理 | evaluation 8/8、QA 50/50、query 10/10；exit 0，日志在基线 run-01 | 含 synthetic/MOCKED/SUBSTITUTED 依赖，测试通过不等于业务指标优秀 |
| 保存结果的数学一致性 | 独立复算 1,152 个逐题指标值及分组聚合/分母通过；离线，无模型调用 | 不重新认证人工标注语义；不替代跨轮重复性分析 |
| 对象身份 | product/runner/model/release hash 前后一致，公开 38 块完整逻辑数据一致；V1 产品 diff 为空 | 未逐位认证存储向量，没有异机可移植索引保证 |
| 复现诊断 | 5 题排名变化、6 题 score map 变化、1 题指标变化如实保存 | 三轮不是统计充分性或确定性保证 |

具体命令、环境、退出码在 [execution.json](../v2/benchmarks/t2003-v1-baseline-1.0/run-01/execution.json)，质量数值在 [metrics.md](../v2/benchmarks/t2003-v1-baseline-1.0/metrics.md)。本次没有依赖安装、产品修复或 Benchmark 重跑；离线反复读报告不会重新查询 Test。latency/cost 明确 NOT_MEASURED。

### 尚未完成与 Phase 整合输入

当前未完成的是独立 Phase 20 Gate、最终 Phase 教材和工程复盘；后续范围由项目负责人决定，不能将 Task DONE 当作优化实验已获批准。现有本地索引继续保留，异机重建需要匹配身份或另行批准映射迁移。正式数据集是小样本合成政策，Test 非盲测、有共享证据块；此后不能根据这些 Test 失误反复调参。

Phase Review 应整合：测量对象身份、宏平均分母、排名和分数稳定性、检索深度混杂、首条命中与完整覆盖的差异、公开逻辑状态与持久化字节边界。工程复盘可讨论候选截断非确定性是否需要新协议下的修复，以及建立可移植索引证据的成本；这些不是本次实现决定。

候选自测：为什么 Dev MRR=1 但 Recall@5<1？为什么 Q014 在最终没有同分时仍可能受上游并列候选影响？为什么 8 道不可回答题都有结果不能推出 8 次幻觉？为什么复制模型文件还不能保证复制了基线？为什么精确复现失败仍可满足“检查并报告复现情况”的验收条件？

本节已按真实代码、原始证据和模板自审；独立 fresh-reader test 为 PENDING，不声称 reader-test DoD 完成，也不继承 T2001 的读者结论。Task AC 的完成与学习读者检查分开记账。

### 2026-09-16 Learning Pass 复核记录

本轮在仓库根目录执行 `python docs/v2/benchmarks/t2003-v1-baseline-1.0/verify.py`，exit 0、PASS：重新复算 1,152 个逐题指标值，并检查聚合、已实现的变化诊断与文件身份。证据为 OFFLINE / STATIC；没有 encode、检索、回归测试重跑或重新采集，未覆盖原 verification.json。原采集的 8/50/10 项测试结果和 REAL 模型/Chroma 证据仍归 2026-09-14。

本轮保留原始手算、难点、设计理由、未测量项与 AC/reader 历史，在现有素材内补充真实逐题到聚合的流程、独立公式机制、失败记录边界和主动练习；没有创建另一份教程，也没有改实现、冻结证据、SPEC/TASKS、Gate、ER 或 Interview。学习索引已有 T2003 入口，无需重复修改。独立 reader test 仍为 PENDING。

两道主动练习（只读报告或手算）：

1. 若 Q014 的 Grade 2 结果从第 4 移到第 6，预测 Recall@3、Recall@5、RR@5、nDCG@5 哪些改变，并算出 Test Recall@5 的变化量。不要据此修改标签或检索配置。
2. 假设报告已保存，但采集进程在 inventory-after 前被终止：哪些文件能提供证据，哪些验收结论还不能成立？为什么离线复算指标正确也不能补出缺失的后置身份核对？

文档检查：`git diff --check` 与 `git diff --cached --check` 通过；46 个本地文件链接可解析，8 个代码围栏成对。相对写入前 243 个 tracked/untracked 非忽略文件的 SHA-256，仅本文改变，无新增或删除文件。未 commit/push；既有工作区修改保留。

### 2026-09-16 独立 fresh-reader 报告与 F1 处置

**来源与结论：** 用户在本会话提供的独立审阅报告，结论为 **PASS WITH FINDINGS**。报告说明先在无实现上下文下阅读学习材料，再核对源码与证据；按 Task Learning Pass 标准审阅 T2002/T2003 及与 T2001 的衔接，确认概念、职责、数据流、代码定位、手算与主动练习基本充分。未发现公式、案例数值或聚合错误，不要求本文提前成为最终 Phase 教材。

**唯一 finding F1（非阻断表达歧义）：** 原句“程序能验证字段与引用存在”可能使读者误认为 validator 已检查批准记录可定位。现已改为明确 `decision_ref` 仅需非空字符串，不解析引用、不验证批准记录存在或人工实际审阅。修订后对照 `dataset.py` 的 `strings` / `review` 定点自审，确认与实现一致；没有修改实现。处置状态为 **已修订 / 自审复核，尚未独立复审修改版**，不将原报告升级为无 findings 的 PASS。

**独立报告的验证范围：** 报告记载执行 `python -B docs/v2/benchmarks/t2003-v1-baseline-1.0/verify.py`，exit 0、PASS，离线复算 1,152 个逐题指标值及分组聚合；内存脚本核对案例、分母、变化量与符号；46 个正文链接有效，Phase 20 索引入口有效，两个 diff 检查均 exit 0。以上为引用独立报告的执行记录，不冒充本次修订重新执行。报告没有运行模型、encode、检索、Benchmark、采集脚本或回归测试。

独立读者认为篇首状态、各节日期和后续记录足以解释历史 TODO/未授权文字，未将保留历史列为 finding；因此保留原文，不新增状态改写。T2001 原 reader 结论也保持不变。本次独立 reader-test 已执行，原 PENDING 已被本报告承接；Task AC、Phase Gate、最终 Phase 教材验收仍各自独立。
