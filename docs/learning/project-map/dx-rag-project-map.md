# DX-RAG 项目地图（Project Map）

> 从项目整体角度理解 DX-RAG：它是什么、为什么存在、每一层做什么、13 个 Phase 如何拼成完整系统。
> 不深入代码细节——代码级的逐行精读请阅读对应的 `phase-XX-*.md` 学习笔记，工程决策分析请阅读 `engineering-review/`。

**当前状态快照**（以 `docs/TASKS.md` 为准，2026-08-27）：
- SPEC.md v1.6 **FROZEN**，Blocking Questions = 0
- Phase 0–5 ✅ DONE（工程地基 + 向量存储 + 嵌入 + 文档管道 + 知识库管理 API + 文件上传 API；Phase 5：Gate Review 裁定 PHASE_5_FAIL → F-1/F-2 修复完成 → Re-review 待执行；Learning Pass / ER / Learning Review 已完成）
- Phase 6 ✅ COMPLETE（T0601–T0602 DONE；PHASE_6_PASS；Learning Review 完成，2026-08-27）；Phase 7–12 ⬜ TODO

---

## 1. 项目背景

### 1.1 为什么需要这个系统？

企业/个人的知识沉淀在**文档**里：课程资料、技术文档、内部规范、会议纪要（PDF、Word、Excel、Markdown……）。这些知识有三个特征：

1. **量大**：动辄几百份文件、几百万字，人工读完不可能；
2. **静态**：知识躺在文件里，不会主动回答你的问题；
3. **非结构化**：PDF、DOCX、XLSX 都是"给人看"的格式，机器无法直接搜索。

DX-RAG 做的事情：把这些文档**喂给一个可以对话的系统**，之后用户用自然语言提问，系统直接从文档内容里找答案，并且**告诉用户答案来自哪份文件**（source citation）。

### 1.2 解决什么业务问题？

| 传统方式 | 痛点 | DX-RAG 的解法 |
|---------|------|--------------|
| 人工翻阅文档 | 慢、遗漏、无法穷举 | 全文入库，检索覆盖所有文档 |
| 关键词搜索（Ctrl+F） | 只认字面，不认语义 | Hybrid Retrieval：关键词 + 语义向量 |
| 找到文档后自己读 | 答案可能散落在多份文档 | LLM 综合多个 chunk 生成结构化 Markdown 答案 |
| 不知道答案可信度 | 无出处 | 每个回答附带 sources（file_id/file_name/relevance_score） |

### 1.3 用户是谁？

SPEC Section 2.2 定义的目标用户：**需要通过自然语言查询知识库文档内容的用户**。典型场景：上传课程资料/技术文档/内部知识库后，以对话方式检索和获取答案。

v1 的部署假设是**本地/可信内网**（无认证体系），所以典型使用者是：个人学习者、小团队、企业内网环境。

### 1.4 为什么普通搜索无法满足需求？

以一个真实 AC（AC-F010-01）为例：

- 知识库里有 chunk：`机器学习是人工智能的分支`
- 用户提问：`AI 的子领域`

**普通关键词搜索**：`AI 的子领域` 的字符和 `机器学习是人工智能的分支` 没有任何字面重合 → 命中 0 条。失败。

**向量语义搜索**：Embedding 模型理解 `AI ≈ 人工智能`、`子领域 ≈ 分支` → 两个句子在 384 维向量空间里距离很近 → 命中。成功。

普通搜索的局限可以归纳为：

1. **不懂语义**：只能做字面匹配，同义词/近义表达全部漏掉；
2. **只返回文档列表**：不生成答案，用户还得自己读；
3. **无综合能力**：答案分散在 5 个文档里时，搜索不能把它们拼成一个回答；
4. **无引用**：用户无法验证信息可信度。

RAG（Retrieval-Augmented Generation）正是针对这四点设计的：**检索补充 LLM 的知识盲区，LLM 把检索结果组织成答案，引用保证可信度**。

---

## 2. 系统整体架构

