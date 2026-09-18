# Phase 20 Engineering Review — 评估基础的可信度、成本与适用边界

## 1. Review Purpose — 这套测量基础能支撑什么判断？

本复盘评估数据契约、离线 Runner 和旧检索基线的工程选择：在什么前提下值得保留、成本由谁承担、失败时哪些证据仍可信，以及何时必须重审设计。评审日期为 **2026-09-18**，依据当前实现、已建立的独立 Gate、已整合的 [Technical Learning](../phase-20-evaluation-foundation.md) 和保存的原始基线。

本文按 [Engineering Review Template V2](../templates/phase-engineering-review-template.md) 与 [Workflow V2](../templates/phase-learning-pass-workflow.md) 编写。机制与手算归 Learning；验收归 Gate；本次工程判断不重发 Gate、不修改契约，也不批准新的实验或生产策略。文中 Documented 表示有契约/批准记录，Inferred 表示本次工程推理，Unknown 表示尚无足够证据。

## 2. Executive Engineering Summary — 当前设计为什么仍合理？

这里的工程问题是：在优化检索之前，怎样避免“测量对象变了、真值变了、评分口径变了”却把数字变化归因于算法。当前设计把人工批准的数据、不可静默变更的指标、未修改的 V1 检索和可复核报告拆开，已经形成一个**范围有限但可追溯的本地参考**。

六个选择构成这个基础：

1. **评估调用旧产品，不进入生产请求链。** 独立测量包避免把评分与产品行为耦合，旧权重、阈值和顺序保持可比较。
2. **以冻结快照与人工批准绑定真值。** UUID 精确匹配、内容哈希和审批记录降低错配风险；程序不假装能认证人工判断。
3. **固定指标及深度，保留解释边界。** 三种指标互补，宏平均和分母透明；深度 10 的 @5 不冒充独立生产请求 5。
4. **无效数据整体失败，合法低分原样保留。** 保护分母与评估资格，代价是批次可能因单项问题停止。
5. **跨进程重复暴露不稳定，而非偷偷修复待测算法。** 保留全部轮次为后续比较提供噪声参照，但三轮不等于充分统计设计。
6. **用文件证据和前后核对保持轻量。** 可以离线复算与追查身份，尚不是事务性、可移植、抗并发的实验平台。

最大代价是：我们保留了 V1 的非确定性和现有索引依赖，同时接受小样本、单人审阅、共享证据与非盲测。最值得防范的风险是**错误使用这些证据**：拿小幅单轮改善作决策、把检索当生成质量、把哈希一致当语义正确、把本地可重跑当异机复现。

工程总判断为 **KEEP WITH KNOWN LIMIT**。适用前提是原始数据/模型/索引继续保留、执行期间遵守无并发修改约定、所有比较披露相同深度和波动、不用 Test 反复调参。若需要跨机协作、无人值守长任务、统计上可信的小幅比较或真实业务泛化，应先重审相应协议与证据设施。此判断不意味着现在开始这些工作。

## 3. Decision Map — 哪些取舍决定了架构？

| Engineering Question | Decision | Benefit | Cost | Revisit When |
|---|---|---|---|---|
| 如何保证测的是已发布行为？ | 独立 evaluation 包调用未改 V1 | 减少测量引入的产品变化；源码身份可核对 | 继承旧排序与候选截断问题 | 实验需改算法或服务路径；必须保留旧参考并另批范围 |
| 真值怎样与实际块对应？ | snapshot 内 UUID + 文本/映射 + Human approval | 精确追溯，防止换库误用标签 | 重摄入/跨机迁移昂贵；人工审阅仍是瓶颈 | 语料更新、模型/索引迁移或业务代表性要求出现 |
| 哪种分数可以解释结果？ | grade≥2 + graded nDCG；分 split/category 宏平均；深度 10 | 分母与收益定义明确，可手算 | 二值信息损失；排除 U；不等价生产 top_k=5 | 要评回答/拒答、family 权重或真实生产轨迹 |
| 如何防止坏数据污染均值？ | 全量 fail-fast，不静默跳题 | 坏标签和真实低分不混淆 | 一个坏项阻止整批；审批真实性仍靠治理 | 数据来源/用户扩大，需认证、批次隔离或机器化审阅链 |
| 如何处理重复性问题？ | seeds 1/2/3 新进程，精确比较且保留原序 | 暴露排名、分数及指标不同层次变化 | 重复加载和检索；无统计置信保证 | 改善与噪声相当，或需因果定位/确定性保证 |
| 如何保存和重验基线？ | JSON、日志、manifest、前后身份检查 | 少依赖、离线可审计、拒绝覆盖旧输出 | 本地索引依赖；部分失败、并发和文件写入非事务 | 共享运行、长任务、跨机或自动化审计需求 |

收益中的“减少风险、便于审计”是结构性判断，不是测得的性能或质量提升。

## 4. Architecture / Ownership Context — 谁拥有状态和责任？

```text
Human project owner ──批准──> 冻结 corpus / snapshot / judgments / split
                                   │ durable input truth
                                   ▼
CLI 父进程 ──逐轮子进程──> validator → V1 adapter → 既有 Hybrid
      │                              │              │
      │                              │              ├─进程内 Keyword 派生索引
      │                              │              └─本地 BGE / 持久化 Chroma
      ▼                              ▼
report.json / execution / logs / manifests  ← 实际观察与身份记录
      │ durable measurement evidence
      ▼
offline verify / 独立审查 → 解释和决策，不反向修改真值
```

