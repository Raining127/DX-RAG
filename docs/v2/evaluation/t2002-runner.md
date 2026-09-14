# T2002 — 检索评估 Runner 0.1.0

执行授权见 [SPEC §1.3](../SPEC.md)，测量定义完全沿用 [冻结 Contract 0.3](retrieval-evaluation-dataset-contract.md)。2026-09-10 启动，2026-09-11 完成验证。T2002 为工具实现；这里的合成观察不是正式 Baseline，也没有把 Pilot 晋升为 Benchmark。

## 组件与调用

独立 Python 标准库包 [backend/evaluation](../../../backend/evaluation/__init__.py)，不由产品导入，无新增依赖：

- `dataset.py`：JSON 加载、重复键检查、全量 fail-fast、快照映射、coverage、审阅和 evidence-family 校验。
- `metrics.py`：Recall、RR、nDCG 的纯计算，输入为已验证真值和去重后的实际有序 IDs。
- `runner.py`：每题只请求一次 `top_k=10`，保留原始 IDs/分数，首次出现去重，逐题计分、分 split/category 聚合及重复性诊断。
- `v1.py`：通过公开 `ChromaVectorStore.list_chunks()` 检查全量 IDs、文本 SHA-256 和文件映射，再直接调用未修改的 `HybridRetriever.hybrid_search()`。
- `__main__.py`：CLI 在独立 Python 进程中重复执行，保存一个完整 JSON 报告；任一无效输入/失败均退出 1，不输出看似成功的部分聚合。

从仓库根目录进入 `backend`，运行合成 fixture：

```powershell
cd backend
python -m evaluation --dataset tests/fixtures/evaluation/hand-calculated.json --mode fixture --seeds 1,2,3 --output ../tmp/t2002/fixture-report.json
python -m unittest discover -s tests -p test_evaluation.py -v
python -m unittest discover -s tests -p test_qa.py -v
python -m unittest discover -s tests -p test_query.py -v
```

每次输出选一个新路径；已有文件拒绝覆盖。`fixture` 模式只消费明确标记的记录列表，不初始化 Chroma、embedding 或 LLM。`--seeds` 至少两个 0～4294967295 的整数；默认 `1,2,3` 是本 Runner 的操作默认值，不是新增冻结指标要求。相同 seed 可用于同条件重跑，不同 seed 用于跨进程 set 顺序风险探测。

后续 T2003 另行获授权、真实数据完成审阅且模型/索引可用后，调用形状如下（占位路径，**本次未运行**）：

```powershell
python -m evaluation --dataset <reviewed-dataset.json> --mode v1 --seeds 1,2,3 --output <new-report.json>
```

所有 worker 的工作目录固定为 `backend`；环境变量与 `.env` 按现有 V1 Settings 生效。运行期间保持数据文件、模型文件、索引和代码不变。加载每个 worker 后校验 dataset hash 一致；V1 adapter 每次重新检查冻结 chunk 映射及内容。禁止并发摄入/修改该 collection。Runner 不创建语料、不重新摄入、不修改排序或生产配置。

## JSON schema 1：冻结契约的序列化实现

[完整 synthetic fixture](../../../backend/tests/fixtures/evaluation/hand-calculated.json) 是机器可读示例；其中的短 ID、审批字段与来源文字仅用于测试。不可替换 `purpose` 或 reviewer role 后冒充正式 Human 审阅数据。

