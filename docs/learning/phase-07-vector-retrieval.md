# Phase 7 — Vector & Hybrid Retrieval 学习笔记

> **Phase 状态**：🟡 IN PROGRESS（T0701、T0702、T0703 已完成；Phase Gate Review 与 Phase Learning Review 尚未执行）
>
> **本文档状态**：T0701 Task Learning Pass 完成（2026-08-28）；T0702 Task Learning Pass 完成（2026-08-31）；T0703 Task Learning Pass 完成（2026-08-31）。这是 Phase 7 的增量 Technical Learning，不把尚未完成的 Phase 写成 complete。
>
> **配套文档**：[Phase 7 Engineering Review](./engineering-review/phase-07-engineering-review.md) · [DX-RAG Interview Guide](./interview-notes/dx-rag-interview-guide.md)

本章只记录当前 checkout 中已经存在的 vector retrieval、hybrid retrieval 与统一 retrieval facade 学习内容。T0702 已在 `qa.py` 中实现 `HybridRetriever`、weighted fusion、chunk identity merge、relevance filter 与最终 Top-K；T0703 又增加了 `retrieve(query, collection, top_k)`，把 concrete `ChromaVectorStore`、两个 retriever 和 HybridRetriever 串成一个 service-level entry point。T0801 已提供无外部 I/O 的 context/source assembly，T0802 已提供 history validation、recent-window truncation 与 formatting，T0803 已提供独立的 DeepSeek client/System Prompt/retry adapter，T0804 已把这些边界编排成 `QAService` service result，T0805 已把 QAService 接到 `POST /api/query`；真实 provider/Chroma/upload E2E 与前端集成仍未验证。看到“未来”时，均表示 `[FUTURE] / Not implemented in v1`，不是当前代码已经拥有的能力。[PROJECT FACT]

## 0. 三层文档边界

Learning Pass 很容易被写成“代码改了哪些文件”的 Task summary。本章刻意把三个问题分开：

| Layer | Canonical 文档 | 本章的职责 |
|---|---|---|
| Layer 1 — Technical Learning | 本文 | 解释代码 mechanics、项目上下游、数据流、Python/TS 学习点、验证边界和练习 |
| Layer 2 — Engineering Review | [phase-07-engineering-review.md](./engineering-review/phase-07-engineering-review.md) | 记录 ADR、trade-off、failure modes、scale 与 Known Gaps；本文只放短摘要和链接 |
| Layer 3 — Interview Preparation | [dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md) | 当前 Task 只保留 Interview Candidates；完整回答、STAR 与 answer bank 等 Phase 完成后再 consolidation |

本次 T0701/T0702/T0703 不会把完整 ADR、failure taxonomy、10x/100x/1000x 容量分析或完整 STAR 塞进 Technical Learning。本文的 `[PROJECT FACT]` 来自代码、SPEC、TASKS 和本次测试；`[ENGINEERING KNOWLEDGE]` 是可迁移的工程概念；`[FUTURE]` 明确表示尚未实现。

## 1. Phase 学习：这一步到底增加了什么能力

### 一句话定位

Phase 7 先把 Phase 2 产出的 query embedding 接到 Phase 1 的 `VectorStore.search()`，再把 keyword/vector 两条可独立测试的 branch 按 `chunk_id` 融合成一个带阈值的最终候选列表，最后由 T0703 的 `retrieve()` facade 统一创建共享 storage、组装 retriever 并暴露一个可供 QA 层消费的入口。

### 学习重点

- 🟢 **必会**：两条 branch 的 score semantics、`chunk_id` identity merge、缺失分支补 0、`0.3/0.7` weighted fusion、`MIN_RELEVANCE_SCORE` 过滤顺序、`top_k * 2` 候选与最终 `top_k` 的区别，以及 T0703 facade 的 empty-collection short-circuit。
- 🟡 **了解原理即可**：Python `Callable`/constructor dependency injection、batch-shaped embedding API、`Dict[str, object]` 的动态 shape、map-based merge、list slicing 与 inclusive threshold。
- 🔵 **知道存在即可**：真实 corpus 的 ranking benchmark、并发调度、dynamic weights、RRF、metadata ownership 的后续统一契约、真实 provider/Chroma E2E 与线上 telemetry；T0805 的 HTTP route 已有 Mocked boundary evidence，但不因 T0703 facade 或 route 注册就假定真实链路已完成。

### 前置知识与学习路线

1. 先复习 [Phase 1 VectorStore](./phase-01-vectorstore.md) 的 public interface 与 distance → similarity boundary。
2. 再读 [Phase 2 Embedding](./phase-02-embedding.md) 的 lazy singleton、`normalize_embeddings=True` 与空输入语义。
3. 对照 Phase 6 keyword branch，理解 T0701 为什么先做成独立 adapter，T0702 再通过 injected retrievers 做 orchestration。
4. 阅读 `qa.py` 的 `VectorRetriever`、`HybridRetriever`、`retrieve()` 和 `test_qa.py` 的 4 个 hybrid tests + 3 个 facade tests，再运行本章“验证”中的命令。
5. 最后用 data flow 和 self-test 题复述：每个 boundary 谁负责什么、过滤与 Top-K 的顺序是什么、empty/missing collection 如何分流，以及哪些结果目前只能说 unit-tested。

## 2. Phase 目标：为什么需要 Vector Retrieval

### 业务目标

关键词检索擅长 exact terminology、型号、编号和代码片段，但它不能自然理解“AI 的子领域”和“人工智能的分支”这类 paraphrase。SPEC F010 因此定义了 semantic retrieval，让 query 与 chunk 在 embedding space 中通过相似度建立联系。[PROJECT FACT]

### T0701 的技术目标

T0701 的目标是完成一条最小、稳定的 vector branch：

```text
query (str)
  → query embedding (List[float])
  → VectorStore.search(collection, query_vector, top_k * 2)
  → similarity_score
  → service result with vector_score
  → top_k
```

它只负责“向量检索的适配”，不负责最终答案，也不负责把两个 ranker 合并。[PROJECT FACT]

### T0702 的技术目标

T0702 在两个已经归一化、方向一致的 branch 之上完成一个可组合的 hybrid result contract：

```text
keyword results (keyword_score) ─┐
                                 ├─→ merge by chunk_id
vector results (vector_score) ───┘       ↓
                           0.3 * keyword + 0.7 * vector
                                      ↓
                         sort → filter >= 0.30 → top_k
```

当前实现的两个调用是**顺序执行**；F011 允许并行或顺序，不能把“允许并行”写成已经使用 `asyncio.gather`。[PROJECT FACT]

### T0703 的技术目标

T0703 不再增加新的 ranking algorithm，而是把 T0602、T0701 与 T0702 已有的能力组装成一个可被后续 QA 层导入的 facade：

```text
retrieve(query, collection, top_k)
  → ChromaVectorStore()
  → get_chunk_count(collection)
       ├─ 0 → []（不创建 retriever、不做 embedding）
       └─ >0 → KeywordRetriever(store)
                VectorRetriever(store)
                HybridRetriever(keyword, vector)
                → hybrid_search(query, collection, top_k)
```

这里的“统一”是 service-module 入口统一，不是 HTTP API。`retrieve()` 让调用方不必自己重复 new 三个 retriever，也让同一个 `ChromaVectorStore` instance 同时服务 `list_chunks()` 与 `search()`；缺失 collection 的 storage exception 仍自然向上传播。T0804 后续实现了独立的 `QAService` orchestration path，当前直接调用 `HybridRetriever`，并不复用这个 module-level facade。[PROJECT FACT]

### 明确不做什么

- 不在 `VectorRetriever` 中再次做 min-max normalization；F008 已规定 `VectorStore` 把 raw distance 转成 `[0, 1]` 的 `similarity_score`。
- 不实现 BM25、TF-IDF、reranker、RRF 或其他 hybrid 算法。
- T0701 本身不实现 `HybridRetriever`、`MIN_RELEVANCE_SCORE` filter、统一 `retrieve()`、QA API、context assembly 或 LLM；这些职责在 T0702/T0703/Phase 8 分开落地。
- T0703 不实现 Context Assembly、Source Citation、DeepSeek client 或 HTTP `/api/query`；T0801/T0802/T0803 在后续 Phase 8 分别提供 converters 与 LLM adapter，T0804 再把它们接入 `QAService`，T0805 提供 HTTP adapter；真实 upload → query E2E 仍未验证。
- 不把 mock 单元测试描述成真实 embedding model + ChromaDB 的 semantic E2E。