| 状态 / 责任 | Owner | 写入、失效与恢复边界 |
|---|---|---|
| 人工真值、版本、split 与覆盖批准 | Human project owner；构建工具记录 | 变更需新的明确审阅；LLM/validator 不能自行批准 |
| 原始政策与公开快照映射 | 冻结数据维护者 | 不能为适配结果修改；新摄入身份不能自动继承旧 judgment |
| 向量与持久化 collection | 既有摄入/VectorStore；运行者负责冻结条件 | 评估不调用增删改业务接口，但客户端可能修改文件；无评估级 rollback |
| Keyword 索引 | KeywordRetriever 进程内派生缓存 | 从 store 构建；产品有 invalidation 机制；新 worker 避免跨轮复用缓存，不阻止外部并发写 |
| 多轮结果与报告 | CLI/collect | 父进程收集；新输出路径，独占创建；中断可能留下不完整证据，没有通用 resume |
| 指标与汇总解释 | metrics/runner 与审阅者 | 可由冻结输入和原始返回复算；不能以新公式静默覆盖旧口径 |
| 下一次实验及生产采用 | 后续获批协议/任务与人工决策 | 本文提出触发条件，不分配新 Task、不选择 Candidate |

源码、数据和模型哈希是身份校验，不是互斥锁、事务、签名认证或语义证明。以下决策必须在这个责任分工下理解。

## 5. ADRs — 六项现有选择何时不再合适？

本节的 **ER20-D1～D6 是工程复盘内的回顾性坐标**，不是新增、获批的 V2 产品 ADR。没有发现需迁移的既有 Phase 20 正式 ADR；[V2 ADR 入口](../../v2/adr/README.md)仍保留未来受控实验后的人工决策职责。已有 CD-1～CD-4、SC01/SC02 与人工批准原文不改。

### ER20-D1 — 先保留待测行为，再隔离测量工具

**Engineering Problem / Constraints。** 基线如果一边采集一边修排序、阈值或权重，就失去“已发布 V1”的含义。EVAL-03 明确保留 0.3/0.7、0.30、既有 pipeline；Phase 20 不授权 Candidate、生成评估或生产集成。

**Alternatives。** 实际获批选择是保留 V1；把评估嵌进 API、另写一份“等价”Retriever、先加 deterministic tie-breaker，是本次教育对照，未做比较实验，也未被证明优劣。未来确定性实现可以成为受控变更，不能伪装成原基线。

**Chosen Design。** `backend/evaluation/` 独立于产品，通过公开 VectorStore 接口核对数据，直接构造现有 Keyword/Vector/Hybrid。没有拷贝一套融合算法，产品不导入评估包。源码 hash 和 tag 差异记录待测实现。

**Why This Fits / Trade-offs。** Documented：先测量再改变。Inferred：复用同一实现减少“双实现行为漂移”的维护成本；相应代价是评估依赖当前产品结构、Python 环境和本地依赖，也完整继承候选截断/排序问题。这里测到的是直接 Hybrid 路径，没有覆盖 API、context 截断和生成。因此产品使用体验仍需别的证据。

**Failure Modes。** STATIC：如果将来改了生产实现却仍把新的结果称为旧 V1，版本号相同也不足以保护比较；hash 只能帮助发现。OBSERVED：旧算法跨进程结果有变化。不得用评估层重排来“消除噪声”，那改变了测量对象。

**When This Stops Being Good。** 前提是研究问题针对最终 Hybrid 检索。若要比较服务侧延迟/错误路径或回答质量，需要另行批准相应执行入口；若要改候选策略，需保留旧实现与旧证据，并明确新变量、同条件参考及回归范围。

**Evidence / Verdict。** [v1.py](../../../backend/evaluation/v1.py)、[qa.py](../../../backend/app/services/qa.py) 为当前 STATIC；[Gate](../../verification/PHASE-20-GATE-REVIEW.md)记录产品与 V1 无差异及机械回归。真实基线仅支持当前指定数据路径。**KEEP**；完整服务/生成评估为 **FUTURE CANDIDATE**，不是这里的缺陷修复。

### ER20-D2 — 精确身份优先于随意重建，人工权威优先于自动标签

**Engineering Problem / Constraints。** 相关性判断必须指向确切块，而不能指向看似相同的文件；Ground Truth 必须经 Human review。Contract §3、§5、§10–12 定义 snapshot、coverage 和 family；冻结后不得按结果静默修改。

**Alternatives。** 实际记录包括 CD-1 稀疏判断需完整覆盖确认、CD-3 单人最终审阅、CD-4 质量优先及 family 隔离；正式版本选择完整 40×38 矩阵，接受 SC01/SC02 的 32A+8U。以内容哈希作主键、任意重摄入、随机 query split、全自动 LLM 标签、多标注员一致性评估，是教育对照或未来候选，没有实测比较结果。

**Chosen Design。** 以 corpus/snapshot + chunk_id 绑定真值，正文 hash 和 file_id/name/index 支持核对；人工审题、最终等级、覆盖、分组和 promotion 独立留证。四份原创政策、38 块、40 题、20 families 为本版确切范围。Pilot 六题不自动晋升正式题集。

**Why This Fits / Trade-offs。** Documented：使用可公开分发材料，不为凑数制造重复证据，接受单人偏差。Inferred：小型全量审阅使边界可检查，精确 UUID 有利于发现错库。代价由维护者承担：重摄入生成新 UUID 后需重映射、审阅和版本化；稀疏表示只能省记录，不能省掉 full-snapshot review。模型和索引不随证据包发布，异机重现还需要同一现存状态或获批迁移方案。

**Failure Modes。** TEST-COVERED：结构性的 ID/映射冲突、family 跨 split 可阻止。REASONED：不同 family ID 仍可能语义重叠，非空 approval 引用仍可能没有真实审批；validator 不能解决。OBSERVED/DOCUMENTED：7 个共享正证据块、2 条跨侧补充规则和非盲测局限已接受；这不等于检测到未批准的核心事实跨侧，也不等于独立测试分布。

