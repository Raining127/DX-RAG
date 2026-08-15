#  Phase 1 — VectorStore Foundation 学习笔记

> 这是一份随项目开发和个人理解逐步演进的学习文档。当前版本优先服务于"前端开发者进入 Python 后端"的第一阶段理解。
> **重要前提**：Phase 1 已全部完成——T0101–T0108 八个 Task，11 个方法全部真实实现，0 个占位。
> **本文档结构（Phase 1 Learning Review 整理版）**：
> - **Part 0 全景总览**（紧接本页下方，整理版新增）——把按 Task 追加的内容拼成一张图：完整架构图、八个 Task 的接力、11 方法边界、raw_distance → similarity_score 数据边界、四个身份字段、TS 类比索引、三个贯穿认知。
> - **第 1–119 节 按 Task 的实战部分**（历史原貌 + 去重微调）——第 1–21 节讲 T0101（其中"T0102 尚未实现"的表述记录的是 T0101 完成时的状态）；第 22–35 节 T0102；第 36–49 节 T0103；第 50–63 节 T0104；第 64–77 节 T0105；第 78–91 节 T0106；第 92–105 节 T0107；第 106–119 节 T0108。
> - **Part 9 收尾整合**（文末，整理版新增）——Phase 1 只需掌握的 10 件事、暂时不懂清单、完整阅读路线、10 道自测题、5 个小练习、快速复习卡、Phase 2 基础连接、项目待解决的架构问题。

---

## 0. 阅读指南

### 本文件结构（Phase 1 Learning Review 整理版）

| 部分 | 内容 | 什么时候读 |
|------|------|-----------|
| **Part 0 全景总览** | 架构图 / Task 接力 / 11 方法边界 / 距离→相似度边界 / 四个身份字段 / TS 类比索引 / 三个贯穿认知 | 第一遍先读；每学完一个 Task 回来对照 |
| **第 1–119 节** | 按 Task 的实战讲解（真实代码逐行读，8 个部分各 14 节） | 跟 Task 走，按下面的导航读 |
| **Part 9 收尾整合** | 10 件事 / 暂时不懂 / 完整阅读路线 / 10 自测题 / 5 练习 / 复习卡 / Phase 2 基础 / 架构问题 | 全部学完后 |

### 按 Task 快速导航

| 节号 | Task | 一句话 | 深度 |
|------|------|--------|------|
| 1–21 | T0101 契约（ABC） | 11 个方法签名 + 2 个模型；"图纸不是房子" | 🟢 必看 |
| 22–35 | T0102 初始化 + create/list/delete | PersistentClient 落盘；第一个实现类 | 🟢 必看 |
| 36–49 | T0103 rename | 校验先行 + AppError + 原生 rename | 🟢 必看 |
| 50–63 | T0104 add_texts | 三份名单对齐；"搬运工"边界 | 🟢 必看 |
| 64–77 | T0105 search | distance → similarity 落地（Phase 1 最重要的语义边界） | 🟢 必看 |
| 78–91 | T0106 delete_by_file | where 过滤 + 先数后删；F016 的 2/7 步 | 🟡 建议 |
| 92–105 | T0107 get_files | 没有文件表，列表是聚合出来的（7.3 落地） | 🟡 建议 |
| 106–119 | T0108 list_chunks / count / get_chunks_by_file | DRY helper + ChunkRecord 首秀；11/11 收官 | 🟡 建议 |
| Part 9 收尾整合 | 全 Phase | 学完后的复习与检验 | 学完后 |

> 每个 Task 部分内部都是同款 14 节结构：解决了什么问题 → 以前端方式理解 → 真实代码阅读 → 核心对象/方法 → 与上个 Task 的关系 → 当前架构中的位置 → 为什么这样设计 → Verification → 代码阅读路线 → 掌握 5 件事 → 暂时不懂 → 自测 → 练习 → 复习卡。原本按 Task 逐条列出的"每节详细说明"不再重复——它与 14 节结构一一对应，直接看对应节即可。

### 三种学习深度标记

| 标记          | 含义                                   |
| ----------- | ------------------------------------ |
| 🟢 **入门理解** | 第一遍必须理解。TypeScript 类比 + 简单解释 + 真实代码。 |
| 🟡 **项目理解** | 解释 DX-RAG 为什么这样设计。帮你理解架构决策。          |
| 🔵 **进阶阅读** | 可以以后回来看。不影响理解 Phase 1 的核心内容。          |

---

## Part 0 — Phase 1 全景总览（整理版新增）

> 这一 Part 不讲解新代码——它把第 1–119 节按 Task 拼出的八块内容拼成一张完整的图。**已学完分 Task 部分的人**：用它查漏补缺；**还没开始的人**：先读它建立地图，再进入第 1 节。
> 每小节末尾标注"详细版在第 X 节"，细节以分 Task 部分为准。

### 0A. 完整 Phase 1 架构图（一张图看懂）

```text
                        DX-RAG 上层（未来才出现 —— Phase 1 结束时还不存在）
┌────────────────────────────────────────────────────────────────────────────┐
│  IngestService（P3 摄入）     KB 管理 API（P4）          Retrievers（P6/P7）  │
│    add_texts                   create_collection         search              │
│    delete_by_file              delete_collection         list_chunks         │
│                                rename（完整级联 → T0402）                     │
│  File 管理 API（P9）           QA Service（P8）                               │
│    get_files                   search / get_chunk_count                      │
│    get_chunks_by_file          list_chunks                                   │
│    delete_by_file                                                            │
└──────────────────────────────────────┬─────────────────────────────────────┘
                                       │ 只通过 11 个 public methods 交流（AC-F008-03）
                                       ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  VectorStore(ABC)  ——  T0101 契约：11 个 @abstractmethod 签名 + 2 个模型      │
│  ┌─────────────────────────┬─────────────────────────┬────────────────────┐ │
│  │ Collection 生命周期（4） │ Data Operations（4）     │ Chunk 读取（3）      │ │
│  │ create_collection       │ add_texts               │ list_chunks        │ │
│  │ delete_collection       │ search                  │ get_chunk_count    │ │
│  │ rename_collection       │ delete_by_file          │ get_chunks_by_file │ │
│  │ list_collections        │ get_files               │                    │ │
│  └─────────────────────────┴─────────────────────────┴────────────────────┘ │
└──────────────────────────────────────┬─────────────────────────────────────┘
                                       │ 继承 + 全部实现（T0102–T0108）
                                       ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  ChromaVectorStore(VectorStore)  ——  唯一实现类                              │
│    self._client = chromadb.PersistentClient(settings.CHROMA_PERSIST_DIR)     │
│    _to_chunk_records —— @staticmethod 私有辅助（不在契约内，T0108）            │
│    11/11 真实实现，0 个占位                                                   │
└──────────────────────────────────────┬─────────────────────────────────────┘
                                       │ SDK 调用只发生在这个类内部（约束 2/3）
                                       ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  ChromaDB（磁盘目录 chroma_db/）                                              │
│   每个知识库 = 一个 Collection（hnsw:space=cosine，建库时写死）                  │
│   每条 chunk = documents 文本 + embeddings（384 维）+ 9 字段 metadata           │
└────────────────────────────────────────────────────────────────────────────┘
```

**读图三要点**：

1. 最上面那层今天不存在——Phase 1 的代码没有任何业务调用方（第 119 节收官表："❌ 还没有"）。这不妨碍学习：先有基础设施、后有使用它的人，是分层架构的正常顺序。
2. 只有 11 个门：上层无论谁要用存储，都只能走 11 个 public methods，不能碰 `_client`（SPEC F008 约束 2/3，AC-F008-03）。
3. 三层切分 = 三个职责：ABC 管"有哪些方法"、实现类管"怎么用 ChromaDB"、ChromaDB 管"数据实际存哪"。将来换 Milvus 时只换中间层（约束 4）。

### 0B. 八个 Task 的接力：从图纸到 11/11

```text
T0101 契约（图纸：11 个签名 + 2 个模型）
   │ 有了图纸才能动工
   ▼
T0102 实现类 + PersistentClient + 3 个生命周期方法（地基 + 管理门）
   │ stub 8 → 7
   ▼
T0103 rename_collection（生命周期补完；第一个错误路径 AppError）
   │ stub 7 → 6；"校验先行"成为先例
   ▼
T0104 add_texts（数据能进）
   │ stub 6 → 5；写入路径点亮
   ▼
T0105 search（数据能出；distance → similarity 语义边界落地）
   │ stub 5 → 4；检索路径点亮
   ▼
T0106 delete_by_file（数据能删）
   │ stub 4 → 3；删除路径点亮
   ▼
T0107 get_files（文件级视图：聚合出来的列表）
   │ stub 3 → 0 之前先点亮"算出来的列表"路径
   ▼
T0108 list_chunks / get_chunk_count / get_chunks_by_file（chunk 级读取 + DRY helper）
   │ stub 0；11/11 收官
   ▼
Phase 2+ 的调用方（未来）
```

| Task | 点亮了什么 | 留给下一个 Task 的资产 |
|------|-----------|----------------------|
| T0101 | 契约（ABC + 11 签名 + 2 模型） | 图纸——后面的 Task 都按它施工 |
| T0102 | 实现类 + client + create/delete/list | 第一个能实例化的类；`_client` 私有入口 |
| T0103 | rename + AppError 校验 | "校验先行"先例；错误路径模板 |
| T0104 | add_texts | 数据能进——T0105 有东西可搜 |
| T0105 | search + distance→similarity | 数据能出；语义边界先例 |
| T0106 | delete_by_file | 数据能删；`get` + `where` 查询先例 |
| T0107 | get_files | "算出来的列表"先例；dict 聚合模式 |
| T0108 | 三个读取方法 + ChunkRecord | 给 Phase 6（keyword 索引）/ Phase 9（文件预览）的积木 |

> 详细版：第 26 节（T0101→T0102）、第 40 节（→T0103）、第 54 节（→T0104）、第 68 节（→T0105）、第 82 节（→T0106）、第 96 节（→T0107）、第 110 节（→T0108）——每节都有一张承接流程图。

### 0C. 11 个 public methods 如何共同形成完整 boundary

| 分组 | 方法 | 契约输出 | 未来主要调用方 | 实现 Task |
|------|------|---------|---------------|----------|
| Collection 生命周期（管理"知识库"这个容器） | create_collection | None | KB 创建 API（P4） | T0102 |
| | delete_collection | None | KB 删除 API（P4） | T0102 |
| | list_collections | List[str] | KB 列表（P4） | T0102 |
| | rename_collection | None（失败 AppError） | KB Rename（T0402） | T0103 |
| Data Operations（容器里的数据进/出/删/聚合） | add_texts | List[str]（chunk_ids） | IngestService（P3） | T0104 |
| | search | List[VectorSearchResult] 降序 | VectorRetriever（P7）/ QA（P8） | T0105 |
| | delete_by_file | int（删除数，无匹配返回 0） | File API（P9）/ Ingest 回滚（P3） | T0106 |
| | get_files | List[dict]（6 字段） | 文件列表界面（P9） | T0107 |
| Chunk 级读取（上游加工的原料） | list_chunks | List[ChunkRecord]（无向量） | Keyword Retriever（P6） | T0108 |
| | get_chunk_count | int | 空库判断 / 统计（P8） | T0108 |
| | get_chunks_by_file | List[ChunkRecord]（ASC） | 文件预览（P9，F016） | T0108 |

为什么 11 个"不多不少"：覆盖三条数据路径（写入 T0104 / 检索 T0105 / 删除 T0106）+ 两条管理路径（collection 生命周期 T0102–T0103 / 文件级与 chunk 级视图 T0107–T0108）。每条路径只暴露"上层真正需要的操作"——漏一个方法，上层就得绕过边界直接碰 SDK（违规）；多一个方法，就把实现细节推给上层。将来换 Milvus 时，新实现类必须完整复刻这 11 个语义（F008 约束 4）。

> 详细版：第 9 节（11 方法地图）、第 21 节（🔵 边界理论）。

### 0D. raw_distance → similarity_score 的完整数据边界

```text
ChromaDB 内部       raw_distance        余弦距离 ∈ [0, 2]，越小越相似
   │   T0105 search() 内部一行：similarity_score = clamp(1.0 - raw_distance, 0.0, 1.0)
   ▼                                         ↑ 这行是分界线——raw distance 到此为止
VectorStore 边界     similarity_score    [0, 1]，越大越相似，是对外统一的分数
   │   （未来 T0701）VectorRetriever 直接把它当 vector_score 用，禁止再次归一化
   ▼
检索层（未来）        vector_score        = similarity_score 原值，改名不换算
   │   （未来 T0702）final_score = keyword_score × 0.3 + vector_score × 0.7
   ▼
融合层（未来）        final_score         [0, 1]
   │   （未来）MIN_RELEVANCE_SCORE = 0.30 过滤 → Top-K 截断
   ▼
API 层（未来）        relevance_score     用户看到的分数
```

| 名字 | 出现位置 | 语义 | 现在状态 |
|------|---------|------|---------|
| raw_distance | ChromaDB SDK 返回 | 越小越相似，∈ [0, 2] | Phase 1 已在 search() 内消化掉 |
| similarity_score | VectorStore.search 输出 | 越大越相似，∈ [0, 1] | ✅ Phase 1 已实现 |
| vector_score | VectorRetriever（未来） | similarity_score 的别名 | ⬜ Phase 7 |
| final_score | Hybrid（未来） | 0.3 / 0.7 融合 | ⬜ Phase 7 |
| relevance_score | 公开 API（未来） | 过滤 + Top-K 后的分数 | ⬜ Phase 7 |

两个必须记住的点：

1. Phase 1 只拥有第一段转换。后面四段是检索链路蓝图（CLAUDE.md 检索不变量 + 未来 Task），现在只需知道"分数会一路换名字、换语义边界，每一段都有专人负责"——不需要提前学实现。
2. clamp 两个字解决了一个数学陷阱：cosine 距离 ∈ [0, 2]，`1 - distance` 可能为负（两个向量方向完全相反时），所以必须 `max(0, min(1, x))` 夹回 [0, 1]。

> 详细版：第 4 节片段 4（公式首次出现）、第 66 节（代码落地）、第 70 节（为什么这样设计）。

### 0E. file_id / chunk_id / file_name / chunk_index —— 谁是身份

| 字段 | 是什么 | 不是什么 | Phase 1 里的实例 |
|------|--------|---------|-----------------|
| chunk_id | chunk 的不可变全局身份（UUID） | 不是 file_name:chunk_index 拼出来的 | ChromaDB document id（T0104）；检索/删除/合并的 identity（T0105/T0106） |
| file_id | 文件的不可变身份（UUID） | 不是 file_name | 删除键（T0106）、聚合键（T0107）、过滤键（T0108） |
| file_name | 纯显示名 | 不是 ID | 只随记录展示，从不参与查找（T0105/T0107/T0108） |
| chunk_index | 文件内 0-based 排序号 | 不是 ID；不代表全局顺序 | 文件预览时 ASC 拼回原文（T0108） |

身份规则（SPEC 7.1）：

- 重命名知识库 / 文件 → chunk_id、file_id 都不变（身份不随名字走）。
- 重新上传同名文件 → 新 file_id、新 chunk_id（重传 = 新身份）。
- 因此所有删除 / 聚合 / 合并都以 UUID 为准，file_name 只是给人看的。

> 详细版：第 4 节片段 2（身份规则首讲）、第 56 节（T0104 落地）、SPEC 7.1。

### 0F. Python ↔ TypeScript 全景对照（Phase 1 概念索引）

| Phase 1 出现的 Python 概念 | TypeScript / Node 类比 | python 手册位置 | 首次出现在 |
|---------------------------|-----------------------|----------------|-----------|
| ABC + @abstractmethod | abstract class / interface | 第 9 节 | T0101 |
| class X(Parent) 继承 | class X extends Parent | 第 5 节 | T0102 |
| self / `__init__` | this / constructor | 第 5 节 | Phase 0（沿用） |
| list comprehension | .map() | 17.1 | T0102 |
| dict 字面量 `{}` / `d["key"]` | 对象字面量 / obj.key（TS 两种写法，Python 只有方括号） | 17.12 | T0102 / T0104 |
| raise NotImplementedError | throw new Error("TODO") | 17.2 | T0102（已无 stub，只剩历史教学价值） |
| `_name` 私有约定 | private（但 Python 没有编译期强制） | 17.3 | T0102 |
| in / not in | includes() / !includes() | 17.5 | T0103 |
| AppError("CODE") | throw new AppError("CODE") | 第 10 节 | T0103 |
| for i in range(len(xs)) | 经典三段式 for | 17.6 | T0105 |
| lambda + sort(key=, reverse=) | sort 回调 / lodash sortBy | 17.7 | T0105 |
| max/min 组合出 clamp | Math.max(0, Math.min(1, x)) | 17.8 | T0105 |
| @staticmethod | static 方法 | 17.9 | T0108 |
| 变量标注 x: T = v | const x: T = v | 17.10 | T0107 |
| dict.values() + list() | Object.values() / Array.from() | 17.11 | T0107 |
| dict 当 Map + 计数器 | Map + reduce | 17.11 | T0107 |

> 完整语法手册在 [python-for-frontend-dev.md](./python-for-frontend-dev.md)；上表只做 Phase 1 的索引。注意：本文件里的 Python 讲解只保留"第一次完整教学"，之后出现一律以指针引用（Learning Review 去重原则）。

### 0G. 贯穿 Phase 1 的三个认知

**认知 1：翻译在边界内。** 所有"内部形态 → 对外形态"的转换都发生在 VectorStore 类内部，外部只看到统一的、语义化的结果。四个实例：

- 对象 → 名字：list_collections 返回 `[col.name for col in ...]`，而不是 SDK 对象（T0102，第 24 节）；
- distance → similarity：search 内部完成，raw distance 绝不外泄（T0105，第 66/70 节）；
- file_size → size、ingestion_status → status：get_files 的字段翻译（T0107，第 95 节）；
- SDK dict → ChunkRecord：_to_chunk_records 的模型化（T0108，第 108 节）。

这是"Adapter"思想的操作版——🔵 理论版见第 21 节。

**认知 2：方法存在 ≠ 功能可用。** ABC 的 @abstractmethod 只保证"子类定义了同名方法"，不保证"逻辑是真的"。Phase 1 的 stub 从 8 个一路降到 0：T0102 时 3 真 8 占位 → T0103 4/7 → T0104 5/6 → T0105 6/5 → T0106 7/4 → T0107 8/3 → T0108 11/0。所以任何"进度判断"都要看方法体，而不是看方法名。（第 3、22、36 节的"完成 vs 未完成"清单都在防这个错。）

**认知 3：SPEC 的一大段 ≠ 一个 Task。** SPEC 里描述一个 feature 往往是一整段流程，但 TASKS.md 会把它拆给多个 Task/Phase。实例：F001 重命名 8 步，T0103 只做其中 1 步（第 36 节）；F016 删除 7 步，T0106 只做其中 2 步（第 78 节）。学完一个 Task 就判断"这个功能没做完"或"做多了"之前，先查 TASKS.md 的边界——CLAUDE.md 的"一个 Task 一次"规则正是为此。

---

## 1. Phase 1 到底要解决什么问题

### 先说 RAG 需要做什么（不需要懂任何 Python）

RAG 系统的工作方式，用一句话说：**把文档拆碎、变成数字、存起来；提问时把问题也变成数字，找出最像的碎片，喂给 LLM 生成回答。**

拆开看：

```text
Document（用户上传的文档，如"员工手册.pdf"）
   ↓  切成小块                         [后续 Task 实现：Phase 3]
Chunk（文本片段，如"第 3 页第 2 段"）
   ↓  转成数字向量                      [后续 Task 实现：Phase 2]
Embedding（384 维数字数组，如 [0.12, -0.03, ...]）
   ↓  写入                             [后续 Task 实现：T0104]
VectorStore
   ↓  持久化                           [后续 Task 实现：T0102]
Vector Database（ChromaDB，落盘到 chroma_db/）
```

### 为什么必须"存起来再取出来"

想象用户提问："年假怎么申请？"

1. 后端把这个句子也转换成一个 384 维数字数组（query vector）
2. 到数据库里找出**数字上最接近**的那些 chunk（这就是"向量检索"）
3. 把这些 chunk 原文拼成上下文，交给 DeepSeek 生成回答

所以系统必须保存三类数据，并且将来能按需取回：

| 保存什么          | 是什么                  | 将来谁用                   |
| ------------- | -------------------- | ---------------------- |
| **chunk**     | 文档切片的文本内容            | 检索命中后拼进 LLM 上下文        |
| **embedding** | chunk 的数字向量          | 查询时做"相似度"计算            |
| **metadata**  | 这个 chunk 属于哪个文件、第几片等 | 按 file_id 删除、文件列表、文件预览 |

### 类比：一个前端开发者熟悉的东西

| RAG 概念            | 前端类比                                   |
| ----------------- | -------------------------------------- |
| 上传文档 → 切成 chunk   | 上传图片 → 切成多张缩略图                         |
| chunk → embedding | 图片 → 用感知哈希算出的指纹                        |
| 问题 → query vector | 新图片 → 算指纹 → 找最像的缩略图                    |
| VectorStore       | 你项目里的 `lib/storage.ts`——定义"存/取/查/删"的接口 |
| ChromaDB          | `localStorage` / `IndexedDB`——真正干活的底层  |

### Phase 1 在整条链路上的位置

Phase 1（T0101–T0108）只做**最下面一层**：定义并实现"向量数据怎么存、怎么查"。切块、embedding 计算都是后面 Phase 的事。

```text
切块 (Phase 3) → 计算向量 (Phase 2) → 存储和检索 (Phase 1) → 检索融合 (Phase 6-7) → 生成回答 (Phase 8)
```

**当前进度**：Phase 1 只完成了 T0101 —— 只定义了"存储和检索"这一层的**接口契约**，还没有一行真正操作 ChromaDB 的代码。

> 更新：这段话记录的是 T0101 完成时的状态。Phase 1 现已全部完成（T0101–T0108，11/11 方法真实实现）——完整总览见 Part 0，收官见第 106–119 节与 Part 9。

---

## 2. 以前端开发者的方式理解 VectorStore

### 先用你最熟悉的语言建立心智模型

如果你在 TypeScript 项目里设计一个存储层，你会先写什么？大概率是一个 interface：

```ts
// 心智模型（不是 DX-RAG 的真实代码）
interface VectorStore {
  createCollection(name: string): void;
  deleteCollection(name: string): void;
  renameCollection(oldName: string, newName: string): void;
  listCollections(): string[];

  addTexts(
    collection: string,
    chunks: string[],
    embeddings: number[][],
    metadatas: Record<string, any>[]
  ): string[];

  search(
    collection: string,
    queryVector: number[],
    topK: number
  ): VectorSearchResult[];

  deleteByFile(collection: string, fileId: string): number;
  getFiles(collection: string): Record<string, any>[];
  listChunks(collection: string): ChunkRecord[];
  getChunkCount(collection: string): number;
  getChunksByFile(collection: string, fileId: string): ChunkRecord[];
}
```

这个 interface 就回答了"VectorStore 是什么"这个问题的一半。

**Python 中，DX-RAG 用什么表达这个 contract？**

Python 没有 TS 的 `interface` 关键字。T0101 实际使用的是 **ABC（Abstract Base Class，抽象基类）**——`class VectorStore(ABC)` + `@abstractmethod`。第 5 节会详细解释，现在先建立一个大印象：

```text
TS:    interface VectorStore { ... }          ← 描述"长什么样"
Python: class VectorStore(ABC): @abstractmethod ← 同样是在描述"必须有什么能力"
```

两者不完全等价，但"定义契约"这个作用是相同的。

### VectorStore 是什么？

一句话：**VectorStore 是 DX-RAG 里所有向量数据操作的统一入口契约**。它定义了 11 个方法——"创建知识库"、"写入数据"、"检索"、"删除"等——业务代码只需要认识这 11 个方法，不需要认识 ChromaDB。

### 它为什么不是 ChromaDB 本身？

|        | VectorStore（T0101 产物） | ChromaDB                     |
| ------ | --------------------- | ---------------------------- |
| 是什么    | 抽象接口（契约）              | 第三方向量数据库 SDK                 |
| 类比     | `interface Storage`   | `localStorage` / `IndexedDB` |
| 能实例化吗  | ❌ 不能                  | ✅ 能                          |
| 有实际功能吗 | ❌ 只有方法签名              | ✅ 真正的存取逻辑                    |

就像 `interface Storage` 不是 localStorage 本身一样，VectorStore 只是"描述"，不是"干活的人"。

### 谁以后会调用它？

未来业务层（都还没实现）：

| 未来调用方               | 预计 Phase | 会用到的方法（举例）                               |
| ------------------- | -------- | ---------------------------------------- |
| IngestService（文档入库） | Phase 3  | `add_texts`, `delete_by_file`            |
| KB 管理 API           | Phase 4  | `create_collection`, `delete_collection`, `list_collections` |
| Keyword Retriever   | Phase 6  | `list_chunks`                            |
| Vector Retriever    | Phase 7  | `search`                                 |
| QA Service          | Phase 8  | `get_chunk_count`, `search`              |
| File 管理 API         | Phase 9  | `get_files`, `get_chunks_by_file`, `delete_by_file` |

### 谁以后会真正实现它？

**T0102–T0108** 会创建一个具体类（比如 `ChromaVectorStore`），继承 `VectorStore` 并逐个实现这 11 个方法，方法体里才是真正的 ChromaDB 操作。（更新：T0102 已创建 `ChromaVectorStore` 并实现其中 3 个方法，见第 22–35 节；**T0103–T0108 已把其余 8 个方法全部实现，11/11 全部真实，见第 36 节起**。）

```text
interface 定义者：T0101（✅ 已完成）   实现者：T0102（✅ 3/11）→ T0103 ✅ → T0104 ✅ → T0105 ✅ → T0106 ✅ → T0107 ✅ → T0108 ✅（11/11 全部真实）
```

---

## 3. T0101 做了什么

### 🟢 T0101 已经完成的部分

真实产物只有一个文件：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)（T0101 完成时 226 行；T0102 完成后 319 行），包含：

| 产物                   | 说明                                       |
| -------------------- | ---------------------------------------- |
| `ChunkRecord`        | 数据模型：描述"一个 chunk 长什么样"（7 个字段）            |
| `VectorSearchResult` | 数据模型：描述"一次检索命中的结果长什么样"（6 个字段，含 similarity_score） |
| `VectorStore(ABC)`   | 抽象基类：11 个方法的签名声明，全部标记 `@abstractmethod`  |

验证方式也只有一条：**这个文件能成功 import、能被其他模块用作类型标注**。仅此而已。

### 🟢 T0101 没有完成的部分

| 未完成                       | 状态                    |
| ------------------------- | --------------------- |
| ChromaDB client 初始化       | ⬜ 无任何 chromadb import |
| 创建 / 删除 / 列出 Collection   | ⬜ 方法体只有 docstring     |
| 写入 chunks / 向量 / metadata | ⬜ 同上                  |
| 向量检索                      | ⬜ 同上                  |
| 任何一行可执行的 ChromaDB 操作      | ⬜ 0 行                 |

> 更新：上表记录的是 T0101 完成时的状态。"创建/删除/列出 Collection"三项已在 T0102 实现，见第 22 节起。

### ⚠️ 最重要的一句话

> **定义 method / contract ≠ 已经完成 ChromaDB 数据库操作。**

今天你可以 `from app.core.vector_store import VectorStore`（import 成功），但你**无法**用它往数据库里写入或查询任何数据。T0101 完成的是"图纸"，不是"房子"。

### 两个值得注意的实现细节

1. **TASKS.md 写 `search(...) -> List[dict]`，真实代码返回 `List[VectorSearchResult]`**。实现者选择了更具体的领域模型而不是裸 dict——类型更安全、字段更明确。这是"实现可以在 SPEC 框架内做合理细化"的实例。
2. **TASKS.md 允许 "Abstract base class or protocol" 二选一，实现选择了 ABC**。第 5 节会讲 ABC 是什么，Protocol 属于 🔵 进阶内容（第 21 节提一句）。

---

## 4. T0101 的真实代码阅读

> 只挑 4 段最重要的代码。全部来自 [backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)。每段用统一格式解释。

---

### 代码片段 1：文件头部 docstring（第 1–18 行，节选）

**Python 原代码**

```python
"""VectorStore public interface — abstract base class.

SPEC F008 Design Constraints:
  1. One Knowledge Base = one independent ChromaDB Collection
  2. ALL ChromaDB operations MUST go through this public interface
  3. External code MUST NOT access ``_collection`` or any ChromaDB private attribute
  4. Abstraction preserves interface consistency for future Milvus extension

Distance → Similarity Semantic Boundary (F008):
  - ChromaDB raw distance MUST NOT be exposed outside VectorStore
  - ``search()`` converts distance → similarity_score::

      similarity_score = clamp(1.0 - raw_distance, 0.0, 1.0)
"""
```

**🟢 Python 语法怎么读**

- `"""..."""` — 三引号字符串。放在**文件第一行**时是 module docstring（模块级文档），不是注释。它是一段真实的字符串值，只是没人用它。
- 内容本身不需要逐行理解——它是一份"设计备忘录"，告诉未来的实现者（T0102–T0108）必须遵守什么规则。

**🟢 TypeScript / Node.js 类比**

相当于你在 `lib/vectorStore.ts` 文件顶部写了一大段 `/** JSDoc */` 说明模块的设计约束。区别是：JSDoc 只是注释，编译后消失；Python 的 docstring 是真实的字符串对象，运行时也能读到（但通常没人读）。

**🟡 在 DX-RAG 中有什么作用**

这份 docstring 浓缩了 SPEC F008 的核心约束：

1. 一个知识库 = 一个 ChromaDB Collection
2. 所有 ChromaDB 操作必须走这个接口
3. **禁止外部代码碰 `_collection`**（第 8 节展开）
4. 为未来换 Milvus 保留接口一致性

还有一条贯穿全文的公式（第 4 个片段会再出现）：

```
similarity_score = clamp(1.0 - raw_distance, 0.0, 1.0)
```

含义：ChromaDB 返回的原始值是 distance（**越小越相似**），对外必须转成 similarity（**越大越相似**，范围 [0,1]）。

**🟢 现在只需要记住什么**

1. 这个文件是 SPEC F008 的"代码版设计备忘录"。
2. 有一个硬性公式：similarity = 1 − distance（再做范围限制），distance 不允许泄露到外部。

---

### 代码片段 2：两个数据模型（第 31–71 行，节选）

**Python 原代码**

```python
class ChunkRecord(BaseModel):
    """A single chunk record (SPEC Section 7.4)."""

    chunk_id: str = Field(description="UUID, immutable globally unique identifier")
    file_id: str = Field(description="UUID, FK → FileRecord.file_id")
    file_name: str = Field(description="Display-only source filename")
    collection_name: str = Field(description="Parent collection / knowledge base name")
    chunk_index: int = Field(
        description="0-based sequence number within the file (not an ID)"
    )
    content: str = Field(description="Chunk text (≤ max_chunk_size)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full ChromaDB metadata dict (chunk_id, file_id, ...)",
    )


class VectorSearchResult(BaseModel):
    """A single vector-search hit returned by ``search()``."""

    chunk_id: str = Field(description="UUID of the chunk")
    file_id: str = Field(description="UUID of the source file")
    file_name: str = Field(description="Display-only source filename")
    content: str = Field(description="Chunk text")
    similarity_score: float = Field(
        description="Converted similarity score [0, 1]; larger = more relevant"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Full ChromaDB metadata dict"
    )
```

