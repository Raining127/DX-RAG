# Phase 9 — File Management API Engineering Review

> **Coverage**：T0901 `GET /api/files`、T0902 `GET /api/files/{file_id}/preview`、T0903 `DELETE /api/files/{file_id}`
>
> **Status**：COMPLETE（2026-09-04）。本文件是 Layer 2 Engineering Review；不重发 Phase Gate verdict，不替代 Technical Learning、Phase Learning Review 或真实集成验收。
>
> **Evidence vocabulary**：`STATIC/CODE-LEVEL` 表示源码或契约检查；`UNIT` 表示隔离依赖的行为测试；`MOCKED` 表示 route 使用真实 FastAPI boundary、但 storage/filesystem/index seam 被 patch；`SUBSTITUTED` 表示使用 concrete components、但以手工 persisted chunks 替代 literal ingestion；`DEFERRED` 表示后续验收范围；`NOT_AVAILABLE` 表示本轮没有相应证据。

## 1. 当前工程结论

Phase 9 把 ingest 后分散在 ChromaDB metadata、persisted chunk content、raw uploads 和 keyword cache 中的文件状态，暴露为三个管理动作：文件级 projection、诊断性 preview 和不可逆 cleanup command。三个动作共享 `(collection_name, file_id)` identity，却刻意使用不同 source of truth：

- list 从所有 chunk metadata 聚合 file records；
- preview 从该 `file_id` 的 persisted chunks 重建已入库文本；
- delete 先用 file-level metadata 将 immutable `file_id` 解析为 server-owned `file_name`，再依序清理 raw file、Chroma data 和 keyword cache lifecycle。

当前实现与 SPEC F016、TASKS T0901–T0903 的 observable contract 一致，本轮未发现阻断文档收口的实现缺陷。最重要的工程边界是：delete 跨 filesystem、ChromaDB 和 process-local keyword index，却没有共享 transaction、durable operation log 或 compensation；因此“成功时三处都清理”已经定义，“中途失败后如何恢复”尚未定义为可靠系统能力。

可准确对外表述为：**Phase 9 的 list/preview/delete contract 已实现并通过独立 Gate；当前 route tests 证明 mocked orchestration，Gate 留存一条从手工 persisted chunks 起步的 SUBSTITUTED smoke；literal upload → ingest → list → preview → delete → re-upload 以及 partial-failure recovery 仍为 DEFERRED。**

## 2. 为什么需要这个模块

上传成功只建立文件生命周期的前半段。没有 Phase 9，用户无法回答三类运营问题：

1. 当前知识库实际包含哪些成功入库的文件？
2. 检索系统实际保存了什么文本，而不是原始文件看起来是什么？
3. 删除一个逻辑文件时，怎样让 raw、vector/metadata 和 derived keyword state 一起退出可见集合？

```text
Upload / Ingest
    │
    ├── raw file: uploads/{collection}/{file_name}
    ├── durable chunks: ChromaDB metadata + document + vector
    └── derived state: in-memory keyword index
             │
             ▼
Phase 9 management boundary
    ├── list    → metadata projection grouped by file_id
    ├── preview → ordered persisted chunks → diagnostic text
    └── delete  → identity lookup → raw → Chroma → index invalidation
```

这个模块的价值不是重新拥有存储逻辑，而是给跨边界状态一个可审计的 HTTP contract，并明确每一步由谁拥有。

## 3. 核心设计决策（ADR）

### ADR-01：`file_id` 是资源身份，`file_name` 只用于展示和 server-side path resolution

- **Decision**：preview/delete path 使用 `file_id`；delete 只在 server 从 persisted file record 取出 `file_name` 后触碰磁盘。
- **Context / Problem**：文件名可变、可能重复于不同知识库，也包含路径注入风险；客户端提供的显示字段不能成为 destructive selector。
- **Why**：UUID identity 与 ingest 时所有 chunks 的 metadata 一致，能精确限定 Chroma filter；路径材料不由请求直接控制。
- **Trade-off**：delete 为取得 `file_name` 需要先构造 file-level view；metadata 损坏时无法安全定位 raw file。
- **Future**：若引入独立 metadata store，仍应保持 `file_id` 为 public identity，并定义迁移与 reconciliation 规则。

