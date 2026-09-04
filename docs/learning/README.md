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

### Learning Pass Workflow（技术教学工作流）

**Canonical workflow**: [templates/phase-learning-pass-workflow.md](./templates/phase-learning-pass-workflow.md)

**Document structure**: [templates/phase-learning-template.md](./templates/phase-learning-template.md)

两份文件职责不同：workflow 定义 Agent **怎样执行** Learning Pass——怎样读证据、推理代码、面向学习者教学、处理验证边界并做 reader test；template 定义 Technical Learning 文档**按哪 11 节组织**。运行未来 Task / Phase Learning Pass 时必须先读 workflow，再按 template 更新现有 Phase 文档。

默认学习者是熟悉 JavaScript / TypeScript / React、有少量 Node.js 经验，但尚未系统学习 Python/backend 的前端开发者。写作采用中文解释 + English technical terms，在准确且有帮助时使用 TypeScript/JavaScript analogies，并显式解释 Python-specific behavior。🟢 必会 / 🟡 了解原理即可 / 🔵 知道存在即可用于管理学习深度。

[phase-05-file-upload.md](./phase-05-file-upload.md) 是 canonical **depth/style precedent**，不是内容或固定行数模板。未来文档应继承它的 learner orientation、真实代码精读、design-intent explanation、项目上下游、verification honesty、failure/data-flow reasoning 与 self-test/practice；篇幅随概念复杂度调整，不能因为文件少或偏好 concise output 而压扁核心教学。

执行层级必须区分：

- **Task Learning Pass**：Task 完成后增量更新当前 Phase Technical Learning，记录该 Task 的 Code / Project / Learning Understanding 与 Interview Candidates，不把未完成 Phase 提前写成 complete。
- **Phase Learning Review / Consolidation**：全部 Phase Tasks DONE 且 Gate 完成后，才进行跨 Task 去重、统一 mental model、补齐 Phase 级 self-test，并按 cadence 晋升 Interview Candidates。

所有 project-specific claims 必须来自 `CLAUDE.md`、相关 TASKS、被引用 SPEC、actual implementation、tests/verification artifacts 与必要 git evidence；Task description、Completion Report、Engineering Review 或历史 verdict 都不能替代读真实代码。验证结论必须区分 code-level、unit、integration、real E2E、deferred 与 not independently rerun。

各类产物的 canonical responsibility：

| 产物 | 负责什么 |
|---|---|
| **Technical Learning** | code mechanics、project context、learner concepts、data flow、verification learning、practice |
| **Engineering Review** | 完整 ADR、trade-off、failure taxonomy、一致性、scalability、Known Gaps |
| **Phase Gate Review** | REVIEW-ONLY 独立验收与 next-Phase readiness verdict |
| **Phase Learning Review** | Gate 后的 Phase-level learning consolidation 与 Interview Candidate 晋升 |
| **Interview Guide** | 项目级完整回答、STAR、追问与诚实边界话术 |

三层内容 cross-link，不复制完整分析；Learning Pass 不能退化为 Task Completion summary，也不能用 Engineering Review 替代 Technical Learning 深度。最终质量问题是：**目标学习者能否读完文档、打开引用代码，并用自己的话解释这个 Phase？**

### Phase Gate Review（独立阶段门）

**Canonical protocol**: [templates/phase-gate-review-template.md](./templates/phase-gate-review-template.md)

Phase Gate Review 位于 Learning Pass 之后、Phase Learning Review 与下一 Phase 之前。默认模式是 **REVIEW-ONLY**：除非用户明确授权，否则审查者不修改文件、不修复 findings、不改 `SPEC.md` 或 Task status、不启动下一 Phase、不提交或推送。

Gate Review 必须独立对照 `SPEC.md > TASKS.md > CLAUDE.md`，审计全部 Phase Tasks、适用 AC、实现契约、runtime evidence 与完整 repository state。Task Completion Report、Technical Learning、Engineering Review、历史 verdict 都可以帮助定位证据，但不能替代当前独立验证：**Existing review verdicts are context, not evidence.**

