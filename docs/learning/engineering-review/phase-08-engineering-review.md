# Phase 8 — RAG & QA Engineering Review

> **Coverage**：T0801 Context/Source Assembly、T0802 Conversation History Processing、T0803 DeepSeek Chat Client、T0804 QA Service Orchestration、T0805 `POST /api/query`
>
> **Status**：COMPLETE（2026-09-04）。本文是 Layer 2 Engineering Review，不重发 Phase Gate verdict，也不替代 Phase Learning Review 或真实集成验收。
>
> **Evidence vocabulary**：`STATIC/CODE-LEVEL` 表示源码或契约检查；`UNIT` 表示隔离依赖的行为测试；`MOCKED` 表示依赖被注入或 patch；`DEFERRED` 表示由后续集成/验收范围负责；`NOT_AVAILABLE` 表示本轮没有可用的运行时证据。

## 1. 当前工程结论

Phase 8 把 Phase 7 的 ranked chunks 变成一次可消费的 QA service call：T0801 负责 bounded context 和 backend-owned sources，T0802 负责 history 的 runtime validation、suffix window 与 prompt-ready formatting，T0803 把 System Prompt、用户输入和 provider error policy 收敛到 DeepSeek adapter，T0804 负责 preflight 与顺序编排，T0805 把 service result 接到 HTTP request/response boundary。

当前最有价值的工程选择不是“接入了一个 LLM”，而是把不同可靠性等级的输出拆开：

- `context` 是给模型的受长度预算约束的文本；
- `sources` 是给客户端和审计使用的 chunk-level identity，不由 LLM 生成；
- `history` 是对话上下文，不是知识事实；
- `answer` 是 provider 输出，必须经过 adapter 的 retry、parse 和 error mapping；
- `QueryResponse` 是 HTTP 出口的 typed shape，不让 service 内部 dict 直接成为公开契约。

当前实现与冻结的 F012–F015、Section 6.4 主要一致，且本轮验证没有发现阻断 Phase 8 文档收口的实现错误。工程上仍有明确边界：没有输入 token/字符预算、没有 service-level result schema、没有真实 DeepSeek/embedding/Chroma/upload-to-query E2E，provider retry 是同步阻塞的，T0703 的独立 `retrieve()` facade 与 T0804 direct retrieval path 也尚未统一。这些是 Known Gaps 或 Future decision，不应被写成“真实 QA 已通过”。

## 2. 为什么需要这个模块

检索结果本身不是用户答案。Phase 8 引入的不是一个单点函数，而是一个跨边界的 data-flow contract：

```text
POST /api/query JSON
    │
    ▼
T0805 request validation + collection existence
    │
    ▼
T0804 QAService
    ├─ get_chunk_count() preflight
    ├─ T0702 HybridRetriever → ranked chunks
    ├─ T0801 assemble_context() → bounded context
    ├─ T0802 process_history() → validated history text
    ├─ T0803 DeepSeekClient → answer text
    └─ T0801 assemble_sources() → backend-owned sources
    │
    ▼
QueryResponse / unified AppError envelope
```

