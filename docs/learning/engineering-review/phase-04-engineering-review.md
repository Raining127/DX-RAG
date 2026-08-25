# Phase 4 Engineering Review — Knowledge Base Management API

> 配套学习笔记：[../phase-04-knowledge-base-management.md](../phase-04-knowledge-base-management.md)（T0401–T0404 代码教材）
> 本文档定位：**工程决策复盘**——Phase 4 为什么这样设计、取舍在哪、已知缺口在哪。
> 本文档是 Phase 4 的**累计评审文档**：T0401 → T0404 → T0402/T0403 已按同一结构完成增量更新（7.6 / 7.8 / 7.9），不按 Task 新建文件。

---

## 0. Review Status

| 项 | 值 |
|----|----|
| **Phase** | Phase 4 — Knowledge Base Management API |
| **Status** | IN PROGRESS |
| **Coverage** | T0401–T0404（POST/GET Create+List、PUT Rename 级联+补偿、DELETE 级联删除、Collection Name Validation 正式验收） |
| **Completed Tasks** | T0401 ✅（含一次真实 SPEC_CONFLICT 处置：SPEC v1.5 → v1.6 naming-compatibility patch）；T0404 ✅（2026-08-25：74/74 实测 PASS，验收表与 v1.6 对齐，见 7.8）；T0402 ✅（2026-08-25：7 步级联 + 两层补偿 ADR-06 + keyword seam ADR-08，见 7.9）；T0403 ✅（2026-08-25：Chroma-first 顺序 + 不可逆 + 防御纵深 ADR-07，见 7.9） |
| **Pending Tasks** | 编码无——Phase 4 编码全部完成；流程环节：Phase Learning Review ✅（2026-08-25，Interview Guide Phase 级 consolidation 落地——P4Q13–P4Q18 + EP4-8）；剩余 Phase Gate Review（完成后 Status → COMPLETE，见模板 L22） |
| **Review Scope** | 本文件已评审 Phase 4 全部四个编码 Task（T0401/T0404/T0402/T0403），累计结构不变 |

---

## 1. Phase Position

| 维度 | 内容 |
|------|------|
| **Business Goal** | [PROJECT FACT] SPEC F001：用户需要按主题/项目隔离文档集合，不同知识库独立检索——Create/List 是知识库管理闭环的第一环 |
| **Technical Goal** | 把 Phase 1 的内部存储能力（VectorStore 11 个 public methods）第一次变成 HTTP 产品能力（/api/collections） |
| **System Position** | API Layer（backend/app/api/collections.py，项目第一个承载产品功能的 API 文件） |
| **Upstream Dependencies** | Phase 0（FastAPI app、router 结构、Pydantic schemas、AppError + 错误目录）；Phase 1（`create_collection` / `list_collections` / `get_files` 三个方法） |
| **Downstream Consumers** | T0402 Rename / T0403 Delete（已实现——消费共享校验函数、VectorStore 级联原语、keyword index seam）；[FUTURE] Phase 5 Upload（KB existence check；T0502 消费 invalidate_keyword_index）、Phase 10/11 Frontend（KnowledgeBaseManager 调用契约；T1101 落地前端等价 TS 校验，F017） |

---

## 2. Why This Phase Exists

没有 Knowledge Base Management，系统会缺什么：

1. **产品没有入口**：ChromaDB 操作能力在 Phase 1 已齐全，但用户/前端无法通过 HTTP 使用——"能力在、入口不在，就还不是产品"。就像一个没有大门的仓库，货架和货都在，用户进不去。
2. **检索没有隔离边界**：[PROJECT FACT] SPEC F001 Define——知识库是检索的隔离单元（产品文档库的问答不能混入人事制度库的内容）。没有 Create，用户只有一个"大杂烩"。
3. **Upload / Frontend 没有前置条件**：[FUTURE] Upload 必须有"目标 KB 存在"这个前提；Frontend 必须有可调用的 HTTP 契约。T0401 同时把这两件事的前置条件立起来了。

一句话：**Phase 1 造好了"存储机器"，Phase 4 把机器接上 HTTP 开关。**

---

## 3. Architecture Overview

[PROJECT FACT] T0401 所处层位：

```text
Client
  ↓
API Layer       ← T0401 主要在这里（collections.py + schemas.py）
  ↓
VectorStore     ← 复用 Phase 1（create/list/get_files 三个方法）
  ↓
ChromaDB
      ── 同时还有 ──
Filesystem
uploads/{name}/  ← T0401 的第二条腿（mkdir）
```

**关键判断：Create KB 是一个跨 API / Storage / Filesystem 的小型业务操作**——一个 HTTP 请求，两个持久化系统。这不是"三层架构里的纯 CRUD"：它有**多系统副作用**，工程上最重要的两个问题都从这里来：顺序（validation before side effects，见 ADR-03）和一致性（见第 7 节）。

[PROJECT FACT] 数据模型（SPEC F001 Detail）：**1 KB = 1 个同名 ChromaDB Collection + 1 个 uploads/{name}/ 目录**——三者用同一个字符串绑定，name 即身份（ADR-02）。业务概念（知识库）与存储实现（ChromaDB Collection）是两个可以独立演化的抽象层：v1 把它们绑定在同一个名字上，是"最简模型"的刻意选择，不是把两者混成同一个概念。

---

## 4. Data Ownership（每层拥有什么事实）

[PROJECT FACT]

| 层 | 拥有的事实 | 不拥有的事实 |
|----|-----------|-------------|
| API Layer（collections.py） | HTTP contract（路径/方法/状态码/错误码/响应形状）+ 业务校验规则 | ChromaDB 怎么创建 collection、metadata 长什么样 |
| Schema（schemas.py） | request / response shape | 业务规则（regex 不在 Schema 里） |
| VectorStore | ChromaDB 操作的唯一通道（F008）；`_client` 私有 | HTTP 概念（不认识 400/409） |
| ChromaDB | vector collection 的持久化 | 目录、文件 |
| Filesystem | 原始文件目录 uploads/{name}/ | 向量、metadata |

**Source of Truth 判断**：

- **Collection identity 的事实来源 = ChromaDB 自己**——`list_collections()` 就是 name 唯一性的裁判；重复检查不查别的，只查它（只有一条真实来源）。
- **file_count = Derived Data**——不是任何系统的存储字段，由 `get_files()`（ChromaDB chunk metadata 按 file_id 聚合）现场派生（ADR-05）。
- **Filesystem State 与 VectorStore State 是两个独立系统**，中间没有 ACID——一致性靠业务层编排纪律，不靠任何事务机制。
- **v1 没有 metadata database**（[PROJECT FACT] SPEC 7.3 明确不引入 SQLite/PostgreSQL/Redis）——不存在"第三处需要对齐的状态"。这是刻意做减法：**状态面越少，一致性问题越少**。

**重点抽查（F008 约束 2/3）**：API Router 不应该绕过 VectorStore 直接操作 ChromaDB 私有对象。T0401 的代码遵守了这一点——collections.py 全文没有出现 `_client`、没有 import chromadb，只调用 `store.create_collection(...)` / `store.list_collections()` / `store.get_files(...)`。**这是 Phase 1 的 abstraction boundary 第一次在真实业务代码里被"抽查通过"。** T0402/T0403 同样遵守：rename/delete 的级联与补偿全部在 VectorStore 内（`rename_collection` / `delete_collection`），API 层只碰 uploads 目录——因为目录的所有权在 API 层（ADR-06：补偿代码的位置 = 资源所有权的位置）。

