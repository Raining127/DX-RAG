# Phase 0 — Project Bootstrap 学习笔记

---

## 1. Phase 0 到底解决了什么问题

### 为什么一个项目不能一开始就直接写 RAG

想象你要盖一栋楼。地基、水电管道、墙壁粉刷可以同时进行吗？可以——但前提是你已经画好了建筑图纸，确定了每面墙的位置。

Phase 0 就是 **画建筑图纸的过程**。

如果跳过 Phase 0 直接开始写 RAG 检索逻辑，你会遇到：

- **配置散落各处**: `DEEPSEEK_API_KEY` 在 `qa.py` 里硬编码，`CHROMA_PERSIST_DIR` 在 `vector_store.py` 里写死。改一个配置要搜遍整个项目。
- **错误格式混乱**: 某个 endpoint 返回 `{"error": "something wrong"}`，另一个返回 `{"detail": "bad request"}`。前端同学要写 N 种不同的错误解析逻辑。
- **代码无处安放**: 新建一个 API endpoint，不知道该放在哪个目录。"放 `backend/` 根目录？`backend/api/`？`backend/routers/`？"
- **依赖冲突**: A 同事 pip install 了 chromadb 0.4.15，B 同事装了 0.5.0，代码在两边表现不一致。

Phase 0 解决的就是这些问题。它为之后的所有 Phase 提供了：

| 基础能力 | 对应 Task | 后续谁依赖它 |
|----------|----------|------------|
| 项目目录结构 | T0001, T0002 | 所有后续 Task 都知道代码放哪 |
| 配置管理 | T0003 | 所有需要读取配置的模块 |
| 错误处理基础 | T0004 | 所有 API endpoint |
| 数据模型定义 | T0005 | 所有需要定义 Request/Response 的 Task |
| 依赖声明 | T0001, T0002 | 所有需要引入新库的 Task |

---

## 2. Phase 0 完成了哪些 Tasks

### T0001 — Backend Application Skeleton

**Goal**: 初始化 FastAPI 应用骨架——创建目录结构、FastAPI 实例、CORS 中间件、Router 占位。

**实际产生的能力**: 可以执行 `uvicorn app.main:app` 启动一个 FastAPI 服务。虽然没有任何业务 endpoint，但应用能成功启动，CORS 已配置，Router 结构已就位。

**为什么后续阶段依赖它**: 后续所有 Backend Task 都需要往 `app/api/` 下添加 Router、往 `app/core/` 下添加核心模块、往 `app/services/` 下添加业务逻辑。T0001 定义了"代码应该放在哪里"。

### T0002 — Frontend Application Skeleton

**Goal**: 初始化 Next.js 14 App Router 项目——安装依赖、创建 `layout.tsx`、`page.tsx`、`globals.css`。

**实际产生的能力**: 可以执行 `npm run dev` 启动 Next.js 开发服务器，浏览器访问 `localhost:3000` 看到 "DX-RAG" 标题。

**为什么后续阶段依赖它**: 后续所有 Frontend Task 都需要在这个骨架之上添加组件（`components/`）、API 客户端（`lib/`）、业务页面逻辑。

### T0003 — Configuration Foundation

**Goal**: 实现 Pydantic `BaseSettings` 配置模型，从环境变量加载 SPEC Section 8.1 定义的 22 个参数。

**实际产生的能力**: 任何模块都可以通过 `from app.core.config import settings` 获取类型安全、有默认值、可被环境变量覆盖的配置对象。

**为什么后续阶段依赖它**: 所有需要读取配置的模块——VectorStore 需要 `CHROMA_PERSIST_DIR`、Embedding 需要 `EMBED_MODEL`、LLM Client 需要 `DEEPSEEK_API_KEY`——都依赖 T0003。

### T0004 — Unified Error Response & Global Exception Handler

**Goal**: 实现统一错误响应格式（`{error: {code, message, details}}`）和全局 FastAPI 异常处理器。

**实际产生的能力**: 任何模块都可以通过 `raise AppError("FILE_TOO_LARGE", details={"max_size_mb": 50})` 抛出一个带有正确 HTTP 状态码、中文错误消息和结构化详情的错误。未预期的异常会被全局 handler 捕获，返回 `INTERNAL_ERROR` 而不泄露 traceback。

**为什么后续阶段依赖它**: 所有 API endpoint 的错误处理都依赖 T0004 定义的 `AppError` 类和全局 handler。

### T0005 — Pydantic Data Models & API Schemas

**Goal**: 定义所有与 SPEC Section 6 API Contracts 和 Section 7 Data Models 对齐的 Pydantic Request/Response 模型。

**实际产生的能力**: 其他模块可以 import `CollectionCreate`、`UploadResponse`、`QueryRequest`、`SourceObject` 等类型，在编写 endpoint 或 service 时使用它们定义数据契约。

**为什么后续阶段依赖它**: 所有 API endpoint 的 Request 解析和 Response 序列化都依赖这些 Pydantic 模型。例如 T0101（VectorStore ABC）需要 `ChunkRecord` 类型；T0805（Query endpoint）需要 `QueryRequest` / `QueryResponse`。

---

## 3. Phase 0 最终目录结构解析

以下是 Phase 0 完成后与学习有关的真实目录结构（省略 `node_modules/`、`.next/`、`__pycache__/` 等自动生成内容）：

```
dx-rag/
├── CLAUDE.md                         # Agent 操作契约（SPEC > TASKS > CLAUDE）
├── .gitignore                        # Git 忽略规则
│
├── backend/
│   ├── app/
│   │   ├── __init__.py               # 标记 app/ 为 Python package
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── api/
│   │   │   ├── __init__.py           # 标记 api/ 为 Python package
│   │   │   └── router.py            # 主 APIRouter，聚合子 router
│   │   ├── core/
│   │   │   ├── __init__.py           # 标记 core/ 为 Python package
│   │   │   ├── config.py            # Settings 配置类（T0003）
│   │   │   └── errors.py            # 错误模型 + 错误码目录（T0004）
│   │   ├── models/
│   │   │   ├── __init__.py           # 标记 models/ 为 Python package
│   │   │   └── schemas.py           # Pydantic 数据模型（T0005）
│   │   └── services/
│   │       └── __init__.py           # 标记 services/ 为 Python package（空）
│   ├── requirements.txt              # Python 依赖声明
│   └── .env.example                  # 环境变量模板
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                # Next.js Root Layout（T0002）
│   │   ├── page.tsx                  # Next.js 首页（T0002）
│   │   └── globals.css               # 全局样式
│   ├── package.json                  # Node 依赖声明 + npm scripts
│   ├── package-lock.json             # 精确版本锁定
│   ├── next.config.js                # Next.js 配置
│   └── tsconfig.json                 # TypeScript 配置
│
└── docs/
    ├── SPEC.md                       # 产品规格（FROZEN）
    ├── TASKS.md                      # 任务分解
    └── learning/                     # 学习文档（本目录）
```

### 逐项解释

#### `backend/app/` — Python Package 根

所有 Backend 代码都在这个 package 下。`__init__.py` 是空的——它的作用仅仅是告诉 Python："这个目录是一个 package，可以被 import"。

当你写 `from app.core.config import settings` 时，Python 会沿着 `app` → `app/core` 的 package 路径寻找 `config.py` 中的 `settings` 对象。

#### `backend/app/main.py` — 应用入口

这是整个 Backend 的启动文件。后续所有 Phase 的 API endpoint 都是通过 `app.include_router()` 挂载到这上面的。它定义了：

- FastAPI 应用实例（`app = FastAPI(...)`）
- CORS 中间件
- 全局异常处理器
- `/api` 前缀的路由聚合

#### `backend/app/api/router.py` — 路由聚合器

当前只有注释掉的占位 import。未来每个 API 模块（collections、upload、query、files）会在这里被 import 并 `include_router`，然后由 `main.py` 统一挂载到 `/api` 前缀下。

#### `backend/app/core/` — 核心基础设施

这个目录放的是"与业务无关、但整个应用都需要的"东西。目前有：

- `config.py` — 配置加载
- `errors.py` — 错误定义

未来还会添加 `vector_store.py`（VectorStore 接口）等。

#### `backend/app/models/` — 数据模型

当前有 `schemas.py`——Pydantic 模型定义。注意：这些模型是 **API 契约层的模型**，不是数据库 ORM 模型。DX-RAG v1 不使用 SQLite/PostgreSQL。

后续 Phase 会定义 `ChunkRecord`、`SearchResult` 等内部数据模型（也可能放在 schemas.py 中）。

#### `backend/app/services/` — 业务逻辑

当前为空目录（只有空的 `__init__.py`）。

这里将是未来业务逻辑的所在地：`ingest.py`（文档处理管道）、`qa.py`（检索 + QA 服务）。

#### `backend/requirements.txt` — Python 依赖

声明了 FastAPI、Uvicorn、ChromaDB、Sentence Transformers 等所有 Python 依赖。使用 `>=` 方式声明最低版本。

#### `backend/.env.example` — 环境变量模板

包含所有 22 个配置参数及其默认值。实际使用时，开发者需要复制为 `.env` 并填入真实的 API Key。

#### `frontend/app/layout.tsx` — Root Layout

Next.js App Router 的根布局。所有页面都会被包裹在这个布局中。当前实现了：

- `<html lang="zh-CN">` 声明
- Ant Design `ConfigProvider` 包裹（全局组件配置）
- 中文 locale 配置

#### `frontend/app/page.tsx` — 首页

当前是一个简单的占位页面，显示 "DX-RAG" 标题。后续 Phase 10-11 会将这里改造为带有 SideMenu 和四个功能区域的单页应用。

#### `frontend/app/globals.css` — 全局样式

当前是极简的 CSS reset（box-sizing、margin、padding、font-family）。后续会随组件开发而扩展。

---

## 4. T0001 — Backend Foundation 深度学习

### 4.1 FastAPI Application 是什么

