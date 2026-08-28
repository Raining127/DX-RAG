# Phase 5 — File Upload API 工程评审（Layer 2 · Engineering Review）

> 本文档是 Phase 5 的**累计**工程复盘（按模板 L22：Phase 内增量更新，一个 Phase 一份，不按 Task 新建）。职责：ADR、一致性缺口、Failure Modes、规模分析、Known Gaps——这些内容禁止在 Layer 1 教材全文展开。
> 事实标记：[PROJECT FACT] 仓库可证 / [ENGINEERING KNOWLEDGE] 通用工程知识 / [FUTURE] 未实现能力。

## 0. Review Status

| Field | Value |
|-------|-------|
| **Coverage** | T0501–T0503 |
| **Status** | IN PROGRESS |
| **Completed Tasks** | T0501 ✅（Learning Pass + Engineering Review，2026-08-25）；T0502 ✅（Learning Pass + Engineering Review，2026-08-25）；T0503 ✅（Learning Pass + Engineering Review，2026-08-25） |
| **Pending Tasks** | 流程：Gate Re-review（届时 Status → COMPLETE，Pending #35–#38 在此裁决）；Phase Learning Review（Interview consolidation）已完成 2026-08-26——见面试指南 Phase 5 深度章 |
| **Gate Remediation** | Phase 5 Gate 裁定 PHASE_5_FAIL（AC-F002-01：>5461 chunk 的合法上传被 ChromaDB 单批次上限拒绝）→ 修复 F-1（VectorStore.add_texts 分批持久化）+ F-2（批次失败后按 file_id 补偿删除，file-level all-or-nothing）已完成（2026-08-25）；verify_t0503_rollback.py 的 V9/V10 由 GUARD 升级为 CHECK，脚本全量复跑 PASS；Gate Re-review 待执行 |
| **验证立场** | T0503 落地了端点级验证脚本（backend/scripts/verify_t0503_rollback.py，586 行，V1–V15）并留下**开发期执行痕迹**（`backend/app/api/__pycache__` 时间戳 21:04/21:07 = 应用被 TestClient 导入执行；脚本内 stderr 过滤器为实测产物——ChromaDB 默认嵌入模型下载刷屏催生了它）。脚本最终版（22:17 定稿）的完整执行输出未见——AC-F002-08/09/10 按"脚本覆盖核对 + 开发期执行痕迹 + 用户 TASKS.md DONE 宣告"记录，不虚构最终版全量 PASS；Phase 12 T1203 正式回归仍待执行 |

---

## 1. Phase 定位

Phase 5 是摄取流水线的 **HTTP 入口**：把 Phase 3 已建成的处理管道（解析 → 清洗 → 切分 → 嵌入 → 存储）接到网络上，并保证"上传失败不留垃圾"（SPEC F002 Upload Failure Atomicity）。

与 Phase 4 的分界（面试导引 P4Q12 的原话）：Phase 4 管 **KB 生命周期**（创建场地），Phase 5 管 **文档生命周期**（放进内容）。T0501 是文档生命周期的**第一段**——六道校验闸门，全部发生在写盘之前；T0502 是**后四段**——保存、摄取、失效、响应，并把"失败不留垃圾"（SPEC F002 Upload Failure Atomicity）落到 HTTP 层；T0503 是**验收段**——把 FAILED 的 4 条强制 observable behavior 变成可执行的检查矩阵，交付物是脚本而非产品代码。

---

## 2. 为什么需要这个模块

- **安全**：路径遍历是文件上传的头号风险（SPEC 10.2）。文件名是用户输入，必须按"不可信数据"处理。
- **原子性的前置**：SPEC F002 的 FAILED 回滚是昂贵操作（删文件 + 按 file_id 删 chunk）——六道校验把最便宜、最常见的失败（类型错/太大/重名）挡在昂贵操作之前，让回滚只在"真正开始处理之后"才可能发生。
- **契约隔离**：T0502 的端点编排只需要"校验通过"或"明确错误码"两种结果，不需要知道每一道校验怎么判的——T0502 的实现确认了这个红利：端点对校验层的调用只有一行 `validate_upload(...)`。
- **副作用必须有主人**（T0502）：一旦文件落盘，之后的一切失败都必须有人清理——T0502 的架构问题不再是"要不要校验"，而是"失败了谁删什么"，见 ADR-06。
- **验证为什么单独成 Task**（T0503）：SPEC L463 明言"Rollback / temporary-file 实现机制属于 implementation detail，但以上 observable behavior 是强制约束"——契约在**行为**不在机制，所以 T0503 的形态天然是"验证"而非"实现"（TASKS.md Implementation Scope 原文："implementation work should already be done in T0308 and T0502"）。验证只走 public interface（ADR-09）正是这句 SPEC 的直接延伸。

---

## 3. 核心设计决策（ADR）

### ADR-01: 校验顺序重排 —— 路径安全提到管道最前

- **Decision**: 实现顺序 路径安全 → 扩展名 → 大小 → 空文件 → KB 存在 → 同名；TASKS.md Implementation Scope 编排顺序是 扩展名 → 大小 → 空文件 → 路径 → KB → 同名。
- **Context**: TASKS.md 按 SPEC F002 正常流程 2–6 步排顺序，但 SPEC 10.2 另行要求"路径校验必须在任何文件系统操作之前"，而 F002 正常流程里没有给路径校验排位置。
- **Problem**: 按 TASKS 顺序，路径校验排第 4——前 3 步（扩展名/大小/空文件）会先处理一个未经路径校验的文件名。
- **Chosen Solution**: 把路径校验提到第 1 步，重排理由写进模块 docstring（upload.py:17-19）：后续步骤永不接触未校验路径——防御纵深。
- **Why**: "先于任何文件系统操作"的最强解释 = "管道第 1 步"。虽然 T0501 各步都是纯函数（本模块零 FS 写），但 T0502 复用这个顺序后，路径校验保持第 1，后续即使未来有人在管道中间加写操作，也不会接触未校验路径——顺序本身就是护栏。
- **Trade-off**: 多违规输入的错误码优先级变了——`../bad.exe` 实现报 `INVALID_FILE_NAME`，TASKS 顺序会报 `UNSUPPORTED_FILE_TYPE`。SPEC 错误场景表对"一个输入违反多条规则"未规定优先级。
- **Future Improvement**: 无代码改动需要；**优先级语义留 Phase Gate Review 确认**（Pending #35）。若产品希望"类型错误优先"，只需调整函数调用顺序——这是纯函数管道的结构性优势。