### ADR-02：文件列表从 chunk metadata 派生，不引入元数据库

- **Decision**：`get_files()` 读取 collection 全部 metadata，按 `file_id` 去重并累计 `chunk_count`；第一条 chunk 提供 `file_name/size/upload_time/status`。
- **Context / Problem**：v1 需要文件视图，但不希望新增双写 database 和同步协议。
- **Why**：Chroma metadata 已是 ingest 后 durable source，派生 projection 避免第二份权威状态。
- **Trade-off**：每次 list 都是 collection-wide metadata scan；实现假设同一 `file_id` 的 denormalized fields 一致，且没有显式排序/pagination。
- **Future**：只有 benchmark 或产品查询需求证明必要时，才引入 file-level index/metadata store；届时必须定义 dual-write、repair 和 source-of-truth ownership。

### ADR-03：Preview 展示 persisted ingestion truth，而不是原文件 rendering

- **Decision**：读取该文件所有 persisted chunks，按 `chunk_index` 升序，以 `\n\n` 拼接，计算完整 `total_chars` 后截断到 `MAX_PREVIEW_CHARS=5000`。
- **Context / Problem**：原文件重解析会重新触发 parser/OCR 依赖，并可能与真正被检索的文本不同。
- **Why**：诊断目标是解释“系统吃进去了什么”；chunk overlap、heading prefix 等 artifact 是诚实的 ingestion output。
- **Trade-off**：不是原文件精确还原；为返回 `total_chars` 必须读取和拼接完整内容，即使响应只返回 5000 字符。
- **Future**：若需要文档 viewer，应建立独立 raw-rendering contract，不能悄悄改变 F016 preview 语义。

### ADR-04：Read paths 区分 empty collection、missing collection 与 missing file

- **Decision**：存在但无文件返回 `200 files=[]`；collection 不存在返回 404 `COLLECTION_NOT_FOUND`；preview/delete 中 file identity 不存在返回 404 `FILE_NOT_FOUND`。
- **Why**：空集合是正常 state，missing resource 是错误；稳定区分可让前端给出准确 recovery action。
- **Trade-off**：每个 route 都先调用 `list_collections()`，随后再执行实际读取；两次操作不在 snapshot 中，存在 check/use race。
- **Future**：若 storage adapter 提供 typed not-found exception，可减少显式 preflight round trip，但必须保持当前 HTTP 语义。

### ADR-05：Delete 顺序固定为 raw file → Chroma file data → keyword invalidation

- **Decision**：所有 no-side-effect preflight 完成后，按 SPEC 顺序执行磁盘 unlink、`delete_by_file()`、`invalidate_keyword_index()`。
- **Context / Problem**：三个 target 没有共享 transaction；顺序本身决定失败后的 residual state。
- **Why**：遵循冻结 contract；`missing_ok=True` 允许 raw file 已缺失时继续清理 durable chunks；Chroma 删除后再使 derived index 失效。
- **Trade-off**：Chroma 失败时 raw 已删除但 chunks 仍可检索；进程在 Chroma 成功后、invalidation 前崩溃时旧 keyword snapshot 可能暂时可见。操作不可逆且当前没有 compensation。
- **Future**：需要以 failure matrix 决定 tombstone、operation journal、retry/reconciliation 或改变顺序；这属于新 engineering decision，不能在 review 中擅改 SPEC。

### ADR-06：Raw path helper 使用 basename、resolve 与 direct-parent invariant

- **Decision**：`PureWindowsPath(file_name).name == file_name`，collection directory 必须是 upload root 的直接子目录，target 必须是 collection directory 的直接子文件；否则拒绝删除。
- **Why**：组合检查覆盖 Windows separator、`..`、absolute path 与 resolve 后逃逸；server-owned filename 再叠加 runtime guard，形成 defense in depth。
- **Trade-off**：这是 code-level protection，不是完整 filesystem security proof；check 与 unlink 之间仍有 TOCTOU，symlink/junction/权限行为依赖 OS。
- **Future**：补充 Windows/POSIX separator、absolute path、nested traversal、symlink/junction 与 race-aware test matrix。

