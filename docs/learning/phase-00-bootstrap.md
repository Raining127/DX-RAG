# Phase 0 — Project Bootstrap 学习笔记

> 这是一份随项目开发和个人理解逐步演进的学习文档。当前版本优先服务于"前端开发者进入 Python 后端"的第一阶段理解；后续可以随着 Phase 推进补充更深入内容。

---

## 0. 阅读指南

### 这一章的目标是什么

读完 Phase 0 后，你不需要成为 Python 专家。你只需要做到：

- 能基本看懂项目里的 Python 代码
- 知道每个模块（main.py、config.py、errors.py、schemas.py）是干什么的
- 能用你已有的 TypeScript / React 知识来理解 Python 后端的结构
- 知道将来你自己的代码应该放在哪个目录

### 本章阅读路线

| 章节 | 深度 | 说明 |
|------|------|------|
| 第 1–3 节 | 🟢 必看 | 先建立"Phase 0 做了什么"的整体印象 |
| 第 4 节 Python 生存基础 | 🟢 必看 | 看懂 Python 代码的最低语法知识，只讲 Phase 0 实际用到的 |
| 第 5 节 T0001 Backend | 🟢 必看 | 理解 FastAPI 是什么、main.py 在做什么 |
| 第 6 节 T0002 Frontend | 🟢 可选 | 你是前端开发者，这部分可以快速扫过 |
| 第 7 节 T0003 Config | 🟢 必看 | 理解 Python 如何管理配置（对比 Node.js process.env） |
| 第 8 节 T0004 Error | 🟢 必看 | 理解 Backend 错误如何变成 HTTP Response |
| 第 9 节 T0005 Schema | 🟢 必看 | 理解 Pydantic 是什么——它不是你熟悉的 TypeScript interface |
| 第 10 节 T0006 Health | 🟢 必看 | 项目第一个真实 endpoint——从 URL 到 JSON 的最短路径 |
| 第 11 节 请求路径 | 🟡 建议理解 | 整合前 10 节，追踪一次完整请求 |
| 第 12–14 节 | 🟡 建议理解 | 对照表、目录结构、阅读路线——以后可以当速查手册 |
| 第 15 节 10 件事 | 🟢 必看 | Phase 0 的最低要求 |
| 第 17 节 FAQ | 🟡 建议理解 | 以前端视角回答常见困惑 |
| 第 22 节 进阶阅读 | 🔵 以后再看 | 等 Python 更熟悉后回来读 |

### 三种学习深度标记

| 标记 | 含义 |
|------|------|
| 🟢 **入门理解** | 第一遍必须理解的内容。用 TypeScript 类比 + 简单解释。|
| 🟡 **项目理解** | 解释 DX-RAG 为什么这样设计。帮你理解架构决策。|
| 🔵 **进阶阅读** | 可以以后回来看。不影响理解 Phase 0 的核心内容。|

---

## 1. Phase 0 到底做了什么

### 从你熟悉的事情开始理解

假设你要启动一个新的前端项目。你不会一上来就写组件代码。你会先：

```bash
npx create-next-app@14 my-app
# 或者
npm init && npm install next react react-dom typescript
```

然后配置 `tsconfig.json`、`next.config.js`、`package.json`。搭建好目录结构：`app/`、`components/`、`lib/`。

**Phase 0 就是后端 + 前端的 "create-next-app" 阶段。**

它搭建了：

| 基础设施 | 对应前端类比 | 后续谁依赖它 |
|----------|------------|------------|
| 后端项目目录结构（T0001） | `npx create-next-app` 搭出来的骨架 | 所有后端代码都知道放哪 |
| 前端项目骨架（T0002） | 同上 | 所有前端组件在此基础上构建 |
| 配置管理（T0003） | `.env.local` + 一个类型安全的 config 对象 | 所有需要 API Key / 参数的地方 |
| 统一错误格式（T0004） | 一个全局 `errorHandler` middleware | 所有 API endpoint |
| API 数据模型（T0005） | `types/api.ts` 里的 TypeScript interface | 所有 Request/Response |

### 为什么不能跳过 Phase 0 直接写 RAG

如果跳过 Phase 0：

- **配置散落各处**：`DEEPSEEK_API_KEY` 在 `qa.py` 里硬编码，改一个配置要搜遍整个项目（类比：把 API URL 硬编码在每个组件里）
- **错误格式混乱**：有的 endpoint 返回 `{"error": "xxx"}`，有的返回 `{"detail": "bad request"}`，前端要写 N 种 error parser
- **代码无处安放**：新建一个 API，不知道放哪个目录
- **没有类型契约**：不知道 Request body 长什么样、Response 返回什么字段

Phase 0 把"地基"打好，后面 12 个 Phase 才可能在上面盖楼。

---

## 2. 用一个前端开发者熟悉的方式理解整个项目

### 整体架构（当前 Phase 0 状态）

```text
┌──────────────────────────────────────────────┐
│  frontend/  (Next.js 14 App Router)           │
│  layout.tsx → page.tsx                        │
│  localhost:3000                               │
│       │                                        │
│       │ 未来通过 fetch 调用后端 API              │
│       │ (Phase 10-11 实现)                     │
│       ▼                                        │
│  ┌─────────────────────────────────────┐      │
│  │ backend/  (FastAPI)                  │      │
│  │ localhost:8000                       │      │
│  │                                      │      │
│  │ main.py  ← 应用入口                   │      │
│  │   ├── CORS middleware                │      │
│  │   ├── Exception handlers             │      │
│  │   └── api_router (/api prefix)       │      │
│  │       └── (未来: collections,        │      │
│  │            upload, query, files)      │      │
│  │                                      │      │
│  │ core/                                │      │
│  │   ├── config.py  ← 环境变量 → 配置对象 │      │
│  │   └── errors.py  ← 统一错误定义       │      │
│  │                                      │      │
│  │ models/                              │      │
│  │   └── schemas.py ← API 数据模型      │      │
│  └─────────────────────────────────────┘      │
│       │                                        │
│       │ 未来（Phase 1+）                        │
│       ▼                                        │
│  ┌─────────────────────────────────────┐      │
│  │ services/ (Phase 3-8 逐步实现)       │      │
│  │ ChromaDB / Embedding / RAG / LLM    │      │
│  └─────────────────────────────────────┘      │
└──────────────────────────────────────────────┘
```

### Phase 0 只搭到了哪里

- ✅ 后端能启动（`localhost:8000`）
- ✅ 前端能启动（`localhost:3000`）
- ✅ 配置可以从环境变量读取
- ✅ 错误有统一格式
- ✅ API 数据类型已定义
- ❌ 没有任何业务 API（`/api/collections`, `/api/upload`, `/api/query` 都还没实现）
- ❌ 前端还没有任何交互组件
- ❌ 前后端还没有连接

---

## 3. Phase 0 的 6 个 Tasks

### T0001 — Backend Application Skeleton

- **做什么**：创建 FastAPI 应用、目录结构、CORS、Router 占位
- **为什么需要**：后续所有后端代码都需要一个"家"——知道放哪个目录、怎么注册路由
- **你应该学到**：FastAPI 是什么、Uvicorn 是干什么的、`app/main.py` 就是后端的入口文件

### T0002 — Frontend Application Skeleton

- **做什么**：Next.js 14 App Router 项目骨架
- **为什么需要**：后续所有前端组件都在这个骨架上构建
- **你应该学到**：这和你熟悉的 create-next-app 基本一样，快速扫过即可

### T0003 — Configuration Foundation

- **做什么**：用 Pydantic BaseSettings 集中管理 22 个配置参数
- **为什么需要**：API Key、路径、大小限制等参数需要一处定义、处处使用
- **你应该学到**：Python 的配置管理方式（对比 Node.js 的 `process.env`）

### T0004 — Unified Error Response & Global Exception Handler

- **做什么**：定义 `{error: {code, message, details}}` 格式，注册全局异常处理器
- **为什么需要**：所有 API 的错误格式统一，前端只需要写一种 error parser
- **你应该学到**：Python Exception 如何变成 HTTP Response

### T0005 — Pydantic Data Models & API Schemas

- **做什么**：定义 16 个 Request/Response 的 Pydantic 模型
- **为什么需要**：API 的数据契约——前端知道该发什么、该收什么
- **你应该学到**：Pydantic 不只是 TypeScript interface，它是 runtime 可验证的类型系统

