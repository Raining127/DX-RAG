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

> 只收录当前 DX-RAG 代码（Phase 0 + T0101–T0108）真实出现过的语法。

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
| `@staticmethod` | `static 方法名() { }` | 方法没有 `self`（不需要实例状态）；TS 用关键字标记，Python 用装饰器标记 | `vector_store.py:436`（`_to_chunk_records`，详见第 17.9 节） |

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
| `...`（ellipsis） | `// TODO` 或空实现 | 占位表达式。⚠️ 注意：`vector_store.py` 的 11 个抽象方法**没有**用 `...`——函数体只有 docstring（见第 9 节"补充"） | （Phase 1 真实代码未使用） |
| `"string"` vs `'string'` | 单引号和双引号都可以 | Python 中 `"` 和 `'` 完全等价，不像 JS 有 prettier 偏好 | `config.py`: 大部分用 `"` |
| `"""docstring"""` | `/** JSDoc */` 或 `/* 多行注释 */` | Python 用三引号写多行文档字符串，放在函数/类定义后第一行 | `vector_store.py:1-18`、`schemas.py:1-6` |
| `[expr for item in iterable]`（list comprehension） | `array.map(item => expr)` | 详见第 17 节 | `vector_store.py:281` |
| `raise NotImplementedError(...)` | `throw new Error("TODO")` | 详见第 17.2 节。⚠️ 当前代码已无 stub（T0108 起 11/11 全部真实）——此写法只剩历史教学价值 | `vector_store.py`（T0102 历史片段） |
| `_name`（单下划线前缀属性） | `private` 字段（但无编译期强制） | 详见第 17 节 | `vector_store.py:250`（`self._client`） |
| `in` / `not in`（成员测试） | `list.includes(x)`（注意 JS 的 `in` 语义不同） | 详见第 17.5 节 | `vector_store.py:299`（`if old_name not in ...`） |
| `range(n)` / `range(len(xs))` | 生成 0…n-1 的整数序列，配合 `for` 做索引循环 | JS 无内置 range；等价 `Array.from({length: n}, (_, i) => i)`，详见第 17.6 节 | `vector_store.py:369` |
| `for i in range(len(xs)):` | 经典三段式 `for (let i = 0; i < xs.length; i++)` | 与 `for x in xs`（遍历元素）是两种循环，详见第 17.6 节 | `vector_store.py:369` |
| `lambda r: r.x` | 箭头函数 `r => r.x` | 只能写一个表达式（不能多行），详见第 17.7 节 | `vector_store.py:382` |
| `list.sort(key=..., reverse=True)` | `arr.sort((a, b) => b.x - a.x)` | 思路不同：Python 交"比什么"（key），JS 交"怎么比"（comparator），详见第 17.7 节 | `vector_store.py:382` |
| `list.append(x)` | `arr.push(x)` | 几乎一致（就地修改） | `vector_store.py:372` |
| `max(a, b)` / `min(a, b)` | `Math.max(a, b)` / `Math.min(a, b)` | 几乎一致；嵌套组合可做 clamp | `vector_store.py:378` |
| 变量标注 `x: Type = value` | `const x: Type = value` | 局部变量也能写类型标注；运行时完全不检查，纯给人/工具看（详见第 17.10 节） | `vector_store.py:417` |
| `dict.values()` | `Object.values(obj)` | Python 返回"视图"不是数组，要 `list(...)` 包一层才是真列表（详见第 17.11 节） | `vector_store.py:432` |
| `list(x)` | `Array.from(x)` | 把可迭代对象转成列表（视图 → 列表） | `vector_store.py:432` |
| dict 当 Map 的聚合计数器（`if k not in d: 初始化` + `d[k]["n"] += 1`） | `Map` + `reduce` 聚合 | dict 的 key 天然唯一 → 去重靠数据结构；首见初始化、其余累加（详见第 17.11 节） | `vector_store.py:417-431` |
| `d["key"]` 按键取值 | `obj.key`（TS 两种写法，Python 只有方括号） | 方括号不是数组下标；键不存在抛 `KeyError`（JS 返回 `undefined`），详见第 17.12 节 | `vector_store.py:331`（`meta["chunk_id"]`） |

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