### ADR-07：Chroma delete 用相同 `file_id` filter 先计数、后删除

- **Decision**：`col.get(where={"file_id": file_id}, include=[])` 计算数量，非零时再 `col.delete(where=...)`，返回删除前 count。
- **Why**：同一 predicate 同时覆盖 documents、vectors 和 metadata，且为调用方提供 observable deleted count。
- **Trade-off**：get/delete 不是 atomic compare-and-delete；并发 mutation 时返回 count 与实际删除范围可能漂移，route 当前也不校验“预期 chunk_count == deleted count”。
- **Future**：并发需求出现时，评估 storage-level atomic primitive、version/tombstone 或 post-delete verification。

### ADR-08：Keyword index 是 derived cache，invalidation failure 不回滚 durable delete

- **Decision**：durable Chroma state 是 source of truth；normal invalidation 异常时 seam 尝试 `mark_dirty()` 并记录日志，不把 durable operation 改写成失败。
- **Why**：cache maintenance 不应反向否定已完成的 irreversible durable mutation；下一次 search 可 full rebuild。
- **Trade-off**：`mark_dirty()` 自身若失败仍可能传播；multi-process worker 的 cache coherence 未解决，日志也没有 operation correlation id。
- **Future**：为多 worker 引入 durable invalidation event/version，并验证 crash recovery 与 stale-read window。

### ADR-09：HTTP responses 使用 Pydantic DTO，不暴露 raw storage records

- **Decision**：list 的每条记录经 `FileItem.model_validate()`；preview/delete 返回各自 response model。
- **Why**：storage dict 不是 public API，DTO 固定字段和类型，防止内部 metadata 无意泄露。
- **Trade-off**：schema 验证只证明 shape；不能证明 timestamp/status 的业务语义或同文件 metadata 一致性。
- **Future**：若状态演进为 enum 或新增 pagination，应先修改冻结 contract，再升级 schema 和 client。

### ADR-10：v1 明确不做 batch、undo、move/rename 与 reconstruction cleanup

- **Decision**：保持三个单文件 management operations；delete 不提供 trash/undo；preview 不做 de-overlap、heading cleanup、OCR 或模型调用。
- **Why**：这些能力会引入新的 identity、lifecycle、retention、authorization 和 recovery contracts，不是当前 endpoint 的“小优化”。
- **Trade-off**：用户误删无法恢复，大文件管理效率有限，preview 会显式保留 ingestion artifacts。
- **Future**：若产品要求恢复能力，优先设计 soft-delete/tombstone 与 retention policy，而不是在当前 irreversible API 外包一层 UI confirmation 就宣称可恢复。

## 4. 架构影响

### 4.1 Ownership 与依赖方向

```text
FastAPI files routes
    ├── response DTO / AppError catalog
    ├── VectorStore public interface
    │      └── ChromaVectorStore
    ├── pathlib filesystem boundary
    └── keyword invalidation seam
```

- API layer：resource preflight、HTTP mapping、跨 target ordering、response projection。
- VectorStore：file metadata aggregation、chunk lookup、file-scoped Chroma deletion。
- Filesystem helper：只负责验证并删除一个 server-resolved raw target。
- Keyword subsystem：只负责 derived cache lifecycle，不拥有 durable content。

### 4.2 新增与稳定的契约

| Contract | Stable input | Stable output / side effect |
|---|---|---|
| File list | `collection_name` | file-level records 或明确 missing collection |
| Preview | `(collection_name, file_id)` | persisted-text diagnostic view，最多 5000 chars |
| Delete | `(collection_name, file_id)` | raw + Chroma + keyword lifecycle cascade |
| Storage projection | collection | grouped file records，不引入第二数据库 |
| Storage delete | collection + file_id | 删除匹配 Chroma records，返回 count |

### 4.3 没有改变的边界

Phase 9 不改变 upload validation、parser/OCR、chunking、embedding、retrieval score、collection rename/delete 或 frontend behavior。它也没有引入 authentication、authorization、audit log、trash、batch operation 或 distributed transaction。