### T0006 — Health Check API

- **做什么**：注册 `GET /api/health`，返回 `{"status": "ok"}`
- **为什么需要**：SPEC Section 6.2 定义的基本可用性探测——让外部调用方（包括将来的前端）确认后端在运行
- **你应该学到**：第一个真实 endpoint 长什么样、`/api` 前缀 + 路由路径如何拼装、为什么 health 不检查数据库/LLM

> T0006 是 Phase 0 Gate Review 之后补充的规划任务（解决"health endpoint 没有 Task owner"的覆盖缺口），2026-08-18 实现完成。

---

## 4. Python 生存基础：只讲 Phase 0 实际用到的

> 这一节不是 Python 教程。只解释你在阅读 Phase 0 代码时会遇到的 Python 语法。

### 4.1 Python 文件就是 Module

**Python 语法**：一个 `.py` 文件就是一个 module。

**TypeScript 思维**：类比一个 `.ts` 文件。Python 的 `config.py` 就像 TypeScript 的 `config.ts`。

### 4.2 import

**Python 原代码**：

```python
from app.core.config import settings
```

**怎么读**：

- `from app.core.config` → 在 `app/core/config.py` 这个文件里
- `import settings` → 拿出那个叫 `settings` 的东西

**TypeScript 思维**：

```ts
import { settings } from "./app/core/config";
```

**差异注意**：
- Python 用 `.` 分隔路径（app.core.config），TS 用 `/`
- Python 不加文件扩展名 `.py`
- Python 的 `from X import Y` 可以选择性导入，不像 `import *`

### 4.3 def — 定义函数

**Python 原代码**：

```python
def get_deepseek_key(self) -> Optional[str]:
    if self.DEEPSEEK_API_KEY is not None:
        return self.DEEPSEEK_API_KEY.get_secret_value()
    return None
```

**怎么读**：

- `def` → "定义一个函数"
- `get_deepseek_key` → 函数名
- `(self)` → 参数
- `-> Optional[str]` → 返回值类型（类似 TS 的 `string | null`）

**TypeScript 思维**：

```ts
function getDeepseekKey(): string | null {
    if (this.deepseekApiKey !== null) {
        return this.deepseekApiKey.getSecretValue();
    }
    return null;
}
```

### 4.4 type hints

**Python 语法**：

```python
name: str = "hello"           # str ≈ string
count: int = 5                # int ≈ number
price: float = 3.14           # float ≈ number
items: List[str] = ["a","b"]  # List[str] ≈ string[]
config: Dict[str, int] = {}    # Dict[str, int] ≈ Record<string, number>
maybe: Optional[str] = None    # Optional[str] ≈ string | null | undefined
```

**TypeScript 思维**：语法像把 TS 的类型标注翻转了位置（`name: str` vs `name: string`）。

**关键差异**：Python type hints **默认不做运行时检查**。它们主要给 IDE 和类型检查器（mypy）用。TS 的编译检查更严格。

### 4.5 class

**Python 原代码**：

```python
class Settings(BaseSettings):
    APP_NAME: str = "dx-rag-demo"
```

**怎么读**：

- `class Settings` → 定义一个类
- `(BaseSettings)` → 继承自 `BaseSettings`

**TypeScript 思维**：

```ts
class Settings extends BaseSettings {
    APP_NAME: string = "dx-rag-demo";
}
```

### 4.6 self — 就是 this

**Python 原代码**：

```python
class Settings(BaseSettings):
    def get_deepseek_key(self) -> Optional[str]:
        if self.DEEPSEEK_API_KEY is not None:    # self ≈ this
            return self.DEEPSEEK_API_KEY.get_secret_value()
```

**关键区别**：Python 的 `self` 必须显式写在**方法参数列表里**（`def method(self, ...)`），而 TS/JS 的 `this` 是隐式的。这是 Python 设计哲学："显式优于隐式"。

**TypeScript 思维**：

```ts
class Settings extends BaseSettings {
    getDeepseekKey(): string | null {
        if (this.DEEPSEEK_API_KEY !== null) {    // this 不需要写在参数里
            return this.DEEPSEEK_API_KEY.getSecretValue();
        }
    }
}
```

### 4.7 `__init__` — 就是 constructor

**Python 原代码**：

```python
class AppError(Exception):
    def __init__(self, code: str, *, details=None, message=None):
        self.code = code
        self.http_status = ...
```

**TypeScript 思维**：

```ts
class AppError extends Error {
    constructor(code: string, opts?: { details?: any; message?: string }) {
        super();
        this.code = code;
        this.httpStatus = ...;
    }
}
```

**注意**：Python 的 `__init__` 和 TS 的 `constructor` 不完全一样（Python 对象在 `__new__` 阶段就创建了，`__init__` 只是初始化）。但 Phase 0 不需要关心这个区别。

### 4.8 decorator — 先理解成"给函数加标签"

**Python 原代码**（在 main.py 中）：

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status, content=...)
```

**先这样理解**：`@app.exception_handler(AppError)` 的意思是"把下面这个函数注册为 FastAPI 的异常处理器：当 `AppError` 被抛出时，调用这个函数来处理。"

**TypeScript 思维**：没有直接等价物。最接近的可能是 NestJS 的 decorator：

```ts
@Catch(AppError)
async appErrorHandler(request, exception) { ... }
```

🔵 **不需要理解 decorator 的实现原理**。只需要知道它让框架"知道"下面这个函数有特殊用途。

### 4.9 async / await

**Python 语法**：和你熟悉的 JS async/await 基本一样：

```python
async def lifespan(app: FastAPI):   # async function
    yield                            # 类似 generator，先不深入
```

**TypeScript 思维**：

```ts
async function lifespan(app: FastAPI) {
    // startup
    await someAsyncInit();
    // ready
}
```

Python 的 async/await 概念和 JS 非常接近——同样是"标记函数为异步，用 await 等待结果"。

### 4.10 `yield` — Python context manager

**Python 原代码**：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 启动时执行
    yield
    # Shutdown: 关闭时执行
```

**先这样理解**：`yield` 上面的代码在"服务启动时"运行，`yield` 下面的代码在"服务关闭时"运行。目前 Phase 0 两边都是空的。

**TypeScript 思维**：类似 Express 的服务启停，但没有直接语法对应。你可以先当成"启动钩子 + 关闭钩子"。

🔵 `yield` 的 generator/context manager 原理现在不需要深究。

---

## 5. T0001 — FastAPI Backend Skeleton

### 🟢 FastAPI 是什么

**先建立类比**：

| 你熟悉的 | FastAPI |
|----------|---------|
| **Express** (Node.js) | FastAPI 是 Web 框架——处理 HTTP 请求、路由、中间件 |
| **NestJS** | FastAPI 也提供类似 decorator 的路由注册 + 依赖注入 |
| **Next.js API Routes** | FastAPI 类似 Next.js 的 `app/api/` 目录，但更专业 |

**不完全等价**，但你可以先这样理解：

```text
Node.js 世界:  Express → HTTP Server
Python 世界:   FastAPI → ASGI Server (Uvicorn)
```

FastAPI 负责"定义路由、解析请求、校验参数、生成文档"，Uvicorn 负责"真正监听端口、收发 HTTP 字节流"。

### 🟢 app/main.py 是什么

**这是整个后端的入口文件。** 类比 Node.js 项目的 `server.ts` 或 `index.ts`。

当前 69 行代码做了 5 件事：

#### 第 1 步：导入依赖（lines 1-12）

```python
import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.errors import AppError, ErrorDetail, ErrorResponse
```

**Python 语法怎么读**：
- `import logging` → 导入标准库模块（类似 Node.js 的 `import fs from "fs"`）
- `from fastapi import FastAPI` → 从 fastapi 包里拿出 FastAPI 这个类（类似 `import { FastAPI } from "fastapi"`）
- `from app.api.router import api_router` → 从自己项目的 `app/api/router.py` 中导入 `api_router` 变量

**TypeScript 思维**：这些 import 就像你的 `server.ts` 顶部的 import 语句。

#### 第 2 步：Lifespan（lines 15-18）

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing to initialize at this stage
    yield
    # Shutdown: nothing to clean up at this stage
