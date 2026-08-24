# Phase 1 Engineering Review — VectorStore Foundation

> 配套学习笔记：[phase-01-vectorstore.md](../phase-01-vectorstore.md)（逐行精读、TS 类比、11 方法学习地图）
> 本文档定位：**工程决策复盘**。所有结论基于真实代码（`backend/app/core/vector_store.py`，495 行）与 SPEC v1.5 / TASKS.md。
> 诚实状态声明：T0101–T0108 全部 DONE。**已知缺口**：`rename_collection` 当前仅完成 collection 级 rename，SPEC v1.5 要求的 metadata 级联由 T0402（Phase 4）在 VectorStore 内部补全（见 TASKS.md T0103/T0402 备注）。

---

## 1. Phase 定位

| 维度 | 内容 |
|------|------|
| **业务目标** | 让知识"存得进、取得出"：一个知识库 = 一个独立的向量数据集合 |
| **技术目标** | 用 ABC 抽象固化 11 个方法的 VectorStore 公共契约，提供 ChromaDB 实现，把"存储细节"关进实现类 |
| **系统位置** | 数据层地基。上游只依赖 Phase 0（config 的 `CHROMA_PERSIST_DIR`、errors 的 `AppError`）；下游被 Ingest（写）、Retriever（读）、File/KB API（管理）三方消费 |
| **上游依赖** | Phase 0：`settings.CHROMA_PERSIST_DIR`、`AppError("COLLECTION_NOT_FOUND")`、`ChunkRecord` 相关数据模型 |
| **下游消费者** | Phase 3 Ingest（`add_texts`/`delete_by_file` —— 已实际发生）、Phase 4 KB API（collection CRUD + rename）、Phase 6 Keyword Retriever（`list_chunks`）、Phase 7 Vector Retriever（`search`）、Phase 9 File API（`get_files`/`get_chunks_by_file`/`delete_by_file`） |

**一句话**：Phase 1 是 RAG 的"仓库层"——没有它，Embedding 产出的向量无处安放，检索无从谈起。

---

## 2. 为什么需要这个模块？

**没有 VectorStore，系统会出现什么问题：**

1. **无法持久化知识**：Ingest 管道解析、切分、嵌入的成果（chunks + vectors）没有一个统一的地方写入——每次查询都得现算 embedding？知识库"库"字就不成立了。
2. **无法检索知识**：QA 服务需要按语义相似度取 top-k 个 chunk，没有 `search()` 就没有 RAG 的 "R"。
3. **ChromaDB 会被到处直接调用**：每个用到向量的模块自己 `chromadb.PersistentClient(...)`、自己 `get_collection(...).query(...)`——ChromaDB 的 API 细节（distance 语义、`_collection` 对象、metadata 查询语法）泄漏到业务层。换 Milvus 时，全项目每个调用点都要改。
4. **没有身份体系的数据落点**：`chunk_id`/`file_id` 的元数据如果各写各的，删除文件、合并去重、来源引用全部无法可靠工作。

特别地，**没有 distance→similarity 转换边界**这一条：ChromaDB 返回的原始分数是 **distance**（越小越相似，L2 距离可到几十），如果直接透传给上层，Hybrid Retrieval 的加权融合公式（`kw*0.3 + vec*0.7`）会把"分数越大越相关"的关键词分数和"越小越相关"的距离混在一起——**融合直接算错**。

---

## 3. 核心设计决策

### 决策 1：VectorStore ABC —— 用抽象类固化 11 方法公共契约

**Decision**: `class VectorStore(ABC)` 定义 11 个 `@abstractmethod`，`ChromaVectorStore(VectorStore)` 提供实现。业务代码只对着 ABC 编程。

**Context**: SPEC F008 设计约束 2-4：所有 ChromaDB 操作必须走公共接口；禁止外部访问 `_collection`；"VectorStore abstraction 为未来 Milvus 扩展保留接口一致性"。Milvus 明确 Out of Scope（Section 2.5）。

