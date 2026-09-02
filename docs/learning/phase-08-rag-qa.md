# Phase 8 — RAG & QA 学习笔记

> **Phase 状态**：🟡 IN PROGRESS（T0801、T0802、T0803、T0804、T0805 DONE；Phase Gate Review 与 Phase Learning Review 尚未执行）
>
> **本文档状态**：T0805 Task Learning Pass 完成（2026-09-02）。本文在 T0801 的 context/source、T0802 的 Conversation History、T0803 的 DeepSeek Chat Client 与 T0804 QA Service orchestration 学习之上，增量记录 POST `/api/query` endpoint；不把尚未完成的 Phase 写成 complete。
>
> **配套文档**：[Phase 7 Technical Learning](./phase-07-vector-retrieval.md) · [DX-RAG Interview Guide](./interview-notes/dx-rag-interview-guide.md)

本章记录当前已落地的 T0801 RAG Context/Source Assembly、T0802 Conversation History Processing、T0803 DeepSeek Chat Client、T0804 QA Service orchestration 与 T0805 POST `/api/query` endpoint。T0801 把 T0702/T0703-compatible ranked retrieval chunks 转成给 LLM 的 context text 与 backend-owned source records；T0802 把前端携带的 history 校验、截断并格式化为 prompt 可嵌入文本；T0803 提供带六原则 System Prompt、OpenAI-compatible DeepSeek client、system + user 两条 API message（user 内含三个 sections）、bounded retry 与错误映射的 LLM adapter；T0804 再把 collection preflight、hybrid retrieval、context/history 转换、LLM call 与 sources 组装成一个 service-level result；T0805 在 FastAPI API boundary 执行请求校验、collection existence check、QAService 调用与统一错误响应。真实 provider/Chroma/upload E2E 与前端集成仍未验证。[PROJECT FACT]

## 0. 三层文档边界

| Layer | Canonical home | 本章怎么处理 |
|---|---|---|
| Layer 1 — Technical Learning | 本文 | 代码 mechanics、项目上下游、Python/TypeScript 学习点、数据流、验证边界和练习 |
| Layer 2 — Engineering Review | `engineering-review/phase-08-engineering-review.md`（当前尚未建立） | 这里只保留短的 engineering implication，不生成完整 ADR、failure taxonomy 或规模分析 |
| Layer 3 — Interview Preparation | [Interview Guide](./interview-notes/dx-rag-interview-guide.md) | 本 Task 只保留 Interview Candidates；完整话术等 Phase Gate 与 Phase Learning Review 后按 cadence consolidation |
| Phase Gate / Phase Learning Review / Task Learning Pass | [Gate template](./templates/phase-gate-review-template.md) · [Task Learning Pass workflow](./templates/phase-learning-pass-workflow.md) | 本文不能替代独立 Gate，也不能把 Task Learning Pass 写成 Phase 收口 |

T0801/T0802/T0803/T0804/T0805 的 `[PROJECT FACT]` 来自当前 `TASKS.md`、`SPEC.md`、`qa.py`、`query.py`、`router.py`、`main.py`、`config.py`、`schemas.py`、`errors.py`、`test_qa.py`、`test_query.py` 和本轮测试；`[ENGINEERING KNOWLEDGE]` 是可迁移的工程概念；`[FUTURE]` 明确表示当前尚未实现的能力。[PROJECT FACT]

## 1. Phase 学习：检索结果怎样变成可消费的上下文

### 一句话定位

Phase 8 的落地顺序体现了一个清晰边界：先把 evidence 变成受控输入，再处理对话上下文，准备并调用 LLM，由 service 编排这些步骤，最后在 API boundary 做请求/响应转换。T0801 用来源标签、separator 和字符预算生成 context，用固定字段生成 sources；T0802 将 history 变成经过校验、最多保留 20 条的 prompt 文本；T0803 把 System Prompt、history、context 和 question 组装成两条 API message，并负责有限重试与错误归一化；T0804 负责 collection preflight、retrieval、转换器与 LLM 的顺序，以及 answer/sources/result metadata 的组合；T0805 负责 `/api/query` 的输入校验、collection existence、service 调用与统一 error envelope。[PROJECT FACT]

### 学习重点

- 🟢 **必会**：`final_score DESC` 排序、完整 chunk 追加、`MAX_CONTEXT_CHARS` 边界、超限后的 `break`、`file_id`/`chunk_id` identity，history 的 role/content 校验、最近 20 条截断和 `User:/Assistant:` 格式，T0803 的六原则 System Prompt/两条 message/retry/error mapping，T0804 的 preflight → retrieval → assembly → LLM → sources 顺序，以及 T0805 的 question/collection/top_k/history 校验和统一错误 envelope。
- 🟡 **了解原理即可**：同一组 retrieval results 分成 context/source branches，history 是独立的 conversational context，DeepSeek client 是可注入的 OpenAI-compatible adapter，QAService 是同步 orchestration boundary；backend validation 是对前端 schema 的 defense in depth，且不负责持久化 history。
- 🔵 **知道存在即可**：HTTP endpoint 本身已由 T0805 实现。[PROJECT FACT] 真实 API key/LLM 调用、真实上传到问答的 E2E、Frontend history lifecycle、API-level semantic quality 与真实依赖集成仍属于后续验收。[FUTURE]

### 前置知识与学习路线