**When This Stops Being Good。** 当比较需要推广到真实业务、多组织政策或更大语料时，当前样本代表性不足；当协作者必须在另一台机器重跑时，单机 UUID/索引依赖变成具体障碍；当争议、漏标复查和审阅成本支配迭代时，应批准更明确的 sampling/coverage、独立标注或映射迁移协议。不能从本次结果直接推导新标注方式正确。

**Evidence / Verdict。** [Contract](../../v2/evaluation/retrieval-evaluation-dataset-contract.md)、[正式数据](../../v2/evaluation/novatech-retrieval-benchmark-1.0.0/dataset.json)、[split 决定](../../v2/evaluation/novatech-retrieval-benchmark-1.0.0/evidence/split-decision.md)、[规模/语料决定](../../v2/evaluation/novatech-retrieval-benchmark-1.0.0/evidence/size-corpus-decision.md)。本次读取来源，不认证人工真实履行过程。**KEEP WITH KNOWN LIMIT**。

### ER20-D3 — 固定口径换取可比较性，接受指标覆盖范围有限

**Engineering Problem / Constraints。** 一个可调整分母、任意 K 请求或混合 Answerable/Unanswerable 的分数，难以解释。Contract §6–9 冻结 binary mapping、gain、宏平均、空结果、重复和深度。

**Alternatives。** 现有选择是 Recall/MRR grade≥2、nDCG 完整等级，按题宏平均；每题请求 10，再取 1/3/5/10 前缀。Grade-3/Core-Evidence Recall 是历史未批准的候选诊断。按 family 加权、将 U 纳入另一个成功率、分别请求各 K、使用生产深度，是教育对照/未来协议选项，不是已执行而败选的方案。

**Chosen Design / Why This Fits。** Documented：完整真值决定 Recall 分母与 IDCG，Unanswerable 主指标为 null，Dev/Test 和类别分开，空有效组不伪造均值。Inferred：固定定义能让工具错误与系统低分分离；多指标和逐题原始观察比单一均值更能暴露不同失败。

**Trade-offs。** 二值 Recall/MRR 忽略 2 与 3 的重要性差别；query 宏平均让题数多的 family 贡献更大，不是独立事实等权。U 被排除保护主相关性定义，却必须单列误召回，不能让“高均值”遮住拒答需求。深度 10 放大候选池，不能把 @5 写成独立生产 Top-K=5。比较者承担解释成本。

**Failure Modes / Evidence。** 原始 Q013 唯一 Grade 3 三轮 rank 9，@5 全零；Q025 @5 Recall=0.6、RR=1；Q032 为 0.5、RR=1。八道 U 均有返回但没有生成测量。这些是 2026-09-14 REAL 检索观察，本次从 [原始报告](../../v2/benchmarks/t2003-v1-baseline-1.0/run-01/report.json)核对；不是新查询，也不推出幻觉率。[metrics.py](../../../backend/evaluation/metrics.py)与 aggregate 的当前 STATIC 解释计分责任。

**When This Stops Being Good。** 若决策目标变为核心答案是否齐全、不同 family 的等权效果、正确拒答或生产请求轨迹，当前指标不完全回答问题；需先批准新 measurement objective、ground truth/分母和版本，保留旧指标作历史参考。不得在看到 Test 结果后悄悄改定义。

**Current Verdict：KEEP WITH KNOWN LIMIT。** 不因低分改标签，不因“其他指标更漂亮”替换冻结主指标。

### ER20-D4 — 全量 fail-fast 保护统计资格，承认结构校验的信任边界

**Engineering Problem / Constraints。** 无效数据如果被记零或删除，会同时损害解释和分母。冻结契约要求审阅完整、映射一致、Answerable 有 grade≥2；业务权限不在 validator 的能力范围。

**Chosen Design。** `load_dataset/validate_dataset` 在所有检索之前检查整份输入；`measure` 校验返回类型、深度、已知 ID 和有限分数。合法空列表计零；坏输入/无效观察失败。fixture purpose 和 SYNTHETIC_TEST role 与 benchmark/Human role 区分。

**Alternatives。** 跳过坏题、把无效项算零是与契约不符的对照，不可直接采用。逐题隔离失败、经过认证的审批引用、正式 JSON schema/外部 registry 是未来增强类别，当前未引入依赖或认证服务。没有证据表明引入框架本身能保证标签语义正确。

**Why This Fits / Trade-offs。** Documented：不让坏数据成为检索低分。Inferred：小规模输入整体预检简单且错误归属清楚；损失是任何坏题都会阻止整批，需修正数据并重新启动。`review` 检查字段、日期、角色与 APPROVED，但只要求 decision_ref 非空；CLI 不执行人工批准认证，也不自动读取 SPEC 的后续执行授权。冻结数据的 benchmark_authorized=false 是发布时历史状态，授权由后续 SPEC §1.10 与流程控制承担，不能靠字段字面值重写历史。

**Failure Modes。** 测试断言 search 未调用，证明的是拒绝时序。恶意或错误填满字段仍可能结构合法；不同 family ID 的语义重复也可能漏过。这是已说明的 trust boundary，不是“所有输入均可靠”的证明。人工审批、数据检查和运行授权不能被一次 validator PASS 合并。

**When This Stops Being Good。** 当输入来自不受信任来源、多维护者审批或自动化调度需要强制权限时，非空引用及人工操作约定不够；应明确授权载体、内容绑定和审批验证责任。若批量失败成本实际过高，需要批准失败隔离与分母规则，而不是实现者自行 skip。

**Evidence / Verdict。** [dataset.py](../../../backend/evaluation/dataset.py)、[test_evaluation.py](../../../backend/tests/test_evaluation.py) 的 fail-fast 与 adapter 测试；历史/Gate 执行边界见 §9，本次未重跑。**KEEP WITH KNOWN LIMIT**；审批真实性仍归 Human/治理，不声称认证系统已存在。