**Problem**: 直接使用 ChromaDB 会让存储实现与业务逻辑焊死。将来 SPEC 允许 Milvus 时（企业级数据量），每个 `chromadb.xxx()` 调用点都是迁移成本。

**Chosen Solution**: Python ABC 固化方法签名（名称、参数、返回值类型），实现类隔离 ChromaDB 细节。文档字符串直接引用 SPEC 条款（"Implementations MUST: Convert raw distance → similarity_score"）。

**Why**: ① **接口即契约**：11 个方法的签名与 SPEC F008 Public Interface 表逐行对齐，SPEC 和代码互相锁定；② **迁移成本前置化**：未来 Milvus 实现只需写第二个子类 `MilvusVectorStore(VectorStore)`，业务代码零改动（这就是为明确未来需求留的"付费扩展点"——SPEC 虽冻结 Milvus，但明确保留此扩展点）；③ Python 的 ABC 在运行时强制子类实现全部方法，漏写一个会实例化失败——抽象契约自我执行。类比 TypeScript：ABC ≈ `abstract class`/`interface`（但 Python 靠运行时检查，TS 靠编译期）。

**Trade-off**: 抽象层增加间接性——找实现要跳一层；ABC 的 docstring 与实现类 docstring 存在重复。**当前项目没有第二个实现类**，抽象是"纯成本"（YAGNI 的争议点）——但 SPEC 把它列为设计约束而非可选项，且这是面试/工程讨论的经典决策点。

**Future Improvement**（Future / Not implemented in v1）: Milvus 实现（SPEC 2.5 明确 defer）；工厂/依赖注入选择实现（当前直接实例化 `ChromaVectorStore()`）。

---

### 决策 2：一个 Knowledge Base = 一个 ChromaDB Collection

**Decision**: 知识库隔离的物理模型：collection 即 KB，`uploads/{kb_name}/` 目录配套。collection 名即 KB 名（3-50 字符校验）。

**Context**: SPEC F001：用户按主题隔离文档集合；SPEC 10.6：KB 隔离（独立 collection + 独立目录，无跨库访问）。

**Problem**: 多 KB 场景下数据如何隔离？选项：① 单 collection + metadata 字段区分 KB；② 每 KB 一个 collection。选项①查询时要带 where 过滤（每次检索都过滤、误写进别的 KB 无法物理隔离）；选项②检索天然只扫本 KB 的数据。

**Chosen Solution**: 每 KB 一个 collection（`create_collection(name)`），cosine 度量 + HNSW 索引，metadata `{"hnsw:space": "cosine"}`。

**Why**: ① **查询性能**：检索不需要 where 过滤，HNSW 图只包含本 KB 向量；② **删除语义简单**：删 KB = `delete_collection(name)` 一条调用（级联目录删除在 Phase 4）；③ **权限边界即物理边界**：无跨 collection 数据访问（SPEC 10.6）。类比：单表 + `tenant_id` 列 vs 每租户独立 database schema——v1 数据量下选后者换简单和隔离。

**Trade-off**: ① collection 数量随 KB 数量线性增长，ChromaDB 管理大量小 collection 的开销；② **跨 KB 检索不可能**（也是 SPEC 想要的隔离）；③ 无跨库去重/共享文档。

**Future Improvement**（Future / Not implemented in v1）: 多租户大规模时可能改为"大 collection + partition/metadata 分区"（Milvus partition key），但 SPEC 冻结了 v1 语义，这是未来产品决策。

---

### 决策 3：distance → similarity 语义边界（clamp(1.0 − raw_distance)）

**Decision**: ChromaDB 原始 distance **不允许**离开 `search()` 方法；对外只返回 `similarity_score = max(0.0, min(1.0, 1.0 - distance))`，并按降序排序。

**Context**: SPEC F008 的核心契约之一。ChromaDB `query()` 返回 distances（cosine space 下越小越相似）；而 Keyword Retrieval 的 `keyword_score` 语义是"越大越相关 [0,1]"。Hybrid 融合公式需要两个分数**同向、同尺度**。

