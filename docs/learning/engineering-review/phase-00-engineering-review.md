# Phase 0 Engineering Review — Project Bootstrap

> 配套学习笔记：[phase-00-bootstrap.md](../phase-00-bootstrap.md)（逐行精读、TS 类比）
> 本文档定位：**工程决策复盘**——不解释代码，回答"为什么这样设计、换一个设计会怎样、规模大了会怎样"。
> 所有结论基于真实代码（`backend/app/main.py`、`core/config.py`、`core/errors.py`、`models/schemas.py`、`api/router.py`）与 SPEC v1.5 / TASKS.md。

---

## 1. Phase 定位

| 维度 | 内容 |
|------|------|
| **业务目标** | 无直接业务价值——Phase 0 不实现任何面向用户的功能 |
| **技术目标** | 建立 12 个后续 Phase 共享的工程地基：项目骨架、配置管理、错误体系、API 数据模型、健康检查 |
| **系统位置** | 最底层。SPEC 依赖链中唯一没有上游依赖的 Phase（T0001/T0002 Dependencies: None） |
| **上游依赖** | 无 |
| **下游消费者** | 所有后续 Phase：VectorStore 读 `settings`/抛 `AppError`（Phase 1）、Embedding 读 `EMBED_MODEL`（Phase 2）、Ingest 抛 `FILE_PARSE_ERROR`（Phase 3）、所有 API 端点复用 Pydantic schemas 与统一错误格式（Phase 4-9）、前端复用错误解析（Phase 10-11） |

**一句话**：Phase 0 是 DX-RAG 的"脚手架 + 宪法"——脚手架决定代码放哪，宪法（错误码目录、配置契约、数据模型）决定所有人怎么写。

---

## 2. 为什么需要这个模块？

**如果没有 Phase 0，直接写 RAG 业务会发生什么：**

| 缺失的基础设施 | 直接后果 |
|--------------|---------|
| 无配置管理 | `DEEPSEEK_API_KEY` 硬编码在 `qa.py` 里，换环境改代码；或散落在 20 个文件的 `os.getenv()` 调用中，漏一个就 500 |
| 无统一错误格式 | endpoint A 返回 `{"error": "..."}`，endpoint B 返回 `{"detail": "..."}`，前端要写 N 个 error parser；错误码有的叫 `FILE_NOT_FOUND` 有的叫 `file-not-found`，机器无法可靠识别 |
| 无全局异常处理器 | FastAPI 默认把未捕获异常包装成 `{"detail": "Internal Server Error"}`，**traceback 可能泄漏到响应里**，且客户端拿不到任何错误码 |
| 无 Pydantic schemas | 每个 endpoint 各自拼 dict，字段名拼错（`chunk_count` vs `chunks`）不会被任何东西检查，直到前端渲染时报 undefined |
| 无骨架/目录约定 | 五个开发者五种目录结构；新建 API 不知道注册到哪个 router |

更隐蔽的一层：**这些缺失不会在 Phase 1-3 立刻爆炸**（当时只有内部服务在互相调用），而会在 Phase 4-9 的 API 层、Phase 10-11 的前端对接时集中爆发——那是修复成本最高的时点。Phase 0 的价值就是把"迟早要统一的约定"在最便宜的时候定下来。

---

## 3. 核心设计决策

### 决策 1：Pydantic BaseSettings 集中配置 + SecretStr 保护密钥

**Decision**: 用 `pydantic_settings.BaseSettings` 单类收敛 SPEC Section 8.1 的全部 22 个参数，API Key 字段用 `SecretStr` 类型。

**Context**: 项目涉及两类配置——普通参数（`MAX_UPLOAD_SIZE_MB=50`、`CHUNK_OVERLAP=120`）与机密（`DEEPSEEK_API_KEY`、`DASHSCOPE_API_KEY`）。SPEC 要求"secrets via env vars only, never in code"。

**Problem**: Python 生态里常见做法是散落 `os.getenv("X", default)`。问题：① 没有类型（`MAX_UPLOAD_SIZE_MB` 拿到的是字符串 `"50"` 还是 int `50`？）；② 没有默认值文档；③ API key 是普通 str，日志/序列化时可能意外泄漏。

**Chosen Solution**: `class Settings(BaseSettings)`，字段即配置项（`MAX_UPLOAD_SIZE_MB: int = 50`），密钥用 `Optional[SecretStr]`，通过 `get_deepseek_key()` / `get_dashscope_key()` 显式取明文，模块级 `settings = Settings()` 单例。