四类产物各自负责不同问题，不能互相折叠：

| 产物 | 回答的问题 |
|---|---|
| **Technical Learning** | 代码是什么、如何运行、学习者需要掌握什么 |
| **Engineering Review** | 设计为何如此、ADR/取舍/failure modes/规模边界是什么 |
| **Phase Gate Review** | 当前 Phase 是否被独立证据验收、是否安全进入下一 Phase |
| **Phase Learning Review** | Gate 后如何做 Phase 级学习 consolidation 与 Interview Candidate 晋升 |

Phase 只有取得标准化 `PHASE_X_PASS — READY_FOR_PHASE_Y` verdict 后，才可视为已准备进入下一 Phase；PASS 本身不授权审查者自动启动下一 Phase。若 Gate 判定 `FAIL` 或 `BLOCKED`，完成修复或取得必要决策后必须执行 **Gate Re-review**。Re-review 按“Original Finding → Required Remediation → Actual Change → Regression Verification → Current Disposition → Revised Verdict”做 delta verification，不覆盖或改写原 verdict 历史。

本协议从创建之日起治理未来 Gate 与显式 Re-review。下方 Phase 状态保留历史执行顺序；个别旧 Phase 的 Learning Review 早于 Gate，不应被解读为新 canonical workflow 的例外或先例。

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

**状态**: 🟡 IN PROGRESS（编码与验证全部完成：T0501–T0503 Learning Pass + Engineering Review + Phase Learning Review completed；Phase Gate Review：PHASE_5_FAIL（AC-F002-01）→ F-1/F-2 修复完成（2026-08-25）→ Re-review 待执行）

**Tasks**: T0501 ✅ | T0502 ✅ | T0503 ✅

**学习重点**:

- 六步上传校验管道（路径安全 → 扩展名 → 大小 → 空文件 → KB 存在 → 同名）✅（T0501）
- `PureWindowsPath` 跨平台路径安全判定 + 拒绝而非改写 ✅（T0501）
- 校验先于任何文件系统写入（AC-SEC-01 / SPEC 10.2）✅（T0501）
- 查重走 `get_files` 派生聚合——FAILED 文件天然可重传 ✅（T0501）
- multipart/form-data 文件上传 + POST /api/upload 端点 ✅（T0502）
- 失败两条路径 × 两个清理责任方（FAILED 归 IngestService / 异常归端点）✅（T0502）
- keyword index 只在 200 结果后失效——失败零副作用的推理链 ✅（T0502）
- SUCCESS / SUCCESS_WITH_WARNINGS / FAILED 三态模型与回滚的端点级验证：15 场景矩阵 + 断言只走 public interface + 零业务代码修复 ✅（T0503）
- 验证基础设施：子进程隔离 / 环境变量先于 import / 声明替代与 GUARD 分离 ✅（T0503）
- VectorStore.add_texts 分批持久化 + 批次失败按 file_id 补偿删除（file-level all-or-nothing）✅（Phase 5 Gate 修复 F-1/F-2，V9/V10 升级 CHECK 复跑 PASS）

**学习文档**（三层架构，各司其职）：

- 📖 **Technical Learning**: [phase-05-file-upload.md](./phase-05-file-upload.md)（T0501–T0503 教材：六步校验 + 端点编排逐行精读 / 失败路径与清理责任 / 验证脚本精读 5.7 / 顺序重排记录 / 自测练习）
- 🔍 **Engineering Review**: [engineering-review/phase-05-engineering-review.md](./engineering-review/phase-05-engineering-review.md)（T0501–T0503 工程复盘：ADR-01~11 / Pending #35–#38 / Known Gaps 1-6 / 规模分析）
- 🎤 **Interview Preparation**: [interview-notes/dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md)（按 cadence，T0501/T0502/T0503 均为普通 Task——Interview Candidates 于教材第 4/10 节；Phase 5 Learning Review（2026-08-26）已完成话术 consolidation：Phase 5 深度章 = 30 秒 + 1-2 分钟 + 验证驱动修复 STAR + 12 高频追问 + 4 工程深问，并更新 3 分钟介绍与亮点 16/17）