### ADR-02: `PureWindowsPath` 跨平台统一路径判定

- **Decision**: 用 `PureWindowsPath`（而不是随平台的 `Path`）判定上传文件名的路径成分。
- **Context**: SPEC 10.2 路径遍历规则点名 `..`、`/`、`\` 三类危险成分；项目部署平台未定（开发在 Windows，SPEC 11.6 兼容性未限平台）。
- **Problem**: `Path("a\\b.txt")` 在 Linux 上 `.name` 是 `"a\\b.txt"`（`\` 不是分隔符）——反斜杠名在 Linux 校验通过，之后文件若落到 Windows 主机解析成目录路径。校验结果随部署平台漂移。
- **Chosen Solution**: `PureWindowsPath(file_name).name != file_name` 的 basename 等式，Windows 语义在所有平台上恒定；显式特判 `""`/`"."`/`".."`。
- **Why**: 上传文件名是用户发来的字符串，没有"宿主平台"可言；用最严的 Windows 语义判定，一次性覆盖 `/` 和 `\` 两类分隔符，且判定结果平台无关。
- **Trade-off**: 语义即"所有上传名按 Windows 规则判"——若未来产品允许合法的反斜杠文件名（几乎不可能），需改此处。
- **Future Improvement**: 无。此决策与 SPEC 10.2 点名 `\` 的原文完全对齐。

### ADR-03: 同名检查大小写不敏感（SPEC 字面之外的收紧）

- **Decision**: 查重比较 `file_name.lower()` 与既有列表的 `.lower()` 集合。
- **Context**: SPEC F002 步骤 6 / AC-F002-02 写"同名文件已存在"；SPEC 只对**扩展名校验**明文"不区分大小写"，对**同名检查**未明说。
- **Problem**: 项目开发平台 Windows，`uploads/` 位于大小写不敏感文件系统——若查重精确匹配，`Doc.pdf` 会通过查重，随后 T0502 保存时**覆盖**已存在的 `doc.pdf`（文件系统层撞车）。查重语义与文件系统行为脱节。
- **Chosen Solution**: 查重按小写化比较（upload.py:128-134，理由写在注释里）。
- **Why**: 查重的目的是防覆盖；覆盖是否发生由文件系统大小写语义决定——查重必须与它对齐，而不是与 SPEC 的示例字面（示例恰好都是小写）对齐。
- **Trade-off**: 比 SPEC 字面更严——产品若想在同一 KB 存 `Doc.pdf` + `doc.pdf` 两个文件（大小写敏感语义），当前实现会 409。这是实现层的合理收紧，但**产品语义确认留 Gate Review**（Pending #36）。
- **Future Improvement**: 若产品确认需要大小写敏感并存，则存储路径需同步改造（大小写敏感目录语义不是所有文件系统都有）——成本高于收益，预计不会发生。

### ADR-04: 查重数据源 = `get_files()` 派生聚合（不扫文件系统）

- **Decision**: 同名检查用 VectorStore `get_files(collection)`（chunk metadata 按 file_id 聚合），不查 `uploads/{kb}/` 目录。
- **Context**: v1 零元数据库（SPEC 7.3）——"该 KB 有哪些文件"的唯一权威来源是 chunk metadata；`get_files` 是 Phase 1 T0107 就建好的聚合原语，Phase 4 的 file_count 已经消费过它。
- **Problem**: 备选方案扫目录——会引入第二个"文件列表"来源，两个来源必然漂移（例如 FAILED 回滚删了目录里的文件但 ChromaDB 里有 chunk 的中间窗口）；且 uploads 目录里的残留文件（Phase 4 Finding #2 的孤儿目录、T0308 的崩溃窗口）会让查重误拒。
- **Chosen Solution**: 只信 chunk metadata。
- **Why**: 单一权威来源消除漂移；更重要的是**[PROJECT FACT] 摄取 FAILED 的文件没有 chunk → 不出现在列表 → 同名重传天然不被阻塞**——SPEC F002 "FAILED observable behavior" 第 4 条（再次上传同名文件不得被上一次失败阻塞）在查重环节**零代码兑现**，不需要"失败文件白名单"之类的特殊逻辑。这是回滚设计与查重设计的正确性互相咬合的例子。
- **Trade-off**: 每次上传 O(该 KB 全部 chunks) 聚合——单机小 KB 规模完全可接受；规模代价见第 6 节。
- **Future Improvement**: 100x 规模 → 查重索引化 / 独立元数据库（SPEC 7.3 已预见）。

### ADR-05: 纯校验模块无 router —— Task 边界设计

- **Decision**: T0501 交付"无 router 的纯函数校验模块"，端点由 T0502 接线。
- **Context**: TASKS 把上传拆成 T0501（校验）/ T0502（端点编排）/ T0503（回滚验证）三个 Task；router.py 已预留注册位（router.py:16-19）。
- **Problem**: 若 T0501 顺手建了端点，端点必然要处理"校验通过后干什么"——即 T0502 的保存/ingest 逻辑，Task 边界失守。
- **Chosen Solution**: 模块 docstring 第一段点名范围（端点/保存/ingest/失效全部归 T0502），函数签名面向 T0502 的复用（`validate_upload` 返回解析后的 collection 名）。
- **Why**: 校验层与端点层的分离带来三个红利：① T0502 复用零成本；② 校验函数可独立单测（无 HTTP/ChromaDB 写依赖）；③ "被拒请求零副作用"从调用纪律升级为**结构事实**——这个模块根本没有写 API。
- **Trade-off**: 无 router 意味着 T0501 无法做端点级实测（AC-SEC 的触发方式尚不存在）——验证 DEFER 至 T0502，这是拆分的已知代价。
- **Future Improvement**: T0502 接线后补端点级实测。（已兑现：T0502 在同一模块接线，复用零成本——本 ADR 的复用红利验证完毕。实测仍未执行，见 §7 Gap-1。）

### ADR-06: 失败清理责任二分 —— FAILED 归服务层、异常归端点

- **Decision**: FAILED 状态的清理（删 raw file + `delete_by_file`）归 `IngestService._fail`（T0308 已有），端点只把 FAILED 映射成 422 `FILE_PARSE_ERROR`；异常路径的 raw file 清理归端点的 `_discard_saved_file`，清理后原样重抛。
- **Context**: SPEC F002 Upload Failure Atomicity 要求失败后"uploads/ 不残留文件、ChromaDB 不残留 chunk"。实现时发现失败有两条形态：**优雅的 FAILED**（`IngestService.process` 返回状态，如全文解析后为空）与**抛异常**（损坏文件 FILE_PARSE_ERROR、加密 PDF ENCRYPTED_PDF、OCR/embedding 致命错误）。
- **Problem**: 若端点统一清理两条路径，FAILED 路径会**重复删除**（IngestService 已删）——虽然 `missing_ok=True` 使其无害，但语义错误且违反责任单一；若全部推给 IngestService，异常路径它又没机会执行（raise 发生在它的 return 之前，且它自己没有 try/except 编排）。
- **Chosen Solution**: 按**副作用归属**切分——谁写入谁回滚：ChromaDB 写和 file_id 都属于 IngestService，FAILED 的完整回滚它自己做完；`save` 是端点引入的副作用，异常时端点负责撤销自己的这一步（docstring 原话："the save is this layer's side effect, so undoing it is this layer's duty"）。
- **Why**: ① 每个清理者只清理自己产生且自己**可见**的东西——异常路径上 file_id 在 `IngestService.process` 内部生成、异常时对端点不可见，端点清不了 ChromaDB（这是结构事实，不是偷懒）；② 不重复清理；③ 两层职责在双方 docstring 里各自声明（upload.py:171-177 与 ingest.py:552 互相点名），契约可读。
- **Trade-off**: 责任分散在两层——若 IngestService 的 FAILED 语义将来改变（例如不再删文件），端点会静默泄漏文件。两层契约靠 docstring 咬合，没有编译器保证。
- **Future Improvement**: 若异常路径也要全量回滚（包括 ChromaDB 半写残留），需要 IngestService 自己包 try/except（它知道 file_id）——见 Gap-4。

### ADR-07: keyword index 只在 200 结果之后失效

- **Decision**: `invalidate_keyword_index(collection)` 放在 FAILED 检查**之后**、return 之前——只有 SUCCESS / SUCCESS_WITH_WARNINGS 才触发失效。
- **Context**: F002 步骤 9 要求"keyword index 失效"；keyword seam（Phase 4 T0402 建立）当前是 no-op，真实 dirty-flag 行为属于 T0602。
- **Problem**: 若无条件失效（失败也失效），FAILED 路径多一次无意义操作；更深层的问题是**语义错误**——失效表示"索引内容已过期"，而失败的上传没有写入任何 chunk，索引内容根本没变。
- **Chosen Solution**: 失效只发生在内容真的变了的路径上。推理链：失败上传 → 零 chunk 写入 → 索引内容不变 → 索引天然正确 → 无需失效。这是"失败零副作用"推理链的第三环（前两环：校验零写、FAILED 回滚）。
- **Why**: 失效调用位置本身就是文档——它声明了"只有成功才改变索引内容"这一不变量。T0602 落地真实 dirty-flag 后无需再改这个位置。
- **Trade-off**: 依赖"失败必零 chunk"的推理——若未来出现"部分写入"的失败形态（如 add_texts 半写，见 Gap-4），此推理链断，索引可能滞后于半写数据。
- **Future Improvement**: 无（T0602 只替换 seam 本体，不改调用位置）。**已兑现（2026-08-27）**：T0602 把 seam 本体替换为 `KeywordRetriever.invalidate()` 委托（in-memory dirty 标脏），调用位置零改动。

### ADR-08: `collection_name` 不做独立路径校验 —— 传递保证

- **Decision**: 保存路径 `uploads/{collection}/{file_name}` 中，`file_name` 过六道校验，`collection` **不**再过路径校验——它的安全性由"KB 存在性检查 + Phase 4 命名正则"传递保证。
- **Context**: SPEC 10.2 的路径遍历规则只点名 file_name；T0502 需要把 collection 拼进路径。
- **Problem**: `uploads/{collection}/` 的 `mkdir` 在 KB 存在性检查**之后**执行——collection 名能通过检查，说明它存在于 ChromaDB；而 v1 里 ChromaDB collection 的唯一创建入口是 Phase 4 的 `POST /api/collections`，其命名正则（3-50 字符、字母数字开头结尾）不含 `/`、`\`。默认值 `CHROMA_COLLECTION = "knowledge_chunks"` 同样安全。
- **Chosen Solution**: 信任链显式化：上游校验 → ChromaDB 存储 → 下游路径拼接。不重复校验。
- **Why**: 信任链每一环在各自 Phase 都有验证记录（T0404 的 74/74 边界用例验收覆盖正则）；重复校验会制造"双源真理"——如果两个校验规则哪天不一致（如正则改了但路径校验没改），会引入新的不一致面。
- **Trade-off**: 传递保证是**全局性质**——未来若出现别的 ChromaDB 写入入口（如 T0601 的关键词索引？不会；但任何直写 ChromaDB 的工具/脚本）绕过命名正则，此保证失效且无本地告警。信任链必须写清楚（本 ADR 即为此存在）。
- **Future Improvement**: 若产品要求 KB 名支持任意字符（几乎不可能，Phase 4 正则即产品决策），此处需补独立校验。

### ADR-09: 验证只走 public interface —— 断言与实现解耦（T0503）

- **Decision**: FAILED 回滚的 4 条强制行为全部通过 public interface 断言——`get_files()`、`get_chunk_count()`、文件系统目录，外加 HTTP 响应；不碰 ChromaDB 私有属性、不读 chroma_db 内部文件。
- **Context**: SPEC L463 把 rollback 机制声明为 implementation detail；SPEC F002 的 4 条强制行为（L457-461）却全部是**可观察行为**——契约在行为不在机制。
- **Problem**: 若断言依赖实现细节（如直查 `_collection`、读 ChromaDB 的 sqlite 文件），验证脚本就和"今天这版实现"焊死——任何回滚机制的重构（临时文件 + 原子 rename、批处理改造）都会砸碎测试，哪怕行为完全正确。
- **Chosen Solution**: 行为 2（ChromaDB 无残留）用**代理观察**断言：chunk_count 等于基线 + `get_files` 不含该文件——任何带失败 file_id 的残留 chunk 都会抬高计数、把文件重新暴露出来（脚本 docstring 的推理链）。行为 3（keyword index 无该文件）复用同一观察——Phase 6 索引从 `list_chunks` 全量重建，文件不在 store 就进不了索引。
- **Why**: 验证与实现解耦——验证锁住的是 SPEC 的契约（observable behavior），不是今天的代码形态。这也让"验证"本身有资格成为 T1203 的验收底座：实现可以变，验收不跟着变。
- **Trade-off**: 断言粒度粗于内部状态——"chunk 数不变"在极端巧合下可能掩盖"残留一批又恰好删掉等量另一批"的故障（现实中不存在这样的代码路径，且 `get_files` 检查提供了第二重确认）。
- **Future Improvement**: 若未来需要更强的残留检测，可补一条"`get_chunks_by_file(file_id)` 返回空"的断言——但仍不越过 public interface。

### ADR-10: 子进程隔离 —— 两个"进程级状态"陷阱的一个套壳解法（T0503）

- **Decision**: 整个验证矩阵跑在**子进程**里（`main()` 父进程 `subprocess.run` 自身 + `--probe-root` 参数切换模式），临时目录由父进程在子进程退出后清理；`UPLOAD_DIR`/`CHROMA_PERSIST_DIR` 的环境变量重定向发生在**任何 app import 之前**。
- **Context**: 验证需要：① ChromaDB 数据与 uploads 目录重定向到一次性临时目录；② 跑完清干净（真实 `chroma_db/`/`uploads/` 零污染）。
- **Problem**: 两个独立的"进程级状态"陷阱：**(a)** ChromaDB 的 Rust 后端把 SQLite/segment 文件句柄持有到进程结束——Windows 上 in-process 清缓存也不释放句柄，父进程无法 `rmtree` 临时目录；**(b)** Settings 是 Pydantic BaseSettings 单例，`UPLOAD_DIR` 在 **import 那一刻**从环境变量读定——先 import 再改 env 无效。
- **Chosen Solution**: 一个套壳同时解决两个问题：矩阵在子进程里跑（子进程退出 = OS 收回全部句柄 → 父进程可清理）；子进程内**先设 env、后 import**（所有 `app.*` import 都住在 `run_probe` 函数体内）——单例的初始化时机就是环境变量的注入时机。
- **Why**: 不修改任何产品代码（配置不动、ChromaDB 不动），隔离是脚本层的结构性保证而非纪律——repo 路径防呆断言（脚本 L226-228：拒绝 `UPLOAD_DIR` 落在仓库内的运行）再补一道保险。
- **Trade-off**: 每次运行多一个解释器进程（~秒级启动）+ 父进程转发输出（需处理 Windows 控制台编码、过滤 ChromaDB 模型下载刷屏）。子进程参数协议（`--probe-root`）是一点自引用的复杂度。
- **Future Improvement**: T1203 若固化此脚本为回归套件，子进程隔离模式可直接沿用（或换成 pytest 的 tmp_path fixture——它天然提供同样的句柄/清理隔离）。

### ADR-11: 声明替代与 GUARD 分离 —— 验证不越界（T0503）

- **Decision**: 两件事合起来是一条原则——**验证脚本的边界**：(a) 环境缺依赖（PyMuPDF / sentence-transformers / dashscope）时用**声明替代**（D-1：空白 .txt 替代"无有效文本 PDF"；D-2：embedding stub + F004 warning 通道注入替代真实 OCR 失败），替代品与字面 fixture 在**相同代码分支**汇合，保真度靠论证写进 docstring；(b) 不可达状态（Chroma 批次上限、半写、失效异常、清理异常）的探针记 GUARD（D-4）——**只报告、不强制、不修复**。
- **Context**: T0503 的验收对象是 T0308/T0502 的回滚行为，不是嵌入质量、不是 ChromaDB 的批次策略、不是 keyword seam。
- **Problem**: 若不声明替代，验证会被环境阻塞（等 PyMuPDF 装好才能跑 AC-F002-08）；若 GUARD 发现当 FAIL 处理，验证任务会"替别人失败"——F-1（owner T0104）、F-3（owner T0602）都不是 T0503 能修或该修的。
- **Chosen Solution**: 替代品的选择标准 = **失败分支等价**：空白 txt 与"所有页面无有效文本的 PDF"都在"清洗后文本为空 → `_fail`"处汇合，验证的是汇合点之后的全部行为；GUARD 与 CHECK 在输出层分离（`[GUARD]`/`[PASS]`/`[FAIL]` 标记 + 汇总只统计 CHECK），问题 owner 写进每一条 GUARD 明细。
- **Why**: 验证任务的产出是**关于验收对象的结论**（回滚对不对），不是"环境装没装好"、不是"别的模块有没有毛病"——替代与 GUARD 两条规则共同保证结论不被无关因素污染。零业务代码修复的结果也由此可信：15 个场景里所有 FAIL 都是注入故障触发的，没有一个是产品代码缺陷。
- **Trade-off**: 替代保真度靠论证而非实现——空白 txt 不验证"PDF 解析器对无文本页面的行为"（那是 Phase 3 的验收范围）；GUARD 靠人工阅读消化，没有机器强制。
- **Future Improvement**: 环境补齐后（PyMuPDF 装上）可把 D-1 升级为字面 fixture；GUARD 项在 owner Task 落地后（T0104 批处理 / T0602 真实索引）可升级为 CHECK。**已部分兑现（2026-08-25）**：Phase 5 Gate 修复 F-1/F-2 后，V9（F-1）/V10（F-2）由 GUARD 升级为 CHECK；V11（F-3）/F-4 仍为 GUARD，owner 未变（T0602 / 全局 handler）。**F-3 owner T0602 已于 2026-08-27 落地**（invalidate 兑现为 in-memory 标脏、无失败路径，V11 观察的"提交后失效异常"形态在 in-memory 实现下不可达）；V11 升级 CHECK 仍待验证脚本复跑。

---

## 4. 架构影响

- **API Layer 的第一个无 router 模块 → 第一个"校验 + 端点同模块"**：T0501 时 upload.py 确立了"纯函数模块也可以住在 api 包"的先例；T0502 在**同一文件**接线（`APIRouter` + 端点，router.py:16 注册）——api 包从此支持"纯逻辑 + 端点混合"的单文件形态（一个端点的完整故事 230 行）。
- **零新依赖**：未引入任何第三方库（`PureWindowsPath` 来自标准库 pathlib；`UploadFile`/`File`/`Form` 来自已装好的 FastAPI）——SPEC 依赖纪律的延续。
- **契约消费**：只走 VectorStore public interface（`list_collections` / `get_files` / `add_texts` / `delete_by_file`，后两者经 IngestService），F008 边界在 Phase 5 继续成立；keyword seam 按 T0402 契约调用（no-op 现状合法，真实行为 DEFER T0602）。
- **副作用归属原则的第二次兑现**：Phase 4 rename 的"两层补偿"（ADR-06）把清理责任按副作用归属分层；Phase 5 上传把它推广到"两条失败路径 × 两个责任方"（ADR-06）——两个 Phase 各自独立得出同一原则，说明它是本代码库的隐性架构主线。
- **与既有模式的呼应**：Validation Before Side Effects（Phase 4）→ 校验段"结构级零副作用"；派生聚合（Phase 4 file_count）→ 查重数据源；传递保证（Phase 4 命名正则）→ collection_name 路径安全。Phase 5 是 Phase 4 原则在文档生命周期的第二次兑现。
- **T0503：scripts/ 目录诞生**——项目第一份验证脚本，也是**第一份"验证即交付物"的 Task**（此前验证全靠代码审查）。它的三个架构原则（public interface only / 子进程隔离 / GUARD 分离）成为后续验证类 Task（T1201/T1203）的候选模板。
- **T0503：零业务代码改动是架构证据**——T0308 的 `_fail` + T0502 的 `_discard_saved_file` 在 15 个端点级场景下无需任何修补，"副作用归属"（ADR-06）经受住了第一次实证而非被推翻；脚本通过 `patched()` 注入故障，产品代码无需为可测性加钩子。

---

## 5. 工程问题分析

### 5.1 可维护性

- 4 个函数职责单一，每个只 raise 一个（或两个互斥的）错误码——错误码 → 函数 的映射可背诵，无组合爆炸。
- 白名单是模块级 set 常量（upload.py:49-62）——格式支持变化只改一张表。
- docstring 密度高：模块 docstring 承担"范围声明 + 顺序契约 + 重排论证 + 副作用声明"四件事——设计意图与代码同址，不会漂移。
- **T0502**：端点函数 57 行，可读性靠**四个清晰的段落**（验证 → 保存 → 失败处理 → 响应）与段内注释；`_STATUS_MESSAGES` 文案表把"SPEC 示例 JSON 的文案"数据化，文案变更零逻辑改动。模块 docstring 随职责演进改写（范围声明 → 流程全景），docstring 与代码同步演进是本模块可维护性的一个证据。
- **T0503**：脚本 586 行单文件，可维护性靠**原语化**——`case`（开场景+拍基线）/ `check`/`ac`/`guard`/`post`/`observe`/`assert_rolled_back`/`patched` 八个 helper 把"场景 = 数据 + 断言序列"的骨架立起来，每个场景 5-15 行即可读；场景是**线性序列**而非数据驱动循环——14 个场景各写各的（注入方式各不相同，数据驱动反而要做元编程）。docstring 承担 D-1/D-2/D-4 决策记录——决策与实现同址。

### 5.2 扩展性

- 新增校验规则 = 新函数 + `validate_upload` 里加一行——管道是显式的函数调用序列，扩展点清晰。
- 未来若校验规则需要可配置（如按 KB 定制白名单），当前硬编码 set 需要改造——v1 不需要，产品无此要求。
- **T0502**：端点流程步骤（保存/ingest/失效/响应）各自一行调用，新增"上传后处理"步骤（如病毒扫描、内容审核）插入点清晰；但 F002 的 10 步序列是**固定编排**——未来若出现"保存后校验"（如 magic-byte 拒绝已落盘文件），需在保存段与摄取段之间插入新错误路径，此时清理责任二分（ADR-06）需要重新审视。
- **T0503**：新场景 = `case()` + 注入 + 断言（一个 block 的成本）；新发现 = `guard()` 一行。两个升级路径已预埋：环境补齐后 D-1 升级为字面 PDF fixture（脚本零结构改动）；GUARD 项在 owner Task（T0104/T0602）落地后升级为 CHECK。

### 5.3 数据一致性

- 查重与文件系统的唯一交汇点在 T0502（保存到 `uploads/{kb}/{file_name}`）——T0501 阶段无一致性风险（零写入）。
- **T0502 预检结论（兑现上轮承诺）**：T0502 的保存是 `write_bytes` 的**静默覆盖**语义，未采用"幂等/明确失败"的排他创建（`'x'` 模式）——TOCTOU 窗口确认存在，在"单用户本地部署 + 查重前置"假设下接受，见 Gap-3（含修复方案）。**好消息**：即使窗口被击中（校验后、保存前出现同名文件），被覆盖的是旧 raw file、新内容以新 file_id 入库，旧 file_id 的 chunks 仍可检索——失败形态是"两个 file_id 共享一个文件名"，不是数据丢失（T0503 验证场景如观察到需记录）。
- **T0502 新增**：清理责任二分（ADR-06）本身就是一致性设计——两个清理者的职责范围是**互斥且完备**的（FAILED=服务层全清 / 异常=端点清文件），唯一的灰色地带是 add_texts 半写（Gap-4）。
- **T0503**：脚本对一致性做了两个观察——V11 检查"raw 文件与 get_files 暴露性**互相一致**"（提交后失效异常不制造 raw/Chroma 分裂状态）；V12 验证**清理失败时的一致性优先级**：`Path.unlink` 被强制失败后，残留 raw file + 零 chunk（文件孤儿但无幽灵数据）——不一致发生了，但方向正确（宁可残留文件不可残留数据）。[ENGINEERING KNOWLEDGE] 一致性设计的终局问题：**失败时哪个方向的不一致可接受**。

### 5.4 错误处理

- 6 个 AppError 全部 Phase 0 就位，零新增错误码——错误目录的前瞻性再次兑现。
- 无 try/except：校验管道不需要捕获任何东西，因为没有副作用需要清理——这是"校验前置"设计在错误处理上的直接红利（对照 Phase 4 rename 的 7 步补偿编排）。
- **T0502**：端点的 `try` 作用域只包 `IngestService.process` 一步——最小作用域，其余代码的错误不会被误当摄取失败清理；`except Exception` 是**裸 except 的合法用例**（任何失败 → 清理 → 原样重抛，无需分辨失败形态）；`_discard_saved_file` 自身"永不 raise"（`except OSError: logger.exception` 不重抛）——清理失败不掩盖正在重抛的主错误，残余路径留日志证据。FAILED 的 `raise` 放在 try **外**，从控制流上杜绝"FAILED 时端点删一个已被服务层删过的文件"的语义错误（虽然 `missing_ok=True` 使其无害）。
- **错误码 → HTTP 的全链路**：校验段 6 码（400/404/409/413）→ 摄取段映射 FAILED → 422 `FILE_PARSE_ERROR` → 全局 handler 统一信封——T0502 兑现了 SPEC 6.3 Error Responses 表的**完整**映射（7 行表全部可达）。
- **T0503**：`TestClient(app, raise_server_exceptions=False)` 让 SPEC 9.4 全局 handler 的 500 响应**作为响应被观察**（V7/V8 断言 500 + error.code），而不是让异常穿透进脚本——验证的对象是"错误经全局 handler 后的 HTTP 形态"，这正是契约的形态。V12 补上错误处理的最后一个设计点：**清理失败不掩盖主错误**（`_discard_saved_file` 吞 OSError 的行为被实证）。V15 则发现一个错误处理缺口：请求级校验 422（缺 file 部分）返回 FastAPI 默认信封 `{"detail": [...]}`，与 SPEC 6.7 "All error responses follow this structure" 矛盾——GUARD F-4，owner 全局 handler（Pending #38）。

### 5.5 性能

- `get_files` 聚合是唯一 O(全 KB chunks) 的操作（每次上传跑一次）——与 Phase 4 file_count 同源的成本结构，见第 6 节规模分析。
- 其余五道校验 O(1)/O(文件名长度)——成本可忽略。
- **T0502**：端点为**同步 `def`**——FastAPI 把它跑在线程池，CPU 密集的 embedding（`encode_chunks`）不阻塞事件循环，其他请求（如 /health）不受单个大上传影响。这是 FastAPI 的默认行为，不是本代码库的决策——但**选 sync def 而非 async def 在这里是对的**（embedding 是阻塞调用，写 async 反而错）。[ENGINEERING KNOWLEDGE]
- **T0502**：`file.file.read()` 在校验之前整读——413 之前要收完全量上传（Starlette SpooledTemporaryFile 超 1MB 滚到磁盘：内存有界、带宽无界）。SPEC 只约束"校验先于写入"，读入内存不在其列——单用户部署接受，见第 6 节。
- **T0503**：验证成本 = 子进程解释器启动（~秒级）+ ChromaDB 冷启动（含默认嵌入模型下载尝试——脚本 stderr 过滤器就是为滤掉它的进度刷屏而生）+ 15 场景顺序执行；总时长被 `timeout=900`（15 分钟）兜底——对一次性验证任务可接受，若 T1203 固化为回归套件需按 pytest 惯例拆分。

### 5.6 安全

- **三层防御**：① 名称安全（Windows 语义 + basename 等式）→ ② KB 存在性（404 挡住不存在的目标）→ ③ 防御纵深（顺序护栏：管道内任何未来新增步骤都不接触未校验路径）。
- **拒绝而非改写**（SPEC 10.2 明文禁止 sanitization）——安全校验不创造数据。
- 剩余风险：扩展名可伪造（`.exe` 改名 `.pdf`）——SPEC 已把 magic-byte 列为 Future consideration，v1 接受此风险（10.2）。
- **T0502**：保存路径的两段各有安全来源——`file_name` 过六道校验（直接校验），`collection` 靠传递保证（ADR-08，信任链已显式化）；`file.file.read()` 的内容**以字节原样落盘**，内容本身不参与任何路径/命令构造（v1 无 shell 调用）。上传内容在 ChromaDB 检索时才会被"当作数据"——那时它已是 Phase 3 清洗管道的输出。
- **T0503**：脚本自身的安全设计——repo 路径防呆断言（L226-228：`UPLOAD_DIR`/`CHROMA_PERSIST_DIR` 落在仓库内则拒绝运行，防"验证脚本误伤真实数据"）；临时目录一次性（`mkdtemp` + 父进程 rmtree 重试）；V1/V2 顺带复验了路径遍历/类型/大小/空文件拒绝——**安全 AC（AC-SEC-01）的端点级实测第一次落地**。

---

## 6. 规模扩大分析

| 规模 | 场景 | 影响 | 状态 |
|------|------|------|------|
| 10×（数百文件/KB） | 每次上传跑 `get_files` 全量聚合 | 查重延迟线性增长，单机可接受（毫秒级） | 当前实现足够 |
| 100×（万级 chunks） | 聚合扫描 + 全量读 metadata | 每次上传秒级查重——成为吞吐瓶颈；与 Phase 4 file_count 同源问题合并治理 | [FUTURE] 查重索引化 / 独立元数据库（SPEC 7.3 已预见）；规模治理挂 T1201 |
| 1000×（多机/海量） | 单机 ChromaDB + 本地文件系统 | 上传服务需独立部署；uploads 目录需对象存储 | [FUTURE] SPEC 明确保留的扩展点（Milvus / 元数据库）；Not implemented in v1 |

**T0502 增量**：

- **嵌入主导单请求成本**：一次上传 = 六道校验（O(1)~O(KB 文件数)）+ 全量嵌入（CPU 密集，随文件大小线性）+ ChromaDB 批量写。同步端点跑线程池，CPU 消耗不阻塞事件循环但**占满线程池**——并发上传数 × 嵌入时长决定吞吐；v1 单用户无所谓，100× 并发场景需独立上传队列。
- **整读先于 413**：超限上传也要全量收完才被拒——带宽/磁盘 spool 成本与文件大小成正比，与"拒绝得快"无关。10× 无感；100× 上传入口需前置 Content-Length / 流式限额（v1 out of scope）。

**核心判断**：T0501 的正确性不随规模退化（校验逻辑 O(1)），只有查重一步随规模线性变慢——它是 Phase 4 file_count 的成本结构的第二次出现，治理时机与 file_count 同步（100× 内先动"现场聚合"）。T0502 的成本形态是"单请求重（嵌入）+ 并发窄（线程池）"——规模瓶颈在嵌入服务而非端点编排。

**T0503 增量**：验证矩阵的成本 = 子进程启动 + ChromaDB 冷启 + 15 场景线性执行——与产品规模无关（固定开销），但**场景数量**会随"失败形态清单"线性增长（每发现一种新失败形态 +1 场景）。V9 的 ~7MB fixture 已暴露出"合法输入也可能触发的规模边界"（F-1：Chroma max batch）——规模问题的**验证入口**是 GUARD 而非产品代码，这是 T0503 给 Phase 12 规模验收留下的探针。10×/100× 下验证脚本无需变化；1000× 下"一次性脚本 vs 回归套件"的分野由 T1203 决定。

---

## 7. Known Gaps & Pending Questions

### 7.1 Known Gaps（已知缺口）

- **Gap-1: 无已执行的端点级实测**——**已填补（T0503）**。T0503 验证脚本（backend/scripts/verify_t0503_rollback.py，586 行，V1–V15）覆盖：V6 加密 PDF / V7 嵌入失败 / V8 Chroma 持久化失败 / V12 清理失败不掩盖主错误（正是本评审 5.6 节的设计点）/ V13-V14 成功对照组 / V1-V2 安全 AC 复验 / V15 请求级校验。**执行证据**：开发期 `__pycache__` 时间戳（21:04/21:07）证明应用被 TestClient 导入执行；脚本内 stderr 过滤器（onnx.tar.gz 刷屏过滤）是实测产物。**剩余部分**：最终版（22:17 定稿）的完整执行输出未见——不虚构全量 PASS；Phase 12 T1203 正式回归仍待执行。Gap-1 从"完全空白"降级为"部分证据"。
- **Gap-2: 无自动化测试脚本**——延续 Phase 4 Finding #4：仓库仍无 tests 目录；T0503 的 verify_t0503_rollback.py 是第一份**已完成**的验证脚本，但形态是"一次性脚本"（无 fixture 文件、无断言框架、靠 exit code 汇报）而非可回归的测试套件——六道校验的边界用例（T0404 式的用例矩阵）仍未固化。Phase 12 T1203 是否将其固化为正式验收（或转 pytest）仍待定。
- **Gap-3: TOCTOU 窗口（T0502 预检结论，兑现 5.3 节承诺）**——保存用 `write_bytes` 静默覆盖语义，未采用排他创建。窗口（校验通过 → 保存前出现同名文件）在**单用户本地部署**假设下接受。**修复方案**（如多用户部署）：`open(path, "x")` 排他创建 + `FileExistsError` → 409，或临时文件名 + `os.replace` 原子落盘。**窗口被击中的失败形态**：旧 raw file 被覆盖、新内容以新 file_id 入库、旧 file_id 的 chunks 仍在 ChromaDB（两个 file_id 共享一个文件名）——可检索但不一致。**T0503 未观察到该形态**（V13/V14 成功对照均为单请求顺序执行，无并发窗口——与预期一致，本 Gap 维持"单用户假设下接受"）。
- **Gap-4: 异常路径不清 ChromaDB 半写残留**——端点的异常清理只删 raw file；若 `store.add_texts` 在批量写入中途失败（如大文件多批次写入），已写入批次的 chunks 可能残留，而 file_id 在异常时对端点不可见（`IngestService.process` 内部生成），**结构上**无法按 file_id 清理。概率低（parse/clean/chunk/embed 的失败都发生在 add_texts 之前，零写入；只有 add_texts 自身中途失败才触发）；且残留 chunks 与已删 raw file 的组合是"幽灵文件"形态（get_files 可见、内容可检索）。[ENGINEERING KNOWLEDGE] 完整修复需 IngestService 自包 try/except 在异常路径也执行 `delete_by_file`（它知道 file_id）——这是 ADR-06 的已知边界。**T0503 观察结果**：V10 场景（`_partial_add`：批次 1 提交后批次 2 抛错）以 GUARD F-2 记录了孤儿 chunks 与同名重传锁定——本 Gap 从"推演"升级为"实证观察（开发期执行）"，结构性修复方案不变（owner 无变化：仍非端点所能及）。
- **✅ REMEDIATED（2026-08-25，Phase 5 Gate 修复 F-2）**：补偿责任落在 `ChromaVectorStore.add_texts` 自身（预检方案"IngestService 自包 try/except"的替代实现）——它同时看得见批次边界与 file_id（来自本调用 metadatas），任一批次失败即以 `delete_by_file` 删除本调用全部 file_id 的 chunk 后原样重抛。比预检方案更优：① 无需 IngestService 重排（零编排层改动）；② 补偿者是写入者自身（ADR-06"谁写入谁回滚"）；③ file_id 不必跨层传回。清理失败按 `_restore_rename` 惯例 best-effort 记录日志、不掩盖主错误。实测：V10 升级为 CHECK（注入真实批处理循环的第 2 批失败），孤儿 chunks 归零、同名重传不阻塞、无关文件/KB 无损。

- **Gap-5: ChromaDB 单批次上限对合法大文件的风险（T0503 脚本 GUARD F-1 观察）**——T0503 脚本 V9 场景观察：合法大小（~7MB < 50MB）但切分后 chunk 数超过 Chroma max batch 的文件，在 `add_texts` 持久化阶段被拒（owner: T0104 VectorStore.add_texts 的批处理策略）；V9 同时验证了"批次失败后回滚 + 同名重传不阻塞"——回滚行为本身正确。与 Gap-4 同源——都是"add_texts 半途失败"的变体，但触发条件是**合法输入**而非故障。脚本以 GUARD（信息性）记录，不作为 T0503 必过项；治理时机挂 T0104 批处理改造或 Phase 12 规模验收。
- **✅ REMEDIATED（2026-08-25，Phase 5 Gate 修复 F-1）**：`ChromaVectorStore.add_texts` 改为按客户端公开 API `get_max_batch_size()`（1.5.9 = 5461）顺序分批写入，`getattr` 缺省回退常量 5461（覆盖 `chromadb>=0.4.15` 旧版本无该方法的场景）。纯传输层细节：无用户可见 chunk 数上限、50MB 上限不变、API 契约/错误码/SPEC 零改动。实测：V9 升级为 CHECK——6000 chunk 合法上传（7.22MB）返回 200 SUCCESS、6000/6000 全量持久化、raw 文件保留、get_files 完整暴露、同名重传 409。

- **Gap-6: 请求级校验错误不走 SPEC 6.7 信封（T0503 脚本 GUARD F-4 新发现）**——V15 场景观察：缺 file 部分的请求返回 422，但响应体是 FastAPI 默认的 `{"detail": [...]}`，而非 SPEC 6.7 的统一信封 `{error: {code, message, details}}`。全局 handler 只接管 AppError（SPEC 9.4），FastAPI 的 RequestValidationError 走框架默认 handler——SPEC 6.7 说"All error responses follow this structure"，框架级校验错误绕过了它。影响面是所有端点的请求级 422（不止 upload）。owner: 全局 handler（T0004）。裁决留 Gate Review（Pending #38）：接受框架默认（SPEC 补例外说明）或注册 RequestValidationError handler 映射到统一信封。

### 7.2 Pending Questions（延续既有编号：Phase 3 起 #1–27，Phase 4 续 #28–34）

- **Pending #35 — 多违规输入的校验优先级未由 SPEC 规定**：`../bad.exe` 实现报 INVALID_FILE_NAME（路径优先），TASKS 顺序会报 UNSUPPORTED_FILE_TYPE。SPEC 错误场景表只定义单违规输入。**Gate Review 确认**：当前优先级（安全优先）是否可接受，或需在 SPEC 补一句优先级规则。
- **Pending #36 — 查重大小写不敏感的产品语义**：SPEC F002 字面"同名"，实现收紧为大小写不敏感（ADR-03）。若产品想要 `Doc.pdf` + `doc.pdf` 并存（几乎不可能，但语义要明确），当前实现会误拒。**Gate Review 确认**：接受实现的收紧，或 SPEC 补"同名检查不区分大小写"一句。
- **Pending #37 — FAILED→422 是否透出 warnings（跨 Phase AC 口径）**：SPEC AC-F004-04（Phase 3）Then 写明"API 返回 422 FILE_PARSE_ERROR，warnings 包含 3 条记录"——T0502 的映射 `raise AppError("FILE_PARSE_ERROR")` 未带 `details`，`result["warnings"]` 被丢弃。项目已有先例（ingest.py:108 `details={"encoding_attempts"}`），修复只需 `details={"warnings": result["warnings"]}` 一行——但 AC 归属 Phase 3（T0305/T0308 已 DONE）、消费在 Phase 5，跨 Phase 口径问题按 Freeze Policy 不擅自决定。**Gate Review 确认**：错误响应是否需要在 details 透出 warnings，若是则补一行实现。
- **Pending #38 — 请求级校验 422 的信封归属（T0503 GUARD F-4 新发现）**：FastAPI RequestValidationError（缺 file 部分、form 字段类型错误）返回框架默认信封 `{"detail": [...]}`，与 SPEC 6.7 "All error responses follow this structure" 矛盾——全局 handler（SPEC 9.4）只覆盖 AppError。影响所有端点的框架级 422，owner 是 T0004 全局 handler。**Gate Review 确认**：接受框架默认（SPEC 补一句例外说明）或注册 RequestValidationError handler 映射到统一信封（`code = "REQUEST_VALIDATION_ERROR"` 或按错误类型细化）。

---

## 8. Cross-links

| 我要…… | 去哪 |
|---------|------|
| 逐行理解 T0501/T0502 代码、做自测练习 | [../phase-05-file-upload.md](../phase-05-file-upload.md)（Layer 1 · Technical Learning） |
| 准备面试话术 | [../interview-notes/dx-rag-interview-guide.md](../interview-notes/dx-rag-interview-guide.md)（Phase 5 深度章已 consolidation——2026-08-26 Phase Learning Review：30 秒 + 1-2 分钟 + 验证驱动修复 STAR + P5Q ×12 + EP5 ×4；候选素材在教材第 4/10 节） |
| 查 Python / FastAPI 知识点 | [../python-for-frontend-dev.md](../python-for-frontend-dev.md) 第 28（T0501）/ 29（T0502）/ 30（T0503）节 |
| 上游设计上下文 | [phase-04-engineering-review.md](./phase-04-engineering-review.md)（校验哲学 / file_count / exist_ok 教训） |

---

> **Phase 5 评审第三次增量（T0503，2026-08-25）**：验证闭环让"失败不留垃圾"从设计主张变成实测结论——3 个新 ADR（09/10/11）的主线是**验证脚本的边界**：断言只走 public interface（SPEC 声明回滚机制是 implementation detail 的直接延伸）、子进程隔离（ChromaDB 句柄 + Settings 单例两个进程级状态陷阱一个套壳解决）、声明替代与 GUARD 分离（不越界修代码）。最有力的结果不是"15 场景通过"，而是**零业务代码修复**——T0308/T0502 的副作用归属设计经受住实证而非被推翻。诚实声明：执行证据为**开发期痕迹**（pycache 21:04/21:07 + 实测催生的 stderr 过滤器），最终版（22:17）完整输出未见——AC-F002-08/09/10 按"脚本覆盖核对 + 开发期执行痕迹 + 用户 TASKS.md DONE 宣告"记录，不虚构全量 PASS；Phase 12 T1203 正式回归仍待执行。Pending 增至四项：#35/#36（T0501 遗留）、#37（FAILED→422 丢 warnings）、#38（请求级校验 422 的 FastAPI 默认信封，来自脚本 GUARD F-4）——全部交 Phase Gate Review 裁决，不擅自回写 SPEC、不擅自改实现（Freeze Policy）。**本次评审到此为止，不启动下一 Task。**