**Problem**: 若把 raw distance 透传：① 上层拿到的是"距离"而非"相似度"，语义相反；② distance 的范围无界（cosine distance 理论 [0,2]），无法与 [0,1] 的 keyword_score 加权；③ 每个上层调用方都得自己写转换——写错的概率 ×N，且 v1.4 明确禁止上层二次 min-max 归一化。

**Chosen Solution**: 转换收口在 `VectorStore.search()` 内部（`max(0.0, min(1.0, 1.0 - distance))` 即 clamp 到 [0,1]），返回 `VectorSearchResult.similarity_score`。SPEC v1.4 固化分数分层：`similarity_score`（VectorStore 输出）→ `vector_score`（VectorRetriever 直用）→ `final_score`（Hybrid）→ `relevance_score`（API）。**每一层只改名字不改值**。

**Why**: ① **语义边界**：存储层不懂业务（距离），业务层不懂存储（相似度）——转换发生在边界上，符合分层原则；② **融合可计算**：kw 和 vec 都 [0,1] 且同向，加权公式才有意义；③ 单点实现，全系统一致。

**Trade-off**: `1.0 - distance` 对 cosine distance 是**近似线性映射**，不是严格数学上的余弦相似度——ChromaDB 文档也指出 raw distance 不保证等于 cosine similarity 的补数。但对排序和融合来说单调性保留即可（v1 无需精确相似度数值，只需相对排序 + 可比较的尺度）。这是**工程近似**，SPEC 已把它固化为契约。

**Future Improvement**（Future / Not implemented in v1）: 若未来需要精确 cosine similarity，可在 ChromaDB 配置或查询方式上调整（如直接取 embeddings 计算）——但会破坏当前边界，需 SPEC 决策。

---

### 决策 4：chunk_id 即 ChromaDB document id（身份体系前置）

**Decision**: `add_texts` 以 metadata 里的 `chunk_id`（UUID4）作为 ChromaDB 的 document id；`chunk_index` 只是文件内顺序号，永远不充当身份。

**Context**: SPEC 7.1 身份规则：`chunk_id` = 不可变全局唯一（UUID4）；`file_id` = 文件身份；`file_name` = 仅显示；`chunk_index` = 仅排序。CLAUDE.md 将其列为**不可违反的 Identity Rules**。

**Problem**: 常见错误设计是 `file_name:chunk_index` 当 ID——但文件删除后重传、KB 重命名都会导致身份漂移；Hybrid merge 按 ID 去重、source citation 引用 chunk、delete_by_file 按 file_id 删除，全部依赖稳定身份。

**Chosen Solution**: 写入时 `ids = [meta["chunk_id"] for meta in metadatas]`（vector_store.py:331），Chromium 内部主键 = 我们的业务 ID。file 级身份靠 metadata 里的 `file_id` 字段 + `where={"file_id": ...}` 查询。

**Why**: ① **零映射层**：业务 chunk_id 与存储 id 一一对应，不需要额外的"存储 ID → 业务 ID"映射表（v1 禁止外部 metadata DB——SQLite 等 Out of Scope）；② **引用稳定**：retrieval 结果、sources 数组里的 chunk_id 直接可用作删除/预览的 key；③ **delete_by_file 简单**：`col.delete(where={"file_id": file_id})` 一条调用。

**Trade-off**: ① 依赖调用方（Ingest）正确生成 UUID——`add_texts` 自己不生成、不校验（T0104 scope 明确：caller provides）；② ChromaDB where 过滤走 metadata，性能依赖 ChromaDB 的 metadata 索引实现（万级 chunk 可接受）。

**Future Improvement**（Future / Not implemented in v1）: 大量文件时 where 过滤的性能需 ChromaDB/Milvus 层面的索引优化评估。

---

### 决策 5：Metadata Denormalization —— 文件级字段冗余到每个 chunk