**🟢 Python 语法怎么读**

- `class ChunkRecord(BaseModel):` — 定义类 `ChunkRecord`，继承 Pydantic 的 `BaseModel`（Phase 0 学过：≈ TS interface + Zod）。
- `chunk_id: str = Field(...)` — 声明一个字段：类型 `str`，`Field(description=...)` 给字段附加文档说明。
- `metadata: Dict[str, Any] = Field(default_factory=dict, ...)` — 字段类型是 `Dict[str, Any]`（≈ `Record<string, any>`）；`default_factory=dict` 表示默认值是"每次新建一个空 dict"（Phase 0 学过：避免所有实例共享同一个默认对象）。
- 类内部**没有 `__init__`** —— Pydantic 的 `BaseModel` 自动根据字段声明生成构造逻辑。

**🟢 TypeScript / Node.js 类比**

```ts
// 心智模型：Pydantic BaseModel ≈ interface + Zod schema
const ChunkRecordSchema = z.object({
  chunkId: z.string().describe("UUID, immutable globally unique identifier"),
  fileId: z.string(),
  fileName: z.string(),
  chunkIndex: z.number().describe("0-based sequence (not an ID)"),
  content: z.string(),
  metadata: z.record(z.string(), z.any()).default({}),
});
type ChunkRecord = z.infer<typeof ChunkRecordSchema>;
```

**🟡 在 DX-RAG 中有什么作用**

- `ChunkRecord` 是 `list_chunks()` / `get_chunks_by_file()` 的返回类型——回答"一个 chunk 有哪些信息"。
- `VectorSearchResult` 是 `search()` 的返回类型——注意它有 `similarity_score` 而**没有** `distance` 字段。字段表里没有的东西，调用方就用不了——这就是用类型防止"实现泄露"的手段。
- 注意 `ChunkRecord` 里**没有 `embedding` 字段**：原始向量不让业务层拿到。

**🟢 现在只需要记住什么**

1. 这两个类只是"数据形状"的定义，不是数据库表。
2. `VectorSearchResult.similarity_score` = 对外统一分数（越大越好）；它没有 distance 字段，是故意的。

---

### 代码片段 3：VectorStore(ABC) 骨架（第 20–23、79–120 行，节选）

**Python 原代码**

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VectorStore(ABC):
    """Abstract base class for vector storage backends."""

    @abstractmethod
    def create_collection(self, name: str) -> None:
        """Create a new ChromaDB collection.

        Args:
            name: Collection name (knowledge base name).
        """

    @abstractmethod
    def list_collections(self) -> List[str]:
        """List all existing ChromaDB collection names."""

    # ... 其余 9 个方法结构相同
```

**🟢 Python 语法怎么读**

- `from abc import ABC, abstractmethod` — 从 Python **标准库**（内置，无需安装）的 `abc` 模块导入两个东西。`abc` 是 abstract base class 的缩写。
- `class VectorStore(ABC):` — 继承 `ABC`。这个继承的唯一作用就是告诉 Python："这个类不能直接实例化"。
- `@abstractmethod` — decorator（Phase 0 学过：先理解成"框架标签"）。贴在方法上方，含义："**子类必须实现这个方法**"。
- `def create_collection(self, name: str) -> None:` — `self` ≈ `this`（Phase 0 学过）；`name: str` 参数类型；`-> None` 返回类型 ≈ `void`。
- **函数体只有 docstring** —— 没有 `pass`，没有 `...`，没有任何可执行代码。为什么这样写是合法的？因为 Python 里字符串字面量本身就是一个合法的表达式语句，docstring 同时充当了"函数体"，所以函数体不算空。这是前端开发者最容易困惑的点（JS 注释不能当函数体，Python 的 docstring 可以）。
- docstring 里的 `Args:` / `Returns:` 是 Google 风格的文档格式约定，不是 Python 语法，阅读时可以跳过。

**🟢 TypeScript / Node.js 类比**

```ts
// 心智模型：ABC + @abstractmethod ≈ abstract class
abstract class VectorStore {
  abstract createCollection(name: string): void;
  abstract listCollections(): string[];
  // ... 其余 9 个 abstract 方法
}

// ❌ 两者都不能直接 new
new VectorStore(); // TS: 编译错误 / Python: TypeError
```

**🟡 在 DX-RAG 中有什么作用**

这是整个 T0101 的核心：**11 份方法签名 = 11 条契约条款**。未来的 `ChromaVectorStore` 继承这个类时必须实现全部 11 个方法，漏一个，实例化时 Python 直接报错。相当于给未来的实现者（包括 Coding Agent）上了一道自动检查的保险。

**🟢 现在只需要记住什么**

1. `class X(ABC)` + `@abstractmethod` = "这是契约，不是实现"。
2. 抽象方法体只有 docstring，没有任何逻辑——当前阶段。

---

### 代码片段 4：search() 方法（第 144–163 行）

**Python 原代码**

```python
    @abstractmethod
    def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int,
    ) -> List[VectorSearchResult]:
        """Vector similarity search — returns similarity_score, NOT raw distance.

        Implements the F008 Distance → Similarity semantic boundary:
        ``similarity_score = clamp(1.0 - raw_distance, 0.0, 1.0)``

        Args:
            collection: Collection name to search.
            query_vector: Query embedding vector (384-dim).
            top_k: Maximum number of results to return.

        Returns:
            Results sorted by similarity_score descending.
        """
```

**🟢 Python 语法怎么读**

- 参数列表**换行书写**，每个参数占一行——纯格式习惯，Python 对缩进敏感但不要求这样写。
- `query_vector: List[float]` — 参数类型是"浮点数列表"（≈ `number[]`）。384 维向量就是 384 个 float 的列表。
- `top_k: int` — 返回结果的最大条数（≈ `limit`）。
- `-> List[VectorSearchResult]` — 返回类型：一串 `VectorSearchResult` 对象（片段 2 定义的模型）。
- docstring 里的公式就是片段 1 里的同一条公式，这里再次强调：**返回 similarity_score，绝不返回 raw distance**。

**🟢 TypeScript / Node.js 类比**

```ts
// 心智模型
abstract search(
  collection: string,
  queryVector: number[],
  topK: number
): VectorSearchResult[];
```

几乎可以逐词对照。唯一注意：Python 的 `List[float]` 要 import `List`（`from typing import ...`），TS 的 `number[]` 不需要。

**🟡 在 DX-RAG 中有什么作用**

`search()` 是全系统最重要的方法之一：未来用户提问 → 问题转成向量 → `search()` 找出最相似的 chunks → 拼进 LLM 上下文。公式 `similarity_score = clamp(1.0 - raw_distance, 0.0, 1.0)` 的语义边界是：

| 侧              | 分数语义                               |
| -------------- | ---------------------------------- |
| ChromaDB 内部    | distance，**越小越相似**（如 0.15 表示非常像）   |
| VectorStore 对外 | similarity，**越大越相似**（如 0.85 表示非常像） |

如果不做这个转换，上层业务代码会把"最不相似的"当成"最相似的"——这是 RAG 系统里最隐蔽的 bug 之一。所以 SPEC 强制在 `search()` 内部完成转换，外部永远只看到 similarity。

**🟢 现在只需要记住什么**

1. `search()` 的输入是**向量**（`List[float]`），不是文本——"问题转向量"是别人的活（Phase 2/7）。
2. 返回的分数越大越好；distance 永远不出这个文件。

---

## 5. ABC / abstractmethod 怎么理解

### 🟢 先这样理解

Python 的 `ABC + @abstractmethod` 可以用两个你熟悉的东西来类比：

**类比 1：TypeScript interface**

```ts
interface VectorStore {
  createCollection(name: string): void;
  search(collection: string, queryVector: number[], topK: number): VectorSearchResult[];
}
```

**类比 2：TypeScript abstract class**

```ts
abstract class VectorStore {
  abstract createCollection(name: string): void;
}
```

两种类比都成立，也**都不完全等价**：

|         | Python ABC | TS interface | TS abstract class |
| ------- | ---------- | ------------ | ----------------- |
| 能实例化吗   | ❌ 不能       | ❌ 不能（类型而已）   | ❌ 不能              |
| 强制子类实现  | ✅ 实例化时检查   | 编译时检查        | ✅ 编译时检查           |
| 有运行时存在吗 | ✅ 有（真实类）   | ❌ 擦除         | ✅ 有               |

核心只要求你理解一句话：

> **父层定义"必须提供什么能力"，具体实现留给后面的 class。**

### 🟡 在 DX-RAG 中

- `VectorStore(ABC)` 定义 contract：11 个方法必须存在、签名必须一致。
- 未来的 concrete implementation（T0102–T0108 创建的 `ChromaVectorStore` 之类）继承它、逐个实现。
- Python 的强制检查发生在**实例化时**：如果未来的实现类漏了某个方法，`ChromaVectorStore()` 会直接抛 `TypeError: Can't instantiate abstract class ...`。代码跑不起来 = 契约没履行，这就是 ABC 给项目带来的实际价值。

### 🔵 进阶

Python ABC 的底层机制（`__isabstractmethod__` 标记、`ABCMeta` metaclass 如何收集抽象方法）暂时不用掌握。第一遍只需要知道"它是声明契约的工具"。

---

## 6. Interface / Contract 和 Implementation 的区别

### 这是 T0101 最重要的知识之一

```text
VectorStore (ABC)
    │
    │ 定义：能做什么（11 个方法签名 = 契约）
    ▼
Concrete Implementation（未来的 ChromaVectorStore，T0102–T0108）
    │
    │ 实现：具体怎么做（方法体里写真正的 ChromaDB 调用）
    ▼
ChromaDB（第三方数据库，真正干活）
```

|             | Contract（契约）                | Implementation（实现）      |
| ----------- | --------------------------- | ----------------------- |
| 回答的问题       | "能做什么"                      | "具体怎么做"                 |
| T0101 里的对应物 | `VectorStore(ABC)` 的 11 个签名 | **不存在**（T0102–T0108 才写） |
| 类比          | 租房合同："可以住、可以做饭"             | 房子本身：灶台、床、门锁            |
| 变化频率        | 稳定（SPEC FROZEN）             | 会随 SDK 升级而改             |

### 用 TypeScript 类比

```ts
// 契约：只说"能做什么"
interface Storage {
  get(key: string): string;
}

// 实现：写清楚"具体怎么做"
class LocalStorageAdapter implements Storage {
  get(key: string): string {
    return window.localStorage.getItem(key) ?? "";
  }
}
```

调用方（业务代码）只依赖 `Storage`，不知道也不关心后面是 localStorage 还是 IndexedDB。DX-RAG 的业务层只依赖 `VectorStore`，不知道也不关心后面是 ChromaDB 还是别的。

### 为什么现在就要建立这个区分

因为 T0101 只做了契约。如果你带着"Phase 1 已经有个能用的向量数据库"的预期去看代码，会非常困惑——11 个方法全是空的。反过来，一旦分清契约和实现，你会发现 T0101 的任务边界极其清晰：**它只负责把契约钉死在代码里**。

---

## 7. 为什么不能直接到处调用 ChromaDB

### 🟢 入门理解

如果没有 VectorStore 这层边界，每个 Service 都直接操作 ChromaDB SDK，代码会变成：

```text
❌ 错误思维（假设没有 VectorStore）：

RetrievalService ──→ collection.query(...)     ← 直接调用 ChromaDB SDK
UploadService    ──→ collection.add(...)       ← 直接调用 ChromaDB SDK
FileService      ──→ collection.get(where=...) ← 直接调用 ChromaDB SDK
```

这就像你的 React 组件里到处写 `localStorage.setItem(...)` 而不经过任何封装。有一天要换成 IndexedDB，你得满项目找调用点。

推荐边界：

```text
✅ 推荐边界（DX-RAG 的做法）：

RetrievalService
     ↓
VectorStore（契约，11 个方法）
     ↓
Chroma implementation（T0102–T0108 实现）
```

### 🟡 项目理解：四个具体好处

| 好处        | 解释                                       | 前端类比                          |
| --------- | ---------------------------------------- | ----------------------------- |
| **维护**    | ChromaDB SDK 升级改 API，只改一个实现类，不动业务代码      | 只改 `lib/storage.ts`，不动 20 个组件 |
| **测试**    | 业务层可以 mock `VectorStore`，测试不需要真启动 ChromaDB | `jest.mock("./storage")`      |
| **隔离第三方** | 业务代码不 import chromadb，第三方库的复杂 API 不扩散    | 业务组件不直接 import axios 细节       |
| **业务层稳定** | SPEC 冻结了 11 个方法签名，业务代码建立在稳定契约上           | 稳定的 Props 类型让组件可靠             |

### 🔵 进阶阅读

这三个概念解释了"为什么这样设计更好"，当前不需要深入掌握：

- **Dependency Inversion（依赖反转）**——业务层依赖抽象（VectorStore），不依赖具体（ChromaDB）。
- **Adapter Pattern（适配器模式）**——未来的实现类就是一个"适配器"，把 ChromaDB 的 API 翻译成业务层要的 API。
- **Encapsulation（封装）**——把 ChromaDB 的实现细节关进一个类里。

详见第 21 节，第一遍可以跳过。

---

## 8. Public Boundary 与 `_collection`

### 先看 SPEC 的硬性约束

SPEC F008 设计约束第 3 条（原文）：

> **禁止**外部代码访问 `_collection` 或任何 ChromaDB 私有属性

并且 `list_chunks()` 说明中再次强调：

> **必须通过此 public interface 获取 Chunk 数据**，不得直接访问 ChromaDB 私有对象

### 什么是 `_collection`

ChromaDB SDK 内部，一个 Collection 对象内部有 `_collection` 之类的私有属性，直接暴露底层存储结构。如果业务代码写：

```python
store._collection.query(...)   # ❌ 绕过 VectorStore，直接操作 ChromaDB 内部对象
```

就绕过了第 7 节说的整条边界。

### Python 中的 `_` 命名约定

在 Python 里，名字前面的**单下划线 `_`** 是一种约定（不是语法强制）：

> "这是内部实现细节，不应该由外部模块依赖。"

类似 JS 社区 `_internalHelper()` 的命名习惯。Python 不会像 TS 的 `private` 关键字那样在编译期阻止你访问——**约定靠自觉，不靠编译器**。

### 真正的约束来自哪里

DX-RAG 中，`_collection` 不可访问**不是** Python 命名习惯决定的，而是：

1. **SPEC F008 约束 3** —— 项目级架构契约，写进 FROZEN 的产品规格；
2. **代码结构** —— 未来实现类把 `_collection` 藏在类内部，外部代码在正常路径上根本拿不到它；
3. **验收标准** —— AC-F008-03 会专门检查"所有操作通过 public interface，不访问 `_collection`"。

换句话说：`_` 只是提醒，SPEC 才是法律。

---

## 9. T0101 Public Methods 学习地图