## 5. 工程问题分析

### 5.1 可维护性

Route 很薄，storage primitives 通过 ABC 暴露，这是清晰的 separation of concerns。重复的 collection preflight 和每次新建 `ChromaVectorStore()` 当前规模可接受，但随着 endpoints 增长，可能形成 error/order drift；若抽取 helper，必须保留具体 error code 与 no-side-effect ordering，不能只为减少行数而隐藏语义。

`get_files()` 以 untyped dict 作为 storage-to-API seam，API 再用 Pydantic 校验。这能保护 HTTP 出口，却让内部 caller 仍依赖字符串 keys。若 file record 被更多 service 消费，可考虑 typed domain model；当前无需为了“类型更漂亮”扩大范围。

### 5.2 一致性与数据语义

1. 同一 `file_id` 的 metadata 被假定一致；`get_files()` 采用 first-chunk-wins，没有检测冲突字段。
2. Preview storage method 和 route 都排序，形成 defense in depth，也带来小幅重复成本。
3. `FILE_NOT_FOUND` 表示没有 persisted chunks/file record，不表示 raw uploads 目录中绝对没有孤儿文件。
4. Delete lookup 与 delete predicate 都使用同一 `file_id`，但中间没有 snapshot；并发上传/删除可能产生 time-of-check/time-of-use drift。
5. `missing_ok=True` 有意把 raw file 缺失视为可继续清理状态，因此成功 response 不能被解读为“本次调用确实删除了一个磁盘文件”。

### 5.3 Failure taxonomy

| Failure / state | 当前行为 | 当前证据 | 工程判断 |
|---|---|---|---|
| existing empty collection list | `200 files=[]` | `MOCKED` route test | 正常 state，不应伪装 404 |
| missing collection | 404 `COLLECTION_NOT_FOUND`，不做后续读取/删除 | `MOCKED` route tests | preflight/no-side-effect 明确 |
| missing file identity | 404 `FILE_NOT_FOUND`，不触碰 disk/Chroma/index | `MOCKED` route tests | destructive rejection ordering 明确 |
| inconsistent/malformed metadata | Pydantic/key access 失败，最终可能 generic 500 | `STATIC`；专门 test `NOT_AVAILABLE` | 需要 ingestion invariant audit/reconciliation |
| preview 超过 5000 chars | 完整计算 total 后返回前 5000 chars | `MOCKED` route test | contract 已测；memory amplification 未测 |
| raw file 已缺失 | `unlink(missing_ok=True)` 后继续 cascade | `STATIC` | 支持 cleanup convergence，不证明 raw 曾存在 |
| unsafe resolved path | `INTERNAL_ERROR`，不进入 Chroma delete | `STATIC`; path matrix `NOT_AVAILABLE` | guard 存在，系统级证明不足 |
| unlink permission/IO failure | generic 500；Chroma/index 尚未改变 | `NOT_AVAILABLE` | residual durable state 完整，但 raw cleanup 未完成 |
| Chroma delete failure | generic 500；raw 可能已删除，chunks/index 仍在 | `NOT_AVAILABLE` | 最危险 partial state，无 compensation |
| process crash after Chroma delete | raw/chunks 已删，旧 keyword snapshot 可能仍在 | `NOT_AVAILABLE` | durable operation log/rebuild trigger 缺失 |
| normal keyword invalidation failure | fallback `mark_dirty()` + log | backend suite 中 synthetic failure path | cache failure 不反转 durable commit |
| fallback `mark_dirty()` failure | 异常可能传播；durable state 已变 | `STATIC`; dedicated test `NOT_AVAILABLE` | 二级 failure policy 未定义 |
| concurrent list/preview/delete | 无 snapshot/isolation contract | `NOT_AVAILABLE` | v1 single-process assumptions 不能当并发保证 |

### 5.4 性能与可用性

