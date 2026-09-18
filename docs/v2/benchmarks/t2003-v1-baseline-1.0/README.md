# T2003 — 完整 V1 Hybrid Retrieval Baseline

**T2003 验收：AC-2003-1～4 PASS。采集成功；排名与部分指标不完全稳定。Phase 20 独立 Gate 尚未执行。**

执行授权：[SPEC §1.10](../../SPEC.md)，`H-T2003-BASELINE-2026-09-14`，Human 原文「推进 T2003：采集完整 V1 混合检索基线」。冻结 release 中 `benchmark_authorized=false` 和“未执行”描述保留其发布时历史；后续授权在 SPEC 独立记账，未改冻结文件。

## 研究问题与测量对象

现有 V1 混合检索在已审阅 NovaTech 题集上能覆盖多少相关证据、把相关证据排到哪里、跨进程是否稳定？本次没有 Candidate，不作改善或生产采用结论。

| 身份 | 实际值 |
|---|---|
| 历史 V1 | `v1.0.0` → `da8be59a60d7f35a2e3c1ab835624946c53d2a55` |
| 测量 checkout | `v2/evaluation`，HEAD `1692aa5877af120680d0fd386b3aa9f82b0069ea` |
| 实现差异 | `backend/app`、`frontend` 相比 V1 无差异；评估包由 V2 提供；采集前后产品及 Runner Python 文件 hash 一致 |
| 工具 | Runner `0.1.0`；Contract `0.3 FROZEN`；脚本/源码/数据 hash 见 execution.json 和 report.json |
| 数据集 | `novatech-retrieval-benchmark-1.0.0`，40 题、32 Answerable + 8 Unanswerable、1,520 个显式等级、20 families |
| 语料／索引身份 | `novatech-pilot-0.1` / `t2001-novatech-pilot-01`；4 文档、38 块；实际 collection 及完整公开快照见 inventory-before.json |
| 模型 | 本地 `BAAI/bge-small-zh-v1.5`；冻结 revision `7999e1d3359715c523056ef9478215996d62a620`；冻结清单 29 项 model hash 匹配，前后完整模型目录 hash 一致；产品强制 512 维输出 |
| 环境 | Windows、Python 3.14.6；ChromaDB 1.5.9、Sentence Transformers 6.0.1、Transformers 5.16.1、Torch 2.14.0；完整包版本见 report.json |
| 配置 | keyword 0.3 + vector 0.7，threshold 0.30；生产默认 Top-K 5；chunk 800 / overlap 120；配置路径与冻结快照一致 |
| 本次执行时间 | 2026-09-14 10:05:45–10:07:17 UTC（包括检查和测试，**不是请求延迟测量**） |
| 执行次数 | 一次 CLI，独立进程 seeds 1/2/3，每轮 40 题，共 120 次 Hybrid 调用；未重跑挑选结果 |