**FastAPI** 是一个 Python 异步 Web 框架。简单说，它的职责是：

1. **接收** HTTP 请求（通过 ASGI 服务器如 Uvicorn）
2. **路由**：根据 URL path 和 HTTP method 找到对应的处理函数
3. **校验**：自动根据类型注解校验请求参数
4. **调用**：执行你的业务逻辑
5. **序列化**：将返回值转为 JSON 响应

"FastAPI 应用" 的核心就是 `FastAPI()` 这个类的实例。在 DX-RAG 项目中，这个实例叫 `app`，定义在 [backend/app/main.py](backend/app/main.py) 中。

```python
app = FastAPI(
    title="DX-RAG",
    description="Enterprise knowledge base Q&A system",
    version="0.1.0",
    lifespan=lifespan,
)
```

这三个参数（`title`、`description`、`version`）会自动出现在自动生成的 OpenAPI 文档中（访问 `http://localhost:8000/docs` 即可看到）。

### 4.2 app/main.py 的职责 — 逐段解释

#### 第一段：imports

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

- `logging` 和 `traceback`：Python 标准库，用于记录错误日志
- `asynccontextmanager`：Python 标准库，用于创建 async context manager（lifespan 要用）
- `FastAPI`, `Request`：FastAPI 核心类
- `CORSMiddleware`：FastAPI 内置的 CORS 中间件
- `JSONResponse`：FastAPI 的 JSON 响应类
- `api_router`：我们自己定义的 APIRouter（来自 `app.api.router`）
- `AppError`, `ErrorDetail`, `ErrorResponse`：我们自己定义的错误模型（来自 `app.core.errors`）

#### 第二段：Lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing to initialize at this stage
    yield
    # Shutdown: nothing to clean up at this stage
```

`lifespan` 是 FastAPI 的 **生命周期管理器**。它是一个 async context manager：

- `yield` **之前**的代码：服务启动时执行（加载模型、初始化数据库连接等）
- `yield` **之后**的代码：服务关闭时执行（清理连接、释放资源等）

在 Phase 0，lifespan 是空的——因为还没有需要初始化的资源。后续 Phase 可能在这里执行一些启动逻辑。

**通用知识**：lifespan 替代了旧版 FastAPI 的 `@app.on_event("startup")` 和 `@app.on_event("shutdown")` 装饰器。它的优势是可以管理有状态的资源（比如用一个变量保存数据库连接，在 shutdown 时关闭）。

#### 第三段：CORS 中间件

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**CORS（Cross-Origin Resource Sharing，跨域资源共享）** 是浏览器的一种安全机制。默认情况下，浏览器会阻止 `localhost:3000`（前端）向 `localhost:8000`（后端）发送请求，因为它们属于不同的 "origin"。

`CORSMiddleware` 告诉浏览器："我允许来自任何 origin（`["*"]`）的请求访问这个 API"。

**为什么 v1 用 `["*"]`**：SPEC 明确假设 v1 部署在本地/可信内网环境，不需要严格的 CORS 限制。生产环境部署时，应通过 `CORS_ORIGINS` 配置项限制为具体的域名。

#### 第四段：全局异常处理器

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

两个 handler 形成两层安全网：

1. **第一层** `AppError` handler：捕获我们主动抛出的 AppError。例如我们 `raise AppError("FILE_TOO_LARGE")`，它会被转换为带有正确 HTTP 状态码、错误码和中文消息的 JSON 响应。

2. **第二层** `Exception` handler（兜底）：捕获所有未被第一层捕获的异常——比如 Python 的 `ValueError`、未预期的 `KeyError` 等。它：
   - 用 `logger.error()` 记录完整 traceback（开发者可以看到）
   - 向前端返回 `INTERNAL_ERROR` 的 500 响应（用户看不到 traceback，安全）

这是 **T0004 的核心价值**详见第 7 节。

#### 第五段：Router 注册

```python
app.include_router(api_router, prefix="/api")
```

这行代码告诉 FastAPI："所有 `api_router` 中的路由，都挂载在 `/api` 前缀下"。

例如，如果 `api_router` 中有一个 `GET /health`，它实际对外暴露的 URL 是 `GET /api/health`。

### 4.3 Python Package 结构

在 DX-RAG Backend 中，每个目录下都有一个 `__init__.py` 文件。这些文件目前都是空的，但它们的存在本身有重要意义：

```
backend/app/
├── __init__.py          # 使得 app/ 成为一个 Python package
├── api/
│   ├── __init__.py      # 使得 app.api/ 成为一个 sub-package
│   └── router.py
├── core/
│   ├── __init__.py      # 使得 app.core/ 成为一个 sub-package
│   ├── config.py
│   └── errors.py
├── models/
│   ├── __init__.py      # 使得 app.models/ 成为一个 sub-package
│   └── schemas.py
└── services/
    └── __init__.py      # 使得 app.services/ 成为一个 sub-package
```

**什么是 Python Package**：一个包含 `__init__.py` 的目录。没有这个文件，你就不能写 `from app.core import config`。

**每个子目录的职责**：

| 目录 | 职责 | 类比 |
|------|------|------|
| `api/` | HTTP 层的路由定义（接收请求、返回响应） | 餐厅的前台 |
| `core/` | 与业务无关的基础设施（配置、错误、接口定义） | 餐厅的水电系统 |
| `models/` | 数据结构定义（API 契约、内部数据模型） | 菜单模板 |
| `services/` | 业务逻辑（文档处理、检索、QA） | 后厨 |

这个分层的核心原则是 **关注点分离（Separation of Concerns）**：API 层只负责 HTTP 协议的事情（解析参数、返回状态码），Service 层只负责业务逻辑（怎么解析 PDF、怎么检索），Core 层提供两者的基础设施。

### 4.4 APIRouter 是什么

在 FastAPI 中，`APIRouter` 是一个 **可复用的路由组**。

想象你有一个 FastAPI 应用，所有的 endpoint 都直接注册在 `app` 上：

```python
@app.get("/api/collections")
def list_collections(): ...

@app.post("/api/collections")
def create_collection(): ...

@app.get("/api/files")
def list_files(): ...
```

当应用有 4 个模块、每个模块有 3-4 个 endpoint 时，`main.py` 会变得非常长。而且每个模块的 endpoint 混在一起，难以维护。

`APIRouter` 解决了这个问题：

1. 每个模块定义自己的 router（例如 `collections.py` 中有一个 `router = APIRouter()`）
2. 所有 router 在 `api/router.py` 中聚合
3. `main.py` 只做一件事：`app.include_router(api_router)`

当前 DX-RAG 的 `api/router.py` 是空的（只有注释掉的 import），但这正是框架的价值——后续 Phase 只需要取消注释、添加 import 即可。

**请求路由的完整路径**：

```
HTTP Request
  → Uvicorn (ASGI server)
    → FastAPI app (main.py)
      → APIRouter prefix="/api" (router.py)
        → Feature Router (collections.py, upload.py, ... )
          → Endpoint function
```

### 4.5 Uvicorn 启动过程

启动命令：

```bash
uvicorn app.main:app
```

我们用这个命令拆解每个部分：

| 部分 | 含义 | 解释 |
|------|------|------|
| `uvicorn` | ASGI 服务器程序 | Uvicorn 是一个 Python ASGI 服务器。它的职责是接收 TCP 连接、解析 HTTP 协议、将请求转交给 ASGI 应用。 |
| `app.main` | Python 模块路径 | 等价于 `from app.main import ...`。Uvicorn 会 import `app/main.py` 这个文件。 |
| `:app` | 变量名 | `app/main.py` 中定义的 `app = FastAPI(...)` 那个变量。Uvicorn 会找到这个 FastAPI 实例。 |

**从命令到应用启动的完整流程**：

```
1. 你在终端输入: uvicorn app.main:app

2. Uvicorn 启动，做两件事：
   a. Import "app.main" module
      → Python 首先找到 app/ 目录（有 __init__.py）
      → 然后找到 app/main.py
      → 执行 main.py 中的所有顶层代码：
          - import 各种模块
          - 创建 FastAPI() 实例 (变量名 "app")
          - 注册 CORS 中间件
          - 注册异常处理器
          - include_router(api_router)
   b. 从 app.main 模块中取出 "app" 变量

3. Uvicorn 将 FastAPI app 实例作为 ASGI application 启动
   → 开始监听 localhost:8000

4. Uvicorn 调用 lifespan(app)
   → 执行 yield 之前的 startup 代码（当前为空）
   → 应用就绪

5. 当有 HTTP 请求到来时：
   → Uvicorn 接收 TCP 连接
   → 解析 HTTP 请求
   → 构造 ASGI scope/event
   → 调用 FastAPI app
   → FastAPI 根据 path + method 找到匹配的 endpoint
   → 执行 endpoint 函数
   → 返回 Response
   → Uvicorn 将 Response 序列化为 HTTP 字节流返回给客户端