---

## 5. Core Engineering Decisions（ADR）

> 格式：Decision / Context / Problem / Chosen Solution / Why / Trade-off / Future Improvement / Status。
> 基于真实项目事实提炼的 8 个决策（ADR-01~05 来自 T0401，ADR-06~08 来自 T0402/T0403 实现）。这些是面试"为什么"类问题的答案库。

### ADR-01 — One KB = one ChromaDB Collection

- **Decision**：一个知识库 = 一个独立的 ChromaDB Collection。
- **Context**：[PROJECT FACT] SPEC F008 Design Constraint 1 明文规定；F001 数据模型："一个 Knowledge Base = 一个独立的 ChromaDB Collection + 一个独立的 uploads/{collection_name}/ 目录"。
- **Problem**：文档集合需要按主题隔离，不同 KB 独立检索（F001 Define）。
- **Chosen Solution**：collection 就是隔离单元——物理隔离，删除/重命名/检索天然按 collection 边界。
- **Why**：ChromaDB 的 collection 本来就是"文档+向量+metadata 的独立命名空间"，用它做 KB 边界零成本；共享一个 collection 再靠 metadata 过滤，检索时每次都要带 where 条件且隔离性靠约定不靠结构。
- **Trade-off**：KB 数量大时 collection 数量同涨（ChromaDB 的 collection 管理成本）；跨 KB 检索不直接支持。
- **Future Improvement**：[FUTURE] 若未来需要跨 KB 检索，需要在检索层做多 collection 查询合并——那是新功能，不动这个基本结构。
- **Status**：Implemented（Phase 1 + T0401 消费）。

### ADR-02 — KB name directly serves as storage collection name in v1

- **Decision**：v1 中 KB name 直接作为 ChromaDB collection name 和 uploads 目录名。
- **Context**：[PROJECT FACT] F001 数据模型 + v1.6 patch 产品决策："v1 不引入 KB 名称→存储名称映射层"。
- **Problem**：中文等宽字符集名字与 ChromaDB 存储约束冲突（第 6 节 Case Study）；是否引入 display_name/storage_name 映射？
- **Chosen Solution**：收紧 name charset 对齐存储约束（v1.6 regex），保持 name 单一身份。
- **Why**：第 6.6 节的全维度分析——变更范围最小、identity ripple 为零、metadata/uploads/rename/query/frontend 全部不动；额外红利：name 字符集 `[A-Za-z0-9_-]` 同时保证目录名文件系统安全（path traversal 防线减负）。
- **Trade-off**：用户不能用中文/Unicode 命名 KB（v1 产品能力受限）；name 即身份意味着**改名 = 改身份**（T0402 必须做全套级联而不是改个显示值）。
- **Future Improvement**：[FUTURE] 若产品要求任意 Unicode 命名 → 引入 kb_id / display_name / storage_key 三身份模型（第 6.8 节）。
- **Status**：Implemented（v1.6 生效，T0401 代码遵守）。

### ADR-03 — Validation happens before persistence side effects

- **Decision**：所有可能拒绝请求的校验（name 规则、重复检查）排在第一个持久化副作用（create_collection）之前。
- **Context**：[PROJECT FACT] F001 Create 五步的顺序本身就是契约：Validate → Duplicate → Create Collection → Create Dir → 201。
- **Problem**：校验后置会导致"请求失败但系统状态已变"（学习笔记第 7.1 节的错误顺序图）。
- **Chosen Solution**：400/409 出口全部前置，副作用从第 3 步才开始。
- **Why**：副作用前的拒绝是免费的（无状态污染、无补偿代码）；把第三方依赖约束翻译成边界校验（学习笔记第 7.3 节）。
- **Trade-off**：校验函数必须先于一切被调用——要求实现者守住顺序纪律（代码顺序即业务顺序）。
- **Future Improvement**：[FUTURE] Phase 5 T0501 的六步校验管道是同一原则的放大版（TASKS L1436 "Validation happens BEFORE any file system write"）。
- **Status**：Implemented。

### ADR-04 — Collection API consumes VectorStore public interface instead of ChromaDB SDK directly

- **Decision**：collections.py 只调用 VectorStore 的 public methods，不 import chromadb、不碰 `_client`。
- **Context**：[PROJECT FACT] F008 Design Constraints 2/3：所有 ChromaDB 操作必须走 public interface；外部代码不得访问私有属性；约束 4：为未来 Milvus 扩展保持接口一致性。
- **Problem**：API 层直连 SDK 会把存储实现细节泄漏到业务层，换存储引擎时业务代码全要改。
- **Chosen Solution**：业务层只喊业务动词（create_collection / list_collections / get_files）。
- **Why**：抽象边界（第 4 节 Data Ownership）；Phase 1 的 11 个 public methods 第一次被真实业务消费（学习笔记第 12 节）。
- **Trade-off**：多一层间接；VectorStore 接口能力不足时（如未来要分页）得先扩接口才能做业务。
- **Future Improvement**：[FUTURE] Milvus 替换 ChromaDB 时，collections.py 理论上零改动（新实现类继承 VectorStore 即可）——这是 F008 约束 4 的兑现点。
- **Status**：Implemented（T0401 代码抽查通过，第 4 节）。

### ADR-05 — file_count derived through existing metadata aggregation rather than separate metadata DB

- **Decision**：file_count 由 `len(get_files(name))` 现场聚合，不维护独立计数字段、不建 metadata 数据库。
- **Context**：[PROJECT FACT] SPEC 7.3 Persistence Strategy：v1 不引入 SQLite/PostgreSQL/Redis；file-level metadata 反规范化冗余存于 chunk metadata；`get_files()` 按 file_id 聚合。
- **Problem**：列表页需要文件数；两种来源——独立维护 vs 派生计算。
- **Chosen Solution**：派生计算（学习笔记第 6 节）。
- **Why**：派生数据永远一致（不存在计数漂移）；写入路径零额外负担。
- **Trade-off**：每次 GET 都要全量拉 metadata 聚合——读取成本 O(该 KB 全部 chunks)；文件数 × chunk 数增长后变重。
- **Future Improvement**：[FUTURE] 规模扩大时的选项（10x：仍可接受；100x：考虑缓存 file_count 或引入 metadata store；1000x：必须引入独立 metadata store + 异步聚合）——均为 Future，未实现，见第 8 节。
- **Status**：Implemented。

### ADR-06 — Rename 原子性 = 两层补偿（存储级快照 + 编排级反转）