**Why**: ① 类型安全：Pydantic 自动把 env 字符串转成声明的类型，`settings.MAX_CHUNK_SIZE + 100` 不会变成 `"800100"`；② `SecretStr` 让 key 在 `repr()`/日志里显示为 `**********`，默认防泄漏；③ 显式的 `get_xxx_key()` 意味着取明文是一个**有意识的行为**，而不是随手 `str(obj)`。类比 TypeScript：相当于把散落的 `process.env.X` 收进一个 `config.ts` 并做 zod 校验。

**Trade-off**: 类型校验只发生在 `Settings()` 实例化时（进程启动），运行中改环境变量不生效——但这正好符合 12-factor 的不可变配置原则。`SecretStr` 多一层 `get_secret_value()` 解包，代码略啰嗦。

**Future Improvement**（Future / Not implemented in v1）: 配置中心（K8s ConfigMap/Secret、Vault）；配置热更新；按环境分层（dev/staging/prod 的 `.env` 分离）。

---

### 决策 2：错误码目录（Error Catalog）+ AppError 统一异常

**Decision**: 把 SPEC Section 9.2 的 26 个错误码收敛为一张 `_ERROR_CATALOG` 表（code → http_status + 默认中文 message），业务代码只 `raise AppError("FILE_TOO_LARGE")`，不手写 HTTP 状态码和文案。

**Context**: SPEC 定义了 26 个错误码，分布在 400/404/409/413/422/500/502 七个 HTTP 状态。每个 endpoint 都要按 Section 6.7 的 `{error: {code, message, details}}` 格式返回。

**Problem**: 如果每个 endpoint 自己写 `JSONResponse(status_code=400, content=...)`：① 同一个错误码在不同 endpoint 可能映射到不同状态码（`COLLECTION_NOT_FOUND` 在 query 里 404、在 upload 里却写成 500——契约崩坏）；② 中文文案重复定义；③ 错误码拼写错误无法被编译期发现。

**Chosen Solution**: `_ERROR_CATALOG: Dict[str, tuple]` 作为唯一真源；`AppError(code, details, message)` 构造时查表得到 http_status 与默认文案；`message` 参数允许调用方覆盖默认文案；未知 code 自动回落到 `INTERNAL_ERROR`。两个 warning-only 码（`OCR_PAGE_FAILED`、`PAGE_RENDER_FAILED`）也在目录里，但注释明确它们只出现在 `warnings[]`，不作为独立 AppError 抛出。

**Why**: ① 契约单一来源：改状态码只改一处；② `raise AppError(...)` 让业务代码完全不懂 HTTP——服务层抛出的是**领域错误**（"文件太大"），HTTP 映射由框架统一完成；③ 目录集中后可以一眼审计"还有哪些 SPEC 错误码没被覆盖"。类比 TypeScript：相当于用 `as const` 的 error map 替代散落各处的 `throw new Error("...")` 加手写 `res.status()`。

**Trade-off**: 目录查表是一层间接性——调试时看到 `AppError("RENAME_FAILED")` 不知道最终 HTTP 码是多少，要查表。换来的是全局一致性，值得。目录的 `tuple`（`(http_status, message)`）不够自文档化，`dataclass` 会更清晰，但 v1 克制住了不为此引入额外结构。

**Future Improvement**（Future / Not implemented in v1）: 结构化日志记录错误码分布（错误监控/告警）；错误码与 HTTP 状态解耦的 API 网关映射层。

---

### 决策 3：两级全局异常处理器（AppError 专用 + catch-all）

**Decision**: 注册两个 `@app.exception_handler`：`AppError` 映射为目录里的状态码；所有其他 `Exception` 统一 500 `INTERNAL_ERROR`，**traceback 只进日志、绝不进响应**。

**Context**: SPEC Section 9.4：未捕获异常 → 500 + `INTERNAL_ERROR` + "do not expose to client"。

**Problem**: FastAPI 默认异常处理有两个缺陷：① 未捕获异常返回的 `{"detail": ...}` 不符合 Section 6.7 的统一格式；② 默认 handler 在某些配置下会带出内部信息。同时，业务异常如果每种都写 `try/except` 包裹，代码全是噪声。

**Chosen Solution**: `app_error_handler`（把 AppError 转成 `ErrorResponse.model_dump()`）+ `unhandled_error_handler`（`logger.error(traceback.format_exc())` 后返回固定 500）。响应构造复用 `ErrorResponse` Pydantic 模型，保证格式永远正确。

**Why**: ① **错误格式永不漂移**：哪怕是 bug 触发的 500，响应也符合 Section 6.7——前端 error parser 只有一条路径；② **安全**：traceback（可能包含文件路径、库版本、内部状态）只写后端日志，客户端拿到的只有"服务器内部错误"；③ 业务代码零 try/except——FastAPI 的 exception handler 机制让异常自然穿越多层调用栈。