**Decision**: `file_size`/`upload_time`/`ingestion_status` 三个文件级字段**冗余存储**在该文件每个 chunk 的 metadata 中；`get_files()` 通过 `file_id` group/dedup 聚合出文件列表。**不引入** SQLite/PostgreSQL/Redis 元数据库。

**Context**: SPEC 7.3 Persistence Strategy："v1 不引入任何 metadata database"，FileRecord 由 chunk metadata 聚合而成。v1 明确 Out of Scope：SQLite/PostgreSQL/Redis（CLAUDE.md 表格）。

**Problem**: 文件列表 API（Phase 9）需要 FileRecord（file_id/name/size/time/chunk_count/status）。没有元数据库，这些信息从哪来？选项：① 扫描 uploads/ 文件系统（拿不到 chunk_count/status，且与 ChromaDB 状态可能不一致）；② 单独维护 JSON 文件（新增一致性负担）；③ 冗余到 chunk metadata。

**Chosen Solution**: 方案③ + 一致性约束："同一个 file_id 的所有 chunks 的 file_size/upload_time/ingestion_status 必须一致"（写入侧由 Ingest 保证——同一批 chunks 用同一组值）。`get_files()` 遍历 collection 的 metadata，按 file_id 聚合，取第一条的冗余字段 + 计数 chunk_count。

**Why**: ① **单一存储引擎**：系统状态只在一个地方（ChromaDB），没有"文件系统 vs 元数据库 vs 向量库"三处对齐问题；② **FAILED 语义天然成立**："FAILED ingestion 不产生 chunks → 不在 get_files 结果中"——不需要额外清理元数据库；③ 符合 SPEC 冻结决策。

**Trade-off**: ① **冗余**：N 个 chunk 存 N 份相同字段，空间浪费（每字段几十字节，万级 chunk 可忽略）；② **写放大**：未来若要改文件级字段（如更新 status），需 update 该文件所有 chunks 的 metadata——正是 rename metadata 级联（SPEC v1.5）的成本所在；③ `get_files()` 全量扫描 collection 的 metadata，文件数大时 O(总 chunk 数)。

**Future Improvement**（Future / Not implemented in v1）: 超过万级文件后应评估专用元数据库（SQLite/PostgreSQL）——SPEC 2.5 已把该选项明确为 v1 之外。

---

### 决策 6：rename 只做 storage-layer；metadata 级联留到 Phase 4（T0402）

**Decision**: 当前 `rename_collection` 只调用 ChromaDB 的 `Collection.modify(name=...)`（含 old_name 存在性校验）；SPEC v1.5 要求的 chunk metadata 级联（`collection_name`/`source_file`）与 uploads 目录 rename、keyword index 失效**不在本方法内**，由 T0402 完成。

**Context**: SPEC v1.5 Patch（2026-08-15）澄清了 rename 的最终契约：`VectorStore.rename_collection` 必须**一次调用内**完成 collection rename + 所有既有 chunk 的 metadata 级联，且这是"唯一合法的 metadata 写入路径"（不得新增第 12 个 public method、不得暴露 generic metadata mutation API）。TASKS.md T0103 备注明确：Phase 1 不因 v1.5 重开，级联由 T0402 在 vector_store.py 内部完成。

**Problem**: KB rename 跨两个存储（ChromaDB + 文件系统）+ 一个缓存（keyword index）。如果各自为政：collection 改了名、metadata 还写着旧 `source_file`，预览/删除靠 metadata 定位文件时直接断裂。

**Chosen Solution**: **责任拆分**（SPEC F001）：storage-layer 负责 collection rename + metadata 级联（v1.5 后）；业务层（T0402）负责 orchestration + compensation（uploads 目录 rename、keyword index 失效、失败回滚到全旧状态）。当前代码只实现第一层的 collection rename 部分，docstring 诚实标注其余归 T0402。