- **Decision**：rename 的"失败后回到全旧状态"（AC-F001-06）用两层补偿实现：存储级子原子性（`VectorStore.rename_collection` 内部快照自补偿）+ 编排级补偿（API 层 `_compensate_rename` 逆序反转已完成步骤）。
- **Context**：[PROJECT FACT] SPEC v1.5 存储级契约：collection 改名 + chunk metadata 级联（collection_name / source_file）一次调用完成、storage level atomic；F001 业务层 7 步（校验 → 存储级改名 → uploads 目录 → keyword 失效 → 只读验证）。PF-2 预检提出的"第二步失败时内部语义未定"就是本决策要回答的问题。
- **Problem**：四类持久化步骤（ChromaDB 改名、metadata 级联、目录改名、keyword 失效）横跨两个系统，没有 ACID；任一步失败都要回到"全旧状态"，但"旧状态"散落在 ChromaDB 与文件系统两处，且存储级两步（改名 + 级联）本身就可能半途失败。
- **Chosen Solution**：存储级先保证自己的子原子性——`col.get(include=["metadatas"])` 一次性快照，ids + metadatas 同时充当级联源与补偿载荷（undo-log 思想：**快照即补偿载荷**），失败时 `_restore_rename` 逆序恢复（先 metadata 回写、后 collection 改名回）；编排级 `_compensate_rename` 按两个 flags（vector_done / uploads_done）判定已完成步骤，逆序反转（目录先回、再反向 `rename_collection(new, old)`）。keyword invalidation 不回滚（F001：invalidation 无恢复要求）。
- **Why**：[ENGINEERING KNOWLEDGE] **补偿代码的位置 = 资源所有权的位置**——ChromaDB 的中间态只有 VectorStore 能可靠恢复：改名已发生后 target 名不确定，外部层连 `get_collection` 该用哪个名都无法可靠判断；uploads 目录只有 API 层知道它的存在。把补偿放在资源所有者处，两层各自收敛自己的状态，不互相猜测。
- **Trade-off**：补偿是 best-effort——双失败（forward + compensate 都失败）时残余中间态，只能 `logger.exception` 不掩盖、不能自愈（7.9 新失败模式 1）；快照的内存成本 O(全部 chunks metadata)；补偿路径是代码里的"影子流程"，读代码时要能一眼看出正向与反向的对应。
- **Future Improvement**：[FUTURE] 1000× 时升级为 saga / 一致性扫描（第 8 节）；三身份模型（6.8）落地后 rename 退化为改 display_name，级联消失。
- **Status**：Implemented（T0402；PF-2 的归属答案 = 两层都要）。

### ADR-07 — Delete 顺序：Chroma-first + 不补偿 + 防御纵深

- **Decision**：级联删除的顺序固定为 ChromaDB delete → uploads rmtree → keyword invalidation；删除不可逆、不补偿；前置 `_assert_safe_uploads_target` 防御性路径检查。
- **Context**：[PROJECT FACT] F001 Delete 4 步 + SPEC 6.5 "irreversible"；T0403 D-1（顺序论证）/ D-2 / D-5（防御纵深）。
- **Problem**：级联删除中途失败时残余状态无法消除（不可逆 = 没有补偿空间）——问题是**选哪种残余最无害**：uploads 先删失败 → 活 KB 缺文件（检索命中 metadata 但文件已丢，性质最坏）；Chroma 先删失败 → 状态完好；Chroma 成功后才失败 → 最坏残余 = 孤儿目录（性质轻，且 DELETE 重试/手动清理都有路径）。
- **Chosen Solution**：Chroma-first。失败 → 500 INTERNAL_ERROR + 结构化日志带 `chroma_deleted` / `uploads_dir_exists` 两 flag——**残余状态可枚举**（7.9 新失败模式 3）；`_assert_safe_uploads_target` 用 `Path.resolve()` + parent 比对拒绝越界目标（RuntimeError → INTERNAL_ERROR，零副作用）；缺失目录是 no-op（删除的目标态 = 缺席）。
- **Why**：[ENGINEERING KNOWLEDGE] 不可逆操作没有补偿空间时，"残余最无害 + 残余可枚举"是诚实性的替代品——把"不知残余为何"变成"失败时刻可精确推断残余"。缺失目录的 no-op 语义与 rename 对缺失源目录的"真实不一致"语义形成对照：**同一物理状态在不同操作下的语义由目标态决定**（学习笔记第 10.6 节）。
- **Trade-off**：无补偿意味着残余只能人肉清；防御检查是 defense-in-depth（正常路径已有 regex 字符集 + 404 存在性双保险，触发它说明 collection 名被人为污染）。
- **Future Improvement**：[FUTURE] 一致性扫描任务（启动时比对 uploads/ 与 ChromaDB）；规模化后可能需要软删除/回收站（SPEC 外，需重新打开决策）。
- **Status**：Implemented（T0403）。

### ADR-08 — Keyword index seam：契约先行，实现后置

- **Decision**：T0402 先建立 `keyword_index.py` 的失效契约（文档化 no-op 实现），T0602 再填真实实现。
- **Context**：[PROJECT FACT] TASKS T0402 Dependencies 写着 "Phase 6 (keyword index — invalidation call…)；Phase 6 排在 Phase 4 之后。PF-1 预检："无对象可失效"。
- **Problem**：rename/delete 的编排步骤要求"失效 keyword index"，但该 index 在 Phase 6 才存在；T0402 却必须现在写定调用点、异常路径、补偿路径。
- **Chosen Solution**：**接口形状先于实现存在**——`invalidate_keyword_index(collection_name)` 契约（单 collection 范围、幂等、索引缺席 no-op、真失败 raise 由调用方映射 RENAME_FAILED）；body 是文档化 no-op（"T0602 replaces the body"），并明确 real integration acceptance DEFER TO T0602。
- **Why**：编排代码一次写对——调用点、异常路径、错误映射全部现在就位，T0602 只需换 body、不改任何调用方；且 no-op 期间语义正确：Phase 6 前没有 index 可失效，"缺席 no-op"本身就是该契约规定的正确行为。对比方案"先不调、等 T0602 再插调用点"更稳——后者会在编排里丢步骤。
- **Trade-off**：契约的正确性（invalidate 失败 → RENAME_FAILED 的映射是否合适）在 T0602 真实实现后才被验证（Pending #34）；失效语义在 T0602 前不生效（但此时无 index，语义空转无害）。
- **Future Improvement**：T0602 用 dirty-flag 实现替换 body；契约本身（调用方视角）预计不变。
- **Status**：Seam established（T0402）；implementation deferred to T0602。

---

## 6. SPEC_CONFLICT Case Study——T0401 真实工程事件

> 这是 T0401 最重要的工程学习案例。它不是"一个 bug 被修好了"，而是"两个已冻结的要求被发现无法同时成立，然后走了一次正规的规格修订流程"。

### 6.1 Problem（原始假设）

[PROJECT FACT] SPEC v1.5 时代，F001 的 canonical regex 是：

```text
^[A-Za-z0-9][A-Za-z0-9_\-一-鿿]{1,48}[A-Za-z0-9]$
```

规则：3-50 字符、首尾必须是字母或数字、**中间允许字母/数字/下划线/连字符/中文字符**（`一-鿿` 是 CJK 统一表意文字区间的正则写法）。

也就是说，"a中b"、"kb-产品文档"这类名字在当时是 SPEC-valid 的输入。同时 SPEC F001 规定：1 KB = 1 个**同名** ChromaDB Collection（ADR-02）。

### 6.2 Runtime Discovery（真实 ChromaDB 约束）

[PROJECT FACT] T0401 验证阶段（真实 TestClient + 真实 ChromaDB + 真实文件系统）发现：**真实 ChromaDB 对 collection name 有自己的约束**——collection name 只接受 `[a-zA-Z0-9._-]` 字符（collections.py:72 的注释、SPEC v1.6 patch note 均有记录）。

于是出现这条链：