```

### 4.6 我应该理解的关键代码

#### 1. [backend/app/main.py:22-27](backend/app/main.py) — FastAPI 实例化

```python
app = FastAPI(
    title="DX-RAG",
    description="Enterprise knowledge base Q&A system",
    version="0.1.0",
    lifespan=lifespan,
)
```

**重点看**: 这里生成了整个 Backend 的唯一 FastAPI 实例。所有的 middleware、handler、router 都注册在它上面。

**你应该理解**: `app` 是整个 Backend 的"根"。任何对 Backend 的配置、扩展都是通过 `app.xxx()` 方法完成的。

#### 2. [backend/app/main.py:68](backend/app/main.py) — Router 挂载

```python
app.include_router(api_router, prefix="/api")
```

**重点看**: 这是 `/api` 前缀的来源。所有业务 API 的 URL 都从 `/api` 开始。

**你应该理解**: 如果未来想加 `/api/v2` 的 router，就在这里再加一行 `app.include_router(v2_router, prefix="/api/v2")`。

---

## 5. T0002 — Frontend Foundation 深度学习

### 5.1 Next.js 在这个项目中的角色

**Next.js** 是一个基于 React 的全栈 Web 框架。在 DX-RAG 中，它的角色是：

1. **渲染界面**: 将 React 组件转换为浏览器可显示的 HTML/CSS/JavaScript
2. **路由管理**: 通过 App Router 管理页面组织
3. **开发体验**: 提供热更新（修改代码后浏览器自动刷新）、TypeScript 支持
4. **构建优化**: 生产构建时自动优化 JS bundle 大小

DX-RAG 使用的是 **Next.js 14.2.24** + **App Router**（不是旧的 Pages Router）。

### 5.2 App Router 是什么

App Router 是 Next.js 13+ 引入的新路由系统。它的核心概念是 **基于文件系统的路由**：

- `app/layout.tsx` → 根布局（所有页面的外层框架）
- `app/page.tsx` → `/` 路径的页面（首页）
- `app/globals.css` → 全局样式

**当前 DX-RAG 只使用了最基础的 App Router 结构**——因为 Phase 0 只是骨架。后续 Phase 10 会在这个基础上添加 SideMenu 和多区域切换。

当前三个文件的关系：

```
<html lang="zh-CN">            ← layout.tsx 定义
  <body>
    <ConfigProvider>            ← Ant Design 全局配置
      {children}                ← page.tsx 的内容会被插入这里
    </ConfigProvider>
  </body>
</html>
```

`layout.tsx` 是"外壳"，`page.tsx` 是"内容"。

### 5.3 Root Layout 的生命周期和职责

在 DX-RAG 中，`layout.tsx` 的职责是：

1. **声明 HTML 结构**: `<html lang="zh-CN">` 告诉浏览器这是中文页面
2. **引入全局配置**: `<ConfigProvider locale={zhCN}>` 确保所有 Ant Design 组件的文案（如日期选择器、分页器）默认显示中文
3. **包裹子页面**: `{children}` 是一个特殊的 React prop，代表子组件——在这里就是 `page.tsx` 的内容

**通用知识——Next.js Layout 的特性**：
- Layout 在路由切换时 **不会重新渲染**，只有 `{children}` 部分会变
- Layout 可以嵌套——可以在 `app/` 下创建子目录，每个子目录有自己的 `layout.tsx`
- 在 DX-RAG v1 中，由于是单页应用（只有 `page.tsx`），只需要一个根 layout

### 5.4 Ant Design 在哪里进入应用

在 [frontend/app/layout.tsx:3-4](frontend/app/layout.tsx)：

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
```

然后在组件中：

```tsx
<ConfigProvider locale={zhCN}>
  {children}
</ConfigProvider>
```

**`ConfigProvider`** 是 Ant Design 的全局配置组件。它使用 React 的 **Context API** 向所有子孙组件传递配置。

**`locale={zhCN}`** 的作用：确保 Ant Design 内置组件（如 Modal、Table、DatePicker）的中文文案。例如 Modal 的"确定"/"取消"按钮、Table 的"共 X 条"。

**为什么放在 layout.tsx**: 因为 layout 是所有页面的最外层。放在这里意味着整个应用的所有 Ant Design 组件都自动获得中文配置，不需要在每个页面重复设置。

### 5.5 package.json 是什么

[frontend/package.json](frontend/package.json) 是 Node.js 项目的 **清单文件**。它包含：

```json
{
  "name": "dx-rag-frontend",    // 项目名称
  "version": "0.1.0",           // 项目版本
  "private": true,              // 标记为私有项目（防止意外发布到 npm）
  "scripts": {                  // 可执行的脚本命令
    "dev": "next dev",          // 启动开发服务器
    "build": "next build",      // 生产构建
    "start": "next start"       // 启动生产服务器
  },
  "dependencies": { ... },      // 生产依赖
  "devDependencies": { ... }    // 开发依赖
}
```

**`dependencies` vs `devDependencies`**:

| 类型 | 说明 | DX-RAG 示例 |
|------|------|------------|
| `dependencies` | 运行时需要的包（用户浏览器中执行的代码依赖） | `next`, `react`, `antd`, `react-markdown` |
| `devDependencies` | 仅在开发/构建时需要 | `typescript`, `@types/react` |

`react-markdown` 在运行时将 Markdown 字符串渲染为 HTML，所以是 `dependencies`。`typescript` 只在开发时做类型检查，构建后不再需要，所以是 `devDependencies`。

### 5.6 package-lock.json 是什么

这是 Node.js 生态中最容易被误解的文件之一。

**`package.json`** 声明了"我需要什么包、最低什么版本"。例如：
```json
"antd": "5.22.7"
```

这告诉 npm："我需要 antd，版本是 5.22.7"。

**`package-lock.json`** 记录了"实际安装了什么包、精确到哪个 commit hash"。例如：
```json
"antd": {
  "version": "5.22.7",
  "resolved": "https://registry.npmjs.org/antd/-/antd-5.22.7.tgz",
  "integrity": "sha512-..."
}
```

**为什么 AI Coding 项目尤其需要 lockfile**：

当你和 AI Coding Agent 协作时，Agent 执行 `npm install` 的时机和你的时机不同。如果没有 `package-lock.json`：

- Agent 的机器上可能安装 `antd@5.22.8`（一个新发布的补丁版本）
- 你的机器上是 `antd@5.22.7`
- 代码在 Agent 那边跑得好好的，到你这边出了问题

有了 `package-lock.json`，无论谁执行 `npm install`，都会得到完全相同的依赖树。

**这就是为什么 `package-lock.json` 必须提交到 Git 仓库中**。

### 5.7 npm install 和 npm run dev 分别发生什么

#### `npm install`

```
1. npm 读取 package.json，解析 dependencies 和 devDependencies
2. npm 读取 package-lock.json（如果存在），按 lockfile 中记录的精确版本下载
3. 下载的包存放在 node_modules/ 目录
4. 如果 package-lock.json 不存在，npm 会生成一个新的
```

**没有网络就不能 `npm install`**：npm 需要从 registry（默认 https://registry.npmjs.org/）下载包。

#### `npm run dev`

```
1. npm 查找 package.json 中 scripts.dev 的值："next dev"
2. npm 在 node_modules/.bin/ 中找到 next 可执行文件
3. 执行 next dev
4. Next.js 开发服务器启动：
   a. 编译 TypeScript → JavaScript
   b. 打包 CSS 和资源
   c. 启动 WebSocket 连接（用于热更新）
   d. 在 localhost:3000 上监听 HTTP 请求
5. 当你在浏览器中打开 localhost:3000：
   a. Next.js 收到请求
   b. 执行 layout.tsx 和 page.tsx 中的 React 组件（服务端渲染）
   c. 返回 HTML 给浏览器
   d. 后续交互由客户端 React 接管（hydration）
```

---

## 6. T0003 — Configuration Foundation

### 6.1 为什么配置不能散落在代码中

假设你在 `qa.py` 中直接写了：

```python
# ❌ 错误做法
deepseek_api_key = "sk-xxxx"
chroma_dir = "./chroma_db"
max_upload_mb = 50
```

这带来了几个问题：

| 问题 | 说明 |
|------|------|
| **安全问题** | API Key 被提交到 Git 仓库，任何能访问仓库的人都能看到 |
| **环境切换困难** | 开发环境用测试 API Key，生产环境用正式 API Key——你需要在每次部署前手动改代码 |
| **团队协作问题** | 同事 A 的 chroma_db 路径是 `/data/chroma`，同事 B 的路径是 `C:\data\chroma`，代码无法同时满足 |
| **难以发现** | 当应用变大，很难快速回答"当前 max_upload_size 是多少？" |

**正确做法**是将配置集中管理，从环境变量中读取，代码只引用一个配置对象。

### 6.2 当前项目实际配置加载路径

DX-RAG 使用 **Pydantic `BaseSettings`** 实现配置管理。完整的配置数据流：

```
┌─────────────────────────────────────────────────────────────────┐
│ Environment Variables / .env file                               │
│ DEEPSEEK_API_KEY=sk-xxx                                         │
│ CHROMA_PERSIST_DIR=chroma_db                                    │
│ MAX_UPLOAD_SIZE_MB=50                                           │
│ ...                                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Pydantic BaseSettings 自动读取
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ backend/app/core/config.py                                       │
│ class Settings(BaseSettings):                                   │
│     DEEPSEEK_API_KEY: Optional[SecretStr] = Field(default=None) │
│     MAX_UPLOAD_SIZE_MB: int = 50                                │
│     ...                                                         │
│                                                                  │
│ settings = Settings()  ← 模块级单例                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ from app.core.config import settings
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 任意 Backend 模块                                                 │
│ settings.MAX_UPLOAD_SIZE_MB  → 50                                │
│ settings.CHROMA_PERSIST_DIR  → "chroma_db"                       │
│ settings.get_deepseek_key() → "sk-xxx" (明文)                    │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 BaseSettings / Pydantic Settings

Pydantic 的 `BaseSettings` 是一个特殊的 Pydantic Model，它会 **自动从环境变量中读取值**。

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # 也读取 .env 文件
        env_file_encoding="utf-8",
        case_sensitive=True,       # 环境变量名大小写敏感
    )

    MAX_UPLOAD_SIZE_MB: int = 50  # 如果环境变量中有 MAX_UPLOAD_SIZE_MB，使用它的值；否则用 50
```

当 `Settings()` 被实例化时，Pydantic 按以下优先级查找每个字段的值：

1. 操作系统环境变量（最高优先级）
2. `.env` 文件
3. Field 默认值（最低优先级）

这意味着你可以设置 `export MAX_UPLOAD_SIZE_MB=100` 来覆盖默认的 50——不需要修改任何代码。

### 6.4 .env 和 .env.example

| 文件 | 作用 | 是否提交到 Git |
|------|------|:---:|
| `.env` | 实际的配置值（含真实 API Key） | ❌ 绝对不能提交 |
| `.env.example` | 配置模板（不含真实值，只有参数说明） | ✅ 应该提交 |