```

**它在干什么**：定义服务启动/关闭时要做什么。Phase 0 是空的（因为还没有数据库连接、模型加载等需要初始化的资源）。

**TypeScript 思维**：

```ts
// 类比 Express / Node server
server.on('listening', () => { /* startup */ });
server.on('close', () => { /* shutdown */ });
```

#### 第 3 步：创建 FastAPI 实例 + CORS（lines 22-35）

```python
app = FastAPI(
    title="DX-RAG",
    description="Enterprise knowledge base Q&A system",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**`app = FastAPI(...)` — 它是什么？**

`app` 是整个后端的"根对象"。类比：

```ts
const app = express();  // Express
// 或
const app = await NestFactory.create(AppModule);  // NestJS
```

之后所有的 middleware、路由、异常处理器都注册在这个 `app` 对象上。

**CORS 是干什么的？**

浏览器的安全机制：默认禁止 `localhost:3000`（前端）向 `localhost:8000`（后端）发请求（因为端口不同 = 不同 origin）。`CORSMiddleware` 告诉浏览器"我允许跨域请求"。v1 用 `["*"]` 允许所有来源，因为是本地/内网部署。

**TypeScript 思维**：

```ts
import cors from 'cors';
app.use(cors({ origin: '*' }));
```

#### 第 4 步：全局异常处理器（lines 43-65）

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
        ).model_dump(),
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(code="INTERNAL_ERROR", message="服务器内部错误", details={})
        ).model_dump(),
    )
```

**它在干什么**：两层安全网：
1. **第一层**：我们主动抛出的 `AppError`（如 "文件太大"）→ 转为规范的 JSON 错误响应
2. **第二层（兜底）**：所有未预期的异常（如 Python 的 `ValueError`）→ 记录日志，返回 500，不泄露 traceback

**TypeScript 思维**：

```ts
// Express middleware 风格
app.use((err, req, res, next) => {
    if (err instanceof AppError) {
        return res.status(err.httpStatus).json({ error: { ... } });
    }
    console.error(err);
    return res.status(500).json({ error: { code: 'INTERNAL_ERROR' } });
});
```

#### 第 5 步：挂载路由（line 68）

```python
app.include_router(api_router, prefix="/api")
```

**它在干什么**：把所有 API 路由挂载在 `/api` 前缀下。未来 `collections.py` 里定义了 `GET /collections`，实际 URL 就是 `GET /api/collections`。

**TypeScript 思维**：

```ts
app.use('/api', apiRouter);  // Express
```

### 🟢 APIRouter 是什么

**类比 Express Router**：

```text
Express:
  const router = express.Router()
  router.get('/users', ...)
  app.use('/api', router)

FastAPI:
  router = APIRouter()
  @router.get('/collections')
  app.include_router(router, prefix='/api')
```

当前 [api/router.py](../../backend/app/api/router.py) 已经注册了第一个真实路由（T0006 的 health check），其余业务路由还是注释：

```python
from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health")
def health_check() -> dict:
    """Basic availability probe (SPEC Section 6.2)."""
    return {"status": "ok"}


# Sub-routers will be included here in future tasks:
# from app.api.collections import router as collections_router
# ...
```

`health_check` 这个函数就是第 10 节要详细讲的第一个 endpoint。

### 🟢 Uvicorn — 你启动后端时真正发生了什么

**启动命令**：

```bash
uvicorn app.main:app
```

**逐段翻译**：

| 部分 | 含义 |
|------|------|
| `uvicorn` | ASGI 服务器程序（负责接收 TCP 连接、解析 HTTP） |
| `app.main` | 等价于 `from app.main import ...`——Uvicorn 去加载 `app/main.py` |
| `:app` | 从 `app/main.py` 中取出名为 `app` 的那个 FastAPI 实例 |

**完整启动流程图**：

```text
终端输入: uvicorn app.main:app
    │
    ▼
Uvicorn 启动
    │
    ├─ 1. Import "app.main" module → 执行 main.py 顶层代码
    │     ├─ 所有 import 被执行
    │     ├─ lifespan 函数被定义
    │     ├─ app = FastAPI(...) 实例被创建
    │     ├─ CORS、异常处理器、路由被注册
    │
    ├─ 2. 从 main.py 中取出 app 变量
    │
    ├─ 3. 将 FastAPI app 作为 ASGI application 启动
    │     → 监听 localhost:8000
    │
    ├─ 4. 调用 lifespan(app)
    │     → 执行 yield 之前的 startup 代码
    │
    └─ 5. 就绪，等待 HTTP 请求
```

**TypeScript 思维**：类比 `node server.js`，但你需要额外知道：**FastAPI 和 Uvicorn 是两个人**。FastAPI 定义"收到什么请求该怎么办"，Uvicorn 负责"真的去收请求"。

🔵 ASGI 是 Python 的异步服务器协议。第一遍不需要深入理解它——和 HTTP 协议一样，等需要底层调试时再学。

---

## 6. T0002 — Next.js Frontend Skeleton

> 你是前端开发者，这一节可以快速扫过。

### 你熟悉的和你需要知道的

[T0002 创建的骨架](../../frontend/) 和你用 `create-next-app` 搭出来的结构基本一样。

**你不需要重新学的**：React、TypeScript、Next.js App Router、npm、package.json、CSS。

**你需要了解的**（为后续 Phase 做准备）：

#### Ant Design 如何进入应用

在 [layout.tsx](../../frontend/app/layout.tsx) 中：

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

// ...
<ConfigProvider locale={zhCN}>
  {children}
</ConfigProvider>
```

`ConfigProvider` 用 React Context 向所有子孙组件提供全局配置。`locale={zhCN}` 确保 Ant Design 组件（Modal、Table）显示中文。

#### 当前项目是单页应用

v1 不使用 Next.js 的文件路由（`/kb`、`/upload` 等独立 URL）。所有功能在 `page.tsx` 一个页面内通过 React state 切换。这类似一个 Tab 切换的 SPA。

#### package-lock.json 必须提交

因为你要和 AI Coding Agent 协作。没有 lockfile，Agent 执行 `npm install` 可能安装不同版本，产生"Agent 那边跑得好好的，你这边不行"的诡异问题。

---

## 7. T0003 — Configuration

> 这是重点。你需要理解 Python 怎么做到和 Node.js `process.env` + `.env` 一样的效果——以及 Pydantic Settings 额外提供了什么。

### 🟢 从你熟悉的事情开始

在 Node.js 项目中，你可能这样处理配置：

```ts
// lib/config.ts
const config = {
    apiKey: process.env.API_KEY || (() => { throw new Error('Missing API_KEY') })(),
    port: parseInt(process.env.PORT || '3000'),
    maxUploadMb: parseInt(process.env.MAX_UPLOAD_MB || '50'),
};
```

这已经是"集中管理"了——所有配置在一个地方定义，有默认值。但它还有问题：

- 类型丢失：`process.env.PORT` 永远是 `string | undefined`
- 没有验证：`MAX_UPLOAD_MB=abc` 运行时才报错
- 没有 secret 保护：如果 console.log(config)，API Key 会明文显示

### 🟢 DX-RAG 的配置加载方式

[config.py](../../backend/app/core/config.py) 的核心代码：

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # API Keys
    DEEPSEEK_API_KEY: Optional[SecretStr] = Field(default=None)
    DASHSCOPE_API_KEY: Optional[SecretStr] = Field(default=None)

    # 应用
    APP_NAME: str = "dx-rag-demo"

    # ChromaDB
    CHROMA_COLLECTION: str = "knowledge_chunks"
    CHROMA_PERSIST_DIR: str = "chroma_db"

    # 文件上传
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Chunk 参数
    MAX_CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    # LLM
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 2048
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 2

    # 检索
    DEFAULT_TOP_K: int = 5
    TOP_K_MIN: int = 1
    TOP_K_MAX: int = 20

    # 历史
    MAX_HISTORY_LENGTH: int = 20

    # RAG Context
    MAX_CONTEXT_CHARS: int = 4000

    # 文件预览
    MAX_PREVIEW_CHARS: int = 5000

    # 混合检索
    MIN_RELEVANCE_SCORE: float = 0.30

    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])


# 模块级单例
settings = Settings()


def get_settings() -> Settings:
    return settings
```

### Python 语法怎么读

```python
class Settings(BaseSettings):        # 继承 BaseSettings
    APP_NAME: str = "dx-rag-demo"   # 字段名: 类型 = 默认值
    MAX_UPLOAD_SIZE_MB: int = 50    # int 就是 number
    LLM_TEMPERATURE: float = 0.2    # float 也是 number