运行使用真实本地 BGE 和现有持久化 Chroma，通过未修改的公开 Hybrid 路径；没有 mock、LLM 调用、重新摄入或索引重建。进程配置 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`、`ANONYMIZED_TELEMETRY=False`、`PYTHONIOENCODING=utf-8`。采集起点工作区包含本任务授权/状态/证据脚本；报告记录 dirty 状态，本次新增证据尚未提交。首次 frozen release 的“未提交”属于历史，实际输入已包含在测量 HEAD 中。

## 指标口径

每题仅请求 `top_k=10`，不分别请求各 K。消费该有序列表前 1/3/5/10 项；Hybrid 两路候选深度为 20，VectorStore 请求深度为 40。独立生产请求 Top-K=5 的对应深度为 10/20，因此本报告 @5 **不保证等同于独立生产请求**；@10 为更深检索诊断。

Recall/MRR 的 relevant 为 grade >= 2；nDCG gain 为 `2^grade-1`，按 `log2(rank+1)` 折扣，IDCG 取完整真值的理想排序。按 query 宏平均，Dev/Test 分开，每侧纳入 16 道 Answerable，排除 4 道 Unanswerable；每轮 invalid=0。不增加 tie-breaker，不改同分顺序，不补足去重后的列表。原始报告保留匹配等级、分组分母与排除理由。

## 真实结果

以下各行列全三轮结果；相同值合并写明 seeds。展示六位小数，未跨轮平均。各类别及全部逐题摘要见 [metrics.md](metrics.md)，完整精度、IDs、分数、每轮每题指标见 [原始报告](run-01/report.json)。

| Split | Seeds | K | Recall | MRR | nDCG |
|---|---|---:|---:|---:|---:|
| Dev | 1/2/3 | 1 | 0.575000 | 1.000000 | 1.000000 |
| Dev | 1/2/3 | 3 | 0.691667 | 1.000000 | 0.843039 |
| Dev | 1/2/3 | 5 | 0.912500 | 1.000000 | 0.912280 |
| Dev | 1/2/3 | 10 | 0.977083 | 1.000000 | 0.938019 |
| Test | 1/2/3 | 1 | 0.671875 | 0.937500 | 0.901786 |
| Test | 1/3 | 3 | 0.885417 | 0.937500 | 0.894264 |
| Test | 2 | 3 | 0.854167 | 0.937500 | 0.883722 |
| Test | 1/3 | 5 | 0.906250 | 0.937500 | 0.896220 |
| Test | 2 | 5 | 0.906250 | 0.937500 | 0.894758 |
| Test | 1/3 | 10 | 0.984375 | 0.944444 | 0.919197 |
| Test | 2 | 10 | 0.984375 | 0.944444 | 0.917736 |

### 复现观察

三个独立 worker PID 为 18996、30516、33688。跨轮精确比较（容差 0）：

- 5/40 题排名变化：Q001、Q002、Q008、Q014、Q033；完整位置和各轮排名在 `repeatability.per_query`。
- 6/40 题 ID→final_score 映射变化：上述五题及 Q034。该诊断同时包含返回 ID 集变化与同 ID 的分数变化，不应一概解释为向量数值漂移。
- 1/40 题指标变化：Q014。Dev 全部聚合不变，Test Recall@3、nDCG@3/5/10 有变化。Q014 的相关 Grade 2 块由 rank 3 移到 rank 4，RR 始终为 1；Recall@3 由 1 降至 0.5，nDCG@5 从 0.955831 降至 0.932444。
- Q014 的无关块 `c59ef50b-ba8a-4ab0-8bc2-2bcb350c3bbf` 分数由 0.3567781925201416 变为 0.3807781925201416，跨过 Grade 2 块。Q034 顺序不变，但一个块分数相差 0.01。因此实际观察不仅是最终同分列表内部换位。

**机制解释为推断，非新增分支测量：** V1 Keyword 从 set 遍历构造候选，按分数稳定排序后截断。并列项若在候选深度边界进出，Hybrid 会在“得到 keyword 加分”和“该路缺席、分数为零”之间改变，即使最终分数不并列也可能换位。当前数值与这一机制相容，但 Runner 未记录两路完整候选，本次不能唯一排除其他因素或宣称已定位全部根因。未加次级排序、调权重或重跑掩盖波动。

复现检查已执行并完整记录；“验收 PASS”表示证据与协议要求满足，**不表示跨进程排名完全确定**。三轮检查不证明所有平台/seed/时间条件下的稳定性，也不提供统计置信区间。

### 检索缺口与不可回答问题

- Q013（Test / Paraphrase）：「跑完一趟客户行程，商家还没补开发票，我能一直等票齐了再报吗？」三轮唯一 Grade 3 证据均排第 9，@1/3/5 全零，@10 Recall=1、RR=1/9。说明存在真实的前部排序缺口，不能用总体 MRR 接近 1 掩盖。
- 多证据覆盖仍不完整：Q025 的 Recall@5=0.6、@10=0.8；Q032 为 0.5、0.75。Dev Multi-chunk 的 Recall@5=0.733333，低于 Dev 总体 0.9125；只命中第一个相关片段不能证明回答所需证据齐全。
- Q020 首条是 Grade 2，Grade 3 位于第 3，故 RR@5=1 而 nDCG@5=0.730929；二值相关和证据重要性不是同一指标。
- Q033–Q040 八道 Unanswerable 三轮均有返回：Q034 每轮 3 条，其余每轮 10 条。命中等级只有 0/1，主指标为 null，分别从各侧排除 4 题。这说明阈值 0.30 会放行主题邻近但不足以回答的问题材料；没有调用生成模型，不能推断拒答正确或幻觉率。
- 无查询执行失败，无无效项，无返回重复 IDs；Q004 每轮返回 8 条，其余 Answerable 每轮 10 条；没有 Answerable 空结果。未基于这些观察调参或修改 Test。

## 数据与运行边界

运行前后完整公开逻辑快照（ID、正文、文件映射、collection、全部公开 metadata）完全一致。冻结 release 全目录 hash、模型全目录 hash、产品/Runner 源码 hash 一致。

Chroma 的 `chroma.sqlite3`、segment `data_level0.bin` 和 `length.bin` 前后 hash 改变，具体路径和 hash 保存在 execution.json。没有调用增删改/摄入/重建 API；原因未确定，不能将字节变化自动归因于客户端内部维护。公开接口不暴露全部存储向量，故本次没有逐位向量审计。运行前系统进程检查未见 Python 应用进程；未持有系统级排他锁，前后核验不能证明期间绝无瞬时外部写入。

数据限制沿用已批准 SC01/SC02：单一虚构组织的合成政策、小样本、类别比例/覆盖缺口、20 families、Dev/Test 共享 7 个正证据块和 2 条补充规则；Test 已人工审阅且不是盲测，不用于反复调参。不能推广为一般企业文档效果，也不能据此选择具体检索 Candidate。

现有本地向量库继续保留，公开快照和模型 hash 支持身份核对；本证据包不含可移植向量库或模型权重。另机复现必须提供同一模型和匹配的既有索引，或另行批准重建与映射迁移；重新入库生成新 UUID，不能直接冒充同一快照。

latency / cost：**NOT_MEASURED**。本次没有 LLM 生成、回答/引用正确性或拒答评分；没有浏览器/API 问答 E2E 声明。

## 复核与重现

从仓库根目录运行离线复核（不检索、不加载模型、不覆盖证据）：

```powershell
python docs/v2/benchmarks/t2003-v1-baseline-1.0/verify.py
```

首次实际采集命令（本次已经执行，不应为查看结果再跑）：

```powershell
python docs/v2/benchmarks/t2003-v1-baseline-1.0/collect.py
```

脚本内实际 Runner 命令与绝对路径保存在 [execution.json](run-01/execution.json)；调用形状为：

```powershell
cd backend
python -m evaluation --dataset ../docs/v2/evaluation/novatech-retrieval-benchmark-1.0.0/dataset.json --mode v1 --seeds 1,2,3 --output ../docs/v2/benchmarks/t2003-v1-baseline-1.0/run-01/report.json
```

今后获授权重现时，先确保 collection 无并发摄入/修改，保持模型/配置/源码不变，给 collect.py 传入新的**绝对输出目录**。默认 run-01 已存在，脚本拒绝覆盖。脚本会重跑相关测试、核对运行前后身份并保留失败日志；失败不应删掉后重跑同一目录。所有输出仅供测量，不改变生产默认设置。

## 验收账本

| AC | 证据 | 结论 |
|---|---|---|
| AC-2003-1 | report.json 的 Git/环境/命令/源码 hash/完整数据/配置；execution.json 的模型和持久化 hash；前后完整公开 inventory；V1 差异为空 | PASS，STATIC + REAL 本地模型/Chroma |
| AC-2003-2 | 三轮各 40 题完整原始结果、逐题指标、按 split/category 聚合；不可回答问题排除及失败/局限分析 | PASS，无 mock Benchmark，无生成结论 |
| AC-2003-3 | seeds 1/2/3 独立进程；容差 0；5 题排名、6 题分数映射、1 题指标变化如实保留；latency/cost 未测量 | PASS，复现检查完成；确定性不成立 |
| AC-2003-4 | 前后 product/runner/model/release hash、全量公开逻辑快照一致；保留原始索引与 V1 行为、命令/条件/波动；相关回归通过 | PASS，向量逐位一致与异机索引迁移未证明 |

本次实际测试（unittest 方法数）：`test_evaluation.py` 8/8、`test_qa.py` 50/50、`test_query.py` 10/10；pip check 通过。命令与 exit code=0 在 execution.json，stdout/stderr 原文同目录保存。这些测试包含 synthetic/MOCKED/SUBSTITUTED 边界，不升级为真实业务质量；真实检索证据由 report.json 独立提供。

[verify.py](verify.py) 仅读取保存的证据，以独立公式复算 3×32×4×3=1,152 个逐题指标值，核对分组分母/聚合/排除项、排名和分数诊断、源文件 hash；[verification.json](verification.json) PASS。独立公式浮点复核容差为 1e-12，不改变 Runner 跨轮容差 0。

Task Learning Pass 见 [Phase 20 学习素材](../../../learning/phase-20-evaluation-foundation.md)。下一步为独立 Phase 20 Gate；本报告不代替 Gate，也不授权启动 Phase 21。