- list 对 collection 全量 metadata 扫描并在 Python 聚合，时间和传输量随 chunk 数增长，而不是只随 file 数增长。
- preview 读取目标文件全部 documents、构造所有 `ChunkRecord`、排序、拼接完整字符串，再截断响应；5000-char response cap 不是 memory/IO cap。
- delete 先全量 `get_files()` 找一个 `file_id`，随后 Chroma 再按 predicate get+delete，至少包含两条读取路径。
- 无 pagination、streaming、background job、timeout/cancellation 或 operation progress；大 collection 下 synchronous endpoint 会占用 request worker。
- 当前没有 benchmark 或 SLA，因此这里只能陈述 complexity pressure，不能宣称现有实现“足够快”或“不可扩展”。

### 5.5 安全、隔离与审计

- path material 由 server metadata 提供并有 resolve/parent guard，但没有专门 traversal/symlink/junction matrix。
- 不同知识库的同名文件理论上以 collection boundary 隔离；当前 focused tests 没有 concrete cross-KB destructive test。
- v1 没有 authentication/authorization，不能推断任何用户级隔离；持有 collection name/file_id 的调用者可访问对应 API。
- irreversible delete 没有 audit record、actor、request id 或 retention window；成功 message 也不返回 deleted chunk count。
- error response 由 global handler 归一化；filesystem absolute path 不应返回客户端，但日志敏感信息策略仍需部署级验证。

## 6. 规模扩大分析（Future / Not implemented in v1）

| 规模 | 当前可推断行为 | 主要压力点 | 需要的后续证据/决策 |
|---|---|---|---|
| 10x chunks / collection | list metadata scan、Python aggregation 线性增长 | latency、Chroma payload、worker memory | benchmark、pagination、file-level projection index |
| 10x chunks / file | preview 全读/排序/拼接；delete predicate 范围扩大 | response cap 不限制内部 memory；delete latency | bounded read、stored total、chunk pagination/profile |
| 100x files | delete 仍先构造完整 file list | lookup amplification、无 operation progress | direct file lookup/index、async delete decision |
| 10x concurrent management calls | 各请求独立 store 与非事务 preflight | races、重复扫描、worker blocking | concurrency matrix、idempotency/version contract |
| 多进程 workers | Chroma/filesystem durable state 共享，keyword cache process-local | invalidation coherence、stale result | durable version/event、worker rebuild protocol |
| 1000x corpus | v1 projection/preview/delete API shape仍可表达 | metadata store、backup/recovery、long-running delete | capacity limits、job model、reconciliation tooling |

任何 metadata database、queue 或 soft-delete 方案都会新增 consistency owner；在没有 profile 和 recovery requirement 前，不把它们当作自动正确答案。

## 7. Verification Review

本轮在当前 checkout 独立执行：

```text
cd backend
python -m unittest tests.test_files -v
→ 10/10 PASS

python -m unittest discover -s tests -p "test_*.py"
→ 78/78 PASS

python -m compileall -q app tests
→ PASS

git diff --check
→ PASS（无 whitespace error）
```

证据边界：

- **`MOCKED route-level`**：`test_files.py` 使用真实 FastAPI `TestClient`，但 patch `ChromaVectorStore`、filesystem unlink 或 keyword invalidation；证明 HTTP shape、error code、调用参数和成功顺序，不证明真实三存储 compatibility。
- **`STATIC/CODE-LEVEL`**：`get_files()` metadata aggregation、`get_chunks_by_file()` predicate/order、`delete_by_file()` where-filter、path guard 和 keyword fallback 可由源码确认；静态检查不能证明 OS/Chroma runtime behavior。
- **`SUBSTITUTED` historical Gate evidence**：Phase 9 Gate 留存一条 concrete smoke，真实 route/Chroma/filesystem/index 从手工 persisted chunks 起步；它没有经过 literal upload/parser/embedding/ingest，因此不能升级为 full E2E。
- **`DEFERRED / NOT_AVAILABLE`**：upload → ingest → list → preview → delete → re-upload、真实 parser/OCR/embedding、path-safety matrix、cross-KB isolation、mid-cascade failures、crash recovery、并发行为和 performance benchmark，本轮均无完整证据。

