# Phase 9 — File Management API 学习笔记

> **Phase 状态**：✅ COMPLETE（T0901、T0902、T0903 DONE；Phase Gate Review：`PHASE_9_PASS — READY_FOR_PHASE_10`；Phase Learning Review：2026-09-04）
>
> **本文档状态**：T0901 + T0902 + T0903 Task Learning Pass、Phase Gate Review、Phase Learning Review 与独立 [Phase 9 Engineering Review](./engineering-review/phase-09-engineering-review.md) 均已完成。本文保留 Task 级代码精读与历史 checkpoint，并新增跨 Task 的 Phase mental model、验证边界、自测链与后续边界。
>
> **配套文档**：[Phase 1 VectorStore](./phase-01-vectorstore.md) · [Project Map](./project-map/dx-rag-project-map.md) · [DX-RAG Interview Guide](./interview-notes/dx-rag-interview-guide.md)

T0901、T0902 与 T0903 组成 Phase 9 的三个 File Management API slice：T0901 暴露 `VectorStore.get_files()` 派生列表，T0902 从 persisted chunks 重建 preview，T0903 删除 raw file、ChromaDB chunks/vectors/metadata 并 invalidate keyword index。列表的 source of truth 是 chunk metadata 的 `file_id` 聚合，preview 的 source of truth 是该 `file_id` 的 persisted chunk content，delete 则以 `(collection_name, file_id)` 定位并跨三个存储目标清理。[PROJECT FACT]

## 0. 三层文档边界

| Layer | Canonical home | 本 Phase / 文档怎么处理 |
|---|---|---|
| Layer 1 — Technical Learning | 本文 | 解释 route、schema、storage adapter 的 data flow、Python/FastAPI 学习点、验证边界与 self-test |
| Layer 2 — Engineering Review | [phase-09-engineering-review.md](./engineering-review/phase-09-engineering-review.md)（2026-09-04 完成） | 完整 ADR、failure taxonomy、规模分析、Known Gaps 与 review closure |
| Layer 3 — Interview Preparation | [Interview Guide](./interview-notes/dx-rag-interview-guide.md) | Task 级只保留短 Interview Candidates；Phase Learning Review 后的完整 Phase 9 话术与高频追问归档在 Interview Guide |
| Task / Phase 状态 | [`docs/TASKS.md`](../TASKS.md) · [Learning workflow](./templates/phase-learning-pass-workflow.md) | TASKS 是任务状态 source of truth；本次 Phase Learning Review 只更新学习文档，不修改 TASKS、SPEC 或应用代码 |

本文中的 `[PROJECT FACT]` 来自当前 `TASKS.md`、`SPEC.md`、`files.py`、`router.py`、`main.py`、`schemas.py`、`vector_store.py`、`test_files.py` 与本轮测试；`[ENGINEERING KNOWLEDGE]` 是可迁移的工程概念；`[FUTURE]` 明确表示尚未实现的能力。

## 1. Phase 学习：文件管理 API 的第一个可见切片

### 一句话定位

Phase 9 把“知识库里有哪些已成功入库的文件、已入库文本是什么样、如何移除文件”从 storage-level data 暴露为 HTTP API：T0901 完成 file list，T0902 完成 chunk-based preview，T0903 完成 cascade delete；三个 Task、Phase Gate Review 与 Phase Learning Review 均已收口。[PROJECT FACT]

### 核心学习点

- 🟢 **必会**：`file_id` 是文件 identity；`file_name` 只是 display value；文件列表由 chunk metadata 按 `file_id` 聚合，而不是由目录扫描得到。
- 🟢 **必会**：missing collection 返回 404 `COLLECTION_NOT_FOUND`；existing-but-empty collection 返回 200 且 `files=[]`，两个状态不能合并。
- 🟢 **必会**：API 使用 `response_model=FileListResponse` 锁定 `{collection_name, files}`，每个 `FileItem` 锁定六个字段；route 不把 Chroma private object 泄露给调用方。
- 🟢 **必会**：preview 使用 `file_id` 定位 persisted chunks，按 `chunk_index` ASC 以 `\n\n` 拼接；`total_chars` 在截断前计算，`preview_chars` 是实际返回内容长度，最多 5000 字符。
- 🟢 **必会**：delete 先用 `(collection_name, file_id)` 找到 display-only `file_name`，再按磁盘 → ChromaDB → keyword index 的顺序执行不可逆清理；缺 collection/file 必须在副作用前返回不同的 404 code。
- 🟡 **了解即可**：FastAPI `Query(...)`、`APIRouter` 注册、`model_validate()`、列表推导式与全局 `AppError` handler。
- 🔵 **知道存在即可**：pagination、独立 metadata database、鉴权、de-overlap、batch/undo、跨存储事务与跨 feature E2E；它们不属于已完成的 T0901/T0902/T0903 slice。

### 前置知识与学习路线

