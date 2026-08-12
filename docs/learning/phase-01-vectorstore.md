# Phase 1 — VectorStore Foundation 学习笔记

> 这是一份随项目开发和个人理解逐步演进的学习文档。当前版本优先服务于"前端开发者进入 Python 后端"的第一阶段理解。
> **重要前提**：Phase 1 目前只完成了 T0101（VectorStore 接口定义）。本文只深入讲 T0101，T0102 及以后**尚未实现**，文中凡涉及它们的地方都会明确标记。

---

## 0. 阅读指南

### 第一遍只看（🟢）

先建立整体认知：VectorStore 是什么、T0101 只做了什么、为什么"定义了方法"不等于"数据库能用了"。

### 第二遍理解（🟡）

理解 DX-RAG 为什么需要抽象边界、11 个方法各自服务谁、T0101 和 Phase 0 / T0102 的关系。

### 以后再看（🔵）

依赖反转、Adapter 模式、ABC 底层机制等深层设计内容全部放在第 21 节，第一遍可以直接跳过。

### 本章阅读路线

| 章节 | 深度 | 说明 |
|------|------|------|
| 第 1 节 Phase 1 解决什么问题 | 🟢 必看 | 用 RAG 的完整数据流建立认知 |
| 第 2 节 前端视角理解 VectorStore | 🟢 必看 | 先用 TypeScript interface 思维建立类比 |
| 第 3 节 T0101 做了什么 | 🟢 必看 | **完成 vs 未完成**，防止误判进度 |
| 第 4 节 真实代码阅读 | 🟢 必看 | 4 段真实代码，逐行解释 Python 语法 |
| 第 5 节 ABC / abstractmethod | 🟢 必看 | T0101 唯一真正新的 Python 语法 |
| 第 6 节 Contract vs Implementation | 🟢 必看 | T0101 最重要的架构知识 |
| 第 7 节 为什么不直接调 ChromaDB | 🟡 建议理解 | 抽象边界的动机 |
| 第 8 节 Public Boundary 与 `_collection` | 🟡 建议理解 | 一条 SPEC 硬性约束 |
| 第 9 节 11 个方法学习地图 | 🟡 当速查表 | 以后可以回来查 |
| 第 10 节 Python ↔ TS 对照 | 🟡 当速查表 | 只列 T0101 新增内容 |
| 第 11–12 节 Phase 0 / T0102 关系 | 🟡 建议理解 | 你在学习地图上的位置 |
| 第 13–14 节 掌握清单 / 暂时不懂 | 🟢 必看 | 最低要求 + 心理减负 |
| 第 15 节 代码阅读路线 | 🟢 必看 | 不要一次读完全部代码 |
| 第 16–17 节 常见错误 / 架构图 | 🟡 建议理解 | 避开新手坑 |
| 第 18–20 节 自测 / 练习 / 复习卡 | 🟢 必看 | 检验学习效果 |
| 第 21 节 🔵 进阶阅读 | 🔵 以后再看 | 第一遍可以跳过 |

### 三种学习深度标记

| 标记 | 含义 |
|------|------|
| 🟢 **入门理解** | 第一遍必须理解。TypeScript 类比 + 简单解释 + 真实代码。|
| 🟡 **项目理解** | 解释 DX-RAG 为什么这样设计。帮你理解架构决策。|
| 🔵 **进阶阅读** | 可以以后回来看。不影响理解 T0101 的核心内容。|

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

| 保存什么 | 是什么 | 将来谁用 |
|---------|--------|---------|
| **chunk** | 文档切片的文本内容 | 检索命中后拼进 LLM 上下文 |
| **embedding** | chunk 的数字向量 | 查询时做"相似度"计算 |
| **metadata** | 这个 chunk 属于哪个文件、第几片等 | 按 file_id 删除、文件列表、文件预览 |

### 类比：一个前端开发者熟悉的东西

| RAG 概念 | 前端类比 |
|---------|---------|
| 上传文档 → 切成 chunk | 上传图片 → 切成多张缩略图 |
| chunk → embedding | 图片 → 用感知哈希算出的指纹 |
| 问题 → query vector | 新图片 → 算指纹 → 找最像的缩略图 |
| VectorStore | 你项目里的 `lib/storage.ts`——定义"存/取/查/删"的接口 |
| ChromaDB | `localStorage` / `IndexedDB`——真正干活的底层 |

### Phase 1 在整条链路上的位置

Phase 1（T0101–T0108）只做**最下面一层**：定义并实现"向量数据怎么存、怎么查"。切块、embedding 计算都是后面 Phase 的事。