```text
SPEC validation PASS（"a中b" 按 v1.5 规则合法）
    ↓
ChromaDB create_collection FAIL（中文字符不被接受）
    ↓
unhandled dependency exception
    ↓
500 INTERNAL_ERROR（main.py:54-65 的全局兜底）
```

### 6.3 Why It Was a Real Conflict

[PROJECT FACT] 按照产品契约，该输入原本**应该成功**。所以这不是普通代码 bug（代码没错，它忠实地执行了 SPEC）——而是：

> **两个已冻结要求无法同时成立**：
> 要求甲（v1.5）：中间允许中文的 KB 名必须可用。
> 要求乙（F001）：KB name 必须直接作为 ChromaDB collection name。
> 而 ChromaDB（第三方事实）不允许中文 collection name。
> 甲乙同时成立 → 不可能。

链路的完整形态：

```text
SPEC-valid input（"a中b"）
    ↓
storage rejects（ChromaDB 命名约束）
    ↓
API cannot satisfy contract（契约说成功，实际 500）
```

### 6.4 Why Catching the Exception Was Not Enough

[ENGINEERING KNOWLEDGE] 一个直觉反应是：

```python
try:
    store.create_collection(name)
except ChromaDBNameError:          # 伪代码
    raise AppError("INVALID_COLLECTION_NAME")
```

看起来"一行修复"，实际是**偷偷修改产品允许的名字范围**。想清楚这个差异：

| 做法 | 本质 | 后果 |
|------|------|------|
| catch 依赖异常 → 转 400 | 让"ChromaDB 的约束"悄悄变成"产品的约束" | 产品规则被第三方依赖绑架，且没人拍板过 |
| 报告冲突 → 产品决策 → 改 SPEC | 让"产品允许什么"由产品说了算，然后让实现与产品对齐 | 规则有 owner、有记录、前后端同步 |

"哪些名字合法"是一个 **Product / Specification Decision**，不是技术实现决定。实现者没有权限替产品缩窄用户可用的名字空间——哪怕缩窄后技术上更"顺"。**catch 只解决了"错误的表现形式"（500 → 400），没有解决"SPEC 与 implementation capability 不一致"这个事实本身**——冲突依旧存在，只是被藏进了异常处理分支里。

### 6.5 Correct Engineering Process

[PROJECT FACT] 项目有明确的 SPEC Freeze Policy（CLAUDE.md）：

```text
发现冲突
→ 停止受影响行为的实现
→ 不自行做产品决策
→ 标记 Task BLOCKED
→ 报告冲突（冲突位置、原因、影响、最小决策点）
→ 等 owner 决策
```

所以开发流程没有偷偷修改产品行为，而是走了完整流程：

```text
Implement → Verify → Discover Conflict → STOP → BLOCKED → Report
→ Product Decision → SPEC Patch（v1.6）→ Regression → DONE
```

要让学习者理解的一点：

> **"会停下来报告问题"也是工程能力，不是开发能力不足。** [ENGINEERING KNOWLEDGE]
> 初级工程师遇到规格和现实冲突时的典型错误是"选一条自己觉得对的路偷偷走过去"；成熟的做法是"把冲突摆到台面上，让有决策权的人拍板"。因为实现者能看见的约束永远少于产品/业务能看见的约束。

### 6.6 Option Analysis（当时摆上台面的两个方案）

**Option A — 收紧 charset（最小修改）**

把 regex 收成 `^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$`：移除中文允许，让产品规则与 ChromaDB 存储约束一致。

**Option B — 引入名称映射层**

增加 `display_name`（用户可见）/ `storage_name`（存储安全名）或 mapping layer：用户用中文名，系统内部翻译成 ASCII 安全名存 ChromaDB。

[PROJECT FACT] 全维度比较：

| 维度 | Option A（收紧） | Option B（映射层） |
|------|-----------------|-------------------|
| **变更范围** | 一行 regex + SPEC 一条规则 | 新身份模型 + 映射逻辑 + 所有消费方改造 |
| **identity ripple（身份涟漪）** | 无——name 语义不变 | KB name 不再是 chunk metadata 的 `collection_name`、`source_file`、uploads 路径的身份锚点——**引入第二身份模型会波及 Phase 3 已建成的整套身份体系**（T0308 metadata 9 字段、F008 反规范化） |
| **metadata** | 不变 | 每个 chunk 的 metadata 要加 storage_name？还是引用 kb_id？全部重设计 |
| **uploads path** | 不变（name 即目录名） | 目录用哪个名？display 还是 storage？谁负责转换？ |
| **rename** | T0402 的 rename 级联只涉及 name | rename 要同时考虑 display 和 storage 两个名（[FUTURE] T0402 复杂度翻倍） |
| **query / frontend** | 不变 | API 要返回两个名字字段，前端每个 KB 组件都要处理 |
| **migration complexity** | 无（v1.5 还没上线任何中文 KB） | 映射规则、重名策略、查询翻译全要设计 |
| **当前产品价值** | 中文 KB 名在 v1 是"锦上添花" | 为锦上添花付出整个身份模型的重构 |

### 6.7 Why v1 Chose A

[PROJECT FACT] SPEC v1.6 patch 记录了产品决策："v1 不引入 KB 名称→存储名称映射层"。结论：**最小规格修订优于在 v1 引入新的身份模型。** 而"选最小方案"本身不是偷懒——它是**在功能价值与模型复杂度之间做取舍**：v1 的目标是走通 RAG 全链路，不是做 KB 命名的企业级方案。

另外两个被记录在案的决策细节（SPEC v1.6 patch note）：

1. **不因 ChromaDB 支持 `.` 而新增 `.` 支持**——即使存储层允许点号，产品决定不放宽。SPEC 没有记录这个决策的理由，所以这里**不猜测产品动机**；[ENGINEERING KNOWLEDGE] 从通用工程角度可以理解这类决策的常见考量：`.` 在路径/文件名语义里容易制造歧义（隐藏文件、扩展名联想、shell glob），而"存储层允许什么"从来不是"产品允许什么"的上限——**产品规则应该比存储约束更窄，而不是对齐到最宽**。
2. **Blocking Open Questions 保持 0**——这次修订没有引入新的待决问题，SPEC 继续 FROZEN（v1.6）。

### 6.8 Why A Is Not Universally Correct

[FUTURE] 未来企业产品很可能更适合：

```text
kb_id        = stable internal identity（UUID，永不改变）
display_name = user-visible name（可中文、可改、展示用）
storage_key  = infrastructure-safe identifier（给 ChromaDB / 目录 / 缓存键用）
```

这套三身份模型能同时满足"用户想要中文名"和"存储层要安全名"。但要注意：

- **这是 Future Architecture，Not implemented in current v1。** [FUTURE]
- v1 的"1 KB = 1 同名 Collection"是为了**先把路走通**；三身份模型是**规模化后**的正确解。
- 不要面试时说"我的项目用了 kb_id/display_name/storage_key 设计"——v1 没有。可以说"项目在 v1.6 经历过一次真实冲突，当时选择了最小修改；如果产品要求任意 Unicode 命名，我会这样重新设计 identity……"（面试话术见 Interview Guide Phase 4 深度章）。

### 6.9 Repository Evidence（仓库里留下的真实证据）

学习时可以直接验证的证据链（基于 git working tree 的真实 diff）：

