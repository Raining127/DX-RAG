# Phase 6 — Keyword Retrieval Engineering Review

> **Coverage**: T0601 + T0602
> **Status**: COMPLETE（2026-08-27）— T0601/T0602 实现、PHASE_6_PASS Gate 与 Phase Learning Review 均已完成

## 1. 当前工程结论

T0601 把分词做成 pure function；T0602 在其上实现 per-collection in-memory inverted index、lazy build、dirty/full rebuild 与 binary token coverage score。13 个 test methods 全部通过，F009 的 unit-level 行为闭环已形成；真实 upload-to-query E2E 仍待 Phase 12。

## 2. 为什么需要这个模块

Vector retrieval 解决 semantic similarity，keyword retrieval 补精确术语、型号、缩写和错误码；Phase 7 的 T0702 已按 `chunk_id` 将两者融合。Phase 6 先以共享 tokenizer 保证 indexing/query normalization 一致，再以 inverted index 将查询成本从扫描所有 chunk 转为访问相关 posting sets。

## 3. 核心设计决策

### ADR-01: v1 中文采用 overlapping character bigram

- **Decision**: 连续中文段用宽度 2、步长 1 的滑动窗口。
- **Context**: SPEC F009 明确排除 jieba、BM25 与 TF-IDF。
- **Why**: 零第三方依赖、无词典生命周期、O(n)、对未登录词与技术名词具有边界鲁棒性。
- **Trade-off**: token 数量与索引体积增大；匹配只代表字符片段重合，不代表理解语义。
- **Future**: 若召回质量或索引规模成为实测瓶颈，再以评测集驱动替换，不提前优化。

### ADR-02: 英文与中文使用两个互斥正则通道

- **Decision**: 英文/数字与连续中文段分别提取。
- **Why**: 规则直接对应 SPEC，标点自然成为边界，不需要先修改原字符串。
- **Trade-off**: 输出按通道分组，不保持跨语言原文顺序；中文范围不覆盖所有 Unicode 扩展区。
- **Assessment**: T0602 按集合语义消费 query tokens，matched counter 不把 token 顺序当相关性信号。

### ADR-03: 稳定去重采用 dict.fromkeys

- **Decision**: 过滤后以 insertion-ordered dict 去重。
- **Why**: keyword_score 的分母要求 unique tokens；稳定结果使测试与诊断可重复。
- **Trade-off**: 建立临时 dict，但复杂度仍为 O(n)，对 query 长度可忽略。

### ADR-04: tokenizer 保持纯函数

- **Decision**: 不把索引、cache、VectorStore 或配置注入 T0601。
- **Why**: document/query 两侧能复用同一规则；测试无需 fixture 或 mock；Task 边界清晰。
- **Trade-off**: KeywordRetriever 必须单独管理索引生命周期，不能从 tokenize() 获得状态。

### ADR-05: exact examples + boundary tests 共同冻结契约

- **Decision**: 除 SPEC exact examples 外，补测 alphanumeric lowercase、单字符、中文 segment boundary 与 stable dedup。
- **Context**: happy-path examples 证明主规则，但不能证明标点是否跨界、重复 token 的顺序或数字是否保留。
- **Why**: 这些边界会直接改变未来 inverted-index keys 与 score denominator。
- **Trade-off**: 当前测试仍不是 Unicode 全域或 property-based test；覆盖范围应诚实限定为已列场景。
- **Future**: 出现真实语料缺口后，再增加对应 regression case。

### ADR-06: class-level shared cache + instance-level VectorStore

- **Decision**: _indexes/_chunks/_dirty_collections 定义为 class attributes；vector_store 由 constructor 注入到 instance。
- **Context**: keyword_index.py 的 standalone seam 只有 collection_name，没有 retriever instance。
- **Why**: classmethod invalidate() 能从任意 mutation caller 标记全进程共享 cache；build 仍可通过 injected VectorStore 测试。
- **Trade-off**: cache namespace 只有 collection name。若同一进程存在多个独立 VectorStore namespace 且 collection 同名，会共享错误 snapshot。
- **Future**: 多 tenant/store 场景将 store identity 纳入 key，或改为 application-owned singleton service。

### ADR-07: 双表 snapshot，不在 posting 中复制 ChunkRecord