**为什么需要 `.env.example`**：当一个新开发者 clone 项目时，他们可以 `cp .env.example .env`，然后填入自己的 API Key。`.env.example` 充当了 **配置文档** 的角色。

DX-RAG 的 [backend/.env.example](backend/.env.example) 包含了全部 22 个参数，每个都有注释说明。

### 6.5 Secret vs Non-Secret Config

在 DX-RAG 的 [backend/app/core/config.py](backend/app/core/config.py) 中，API Key 使用了 `SecretStr` 类型：

```python
DEEPSEEK_API_KEY: Optional[SecretStr] = Field(default=None)
DASHSCOPE_API_KEY: Optional[SecretStr] = Field(default=None)
```

**`SecretStr`** 是 Pydantic 提供的特殊类型。它的行为：
- 从环境变量读取时：正常工作
- 被打印/序列化时：显示为 `'**********'` 而非真实值
- 需要真实值时：调用 `.get_secret_value()` 方法

这就是为什么 `config.py` 中提供了 helper 方法：

```python
def get_deepseek_key(self) -> Optional[str]:
    if self.DEEPSEEK_API_KEY is not None:
        return self.DEEPSEEK_API_KEY.get_secret_value()
    return None
```

### 6.6 为什么 API Key 不能放 Frontend

这是一个关键的安全原则：

**任何进入浏览器的东西都是公开的。**

即使用户看不到你的源代码，浏览器的 DevTools → Network 标签页可以清楚地看到所有 API 请求。如果你把 `DEEPSEEK_API_KEY` 放在前端代码中，任何人打开开发者工具就能获取。

**SPEC 明确规定**: API keys env-only, never in frontend, never committed.

**正确的架构**:

```
Frontend (浏览器)                    Backend (服务器)
     │                                    │
     │  POST /api/query                   │
     │  {question: "xxx"}                  │
     │  (无需 API Key)                     │
     │ ──────────────────────────────────► │
     │                                    │ 从环境变量读取 DEEPSEEK_API_KEY
     │                                    │ 调用 DeepSeek API（附加 API Key）
     │                                    │
     │  {answer: "xxx", sources: [...]}   │
     │ ◄────────────────────────────────── │
     │                                    │
```

API Key **只存在于 Backend 环境变量中**，Frontend 只知道如何调用自己的 Backend API，Backend 代替 Frontend 调用第三方 AI 服务。

---

## 7. T0004 — Error / API Foundation

### 7.1 HTTP Error 和 Python Exception 的区别

| 概念 | 是什么 | 例子 |
|------|--------|------|
| **HTTP Error** | HTTP 协议层面的状态码，告诉客户端"请求失败了" | `404 Not Found`, `500 Internal Server Error` |
| **Python Exception** | Python 程序内部的异常，表示"代码执行出错了" | `ValueError`, `KeyError`, `FileNotFoundError` |

两者的关系：在 Web 框架中，Python Exception 需要被 **转换** 为 HTTP Error Response。如果你不处理一个 Python Exception，FastAPI 默认会返回 500 Internal Server Error（有时候还会暴露 traceback）。

**T0004 要解决的问题**: 建立一套"将 Python Exception 系统地转换为 HTTP Error Response"的机制。

### 7.2 为什么项目需要统一 Error Schema

没有统一 Error Schema 时，不同 endpoint 返回的错误格式可能不一致：\

```json
// Endpoint A 的错误
{"error": "File not found"}

// Endpoint B 的错误
{"detail": "Invalid input", "code": 400}

// Endpoint C 的错误（FastAPI 默认）
{"detail": [{"loc": ["body", "name"], "msg": "field required"}]}
```

前端必须写三种不同的解析逻辑。统一 Error Schema 解决这个问题：

```json
// 所有 endpoint 的错误都遵循这个格式
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "文件不存在",
    "details": {}
  }
}
```

### 7.3 FastAPI Exception Handler 的工作原理

FastAPI 允许你注册 **exception handler**——类似于全局的 `try/except`：

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

当任何 endpoint 中 `raise AppError(...)` 时，FastAPI 不会让这个异常传播到用户。它会：
1. 拦截这个 `AppError` 异常
2. 调用我们注册的 handler
3. 将 handler 返回的 `JSONResponse` 作为 HTTP 响应发送

**调用流程**：

```
Endpoint 函数中 raise AppError("FILE_TOO_LARGE", details={"max_size_mb": 50})
    │
    ▼
FastAPI 捕获异常
    │
    ▼
匹配到 app_error_handler（因为异常是 AppError 类型）
    │
    ▼
handler 返回 JSONResponse(status_code=413, content={...})
    │
    ▼
用户收到 HTTP 413，body = {"error": {"code": "FILE_TOO_LARGE", ...}}
```

### 7.4 error.code / error.message / error.details

这三个字段各司其职：

| 字段 | 类型 | 目的 | 示例 |
|------|------|------|------|
| `error.code` | `str` | 机器可读的错误标识（UPPER_SNAKE_CASE） | `"FILE_TOO_LARGE"` |
| `error.message` | `str` | 人类可读的中文描述 | `"文件大小超出限制"` |
| `error.details` | `dict` | 可选的附加上下文信息 | `{"max_size_mb": 50}` |

**前端如何使用**：
- `code` 用于程序化判断——例如 `if (error.code === "COLLECTION_EMPTY") { showUploadPrompt(); }`
- `message` 用于用户提示——直接展示给用户
- `details` 用于更丰富的错误展示——例如 `"文件大小超出限制（最大 50 MB）"`

### 7.5 为什么前端不能依赖 Python Traceback

Python 的 traceback 长这样：

```
Traceback (most recent call last):
  File "/app/services/qa.py", line 42, in search
    result = model.encode(query)
  File "/venv/lib/site-packages/sentence_transformers/...", line 128, in encode
    ...
```

这些信息对前端开发者和用户毫无意义，而且可能暴露：

- 服务器文件系统路径
- 使用的第三方库版本
- 内部数据结构

**因此 SPEC Section 9.4 明确要求**：500 错误时，traceback 必须被记录到 Backend 日志中（开发者查看），但 **不得暴露给用户**。

在 DX-RAG 的实现中，这体现在第二层 handler：

```python
@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
    # ↑ traceback 被写入了日志

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(code="INTERNAL_ERROR", message="服务器内部错误", details={})
            # ↑ 用户只看到这行，看不到 traceback
        ).model_dump(),
    )
```

### 7.6 INTERNAL_ERROR 的作用

`INTERNAL_ERROR` 是一个 **兜底错误码**。它的含义是：

> "发生了服务器内部未预期的错误。我们不告诉用户具体是什么（安全考虑），但我们记录了完整日志（开发者排查用）。"

它在两种情况下出现：

1. **代码中主动 raise** `AppError("INTERNAL_ERROR")`——但实际项目中很少主动用
2. **兜底 handler 捕获未知异常**——这是主要使用场景

---

## 8. T0005 — Pydantic Data Models & API Schemas

### 8.1 T0005 的真正职责

T0005 的职责是 **定义数据契约**——API 的 Request 长什么样、Response 长什么样。

它不实现任何业务逻辑。它只是"预先声明"了数据结构，让后续 Task 在写 endpoint 时可以直接使用这些类型。

### 8.2 Pydantic BaseModel 是什么

**Pydantic** 是 Python 的数据验证库。它的 `BaseModel` 类允许你声明一个数据结构的"形状"：

```python
from pydantic import BaseModel, Field

class CollectionCreate(BaseModel):
    name: str = Field(description="Collection name (3-50 chars)")
```

当你使用这个模型时：

```python
# 自动验证 + 类型转换
data = CollectionCreate(name="my-kb")    # ✅ 正常
data = CollectionCreate(name=123)        # ✅ Pydantic 自动将 123 转为 "123"
data = CollectionCreate(name="")         # ❌ 如果定义了 min_length 会报错
```

**Pydantic vs dataclass vs TypedDict**：Pydantic 在数据验证方面更强大，而且是 FastAPI 的原生选择——FastAPI 用 Pydantic 做自动的 Request 解析、Response 序列化和 OpenAPI Schema 生成。

### 8.3 当前项目中定义的主要模型

在 [backend/app/models/schemas.py](backend/app/models/schemas.py) 中，定义了以下模型：

| 模型 | 用途 | 关联 SPEC |
|------|------|----------|
| `ChatMessage` | 单条对话消息（role + content） | Section 6.4, 7.6 |
| `CollectionCreate` | 创建知识库的 Request Body | Section 6.5 |
| `CollectionRename` | 重命名知识库的 Request Body | Section 6.5 |
| `CollectionItem` | 列表中的单个知识库条目 | Section 7.2 |
| `CollectionResponse` | 创建/删除知识库的 Response | Section 6.5 |
| `CollectionRenameResponse` | 重命名知识库的 Response | Section 6.5 |
| `CollectionListResponse` | 知识库列表的 Response | Section 6.5 |
| `UploadWarning` | 上传处理中的一条 warning | Section 6.3 |
| `UploadResponse` | 上传成功的 Response | Section 6.3 |
| `SourceObject` | 答案中引用的一条来源 | Section 6.4, 7.5 |
| `QueryRequest` | QA 请求的 Request Body | Section 6.4 |
| `QueryResponse` | QA 响应的 Response | Section 6.4 |
| `FileItem` | 文件列表中的单个文件条目 | Section 6.6 |
| `FileListResponse` | 文件列表的 Response | Section 6.6 |
| `FilePreviewResponse` | 文件预览的 Response | Section 6.6 |
| `FileDeleteResponse` | 文件删除的 Response | Section 6.6 |

### 8.4 为什么 v1 不引入通用成功响应包装器

你可能在其他项目中见过这种模式：

```json
// ❌ DX-RAG v1 明确不采用这种格式
{
  "code": 200,
  "data": { ... },
  "message": "success"
}
```

