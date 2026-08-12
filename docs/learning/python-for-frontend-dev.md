# Python for Frontend Developers — DX-RAG 学习手册

> 这不是一本完整的 Python 教程。它只记录截至目前 DX-RAG 项目真实出现过的 Python 知识，帮助你利用已有的 TypeScript / Node.js 经验逐步看懂 Python 后端代码。

---

## 1. 如何使用这份文档

### 这是什么

这是一份**随项目生长**的 Python 速查手册。每当 DX-RAG 完成一个 Coding Task，如果涉及你还不熟悉的 Python 语法或概念，就会在这里新增对应条目。

### 这不是什么

- ❌ 不是 Python 语言教程（不会讲 `for` 循环、`if` 语句、`lambda` 等基础语法）
- ❌ 不是"Python 所有特性"的百科
- ❌ 不会提前教授当前项目还没出现的 Python 特性

### 怎么用

1. **遇到看不懂的代码** → 来这里查"Python 生词表"（第 15 节）或对应章节
2. **开始看一个新文件前** → 先看"当前项目 Python 阅读路线"（第 13 节）
3. **想复习** → 看"快速对照表"（第 2 节）和"最容易混淆的概念"（第 12 节）
4. **想知道学了多少** → 看"学习进度"（第 16 节）

### 约定

- 中文为主，技术术语保留英文
- 每次类比 TypeScript / Node.js 都会注明"不完全等价"
- 🟢 = 必须看懂，🟡 = 知道存在就行，🔵 = 暂时不用学

---

## 2. Python ↔ TypeScript 快速对照

> 只收录当前 DX-RAG 代码（Phase 0 + T0101）真实出现过的语法。

### 类型

| Python | TypeScript 类比 | 重要差异 | DX-RAG 出现位置 |
|--------|----------------|---------|---------------|
| `str` | `string` | | `schemas.py`: `name: str`、`config.py`: `APP_NAME: str` |
| `int` | `number` | Python 区分 `int`(整数) 和 `float`(小数)，TS 只有 `number` | `config.py`: `MAX_UPLOAD_SIZE_MB: int = 50` |
| `float` | `number` | TS 的 `number` 覆盖了 `int` + `float` | `config.py`: `LLM_TEMPERATURE: float = 0.2` |
| `bool` | `boolean` | Python 字面量是 `True` / `False`（大写开头） | |
| `List[str]` | `string[]` | 需要 `from typing import List` | `config.py`: `CORS_ORIGINS: List[str]`、`vector_store.py`: `-> List[str]` |
| `List[dict]` | `Array<Record<string,any>>` | | `vector_store.py`: `-> List[Dict[str, Any]]` |
| `Dict[str, Any]` | `Record<string, any>` | 需要 `from typing import Dict` | `errors.py`: `details: Dict[str, Any]`、`vector_store.py`: `metadata: Dict[str, Any]` |
| `Optional[str]` | `string \| null \| undefined` | Python 没有 `undefined`。`Optional[X]` = `X \| None` | `config.py`: `DEEPSEEK_API_KEY: Optional[SecretStr]` |
| `Literal["a", "b"]` | `"a" \| "b"` (union of literals) | 需要 `from typing import Literal` | `schemas.py`: `role: Literal["user", "assistant"]`、`status: Literal["SUCCESS", "SUCCESS_WITH_WARNINGS"]` |
| `Any` | `any` | 和 TS 的 `any` 类似——"我不限制这个类型" | `vector_store.py`: `metadata: Dict[str, Any]` |
| `None` | 根据语境：作为值时 ≈ `null`；作为返回类型 ≈ `void` | Python 没有 `undefined` 也没有 `void` 关键字。函数无返回值时写 `-> None` | `config.py`: `-> Optional[str]` (可能返回 `None`) |

### 函数和方法

| Python | TypeScript 类比 | 重要差异 | DX-RAG 出现位置 |
|--------|----------------|---------|---------------|
| `def func_name():` | `function funcName() { }` | Python 用缩进表示函数体，不用 `{}` | 到处可见 |
| `def method(self, x):` | 类的方法（`this` 隐式传入） | Python 必须**显式写 `self`** 作为第一个参数 | `errors.py`: `def __init__(self, code, ...)`、`config.py`: `def get_deepseek_key(self)` |
| `-> ReturnType` | 返回值类型标注 `: ReturnType` | Python 写在参数列表之后，用 `->` | `vector_store.py`: `-> None`、`-> List[str]`、`-> int` |
| `-> None` | `: void` | Python 没有 `void` 关键字 | `vector_store.py`: `def create_collection(self, name: str) -> None` |
| `return value` | `return value` | | `config.py`: `return self.DEEPSEEK_API_KEY.get_secret_value()` |

### 类

| Python | TypeScript 类比 | 重要差异 | DX-RAG 出现位置 |
|--------|----------------|---------|---------------|
| `class Name:` | `class Name { }` | 用缩进替代 `{}` | `errors.py`: `class AppError(Exception)`、`config.py`: `class Settings(BaseSettings)` |
| `class Child(Parent):` | `class Child extends Parent { }` | Python 用括号，TS 用 `extends` | `errors.py`: `class AppError(Exception)`、`schemas.py`: `class ChatMessage(BaseModel)` |
| `self` | `this` | Python 必须**显式写**在方法参数列表里，且方法内访问属性也必须写 `self.xxx` | `config.py`: `self.DEEPSEEK_API_KEY`、`errors.py`: `self.code = code` |
| `__init__(self, ...)` | `constructor(...)` | Python 对象在 `__new__` 时已创建，`__init__` 只做初始化。但先当成 constructor 理解就行 | `errors.py`: `AppError.__init__` |

### 模块和导入

| Python | TypeScript 类比 | 重要差异 | DX-RAG 出现位置 |
|--------|----------------|---------|---------------|
| `import logging` | `import * as logging from "logging"` | 导入整个模块，使用时需加前缀 `logging.getLogger(...)` | `main.py:1` |
| `from fastapi import FastAPI` | `import { FastAPI } from "fastapi"` | Python 路径用 `.` 分隔 | `main.py:5` |
| `from app.core.config import settings` | `import { settings } from "./app/core/config"` | 无 `./` 前缀，无文件扩展名 | `main.py:9` |
| `from typing import List, Optional` | `import type { List, Optional } from ...` 没有直接等价 | Python 类型标注需要的泛型需要显式 import | `config.py:4`、`schemas.py:8` |

### 其他