1. 先读 [Phase 1 T0107](./phase-01-vectorstore.md) 的 `get_files()`：理解为什么没有 FileRecord table，以及 `file_size → size`、`ingestion_status → status` 的字段翻译。
2. 复习 Phase 4 的 collection existence 与 Phase 5 的 upload/ingestion 状态，理解为什么 FAILED ingestion 没有 chunk 就不会出现在列表。
3. 阅读 [`FileItem` / `FileListResponse` / `FilePreviewResponse` / `FileDeleteResponse`](../../backend/app/models/schemas.py#L152-L188)、[`files.py`](../../backend/app/api/files.py#L21-L112) 与 [`router.py`](../../backend/app/api/router.py#L1-L20)。
4. 阅读 [`FileListEndpointTests`](../../backend/tests/test_files.py#L12-L289)，先预测 list、preview 与 delete 的成功/空态/缺失/级联顺序响应，再运行验证命令。

## 2. Phase 目标：从派生文件视图到 HTTP management boundary

### 业务目标

F016 的文件管理包括列表、预览和删除。列表让用户知道某个 Knowledge Base 当前有哪些已入库文件及其 metadata；空 Knowledge Base 是正常的 empty state，非-existent Knowledge Base 才是 404 error。[PROJECT FACT]

### T0901 技术目标

```text
GET /api/files?collection_name=xxx
  → collection existence check
  → VectorStore.get_files(collection)
  → FileItem validation
  → FileListResponse
```

具体 contract 是：

- collection 存在且有 3 个文件时返回 3 条 `{file_id, file_name, size, upload_time, chunk_count, status}`；
- collection 存在但没有 chunks 时返回 200 和空数组；
- collection 不存在时在调用 `get_files()` 前返回 404 `COLLECTION_NOT_FOUND`；
- response shape 对齐 SPEC Section 6.6，不能把 chunk content、embedding 或 storage internals 顺手加进文件列表。[PROJECT FACT]

### T0902 技术目标

```text
GET /api/files/{file_id}/preview?collection_name=xxx
  → collection existence check
  → VectorStore.get_chunks_by_file(collection, file_id)
  → chunk_index ASC defensive sort
  → concatenate persisted content with "\n\n"
  → total_chars before truncation
  → MAX_PREVIEW_CHARS slice
  → FilePreviewResponse
```

具体 contract 是：

- `file_id` 来自 path，是 preview 的 resource identity；`collection_name` 来自 required query parameter；
- collection 不存在时，在 `get_chunks_by_file()` 前返回 404 `COLLECTION_NOT_FOUND`；
- collection 存在但该 `file_id` 没有 chunks 时返回 404 `FILE_NOT_FOUND`；
- chunks 按 `chunk_index` ASC 排序后，以 `\n\n` 拼接已持久化的 `content`；
- `total_chars` 是完整拼接文本的字符数，`content` 再按 `settings.MAX_PREVIEW_CHARS`（当前为 5000）截断，`preview_chars` 是截断后实际返回的字符数；
- response 只包含 `file_id`、`file_name`、`collection_name`、`content`、`preview_chars`、`total_chars`；不调用 parser、OCR、embedding、LLM，也不重新读取 `uploads/`。[PROJECT FACT]

### T0903 技术目标

```text
DELETE /api/files/{file_id}?collection_name=xxx
  → collection existence check
  → VectorStore.get_files(collection) 找到 file_name
  → file_id 不存在 → FILE_NOT_FOUND
  → safe raw-file unlink
  → VectorStore.delete_by_file(collection, file_id)
  → invalidate_keyword_index(collection)
  → FileDeleteResponse
```

具体 contract 是：

- `file_id` 来自 path，`collection_name` 来自 required query parameter；文件名只从已持久化的 file-level record 取得，不由客户端提供；
- collection 不存在时返回 404 `COLLECTION_NOT_FOUND`；存在但 `get_files()` 找不到该 `file_id` 时返回 404 `FILE_NOT_FOUND`，两种错误都必须发生在删除副作用之前；
- 成功路径按当前实现的确定顺序删除 `uploads/{collection_name}/{file_name}`、ChromaDB 中该 `file_id` 的 chunks/vectors/metadata，再调用 keyword-index invalidation seam；
- raw-file helper 要求解析后的目标仍是 collection 目录的直接子文件，并使用 `missing_ok=True`；路径不满足不变量时抛出 `INTERNAL_ERROR`，避免越界删除；
- 成功 response 只包含 `message`、`file_name`、`collection_name`；操作不可逆，不提供 batch delete、undo 或 trash recovery。[PROJECT FACT]

### 明确不做什么

- 不在本学习文档中扩展 batch delete、undo 或 trash recovery；单文件 raw file、Chroma chunks/vectors/metadata 与 keyword-index cascade 已由 T0903 实现。
- 不新增 SQLite/PostgreSQL 等 external metadata database；F016/Section 7.3 仍规定从 chunk metadata 聚合。
- 不扫描 `uploads/` 目录作为列表 source of truth，不重新解析原始文件，不调用 parser、OCR、embedding 或 LLM。
- 不在 T0901/T0902/T0903 做 pagination、authentication、batch operation、undo/trash recovery 或 cross-feature upload → list → preview → delete E2E。[FUTURE]

相关契约：[SPEC F016](../SPEC.md#f016-file-management)、[SPEC Section 6.6](../SPEC.md#66-file-management)、[SPEC Section 7.3 FileRecord](../SPEC.md#73-filerecord)、[SPEC Section 9.2](../SPEC.md#92-error-codes)、[T0901](../TASKS.md#t0901--get-apifiles-file-list)、[T0902](../TASKS.md#t0902--get-apifilesfile_idpreview-chunk-based-preview)、[T0903](../TASKS.md#t0903--delete-apifilesfile_id-cascade-delete)、[T0106](../TASKS.md#t0106--chromadb-delete-by-file-id)、[T0107](../TASKS.md#t0107--chromadb-get-files-metadata-aggregation)、[T0108](../TASKS.md#t0108--chromadb-list_chunks-get_chunk_count-get_chunks_by_file)、[T0602](../TASKS.md#t0602--inverted-index--keyword-search) 与 [T1203](../TASKS.md#t1203--file-management--security-cross-feature-verification)。

## 3. 项目位置：API Layer 与 Storage / File / Index Layer 之间的管理适配器

### 所属层与上下游

| 方向 | 契约 / 模块 | T0901/T0902/T0903 的责任 |
|---|---|---|
| HTTP upstream | FastAPI path `file_id: str` + query parameter `collection_name: str` | list/preview/delete 共用 collection selector；preview/delete 再绑定 file identity |
| Storage upstream | `ChromaVectorStore.list_collections()` | 在读取文件前确认 collection identity 存在 |
| Storage data source | `VectorStore.get_files(collection)` / T0107；`get_chunks_by_file(collection, file_id)` / T0108；`delete_by_file(collection, file_id)` / T0106 | T0901 消费 file-level records；T0902 消费 `ChunkRecord`；T0903 用 file-level record 找 display name，再调用 file-scoped delete |
| File-system boundary | `settings.UPLOAD_DIR` + `_delete_raw_file()` | T0903 解析并校验目标必须是 collection 目录的直接子文件，再执行幂等 `unlink` |
| Keyword-index boundary | `invalidate_keyword_index(collection)` / T0602 seam | T0903 在 Chroma 删除后标记该 collection index dirty；下次 keyword search 再 rebuild |
| Schema boundary | `FileItem`、`FileListResponse`、`FilePreviewResponse`、`FileDeleteResponse` | 把 list/preview/delete 的内部结果变成受 Pydantic response model 约束的 JSON |
| HTTP downstream | `app.main` 的 `/api` prefix + global `AppError` handler | 对外形成 `/api/files`、`/api/files/{file_id}/preview`、`DELETE /api/files/{file_id}` 与统一错误 envelope |
| Future consumers | Phase 10/11 frontend、T1203 integration verification | 消费列表、诊断性 preview 与删除结果；跨 feature lifecycle 仍待 T1203 |

T0901 在查询路径之外增加了一条“管理 read path”：它读取已经落盘的文件级派生视图，不改变向量、chunk 或 keyword index。存储层的 `get_files()` 已在 T0107 完成，T0901 的增量是 API adapter 和 route registration，而不是重新实现 storage aggregation。[PROJECT FACT]

T0902 沿着同一条 read-only boundary 继续向下读取：`get_chunks_by_file()` 返回已经持久化的 `ChunkRecord`，API 层负责顺序、拼接、截断和 response shape。它只重建“当前入库文本的诊断性视图”，不承诺原始文档的精确还原，也不引入 parser/OCR/embedding/LLM 副作用。[PROJECT FACT]

T0903 则是同一管理 API 的第一个 write path：先用 `get_files()` 找到 file-level display metadata，再把一个 `file_id` 的副作用分发到 filesystem、ChromaDB 与 keyword index 三个边界。它没有跨存储 transaction；因此“顺序确定”不等于“全链路原子”。[PROJECT FACT]

### 数据流图

```text
GET /api/files?collection_name=test-kb
  │
  ├─ FastAPI Query(...) → collection_name: str
  │
  ├─ ChromaVectorStore()
  │    └─ list_collections()
  │         ├─ not found → AppError(COLLECTION_NOT_FOUND) → 404 envelope
  │         └─ found
  │              └─ get_files(collection)
  │                   └─ T0107: chunk metadata → group by file_id → List[dict]
  │
  ├─ FileItem.model_validate(file_record) → List[FileItem]
  └─ FileListResponse(collection_name, files) → HTTP 200 JSON

GET /api/files/file-1/preview?collection_name=test-kb
  │
  ├─ FastAPI path file_id + Query(...) collection_name
  ├─ ChromaVectorStore().list_collections()
  │    ├─ not found → AppError(COLLECTION_NOT_FOUND) → 404 envelope
  │    └─ found
  │         └─ get_chunks_by_file(collection, file_id)
  │              ├─ [] → AppError(FILE_NOT_FOUND) → 404 envelope
  │              └─ ChunkRecord[]
  │                   → sorted(chunk_index ASC)
  │                   → "\n\n" join persisted content
  │                   → total_chars
  │                   → [:MAX_PREVIEW_CHARS]
  │                   → FilePreviewResponse → HTTP 200 JSON

DELETE /api/files/file-1?collection_name=test-kb
  │
  ├─ FastAPI path file_id + Query(...) collection_name
  ├─ ChromaVectorStore().list_collections()
  │    ├─ absent → AppError(COLLECTION_NOT_FOUND) → 404; no cascade
  │    └─ present
  │         └─ get_files(collection)
  │              ├─ no matching file_id → AppError(FILE_NOT_FOUND) → 404; no cascade
  │              └─ file_name
  │                   → _delete_raw_file(collection, file_name)
  │                   → delete_by_file(collection, file_id)
  │                       └─ Chroma chunks + vectors + metadata
  │                   → invalidate_keyword_index(collection)
  │                   → FileDeleteResponse → HTTP 200 JSON
```

## 4. Task 学习：T0901 + T0902 — File List 与 Chunk-Based Preview

### 4.1 A. Code Understanding

#### Route 的输入、控制流和输出

- `router = APIRouter()` 位于 [`files.py:10`](../../backend/app/api/files.py#L10)。它让文件管理 endpoint 可以独立定义，再由总 router 组合。
- `@router.get("/files", response_model=FileListResponse)` 位于 [`files.py:13`](../../backend/app/api/files.py#L13)。同一个声明同时确定 URL method/path 与 response schema。
- `collection_name: str = Query(...)` 位于 [`files.py:14-L16`](../../backend/app/api/files.py#L14-L16)，表示 query parameter 是必填字符串；它不是 request body，也不是 path parameter。
- `ChromaVectorStore()` 在 [`files.py:18`](../../backend/app/api/files.py#L18) 创建当前请求使用的 storage adapter。endpoint 只接触 public methods，不接触 `_client` 或 `_collection`。
- `list_collections()` 检查在 [`files.py:19-L20`](../../backend/app/api/files.py#L19-L20) 发生。不存在时抛出 `AppError("COLLECTION_NOT_FOUND")`，由 [`main.py:43-L67`](../../backend/app/main.py#L43-L67) 的全局 handler 映射为 404 envelope；因此 missing collection 不会继续读取文件。
- 列表推导式在 [`files.py:22-L24`](../../backend/app/api/files.py#L22-L24) 对每条 storage dict 执行 `FileItem.model_validate()`。这是 API-side shape validation，不是重新计算 `chunk_count`。
- `FileListResponse(...)` 在 [`files.py:26`](../../backend/app/api/files.py#L26) 组装顶层 `collection_name` 和 `files`，FastAPI 再按 `response_model` 序列化返回。

#### Storage contract 由谁负责

T0901 不重复实现 `get_files()`。T0107 的 [`ChromaVectorStore.get_files()`](../../backend/app/core/vector_store.py#L542-L566) 通过 Chroma public `get(include=["metadatas"])` 取出所有 chunk metadata，再以 `file_id` 为 key 聚合：首个 chunk 提供 `file_name`、`file_size`、`upload_time`、`ingestion_status`，每个 chunk 将 `chunk_count` 加一，最后输出 `list(files.values())`。因此 API 层只做 boundary translation：`dict → FileItem → FileListResponse`。[PROJECT FACT]

#### Schema 锁定的字段

[`FileItem`](../../backend/app/models/schemas.py#L152-L160) 的六个字段是 `file_id`、`file_name`、`size`、`upload_time`、`chunk_count`、`status`；[`FileListResponse`](../../backend/app/models/schemas.py#L163-L169) 再包一层 `collection_name` 和 `files`。`size/status` 是对内部 metadata `file_size/ingestion_status` 的 API 命名翻译，不能因为 Python dict 是动态的就把内部字段原样暴露。[PROJECT FACT]

### 4.2 B. Project Understanding

T0901 解决的不是“把一个 Python list 返回给浏览器”，而是把文件管理的 source of truth 放在正确的边界：

1. **Storage layer** 负责从 chunk metadata 派生 file-level view；它知道 Chroma 的读取方式，但不负责 HTTP status。
2. **API layer** 负责 collection existence、response model 和错误 envelope；它不重新扫描目录，也不读取 Chroma private object。
3. **Frontend / later integration** 将来消费稳定的六字段 records、诊断性 preview 与删除结果；T0902/T0903 分别提供独立的 read path 与 side-effect path，跨 feature lifecycle 仍由后续集成负责。

这个拆分延续了 Phase 1 的 Adapter / public-interface boundary：没有 metadata database 时，列表仍然是可重建的 derived view；FAILED ingestion 因为不产生 chunks，自然不会生成“幽灵文件”记录。[PROJECT FACT]

### 4.3 C. Learning Understanding

对熟悉 TypeScript/Node 的前端开发者，可以把 T0901 看成一个只读 route adapter：

```ts
type FileItem = {
  file_id: string;
  file_name: string;
  size: number;
  upload_time: string;
  chunk_count: number;
  status: string;
};

type FileStore = {
  listCollections(): string[];
  getFiles(collection: string): Record<string, unknown>[];
};

function listFiles(collectionName: string, store: FileStore) {
  if (!store.listCollections().includes(collectionName)) {
    throw new CollectionNotFoundError();
  }
  return {
    collection_name: collectionName,
    files: store.getFiles(collectionName).map((raw) => validateFileItem(raw)),
  };
}
```

Python 的 `FileItem.model_validate(raw)` 类似 runtime schema validation；`response_model=FileListResponse` 类似对 handler 返回值再加一道公开 DTO 检查。差异是 Pydantic model 同时承担字段声明、校验和序列化，而 TypeScript interface 本身不会在 runtime 验证对象。[ENGINEERING KNOWLEDGE]

本 Task 最值得迁移的 mental model 是：**一个 API endpoint 是 contract adapter，不是数据源；它应先确认资源边界，再读取唯一 source of truth，最后把内部形态映射为稳定的公开 DTO。**

### 4.4 验证（Verification）

T0901 新增 [`FileListEndpointTests`](../../backend/tests/test_files.py#L12-L110) 的 3 个 route-level tests：

| Test | 观察行为 | 证据标签 |
|---|---|---|
| `test_populated_collection_returns_file_records` | patched store 返回 3 个 records；HTTP 200；顶层 collection_name 和六字段 records 原样符合 response model；确认 `list_collections()` 与 `get_files()` 调用顺序/参数 | **MOCKED** route composition |
| `test_empty_collection_returns_empty_files` | existing collection 的 `get_files()` 返回 `[]`；HTTP 200、`files=[]`，不是 error | **MOCKED** empty-state boundary |
| `test_missing_collection_returns_404_without_getting_files` | `list_collections()` 返回空列表；HTTP 404 `COLLECTION_NOT_FOUND`；`get_files()` 未被调用 | **MOCKED** preflight/error boundary |

这些测试使用真实 FastAPI `TestClient` 和真实路由注册，但 patch `app.api.files.ChromaVectorStore` 为 `Mock`；因此它们证明的是 HTTP wiring、Pydantic response shape、调用顺序与 error mapping，不证明 concrete Chroma persistence、真实 T0107 aggregation、upload → ChromaDB → `/api/files` E2E 或前端消费。[PROJECT FACT]

建议从 `backend` 目录运行：

```powershell
python -m unittest tests.test_files -v
python -m unittest discover -s tests -p "test_*.py" -q
python -m compileall -q app tests
```

本次 Learning Pass 的当前 checkout 证据应分别记录：T0901/T0902/T0903 tests 的方法级结果、全量 suite 结果和 compileall 结果；不要把 Mocked route tests 写成 concrete Chroma E2E。[PROJECT FACT]

### 4.5 Interview Candidates（Task 级，仅候选）

> Task-level candidate 保持短小；Phase 9 Learning Review 已完成跨 Task consolidation，完整 30 秒答案与高频追问已提升到 [Interview Guide](./interview-notes/dx-rag-interview-guide.md) 的 Phase 9 深度章。

- **Technical Points**：`get_files()` 是 chunk metadata 的 derived view；`file_id` 去重、`chunk_count` 聚合、`file_size → size` 字段翻译；`FileItem.model_validate()` 与 `response_model` 的双层 response contract。
- **Engineering Questions**：为什么 missing collection 要在 `get_files()` 前拦截？为什么不扫 `uploads/`？为什么 empty collection 是 200 而不是 404？
- **Candidate Interview Questions**：`FileRecord` 为什么不单独存表？T0901 的 3 个 Mocked tests 能证明什么、不能证明什么？如果列表变慢，先检查 full metadata scan 还是 API serialization？
- **STAR Candidate**：无；这是普通 Task，没有已闭环 incident。

### 4.6 T0902 — `GET /api/files/{file_id}/preview`（Chunk-Based Preview）

#### A. Code Understanding

T0902 的 route 位于 [`files.py:29-L56`](../../backend/app/api/files.py#L29-L56)，对应 SPEC F016 的“从 persisted chunks 展示当前已入库文本”语义：

1. `file_id: str` 是 path parameter，表示要查找的文件 identity；`collection_name: str = Query(...)` 是 required query parameter，表示查找范围。两者一起构成 `(collection, file_id)` 的资源定位，而不是用 `file_name` 做 lookup。
2. endpoint 创建 `ChromaVectorStore()`，先调用 `list_collections()`。collection 不存在时立即抛出 `AppError("COLLECTION_NOT_FOUND")`，全局 handler 将它映射为 404；因此不会把 missing collection 当成“该文件没有 chunks”。
3. collection 存在后调用 `get_chunks_by_file(collection_name, file_id)`。返回空列表时抛出 `AppError("FILE_NOT_FOUND")`；这是“有效 Knowledge Base 中没有该文件”的错误边界。
4. 即使 T0108 的 storage contract 已保证 `chunk_index` 升序，endpoint 仍用 `sorted(..., key=lambda chunk: chunk.chunk_index)` 做 defensive ordering。这样 route 的 preview contract 不依赖 mock、替代 adapter 或未来 storage 实现是否已经排序。
5. `"\n\n".join(chunk.content for chunk in ordered_chunks)` 只读取 `ChunkRecord.content`，重建的是已持久化的文本。chunk overlap、Markdown heading-path 等产物会保留；T0902 不做 de-overlap、heading 去重或原始文件重解析。
6. 先计算 `full_content` 的长度，再用 `full_content[: settings.MAX_PREVIEW_CHARS]` 截断。当前 [`config.py:66`](../../backend/app/core/config.py#L66) 的 `MAX_PREVIEW_CHARS` 是 5000；`total_chars` 反映截断前的完整拼接长度，`preview_chars` 反映实际返回 `content` 的长度。
7. `FilePreviewResponse` 在 [`schemas.py:172-L180`](../../backend/app/models/schemas.py#L172-L180) 锁定六个公开字段。`file_name` 取排序后第一个 chunk 的 display metadata；同一 `file_id` 的 chunks 应共享该元数据，文件 identity 仍由 `file_id` 承担。[PROJECT FACT]

#### B. Project Understanding

T0902 的关键不是“从文件系统打开文件并截取前 5000 个字符”，而是尊重 ingestion 的持久化边界：

- **T0108 / storage** 负责在指定 collection 内按 `file_id` 取回 `ChunkRecord`，并在 concrete Chroma adapter 中按 `chunk_index` 排序；它不负责 HTTP status 或 preview length。
- **T0902 / API** 负责 collection preflight、file-not-found 语义、顺序防御、chunk 拼接、截断与 Pydantic response serialization；它不调用 parser、OCR、embedding model、LLM，也不重新读取 `uploads/`。
- **Frontend / later integration** 将来可以根据 `preview_chars < total_chars` 显示“内容已截断”，但不能把这个 endpoint 当成原始 PDF/DOCX 的 byte-for-byte 或 layout-faithful reconstruction。[PROJECT FACT]

这条边界把“可诊断的 ingestion 结果”与“原始文件预览器”分开：当前 preview 让开发者确认哪些文本真正进入了知识库，同时避免重复计算、模型调用和原始文件状态漂移。若未来需要精确渲染、分页或按页预览，应另立 contract，而不是在 T0902 偷换语义。[ENGINEERING KNOWLEDGE]

#### C. Learning Understanding

对熟悉 TypeScript/Node 的前端开发者，可以把核心重建逻辑理解为：

```ts
type ChunkRecord = {
  chunk_id: string;
  file_id: string;
  file_name: string;
  chunk_index: number;
  content: string;
};

function buildPreview(chunks: ChunkRecord[], maxChars: number) {
  const ordered = [...chunks].sort(
    (a, b) => a.chunk_index - b.chunk_index,
  );
  const fullContent = ordered.map((chunk) => chunk.content).join("\n\n");
  const content = fullContent.slice(0, maxChars);
  return {
    file_id: ordered[0].file_id,
    file_name: ordered[0].file_name,
    content,
    preview_chars: content.length,
    total_chars: fullContent.length,
  };
}
```

Python 的 `sorted()` 不会原地修改由 storage 返回的 list，和 TypeScript 中先展开为 `[...chunks]` 再 `.sort()` 的意图相似；generator expression 让 `join()` 只产生待拼接的 content；字符串切片 `[:5000]` 与 JavaScript `slice(0, 5000)` 都是按字符序列截取，而不是按 chunk 数截取。区别在于 Python/Pydantic 的 response model 会在 API boundary 做 runtime 字段约束，TypeScript type 主要是编译期提示。[ENGINEERING KNOWLEDGE]

#### 4.6.1 验证（Verification）

T0902 在 [`FileListEndpointTests`](../../backend/tests/test_files.py#L112-L202) 中新增 4 个 route-level tests：

| Test | 观察行为 | 证据标签 |
|---|---|---|
| `test_preview_reconstructs_chunks_in_chunk_index_order` | patched store 故意以 2、0、1 顺序返回 chunks；HTTP 200 的 content 仍为 `first\n\nmiddle\n\nlast`，并验证 `(collection, file_id)` 参数 | **MOCKED** ordering/reconstruction |
| `test_preview_truncates_content_and_keeps_full_total` | 两个 3000 字符 chunks 拼接后，content 截到 5000；`preview_chars == 5000`，`total_chars` 仍是完整拼接长度 | **MOCKED** truncation/length semantics |
| `test_preview_missing_collection_returns_404_without_chunk_lookup` | collection preflight 失败时返回 404 `COLLECTION_NOT_FOUND`，且 `get_chunks_by_file()` 未调用 | **MOCKED** preflight/error boundary |
| `test_preview_missing_file_returns_404` | collection 存在但 chunk lookup 返回 `[]` 时返回 404 `FILE_NOT_FOUND` | **MOCKED** file-not-found boundary |

这些测试使用真实 FastAPI `TestClient` 和真实 route registration，但 patch `app.api.files.ChromaVectorStore` 为 `Mock`。因此它们证明 HTTP path/query binding、error mapping、拼接/截断逻辑和 response shape；它们不证明 concrete Chroma persistence、真实 T0108 → preview、upload → ChromaDB → preview E2E、parser/OCR/embedding/LLM 未被真实调用，或前端展示行为。[PROJECT FACT]

#### 4.6.2 Interview Candidates（Task 级，仅候选）

> Task-level candidate 保持短小；Phase 9 Learning Review 已完成跨 Task consolidation，完整答案统一归档在 [Interview Guide](./interview-notes/dx-rag-interview-guide.md) 的 Phase 9 深度章。

- **Technical Points**：为何用 `(collection_name, file_id)` 定位资源；`ChunkRecord` 与 `FilePreviewResponse` 的 boundary；`chunk_index` 排序、`\n\n` join、`MAX_PREVIEW_CHARS`、`total_chars`/`preview_chars` 的先后关系。
- **Engineering Questions**：为什么 preview 要读 persisted chunks 而不是重解析 `uploads/`？为什么保留 overlap/heading artifacts？为什么 storage 已排序后 API 仍 defensive sort？
- **Candidate Interview Questions**：如果 `total_chars > 5000`，哪些字段变化、哪些字段不变？如何证明 missing collection 不会触发 chunk lookup？如何设计真实 Chroma integration test 而不把 Mocked route test 冒充 E2E？
- **STAR Candidate**：无；当前没有已闭环 incident 或性能/数据修复案例。

### 4.7 T0903 — `DELETE /api/files/{file_id}`（Cascade Delete）

#### A. Code Understanding

T0903 的 route 位于 [`files.py:67-L112`](../../backend/app/api/files.py#L67-L112)，对应 SPEC F016 的“raw file + ChromaDB + keyword index”级联清理：

1. `file_id: str` 来自 path，`collection_name: str = Query(...)` 来自 required query；调用方不能把任意 `file_name` 直接传给删除逻辑。
2. route 先创建 `ChromaVectorStore()` 并检查 `list_collections()`。collection 不存在时抛出 `COLLECTION_NOT_FOUND`，全局 handler 返回 404；此时 `get_files()`、磁盘删除、Chroma 删除和 keyword invalidation 都不会执行。
3. collection 存在后，`next(..., None)` 扫描 `get_files(collection)` 找到 `record["file_id"] == file_id` 的 file-level record。找不到时抛出 `FILE_NOT_FOUND`，因此不存在的 file_id 不会触发任何 cascade。
4. 成功匹配后只从 storage record 读取 `file_name`。`_delete_raw_file()` 先对 upload root、collection 目录和目标文件执行 `resolve()`，并用 `PureWindowsPath(file_name).name == file_name`、父目录关系检查阻止路径分隔符、`..`、绝对路径或 symlink 越界；不满足安全不变量时抛出 `INTERNAL_ERROR`。
5. 当前 contract 的副作用顺序是：`_delete_raw_file()` → `vector_store.delete_by_file()` → `invalidate_keyword_index()`。前者以 `target.unlink(missing_ok=True)` 删除 raw file；T0106 的 [`delete_by_file()`](../../backend/app/core/vector_store.py#L525-L540) 先按 `file_id` 取匹配 ID 计数，再用同一 where 条件删除 Chroma chunks/vectors/metadata；T0602 seam 只把已存在的 keyword index 标记 dirty，下次 search 才 rebuild。
6. 成功返回 [`FileDeleteResponse`](../../backend/app/models/schemas.py#L183-L188)：`message`、`file_name`、`collection_name`。没有 deleted-count 字段、undo token 或恢复机制；“删除成功”不等于可以恢复原始文件。[PROJECT FACT]

#### B. Project Understanding

T0903 是 Phase 9 从 read path 进入 side-effect path 的边界：

- **API layer** 负责资源 preflight、file-level lookup、路径安全 guard、跨边界调用顺序、错误 envelope 与 response DTO。
- **File system** 只负责删除 `uploads/{collection_name}/{file_name}`；它不负责决定 file_id 是否存在。
- **VectorStore / T0106** 负责按 `file_id` 删除 Chroma 中的 chunks、vectors 与 metadata，并返回删除数量；API 当前不把这个内部计数暴露给 response。
- **Keyword index / T0602** 负责让旧 inverted index 在下一次查询前失效；它不是 Chroma 删除的事务参与者。

这三个目标没有共享 transaction。当前实现选择确定的“磁盘 → ChromaDB → index”顺序，符合 T0903 task contract，但如果中间一步抛错，已经完成的前一步不会自动补偿。例如磁盘已删而 Chroma 删除失败时，仍可能留下可检索的 orphan chunks；这属于需要独立工程决策或 T1203 验证的 residual-state 风险，不应在 Task Learning Pass 中假装成原子操作。[ENGINEERING KNOWLEDGE]

#### C. Learning Understanding

对熟悉 TypeScript/Node 的前端开发者，可以把 T0903 想成一个显式编排多个 side effect 的 handler：

```ts
async function deleteFile(
  collectionName: string,
  fileId: string,
  store: FileStore,
) {
  if (!store.listCollections().includes(collectionName)) {
    throw new CollectionNotFoundError();
  }

  const record = store
    .getFiles(collectionName)
    .find((item) => item.file_id === fileId);
  if (!record) throw new FileNotFoundError();

  await fs.rm(path.join(uploadRoot, collectionName, record.file_name), {
    force: true,
  });
  await store.deleteByFile(collectionName, fileId);
  invalidateKeywordIndex(collectionName);

  return {
    message: "文件删除成功",
    file_name: record.file_name,
    collection_name: collectionName,
  };
}
```

Python 的 `next(generator, None)` 类似 JavaScript 的 `.find()` 加上 `undefined` fallback；`Path.resolve()` + parent comparison 是 filesystem boundary 的 runtime guard；`missing_ok=True` 类似 `fs.rm(..., {force: true})` 的“目标已不存在也不报错”。但两种语言都不会因为连续写了三个 `await`/调用就自动获得 distributed transaction：失败恢复、重试与幂等策略必须由工程设计明确提供。[ENGINEERING KNOWLEDGE]

#### 4.7.1 验证（Verification）

T0903 在 [`FileListEndpointTests`](../../backend/tests/test_files.py#L204-L289) 中新增 3 个 route-level tests：

| Test | 观察行为 | 证据标签 |
|---|---|---|
| `test_delete_file_removes_disk_and_storage_in_order` | patched store 返回 file record；patch `Path.unlink`、`delete_by_file`、`invalidate_keyword_index` 收集事件；HTTP 200 response 正确，事件顺序为 `disk → chroma → index` | **MOCKED** cascade orchestration |
| `test_delete_missing_collection_returns_404_without_cascade` | collection preflight 失败返回 404 `COLLECTION_NOT_FOUND`；`get_files()`、`delete_by_file()`、invalidation 都未调用 | **MOCKED** preflight/no-side-effect boundary |
| `test_delete_missing_file_returns_404_without_cascade` | file-level lookup 找不到 path file_id 返回 404 `FILE_NOT_FOUND`；raw delete、Chroma delete、invalidation 都未调用 | **MOCKED** file-not-found/no-side-effect boundary |

这些测试使用真实 FastAPI `TestClient` 和真实 route registration，但把 Chroma store、filesystem unlink 与 keyword invalidation 都 patch 掉。因此它们证明 route 编排、resource lookup、错误映射和调用顺序；不证明真实 raw file 已删除、真实 Chroma chunks/vectors/metadata 已删除、真实 keyword cache 已 rebuild，也不覆盖 `_delete_raw_file()` 的 traversal/symlink guard。[PROJECT FACT]

辅助证据是 T0106 的 concrete code inspection（`delete_by_file` 的 where 过滤与先数后删）以及 T0602 的独立 keyword-index invalidation lifecycle test；它们不能合并成 upload → delete → query 的真实跨存储 E2E。当前没有专门的 path-safety test 或 mid-cascade failure/compensation test，记为 **NOT_AVAILABLE / DEFERRED**。[PROJECT FACT]

#### 4.7.2 Interview Candidates（Task 级，仅候选）

> Task-level candidate 保持短小；Phase 9 Learning Review 已完成跨 Task consolidation，完整答案统一归档在 [Interview Guide](./interview-notes/dx-rag-interview-guide.md) 的 Phase 9 深度章。

- **Technical Points**：`(collection_name, file_id)` identity；`get_files()` 找 display filename；`PureWindowsPath` + `resolve()` path guard；磁盘 → ChromaDB → keyword-index 的固定顺序；`missing_ok=True` 与 `delete_by_file(where={file_id})`。
- **Engineering Questions**：为什么不能让客户端直接传 `file_name` 删除？为什么缺 collection/file 必须在副作用前返回？三个存储目标没有 transaction 时如何处理 partial failure？keyword invalidation 为什么是 dirty mark 而不是立即 rebuild？
- **Candidate Interview Questions**：如果 Chroma 删除失败但磁盘已删，系统会留下什么残留？如何补一条真实临时目录 + Chroma test？如何证明 path guard 拒绝 `../doc.pdf`、绝对路径和 symlink？为什么 current tests 只能叫 Mocked？
- **STAR Candidate**：无；当前只有 route orchestration evidence，没有已闭环的删除事故或恢复案例。

## 5. 代码理解：五处关键边界

### 精读 1：`list_files()`（`backend/app/api/files.py:13-26`）

```python
@router.get("/files", response_model=FileListResponse)
def list_files(
    collection_name: str = Query(..., description="Target knowledge base name"),
) -> FileListResponse:
    vector_store = ChromaVectorStore()
    if collection_name not in vector_store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    files = [
        FileItem.model_validate(file_record)
        for file_record in vector_store.get_files(collection_name)
    ]
    return FileListResponse(collection_name=collection_name, files=files)
```

- decorator 把 Python function 变成 `/api/files`（总 router 的 `/api` prefix 由 [`main.py:68`](../../backend/app/main.py#L68) 加上）并锁定 response model；
- `Query(...)` 让 resource selector 来自 query string，且缺失参数在进入 storage 前被 FastAPI 拦截；
- existence check 与 data read 分开，避免“collection 不存在”被 storage 原始异常或空列表误表示；
- list comprehension 是从 storage DTO 到 API model 的一对一映射，不引入额外排序、过滤或副作用；
- `FileListResponse` 是公开 contract 的最后一层，任何 malformed file record 都会在 API boundary 暴露，而不是静默返回任意 dict。[PROJECT FACT]

### 精读 2：T0107 `get_files()` 的聚合接口

```python
metadatas = col.get(include=["metadatas"])["metadatas"]
files: Dict[str, Dict[str, Any]] = {}
for meta in metadatas:
    fid = meta["file_id"]
    if fid not in files:
        # First chunk supplies the denormalized fields
        # (consistent across chunks of the same file_id, SPEC 7.4)
        files[fid] = {
            "file_id": fid,
            "file_name": meta["file_name"],
            "size": meta["file_size"],
            "upload_time": meta["upload_time"],
            "chunk_count": 0,
            "status": meta["ingestion_status"],
        }
    files[fid]["chunk_count"] += 1
return list(files.values())
```

这段代码的 owner 是 storage，不是 T0901；它把多个 chunk metadata records 压成一个 file-level read model。T0901 的学习重点是识别并消费这个既有 contract，而不是在 endpoint 中重新按 `file_id` 聚合一次。[PROJECT FACT]

### 精读 3：`preview_file()`（`backend/app/api/files.py:29-56`）

```python
@router.get(
    "/files/{file_id}/preview", response_model=FilePreviewResponse
)
def preview_file(
    file_id: str,
    collection_name: str = Query(..., description="Target knowledge base name"),
) -> FilePreviewResponse:
    vector_store = ChromaVectorStore()
    if collection_name not in vector_store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    chunks = vector_store.get_chunks_by_file(collection_name, file_id)
    if not chunks:
        raise AppError("FILE_NOT_FOUND")

    ordered_chunks = sorted(chunks, key=lambda chunk: chunk.chunk_index)
    full_content = "\n\n".join(chunk.content for chunk in ordered_chunks)
    preview_content = full_content[: settings.MAX_PREVIEW_CHARS]

    return FilePreviewResponse(
        file_id=file_id,
        file_name=ordered_chunks[0].file_name,
        collection_name=collection_name,
        content=preview_content,
        preview_chars=len(preview_content),
        total_chars=len(full_content),
    )
```

逐行抓住四个 boundary：

- decorator 同时声明 URL pattern 与 response schema；总 router 的 `/api` prefix 仍由 [`main.py:68`](../../backend/app/main.py#L68) 提供。
- path `file_id` 与 query `collection_name` 共同确定资源；collection preflight 先于 file lookup，两个 404 code 不混淆。
- `sorted` → `join` → `len(full_content)` → slice 的顺序很重要：先恢复逻辑顺序，再计算完整长度，最后才限制返回体大小。
- response model 只暴露六个字段；`file_name` 是 display metadata，`file_id` 才是 lookup identity。整个函数没有文件系统、parser、OCR、embedding 或 LLM 调用。[PROJECT FACT]

### 精读 4：`delete_file()`（`backend/app/api/files.py:82-112`）

```python
@router.delete("/files/{file_id}", response_model=FileDeleteResponse)
def delete_file(
    file_id: str,
    collection_name: str = Query(..., description="Target knowledge base name"),
) -> FileDeleteResponse:
    vector_store = ChromaVectorStore()
    if collection_name not in vector_store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    file_record = next(
        (
            record
            for record in vector_store.get_files(collection_name)
            if record["file_id"] == file_id
        ),
        None,
    )
    if file_record is None:
        raise AppError("FILE_NOT_FOUND")

    file_name = file_record["file_name"]
    _delete_raw_file(collection_name, file_name)
    vector_store.delete_by_file(collection_name, file_id)
    invalidate_keyword_index(collection_name)

    return FileDeleteResponse(
        message="文件删除成功",
        file_name=file_name,
        collection_name=collection_name,
    )
```

- `@router.delete(..., response_model=...)` 建立 DELETE path 与公开 response contract；`collection_name` 仍是 query，不是 body。
- `next((record for ...), None)` 表达“首个匹配 record 或没有”；它把 file-level metadata lookup 与后续副作用分开，防止未知 `file_id` 进入 cascade。
- 三个 side-effect call 是显式的编排边界。这里没有 `try/except` 补偿，所以调用顺序需要被测试与文档同时锁定；顺序本身不能提供跨存储原子性。
- `FileDeleteResponse` 不返回 Chroma 的 deleted count，避免把 storage 内部计数扩大成 HTTP contract；`message` 只是人类可读结果，不是可恢复 token。[PROJECT FACT]

### 精读 5：`_delete_raw_file()` 与 `delete_by_file()` 的安全/存储边界

```python
def _delete_raw_file(collection_name: str, file_name: str) -> None:
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    collection_dir = (upload_root / collection_name).resolve()
    target = (collection_dir / file_name).resolve()
    if (
        PureWindowsPath(file_name).name != file_name
        or collection_dir.parent != upload_root
        or target.parent != collection_dir
    ):
        raise AppError("INTERNAL_ERROR")

    target.unlink(missing_ok=True)
```

`resolve()` 把相对路径、`..` 与 symlink 影响纳入比较；`PureWindowsPath(file_name).name != file_name` 拒绝带目录成分的文件名；两个 parent 比较保证 collection 和 target 都没有逃出预期根目录。`missing_ok=True` 让“文件已经不在磁盘”成为幂等删除，而不是把后续 Chroma 清理挡住。[PROJECT FACT]

T0106 的 concrete storage primitive 则只处理向量库：`col.get(where={"file_id": file_id}, include=[])` 先取得匹配 ID 数量，再 `col.delete(where={"file_id": file_id})` 删除同一范围的 chunks、vectors 和 metadata，并返回数量。它不知道 raw file 路径，也不负责 keyword index。[PROJECT FACT]

## 6. 数据流与错误边界

```text
query string
  → FastAPI Query validation
      ├─ missing collection_name → framework validation boundary
      └─ str collection_name
          → list_collections()
              ├─ absent → AppError(COLLECTION_NOT_FOUND) → global handler → 404
              └─ present
                  → get_files(collection)
                      ├─ empty chunks → [] → FileListResponse(files=[])
                      └─ metadata aggregation → file dicts
                          → FileItem.model_validate()
                               ├─ malformed shape → response/model validation error
                               └─ valid items → FileListResponse → 200

path file_id + query collection_name
  → FastAPI path/query validation
      ├─ missing collection_name → framework validation boundary
      └─ (file_id, collection_name)
          → list_collections()
              ├─ absent → AppError(COLLECTION_NOT_FOUND) → global handler → 404
              └─ present
                  → get_chunks_by_file(collection, file_id)
                      ├─ [] → AppError(FILE_NOT_FOUND) → 404
                      └─ ChunkRecord[]
                          → sorted by chunk_index ASC
                          → join content with "\n\n"
                          → full_content
                              ├─ len(full_content) → total_chars
                              └─ [:MAX_PREVIEW_CHARS] → content
                                  → len(content) → preview_chars
                                      → FilePreviewResponse → 200

delete path file_id + query collection_name
  → FastAPI path/query validation
      ├─ missing collection_name → framework validation boundary
      └─ (file_id, collection_name)
          → list_collections()
              ├─ absent → AppError(COLLECTION_NOT_FOUND) → 404; no side effects
              └─ present
                  → get_files(collection)
                      ├─ no matching file_id → AppError(FILE_NOT_FOUND) → 404; no side effects
                      └─ file_name
                          → safe target validation + unlink(missing_ok=True)
                          → delete_by_file(collection, file_id)
                          → invalidate_keyword_index(collection)
                          → FileDeleteResponse → 200
```

### 类型变化

list path 的 `str` query parameter → `List[Dict[str, Any]]` storage DTO → `List[FileItem]` Pydantic models → `FileListResponse`；preview path 的 `file_id`/`collection_name` → `List[ChunkRecord]` → ordered `full_content` → truncated `content` + two length metrics → `FilePreviewResponse`；delete path 的 `file_id`/`collection_name` → file-level record → safe disk unlink → Chroma delete → keyword-index invalidation → `FileDeleteResponse`。关键转换与副作用编排发生在 API boundary，不是 Chroma adapter 里。[PROJECT FACT]

### 三种“没有文件”/资源状态

- collection 不存在：资源 identity 无效，返回 404 `COLLECTION_NOT_FOUND`，并且不能调用 `get_files()`。
- collection 存在但没有 chunks：资源有效，只是 empty state，返回 200 和 `files=[]`。
- collection 存在但 delete/preview 的 `file_id` 没有匹配 chunks/records：返回 404 `FILE_NOT_FOUND`，并且不能执行后续副作用。

这和 Phase 8 的“empty collection vs empty retrieval result”是同一类工程思维：先区分资源状态，再决定 HTTP 语义；不要用一个空数组掩盖资源不存在。[ENGINEERING KNOWLEDGE]

### Preview 的两个长度

`total_chars` 与 `preview_chars` 不是两个不同来源的估算值，而是同一条字符串在两个时点的长度：先把所有 persisted chunk content 拼成 `full_content`，因此 `total_chars = len(full_content)`；再取 `full_content[:MAX_PREVIEW_CHARS]`，因此 `preview_chars = len(returned_content)`。当 `total_chars > preview_chars` 时，consumer 可以提示“已截断”，但不能据此推断原始文件字符数。[PROJECT FACT]

### Preview 的语义边界

preview 是“当前已入库文本的诊断性重建”，不是原始文档的精确还原。chunk overlap 可能出现重复，Markdown heading-path 可能保留前缀；这些都是 ingestion 产物，T0902 有意不做 de-overlap、去重或重新解析。这样可以在不触发 parser/OCR/embedding/LLM 的前提下检查入库结果。[PROJECT FACT]

### Delete 的失败时序

成功路径是 `lookup → disk → Chroma → index`，不是一个跨存储 transaction。磁盘、ChromaDB 或 keyword invalidation 任一步失败，都可能让系统停在部分完成状态；当前全局 handler 只能把未处理异常映射为 500 `INTERNAL_ERROR`，不会自动执行反向补偿。这个风险应由后续工程评审和 T1203 cross-feature verification 明确 owner。[ENGINEERING KNOWLEDGE]

### Delete 的副作用边界

delete 与 list/preview 不同：它会修改三个状态持有者。第一步从 Chroma 的 file-level view 得到 `file_name`，避免客户端控制磁盘路径；第二步 `_delete_raw_file()` 只允许目标解析后仍位于 `uploads/{collection_name}` 的直接子文件，并以 `missing_ok=True` 提供幂等的磁盘删除；第三步 `delete_by_file()` 以 `file_id` 过滤并删除 Chroma chunks、vectors 与 metadata；最后 keyword index 只被标记 dirty，由下一次 search 触发 rebuild。[PROJECT FACT]

当前 route 没有跨存储 transaction 或补偿逻辑：如果磁盘删除成功后 Chroma 删除失败，可能留下“raw file 已删除、chunks 仍存在”的中间状态；如果 index invalidation 失败，检索缓存可能暂时陈旧。全局 handler 会返回 `INTERNAL_ERROR`，但不会把已经发生的副作用自动恢复。这是本 Task 的已知 engineering risk，不应被 3 个 Mocked route tests 掩盖。[ENGINEERING KNOWLEDGE]

## 7. 架构设计：新增能力与刻意保留的边界

### 7.1 新增能力

- **API read boundary**：文件级 metadata 可以通过 `/api/files` 被 HTTP consumer 读取。
- **Contract translation**：storage 的 dynamic dict 通过 `FileItem` / `FileListResponse` 变成稳定 JSON shape。
- **Preflight semantics**：missing collection 在读取数据前映射到统一 404 error envelope。
- **Chunk preview boundary**：`/api/files/{file_id}/preview` 通过 T0108 读取 persisted chunks，按 `chunk_index` 重建并在 5000 字符处截断，同时返回完整/实际长度。[PROJECT FACT]
- **Cascade delete boundary**：`DELETE /api/files/{file_id}` 从 file-level metadata 得到安全的 `file_name`，按固定顺序清理 raw file、ChromaDB file data 与 keyword-index dirty state。[PROJECT FACT]
- **Router composition**：`files_router` 在 [`router.py:4`](../../backend/app/api/router.py#L4) 导入并在 [`router.py:20`](../../backend/app/api/router.py#L20) 注册，随后由 `/api` prefix 对外可见。[PROJECT FACT]

### 7.2 没有改变的边界

- `get_files()` 仍然是 Chroma chunk metadata 的派生聚合，不新增 external metadata store。
- list/preview endpoint 不知道 `uploads/` 的磁盘结构，不重解析原始文件，不触碰 Chroma private API；delete 只通过受 guard 保护的 helper 触碰目标文件。
- T0901/T0902 是只读；T0903 是唯一会触发文件系统、Chroma file data 和 keyword-index 状态变化的 Phase 9 route。[PROJECT FACT]
- file identity 仍是 `file_id`；`file_name` 不承担 lookup 或 uniqueness contract。
- T0902 的 reconstruction/truncate 与 T0903 的 cascade cleanup 已完成；de-overlap、原始文件精确渲染、batch/undo、跨存储 transaction 与 compensation 仍不属于当前 slice。[PROJECT FACT]

### 7.3 简短 engineering implication

列表、preview 与 delete endpoint 看起来都很薄，但它们把容易漂移的来源固定成三条明确路径：collection existence 由 storage public method 判断，列表 records 由 `get_files()` 派生，preview text 由 `get_chunks_by_file()` 派生，delete 的 file identity 由同一 file-level view 确认，HTTP shape 由 Pydantic model 锁定。代价是 list 需要全量 metadata aggregation，preview 需要读取并拼接该文件的所有 chunks，delete 需要跨 filesystem/Chroma/index 编排；分页、索引化、精确重构、transaction 或 metadata database 都属于独立的后续 engineering decision。[ENGINEERING KNOWLEDGE]

## 8. Engineering Review 摘要

Phase 9 Engineering Review 已独立完成；本节不复制完整 ADR，详细 failure taxonomy、规模分析与 Known Gaps 见 [工程评审](./engineering-review/phase-09-engineering-review.md)。T0901/T0902/T0903 的短结论有六点：

1. **Single source of truth**：从 chunk metadata 派生列表，避免 `uploads/` 目录与 Chroma 状态漂移；FAILED ingestion 没有 chunks，因此自然不出现在列表。
2. **Defense in depth**：API 先做 collection existence check，随后用 `FileItem` 和 `FileListResponse` 做 shape validation；两层分别解决 resource identity 与 payload shape。
3. **Read amplification boundary**：`get_files()` 是全量 metadata aggregation，没有分页或独立索引。当前是 v1 明确的 trade-off，不应在 T0901 学习文档中擅自改成性能优化方案。[PROJECT FACT]
4. **Diagnostic preview boundary**：T0902 读取并拼接完整 persisted chunks，再做 5000 字符 slice；这能验证入库文本，但 overlap/heading artifacts 与原始文件字符数差异是有意保留的语义，不是 preview bug。若消费方需要精确渲染或分页，应另行建立 contract。[PROJECT FACT]
5. **Cascade scope boundary**：T0903 以 `(collection_name, file_id)` 找到 file_name，再清理 raw file、ChromaDB file data 和 keyword-index dirty state；客户端不能直接决定路径或删除范围。[PROJECT FACT]
6. **Partial-failure risk**：三个目标没有共享 transaction，当前 route 也没有 compensation。固定顺序使行为可预测，但不保证中途失败后零残留；需要真实 integration/failure testing 与独立 engineering owner。[ENGINEERING KNOWLEDGE]

## 9. Technical Decision（技术决策速查）

| 决策 | 备选 | 选择理由 | 代价 / 边界 |
|---|---|---|---|
| 先 `list_collections()` 再 `get_files()` | 直接调用 `get_files()`，让 storage 异常决定 404 | 明确区分 missing resource 与 empty collection，并保证 missing 时不读文件 | 每次请求多一次 public read |
| 文件列表信任 `get_files()` | 扫 `uploads/{collection}` 目录 | 与 SPEC 7.3 一致，避免磁盘残留、失败回滚窗口和 Chroma 状态漂移 | 每次全量扫描 chunk metadata |
| `FileItem` + `FileListResponse` | 原样返回 dict | API 出口有明确字段、类型和 response serialization contract | malformed record 会在 boundary 失败 |
| empty collection 返回 200 `files=[]` | 404 或特殊 error code | empty 是有效资源状态，符合 F016 AC-F016-03 | consumer 需要区分空数组与 error envelope |
| endpoint 每次创建 `ChromaVectorStore` | 共享 global store 或直接暴露 client | 遵守现有 adapter boundary，避免请求间共享可变 SDK 对象 | client lifecycle / connection reuse 仍是后续工程问题 |
| preview 从 persisted chunks 重建 | 重新读取并解析 `uploads/` 原始文件 | 与 F016 的“当前已入库文本”语义一致，避免 parser/OCR/embedding/LLM 与磁盘状态漂移 | 不是原始文档的精确还原，overlap/heading artifacts 会保留 |
| API 对 chunks 做 defensive `chunk_index` sort | 完全信任 storage 返回顺序 | route contract 独立于 mock、替代 adapter 或未来 storage 实现 | 多一次 O(n log n) 排序；n 是该文件 chunks 数 |
| 先算 `total_chars` 再 slice `content` | 截断后再估算总长度 | consumer 能判断是否截断，且 `preview_chars == len(content)` | `total_chars` 不是原始文件字符数 |
| 以 `(collection_name, file_id)` 定位 preview | 以 `file_name` 定位 | file_id 是稳定 identity，collection 提供隔离边界 | consumer 必须同时提供 path 与 query 参数 |
| delete 先从 `get_files()` 查 file_name | 直接拼接客户端提供的 file_name | 客户端只提交稳定 file_id；服务端从 persisted metadata 得到 display name，降低路径注入风险 | 依赖 file-level metadata 尚未损坏 |
| 删除顺序为 disk → Chroma → keyword dirty mark | 任意顺序或先 invalidate | 与 T0903 contract 一致且容易在 route test 中观察；最后才让旧检索索引失效 | 无跨存储 transaction；中途失败可能留下 residual state |
| `Path.resolve()` + parent checks + `missing_ok=True` | 直接 `Path(UPLOAD_DIR) / name / file_name` 后 unlink | 防止 traversal/absolute/symlink 越界，同时让重复删除磁盘目标幂等 | 当前没有专门的 path-safety/compensation test |
| 不提供 batch delete / undo | 扩展为批量或回收站 API | 遵守 T0903 scope 与 F016 irreversible contract | 用户误删后的恢复需另立产品/存储设计 |

## 10. Interview Notes（Task 候选；完整 Phase 9 话术见 Interview Guide）

1. 为什么文件列表是从 chunk metadata “算出来的”，而不是查询 FileRecord table？
2. `file_id`、`file_name`、`chunk_index` 分别承担什么角色？
3. 为什么 missing collection 必须在 `get_files()` 前返回 404，而 empty collection 返回 200？
4. `FileItem.model_validate()` 与 `response_model=FileListResponse` 各自保护哪一层 contract？
5. 三个 `FileListEndpointTests` 为什么是 route-level Mocked evidence，不是 concrete Chroma E2E？
6. 如果未来加入文件排序或 pagination，应先修改哪个 SPEC/API contract，而不是直接改列表推导式？
7. T0902 为什么使用 `(collection_name, file_id)`，而不是 `file_name`？
8. `total_chars` 与 `preview_chars` 分别在哪个时点计算？为什么不能把 `total_chars` 当成原始文件长度？
9. 为什么 T0902 要保留 chunk overlap 与 heading-path artifacts，而不在 preview endpoint 中“修复”？
10. 4 个 T0902 Mocked tests 分别覆盖什么边界？它们还缺少哪一种 concrete integration evidence？
11. T0903 为什么先用 `get_files()` 找到 `file_name`，再调用 `delete_by_file()`？
12. `_delete_raw_file()` 的 `resolve()`、父目录比较和 `PureWindowsPath(...).name` 各自防什么问题？
13. 为什么 keyword index 是 dirty mark，而不是在 DELETE request 内立即 rebuild？
14. 如果磁盘 unlink 成功但 Chroma 删除失败，当前系统可能处于什么 residual state？如何验证或补偿？
15. 三个 T0903 route-level Mocked tests 能证明什么、不能证明什么？

## 11. Future Improvement（Future / Not implemented in v1）

| 方向 | 当前边界 | 状态 / owner |
|---|---|---|
| Chunk-based file preview | 已从 `get_chunks_by_file()` 按 `chunk_index` 拼接，最多 5000 字符，不重解析原文件；这是诊断性 preview，overlap/heading artifacts 可能保留 | `[PROJECT FACT]`，T0902 DONE |
| Cascade file delete | 已按 `file_id` 删除 raw file、Chroma chunks/vectors/metadata，并 invalidate keyword index；操作不可逆 | `[PROJECT FACT]`，T0903 DONE |
| Cross-feature verification | upload → list → preview → delete → re-upload、跨 KB 隔离、安全路径验证 | `[FUTURE]`，T1203 |
| Pagination / sorting contract | 当前无分页，文件顺序不构成独立 API contract | `[FUTURE]`，需先更新 SPEC/API 设计 |
| Metadata read amplification | 每次 `get_files()` 全量读取 chunk metadata | `[FUTURE]`，规模证据出现后再评估索引或 metadata store |
| Frontend File Manager | 当前只有 HTTP list slice，没有列表 UI、loading/empty/error 状态 | `[FUTURE]`，Phase 10–11 |
| Mid-cascade failure / compensation | 磁盘、ChromaDB、keyword index 之间没有共享 transaction；当前 route 不做自动补偿 | `[FUTURE]`，需独立 Engineering Review / T1203 证据 |

## 12. Phase Learning Review 收口（2026-09-04）

### 12.1 Review 前提与 Phase mental model

Phase 9 的三个 Task 已完成独立 Task Learning Pass，且 Phase Gate Review 给出 **`PHASE_9_PASS — READY_FOR_PHASE_10`**。本次 Learning Review 不重新定义 API，也不把 Gate 的验证证据升级成更强的 E2E 证据；它的作用是把三个相邻 slice 收束成一个可迁移的 mental model。[PROJECT FACT]

最适合记忆 Phase 9 的主线是：**Identity → Projection → Orchestration**。

- **Identity**：`(collection_name, file_id)` 是资源 identity；`file_name` 是服务端从 persisted metadata 得到的 display/path value，客户端不能用它决定删除范围。
- **Projection**：T0901 把 chunk metadata 投影成 `FileItem` 列表；T0902 把 persisted `ChunkRecord` 投影成诊断性 preview。两个 endpoint 都读取 storage 的 public API，不暴露 Chroma private object。
- **Orchestration**：T0903 先做 collection/file preflight，再按 raw file → ChromaDB → keyword-index dirty mark 的固定顺序完成不可逆清理；三个目标没有共享 transaction。[PROJECT FACT]

这条主线可以用 TypeScript/Node 的类比理解：T0901/T0902 类似把 repository record 映射成稳定的 DTO，T0903 则像一个明确声明副作用顺序的 service command。`interface` 只能描述 shape，不能自动保证 runtime validation、filesystem safety 或跨存储 rollback；这些仍要由 Pydantic、path guard 与 orchestration policy 分别承担。[ENGINEERING KNOWLEDGE]

### 12.2 跨 Task data flow

```text
(collection_name, file_id)
          │
          ▼
  collection preflight: list_collections()
          │
    ┌─────┼───────────────────────────────┐
    │     │                               │
    ▼     ▼                               ▼
 T0901  T0902                           T0903
 list   preview                          delete
    │     │                               │
 get_files()  get_chunks_by_file()       get_files() → file_name
    │     │                               │              │
 file_id     chunk_index sort             │       safe raw-file unlink
 aggregation → join → total/slice         │              │
    │     │                               └──────→ delete_by_file()
    ▼     ▼                                             │
 FileItem / FilePreviewResponse                         └→ keyword dirty mark
    │     │                                                        │
    └─────┴────────────── typed HTTP response                      ▼
                 (delete returns FileDeleteResponse)
```

跨 Task 的不变量有四个：

1. missing collection 必须在 `get_files()` / `get_chunks_by_file()` 以及所有 delete side effect 之前被拦截；
2. existing-but-empty collection 是有效资源，list 返回 200 和 `files=[]`；
3. preview 的 `total_chars` 是完整 persisted join 的长度，`preview_chars` 是 slice 后实际返回内容长度；
4. missing file 必须在磁盘删除前返回 `FILE_NOT_FOUND`，但 raw file 已经被外部手动删除并不等同于 API 层的 missing file。[PROJECT FACT]

### 12.3 Ownership 与 boundary consolidation

| Boundary | 当前 owner | Phase 9 review 后应记住的 contract |
|---|---|---|
| Persisted chunk metadata | `VectorStore.get_files()` | 是 file list 的 source of truth；按 `file_id` 聚合，不扫描 `uploads/` |
| Persisted chunk content | `VectorStore.get_chunks_by_file()` | 是 preview 的 source of truth；按 `chunk_index` 防御性排序后拼接 |
| HTTP resource boundary | `files.py` + Pydantic schemas | 负责 query/path binding、preflight、错误映射、DTO 组装与 response serialization |
| Raw filesystem | `_delete_raw_file()` | 只允许落在 collection upload root 内的安全目标；使用 `file_id` 查出的 `file_name`，不是客户端任意 path |
| Vector/metadata cleanup | `VectorStore.delete_by_file()` | 以 `where={file_id}` 删除目标 file 的 Chroma data，并保留先数后删等 storage contract |
| Keyword retrieval cache | `invalidate_keyword_index()` | DELETE 后标记 dirty，由后续 query lazy rebuild；不在 DELETE request 内同步重建 |
| Frontend file manager | Phase 10–11 | 目前是 future consumer；loading/empty/error/rendering contract 尚未建立 |

因此，Phase 9 不是“又加了三个薄 route”，而是把 file lifecycle 的后三个状态转换显式化：**metadata view、persisted-content view、cross-store cleanup command**。这样读路径和写路径共用 `file_id` identity，但各自拥有不同的 source of truth 与 failure boundary。[ENGINEERING KNOWLEDGE]

### 12.4 当前验证证据与诚实边界

本次收口采用以下证据分层：

- **MOCKED**：T0901 3 个、T0902 4 个、T0903 3 个 route-level tests，共 10/10 focused tests；它们证明 FastAPI wiring、Pydantic response shape、preflight、错误映射、preview reconstruction/truncation 与 delete side-effect order，不证明真实三存储贯通。
- **PROJECT-WIDE**：backend full unittest discovery 为 **78/78 PASS**；`compileall` 通过。全量通过说明当前 checkout 的测试集合没有回归，但不改变单项测试的 Mocked 性质。
- **SUBSTITUTED**：Gate Review 另有一次 concrete smoke，使用真实 FastAPI route、真实 ChromaDB、真实 filesystem 与真实 keyword index，但通过手工写入 persisted chunks 构造 fixture；它证明 list/preview/delete 在已持久化数据上的 concrete seam 和清理结果，不是 literal upload → parse → embed → ingest → list → preview → delete → re-upload E2E。
- **NOT_AVAILABLE**：当前环境没有 `pytest` 模块，因此没有把 pytest 当作通过证据，也没有临时安装依赖。
- **DEFERRED**：T1203 继续负责跨 feature upload→list→preview→delete→re-upload、path traversal/absolute/symlink、cross-KB isolation 与更完整的删除验证；mid-cascade compensation 仍是 future engineering work。[PROJECT FACT]

“真实”在这里必须拆开说：`SUBSTITUTED` smoke 比纯 route mock 更接近 concrete storage，但它仍然绕过了 upload/ingestion pipeline；这正是 evidence label 要防止的 overclaim。[ENGINEERING KNOWLEDGE]

### 12.5 文档与面试素材的收口方式

- 本文第 4 节保留 T0901/T0902/T0903 的 code reading、Task-level verification 和短候选题，方便按 Task 回看实现。
- 本节提供跨 Task 的统一 mental model、ownership、failure boundary 与证据分类，避免在三个 Task 中重复同一套 Phase 级解释。
- [Interview Guide](./interview-notes/dx-rag-interview-guide.md) 新增 Phase 9 深度章，承载 30 秒回答、1–2 分钟 data flow、高频追问和诚实边界；本文不生成 STAR，因为当前没有已闭环 incident。[PROJECT FACT]
- Phase 9 Engineering Review 已独立完成；本文不复制其 ADR、failure taxonomy、规模分析或 compensation decision，详见 [工程评审](./engineering-review/phase-09-engineering-review.md)。[PROJECT FACT]

### 12.6 Phase-level self-test chain

按下面的顺序自测，必须能从一个 HTTP request 讲到 storage side effect，并在每一步标出证据等级：

| Step | 自测问题 | 应答关键词 |
|---|---|---|
| 1. Identity | 为什么 list、preview、delete 都使用 `collection_name + file_id`，而不是客户端 `file_name`？ | namespace isolation、stable identity、display-only filename |
| 2. List | collection 存在但没有 chunks 时，为什么是 200 `files=[]`？ | valid empty resource，不等同于 missing collection |
| 3. Preview | chunks 返回 `[2, 0, 1]` 且总拼接超过 5000 字符时，哪些字段先计算、哪些内容被截断？ | defensive sort、full `total_chars`、slice、`preview_chars` |
| 4. Delete preflight | file 不存在时，为什么 raw unlink、Chroma delete、keyword invalidation 都不能发生？ | lookup before side effect、`FILE_NOT_FOUND` |
| 5. Delete order | 磁盘、Chroma、keyword index 的顺序是什么？为什么最后只 dirty mark？ | predictable irreversible order、lazy rebuild |
| 6. Failure | Chroma 删除在磁盘 unlink 后失败，当前系统可能留下什么？ | residual state、no shared transaction、compensation deferred |
| 7. Evidence | 10/10 route tests 与 concrete smoke 各自证明什么？ | MOCKED vs SUBSTITUTED；都不是 upload-to-reupload E2E |

如果能同时回答这 7 步，说明掌握的不是三个 endpoint 的记忆，而是 Phase 9 的 resource identity、read projection、write orchestration 与 evidence discipline。[ENGINEERING KNOWLEDGE]

### 12.7 收口结论

Phase 9 Learning Review 完成。当前可对外准确表述为：**文件列表、persisted-chunk preview、按 `file_id` 的级联删除 API 已实现并通过 Phase Gate；路由级 contract 与一条绕过 ingestion 的 concrete substituted smoke 已验证；完整跨 feature E2E、路径安全矩阵、跨 KB 隔离和 partial-failure compensation 仍由 T1203 / 后续 engineering decision 负责。**[PROJECT FACT]

## 自测题与动手练习

### Concept

1. T0901 的唯一 source of truth 是什么？为什么不是 `uploads/` 目录？
2. `file_id` 去重如何让多个 chunks 变成一条 FileItem？`chunk_count` 在哪一层累计？
3. `size` 与 `status` 为什么不是 storage metadata 的原始字段名？

### Code reading / behavior prediction

4. `list_collections()` 返回 `[]` 时，`get_files()` 是否会被调用？HTTP status 和 error code 是什么？
5. `list_collections()` 返回 `['test-kb']`、`get_files()` 返回 `[]` 时，响应 body 是什么？
6. storage 返回 3 条 file dict 时，哪一层保证每条包含六个 FileItem 字段？
7. `collection_name` 缺失时，代码会进入 `ChromaVectorStore()` 吗？为什么？

### Design reasoning

8. 如果把 `list_collections()` 检查删掉，missing collection 与 empty collection 可能在哪里混淆？
9. 如果 endpoint 直接返回 `vector_store.get_files()`，会失去哪些 response contract？
10. 如果产品还要求原始 PDF 的精确页面渲染，为什么不能直接把 T0902 的 `content` 当成 renderer 输入？

### T0902 Preview

11. `file_id` 和 `collection_name` 分别来自 URL 的哪一部分？两者为什么必须同时参与 lookup？
12. chunks 以 `[2, 0, 1]` 顺序返回时，`sorted(..., key=lambda chunk: chunk.chunk_index)` 后的拼接顺序是什么？
13. 两个 3000 字符 chunks 以 `\n\n` 拼接后，`total_chars` 为什么是 6002，而 `preview_chars` 是 5000？
14. 如果 `get_chunks_by_file()` 返回 `[]`，为什么是 `FILE_NOT_FOUND`，而不是 200 空 preview？
15. preview 逻辑是否会调用 parser、OCR、embedding model、LLM 或读取 `uploads/`？从代码哪一段可以证明？
16. 为什么 T0108 已经声称返回升序 chunks，T0902 仍要再次排序？

### T0903 Cascade Delete

17. `delete_file()` 为什么必须先从 `get_files()` 找到 `file_name`，而不是直接使用客户端输入？
18. collection 不存在、file_id 不存在、raw file 已经不存在，三种情况分别如何处理？
19. `_delete_raw_file()` 的 `PureWindowsPath(file_name).name` 与 `Path.resolve()`/parent checks 如何共同阻止路径越界？
20. `delete_by_file()` 删除 ChromaDB 的哪些对象？为什么 keyword index 不在同一方法里直接 rebuild？
21. 当前实现的成功顺序是什么？如果磁盘 unlink 成功但 Chroma 删除失败，会有什么 residual state？
22. 3 个 T0903 route-level Mocked tests 覆盖了哪些行为？哪一条真实三存储证据仍然缺失？

### 小型练习（不修改产品代码）

用 TypeScript `Map<string, FileItem>` 或 Python `dict` 手算 5 条 chunk metadata：其中 3 条属于 `file-a`、2 条属于 `file-b`。先得到两个 `chunk_count`，再把它们映射为 T0901 的六字段 FileItem。再为 `file-a` 准备 3 个乱序 `ChunkRecord`，手算排序、`\n\n` 拼接、`total_chars` 与 5000 字符 slice。最后为其中一个 file 画出 delete 前后三个目标的状态，并分别模拟：

- existing collection + `[]`；
- missing collection；
- 一个字段缺失的 malformed record。
- preview collection 不存在与 file_id 不存在。
- delete collection 不存在、file_id 不存在、raw file 已被手动删除。
- Chroma 删除失败或 keyword invalidation 失败的 mid-cascade 情况（只推演 residual state，不连接真实存储）。

预测每种情况在哪个 boundary 被处理，并对照 `FileListEndpointTests` 的 Mocked evidence；不要连接真实 Chroma、模型或上传目录。[PROJECT FACT]

## Quick Review

```text
Phase 9 read model
  List input  GET /api/files?collection_name=xxx
  List path   preflight → get_files() → file_id aggregation → FileItem → 200
  Preview     GET /api/files/{file_id}/preview?collection_name=xxx
  Preview path preflight → get_chunks_by_file() → chunk_index sort → join → slice → 200
  Delete      DELETE /api/files/{file_id}?collection_name=xxx
  Delete path preflight → get_files() → safe unlink → Chroma delete → index dirty mark → 200
  Errors      missing collection => 404 COLLECTION_NOT_FOUND
              missing file_id    => 404 FILE_NOT_FOUND
              existing empty KB  => list 200 with files=[]
  Identity    (collection_name, file_id); file_name is display-only
  Lengths     total_chars = full persisted join; preview_chars = returned content length
  Semantics   diagnostic persisted-chunk view; overlap/heading artifacts may remain
  Ownership   storage reads/deletes; API validates/assembles/orchestrates/serializes
  Evidence    3 list + 4 preview + 3 delete route-level MOCKED tests; one concrete SUBSTITUTED smoke with real FastAPI/Chroma/filesystem/keyword; no upload-to-reupload E2E
  Semantics   delete is irreversible; keyword index invalidation marks dirty for next rebuild
  Deferred    cross-feature E2E (T1203), path-safety/failure compensation tests, pagination/UI, exact rendering
```

> **T0901 Learning Pass 记录（2026-09-03）**：本章记录了 `GET /api/files` 的 route contract、collection preflight、T0107 派生 file view、Pydantic response boundary、router registration、empty/missing distinction 与 3 个 route-level Mocked tests。
>
> **T0902 Learning Pass 记录（2026-09-03）**：本章新增 `GET /api/files/{file_id}/preview` 的 path/query contract、T0108 `ChunkRecord` 消费、chunk 顺序重建、`\n\n` 拼接、5000 字符截断、`total_chars`/`preview_chars` 语义、`COLLECTION_NOT_FOUND`/`FILE_NOT_FOUND` 边界与 4 个 route-level Mocked tests。该条记录只描述 T0902 pass 当时的边界；当时 T0903、Phase 9 Gate Review、Phase 9 Learning Review、真实 upload → ChromaDB → list/preview integration 与前端消费仍未执行或未完成，后续 T0903 增量见本章 4.7。[PROJECT FACT]
>
> **T0903 Learning Pass 记录（2026-09-03）**：本章新增 `DELETE /api/files/{file_id}` 的 identity/lookup contract、raw-file path guard、磁盘 → ChromaDB → keyword-index 的级联顺序、不可逆与 partial-failure 风险、`COLLECTION_NOT_FOUND`/`FILE_NOT_FOUND` no-side-effect 边界和 3 个 route-level Mocked tests。三个 Task 已 DONE；Phase 9 Gate Review、Phase 9 Learning Review、真实 upload → list → preview → delete → query E2E、路径安全与补偿测试仍未收口。[PROJECT FACT]