### ER20-D5 — 观察非确定性，而不是让基线为了验收变得确定

**Engineering Problem / Constraints。** 旧 Keyword 候选涉及 set 遍历，稳定 sort 不能保证跨进程输入顺序相同。冻结协议要求消费实际返回，不新增 secondary sort。

**Chosen Design。** CLI 用三个新进程 seeds 1/2/3；每轮相同数据，保存 order、score map 和 metrics，容差 0 精确诊断，不跨轮均值掩盖差异。原始 PID 为 18996/30516/33688。

**Alternatives。** 只跑一次无法显示该风险；同一进程重跑不等价探测跨进程 set 顺序；排序稳定化或固定 seed 可改变观察条件，不能当作已发布基线确定性的证据。这些是分析对照，未做候选优劣实验。更多重复、配对比较和不确定性分析是后续可批准的方法，本文不定次数或显著性阈值。

**Why This Fits / Trade-offs。** Documented：暴露并保留波动。Inferred：新进程隔离 Keyword 类级缓存，有利于观察启动条件差异；每个 worker 重新加载/校验并检索，承担额外资源和时间成本，未测 latency/cost。固定三轮是当前执行协议，不是抽样充分性的证明。

**Failure Modes / Evidence。** 当前原始证据有 5 题 order、6 题 score map、1 题 metrics 变化；Q014 的 Grade 2 块由 rank 3 到 4，使 Test Recall@3 相差 0.03125，Test nDCG@5 为 0.894758～0.896220。不是仅最终同分换位。Inferred：上游并列候选跨截断边界改变 keyword 加分与此相容；Unknown：未保存两路完整候选，不能唯一归因。score map 变化含返回 ID 集变化，不能一律叫向量漂移。

**When This Stops Being Good。** 当 Candidate 改善量与现有波动相当，或结论依赖某一轮最好值时，三轮描述性检查不足以支撑采用决策。应先批准更充分的比较设计、配对单位和诊断采集；同 family 相关性需考虑。修复排序如获授权也是新版本的受控变更，旧基线需保留。

**Evidence / Verdict。** [repeatability](../../../backend/evaluation/runner.py)、[CLI](../../../backend/evaluation/__main__.py)、[原始报告](../../v2/benchmarks/t2003-v1-baseline-1.0/run-01/report.json)。本次离线复核通过，不重新搜索。**KEEP WITH KNOWN LIMIT**；统计推断与原因定位为 **REVISIT WHEN 决策依赖小差异或稳定性**。

### ER20-D6 — 文件证据适合首个本地基线，但不是事务性实验平台

**Engineering Problem / Constraints。** 基线必须能追溯实现、数据、环境和失败，不能只给汇总数字；不能为测量 reset 工作区、移动 tag 或重建索引。

**Chosen Design。** CLI 以 x 模式写新的 report；collect 新建独立目录，记录命令和 stdout/stderr、前后 source/model/release/public inventory/persistence hashes；report 内嵌数据和包版本。manifest 覆盖包内其余 24 个文件，离线 verify 独立公式复算及身份核对。数据集/模型/索引仍为本地资源。

**Alternatives。** 只保存均值会损失错误定位；覆盖固定 report 会丢历史。事务式运行目录、逐 worker checkpoint、经过校验的索引导出、环境锁定/可移植包、内容寻址证据库是未来方案类别，当前没有建设或比较。无需为小基线先引入通用实验平台，并不意味着文件方案永远足够。

**Why This Fits / Trade-offs。** Documented：完整原始证据、失败保留、新路径不覆盖。Inferred：JSON 和已有标准库降低新增依赖及维护面，报告便于直接审查。代价是 report 当前有 2,084,161 字节（本次文件大小观察，不是性能测量）；大量正文、内嵌数据和多轮输出随规模增长。包版本清单不是锁文件，路径不是可移植索引；哈希绑定也不是防篡改签名。

**Failure Modes。** STATIC：父进程将成功 worker 结果保留在内存，全部完成后才保存报告；后续 worker 失败可能丢失之前轮次的独立结果。collect 可保留命令日志与 FAIL execution，但不等于逐 worker checkpoint；硬中断或写盘失败可能没有完整 execution。x 模式防覆盖，不保证 JSON 写入原子完成；没有临时文件原子发布、全局 writer lock 或自动 rollback。`subprocess.run` 未配置 timeout，是无人值守场景的潜在等待风险，非本次观察到的 hang。采集/verify 的许多审计条件用 assert；运行时不能使用 Python `-O`/优化模式，否则断言可被禁用。历史命令为普通 Python，本轮为 `-B`，不改变该边界。

**一致性证据。** OBSERVED：真实采集窗口内 sqlite3、data_level0.bin、length.bin 哈希变化，38 块公开逻辑数据相同；原因 Unknown。Gate 后续核对 29 模型文件和 45 索引文件与采集结束状态相同，不能倒推采集期间绝无变化或向量语义正确。没有排他锁，起终点一致不能排除瞬时外部写入。

**When This Stops Being Good。** 当跨机复现第一次成为要求，先设计同一索引/模型的可核对迁移；当长任务中断重跑代价显著，考虑经批准的 checkpoint 与完整性发布；当自动化或多运行者共享库时，须重新界定 writer 隔离、超时、状态机及失败责任。未来若把脚本作为 CI 强验收入口，应先将优化模式和断言风险纳入明确执行约束或获批工具加固。没有在本轮实现这些机制。