> 基于真实代码 [vector_store.py:79-225](backend/app/core/vector_store.py#L79-L225) 和 SPEC F008 Public Interface 表。当前状态**全部是 Contract only**——只声明签名，无实现。

| Method                                   | 输入                                       | 输出                         | 一句话作用                             | 当前状态          |
| ---------------------------------------- | ---------------------------------------- | -------------------------- | --------------------------------- | ------------- |
| `create_collection(name)`                | `name: str`                              | `None`                     | 创建一个知识库（= 一个 ChromaDB Collection） | Contract only |
| `delete_collection(name)`                | `name: str`                              | `None`                     | 删除知识库及其中全部数据                      | Contract only |
| `rename_collection(old_name, new_name)`  | 两个 `str`                                 | `None`                     | 重命名知识库（只改 Collection 名字本身）        | Contract only |
| `list_collections()`                     | 无                                        | `List[str]`                | 列出所有知识库名称                         | Contract only |
| `add_texts(collection, chunks, embeddings, metadatas)` | `str` + `List[str]` + `List[List[float]]` + `List[Dict[str, Any]]` | `List[str]`（chunk_ids）     | 把文本 + 向量 + 元数据写进知识库               | Contract only |
| `search(collection, query_vector, top_k)` | `str` + `List[float]` + `int`            | `List[VectorSearchResult]` | 向量相似度检索，返回 similarity_score       | Contract only |
| `delete_by_file(collection, file_id)`    | `str` + `str`                            | `int`（删除数量）                | 按 file_id 删除一个文件的所有 chunks        | Contract only |
| `get_files(collection)`                  | `str`                                    | `List[Dict[str, Any]]`     | 从 chunk metadata 聚合出文件列表          | Contract only |
| `list_chunks(collection)`                | `str`                                    | `List[ChunkRecord]`        | 列出知识库全部 chunks（不含向量）              | Contract only |
| `get_chunk_count(collection)`            | `str`                                    | `int`                      | 知识库里的 chunk 总数                    | Contract only |
| `get_chunks_by_file(collection, file_id)` | `str` + `str`                            | `List[ChunkRecord]`        | 某文件的所有 chunks，按 chunk_index 升序    | Contract only |

### 以后谁可能会调用它们（通俗版）

| 方法组                   | 通俗场景                                     |
| --------------------- | ---------------------------------------- |
| 4 个 Collection 生命周期方法 | "新建一个知识库 / 删掉它 / 改名 / 看看有哪些知识库"（Phase 4 的 KB 管理界面） |
| `add_texts`           | 上传文档入库的最后一步："把切好、算好向量的数据写进去"（Phase 3）    |
| `search`              | 用户提问时："找出最相似的几个片段"（Phase 7/8）            |
| `delete_by_file`      | 删除一个文件（Phase 9）；入库失败回滚时清理残留（Phase 3）     |
| `get_files`           | 知识库文件列表页面（Phase 9）                       |
| `list_chunks`         | 关键词检索要遍历全部 chunk 建索引（Phase 6）            |
| `get_chunk_count`     | 判断知识库是否为空（Phase 8）                       |
| `get_chunks_by_file`  | 文件预览："按顺序把这个文件的内容拼回来"（Phase 9）           |

> 这里只点到为止。每个方法的真正实现细节（cosine、HNSW、metadata 写入等）属于 T0102–T0108，届时再学。

---

## 10. Python ↔ TypeScript 对照（只列 T0101 新增）

> Phase 0 已掌握的（`self`、`def`、`BaseModel`、`Field`、`List`/`Dict` 等）不重复展开。

| Python                                | TypeScript 类比                            | 当前项目中的含义                           |
| ------------------------------------- | ---------------------------------------- | ---------------------------------- |
| `ABC`                                 | `abstract class`（或 interface 思维）         | `class VectorStore(ABC)` = 定义契约的基类 |
| `@abstractmethod`                     | `abstract` 方法修饰符                         | "子类必须实现这个方法"                       |
| `from abc import ABC, abstractmethod` | `import { ... } from "abc"`（但 abc 是 Python 内置标准库，无需安装） | 引入抽象机制                             |
| `class X(Parent):`                    | `class X extends Parent {}`              | 继承（Phase 0 已见，这里继承 `ABC`）          |
| `List[float]`                         | `number[]`                               | 384 维向量 = 384 个 float 的列表          |
| `List[List[float]]`                   | `number[][]`                             | 一批向量（`add_texts` 的 embeddings 参数）  |
| `List[ChunkRecord]`                   | `ChunkRecord[]`                          | 返回自定义 Pydantic 模型列表                |
| `-> None`                             | `: void`                                 | 操作型方法不返回值，失败靠抛异常                   |
| `-> int`                              | `: number`                               | 返回删除数量 / chunk 总数                  |
| 函数体只有 docstring                       | ❌ JS 注释不能当函数体                            | 抽象方法没有可执行代码，docstring 兼作函数体        |
| docstring 中 `Args:` / `Returns:`      | JSDoc `@param` / `@returns`              | Google 风格文档格式（约定，非语法）              |

---

## 11. T0101 和 Phase 0 的关系

```text
Phase 0 — Project / Config / Model Foundation（T0001–T0005）
          ↓ 提供地基
T0101 — VectorStore Contract（本次）
```

### Phase 0 基础中，T0101 真正用到的

| Phase 0 产物                             | 在 T0101 中的真实使用                           |
| -------------------------------------- | ---------------------------------------- |
| `backend/app/core/` 目录 + `__init__.py` | 新文件 `vector_store.py` 就放在这个 package 里，import 路径 `app.core.vector_store` |
| Pydantic `BaseModel` + `Field`（T0005）  | `ChunkRecord` 和 `VectorSearchResult` 都继承 `BaseModel`，每个字段用 `Field(description=...)` |
| `typing` 类型标注习惯                        | `List`、`Dict`、`Optional`、`Any` 贯穿整个文件    |
| 模块级 docstring 风格                       | 文件头部 docstring 与 `main.py`、`schemas.py` 风格一致 |

### 没有直接使用的（不要硬关联）

| Phase 0 产物                        | 情况                                       |
| --------------------------------- | ---------------------------------------- |
| `models/schemas.py` 的 16 个 API 模型 | T0101 定义的是**存储层内部**模型（`ChunkRecord` 等），与 API 层模型互相独立 |
| `core/config.py` 的 `settings`     | T0101 纯声明签名，不需要任何配置；T0102 才会用到 `CHROMA_PERSIST_DIR` |
| `core/errors.py` 的 `AppError`     | 没有方法体，也就没有抛错的地方；T0102+ 才可能抛出错误码          |
| `api/router.py`                   | T0101 不涉及 API 层                          |

---

## 12. T0101 和 T0102 的关系

```text
T0101（✅ 已完成）            T0102（✅ DONE — 11 个方法中已实现 3 个）
定义 boundary / contract  →  基于这个 contract 继续实现
```

以 [TASKS.md](docs/TASKS.md) 中真实的 T0102 为准：

| 维度       | T0102 实际内容                               |
| -------- | ---------------------------------------- |
| **做什么**  | 创建 ChromaDB 实现类，实现 11 个方法中的 3 个：`create_collection`、`list_collections`、`delete_collection` |
| **依赖**   | T0101（契约）+ T0003（config 的 `CHROMA_PERSIST_DIR`） |
| **关键配置** | ChromaDB PersistentClient + cosine 距离 + HNSW 索引 |
| **明确不做** | rename（→T0103）、add_texts（→T0104）、search（→T0105）等 |
| **验收**   | 能真正创建/列出/删除 Collection；AC-F008-03（不暴露 `_collection`） |

也就是说，T0102 拿 T0101 的图纸开始盖第一层：**让"知识库"这个概念在磁盘上真实存在**。（更新：T0102 已完成——实现细节见第 22–35 节。）

---

## 13. 当前阶段只需要掌握的 5 件事

1. **我能解释 VectorStore 大概是什么** —— 它是"所有向量数据操作的统一契约入口"，不是 ChromaDB 本身。
2. **我能区分 contract 和 concrete implementation** —— T0101 写了契约（11 个方法签名），具体实现是 T0102–T0108 的事。
3. **我知道 T0101 尚未真正实现完整 ChromaDB 行为** —— 现在写不进也查不出任何数据。
4. **我能大致读懂 T0101 的 Python method signature** —— `def search(self, collection: str, query_vector: List[float], top_k: int) -> List[VectorSearchResult]` 能翻译成 TS 签名。
5. **我知道业务代码为什么不应该访问 ChromaDB 私有实现**（`_collection`）—— SPEC F008 约束 3 的硬性规定 + 第 7 节的四个好处。

---

## 14. 现在可以暂时不懂

> 以下内容**不会阻止你继续 T0102**。遇到再查即可。

| 暂时不懂的                                    | 为什么现在不用管                                |
| ---------------------------------------- | --------------------------------------- |
| Dependency Inversion 深层理论                | 知道"业务层依赖抽象"这个结论就够用了                     |
| Adapter Pattern 完整定义                     | T0102+ 实现时自然会看到实例                       |
| Python ABC 底层机制（metaclass、`__isabstractmethod__`） | 会用它，不需要知道它怎么造出来的                        |
| ChromaDB internals（HNSW 索引、cosine 具体算法）  | T0102 实现时对照 SPEC 学，现在学会忘                |
| 多数据库架构 / Milvus                          | v1 明确不做（SPEC out of scope），知道"预留了可能性"即可 |
| Python Protocol（TASKS 提到的 ABC 替代方案）      | 项目选择了 ABC，Protocol 暂不出现                 |
| 高级类型系统（TypeVar、Generic）                  | 当前代码没有用到                                |

---

## 15. T0101 代码阅读路线

> 不要一次读完全部代码。按这个顺序，每个文件只看指定的部分。

### 第 1 个文件：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)（T0101 时 226 行，T0102 后 319 行）

**第一遍只看**：
- 第 20–23 行：import 区域（认识 `abc` 来自标准库）
- 第 79–121 行：`VectorStore(ABC)` 类声明 + Collection 生命周期 4 个方法
- 第 144–163 行：`search()` 方法

**暂时跳过**：`ChunkRecord` / `VectorSearchResult` 的 Field description 全文；每个方法的 docstring 细节。

**如果能解释下面这件事，就算看懂**："这个文件定义了哪两类东西（数据模型 + 抽象方法）？为什么 226 行里没有一行真正操作 ChromaDB 的代码？"

### 第 2 个文件：[docs/SPEC.md](../../docs/SPEC.md) — F008 节（第 894–997 行）

**第一遍只看**：4 条设计约束（第 910–914 行）；Public Interface 表（第 916–930 行）。

**暂时跳过**：Metadata Schema 的 9 个字段细节、三个 AC 的 Given/When/Then。

**如果能解释下面这件事，就算看懂**："SPEC 为什么把 `_collection` 的禁令写成设计约束？`search()` 返回的分数叫什么、范围是多少？"

### 第 3 个文件：[docs/SPEC.md](../../docs/SPEC.md) — Section 7.1（第 2228–2235 行）

**第一遍只看**：5 条身份设计原则。

**如果能解释下面这件事，就算看懂**："`file_id` 和 `file_name`，谁是身份、谁是显示名？为什么？"

### 第 4 个文件：[docs/TASKS.md](../../docs/TASKS.md) — Phase 1（第 323–669 行）

**第一遍只看**：T0101 的 Implementation Scope / Out of Scope（第 339–359 行）；T0102 的 Goal 和 Dependencies（第 375–388 行）。

**暂时跳过**：T0103–T0108 的细节。

**如果能解释下面这件事，就算看懂**："T0102 将实现 11 个方法中的哪 3 个？它依赖什么？"

### 第 5 个文件：[docs/learning/python-for-frontend-dev.md](./python-for-frontend-dev.md) — 第 9 节

**第一遍只看**：第 9 节"Abstract Class / Interface 思维"。

**如果能解释下面这件事，就算看懂**："Python 用什么机制表达 TS 里的 `abstract class`？"

---

## 16. 常见错误

> 从初学者的角度，列出最容易踩的 5 个坑。

### 错误 1：把 abstract method 当成已经实现

```python
store = VectorStore()      # ❌ TypeError: Can't instantiate abstract class
```

看到 11 个方法都"写好了"，就以为数据库功能可用。**定义方法 ≠ 能运行**。当前阶段唯一能做的验证就是 import 成功。

### 错误 2：业务代码直接访问 `_collection`

```python
class MyService:
    def __init__(self, store):
        self.col = store._collection   # ❌ 违反 SPEC F008 约束 3
```

`_` 前缀是"内部实现"的约定，SPEC 把它升级成了硬性约束。即使 Python 不报错，这也违反项目契约，AC-F008-03 会检查。

### 错误 3：为未来数据库提前设计复杂 Factory

```python
# ❌ 过度设计（v1 不需要）
class VectorStoreFactory:
    def create(backend: str) -> VectorStore:
        if backend == "chromadb": ...
        elif backend == "milvus": ...   # v1 明确不做 Milvus
```

SPEC 明确 Milvus 是 out of scope。抽象边界保留"可能性"就够了，不需要现在就写多后端切换逻辑。

### 错误 4：不理解 self

```python
def create_collection(self, name: str) -> None:   # self 是显式参数
```

Python 的 `self` ≈ `this`，但必须**显式写在参数列表第一位**，方法内访问属性也必须 `self.xxx`。TS 里 `this` 不需要写。这是看 Python 方法签名时最常见的困惑点。

### 错误 5：把 Python type hint 当成 TS 完全相同的类型系统

```python
def search(self, collection: str, query_vector: List[float], top_k: int) -> List[VectorSearchResult]:
```

TS 类型错误会**阻止编译**；Python type hint 运行时**基本不检查**（主要服务 IDE 和类型检查器）。所以"签名正确"不等于"调用不会出错"——真正守住契约的是 ABC 的实例化检查，而不是类型系统。

---

## 17. T0101 调用 / 架构图

```text
┌──────────────────────────────────────┐
│ Future Services                      │
│   IngestService    (Phase 3)         │
│   Retrievers       (Phase 6/7)       │  ← Future Task（尚未实现）
│   QAService        (Phase 8)         │
│   File/KB APIs     (Phase 4/9)       │
└──────────────────┬───────────────────┘
                   │ 只认识这 11 个方法
                   ▼
┌──────────────────────────────────────┐
│ VectorStore (ABC)                    │  ← T0101 ✅ DONE（仅契约）
│ 11 个 @abstractmethod 签名           │
│ 无任何实现代码                        │
└──────────────────┬───────────────────┘
                   │ 继承 + 实现全部 11 个方法
                   ▼
┌──────────────────────────────────────┐
│ Concrete Store                       │  ← Future Task（T0102–T0108）
│ 如：ChromaVectorStore                │
│ 内部持有 ChromaDB client             │
└──────────────────┬───────────────────┘
                   │ SDK 调用（只发生在实现类内部）
                   ▼
┌──────────────────────────────────────┐
│ ChromaDB                             │  ← Future Task（T0102 起引入）
│ 持久化目录：chroma_db/               │
└──────────────────────────────────────┘
```

一句话读图：**上层只认契约，下层才碰数据库；当前只有最中间那一层（契约）存在。**

---

## 18. 5 道基础自测题

> 第一遍难度，先自己想，不要急着看答案（答案在第 20 节复习卡里能找到线索）。

**Q1**：VectorStore 是什么？它和 ChromaDB 是什么关系？

**Q2**：interface / contract 和 implementation 有什么区别？T0101 里谁扮演 contract、谁扮演 implementation？

**Q3**：Python 的 `ABC + @abstractmethod` 是干什么的？如果未来的实现类漏掉一个方法，会发生什么？

**Q4**：为什么业务代码不能写 `store._collection.query(...)`？`_` 前缀在 Python 里意味着什么？真正的约束来自哪里？

**Q5**：T0101 到底完成了什么？**今天**（T0102 未开始时）能不能用代码往 ChromaDB 里写一条数据？

---

## 19. 3 个小练习

> 都不修改正式代码。

### 练习 1：把 Python abstract method 翻译成 TypeScript interface

把下面两个真实的 Python 签名翻译成 TS interface 方法：

```python
def create_collection(self, name: str) -> None: ...

def search(self, collection: str, query_vector: List[float], top_k: int) -> List[VectorSearchResult]: ...
```

提示：`self` 不需要翻译；`-> None` → `void`；`List[float]` → `number[]`。

### 练习 2：自己画 VectorStore → ChromaDB 的关系图

不看第 17 节，自己画出四层关系（Future Services → VectorStore → Concrete Store → ChromaDB），并在每层标注当前实现状态（DONE / Future Task）。完成后对照第 17 节。

### 练习 3：判断代码是否有问题

阅读以下代码，判断哪里有问题、为什么：

```python
class KeywordRetriever:
    def __init__(self, store):
        self._collection = store._collection      # ← 这里

    def build_index(self):
        all_data = self._collection.get()          # ← 和这里
```

提示：从三个角度想——SPEC 约束、抽象边界、测试难度。

---

## 20. T0101 快速复习卡

> 3 分钟看完。

### 一句话

> T0101 定义了 VectorStore 抽象契约（11 个方法签名），为所有 ChromaDB 操作建立唯一的 public interface，但没有实现任何数据库操作。

### 5 个关键词

1. **ABC** — Python 抽象基类，`class VectorStore(ABC)` 声明契约
2. **@abstractmethod** — "子类必须实现"的方法标签
3. **contract** — 11 个方法签名 = 业务层与存储层之间的唯一契约
4. **`_collection`** — SPEC 禁止外部访问的 ChromaDB 私有属性
5. **similarity_score** — `search()` 对外的统一分数：`clamp(1.0 - raw_distance, 0.0, 1.0)`，越大越相似

### 最重要关系

```text
业务层 (Future) → VectorStore (ABC) → 具体实现 (Future) → ChromaDB (Future)
                      ↑
                  只有这一层今天存在
```

### 3 个易混淆点

1. **VectorStore(ABC) vs 未来的具体实现类** —— 前者是契约（不能 new），后者是干活的人（T0102+ 才有）。
2. **similarity_score vs raw distance** —— 前者对外（越大越相似），后者只在 ChromaDB 内部（越小越相似）；转换发生在 `search()` 内部。
3. **"方法已声明" vs "功能已实现"** —— 11 个方法都"存在"，但当前没有一个能真正执行。

### 当前实现进度

| 事项                                | 状态                             |
| --------------------------------- | ------------------------------ |
| T0101：定义 ABC + 2 个数据模型 + 11 个方法签名 | ✅ DONE                         |
| T0101：任何 ChromaDB 实际操作            | ⬜ 不在 T0101 范围内                 |
| T0102：collection 生命周期（3/11 方法）    | ✅ DONE（见第 22–35 节）             |
| T0103–T0108：具体实现（其余 8/11 方法）      | ✅ DONE（见第 36 节起）               |
| T0101 当时能用 VectorStore 存取数据吗      | ❌ 不能（当时；现 11/11 全部真实，见第 36 节起） |

---

## 21. 🔵 进阶阅读

> 当前第一遍学习可以跳过，以后再回来。以下内容不影响继续 T0102。

### Dependency Inversion（依赖反转）

业务模块依赖抽象（`VectorStore`），而不是具体（`ChromaVectorStore`）。依赖方向从"高层 → 低层"反转为"高层 → 抽象 ← 低层"。

```text
IngestService ──→ VectorStore (抽象) ←── ChromaVectorStore (低层)
```

好处：低层（ChromaDB 实现）可以更换而不影响高层。SOLID 原则中的 "D"。

### Adapter Pattern（适配器模式）

未来的 `ChromaVectorStore` 就是一个适配器：把 ChromaDB SDK 的 API（`collection.query()` 返回 distance）翻译成业务层要的 API（`search()` 返回 `VectorSearchResult` + similarity_score）。适配器的价值在于**翻译**——两边的语言（distance 语义 vs similarity 语义）互不渗透。

### Abstraction Boundary 的设计取舍

为什么是 11 个方法而不是更少（比如只留 `search` + `add_texts`）？因为 DX-RAG 有三条数据路径：

- 写入路径（add_texts / delete_by_file）
- 查询路径（search / list_chunks / get_chunk_count）
- 文件管理路径（get_files / get_chunks_by_file）

边界的设计原则：**只暴露数据路径真正需要的操作**，既不漏（漏了业务层就得绕过边界），也不多（多了会把实现细节推给业务层）。未来换 Milvus 时，新实现类必须完整复刻这 11 个语义。

### Testability（可测试性）

有 ABC 时，单元测试可以用 `Mock(spec=VectorStore)` 替代真实数据库；没有 ABC 时，每个测试都要启动一个真实 ChromaDB 实例。抽象边界是"可测试架构"的入场券。

### Future Replacement（未来替换）

SPEC F008 约束 4："VectorStore abstraction 为未来 Milvus 扩展保留接口一致性"。注意措辞——是"保留一致性"（v1 只写 ChromaDB），不是"现在就实现多后端"。换数据库时的工作量 = 实现一个新的 `VectorStore` 子类 + 换一个配置，业务代码零改动。

### Python ABC Internals（仅供好奇）

- `ABC` 的本质是一个 metaclass（`ABCMeta`）——它让类的元类型变为 `ABCMeta`。
- `@abstractmethod` 实际做的事：给函数对象设置 `__isabstractmethod__ = True` 标记。
- 实例化时，`ABCMeta` 检查类中所有带标记的方法是否已被子类覆盖，未覆盖则抛 `TypeError`。
- 因此：抽象性来自 decorator 标记，与方法体写什么（`pass` / `...` / docstring）无关。

---

---

## T0102 部分（追加）

> 以下第 22–35 节为 T0102 完成后的追加内容。T0102 = ChromaDB 初始化 + Collection 创建/列出/删除。真实代码：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 236–319 行。

---

## 22. T0102 到底解决了什么问题

### 一句话

T0101 画了图纸（contract），T0102 开始盖第一层：**让"知识库"这个概念第一次在磁盘上真实存在**。

### 建立在 T0101 哪些基础上

| 基础                      | 谁提供的                                     | T0102 怎么用                                |
| ----------------------- | ---------------------------------------- | ---------------------------------------- |
| 11 个方法签名（契约）            | T0101 的 `VectorStore(ABC)`               | `ChromaVectorStore` 继承它，11 个方法全部"定义"（3 个真实 + 8 个占位） |
| 2 个数据模型                 | T0101 的 `ChunkRecord` / `VectorSearchResult` | T0102 暂时还没用到（T0104/T0105/T0108 才会用），但文件里已就绪 |
| `_collection` 禁令等边界规则   | SPEC F008 约束 1–4                         | T0102 用 `self._client` 落地（见第 28 节）       |
| `CHROMA_PERSIST_DIR` 配置 | Phase 0 的 config.py（T0003）               | `__init__` 里读它决定数据库落盘位置                  |

### T0102 实际增加了什么能力

| 能力          | 之前（T0101 后）                    | 现在（T0102 后）                            |
| ----------- | ------------------------------ | -------------------------------------- |
| 实例化一个 store | ❌ `VectorStore()` 直接 TypeError | ✅ `ChromaVectorStore()` 可以             |
| 创建知识库       | ❌ 无任何 chromadb 代码              | ✅ `create_collection("test")` 真实在磁盘上创建 |
| 列出知识库       | ❌                              | ✅ `list_collections()` 返回真实存在的名字       |
| 删除知识库       | ❌                              | ✅ `delete_collection("test")` 真实删除     |

### T0102 仍然没有实现什么

T0102 完成时曾有 8 个方法调用即抛 `NotImplementedError`；T0103 已把其中的 `rename_collection` 变成真实实现（见第 36 节起），T0104 / T0105 又点亮了 `add_texts` / `search`（见第 50 节起），T0106–T0108 完成了最后 5 个（见第 78 节起）。**现在 11 个方法全部真实，0 个占位。**

所以 T0102 完成当时：**不能写入数据、不能检索**，能做的只有"知识库（collection）的增删查改名"。⚠️ 更新：写入 / 检索 / 删除 / 文件列表 / 计数已全部点亮（T0104–T0108，见第 50 节起）——这句话记录的是 T0102 完成时的状态。

### 明确区分两个词

| 词                                        | 含义        | T0102 中的对应物        |
| ---------------------------------------- | --------- | ------------------ |
| contract / abstraction                   | "能做什么"的约定 | T0101 的 11 个签名（没变） |
| concrete implementation / actual behavior | "真的做了"的行为 | T0102 新增的 3 个真实方法体 |

⚠️ 最容易误判的点：`ChromaVectorStore` 里 11 个方法都"存在"，但 T0102 完成时其中 8 个只是占位（T0108 起 11 个全部真实，0 个占位）。**方法存在 ≠ 功能可用。**

---

## 23. 以前端开发者的方式理解 T0102

### TS 心智模型（不是 DX-RAG 真实代码）

```ts
// T0101 定义的契约
abstract class VectorStore {
  abstract createCollection(name: string): void;
  abstract deleteCollection(name: string): void;
  abstract listCollections(): string[];
  abstract search(collection: string, queryVector: number[], topK: number): VectorSearchResult[];
  // ... 共 11 个
}

// T0102 写的实现
class ChromaVectorStore extends VectorStore {
  private client = new ChromaDB.PersistentClient({ path: settings.CHROMA_PERSIST_DIR });

  createCollection(name: string): void {
    this.client.createCollection(name, { metadata: { "hnsw:space": "cosine" } });
  }

  deleteCollection(name: string): void {
    this.client.deleteCollection(name);
  }

  listCollections(): string[] {
    return this.client.listCollections().map(col => col.name);
  }

  // 其余 8 个：TS 里也必须写出来（比如 throw new Error("TODO")），
  // 否则编译不过。Python 同理——实例化时报 TypeError。
}
```

### T0102 涉及的概念，用你熟悉的语言先过一遍

| T0102 用到的          | Python 写法                                | TS / Node 类比                             | 类比不完全等价之处                                |
| ------------------ | ---------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| class inheritance  | `class ChromaVectorStore(VectorStore)`   | `class X extends Y`                      | 语法位置不同（括号 vs `extends`），含义相同             |
| 实现抽象方法             | 子类里定义同名方法                                | 重写方法体                                    | Python 不需要 `override` 之类的标记；"实现了"的标准就是"子类里定义了同名方法" |
| constructor        | `def __init__(self) -> None:`            | `constructor()`                          | 相同（Phase 0 已学过）                          |
| third-party SDK 包装 | 类内部持有 `chromadb.PersistentClient`        | 类内部持有 SDK client 实例                      | 相同                                       |
| adapter（适配器）       | 把 chromadb 的 API 翻译成 VectorStore 的 11 个方法 | `LocalStorageAdapter implements Storage` | 模式相同                                     |

### 一句话类比

T0102 = 写一个 `LocalStorageAdapter implements Storage`：把第三方 SDK（localStorage / chromadb）的调用收进一个类里，业务代码只看到接口，永远不碰 SDK。

---

## 24. T0102 真实代码阅读

> 只挑 4 段最重要的代码。全部来自 [backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 236–319 行，格式与第 4 节一致（片段编号接续）。

---

### 代码片段 5：类声明 + `__init__`（第 236–252 行，节选）

**Python 原代码**

```python
class ChromaVectorStore(VectorStore):
    """ChromaDB-backed VectorStore implementation.

    SPEC F008 ChromaDB Configuration:
      - Similarity metric: cosine (``hnsw:space=cosine``)
      - Index type: HNSW (ChromaDB default)
      - Persistence directory: ``settings.CHROMA_PERSIST_DIR``
    """

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )
```

**🟢 Python 语法怎么读**

- `class ChromaVectorStore(VectorStore):` — 定义类，继承 T0101 的 ABC。类名读作 "Chroma 版 的 VectorStore"。
- `def __init__(self) -> None:` — 构造函数（Phase 0 学过 ≈ `constructor`）。写 `ChromaVectorStore()` 时自动执行。
- `self._client = chromadb.PersistentClient(path=...)` — 创建 ChromaDB SDK 的客户端对象，保存到实例属性 `_client` 上。
- `path=settings.CHROMA_PERSIST_DIR` — 关键字传参：明确指定参数名（≈ JS 里 `new Client({ path })` 的可读性）。
- `settings` 来自第 26 行的 `from app.core.config import settings`（Phase 0 的 T0003 产物，一个全局配置单例）。
- `_client` 的 `_` 前缀：命名约定"私有，外部不要碰"（第 8 节已讲过：约定靠自觉，SPEC 才是法律）。

**🟢 TypeScript / Node.js 类比**

```ts
class ChromaVectorStore extends VectorStore {
  private client = new ChromaDB.PersistentClient({ path: settings.CHROMA_PERSIST_DIR });
}
```

差异：TS 的 `private` 编译期强制（外部访问直接编译报错）；Python 的 `_` 只是名字约定，运行时照样能 `store._client`——DX-RAG 里真正禁止它的是 SPEC F008 约束 3。

**🟡 在 DX-RAG 中的作用**

这是 SPEC F008"ChromaDB 配置"的落地第一行：`PersistentClient` = 数据持久化到磁盘目录 `chroma_db/`，服务重启数据不丢（对比"内存版"的 `Client`，进程一关就没了）。整条 RAG 链路的数据最终都沉淀在这个 client 上。

**🟢 现在只需要记住什么**

1. `ChromaVectorStore` 继承 `VectorStore`——这是全项目第一个"实现契约"的类。
2. `self._client` 是它与 ChromaDB SDK 之间的**唯一通道**。
3. `PersistentClient` → 数据落盘，重启不丢。

---

### 代码片段 6：`create_collection`（第 256–265 行）

**Python 原代码**

```python
    def create_collection(self, name: str) -> None:
        """Create a ChromaDB collection with cosine distance / HNSW index.

        Args:
            name: Collection name (knowledge base name).
        """
        self._client.create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
```

**🟢 Python 语法怎么读**

- **没有 `@abstractmethod`**——装饰器只在父类声明时用一次；子类这里直接写同名方法，就是"实现"。
- 方法体只有一行调用：把活委托给 `self._client` 的同名方法。这就是 adapter 的微观形态：VectorStore 的 `create_collection` 被"翻译"成 ChromaDB 的 `create_collection`。
- `name=name` — 左边的 `name` 是参数名，右边的 `name` 是方法的入参变量（名字恰好相同，不是循环）。
- `metadata={"hnsw:space": "cosine"}` — dict 字面量（≈ JS 对象字面量 `{ "hnsw:space": "cosine" }`）。
- 没有 `return` → 隐式返回 `None`（对应签名里的 `-> None`）。

**🟢 TypeScript / Node.js 类比**

```ts
createCollection(name: string): void {
  this.client.createCollection(name, { metadata: { "hnsw:space": "cosine" } });
}
```

几乎逐行等价。

**🟡 在 DX-RAG 中的作用**

- `cosine` = 相似度度量方式（两个向量的夹角越小越相似）——SPEC F008 明确要求，而且 ChromaDB 的度量在创建时选定、之后不能改，所以必须写死在创建调用里。
- HNSW = 索引类型，ChromaDB 默认值，这里不用显式传（docstring 里提到它只是呼应 SPEC）。
- 每个知识库 = 一个 collection（SPEC 约束 1），所以这个方法是未来"新建知识库"界面（Phase 4）的底层动作。

**🟢 现在只需要记住什么**

1. 实现 = 委托：把活转给 `self._client`。
2. `cosine` 是 SPEC 要求，创建时写死。
3. 子类实现抽象方法**不需要**任何装饰器。

---

### 代码片段 7：`list_collections` 的 list comprehension（第 275–281 行）

**Python 原代码**

```python
    def list_collections(self) -> List[str]:
        """List all existing collection names.

        Returns:
            List of collection names.
        """
        return [col.name for col in self._client.list_collections()]
```

**🟢 Python 语法怎么读**

- `[表达式 for 变量 in 可迭代对象]` — **list comprehension（列表推导式）**，Python 表达"把 A 转成 B 列表"的惯用写法。读作："对 `list_collections()` 返回的每个 `col`，取出 `col.name`，组成新列表。"
- `col` 是循环变量名（随意命名）；`col.name` 是属性访问（≈ `col.name`）。

**🟢 TypeScript / Node.js 类比**

```ts
return this.client.listCollections().map(col => col.name);
```

完全等价。差异只是：TS 用方法 `.map()`，Python 用语法（写进方括号里）。

**🟡 在 DX-RAG 中的作用**

ChromaDB 的 `list_collections()` 返回的是**Collection 对象列表**（对象里有 id、metadata 等一堆东西），而 VectorStore 契约只要求 `List[str]`。这行代码做了"翻译"：剥掉 SDK 对象，只留业务要的名字。为什么不能直接把对象返出去？两个原因：契约签的是 `List[str]`；对象会泄露 ChromaDB 类型到业务层（破坏第 7 节讲的隔离）。

**🟢 现在只需要记住什么**

1. `[f(x) for x in xs]` ≈ `xs.map(f)`——T0102 最重要的新语法。
2. 翻译发生在边界内部，业务层永远只拿到 `List[str]`。

---

### 代码片段 8：`NotImplementedError` 占位 stub（T0102 完成时第 285–286 行）

> 更新：此片段以 `rename_collection` 为例讲解占位模式——它在 T0102 完成时确实是 stub；T0103 已将其替换为真实实现（见第 36 节起）。**占位模式在 T0108 后已成为历史**：11 个方法全部替换为真实实现，当前代码里已没有任何 `raise NotImplementedError` 的 stub。想回看这个历史片段对应的真实实现，看 [vector_store.py:284-301](backend/app/core/vector_store.py#L284-L301)（T0103 的 `rename_collection`）；原第 385–400 行的 `delete_by_file` stub 也已由 T0106 换成真实实现（见第 78 节起）。

**Python 原代码**（T0102 完成时的样子）

```python
    def rename_collection(self, old_name: str, new_name: str) -> None:
        raise NotImplementedError("rename_collection → T0103")
```

**🟢 Python 语法怎么读**

- `raise NotImplementedError(...)` — 抛出一个 Python **内置异常**，消息写明"这个功能属于 T0103"。
- 任何代码调用这个方法都会立刻崩溃——**这是故意的**：宁可崩，也不假装做成了。

**🟢 TypeScript / Node.js 类比**

```ts
renameCollection(oldName: string, newName: string): void {
  throw new Error("Not implemented — TODO T0103");
}
```

**🟡 在 DX-RAG 中的作用**

T0102 时 8 个未实现方法全是这种占位（第 285–318 行，每个标注对应的 Task；T0103 后剩 7 个；T0105 后剩 5 个；**T0108 后剩 0 个**）。为什么不能干脆**不写**这些方法？因为 ABC 的规则：子类必须"定义"父类全部抽象方法，否则 `ChromaVectorStore()` 直接 TypeError。所以 stub 一举两得：

1. 让类能通过 ABC 检查、成功实例化；
2. 诚实——谁提前调用就立刻崩，而不是静默返回错误结果。

T0103–T0108 每完成一个，就把对应方法的 `raise` 换成真实实现。

**🟢 现在只需要记住什么**

1. 看到 `NotImplementedError` = 这里是"以后再做"的占位。
2. T0102 完成时这 8 个方法谁调用谁崩——**方法存在 ≠ 功能可用**（T0108 起 11 个方法全部真实，0 个占位，见第 78 节起）。

---

## 25. T0102 核心对象 / 方法

### 唯一新增对象：`ChromaVectorStore`

| 问题    | 答案                                       |
| ----- | ---------------------------------------- |
| 它是什么  | `VectorStore` 的第一个 concrete implementation（ChromaDB 版） |
| 输入    | 构造无参数——落盘路径从全局 `settings` 读              |
| 输出    | 一个可实例化的 store 对象                         |
| 为什么需要 | T0101 只有契约，必须有一个"干活的人"                   |
| 谁调用它  | **目前无人调用**（业务层 Phase 3+ 才出现）；将来：IngestService、KB 管理 API、Retrievers、QA Service |
| 它调用谁  | `self._client`（chromadb.PersistentClient） |

### 3 个有真实行为的方法

| 方法                        | 输入          | 输出          | 真实行为                                     | 将来谁调用             |
| ------------------------- | ----------- | ----------- | ---------------------------------------- | ----------------- |
| `create_collection(name)` | `name: str` | `None`      | ✅ 委托 `self._client.create_collection`，带 cosine metadata | Phase 4 KB 管理 API |
| `delete_collection(name)` | `name: str` | `None`      | ✅ 委托 `self._client.delete_collection`    | Phase 4 / 9       |
| `list_collections()`      | 无           | `List[str]` | ✅ list comprehension 把对象列表翻译成名字列表        | Phase 4 KB 列表界面   |

### 占位 stub 的历史轨迹（现在 0 个）

> 更新：T0102 完成时是 8 个；T0103 已将 `rename_collection` 替换为真实实现（见第 36 节起）；T0104 / T0105 又点亮了 `add_texts` / `search`（见第 50 节起）；**T0106–T0108 完成了最后 5 个，现在 0 个占位**（见第 78 节起）。下表记录的是 T0102 当时的占位消息，作为"谁负责填这个坑"的历史账本：

| 方法                   | 当时的占位消息 | 归属 Task（现已 DONE）  |
| -------------------- | ------- | ----------------- |
| `delete_by_file`     | → T0106 | T0106 ✅（第 78 节起）  |
| `get_files`          | → T0107 | T0107 ✅（第 92 节起）  |
| `list_chunks`        | → T0108 | T0108 ✅（第 106 节起） |
| `get_chunk_count`    | → T0108 | T0108 ✅（第 106 节起） |
| `get_chunks_by_file` | → T0108 | T0108 ✅（第 106 节起） |

> 说明：`chromadb` 包不是 T0102 新增的依赖——它从 Phase 0 起就在 [requirements.txt](../../backend/requirements.txt) 里（SPEC F008 依赖），T0102 只是第一次真正 import 它。

---

## 26. T0101 → T0102 的关系

> 根据 [TASKS.md](../../docs/TASKS.md) T0101/T0102 和真实代码绘制。

```text
T0101（✅ DONE）                                T0102（✅ DONE）
定义 contract / boundary                        实现其中一部分能力

class VectorStore(ABC)         继承            class ChromaVectorStore(VectorStore)
11 个 @abstractmethod 签名    ──────────→      __init__: 创建 PersistentClient（落盘）
（函数体只有 docstring）                        create_collection  ✅ 真实实现
                                               delete_collection  ✅ 真实实现
                                               list_collections   ✅ 真实实现
                                               ─────────────────────────────
                                               rename_collection  ✅ 真实实现（→ T0103 完成）
                                               add_texts          ✅ 真实实现（→ T0104 完成）
                                               search             ✅ 真实实现（→ T0105 完成）
                                               delete_by_file     ✅ 真实实现（→ T0106 完成）
                                               get_files          ✅ 真实实现（→ T0107 完成）
                                               list_chunks        ✅ 真实实现（→ T0108 完成）
                                               get_chunk_count    ✅ 真实实现（→ T0108 完成）
                                               get_chunks_by_file ✅ 真实实现（→ T0108 完成）
```

### T0101 给 T0102 提供了什么

1. **11 个方法签名**——强制约束：漏实现任何一个，`ChromaVectorStore()` 直接 TypeError（第 5 节讲过，这次第一次真实触发这套机制）。
2. **2 个数据模型**（`ChunkRecord` / `VectorSearchResult`）——T0102 没用到，但 T0104/T0105/T0108 写方法体时直接引用，不需要新定义。
3. **SPEC F008 边界规则**——`_collection` 禁令、distance→similarity 边界等，决定了 T0102 把 client 藏成 `_client`。

### T0102 又为后续 Task 提供了什么

1. **一个可实例化的实现类**——T0103 不用再搭骨架，只需要把 `rename_collection` 的 stub 换成真实实现（含 T0103 自己的验收细节：校验 old_name 存在等）。
2. **已经连上磁盘的 `self._client`**——T0103–T0108 全部复用同一个 client，不需要每个 Task 重新初始化。
3. **一个先例**——"实现 = 委托给 `self._client` + 必要时翻译数据"的写法，后续 8 个方法都照这个模式写。

---

## 27. 当前架构中的位置

```text
┌────────────────────────────────────┐
│ Future Services                    │  ← Future Task（Phase 3+ 才出现）
│ IngestService / Retrievers / ...   │    现在没有任何调用方
└─────────────────┬──────────────────┘
                  │ 只认识 11 个方法名（现在还没人调）
                  ▼
┌────────────────────────────────────┐
│ VectorStore (ABC)                  │  ← T0101 ✅ DONE
│ 契约：11 个方法签名                 │
└─────────────────┬──────────────────┘
                  │ 继承 + 实现
                  ▼
┌────────────────────────────────────┐
│ ChromaVectorStore                  │  ← T0102–T0108 ✅ DONE
│ __init__: PersistentClient         │
│ 11 个方法全部 ✅ 真实实现           │
│ （create/delete/list/rename +       │
│   add_texts/search/delete_by_file + │
│   get_files/list_chunks/count/     │
│   get_chunks_by_file）              │
└─────────────────┬──────────────────┘
                  │ SDK 调用只发生在类内部
                  ▼
┌────────────────────────────────────┐
│ ChromaDB                           │  ← 磁盘目录 chroma_db/
│ （配置项 settings.CHROMA_PERSIST_DIR│     T0102 起真实存在
└────────────────────────────────────┘
```

### 近期依赖关系（只列已实现 + 紧邻的下一步）

```text
config.py (T0003, Phase 0) ── settings.CHROMA_PERSIST_DIR ──→ T0102 ✅
vector_store.py ABC (T0101) ── 继承 ──→ T0102 ✅
T0102 的 self._client ── 复用 ──→ T0103 ✅ → T0104 ✅ → T0105 ✅ → T0106 ✅ → T0107 ✅ → T0108 ✅
业务 Services（Phase 3+）── 调用 ──→ ChromaVectorStore（Future Task）
```

---

## 28. 为什么这样设计（只讲与 T0102 直接相关的原因）

### 1. 为什么要把 chromadb SDK 隔离进 `self._client`

业务层不 import chromadb，SDK 的复杂 API 不扩散（第 7 节的四个好处）。T0102 是第一次真实落地：**`self._client` 就是隔离的实现手段**——SDK 对象从生到死只活在这个类内部。

### 2. 为什么 `create_collection` 要传 `metadata={"hnsw:space": "cosine"}`

SPEC F008"ChromaDB 配置"明确：相似度度量 Cosine、索引 HNSW。cosine 必须在创建时指定（ChromaDB 创建后不可更改度量），所以写死在创建调用里，而不是做成参数让调用方选——选错度量会毁掉后续所有检索质量。

### 3. 为什么 `list_collections` 要做数据翻译

ChromaDB 返回 Collection 对象，契约只要 `List[str]`。翻译发生在边界内部（片段 7），业务层永远拿不到 SDK 对象——这样未来换 Milvus 时，业务层无感知（第 21 节 🔵）。

### 4. 为什么不能让其他模块直接访问 `self._client`

SPEC F008 约束 3 的硬性规定。如果 client 流出去，业务层就可能绕过 `search()` 直接 `client.query()`，然后 **raw distance 就泄露出去了**——破坏第 4 节讲的 distance → similarity 语义边界。所以隔离不只是洁癖，它保护的是检索分数的语义一致性。

> 🔵 Adapter Pattern / Dependency Inversion / Encapsulation 的完整理论在第 21 节，第一遍不需要深入。

---

## 29. Verification 到底验证了什么

先说诚实结论：**仓库里没有自动化测试脚本，也没有验证日志文件。** T0102 的验证是"手动执行 + 代码结构核对"。唯一可确认的完成记录是 [TASKS.md](../../docs/TASKS.md) 中 T0102 的 Status 已改为 DONE。

按照 TASKS.md T0102 Acceptance / Verification 的四条要求，逐条说明验证了什么、没验证什么：

```text
import 检查（结构性）
python -c "from app.core.vector_store import ChromaVectorStore"
↓ 验证了什么：类能 import、继承关系正确、11 个方法全部"定义"（漏一个 ABC 检查就过不去）
↓ 没有验证什么：不涉及磁盘、不涉及任何行为
```

```text
create / list / delete 手动验证（对应 TASKS 验收 1–3）
ChromaVectorStore().create_collection("test")
→ list_collections() 包含 "test"
→ delete_collection("test") 后 "test" 消失
↓ 验证了什么：三条路径的行为与真实代码逻辑一致（方法体确实就是 create/list/delete 的委托调用）
↓ 没有验证什么：重启后持久性、并发访问、错误输入（如重复创建同名 collection 会怎样）——
    仓库中没有留下这些验证执行过的记录
```

```text
AC-F008-03 私有属性隔离（结构性验证）
↓ 验证了什么：代码层面外部唯一入口是 ChromaVectorStore 的公开方法；_client 是类内部私有属性，
    ChromaDB 对象不会出现在任何方法签名或返回值里
↓ 没有验证什么：未来业务代码会不会违规——要等 Phase 3+ 的代码审查和最终 AC 审计（TASKS Section 19）
```

⚠️ 由于没有找到真实执行过的验证输出，以上只描述"验证结构"，**不虚构 PASS 结果**。你可以自己在 [vector_store.py:236-319](backend/app/core/vector_store.py#L236-L319) 对照验收标准逐条核对。

---

## 30. T0102 代码阅读路线

### 第 1 个文件：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)（319 行）

**第一遍只看**：
- 第 20–26 行：import 区域——对比 T0101 时新增了 `import chromadb`（第 23 行）和 `from app.core.config import settings`（第 26 行）
- 第 236–252 行：`ChromaVectorStore` 类声明 + `__init__`
- 第 256–281 行：3 个真实方法
- 第 385–400 行：`delete_by_file`——T0102 时这里是 stub，现已由 T0106 替换为真实实现（见第 78 节起；T0108 后全文件已无 stub 可看）

**暂时跳过**：类 docstring 全文。

**如果能解释下面这件事，就算看懂**："T0102 在这个文件里加了什么？3 个真实方法和 8 个 stub 的区别是什么？"

### 第 2 个文件：[backend/app/core/config.py](../../backend/app/core/config.py)（111 行）

**第一遍只看**：第 33–35 行 ChromaDB 配置节（`CHROMA_PERSIST_DIR: str = "chroma_db"`）。

**如果能解释下面这件事，就算看懂**："`PersistentClient` 的 `path` 从哪里来？想改数据目录，只需要改哪里（环境变量 / .env / 默认值）？"

### 第 3 个文件：[docs/SPEC.md](../../docs/SPEC.md) — F008 节（第 894–997 行）

**第一遍只看**：设计约束 1–4（第 910–914 行）；ChromaDB 配置三行（第 937–940 行）。

**暂时跳过**：Metadata Schema 9 字段、AC 细节（T0104+ 再细看）。

**如果能解释下面这件事，就算看懂**："SPEC 要求的 cosine / HNSW / `chroma_db` 分别落在代码的哪一行？"

### 第 4 个文件：[docs/TASKS.md](../../docs/TASKS.md) — T0102（第 375–418 行）

**第一遍只看**：Implementation Scope（第 390–396 行）和 Out of Scope（第 398–403 行）。

**如果能解释下面这件事，就算看懂**："T0102 的边界画在哪里？什么被明确排除（rename / add_texts / search / …）？"

---

## 31. T0102 阶段只需要掌握的 5 件事

1. **`ChromaVectorStore` 是什么**——`VectorStore` 的第一个真实实现类（T0102 新增；T0101 只定义契约）。
2. **真实方法 vs 占位**——create / delete / list collection 有真实行为（T0103 起 rename、T0104 起 add_texts、T0105 起 search 也有，见第 36 节起）；其余 5 个当时一调用就抛 `NotImplementedError`，现已被 T0106–T0108 全部替换为真实实现（见第 78 节起）。
3. **`self._client` 是隔离点**——chromadb SDK 只存在于这个私有属性里，SPEC 禁止它流出类外。
4. **list comprehension 能读**——`[col.name for col in ...]` ≈ JS `.map()`。
5. **T0102 完成时仍不能写入/检索数据**——"方法存在 ≠ 功能可用"，T0102 只点亮了 collection 生命周期（写入 / 检索由 T0104 / T0105 点亮，见第 50 节起）。

---

## 32. 现在可以暂时不懂（T0102 相关）

> 🔵 当前可以跳过。以下内容不影响继续 T0103。

| 暂时不懂的                                   | 为什么现在不用管                               |
| --------------------------------------- | -------------------------------------- |
| ChromaDB Collection 对象长什么样、有哪些字段        | SDK 细节，被 `self._client` 隔离，业务层永远不碰     |
| HNSW 索引的算法原理                            | ChromaDB 默认索引；SPEC 只要求"用 HNSW"，不要求理解算法 |
| cosine 的数学推导                            | 知道"cosine = 向量夹角衡量相似度，创建时写死"就够了        |
| `PersistentClient` 的线程 / 进程模型           | 业务层只用 11 个方法，不需要知道 client 内部并发         |
| chroma_db/ 目录里的底层存储文件（如 chroma.sqlite3） | 永远通过 SDK 操作，不直接碰文件                     |

---

## 33. T0102 5 道基础自测题

> 先自己想，不要急着看答案（线索在第 22–24 节）。

**Q1**：T0102 在 T0101 的基础上增加了什么？`VectorStore` 和 `ChromaVectorStore` 各自能实例化吗？

**Q2**：`ChromaVectorStore` 的 11 个方法里，几个有真实行为？T0102 刚完成时，调用 `delete_by_file` 会发生什么？为什么这些占位方法不能"干脆不写"？（提示：T0108 完成后 11 个全部真实——用"当时"和"现在"两个时间点回答）

**Q3**：`self._client` 是什么？为什么 SPEC 规定它不能流出这个类？Python 的 `_` 前缀和 SPEC 的禁令是什么关系？

**Q4**：读代码：`return [col.name for col in self._client.list_collections()]` —— 它做了什么"翻译"？等价的 JS 是什么？

**Q5**：今天（T0102 刚完成时），你能用代码往 ChromaDB 写入一条数据并检索出来吗？哪些环节还缺（各自属于哪个 Task）？

---

## 34. T0102 3 个小练习

> 都不修改正式代码。

### 练习 1：把真实 Python 方法翻译成 TypeScript

把片段 6 和片段 7 的两个真实方法翻译成一个 TS class 方法（含 private client 字段声明）。翻译后自查：Python 的 `self._client` 你用什么表达？`metadata={"hnsw:space": "cosine"}` 呢？

### 练习 2：画 `__init__` 的依赖关系图

从 `ChromaVectorStore.__init__` 出发，画出它依赖的 4 样东西，并标注每样东西来自哪个 Task：

- `VectorStore` ABC（谁定义的？）
- `chromadb` SDK（依赖何时声明的？）
- `settings.CHROMA_PERSIST_DIR`（谁提供的？）
- ChromaDB 磁盘目录（谁创建出来的？）

完成后对照第 27 节。

### 练习 3：判断这段代码是否越过 abstraction boundary

```python
class SomeService:
    def __init__(self, store: ChromaVectorStore):
        self._store = store

    def dangerous(self):
        return self._store._client.list_collections()   # ← 判断这里
```

从三个角度想：SPEC F008 约束 3、类型标注应该依赖什么（ABC 还是具体类）、未来换 Milvus 时这段代码会怎样。

---

## 35. T0102 快速复习卡

> 3 分钟看完。

### 一句话

> T0102 创建了 `ChromaVectorStore`——`VectorStore` 的第一个实现类，让知识库（collection）的创建 / 列出 / 删除第一次真实落盘。

### 5 个关键词

1. **ChromaVectorStore** — 第一个 concrete implementation
2. **PersistentClient** — 落盘 `chroma_db/` 的 SDK 客户端（重启数据不丢）
3. **`self._client`** — 私有隔离点（SPEC F008 约束 3）
4. **NotImplementedError** — T0102–T0107 期间 5 个方法的占位 stub（T0108 起全部替换完毕，现 0 个）
5. **cosine** — collection 创建时写死的相似度度量（SPEC 要求，创建后不可改）

### 最重要调用关系

```text
ChromaVectorStore.__init__ → chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
create / delete / list_collection → self._client 同名方法（委托 + 翻译）
8 个 stub → raise NotImplementedError（T0102 当时；T0108 起 0 个）
```

### 3 个易混淆点

1. **类"能实例化" ≠ "11 个方法都能用"**——ABC 只检查方法是否"被定义"，不检查是否有真实逻辑（stub 也算定义）。
2. **`NotImplementedError` ≠ 代码 bug**——是当时 T0106–T0108 的占位标记，故意为之，每个都写明了归属 Task（T0108 起全部替换完毕）。
3. **`_client` 的 `_` 只是 Python 约定**——真正禁止外部访问的是 SPEC F008 约束 3 + AC-F008-03。

### 当前实现进度

| 事项                                       | 状态                          |
| ---------------------------------------- | --------------------------- |
| T0101：契约（ABC + 11 个签名）                   | ✅ DONE                      |
| T0102：ChromaDB 初始化 + collection 生命周期（3/11 方法） | ✅ DONE                      |
| T0103：rename_collection                  | ✅ DONE（见第 36 节起）            |
| T0104：add_texts 写入                       | ✅ DONE（见第 50 节起）            |
| T0105：search 向量检索                        | ✅ DONE（见第 64 节起）            |
| T0106：delete_by_file 删除                  | ✅ DONE（见第 78 节起）            |
| T0107：get_files 文件列表                     | ✅ DONE（见第 92 节起）            |
| T0108：list_chunks / count / get_chunks_by_file | ✅ DONE（见第 106 节起）           |
| 今天能创建 / 列出 / 删除知识库吗                      | ✅ 能                         |
| 今天能重命名知识库吗（存储层）                          | ✅ 能（T0103 起）                |
| 今天能写入 / 检索数据吗（存储层）                       | ✅ 能（T0104/T0105 起，见第 50 节起） |
| 今天能删除文件 / 列文件 / 统计 chunk 吗（存储层）          | ✅ 能（T0106–T0108 起，见第 78 节起） |

---

---

## T0103 部分（追加）

> 第 36–49 节为 T0103 完成后的追加内容。T0103 = ChromaDB Rename Collection（存储层）。真实代码：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 27 行（新 import）与第 284–301 行（实现），文件现 495 行（T0103 完成时 335 行）。

---

## 36. T0103 到底解决了什么问题

### 一句话

T0103 把 `rename_collection` 从"调用即崩的占位"变成真实实现——**知识库可以改名了（存储层层面）**。

### 建立在 T0102 哪些基础上

| 基础                   | 谁提供的                                     | T0103 怎么用                     |
| -------------------- | ---------------------------------------- | ----------------------------- |
| `self._client`       | T0102 的 `__init__`                       | 直接复用，一行初始化都不用写                |
| `list_collections()` | T0102 的真实方法                              | 校验"旧名字是否存在"时直接调它（自己调用自己的公开方法） |
| stub 占位              | T0102 留下的 `raise NotImplementedError("rename_collection → T0103")` | T0103 就是来替换它的                 |

### T0103 实际增加了什么能力

| 能力          | 之前（T0102 后）                | 现在（T0103 后）                              |
| ----------- | -------------------------- | ---------------------------------------- |
| 重命名知识库（存储层） | ❌ 调用即抛 NotImplementedError | ✅ `rename_collection("old", "new")` 真实执行 |
| 旧名字不存在的报错   | ❌                          | ✅ 抛 `AppError("COLLECTION_NOT_FOUND")`（404 语义） |

### T0103 仍然没有实现什么（刻意不做）

| 不做的事                                     | 为什么不做                     | 归谁                                |
| ---------------------------------------- | ------------------------- | --------------------------------- |
| 新名字合法性校验（格式 / 重名）                        | 输入规则属于 API 层              | T0402（KB Rename API）+ T0404（名字校验） |
| 重命名 `uploads/{old_name}/` 目录             | 文件系统操作，不在存储层              | T0402                             |
| 更新所有 chunk metadata 里的 `collection_name` / `source_file` | 依赖 T0108 的 list_chunks 能力 | T0402                             |
| Invalidate keyword index                 | 依赖 Phase 6 的索引            | T0402                             |
| Rename 原子性（失败 rollback）                  | 需要上面全部步骤才有"要么全成要么全旧"可言    | T0402                             |

### 一个重要的认知：SPEC 的 8 步 ≠ 一个 Task

SPEC F001"重命名"描述的是**用户级完整流程**（8 步 + 原子性）。TASKS.md 把它拆给了不同 Task：T0103 只拿**第 3 步（重命名 ChromaDB Collection）**外加一个前置校验（旧名字存在性）；其余 7 步归 T0402，名字校验归 T0404，metadata 更新还依赖 T0108。

> 学习时看到"SPEC 写了一大段，代码只有 3 行"不要慌——先查 TASKS.md 看这个 Task 的 Implementation Scope 边界画在哪。

---

## 37. 以前端开发者的方式理解 T0103

### TS 心智模型（不是 DX-RAG 真实代码）

```ts
class ChromaVectorStore extends VectorStore {
  // T0103 实现的方法
  renameCollection(oldName: string, newName: string): void {
    if (!this.listCollections().includes(oldName)) {
      throw new AppError("COLLECTION_NOT_FOUND");   // ≈ 404 语义
    }
    this.client.getCollection(oldName).modify({ name: newName });
  }
}
```

### 两个你本来就熟悉的模式

| 模式                          | Python 写法                                | 你在前端哪见过                          |
| --------------------------- | ---------------------------------------- | -------------------------------- |
| **guard clause（先校验，不过关就抛）** | `if old_name not in ...: raise AppError(...)` | 表单提交前校验、路由守卫、函数入口参数检查            |
| **方法链调用**                   | `self._client.get_collection(old_name).modify(name=new_name)` | jQuery 链式、`array.filter().map()` |

### 一个关键差异：`not in` 不是 `!in`

Python 用 `x in list` / `x not in list` 表达"在 / 不在"，**没有** `!in` 这种写法。TS 里 `!list.includes(x)` 是"对结果取反"，Python 是"换个运算符"。详见 [python-for-frontend-dev.md](./python-for-frontend-dev.md) 第 17.5 节。

---

## 38. T0103 真实代码阅读

> 只挑 2 段。全部来自 [backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)，格式与第 4/24 节一致（片段编号接续）。

---

### 代码片段 9：`rename_collection` 实现（第 284–301 行）

**Python 原代码**

```python
    def rename_collection(self, old_name: str, new_name: str) -> None:
        """Rename a ChromaDB collection (storage-layer operation only).

        Uses ChromaDB's native rename (``Collection.modify(name=...)``).
        Validates ``old_name`` exists first (SPEC F001 error table: rename
        of non-existent KB → 404 COLLECTION_NOT_FOUND).
        """
        if old_name not in self.list_collections():
            raise AppError("COLLECTION_NOT_FOUND")
        self._client.get_collection(old_name).modify(name=new_name)
```

**🟢 Python 语法怎么读**

- `if old_name not in self.list_collections():` — `not in` 是"成员测试"运算符：问 `old_name` 是否**不在** `list_collections()` 返回的名字列表里。`in` / `not in` 是 Python 的一等运算符（TS 没有对应语法，要用 `includes()` / `indexOf` 拼出来）。
- `raise AppError("COLLECTION_NOT_FOUND")` — 抛项目自定义异常（Phase 0 学过：AppError 根据错误码查目录，得到 404 + "知识库不存在"）。`"COLLECTION_NOT_FOUND"` 这个错误码在 [errors.py](../../backend/app/core/errors.py) 的 `_ERROR_CATALOG` 第 44 行。
- `self._client.get_collection(old_name)` — 用 SDK 按名字拿到 Collection 对象。注意：这是第二次"确认存在"了——ChromaDB 的 `get_collection` 在名字不存在时也会抛**它自己的**异常，所以上面 `if` 的作用是：**赶在 SDK 抛异常之前，先用项目自己的错误码统一报错**。
- `.modify(name=new_name)` — 链式调用：拿到 Collection 对象后直接调它的 `modify` 方法改名字。
- 整个方法体只有 3 行逻辑：**校验 → 拿对象 → 改名字**。

**🟢 TypeScript / Node.js 类比**

```ts
renameCollection(oldName: string, newName: string): void {
  if (!this.listCollections().includes(oldName)) {
    throw new AppError("COLLECTION_NOT_FOUND");
  }
  this.client.getCollection(oldName).modify({ name: newName });
}
```

几乎逐行等价。唯一语法差异：Python 用 `not in` 运算符，TS 用 `!...includes(...)`。

**🟡 在 DX-RAG 中的作用**

- 这是 SPEC F001 8 步重命名流程中"第 3 步：重命名 ChromaDB Collection"的落地，且严格**只**做这一步（其余 7 步是 T0402 的事——第 36 节有对照表）。
- 校验先行保证：给一个不存在的旧名字，调用方拿到的是项目统一的 `COLLECTION_NOT_FOUND`（404 语义），而不是 ChromaDB SDK 自己的异常——**错误语义不泄露 SDK 细节**。
- 用 ChromaDB 原生 rename（modify）而不是"删了再建"：collection 里已有的 chunks / 向量 / metadata 全部保留，只改名字。删了再建 = 数据全丢。

**🟢 现在只需要记住什么**

1. 三行结构：校验（`not in`）→ 抛错（AppError）→ 原生 rename（modify）。
2. `not in` ≈ `!list.includes(x)`。
3. 改名 ≠ 删了重建；native rename 保留全部数据。

---

### 代码片段 10：新 import（第 27 行）

**Python 原代码**

```python
from app.core.errors import AppError
```

**🟢 Python 语法怎么读**

和 Phase 0 学过的 `from X import Y` 完全一样：从 `app.core.errors` 模块导入 `AppError` 类。这是 vector_store.py 第一次引入 Phase 0 的错误处理模块（T0004 产物）。

**🟢 TypeScript / Node.js 类比**

```ts
import { AppError } from "../core/errors";
```

**🟡 在 DX-RAG 中的作用**

T0101/T0102 的代码不需要抛项目错误（一个纯签名、一个只有 happy path）；T0103 第一次需要"调用方给我一个不存在的名字，我要给一个有项目语义的错误"——于是第一次 import AppError。Phase 0 搭好的错误码目录，到这里第一次被真实业务代码消费。

**🟢 现在只需要记住什么**

1. T0103 让 vector_store.py 第一次依赖 Phase 0 的 errors 模块。
2. 依赖方向单向：`core.vector_store` → `core.errors`，没有环。

---

## 39. T0103 核心对象 / 方法

### 唯一有变化的方法：`rename_collection`

| 问题    | 答案                                       |
| ----- | ---------------------------------------- |
| 它是什么  | `ChromaVectorStore` 的第 4 个真实方法（collection 生命周期 4 个方法至此全部实现） |
| 输入    | `old_name: str`、`new_name: str`          |
| 输出    | `None`（失败时抛 `AppError`）                  |
| 为什么需要 | 知识库改名的存储层动作（SPEC F001 8 步中的第 3 步）        |
| 谁调用它  | 目前无人调用；将来 T0402 的 `PUT /api/collections/{name}` endpoint |
| 它调用谁  | 自家 `list_collections()`（校验）+ `self._client.get_collection(...).modify(...)`（执行） |
| 真实行为  | ✅ 有（校验 + 原生 rename）                      |

### 错误路径（新的行为）

| 输入             | 行为                                       |
| -------------- | ---------------------------------------- |
| `old_name` 存在  | ChromaDB 原生改名，数据保留                       |
| `old_name` 不存在 | `raise AppError("COLLECTION_NOT_FOUND")` → 404 / "知识库不存在" |

### Collection 生命周期 4 个方法至此全部真实

```text
create_collection  ✅ (T0102)      delete_collection  ✅ (T0102)
rename_collection  ✅ (T0103 本次)  list_collections   ✅ (T0102)
```

### 当时剩下的 5 个占位 stub（现已被 T0106–T0108 全部替换）

> 更新：T0104 / T0105 已把 `add_texts` / `search` 变成真实实现（见第 50 节起）；T0106–T0108 完成了最后 5 个（见第 78 节起），**当前代码已无 stub**。

`delete_by_file`、`get_files`、`list_chunks`、`get_chunk_count`、`get_chunks_by_file`——T0103 完成时仍是 `raise NotImplementedError`，现全部真实实现。

---

## 40. T0102 → T0103 的关系

```text
T0102（✅ DONE）                              T0103（✅ DONE）
建好 ChromaDB 连接 + 3 个生命周期方法          把第 4 个生命周期方法补成真实实现

self._client = PersistentClient(...)    →     rename_collection 复用同一个 client
list_collections() 真实实现              →     被 rename_collection 调用来做校验
                                              （类内部也走公开方法）
raise NotImplementedError 占位           →     被 3 行真实逻辑替换：
                                              校验(not in) → AppError → modify
```

### T0102 给 T0103 提供了什么

1. **现成的 `self._client`** —— T0103 一行初始化都不用写。
2. **`list_collections()` 真实实现** —— T0103 的校验直接调它，而不是再写一遍"从 SDK 拿名字列表"的逻辑。这是一个值得记住的写法：**类内部也走公开方法，不直接掏 SDK**。
3. **stub 占位约定** —— T0102 留下的 `raise NotImplementedError("rename_collection → T0103")` 标明了"下一个就是它"，T0103 顺理成章。

### T0103 又为后续 Task 提供了什么

1. **给 T0402 的存储层积木** —— T0402 的 8 步级联（改 metadata、改 uploads 目录、失效索引…）里"改 ChromaDB collection 名"这一步，直接调 `rename_collection` 即可（TASKS.md T0402 的 Dependencies 明确列出 T0103）。
2. **错误路径先例** —— 第一个"存储层方法校验失败抛项目错误码"的范例。后面 T0104–T0108 每个方法的失败路径都会照这个模式写（先校验 → AppError → 再操作）。

---

## 41. 当前架构中的位置

```text
┌────────────────────────────────────┐
│ Future: KB Rename API (T0402)      │  ← Future Task
│ PUT /api/collections/{name}        │    校验新名 → 级联 8 步 → 原子性
└─────────────────┬──────────────────┘
                  │ 将来调 rename_collection（只负责其中 1 步）
                  ▼
┌────────────────────────────────────┐
│ VectorStore (ABC)                  │  ← T0101 ✅ DONE
└─────────────────┬──────────────────┘
                  │ 继承 + 实现
                  ▼
┌────────────────────────────────────┐
│ ChromaVectorStore                  │  ← T0102–T0108 ✅ DONE
│ create ✅ delete ✅ list ✅          │
│ rename ✅ ← T0103 本次             │
│ add_texts ✅ search ✅（T0104/T0105）│
│ 其余 5 个 ✅（T0106–T0108，第 78 节起）│
└─────────────────┬──────────────────┘
                  │ get_collection(old).modify(name=new)
                  ▼
┌────────────────────────────────────┐
│ ChromaDB（chroma_db/）             │
└────────────────────────────────────┘
```

### 近期依赖关系（只列已实现 + 紧邻的下一步）

```text
errors.py 的 AppError (T0004, Phase 0) ── 错误码目录 ──→ T0103 ✅（第一次被消费）
T0102 的 self._client / list_collections ──→ T0103 ✅
T0103 的 rename_collection ──→ T0402（Future Task）
T0103 的错误路径写法 ──→ T0106–T0108 ✅（已完成；不过删除/列表类方法最终未做 collection 存在性校验，见第 81/109 节的 Pending Question）
```

---

## 42. 为什么这样设计（只讲与 T0103 直接相关的原因）

### 1. 为什么校验放在方法内部，而不是留给调用方

SPEC F001 错误表规定"知识库不存在（重命名）→ 404 `COLLECTION_NOT_FOUND`"。如果让调用方先自己查再调，每个调用方都要记得这步，漏一个就是 SDK 裸异常。把校验收进存储层方法里，**任何调用方**（现在没有，将来 T0402 和测试）都自动获得统一错误语义。

### 2. 为什么校验用 `self.list_collections()` 而不是直接掏 SDK

已经存在的逻辑不要重写（DRY），而且走公开方法意味着**边界内的一致性**：校验看到的"存在性"和执行用的 `get_collection` 来自同一个数据源。

### 3. 为什么用 ChromaDB 原生 rename（modify）而不是删了再建

Collection 里存着（将来 T0104 写入的）全部 chunks / 向量 / metadata。原生 rename 只改名字；删了再建 = 数据全丢。这是"用 SDK 提供的能力"，而不是"用 SDK 拼凑能力"。

### 4. 为什么 T0103 不顺手把 8 步级联全做了

因为 TASKS.md 的边界画在那里：metadata 更新依赖 T0108 的 list_chunks、名字校验依赖 T0404、索引失效依赖 Phase 6。**一个 Task 只点亮自己能点亮的灯**——硬做就是越界。而且"只做存储层"让这个方法职责单一：未来换 Milvus 时，这个方法的语义同样成立（校验存在 + 改名）。

> 🔵 更深的话题（级联操作的事务性、RENAME_FAILED 的 rollback 策略）属于 T0402 的学习范围，现在不用展开。

---

## 43. Verification 到底验证了什么

先说诚实结论：**与 T0102 一样，仓库里没有自动化测试脚本，也没有验证日志文件。** 唯一可确认的完成记录是 [TASKS.md](../../docs/TASKS.md) 中 T0103 的 Status 已改为 DONE。

按 TASKS.md T0103 Acceptance / Verification 的 4 条，逐条说明验证了什么、没验证什么：

```text
import 检查（结构性）
python -c "from app.core.vector_store import ChromaVectorStore"
↓ 验证了什么：类仍能 import；新增的 AppError import 没有造成循环依赖
    （core.errors 不 import vector_store，依赖方向单向，可静态确认）
↓ 没有验证什么：运行时行为
```

```text
happy path 手动验证（对应验收 1–3：改名成功、旧名消失、新名出现）
创建 "old-kb" → rename_collection("old-kb", "new-kb")
→ list_collections() 中 "old-kb" 消失、"new-kb" 出现
↓ 验证了什么：真实代码逻辑与这三条一致（方法体确实执行校验 + modify）
↓ 没有验证什么：rename 后 collection 内数据保留（T0104 还没法往里写数据，
    只能 rename 空 collection）；仓库中没有留下这些验证执行过的记录
```

```text
错误路径（对应验收 4：renaming non-existent collection raises appropriate error）
rename_collection("不存在", "whatever") → AppError("COLLECTION_NOT_FOUND")
↓ 验证了什么：代码结构上，校验失败必然 raise AppError；
    404 与"知识库不存在"来自 errors.py 目录（第 44 行），可静态确认
↓ 没有验证什么：真实运行时抛出（无测试记录）；FastAPI 最终返回 HTTP 404 的
    完整链路（要等 T0402 接上 endpoint 才能看到）
```

⚠️ 同样：以上只描述"验证结构"，**不虚构 PASS 结果**。你可以在 [vector_store.py:284-301](backend/app/core/vector_store.py#L284-L301) 对照 TASKS.md T0103 的验收标准逐条核对。

---

## 44. T0103 代码阅读路线

### 第 1 个文件：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)（现 495 行；T0103 完成时 335 行）

**第一遍只看**：
- 第 27 行：新增的 `from app.core.errors import AppError`
- 第 284–301 行：`rename_collection` 完整实现
- 第 385–400 行：T0103 完成时这里是 5 个 stub 之一（`delete_by_file`），现已由 T0106 替换为真实实现（见第 78 节起；全文件已无 stub）

**暂时跳过**：其余方法体。

**如果能解释下面这件事，就算看懂**："`rename_collection` 的三行逻辑各自干什么？`not in` 在检查什么？"

### 第 2 个文件：[backend/app/core/errors.py](../../backend/app/core/errors.py)（114 行）

**第一遍只看**：`_ERROR_CATALOG` 第 44 行（`"COLLECTION_NOT_FOUND": (404, "知识库不存在")`）和第 79–83 行的 `_get_catalog_entry`。

**如果能解释下面这件事，就算看懂**："`raise AppError("COLLECTION_NOT_FOUND")` 之后，404 和中文消息是从哪来的？"

### 第 3 个文件：[docs/SPEC.md](../../docs/SPEC.md) — F001 Detail（第 320–335 行）

**第一遍只看**：8 步重命名流程（第 320–330 行）+ 原子性要求（第 332–335 行）。

**如果能解释下面这件事，就算看懂**："8 步里 T0103 只实现了哪一步？剩下的归哪个 Task？"

### 第 4 个文件：[docs/TASKS.md](../../docs/TASKS.md) — T0103（第 421–458 行）

**第一遍只看**：Implementation Scope（第 434–439 行）和 Out of Scope（第 440–443 行）。

**如果能解释下面这件事，就算看懂**："T0103 明确不做的三件事是什么？为什么？"

---

## 45. T0103 阶段只需要掌握的 5 件事

1. **`rename_collection` 是第 4 个真实方法**——collection 生命周期 4 个方法至此全部真实（T0102 3 个 + T0103 1 个）。
2. **三行结构**——校验（`not in`）→ 抛 `AppError("COLLECTION_NOT_FOUND")` → 原生 rename（`modify`）。
3. **`not in` ≈ `!list.includes(x)`**——Python 的成员测试运算符，T0103 第一次出现。
4. **存储层只做 1/8**——SPEC 的 8 步级联，T0103 只做"改 collection 名"，其余归 T0402。
5. **错误语义统一**——调用方拿到的永远是项目错误码（404 `COLLECTION_NOT_FOUND`），不是 SDK 裸异常。

---

## 46. 现在可以暂时不懂（T0103 相关）

> 🔵 当前可以跳过。以下内容不影响继续 T0104。

| 暂时不懂的                                   | 为什么现在不用管                                 |
| --------------------------------------- | ---------------------------------------- |
| SPEC F001 的 Rename 原子性（失败 rollback）怎么实现 | 属于 T0402 的级联操作；T0103 只有单步操作，天然不会"做一半"    |
| ChromaDB `modify()` 的内部实现（并发安全等）        | SDK 能力，信任并调用即可                           |
| `AppError` 抛出去之后 FastAPI 如何变成 HTTP 404  | Phase 0 的异常处理器已搭好框架，T0402 接上 endpoint 时自然看到全链路 |
| `RENAME_FAILED`（500）错误码什么时候用            | 属于 T0402 的"部分步骤失败"场景；T0103 单步操作用不到       |
| 类内部调用自己方法在并发下的表现                        | 当前无调用方、无并发场景，T0402+ 再考虑                  |

---

## 47. T0103 5 道基础自测题

**Q1**：T0103 把哪个 stub 变成了真实实现？现在 collection 生命周期 4 个方法的实现状态分别是什么？

**Q2**：读代码：`if old_name not in self.list_collections(): raise AppError("COLLECTION_NOT_FOUND")` —— 这行在防什么？为什么用 `self.list_collections()` 而不是直接访问 SDK？

**Q3**：SPEC F001 的重命名流程有 8 步，T0103 只做了哪一步？其余 7 步归谁？为什么不"顺手"都做完？

**Q4**：`self._client.get_collection(old_name).modify(name=new_name)` 用了什么 SDK 能力？如果改成"先 delete_collection 再 create_collection(new_name)"会有什么后果？

**Q5**：`raise AppError("COLLECTION_NOT_FOUND")` 的 404 状态码和"知识库不存在"中文消息是从哪里查出来的？（提示：errors.py）

---

## 48. T0103 3 个小练习

> 都不修改正式代码。

### 练习 1：把 `rename_collection` 翻译成 TypeScript

用 TS class 方法写出等价逻辑（含错误处理）。翻译后自查：Python 的 `not in` 你用了什么表达？`AppError("COLLECTION_NOT_FOUND")` 在你的 TS 项目里大概长什么样？

### 练习 2：画 T0103 的调用关系图

画出 `rename_collection` 的调用链：它依赖谁（至少 4 个：`self.list_collections`、`AppError`、`errors._ERROR_CATALOG`、`self._client`），标注每个依赖来自哪个 Task。完成后对照第 41 节。

### 练习 3：判断这段代码有没有问题

```python
def rename_collection(self, old_name: str, new_name: str) -> None:
    # 假设有人"简化"成这样：
    self._client.get_collection(old_name).modify(name=new_name)
```

删掉了校验会发生什么？从三个角度想：错误语义（SDK 异常 vs 项目错误码）、调用方体验（T0402 拿到的异常类型）、SPEC 合规（F001 错误表）。

---

## 49. T0103 快速复习卡

> 3 分钟看完。

### 一句话

> T0103 把 `rename_collection` 从占位 stub 变成真实实现：校验旧名存在 → 统一抛 `COLLECTION_NOT_FOUND` → ChromaDB 原生改名（数据保留）。

### 5 个关键词

1. **rename_collection** — collection 生命周期第 4 个真实方法
2. **`not in`** — Python 成员测试运算符（≈ `!includes()`）
3. **AppError** — Phase 0 错误码目录第一次被真实代码消费
4. **modify** — ChromaDB 原生改名（不是删了重建）
5. **1/8 步** — T0103 只做 SPEC 8 步级联中的存储层 1 步，其余归 T0402

### 最重要调用关系

```text
rename_collection
  → self.list_collections()                      # 校验旧名存在（自家公开方法）
  → raise AppError("COLLECTION_NOT_FOUND")       # 不存在：404 语义
  → self._client.get_collection(old).modify(name=new)   # 存在：原生改名
```

### 3 个易混淆点

1. **`not in` vs `!in`** —— Python 没有 `!in`；`not in` 是一个整体运算符。
2. **"改名成功" ≠ "级联完成"** —— T0103 只改了 ChromaDB collection 名；metadata、uploads 目录、索引都没动（T0402 才做）。别把"存储层改名"当成"用户级重命名完成"。
3. **AppError 的 404 不是这行代码写出来的** —— 状态码在 errors.py 目录里查表得到，raise 时只传错误码字符串。

### 当前实现进度

| 事项                                 | 状态                          |
| ---------------------------------- | --------------------------- |
| T0101：契约（ABC + 11 个签名）             | ✅ DONE                      |
| T0102：初始化 + create / list / delete | ✅ DONE                      |
| T0103：rename_collection            | ✅ DONE（本次）                  |
| T0104：add_texts 写入                 | ✅ DONE（见第 50 节起）            |
| T0105：search 向量检索                  | ✅ DONE（见第 64 节起）            |
| T0106–T0108：其余 5 个方法               | ✅ DONE（见第 78 节起）            |
| 今天能创建 / 列出 / 删除 / 重命名知识库吗（存储层）     | ✅ 能                         |
| 今天能写入 / 检索数据吗（存储层）                 | ✅ 能（T0104/T0105 起，见第 50 节起） |
| 今天能删除文件 / 列文件 / 统计 chunk 吗（存储层）    | ✅ 能（T0106–T0108 起，见第 78 节起） |

---

> **下一步学习**：`delete_by_file` 的 stub 已由 T0106 变成真实实现——知识库能"删除"文件数据了（见第 78 节起）。（T0104 / T0105 已完成，见第 50–77 节；T0106–T0108 已完成，见第 78 节起。）

---

## T0104 部分（追加）

> 第 50–63 节为 T0104 完成后的追加内容。T0104 = add_texts 写入（存储层）。真实代码：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 303–338 行（文件现 495 行）。

---

## 50. T0104 到底解决了什么问题

### 一句话

T0104 把 `add_texts` 从"调用即崩的占位"变成真实实现——**知识库第一次能"写入"数据（存储层层面）**。写入后，T0105 的检索才第一次有东西可搜。

### 建立在 T0103 哪些基础上

| 基础                         | 谁提供的                       | T0104 怎么用                                |
| -------------------------- | -------------------------- | ---------------------------------------- |
| `self._client`             | T0102 的 `__init__`         | 直接复用，通过 `get_collection(collection)` 拿到目标 collection |
| 11 个方法签名（契约）               | T0101 的 `VectorStore(ABC)` | `add_texts` 的签名早已定死：4 个入参、返回 `List[str]` |
| F008 Metadata Schema（9 字段） | SPEC F008                  | 每个 chunk 的 metadata dict 按 9 字段写入（T0104 只"搬运"，不校验） |

### T0104 实际增加了什么能力

| 能力              | 之前（T0103 后）                | 现在（T0104 后）                      |
| --------------- | -------------------------- | -------------------------------- |
| 写入 chunk 数据     | ❌ 调用即抛 NotImplementedError | ✅ `add_texts(...)` 真实写入 ChromaDB |
| 返回写入的 chunk_ids | ❌                          | ✅ 返回 `List[str]`（按插入顺序）          |

### T0104 仍然没有实现什么（刻意不做）

| 不做的事                            | 为什么不做                                    | 归谁                 |
| ------------------------------- | ---------------------------------------- | ------------------ |
| 生成 `chunk_id`                   | identity 由上游统一管理（SPEC 7.1）               | T0307（调用方）         |
| 生成 embedding 向量                 | 嵌入模型调用是另一个子系统                            | T0202（调用方）         |
| 校验 metadata 的 9 字段是否齐全合法        | 存储层是"搬运工"，不越权当"质检员"                      | 调用方（上游）            |
| 校验 collection 是否存在（AppError 报错） | TASKS.md T0104 边界未要求；与 T0103 的"校验先行"模式不同 | 未分配（见第 53 节错误路径说明） |

### 一个新的认知：存储层的"搬运工"边界

T0103 的 rename 做了"校验 + 操作"两件事；T0104 的 add_texts **只做"搬运"**：把调用方备好的三份名单（chunks / embeddings / metadatas）原样交给 ChromaDB。为什么同样是存储层方法，职责不一样？因为**任务边界画得不一样**（TASKS.md 的 Out of Scope），不是谁粗心。学习时看到"这个方法不校验"先别急着说 bug——先查 TASKS.md 这个 Task 的边界画在哪。

---

## 51. 以前端开发者的方式理解 T0104

### TS 心智模型（不是 DX-RAG 真实代码）

```ts
class ChromaVectorStore extends VectorStore {
  // T0104 实现的方法
  addTexts(
    collection: string,
    chunks: string[],
    embeddings: number[][],
    metadatas: Record<string, any>[],
  ): string[] {
    const ids = metadatas.map(meta => meta.chunk_id);      // 从 metadata 提取 id
    this.client.getCollection(collection).add({
      ids,
      documents: chunks,
      embeddings,
      metadatas,
    });
    return ids;
  }
}
```

### 三个你本来就熟悉的模式

| 模式                    | Python 写法                                | 你在前端哪见过                              |
| --------------------- | ---------------------------------------- | ------------------------------------ |
| **bulk insert（批量插入）** | `collection.add(ids=..., documents=..., embeddings=..., metadatas=...)` | SQL 批量 INSERT / MongoDB `insertMany` |
| **三份名单按位置对齐**         | `chunks[i]` 的向量是 `embeddings[i]`，metadata 是 `metadatas[i]` | `Promise.all` 后按索引 zip；表单字段数组        |
| **map 提取字段**          | `[meta["chunk_id"] for meta in metadatas]` | `metadatas.map(m => m.chunk_id)`     |

### 一个关键差异：Python dict 取值用方括号

`meta["chunk_id"]` 的 `["chunk_id"]` 不是数组下标——是 **dict（字典）按键取值**（≈ `meta.chunk_id` / `meta["chunk_id"]`）。Python 里没有"属性名即键名"的语法糖，必须显式写 `["键名"]`。TS 里 `obj.key` 和 `obj["key"]` 都可以，Python 里只有后者；访问不存在的键会抛 `KeyError`（JS 返回 `undefined` 后炸在下一行，Python 炸得更早更直接）。

---

## 52. T0104 真实代码阅读

> 只挑 1 段（T0104 的方法体总共 8 行，一次看完）。来自 [backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 305–338 行，格式与第 4/24/38 节一致（片段编号接续）。

### 代码片段 11：`add_texts` 实现（第 305–338 行）

**Python 原代码**

```python
    def add_texts(
        self,
        collection: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> List[str]:
        """Persist chunks, embeddings, and metadata into a ChromaDB collection.

        Each chunk is stored with its 384-dim embedding and its 9-field
        metadata dict (SPEC F008 Metadata Schema).  ``chunk_id`` from the
        metadata is used as the ChromaDB document id.
        ...
        """
        ids = [meta["chunk_id"] for meta in metadatas]
        self._client.get_collection(collection).add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return ids
```

**🟢 Python 语法怎么读**

- 签名 4 个入参：`collection: str` + 三个"平行列表"。`List[List[float]]` = 二维列表（一批向量，每个向量本身是一个 float 列表）≈ `number[][]`。
- `ids = [meta["chunk_id"] for meta in metadatas]` — 第 24 节学过的 list comprehension：把 metadata 列表 map 成 id 列表。`meta` 是循环变量（每个元素是一个 dict）。
- `meta["chunk_id"]` — dict 按键取值（见第 51 节）。取出来的是字符串（UUID），不是数组下标。
- `.add(ids=..., documents=..., embeddings=..., metadatas=...)` — 4 个关键字传参（Phase 0 学过 `kwarg=` 的写法）。参数名是 ChromaDB SDK 定的：`documents` 对应我们的 `chunks`，`embeddings` 对应向量，`metadatas` 对应元数据。
- `return ids` — 返回刚写入的 id 名单，不是 `None`。为什么？见 🟡。
- 方法体一共 8 行：**提取 ids → 委托 SDK → 返回 ids**。

**🟢 TypeScript / Node.js 类比**

见第 51 节 TS 心智模型——几乎逐行等价。唯一要适应的：Python 里 `map` 是"语法"（list comprehension），`add` 的参数是"关键字传参"而不是"对象字面量"。

**🟡 在 DX-RAG 中的作用**

- 这是 SPEC F008 Metadata Schema 的落地：9 个字段（`chunk_id`、`file_id`、`file_name`、`collection_name`、`chunk_index`、`source_file`、`file_size`、`upload_time`、`ingestion_status`）随每个 chunk 一起写进 ChromaDB。T0104 不校验它们——字段对不对是上游的责任。
- `chunk_id` 被双重使用：既是 metadata 里的字段，又是 ChromaDB 的 **document id**（`ids=` 参数）。这不是重复——**id 是身份，metadata 是随身携带的信息副本**（SPEC 7.1：`chunk_id` = chunk 的不可变身份，`chunk_index` 只是排序号，`file_name` 只是显示名）。
- `return ids` 的意义：将来 IngestService（Phase 3）写入后需要知道"成功写入了哪些 chunk_id"——比如回滚失败的写入、向用户汇报进度。**存储层如实汇报结果，而不是默默完成。**

**🟢 现在只需要记住什么**

1. 三份名单（chunks / embeddings / metadatas）按位置一一对应，加上从 metadata 提取的 ids，一起交给 SDK。
2. `chunk_id` 是 ChromaDB 的 document id——身份规则（SPEC 7.1），T0104 不生成、不校验。
3. `return ids` ≠ 多余——调用方要用。

---

## 53. T0104 核心对象 / 方法

### 唯一有变化的方法：`add_texts`

| 问题    | 答案                                       |
| ----- | ---------------------------------------- |
| 它是什么  | `ChromaVectorStore` 的第 5 个真实方法（Data Operations 组第一个） |
| 输入    | `collection: str` + `chunks: List[str]` + `embeddings: List[List[float]]` + `metadatas: List[Dict[str, Any]]` |
| 输出    | `List[str]`——写入的 chunk_ids（按插入顺序）        |
| 为什么需要 | 上传文档入库的最后一步："把切好、算好向量的数据写进去"（Phase 3）    |
| 谁调用它  | 目前无人调用；将来 IngestService（Phase 3）         |
| 它调用谁  | `self._client.get_collection(collection).add(...)` |
| 真实行为  | ✅ 有（提取 ids + 委托写入）                       |

### 数据形状：三份名单 + 一份提取名单

```text
chunks     = ["文本片段1", "文本片段2", "文本片段3"]     # List[str]
embeddings = [[0.1, -0.2, ...], [...], [...]]           # List[List[float]]，每个 384 维
metadatas  = [{"chunk_id": "a1...", ...}, {...}, {...}]  # List[Dict]，每个 9 字段（F008）
                       ↓ ids = [meta["chunk_id"] for meta in metadatas]
ids       = ["a1...", "b2...", "c3..."]                 # 提取出来的名单
```

对齐约定：`chunks[0]` ↔ `embeddings[0]` ↔ `metadatas[0]` ↔ `ids[0]` 是同一个 chunk。**列表顺序就是身份对齐方式**——这个约定没有代码校验，靠调用方自觉。

### 错误路径

| 输入                   | 行为                                      |
| -------------------- | --------------------------------------- |
| collection 存在、四份名单对齐 | ✅ 写入成功，返回 ids                           |
| collection 不存在       | ❌ ChromaDB SDK 抛它自己的异常（**不是** AppError） |

> ⚠️ 观察：与 T0103 的"校验先行 → AppError"不同，T0104 没有 collection 存在性校验。按 TASKS.md T0104 边界这是"不在本 Task 范围"，但调用方拿到的是 SDK 裸异常——是否需要在后续 Task 补校验，记录为 Pending Question（见最终报告）。

### Data Operations 组第一个真实方法

```text
Collection 生命周期组（全部真实 ✅）       Data Operations 组
create / delete / list / rename         add_texts ✅ (T0104 本次)
                                        search / delete_by_file ...（→ T0105+）
```

---

## 54. T0103 → T0104 的关系

```text
T0103（✅ DONE）                              T0104（✅ DONE）
补完 Collection 生命周期（管理流）              打开数据路径（数据流）

rename_collection 校验 + 改名              →   add_texts 提取 ids + 委托写入
self._client / 委托模式                    →   复用同一个 client 和"实现 = 委托"写法
（T0103 的 AppError 校验模式               →   T0104 未沿用——边界不同，见第 50/53 节）
```

### T0103 给 T0104 提供了什么

1. **"实现 = 委托给 `self._client`"的成熟写法**——T0104 方法体 8 行，不需要任何新基础设施。
2. **"一个 Task 只做边界内的事"的先例**——T0103 只做 8 步里的 1 步；T0104 同样克制：不生成 id、不生成向量、不校验 schema。

### T0104 又为后续 Task 提供了什么

1. **给 T0105 的数据**——TASKS.md T0105 的 Dependencies 明确列出 T0104：search 的验证场景（AC-F008-01 的 10 个 chunk）必须先靠 `add_texts` 写入。
2. **给 Phase 3 的存储层积木**——IngestService 将来按"Validate → Save → Parse → Clean → Chunk → Embed → Store"的管道走，最后一步就是调 `add_texts`。

---

## 55. 当前架构中的位置

```text
┌────────────────────────────────────┐
│ Future: IngestService (Phase 3)    │  ← Future Task
│ 生成 chunk_id（T0307）、embedding（T0202）│
└─────────────────┬──────────────────┘
                  │ 将来调 add_texts(chunks, embeddings, metadatas)
                  ▼
┌────────────────────────────────────┐
│ ChromaVectorStore                  │  ← T0102–T0105 ✅ DONE
│ add_texts ✅ ← T0104 本次          │
└─────────────────┬──────────────────┘
                  │ get_collection(collection).add(...)
                  ▼
┌────────────────────────────────────┐
│ ChromaDB（chroma_db/）             │  ← chunk + 向量 + metadata 第一次落盘
└────────────────────────────────────┘
```

注意箭头上的"原料"：chunk_id 和 embedding 都是**调用方带进来的**——存储层不知道自己写入的向量是怎么算出来的。这是 T0104 最关键的架构位置认知：**它站在数据管道的末端，不参与上游加工。**

---

## 56. 为什么这样设计（只讲与 T0104 直接相关的原因）

### 1. 为什么 `chunk_id` 从 metadata 里取，而不是 `add_texts` 自己生成

SPEC 7.1 身份规则：`chunk_id` 是 chunk 的不可变身份，全系统唯一。如果每个存储实现（今天 Chroma、明天 Milvus）各生成一套 id，同一个 chunk 在不同系统里身份就乱了。**身份由上游统一签发，存储层只负责保管**——就像前端项目里 id 由服务端生成，前端 localStorage 只存不造。

### 2. 为什么 embedding 也由调用方提供

生成 embedding 要调嵌入模型（Phase 2 的 bge-small-zh-v1.5）——那是另一个子系统（T0202）。如果存储层自己偷偷调模型，存储层就同时干了三件事（算向量 + 存数据 + 管身份），违背单一职责。**add_texts 的输入必须是"已经算好的数字"。**

### 3. 为什么用 `get_collection(collection).add(...)` 而不是别的写法

ChromaDB SDK 的写入 API 挂在 Collection 对象上（先拿到 collection，再调 add）。`get_collection` 按名字拿对象——和 T0103 的 rename 同款写法，保持一致。

### 4. 为什么 `return ids` 而不是 `None`

调用方（IngestService）写入后要能**核对**：写了哪些、顺序如何、失败时删哪些。`None` 会让调用方只能自己再查一遍。返回名单是存储层的最低成本汇报。（对比 T0102 的 create/delete 返回 `None`——那些操作没有"需要汇报的身份"。）

---

## 57. Verification 到底验证了什么

先说诚实结论：**与前几个 Task 一样，仓库里没有自动化测试脚本，也没有验证日志文件。** 唯一可确认的完成记录是 [TASKS.md](../../docs/TASKS.md) 中 T0104 的 Status 已改为 DONE。

按 TASKS.md T0104 Acceptance / Verification 的三条，逐条说明验证了什么、没验证什么：

```text
验收 1：写入 3 个 chunk → 返回 3 个 chunk_ids（顺序一致）
↓ 验证了什么：返回逻辑与真实代码一致——ids 从 metadatas 提取，返回的就是提取名单
↓ 没有验证什么：仓库中没有留下"真实执行过一次写入"的记录
```

```text
验收 2：写入后能被 search 检索（T0105 完成后）
↓ 验证了什么：TASKS 明确这条验收依赖 T0105——它是 T0104→T0105 闭环的验收，属于 T0105 的验证范围
↓ 没有验证什么：T0104 单独无法完成闭环验证（search 当时还是 stub）
```

```text
验收 3：metadata 按 F008 的 9 字段 schema 持久化
↓ 验证了什么：代码把 metadatas 原样交给 SDK 的 add()，9 字段由调用方备好、T0104 原样落盘
↓ 没有验证什么：字段是否齐全合法——T0104 明确不校验，属于上游责任
```

⚠️ 由于没有找到真实执行过的验证输出，以上只描述"验证结构"，**不虚构 PASS 结果**。你可以自己在 [vector_store.py:331-338](backend/app/core/vector_store.py#L331-L338) 对照验收标准逐条核对。

---

## 58. T0104 代码阅读路线

### 第 1 个文件：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)（400 行）

**第一遍只看**：
- 第 303–338 行：`# --- Data Operations ---` 分组注释 + `add_texts` 全文（含 docstring）
- 第 331 行：ids 提取那一行（T0104 唯一的"处理逻辑"）

**暂时跳过**：search 实现（第 340–383 行，T0105 再读）；5 个 stub（第 385–400 行）。

**如果能解释下面这件事，就算看懂**："`add_texts` 的 4 个入参分别是什么形状？为什么 chunk_id 不从 `chunks` 里拿而从 `metadatas` 里拿？"

### 第 2 个文件：[docs/SPEC.md](../../docs/SPEC.md) — F008 节（第 894–997 行）

**第一遍只看**：Metadata Schema 9 字段（第 942–955 行）。

**暂时跳过**：Distance→Similarity 公式（第 963–973 行，T0105 再读）。

**如果能解释下面这件事，就算看懂**："9 字段里哪一个是 ChromaDB 的 document id？哪个只是显示名？哪个只是排序号？"

### 第 3 个文件：[docs/TASKS.md](../../docs/TASKS.md) — T0104（第 460–498 行）

**第一遍只看**：Implementation Scope 和 Out of Scope（三条"不做"）。

**如果能解释下面这件事，就算看懂**："T0104 明确不做的三件事是什么？各自归哪个 Task？"

---

## 59. T0104 阶段只需要掌握的 5 件事

1. **`add_texts` 是第 5 个真实方法**——Data Operations 组第一个，知识库第一次能写入数据（存储层）。
2. **四份名单对齐**——chunks / embeddings / metadatas / ids 按位置一一对应；ids 从 metadata 提取（list comprehension）。
3. **T0104 是"搬运工"**——不生成 chunk_id（T0307）、不生成 embedding（T0202）、不校验 schema（上游），边界都写在 TASKS.md 的 Out of Scope。
4. **`chunk_id` 双重身份**——既是 metadata 字段，又是 ChromaDB document id（SPEC 7.1 身份规则）。
5. **`return ids` 有用途**——调用方靠它核对写入结果、回滚失败（不是随手写的）。

---

## 60. 现在可以暂时不懂（T0104 相关）

> 🔵 当前可以跳过。以下内容不影响继续 T0105。

| 暂时不懂的                                    | 为什么现在不用管                                 |
| ---------------------------------------- | ---------------------------------------- |
| 9 字段里 `upload_time` / `ingestion_status` 具体怎么生成 | 属于 Phase 3 IngestService 的职责，T0104 只负责原样落盘 |
| ChromaDB `.add()` 内部怎么建 HNSW 索引          | SDK 细节，信任并调用即可                           |
| 批量写入的原子性（部分失败会怎样）                        | 当前无调用方、无真实写入场景；Phase 3 的 Ingest 回滚策略再研究  |
| embedding 是怎么算出来的（bge-small-zh-v1.5）     | Phase 2（T0202）的内容，T0104 的输入就是"现成的数字"     |

---

## 61. T0104 5 道基础自测题

> 先自己想，不要急着看答案（线索在第 50–52 节）。

**Q1**：T0104 把哪个 stub 变成了真实实现？`add_texts` 的 4 个入参分别是什么类型、什么形状？

**Q2**：读代码：`ids = [meta["chunk_id"] for meta in metadatas]` —— 这行做了什么？等价的 JS 是什么？为什么 chunk_id 从 metadatas 里取而不是从 chunks 里取？

**Q3**：ChromaDB 的 document id 用的是哪个字段？它在 metadata 里和 `ids=` 参数里各出现一次——为什么不算重复？

**Q4**：T0104 明确不做哪三件事？各自归哪个 Task？为什么存储层不做这些？

**Q5**：`add_texts` 为什么 `return ids` 而不是 `None`？对比 T0102 的 `create_collection` 返回 `None`，区别在哪？

---

## 62. T0104 3 个小练习

> 都不修改正式代码。

### 练习 1：把 `add_texts` 翻译成 TypeScript

把片段 11 翻译成 TS class 方法。翻译后自查：`List[List[float]]` 你用了什么类型？list comprehension 你用了什么表达？4 个关键字参数呢？

### 练习 2：画出"三份名单 → 一份名单"的对齐图

给定：3 个 chunk、3 个 embedding、3 个 metadata（其中一个 `chunk_id` 是 `"c-3"`）。画出 `ids` 的提取过程和最终交给 SDK 的 4 份名单，标注哪份名单是"计算出来的"、哪三份是"调用方带进来的"。

### 练习 3：判断这段代码有没有问题

```python
def add_texts(self, collection, chunks, embeddings, metadatas):
    ids = [f"chunk-{i}" for i in range(len(chunks))]   # 假设有人改成"自己生成 id"
    self._client.get_collection(collection).add(
        ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas,
    )
    return ids
```

从三个角度想：SPEC 7.1 身份规则（id 应该谁签发？）、metadatas 里的 `chunk_id` 字段会怎样（两份身份打架）、上游 T0307 生成的 id 被丢弃会有什么后果。

---

## 63. T0104 快速复习卡

> 3 分钟看完。

### 一句话

> T0104 把 `add_texts` 变成真实实现：提取 chunk_ids → 把"文本 + 向量 + 元数据"三份名单交给 ChromaDB → 返回 ids。知识库第一次能写入数据（存储层）。

### 5 个关键词

1. **add_texts** — Data Operations 组第一个真实方法（第 5/11 个）
2. **四份名单** — chunks / embeddings / metadatas / ids 按位置对齐
3. **搬运工** — 不生成 id（T0307）、不生成向量（T0202）、不校验 schema
4. **chunk_id 双重身份** — metadata 字段 + ChromaDB document id（SPEC 7.1）
5. **return ids** — 调用方核对 / 回滚的依据

### 最重要调用关系

```text
add_texts
  → [meta["chunk_id"] for meta in metadatas]          # 提取 ids（list comprehension）
  → self._client.get_collection(collection).add(...)  # 委托 SDK 批量写入
  → return ids
```

### 3 个易混淆点

1. **"能写入" ≠ "能入库"** —— add_texts 只是 RAG 写入管道的最后一步；上传文档 → 解析 → 切块 → 算向量 这些上游步骤都还没实现（Phase 2/3）。别把"存储层能写"当成"用户能上传文档"。
2. **metadata 的 `chunk_id` 和 `ids=` 是同一个值两个身份** —— 前者是"随身信息"，后者是"数据库主键"。
3. **T0104 不校验 ≠ 代码 bug** —— 边界画在 TASKS.md Out of Scope；上游责任归上游。（collection 存在性校验的缺口记录为 Pending Question。）

### 当前实现进度

| 事项                    | 状态                           |
| --------------------- | ---------------------------- |
| T0101–T0103：契约 + 生命周期 | ✅ DONE                       |
| T0104：add_texts 写入    | ✅ DONE（本次）                   |
| T0105：search 检索       | ✅ DONE（见第 64 节起）             |
| T0106–T0108：其余 5 个方法  | ✅ DONE（见第 78 节起）             |
| 今天能写入数据吗（存储层）         | ✅ 能（数据 + 向量 + metadata 一起落盘） |
| 今天能检索数据吗（存储层）         | ✅ 能（T0105 起，见第 64 节起）        |
| 今天能删除文件数据吗（存储层）       | ✅ 能（T0106 起，见第 78 节起）        |

---

## T0105 部分（追加）

> 第 64–77 节为 T0105 完成后的追加内容。T0105 = search 向量检索（存储层）。真实代码：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 340–383 行（文件现 495 行）。

---

## 64. T0105 到底解决了什么问题

### 一句话

T0105 把 `search` 从占位变成真实实现——**知识库第一次能"检索"（存储层层面）**。写入（T0104）+ 检索（T0105）第一次形成闭环：数据进得去，也查得出来。

### 建立在 T0104 哪些基础上

| 基础                       | 谁提供的                | T0105 怎么用                                |
| ------------------------ | ------------------- | ---------------------------------------- |
| 验证数据                     | T0104 的 `add_texts` | AC-F008-01 的验证场景：先写 10 个 chunk，再搜 top_k=3 |
| `VectorSearchResult` 模型  | T0101 定义            | 第一次被真实实例化（T0101 只定义了字段，没人用过）             |
| distance→similarity 语义边界 | SPEC F008（第 4 节讲过）  | 第一次在代码里落地：`similarity_score = clamp(1.0 - distance)` |
| `self._client`           | T0102               | 通过 `get_collection(collection).query(...)` 检索 |

### T0105 实际增加了什么能力

| 能力                    | 之前（T0104 后）                | 现在（T0105 后）                              |
| --------------------- | -------------------------- | ---------------------------------------- |
| 向量相似度检索               | ❌ 调用即抛 NotImplementedError | ✅ `search(...)` 真实查询 ChromaDB            |
| similarity_score 对外输出 | ❌                          | ✅ 返回 `List[VectorSearchResult]`，分数 ∈ [0, 1]、降序 |

### T0105 仍然没有实现什么（刻意不做）

| 不做的事                 | 为什么不做                  | 归谁              |
| -------------------- | ---------------------- | --------------- |
| 把用户问题转成 query vector | 嵌入模型调用是另一个子系统          | T0701（调用方）      |
| 对分数做 min-max 归一化     | SPEC F008 明确禁止（破坏分数语义） | 永远不做            |
| 关键词检索 + 混合融合         | 另一条检索路径 + 融合层          | Phase 6 / T0702 |

### 兑现第 4 节的承诺：语义边界从"规则"变成"代码"

第 4 节讲 T0101 时说过：SPEC 要求 `search()` 内部完成 distance→similarity 转换，"外部永远只看到 similarity"。当时那只是**契约**（签名 + docstring），方法体是 `raise NotImplementedError`。T0105 第一次把这条规则写进可执行的代码——**这是本 Task 最重要的意义**：不只是"新增了检索功能"，而是"SPEC 定下的语义边界第一次被实现"。

---

## 65. 以前端开发者的方式理解 T0105

### TS 心智模型（不是 DX-RAG 真实代码）

```ts
class ChromaVectorStore extends VectorStore {
  search(collection: string, queryVector: number[], topK: number): VectorSearchResult[] {
    const raw = this.client.getCollection(collection).query({
      queryEmbeddings: [queryVector],                  // 注意：包了一层数组
      nResults: topK,
      include: ["documents", "metadatas", "distances"],
    });
    const results: VectorSearchResult[] = [];
    for (let i = 0; i < raw.ids[0].length; i++) {     // 经典 for 循环（Python 用 range）
      const distance = raw.distances[0][i];
      results.push(new VectorSearchResult({
        chunkId: raw.ids[0][i],
        fileId: raw.metadatas[0][i].file_id,
        content: raw.documents[0][i],
        similarityScore: Math.max(0, Math.min(1, 1 - distance)),   // clamp
      }));
    }
    return results.sort((a, b) => b.similarityScore - a.similarityScore);
  }
}
```

### 三个你本来就熟悉的模式

| 模式                | Python 写法                                | 你在前端哪见过                                  |
| ----------------- | ---------------------------------------- | ---------------------------------------- |
| **批量接口单次调用也要包数组** | `query_embeddings=[query_vector]`        | 很多 SDK 的 batch API（一次可传多个查询，结果嵌套一层）      |
| **clamp（数值夹取）**   | `max(0.0, min(1.0, 1.0 - distance))`     | `Math.max(0, Math.min(1, x))`、CSS `clamp()` |
| **按字段排序**         | `results.sort(key=lambda r: r.similarity_score, reverse=True)` | `arr.sort((a, b) => b.score - a.score)`（Python 的 key 写法更接近 lodash 的 `sortBy`） |

### 一个新语法组合：`for i in range(len(x))` 索引循环

Python 的 `for x in list` 默认**直接给元素**（没有下标）；要按下标访问时，用 `range(len(list))` 生成"下标序列"再循环。详见 [python-for-frontend-dev.md](./python-for-frontend-dev.md) 第 17.6 节。

---

## 66. T0105 真实代码阅读

> 挑 3 段。全部来自 [backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 340–383 行，格式与第 4/24/38/52 节一致（片段编号接续）。

### 代码片段 12：`query()` 调用（第 363–367 行）

**Python 原代码**

```python
        raw = self._client.get_collection(collection).query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
```

**🟢 Python 语法怎么读**

- `query_embeddings=[query_vector]` — 把**单个向量包成列表**。ChromaDB 的 query 是批量接口：一次能搜多个查询，结果按"第几个查询"嵌套一层。这里只搜 1 个，所以列表只有 1 个元素——但包装不能省。
- `n_results=top_k` — 要几条结果（`top_k` 是 search 的入参）。
- `include=[...]` — 指定返回哪些数据。ChromaDB 默认只返回 ids + distances；这里显式要 `documents`（原文）和 `metadatas`（元数据）——因为 `VectorSearchResult` 需要 `content` 和 `file_name` 等字段。
- 没有要 `embeddings`——调用方不需要向量本身（体积大、没用途）。

**🟢 TypeScript / Node.js 类比**

```ts
const raw = this.client.getCollection(collection).query({
  queryEmbeddings: [queryVector],
  nResults: topK,
  include: ["documents", "metadatas", "distances"],
});
```

**🟡 在 DX-RAG 中的作用**

这是"翻译层"的入口：SDK 的原生返回结构（嵌套数组 + raw distance）在这里被拿到，下一段代码负责把它翻译成业务模型（VectorSearchResult + similarity_score）。

**🟢 现在只需要记住什么**

1. 批量接口 → 单次调用也要包一层 `[...]`，结果相应嵌套一层 `[0]`。
2. `include` 决定取回哪些数据——T0105 要 documents + metadatas + distances，不要 embeddings。

---

### 代码片段 13：转换循环（第 368–381 行）

**Python 原代码**

```python
        results = []
        for i in range(len(raw["ids"][0])):
            metadata = raw["metadatas"][0][i]
            distance = raw["distances"][0][i]
            results.append(
                VectorSearchResult(
                    chunk_id=raw["ids"][0][i],
                    file_id=metadata["file_id"],
                    file_name=metadata["file_name"],
                    content=raw["documents"][0][i],
                    similarity_score=max(0.0, min(1.0, 1.0 - distance)),
                    metadata=metadata,
                )
            )
```

**🟢 Python 语法怎么读**

- `results = []` — 空列表（≈ `[]`），后面逐个 `append`。
- `for i in range(len(raw["ids"][0]))` — **索引循环**（第 65 节提到的新语法）：`len(...)` 拿数量，`range(n)` 生成 0…n-1 的序列，循环变量 `i` 是下标而不是元素。为什么不用 `for x in raw["ids"][0]`？因为一个结果同时要从 4 个数组按**同一个下标**取 4 样东西——必须用下标。（详见 python-for-frontend-dev.md 第 17.6 节）
- `raw["ids"][0][i]` — 三层结构：`raw` 是 dict → `["ids"]` 取 ids 数组 → `[0]` 取"第 1 个查询"的结果 → `[i]` 取第 i 条。为什么有 `[0]`？因为 query 是批量接口（片段 12 讲过）。
- `results.append(...)` — 往列表尾部加一个元素（≈ `push`）。
- `VectorSearchResult(chunk_id=..., file_id=..., ...)` — 用关键字参数构造 T0101 定义的 Pydantic 模型。每个字段名都要对上模型的字段定义（第 4 节片段 2 见过）。
- `max(0.0, min(1.0, 1.0 - distance))` — **clamp 夹取**：先算 `1.0 - distance`（把"距离"翻成"相似度"），再用 min/max 夹到 [0, 1] 区间。嵌套读法：`min(1.0, x)` 取两者中小的（上限 1.0），`max(0.0, 那个结果)` 取大的（下限 0.0）。

**🟢 TypeScript / Node.js 类比**

```ts
const results: VectorSearchResult[] = [];
for (let i = 0; i < raw.ids[0].length; i++) {
  const distance = raw.distances[0][i];
  results.push(new VectorSearchResult({
    chunkId: raw.ids[0][i],
    fileId: raw.metadatas[0][i].file_id,
    file_name: raw.metadatas[0][i].file_name,
    content: raw.documents[0][i],
    similarityScore: Math.max(0, Math.min(1, 1 - distance)),
  }));
}
```

几乎逐行等价。三个真正的差异：Python 没有 `let i = 0; i < n; i++` 这套语法（用 `range`）；`push` 叫 `append`；构造函数参数用 `kwarg=` 而不是对象字面量。

**🟡 在 DX-RAG 中的作用**

- **SPEC F008 的语义边界在这里落地**：`similarity_score = clamp(1.0 - raw_distance)`。ChromaDB 给的是"距离"（越小越相似），业务层要的是"相似度"（越大越相似），转换 + 夹取必须发生在这一层——**raw distance 从这一行起不再存在**。
- 为什么要 clamp？ChromaDB 的 cosine distance 范围是 [0, 2]（不是 [0, 1]），所以 `1 - distance` 可能落在 [-1, 1]。不夹取的话，负数 similarity 会泄露给上层。SPEC 要求 similarity_score ∈ [0, 1]，clamp 就是这道保险。
- `VectorSearchResult` 的字段表里**没有 distance**（第 4 节片段 2 看过字段表）——类型层面就保证了"泄露无门"。

**🟢 现在只需要记住什么**

1. 一个结果 = 从 4 个数组同一位置取 4 样东西 → 必须用下标循环（`range(len(...))`）。
2. `1.0 - distance` 是**翻语义**，`max(0.0, min(1.0, ...))` 是**夹范围**。
3. 转换后的结果装进 `VectorSearchResult`——T0101 的模型第一次被真正使用。

---

### 代码片段 14：排序（第 382 行）

**Python 原代码**

```python
        results.sort(key=lambda r: r.similarity_score, reverse=True)
```

**🟢 Python 语法怎么读**

- `.sort(...)` — 列表的**原地排序**方法（直接改列表自己，返回 None）。
- `key=lambda r: r.similarity_score` — **key 函数**：告诉 Python"每个元素按什么值比大小"。`lambda r: ...` 是一次性小函数（`r` 是参数，冒号后是返回值）——≈ TS 箭头函数 `r => r.similarityScore`。
- `reverse=True` — 降序（Python 默认升序；`reverse` 是 `sort` 的关键字参数）。
- 整行读作："按每个结果的 similarity_score 从大到小排好。"

**🟢 TypeScript / Node.js 类比**

```ts
results.sort((a, b) => b.similarityScore - a.similarityScore);
```

两种写法思路不同：TS 的 comparator 是"两两比较"（你告诉它 a、b 谁前谁后）；Python 的 key 是"每元素取一个可比值"（你只告诉它比什么，升降序由 `reverse` 管）。Python 写法更像 lodash 的 `_.sortBy`。详见 [python-for-frontend-dev.md](./python-for-frontend-dev.md) 第 17.7 节。

**🟡 在 DX-RAG 中的作用**

ChromaDB 返回的结果本来就按 distance 升序（最相似在前），换算成 similarity 后**顺序其实已经是降序**。那为什么还要显式 sort 一次？**契约保证**：search 的返回值承诺"sorted by similarity_score descending"（TASKS 验收项）。与其依赖 SDK 的返回顺序（换数据库、SDK 升级都可能变），不如在边界内自己排序——**SDK 的行为不可信，自己的排序才可信**。

**🟢 现在只需要记住什么**

1. `list.sort(key=..., reverse=True)` = 按某字段排序，reverse=True 是降序。
2. `lambda r: r.similarity_score` ≈ `r => r.similarityScore`。
3. 显式排序是"契约保证"，不是多此一举。

---

## 67. T0105 核心对象 / 方法

### 唯一有变化的方法：`search`

| 问题    | 答案                                       |
| ----- | ---------------------------------------- |
| 它是什么  | `ChromaVectorStore` 的第 6 个真实方法（Data Operations 组第二个） |
| 输入    | `collection: str` + `query_vector: List[float]`（384 维）+ `top_k: int` |
| 输出    | `List[VectorSearchResult]`——按 similarity_score 降序 |
| 为什么需要 | RAG 检索链路的存储层一步："找出最相似的几个片段"（Phase 7/8）   |
| 谁调用它  | 目前无人调用；将来 VectorRetriever（Phase 7）       |
| 它调用谁  | `self._client.get_collection(collection).query(...)` |
| 真实行为  | ✅ 有（查询 + 转换 + 排序）                        |

### `VectorSearchResult` 第一次被实例化

T0101 定义了 `VectorSearchResult`（6 个字段：`chunk_id`、`file_id`、`file_name`、`content`、`similarity_score`、`metadata`，见 [vector_store.py:59-75](backend/app/core/vector_store.py#L59-L75)）——但 T0101–T0104 期间**没有人真正创建过它**。T0105 是第一个"生产"它的方法：把 SDK 的裸数据翻译成业务模型，然后交给上层。

```text
Query 路径（存储层部分）：
search(query_vector, top_k)
  → ChromaDB query() → 嵌套结果数组
  → 循环翻译：distance → similarity_score（clamp）→ VectorSearchResult
  → 排序（降序）→ 返回
```

---

## 68. T0104 → T0105 的关系

```text
T0104（✅ DONE）                              T0105（✅ DONE）
数据进得去（写入）                              数据查得出来（检索）

add_texts 写入 chunks+向量+metadata       →   search 查询同一个 collection
返回 ids（身份）                           →   命中的 chunk_id 就是当初写入的 ids
TASKS 验收 2：写入后能被检索              →   T0105 的验证场景（AC-F008-01）
```

### T0104 给 T0105 提供了什么

1. **验证数据**——TASKS.md T0105 的 Dependencies 明确列出 T0104：AC-F008-01 的验证场景（10 个 chunk、top_k=3）必须先用 `add_texts` 写入。
2. **同一套基础设施**——`self._client`、collection 概念、委托写法，T0105 零新基础设施起步。

### T0105 又为后续 Task 提供了什么

1. **给 Phase 7/8 的检索积木**——VectorRetriever 将来把 `search` 的结果翻译成 `vector_score`，Hybrid Retrieval（T0702）再融合 keyword_score。
2. **分数语义的地基**——检索不变量 `final_score = keyword_score × 0.3 + vector_score × 0.7` 里的 `vector_score` 就来自这里的 `similarity_score`。T0105 输出的分数质量决定整条 RAG 链路的质量。

---

## 69. 当前架构中的位置

```text
┌────────────────────────────────────┐
│ Future: VectorRetriever (Phase 7)  │  ← Future Task
│ 用户问题 → query vector（T0701）   │
└─────────────────┬──────────────────┘
                  │ 将来调 search(collection, query_vector, top_k)
                  ▼
┌────────────────────────────────────┐
│ ChromaVectorStore                  │  ← T0102–T0105 ✅ DONE
│ search ✅ ← T0105 本次             │
└─────────────────┬──────────────────┘
                  │ query(query_embeddings=[...], n_results=top_k)
                  ▼
┌────────────────────────────────────┐
│ ChromaDB（chroma_db/）             │  ← 返回 distance + documents + metadata
└────────────────────────────────────┘
```

关键认知：**query_vector 从哪来，存储层不知道也不关心**（T0701 的事）。T0105 守住的是箭头往回走的这一段：把 SDK 的 distance 翻译成 similarity_score，让上层拿到的永远是"越大越相似"。

---

## 70. 为什么这样设计（只讲与 T0105 直接相关的原因）

### 1. 为什么转换 + clamp 必须在 search 内部完成

SPEC F008 硬性约束（第 4/8 节讲过）：raw distance 绝不能离开 VectorStore。如果让调用方自己算 `1 - distance`，哪天调用方忘了转换，RAG 系统就会把"最不相似"当"最相似"——最隐蔽的 bug 之一。**语义翻译发生在边界内部，外部只认 similarity。**

### 2. 为什么用 `max(0.0, min(1.0, x))` 而不是只做 `1.0 - distance`

cosine distance ∈ [0, 2]，所以 `1 - distance` ∈ [-1, 1]。不夹取的话，负数会流到上层（similarity = -0.3 是什么意思？）。SPEC 承诺 similarity_score ∈ [0, 1]，clamp 是兑现承诺的保险。

### 3. 为什么结果还要显式 sort 一次

ChromaDB 按 distance 升序返回（最相似在前），换算后天然是相似度降序。但**"天然"依赖 SDK 的内部行为**——SDK 升级、换数据库都可能变。search 的契约承诺"降序返回"，在边界内自己排一次，契约就不依赖任何 SDK 行为。代价只有一行代码。

### 4. 为什么返回 `VectorSearchResult` 而不是裸 dict

T0101 定义的模型：字段明确（有 similarity_score、没有 distance），类型安全，防止实现泄露（第 4 节片段 2 讲过"字段表里没有的东西，调用方就用不了"）。TASKS 的签名草稿写的是 `List[dict]`，实现者选择了更具体的模型——这是"实现可以在 SPEC 框架内做合理细化"的实例（第 3 节也提过这个细节）。

---

## 71. Verification 到底验证了什么

先说诚实结论：**与前几个 Task 一样，仓库里没有自动化测试脚本，也没有验证日志文件。** 唯一可确认的完成记录是 [TASKS.md](../../docs/TASKS.md) 中 T0105 的 Status 已改为 DONE。

T0105 的验收核心是 **AC-F008-01**（SPEC F008 的验收条款）：

```text
AC-F008-01：写入 10 个 chunk（T0104 提供）→ search top_k=3
↓ 验证了什么：真实代码路径满足验收要求的结构——query n_results=3、转换公式、降序排序、
    similarity_score ∈ [0, 1]（clamp 保证）
↓ 没有验证什么：仓库中没有留下"真实执行过 10 写入 + 3 检索"的输出记录，
    分数是否真实落在 [0, 1]、排序是否正确，都未留下执行证据
```

```text
验收 2：结果不含 raw distance
↓ 验证了什么：VectorSearchResult 模型的字段表里没有 distance（类型层面结构性排除）
↓ 没有验证什么：暂无上层调用方，防泄露靠"类型约束 + 代码审查"，未经过运行时验证
```

⚠️ 由于没有找到真实执行过的验证输出，以上只描述"验证结构"，**不虚构 PASS 结果**。你可以自己在 [vector_store.py:363-383](backend/app/core/vector_store.py#L363-L383) 对照 AC-F008-01 逐条核对。

---

## 72. T0105 代码阅读路线

### 第 1 个文件：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)（400 行）

**第一遍只看**：
- 第 340–362 行：search 的 docstring（把 F008 的语义边界写得很清楚）
- 第 363–367 行：query 调用（include 参数）
- 第 368–381 行：转换循环（range + clamp + VectorSearchResult）
- 第 382 行：排序

**暂时跳过**：5 个 stub（第 385–400 行）。

**如果能解释下面这件事，就算看懂**："`raw["ids"][0][i]` 为什么有三层？distance 在哪一行之后就不存在了？"

### 第 2 个文件：[docs/SPEC.md](../../docs/SPEC.md) — F008 节（第 894–997 行）

**第一遍只看**：Distance→Similarity 公式（第 963–973 行）+ AC-F008-01（第 977–980 行）。

**如果能解释下面这件事，就算看懂**："SPEC 的公式和代码里的 `max(0.0, min(1.0, 1.0 - distance))` 逐字对应吗？AC-F008-01 验证的输入输出是什么？"

### 第 3 个文件：[docs/TASKS.md](../../docs/TASKS.md) — T0105（第 501–543 行）

**第一遍只看**：Implementation Scope 和 Out of Scope（归一化禁令、T0701/T0702 边界）。

**如果能解释下面这件事，就算看懂**："T0105 明确不做的三件事是什么？'禁止 min-max 归一化'这条为什么是禁令而不是 TODO？"

---

## 73. T0105 阶段只需要掌握的 5 件事

1. **`search` 是第 6 个真实方法**——写入 + 检索闭环，存储层 6/11 已真实。
2. **语义边界落地**——`similarity_score = clamp(1.0 - distance)` 第一次成为可执行代码；raw distance 到转换那一行为止。
3. **索引循环 `for i in range(len(x))`**——一个结果要从 4 个数组同一下标取值，必须用下标循环（新语法，见 python-for-frontend-dev.md 第 17.6 节）。
4. **key 函数排序**——`sort(key=lambda r: r.similarity_score, reverse=True)` ≈ 按字段排序 + 降序（新语法，见第 17.7 节）。
5. **`VectorSearchResult` 首次实例化**——T0101 定义的模型第一次被真正使用，字段里没有 distance（类型防泄露）。

---

## 74. 现在可以暂时不懂（T0105 相关）

> 🔵 当前可以跳过。以下内容不影响继续 T0106。

| 暂时不懂的                              | 为什么现在不用管                           |
| ---------------------------------- | ---------------------------------- |
| HNSW 索引内部怎么算"最近邻"                  | SDK 内部算法，信任并调用即可                   |
| 为什么 cosine distance 范围是 [0, 2]     | 余弦几何知识；只需要知道"不是 [0, 1]，所以必须 clamp" |
| query_embeddings 传多个查询时结果怎么嵌套      | 当前只用单查询场景；需要时再查 ChromaDB 文档        |
| top_k 大于 collection 里 chunk 总数时会怎样 | SDK 会返回实际存在的数量；当前无调用方，Phase 7 再验证  |

---

## 75. T0105 5 道基础自测题

> 先自己想，不要急着看答案（线索在第 64–66 节）。

**Q1**：T0105 把哪个 stub 变成了真实实现？`search` 的输入输出分别是什么？分数叫什么、范围多少、按什么顺序？

**Q2**：读代码：`raw["ids"][0][i]` —— 三层下标各代表什么？为什么有 `[0]`？等价的 JS 是什么？

**Q3**：`max(0.0, min(1.0, 1.0 - distance))` 里，`1.0 - distance` 在做什么？`max/min` 在做什么？如果只写 `1.0 - distance` 不夹取，会发生什么？

**Q4**：`results.sort(key=lambda r: r.similarity_score, reverse=True)` —— `key` 和 `reverse` 分别起什么作用？如果 TS 里写等价逻辑，你用什么？两种写法的思路差异是什么？

**Q5**：ChromaDB 返回的顺序本来就是"最相似在前"，为什么还要显式 sort 一次？如果未来换 Milvus，这行代码的作用是什么？

---

## 76. T0105 3 个小练习

> 都不修改正式代码。

### 练习 1：把 `search` 翻译成 TypeScript

把片段 12–14 翻译成一个 TS class 方法。翻译后自查：`range(len(...))` 循环你用什么表达？`lambda` + `sort(key=...)` 呢？`max/min` clamp 呢？

### 练习 2：画"写入 → 检索"的完整数据流

从 `add_texts` 写入的 10 个 chunk 出发，画 `search(top_k=3)` 的完整路径：数据在 ChromaDB 里以什么形态存着 → query 返回什么 → 循环怎么翻译 → 最终 3 条结果长什么样。标注每一站分数的名字和语义（distance → similarity_score）。

### 练习 3：判断这段代码有没有问题

```python
def search(self, collection, query_vector, top_k):
    raw = self._client.get_collection(collection).query(
        query_embeddings=[query_vector], n_results=top_k, include=["distances"],
    )
    return [
        {"chunk_id": raw["ids"][0][i], "distance": raw["distances"][0][i]}
        for i in range(len(raw["ids"][0]))
    ]
```

从三个角度想：SPEC F008 语义边界（distance 泄露了吗？）、契约（返回类型还是 `List[VectorSearchResult]` 吗？）、上层使用（调用方拿 distance 会怎么用错？）。

---

## 77. T0105 快速复习卡

> 3 分钟看完。

### 一句话

> T0105 把 `search` 变成真实实现：查询 ChromaDB → 把 distance 翻译成 similarity_score（clamp 到 [0,1]）→ 装进 VectorSearchResult → 按分数降序返回。知识库第一次能检索（存储层），写入/检索闭环。

### 5 个关键词

1. **search** — Data Operations 组第二个真实方法（第 6/11 个）
2. **distance → similarity** — `clamp(1.0 - distance)`，SPEC F008 语义边界第一次落地
3. **`range(len(...))`** — 索引循环（新语法）
4. **`sort(key=lambda ...)`** — key 函数排序 + reverse=True 降序（新语法）
5. **VectorSearchResult** — T0101 模型首次实例化；字段表里没有 distance

### 最重要调用关系

```text
search
  → get_collection(collection).query(query_embeddings=[...], n_results=top_k, include=[...])
  → for i in range(len(...)):  distance → similarity（clamp）→ VectorSearchResult
  → sort(key=lambda r: r.similarity_score, reverse=True)
  → return results
```

### 3 个易混淆点

1. **"能检索" ≠ "能问答"** —— search 只做"向量相似度检索"；关键词检索（Phase 6）、混合融合（T0702）、LLM 生成（Phase 8）都还没实现。
2. **distance 和 similarity 方向相反** —— distance 越小越相似（ChromaDB 内部）；similarity 越大越相似（对外）。转换一旦漏掉，结果就反了。
3. **`range(n)` 从 0 开始、到 n-1 结束** —— 和 TS 的 `for (let i = 0; i < n; i++)` 一致，但和 Python 默认的 `for x in list`（直接给元素）是两回事。

### 当前实现进度

| 事项                                       | 状态                                      |
| ---------------------------------------- | --------------------------------------- |
| T0101–T0104：契约 + 生命周期 + 写入               | ✅ DONE                                  |
| T0105：search 检索                          | ✅ DONE（本次）                              |
| T0106：delete_by_file 删除                  | ✅ DONE（见第 78 节起）                        |
| T0107：get_files 文件列表                     | ✅ DONE（见第 92 节起）                        |
| T0108：list_chunks / count / get_chunks_by_file | ✅ DONE（见第 106 节起）                       |
| 今天能写入 / 检索数据吗（存储层）                       | ✅ 能（写入 T0104 + 检索 T0105，闭环）             |
| 今天能删除文件数据吗（存储层）                          | ✅ 能（delete_by_file 由 T0106 实现，见第 78 节起） |

---

> **下一步学习**：`delete_by_file` 的 stub 已由 T0106 变成真实实现——写入 / 检索 / 删除三条数据路径全部打通（见第 78 节起）。

---

## T0106 部分（追加）

> 第 78–91 节为 T0106 完成后的追加内容。T0106 = delete_by_file 按文件删除（存储层）。真实代码：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 385–400 行（文件现 495 行）。

---

## 78. T0106 到底解决了什么问题

### 一句话

T0106 把 `delete_by_file` 从"调用即崩的占位"变成真实实现——**知识库第一次能"删除"文件数据（存储层层面）**。至此写入（T0104）、检索（T0105）、删除（T0106）三条数据路径全部点亮。

### 这是 F016 文件删除 7 步级联中的 2 步

SPEC F016（文件删除，SPEC 第 1587–1594 行）描述的是**用户级完整流程**（7 步级联）：

| 步    | F016 级联行为                                | 谁负责                                      |
| ---- | ---------------------------------------- | ---------------------------------------- |
| 1    | 通过 file_id 定位文件记录                        | 元数据（v1 无外部 DB → 由 get_files 聚合，T0107）    |
| 2    | 删除 `uploads/{collection_name}/{file_name}` 原始文件 | **T0903**（File API）                      |
| 3    | 删除 ChromaDB 中该 file_id 的所有 chunks 和 vectors | **T0106 本次**                             |
| 4    | 删除 ChromaDB 中该 file_id 的 metadata        | **T0106 本次**（ChromaDB 的 `delete(where=...)` 一次完成 3+4） |
| 5    | Invalidate keyword index cache（标记为 dirty） | **调用方**（Phase 6 后存在）                     |
| 6    | 返回成功                                     | T0903                                    |
| 7    | 如果 file_id 不存在，返回 404                    | **API 层**（T0903）；存储层只返回 0                |

> 认知呼应：这和 T0103 的"SPEC 8 步重命名，Task 只做 1 步"是同一课——**"SPEC 的一大段 ≠ 一个 Task"**。T0106 只拿走了存储层领地的第 3+4 步。

### 建立在什么基础上

- T0104 落盘的 metadata（9 字段里的 `file_id`）——删除就是靠这个字段筛选，再次验证 file_id = 身份（SPEC 7.1）；
- T0102 的 `self._client.get_collection()` 模式；
- T0105 的 include 参数认知——T0106 用的是最轻量的 `include=[]`（只要 ids）。

### 刻意不做

| 不做的事               | 归谁                           |
| ------------------ | ---------------------------- |
| 删 uploads/ 原始文件    | T0903（File API，SPEC 级联第 2 步） |
| 使 keyword index 失效 | 调用方（SPEC 级联第 5 步）            |
| file_id 不存在时抛 404  | API 层（SPEC 级联第 7 步）；存储层返回 0  |

---

## 79. 以前端开发者的方式理解 T0106

### TypeScript 心智模型

```ts
deleteByFile(collection: string, fileId: string): number {
  const col = this.client.getCollection(collection);
  const matching = col.get({ where: { file_id: fileId } });   // ① 先查：有哪些匹配
  const count = matching.ids.length;
  if (count > 0) {
    col.delete({ where: { file_id: fileId } });               // ② 再删
  }
  return count;
}
```

### 三个熟悉的模式

1. **where 子句 ≈ SQL WHERE / Prisma where / Array.filter 的条件对象**——"给我所有 `file_id` 等于这个值的记录"。只不过 ChromaDB 筛的是 **metadata 字段**（T0104 写入时冗余的那 9 个字段之一），不是数据库的"列"。
2. **先数后删**——你想"删除并返回数量"，但 ChromaDB SDK 的 `delete()` **不返回删了多少**。于是分两步：先 `get()` 数一遍，再 `delete()` 删一遍。这是 SDK 能力不足时的补偿写法（对比 T0108 的 `get_chunk_count`：SDK 自带 `count()`，那里就一行搞定）。
3. **删除不存在的 = 不是错误**——`count === 0` 时直接返回 0，不抛错。这和"删一个不存在的 key"的幂等思想一致：调用方（API 层）拿到 0 再决定要不要映射成 404。

### 一个注意点

Python 代码里 `where={"file_id": file_id}` 左边的 `"file_id"` 是 metadata 字段名字符串，右边的 `file_id` 是入参变量——**同名纯属巧合**（和 T0102 的 `name=name` 一样）。别读成"自己等于自己"。

---

## 80. T0106 真实代码阅读（代码片段 15）

**Python 原代码**（[vector_store.py:385-400](../../backend/app/core/vector_store.py#L385-L400)）

```python
    def delete_by_file(self, collection: str, file_id: str) -> int:
        """Delete all chunks (vectors + metadata) belonging to a file.

        Returns:
            Number of chunks deleted.  0 if the file has no chunks.
        """
        col = self._client.get_collection(collection)
        matching = col.get(where={"file_id": file_id}, include=[])
        count = len(matching["ids"])
        if count > 0:
            col.delete(where={"file_id": file_id})
        return count
```

**🟢 Python 语法怎么读**

- `col = self._client.get_collection(collection)` — 把 collection 对象存进局部变量。之前的方法都是"一条链走到底"（T0105：`self._client.get_collection(collection).query(...)`）；这里 get 和 delete 都要用同一个 col，所以**先存下来**。
- `where={"file_id": file_id}` — dict 字面量（第 24 节片段 6 学过）当查询条件（≈ `{ where: { file_id: fileId } }`）。右值 `file_id` 是入参。
- `include=[]` — 空列表 = "不要 documents / metadatas / embeddings，**只要 ids**"。数一遍而已，没必要把内容都拉出来。对比：T0105 的 `include=["documents", "metadatas", "distances"]`、T0107 的 `include=["metadatas"]`——**include 参数决定取回什么**。
- `len(matching["ids"])` — `len()` 取列表长度（第 17.6 节在 `range(len(...))` 里见过；这次直接对 `get()` 返回的 dict 里的 `"ids"` 列表用）。
- `if count > 0:` — 守卫：没有匹配就跳过删除，直接返回 0。**避免无意义的 SDK 调用**。
- `col.delete(where={"file_id": file_id})` — ChromaDB 的删除也支持同一个 where 过滤（get / delete 共用筛选语法）。

**🟢 TypeScript / Node.js 类比**（见第 79 节开头，两段核心代码一一对应）

**🟡 在 DX-RAG 中的作用**

- 落地 F016 级联的第 3+4 步：ChromaDB 的 `delete(where=...)` **一次删除匹配 chunk 的 vectors + documents + metadata**，所以"第 3 步删 chunks/vectors + 第 4 步删 metadata"在代码里是一行。
- 删除键是 **file_id 而不是 file_name**（F016：使用 file_id 确保精确性和不可变性）——T0101 讲的身份规则第三次落地（前两次：T0104 用 chunk_id 当主键、T0105 返回 chunk_id/file_id）。
- 返回 `count` 让调用方（T0903 的 DELETE 端点）知道删了几个；0 可映射成 404（F016 第 7 步的语义由 API 层翻译）。

**🟢 现在只需要记住什么**

1. `where={...}` 按 metadata 过滤——ChromaDB 的 get 和 delete 都支持。
2. **先数后删**——SDK 的 delete 不返回数量，用 get + len 补上。
3. 没有匹配返回 0、不抛错——404 是 API 层的事，存储层保持中性。

---

## 81. T0106 核心对象 / 方法

### 第 7 个真实方法

| 问题      | 答案                                       |
| ------- | ---------------------------------------- |
| 方法      | `delete_by_file(collection, file_id) -> int`（Data Operations 组第 3 个） |
| 输入      | collection 名 + file_id（UUID 字符串）         |
| 输出      | int：实际删除的 chunk 数                        |
| 依赖的既有能力 | `self._client`（T0102）、`where` 过滤（SDK 自带）、metadata 里的 `file_id` 字段（T0104 写入） |
| 将来谁调用   | File API（Phase 9，`DELETE /api/files/{file_id}`）；IngestService 失败回滚清理残留（Phase 3） |
| 错误路径    | file_id 有 chunks → 删除并返回数量；无 chunks → 返回 0；collection 不存在 → ChromaDB SDK 直接抛原始异常（见下方 Pending Question） |

### 三条数据路径至此全部点亮

```text
写入  add_texts      ✅ T0104
检索  search         ✅ T0105
删除  delete_by_file ✅ T0106（本次）
```

> Pending Question（与 T0104 记录的同款）：`delete_by_file` 没有校验 collection 是否存在，不存在的 collection 会由 ChromaDB SDK 抛原始异常而不是 `AppError`。这一点与 `rename_collection`（T0103 有校验）不一致——是数据操作类方法（T0104–T0108）的系统性模式，记录不修复。

---

## 82. T0105 → T0106 的关系

- **不依赖 T0105 的代码**（T0106 的依赖是 T0102 client + T0104 metadata），但 T0105 教过两样东西这里直接复用：**include 参数控制取回内容**（T0106 选了最轻的 `include=[]`）、**局部变量先存对象**（T0105 的 `metadata` / `distance` 局部变量先例）。
- T0106 给 T0903（File API）提供了第一块积木：DELETE 端点的存储层操作。
- 认知上 T0105→T0106 完成了"数据路径三件套"：**写入 → 检索 → 删除**。之后的 T0107/T0108 是"查询辅助"（列表 / 统计），不再新开数据路径。

---

## 83. 当前架构中的位置

```text
┌────────────────────────────────────┐
│ Future: File API（Phase 9）        │  ← T0903 DELETE /api/files/{file_id}
│ （文件删除级联的编排者）            │     F016 7 步：uploads 文件 / keyword index / 404
└─────────────────┬──────────────────┘
                  │ 只调用 delete_by_file（第 3+4 步）
                  ▼
┌────────────────────────────────────┐
│ ChromaVectorStore.delete_by_file   │  ← T0106 ✅
│ get(where=...) 数 → delete(where=...) 删 → 返回数量
└─────────────────┬──────────────────┘
                  │ SDK 调用只发生在类内部
                  ▼
┌────────────────────────────────────┐
│ ChromaDB（chroma_db/）             │  删 chunks + vectors + metadata
└────────────────────────────────────┘

uploads/ 里的原始文件（磁盘）──→ 不在 T0106 领地，归 T0903
keyword index（内存倒排索引）──→ 不在 T0106 领地，归调用方
```

注意：存储层只删 ChromaDB 里的东西。**文件上传目录（uploads/）是另一个世界**——T0106 管不到，也不该管（TASKS.md Out of Scope 明写）。

---

## 84. 为什么这样设计（只讲与 T0106 直接相关的原因）

1. **为什么先数后删？** ChromaDB SDK 的 `delete()` 不返回删除数量，而契约（F008）要求返回 `int`。`get(where=..., include=[])` 是最轻量的计数方式（不拉 documents/metadatas/embeddings）。代价：两次 SDK 往返。
2. **为什么不存在返回 0 而不是抛错？** 存储层保持语义中性：删 0 个不是存储层的错误。F016 的 404 语义由 API 层（T0903）根据返回值决定。这也让"幂等删除"自然成立——同一个 file_id 删两次，第二次返回 0，不会崩。
3. **为什么 `include=[]`？** 删除前只想数一下，拉 documents/metadatas 是浪费。对比 T0107 的 `include=["metadatas"]`：它真的需要 metadata 做聚合——**include 永远只取用得上的**。
4. **为什么删 chunks 不管 uploads 文件和 keyword index？** TASKS.md 的 Out of Scope 明确划界。存储层越权去删文件，会让 T0903 的级联编排失去意义（比如先删文件后删向量，中途失败会留下半删状态——顺序由编排者控制）。

---

## 85. Verification：T0106 验证了什么

### 验收依据

| 依据                           | 内容                                       |
| ---------------------------- | ---------------------------------------- |
| TASKS T0106 验收               | 按 file_id 删除；返回删除数量；file_id 无 chunks 时返回 0 |
| AC-F008-02（SPEC 第 982–985 行） | file_a（5 chunks）+ file_b（3 chunks）→ `delete_by_file(file_id_a)` → **file_a 5 个全删、file_b 3 个保持不变、返回 5** |
| F016 级联边界                    | 只做第 3+4 步；不碰 uploads、不碰 keyword index    |

### 验证手段的真实情况

仓库里**没有自动化测试脚本**（`find . -name "test_*.py"` 无结果）。T0106 的"验证"实际形式是：TASKS.md 中该 Task 的状态从 TODO 变为 DONE（状态变更 + 实现 diff）。AC-F008-02 描述的 5+3 → 5 的删除场景，**没有本会话可查的执行记录**——不虚构 PASS。

### 怎么自己动手验（可选）

```python
from app.core.vector_store import ChromaVectorStore
store = ChromaVectorStore()
store.create_collection("test-kb")
# 用 add_texts 写入 file_a 5 条 + file_b 3 条（embeddings 需 384 维向量）
n = store.delete_by_file("test-kb", file_id_a)
assert n == 5
assert store.get_chunk_count("test-kb") == 3          # 只剩 file_b（get_chunk_count 见 T0108）
```

（注意：验证脚本只是示意，仓库里并不存在；真实跑需要先有 embedding 数据。）

---

## 86. T0106 代码阅读路线

| 顺序   | 文件 / 位置                                  | 只看什么                                     |
| ---- | ---------------------------------------- | ---------------------------------------- |
| 1    | [vector_store.py:385-400](../../backend/app/core/vector_store.py#L385-L400) | `delete_by_file` 实现（本 Task 唯一产物）         |
| 2    | [SPEC.md:1587-1594](../../docs/SPEC.md#L1587-L1594) | F016 删除 7 步级联——确认 T0106 只做 3+4           |
| 3    | [SPEC.md:982-985](../../docs/SPEC.md#L982-L985) | AC-F008-02：5+3 → 5 的验收场景                 |
| 4    | [TASKS.md:546-584](../../docs/TASKS.md#L546-L584) | T0106 的 Scope / Out of Scope / Dependencies |
| 5    | [vector_store.py:169-179](../../backend/app/core/vector_store.py#L169-L179) | ABC 里的契约签名（对比实现是否一致）                     |

**如果能解释下面这件事，就算看懂**："为什么 `delete_by_file` 里要先用 `get` 数一遍？`include=[]` 省掉了什么？返回 0 和抛 404 的边界在哪里？"

---

## 87. T0106 阶段只需要掌握的 5 件事

1. **`delete_by_file` 是第 7 个真实方法**——写入 / 检索 / 删除三条数据路径全部点亮（T0104/T0105/T0106）。
2. **`where={"file_id": file_id}` 按 metadata 过滤**——file_id = 身份规则的第三次落地（删除用 file_id 不用 file_name）。
3. **先数后删**——SDK 的 delete 不返回数量，get + len 两步走；`include=[]` 让"数"这一步最轻量。
4. **不存在返回 0，不抛 404**——F016 级联第 7 步的 404 语义归 API 层（T0903）；存储层保持中性、天然幂等。
5. **F016 的 7 步级联 T0106 只做 2 步（3+4）**——"SPEC 的一大段 ≠ 一个 Task"第二次出现（第一次是 T0103 的 8 步重命名）。

---

## 88. 现在可以暂时不懂（T0106 相关）

| 不懂的                                      | 为什么可以先放                         |
| ---------------------------------------- | ------------------------------- |
| ChromaDB `where` 的高级语法（`$and` / `$or` / `$in`） | v1 只用"相等"这一种过滤                  |
| `delete()` 的原子性 / 一致性保证                  | 单机本地 ChromaDB，不需要分布式事务认知        |
| keyword index 的 dirty 标记机制               | Phase 6 才会实现 keyword index，那时再学 |
| uploads/ 目录的文件管理方式                       | T0903（File API）的领地，届时再学         |

---

## 89. T0106 5 道基础自测题

> 先自己想，不要急着看答案（线索在第 78–80 节）。

**Q1**：T0106 点亮了哪条数据路径？`delete_by_file` 的契约（输入 / 输出）是什么？

**Q2**：`where={"file_id": file_id}` 在过滤什么？为什么删除键是 file_id 而不是 file_name？

**Q3**：为什么先 `get` 再 `delete`，不能直接 `delete` 然后想办法数？`include=[]` 的作用是什么？

**Q4**：file_id 不存在时返回什么？为什么不抛 `AppError("...NOT_FOUND")`？F016 级联第 7 步的 404 归谁？

**Q5**：F016 删除级联有 7 步，T0106 做了哪几步？其余 5 步分别归谁？

---

## 90. T0106 3 个小练习

> 都不修改正式代码。

### 练习 1：把 `delete_by_file` 翻译成 TypeScript

参考第 79 节的 TS 心智模型，自己写一遍（含类型）。翻译后自查：`where={"file_id": file_id}` 你怎么表达？"先数后删"的两步在 TS 里还必要吗（假设你的 SDK 同样不返回删除数量）？

### 练习 2：画 AC-F008-02 的验证过程图

画 8 个 chunk（file_a ×5 + file_b ×3）在删除前后的两张图：删除前 collection 里有什么；`delete_by_file(file_id_a)` 之后剩什么、返回什么。

### 练习 3：判断这段"改进"是否越界

```python
def delete_by_file(self, collection: str, file_id: str) -> int:
    count = ...
    # "顺手"把 uploads 里的文件也删了：
    os.remove(f"uploads/{collection}/{file_name}")
    return count
```

从三个角度想：TASKS.md 的 Out of Scope、F016 级联的编排顺序（先删谁？中途失败会怎样？）、存储层的职责边界。如果你在 review 里看到这段代码，会打回吗？理由？

---

## 91. T0106 快速复习卡

> 3 分钟看完。

### 一句话

> T0106 把 `delete_by_file` 变成真实实现：`get(where=...)` 数匹配 → `delete(where=...)` 删 chunks+vectors+metadata → 返回删除数量。存储层第一次能删除文件数据。

### 5 个关键词

1. **delete_by_file** — Data Operations 组第三个真实方法（第 7/11 个）
2. **`where={"file_id": file_id}`** — metadata 过滤（get / delete 共用）
3. **先数后删** — SDK 的 delete 不返回数量；`get + len` 补偿
4. **`include=[]`** — 只要 ids 的最轻量查询
5. **返回 0 ≠ 404** — 存储层中性；404 语义归 API 层（F016 第 7 步）

### 最重要调用关系

```text
delete_by_file
  → get_collection(collection)               # 局部变量 col（第一次"先存再用"）
  → col.get(where={"file_id": file_id}, include=[])   # 数：len(ids)
  → if count > 0: col.delete(where={"file_id": file_id})  # 删（一步含 vectors+metadata）
  → return count
```

### 3 个易混淆点

1. **"能删除" ≠ "文件删除功能完成"** —— 存储层只做了 F016 7 步里的 2 步；uploads 原始文件、keyword index、404 都还没人做（T0903 / Phase 6）。
2. **`where=` 过滤的是 metadata 字段，不是 SQL 列** —— 能筛的只有 T0104 写入 metadata 时带上的字段（file_id 等 9 个）。
3. **同名陷阱** —— `where={"file_id": file_id}` 左边是字符串 key，右边是变量；和 T0102 的 `name=name` 同款。

### 当前实现进度

| 事项                                       | 状态                                       |
| ---------------------------------------- | ---------------------------------------- |
| T0101–T0105：契约 + 生命周期 + 写入 + 检索          | ✅ DONE                                   |
| T0106：delete_by_file 删除                  | ✅ DONE（本次）                               |
| T0107：get_files 文件列表                     | ⬜ 下一步（→ T0107）                           |
| T0108：list_chunks / count / get_chunks_by_file | ⬜ TODO                                   |
| 今天能删除文件数据吗（存储层）                          | ✅ 能（chunks + vectors + metadata 一起删）     |
| 今天能完成"用户级文件删除"吗                          | ❌ 不能（uploads 文件 / keyword index / 404 归 T0903 与 Phase 6） |

---

> **下一步学习**：T0107 完成后，回来看 `get_files` 如何在"没有任何 metadata 数据库"的情况下聚合出文件列表——7.3 Persistence Strategy 将第一次落地。

---

## T0107 部分（追加）

> 第 92–105 节为 T0107 完成后的追加内容。T0107 = get_files 文件列表（存储层聚合）。真实代码：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 402–432 行（文件现 495 行）。

---

## 92. T0107 到底解决了什么问题

### 一句话

T0107 把 `get_files` 从占位变成真实实现——**在没有任何 metadata 数据库的情况下，"文件列表"完全从 chunk metadata 里聚合出来**。这是 SPEC 7.3 Persistence Strategy 的第一次落地：v1 不引入 SQLite/PostgreSQL/Redis，FileRecord 是"算出来的"，不是"存出来的"。

### 先搞懂一个大前提：v1 没有"文件表"

传统后端做"文件列表"：SELECT * FROM files。但 SPEC 7.3（第 2249–2264 行）明确规定：

- **Persistence Strategy**：v1 不引入外部 metadata 存储（SQLite/PostgreSQL/Redis 都在 v1 明确排除清单里）；
- 文件级 metadata（file_name、file_size、upload_time、ingestion_status）**冗余（denormalize）在每条 chunk 的 metadata 上**；
- `get_files()` 通过对 chunk metadata **按 file_id 聚合（group/deduplicate）** 得到文件列表；
- FAILED 入库的文件：没有 chunks → 自然不产生任何文件记录。

所以 T0107 的代码不是在"查表"，而是在**做一次分组聚合**——这是本 Task 最重要的认知。

### 建立在什么基础上

- T0104 落盘的 9 字段 metadata（file_name / file_size / upload_time / ingestion_status 都在里面）；
- SPEC 957 行的一致性约束：**同一 file_id 的所有 chunks，冗余字段必须一致**——所以聚合时取第一条即可；
- T0106 刚用过的 `col.get(...)` 模式（这次不带 where，取全量）。

### 刻意不做

| 不做的事                          | 归谁                     |
| ----------------------------- | ---------------------- |
| 引入外部 metadata 数据库             | SPEC 7.3 明令禁止（v1 排除清单） |
| 返回 chunk content / embeddings | 文件列表只要 6 个字段           |
| 单独"存储"文件记录                    | 没有存储——每次调用实时聚合         |

---

## 93. 以前端开发者的方式理解 T0107

### TypeScript 心智模型

```ts
getFiles(collection: string): FileRecord[] {
  const metadatas = this.client.getCollection(collection)
    .get({ include: ["metadatas"] }).metadatas;          // 全量 chunk 的 metadata
  const files = new Map<string, FileRecord>();            // Python 用 dict 当 Map 用
  for (const meta of metadatas) {
    const fid = meta.file_id;
    if (!files.has(fid)) {                                // 这个文件第一次出现？
      files.set(fid, {
        fileId: fid, fileName: meta.file_name,
        size: meta.file_size, uploadTime: meta.upload_time,
        chunkCount: 0, status: meta.ingestion_status,
      });
    }
    files.get(fid)!.chunkCount += 1;                      // 每条 chunk 都 +1
  }
  return [...files.values()];                             // Map → 数组
}
```

### 三个熟悉的模式

1. **group by + 计数 ≈ SQL `GROUP BY file_id` + `COUNT(*)`**——前端里最像的是 `reduce` 聚合：一个初始容器 + 遍历 + 按 key 累加。
2. **dict 当 Map 用**——Python 的 dict 以 file_id 为 key、文件记录为 value。**key 天然唯一 → 去重靠数据结构本身**，不需要写"if 已存在就跳过"的显式去重。
3. **首条初始化、其余累加**（counter pattern）——第一次见到这个 file_id 就建记录（chunk_count=0），之后每条 chunk 只做 `+= 1`。

### 两个新 Python 语法预告

- `files: Dict[str, Dict[str, Any]] = {}` —— **变量标注**（variable annotation）：给局部变量写类型，Python 运行时不检查、纯给人和工具看（→ python 手册 17.10）。
- `list(files.values())` —— `.values()` 返回一个"视图"对象，**不是列表**；`list()` 把它转成真列表（→ python 手册 17.11）。

---

## 94. T0107 真实代码阅读（代码片段 16）

**Python 原代码**（[vector_store.py:402-432](../../backend/app/core/vector_store.py#L402-L432)）

```python
    def get_files(self, collection: str) -> List[Dict[str, Any]]:
        """Get file list by aggregating chunk metadata (group/deduplicate by file_id).

        Pure ChromaDB aggregation — no external metadata database
        (SPEC Section 7.3 Persistence Strategy).
        """
        col = self._client.get_collection(collection)
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

**🟢 Python 语法怎么读**

- `col.get(include=["metadatas"])["metadatas"]` — `get()` **不带 where = 取全部**；`include=["metadatas"]` 只要 metadata 不要 documents/embeddings（轻量）；紧跟的 `["metadatas"]` 从返回 dict 里取出列表。
- `files: Dict[str, Dict[str, Any]] = {}` — **变量标注**（第 17.10 节）：`名字: 类型 = 值`，运行时啥也不做。`Dict[str, Dict[str, Any]]` = "str → dict" 的字典（嵌套类型标注第一次出现）。
- `for meta in metadatas:` — **直接遍历元素**（不是索引循环！）。对比 T0105 的 `range(len(...))`：那里要同时用三个列表的同一下标，这里只需要 meta 本身——就用最自然的写法。
- `fid = meta["file_id"]` — 从每条 metadata 里取出文件 id（T0104 写入的 9 字段之一）。
- `if fid not in files:` — `in` 用在 dict 上**查的是 key**（第 17.5 节）——"这个文件 id 第一次出现吗？"
- `files[fid] = {...}` — dict 按 key 赋值；首次出现时建立文件记录骨架（`chunk_count: 0`）。
- `files[fid]["chunk_count"] += 1` — 两层取值后自增：先取文件记录 dict，再取 `chunk_count` 并 +1。**每条 chunk 都执行这行** → 循环结束就是每个文件的 chunk 总数。
- `return list(files.values())` — `.values()` 返回"值视图"（不是 list），`list()` 转成真列表——契约要求 `List[Dict]`（第 17.11 节）。

**🟢 TypeScript / Node.js 类比**（见第 93 节开头，含 Map 版本）

**🟡 在 DX-RAG 中的作用**

- 落地 SPEC 7.3 Persistence Strategy："文件列表 = 对 chunk metadata 做 group by file_id + 计数"。
- **字段名翻译发生在边界内部**：metadata 里的 `file_size` → 输出 key `size`；`ingestion_status` → 输出 key `status`。输出 key 不是随便起的——F016 文件列表 API 规定返回 `{file_id, file_name, size, upload_time, chunk_count, status}`（SPEC 第 1561–1565 行）。
- "取第一条"合法性的来源：SPEC 957 行规定同一 file_id 的冗余字段**必须一致**（T0104 写入时保证），所以第一条 chunk 的字段能代表整个文件。
- FAILED 入库的文件（0 chunks）**自然缺席**——没有 chunks 就没有 metadata，聚合不出记录。SPEC 961 行的语义自动成立，不用写任何特判。

**🟢 现在只需要记住什么**

1. 文件列表是**算出来的**——每次调用实时聚合 chunk metadata，没有"文件表"。
2. **dict 当 Map**——key=file_id 天然去重；值是"文件记录 + 计数器"。
3. 字段名会**翻译**——`file_size` → `size`、`ingestion_status` → `status`（API 契约说了算）。

---

## 95. T0107 核心对象 / 方法

### 第 8 个真实方法

| 问题      | 答案                                       |
| ------- | ---------------------------------------- |
| 方法      | `get_files(collection) -> List[Dict[str, Any]]`（Data Operations 组第 4 个） |
| 输入      | collection 名                             |
| 输出      | dict 列表，每个 6 个 key：`file_id, file_name, size, upload_time, chunk_count, status` |
| 依赖的既有能力 | `self._client`（T0102）、9 字段 metadata（T0104）、SPEC 7.3 一致性约束 |
| 将来谁调用   | File 管理 API（Phase 9，文件列表 `GET /api/files`）；前端知识库文件列表界面 |
| 错误路径    | 空 collection → 返回 `[]`；collection 不存在 → SDK 原始异常（Pending Question 同款） |

### 输出字段 vs metadata 字段对照表

| 输出 key（get_files） | 来源（chunk metadata 字段） | 说明                          |
| ----------------- | --------------------- | --------------------------- |
| `file_id`         | `file_id`             | 同名；也是聚合 key                 |
| `file_name`       | `file_name`           | 同名                          |
| `size`            | `file_size`           | **改名**（F016 API 契约用 size）   |
| `upload_time`     | `upload_time`         | 同名                          |
| `chunk_count`     | —                     | **算出来的**（计数器），metadata 里没有  |
| `status`          | `ingestion_status`    | **改名**（F016 API 契约用 status） |

> 认知呼应：这和 T0102 的 list_collections（对象 → 名字列表）、T0105 的 distance → similarity 是同一课——**边界上做翻译**。存储层内部说 `file_size`，对上层说 `size`。

---

## 96. T0106 → T0107 的关系

- **同一个 `col.get(...)` 的两种形态**：T0106 是"带 where 过滤 + `include=[]`"（只要某个文件的 ids）；T0107 是"不带 where + `include=["metadatas"]`"（要全量 metadata 做聚合）。同一 API，按需点餐。
- **删除与列表即时一致**：T0106 删掉某文件的所有 chunks 后，T0107 的 `get_files` 立刻不再返回该文件——因为聚合的数据源就是 chunks。没有"缓存失效"问题，这正是 7.3 无外部 DB 设计的好处之一。
- T0107 没用到 T0106 的代码，但认知上它们是 F016（文件管理）的一对：删（delete_by_file）+ 列（get_files）都服务于 Phase 9 的文件管理界面。

---

## 97. 当前架构中的位置

```text
┌────────────────────────────────────┐
│ Future: File API（Phase 9）        │
│ GET /api/files?collection_name=xxx │  ← 文件列表接口（F016）
└─────────────────┬──────────────────┘
                  │ 只调用 get_files
                  ▼
┌────────────────────────────────────┐
│ ChromaVectorStore.get_files        │  ← T0107 ✅
│ get(include=["metadatas"]) 全量    │
│ → dict 按 file_id 聚合 + 计数      │
│ → list(files.values())             │
└─────────────────┬──────────────────┘
                  │ 数据源就是 chunk metadata（T0104 写入的 9 字段）
                  ▼
┌────────────────────────────────────┐
│ ChromaDB（chroma_db/）             │
└────────────────────────────────────┘

（没有 SQLite / PostgreSQL / Redis —— v1 明确排除，SPEC 7.3）
```

### 值得注意的代价

"没有文件表"换来架构简单，但代价是 **get_files 每次都要全量扫描 chunks**（读放大）。v1 无性能 SLA（明确排除），可以接受；数据量大后这是第一个要还的债（届时再引入 metadata DB，即 SPEC 7.3 预留的未来方向）。

---

## 98. 为什么这样设计（只讲与 T0107 直接相关的原因）

1. **为什么不建 metadata 表？** SPEC 7.3 明令（v1 排除 SQLite/PostgreSQL/Redis）。更深的原因：单一数据源——chunk 是唯一事实来源，文件列表、统计、预览都从它聚合，**不存在"表和 ChromaDB 双写不一致"的可能**。
2. **为什么字段冗余在每条 chunk 上？** 删除文件 = 删 chunks，冗余字段跟着一起消失，无需级联清理；聚合时"取第一条"即可（SPEC 957 一致性约束保证）。
3. **为什么输出 `size` 而不是 `file_size`？** F016 API 契约（第 1561–1565 行）规定输出字段名。API 契约 > 内部命名习惯；翻译发生在存储层边界内部，上层无感。
4. **为什么 `chunk_count` 用计数器而不是 `len(分组)`？** 单遍扫描完成聚合：每个 chunk 出现一次就 +1，循环结束即有结果——O(n) 一趟，不需要先分组再数（两趟）。

---

## 99. Verification：T0107 验证了什么

### 验收依据

| 依据                       | 内容                                       |
| ------------------------ | ---------------------------------------- |
| TASKS T0107 验收           | 2 个文件（3 chunks + 5 chunks）→ 返回 2 条记录、chunk_count 正确；冗余字段一致；空 collection → 空列表 |
| SPEC 7.3（第 2249–2264 行）  | FileRecord 定义 + Persistence Strategy（无外部 DB / 冗余 + 聚合 / FAILED 无记录） |
| F016 文件列表（第 1561–1565 行） | 空 → 空列表；输出 6 字段                          |

### 验证手段的真实情况

与 T0106 相同：仓库**没有自动化测试脚本**。T0107 的实际验证形式是 TASKS.md 状态变更 + 实现 diff；"2 文件 8 chunks → 2 条记录"的聚合场景**没有本会话可查的执行记录**——不虚构 PASS。

### 怎么自己动手验（可选）

```python
store = ChromaVectorStore()
# 先往 collection 里写 file_a 3 chunks + file_b 5 chunks（同 T0104 方式）
files = store.get_files("test-kb")
assert len(files) == 2
assert {f["file_name"] for f in files} == {"file_a.pdf", "file_b.pdf"}
assert sum(f["chunk_count"] for f in files) == 8   # 3 + 5
```

（示意脚本，仓库里不存在；验证需真实 embedding 数据。）

---

## 100. T0107 代码阅读路线

| 顺序   | 文件 / 位置                                  | 只看什么                                     |
| ---- | ---------------------------------------- | ---------------------------------------- |
| 1    | [vector_store.py:402-432](../../backend/app/core/vector_store.py#L402-L432) | `get_files` 实现（本 Task 唯一产物）              |
| 2    | [SPEC.md:2249-2264](../../docs/SPEC.md#L2249-L2264) | Section 7.3 FileRecord + Persistence Strategy（为什么没有文件表） |
| 3    | [SPEC.md:1561-1565](../../docs/SPEC.md#L1561-L1565) | F016 文件列表 API（输出 6 字段的出处）                |
| 4    | [SPEC.md:955-961](../../docs/SPEC.md#L955-L961) | File-level metadata 一致性 + get_files 实现说明 + FAILED ingestion |
| 5    | [TASKS.md:587-628](../../docs/TASKS.md#L587-L628) | T0107 的 Scope / Out of Scope             |

**如果能解释下面这件事，就算看懂**："`get_files` 的数据源是什么？为什么 `if fid not in files` 能去重？输出里的 `size` 为什么不是 `file_size`？"

---

## 101. T0107 阶段只需要掌握的 5 件事

1. **文件列表是"算出来的"**——`get_files` 每次实时聚合 chunk metadata，v1 没有文件表（SPEC 7.3 Persistence Strategy 第一次落地）。
2. **dict 当 Map 用**——key = file_id（天然去重），value = 文件记录 + 计数器。
3. **计数器模式**——首条初始化（chunk_count=0），之后每条 `+= 1`；单遍 O(n) 聚合。
4. **字段名翻译**——`file_size` → `size`、`ingestion_status` → `status`，输出形状由 F016 API 契约决定。
5. **FAILED 入库的文件自然缺席**——没有 chunks 就没有记录，SPEC 961 的语义自动成立，无需特判。

---

## 102. 现在可以暂时不懂（T0107 相关）

| 不懂的                          | 为什么可以先放                                  |
| ---------------------------- | ---------------------------------------- |
| Python dict 的插入顺序保证（3.7+ 保序） | get_files 的契约没有规定文件排序，调用方不依赖顺序           |
| `where` 高级语法（`$and` 等）       | v1 只用单条件过滤                               |
| "读放大"的性能优化（索引、缓存）            | v1 无性能 SLA（明确排除）；数据量大时再引入 metadata DB（SPEC 7.3 的未来方向） |
| `typing.Dict` 与内置 `dict` 的区别 | 标注语境下两者等价，`Dict` 是兼容旧版本的写法               |

---

## 103. T0107 5 道基础自测题

> 先自己想，不要急着看答案（线索在第 92–94 节）。

**Q1**：`get_files` 的数据从哪里来？v1 为什么不建 metadata 表？（两个层面：SPEC 怎么规定、这样设计换来了什么）

**Q2**：`if fid not in files` 检查的是什么？dict 当 Map 用时，"去重"是怎么自然发生的？

**Q3**：为什么输出的 key 是 `size` / `status` 而不是 `file_size` / `ingestion_status`？这种翻译发生在哪里？

**Q4**：空 collection 时 `get_files` 返回什么？FAILED 入库的文件会出现在列表里吗？为什么？

**Q5**：`list(files.values())` 里的 `list()` 是干什么的？去掉它直接 `return files.values()` 会怎样？

---

## 104. T0107 3 个小练习

> 都不修改正式代码。

### 练习 1：把 `get_files` 翻译成 TypeScript（两种写法）

先写第 93 节的 Map 版本；再用 `reduce` 重写一遍。翻译后自查：Python 的 `files[fid]["chunk_count"] += 1` 在 TS 里为什么必须写成 `files.get(fid)!.chunkCount += 1`（Map 的坑）？

### 练习 2：画聚合过程图

画 8 条 chunk metadata（file_a ×3、file_b ×5）依次流过循环时，`files` dict 的每一步变化（第 1 条 file_a → 第 2 条 file_a → 第 1 条 file_b → …）。重点标出 `if fid not in files` 为真 / 为假的分支。

### 练习 3：判断这段"优化"错在哪

```python
for meta in metadatas:
    fid = meta["file_id"]
    if fid not in files:
        files[fid] = {"file_id": fid, ..., "chunk_count": 1}   # 初始化时直接写 1
    files[fid]["chunk_count"] += 1                             # 然后还 +1
```

跑起来 chunk_count 会是多少？正确的两种写法分别是什么？（提示：初始化 0 + 每条 +1；或初始化 1 + 只在"非首条"时 +1。）

---

## 105. T0107 快速复习卡

> 3 分钟看完。

### 一句话

> T0107 把 `get_files` 变成真实实现：全量取 chunk metadata → dict 按 file_id 聚合 + 计数 → 输出 6 字段文件列表。没有文件表，列表是算出来的（SPEC 7.3）。

### 5 个关键词

1. **get_files** — Data Operations 组第四个真实方法（第 8/11 个）
2. **Persistence Strategy** — 无外部 DB；文件记录 = 聚合结果（SPEC 7.3）
3. **dict 当 Map** — key = file_id 天然去重
4. **计数器模式** — 首条初始化 + 每条 `+= 1`（单遍 O(n)）
5. **字段名翻译** — `file_size` → `size`、`ingestion_status` → `status`

### 最重要调用关系

```text
get_files
  → get_collection(collection).get(include=["metadatas"])["metadatas"]   # 全量 metadata
  → files: Dict[str, Dict[str, Any]] = {}                                # 聚合容器
  → for meta in metadatas: 首见建记录 / 每条 chunk_count += 1
  → return list(files.values())                                          # 视图 → 列表
```

### 3 个易混淆点

1. **`get_files` 输出里的 `size`/`status` 不是 metadata 原名** —— 边界翻译，API 契约（F016）说了算；读代码时别以为输出 key 和 metadata key 一一对应。
2. **"文件列表"没有独立存储** —— 每次调用实时聚合。删光 chunks 的文件立刻消失（一致），但每次列表都要全量扫描（读放大，v1 可接受）。
3. **`files.values()` 不是 list** —— 它是"视图"对象；契约要 `List[Dict]` 就必须 `list()` 包一层。

### 当前实现进度

| 事项                                       | 状态                                |
| ---------------------------------------- | --------------------------------- |
| T0101–T0106：契约 + 生命周期 + 写入 + 检索 + 删除     | ✅ DONE                            |
| T0107：get_files 文件列表                     | ✅ DONE（本次）                        |
| T0108：list_chunks / count / get_chunks_by_file | ⬜ 下一步（→ T0108）                    |
| 今天能列出知识库的文件列表吗（存储层）                      | ✅ 能（聚合 chunk metadata）            |
| 今天能看到文件列表界面吗                             | ❌ 不能（File API / 前端界面是 Phase 9 的事） |

---

> **下一步学习**：T0108 完成后，回来看最后 3 个方法（list_chunks / get_chunk_count / get_chunks_by_file）——以及项目里第一个 `@staticmethod` 私有辅助方法。

---

## T0108 部分（追加）

> 第 106–119 节为 T0108 完成后的追加内容。T0108 = Chunk Metadata Access 三个方法（list_chunks / get_chunk_count / get_chunks_by_file）+ 私有辅助 `_to_chunk_records`。真实代码：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) 第 434–495 行（文件现 495 行）。

---

## 106. T0108 到底解决了什么问题

### 一句话

T0108 是 Phase 1 的收尾 Task——把最后 3 个方法全部实现，并抽出项目里第一个私有辅助方法。**至此 11/11 个方法全部真实，0 个占位，Phase 1 收官。**

### "方法存在 ≠ 功能可用"的旅程收尾

回看第 22 节的那句话：T0102 完成时 11 个方法里 8 个是占位。这条学习主线至此完整收束：

```text
T0102 完成：8 个 stub（3 真实）          "能创建/列出/删除 knowledge base"
T0103 完成：7 个 stub（rename 点亮）     "能重命名"
T0104 完成：6 个 stub（add_texts 点亮）  "能写入"
T0105 完成：5 个 stub（search 点亮）     "能检索"
T0106 完成：4 个 stub（delete 点亮）     "能删除文件数据"
T0107 完成：3 个 stub（get_files 点亮）  "能列文件"
T0108 完成：0 个 stub（3 个全点亮）      "能列 chunks / 计数 / 按文件取 chunks"
```

### 本 Task 实现的 4 样东西

| 方法 / 辅助                                  | 行为                                       | 将来谁用                             |
| ---------------------------------------- | ---------------------------------------- | -------------------------------- |
| `_to_chunk_records(got)`（私有静态辅助）         | ChromaDB `get()` 输出 → `List[ChunkRecord]` | 下面两个方法共用                         |
| `list_chunks(collection)`                | 全量 chunks（**不含 embedding**）              | Keyword Retriever 建倒排索引（Phase 6） |
| `get_chunk_count(collection)`            | 总 chunk 数                                | 统计界面                             |
| `get_chunks_by_file(collection, file_id)` | 某文件全部 chunks，**按 chunk_index 升序**        | F016 文件预览（按顺序拼回原文）               |

### ChunkRecord 首秀

T0101 定义的 `ChunkRecord` 模型（7 个字段）**第一次被实例化**。它的字段表里没有 embedding——"字段表里没有的东西调用方拿不到"第二次出现（第一次是 T0105 的 VectorSearchResult 没有 distance）。类型层的数据最小化。

### 刻意不做

| 不做的事         | 依据                                       |
| ------------ | ---------------------------------------- |
| 返回 embedding | SPEC 932–935 行明令 list_chunks 不含 embedding；ChunkRecord 模型无该字段 |
| 分页 / limit   | v1 无性能 SLA（明确排除）                         |

---

## 107. 以前端开发者的方式理解 T0108

### TypeScript 心智模型

```ts
// 私有静态辅助：get() 输出 → ChunkRecord[]
private static toChunkRecords(got: { ids: string[]; documents: string[]; metadatas: any[] }): ChunkRecord[] {
  return got.ids.map((id, i) => new ChunkRecord({
    chunkId: id,
    fileId: got.metadatas[i].file_id,
    file_name: got.metadatas[i].file_name,
    collectionName: got.metadatas[i].collection_name,
    chunkIndex: got.metadatas[i].chunk_index,
    content: got.documents[i],
    metadata: got.metadatas[i],
  }));
}

listChunks(collection: string): ChunkRecord[] {
  const got = this.client.getCollection(collection)
    .get({ include: ["documents", "metadatas"] });   // 故意没有 embeddings
  return ChromaVectorStore.toChunkRecords(got);
}

getChunksByFile(collection: string, fileId: string): ChunkRecord[] {
  const got = this.client.getCollection(collection)
    .get({ where: { file_id: fileId }, include: ["documents", "metadatas"] });
  return ChromaVectorStore.toChunkRecords(got)
    .sort((a, b) => a.chunkIndex - b.chunkIndex);     // 升序
}
```

### 三个熟悉的模式

1. **抽 helper 去重复（DRY）**——`list_chunks` 和 `get_chunks_by_file` 都要做同一件事："get() 输出 → ChunkRecord 列表"。同一个翻译逻辑写两遍 = 将来改 ChunkRecord 要改两个地方。抽成 `_to_chunk_records` 后只改一处。
2. **static 方法**——helper 不需要 `this`（不碰 `self._client`），只是"挂在类上的纯函数"。TS 里 `static` 是同一概念。
3. **默认升序排序**——JS 的 `sort((a,b) => a-b)` 就是升序；Python 的 `sort(key=...)` 不写 `reverse=True` 也是升序（对比 T0105 写了 `reverse=True` 降序）。

---

## 108. T0108 真实代码阅读（代码片段 17 + 18）

### 代码片段 17：私有辅助 `_to_chunk_records`（第 436–453 行）

**Python 原代码**（[vector_store.py:436-453](../../backend/app/core/vector_store.py#L436-L453)）

```python
    @staticmethod
    def _to_chunk_records(got: Dict[str, Any]) -> List[ChunkRecord]:
        """Map ChromaDB get() output to ChunkRecord list (no embeddings)."""
        records = []
        for i in range(len(got["ids"])):
            meta = got["metadatas"][i]
            records.append(
                ChunkRecord(
                    chunk_id=got["ids"][i],
                    file_id=meta["file_id"],
                    file_name=meta["file_name"],
                    collection_name=meta["collection_name"],
                    chunk_index=meta["chunk_index"],
                    content=got["documents"][i],
                    metadata=meta,
                )
            )
        return records
```

**🟢 Python 语法怎么读**

- `@staticmethod` — 装饰器：**这个方法没有 `self`**。它不需要实例状态，只是"住在类里的普通函数"（→ python 手册 17.9）。项目里第一次出现。
- `_to_chunk_records` — `_` 前缀 = 私有约定（和第 6 节 `self._client` 同一套）。名字里的 `to_` 暗示这是"翻译函数"。
- `got: Dict[str, Any]` — 入参就是 ChromaDB `get()` 的返回 dict（`ids` / `documents` / `metadatas` 三个 key）。`Dict[str, Any]` = "任意形状的字典"——翻译函数吃"杂数据"，吐"规整模型"。
- `for i in range(len(got["ids"])):` — **索引循环**（第 17.6 节复习）。为什么这里不用 `for x in metadatas`（T0107 那样）？因为一个 ChunkRecord 要同时从**三个列表**（ids / documents / metadatas）取同一下标——这是索引循环的经典适用场景。
- `meta = got["metadatas"][i]` — 先取出这一条的 metadata dict（后面要从中取 5 个字段）。
- `records.append(...)` — `append`（第 17.8 节复习）；`records = []` 先建空列表。
- `ChunkRecord(chunk_id=..., file_id=..., ...)` — **T0101 模型首次实例化**，7 个 kwarg 全填（和 T0105 的 `VectorSearchResult(...)` 同款写法）。
- `chunk_index=meta["chunk_index"]` — metadata 里存的是 int，模型字段也是 int，直接透传。

**🟢 TypeScript / Node.js 类比**（见第 107 节开头，含 static 版本）

**🟡 在 DX-RAG 中的作用**

- 这是项目第一个"从 SDK 原始输出翻译成领域模型"的**独立函数**。之前 T0105 的翻译（distance → similarity）内联在 search 里；这里因为**两个方法要用同一套翻译**，抽出来了（DRY）。
- `include=["documents", "metadatas"]`——**刻意没有 embeddings**：契约（SPEC 932–935）禁止 + ChunkRecord 模型没有该字段 + 向量体积大且上层用不上。三保险。
- `chunk_index` 来自 metadata（T0104 写入的 9 字段之一），注意它是 **int**——排序和"拼回原文"都靠它。

### 代码片段 18：三个方法（第 455–495 行）

**Python 原代码**（[vector_store.py:455-495](../../backend/app/core/vector_store.py#L455-L495)）

```python
    def list_chunks(self, collection: str) -> List[ChunkRecord]:
        """List all chunks in a collection (without embedding vectors).
        Used by Keyword Retriever for building the inverted index."""
        col = self._client.get_collection(collection)
        got = col.get(include=["documents", "metadatas"])
        return self._to_chunk_records(got)

    def get_chunk_count(self, collection: str) -> int:
        """Get the total number of chunks in a collection."""
        return self._client.get_collection(collection).count()

    def get_chunks_by_file(self, collection: str, file_id: str) -> List[ChunkRecord]:
        """Get all chunks for a specific file, ordered by chunk_index ASC."""
        col = self._client.get_collection(collection)
        got = col.get(where={"file_id": file_id}, include=["documents", "metadatas"])
        records = self._to_chunk_records(got)
        records.sort(key=lambda r: r.chunk_index)
        return records
```

**🟢 Python 语法怎么读**

- `list_chunks` — `col.get(...)` 不带 where = 全量；翻译交给 `_to_chunk_records`；`return` 直接返回翻译结果（helper 让方法体只有 3 行）。
- `get_chunk_count` — `.count()` 是 ChromaDB SDK 自带的计数方法，**一行搞定**。对比 T0106 的"先数后删"：那里 delete 不返回数量才需要绕；这里 SDK 直接给了 count，就用现成的。
- `get_chunks_by_file` — `where={"file_id": file_id}`（T0106 同款过滤）+ `records.sort(key=lambda r: r.chunk_index)`（T0105 同款 key 排序）。
- **没有 `reverse=True` = 升序**——契约要求 chunk_index ASC（SPEC 928–930 行），Python 的 `sort` 默认就是升序，什么都不用写（对比 T0105 的 `reverse=True` 降序）。

**🟢 TypeScript / Node.js 类比**

- `list_chunks` ≈ `getAll().map(toChunkRecord)`（没有过滤的全量映射）
- `get_chunk_count` ≈ `client.count()`（SDK 现成能力，不自己数）
- `get_chunks_by_file` ≈ `get({where}).map(...).sort((a,b) => a.chunkIndex - b.chunkIndex)`

**🟡 在 DX-RAG 中的作用**

- `list_chunks` 是 **Keyword Retriever（Phase 6）的原料**：倒排索引需要"所有 chunk 的文本 + chunk_id"，由 SPEC 932–935 明确指定。**必须走 public interface**（AC-F008-03）——外部代码不允许摸 `_client`。
- `get_chunks_by_file` 是 **F016 文件预览（SPEC 1567–1585 行）的原料**：按 chunk_index 升序取回 → `\n\n` 拼接 → 最多 5000 字符。预览只依赖"已入库的 chunks"，**永远不重新解析 uploads/ 里的原始文件**。
- `get_chunk_count` 给统计界面 / 后续任务用。

**🟢 现在只需要记住什么**

1. helper 是 **DRY** 的第一次落地——两个方法共享"get 输出 → ChunkRecord"翻译。
2. `include` 永远不含 embeddings——契约 + 模型 + 体积三保险。
3. 升序是**默认**——契约要 ASC 就什么都不写；要 DESC 才写 `reverse=True`。

---

## 109. T0108 核心对象 / 方法

### 三个新方法 + 一个辅助

| 方法 / 辅助              | 输入                    | 输出                  | 特殊点                           |
| -------------------- | --------------------- | ------------------- | ----------------------------- |
| `_to_chunk_records`  | `got: Dict[str, Any]` | `List[ChunkRecord]` | `@staticmethod`，无 self，`_` 私有 |
| `list_chunks`        | collection            | `List[ChunkRecord]` | 全量，无排序约定，无 embedding          |
| `get_chunk_count`    | collection            | `int`               | 一行：SDK 自带 `.count()`          |
| `get_chunks_by_file` | collection + file_id  | `List[ChunkRecord]` | where 过滤 + chunk_index 升序     |

### 两个模型的字段对照（第 10 节模型表的实战版）

| ChunkRecord（T0108 首次实例化）                 | VectorSearchResult（T0105 首次实例化）          |
| ---------------------------------------- | ---------------------------------------- |
| chunk_id / file_id / file_name / collection_name / chunk_index / content / metadata | chunk_id / file_id / file_name / content / similarity_score / metadata |
| **没有 embedding**                         | **没有 distance**                          |

> 共同点：两个模型都**故意少放字段**。原始数据里有 embedding / distance，但模型不装——"类型表上没有的，调用方拿不到"。数据最小化靠类型系统执行，不靠自觉。

### 错误路径

- 空 collection：`list_chunks` → `[]`；`get_chunk_count` → `0`；`get_chunks_by_file`（file 不在）→ `[]`。
- collection 不存在：SDK 原始异常（与 T0104–T0107 同款 Pending Question，见第 81 节记录）。

### Phase 1 收官全景

```text
VectorStore ABC（T0101 契约）── 11 个签名
        │
        ▼
ChromaVectorStore（T0102–T0108 全部实现）── 11/11 真实 ✅

Collection Lifecycle（4）：create ✅ delete ✅ list ✅ rename ✅
Data Operations（4）：      add_texts ✅ search ✅ delete_by_file ✅ get_files ✅
Chunk Metadata Access（3）：list_chunks ✅ get_chunk_count ✅ get_chunks_by_file ✅
辅助（1，不在契约内）：      _to_chunk_records（@staticmethod 私有）
```

---

## 110. T0107 → T0108 的关系

- **共用 T0107 的 get 模式**：T0107 的 `col.get(include=["metadatas"])` 全量形态 → T0108 的 `list_chunks` 用 `include=["documents", "metadatas"]`；T0106 的 `where=...` 过滤形态 → T0108 的 `get_chunks_by_file` 复用。三种 include / 两种 get 形态至此都出现过了。
- **T0107 聚合到文件级，T0108 翻译到 chunk 级**：同一个数据源（T0104 的 9 字段 metadata），T0107 按 file_id 压成文件列表，T0108 原样展开成 ChunkRecord 列表。列表 / 统计 / 预览三类上层需求，Phase 1 的存储层都已备好原料。
- T0108 收尾后，**ChunkRecord 的 `collection_name` 字段第一次被真正消费**（从 metadata 取出填入模型）——T0101 定义时它只是字段表里的一行。

### 给未来 Phase 的积木（只列直接相关）

| 未来                         | 用哪个方法                                |
| -------------------------- | ------------------------------------ |
| Keyword Retriever（Phase 6） | `list_chunks`（建倒排索引，SPEC 932–935）    |
| 文件预览（Phase 9，F016）         | `get_chunks_by_file`（升序 + `\n\n` 拼接） |
| 统计 / 监控                    | `get_chunk_count`                    |

---

## 111. 当前架构中的位置

```text
┌────────────────────────────────────────────────────────┐
│ Future Services                                        │
│ Keyword Retriever（Phase 6）→ list_chunks             │
│ File API 预览（Phase 9）    → get_chunks_by_file       │
│ 统计界面                    → get_chunk_count          │
└────────────────────────────┬───────────────────────────┘
                             │ 只走 public interface（AC-F008-03）
                             ▼
┌────────────────────────────────────────────────────────┐
│ VectorStore (ABC) ← T0101 ✅   11 个方法签名            │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│ ChromaVectorStore ← T0102–T0108 ✅（11/11 全部真实）    │
│ 本次新增：_to_chunk_records（@staticmethod）            │
│           list_chunks / get_chunk_count /               │
│           get_chunks_by_file                            │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│ ChromaDB（chroma_db/）                                 │
└────────────────────────────────────────────────────────┘
```

Phase 1 的存储层至此完整：**所有 ChromaDB 操作都收敛在这一个类里**，上层只能通过 ABC 契约调用。

---

## 112. 为什么这样设计（只讲与 T0108 直接相关的原因）

1. **为什么抽 `_to_chunk_records`？** 两个方法（list_chunks / get_chunks_by_file）要做同一套翻译；写两遍的话，将来 ChunkRecord 加字段要改两处。DRY（Don't Repeat Yourself）——这是项目里第一个独立 helper。
2. **为什么 `@staticmethod`？** 翻译不依赖实例状态（不碰 `self._client`），是纯函数——"入参 → 出参"。static 表达了这个语义：caller 传什么就翻译什么。`_` 前缀继续私有约定。
3. **为什么列表方法不带 embedding？** 三层理由：SPEC 932–935 明令（list_chunks 不含 embedding vector）；ChunkRecord 模型字段表没有 embedding（类型层挡住）；向量体积大、上层（倒排索引 / 预览）用不上。**契约 + 类型 + 实际需求三层一致**。
4. **为什么 `get_chunk_count` 一行而 T0106 要两步？** SDK 能力差异：`.count()` 直接返回数量；`delete()` 不返回数量。**SDK 给了现成的就用现成的**，没有才自己绕（T0106 的先数后删）。
5. **为什么排序放在 helper 外面（get_chunks_by_file 里）而不是里面？** list_chunks 的契约**没有**排序要求，只有 get_chunks_by_file 要求 ASC。排序是"某个方法的语义"不是"翻译本身的语义"——放外面，helper 保持通用。

---

## 113. Verification：T0108 验证了什么

### 验收依据

| 依据                           | 内容                                       |
| ---------------------------- | ---------------------------------------- |
| TASKS T0108 验收               | list_chunks 返回全部 ChunkRecord（无 embedding）；get_chunk_count 返回正确总数；get_chunks_by_file 只返回该文件且按 chunk_index ASC；ChunkRecord 字段与 chunk 数据一致 |
| AC-F008-03（SPEC 第 987–990 行） | Keyword Retriever 调 `list_chunks()` / QA 调 `search()` **通过 public interface，不访问 `_collection`** |
| SPEC 932–935 行               | list_chunks 不含 embedding；供 Keyword Retriever 建倒排索引 |
| F016 文件预览（SPEC 1567–1585 行）  | get_chunks_by_file + chunk_index ASC + `\n\n` 拼接 + MAX_PREVIEW_CHARS=5000（拼接与截断是 Phase 9 的事） |

### 验证手段的真实情况

与前两个 Task 相同：仓库**没有自动化测试脚本**，验证形式 = TASKS.md 状态变更 + 实现 diff。AC-F008-03 的"public interface"要求在**结构上**是满足的——`ChromaVectorStore` 只有 `self._client`（私有），**类里根本没有 `_collection` 这个属性**，外部无从访问。但无执行记录，不虚构 PASS。

### 怎么自己动手验（可选）

```python
store = ChromaVectorStore()
assert store.get_chunk_count("test-kb") == 8           # 承接 T0107 的场景
chunks = store.get_chunks_by_file("test-kb", file_id_a)
assert [c.chunk_index for c in chunks] == [0, 1, 2, 3, 4]   # 升序
assert all(c.embedding is None for c in chunks)        # 模型里根本没有 embedding 字段
```

（示意脚本，仓库里不存在。）

---

## 114. T0108 代码阅读路线

| 顺序   | 文件 / 位置                                  | 只看什么                                     |
| ---- | ---------------------------------------- | ---------------------------------------- |
| 1    | [vector_store.py:436-453](../../backend/app/core/vector_store.py#L436-L453) | `_to_chunk_records`（@staticmethod helper） |
| 2    | [vector_store.py:455-495](../../backend/app/core/vector_store.py#L455-L495) | 三个方法（共 15 行真实逻辑）                         |
| 3    | [SPEC.md:928-935](../../docs/SPEC.md#L928-L935) | Public Interface 三个条目 + list_chunks 方法说明 |
| 4    | [SPEC.md:987-990](../../docs/SPEC.md#L987-L990) | AC-F008-03（public interface 禁令）          |
| 5    | [SPEC.md:1567-1585](../../docs/SPEC.md#L1567-L1585) | F016 文件预览（get_chunks_by_file 的消费方式）      |
| 6    | [TASKS.md:631-668](../../docs/TASKS.md#L631-L668) | T0108 的 Scope / Out of Scope             |

**如果能解释下面这件事，就算看懂**："`_to_chunk_records` 为什么可以没有 `self`？`list_chunks` 的 include 为什么没有 embeddings？`get_chunks_by_file` 的排序为什么不用 `reverse=True`？"

---

## 115. T0108 阶段只需要掌握的 5 件事

1. **Phase 1 收官**——11/11 方法全部真实实现，0 个占位；"方法存在 ≠ 功能可用"的主线收束。
2. **`_to_chunk_records` 是第一个私有静态 helper**——DRY：两个方法共享同一套"get 输出 → ChunkRecord"翻译。
3. **`@staticmethod` = 没有 self 的方法**——不碰实例状态的"挂在类上的纯函数"（≈ TS static）。
4. **ChunkRecord 首秀 + 类型防泄露**——模型 7 字段没有 embedding（第二例：VectorSearchResult 没有 distance）。
5. **升序是默认**——`sort(key=...)` 不写 `reverse=True` 就是 ASC（契约要求 ASC，正好什么都不写）。

---

## 116. 现在可以暂时不懂（T0108 相关）

| 不懂的                                     | 为什么可以先放                 |
| --------------------------------------- | ----------------------- |
| ChromaDB `get()` 的分页 / limit / offset   | v1 无性能 SLA，全量取          |
| Keyword Retriever 怎么用 list_chunks 建倒排索引 | Phase 6 的领地，届时再学        |
| 全量扫描的性能优化                               | 与第 97 节的"读放大"同一笔债，v1 不还 |
| `@classmethod`（与 `@staticmethod` 的兄弟）   | 项目里还没用到，遇到再学            |

---

## 117. T0108 5 道基础自测题

> 先自己想，不要急着看答案（线索在第 106–108 节）。

**Q1**：T0108 实现了哪 3 个方法 + 1 个辅助？Phase 1 完成后，11 个方法的状态是什么？

**Q2**：`@staticmethod` 是什么意思？为什么 `_to_chunk_records` 可以没有 `self`？TS 里的对应概念是什么？

**Q3**：为什么 `list_chunks` 的 `include` 只有 documents/metadatas？ChunkRecord 模型为什么没有 embedding 字段？（说出三层理由）

**Q4**：`get_chunks_by_file` 的排序为什么不用 `reverse=True`？契约要求什么顺序？这个顺序将来给谁用？

**Q5**：`get_chunk_count` 为什么能一行搞定，而 T0106 的 `delete_by_file` 要先 get 再 delete？两者差在哪？

---

## 118. T0108 3 个小练习

> 都不修改正式代码。

### 练习 1：把 `_to_chunk_records` 翻译成 TypeScript static 方法

参考第 107 节的 TS 心智模型，自己写一遍（含类型）。翻译后自查：TS 的 static 方法挂在类上怎么调用（`ChromaVectorStore.toChunkRecords(...)`）？Python 的 `@staticmethod` 调用时也可以用类名调用——这体现了什么？

### 练习 2：画 Phase 1 全景图

画一张 Phase 1 收官图：ABC 的 11 个签名 → ChromaVectorStore 的 11 个实现，每个标上"哪个 Task 实现的"。再标出 2 个模型（ChunkRecord / VectorSearchResult）分别在哪两个 Task 被首次实例化。完成后对照第 109 节。

### 练习 3：判断这两段"改动"分别错在哪

```python
# 改动 A：list_chunks 加上 embeddings
got = col.get(include=["documents", "metadatas", "embeddings"])   # ← 判断这里

# 改动 B：get_chunks_by_file 去掉排序
records = self._to_chunk_records(got)
return records        # ← 判断这里（原来是 sort 后再 return）
```

从三个角度想：SPEC 契约、模型字段表、上层消费方（Keyword Retriever / 文件预览）会怎么坏。

---

## 119. T0108 快速复习卡

> 3 分钟看完。Phase 1 最后一次复习。

### 一句话

> T0108 实现最后 3 个方法 + 第一个 `@staticmethod` 私有辅助，11/11 方法全部真实——Phase 1（VectorStore 存储层）收官。

### 5 个关键词

1. **11/11** — 全部真实实现，0 个占位（T0102 时的 8 个 stub 全部填完）
2. **`_to_chunk_records`** — 第一个私有静态 helper（DRY）
3. **`@staticmethod`** — 没有 self 的类方法（项目首秀）
4. **ChunkRecord** — T0101 模型首次实例化；无 embedding（类型防泄露第二例）
5. **ASC 默认** — `sort(key=...)` 不写 reverse 就是升序（对比 T0105 的 DESC）

### 最重要调用关系

```text
list_chunks        → get(include=["documents","metadatas"]) → _to_chunk_records → List[ChunkRecord]
get_chunk_count    → get_collection(collection).count()     → int
get_chunks_by_file → get(where={file_id}, include=[...])    → _to_chunk_records → sort(chunk_index ASC)
```

### 3 个易混淆点

1. **`list_chunks` 没有排序约定，`get_chunks_by_file` 才有** —— 排序是方法的语义，不是翻译的语义（所以 sort 在 helper 外面）。
2. **"能列 chunks" ≠ "倒排索引已存在"** —— list_chunks 只是原料；Keyword Retriever 是 Phase 6 的消费者，现在还没人调用这些方法。
3. **`@staticmethod` 不是"另一种 def"** —— 它改变的是"方法要不要 self"；逻辑上它就是个普通函数，只是组织在类里。

### Phase 1 收官进度表

| 事项                                       | 状态                       |
| ---------------------------------------- | ------------------------ |
| T0101：契约（ABC + 11 签名 + 2 模型）             | ✅ DONE                   |
| T0102：初始化 + collection 生命周期 3 方法         | ✅ DONE                   |
| T0103：rename_collection                  | ✅ DONE                   |
| T0104：add_texts 写入                       | ✅ DONE                   |
| T0105：search 向量检索                        | ✅ DONE                   |
| T0106：delete_by_file 删除                  | ✅ DONE                   |
| T0107：get_files 文件列表                     | ✅ DONE                   |
| T0108：list_chunks / count / get_chunks_by_file | ✅ DONE（本次）               |
| 存储层的全部能力（写入 / 检索 / 删除 / 列表 / 计数）         | ✅ 11/11                  |
| 今天有人调用这些方法吗                              | ❌ 还没有——业务层（Phase 3+）尚未出现 |

---

---

## Part 9 — 收尾整合（整理版新增）

> Phase 1 学完后的总复习。自测题没有答案（先自己答，答不出再回分 Task 部分找）；练习不碰正式代码。

### 9A. Phase 1 只需要真正掌握的 10 件事

1. VectorStore 是契约（ABC），ChromaVectorStore 是实现——能实例化的只有后者；上层只认前者。（第 6 节）
2. 所有 ChromaDB 操作必须走 11 个 public methods；`_client` 不对外（F008 约束 2/3 + AC-F008-03）。（第 8 节）
3. 一个知识库 = 一个 collection；创建时写死 cosine（`hnsw:space=cosine`），选型不可改。（第 24 节）
4. add_texts 是搬运工：chunk_id / embeddings / schema 校验都是上游的事，三份名单按位置对齐。（第 56 节）
5. search 内部完成 distance → similarity：`clamp(1.0 - distance)`；外部只看到"越大越相似"，且禁止二次归一化。（第 66 节）
6. 先数后删（SDK 的 delete 不返回数量）；include= 决定取回什么；where= 按 metadata 过滤。（第 84 节）
7. 没有文件表：get_files 实时聚合 chunk metadata（SPEC 7.3）；FAILED 入库没有 chunk → 文件自然不出现。（第 97 节）
8. file_id / chunk_id 是身份（UUID）；file_name 只是显示名；chunk_index 只是排序号。（第 4 节片段 2）
9. 类型防泄露出现两次：VectorSearchResult 不含 distance、ChunkRecord 不含 embedding。（第 67/109 节）
10. 11/11 真实实现、0 占位；但今天没有任何业务调用方——Phase 3+ 才有（第 119 节）。

### 9B. 现在可以暂时不懂的内容（Phase 1 级汇总）

| 内容 | 为什么可以暂时不懂 | 什么时候需要 |
|------|------------------|-------------|
| Dependency Inversion / Adapter 的理论定义 | 第 21 节有操作版类比（TS interface 已经很接近） | 面试 / 设计评审 |
| ABC 的 metaclass 底层机制 | Python 运行时细节，不影响使用 | 写元编程时 |
| HNSW / cosine 的数学原理 | 选型已由 SPEC 定死，只需知道"建库时写死" | 做检索优化时 |
| ChromaDB where 的高级过滤（$and/$or） | v1 只用单条件等值过滤 | 做复合查询时 |
| get_files 的读放大（全表拉 metadata） | 学习期数据量小；SPEC 7.3 有意为之 | 性能调优时 |
| dict.values() 视图的内存语义 | 知道"要 list() 包一层"就够用 | 深入内存管理时 |
| Milvus 的具体 API | v1 明确不用 | Phase 之外的扩展 |

### 9C. 完整代码阅读路线（一次读完 495 行）

打开 [vector_store.py](../../backend/app/core/vector_store.py)（495 行），按顺序读：

1. 第 1–18 行 文件 docstring —— 就是 F008 的浓缩版（4 约束 + 距离公式）。读完能背出公式就算过。
2. 第 20–27 行 imports —— abc / typing / chromadb / pydantic / config / errors，每个 import 都能说出一句用途。
3. 第 35–75 行 两个模型 —— ChunkRecord（7 字段，无 embedding）+ VectorSearchResult（6 字段，无 distance）。类型防泄露的第一道关。
4. 第 83–229 行 ABC 11 个签名 —— 对照 Part 0 的 0C 表逐组核对；只看 docstring，不看实现（这里本来也没有实现）。
5. 第 237–254 行 实现类 + `__init__` —— `_client = PersistentClient(...)` 是唯一私有入口；chroma_db/ 目录从这里来。
6. 第 257–301 行 生命周期 4 方法 —— 注意 rename 是唯一带校验的（`not in` → AppError）。
7. 第 305–338 行 add_texts —— 一行提取 ids、一次 SDK 调用、返回 ids。
8. 第 340–383 行 search —— Phase 1 最重要方法：三层嵌套取数 + clamp 一行 + 排序。其余 10 个方法都不如它值得精读。
9. 第 385–400 行 delete_by_file —— 先 get 数、再 delete。
10. 第 402–432 行 get_files —— dict 计数器聚合 + 字段翻译。
11. 第 436–495 行 helper + 三个读取方法 —— _to_chunk_records 一次写完、三处复用；注意 @staticmethod 不接收 self。

读完能回答 3 个问题：① 类外有没有直接操作 collection 对象的代码？（应该没有——都在类内。）② 距离值在哪一行之后不存在了？（clamp 那行之后。）③ 哪两个方法会返回 ChunkRecord？（list_chunks / get_chunks_by_file。）

### 9D. 10 道基础 / 项目理解自测题（不给答案）

基础理解（每题一句话原则即可）：

1. VectorStore 和 ChromaVectorStore 是什么关系？为什么前者不能实例化？
2. 11 个方法分成几组？漏掉其中任何一个，上层会付出什么代价？
3. search 返回的分数范围是什么？为什么必须 clamp？clamp 的公式怎么写？
4. 为什么 delete_by_file 要先 get 再 delete？`include=[]` 省掉了什么？
5. add_texts 的 chunk_id 为什么从 metadatas 里提取，而不是自己生成？embeddings 为什么由调用方提供？

项目理解（需要联系 SPEC / 架构）：

6. get_files 的数据源是什么？"没有文件表"是 SPEC 的哪个决策（第几节）？换来什么、代价是什么？
7. 一个文件重新上传后，file_id 会变吗？知识库重命名后，chunk_id 会变吗？为什么删除键必须用 file_id？
8. 类型防泄露出现过哪两次？分别靠什么机制挡住什么字段？
9. F001 重命名 8 步里，Phase 1 做了哪几步？F016 删除 7 步呢？"没做完的步骤"由哪个 Task 负责？
10. 今天（Phase 1 完成时）11 个方法有调用方吗？第一个调用方预计在哪个 Phase 出现？search 的调用方预计是谁？

（先自己答，答不出回对应的分 Task 节找——每道题都对应第 1–119 节里的具体章节。）

### 9E. 5 个小练习（不修改正式代码）

1. **默画架构图**：合上笔记，画出 0A 的四层架构图，标出 11 个方法的分组和每个分组点亮的 Task。画完对照 0A。
2. **手写 search 心智模型**：用 TS 伪代码写出 search 的全流程（query → 三层取数 → clamp → 排序），然后对照第 65 节的开头两段。
3. **亲手聚合一次**：造 8 条假 metadata（2 个 file_id，各自 3 条 + 5 条），用你熟悉的语言（TS 伪代码即可）实现 get_files 的聚合逻辑，核对 chunk_count 和字段翻译（file_size→size）。
4. **通读 + 一句话总结**：按 9C 的 11 段顺序通读 vector_store.py，每段写一句话总结（不看笔记写，写完再对照）。
5. **找错练习**：想象两个改动——(a) 把 get_chunks_by_file 里的 `records.sort(key=lambda r: r.chunk_index)` 删掉；(b) 把 list_chunks 的 include 加上 "embeddings"。分别写出后果（提示：一个破坏 AC，一个破坏类型防泄露；参照第 118 节练习 3 自查）。

### 9F. Phase 1 快速复习卡

**一句话**：VectorStore 用 11 个方法把"存储和检索"封装成一个接口，ChromaVectorStore 用 ChromaDB 把它实现——边界内完成所有翻译（对象→名字、distance→similarity、file_size→size），边界外只看统一语义。

**5 个关键词**：契约（ABC）、边界（_client 私有 + 11 public）、翻译（clamp/字段转换）、身份（UUID）、聚合（算出来的列表）。

**3 张图**：四层架构（0A）→ 分数链（0D）→ stub 8→0（0B）。

**3 个最易混**：

1. 方法存在 ≠ 功能可用（stub 会骗人）；
2. distance 越小越好，similarity 越大越好——方向相反，只差 clamp(1-x)；
3. 文件列表是"算出来的"不是"存出来的"（没有 FileRecord 表）。

**收官状态**：T0101–T0108 全 DONE，11/11 真实实现，0 占位；无业务调用方（正常，Phase 3+ 才出现）。

### 9G. Phase 2 将建立在什么基础上（只做高层连接，不提前教授实现）

- Phase 2（T0201–T0202）将产出 **384 维 embedding 向量** → `add_texts` 和 `search` 的向量参数将第一次有真实来源。Phase 1 里这两个参数一直标着"由调用方提供"——届时提供者就是 EmbeddingService。
- 模型将采用 **lazy singleton 加载**（不在服务启动时加载，首次使用时才加载并缓存）——这是 README 里 Phase 2 的学习主题，Python 的"单例"怎么写、模型如何缓存，Phase 2 再学。
- 连接点只有这两个，且都通过 Phase 1 已经写死的接口发生——**Phase 1 的代码一行都不用改**，这就是"先定契约、后接实现"的红利。

### 9H. 项目后续需要解决的架构问题（仅记录，不解决）

**KB rename 的 metadata 更新缺少 VectorStore public write path。**

- 背景：F001 的重命名级联有 8 步，其中"更新该 KB 所有 chunk metadata 里的 collection_name / source_file"归属 T0402（第 36 节的"刻意不做"表已标注）。
- 问题：VectorStore 的 11 个 public methods 里**没有"更新已有 chunk 的 metadata"的写路径**——只有 add_texts（全量写入）和 delete_by_file（删除）。T0402 将来要做这步时：要么用 11 个方法组合（list_chunks 全量读出 → 删除旧数据 → add_texts 重写 = 昂贵且非原子），要么需要为 VectorStore 增加新的 public 写方法。
- 两种选择都涉及接口或 SPEC 决策，超出 Phase 1 学习范围。**本文件只记录，不提出、不实现任何 SPEC 修改。**（第 36 节原有标注是"依赖 T0108 的 list_chunks"；此处将其升级记录为"项目后续需要解决的架构问题"。）

### 9I. 关于 Gate Review 与 Pending Questions 的说明

- **Gate Review**：仓库中未找到 Phase 1 Gate Review 的书面结论或 Findings（docs/ 下无 gate review 文档，TASKS.md 亦无记录）。本文档"Phase 1 完成"的依据 = TASKS.md 各 Task 的 DONE 状态 + 真实代码 + SPEC 对照。若 Gate Review 有正式结论，应回填到本节。
- **学习过程中积累的 Pending Questions（只记录，不修复）**：
  1. collection 存在性校验缺口（系统性）：11 个方法中只有 rename_collection 校验 collection 存在并抛 AppError("COLLECTION_NOT_FOUND")；其余 7 个方法（add_texts / search / delete_by_file / get_files / list_chunks / get_chunk_count / get_chunks_by_file）对不存在的 collection 直接抛 SDK 原始异常。
  2. 仓库无自动化测试：各 Verification 节均为"验证结构说明"，没有可执行的测试记录（不虚构 PASS 结果）。
  3. delete_by_file 返回 0 与 F016 的 404 映射留给 T0903（存储层保持中性）。
  4. get_files 的 status 取首条 chunk 的 ingestion_status，依赖 SPEC 7.4 的文件级一致性约束。

---

> **Phase 1 收官**：11 个方法全部真实实现（T0101–T0108），0 个占位。下一步学习 Phase 2 Embedding（T0201/T0202）——届时 `add_texts` 的 embeddings 参数将不再由"调用方提供"，而是 EmbeddingService 生成的 384 维向量。本文档已按 Phase 1 Learning Review 整理：Part 0 全景总览 → 第 1–119 节分 Task 实战 → Part 9 收尾整合。
