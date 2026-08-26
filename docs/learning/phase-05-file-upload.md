# Phase 5 — File Upload API 学习笔记

> **Phase 状态**: T0501–T0503 DONE（Phase 5 编码 + 验证全部完成）；Phase Gate Review 已裁定 PHASE_5_FAIL（AC-F002-01）→ F-1/F-2 修复完成（2026-08-25）→ Re-review 待执行
> **本文档状态**: T0501 + T0502 + T0503 Learning Pass 完成（2026-08-25）；Phase 5 Learning Review 完成（2026-08-26）——Interview consolidation 见面试指南 Phase 5 深度章
> **配套文档**: [工程评审](./engineering-review/phase-05-engineering-review.md) · [面试指南](./interview-notes/dx-rag-interview-guide.md)
>
> 面向读者：前端开发者，熟悉 JavaScript / TypeScript / React，有少量 Node.js 经验，没有系统 Python 基础。

---

## 0. 三层文档架构（先读这一节）

Phase 4 起强制执行：一份文档只承担一种职责。

| 我要…… | 读哪个文档 |
|---------|-----------|
| 看懂代码、学 Python、做自测练习 | **本文档**（Layer 1 · Technical Learning） |
| 理解 ADR、一致性缺口、Failure Modes、规模分析 | [phase-05-engineering-review.md](./engineering-review/phase-05-engineering-review.md)（Layer 2 · Engineering Review） |
| 准备面试话术（30 秒 / STAR / 追问） | [dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md)（Layer 3 · Interview，Phase 5 深度章已 consolidation——2026-08-26 Phase Learning Review） |

**三种事实标记**（贯穿全学习体系）：

- [PROJECT FACT] — 仓库可证的项目事实（带文件:行号）
- [ENGINEERING KNOWLEDGE] — 通用工程知识（与具体项目无关）
- [FUTURE] — 任何未实现的能力，必须标注

---

## 1. Phase 学习（本章学什么、怎么学）

- **一句话定位**: 本 Phase 打开**知识库内容的入口**——用户上传的文件经六道校验安全进入 `uploads/{kb}/{file_name}`，交给 Phase 3 已建成的摄取管道，最后把结果（SUCCESS / SUCCESS_WITH_WARNINGS / FAILED→422）翻译成 HTTP 响应。T0501 建六道校验闸门，T0502 把它们接上端点并承担"失败不留垃圾"的清理责任，T0503 用一份 586 行的验证脚本把 SPEC F002 的 FAILED 原子性强制行为变成 15 个端点级场景的检查矩阵——验证结果是**零业务代码修复**，T0308/T0502 的回滚设计经受住实测。
- **核心学习点**:
  - 🟢 **六步校验管道**：路径安全 → 扩展名 → 大小 → 空文件 → KB 存在 → 同名——以及"校验先于任何文件系统写入"（Phase 4 的 Validation Before Side Effects 在 Upload 的延伸）
  - 🟢 **路径遍历的判定方法**：`PureWindowsPath` + basename 等式——为什么它在 Linux 上也能挡住 `..\evil.pdf`
  - 🟢 **端点编排与失败清理**（T0502）：保存 → ingest → FAILED 映射 → 失效 → 响应；失败的两条路径（FAILED 状态 / 异常）由**两个不同的责任方**清理——为什么这么分（第 5.5 节）
  - 🟢 **验证方法论**（T0503）：断言只走 public interface、基线前后对比、GUARD 与 CHECK 分离、声明替代——验证脚本怎么写才不锁死实现（第 5.7 节）
  - 🟢 **子进程隔离**（T0503）：ChromaDB 文件句柄进程级持有 + Settings 单例 import 时读环境变量——两个"进程级状态"陷阱的一个套壳解法
  - 🟡 校验顺序与 TASKS 编排顺序的差异及理由（实现把路径检查提到最前——第 5.1/9 节）
  - 🟡 查重为什么走 `get_files()` 派生聚合而不是查 uploads 目录（与零元数据库设计一致）
  - 🟡 keyword index 为什么**只在 200 结果之后**失效——"失败零 chunk → 索引天然正确"的推理链（第 5.5 节）
  - 🟡 声明替代（D-1/D-2）：环境缺依赖时用"走相同失败分支"的替代品验证——保真度靠论证（第 5.7.1 节）
  - 🔵 大小写不敏感的两处细节（扩展名 / 同名检查）；同步 `def` 端点跑在线程池（embedding 不阻塞事件循环）
- **前置依赖**: Phase 3 摄取管道（T0308 的 Ingest Service）、Phase 4 校验哲学与错误码用法（[collections.py](../../backend/app/api/collections.py)）、Phase 4 建立的 keyword index seam（T0402 的 `invalidate_keyword_index`）、Phase 1 VectorStore 原语（`list_collections` / `get_files`）；T0503 验证还依赖 `fastapi.testclient`（TestClient）与 Phase 0 全局 handler 的错误码 → HTTP 映射
- **学习建议**: 先读 [upload.py](../../backend/app/api/upload.py) 全文（230 行）→ 对照 SPEC F002（正常流程 10 步）与 Section 6.3 / 10.2 / 12.7 → 读本文档第 5 节逐行精读 → T0503 部分先读 [verify_t0503_rollback.py](../../backend/scripts/verify_t0503_rollback.py)（586 行）→ 第 5.7 节 → 做第 12 节自测题

---

## 2. Phase 目标（为什么做这个 Phase）

- **业务目标**: 用户上传文件到指定知识库，触发完整的处理管道（解析 → 清洗 → 切分 → 嵌入 → 存储）——知识库内容的入口（SPEC F002 Define）。
- **技术目标**: T0501 把 SPEC F002 正常流程的前置校验做成**独立、可复用的函数集**；T0502 把它接上 `POST /api/upload` 端点，兑现 F002 步骤 7–10（保存 → ingest → 失效 → 响应），并完成 FAILED→422 的 HTTP 映射与失败清理；T0503 把 F002 Upload Failure Atomicity 的 4 条强制 observable behavior 变成可执行的检查矩阵——它是**验证 Task**：实现已在 T0308/T0502 完成，交付物是脚本而非产品代码（TASKS.md Implementation Scope 原文），结果是零业务代码修复。
- **本 Phase 明确不做**:
  - 不做 magic-byte 内容校验（SPEC 10.2 明确 v1 out of scope）
  - 批量上传、断点续传、上传进度推送、文件夹上传、partial upload / resume（F002 "不包含" + T0502 Out of Scope）
  - 端点不做 FAILED 的文件删除（IngestService 已回滚——见第 5.5 节"清理责任二分"）
  - 验证不修 GUARD 发现（F-1~F-4 owner 化：T0104 / T0602 / 全局 handler / ER Gap-4——第 5.7.4 节）；不把脚本固化为回归套件（T1203 决策）
- **SPEC 引用**: F002 Define/Detail/Determine · F002 Detail "Upload Failure Atomicity"（FAILED 4 条强制行为）· Section 6.3（API 契约）· Section 10.2（Upload Security）· Section 12.7（AC-SEC-01/02）· Section 12.2（AC-F002-01/03/07/08/09/10）· Section 8.1（`MAX_UPLOAD_SIZE_MB` / `UPLOAD_DIR`）· Section 9.2（错误码目录）

---

## 3. 项目位置（这个 Phase 在系统地图的哪里）

