# Phase 12 — Integration & Acceptance Technical Learning

> **Phase 状态**：GATE REMEDIATION（T1201、T1202、T1204 BLOCKED；T1203 DONE；不得进入新 Phase）
> **本文档状态**：2026-09-07 BGE 规格冲突修订与真实模型证据已同步；DashScope / DeepSeek live acceptance 仍待单独授权
> **当前证据**：原 Gate finding `SPEC_CONFLICT` 已按产品决策修复：保留 `BAAI/bge-small-zh-v1.5`，SPEC v1.7 / implementation / fixtures 统一为 512 维。官方本地模型 revision `7999e1d3359715c523056ef9478215996d62a620` 的完整性、加载、4×512 norm、lazy singleton 与真实 BGE + 临时 Chroma 中文同义排序均为 **REAL 4/4 PASS**；focused embedding 3/3、T0503 56/56、T1201 81/81、T1202 46/46、T1203 43/43、T1204 29/29及完整backend 81/81均exit 0。
> **证据边界**：T1201–T1204 broad probes仍用512维deterministic BGE substitute以保持分支可重复；BGE真实性由独立`verify_bge_model.py`提供。DashScope OCR与DeepSeek真实回答/grounding/history/prompt-injection均为`NOT_AVAILABLE`，未调用、未标PASS。原100% audit结论已撤回，当前Phase Gate仍为`PHASE_12_FAIL — FIX_REQUIRED`。
> **本轮边界**：只做Phase 12 Gate remediation、隔离测试与证据修正；不读取/展示`.env`密钥，不调用外部付费API，不触碰业务`uploads`/`chroma_db`，不启动新Phase，不commit/push。

---

## 0. 三层文档边界

| 层 | 当前归属 | T1201–T1204 Learning Pass 的职责 |
|---|---|---|
| Technical Learning | 本文件 | 解释三条跨功能 harness 与最终审计怎样组合、各边界是真是假、怎样从 observable behavior 证明 AC |
| Engineering Review | 尚未建立独立 Phase 12 文件 | 后续累计 ADR、failure taxonomy、scale 与 Known Gaps；本轮只保留短摘要 |
| Interview Guide | [项目级指南](./interview-notes/dx-rag-interview-guide.md) | T1201–T1204 只记录 candidates，不在 Phase 未完成时生成完整答案或 STAR |
| Phase Gate / Learning Review | Gate已执行并裁定`PHASE_12_FAIL — FIX_REQUIRED`；当前remediation | focused probe PASS不等于Task或Gate PASS；Learning Review仍待Gate通过 |

本文件不是 Task Completion Report。它不只回答“81/81、46/46、43/43、29/29 通过”，而是帮助学习者看懂：这些检查穿过了哪些真实层、替代了哪些外部边界、为什么不会污染仓库，以及最终 104 个 AC occurrences 怎样去重为 85 个 ID并映射到组合证据。

---

## 1. Phase 学习：从“模块分别正确”走向“组合路径有证据”

### 一句话定位

Phase 12 不再新增主要产品模块，而是把此前 Phase 的局部实现放进跨层场景，检查同一份输入能否穿过 API、service、storage 与 recovery boundaries，最终兑现冻结 SPEC 的 observable behavior。[PROJECT FACT]

T1201 是第一段：它从真实 `POST /api/upload` 进入，覆盖解析、清洗、切分、Embedding service boundary、Chroma persistence、文件列表和 keyword-index invalidation；同时构造 native/scanned/mixed/partial-failure/all-failed PDF，以及全部 11 种支持扩展名。[PROJECT FACT]

T1202 是第二段：它先经真实 collection/upload API 把已知文本写入真实临时 Chroma，再从真实 `POST /api/query` 进入，执行 keyword/vector retrieval、`chunk_id` merge、0.3/0.7 fusion、relevance filter、context/history、DeepSeek client orchestration 与 backend-owned sources。只有 embedding model 与 DeepSeek transport 是 deterministic substitutes。[PROJECT FACT]

T1203 是第三段：它把同一文件 identity 从真实 upload 带到 list、persisted-chunk preview、cascade delete 与 re-upload，并在两个真实 knowledge bases 中验证同名文件隔离；同时把 `../doc.pdf`、`..\\doc.pdf` 与 `subdir/doc.pdf` 作为原始 multipart filenames 送入上传端点，证明拒绝发生在 filesystem/Chroma 副作用之前。[PROJECT FACT]

T1204 是第四段，也是 audit overlay：它不重跑一份“万能 E2E”，而是冻结 Section 5/12 AC inventory、Section 6 route surface、Section 9 error catalog和mandatory DoD，再把T0503/T1201–T1204、backend regression、frontend build/runtime validation与browser outcomes组合成evidence ledger。T1204自身的29个checks重点关闭F001 lifecycle、literal F008-02与契约清单；85个AC的结论来自整套证据组合，不是29与85之间的一一对应。[PROJECT FACT]

### 核心学习点

- 🟢 **E2E 是路径范围，不是“零替代”的同义词**：本脚本跨过真实应用层与持久化层，但替代两个不可用的重型/外部边界；因此必须同时说清 path coverage 与 dependency fidelity。
- 🟢 **隔离必须发生在 import 之前**：`settings` 在模块 import 时读取环境；ChromaDB 又持有进程级文件句柄。父进程创建 temp root、子进程先设置 env 再 import，才能同时获得正确配置与可回收存储。
- 🟢 **验证 public observable behavior**：HTTP status/error envelope、raw file、file-list API、public VectorStore methods、keyword search 与 same-name retry 比私有 Chroma internals 更接近 SPEC。
- 🟢 **rollback 要证明“副作用消失”**：只看到 422 不够；T1201 同时检查 raw、chunk/vector/metadata projection、keyword index 和 re-upload behavior。
- 🟡 **runtime fixture generation**：DOCX、Excel 和 PDF 在 temp tree 内生成，避免提交大批 binary fixtures，也能精确控制 native/scan/page-order conditions。
- 🟡 **deterministic test double 的形状必须匹配真实 adapter**：假 Embedding model 仍返回 `.tolist()` 可消费的 512 维、L2-normalized matrix；假 OCR response 保持 DashScope SDK 的嵌套对象形状。
- 🟢 **分数名是跨层契约**：`similarity_score → vector_score → final_score → relevance_score` 只在 owner 边界改名；T1202 检查 VectorRetriever 不二次归一化，Hybrid 只按固定公式融合，API sources 原样投影最终分数。
- 🟢 **“空库”与“检索为空”是两个状态**：0 chunks 在 LLM 前返回 409；非空库经 relevance filter 后无结果仍调用 LLM，并用空 context placeholder 触发无信息回答。
- 🟢 **prompt structure 不等于 model safety proof**：T1202 证明 system/user message ownership、恶意文档位于参考资料段和 deterministic double 的预期响应；不证明真实 DeepSeek 在所有 prompt injection 下都服从。
- 🟢 **安全拒绝必须同时验证错误与零状态变化**：T1203 不只断言 400 `INVALID_FILE_NAME`，还在每次危险 filename 前后比较 raw-file snapshot 与两个 KB 的 chunk IDs，避免“报错正确但已经写入”的假安全。
- 🟢 **资源 identity 是 `(collection_name, file_id)`**：同名文件可存在于不同 KB；preview/delete 用 collection 划定租户边界、用不可变 file ID 精确定位，不能让 display filename 变成授权或删除键。
- 🟢 **级联删除的完成条件是多个 observable states 同时消失**：raw file、Chroma chunks/vectors/metadata、旧 keyword cache entry 与旧 file identity 都要消失；随后同名 re-upload 必须得到新 UUID 并重新进入检索。
- 🟡 **required checks 不等于 AC 数量**：四份 matrix 还包含隔离 guard、KB setup、adapter wiring、identity 与 cleanup checks；T1204的29个checks也不是85个AC的自动逐条证明。AC traceability必须按行为、来源与evidence level映射。
- 🟢 **occurrence 与 unique ID 是两种审计口径**：Section 5有65次、Section 12有39次，其中19个ID重叠，所以总和104次却只有85个唯一ID。前者证明两个source-of-truth都被遍历，后者避免重复计数。
- 🟢 **最终审计是证据组合，不是测试数量相加**：五份backend probes共有255个supporting checks，但它们不能替代AC清单；正确做法是从每个AC回指能证明其Given/When/Then的primary evidence。
- 🟢 **成功rename要保护identity，失败rename要恢复状态向量**：T1204同时比较chunk/file IDs、content、非级联metadata、vector score、raw path与keyword rebuild；只有HTTP 200/500都不足以证明F001。
- 🟡 **清单守卫也有强弱之分**：当前T1204脚本自动守卫65/39/85计数，Learning Pass另做报告矩阵与SPEC的exact-set对照并得到85/85；但脚本没有对每条Given/When/Then做hash或assertion binding，等量替换仍可能绕过count-only guard。
- 🟡 **browser evidence需要分开写real path与substituted edge**：本轮6/6真实经过Next.js→HTTP→Uvicorn→FastAPI；答案与向量语义来自deterministic doubles，所以可证明render/state/error wiring，不能证明live provider质量。
- 🔵 **Windows console 与 dependency deprecation**：本轮日志中的部分中文/破折号被 legacy console 替换为 `?`，且 PyMuPDF 发出 `fitz` API deprecation warning；都没有改变 assertion 与 exit code，但属于工具链维护信号。

### 前置依赖

- Phase 1：`ChromaVectorStore` public interface 与 cosine similarity boundary。
- Phase 3：parse → clean → chunk → embed → store、OCR page tolerance 与 FAILED rollback。
- Phase 4：真实 collection create/list/rename/delete、storage/filesystem cascade与rename compensation；T1204补齐endpoint-level runtime证据。
- Phase 5：[上传 API 与回滚验证](./phase-05-file-upload.md)，尤其是副作用归属、子进程隔离和 public-interface assertions。
- Phase 6：keyword index lazy build / invalidation / rebuild。
- Phase 7：[Vector & Hybrid Retrieval](./phase-07-vector-retrieval.md) 提供 score/identity/fusion/filter contracts；T1202 首次把这些真实实现接到真实 Chroma 与 query API。
- Phase 8：[RAG & QA](./phase-08-rag-qa.md) 提供 context/history/DeepSeek/QAService/query endpoint；T1202 关闭其 deferred composition boundary，但不关闭 live-provider boundary。
- Phase 9：[File Management](./phase-09-file-management.md) 提供 file projection、persisted-chunk preview 与不可逆 cascade orchestration；T1203 把此前 Mocked/substituted seam 推进到真实 upload→delete→re-upload 生命周期。
- Phase 11：四个persistent panels、typed API client、upload validation、QA Markdown/sources与error states；T1204 browser path第一次在Phase 12真实执行其中一组关键交互。

### 推荐阅读顺序