| 证据 | 内容 |
|------|------|
| SPEC v1.5 → v1.6 diff | 旧 regex `^[A-Za-z0-9][A-Za-z0-9_\-一-鿿]{1,48}[A-Za-z0-9]$` → 新 regex `^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$`（F001 创建步骤 1） |
| SPEC v1.6 patch note | "KB Name Naming-Compatibility Resolution …… 产品决策：v1 不引入 KB 名称→存储名称映射层，不因 ChromaDB 支持 `.` 而新增 `.` 支持" |
| TASKS.md T0404 验收表 | `"测试-kb" (Chinese chars) → accepted` 改为 `→ rejected`；新增 `"a中b" (Chinese char in middle) → rejected` |
| TASKS.md T0401 | Status: TODO → DONE |
| collections.py:70-74 | 新 regex 常量 + 三行注释（v1.6 patch、无中文、无 `.`） |

两个诚实的说明：

1. **中间态 BLOCKED 没有持久化在当前 TASKS.md 里**——现在能看到的只有两个端点（TODO → DONE）+ SPEC patch 记录。BLOCKED → 报告 → 决策的过程本身没有文件化留存。这不影响结论（v1.6 patch note 是决策的正式记录），但值得记住：**事件的过程痕迹比结果痕迹容易丢**，这也是为什么"写下来"有价值。
2. **旧规则本身是模糊的**——v1.5 的 T0404 验收表把"测试-kb"（首字符就是中文）标为 accepted，但按 v1.5 的正则（首尾必须字母/数字）它其实**不合法**。旧验收表与旧正则并不完全自洽——这本身是"中文到底允不允许、允许到什么程度"在旧规则里没有真正想清楚的证据。SPEC_CONFLICT 的价值之一，就是把这种模糊**一次决策清掉**。

### 6.10 开发过程复盘（真实工作闭环）

> 用工程师视角复盘 T0401 从需求到 DONE 的完整闭环——事件过程（Requirement → … → Done）与上文的冲突处置（6.5）互为表里。

**Requirement**：拿到 SPEC F001（KB 管理）+ Section 6.5（Create/List 契约）+ AC-F001-01/02。要点：POST 五步流、201/400/409、GET 带 file_count、响应形状逐字段给定。

**Implementation**：新建 `backend/app/api/collections.py`（81 行）：模块级 regex 常量 + 共享校验函数 + 两个端点；在 router.py 注册子路由。Schema 直接用 Phase 0 建好的三个模型。

**Verification**：用 **real TestClient + real ChromaDB + real filesystem** 验证，而不是只 mock。为什么？——**因为 ChromaDB 的命名约束只有在真实存储层才会暴露**。如果 mock 掉 VectorStore，`"a中b"` 这个名字会一路绿灯，SPEC_CONFLICT 就永远不会被发现。**验证环境的真实性决定了你能发现哪一类问题：mock 能验证你的代码逻辑，只有真实依赖能验证世界与你的假设之间的裂缝。** [ENGINEERING KNOWLEDGE]

（诚实说明：仓库中没有持久化测试脚本——本次验证是开发期的真实集成验证，TASKS.md 记录 DONE；第 7.5 节有完整立场。）

**Unexpected Issue**：发现 SPEC_CONFLICT：v1.5 允许中间中文，真实 ChromaDB 不接受 → SPEC-valid 输入 500。

**Escalation**：没有自己 catch 掉、没有自己改 SPEC——按 SPEC Freeze Policy：停止受影响行为 → 标记 BLOCKED → 报告冲突（位置/原因/影响/最小决策点）。

**Product Decision**：owner 拍板：收紧 charset（Option A），不引入映射层，不新增 `.` 支持 → SPEC v1.6 patch。

**Regression**：决策之后重新验证：合法 ASCII 名（"test-kb"）→ 201 + collection + 目录 ✅；重复名 → 409 ✅；"a中b"/"测试-kb" → 400 ✅（新规则）；TASKS T0404 验收表同步更新（accepted → rejected）；响应格式与 SPEC 6.5 逐字段比对 ✅。

**Result**：T0401 DONE：DX-RAG 第一个业务 API 上线，KB 管理闭环的第一环。

完整闭环：

```text
Requirement → Design → Implementation → Integration Test
→ Conflict → Escalation → Decision → Spec Sync → Regression → Done
```

[ENGINEERING KNOWLEDGE] 注意这个闭环里，"写代码"只占三格，**发现冲突、上报、决策、回归占一半**——真实企业开发的日常就是这样的分布。这就是为什么"只写代码"和"能走完闭环"是两种能力。

---

## 7. Failure Modes & Consistency Analysis（最诚实的一节）

### 7.1 Failure Modes 清单

[PROJECT FACT] 区分"当前已定义/处理"与"值得未来关注"：

| 失败场景 | 当前行为 | 状态 |
|----------|---------|------|
| name 不合法 | `validate_collection_name` → AppError → 400 INVALID_COLLECTION_NAME | ✅ 已定义（SPEC 6.5 / 9.2） |
| name 重复 | duplicate check → AppError → 409 COLLECTION_ALREADY_EXISTS | ✅ 已定义 |
| 请求体不是合法 JSON / 缺 name 字段 | FastAPI 默认 422（**不是** SPEC 6.7 信封形状） | ⚠️ 框架默认，见 7.4 |
| ChromaDB 创建失败（磁盘、内部错误等） | 异常上抛 → 全局兜底 500 INTERNAL_ERROR（无专属错误码） | ⚠️ SPEC 未给 Create 定义专属 5xx 码（Rename 才有 RENAME_FAILED） |
| mkdir 失败（权限/磁盘满） | OSError 上抛 → 500；**且 ChromaDB collection 已创建，无补偿** | ⚠️ 一致性 gap，见 7.2 |
| 未知异常 | 全局兜底 500 INTERNAL_ERROR + traceback 日志（main.py:54-65） | ✅ 已定义（SPEC 9.4） |

### 7.2 Create 双副作用——无补偿的跨系统一致性缺口

Create KB 本质上有**两个持久化副作用**：

```text
ChromaDB Collection   （副作用 1，collections.py:98）
+
uploads directory     （副作用 2，collections.py:100）
```

工程问题：**如果 Collection 创建成功，但 mkdir 失败，会怎样？**

```text
Current implementation:   collections.py:98-100 —— ChromaDB 先建、目录后建，
                          两个操作之间没有任何补偿/回滚逻辑。
                          mkdir 抛 OSError → 全局兜底 500 INTERNAL_ERROR，
                          而 ChromaDB collection 已经存在。

Potential consistency gap: 出现"孤儿 Collection"——ChromaDB 里有这个 KB、
                          文件系统没有对应目录。下次同名创建会被 409 挡住
                          （collection 存在），用户看到一个"创建失败但名字
                          被占用"的知识库。

Current SPEC status:      SPEC F001 的原子性要求（AC-F001-06）只覆盖 Rename
                          （T0402），Create 没有定义失败补偿语义。

→ CURRENTLY NOT FIXED. 这是真实存在的一致性缺口，不是已解决的问题；
  没有 rollback、没有 compensation、没有 saga——任何声称"已修复"的说法都不属实。
```

### 7.3 Reverse Orphan——exist_ok=True 的静默合并

还有一个**反向的孤儿**，同样诚实记录：