- **所属层**: API Layer（`backend/app/api/`）——T0501 交付时是**无 router 的纯校验模块**（原因见第 7 节）；T0502 在同一文件接上 `APIRouter` 与端点，并已在 [router.py:16](../../backend/app/api/router.py#L16) 注册进 `api_router`。
- **上游依赖**:
  - T0003 配置：[config.py:34](../../backend/app/core/config.py#L34) `CHROMA_COLLECTION = "knowledge_chunks"`、[config.py:41-42](../../backend/app/core/config.py#L41-L42) `UPLOAD_DIR = "uploads"` / `MAX_UPLOAD_SIZE_MB = 50`
  - T0102 `list_collections()`：[vector_store.py:284](../../backend/app/core/vector_store.py#L284) —— KB 存在性检查
  - T0107 `get_files()`：[vector_store.py:491](../../backend/app/core/vector_store.py#L491) —— 同名检查的数据源
  - T0308 `IngestService.process()`：[ingest.py:562](../../backend/app/services/ingest.py#L562) —— 解析→清洗→切分→嵌入→存储；FAILED 时自带回滚（删文件 + delete_by_file）
  - T0402 seam `invalidate_keyword_index()`：[keyword_index.py:25](../../backend/app/services/keyword_index.py#L25) —— 目前是文档化 no-op，真实 dirty-flag 行为属于 Phase 6 T0602
  - Phase 0 错误体系：6 个校验错误码 + `FILE_PARSE_ERROR`(422) 全部已在 [errors.py](../../backend/app/core/errors.py) 就位（零新增）
- **下游消费者**: T0503（ROLLBACK 行为验证）——**已兑现**：`backend/scripts/verify_t0503_rollback.py`（586 行）以 TestClient 对端点做 15 场景实测，结果零业务代码修复（见第 4/5.7 节）；前端 Upload 组件（Phase 11）最终消费整个端点。
- **验证脚本位置**: [backend/scripts/](../../backend/scripts/) 目录由 T0503 创立——项目第一份验证脚本（此前验证全靠代码审查，无 tests 目录）。
- **数据流角色**: 摄取流水线的**第一段**（用户输入 → 校验闸门 → 保存 → 摄取管道）——它是"文档生命周期"的起点；Phase 4 管"KB 生命周期"（创建场地），Phase 5 管"文档生命周期"（放进内容）。

---

## 4. Task 学习（每个 Task 学了什么）

### T0501 — File Name & Upload Validation

- **Task 目标**（TASKS.md 原文）: Implement all pre-ingestion upload validations: file name path traversal check, extension whitelist, size limit, empty file detection, KB existence, and duplicate check.
- **实现摘要**: 新建 [upload.py](../../backend/app/api/upload.py)（T0501 交付时 137 行；T0502 接线后 230 行）——一个常量表 + 4 个函数，全部 side-effect free。模块 docstring（T0501 时代为 1–23 行）声明范围：**只做校验，不写盘、不碰 ChromaDB 写路径、不声明 router**（T0502 接线时改写为端点流程全景，见 5.0 节）。
- **新知识**（详见手册第 28 节）:
  - `PureWindowsPath`（🟢）——跨平台的 Windows 路径视图
  - `Path.name` / `.suffix`（🟡）——basename / 最后扩展名
  - set 推导式（🟡）——`{expr for x in iterable}`
  - `or` 默认值惯用法（🟡）——`collection_name or settings.CHROMA_COLLECTION`
- **TS 类比**: 整个模块 ≈ 一个导出一组纯函数的 `validators.ts`——没有副作用、没有 router 注册，T0502 像 `upload.route.ts` 一样把它 import 进来编排。
- **验证**（诚实记录）:
  - TASKS.md T0501 Status = DONE，实现代码存在且与 AC 描述的行为一致（逐条代码级核对，见下）。
  - 仓库中**无测试目录、无实测执行记录**（`backend/` 下只有 app/chroma_db/requirements.txt）——所以 AC 的表述是：**按 TASKS.md DONE + 代码审查记录，不虚构 PASS**。
  - 关键限制（2026-08-25 二次更新）：T0501 阶段核对的是函数级行为；端点级实测已在 T0503 兑现（15 场景脚本 + 开发期执行痕迹 + 用户 DONE 宣告——见 T0503 Task 学习），Phase 12 T1203 正式集成回归仍待执行：

| AC | 函数级核对（代码审查） | 端点级 |
|----|----------------------|--------|
| AC-SEC-01 `../doc.pdf` → 400 INVALID_FILE_NAME | `validate_file_name("../doc.pdf")` → `PureWindowsPath("../doc.pdf").name == "doc.pdf" ≠ 原文` → raise ✓（反斜杠变体 `..\doc.pdf` 同理，Windows 语义下 `.name` 同为 `"doc.pdf"`） | T0503 V1 ✓（`../evil.txt` → 400 INVALID_FILE_NAME） |
| AC-SEC-02 合法名 → 通过 | `validate_file_name("doc.pdf")` → `.name == "doc.pdf" == 原文` → 无异常 ✓ | T0503 V13 ✓（合法名 good.txt → 200 SUCCESS） |
| AC-F002-04 51MB → 413 | `len(content) > 50*1024*1024` → raise FILE_TOO_LARGE ✓ | T0503 V1 ✓（超限 → 413 FILE_TOO_LARGE） |
| AC-F002-05 `.exe` → 400 | `.suffix.lower() == ".exe"` 不在白名单 → raise ✓ | T0503 V1 ✓（evil.exe → 400 UNSUPPORTED_FILE_TYPE） |
| AC-F002-06 0-byte → 400 | `len(content) == 0` → raise EMPTY_FILE ✓ | T0503 V1 ✓（empty.txt → 400 EMPTY_FILE） |
| AC-F002-02 同名 → 409 | `file_name.lower() in existing` → raise FILE_ALREADY_EXISTS ✓ | T0503 V5 ✓（成功后重传 → 409 FILE_ALREADY_EXISTS） |
| 不存在的 KB → 404 | `collection not in store.list_collections()` → raise COLLECTION_NOT_FOUND ✓ | T0503 V1 ✓（no-such-kb → 404 COLLECTION_NOT_FOUND） |
| AC-SEC-01 "no file written" | 校验函数零文件系统写入 ✓；端点级：`validate_upload` 在 `target.write_bytes` **之前**执行完毕（upload.py:190-196 顺序）→ 结构保证 ✓ | T0503 V1/V2 ✓（4 种拒绝后 raw/chunks 均为空——"no validation rejection created any file"） |

- **Interview Candidates**（保持简短）:

  > Candidate only — not yet promoted to the project Interview Guide（更新时机见模板 Interview Update Cadence；Phase 5 完成后的 Learning Review 统一 consolidation）。**已晋升**：2026-08-26 Phase 5 Learning Review 将本节候选素材 consolidation 进 Interview Guide Phase 5 深度章。

  - **Technical Points**: `PureWindowsPath` 跨平台路径判定；`.suffix` 只认最后一段（`archive.tar.gz` 按 `.gz` 判）；查重走派生聚合（get_files）而非文件系统
  - **Engineering Questions**: "校验顺序为什么和 TASKS 编排不一致？"（路径安全提到最前——10.2 + 防御纵深）；"同名检查为什么大小写不敏感？"（大小写不敏感文件系统上的覆盖风险）；"查重为什么用 get_files？"（零元数据库 + FAILED 文件天然可重传）
  - **Candidate Interview Questions**: "怎么判断一个文件名是不是路径遍历？" / "`.exe` 和 `.EXE` 哪个会通过扩展名校验？" / "上传失败的残留文件会导致同名误拒吗？"
  - **STAR Candidate**: 无（普通 Task）

### T0502 — POST /api/upload Endpoint

- **Task 目标**（TASKS.md 原文）: Implement the full POST /api/upload endpoint that validates, saves the file, runs the ingestion pipeline, invalidates the keyword index, and returns the response.
- **实现摘要**: [upload.py:161-217](../../backend/app/api/upload.py#L161-L217) 的 `upload_file` 端点 + [upload.py:220-229](../../backend/app/api/upload.py#L220-L229) 的 `_discard_saved_file` 清理函数 + 两个模块级常量（`router` / `_STATUS_MESSAGES`），并在 [router.py:16](../../backend/app/api/router.py#L16) 注册。模块 docstring 也同步改写（从"范围声明"升级为"端点流程全景"，见 5.0 节）。
- **新知识**（详见手册第 29 节）:
  - `UploadFile` + `File(...)` / `Form(...)`（🟢）——FastAPI 的 multipart 处理
  - 同步 `def` 端点跑在线程池（🟡）——CPU 密集的 embedding 不阻塞事件循环
  - `except Exception: 清理; raise`（🟡）——裸 except 的合法用例
  - dict 查表 + 穷举键（🔵）——`_STATUS_MESSAGES[status]` 为什么不会 KeyError
- **TS 类比**: 整个端点 ≈ `upload.route.ts`——把 `validators.ts`（T0501）import 进来，编排 multer 保存 → 调用服务 → 构造响应；`_discard_saved_file` ≈ `finally` 块里的 `fs.unlink`，但它是显式函数，只在异常路径被调用。
- **验证**（诚实记录）:
  - TASKS.md T0502 Status = DONE，实现代码存在，AC 行为逐条代码级核对（见下）。
  - T0502 提交时仓库无测试目录、无已执行的实测记录——AC-F002-01/03/07 的 HTTP 级验证当时尚未执行过；不虚构 PASS。此后 T0503 兑现了端点级实测（见下）；Phase 12 T1203 集成回归仍待执行。
  - **重要更新（2026-08-25 二次更新）**：T0503 已 DONE——验证脚本 [verify_t0503_rollback.py](../../backend/scripts/verify_t0503_rollback.py)（586 行，V1–V15 场景）对端点做了实测。执行证据：开发期 `__pycache__` 时间戳（21:04/21:07，应用被 TestClient 导入执行）+ 脚本内 stderr 过滤器（L568）是实测产物；最终版（22:17 定稿）完整输出未见——实测结论归 T0503 Learning Pass 记录（见 T0503 Task 学习节）。

| AC | 代码级核对（代码审查） | 运行时 |
|----|----------------------|--------|
| AC-F002-01 正常上传 → 200、`uploads/test-kb/doc.pdf` 存在、chunks>0 | 保存路径 `Path(settings.UPLOAD_DIR) / collection / file_name`（upload.py:194）✓；响应字段与 SPEC 6.3 逐一对齐（见下）✓；chunks 取 `result["chunks_count"]`（ingest.py:640，0 chunks 会走 FAILED 分支到不了 200）✓ | T0503 V13 成功对照 ✓（提交路径实测）；SPEC 字面 fixture（doc.pdf/test-kb）未逐字复现 → Phase 12 T1203 |
| AC-F002-03 不同 KB 同名独立 | 查重作用域 = 单 KB（`get_files(collection)` 只含目标 KB 的文件，upload.py:149）✓ | DEFER Phase 12（T0503 无跨 KB 同名场景） |
| AC-F002-07 部分 OCR 失败 → 200 SUCCESS_WITH_WARNINGS | `warnings` 来自 OCR 警告表（ingest.py:607-608 `status = "SUCCESS_WITH_WARNINGS" if warnings`）→ `_STATUS_MESSAGES` 有对应消息（upload.py:44-47）→ `UploadWarning` Literal 与两种 warning code 完全匹配（schemas.py:87）✓ | T0503 V14 ✓（F004 warning 通道注入 → 200 SWW + `{page_number:3, error_code:"OCR_PAGE_FAILED"}`） |
| 响应 JSON = SPEC 6.3 格式 | `UploadResponse` 字段：status/message/file_id/file_name/chunks/collection_name/warnings（schemas.py:92-108）与 SPEC 6.3 Response Fields 表逐字段一致 ✓；message 文案与 SPEC 示例 JSON 一字不差（"上传并入库成功" / "上传并入库成功（部分页面 OCR 失败）"）✓ | —（格式可由 schema 验证，无需运行时） |
| FAILED → 422 FILE_PARSE_ERROR | `result["status"] == "FAILED"` → `raise AppError("FILE_PARSE_ERROR")`（upload.py:204-205）；错误码 → 422 在 errors.py:56 ✓；SPEC 6.3 "FAILED 不是 HTTP 200" 注释兑现 ✓ | T0503 V3 ✓（AC-F002-08/09/10 归 T0503——见 T0503 Task 学习） |
| Keyword index 失效 | 成功路径调用 `invalidate_keyword_index(collection)`（upload.py:207）✓——但 seam 本体是文档化 no-op（keyword_index.py:42-44） | 真实 dirty-flag 行为 DEFER T0602（T0503 V11 GUARD F-3 观察"提交后失效异常"形态） |
| 依赖 T0602 | T0602 仍 TODO，但 T0502 依赖的是"共享失效接口"——Phase 4 T0402 已建 seam，接口契约满足 ✓；T0502 无 BLOCKED 依据 | — |

- **发现**（诚实记录）:
  - **FAILED→422 时 warnings 被丢弃**：SPEC AC-F004-04（Phase 3 OCR 全页失败）的 Then 写明"API 返回 422 FILE_PARSE_ERROR，warnings 包含 3 条记录"——当前 `raise AppError("FILE_PARSE_ERROR")` 没带 `details`，`result["warnings"]` 在映射时丢失。项目已有先例（ingest.py:108 的 `details={"encoding_attempts"}`）。记为 ER Pending #37，Phase Gate Review 确认（跨 Phase 的 AC 口径问题，不擅自改代码）。
- **Interview Candidates**（保持简短）:

  > Candidate only —— 话术 consolidation 已由 2026-08-26 Phase 5 Learning Review 完成（见 Interview Guide Phase 5 深度章）。

  - **Technical Points**: 失败两条路径 × 两个清理责任方；keyword index 只在 200 结果后失效；同步端点 + 线程池（embedding 不阻塞事件循环）
  - **Engineering Questions**: "为什么 FAILED 时端点不自己删文件？"（IngestService 的 `_fail` 已回滚——不重复清理，责任单一）；"为什么异常路径只删 raw file？"（file_id 在异常时对端点不可见——端点只清理自己保存的东西）
  - **Candidate Interview Questions**: "上传失败的响应里能看到哪几页 OCR 失败吗？"（诚实：FAILED→422 目前不带 warnings——Pending #37）
  - **STAR Candidate**: 无（普通 Task）

### T0503 — Upload ROLLBACK Behavior Verification

- **Task 目标**（TASKS.md 原文）: Verify the all-or-nothing FAILED upload semantics and ensure no partial data persists after ingestion failure.
- **Task 性质**: **验证 Task，不是实现 Task**——TASKS.md Implementation Scope 明说"implementation work should already be done in T0308 and T0502"，交付物是验证脚本而非产品代码。结果是**零业务代码修复**："Only fix bugs discovered during verification"未触发——T0308 的 `_fail` 回滚与 T0502 的 `_discard_saved_file` 经受住 15 个端点级场景，一行未改（这本身是验证结论，见第 7 节）。
- **实现摘要**: 新建 [verify_t0503_rollback.py](../../backend/scripts/verify_t0503_rollback.py)（586 行）——**两级进程**结构：`main()` 父进程（L530-579）起子进程跑 `run_probe()`（L73-527），子进程用 TestClient 对 `POST /api/upload` 打 15 个场景（V1–V15），父进程负责清理临时目录与转发输出。场景矩阵覆盖四条失败路径（FAILED 状态 / 解析异常 / 嵌入异常 / Chroma 异常）+ 校验拒绝 + 成功对照 + 4 个 GUARD 观察项（详见第 5.7.4 节）。
- **新知识**（详见手册第 30 节）:
  - `subprocess.run` 子进程编排 + Windows 文件句柄生命周期推理（🟢）
  - `@contextmanager` + `with` 语句 + `yield`（🟢）——项目第一个 `with` 语句、第一个生成器函数（手册 §16 两条预言同时兑现）
  - 运行时 monkey-patch（`getattr` / `setattr` / `delattr`）（🟡）——测试替身 ≈ jest.spyOn
  - `os.environ` 先于 import 注入——Settings 单例在 import 时定值（🟡）
  - `TestClient(raise_server_exceptions=False)` 观察全局 handler 的 500 响应（🟡）
- **验证方法论**（本 Task 真正的学习内容）:
  1. **断言只走 public interface**（脚本 docstring L21-29）：回滚的 observable behavior 用 `get_files()` / `get_chunk_count()` / 文件系统目录观察，**不碰 ChromaDB 私有属性**——因为 SPEC L463 明说"Rollback / temporary-file 实现机制属于 implementation detail"。验证与实现解耦：哪天 `_fail` 改成临时文件 + 原子 rename，脚本一行不用改。
  2. **基线对比**（`assert_rolled_back`，脚本 L196-215）：每个场景先 `observe()` 拍基线（raw 目录列表 / chunk 总数 / get_files 列表 / 其他 KB 的 chunk 数），失败后重拍对比——"无残留"的判定是"和失败前一样"，而不是"绝对为零"（后者会误判同 KB 既有数据）。
  3. **声明替代**（D-1/D-2，脚本 docstring L43-52）：SPEC 字面的"无有效文本 PDF"用**空白 .txt** 替代——两者在"清洗后文本为空 → FAILED"同一分支汇合（PyMuPDF 未装）；embedding 用 stub（sentence-transformers 未装，且 F007 不在本 Task 验证范围）。替代保真度靠**论证**：替代品与字面 fixture 走的代码路径相同。
  4. **GUARD 与 CHECK 分离**（D-4，脚本 docstring L54-58）：V9–V12 探针模拟的是**当前代码不可达**的状态（Chroma 批次上限、半写、失效异常、清理异常），它们被记录为 GUARD——**只报告、不强制、不修复**。验证任务不越界：发现的问题 owner 是 T0104/T0602/全局 handler，不是 T0503。

| AC | 场景 | 断言方式 | 记录 |
|----|------|---------|------|
| AC-F002-08 全页失败 → 422 FILE_PARSE_ERROR | V3（D-2 替代：空白 .txt） | HTTP 422 + `error.code`（脚本 L275-279） | 脚本设计级核对 ✓ |
| AC-F002-09 FAILED 不残留（4 强制行为） | V3 `assert_rolled_back` + V4 重传 | 行为 1：raw 目录无该文件；行为 2：chunk_count 等于基线（任何带失败 file_id 的残留 chunk 都会抬高计数——脚本 docstring 的推理链）；行为 3：同上观察（Phase 6 索引建于 `list_chunks`，不在 store 的文件进不了索引——不必等 T0602 才能验）；行为 4：V4 同名重传 → 200；另加第 5 项检查：其他 KB 不受影响 | 脚本设计级核对 ✓ |
| AC-F002-10 SWW 后重传 → 409 | V14（经 F004 warning 通道注入 OCR 警告） | 409 + FILE_ALREADY_EXISTS（脚本 L503-509） | 脚本设计级核对 ✓ |
| TASKS.md T0503 节 AC-F002-10 摘要行口径 | V4（FAILED 后重传 → 200） | 200 + SUCCESS（脚本 L282-297） | 见下"发现" |

- **发现**（诚实记录）:
  - **执行证据与诚实边界**：脚本开发期确有执行痕迹——`backend/app/api/__pycache__` 时间戳（21:04/21:07）证明应用被 TestClient 导入执行过；脚本内的 stderr 过滤器（L568，滤掉 `it/s` / `onnx.tar.gz`）是**实测产物**（ChromaDB 默认嵌入模型的下载进度刷屏才催生了它）。但脚本最终版（22:17 定稿）的完整执行输出未见——T0503 DONE 为用户在 TASKS.md 的宣告，本表按"脚本覆盖 + 开发期执行痕迹 + 用户 DONE"记录，**不虚构最终版全量 PASS**。
  - **TASKS.md T0503 节的 AC-F002-10 摘要行与 SPEC 原文口径不一致**：TASKS.md 写"re-upload after FAILED → 200, not 409"，而 SPEC AC-F002-10 原文是"SUCCESS_WITH_WARNINGS 后重传 → 409"（FAILED 后重传其实是 AC-F002-09 第 4 条）。脚本按 **SPEC 原文**实现（V14 验 409），且 V4 顺带覆盖 TASKS.md 摘要行的读法——两读法都覆盖，无实际缺口；摘要行是文档口径问题，不需改代码。
  - **四个 GUARD 发现全部"owner 化"**：F-1（合法大文件撞 Chroma max batch，owner T0104）、F-2（半写残留 + 同名重传锁定——即 ER Gap-4 的实证观察）、F-3（提交后失效异常——seam 今天是 no-op 不可能触发，owner T0602）、F-4（缺 file 部分的 422 信封是 FastAPI 默认 `{"detail": [...]}`，不是 SPEC 6.7 信封，owner 全局 handler）——验证任务找到的问题全是**别处的问题**，T0503 自己的验收对象（T0308/T0502 回滚）零缺陷。**后续进展**：F-1/F-2 已于 2026-08-25 Phase 5 Gate 修复（`add_texts` 分批持久化 + 批次失败按 file_id 补偿删除），V9/V10 由 GUARD 升级为 CHECK 并复跑 PASS——见 ER §0。
- **Interview Candidates**（保持简短）:

  > Candidate only —— 话术 consolidation 已由 2026-08-26 Phase 5 Learning Review 完成（见 Interview Guide Phase 5 深度章）。

  - **Technical Points**: 验证只走 public interface（SPEC 把回滚机制声明为 implementation detail 的直接延伸）；子进程隔离（ChromaDB 句柄 + Settings 单例两个进程级状态陷阱）；GUARD 与 CHECK 分离；"零业务代码修复"本身是验证结论
  - **Engineering Questions**: "为什么 FAILED 的 4 条强制行为可以用 chunk_count 基线对比验证？" / "为什么验证脚本要跑子进程？" / "GUARD 发现为什么不当 FAIL 处理？"
  - **Candidate Interview Questions**: "怎么验证 ChromaDB 里没有残留 chunk？" / "验证脚本怎么保证不污染真实数据？"（temp 目录重定向 + 子进程隔离 + repo 路径防呆断言）
  - **STAR Candidate**: 无（验证 Task——但"零修复"可作为 Phase 级 STAR 素材候选）

---

## 5. 代码理解（关键代码逐行精读）

> upload.py 全文 230 行（T0502 接线后），结构：模块 docstring（1–24）→ imports（26–37）→ 常量（44–62）→ 校验函数 ×4（65–153）→ 端点（161–217）→ 清理函数（220–229）。

### 5.0 模块 docstring（upload.py:1-24）——docstring 随职责演进而改写

T0501 时代的 docstring 第一段是**范围声明**（"T0501 scope is the validation pipeline only... this module therefore declares no router"——把端点/保存/ingest/失效逐一点名"不归我管"）。T0502 实现时它被改写成**端点流程全景**：

```python
"""File Upload API — POST /api/upload (SPEC F002, Sections 6.3 and 10.2).

Endpoint flow (SPEC F002 Detail normal flow, T0502):
  1-6.  ``validate_upload`` — the pre-ingestion checks below (T0501)
  7.    save the raw bytes to ``uploads/{collection_name}/{file_name}``
  8.    ``IngestService.process`` — parse → clean → chunk → embed → store
  9.    invalidate this collection's keyword index cache
  10.   return the Section 6.3 response

Validation order (SPEC F002 Detail normal flow steps 2-6 + Section 10.2):
  1. file name safety     — 400 `INVALID_FILE_NAME`
  2. extension whitelist  — 400 `UNSUPPORTED_FILE_TYPE`
  3. size limit           — 413 `FILE_TOO_LARGE`
  4. empty file           — 400 `EMPTY_FILE`
  5. knowledge base exists— 404 `COLLECTION_NOT_FOUND`
  6. duplicate file name  — 409 `FILE_ALREADY_EXISTS`

File name safety runs first: SPEC Section 10.2 requires the check to
happen before any filesystem operation, and putting it ahead of the
whole pipeline means no later step ever handles an unvalidated path.

Every check is side-effect free — a rejected upload leaves no file in
``uploads/`` and no data in ChromaDB (AC-SEC-01).
"""
```

逐段读：

- **第一段 = 端点流程全景**：F002 正常流程的 10 步被原样搬进 docstring，并标了"1–6 归 T0501 的 `validate_upload`、7–10 是本模块"。注意第 7 步的保存路径 `uploads/{collection_name}/{file_name}` 和第 9 步的"invalidate this collection's keyword index cache"——这两行就是端点的副作用清单。[ENGINEERING KNOWLEDGE] **docstring 第一段从"范围声明"变成"流程全景"不是风格偏好，是模块职责演进的自然结果**：T0501 时代这个模块只有校验，范围声明防止别人往里加保存逻辑；T0502 时代模块自己就是完整上传流，docstring 改而回答"整个流程长什么样"。docstring 永远和代码在一起，所以它必须和代码同步演进——否则就是 T0501 时代读到的过时文档。
- **第二段 = 顺序契约**：6 步顺序 + 每步的错误码，就是 F002 正常流程 2–6 步的"代码化"。注意这里列的顺序（路径安全第 1）与 TASKS.md Implementation Scope 写的顺序（路径检查第 4）**不一样**——这是实现的有意重排，论证在下一段。
- **第三段 = 重排理由**：SPEC 10.2 要求路径校验"在任何文件系统操作之前"，实现把"任何文件系统操作之前"理解为"整个管道的第 1 步"——后续步骤永远不会接触一个未校验的路径。[ENGINEERING KNOWLEDGE] 这是**防御纵深**：不依赖"前面的步骤不会碰路径"这个假设，而是从结构上消灭该假设。
- **第四段 = 副作用声明**：呼应 AC-SEC-01——被拒的上传在 `uploads/` 和 ChromaDB 都零痕迹。注意它说的是"every check"（六道校验）——校验零副作用这个事实在端点存在之后依然成立。

### 5.1 validate_file_name（upload.py:65-84）——路径遍历的第一道闸

```python
def validate_file_name(file_name: str) -> None:
    if not file_name or file_name in {".", ".."}:
        raise AppError("INVALID_FILE_NAME")
    if PureWindowsPath(file_name).name != file_name:
        raise AppError("INVALID_FILE_NAME")
```

- **逐行讲解**:
  1. `if not file_name`：空文件名直接拒。没有这一步，后面的 `PureWindowsPath("")` 会返回 `.name == ""`，恰好**等于**原文 `""`——basename 等式会漏掉空串。同理 `"."` 和 `".."` 的 `.name` 都是 `""`，也不等于自身，理论上会被第二行挡住——但显式点名这三个特例，读代码的人一眼看到意图，不靠 pathlib 的边角语义。
  2. `PureWindowsPath(file_name).name != file_name`：**核心判定**——一个安全的文件名等于它自己的 basename。`PureWindowsPath("a/b.txt").name == "b.txt" != "a/b.txt"` → 拒。`PureWindowsPath("a\\b.txt")` 在**任何平台**上 `.name` 都是 `"b.txt"` → 拒。为什么不用 `Path`？`Path` 跟随宿主平台：在 Linux 上 `Path("a\\b.txt").name` 是 `"a\\b.txt"`（`\` 不算分隔符）——一个反斜杠文件名会在 Linux 校验通过，然后**在 Windows 上解析成目录路径**。上传文件名没有"平台"可言（它是用户发来的字符串），所以用 Windows 语义判定最严——详见 docstring 与 ER ADR-02。
- **关键设计点**:
  - **拒绝而非改写**：SPEC 10.2 明文禁止 sanitization——不能把 `a/b.txt` 悄悄改成 `a_b.txt`。改写会让用户以为文件按原名存好了，实际文件名对不上。[ENGINEERING KNOWLEDGE] 安全校验的姿势只有两种：拒绝或改写；**改写必须在产品语义里明示**（比如 slug 化），否则就是欺骗。
  - 校验是**纯函数**：输入 str、输出"通过"或异常——不碰任何全局状态，T0502 可以零顾虑地调用。
- **TS 类比**: `PureWindowsPath` ≈ Node 的 `path.win32`；`path.win32.basename("a\\b.txt") === "b.txt"` 在任何操作系统上都成立——同一思想。

### 5.2 validate_extension（upload.py:87-97）——白名单与大小写

```python
def validate_extension(file_name: str) -> None:
    if PureWindowsPath(file_name).suffix.lower() not in _ALLOWED_EXTENSIONS:
        raise AppError("UNSUPPORTED_FILE_TYPE")
```

- **逐行讲解**:
  - `.suffix`：pathlib 的"最后一段扩展名"——`archive.tar.gz` 的 suffix 是 `.gz`（不是 `.tar.gz`），所以按 `.gz` 判；`.bashrc` 的 suffix 是 `""`（点开头的隐藏文件不算有扩展名）。**判定对象是最后的 suffix**，不是文件名的尾部匹配——`"x.txt.exe"` 会被 `.exe` 拒，不会因为"包含 .txt"而放行。
  - `.lower()`：SPEC F002 边界条件明文"扩展名校验不区分大小写"——`DOC.PDF` 与 `doc.pdf` 等价。
  - `_ALLOWED_EXTENSIONS`（upload.py:49-62）：11 个扩展名 = **F003 解析器能处理的全部格式**（.txt/.md/.csv/.json/.log/.pdf/.docx/.xlsx/.xlsm/.xltx/.xltm）。[PROJECT FACT] 白名单不是"产品允许什么"，而是"下游管道能消化什么"——校验规则对齐**下游能力**而不是产品想象力（与 Phase 4 校验对齐存储约束同一个思想）。
- **关键设计点**: 白名单是 set——成员检查 O(1)；而且它把"支持哪些格式"从逻辑里提出来变成数据，未来 F003 加格式只改这一张表。
- **TS 类比**: ≈ `["md","pdf",...].includes(path.extname(f).slice(1).toLowerCase())`——但 Python 用 set 成员检查，JS 习惯用 array includes。

### 5.3 validate_content（upload.py:100-112）——字节检查

```python
def validate_content(content: bytes) -> None:
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise AppError("FILE_TOO_LARGE")
    if len(content) == 0:
        raise AppError("EMPTY_FILE")
```

- **逐行讲解**:
  - `len(bytes)`：Python 的 `len()` 对 bytes 返回**字节数**——1 MB = 1024×1024 字节的换算是显式写出来的（`settings.MAX_UPLOAD_SIZE_MB` 存的是"MB"这个人类单位，代码负责换算）。
  - **边界语义**：`>` 不是 `>=`——**恰好 50 MB 允许**，51 MB 拒绝。这条在 SPEC F002 边界条件里明文："50 MB 本身允许上传"。边界语义是 AC-F002-04 的核心（"51 MB 拒绝"的前提是"50 MB 通过"），代码把它翻译成了严格的 `>`。
  - 空文件检查在大小检查之后：0 字节不可能超限，两个分支天然互斥，顺序不影响结果——但"先查大小再查空"让读代码的人先处理"太大"这个更明显的错误。
- **关键设计点**: `content: bytes` 参数**只在这里消费**——`validate_upload` 把整个文件内容传进来，校验函数只用 `len()` 看两眼。这是"依赖最小化"的签名设计：函数声明它只需要字节数，而不是文件对象。
- **TS 类比**: `content.length` 在 JS 里对 Buffer 也是字节数；但 JS 的 Buffer 有 `.byteLength` 区分，Python 的 bytes 没有"字符长度"概念，`len()` 就是字节数。

### 5.4 validate_upload（upload.py:115-153）——编排

```python
def validate_upload(
    file_name: str,
    content: bytes,
    collection_name: Optional[str] = None,
) -> str:
    validate_file_name(file_name)
    validate_extension(file_name)
    validate_content(content)

    collection = collection_name or settings.CHROMA_COLLECTION
    store = ChromaVectorStore()
    if collection not in store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    existing = {file["file_name"].lower() for file in store.get_files(collection)}
    if file_name.lower() in existing:
        raise AppError("FILE_ALREADY_EXISTS")

    return collection
```

- **逐行讲解**:
  1. **三个纯校验先行**：路径 → 扩展名 → 内容，全部无副作用。KB 存在性和同名检查**放在它们后面**——因为这两步要实例化 `ChromaVectorStore` 并读库，是"外部依赖调用"，把纯函数排在前面是校验管道的最低成本顺序。
  2. `collection_name or settings.CHROMA_COLLECTION`：SPEC F002 步骤 4——collection_name 为空则用默认值。`or` 的语义是 falsy 兜底：`None` 和 `""` 都会落到默认值（⚠️ 与 JS 的 `??` 不同，`??` 只兜 null/undefined——见手册 28.4）。
  3. **KB 存在性**：`collection not in store.list_collections()`——沿用 Phase 4 的存在性检查惯用法（collections.py 同样这么写）。返回的 `collection` 是**解析后的目标 KB 名**，供 T0502 保存文件时使用——校验函数的返回值把"用户没指定 KB"这个分支的决策传给了下游。
  4. **同名检查**（重点，见下）。
  5. `return collection`：**解析后的 collection 名**是唯一的返回值——校验通过的唯一"产出"是"目标 KB 名"。文件内容、文件名都不被修改或传递——校验层不改数据，只做闸门。
- **同名检查的三个设计点**:
  - **数据源是 `get_files(collection)`**——从 chunk metadata 按 file_id 聚合出的文件列表（Phase 1 T0107），**不是查 uploads 目录**。原因一：v1 零元数据库（SPEC 7.3），"该 KB 有哪些文件"的唯一权威来源是 chunk metadata；原因二：[PROJECT FACT] 摄取 FAILED 的文件没有 chunk → 不出现在列表里 → **可重传**——这正是 SPEC F002 "FAILED observable behavior" 第 4 条（再次上传同名文件不得被上一次失败阻塞）在查重环节的天然兑现，不需要任何特殊逻辑。
  - **作用域 = 单个 KB**：`existing` 只包含目标 KB 的文件——AC-F002-03（不同 KB 同名文件互相独立）由数据源天然保证。
  - **大小写不敏感**：`file_name.lower() in existing`——注释给出的理由是 uploads/ 目录在大小写不敏感的文件系统（Windows/macOS 默认）上，`Doc.pdf` 会覆盖 `doc.pdf`，所以查重也必须大小写不敏感，否则查重和文件系统行为脱节。⚠️ 这是实现比 SPEC 字面（"同名"）更严的扩展——见 ER ADR-03 与 Pending #36。

### 5.5 upload_file（upload.py:161-217）——端点编排与失败清理

```python
@router.post("/upload", response_model=UploadResponse)
def upload_file(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Form(default=None),
) -> UploadResponse:
    file_name = file.filename or ""
    content = file.file.read()
    collection = validate_upload(file_name, content, collection_name)

    target = Path(settings.UPLOAD_DIR) / collection / file_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    try:
        result = IngestService.process(target, file_name, collection)
    except Exception:
        _discard_saved_file(target)
        raise

    if result["status"] == "FAILED":
        raise AppError("FILE_PARSE_ERROR")

    invalidate_keyword_index(collection)

    return UploadResponse(
        status=result["status"],
        message=_STATUS_MESSAGES[result["status"]],
        file_id=result["file_id"],
        file_name=result["file_name"],
        chunks=result["chunks_count"],
        collection_name=collection,
        warnings=result["warnings"],
    )
```

逐行读（按"验证 → 副作用 → 失败处理 → 响应"四段）：

- **验证段（190-192）**：`file.filename or ""` 兜住 `filename` 为 `None` 的边角（Starlette 类型上允许 None）；`file.file.read()` 把整个上传读成 bytes——注意**读发生在校验之前**，所以"413 太大"要等全量收完才返回（详见 5.5 末的性能点）。校验通过后才拿到 `collection` 和写入权限——`validate_upload` 的返回值为第 194 行所用（T0501 的"唯一产出"在这里被消费）。
- **保存段（194-196）**：`target.parent.mkdir(parents=True, exist_ok=True)` 建 `uploads/{collection}/` 目录（`exist_ok=True`：目录可能已存在，不是错误）；`target.write_bytes(content)` 原样写字节。**为什么 `collection` 不单独做路径校验？** 因为 KB 存在性检查在前——collection 名能通过检查，说明它来自 ChromaDB，而 ChromaDB 里只有经 Phase 4 T0401 命名正则（不含 `/`、`\`）创建的名字——路径安全是**传递保证**的（ER ADR-08）。[ENGINEERING KNOWLEDGE] 传递保证的信任链是"上游校验 → 存储 → 下游复用"，链条任何一环被绕过（比如未来有别的入口直接写 ChromaDB）保证就失效——它比"每个环节各自校验"省事，但信任链必须写清楚。
- **失败处理段（198-205）——本 Task 的核心设计**：
  - `try` 只包住 `IngestService.process` 一步——作用域最窄，其余代码的错误不会被误清理。
  - **失败有两条路径，两个清理责任方**（docstring 明说，ER ADR-06）：
    1. **FAILED 状态**（优雅失败，如全文解析后为空）：`IngestService._fail` 已经删掉 raw file + `delete_by_file` 清 ChromaDB（ingest.py:675-676）——端点**不再**删文件，只把 FAILED 映射成 `AppError("FILE_PARSE_ERROR")`（→422，errors.py:56）。不重复清理，责任单一。
    2. **异常**（如损坏 PDF 抛 FILE_PARSE_ERROR、加密 PDF 抛 ENCRYPTED_PDF）：`except Exception: _discard_saved_file(target); raise`——端点删掉自己保存的 raw file 后**原样重抛**。为什么这里只删文件不清 ChromaDB？因为异常发生在 ingest 中途，file_id 在 `IngestService.process` 内部生成、异常时对端点**不可见**——端点能清理的只有自己写入的东西。[ENGINEERING KNOWLEDGE] 这就是**"副作用归属"原则**：谁写入，谁负责回滚；外层只能清理自己产生的副作用，看不到的不能假装清理（残留风险见 ER Gap-4）。
  - 注意 FAILED 的 `raise` 在 `try` **外面**——FAILED 时文件已由 IngestService 删除，若误放 try 内会触发第二次删除（`missing_ok=True` 使其无害，但语义错了）。
- **失效段（207）**：`invalidate_keyword_index(collection)` 只在**通过 FAILED 检查之后**执行——即只有 200 结果才失效。为什么失败路径不用失效？**失败的上传没有写入任何 chunk → 索引内容没变 → 索引天然正确**。这是"失败零副作用"推理链的第三环（第一环：校验零写；第二环：FAILED 回滚）。[PROJECT FACT] 当前 seam 本体是 no-op（keyword_index.py:42-44），真实 dirty-flag 行为 DEFER T0602——但调用位置已经按正确语义放好，T0602 落地时无需再动这里。
- **响应段（209-217）**：`_STATUS_MESSAGES[result["status"]]`——dict 查表拿中文文案，两个键与 SPEC 6.3 的示例 JSON 一字不差。**为什么不会 KeyError？** 到这个位置 `result["status"]` 只可能是 SUCCESS / SUCCESS_WITH_WARNINGS（FAILED 已在 204 行 raise）——穷举性由**控制流**保证，不是运气。[ENGINEERING KNOWLEDGE] dict 查表 + 提前排除不可能分支，是"用控制流缩小类型"的常见姿势。
- **性能点（诚实记录）**：`file.file.read()` 在**校验之前**整读——一个超限的上传也要全量收完才得到 413（Starlette 的 SpooledTemporaryFile 会把大文件滚到磁盘，内存有界但带宽无界）。SPEC 只要求"校验先于写入"，读入内存不在其列——单用户部署可接受，记录在 ER 第 6 节。

### 5.6 _discard_saved_file（upload.py:220-229）——永不掩盖主错误的清理

```python
def _discard_saved_file(target: Path) -> None:
    try:
        target.unlink(missing_ok=True)
    except OSError:
        logger.exception("upload rollback: failed to delete %s", target)
```

- **`missing_ok=True`**：文件已不存在也不算错误（幂等删除——手册 25.7 在 T0308 FAILED 回滚见过，这里是第二次使用）。
- **`except OSError: logger.exception(...)` 而不是 raise**：清理失败**不能掩盖**正在重抛的摄取错误——异常路径的目标是"把原始错误带给调用方"，清理只是顺带。清理失败用日志留下证据（`logger.exception` 自动附 traceback，手册 27.4），残余路径可从日志追回。
- **TS 类比**：≈ catch 块里的 `fs.rmSync(path, { force: true })` + `console.error`——JS 的 `finally` 里写清理也是这个思路，但 Python 版显式限制了"只捕获 OSError"（`finally` 里的 throw 会吞掉原始异常，这里用窄 except 避免同类问题）。

### 5.7 verify_t0503_rollback.py（586 行）——验证脚本精读

> 脚本全文结构：docstring（1–59，声明替代 D-1/D-2 与 GUARD 决策 D-4）→ 顶层与 `sys.path`（61–70）→ `run_probe` 子进程主体（73–527）→ `main` 父进程（530–585）。读脚本的顺序是父进程 → 子进程，但**理解**脚本的顺序是反的：先看子进程里"验什么"，再看父进程里"为什么套壳"。

#### 5.7.1 环境变量先于 import（脚本 L76-83）——Settings 单例陷阱

```python
def run_probe(tmp_root: Path) -> int:
    import os
    os.environ["UPLOAD_DIR"] = str(tmp_root / "uploads")
    os.environ["CHROMA_PERSIST_DIR"] = str(tmp_root / "chroma")

    from fastapi.testclient import TestClient
    import app.services.embedding as embedding_mod
    ...
```

- 所有 `app.*` 的 import **都在函数体内**——因为 [config.py](../../backend/app/core/config.py) 的 Settings 是 Pydantic BaseSettings 单例，`UPLOAD_DIR` 在 **import 那一刻**从环境变量读定。模块顶层先 import 了 app，再改环境变量就晚了（单例已经拿着旧值）。
- 这解释了为什么 `run_probe` 的 docstring 说 "every app import lives inside this function"——**单例的初始化时机就是环境变量的注入时机**。[ENGINEERING KNOWLEDGE] 测试里最常见的坑之一：单例 + 环境变量 = "改晚了没生效，改早了污染别的测试"。解法只有两种：先设 env 再 import（本脚本），或把配置改成可注入参数（改动产品代码）。

#### 5.7.2 patched()（脚本 L114-127）——项目第一个 `with` 语句

```python
@contextmanager
def patched(target, attr, value):
    is_class = isinstance(target, type)
    missing = object()
    original = target.__dict__.get(attr, missing) if is_class else getattr(target, attr)
    setattr(target, attr, value)
    try:
        yield
    finally:
        if is_class and original is missing:
            delattr(target, attr)
        else:
            setattr(target, attr, original)
```

- `@contextmanager` 把生成器函数变成 with 资源：`yield` 之前的代码是"进入"，`finally` 里是"退出"——这是**项目第一个 `with` 语句 + 第一个生成器函数**（手册 §16 "尚未遇到"表的两条预言同时兑现，`yield from` 仍未见）。
- `is_class = isinstance(target, type)`：类是 type 的实例——patch 一个类（如 `IngestService._parse`）还是模块/实例，取值姿势不同：类要查 `__dict__` 而不是 `getattr`（`getattr` 会沿 MRO 找父类，可能拿到父类方法，恢复时就错设到子类上）；`missing = object()` 哨兵 + `delattr` 恢复保证 patch 不留痕。
- 整个脚本的场景注入全靠它（V6–V12 的 `with patched(...)`）——**被验证代码零改动**，不为可测性给产品代码加钩子。

#### 5.7.3 基线对比断言（observe L137-144 + assert_rolled_back L196-215）

```python
def assert_rolled_back(tag, collection, name, base) -> dict:
    state = observe(collection)
    check(f"{tag}: no raw file residue", name not in state["raw"], ...)
    check(f"{tag}: no residual chunk/vector/metadata",
          state["count"] == base["state"]["count"], ...)
    check(f"{tag}: file not exposed by get_files()", name not in state["files"], ...)
    check(f"{tag}: no other knowledge base affected",
          others(collection) == base["others"], ...)
```

- 四条检查 = SPEC L457-461 强制行为的逐条翻译 + 一条附加（跨 KB 隔离）：
  1. `name not in state["raw"]` → 行为 1（uploads/ 无残留）
  2. `state["count"] == base["state"]["count"]` → 行为 2（ChromaDB 无残留）——**为什么计数不变等价于无残留**：任何带失败 file_id 的 chunk 都会抬高计数（脚本 docstring 的推理链）；配合检查 3（`get_files` 不含该文件）双重确认
  3. 行为 3（keyword index）**复用同一观察**：Phase 6 索引从 `VectorStore.list_chunks` 全量重建，文件不在 store 就进不了索引——不必等 T0602 才能验证这条
  4. `others(collection) == base["others"]` → 附加检查：回滚不误伤其他 KB（呼应 Phase 4 rename 的跨 KB 语义）
- 基线是**场景启动时拍的**（`case()` L168-173 同时建 collection + 拍基线）——"无残留"定义为"和失败前一样"，而不是"绝对为空"，这样同 KB 既有文件不会造成误判。[ENGINEERING KNOWLEDGE] 状态类断言的通用姿势：**对比的是前后差异，不是绝对状态**。

#### 5.7.4 场景矩阵的覆盖面（V1–V15）

| 场景 | 注入方式 | 验证什么 |
|------|---------|---------|
| V1/V2 | 无注入 | 5 种校验拒绝（400/404/413/409 前身）后零副作用——AC-SEC-01 的端点级复验 |
| V3 | 空白 .txt（D-2） | FAILED → 422 + 4 行为回滚（AC-F002-08/09） |
| V4 | fake_embeddings | FAILED 后同名重传 → 200（AC-F002-09 行为 4） |
| V5 | 无注入 | 成功后重传 → 409（查重对照） |
| V6 | patch `_parse` raise ENCRYPTED_PDF | 解析异常 → 422 + 回滚 |
| V7 | patch `encode_chunks` raise | 嵌入异常 → 500 EMBEDDING_MODEL_ERROR + 回滚 |
| V8 | patch `add_texts` raise | Chroma 持久化异常 → 500 INTERNAL_ERROR + 回滚 |
| V9 | 真实 ~7MB 大文件 | GUARD F-1：Chroma max batch 拒绝合法文件 + 回滚 + 重传不阻塞 |
| V10 | `_partial_add` 半写 | GUARD F-2：孤儿 chunks + 同名重传锁定（ER Gap-4 实证观察） |
| V11 | patch invalidate raise | GUARD F-3：提交后失效异常，raw/chunks 仍一致 |
| V12 | patch `Path.unlink` raise | 清理失败不掩盖原始错误（对应 5.6 节设计点） |
| V13/V14 | fake_embeddings / F004 warning 注入 | SUCCESS / SWW 对照 + AC-F002-10 |
| V15 | 缺 file 部分 | 请求级校验 422 + 零持久化副作用；GUARD F-4（FastAPI 信封） |

- V14 的 SWW 用 `ingest_mod._record_ocr_warning(3, "OCR_PAGE_FAILED")` 走 F004 **真实 warning 通道**注入——替代"真实 Qwen-VL 失败"（dashscope 未装）。
- GUARD 场景（V9–V12）模拟的是**当前代码不可达**的状态：它们报告、不强制、不修复——owner 化（T0104/T0602/全局 handler）。

#### 5.7.5 父进程为什么存在（main L530-579）——Windows 文件句柄

```python
probe_root = Path(tempfile.mkdtemp(prefix="t0503_"))
completed = subprocess.run(
    [sys.executable, str(Path(__file__).resolve()), "--probe-root", str(probe_root)],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
)
```

- **自己起自己**：`--probe-root` 参数切换到子进程模式（L583-584），整个矩阵跑完返回 exit code。为什么必须套壳——ChromaDB 的 Rust 后端把 SQLite/segment 文件句柄持有到**进程结束**；Windows 上进程内清不掉 → 父进程无法 `rmtree` 临时目录。子进程退出 = OS 收句柄 → 父进程清理。这是 Windows 特有的资源生命周期问题。[ENGINEERING KNOWLEDGE] "资源句柄属于进程"是跨语言常识，但只有遇到清不掉的目录时才会被真正学会。
- 两个收尾细节：`emit()`（L548-561）做**编码安全写**——Windows 控制台 GBK 码页可能拒绝 UTF-8 解码产物，写不出去不能搞挂整个 run；stderr 过滤器（L568）滤掉 ChromaDB 默认嵌入模型的 `onnx.tar.gz` 下载进度刷屏（**实测催生的过滤器**）。
- `shutil.rmtree(ignore_errors=True)` + 10 次重试（L571-575）：句柄可能晚一点释放，重试 + 最终警告而不是硬失败。

---

## 6. 数据流（数据在本 Phase 怎么流动）

```
POST /api/upload（T0502 已接线）:
multipart { file, collection_name? }
  ┌─ 校验段（T0501 的 validate_upload，全部先于写盘）─────────────
  │  1. validate_file_name  (str → None 或 AppError INVALID_FILE_NAME 400)
  │  2. validate_extension  (str → None 或 AppError UNSUPPORTED_FILE_TYPE 400)
  │  3. validate_content    (bytes → None 或 AppError FILE_TOO_LARGE 413 / EMPTY_FILE 400)
  │  4. collection 解析      (str|None → str；falsy 兜底为 settings.CHROMA_COLLECTION)
  │  5. KB 存在性            (str in List[str]；不在 → AppError COLLECTION_NOT_FOUND 404)
  │  6. 同名检查             (get_files → set[str]；命中 → AppError FILE_ALREADY_EXISTS 409)
  │  → 返回 resolved collection_name (str)
  └─────────────────────────────────────────────────────────────
  ├─ 保存段: mkdir(uploads/{collection}/) → write_bytes   ← 第一个副作用
  ├─ 摄取段: IngestService.process(target, file_name, collection)
  │     └─ 失败两条路径:
  │         a. FAILED 状态 → IngestService._fail 已回滚（删文件 + delete_by_file）
  │            → 端点 raise AppError FILE_PARSE_ERROR (422)      [不重复删文件]
  │         b. 异常 → _discard_saved_file(target) + 原样重抛       [只删端点自己写的文件]
  ├─ 失效段: invalidate_keyword_index(collection)   ← 只在 200 结果后执行
  └─ 响应段: UploadResponse(status/message/file_id/file_name/chunks/collection_name/warnings)
```

- **类型变化**: 校验段里 `content: bytes` 只被 `len()` 消费，零拷贝、零解析；保存段把它**原样写盘**（第一次"内容落地"）；摄取段由 IngestService 解析成文本 → 清洗 → chunks → embeddings → ChromaDB metadata（Phase 3 的数据流，见 phase-03 教材）；响应段把 result dict 的 5 个字段 + 查表文案组装成 `UploadResponse`。**数据在本 Phase 被转手三次，每次都是"接收 → 判断/写入 → 移交"**，模块自己不解析内容。
- **错误在哪一步被拦截**: 校验段 6 个错误码、6 个独立出口（无 try/except——无副作用可清理）；摄取段 1 个映射（FAILED → 422）+ 一个宽 except（清理 + 重抛）；响应段 0 个失败路径（构造 schema 由 FastAPI/Pydantic 验证）。**只有产生副作用的代码段才有 try**——这是本模块错误处理的整体形状（ER 5.4 节展开）。
- **副作用清单（诚实列全）**: ① 写 `uploads/{collection}/{file_name}`（端点）；② ChromaDB 写 chunks（IngestService）；③ keyword index 失效（端点调用 seam）。**任何 4xx/422 响应的请求都不产生任何副作用**——校验在 ① 之前完成；422 的 FAILED 路径由 IngestService 回滚 ①②；异常路径端点回滚 ①。

**T0503 验证数据流**（脚本视角——与产品数据流的对照）:

```
[产品数据流] POST /api/upload ──验证→保存→ingest→失效→响应
[T0503 视角]  同一个端点，但观察的是"失败后数据怎么消失":

  父进程: mkdtemp("t0503_") → subprocess.run(自身, --probe-root)
  子进程: env 重定向（先于 import）→ 每场景:
    case() 拍基线 {raw, count, files, others}
      → 注入（patched 一个函数 / fake_embeddings）
        → POST /api/upload（TestClient）
          → observe() 重拍 → assert_rolled_back 对比
            → GUARD 记录（只报告不强制）
  父进程: 转发子进程输出 → rmtree 重试 → exit code = 子进程结果
```

- 两个视角读同一段代码：产品数据流问"数据怎么进去"，验证数据流问"失败后数据怎么消失、怎么证明它消失了"。**"消失"的证明手段是基线对比**——不是检查"绝对为空"，而是检查"和失败前一样"（第 5.7.3 节）。

---

## 7. 架构设计（本 Phase 的架构影响）

- **新增能力**: 六步上传校验管道（4 个函数 + 1 张白名单表）→ T0502 在同一模块接上 `POST /api/upload` 端点（校验复用零成本——`validate_upload` 一行调用）。项目第一条"上传→入库"的端到端链路就此打通。
- **契约兑现**:
  - **消费**上游契约：VectorStore 的 public 原语（`list_collections` / `get_files` / `add_texts` / `delete_by_file`，后两者由 IngestService 消费）——全程不碰 `_collection` 私有属性（F008 边界延续）；错误体系零新增（全部错误码 Phase 0 就位）；keyword seam 按契约调用（`invalidate_keyword_index(collection)`，no-op 现状按契约不报错）。
  - **兑现** SPEC 10.2："validation 必须发生在任何文件系统操作之前"——校验段**先于保存段执行完毕**（upload.py:190-196 的顺序），被拒请求零痕迹（AC-SEC-01）。
  - **兑现** SPEC 6.3：响应 schema 字段级对齐；FAILED 永不出现在 200（"FAILED 不是 HTTP 200 status" 注释的代码化）。
- **设计边界**:
  - **模块形态的演进**：T0501 交付时是无 router 纯校验模块（[router.py:18-20](../../backend/app/api/router.py#L18-L20) 当时只有注释预留）；T0502 在**同一文件**声明 `APIRouter` + 端点并注册（[router.py:16](../../backend/app/api/router.py#L16)）。校验函数与端点同住一个模块——**单文件 230 行是"一个端点的完整故事"**，跨文件反而要把同一流程拆成两半（ER ADR-05 的复用红利在这里兑现：T0502 零成本消费 T0501）。
  - **校验顺序的重排**：TASKS.md 编排顺序是 扩展名→大小→空→路径→KB→同名；实现是 **路径→扩展名→大小→空→KB→同名**。这是与任务计划的一处**有意偏差**，理由写在 docstring 里（10.2 + 防御纵深），多违规输入的错误码优先级 SPEC 未规定——记录在 ER ADR-01 / Pending #35，Phase Gate Review 确认。
  - **清理责任二分**（T0502 新增）：FAILED 状态的清理归 IngestService（它产生 ChromaDB 副作用，且知道 file_id）；异常路径的 raw file 清理归端点（save 是端点的副作用）。"谁写入谁回滚"在两条失败路径上各自兑现（ER ADR-06）。
- **与既有模式的呼应**: "校验先于副作用"是 Phase 4 建立的原则，Phase 5 把它从"一个端点内部"推进到"整个上传流程的前置阶段"——Phase 4 的 400/404/409 前置在 rename 里是为了防止 4xx 被映射成 500，Phase 5 则是为了"被拒请求零痕迹"（AC-SEC-01）。T0502 的"失败两条路径 × 两个清理责任方"则呼应 Phase 4 rename 的"两层补偿"（ADR-06）——副作用归属原则的第二次出现。
- **T0503 验证脚本的架构三原则**（详见 ER ADR-09/10/11）: ① **public interface only**——SPEC L463 把回滚机制声明为 implementation detail，断言只走 `get_files`/`get_chunk_count`/文件系统，实现可自由重构；② **子进程隔离**——ChromaDB 句柄进程级持有 + Settings 单例 import 时定值，两个"进程级状态"陷阱一个套壳解决；③ **GUARD/CHECK 分离**——不可达状态的探针只报告不修复，问题 owner 化（T0104/T0602/全局 handler）。
- **零业务代码改动本身是架构证据**：T0308 的 `_fail` + T0502 的 `_discard_saved_file` 在 15 个端点级场景下无需任何修补——"副作用归属"（ADR-06）经受住了第一次实证，而不是被验证推翻。

---

## 8. Engineering Review（工程决策复盘摘要）

> 完整复盘见 [phase-05-engineering-review.md](./engineering-review/phase-05-engineering-review.md)。本文档只放一句话结论，不展开。

- **ADR-01**: 校验顺序重排（路径安全第一）——TASKS 排第 4 → 实现排第 1，理由 = SPEC 10.2 + 防御纵深；代价 = 多违规输入先报 INVALID_FILE_NAME（Pending #35）
- **ADR-02**: `PureWindowsPath` 跨平台统一路径判定——上传文件名按 Windows 语义判定（最严），消除"Linux 放行、Windows 成路径"的平台差异绕过
- **ADR-03**: 同名检查大小写不敏感——SPEC 字面未规定，实现为对齐大小写不敏感文件系统的覆盖风险而收紧（Pending #36）
- **ADR-04**: 查重数据源 = `get_files` 派生聚合——零元数据库下的唯一权威来源，且天然兑现"FAILED 文件可重传"（F002 强制行为）
- **ADR-05**: T0501 纯校验模块交付——校验与端点拆两个 Task 的边界设计；T0502 在同一模块接线，复用零成本（ADR 结论已验证）
- **ADR-06**（T0502）: 清理责任二分——FAILED 状态的清理归 IngestService（它知道 file_id），异常路径的 raw file 清理归端点（save 是端点的副作用）；不重复清理、不越界清理
- **ADR-07**（T0502）: keyword index 只在 200 结果后失效——失败上传零 chunk → 索引天然正确；调用位置已按正确语义放好，真实 dirty-flag 行为 DEFER T0602
- **ADR-08**（T0502）: `collection_name` 不单独做路径校验——KB 存在性检查 + Phase 4 命名正则的**传递保证**（信任链：上游校验 → ChromaDB → 下游路径拼接）
- **ADR-09**（T0503）: 验证只走 public interface——SPEC 声明回滚机制是 implementation detail 的直接延伸；断言与实现解耦（`get_files`/`get_chunk_count`/文件系统，不碰私有属性）
- **ADR-10**（T0503）: 子进程隔离——ChromaDB Rust 句柄进程级持有 + Settings 单例 import 时读 env，两个陷阱一个套壳
- **ADR-11**（T0503）: 声明替代与 GUARD 分离——缺依赖用走相同失败分支的替代品（保真度靠论证）；不可达状态只观察不修复（owner 化 T0104/T0602/全局 handler）

**已知缺口**: T0503 脚本落地 + 开发期执行痕迹（pycache 21:04/21:07、stderr 过滤器为实测产物）——Gap-1"无已执行的实测"大部分观察项已填；Phase 5 Gate 修复后脚本已全量复跑 PASS（ER §0），剩余 Phase 12 正式回归；Gap-4/Gap-5 经 V10/V9 GUARD 观察升级为实证，并于 2026-08-25 Gate 修复（F-1 分批持久化 / F-2 补偿删除——ER §7.1 REMEDIATED）；无自动化测试脚本（延续 Phase 4 Finding #4，固化待 T1203）；FAILED→422 丢弃 warnings（AC-F004-04 口径，Pending #37）；新增 F-4 发现（FastAPI 请求级校验 422 信封 ≠ SPEC 6.7，owner 全局 handler）→ Pending #38。

---

## 9. Technical Decision（技术决策备忘录）

| 决策 | 备选方案 | 选择理由 | 代价/边界 |
|------|---------|---------|----------|
| 路径检查提到管道最前 | 按 TASKS 顺序排第 4 | SPEC 10.2 要求先于任何文件系统操作；后续步骤永不接触未校验路径（防御纵深） | 多违规输入先报 INVALID_FILE_NAME（如 `../bad.exe`）——SPEC 未规定优先级，Pending #35 |
| `PureWindowsPath` 判定路径成分 | `Path`（随平台）/ 手写 `\` 判断 | 上传文件名是用户发来的字符串，没有"平台"；Windows 语义最严，Linux 上也能挡住 `..\` | 语义即"所有上传名按 Windows 规则判"——文档化即可，无实际代价 |
| 同名检查大小写不敏感 | SPEC 字面的精确同名 | uploads/ 在大小写不敏感文件系统上 `Doc.pdf` 会覆盖 `doc.pdf`——查重必须与文件系统行为对齐 | 比 SPEC 字面更严，可能拒绝产品想要的 `doc.pdf` + `Doc.pdf` 并存——Pending #36 |
| 查重用 `get_files()` 派生聚合 | 扫 `uploads/{kb}/` 目录 | chunk metadata 是零元数据库下的唯一权威；FAILED 文件无 chunk 天然可重传（F002 强制行为第 4 条） | 每次上传 O(全 KB chunks) 聚合——规模代价见 ER 第 6 节 |
| FAILED 清理归 IngestService，端点只映射 422 | 端点统一清理（FAILED + 异常） | IngestService 的 `_fail` 已做全量回滚且**知道 file_id**；端点重复删除违反"责任单一" | 责任分散在两层——IngestService 语义若变化（如不再删文件），端点会静默泄漏文件（两层契约靠 docstring 咬合，ER ADR-06） |
| keyword index 只在 200 结果后失效 | 无条件失效（任何结果都失效） | 失败上传零 chunk → 索引内容没变 → 失效是多余操作 | 依赖"失败必零 chunk"的推理链——T0503 验证 FAILED 回滚时顺带确认（ER ADR-07） |
| `collection_name` 不做路径校验 | 与 file_name 一样过 `validate_file_name` | KB 存在性检查 + Phase 4 命名正则（禁 `/`、`\`）传递保证路径安全 | 信任链依赖"ChromaDB 只含合法名"——未来若有别的入口直写 ChromaDB 则失效（ER ADR-08） |
| 验证只走 public interface | 直查 ChromaDB 私有属性 / 直接读 chroma_db 文件 | SPEC L463 声明回滚机制是 implementation detail——验证与实现解耦，实现可重构 | 断言粒度粗（chunk_count 代理"无残留"），但换来重构自由（ER ADR-09） |
| 子进程隔离（脚本自起子进程） | 进程内跑 + 手动清临时目录 | ChromaDB Rust 句柄进程级持有，Windows 进程内清不掉；子进程退出 = OS 收句柄 | 每次运行多一个解释器进程（~秒级启动）；输出经父进程转发需处理控制台编码（ER ADR-10） |
| GUARD 不强制失败 | 发现即 FAIL | 不可达状态的问题 owner 在别的 Task（T0104/T0602/全局 handler）——验证不越界修代码、不因别处的问题判自己 FAIL | GUARD 靠人工阅读消化；需要纪律（D-4 决策明确写出）（ER ADR-11） |
| 声明替代（D-1/D-2） | 装齐 PyMuPDF/sentence-transformers 跑字面场景 | 环境缺依赖；替代品与字面 fixture 在相同代码分支汇合（空白 txt 与"无有效文本 PDF"都走"清洗后为空 → FAILED"） | 保真度靠论证而非实现；F007 不在本 Task 范围所以 stub 无信息损失（ER ADR-11） |

---

## 10. Interview Notes（面试速记）

> 更新时机遵守 **Interview Update Cadence**：T0501/T0502/T0503 均为普通 Task，本节只记候选素材；Phase Gate Review 后的 Phase 5 Learning Review 统一筛选去重再更新 `dx-rag-interview-guide.md`。**已完成**（2026-08-26）：本节候选素材经筛选、去重后晋升为面试指南 Phase 5 深度章（30 秒 + 1-2 分钟 + STAR + 12 高频追问 + 4 工程深问）。

- **高频问题**（候选）:
  1. "上传校验有哪几道？顺序为什么这么排？" → 六道 + 路径安全第一（10.2 + 防御纵深）
  2. "路径遍历怎么防？" → basename 等式 + PureWindowsPath 跨平台 + 拒绝而非改写
  3. "同名检查为什么能允许重传失败文件？" → 查重走 chunk 聚合，FAILED 无 chunk = 不可见
  4. "上传失败时文件谁删的？" → 两条失败路径两个责任方：FAILED 状态由 IngestService 回滚（它知道 file_id），异常路径端点删自己保存的 raw file 后重抛——谁写入谁回滚
  5. "为什么 keyword index 只在成功后失效？" → 失败上传零 chunk → 索引内容没变 → 天然正确（失败零副作用的推理链）
  6. "上传失败的回滚是怎么验证的？" → 15 场景端点级矩阵（TestClient）+ 断言只走 public interface + 基线对比 + GUARD/CHECK 分离——结果零业务代码修复
- **亮点话术**: "上传入口的设计主线是**副作用归属**：校验段零写入（被拒请求零痕迹），失败清理按'谁写入谁回滚'分到两个责任方，keyword index 只在内容真的变了之后才失效。三条推理链都指向同一个原则——副作用和清理责任同址。这套设计在 T0503 拿到了端点级实证：15 个场景（四条失败路径 + 成功对照 + 4 个 GUARD 观察项），零业务代码修复。"
- **诚实边界**: T0503 验证脚本已就位并留下**开发期执行痕迹**（应用被 TestClient 导入执行、脚本内的 stderr 过滤器是实测产物）；最终版完整输出未见——面试时说"验证按 TASKS.md DONE + 开发期执行痕迹"，不虚构"我亲眼看到 15/15 PASS"。另外两处待确认项：FAILED→422 的响应目前不带 warnings（Pending #37）；缺 file 部分的请求级 422 用的是 FastAPI 默认信封而非 SPEC 6.7 信封（Pending #38）。

---

## 11. Future Improvement（未来改进方向）

| 方向 | 触发条件（什么时候需要） | 是否 SPEC 已规划 | 相关条款 |
|------|------------------------|----------------|---------|
| Magic-byte 内容校验 | 安全要求提升（扩展名可伪造） | 是（v1 明确 out of scope） | SPEC 10.2 Future consideration |
| 文件名 Unicode 规范化（NFC/NFD） | 跨系统上传（macOS NFD 文件名绕过同名检查） | 否（个人复盘建议） | — |
| 查重索引化 / 元数据库 | 单 KB 文件数大时 `get_files` 聚合变慢 | 是 | SPEC 7.3（规模终局） |
| 上传大小流式限制 | **T0502 已确认该形态**：`file.file.read()` 在 413 之前整读全量（磁盘 spool 保内存有界、带宽无界）；大文件并发上传时需要 | 否（个人复盘建议） | — |
| 校验-保存原子化（TOCTOU） | 多用户并发上传同名文件；`write_bytes` 的静默覆盖需改为排他创建（`'x'` 模式）或临时名+原子 rename | 否（个人复盘建议，ER Gap-3） | SPEC F002（同名规则） |
| FAILED→422 透出 warnings | 产品确认 AC-F004-04 的 "warnings 包含 N 条记录" 对错误响应也适用 | 待定 | Pending #37 |
| Chroma max batch 对合法大文件的拒绝 | 单个合法文件切分后超过 Chroma 单批次上限（T0503 GUARD F-1） | 否（验证发现） | ✅ 已修复（2026-08-25 Phase 5 Gate：`add_texts` 按 `get_max_batch_size` 分批持久化，V9 升级 CHECK 复跑 PASS） |
| 批次失败留下的半写 chunk（file-level 原子性） | `add_texts` 多批次写入中途失败会留孤儿 chunks + 同名重传锁定（T0503 GUARD F-2 = ER Gap-4） | 否（验证发现） | ✅ 已修复（2026-08-25 Phase 5 Gate：批次失败按 file_id 补偿删除，V10 升级 CHECK 复跑 PASS） |
| 请求级校验错误统一信封 | FastAPI RequestValidationError（缺 file 部分等）返回框架默认 `{"detail": [...]}`，与 SPEC 6.7 "All error responses" 矛盾（T0503 GUARD F-4） | 待定 | Pending #38 |
| 验证脚本固化为回归套件 | Phase 12 T1203 集成验证需要可重复运行的验收 | 是 | T1203 / ER Gap-2 |

---

## 12. 自测题

1. **顺序题**：六步校验的实现顺序是什么？它和 TASKS.md 编排顺序差在哪？为什么重排？多违规输入（`../bad.exe`）会先报哪个错误码？
2. **路径题**：写出 `PureWindowsPath` 对 `"a/b.txt"`、`"a\\b.txt"`、`"."`、`""` 四个输入的 `.name`，并说明 basename 等式为什么能挡住前两个、为什么后两个需要显式特判。
3. **扩展名题**：`"archive.tar.gz"`、`".bashrc"`、`"DOC.PDF"` 三个文件名的 `.suffix.lower()` 各是什么？各自通过/拒绝？
4. **查重题**：为什么同名检查不扫 uploads 目录而走 `get_files()`？一个摄取 FAILED 的文件（已写入又回滚）会挡住同名重传吗？为什么？
5. **动手练习**：写出三个输入——51 MB、恰好 50 MB、0 字节——在 `validate_content` 里各自走哪个分支（用 `MAX_UPLOAD_SIZE_MB = 50` 心算）。
6. **动手练习**：给 `validate_file_name` 写 8 个边界输入（参考 Phase 4 T0404 的边界用例风格：空串 / `.` / `..` / 纯文件名 / `/` 前缀 / 子目录 / 反斜杠 / 合法中文名），逐个预测结果，再对照代码推演一遍。
7. **失败路径题**（T0502）：一次上传在 ingest 阶段失败，有哪两种失败形态？各自由谁清理什么？为什么 FAILED 的 `raise` 不能放进 `try` 块里？
8. **查表题**（T0502）：`_STATUS_MESSAGES[result["status"]]` 为什么只有两个键也不会 KeyError？如果把 FAILED 的检查删掉，运行时会发生什么？
9. **失效时机题**（T0502）：为什么 `invalidate_keyword_index` 放在 FAILED 检查之后？一个失败的上传如果不失效 keyword index，检索结果会错吗？为什么？
10. **验证方法论题**（T0503）：为什么断言只走 `get_files` / `get_chunk_count` / 文件系统，而不用 file_id 直查 ChromaDB？SPEC 的哪句话支持这个选择？"chunk_count 等于基线"为什么能等价于"无残留 chunk"？
11. **子进程题**（T0503）：为什么整个验证矩阵必须跑在子进程里？"环境变量先于 import"解决的是什么问题？如果 Settings 不是 import 时读 env 的单例，还需要这个套壳吗？
12. **GUARD 题**（T0503）：V10 的 `_partial_add` 模拟了什么？为什么它是 GUARD 而不是 CHECK？V12 的 `Path.unlink` patch 验证了 5.6 节的哪个设计点？

---

> **T0503 学习收官 —— Phase 5 Learning Pass 完成（2026-08-25）**：T0501 的六道校验 + T0502 的端点编排 + T0503 的回滚验证合起来是一条**已验证**的"上传→入库"链路——主线只有一个词：**副作用归属**（校验零写、失败清理责任二分、索引只在内容真的变了之后失效），而 T0503 把它从设计主张变成了实测结论：15 个端点级场景、零业务代码修复。诚实声明：T0503 脚本留有**开发期执行痕迹**（pycache 时间戳、实测催生的 stderr 过滤器），但最终版（22:17 定稿）的完整执行输出未见——AC-F002-08/09/10 按"脚本覆盖核对 + 开发期执行痕迹 + 用户 TASKS.md DONE 宣告"记录，不虚构全量 PASS；Phase 12 T1203 正式集成回归仍待执行。另诚实记录两处待 Gate Review 的口径问题：FAILED→422 丢弃 warnings（Pending #37）与请求级校验 422 的 FastAPI 默认信封（Pending #38，来自脚本 GUARD F-4）。两层文档各司其职：看代码来这，看取舍去 Engineering Review，备面试去 Interview Guide 的 Phase 5 深度章（2026-08-26 Phase 5 Learning Review 已 consolidation：30 秒 + 1-2 分钟 + 验证驱动修复 STAR + 12 高频追问 + 4 工程深问）。**后续进展**：Phase 5 Gate Review 裁定 PHASE_5_FAIL（AC-F002-01）→ F-1/F-2 修复完成（`add_texts` 分批持久化 + 补偿删除，V9/V10 升级 CHECK 全量复跑 PASS）→ Re-review 待执行。**本次学习到此为止，不启动下一 Task。**