**Why**: ① **原子性边界**：跨 ChromaDB + 文件系统的操作没有天然 ACID，SPEC 用"业务层编排 + 补偿回滚"实现可观察原子性（失败后 = 全旧名或全新名，禁止 mixed state）；② **AC-F008-03 合规**：metadata 级联必须封装在 VectorStore 内部（禁止外部通过 `list_chunks` 读 + 直接写 Chroma 的路径）；③ 不新增 public method——SPEC 明确否决了 generic metadata update API 的诱惑（"第 12 个方法"）。

**Trade-off**: 当前状态是**不完整契约**（collection rename 已可用，metadata 级联未实现）——Phase 4 之前调用 rename 会产生 metadata 与实际状态不一致。这是 TASKS.md 明示的诚实状态，不是 bug；先建存储层、后补编排层的分阶段策略符合 Phase 边界。

**Future Improvement**（Future / Not implemented in v1）: 真正的跨存储事务（如引入 SQL 元数据库后的两阶段提交）——SPEC 已声明 v1 用补偿模式。

---

### 决策 7：cosine 度量 + HNSW 索引（存储引擎参数选择）

**Decision**: 创建 collection 时固定 `metadata={"hnsw:space": "cosine"}`；索引用 ChromaDB 默认 HNSW；持久化目录 `settings.CHROMA_PERSIST_DIR`。

**Context**: SPEC F008 ChromaDB 配置三行：similarity metric = Cosine、index = HNSW、persist dir = `chroma_db/`。

**Problem**: 向量相似度度量有 cosine / L2 / inner product 三种主流选择，选错直接毁掉检索质量——特别是与 Embedding 的归一化策略耦合（Phase 2 的 `normalize_embeddings=True`）。

**Chosen Solution**: cosine + HNSW。Embedding 侧做 L2 归一化（Phase 2），归一化后 cosine 距离与 L2 距离单调等价，cosine 空间下 `1 - distance` 的近似映射更合理。

**Why**: ① **方向 > 长度**：文本语义相似度更关心向量方向（"AI"和"人工智能"方向近但长度可能差很多），cosine 天然度量方向；② **与归一化配套**：bge 模型输出 L2 归一化向量后，cosine 是事实标准；③ HNSW 是 ANN 领域成熟算法，ChromaDB 默认，v1 数据量下性能充裕。

**Trade-off**: ① HNSW 构建有内存/时间开销，且删除/更新语义是近似图维护（ChromaDB 处理）；② cosine space 下 `1.0 - distance` 映射的近似性（见决策 3）。

**Future Improvement**（Future / Not implemented in v1）: 大规模时 HNSW 参数调优（M/ef）；Milvus 的 GPU 索引。

---

## 4. 架构影响

Phase 1 完成后，系统新增的能力与依赖关系：

| 新增能力 | 谁开始依赖它 | 未来 Phase 谁使用 |
|---------|------------|-----------------|
| Collection CRUD（create/list/delete/rename） | — | Phase 4 KB API（T0401/T0402/T0403 直接包装） |
| `add_texts`（chunks+vectors+9 字段 metadata 持久化） | Phase 3 Ingest（`IngestService.process` 的 store 步骤 —— **已实际发生**） | Phase 5 Upload（经由 Ingest） |
| `search`（similarity_score 检索） | — | Phase 7 VectorRetriever（T0701 直接消费） |
| `delete_by_file` | Phase 3（FAILED 回滚 —— **已实际发生**） | Phase 9 File Delete（T0903） |
| `get_files`（metadata 聚合） | — | Phase 4（file_count）、Phase 9 File List（T0901） |
| `list_chunks`/`get_chunk_count`/`get_chunks_by_file` | — | Phase 6 Keyword Retriever（倒排索引数据源）、Phase 8（COLLECTION_EMPTY 判断）、Phase 9 Preview（T0902） |
| 私有属性隔离惯例（`self._client`） | Phase 3 通过公共方法调用，未触碰私有 API | 全项目（AC-F008-03 是 SPEC 级验收项） |