1. 先看本文件第 6 节的 REAL/SUBSTITUTED 数据流；
2. 摄取侧读 [verify_t1201_ingestion.py](../../backend/scripts/verify_t1201_ingestion.py) 的 module docstring 与 `main()`；
3. 查询侧读 [verify_t1202_retrieval_qa.py](../../backend/scripts/verify_t1202_retrieval_qa.py)，先找 real/substituted boundary，再按 retrieval、assembly、API/LLM 三组读；
4. 文件生命周期侧读 [verify_t1203_file_management_security.py](../../backend/scripts/verify_t1203_file_management_security.py)，按 filename security、list/isolation、preview、delete/re-upload 四组阅读；
5. 最终审计先读 [T1204 audit report](../T1204-SPEC-ACCEPTANCE-AUDIT.md)，再读 [verify_t1204_spec_acceptance.py](../../backend/scripts/verify_t1204_spec_acceptance.py) 与 [browser backend harness](../../backend/scripts/serve_t1204_browser_backend.py)，区分report、probe与manual/browser evidence；
6. 对照 [SPEC Section 5](../SPEC.md#5-functional-specifications)、[Section 12](../SPEC.md#12-acceptance-criteria)、[mandatory DoD](../SPEC.md#131-required-mandatory) 与 [coverage matrix](../SPEC.md#15-spec-coverage-matrix)；
7. 最后做第12节自测与练习，确认能分别解释path coverage、dependency fidelity、occurrence/unique口径与尚未验证内容。

---

## 2. Phase 目标：验证三条组合路径与一层最终审计

### T1201 业务目标

用户把一个受支持文件交给上传端点后，系统需要真的得到可检索、可列举、带稳定 identity 的 persisted chunks；失败文件则必须像从未成功上传一样不残留。T1201 把这条业务承诺从跨 Phase 的代码拼图变成一次可重复执行的 verification matrix。[PROJECT FACT]

### T1201 技术目标

- 从真实 FastAPI route 发起 multipart upload，而不是直接调用 parser helper；
- 运行全部 11 种支持扩展名的 dispatcher path；
- 检查文本编码、DOCX table、Excel sheets、PDF native/OCR selection 与 page order；
- 检查 clean/chunk parameters、Embedding contract、9-field metadata 与 public search；
- 检查 `SUCCESS`、`SUCCESS_WITH_WARNINGS`、FAILED→422 和 validation errors；
- 检查 raw/Chroma/keyword side effects 与 retry/duplicate semantics；
- 把环境隔离与 substitutions 写入脚本本身，而不是只存在于执行者记忆中。

### T1202 业务目标

用户的问题必须经过真实知识库数据、两路 retrieval、受限 context 与 LLM adapter，最终返回非空 answer 和可审计 sources；无匹配、空库、history、非法 top_k 和 provider failure 又必须各自走不同的公共响应。T1202 把 Phase 6–8 的分层实现组合为一次可重复查询证据。[PROJECT FACT]

### T1202 技术目标

- 用真实 collection/upload/query endpoints 建立 `upload → Chroma → retrieve → QA → response` 路径；
- 用真实 KeywordRetriever、VectorRetriever 与 HybridRetriever 检查 score ownership、`chunk_id` 去重、filter-before-top-k；
- 检查 `MAX_CONTEXT_CHARS=4000` 下 3800 字符完整 context 与 overflow `break`；
- 检查 sources 的四字段 shape、chunk-level identity、descending order 与 backend ownership；
- 区分 empty collection 与 non-empty/no-match，并证明前者跳过 retrieval/LLM、后者继续调用 LLM；
- 检查 20-message suffix history、single-turn、system-first prompt structure 与 no-inline-citation policy；
- 运行 timeout→retry success 与三次耗尽→502 两条 DeepSeekClient control-flow paths；
- 让 deterministic vectors/answers 精确暴露替代边界，而不把它们写成真实模型质量证据。

### T1203 业务目标

用户上传文件后，应能在所属知识库中看到准确 metadata、预览真正入库的文本、不可逆地删除全部关联状态，并在删除后重新上传同名文件；另一个知识库中的同名文件不能被看到或误删。危险 filename 必须在任何写入前被拒绝。T1203 把这组 file lifecycle 与 isolation/security 承诺变成可重复的跨 feature 证据。[PROJECT FACT]

### T1203 技术目标

- 通过真实 collection/upload/files endpoints 完成 `upload → list → preview → delete → re-upload`；
- 用 raw filesystem、public Chroma reads/search 与 keyword query 同时观察级联删除；
- 证明 preview 从 persisted chunks 按 `chunk_index` 重建，即使 raw file 已被修改也不重新解析；
- 证明长 preview 在 5000 字符截断，同时 `total_chars` 保留截断前长度；
- 对 parent、Windows-parent 与 nested filename 分别验证 400 `INVALID_FILE_NAME` 和零 raw/chunk delta；
- 用 KB-A/KB-B 同名文件证明 list、preview、delete 与 re-upload 都受 collection boundary 约束；
- 静态核对 `FileManager` 与 API client 使用 `file_id + collection_name`，但不把 source matching 写成 browser interaction evidence。

### T1204 业务目标

所有功能“分别看起来能工作”仍不能回答产品是否兑现完整冻结SPEC。T1204需要建立封闭清单：Section 5与12的每个mandatory AC都必须有PASS evidence，DOD-01～06必须单独确认，发现偏差只能修bug、不能改AC或扩feature。[PROJECT FACT]

### T1204 技术目标

- 分别统计65个Section 5 occurrences、39个Section 12 occurrences，并去重为85个AC IDs；
- 将85个ID按F001–F017、QA、FE与SEC area映射到已有probes/build/browser证据；
- 对generated OpenAPI method/path表面与Section 9 error status catalog做exact equality；
- 用真实FastAPI/Chroma/filesystem补齐F001 create/list/validation/rename/delete与rename-failure compensation；
- 逐字建立AC-F008-02的`file_a=5`、`file_b=3` fixture，验证删除5且保留3；
- 用Next.js + Uvicorn browser path检查四面板导航、QA Markdown/sources、KB切换history reset、409/500/network errors与51 MiB preflight；
- 把live-provider和deployment acceptance边界写进报告，避免100% AC被误读为所有外部依赖都已实测。

### 明确不做

- 不修改 application behavior；T1201 是 verification task，发现 bug 才允许在明确 bug-fix scope 内修复。[PROJECT FACT]
- broad matrices仍不在每个场景重复运行真实BGE；真实本地模型由独立离线脚本验证。T1201不调用真实Qwen-VL，T1202不调用真实DeepSeek transport；本轮未授权任何provider live call。[PROJECT FACT]
- 不证明 model semantic quality、OCR accuracy、external provider availability、network retry timing 或 production throughput。
- T1201–T1203 backend probes不启动Uvicorn/TCP/CORS；T1204 browser evidence另行经过Next.js与Uvicorn，但不覆盖所有页面操作、浏览器矩阵或production deployment。
- 独立REAL probe只证明受控中文同义查询的基础排序，不证明大规模bge ranking benchmark；真实DeepSeek grounding/指代消解/prompt-injection robustness、provider SDK compatibility、latency、cost或availability仍未验证。
- T1204 browser matrix不执行FileManager preview/delete、KB CRUD modal、upload happy/warning flows、error-boundary render-crash injection或完整accessibility audit。
- 不制造磁盘删除成功后 Chroma 删除失败等 mid-cascade fault；T1203 证明 happy cascade 与 preflight 失败零副作用，不证明跨存储 transaction 或补偿已经存在。
- 不把T1204 focused inventory/probe PASS写成T1204或Phase Gate PASS；当前T1204为BLOCKED，Phase Learning Review与Engineering Review仍需各自独立执行。

### SPEC / Task 引用

- [TASKS T1201](../TASKS.md#t1201--ingestion-pipeline-e2e-verification)
- [F002 File Upload](../SPEC.md#f002-file-upload) 到 F008 Vector Storage
- [Section 12.2 File Upload](../SPEC.md#122-file-upload-f002)
- [Section 12.3 Document Parsing & PDF Processing](../SPEC.md#123-document-parsing--pdf-processing-f003--f004)
- [DOD-02 Acceptance Criteria pass](../SPEC.md#131-required-mandatory)
- [TASKS T1202](../TASKS.md#t1202--retrieval--qa-pipeline-e2e-verification)
- [F009 Keyword Retrieval](../SPEC.md#f009-keyword-retrieval) 到 [F015 Source Citation](../SPEC.md#f015-source-citation)
- [Section 12.4 QA & Retrieval](../SPEC.md#124-qa--retrieval-f009-f013)
- [TASKS T1203](../TASKS.md#t1203--file-management--security-cross-feature-verification)
- [F016 File Management](../SPEC.md#f016-file-management)
- [Section 10.2 File Upload Security](../SPEC.md#102-file-upload-security)
- [Section 12.6 File Management](../SPEC.md#126-file-management-f016)
- [Section 12.7 Security](../SPEC.md#127-security--invalid_file_name-f002--section-102)
- [TASKS T1204](../TASKS.md#t1204--full-spec-acceptance-criteria-audit)
- [T1204 SPEC Acceptance Audit](../T1204-SPEC-ACCEPTANCE-AUDIT.md)
- [Section 6 API Specification](../SPEC.md#6-api-specification)
- [Section 9 Error Handling](../SPEC.md#9-error-handling)
- [Section 15 Spec Coverage Matrix](../SPEC.md#15-spec-coverage-matrix)

---

## 3. 项目位置：三条 execution overlays + 一层 final audit

T1201 不位于产品 request path 的某一层；它从仓库外侧观察整条 path：

```text
Verification harness
  ├─ creates isolated storage + runtime fixtures
  ├─ calls real FastAPI TestClient
  │    → Phase 5 upload validation / endpoint
  │    → Phase 3 parse / OCR / clean / chunk / ingest
  │    → Phase 2/3 embedding service boundary
  │    → Phase 1 ChromaVectorStore
  │    → Phase 6 keyword invalidation/rebuild
  └─ observes HTTP + filesystem + public storage/search behavior

T1202 query harness
  ├─ uploads known text through the real ingestion route
  ├─ reads persisted chunks through real Keyword/Vector retrievers
  ├─ merges by chunk_id → fixed fusion → filter → Top-K
  ├─ builds bounded context + validated history
  ├─ calls real DeepSeekClient orchestration → substituted transport
  └─ observes QueryResponse, sources, retries and public errors

T1203 file-lifecycle harness
  ├─ submits safe and traversal multipart filenames
  ├─ uploads same display name into two real KBs
  ├─ lists metadata and reconstructs preview from persisted chunks
  ├─ deletes KB-A raw file + Chroma data + keyword visibility
  ├─ re-uploads same name with a new file_id
  └─ observes isolation, stale-state absence and temp cleanup

T1204 final audit overlay
  ├─ parses frozen Section 5/12 AC inventory
  ├─ checks OpenAPI routes + error catalog
  ├─ executes F001 lifecycle + compensation and literal F008 deletion
  ├─ composes T0503/T1201/T1202/T1203/build/runtime/browser evidence
  └─ guards 65/39/85 inventory counts; provider-dependent ACs remain failed
```

| 关系 | T1201 消费的能力 |
|---|---|
| 上游配置/错误 | env-backed settings、`AppError`→HTTP envelope、TestClient app wiring |
| 上游数据入口 | collection creation + multipart `/api/upload` |
| 上游 transformations | real parsers、cleaner、splitters、Embedding adapter、metadata construction |
| 上游 persistence/cache | real temporary filesystem、real ChromaDB、real KeywordRetriever invalidation/rebuild |
| 当前产物 | broad probes：T1201 81/81、T1202 46/46、T1203 43/43、T1204 29/29；REAL BGE 4/4；[remediation report](../T1204-SPEC-ACCEPTANCE-AUDIT.md)明确DashScope/DeepSeek仍FAIL/NOT_AVAILABLE |
| 相邻/下游 | T1203 为 DONE；T1201/T1202/T1204 因真实 provider 验收未完成而为 BLOCKED；Phase 12 Gate 当前为 FAIL / FIX_REQUIRED，Phase Learning Review 与 Phase 12 Engineering Review 仍未执行 |

一个关键理解是：**verification artifact 新增的是证据能力，不是用户功能**。本次application改动仅在Embedding边界显式守卫已批准的512维合同，没有新增产品功能；`TASKS.md`当前记录T1201/T1202/T1204为BLOCKED、T1203为DONE。[PROJECT FACT]

T1202 broad matrix关闭了Phase 7/8 deferred的upload/Chroma与QA composition；本次remediation再以独立REAL probe关闭固定BGE revision的加载、维度、norm、singleton与受控semantic ranking。DeepSeek provider与完整browser lifecycle仍未关闭。[PROJECT FACT]

T1203 关闭的是 Phase 9 曾明确 deferred 的“真实 upload→list/preview/delete/re-upload、path traversal matrix 与跨 KB isolation 尚未贯通”边界；它没有关闭 mid-cascade failure compensation、symlink/absolute/encoded filename 扩展矩阵或 browser behavior 边界。[PROJECT FACT]

T1204补齐的是完整AC inventory、F001 endpoint lifecycle/rename compensation、F008字面5/3 fixture、API/error surface与一组frontend runtime evidence。本次remediation另补REAL BGE evidence；live Qwen-VL/DeepSeek、复杂真实corpus、deployment credentials与Phase governance gate仍未完成。[PROJECT FACT]

---

## 4. Task 学习：怎样把 AC 变成隔离场景矩阵

### 4.1 T1201 — Ingestion Pipeline E2E Verification

#### A. Code Understanding

脚本有两层控制流：

1. `main()` 创建 system temp root，并启动同一脚本的 child mode；
2. `run_probe()` 在 child 中先设置 `UPLOAD_DIR` / `CHROMA_PERSIST_DIR` / key，再 import application；
3. 构造 deterministic Embedding/OCR boundaries；
4. 通过真实 TestClient 创建 KB、上传 runtime fixtures；
5. 用统一 `check(label, condition, detail)` 收集结果；
6. 输出 `passed/total`，任一 required check false 则 exit 1；
7. child 退出释放 Chroma handles，parent 重试清理 temp tree；残留目录会让最终 exit 1。

`run_probe()` 的场景不是按模块文件排列，而是按业务问题分组：[PROJECT FACT]

| 场景组 | 主要问题 | 代表证据 |
|---|---|---|
| Embedding + isolation | model singleton、512-dim normalized shape、temp guard | F007 + harness safety |
| Text + cleaning | UTF-8/GBK、CSV/JSON/LOG plain text、cleaned-empty | F003/F005 |
| Markdown + recursive chunking | header path、800 max、120 overlap、short text | F006 |
| Office formats | DOCX paragraph/table、XLSX multi-sheet、四种 Excel extension | F003 |
| PDF matrix | native、all-scan、mixed、partial warning、all failed | F002/F003/F004 |
| Validation + index | 400/409/413、cross-KB duplicate scope、cache rebuild | F002 + keyword seam |
| Vector persistence | 10 chunks、UUIDs、9 metadata fields、top-3 search、delete isolation | F008 |

#### B. Project Understanding

此前证据主要分散在 parser/unit、upload contract 和 rollback scripts。T1201 的新增价值是让同一份 fixture 从 HTTP boundary 穿到 Chroma，再从 file list/search/read APIs 返回；它验证的不是某个 helper 单独输出正确，而是多个已实现 contract 能否组合。[PROJECT FACT]

它也修正了“真实”这个词的使用方式：

| Boundary | 本轮 fidelity |
|---|---|
| FastAPI app/router/error handler | REAL，进程内 TestClient |
| multipart request + validation + raw file | REAL，隔离 temp filesystem |
| parsing/cleaning/chunking/metadata | REAL |
| ChromaDB persistence/search/delete | REAL，temp persistent client |
| keyword index invalidate/rebuild | REAL，child-process memory |
| SentenceTransformer adapter/lazy singleton | REAL code；model construction/data 为 deterministic SUBSTITUTE |
| PDF page detection/render/Base64/retry/warning | REAL code；DashScope network response 为 deterministic SUBSTITUTE |
| browser/Uvicorn/TCP/provider/model quality | NOT EXECUTED |

#### C. Learning Understanding

##### 4.1.1 “Substituted E2E”不是自相矛盾

E2E 可以描述**被测业务 path 的起点与终点**，而 mock/substitute 描述**某个 dependency boundary 的 fidelity**。两者必须同时标注。[ENGINEERING KNOWLEDGE]

本例从 `/api/upload` 到真实 ChromaDB 和 file-list/search observable output，路径是端到端的；但模型权重与外部 OCR response 没有真实运行，所以不能说 all-real、live-provider 或 production E2E。[PROJECT FACT]

##### 4.1.2 Test double 的价值取决于替代位置

T1201 没有 patch `IngestService.process()` 返回一个成功 dict，因为那会跳过几乎整个验收对象。它只在最外缘替代：

- `SentenceTransformer` constructor/encode implementation；
- `MultiModalConversation.call` 的 network response。

因此 parser dispatch、OCR page selection、image rendering、Base64 message assembly、retry count、warning collection、clean/chunk、metadata、Chroma write 与 API mapping 仍然运行。[PROJECT FACT]

##### 4.1.3 AC ID 需要带 section context

冻结 SPEC 的 Feature-level F003 与 Section 12.3 都使用 `AC-F003-01/02/03`，但个别编号含义不同：例如 Feature F003 的 `AC-F003-03` 是 mixed PDF，Section 12.3 的 `AC-F003-03` 是 DOCX table。脚本用 `AC-F003-02 / AC-F004-02 mixed PDF`、`AC-F003-03/04 DOCX` 这样的 composite label 同时提示两层映射。[PROJECT FACT]

这说明 traceability 不能只写裸 ID；教材和最终 audit 应写 `Section 5 F003 AC-F003-03` 或 `Section 12.3 AC-F003-03`。[ENGINEERING KNOWLEDGE]

#### 验证结果与 AC coverage

本 Learning Pass 于 2026-09-07 重新执行主脚本，结果为 `Required checks: 81/81 passed`、`RESULT: PASS`、exit code 0；输出中的 temp root 在 parent cleanup 后不存在。[PROJECT FACT]

| Contract group | 当前 T1201 runtime evidence | 边界 |
|---|---|---|
| F002 AC-01～10 | normal upload、duplicate/cross-KB、51 MB/.exe/empty、warning、FAILED、rollback/retry、warning duplicate均执行通过 | real route/filesystem/Chroma；OCR provider substituted |
| Feature F003 AC-01～05 | UTF-8、GBK、mixed PDF、DOCX table、XLSX sheets均执行通过 | parsers real；mixed OCR response substituted |
| Section 12.3 AC-01～03 | GBK full upload、mixed PDF、DOCX table均执行通过 | 同上；必须带 section 解释编号 |
| F004 AC-01～05 | scan success、mixed、partial warning、all failed、warning exposure均执行通过 | page/render/retry/warning real；provider call substituted |
| F005 AC-01～02 | whitespace cleaning与 cleaned-empty rejection/cleanup执行通过 | real |
| F006 AC-01～03 | Markdown path、2000-char recursive split 800/120、300-char single chunk执行通过 | real splitter |
| F007 AC-01～02 | broad matrix以3×512 double验证adapter；独立脚本以真实模型验证512维、L2 norm、configured path与singleton | REAL BGE 4/4 PASS；broad branch matrix仍为SUBSTITUTED |
| F008 AC-01 | 10 chunks→top-3 search、UUID identity、score range、9 metadata fields执行通过 | real Chroma |
| F008 AC-02 | delete one 10-chunk file并保留另一 1-chunk file执行通过 | 证明行为；未逐字复现 SPEC Given 的 5/3 数量 |
| F008 AC-03 | AST 扫描 application code，未发现 VectorStore 外 `_client/_collection` access | static check inside runtime matrix |

额外回归：标准库 `unittest` 在当前 checkout 执行 78 tests，全部 PASS；其中模拟 keyword invalidation outage 的 traceback 是被测日志行为，最终仍为 `OK`。`pytest` 没有安装，`python -m pytest tests -q` 因 `No module named pytest` 未启动任何测试；不能把这次命令写成 test failure，也不能写成 pytest PASS。[PROJECT FACT]

#### Interview Candidates（Task-level only）

> 这些只是 candidates；Phase 12 尚未完成，不晋升到项目级 Interview Guide。

- **Technical Points**：child process + env-before-import isolation；runtime binary fixtures；two-boundary substitution；public observable rollback proof。
- **Engineering Questions**：一个带 substitutions 的验证为什么仍可称 E2E？怎样选择替代边界才不会把被测对象 mock 掉？
- **Candidate Interview Questions**：为什么 422 不足以证明 rollback？为什么不能只看 81/81 就宣称所有依赖都真实？
- **STAR Candidate**：无。本 Task 没有 production incident，也没有发现→修复的重大闭环，不构造 STAR。

### 4.2 T1202 — Retrieval + QA Pipeline E2E Verification

#### A. Code Understanding

[verify_t1202_retrieval_qa.py](../../backend/scripts/verify_t1202_retrieval_qa.py) 延续 parent/child 隔离模式，但验证对象从写入侧改为查询侧：[PROJECT FACT]

1. parent 创建 `t1202_retrieval_qa_*` system temp root，启动 child，结束后验证删除；
2. child 在 application import 前设置 upload/chroma/key 环境变量；
3. 通过真实 collection 与 upload endpoints 写入四份已知文本；
4. 对真实 Keyword/Vector/Hybrid classes 做一次组合检索，再用 static retrievers 精确复现 F011 数值 Given；
5. 直接调用真实 `assemble_context()` / `assemble_sources()` 检查 3800/4000 边界和 source projection；
6. patch `qa_mod.OpenAI` 为 recording transport 后，通过真实 `/api/query` 执行 QAService、prompt、retry、history 与 sources；
7. 聚合 46 个 required observations；任一 false、child crash、timeout 或 cleanup failure 都返回非零 exit code。

脚本的场景矩阵按“组合问题”而不是源文件排列：

| 场景组 | 真实执行部分 | 主要证明 |
|---|---|---|
| Setup + seed | collection/upload route、text ingest、temp Chroma | 查询确实消费本轮持久化数据，不是预置 Mock rows |
| Real retrieval | keyword/vector/hybrid + Chroma search | exact hit、semantic-only hit、score rename/fusion、real ranking |
| Literal F011 | real Hybrid + static branch inputs | 0.87、0.18 filter、20→5、same `chunk_id` collapse |
| Assembly | real converters + synthetic ranked dicts | 3800 exact fit、overflow stop、四字段 sources |
| Query happy/no-match | real route/service/prompt/source flow | HTTP 200、answer/sources、empty-context placeholder |
| Empty/validation | real empty Chroma + API validation | 409 before retrieval/LLM；非法 top_k 为 400 |
| History/security | real formatter/message builder + transport double | recent 20、single turn、system-first、retrieved instruction位置 |
| Retry | real DeepSeekClient retry/error mapping + queued outcomes | 1 次失败后成功；3 次耗尽为 502 |

#### B. Project Understanding

Phase 6–8 已分别拥有 keyword、vector/hybrid、context/history、DeepSeek adapter、QAService 与 query route；此前测试主要在各自的 Mocked/unit boundary。T1202 的新增价值是把真实上传产生的 chunks 交给真实 Chroma 与真实 retrieval classes，再经真实 query route 返回 public response，因而验证的是**已有模块的 composition**。[PROJECT FACT]

| Boundary | T1202 fidelity |
|---|---|
| FastAPI collection/upload/query + AppError mapping | REAL，进程内 TestClient |
| text parsing/clean/chunk + temp filesystem | REAL |
| embedding wrapper/lazy singleton | REAL code；model/semantic features 为 SUBSTITUTE |
| Chroma persistence/search/count | REAL，system temp persistent store |
| Keyword/Vector/Hybrid retrieval | REAL implementation |
| context/history/QAService/source assembly | REAL implementation |
| DeepSeekClient message/config/retry/response extraction | REAL implementation |
| OpenAI constructor/DeepSeek transport与 answer semantics | deterministic RECORDING SUBSTITUTE |
| Uvicorn/TCP/browser/frontend history lifecycle | NOT EXECUTED |

#### C. Learning Understanding

##### 4.2.1 一个 AC 可以需要两种 fixture

真实 corpus path 擅长证明“模块真的接上了”：uploaded chunk 能经 Chroma 被两路 retriever 找到，真实融合分数也满足公式。但浮点 similarity 会随 model/corpus 改变，不适合精确制造 `0.8` 与 `0.9`。[ENGINEERING KNOWLEDGE]

所以 T1202 同时使用 static branch rows 精确复现 F011 Given：`0.8×0.3 + 0.9×0.7 = 0.87`。这不是退回纯 Mocked E2E，而是把两个问题分开：real path 证明 wiring，controlled inputs 证明公式与边界。[PROJECT FACT]

##### 4.2.2 空库与无匹配不能共用一个“空”分支

- **Empty collection**：storage count 为 0，`QAService.answer()` 在 retrieval 和 LLM 之前抛 `COLLECTION_EMPTY`，API 映射为 409。
- **No relevant chunks**：collection 非空，但 hybrid filter 返回 `[]`；context 变为 `""`，DeepSeek user message写入“知识库中暂无相关文档”，LLM仍被调用，response为 200与 `sources=[]`。

这两个状态的区别是业务语义而不是实现细节：前者是资源没有可查询数据，后者是合法查询但证据不足。[PROJECT FACT]

##### 4.2.3 Answer 与 sources 的 authority 不同

`answer` 来自模型边界，可能受模型随机性与指令遵循影响；`sources` 由 backend 从同一批 ranked retrieval results 投影，不从 answer 解析，也不相信模型生成的引用。[PROJECT FACT]

因此 T1202 对 F015 的证据强于对真实 F013 semantics 的证据：它能真实证明 source IDs、字段与排序来自 persisted chunks；但 history 指代消解、无信息措辞与 injection response 由 deterministic transport double 产生，只证明 prompt/data plumbing 和预期 contract，不证明 live DeepSeek behavior。[PROJECT FACT]

##### 4.2.4 分数链只允许一次语义转换

```text
Chroma distance
  → VectorStore: similarity_score
  → VectorRetriever: vector_score（仅改名）
  → HybridRetriever: final_score = keyword*0.3 + vector*0.7
  → SourceObject: relevance_score（仅公开字段改名）
```

T1202 把真实 `VectorStore.search()` 结果按 `chunk_id` 对照 VectorRetriever，证明中间没有二次 min-max；又把 Hybrid 输出与 API sources 对照，证明 public score 没被重新计算。[PROJECT FACT]

#### 验证结果与 AC coverage

本 Learning Pass 于 2026-09-07 重新执行 T1202 脚本：`Required checks: 46/46 passed`、`RESULT: PASS`、exit code 0；parent 输出中的 temp root 随后 `Test-Path=False`。[PROJECT FACT]

| Contract group | 当前证据 | 不能升级成什么 |
|---|---|---|
| F009 | T1202 real keyword exact-hit；当前 focused suite 覆盖 bigram/no-match/partial/mixed/invalidation；T1201 另有 real invalidation path | 不等于 BM25、增量 index 或生产 corpus recall |
| F010 | broad matrix以deterministic feature model验证wiring；独立REAL BGE + Chroma将受控中文同义目标排第一 | 基础REAL排序已证明；不等于大规模recall/quality benchmark |
| F011 AC-01～04 | real fusion/dedupe + controlled literal 0.87/0.18/20→5/duplicate scenarios | static branch rows只证明 Hybrid contract，不是 full real-corpus ranking |
| F012 AC-01～02 / QA-07 | real assembly function；3800 exact fit、overflow stop；no-match经 API继续调用LLM | 不证明 token budget、summarization或任意超长 prompt behavior |
| F013 AC-01～04 | real System Prompt/message/config/retry/error mapping；transport double返回可控答案/异常 | 不证明 live DeepSeek grounding、language adherence、安全性或 provider compatibility |
| F014 AC-01～03 | real API→history formatter→prompt；20-message window与 no-history | pronoun answer由double产生；browser侧 KB切换/history state未执行 |
| F015 AC-01～02 | real backend source assembly与 API response对应 persisted chunk IDs | 不证明前端如何展示 sources |
| AC-QA-01～07 | 七组 cross-feature behaviors均在 matrix 中有对应 runtime observation | fidelity随上表边界变化，不是七组 all-real provider evidence |

本轮还执行 `python -m unittest tests.test_qa tests.test_query -v`，60/60 PASS；执行完整 `python -m unittest discover -s tests -v`，78/78 PASS。前者补足 F009/F010/F012 与 query validation 的 focused unit/route evidence，后者证明当前 backend regression 未退化。`python -m pytest tests -q` 因未安装 pytest而未启动测试，记录为 `NOT_AVAILABLE`，不是 test failure或 PASS。[PROJECT FACT]

#### Interview Candidates（Task-level only）

> Candidate only；Phase 12 尚未完成，不晋升到项目级 Interview Guide。

- **Technical Points**：real path + literal fixture 双层证据；score ownership chain；empty collection vs empty retrieval；backend-owned sources。
- **Engineering Questions**：怎样证明 prompt结构而不夸大模型安全？为什么真实 corpus测试和controlled-score测试缺一不可？
- **Candidate Interview Questions**：`final_score` 与 `relevance_score` 的 owner分别是谁？为什么无匹配仍调用 LLM而空库不调用？
- **STAR Candidate**：无。本 Task 是预期 verification work，没有 production incident或发现→修复闭环，不构造 STAR。

---

### 4.3 T1203 — File Management & Security Cross-Feature Verification

#### A. Code Understanding

[verify_t1203_file_management_security.py](../../backend/scripts/verify_t1203_file_management_security.py) 复用 parent/child isolation shell，但把 observation window 切到文件生命周期：[PROJECT FACT]

1. parent 创建 `t1203_file_management_*` system temp root，child 在 import 前绑定 upload/chroma paths；
2. 以 deterministic 512-dim model保持文件生命周期矩阵可重复，真实 upload ingestion 仍生成 persisted chunks；真实BGE另有独立REAL证据；
3. 创建 KB-A 与 KB-B，用真实 multipart request 分别提交三种 traversal filename 和 clean PDF control；
4. 上传 preview、long-preview 与两个 KB 的同名 delete fixtures，再核对六字段 file projection；
5. 修改 raw preview 文件，并阻断 parser/OCR/embedding/LLM calls，证明 preview 只消费 persisted chunks；
6. 先建立 keyword index，再删除 KB-A 文件，同时观察 filesystem、Chroma、vector search、file projection 与 cache dirty/rebuild；
7. 重新上传同名文件，要求新 `file_id`、旧 identities 消失、新 keyword results 可见；
8. 静态读取前端源码，确认 preview/delete 都传递 `file_id + collection_name`；
9. 聚合 43 个 required observations；任一 false、child crash、timeout 或 cleanup residual 都返回非零 exit code。

| 场景组 | 真实执行部分 | 主要证明 |
|---|---|---|
| Filename security | multipart parser、upload route、validation、state snapshots | 三种 SPEC filename 均 400 `INVALID_FILE_NAME`，且 raw/chunks 零变化 |
| Clean control | generated PDF、real parser/ingest/Chroma | 合法 filename 不是被安全规则误杀，而是完成正常 upload |
| List + isolation | 两个 collection、同名 raw files、Chroma projection | metadata shape/值正确；KB-A/B identities 不泄漏 |
| Preview | real persisted chunks、real endpoint | index order、`\n\n` 拼接、5000 截断、404 taxonomy、无重解析 |
| Cascade delete | raw unlink、Chroma delete/search、keyword cache | 三类存储状态清理，另一个 KB 不受影响 |
| Re-upload | same-name real upload + cache rebuild | 新 UUID、新 chunks 可见，旧 file/chunk identity 不复活 |
| Frontend wiring | source text matching | 组件与 client 代码包含正确参数；不等于 UI runtime |

#### B. Project Understanding

Phase 5 已实现 upload security，Phase 9 已实现 list/preview/delete，Phase 11 已实现 FileManager；此前最强 Phase 9 证据仍是 Mocked route tests 与一条绕过 ingestion 的 concrete smoke。T1203 的新增价值，是让文件从真实上传产生 `file_id/chunks/raw file`，再让同一 identity 经读路径、删除路径和重传路径完成生命周期闭环。[PROJECT FACT]

| Boundary | T1203 fidelity |
|---|---|
| FastAPI collection/upload/files routes + error handlers | REAL，进程内 TestClient |
| multipart filename transport + upload preflight | REAL |
| PDF/TXT parse、clean、chunk、metadata、ingestion | REAL |
| filesystem raw files + unlink | REAL，system temp tree |
| Chroma persistence/list/read/delete/vector search | REAL，temp persistent client |
| keyword index build/invalidate/rebuild | REAL，child-process memory |
| embedding service/lazy singleton | REAL code；SentenceTransformer construction/vector semantics 为 deterministic SUBSTITUTE |
| preview 的 parser/OCR/embed/LLM“不调用” | REAL endpoint；这些调用被 fail-fast probes 监视 |
| FileManager/API client integration | STATIC SOURCE ASSERTION |
| Uvicorn/TCP/CORS/browser clicks/render/refresh | NOT EXECUTED |

#### C. Learning Understanding

##### 4.3.1 安全 AC 是“拒绝结果 + 零副作用”二元契约

只验证 `400 INVALID_FILE_NAME` 仍可能漏掉危险实现：endpoint 可能先创建目录或写文件，再发现非法名称并返回 400。T1203 在每次拒绝前保存完整 raw-file snapshot 与两个 collection 的 chunk IDs，拒绝后要求两者完全相等，并额外确认 escaped/nested `doc.pdf` 不存在。[PROJECT FACT]

```text
unsafe multipart filename
  → validate_file_name()                    [REAL]
  → 400 INVALID_FILE_NAME                   [observable result]
  → filesystem snapshot unchanged          [no raw side effect]
  → Chroma chunk-id snapshot unchanged      [no persisted side effect]
```

这比“测试 helper 抛 AppError”更强，因为它从真实 HTTP boundary 证明 validation precedence；但覆盖仍只限 SPEC 点名的 `../`、`..\\` 与 `subdir/` 三种形式，不自动等价于绝对路径、URL-encoded payload、Unicode separator、symlink 或所有平台差异的完整安全审计。[ENGINEERING KNOWLEDGE]

##### 4.3.2 Preview 的 source of truth 可以用“制造分歧”证明

如果 raw file 与 persisted chunks 内容相同，preview 返回正确内容仍无法判断它读的是哪一个。脚本先从 Chroma 计算期望拼接文本，再把 raw file 改成 `RAW FILE MUTATED AFTER INGESTION`；随后让 ingestion、各 parser、OCR、embedding 与 LLM 一旦被调用就抛异常。Preview 仍返回原 persisted content，且所有 probes 的 call count 为 0，于是 source-of-truth 与 negative-call contract 同时被证明。[PROJECT FACT]

##### 4.3.3 删除不是“HTTP 200”，而是状态向量变化

删除前，脚本记录 file 的 chunk IDs、raw bytes、file projection 与 keyword hit；删除后同时要求：[PROJECT FACT]

- raw path 不存在；
- `get_chunks_by_file()` 为空，`list_chunks()` 与 vector search 都没有旧 chunk IDs；
- `get_files()` 不再投影旧 `file_id`；
- keyword collection 先进入 dirty set，下一次搜索 rebuild 后旧 unique token 无结果；
- KB-B 的同名 raw file、chunks、preview 与 list 均保持不变。

这些观察证明 success path 的级联完成，不证明三类存储具有 transaction。当前 route 顺序仍是 disk → Chroma → keyword invalidation；若第二步抛错，第一步不会自动回滚。T1203 未注入这种 mid-cascade fault，因此 Phase 9 的 partial-failure risk 仍然成立。[ENGINEERING KNOWLEDGE]

##### 4.3.4 Re-upload 用新 identity 证明“没有幽灵状态”

删除后仅允许“同名上传返回 200”还不够：若旧 metadata 或 cache 未清理，系统可能同时保留两个逻辑文件。T1203 要求 re-upload 获得合法且不同的新 UUID、同名 file projection 恰好一条、旧 file ID 查不到 chunks、新 file ID 有 chunks、keyword search 只返回新 identity。[PROJECT FACT]

##### 4.3.5 Source assertion 是 wiring smoke，不是 frontend E2E

脚本用字符串检查确认 `FileManager` 调用 `previewFile(file.file_id, resolvedCollection)` / `deleteFile(file.file_id, collectionName)`，并确认 API client 对 file/collection 参数做 URL encoding。这能快速捕获明显的 identity 接线漂移，却不会执行 TypeScript、React state、modal、refresh、network transport 或 accessibility behavior；重构等价代码也可能让字符串检查产生假阴性。[ENGINEERING KNOWLEDGE]

#### 验证结果与 AC coverage

本 Learning Pass 于 2026-09-07 重新执行 T1203 脚本：`Required checks: 43/43 passed`、`RESULT: PASS`、exit code 0；运行目录 `t1203_file_management_hdmal4ki` 随后 `Test-Path=False`。[PROJECT FACT]

| Contract group | 当前 T1203 runtime evidence | 不能升级成什么 |
|---|---|---|
| AC-F016-04 | real uploaded persisted chunks、乱序防御、raw mutation、8 个 forbidden-call probes | 不等于原始文档精确渲染或 de-overlap |
| AC-F016-05 | 8409 字符完整拼接被截到 5000，两个长度字段分别核对 | 不证明 streaming/pagination 或超大文件 memory profile |
| AC-F016-06/07 | missing collection 与 missing/cross-KB file ID 返回不同 404 code | 不等于认证/授权；v1 仍是可信内网、无 auth |
| AC-F016-08 | real raw + Chroma chunks/vectors/metadata + keyword dirty/rebuild 全部观察 | fixture 被删文件有 1 chunk；不逐字复现 Feature-level AC-F016-02 的 15 chunks，也不覆盖 mid-cascade faults |
| AC-F016-09 | missing delete 为 404，filesystem/chunk snapshots 不变 | 不证明重复删除是 2xx 幂等；contract 明确要求 404 |
| AC-SEC-01 | 三个 literal filename 经真实 multipart endpoint 被拒，raw/Chroma 零 delta | 不是完整 path fuzzing、symlink 或 encoded-input audit |
| AC-SEC-02 | clean generated PDF 经正常 upload 得到 raw file、UUID 与 Chroma file projection | embedding semantics 仍由 substitute 产生 |
| Cross-KB lifecycle | 同名文件 list/preview/delete/re-upload 隔离 | collection boundary 不是 user authorization boundary |
| Frontend dependency | source-level `file_id + collection` wiring | 不是 browser/runtime acceptance |

本轮还执行 `python -m unittest tests.test_files tests.test_upload -v`，18/18 PASS；执行完整 `python -m unittest discover -s tests -v`，78/78 PASS。Focused suite 提供 Mocked route error/order 与 upload contract 的细粒度证据，matrix 提供真实 storage composition，二者互补。`python -m pytest tests -q` 因未安装 pytest 而未启动，记录为 `NOT_AVAILABLE`，不是 test failure 或 PASS。[PROJECT FACT]

#### Interview Candidates（Task-level only）

> Candidate only；Phase 12 尚未完成，不晋升到项目级 Interview Guide。

- **Technical Points**：安全 AC 的 no-side-effect proof；persisted chunks 作为 preview source of truth；cascade state vector；new identity after re-upload。
- **Engineering Questions**：如何用制造 raw/persisted 分歧证明 read source？为什么 success cascade evidence 不能推出 failure atomicity？
- **Candidate Interview Questions**：怎样证明跨 KB 同名文件未被误删？为什么 source string assertion 不是 frontend E2E？
- **STAR Candidate**：无。本 Task 是预期 verification work，没有 production incident 或发现→修复闭环，不构造 STAR。

---

### 4.4 T1204 — Full SPEC Acceptance Criteria Audit

#### A. Code Understanding

T1204有三个不同职责的artifact，阅读时不能混为一体：[PROJECT FACT]

1. [T1204 audit report](../T1204-SPEC-ACCEPTANCE-AUDIT.md) 是最终evidence ledger：定义104 occurrences / 85 unique IDs口径，逐area列primary evidence，确认DOD-01～06与deviation disposition；
2. [verify_t1204_spec_acceptance.py](../../backend/scripts/verify_t1204_spec_acceptance.py) 是662行可执行probe：自动守卫计数、OpenAPI/error catalog、literal F008-02与完整F001 lifecycle；
3. [serve_t1204_browser_backend.py](../../backend/scripts/serve_t1204_browser_backend.py) 是143行本地服务harness：seed两个KB和一份文本，替代embedding/DeepSeek后启动真实Uvicorn，供Next.js browser interaction使用。它本身不含浏览器assertions。

主probe延续前三个Task的parent/child隔离模式，但覆盖面更集中：

```text
parent main()
  → mkdtemp(t1204_spec_audit_*)
  → child --probe-root
      → env-before-import + deterministic 512-dim model
      → parse SPEC Section 5 / 12 / 13 inventories
      → GET /openapi.json and compare exact route/method dict
      → compare runtime error catalog with expected status dict
      → create literal 5/3 VectorStore fixture
      → F001 create/list/validation/rename/fault/delete matrix
      → aggregate 29 checks
  → child exit → remove temp root → propagate exit code
```

这里最重要的阅读纪律是：**probe没有执行T0503/T1201/T1202/T1203，也没有把85个ID逐条绑定到29个assertions。** 报告的全量结论是一个组合证据判断；probe负责冻结关键inventory与关闭剩余runtime gap。把`29/29`写成“29条AC”或“全量AC全部由本脚本自动验证”都不准确。[PROJECT FACT]

#### B. Project Understanding

##### 4.4.1 两个source-of-truth为什么产生104与85两个正确数字

SPEC明确说Section 5是Feature-level AC、Section 12是Cross-feature/E2E AC，两者都mandatory且不可互相替代。当前Section 5有65次、Section 12有39次；19个ID在两个section重叠，因此：[PROJECT FACT]

```text
mandatory occurrences = 65 + 39 = 104
unique mandatory IDs  = 65 + 39 - 19 = 85
```

`104`回答“两个section中共有多少次mandatory AC出现”；`85`回答“去重后有多少逻辑ID”。旧Learning Pass曾把报告matrix与SPEC做exact-set comparison并得到85个ID，但这只证明清单身份一致；Gate已确认它不能把substituted provider behavior升级为85/85 runtime PASS。[PROJECT FACT]

这项额外检查也暴露了自动化边界：T1204脚本只断言三个count，没有断言exact ID set，更没有对Given/When/Then文本做hash。若未来删掉一个ID又补入另一个ID使计数不变，count-only guard可以继续PASS；因此报告中的“不能静默漂移”应理解为**对数量缩减敏感**，不是完整semantic drift detector。[ENGINEERING KNOWLEDGE]

##### 4.4.2 API/error audit验证的是“运行表面等于冻结oracle”

probe通过真实`TestClient`读取generated OpenAPI，并与8条path、11个method的expected dict做集合相等；多route、少route或method错位都会失败。错误目录把warning-only的`OCR_PAGE_FAILED`/`PAGE_RENDER_FAILED`排除在HTTP catalog equality外，再单独检查它们存在，避免把upload warning误当独立HTTP error。[PROJECT FACT]

这里的expected route/error dict是脚本内手工固化的oracle，并非运行时解析SPEC表格。这种做法简单、独立于application，却要求SPEC变更时人工同步；T1204报告完成的是当前v1.6 checkout的一致性，不是未来永久免维护。[ENGINEERING KNOWLEDGE]

##### 4.4.3 F001 rename的完成条件是identity-preserving state transition

成功rename前，probe上传真实生成的`doc.pdf`，记录完整chunk snapshot、raw bytes、vector score与keyword hits；rename后要求：[PROJECT FACT]

- old collection/path消失，new collection/path出现；
- `chunk_id`、`file_id`、`file_name`、`chunk_index`、content和所有非级联metadata不变；
- 只有`collection_name`与`source_file`切到new name；
- 同一query vector的score dict前后完全相等，本轮fixture为`1.0 → 1.0`；
- old keyword state进入dirty set，new collection下一次search完成rebuild；
- collection/file list仍能用原file identity观察到对象。

这比“rename endpoint返回200”更接近AC-F001-04：它证明的是一次保持identity与检索语义的ownership迁移，而不是重新ingest或重新生成UUID。

##### 4.4.4 compensation必须恢复完整old observable state

probe在`VectorStore.rename_collection(old,new)`成功之后，对`_rename_uploads_dir`注入`OSError`。API route捕获失败后执行reverse-order compensation，再返回500 `RENAME_FAILED`。断言同时比较old/new collection存在性、raw bytes/path、完整metadata/content snapshot和vector scores；new-name residue必须为零。[PROJECT FACT]

这关闭的是**rename指定故障点**的原子性证据，不是所有cascade都具有transaction。KB delete仍按SPEC不可逆，T1203的file delete也没有跨filesystem/Chroma/cache补偿；不能把rename的compensation设计外推到所有delete路径。[ENGINEERING KNOWLEDGE]

##### 4.4.5 literal fixture用于关闭“同语义、不同Given”的证据差距

T1201曾用10/1 fixture证明`delete_by_file`隔离语义；T1204重新按AC-F008-02逐字构造`file_a=5`、`file_b=3`，再要求返回`deleted_count=5`、A归零、B仍为3、collection总数为3。两者产品语义相同，但literal fixture提高了审计可追溯性，不能倒写成T1201当时已经执行5/3。[PROJECT FACT]

##### 4.4.6 browser path补的是React/HTTP行为，不补provider质量

browser harness先通过真实FastAPI seed `browser-kb`、`browser-empty` 与`machine-learning.txt`，再运行Uvicorn。T1204报告记录6/6 local browser outcomes；本Learning Pass在当前checkout重新执行同六个场景：[PROJECT FACT]

| 场景 | 本轮可见结果 |
|---|---|
| SPA navigation | 四个panel heading依次出现，URL始终为`http://127.0.0.1:3000/` |
| QA Markdown + sources | `# 验收回答`、bold/list渲染；展开后显示`machine-learning.txt`与`0.300`；history为2 |
| KB switch + empty query | 切到`browser-empty`后history归0、旧answer消失；查询显示“知识库暂无文档，请先上传文件。” |
| deterministic HTTP 500 | `trigger500`显示统一“问答请求失败”、可理解说明与retry action |
| backend network failure | 真实停止本地backend并reload后显示connection error与“重新加载” |
| 51 MiB upload preflight | 显示“文件大小超过 50MB 限制。”，upload queue为0，backend file count前后均为1 |

这条路径真实包含Next.js、React state、browser fetch、HTTP/Uvicorn、FastAPI、真实retrieval/Chroma/filesystem；SentenceTransformer model与DeepSeek answer/error为deterministic substitutions。临时51 MiB fixture、backend storage tree与两个server在运行后全部清理。[PROJECT FACT]

浏览器服务harness被仓库化了，但浏览器操作/assertions只存在于审计记录与本轮执行会话，没有checked-in reusable runner。因此“6/6可人工/工具复现”成立，“已有repository-owned browser regression suite”不成立。[ENGINEERING KNOWLEDGE]

#### C. Learning Understanding

T1204最值得迁移的不是某个断言，而是四层审计模型：

1. **Inventory completeness**：先冻结应审什么，避免只挑容易通过的场景；
2. **Evidence traceability**：每个AC指向primary evidence，不能拿总check数替代映射；
3. **Fidelity declaration**：逐边界标REAL/SUBSTITUTED/NOT EXECUTED；
4. **Governance separation**：task audit PASS、Phase Gate、Learning Review、Engineering Review是不同事件。

反过来说，任何“100%通过”的结论都至少要追问四个问题：分母是什么？是否去重？由哪个可执行证据证明？哪些依赖被替代？答不清时，百分比本身没有足够信息。

#### 验证结果与 AC coverage

本Learning Pass于2026-09-07重新执行/核对：[PROJECT FACT]

- `python backend/scripts/verify_t1204_spec_acceptance.py`：29/29 PASS，exit 0，temp root清理后不存在；
- `python -m unittest discover -s tests -v`：78/78 PASS；
- `npm.cmd run build`：production compile、lint与type validation PASS；
- 对真实`upload-validation.ts`做runtime transpile/evaluation：5/5 PASS（11 extensions、50 MiB允许、51 MiB/empty/unsupported拒绝）；
- 当前SPEC inventory仍为65/39/85；旧matrix exact-set检查只保留为inventory历史，不作为provider PASS；
- Next.js + isolated Uvicorn browser：上述6/6 scenarios PASS。

| Audit layer | 当前证据 | 不能升级成什么 |
|---|---|---|
| Mandatory inventory | 65 + 39 occurrences、85 unique IDs的count guard通过 | 不等于每个Given/When/Then通过，尤其不覆盖live providers |
| F001 | real endpoint/filesystem/Chroma/cache；success identity与injected failure compensation | 不等于delete具有补偿或所有故障点都被穷举 |
| F008-02 | public interface literal 5/3 fixture | 不证明大规模delete性能 |
| API/error | generated OpenAPI与runtime catalog exact equality | expected oracle仍是手写常量，不是SPEC parser |
| Frontend | build + validator runtime + 6 browser scenarios | 不等于完整browser suite、accessibility或render-crash boundary proof |
| Providers | deterministic embedding/OCR/LLM edges | 不证明live model quality、credentials、latency、cost或availability |
| DoD | 脚本确认DOD-01～06 IDs存在 | 旧报告的全PASS声明已撤回；当前provider findings使T1204/Gate不能PASS |

#### Interview Candidates（Task-level only）

> Candidate only；Phase Gate尚未完成，不晋升到项目级Interview Guide。

- **Technical Points**：occurrence vs unique inventory；evidence ledger与executable probe的职责分离；identity-preserving rename；state-vector compensation；browser fidelity map。
- **Engineering Questions**：count guard怎样升级为semantic manifest？怎样把AC→command→assertion→fidelity变成machine-readable traceability？
- **Candidate Interview Questions**：为什么29/29不能直接证明85条AC？怎样区分task audit PASS与Phase Gate PASS？
- **STAR Candidate**：无。审计未发现需要修复的application bug，不虚构incident或补救闭环。

---

## 5. 代码理解：十三个最值得精读的 verification mechanisms

### 5.1 `main()` + env-before-import：用进程边界获得可靠隔离

核心位置：[verify_t1201_ingestion.py:45](../../backend/scripts/verify_t1201_ingestion.py#L45) 与 [verify_t1201_ingestion.py:720](../../backend/scripts/verify_t1201_ingestion.py#L720)。

```python
def main() -> int:
    probe_root = Path(tempfile.mkdtemp(prefix="t1201_ingestion_"))
    try:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--probe-root", str(probe_root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
        )
        return_code = completed.returncode
    ...
    for _ in range(10):
        shutil.rmtree(probe_root, ignore_errors=True)
        if not probe_root.exists():
            break
        time.sleep(0.3)
```

child 进入 `run_probe()` 后先做：

```python
os.environ["UPLOAD_DIR"] = str(probe_root / "uploads")
os.environ["CHROMA_PERSIST_DIR"] = str(probe_root / "chroma")
os.environ["DASHSCOPE_API_KEY"] = f"test-double-{probe_root.name}"

sys.path.insert(0, str(_BACKEND))
import app.services.embedding as embedding_mod
from app.core.config import settings
from app.main import app
```

设计意图：

1. `tempfile.mkdtemp()` 给本次运行一个独立 root；真实仓库 `backend/uploads` 和 `backend/chroma_db` 不进入目标路径。
2. `subprocess.run()` 启动全新解释器；Python module cache、Pydantic settings singleton、Embedding singleton 与 Chroma handle 都从空状态开始。
3. env 必须写在 application imports 之前。若先 import `settings` 再改 env，当前进程中的 settings object 已经读取旧值。
4. parent 等 child 退出后再删除目录，因为 Windows 下仍被当前进程持有的 Chroma/Rust file handle 可能阻止删除。
5. cleanup 自己也是验收条件；temp root 十次重试后仍存在就 exit 1。

**TypeScript 类比**：接近 Node.js 用 `child_process.spawn(process.execPath, args, {env})` 跑一个 isolated integration worker；测试不是在同一个 Jest module registry 中修改 `process.env` 后期待已 import config 自动刷新。

### 5.2 `patch.dict(sys.modules)`：替代重型 constructor，保留真实 adapter

核心位置：[verify_t1201_ingestion.py:101](../../backend/scripts/verify_t1201_ingestion.py#L101)。

```python
class DeterministicSentenceTransformer:
    def encode(self, texts, normalize_embeddings=False):
        ...
        vector = [0.0] * 512
        vector[index] = 1.0
        rows.append(vector)
        return Matrix(rows)

fake_sentence_transformers = types.ModuleType("sentence_transformers")
fake_sentence_transformers.SentenceTransformer = DeterministicSentenceTransformer
embedding_mod._model = None
with patch.dict(sys.modules, {"sentence_transformers": fake_sentence_transformers}):
    first_model = embedding_mod.get_model()
    second_model = embedding_mod.get_model()
    contract_vectors = embedding_mod.encode_chunks(["one", "two", "three"])
```

这里没有替换 `embedding_mod.get_model()` 或 `encode_chunks()`。真实函数仍负责 lazy import、singleton cache、`normalize_embeddings=True` 与 `.tolist()` conversion；fake module 只提供缺失的 model construction/encode edge。[PROJECT FACT]

`Matrix` double 专门提供 `.tolist()`，因为真实 SentenceTransformer 返回 NumPy-like matrix。每个向量只有一个值为 1，其余为 0，所以维度固定 512，L2 norm 必然是 1；文本 hash 决定非随机 index，使同内容 query 能在真实 Chroma cosine search 中命中自己。[PROJECT FACT]

一个容易漏掉的 Python 细节：`with patch.dict(...)` 结束后，`sys.modules` 恢复，但 `embedding_mod._model` 已缓存 fake instance。因此后面的全部 HTTP ingestion 仍复用这个 deterministic model；脚本既验证 singleton，又避免每个场景重新 patch。[PROJECT FACT]

OCR 的替代更窄：`patch.object(dashscope.MultiModalConversation, "call", ...)` 只替换 network response，真实 `ocr_page()` 仍完成 page render、JPEG/Base64、model/prompt assembly、retry loop 与 warning collection。这个“尽量靠近外部边缘替代”的选择保留了更多项目行为。[ENGINEERING KNOWLEDGE]

### 5.3 FAILED matrix：从四个外部观察证明 rollback

核心位置：[verify_t1201_ingestion.py:508](../../backend/scripts/verify_t1201_ingestion.py#L508)。

```python
failed_baseline_count = store.get_chunk_count("t1201-pdf")
KeywordRetriever(store).keyword_search("t1201-pdf", "FAILED_SCAN_UNIQUE", 5)

with patch.object(
    dashscope.MultiModalConversation,
    "call",
    return_value=ocr_failure(),
), patch.object(ingest_mod.time, "sleep", return_value=None):
    failed_response = upload(
        "t1201-pdf", "all-failed.pdf", all_failed_pdf, "application/pdf"
    )

check(
    "AC-F002-09 FAILED leaves no raw file, chunk/vector/metadata, or keyword entry",
    not (upload_root / "t1201-pdf" / "all-failed.pdf").exists()
    and store.get_chunk_count("t1201-pdf") == failed_baseline_count
    and not any(item.get("file_name") == "all-failed.pdf" for item in current_files)
    and failed_keyword_results == [],
)
```

为什么不是只断言 `HTTP 422`：

- 422 只说明 error mapping，不说明保存后的 raw file 被删；
- chunk count 回到 baseline 说明失败请求没有增加 persisted chunk set；
- file-list 不出现名称说明 FAILED 没形成 file-level projection；
- keyword query 为空说明检索侧没有残留 token→chunk visibility；
- 随后的 same-name retry 200 证明 duplicate preflight 没被前一次失败锁住。

这组断言刻意使用公开接口与业务结果。脚本无法从 422 response 获得内部 `file_id`，所以采用 baseline + file list + keyword search + retry 组合证明 observable semantics；它不读取 Chroma `_collection` 私有对象。[PROJECT FACT]

`patch.object(ingest_mod.time, "sleep", return_value=None)` 只去掉 retry backoff 的真实等待，没有减少 retry attempts；`ocr_call.call_count == 9` 仍证明 3 pages × 3 total attempts。[PROJECT FACT]

### 5.4 Real retrieval + controlled scores：分别证明接线和数学

核心位置：[verify_t1202_retrieval_qa.py:311](../../backend/scripts/verify_t1202_retrieval_qa.py#L311) 与 [verify_t1202_retrieval_qa.py:457](../../backend/scripts/verify_t1202_retrieval_qa.py#L457)。

```python
keyword_results = keyword.keyword_search(
    knowledge_base, "机器学习是什么", 6
)
vector_results = vector.vector_search(
    "机器学习是什么", knowledge_base, 6
)
hybrid_results = hybrid.hybrid_search(
    "机器学习是什么", knowledge_base, 3
)

check(
    "AC-F011-01 real branch scores use the fixed 0.3/0.7 fusion formula",
    all(
        math.isclose(
            item["final_score"],
            keyword_by_id[item["chunk_id"]]["keyword_score"] * 0.3
            + vector_by_id[item["chunk_id"]]["vector_score"] * 0.7,
        )
        for item in hybrid_results
    ),
)
```

这里先通过真实 upload生成 chunks，再由真实 Keyword/Vector/Hybrid各查一次；`chunk_id` 是三份结果之间的 join key。测试不是用 list index 对齐，因为两个 branch的候选集合和顺序可以不同。[PROJECT FACT]

随后脚本把 `0.8` 与 `0.9` 的 static rows注入**真实 HybridRetriever**，精确检查 `0.87`。Controlled rows替代的是上游 branch output，不替代被验的 merge/fusion/filter code。这个组合方式可以概括为：

```text
real corpus path      → composition confidence
controlled score path → arithmetic/boundary confidence
```

T1202 broad matrix的deterministic embedding不是随机hash-only double；它为“机器学习/人工智能/AI”“子领域/分支”等词组分配显式feature dimensions，所以该matrix中的语义来自测试作者。真实BGE语义另由`verify_bge_model.py`在临时Chroma中独立验证，不应混用两类evidence label。[PROJECT FACT]

### 5.5 `RecordingOpenAI`：替代 transport，不替代 DeepSeekClient

核心位置：[verify_t1202_retrieval_qa.py:181](../../backend/scripts/verify_t1202_retrieval_qa.py#L181)、[qa.py:321](../../backend/app/services/qa.py#L321) 与 [verify_t1202_retrieval_qa.py:648](../../backend/scripts/verify_t1202_retrieval_qa.py#L648)。

```python
class RecordingOpenAI:
    constructor_calls: list[dict] = []
    create_calls: list[dict] = []
    forced_outcomes: list[object] = []

    def __init__(self, **kwargs) -> None:
        type(self).constructor_calls.append(kwargs)
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

with (
    patch.object(qa_mod, "OpenAI", RecordingOpenAI),
    patch.object(qa_mod.time, "sleep", return_value=None) as retry_sleep,
):
    match_response = client.post("/api/query", json=...)
```

`patch.object(qa_mod, "OpenAI", ...)` 很重要：`DeepSeekClient._get_client()` 在 `qa.py` module namespace查找 `OpenAI`，所以要 patch **使用方的名字**，不是另一个模块里同名 symbol。真实 `_get_client()` 仍读取 key、传入 base URL/timeout/`max_retries=0`；真实 `generate_answer()` 仍构造 system/user messages、应用 model options、分类异常、循环重试并解析 response。[PROJECT FACT]

double 的 `constructor_calls` 和 `create_calls` 相当于 spy，允许从调用记录检查那些不会直接出现在 HTTP response里的 outbound contract。`forced_outcomes`则是一个 FIFO队列：元素是异常就 raise，是字符串就包成 OpenAI-compatible response shape；由此可稳定驱动“timeout后成功”和“三次耗尽”。[PROJECT FACT]

`time.sleep` 被 patch 只消除 1s/2s wall-clock backoff；`create_calls` 增量与 `retry_sleep.call_count` 仍分别证明 attempts和等待次数。真实 OpenAI SDK serialization、TLS、DeepSeek auth/rate-limit payload以及 provider response shape仍未执行。[PROJECT FACT]

### 5.6 Empty collection 与 empty retrieval：控制流相似，业务结果相反

核心位置：[qa.py:515](../../backend/app/services/qa.py#L515) 与 [verify_t1202_retrieval_qa.py:732](../../backend/scripts/verify_t1202_retrieval_qa.py#L732)。

```python
if vector_store.get_chunk_count(collection_name) == 0:
    raise AppError("COLLECTION_EMPTY")

results = self._get_hybrid_retriever().hybrid_search(...)
context_text = assemble_context(results)
history_text = process_history(history)
answer_text = self._get_llm_client().generate_answer(...)
sources = assemble_sources(results)
```

`get_chunk_count()==0` 是 preflight terminal branch：脚本临时把 `HybridRetriever.hybrid_search` patch成一旦调用就抛 `AssertionError`，同时记录 LLM call count不变。这比只断言 409更强，因为它证明昂贵/无意义的下游工作没有发生。[PROJECT FACT]

非空库的 no-match不是异常。Hybrid返回空 list后，`assemble_context([])` 给出空字符串，`_build_user_message()`把它替换成 placeholder，仍调用 LLM，再由 `assemble_sources([])`返回空数组。这里的“继续调用”是 F012/F013 contract，不应为了省一次 provider call而静默改成 backend硬编码答案。[PROJECT FACT]

**TypeScript 类比**：这像 service function先用 repository count执行 guard clause；通过 guard后，即使 `rankedHits.length===0`，仍调用 configured answer adapter。两种 `[]` 出现在不同 state boundary，不能只看容器形状就合并语义。

### 5.7 Traversal matrix：从真实 request 证明 validation-before-write

核心位置：[verify_t1203_file_management_security.py:246](../../backend/scripts/verify_t1203_file_management_security.py#L246) 与 [upload.py:65](../../backend/app/api/upload.py#L65)。

```python
for file_name in ("../doc.pdf", "..\\doc.pdf", "subdir/doc.pdf"):
    files_before = upload_files_snapshot()
    chunks_before = chunk_ids_snapshot()
    response, body = upload(kb_a, file_name, valid_pdf, "application/pdf")

    check(..., response.status_code == 400 and code_of(response) == "INVALID_FILE_NAME")
    check(..., upload_files_snapshot() == files_before
               and chunk_ids_snapshot() == chunks_before)
```

真实 `validate_file_name()` 使用 `PureWindowsPath`，所以即使 host 是 Linux，反斜杠仍按 Windows separator 解释；`../` 与 `subdir/` 也会让 basename 不等于原 filename。更重要的是，它位于 `validate_upload()` 第一步，而 `mkdir/write_bytes` 在完整 validation 返回之后，因而结构上先拒绝、后副作用。[PROJECT FACT]

快照比较把代码顺序提升为 runtime evidence：哪怕未来在 validation 前不小心新增 write，这一组检查也会因为 snapshot delta 而失败。clean PDF control 又证明危险名拒绝不是 parser 或 extension error 偶然造成的。[ENGINEERING KNOWLEDGE]

### 5.8 Preview divergence probe：正向内容 + 负向调用双证据

核心位置：[verify_t1203_file_management_security.py:389](../../backend/scripts/verify_t1203_file_management_security.py#L389) 与 [files.py:40](../../backend/app/api/files.py#L40)。

```python
expected_preview_full = "\n\n".join(
    chunk.content for chunk in sorted(preview_chunks, key=lambda c: c.chunk_index)
)
raw_path(kb_a, "preview-source.txt").write_text("RAW FILE MUTATED AFTER INGESTION")

with patch.object(IngestService, "process", side_effect=AssertionError(...)), ...:
    preview_response = client.get(f"/api/files/{file_id}/preview", params=...)
```

正向断言要求 response content 等于 persisted chunks；负向断言要求 raw mutation 不出现，且 ingestion/parsers/OCR/embedding/LLM 的总 call count 为 0。两类证据相互补强：前者说明“读到了什么”，后者说明“没有从哪些昂贵或漂移边界读取”。[PROJECT FACT]

### 5.9 Cascade + re-upload：沿 immutable IDs 检查旧状态消失

核心位置：[verify_t1203_file_management_security.py:533](../../backend/scripts/verify_t1203_file_management_security.py#L533) 与 [files.py:83](../../backend/app/api/files.py#L83)。

```python
deleted_chunk_ids = {chunk.chunk_id for chunk in store.get_chunks_by_file(kb_a, file_id)}
KeywordRetriever(store).keyword_search(kb_a, "cascadeuniquekey", 5)
delete_response = client.delete(f"/api/files/{file_id}", params={"collection_name": kb_a})

# raw absent + Chroma/file projection absent + cache dirty/rebuilt
# then same display name gets a different file_id and fresh chunks
```

这里的核心不是文件名，而是 identity transition：`old file_id + old chunk_ids → absent`，随后 `same display name → new file_id + new chunk_ids`。KB-B 以相同 display filename 充当 isolation control；若删除错误地按 filename 做全局匹配，它的 raw/chunks/preview 任一项都会变化并触发失败。[PROJECT FACT]

删除 endpoint 自身没有跨存储 rollback。此 close read 只能支持“在没有注入故障的运行中，成功响应对应完整 observable cleanup”，不能支持“任意中间失败都原子恢复”。[ENGINEERING KNOWLEDGE]

### 5.10 AC inventory：先保留occurrence，再做set union

核心位置：[verify_t1204_spec_acceptance.py:163](../../backend/scripts/verify_t1204_spec_acceptance.py#L163)。

```python
section_5 = spec_text.split("## 5.", 1)[1].split("## 6.", 1)[0]
section_12 = spec_text.split("## 12.", 1)[1].split("## 13.", 1)[0]
feature_acs = re.findall(r"\*\*(AC-[A-Z0-9-]+):", section_5)
cross_feature_acs = re.findall(r"\*\*(AC-[A-Z0-9-]+):", section_12)
unique_acs = set(feature_acs) | set(cross_feature_acs)
```

两个list保留occurrence语义，set union承担去重；若一开始只建set，就无法证明Section 5的65次与Section 12的39次都被保留。当前断言是count equality而非set equality，所以Learning Pass另外比较了report matrix与SPEC exact set。[ENGINEERING KNOWLEDGE]

DoD代码从整个Section 13提取ID并用`>= {DOD-01..06}`检查mandatory IDs存在；因为Section 13.2本来还有recommended DOD-07～10，输出label中的“exactly”不应理解为“Section 13只能出现六个DOD”。更准确的语义是：**mandatory subset完整存在**。[PROJECT FACT]

### 5.11 OpenAPI与error catalog：集合相等防止“多也算通过”

核心位置：[verify_t1204_spec_acceptance.py:197](../../backend/scripts/verify_t1204_spec_acceptance.py#L197)。

```python
actual_routes = {
    path: set(operations) & {"get", "post", "put", "patch", "delete"}
    for path, operations in openapi_paths.items()
}
check("OpenAPI route/method surface matches SPEC Section 6",
      actual_routes == expected_routes)

actual_error_statuses = {
    code: value[0]
    for code, value in _ERROR_CATALOG.items()
    if code not in {"OCR_PAGE_FAILED", "PAGE_RENDER_FAILED"}
}
```

`==`同时拒绝missing与extra route/error，不像subset check只防缺失。warning-only codes被刻意从HTTP equality移出后再做presence check，体现“同一个catalog里存放，不代表同一种transport语义”。[ENGINEERING KNOWLEDGE]

### 5.12 Rename双层补偿：storage原子边界 + route orchestration边界

核心位置：[vector_store.py:297](../../backend/app/core/vector_store.py#L297)、[collections.py:102](../../backend/app/api/collections.py#L102) 与 [verify_t1204_spec_acceptance.py:501](../../backend/scripts/verify_t1204_spec_acceptance.py#L501)。

```python
# storage layer
col.modify(name=new_name)
self._client.get_collection(new_name).update(ids=ids, metadatas=new_metadatas)
# exception → restore metadata, then collection name

# API orchestration layer
store.rename_collection(old_name, new_name)
_rename_uploads_dir(old_name, new_name)
invalidate_keyword_index(old_name)
invalidate_keyword_index(new_name)
_verify_rename(store, old_name, new_name)
# exception → uploads back, then VectorStore.rename_collection(new, old)
```

VectorStore拥有Chroma collection+metadata的原子边界；API route拥有Chroma、uploads directory、cache seam的组合边界。测试在第二层注入filesystem rename失败，实际触发第一层的反向rename。分层补偿的价值是每层只恢复自己拥有的state，同时上层按完成标记逆序调用。[ENGINEERING KNOWLEDGE]

### 5.13 Browser harness：seed与external-edge substitution必须发生在server启动前

核心位置：[serve_t1204_browser_backend.py:56](../../backend/scripts/serve_t1204_browser_backend.py#L56)。

```python
probe_root = Path(tempfile.mkdtemp(prefix="t1204_browser_"))
os.environ["UPLOAD_DIR"] = str(probe_root / "uploads")
os.environ["CHROMA_PERSIST_DIR"] = str(probe_root / "chroma")

qa_mod.DeepSeekClient.generate_answer = deterministic_answer
client = TestClient(app, raise_server_exceptions=False)
# create browser-kb/browser-empty and upload machine-learning.txt
uvicorn.run(app, host="127.0.0.1", port=8000)
```

同一个`app`先由TestClient seed，再由Uvicorn暴露给browser，因此浏览器看到的是真实持久化状态，不是前端mock response。`deterministic_answer`只控制answer/500 branch；sources仍由真实retrieval path组装。`finally`负责正常退出清理，但强制kill无法保证Python finally执行，因此本轮在停止服务后又显式验证并删除精确temp target。[PROJECT FACT]

---

## 6. 数据流：REAL path、SUBSTITUTED edges 与 failure exits

```text
parent process
  → mkdtemp(system temp)
  → spawn child with --probe-root
      → set UPLOAD_DIR / CHROMA_PERSIST_DIR before import
      → import real FastAPI app + services
      → install deterministic model edge
      → generate TXT/MD/DOCX/Excel/PDF fixtures
      → TestClient POST /api/collections                 [REAL ASGI]
      → TestClient POST /api/upload multipart            [REAL ASGI]
          → validate → save                              [REAL filesystem]
          → parse → OCR adapter → clean → chunk          [REAL code]
                    ↘ MultiModalConversation.call        [SUBSTITUTE]
          → encode_chunks/get_model                      [REAL adapter]
                    ↘ SentenceTransformer model          [SUBSTITUTE]
          → add_texts                                    [REAL Chroma]
          → invalidate keyword index                     [REAL memory cache]
          → UploadResponse / AppError envelope           [REAL API]
      → inspect file list / public store/search/cache    [REAL]
      → aggregate 81 required checks → exit 0/1
  → child exits, OS releases handles
  → parent removes temp root
  → propagate child exit code
```

T1202 在同一种隔离外壳里走查询链：

```text
known UTF-8 text
  → POST /api/upload                               [REAL]
  → parse / clean / chunk / encode
                        ↘ SentenceTransformer      [SUBSTITUTE]
  → Chroma documents + vectors                    [REAL]
  → POST /api/query {question, collection, top_k, history}
  → API validation + collection existence         [REAL]
  → QAService collection chunk-count preflight    [REAL]
       0 chunks → 409 COLLECTION_EMPTY             [REAL failure exit]
  → KeywordRetriever + VectorRetriever             [REAL]
  → merge by chunk_id → 0.3/0.7 → sort/filter/top-k
  → assemble_context + process_history             [REAL]
  → DeepSeekClient builds system/user messages     [REAL]
                        ↘ OpenAI/DeepSeek transport [SUBSTITUTE]
  → answer text + assemble_sources(results)        [mixed + REAL sources]
  → QueryResponse / AppError envelope              [REAL API]
  → aggregate 46 checks → parent cleanup → exit
```

T1203 继续复用隔离外壳，但围绕一个 file identity 观察完整生命周期：

```text
multipart filename + bytes
  → POST /api/upload validation                       [REAL]
       unsafe → 400 + raw/chunk snapshots unchanged  [REAL failure exit]
       safe   → raw file + persisted chunks           [REAL]
                         ↘ SentenceTransformer model  [SUBSTITUTE]
  → GET /api/files                                    [REAL projection]
  → GET /api/files/{file_id}/preview                  [REAL persisted read]
       → sort chunks → join → truncate                [REAL]
       ↛ raw/parser/OCR/embed/LLM                      [verified non-calls]
  → DELETE /api/files/{file_id}
       → unlink raw → delete Chroma rows → mark cache dirty
  → keyword search triggers lazy rebuild              [REAL]
  → same-name upload → new file_id                    [REAL]
  → compare KB-B isolation + static frontend wiring
  → aggregate 43 checks → parent cleanup → exit
```

T1204把execution evidence提升为audit evidence，并增加一条真实browser path：

```text
frozen SPEC
  → Section 5 regex scan                         65 occurrences
  → Section 12 regex scan                        39 occurrences
  → set union                                    85 unique IDs
  → inventory union                               85 IDs

real FastAPI app
  → generated OpenAPI                            [REAL runtime surface]
  → _ERROR_CATALOG                               [REAL runtime catalog]
  → expected route/error dictionaries            [MANUAL FROZEN ORACLE]
  → equality checks

F001/F008 fixtures
  → TestClient + generated PDF + public store    [REAL]
  → SentenceTransformer constructor              [SUBSTITUTE]
  → success rename / injected uploads failure
  → state-vector assertions → 29/29

browser
  → Next.js → fetch → Uvicorn/FastAPI             [REAL]
  → retrieval/Chroma/filesystem                   [REAL]
  → embedding model + DeepSeek transport          [SUBSTITUTE]
  → rendered navigation/answer/source/errors      [REAL UI observations]
```

### 主要类型变化

```text
runtime fixture bytes
  → multipart UploadFile
  → raw Path
  → parsed str
  → cleaned str
  → List[{chunk_id, file_id, content, chunk_index}]
  → List[List[float]] (512-dim deterministic vectors)
  → Chroma documents + embeddings + 9-field metadata
  → UploadResponse / ErrorResponse + public read projections

query JSON
  → QueryRequest fields
  → keyword tokens + 512-dim query vector
  → two branch result lists
  → merged List[{chunk_id, final_score, ...}]
  → context/history strings + two LLM messages
  → answer str + List[SourceObject(relevance_score=final_score)]
  → QueryResponse JSON

file lifecycle
  → UploadResponse.file_id
  → FileItem projection + List[ChunkRecord]
  → FilePreviewResponse(content, preview_chars, total_chars)
  → deleted old file_id/chunk_ids + dirty collection marker
  → rebuilt keyword index without old IDs
  → new UploadResponse.file_id for the same display name

audit inventory
  → List[AC occurrence in Section 5]
  → List[AC occurrence in Section 12]
  → Set[unique AC ID]
  → area/evidence/result rows in Markdown report

rename lifecycle
  → old collection/chunk/raw/cache state vector
  → new collection with preserved immutable IDs/scores
  → or injected failure → restored old state vector + RENAME_FAILED
```

### Error / recovery exits

| 失败点 | 对外形态 | T1201 怎样观察 |
|---|---|---|
| extension/empty/oversize | 400/400/413 typed code | response + zero persistence delta |
| cleaned text empty | 422 `FILE_PARSE_ERROR` | raw file absent |
| one OCR page exhausts retries | 200 `SUCCESS_WITH_WARNINGS` | good page text persists + exact warning + 3 attempts |
| all OCR pages fail | 422 `FILE_PARSE_ERROR` | warnings preserved + four-store/read-model rollback checks + retry 200 |
| duplicate same KB | 409 `FILE_ALREADY_EXISTS` | case-insensitive name variant |
| same name different KB | two 200 responses | collection isolation |
| harness isolation violation | RuntimeError / exit non-zero | resolved paths must stay outside repository |
| cleanup cannot remove temp root | exit 1 | parent checks `probe_root.exists()` |

T1202 的查询侧 exits：

| 状态/失败点 | 对外形态 | T1202 怎样观察 |
|---|---|---|
| non-empty + relevant hits | 200 answer + 3 sources | persisted IDs、descending score、no inline citation |
| non-empty + filtered empty | 200 no-information + `sources=[]` | LLM call增加且prompt含empty-context placeholder |
| collection exists but 0 chunks | 409 `COLLECTION_EMPTY` | Hybrid patch不得被调用，LLM count不变 |
| top_k为0/21/-1 | 400 `INVALID_TOP_K` | 三个真实API request；focused route test另证 storage/service不启动 |
| transient timeout | 第二次attempt成功→200 | create calls +2，sleep calls +1 |
| 三次timeout | 502 `LLM_UNAVAILABLE` | create calls +3，sleep calls +2 |
| retrieved instruction | 200 safe double answer | system/user位置真实；provider compliance substituted |

T1203 的文件生命周期 exits：

| 状态/失败点 | 对外形态 | T1203 怎样观察 |
|---|---|---|
| unsafe parent/Windows/nested filename | 400 `INVALID_FILE_NAME` | 每个 request 前后 raw/chunk snapshots 相等 |
| clean supported filename | 200 `SUCCESS` | raw bytes、UUID、Chroma file projection 一致 |
| preview missing collection | 404 `COLLECTION_NOT_FOUND` | collection preflight 优先 |
| preview missing/cross-KB file ID | 404 `FILE_NOT_FOUND` | 正确 KB 文件保持可见 |
| valid delete | 200 confirmation | raw/Chroma/file view/keyword old identity 全消失 |
| missing/cross-KB delete | 404 `FILE_NOT_FOUND` | filesystem 与 chunks 不变，KB-B raw 保留 |
| same-name re-upload | 200 + new UUID | 旧 IDs 不复活，新 chunks/keyword results 可见 |
| mid-cascade exception | 未注入 | 不能从 success matrix 推出 compensation/atomicity |

T1204新增的审计与browser exits：

| 状态/失败点 | 对外形态 | T1204怎样观察 |
|---|---|---|
| AC inventory count drift | probe exit 1 | Section 5/12/unique任一count不等于65/39/85 |
| report/spec ID drift | Learning Pass review fail | exact-set comparison出现missing或extra；当前均为空 |
| route/method或HTTP error drift | probe exit 1 | generated runtime set与frozen oracle不相等 |
| rename uploads step failure | 500 `RENAME_FAILED` | old Chroma/metadata/vector/raw/path全部恢复，new residue为零 |
| empty KB browser query | rendered warning | history已清空，显示空库提示与retry action |
| deterministic LLM response error | rendered error | 500映射为统一QA error与retry action |
| backend stopped | rendered connection error | reload后显示可理解提示与“重新加载” |
| 51 MiB selection | frontend rejection | queue=0，backend file count保持1→1 |

### Mental Model

把 T1201 想成一个**密封的摄取实验舱**：入口是真实 HTTP contract，内部的管道与 Chroma 是真实装置；只有仓库当前缺少或需要联网的两台昂贵设备被换成尺寸、接口与行为可控的校准器。实验结束后整间舱室被拆除。结论能证明装置之间的连接和数据契约，却不能证明被替代设备的真实质量、速度或可用性。

T1202 是相邻的**查询实验舱**：先把已知样本通过真实入口放进真实存储，再观察同一 persisted identity怎样经过两个 ranker、一个 fusion gate、context/history与LLM adapter分成 answer/source两条输出。模型double像信号发生器：它让路径可测，却不是被替代模型本身的质量证书。

T1203 是一条**带双仓对照的证物链**：KB-A 的 file ID 像封条编号，从入库、清单、预览、销毁到重新编号都被记录；KB-B 放置同名对照物，任何按 filename 越界的操作都会暴露。危险 filename 则在进入证物室前被拦截，并通过“门内状态完全没变”证明拦截足够早。

T1204是一位**总账审计员**：65与39是两本必须分别点数的账，85是合并后去重的账户清单；29个现场抽查只负责部分高风险项。浏览器记录像柜台录像，不能替代外部provider质量检测；因此在provider凭证缺失时，总账与Phase Gate都必须保持未通过。

---

## 7. 架构设计：verification artifact 本身也有 architecture

### 新增能力

- 一条可重复的 ingestion composition probe，而不是零散 helper checks；
- runtime generation 的 11-extension fixture matrix；
- 对 success/warning/failed 三态的同一入口验证；
- 对 filesystem、Chroma、keyword index 与 file list 的跨边界观察；
- 能在 Windows 上释放 Chroma handles 并验证 temp cleanup 的 process wrapper。
- 一条从真实 upload seed到真实 query response的 retrieval/QA composition probe；
- 对 real-corpus wiring与 controlled-score arithmetic的双层验证；
- 对 answer/model authority与 sources/backend authority的独立观察；
- 对 empty collection、filtered-empty、invalid input与provider retry的分支证据。
- 一条真实 upload→list→preview→delete→re-upload 的 file-lifecycle probe；
- 对 traversal rejection、persisted-preview source、cascade cleanup 与跨 KB isolation 的联合观察；
- 通过 old/new file/chunk IDs 检查删除后重传没有 stale identity。
- 一份把104个mandatory occurrences去重为85个ID并逐area映射primary evidence的final audit ledger；
- 一条补齐F001 endpoint lifecycle、rename compensation、literal F008-02和runtime API/error surface的probe；
- 一套可启动deterministic backend的browser harness，以及当前checkout上的6场景UI/HTTP evidence。

### 契约兑现

T1201 把 F002–F008 的关键行为与 Section 12.2/12.3 AC 放进同一次 execution。它还检查两个容易被“功能成功”掩盖的 non-functional contract：所有 Chroma access 通过 public interface，以及 test storage 不得指向 repository tree。[PROJECT FACT]

T1202 把 F009–F015 与 Section 12.4 的关键行为放进同一 execution，并把 score ownership、`chunk_id` identity、context budget、history window、system/user prompt hierarchy和 backend-owned sources贯通到 public API response。[PROJECT FACT]

T1203 把 F016 的 preview/delete contracts、Section 10.2 与 Section 12.7 的 filename security 放进同一次 execution，并把 upload 产生的真实 identity 贯通到 list、preview、delete、keyword rebuild 与 re-upload。它还用第二个真实 KB 作为同名隔离对照。[PROJECT FACT]

T1204把Section 5与12全部mandatory inventory、Section 6 API、Section 9 errors、Section 13.1 DoD与Section 15 coverage视角汇总进一份审计报告；当前报告matrix与SPEC exact ID set一致，F001/F008/runtime contracts与frontend browser path又获得新增执行证据。[PROJECT FACT]

### 设计边界

- TestClient 证明真实 ASGI composition，不证明 live server/network/CORS。
- Deterministic vectors证明broad matrix的数量、维度、normalization flag与wiring；独立REAL脚本已证明当前固定revision的加载、512维、norm与受控中文语义排序，但不构成大规模quality/latency benchmark。
- Deterministic OCR response 证明 adapter/retry/status/warning wiring，不证明 Qwen-VL OCR accuracy、authentication 或 service availability。
- Synthetic fixtures 精确、可重复，但不代表真实世界 corrupted/complex Office/PDF corpus。
- 脚本当前为手动 command，不在 CI/test runner 自动发现范围。
- T1202 deterministic semantic dimensions证明 query→vector→Chroma wiring，不证明 bge的真实近义词能力或 ranking quality。
- RecordingOpenAI证明 DeepSeekClient outbound contract、retry和response extraction，不证明真实 SDK/network/provider behavior。
- prompt injection场景证明结构性mitigation和double contract，不是安全保证；真实provider需要独立red-team/eval。
- TestClient不经过TCP/CORS/browser；Frontend的history append、KB-switch clearing与source rendering不在T1202路径内。

- T1203 的 traversal matrix 只覆盖冻结 SPEC 点名的三种 filename；absolute、encoded、Unicode、symlink 与 fuzzing未执行。
- 成功 delete 的多状态清理不证明 mid-cascade exception会补偿；当前实现仍没有跨 filesystem/Chroma/cache transaction。
- FileManager/API client 只做 source string assertion，不证明 TypeScript build、React runtime、网络请求、UI refresh或 accessibility。
- T1204 browser matrix关闭了导航、QA render/source、KB-switch reset、409/500/network与51 MiB validation这些具体runtime gaps；它没有覆盖FileManager modal/delete/refresh、KB CRUD、ErrorBoundary render crash、responsive/browser matrix或完整accessibility。
- Browser backend harness已仓库化，browser assertions没有形成repository-owned automated suite；当前6/6是可复现执行记录，不是CI regression asset。
- T1204的65/39/85是count guard；exact-set match由本Learning Pass独立检查，Given/When/Then semantic hash与AC→assertion machine binding仍不存在。
- API/error expected dictionaries是人工冻结oracle；它们与当前SPEC一致，但未来contract change需要同步维护。

### 与旧验证的关系

T0503 重点证明 FAILED atomicity 的多种异常/回滚形态；T1201 重点证明所有支持格式、成功/警告/失败状态以及 F005–F008 能在同一真实 upload composition 中贯通。二者是 coverage expansion，不应互相覆盖或把旧历史叙事改写成“直到 T1201 才第一次验证回滚”。

Phase 7/8 的 unit、Mocked composition和route tests先冻结每层contract；T1202再用真实Chroma与真实API把它们串起来。两者不是替代关系：unit tests更精确覆盖tokenizer/error taxonomy，T1202更擅长发现跨层接线、identity和state boundary问题。[PROJECT FACT]

Phase 9 的 10 个 Mocked route tests精确锁定 response shape、preflight与调用顺序，一条 concrete smoke验证已持久化数据上的 list/preview/delete；T1203再从真实 upload开始，并观察真实 raw/Chroma/cache/re-upload。它关闭的是 composition gap，不会抹去 unit tests对 failure ordering的价值，也不会自动关闭 mid-cascade compensation gap。[PROJECT FACT]

Phase 4早期tests与学习材料定义了F001 ownership；T1204不是重新实现KB API，而是用真实endpoint、Chroma、filesystem、keyword cache和fault injection把成功/失败state vector持久化为最终证据。T1201的10/1 deletion fixture仍是有效语义证据，T1204的5/3只提高literal fidelity。[PROJECT FACT]

---

## 8. Engineering Review 摘要（非完整 Phase 12 Review）

Phase 12 独立 Engineering Review 尚未建立；本节只记录理解 T1201–T1204 所需的 decision summary：

- 用 child process 同时解决 settings import cache 与 Chroma handle cleanup；
- 用 system temp tree + repository containment guard 防止测试污染；
- 在 external/heavy edge 做窄替代，保留 application composition；
- runtime 生成 binary fixtures，避免依赖手工准备的隐形输入；
- 用 public observable behavior 证明 rollback，而不是锁定私有实现；
- 聚合所有 required checks，并让 cleanup failure 影响最终 exit code。
- T1202同时保留真实corpus path与controlled-score path，避免用一种fixture回答两个不同问题；
- 只替代OpenAI-compatible transport，保留DeepSeekClient的配置、prompt、retry与错误映射；
- 用调用记录观察outbound contract，用queued outcomes驱动retry branches；
- 把sources从retrieval results直接组装，避免把模型输出当成citation authority；
- 用preflight call-count assertions区分empty collection和empty retrieval。
- 用 request 前后 snapshots 证明危险 filename 拒绝没有 raw/Chroma 副作用；
- 用 raw mutation + fail-fast probes 证明 preview 的 persisted source-of-truth；
- 用双 KB 同名 control 与 old/new IDs 证明 delete/re-upload 的 isolation 和 stale-state absence；
- 把 frontend source assertion 降级标为 static wiring smoke，不冒充 browser E2E。
- 同时保留104个occurrences与85个unique IDs，避免漏掉双source-of-truth或重复计算；
- 把final report、focused executable probe与browser server harness分成三个职责；
- 用完整identity/metadata/vector/raw/cache state证明rename success与compensation；
- 用真实Next.js/Uvicorn浏览器路径补UI state与error rendering证据，并公开model/LLM substitutions。

当前需保留给后续Engineering Review的问题：CI ownership、真实provider/model acceptance threshold、AC count guard升级为semantic manifest、machine-readable traceability、repository-owned browser runner、prompt-injection eval标准、provider failure fixtures、PyMuPDF import deprecation、console encoding、完整path fuzz/symlink测试、delete mid-cascade fault/compensation策略、F016 literal 15-chunk fidelity、未覆盖frontend runtime与更大corpus的时间/空间成本。完整ADR、failure taxonomy与规模分析不在Task Learning Pass展开。

---

## 9. Technical Decision：验证范围怎样换取速度与可信度

| 决策 | 备选 | 选择理由 | 代价 / 边界 |
|---|---|---|---|
| 真实 TestClient route，而非直接调 service | unit-call `IngestService.process()` | 覆盖 multipart、validation、save、error handler、response mapping | 不经过真实 TCP/Uvicorn/CORS |
| temp filesystem + real Chroma | in-memory fake store | 验证持久化、metadata、search/delete 与句柄 lifecycle | 启动更慢，需 child cleanup |
| broad matrix替代model constructor | 每个场景重复运行真实BGE | 保留分支可重复性与运行速度；真实模型由独立离线probe验证 | broad matrix本身仍非REAL model evidence |
| 替代 DashScope call | live Qwen-VL | 无 key且避免网络不确定；保留 render/Base64/retry/warnings | 不证明 provider auth、latency、OCR accuracy |
| runtime 生成 fixtures | 提交 binary test-data | 可重复控制页型/表格/sheets且不膨胀仓库 | 合成文档覆盖不了复杂真实文档 |
| child process | 同进程改 env + cleanup | settings/module cache 与 Windows file handles 都能重置 | 多一次进程启动，输出编码更复杂 |
| aggregated `check()` | 第一失败立即 assert | 一次运行得到完整矩阵，便于定位 coverage holes | 未捕获异常仍可能提前终止；label discipline更重要 |
| standard-library unittest 回归 | 强制 pytest | 当前测试文件使用 unittest，仓库未声明 pytest dependency | 缺少 pytest ecosystem，不应把未安装误写为测试失败 |
| real retrieval + controlled branch rows | 只用real corpus或只用Mocks | 前者证明接线，后者精确复现固定数值与filter边界 | 两种evidence level必须分开陈述 |
| patch `qa_mod.OpenAI` transport | patch整个QAService或调用live DeepSeek | 保留真实prompt/config/retry/orchestration，且当前无测试credential | 不证明SDK/network/provider compatibility与answer quality |
| empty filtered context仍调用LLM | backend直接返回固定文案 | 遵守F012/F013 ownership，统一由System Prompt定义回答 | 每次无匹配仍产生provider调用成本 |
| sources由backend投影 | 让LLM生成/解析citation | identity与score可追溯到retrieval结果 | v1没有inline marker与source-content alignment |
| rejection 前后比较 raw/chunk snapshots | 只断言 400 error code | 同时证明 validation结果与no-side-effect时序 | 只覆盖声明的输入矩阵，snapshot范围需要随新存储扩展 |
| 修改 raw file 后再 preview | raw与chunks保持相同内容 | 制造两个 source之间的可观察分歧，定位真正source of truth | 属于测试性 mutation，只证明chunk-based preview |
| 双 KB 同名 isolation control | 只测单 KB happy path | 能暴露按filename全局删除/读取错误 | 不等于用户级授权或多租户安全 |
| frontend source string assertion | browser自动化 | 低成本捕获当前identity参数接线 | 对等价重构脆弱，不能覆盖runtime behavior |
| 65/39/85三重count guard | 只维护一张手写总表 | 自动发现明显的scope缩减，保留occurrence/unique双口径 | 等量ID/语义替换不会被count发现 |
| report evidence ledger + focused probe | 写一个“万能脚本” | 复用前序强证据并把剩余gap集中验证 | traceability仍是Markdown人工映射 |
| OpenAPI/error set equality | subset或抽样检查 | 同时捕获missing、extra与method/status drift | expected oracle是手写常量，需同步SPEC |
| injected uploads rename failure | 只测success rename | 证明route-level reverse compensation与完整old state | 未穷举storage/cache verification等每个故障点 |
| checked-in browser backend harness | 前端完全mock API | 保留真实HTTP/FastAPI/retrieval/storage路径且结果确定 | 浏览器assertions未仓库化，CI不能自动发现 |

---

## 10. Interview Notes（Task candidates only）

- **候选主线**：我没有把“E2E”粗暴等同于“零 mock”，而是画出 fidelity map：真实 HTTP composition、真实 parser/Chroma/cache，只有缺失模型与外部 OCR call 被窄替代；所以结论准确叫 isolated substituted E2E。
- **候选问题 1**：为什么 env 必须在 import 前设置？——Pydantic settings/module singleton 已 import 后不会因 env 改变自动重建。
- **候选问题 2**：为什么用 child process？——隔离 Python module/singleton state，并让 child exit 后 OS 释放 Chroma Windows handles。
- **候选问题 3**：怎样证明 FAILED rollback？——HTTP 422 + raw absent + chunk baseline + file-list absent + keyword absent + same-name retry，不碰私有 API。
- **候选问题 4**：81/81 代表什么？——81 个 required runtime observations，不是 81 个 AC，也不证明被替代 provider/model。
- **T1202 候选主线**：用real path证明composition、用controlled scores证明fusion math，并沿`similarity_score → vector_score → final_score → relevance_score`锁定owner。
- **T1202 候选问题 1**：为什么no-match仍调用LLM而empty KB不调用？——前者是有数据但证据不足，后者是资源无可查询数据。
- **T1202 候选问题 2**：怎样证明sources不是LLM生成？——响应source IDs/score来自真实retrieval rows，transport double只返回answer content。
- **T1202 候选问题 3**：injection check证明了什么？——证明message hierarchy与deterministic contract，不证明live model安全。
- **T1203 候选主线**：用快照证明validation-before-write，用raw/chunk分歧证明preview source，用双KB与old/new IDs证明cascade isolation和无幽灵状态。
- **T1203 候选问题 1**：为什么400不够证明path security？——还要证明raw与Chroma在拒绝前后完全不变。
- **T1203 候选问题 2**：怎样证明preview没有读raw file？——先修改raw，再阻断所有重解析/模型调用，response仍等于persisted chunks。
- **T1203 候选问题 3**：成功级联为何不等于删除原子性？——脚本未注入步骤2/3失败，application也没有跨存储transaction/compensation。
- **T1204 候选主线**：先冻结分母，再把每个AC映射到不同fidelity的primary evidence；29个现场检查与85个逻辑ID是不同维度。
- **T1204 候选问题 1**：104与85为什么都正确？——两个mandatory sections共有19个重复ID，occurrence与unique口径回答不同问题。
- **T1204 候选问题 2**：怎样证明rename失败原子性？——在Chroma forward rename后注入filesystem failure，比较old/new collection、metadata、vectors、raw path和residue。
- **T1204 候选问题 3**：focused probe PASS为什么不是T1204/Phase Gate PASS？——29个检查只覆盖局部runtime与inventory，provider-dependent AC仍需独立REAL证据。
- **诚实边界**：真实BGE固定revision已4/4 PASS；broad probes的最新重跑结果以本轮验收报告为准。DashScope/DeepSeek live仍未执行，browser的embedding/LLM仍为substitutions，delete mid-cascade matrix、完整frontend/browser suite与Phase Gate仍未完成。

不把本 Task 的普通 verification work 扩写成完整 STAR，也不在 Phase 12 未完成时更新项目级 Interview Guide。

---

## 11. Future Improvement（Future / Not implemented）

| 方向 | 触发条件 | 当前归属 | 状态 |
|---|---|---|---|
| live bge model acceptance | 模型文件进入受控验证环境 | Phase 12 remediation | **DONE / REAL**：官方revision、完整目录、权重hash、512维、norm、singleton与临时Chroma语义排序均已验证 |
| live Qwen-VL OCR corpus | 有 test key、预算与稳定 provider window | external dependency acceptance | 本Learning Pass未执行；T0503/T1201使用provider substitution |
| live DeepSeek contract/eval corpus | 有受控test key、预算、redaction与稳定provider window | external dependency acceptance | 本Learning Pass未执行；T1202/browser使用transport/answer substitution |
| live bge retrieval benchmark | 更大有标注query-document corpus可用 | model acceptance | 受控单查询REAL排序已完成；统计性recall/quality/latency benchmark仍Future |
| prompt-injection red-team/eval | 需要衡量真实model在恶意文档下的遵循率 | Security/LLM evaluation follow-up | Future；System Prompt不是安全保证 |
| browser FileManager/KB CRUD/upload success | 验证preview/delete/modal/refresh与mutation reconciliation | frontend acceptance | Future；T1204 browser只覆盖导航、QA/errors与oversize preflight |
| ErrorBoundary render-crash runtime proof | 验证React render error、fallback与reset | frontend acceptance | Future；HTTP/network error不等于render crash |
| repository-owned browser runner | 需要CI重复6个browser assertions | Engineering follow-up | Future；当前只有server harness与执行记录 |
| CI 固化 T1201–T1204 commands | 需要每次变更自动防回归 | Engineering follow-up | Future；当前手动脚本 |
| machine-readable report | CI 需要 JUnit/JSON artifacts 与历史趋势 | Engineering follow-up | Future |
| AC semantic manifest/hash | SPEC允许后续受控变更时仍需检测等量替换 | audit follow-up | Future；当前脚本自动守卫count，本轮人工exact-set |
| machine-readable AC→assertion binding | 需要自动证明每个ID存在有效primary evidence | audit follow-up | Future；当前Markdown evidence ledger |
| richer real-world fixture corpus | synthetic docs 无法代表复杂 layout/corruption | future QA | Future；需控制版权与仓库体积 |
| migrate deprecated `fitz` import surface | PyMuPDF 删除旧 API 前 | dependency maintenance | Future；本轮只有 warning |
| console Unicode output cleanup | Windows logs需要完整中文/符号 | tooling maintenance | Future；不影响 checks/exit code |
| 统一 test runner policy | CI 需要单一入口 | Engineering follow-up | Future；当前 unittest 可用、pytest 未安装 |
| filename fuzz/encoded/absolute/symlink matrix | 安全回归需要超出 literal AC 输入 | Security follow-up | Future；T1203只覆盖三种SPEC filename |
| delete mid-cascade fault injection + compensation policy | 需要定义disk/Chroma/cache任一步失败后的目标状态 | Phase 12 Engineering Review | Future；T1204只关闭rename compensation，不改变delete边界 |

---

## 12. 自测题与答案

### 12.1 T1201 概念与代码阅读

1. **为什么 T1201 不能只调用 `IngestService.process()`？**
   - 因为 Task 要验证 upload E2E；直接调 service 会跳过 multipart、六道 preflight、raw save、HTTP error mapping、keyword invalidation 与 response schema。
2. **为什么准确标签是 SUBSTITUTED E2E？**
   - 路径从真实 ASGI upload 到真实 Chroma/read projections，但 SentenceTransformer 实例和 DashScope network response被替代；path scope 与 dependency fidelity 必须同时表达。
3. **env 为什么要在 application import 前设置？**
   - `settings` 是 import-time singleton；先 import 会把默认/repository路径缓存进当前解释器，之后修改 `os.environ` 不会自动重建它。
4. **为什么 parent 不直接调用 `run_probe()`？**
   - child 提供全新 module/singleton state；退出后还能释放 Chroma file handles，使 Windows temp cleanup可靠。
5. **`patch.dict(sys.modules, ...)` 结束后，后续上传为什么仍使用 fake model？**
   - `get_model()` 已把 fake instance写入 `embedding_mod._model`；module mapping恢复不等于清除已缓存对象。
6. **为什么 deterministic vector 用 one-hot 512 dimensions？**
   - 它天然 L2 norm=1、形状稳定、由文本 hash决定位置；相同文本生成同向量，能经过真实 Chroma cosine search稳定命中。
7. **OCR substitute 到底没有替代什么？**
   - 没替代 PDF page detection/render、JPEG/Base64、frozen model/prompt assembly、retry loop、warning list、status mapping、clean/chunk/store。
8. **为什么 all-failed 场景把 `time.sleep` patch 掉仍能验证 retry？**
   - 只移除 backoff wall time；loop 与 call count不变，3 pages×3 attempts仍由 `ocr_call.call_count == 9` 证明。
9. **为什么 422 不能证明失败原子性？**
   - HTTP code 只证明错误映射；raw file、Chroma data、file projection、keyword visibility仍可能残留。
10. **81/81 是不是 81 个 AC？**
    - 不是。它包含 AC observations，也包含 isolation、fixture、KB setup、adapter wiring、extension coverage 等支持性 required checks。

### 12.2 T1201 推理题

11. **若把 `ChromaVectorStore` 整体 fake 掉，还能声称什么？**
    - 只能证明 API/service 与 fake contract composition；不能证明真实 Chroma metadata、cosine search、delete、persistence或句柄 cleanup。
12. **若 failed chunk count 等于 baseline，但 file list 出现 `all-failed.pdf`，结论是什么？**
    - rollback仍 FAIL；file-level metadata projection出现残余。多 observable assertions 是 AND 关系，不可只挑一个通过。
13. **为什么 F003 AC 必须写 section context？**
    - Feature-level 与 Section 12.3 的相同 `AC-F003-xx` 编号并非总是相同行为；裸 ID 会让 traceability含糊。
14. **主脚本 PASS、pytest command失败，Task是否因此失败？**
    - 不能这样推导。pytest 未安装所以测试没有启动；项目实际 tests 使用 unittest，78/78 PASS。应分别记录 tool availability 与 test result。
15. **F008-02 的 10/1 场景能否写成“逐字复现 5/3 Given”？**
    - 不能。它证明同一 delete isolation语义，但 fixture count不同；最终 literal audit若要求逐字对应，应补 5/3 场景。

### 12.3 T1202 概念与推理题

16. **为什么 T1202 同时需要 real retrieval 与 static branch rows？**
    - Real path证明upload/Chroma/retriever/QA确实接通；static rows精确制造0.8/0.9、0.6/0和20 candidates，证明fusion arithmetic与边界。一个fixture无法同样可靠地回答两类问题。
17. **`similarity_score` 为什么不能在 VectorRetriever 再归一化？**
    - VectorStore已经把distance转换为[0,1] similarity；VectorRetriever只把contract name改成`vector_score`。再归一化会改变与keyword score的固定融合尺度。
18. **同一个数值为什么从 `final_score` 改名为 `relevance_score`？**
    - `final_score`是Hybrid内部结果字段；`relevance_score`是F015 public source contract。`assemble_sources()`只做owner-boundary projection，不重新计算。
19. **空库和no-match各自是否调用retrieval/LLM？**
    - 空库在chunk-count preflight返回409，两者都不调用；非空库no-match经过retrieval得到空list，仍调用LLM并返回200与空sources。
20. **为什么 patch `qa_mod.OpenAI` 而不是 patch一个任意的 `openai.OpenAI` 名字？**
    - Python函数运行时从定义模块的global namespace解析symbol；`DeepSeekClient`查找的是`qa_mod.OpenAI`。应patch where-used，而不是where-defined的另一个binding。
21. **prompt-injection场景能否证明真实DeepSeek安全？**
    - 不能。它真实证明system/user顺序、System Prompt规则和恶意文本位于参考文档段；安全回答来自deterministic double，只是预期contract evidence。
22. **一次timeout后成功与三次timeout耗尽，attempt/sleep数分别是多少？**
    - 前者2 attempts、1 sleep；后者3 attempts、2 sleeps。最后一次失败后没有下一次attempt，所以不再sleep。
23. **怎样证明sources不是LLM生成？**
    - `assemble_sources(results)`在backend从ranked rows投影；API source IDs属于真实persisted chunks。RecordingOpenAI response只含answer字符串，没有source payload。
24. **46/46 是否等于F009–F015的全部AC都以同一fidelity通过？**
    - 不是。46包含setup/isolation/wiring checks；部分AC是real composition，部分用controlled rows，F013/F014的answer semantics使用transport double，F009字面token/index cases还由focused unit suite补足。
25. **为什么还要执行60/60 focused suite和78/78 full suite？**
    - Matrix提高跨层confidence，但不会穷举tokenizer、error taxonomy和route validation；focused suite补细粒度contract，full suite检查T1202没有破坏其他backend paths。

### 12.4 T1203 概念与推理题

26. **为什么 `400 INVALID_FILE_NAME` 不能单独证明 AC-SEC-01？**
    - AC还要求validation先于写入；必须同时证明拒绝前后raw filesystem与Chroma数据没有变化。
27. **为什么三种危险filename要通过真实multipart request发送，而不是只调用`validate_file_name()`？**
    - 真实request还能覆盖multipart parser到`UploadFile.filename`再到route validation的传递，避免transport层先改写或丢失目标输入。
28. **怎样证明preview读取persisted chunks而不是raw file？**
    - 先让两者内容分叉：修改raw，保留Chroma；再阻断parser/OCR/embed/LLM。若response仍等于按index拼接的chunks，source-of-truth才被定位。
29. **为什么preview route在storage已排序后仍再次`sorted()`？**
    - API contract自己承担order语义，避免依赖Mock、未来adapter或storage实现永远满足隐式顺序。
30. **T1203怎样证明delete没有误伤另一个KB的同名文件？**
    - KB-B保留独立file ID、raw bytes和chunk IDs；KB-A delete/re-upload后，KB-B的raw、chunks、list和preview均必须不变。
31. **删除后同名upload成功为什么仍不足以证明无stale state？**
    - 还要检查新旧UUID不同、同名projection恰好一条、旧file ID无chunks、新file ID有chunks、keyword results不含旧chunk IDs。
32. **43/43能否写成43条AC全部通过？**
    - 不能。43包含KB setup、storage isolation、supporting observations和frontend source smoke；AC映射必须按行为表说明。
33. **AC-F016-08的证据是否等于Feature-level AC-F016-02的literal 15-chunk Given？**
    - 不等于。T1203删除fixture有1个chunk，证明Section 12.6的N-chunk级联语义；没有逐字复现Feature-level AC-F016-02的15个chunks。
34. **为什么T1203不能证明cascade failure atomicity？**
    - 它没有在raw unlink后注入Chroma failure或在Chroma delete后注入cache failure；实现也没有跨存储transaction/compensation。
35. **前端source字符串检查到底证明什么？**
    - 只证明当前源码包含`file_id + collection`和URL encoding接线；不证明代码编译、浏览器事件、network request、UI refresh或错误呈现。

### 12.5 T1204 概念与推理题

36. **为什么65 + 39不等于85是数据错误？**
    - 因为Section 5与12有19个重复ID；104是mandatory occurrences，85是set union后的unique IDs，两者都需保留。
37. **29/29是否代表T1204自动执行了85个AC？**
    - 不代表。29是focused probe observations；全量结论由T0503/T1201–T1204、unit/build/runtime/browser与报告traceability组合而来。
38. **count guard能检测哪些漂移，不能检测哪些？**
    - 能检测65/39/85数量变化；不能检测保持数量不变的ID替换或Given/When/Then语义改写。
39. **本轮exact-set comparison比count guard多证明什么？**
    - 证明当前report matrix中的85个ID与当前SPEC union完全相同，无missing/extra；仍不证明每个行为已machine-bind到assertion。
40. **为什么OpenAPI comparison使用set equality而不是subset？**
    - API contract要求exact surface；subset只能发现缺少，无法发现多出的path/method。
41. **warning-only error codes为什么单独检查？**
    - 它们存在于统一catalog但只进入upload warnings，不是独立HTTP error；混入HTTP status equality会扭曲transport contract。
42. **成功rename为什么要比较vector score？**
    - IDs/metadata相同仍不能排除embedding被重写或检索语义漂移；同query score dict相等提供额外identity/persistence证据。
43. **注入uploads rename失败时，哪两层补偿协作？**
    - API orchestration反向调用`VectorStore.rename_collection(new,old)`；VectorStore内部再保证collection+metadata storage rename的原子边界。
44. **browser 6/6能否证明live DeepSeek质量？**
    - 不能。Next.js/HTTP/FastAPI/retrieval/render是真实的，answer/500 branch来自deterministic DeepSeek substitution。
45. **为什么T1204 focused probe 29/29后Task与Phase仍不能PASS？**
    - probe没有执行live DashScope/DeepSeek；Gate已判定substituted provider证据不足，所以T1204为BLOCKED、Phase Gate为FAIL。

### 12.6 动手练习

1. 从脚本输出挑一个场景，画出 `fixture bytes → HTTP → storage → observable assertion` 四段图，并标出 REAL/SUBSTITUTED。
2. 暂时把 `failed_keyword_results == []` 改为 false condition，观察 aggregate summary 与 exit code；完成后恢复，不保留改动。
3. 新增一个只读实验：打印 child 中 `settings.UPLOAD_DIR` 的解析路径，解释 containment guard 的四个条件分别阻止什么。
4. 用 `unittest.mock` 写一个最小示例证明 `patch.dict(sys.modules)` 结束后，另一个模块缓存的 singleton仍存在。
5. 对照 SPEC，为 F003 的两套 AC 编号做一张 `section + id + behavior + script label` traceability table。
6. 对同一`chunk_id`记录keyword/vector/final/relevance四个字段，手算并定位每次改名发生在哪个函数。
7. 把static F011 fixture的`vector_score`从0.9改成0.1，先预测final score与filter结果，再运行脚本；完成后恢复，不保留改动。
8. 给`RecordingOpenAI.queue()`排入“timeout、timeout、success”，预测create/sleep counts和HTTP结果，再用临时实验验证。
9. 从`QAService.answer()`画出empty collection与empty retrieval两条control-flow，标出第一个发生分叉的state read。
10. 设计一个live-provider eval表，但不要执行：至少分开记录prompt结构、answer grounding、language adherence、injection resistance与provider availability，解释为什么不能用一个PASS概括。
11. 为T1203画一个状态表：行是upload/list/preview/delete/re-upload，列是raw、file projection、chunk IDs、keyword cache、KB-B control，填写每一步的期望状态。
12. 给preview设计一个反例：若endpoint错误地读取raw file，`RAW FILE MUTATED AFTER INGESTION`场景会在哪个断言失败？哪些blocked probes可能仍为0？
13. 只做纸面推演：在disk unlink后让`delete_by_file()`抛错，列出HTTP、raw、Chroma、keyword四个状态；不要把推演写成已实现补偿。
14. 把frontend字符串检查改写成一个未来browser test outline：至少包含选择KB、预览、删除确认、list refresh、同名重传与KB-B不变；本轮不执行。
15. 用集合公式手算`65 + 39 - 19`，再列出19个section overlap IDs，解释为什么不能直接把104写成unique coverage。
16. 将report matrix的AC IDs与SPEC union做一次临时exact-set comparison，分别人为删除/添加一个ID，观察missing/extra输出；不要修改仓库文件。
17. 纸面设计一个semantic manifest：每行至少包含`section、AC ID、Given/When/Then hash、evidence command、assertion label、fidelity`。
18. 在不改application的前提下，为F001 rename再设计两个fault points：metadata update失败与read-only verification失败；逐项列期望old/new state。
19. 把browser六场景改写成repository-owned runner outline，明确server lifecycle、51 MiB temp fixture、backend file-count oracle、console log policy与cleanup failure退出码。
20. 比较DOD-01～06、T1204 audit disposition与Phase Gate三者的owner/输入/输出，解释为什么不能用一个PASS复用三种状态。

---

## 13. T1201–T1204 Learning Pass 收口边界

T1201 的broad ingestion harness继续以512维SentenceTransformer double与Qwen-VL response substitution贯通F002–F008；独立REAL BGE probe已关闭模型维度/加载/singleton/基础语义排序问题。live DashScope OCR仍`NOT_AVAILABLE`，因此T1201当前为BLOCKED，不能沿用DONE/PASS。

T1202 的broad retrieval/QA harness继续以512维BGE double与DeepSeek transport substitution覆盖控制流；独立REAL BGE + Chroma probe已关闭受控中文semantic ranking。live DeepSeek回答、grounding、history与prompt-injection仍`NOT_AVAILABLE`，因此T1202当前为BLOCKED，不能沿用DONE/PASS。

T1203 Learning Pass 完成。当前准确表述是：**一份 802 行 isolated file-management/security verification harness 已从真实multipart upload建立raw file与temp Chroma数据，再贯通list、persisted-chunk preview、cascade delete、keyword invalidation/rebuild和same-name re-upload；两个真实KB承担同名隔离对照，SentenceTransformer model为唯一substitution，frontend只做static source wiring check。本轮重跑得到43/43 required checks PASS、temp root清理成功；focused unittest 18/18与完整backend 78/78 PASS。**

T1204原先把substituted provider evidence升级为100% mandatory AC PASS，Gate判定该结论过强。本轮已撤回100%声明并把BGE证据升级为REAL；由于DashScope与DeepSeek literal provider acceptance仍未完成，T1204当前为BLOCKED，Phase Gate保持FAIL。

不得省略的限制是：真实BGE已验证，但这不是大规模质量benchmark；live DashScope OCR、live DeepSeek与真实复杂document/query corpus仍未验证，deterministic answer不能升级为model quality/security证书。T1203仍没有执行absolute/encoded/Unicode/symlink fuzzing或delete mid-cascade compensation，其AC-F016-08 fixture也不是Feature-level AC-F016-02的literal 15-chunk Given。T1204自动守卫count而非AC semantic hash；report traceability与browser assertions仍是Markdown/执行记录，不是machine-readable CI suite。Phase Gate仍FAIL，Phase Learning Review与Phase 12 Engineering Review尚未完成。

本次remediation已获产品授权修改SPEC/TASKS/application assertions/verification baselines与验收报告；没有启动新Phase，没有commit/push，也没有调用DashScope/DeepSeek。
