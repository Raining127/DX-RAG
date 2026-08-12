# DX-RAG 项目学习路线

> **适用于**: 正在通过 DX-RAG 项目学习现代全栈 + RAG 开发的学习者
> **前置知识**: 基础 Python / JavaScript / TypeScript

---

## 学习方式

本项目的学习方法与传统的"看教程 → 做练习"不同。DX-RAG 采用以下学习流水线：

```
Task Coding（任务编码）
  → Task Verification（任务验证）
    → Learning Pass（学习文档编写）
      → Phase Gate Review（阶段门审查）
        → Phase Learning Review（阶段学后复习）
```

每一次 Phase 完成后，你会得到一章对应的学习笔记（即当前目录下的 `phase-XX-*.md` 文件）。这些笔记：

- **基于真实项目代码**，而非虚构示例
- **结合 SPEC 设计意图**与**实际实现状态**
- **解释"为什么这样做"**，而不仅仅"做了什么"
- **明确区分** SPEC 要求、当前实际实现、通用工程知识
- **包含自测题和动手练习**，可用于学习检验

---

## Phase 学习地图

### Phase 0 — Project Bootstrap

**状态**: ✅ COMPLETED

**Tasks**: T0001–T0005

**学习重点**:

- Python / FastAPI 项目结构
- Next.js 14 App Router 项目结构
- 配置管理（Pydantic BaseSettings / 环境变量）
- 统一错误处理基础（Error Code 目录 / Global Exception Handler）
- Pydantic Data Models（API Request/Response Schemas）
- Health Endpoint（SPEC 定义，尚未实现）
- Python 依赖管理 vs Node 依赖管理
- Git / Repository Hygiene

**学习文档**: [phase-00-bootstrap.md](./phase-00-bootstrap.md)

---

### Phase 1 — VectorStore Foundation

**状态**: ⬜ NOT STARTED

**Tasks**: T0101–T0108

**未来主要学习主题**（仅根据 TASKS.md 列出，具体内容以实际实现为准）:

- Abstract Base Class（ABC）在接口设计中的应用
- ChromaDB PersistentClient 初始化与生命周期
- ChromaDB Collection CRUD
- ChromaDB metadata schema 设计
- Vector search 与 distance → similarity 转换
- File-level metadata aggregation（从 chunk metadata 去重聚合）
- Public interface 隔离私有实现的原则

---

### Phase 2 — Embedding

**状态**: ⬜ NOT STARTED

**Tasks**: T0201–T0202

**未来主要学习主题**:

- Lazy Singleton 设计模式在 Python 中的实现
- Sentence Transformers 模型加载与缓存
- Embedding 向量生成（384 维 L2 归一化）
- 为什么模型不在服务启动时加载

---

### Phase 3 — Document Processing Pipeline

**状态**: ⬜ NOT STARTED

**Tasks**: T0301–T0308

**未来主要学习主题**:

- 多格式文档解析（TXT/MD/PDF/DOCX/XLSX）
- 编码 fallback 策略（UTF-8 → UTF-16 → GBK）
- 逐页 PDF 处理 + Qwen-VL OCR fallback
- 文本清洗管道
- Markdown 标题切分 + 递归字符切分
- UUID-based chunk_id / file_id 设计
- 完整 Ingest Pipeline 编排
- FAILED rollback 原子性保证

---

### Phase 4 — Knowledge Base Management API

**状态**: ⬜ NOT STARTED

**Tasks**: T0401–T0404

**未来主要学习主题**:

- FastAPI Router 注册与 API Contract 实现
- Collection name validation（正则表达式）
- Rename 级联操作与原子性
- Cascade Delete

---

### Phase 5 — File Upload API

**状态**: ⬜ NOT STARTED

**Tasks**: T0501–T0503

**未来主要学习主题**:

- multipart/form-data 文件上传
- 多层上传校验管道
- Path traversal 安全防护
- SUCCESS / SUCCESS_WITH_WARNINGS / FAILED 三态模型
- FAILED rollback 验证

---

### Phase 6 — Keyword Retrieval

**状态**: ⬜ NOT STARTED

**Tasks**: T0601–T0602

**未来主要学习主题**:

- 中文 overlapping character bigram 分词
- 倒排索引（Inverted Index）构建与更新
- Lazy build + dirty flag 索引生命周期
- keyword_score 计算公式

---

### Phase 7 — Vector & Hybrid Retrieval

**状态**: ⬜ NOT STARTED

**Tasks**: T0701–T0703

**未来主要学习主题**:

- Vector Retrieval（语义检索）
- Hybrid Retrieval（关键词 30% + 向量 70% 加权融合）
- chunk_id-based merge & dedup
- Relevance Filter（MIN_RELEVANCE_SCORE）
- Top-K 截断

---

### Phase 8 — RAG & QA

**状态**: ⬜ NOT STARTED

**Tasks**: T0801–T0805

**未来主要学习主题**:

- RAG Context Assembly（格式化 + MAX_CONTEXT_CHARS 截断）
- Source Citation（来源组装，非 LLM 生成）
- Conversation History 处理
- DeepSeek Chat API Client + System Prompt 设计
- Retry 策略（指数退避、可重试 vs 不可重试错误）
- QA Service 编排
- COLLECTION_EMPTY vs relevance-filter-empty 的区别

---

### Phase 9 — File Management API

**状态**: ⬜ NOT STARTED

**Tasks**: T0901–T0903

**未来主要学习主题**:

- File list API（metadata 聚合）
- Chunk-based file preview
- File cascade delete

---

### Phase 10 — Frontend Foundation

**状态**: ⬜ NOT STARTED

**Tasks**: T1001–T1002

**未来主要学习主题**:

- 集中式 API Client 设计
- TypeScript 类型定义与后端 Pydantic Schema 对齐
- Ant Design 全局配置与 Layout 搭建
- React state 控制单页应用（无 Router）

---

### Phase 11 — Frontend Features

**状态**: ⬜ NOT STARTED

**Tasks**: T1101–T1105

**未来主要学习主题**:

- KnowledgeBaseManager 组件（loading/empty/success/error 四态）
- File Upload 组件（Ant Design Upload.Dragger + 前端校验）
- QA Panel 组件（React Markdown 渲染 + 对话历史管理）
- File Manager 组件（表格 + 预览 + 删除）
- Cross-component patterns（KB 切换清空 history 等）

---

### Phase 12 — Integration & Acceptance

**状态**: ⬜ NOT STARTED

**Tasks**: T1201–T1204

**未来主要学习主题**:

- E2E 验证方法论
- Acceptance Criteria 审计
- 跨 Feature 集成测试

---

## 如何使用这些学习文档

1. **按 Phase 顺序阅读**: 每个 Phase 的学习文档假设你已经理解了前面所有 Phase 的内容
2. **配合代码阅读**: 学习文档会引用具体文件路径，请打开对应文件对照阅读
3. **完成自测题**: 每章末尾有自测题，建议先尝试回答再看答案
4. **做动手练习**: 在理解的基础上，通过练习加深记忆
5. **不要跳 Phase**: 后期 Phase 高度依赖前期建立的基础设施

---

> **注意**: 学习文档是"学习材料"，不是"开发日志"。它们面向的是学习者，而非 Coding Agent。
> 如果你需要了解项目的产品规格，请阅读 `docs/SPEC.md`。
> 如果你需要了解任务的实现细节，请阅读 `docs/TASKS.md`。