**关键洞察**：Phase 1 的"下游"分两批到来——Phase 3 先兑现了写入侧（add_texts/delete_by_file 被 Ingest 真实调用），检索侧（search/list_chunks）要等 Phase 6-7 才兑现。公共接口设计的正确性在 Phase 3 得到了第一次实战检验：Ingest 不需要知道 ChromaDB 的任何细节就能完成存储。

---

## 5. 工程问题分析

### 可维护性

- ✅ 契约文档化：ABC 的每个方法 docstring 直接引用 SPEC 条款（如 search 引用 F008 公式），SPEC 与代码互为索引
- ✅ 数据模型内聚：`ChunkRecord`/`VectorSearchResult` 定义为 Pydantic 模型，字段级 description 即文档
- ⚠️ 495 行单文件包含 ABC + 实现 + 3 个内部模型——未来加 Milvus 实现时建议拆分文件
- ⚠️ `get_files` 返回 `List[Dict[str, Any]]`（自由 dict）而非强类型 FileRecord 模型——字段拼写错误无运行时检查（schemas.py 的 `FileItem` 是 API 层模型，两者靠人工对齐）

### 扩展性

- ✅ **换存储引擎是明确的扩展路径**：新实现子类化 `VectorStore` 即可（Milvus 是 SPEC 明示的 future 方向）
- ⚠️ 无依赖注入/工厂：调用方直接 `ChromaVectorStore()`（ingest.py 内部 import）——换实现仍需改实例化点
- ⚠️ 11 个方法是"最大公约数"契约：Milvus 与 ChromaDB 的能力差（如 Milvus 的分区）无法通过现有接口表达——未来可能发现接口需要演进，但 SPEC 已否决新增方法，届时需 SPEC 决策

### 数据一致性

- ✅ **denormalization 一致性约束**：同 file_id 的 file_size/upload_time/ingestion_status 必须一致——写入侧（Ingest 一次构造）天然保证，读取侧（get_files 取第一条）依赖该保证
- ✅ FAILED 语义：FAILED ingestion 不产生 chunks → 自动从 get_files 消失（无幽灵文件记录）
- ⚠️ **rename 的当前缺口**（已知、有计划）：metadata 级联未实现前，直接调用 rename 会造成 `metadata.collection_name`/`source_file` 与实际不一致——T0402 补全并保证原子性
- ⚠️ ChromaDB 写入与文件系统之间无事务：Ingest 先写文件、后写 Chroma，中间崩溃可能留下孤儿文件（FAILED 回滚只覆盖"管道内失败"，不覆盖进程崩溃）——v1 无备份策略（SPEC OQ-011 DEFER）

### 错误处理

- ✅ `rename_collection` 校验 old_name 存在（`AppError("COLLECTION_NOT_FOUND")`），对齐 SPEC F001 错误表
- ✅ 异常统一走 Phase 0 的 AppError 体系，无 ChromaDB 原始异常泄漏（未捕获的会落 500 INTERNAL_ERROR）
- ⚠️ `get_collection(collection)` 对不存在 collection 的行为未显式包装——ChromaDB 抛出的异常会落到 catch-all 500 `INTERNAL_ERROR`，而不是 404 `COLLECTION_NOT_FOUND`。**这是已知语义缺口**：Phase 4/6/7 的调用方需要在上层显式检查 collection 存在性（T0401 的依赖检查、T0804 的 get_chunk_count 前置检查），或未来在 VectorStore 内统一包装

### 性能

- ✅ 检索路径（search）是 HNSW 近似检索，log 级复杂度，v1 数据量毫秒级
- ✅ `get_chunk_count` 用 ChromaDB 原生 `count()`（元数据操作，不拉全量数据）
- ⚠️ `get_files`/`list_chunks` 是**全量扫描**（`col.get()` 拉全部 metadata/documents）——Keyword Retriever 构建倒排索引必须全量（v1 无增量），文件列表全量聚合。万级 chunk 可接受，十万级会明显变慢
- ⚠️ `search` 每次构造 `VectorSearchResult` Pydantic 模型 + 排序（top_k 小，开销可忽略）