| Python | TypeScript 类比 | 重要差异 | DX-RAG 出现位置 |
|--------|----------------|---------|---------------|
| `@decorator` | NestJS 的 `@Decorator()`（不完全等价） | 先理解成"给函数/类加框架标签"。Python decorator 本质是函数调用 | `main.py`: `@app.exception_handler(AppError)`、`@asynccontextmanager`、`config.py`: `@field_validator(...)`、`@classmethod` |
| `async def` / `await` | `async function` / `await` | 概念基本相同 | `main.py`: `async def lifespan(...)`、`async def app_error_handler(...)` |
| `pass` | 空函数体 `{ }` (无内容的 `{}`) | Python 用缩进表示代码块，空代码块必须有 `pass` 占位 | Phase 0 代码中函数体只有 docstring 时不需要 `pass` |
| `...`（ellipsis） | `// TODO` 或空实现 | 在 ABC 的 `@abstractmethod` 中表示"子类来填" | `vector_store.py`: 所有 `@abstractmethod` 的方法体都是 `...` |
| `"string"` vs `'string'` | 单引号和双引号都可以 | Python 中 `"` 和 `'` 完全等价，不像 JS 有 prettier 偏好 | `config.py`: 大部分用 `"` |
| `"""docstring"""` | `/** JSDoc */` 或 `/* 多行注释 */` | Python 用三引号写多行文档字符串，放在函数/类定义后第一行 | `vector_store.py:1-18`、`schemas.py:1-6` |

---

## 3. Python 文件、Module 和 Package

### 结合 DX-RAG 真实目录理解

```
backend/app/
├── __init__.py          ← 标记 app/ 是 package
├── main.py              ← 一个 module
├── api/
│   ├── __init__.py      ← 标记 api/ 是 sub-package
│   └── router.py        ← app.api.router module
├── core/
│   ├── __init__.py
│   ├── config.py        ← app.core.config module
│   └── errors.py        ← app.core.errors module
├── models/
│   ├── __init__.py
│   └── schemas.py       ← app.models.schemas module
└── services/
    └── __init__.py
```

### 三个层级

| 层级 | Python 术语 | 真实例子 | TypeScript 类比 |
|------|-----------|---------|----------------|
| 文件 | **Module** | `config.py` | 一个 `.ts` 文件 |
| 含 `__init__.py` 的目录 | **Package** | `app/core/` | 一个含 `index.ts` 的目录 |
| 包嵌套 | **Sub-package** | `app.core` | 嵌套的目录模块 |

### `__init__.py` 是干什么的

**真实代码**：DX-RAG 中所有 `__init__.py` 都是**空文件**。

```python
# backend/app/core/__init__.py
# (这个文件是空的)
```

**作用**：告诉 Python "这个目录是一个 package，可以被 import"。如果没有它，`from app.core import config` 会报 `ModuleNotFoundError`。

**TypeScript 类比**：并不完全等价，但可以先理解成：`__init__.py` 的存在本身 ≈ 一个空的 `index.ts` 文件标识了目录是一个模块入口。区别是 TS 的 `index.ts` 如果不导出任何东西就没意义，但 Python 的空 `__init__.py` 即使什么都不做，它的存在本身就完成了"标记 package"的职责。

### import 路径怎么读

```python
# 真实代码：main.py 第 9 行
from app.api.router import api_router
```

**阅读方式**：
1. `app.api.router` → 去 `app/api/router.py` 这个文件
2. `import api_router` → 拿出那个文件里名为 `api_router` 的东西

```python
# 真实代码：main.py 第 5 行
from fastapi import FastAPI, Request
```

**阅读方式**：
1. `fastapi` → 系统安装的 `fastapi` 包
2. `import FastAPI, Request` → 从包里拿出这两个类

**TypeScript 类比**：

```ts
// from app.api.router import api_router ≈
import { apiRouter } from "./app/api/router";

// from fastapi import FastAPI, Request ≈
import { FastAPI, Request } from "fastapi";
```

**关键差异**：
- Python 路径用 `.` 分隔，不是 `/`
- Python 不加文件扩展名 `.py`
- Python 没有 `./` 相对路径前缀（默认搜索 `sys.path` 中的路径）

### 当前项目需要知道的 import 规则

在 DX-RAG 中运行 `uvicorn app.main:app`，必须在 `backend/` 目录下执行。因为 Python 从**当前工作目录**开始搜索 `app` package。

```bash
cd backend
uvicorn app.main:app    # ✅ 能找到 app/
```

```bash
cd ~/dx-rag             # 从项目根目录
uvicorn app.main:app    # ❌ 找不到 app/（除非设置了 PYTHONPATH）
```

---

## 4. 函数

### `def` — 定义函数