**Trade-off**: catch-all 会吞掉**所有**未分类异常，包括本应被识别为 4xx 的 bug——例如将来某处忘了抛 `AppError("FILE_NOT_FOUND")` 而是让 `KeyError` 冒出来，用户会看到 500 而不是 404。这要求团队纪律：**新增错误场景必须先在目录注册**。

**Future Improvement**（Future / Not implemented in v1）: 结构化日志 + 错误追踪 ID（trace-id 关联客户端请求与后端日志）；sentry 等 APM 集成。

---

### 决策 4：模块化 Router 结构（api_router 聚合子路由）

**Decision**: `app/api/router.py` 定义唯一的 `api_router = APIRouter()`，`main.py` 以 `prefix="/api"` 注册；子路由（collections/upload/query/files）将来各自成文件，在 router.py 聚合。

**Context**: SPEC Section 4 定义 `api/` 子包按资源拆分路由模块（collections.py、upload.py、query.py、files.py），Section 3.2 要求 "Modular router structure"。

**Problem**: 单文件 router 在 15+ 个 endpoint 后会变成 800 行的巨型文件；多 router 如果没有统一 prefix，每个子路由都要自己写 `/api/collections`，改 base path 要动所有文件。

**Chosen Solution**: 每个资源一个子 router 文件，注册到 `api_router`，`prefix="/api"` 只在 `main.py` 写一次。当前 router.py 只有 `GET /health`，其余为注释占位。

**Why**: ① 关注点分离：一个 endpoint 文件只关心一个资源；② base path 单一来源：未来如果加 `/api/v2`，只改 main.py 一行；③ 与 SPEC 目录结构一一对应，agent 实现新 endpoint 时"知道放哪、怎么注册"——项目当前由 Coding Agent 驱动开发，**结构的可预测性直接降低后续 Phase 的实现成本**。

**Trade-off**: 多一层文件/import 间接性；空文件（`api/__init__.py` 等）在 Python 包里是必需的样板。当前只有 health 一个 endpoint 时，这套结构显得"重"——但这是为 Phase 4-9 的 15+ endpoints 预付的结构成本。

**Future Improvement**（Future / Not implemented in v1）: 按版本分组的 router（`/api/v1`）；OpenAPI tags 分组完善（自动文档体验）。

---

### 决策 5：API Key 可选 + 懒校验（启动时不检查）

**Decision**: `DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY` 定义为 `Optional[SecretStr]`，应用启动时**不**校验；缺失时仅在首次调用 LLM/OCR 时抛 `LLM_NOT_CONFIGURED` / `OCR_NOT_CONFIGURED`。

**Context**: SPEC v1.3 Patch 固化："API Keys Optional；缺失时应用正常启动；仅在调用时返回对应 NOT_CONFIGURED 错误"。项目部署假设是本地/可信网络，用户可能只配置其中一个 key（只传纯文本文件就不需要 OCR key）。

**Problem**: 强制启动校验会让"功能部分可用"的部署场景完全无法启动——没有 DashScope key 的用户连纯文本文件上传都用不了。

**Chosen Solution**: 配置层只声明 Optional；服务层（ingest.py 的 `ocr_page`、未来的 QA service）在**实际需要**时检查 `settings.get_dashscope_key() is None` 并抛领域错误。

**Why**: ① **fail-soft 部署**：配置了 DeepSeek key 就能跑纯文本 RAG；② 错误信息有上下文：用户知道是"当前这一步缺 key"，而不是"应用起不来"；③ 遵循 SPEC v1.3 的明确决策（F004: "禁止因 DASHSCOPE_API_KEY 缺失而阻止纯文本文件的上传处理"）。

**Trade-off**: 启动时不校验意味着"配置错误"要到运行期才暴露——集成部署时可能第一次调用 LLM 才发现 key 没配。缓解手段是 `/api/health` 之外（Future）可加 readiness 检查。

**Future Improvement**（Future / Not implemented in v1）: readiness endpoint 检查各外部依赖可用性；key 的加密存储与轮换。

---

### 决策 6：Pydantic schemas 用 Literal 收敛状态枚举

**Decision**: 在 `schemas.py` 中用 `Literal["SUCCESS", "SUCCESS_WITH_WARNINGS"]`、`Literal["user", "assistant"]`、`Literal["OCR_PAGE_FAILED", "PAGE_RENDER_FAILED"]` 表达有限状态，而非自由 `str`。