**Evidence / Verdict。** [collect.py](../../v2/benchmarks/t2003-v1-baseline-1.0/collect.py)、[verify.py](../../v2/benchmarks/t2003-v1-baseline-1.0/verify.py)、[execution](../../v2/benchmarks/t2003-v1-baseline-1.0/run-01/execution.json)。**KEEP WITH KNOWN LIMIT**；可恢复性、执行稳健性与长期归档列为有条件处理的 **TECHNICAL DEBT**，不是当前 Gate 的新阻断项。

## 6. Failure & Consistency — 最脆弱的是哪些责任接缝？

| Failure / Risk | Cause / 性质 | Current Protection | Residual Risk | Upgrade Direction / Owner |
|---|---|---|---|---|
| 真值错配到新索引 | 测试覆盖 + 重摄入机制推理 | snapshot/ID/正文/文件映射校验 | 不认证所有存储向量；同名不能迁移身份 | 迁移发生前，由数据/索引维护者批准映射与复验 |
| 标签结构合法但语义或批准不实 | Reasoned trust risk | 全量 schema/coverage 状态校验、人工 promotion | 不解析 decision_ref，不自动识别语义同 family | 输入协作范围扩大时明确审批认证和独立复核 |
| Keyword 与向量分支观察不同状态 | Reasoned concurrency risk | 新进程、禁止并发修改约定、前后 inventory | 初始快照检查到查询有时间窗；进程内 keyword 缓存不感知外部更新 | 共享执行前设计 writer 隔离/冻结副本；运行者负责 |
| 合法低分被排除造成均值虚高 | Test-covered protection | 空结果保留分母，坏输入整体失败 | 人工错误标签仍可影响口径 | 保持人工审阅，不以 skip 修复输入 |
| 单轮改善被误认为算法收益 | Observed variability | 保存三轮与逐题差异，不改顺序 | seeds 非独立样本，family 相关；无置信区间 | 比较负责人先批准统计/配对协议 |
| 持久化字节改变被误认正常维护 | Observed；根因 Unknown | 公开逻辑与文件哈希分别记录 | 无法唯一归因，无法证明逐位向量不变 | 重现/完整性需求出现时补诊断，不能直接免责 |
| 后半轮失败，前半轮难恢复 | Reasoned partial failure | collect 日志、preconditions、一般异常记录 | 无逐 worker checkpoint；硬中断/磁盘失败可能留半成品 | 重跑成本不可接受时由工具维护者设计恢复协议 |
| 报告已存在被误认采集成功 | Reasoned publication risk | 执行状态、after inventory、manifest、离线核对 | existence 不代表 JSON 完整或后置检查完成 | 自动消费前建立完整发布标记/验证流程 |
| 保存证据无长期副本 | Gate INFO；当前包未跟踪 | 完整工作区包及 manifest | Git HEAD 单独不足以恢复全部交付 | 维护者按用户另行授权归档/提交；本次不执行 |

持久事实分成两类：批准的输入真值与采集的原始观察。宏平均、展示表格和解释是可派生结果；不能用重新计算去补造当时缺失的 after 检查。故障恢复要保留失败目录和旧输入，而不是覆盖证据、回滚未知的 Chroma 内部写入或修改判断来“让结果通过”。

## 7. Scalability & Upgrade Triggers — 先观察哪种成本？

| Current assumption / design | First likely bottleneck | How to observe | Redesign trigger | Candidate architecture class |
|---|---|---|---|---|
| 小语料可全量覆盖审阅 | 人工判断/复核量随 query×chunk 增长 | 实际审阅时长、争议量、漏标复查 | 人工成本阻止数据维护或代表性扩展 | 获批抽样/分层覆盖、独立标注与审阅工具；不自动降低真值标准 |
| 单 JSON 内嵌数据与多轮报告 | report 大小、父进程内存、定位成本 | 字节数、内存峰值、分析耗时 | 文件和内存成本实际妨碍采集/审阅 | 分片、索引化观察与可验证 manifest，不只保存均值 |
| 每轮新进程顺序执行 | 重复初始化和重新查询 | 区分初始化/检索/校验的真实耗时 | 执行时间影响迭代且有测量依据 | 先定义冷热/并行条件，再考虑隔离 worker；不能无声改变复现条件 |
| 保留单机现有模型和库 | 协作者没有相同状态 | 复现实操的身份差异/缺资源 | 需要首次跨机或跨环境对比 | 可核对导出、环境约束、版本映射；需授权和真实验证 |
| 人工监督的小批次执行 | 中断恢复、挂起、残缺发布 | 失败日志、重复成本、无法终止的 worker | 无人值守或长任务成为实际需求 | timeout、checkpoint、明确终态和原子发布策略 |
| 三轮描述性噪声检查 | 无法判断微小变化可信度 | 差异与基线波动相当、不同运行结论反转 | 采用决策依赖微小收益 | 获批重复/配对/不确定性分析与污染控制 |

复杂度判断来自代码：完整标注矩阵为 Q×N；每轮保留 Q 个最多深度 D 的返回，R 轮返回数据随 R×Q×D 增长，另有内嵌 dataset 与其他元数据。没有对新规模做实际压力测试，不推造吞吐、SLA 或“超过某题数必须分布式”的阈值。

## 8. Known Gaps — 接受的范围、技术债、未证实假设和未来能力

模板中的 **Accepted v1 Limitation** 在这里指“本次获批首版数据/基线的限制”，不是把产品所有 V1 排除项永久化。