### 2.1 分层架构图

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND  (Next.js 14 + React + TypeScript + Ant Design 5)      │
│                                                                  │
│  page.tsx 单页应用：SideMenu 切换四个功能区                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ 知识库管理 │ │ 文件上传  │ │ 知识问答  │ │ 文件管理  │  ← Phase 10-11 │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       └────────────┴────────────┴────────────┘                   │
│                    集中式 API Client (lib/api-client.ts)          │
│                    对话历史维护在 React state（不持久化）           │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP REST (JSON + multipart/form-data)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  API LAYER  (FastAPI, prefix=/api)                               │
│                                                                  │
│  /api/health       ← Phase 0 ✅ 已实现                            │
│  /api/collections  ← Phase 4 ✅                                  │
│  /api/upload       ← Phase 5 ✅                                  │
│  /api/query        ← Phase 8 ⬜                                  │
│  /api/files        ← Phase 9 ⬜                                  │
│  统一错误格式 {error: {code, message, details}} ✅                 │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  SERVICE LAYER  (backend/app/services/)                          │
│                                                                  │
│  Ingest Service ✅  解析→清洗→切分→嵌入→存储（Phase 3）            │
│  Keyword Retriever ✅  倒排索引→关键词排序（Phase 6）             │
│  QA Service ⬜         Hybrid→上下文→LLM→来源（Phase 7-8）          │
│  Embedding ✅      bge-small-zh-v1.5 lazy singleton（Phase 2）   │
│  VectorStore ✅    11 方法公共接口 + ChromaDB 实现（Phase 1）      │
└──────────┬──────────────────┬──────────────────┬────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│ AI/DATA LAYER    │ │ STORAGE LAYER    │ │ EXTERNAL AI          │
│                  │ │                  │ │                      │
│ ChromaDB ✅      │ │ uploads/         │ │ DeepSeek Chat ⬜     │
│ (每 KB 一个       │ │ {kb_name}/       │ │ (答案生成, Phase 8)   │
│  collection,     │ │ 原始上传文件 ✅    │ │                      │
│  cosine+HNSW)    │ │                  │ │ Qwen-VL-Plus ✅      │
│                  │ │ models/          │ │ (扫描页 OCR, Phase 3) │
│                  │ │ bge-small-zh-    │ │                      │
│                  │ │ v1.5/ 本地模型 ✅ │ │                      │
└──────────────────┘ └──────────────────┘ └──────────────────────┘
```

### 2.2 文档进入流程（Ingestion Flow）

```
用户上传文件
    │
    ▼
Frontend: 类型/大小前端校验 → multipart POST /api/upload
    │
    ▼
API Layer: 路径安全 → 扩展名白名单 → 大小 → 空文件 → KB 存在 → 同名检查
    │   （任一失败 → 4xx，且不产生任何文件系统写入）
    ▼
保存到 uploads/{collection_name}/{file_name}
    │
    ▼
Ingest Service（Phase 3 ✅ 已实现）:
    按扩展名选 parser（txt/md/csv/json/log | pdf | docx | xlsx 系列）
      ├─ PDF 逐页：page.get_text() 有文本 → 用原生文本
      │           无文本 → 渲染 JPEG → Qwen-VL OCR（单页失败只记 warning）
      ├─ 编码级联：UTF-8 strict → UTF-16 strict → GBK ignore
      └─ 多格式 → 纯文本字符串
    → clean_text：去空行、去行首尾空格
    → chunk_text：Markdown 标题切分 + 递归字符切分（800 字符 / 120 重叠）
    → encode_chunks：bge-small-zh-v1.5 → 384 维 L2 归一化向量
    → VectorStore.add_texts：chunks + embeddings + 9 字段 metadata → ChromaDB
    │
    ▼
结果三态：
    SUCCESS（无 warning） | SUCCESS_WITH_WARNINGS（部分页 OCR 失败） |
    FAILED（0 chunk → 删除原始文件 + delete_by_file 全量回滚）
    │
    ▼