SPEC Section 7.7 明确禁止这种"通用成功包装器"。

**为什么禁止**：
- 增加了一层没有语义价值的嵌套
- 前端每次都要 `.data` 才能拿到真正需要的字段
- 不同类型的响应有不同的字段，强行包装会让类型定义变复杂
- 错误有独立的 error format，不需要在成功响应中携带 code/message

**DX-RAG 的做法**：每个 API endpoint 使用自己独立的 Response Model，字段就是业务需要的字段。例如 UploadResponse 直接有 `status`、`file_id`、`chunks` 等字段，没有外层包装。

---

## 9. Backend 启动完整流程

以 `uvicorn app.main:app` 为起点：

```
Shell Command
  uvicorn app.main:app
    │
    ▼
Uvicorn 启动
    │ import "app.main" module
    ▼
Python 执行 backend/app/main.py 顶层代码
    │
    ├─ import logging, traceback
    ├─ from fastapi import FastAPI, ...
    ├─ from app.api.router import api_router
    │   │
    │   └─ Python 执行 backend/app/api/router.py
    │       │
    │       └─ 创建 api_router = APIRouter()
    │           （当前为空，无子 router）
    │
    ├─ from app.core.errors import AppError, ErrorDetail, ErrorResponse
    │   │
    │   └─ Python 执行 backend/app/core/errors.py
    │       │
    │       ├─ 定义 ErrorDetail(BaseModel)
    │       ├─ 定义 ErrorResponse(BaseModel)
    │       ├─ 定义 _ERROR_CATALOG dict（26 个错误码）
    │       └─ 定义 AppError(Exception)
    │
    ├─ 创建 app = FastAPI(title="DX-RAG", ...)
    ├─ 注册 CORSMiddleware
    │   allow_origins=["*"]
    │
    ├─ 注册 AppError 异常处理器
    │   @app.exception_handler(AppError)
    │
    ├─ 注册兜底 Exception 异常处理器
    │   @app.exception_handler(Exception)
    │
    └─ 注册主 Router
        app.include_router(api_router, prefix="/api")
    │
    ▼
Uvicorn 取得 "app" 变量（FastAPI 实例）
    │
    ▼
Uvicorn 启动 ASGI 服务器
    │ 执行 lifespan(app):
    │   yield 之前：startup（当前为空）
    │   应用就绪
    │
    ▼
监听 localhost:8000，等待 HTTP 请求
    │
    ▼
HTTP 请求到来时：
    Request → Uvicorn → FastAPI app → Middleware(CORS) → Router → Endpoint → Response
```

**当前阶段的特点**：所有 import 都能成功，没有循环依赖，应用能启动。但因为没有业务 endpoint，所有请求会返回 404。

---

## 10. Frontend 启动完整流程

以 `npm run dev` 为起点：

```
Shell Command
  npm run dev
    │
    ▼
npm 在 package.json 中找到 "dev": "next dev"
    │
    ▼
npm 在 node_modules/.bin/ 中找到 next 可执行文件
    │ next dev
    ▼
Next.js 开发服务器启动
    │
    ├─ 读取 next.config.js
    │   transpilePackages: ['antd']
    │
    ├─ 读取 tsconfig.json
    │   strict: true, jsx: "preserve", ...
    │
    ├─ 编译 App Router（基于文件系统）
    │   │
    │   ├─ 发现 app/layout.tsx → RootLayout 组件
    │   └─ 发现 app/page.tsx   → Home 组件
    │
    ├─ 应用全局 CSS (globals.css)
    │
    ▼
启动 WebSocket 热更新服务
    │
    ▼
监听 localhost:3000，等待 HTTP 请求
    │
    ▼
浏览器访问 localhost:3000 时：
    │
    ├─ Next.js 服务端渲染 (SSR)：
    │   1. 执行 RootLayout 组件
    │      <html lang="zh-CN">
    │        <body>
    │          <ConfigProvider locale={zhCN}>
    │            渲染 {children}（即 Home 组件）
    │              └─ <main><h1>DX-RAG</h1><p>Enterprise knowledge base...</p></main>
    │            完成
    │          </ConfigProvider>
    │        </body>
    │      </html>
    │
    │   2. 序列化为 HTML 字符串，发送给浏览器
    │
    ├─ 浏览器接收 HTML，开始渲染
    │
    ├─ 浏览器加载 JavaScript bundle（hydration）
    │   React 接管页面，绑定事件处理器
    │
    ▼
页面渲染完成 → 用户看到 "DX-RAG" 标题
```

**开发服务器启动成功 vs 浏览器页面无 console error 不是同一回事**：

- `npm run dev` 成功启动 = "Webpack/Turbopack 编译成功，没有语法错误，TypeScript 类型检查通过"
- 浏览器无 console error = "React 组件渲染正常，没有运行时错误，没有未捕获的异常"

一个常见的场景：`npm run dev` 成功（代码编译通过），但浏览器 Console 中有红色错误（如 Ant Design 组件缺少必需的 prop）。

**当前 Phase 0 的 Frontend 状态**：两种验证都应该通过——页面只是一个简单的 `<h1>` 标签，Ant Design 的 ConfigProvider 只是设置 locale，不渲染任何组件。

---

## 11. Browser → Backend 请求将来会怎么走

Phase 0 已经建立了 Frontend 和 Backend 之间的 **HTTP 通信基础**。以下是未来请求的完整路径：

```
┌─────────────────────────────────────────────────────────────────────┐
│ Browser (localhost:3000)                                            │
│                                                                     │
│ 用户点击 "发送" 按钮                                                  │
│   │                                                                 │
│   ▼                                                                 │
│ QAPanel 组件调用 api-client.ts 中的 queryQA()                        │
│   │                                                                 │
│   ▼                                                                 │
│ fetch("http://localhost:8000/api/query", {                          │
│   method: "POST",                                                   │
│   body: JSON.stringify({question, collection_name, top_k, history}) │
│ })                                                                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP POST /api/query
                               │ (JSON body)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Backend (localhost:8000)                                            │
│                                                                     │
│ Uvicorn 接收 HTTP 请求                                               │
│   │                                                                 │
│   ▼                                                                 │
│ FastAPI app (main.py)                                               │
│   │ CORSMiddleware: 检查 Origin → 允许 localhost:3000                │
│   ▼                                                                 │
│ APIRouter (prefix="/api")                                           │
│   │ 路由匹配: POST /api/query → query.py 中的 query endpoint         │
│   ▼                                                                 │
│ Endpoint 函数:                                                       │
│   1. Pydantic 自动解析 + 校验 Request Body                           │
│   2. 调用 Service 层业务逻辑                                         │
│   3. Pydantic 自动序列化 Response                                    │
│   ▼                                                                 │
│ JSONResponse → Uvicorn → HTTP Response                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP 200 OK
                               │ {answer, sources, query, collection_name}
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Browser                                                             │
│                                                                     │
│ QAPanel 组件接收响应                                                  │
│   → 更新 React state                                                 │
│   → react-markdown 渲染 answer                                       │
│   → 展开 sources 列表                                                │
└─────────────────────────────────────────────────────────────────────┘
```

**Phase 0 已就位的基础设施**：

- CORS 中间件允许 Frontend → Backend 跨域请求
- `/api` Router 结构已就位，后续只需添加子 Router
- 错误处理机制已就位，异常会被正确转换为 JSON Error Response
- Response 模型已在 T0005 中定义，endpoint 可以直接使用

**后续 Task 将在这个基础上加入具体业务 Endpoint。**

---

## 12. 依赖管理

### Python 依赖管理

DX-RAG Backend 使用 [requirements.txt](backend/requirements.txt) 声明 Python 依赖：

```
fastapi>=0.104.1
uvicorn>=0.24.0
chromadb>=0.4.15
...
```

**`>=` 的含义**：最低版本约束。"我需要 chromadb 0.4.15 或更高版本。"

**安装方式**：
```bash
pip install -r requirements.txt
```

**Python 依赖管理的特点**：
- `requirements.txt` 只声明直接依赖（不声明依赖的依赖）
- 实际安装的版本取决于 `pip install` 时的最新兼容版本
- 没有像 `package-lock.json` 那样的标准 lockfile 机制（pip-tools、Poetry、uv 等工具可以生成 lockfile，但不是 Python 标准）

**这意味着**：如果 `chromadb` 依赖了 `numpy`，而 `numpy` 发布了一个不兼容的新版本，不同时间执行 `pip install` 可能得到不同的 numpy 版本。

### Node 依赖管理

DX-RAG Frontend 使用 `package.json` + `package-lock.json` 双重管理：

**`package.json`**: 声明依赖和版本约束。
```json
"antd": "5.22.7"       // 精确版本
"react": "^18.3.1"      // 兼容 18.x 的最新版本
```

**`package-lock.json`**: 锁定整个依赖树的精确版本。

**安装方式**：
```bash
npm install    # 按 package-lock.json 精确安装
npm ci         # 更严格的安装（要求 package-lock.json 存在且与 package.json 一致）
```

### Python vs Node 依赖管理对比

| 维度 | Python (pip) | Node (npm) |
|------|-------------|-----------|
| 依赖声明 | `requirements.txt` | `package.json` |
| 版本锁定 | 无标准 lockfile | `package-lock.json` |
| 安装命令 | `pip install -r requirements.txt` | `npm install` |
| 可重复构建 | 依赖 pip 生态外的工具 | 原生支持（通过 lockfile） |
| 依赖存储 | 全局 site-packages 或 venv | 项目本地 `node_modules/` |

### 为什么版本锁定重要

无论是 Python 还是 Node，**可重复构建**都是一个重要的工程实践：

> 同样的代码 + 同样的依赖版本 = 同样的行为

没有版本锁定，可能出现：
1. 今天代码跑得好好的，明天一个依赖的更新导致 Bug
2. CI/CD 环境和本地开发环境行为不一致
3. 团队中不同成员的开发环境不一致