| Category | Gap | Current impact | Why accepted / unresolved | Trigger for action |
|---|---|---|---|---|
| Accepted v1 Limitation | 合成单组织政策，32A+8U，单人审阅与类别缺口 | 不可泛化为真实企业总体效果 | SC01/SC02、CD-3 明确批准；数据负责人拥有边界 | 决策需要更广泛业务代表性 |
| Accepted v1 Limitation | 共享 7 正证据块、2 补充规则，Test 非盲测 | 不能宣称来源独立/盲测；有污染风险 | 人工 split 批准已披露；核心 family 不跨侧 | 候选选择前需要更强独立性或发生 Test 调参污染 |
| Accepted v1 Limitation | 深度 10 口径、二值相关性、U 不入主均值 | 不完全对应生产请求或回答成功率 | 冻结 measurement objective | 目标变更时先修订批准协议，保留旧口径 |
| Technical Debt | 运行证据尚为未跟踪工作区文件 | HEAD 不等于完整交付 | Gate F-4；未授权提交；维护者负责保存 | 需要长期交接/灾后恢复时另行授权归档 |
| Technical Debt | 单体报告、缺逐 worker checkpoint/timeout/原子发布 | 长任务失败恢复与自动化成本 | 当前小规模受监督运行可管理；非已发生故障 | 中断/运行时长/共享执行要求出现 |
| Technical Debt | 采集/离线审计使用 assert | 优化模式可能绕过部分检查 | 普通 Python 命令下使用；未做工具加固 | 进入自动化验收时明确禁优化或获批显式检查 |
| Unverified Assumption | 存储向量完整性、磁盘变化根因 | 不能从公开文本一致推导向量逐位语义 | 公共接口与无分支诊断的证据边界 | 对结果漂移进行因果定位或强完整性验证时 |
| Unverified Assumption | 三轮可代表更多 seeds/平台/时间 | 当前只有描述性范围 | 没有统计充分性或跨平台实验 | 改善与噪声相近，或更换环境 |
| Unverified Assumption | 无瞬时外部写入 | 起终点相同不足以排除中途变化 | 无 OS 级 writer lock；运行者约定 | 多进程/协作同时访问 collection |
| Future Capability | 可移植模型/索引复现包与迁移协议 | 本地存在状态不保证异机复现 | 未要求本阶段建设通用交付平台 | 首次跨机复现需求 |
| Future Capability | 生成质量及 latency/cost 测量 | 无法判断答案/拒答/资源收益 | 生成归后续获批 Phase 24；latency/cost 未测，预算未定义 | 决策目标确实需要这些维度并明确 owner/协议 |
| Future Capability | RRF/BM25/Reranker/Query Rewrite 等 Candidate | 无算法采用或收益结论 | 本阶段只建基线 | Phase 21 或其他阶段独立获批具体研究问题与任务 |

技术债是当前工程判断，不替代 Gate severity，也不自动创建阻断项或授权修复。未验证项不一律写 DEFERRED；只有明确后续 owner 的生成评估才有对应阶段归属，其余需未来协议决定。

## 9. Evidence & Verification Boundary — 结论来自哪一层？

### 9.1 Phase closure evidence

| Engineering claim | Source / command | Scope + dependency boundary | Result / date | Not established |
|---|---|---|---|---|
| 输入契约和工具计算可检查 | [Contract](../../v2/evaluation/retrieval-evaluation-dataset-contract.md)、[测试](../../../backend/tests/test_evaluation.py) | STATIC 定义；历史 UNIT + MOCKED/SUBSTITUTED | 2026-09-11 工具验收；2026-09-14 原始日志 8/50/10 | 不能认证人工语义或真实企业效果；ER 未重跑测试 |
| 真实 Hybrid 在冻结数据上运行 | [report](../../v2/benchmarks/t2003-v1-baseline-1.0/run-01/report.json)、[execution](../../v2/benchmarks/t2003-v1-baseline-1.0/run-01/execution.json) | REAL 本地 BGE/Chroma，120 次 Hybrid，非 LLM | 2026-09-14 三轮各 40 题；命令退出 0 | 非浏览器/API/生成 E2E，非生产深度 5 独立测量 |
| 波动不是被均值隐藏 | 同一 report 的 raw_results、metrics、repeatability | REAL 历史输出与离线分析 | 5 order / 6 score map / 1 metrics 变化 | 不证明根因、统计显著性或所有环境稳定性 |
| 公开状态与磁盘身份分开记录 | before/after inventory、execution hashes | REAL 历史读取 + STATIC 文件记录 | 38 块逻辑相同，3 持久化文件字节变化 | 非逐位向量语义审计、非排他运行证明 |
| 独立 Gate 的必需验收成立 | [Gate 报告](../../verification/PHASE-20-GATE-REVIEW.md) | 2026-09-18 67 tests；离线复算/替代重放/文件核对 | 既有 Gate PASS；4 INFO | ER 引用而不重签；Gate 未重跑 live/写文件 CLI |

历史完整测试为 8+50+10=68 个方法；独立 Gate 为 7+50+10=67，主动排除会写临时报告的 CLI 测试。两者不能混写为同一次 68/68。历史三轮使用真实模型和库，但语料为合成政策；UNIT、MOCKED、SUBSTITUTED 与 REAL 是不同执行边界，不是自动升级阶梯。

### 9.2 Later project evidence 与本次 ER

Gate 后的 Learning Review 只重组教材、核对数值/链接和完成独立读者检查，没有新增真实检索。本次 ER 又是独立活动：重新读实现、脚本、原始 JSON 与决策资料，并执行一次安全离线复核。