| 层级 | 必填字段与语义 |
|---|---|
| Dataset | `schema_version="1"`、`contract_version="0.3"`、`purpose`（`synthetic_fixture` / `benchmark`）、非空 `dataset_version`、`corpus_version`、`snapshot_id`、`collection`、`provenance`、`review`、`snapshot`、非空 `queries`。一个文件对应一个 dataset version 和 snapshot。 |
| Provenance | 非空文字 `source`、`distribution_basis`、`annotation_method`、`git_context`、`limitations`、`ingestion_config`、`model_version`；应记录实际版本/配置/审批引用，不能用缺省猜测替代。 |
| Snapshot | `corpus_version`、`snapshot_id` 必须与 dataset 一致；非空 `chunks` 为完整冻结 inventory。snapshot_id 本身是唯一快照版本身份，无需冗余版本号。 |
| Chunk | 非空 `chunk_id`、`file_id`、`file_name`，非负整数 `chunk_index`，小写 64 位 `content_sha256`（原始 chunk 文本 UTF-8 的 SHA-256）。 |
| Query | 非空 `query_id`、`query_text`、`evidence_family_id`、匹配的 `corpus_version/snapshot_id`，四种获批 `query_category` 之一，严格 boolean `answerable`、`coverage_reviewed=true`，`review_status="APPROVED"`，`split="Dev"/"Test"`，`review`、`coverage_review` 和 `judgments` 列表。 |
| Review | `status="APPROVED"`、`role="Human project owner"`、ISO 日期 `date`、非空 `decision_ref`。synthetic 模式必须改用 `role="SYNTHETIC_TEST"`，不能声称人工审批。Dataset review 引用最终 promotion（含 split/leakage），Query review 引用 wording/category/answerability 批准，judgment review 引用最终等级批准。 |
| Coverage review | 同上，另有 `full_snapshot_screened=true`、`no_positive_omissions=true`；继承所属 query 的绑定身份，记录完整快照覆盖和无正证据遗漏决定。 |
| Judgment | `chunk_id`、`file_name`、`chunk_index`、0～3 整数 `human_grade`、`review`；可选 `file_id` 必须匹配；可选 `suggested_grade` 必须为 0～3 整数，与最终值不同时必须有非空 `rationale`。 |

整个 dataset 在任何 search 前验证。重复 query ID、未知 chunk、映射冲突、无效 grade（含 Python bool）、缺失/不兼容版本、coverage 未完成、非 APPROVED、缺 provenance、错误类别/split、同 evidence family 跨 Dev/Test、冲突 Human judgments 均阻止执行。同一 query/chunk 的相同重复判断可合并为一个真值，不重复扩大分母。隐式 0 只用于已完成 coverage 的 snapshot 内未列块。

Validator 只能验证记录的结构与一致性，不能证明 `decision_ref` 背后的人工决定真实存在，不能自动判断两条语义相同问题是否被错误分到不同 family；这些仍由 Human promotion review 负责。正式数据必须补齐真实的模型/索引版本与审阅证据。

## 指标与报告边界

所有 `K=1,3,5,10` 消费同一次深度 10 返回的去重列表前缀；重复位置按原始 1-based rank 记录，不重新检索补足。分数相同保持原顺序。Recall 分母是全部 `grade>=2` 真值；RR 只在该 K 内找第一个相关名次。nDCG 使用 `2^grade-1` gain 和 `1/log2(rank+1)`，IDCG 来自完整真值而非命中集合。

有效 Answerable 空结果在全部 K 计 0 并保留于分母。Answerable 没有 grade>=2 则阻止整个输入运行。Unanswerable 保留原返回、匹配等级和排除原因，主指标为 null；仅 Grade 1 的无二值相关项条目标为 `unanswerable_weak_only` 单列，不自动改写 Answerable。没有合格 query 的组为 null，不能写成零均值。

每轮报告保存 `per_query` 与 `aggregates`。聚合按 Dev/Test 分开，分别有全类别和每个 query-category 的 included/excluded/invalid/denominator；`invalid=0` 仅出现在整份数据校验通过的成功报告中。aggregate 指标名为 `mrr`，per-query 为 `rr`，均嵌套于明确 K 下。排除 IDs 和逐题返回支持 Unanswerable 误召回审阅，不新增拒答评分。

报告顶层内嵌 dataset/config/provenance、Runner 版本、UTC 时间、完整命令、Python/platform/包版本、Git HEAD/status、V1 tag 与产品 diff，以及工作区 Python 源码/契约 SHA-256。未提交代码不会被表述为 HEAD 中已有；相同版本号下也能核对实际工具内容。每次 worker 保留 pid/hash seed、实际配置、stderr 和所有指标；不跨重复轮次取均值掩盖波动。