**在 AI Coding 项目中尤为重要**：AI Agent 可能会执行 `pip install` 或 `npm install`，如果依赖版本不确定，AI 验证通过的行为可能在你本地无法复现。

---

## 13. Git 与 Repository Hygiene

### 13.1 git status --short

这个命令显示 **工作目录相对于最新 commit 的变化**：

```
$ git status --short
 M backend/app/main.py    # M = Modified（已跟踪文件被修改）
?? new_file.txt           # ?? = Untracked（新文件，从未被 git 跟踪）
```

**当前项目状态**：`git status --short` 输出为空——意味着工作目录是干净的，所有 Phase 0 的变更都已经 commit。

### 13.2 git diff

显示 **已跟踪文件中未暂存（unstaged）的具体修改内容**：

```bash
git diff              # 显示所有未暂存的修改
git diff --staged     # 显示已暂存（git add 后）尚未 commit 的修改
```

**重要——git diff 看不到 untracked files**：

这是初次使用 Git 的人常犯的错误。你创建了一个新文件，执行 `git diff` 看到没有输出，以为"没有改动"——但实际上这个文件根本不在 Git 的视野内。你需要 `git status` 来查看 untracked files。

### 13.3 git ls-files --others --exclude-standard

这个命令列出所有 **untracked 且未被 .gitignore 忽略** 的文件。

`--others`：显示未被 Git 跟踪的文件
`--exclude-standard`：应用 `.gitignore` 规则

### 13.4 .gitignore 的作用

[.gitignore](.gitignore) 告诉 Git "这些文件/目录不要跟踪"。

**DX-RAG 中忽略的关键目录和文件**：

| 忽略内容 | 原因 |
|----------|------|
| `node_modules/` | 第三方依赖，体积巨大（几百 MB），可通过 `package.json` + `npm install` 随时重建 |
| `.next/` | Next.js 构建产物，可通过 `npm run build` 随时重建 |
| `__pycache__/`, `*.pyc` | Python 字节码缓存，自动生成 |
| `.env` | 包含真实的 API Key，绝对不能泄露 |
| `.env.local`, `.env.*.local` | 本地私有环境变量 |

**为什么这些文件不应该提交**：

1. **体积**：`node_modules/` 通常有几百 MB，提交它会让仓库变得极其臃肿
2. **可重建性**：只要有 `package.json`，任何人都可以通过 `npm install` 得到完全相同的 `node_modules/`
3. **安全**：`.env` 包含 API Key，泄露意味着任何人都能用你的 Key 调用 API

**为什么这些文件应该提交**：

| 文件 | 原因 |
|------|------|
| `.env.example` | 文档作用——告诉新开发者需要配置哪些环境变量 |
| `package-lock.json` | 确保所有人安装完全相同的依赖版本 |
| 所有源代码文件 | 这是项目本身 |

---

## 14. Phase 0 的关键设计决策

### 决策 1：Backend / Frontend 分离

**为什么这么设计**：Backend 和 Frontend 是技术上完全不同的运行时（Python vs Node.js），有不同的依赖管理、构建系统和部署方式。分离使它们可以独立开发、测试和部署。

**如果不分离呢**：如果强行放在同一个目录，`npm install` 会去安装 `requirements.txt` 中的包（不行），`pip install` 会去安装 `package.json` 中的包（也不行）。构建脚本会变得复杂。一个团队中写 Python 的人需要安装 Node.js，写 React 的人需要安装 Python。

### 决策 2：FastAPI Modular Router

**为什么这么设计**：4 个 API 模块（collections, upload, query, files）各有一个 Router，通过一个聚合 Router 挂载到 `/api` 前缀。这样每个模块可以独立开发和测试，不会在同一个文件中互相干扰。

**如果不用 Router**：所有 endpoint 都注册在 `main.py` 的 `app` 上，`main.py` 会变成几千行的巨型文件，改一个 endpoint 就要在这几千行中找位置。

### 决策 3：Next.js App Router（而非 Pages Router）

**为什么这么设计**：App Router 是 Next.js 13+ 的推荐方式，比 Pages Router 更现代。它支持 React Server Components、嵌套 Layout、Streaming 等新特性。虽然 DX-RAG v1 是单页应用，但选择 App Router 为未来扩展留了余地。

**如果不用 App Router**：用 Pages Router 也能完成任务，但会在项目初期就锁定在旧架构上。而且 App Router 的 `layout.tsx` 天然适合做全局配置（如 Ant Design ConfigProvider），Pages Router 需要额外的 `_app.tsx`。

### 决策 4：Centralized Configuration（集中式配置）

**为什么这么设计**：所有 22 个配置参数集中在一个 `Settings` 类中，通过模块级 singleton 对外提供。任何模块需要配置时，只需要 `from app.core.config import settings`。

**如果不集中管理**：每个模块各自从 `os.environ.get()` 读取配置——重复代码多，默认值散落各处，很难快速回答"当前所有可配置参数有哪些"。

### 决策 5：Unified Error Contract（统一错误契约）

**为什么这么设计**：所有错误响应遵循 `{error: {code, message, details}}` 格式。26 个错误码集中在一个 catalog 中管理。全球异常 handler 兜底。

**如果不统一**：前端需要写多种不同的错误解析逻辑，而且不同开发者会创造不同的错误格式。维护成本随 API 数量增长。

### 决策 6：Secrets Backend-Only（API Key 仅在后端）

**为什么这么设计**：`DEEPSEEK_API_KEY` 和 `DASHSCOPE_API_KEY` 只存在于 Backend 环境变量中。Frontend 不需要知道它们存在。Frontend 调用 Backend API，Backend 调用第三方 AI API。

**如果放到前端**：任何用户打开 DevTools 就能获取你的 API Key，然后可以无限调用 API（消耗你的额度）。

### 决策 7：Pydantic models 预定义所有 API Schemas（T0005）

**为什么这么设计**：在实现任何 endpoint 之前，先把所有 API 的 Request/Response 模型定义好。这样后续 Task 可以直接 import 使用，不需要每个 Task 都重新定义。

**如果不预先定义**：每个 Task 各自定义模型——可能出现同一个 Collection 在 `collections.py` 和 `upload.py` 中有不同的字段定义，导致不一致。

### 决策 8：Minimal Lifespan（Phase 0 无启动逻辑）

**为什么这么设计**：lifespan 中 `yield` 前后都为空。不做任何启动时初始化——不连接数据库、不加载模型、不创建目录。

**为什么不在启动时做这些**：SPEC 要求 Embedding Model 懒加载（首次使用时才加载，不在启动时），ChromaDB 在服务启动时也不需要预连接。Phase 0 遵循"不做不需要做的事情"的原则。

### 决策 9：package-lock.json 必须提交

**为什么这么设计**：见第 12 节。在 AI Coding 项目中，可重复的依赖安装尤其重要——确保 AI Agent 验证通过的行为在你本地能复现。

### 决策 10：空 `__init__.py` 文件的存在

**为什么这么设计**：每个目录下都有一个空的 `__init__.py`。它不包含任何代码，但标志这个目录是一个 Python package。没有它，Python 无法执行 `from app.core import config`。

**如果不加**：你会得到一个 `ModuleNotFoundError: No module named 'app.core'`。

---

## 15. 常见错误与 Debug 思路

### 错误 1: ModuleNotFoundError: No module named 'app'

**症状**：
```
ModuleNotFoundError: No module named 'app'
```

**可能原因**：
- 执行 `python app/main.py` 而不是 `uvicorn app.main:app`
- 当前工作目录不在 `backend/` 下
- PYTHONPATH 没有包含 `backend/`

**检查方法**：
1. 确认当前目录：`pwd`（应该在 `backend/` 下）
2. 使用 `uvicorn app.main:app` 而不是 `python app/main.py`
3. 如果必须用 `python`，需要设置 PYTHONPATH：`PYTHONPATH=. python app/main.py`

**为什么 `uvicorn app.main:app` 能工作**：Uvicorn 在启动时会自动将当前目录加入 Python path。

### 错误 2: Uvicorn import path 错误

**症状**：
```
Error: Could not import module "app.main"
```

**可能原因**：
- 不在 `backend/` 目录下执行命令
- 缺少 `__init__.py` 文件
- 代码中有语法错误导致 import 失败

**检查方法**：
1. `cd backend/` 确认在正确目录
2. `ls app/__init__.py` 确认文件存在
3. `python -c "from app.main import app"` 测试 import

### 错误 3: Next.js dependency 安装问题

**症状**：
```
npm install 报错，提示版本冲突或不兼容
```

**可能原因**：
- Node.js 版本低于 18
- package-lock.json 损坏
- npm registry 连接问题

**检查方法**：
1. `node --version` 确认 Node.js 版本 ≥ 18
2. 删除 `node_modules/` 和 `package-lock.json`，重新 `npm install`
3. 尝试 `npm install --legacy-peer-deps`（解决 peer dependency 冲突）
4. 检查网络是否能访问 `https://registry.npmjs.org/`

### 错误 4: Port 被占用

**症状**：
```
Error: listen EADDRINUSE: address already in use :::3000
# 或
ERROR: [Errno 98] address already in use
```

**可能原因**：
- 已经有一个 Next.js Dev Server 在运行
- 另一个进程占用了 3000 端口

**检查方法**：
```bash
# Windows: 查找占用 3000 端口的进程
netstat -ano | findstr :3000

# 使用不同端口启动
npm run dev -- -p 3001   # Next.js
uvicorn app.main:app --port 8001   # FastAPI
```

### 错误 5: TypeScript Configuration 错误

**症状**：
```
Cannot find module 'antd' or its corresponding type declarations.
```

**可能原因**：
- `npm install` 没有正确执行
- `tsconfig.json` 中 `moduleResolution` 设置错误