**本次实际命令（仓库根目录，Windows PowerShell / Python 3.14.6）：**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -B docs/v2/benchmarks/t2003-v1-baseline-1.0/verify.py
```

退出 **0 / PASS**；重新计算 **1,152 个逐题指标值**并核对聚合与已有变化诊断、文件哈希；公式比较容差 `1e-12`，原跨轮比较容差仍为 0。REAL 指离线验证程序实际执行，不是新的 REAL 检索。当前 source/release/artifact 与采集身份核对通过，不加载模型，不初始化 Chroma，不改 report。

另执行 `python -B -` 只读内存探针，打印 protocol、三个 PID、变化题 ID、公开记录的持久化差异、各命令退出码、Q013/Q014/Q025/Q032 单题值和 split @5 聚合、report 文件大小；退出 0。这是原始字段检查，不是新的指标 Runner、采集或性能 Benchmark。工具输入保留于本次会话，未新增检查脚本。

本次 **未执行** unittest、pip check、真实模型加载/encode/retrieval、collect、provider、浏览器或 API E2E，也没有重新哈希本地模型/索引全目录。Gate 的 29/45 文件核对是之前证据，不冒充本次新执行。latency/cost、生成质量、异机复现仍未测量；不存在可以凭本文补出的缺失证据。

## 10. Engineering Lessons — 值得迁移的判断

1. **比较之前先固定观察对象。** 在保存 V1 前修排序，会改变要回答的问题；正确的后续改动也需要新版本和参考。
2. **校验资格与评判语义分开。** fail-fast 可以保护均值分母，但不能认证人工批准或发现所有语义泄漏。
3. **分母和执行深度属于产品化测量契约。** 相同名字的 @5 可能来自不同候选空间，不能只对齐展示列。
4. **负向观察是测量产物。** Q013 的低排名和 Q014 的波动让未来问题更明确；删掉它们会损失判断基础。
5. **重复性有三个层次。** 数据身份、顺序、指标分别检查；文件相同并不保证排名相同，指标相同也可能隐藏排名变化。
6. **文件防覆盖不等于成功发布。** 目录存在、report 存在、after 检查完成、可离线复算是不同后置条件。
7. **公开逻辑一致不等于磁盘不变。** 实际观察要求保留未知根因，不能用“客户端只读”替代磁盘或并发证据。
8. **初始平台应适合当前问题，也要知道退出条件。** 小型本地 JSON 基线合理，跨机、长任务和小幅决策出现时才有明确升级问题；不提前建设通用平台，也不否认技术债。

这些教训来自当前代码、历史观察与本次推理，未虚构线上事故、性能收益或 Candidate 胜出经历。

## 11. Engineering Self-Review — 能否论证这些选择？

1. 如果为了复现给 V1 排序加次级键，失去的参考是什么？怎样在新授权下同时保留旧参考和新实现？
2. 为什么公开快照校验、文件哈希和真实检索三者合起来仍不认证人工标签正确？
3. 当前单人审阅与 32A+8U 在什么研究目标下够用，在哪类业务结论下不够？
4. 共享 chunk 与共享核心事实有何不同？为什么批准 family 隔离仍不能称 Test 为盲测？
5. 若 Candidate 的 nDCG 提升与已见波动同量级，下一项应批准的是哪类验证，而不是哪种算法？
6. 为什么有效题空结果应保留，而坏题不能 skip 后继续平均？若未来必须隔离失败，哪个契约要先明确？
7. 一个 worker 在第三轮失败时，当前工具能保留什么、可能丢什么？哪项需求会使 checkpoint 值得建设？
8. 为什么 x 模式、防覆盖目录和 manifest 不能自动提供事务、签名或并发隔离？
9. 第一次跨机重现时，需要带走和验证哪些身份？为何重新入库不是透明替代？
10. 什么实测信号才足以支持改变数据格式、执行方式或审阅流程？哪些成本目前只有推理没有测量？
11. 如何向后续实验负责人说明 Gate readiness、工程 KEEP WITH KNOWN LIMIT 和实际执行授权是三个不同结论？

## Appendix A — Implementation / Task Traceability

| Engineering concept | File / Class / Function | Task coordinates |
|---|---|---|
| 数据契约与身份/审阅职责 | [Contract](../../v2/evaluation/retrieval-evaluation-dataset-contract.md) §3–14 | T2001 / ER20-D2–D4 |
| 全量校验 | [dataset.py](../../../backend/evaluation/dataset.py) validate_dataset / review | T2002 / ER20-D4 |
| 固定公式和分母 | [metrics.py](../../../backend/evaluation/metrics.py) score_query；[runner.py](../../../backend/evaluation/runner.py) aggregate | T2002 / ER20-D3 |
| 独立接入与进程重复 | [v1.py](../../../backend/evaluation/v1.py) build_search；[CLI](../../../backend/evaluation/__main__.py) main/worker | T2002 / ER20-D1/D5 |
| 历史产品候选与状态 | [qa.py](../../../backend/app/services/qa.py) Keyword/Vector/Hybrid；[ingest.py](../../../backend/app/services/ingest.py) chunk_text | 继承 V1；非本 Phase 新实现 |
| 采集与离线复核 | [collect](../../v2/benchmarks/t2003-v1-baseline-1.0/collect.py)、[verify](../../v2/benchmarks/t2003-v1-baseline-1.0/verify.py) | T2003 / ER20-D6 |

## Appendix B — SPEC / AC / Gate / Evidence References

权威层级：[V2 SPEC](../../v2/SPEC.md) > [V2 TASKS](../../v2/TASKS.md) > [CLAUDE](../../../CLAUDE.md)。EVAL-01/02 对应数据与工具，EVAL-03 对应保留真实 V1；EXP-01/02 约束未来实验及采用，GEN-01/SAFE-01 限制结论与生产变更。AC-2001-1～3、AC-2002-1～4、AC-2003-1～4 的验收归独立 Gate，本文不重新逐项裁决。

已有 Gate 正式结论为 **PHASE_20_PASS — READY_FOR_PHASE_21**，无 BLOCKER/MAJOR/MINOR、4 INFO。F-1 波动→ER20-D5；F-2 持久化与向量边界→D6；F-3 数据局限→D2/D3；F-4 未跟踪证据→D6/§8。没有把 INFO 擅自改成已修复或新增 Task。

版本：V1 tag `da8be59a60d7f35a2e3c1ab835624946c53d2a55`；当前/测量 HEAD `1692aa5877af120680d0fd386b3aa9f82b0069ea`；Runner 0.1.0、Contract 0.3、dataset novatech-retrieval-benchmark-1.0.0、snapshot t2001-novatech-pilot-01。历史依赖见原 report；Windows/Python 3.14.6、ChromaDB 1.5.9、Sentence Transformers 6.0.1、Transformers 5.16.1、Torch 2.14.0。记录身份不等于锁定或重新验证所有环境。

## Appendix C — Historical Notes 与保留审计

- 2026-09-09～10：Pilot 真实入库、人工修订与 coverage、Contract 0.3 冻结。Pilot 30 显式 +198 隐式判断；CQ-005 一块 Grade 3、四块 Grade 2 保持 CD-2 语义，不是等待工具“纠正”的标签。
- 2026-09-11：Runner 与 fixtures 验证；历史 Windows 路径键问题修为 as_posix，8 tests 通过；替代 store/vector 的同分测试不能冒充真实模型效果。
- 2026-09-14：正式数据冻结和后续执行授权分开；预检首次计数方法名错误、修正及冒烟范围保留在各自原材料；完整三轮基线另行记录，早期“未授权/未执行”字段没有回写。
- 2026-09-18：独立 Gate、Learning consolidation 和本次 ER 是三次不同职责的活动。同日也必须区分哪些测试真的再次执行。
- [原 Task 学习历史](../phase-20-task-learning-history-2026-09-18.md)与 [Learning](../phase-20-evaluation-foundation.md) 保留原理由、失败和 reader 修订；本次没有迁移或删除它们。没有旧 Phase 20 ER 被覆盖。
- 本文承接全部重要决策材料：CD-1 coverage、CD-2 binary/graded、CD-3 Human authority、CD-4 target/split，SC01/SC02 的规模/语料接受，深度差异、排序波动与采集副作用；将其重组为工程判断而非再写教程。新增的 checkpoint/timeout/assert 等讨论均标为 STATIC 推导与未来触发条件，不追记为历史事故或原团队当年的实际动机。
- 历史基线包及证据尚未跟踪，不把当前 HEAD 当完整交付；本次不提交 Git、不修改文件身份清单、不启动 Phase 21，不自动生成 Interview synthesis。

## Appendix D — 本次文档质量检查

### D.1 独立工程读者检查

2026-09-18 通过 doc-coauthoring 技能 Stage 3 启动无父会话/写作上下文的独立 reader `phase20_er_reader`。**PASS，无必须修订的内容 finding。** 读者先只看 ER，再核对工程模板、CLI、collect、verify、runner、V1 adapter、validator 及已有 Gate。全程只读，没有执行测试、验证脚本、模型、检索或采集；不把本次读者判断当成运行证据。

八项推理检查均正确恢复：①六项选择的本地、小规模、人工监督前提；②真实批准与教育/未来替代方案的区别；③人工、执行、解释和恢复成本的 owner；④后续 worker 失败导致前轮内存结果可能未落盘；⑤x 模式防覆盖与完整发布的区别；⑥timeout/assert 为源码推理而非事故；⑦可观察升级条件及四类 Known Gaps；⑧历史 68 tests、Gate 67 tests、ER 离线执行及未来授权分别记账。

读者确认新增 partial failure、checkpoint、timeout、assert 分析有源码支撑且标签准确；没有将本文误写为教程、Gate 或 Phase 21 授权。独立读者未重演本轮离线命令，也未认证历史人工审批真实性；这些边界保留。

### D.2 文档与完整范围核对

- 写入前对 **245 个** tracked/untracked 非忽略文件建立 SHA-256 清单。逐项比较后，仅 CLAUDE.md、学习 README、Learning 附录 A 的 ER 导航、V2 README 四个现有文档有变化；新增本 ER，**无删除**。没有覆盖旧 ER、原 Task 学习历史、已有 reader 或 Gate 记录。
- 四处导航仅承接后续 ER 活动及其位置；Learning 正文、历史“本次未执行 ER”的交付时点不重写。TASKS 中先前学习活动的记录不作为本次修改目标，任务状态、AC 和未来路线图均未改变。
- 产品、测试、Runner、SPEC、TASKS、独立 Gate、冻结数据及 **25 个原始基线包文件**与本次起点哈希一致。已有 dirty 工作区完整保留；未把普通 Git diff 中的既有改动算成本次修改。忽略目录中的模型/索引没有被本次工具初始化或写入，未声称本轮对其另做全量哈希。
- Windows PowerShell 下 `python -B -` 内存文档探针退出 0：本 ER 与四个导航文件共 **165 个本地文件链接**有效、缺失 0，代码围栏成对；确认模板 11 个核心章节及六项决策坐标齐备。没有新增检查脚本。
- `git -c core.safecrlf=false diff --check`、`git diff --cached --check` 均退出 0；`git diff --cached --stat` 无输出。HEAD 保持 `1692aa5877af120680d0fd386b3aa9f82b0069ea`。本轮离线复算及命令边界另见 §9.2，不重复计算为新一轮 Benchmark。
- Loss audit：已有 CD/SC 选择、替代方案性质、失败/修订、Gate 四项 INFO、真实与替代证据、并发和向量边界均有承接，原文来源未删除。Engineering audit：每项决策含成本、失败和重审条件；8 条工程教训、11 道推理自测；不生成面试话术。

**本次 Engineering Review 及独立 reader-test 完成。** 工程判断与 Gate 状态分别记账；没有修改产品、SPEC、任务状态或原始基线，没有启动 Phase 21，没有 commit/push。Interview synthesis 未执行。