```text
Current implementation:   mkdir(parents=True, exist_ok=True) —— exist_ok=True
                          让"目录已存在"静默通过。

Potential gap:            如果文件系统里已有一个孤儿目录 uploads/{name}/
                          （比如历史上建过 KB 后 ChromaDB 侧被手动清掉），
                          重新创建同名 KB 会静默合并进旧目录——filesystem state
                          被静默复用，旧目录里的残留文件会被当成新 KB 的内容。

Current SPEC status:      SPEC 未定义"目录已存在但 collection 不存在"的语义。

→ CURRENTLY NOT FIXED.
```

[ENGINEERING KNOWLEDGE] 这两个缺口不是"代码写错了"——它们是**跨系统副作用缺少编排层的必然产物**。要真正解决需要某种"事务协调器"（compensation / saga / 两阶段提交），而 SPEC 明确把这类机制排除在 v1 之外（Rename 的补偿留给 T0402，Create 根本没提）。所以正确态度是：**知道缺口在哪、什么条件下会被触发、后果是什么**，而不是假装它不存在或私下加机制（那是 Scope Discipline 违规）。

### 7.4 Request Validation Error Shape（框架 422 与统一错误信封）

```text
Observation:   collections.py 只对业务校验（validate_collection_name / duplicate
               check）抛 AppError——它们走 main.py:43-51 的 AppError handler，
               得到 SPEC 6.7 统一信封 {"error": {code, message, details}}。
               但请求体本身不合法（缺 name 字段、类型错误）时，校验发生在
               Pydantic/FastAPI 框架层——main.py 只注册了 AppError 与
               Exception 两个 handler，FastAPI 内置的 RequestValidationError
               handler 优先于 Exception 兜底（Starlette 按 MRO 选最具体 handler），
               最终返回 FastAPI 默认 422 形状 {"detail": [...]}——非统一信封。

Needs verification: 该行为基于代码结构推断（handler 注册情况），
                    尚未在真实运行环境实测确认。

Impact（若属实）:  错误契约在边界场景下形状不一致，前端错误解析要兼容两套形状。

Current SPEC status: SPEC 6.7 定义了统一错误信封；SPEC 未显式规定框架级
                     校验错误的形状。修复路径（注册自定义
                     RequestValidationError handler 或为 422 定义错误码）
                     属于 SPEC 决策，不是实现层可自行决定的行为。

→ Needs verification（建议 T1201 集成阶段实测确认后上报 SPEC），
  不写成已确认 defect。
```

### 7.5 Test Coverage Gap

```text
Observation:   仓库中没有持久化的自动化测试脚本（backend 无 test 文件）。
               T0401 的验证证据只存在于开发期真实集成验证（real TestClient
               + real ChromaDB + real filesystem）与 TASKS.md 的 DONE 记录。

Risk:          改任何下游（VectorStore / schemas / errors 目录）时无法自动
               发现 T0401 回归；SPEC_CONFLICT 类边界（命名规则）一旦再漂移，
               没有测试兜住。

Current SPEC status: SPEC 未要求 v1 测试基建（个人建议随 Phase 12 补）。
本次文档重构不新增测试（学习任务约束）。
```

### 7.6 Learning Review Findings 汇总 + Pending Questions

| # | Observation | Evidence | Impact | Suggested owner/task |
|---|------------|----------|--------|---------------------|
| 1 | Create 的两个持久化副作用无补偿：ChromaDB 成功后 mkdir 失败 → 500 且留下孤儿 collection | collections.py:98-100（无 try/补偿）；SPEC F001 原子性只定义 Rename（AC-F001-06） | 用户看到"创建失败但名字被占用"；重试 409 | T0403 已落地：cascade delete 提供了孤儿清理路径（DELETE 同名 KB 即可）；Create 自身补偿仍待 SPEC 决策（建议 T1201） |
| 2 | `exist_ok=True` 静默合并孤儿目录：目录存在但 collection 不存在时，创建同名 KB 会复用旧目录 | collections.py:100 | 上传落进历史残留目录；跨"KB 实例"的文件混淆风险 | 同 1（T0403 已提供清理路径） |
| 3 | 请求体不合法（缺字段/类型错）→ FastAPI 默认 422 形状（`{"detail": [...]}`），非 SPEC 6.7 统一信封 | main.py 只注册 AppError 与 Exception handler（L43-65）；FastAPI 内置 RequestValidationError handler 优先于 Exception 兜底 | 错误契约在边界场景下形状不一致（前端错误解析要兼容两套） | 建议 T1201 实测确认；若属实上报 SPEC（加错误码或注册自定义 handler） |
| 4 | 无持久化测试脚本：T0401 的验证证据只在开发期，未来回归无自动化保障 | 仓库无 test 文件 | 改任何下游（VectorStore/schema）时无法自动发现 T0401 回归 | 待定（SPEC 未要求 v1 测试基建；个人建议随 Phase 12 补） |

Pending Questions（延续 Phase 3 的 #1–27 编号）：

| # | 问题 | 来源 | 状态 |
|---|------|------|------|
| #28 | Create 失败（mkdir）是否需要在未来定义补偿语义？还是接受孤儿 collection 作为已知边界？ | T0401 Finding 1 | 待 SPEC 决策（T0403 落地后清理路径已存在，问题缩小为：Create 自身是否需要补偿） |
| #29 | "目录已存在但 collection 不存在"是否应视为冲突（409）而非静默合并？ | T0401 Finding 2 | 待 SPEC 决策（T0403 的 DELETE 可清理此类孤儿目录） |
| #30 | 框架级校验错误（422）是否需要接入统一错误信封？ | T0401 Finding 3 | 待 T1201 实测确认后上报 |
| #31 | v1 是否需要任何持久化测试基建以保护已完成 Task 的回归？ | T0401 Finding 4 | 待定（SPEC 无要求） |
| #32 | F017 前后端等价校验（backend Python 已落地 / frontend TS 待 T1101）需要什么机制性防漂移（共享测试向量 / 契约测试）？ | T0404 增量评审（7.8） | 待 T1101 落地时决策 |
| #33 | rename 双失败（forward + compensate）后的中间态残余是否需要一致性扫描/恢复任务？ | T0402 增量评审（7.9） | 待定（建议与 #31 一并考虑；v1 单机可接受） |
| #34 | keyword seam 契约（invalidate 失败 → RENAME_FAILED 映射）在 T0602 真实实现后是否仍成立？ | T0402 增量评审（7.9）+ PF-1 | 待 T0602 验证 |

### 7.7 其它工程观察（可维护性 / 安全）

**可维护性**：

- ✅ 81 行单文件 + 文件头浓缩契约（SPEC F001 五步 + 范围边界）——读代码不用翻 SPEC
- ✅ 校验规则只有一个家（模块级共享函数 `validate_collection_name`，T0402 已复用）；每个错误码有且只有一个抛出点
- ✅ `list_collections()` + `in` 的 O(n) 重复检查只有一条真实来源（ChromaDB 是 name 唯一性的裁判）——在 v1 规模（几十个 KB）下完全合理，且比"捕获依赖异常"更可读
- ⚠️ 代码顺序即业务顺序（Validate → Duplicate → Create → mkdir）——顺序纪律靠人守，没有机制性保障；T0402 的 rename 编排面对了同样问题，用 vector_done / uploads_done 两个 flags 让"已完成的步骤"可判定（ADR-06），delete 用两个残余 flag 让"残余状态"可枚举（ADR-07）——顺序纪律从"靠人"升级为"可判定"

**安全**：