相关契约：[SPEC F007 Embedding](../SPEC.md#f007-embedding)、[SPEC F008 Vector Storage](../SPEC.md#f008-vector-storage)、[SPEC F009 Keyword Retrieval](../SPEC.md#f009-keyword-retrieval)、[SPEC F010 Vector Retrieval](../SPEC.md#f010-vector-retrieval)、[SPEC F011 Hybrid Retrieval](../SPEC.md#f011-hybrid-retrieval)、[SPEC Section 8.1](../SPEC.md#81-environment-variables--config-parameters)，以及 [T0701](../TASKS.md#t0701--vector-retrieval) / [T0702](../TASKS.md#t0702--hybrid-retrieval-merge-fusion-relevance-filter-top-k) / [T0703](../TASKS.md#t0703--retrieval-module-integration) / [T0805](../TASKS.md#t0805--post-apiquery-endpoint)。

## 3. 项目位置：它夹在什么边界之间

### 所属层

`VectorRetriever` 位于 **Service Layer**（`backend/app/services/qa.py`）。它不自己加载 Chroma private object，也不自己解释 raw distance；它组合两个既有能力：

| 方向 | 已有契约 | T0701 如何消费 |
|---|---|---|
| Upstream — Embedding | T0202 / F007 的 `encode_chunks(List[str]) -> List[List[float]]` | 用 `[query]` 包装单个问题，取返回 batch 的第一个 vector |
| Upstream — Storage | T0105 / F008 的 `VectorStore.search(collection, query_vector, top_k)` | 传入扩大后的召回数量，接收 `VectorSearchResult` |
| Config | T0003 的 `settings.DEFAULT_TOP_K`（当前值 5） | 作为 service method 的默认 `top_k` |
| Downstream | T0702 `HybridRetriever`；T0703 `retrieve()` facade；T0804 `QAService`；T0805 HTTP endpoint | T0702 消费 `vector_score` 并输出 `final_score`；T0703 提供独立 Python entry point；T0804 直接消费 Hybrid 结果，T0805 再把 QAService 接到 `/api/query`（不复用 T0703 facade） |

### 查询侧位置

当前查询模型可以画成“两条 branch + 一个 service-level merge”：

```text
Question
   ├─ KeywordRetriever (Phase 6) → keyword_score
   └─ VectorRetriever (T0701)    → vector_score
             └───────────────→ HybridRetriever (T0702)
                                  → final_score
                                  → relevance filter
                                  → top_k
                                      ↑
                         retrieve() facade (T0703)
```

这是一种故意的 **adapter/orchestration boundary**：vector branch 先输出稳定的 service-level shape，hybrid branch 再决定如何按 `chunk_id` 合并和筛选，`retrieve()` facade 最后把共享 storage 和三个 retriever 组装起来；T0804 则在另一个 service boundary 直接编排 Hybrid、context/history、LLM 和 sources，T0805 的 HTTP route 继续消费这条 T0804 path。当前没有证据可以说 T0703 facade 已被 HTTP route 复用，或真实 provider/Chroma 已贯通。[PROJECT FACT]

## 4. Task 学习：T0701 Vector Retrieval

### 4.1 A. Code Understanding

#### 输入、输出和控制流

- **输入**：`query: str`、`collection: str`、可选 `top_k: int`。
- **第一步**：把单条 query 包装成 batch，交给 `embedder` 得到 `List[List[float]]`，再取第一个向量。
- **第二步**：调用 `vector_store.search()`，但传入 `top_k * 2`，为后续融合预留 recall。
- **第三步**：将 `VectorSearchResult` 的公开字段映射为 service dict；`similarity_score` 原值改名为 `vector_score`。
- **第四步**：对 storage 返回的已排序结果做 `[:top_k]` 截断。
- **输出**：`List[Dict[str, object]]`，每条只包含 `chunk_id`、`file_id`、`file_name`、`content`、`vector_score`。

实现位于 [`qa.py:87-117`](../../backend/app/services/qa.py#L87-L117)。`VectorRetriever` 没有写入 class cache、文件系统或 Chroma state；它只在一次调用中创建 query vector 和结果列表。[PROJECT FACT]

#### 结果 shape 为什么不直接返回 `VectorSearchResult`

`VectorSearchResult` 是 storage contract，包含 `metadata` 和 storage 语义下的 `similarity_score`；service contract 需要用 `vector_score` 与 keyword branch 的 `keyword_score` 对齐，并隐藏不属于 hybrid 输入的完整 metadata。这个映射是 boundary translation，不是重复存储。

### 4.2 B. Project Understanding

T0701 存在的原因不是“再包一层 class”，而是把语义检索能力放到正确的 owner：

1. Embedding module 负责把 text 变成 normalized vector。
2. VectorStore 负责 backend query 和 distance → similarity conversion。
3. Retriever 负责 query-level orchestration 和结果 shape。
4. HybridRetriever（T0702，已实现但不属于 T0701 的代码范围）负责把 keyword/vector 两种 score 统一到最终排序。

如果让 T0701 直接访问 Chroma `_collection`，service 就会知道 backend private details；如果让它自己把 distance 归一化一次，score 的意义就会漂移。F008/F010 把这两个责任分别锁在 storage 与 retrieval contract 中。[PROJECT FACT]

### 4.3 C. Learning Understanding

本 Task 最值得迁移的 mental model 是：**一个 service adapter 不必拥有全部算法；它要把上游稳定契约转换成下游可组合契约，同时避免越权。**

对 TypeScript/Node 学习者，可以先把 Python 代码想成：

```ts
type Embedder = (texts: string[]) => number[][];
type VectorStore = {
  search(collection: string, query: number[], topK: number): VectorSearchResult[];
};

class VectorRetriever {
  constructor(private store: VectorStore, private embedder: Embedder) {}
}
```

但 Python 的 `Callable[[List[str]], List[List[float]]]` 只是 type annotation，不会像 TypeScript compiler 一样在运行时验证函数签名；真正的保护来自注入 seam、测试和上游契约。这个差异值得明确记住。

### 4.4 T0701 验证学习，而不是只报测试数量

本次在 `backend` 目录执行：

```text
python -m unittest tests.test_qa -v
```

在 T0701 checkpoint（2026-08-28）执行时结果为 **17/17 PASS**：6 个 tokenizer tests、7 个 keyword retriever tests、4 个 vector retriever tests。当前 T0702 增量把 suite 扩展为 21 tests，详见下方 T0702 验证；另执行 `python -m compileall -q app tests`，结果 PASS。[PROJECT FACT]

T0701 的四个测试分别锁定这些 observable behaviors：

| 测试 | 它真正证明什么 | 边界 |
|---|---|---|
| semantic match mapping | 注入的 vector `[0.1, 0.2, 0.3]` 被传给 store；`0.82` 原样成为 `vector_score`；metadata 未泄漏 | `embedder` 与 `VectorStore` 都是 Mock；不证明真实 model 的 semantic quality |
| empty collection | store 返回 `[]` 时 service 返回 `[]`，不人为制造错误 | 是 mock empty-result unit boundary；真实空 Chroma KB E2E 仍未执行 |
| expanded recall | `top_k=3` 时下游收到 6，最终只返回前 3 条 | 证明调用数量和 slice；不证明 hybrid 融合后的最终 recall |
| default top_k | 未传 `top_k` 时使用 `settings.DEFAULT_TOP_K * 2` | 证明当前 config wiring；不证明 API 输入 validation |

SPEC 的 AC-F010-01（语义示例“AI 的子领域”匹配“人工智能的分支”）在当前证据下只能写成：**adapter mapping unit-tested；literal semantic match DEFERRED**。要升级为 real E2E，需要真实 model、真实 VectorStore/Chroma 数据和运行环境；该链路属于后续集成验证（项目当前计划将 literal upload → real Chroma → query 留给 Phase 12/T1202 范围）。AC-F010-02 的“空知识库返回空列表”在 mock boundary 已覆盖，但 real empty-KB 行为同样是 DEFERRED。[PROJECT FACT]

### 4.5 Interview Candidates（仅候选，不生成完整答案）

- **Technical point**：为什么 `VectorRetriever` 直接使用 `similarity_score`，而不再做一次 normalization？
- **Engineering question**：为什么 query 只编码一次，却向 `VectorStore` 请求 `top_k * 2`？这个扩大召回与后续 hybrid 的关系是什么？
- **Boundary question**：当前四个测试为什么不能证明 bge-small-zh-v1.5 真能理解 paraphrase？你会怎样补上真实验证？
- **Python/TS question**：`Callable` 注入与 TypeScript function type 相似在哪里，又不相似在哪里？

这些候选在 Task level 保持短小；完整 30 秒/1–2 分钟回答、follow-ups 和 STAR 不在本文生成，按 [Interview Update Cadence](./templates/phase-learning-template.md#interview-update-cadence) 等 Phase 级 consolidation。

### 4.6 T0702 A. Code Understanding：HybridRetriever 做了哪些转换

T0702 的输入仍然是一个 query，但它不再只调用一个 ranker：

- **输入**：`query: str`、`collection: str`、可选 `top_k: int`，以及 constructor 中可选的 `weights`。
- **召回**：先计算 `expanded_top_k = top_k * 2`，顺序调用 keyword 与 vector 两个 retriever。
- **合并**：把两个 branch 的 dict 放进以 `chunk_id` 为 key 的 `merged` map；不存在的分支分数从 `0.0` 开始。
- **融合**：默认按 `0.3 * keyword_score + 0.7 * vector_score` 计算 `final_score`。
- **筛选**：先按 `final_score` 降序排列，再保留 `final_score >= settings.MIN_RELEVANCE_SCORE` 的结果；当前阈值为 `0.30`，等于阈值的结果会保留。
- **截断**：最后才执行 `results[:top_k]`，所以低分结果不会抢占最终名额。
- **输出**：`chunk_id`、`file_id`、`file_name`、`content`、`final_score`、`metadata`。

实现位于 [`qa.py:120-199`](../../backend/app/services/qa.py#L120-L199)。这里有两个容易被忽略的实际细节：[PROJECT FACT]

1. 两个 retriever 的参数顺序不一致：keyword 是 `keyword_search(collection, query, top_k)`，vector 是 `vector_search(query, collection, top_k)`；`HybridRetriever` 没有另写 wrapper，而是在调用处显式遵守各自签名。
2. T0702 在 service level 把 `top_k * 2` 传给 `VectorRetriever.vector_search()`；而 T0701 的 `VectorRetriever` 内部还会把收到的值再乘 2 传给 `VectorStore.search()`，然后切回收到的 `top_k`。因此最终 `top_k=5` 时，mock hybrid test 观察到 vector retriever 收到 10；若走真实 VectorRetriever，底层 store 请求的是 20，返回给 hybrid 的是最多 10 条。这个组合成本不能被简化成“整个链路只请求 10 条”。

### 4.7 T0702 B. Project Understanding：为什么要按 chunk_id 融合

Phase 6 的 keyword branch 处理字面命中，T0701 的 vector branch 处理 semantic similarity；它们对同一个 chunk 可能各自产生一条记录。T0702 的核心不是“把两个数组拼接起来”，而是把两个 ranker 的观察合成一个**稳定的 chunk-level identity**：

```text
keyword hit: {chunk_id: A, keyword_score: 0.8}
vector hit:  {chunk_id: A, vector_score: 0.9}
                  ↓ same identity
one result:  {chunk_id: A, final_score: 0.87}
```

如果用 content 字符串去重，重叠 chunk、格式化差异或同内容的不同 chunk 都可能被错误合并；SPEC 7.1 明确把不可变 UUID `chunk_id` 作为 Retrieval Result identity。`merged: Dict[str, Dict[str, object]]` 正是在 service layer 把这个 identity contract 变成可执行的数据结构。[PROJECT FACT]

两个 score 已经在各自 owner 中同向化：F009 的 `keyword_score` 是 unique-token coverage，F010/T0701 的 `vector_score` 来自 storage 的 similarity。这样线性加权才有可解释的前提；T0702 不再重新读取 Chroma private state，也不重新计算距离。[ENGINEERING KNOWLEDGE]

还要区分“contract shape 已经存在”和“所有字段都已经由真实链路提供”：T0702 会输出 `metadata`，但 T0701 当前的 vector projection 明确没有把 `VectorSearchResult.metadata` 带出来。因此真实 T0701 → T0702 组合通常会得到默认 `{}`；dual-match 测试特意向 mock vector branch 注入 `metadata`，验证的是 HybridRetriever 的转发逻辑，而不是实际 VectorStore metadata 的端到端贯通。这是 T0801 已避开 metadata 依赖、但后续 F012/source contract 仍需明确的 ownership gap。[PROJECT FACT]

### 4.8 T0702 C. Learning Understanding：从两个排序器到一个候选集

可以用一个更通用的 **ranker ensemble** mental model 来理解这段 Python：

1. 每个 ranker 只负责自己的 evidence（keyword 或 vector score）。
2. orchestrator 用稳定 identity 做 union，而不是盲目 append。
3. 缺失 evidence 记作零，表达“该 ranker 没有支持这个 chunk”，不等于删除这个 chunk。
4. 用固定权重把同尺度 evidence 合成一个 utility score。
5. 先过滤低于产品阈值的噪声，再把剩余候选交给 Top-K。

TypeScript 类比可以先写成：

```ts
type KeywordHit = BaseHit & { keyword_score: number };
type VectorHit = BaseHit & { vector_score: number };
type HybridHit = BaseHit & {
  final_score: number;
  metadata: Record<string, unknown>;
};

class HybridRetriever {
  constructor(
    private keyword: KeywordRetriever,
    private vector: VectorRetriever,
    private weights: [number, number] = [0.3, 0.7],
  ) {}
}
```

Python 实际使用 `Dict[str, object]`，不是 TypeScript 那样的 discriminated union；因此 `.get()`、`float()` 和 `None` fallback 是运行时防御，而不是 compiler 已经替你证明的类型安全。对 frontend developer 来说，最重要的迁移点是：`Map<chunkId, accumulator>` 对应 Python dict accumulator；`final_score >= threshold` 对应一个明确的业务 predicate；`slice(0, topK)` 只能放在 filter 之后才符合 SPEC。

`weights` 也不是一个自动验证过的 tuple：`weights or [0.3, 0.7]` 会在 `None` 或空 list 时使用默认值，但长度不是 2 会在 unpack 阶段失败，权重是否在 `[0,1]` 或是否和为 1 当前没有 guard。学习时要把“默认配置”与“输入校验”分成两个问题。[PROJECT FACT]

### 4.9 T0702 验证学习：四个测试分别锁定什么

在 `backend` 目录运行：

```text
python -m unittest tests.test_qa -v
```

在 T0702 checkpoint（2026-08-31）结果为 **21/21 PASS**：6 个 tokenizer tests、7 个 keyword retriever tests、4 个 vector retriever tests、4 个 hybrid retriever tests。T0703 checkpoint 又增加 3 个 facade tests，成为 **24/24 PASS**；T0801 后续再增加 5 个 context/source tests，成为 **30/30 PASS**；T0802 再增加 4 个 history tests，成为 **34/34 PASS**；T0803 再增加 12 个 DeepSeek client tests，成为 **46/46 PASS**；T0804 再增加 4 个 QAService orchestration tests，成为 **50/50 PASS**；T0805 再增加 10 个 route-level tests，当前完整 suite 是 **60/60 PASS**。T0702 的四个测试使用 Mock retrievers，T0703 的三个测试使用 patched constructors，T0801 的五个测试使用 synthetic dict inputs，T0802 的四个测试使用 synthetic list/dict histories，T0803 的 12 个测试使用 injected/patched LLM client、OpenAI constructor、settings 与 sleep，T0804 的 4 个测试使用 injected Mock store/retriever/LLM，T0805 的 10 个测试使用真实 FastAPI `TestClient` 但 patch storage/service。它们验证各自边界的可观察行为，但不代表真实 embedding、ChromaDB、DeepSeek API、Frontend state 或 upload → query E2E。[PROJECT FACT]

| 测试 | 观察到的行为 | 证据边界 |
|---|---|---|
| `test_dual_match_is_fused_once_by_chunk_id` | keyword `0.8` 与 vector `0.9` 形成一条结果，`final_score=0.87`；两个 branch 都收到 `top_k * 2`；metadata 能从提供它的 branch 进入输出 | keyword/vector retriever 都是 Mock；不验证真实 T0602/T0701 串接，也不验证底层 vector store 的二次 `×2` 召回 |
| `test_low_keyword_only_match_is_removed_by_relevance_filter` | keyword-only `0.6` 会计算成 `0.18`，低于 `0.30` 后返回空列表 | 通过最终空结果间接证明 filter；没有单独暴露 pre-filter map |
| `test_relevance_filter_runs_before_top_k` | 低分候选与 5 个 vector 候选混合时，最终 `top_k=3` 是最高的 `high-4/high-3/high-2`，不是先切片再过滤 | fixture 是小规模 2+5，不是 SPEC 示例的 20 条真实 corpus；证明顺序，不证明 latency/recall |
| `test_same_chunk_id_is_deduplicated_even_with_different_content` | 两个 payload 不同但 identity 相同仍只输出一条 | 证明 key 是 `chunk_id`；没有断言冲突 payload 的业务一致性策略 |

所以本轮可以诚实地说：T0702 的四个 AC 行为与 T0703 的三个 facade behaviors 在其 checkpoint 的 injected/patched unit boundary 有对应证据；T0801 的 context/source behaviors 另有 5 个 unit tests，T0802 的 history behaviors 另有 4 个 unit tests，T0803 的 client/prompt/retry/error behaviors 另有 12 个 unit tests，T0804 的 service orchestration behaviors 另有 4 个 Mocked tests，T0805 的 route/error-envelope behaviors 另有 10 个 route-level Mocked tests，`python -m compileall -q app tests` 通过；不能把这些证据升级为真实 upload → Chroma → hybrid query → DeepSeek、Frontend history integration 或 QA context/LLM 的集成 PASS。真实语义质量、metadata 完整性、history lifecycle、branch failure policy、provider latency/cost、facade 与真实 storage 的串接、QAService 与真实依赖的贯通仍需后续验证。[PROJECT FACT]

### 4.10 T0702 Interview Candidates（仅候选，不生成完整答案）

- **Technical point**：为什么 hybrid merge 必须用 `chunk_id`，而不能用 content 字符串？
- **Scoring question**：`0.8` 与 `0.9` 为什么得到 `0.87`；缺失 branch 的 score=0 会带来什么产品语义？
- **Ordering question**：为什么 relevance filter 必须发生在 final Top-K 之前？如果反过来会丢掉什么？
- **Composition question**：T0702 已经传 `top_k * 2`，为什么真实 VectorStore 路径还可能看到第二次 `×2`？测试为什么没有暴露它？
- **Boundary question**：HybridRetriever 输出 `metadata`，但 T0701 projection 没有 metadata；你会把补字段放在哪一层，依据是什么？
- **Python/TS question**：`dict` accumulator 与 TypeScript `Map<chunkId, accumulator>` 的共同点和类型安全差异是什么？

这些仍是 Task-level candidates；完整 30 秒/1–2 分钟回答、follow-ups 和 STAR 等 Phase-level assets 继续放在 [Interview Guide](./interview-notes/dx-rag-interview-guide.md) 的后续 consolidation，不在这里复制。

### 4.11 T0703 A. Code Understanding：`retrieve()` facade 如何组装模块

T0703 的代码很短，但它改变了调用方式：调用方只需要知道一个函数，而不必知道三个 retriever 的创建顺序。真实实现位于 [`qa.py:202-216`](../../backend/app/services/qa.py#L202-L216)。[PROJECT FACT]

```python
def retrieve(
    query: str,
    collection: str,
    top_k: int = settings.DEFAULT_TOP_K,
) -> List[Dict[str, object]]:
    """Run the complete keyword/vector hybrid retrieval pipeline."""
    vector_store = ChromaVectorStore()
    if vector_store.get_chunk_count(collection) == 0:
        return []

    keyword_retriever = KeywordRetriever(vector_store)
    vector_retriever = VectorRetriever(vector_store)
    hybrid_retriever = HybridRetriever(keyword_retriever, vector_retriever)
    return hybrid_retriever.hybrid_search(query, collection, top_k)
```

按 control flow 拆开看：

1. **选择 storage implementation**：facade 创建一个 `ChromaVectorStore`。这是 composition root 的一个很小版本：T0703 需要决定生产路径使用哪个 `VectorStore` implementation，但后续 retriever 仍只接收 `VectorStore` public interface。
2. **先做 chunk-count preflight**：调用 public `get_chunk_count(collection)`。如果结果是 `0`，立即返回 `[]`，因此不会创建三个 retriever，也不会触发 query embedding 或 keyword index build。
3. **共享同一 store instance**：`KeywordRetriever(vector_store)` 与 `VectorRetriever(vector_store)` 收到同一个对象。前者之后通过 `list_chunks()` 读全量 chunk，后者通过 `search()` 做向量查询；两种访问都经过 public interface。
4. **组装 orchestration chain**：把两个 branch 注入 `HybridRetriever`，由 T0702 负责 `chunk_id` merge、weighted fusion、filter 与 Top-K。
5. **只做一次 delegation**：facade 原样传递 `query`、`collection`、`top_k`，返回 Hybrid 的结果，不再复制 score 计算或重新排序逻辑。

这段代码的关键不是“new 了几个 class”，而是把**创建责任**与**运行责任**分开：`retrieve()` 负责 wiring，三个 retriever 负责各自 mechanics。它避免了调用方写出一套容易漂移的手工组装流程。[PROJECT FACT]

### 4.12 T0703 B. Project Understanding：统一入口的边界是什么

T0703 兑现的是“retrieval module 可被 QA 层消费”的 Python-level contract，而不是完整问答产品：

| 边界 | T0703 当前行为 | 没有做什么 |
|---|---|---|
| storage selection | 选择 `ChromaVectorStore()` 作为真实 facade 的 backend | 没有把 `_client` 或 `_collection` 暴露给 retriever |
| collection preflight | `get_chunk_count()==0` 返回空列表 | 没有把空库改写成错误；`COLLECTION_EMPTY` 的 HTTP 语义仍由 API 层决定 |
| branch wiring | 同一个 store 注入 keyword/vector，再注入 Hybrid | 没有新增第二份 index、embedding model 或 vector store |
| result contract | 返回 Hybrid 的六字段结果 | 没有组装 context、sources、answer 或 `relevance_score` public API 字段 |
| failure policy | missing collection、embedding/storage 异常自然向上传播 | 没有在 facade 私自 catch、retry、fallback 或映射 HTTP error |

这里要特别区分两个容易混淆的句子：

- “有统一 `retrieve()`”现在是真的：`app.services.qa.retrieve` 已经存在，后续 QA service 可以导入它。
- “QA service / `/api/query` 已经工作”要拆开说：T0804 已实现 `QAService.answer()`，T0805 已实现 query router、request validation、response envelope 与统一错误映射；但 route tests 使用 Mocked storage/service，真实 provider/Chroma E2E 仍未完成。T0801/T0802/T0803 已由 T0804 消费，T0805 消费 T0804 result。[PROJECT FACT]

T0703 对 DOD-03 的实际落实也要按这个边界理解：它遵守已存在的 Python function/result contract，没有另造一套响应格式；但因为本 Task 没有创建 HTTP endpoint，所以不能把 DOD-03 写成 `/api/query` 的端到端 API 验收。[PROJECT FACT]

### 4.13 T0703 C. Learning Understanding：Facade、composition root 与短路路径

对 TypeScript/Node 学习者，可以把 T0703 先想成一个同步的 composition function：

```ts
type SearchResult = {
  chunk_id: string;
  file_id: string | null;
  file_name: string | null;
  content: string | null;
  final_score: number;
  metadata: Record<string, unknown>;
};

function retrieve(
  query: string,
  collection: string,
  topK = settings.DEFAULT_TOP_K,
): SearchResult[] {
  const store = new ChromaVectorStore();
  if (store.getChunkCount(collection) === 0) return [];

  const keyword = new KeywordRetriever(store);
  const vector = new VectorRetriever(store);
  return new HybridRetriever(keyword, vector).hybridSearch(
    query, collection, topK,
  );
}
```

这个类比能帮助理解三点：

1. `retrieve()` 是 **facade**：它隐藏 wiring 细节，给上层一个稳定函数。
2. `store` 是共享依赖：不是每个 retriever 都创建自己的 client；同一 request 的两个 branch 指向同一个 storage boundary。
3. `return []` 是 **short-circuit**：空 collection 是一个正常数据状态，提前结束可以避免无意义的 expensive work。

但 Python 与 TypeScript 仍有差异。当前 Python 返回值是 `List[Dict[str, object]]`，不是 compiler 可穷尽检查的 `SearchResult[]`；`top_k` 也没有在 facade 内验证 `[1,20]`。因此“有 facade”只解决了 wiring duplication，不自动解决 runtime schema、输入校验或真实依赖可用性。[ENGINEERING KNOWLEDGE]

一个可迁移的 mental model 是：**Facade 不拥有下游业务语义，它只把已经有契约的组件按正确顺序组装，并把正常短路与异常传播保留下来。** 看到类似函数时，先问：它创建了哪些 concrete dependency？哪些依赖被共享？什么状态会提前返回？什么异常没有被吞掉？

### 4.14 T0703 验证学习：wiring test 不等于 literal integration test

T0703 在当前 `test_qa.py` 中增加了 3 个 `RetrievalIntegrationTests`。虽然测试类名叫 Integration，但它们实际是**Mocked composition/wiring tests**：`ChromaVectorStore`、`KeywordRetriever`、`VectorRetriever` 与 `HybridRetriever` 都被 patch 或替换，没有启动真实 ChromaDB，也没有上传文本文件。[PROJECT FACT]

| 测试 | 它真正证明什么 | 证据边界 |
|---|---|---|
| `test_retrieve_wires_retrievers_through_one_store` | facade 创建一个 store；把同一个 store 注入 keyword/vector；再把两个实例交给 Hybrid；`hybrid_search` 收到原始参数并被 delegation | 没有证明真实 class 的行为、真实 Chroma persistence 或真实 embedding |
| `test_retrieve_empty_collection_returns_empty_list_without_embedding` | `get_chunk_count()==0` 后返回 `[]`，三个 retriever constructor 都不会调用 | store 是 Mock；不证明真实空 Chroma collection 的 count 行为 |
| `test_retrieve_propagates_missing_collection_error` | `get_chunk_count` 抛异常时，facade 不吞异常，原异常向上传播 | 使用 `RuntimeError` substitute；不证明 Chroma 的具体异常类型或 API error mapping |

因此当前 suite 的数字应按 checkpoint 解释：T0702 Learning Pass 时是 21/21；T0703 增加 3 个 facade tests 后是 **24/24**；T0801 再增加 5 个 context/source tests，成为 **30/30**；T0802 再增加 4 个 history tests，成为 **34/34**；T0803 再增加 12 个 DeepSeek client tests，成为 **46/46**；T0804 再增加 4 个 QAService tests，成为 **50/50**；T0805 再增加 10 个 query endpoint tests，当前是 **60/60**（6 tokenizer + 7 keyword + 4 vector + 5 hybrid + 3 retrieval facade + 5 context/source + 4 history + 12 DeepSeek client + 4 QAService + 10 query endpoint）。这证明了各层 module-level/route-level observable behavior，不证明 Task 描述中的 literal “text file uploaded → query → merged”、真实 provider answer、Frontend history lifecycle 或完整 QA context/LLM 链路。[PROJECT FACT]

T0703 的真实集成验证仍需要：真实 `ChromaVectorStore`、已入库的 text chunk、可用 embedding model（或明确的 test substitute）、keyword index lifecycle、VectorStore query，以及对最终 merge 结果的断言。按当前任务边界，这类 upload → real Chroma → query 验证继续归后续集成验收范围，而不是把 Mock wiring test 升级成 E2E PASS。

### 4.15 T0703 Interview Candidates（仅候选，不生成完整答案）

- **Facade question**：为什么 `retrieve()` 要先做 `get_chunk_count()`，而不是直接让两个 retriever 返回空列表？
- **Dependency question**：为什么 keyword 与 vector retriever 必须共享同一个 `VectorStore` instance？共享的是对象、接口还是 state？
- **Boundary question**：T0703 已有 `retrieve()`，为什么仍不能说 `/api/query` 或 QA Service 已完成？
- **Failure question**：missing collection 为什么应该传播，而 empty collection 为什么返回 `[]`？这两个状态在 API 层如何继续区分？
- **Evidence question**：为什么 `RetrievalIntegrationTests` 仍只能算 Mocked wiring evidence？要满足 literal integration 还缺什么真实依赖？

这些仍是 Task-level candidates；完整回答、STAR 与 Phase-level retrieval story 等待 Phase Gate 与 Phase Learning Review consolidation。

## 5. 代码理解：close reading

### 5.1 模块依赖：service 只拿它需要的 public contract

[`qa.py:3-8`](../../backend/app/services/qa.py#L3-L8) 的关键 import 是：

```python
from typing import Callable, Dict, List, Optional, Set

from app.core.config import settings
from app.core.vector_store import ChromaVectorStore, ChunkRecord, VectorStore
from app.services.embedding import encode_chunks
```

- `Callable` 让 constructor 能描述“任何可把文本 batch 编成 vectors 的函数”。这比在 class 内硬编码模型更容易替换和测试。
- `settings` 只提供默认 `top_k`；它不把 retriever 变成 configuration singleton。
- `VectorStore` 是 retriever 使用的 abstract public interface。T0701/T0702 不 import concrete backend；T0703 的 `retrieve()` 作为 composition facade 才选择 `ChromaVectorStore`，然后把它以 `VectorStore` 能力传给下游。
- `encode_chunks` 是已经存在的 embedding owner；T0701 不复制模型加载、lazy singleton 或 normalization 逻辑。
- `ChunkRecord` 仍被 keyword branch 使用；它不意味着 vector branch 可以绕过 `VectorSearchResult`。

这里的设计意图大于 import 语法：retriever 依赖能力（embed + search），不依赖具体基础设施实现；只有最外层 facade 负责 concrete implementation selection。

### 5.2 Constructor：Dependency Injection 让边界可观察

真实代码 [`qa.py:90-96`](../../backend/app/services/qa.py#L90-L96)：

```python
def __init__(
    self,
    vector_store: VectorStore,
    embedder: Callable[[List[str]], List[List[float]]] = encode_chunks,
) -> None:
    self.vector_store = vector_store
    self.embedder = embedder
```

逐行理解：

1. `vector_store` 是必需依赖，因为没有它就不能查 collection。
2. `embedder` 默认指向项目已有的 `encode_chunks`，所以生产路径不需要额外 wiring。
3. 测试可以传入 `Mock(return_value=[[...]])`，观察 query 是否按 batch shape 传入；这就是 dependency injection（DI）带来的 seam。
4. `self.*` 把依赖保存到 instance state，但没有共享 cache 或副作用；同一个 instance 可重复查询不同 collection。

TypeScript 类比是 constructor injection：

```ts
constructor(
  private store: VectorStore,
  private embedder: Embedder = encodeChunks,
) {}
```

但要注意 Python default expression 在函数定义时绑定默认对象；这里默认的是函数引用，不是每次调用都重新加载 model。model 的 lazy lifecycle 仍由 `embedding.py:get_model()` owner 负责，而不是由 constructor 管理。[ENGINEERING KNOWLEDGE]

### 5.3 `vector_search()`：四个转换点

真实代码 [`qa.py:98-117`](../../backend/app/services/qa.py#L98-L117)：

```python
def vector_search(
    self,
    query: str,
    collection: str,
    top_k: int = settings.DEFAULT_TOP_K,
) -> List[Dict[str, object]]:
    """Embed a query and return VectorStore similarity as vector_score."""
    query_vector = self.embedder([query])[0]
    search_results = self.vector_store.search(collection, query_vector, top_k * 2)

    return [
        {
            "chunk_id": result.chunk_id,
            "file_id": result.file_id,
            "file_name": result.file_name,
            "content": result.content,
            "vector_score": result.similarity_score,
        }
        for result in search_results[:top_k]
    ]
```

#### 转换点 1：`[query]` 是 batch adapter

`encode_chunks()` 接收 `List[str]`，而用户只给一条 `str`。`[query]` 将单条请求转换成长度为 1 的 batch；返回值因此是二维 `List[List[float]]`，`[0]` 再取出本次 query 的一维向量。它不是“多余的数组”，而是把单条 service 输入适配到可批量化的 embedding API。

TypeScript 中这类似于把 `string` 送进 `embedMany([query])`，再取 `vectors[0]`。如果未来需要 batch query，embedding owner 的 shape 不需要重写；但当前 service method 仍然是一次处理一个 query。

#### 转换点 2：`top_k * 2` 是召回策略，不是最终输出数量

store 先拿两倍候选，retriever 再 `[:top_k]`。在当前单 branch 中，这看起来像额外工作；在 F011 的目标 pipeline 中，两条 branch 各自扩大召回后才有足够候选进行 merge、fusion、filter 和最终 Top-K。T0701 只实现这条下游可复用的召回契约，不提前实现 hybrid。

#### 转换点 3：直接透传 `similarity_score`

F008 的 storage boundary 已经做了：

```text
raw distance → clamp(1.0 - distance, 0.0, 1.0) → similarity_score
```

因此这里使用 `result.similarity_score`，只做命名转换，不做 min-max、除法或二次 clamp。若这里“看起来更严谨”地再归一化一次，实际上会改变分数尺度，破坏 F011 要求的 `keyword_score` / `vector_score` 可比较前提。

#### 转换点 4：输出投影与 slice

list comprehension 将 Pydantic `VectorSearchResult` 投影为更小的 plain dict，并通过 `search_results[:top_k]` 保留前 `top_k`。这里依赖 F008 的排序契约：store 返回结果按 `similarity_score` descending。Python slice 对短列表是安全的，所以 empty collection 自然得到 `[]`，不需要额外分支。[PROJECT FACT]

### 5.4 Storage boundary：为什么要读 `VectorStore.search()`

在 [`vector_store.py:480-523`](../../backend/app/core/vector_store.py#L480-L523)，真实 Chroma implementation 负责：

```python
raw = self._client.get_collection(collection).query(
    query_embeddings=[query_vector],
    n_results=top_k,
    include=["documents", "metadatas", "distances"],
)
...
similarity_score=max(0.0, min(1.0, 1.0 - distance))
...
results.sort(key=lambda r: r.similarity_score, reverse=True)
```

这个片段展示了 ownership：`_client` 和 raw distance 留在 storage 内部；service 只看 `VectorSearchResult`。`VectorSearchResult` 的 public schema 在 [`vector_store.py:62-78`](../../backend/app/core/vector_store.py#L62-L78)，其中 `similarity_score` 被定义为 `[0, 1]`、越大越相关。T0701 的代码没有接触 `_client`、`_collection` 或 Chroma query result 的 private shape。[PROJECT FACT]

### 5.5 Failure path 与当前边界

这是对实际 control flow 的诚实阅读，而不是把没有测试的路径写成“已处理”：

| 位置 | 当前行为 | 证据/边界 |
|---|---|---|
| `self.embedder([query])[0]` | 若 embedder 返回空 list，会触发 `IndexError`；正常 `encode_chunks([query])` 对非空 query 返回一个 vector | 当前 T0701 没有空 embedding result guard；应由上游 contract 或未来边界决策处理 |
| `encode_chunks()` | model 首次使用时 lazy load；加载失败向上抛 `EMBEDDING_MODEL_ERROR` | F007/Phase 2 owner；T0701 不吞异常、不重试 |
| `VectorStore.search()` | storage/backend 异常向上冒泡 | 当前 service 没有把异常改写成另一种错误码 |
| `top_k` | default 来自 config；class 内没有 min/max validation | 当前调用边界的验证责任尚未在 T0701 建立；不要声称 retriever 已校验非法值 |
| empty store result | list comprehension 产出 `[]` | 由 `test_empty_collection_returns_empty_list` 在 Mock store boundary 覆盖 |

对 learner 来说，重点是区分“异常会自然传播”与“异常已经有专门 handling”。没有专门的 `try/except` 就不要脑补 rollback、retry 或 fallback。

#### T0703 facade 的两个分流点

`retrieve()` 把空 collection 与 missing collection 分成两条不同的 control-flow：

- `get_chunk_count(collection) == 0` 是正常数据状态，返回 `[]` 并短路后续 embedding/index/search；
- `get_chunk_count()` 本身抛异常（例如 collection 不存在）时，facade 没有 `try/except`，所以异常继续向调用方传播。

这不是把两种情况都“转成空列表”的便利包装。空库可以让 QA 层决定如何处理 empty retrieval；缺失 collection 则保留 infrastructure/error signal，供更高层做错误映射。当前 T0703 没有实现这种 HTTP 映射，也没有声明 Chroma 的具体异常类型。[PROJECT FACT]

### 5.6 `HybridRetriever`：把两个 branch 编排成一个 result

真实代码位于 [`qa.py:120-199`](../../backend/app/services/qa.py#L120-L199)：

```python
class HybridRetriever:
    """Merge keyword and vector retrieval results with weighted scoring."""

    def __init__(
        self,
        keyword_retriever: KeywordRetriever,
        vector_retriever: VectorRetriever,
        weights: Optional[List[float]] = None,
    ) -> None:
        self.keyword_retriever = keyword_retriever
        self.vector_retriever = vector_retriever
        self.keyword_weight, self.vector_weight = weights or [0.3, 0.7]

    def hybrid_search(
        self,
        query: str,
        collection: str,
        top_k: int = settings.DEFAULT_TOP_K,
    ) -> List[Dict[str, object]]:
        """Fuse both retrieval branches, filter, and return the top results."""
        expanded_top_k = top_k * 2
        keyword_results = self.keyword_retriever.keyword_search(
            collection, query, expanded_top_k
        )
        vector_results = self.vector_retriever.vector_search(
            query, collection, expanded_top_k
        )

        merged: Dict[str, Dict[str, object]] = {}
        for branch_results, score_key in (
            (keyword_results, "keyword_score"),
            (vector_results, "vector_score"),
        ):
            for result in branch_results:
                chunk_id = result["chunk_id"]
                if chunk_id not in merged:
                    merged[chunk_id] = {
                        "chunk_id": chunk_id,
                        "file_id": result.get("file_id"),
                        "file_name": result.get("file_name"),
                        "content": result.get("content"),
                        "metadata": result.get("metadata") or {},
                        "keyword_score": 0.0,
                        "vector_score": 0.0,
                    }

                entry = merged[chunk_id]
                score = float(result.get(score_key) or 0.0)
                entry[score_key] = max(float(entry[score_key]), score)
                if entry["metadata"] == {} and result.get("metadata"):
                    entry["metadata"] = result["metadata"]

                for field in ("file_id", "file_name", "content"):
                    if entry[field] is None and result.get(field) is not None:
                        entry[field] = result[field]

        results = []
        for entry in merged.values():
            final_score = (
                float(entry["keyword_score"]) * self.keyword_weight
                + float(entry["vector_score"]) * self.vector_weight
            )
            results.append(
                {
                    "chunk_id": entry["chunk_id"],
                    "file_id": entry["file_id"],
                    "file_name": entry["file_name"],
                    "content": entry["content"],
                    "final_score": final_score,
                    "metadata": entry["metadata"],
                }
            )

        results.sort(key=lambda result: result["final_score"], reverse=True)
        results = [
            result
            for result in results
            if result["final_score"] >= settings.MIN_RELEVANCE_SCORE
        ]
        return results[:top_k]
```

#### 读取 1：constructor 先固定依赖，再固定权重

`keyword_retriever` 与 `vector_retriever` 是 constructor injection。HybridRetriever 不自己 new 两个 concrete implementation，所以测试可以用两个 Mock 观察调用；生产代码则可以传入真实 retriever。`weights or [0.3, 0.7]` 表达的是默认值选择，不是完整的 configuration validation：`None` 或空 list 使用默认值，长度不为 2 的 list 会在 unpack 时失败，负数、超过 1 或总和不为 1 的权重目前不会被拒绝。[PROJECT FACT]

这和 TypeScript 的 `constructor(private keyword: KeywordRetriever, private vector: VectorRetriever, private weights: [number, number] = [0.3, 0.7])` 很像；差异在于 Python 的 `List[float]` 只写了意图，runtime 不会自动 enforce tuple length 或 value range。[ENGINEERING KNOWLEDGE]

#### 读取 2：`expanded_top_k` 是 orchestration policy

`expanded_top_k = top_k * 2` 只计算一次，再传给两个 branch。关键词方法的签名是 `(collection, query, top_k)`，向量方法的签名是 `(query, collection, top_k)`，所以两行调用看起来不对称却是按真实 API 写的。F011 允许 parallel 或 sequential；这里没有 thread、async task 或 `gather`，执行顺序就是 keyword 完成后再 vector。

组合时需要沿着调用链继续读：关键词 branch 直接把收到的 `expanded_top_k` 用作结果切片；vector branch 把收到的值再次乘 2 传给 `VectorStore.search()`，再切回自己的 `top_k`。因此 `HybridRetriever(top_k=5)` → vector method 收到 10 → store 可能收到 20。这个二次扩展是当前实现组合出来的行为，unit test 只 mock 了 vector retriever，故只观察到第一层 10。[PROJECT FACT]

#### 读取 3：merge map 同时承担 identity、fallback 和冲突防御

`merged` 的 key 是 `chunk_id`，value 是一个尚未完成的 accumulator。第一次见到 chunk 时，代码把 payload 字段拷贝进去、两个 score 初始化为 0，并把缺失 metadata 变成 `{}`。这样只命中 keyword 或只命中 vector 的 chunk 仍然有一个完整的 accumulator，未出现的 branch 自然保持零分。

再次遇到相同 `chunk_id` 时：

- `max(existing, score)` 选择该 branch 看到的最高分，避免同一 branch 的重复记录把分数相加；
- metadata 只有在当前还是空 dict 且新结果提供了 metadata 时才补入；
- `file_id`、`file_name`、`content` 只在已有值为 `None` 时补齐，不会静默覆盖第一个非空 payload。

这是“按 identity 合并”而非“按 content 合并”。它也意味着不一致 payload 不会被自动报错：同一个 `chunk_id` 如果来自两个不同文件，当前代码会保留第一次的非空字段，同时仍合并 score。该一致性假设需要上游 `chunk_id` contract 与更高层验证守护。[PROJECT FACT]

#### 读取 4：`float(... or 0.0)` 把缺失 score 变成可计算值

`result.get(score_key)` 允许某个 branch 不提供对应 score；`None` 或其他 falsy 值会落到 `0.0`，再用 `float()` 统一成可乘的 numeric value。它不是范围校验：字符串数字可能被转换，非数字会抛 `ValueError`/`TypeError`，`-1` 或 `2` 也不会在这里被 clamp。F009/F010 的 `[0, 1]` contract 是这里的前置条件，而不是这段代码重新建立的保证。

#### 读取 5：先生成 final score，再排序、过滤、截断

第二个 loop 把 accumulator 投影成最终字典，并只输出 SPEC F011 要求的六个字段。`final_score` 使用 constructor 中的两个权重；默认值给出 `0.3 * keyword_score + 0.7 * vector_score`。接着 `sort(..., reverse=True)` 先建立 descending order，列表推导式保留 `>= settings.MIN_RELEVANCE_SCORE` 的记录，最后 `[:top_k]`。

这三个动作不能交换：

```text
merge → score → sort → relevance filter → top_k slice
```

如果先 slice，低分候选可能占据名额，高分候选会在 filter 前被丢掉；如果先 filter 每个 branch，再 merge，则会误删“单 branch 分数低、合并后足够高”的 chunk。当前代码遵守 F011 的“扩大召回 → 融合 → 过滤 → 截断”意图；`sort` 位于 filter 之前，但因为 filter 只删除元素，不改顺序，所以输出仍保持 descending。[PROJECT FACT]

#### 读取 6：输出 metadata 与真实上游 shape 之间存在缝隙

HybridRetriever 的输出总是有 `metadata` key；初始化时没有 metadata 就是 `{}`。但 T0701 的 vector projection 只输出五个字段，keyword branch 也只输出五个字段，所以真实 T0602/T0701 组合没有 metadata 来源。测试中手工给 vector Mock 加了 `{"source": "vector"}`，只是验证 merge 逻辑能保留可用 metadata，不是证明真实 VectorStore metadata 已贯通。若 F012/F015 需要来源字段，应先更新 service contract 和上游 projection，再决定字段 owner；不能绕过 public interface 直接读取 Chroma private object。[PROJECT FACT]

## 6. 数据流与 Mental Model

### 6.1 完整数据流

```text
retrieve(query: str, collection: str, top_k: int)
  │
  ├─ ChromaVectorStore()
  │    └─ get_chunk_count(collection)
  │          ├─ 0 → []（short-circuit）
  │          └─ >0 → shared store passed to all retrievers
  │
  ├─ default top_k ← settings.DEFAULT_TOP_K（未传时）
  │
  ├─ expanded_top_k = top_k * 2
  │    │
  │    ├─ KeywordRetriever.keyword_search(collection, query, expanded_top_k)
  │    │    └─ List[{chunk_id, ..., keyword_score}]
  │    │
  │    └─ VectorRetriever.vector_search(query, collection, expanded_top_k)
  │         ├─ [query] → encode_chunks() → query_vector
  │         ├─ VectorStore.search(..., expanded_top_k * 2)  # T0701 再扩展
  │         └─ List[{chunk_id, ..., vector_score}]
  │
  ▼
merged: Dict[chunk_id, accumulator]
  │  union identity；缺失 score = 0；同 branch 重复取 max
  ▼
final_score = keyword_score * 0.3 + vector_score * 0.7
  │
  ▼
sort DESC → keep final_score >= MIN_RELEVANCE_SCORE (0.30)
  │
  ▼
results[:top_k]
  │
  ▼
List[{chunk_id, file_id, file_name, content, final_score, metadata}]
```

### 6.2 类型变化

| 阶段 | 类型 | 发生了什么 |
|---|---|---|
| facade 输入 | `str` + `str` + `int` | query、collection 与期望的最终 Top-K |
| storage preflight | `ChromaVectorStore` → `int` | `get_chunk_count()` 决定 short-circuit 还是继续组装 |
| branch 调用参数 | `int` | T0702 先变成 `expanded_top_k = top_k * 2` |
| keyword branch | `List[Dict[str, object]]` | `keyword_score` 与 chunk identity |
| embedding 输入 | `List[str]` | VectorRetriever 把单条 query 包装为 batch |
| embedding 输出 | `List[List[float]]` | 每个文本对应一个向量，取第一个 |
| vector branch | `List[Dict[str, object]]` | `vector_score` 与 chunk identity；真实路径底层还会再请求 2 倍 |
| merge state | `Dict[str, Dict[str, object]]` | key 是 `chunk_id`，value 保存两种 score 与 payload |
| final service 输出 | `List[Dict[str, object]]` | `final_score`、`metadata`、过滤后按分数降序的结果 |

### 6.3 失败出口

```text
empty collection (count=0) ────→ []（facade short-circuit）
missing collection ────────────→ get_chunk_count exception propagation
empty embedding batch ─────────→ [当前未 guard] IndexError（VectorRetriever）
model load failure ────────────→ AppError(EMBEDDING_MODEL_ERROR)
branch/storage exception ──────→ exception propagation（facade/Hybrid 不 catch）
missing chunk_id ──────────────→ KeyError
missing/non-numeric score ─────→ 0.0 fallback / float conversion error
invalid weights length ────────→ unpack ValueError
empty keyword + vector results → []
invalid top_k/weight range ────→ 当前没有专门 validation
```

### 6.4 Mental Model

把 T0703 记成一个**保留边界的 composition facade**，把 T0702 记成其中的 **identity-preserving rank fusion orchestrator**，把 T0701 记成它里面的 **score-preserving adapter**：

> T0701 把“人类问题”转换成“可查询的向量”，把 storage 的“已排序相似度”转换成 `vector_score`；T0702 再把 keyword/vector 的 evidence 按不可变 `chunk_id` union，补齐缺失分支的零分，计算统一的 `final_score`，先过滤噪声再截断 Top-K；T0703 最后创建共享 storage、完成 empty-collection short-circuit，并把整条 retrieval chain 暴露为 `retrieve()`。它不重新发明 embedding、距离或 RRF，也不假装已经接到 HTTP QA。

这个 mental model 比记住一串函数名更有用。以后看到任何 retrieval pipeline，都可以问四件事：谁生成 evidence？谁拥有 score semantics？谁决定 identity merge？谁决定 filter 与最终返回多少条？

## 7. 架构设计：新增能力与刻意保留的边界

### 7.1 新增能力

| 能力 | 生产者 | 当前消费者 |
|---|---|---|
| query semantic retrieval | `VectorRetriever.vector_search()` | T0702 hybrid branch；当前仍由 tests 观察 |
| `vector_score` service contract | result projection | `HybridRetriever` weighted fusion |
| expanded candidate recall | T0702 branch call + T0701 vector-store call | merge/filter 前的候选空间 |
| `final_score` hybrid contract | `HybridRetriever.hybrid_search()` | T0702 tests；T0703 facade delegates；T0801 consumes the ranked result for context/source projection |
| relevance filter + final Top-K | `settings.MIN_RELEVANCE_SCORE` + list slice | T0702 tests；T0801/T0802/T0803/T0804 消费这条 retrieval contract；T0805 通过 T0804 接到 HTTP |
| unified retrieval facade | `retrieve(query, collection, top_k)` | T0703 已实现独立 Python entry point；T0804/T0805 当前直接走 HybridRetriever path，不复用 facade |

这不是完整真实 QA 能力。当前已经有 module-level `retrieve()` entry point、T0801/T0802 converters、T0803 DeepSeek client、T0804 `QAService` orchestration 与 T0805 `/api/query` adapter；但没有证据显示真实 provider、真实 storage 或 upload → query 已贯通，这些仍属于后续 Phase。[PROJECT FACT]

### 7.2 契约链

```text
F007 encode_chunks
  → F010 VectorRetriever
  → F011 HybridRetriever
  → T0703 retrieve() facade
  → T0801 F012 Context Assembly
  → T0802 F014 History Processing
  → T0803 F013 LLM Answer Generation
  → T0804 QAService orchestration
  → T0805 HTTP endpoint
```

Phase 6 的 `keyword_score` 与 T0701 的 `vector_score` 是进入 F011 的两个同尺度输入；每个箭头都是一个可观察的 contract boundary：输入类型、score name、identity、排序语义和失败责任都要明确。T0702 冻结 merge/fusion/filter 的 service behavior，T0703 再把共享 store 与三个 retriever 组装成一个 facade；T0801/T0802 已分别提供 context/source/history converters，T0803 已提供 DeepSeek prompt/client/retry adapter，T0804 已实现 QAService 的 service-level orchestration，T0805 已完成 HTTP 接线，但 route 的真实依赖与 upload → query 仍未验证。

### 7.3 设计取舍摘要

- 用共享 `encode_chunks`：避免 embedding model loading/normalization drift。
- 用 constructor injection：默认生产函数不变，T0702 测试可替换两个 ranker。
- 用 `top_k * 2`：为融合扩大候选；注意 T0701 vector method 的下层 store 还会再次扩大。
- 透传 `similarity_score`：保持 F008 的 score ownership，禁止 double normalization。
- 按 `chunk_id` 使用 accumulator map：同一 chunk 的两种 evidence 合成一条结果，禁止 content-based dedup。
- 先算/排序/过滤再 slice：落实 F011 的 relevance threshold 与最终 Top-K 顺序。
- 输出 `metadata` 但允许 `{}`：保持 F011 shape，同时诚实暴露 T0701 projection 尚未传 metadata 的缝隙。
- 由 `retrieve()` 做 composition：共享一个 `ChromaVectorStore`，先用 `get_chunk_count()` 处理空库，再把真实 store 注入三个 retriever。

完整 ADR、failure taxonomy 与 scale analysis 在 [Engineering Review](./engineering-review/phase-07-engineering-review.md) 维护，本文不重复展开。

## 8. Engineering Review 摘要

本次增量 Engineering Review 的结论是：T0701 的主要工程价值是把 embedding、storage similarity 与 vector result shape 分开；T0702 的主要工程价值是把两个 ranker 以 `chunk_id` identity 合成一个有阈值的结果 contract；T0703 的主要工程价值是把这些组件组成一个可导入的 retrieval facade，并保留 empty/missing collection 的不同语义。DI、public interface isolation、score pass-through、expanded recall、fixed weighted fusion、filter-before-top-k 与 facade short-circuit 是当前最关键的决策。

评审文档还记录了：

- 当前错误与 validation ownership；
- empty result、embedding failure、storage exception 的 failure boundary；
- 单次 query 的调用成本、T0701/T0702 组合后的二次召回与 `top_k * 2` 取舍；
- duplicate payload、metadata continuity、weight/top_k validation 与 error propagation 的 Known Gaps；
- 多 worker、真实 model/Chroma E2E、T0703 facade 的 literal integration 与后续 QA wiring 等仍未完成的边界。

请在需要工程判断、规模推演或完整 ADR 时阅读 [Phase 7 Engineering Review](./engineering-review/phase-07-engineering-review.md)，不要把本章的学习摘要当成完整 review。

## 9. Technical Decision：当前实现为什么这样写

| 决策 | 备选 | 选择理由 | 当前代价/边界 |
|---|---|---|---|
| 复用 `encode_chunks` | 在 retriever 内直接实例化模型 | Embedding singleton、normalize 与错误码已有 owner | retriever 依赖上游函数契约；模型替换要遵守同一 shape |
| 注入 `embedder` | 测试时 monkey-patch 全局 model | seam 明确，测试不需要真实模型，依赖可观察 | 当前测试不能证明真实模型质量 |
| `[query]` → `[0]` | 为单条 query 另写一套 embedding API | 复用 batch API，未来可扩展 batch | 空返回会在 `[0]` 处暴露为异常，当前没有专门 guard |
| storage 请求 `top_k * 2` | 只请求最终 `top_k` | 给后续 merge/filter 更多候选 | 单 branch 可能多做一次 storage work；最终仍截断 |
| `vector_score = similarity_score` | 在 service 再 min-max | F008 已完成距离转换，保持 score scale 一致 | 依赖 F008 的 similarity contract 与范围保证 |
| service dict 只保留五个字段 | 原样返回完整 Pydantic metadata | 与 keyword branch shape 对齐，减少耦合 | 下游若需要 metadata，需在后续 contract 中明确补回 |
| 默认 `settings.DEFAULT_TOP_K` | 每次调用都要求显式 top_k | 与项目 config contract 对齐 | retriever 本身不负责范围 validation |
| `HybridRetriever` 注入两个 ranker | 在 hybrid 内部 new concrete retriever | 测试可替换依赖，orchestrator 只负责组合 | facade 仍需负责 concrete store selection；T0805 route 通过 T0804 path 接入，但不复用 facade |
| 用 `chunk_id` accumulator merge | append 后按 content 去重 | identity 稳定，双命中只产生一条结果；同 branch 重复取最高分 | 冲突 payload 不会自动报错，需要上游 identity contract |
| 固定 `[0.3, 0.7]` weighted sum | RRF 或 dynamic weighting | 直接兑现 F011，分数可解释、实现小 | 没有 weight range/sum validation，也没有质量 benchmark |
| filter 后再 `[:top_k]` | 每个 branch 先截最终数量或先切片再过滤 | 低分噪声不占名额，保留融合后才变高的候选 | 当前阈值与顺序有 unit evidence，真实检索质量未测量 |
| 顺序执行 keyword → vector | `asyncio.gather` 并行 | F011 允许顺序；当前同步依赖和错误传播更直接 | wall-clock latency 未 benchmark，不能声称已并行 |
| `retrieve()` 先 `get_chunk_count()` | 让每个 branch 自己处理空库 | 空 collection 直接返回 `[]`，避免无意义 embedding/index work；missing collection exception 保留 | concrete `ChromaVectorStore` 在 facade 内选择；真实 empty/missing Chroma 行为未做 E2E |

这些是当前代码可直接观察到的 decisions；T0702 的 merge/fusion/filter、T0703 的 module-level facade、T0804 的 service-level orchestration 与 T0805 的 HTTP adapter 已实现，但真实依赖端到端行为仍不是当前承诺。

## 10. Interview Notes 路由

本 Task 只新增候选素材，不提前生成完整面试答案：

1. 解释 `similarity_score` 与 `vector_score` 的 ownership boundary。
2. 解释 `top_k * 2` 的 expanded recall 为什么在 hybrid pipeline 有意义。
3. 解释 `Callable` / constructor DI 如何让真实依赖与 Mock 依赖共享同一 service control flow。
4. 解释 `chunk_id` accumulator 如何合并双命中、处理缺失 score 与避免 content-based dedup。
5. 解释 `final_score`、`MIN_RELEVANCE_SCORE` 与 Top-K 的顺序，以及为什么阈值相等仍保留。
6. 诚实说明 T0701/T0702/T0703 unit tests 没有覆盖的 real model、real Chroma、metadata 完整贯通、literal upload → query、HTTP QA 和并发行为。

候选的完整晋升路径是：T0701/T0702/T0703 Task Learning Pass → Phase Gate Review → Phase Learning Review → 更新项目级 [Interview Guide](./interview-notes/dx-rag-interview-guide.md)。当前 Phase 7 尚未满足这个 consolidation 条件，因此本文不写 30 秒稿、1–2 分钟稿或 STAR。

## 11. Future Improvement：未来边界

| 方向 | 为什么需要 | 当前状态 | 可能的 owner |
|---|---|---|---|
| Hybrid merge/fusion | 按 `chunk_id` 合并 keyword/vector 并计算 `0.3/0.7` final score | T0702 已实现；当前有 injected unit evidence | Phase 7 / F011 |
| Relevance Filter + final Top-K | 去掉 `final_score < MIN_RELEVANCE_SCORE` 的噪声 | T0702 已实现；当前阈值为 0.30，filter 后再 slice | Phase 7 / F011 |
| Retrieval facade wiring | 让两条 branch 由同一个 module-level 查询入口消费 | T0703 已实现 `retrieve()`；T0804/T0805 直接走 HybridRetriever path，route-level HTTP evidence 已有但不复用 facade | Phase 7 / T0703 |
| HTTP query adapter | 将已编排的 QA result 暴露为稳定的 request/response/error contract | T0805 已实现 `/api/query` 与 10 个 route-level Mocked tests；真实 provider/Chroma/upload E2E 仍 deferred | Phase 8 / T0805 |
| Literal upload → retrieval integration | 验证摄取、持久化与 facade 的真实串接 | `[FUTURE]` / DEFERRED；当前 3 个 T0703 tests 是 Mocked wiring | Phase 12/T1202 |
| Metadata continuity | 让真实 T0701 projection 的 metadata 能到达 F012/F015 | `[FUTURE]`；Hybrid 有 `{}` fallback，真实上游目前不提供 metadata | Phase 7/8 service contract |
| Weight/top_k validation | 防止非法权重、超范围 top_k 进入计算或 storage | `[FUTURE]`；当前 class 没有专门 guard | T0703/API boundary |
| Parallel branch scheduling | 在不改变错误/timeout 语义的前提下降低 wall-clock latency | `[FUTURE]`；当前顺序 keyword → vector | Phase 7/QA orchestration |
| Real semantic AC | 使用真实 bge-small-zh-v1.5、VectorStore 与数据验证 paraphrase match | `[FUTURE]` / DEFERRED；当前只有 Mock adapter evidence | 集成验证 / Phase 12 T1202 |
| Full upload → Chroma → query E2E | 验证 ingest、persistence、retrieval 的真实链路 | `[FUTURE]` / DEFERRED | Phase 12/T1202 范围 |
| Payload/schema validation | 防止非法 `chunk_id`、score 或 payload shape 进入融合 | 当前 Hybrid 依赖上游 contract，未实现专门 validation | 后续 service/API boundary，需先有明确 contract |
| Embedding failure policy | 明确 retry、timeout 或 provider fallback | 当前沿用 F007 `AppError` propagation | 需要产品/架构决策，不能在 T0701 猜测 |
| Ranking/latency benchmark | 用真实 corpus 评估 recall、latency、memory，尤其是 vector branch 的二次 `×2` | `[FUTURE]`，本次没有 benchmark | Phase 7/12 verification |

这些条目是明确的 Future，不代表当前代码已经拥有对应能力。

## 自测题与动手练习

请先遮住答案，尝试用自己的话推理；题目刻意覆盖 concept、code reading、predict behavior 和 design reasoning。

### Concept

1. 为什么 F008 的 `similarity_score` 是 `VectorStore` 的责任，而不是 `VectorRetriever` 的责任？如果两层都转换，会破坏什么？
2. `top_k * 2` 是“返回两倍结果”还是“向下游请求两倍候选”？当前代码最终返回多少条由哪一行决定？
3. 为什么 `encode_chunks` 的输入是 `List[str]`，而 `vector_search` 的输入是 `str`？这两个 shape 如何转换？
4. 什么是 dependency injection？本 Task 的 `embedder` 参数解决了哪一个测试问题？
5. “empty result 已测试”与“empty knowledge base 的真实 E2E 已验证”为什么不是同一句话？

### Code reading / behavior prediction

6. 若 `top_k=3`，Mock store 返回 6 个已排序结果，`vector_store.search` 应收到哪个整数，最终列表长度是多少？
7. 若 store 返回 `[]`，list comprehension 是否需要特殊 `if` 才能返回 `[]`？为什么？
8. 若 `VectorSearchResult.similarity_score=0.82`，service 输出的 `vector_score` 是多少？代码中是否有任何乘法或 normalization？
9. 若 embedder 被错误地写成返回 `[]`，代码会在哪一步失败？当前有没有 catch？
10. 为什么测试要断言 `store.search.assert_called_once_with(..., 10)`，而不只断言结果前三个 `chunk_id`？

### Design reasoning

11. 如果有人提议让 `VectorRetriever` 直接调用 `self.vector_store._collection.query(...)`，你会指出哪条架构边界被破坏？
12. 如果下一步实现 T0702，为什么应该保留 `vector_score` 这个名字，而不是在 T0701 中提前改成 `final_score`？
13. 如果真实 semantic AC 失败，你会先检查 query text、model version、stored embeddings、distance semantics 还是 hybrid weights？请按 ownership 顺序说明，不要把所有问题都归给 retriever。
14. 如果未来需要返回 metadata，应该直接把 storage 的全部 dict 泄漏出来，还是先更新 service contract？为什么？

### T0702 Hybrid Retrieval

#### Concept

15. keyword score=0.8、vector score=0.9 时，默认权重下 `final_score` 是多少？这个数值依赖哪两个 upstream 前提？
16. 一个 chunk 只出现在 keyword branch，另一个只出现在 vector branch；为什么两者都先进入 `merged`，而不是直接丢弃单 branch 命中？
17. 为什么 identity 必须是 `chunk_id` 而不是 content？请结合同一 chunk 的两个不同 payload 说明。
18. `final_score == MIN_RELEVANCE_SCORE` 时当前代码会保留还是删除？这对应 SPEC 的哪个比较关系？

#### Code reading / behavior prediction

19. `top_k=5` 时 T0702 传给两个 retriever 的参数分别是什么？如果 vector retriever 是当前 T0701 实现，VectorStore 最终收到多少？
20. 同一 branch 对同一 `chunk_id` 出现两个 score，代码为什么使用 `max()` 而不是累加？这个选择隐含了什么输入假设？
21. keyword result 没有 `metadata`，vector result 提供 `{"source": "vector"}`；最终 metadata 是什么？如果两个 branch 都没有呢？
22. `weights=[0.3]` 或 `weights=[0.3, 0.7, 0.0]` 会怎样？当前是否有友好的 domain error？
23. 如果 keyword retriever 抛出 storage exception，HybridRetriever 会返回空列表、尝试 vector fallback，还是直接向上传播？请从实际代码找证据。

#### Design reasoning

24. 为什么 `top_k` 不能在每个 branch 先截断后再 merge？请构造一个“单 branch 排名较低、融合后进入 Top-K”的例子。
25. F011 允许并行或顺序执行；当前实现选择了什么？如果改为并行，需要重新验证哪些 error/timeout semantics？
26. T0702 输出 `metadata`，但 T0701 projection 不输出它；你会在 VectorRetriever、HybridRetriever 还是 F012 source assembly 补字段？请先说明 contract owner。
27. 如果未来要换 RRF 或 dynamic weighting，哪些现有测试/契约可以保留，哪些 score assumptions 必须重新评估？

#### 小型动手练习（不改产品代码）

28. 用两个简单的 fake retriever 写一个小表：chunk A 双命中（0.8/0.9）、chunk B 仅 vector 命中（0.5）、chunk C 仅 keyword 命中（0.6）。手算三条 pre-filter `final_score`，判断哪些会被 0.30 filter 保留。
29. 把 fake vector retriever 替换成当前 `VectorRetriever`，记录 `top_k=2` 时 Hybrid → VectorRetriever → VectorStore 的每一级参数；解释为什么底层候选数不是直觉中的 4。
30. 写一个断言，证明两个不同 content 但相同 `chunk_id` 只产生一条结果；再写一个断言，证明 metadata 为空时输出仍有 `metadata={}`。
31. 设计一个尚未实现的 validation test：非法 `weights` 或负 `top_k` 应由哪个边界拒绝？只写测试意图，不把它写成当前代码已经 PASS。

### T0703 Retrieval Module Integration

#### Concept / boundary

32. `retrieve()` facade 解决了哪一种 wiring duplication？为什么它仍然不等于 `QAService` 或 `/api/query`？
33. 为什么 `retrieve()` 要选择 `ChromaVectorStore`，但 `KeywordRetriever` / `VectorRetriever` 仍然只依赖 `VectorStore` public interface？

#### Code reading / behavior prediction

34. `get_chunk_count(collection)` 返回 `0` 时，哪些 constructor 和 expensive operation 不会发生？
35. `get_chunk_count()` 抛出 missing-collection exception 时，facade 会返回 `[]`、转换错误，还是继续传播？请指出没有哪一个 `try/except`。
36. 为什么 T0703 的 `RetrievalIntegrationTests` 仍只能证明 Mocked wiring？要满足 literal “text file uploaded → query” 还需要哪些真实组件？

#### Design reasoning

37. 如果未来 QA Service 想传入 fake store 做测试，当前 `retrieve()` 的 concrete `ChromaVectorStore()` 选择会带来什么 seam trade-off？你会在哪个边界引入可注入 factory？
38. empty collection 与 missing collection 都没有结果，为什么仍要保留不同语义？它们在 API layer 可能对应什么不同处理？

### 小型动手练习（不改产品代码）

39. 在 Python REPL 中写一个 `fake_embedder(texts)`，断言它只收到 `['hello']`，并返回 `[[1.0, 0.0]]`；再用 `Mock(spec=VectorStore)` 返回两个 `VectorSearchResult`，手工预测 `top_k=1` 的 vector 结果。
40. 把 fake store 的返回顺序改成相似度 `[0.2, 0.9, 0.7]`，思考：当前 vector retriever 会不会自己排序？如果不会，哪个 upstream contract 必须保证顺序？
41. 写一个小表格记录一次 hybrid 调用的类型：`str`、`int`、branch dict、merge accumulator、final service dict；为每次转换写一句“谁负责”。
42. 设计一个尚未实现的 test case，专门说明“negative/zero top_k 或非法 weights 的 validation owner 还没有决定”，但不要把它写成当前代码已经 PASS。

## Quick Review

```text
Phase 7 current slice
  T0701 DONE        query → vector → VectorStore.search → vector_score
  T0702 DONE        chunk_id merge → weighted fusion → relevance filter → final Top-K
  T0703 DONE        retrieve() facade → shared ChromaVectorStore → keyword/vector/hybrid chain

T0701 + T0702 + T0703 mental model
  Input       query: str, collection: str, top_k (default config)
  Preflight   get_chunk_count == 0 → []；missing collection exception propagates
  Branches    keyword_score + vector_score（T0701 vector branch）
  Recall      T0702 先传 top_k * 2；真实 T0701 vector store 还会再 ×2
  Identity    Dict accumulator keyed by chunk_id；missing branch score = 0
  Fusion      final_score = 0.3 * keyword_score + 0.7 * vector_score
  Boundary    storage owns distance → similarity_score [0,1]
  Filter      keep final_score >= MIN_RELEVANCE_SCORE (0.30)
  Truncate    results[:top_k]（filter 之后）
  Facade     T0703 共享一个 store，创建三个 retriever 后 delegation 到 Hybrid
  Verified   4 vector + 5 hybrid + 3 facade + 5 context/source + 4 history + 12 DeepSeek + 10 query tests inside 60-test suite; compileall PASS
  Honest gap  facade/retriever/LLM/storage dependencies are Mocked or patched in tests; real upload→Chroma→DeepSeek→query/QA E2E DEFERRED
```

读完本章后，至少能够回答：

- query 为什么要先变成 batch-shaped input？
- 为什么 `VectorRetriever` 不接触 Chroma private API？
- 为什么 `0.82` 必须原样成为 `vector_score`？
- 为什么 `chunk_id` merge、relevance filter 与最终截断必须按固定顺序？
- 为什么 T0702 的 `top_k * 2` 与 T0701 的 vector-store `×2` 会叠加？
- `retrieve()` 如何区分 empty collection 与 missing collection？
- 当前测试到底验证了哪条 facade/hybrid 边界，哪条边界仍然需要真实依赖？

> **T0701 Learning Pass 记录（2026-08-28）**：本章先增量记录 query embedding、score ownership、expanded recall 与 DI 边界；当时 T0702/T0703 仍未实现。
>
> **T0702 Learning Pass 记录（2026-08-31）**：本章继续增量记录 HybridRetriever 的真实 merge/fusion/filter 代码、T0702 测试边界、metadata 与二次召回的已知缝隙。Phase 7 仍未完成；T0703 wiring、Phase Gate Review 与 Phase Learning Review 不能被本 Task 的文档替代。
>
> **T0703 Learning Pass 记录（2026-08-31）**：本章继续记录 `retrieve()` facade 的 shared-store wiring、empty-collection short-circuit、missing-collection exception propagation 与 3 个 Mocked composition tests。T0703 已完成 module-level integration，但 literal upload → real Chroma → query、QA endpoint、Phase Gate Review 与 Phase Learning Review 仍未执行。
>
> **后续状态（T0801/T0802 Learning Pass，2026-09-02）**：在该 checkpoint，T0801 在 `qa.py` 增加 context/source 两个无外部 I/O 转换函数与 5 个 unit tests；T0802 增加 history validation/truncation/formatting 与 4 个 unit tests。Phase 7 的 retrieval slice 当时仍未接入 QA Service、LLM 或 HTTP endpoint；本段只同步当前测试数字和下游边界，不改写 T0701–T0703 的历史 checkpoint。
>
> **后续状态（T0803 Learning Pass，2026-09-02）**：T0803 在同一 `qa.py` 增加 DeepSeek client、System Prompt、message assembly、bounded retry、错误映射与 12 个 Mocked/patched unit tests；**在该 T0803 checkpoint**，完整 `test_qa` suite 为 46/46 PASS，T0804 尚未执行。本段保留该历史边界，不改写 T0701–T0703 的 checkpoint。
>
> **后续状态（T0804 Learning Pass，2026-09-02）**：T0804 在 `qa.py` 增加 `QAService` 的 dependency injection/lazy creation、collection preflight、Hybrid retrieval、context/history converters、DeepSeek call、sources projection 与 service result 组装；4 个 orchestration tests 让当前完整 `test_qa` suite 达到 50/50 PASS。`/api/query`、真实 provider/Chroma/upload E2E、Phase 7 Gate Review 与 Phase Learning Review 仍未执行；本段只同步当前 downstream 状态，不改写 T0701–T0703 的历史 checkpoint。
>
> **后续状态（T0805 Learning Pass，2026-09-02）**：T0805 在 `api/query.py` 增加 request validation、collection existence、QAService delegation、`QueryResponse` 与统一错误 envelope；10 个 route-level Mocked tests 使当前完整 suite 达到 60/60 PASS。T0703 facade 仍不是 T0805 的调用入口，真实 provider/Chroma/upload → query E2E 与前端集成仍未执行；本段只同步当前 downstream 状态，不改写 T0701–T0703 的历史 checkpoint。