```

**TypeScript 思维**：

```ts
class Settings extends BaseSettings {
    APP_NAME: string = "dx-rag-demo";
    MAX_UPLOAD_SIZE_MB: number = 50;
    LLM_TEMPERATURE: number = 0.2;
}
```

### 🟢 BaseSettings 解决了什么

`BaseSettings` 会**自动**从环境变量和 `.env` 文件中读取值。优先级：

1. **操作系统环境变量**（最高）
2. **`.env` 文件**
3. **Field 默认值**（最低）

所以你在服务器上设置 `export MAX_UPLOAD_SIZE_MB=100` 就能覆盖默认的 50，不需要改代码。

**TypeScript 思维**：你不需要手动写 `process.env.XXX || defaultValue` 了。Pydantic 帮你做了自动查找 + 类型转换。

### 🟢 SecretStr — API Key 为什么不能裸奔

```python
DEEPSEEK_API_KEY: Optional[SecretStr] = Field(default=None)
```

`SecretStr` 的行为：
- 被 `print()` 或序列化时 → 显示 `'**********'`
- 需要真实值时 → 调用 `.get_secret_value()`

**TypeScript 思维**：就像你永远不会把 `API_KEY` 放在前端 `NEXT_PUBLIC_*` 环境变量里——`SecretStr` 是后端侧的同样原则。

### 🟡 get_settings() — 为什么不用每次都 new Settings()

```python
settings = Settings()           # 模块加载时创建一次

def get_settings() -> Settings: # 返回同一个实例
    return settings
```

这确保整个应用共享同一个配置对象（单例）。从任何模块 `from app.core.config import settings` 拿到的都是同一个对象。

**TypeScript 思维**：

```ts
// config.ts
export const settings = loadConfig();  // 模块级单例，import 时只执行一次
```

---

## 8. T0004 — Error Handling

### 🟢 从你熟悉的事情开始

在 Node.js 后端中，你可能有这样的错误处理：

```ts
// Express error middleware
app.use((err, req, res, next) => {
    if (err instanceof ValidationError) {
        return res.status(400).json({ error: { code: 'VALIDATION_ERROR', message: err.message } });
    }
    console.error(err);
    res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Internal error' } });
});
```

DX-RAG 的 T0004 做了完全一样的事情——但用 Python 的异常机制来实现。

### 🟢 两层安全网

在 `main.py` 中注册了两个异常处理器：

**第一层：AppError（我们主动抛的）**

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
        ).model_dump(),
    )
```

当你（或任何服务）执行 `raise AppError("FILE_TOO_LARGE", details={"max_size_mb": 50})`，FastAPI 会自动：
1. 查错误目录，找到 FILE_TOO_LARGE → 413 + "文件大小超出限制"
2. 返回 `{"error": {"code": "FILE_TOO_LARGE", "message": "文件大小超出限制", "details": {"max_size_mb": 50}}}`

**第二层：兜底（Python 自带的异常）**

```python
@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(code="INTERNAL_ERROR", message="服务器内部错误", details={})
        ).model_dump(),
    )
```

如果 Python 代码自己抛了 `ValueError`、`KeyError`——先记录完整 traceback（开发者能看到），再返回 500（用户看不到 traceback）。

### 🟢 AppError 类

[errors.py](../../backend/app/core/errors.py) 的核心：

```python
class AppError(Exception):          # 继承 Python 原生 Exception
    def __init__(                    # __init__ = constructor
        self,
        code: str,                   # 错误码，如 "FILE_TOO_LARGE"
        *,
        details: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ):
        self.code = code
        _http_status, default_message = _get_catalog_entry(code)
        self.http_status = _http_status      # 自动查表得到 HTTP 状态码
        self.message = message or default_message
        self.details = details or {}
```

**Python 语法怎么读**：
- `class AppError(Exception):` — 定义一个类，继承 `Exception`
- `def __init__(self, code: str, *, details=None):` — constructor。`*` 后面的参数必须用名字传参
- 从 `_ERROR_CATALOG` 字典里查 `code` → 得到 `(http_status, chinese_message)`

**TypeScript 思维**：

```ts
class AppError extends Error {
    code: string;
    httpStatus: number;
    details: Record<string, any>;

    constructor(code: string, opts?: { details?: Record<string, any>; message?: string }) {
        const [httpStatus, defaultMessage] = ERROR_CATALOG[code] ?? [500, '内部错误'];
        super(opts?.message ?? defaultMessage);
        this.code = code;
        this.httpStatus = httpStatus;
        this.details = opts?.details ?? {};
    }
}
```

### 🟢 错误目录（Error Catalog）

```python
_ERROR_CATALOG: Dict[str, tuple] = {
    "INVALID_COLLECTION_NAME": (400, "知识库名称格式无效"),
    "COLLECTION_NOT_FOUND": (404, "知识库不存在"),
    "COLLECTION_ALREADY_EXISTS": (409, "知识库名称已存在"),
    "FILE_TOO_LARGE": (413, "文件大小超出限制"),
    "FILE_PARSE_ERROR": (422, "文件解析失败"),
    # ... 共 26 个
}
```

**它在干什么**：一个"错误码 → (HTTP 状态码, 中文消息)" 的映射表。统一定义的好处：所有地方 raise 同一个 `AppError("FILE_TOO_LARGE")`，返回的状态码和消息永远一致。

**TypeScript 思维**：类似你项目的 `errorCodes.ts` 常量文件。

### 🟢 Python Exception vs HTTP Error

| 概念 | 是什么 | 类比 |
|------|--------|------|
| Python Exception | 程序内部的异常信号 | TS `throw new Error()` |
| HTTP Error | 返回给客户端的 4xx/5xx | Express `res.status(400).json(...)` |
| try / except | 捕获异常 | try / catch |

**关键关系**：FastAPI Exception Handler 的作用就是 **把 Python Exception 翻译成 HTTP Error Response**。

---

## 9. T0005 — Pydantic / API Schema

> 这一节对你最重要。Pydantic 不是你熟悉的 TypeScript interface。

### 🟢 TypeScript interface 能做什么

```ts
interface QueryRequest {
    question: string;
    collection_name: string;
    top_k: number;
    history: ChatMessage[];
}
```

这是纯**编译时**类型检查。运行时你收到一个 JSON，TypeScript 不会自动帮你验证 `question` 是不是 string。

### 🟢 Pydantic BaseModel 额外能做什么

Pydantic 不仅是类型标注，它是**运行时**的。同样一个 QueryRequest：

```python
class QueryRequest(BaseModel):
    question: str = Field(description="User question")
    collection_name: str = Field(description="Target knowledge base name")
    top_k: int = Field(default=5, description="Number of chunks to retrieve (1-20)")
    history: List[ChatMessage] = Field(default_factory=list)
```

当 FastAPI 收到一个请求 body，它会：
1. **解析** JSON → Python dict
2. **验证** 每个字段的类型是否正确
3. **转换** "5"（字符串）→ 5（整数）如果类型是 int
4. **填充** 默认值（top_k 没传 → 自动填 5）
5. **拒绝** 多余字段或错误类型 → 返回 422

**先这样理解**：Pydantic Model ≈ TypeScript interface + Zod schema 的组合。

```ts
// TypeScript 等价思维（但本质不同）
import { z } from 'zod';

const QueryRequestSchema = z.object({
    question: z.string(),
    collection_name: z.string(),
    top_k: z.number().default(5),
    history: z.array(ChatMessageSchema).default([]),
});

type QueryRequest = z.infer<typeof QueryRequestSchema>;
```

这个类比并不完美，但它帮你理解：Pydantic 不止描述 shape，还在 runtime 做验证。

### 🟢 读取一段真实的 Pydantic 代码

```python
class UploadResponse(BaseModel):
    """POST /api/upload (200) response."""
    status: Literal["SUCCESS", "SUCCESS_WITH_WARNINGS"] = Field(...)
    message: str = Field(description="Human-readable result message")
    file_id: str = Field(description="UUID of the uploaded file")
    file_name: str = Field(description="Original filename")
    chunks: int = Field(description="Number of chunks generated")
    collection_name: str = Field(description="Target collection name")
    warnings: List[UploadWarning] = Field(default_factory=list)
```