### 安全

- ✅ 私有属性隔离：`self._client` 不暴露，外部无法绕过公共接口拿 ChromaDB 对象做任意操作（AC-F008-03 验收项）
- ✅ raw distance 不泄漏——检索分数语义由公共契约锁定
- ⚠️ collection name 作为查询 key 直接传给 ChromaDB：name 的合法性校验在 Phase 4 的 API 层（canonical regex）——**当前**（Phase 4 前）没有调用方会用用户输入创建 collection，但这是"校验在边界"原则的提醒：存储层信任调用方已校验
- ⚠️ ChromaDB 持久化目录本地文件，无加密——部署假设可信网络（SPEC 10.5）

---

## 6. 如果规模扩大怎么办？

> 本节所有方案均为 **Future / Not implemented in v1** 分析。SPEC NFR 11.2：v1 单机、万级 document；"ChromaDB 超出后需评估迁移到 Milvus"是 SPEC 原文。

### 10× 规模（文档量 ×10，如知识库到十万级 chunk）

**可能出现的瓶颈**：

- `get_files()` / `list_chunks()` 全量扫描：每次文件列表、每次 keyword index 构建都拉全量 metadata，chunk 数到十万级时单次操作进入秒级
- keyword index 全量重建（Phase 6，内存倒排索引）：十万级 chunk × 中文 bigram 分词，构建时间与内存线性增长
- collection 数量增多后 `list_collections()` 与大量小 collection 的管理开销

**优化方向**（Not implemented in v1）：

- keyword index 增量更新（SPEC 2.5 明确 defer：v1 仅全量重建）——按 file_id 粒度增量增删
- `get_files` 分页 / 缓存（文件列表不必每次全量）

### 100× 规模（文档量 ×100，如百万级 chunk）

**可能出现的瓶颈**：

- **ChromaDB 单机上限**：SPEC 原文"ChromaDB 适合中小规模（万级 document）"——百万级 chunk 超出设计目标
- 单进程内存：keyword 倒排索引、ChromaDB HNSW 图都在单机内存/磁盘
- `where={"file_id": ...}` 的 metadata 过滤在大量数据下的性能衰减

**优化方向**（Not implemented in v1）：

- **ChromaDB → Milvus**：VectorStore ABC 就是为此保留的扩展点——实现 `MilvusVectorStore(VectorStore)`，业务代码零改动（这是 Phase 1 决策 1 的兑现时刻）
- keyword index 迁出进程内存 → Redis/独立索引服务
- 异步索引构建：上传与索引解耦（消息队列）

### 1000× 规模（SaaS 化，千万级 chunk、多租户并发）

**可能出现的瓶颈**：

- 单机存储与检索吞吐：HNSW 检索受单机 CPU/内存限制，并发 QPS 上不去
- 单点故障：ChromaDB 无副本/分片（v1 依赖文件系统持久化，无备份策略）
- 元数据聚合（get_files）在千万级 chunk 下不可行——必须回到专用元数据库

**优化方向**（Not implemented in v1）：

- **单机 → 分布式**：Milvus 分布式部署（proxy + data/index/query nodes），collection 分片
- **同步 → 异步任务队列**：上传/ingest 走 Celery/RQ 等任务队列，API 立即返回任务 ID，前端轮询进度（SPEC 2.5：v1 无上传进度推送）
- 专用元数据库（PostgreSQL）：FileRecord 独立存储，chunk metadata 只保留检索必需字段——推翻"denormalization"决策，这是规模倒逼的架构演进
- 多副本 + 备份策略（SPEC OQ-011 defer 项）

**核心判断**：Phase 1 的抽象决策是**为 100× 时刻预留的保险**。ABC 今天看是"纯成本"，但它把最贵的架构迁移（换向量数据库）变成了"写一个新子类"。规模分析的正确姿势不是"现在实现这些"，而是"确认现在的设计不会堵死那条路"。