- ✅ name 字符集 `[A-Za-z0-9_-]` 保证 uploads/{name}/ 目录名在任何主流 OS 都是合法文件名——间接为 Phase 5 的 path traversal 防线减负（KB 名不可能携带 `../`）
- ✅ API key env-only、v1 无认证——部署假设（本地/可信网络）与 CLAUDE.md 安全规则一致
- ⚠️ 无认证是部署边界而非安全保证——公网部署必须先加认证（SPEC 明确 Out of Scope）

### 7.8 T0404 增量评审（2026-08-25）

[PROJECT FACT] T0404 的实质：**0 行新增功能代码**——`validate_collection_name` 在 T0401 已落地（collections.py:77-88），T0404 做的是把 TASKS.md 验收表与 SPEC v1.6 对齐（8 个边界用例）并标记 DONE。工程上值得记录的观察：

**验证证据**（2026-08-25 实测）：

- 74/74 checks PASS（real TestClient + real ChromaDB + real filesystem，临时目录）：6 valid + 9 invalid 全部按 v1.6 规则判对；side-effect boundary 交叉验证（invalid 拒绝后 collection 列表 / 目录树 / 计数三方无残留）。
- 但**脚本已删除**：验证发生过、没有固化——Finding #4 对 T0404 的表述因此更精确：**"验证发生过，但回归没有自动化保障"**。将来任何对 regex 或校验链的改动，都要重新人工验证或重新写脚本。

**共享函数的位置观察**：TASKS.md T0404 允许 `backend/app/api/collections.py` **或** `backend/app/core/validators.py` 两处（L1386）。实现选择了 API 模块内。当前判断：正确——它目前唯一的消费者就在本模块（T0402 rename 也写进 collections.py）；若未来出现跨模块消费者（如 Phase 5 文件名校验复用同一风格），再考虑提升到 core/。**规则的位置应该跟着消费者走，不提前抽象。**

**F017 前后端漂移风险**（新增 Pending #32）：canonical regex 存在两份实现的隐患（backend Python 已落地；frontend TS 待 T1101）。当前唯一防漂移机制是"SPEC 是单一契约来源"这条纪律。T1101 落地后建议用共享测试向量（同一组合法/非法用例喂两端）做机制性保障。

**验收表自洽性确认**：6.9 的诚实说明 2 指出 v1.5 验收表与旧正则不自洽（"测试-kb"首字符中文却标 accepted）。v1.6 修订后验收表已自洽（TASKS.md diff：accepted → rejected + 新增 "a中b"）——旧模糊已随本次决策一次清掉。

### 7.9 T0402/T0403 增量评审（2026-08-25）

[PROJECT FACT] T0402/T0403 的实质：Phase 4 第一次面对**跨系统副作用的原子性与不可逆性**。Create 的一致性缺口（7.2/7.3）在 rename/delete 上没有重演：rename 用两层补偿把"失败后回到全旧状态"变成编排纪律（AC-F001-06，ADR-06），delete 用顺序设计 + 残余可枚举把"不可逆"变诚实（ADR-07）。预检 PF-1~5 逐条评估：

| PF | 预检发现 | 实现后评估 |
|----|---------|-----------|
| PF-1 | keyword index 无对象可失效 | ✅ 已解决：keyword_index.py 契约先行（ADR-08）；AC-F001-04 的 keyword 子句验证 DEFER T0602 |
| PF-2 | rename_collection 子原子性归属未定 | ✅ 已决策：两层都要（ADR-06）——存储级快照自补偿 + 编排级逆序反转 |
| PF-3 | 孤儿目录触发 fs rename 失败 | ⚠️ 仍成立（触发路径未变，Windows FileExistsError）；治理半解决：T0403 DELETE 可清孤儿目录，但"rename 撞孤儿目录 → 500"本身未改（孤儿治理仍挂 T1201） |
| PF-4 | ChromaDB 1.5.9 原语能力实测 | ✅ 确认：实现直接使用 modify / update 两原语；409 前置检查硬前提被遵守（重名 modify 抛原始 InternalError 的路径被前置 409 挡住） |
| PF-5 | RENAME_FAILED 零 raise 点 | ✅ 兑现：T0402 首用（collections.py:159），错误目录零新增 |

**新失败模式（T0402/T0403 引入的残余状态空间）**：

1. **rename 双失败（forward + compensate 都失败）**：两层补偿是 best-effort——补偿失败只 `logger.exception` 不掩盖，但残余 = 中间态（部分新部分旧），无第三层兜底。v1 单机规模下可接受（触发条件 = 两次独立持久化操作连续失败），规模化答案是 saga / 一致性扫描（第 8 节 1000×）→ Pending #33。
2. **验证步骤本身可触发补偿**：`_verify_rename` 只走 public read APIs（list_collections / list_chunks，AC-F008-03 合规）——但验证失败 → RuntimeError → 补偿 → 500 RENAME_FAILED 的链路意味着"验证"在 rename 里不是旁路而是可失败步骤（SPEC F001 step 5 明确要求，非过度工程）。
3. **delete 残余可枚举**：`chroma_deleted` / `uploads_dir_exists` 两 flag 结构化日志——失败时刻可精确推断残余：chroma_deleted=False → Chroma 未删（状态完好）；True + dir exists → 孤儿目录（性质轻）。
4. **keyword invalidation 不回滚**：rename 补偿不回滚 invalidation（F001 无恢复要求）——回滚后 index 处于"已失效"状态是语义安全的（失效 = 下次重建，不存在陈旧性风险）。这是"补偿不需要完全对称"的实例。
5. **缺失目录语义对照**：rename 缺失源目录 = 真实不一致（fail → compensate）；delete 缺失目录 = no-op（目标态即缺席）。同一物理状态在不同操作下的语义由目标态决定（学习笔记第 10.6 节）。

**可维护性增量**：

- ✅ 文件头浓缩契约扩展到 7 步 rename + 4 步 delete（collections.py:1-44）——"读代码不用翻 SPEC"惯例延续
- ✅ 错误码零新增：T0402/T0403 用到的 400/404/409/500 全部 Phase 0 已建（PF-5 兑现）
- ✅ `except AppError: raise` 显式透传（collections.py:279-280）——防止 404 被 catch-all `except Exception` 吞掉后伪装成 INTERNAL_ERROR
- ⚠️ rename 的 O(chunks) metadata 级联成本（快照 + 全量 update）——大 KB 改名变重（第 8 节 10× 已记录）

新增 Pending #33 / #34（已并入 7.6 Pending 表）。

---

## 8. Scalability Review（10x / 100x / 1000x）

> 本节所有方案均为 **[FUTURE] / Not implemented in v1** 分析。SPEC NFR：v1 单机、万级 document。

### 10× 规模（几十个 KB → 几百个 KB）

**可能出现的瓶颈**：

- GET /api/collections 的聚合成本线性放大：每 KB 一次 `get_files()` 全量拉 metadata，总成本 O(KB 数 × 平均 chunk 数)——几百 KB 时列表接口开始变慢
- rename 的 metadata 级联是 O(该 KB 全部 chunks)：快照 + 全量 metadata update（ADR-06 快照模式的固有代价）——大 KB 改名时一次性成本可观
- 孤儿缺口（7.2/7.3）的触发概率随创建次数上升——手动清理不再可行

**优化方向**（Not implemented in v1）：