**真实代码**：[config.py:107-109](backend/app/core/config.py#L123-L125)

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

**真实代码**：[errors.py:101-107](backend/app/core/errors.py#L117-L123)

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

**真实代码**：[vector_store.py:89-91](backend/app/core/vector_store.py#L105-L107)

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

**真实代码**：[schemas.py:18-24](backend/app/models/schemas.py#L34-L40)

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

**真实代码**：[config.py:90-94](backend/app/core/config.py#L106-L110)

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

**真实代码**：[errors.py:101-113](backend/app/core/errors.py#L117-L129)

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

**真实代码**：[config.py:104](backend/app/core/config.py#L120)

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

**真实代码**：[schemas.py:18-24](backend/app/models/schemas.py#L34-L40)

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

**真实代码**：[schemas.py:130-133](backend/app/models/schemas.py#L146-L149)

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

**真实代码**：[config.py:10-21](backend/app/core/config.py#L26-L37)

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

**真实代码**：[config.py:24-25](backend/app/core/config.py#L40-L41)

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

**真实代码**：[main.py:43-51](backend/app/main.py#L59-L67)

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

**真实代码**：[main.py:15-18](backend/app/main.py#L31-L34)

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

**真实代码**：[vector_store.py:79-85](backend/app/core/vector_store.py#L95-L101)

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

**真实代码**：[vector_store.py:89-95](backend/app/core/vector_store.py#L105-L111)

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

### T0102 补充：ABC 的实现侧（子类怎么写）

> T0101 只讲了"声明契约"这一侧。T0102 第一次出现了"实现契约"这一侧，有两个关键认知补充。

**真实代码**：[vector_store.py:256-265](backend/app/core/vector_store.py#L272-L281)

```python
class ChromaVectorStore(VectorStore):
    def create_collection(self, name: str) -> None:
        self._client.create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
```

**怎么读**：子类重写父类的抽象方法——**不需要**任何装饰器、`override` 关键字或特殊标记。父类那里标过一次 `@abstractmethod`，子类这里直接写同名方法就算"实现"。

**TypeScript 类比**：

```ts
class ChromaVectorStore extends VectorStore {
  createCollection(name: string): void { ... }  // TS 可选写 override 关键字
}
```

**两个关键差异（T0102 新认知）**：

1. **检查时机**：Python 的检查发生在**实例化时**（漏了抽象方法 → `ChromaVectorStore()` 抛 TypeError），TS 是编译期报错。
2. **检查的是"有没有定义"，不是"有没有真实逻辑"**：T0102 的 8 个方法虽然只是 `raise NotImplementedError` 的占位（见第 17 节），但它们在子类里"被定义"了，所以类照样能实例化。ABC 不是质量检查员，只是"签名点名器"。

**DX-RAG T0102 中在哪里使用**：[vector_store.py:236-335](backend/app/core/vector_store.py#L252-L351) — `ChromaVectorStore` 是项目中第一个 ABC 实现类（T0102 时 3 个真实方法 + 8 个占位；T0103 起 4 + 7）。

---

## 10. Exception Handling

### Python 异常处理的基本语法

**真实代码**：[main.py:43-65](backend/app/main.py#L59-L97)（异常处理器）

虽然 Phase 0 代码中没有直接的 `try/except` 语句，但 `AppError` 类和异常处理器的设计本身依赖 Python 的异常机制。

### Python Exception ←→ JS Error

| Python | JavaScript / TypeScript | 说明 |
|--------|------------------------|------|
| `raise AppError("CODE")` | `throw new AppError("CODE")` | 抛出异常 |
| `try:` ... `except X:` | `try { } catch (e) { }` | 捕获异常 |
| `except AppError as e:` | `catch (e) { if (e instanceof AppError) ... }` | 按类型捕获 |
| `Exception` | `Error` | 所有异常的基类 |

### 真实代码中的 AppError

**真实代码**：[errors.py:91-113](backend/app/core/errors.py#L107-L129)

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
| **方法体** | 只有 docstring（空函数体，见第 9 节"补充"） | 真实的 ChromaDB 操作代码 |
| **完成的 Task** | T0101 | T0102–T0108 |

**记住**：看到 `@abstractmethod`（函数体只有 docstring）时，它在说"这个方法是合同——具体怎么做由另一个人（子类）来填"。不要认为定义了方法就等于实现了功能。

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

### 5. [backend/app/core/vector_store.py](../../backend/app/core/vector_store.py) — ABC 接口 + ChromaDB 实现（495 行）

**第一遍看**：
- 文件头部 docstring（1–18 行）—— 理解 SPEC F008 的 4 条约束
- `ChunkRecord` 和 `VectorSearchResult` 的字段（35–75 行）
- `VectorStore(ABC)` 的方法签名（83–226 行）
- `ChromaVectorStore`（237–495 行）—— 11 个方法全部真实实现（T0108 起已无 stub），先看 `__init__`（250–252 行）再看感兴趣的方法

**暂时跳过**：每个方法的 docstring 细节

**能回答这些就算看懂**："`@abstractmethod` 是干什么的？T0101 的 11 个方法为什么一个都没实现？T0102 当时为什么有 8 个方法要写成 `raise NotImplementedError` 占位、而不是干脆不写？现在 11 个方法全部真实实现了吗？`search()` 为什么返回 `similarity_score` 而不是距离？"

### 6. [backend/app/services/embedding.py](../../backend/app/services/embedding.py) — Embedding 模型懒加载单例 + 向量生成（77 行，T0201/T0202）

**第一遍看**：
- 文件头部 docstring（1–16 行）—— SPEC F007 的浓缩契约（加载策略 + 生成契约 + 错误契约）
- 模块级缓存变量（27–28 行）—— `_model: Optional["SentenceTransformer"] = None`，单例地基
- `get_model()`（31–55 行）—— T0201 全部逻辑，注意 `global _model`、函数内 import、`raise ... from exc` 三处新语法
- `encode_chunks()`（58–77 行）—— T0202 新增：`if not chunks` 真值判断 + 一行链式调用 `.encode(...).tolist()`（numpy 知识见 19.2）

**暂时跳过**：无——77 行没有冗余内容。

**能回答这些就算看懂**："`if TYPE_CHECKING:` 里的 import 什么时候执行？为什么顶部不直接 import sentence_transformers？删掉 `global _model` 会怎样？模型加载失败后第二次调用会发生什么？`encode_chunks` 为什么需要 `.tolist()`？`if not chunks` 在 JS 里照抄会有什么 bug？"

### 7. [backend/app/services/ingest.py](../../backend/app/services/ingest.py) — 解析 + OCR + 清洗 + 切分 + 编排（686 行，T0301–T0308）

**建议读完 embedding.py 再读**。Phase 3 的核心文件，七个函数 + 一个服务类（`IngestService`）+ 一组警告基础设施都在这（T0307 的 `chunk_text` 新增知识见第 24 节，T0308 的 `IngestService` 见第 25 节）。

**第一遍看**：
- 文件头部 docstring（1–65 行）—— 八段契约：文本 + DOCX + Excel + PDF + OCR + 清洗 + 切分 + **Ingest 管道** + 错误契约（"文件头 = 浓缩契约"，读到哪个 Task 看哪段）
- `parse_text_file()`（78–108 行）—— 读 bytes → 三级编码级联 → str（T0301）
- `parse_docx_file()`（111–147 行）—— python-docx 打开 → 段落+表格拼接（T0302）
- `parse_excel_file()`（150–191 行）—— openpyxl 打开 → 逐 sheet 逐行提取、跳空行空 sheet（T0303）
- `parse_pdf_file()`（194–251 行）—— fitz 逐页提取原生文本；空页 → 回调 ocr_page；页间 "\n\n" 拼接；needs_pass → 422 ENCRYPTED_PDF；finally close（T0304）
- OCR 基础设施（253–281 行）—— `_OCR_PROMPT` / 重试常量 / `_OCR_WARNINGS` 模块级状态 + get/clear 访问器对
- `ocr_page()`（284–378 行）—— key 检查 → 渲染 JPEG → Base64 → Qwen-VL 调用 → try/except/else 重试（1s/2s 退避 ×3）→ 失败页记 warning + ""（T0305）
- `clean_text()`（386–413 行）—— 三行列表推导管道：splitlines → strip → 过滤空行 → join（T0306）
- `chunk_text()`（433–531 行）—— 两段式切分（标题优先、超长递归再切）+ UUID ID 生成；T0308 起签名新增 `file_id` 继承参数（T0307）
- `IngestService`（534–683 行）—— 类方法编排 parse→clean→chunk→embed→store + 三态判定 + FAILED 幂等回滚（T0308）

**暂时跳过**：无——686 行没有冗余内容（`clean_text` 函数体只有 4 行；`chunk_text` 见 phase-03 第 32–36 节，`IngestService` 见 phase-03 第 37–41 节，新增语法见本手册第 24–25 节）。

**能回答这些就算看懂**："为什么用 `read_bytes()` 而不是 `read_text()`？UTF-8/UTF-16 为什么用 strict、GBK 为什么用 ignore？循环里没有 `break` 为什么第一次成功就能退出？五个函数各自的 `raise` 分别在什么条件下触发？`from docx import Document` 为什么放函数里？`Document(str(file_path))` 为什么有 `str()`、`load_workbook(file_path)` 为什么没有、`fitz.open(str(file_path))` 为什么又有了？`load_workbook(..., data_only=True)` 的 data_only 是干嘛的？为什么 `cell is not None` 而不是 `if cell`？全空行、全空 sheet 各在哪一行被跳过？`parse_pdf_file` 的三岔口（原生/回调/空串）是什么条件？`page.number + 1` 和 `page_number - 1` 为什么两个方向都要转？`OCR_AUTH_FAILED` 写在 `else` 块里为什么不会被 `except Exception` 吞掉？`_OCR_WARNINGS` 为什么不作为返回值？为什么 `splitlines()` 而不是 `split("\n")`？先 strip 后过滤、先过滤后 strip 有区别吗？SPEC 的 Step 5 代码在哪里？clean_text 为什么是全模块唯一没有 try/except 的函数？chunk_text 为什么先标题切分再递归切分、而不是反过来？`source_file` 参数在函数体里出现了几次、为什么还要保留？file_id 为什么在循环外生成、chunk_id 为什么在循环内？`pieces.append` 和 `pieces.extend` 为什么必须分清？空文本进 chunk_text 会怎样、谁负责"拒绝"？`"Header 1"` 这种键名是谁定的？IngestService.process 的五键 dict 里为什么没有文本？file_id 为什么上移到管道第一行生成？FAILED 为什么不 raise？两道闸门各接住哪个站点产出的空值？`suffix in _TEXT_EXTENSIONS` 为什么用 set 而不是 list？`f"uploads/..."` 是什么语法？`unlink(missing_ok=True)` 的 missing_ok 是干什么的？"

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
- [ ] `range(len(x))` 索引循环 ≈ 经典三段式 for 循环
- [ ] `lambda` + `sort(key=..., reverse=True)`（按字段排序，reverse=True 降序）
- [ ] `@staticmethod`（类里的静态方法，没有 self）
- [ ] `if not 容器` 真值判断（空 list/dict/str 是假值；⚠️ JS 里 `[]` 是真值）
- [ ] `global` 关键字（函数内给模块级变量赋值必须声明；读不需要）
- [ ] `is None` 身份比较（判断空值用 `is`，`==` 可被重写）
- [ ] 函数内 import（延迟 import：首次调用才加载，重复执行零开销）
- [ ] `if TYPE_CHECKING:` + 字符串类型标注（重依赖的"假 import"，运行时零成本）
- [ ] `.tolist()`（numpy 数组 → Python 原生 list；numpy float32 ≠ Python float）
- [ ] `Path.read_bytes()`（pathlib 路径对象 + 一次性读文件为 bytes）
- [ ] `bytes` / `str` 与 `.decode(encoding, errors=...)`（str 是码点、bytes 是字节；二进制读入必须解码）
- [ ] 解码错误策略 `errors="strict"` / `"ignore"`（strict 遇非法字节抛错、ignore 静默丢弃；≈ TextDecoder 的 fatal 开关）
- [ ] `str(path)`（Path → 字符串，桥接只认 str 路径的老库 API）
- [ ] 生成器表达式 `(x for x in y)`（圆括号版列表推导：惰性、不造中间 list，常作 `join()` 等函数的参数）
- [ ] `str.splitlines()` —— 按"行边界"切文本：认 `\r\n` / `\r` / `\v` / `\f` / Unicode 行分隔符，且**不产生末尾空串**（`split('\n')` 的升级版）
- [ ] `str.strip()` —— 去掉字符串首尾空白（≈ JS `trim()`；还认全角空格等 Unicode 空白，且不动行内）
- [ ] `"sep".join(可迭代对象)`（⚠️ 和 JS 方向相反：Python 的 join 挂在分隔符字符串上，不是数组上）
- [ ] `is not None`（过滤"没有值"：⚠️ `0` 是合法值且是假值，真值判断会误杀——判断空值用 `is None` / `is not None`）
- [ ] `data_only=True`（公式单元格读缓存值；无缓存 → None）
- [ ] 生成器表达式带过滤 `(str(c) for c in row if c is not None)`（**先过滤、后转换**——`if` 检查原始元素）
- [ ] `try/except/else`（else 只在 try 无异常时执行；⚠️ **else 里的异常不会被本层 except 捕获**——所以 else 里 raise 的 AUTH_FAILED 能穿透重试循环）
- [ ] 回调函数作为参数（`parse_pdf_file(file_path, ocr_page=...)`——函数是一等公民，TS 传 callback 同款；Python 写法是 `Optional[Callable[[Path, int], str]]`）
- [ ] `isinstance(item, dict)`（运行时类型检查——判断"这个值是不是某类型"；防御外部 API 返回的不可信数据）
- [ ] `base64.b64encode(bytes).decode("ascii")`（二进制 → Base64 文本；Base64 只含 ASCII 字符所以 decode("ascii") 永远安全）
- [ ] `uuid.uuid4()` + `str()`（UUID4 = 随机 128 位全局唯一；`str()` 因为 uuid4() 返回 UUID 对象不是 str——≈ `crypto.randomUUID()` 直接给 string，Python 多一步转换）
- [ ] `enumerate(可迭代对象)`（带下标遍历：`for index, item in enumerate(xs)` 产出 `(0, 元素0), (1, 元素1)...`——≈ map/forEach 的第二个参数）
- [ ] `list.append(x)` vs `list.extend(可迭代对象)`（加一个元素 vs 摊开加一筐；⚠️ `append(一个 list)` 会得到嵌套 list——≈ `push(x)` vs `push(...xs)`）
- [ ] 元组 `(a, b)`（圆括号的不可变序列；常作"键值对"常量表；支持解包 `for a, b in pairs`——JS 无内置元组，≈ `as const` 只读数组）
- [ ] 字典字面量 `{"key": value}`（造 dict 的基本写法，key 要带引号；列表推导里每轮造一个新 dict——≈ JS 对象字面量）
- [ ] `@classmethod` + `cls`（类方法：第一个参数是**类本身**不是实例，`cls._parse(...)` ≈ static 方法里的 `IngestService._parse(...)`——T0308 起与 `@staticmethod` 并存）
- [ ] `datetime.now(timezone.utc).isoformat()`（UTC 时间戳字符串——显式时区 + ISO 8601 格式；≈ `new Date().toISOString()`）
- [ ] 关键字实参 `fn(x=1, y=2)`（按**参数名**传值——长参数列表防顺序错误；T0308 的 `chunk_text(cleaned, file_name, file_id=file_id)` 就是它）
- [ ] set 字面量 `{".txt", ".md"}`（花括号里**没冒号** = set；成员测试 `x in s` ≈ `set.has(x)`，O(1)）
- [ ] f-string `f"uploads/{a}/{b}"`（字符串插值——≈ JS 模板字符串 `${a}`；Python 3.6+，前缀 `f`）
- [ ] `Path.unlink(missing_ok=True)`（删除文件；`missing_ok=True` 时文件不存在也不报错——**幂等删除** ≈ `fs.rmSync(p, { force: true })`）

### 🟡 知道存在即可

- [ ] `@decorator` 是给函数/类加"框架标签"
- [ ] `async def` / `await` — 和 JS 差不多，目前不需要深究
- [ ] `yield` — lifespan 中用于分隔 startup 和 shutdown
- [ ] `SecretStr` — 保护 API Key 不泄露
- [ ] `model_dump()` — Pydantic 的对象转 dict 方法
- [ ] `Field(description=...)` — Pydantic 字段的元数据
- [ ] `Optional[X]` = `X | None`
- [ ] 变量标注（`x: Type = value`）——局部变量也能写，运行时完全不检查
- [ ] `dict.values()` + `list(...)`——`values()` 是"视图"不是列表，`list()` 转真列表
- [ ] `raise X from exc`（异常链：翻译异常的同时保留根因，traceback 里两者都可见）
- [ ] 按类型捕获异常 `except OSError` / `except UnicodeDecodeError`（≈ catch 分支的 instanceof 过滤；具体异常类型第一次进项目）
- [ ] `str(exc)`（异常对象转可读字符串，用于记录失败原因）
- [ ] `except Exception` 全收的场合（失败形态不可枚举、无需分流处理时——T0302/T0303 损坏 zip 的场景）
- [ ] `iter_rows(values_only=True)`（openpyxl 逐行生成器；values_only 给值不给 Cell 对象）
- [ ] openpyxl 直接收 `Path`（新一代库已支持 pathlib——对比 python-docx 需要 `str()` 桥接；⚠️ fitz 又需要桥接——各库不统一，不确定就 `str()` 一下）
- [ ] 模块级可变状态 + 访问器函数（`_OCR_WARNINGS` list + `get_ocr_warnings()` / `clear_ocr_warnings()`——模块当"穷人版单例"用；⚠️ 状态归谁清要看注释/契约）
- [ ] `time.sleep(seconds)` + `range(1, N+1)`（暂停执行等待退避；1-based 循环计数器——`for attempt in range(1, 4)` 数 1、2、3）
- [ ] `try/finally`（finally 无论成功、raise 还是 return 都执行——资源释放写这里；`doc.close()` 的保证）

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
| `...`（ellipsis） | 占位符——表示"实现由别人填"（⚠️ `vector_store.py` 真实代码未使用，方法体只有 docstring，见第 9 节"补充"） | `// TODO` 或空函数体 | T0101 |
| `*`（在参数列表中） | `*` 之后的参数必须用名字传参 | 无直接 TS 语法 | T0004 |
| `pass` | 空语句占位符 | 空的 `{}` | (Phase 0 未实际使用) |
| `Exception` | Python 所有异常的基类 | `Error` | T0004 |
| `raise` | 抛出异常 | `throw` | T0004 |
| `super()` | 调用父类方法 | `super` | T0004 |
| `logging` | Python 标准日志模块 | `console.log` / `winston` 等 | T0001 |
| `yield` | generator / context manager 暂停点 | 无直接类比 | T0001 |
| list comprehension（`[expr for x in xs]`） | 列表推导式——把每个元素变换成新列表 | `xs.map(x => expr)` | T0003（config.py 已出现，当时未记录）/ T0102 |
| `NotImplementedError` | 内置异常——"这方法还没实现"的占位标记 | `throw new Error("TODO")` | T0102 |
| `_name`（单下划线前缀） | 命名约定：私有属性，外部不要碰（无编译器强制） | `private`（但 TS 编译期强制） | T0102 |
| `in` / `not in` | 成员测试：元素在/不在容器里 | `list.includes(x)`（注意与 JS `in` 语义不同） | T0103 |
| `range(n)` | 生成 0 到 n-1 的整数序列 | 无内置等价；`Array.from({length: n}, (_, i) => i)` | T0105 |
| `for i in range(len(xs))` | 索引循环——按下标遍历 | `for (let i = 0; i < xs.length; i++)` | T0105 |
| `lambda x: expr` | 一次性匿名函数 | 箭头函数 `x => expr` | T0105 |
| `.sort(key=..., reverse=True)` | 按 key 函数取值排序；`reverse=True` 降序 | `arr.sort((a, b) => ...)`（思路不同） | T0105 |
| `.append(x)` | 往列表尾部添加元素 | `push(x)` | T0105 |
| `max(a, b)` / `min(a, b)` | 取较大 / 较小值 | `Math.max(a, b)` / `Math.min(a, b)` | T0105 |
| 变量标注（`x: Type = value`） | 给变量（含局部变量）写类型标注，运行时不检查 | `const x: Type = value` | T0107 |
| `dict.values()` | 取字典所有值的"视图"（不是列表，随 dict 动态变化） | `Object.values()`（但直接给数组） | T0107 |
| `list(...)` | 把可迭代对象转成列表 | `Array.from(...)` | T0107 |
| dict 聚合计数器模式 | dict 当 Map：首见初始化 + 每条累加（key 天然去重） | `Map` + `reduce` | T0107 |
| `@staticmethod` | 类里的静态方法：没有 `self`，不需要实例状态 | `static 方法名()` | T0108 |
| `TYPE_CHECKING` | 永远为 False 的常量——放进 `if TYPE_CHECKING:` 的 import 运行时不会执行，只给类型检查器看 | `import type` | T0201 |
| 字符串类型标注（`"TypeName"`） | 类型名写成字符串，运行时不解引用——不 import 也能标注 | `import type` 的另一半 | T0201 |
| `global` | 函数内声明"我要给模块级变量赋值"——Python 默认写创建局部变量 | JS 无需声明（赋值自动沿作用域链外找） | T0201 |
| 函数内 import（延迟 import） | import 写在函数体里，首次调用才执行；已导入的模块有全局缓存，不重复加载 | `await import()` | T0201 |
| `raise X from exc` | 异常链：抛新异常时保留原异常为根因（traceback 里两者都可见） | `throw new Error(msg, { cause: e })` | T0201 |
| `is` / `is None` | 身份比较：判断是不是同一个对象（None 是单例）；`==` 是值比较且可被重写 | `=== null` | T0201 |
| 真值判断（`if not chunks:`） | 空容器（空 list/dict/str）是假值；`not` 转布尔取反 | `if (!arr.length)`（⚠️ JS 里 `[]` 是真值！） | T0202 |
| numpy / `.tolist()` | numpy 是数值计算库；`model.encode()` 返回 numpy 数组，`.tolist()` 转 Python 原生 list | `Float32Array` → `Array.from()` / `[...f32]` | T0202 |
| `List[List[float]]` | 嵌套类型标注：外层 = 条数，内层 = 每条的维度 | `number[][]` | T0202（vector_store.py 先出现） |
| `Path` / `read_bytes()` | 路径对象；一次性读文件为 bytes（方法挂在路径对象上） | `node:path` + `fs.readFileSync`（返回 Buffer） | T0301 |
| `bytes` | 原始字节序列（0–255），Python 的"二进制"类型 | Node `Buffer` | T0301 |
| `str` vs `bytes` | 文本（Unicode 码点）vs 二进制（字节）；两种类型，`.decode()` / `.encode()` 互转 | `string` vs `Buffer` | T0301 |
| `.decode(encoding)` | bytes → str，按指定编码解码 | `buf.toString("utf-8")` | T0301 |
| `errors="strict"/"ignore"` | 解码遇非法字节：抛 UnicodeDecodeError / 静默丢弃 | `TextDecoder` 的 `fatal` 开关（strict ≈ fatal:true；ignore 无直接等价） | T0301 |
| `OSError` | 系统调用失败异常基类（文件不存在 / 权限不足等） | Node 系统错误（fs 回调的 err） | T0301 |
| `UnicodeDecodeError` | 按编码解码失败的异常（是 ValueError 子类） | fatal 模式下 TextDecoder 抛的错 | T0301 |
| `str(exc)` | 异常对象转可读字符串 | `${err.message}` | T0301 |
| `str(path)` | Path 对象转字符串路径——桥接只认 str 的老库 API（如 python-docx） | `url.href`（URL 转 string 喂老 API） | T0302 |
| 生成器表达式 `(x for x in y)` | 圆括号版列表推导：惰性、不造中间 list，常作函数参数 | iterator / `function*` + `yield` | T0302 |
| `str.splitlines()` | 按行边界切分——认 `\r\n` / `\r` / `\v` / `\f` / Unicode 行分隔符，且无末尾空串 | `text.split(/\r?\n/)`（splitlines 更强） | T0306 |
| `str.strip()` | 去首尾空白（含 `\t`、全角空格），不动行内 | `String.prototype.trim()` | T0304（`text.strip()` 判断）/ T0306（清洗） |
| `"sep".join(可迭代对象)` | 用分隔符连接（⚠️ 挂在字符串上，与 JS 的数组 join 方向相反） | `arr.join("sep")`（挂在数组上） | T0302 |
| `load_workbook` | openpyxl 的打开函数——读 xlsx 得到工作簿对象 | `XLSX.readFile()`（SheetJS） | T0303 |
| `iter_rows(values_only=True)` | 逐行读工作表：返回行元组的生成器；`values_only=True` 给单元格值而非 Cell 对象 | `sheet_to_json({header: 1})` 的逐行版 | T0303 |
| `is not None`（过滤空单元格） | 判断"没有值"用 `is not None`；⚠️ 不能用真值判断——`0` 是合法值且是假值 | `cell !== null`（JS 的 `0` 同样是 falsy，`if (cell)` 也误杀） | T0303 |
| `data_only=True` | 公式单元格返回上次保存的缓存值（无缓存 → None），而不是公式文本 `"=SUM(...)"` | 读"显示值"而不是"公式字符串" | T0303 |
| `str(cell)` 多类型统一 | 单元格值类型杂多（int/float/datetime/str/bool），str() 统一成文本 | `${value}` 模板串自动转 | T0303 |
| `try/except/else` | else 只在 try 无异常时执行；⚠️ **else 里的异常不被本层 except 捕获** | `try {} catch {}` + 成功分支写 try 外面（JS 无 else 子句） | T0305 |
| 回调函数参数（`Callable`） | 函数可以当参数传；`Callable[[Path, int], str]` = "吃 (Path, int)、吐 str 的函数" | `(p: string, n: number) => string` | T0304 |
| `isinstance(x, T)` | 运行时类型检查：x 是不是 T 的实例 | `typeof x === "object"` / `x instanceof T` | T0305 |
| `base64` 模块 | 二进制 ↔ Base64 文本编码（64 个安全字符，比二进制可传性更好） | `btoa()` / `atob()` | T0305 |
| `time.sleep(sec)` | 暂停当前线程 sec 秒（重试退避用） | `await sleep(ms)`（JS 无同步版，Python 有） | T0305 |
| 模块级状态 + 访问器函数 | 模块级 list 存状态 + get/clear 函数读写——"穷人版单例"（无 class 的状态容器） | module 级数组 + 导出函数 | T0305 |
| `try/finally` | finally 块无论成功、raise、return 都执行——资源释放的保证 | `try {} finally {}`（JS 同款） | T0304 |
| `uuid.uuid4()` | 生成随机 UUID4 对象（`str()` 转字符串）——UUID4 = 随机 128 位，全局唯一 | `crypto.randomUUID()`（直接返回 string） | T0307 |
| `enumerate(xs)` | 带下标遍历：产出 `(0, 元素0), (1, 元素1)...` 的惰性序列 | `xs.map((item, i) => ...)` 的 i / `xs.entries()` | T0307 |
| `.extend(可迭代对象)` | 把另一个序列的元素**摊开**加进列表（vs `.append(x)` 整个加一个） | `arr.push(...xs)` | T0307 |
| 元组 `(a, b)` | 圆括号的不可变序列；常作"键值对"常量表；支持解包 | `as const` 只读数组（无内置元组） | T0307（`(1.0, 2.0)` 先于 T0305 出现） |
| 字典字面量 `{"k": v}` | 造 dict 的字面量写法（key 要带引号）；列表推导里每轮造一个新 dict | JS 对象字面量（key 不用引号） | T0307 |
| `@classmethod` + `cls` | 类方法：第一个参数是**类本身**不是实例；`cls._parse(...)` 以类为命名空间调用 | static 方法里的类引用（≈ `this` 换成"类"） | T0308 |
| `datetime.now(timezone.utc).isoformat()` | UTC 当前时间的 ISO 8601 字符串——显式时区防跨服务器错乱 | `new Date().toISOString()` | T0308 |
| 关键字实参（keyword argument） | `fn(a=1, b=2)` 按**参数名**传值——长参数列表防顺序错误 | TS 的对象参数（JS 无原生具名实参） | T0308 |
| set 字面量 `{a, b}` | 花括号里没冒号 = set（无重复无序集合）；成员测试 `in` 是 O(1) | `new Set([...])` + `.has()` | T0308 |
| f-string `f"{x}"` | 字符串插值：前缀 `f`、花括号内嵌表达式 | JS 模板字符串 `` `${x}` `` | T0308 |
| `Path.unlink(missing_ok=True)` | 删除文件；`missing_ok=True` 时文件不存在也不抛错（幂等） | `fs.rmSync(p, { force: true })` | T0308 |

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
| `ABC` / `@abstractmethod` | T0101, T0102 | 知道定义 contract ≠ 实现功能；T0102 起知道实现侧规则（子类重写无需标记，实例化只查"是否定义"） |
| `async` / `await` | T0001 | 和 JS 差不多 |
| list comprehension | T0102 | `[x for x in y]` ≈ `.map()` |
| `NotImplementedError` 占位 stub | T0102 | 知道"方法存在 ≠ 功能可用" |
| `_name` 私有命名约定 | T0102 | 约定 + SPEC F008 硬性约束 |
| `in` / `not in` 成员测试 | T0103 | ≈ `includes()`；注意 JS `in` 查属性、Python `in` 查元素 |
| `range()` 索引循环 | T0105 | ≈ 经典三段式 for 循环；区分"遍历元素"与"遍历下标" |
| `lambda` + `sort(key=...)` | T0105 | key 函数 ≈ 箭头函数；排序思路 ≈ lodash `sortBy` |
| `.append()` / `max()` / `min()` | T0105 | ≈ push / Math.max / Math.min，几乎零成本 |
| 变量标注 + `dict.values()` + `list()` | T0107 | 局部变量标注运行时无效果；`values()` 是视图，要 `list()` 转真列表 |
| dict 聚合计数器模式 | T0107 | ≈ Map + reduce；key 天然去重、首见初始化 + 累加 |
| dict 按键取值 `d["key"]` | T0104 | 方括号是按键取值，不是数组下标；键不存在抛 KeyError（JS 返回 undefined） |
| `@staticmethod` | T0108 | = static 方法：无 self、不碰实例状态；项目首个（`_to_chunk_records`） |
| `try / except` | T0201 | 提前出现（原预计 Phase 3+）：`except Exception` 捕获一切常规异常 ≈ `catch (e)` |
| `TYPE_CHECKING` + 字符串类型标注 | T0201 | ≈ `import type`：重依赖（sentence_transformers）运行时零成本 |
| 函数内 import | T0201 | ≈ `await import()`：首次调用才真正加载重依赖；模块全局缓存保证只执行一次 |
| `global` | T0201 | 函数内给模块级变量赋值必须声明；删掉不报错但单例静默失效 |
| `raise ... from exc` | T0201 | ≈ `{ cause: e }`：翻译成 AppError 的同时保留底层根因 |
| `is None` 身份比较 | T0201 | ≈ `=== null`：判断空值用 `is` 不用 `==`（`==` 可被重写） |
| 真值判断 `if not chunks` | T0202 | ⚠️ JS 里 `[]` 是真值——Python 空容器是假值，照抄 `!chunks` 会出 bug |
| numpy 数组 + `.tolist()` | T0202 | ≈ `Float32Array` → `Array.from()`：numpy float32 ≠ Python float，跨边界必须转 |
| `List[List[float]]` 嵌套标注 | T0202 | ≈ `number[][]`：外层条数、内层维度（vector_store.py 先出现，T0202 成为生产者） |
| `Path` + `read_bytes()` | T0301 | 路径对象 ≈ node:path；一次性读文件 ≈ fs.readFileSync |
| `bytes` / `str` / `.decode()` | T0301 | Python 二进制与文本是两种类型；JS string 无编码概念、Buffer 对应 bytes |
| 解码错误策略 strict / ignore | T0301 | ≈ TextDecoder 的 fatal 开关；ignore 比 replace 更激进（直接丢字节，连 � 都不留） |
| 按类型捕获异常 + `str(exc)` | T0301 | except 分支 ≈ catch 的 instanceof 过滤；异常对象可转字符串（记录失败原因） |
| 编码级联策略（项目设计） | T0301 | 顺序尝试：UTF-8 strict → UTF-16 strict → GBK ignore；严格打前站防乱码、宽松兜底保内容 |
| `str(path)` 桥接老库 API | T0302 | Path → 字符串；老库（python-docx）只认 str 路径 |
| 生成器表达式 | T0302 | ≈ 惰性 iterator；只作函数参数时用，存变量用列表推导 |
| str.splitlines() | T0306 | 行感知 split；`split('\n')` 的升级版 |
| str.strip() | T0304 | ≈ trim()；T0306 在清洗管道中正式出场 |
| 管道式重赋值（`lines = ...; lines = ...`） | T0306 | 列表推导流水线惯用法 |
| uuid.uuid4() | T0307 | ≈ crypto.randomUUID()；注意 `str()` 转换 |
| enumerate() | T0307 | 带下标遍历；chunk_index 的 0-based 来源 |
| .extend() vs .append() | T0307 | 加一筐 vs 加一个；嵌套 list 的坑 |
| 元组 + 解包 | T0307 | 键值对常量表（`(1.0, 2.0)` 在 T0305 就见过） |
| 字典字面量 | T0307 | 造 dict 的基本写法；"位置决定共享" |
| `@classmethod` | T0308 | = static 方法里的类引用（`cls` ≈ 类名本身）；与 `@staticmethod` 并存——用到类引用就 classmethod，用不到就 staticmethod |
| datetime + timezone（UTC 时间戳） | T0308 | ≈ `new Date().toISOString()`；`timezone.utc` 显式声明时区——upload_time 取一次全文件共享 |
| 关键字实参 | T0308 | 按参数名传值（`chunk_text(..., file_id=file_id)`）；长参数列表防顺序错误 |
| set + 成员测试 | T0308 | ≈ `Set` + `.has()`；扩展名分发用 set（O(1) 成员测试） |
| f-string | T0308 | ≈ JS 模板字符串——**预言兑现**（"尚未遇到"表曾预言它还没出现） |
| `Path.unlink(missing_ok=True)` | T0308 | 幂等删除——FAILED 回滚的原子性基础 |
| `"sep".join(...)` | T0302 | ⚠️ 与 JS 方向相反——分隔符.join(可迭代对象) |
| `except Exception` 全收的场合 | T0302 | 失败形态不可枚举、无分流需求时全收 + `from exc` 保根因（vs T0301 按类型分流） |
| 第三方库对象模型（python-docx） | T0302 | doc.paragraphs / table.rows / cell.text 属性链；库挡住 zip+XML |
| `is not None` 过滤 | T0303 | ⚠️ `0` 是合法值且假值——过滤"没有值"必须 `is not None`，不能真值判断 |
| 带过滤条件的生成器表达式 | T0303 | 过滤作用于原始元素（先过滤后转换）；T0302 的 20.7 进阶形态 |
| `data_only=True` 公式语义 | T0303 | 读缓存值不读公式文本；机器生成文件无缓存 → None → 被跳过 |
| `iter_rows(values_only=True)` + `load_workbook` | T0303 | openpyxl 逐行生成器；库函数名需要时查文档即可 |
| `str(cell)` 多类型统一 | T0303 | 单元格值 int/float/datetime/str 杂多，str() 统一（20.8 预防针兑现） |
| `try/except/else` | T0305 | ⚠️ else 里的异常不被本层 except 捕获——AUTH_FAILED 靠这个穿透重试循环；JS 无 else 子句（成功分支写 try 外） |
| 回调函数参数 + `Callable` 标注 | T0304 | ≈ TS 传 callback；`Optional[Callable[[Path, int], str]]` = 可选的 (Path, int) → str 函数 |
| `isinstance(x, T)` | T0305 | 运行时类型检查 ≈ `x instanceof T`；防御外部 API 不可信数据（200 响应也过滤） |
| `base64` 模块 | T0305 | ≈ `btoa()`；二进制 → Base64 文本；`.decode("ascii")` 安全（Base64 只含 ASCII） |
| `time.sleep(sec)` | T0305 | 退避等待；⚠️ Python 是同步阻塞（JS 要 await，Python 直接睡） |
| 模块级状态 + 访问器函数 | T0305 | 模块级 list + get/clear = "穷人版单例"；⚠️ 状态归谁清看注释（T0308 负责） |
| `try/finally` | T0304 | finally 无论成败都执行——`doc.close()` 的保证；JS 同款 |
| 虚拟环境 / pip / requirements.txt | T0001 | 知道基本命令 |

### 正在建立理解（🟡）

| 知识 | 需要结合哪些后续代码 |
|------|-------------------|
| FastAPI Request → Response 完整生命周期 | T0102+ 的 endpoint 实现 |
| Pydantic 的运行时验证如何被 FastAPI 触发 | T0401+ 的第一个 API endpoint |
| `yield` / context manager | Phase 3 出现具体 startup / 文件操作逻辑时（T0301 文件操作用了 `read_bytes()`，仍未用到） |
| Python 的 import 搜索路径问题排查 | 首次遇到 `ModuleNotFoundError` 时 |

### 尚未遇到

| 未来会出现的 Python 概念 | 预期出现的 Task |
|------------------------|---------------|
| `with` 语句 (context manager) | T0304/T0305 用 `try/finally` 实现了等价效果（`doc.close()`）；仍未用 `with`——`fitz.open()` 支持 with 语法，实现选择了 try/finally（两者等价，项目第一次显式管理资源） |
| Generator / `yield from` | 生成器表达式已出现（T0302 作 join 参数、T0303 带过滤条件）；`yield` 语句 / 生成器函数仍未出现（iter_rows 内部用，项目代码未写） |
| TypeVar / Generic | 如需泛型抽象 |
| Dataclass | 如需轻量数据容器 |
| ~~f-string（`f"{x}"` 字符串插值）~~ | ✅ **预言兑现**：T0308 的 `f"uploads/{collection_name}/{file_name}"` 是项目第一个 f-string（已移入"已经接触"） |

---

---

## 17. T0102 新增 Python 知识

> 本节按 Task 顺序增量记录 vector_store.py 中出现的 Python 知识（T0102 起，每次 Learning Pass 追加）。每条按"Python 写法 → 怎么读 → TS 类比 → 重要差异 → DX-RAG 使用位置"展开。

### 17.1 list comprehension（列表推导式）

**Python 写法**（真实代码：[vector_store.py:281](backend/app/core/vector_store.py#L297)）：

```python
return [col.name for col in self._client.list_collections()]
```

**怎么读**：对 `self._client.list_collections()` 返回的每个 `col`，取出 `col.name`，组成一个新的列表返回。公式：`[表达式 for 变量 in 可迭代对象]`。

**TypeScript / Node.js 类比**：

```ts
return this.client.listCollections().map(col => col.name);
```

**重要差异**：TS 用方法 `.map()`；Python 用语法（写进方括号里）。两者都是"把每个元素变换成另一个值"。Python 也有 `map()` 函数，但社区惯用 list comprehension，DX-RAG 也用这一种。

**DX-RAG T0102 中在哪里使用**：`list_collections()` 把 ChromaDB 返回的 Collection 对象列表"翻译"成契约要求的 `List[str]`——剥掉 SDK 对象，只留业务要的名字。

> 补充：Phase 0 的 config.py（`parse_cors_origins` 里 `[str(item) for item in v]`）其实已经出现过 list comprehension，当时没有单独讲。T0102 是它第一次出现在 vector_store.py 的核心逻辑里，现在补上。

### 17.2 `raise NotImplementedError` —— 占位 stub

**Python 写法**（真实代码，T0102 完成时：[vector_store.py:285-286](backend/app/core/vector_store.py#L301-L302)）：

```python
def rename_collection(self, old_name: str, new_name: str) -> None:
    raise NotImplementedError("rename_collection → T0103")
```

**怎么读**：抛出一个内置异常 `NotImplementedError`，消息写明"这个功能属于 T0103"。任何代码调用这个方法都会立刻崩溃——**这是故意的**：宁可崩，也不假装做成了。

**TypeScript / Node.js 类比**：

```ts
renameCollection(oldName: string, newName: string): void {
  throw new Error("Not implemented — TODO T0103");
}
```

**重要差异**：`raise` 在第 10 节已学过（≈ `throw`）。新的知识点是 `NotImplementedError` 这个**专门的内置异常**——Python 生态标记"未完成方法"的标准做法，而不是用普通 `Exception` 或静默 `return`。读代码的人一眼就能分辨"这是没写完的占位"。

**DX-RAG T0102 中在哪里使用**：[vector_store.py:285-318](backend/app/core/vector_store.py#L301-L334) —— 当时 8 个尚未实现的方法（rename→T0103、add_texts→T0104、search→T0105 等）全部是这种 stub。T0103–T0108 每完成一个，就把对应方法的 `raise` 换成真实实现。

> 更新：`rename_collection` 已由 T0103 实现（现第 284–301 行），`add_texts` / `search` 已由 T0104 / T0105 实现，其余 5 个由 T0106–T0108 全部实现。**占位阶段已结束**——当前代码里已没有任何 `NotImplementedError` stub（11/11 全部真实）。这个片段现在只有历史教学价值。

### 17.3 `_name` —— 单下划线私有约定

**Python 写法**（真实代码：[vector_store.py:250-252](backend/app/core/vector_store.py#L266-L268)）：

```python
def __init__(self) -> None:
    self._client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR
    )
```

**怎么读**：实例属性名 `_client` 开头加一个下划线。含义是**约定**："这是类的内部实现细节，外部代码不要碰"。

**TypeScript / Node.js 类比**：TS 的 `private client`。

**重要差异**：TS 的 `private` 是**编译期强制**的——外部访问直接编译报错；Python 的 `_` 只是命名约定，运行时外部照样能 `store._client`，Python 不会阻止你，约束来自社区约定和代码审查。在 DX-RAG 里它被**升级为项目法律**：SPEC F008 约束 3 明文"禁止外部代码访问 `_collection` 或任何 ChromaDB 私有属性"，还有 AC-F008-03 专门验收。

**DX-RAG T0102 中在哪里使用**：`self._client` 是 `ChromaVectorStore` 与 ChromaDB SDK 之间的唯一通道——SDK 对象从生到死只活在这个类内部。

### 17.4 ABC 实现侧（T0102 新用法）

> **去重说明（Phase 1 Learning Review）**：本条目与第 9 节"T0102 补充：ABC 的实现侧（子类怎么写）"内容重复——那里已有同一段真实代码（`ChromaVectorStore.create_collection`）和两个关键认知（检查时机：实例化时 vs TS 编译期；只查"有没有定义"，不查"有没有真实逻辑"）。**完整内容见第 9 节，这里只保留 17.x 系列的索引位置。**

**一句话**：子类重写抽象方法**不需要**任何装饰器或 `override` 标记——父类标过一次 `@abstractmethod`，子类直接写同名方法就算"实现"。

**DX-RAG 进度**：`ChromaVectorStore` 是项目中第一个 ABC 实现类（T0102 时 3 真实 + 8 占位；T0103 起 4 + 7；T0104 起 5 + 6；T0105 起 6 + 5；T0106 起 7 + 4；T0107 起 8 + 3；**T0108 起 11 + 0，占位阶段结束**）。

### 17.5 `in` / `not in` —— 成员测试运算符

**Python 写法**（真实代码：[vector_store.py:299](backend/app/core/vector_store.py#L315)）：

```python
if old_name not in self.list_collections():
    raise AppError("COLLECTION_NOT_FOUND")
```

**怎么读**：`x in 容器` 问"x 在不在这个容器里"，`not in` 是它的否定形式。这里的含义："如果旧名字**不在**已有知识库名字列表里"。

**TypeScript / Node.js 类比**：

```ts
if (!this.listCollections().includes(oldName)) {
  throw new AppError("COLLECTION_NOT_FOUND");
}
```

**重要差异**：JS 也有 `in` 运算符，但语义**不同**——JS 的 `'key' in obj` 检查的是对象**属性**是否存在；Python 的 `x in list` 检查的是**元素**是否属于容器。所以对应 `x in list` 的正确 JS 是 `list.includes(x)`，而不是 `x in list`（那在 JS 里检查的是数组下标/属性名）。另外 Python 的 `in` 还能用于：

- 字符串：`"ab" in "abc"` → 子串判断（≈ JS `"abc".includes("ab")`）
- dict：`"name" in obj` → 查 key 是否存在（≈ JS `"name" in obj` 或 `hasOwnProperty`）

Python 没有 `!in` 这种写法——否定就用 `not in` 一个整体运算符。

**DX-RAG T0103 中在哪里使用**：`rename_collection` 的校验行——旧名字不在知识库列表里就抛 `COLLECTION_NOT_FOUND`。这是 T0103 三行结构的第 1 行（校验 → 抛错 → 改名）。

### 17.6 `range()` + `for i in range(len(x))` —— 索引循环

**Python 写法**（真实代码：[vector_store.py:369](backend/app/core/vector_store.py#L385)）：

```python
for i in range(len(raw["ids"][0])):
    metadata = raw["metadatas"][0][i]
    distance = raw["distances"][0][i]
```

**怎么读**：`len(...)` 先取列表长度，`range(n)` 生成从 0 到 n-1 的整数序列，`for i in ...` 逐个把整数放进变量 `i`。循环体里用 `[i]` 按下标访问列表——所以叫"索引循环"。

**TypeScript / Node.js 类比**：

```ts
for (let i = 0; i < raw.ids[0].length; i++) {
  const metadata = raw.metadatas[0][i];
  const distance = raw.distances[0][i];
}
```

几乎逐行等价。JS 没有内置 `range()`——需要的话要自己写 `Array.from({ length: n }, (_, i) => i)`。

**重要差异**：Python 的 `for` 默认是"直接给元素"（`for x in list` ≈ `for (const x of list)`），`range()` 是特例：它给的是"整数"。所以：

- `for x in xs:` → 遍历元素（≈ for-of）
- `for i in range(len(xs)):` → 遍历下标（≈ 经典三段式 for）

什么时候必须用第二种？**一个循环里要按同一个下标访问多个列表**时。T0105 的 search 循环就是典型：一个结果要从 ids / metadatas / distances / documents 四个数组的**同一个下标**取四样东西——不按下标就没办法把四个数组"缝"到一起。

**DX-RAG T0105 中在哪里使用**：`search()` 的转换循环（第 369 行）——把 ChromaDB 返回的四组平行数组翻译成一条条 `VectorSearchResult`。

### 17.7 `lambda` + `sort(key=..., reverse=True)` —— key 函数排序

**Python 写法**（真实代码：[vector_store.py:382](backend/app/core/vector_store.py#L398)）：

```python
results.sort(key=lambda r: r.similarity_score, reverse=True)
```

**怎么读**：`sort` 按"每个元素的哪个值"来比较大小——`key=` 参数回答这个问题：`lambda r: r.similarity_score` 是一个一次性小函数，"给我一个结果 r，我返回它的 similarity_score"。`reverse=True` 表示降序。整行读作："按 similarity_score 从大到小排好。"

**TypeScript / Node.js 类比**：

```ts
results.sort((a, b) => b.similarityScore - a.similarityScore);
```

**重要差异**：两种排序 API 的思路完全不同：

| | TS comparator | Python key 函数 |
|---|---|---|
| 你告诉它 | a、b 两个元素谁前谁后（返回差值） | 每个元素"用什么值比大小" |
| 升降序 | 自己通过 `b - a` / `a - b` 控制 | 交给 `reverse=True/False` 一个开关 |
| 更接近 | —— | lodash 的 `_.sortBy(results, r => r.similarityScore)` 再 `reverse` |

另外两点：

1. `lambda x: 表达式` 就是 Python 的匿名函数，≈ 箭头函数 `x => 表达式`。它只能写一个表达式（不能多行），所以项目里常见的 lambda 都是这种"取字段"的一行函数。
2. `.sort()` 是**原地排序**（直接改列表、返回 `None`）——这点和 JS 的 `Array.prototype.sort()` 一致。

**DX-RAG T0105 中在哪里使用**：`search()` 最后一行——把检索结果按相似度降序排好，兑现契约"sorted by similarity_score descending"（不依赖 ChromaDB 的返回顺序）。

### 17.8 附带出现的小件：`.append()` / `max()` / `min()`

这三个在 T0105 的转换循环里一起出现，对 JS 开发者几乎零成本，不展开：

| Python | 等价 JS | DX-RAG 位置 |
|--------|--------|------------|
| `results.append(x)` | `results.push(x)` | [vector_store.py:372](backend/app/core/vector_store.py#L388) |
| `max(a, b)` / `min(a, b)` | `Math.max(a, b)` / `Math.min(a, b)` | [vector_store.py:378](backend/app/core/vector_store.py#L394) |

> 值得记的唯一组合拳：`max(0.0, min(1.0, x))` = 把 x 夹到 [0, 1] 区间（clamp）——和 JS 的 `Math.max(0, Math.min(1, x))` 一模一样，只是函数名少了 `Math.` 前缀。

---

### 17.9 `@staticmethod` —— 没有 self 的类方法

**Python 写法**（真实代码：[vector_store.py:436-437](backend/app/core/vector_store.py#L452-L453)）：

```python
@staticmethod
def _to_chunk_records(got: Dict[str, Any]) -> List[ChunkRecord]:
    """Map ChromaDB get() output to ChunkRecord list (no embeddings)."""
    ...
```

**怎么读**：`@staticmethod` 装饰器声明"这个方法**没有 `self`**"。它不碰实例状态（不用 `self._client`），本质上是一个**住在类里的普通函数**——只做"入参 → 出参"的纯翻译。调用时 `self._to_chunk_records(...)` 和 `ChromaVectorStore._to_chunk_records(...)` 都可以。

**TypeScript / Node.js 类比**：

```ts
private static toChunkRecords(got: ...): ChunkRecord[] { ... }
```

**重要差异**：TS 用 `static` 关键字标记；Python 用装饰器标记——因为 Python 的"普通方法"默认自带 self，需要装饰器把 self"剥掉"。别和 `@classmethod` 混（classmethod 拿到的是类本身 `cls`）——项目还没用到，遇到再学。

**DX-RAG T0108 中在哪里使用**：`_to_chunk_records` 是项目**第一个 static 方法**——`list_chunks` 和 `get_chunks_by_file` 都要做"get() 输出 → ChunkRecord"翻译，抽出来避免写两遍（DRY）。

### 17.10 变量标注（variable annotation）—— 局部变量也能写类型

**Python 写法**（真实代码：[vector_store.py:417](backend/app/core/vector_store.py#L433)）：

```python
files: Dict[str, Dict[str, Any]] = {}
```

**怎么读**：`名字: 类型 = 值`——给**局部变量**写类型标注（Python 3.6+）。运行时**什么都不检查**，纯粹给人和工具（IDE 补全、mypy）看。`Dict[str, Dict[str, Any]]` 逐层读："str 为 key、任意 dict 为 value 的字典"——嵌套类型标注第一次出现。

**TypeScript / Node.js 类比**：`const files: Map<string, Record<string, any>> = new Map()`。

**重要差异**：之前项目里的 type hints 都在**函数签名**（参数、返回值）和**模型字段**上；这次出现在局部变量上。认知统一：Python 的标注体系（函数参数、返回值、局部变量）都是"注释性质"，运行时一律不检查——TS 是编译期强制，这是两者的根本区别。

**DX-RAG T0107 中在哪里使用**：`get_files` 的聚合容器——标注帮读者一眼看出"这是 file_id → 文件记录的映射"。

### 17.11 `dict.values()` + `list()` —— 视图转列表；聚合计数器模式

**Python 写法**（真实代码：[vector_store.py:417-432](backend/app/core/vector_store.py#L433-L448)，节选）：

```python
files: Dict[str, Dict[str, Any]] = {}
for meta in metadatas:
    fid = meta["file_id"]
    if fid not in files:
        files[fid] = {"file_id": fid, ..., "chunk_count": 0}
    files[fid]["chunk_count"] += 1
return list(files.values())
```

**怎么读**（三个知识点叠在一起）：

1. **dict 当 Map 用**：key = file_id，value = 文件记录。dict 的 key 天然唯一 → **去重靠数据结构**，不用写显式去重逻辑。
2. **计数器模式**：`if fid not in files` 检查 key 是否首见（`in` 用在 dict 上查 key，第 17.5 节）；首见就建记录（chunk_count=0），之后每条 chunk 都执行 `files[fid]["chunk_count"] += 1`（两层取值后自增）。
3. **`list(files.values())`**：`.values()` 返回"**视图**"（view）——一个随 dict 动态变化的窗口对象，**不是列表**（不能索引、不是 `List[Dict]`）。契约要求返回 `List[Dict[str, Any]]`，必须用 `list(...)` 把它转成真列表。

**TypeScript / Node.js 类比**：

```ts
const files = new Map<string, FileRecord>();
for (const meta of metadatas) {
  if (!files.has(meta.file_id)) {
    files.set(meta.file_id, { ..., chunkCount: 0 });
  }
  files.get(meta.file_id)!.chunkCount += 1;
}
return [...files.values()];   // 注意 TS 这里是展开运算符，Python 是 list()
```

**重要差异**：JS 的 `Object.values()` **直接返回数组**；Python 的 `dict.values()` 返回**视图**——必须 `list()` 包一层才是真列表。TS 里 `files.get(...)!` 的非空断言（Map 的 get 可能返回 undefined）在 Python 里不存在——因为 `files[fid]` 此时一定存在（刚建过）。

**DX-RAG T0107 中在哪里使用**：`get_files` 的整段聚合——这是 SPEC 7.3 "无外部 metadata 数据库"的落地：文件列表不是查表查出来的，是对 chunk metadata 按 file_id **聚合 + 计数**算出来的（单遍 O(n)）。

### 17.12 dict 按键取值 `d["key"]`（T0104 起反复出现；Phase 1 Learning Review 补记）

**Python 写法**（真实代码：[vector_store.py:331](../../backend/app/core/vector_store.py#L347)）：

```python
ids = [meta["chunk_id"] for meta in metadatas]
```

**怎么读**：`meta["chunk_id"]` 的方括号**不是数组下标**——是**按键取值**（≈ `meta.chunk_id`）。Python 的 dict 没有"属性名即键名"的语法糖，必须显式写 `["键名"]`。

**TypeScript / Node.js 类比**：TS 里 `obj.key` 和 `obj["key"]` 两种写法都行；Python 只有 `obj["key"]`（`obj.key` 是属性访问，dict 没有这个属性）。

**重要差异**：键不存在时 Python 抛 `KeyError`（当场炸）；JS 返回 `undefined`（炸在下一行）。Python 的报错更早更直接。

**DX-RAG 中在哪里使用**：`add_texts` 提取 ids（[vector_store.py:331](../../backend/app/core/vector_store.py#L347)）；`search` 三层取值 `raw["ids"][0][i]`（结构见 phase-01-vectorstore.md 第 66 节）；`get_files` 的 `files[fid]["chunk_count"] += 1`（两层取值后自增，17.11）。首次完整讲解在 phase-01-vectorstore.md 第 51 节。

---

> **Phase 1 收官**：T0106–T0108 的知识已记录在上方（17.9–17.11）；17.12 为 Phase 1 Learning Review 补记（dict 按键取值）。本次 Review 还做了两处去重/修正：17.4 压缩为指向第 9 节"T0102 补充"的索引条目；修正第 2/12 节中"抽象方法体是 `...`"与真实代码不符的描述（真实代码为 docstring-only）。下一步学习 Phase 2（T0201/T0202 Embedding）——届时 `add_texts` 的 embeddings 参数将不再由调用方提供，而是 EmbeddingService 生成；预计将遇到模型加载相关的 Python 知识（如 `with` 语句、文件操作），届时更新此文档。

---

## 18. T0201 新增 Python 知识

> 本节按 Task 顺序增量记录 embedding.py 中出现的 Python 知识（T0201，每次 Learning Pass 追加）。格式同第 17 节：Python 写法 → 怎么读 → TS 类比 → 重要差异 → DX-RAG 使用位置。完整讲解见 [phase-02-embedding.md](./phase-02-embedding.md) 第 3 节。

### 18.1 `TYPE_CHECKING` + 字符串类型标注 —— 重依赖的"假 import"

**Python 写法**（真实代码：[embedding.py:23-24](../../backend/app/services/embedding.py#L39-L40) + [embedding.py:28](../../backend/app/services/embedding.py#L44)）：

```python
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_model: Optional["SentenceTransformer"] = None
```

**怎么读**：`TYPE_CHECKING` 是 Python 官方提供的常量，**永远为 False**——`if TYPE_CHECKING:` 里的 import 在运行时**不会执行**，只在 IDE / 类型检查器（mypy）分析时"假装执行"。第 27 行的 `"SentenceTransformer"` 用**字符串**写类型名，运行时同样不解引用这个类型，因此不需要真的 import 它。

**TypeScript / Node.js 类比**：`import type { SentenceTransformer } from "sentence-transformers"`——TS 的 `import type` 编译后完全消失，只给类型系统看。两者语义几乎完全相同。

**重要差异**：JS/TS 没有"import 要几秒钟"的顾虑（Node 的 require 会同步加载模块，但 JS 包普遍轻）；Python 里 `import sentence_transformers` 会连带加载 torch，可能耗时数秒甚至更久——所以 Python 生态里有"能不用顶部 import 就不用"的讲究，JS 生态里这种顾虑弱得多。

**DX-RAG 中在哪里使用**：`embedding.py` 全文。效果 = 任何代码 `from app.services.embedding import get_model` 都轻量无副作用；环境没装 sentence_transformers 时，import 本模块也不会崩（真正的 import 推迟到 get_model 首次调用，见 18.2）。

### 18.2 函数内 import —— 延迟 import

**Python 写法**（真实代码：[embedding.py:49-50](../../backend/app/services/embedding.py#L65-L66)）：

```python
def get_model() -> "SentenceTransformer":
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(settings.EMBED_MODEL)
```

**怎么读**：import 语句写在**函数体里**而不是文件顶部——Python 的 import 可以出现在任何位置，首次执行到这一行时才真正加载该模块。已加载的模块会被 `sys.modules` 全局缓存，**重复执行这行 import 几乎零开销**（不会重新加载）。

**TypeScript / Node.js 类比**：`const { SentenceTransformer } = await import("sentence-transformers")`——动态 import，把加载推迟到真正需要的时候。Node 里 `require()` 也有模块缓存（`require.cache`），重复 require 不重复执行，与 `sys.modules` 对应。

**重要差异**：Python 的普通 import 是**语句**（不是表达式），不能 `x = import ...`；TS 的动态 import 是**表达式**（返回 Promise），可以赋给变量、传给函数。

**DX-RAG 中在哪里使用**：`get_model()` 内——与 18.1 是同一策略的两个层次（模块 import 时零成本 + 首次调用时才加载）。Phase 1 的 `vector_store.py` 顶部直接 `import chromadb`，因为 chromadb 相对轻且 Phase 1 所有方法都用它；embedding 的依赖重且可能不被调用，所以用延迟策略。

### 18.3 `global` 关键字 —— 赋值默认是局部的

**Python 写法**（真实代码：[embedding.py:47-48](../../backend/app/services/embedding.py#L63-L64)）：

```python
_model: Optional["SentenceTransformer"] = None  # 模块级（第 28 行）

def get_model() -> "SentenceTransformer":
    global _model
    if _model is None:
        ...
        _model = SentenceTransformer(settings.EMBED_MODEL)
    return _model
```

**怎么读**：Python 作用域规则是"**读自动向外找，写默认局部**"——函数里给名字**赋值**，默认创建同名局部变量，除非声明 `global`。`global _model` 声明"下面的 `_model = ...` 作用于模块级那个变量"。

**TypeScript / Node.js 类比**：JS 不需要任何声明——函数内 `model = ...` 会自动沿作用域链找到外层变量赋值（除非用 `let`/`const` 遮蔽）。这正是 Python 与 JS 的一个经典差异点。

**重要差异**（必背）：

- **删掉 `global _model` 不会报错**——只会静默创建局部变量：模块级 `_model` 永远是 None，**每次调用都重新加载模型**，单例静默失效（这正是 T0201 自测题第 4 题的答案）。
- **读取不需要 `global`**：`return _model` 读的是模块级变量（读自动向外找）。只有赋值才需要声明。

**DX-RAG 中在哪里使用**：`embedding.py` 的 `get_model()`——模块级单例模式的赋值关键。本项目第二次出现模块级单例（第一次是 `config.py` 的 `settings = Settings()`），但 config 的赋值发生在模块顶层（不需要 global），embedding 的赋值发生在函数内（必须 global）——对照这两处就能记住规则。

### 18.4 `raise ... from exc` —— 异常链

**Python 写法**（真实代码：[embedding.py:53-54](../../backend/app/services/embedding.py#L69-L70)）：

```python
        except Exception as exc:
            raise AppError("EMBEDDING_MODEL_ERROR") from exc
```

**怎么读**：`except Exception as exc` 捕获一切常规异常（`Exception` 是所有内置异常的父类，≈ JS 的 `catch (e)` 不加过滤）；`raise AppError(...) from exc` 抛出新异常，同时把 `exc` 设为新异常的 `__cause__`（根因）——traceback 里两个异常都完整可见。

**TypeScript / Node.js 类比**：`throw new AppError("EMBEDDING_MODEL_ERROR", { cause: e })`（ES2022 的 `cause` 选项）——语义几乎相同：对外抛语义化错误，对内保留底层根因。

**重要差异**：

- Python 的 `from exc` 是**语法**，JS 的 `{ cause: e }` 是**构造参数**；Python 任何 `raise` 都可以加 `from`，JS 只有手动传 cause。
- 不写 `from exc` 也不报错：Python 会隐式建立异常链，但 traceback 显示为"在处理异常时又发生异常"（`During handling of the above exception...`），可读性差——**规范写法是显式 `from`**。
- 还有一个少见变体 `raise X from None`：显式**切断**异常链（"根因无关紧要，别显示"）。T0201 未使用。

**DX-RAG 中在哪里使用**：`get_model()` 的加载失败翻译——底层库的任意异常（路径不存在 / 文件损坏 / OOM / 下载失败）统一翻译为 `AppError("EMBEDDING_MODEL_ERROR")`（HTTP 500），根因经 `from exc` 保留在服务端 traceback 中（对外响应 details 为空，不泄露内部细节）。Phase 1 的 `rename_collection` 也 raise AppError 但没有底层异常可链（是主动校验），所以 T0201 是项目里 `from exc` 的首秀。

---

### 18.5 `is None` —— 身份比较

**Python 写法**（真实代码：[embedding.py:48](../../backend/app/services/embedding.py#L64)）：

```python
    if _model is None:
```

**怎么读**：`is` 做**身份比较**——判断左右两边是不是**同一个对象**；`==` 做**值比较**——判断两边**相等**。`None` 是 Python 里唯一的 NoneType 实例（单例），所以 `x is None` 是判断"是空"的官方推荐写法。

**TypeScript / Node.js 类比**：`value === null`。JS 里 `===` 对原始值/对象引用做同一性比较，`null` 同样只有一个实例——语义几乎相同；JS 的 `== null` 则会连带匹配 `undefined`（宽松相等），与 Python 的 `== None` 不同（Python `==` 不宽松）。

**重要差异**：Python 的 `==` 可以被类**重写**（`__eq__` 方法）——某些对象可能"等于 None 却不 is None"（罕见但存在）；`is` 永远不能被重写。所以判断空值用 `is None` 而不是 `== None` 是社区共识。

**DX-RAG 中在哪里使用**：`get_model()` 的单例开关——"缓存是否还是空的"用身份判断最干净。Phase 1 的代码没有用到 `is None`（判断用过 `if count > 0`、`if fid not in files`），T0201 是首次出现。

---

> **T0201 收官**：18.1–18.5 为 T0201 新增知识（TYPE_CHECKING、函数内 import、global、raise from、is None）。`try / except` 提前在 T0201 出现（第 16 节"尚未遇到"已移除）。预计 T0202 将出现 numpy 数组 `.tolist()`、`List[List[float]]` 嵌套类型标注等——届时更新此文档。

---

## 19. T0202 新增 Python 知识

> 本节记录 encode_chunks 中出现的 Python 知识（T0202）。格式同第 17/18 节。完整讲解见 [phase-02-embedding.md](./phase-02-embedding.md) 第 13–14 节。

### 19.1 真值判断 `if not chunks:` —— 空容器是假值

**Python 写法**（真实代码：[embedding.py:75-76](../../backend/app/services/embedding.py#L91-L92)）：

```python
    if not chunks:
        return []
```

**怎么读**：`not x` 先把 x 转成布尔再取反。Python 的**真值规则**：空容器（空 list / dict / str / set / tuple）、`None`、`0`、`False` 都是**假值（falsy）**；其余是真值。所以 `if not chunks:` = "如果列表为空"。

**TypeScript / Node.js 类比**：`if (!arr.length) return [];`。⚠️ **关键差异**：JS 里空数组 `[]` 是 **truthy**——`if (!chunks)` 对空数组永远不进分支（bug！）。JS 必须显式查 `.length`，Python 直接 `not 容器`。这是两者最经典的真值差异之一。

**重要差异**（必背）：Python 的假值集合 = `None` / `False` / `0` / 空容器 / 空字符串；JS 的 falsy 集合 = `null` / `undefined` / `false` / `0` / `NaN` / `""`——**JS 的空数组和空对象都是 truthy**。

**DX-RAG 中在哪里使用**：`encode_chunks` 的空输入短路——"0 个 chunk 进，0 个向量出"，数据管道哲学（上游可能产出 0 段，这是正常数据流不是异常）。Phase 1 的判断都写显式比较（`if count > 0`、`if fid not in files`），T0202 是项目里第一次用真值判断。

### 19.2 numpy 数组 + `.tolist()` —— 数值类型转原生 list

**Python 写法**（真实代码：[embedding.py:77](../../backend/app/services/embedding.py#L93)）：

```python
    return get_model().encode(chunks, normalize_embeddings=True).tolist()
```

**怎么读**：`model.encode(...)` 返回 **numpy 数组（ndarray）**——numpy 是 Python 数据科学的基础库（多维数组 + 高效数值计算，sentence-transformers 底层就是它）。`.tolist()` 是 numpy 数组的方法，把多维数组**递归转换**成 Python 原生 list（numpy float32 标量 → Python float）。链式调用 `a().b().c()` 在 Python 和 JS 里语法相同：每一步返回值上继续调方法。

**TypeScript / Node.js 类比**：`Array.from(f32Array)` 或 `[...f32Array]`——把 `Float32Array` 转成 `number[]`。numpy 之于 Python 数值计算 ≈ 类型化数组/张量之于 JS（不完美类比，方向正确）。

**重要差异**：

- **numpy.float32 ≠ Python float**：numpy 数组里的标量是 C 层对象的包装，不是 Python 内置 float——JSON 序列化、Pydantic 校验、ChromaDB 存储都会拒绝或出错。
- Python 没有类型系统替你在边界挡这些——靠**契约纪律**：`VectorStore.add_texts` 的签名写死 `List[List[float]]`，生产者必须自己转换成对的类型。

**DX-RAG 中在哪里使用**：`encode_chunks` 的返回转换——384 维向量必须以 `List[List[float]]`（纯 Python float）交给 Phase 1 的 `add_texts` / `search`。类型翻译在 embedding 模块边界内完成，numpy 不泄漏到模块外（与 Phase 1 的 distance→similarity 边界翻译同一哲学）。

### 19.3 `List[List[float]]` —— 嵌套类型标注

**Python 写法**（真实代码：[embedding.py:58](../../backend/app/services/embedding.py#L100)）：

```python
def encode_chunks(chunks: List[str]) -> List[List[float]]:
```

**怎么读**：`List[X]` 在 Phase 0 学过（≈ `X[]`）。嵌套就是**套娃**：`List[List[float]]` = "list，其中每个元素又是 list，最内层是 float"——外层长度 = 条数（chunk 数），内层长度 = 每条的长度（384 维）。Python 的类型标注运行时同样不检查（Phase 0 学过），这里纯粹是契约文档。

**TypeScript / Node.js 类比**：`number[][]`——完全对应。TS 还能写得更细（如固定长度的 tuple），Python 类型系统做不到，但语义上够用。

**重要差异**：无本质差异。唯一提醒：Python 的 `List` 来自 `typing` 模块（`from typing import List`——[embedding.py:18](../../backend/app/services/embedding.py#L34) 恰好是 T0202 新增的 import），Python 3.9+ 也能用小写 `list[list[float]]`（内置泛型），本项目用 `typing.List` 保持与 Phase 0 一致。

**DX-RAG 中在哪里使用**：`encode_chunks` 的返回类型。**第一次出现其实在 Phase 1**——`vector_store.py` 的 `add_texts(embeddings: List[List[float]])` 和 `search(query_vector: List[float])` 早就写下了这个形状；T0202 是它的**生产者**——契约在前、实现在后，又一次应验。

---

> **T0202 收官**：19.1–19.3 为 T0202 新增知识（真值判断、numpy/.tolist()、嵌套类型标注）。Phase 2 的 Python 知识到此闭环：T0201 管"怎么加载"（18.1–18.5），T0202 管"怎么生产"（19.1–19.3）。`with` 语句仍未出现（原预计 Phase 2 模型加载，实际未用）——继续留在"尚未遇到"，Phase 3 文件操作时再记录。

---

## 20. T0301 新增 Python 知识

> 本节记录 ingest.py 中出现的 Python 知识（T0301）。格式同第 17/18/19 节。完整讲解见 [phase-03-document-processing.md](./phase-03-document-processing.md) 第 3–4 节。

### 20.1 `pathlib.Path` 与 `read_bytes()`

**真实代码**：[ingest.py:78-108](../../backend/app/services/ingest.py#L78-L108)

```python
from pathlib import Path          # 第 71 行

def parse_text_file(file_path: Path) -> str:
    try:
        raw = file_path.read_bytes()
```

**怎么读**：`pathlib` 是 Python 3.4+ 的标准路径库。`Path("data/a.txt")` 创建一个**路径对象**，方法都挂在对象上：`read_bytes()` 读二进制、`read_text()` 按编码读文本、`exists()`、`parent`、`name`。旧式代码用 `os.path` 的函数（`os.path.join`、`os.path.exists`），新代码推荐 pathlib。

**TypeScript / Node.js 类比**：`node:path` 的纯函数 + `fs` 的操作，合并成对象 API：

```ts
// Node：操作是独立函数
import { readFileSync } from 'fs';
const raw: Buffer = readFileSync(filePath);

// Python：操作挂在路径对象上
raw = file_path.read_bytes()
```

**DX-RAG 中在哪里使用**：T0301 是 `pathlib` 第一次进项目（此前 config.py 用字符串路径）。为什么用 `read_bytes` 而不是 `read_text`？因为这个函数的任务就是"自己猜编码"——先拿原始字节，再自己决定怎么解（见 20.2）。`read_text` 默认按 UTF-8 读，猜错了没机会补救。

### 20.2 `bytes` vs `str` —— Python 的"二进制"和"文本"（本 Task 最核心的新概念）

**真实代码**：[ingest.py:95-105](../../backend/app/services/ingest.py#L95-L105)

```python
raw = file_path.read_bytes()          # → bytes
return raw.decode(encoding, errors=errors)   # → str
```

**怎么读**：Python 有**两种独立的字符串相关类型**：

| | `str` | `bytes` |
|--|-------|---------|
| 是什么 | Unicode 码点序列（"抽象字符"） | 原始字节序列（0–255） |
| 例子 | `"中文"` | `b"\xd6\xd0"`（GBK 的"中"） |
| 转换 | `.encode(enc)` → bytes | `.decode(enc)` → str |

**关键认知：解码（decode）是 bytes → str 方向的转换。** 磁盘上的文件永远是 bytes；要得到能处理的文本 str，必须经过一次"按编码解码"。编码（encoding）就是"字节和字符之间的对应规则"——同一串字节按 UTF-8 解是 `"中"`，按 GBK 解可能完全不同或直接报错。

**TypeScript / Node.js 类比**：JS 的 `string` 内部是 UTF-16，**天生已经"解码完成"**——所以 JS 里没有"字符串的编码"这个概念；Node 的 `Buffer` 才对应 Python 的 `bytes`。你已有的直觉是：`readFileSync` 拿 Buffer → `buf.toString('utf-8')` 拿 string。Python 把这个直觉变成了**类型系统的一部分**：`bytes` 和 `str` 是不同的类型，`.decode()` / `.encode()` 是显式转换。

**DX-RAG 中在哪里使用**：`parse_text_file` 的全部逻辑 = "bytes → str 的转换，中间可能要试 3 种编码"。这也是为什么 Python 处理老文件比 Node 顺手（见 20.3）。

### 20.3 解码错误策略：`errors="strict"` / `"ignore"`（还有 `"replace"`）

**真实代码**：[ingest.py:101-105](../../backend/app/services/ingest.py#L101-L105)

```python
errors = "ignore" if encoding == "gbk" else "strict"
try:
    return raw.decode(encoding, errors=errors)
except UnicodeDecodeError as exc:
    ...
```

**怎么读**：`bytes.decode()` 遇到"按这个编码解不开的字节"时怎么办，由 `errors` 参数决定：

| 策略 | 行为 | 类比 |
|------|------|------|
| `strict`（默认） | 抛 `UnicodeDecodeError` | `TextDecoder` 的 `fatal: true` |
| `replace` | 替换成 � (U+FFFD) | `TextDecoder` 默认的 `fatal: false` |
| `ignore` | 静默丢弃非法字节 | JS 无直接等价（比 replace 更激进） |

**DX-RAG 为什么 strict 打前站、ignore 兜底**：前两级（UTF-8/UTF-16）用 strict——**错猜编码必须响亮地失败，把机会让给下一级**；如果错猜时悄悄 replace，就会静默返回一坨 �（乱码），用户知识库里全是坏文本还没报错。最后一级 GBK 用 ignore——已经没有下一级了，宁丢个别坏字节也要保住可读的绝大部分。完整故事（含中文编码史）见 phase-03 文档第 4 节。

### 20.4 按具体类型捕获异常：`OSError` / `UnicodeDecodeError`

**真实代码**：[ingest.py:95-107](../../backend/app/services/ingest.py#L95-L107)

```python
try:
    raw = file_path.read_bytes()
except OSError as exc:            # 读文件失败
    raise AppError("FILE_PARSE_ERROR") from exc

for encoding in (...):
    try:
        return raw.decode(encoding, errors=errors)
    except UnicodeDecodeError as exc:    # 这个编码猜错了
        attempts.append({"encoding": encoding, "error": str(exc)})
```

**怎么读**：`except 异常类型` 只接住**指定类型（及其子类）**的异常——不同 except 分支按异常类型分流。T0201 写的是 `except Exception`（全收）；**T0301 是项目里第一次按具体类型分别捕获**。

异常是类，有继承层级（TS 的 Error 也有，但 JS 里很少用 instanceof 分流）：

```text
BaseException
 └─ Exception
     ├─ OSError               ← 系统调用失败：文件不存在 / 权限不足 / 磁盘错误
     │   ├─ FileNotFoundError
     │   └─ PermissionError
     └─ ValueError
         └─ UnicodeDecodeError   ← "按这个编码解不开"
```

**为什么这里必须区分**：`UnicodeDecodeError` 在这里**不是"事故"，是"信号"**——它告诉循环"这个编码猜错了，换下一个"，所以被记入 attempts 继续循环；`OSError` 是"文件根本读不了"，没有重试空间，直接翻译成 422。同一份代码里，两种异常走完全不同的命运——这正是按类型捕获的意义。

**TypeScript / Node.js 类比**：`catch (e)` 里写 `if (e instanceof X) {...}` 的路由逻辑，Python 直接用 `except X:` 语法化。附带 `as exc` 捕获异常对象（≈ catch 的参数）。

### 20.5 `str(exc)` —— 异常对象转字符串

**真实代码**：[ingest.py:107](../../backend/app/services/ingest.py#L107)

```python
attempts.append({"encoding": encoding, "error": str(exc)})
```

**怎么读**：`str()` 是 Python 的内置转换函数——任何对象都能转成可读字符串（≈ JS 的 `String(x)`）。异常对象转字符串得到**人类可读的失败原因**：

```
'utf-8' codec can't decode byte 0xd6 in position 0: invalid continuation byte
```

（`0xd6` 是 GBK 的中文字节——对 UTF-8 来说非法。看到这种错误信息，有经验的人一眼就知道"这文件八成是 GBK 编码"。）

**TypeScript / Node.js 类比**：`err.message` / `` `${err.message}` ``。注意细微差异：Python 没有 `.message` 属性约定，`str(exc)` 是通用做法。

**DX-RAG 中在哪里使用**：`details.encoding_attempts` 的内容来源——**全项目第一次给 AppError 的 `details` 传真实数据**。三种编码各自为什么失败，装进 422 响应的 details，API 调用方不用翻日志就能定位"这是文件损坏还是第四种编码"。

### 20.6 `str(path)` —— Path 与老库 API 的桥接

**真实代码**：[ingest.py:138](../../backend/app/services/ingest.py#L138)（docx）；[ingest.py:232](../../backend/app/services/ingest.py#L232)（fitz，T0304 同款）

```python
from docx import Document

doc = Document(str(file_path))   # 不是 Document(file_path)！
```

**怎么读**：`str()` 是 Python 的内置转换函数（20.5 已接触 `str(exc)` 的用法，同一个函数）。`str(Path对象)` 返回它的字符串路径（Windows 上注意：Python 的 Path 转 str 得到反斜杠路径，如 `'uploads\\a.docx'`——这正是老库 API 要的格式）。

**为什么需要这一步**：python-docx 是 2008 年的库，API 定型早于 pathlib（2014 年 Python 3.4 才引入）。它的 `Document()` 只认 **`str` 路径或文件对象**，不认识 `Path` 对象。项目内部统一用现代惯例（`Path`），交接处用一行 `str()` 桥接——**两种惯例和平共处**。

**TypeScript / Node.js 类比**：老库 API 要 `string`，你手上是 `URL` 对象 → 传 `url.href`。或者旧代码库约定 `string` 路径，新代码用 `path.parse` 的对象——边界处转一下。这是所有语言里"新旧 API 共存"的通用姿势。

**DX-RAG 中在哪里使用**：`parse_docx_file` 打开文档时。**这个故事有三幕**：

- T0302 时曾预测"后续 T0303（openpyxl）大概率也是同款——老库认 str 路径"——**预测错了**：T0303 直接传 `Path` 就工作（openpyxl 是新一代库，底层 zipfile 自 Python 3.6 起原生支持 Path）。桥接只在"老库不认新类型"时需要，不是所有第三方库都需要——对比见 21.4。
- **T0304 第三幕：桥接又回来了**——`fitz.open(str(file_path))`（[ingest.py:232](../../backend/app/services/ingest.py#L232)）。PyMuPDF 的 fitz 是 C++ 绑定库，它的 open 接口同样不认 `Path`。**三个库三种情况**：python-docx 要桥、openpyxl 不要、fitz 又要。**最终教训：Path 支持没有统一答案**——看库文档的参数标注（`filename: str | Path`），不确定就 `str()` 一下，多写一行永远不炸。

### 20.7 生成器表达式 `(x for x in y)` —— 惰性版列表推导

**真实代码**：[ingest.py:145](../../backend/app/services/ingest.py#L145)

```python
rows = [" ".join(cell.text for cell in row.cells) for row in table.rows]
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#              圆括号里是生成器表达式（不是列表推导）
```

**怎么读**：列表推导你已经会了（T0102：`[x for x in y]` ≈ `.map()`）。把方括号换成**圆括号**，就得到生成器表达式——它不立刻造出整个 list，而是返回一个"**按需产出**"的迭代器：

```python
nums = [x * 2 for x in range(5)]   # 列表推导：立刻算出 [0, 2, 4, 6, 8]，占内存
nums = (x * 2 for x in range(5))   # 生成器表达式：先不干活，每次 next() 算一个
```

**为什么要它**：`" ".join(...)` 需要一个"可迭代对象"（list 也行，生成器也行）。写列表推导会先造一个中间 list（比如 100 个 cell 的文本 list），再交给 join 全部读完丢弃；写生成器表达式**省掉这个中间 list**——join 取一个、生成一个。数据量大时是内存与速度的差异。

**TypeScript / Node.js 类比**：列表推导 ≈ `.map()`（立刻返回新数组）；生成器表达式 ≈ **iterator / 惰性管道**（`function*` + `yield`，或 RxJS 的 Observable——订阅时才产数据）。

**DX-RAG 中在哪里使用**：表格行内 cell 的拼接。⚠️ 项目惯例：**只作为函数参数（如 `join(...)` 的实参）时写生成器表达式**；要存进变量的仍用列表推导（如 [ingest.py:142](../../backend/app/services/ingest.py#L142) 的 `[p.text for p in doc.paragraphs]`）。两者语义几乎相同，读代码时圆括号、方括号都当"遍历并收集"即可。

### 20.8 `"sep".join(可迭代对象)` —— Python 的 join 在字符串上

**真实代码**：[ingest.py:145-147](../../backend/app/services/ingest.py#L145-L147)

```python
" ".join(cell.text for cell in row.cells)   # 空格分隔
"\n".join(rows)                             # 换行分隔
"\n".join(paragraphs + tables)              # 最终拼接
```

**怎么读**：Python 的 `join` 是**字符串的方法**，挂在分隔符上；JS 的 `join` 是**数组的方法**，挂在数组上。方向正好相反：

| | JS | Python |
|--|----|--------|
| 写法 | `rows.join(" ")` | `" ".join(rows)` |
| 方法挂在 | 数组（被连接者） | 分隔符 |
| 接收参数 | 分隔符 | 可迭代对象（list/生成器等） |

**这个方向差是高频笔误源**：写顺手了 JS，很容易写出 `rows.join(" ")` 然后得到 `AttributeError: 'list' object has no attribute 'join'`。记忆锚点：**Python 的 join 是"分隔符伸出手来把你们串起来"**——`"、".join(["苹果", "梨"])` → `"苹果、梨"`。

**一个细节**：`join` 要求元素都是 `str`（数字要先 `str()` 化——`",".join(map(str, [1, 2, 3]))` 或列表推导），JS 的 join 会自动把数字转字符串。项目里 `cell.text` 已经是 str，没碰到这个坑；T0303（Excel）**果然碰到了**——SPEC 伪代码里的 `str(cell)` 就是为它准备的（兑现见 21.5）。

**DX-RAG 中在哪里使用**：`parse_docx_file` 的三层拼接（行内空格 → 行间换行 → 段落表格换行）。这是全项目第一次密集使用 `join`。

---

> **T0301 收官**：20.1–20.5 为 T0301 新增知识（路径对象、bytes/str、解码错误策略、按类型捕获异常、异常转字符串）。Phase 3 的 Python 知识从这里开始积累——T0301 管"文本类文件的字节解码"，T0302 起带来第三方解析库（python-docx 已到，见 20.6–20.8）。

> **T0302 收官**：20.6–20.8 为 T0302 新增知识（str() 桥接、生成器表达式、字符串上的 join）。T0302 没有引入新的"语言机制"，主要是**新语法 + 项目惯例**——真正的重头戏（第三方库对象模型）属于 python-docx 的学习，见 phase-03 文档第 13 节。

---

## 21. T0303 新增 Python 知识

> 本节记录 ingest.py 中出现的 Python 知识（T0303）。格式同第 17–20 节。完整讲解见 [phase-03-document-processing.md](./phase-03-document-processing.md) 第 19–20 节。

### 21.1 `is not None` —— "没有值"和"假值"是两回事（⚠️ 0 是合法值）

**真实代码**：[ingest.py:186](../../backend/app/services/ingest.py#L186)

```python
line = " ".join(str(cell) for cell in row if cell is not None)
#                                         ^^^^^^^^^^^^^^^
#                                         过滤条件：is not None，不是 if cell
```

**怎么读**：过滤条件写的是 `cell is not None`，而不是 `if cell`。区别在"假值家族"——Python 里 `None`、`0`、`0.0`、`""`、`[]`、`{}`、`False` 都是假值：

| 单元格值 | `if cell`（真值判断） | `cell is not None` |
|----------|----------------------|-------------------|
| `None`（空格子） | 跳过 ✓ | 跳过 ✓ |
| `0`（合法数字） | **跳过 ✗** | 保留 ✓ |
| `0.0` | **跳过 ✗** | 保留 ✓ |
| `""`（空串） | 跳过 | 保留（join 后无差别） |
| `"0"`（文本零） | 保留 ✓ | 保留 ✓ |

**核心陷阱**：`0` 是合法单元格值（财务表的"本期利润 0"）但它是假值——`if cell` 会把 0 当成空格子丢掉。所以判断"**没有值**"必须用 `is not None`（T0201 的 is 身份比较），判断"**值空不空**"才用真值。

**TypeScript / Node.js 类比**：JS 的 `0` 同样是 falsy——`if (cell)` 也会误杀 0，`cell !== null` 才正确。Python 和 JS 坑法一致，区别是 Python 把 `None` 单例 + `is` 写成了习惯用法。

**DX-RAG 中在哪里使用**：`parse_excel_file` 的行内过滤。⚠️ 项目里同一函数的另一条过滤 `if line:`（全空行）用真值判断是**安全**的——那时值已经 `str()` 化，空串才是"没内容"。

### 21.2 生成器表达式带过滤条件 `(expr for x in xs if cond)`

**真实代码**：[ingest.py:186](../../backend/app/services/ingest.py#L186)

```python
" ".join(str(cell) for cell in row if cell is not None)
#        ^^^^^^^^^^                 ^^^^^^^^^^^^^^^^
#        转换（expr）                过滤（if cond，作用于原始元素）
```

**怎么读**：20.7 学了生成器表达式，T0303 出现**进阶形态：带 `if` 过滤**。语法位置和列表推导完全一样：`[expr for x in xs if cond]` / `(expr for x in xs if cond)`。

**执行顺序是"先过滤、后转换"**：`if` 检查的是循环变量 `cell`（原始元素），不是 `str(cell)` 的结果——None 单元格在 `str()` 之前就被挡掉了。这也是为什么 `if cell is not None`（而不是 `if str(cell)`）的写法既正确又高效。

**为什么过滤写在表达式里而不是外面**：一行表达式里"过滤 + 转换 + 拼接"三合一，正是 SPEC 3.4 伪代码的逐字形态——SPEC 给什么，实现照抄什么。

### 21.3 `data_only=True` —— 公式单元格读"值"还是读"公式"

**真实代码**：[ingest.py:177](../../backend/app/services/ingest.py#L177)

```python
wb = load_workbook(file_path, data_only=True)
```

**怎么读**：Excel 的公式单元格有两层内容：**公式文本**（`"=SUM(A1:A2)"`）和**上次保存时算好的缓存值**（42）。openpyxl 默认（`data_only=False`）读公式文本；`data_only=True` 读缓存值。

**RAG 为什么要值**：知识库要"用户看到的内容"——公式文本对语义检索没意义（搜"42"不应该命中 `=SUM(...)`）。

**⚠️ 陷阱（连锁反应）**：缓存值只在"用 Excel 打开过并保存"的文件里存在。**程序生成的 xlsx**（openpyxl 写、BI 导出）的公式格没有缓存 → `data_only=True` 读到 None → 被 21.1 的过滤跳过。链条：**data_only → None → 跳过**——这正是 21.1 的 `is not None` 过滤存在的原因之一。

**TypeScript / Node.js 类比**：SheetJS 的 `cell.f`（公式）vs `cell.v`（原始值）vs `cell.w`（格式化显示文本）——`data_only=True` 大约等于"要 `v` 不要 `f`"。

### 21.4 `iter_rows(values_only=True)` + openpyxl 直接收 Path

**真实代码**：[ingest.py:184](../../backend/app/services/ingest.py#L184) / [ingest.py:177](../../backend/app/services/ingest.py#L177)

```python
for row in ws.iter_rows(values_only=True):
#                   ^^^^^^^^^^^^^^^^
#                   逐行生成器；values_only 给值不给 Cell 对象
```

**怎么读**：`iter_rows()` 是 openpyxl 工作表对象的**逐行生成器**——每次迭代产出一个行元组 `(v1, v2, ..., vN)`。`values_only=True` 决定元组里装的是**单元格值**（int/float/str/None）；默认 False 给 Cell 对象（要自己 `.value`）。一行 None 就是一个"没有这一格"。

**Path 支持（20.6 预测被证伪）**：openpyxl 的 `load_workbook()` **直接收 Path 对象**——T0303 没有 `str(file_path)` 桥接。原因：openpyxl 是新一代库（2010 年代，与 pathlib 同期成长），底层 zipfile 自 Python 3.6 起原生支持 Path；python-docx 是 2008 年的老库。**桥接只在"老库不认新类型"时需要**。判断方法：看库文档的参数类型写 `filename: str | Path` 就不用桥。

**TypeScript / Node.js 类比**：SheetJS `XLSX.readFile()` 收 string 路径；`sheet_to_json({header: 1})` 的逐行思想一致。

### 21.5 `str(cell)` —— 单元格值类型杂多，str() 统一

**真实代码**：[ingest.py:186](../../backend/app/services/ingest.py#L186)

**怎么读**：同一个 worksheet 里，单元格值类型可以各不相同：文本 → `str`、数字 → `int`/`float`、日期 → `datetime` 对象、布尔 → `bool`、空 → `None`。`" ".join(...)` 要求元素全是 `str`（20.8 的细节），所以每个值先 `str()` 化。

**⚠️ 20.8 的预防针兑现**：T0302 时写了"T0303 读数字单元格时大概率会遇到 join 要求 str 的坑——先打个预防针"，T0303 **果然遇到**，而且 SPEC 伪代码里就写好了 `str(cell)`——坑被 SPEC 提前埋好了答案。

**datetime 的 str() 结果**：日期单元格变成 `"2024-01-15 00:00:00"` 这样的字符串（v1 接受；格式化控制不是解析器的活）。

**TypeScript / Node.js 类比**：`${value}` 模板串自动转字符串——但 JS 的数字转字符串是 join 自动做的，Python 要显式 `str()`。

---

> **T0303 收官**：21.1–21.5 为 T0303 新增知识。T0303 没有引入新的"语言机制"，主要是**一个语法进阶（带过滤的生成器表达式）+ 一个语义陷阱（None vs 假值）+ 第三方库的 data_only 契约**。Phase 3 的解析器至此三分天下——文本（编码战）、DOCX（结构战）、Excel（单元格值战），见 phase-03 文档第 18 节。

---

## 22. T0304/T0305 新增 Python 知识

> 本节记录 ingest.py 中出现的 Python 知识（T0304/T0305）。格式同第 17–21 节。完整讲解见 [phase-03-document-processing.md](./phase-03-document-processing.md) 第 22–26 节。
>
> T0304/T0305 与前面三个 Task 不同：它们第一次带来**语言机制级别**的新知识（try/except/else、模块级状态、try/finally），而不只是语法糖。因为 PDF 解析引入了"外部世界不可靠"这个新问题域。

### 22.1 `try/except/else` —— else 只在 try 无异常时执行

**真实代码**：[ingest.py:349-369](../../backend/app/services/ingest.py#L349-L369)（ocr_page 的重试循环）

```python
for attempt in range(1, _MAX_TOTAL_ATTEMPTS + 1):
    try:
        response = MultiModalConversation.call(...)
    except Exception:
        retriable = True        # 调用炸了（网络层）
    else:
        if response.status_code == 200: ...
        if response.status_code in (401, 403):
            raise AppError("OCR_AUTH_FAILED")   # ← 这个 raise 不会被上面的 except 捕获！
        retriable = ...
```

**怎么读**：`else` 子句只在 **try 块没有抛异常**时执行。分工是：`except` 处理"调用炸了"，`else` 处理"调用成功回来了"——把"失败路径"和"成功路径"从语法上分开。

**⚠️ 最关键的微妙处**：**else 块里的异常不被本层的 except 捕获**。上面 `raise AppError("OCR_AUTH_FAILED")` 写在 else 里——如果它写在 try 里，会被 `except Exception` 吞掉（认证失败变成"网络错误"重试 3 次，浪费时间还报错错码）。写在 else 里，它干净地穿透重试循环 → 穿透 try/finally（finally 照常执行 close）→ 传播给调用方。**这是一个靠语法结构保证正确性的设计**：换个写法（try 里 raise）就是 bug。

**TypeScript / Node.js 类比**：JS 没有 `try/else` 子句。等价写法是"成功分支写在 try/catch 外面"：

```ts
let response: Response;
try {
  response = await call();
} catch (e) {
  retriable = true;
}
if (response.status === 401) throw new AppError('OCR_AUTH_FAILED');  // 在 catch 的势力范围外
```

Python 的 `else` 就是给这个"势力范围外"一个正式的语法位置。注意区分两个 else：**for-else**（第 11 节提过，循环正常走完才执行）和 **try-else**（try 无异常才执行）——名字一样，语义不同。

**DX-RAG 中在哪里使用**：ocr_page 的 API 调用。全项目第一次用 try/except/else。

### 22.2 回调函数 + `Callable` 类型标注 —— 函数是一等公民

**真实代码**：[ingest.py:194-197](../../backend/app/services/ingest.py#L194-L197)

```python
def parse_pdf_file(
    file_path: Path,
    ocr_page: Optional[Callable[[Path, int], str]] = None,
) -> str:
```

**怎么读**：函数的参数可以是一个**函数**。`Callable[[Path, int], str]` 读作"吃 `(Path, int)`、吐 `str` 的函数类型"——方括号里**逗号前是参数类型列表，逗号后是返回类型**。`Optional[...]` 表示可以传 `None`（默认值 `= None` 就是"可选参数"）。

**怎么用**：调用方可以传自己的函数进去（`parse_pdf_file(path, ocr_page=my_func)`），被调用方在需要时调用它（`ocr_page(file_path, page.number + 1)`）——**和 TS 传 callback 完全同一个概念**，只是类型标注语法不同。

**TypeScript / Node.js 类比**：

```ts
type OcrCallback = (pdfPath: string, pageNumber: number) => string;
function parsePdfFile(filePath: string, ocrPage?: OcrCallback): string
```

这是前端日常技能（`onClick`、`array.map(fn)`、事件订阅都是传函数）。Python 无新概念，只有新语法。**为什么 Python 的 `Callable` 在 `typing` 里而不是语言内置**：函数类型标注是后来加的类型系统特性，`typing.Callable` 就是它的名字。

**DX-RAG 中在哪里使用**：`parse_pdf_file` 的 OCR 回调口——T0304 用它**冻结了 T0305 的契约**（"frozen T0305 contract"）：T0305 的函数必须按 `(Path, int) -> str` 实现。**先定接口再各自实现**——与 Phase 1 的 ABC 同思想、不同形态（ABC 用类继承，这里用函数签名）。

### 22.3 模块级可变状态 + 访问器函数 —— "穷人版单例"

**真实代码**：[ingest.py:266](../../backend/app/services/ingest.py#L266)、[ingest.py:269-281](../../backend/app/services/ingest.py#L269-L281)

```python
_OCR_WARNINGS: List[Dict[str, Any]] = []

def get_ocr_warnings() -> List[Dict[str, Any]]:
    """Return the warnings recorded by ``ocr_page`` since the last clear."""
    return list(_OCR_WARNINGS)          # ← 防御性拷贝

def clear_ocr_warnings() -> None:
    """Reset the OCR warning list."""
    _OCR_WARNINGS.clear()
```

**怎么读**：模块顶部的 list 是**模块级可变状态**——模块被 import 时创建一次，之后所有函数共享同一份。这打破了前三个 parser 的"纯函数"世界（同样的输入 → 同样的输出），进入"有状态"世界。

**为什么不开 class**：状态只有一个 list、操作只有读/清/记，不值得为一个 list 建一个类。Python 社区的务实做法：**模块级变量 + 访问器函数 = "穷人版单例"**——模块本身就是单例（import 机制保证只加载一次），所以模块级变量天然全局唯一。这个模式和 T0201 的 embedding `_model` 单例**同一个家族**：都是"模块当对象用"（embedding 那个用 `global` 赋值，这个直接修改 list——**list 不需要 global**，因为 `.append()` / `.clear()` 是原地操作，不是重新赋值）。

**`return list(_OCR_WARNINGS)` 为什么拷贝**：调用方拿到的是快照——外面怎么改都动不了模块内部状态。TS 类比：`return [...warnings]`。T0107 学过 `list()` 转换，这里是它的第三个用途（转真列表 / 视图转列表 / **防御性拷贝**）。

**⚠️ 状态的所有权**：模块级状态最难的不是写，是**谁负责清**。代码注释写明："Lifecycle (clear per file) is owned by the ingest pipeline (T0308)"——**状态归谁管写在注释里**，谁漏清谁背锅。

**TypeScript / Node.js 类比**：module 级数组 + 导出的 get/clear 函数——JS 里天天见（模块级 store、事件队列）。差异是 Python 没有闭包作用域保护（`_` 前缀只是约定），JS 有 module 作用域天然私有。

**DX-RAG 中在哪里使用**：OCR 警告收集。为什么 warnings 不走返回值？因为**五个函数的外形必须一致**（都是 `Path → str`）——警告走旁路，主数据流保持纯净（phase-03 第 25 节⑥）。

### 22.4 `isinstance(x, T)` —— 运行时类型检查

**真实代码**：[ingest.py:359-363](../../backend/app/services/ingest.py#L359-L363)

```python
return "".join(
    item["text"]
    for item in content
    if isinstance(item, dict) and "text" in item
)
```

**怎么读**：`isinstance(x, T)` 返回"x 是不是 T 类型（或其子类）的实例"——Python 的**运行时类型检查**。上面这行在防御**外部 API 的返回数据**：content 列表里可能有 dict、str、None 等各种形态，只取"是 dict 且有 text 键"的项。

**为什么需要它**：Python 是动态语言，`content` 里装什么运行时才知道——尤其是**外部 API 返回的数据，结构不完全由我们控制**（API 升级、模型输出变化都可能改结构）。`isinstance` 是处理不可信数据的第一道防线：**先确认形状，再取值**。

**TypeScript / Node.js 类比**：TS 的 `x instanceof T` / `typeof x`——但 TS 的编译期类型系统在"外部不可信数据"面前也不管用（类型是"编译期承诺"，API 数据是"运行时现实"），所以 TS 生态里也有 zod / 运行时校验库做同类的事。**动态语言的运行时检查 ≈ 静态语言的运行时校验库**。

**DX-RAG 中在哪里使用**：OCR 响应的防御性过滤。⚠️ 与 21.1 的 `is not None` 区分：`is not None` 判断"没有值"；`isinstance` 判断"是什么类型"。

### 22.5 `time.sleep` + `range(1, N+1)` —— 退避等待与 1-based 循环

**真实代码**：[ingest.py:349-373](../../backend/app/services/ingest.py#L349-L373)

```python
for attempt in range(1, _MAX_TOTAL_ATTEMPTS + 1):   # 1, 2, 3
    ...
    if attempt < _MAX_TOTAL_ATTEMPTS and retriable:
        time.sleep(_RETRY_BACKOFF_SECONDS[attempt - 1])   # 1.0s → 2.0s
        continue
    break
```

**怎么读**：两个小知识合起来是一条"指数退避"：

- **`range(1, 4)` 是 1-based 计数器**：产出 1、2、3（而不是默认习惯的 0、1、2）。为什么这次要 1-based？因为要算两件事："还有没有下一次"（`attempt < 3`）和"这次该睡多久"（`_RETRY_BACKOFF_SECONDS[attempt - 1]`——元组下标是 0-based，所以又转回来）。**1-based 计数器 + 0-based 下标混用时，`attempt - 1` 这类转换是不可避免的**——和 `page.number + 1` / `page_number - 1`（PDF 页码）同一类边界转换。
- **`time.sleep(seconds)`**：暂停当前线程 N 秒。**重试之间的等待**——服务器被 429 限流时，立刻重试大概率再撞墙，睡 1s/2s（每次翻倍 = 指数退避）给服务器喘息时间。SPEC 9.3 明示的策略（~1s、~2s），实现把它变成常量 `_RETRY_BACKOFF_SECONDS = (1.0, 2.0)`。

**TypeScript / Node.js 类比**：`await new Promise(r => setTimeout(r, ms))`——⚠️ 一个关键差异：**JS 的 sleep 是异步的**（要 await，不阻塞事件循环），**Python 的 `time.sleep` 是同步阻塞的**（当前线程真停住）。服务端 Python 的同步阻塞在 FastAPI async 端点里会成为问题——但本项目服务层目前全是同步函数（`def` 不是 `async def`），FastAPI 会把它们丢到线程池跑，所以安全。这个差异以后写 async 代码时会重新浮出水面。

**DX-RAG 中在哪里使用**：ocr_page 的重试退避。⚠️ 项目里"重试"不是库（如 tenacity）而是**手写循环**——v1 范围控制（CLAUDE.md Out of Scope：无额外依赖），手写三行循环的成本低于引入重试库的成本。

### 22.6 `base64.b64encode(...).decode("ascii")` —— 二进制到文本的"安全通道"

**真实代码**：[ingest.py:333](../../backend/app/services/ingest.py#L333)

```python
img_b64 = base64.b64encode(pix.tobytes("jpg")).decode("ascii")
```

**怎么读**：三步链：`pix.tobytes("jpg")` 得 JPEG 字节（bytes）→ `base64.b64encode()` 把任意 bytes 编码成"只含 64 个安全字符"的 bytes → `.decode("ascii")` 转成 str。为什么最后用 `"ascii"` 解码？**因为 Base64 的输出字符集就是 ASCII 的子集**（A-Za-z0-9+/=）——用 ascii 解码永远不会失败（对比 T0301 的编码级联：那是解"未知编码"，这里是解"已知必然成功的编码"）。

**为什么要 Base64**：HTTP API 传二进制图片有两种方式：multipart 文件上传，或**把二进制塞进 JSON 字符串**。JSON 只能装文本，Base64 就是"二进制 → 文本"的标准转换。再拼上 `data:image/jpeg;base64,` 前缀，就成了 **data-URI**——和网页 `<img src>` 里的一模一样。

**TypeScript / Node.js 类比**：`btoa(binaryString)` / `atob()`——前端做 `FileReader.readAsDataURL()` 时**同一个 Base64 + data-URI 机制**（头像上传预览就是它）。前端直觉完整迁移，零新概念。

**DX-RAG 中在哪里使用**：OCR 页图片的编码。SPEC F004 明示的格式：`data:image/jpeg;base64,{img_base64}`（[ingest.py:343](../../backend/app/services/ingest.py#L343) 拼前缀）。

### 22.7 `try/finally` —— 无论成败都要执行的块

**真实代码**：[ingest.py:236-251](../../backend/app/services/ingest.py#L236-L251)（parse_pdf_file）、[ingest.py:329-378](../../backend/app/services/ingest.py#L329-L378)（ocr_page）

```python
    try:
        if doc.needs_pass:
            raise AppError("ENCRYPTED_PDF")
        ...
        return "\n\n".join(page_texts)
    finally:
        doc.close()          # 成功、raise、return——三种路径都走到这一行
```

**怎么读**：`finally` 块在 try 块**无论怎么结束**（正常走完 / return / raise）都会执行。这里是"**资源释放的保证**"：`doc.close()` 释放文件句柄，任何路径都不漏。

**为什么重要**：这是全模块**第一次显式关闭资源**——对比 openpyxl 的 workbook（第 21 节 Pending #8：没关，靠 GC 回收）。**资源纪律**：打开的东西要关。前三个 parser 的库对象没有"必须显式关"的要求（python-docx/openpyxl 的对象 GC 就能收），fitz 的 Document 持有文件句柄，规范做法是显式 close——**新代码按更高标准写，旧代码不回头改**（"加"不改）。

**与 `with` 语句的关系**：`with fitz.open(...) as doc:` 是 Python 更惯用的写法（自动 close），效果与 try/finally 等价——实现选择了 try/finally（也许是因为 needs_pass 检查和循环结构都嵌在 try 里更直观）。两者都记住：**`with` 是 try/finally 的语法糖**。

**TypeScript / Node.js 类比**：JS 的 `try {} finally {}` 同款语义。前端里类似的"保证执行"：`useEffect` 的 cleanup 函数（组件卸载时执行）、`fs.closeSync` 前的 finally。

**DX-RAG 中在哪里使用**：两个 PDF 函数各一个 `finally: doc.close()`。

### 22.8 `for page in doc` —— 库对象也能被 for 遍历

**真实代码**：[ingest.py:240](../../backend/app/services/ingest.py#L240)

```python
    for page in doc:
        text = page.get_text()
```

**怎么读**：`doc` 是 PyMuPDF 的 `Document` 对象，**不是 list**——但它能被 `for` 遍历。因为 Python 的 for 循环不要求容器类型，只要求对象实现 `__iter__`（迭代协议）："给我一个能挨个产出的东西就行"。PyMuPDF 实现了它，于是 `for page in doc` 逐页产出。

**这个特性的意义**：第三方库可以把自己的对象设计得"像容器"——用户不用记 `doc.get_pages()` 还是 `doc.pages()`，for 就好。Python 生态的库普遍遵循这个协议（openpyxl 的 `wb.worksheets` 是 list、`ws.iter_rows` 是生成器、fitz 的 `doc` 是迭代器——各有各的实现，统一用 for）。

**TypeScript / Node.js 类比**：`for (const page of doc)`——JS 的 for-of 同样是协议（iterable / `Symbol.iterator`），**两门语言在这一点上思想完全一致**：for 遍历的是"协议"，不是"类型"。

**DX-RAG 中在哪里使用**：parse_pdf_file 的逐页循环。附赠一个相关点：`doc.needs_pass` 是对象上的**属性**（不是方法调用）——"文档是否加密"是状态，不是动作，所以设计成属性。读第三方库对象时区分"状态（属性）"和"动作（方法）"能帮你看懂大量库 API。

---

> **T0304/T0305 收官**：22.1–22.8 为 T0304/T0305 新增知识。与 T0302/T0303 的"新语法为主"不同，这一轮带来的是**语言机制级别**的知识（try/except/else 的穿透性、模块级状态、try/finally 资源纪律、回调契约）——因为 PDF + OCR 第一次把"外部世界不可靠"（网络、认证、限流）和"资源生命周期"（文件句柄）拉进项目。Phase 3 的 Parse 站至此 5/5 完成，错误哲学从"全有或全无"进化到"文件级 fatal / 页级容错"两级，见 phase-03 文档第 25 节。

---

## 23. T0306 新增 Python 知识

> 本节记录 ingest.py 中出现的 Python 知识（T0306）。格式同第 17–22 节。完整讲解见 [phase-03-document-processing.md](./phase-03-document-processing.md) 第 27–31 节。
>
> T0306 是"语法密度"最低的一轮——没有新机制，只有几个小件 + 一个惯用法。但它是全模块唯一一个**纯函数**（无 try、无 except、无状态、无 I/O），值得停下来看看"简单"长什么样。

### 23.1 `str.splitlines()` —— 按"行边界"切分的 split

**真实代码**：[ingest.py:410](../../backend/app/services/ingest.py#L410)

```python
lines = text.splitlines()  # Step 1: split by line boundaries
```

**怎么读**：`splitlines()` 按**行边界**切字符串——注意不是按 `"\n"` 字符。它认识 Python 定义的全部行边界：`\n`、`\r\n`、`\r`（老 Mac）、`\v`、`\f`，以及 Unicode 行分隔符（U+2028 / U+2029）。

**两个关键差异（vs `split("\n")`）**：

- `"a\nb\n".splitlines()` → `["a", "b"]`；`"a\nb\n".split("\n")` → `["a", "b", ""]`——**splitlines 不产生末尾空串**（结尾的换行不代表"还有一个空行"）
- Windows 文本（`\r\n`）用 `split("\n")` 切会每行残留一个 `\r`，还得再处理——splitlines 一步到位

**为什么 SPEC 指定它**：清洗的输入来自五种 parser，任意一种都可能产出混用行边界的文本（PDF 提取尤其如此）。行边界是"概念"，不是"字符"——用行感知的 API 切。

**TypeScript / Node.js 类比**：JS 没有内置等价物——`text.split('\n')` 会残留 `\r`（所以前端常常写 `text.split(/\r?\n/)`）。Python 把它做成了内置方法。

**DX-RAG 中在哪里使用**：clean_text 的 Step 1。⚠️ 与 `split()` 区分：`split()`（无参）按任意空白切且吞掉连续空白——**会破坏行内空格**；`splitlines()` 只按行边界切，行内内容原样保留。两者都在项目里出现，别混。

### 23.2 管道式重赋值 —— 三行列表推导组成的流水线

**真实代码**：[ingest.py:410-413](../../backend/app/services/ingest.py#L410-L413)

```python
lines = text.splitlines()                        # Step 1
lines = [line.strip() for line in lines]         # Step 2
lines = [line for line in lines if line]         # Step 3
return "\n".join(lines)                          # Step 4
```

**怎么读**：同一个变量名 `lines` 被连续赋值三次，每次都在**上一版的产出上加工**——这是 Python 社区写"管道"的惯用姿势：**重赋值而非新变量**（写 `lines1`、`lines2`、`lines3` 会被 Python 社区笑话）。

**为什么不方法链**：Python 的 list 没有 `.map()` / `.filter()` 方法（那是 TS/JS 的世界）。所以"变换一个列表"的每一步都写成**列表推导式 + 重赋值**——列表推导 ≈ `.map()`（17.1），带 if 的列表推导 ≈ `.filter()`（23.3）。

**TypeScript / Node.js 类比**：

```ts
const cleaned = text
  .split(/\r?\n/)
  .map(l => l.trim())
  .filter(Boolean)
  .join('\n');
```

同一个管道，TS 用方法链（每个方法挂在返回值上），Python 用重赋值（每个推导式独立成行）。**读 Python 的"纵向管道"**：看到连续 `x = ...; x = ...; x = ...`，就当成 `.map().filter()` 链。

**DX-RAG 中在哪里使用**：clean_text 的 5 步 SPEC 就是天然管道，3 行代码兑现 5 步要求（Step 5 免费，见 23.4）。

### 23.3 带过滤条件的列表推导 `[x for x in xs if cond]` —— 21.2 的方括号版

**真实代码**：[ingest.py:412](../../backend/app/services/ingest.py#L412)

```python
lines = [line for line in lines if line]
```

**怎么读**：21.2 学过生成器表达式带过滤 `(expr for x in xs if cond)`；这里是**列表推导式带过滤**——语法位置一模一样，方括号圆括号的区别也一模一样（立刻造 list vs 惰性）。`if line` 用真值判断过滤：空串是假值（19.1）→ 空行被删。

**为什么这里用列表推导而不是生成器**：项目惯例（20.7 提过）：**要存进变量的用列表推导**。Step 2/3 的结果都要给下一步用，所以都造实体 list。

**一个横向对比**：T0303 的 `if cell is not None`（Excel）和这里的 `if line`（清洗）都是"过滤"，但判断标准不同：Excel 里 `0` 是合法值，只能用"有没有值"（`is not None`）；清洗里"空串"就是要删的对象，直接用"是不是假值"。**什么时候用哪种，取决于"假值"里有没有你要保留的合法值**。

**TypeScript / Node.js 类比**：`.filter(Boolean)`（删空串）vs `.filter(x => x != null)`（保留 0）——同一个分岔，JS 里天天见。

**DX-RAG 中在哪里使用**：clean_text Step 3。

### 23.4 `"\n".join([])` == `""` —— 一个"免费"兑现的 SPEC 要求

**真实代码**：[ingest.py:413](../../backend/app/services/ingest.py#L413)

```python
return "\n".join(lines)  # Step 4; empty → "" (Step 5)
```

**怎么读**：SPEC F005 的 Step 5 是"清洗后为空 → 返回空字符串"。实现里**没有 Step 5 的代码**——因为 `"\n".join([])` 天然返回 `""`。**join 一个空列表，结果就是空串**——这是 Python 保证的行为，不是巧合。注释自己也写着 `# Step 4; empty → "" (Step 5)`——实现者知道 Step 5 被 Step 4 免费覆盖了。

**为什么这个细节值得学**：好的抽象让边界情况免费。JS 里 `[].join('\n')` 同样返回 `""`——**"join 零个元素 = 恒等元"**是两门语言一致的约定。读代码时看到"没有显式处理边界"的写法，先想想边界是不是被免费覆盖了，再怀疑是 bug。

**DX-RAG 中在哪里使用**：clean_text 的 Step 4/5 合并点。`""` 往上传，由 T0308 判定 FAILED——清洗站只报告不裁决。

### 23.5 `str.strip()` 的精确语义 —— 它比 JS trim() 更"凶"

**真实代码**：[ingest.py:411](../../backend/app/services/ingest.py#L411)

```python
lines = [line.strip() for line in lines]
```

**怎么读**：`strip()` 无参时去掉**两端的所有 Unicode 空白**：空格、`\t`、`\n`、`\r`、`\v`、`\f`、全角空格（U+3000）、不换行空格（U+00A0）……覆盖比 JS 的 `trim()` 更广。

**两个要点**：

- **只动两端**：行内空白原样保留——`"a  b".strip()` 还是 `"a  b"`。SPEC 说"去行首行尾空格"，不是"压缩所有空白"（那是 whitespace normalization，v1 不做）
- **"空格"的范围**：SPEC 说"空格"，实现去的是"所有 Unicode 空白"——对中文文档这是优点（全角空格、`\xa0` 是中文排版常见噪声），但严格说实现比 SPEC 字面更激进（phase-03 第 31 节 Pending #17）

**TypeScript / Node.js 类比**：`String.prototype.trim()`——方向一致：**去两端、不动中间**；差异在空白字符集的覆盖范围。

**DX-RAG 中在哪里使用**：clean_text Step 2。⚠️ 项目里 strip 的两个用法横向看：T0304 的 `text.strip()` 是**真值判断**（"这页有没有字"），T0306 的 `line.strip()` 是**清洗**（"去两端空白"）——同一个方法，一个当"检测器"用，一个当"变换器"用。

---

> **T0306 收官**：23.1–23.5 为 T0306 新增知识。这一轮没有新语法机制，全是"小件"（splitlines / strip / 过滤推导 / join 空列表）——但合在一起是**全模块唯一一个纯函数**，也是 Parse 站之后的第一道质量闸门。Phase 3 从"解析"进入"加工"：parser 们交出 str，清洗站把它变成"无空行、无端白"的干净 str，交给切分站（第 24 节）。错误哲学不变——因为纯函数没有错误可谈。

---

## 24. T0307 新增 Python 知识

> 本节记录 ingest.py 中出现的 Python 知识（T0307）。格式同第 17–23 节。完整讲解见 [phase-03-document-processing.md](./phase-03-document-processing.md) 第 32–36 节。
>
> T0307 是"形状转换"轮——语法上全是熟面孔的新组合（uuid / enumerate / 元组 / 字典字面量），没有全新机制；真正新的是**身份**（ID 从无到有）与**形状**（`str → List[dict]`）。

### 24.1 `uuid.uuid4()` —— Python 的 randomUUID

**真实代码**：[ingest.py:487](../../backend/app/services/ingest.py#L487)（file_id 兜底）、[ingest.py:525](../../backend/app/services/ingest.py#L525)（chunk_id）

```python
if file_id is None:              # T0308 起：调用方没传才生成（兜底）
    file_id = str(uuid.uuid4())  # 每次调用生成一个
...
"chunk_id": str(uuid.uuid4()),   # 循环内：每块生成一个
```

**怎么读**：`uuid` 是标准库模块；`uuid4()` 生成基于随机数的 UUID（122 位随机 + 版本/变体位）——全局唯一靠的是随机空间够大，不靠中央协调。返回的是 `UUID` **对象**不是字符串，所以包一层 `str()` 转成 `"550e8400-e29b-41d4-a716-446655440000"`。

**为什么值得学**：uuid 家族还有其他版本——`uuid1()` 用时间戳 + MAC 地址（泄露机器信息，不推荐）、`uuid5()` 用名字做确定性生成（同一输入永远同一 ID）。**分布式系统发 ID 不靠协调者**，这个思想贯穿 RAG 管道：每个 chunk 在切分时自己给自己发 ID。

**TypeScript / Node.js 类比**：`crypto.randomUUID()`（Node 14.17+ / 现代浏览器）——差别：JS 版直接返回 `string`，Python 版要先 `str()`。旧写法 `uuidv4()`（uuid npm 包）也等价。

**DX-RAG 中在哪里使用**：SPEC 7.1 的身份体系落地点——file_id 每调用一个（全块共享）、chunk_id 每块一个。⚠️ 注意两个调用的**位置**：一个在循环外、一个在循环内——位置决定"共享"还是"每轮新值"（见 24.6）。**T0308 更新**：file_id 的**主生成**已上移到 `IngestService.process()`（管道入口只生成一次，见 25.3）——chunk_text 只保留 `if file_id is None` 的兜底（签名向后兼容的扩展，见 25.6）。"位置决定共享"的原则没变，只是舞台挪大了。

### 24.2 `enumerate()` —— map 的第二参数

**真实代码**：[ingest.py:523-531](../../backend/app/services/ingest.py#L523-L531)

```python
for index, piece in enumerate(pieces):
    ...
```

**怎么读**：`enumerate(xs)` 把序列变成 `(下标, 元素)` 对序列：`(0, x0), (1, x1), ...`——边遍历边数数。它是**惰性**的（生成器，不造中间 list）。`for index, piece in ...` 是元组解包：每次迭代把一对拆开接住。

**为什么值得学**：Python 里"遍历同时需要下标"的惯用解就是 enumerate——比 `for i in range(len(xs))` 更 Pythonic（后者是全模块 Phase 1 时代的写法，见第 10 节）。这里 enumerate 直接兑现 SPEC 7.1 的"chunk_index 0-based 仅排序"——**数据结构的默认计数方式正好匹配规范**，零转换代码。

**TypeScript / Node.js 类比**：`xs.map((piece, index) => ...)` 的第二个参数，或 `for (const [index, piece] of xs.entries())`。

**DX-RAG 中在哪里使用**：chunk_text 的返回推导——chunk_index 的 0-based 来源。⚠️ 与 T0305 的页码对比：ocr_page 的 page_number 是 **1-based**（人类计数，`page.number + 1` / `page_number - 1` 两端转换）——同一个文件里两种计数哲学并存：人类看的页码从 1 数，机器身份从 0 数。

### 24.3 元组与元组列表 —— 键值对常量表

**真实代码**：[ingest.py:422-427](../../backend/app/services/ingest.py#L422-L427)

```python
_MD_HEADERS_TO_SPLIT_ON = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
]
```

**怎么读**：元组 `(a, b)` 是**不可变序列**（创建后不能增删改元素）——列表是"随时可改的集合"，元组是"定型的组合"。这里每个元组 = 一对（Markdown 前缀, metadata 键）：库配置要求的"键值对清单"。

**两个要点**：

- **键名是 LangChain 的约定**：`"Header 1"`…`"Header 4"` 是 `MarkdownHeaderTextSplitter` 把标题塞进 `doc.metadata` 时用的键名——**第三方库的词汇表反向定义了我们的代码**。读库的文档先对齐它的词汇，再写自己的配置
- **元组解包**：`for a, b in pairs` 一次拆两个值——JS 的解构赋值同款，但 Python 对元组自动支持，不需要额外语法

**TypeScript / Node.js 类比**：无内置元组——`as const` 声明的只读数组最接近（`readonly [string, string][]`）。JS 里"键值对清单"通常用对象字面量（`{ "#": "Header 1", ... }`），但对象**不保证顺序**——元组列表保序，这正是标题层级 `#` → `####` 需要顺序的原因。

**DX-RAG 中在哪里使用**：`_MD_HEADERS_TO_SPLIT_ON` 常量。⚠️ 元组其实早就出现过：T0305 的 `_RETRY_BACKOFF_SECONDS = (1.0, 2.0)` 就是元组（当时只当"常量表"读）；T0307 是它第一次以"键值对清单"身份登场，值得正式认识。

### 24.4 `list.extend()` vs `append()` —— 加一个 vs 加一筐

**真实代码**：[ingest.py:517-521](../../backend/app/services/ingest.py#L517-L521)

```python
if len(candidate) <= max_chunk_size:
    pieces.append(candidate)              # 直通：加"一个"字符串
else:
    pieces.extend(recursive_splitter.split_text(candidate))  # 再切：加"一筐"字符串
```

**怎么读**：`append(x)` 把 x **作为一个元素**加进列表；`extend(iterable)` 把 iterable 的**每个元素**摊开加进去。

```python
xs = [1]
xs.append([2, 3])   # [1, [2, 3]]  —— list 被当单个元素，嵌套！
xs = [1]
xs.extend([2, 3])   # [1, 2, 3]    —— 摊开
```

**为什么值得学**：换错的后果在这里是真实 bug：`append(一个列表)` 会让 `pieces` 混入 list——下游 `enumerate(pieces)` 时 piece 是 list，chunk 的 content 变成列表对象。**返回值类型决定用哪个**：单个值 → append，序列 → extend。看一遍 `split_text` 的返回类型标注（`List[str]`）就知道该用 extend。

**TypeScript / Node.js 类比**：`push(x)` ≈ append（JS 的 `push(数组)` 同样嵌套）；`push(...xs)` ≈ extend（展开运算符）。

**DX-RAG 中在哪里使用**：chunk_text 的 Step 2/3 分岔点——直通块 append（单个 str）、递归再切 extend（List[str]）。这是项目里第一次出现 extend（此前只有 T0105 的 append）。

### 24.5 惰性导入第四次出现 —— 模式回顾

**真实代码**：[ingest.py:482-485](../../backend/app/services/ingest.py#L482-L485)

```python
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
```

**怎么读**：与前三次（docx / openpyxl / fitz）一模一样的姿势：**重库不放在文件顶部，放在函数体里首次调用时导入**——模块 import 永远不炸，失败推迟到真正使用那一刻。

**但这次有一处不同——没有 try/except 包裹**：

| | docx / openpyxl / fitz | langchain_text_splitters |
|--|----------------------|--------------------------|
| 导入失败 | 包成 `AppError("FILE_PARSE_ERROR")` → 422 | **裸奔**：ImportError 直接漏出 → 全局处理器 500 |

为什么？切分的失败是"程序环境坏了"（依赖没装），不是"用户的文件坏了"——没有用户可纠正的含义，所以不进错误目录（SPEC 9.4）。**错误处理的待遇跟着"失败是谁的错"走**，不是跟着"用了什么库"走。

**TypeScript / Node.js 类比**：`await import()` 动态导入——但 JS 里 top-level import 打包期就失败（更早暴露），Python 顶部 import 在运行时才失败——所以 Python 更常用函数内导入做"启动不炸"的保险。

**DX-RAG 中在哪里使用**：第 4 次（docx L136 / openpyxl L175 / fitz L230 / langchain L482）。同一个模式四次出现，已经从"知识点"升级为**项目惯例**：重型第三方库一律函数内导入。**T0308 更新**：这个惯例又用了三次——`process()` 惰性导入 ChromaVectorStore + encode_chunks，`_fail()` 再惰性导入一次 ChromaVectorStore（第 5–7 次，见 25.8）。

### 24.6 字典字面量 + 列表推导 —— "位置决定共享"

**真实代码**：[ingest.py:523-531](../../backend/app/services/ingest.py#L523-L531)

```python
return [
    {
        "chunk_id": str(uuid.uuid4()),  # 每轮求值 → 每块新 ID
        "content": piece,
        "chunk_index": index,
        "file_id": file_id,             # 引用外层变量 → 全块共享
    }
    for index, piece in enumerate(pieces)
]
```

**怎么读**：字典字面量 `{"key": value}` 造 dict（≈ JS 对象字面量；Python 的 key 必须带引号）。列表推导的表达式位置放一个 dict 字面量 = **每轮迭代造一个新 dict**——"推导式 + 字典"是 Python 造结构化数据的组合技（等价于 `pieces.map(piece => ({...}))`）。

**为什么值得学——"位置决定共享"**：同一个推导式里，`str(uuid.uuid4())` 写在字典里 → 每轮重新求值（每块新 chunk_id）；`file_id` 引用片段 2 的变量 → 每轮拿同一个值（全块共享）。**没有"共享声明"，位置就是声明**。反过来写（file_id 在循环内、chunk_id 在外面算一次）会把文件身份和块身份全部打碎——SPEC 7.1 的 ID 规则被一行代码的摆放位置兑现或破坏。

**TypeScript / Node.js 类比**：`pieces.map((piece, index) => ({ chunkId: crypto.randomUUID(), content: piece, chunkIndex: index, fileId }))`——同一个思路：闭包内的 `crypto.randomUUID()` 每次调用新值、`fileId` 引用外层 const。

**DX-RAG 中在哪里使用**：chunk_text 的返回——四键字典 = SPEC 7.4 ChunkRecord 的子集（embedding / metadata 由下游补上）。**T0308 更新**："位置决定共享"的舞台已扩大——`file_id` 的生成从"chunk_text 循环外"上移到了 `process()`（管道最上游，25.3），chunk_text 里只剩 `if file_id is None` 兜底；四键字典本身不变，推导式里的位置规则依然成立。

---

> **T0307 收官**：24.1–24.6 为 T0307 新增知识。这一轮的语法全是"熟面孔新组合"——真正的新东西是**身份体系**（SPEC 7.1 的 UUID 在这里第一次落地，位置即声明）和**数据形状分叉**（`str → List[dict]`）。Phase 3 的三个站到此全部有教学：Parse（五种格式）、Clean（纯函数）、Chunk（两段式切分 + ID）。下一站 T0308 编排已把它们接成管道（`IngestService.process`，见第 25 节）——file_id 的"主生成"随之从 chunk_text 上移到管道入口，chunk_text 的签名也第一次被**向后兼容地修改**（25.6）。错误哲学没有新花样：切分没有目录错误码，失败交给全局处理器。

---

## 25. T0308 新增 Python 知识

> 本节记录 ingest.py 中出现的 Python 知识（T0308）。格式同第 17–24 节。完整讲解见 [phase-03-document-processing.md](./phase-03-document-processing.md) 第 37–41 节。
>
> T0308 是 Phase 3 的收官轮——它把前七个 Task 写的函数**接成管道**（`IngestService`）。这一轮**没有全新的语法机制**（`@classmethod` 是新面孔但不是新概念），真正新的是**组织方式**：类当命名空间、身份在管道最上游发放、失败用返回值表达、rollback 幂等。另外两个"项目第一次"：第一个 f-string、第一个 400 错误码（`UNSUPPORTED_FILE_TYPE`，见 phase-03 第 37 节）。

### 25.1 `@classmethod` —— Python 的静态方法

**真实代码**：[ingest.py:562-568](../../backend/app/services/ingest.py#L562-L568)

```python
class IngestService:
    @classmethod
    def process(
        cls,
        file_path: Path,
        file_name: str,
        collection_name: str,
    ) -> Dict[str, Any]:
```

**怎么读**：`@classmethod` 装饰器把方法变成"类方法"——第一个参数是**类本身**（惯例命名 `cls`），调用时不需要实例：`IngestService.process(path, name, col)`。项目此前只见过 `@staticmethod`（`_to_chunk_records`，T0108，见 17.9）；classmethod 多一个 `cls` 参数，是两者唯一的实质区别——不需要实例、但想要"类"这个引用时用 classmethod。

**TypeScript / Node.js 类比**：TS 的 `static` 方法——`IngestService.process(...)` ≈ `class IngestService { static process(...) {...} }`；`cls` ≈ 静态方法里的 `this`（指向类构造器本身）。

**为什么值得学**：`IngestService` 从不实例化——类在这里纯粹当**命名空间**用，把编排相关的 `process` / `_parse` / `_fail` 收拢在一起，避免又一组模块级函数散落。管道函数已经 7 个了，再堆 3 个模块级函数会让"读文件头看结构"变成猜谜。⚠️ 一个真实的冗余：`_fail` 也是 `@classmethod` 但没用 `cls`（直接 return dict）——写成 `@staticmethod` 更准确，功能无差别（Pending Question，见 phase-03 第 41 节）。

**DX-RAG 中在哪里使用**：`IngestService.process` 是 SPEC F002 第 8 步的落点——上传层保存文件后调用它，拿回 F004 三态结果（SUCCESS / SUCCESS_WITH_WARNINGS / FAILED）。

### 25.2 `datetime.now(timezone.utc).isoformat()` —— Python 的时间戳

**真实代码**：[ingest.py:595](../../backend/app/services/ingest.py#L595)

```python
upload_time = datetime.now(timezone.utc).isoformat()
```

**怎么读**：`datetime.now(timezone.utc)` 取"带时区意识的当前时间"，`.isoformat()` 转成 ISO 8601 字符串（`"2026-08-23T07:30:00+00:00"`）。两步分开读：先构造时间对象，再格式化。⚠️ 只用 `datetime.now()`（不带 timezone）拿的是"本地时间但不带时区标记"——存库、跨服务器比较时会出"同一时刻两种写法"的坑，所以项目显式传了 `timezone.utc`。

**TypeScript / Node.js 类比**：`new Date().toISOString()`——几乎一一对应，都输出 UTC 的 ISO 8601 字符串。差别：JS 的 Date 内部永远是 UTC（`getHours()` 才转本地），Python 必须显式给 timezone 才"知道自己在哪个时区"。

**为什么值得学**：metadata 里的 `upload_time` 是 SPEC 7.4 / F008 的 9 字段之一，且被**反规范化**——同一文件的每个 chunk 都存同一时间戳。所以"取一次、存 N 份"：时间戳在管道最上游取一次（和 file_id 同一个"身份准备"区，相邻三行），下游全是复制。

**DX-RAG 中在哪里使用**：`process()` 的身份准备区（[ingest.py:594-596](../../backend/app/services/ingest.py#L594-L596)）——file_id、upload_time、OCR 警告清空，三件事都必须在管道**开跑之前**做（FAILED 路径也需要 file_id 和时间戳）。

### 25.3 关键字实参（keyword argument）—— 按名字传参

**真实代码**：[ingest.py:603](../../backend/app/services/ingest.py#L603)

```python
chunks = chunk_text(cleaned, file_name, file_id=file_id)
```

**怎么读**：Python 调用函数有两种传参方式：位置实参（`chunk_text(cleaned, file_name)`）和关键字实参（`file_id=file_id`）。关键字实参**不依赖参数顺序**，且自文档化——读代码的人不用翻签名就知道第三个参数是什么。`file_id=file_id` 左右两边：左边是**形参名**（chunk_text 签名里那个），右边是**实参值**（process 里的局部变量）——同名是巧合（变量名跟着形参名走是社区惯例）。

**TypeScript / Node.js 类比**：TS 没有（最接近的是传对象 `chunkText(cleaned, name, { fileId })`）——这是 Python 的纯增量，不是任何 JS 习惯的翻译。

**为什么值得学**：这是"身份先于管道"的传送带——file_id 在 `process()` 顶部只生成一次（[ingest.py:594](../../backend/app/services/ingest.py#L594)），通过 `file_id=file_id` 送进 chunk_text，被复制到每个 chunk 的元数据里。T0307 时 chunk_text 自己生成 file_id（24.1）；T0308 把生成权上移，靠的就是给签名加一个**带默认值的可选参数**（25.6）——项目第一次**修改**已有函数（"只加不改"惯例的第一次例外，详见 phase-03 第 41 节）。

**DX-RAG 中在哪里使用**：`process()` 里的关键字实参有两处——这里（身份流入）和 `store.add_texts(collection=..., chunks=..., embeddings=..., metadatas=...)`（[ingest.py:629-634](../../backend/app/services/ingest.py#L629-L634)，参数多、按名字传更清晰）。两处都是"参数语义重"的场合；其余调用（`_parse` / `clean_text` / `encode_chunks`）参数少且顺序直觉，保持位置传参。

### 25.4 set 字面量 —— JS 的 Set

**真实代码**：[ingest.py:538-539](../../backend/app/services/ingest.py#L538-L539)

```python
_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}
_EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xltx", ".xltm"}
```

**怎么读**：花括号里没有 `key: value` 的就是 **set 字面量**（有冒号的是字典字面量，见 24.6——同一个符号两种含义）。set 是无序、去重的集合。⚠️ 空花括号 `{}` 是**空字典**不是空 set（空 set 要写 `set()`）。

**TypeScript / Node.js 类比**：`new Set([".txt", ".md", ...])`——JS 没有 set 字面量（提案一直没落地），这是 Python 语法糖的净优势。

**为什么值得学**：成员测试 `suffix in _TEXT_EXTENSIONS` 是 O(1)（哈希表）；写成 list 也能跑但每次 O(n)。更重要的是**语义正确**：set 天生表达"这些值无顺序、无重复、只问属不属于"。

**DX-RAG 中在哪里使用**：`_parse` 的扩展名分发（[ingest.py:644-656](../../backend/app/services/ingest.py#L644-L656)）——先查文本类集合，再逐个 `if` 特殊格式（.pdf / .docx），最后不在 Excel 集合就抛 `UNSUPPORTED_FILE_TYPE`（项目第一个 400 错误码）。为什么是"模块级常量集合"而不是写死在 if 里？因为"支持哪些格式"是文件头一眼可见的清单，且 T0501 的上传校验层可能复用。

### 25.5 f-string —— JS 的模板字符串

**真实代码**：[ingest.py:619](../../backend/app/services/ingest.py#L619)

```python
"source_file": f"uploads/{collection_name}/{file_name}",
```

**怎么读**：`f"..."` 是 f-string（格式化字符串字面量）——大括号里是**任意表达式**，运行时求值后拼进字符串。这是项目第一个 f-string（此前一直挂在"尚未遇到"清单里，T0308 兑现）。

**TypeScript / Node.js 类比**：JS 的模板字符串 `` `uploads/${collectionName}/${fileName}` ``——几乎一一对应（Python 还有更老的 `"{}".format()` 和 `%` 写法，现代代码一律 f-string）。

**为什么值得学**：SPEC 7.4 的 `source_file` 是"原始文件相对路径"——它必须**反规范化**进每个 chunk 的 metadata（而不是查表），所以要在 metadata 的字典推导里现拼。f-string 让"拼路径"这种高频操作零样板。

**DX-RAG 中在哪里使用**：metadata 9 字段之一（[ingest.py:610-625](../../backend/app/services/ingest.py#L610-L625)）。⚠️ 拼出来的是**展示/追溯用途**的字符串，不是解析用路径——真实文件路径是 `file_path`（Path 对象），两者在 F008 里分工不同。

### 25.6 `Optional[str]` 默认参数 —— 签名第一次被修改

**真实代码**：[ingest.py:433-437](../../backend/app/services/ingest.py#L433-L437)（签名）、[ingest.py:487-488](../../backend/app/services/ingest.py#L487-L488)（兜底）

```python
def chunk_text(
    text: str,
    source_file: str,
    file_id: Optional[str] = None,   # T0308 新增：可选参数，默认 None
) -> List[Dict[str, str]]:
    ...
    if file_id is None:              # 兜底：调用方没传才生成
        file_id = str(uuid.uuid4())
```

**怎么读**：`Optional[str]` = "str 或 None"（≈ `string | null`），`= None` 让它成为**可选参数**——调用方不传也能跑。这是 T0307 函数第一次被修改（此前项目惯例是"只加不改"）：不是重写，而是**向后兼容的扩展**——老调用（不传 file_id）行为完全不变（自己兜底生成），新调用（传 file_id）得到共享身份。修改的纪律：**加参数 → 给默认值 → 老行为保留**。

**TypeScript / Node.js 类比**：`function chunkText(text: string, source: string, fileId: string | null = null)`——一一对应。

**为什么值得学**：函数签名是"冻结契约"（谁改谁负责所有调用方），但"冻结"不等于"不许演化"——演化方式是"只增不改"：新增可选参数、保留默认行为。⚠️ 教学自省：T0307 的教学曾断言 chunk_text 的签名"冻结"——T0308 立刻展示了"冻结的正确姿势"是什么样。

**DX-RAG 中在哪里使用**：`IngestService.process` 通过 `file_id=file_id` 传入（25.3）——这是"身份先于管道"的技术支撑：管道入口发一次 ID，切分站要么接收、要么兜底，两条路径都收敛到同一个 UUID。

### 25.7 `Path.unlink(missing_ok=True)` —— 删文件

**真实代码**：[ingest.py:675](../../backend/app/services/ingest.py#L675)

```python
file_path.unlink(missing_ok=True)
```

**怎么读**：`unlink` 是 pathlib 删文件的动词（源自 Unix `unlink` 系统调用）；`missing_ok=True` 让"文件不存在"不算错（默认 False 会抛 `FileNotFoundError`）。⚠️ 只删文件，不删目录（目录用 `rmdir`）。

**TypeScript / Node.js 类比**：`fs.rmSync(filePath, { force: true })`——`force` 和 `missing_ok` 是同一个思想："幂等地删"——删一个可能已经不存在的文件不是错误。

**为什么值得学**：FAILED 的 rollback 里删文件，**幂等是故意的**：两个失败闸门都开在"写向量库之前"（0 chunks），文件可能被上游存过、也可能没有——`missing_ok=True` 让两种历史都静默收敛到"文件不存在"。**写 rollback 代码的通用原则**：清理动作必须幂等，因为 rollback 自己也可能被重跑。

**DX-RAG 中在哪里使用**：`_fail()` 的第一步（[ingest.py:658-683](../../backend/app/services/ingest.py#L658-L683)）——删原始文件 + `delete_by_file` 清向量库，两个动作都幂等，保证"FAILED 之后重传同名文件不会被 409 挡住"（F004 检查③，最终验收在 T0502）。

### 25.8 惰性导入的第 5–7 次 —— 惯例的延伸

**真实代码**：[ingest.py:588-589](../../backend/app/services/ingest.py#L588-L589)、[ingest.py:673](../../backend/app/services/ingest.py#L673)

```python
def process(cls, ...):               # 函数体开头
    from app.core.vector_store import ChromaVectorStore
    from app.services.embedding import encode_chunks
    ...
def _fail(cls, ...):                 # 另一个函数体开头
    from app.core.vector_store import ChromaVectorStore
```

**怎么读**：第 5–7 次函数内导入（前 4 次见 24.5）。两个新情况：① **同一个模块被导入两次**——process 和 _fail 各自导入 ChromaVectorStore；Python 的 import 是**幂等 + 全局缓存**（`sys.modules`），第二次只是查表，没有"重复加载"的代价，所以"每个用到的函数各自导入"是合法风格。② `encode_chunks` 是**自家模块**（services.embedding）——惰性导入不只防"第三方库启动炸"，也防**循环导入**。

**TypeScript / Node.js 类比**：`await import()` 同样只加载一次（模块缓存）——重复 import 同一模块走缓存，没有重复执行代价。

**为什么值得学**：**惯例的诞生**——"重型第三方库一律函数内导入"从 4 次长到 7 次，说明它已稳定为项目风格（未来写代码默认遵循）。而 ChromaVectorStore 进 `_fail` 是"管道编排"的自然结果：FAILED 也要访问向量库（删除），所以它同样在**用得着的时候**才导入。两个函数的 import 都集中在函数体开头（PEP 8 惯例：函数内 import 不散落各处）。

**DX-RAG 中在哪里使用**：`process()` 和 `_fail()` 的开头——前者为"写"，后者为"删"，同一个类里写路径和删路径各自声明自己的依赖。

---

> **T0308 收官**：25.1–25.8 为 T0308 新增知识。这一轮**没有全新语法机制**（f-string 是兑现而非新概念）——真正的升级是**组织方式**：类当命名空间（25.1）、身份在管道最上游发放（25.2/25.3/25.6）、失败用返回值表达、rollback 幂等（25.7）、惯例延伸（25.8）。Phase 3 的 Python 教学到此闭环：从 T0301 的 bytes/str 到 T0308 的管道编排，一个前端开发者现在能完整读懂 686 行的 ingest.py。下一步 Phase 4（Knowledge Base API）回到 FastAPI 层，Python 新知识将转向路由与 Pydantic。