测试运行出现 Starlette 关于 `httpx`/`TestClient` 的 deprecation warning，但没有测试失败。full suite 中 synthetic keyword invalidation failure 会记录预期 traceback 后由 fallback 继续，最终 78/78 PASS；这不是本轮新 regression。

当前 Git 审计还显示既有 Phase 10 frontend/learning changes，以及无法读取的 `backend/tmpnw2f1mgn/` 目录。它们不属于 Phase 9 Engineering Review，未被修改或用作 Phase 9 正向证据。

## 8. Known Gaps & Pending Questions

1. **Mid-cascade recovery**：raw unlink 后 Chroma 失败没有 compensation；需决定优先 convergence、rollback 还是 reconciliation。
2. **Crash consistency**：Chroma commit 与 keyword dirty mark 之间没有 durable handoff；进程崩溃可能留下 stale process-local index。
3. **Path safety proof**：guard 已实现，但 traversal、absolute、separator、symlink/junction、TOCTOU 和权限矩阵缺失。
4. **Cross-KB isolation**：identity filter 与 collection boundary 在代码上分离清晰，但没有 concrete 同名文件/相同或伪造 file_id 的破坏性隔离测试。
5. **Metadata invariants**：first-chunk-wins 掩盖同一 file_id 的 file_name/size/status 不一致；缺少检测或 repair policy。
6. **Read amplification**：list 按 chunks 全扫；delete 为 lookup 建完整 file list；preview 的 response cap 不限制内部全量 read/join。
7. **Concurrency semantics**：preflight、lookup、count 与 delete 都不是 snapshot/transaction；重复 delete 和并发 upload/delete 的 observable contract 未冻结。
8. **Audit/recovery UX**：不可逆 delete 没有 actor、operation id、deleted count、tombstone、trash 或 retention policy。
9. **Authorization**：当前没有 authN/authZ 或 tenant isolation，不能将 collection boundary 表述为安全权限边界。
10. **Integration proof**：T1203 所需 literal cross-feature workflow 尚未完成；当前 mocked/substituted evidence 不能证明完整生命周期。

这些是工程边界与后续决策，不是本次 review 擅自扩张 v1 scope 或修改冻结删除顺序的理由。

## 9. Cross-links

- Technical Learning：[phase-09-file-management.md](../phase-09-file-management.md)
- Phase Gate / Learning Review context：[Phase 9 Quick Review](../phase-09-file-management.md#quick-review)
- Source contract：[SPEC F016](../../SPEC.md#f016-file-management) · [SPEC Section 12.6](../../SPEC.md#126-file-management-f016)
- Task contract：[T0901](../../TASKS.md#t0901--get-apifiles-file-list) · [T0902](../../TASKS.md#t0902--get-apifilesfile_idpreview-chunk-based-preview) · [T0903](../../TASKS.md#t0903--delete-apifilesfile_id-cascade-delete)
- Upstream storage review：[phase-01-engineering-review.md](./phase-01-engineering-review.md)
- Upstream retrieval review：[phase-06-engineering-review.md](./phase-06-engineering-review.md)
- Project map：[dx-rag-project-map.md](../project-map/dx-rag-project-map.md)
- Interview Guide：[Phase 9 深度章](../interview-notes/dx-rag-interview-guide.md#phase-9-深度章--file-management-apit0901t0903-已实现--gate--learning-review-完成)

> **Ownership boundary**：Technical Learning 解释代码、data flow 与学习 mental model；本文件记录 ADR、failure modes、一致性、规模与 Known Gaps；Interview Guide 负责可复用回答。三者 cross-link，不复制完整分析。

## 10. Review closure

Phase 9 Engineering Review 完成并仅产生文档层变更；既有 Gate verdict `PHASE_9_PASS — READY_FOR_PHASE_10` 仍是独立 context，不由本文件重判。评审未修改 `SPEC.md`、`TASKS.md` 或 application code，未启动 Phase 11，也未 commit/push。

收口结论：**当前 file-management contract 与成功/拒绝路径具备足够的代码和 mocked route evidence；不可逆 delete 的 partial-failure、crash recovery、path/system isolation 与真实跨 feature E2E 继续保持 `DEFERRED`，不得描述为已解决。**
