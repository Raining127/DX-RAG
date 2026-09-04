# Phase 7 — Vector & Hybrid Retrieval Engineering Review

> **Coverage**: T0701 — Vector Retrieval + T0702 — Hybrid Retrieval + T0703 — Retrieval Module Integration（本轮增量评审）
>
> **Status**: COMPLETE（following the Phase 7 Formal Closure / Gate Verification）。T0701/T0702/T0703 implementation、F011 decision/remediation/verification、Gate closure 与 Phase Learning Review 已完成（2026-09-03）。

## 1. 当前工程结论

T0701 在 Service Layer 增加了一个窄职责的 `VectorRetriever`：它调用既有 `encode_chunks` 生成 query vector，再通过 `VectorStore.search` 获取已转换、已排序的 `similarity_score`，最后投影为 `vector_score` 并截断到 `top_k`。T0702 在同一 service module 增加 `HybridRetriever`：顺序调用两个 branch、按 `chunk_id` 合并、按固定权重计算 `final_score`、执行 relevance filter，再截断最终 Top-K。T0703 增加 module-level `retrieve()` facade：选择 `ChromaVectorStore`、先做 chunk-count preflight，再把同一 store 注入 keyword/vector retriever，最后委托给 Hybrid。实际代码见 [`backend/app/services/qa.py:87-216`](../../../backend/app/services/qa.py#L87-L216)。

本轮的核心判断是：**T0701 的工程价值在于 contract ownership 和可组合性；T0702 的工程价值在于不改变两个 ranker 的 owner，却把它们合成为一个 identity-stable、可过滤的结果 contract；T0703 的工程价值在于把三者组装成一个可导入的 facade，同时保留 empty 与 missing collection 的不同语义。** Embedding model lifecycle 属于 F007/T0202，raw distance → similarity 属于 F008/T0105，keyword/vector fusion 属于 F011/T0702，module wiring 属于 T0703。Phase 7 review checkpoint 的 `python -m unittest tests.test_qa -v` 为 24/24 PASS；T0801 后续新增 5 个 context/source tests，成为 30/30 PASS；T0802 再新增 4 个 history tests，成为 34/34 PASS；T0803 再新增 12 个 DeepSeek client tests，成为 46/46 PASS；T0804 再新增 4 个 QAService orchestration tests，成为 50/50 PASS；T0805 checkpoint 再新增 10 个 route-level tests，成为 60/60 PASS；T0901–T0903 后续新增 18 个 file-management/upload tests，当前 backend discovery 为 78/78 PASS。原 review 中的 4 个 vector tests 使用 injected embedder 与 Mock `VectorStore`，4 个 hybrid tests 使用 Mock retrievers，3 个 facade tests patch 了 store/retriever constructors；T0801 使用 synthetic dict inputs，T0802 使用 synthetic list/dict histories，T0803 使用 injected/patched LLM client、OpenAI constructor、settings 与 sleep，T0804 使用 injected Mock store/retriever/LLM，T0805 使用真实 FastAPI `TestClient` 但 patch storage/service。这些证据不能升级为真实 model + ChromaDB + DeepSeek semantic E2E、Frontend history integration 或 upload → query E2E。

## 2. 为什么需要这个模块

Keyword retrieval 能处理 exact token、编号和代码，但不能可靠覆盖语义改写。F010 需要一条独立的 semantic branch，让同一 query 在 embedding space 中与 stored chunk vectors 比较。该 branch 必须先输出稳定的 `vector_score`，才能被后续 hybrid contract 消费。

T0701/T0702/T0703 的当前边界如下：

```text
F007 encode_chunks → T0701 VectorRetriever ─┐
F008 VectorStore.search ────────────────────┤→ T0702 HybridRetriever
F009 KeywordRetriever ──────────────────────┘
                                              ↓
                                  T0703 retrieve() facade
                                               ↓
                                  T0804 QAService → T0805 HTTP API
```

T0701 不负责 `MIN_RELEVANCE_SCORE` 或 `final_score`；T0702 已负责这两项；T0703 负责 concrete store selection、empty preflight 与 facade delegation。三者都不负责 context assembly、DeepSeek client 或 HTTP QA endpoint；T0803 在后续 Phase 8 单独提供 LLM adapter。当前两个 branch 顺序执行；F011 允许并行或顺序，不能据此声称有异步调度。

## 3. 核心设计决策（ADR）

### ADR-01：复用 `encode_chunks`，不在 retriever 内实例化模型

- **Decision**：默认 `embedder` 使用 `app.services.embedding.encode_chunks`。
- **Context / Problem**：F007 已定义 bge-small-zh-v1.5、lazy singleton、L2 normalization 和 `EMBEDDING_MODEL_ERROR`。若 retriever 再加载模型，会产生 lifecycle、normalization 和 error semantics drift。
- **Chosen Solution**：`VectorRetriever.__init__` 接收 callable，默认绑定现有 `encode_chunks`。
- **Why**：Embedding owner 保持单一；service 只编排 query。
- **Trade-off**：retriever 依赖 `List[str] -> List[List[float]]` 的上游契约，模型替换必须保持该 shape 或显式更新契约。
- **Future Improvement**：需要 provider fallback、model versioning 或 batch API 时，先更新 F007/T0202 contract，再改 retriever；不在 T0701 私自增加 fallback。

### ADR-02：使用 constructor Dependency Injection

- **Decision**：`vector_store` 与 `embedder` 都保存在 instance 上；测试可以注入替代实现。
- **Context / Problem**：真实 model 和 ChromaDB 不是每个 unit test 都可用，且直接依赖 concrete backend 会锁死 service。
- **Chosen Solution**：类型标注为 `VectorStore` 与 `Callable[[List[str]], List[List[float]]]`，生产仍用默认依赖，测试传 Mock。
- **Why**：依赖边界可观察，测试可以断言 query batch shape、向量和 `top_k * 2` 调用参数。
- **Trade-off**：Python annotation 不在 runtime 自动验证 callable；错误签名会在调用时暴露，需靠契约、测试和更高层验证。
- **Future Improvement**：若未来需要更强 runtime validation，可在明确的 API boundary 加 schema/guard；不要将 service mock 误当成真实依赖兼容性。

### ADR-03：由 `VectorStore` 独占 distance → similarity conversion

- **Decision**：T0701 直接把 `result.similarity_score` 作为 `vector_score`，不做第二次 normalization。
- **Context / Problem**：F008 的 `VectorStore.search` 已在 storage boundary 做 `clamp(1.0 - distance, 0.0, 1.0)`，并承诺 descending order 和 `[0, 1]`。
- **Chosen Solution**：retriever 只改字段名和输出 shape。
- **Why**：同一 score semantics 才能与 F009 的 `keyword_score` 进入 F011 的加权公式。
- **Trade-off**：T0701 信任 F008 contract；若 backend distance semantics 改变，应修 storage contract/测试，而不是在每个 caller 加隐藏补丁。
- **Future Improvement**：真实 backend compatibility 与 score distribution 需要集成测试和 benchmark；当前 unit test 只验证 pass-through。

### ADR-04：扩大召回后再由 service 截断

- **Decision**：调用 `search(..., top_k * 2)`，然后对已排序结果执行 `[:top_k]`。
- **Context / Problem**：F011 计划把 keyword/vector 各自的候选合并、融合、过滤后再取 final Top-K；只召回最终数量会让单 branch 的低位候选过早消失。
- **Chosen Solution**：T0701 先落实可复用的 expanded recall contract，当前仍返回本 branch 的 `top_k`。
- **Why**：为后续 hybrid 留出候选空间，同时不把 T0702 的职责提前塞进 T0701。
- **Trade-off**：单独使用 vector branch 时，storage 可能多返回并处理候选；这个成本需要与 recall 价值一起测量。
- **Future Improvement**：T0702/T0703 已落地 service-level composition；下一步用真实 query/corpus 评估倍数、latency 和 recall，不凭直觉把 2 倍改成其他数字。

### ADR-05：投影为 service-level plain dict

- **Decision**：返回 `chunk_id`、`file_id`、`file_name`、`content`、`vector_score`，不透出完整 `metadata`。
- **Context / Problem**：storage 的 `VectorSearchResult` 是 backend-facing contract，包含 `similarity_score` 和 metadata；keyword branch 使用 `keyword_score`，hybrid 需要统一 score names。
- **Chosen Solution**：在 retriever 做显式 field projection 与 `similarity_score → vector_score` 命名转换。
- **Why**：下游只依赖它需要的字段，storage metadata 不成为 accidental API。
- **Trade-off**：未来如果 context/citation 需要更多 metadata，必须更新 service contract，而不是绕过 retriever 访问 private object。
- **Future Improvement**：在 F012/后续 service contract 明确 metadata ownership 和来源展示字段后，再增量扩展 shape。

### ADR-06：错误与输入校验不在 T0701 内重复定义

- **Decision**：模型加载错误沿用 F007 的 `AppError`；storage 异常自然传播；`top_k` 的范围 validation 不由当前 class 私自发明。
- **Context / Problem**：不同层的错误 owner 不同；T0701 当前 method 只有默认值 wiring，没有完整 API validation contract。
- **Chosen Solution**：保持窄职责，记录未覆盖路径。
- **Why**：避免吞异常、重复 retry 或出现与配置/API 不一致的校验规则。
- **Trade-off**：embedder 空返回会在 `[0]` 暴露为 `IndexError`；非法 `top_k` 的当前行为没有专门 guard，不能写成已处理。
- **Future Improvement**：在调用边界和 SPEC 决策明确后补 validation/error tests；若要改变错误语义，应有独立决策和回归证据。

### ADR-07：通过 constructor 注入两个 ranker，Hybrid 只做 orchestration

- **Decision**：`HybridRetriever` 只接收 `KeywordRetriever` 与 `VectorRetriever`，不在内部 new concrete retriever；F011 权重由 module-internal constants 持有。
- **Context / Problem**：Hybrid 的责任是组合两个已经存在的 score contract；若它自行创建 storage、embedding 或 keyword index，会重新拥有生命周期和基础设施依赖。
- **Chosen Solution**：保存两个 retriever instance，在 `hybrid_search()` 中按各自公开方法调用；测试以 Mock 替换二者。
- **Why**：依赖方向清晰，调用参数、返回 shape 和 error propagation 都能被观察；这也让 T0702 unit tests 不需要真实 model/Chroma。
- **Trade-off**：Python `Dict[str, object]` 不是强静态 result type；错误签名和缺失字段要靠测试与上游 contract 发现。
- **Future Improvement**：T0703 已在不改变 fusion 规则的前提下建立统一 `retrieve()` facade；后续仍可为 retriever protocol 增加更明确的 type/schema。

### ADR-08：采用顺序 branch execution，遵守 F011 的允许范围

- **Decision**：当前先调用 `keyword_search()`，完成后再调用 `vector_search()`；不新增 async/thread scheduling。
- **Context / Problem**：F011 写的是“并行（或顺序）执行”；当前两个依赖是同步 service method，Task 没有要求并发基础设施或独立 timeout policy。
- **Chosen Solution**：保留最直接的同步 control flow，两个 branch 都收到 `top_k * 2`。
- **Why**：实现小、错误自然传播、测试容易断言调用参数；没有把“未来可并行”误写成“现在已并行”。
- **Trade-off**：wall-clock latency 是两条 branch 成本之和；没有 benchmark 证明顺序是否足够。
- **Future Improvement**：只有明确 timeout、cancellation、partial failure 和 resource limits 后，才评估 `asyncio.gather` 或任务队列，并补回归证据。

### ADR-09：以 `chunk_id` 为 identity，重复 score 取 branch 内最大值

- **Decision**：`merged` 使用 `Dict[chunk_id, accumulator]`；同一 branch 再次看到相同 id 时，`max(existing_score, score)`，而不是累加或按 content 去重。
- **Context / Problem**：两个 ranker 可能同时命中同一 chunk；SPEC 7.1 要求 chunk UUID 是 Retrieval Result identity，禁止把 content 当唯一 key。
- **Chosen Solution**：首次出现创建 accumulator，初始化另一 branch score 为 0；随后补 metadata/None payload，但不覆盖已有非空字段。
- **Why**：同一 chunk 的双 evidence 只产生一个结果，避免重复记录放大分数；最大值把异常重复视为同一 branch 的同一 evidence。
- **Trade-off**：不同 payload 对同一 id 的冲突不会自动报错；“第一次非空字段优先”依赖上游 identity/data consistency。
- **Future Improvement**：在上游或 schema boundary 增加一致性检查，并用明确的 conflict policy 处理 file/content/metadata 不一致。

### ADR-10：缺失 branch score 视为 0，并保留六字段输出 shape

- **Decision**：用 `result.get(score_key) or 0.0` 填补缺失 score；最终始终输出 `chunk_id/file_id/file_name/content/final_score/metadata`，metadata 缺失时为 `{}`。
- **Context / Problem**：只命中一个 ranker 的 chunk 仍应参与 fusion；F011 的输出 shape 又要求 metadata，即使当前 T0701 projection 尚未提供它。
- **Chosen Solution**：accumulator 初始化两种 score 为 0，metadata 使用空 dict fallback；若后来的 branch 提供 metadata 且已有值为空则补入。
- **Why**：线性公式可以统一处理双命中和单命中，消费者不必为缺失 key 写分支；输出 shape 与 SPEC 保持一致。
- **Trade-off**：`0.0` 表示“不被该 branch 支持”，不是测量到的低相似度；T0701 的真实 metadata 目前会被 projection 丢掉，Hybrid 的 `{}` 可能只是占位。
- **Future Improvement**：先决定 metadata 的 service owner，再扩展 T0701/F012 contract；不要通过 Chroma private object 绕过层次。

### ADR-11：固定权重 + filter-before-final-top-k

- **Decision**：v1 使用内部固定常量 `keyword_weight = 0.3` 与 `vector_weight = 0.7`；每个 accumulator 先计算 `final_score`，排序后删除 `< settings.MIN_RELEVANCE_SCORE` 的结果，最后 `[:top_k]`。
- **Context / Problem**：F011 需要关键词精确性与向量语义的可解释加权，并明确 relevance filter 必须发生在最终 Top-K 之前。
- **Historical finding**：早期 T0702/interim material 曾把 `weights` 写成可选 constructor input，形成 F011 governance conflict；owner 已决定 **OPTION B — Frozen Internal Weights**，并完成授权的 SPEC remediation。该历史发现保留，但不再代表当前 contract。
- **Chosen Solution**：使用 module-internal fixed constants 完成线性组合，当前 config 的阈值为 `0.30`；比较式为 `>=`，因此等于阈值保留。
- **Why**：权重与 score 的 [0,1] 前提直接对应 SPEC；先过滤避免噪声占名额，也保留融合后才达到阈值的候选。
- **Trade-off**：固定权重未经过真实评估集校准，排序的 equal-score tie-breaker 也未定义；这不构成 v1 的 caller configuration gap。
- **Future Improvement**：用真实 relevance judgments 评估权重、阈值和 tie-breaker；若未来引入 RRF/dynamic weighting，需重新取得产品决策并重审 score semantics 与验收标准。

### ADR-12：Hybrid 不吞异常，也不私自添加 input validation

- **Decision**：keyword/vector retriever 或 storage 抛出的异常自然向上传播；Hybrid 当前不验证 `top_k`、权重范围、chunk payload schema，也不做 fallback/retry。
- **Context / Problem**：这些错误的 HTTP/error-code owner 尚由上层 API boundary 决定；在 T0702 中猜测会制造与 SPEC 不一致的第二套规则。
- **Chosen Solution**：保持纯 orchestration，记录 `KeyError`、`ValueError`、`TypeError` 等运行时失败可能性。
- **Why**：不把“空结果”与“依赖失败”混淆；上层才能决定是否返回 `COLLECTION_NOT_FOUND`、`EMBEDDING_MODEL_ERROR` 或其他 API error。
- **Trade-off**：非法输入可能进入计算或在 Python 原生操作处失败；当前 unit tests 没有覆盖这些负向路径。
- **Future Improvement**：HTTP/API boundary 明确合法范围和错误映射后，再增加 validation tests；真实 dependency failure 与 partial-result policy 需独立验证。

### ADR-13：由 `retrieve()` 作为 module-level composition facade

- **Decision**：T0703 暴露 `retrieve(query, collection, top_k)`，在一个函数内创建 `ChromaVectorStore`、两个 retriever 与 `HybridRetriever`，再委托给 `hybrid_search()`。
- **Context / Problem**：如果每个调用方都重复组装三层 retriever，store sharing、constructor 顺序和默认参数会产生 drift；但 T0703 也不应把 HTTP/QA orchestration 提前塞进 retrieval module。
- **Chosen Solution**：只在 facade 边界选择 concrete `ChromaVectorStore`，下游 class 仍通过 `VectorStore` public contract 接收依赖。
- **Why**：调用方得到一个稳定的 Python entry point，同时 storage private API 仍被封装在 implementation 内。
- **Trade-off**：facade 当前不能注入 fake store/factory，unit test 只能 patch module symbols；它也不是 `/api/query` 或 `QAService`。
- **Future Improvement**：若后续需要多 backend、request-scoped store 或更强测试 seam，可在不改变 `retrieve()` contract 的前提下注入 store factory，并补真实 integration evidence。

### ADR-14：空 collection 在 facade 入口短路，缺失 collection 保留异常

- **Decision**：先调用 `get_chunk_count(collection)`；count 为 `0` 时返回 `[]`，不创建 retriever、不做 embedding；该调用抛异常时不 catch。
- **Context / Problem**：空知识库是合法但无候选的状态；不存在的 collection 则是 storage/error signal。把两者都转成空列表会隐藏调用方需要知道的错误。
- **Chosen Solution**：用一个 public count preflight 分流正常空结果与 exception propagation。
- **Why**：满足 T0703 的 empty collection contract，并把 `COLLECTION_EMPTY` 的 HTTP policy 留给 API layer。
- **Trade-off**：每次 facade 调用增加一次 count；真实 Chroma count/error behavior 尚未在本轮执行。
- **Future Improvement**：QA/API boundary 建成后，定义 missing collection 的统一错误映射，并评估是否需要把 count 与首次检索合并以减少 backend round trip。

### ADR-15：两个 branch 共享同一个 store instance

- **Decision**：`retrieve()` 创建一个 `ChromaVectorStore`，同时传给 `KeywordRetriever` 与 `VectorRetriever`；Hybrid 只接收两个 retriever。
- **Context / Problem**：keyword 需要 `list_chunks()`，vector 需要 `search()`；各自创建 store 会重复 backend client，并让同一请求的 storage boundary 不一致。
- **Chosen Solution**：共享 instance，但仍只调用 `VectorStore` public methods；具体 `_client` 只留在 `ChromaVectorStore` 内部。
- **Why**：对象共享不等于 private state 泄漏；它减少 wiring duplication，并让测试可以断言两种 retriever 收到同一个对象。
- **Trade-off**：facade 没有显式 lifecycle/close 管理，也没有证明 PersistentClient 的创建成本；多进程与并发语义仍是 Future。
- **Future Improvement**：需要持久 client lifecycle、backend pooling 或 multi-worker coordination 时，先建立运行时约束与 benchmark，再调整 composition owner。

## 4. 架构影响

### 4.1 依赖方向

```text
Embedding (F007/T0202) ──┐
                         ├─→ VectorRetriever (T0701)
VectorStore (F008/T0105) ┘             │
KeywordRetriever (F009/T0602) ─────────┘
                                       └─→ HybridRetriever (T0702)
                                             │
                                             └─→ T0703 retrieve()
                                                   (shared ChromaVectorStore)
                                                         │
                                                         └─→ T0801/T0802/T0803/T0804/T0805
                                                               (real provider/storage E2E deferred)
```

`qa.py` 的 T0701/T0702 retriever 依赖 `VectorStore` interface，而不是 `ChromaVectorStore` 或 `_collection`；T0703 facade 才在 composition boundary 选择 `ChromaVectorStore`，然后把同一个对象传给两个 retriever。Hybrid 进一步依赖两个 retriever 的 service-level methods，而不是直接访问 storage；这保持了 storage backend isolation，并允许用同一 control flow 做 unit test。

### 4.2 新增契约

T0701 冻结了一个中间 service shape：

```text
{chunk_id, file_id, file_name, content, vector_score}
```

其中 `vector_score` 的数值语义来自 F008 `similarity_score`，不是新的评分算法；`keyword_score` 来自 F009 的 unique-token coverage。T0702 冻结的最终 service shape 是：

```text
{chunk_id, file_id, file_name, content, final_score, metadata}
```

它按 `chunk_id` 合并两个中间契约，不需要重新查询 storage private state。当前真实 T0701 projection 没有 metadata，Hybrid 以 `{}` 作为 fallback；这是 shape 已满足、来源尚未贯通的明确 gap。

T0703 没有再发明一套结果 shape；`retrieve(query, collection, top_k)` 直接返回 Hybrid 的六字段 `List[Dict]`。它新增的是 wiring contract：由 facade 选择 `ChromaVectorStore`，先调用 `get_chunk_count()`，再把同一个 store 注入两个 retriever。空 collection 返回 `[]`，missing collection 的 exception 不被 facade 改写。[PROJECT FACT]

### 4.3 没有改变的边界

- 没有修改 `VectorStore` 的 public interface 或 Chroma distance semantics。
- T0703 已提供 module-level `retrieve()`，但没有把 query retrieval 接到 `/api/query`；T0804 后来实现了 service-level QA orchestration，T0805 再提供 HTTP endpoint/response envelope。T0805 的 route-level tests 不等于真实 provider/Chroma E2E。
- T0702 已实现 hybrid merge、relevance filter 与 final score；T0703 只做 facade wiring；T0801/T0802 已分别提供 context/source 与 history converters，T0803 已提供 DeepSeek client，T0804 已直接把这些模块接入 `QAService`（不复用 T0703 facade），T0805 再把 QAService 接到 `/api/query`。
- 没有新增持久化、cache、后台任务或网络 dependency。

## 5. 工程问题分析

### 5.1 可维护性

T0701 的方法短且职责单一；T0702 也保持为一个同步 orchestration method，constructor 注入使两个 ranker 依赖显式；T0703 把创建顺序集中在一个 facade。关键维护风险是 `qa.py` 当前同时包含 keyword、vector、hybrid 与 facade；模块 docstring 和 `test_qa.py` 的 module docstring 仍使用较早的 tokenizer 描述，属于文档债务。若 Phase 7/8 继续增长，应按真实职责拆分，而不是无限扩展同一文件。facade 目前直接选择 concrete `ChromaVectorStore`，后续多 backend 或更强测试 seam 可能需要 factory injection。

### 5.2 一致性

最重要的一致性约束是 score semantics：storage 转换一次，retriever 不再转换；keyword/vector 两个 branch 都输出 `[0, 1]` 方向一致的 score。T0702 已按 `chunk_id` 做 identity merge，缺失 branch 以 0 参与公式，不能用 content 字符串去重。T0703 通过同一个 store instance 把 `list_chunks()` 与 `search()` 放进同一条 facade control flow，但不改变上游 contract。当前仍依赖上游保证 score range 与 payload identity；Hybrid 与 facade 自身没有再次校验。

### 5.3 错误处理

当前可观察路径包括：

| Failure | 当前 owner / 行为 | 处置 |
|---|---|---|
| model import/load failure | `embedding.get_model()` 抛 `EMBEDDING_MODEL_ERROR` | 由 F007/上层错误边界决定 |
| storage/backend exception | `VectorStore.search` 异常向上传播 | T0701 不吞异常、不伪造空结果 |
| empty storage result | list comprehension 返回 `[]` | 有 unit test，真实 Chroma empty-KB 未验证 |
| empty embedder output | `[0]` 触发 `IndexError` | 当前未定义专门 guard，标为 gap |
| invalid/negative `top_k` | class 内无范围校验 | 需要后续调用边界 contract |
| branch result 缺少 `chunk_id` | `result["chunk_id"]` 触发 `KeyError` | Hybrid 不吞异常；schema validation 尚未建立 |
| branch score 缺失/非法 | 缺失或 falsy 值 fallback 到 `0.0`；非 numeric 在 `float()` 处失败 | 依赖 F009/F010 score contract；没有 clamp |
| caller supplied `weights` | 当前 `HybridRetriever` constructor 不接受该输入，override 会在调用边界失败 | dynamic weighting 不是 v1 contract；已由 F011 focused regression verification 固化 |
| duplicate/conflicting payload | score 取 branch 内 max；非空 file/content 首值保留 | 不自动检测同一 chunk 的 payload 冲突 |
| empty collection | `get_chunk_count()==0` 后 facade 返回 `[]` | T0703 unit 覆盖的是 Mock count；真实 Chroma empty-KB 未验证 |
| missing collection | `get_chunk_count()` 异常直接向上传播 | 不在 retrieval module 映射 HTTP error；具体 Chroma exception 未验证 |

这张表不是 full failure taxonomy；完整跨层错误决策应在 Phase Gate/后续 ER 增量维护。

### 5.4 性能与扩展性

- 单次 T0701 query 做一次 embedding 和一次 storage search；T0702 先向两个 retriever 请求 `2 * top_k`。当 vector branch 使用当前 T0701 实现时，T0701 又把收到的值乘 2 传给 VectorStore，因此最终 vector storage 请求为 `4 * top_k`，再切回最多 `2 * top_k` 给 Hybrid。
- 当前 config 的 default `top_k` 为 5，因此 T0702 默认向两个 retriever 传 10；真实 vector storage 可能收到 20。这个事实由代码组合推导，不等于对生产 latency 的 benchmark。
- 每次 `retrieve()` 调用还会创建一个 `ChromaVectorStore` 与三个 retriever；keyword index 的 class-level cache 仍由 KeywordRetriever 共享，但 facade 没有 client pooling 或生命周期 benchmark。
- 真正的成本还受 embedding model、Chroma index、collection size 和 distance backend 影响；本轮没有 real corpus measurement。
- 当前实现顺序执行 keyword → vector；并行调度、partial failure policy、多 worker、批量 query 与缓存策略都属于未来设计，不应从这段同步方法推断出来。

### 5.5 安全与隔离

T0701/T0702 不直接解析文件路径、不拼接 Chroma private query、不执行用户输入；T0703 只在 facade 边界选择 `ChromaVectorStore`，随后仍通过 public methods 访问 count/list/search。query、collection 只作为 service/public method 参数传递。Hybrid/facade 仍未验证 `chunk_id`/payload schema，也未提供 query length 或 top_k range guard；weights 不属于 caller input。认证、请求限流与 HTTP 输入 policy 不是本 Task 的已实现能力，仍由外层边界决定。

## 6. 规模分析（Future）

| 规模 | 当前推理 | `[FUTURE]` 需要验证 |
|---|---|---|
| 10x query rate | 每次 query 仍会触发 keyword + embedding/vector；当前顺序执行，vector branch 可能产生 `4 * top_k` 的底层候选请求 | real model throughput、connection/resource limits、parallel scheduling、filter cost |
| 100x corpus | ANN index、keyword full rebuild 与 merge accumulator 的实际 latency 可能改变；二次 vector expansion 会放大候选成本 | Chroma/keyword benchmark、recall/latency curve、memory profile |
| 1000x corpus / multi-worker | 当前没有跨进程 cache 或分布式 coordination contract | index ownership、tenant isolation、backend migration、operational limits |

没有 benchmark 数据时，不把上述推理写成当前性能结论。

## 7. Verification Review

本次执行：

```text
python -m unittest tests.test_qa -v       → 50/50 PASS（Phase 7 review checkpoint 24/24；T0801 后 30/30；T0802 后 34/34；T0803 后 46/46；T0804 后 50/50）
python -m unittest tests.test_query -v    → 10/10 PASS（T0805 route-level Mocked boundary）
python -m unittest discover -s tests -v  → 78/78 PASS（含 T0901–T0903；T0805 checkpoint 为 60/60，Phase 7 review checkpoint 为 24/24）
python -m compileall -q app tests         → PASS
```

T0701 四个 unit tests 的 evidence boundary：

1. semantic mapping：Mock embedder 返回固定 vector，Mock store 返回 `similarity_score=0.82`；断言 query batch、store 参数、字段投影和 score pass-through。
2. empty collection：Mock store 返回 `[]`，断言 service 返回 `[]`。
3. expanded recall：断言 `top_k=3` 时下游收到 6，输出只保留前三条。
4. default top-k：断言默认值由 `settings.DEFAULT_TOP_K` 提供并乘以 2。

T0702 的四个 unit tests 进一步验证：

1. dual match：keyword `0.8` + vector `0.9` 得到一条 `0.87` 结果，并分别收到 `top_k * 2`。
2. low keyword-only：`0.6 * 0.3 = 0.18`，低于 `MIN_RELEVANCE_SCORE=0.30` 后被移除。
3. filter-before-top-k：低分候选不占名额，`top_k=3` 返回排序后的三个高分候选。
4. chunk-id dedup：即使两个 payload 的 content/file 不同，相同 `chunk_id` 仍只有一条结果。

T0703 的三个 wiring tests 验证：

1. facade 只创建一个 store，并把同一个对象传给 keyword/vector，再把两个 retriever 交给 Hybrid；最终参数由 facade delegation 保留。
2. count 为 `0` 时返回 `[]`，不创建 retriever，也不触发 embedding/index work。
3. count 检查抛出异常时不被 facade 吞掉，原异常继续向上传播。

测试类名 `RetrievalIntegrationTests` 不能改变证据等级：由于四个 constructor/依赖都被 patch 或替换，它们仍是 **Mocked composition tests**，不是 literal upload → ChromaDB → query integration。

因此当前 verification classification 是 **unit-tested at injected/patched dependency boundary**，并有 T0805 的 route-level `TestClient` evidence。T0702 的 AC-F011-01～04、T0703 的 facade behavior、T0804 的 service orchestration behavior 与 T0805 的 request/status/envelope mapping 均有对应的 observable assertion，但测试没有证明 T0602/T0701/T0702 的真实串接、真实 Chroma persistence、真实 metadata、真实 bge-small-zh-v1.5、literal upload → query、真实 DeepSeek 或完整 HTTP QA integration。上述内容均为 **DEFERRED / not independently verified**，不能写成 real E2E PASS。

## 8. Known Gaps & Pending Questions

1. `encode_chunks([query])[0]` 对空返回没有显式错误语义。
2. `top_k` 的最小/最大值校验与错误码 owner 尚未在 T0701 定义。
3. 当前 tests 不执行真实 embedding model 或 ChromaDB；semantic quality 与 score distribution 未测量。
4. T0703 已提供 module-level `retrieve()` facade，并消费 T0702 的 Hybrid；T0804 有独立的 `QAService` path，T0805 已把该 path 接到 HTTP QA endpoint，但仍没有统一两个 retrieval entry point，且真实依赖尚未验证。
5. T0702 → T0701 组合会使真实 vector storage 看到二次 `×2`；当前 tests mock 掉了这段调用链，尚无 recall/latency benchmark 或产品决策。
6. Hybrid 输出 `metadata`，但 T0701/T0602 当前 projection 没有真实 metadata 来源；F012/F015 的 source contract 尚未贯通。
7. `top_k`、branch payload schema、equal-score tie-breaker 与 partial failure policy 没有专门 validation/contract；dynamic weighting 已明确排除在 v1 外。
8. service/test module docstring 仍有旧的 tokenizer wording，需要后续文档维护。
9. backend distance metric、model version、multi-worker deployment 的一致性策略仍需在后续阶段决定。
10. facade 当前直接创建 concrete `ChromaVectorStore`，真实 store lifecycle、missing/empty Chroma behavior 与 upload → query integration 尚未执行。

这些是已知边界或 Future questions，不是本 Task 的失败 verdict。

## 9. Cross-links

- Technical Learning：[phase-07-vector-retrieval.md](../phase-07-vector-retrieval.md)
- Source contract：[SPEC F007](../../SPEC.md#f007-embedding) · [SPEC F008](../../SPEC.md#f008-vector-storage) · [SPEC F009](../../SPEC.md#f009-keyword-retrieval) · [SPEC F010](../../SPEC.md#f010-vector-retrieval) · [SPEC F011](../../SPEC.md#f011-hybrid-retrieval) · [SPEC Section 8.1](../../SPEC.md#81-environment-variables--config-parameters)
- Task contract：[T0701](../../TASKS.md#t0701--vector-retrieval) · [T0702](../../TASKS.md#t0702--hybrid-retrieval-merge-fusion-relevance-filter-top-k) · [T0703](../../TASKS.md#t0703--retrieval-module-integration)
- Previous retrieval learning：[phase-06-keyword-retrieval.md](../phase-06-keyword-retrieval.md)
- Project-level interview candidates：[dx-rag-interview-guide.md](../interview-notes/dx-rag-interview-guide.md)

> **Review boundary**：本文件第 1–9 节覆盖 T0701 + T0702 + T0703 的增量工程评审；第 10 节是随后同步的正式 closure record。Phase Learning Review 是独立的学习 consolidation 工作，已于 2026-09-03 完成；其 Technical Learning 与 Interview Guide 产物不替代本文件的工程判断。

## 10. Phase 7 Formal Closure / Gate Verification

> 本节同步已建立的 Phase 7 Formal Closure / Gate Verification 结果，不是新的 technical re-review、remediation 或 Phase 10 authorization。历史评审、F011 决策与修复链保持可追溯。

### 10.1 Historical chain

```text
T0701–T0703 implementation completed
  → Phase 7 retrieval verification
  → Interim Engineering Review
  → F011 weights governance conflict identified
  → Owner Decision: OPTION B — Frozen Internal Weights
  → Authorized F011 SPEC remediation
  → F011 verification
  → Phase 7 Formal Closure / Gate Verification
  → PHASE_7_PASS — CLOSED
```

### 10.2 Final F011 record

```text
F011 Decision: OPTION B — Frozen Internal Weights

keyword_weight = 0.3
vector_weight = 0.7

final_score = keyword_score * 0.3 + vector_score * 0.7
```

The weights are fixed internal v1 constants. They are not caller-, runtime-, constructor-, `QAService`-, API-, environment-, or application-configuration inputs. Dynamic weighting is not supported in v1.

**Final F011 state: CLOSED.**

### 10.3 Gate evidence

| Gate item | Result | Evidence boundary |
|---|---|---|
| T0701–T0703 declared completion | PASS | All three Tasks remain `DONE`; current implementation and Task contracts were rechecked |
| Fixed-weight retrieval contract | PASS | Static implementation inspection plus fixed-weight regression; no weight exposure |
| Focused Phase 7 / QA tests | PASS | `python -m unittest tests.test_qa -v` → 50/50; MOCKED/STATIC composition evidence |
| Full backend suite | PASS | `python -m unittest discover -s tests -v` → 78/78; real model/Chroma E2E not implied |
| Compilation | PASS | `python -m compileall -q app scripts tests` |
| Diff check | PASS | `git diff --check` |

### 10.4 Findings and deferred evidence

- `BLOCKER`: 0.
- `MAJOR`: 0.
- Nested retrieval over-fetch remains `MINOR` with disposition `ACCEPTED_V1_BOUNDARY`; it is not fixed or escalated here.
- Real BGE semantic retrieval, real ChromaDB retrieval E2E, and real semantic empty-KB verification remain `DEFERRED / T1202`.
- The focused F011 closure did not require a full Phase 7 Gate re-review.

### 10.5 Closure state

**PHASE_7_PASS — CLOSED**

Phase 10 was not started by the closure review. Phase Learning Review was completed on 2026-09-03: the Technical Learning now records the cross-task mental model and verification boundary, and selected Interview Candidates were promoted to the Phase 7 deep chapter. This changed documentation state only; it introduced no technical contract change and is not a new Gate finding.

| Governance record | State |
|---|---|
| Engineering Review | SYNCHRONIZED / COMPLETE |
| Phase 7 Gate Review | `PHASE_7_PASS — CLOSED` |
| Phase Learning Review | `COMPLETE`（2026-09-03） |