这个拆分让每条输出拥有单一 owner：长度边界由 context assembler 管，来源身份由 backend 管，provider 交互由 client adapter 管，HTTP 状态码由 `AppError` catalog/handler 管。对应实现集中在 [`qa.py`](../../../backend/app/services/qa.py#L263-L550) 与 [`query.py`](../../../backend/app/api/query.py#L16-L68)。

## 3. 核心设计决策（ADR）

### ADR-01：Context 只保留按分数排序的完整 chunk 前缀

- **Decision**：`assemble_context()` 先按 `final_score` descending 排序；每次计算加入 label、content 和 separator 后的完整 candidate，超出 `MAX_CONTEXT_CHARS` 就 `break`，不做 mid-chunk truncation。
- **Context / Problem**：截断单个 chunk 会破坏句子、代码或表格语义；跳过超限 chunk 后继续寻找低分 chunk 又会改变 F012 的“高分前缀”语义。
- **Chosen Solution**：默认 `MAX_CONTEXT_CHARS=4000`，保持排序、完整性和停止条件一致。
- **Why**：这是可审计的 deterministic boundary，也避免把摘要/压缩质量误算成当前 v1 能力。
- **Trade-off**：一个过大的高分 chunk 会使后续较小 chunk 全部不进入 context；当前没有 token-aware packing 或 compression。
- **Future Improvement**：若产品要求更高 budget utilization，应先修改 F012 contract，再用 token budget、recall 和 answer quality 数据验证。

### ADR-02：Sources 按 chunk 投影，由 backend 生成

- **Decision**：`assemble_sources()` 从 Hybrid 最终 Top-K 逐 chunk 投影 `{file_id, file_name, chunk_id, relevance_score}`，不按 `file_name` 去重，不添加 `content_preview`，不让 LLM 生成引用。
- **Context / Problem**：同一文件的多个 chunk 是不同 evidence unit；用文件名去重会丢失 chunk identity，解析模型文本又无法保证真实 ID。
- **Chosen Solution**：以 `chunk_id` 保留 identity，以 `final_score` 作为 `relevance_score`，在 service result 中独立传递 sources。
- **Why**：source records 可追溯、可排序、不会被 prompt injection 或模型幻觉改写。
- **Trade-off**：context 可能因 4000 字符预算只包含高分前缀，而 sources 仍包含全部 Hybrid Top-K；因此某条 source 可能是检索证据，但未进入本次 LLM context。这是当前 F015 的明确语义，同时是产品展示层需要理解的边界。
- **Future Improvement**：若产品要求“只展示实际送入模型的来源”，需要单独定义 context-selected source contract，不能偷偷改变 `assemble_sources()` 的 F015 输入。

### ADR-03：Frontend 持有 history，backend 做防御性校验和最近窗口截断

- **Decision**：backend 不持久化 history；`process_history()` 校验整个输入列表，确认 role 只能是 `user|assistant` 且 content 为 `str`，然后保留最后 20 条并格式化为 `User:/Assistant:` 行。
- **Context / Problem**：Frontend 负责 conversation lifecycle，但 backend 不能假设所有 direct caller 或未来客户端都已经遵守 20 条限制。
- **Chosen Solution**：API boundary 在 [`_parse_query_request()`](../../../backend/app/api/query.py#L16-L50) 先校验，service boundary 在 [`process_history()`](../../../backend/app/services/qa.py#L293-L318) 再校验。
- **Why**：两层校验保留统一 `INVALID_HISTORY_FORMAT`，并防止“非法旧消息恰好会被截断”而静默消失。
- **Trade-off**：全量 validation 需要遍历全部输入；20 条是 message-count window，不是 token-count window，也不保证保留完整 user/assistant pair。
- **Future Improvement**：前端切换 Knowledge Base 时清空 history 仍属于 frontend integration；若要 token-aware history，需要新增明确预算与截断策略。

### ADR-04：显式 API validation，不依赖 FastAPI 默认 422

- **Decision**：T0805 接收 `Any` body，按项目错误码显式校验 question、collection、top_k、history，再构造 `QueryRequest`；只有框架层未预期的 validation 才走统一 422 handler。
- **Context / Problem**：直接依赖 Pydantic/FastAPI 默认行为会把多种 query 错误压成框架的 422，丢失 `INVALID_QUERY`、`INVALID_TOP_K` 和 `INVALID_HISTORY_FORMAT` 的业务语义。
- **Chosen Solution**：先做业务输入检查，再通过 `QueryResponse.model_validate()` 锁定成功响应出口；错误由 [`AppError`](../../../backend/app/core/errors.py#L41-L77) 与全局 handler 统一映射。
- **Why**：请求在任何 storage work 前被拒绝，HTTP contract 与 SPEC Section 6.4 一致。
- **Trade-off**：存在手写 parser 与 Pydantic schema 两层规则，需要持续保持一致；当前 parser 特别拒绝 `bool`，因为 Python 中 `bool` 是 `int` 的 subclass。
- **Future Improvement**：可以在不改变错误码语义的前提下，评估 strict schema 或统一 validator owner；目前不应通过删除业务 parser 直接回到默认 422。

### ADR-05：System Prompt 与 data payload 使用两条 message

- **Decision**：T0803 始终发送一条 `system` message 和一条 `user` message；history、context、question 都位于 user payload 中，检索文档的指令性文本被视为 data。
- **Context / Problem**：把 policy 和 retrieved content 拼成同一层会削弱规则优先级；把 sources 交给模型生成又会让 citation identity 不可审计。
- **Chosen Solution**：`SYSTEM_PROMPT` 固定六项原则，`_build_user_message()` 按 history → context → question 组装，并在空 context 时使用 placeholder。
- **Why**：System Prompt 是 policy owner；retrieved document 只能作为参考数据，不能覆盖 grounding、语言和 anti-fabrication 规则。
- **Trade-off**：这只能建立 prompt-level defense，不能从静态代码证明模型一定遵守规则；恶意文本仍会进入 provider 输入。
- **Future Improvement**：真实 provider adversarial tests、输出评估和模型/提示版本管理属于后续质量与集成范围。

### ADR-06：DeepSeek client lazy creation + dependency injection

- **Decision**：`DeepSeekClient` 接受可注入 client；生产 client 在第一次生成答案时读取 `DEEPSEEK_API_KEY` 并创建 OpenAI-compatible client，构造 service 或启动应用不强制验证 key。
- **Context / Problem**：health、collection、文件等不需要 LLM 的路径不应因缺少 provider key 而无法启动；直接在函数内 new SDK 又会让测试绑定网络。
- **Chosen Solution**：[`DeepSeekClient._get_client()`](../../../backend/app/services/qa.py#L321-L347) 负责 lazy wiring，`max_retries=0` 将 retry ownership 留给 service。
- **Why**：配置失败在真正需要 LLM 时可观察，provider 细节集中，unit tests 可以完全隔离网络。
- **Trade-off**：配置错误延迟到第一次 QA；不同部署进程各自拥有 client，当前没有连接池或 provider circuit breaker。
- **Future Improvement**：若需要共享 HTTP transport、连接池或多模型 routing，应先明确 lifecycle、timeout 和 ownership contract。

### ADR-07：由 service 统一 retry 与 error mapping

- **Decision**：timeout/network/429/5xx 最多执行初始请求加 2 次 retry，backoff 为约 1s、2s；401/403 和 400 不 retry；结果统一映射为 `LLM_*` AppError。
- **Context / Problem**：SDK retry 与 service retry 叠加会使实际请求次数不可预测，也会造成错误码漂移。
- **Chosen Solution**：SDK `max_retries=0`，`generate_answer()` 在 [`qa.py`](../../../backend/app/services/qa.py#L422-L478) 内维护最多 3 次 attempts 与 mapping。
- **Why**：调用次数、backoff 和客户端可观察错误只有一个 owner，测试可以精确断言。
- **Trade-off**：retry 使用同步 `time.sleep`，没有 jitter、circuit breaker、bulkhead 或请求级 rate limit；连续 provider 故障会放大 latency 与流量。
- **Future Improvement**：生产化前应以 provider quota、并发模型和 SLA 数据决定 async retry、jitter、circuit breaker 或队列化，而不是仅凭直觉调整次数。

### ADR-08：区分 empty collection 与 relevance-filter-empty

- **Decision**：T0804 先通过 `get_chunk_count()` 判断 collection 是否真的没有 chunks；0 chunks 抛 `COLLECTION_EMPTY`/409，非空 collection 即使 Hybrid 过滤后没有结果，仍以空 context 调用 LLM 并返回 `sources=[]`。
- **Context / Problem**：两者都可能产生空列表，但一个是 storage state，一个是 retrieval outcome；合并会让用户看到错误状态，或者错误地跳过 no-information answer。
- **Chosen Solution**：preflight 在 retrieval 前执行，空检索结果走正常 provider path。
- **Why**：保持 Section 6.4 的状态语义和前端提示语义稳定；空库不浪费 embedding/LLM，非空但无关则仍让 System Prompt 生成无信息回复。
- **Trade-off**：preflight 与后续检索不是一个 transaction；并发删除/上传时可能出现 check 与 search 之间的 state drift。
- **Future Improvement**：真实 Chroma concurrency behavior、snapshot/isolation 或更强 query consistency 需要单独的 storage decision。

### ADR-09：QAService 负责编排，但当前保留 direct Hybrid path

- **Decision**：QAService 通过 injected/lazy-created `VectorStore`、`HybridRetriever` 和 `DeepSeekClient` 组成 service-level seam；T0804 直接调用 `HybridRetriever.hybrid_search()`，不调用 T0703 module-level `retrieve()` facade。
- **Context / Problem**：service 需要共享同一 store、便于测试和 collection preflight；同时 T0703 已存在一个独立的 retrieval composition facade。
- **Chosen Solution**：[`QAService`](../../../backend/app/services/qa.py#L481-L550) 保持注入优先、懒创建，并在一个方法内明确顺序：preflight → retrieval → converters → LLM → sources。
- **Why**：依赖方向可见，unit tests 可以分别替换各 seam；HTTP path 不必把 retrieval facade 的 concrete store 选择带入 service。
- **Trade-off**：两个 retrieval entry point 可能发生 wiring 或默认值 drift；T0703 facade 的 concrete-store lifecycle 不会被 `/api/query` 这条路径覆盖。
- **Future Improvement**：统一入口前需先比较 public contract、empty/missing semantics、store injection 和当前两组测试；不能在 Phase 8 review 中擅自替换。

### ADR-10：全局 AppError handler 作为 API 错误出口

- **Decision**：service/route 抛出带 code 的 `AppError`，全局 handler 根据 error catalog 返回 `{error: {code, message, details}}`；未处理异常记录 traceback 并返回 `INTERNAL_ERROR`。
- **Context / Problem**：如果每个 endpoint 自己 catch，状态码、中文消息和 envelope 容易分叉。
- **Chosen Solution**：[`main.py`](../../../backend/app/main.py#L40-L84) 集中处理 `AppError`、framework validation 和未知异常。
- **Why**：T0803 的 provider errors、T0804 的 collection state 和 T0805 的 request errors 可以共享同一 HTTP shape。
- **Trade-off**：未知异常会被归一为通用 500，调用方看不到具体 failure；任何新 error code 都必须同步 catalog，否则可能出现 code 与 status fallback 不一致。
- **Future Improvement**：保留敏感信息不出现在 response 的前提下，增加结构化 correlation/observability 属于后续 NFR 范围。

### ADR-11：成功响应在 API 出口重新验证

- **Decision**：QAService 返回内部 dict，T0805 在返回前执行 `QueryResponse.model_validate(result)`；`SourceObject` 锁定四个 source fields，response 锁定 `answer/sources/query/collection_name`。
- **Context / Problem**：service 编排需要保持轻量，但 HTTP response 不能依赖隐含的 dict 约定。
- **Chosen Solution**：schema 作为 transport boundary，定义在 [`schemas.py`](../../../backend/app/models/schemas.py#L116-L144)。
- **Why**：API 可以拒绝缺字段或错误类型，避免把内部临时字段无意公开。
- **Trade-off**：这不是 answer quality validator，也不能证明 answer 非空、内容 grounded 或 relevance score 真的语义正确；Pydantic 默认对未声明 extra field 的行为也不是业务质量检查。
- **Future Improvement**：若需要质量门槛，应定义独立的 answer/source quality policy，不把它偷偷塞进 response model。

### ADR-12：v1 保留同步、无持久化、无 streaming 的窄范围

- **Decision**：backend 不存储 conversation history，不缓存 QA result，不做 streaming、不做 answer quality scoring、不做 context summarization/compression；T0803 使用同步非 streaming provider call。
- **Context / Problem**：Phase 8 的目标是冻结 RAG→QA 的可组合 contract，而不是一次引入 session、cache、queue、streaming 和评估平台。
- **Chosen Solution**：把这些能力记录为 explicit out-of-scope/future boundary。
- **Why**：减少状态 owner 和跨请求一致性问题，让当前 tests 聚焦 observable data flow。
- **Trade-off**：页面刷新会丢 history；长请求占用 worker；重复 query 没有缓存收益；语义质量没有自动门槛。
- **Future Improvement**：每项扩展都需要重新定义 ownership、失效、隔离、成本和验证证据，不能以“优化”名义直接改变 v1 contract。

## 4. 架构影响

### 4.1 依赖方向

```text
T0702 HybridRetriever ───────┐
                             ├─→ T0804 QAService ─→ T0805 /api/query
T0801 context/sources ───────┤                         │
T0802 history formatter ─────┤                         ├─→ QueryResponse
T0803 DeepSeek adapter ──────┘                         └─→ AppError envelope
```

- T0801/T0802 是无外部 I/O 的转换边界。
- T0803 是唯一的 DeepSeek provider adapter；它不拥有 retrieval 或 source identity。
- T0804 是 service-level integration seam；它不持久化 history，也不生成来源文本。
- T0805 是 HTTP adapter；它不直接拼 prompt，不访问 Chroma private API。
- `VectorStore` 仍是 retrieval 的 public storage boundary；Phase 8 只消费它，不改变 F008 的 ownership。

### 4.2 新增与稳定的契约

| 契约 | 当前 owner | 工程含义 |
|---|---|---|
| Context string | T0801 | 有 label/separator、完整 chunk、4000 字符 stop boundary |
| Source record | T0801/T0804 | chunk-level identity，backend-owned，四字段 |
| History text | T0802 | 先全量校验，再保留最近 20 条 |
| Provider call | T0803 | 两条 message、固定 model/config、bounded retry、统一错误 |
| QA result | T0804 | `answer + sources + query + collection_name` 的内部 result |
| HTTP success | T0805/schema | `QueryResponse` typed response |
| HTTP failure | error catalog/main handler | `AppError` code → status/message/envelope |

### 4.3 没有改变的边界

Phase 8 没有改变 embedding model lifecycle、Chroma distance→similarity semantics、Hybrid fixed weights、keyword index invalidation、upload rollback 或 file-management cascade delete。它消费这些上游结果；真实 upload → Chroma → retrieval → DeepSeek → HTTP 的贯通仍必须由后续 integration/acceptance evidence 证明。

## 5. 工程问题分析

### 5.1 可维护性

`qa.py` 当前从 tokenizer、keyword/vector/hybrid retrieval 一直延伸到 context、history、DeepSeek client 和 QAService，已经是一个跨多个 feature owner 的大模块；这让 import seam 简单，但也提高了未来修改时误触相邻契约的风险。文件顶部 docstring 仍是 `Keyword and vector retrieval services`，与当前实际职责不一致，属于低风险但明确的文档维护债务。

T0801/T0802 的纯函数和 T0803/T0804 的 injected dependencies 形成了较好的测试 seam；T0805 仍通过手写 parser 维持业务错误码。下一次拆分应以 ownership 为依据，并保持这些 public seams，而不是为了文件长度进行机械拆分。

### 5.2 一致性与数据语义

1. `assemble_context()` 和 `assemble_sources()` 都独立排序，保证 direct caller 不必信任上游排序；代价是每条路径各做一次排序。
2. sources 来自 Hybrid final Top-K，而 context 受字符预算限制，两者不是严格相同的集合。这符合 F015，但前端必须把 sources 理解为检索证据列表，而不能自动宣称每条都被模型实际读到。
3. T0805 与 T0802 都校验 history，形成 defense in depth；但 direct `QAService.answer()` 的 invalid history 会在 retrieval/context 之后才失败，说明 service boundary 的拒绝顺序仍可优化，当前 route path 则在 storage work 前拒绝。
4. T0703 `retrieve()` 与 T0804 direct Hybrid path 同时存在，当前没有统一的 composition owner；这不是当前测试失败，但会增加默认参数、store lifecycle 和空库语义漂移的可能。

### 5.3 Failure taxonomy

| Failure / state | 当前行为 | 当前证据 | 工程判断 |
|---|---|---|---|
| 空 question/collection | 400 `INVALID_QUERY`，不做 storage/service work | `MOCKED` route tests | API boundary 行为明确 |
| 非法 top_k | 400 `INVALID_TOP_K`，拒绝 `bool` 和越界整数 | `MOCKED` route tests | 输入 contract 明确 |
| 非法 history | 400 `INVALID_HISTORY_FORMAT` | `UNIT` + `MOCKED` route tests | route 早拒绝；direct service 顺序仍有 gap |
| missing collection | 404 `COLLECTION_NOT_FOUND`，不调用 QAService | `MOCKED` route test | 真实 Chroma list behavior 未验证 |
| existing but 0 chunks | 409 `COLLECTION_EMPTY`，不 retrieval、不 LLM | `MOCKED` QAService test | preflight 语义清晰 |
| non-empty but no retrieval result | 继续 LLM，context/source 为空 | `MOCKED` QAService/route tests | 真实 no-match semantic answer 未验证 |
| timeout/network/429/5xx | 最多 3 次尝试，耗尽后 502 `LLM_UNAVAILABLE` | `UNIT` with injected client | retry state machine 已测，provider 未测 |
| 401/403 | 立即 500 `LLM_AUTH_FAILED`，不 retry | `UNIT` with synthetic status error | 真实 SDK exception shape 未测 |
| 400 或其他 provider error | 500 `LLM_RESPONSE_ERROR` | `UNIT` with synthetic status error | broad mapping 可能掩盖 provider 细节 |
| malformed provider response | 500 `LLM_RESPONSE_ERROR` | `UNIT` | response parser 有明确出口 |
| provider 返回空字符串 | 原样返回空 `answer`，可继续到 200 response | `UNIT` | 与 AC-QA-01 的 non-empty 目标存在 contract tension |
| malformed retrieval result | 可能在 assembler 的 dict access 处抛异常，最终走 generic 500 | `NOT_AVAILABLE` 专门 contract test | 尚无 service-level result schema/policy |
| Chroma/list/count runtime failure | 非 `AppError` 时走 global `INTERNAL_ERROR` | `STATIC`；未做真实 API path test | 需要后续明确 storage error mapping |

### 5.4 性能与可用性

- 两条 retrieval branch 当前顺序执行；T0702 允许顺序，但没有 benchmark 证明顺序对目标负载足够。
- `VectorRetriever` 与 Hybrid 的双层 `top_k * 2` 会扩大候选量；真实 candidate count、recall、latency 和 memory 没有测量。
- LLM call 是同步的；最坏路径大约包含 3 次 provider timeout 加两次 backoff，单 worker 可能长时间被占用。T0805 明确不做 rate limiting，这个风险属于后续部署设计。
- `MAX_CONTEXT_CHARS` 限制了 context text，但 question 和每条 history content 没有 token/字符上限；恶意或误用输入仍可能超过 provider context window，触发 400、截断或高成本。
- keyword index 的 class-level cache、dirty rebuild、并发 publication 和多 worker coherence 是 Phase 6/7 继承边界；Phase 8 不会自动修复这些问题。

以上是源码结构和契约推理，不是性能 SLA；SPEC 当前也没有正式 QA latency target。

### 5.5 安全与隔离

- `DEEPSEEK_API_KEY` 只在 backend config 读取，成功 response 与 error response 不回显 secret；真实日志/provider transport 仍需在后续部署验证。
- System Prompt 明确把检索文档的指令性文本当作 data，并禁止虚构 citations；但当前 tests 只检查 prompt 字符串，不能证明真实模型在 adversarial input 下的行为。
- history 不进入持久化存储，符合 v1 scope；但在 provider call 中会作为 user message 发送，隐私、保留期和第三方处理边界尚未在工程运行策略中展开。
- v1 无 authentication/authorization/user isolation；任何 collection access control 都不能从当前 Phase 8 实现推断出来。

## 6. 规模扩大分析（Future / Not implemented in v1）

| 规模 | 当前可推断行为 | 主要压力点 | 需要的后续证据/决策 |
|---|---|---|---|
| 10x query/history length | context 仍按字符预算；history 仍按 message count 截断 | 无输入 token budget；provider context overflow；同步 retry latency | question/history limits、token-aware packing、provider error matrix |
| 10x corpus | Hybrid 候选和 context 形状不变 | keyword full rebuild、vector expanded recall、Chroma round trips | recall/latency/memory benchmark |
| 100x corpus | service contract 仍可组合，但单次 query 成本上升 | in-memory inverted index、full rebuild cold/dirty latency、candidate duplication | profile、background rebuild 或 index architecture decision |
| 1000x corpus | v1 单进程内存假设很可能成为硬边界 | cache memory、multi-worker divergence、Chroma persistence/backup/compaction | durable/distributed index、worker coherence、容量上限 |
| 10x concurrent QA | 每个请求独立 service/store/client seam | synchronous provider call、retry sleep、无 rate limit/circuit breaker | concurrency load test、quota policy、async/cancellation design |
| 100x provider failure rate | bounded retry 限制单请求次数 | retry storm、排队、成本和用户等待时间 | jitter、circuit breaker、bulkhead、degraded response policy |

没有 benchmark 时，不把 O(n) 推理或“可扩展”写成当前性能结论。`MAX_CONTEXT_CHARS=4000` 也只是字符边界，不等于 provider token budget 或答案质量保证。

## 7. Verification Review

本轮在当前 checkout 执行：

```text
python -m unittest tests.test_qa tests.test_query
→ 60/60 PASS

python -m unittest discover -s tests -p "test_*.py"
→ 78/78 PASS

python -m compileall -q app tests
→ PASS

git diff --check
→ PASS（无 whitespace error）
```

Phase 8 focused evidence 的组成是：T0801 5 个 context/source tests、T0802 4 个 history tests、T0803 12 个 DeepSeek client tests、T0804 4 个 QAService tests、T0805 10 个 `QueryEndpointTests`，合计 35/35。当前 `tests.test_qa` 的 50 个 tests 还包含前置 retrieval tests，`tests.test_query` 的 10 个 tests 是 route-level boundary；因此 60/60 不是 60 个真实 E2E 场景。

证据边界如下：

- **`UNIT`**：T0801/T0802 以 synthetic dict/list 输入验证排序、预算、字段、history validation/truncation；T0803 以 injected client、synthetic status error、patched sleep 验证 message shape、retry 和 error mapping。
- **`MOCKED composition`**：T0804 注入 Mock `VectorStore`、`HybridRetriever`、`DeepSeekClient`，证明 preflight、调用顺序、空库/空检索分叉和 result shape，不证明 concrete dependency compatibility。
- **`MOCKED route-level`**：T0805 使用真实 FastAPI `TestClient`，但 patch `ChromaVectorStore` 与 `QAService`，证明 request/status/envelope/delegation，不证明 Chroma、embedding、provider 或 upload workflow。
- **`STATIC/CODE-LEVEL`**：System Prompt 六原则、lazy key、global error handler、schema fields 和 retry conditions 可由源码检查；不能由此推出模型 semantic compliance。
- **`DEFERRED / NOT_AVAILABLE`**：真实 DeepSeek API、真实 bge-small-zh-v1.5、concrete Chroma persistence、literal upload → ingest → retrieval → query、frontend history lifecycle、semantic answer quality、recall/latency benchmark 均未在本轮获得证据。

测试运行时出现 Starlette 关于 `httpx`/`TestClient` 的 deprecation warning，但没有测试失败；依赖升级不属于本次 Engineering Review 的授权范围。

## 8. Known Gaps & Pending Questions

1. **输入预算**：F014 只规定最多 20 条 message，F012 只规定 context 字符数；question 和 history content 没有 token/字符上限。需要定义超限错误、截断 owner 与 provider context budget。
2. **空回答语义**：T0803 当前允许 provider 返回 `""`，而 T0804/T0805 会原样传递；这与 `AC-QA-01` 的 answer non-empty 目标以及 F013“空回答应是无信息回复”的描述存在 tension。需要产品/契约决定是否接受空字符串或由哪一层生成 fallback。
3. **Retrieval result schema**：T0804 假设结果包含 `file_name/content/final_score` 等字段；缺字段会在 assembler 处失败，当前没有 machine-readable malformed-result contract，也没有在 provider call 前的 schema validation。
4. **Failure ordering**：HTTP path 会在 storage work 前验证 history，但 direct service caller 在 retrieval/context 之后才触发 `INVALID_HISTORY_FORMAT`。需要决定 QAService 是否也应把所有纯输入 validation 前置。
5. **Context/source selection**：当前 sources 是 final Top-K，context 是预算内前缀；若产品文案说“sources used in answer”，需要澄清尾部 source 的展示语义。
6. **Retrieval composition duplication**：T0703 `retrieve()` 与 T0804 direct Hybrid path 并存；尚无统一 entry point、store factory 或跨入口回归矩阵。
7. **Provider resilience**：同步 retry 没有 jitter、circuit breaker、rate limit、cancellation 或 degraded mode；`LLM_TIMEOUT=60s` 是 transport timeout，不是整个 QA request SLA。
8. **Consistency/concurrency**：`get_chunk_count()` 与 retrieval 之间没有 snapshot contract；keyword cache 的 lock、multi-worker invalidation 和 store identity 仍是上游已知边界。
9. **Semantic quality**：当前没有真实 query/corpus relevance judgments，不能证明 `relevance_score` 与人工相关性一致，也不能证明 System Prompt 能抵抗真实 prompt injection。
10. **Integration proof**：真实 upload → Chroma → Hybrid → DeepSeek → HTTP 与 frontend history integration 仍需后续 Phase 12/T1202 责任内的 evidence；当前测试不能升级为 real E2E。

这些项目是工程边界和待决策项，不是本轮把 v1 scope 擅自扩大的理由。

## 9. Cross-links

- Technical Learning：[phase-08-rag-qa.md](../phase-08-rag-qa.md)
- Phase Gate / Phase Learning context：[phase-08-rag-qa.md#quick-review](../phase-08-rag-qa.md#quick-review)
- Source contract：[SPEC F012](../../SPEC.md#f012-rag-context-assembly) · [SPEC F013](../../SPEC.md#f013-llm-answer-generation) · [SPEC F014](../../SPEC.md#f014-conversation-memory) · [SPEC F015](../../SPEC.md#f015-source-citation) · [SPEC Section 6.4](../../SPEC.md#64-knowledge-qa)
- Task contract：[T0801](../../TASKS.md#t0801--context-assembly--source-assembly) · [T0802](../../TASKS.md#t0802--conversation-history-processing) · [T0803](../../TASKS.md#t0803--deepseek-chat-client) · [T0804](../../TASKS.md#t0804--qa-service-orchestration) · [T0805](../../TASKS.md#t0805--post-apiquery-endpoint)
- Upstream retrieval review：[phase-07-engineering-review.md](./phase-07-engineering-review.md)
- Project map：[dx-rag-project-map.md](../project-map/dx-rag-project-map.md)
- Interview Guide：[dx-rag-interview-guide.md](../interview-notes/dx-rag-interview-guide.md)

> **Ownership boundary**：Technical Learning 解释代码和学习 mental model；本文件记录 ADR、failure modes、一致性、规模与 Known Gaps；Interview Guide 负责项目故事和可复用回答。三者通过链接关联，不复制完整分析。

## 10. Review closure

本 Engineering Review 已完成并仅产生文档层变更；没有修改 `SPEC.md`、`TASKS.md`、Phase 8 application code，也没有启动下一 Phase、commit 或 push。既有 `PHASE_8_PASS — READY_FOR_PHASE_9` 是独立 Gate context，不由本文件重新裁定。真实 provider/Chroma/upload E2E、semantic quality 与 frontend integration 仍保持 `DEFERRED`。