**Python 语法怎么读**：
- `class UploadResponse(BaseModel):` — 定义一个数据模型，继承 BaseModel
- `status: Literal["SUCCESS", "SUCCESS_WITH_WARNINGS"]` — status 字段只能是这两个值之一
- `chunks: int` — chunks 是一个整数
- `warnings: List[UploadWarning]` — warnings 是一个 UploadWarning 数组
- `Field(default_factory=list)` — 默认值是空列表 `[]`

**TypeScript 思维**：

```ts
interface UploadResponse {
    status: "SUCCESS" | "SUCCESS_WITH_WARNINGS";
    message: string;
    file_id: string;        // UUID
    file_name: string;       // 原始文件名
    chunks: number;
    collection_name: string;
    warnings: UploadWarning[];
}
```

### 🟢 16 个 Pydantic 模型一览

| 模型 | 用途 | TypeScript 等价思维 |
|------|------|-------------------|
| `ChatMessage` | 单条对话（用户/助手） | `{ role: 'user' \| 'assistant', content: string }` |
| `CollectionCreate` | 创建知识库的请求 | `{ name: string }` |
| `CollectionRename` | 重命名请求 | `{ new_name: string }` |
| `CollectionItem` | 列表中一条知识库 | `{ name: string, file_count: number }` |
| `CollectionResponse` | 创建/删除的响应 | `{ message: string, name: string }` |
| `CollectionRenameResponse` | 重命名响应 | `{ message, old_name, new_name }` |
| `CollectionListResponse` | 知识库列表响应 | `{ collections: CollectionItem[] }` |
| `UploadWarning` | 上传警告 | `{ page_number: number, error_code: string }` |
| `UploadResponse` | 上传成功响应 | `{ status, message, file_id, chunks, ... }` |
| `SourceObject` | 一条来源引用 | `{ file_id, file_name, chunk_id, relevance_score }` |
| `QueryRequest` | QA 请求 | `{ question, collection_name, top_k?, history? }` |
| `QueryResponse` | QA 响应 | `{ answer, sources, query, collection_name }` |
| `FileItem` | 文件列表中一条 | `{ file_id, file_name, size, upload_time, ... }` |
| `FileListResponse` | 文件列表响应 | `{ collection_name, files: FileItem[] }` |
| `FilePreviewResponse` | 文件预览响应 | `{ file_id, content, preview_chars, total_chars }` |
| `FileDeleteResponse` | 文件删除响应 | `{ message, file_name, collection_name }` |

### 🟡 Pydantic 和 TypeScript 的关键区别

| 维度 | TypeScript interface | Pydantic BaseModel |
|------|---------------------|-------------------|
| **检查时机** | 编译时（build/CI） | 运行时（请求进来时） |
| **验证** | 不验证 | 自动类型验证 + 转换 |
| **默认值** | 无（需手动解构 + 默认值） | `Field(default=...)` |
| **序列化** | `JSON.stringify` | `.model_dump()` |
| **反序列化** | `JSON.parse` + 手动验证 | `Model(**json_dict)` 自动 |
| **文档生成** | 需额外工具 | 自动生成 OpenAPI JSON Schema |

**一句话总结**：TypeScript interface 帮你写好代码；Pydantic BaseModel 帮你在运行时挡住错误数据。

---

## 10. T0006 — Health Check API

> 这是整个项目第一个**真实可访问**的 endpoint。前面的章节都在讲"骨架"，从这一节开始，骨架上长出了第一块肉。

### 10.1 它是什么，为什么第一个实现它

SPEC Section 6.2 定义了一个极简契约：

```text
GET /api/health  →  200  {"status": "ok"}
```

**为什么需要它**：SPEC NFR Section 11.5 说 v1 不集成 APM/监控系统，health endpoint 就是"基本可用性探测"——外部调用方（浏览器、运维脚本、将来的前端）发一个 GET 就能知道后端活着。

**为什么它最应该第一个实现**：它不依赖任何东西。不碰 ChromaDB、不加载 embedding 模型、不调用 DeepSeek。对于学习来说，它是"从 URL 到 JSON"的最短完整路径。

### 10.2 逐行读真实代码

新增的 [backend/app/api/router.py](../../backend/app/api/router.py)：

```python
@api_router.get("/health")
def health_check() -> dict:
    """Basic availability probe (SPEC Section 6.2)."""
    return {"status": "ok"}
```

逐行解释：

| 代码 | 解释 | 前端类比 |
|------|------|---------|
| `@api_router.get("/health")` | decorator：给 `api_router` 注册一条 GET 路由。第 4.8 节说过，先理解成"给函数加标签" | `router.get('/health', handler)`（Express） |
| `def health_check() -> dict` | 普通函数（不是 `async def`）。因为它内部没有任何 `await`，同步函数就够了，FastAPI 会把它丢进线程池 | 普通 handler，不需要 async |
| `return {"status": "ok"}` | 返回一个 Python dict。FastAPI 自动序列化成 JSON，并设置 `Content-Type: application/json`（SPEC Section 6.1 要求） | `res.json({status: 'ok'})` |

**注意 return 的 dict 和浏览器收到的 JSON 之间的关系**：你 return 的是 Python dict，浏览器收到的是 JSON 字符串。中间"Python 对象 → JSON 字符串"的转换由 FastAPI 完成，不需要你手动 `json.dumps()`。这正是 FastAPI 和 Express 的关键区别之一——Express 里你得自己调 `res.json()`。

### 10.3 `/api/health` 这个完整路径是怎么拼出来的

两个部分：

1. `router.py` 里注册的是 `/health`
2. `main.py` 里 `app.include_router(api_router, prefix="/api")` 给所有路由加上前缀

所以完整路径 = `/api` + `/health` = `/api/health`。

这也是为什么 T0001 时代（router 全空时）访问 `/api/health` 会 404——FastAPI 找不到匹配的路由（T0006 实现后就不会了）。

### 10.4 为什么它只返回 `{"status": "ok"}`，不检查别的

你可能觉得"健康检查"应该顺便检查 ChromaDB 连不连得上、DeepSeek 有没有 API Key。但 SPEC 冻结的契约就是 `{"status": "ok"}`，T0006 的 Out of Scope 明确禁止：

- ChromaDB connectivity check
- embedding model loading check
- DeepSeek / Qwen API check
- filesystem diagnostics

**原因**：这是 **availability probe（可用性探测）**，不是 **readiness probe（就绪探测）**。它回答的问题是"进程还活着吗"，不是"所有依赖都健康吗"。后者的复杂度（超时、错误分类、部分健康状态）属于 SPEC 明确排除的监控/APM 范畴。

**工程启示**：Frozen SPEC 已经把 contract 定死了，实现者的任务是把 contract 精确落地，而不是"顺手增强"。加一个 `"version"` 字段看似无害，但会破坏"Response body 精确符合 SPEC"的验收标准。

### 10.5 如何验证它

实现后如何确认？两种方式：

```bash
# 方式一：curl（需要先启动后端：cd backend && uvicorn app.main:app --port 8000）
curl http://localhost:8000/api/health
```

```python
# 方式二：TestClient（FastAPI 自带的测试客户端，不开真实端口）
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
r = c.get("/api/health")
assert r.status_code == 200
assert r.json() == {"status": "ok"}
```

TestClient 类比前端测试里的 supertest——不用真开端口，直接在进程内发请求。

### 10.6 从 T0006 学到的规划教训

T0006 是 Phase 0 Gate Review **之后**才补进 TASKS.md 的。原因：SPEC 定义了 `GET /api/health`，但 TASKS.md 里没有任何 Task 负责实现它——T0001 的验收里甚至写着"expected 404 is acceptable at this stage"。

这暴露了一个规划原则：**SPEC 里每个 API contract 都必须有且只有一个 Task owner**。文档先行（SPEC）→ 任务分解（TASKS）→ 代码实现（backend）这条链上，任何一环漏掉，契约就落不了地。

---

## 11. 从前端请求到 FastAPI 的完整路径

> 整合 T0001–T0006，追踪一次（未来的）完整请求。

