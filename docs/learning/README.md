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

**状态**: ✅ COMPLETED（T0006 于 Gate Review 后补充，现 DONE + Learning Pass 完成）

**Tasks**: T0001–T0006

**学习重点**:

- Python / FastAPI 项目结构
- Next.js 14 App Router 项目结构
- 配置管理（Pydantic BaseSettings / 环境变量）
- 统一错误处理基础（Error Code 目录 / Global Exception Handler）
- Pydantic Data Models（API Request/Response Schemas）
- Health Check Endpoint（SPEC Section 6.2 / T0006 —— 项目第一个真实 endpoint）
- Python 依赖管理 vs Node 依赖管理
- Git / Repository Hygiene

**学习文档**: [phase-00-bootstrap.md](./phase-00-bootstrap.md)

---

### Phase 1 — VectorStore Foundation

**状态**: 🟡 IN PROGRESS（T0101 Learning Pass completed）

**Tasks**: T0101 ✅ | T0102–T0108 ⬜

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

**状态**: 🟡 IN PROGRESS（Learning Pass + Learning Review completed；Gate Review 无书面记录）

**Tasks**: T0201 ✅ | T0202 ✅

**学习重点**:

- Lazy Singleton 设计模式在 Python 中的实现（T0201 ✅）
- Sentence Transformers 模型加载与缓存（T0201 ✅）
- 为什么模型不在服务启动时加载（T0201 ✅）
- TYPE_CHECKING / 函数内 import / `global` / `raise from` / `is None`（T0201 Python 新知识）
- Embedding 向量生成：`encode_chunks` + numpy `.tolist()` + 真值判断（T0202 ✅）
- 契约兑现：`add_texts` / `search` 的向量参数第一次有真实来源（T0202 ✅）

**学习文档**: [phase-02-embedding.md](./phase-02-embedding.md)（Phase 2 全章）

---

### Phase 3 — Document Processing Pipeline

**状态**: 🟡 IN PROGRESS（T0301–T0308 Learning Pass + Learning Review completed；Gate Review 无书面记录）

**Tasks**: T0301 ✅ | T0302 ✅ | T0303 ✅ | T0304 ✅ | T0305 ✅ | T0306 ✅ | T0307 ✅ | T0308 ✅

**未来主要学习主题**（仅根据 TASKS.md 列出，具体内容以实际实现为准）:

- 多格式文档解析（文本类 TXT/MD/CSV/JSON/LOG ✅ T0301；DOCX 段落+表格 ✅ T0302；XLSX 多 sheet ✅ T0303；PDF 逐页解析 + Qwen-VL OCR fallback ✅ T0304/T0305）
- 编码 fallback 策略（UTF-8 → UTF-16 → GBK）✅（T0301）
- 文本清洗管道 ✅（T0306）
- Markdown 标题切分 + 递归字符切分 ✅（T0307）
- UUID-based chunk_id / file_id 设计 ✅（T0307）
- 完整 Ingest Pipeline 编排 ✅（T0308）
- FAILED rollback 原子性保证 ✅（T0308）

**学习文档**: [phase-03-document-processing.md](./phase-03-document-processing.md)（T0301 + T0302 + T0303 + T0304 + T0305 + T0306 + T0307 + T0308 章）

---

### Phase 4 — Knowledge Base Management API

**状态**: 🟡 IN PROGRESS（编码全部完成：T0401–T0404 Learning Pass + Engineering Review + Phase Learning Review completed；剩余流程环节：Phase Gate Review）

**Tasks**: T0401 ✅ | T0404 ✅ | T0402 ✅ | T0403 ✅

**学习重点**:

- FastAPI Router 注册与 API Contract 实现 ✅（T0401）
- Collection name validation（正则表达式 + v1.6 naming-compatibility patch）✅（T0401）
- Validation before side effects 原则 ✅（T0401）
- SPEC_CONFLICT 处理流程（BLOCKED → 报告 → 产品决策 → SPEC patch）✅（T0401）
- file_count 派生聚合（消费 Phase 1 `get_files`）✅（T0401）
- Collection name validation 边界用例正式验收（canonical regex 8 用例 + `re.fullmatch`）✅（T0404）
- Rename 级联操作与原子性 ✅（T0402：7 步级联 + 两层补偿 + keyword index seam）
- Cascade Delete ✅（T0403：Chroma-first 顺序 + 不可逆 + 防御纵深）

**学习文档**（三层架构，各司其职——2026-08-24 文档重构）：

