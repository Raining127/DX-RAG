# Phase 2 — Embedding 学习笔记

> 这是一份随项目开发和个人理解逐步演进的学习文档。当前版本覆盖 **Phase 2 全部（T0201 + T0202）**，已按 Phase 2 Learning Review 整理：第 0 节全景速览 → 第 1–11 节 T0201（懒加载单例）→ 第 12–16 节 T0202（向量生成）→ 第 17–19 节收尾整合。
>
> 面向读者：前端开发者，熟悉 JavaScript / TypeScript / React，有少量 Node.js 经验，没有系统 Python 基础。

---

## 0. 阅读指南

### 这一章的目标是什么

读完 Phase 2 后，你需要做到：

- 理解"懒加载 + 单例"（lazy singleton）在 Python 里怎么写、为什么这样写
- 能用你已有的 JS/TS 知识（模块缓存、顶层 `let` 变量）类比理解这份 77 行的代码
- 知道 `EMBEDDING_MODEL_ERROR` 从 `raise` 到 HTTP 500 的完整链路
- 理解 `encode_chunks` 一行链式调用背后的数据形状转换（文本 → numpy → `List[List[float]]`）
- 理解 Phase 2 与 Phase 1 的接口关系：`add_texts` / `search` 的向量参数"由调用方提供"，提供者就是这里

### 本章阅读路线

| 章节 | 深度 | 说明 |
|------|------|------|
| 第 1 节 Phase 2 做什么 | 🟢 必看 | T0201/T0202 的分工与全局位置 |
| 第 2 节 用 JS/TS 类比理解 lazy singleton | 🟢 必看 | 先建立"这模式我见过"的直觉 |
| 第 3 节 逐行精读 embedding.py | 🟢 必看 | T0201 的 55 行，每行都有解释 |
| 第 4 节 错误契约完整链路 | 🟢 必看 | 从 raise 到 HTTP 500 的接力 |
| 第 5 节 与 Phase 1 的接口连接 | 🟡 建议理解 | 为什么 Phase 1 一行代码都不用改 |
| 第 6 节 SPEC F007 逐条对照 | 🟡 建议理解 | 学会"实现 vs SPEC"的对照读法 |
| 第 7 节 验证与 AC | 🟡 建议理解 | 没有自动化测试，验证靠什么 |
| 第 8 节 Python 新知识索引 | 🟢 按需 | 指向 python-for-frontend-dev.md 第 18 节 |
| 第 9 节 自测题与练习 | 🟢 必看 | 检验 T0201 掌握程度 |
| 第 10 节 快速复习卡 | 🟢 必看 | T0201 收官速记 |
| 第 11 节 进阶与 Pending Questions | 🔵 以后再看 | 并发首载、Hub 回退下载等 |
| 第 12–16 节 T0202 | 🟢 必看 | encode_chunks 逐行精读、numpy 新知识、契约兑现 |
| 第 17 节 Phase 2 总复习卡 | 🟢 必看 | 全 Phase 收官速记 |
| 第 18 节 T0202 自测题与练习 | 🟢 必看 | 检验 T0202 掌握程度 |
| 第 19 节 Pending Questions 与收官 | 🔵 以后再看 | Phase 2 收尾观察 |

### 三种学习深度标记

| 标记 | 含义 |
|------|------|
| 🟢 **入门理解** | 第一遍必须掌握的内容。用 TypeScript 类比 + 简单解释。|
| 🟡 **项目理解** | 解释 DX-RAG 为什么这样设计。帮你理解架构决策。|
| 🔵 **进阶阅读** | 可以以后回来看。不影响理解 Phase 2 的核心内容。|

### 当前进度（2026-08-20）

- **T0201**: ✅ DONE — [embedding.py](../../backend/app/services/embedding.py)（第 1–55 行，Lazy Singleton）
- **T0202**: ✅ DONE — 同一文件第 58–77 行（`encode_chunks`）

### 全景速览（Learning Review 新增）

Phase 2 的全部成果 = 一个 77 行文件里的 **2 个函数**。这也是 Phase 2 的完整对外接口：

```text
embedding.py（77 行）—— Phase 2 对外接口 = 2 个函数
┌─────────────────────────────────────────────────────────┐
│ get_model()          T0201 · 装机器                      │
│   _model 缓存 → 懒加载一次 → 永远返回同一实例              │
│   失败 → AppError("EMBEDDING_MODEL_ERROR") → HTTP 500   │
└────────────────────────┬────────────────────────────────┘
                         │ 内部调用（get_model 的唯一调用方）
┌────────────────────────▼────────────────────────────────┐
│ encode_chunks()      T0202 · 开机器                      │
│   List[str] → 空检查 → .encode(normalize) → .tolist()    │
│   → List[List[float]]（384 维，L2 归一化）               │
└─────────────────────────────────────────────────────────┘
```

**数据边界链（5 站）**：`文本 str 列表 → numpy (n, 384) → Python list[list[float]] → add_texts 的 embeddings / search 的 query_vector`——numpy 在第 2→3 站被 `.tolist()` 翻译掉，绝不跨出模块边界（第 14 节）。

**资产接力**：T0201 留下 `_model` + `get_model()`，T0202 是它们的唯一消费方（第 12 节）；Phase 1 留下的两个"空参数"由此获得来源（第 15 节）。

---

## 1. Phase 2 到底做了什么

### 从 Phase 1 留下的一个"空参数"说起

Phase 1 的 `VectorStore` 里有两个方法的参数一直"悬空"：

```python
# vector_store.py — Phase 1 的契约（第 129–134 行）
def add_texts(self, collection, chunks, embeddings, metadatas) -> List[str]:
    """... embeddings: Corresponding embedding vectors (384-dim)."""

# vector_store.py — Phase 1 的契约（第 149–153 行）
def search(self, collection, query_vector, top_k) -> List[VectorSearchResult]:
    """... query_vector: Query embedding vector (384-dim)."""
```

`embeddings` 和 `query_vector` 都是 384 维浮点向量，但 Phase 1 结束时**没有任何代码能生产它们**——docstring 一律写"由调用方提供"（第 56 节：add_texts 是搬运工）。

**Phase 2 就是"向量生产车间"**：把文本变成 384 维向量，让 Phase 1 的这两个参数第一次有真实来源。

### 车间只有两个工序：先装机器，再生产

Phase 2 只有两个 Task，分工极其清晰：

| Task | 干什么 | 类比 | 状态 |
|------|--------|------|------|
| T0201 | 加载 embedding 模型，缓存为单例 | **装机器**（把机床安装好、通电） | ✅ DONE |
| T0202 | `encode_chunks(chunks)` 生成向量 | **开机器生产**（投料 → 产出 384 维向量） | ✅ DONE |