`repeatability` 使用精确比较（指标容差 0），记录每题各轮 order、受影响位置、分数及指标是否改变、各轮指标。检查失败与观察到排名不稳定不同：后者仍是成功保存的有效观察，`order_stable=false`，不会修改 V1 来使报告变绿。

`@1/@3/@5` 仍来自请求 10，未必等于独立 production Top-K=5 执行。Hybrid 分支请求深度为 20、VectorStore 为 40；production 对应 10 和 20。`@10` 是 deeper retrieval diagnostic，不能叫 production Recall@10。latency/cost 明确 `NOT_MEASURED`。

## 验收证据（2026-09-11）

环境：Windows PowerShell，Python 3.14.6；开始 HEAD `fe23d3846c276a7c127c29bc0ea3456b89ebbb89`。V1 tag 仍为 `da8be59a60d7f35a2e3c1ab835624946c53d2a55`。无 commit/push、无新增依赖。

| AC | 本次证据 | 结论与边界 |
|---|---|---|
| AC-2002-1 | `test_evaluation.py` 手算与空/短/重复/弱相关边界：grades a=3,b=2,c=1，实际 c,b,b,a,d → c,b,a,d；Recall@1=0、RR@1=0、nDCG@1=1/7；Recall@3=1、RR@3=1/2、nDCG@3=(1+3/log2(3)+7/2)/(7+3/log2(3)+1/2)。另测遗漏真值分母与 macro 聚合。 | PASS；UNIT synthetic，无质量代表性。 |
| AC-2002-2 | 多项非法输入逐项断言 ValueError 且 search 未调用；无效返回拒绝计零。CLI 端到端保存 3 worker 报告并检查身份、源码 hash、范围、未测量字段及拒绝覆盖。 | PASS；校验事实真实性仍依赖 Human review。 |
| AC-2002-3 | CLI 固定记录列表 3 进程稳定；实际 V1 Keyword+Hybrid、替代 store/vector、8 个同分 chunk、hash seed 1/2/3 观察到排名与指标波动，报告断言顺序未改变且分数本身不变。 | PASS；SUBSTITUTED，非真实模型/索引稳定性证明。 |
| AC-2002-4 | 评估测试 8/8；既有 `test_qa.py` 50/50、`test_query.py` 10/10；`git diff v1.0.0 --stat -- backend/app frontend` 无输出。 | PASS；UNIT/MOCKED + STATIC，无产品差异，不宣称 LIVE/E2E。 |

原始本地运行证据位于 `tmp/t2002/evaluation-tests.txt`、`qa-regression.txt`、`query-regression.txt`（忽略目录，命令可重现）。测试首次发现 Windows 路径分隔符使源码 hash key 与跨平台路径约定不符；修正为 `as_posix()` 后评估测试 8/8 通过。ChromaDB 依赖产生 Python 3.14 deprecation warning，不影响断言。

受控 V1 同分样例三次实际 ID 顺序：

```text
seed 1: d g e a b h c f
seed 2: h b g e c d f a
seed 3: g e b c f h d a
```

同一 Answerable 真值 a=3,b=2,c=1 下，Recall@3 分别为 0、0.5、0.5；RR@3 为 0、0.5、1/3；nDCG@3 为 0、0.20151514190050243、0.15969697161989949。这只是合成输入对已知 set 顺序风险的可执行证据；生产语料发生频率未知，未修复 V1。

## 当前局限与后续条件

T2003 尚未执行。真实 embedding、持久化 Chroma snapshot、Pilot 检索、正式版本化 Benchmark 和性能/成本均未测量。snapshot 校验覆盖 IDs/文本/映射，公开 VectorStore 不暴露 embedding，因此无法独立证明存储向量或模型文件版本；保留外部冻结索引与模型 provenance、运行期不变条件。三次 seed 检查不是所有平台或任意次数稳定性的证明。

下一步需要独立授权的数据构建/审阅和 T2003 执行；工具存在不代表这些条件已满足。Phase 20 Gate 未启动。