- 📖 **Technical Learning**: [phase-04-knowledge-base-management.md](./phase-04-knowledge-base-management.md)（T0401–T0404 教材：三层视角 / 逐行精读 / 链路追踪 / Validation Before Side Effects / T0404 边界用例矩阵 / T0402 Rename 级联与补偿 / T0403 Delete 级联 / 自测练习 / Quick Review）
- 🔍 **Engineering Review**: [engineering-review/phase-04-engineering-review.md](./engineering-review/phase-04-engineering-review.md)（T0401–T0404 工程复盘：SPEC_CONFLICT 全案 / ADR-01~08 / 一致性缺口 / Failure Modes / T0402/T0403 增量评审 7.9 / 规模分析）
- 🎤 **Interview Preparation**: [interview-notes/dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md)（Phase 4 深度章：30 秒 / 1-2 分钟 / SPEC_CONFLICT STAR / 18 高频追问 + 8 工程追问；T0404 为普通 Task，按 cadence 只记 Interview Candidates 于教材第 8 节；T0402/T0403 同为 Task 级——Interview Candidates 于教材第 9.9/10.7 节；Phase Learning Review（2026-08-25）已完成话术 consolidation：新增 P4Q13–P4Q18 + EP4-8、修正 EP4-3、更新 3 分钟介绍与亮点 15）

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

## 增强学习文档（项目地图 / 工程评审 / 面试 / 模板）

> 以下文档于 2026-08-23 新增，与逐 Phase 学习笔记互补：
> Phase 笔记回答"每一章怎么学"，这些文档回答"整个项目怎么看、怎么讲、怎么复盘"。

### 项目地图

**文档**: [project-map/dx-rag-project-map.md](./project-map/dx-rag-project-map.md)

- 第 1 节：项目背景（为什么需要 RAG、业务问题、目标用户、为什么普通搜索不够）
- 第 2 节：系统整体架构（五层架构图 + 文档摄取流程 + 用户查询流程标注）
- 第 3 节：数据生命周期（上传侧与查询侧两条完整流水线 + 身份规则）
- 第 4 节：Phase 地图（13 个 Phase 各自的 解决什么问题/输入/输出/为什么存在 + 依赖全景）

> **状态说明**：本 README 各 Phase 的状态行可能滞后于实际开发进度——**Task 状态一律以 `docs/TASKS.md` 为准**（CLAUDE.md 规定 TASKS.md 是权威来源）。

### Engineering Review（工程评审）

**目录**: [engineering-review/](./engineering-review/)

每个已完成的 Phase 一份独立的工程决策复盘，统一六节结构：
Phase 定位 / 为什么需要这个模块 / 核心设计决策（Decision-Context-Problem-Chosen Solution-Why-Trade-off-Future Improvement）/ 架构影响 / 工程问题分析（可维护性/扩展性/数据一致性/错误处理/性能/安全）/ 规模扩大分析（10x/100x/1000x，均标记 Future / Not implemented in v1）。

- [phase-00-engineering-review.md](./engineering-review/phase-00-engineering-review.md) — Project Bootstrap（配置/错误体系/数据模型）
- [phase-01-engineering-review.md](./engineering-review/phase-01-engineering-review.md) — VectorStore Foundation（ABC 抽象/距离语义边界/反规范化）
- [phase-02-engineering-review.md](./engineering-review/phase-02-engineering-review.md) — Embedding（Lazy Singleton/L2 归一化/离线部署）
- [phase-03-engineering-review.md](./engineering-review/phase-03-engineering-review.md) — Document Processing Pipeline（编码级联/OCR 分级/三态回滚）
- [phase-04-engineering-review.md](./engineering-review/phase-04-engineering-review.md) — Knowledge Base Management（T0401：SPEC_CONFLICT 真实案例 / ADR-01~05 / Create 双副作用一致性缺口）

### 面试指南

**文档**: [interview-notes/dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md)

- 第一部分：3 分钟项目介绍（背景/架构/我的工作/挑战/解决方案，含诚实话术）
- 第二部分：15 个技术亮点（每个含一句话概括 + 展开点 + 代码位置）
- 第三部分：34 道高频面试题（项目理解/架构设计/RAG/工程问题四类，每题含 面试官问题/优秀回答/进一步追问/回答方向）
- Phase 4 深度章（T0401–T0404 已实现）：30 秒回答 / 1-2 分钟深入 / SPEC_CONFLICT STAR / 18 道高频追问 + 8 道工程深问
- 附录：面试前自查清单

### Phase 学习模板（Phase 4-12 用）

**文档**: [templates/phase-learning-template.md](./templates/phase-learning-template.md)

后续 Phase 学习笔记的 11 节标准结构（Phase 学习 / Phase 目标 / 项目位置 / Task 学习 / 代码理解 / 数据流 / 架构设计 / Engineering Review / Technical Decision / Interview Notes / Future Improvement），并强制"三层文档架构"边界（Learning / Engineering Review / Interview 各归其位，禁止再混写成巨型文件；每个 Task 的 Learning 只回答 Code / Project / Learning Understanding 三类问题）。

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