```text
切块 (Phase 3) → 计算向量 (Phase 2) → 存储和检索 (Phase 1) → 检索融合 (Phase 6-7) → 生成回答 (Phase 8)
```

**当前进度**：Phase 1 只完成了 T0101 —— 只定义了"存储和检索"这一层的**接口契约**，还没有一行真正操作 ChromaDB 的代码。

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

| | VectorStore（T0101 产物） | ChromaDB |
|---|---|---|
| 是什么 | 抽象接口（契约） | 第三方向量数据库 SDK |
| 类比 | `interface Storage` | `localStorage` / `IndexedDB` |
| 能实例化吗 | ❌ 不能 | ✅ 能 |
| 有实际功能吗 | ❌ 只有方法签名 | ✅ 真正的存取逻辑 |

就像 `interface Storage` 不是 localStorage 本身一样，VectorStore 只是"描述"，不是"干活的人"。

### 谁以后会调用它？

未来业务层（都还没实现）：

| 未来调用方 | 预计 Phase | 会用到的方法（举例） |
|-----------|-----------|---------------------|
| IngestService（文档入库） | Phase 3 | `add_texts`, `delete_by_file` |
| KB 管理 API | Phase 4 | `create_collection`, `delete_collection`, `list_collections` |
| Keyword Retriever | Phase 6 | `list_chunks` |
| Vector Retriever | Phase 7 | `search` |
| QA Service | Phase 8 | `get_chunk_count`, `search` |
| File 管理 API | Phase 9 | `get_files`, `get_chunks_by_file`, `delete_by_file` |

### 谁以后会真正实现它？

**T0102–T0108** 会创建一个具体类（比如 `ChromaVectorStore`），继承 `VectorStore` 并逐个实现这 11 个方法，方法体里才是真正的 ChromaDB 操作。当前这个类**还不存在**。

```text
interface 定义者：T0101（✅ 已完成）   实现者：T0102–T0108（⬜ 未开始）
```

---

## 3. T0101 做了什么

### 🟢 T0101 已经完成的部分

真实产物只有一个文件：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)（226 行），包含：

| 产物 | 说明 |
|------|------|
| `ChunkRecord` | 数据模型：描述"一个 chunk 长什么样"（7 个字段） |
| `VectorSearchResult` | 数据模型：描述"一次检索命中的结果长什么样"（6 个字段，含 similarity_score） |
| `VectorStore(ABC)` | 抽象基类：11 个方法的签名声明，全部标记 `@abstractmethod` |

验证方式也只有一条：**这个文件能成功 import、能被其他模块用作类型标注**。仅此而已。

### 🟢 T0101 没有完成的部分

| 未完成 | 状态 |
|--------|------|
| ChromaDB client 初始化 | ⬜ 无任何 chromadb import |
| 创建 / 删除 / 列出 Collection | ⬜ 方法体只有 docstring |
| 写入 chunks / 向量 / metadata | ⬜ 同上 |
| 向量检索 | ⬜ 同上 |
| 任何一行可执行的 ChromaDB 操作 | ⬜ 0 行 |

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

| 侧 | 分数语义 |
|----|---------|
| ChromaDB 内部 | distance，**越小越相似**（如 0.15 表示非常像） |
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

| | Python ABC | TS interface | TS abstract class |
|---|---|---|---|
| 能实例化吗 | ❌ 不能 | ❌ 不能（类型而已） | ❌ 不能 |
| 强制子类实现 | ✅ 实例化时检查 | 编译时检查 | ✅ 编译时检查 |
| 有运行时存在吗 | ✅ 有（真实类） | ❌ 擦除 | ✅ 有 |

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

| | Contract（契约） | Implementation（实现） |
|---|---|---|
| 回答的问题 | "能做什么" | "具体怎么做" |
| T0101 里的对应物 | `VectorStore(ABC)` 的 11 个签名 | **不存在**（T0102–T0108 才写） |
| 类比 | 租房合同："可以住、可以做饭" | 房子本身：灶台、床、门锁 |
| 变化频率 | 稳定（SPEC FROZEN） | 会随 SDK 升级而改 |

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

| 好处 | 解释 | 前端类比 |
|------|------|---------|
| **维护** | ChromaDB SDK 升级改 API，只改一个实现类，不动业务代码 | 只改 `lib/storage.ts`，不动 20 个组件 |
| **测试** | 业务层可以 mock `VectorStore`，测试不需要真启动 ChromaDB | `jest.mock("./storage")` |
| **隔离第三方** | 业务代码不 import chromadb，第三方库的复杂 API 不扩散 | 业务组件不直接 import axios 细节 |
| **业务层稳定** | SPEC 冻结了 11 个方法签名，业务代码建立在稳定契约上 | 稳定的 Props 类型让组件可靠 |

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