```text
1. 用户在浏览器输入问题，点击发送
       │
2.     ▼
   Next.js (localhost:3000)
   React 组件触发 fetch("/api/query", { method: "POST", body: ... })
       │                                    ↑
       │  HTTP POST /api/query                │
       ▼                                    │
3. Uvicorn (ASGI Server, port 8000)         │
   接收 TCP 连接，解析 HTTP 字节流            │
       │                                    │
       ▼                                    │
4. FastAPI app (main.py)                    │
   检查 URL path: /api/query                │
       │                                    │
       ▼                                    │
5. CORS Middleware                          │
   允许 localhost:3000 的跨域请求            │
       │                                    │
       ▼                                    │
6. APIRouter (prefix="/api")                │
   匹配 /query → query.py 的 endpoint        │
       │                                    │
       ▼                                    │
7. Pydantic 验证 (QueryRequest)              │
   检查 question 是 string、top_k 在 1-20     │
   验证失败 → 422                            │
       │                                    │
       ▼                                    │
8. Endpoint function                        │
   执行业务逻辑 (Phase 3-8 实现)              │
       │                                    │
       ▼                                    │
9. Pydantic 序列化 (QueryResponse)           │
   Python 对象 → JSON                        │
       │                                    │
       ▼                                    │
10. 响应原路返回                              │
    FastAPI → Uvicorn → HTTP → fetch ───────┘
       │
       ▼
11. Next.js 收到响应，更新 React state
    用户看到答案
```

**Phase 0 当前实现了什么**：步骤 3-6 的基础设施已就绪。步骤 7-9 的类型定义已完成。步骤 8 的业务逻辑由后续 Phase 实现。

---

## 12. Python 与 TypeScript 对照表

> 只收录 Phase 0 真实出现的内容。

| Python | TypeScript / Node 类比 | 差异 / 注意 | 在 DX-RAG 哪里出现 |
|--------|----------------------|-----------|------------------|
| `str` | `string` | | schemas.py、config.py 到处可见 |
| `int` | `number` | Python 区分 `int`/`float`，TS 只有 `number` | config.py |
| `float` | `number` | | config.py |
| `bool` | `boolean` | Python 的是 `True`/`False`（大写） | |
| `list[str]` | `string[]` | | config.py: `List[str]` |
| `dict[str, any]` | `Record<string, any>` | | errors.py: `Dict[str, Any]` |
| `Optional[str]` | `string \| null \| undefined` | | config.py |
| `None` | `null`（大部分语境）/ `void`（函数返回值） | Python 没有 `undefined` | 到处可见 |
| `def` | `function` / method | | 所有函数定义 |
| `class` | `class` | | 所有类定义 |
| `self` | `this` | Python 必须显式写在方法参数里 | errors.py, config.py |
| `__init__` | `constructor` | Python 对象在 `__new__` 时就创建了 | errors.py |
| `import X` | `import X from ...` | Python 可以只 import module 不 import 具体项 | main.py |
| `from X import Y` | `import { Y } from X` | Python 用 `.` 分隔路径 | main.py, router.py |
| `BaseModel` | TS `interface` + Zod `z.object()` | Pydantic 是 runtime + compile-time | schemas.py, errors.py |
| `BaseSettings` | `process.env` + 类型验证库 | 自动读环境变量 + 类型转换 + 默认值 | config.py |
| `@decorator` | 无直接等价，类似 NestJS decorator | 给函数/类附加框架行为 | main.py |
| `try / except` | `try / catch` | | |
| `async / await` | `async / await` | 概念基本相同 | main.py |
| `yield` | 无直接等价 | Context manager，先理解成"启动/关闭钩子" | main.py |
| `Field(...)` | 类似 Zod 的 `.describe()` | Pydantic 字段元数据 | schemas.py, errors.py |

---

## 13. 项目目录：用前端工程思维理解

```text
backend/app/
├── main.py             ← 后端入口，类比 server.ts / index.ts
├── api/                ← 类比 Next.js 的 app/api/ 目录
│   ├── __init__.py
│   └── router.py       ← 主路由，类比 Express Router
├── core/               ← 类比 lib/ 或 utils/
│   ├── __init__.py
│   ├── config.py       ← 类比 config.ts（环境变量 → 类型安全对象）
│   └── errors.py       ← 类比 errorCodes.ts + errorHandler.ts
├── models/             ← 类比 types/api.ts
│   ├── __init__.py
│   └── schemas.py      ← API 的 Request/Response 类型定义
└── services/           ← 类比 services/ 或 useCases/
    └── __init__.py     ← 目前空，未来放业务逻辑
```

### 每个目录的职责边界

| 目录 | 职责 | 我不应该在这里看到什么 |
|------|------|---------------------|
| `api/` | HTTP 层——路由定义、参数解析、返回响应 | 不应该有数据库操作、文件解析逻辑 |
| `core/` | 基础设施——配置、错误、接口定义 | 不应该有业务逻辑、API 特定代码 |
| `models/` | 数据结构——API 契约 | 不应该有函数实现 |
| `services/` | 业务逻辑——文档处理、检索、QA | 不应该直接处理 HTTP Request/Response |

### 空 `__init__.py` 是干什么的

Python 要求：一个目录要被 `import`（如 `from app.core import config`），必须包含一个 `__init__.py` 文件。它可以是空的——它的存在本身就是 "这个目录是 Python package" 的声明。

**TypeScript 思维**：类比 `index.ts` 的 re-export 文件，但 Python 的 `__init__.py` 即使空着也有作用（标记 package）。

---

## 14. Phase 0 关键代码阅读路线

> 不要一次读所有文件。按这个顺序来。

### 第一遍阅读（目标：看懂后端是怎么启动的）

#### 1. [backend/app/main.py](../../backend/app/main.py) — 69 行

**第一遍只看**：
- import 区域（知道引入了什么）
- `app = FastAPI(...)` — 入口
- `app.include_router(api_router, prefix="/api")` — 理解 `/api` 前缀怎么来的

**暂时跳过**：
- `@asynccontextmanager` 语法细节
- `@app.exception_handler` decorator 原理

**能回答这些就算看懂**："整个后端的入口是什么？CORS 在哪配置？`/api` 前缀在哪定义？"

#### 2. [backend/app/api/router.py](../../backend/app/api/router.py) — 17 行

**第一遍只看**：`api_router = APIRouter()` + `@api_router.get("/health")` 这个真实路由 + 注释中的未来 import。

**能回答这些就算看懂**："目前唯一真实的 API 是哪个？它的完整路径是什么？未来 API 会怎么添加？"

#### 3. [backend/app/core/config.py](../../backend/app/core/config.py) — 111 行

**第一遍只看**：
- `class Settings(BaseSettings)` 下面的 22 个字段
- `settings = Settings()` 这一行（最后几行）
- `get_deepseek_key()` 方法

**暂时跳过**：
- `field_validator` 细节
- `model_config` 细节

**能回答这些就算看懂**："配置从哪里来？`MAX_UPLOAD_SIZE_MB` 的默认值是多少？怎么读到真实的 API Key？"

#### 4. [backend/app/core/errors.py](../../backend/app/core/errors.py) — 114 行

**第一遍只看**：
- `_ERROR_CATALOG` 字典（理解有哪些错误码）
- `AppError.__init__` 方法（理解 error code → HTTP status 的查找逻辑）

**暂时跳过**：
- Pydantic `BaseModel` 的 `model_dump()` 方法

**能回答这些就算看懂**："如果我想抛一个'文件不存在'的错误，应该用什么 code？前端的 error parser 应该怎么解析？"

#### 5. [backend/app/models/schemas.py](../../backend/app/models/schemas.py) — 189 行

**第一遍只看**：
- `class ChatMessage` — 最简单的模型
- `class QueryRequest` — 理解 Pydantic 模型的结构
- `class UploadResponse` — 理解 `Literal` 类型的用法

**暂时跳过**：
- 每个 `Field(description=...)` 的具体内容

**能回答这些就算看懂**："QA 请求需要哪些字段？上传成功后的 Response 长什么样？这些模型和 TypeScript interface 有什么关键不同？"

---

## 15. 我现在只需要掌握的 10 件事

1. **`self` ≈ `this`**，但 Python 要求你显式写在方法参数列表的第一个位置

2. **`__init__` ≈ `constructor`**，实例化时自动调用

3. **Uvicorn 是服务器，FastAPI 是 Web 框架**——类似 Node.js 里 Express 处理路由、底层 http 模块监听端口

4. **`app/main.py` = 后端入口文件**——类比 `server.ts`

5. **`BaseSettings`** 自动从环境变量和 `.env` 文件读取配置，不需要手动 `process.env.xxx`

6. **Pydantic `BaseModel` ≠ TypeScript `interface`**——Pydantic 在 runtime 做验证和转换，不只是编译时检查