**检查方法**：
1. 确认 `node_modules/antd/` 目录存在
2. 确认 `tsconfig.json` 中 `"moduleResolution": "bundler"`
3. 尝试重启 VS Code 的 TypeScript Server（`Ctrl+Shift+P` → "TypeScript: Restart TS Server"）

### 错误 6: Environment Variable 未读取

**症状**：
```
settings.DEEPSEEK_API_KEY 返回 None（但实际上已经设置了环境变量）
```

**可能原因**：
- `.env` 文件不在当前工作目录
- `.env` 文件编码不是 UTF-8
- 环境变量名大小写不匹配

**检查方法**：
1. 确认 `.env` 文件在 `backend/` 目录下
2. 在 Python 中测试：`python -c "from app.core.config import settings; print(settings.DEEPSEEK_API_KEY)"`
3. 检查是否在正确的进程/终端中设置了环境变量

### 错误 7: CORS 问题

**症状**：
```
Access to fetch at 'http://localhost:8000/api/query' from origin
'http://localhost:3000' has been blocked by CORS policy
```

**可能原因**：
- Backend 没有配置 CORS 中间件
- `allow_origins` 没有包含 Frontend 的 origin

**检查方法**：
1. 确认 `main.py` 中有 `app.add_middleware(CORSMiddleware, ...)`
2. 确认 `allow_origins=["*"]`（开发环境）
3. 查看浏览器 Network 标签页中 Response Headers 是否有 `Access-Control-Allow-Origin`

### 错误 8: .env 被误提交

**症状**：
```
git log --oneline -- .env    # 发现 .env 出现在 commit 历史中
```

**处理方法**（如果已经发生）：
1. 立即轮换所有 API Key（去服务商后台重新生成）
2. 将 `.env` 加入 `.gitignore`
3. 从 Git 历史中移除 `.env`（需要 `git filter-branch` 或 `BFG`）
4. 以后只用 `.env.example` 作为模板

### 错误 9: node_modules 被 Git 跟踪

**症状**：
```
$ git status
... 几千个 node_modules 下的文件显示为 modified ...
```

**可能原因**：
- `.gitignore` 中没有 `node_modules/` 这一行
- 或者 `.gitignore` 是在 `node_modules/` 已经被 `git add` 之后才创建的

**检查方法**：
1. 确认 `.gitignore` 中有 `node_modules/`
2. 如果 node_modules 已经被跟踪：`git rm -r --cached node_modules/`

---

## 16. 本阶段执行过的重要命令

以下命令可根据 Git 历史和项目结构确认：

### `uvicorn app.main:app`

**作用**：启动 FastAPI Backend 开发服务器
**执行位置**：`backend/` 目录
**成功意味着**：
- 所有 Python import 成功（无 ModuleNotFoundError）
- CORS 中间件注册成功
- 异常处理器注册成功
- 服务在 `localhost:8000` 上监听
**不意味着**：服务有可用的 API endpoint（当前除了 404 不会有其他响应）

### `npm install`

**作用**：安装 `package.json` 中声明的所有依赖
**执行位置**：`frontend/` 目录
**成功意味着**：
- 所有依赖已下载到 `node_modules/`
- `package-lock.json` 已生成/更新
**不意味着**：项目可以成功编译（可能有 TypeScript 类型错误）

### `npm run dev`

**作用**：启动 Next.js 开发服务器
**执行位置**：`frontend/` 目录
**成功意味着**：
- TypeScript 编译通过
- CSS 处理通过
- 开发服务器在 `localhost:3000` 上监听
- 浏览器可以打开页面
**不意味着**：所有 React 组件没有运行时错误（当前 Phase 0 组件很简单，应该没有）

### `git status --short`

**作用**：检查工作目录是否干净
**成功意味着**：输出为空——所有变更已 commit，没有 untracked files
**不意味着**：代码是正确的（只是说明没有未保存的修改）

### `git log --oneline`

**作用**：查看 commit 历史
**在当前仓库中显示**：
```
a1976ed 添加项目级 git-save-push 技能，新增数据模型 schemas 模块，更新 TASKS.md
99cb486 Add error handlers module, enhance main.py startup, update TASKS.md
beaf705 Add backend config module, update TASKS.md
3db1b5e Add backend (FastAPI skeleton) and frontend (Next.js skeleton) implementations
9b2b438 Add CLAUDE.md agent contract, update SPEC to v1.4, add TASKS.md with 54 implementation tasks
b936491 Initial commit: DX-RAG project setup with SPEC and docs
```

可以看到 Phase 0 的 5 个 Task 对应了 5 个 commit（从 T0001/T0002 合并提交开始的第一个 commit，到 T0005 的最后一个 commit）。

---

## 17. Phase 0 概念地图

```
DX-RAG Project
│
├── Backend (Python / FastAPI)
│   │
│   ├── FastAPI Application (main.py)
│   │   ├── app = FastAPI(title="DX-RAG", version="0.1.0")
│   │   ├── lifespan（startup/shutdown 生命周期，当前为空）
│   │   ├── CORSMiddleware（allow_origins=["*"]）
│   │   └── Exception Handlers
│   │       ├── AppError handler → 结构化错误响应
│   │       └── Exception handler → 500 INTERNAL_ERROR（隐藏 traceback）
│   │
│   ├── APIRouter (api/router.py)
│   │   └── prefix="/api" → 所有业务 API 的 URL 前缀
│   │   └── [未来] collections / upload / query / files 子 Router
│   │
│   ├── Configuration (core/config.py)
│   │   ├── Pydantic BaseSettings
│   │   ├── 22 参数（来自 SPEC Section 8.1）
│   │   ├── SecretStr（API Keys 安全存储）
│   │   └── Singleton（模块级 settings 实例）
│   │
│   ├── Error Handling (core/errors.py)
│   │   ├── ErrorDetail / ErrorResponse（统一错误格式）
│   │   ├── Error Catalog（26 个错误码 → HTTP 状态码 + 中文消息）
│   │   └── AppError（可抛出的业务异常）
│   │
│   ├── Data Models (models/schemas.py)
│   │   ├── Collection Models（create, rename, list, response）
│   │   ├── Upload Models（UploadResponse + UploadWarning）
│   │   ├── QA Models（QueryRequest, QueryResponse, SourceObject）
│   │   ├── File Models（FileItem, FileListResponse, Preview, Delete）
│   │   └── ChatMessage（role: user|assistant）
│   │
│   └── Python Package Structure
│       ├── __init__.py（每个目录）
│       ├── requirements.txt（依赖声明）
│       └── .env.example（环境变量模板）
│
├── Frontend (TypeScript / Next.js 14)
│   │
│   ├── Next.js App Router
│   │   ├── layout.tsx（根布局：HTML 结构 + Ant Design ConfigProvider）
│   │   ├── page.tsx（首页占位）
│   │   └── globals.css（全局样式重置）
│   │
│   ├── Ant Design Integration
│   │   └── ConfigProvider locale={zhCN}（全局中文配置）
│   │
│   ├── TypeScript Configuration
│   │   └── tsconfig.json（strict: true, moduleResolution: bundler）
│   │
│   ├── Next.js Configuration
│   │   └── next.config.js（transpilePackages: ['antd']）
│   │
│   └── Node.js Project
│       ├── package.json（依赖 + scripts）
│       └── package-lock.json（精确版本锁定）
│
└── Engineering Practices
    │
    ├── Dependency Management
    │   ├── Python: requirements.txt（最低版本约束）
    │   └── Node: package.json + package-lock.json（精确版本锁定）
    │
    ├── Environment Variables
    │   ├── .env（不提交，含真实值）
    │   └── .env.example（提交，含文档）
    │
    ├── Git Hygiene
    │   ├── .gitignore（排除 node_modules, .next, __pycache__, .env, ...）
    │   ├── git status --short（检查工作目录状态）
    │   └── git diff（检查具体修改）
    │
    └── API Contract
        ├── 统一错误格式 {error: {code, message, details}}
        ├── 无通用成功包装器（v1 明确禁止）
        └── Pydantic 模型 = API 契约的单一来源
```

---

## 18. 我真正应该理解的代码

建议按照以下顺序亲自打开文件阅读：

### 1. [backend/app/main.py](backend/app/main.py) — 整个 Backend 的入口

**重点看**:
- `app = FastAPI(...)` 的创建
- `CORSMiddleware` 的配置
- 两个 `@app.exception_handler` 的注册
- `app.include_router(api_router, prefix="/api")`

**你应该理解**: 为什么这个文件只有 69 行却能支撑整个 Backend 的骨架。

### 2. [backend/app/core/config.py](backend/app/core/config.py) — 配置如何从环境变量流向代码

**重点看**:
- `class Settings(BaseSettings)` 的字段定义和默认值
- `model_config` 中 `env_file=".env"` 的作用
- `SecretStr` 的使用方式
- `get_settings()` 函数如何返回单例

**你应该理解**: 为什么 `from app.core.config import settings` 就能在任何地方获取配置。

### 3. [backend/app/core/errors.py](backend/app/core/errors.py) — 错误码目录和 AppError

**重点看**:
- `_ERROR_CATALOG` dict 的结构（error_code → (http_status, chinese_message)）
- `AppError.__init__` 如何从 catalog 查找 HTTP 状态码和默认消息
- `ErrorDetail` 和 `ErrorResponse` 的 Pydantic 模型定义

**你应该理解**: 为什么 `raise AppError("FILE_TOO_LARGE")` 能自动产生 413 状态码。

### 4. [backend/app/models/schemas.py](backend/app/models/schemas.py) — 所有 API 的数据契约

**重点看**:
- `ChatMessage`（role Literal 类型）
- `UploadResponse`（status Literal 类型 + warnings 列表）
- `QueryRequest`（question, collection_name, top_k 默认值, history）
- `FileItem`（file_id, file_name, size, upload_time, chunk_count, status）

**你应该理解**: Pydantic 的 `Field(description=...)` 如何充当自动文档。

### 5. [backend/app/api/router.py](backend/app/api/router.py) — Router 聚合模式