---

### Phase 6 — Keyword Retrieval

**状态**: ✅ COMPLETED（T0601–T0602 DONE；Learning Pass + PHASE_6_PASS Gate + Phase Learning Review 全部完成，2026-08-27）

**Tasks**: T0601 ✅ | T0602 ✅

**当前学习产物**:

- 📖 **Technical Learning**: [phase-06-keyword-retrieval.md](./phase-06-keyword-retrieval.md)（T0601–T0602 教材：mixed-language tokenizer / inverted index 双表 snapshot / lazy + dirty lifecycle / normalized score / 13 项测试证据 / AC-F009-05 E2E 边界 / 自测练习）
- 🔍 **Engineering Review**: [engineering-review/phase-06-engineering-review.md](./engineering-review/phase-06-engineering-review.md)（T0601–T0602 增量评审 + 历史 PHASE_6_PASS Gate 记录：ADR-01~10 / shared cache 风险 / 一致性与并发边界 / 规模分析 / Known Gaps）
- 🎤 **Interview Preparation**: [interview-notes/dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md)（Phase 6 Learning Review 已完成 consolidation：Phase 6 深度章 = 30 秒 + 1–2 分钟 + 8 高频追问 + 4 工程深问；无真实 incident，不虚构 STAR；并同步更新项目介绍、亮点 18 与既有 Phase 6 状态话术）

**学习重点**:

- mixed-language tokenizer（English/alphanumeric + Chinese overlapping bigram）
- 倒排索引（Inverted Index）构建与更新
- Lazy build + dirty flag 索引生命周期
- keyword_score 计算公式
- VectorStore public-interface isolation
- class-level shared state 与 test isolation

---

### Phase 7 — Vector & Hybrid Retrieval

**状态**: ✅ COMPLETE（T0701、T0702、T0703 DONE；`PHASE_7_PASS — CLOSED`；Engineering Review 与 Phase Learning Review 已完成，2026-09-03）

**Tasks**: T0701 ✅ | T0702 ✅ | T0703 ✅

**当前学习产物**:

- 📖 **Technical Learning**: [phase-07-vector-retrieval.md](./phase-07-vector-retrieval.md)（T0701–T0703 + Phase Learning Review：统一 retrieval mental model、score/identity/filter/storage ownership、跨 Task data flow、self-test chain 与验证边界）
- 🔍 **Engineering Review / Gate record**: [engineering-review/phase-07-engineering-review.md](./engineering-review/phase-07-engineering-review.md)（T0701–T0703 增量评审 + `PHASE_7_PASS — CLOSED` closure record；F011 历史、accepted MINOR 与 T1202 deferred evidence 已保留）
- 🎤 **Interview Preparation**: Phase Learning Review 已完成候选筛选与晋升，完整 30 秒 / 1–2 分钟回答、10 道高频追问、4 道工程深问与诚实验证边界已进入 [Interview Guide 的 Phase 7 深度章](./interview-notes/dx-rag-interview-guide.md#phase-7-深度章--vector--hybrid-retrievalt0701t0703-已实现--gate--learning-review-完成)

**当前与未来主要学习主题**:

- Vector Retrieval（语义检索，T0701 ✅）
- query embedding → `VectorStore.search()` → `vector_score` 的契约边界（T0701 ✅）
- Hybrid Retrieval（关键词 30% + 向量 70% 加权融合，T0702 ✅）
- `chunk_id`-based merge & dedup（T0702 ✅）
- Relevance Filter（`MIN_RELEVANCE_SCORE`，T0702 ✅）
- Retrieval facade / unified module entry point（T0703 ✅；QA Service T0804 ✅；HTTP endpoint T0805 ✅）

---

### Phase 8 — RAG & QA

**状态**: ✅ COMPLETE（T0801、T0802、T0803、T0804、T0805 DONE；Phase Gate Review `PHASE_8_PASS — READY_FOR_PHASE_9`；Phase Learning Review 完成 2026-09-02；当前证据复核完成 2026-09-03；Engineering Review 完成 2026-09-04）

**Tasks**: T0801 ✅ | T0802 ✅ | T0803 ✅ | T0804 ✅ | T0805 ✅

**当前学习产物**:

- 📖 **Technical Learning**: [phase-08-rag-qa.md](./phase-08-rag-qa.md)（T0801–T0805 + Phase Learning Review：统一 RAG→QA data flow、context/source assembly、history validation/truncation/formatting、DeepSeek client/System Prompt/retry/error mapping、QAService orchestration、POST `/api/query` endpoint、验证边界；当前 35/35 Phase 8 focused、78/78 backend evidence 已复核）
- 🔍 **Engineering Review**: [engineering-review/phase-08-engineering-review.md](./engineering-review/phase-08-engineering-review.md)（T0801–T0805：ADR、failure taxonomy、一致性/可维护性、同步 retry 与输入预算边界、10x/100x/1000x 规模分析）
- 🎤 **Interview Preparation**: Phase Learning Review 已将精选内容晋升到 [Interview Guide 的 Phase 8 深度章](./interview-notes/dx-rag-interview-guide.md)；Technical Learning 仍保留完整 self-test 与候选问题

**当前与未来主要学习主题**:

- RAG Context Assembly（格式化 + MAX_CONTEXT_CHARS 截断，T0801 ✅）
- Source Citation（来源组装，非 LLM 生成，T0801 ✅）
- Conversation History 处理（T0802 ✅：校验 + 最近 20 条截断 + 格式化）
- DeepSeek Chat API Client + System Prompt（T0803 ✅：OpenAI-compatible adapter + message assembly）
- Retry 策略（T0803 ✅：指数退避、可重试 vs 不可重试错误）
- QA Service 编排（T0804 ✅：preflight → hybrid retrieval → context/history → LLM → sources）
- POST `/api/query` API boundary（T0805 ✅：request validation → collection existence → QAService delegation → response/error envelope）
- `COLLECTION_EMPTY` vs relevance-filter-empty 的区别（T0804/T0805 ✅；HTTP mapping 已完成，真实依赖仍 deferred）

---

### Phase 9 — File Management API

**状态**: ✅ COMPLETE（T0901、T0902、T0903 DONE；Phase Gate Review：`PHASE_9_PASS — READY_FOR_PHASE_10`；Phase Learning Review 完成 2026-09-04）

**Tasks**: T0901–T0903

**当前与未来主要学习主题**:

- File list API（metadata 聚合，T0901 ✅）
- Chunk-based file preview（T0902 ✅：persisted chunks 按 `chunk_index` 重建，最多 5000 字符）
- File cascade delete（T0903 ✅：raw file → ChromaDB file data → keyword index dirty mark）

**当前学习产物**:

- 📖 **Technical Learning**: [phase-09-file-management.md](./phase-09-file-management.md)（T0901–T0903 Task 精读 + Phase-level mental model、data flow、ownership、evidence boundary 与 self-test chain）
- 🔍 **Engineering Review**: [engineering-review/phase-09-engineering-review.md](./engineering-review/phase-09-engineering-review.md)（T0901–T0903：identity/source-of-truth、不可逆级联顺序、path safety、failure taxonomy、规模分析与 Known Gaps；2026-09-04）
- 🎤 **Interview Preparation**: [Interview Guide](./interview-notes/dx-rag-interview-guide.md) 已收录 Phase 9 深度章；本文仍保留 Task-level candidates，避免和项目级 answer bank 重复

---

### Phase 10 — Frontend Foundation

**状态**: ✅ COMPLETE（T1001、T1002 DONE；`PHASE_10_PASS — READY_FOR_PHASE_11`；Phase Learning Review 完成 2026-09-04）

**Tasks**: T1001 ✅ | T1002 ✅

**当前学习产物**:

- 📖 **Technical Learning**: [phase-10-frontend-foundation.md](./phase-10-frontend-foundation.md)（T1001–T1002 + Phase Learning Review：typed HTTP boundary、UI composition boundary、三类契约、统一 cross-Task mental model、Gate-calibrated evidence 与贯通 self-test）
- 🔍 **Engineering Review**: [engineering-review/phase-10-engineering-review.md](./engineering-review/phase-10-engineering-review.md)（T1001–T1002：typed transport boundary、runtime validation gap、controlled shell、client/remount lifecycle、failure taxonomy 与 scale analysis；2026-09-04）
- 🎤 **Interview Preparation**: candidates 已完成筛选并晋升到 [Interview Guide 的 Phase 10 深度章](./interview-notes/dx-rag-interview-guide.md#phase-10-深度章--frontend-foundationt1001t1002-已实现--gate--learning-review-完成)

**当前与未来主要学习主题**:

- 集中式 API Client 设计（T1001 ✅）
- TypeScript 类型定义与后端 Pydantic Schema 对齐（T1001 ✅）
- 统一 error normalization 与 compile-time/runtime contract 边界（T1001 ✅）
- Ant Design 全局配置与 Layout 搭建（T1002 ✅）
- React controlled state 驱动单页区域切换、无 Router（T1002 ✅）
- responsive zero-width Sider 与 accessibility semantics（T1002 ✅；自动化回归尚未建立）

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

每个已完成的 Phase 一份独立工程决策复盘；进行中的 Phase 可按 Task 增量维护同一文件，待 Phase Gate 后再收口状态。评审使用统一结构：
Phase 定位 / 为什么需要这个模块 / 核心设计决策（Decision-Context-Problem-Chosen Solution-Why-Trade-off-Future Improvement）/ 架构影响 / 工程问题分析（可维护性/扩展性/数据一致性/错误处理/性能/安全）/ 规模扩大分析（10x/100x/1000x，均标记 Future / Not implemented in v1）。

- [phase-00-engineering-review.md](./engineering-review/phase-00-engineering-review.md) — Project Bootstrap（配置/错误体系/数据模型）
- [phase-01-engineering-review.md](./engineering-review/phase-01-engineering-review.md) — VectorStore Foundation（ABC 抽象/距离语义边界/反规范化）
- [phase-02-engineering-review.md](./engineering-review/phase-02-engineering-review.md) — Embedding（Lazy Singleton/L2 归一化/离线部署）
- [phase-03-engineering-review.md](./engineering-review/phase-03-engineering-review.md) — Document Processing Pipeline（编码级联/OCR 分级/三态回滚）
- [phase-04-engineering-review.md](./engineering-review/phase-04-engineering-review.md) — Knowledge Base Management（T0401：SPEC_CONFLICT 真实案例 / ADR-01~05 / Create 双副作用一致性缺口）
- [phase-05-engineering-review.md](./engineering-review/phase-05-engineering-review.md) — File Upload API（T0501–T0503：校验、端点编排、回滚验证）
- [phase-06-engineering-review.md](./engineering-review/phase-06-engineering-review.md) — Keyword Retrieval（T0601–T0602 增量评审完成；含历史 PHASE_6_PASS Gate 记录）
- [phase-07-engineering-review.md](./engineering-review/phase-07-engineering-review.md) — Vector & Hybrid Retrieval（T0701–T0703 增量评审 + `PHASE_7_PASS — CLOSED` Gate record；Phase Learning Review 已完成）
- [phase-08-engineering-review.md](./engineering-review/phase-08-engineering-review.md) — RAG & QA（T0801–T0805：Context/Source、History、DeepSeek adapter、QA orchestration、`/api/query`；ADR / failure taxonomy / scale analysis；2026-09-04）
- [phase-09-engineering-review.md](./engineering-review/phase-09-engineering-review.md) — File Management API（T0901–T0903：metadata projection、persisted preview、irreversible cascade delete、path safety / partial failure / scale analysis；2026-09-04）
- [phase-10-engineering-review.md](./engineering-review/phase-10-engineering-review.md) — Frontend Foundation（T1001–T1002：typed API client、controlled App Shell、runtime/interaction evidence、failure taxonomy 与 scale analysis；2026-09-04）

### 面试指南

**文档**: [interview-notes/dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md)

- 第一部分：3 分钟项目介绍（背景/架构/我的工作/挑战/解决方案，含诚实话术）
- 第二部分：19 个技术亮点（每个含一句话概括 + 展开点 + 代码位置）
- 第三部分：34 道高频面试题（项目理解/架构设计/RAG/工程问题四类，每题含 面试官问题/优秀回答/进一步追问/回答方向）
- Phase 4 深度章（T0401–T0404 已实现）：30 秒回答 / 1-2 分钟深入 / SPEC_CONFLICT STAR / 18 道高频追问 + 8 道工程深问
- Phase 5 深度章（T0501–T0503 已实现，含 Gate Review 修复中状态）：30 秒回答 / 1-2 分钟深入 / 验证驱动修复 STAR / 12 道高频追问 + 4 道工程深问
- Phase 7 深度章（T0701–T0703 已实现；Gate `PHASE_7_PASS — CLOSED`；Learning Review 完成）：30 秒回答 / 1–2 分钟深入 / 10 道高频追问 + 4 道工程深问 / 诚实验证边界
- Phase 8 深度章（T0801–T0805 已实现；Gate PASS；Learning Review 完成）：30 秒回答 / 1-2 分钟深入 / 10 道高频追问 + 4 道工程深问 / 诚实验证边界
- Phase 9 深度章（T0901–T0903 已实现；Gate PASS；Learning Review 完成）：30 秒回答 / 1–2 分钟深入 / 高频追问 + 工程深问 / 跨存储删除边界
- Phase 10 深度章（T1001–T1002 已实现；Gate PASS；Learning Review 完成）：30 秒回答 / 1–2 分钟深入 / 8 道高频追问 + 4 道工程深问 / 前端验证证据分级
- 附录：面试前自查清单

### Phase 学习模板（Phase 4-12 用）

**文档**: [templates/phase-learning-template.md](./templates/phase-learning-template.md)

后续 Phase 学习笔记的 11 节标准结构（Phase 学习 / Phase 目标 / 项目位置 / Task 学习 / 代码理解 / 数据流 / 架构设计 / Engineering Review / Technical Decision / Interview Notes / Future Improvement），并强制"三层文档架构"边界（Learning / Engineering Review / Interview 各归其位，禁止再混写成巨型文件；每个 Task 的 Learning 只回答 Code / Project / Learning Understanding 三类问题）。

### Phase Learning Pass Workflow

**文档**: [templates/phase-learning-pass-workflow.md](./templates/phase-learning-pass-workflow.md)

未来 Learning Pass 的 canonical execution method：证据包、学习者画像、Phase 5 depth/style precedent、Task vs Phase 两级 cadence、Code / Project / Learning 三种理解、close reading、data flow + mental model、verification-as-learning、self-test/practice、三层所有权、quality guardrails 与 fresh-reader test。它规定“怎样执行”；上方 template 规定“文档长什么样”。

### Phase Gate Review 模板

**文档**: [templates/phase-gate-review-template.md](./templates/phase-gate-review-template.md)

未来 Phase Gate Review 与显式 Gate Re-review 的 canonical protocol：REVIEW-ONLY contract、独立证据规则、Task/AC audit、Git state audit、runtime verification、evidence/severity/disposition vocabulary、next-Phase readiness 与标准 verdict/report structure。历史 Gate 记录保持原样，不要求按新模板追溯重写。

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