| Method | 输入 | 输出 | 一句话作用 | 当前状态 |
| ------ | ---- | ---- | ---------- | -------- |
| `create_collection(name)` | `name: str` | `None` | 创建一个知识库（= 一个 ChromaDB Collection） | Contract only |
| `delete_collection(name)` | `name: str` | `None` | 删除知识库及其中全部数据 | Contract only |
| `rename_collection(old_name, new_name)` | 两个 `str` | `None` | 重命名知识库（只改 Collection 名字本身） | Contract only |
| `list_collections()` | 无 | `List[str]` | 列出所有知识库名称 | Contract only |
| `add_texts(collection, chunks, embeddings, metadatas)` | `str` + `List[str]` + `List[List[float]]` + `List[Dict[str, Any]]` | `List[str]`（chunk_ids） | 把文本 + 向量 + 元数据写进知识库 | Contract only |
| `search(collection, query_vector, top_k)` | `str` + `List[float]` + `int` | `List[VectorSearchResult]` | 向量相似度检索，返回 similarity_score | Contract only |
| `delete_by_file(collection, file_id)` | `str` + `str` | `int`（删除数量） | 按 file_id 删除一个文件的所有 chunks | Contract only |
| `get_files(collection)` | `str` | `List[Dict[str, Any]]` | 从 chunk metadata 聚合出文件列表 | Contract only |
| `list_chunks(collection)` | `str` | `List[ChunkRecord]` | 列出知识库全部 chunks（不含向量） | Contract only |
| `get_chunk_count(collection)` | `str` | `int` | 知识库里的 chunk 总数 | Contract only |
| `get_chunks_by_file(collection, file_id)` | `str` + `str` | `List[ChunkRecord]` | 某文件的所有 chunks，按 chunk_index 升序 | Contract only |

### 以后谁可能会调用它们（通俗版）

| 方法组 | 通俗场景 |
|--------|---------|
| 4 个 Collection 生命周期方法 | "新建一个知识库 / 删掉它 / 改名 / 看看有哪些知识库"（Phase 4 的 KB 管理界面） |
| `add_texts` | 上传文档入库的最后一步："把切好、算好向量的数据写进去"（Phase 3） |
| `search` | 用户提问时："找出最相似的几个片段"（Phase 7/8） |
| `delete_by_file` | 删除一个文件（Phase 9）；入库失败回滚时清理残留（Phase 3） |
| `get_files` | 知识库文件列表页面（Phase 9） |
| `list_chunks` | 关键词检索要遍历全部 chunk 建索引（Phase 6） |
| `get_chunk_count` | 判断知识库是否为空（Phase 8） |
| `get_chunks_by_file` | 文件预览："按顺序把这个文件的内容拼回来"（Phase 9） |

> 这里只点到为止。每个方法的真正实现细节（cosine、HNSW、metadata 写入等）属于 T0102–T0108，届时再学。

---

## 10. Python ↔ TypeScript 对照（只列 T0101 新增）

> Phase 0 已掌握的（`self`、`def`、`BaseModel`、`Field`、`List`/`Dict` 等）不重复展开。

| Python | TypeScript 类比 | 当前项目中的含义 |
| ------ | -------------- | ---------------- |
| `ABC` | `abstract class`（或 interface 思维） | `class VectorStore(ABC)` = 定义契约的基类 |
| `@abstractmethod` | `abstract` 方法修饰符 | "子类必须实现这个方法" |
| `from abc import ABC, abstractmethod` | `import { ... } from "abc"`（但 abc 是 Python 内置标准库，无需安装） | 引入抽象机制 |
| `class X(Parent):` | `class X extends Parent {}` | 继承（Phase 0 已见，这里继承 `ABC`） |
| `List[float]` | `number[]` | 384 维向量 = 384 个 float 的列表 |
| `List[List[float]]` | `number[][]` | 一批向量（`add_texts` 的 embeddings 参数） |
| `List[ChunkRecord]` | `ChunkRecord[]` | 返回自定义 Pydantic 模型列表 |
| `-> None` | `: void` | 操作型方法不返回值，失败靠抛异常 |
| `-> int` | `: number` | 返回删除数量 / chunk 总数 |
| 函数体只有 docstring | ❌ JS 注释不能当函数体 | 抽象方法没有可执行代码，docstring 兼作函数体 |
| docstring 中 `Args:` / `Returns:` | JSDoc `@param` / `@returns` | Google 风格文档格式（约定，非语法） |