**Context**: SPEC Section 6 定义了多处枚举语义：upload status 两态、warning error_code 两态、ChatMessage role 两态。SPEC 7.7 明确**禁止**通用成功响应包装器。

**Problem**: 自由 `str` 的 schema 无法在运行时拦截 `"status": "SUCESS"`（拼写错误）或 `"FAILED"`（违反"FAILED 不是 HTTP 200 status"的 SPEC 契约）。

**Chosen Solution**: `status: Literal["SUCCESS", "SUCCESS_WITH_WARNINGS"]`。`UploadResponse.status` 的 docstring 直接写明 "FAILED is not an HTTP 200 status; it is expressed via 4xx/5xx error responses"。

**Why**: ① Pydantic 运行时校验让**契约在代码里自我执行**——这是 Python 世界对 TypeScript 编译期检查的等价物（union type 的运行时版本）；② 读 schema 即读契约：`Literal` 一眼看出合法值域，无需翻 SPEC。

**Trade-off**: `Literal` 是 Pydantic v2 特性，与 v1 旧写法不兼容；枚举变长时（未来加 `"PARTIAL"` 状态）要改所有引用点——但 SPEC 已 FROZEN，v1 不存在这种变化。

**Future Improvement**（Future / Not implemented in v1）: Python 3.12 `type` 语法、`enum.StrEnum` 复用（当前 Literal 更轻，符合 v1 克制的原则）。

---

## 4. 架构影响

Phase 0 完成后，系统新增的能力与依赖关系：

| 新增能力 | 谁开始依赖它 | 未来 Phase 谁使用 |
|---------|------------|-----------------|
| `settings` 单例（22 参数） | — | Phase 1（`CHROMA_PERSIST_DIR`）、Phase 2（`EMBED_MODEL`）、Phase 3（`MAX_CHUNK_SIZE`/`CHUNK_OVERLAP`）、Phase 5（`MAX_UPLOAD_SIZE_MB`）、Phase 8（全部 LLM 参数）——**已实际发生** |
| `AppError` + 目录（26 码） | Phase 1（`COLLECTION_NOT_FOUND`）、Phase 3（`FILE_PARSE_ERROR` 等 6 码）——**已实际发生** | Phase 4-9 全部 endpoint 错误路径；前端错误解析（Phase 10） |
| 统一错误响应格式 | 前端 error parser（Phase 10） | 所有 API 调用方 |
| Pydantic schemas（16 模型） | 无运行时消费（Phase 4+ 才用于 endpoint） | Phase 4（Collection*）、Phase 5（UploadResponse）、Phase 8（Query*）、Phase 9（File*） |
| `/api/health` | 外部可用性探测（NFR 11.5） | Phase 12 集成验收、部署探针 |
| CORS 中间件 | 无（前端尚未接入） | Phase 10-11 前端跨域调用 |

一个值得注意的现象：**Phase 0 的产出在 Phase 1-3 中"悄然"兑现**——VectorStore 抛 `AppError("COLLECTION_NOT_FOUND")`、Embedding 读 `settings.EMBED_MODEL`、Ingest 抛 `FILE_PARSE_ERROR`，都验证了地基设计的正确性。地基质量如何，看的是上层引用它时是否顺滑。

---

## 5. 工程问题分析

### 可维护性

- ✅ 单一真源：配置 22 参数一处定义、错误码一处定义、API 模型一处定义——改契约只动一个文件
- ✅ 目录/文件的对称性：`core/`、`models/`、`api/`、`services/` 边界清晰，新代码"知道放哪"
- ⚠️ `_ERROR_CATALOG` 用裸 tuple 表达 (status, message)——未来加第三个维度（如"是否可重试"）要重构。v1 可接受
- ⚠️ `main.py` 的 handlers 与 `errors.py` 的模型分居两文件，新增错误时容易忘记"目录 + handler"是配套的（当前 handler 是通用的，无需改，所以风险低）

### 扩展性

- ✅ 配置扩展：加参数 = 在 Settings 加一行字段，零样板
- ✅ 错误扩展：加错误码 = 目录加一行
- ✅ 路由扩展：新 endpoint 文件 → 注册进 api_router
- ⚠️ schemas 与 endpoint 一一对应，未来 API 版本化（v2）需要平行 schema 集——v1 无此需求

### 数据一致性

- Phase 0 本身无持久化数据，一致性问题不适用。但 **schemas 是 API 契约一致性**的载体：后端 Pydantic 与前端 TypeScript interface（Phase 10 的 `lib/types.ts`）需要人工保持同步——**没有代码生成工具**（Future improvement 候选：openapi-typescript 从 FastAPI 自动生成的 OpenAPI 生成前端类型）

