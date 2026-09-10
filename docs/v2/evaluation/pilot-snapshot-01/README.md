# T2001 NovaTech Pilot 入库快照 01

本目录记录 2026-09-09 按本次单独人工授权执行的真实 V1 入库及存储回读结果。这是 **Pilot evidence**，不是正式 Benchmark 结果，不包含 Recall@K、RR/MRR 或 nDCG@K。Ground Truth 尚未创建；此快照是下一步人工检查与标注的目标。

T2001 仍为 IN_PROGRESS，T2002/T2003 仍为 TODO。本次不代表 T2001 最终验收或 Phase 20 Gate 通过，也不授权后续查询或评估工作。

## 快照身份与执行方式

- Collection / snapshot ID：`t2001-novatech-pilot-01`。
- 源语料：[novatech-pilot-0.1](../pilot-corpus/README.md)，仅入库其中四份政策 Markdown，未入库 README。
- Git branch：`v2/evaluation`；HEAD：`f9817817a602caf24ad95e500fe08e44224ffc2d`。执行时 V2 文档尚未提交，不能仅凭 HEAD 重建语料。
- [snapshot.json](snapshot.json) 记录执行前 working-tree 状态、四份源文件 SHA-256、应用 Python 文件 SHA-256、本地模型文件 SHA-256、包版本、UTC 时间、上传响应及完整 chunks/metadata。仅记录白名单配置及相对路径，不包含密钥或向量。
- 从 `backend/` 工作目录，使用 FastAPI `TestClient(app)` 在进程内调用真实 `POST /api/collections` 与 `POST /api/upload`。没有 mock，实际经过现有 V1 parsing、clean_text、chunking、embedding 和持久化 Chroma；这是进程内 API 执行证据，不是浏览器或 TCP 端到端验证。
- 创建前确认目标 collection 和上传目录均不存在。创建返回 HTTP 201；按 employee → travel → expense → IT 的顺序各上传一次，全部返回 HTTP 200 / SUCCESS，warnings 均为空。未删除、重建或重试。

## 实际文件与 chunks

完整逐块正文见 [Chunk Inventory](chunk-inventory.md)。展示按 `file_name` → `chunk_index` 排序，仅便于 Review，不影响存储或 Retrieval 排名。

| file_name | 实际 file_id | chunks | chunk_index |
|---|---|---:|---|
| employee_handbook.md | `9a218b3b-1d76-48c5-a20c-1779eacd37d7` | 10 | 0–9 |
| expense_policy.md | `09917d50-a3fd-44ae-9607-541d18d32658` | 9 | 0–8 |
| it_security_policy.md | `bc7e515f-c5e0-4655-94f1-0c28a915b0bf` | 10 | 0–9 |
| travel_policy.md | `1d06e49c-9ac1-4dcc-a0a3-a38b989464f1` | 9 | 0–8 |
| 合计 | 4 个不同 file_id | 38 | 各文件从 0 连续编号 |

## 运行时配置与代码默认值

下表运行时值来自本次实际加载的 `settings`；默认值独立读取自 `Settings.model_fields`，二者本次相同。路径均相对于 `backend/`，不是机器私有绝对路径。

| 配置 | 运行时确认值 | 代码默认值 |
|---|---|---|
| MAX_CHUNK_SIZE | 800 | 800 |
| CHUNK_OVERLAP | 120 | 120 |
| EMBED_MODEL | `models/bge-small-zh-v1.5` | `models/bge-small-zh-v1.5` |
| UPLOAD_DIR | `uploads` | `uploads` |
| CHROMA_PERSIST_DIR | `chroma_db` | `chroma_db` |
| MAX_UPLOAD_SIZE_MB | 50 | 50 |
| DEFAULT_TOP_K | 5 | 5 |
| MIN_RELEVANCE_SCORE | 0.30 | 0.30 |

实际加载的模型对象为 `SentenceTransformer`，确认输出维度 512、`max_seq_length` 512；本地模型文件指纹见 JSON，未推断未核实的上游模型 revision。现有 `encode_chunks` 实现使用 `normalize_embeddings=True`，这是执行路径的代码事实；本次未导出向量或另行测量向量范数。Top-K 与 threshold 仅记录配置，未执行 Retrieval。

运行环境为 Python 3.14.6、ChromaDB 1.5.9、sentence-transformers 6.0.1、langchain-text-splitters 1.1.2；其余相关包版本见 JSON。配置值 800 是分块上限设置，不表示每块固定 800 字符，也不等同于模型 token 上限。

## 回读验证与观察

上传进程正常结束后，另起 Python 进程使用现有 `ChromaVectorStore` 的 `list_chunks`、`get_files`、`get_chunk_count`、`get_chunks_by_file` 从持久化存储回读。全部 38 个 chunks 的 ID、正文和 metadata 与首次捕获逐项相等；四个文件计数与上传响应一致，上传文件字节 SHA-256 与源文件一致。

未发现缺失或重复 chunk_id、重复 file_id、文件映射错误或索引断号；每个 chunk 的身份字段与 metadata 一致，source_file 和文件大小匹配源文件。各文件 index 0 是实际产生的简短标题/合成声明块；其余块保留现有标题前缀和原文引用。实际正文长度为 86–582 个 Python 字符。没有为改善边界而调整内容或配置；这些观察不构成检索质量判断。

未发现入库异常。Git 命令提示无法读取用户级 global ignore 文件，但退出成功；工作区变更核查另以执行前后的文件 SHA-256 对照完成，该提示未影响入库。

## 保存与后续人工审阅

实际运行数据保留在 `backend/uploads/t2001-novatech-pilot-01/` 和 `backend/chroma_db/`；文档目录仅保存文本证据，不复制运行时数据库或模型文件。JSON 与 Inventory 是观测记录，不是可直接恢复向量索引的备份。

当前 UUID 身份只对这个已捕获快照有效。请勿随意删除或重新入库此 collection；下一步创建的 Ground Truth 必须绑定此快照及其 chunk_id。如以后必须重建，应记录为新快照，并重新映射和人工审阅相关性标注，不能假定 UUID 不变。

下一步由人工 Review 实际 chunks，再决定后续标注工作。本次未创建 Query Dataset、query_id、相关性判断/等级、Answerable/Unanswerable 标签或 Dev/Test split；未运行评估查询、Hybrid Retrieval、指标计算或 Candidate comparison。