**重点看**:
- `api_router = APIRouter()` 的创建
- 注释掉的子 Router import（未来 Phase 的接入点）

**你应该理解**: 为什么只需要取消注释就能接入新的 API 模块。

### 6. [frontend/app/layout.tsx](frontend/app/layout.tsx) — Next.js 的根布局

**重点看**:
- `'use client'` 指令（为什么需要它）
- `ConfigProvider` 的包裹方式
- `{children}` 的位置

**你应该理解**: Ant Design 如何在应用最外层"注入"中文配置。

### 7. [frontend/package.json](frontend/package.json) — 前端依赖清单

**重点看**:
- `dependencies` vs `devDependencies` 的区别
- 精确版本（`"antd": "5.22.7"`）vs 范围版本（`"react": "^18.3.1"`）
- `scripts` 中 `dev/build/start` 的定义

**你应该理解**: `npm run dev` 实际上执行的是 `next dev`。

### 8. [backend/requirements.txt](backend/requirements.txt) — 后端依赖清单

**重点看**:
- 每个包的用途（fastapi/框架、chromadb/向量数据库、sentence-transformers/嵌入模型...）
- `>=` 版本约束的含义

**你应该理解**: 为什么 `dashscope` 没有版本号（SPEC 说 "latest compatible"）。

### 9. [.gitignore](.gitignore) — Git 忽略规则

**重点看**:
- `node_modules/`、`.next/`、`__pycache__/` 等自动生成目录
- `.env` 安全敏感文件
- `*.pyc`、`.DS_Store` 等系统文件

**你应该理解**: 每一条规则背后是"可重建"或"安全"或"隐私"的理由。

### 10. [backend/.env.example](backend/.env.example) — 配置模板

**重点看**:
- 22 个参数的默认值和注释
- API Key 字段为空（需要开发者自行填入）
- 注释中标注了相对路径（如 `# ChromaDB persistence directory (relative to backend/)`）

**你应该理解**: 这个文件的读者是谁——新加入项目的开发者。

---

## 19. 自测题

### 基础理解

**Q1**: 解释 `uvicorn app.main:app` 中每个部分的含义。如果 Uvicorn 找不到 `app.main` 模块，可能是什么原因？

**Q2**: 一个 Python 目录下有 `__init__.py` 和没有 `__init__.py` 有什么区别？

**Q3**: `package.json` 中的 `dependencies` 和 `devDependencies` 有什么区别？`typescript` 应该放在哪个里面？为什么？

**Q4**: CORS 是什么？为什么 DX-RAG 需要配置 `allow_origins=["*"]`？

**Q5**: `npm install` 和 `pip install -r requirements.txt` 在版本锁定行为上有什么关键区别？

### 项目理解

**Q6**: DX-RAG 的 Backend 为什么在 `config.py` 中使用 `SecretStr` 而不是普通的 `str` 来存储 API Key？

**Q7**: 在 `main.py` 中注册了两个异常处理器。如果 endpoint 中 `raise ValueError("something went wrong")`，用户会收到什么响应？为什么？

**Q8**: SPEC Section 7.7 明确禁止"通用成功响应包装器"。什么是"通用成功响应包装器"？为什么 v1 禁止它？

**Q9**: 当前 DX-RAG 的 Frontend 只有一个 `page.tsx`。Phase 10 会把它改造为带有 SideMenu 的单页应用。为什么选择单页应用而不是独立 URL 路由（如 `/kb`、`/upload`、`/qa`）？

**Q10**: Backend 的 `api/router.py` 当前几乎是空的（只有注释掉的 import）。为什么在 Phase 0 就创建它，而不是等有了具体 endpoint 再创建？

### Debug / 推理题

**Q11**: 你在 `backend/` 目录下执行 `uvicorn app.main:app`，收到 `ModuleNotFoundError: No module named 'app'`。列举三种可能的原因和对应的解决方法。

**Q12**: Frontend `npm run dev` 成功启动，但浏览器访问 `localhost:3000` 时 Console 报错 `ConfigProvider` 相关错误。可能是什么问题？怎么排查？

**Q13**: 你在 `.env` 中设置了 `MAX_UPLOAD_SIZE_MB=100`，但在代码中 `settings.MAX_UPLOAD_SIZE_MB` 仍然是 50。列举可能的原因。

**Q14**: 一个新开发者 clone 了项目，执行 `npm install` 后 `npm run dev` 报大量 TypeScript 类型错误。你怀疑是 `node_modules` 版本不一致导致的。如何验证？如何解决？

**Q15**: 如果你想在不修改代码的情况下，临时改变 FastAPI 的监听端口从 8000 改为 9000，应该怎么做？

---

## 20. 动手练习

### 练习 1：手画 Backend Request Flow

**要求**：在一张纸上画出以下流程（不参考代码）：

```
HTTP Request (GET /api/health)
  → Uvicorn (做了什么)
    → FastAPI app (做了什么)
      → CORSMiddleware (做了什么)
        → APIRouter (做了什么)
          → Endpoint (返回了什么)
            → Response (怎么回到用户)
```

**训练目的**：理解 HTTP 请求在 FastAPI 栈中的完整路径。

### 练习 2：不看代码写出项目主要目录

**要求**：合上编辑器，手写出 `backend/app/` 下的所有子目录及其职责。然后对照实际目录检查。

**训练目的**：熟悉项目结构，做到"不用看目录就知道代码在哪"。

### 练习 3：解释 package-lock.json

**要求**：向一个完全不了解 Node.js 的 Python 开发者解释：
- `package.json` 和 `package-lock.json` 的关系
- 为什么要提交 `package-lock.json`
- 如果两个人执行 `npm install` 得到不同的 `node_modules`，可能是哪里出了问题

**训练目的**：理解依赖锁定，并能向他人解释。

### 练习 4：判断删除 __init__.py 的后果

**要求**：
- 如果删除 `backend/app/core/__init__.py`，什么代码会报错？
- 报什么错？
- 如果在一个没有 `__init__.py` 的目录下创建一个新 `.py` 文件，其他模块能 import 它吗？

**训练目的**：理解 Python package 机制。

### 练习 5：Debug 路径设计

**要求**：假设以下报错情景，写出你的排查步骤（1→2→3→...）：

```
$ cd backend
$ uvicorn app.main:app
Error: Could not import module "app.main"
```

写出至少 5 个你依次检查的内容。

**训练目的**：培养系统化的 Debug 思维（而不是乱试）。

---

## 21. Phase 0 完成后我应该具备什么能力

完成 Phase 0 的学习后，你应该能够：

1. **解释** `uvicorn app.main:app` 每一部分的含义（uvicorn 是什么、app.main 是什么、:app 是什么）
2. **指出** 一个新的 API Router（如 `collections.py`）应该放在 `backend/app/api/` 目录下，并在 `router.py` 中注册
3. **解释** Next.js `layout.tsx` 与 `page.tsx` 的关系——layout 是外壳，page 是内容
4. **判断** 一个环境变量是否可以作为 `NEXT_PUBLIC_` 前缀暴露给前端（API Key 绝对不能，API Base URL 可以）
5. **使用** `git status` 判断是否有 untracked files，`git diff` 查看具体修改
6. **区分** `.env` 和 `.env.example` 的用途——一个含真实值不提交，一个含模板提交
7. **说明** 为什么 `node_modules/` 被 `.gitignore` 但 `package-lock.json` 被提交
8. **追踪** 一个 HTTP 请求从浏览器到 Backend 再返回的完整路径
9. **识别** 模块级 singleton（如 `settings`）和 FastAPI 的 exception handler 注册模式
10. **解释** `raise AppError("FILE_TOO_LARGE")` 如何最终变成 HTTP 413 + JSON Error Response

---

## 22. Phase 1 将建立在什么基础上

读取 TASKS.md Phase 1 章节可知，Phase 1 将实现 **VectorStore Foundation**——ChromaDB 的 Vector Store 公共接口（ABC）和具体实现。

Phase 1 将直接利用 Phase 0 建立的以下基础：

| Phase 0 基础 | Phase 1 如何使用 |
|-------------|-----------------|
| **目录结构** | `backend/app/core/vector_store.py` 放在 `core/` 目录下（基础设施，不属于业务 services） |
| **Config (T0003)** | `VectorStore` 需要 `CHROMA_PERSIST_DIR` 配置项来初始化 ChromaDB PersistentClient |
| **Data Models (T0005)** | `VectorStore` 的方法签名使用 `ChunkRecord`、`List[dict]` 等已定义的类型 |
| **Error Handling (T0004)** | `VectorStore` 中的异常通过 `AppError` 和全局 handler 向外传递 |
| **APIRouter 结构** | 虽然 Phase 1 主要是内部模块，但 Router 结构已就位，后续 Phase 4 接入时无需修改架构 |
| **Python Package 结构** | `app/core/__init__.py` 使 Phase 1 可以直接创建 `app/core/vector_store.py` 并被其他模块 import |
| **依赖声明** | `chromadb>=0.4.15` 已在 T0001 的 `requirements.txt` 中声明 |

**高层说明**：Phase 1 不会增加任何 API endpoint。它纯粹是 Backend 内部的抽象层——定义 VectorStore 的公共方法签名，然后用 ChromaDB 实现这些方法。Phase 0 提供的配置、错误处理、项目结构基础使 Phase 1 可以专注于"如何设计一个干净的存储抽象层"，而不需要操心"配置从哪来"或"异常怎么报"。

---

## 学习过程中发现的待确认事项

无。

Phase 0 的实际实现与 SPEC.md / TASKS.md 一致。所有 5 个 Task 均已按照 SPEC 要求完成，代码结构清晰，无冲突或未完成项。

---

> **文档版本**: v1.0
> **编写日期**: 2026-08-12
> **基于代码状态**: Phase 0 DONE, Phase 1 NOT STARTED
> **Git Commit**: a1976ed（Phase 0 完成时的最新 commit）