### 错误处理

- ✅ 所有错误路径收敛到两条 handler，格式永不漂移
- ✅ traceback 不进响应（安全）
- ⚠️ `AppError` 的 `details` 是自由 `Dict[str, Any]`——caller 可以塞任意结构，跨 endpoint 的 details 形状没有 schema 约束（如 `FILE_TOO_LARGE` 的 `{"max_size_mb": 50}` 是约定俗成而非强制的）
- ⚠️ catch-all handler 会把未分类 bug 变成 500 `INTERNAL_ERROR`，对用户不可区分——这是 SPEC 要求（9.4），但团队需要靠日志排查

### 性能

- Phase 0 全部为常量级开销：Settings 实例化一次、错误查表 O(1)、Pydantic 校验仅发生在请求边界
- ⚠️ 唯一注意点：`Settings()` 在 import 时执行（模块级单例）——env 文件读取发生在进程启动，多 worker 部署时每个 worker 各读一次（幂等，无实际问题）

### 安全

- ✅ `SecretStr` 防日志/序列化泄漏；显式 `get_xxx_key()` 收敛明文访问点
- ✅ 未捕获异常不暴露内部细节（traceback 仅日志）
- ✅ 前端永不接触 key（key 只存在于后端 env）
- ⚠️ **CORS `allow_origins=["*"]` + `allow_credentials=True` 是 v1 已知的宽松组合**——SPEC 假设本地/可信网络部署（Section 10.3、10.5：v1 无认证）。部署到不可信网络前必须收紧 CORS 并补认证（SPEC 明确要求 "authentication must be added before v1 release" if deployed beyond trusted network）

---

## 6. 如果规模扩大怎么办？

> 本节所有方案均为 **Future / Not implemented in v1** 分析。v1 目标是单机、单用户/少量并发（SPEC NFR 11.2）。

### 10× 规模（用户/请求量 ×10，如小型团队全面使用）

**可能出现的瓶颈**：

- **无**：Phase 0 的组件（配置、错误处理、schemas）全部是请求级别的 O(1) 操作，10 倍负载下不构成瓶颈。真正的瓶颈在 Phase 2（embedding 计算）和 Phase 1（ChromaDB），不在本 Phase。

**仍值得做的加固**：

- 收紧 CORS：从 `["*"]` 改为具体前端 origin 列表（配置已支持 `CORS_ORIGINS`）
- `/api/health` 保持"零依赖"语义（SPEC 明确禁止加入 ChromaDB/模型检查）——真正需要的是新增独立 readiness endpoint（Future）

### 100× 规模（如企业内网全员使用，多部署实例）

**可能出现的瓶颈**：

- **错误契约的手工同步**：前后端 schemas 人工对齐开始不可靠——字段变更的回归靠人眼
- **配置漂移**：多实例部署时 `.env` 各机器手改，出现"A 机器 50MB 上限、B 机器 200MB"的隐性不一致
- **错误不可观测**：26 个错误码没有分布统计，出现系统性 500 只能翻日志

**优化方向**（Not implemented in v1）：

- 用 OpenAPI 代码生成（openapi-typescript 等）从 FastAPI 自动生成前端 TS 类型，消除手工同步
- 配置上移到 K8s ConfigMap/Secret 或配置中心，多实例共享
- 日志聚合（ELK/Loki）+ 错误码指标（Prometheus counter by code）——SPEC OQ-010 已 DEFER，未来版本可引入

### 1000× 规模（如 SaaS 化、多租户对外服务）

**可能出现的瓶颈**：

- **单错误目录无法区分租户上下文**：多租户下同一个 `COLLECTION_NOT_FOUND` 需要知道是哪个租户的请求失败——需要 trace-id 贯穿日志与响应
- **error message 的 i18n**：中文默认文案无法直接对外服务多语言用户
- **schemas 成为 API 治理对象**：1000× 规模下 API 契约变更是对外承诺，需要版本化与兼容性管理（API versioning）

**优化方向**（Not implemented in v1）：

- 请求级 trace-id（middleware 注入 + 响应头 + 结构化日志）
- 错误文案按客户端 locale 渲染（目录只存 code，文案移到 presentation 层）
- API 版本化（`/api/v1`）与契约兼容性测试（contract testing）

**核心判断**：Phase 0 的地基设计（单例配置、错误目录、统一异常处理）在 1000× 下**不需要推翻**，只需要在外围加观测与治理层。这正是"地基打得对"的标志——地基的问题从来不是"不够快"，而是"上层楼时发现要拆掉重来"。