- **Decision**: _indexes 保存 token → chunk_id set，_chunks 保存 chunk_id → ChunkRecord。
- **Why**: posting set 保持轻量；返回阶段按 chunk_id 做 in-memory join，避免每个 token 重复保存 content/metadata。
- **Trade-off**: 两张表必须来自同一次 build；当前是依次发布而非并发原子替换，否则可能出现 dangling id 或跨版本观察。
- **Mitigation**: 当前实现先在 local dict 完整构建，再依次替换 shared state；这能避免单线程异常时发布 half-built snapshot，但不提供无锁并发下的 atomic publication。

### ADR-08: lazy build + dirty flag + query-time full rebuild

- **Decision**: cold/dirty cache 在下一次 keyword_search 前 full rebuild；mutation path 只 add dirty flag。
- **Why**: 符合 SPEC v1 明确的“无增量更新”；没有查询的 collection 不付 build 成本；upload/rename/delete 保持轻量。
- **Trade-off**: mutation 后第一个 query 承担全量重建 latency；旧 snapshot 在此之前仍占内存。
- **Future**: 只有真实规模证明 full rebuild 不可接受时才评估 incremental index。

### ADR-09: binary unique-token coverage score

- **Decision**: matched unique query tokens / total unique query tokens。
- **Why**: 直接兑现 SPEC，天然归一化到 [0,1]，可供 Phase 7 与 vector score 融合。
- **Trade-off**: 不看 term frequency、inverse document frequency 或 token rarity；常见 token 与稀有 token 等权。

### ADR-10: local build 后发布，失败不清 dirty

- **Decision**: _build_index 先构建 local inverted_index/chunks；成功后才写 class cache 并 discard dirty。
- **Why**: list_chunks/tokenize 失败时不发布 half-built snapshot，下次查询仍可重试 rebuild。
- **Trade-off**: rebuild 峰值期间旧/新 snapshot 可能同时占内存；当前无并发 synchronization。

## 4. 架构影响