Invalidate keyword index（该 KB 的倒排索引标记 dirty，下次查询重建）
```

### 2.3 用户查询流程（Query Flow）

```
用户输入问题（选择 KB，携带对话历史）
    │
    ▼
Frontend: POST /api/query {question, collection_name, top_k, history}
    │
    ▼
API Layer 校验 → QA Service
    │
    ├─ KB 有 0 chunk → 409 COLLECTION_EMPTY（不检索、不调 LLM）
    │
    ▼
Hybrid Retrieval（关键词 + 向量，各召回 top_k × 2）:
    KeywordRetriever: 倒排索引（lazy build）→ token 命中率 → keyword_score [0,1]
    VectorRetriever: 问题嵌入 → ChromaDB 检索 → similarity_score [0,1]
    │
    ▼
按 chunk_id 合并 → final_score = keyword_score × 0.3 + vector_score × 0.7
    │
    ▼
排序 DESC → Relevance Filter（< 0.30 丢弃）→ Top-K 截断
    │
    ▼
Context Assembly：按分数降序拼装，MAX_CONTEXT_CHARS = 4000，不截断单个 chunk
    │
    ▼
Prompt 组装：System Prompt + 对话历史（≤20 条）+ 参考文档 + 用户问题
    │
    ▼
DeepSeek Chat（temperature=0.2, max_tokens=2048, 超时/网络/429/5xx 最多重试 2 次）
    │
    ▼
返回 {answer(Markdown), sources[{file_id, file_name, chunk_id, relevance_score}],
       query, collection_name}
    │
    ▼
Frontend: react-markdown 渲染答案 + 可折叠 sources 列表
```

---

## 3. 数据生命周期

### 3.1 上传文档：从 File 到向量

```
File（用户上传，≤50MB，扩展名白名单）
    ↓
Validation（路径安全 → 扩展名 → 大小 → 空文件 → KB 存在 → 同名；全部通过才写盘）
    ↓
Save（uploads/{collection_name}/{file_name}）
    ↓
Parse（按扩展名选解析器；PDF 逐页：原生文本 → OCR fallback）
    ↓
Clean（去行首尾空格、去空行、合并连续空白行）
    ↓
Chunk（Markdown 标题切分 + 递归切分；800 字符 / 120 重叠；每个 chunk 一个 UUID）
    ↓
Embedding（bge-small-zh-v1.5 → 384 维，L2 归一化）
    ↓
Vector Store（ChromaDB collection = 知识库；content + vector + 9 字段 metadata）
    ↓
Invalidate keyword index（标记 dirty，下次查询全量重建）
```

### 3.2 查询：从 Question 到 Answer + Citation

```
Question
    ↓
Retrieval（关键词检索 + 向量检索，各召回 top_k × 2，分数都归一化到 [0,1]）
    ↓
Merge & Fusion（按 chunk_id 合并 → final_score = 0.3×kw + 0.7×vec → 排序）
    ↓
Relevance Filter（final_score < 0.30 丢弃）→ Top-K
    ↓
Context Assembly（降序拼装，4000 字符上限，整 chunk 加入，不截断）
    ↓
LLM（DeepSeek Chat：System Prompt + 历史 + 上下文 + 问题 → Markdown 答案）
    ↓