---

## 11. T0101 和 Phase 0 的关系

```text
Phase 0 — Project / Config / Model Foundation（T0001–T0005）
          ↓ 提供地基
T0101 — VectorStore Contract（本次）
```

### Phase 0 基础中，T0101 真正用到的

| Phase 0 产物 | 在 T0101 中的真实使用 |
|-------------|---------------------|
| `backend/app/core/` 目录 + `__init__.py` | 新文件 `vector_store.py` 就放在这个 package 里，import 路径 `app.core.vector_store` |
| Pydantic `BaseModel` + `Field`（T0005） | `ChunkRecord` 和 `VectorSearchResult` 都继承 `BaseModel`，每个字段用 `Field(description=...)` |
| `typing` 类型标注习惯 | `List`、`Dict`、`Optional`、`Any` 贯穿整个文件 |
| 模块级 docstring 风格 | 文件头部 docstring 与 `main.py`、`schemas.py` 风格一致 |

### 没有直接使用的（不要硬关联）

| Phase 0 产物 | 情况 |
|-------------|------|
| `models/schemas.py` 的 16 个 API 模型 | T0101 定义的是**存储层内部**模型（`ChunkRecord` 等），与 API 层模型互相独立 |
| `core/config.py` 的 `settings` | T0101 纯声明签名，不需要任何配置；T0102 才会用到 `CHROMA_PERSIST_DIR` |
| `core/errors.py` 的 `AppError` | 没有方法体，也就没有抛错的地方；T0102+ 才可能抛出错误码 |
| `api/router.py` | T0101 不涉及 API 层 |

---

## 12. T0101 和 T0102 的关系

```text
T0101（✅ 已完成）            T0102（⬜ TODO）
定义 boundary / contract  →  基于这个 contract 继续实现
```

以 [TASKS.md](docs/TASKS.md) 中真实的 T0102 为准：

| 维度 | T0102 实际内容 |
|------|---------------|
| **做什么** | 创建 ChromaDB 实现类，实现 11 个方法中的 3 个：`create_collection`、`list_collections`、`delete_collection` |
| **依赖** | T0101（契约）+ T0003（config 的 `CHROMA_PERSIST_DIR`） |
| **关键配置** | ChromaDB PersistentClient + cosine 距离 + HNSW 索引 |
| **明确不做** | rename（→T0103）、add_texts（→T0104）、search（→T0105）等 |
| **验收** | 能真正创建/列出/删除 Collection；AC-F008-03（不暴露 `_collection`） |

也就是说，T0102 拿 T0101 的图纸开始盖第一层：**让"知识库"这个概念在磁盘上真实存在**。具体实现方案等 T0102 完成时再学，现在不需要提前准备。

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

| 暂时不懂的 | 为什么现在不用管 |
|-----------|-----------------|
| Dependency Inversion 深层理论 | 知道"业务层依赖抽象"这个结论就够用了 |
| Adapter Pattern 完整定义 | T0102+ 实现时自然会看到实例 |
| Python ABC 底层机制（metaclass、`__isabstractmethod__`） | 会用它，不需要知道它怎么造出来的 |
| ChromaDB internals（HNSW 索引、cosine 具体算法） | T0102 实现时对照 SPEC 学，现在学会忘 |
| 多数据库架构 / Milvus | v1 明确不做（SPEC out of scope），知道"预留了可能性"即可 |
| Python Protocol（TASKS 提到的 ABC 替代方案） | 项目选择了 ABC，Protocol 暂不出现 |
| 高级类型系统（TypeVar、Generic） | 当前代码没有用到 |

---

## 15. T0101 代码阅读路线

> 不要一次读完全部代码。按这个顺序，每个文件只看指定的部分。

### 第 1 个文件：[backend/app/core/vector_store.py](../../backend/app/core/vector_store.py)（226 行）

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

| 事项 | 状态 |
|------|------|
| T0101：定义 ABC + 2 个数据模型 + 11 个方法签名 | ✅ DONE |
| T0101：任何 ChromaDB 实际操作 | ⬜ 不在 T0101 范围内 |
| T0102–T0108：具体实现 | ⬜ TODO |
| 今天能用 VectorStore 存取数据吗 | ❌ 不能 |

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

> **下一步学习**：当 T0102 完成后，阅读具体实现类，对比 T0101 的接口定义——理解抽象如何落地为具体代码。