- **新增契约**: str → ordered unique tokens；以及 collection/query/top_k → ranked keyword results。
- **依赖方向**: KeywordRetriever 依赖 tokenize() 与 VectorStore public list_chunks()；tokenize() 不反向依赖 index/cache。
- **共享规则**: chunk content 与 query 必须复用同一函数，避免 indexing/query drift。
- **隔离性**: index 只在内存中，不引入新 dependency 或持久化格式。
- **seam 兑现**: [keyword_index.py:4](../../../backend/app/services/keyword_index.py#L4) 已从 documented no-op 变为调用 KeywordRetriever.invalidate()；既有 upload/rename/delete callers 无需改变调用形状。
- **下游边界**: T0702 `HybridRetriever` 已消费 T0602 的 keyword result；T0703 `retrieve()` facade 已把三层 retriever 组装到同一个入口；QA API 尚未实现。

## 5. 工程问题分析

### 5.1 可维护性

tokenizer 规则集中，KeywordRetriever 的 build/search 生命周期也保持在一个 class。当前 qa.py 模块 docstring 仍只写 Query tokenization，test_qa.py docstring 仍只写 T0601，已经落后于文件职责；这是文档级维护债。若 Phase 7/8 继续塞入同文件，应按真实职责拆分，而不是继续扩大 qa.py。

### 5.2 扩展性

tokenizer 替换会改变 index keys、查询结果与 score，必须重建全部 index。class-level cache 让单进程内所有 instances 共享，但不支持跨进程一致 invalidation；多 worker 部署时每个进程持有独立 cache，mutation 只会标脏处理该请求的进程。

### 5.3 数据一致性

local-build-then-publish 避免单线程异常路径暴露 half-built snapshot；dirty 只在成功发布后清除。但 class dict/set 没有 lock，并发 search 与 invalidate/build 的 interleaving 未测试；多进程 cache 也彼此不可见。

### 5.4 错误处理

空 query tokens 返回 []；missing token 用 empty set 静默跳过。list_chunks/build 的异常向上传播且 dirty 保留。top_k 没有在 class 内校验：0 返回 []，负数遵循 Python slice 语义；合法 top_k 应由未来调用边界保证。

### 5.5 性能

build 对 corpus 总字符量近似 O(C)，search posting lookup 约 O(q + P)，对 m 个 matched chunks 排序 O(m log m)。full rebuild 会在首个 cold/dirty query 上集中发生。当前没有 benchmark，不能声称具体 latency。

### 5.6 安全

tokenizer 不执行输入、不访问路径、不调用网络；index content 来自 VectorStore public records。超长 query/corpus 会消耗 CPU/内存；请求长度与 top_k validation 属于未来 API boundary。

## 6. 规模扩大分析

| 规模 | 当前判断 | [FUTURE] 真正压力点 |
|------|------------|----------------------|
| 10x query length | O(n) 线性增长，通常可接受 | API 是否需要 question length limit |
| 100x corpus | full rebuild latency 与双 snapshot 峰值上升 | corpus benchmark、background rebuild |
| 1000x corpus | 单进程 memory index 可能不再合适 | 增量/持久化/分布式 index；均非 v1 |

这里不虚构 benchmark。bigram 会比词典分词生成更多 keys 是一般性质，但本仓库尚无 corpus-level measurement。

## 7. Verification Review

2026-08-27 执行 python -m unittest tests.test_qa -v：13/13 test methods PASS，其中 tokenizer 6 个、retriever 7 个。新增覆盖：

- lazy list_chunks build + AC-F009-01 1.0
- AC-F009-02 empty result
- AC-F009-03 partial score 0.6
- AC-F009-04 mixed-language 1.0
- score DESC + top_k
- dirty → next search full rebuild
- absent index invalidation no-op

AC-F009-01~04 的 unit-level behavior 已覆盖。AC-F009-05 的核心 lifecycle 已覆盖，但测试直接调用 invalidation seam 并更新 Mock list_chunks source，没有经过真实 upload HTTP workflow；literal E2E DEFERRED TO PHASE 12。

## 8. Known Gaps & Pending Questions

1. literal upload/rename/delete → invalidate → real Chroma rebuild → query E2E 未覆盖。
2. class-level cache 仅以 collection name 为 namespace；多 VectorStore/tenant 同名 collection 可能碰撞。
3. 多进程 worker 的 in-memory cache 与 dirty flag 不共享；当前本地单进程假设下可用。
4. shared dict/set 无 concurrency lock；并发 build/invalidate 未测试。
5. equal-score tie-breaker 未定义；set iteration 可能影响同分结果顺序。
6. qa.py 与 test_qa.py module docstring 仍只描述 T0601 tokenization，已落后于实际职责。
7. 当前中文 regex 仅覆盖基本 CJK 区；没有 corpus benchmark、property-based test 或 Unicode 全域测试。
8. Phase 4 ER Pending #34（invalidate 失败 → RENAME_FAILED 映射是否成立）于 T0602 落地后可裁决：`invalidate()` 是 in-memory 标脏（`set.add`），当前实现没有失败路径——契约第四要素（真失败 raise）保持为防御性条款；RENAME_FAILED 映射在 in-memory 实现下不可达，但与调用方补偿逻辑无冲突。

## 9. Cross-links

- 代码学习与自测：[phase-06-keyword-retrieval.md](../phase-06-keyword-retrieval.md)
- Python / TS 语法映射：[python-for-frontend-dev.md](../python-for-frontend-dev.md)
- 项目级面试资产：[dx-rag-interview-guide.md](../interview-notes/dx-rag-interview-guide.md)（Phase Learning Review 已将 T0601/T0602 candidates 筛选、去重并晋升到 Phase 6 深度章）

> **T0602 review boundary**: 本评审覆盖 Phase 6 implementation；不启动 Phase 7，不把 unit tests 写成 E2E PASS。

> **后续状态（T0701 Learning Pass，2026-08-28）**：上面的“不启动 Phase 7”是 2026-08-27 Phase 6 review checkpoint。之后 T0701 已实现 `VectorRetriever`，把 query embedding 接到 `VectorStore.search()` 并透传 `vector_score`；详见 [Phase 7 Technical Learning](../phase-07-vector-retrieval.md) 与 [Phase 7 Engineering Review](./phase-07-engineering-review.md)。
>
> **后续状态（T0702 Learning Pass，2026-08-31）**：T0702 已在 `qa.py` 中按 `chunk_id` 完成 0.3/0.7 weighted fusion、relevance filter 与最终 Top-K，并以 unit tests 验证 service-level behavior。当时 T0703 unified wiring、真实 upload → ChromaDB → query E2E 与 QA API 仍未实现；本 Phase 6 review 的历史 Gate 结论不因此被改写。
>
> **后续状态（T0703 Learning Pass，2026-08-31）**：T0703 已在 `qa.py` 提供 `retrieve(query, collection, top_k)` facade。它在边界处创建 concrete `ChromaVectorStore`，对空 collection 返回 `[]`，非空时把同一 store 注入 Keyword/Vector/Hybrid retrievers；missing collection 的异常不被吞掉。3 个 facade tests 验证的是 patched composition/propagation boundary，而非真实 Chroma lifecycle 或 upload → query E2E。Phase 6 的 Gate/Learning Review 历史结论保持不变；QA API、context/LLM 与真实集成仍待后续 Phase。

## 10. Phase 6 Gate Review（2026-08-27）

### 10.1 Verdict

**PHASE_6_PASS**。T0601/T0602 的实现与冻结 SPEC F009 一致，没有发现阻断 Phase 6 收口的问题；允许进入 Phase Learning Review，但本次不启动 Phase 7。

### 10.2 Gate evidence

| Gate item | Result | Evidence |
|---|---|---|
| T0601 exact tokenizer contract | PASS | SPEC 三组示例、lowercase、单字符过滤、segment boundary、stable dedup 均由 `TokenizeTests` 覆盖 |
| T0602 public-interface index build | PASS | `KeywordRetriever._build_index()` 只调用 `VectorStore.list_chunks()`，未访问 Chroma private object |
| Lazy build + dirty/full rebuild | PASS | 首次查询只构建一次；shared invalidation seam 标脏；下一次查询重新读取全量 chunks |
| Score / sort / top-k | PASS | AC-F009-01=1.0、AC-F009-02=[]、AC-F009-03=0.6、AC-F009-04=1.0，降序与 top-k 有独立测试 |
| Mutation integration seam | PASS（代码路径 + unit lifecycle） | upload、rename、delete 的既有调用点均进入 `invalidate_keyword_index()`；真实 HTTP/Chroma E2E 仍按计划留给 Phase 12/T1202 |
| Focused test | PASS | `python -m unittest tests.test_qa -v` → 13/13 |
| Discovered regression suite | PASS | `python -m unittest discover -s tests -v` → 13/13（当前仓库 tests 仅此 suite） |
| Syntax/import compilation | PASS | `python -m compileall -q app tests` |
| Diff hygiene | PASS | `git diff --check` 无 whitespace error；未修改冻结的 `docs/SPEC.md`，未引入 dependency 或 Phase 7 代码 |

> **记录澄清（Learning Pass 补记，2026-08-27）**：上表 Diff hygiene 行的「未修改 `docs/SPEC.md`」指 T0601/T0602 的实现 diff。当日另有一次独立提交 `33e0bdb`（15:05，Gate Review 之前）修正了冻结 SPEC F009「Python机器学习」示例的笔误（6 tokens → 4 tokens，与 TASKS.md 同步）——属示例勘误，不是实现改动；Gate 的 `git diff --check` 针对实现工作树，结论不受影响。

`black` 与 `ruff` 不在当前环境/requirements 中，因此对应检查记为 **NOT AVAILABLE**，不作为 Gate failure；本次没有为审查新增依赖。

### 10.3 Acceptance decision

- **AC-F009-01 — PASS**：中文 bigram 全命中，score = 1.0。
- **AC-F009-02 — PASS**：无 token 命中返回空列表。
- **AC-F009-03 — PASS**：3/5 unique query tokens 命中，score = 0.6。
- **AC-F009-04 — PASS**：中英混合 query 的 `python` / `编程` 均命中，score = 1.0。
- **AC-F009-05 — PASS（Phase 6 scope）**：已建索引经 shared seam 标脏后，下一次 search 全量重建并检索到新增 chunk。真实 upload HTTP → ChromaDB → query 的字面 E2E 未宣称通过，继续归 Phase 12/T1202。

### 10.4 Non-blocking findings

第 8 节的多进程 invalidation、并发锁、同分 tie-break、基本 CJK 范围、benchmark 与 module docstring 债务均不违反 v1 F009 或当前 Task Completion Conditions，维持 Known Gaps / Future 状态。Gate 不把这些改写成已实现能力，也不以“顺手优化”扩大 Phase 6 scope。