- [FUTURE] file_count 缓存（带失效）或按需聚合（列表页先返回 name，file_count 懒加载）
- ✅ T0403 的 cascade delete 已落地（2026-08-25）——孤儿 collection 的清理路径现在真实存在：DELETE /api/collections/{name}（不可逆，人工运维手段）

### 100× 规模（团队级知识库、每日大量文档）

**可能出现的瓶颈**：

- GET /api/collections 每次全量扫描成为明确瓶颈——file_count 派生计算的"查询成本换写入一致性"权衡开始翻转
- name 即身份的限制放大：无重命名历史、目录与 collection 的状态全靠同名字符串对齐，任何一侧的漂移都无痕迹可查
- Create 无补偿：100× 的创建频率下，孤儿窗口（mkdir 失败）从"理论缺口"变成"真实事件"

**优化方向**（Not implemented in v1）：

- [FUTURE] 独立 metadata store（SQLite/PostgreSQL）接管 FileRecord 与 file_count（SPEC 外，需重新打开 7.3 决策）
- [FUTURE] Create 的补偿逻辑（mkdir 失败 → delete_collection）或顺序反转（先目录后 collection，留孤儿目录性质更轻；T0402 的两层补偿模式 ADR-06 是现成范本）
- [FUTURE] 一致性扫描任务（启动时比对 uploads/ 与 ChromaDB collection 差异）

### 1000× 规模（SaaS 化、多租户）

**可能出现的瓶颈**：

- ChromaDB 单机触顶（SPEC 原文：适合中小规模）——collection 数量与 chunk 总量都超设计目标
- name 即身份的模型彻底失效：多租户下重名、改名、任意 Unicode 命名都是刚需
- 本地 uploads/ 目录不可扩展

**优化方向**（Not implemented in v1）：

- [FUTURE] Milvus（F008 约束 4 的兑现点：MilvusVectorStore 继承 VectorStore，API 层零改动）
- [FUTURE] kb_id / display_name / storage_key 三身份模型（6.8 节）——所有内部引用改用 kb_id
- [FUTURE] 分布式存储（S3/MinIO）替代本地 uploads/，source_file 语义改为对象键
- [FUTURE] 异步 workflow：创建/重命名等跨系统操作用任务编排 + 事务/补偿模式（saga）
- [FUTURE] transaction / saga 正式引入（T0402/T0403 的补偿编排与顺序设计是前身——ADR-06/07——但它们是单操作内的人工编排，不是可复用的事务机制）

**核心判断**：T0401 的决策本质是**用最简身份模型 + 派生数据换 v1 的简单与正确**——在单机、几十个 KB 的规模下完全正确。T0402/T0403 在此基础上把跨系统副作用的一致性管理（补偿 / 顺序设计 / 残余报告）第一次带进项目——但那是单机、人工运维规模下的"编排纪律"，不是事务机制；规模化时的升级路径就是本节各段所列的 saga / 一致性扫描。规模扩大时，最先要动的是"name 即身份"（100× 内）和"现场聚合"（100× 内），然后才是存储引擎与身份模型的结构性升级（1000×）。

---

## 9. Cross-links（本文档与其它文档的边界）

| 我要…… | 去哪 |
|---------|------|
| 逐行理解 T0401–T0404 代码、做自测练习 | [../phase-04-knowledge-base-management.md](../phase-04-knowledge-base-management.md)（Layer 1 · Technical Learning） |
| 准备面试话术（30 秒 / STAR / 追问） | [../interview-notes/dx-rag-interview-guide.md](../interview-notes/dx-rag-interview-guide.md) Phase 4 深度章（Layer 3 · Interview） |
| 查 Python / FastAPI 知识点 | [../python-for-frontend-dev.md](../python-for-frontend-dev.md) 第 26/27 节 |

> **Phase 4 复盘完结（T0401–T0404）**：T0401 用 81 行代码兑现了 SPEC F001 的 Create/List 契约，并留下了比代码更值钱的东西——一次完整的"规格冲突 → 上报 → 产品决策 → 规格修订 → 回归"流程样本（SPEC v1.6）；T0404 以 0 行功能代码把共享校验函数正式验收为契约（74/74 实测）；T0402/T0403 把跨系统副作用的一致性管理第一次带进项目：rename 的两层补偿（ADR-06）、delete 的顺序设计与残余可枚举（ADR-07）、keyword index 的契约先行 seam（ADR-08）。AC-F001-01~06 对应实现全部落地（验证立场见学习笔记第 19.2 节——T0402/T0403 无本会话可查的端点级实测记录，按 TASKS.md DONE + 代码审查记录，不虚构 PASS）。Phase 4 编码到此完结。流程环节进展：Phase Learning Review ✅（2026-08-25）——Interview Guide 的 Phase 级 consolidation 已落地（新增 P4Q13–P4Q18 + EP4-8、修正 EP4-3、更新 3 分钟介绍与亮点 15）。剩余：Phase Gate Review——完成后本文档 Status → COMPLETE（模板 L22）。**本次评审到此为止，不启动下一 Task。**

---

## T0402 Pre-flight Review Findings

Status: Assessed（2026-08-25 预检；T0402/T0403 实现后逐条评估见 7.9——PF-1→ADR-08 已解决；PF-2→ADR-06 两层都要；PF-3 仍成立、治理半解决；PF-4 原语确认；PF-5 已兑现）

- **PF-1 — keyword-index 失效步骤无对象可失效**：Phase 6 未开始（T0601/T0602 TODO），仓库中无任何 keyword index 实现（grep 仅 docstring）。T0402 需先定义共享 invalidation 接口形状（TASKS 已预期 "define a shared invalidation interface"）；AC-F001-04 的 "keyword index 已 invalidate" 子句验证 DEFER 至 T0602。
- **PF-2 — rename_collection 子原子性归属未定**：SPEC v1.5 要求一次调用内完成 Collection 改名 + metadata 级联（两步 ChromaDB 操作），但未规定第二步失败时的内部语义；F001 补偿责任在业务层。候选：方法内自补偿 vs 编排层反向调用 `rename_collection(new, old)`。observable 原子性由 AC-F001-06 兜底。
- **PF-3 — 孤儿目录触发 fs rename 失败**：`uploads/{new_name}/` 已存在（T0401 Finding #2 成因）时 Windows 下 `Path.rename` 抛 FileExistsError → 触发补偿路径 → 500 RENAME_FAILED。孤儿目录治理建议挂 T0403 / T1201。
- **PF-4 — ChromaDB 1.5.9 运行时能力实测（真实 1.5.9 探针，临时目录）**：`Collection.modify(name=...)` 改名成功且 docs / collection metadata 保留；`Collection.update(ids, metadatas)` 只改写传入字段、documents 完好（级联可行原语确认）；**重名 modify 抛原始 `chromadb.errors.InternalError`（SQLite UNIQUE constraint, code 2067）——409 前置检查是契约正确性硬前提**；collection name 规则 3-512 `[a-zA-Z0-9._-]`（与 v1.6 regex 兼容）。版本差距（runtime 1.5.9 vs `^0.4.15`）不阻断 rename 能力，不升级依赖。
- **PF-5 — RENAME_FAILED 已在错误目录（errors.py:46）但零 raise 点**：T0402 首用，无需改错误目录。T0402 涉及的 4 个契约错误码（400/404/409/500）全部已存在。