1. 先读 [Phase 7 Technical Learning](./phase-07-vector-retrieval.md)，确认 `HybridRetriever` 已输出 `final_score` 排序的 chunk records。
2. 对照 [F012](../SPEC.md#f012-rag-context-assembly)、[F014](../SPEC.md#f014-conversation-memory) 和 [F015](../SPEC.md#f015-source-citation)，分别读 context、history 与 source contracts。
3. 精读 [`assemble_context()`](../../backend/app/services/qa.py#L258-L270)、[`assemble_sources()`](../../backend/app/services/qa.py#L273-L285)、[`process_history()`](../../backend/app/services/qa.py#L288-L313)、[`DeepSeekClient`](../../backend/app/services/qa.py#L316-L473)、[`QAService`](../../backend/app/services/qa.py#L476-L545) 和 [`query()`](../../backend/app/api/query.py#L16-L68)。
4. 阅读 [`ContextAndSourceAssemblyTests`](../../backend/tests/test_qa.py#L428-L550)、[`HistoryProcessingTests`](../../backend/tests/test_qa.py#L553-L601)、[`DeepSeekClientTests`](../../backend/tests/test_qa.py#L604-L800)、[`QAServiceTests`](../../backend/tests/test_qa.py#L803-L935) 与 [`QueryEndpointTests`](../../backend/tests/test_query.py#L12-L233)，先预测转换、prompt、retry、preflight、HTTP status 和错误 envelope，再执行测试。
5. 最后回答：哪个字符串被计数、哪个 chunk 会被保留、sources 是否会因同一文件而合并、无效 history 为什么即使来自旧消息也会失败、为什么 client 自己关闭 SDK retry、API 为什么在 storage check 前拒绝非法 top_k，以及当前证据为什么仍不是真实 provider/Chroma E2E。[PROJECT FACT]

## 2. Phase 目标：为什么需要 Context 与 Sources

### 业务目标

检索结果本身只是若干候选 chunk，不是用户可读的答案；history 也不是知识库事实。LLM 需要有顺序、有来源标签且长度受控的 context，还需要用于指代消解的历史文本；用户又需要知道答案依据了哪些文件和 chunk。T0801 与 T0802 因此分别产出 evidence text/source records 和 conversational context。[PROJECT FACT]

### T0801 的技术目标

`assemble_context(chunks)` 的 contract 是：按 `final_score` 降序处理每个 chunk，格式化为 `[来源: file_name]\ncontent`，用 `\n\n---\n\n` 分隔；默认 `MAX_CONTEXT_CHARS=4000`，只有候选完整 context 的长度**大于**预算时才停止，恰好等于预算是允许的；如果加入下一个**完整格式化 chunk**会超过 `settings.MAX_CONTEXT_CHARS`，立即停止，不截断该 chunk，也不继续尝试后面的 chunk。[PROJECT FACT]

`assemble_sources(chunks)` 的 contract 是：按 `final_score` 降序映射每个 retrieval result 为 `{file_id, file_name, chunk_id, relevance_score}`，其中 `relevance_score` 等于 `final_score`；同一 `file_name` 的多个 chunk 仍保留，且 v1 不添加 `content_preview`。在同一份完整 retrieval Top-K 输入上，它会映射所有输入项，包括因 context 预算而未进入文本的尾部 chunk。[PROJECT FACT]

> **Contract note**：`TASKS.md` 的 F012 Detail shorthand 写成了格式串末尾带 `\n\n---\n\n`；`SPEC.md` 的详细规则、当前 `qa.py` 与测试则把 separator 理解为 chunks **之间**的分隔，不产生 trailing separator。本 Learning Pass 按当前详细规则和实现记录 observable behavior；是否要把 trailing separator 写入正式 contract，仍需一次显式的 SPEC/TASKS 决策，不能在 T0801 学习文档里默默改写。[PROJECT FACT]

### T0802 的技术目标

`process_history(history)` 的 contract 是：输入必须是 list；每个 message 必须是 dict，`role` 只能是 `"user"` 或 `"assistant"`，`content` 必须是 str。任何不符合格式的输入都抛出 `AppError("INVALID_HISTORY_FORMAT")`，其 error catalog 映射为 HTTP 400；通过校验后只保留最近 `settings.MAX_HISTORY_LENGTH` 条（当前默认 20），按原顺序格式化为 `User: {content}` / `Assistant: {content}`，用 `\n` 连接；空 history 返回 `""`。[PROJECT FACT]

F014 把 history 的生命周期 owner 定义为 Frontend：前端维护 React state、每次请求携带 history、切换 Knowledge Base 时清空；v1 不要求 backend 持久化、session management、user isolation 或 history search。[PROJECT FACT]

当前 frontend integration（F014）仍未实现；T0805 已在 HTTP boundary 完成 request validation、collection existence check、QAService 调用与统一错误映射，T0804 继续负责 service orchestration，T0803 负责 adapter-side message assembly 与 provider call，T0802 在 API 与 service 两层被用于防御性 history 校验。[PROJECT FACT]

### T0803 的技术目标

`DeepSeekClient` 是一个 OpenAI-compatible adapter：在真正需要生成答案时才读取 `DEEPSEEK_API_KEY` 并懒创建 `OpenAI` client，固定使用 DeepSeek `deepseek-chat`，把 `SYSTEM_PROMPT` 与下游传入的 history/context/question 组装成一条 `system` message 和一条 `user` message。调用参数来自配置（`temperature=0.2`、`max_tokens=2048`、`stream=false`、`timeout=60s`）；SDK 自带 retry 被设为 0，由 service 自己执行最多 2 次额外重试。[PROJECT FACT]

> **接线结果（T0804 已落地）**：`QAService.answer()` 先把 `assemble_context()` 与 `process_history()` 的 prepared text 传给 `DeepSeekClient.generate_answer()`，并显式传入 `SYSTEM_PROMPT`；F013 的三个 user sections 仍由 T0803 的 `_build_user_message()` 机械组装，T0804 不重复实现 builder。`TASKS.md` 中 “Build user message per F013 structure” 在当前实现里由 T0804 提供输入、T0803 完成 adapter-side assembly。[PROJECT FACT]

重试只覆盖 timeout/network、429 和 5xx，并按约 1s → 2s backoff；401/403 映射为 `LLM_AUTH_FAILED`，400 或非重试异常映射为 `LLM_RESPONSE_ERROR`，重试耗尽映射为 `LLM_UNAVAILABLE`。响应解析同时兼容 SDK object 与 mapping shape；缺 key 在调用时映射为 `LLM_NOT_CONFIGURED`。T0803 只返回 answer text，不生成 inline citation markers，sources 仍由 backend 的 T0801/F015 路径负责。[PROJECT FACT]

`SYSTEM_PROMPT` 把 F013 的六条规则写成 runtime policy：grounding、知识不足时的固定无信息回复、history 不作为事实来源、结构化 Markdown、检索文档指令不能覆盖 system prompt，以及不虚构/不生成内联来源标记。System prompt 能约束模型，但它本身不是 prompt-injection 的安全保证。[PROJECT FACT]


### 明确不做什么

- 不做 context summarization、compression 或中间 chunk truncation。
- 不按 `file_name` 去重 sources；source identity 仍然落到具体 `chunk_id`。
- 不让 LLM 生成 source records，也不在 T0801 调用 LLM。
- T0803 不实现 streaming、multi-model routing、startup API-key validation、prompt-injection detection、`QAService` 或 `/api/query`；不把 LLM answer 当作 source of truth，也不让 LLM 生成 inline citation markers。[PROJECT FACT]
- T0804 已把 collection preflight、`HybridRetriever.hybrid_search()`、context/history 转换、`DeepSeekClient.generate_answer()` 与 `assemble_sources()` 接成 service-level result；T0805 已提供请求校验、collection existence check、HTTP error envelope 与 `POST /api/query`，但不实现 streaming、conversation storage 或 rate limiting。[PROJECT FACT]

相关契约：[F012](../SPEC.md#f012-rag-context-assembly)、[F013](../SPEC.md#f013-llm-answer-generation)、[F014](../SPEC.md#f014-conversation-memory)、[F015](../SPEC.md#f015-source-citation)、[T0801](../TASKS.md#t0801--context-assembly--source-assembly)、[T0802](../TASKS.md#t0802--conversation-history-processing)、[T0803](../TASKS.md#t0803--deepseek-chat-client)、[T0804](../TASKS.md#t0804--qa-service-orchestration)、[T0805](../TASKS.md#t0805--post-apiquery-endpoint)，以及 LLM 配置（[`config.py:23-52`](../../backend/app/core/config.py#L23-L52)）和错误目录（[`errors.py:64-71`](../../backend/app/core/errors.py#L64-L71)）。

## 3. 项目位置：它连接哪两个边界

### 所属层

| 方向 | 上下游契约 | T0801–T0805 的作用 |
|---|---|---|
| Upstream | T0702 `HybridRetriever` → `List[dict]`，每项含 `file_id`、`file_name`、`chunk_id`、`content`、`final_score`；T0703 `retrieve()` 是另一条 facade 入口 | 不重新检索、不重新计算 score，只消费 ranked chunks |
| Context branch | F012 / T0804 orchestration input | 生成受 `MAX_CONTEXT_CHARS` 约束的纯文本，供 T0803 的 user-message builder 消费 |
| Source branch | F015 / T0804 QA response | 生成 backend-owned 的四字段 source list |
| History branch | F014 / T0804 orchestration input | T0802 校验、截断并格式化 history；T0803 再将其放入 user message，不持久化 history |
| LLM branch | F013 / DeepSeek Chat API | T0803 提供 System Prompt、message assembly、调用参数、retry 与 error mapping；不负责 retrieval/HTTP |
| Downstream | T0805 | T0804 已把 converters、retrieval 与 LLM 串成 service result；T0805 已将它接到 HTTP query endpoint |

### 查询侧位置

```text
POST /api/query (T0805) or direct service caller
    → [T0804] QAService.answer(question, collection, top_k, history)
         ├─→ VectorStore.get_chunk_count()
         │     0 chunks → COLLECTION_EMPTY / 409
         ├─→ HybridRetriever.hybrid_search()
         │     ranked retrieval chunks (T0702 behavior)
         ├─→ assemble_context() + process_history()
         │     prepared context/history text
         ├─→ [T0803] DeepSeekClient.generate_answer()
         │     SYSTEM_PROMPT + user sections → answer text
         └─→ assemble_sources()
               answer + sources + query + collection_name
               → service-level result dict
```

这里的关键边界是：context 是给模型的 evidence 输入文本，history 是用于 conversational context 的文本，sources 是 backend 维护的可审计结构；history 不是知识事实，sources 不应依赖模型是否听话，也不应从 LLM 输出中反解析。[PROJECT FACT]

## 4. Task 学习：T0801/T0802/T0803/T0804 输入准备、服务编排与 T0805 API 接线

### 4.1 A. Code Understanding

#### `assemble_context()` 的输入、输出和控制流

- **输入**：`List[Dict[str, object]]`，每项至少需要 `final_score`、`file_name` 和 `content`。
- **排序**：函数自己按 `final_score` descending 排序，因此即使调用方传入未排序列表，输出顺序仍按契约稳定化。
- **格式化**：每项变成 `[来源: {file_name}]\n{content}`。
- **预算判断**：把已有 formatted chunks 与候选 chunk 用 separator 拼成 `candidate`，再用 `len(candidate)` 与 `settings.MAX_CONTEXT_CHARS` 比较；默认预算是 4000，`len(candidate) == 4000` 仍会加入，只有 `> 4000` 才触发停止。
- **停止规则**：候选超限就 `break`；这表示该 chunk 以及它后面的 chunk 都不加入，而不是跳过当前 chunk 继续试。
- **输出**：已接受的 formatted chunks 再用相同 separator 连接；空输入或第一个 chunk 就超限时返回 `""`。[PROJECT FACT]

#### `assemble_sources()` 的输入、输出和控制流

- **输入**：排序后的 Hybrid retrieval result list（T0702 result shape；T0703 facade 也能产生兼容 shape）；每项至少需要 `file_id`、`file_name`、`chunk_id`、`final_score`。它不读取 `content`，因为 source projection 不复制正文。
- **排序**：按 `final_score` descending 排序，不依赖调用方已经排序。
- **投影**：只产生 `file_id`、`file_name`、`chunk_id`、`relevance_score` 四个键。
- **保留粒度**：列表推导逐 chunk 产生一条记录；同一文件的不同 `chunk_id` 不会被合并。
- **输出**：空输入返回 `[]`；没有 LLM、文件系统或 VectorStore side effect。[PROJECT FACT]

#### 这两个函数为什么都重新排序？

TASKS 说明输入 chunks 已按 `final_score` 排序，但函数边界再次排序是一种轻量的 defensive normalization：它让每个无外部 I/O 转换函数都能独立得到确定顺序，也不修改输入 list。代价是多一次排序；在 T0801 的小列表上，清晰的边界比提前优化更重要。[ENGINEERING KNOWLEDGE]

### 4.2 B. Project Understanding

1. **检索结果不是 prompt**：T0702/T0703-compatible 的结构化 dict 还需要转换，才能被后续 LLM client 消费。
2. **来源必须由 backend 组装**：F015 要求 sources 来自 retrieval results，而不是让模型“猜”文件名或生成引用。
3. **长度边界保护下游**：`MAX_CONTEXT_CHARS` 是配置层的约束，避免 prompt context 无界增长；T0801 不擅自压缩内容，因此超限策略是“停止加入完整 chunk”。
4. **身份不能降级成文件名**：同一文件可能贡献多个 chunk；`chunk_id` 是具体证据单元，`file_name` 只是 display name。[PROJECT FACT]

### 4.3 C. Learning Understanding

#### Python mental model

- `sorted(chunks, key=..., reverse=True)` 返回一个新列表，不会就地改写调用方的 list；Python sort 是 stable，因此 score 相同的项保留其输入相对顺序。[ENGINEERING KNOWLEDGE]
- `f"[来源: {chunk['file_name']}]\n{chunk['content']}"` 是 f-string + dict lookup。它类似 TypeScript 的 template literal，但 Python 的字典键访问缺少 TypeScript 的静态属性检查，键名错误会在运行时抛 `KeyError`。[ENGINEERING KNOWLEDGE]
- `"\n\n---\n\n".join(...)` 由 separator 所有者负责连接；不要在每个 chunk 内额外添加 separator，否则边界会重复。
- `break` 是本函数的业务规则，不是普通循环优化：因为契约要求按分数顺序停止，不能把超限 chunk 删除后继续收集低分 chunk。
- `len(candidate)` 计算 Python `str` 的 Unicode code point 数，不是 UTF-8 字节数，也不是 model token 数；当前 T0801 实现因此是 character budget，而非 token-aware budget。[ENGINEERING KNOWLEDGE]
- `List[Dict[str, object]]` 是 type annotation，不会像 TypeScript compiler 一样在运行时验证每个 dict 的键和值；当前保护来自契约、测试和调用边界。[ENGINEERING KNOWLEDGE]

#### TypeScript / Node.js 类比

```ts
type RetrievalChunk = {
  file_id: string;
  file_name: string;
  chunk_id: string;
  content: string;
  final_score: number;
};

// T0801 的概念等价物：先排序，再把完整 formatted chunk 放入 budget。
function assembleSources(chunks: RetrievalChunk[]) {
  return [...chunks]
    .sort((a, b) => b.final_score - a.final_score)
    .map(({ file_id, file_name, chunk_id, final_score }) => ({
      file_id,
      file_name,
      chunk_id,
      relevance_score: final_score,
    }));
}
```

这个类比只帮助迁移“无外部 I/O 转换 + map/sort + 明确输出 shape”的思路；Python 当前实现仍使用普通 dict，不能假设有 TypeScript 的 compile-time exhaustiveness。[ENGINEERING KNOWLEDGE]

### 4.4 T0801 验证学习：测试锁定了哪些 observable behavior

执行命令：

```text
cd backend
python -m unittest discover -s tests -p "test_*.py" -v
```

T0801 checkpoint 的结果是 **30/30 PASS**；T0802 checkpoint 后 suite 为 **34/34 PASS**；T0803 checkpoint 后为 **46/46 PASS**；T0804 checkpoint 后为 **50/50 PASS**；T0805 后当前完整 suite 为 **60/60 PASS**。其中 T0801 有 5 个无外部 I/O 转换 unit tests；另外执行 `python -m compileall -q app tests`，结果 PASS。[PROJECT FACT]

| 测试 | 证明什么 | 证据边界 |
|---|---|---|
| `test_context_formats_chunks_in_score_descending_order` | 乱序输入按 score 降序输出，来源标签和 separator 格式准确 | 纯 dict unit test；不包含 T0703/真实 storage |
| `test_empty_context_results_in_empty_string` | 空 retrieval results → `""` | 只验证函数边界，不验证后续 LLM 是否仍会被调用；这由 T0804 service test 与 T0805/API integration 负责 |
| `test_context_stops_before_chunk_that_exceeds_limit` | 已接受完整 chunks 后，下一项超限即停止 | 该 fixture 把超限项放在列表末尾，因此直接覆盖“超限项不加入”；“超限后更后面的项也不加入”由 `break` 代码路径保证，未被这个 fixture 单独展示 |
| `test_oversized_first_chunk_is_not_partially_truncated` | 单个 chunk 超过预算时返回空字符串，不截断一半 | 验证 no-mid-chunk 行为 |
| `test_sources_have_exact_fields_and_keep_same_file_chunks` | source 按 score 排序、保留同文件多 chunk、没有 `content_preview` | 纯 dict unit test；不验证 HTTP response schema |

因此可以说：T0801 的转换行为在当前 direct input boundary 已 unit-tested；不能说真实 T0703 → T0801 → LLM、HTTP `/api/query`、真实 prompt token budget 或 upload → answer E2E 已验证。[PROJECT FACT]

### 4.5 Interview Candidates（仅候选）

- 为什么 context 超限时选择 `break`，而不是跳过当前 chunk 再尝试后面的 chunk？
- `MAX_CONTEXT_CHARS` 计算的是 raw content，还是包含 source label 与 separator 的最终 context？如何从代码证明？
- 为什么 sources 不按 `file_name` 去重，而要保留每个 `chunk_id`？
- 为什么 source records 应由 backend 组装，而不是让 LLM 输出 `[来源: ...]`？
- 当前 5 个 T0801 tests 为什么不能证明真实 QA endpoint 会在空 context 时继续调用 LLM？

### 4.6 T0802 Conversation History Processing

#### A. Code Understanding

- **输入边界**：`process_history(history)` 的 annotation 是 `List[Dict[str, object]]`，但 annotation 不会在 runtime 自动校验；函数先显式要求顶层对象是 `list`。[PROJECT FACT]
- **逐条校验**：每条 message 必须是 `dict`；缺失键通过 `.get()` 得到 `None` 并失败；`role` 只接受小写 `user`/`assistant`，`content` 接受任意 `str`（包括空字符串）；额外键会被忽略。[PROJECT FACT]
- **先验后截断**：函数先遍历并校验全部输入，再执行 `validated[-settings.MAX_HISTORY_LENGTH:]`。当输入超过 20 条时，窗口之外的旧消息最终不会被使用，但其中一条格式非法仍会让整个调用失败；截断不是绕过 validation 的办法。[ENGINEERING KNOWLEDGE]
- **保留最近窗口**：当前 `MAX_HISTORY_LENGTH=20`；负切片取最后 20 条且保持它们原来的相对顺序，不会就地修改调用方 list。[PROJECT FACT]
- **输出格式**：使用 `message["role"].capitalize()` 生成 `User`/`Assistant` 前缀，再以 `\n` 连接各行；没有尾部换行。空 list 的 `join` 自然返回 `""`。[PROJECT FACT]
- **错误边界**：非法输入统一抛 `AppError("INVALID_HISTORY_FORMAT")`；error catalog 给它 400 状态。当前没有在 `process_history()` 内直接构造 HTTP response，endpoint mapping 留给 T0805。[PROJECT FACT]

#### B. Project Understanding

1. **Frontend 是生命周期 owner**：F014 规定 history 由 Frontend state 维护、每次 query request 携带；切换 Knowledge Base 时必须清空。v1 不做 backend persistence、session management、user isolation 或 history search。[PROJECT FACT]
2. **Schema 与 service 是两道边界**：`QueryRequest.history` 使用 Pydantic 的 `List[ChatMessage]` 描述请求 shape，但 T0802/T0804 的函数 contract/测试输入是普通 dict，是 defense in depth。[PROJECT FACT] T0805 已把 `ChatMessage` model 转成 plain dict 后传给 service；direct service caller 仍可直接传 plain dict。
3. **History 不是 evidence**：retrieval context 负责知识库事实，history 只帮助 pronoun resolution 和多轮上下文；T0804 已把两者的 prepared text 接入 T0803，并显式传入 `SYSTEM_PROMPT`。[ENGINEERING KNOWLEDGE]
4. **不要把 20 条误读成固定 10 轮**：SPEC 用“10 轮”描述理想的 user/assistant 交替；函数实际按 message 条数截断，不检查角色是否成对。[ENGINEERING KNOWLEDGE]

#### C. Learning Understanding

- 在 TypeScript 中可以把输入想成 `unknown`，先用 type guard 验证 `Array.isArray`、对象、literal union role 和 string content，再 `slice(-20)`；Python 当前实现用 `isinstance` 与 `set` membership 完成同一层 runtime narrowing。[ENGINEERING KNOWLEDGE]
- `validated[-20:]` 是 suffix window：保留最新消息而不是最早消息。先 validation 后 slicing 的顺序体现“数据合法性”和“上下文容量”是两个不同问题。[ENGINEERING KNOWLEDGE]
- `"\n".join(...)` 是格式化 owner；它只生成 prompt-ready history text，不添加 `## 对话历史` 标题，也不和 context/question 拼接。[ENGINEERING KNOWLEDGE]
- 复杂度是 O(n) 校验全部输入，加上 O(min(n, 20)) 格式化；T0802 没有引入 storage、网络或模型 side effect。[ENGINEERING KNOWLEDGE]

### 4.7 T0802 验证学习：测试锁定了哪些 observable behavior

T0802 使用同一条测试命令：

```text
cd backend
python -m unittest discover -s tests -p "test_*.py" -v
```

T0802 checkpoint 的结果是 **34/34 PASS**；T0803 checkpoint 后为 **46/46 PASS**；T0804 checkpoint 后为 **50/50 PASS**；T0805 后当前完整 suite 为 **60/60 PASS**。其中 T0802 有 4 个 test methods；另外执行 `python -m compileall -q app tests`，结果 PASS。[PROJECT FACT]

| 测试 | 证明什么 | 证据边界 |
|---|---|---|
| `test_history_is_formatted_in_order` | 按输入顺序输出 `User:`/`Assistant:` 行，换行连接且无额外尾部文本 | 直接调用 service；不证明 prompt 或 LLM 消费结果 |
| `test_empty_history_returns_empty_string` | 空 history → `""`，可支持单轮模式的下游输入 | 不验证 T0804 是否把空 history 传给 T0803 |
| `test_history_is_truncated_to_most_recent_twenty_messages` | 30 条输入只保留最近 20 条，旧消息被排除 | synthetic messages；不验证 Frontend state 或真实 HTTP body |
| `test_invalid_history_raises_invalid_history_format` | 缺失 role、非法 role、非字符串 content 等格式都抛 `AppError`，且 code/status 为 `INVALID_HISTORY_FORMAT`/400 | 验证 service error contract；不验证 FastAPI endpoint 的 JSON envelope |

这些测试足以证明 T0802 在 direct list/dict boundary 的逐条 message 校验、窗口和格式化行为；顶层 `history` 非 list 的 guard 来自代码与 contract 阅读，而不是独立 test case。它们不能证明 F014-01 的“它”指代已被 LLM 正确解析，也不能证明 30 条 history 经 `/api/query` 后真实进入 DeepSeek prompt。[PROJECT FACT]

### 4.8 T0802 Interview Candidates（仅候选）

- 为什么必须先校验全部 history，再截断最近 20 条？如果顺序相反，可能掩盖什么错误？
- `MAX_HISTORY_LENGTH=20` 是按 message 还是按 turn 计数？不完整的 user/assistant pair 会怎样？
- 为什么 `process_history()` 使用 `capitalize()` 和 `join()`，而不是把原始 role/content dict 直接交给 LLM？
- `QueryRequest` 已有 `ChatMessage` schema，为什么 service 还要做 runtime validation？
- history 由谁维护和清空？为什么 T0802 不应该把它写入 backend storage？

### 4.9 T0803 DeepSeek Chat Client

#### A. Code Understanding

- **System Prompt**：`SYSTEM_PROMPT` 是模块级的 runtime policy，逐条落实 F013 的 grounding、知识不足时的固定回复、history 不作为事实、结构化 Markdown、抗文档指令覆盖和不生成 inline citation 六原则。它还要求回答语言跟随用户问题；`DEFAULT_SYSTEM_PROMPT` 只是同一字符串的别名。[PROJECT FACT]
- **依赖注入与懒创建**：`DeepSeekClient(client=None)` 接受可注入的 OpenAI-compatible client；若没有注入，`_get_client()` 在真正调用 `generate_answer()` 时读取 `settings.get_deepseek_key()`，再创建 `OpenAI(api_key, base_url, timeout, max_retries=0)`。没有 key 是 `LLM_NOT_CONFIGURED`，SDK 不可用或 client 创建失败归一化为 `LLM_UNAVAILABLE`；应用启动时不会因为缺 key 失败。[PROJECT FACT]
- **User message assembly**：`_build_user_message()` 把 history、context、question 放入 `## 对话历史`、`## 参考文档`、`## 用户问题` 三个 section。空 history 省略第一段；空 context 替换为 `（知识库中暂无相关文档）`；它只返回 user message 的 content，不负责检索、sources 或 HTTP response。[PROJECT FACT]
- **两条 API message**：`generate_answer()` 把调用方传入的 `system_prompt` 放进 `{"role": "system"}`，把组装后的文本放进 `{"role": "user"}`。当前函数不会自动把 `DEFAULT_SYSTEM_PROMPT` 填进去；T0804 已显式传入 `SYSTEM_PROMPT`。[PROJECT FACT]
- **调用参数**：固定 model 为 `deepseek-chat`；temperature、max_tokens 和 stream 来自配置/实现（0.2、2048、false）。HTTP timeout 在 client construction 时设置为 60 秒；`max_retries=0` 则关闭 SDK 内建重试，把 retry ownership 留给本 service。[PROJECT FACT]
- **Retry policy**：`LLM_MAX_RETRIES` 被限制在 0–2，实际总尝试数为 `1 + retry_count`。timeout/network、429 和 5xx 才会重试；每次重试前 sleep 约 1s、2s。401/403 立即映射为 `LLM_AUTH_FAILED`，400 与其他不可重试异常映射为 `LLM_RESPONSE_ERROR`，重试耗尽映射为 `LLM_UNAVAILABLE`。[PROJECT FACT]
- **Response extraction**：`_extract_answer()` 同时读取 SDK object shape 与 mapping shape 的 `choices[0].message.content`；choices 缺失、为空、结构错误或 content 不是 str 都映射为 `LLM_RESPONSE_ERROR`。当前空字符串 answer 会原样返回，不会在 client 内自动补一段“无信息”文案。[PROJECT FACT]

#### B. Project Understanding

1. **Adapter boundary**：DeepSeek 使用 OpenAI-compatible protocol，因此 provider-specific base URL、model name、参数和异常差异被收敛在 `DeepSeekClient`；retrieval、context/source assembly 不需要知道 SDK 细节。[ENGINEERING KNOWLEDGE]
2. **Policy 与 data 分层**：system message 放不可被检索文档覆盖的行为规则；history、context、question 都作为 user message data 传入。System Prompt 是 prompt-level mitigation，不是可以保证 100% 抵御 prompt injection 的安全边界。[ENGINEERING KNOWLEDGE]
3. **Empty context 不是 empty collection**：T0803 只把传入的空 context 文本替换成提示语；collection 是否为空、是否应返回 `COLLECTION_EMPTY`，仍由 T0804 的 retrieval orchestration 决定。[PROJECT FACT]
4. **错误归一化的价值**：OpenAI SDK、网络异常和 HTTP status 的形状不统一；`_status_code()`、`_is_auth_error()` 与 `_is_retryable_error()` 把它们压缩为项目自己的 `AppError` code/status，后续 endpoint 才负责 JSON envelope。[ENGINEERING KNOWLEDGE]
5. **证据与答案分离**：T0803 只返回 answer text；F015 的 `sources` 仍来自 retrieval result 的 backend projection，不让模型生成或解析引用。[PROJECT FACT]

#### C. Learning Understanding

- 在 TypeScript/Node.js 中，可以把 `DeepSeekClient` 看成一个接受 `OpenAICompatibleClient` interface 的 class；测试时注入 fake client，生产时 lazy factory 创建真实 client。这相当于把 `fetch`/SDK 从业务函数中抽离，避免 unit test 真的访问网络。[ENGINEERING KNOWLEDGE]
- `system_prompt`、`history_text`、`context_text`、`question` 都是已经准备好的 `string`；T0803 的职责类似 `buildMessages()` + `callWithRetry()`，不是 `retrieve()` 或 `assemble_sources()`。[ENGINEERING KNOWLEDGE]
- Python 的 `Optional[Any]` 没有 TypeScript 的 compile-time interface guarantee，所以运行时仍需检查 client、status code、choices 和 content；`Mapping` 分支让同一解析器兼容 dict-like test double 与 SDK object。[ENGINEERING KNOWLEDGE]
- 这是同步 retry loop：`time.sleep()` 会阻塞当前线程。v1 的同步 service 可以接受这个边界；若未来改成 async FastAPI path，需要重新设计 awaitable backoff 与 client 生命周期。[FUTURE]

### 4.10 T0803 验证学习：测试锁定了哪些 observable behavior

T0803 使用同一条全量测试命令：

```text
cd backend
python -m unittest discover -s tests -p "test_*.py" -v
```

**在 T0803 checkpoint**，完整 suite 为 **46/46 PASS**；T0804 checkpoint 后为 **50/50 PASS**；T0805 后当前 suite 为 **60/60 PASS**。其中 T0803 有 12 个 test methods，另外执行 `python -m compileall -q app tests`，结果 PASS。[PROJECT FACT]

| 测试 | 证明什么 | 证据边界 |
|---|---|---|
| `test_generate_answer_assembles_prompt_and_uses_configured_options` | 两条 message、三段 user content、model/temperature/max_tokens/stream 参数按契约传给 client | 注入 `Mock` client；不证明真实 DeepSeek API 接受请求 |
| `test_empty_history_is_omitted_and_empty_context_uses_placeholder` | 空 history section 被省略，空 context 使用 F013 placeholder | 直接验证字符串组装；不证明 T0804 的 collection-empty policy |
| `test_system_prompt_covers_grounding_and_injection_rules` | 选定的 System Prompt 规则片段（知识不足回复、history/data separation、文档指令隔离和 no-inline-citation）存在 | 只断言这些片段；六原则的完整文本来自代码阅读，且不证明真实模型一定遵守规则 |
| `test_missing_api_key_is_checked_when_generating` | key 在调用时检查，缺失映射为 `LLM_NOT_CONFIGURED`/500 | patch settings；不覆盖进程启动或真实环境变量读取 |
| `test_client_is_created_lazily_with_deepseek_configuration` | client 延迟到首次生成时创建，并传入 DeepSeek base URL、timeout、`max_retries=0` | patch `OpenAI` 与 SecretStr；不连接真实 SDK/API |
| `test_timeout_retries_then_returns_answer` / `test_retryable_http_errors_are_retried` | timeout、429、500 会 sleep 后重试，第二次成功则返回 answer | 使用 synthetic exception 与 Mock；不证明真实网络异常分类完整 |
| `test_exhausted_retries_map_to_llm_unavailable` | 三次失败、两次 backoff 后抛 `LLM_UNAVAILABLE`/502 | patch `time.sleep`，不等待真实 1s/2s，也不验证 provider rate-limit headers |
| `test_auth_errors_fail_immediately_without_retry` / `test_bad_request_does_not_retry` | 401/403 不重试并映射 auth；400 不重试并映射 response error | `StatusError` substitute；不证明 SDK 各具体异常类的 inheritance |
| `test_malformed_response_maps_to_response_error` | 空 choices 等解析失败映射 `LLM_RESPONSE_ERROR`/500 | 只覆盖一种 malformed shape；不覆盖所有 provider response 变体 |
| `test_empty_answer_is_returned_without_error` | provider 返回空字符串时，client 原样返回空字符串 | 不证明产品是否应在 API 层补 no-info fallback；当前 T0805 也原样返回 |

这些测试覆盖了 T0803 的 service boundary、retry/error branches 和 message assembly，但所有 LLM 调用都使用 injected/patched doubles；没有真实 API key、真实 DeepSeek 网络请求、真实模型语义回答或 prompt-injection E2E。因此 AC-F013-01/02/03 的“回答质量/中文/不被文档指令覆盖”仍是未验证的 integration behavior；AC-F013-04 的重试与错误映射则在 synthetic unit boundary 有证据。T0804 的 4 个 orchestration tests 另行验证 service-level 顺序与分支，不提升 T0803 的 provider 证据等级。[PROJECT FACT]

### 4.11 T0803 Interview Candidates（仅候选）

- 为什么要把 OpenAI SDK 的 `max_retries` 设为 0，再由 service 自己管理最多 2 次重试？
- 为什么 `DEEPSEEK_API_KEY` 在调用时检查，而不是应用启动时检查？
- 哪些异常/HTTP status 可重试？为什么 400、401、403 不能重试？
- `system` message 与 `user` message 的职责怎样分开？检索文档中的恶意指令属于哪一层？
- 为什么 unit test 注入 `Mock` client 并 patch `time.sleep`，仍不能称为 DeepSeek E2E？
- `generate_answer()` 传入任意 `system_prompt` 而不是默认 `SYSTEM_PROMPT`，未来 QA Service 需要承担什么责任？
- 空 context placeholder、空 answer、empty collection 三者分别由哪个边界处理？
- 为什么 answer 与 sources 必须分开生成？如果让 LLM 生成 `[来源: ...]` 会引入什么风险？

### 4.12 T0804 QA Service Orchestration

#### A. Code Understanding

- **依赖注入（Dependency Injection）**：`QAService` 可以接收 `vector_store`、`hybrid_retriever` 和 `llm_client` 三个依赖；测试传入 `Mock`，生产调用方不传时再由 service 的 lazy getter 创建真实对象。[PROJECT FACT]
- **三个 lazy getter**：`_get_vector_store()` 缺依赖时创建 `ChromaVectorStore()`；`_get_hybrid_retriever()` 使用同一个 store 创建 `KeywordRetriever`、`VectorRetriever` 和 `HybridRetriever`；`_get_llm_client()` 缺依赖时创建 `DeepSeekClient()`。构造 `QAService` 本身不会访问 ChromaDB 或 DeepSeek。[PROJECT FACT]
- **Collection preflight**：`answer()` 先通过 `VectorStore.get_chunk_count(collection_name)` 检查持久化 chunk 数。数量为 0 时立即抛出 `AppError("COLLECTION_EMPTY")`，error catalog 将它映射为 HTTP 409；retrieval 和 LLM 都不会执行。[PROJECT FACT]
- **主控制流**：通过 preflight 后，调用 `HybridRetriever.hybrid_search(question, collection_name, top_k)`；再依次执行 `assemble_context(results)`、`process_history(history)`、`DeepSeekClient.generate_answer(SYSTEM_PROMPT, history_text, context_text, question)`，最后执行 `assemble_sources(results)`。[PROJECT FACT]
- **空结果分支**：non-empty collection 但 relevance filter 后 `results == []` 时，不抛 `COLLECTION_EMPTY`；context 是 `""`、sources 是 `[]`，仍会调用 LLM。至于模型是否返回“知识库中没有足够的信息”，属于 provider/后续集成行为，不是 QAService 自己生成的文案。[PROJECT FACT]
- **返回 shape**：service 只返回 `answer`、`sources`、`query`、`collection_name` 四个 key；它不是 FastAPI response model，也不负责 HTTP status 或 error envelope。[PROJECT FACT]
- **异常传播**：`QAService` 没有吞掉下游 `AppError`。例如 history 格式错误会在 retrieval 已完成后、LLM 调用前传播；LLM 的 `LLM_*` 错误也交给上层 API boundary。[PROJECT FACT]

#### B. Project Understanding

1. **T0804 是组合边界**：T0801/T0802/T0803 分别提供 context/source、history 和 LLM adapter；T0804 决定它们的调用顺序，并把 answer 与 backend-owned sources 组合成 service result。[PROJECT FACT]
2. **两个“空”必须分开**：`get_chunk_count() == 0` 表示 Knowledge Base 没有持久化数据，属于 `COLLECTION_EMPTY`；Hybrid 返回空则可能只是所有候选被 relevance filter 移除，仍需让 LLM 处理空 context。这两个状态不能共用一个错误。[PROJECT FACT]
3. **T0804 不重新实现 prompt builder**：它把 `SYSTEM_PROMPT`、`process_history()` 与 `assemble_context()` 的结果传给 T0803；F013 的 user sections 仍由 `DeepSeekClient` 的 adapter-side builder 组装。[PROJECT FACT]
4. **T0804 当前直接组装 retriever**：实现通过 `_get_hybrid_retriever()` 直接创建并调用 `HybridRetriever`，没有调用 module-level `retrieve()` facade；因此 T0703 facade 与 T0804 的 service orchestration 是两个可观察入口，不能把一次测试的调用对象写错。[PROJECT FACT]
5. **请求校验在 API boundary**：`QAService.answer()` 不负责 question、collection_name、top_k 的 HTTP/Pydantic 校验，也不负责把 `ChatMessage` model 转成 API response；T0805 的 `_parse_query_request()` 负责校验和 model conversion，路由再通过 `QueryResponse` 做 response validation。[PROJECT FACT]

#### C. Learning Understanding

- 在 TypeScript/Node.js 中，可以把 `QAService` 看成接受 `VectorStore`、`HybridRetriever`、`DeepSeekClient` interface 的 application service；单元测试注入 fake dependencies，生产环境才由 factory 创建 concrete adapters。[ENGINEERING KNOWLEDGE]
- `_get_*()` 是带缓存的 lazy factory：第一次需要时创建并写回 `self.xxx`，后续调用复用同一实例。这类似把 `let client` 与 `getClient()` 封装起来，但 Python 这里没有 TypeScript compiler 替你检查 interface。[ENGINEERING KNOWLEDGE]
- `raise` 的短路效果是 control-flow contract：empty collection 在第一道 guard 结束；history/LLM 异常则沿调用栈冒泡，`answer()` 不用一个大 `try/except` 把不同错误压成同一结果。[ENGINEERING KNOWLEDGE]
- 这是同步 orchestration，不是异步并行调度：一次调用内先完成 preflight、retrieval、文本转换、LLM call，再投影 sources。若未来要并行 keyword/vector 或引入 streaming，必须重新审视 timeout、错误 owner 与 API contract。[ENGINEERING KNOWLEDGE]

### 4.13 T0804 验证学习：测试锁定了哪些 observable behavior

T0804 仍使用同一条全量测试命令：

```text
cd backend
python -m unittest discover -s tests -p "test_*.py" -v
```

**在 T0804 checkpoint**，完整 suite 为 **50/50 PASS**；T0805 后当前 suite 为 **60/60 PASS**。其中 T0804 有 4 个 `QAServiceTests` test methods，另外执行 `python -m compileall -q app tests`，结果 PASS。[PROJECT FACT]

| 测试 | 证明什么 | 证据边界 |
|---|---|---|
| `test_answer_runs_full_pipeline_and_returns_sources` | service 依次消费 collection count、hybrid results、context/history converters 与 LLM answer，并返回四字段 result；`SYSTEM_PROMPT` 和 prepared text 传给 LLM，sources 按 score 投影（调用顺序由 `qa.py` 实现确认） | `VectorStore`、`HybridRetriever`、`DeepSeekClient` 都是 Mock，测试未单独断言跨依赖 call order；不证明真实 Chroma、retrieval、DeepSeek 或 HTTP response |
| `test_empty_collection_raises_before_retrieval_or_llm` | `get_chunk_count() == 0` → `COLLECTION_EMPTY`/409，且 retrieval 与 LLM 均未调用 | 证明 service-level preflight；HTTP 409 envelope 由 T0805 endpoint tests 另行验证 |
| `test_relevance_filtered_empty_still_calls_llm_with_empty_context` | non-empty collection + `hybrid_search() == []` → LLM 仍收到空 history/空 context，最终 sources 为 `[]` | LLM 是 Mock；不证明真实模型会返回 F013 的 no-information 文案 |
| `test_history_validation_error_propagates_before_llm_call` | retrieval 已发生后，非法 history 抛 `INVALID_HISTORY_FORMAT`，LLM 不被调用 | 只锁定当前同步顺序；不覆盖 API/Pydantic validation 或真实 frontend history |

这些测试证明的是 **service-level composition boundary**，不是 literal upload → ChromaDB → DeepSeek → HTTP E2E。T0804 的 collection-empty 与 relevance-filter-empty 分支有 Mocked unit evidence；T0805 已增加 route-level `TestClient` tests 验证 HTTP status/envelope，但 AC-F013-01/02/03 的真实模型语义、真实 provider/Chroma、Frontend history lifecycle 与 upload → answer E2E 仍待集成验收。[PROJECT FACT]

### 4.14 T0804 Interview Candidates（仅候选）

- 为什么必须先调用 `get_chunk_count()`，而不是让 `HybridRetriever` 返回空列表后统一处理？
- `COLLECTION_EMPTY` 与 relevance-filter-empty 的业务语义、HTTP 状态和 LLM 行为分别是什么？
- 为什么 `QAService` 要让 `VectorStore`、retriever 和 LLM client 可注入，并且 lazy 创建？
- 当前 T0804 为什么直接调用 `HybridRetriever.hybrid_search()`，而不是复用 T0703 的 module-level `retrieve()` facade？这两个入口的 owner 有什么差异？
- 为什么非法 history 的测试里 retrieval 已经调用，但 LLM 没有调用？这暴露了怎样的 control-flow 顺序？
- 为什么 `assemble_sources()` 放在 LLM 调用之后？如果 LLM 失败，当前 service 是否会返回 sources？
- 为什么 `QAService.answer()` 不直接返回 HTTP 409/502？哪一层应该拥有 response envelope？

### 4.15 T0805 POST `/api/query` Endpoint

#### A. Code Understanding

- **路由位置与注册**：`backend/app/api/query.py` 定义 `APIRouter` 和 `POST /query`；`backend/app/api/router.py` include 该 sub-router，`backend/app/main.py` 再以 `/api` prefix 注册，因此对外路径是 `POST /api/query`。[PROJECT FACT]
- **手动请求解析**：路由参数使用 `Body(default=None)` 接收 `Any`，先由 `_parse_query_request()` 做显式校验，再构造 `QueryRequest`。这让缺 body、非 object JSON、字段缺失和类型错误都能落到项目自己的 `AppError` code，而不是直接暴露框架默认 422 shape。[PROJECT FACT]
- **字段校验**：`question` 与 `collection_name` 必须是非空字符串；`top_k` 缺省使用 `settings.DEFAULT_TOP_K`（当前 5），拒绝 bool、非 int 和 `[settings.TOP_K_MIN, settings.TOP_K_MAX]`（当前 1–20）之外的值；`history` 缺省为 `[]`，非 list 或不符合 T0802 role/content contract 时抛 `INVALID_HISTORY_FORMAT`。[PROJECT FACT]
- **存在性与 service 调用**：请求通过字段校验后创建 `ChromaVectorStore`，用 public `list_collections()` 检查目标 collection；不存在时抛 `COLLECTION_NOT_FOUND`，不会创建/调用 `QAService`。存在时把同一个 store 注入 `QAService`，并将 Pydantic `ChatMessage` 转成 plain dict 传给 `QAService.answer()`。[PROJECT FACT]
- **响应模型**：`@router.post(..., response_model=QueryResponse)` 把 service result 验证成 `{answer, sources, query, collection_name}`；`QueryResponse` 与 SPEC Section 6.4 的 200 response shape 对齐，sources 仍是 backend-owned records。[PROJECT FACT]
- **统一错误出口**：endpoint 不重复 catch 每个 `AppError`，而是让 `main.py` 的全局 `app_error_handler` 依据 error catalog 生成 `{error: {code, message, details}}`；未预期异常由 catch-all handler 映射为 `INTERNAL_ERROR`/500。[PROJECT FACT]

#### B. Project Understanding

1. **API 是 boundary adapter**：T0805 负责 HTTP body → `QueryRequest` → service call → `QueryResponse`，不负责 retrieval ranking、prompt layout 或 history persistence。[PROJECT FACT]
2. **校验顺序有副作用含义**：非法 question/top_k/history 在创建 Chroma store 或调用 collection existence check 前被拒绝；missing collection 在 QAService preflight 前返回 404；empty collection 则由 T0804 返回 409；relevance-filter-empty 继续走 LLM 并返回 200。[PROJECT FACT]
3. **Pydantic 与 runtime validation 是两层防线**：`QueryRequest`/`ChatMessage` 描述 API shape，`_parse_query_request()` 和 T0802 `process_history()` 又把关键约束显式执行，避免 `Any` body 或 plain dict 绕过业务语义。[PROJECT FACT]
4. **错误 envelope 归属应用层**：路由抛出 machine-readable `AppError`，全局 handler 统一 status/message/details；因此 service 不需要知道 FastAPI `JSONResponse`，API 也不需要复制 LLM/embedding 的错误分类。[ENGINEERING KNOWLEDGE]
5. **当前实现是同步 HTTP adapter**：没有 conversation storage、streaming、rate limiting 或真实 provider fallback；这些不因 endpoint 注册成功而自动存在。[PROJECT FACT]

#### C. Learning Understanding

- 在 TypeScript/Node.js 中，可以把 `query.py` 看成 controller/route adapter：先把 `unknown` body 解析成 `QueryRequest`，再调用 application service，最后返回 `QueryResponse`。全局 `AppError` handler 类似统一 middleware error boundary。[ENGINEERING KNOWLEDGE]
- `response_model` 类似 TypeScript 的 output schema，但运行时仍由 Pydantic 执行；类型注解本身不会替代 service/API 的错误路径测试。[ENGINEERING KNOWLEDGE]
- `list_collections()` 是 API-level existence check，`get_chunk_count()` 是 service-level empty-state check：两个检查都看 storage，但语义和 HTTP 责任不同。[ENGINEERING KNOWLEDGE]

### 4.16 T0805 验证学习：测试锁定了哪些 observable behavior

T0805 使用真实 FastAPI `TestClient`，但把 `ChromaVectorStore` 与 `QAService` patch 成 Mock，因此这是 **route-level mocked integration**，不是真实 Chroma/DeepSeek E2E：[PROJECT FACT]

```text
cd backend
python -m unittest discover -s tests -p "test_*.py" -v
```

T0805 增加 10 个 `QueryEndpointTests` test methods；T0804 checkpoint 的 50/50 加上它们后，当前完整 suite 为 **60/60 PASS**。[PROJECT FACT]

| 测试 | 证明什么 | 证据边界 |
|---|---|---|
| `test_valid_query_returns_exact_response_shape` | 合法 body 返回 HTTP 200、四字段 response，并把 history model 转成 service plain dict | `ChromaVectorStore`/`QAService` 是 Mock；不证明真实 retrieval/LLM |
| `test_omitted_optional_fields_use_spec_defaults` | 缺省 `top_k` 使用 5，缺省 history 使用 `[]` | 只验证当前 config/default；不覆盖环境覆盖值 |
| `test_no_matching_content_returns_200_with_empty_sources` | relevance-filter-empty 的 response 仍为 200 且 sources=[] | answer 是 synthetic service output；不证明真实模型会生成 F013 no-information 文案 |
| `test_collection_empty_maps_to_409` | service 的 `COLLECTION_EMPTY` 映射为 409 统一 envelope | QAService 本身是 Mock；不证明真实 Chroma count |
| `test_llm_and_embedding_errors_use_unified_error_mapping` | `LLM_NOT_CONFIGURED`/`LLM_AUTH_FAILED`/`LLM_RESPONSE_ERROR`/`EMBEDDING_MODEL_ERROR` 为 500，`LLM_UNAVAILABLE` 为 502 | 使用 synthetic `AppError`；不覆盖真实 SDK/embedding 异常分类 |
| `test_missing_collection_returns_404_without_calling_service` | collection existence check 先于 service，缺失时返回 404 | storage list 是 Mock；不证明真实 collection lifecycle |
| `test_invalid_top_k_returns_400_without_storage_or_service_work` | 0/21/-1 在 storage check 前映射为 `INVALID_TOP_K`/400 | 只覆盖列出的边界；不做性能/并发验证 |
| `test_empty_question_or_collection_returns_invalid_query` | 空/空白/缺失 question 或 collection 映射为 `INVALID_QUERY`/400 | 不覆盖 collection-name regex；存在性由后续 check 负责 |
| `test_invalid_history_returns_400_without_storage_or_service_work` | 非 list、非法 role/content 等 history 映射为 `INVALID_HISTORY_FORMAT`/400 | service history 的完整行为由 T0802/T0804 tests 覆盖 |
| `test_non_object_body_returns_invalid_query` | null/list/string body 不进入 storage/service，返回 `INVALID_QUERY`/400 | TestClient JSON body boundary；不覆盖 multipart/streaming |

这些 tests 锁定的是 **HTTP route + error envelope + service delegation** 的可观察行为。它们证明 AC-QA-05/06、invalid query/history、missing collection 与 LLM/embedding error mapping 的 Mocked route boundary；AC-QA-01 的非空答案质量、AC-QA-02 的真实 no-information 文案、AC-QA-03 指代消解、AC-QA-04 relevance semantic quality、真实 `list_collections()`/`get_chunk_count()`、真实 provider 和 upload → Chroma → `/api/query` E2E 仍是 DEFERRED。[PROJECT FACT]

`TASKS.md` 的 `DONE` 是任务状态字段；本 Learning Pass 将其解释为 T0805 的 implementation/route-contract slice 已完成，而不是真实 DeepSeek/Chroma/upload E2E 或 AC-QA-01～04 的语义质量已经通过。[PROJECT FACT]

### 4.17 T0805 Interview Candidates（仅候选）

- 为什么 endpoint 使用手动 `_parse_query_request()`，而不是直接把 `QueryRequest` 作为 FastAPI 参数？这对 error envelope 有什么影响？
- `list_collections()` 的 404、`get_chunk_count()==0` 的 409、relevance-filter-empty 的 200 为什么必须分开？
- 为什么非法 `top_k` 要在 storage construction/existence check 前拒绝？
- `QueryRequest` 的 Pydantic history 校验与 T0802 `process_history()` 的 runtime 校验是否重复？各自保护什么？
- `response_model=QueryResponse` 验证了什么，为什么仍不能证明真实 LLM answer？
- 全局 `AppError` handler 如何把 service/LLM 的 machine-readable code 变成统一 HTTP response？
- 10 个 endpoint tests 为什么属于 route-level mocked integration，而不是 upload → Chroma → DeepSeek E2E？

## 5. 代码理解：关键代码逐行精读

### 5.1 `assemble_context()`：格式化和预算是一个原子决策

真实代码：[`qa.py:258-270`](../../backend/app/services/qa.py#L258-L270)。核心片段：

```python
context_chunks: List[str] = []
for chunk in sorted(
    chunks, key=lambda item: item["final_score"], reverse=True
):
    formatted = f"[来源: {chunk['file_name']}]\n{chunk['content']}"
    candidate = "\n\n---\n\n".join(context_chunks + [formatted])
    if len(candidate) > settings.MAX_CONTEXT_CHARS:
        break
    context_chunks.append(formatted)

return "\n\n---\n\n".join(context_chunks)
```

逐段读：

1. `context_chunks` 只保存**已经通过预算检查**的字符串，而不是原始 dict；因此后面不需要再次格式化。
2. `sorted(... reverse=True)` 把 highest score 放在前面。context 的顺序因此和 Hybrid Retrieval 的 relevance 语义一致。
3. `formatted` 同时加入 source label 和 content。标签在这里生成，后面的 LLM 不需要自己猜来源。
4. `candidate` 先模拟“如果现在加入它，完整输出会是什么”，再测长度。这比先 append 再回滚更容易读，也避免短暂持有一个越界状态。
5. `break` 把长度规则落实成 control-flow policy：排序靠前的超限 chunk 一旦不能完整加入，后续更低分 chunks 也不再进入 context。
6. 最后一行只连接已接受项；空列表的 `join` 自然返回 `""`，所以 empty result 不需要单独的 special branch。[PROJECT FACT]

### 5.2 `assemble_sources()`：projection 不是摘要

真实代码：[`qa.py:273-285`](../../backend/app/services/qa.py#L273-L285)。

```python
return [
    {
        "file_id": chunk["file_id"],
        "file_name": chunk["file_name"],
        "chunk_id": chunk["chunk_id"],
        "relevance_score": chunk["final_score"],
    }
    for chunk in sorted(
        chunks, key=lambda item: item["final_score"], reverse=True
    )
]
```

这里没有 content 拼接、去重、摘要或模型调用。`relevance_score` 是字段名的 API-facing projection，但数值仍沿用 Hybrid 的 `final_score`；T0801 没有偷偷发明第二套分数。[PROJECT FACT]

### 5.3 `process_history()`：validation、suffix window 与格式化

真实代码：[`qa.py:288-313`](../../backend/app/services/qa.py#L288-L313)；配套请求 shape 在 [`schemas.py:18-27`](../../backend/app/models/schemas.py#L18-L27)，错误目录在 [`errors.py:64-75`](../../backend/app/core/errors.py#L64-L75)。核心片段：

```python
if not isinstance(history, list):
    raise AppError("INVALID_HISTORY_FORMAT")

validated: List[Dict[str, str]] = []
for message in history:
    if not isinstance(message, dict):
        raise AppError("INVALID_HISTORY_FORMAT")

    role = message.get("role")
    content = message.get("content")
    if (
        not isinstance(role, str)
        or role not in {"user", "assistant"}
        or not isinstance(content, str)
    ):
        raise AppError("INVALID_HISTORY_FORMAT")

    validated.append({"role": role, "content": content})

recent_messages = validated[-settings.MAX_HISTORY_LENGTH :]
return "\n".join(
    f"{message['role'].capitalize()}: {message['content']}"
    for message in recent_messages
)
```

逐段读：

1. 顶层和每条 message 都做 runtime type check；`.get()` 让缺失字段进入统一失败分支，而不是产生半格式化文本。
2. `not isinstance(role, str)` 放在 `role not in {"user", "assistant"}` 前面，利用 `or` short-circuit 安全拒绝 list 等不可哈希值；role 通过后才检查两个允许值。
3. `validated` 先复制出受控的 `{role, content}` shape，再对完整输入做 suffix slicing；extra keys 不会流入后续 prompt。
4. `validated[-settings.MAX_HISTORY_LENGTH:]` 取最新窗口，当前默认 20；输入少于 20 条时全部保留，空 list 时循环为空且最终返回空字符串。
5. `capitalize()` 把受控的小写 role 转成展示前缀，`join()` 只负责行间换行；它不添加标题、context 或 question。[PROJECT FACT]
6. `AppError` 保存 machine-readable code，`errors.py` 再提供 400 状态和中文默认消息；HTTP envelope 由全局 handler/API boundary 负责，而不是本函数负责。[PROJECT FACT]

### 5.4 `DeepSeekClient`：从 policy 到 bounded API call

真实代码：[`qa.py:46-54`](../../backend/app/services/qa.py#L46-L54) 的 `SYSTEM_PROMPT`，以及 [`qa.py:316-473`](../../backend/app/services/qa.py#L316-L473) 的 `DeepSeekClient`；配置来自 [`config.py:23-52`](../../backend/app/core/config.py#L23-L52)。核心调用路径可以压缩成：

```text
SYSTEM_PROMPT + prepared history/context/question
        │
        ▼
DeepSeekClient.generate_answer()
        │
        ├─ _get_client(): injected client 或 lazy OpenAI(api_key, base_url, timeout)
        ├─ _build_user_message(): 省略空 history，替换空 context，拼接三个 section
        ├─ messages: system policy + user data
        ├─ create(model, temperature, max_tokens, stream=False)
        ├─ retry timeout/network/429/5xx，backoff 1s → 2s
        └─ _extract_answer(): choices[0].message.content → str
```

逐段读：

1. `SYSTEM_PROMPT` 是静态字符串，不是每次请求拼出来的知识库内容；因此文档中的“请忽略之前指令”只能出现在 user data/context 侧，不能改变 system message 的优先级。[PROJECT FACT]
2. `_get_client()` 先看 dependency injection，再在首次调用时读取 SecretStr 的明文 key。`OpenAI` 的 `base_url` 指向 DeepSeek，`max_retries=0` 避免 SDK retry 与 service retry 叠加；创建异常被收敛为 `LLM_UNAVAILABLE`。[PROJECT FACT]
3. `_build_user_message()` 不重复包一层 system policy；它只负责 section layout。空 history 直接省略，空 context 使用 F013 指定 placeholder，question 即使为空也会被原样放入本函数的 user section，输入校验属于更上游的 Query/API contract。[PROJECT FACT]
4. `generate_answer()` 把 `LLM_MAX_RETRIES` clamp 到 0–2，循环最多三次。异常路径和“返回了带 status code 的 response”路径都经过同一组 auth/retry 判断，因此 401/403 不会 sleep，429/5xx 才进入 backoff。[PROJECT FACT]
5. `_extract_answer()` 故意兼容 attribute-based SDK objects 与 dict-like test doubles；它只抽取文本，不替 answer 加来源、不清洗 Markdown，也不把空字符串改写成固定拒答。[PROJECT FACT]

这里的关键不是“写了一个 HTTP request”，而是把四种责任分开：policy（System Prompt）、data layout（user message）、transport/retry（OpenAI call）和 response normalization（answer extraction）。这种分层让已经实现的 T0804 可以组合已有 converter，而不必重新知道 provider 的异常类和 response shape。[ENGINEERING KNOWLEDGE]

### 5.5 `QAService.answer()`：把窄职责模块串成一次 service call

真实代码：[`qa.py:476-545`](../../backend/app/services/qa.py#L476-L545)，对应测试：[`QAServiceTests`](../../backend/tests/test_qa.py#L803-L935)。核心片段：

```python
vector_store = self._get_vector_store()
if vector_store.get_chunk_count(collection_name) == 0:
    raise AppError("COLLECTION_EMPTY")

results = self._get_hybrid_retriever().hybrid_search(
    question, collection_name, top_k
)
context_text = assemble_context(results)
history_text = process_history(history)
answer_text = self._get_llm_client().generate_answer(
    SYSTEM_PROMPT,
    history_text,
    context_text,
    question,
)
sources = assemble_sources(results)

return {
    "answer": answer_text,
    "sources": sources,
    "query": question,
    "collection_name": collection_name,
}
```

逐段读：

1. `_get_vector_store()` 是第一个依赖边界；先拿到 public `VectorStore`，再做 `get_chunk_count()` preflight。这里没有访问 ChromaDB 的 private collection，也没有把“查不到结果”先交给 LLM 猜。[PROJECT FACT]
2. `== 0` 的 guard 是业务语义分叉：空 Knowledge Base 抛 `COLLECTION_EMPTY`；它发生在 `hybrid_search()` 之前，所以没有 retrieval side effect，也没有 LLM side effect。[PROJECT FACT]
3. `_get_hybrid_retriever().hybrid_search(...)` 直接调用 HybridRetriever，并把 `top_k` 原样传入；当前 QAService 没有调用 T0703 的 module-level `retrieve()` facade。retriever 的内部 `top_k * 2` branch recall、fusion、filter 和最终 Top-K 仍由 T0702/T0703 相关实现负责。[PROJECT FACT]
4. `assemble_context(results)` 与 `process_history(history)` 把结构化 retrieval/history 输入转成两个 prepared strings；QAService 不重新计算 score，也不持久化 history。[PROJECT FACT]
5. `_get_llm_client().generate_answer(...)` 显式传入 `SYSTEM_PROMPT`，然后把 history、context 和 question 交给 T0803；QAService 负责“何时调用”，DeepSeekClient 负责 message layout、provider I/O、retry 和 response parsing。[PROJECT FACT]
6. `assemble_sources(results)` 使用同一批 filtered retrieval results 生成 backend-owned source records；它在 LLM 调用之后执行，因此当前 LLM 失败时，service 不会返回一个半成品 result。[PROJECT FACT]
7. 最后的 dict 是 service-level contract；T0805 的 route 再通过 `QueryResponse` 验证它，并负责 HTTP status、错误 envelope 和路由注册。[PROJECT FACT]

这段代码的设计重点是 **orchestration order**，不是把所有业务塞进一个函数：preflight 保护“空库”语义，retrieval 产出 evidence，两个 converter 准备文本，LLM 产生 answer，source projector 保留审计信息。把依赖作为 constructor 参数并在 getter 中 lazy 创建，则让同一条 control flow 可以被真实 adapter 或测试 double 消费。[ENGINEERING KNOWLEDGE]

### 5.6 失败路径与输入假设

T0801 的两个 assembly 函数是窄职责的无外部 I/O 转换层，因此没有 input validation 或 exception translation：缺少必需 retrieval key 时，Python 原生 `KeyError`/`TypeError` 可能向上传播；空 list 是合法输入，返回 `""` 或 `[]`。T0802 显式把非法 history 映射到 `AppError("INVALID_HISTORY_FORMAT")`，T0803 把 LLM transport/response 问题映射到 `LLM_NOT_CONFIGURED`、`LLM_AUTH_FAILED`、`LLM_UNAVAILABLE` 或 `LLM_RESPONSE_ERROR`；T0804 不吞掉这些异常，T0805 的全局 API handler 再负责 HTTP response envelope。T0804 自己新增的主要失败出口是 `COLLECTION_EMPTY`，T0805 新增的主要 API 失败出口是 `INVALID_QUERY`、`INVALID_TOP_K` 与 `COLLECTION_NOT_FOUND`，以及下游 retrieval/converter/LLM 异常的统一映射。[PROJECT FACT]

### 5.7 `query()`：把 service result 接到 HTTP boundary

真实代码：[`query.py:16-68`](../../backend/app/api/query.py#L16-L68)，路由注册见 [`router.py:1-19`](../../backend/app/api/router.py#L1-L19)，全局错误处理见 [`main.py:43-67`](../../backend/app/main.py#L43-L67)。核心片段：

```python
request = _parse_query_request(body)

vector_store = ChromaVectorStore()
if request.collection_name not in vector_store.list_collections():
    raise AppError("COLLECTION_NOT_FOUND")

result = QAService(vector_store=vector_store).answer(
    request.question,
    request.collection_name,
    request.top_k,
    [message.model_dump() for message in request.history],
)
return QueryResponse.model_validate(result)
```

逐段读：

1. `Body(default=None)` 让 route 能看到原始 JSON；`_parse_query_request()` 先拒绝非 object、空 question/collection、越界 `top_k` 和非法 history，并把它们统一成 `AppError`。[PROJECT FACT]
2. `list_collections()` 只做 existence check。missing collection 返回 404；只有存在的 collection 才进入 T0804，后者再用 `get_chunk_count()` 区分 empty collection 的 409。[PROJECT FACT]
3. `message.model_dump()` 是 API → service 的 normalization seam：HTTP 层使用 `ChatMessage` model，T0804/T0802 仍消费 plain dict，不把 Pydantic 类型泄露成下游 prompt contract。[PROJECT FACT]
4. `QueryResponse.model_validate(result)` 锁定 response shape；它不验证 answer 的事实正确性，也不调用 LLM。[PROJECT FACT]
5. `query()` 自己不捕获每种下游错误；`AppError` 交给 `app_error_handler`，未知异常交给 catch-all handler。这样 status、machine-readable code 和 `{error: {code, message, details}}` 由单一 owner 统一生成。[ENGINEERING KNOWLEDGE]

## 6. 数据流与 Mental Model

### 6.1 完整数据流

```text
POST /api/query (T0805) or direct service caller
       │
       ▼
T0804 QAService.answer(question, collection, top_k, history)
       │
       ├── VectorStore.get_chunk_count()
       │     0 → AppError("COLLECTION_EMPTY") / 409
       │
       ├── HybridRetriever.hybrid_search()
       │     → List[retrieval dict] (final_score / identity / content)
       │
       ├── assemble_context(results)
       │     sort → format → candidate length check → str context
       │
       ├── process_history(history)
       │     validate → latest 20 → User:/Assistant: lines → str history
       │
       ├── T0803 DeepSeekClient.generate_answer()
       │     SYSTEM_PROMPT + prepared texts → str answer
       │
       ├── assemble_sources(results)
       │     sort → exact four fields → List[source dict]
       │
       └── {answer, sources, query, collection_name}
             → T0805 QueryResponse + HTTP 200
```

### 6.2 类型变化

| 阶段 | 类型 | 关键变化 |
|---|---|---|
| T0805 HTTP 输入 | JSON object | `_parse_query_request()` 校验 question、collection_name、top_k、history，再构造 `QueryRequest` |
| T0804 输入 | `question + collection_name + top_k + history` | T0805 传入 service 的已校验/转换 shape；direct service caller 仍可传 plain dict history |
| Preflight | `int` | `VectorStore.get_chunk_count()` 决定 `COLLECTION_EMPTY` 分支 |
| T0702/T0703 retrieval 输出 | `List[Dict]` | 每项有 chunk content、identity 和 `final_score` |
| Context branch | `List[str]` → `str` | dict 被格式化，完整项按字符预算累积 |
| Source branch | `List[Dict]` | dict 被投影为四字段 source record |
| LLM branch | `str` inputs → `List[Dict]` messages → `str` | system/user message assembly、provider call、retry 和 response extraction |
| QA result | `Dict[str, object]` | answer、sources、query、collection_name；由 T0805 response model 验证 |
| HTTP response | `QueryResponse` | T0805 返回 HTTP 200 与 SPEC Section 6.4 的四字段 response |
| History branch | `List[ChatMessage/dict]` → `str` | message 经 validation、suffix truncation、role prefix formatting；不包含 prompt 标题 |

### 6.3 失败与边界出口

- 空 chunks：context 为 `""`，sources 为 `[]`；这是正常数据状态，不是异常。
- 空 history：`process_history([])` 返回 `""`；这是正常单轮输入，不是异常。
- history 顶层不是 list、message 不是 dict、role 不受支持或 content 不是 str：抛 `AppError("INVALID_HISTORY_FORMAT")`，error catalog 状态为 400。
- 首个 formatted chunk 超过预算：context 为 `""`，不产生半个 chunk。
- 中间某个 chunk 超过预算：已接受的前缀保留，当前及之后项全部停止。
- retrieval 必需键缺失或类型不能比较/计数：原生 `KeyError`/`TypeError` 可能向上传播；未预期异常由全局 handler 映射为 `INTERNAL_ERROR`/500。
- T0803：缺 key → `LLM_NOT_CONFIGURED`/500，401/403 → `LLM_AUTH_FAILED`/500，重试耗尽 → `LLM_UNAVAILABLE`/502，解析或不可重试请求错误 → `LLM_RESPONSE_ERROR`/500；空 answer 当前是正常 `""`。[PROJECT FACT]
- T0804：`get_chunk_count() == 0` → `COLLECTION_EMPTY`/409，且不调用 retrieval/LLM；非空 collection 的空 retrieval results 则继续调用 LLM，返回 sources `[]`。[PROJECT FACT]
- T0804 不负责 question/collection/top_k 的请求校验、HTTP status 或 JSON envelope；T0805 在 API boundary 完成这些责任。[PROJECT FACT]
- T0805：非法 question/collection → `INVALID_QUERY`/400；非法 top_k → `INVALID_TOP_K`/400；非法 history → `INVALID_HISTORY_FORMAT`/400；missing collection → `COLLECTION_NOT_FOUND`/404；下游 `COLLECTION_EMPTY`/LLM/embedding errors 由统一 handler 返回对应 status/envelope。[PROJECT FACT]

### 6.4 Mental Model

把 Phase 8 当前切片记成“**四个准备/适配模块 + 一个编排器 + 一个 API boundary**”：T0801 把 ranked evidence 投影成受预算控制的 context text 和可审计 sources；T0802 把 frontend history 投影成经过校验、保留最近 20 条的 prompt-ready text；T0803 把 policy 与这些已准备文本交给 OpenAI-compatible DeepSeek client；T0804 负责 preflight、retrieval、转换器、LLM 与 result 的顺序组合；T0805 负责 JSON body、collection existence、service delegation、response model 与错误 envelope。context 只保留完整 chunk 的高分前缀，sources 在同一份完整 retrieval results 上映射所有输入项（包括被 context budget 排除的尾部），history 则不是知识事实。T0804 是 service-level integration seam，T0805 是 HTTP adapter；两者都不等于真实 provider/Chroma E2E。[ENGINEERING KNOWLEDGE]

## 7. 架构设计：新增能力与刻意保留的边界

### 7.1 新增能力

- 为 F012 提供稳定的 context string，统一 source label 与 separator。
- 把 `MAX_CONTEXT_CHARS` 从配置注入转换逻辑，形成单一长度边界。
- 为 F015 提供 exact source shape，保留 chunk-level identity。
- 为 F014 提供 history runtime validation、recent-window truncation 和 `User:/Assistant:` formatting。
- 让 context、sources 和 history 成为独立、可测试的转换函数，把 DeepSeek provider I/O、retry 与 response parsing 收敛到 `DeepSeekClient`，再由 T0804 将这些边界组合为 service-level result。[PROJECT FACT]
- 为 QA flow 提供 collection preflight、Hybrid retrieval → context/history → LLM → sources 的同步 orchestration，以及稳定的 `{answer, sources, query, collection_name}` result shape；T0805 再提供 `/api/query` 的 request/response adapter。[PROJECT FACT]

### 7.2 没有改变的边界

- 不触碰 ChromaDB private object，不重新查询 storage。
- 不改变 T0703 的 `final_score`，也不重新排序 retrieval semantics 之外的字段。
- T0801/T0802 不调用 embedding、LLM、文件系统或 HTTP；T0803 仅在 `generate_answer()` 被调用时访问 OpenAI-compatible LLM；T0804 负责 service-level orchestration；T0805 负责 HTTP route、request validation 与 response envelope。[PROJECT FACT]
- 不持久化 history、不实现 session management 或 user isolation；这些是 F014 明确排除的 backend 责任。[PROJECT FACT]
- 不宣称 Phase 8 已完成；T0801–T0805 虽已实现，Phase Gate 和 Phase Learning Review 仍未执行。[PROJECT FACT]

### 7.3 简短 engineering implication

“Context text”“source records”“history text”和“answer text”虽然来自不同分支，但拥有不同的消费者与失败后果：context 受长度限制，sources 需要 identity 完整，history 需要合法 role/content 与最近窗口，answer 还涉及 provider I/O、retry、超时和 response parsing。T0804 通过 preflight 和明确顺序把这些窄边界组合起来，T0805 再把 service result 接到 HTTP；这样 service/route tests 可以在不启动真实网络/API 的情况下验证跨模块 data flow。[ENGINEERING KNOWLEDGE]

## 8. Engineering Review 摘要

当前五个 Task 的完整 ADR、failure taxonomy、规模分析和后续容量决策不放入 Technical Learning。这里仅保留导航结论：context 长度由配置控制；source identity 使用 `chunk_id`；backend 组装 sources；history 在 service boundary 校验后只保留最近 20 条，且不由 backend 持久化；T0803 在 client boundary 统一 DeepSeek 参数、retry 和 error code；T0804 在 service boundary 统一 preflight、retrieval、转换器、LLM 与 result 的顺序；T0805 在 API boundary 统一 request validation、collection existence、service delegation、response model 与 error envelope。Phase 8 Engineering Review 当前尚未建立；这不影响 T0801/T0802/T0803/T0804/T0805 的 Task Learning Pass，也不替代未来独立的 Engineering Review。[PROJECT FACT]

## 9. Technical Decision（技术决策速查）

| 决策 | 备选 | 选择理由 | 代价 |
|---|---|---|---|
| 在函数边界按 score 再排序 | 信任所有调用方已排序 | 转换函数独立可用，输出顺序更可预测 | 每次多一次排序 |
| 超限时 `break` | 跳过当前 chunk，继续寻找更小 chunk | F012 明确要求按排序顺序停止，保证 context 是高分前缀 | 预算可能留下未使用空间 |
| source 按 chunk 投影 | 按 file_name 聚合 | 一个文件的多个 chunk 是不同证据单元，F015 要求 per-chunk records | sources 可能出现同文件多条 |
| backend 生成 sources | 让 LLM 生成或解析引用 | backend 掌握真实 IDs 与 score，结果可审计 | 需要后续 QA response 继续传递该数组 |
| 只返回四个 source 字段 | 附加 `content_preview` | 遵守 v1 F015 exact field set | 前端若要预览需另用 File Preview 能力 |
| history 先校验再截断 | 先截断再校验 | 防止旧消息中的非法结构被窗口策略掩盖；错误 contract 清晰 | 需要遍历全部输入，不能只检查最终 20 条 |
| 按 message 保留最近 20 条 | 按固定轮数或按 token 截断 | 与 F014/T0802 contract 一致，逻辑简单可测 | 可能留下不完整的 user/assistant pair，且不是 token-aware |
| Frontend 维护 history | backend 持久化 session history | 符合 v1 ownership 与隐私/状态边界 | 页面刷新或 KB 切换的清理责任在前端 |
| `DeepSeekClient` 接受 injected client | 在函数内直接 new SDK client | 测试可隔离网络，provider 细节集中在 adapter | 生产接线必须提供正确的 client 或 API key |
| SDK `max_retries=0`，service 自己 retry | SDK retry 与 service retry 叠加 | 总尝试次数、backoff 和错误映射只有一个 owner | service 需要维护异常分类和 sleep 策略 |
| 首次生成时 lazy 读取 API key | 应用启动时强制验证 key | 纯文本/非 LLM 场景仍可启动，遵守 fail-soft 配置契约 | 配置错误延迟到第一次 LLM 调用才暴露 |
| 两条 message：system policy + user data | 把规则和 context 全塞到 user message | 保留 system 优先级，降低检索文档覆盖规则的风险 | T0804 显式传入 `SYSTEM_PROMPT` 和已准备输入，不重复实现 section builder |
| answer 与 sources 分离 | 让 LLM 生成 `[来源: ...]` | source identity/score 可审计，不受模型输出影响 | QA response 必须继续传递 backend-owned sources |
| `get_chunk_count()` preflight | 让空库和空检索结果走同一分支 | 在 retrieval/LLM 前保留 `COLLECTION_EMPTY` 的 409 语义 | 需要一次额外的 public store count 调用 |
| 空库与 relevance-filter-empty 分离 | 所有空结果统一返回空答案 | 空库是存储状态，过滤为空是检索结果状态；后者仍需调用 LLM | T0805 已提供 envelope；no-information 文案仍依赖 System Prompt/provider |
| T0804 直接组装 `HybridRetriever` | 调用 T0703 module-level `retrieve()` | 让 service 的 injected store/retriever seam 清晰，按 T0804 contract 直接控制 orchestration | 目前存在两个 retrieval 入口，未来需要避免行为漂移 |
| 下游异常向上冒泡 | 在 QAService 内统一 catch 成一个错误 | 保留 `INVALID_HISTORY_FORMAT`、`LLM_*` 等 machine-readable code，由全局 API handler 统一映射 | handler 与 response envelope 已由 T0805 接线 |
| T0805 手动解析 `Any` body 后构造 `QueryRequest` | 直接依赖 FastAPI 默认 422 | 保持项目统一 `AppError` code/message/details envelope，并在 storage side effect 前拒绝非法 query | 需要维护一层显式字段校验，与 Pydantic schema 形成 defense in depth |
| collection existence 在 API 先检查 | 让 QAService 统一处理 missing/empty | 404 missing 与 409 empty 是不同业务状态，且 missing 时不创建/调用 service | 多一次 public `list_collections()` 调用 |
| 全局 `AppError` handler | 每个 endpoint 自己 catch 并构造 JSON | 所有 service/API 错误共享同一 response shape 与 status mapping | handler 必须持续覆盖 error catalog |
| `response_model=QueryResponse` | 原样返回任意 service dict | 在 API 出口锁定 SPEC 四字段 response shape | malformed service result 会在 response validation 处失败 |

## 10. Interview Notes（仅候选，不生成完整答案）

1. 你如何证明 T0801 没有把一个 chunk 从中间截断？
2. 为什么 `len(candidate)` 要在 append 前计算？如果先 append，会产生什么回滚复杂度？
3. 同一个 `file_name` 出现三条 source 是 bug 还是契约？`chunk_id` 在这里承担什么 identity 角色？
4. 空 context 与空 knowledge base 是否是一回事？当前 T0801 能区分到哪一层，哪一层还要由 T0804/T0805 处理？
5. T0804 的 4 个 service tests 与 T0805 的 route tests 分别能证明什么？为什么它们仍不能证明真实 DeepSeek answer？
6. T0802 为什么在截断之前校验所有 history？这对 malformed old message 的处理意味着什么？
7. F014 说最近 20 条约 10 轮；T0802 实际保证的是 message count 还是成对 turn？
8. `QueryRequest.history` 已经有 schema，service-level `process_history()` 的第二次校验解决了哪类边界问题？
9. 为什么 `DeepSeekClient` 要注入 client、懒读取 API key，并把 OpenAI SDK 的 `max_retries` 设为 0？
10. timeout、network、429、5xx、400、401/403 分别走哪条错误路径？哪些会触发 backoff？
11. `SYSTEM_PROMPT` 的六原则能由当前 unit tests 证明到什么程度？为什么不能直接宣称 AC-F013-03 通过？
12. 空 context placeholder、empty answer 和 `COLLECTION_EMPTY` 分别由哪个边界决定？
13. 为什么 `/api/query` 要在 `QAService` 前做 collection existence check？
14. `INVALID_QUERY`、`INVALID_TOP_K`、`INVALID_HISTORY_FORMAT`、`COLLECTION_NOT_FOUND` 和 `COLLECTION_EMPTY` 分别由哪个边界产生？
15. `response_model=QueryResponse` 与全局 `AppError` handler 如何共同锁定 API contract？
16. 为什么 T0805 的 `TestClient` tests 是 route-level mocked integration，而不是 literal upload → Chroma → DeepSeek E2E？

## 11. Future Improvement（Future / Not implemented in v1）

| 方向 | 当前边界 | 状态 / owner |
|---|---|---|
| Conversation History | service-level history 校验、最近 20 条截断、`User:/Assistant:` 格式化 | `[PROJECT FACT]`，T0802 DONE |
| Frontend history lifecycle | React state 携带 history、切换 Knowledge Base 时清空 | `[FUTURE]`，frontend / F014 integration |
| DeepSeek client | `SYSTEM_PROMPT`、message assembly、OpenAI-compatible call、timeout/retry、error mapping 已在 service boundary 实现 | `[PROJECT FACT]`，T0803 DONE；真实 provider/E2E 仍 deferred |
| QA orchestration | 已把 collection preflight → Hybrid retrieval → context/history → LLM → sources 串成 service result | `[PROJECT FACT]`，T0804 DONE |
| HTTP API | `POST /api/query`、请求校验、collection existence、response model 与错误码映射已实现 | `[PROJECT FACT]`，T0805 DONE；真实依赖仍 deferred |
| Real integration | 当前没有真实 DeepSeek model/API key 调用、Chroma、upload → answer 或 API E2E；T0804/T0805 tests 使用 Mocked service/route boundaries | `[FUTURE]` / `DEFERRED`，Phase 12 集成验收 |
| Context quality | 当前只做长度边界，不做压缩、摘要、token-aware budget 或 ranking benchmark | `[FUTURE]`，需独立 SPEC/engineering decision |
| Malformed result policy | 必需字段和类型没有专门 validation contract | `[FUTURE]`，由后续 service/API boundary 决定 |
| Prompt assembly / orchestration seam | T0803 实现 F013 section builder；T0804 已把 prepared values 与 `SYSTEM_PROMPT` 传入 `generate_answer()` | `[PROJECT FACT]`，T0803/T0804 DONE |
| API → service history normalization | T0805 将 `QueryRequest.history` 的 `ChatMessage` models 转成 plain dict，再由 T0804/T0802 做 service-level validation | `[PROJECT FACT]`，T0805 DONE；Frontend lifecycle 仍 deferred |
| Empty answer policy | T0803 原样返回 provider 的空字符串，T0804 原样放入 result，T0805 原样通过 `QueryResponse`；不额外生成 no-info fallback | `[PROJECT FACT]`；产品文案仍依赖 System Prompt/provider |

## 自测题与动手练习

### Concept

1. T0801 为什么要同时产出 context text 和 source list？两者的消费者分别是谁？
2. `relevance_score` 与 `final_score` 的关系是什么？T0801 有没有重新计算分数？
3. 为什么 F015 不允许按 `file_name` 去重？

### Code reading / behavior prediction

4. 输入三个 score 为 `0.4、0.9、0.7` 的 chunks，`assemble_context()` 的输出顺序是什么？
5. 如果第一个 chunk 格式化后长度为 4001，`MAX_CONTEXT_CHARS=4000`，返回什么？是否会保留后面的短 chunk？
6. 如果前两个 chunk 已加入，第三个超限，第四个很短，最终 context 包含哪些项？
7. `assemble_sources()` 输入同一 `file_name` 的两个不同 `chunk_id` 时，返回几条 source？
8. 为什么测试中的 `1250 × 3` content chunks 仍可能低于 4000，而再加入 500 字 chunk 会超限？请把 label 和 separator 也算进去。

### Design reasoning

9. 如果产品想“尽量填满预算”，你会直接把 `break` 改成 `continue` 吗？先说明这会不会改变 F012 contract。
10. 如果前端想显示 preview，为什么不能直接给 T0801 的 source dict 加 `content_preview`？应先查哪个 SPEC contract？
11. 空 context 时继续调用 LLM 的行为写在 F012，但为什么当前 T0801 test 不应该断言 LLM 被调用？

### T0802 history processing

12. 顶层 `history` 不是 list 时，`process_history()` 抛出什么？
13. 30 条合法 messages 输入后，哪 20 条进入输出？它们的相对顺序是否改变？
14. 第 1 条（最终被截断掉的旧消息）缺少 `role`，结果仍会成功还是失败？为什么？
15. `role="user"`、`role="assistant"` 如何变成输出前缀？`content=""` 是否被接受？
16. 为什么 `process_history()` 的结果还不能直接称为完整 F013 user message？

### T0803 DeepSeek client

17. `DeepSeekClient.generate_answer()` 为什么需要两条 message，而不是把 `SYSTEM_PROMPT` 拼到 user content？
18. 当 `LLM_MAX_RETRIES=2` 时，最多调用几次 provider？backoff 发生在第几次调用之前？
19. 为什么 401/403 不应 retry，而 429/5xx 应 retry？它们分别映射到哪些 `AppError` code？
20. `OpenAI` client 为什么在第一次生成时才创建？缺 key 时应用启动和第一次调用分别发生什么？
21. 当前 tests 如何证明 message layout 和 error mapping，却不能证明模型真的遵守 grounding 或抗注入规则？
22. T0803 原样返回空 answer 对 T0804 的 no-info policy 有什么影响？

### T0804 QA Service orchestration

23. 为什么 `get_chunk_count() == 0` 必须在 `hybrid_search()` 之前处理？它和 `hybrid_search() == []` 的语义有什么不同？
24. `QAService` 的四个主要步骤是什么？哪一步把 `SYSTEM_PROMPT` 传给 T0803，哪一步生成 sources？
25. 如果 history 的第一个 message 非法但检索结果已经得到，当前 control flow 会调用 LLM 吗？为什么？
26. 为什么 QAService 测试可以注入 fake store/retriever/LLM，却不能证明 upload → ChromaDB → DeepSeek → HTTP E2E？
27. 当前 T0804 为什么没有调用 T0703 的 `retrieve()` facade？如果未来要统一入口，应该先检查哪些 contract 和测试？

### T0805 HTTP endpoint

28. `_parse_query_request()` 为什么先接收 `Any` body，再构造 `QueryRequest`？直接使用 FastAPI 默认 422 会改变什么？
29. `top_k=True` 为什么必须拒绝，即使 Python 中 `bool` 是 `int` 的子类？
30. 为什么 missing collection 要在 T0804 `get_chunk_count()` 之前返回 404？
31. `QueryResponse.model_validate(result)` 能保证哪些字段，不能保证 answer 的哪些语义？
32. `AppError` handler 如何把 `COLLECTION_EMPTY`、`LLM_UNAVAILABLE` 和 `INVALID_TOP_K` 映射成不同的 status/envelope？
33. 10 个 `QueryEndpointTests` 为什么只证明 route-level mocked integration？还缺哪些真实依赖？

### 小型动手练习（不改产品代码）

在 Python REPL 中构造三条 retrieval dict，先手算 formatted length，再执行：

```python
from app.services.qa import assemble_context, assemble_sources, process_history

chunks = [
    {"file_id": "f1", "file_name": "a.md", "chunk_id": "c1", "content": "A", "final_score": 0.6},
    {"file_id": "f1", "file_name": "a.md", "chunk_id": "c2", "content": "B", "final_score": 0.9},
    {"file_id": "f2", "file_name": "b.md", "chunk_id": "c3", "content": "C", "final_score": 0.7},
]

print(assemble_context(chunks))
print(assemble_sources(chunks))

history = [
    {"role": "user", "content": "什么是 Python？"},
    {"role": "assistant", "content": "一种编程语言。"},
    {"role": "user", "content": "它的优点是什么？"},
]
print(process_history(history))
```

然后把某一项的 `content` 换成超过 `settings.MAX_CONTEXT_CHARS` 的字符串，预测 `break` 的位置；再确认 sources 仍逐 chunk 保留，且没有 `content_preview`。另把 history 增加到 21 条，观察只保留最新 20 条；将旧消息删掉 `role`，确认即使它最终会被截断仍会抛 `INVALID_HISTORY_FORMAT`。

继续在 Python REPL 中只调用本地纯函数，不触发网络：

```python
from app.services.qa import DeepSeekClient

print(DeepSeekClient._build_user_message("", "", "什么是 Python？"))
print(DeepSeekClient._build_user_message("User: 之前的问题", "[来源: notes.md]\nPython", "它是什么？"))
print(DeepSeekClient._is_retryable_error(TimeoutError(), None))
print(DeepSeekClient._is_retryable_error(Exception(), 400))
```

预测两次 user message 的 section 差异、`TimeoutError`/400 的布尔结果，并说明为什么这些调用仍不能验证真实 DeepSeek answer。[PROJECT FACT]

再构造三个 `Mock` dependency 注入 `QAService`（不要创建真实 Chroma 或 OpenAI client），分别让 `get_chunk_count()` 返回 `0`、让 `hybrid_search()` 返回 `[]`、让它返回两个有分数的 chunks；预测三种情况下的异常、LLM 参数和 sources，再运行 `QAServiceTests` 对照。[PROJECT FACT]

最后使用 `TestClient`（仍 patch `app.api.query.ChromaVectorStore` 与 `app.api.query.QAService`）构造四个请求：合法 query、`top_k=0`、missing collection、`history` 含 `role="system"`。先预测 HTTP status、error code、service 是否被调用，再运行 `QueryEndpointTests` 对照；这个练习不触发真实 Chroma、embedding 或 DeepSeek 网络。[PROJECT FACT]

## Quick Review

```text
Phase 8 current mental model
  Input       POST /api/query JSON → T0805 validation → T0804 input
  Context     sort DESC → format label/content → candidate length check
  Boundary    MAX_CONTEXT_CHARS; oversized chunk causes break
  Output      context string; empty input/overflow-first => ""
  Sources     sort DESC → exact {file_id, file_name, chunk_id, relevance_score}
  Identity    chunk_id; same file may appear multiple times
  Ownership   backend assembles sources; LLM does not generate them
  History     validate role/content → keep latest 20 → `User:/Assistant:` lines
  LLM         T0803 system policy + user sections → DeepSeek call → bounded retry → answer
  Orchestrator T0804 preflight → hybrid → converters → LLM → sources → result dict
  API         T0805 existence check → QAService delegation → QueryResponse/error envelope
  Verified    5 T0801 + 4 T0802 + 12 T0803 + 4 T0804 + 10 T0805 test methods inside 60-test suite; compileall PASS
  Deferred    real provider/API E2E, Chroma/upload integration, frontend integration, semantic quality
```

> **T0801 Learning Pass 记录（2026-09-02）**：本章记录 context/source 两条无外部 I/O 转换路径、完整 chunk budget、chunk-level source identity。
>
> **T0802 Learning Pass 记录（2026-09-02）**：本章增量记录 history 的 runtime validation、最近 20 条 suffix window、`User:/Assistant:` formatting 与 34/34 unit verification。**在该 T0802 checkpoint 当时**，T0803–T0805、Phase 8 Gate Review 与 Phase Learning Review 尚未执行；当前 T0803 已由下方增量记录，本 Task 的学习文档不能替代独立的 Phase Review。
>
> **T0803 Learning Pass 记录（2026-09-02）**：本章增量记录 `SYSTEM_PROMPT` 六原则、OpenAI-compatible DeepSeek adapter、两条 message assembly、lazy key/config、bounded retry、错误映射与 response extraction。**在该 T0803 checkpoint 当时**，当前 46/46 tests PASS；真实 DeepSeek API、QA orchestration、`/api/query`、Phase 8 Gate Review 与 Phase Learning Review 尚未执行。T0804 已在下方增量接入 service orchestration。
>
> **T0804 Learning Pass 记录（2026-09-02）**：**在该 T0804 checkpoint**，本章增量记录 QAService 的 dependency injection/lazy creation、collection preflight、空库与空检索结果分叉、context/history/LLM/sources 顺序、service result shape 与 4 个 Mocked orchestration tests；当时 50/50 tests PASS，`/api/query` 尚未执行。真实 provider/Chroma/upload E2E、Phase 8 Gate Review 与 Phase Learning Review 仍未执行。
>
> **T0805 Learning Pass 记录（2026-09-02）**：本章增量记录 POST `/api/query` 的手动 body/request validation、collection existence check、T0804 service delegation、`QueryResponse` response model、全局 `AppError` envelope 与 10 个 route-level Mocked tests。当前完整 suite 为 60/60 PASS；真实 provider/Chroma/upload → query E2E、Frontend history lifecycle、Phase 8 Gate Review 与 Phase Learning Review 仍未执行。