Answer + Citation（answer 不含内联引用标记；sources 由后端从检索结果组装）
```

### 3.3 数据实体的身份规则（贯穿两条生命周期）

| 实体 | 身份 | 类比 TypeScript |
|------|------|----------------|
| Knowledge Base | `collection_name`（名字即身份，唯一） | `Map<string, KB>` 的 key |
| File | `file_id`（UUID4，不可变） | 数据库主键，`file_name` 只是 `displayName` |
| Chunk | `chunk_id`（UUID4，不可变，全局唯一） | React 列表的 `key`（但**不能**用 index！） |
| Chunk 顺序 | `chunk_index`（0-based，仅排序） | 数组下标，不是身份 |

**为什么不用 `file_name` 当身份？** 因为显示名会重命名、会重复（不同 KB 可有同名文件）、会变化——身份必须不可变。这正是 `key={index}` 反模式在后端的对应物。

---

## 4. Phase 地图

> 状态以 TASKS.md 为准。每个 Phase 回答四问：**解决什么问题 / 输入 / 输出 / 为什么存在**。

### Phase 0 — Project Bootstrap（基础工程）✅ DONE

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 项目没有"骨架"：代码不知道放哪、配置散落、错误格式混乱、前后端各自独立 |
| 输入 | SPEC 的项目结构定义（Section 4）与配置清单（Section 8.1，22 个参数） |
| 输出 | FastAPI 骨架 + Next.js 骨架 + Settings（22 参数）+ 26 个错误码目录 + 统一错误格式 + 16 个 Pydantic 模型 + `GET /api/health` |
| 为什么存在 | 后面 12 个 Phase 全部建立在这层地基上。类比：`create-next-app` + `tsconfig` + 全局 errorHandler，没有它每写一个 endpoint 都要重新发明轮子 |

### Phase 1 — VectorStore Foundation（向量存储）✅ DONE

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 向量数据需要"存进去、取出来"，且存储层不能和 ChromaDB 绑定死（未来可能换 Milvus） |
| 输入 | chunks + embeddings + metadata + collection_name |
| 输出 | `VectorStore` ABC 11 个方法 + `ChromaVectorStore` 实现（collection CRUD、add_texts、search（distance→similarity 转换）、delete_by_file、get_files、list_chunks 等） |
| 为什么存在 | RAG 的地基：没有它，Ingest 写不进数据、Retriever 读不出数据。抽象层保证"换数据库不动业务代码" |

### Phase 2 — Embedding（向量化）✅ DONE

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 文本无法直接做数学运算，必须转成向量才能计算语义相似度 |
| 输入 | chunks（List[str]） |
| 输出 | 384 维 L2 归一化向量（List[List[float]]），懒加载单例模型 |
| 为什么存在 | 语义搜索的前提。没有 Embedding，VectorStore 里存的只是字符串，"AI 的子领域"永远找不到"机器学习的分支" |

### Phase 3 — Document Processing Pipeline（文档处理管道）✅ DONE

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 用户给的是 PDF/Word/Excel，机器要的是干净的小段文本——中间隔着解析、清洗、切分三道工序 |
| 输入 | 已保存的文件路径（Phase 5 会保存） |
| 输出 | 存进 ChromaDB 的 chunks；三态结果（SUCCESS / SUCCESS_WITH_WARNINGS / FAILED+回滚） |
| 为什么存在 | 知识库的"入口管道"。垃圾进垃圾出——解析质量和切分质量直接决定检索质量 |

### Phase 4 — Knowledge Base Management API（知识库管理）✅ DONE

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 用户需要按主题隔离文档（课程资料 vs 技术文档），需要创建/重命名/删除知识库 |
| 输入 | HTTP 请求（POST/GET/PUT/DELETE /api/collections） |
| 输出 | ChromaDB collection + `uploads/{name}/` 目录的增删改查；重命名级联（collection + metadata + 目录 + keyword index）且保证原子性 |
| 为什么存在 | 多租户隔离的最小单位：一个 KB = 一个 collection = 一个目录。也是第一个真正面向用户的 API |

### Phase 5 — File Upload API（上传）✅ DONE（T0501–T0503；Gate Re-review 待执行）

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 把 Phase 3 的管道接到 HTTP 上，并保证"上传失败不留垃圾" |
| 输入 | multipart 文件 + collection_name |
| 输出 | UploadResponse（status/file_id/file_name/chunks/warnings）；FAILED 时全量回滚（T0503 端点级验证：15 场景矩阵 + 零业务代码修复）；Gate 修复 F-1/F-2：add_texts 分批持久化 + 批次失败补偿删除（V9/V10 升级 CHECK 复跑 PASS） |
| 为什么存在 | 知识库内容的入口 API。六道校验（路径安全/扩展名/大小/空/KB/同名）全部在写盘之前完成；回滚契约（SPEC F002 Upload Failure Atomicity）由验证脚本固化 |

### Phase 6-7 — Retrieval（关键词 + 向量 + 混合检索）✅ Phase 6 已完成；Phase 7 TODO

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 单一检索有盲区：关键词不懂语义，向量不懂精确术语/编号 |
| 输入 | query + collection_name + top_k |
| 输出 | 按 chunk_id 合并后的结果列表（final_score = 0.3×kw + 0.7×vec，Relevance Filter ≥ 0.30，Top-K） |
| 为什么存在 | 检索质量决定 RAG 答案质量的上限。关键词覆盖精确匹配（型号、代码、编号），向量覆盖语义匹配（同义词、改写） |

### Phase 8 — RAG & QA（问答）⬜ TODO

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 检索结果不是答案——需要 LLM 把散落的 chunk 综合成结构化回答，并附上来源 |
| 输入 | question + history + 检索结果 |
| 输出 | {answer(Markdown), sources, query, collection_name}；POST /api/query |
| 为什么存在 | 产品核心价值所在：用户要的是答案，不是文档列表。System Prompt 六原则保证"只基于知识库回答、不编造、不被文档注入指令覆盖" |

### Phase 9 — File Management API（文件管理）⬜ TODO

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 用户需要看到知识库里有什么、预览内容、删除过期文件 |
| 输入 | GET /api/files、GET /api/files/{file_id}/preview、DELETE /api/files/{file_id} |
| 输出 | 文件列表（metadata 聚合）；chunk 拼接预览（≤5000 字符）；级联删除（文件 + chunks + keyword index） |
| 为什么存在 | 知识库的"生命周期后半段"：入库不是终点，还需要维护和清理 |

### Phase 10-11 — Frontend（前端产品）⬜ TODO

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 用户不能对着 curl 用系统——需要知识库管理、上传、问答、文件管理四个界面 |
| 输入 | 用户操作（点击、拖拽文件、输入问题） |
| 输出 | 单页应用：SideMenu 切换 + 四个功能组件 + 集中式 API Client + 对话历史（React state） |
| 为什么存在 | 产品体验层。v1 约束：不引入 Redux/Zustand、无独立路由、无暗色模式——用 React 内置能力解决单页切换 |

### Phase 12 — Integration & Acceptance（集成验收）⬜ TODO

| 维度 | 内容 |
|------|------|
| 解决什么问题 | 各 Phase 单元验证通过 ≠ 系统整体工作——需要跨 Feature 的端到端验证 |
| 输入 | 全部 11 个 Phase 的产出 |
| 输出 | 摄取 E2E 验证 + 检索/QA E2E 验证 + 文件管理/安全验证 + 全量 AC 审计报告 |
| 为什么存在 | SPEC Section 12 的 60+ 条跨 Feature AC 是"系统算完成"的最终判据 |

### 4.1 依赖全景

```
Phase 0 (地基) ──┬──→ Phase 1 (VectorStore) ──┬──→ Phase 4 (KB API) ──→ Phase 5 (Upload API)
                 │                            ├──→ Phase 6 (Keyword) ──→ Phase 7 (Hybrid) ──→ Phase 8 (QA)
                 ├──→ Phase 2 (Embedding) ────┴──→ Phase 3 (Ingest) ────→ Phase 5
                 │                                                            │
                 └──→ Phase 9 (File API) ←── Phase 1/5                        │
                                                                              │
        Phase 10 (前端地基) ←── Phase 4/5/8/9 ──→ Phase 11 (前端功能)          │
                                                                              │
        Phase 12 (集成验收) ←── 全部 Phase ───────────────────────────────────┘
```

> **Readme 导航**：[docs/learning/README.md](../README.md)（Phase 学习地图）· [SPEC.md](../../SPEC.md)（产品规格）· [TASKS.md](../../TASKS.md)（任务状态）
> **工程决策分析**：[engineering-review/](../engineering-review/)（Phase 0-6 的设计决策与规模分析）
> **面试准备**：[interview-notes/](../interview-notes/)（3 分钟介绍 + 34 高频问题 + Phase 4/5/6 深度章）