7. **`AppError("FILE_TOO_LARGE")`** 会被全局 handler 自动转换为 `{"error": {"code": "FILE_TOO_LARGE", "message": "文件大小超出限制"}}`

8. **`/api` 前缀**来自 `main.py` 中 `app.include_router(api_router, prefix="/api")`

9. **`__init__.py`** 即使是空文件也不可少——它告诉 Python 这个目录是一个 package

10. **API Key 永远只在 Backend**——通过环境变量和 `SecretStr` 保护，前端不持有任何第三方 API Key

---

## 16. 现在可以暂时不懂的内容

> 以下内容不影响你理解 Phase 0 的核心。以后遇到实际需求再回来学。

- **ASGI protocol 细节** — Uvicorn 和 FastAPI 之间的通信协议。先当成"类似 Node.js HTTP server 和 Express 的关系"就够用
- **decorator 实现原理** — `@app.exception_handler` 怎么工作的。先当成"框架给函数加标签"就行
- **Pydantic internals** — model 验证/序列化的底层机制。先知道 `.model_dump()` 就是"转成 dict"就够了
- **Python descriptor / metaclass** — Phase 0 完全没用到
- **Dependency injection** — FastAPI 的 `Depends()` Phase 0 还没用
- **FastAPI internal routing machinery** — 路由匹配的底层算法
- **Python async event loop** — `asyncio` 的事件循环机制
- **Context manager protocol** — `yield` 在 `@asynccontextmanager` 背后的 `__enter__`/`__exit__` 机制
- **SettingsConfigDict 的细节** — `case_sensitive=True` 具体是什么意思、还有哪些配置项

---

## 17. 常见问题：以前端开发者视角回答

### Q1: 为什么 Python 文件里到处有 `__init__.py`？它是干什么的？

**简单回答**：它告诉 Python "这个目录是一个 package，可以被 import"。

如果没有 `app/core/__init__.py`，你就不能写 `from app.core import config`。

**前端类比**：不完全等价，但可以类比 `index.ts` barrel export 文件——它标识一个目录是一个模块入口。但 Python 的即使是空文件也有作用（不像 TS 的 index.ts 必须包含 export 才有意义）。

### Q2: `self` 为什么必须写在参数里？

**简单回答**：这是 Python 设计哲学——"显式优于隐式"。Python 的设计者认为方法第一个参数应该明确说出来，而不是像 JS 的 `this` 那样隐式传入。

```python
# Python: self 是显式的
class Foo:
    def method(self, x):  # self 在参数列表里
        self.x = x        # 访问实例属性也显式写 self
```

### Q3: 为什么 Python 有 type hint 但运行时还能是动态类型？

**简单回答**：Python type hints **不强制运行时检查**。它们给 IDE 和类型检查器（mypy / pyright）用，但 Python 解释器自己不管。这和 TS 不同——TS 编译时会报错拒绝运行，Python 只会"建议"你写类型。

### Q4: Pydantic 和 TypeScript interface 到底有什么区别？

**核心区别**：TypeScript interface 在编译后**消失**——运行时没有任何接口信息。Pydantic model 在运行时**仍然存在**——它可以验证数据、转换类型、生成 JSON Schema。

**类比**：TypeScript interface = 设计图纸（建完房子就没了）。Pydantic BaseModel = 安检门（每个通过的请求都要被检查）。

### Q5: FastAPI 和 Express 有什么区别？

| 维度 | Express | FastAPI |
|------|---------|---------|
| **路由定义** | `app.get('/path', handler)` | `@app.get('/path')` 或 `@router.get('/path')` |
| **参数验证** | 手动或第三方库（Joi, Zod） | 内置（基于 Pydantic） |
| **类型标注** | TypeScript（编译时） | Python type hints + Pydantic（运行时） |
| **API 文档** | 需要 swagger-jsdoc 等 | 自动生成 OpenAPI（`/docs`） |
| **异步** | 原生 Promise/async | asyncio + async/await |
| **服务器** | 内置 http 模块 | 需要 ASGI 服务器（Uvicorn） |

### Q6: Uvicorn 和 FastAPI 为什么不是一个东西？

**简单回答**：FastAPI 是"业务逻辑框架"（定义路由、解析参数、返回响应），Uvicorn 是"网络服务器"（监听端口、收发 HTTP 字节流）。它们之间通过 ASGI 协议通信。

**前端类比**：就像 Next.js 和 Node.js http 模块的关系——Next.js 处理 React 渲染和路由，Node.js http 负责底层 TCP 连接。但 Python 把它们拆成了两个独立程序。

### Q7: `BaseSettings` 为什么不能直接 `os.getenv()`？

`os.getenv("KEY")` 只能读到一个字符串。`BaseSettings` 额外做了：
- **类型转换**：`MAX_UPLOAD_SIZE_MB` 是 int，自动把 `"50"` 转成 `50`
- **默认值**：环境变量没设置时用 default
- **验证**：可以检查值是否合法
- **集中管理**：22 个参数在一个地方定义，IDE 可以自动补全

### Q8: 后端为什么需要统一 ErrorResponse？

因为前端只需要写**一个** error parser：

```ts
// 前端统一的错误处理
const response = await fetch('/api/upload', { ... });
if (!response.ok) {
    const { error } = await response.json();
    // error.code   → "FILE_TOO_LARGE"
    // error.message → "文件大小超出限制"
    // error.details → { max_size_mb: 50 }
    handleError(error);
}
```

而不是每个 API 各自猜格式。

---

## 18. Debug：用我已有经验迁移

### ModuleNotFoundError ←→ Module not found

| 症状 | Node.js | Python |
|------|---------|--------|
| 找不到模块 | `Error: Cannot find module './config'` | `ModuleNotFoundError: No module named 'app.core.config'` |
| 常见原因 | 路径写错 / 文件不存在 | 路径写错 / `__init__.py` 缺失 / PYTHONPATH 问题 |
| 检查方式 | `ls` 看文件在不在 | 检查目录是否有 `__init__.py`，路径拼写是否正确 |
| 运行目录 | 从项目根目录 | 从 `backend/` 目录运行（或设置 PYTHONPATH） |

### pip install ←→ npm install

| 操作 | npm | pip |
|------|-----|-----|
| 安装依赖 | `npm install` (读 package.json) | `pip install -r requirements.txt` (读 requirements.txt) |
| 声明文件 | `package.json` | `requirements.txt` |
| Lock 文件 | `package-lock.json` | Python 没有统一的 lockfile 标准（可用 `pip freeze > ...`） |
| 安装到哪里 | `node_modules/` | 系统 Python site-packages 或虚拟环境 |
| 虚拟环境 | `node_modules/.bin/` | `venv/`（需要手动创建和激活） |

### 如何检查 import 是否成功

```bash
# Node.js 等价: node -e "require('./config')"
cd backend
python -c "from app.core.config import settings; print(settings.APP_NAME)"
# 输出 "dx-rag-demo" 表示成功
```

### 如何定位错误

**Python traceback 怎么读**（Node.js 开发者也看 stack trace）：

```text
Traceback (most recent call last):
  File "app/main.py", line 68, in <module>      ← 从这里开始
    app.include_router(api_router, prefix="/api")
  File "app/api/router.py", line 3, in <module>  ← 跳到这里
    from app.core.config import settings
ModuleNotFoundError: No module named 'app.core.config'  ← 这里崩了
```

**读法**：从下往上读——最底部是最终错误，往上是调用链。和 Node.js stack trace 读法一样。

---

## 19. 6 道基础自测题

**Q1**：`backend/app/core/config.py` 最后两行是什么？为什么 `settings = Settings()` 要放在模块级别而不是函数内部？

**Q2**：如果前端发了一个 POST 请求，body 里 `top_k` 的值是 `"abc"`（字符串），Pydantic 会怎么处理？TypeScript interface 会怎么处理？

**Q3**：以下代码中，哪个是正确的 import 方式？为什么？
```python
# A
import app.main

# B
from app.main import app

# C
from backend.app.main import app
```

**Q4**：如果我想新增一个配置参数 `MAX_FILE_COUNT = 100`，应该在哪个文件、哪个类的哪个位置添加？

**Q5**：前端的 error parser 应该怎么写？读完 `errors.py` 后，用 TypeScript 写出一个通用的错误处理函数签名。