> 更新：上段"T0201 完成时（也就是现在）……还没有人开它"记录的是 T0201 刚完成时的状态。T0202 已完成后，**机器的第一个操作者是 `encode_chunks`**——`get_model()` 有了调用方（[embedding.py:77](../../backend/app/services/embedding.py#L77)）。但 `encode_chunks` 本身仍无调用方（正常——Phase 3 的 ingest 管道才是第一个消费者，见第 15 节）。

### 机器参数：bge-small-zh-v1.5

SPEC F007 指定的模型：

| 项目 | 值 |
|------|-----|
| 模型 | `bge-small-zh-v1.5`（BAAI 的中文语义 embedding 模型） |
| 本地路径 | `models/bge-small-zh-v1.5/`（相对 backend 运行目录） |
| 维度 | 384（每段文本 → 384 个 float） |
| 归一化 | L2 normalize（`normalize_embeddings=True`） |
| 运行时 | [sentence-transformers](https://www.sbert.net/) ≥ 2.2.2（requirements.txt 已声明，Phase 0 就加好了） |

> **模型目录不在仓库里**。`backend/` 下只有 `app/`、`chroma_db/`、`requirements.txt`，没有 `models/`。模型文件（约 90+ MB）需要单独放到 `backend/models/bge-small-zh-v1.5/` 才能真实运行。这正是"懒加载"策略的前提之一——如果启动时就必须加载模型，模型缺失会直接导致服务起不来。

### 为什么"装机器"要单独成一个 Task

装模型和用模型是两个完全不同的技术问题：

- **T0201 的技术问题**：什么时候加载？加载几次？加载失败怎么办？（生命周期管理）
- **T0202 的技术问题**：怎么调用 encode？空列表怎么办？返回什么形状？（数据转换）

把它们拆开，每个 Task 的验证也独立：T0201 验证"第二次调用是同一个实例"（AC-F007-02），T0202 验证"3 个 chunks → 3 个 384 维向量"（AC-F007-01）。

---

## 2. 用 JS/TS 类比理解 Lazy Singleton

> 🟢 入门理解。这一节不涉及 Python 语法，先建立直觉。

### 这个模式你在 JS 里写过一百遍

T0201 的整个模式，用 TypeScript 写出来是这个样子：

```typescript
// modelCache.ts —— T0201 的 TS 版本
let model: SentenceTransformerModel | null = null;

export function getModel(): SentenceTransformerModel {
  if (model === null) {
    model = loadSentenceTransformer("models/bge-small-zh-v1.5");
  }
  return model;
}
```

一模一样的四件事：

1. **模块级变量当缓存**：`let model = null` ↔ Python 的 `_model: Optional[...] = None`
2. **首次调用才加载**：`if (model === null)` 里才真正加载
3. **之后直接返回缓存**：第二次调用跳过加载，直接 `return model`
4. **进程内共享**：模块只执行一次，变量只存一份

### 一个关键差异：JS 模块"天生单例"，Python 需要显式声明

**Node.js / ESM 的世界里，模块本身就是单例**：`require()` 的结果被缓存，同一个模块无论被 import 多少次，只执行一次，导出的对象天然只有一份。

**Python 的模块也是单例**（`import` 同样只执行一次模块代码，`sys.modules` 缓存），但有一个差异点值得注意：

- JS 里 `export let model = null` 导出的是**同一个绑定**，别的文件 `import { model }` 拿到的就是那一份；
- Python 里**没有"导出"概念**——模块里写的 `_model = None` 就是模块属性，任何地方 `from app.services.embedding import get_model` 时，模块只初始化一次，`_model` 自然只有一份。

所以 Python 版和 TS 版真正的区别不是"要不要缓存"，而是 **Python 需要在函数里显式写 `global _model` 才能给模块级变量重新赋值**（这是 Python 语法细节，见第 3 节片段 3 和 python 手册 18.3）——JS 里 `model = ...` 直接就能赋值，不需要任何声明。

### 为什么"懒加载"（不启动时加载）

SPEC F007 明确要求：**首次使用时加载，非服务启动时加载**。从运维角度看有两条理由：

| 理由 | 说明 | 前端类比 |
|------|------|---------|
| 启动速度 | 模型加载要数秒（解压/初始化权重），启动时不加载 → `uvicorn` 秒起 | 首屏不做重计算，click 时才做 |
| 故障隔离 | 模型文件缺失/损坏时，**服务仍然能启动**，只有用到 embedding 的请求才报错 | 可选依赖（如图表库）CDN 挂了不影响首页 |

`main.py` 的 lifespan 里没有任何模型初始化代码（`# Startup: nothing to initialize at this stage`）——这就是 SPEC 决策落地的证据。

> 🔵 顺带一提：JS 生态里的对应物是 `import()` 动态导入 + 模块级缓存（如 Next.js 的 `dynamic(() => import(...))`、Webpack 的懒加载 chunk）。Python 里也有类似的"动态导入"语法，T0201 恰好用到了——见第 3 节片段 3 的"函数内 import"。

---

## 3. 逐行精读 embedding.py 的 T0201 部分（第 1–55 行）

> 🟢 入门理解。打开 [embedding.py](../../backend/app/services/embedding.py) 对照阅读。T0201 的 55 行分 4 个片段：docstring 契约、imports、模块级缓存变量、get_model 函数。T0202 追加的第 58–77 行（encode_chunks）见第 13 节。

### 片段 0：先看全景

```
embedding.py（T0201 交付时为 55 行；T0202 完成后共 77 行）
├── 第 1–15 行  docstring —— SPEC F007 的浓缩契约（加载策略 + 错误契约 + 越界声明）
├── 第 17–23 行  imports —— 只有 3 个 import，注意第 22–23 行的 TYPE_CHECKING 特殊写法
├── 第 27–28 行  模块级缓存变量 —— 整个单例模式的地基，就 1 行
├── 第 31–55 行  get_model() —— T0201 唯一的 public 函数，全部逻辑所在
└── 第 58–77 行  encode_chunks() —— T0202 追加（见第 12–14 节）
```

### 片段 1：docstring（第 1–16 行）—— 文件头就是契约

```python
"""Embedding — bge-small-zh-v1.5 lazy singleton + chunk encoding (SPEC F007).

SPEC F007 Model Loading Strategy:
  - Lazy load on FIRST use (never at application startup)
  - Cache the loaded model as a process-level singleton
  - Subsequent calls reuse the cached instance — never reload per request

SPEC F007 Embedding Generation:
  - encode_chunks(chunks) → model.encode(chunks, normalize_embeddings=True).tolist()
  - Empty chunks → empty list (not an error)

Error contract (SPEC F007):
  - Model path missing, corrupt files, OOM, or ANY load failure on first
    use → AppError("EMBEDDING_MODEL_ERROR") → HTTP 500
    (catalog entry: app.core.errors)
"""
```

**读法**：和 Phase 1 的 `vector_store.py` 一样，DX-RAG 的文件 docstring 不是寒暄，而是**SPEC 要求的浓缩版**——三件事：加载策略（3 条）、生成契约（2 条）、错误契约（1 条）。这对应 CLAUDE.md 的 Scope Discipline：每个文件明确写出"我做什么、我不做什么"。

> 历史对照：T0201 交付时，docstring 里写的是 "Out of scope here (→ T0202): encode / encode_chunks / ..." 的越界声明；T0202 完成后，该段被替换为 "Embedding Generation" 契约段。**越界声明不是永久内容——Task 完成时它要让位给真正的契约。**

### 片段 2：imports（第 17–23 行）—— 第一次见到 TYPE_CHECKING

```python
from typing import TYPE_CHECKING, Optional

from app.core.config import settings
from app.core.errors import AppError

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer
```

三个普通 import 很好懂：`settings`（读 `EMBED_MODEL` 路径）、`AppError`（错误契约）、`Optional`（类型标注）。

**但 `sentence_transformers` 的 import 为什么包在 `if TYPE_CHECKING:` 里？**

- `TYPE_CHECKING` 是一个**永远为 False 的常量**（Python 官方提供，专用于类型标注场景）。
- `if TYPE_CHECKING:` 里的 import **运行时不会执行**——只在 IDE / mypy 做类型检查时"假装执行"，让类型检查器知道 `SentenceTransformer` 这个类型存在。
- 下面第 28 行 `_model: Optional["SentenceTransformer"]` 用**字符串**写类型名，也是同理：运行时根本不解析这个字符串，所以不需要真的 import 这个类。

**为什么要绕这一圈？** 因为 `sentence_transformers` 是个**重依赖**（import 它会连带加载 torch 等一大堆库，可能要几秒钟）。如果文件顶部直接 `from sentence_transformers import SentenceTransformer`：

1. 任何代码 `import embedding` 模块 → 连带加载 torch → 慢；
2. 环境里没装这个包 → `import embedding` 直接崩溃（哪怕根本不调用 get_model）。

用 `TYPE_CHECKING` + 字符串标注，**import 这个模块永远是轻量、无副作用的**——真正的 import 推迟到 get_model() 第一次被调用（片段 3）。

> TS 类比：`import type { SentenceTransformer } from "sentence-transformers"` —— TS 的 `import type` 在编译后完全消失，和 `TYPE_CHECKING` 的作用一模一样。前端开发者应该一秒就懂。

### 片段 3：模块级缓存变量（第 27–28 行）—— 单例的地基

```python
# Module-level singleton cache — None until the first successful load.
_model: Optional["SentenceTransformer"] = None
```

就一行，但它是整个模式的**核心数据结构**：

| 要素 | 说明 | TS 类比 |
|------|------|---------|
| 变量名 `_model` | 单下划线前缀 = 模块私有约定（Phase 1 学过，python 手册 17.3） | 不导出，只在本模块用 |
| 类型 `Optional["SentenceTransformer"]` | 要么是模型实例，要么是 `None`（还没加载） | `SentenceTransformerModel \| null` |
| 初始值 `None` | 程序启动时**不加载**，缓存为空 | `let model = null` |
| 位置：模块顶层 | import 时只执行这一行赋值，不触发任何加载 | 模块顶层 `let` |

**为什么类型标注写在变量名后面**（`_model: Optional[...]` 而不是函数参数那种写法）：这是 Python 3.6+ 的**变量标注（variable annotation）**语法，Phase 1 已经接触过（python 手册 17.10）——它只是给 IDE/类型检查器看的，运行时同样不执行。

### 片段 4：get_model()（第 31–55 行）—— 全部逻辑

```python
def get_model() -> "SentenceTransformer":
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(settings.EMBED_MODEL)
        except Exception as exc:
            raise AppError("EMBEDDING_MODEL_ERROR") from exc
    return _model
```

逐行拆解（共 4 个知识点，3 个是 T0201 新出现的）：

**① `global _model`（第 2 行）—— Python 的赋值作用域规则**

Python 规则：**函数里给变量赋值，默认创建的是"局部变量"**，除非声明 `global`。所以：

- 没有 `global _model`：函数里 `_model = ...` 会创建一个同名局部变量，模块级的 `_model` 永远不被更新——**每次调用都重新加载模型**，单例失效（而且局部变量函数结束就丢弃）。
- 有 `global _model`：赋值直接作用于模块级那个变量。

这是 Python 和 JS 的重要差异：JS 里函数内赋值会自动沿作用域链找到外层变量（只要不 `let`/`const` 遮蔽），**Python 必须显式声明**。详细版见 python 手册 18.3。

> 🔵 冷知识：`return _model`（读）不需要 `global` 声明——只有**赋值**才需要。Python 的规则是"读自动外找，写默认局部"。

**② `if _model is None:`（第 3 行）—— 单例开关**

- `is None` 用**身份比较**而不是 `== None`——判断"是不是同一个 None 对象"。对 None 比较，Python 官方推荐 `is`（T0201 首次出现，详细见 python 手册 18.5）。
- 只有缓存为空（从未成功加载过）才进入加载分支；加载成功后 `_model` 非 None，后续调用直接跳过整个 if。
- **注意**：判断条件是"未加载"而不是"加载失败"。加载失败会直接 raise（见 ④），`_model` 保持 None——**下一次调用会重试加载**。这是合理的：临时性故障（如磁盘抖动）不该让服务永久失去 embedding 能力。

**③ 函数内 import（第 5 行）—— 延迟 import**

`from sentence_transformers import SentenceTransformer` 写在函数体里，而不是文件顶部。Python 的 import 可以出现在任何位置，且 import 的模块会被 `sys.modules` 全局缓存——**重复 import 不重复加载**，第二次调用 get_model 时这行几乎零开销。

为什么要这样（和片段 2 的 TYPE_CHECKING 是同一策略的两个层次）：

| 层次 | 手段 | 效果 |
|------|------|------|
| import 本模块时 | `TYPE_CHECKING` + 字符串标注 | 不 import sentence_transformers |
| 第一次调 get_model 时 | 函数内 import | 此刻才真正 import（慢，但只发生一次） |

TS 类比：`const { SentenceTransformer } = await import("sentence-transformers")` —— 动态 import，把加载推迟到真正需要的时候。

**④ `try / except Exception as exc` + `raise AppError(...) from exc`（第 6–9 行）—— 错误翻译 + 异常链**

- `except Exception`：捕获**一切**异常（Python 里 `Exception` 是所有常规异常的父类，接近 JS 的 `catch (e)` 不加类型过滤）。
- 为什么捕获一切：SPEC F007 的错误表里列了"模型路径不存在、模型文件损坏、OOM 或**任何加载失败**"——实现层无法枚举底层库可能抛的所有异常，干脆全收。
- `raise AppError("EMBEDDING_MODEL_ERROR") from exc`：把"底层库的任意异常"**翻译成**项目自己的错误码。`from exc` 叫**异常链（exception chaining）**：新异常会保留原始异常作为 `__cause__`，traceback 里两个都看得到——排查时既知道"对外报什么码"，也知道"根因是什么"。TS 类比：`throw new AppError("EMBEDDING_MODEL_ERROR", { cause: e })`（ES2022 的 `cause` 选项，几乎同一语义）。
- 没有 `from exc` 会怎样：traceback 会显示"在处理异常时又发生异常"（`During handling of the above exception...`），链依然在但可读性差。显式 `from` 是 Python 规范写法。详细版见 python 手册 18.4。

**最后 `return _model`（第 10 行）**：无论走没走加载分支，出口只有一个——返回缓存的模型实例。这是"单例"的兑现点：所有调用方拿到的是**同一个对象**。

### 片段 5：T0201 的越界检查 —— 这 55 行里"没有"什么

按 T0201 的 Out of Scope 逐条核对：

| Out of Scope 条目 | 代码证据 |
|------------------|---------|
| 不在启动时加载 | `main.py` lifespan 是空的；模型加载只在 get_model() 内部 |
| 不在启动时校验模型存在 | 全文没有启动路径上的存在性检查代码 |
| 不支持多模型 / GPU 配置 | 全文只有一个 `SentenceTransformer(settings.EMBED_MODEL)` 构造，无任何配置分支 |

（以及 T0202 的 encode 完全没出现——当时的 docstring 已声明越界；T0202 完成后的实现见第 12–14 节。）

---

## 4. 错误契约完整链路：从 raise 到 HTTP 500

> 🟡 项目理解。Phase 0 学过错误机制（phase-00 第 8 节），这里第一次看到**服务层**用它。

T0201 只 raise 一次，但"模型加载失败 → 客户端收到 500"是一段四人接力：

```
① embedding.py:54   raise AppError("EMBEDDING_MODEL_ERROR") from exc
        │  ② 查目录表：errors.py:72
        ▼
"EMBEDDING_MODEL_ERROR": (500, "嵌入模型加载或编码失败")
        │  → http_status = 500，message 取中文默认值
        ▼
③ FastAPI 全局异常处理器：main.py:43–51
   @app.exception_handler(AppError)
        │  → JSONResponse(status_code=500, content={error: {code, message, details}})
        ▼
④ 客户端收到 HTTP 500：
   {"error": {"code": "EMBEDDING_MODEL_ERROR",
              "message": "嵌入模型加载或编码失败",
              "details": {}}}
```

**值得注意的三个点：**

1. **错误码是字符串常量，不是异常类**。Phase 1 的 `rename_collection` 用过同一个机制（`AppError("COLLECTION_NOT_FOUND")`），T0201 是第二个使用方。新增错误只需在 catalog 加一行 dict 条目 + 在需要处 `raise AppError(...)`，不用新建异常类——这是 Phase 0（T0004）设计的红利。
2. **details 为空**：底层原始异常信息**没有**放进响应（`details={}`）——对外不泄露内部细节（比如文件系统路径、torch 内部报错）。原始异常只存在于服务端 traceback（经由 `from exc` 保留）。这是 SPEC 9.4 的"统一错误格式、不泄露细节"要求的体现。
3. **注意 404 与 500 的区别**：模型缺失不是"请求方的问题"（那会是 4xx），而是"服务配置/环境问题"（5xx）——SPEC 错误表把 EMBEDDING_MODEL_ERROR 定为 500，语义是"服务器侧出错，客户端换写法没用"。

---

## 5. 与 Phase 1 的接口连接

> 🟡 项目理解。Phase 1 学习文档 9G 预告过这条连接线，这里兑现。

Phase 1 里 `add_texts` / `search` 的向量参数写的是"由调用方提供"。T0201 完成后，这条供应线的**第一段**接上了：

```text
文本 chunks ──(T0202 encode_chunks)──▶ 384 维向量 ──(Phase 3 ingest)──▶ add_texts(embeddings=...)
用户问题   ──(T0202 encode_chunks)──▶ query_vector  ──(Phase 7/8 检索)─▶ search(query_vector=...)
                    ▲
                    │ 两台机器共用一台：get_model() 返回的同一个单例
```

- T0201 提供 `get_model()`——**机器本体**；
- T0202 已提供 `encode_chunks()`——**操作机器的函数**（`get_model().encode(chunks, normalize_embeddings=True).tolist()`，SPEC F007 已写明调用式；实现精读见第 12–14 节）；
- Phase 1 的 `VectorStore` **一行都不用改**——它在 Phase 1 写死契约时，参数形状（`List[List[float]]`，384 维）就与 F007 对齐了。这就是"先定契约、后接实现"的红利，和 9G 说的一模一样。

**Phase 1 学习过的"搬运工"原则在这里对称出现**：add_texts 不管向量怎么来（只负责搬），get_model 不管向量怎么用（只负责提供机器）。每层只管自己边界内的事。

---

## 6. SPEC F007 逐条对照

> 🟡 项目理解。学会"实现 vs SPEC"的对照读法——这是 DX-RAG 学习流程的核心方法。

### Define 表对照

| SPEC F007 Define | 实现对照 |
|------------------|---------|
| 输入 chunks / 输出 384 维向量 | **T0202 的范围**，T0201 不涉及（docstring 已声明越界）✓ |
| 包含：模型懒加载 | `get_model()` 首次调用才构造模型 ✓ |
| 包含：单例缓存 | `_model` 模块级变量 + `if _model is None` ✓ |
| 包含：L2 归一化 | 在 T0202 的 encode 参数里（`normalize_embeddings=True`），T0201 只是"机器支持" ✓ |
| 不包含：多模型、GPU、动态切换 | 55 行里无任何相关分支 ✓ |

### 加载策略 3 条对照

| SPEC 要求 | 实现位置 |
|-----------|---------|
| 首次使用时懒加载（非服务启动时） | 加载只发生在 get_model() 内；main.py lifespan 无初始化 ✓ |
| 加载后缓存为进程级 Singleton | `_model` 模块级变量；进程内所有调用方共享 ✓ |
| 禁止每次请求重新加载 | `if _model is None` 保证只有第一次进入加载分支 ✓ |

### 错误场景 2 条对照

| SPEC 场景 | 实现对照 |
|-----------|---------|
| 模型路径不存在 / 文件损坏 / OOM / 任何加载失败 → 500 EMBEDDING_MODEL_ERROR | `except Exception` → `raise AppError("EMBEDDING_MODEL_ERROR") from exc`；catalog 定 500 ✓ |
| chunks 为空列表 → 空列表（非错误） | **T0202 的范围**，T0201 不涉及 ✓ |

### AC 对照（诚实版）

- **AC-F007-02（模型缓存）**：`get_model()` 的 `if _model is None` 结构上保证第二次调用复用同一实例——**代码审查可确认**，但仓库中没有可执行的自动化测试（见第 7 节）。
- **AC-F007-01（3 chunks → 3 个 384 维向量）**：属于 T0202，本 Task 不验证。

### 一处"实现比 SPEC 更细"的观察

SPEC 只要求"失败返回 500"，实现进一步用 `from exc` 保留了根因（异常链），且失败后 `_model` 保持 None、下次调用可重试。这些是实现的合理工程选择，不违反 SPEC。

---

## 7. 验证与 AC：没有自动化测试，怎么确认 DONE

> 🟡 项目理解。和 Phase 1 的 9I 一致：仓库中**没有可执行的自动化测试**，TASKS.md 的 Verification 条目是"验证结构说明"而非测试记录。这里如实说明验证方法，不虚构 PASS 结果。

T0201 的验证条目（TASKS.md）：

| 验证条目 | 如何手工验证 | 依赖 |
|----------|------------|------|
| 第一次 get_model() 调用加载模型（耗时长） | 在 backend 目录下运行 `python -c "from app.services.embedding import get_model; get_model()"`，观察首调用耗时数秒 | 需要本地有模型目录 |
| 第二次调用立即返回同一实例 | 同一进程内再调一次；或用 `get_model() is get_model()`（应返回 True） | 同上 |
| 模型目录缺失 → 首次 encode 时抛错 | 不放置模型目录，调用 get_model() → 应抛出 AppError，`code == "EMBEDDING_MODEL_ERROR"`，`http_status == 500` | 无需模型目录（故意缺失即可） |

**第三条可以在没有模型的环境里验证**——它验证的正是"失败路径"。前两条需要先放置真实的 bge-small-zh-v1.5 模型目录（不在仓库中，需单独准备）。

---

## 8. Python 新知识索引

T0201 给前端开发者带来了 4 个真正新的 Python 概念，已整理进 [python-for-frontend-dev.md](./python-for-frontend-dev.md) 第 18 节：

| 概念 | 一句话 | 手册位置 | TS 类比 |
|------|--------|---------|---------|
| `TYPE_CHECKING` + 字符串类型标注 | 只在类型检查时"假装 import"，运行时零成本 | 18.1 | `import type` |
| 函数内 import（延迟 import） | import 写在函数体里，首次调用才执行 | 18.2 | `await import()` |
| `global` 关键字 | 函数内给模块级变量赋值必须显式声明 | 18.3 | JS 不需要（赋值自动外找） |
| `raise ... from exc`（异常链） | 翻译异常的同时保留根因 | 18.4 | `{ cause: e }` |

其余用到的语法（`Optional`、单下划线私有、docstring、`is None`、类型标注）Phase 0/1 已学过，不重复。

---

## 9. 自测题与练习

### 自测题（不给答案；答不出回对应小节找）

1. T0201 与 T0202 的分工一句话是什么？为什么"装机器"要单独成一个 Task？
2. 用 TS 伪代码写出 get_model 的等价实现（不看书）。
3. `if TYPE_CHECKING:` 里的 import 运行时会不会执行？为什么 embedding.py 要这样写？直接顶部 import 会有什么后果？
4. 如果删掉 `global _model` 这行，代码运行时会怎样？哪个现象说明单例失效了？
5. `if _model is None` 里的 `is` 能不能换成 `==`？为什么？
6. 函数内 import 每次调用都会重新加载模型吗？Python 的什么机制保证不会？
7. 模型加载失败后，下一次调用 get_model 会发生什么？为什么这个行为是合理的？
8. 从 `raise AppError("EMBEDDING_MODEL_ERROR")` 到客户端拿到响应，中间经过哪几步？`details` 为什么是空 dict？
9. 为什么模型缺失报 500 而不是 404？两者语义区别是什么？
10. Phase 1 的哪两个方法参数会因为 Phase 2 获得真实来源？它们的契约形状为什么不用改？

### 小练习（不修改正式代码）

1. **默写 TS 版本**：合上笔记，用 TypeScript 写一个 lazy singleton 的 `getModel()`，再对照第 2 节。
2. **手画错误接力图**：画出第 4 节的四步接力（① raise → ② catalog → ③ handler → ④ JSON），标出每一步所在文件和行号。
3. **在 scratch 里验证单例**：随便找个临时 .py 文件，写一个"加载 0.5 秒后打印一次"的假加载函数，套用 get_model 的模式（global + if None + 缓存），连续调用 3 次，验证只打印一次。做完删除临时文件。
4. **对照读 SPEC**：打开 SPEC.md 的 F007 一节，按第 6 节的三张对照表逐条在 embedding.py 里找出对应行。
5. **边界检查练习**：假装你要在 embedding.py 里加"启动时校验模型是否存在"的代码——先写出你的版本，再对照 T0201 的 Out of Scope，说出为什么这个改动违反 SPEC（即使它"更友好"）。

---

## 10. T0201 快速复习卡

**一句话**：T0201 用 55 行实现了"懒加载单例"——首次调用时加载 bge-small-zh-v1.5 模型并缓存到模块级变量，之后所有调用返回同一个实例；加载失败翻译为 `EMBEDDING_MODEL_ERROR`（HTTP 500）。

**4 个关键词**：懒加载（首次用才加载）、单例（模块级 `_model`）、错误翻译（`from exc` 保留根因）、越界（encode 是 T0202 的事）。

**1 张图**：

```text
import embedding 模块 ──▶ 轻量，无模型加载（TYPE_CHECKING 保证）
        │
第一次 get_model() ──▶ import sentence_transformers（慢，一次）
        │                └─ SentenceTransformer(settings.EMBED_MODEL)（更慢，一次）
        │                     ├─ 成功 → _model = 实例
        │                     └─ 失败 → raise AppError("EMBEDDING_MODEL_ERROR") from exc
        │                                    （_model 保持 None，下次可重试）
        ▼
之后 get_model() ──▶ 直接 return _model（快，永远不重载）
```

**3 个最易混**：

1. `global` 是**赋值**规则不是读取规则——删掉它不会报错，只会让单例静默失效（每次重新加载）；
2. `TYPE_CHECKING` 是**永远 False** 的常量——它不"延迟 import 到第一次调用"，它让 import **永不发生**；延迟到第一次调用的是函数内的那个 import，两者配合但机制不同；
3. 懒加载 ≠ 重试禁止——加载失败后 `_model` 仍是 None，下次调用会**重试**加载（临时故障可自愈）。

**当前状态**：T0201 DONE；`get_model()` 尚无调用方（正常——T0202 的 `encode_chunks` 是第一个）。

---

## 11. 进阶与 Pending Questions

> 🔵 进阶阅读 + 本阶段学习过程中发现的待确认点（只记录，不修复）。

### 🔵 并发首次加载：简单 lazy singleton 不是线程安全的

FastAPI 的同步 endpoint 在线程池中运行。如果两个请求**同时**首次触发 `get_model()`，两者都可能看到 `_model is None` 并同时加载——浪费一次加载（结果仍是同一个缓存，正确性不受影响）。标准的 Python 双检锁（threading.Lock + 两次检查）可以消除这种浪费。

**SPEC 没有要求加锁**（F007 只要求懒加载 + 单例 + 失败报错），当前实现满足 SPEC。此条仅作为"lazy singleton 在并发下的经典话题"记录，v1 不处理。

### 🔵 模型路径缺失时的 Hub 回退

`sentence_transformers` 对传入的字符串会先当作本地路径；若路径不存在，会把字符串当作 HuggingFace Hub 的模型名**尝试联网下载**（如 `models/bge-small-zh-v1.5` 不是合法 repo id，通常会快速失败；无网络时也会失败）。无论哪种失败，都落入 `except Exception` → `EMBEDDING_MODEL_ERROR`——实现层无需区分"路径错了"还是"下载失败"，SPEC 只要求"失败 → 500"。

### Pending Questions（只记录，不修复）

1. **仓库无自动化测试**：AC-F007-02（模型缓存）仅靠代码结构确认，无可执行测试（与 Phase 1 的 9I-2 一致，不虚构 PASS）。
2. **模型目录不在仓库**：`backend/models/bge-small-zh-v1.5/` 需单独准备（未在 .gitignore 显式声明 `models/`，如需忽略本地模型目录建议后续确认）。
3. **首载失败的重试语义**：SPEC 未明确"失败后下次调用是否重试"——实现选择了重试（`_model` 保持 None）。这是合理默认，但严格说属于实现选择而非 SPEC 规定。

---

## 12. T0202 做了什么：开机器投产

> 🟢 入门理解。T0202 是 Phase 2 的第二个、也是最后一个 Task。

回顾第 1 节的分工表：T0201 **装机器**（加载模型、缓存单例），T0202 **开机器**（调用模型、生产向量）。T0202 的实现也在 `embedding.py`（TASKS.md 预期"same file as T0201"）——文件从 55 行长到 77 行。

**实现范围（TASKS.md）四件事：**

| 要求 | 一句话 |
|------|--------|
| `encode_chunks(chunks: List[str]) -> List[List[float]]` | 输入文本列表，输出 384 维向量列表 |
| 调用 `get_model().encode(chunks, normalize_embeddings=True)` | 复用 T0201 的单例 |
| 返回 Python list 形状的 384 维向量 | 靠 `.tolist()` 转换（见第 14 节） |
| 空列表 → 空列表（非错误） | `if not chunks: return []` |

**Out of Scope 检查**（T0202 明确不做的三件事，逐条对照代码）：不加 batch 大小限制（一次全量交给模型）、不加 GPU 配置、不加进度回调——77 行里都没有，越界干净。

**一个值得注意的现象**：T0202 是**一个函数**的 Task。20 行代码（含 docstring）撑起一个 Task 不奇怪——验证它的 AC（形状、归一化、空列表）每一项都对应 SPEC 的硬契约。Task 的大小不由代码行数决定，由契约复杂度决定。

---

## 13. 逐行精读 encode_chunks（第 58–77 行）

> 🟢 入门理解。打开 [embedding.py:58-77](../../backend/app/services/embedding.py#L58-L77) 对照阅读。

```python
def encode_chunks(chunks: List[str]) -> List[List[float]]:
    """Convert text chunks to 384-dim L2-normalized vectors (SPEC F007).

    Uses the singleton model from ``get_model()``; the model itself
    performs L2 normalization (``normalize_embeddings=True``) and the
    result is converted to plain Python float lists via ``.tolist()``.

    Args:
        chunks: List of chunk text strings.

    Returns:
        One 384-dim vector per chunk as List[List[float]].  Empty input
        returns an empty list — not an error (SPEC F007 error table).

    Raises:
        AppError: EMBEDDING_MODEL_ERROR (500) if the model fails to load.
    """
    if not chunks:
        return []
    return get_model().encode(chunks, normalize_embeddings=True).tolist()
```

逐段拆解（真正的新知识点只有 3 个）：

**① docstring（第 59–74 行）—— 又是浓缩契约**

- 第一段说明数据形状："384 维、L2 归一化、经 `.tolist()` 转成**纯 Python float**"——"plain Python float"这个措辞是关键（为什么强调，见第 14 节）。
- Returns 段直接引用 SPEC 的错误表："Empty input returns an empty list — not an error"。
- Raises 段只列 EMBEDDING_MODEL_ERROR——**encode 本身没有新错误**，它可能抛的错都来自 get_model（模型加载）。这说明错误契约的继承关系：T0202 没有给错误目录增加任何条目。

**② `if not chunks:`（第 75 行）—— 真值判断**

Python 的 `not` 把对象转成布尔：**空容器（空 list / dict / str）都是假值**。所以 `if not chunks:` 就是"如果列表为空"。

- **TS 类比有个坑**：JS 里 `if (!chunks)` 对空数组**永远不进分支**——因为 JS 的 `[]` 是 **truthy**！正确写法是 `if (!chunks.length)`。这是 Python 和 JS 最经典的真值差异之一（详细见 python 手册 19.1）。
- 🔵 顺带观察：如果调用方传 `None`，`not None` 也是 True → 也返回 `[]`。SPEC 只规定了空列表，实现顺带兼容了 None——宽松于 SPEC 的良性行为（记入第 19 节 Pending Questions）。
- 为什么"空列表返回空列表"而不是抛错：这是**数据管道哲学**——上游可能产出 0 个 chunk（如空文件被解析出 0 段），对下游来说"0 进 0 出"是正常数据流，不是异常。抛错会逼迫每个上游调用方自己判断空列表。

**③ `return get_model().encode(...).tolist()`（第 77 行）—— 一行链式调用**

三个点连成一条链，每个点返回一个值，下一个点接着调——这行是 T0202 的全部生产逻辑。三层拆解见第 14 节。

**越界检查**：T0202 的代码里没有"批量上限"、没有"GPU 开关"、没有"进度回调"——与 Out of Scope 一致。也没有任何打印/日志——项目 v1 无结构化日志（CLAUDE.md 明确排除）。

---

## 14. 一行链式调用的三层拆解 + numpy 新知识

> 🟢 入门理解（numpy 部分 🟡）。`get_model().encode(chunks, normalize_embeddings=True).tolist()` 逐层拆开：

```python
get_model()                                    # ① SentenceTransformer 实例（T0201 的单例）
    .encode(chunks, normalize_embeddings=True) # ② numpy.ndarray，形状 (n, 384)
    .tolist()                                  # ③ Python 原生 list[list[float]]
```

**第 1 层 `get_model()`**：第 5 节说过——返回 T0201 缓存的单例。encode_chunks 不关心模型是否已加载、怎么加载，那是 T0201 的边界。

**第 2 层 `.encode(chunks, normalize_embeddings=True)`**：模型推理。返回的是 **numpy 数组（ndarray）**，形状 `(n, 384)`——n 个 chunk，每个 384 维。

- **normalize_embeddings=True 的位置值得注意**：它在这里（编码时）传入，而不是 T0201 构造模型时传入（`SentenceTransformer(settings.EMBED_MODEL)` 没带任何参数）。说明 L2 归一化是 **encode 的选项**，不是模型固有属性——"装机器"时不绑定，"生产"时按需开启。SPEC F007 的调用式就是这么写的，实现逐字对齐。
- **L2 归一化做了什么**：把每个向量缩放到长度为 1（各维平方和开根号 = 1）。效果是让所有向量处在同一个"单位球面"上，cosine 相似度计算更稳定——Phase 1 的 `search` 用 cosine 距离（建库时写死的 `hnsw:space=cosine`），归一化让 cosine 距离和 dot product 等价。
- **numpy 是什么**：Python 数据科学的基础库——多维数组 + 数值计算。类比：JS 里的 `Float32Array` / TensorFlow.js 的张量（不完美，但方向对）。sentence-transformers 的 encode 默认返回 numpy 数组（详细见 python 手册 19.2）。

**第 3 层 `.tolist()`**：把 numpy 数组转成 Python 原生 list。**为什么这步必不可少：**

| 理由 | 说明 |
|------|------|
| 契约形状 | `VectorStore.add_texts` 的 `embeddings: List[List[float]]` 要的是 Python `float`；numpy 数组里的元素是 `numpy.float32`——**不是同一个类型** |
| 序列化 | ChromaDB 持久化、JSON 序列化都要求普通 float；numpy 标量是 C 对象包装，序列化会炸 |
| 边界哲学 | 和 Phase 1 的 distance → similarity 一样：**类型翻译在模块边界内完成**，numpy 类型不泄漏到 embedding 模块之外 |

TS 类比：`Array.from(f32Array)` 或 `[...f32Array]` 把 `Float32Array` 转成 `number[]`——下游 API 只要 `number[]`，类型系统替你挡，Python 没有这个保护，靠纪律 + 文档契约。

**形状核对（AC-F007-01 的形状部分）**：输入 3 个 chunk → encode 返回 `(3, 384)` 的 ndarray → tolist 后是 3 个长度为 384 的 list。`List[List[float]]` 的外层长度 = chunk 数，内层长度 = 384。

---

## 15. 契约兑现：从文本到 VectorStore 的完整数据流

> 🟡 项目理解。Phase 2 完成后，Phase 1 留下的两个"空参数"正式有了来源。

```text
                    ┌──────────────── Phase 2 的边界 ────────────────┐
文本 chunks          │  encode_chunks(chunks)                        │   List[List[float]]
（Phase 3 解析切分产出）│   └─ get_model().encode(..., normalize=True) │  （384 维，L2 归一化）
                    │        .tolist()                                │
                    └───────────────────┬────────────────────────────┘
                                        │
           ┌────────────────────────────┴───────────────────────────┐
           ▼                                                          ▼
  入库方向：add_texts(embeddings=...)                    查询方向：search(query_vector=...)
  （Phase 3 ingest 管道调用）                            （Phase 7/8 检索调用）
```

**三个值得理解的架构点：**

1. **一台机器服务两个方向**：入库（chunks → 向量 → ChromaDB）和查询（问题 → 向量 → 相似度检索）共用同一个模型单例。这不是省钱，是**数学必需**：入库向量和查询向量必须来自同一个语义空间（同一个模型、同一套权重），否则"相似度"毫无意义。换一个模型向量空间就变了，旧数据全部作废。
2. **三层等待链**：Phase 1 的方法等 Phase 2 的向量（已兑现）；Phase 2 的函数等 Phase 3 的文本（`encode_chunks` 今天没有任何调用方）。每层完成时都"悬空"，是契约优先开发的常态——**方法存在 ≠ 功能可用**（Phase 1 的 0G 认知，再次应验）。
3. **Phase 1 一行没改**：`VectorStore` 契约在 Phase 1 就写死了 `List[List[float]]` 形状，Phase 2 只是"向契约里填数据"——第 5 节讲过的"先定契约、后接实现"在这里兑现。

---

## 16. SPEC F007 对照 + AC + 验证（诚实版）

> 🟡 项目理解。延续第 6 节的对照读法。

### Embedding 生成契约对照

| SPEC F007 | 实现位置 | 结果 |
|-----------|---------|------|
| `model.encode(chunks, normalize_embeddings=True).tolist()` | [embedding.py:77](../../backend/app/services/embedding.py#L77) | 逐字对应 ✓ |
| chunks 为空列表 → 返回空列表（非错误） | 第 75–76 行 `if not chunks` | ✓ |
| 每个向量 384 维 | 由 bge-small-zh-v1.5 模型保证（代码不硬编码 384） | ✓ |
| L2 normalize | `normalize_embeddings=True`（第 77 行） | ✓ |
| 错误：任何加载失败 → 500 EMBEDDING_MODEL_ERROR | 继承自 get_model（第 73 行 docstring 声明） | ✓ |

### AC 对照（诚实版）

- **AC-F007-01（3 chunks → 3 个 384 维向量，L2 norm ≈ 1.0）**：形状（n → (n, 384) → n×384 嵌套 list）与归一化参数传递可**代码审查确认**；"norm ≈ 1.0"的数值验证需要真实模型目录 + 可执行环境——仓库中无自动化测试、无模型目录，**不虚构 PASS**（与第 7 节、第 11 节一致的立场）。
- **AC-F007-02（模型缓存）**：encode_chunks 每次调用都走 `get_model()`，复用同一实例——结构确认 ✓。
- **空列表 → 空列表**：无需模型即可验证（`encode_chunks([])` 在第 75 行直接返回，不触模型）——这条 AC 的验证成本最低，因为实现把空检查放在了"碰模型之前"。

### 验证条目（TASKS.md）与手工验证方法

| 条目 | 手工验证 | 依赖 |
|------|---------|------|
| 3 chunks → 3 个 384 维向量 | `python -c "from app.services.embedding import encode_chunks; vs = encode_chunks(['你好','世界','测试']); print(len(vs), [len(v) for v in vs])"` | 需模型目录 |
| L2 norm ≈ 1.0 | 对结果向量算平方和开根号 | 需模型目录 + 手工计算 |
| 空列表 → 空列表 | `encode_chunks([]) == []` | **无需模型** |
| 模型单例复用 | 连续两次 encode 观察第二次速度 / `get_model() is get_model()` | 需模型目录 |

---

## 17. Phase 2 总复习卡（全 Phase）

**一句话**：77 行 = 装机器（懒加载单例 get_model）+ 开机器（一行链式编码 encode_chunks）——文本列表进来，`List[List[float]]`（384 维、L2 归一化）出去，错误统一为 `EMBEDDING_MODEL_ERROR`（HTTP 500）。

**5 个关键词**：懒加载、单例、真值判断（`if not chunks`）、链式调用（`.encode().tolist()`）、契约兑现。

**2 张图**：第 15 节的数据流图（文本 → Phase 2 → add_texts/search）+ 第 10 节的 get_model 图（懒加载 + 失败重试）。

**3 个最易混（Phase 2 版）**：

1. `if (!chunks)` 在 JS 里对空数组是错的（`[]` 是 truthy）——Python 空容器是假值，JS 不是；
2. `normalize_embeddings=True` 是 **encode 的参数**，不是模型构造参数——归一化是"生产选项"不是"机器属性"；
3. `.tolist()` 不是可省略的装饰——numpy `float32` ≠ Python `float`，跨契约边界必须转换（类型翻译在边界内）。

**收官状态**：T0201 + T0202 全 DONE，77 行，越界干净。`encode_chunks` 无调用方（正常，Phase 3 才出现）。

### 17A. Phase 2 只需要真正掌握的 8 件事

1. 懒加载单例四要素：模块级 `_model` 缓存 + `global` 声明赋值 + `if _model is None` 开关 + 函数内 import。（第 2/3 节）
2. `TYPE_CHECKING` + 字符串标注让 `import embedding` 零成本；重依赖只在 `get_model` 首次调用时加载，且永不重复加载。（第 3 节片段 2）
3. 加载失败 → `AppError("EMBEDDING_MODEL_ERROR")` → HTTP 500；失败后 `_model` 保持 None，**下次调用会重试**。（第 4 节）
4. `if not chunks` 判空发生在触碰模型**之前**；"空进空出"是数据管道哲学，不是错误。（第 13 节）
5. 一行链式调用三层：单例 → numpy `(n, 384)` → `.tolist()` 转 Python float。（第 14 节）
6. numpy float32 ≠ Python float——类型翻译在模块边界内完成，与 Phase 1 的 distance→similarity 同一哲学。（第 14 节）
7. `normalize_embeddings=True` 是 encode 的参数（生产选项），不是模型构造参数；归一化让 cosine 检索更稳。（第 14 节）
8. 一台机器服务两个方向（入库 + 查询），同一语义空间是数学必需；Phase 1 契约一行没改。（第 15 节）

### 17B. 现在可以暂时不懂的内容（Phase 2 级汇总）

| 内容 | 为什么可以暂时不懂 | 什么时候需要 |
|------|------------------|-------------|
| numpy 广播 / 矩阵运算原理 | 返回值处理只需 `.tolist()` 一层 | 做自定义数值计算时 |
| torch / sentence-transformers 内部机制 | SPEC 定死模型与调用式，实现照抄即可 | 换模型 / 调优时 |
| L2 归一化与 cosine 的数学推导 | 只需知道"归一化让 cosine 更稳" | 检索质量调优时 |
| 双检锁（并发首载） | SPEC 未要求；v1 不处理并发首载竞争 | 做高并发优化时 |
| HuggingFace Hub 下载机制 | 任何下载失败都归入 EMBEDDING_MODEL_ERROR | 部署模型管理时 |

### 17C. 完整代码阅读路线（一次读完 77 行）

打开 [embedding.py](../../backend/app/services/embedding.py)（77 行），按顺序读：

1. 第 1–16 行 文件 docstring —— 三块契约（加载策略 3 条 / 生成契约 2 条 / 错误契约 1 条）。读完能背出调用式 `model.encode(chunks, normalize_embeddings=True).tolist()` 就算过。
2. 第 18–24 行 imports —— `List` 是 T0202 加的；`if TYPE_CHECKING:` 里的 import 永远不执行。
3. 第 27–28 行 `_model` 缓存变量 —— 单例地基，就一行赋值。
4. 第 31–55 行 get_model —— 三处新语法：`global`（赋值需声明）、函数内 import（延迟加载）、`raise ... from exc`（异常链）。
5. 第 58–77 行 encode_chunks —— 真值判断空检查 + 一行链式调用。

读完能回答 4 个问题：① 全文有几个函数？各自的输入输出契约是什么？② 全文有几个 `raise`？（1 个——encode_chunks 自己没有新错误，它继承 get_model 的。）③ numpy 类型在哪一行之后不存在了？（`.tolist()` 之后。）④ 哪个 import 是 T0202 新增的？（`List`。）

---

## 18. T0202 自测题与练习

### 自测题（不给答案；答不出回第 12–16 节找）

1. `encode_chunks` 的输入输出契约是什么？空列表输入返回什么？为什么"返回空列表"比"抛错"更好？
2. `if not chunks:` 在 Python 里等价于 JS 的什么写法？为什么直接照搬成 `if (!chunks)` 在 JS 里是错的？
3. `get_model().encode(...)` 返回什么类型？`.tolist()` 做了什么？为什么不能把 encode 的返回值直接交给 `add_texts`？
4. `normalize_embeddings=True` 是在"装机器"（T0201）时配置还是"生产"（T0202）时配置？L2 归一化与 Phase 1 的 cosine 距离是什么关系？
5. `encode_chunks` 需要关心模型是否已加载吗？模型加载失败时它的行为是什么？错误码是什么？
6. 为什么入库和查询必须用同一个模型？换一个模型会有什么后果？
7. AC-F007-01 的 "L2 norm ≈ 1.0" 由代码里哪一行保证？为什么仓库里没有它的自动化测试？
8. 今天谁调用 `encode_chunks`？第一个调用方预计在哪个 Phase 出现？"方法存在 ≠ 功能可用"在这里如何体现？
9. 把 `None` 传给 `encode_chunks` 会发生什么？为什么？（提示：`not None` 也是 True）
10. 77 行的文件里，哪几行属于 T0201 的资产、哪几行属于 T0202？docstring 的哪一段在 T0202 后被替换了？

### 小练习（不修改正式代码）

1. **默画数据流图**：合上笔记，画出第 15 节的完整数据流（文本 → 三步转换 → 两个消费方向），标出每一步的**类型**。
2. **TS 版 encode_chunks**：用 TypeScript 伪代码写等价实现（含空检查）——特别注意 JS 的空数组检查怎么写才正确。
3. **形状推算**：假设 5 个 chunk，写出 encode 返回的 numpy 形状、`.tolist()` 后的 Python 结构（画出嵌套层级）。
4. **对照读 F007**：打开 SPEC.md 的 F007 "Embedding 生成"代码块，与 embedding.py 第 77 行逐字符对照。
5. **边界思考**：`chunks = [""]`（含一个空字符串的列表）会走 `if not chunks` 分支吗？接下来会发生什么？想想"谁应该保证不产出空 chunk"（提示：Phase 3 的切分管道）。

### 跨 Task 整合自测（Learning Review 新增；不给答案）

1. 用一句话把 77 行讲完——要求同时覆盖两个函数的契约与它们的关系。
2. 如果未来换一个不支持 numpy 的向量存储，77 行里哪一行保护了它？为什么这一行的位置（模块边界内）和 Phase 1 的哪一行是同一个哲学？
3. 从"用户上传一个文件"到"chunk 向量落库"，Phase 2 参与哪一步？今天这条路走得通吗？断点在哪一层？
4. T0201 的 docstring 在 T0202 完成后被改动了什么？这个改动反映的是哪条纪律（提示：第 3 节片段 1 的"历史对照"）？
5. 删掉整个 embedding.py，Phase 1 的 `add_texts` / `search` 会立刻报错吗？为什么不会？这说明了"契约"与"实现"的什么关系？

---

## 19. Pending Questions 与收官

> 本阶段学习过程中发现的待确认点（只记录，不修复）。T0201 的 4 条见第 11 节，以下是 T0202 新增的：

1. **仓库无自动化测试**（延续 11-1）：AC-F007-01 的数值验证（L2 norm ≈ 1.0）无法在无模型目录的环境中执行；本文件只做代码结构确认，不虚构 PASS。
2. **`None` 入参返回 `[]`**：实现顺带兼容（`not None` → True），SPEC F007 只规定了"空列表 → 空列表"。宽松处理是良性的，但严格说属于实现选择而非 SPEC 规定。
3. **空字符串 chunk 会被编码**：`[""]` 是非空列表，`if not chunks` 不拦截——空字符串会被当作普通文本交给模型（可能得到全零/异常向量）。SPEC 未定义此边界；"不产出空 chunk"的责任落在 Phase 3 的文本清洗/切分管道。
4. **归一化位置**：归一化在 encode 层开启（而非模型构造时），与 SPEC 调用式一致——但值得记住："归一化"是编码选项，模型对象本身不绑定。

### Gate Review 说明

仓库中未找到 Phase 2 Gate Review 的书面结论或 Findings（TASKS.md 中唯一的 Gate Review 记录属于 Phase 0）。本文档"Phase 2 完成"的依据 = TASKS.md T0201/T0202 的 DONE 状态 + 真实代码 + SPEC 对照。若 Gate Review 有正式结论，应回填本节。

### Phase 3 将建立在什么基础上（只做高层连接，不提前教授实现）

- Phase 3（T0301–T0308）将产出**文本 chunks**（多格式解析 + 清洗 + 切分）——`encode_chunks` 的第一个调用方；ingest 管道把 解析→清洗→切分→编码→写入 编排起来。
- `add_texts` 的 `embeddings` 参数将第一次被真实填充——Phase 1 的"搬运工"收到真货。
- 检索链（Phase 6–8）的 query 文本同样走 `encode_chunks` → `search` 的 `query_vector`——同一台机器第二次出场。
- 三个连接点都通过已写死的接口发生，**Phase 2 的代码无需任何改动**。

---

> **Phase 2 收官**：T0201 + T0202 全部完成（embedding.py 共 77 行，越界干净，错误链路完整）。机器（`get_model` 懒加载单例）与生产函数（`encode_chunks`）就位，向量契约（`List[List[float]]`，384 维，L2 归一化）兑现。`encode_chunks` 尚无调用方——Phase 3（T0301–T0308）的 ingest 管道将是第一个消费者：届时文本 chunks 由解析/切分产出，向量经 `add_texts` 写入 ChromaDB，检索链（Phase 6–8）随之接通。本文档已按 Phase 2 Learning Review 整理：第 0 节全景速览 → 第 1–11 节 T0201 → 第 12–16 节 T0202 → 第 17–19 节收尾整合。下一步学习 Phase 3 Document Processing Pipeline。