**真实代码**：[config.py:107-109](backend/app/core/config.py#L107-L109)

```python
def get_settings() -> Settings:
    """Return the module-level Settings singleton."""
    return settings
```

**怎么读**：
- `def` → "我要定义一个函数"（define function）
- `get_settings` → 函数名
- `()` → 参数列表（这个函数没有参数）
- `-> Settings` → 这个函数返回一个 `Settings` 类型的对象
- `:` 后面的缩进块 → 函数体

**TypeScript 类比**：

```ts
function getSettings(): Settings {
    return settings;
}
```

### 参数和 type hints

**真实代码**：[errors.py:101-107](backend/app/core/errors.py#L101-L107)

```python
def __init__(
    self,
    code: str,
    *,
    details: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
) -> None:
```

**怎么读**：
- `self` → 第一个参数永远是实例自身（≈ `this`）
- `code: str` → 参数 `code` 的类型是 `str`
- `*` → 特殊语法：`*` 之后的所有参数必须用**关键字传参**（`AppError("CODE", details={...})` 可以，`AppError("CODE", {...})` 不行）
- `details: Optional[Dict[str, Any]] = None` → 参数 `details` 可以是 `Dict[str, Any]` 或 `None`，默认值是 `None`
- `-> None` → 构造函数不返回值（≈ `: void`）

**TypeScript 类比**：

```ts
constructor(
    code: string,
    opts?: { details?: Record<string, any>; message?: string }
) { ... }
```

Python 的 `*` 没有直接的 TS 语法对应。它强制调用方在 `*` 后面的参数用名字传参。

### `-> None` — 无返回值

**真实代码**：[vector_store.py:89-91](backend/app/core/vector_store.py#L89-L91)

```python
@abstractmethod
def create_collection(self, name: str) -> None:
    """Create a new ChromaDB collection."""
    ...
```

**怎么读**：这个函数执行一个操作（创建 collection），不返回任何有意义的值。

**TypeScript 类比**：

```ts
abstract createCollection(name: string): void;
```

### 在当前项目中的作用

DX-RAG 中的函数主要分三类：

1. **API endpoint handler**（目前还没）— 接收 HTTP 请求，返回 JSON 响应
2. **Service 方法**（目前还没）— 执行业务逻辑
3. **工具函数** — 如 `get_settings()`、`get_deepseek_key()`，提供便捷访问

---

## 5. Class：从 TypeScript class 迁移

### 定义一个类

**真实代码**：[schemas.py:18-24](backend/app/models/schemas.py#L18-L24)

```python
class ChatMessage(BaseModel):
    """A single conversation turn."""

    role: Literal["user", "assistant"] = Field(
        description="Message role: user or assistant"
    )
    content: str = Field(description="Message content")
```

**怎么读**：
- `class ChatMessage(BaseModel):` → 定义类 `ChatMessage`，继承自 `BaseModel`
- `role: Literal[...] = Field(...)` → 类属性 `role`，类型只能是 `"user"` 或 `"assistant"`
- `content: str = Field(...)` → 类属性 `content`，类型是 `str`

**TypeScript 类比**：

```ts
class ChatMessage extends BaseModel {
    role: "user" | "assistant";
    content: string;
}
```

### `self` — 就是 `this`

**真实代码**：[config.py:90-94](backend/app/core/config.py#L90-L94)

```python
def get_deepseek_key(self) -> Optional[str]:
    """Return the plain-text DeepSeek API key, or None."""
    if self.DEEPSEEK_API_KEY is not None:
        return self.DEEPSEEK_API_KEY.get_secret_value()
    return None
```

**怎么读**：
- `self` 是方法的第一个参数 → 调用时自动传入实例
- `self.DEEPSEEK_API_KEY` → 访问这个实例的 `DEEPSEEK_API_KEY` 属性

**TypeScript 类比**：

```ts
getDeepseekKey(): string | null {
    if (this.DEEPSEEK_API_KEY !== null) {   // this 是隐式的
        return this.DEEPSEEK_API_KEY.getSecretValue();
    }
    return null;
}
```

**关键差异**：Python 的 `self` 必须：
1. 显式写在方法参数列表的第一个位置
2. 方法内访问任何实例属性都要写 `self.xxx`

这是 Python 设计哲学"显式优于隐式"(Explicit is better than implicit)的体现。

### `__init__` — 就是 constructor

**真实代码**：[errors.py:101-113](backend/app/core/errors.py#L101-L113)

```python
def __init__(
    self,
    code: str,
    *,
    details: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
) -> None:
    self.code = code
    _http_status, default_message = _get_catalog_entry(code)
    self.http_status: int = _http_status
    self.message: str = message if message is not None else default_message
    self.details: Dict[str, Any] = details if details is not None else {}
    super().__init__(self.message)
```

**怎么读**：
- `def __init__(self, code, ...)` → 构造方法，在 `AppError("FILE_TOO_LARGE")` 时自动调用
- `self.code = code` → 把传入的 `code` 保存到实例上
- `self.http_status: int = ...` → 在赋值的同时声明类型为 `int`
- `super().__init__(self.message)` → 调用父类（`Exception`）的构造方法

**TypeScript 类比**：

```ts
constructor(
    code: string,
    opts?: { details?: Record<string, any>; message?: string }
) {
    super(opts?.message ?? ERROR_CATALOG[code]?.[1] ?? "内部错误");
    this.code = code;
    const [httpStatus, defaultMessage] = getCatalogEntry(code);
    this.httpStatus = httpStatus;
    this.message = opts?.message ?? defaultMessage;
    this.details = opts?.details ?? {};
}
```

### 继承

**真实代码**（当前项目出现的继承关系）：

```python
class AppError(Exception):           # 继承 Python 内置异常
class ChatMessage(BaseModel):        # 继承 Pydantic 数据模型
class Settings(BaseSettings):        # 继承 Pydantic 配置模型
class VectorStore(ABC):              # 继承 Python 抽象基类
class ChunkRecord(BaseModel):        # 继承 Pydantic 数据模型
class VectorSearchResult(BaseModel): # 继承 Pydantic 数据模型
```

**TypeScript 类比**：Python 用 `class Child(Parent)`，和 TS 的 `class Child extends Parent` 一样。

### 实例化

**真实代码**：[config.py:104](backend/app/core/config.py#L104)

```python
settings = Settings()    # 创建一个 Settings 实例，赋给模块级变量
```

**TypeScript 类比**：

```ts
const settings = new Settings();
```

---

## 6. Python Type Hints

### 为什么要学这个

DX-RAG 项目中**几乎每一行代码都有 type hints**。你需要能读懂它们，但不需要写。

### 基本类型

```python
# 真实代码中的基本类型标注
name: str                    # config.py: APP_NAME: str = "dx-rag-demo"
count: int                   # config.py: MAX_UPLOAD_SIZE_MB: int = 50
price: float                 # config.py: LLM_TEMPERATURE: float = 0.2
flag: bool                   # (目前只出现在概念中)
items: List[str]             # config.py: CORS_ORIGINS: List[str]
mapping: Dict[str, Any]      # errors.py: details: Dict[str, Any]
maybe: Optional[str]         # config.py: DEEPSEEK_API_KEY: Optional[SecretStr]
only_these: Literal["a","b"] # schemas.py: role: Literal["user", "assistant"]
any_type: Any                # vector_store.py: metadata: Dict[str, Any]
```

### 和 TypeScript 类型标注的对比

| 维度 | TypeScript | Python Type Hints |
|------|-----------|-------------------|
| **检查时机** | 编译时 | IDE / mypy / pyright 静态检查 |
| **运行时** | 类型被**擦除** | 类型也被**忽略**（Python 解释器不检查） |
| **阻止运行** | ✅ 编译失败不生成 JS | ❌ 类型错误仍然能运行 |
| **动态类型** | 运行时类型必须匹配 | 运行时可以赋任何类型（只要有 hint） |
| **写还是不写** | 几乎所有项目都写 | 不是所有 Python 项目都写，但 DX-RAG 写了 |

### 为什么 Python 动态语言还要写 type hints

一句话回答：**给 IDE 和同事看的，不给自己看的。**

具体原因：
1. IDE 自动补全：写 `settings.` 时，IDE 能列出所有字段
2. 文档作用：读代码的人能立刻知道参数/返回值类型
3. 静态检查：CI 中可以运行 `mypy` 检查类型错误
4. FastAPI 利用它们：FastAPI 根据 type hints 自动生成 OpenAPI 文档

### 在当前项目中你需要能读懂的 type hints

| 写法 | 出现在 |
|------|--------|
| `name: str` | schemas.py、config.py 到处可见 |
| `-> None` | vector_store.py: 所有 abstract method |
| `-> List[str]` | vector_store.py: `add_texts`, `list_collections` |
| `-> int` | vector_store.py: `get_chunk_count`, `delete_by_file` |
| `Optional[X]` | config.py: API Key 字段 |
| `Dict[str, Any]` | errors.py、vector_store.py |
| `Literal["a", "b"]` | schemas.py: role, status, error_code |

---

## 7. Pydantic：以前端开发者的方式理解

### 先建立类比

你熟悉两种东西：

1. **TypeScript interface** — 描述数据的 shape，编译后消失
2. **Zod schema** — 描述数据 shape，运行时做验证

Pydantic 的 `BaseModel` ≈ **两者的结合体**。它既能在开发时提供类型信息，又能在运行时验证数据。

### 最简单的 BaseModel

**真实代码**：[schemas.py:18-24](backend/app/models/schemas.py#L18-L24)

```python
class ChatMessage(BaseModel):
    """A single conversation turn."""

    role: Literal["user", "assistant"] = Field(
        description="Message role: user or assistant"
    )
    content: str = Field(description="Message content")
```

**Python 语法怎么读**：
- `class ChatMessage(BaseModel):` — 定义一个 Pydantic 数据模型
- `role: Literal["user", "assistant"]` — 字段 role，只能是这两个值
- `= Field(description=...)` — 字段的元数据（描述、默认值、验证规则等）

**TypeScript 思维**（Zod 类比）：

```ts
import { z } from "zod";

const ChatMessageSchema = z.object({
    role: z.enum(["user", "assistant"]).describe("Message role: user or assistant"),
    content: z.string().describe("Message content"),
});

type ChatMessage = z.infer<typeof ChatMessageSchema>;
```

这个类比很接近但不完全等价。关键区别：Pydantic 的 `Field` 不仅做验证，还会被 FastAPI 用来生成 OpenAPI 文档。

### Default values

**真实代码**：[schemas.py:130-133](backend/app/models/schemas.py#L130-L133)

```python
class QueryRequest(BaseModel):
    question: str = Field(description="User question")
    collection_name: str = Field(description="Target knowledge base name")
    top_k: int = Field(default=5, description="Number of chunks to retrieve (1-20)")
    history: List[ChatMessage] = Field(
        default_factory=list, description="Conversation history (max 20 messages)"
    )
```

**怎么读**：
- `top_k: int = Field(default=5, ...)` → 不传时默认值是 `5`
- `history: List[ChatMessage] = Field(default_factory=list, ...)` → 不传时默认值是空列表 `[]`
- `default_factory=list` → 每次创建实例时调用 `list()` 生成新的空列表（避免所有实例共享同一个列表对象）

**TypeScript 类比**：

```ts
// 类似在函数参数中解构
function handleQuery({ question, collection_name, top_k = 5, history = [] }: QueryRequest) { ... }
```

### BaseSettings — 自动读环境变量的 Pydantic Model

**真实代码**：[config.py:10-21](backend/app/core/config.py#L10-L21)

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_NAME: str = "dx-rag-demo"
    MAX_UPLOAD_SIZE_MB: int = 50
    ...
```

**怎么读**：
- `class Settings(BaseSettings):` — 和 `BaseModel` 类似，但额外会自动读环境变量
- `model_config = SettingsConfigDict(...)` — 配置选项（从哪里读 env、编码等）
- `APP_NAME: str = "dx-rag-demo"` — 环境变量 `APP_NAME` 如果设置了就用它的值，否则用 `"dx-rag-demo"`

**优先级**：环境变量 > `.env` 文件 > Field 默认值

**TypeScript 思维**：

```ts
// 不像 TS/Node.js 的
const APP_NAME = process.env.APP_NAME || "dx-rag-demo";

// BaseSettings 更像是：你只需要声明字段和默认值，
// 环境变量自动注入、自动类型转换。
```

### SecretStr — 保护敏感值

**真实代码**：[config.py:24-25](backend/app/core/config.py#L24-L25)

```python
DEEPSEEK_API_KEY: Optional[SecretStr] = Field(default=None)
DASHSCOPE_API_KEY: Optional[SecretStr] = Field(default=None)
```

**怎么读**：
- `SecretStr` 是 Pydantic 提供的特殊类型
- 当这个值被 `print()` 或序列化时 → 显示为 `'**********'`
- 需要真实值时 → 调用 `.get_secret_value()`

**为什么需要**：防止 API Key 意外泄露到日志、错误消息或 API 响应中。

### 在当前项目中的作用

Pydantic 在 DX-RAG 中有三种用途：

| 用途 | 类 | 文件 |
|------|---|------|
| API Request/Response 数据模型 | `BaseModel` | `models/schemas.py` |
| 错误响应格式 | `BaseModel` | `core/errors.py` |
| 配置管理 | `BaseSettings` | `core/config.py` |
| 内部存储模型 | `BaseModel` | `core/vector_store.py` |

---

## 8. FastAPI 中出现的特殊 Python 写法

### decorator — `@something`

**真实代码**：[main.py:43-51](backend/app/main.py#L43-L51)

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convert AppError to unified error response format."""
    return JSONResponse(
        status_code=exc.http_status,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
        ).model_dump(),
    )
```

**怎么读**：`@app.exception_handler(AppError)` 的意思是——"把下面这个函数注册为 FastAPI app 的异常处理器。当有人 raise AppError 时，自动调用这个函数。"

**先这样理解**：decorator ≈ 给函数贴了一个"标签"，框架看到这个标签就知道这个函数有特殊用途。

**TypeScript 类比**：最接近的是 NestJS 的 decorator：

```ts
@Catch(AppError)
async appErrorHandler(request: Request, exception: AppError) { ... }
```

🔵 decorator 在 Python 中本质是一个函数调用（`exception_handler(AppError)(app_error_handler)`），但现在不需要理解原理。先当成"框架标签"就行。

### 当前项目出现的 decorator

| Decorator | 文件 | 作用 |
|-----------|------|------|
| `@app.exception_handler(AppError)` | main.py:43 | 注册 AppError 异常处理器 |
| `@app.exception_handler(Exception)` | main.py:54 | 注册全局兜底异常处理器 |
| `@asynccontextmanager` | main.py:15 | 将 async generator 转为 context manager |
| `@abstractmethod` | vector_store.py | 标记方法为"子类必须实现" |
| `@field_validator("CORS_ORIGINS", mode="before")` | config.py:71 | 在字段赋值前运行自定义验证逻辑 |
| `@classmethod` | config.py:72 | 标记方法为类方法（第一个参数是 `cls` 而不是 `self`） |

### `async def` — 异步函数

```python
async def lifespan(app: FastAPI):      # async 函数定义
    yield

async def app_error_handler(...):       # async 异常处理器
    return JSONResponse(...)
```

**TypeScript 类比**：和 JS 的 `async function` 基本一样——函数返回一个可 await 的对象。

🔵 Python async 底层用的是 `asyncio` 事件循环，和 Node.js 的 libuv 不同。Phase 0 不需要深入这个区别。

### `yield` — "暂停，等一下"

**真实代码**：[main.py:15-18](backend/app/main.py#L15-L18)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing to initialize at this stage
    yield
    # Shutdown: nothing to clean up at this stage
```

**怎么读**（先这样理解）：
- `yield` 上面的代码 → 服务**启动时**执行
- `yield` 下面的代码 → 服务**关闭时**执行
- Phase 0 两边都是空的（还没需要初始化的资源）

**TypeScript 类比**：没有直接的语法等价物。最接近的概念可能是 Express 的：

```ts
server.on('listening', () => { /* startup */ });
server.on('close', () => { /* shutdown */ });
```

🔵 `yield` 的完整语义涉及 Python generator 和 context manager 协议，当前不需要深入。

---

## 9. Abstract Class / Interface 思维

> T0101 引入了 ABC（Abstract Base Class）。这是 Phase 0 之后新增的第一个重要 Python 概念。

### 真实代码

**真实代码**：[vector_store.py:79-85](backend/app/core/vector_store.py#L79-L85)

```python
from abc import ABC, abstractmethod

class VectorStore(ABC):
    """Abstract base class for vector storage backends."""

    @abstractmethod
    def create_collection(self, name: str) -> None:
        """Create a new ChromaDB collection."""
        ...

    @abstractmethod
    def search(self, collection, query_vector, top_k) -> List[VectorSearchResult]:
        ...
```

### `ABC` — Abstract Base Class

**怎么读**：
- `from abc import ABC, abstractmethod` → 从 Python 标准库的 `abc` 模块导入两个东西
- `class VectorStore(ABC):` → 继承 `ABC`，标记这个类为"抽象基类"——**它不能被实例化**
- `@abstractmethod` → 标记方法为"抽象方法"——**子类必须实现这个方法**

```python
# ❌ 直接实例化 ABC 会报错
store = VectorStore()  # TypeError: Can't instantiate abstract class VectorStore
```

### 先建立类比

**TypeScript 思维**：

```ts
// Python ABC ≈ TypeScript abstract class
abstract class VectorStore {
    abstract createCollection(name: string): void;
    abstract search(collection: string, queryVector: number[], topK: number): VectorSearchResult[];
}

// ❌ 也不能直接 new
const store = new VectorStore();  // TS 编译错误
```

或者用 interface 思维来理解 contract：

```ts
// ABC 的 11 个 @abstractmethod ≈ 这个 interface 的 11 个方法
interface VectorStore {
    createCollection(name: string): void;
    search(collection: string, queryVector: number[], topK: number): VectorSearchResult[];
    // ... 其余 9 个方法
}
```

### 关键认知

**ABC 定义的是"契约"（contract），不是"实现"（implementation）。**

T0101 的 `VectorStore` 做了以下事情：
- ✅ 说清楚了：有 11 个方法，每个的签名是什么
- ✅ 强制子类必须实现全部 11 个方法（否则无法实例化）
- ❌ 没有一行代码真的操作 ChromaDB

具体 ChromaDB 操作由 T0102-T0108 逐步完成。当前项目中，`VectorStore` 只是一个"接口文档"——Python 会确保后续的实现者不会漏掉某个方法。

### `...`（ellipsis）是什么

```python
@abstractmethod
def create_collection(self, name: str) -> None:
    """Create a new ChromaDB collection."""
    ...                              # ← 这个
```

`...` 在 Python 中是一个合法的表达式（字面量），在这里表示"这个方法体由别人来填"。你可以理解为 `// TODO: 子类实现`。

### 补充：真实代码里 abstract method 的函数体只有 docstring

> 更正：上面说"方法体是 `...`"——查真实代码后确认，vector_store.py 的 11 个抽象方法**没有** `...`，函数体只有 docstring。

**真实代码**：[vector_store.py:89-95](backend/app/core/vector_store.py#L89-L95)

```python
@abstractmethod
def create_collection(self, name: str) -> None:
    """Create a new ChromaDB collection.

    Args:
        name: Collection name (knowledge base name).
    """
```

**为什么这样写是合法的 Python**：字符串字面量（`"""..."""`）本身就是一个合法的表达式语句。函数体只要包含一个字符串，就"非空"，不需要 `pass` 占位。这个 docstring 同时扮演两个角色：

1. 函数的文档（人类阅读用）
2. 函数体本身（让函数体合法非空）

**TypeScript 对比**：JS/TS 中注释**不是**代码——`// comment` 不能充当函数体，空函数体必须写 `{}`。但 Python 的 docstring 不是注释，它是一段真实的字符串表达式。这是前端开发者最容易困惑的差异之一。

**三种"空函数体"写法都是合法的**：

| 写法 | 含义 |
|------|------|
| `pass` | "什么都不做"（显式占位符） |
| `...` | 同样是占位（ellipsis 字面量），语义同 `pass` |
| 只有 docstring | 合法——docstring 兼作函数体 |

**DX-RAG 真实情况**：vector_store.py 全部 11 个抽象方法用的是第三种（docstring-only）。注意：方法的"抽象性"来自 `@abstractmethod` decorator 标记本身——函数体写什么**不影响**"子类必须实现"这个约束，即使写满了真代码，标了 `@abstractmethod` 依然是抽象的。

### docstring 里的 `Args:` / `Returns:` 格式

vector_store.py 的 docstring 里出现了结构化段落：

```python
def create_collection(self, name: str) -> None:
    """Create a new ChromaDB collection.

    Args:
        name: Collection name (knowledge base name).
    """
```

**怎么读**：`Args:` 下面逐行列出"参数名: 说明"；`Returns:` 下面描述返回值。这是 **Google 风格 docstring 约定**（也有 NumPy 风格等其他流派），**不是 Python 语法**——它只是一段给人看的文字，Python 解释器不解析它。

**TypeScript 类比**：

```ts
/**
 * Create a new ChromaDB collection.
 * @param name Collection name (knowledge base name).
 */
```

和 JSDoc 的 `@param` / `@returns` 作用相同。阅读代码时可以直接跳过这些段落——它们不影响代码行为。

---

## 10. Exception Handling

### Python 异常处理的基本语法

**真实代码**：[main.py:43-65](backend/app/main.py#L43-L65)（异常处理器）

虽然 Phase 0 代码中没有直接的 `try/except` 语句，但 `AppError` 类和异常处理器的设计本身依赖 Python 的异常机制。

### Python Exception ←→ JS Error

| Python | JavaScript / TypeScript | 说明 |
|--------|------------------------|------|
| `raise AppError("CODE")` | `throw new AppError("CODE")` | 抛出异常 |
| `try:` ... `except X:` | `try { } catch (e) { }` | 捕获异常 |
| `except AppError as e:` | `catch (e) { if (e instanceof AppError) ... }` | 按类型捕获 |
| `Exception` | `Error` | 所有异常的基类 |

### 真实代码中的 AppError

**真实代码**：[errors.py:91-113](backend/app/core/errors.py#L91-L113)

```python
class AppError(Exception):
    def __init__(
        self,
        code: str,
        *,
        details: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> None:
        self.code = code
        _http_status, default_message = _get_catalog_entry(code)
        self.http_status: int = _http_status
        self.message: str = message if message is not None else default_message
        self.details: Dict[str, Any] = details if details is not None else {}
        super().__init__(self.message)
```

**怎么读**：
- `class AppError(Exception):` → 自定义异常类，继承 Python 的 `Exception`
- `raise AppError("FILE_TOO_LARGE", details={"max_size_mb": 50})` → 抛出一个 AppError
- 在 `__init__` 中自动查 `_ERROR_CATALOG` → 得到 HTTP 状态码和中文消息
- `super().__init__(self.message)` → 调用父类 Exception 的构造方法

**TypeScript 类比**：

```ts
class AppError extends Error {
    code: string;
    httpStatus: number;
    details: Record<string, any>;

    constructor(code: string, opts?: { details?: Record<string, any>; message?: string }) {
        const [httpStatus, defaultMessage] = ERROR_CATALOG[code] ?? [500, '服务器内部错误'];
        super(opts?.message ?? defaultMessage);
        this.code = code;
        this.httpStatus = httpStatus;
        this.details = opts?.details ?? {};
    }
}
```

### 当前项目中异常的工作流程

```text
某个 Service 层代码:
    raise AppError("FILE_TOO_LARGE", details={"max_size_mb": 50})
        │
        ▼
FastAPI 捕获这个异常（因为注册了 @app.exception_handler(AppError)）
        │
        ▼
app_error_handler 函数:
    1. 从 exc.code 得到 "FILE_TOO_LARGE"
    2. 从 exc.http_status 得到 413
    3. 从 exc.message 得到 "文件大小超出限制"
    4. 构建 ErrorResponse JSON
        │
        ▼
返回 HTTP 413:
    {"error": {"code": "FILE_TOO_LARGE", "message": "文件大小超出限制", "details": {"max_size_mb": 50}}}
```

---

## 11. Python Dependency Management

### 对比你熟悉的 Node.js

| 概念 | Node.js / npm | Python / pip | DX-RAG 相关 |
|------|-------------|-------------|-----------|
| 依赖声明文件 | `package.json` | `requirements.txt` | [backend/requirements.txt](../../backend/requirements.txt) |
| 安装命令 | `npm install` | `pip install -r requirements.txt` | |
| 安装目录 | `node_modules/` | 系统 site-packages 或虚拟环境 | |
| 环境隔离 | `node_modules/.bin/` | `venv/` 虚拟环境 | 需要手动创建 |
| 精确版本锁定 | `package-lock.json` | Python 没有统一 lockfile 标准 | DX-RAG 目前只用 `>=` |
| 包仓库 | npm registry | PyPI | |

### 虚拟环境是什么

Python 默认把安装的包放在**系统全局目录**。如果项目 A 需要 `chromadb==0.4.15`，项目 B 需要 `chromadb==0.5.0`，全局安装会冲突。

**虚拟环境** 给每个项目创建一个**隔离的 Python 环境**，里面有独立的 site-packages 目录。

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows

# 之后所有 pip install 都只影响这个项目
pip install -r requirements.txt
```

**前端类比**：`node_modules/` 天然按项目隔离（每个项目有自己的 `node_modules`），所以 Node.js 不需要"虚拟环境"这个概念。Python 选择了一个不同的路径：通过 venv 明确隔离。

### DX-RAG 当前依赖

[requirements.txt](../../backend/requirements.txt) 中的 11 个包：

```text
fastapi>=0.115.0
uvicorn>=0.34.0
chromadb>=0.4.15
sentence-transformers>=3.0.0
PyMuPDF>=1.27.2
python-docx>=1.1.0
openpyxl>=3.1.0
openai>=1.0.0
dashscope>=1.21.0
python-multipart>=0.0.18
pydantic-settings>=2.0.0
```

**怎么读**：`>=` 表示"这个版本及以上"。不像 `package.json` 有 `^`/`~` 等详细的范围语义。

---

## 12. 最容易混淆的 Python 概念

> 根据当前 DX-RAG 代码整理。

### 1. `self` vs `this`

| | Python `self` | TypeScript `this` |
|---|---|---|
| **声明** | 显式写在方法第一个参数 | 隐式、自动可用 |
| **访问属性** | 必须写 `self.xxx` | `this.xxx` |
| **原理** | Python 把实例作为第一个参数传入 | JS 根据调用方式动态绑定 |

**记住**：在 Python 类的方法中，**只要是访问实例自身的属性，前面都必须加 `self.`**。

### 2. `None` vs `null` vs `undefined` vs `void`

| Python | TypeScript | 什么时候用 |
|--------|-----------|----------|
| `x = None` | `x = null` | 表示"没有值" |
| (不存在) | `undefined` | Python 没有这个概念 |
| `-> None` | `: void` | 函数不返回有意义的值 |

**记住**：Python 只有 `None`，它同时扮演了 `null` 和 `void` 的角色，但没有 `undefined`。

### 3. `BaseModel` vs TypeScript `interface`

| | Pydantic BaseModel | TypeScript interface |
|---|---|---|
| **存在时机** | 运行时 + IDE | 仅编译时 |
| **验证数据** | ✅ 自动 | ❌ 需要 Zod 等库 |
| **序列化** | `.model_dump()` | `JSON.stringify()` |
| **反序列化** | `Model(**dict)`，自动验证 | `JSON.parse()`，需手动验证 |
| **文档生成** | FastAPI 自动生成 OpenAPI | 需额外工具 |

**记住**：Pydantic 不只是"Python 的 interface"。把它想成 interface + Zod + 自动文档三合一。

### 4. Module vs Package

| | Module | Package |
|---|---|---|
| **是什么** | 一个 `.py` 文件 | 一个含 `__init__.py` 的目录 |
| **例子** | `config.py` | `app/core/` |
| **import** | `from app.core.config import settings` | `from app.core import config` |

**记住**：区分的关键是——看有没有 `__init__.py`。有它就是 package（目录），没有它的 `.py` 文件就是 module。

### 5. FastAPI vs Uvicorn

| | FastAPI | Uvicorn |
|---|---|---|
| **是什么** | Web 框架 | ASGI 服务器 |
| **职责** | 路由匹配、参数解析、响应生成 | TCP 监听、HTTP 字节流收发 |
| **类比** | Express | Node.js `http.createServer()` |
| **关系** | 一个人写"收到请求该怎么办" | 一个人负责"真的去收请求" |

**记住**：FastAPI 和 Uvicorn 是两个人，不是一个东西。启动后端时你调用的是 Uvicorn，Uvicorn 再驱动 FastAPI。

### 6. ABC method 声明 vs Concrete Implementation

| | T0101 的 `VectorStore` | 未来的 `ChromaVectorStore` |
|---|---|---|
| **是什么** | 抽象基类（ABC） | 具体实现类 |
| **能实例化吗** | ❌ 不能 | ✅ 能 |
| **方法体** | `...`（空） | 真实的 ChromaDB 操作代码 |
| **完成的 Task** | T0101 | T0102–T0108 |

**记住**：看到 `@abstractmethod` + `...` 时，它在说"这个方法是合同——具体怎么做由另一个人（子类）来填"。不要认为定义了方法就等于实现了功能。

---

## 13. 当前项目 Python 阅读路线

> 按这个顺序阅读 Python 文件，难度递增。

### 1. [backend/app/models/schemas.py](../../backend/app/models/schemas.py) — Pydantic 模型（189 行）

**建议第一个读**。你只需要理解 class 和 type hints。

**第一遍看**：
- `ChatMessage`（18–24 行）—— 最简单的模型，只有两个字段
- `QueryRequest`（125–133 行）—— 注意 `Field(default=5)` 怎么设默认值
- `UploadResponse`（92–108 行）—— 注意 `Literal["SUCCESS", "SUCCESS_WITH_WARNINGS"]` 的用法

**暂时跳过**：`Field(description=...)` 的具体文字内容

**能回答这些就算看懂**："这个文件定义了什么？Pydantic 的 `Field` 可以做什么？"

### 2. [backend/app/core/errors.py](../../backend/app/core/errors.py) — 错误定义（114 行）

**第一遍看**：
- `_ERROR_CATALOG` 字典（41–76 行）—— 所有错误码
- `AppError.__init__`（101–113 行）—— 理解 `self.code = code` 是怎么保存参数到实例的

**暂时跳过**：`_get_catalog_entry` 函数实现

**能回答这些就算看懂**："如果想新增一个错误类型，在哪里加？`AppError` 的 constructor 做了什么事？"

### 3. [backend/app/core/config.py](../../backend/app/core/config.py) — 配置（111 行）

**第一遍看**：
- `Settings` 类的 22 个字段（24–70 行）
- `settings = Settings()`（104 行）和 `get_settings()`（107–109 行）
- `get_deepseek_key()` 方法（90–94 行）—— 理解 `self.xxx` 怎么用

**暂时跳过**：
- `model_config` 细节（17–21 行）
- `field_validator` / `@classmethod`（71–72 行）

**能回答这些就算看懂**："`MAX_UPLOAD_SIZE_MB` 的默认值在哪定义的？如果想加一个新配置项，怎么做？"

### 4. [backend/app/main.py](../../backend/app/main.py) — 应用入口（69 行）

**第一遍看**：
- import 区域（1–12 行）—— 理解哪些是自己的模块、哪些是第三方库
- `app = FastAPI(...)`（22–27 行）
- `app.add_middleware(CORSMiddleware, ...)`（29–35 行）
- `app.include_router(api_router, prefix="/api")`（68 行）

**暂时跳过**：
- `@asynccontextmanager` 和 `yield` 的原理
- `@app.exception_handler` decorator 的原理
- `model_dump()` 的具体实现

**能回答这些就算看懂**："CORS 在哪配置？`/api` 前缀从哪来？全局异常处理怎么注册的？"

### 5. [backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) — ABC 接口（226 行）

**第一遍看**：
- 文件头部 docstring（1–18 行）—— 理解 SPEC F008 的 4 条约束
- `ChunkRecord` 和 `VectorSearchResult` 的字段（31–71 行）
- `VectorStore(ABC)` 的方法签名（79–225 行）

**暂时跳过**：每个方法的 docstring 细节

**能回答这些就算看懂**："`@abstractmethod` 是干什么的？这个文件定义了 11 个方法，但为什么没有一个实现了？`search()` 为什么返回 `similarity_score` 而不是距离？"

---

## 14. 当前阶段只需要掌握的内容

### 🟢 现在必须能看懂

- [ ] `def` 定义函数，`class` 定义类
- [ ] `self` ≈ `this`，但必须显式写
- [ ] `__init__` ≈ constructor
- [ ] `from X import Y` 的基本读法
- [ ] `: str`、`: int`、`: bool` 这些 type hints
- [ ] `-> None` 表示无返回值
- [ ] `List[X]` ≈ `X[]`，`Dict[str, X]` ≈ `Record<string, X>`
- [ ] Pydantic `BaseModel` = 数据类型定义 + 运行时验证
- [ ] `BaseSettings` 自动读环境变量
- [ ] `@abstractmethod` = 子类必须实现这个方法
- [ ] `raise AppError("CODE")` ≈ `throw new AppError("CODE")`

### 🟡 知道存在即可

- [ ] `@decorator` 是给函数/类加"框架标签"
- [ ] `async def` / `await` — 和 JS 差不多，目前不需要深究
- [ ] `yield` — lifespan 中用于分隔 startup 和 shutdown
- [ ] `SecretStr` — 保护 API Key 不泄露
- [ ] `model_dump()` — Pydantic 的对象转 dict 方法
- [ ] `Field(description=...)` — Pydantic 字段的元数据
- [ ] `Optional[X]` = `X | None`

### 🔵 暂时完全不用学

- [ ] decorator 的实现原理（`@` 语法背后怎么工作的）
- [ ] Python generator / `yield` 的完整机制
- [ ] ASGI protocol 细节
- [ ] Python `asyncio` 事件循环
- [ ] Context manager protocol（`__enter__` / `__exit__`）
- [ ] Python descriptor protocol
- [ ] Metaclass
- [ ] `mypy` 类型检查器的配置
- [ ] Pydantic v1 vs v2 的差异
- [ ] FastAPI `Depends()` 依赖注入

---

## 15. Python 生词表

> 按首次出现顺序排列。持续性维护。

| 术语 | 最简单解释 | TS / Node 类比 | 首次出现 |
|------|----------|---------------|---------|
| `def` | 定义函数 | `function` | T0001 |
| `class` | 定义类 | `class` | T0003 |
| `import X` | 导入整个模块 | `import * as X from "x"` | T0001 |
| `from X import Y` | 从模块中导入指定项 | `import { Y } from "x"` | T0001 |
| `self` | 类方法中指向实例自身 | `this`（但语法不同） | T0003 |
| `__init__` | 构造方法 | `constructor` | T0004 |
| `str` | 字符串类型 | `string` | T0003 |
| `int` | 整数类型 | `number`（不区分整/浮） | T0003 |
| `float` | 浮点数类型 | `number` | T0003 |
| `bool` | 布尔类型 | `boolean` | T0003 |
| `None` | 空值 / 无返回值 | `null` / `void`（兼有两者含义） | T0003 |
| `True` / `False` | 布尔字面量 | `true` / `false` | T0004 |
| `List[X]` | 列表（动态数组） | `X[]` | T0003 |
| `Dict[K, V]` | 字典（键值对映射） | `Record<K, V>` | T0004 |
| `Optional[X]` | 可选类型 | `X \| null` | T0003 |
| `Literal["a"]` | 字面量联合类型 | `"a" \| "b"` | T0005 |
| `Any` | 任意类型 | `any` | T0005 |
| `-> ReturnType` | 返回值类型标注 | `: ReturnType` | T0001 |
| `-> None` | 无返回值 | `: void` | T0101 |
| `@decorator` | 给函数/类加"框架标签" | NestJS `@Decorator()`（不完全等价） | T0001 |
| `async def` | 定义异步函数 | `async function` | T0001 |
| `await` | 等待异步结果 | `await` | T0001 |
| `BaseModel` | Pydantic 数据模型基类 | TypeScript interface + Zod schema | T0005 |
| `BaseSettings` | 自动读环境变量的配置模型 | `process.env` + 类型验证 | T0003 |
| `SecretStr` | 保护敏感字符串不被打印 | 无直接类比 | T0003 |
| `Field(...)` | Pydantic 字段元数据 | Zod `.describe()` / `.default()` | T0005 |
| `model_dump()` | 将 Pydantic 对象转为 dict | `JSON.stringify()` 的前一步 | T0004 |
| `ABC` | 抽象基类 | `abstract class` | T0101 |
| `@abstractmethod` | 标记方法为"子类必须实现" | `abstract method()` | T0101 |
| `...`（ellipsis） | 占位符——表示"实现由别人填" | `// TODO` 或空函数体 | T0101 |
| `*`（在参数列表中） | `*` 之后的参数必须用名字传参 | 无直接 TS 语法 | T0004 |
| `pass` | 空语句占位符 | 空的 `{}` | (Phase 0 未实际使用) |
| `Exception` | Python 所有异常的基类 | `Error` | T0004 |
| `raise` | 抛出异常 | `throw` | T0004 |
| `super()` | 调用父类方法 | `super` | T0004 |
| `logging` | Python 标准日志模块 | `console.log` / `winston` 等 | T0001 |
| `yield` | generator / context manager 暂停点 | 无直接类比 | T0001 |

---

## 16. 我的 Python 学习进度

### 已经接触（✅）

| 知识 | 来自 | 理解程度 |
|------|------|---------|
| `def` / `class` / `import` | T0001 | 基本能读 |
| `self` / `__init__` | T0003, T0004 | 知道 ≈ `this` / `constructor` |
| type hints (`: str`, `-> None`) | T0003, T0005, T0101 | 能读基本类型 |
| Pydantic `BaseModel` | T0005 | 知道 = TS interface + Zod |
| Pydantic `BaseSettings` | T0003 | 知道自动读环境变量 |
| `AppError` / 异常处理 | T0004 | 知道 ≈ `throw new AppError()` |
| `@decorator` | T0001, T0101, T0003 | 先当成"框架标签" |
| `ABC` / `@abstractmethod` | T0101 | 知道定义 contract ≠ 实现功能 |
| `async` / `await` | T0001 | 和 JS 差不多 |
| 虚拟环境 / pip / requirements.txt | T0001 | 知道基本命令 |

### 正在建立理解（🟡）

| 知识 | 需要结合哪些后续代码 |
|------|-------------------|
| FastAPI Request → Response 完整生命周期 | T0102+ 的 endpoint 实现 |
| Pydantic 的运行时验证如何被 FastAPI 触发 | T0401+ 的第一个 API endpoint |
| `yield` / context manager | Phase 2/3 出现具体 startup 逻辑时 |
| Python 的 import 搜索路径问题排查 | 首次遇到 `ModuleNotFoundError` 时 |

### 尚未遇到

| 未来会出现的 Python 概念 | 预期出现的 Task |
|------------------------|---------------|
| `try / except` | Phase 3+ 文件处理异常 |
| `with` 语句 (context manager) | Phase 2 模型加载 / 文件操作 |
| Generator / `yield from` | 如项目用到需要大量数据处理 |
| TypeVar / Generic | 如需泛型抽象 |
| Dataclass | 如需轻量数据容器 |

---

> **下一步**：继续积累 Phase 1 (T0102–T0108) 中遇到的 Python 知识，届时更新此文档。