**Q6**：`GET /api/health` 的完整路径是哪两部分拼出来的？浏览器收到的 JSON 是哪个环节从 Python dict 序列化出来的？为什么 T0006 明确禁止在 health 里检查 ChromaDB / DeepSeek？

---

## 20. 4 个小练习

### 练习 1：手工翻译

把以下 Python 代码翻译成 TypeScript：

```python
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(description="Message role")
    content: str = Field(description="Message content")

class QueryRequest(BaseModel):
    question: str = Field(description="User question")
    collection_name: str = Field(description="Target KB name")
    top_k: int = Field(default=5)
    history: List[ChatMessage] = Field(default_factory=list)
```

**要求**：分别用 (a) 纯 TypeScript interface 和 (b) Zod schema 两种方式。

### 练习 2：画出请求流程

不参考资料，画一张图：从前端 `fetch("/api/query", ...)` 到 FastAPI 返回 Response 的完整路径。标注每个环节在项目中对应的文件。

### 练习 3：不看代码解释

找一个同事（或者自言自语），不看项目代码，用简单语言解释：
- `self` 是什么？为什么它和 `this` 不一样？
- `__init__` 是什么？
- Pydantic 和 TypeScript interface 有什么区别？

### 练习 4：动手摸第一个 endpoint

1. 启动后端（`cd backend && uvicorn app.main:app --port 8000`），用浏览器或 curl 访问 `http://localhost:8000/api/health`
2. 观察响应的 `Content-Type` 响应头是什么
3. 再访问 `http://localhost:8000/health`（少了 `/api`），观察 404 长什么样——它和第 8 节讲的统一错误格式有什么关系？
4. （可选）临时把 `router.py` 里的返回值改成 `{"status": "ok", "foo": 1}`，重启后再访问一次，确认 FastAPI 自动序列化任意 dict——然后把代码改回来

---

## 21. Phase 0 快速复习卡

### 一句话总结

Phase 0 搭建了 DX-RAG 的项目骨架——后端 FastAPI 能启动、前端 Next.js 能启动、配置集中管理、错误统一格式、API 数据契约已定义。

### Python 5 个关键词（Phase 0 最高频）

| 关键词 | 一句话解释 |
|--------|----------|
| `self` | 方法的第一个参数，≈ `this`，但必须显式写 |
| `__init__` | ≈ constructor |
| `@decorator` | 给函数/类加"框架标签" |
| `BaseModel` | Pydantic 的数据模型 = TS interface + Zod 验证 |
| `BaseSettings` | 自动从环境变量读配置的模型 |

### Backend 5 个关键词

| 概念 | 一句话解释 |
|------|----------|
| **FastAPI** | Python Web 框架，≈ Express |
| **Uvicorn** | ASGI 服务器，真正监听端口收 HTTP 请求 |
| **APIRouter** | 路由组，≈ Express Router |
| **AppError** | 统一业务异常，携带 error code → 自动查表得到 HTTP status + 中文消息 |
| **settings** | 模块级配置单例，从 `.env` / 环境变量自动加载 |

### 最重要的流程

```text
前端 fetch("/api/xxx")
  → Uvicorn (收 HTTP)
    → FastAPI app (路由匹配)
      → CORS check
        → APIRouter prefix="/api"
          → Pydantic 验证 Request
            → Endpoint handler
              → Pydantic 序列化 Response
                → 原路返回前端
```

### 3 个最容易混淆的概念

1. **Uvicorn vs FastAPI** — Uvicorn 是服务器（监听端口），FastAPI 是框架（处理路由）。类比：Node.js `http.createServer()` vs `express()`
2. **Pydantic vs TypeScript interface** — Pydantic 运行时还在，TS interface 编译后就没了。Pydantic 不"描述"类型，它"执行"验证
3. **`__init__.py` vs 普通 .py** — `__init__.py` 是 package 标记文件，让它所在的目录可以被 import。普通的 `.py` 是 module

---

## 22. 🔵 进阶阅读

> 以下内容来自原学习文档中的高级章节。**当前第一遍学习可以跳过。** 等你 Python/后端能力提升后，可以回来阅读。

### 22.1 FastAPI Lifespan 的完整机制

`@asynccontextmanager` 装饰的 `lifespan` 函数是一个 async context manager。FastAPI 在启动时进入 `yield` 之前的代码，关闭时执行 `yield` 之后的代码。这种模式替代了旧版 FastAPI 的 `@app.on_event("startup")` / `@app.on_event("shutdown")` 装饰器。

优势：可以管理有状态资源（例如用一个变量保存数据库连接引用），在 shutdown 时确保释放。而 `@app.on_event` 方式下，不同 event handler 之间的状态共享比较困难。

Phase 0 中 lifespan 是空的，但后续 Phase 如果需要初始化 ChromaDB 连接或加载模型，代码会加在 `yield` 之前。

### 22.2 CORS 的安全考虑

Phase 0 使用 `allow_origins=["*"]` 是因为 v1 的部署假设是本地/可信内网环境。生产环境中，应该通过 `CORS_ORIGINS` 配置项限制为具体的域名。

SPEC Section 8.1 定义了 `CORS_ORIGINS` 参数（List[str]），但 main.py 中没有使用它——这是 T0003 和 T0001 之间的已知不对称（config 提供了参数，但 main.py 没有消费它）。

### 22.3 Python Module 搜索路径

当 Python 执行 `from app.core.config import settings` 时，它会沿着 `sys.path` 搜索 `app` package。默认情况下，`sys.path` 包含当前工作目录。这就是为什么需要在 `backend/` 目录下运行 `uvicorn app.main:app`——如果从项目根目录运行，Python 可能找不到 `app` module。

### 22.4 配置管理的设计权衡

为什么使用 Pydantic BaseSettings 而不是更简单的 `os.getenv()`：

| 方案 | 优点 | 缺点 |
|------|------|------|
| `os.getenv()` | 简单，无依赖 | 无类型转换、无默认值管理、无验证 |
| 自定义 config module | 灵活 | 需要自己处理所有边界情况 |
| Pydantic BaseSettings | 类型安全、自动加载、验证、secret 保护 | 引入额外依赖 |

DX-RAG 选择 BaseSettings 是因为 22 个参数分散在后端几乎所有模块中，需要一个"统一真相来源"。

### 22.5 Error Model 的 Pydantic 序列化

`ErrorResponse` 和 `ErrorDetail` 都继承自 `BaseModel`。`model_dump()` 方法将它们转换为 Python dict，然后 `JSONResponse` 将其序列化为 JSON。

设计上 T0004 将 Error model 放在 `errors.py` 中，而不是 `schemas.py` 中，因为 error handling 是基础设施而非 API contract。但在整个应用中，只有一处定义了 ErrorResponse 的结构。

### 22.6 v1 没有 Universal Success Response Wrapper

SPEC Section 7.7 明确规定 v1 不得引入统一的成功响应包裹器（如 `{"data": ..., "success": true}`）。每个 API endpoint 的 Response 格式是独立的，由各自的 Pydantic model 定义。这是为了防止过度抽象——当项目很小（v1 只有十几个 endpoint）时，统一的 wrapper 增加的复杂度大于它带来的收益。

---

## 学习过程中发现的待确认事项

> 以下是在编写学习文档过程中发现的值得关注的细节，不构成实现缺陷。

| # | 文件 | 现象 | 为什么值得确认 |
|---|------|------|---------------|
| 1 | `main.py:31` vs `config.py:31` | 配置中定义了 `CORS_ORIGINS: List[str]`，但 `main.py` 硬编码了 `allow_origins=["*"]` | 后续 Task 应该让 main.py 消费 config 中的 CORS_ORIGINS |
| 2 | `schemas.py` | 定义了 `ChunkRecord`/`SearchResult` 的引用，但实际定义在 T0101 的 `vector_store.py` 中 | 需要确认这些类型是应该统一到 schemas.py，还是分属不同层 |
| 3 | `router.py` | T0006 已注册 `GET /api/health`，其余子路由仍是注释 | Phase 4 开始会逐步取消注释并加入真正的 router |
| 4 | `services/` | 空目录，Phase 0 没有创建任何 service 代码 | Phase 3 开始才会在此目录添加业务逻辑 |

---

> **下一步**：Phase 1 学习文档 → [phase-01-vectorstore.md](./phase-01-vectorstore.md)（T0101 已完成）
