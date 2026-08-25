# Phase 4 — Knowledge Base Management API 学习笔记

> 这是一份随项目开发和个人理解逐步演进的学习文档。当前版本覆盖 **Phase 4 全部四个 Task：T0401（创建 + 列表）、T0404（名称验证正式验收）、T0402（Rename 级联 + 原子性）、T0403（Delete 级联）**。
>
> **Phase 4 编码部分全部完成。** 当前学习内容：T0401 ✅、T0402 ✅、T0403 ✅、T0404 ✅。**本文档状态：Learning Pass + Learning Review 完成**（2026-08-25；Interview Guide 的 Phase 级 consolidation 已落地——见 Interview Guide P4-4 的 P4Q13–P4Q18 与 P4-5 的 EP4-8）。尚未完成的只剩流程环节：Phase Gate Review。
>
> **本文档是"教材"——只管代码学习。** Phase 4 的学习体系分三层，每种知识有唯一归属：
>
> | 我要…… | 读哪个文档 |
> |---------|-----------|
> | 看懂代码、学 Python、做自测练习 | **本文档**（Layer 1 · Technical Learning） |
> | 理解设计取舍、ADR、一致性缺口、SPEC_CONFLICT 完整复盘 | [phase-04-engineering-review.md](./engineering-review/phase-04-engineering-review.md)（Layer 2 · Engineering Review） |
> | 准备面试话术（30 秒 / STAR / 追问） | [dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md) Phase 4 深度章（Layer 3 · Interview） |
>
> 面向读者：前端开发者，熟悉 JavaScript / TypeScript / React，有少量 Node.js 经验，没有系统 Python 基础。

---

## 0. 阅读指南

### 这一章的目标是什么

读完 Phase 4（T0401 + T0402 + T0403 + T0404）后，你需要做到：

- 把 T0401 放回整个系统：理解"知识库管理"在 DX-RAG 里的位置，以及它为什么是"底层基础设施 → 业务 API 层"的转折点
- 能从三层视角说清"知识库到底是什么"：用户视角（容器）/ 领域模型（Collection）/ 存储实现（ChromaDB Collection + uploads 目录），并且**不把后两者混成同一个抽象层**
- 能画出 POST /api/collections 的完整链路，说清每一站"谁负责什么、谁不负责什么"
- 理解 file_count 为什么不在数据库里、而是每次由 Phase 1 的 `get_files()` 现场聚合出来——并意识到"Phase 1 不是学完就结束，Phase 4 正在消费它"
- 掌握 T0401 的核心工程原则：**Validation Before Side Effects**（校验必须在持久化副作用之前）
- 知道 T0401 开发期间真实发生过一次 **SPEC_CONFLICT**（旧 SPEC 允许部分中文 KB 名 → 真实 ChromaDB 不支持 → SPEC v1.6 patch），并能说出它的最小版本（第 11 节）
- 理解 T0404 的"函数先落地、验收后置"时序，并能推演 8 个边界用例各自被正则的哪一段拒绝/放行（第 8 节）
- 知道 `fullmatch` / `match` / `search` 三个函数的语义差，以及为什么校验必须全串锚定（第 8 节）
- 能画出 T0402 rename 的 7 步级联 + 补偿路径，说清**两层补偿**各自的作用域边界（第 9 节），以及"快照即补偿载荷"的由来
- 能说出 T0403 delete 为什么 Chroma 先删、为什么删除不做补偿、防御性路径检查防的是什么（第 10 节）
- 理解 keyword index 失效 seam 的设计：**T0402 先立契约（no-op 实现），T0602 再填实现**——"接口形状先于实现存在"（第 9 节）
- 知道去哪里看完整工程复盘（Engineering Review）和面试话术（Interview Guide）——三层文档各归其位

### 三种事实标记（贯穿全学习体系）

为了避免"项目事实"、"通用工程知识"、"未来设想"三类内容混在一起，本文档使用三种标记：

| 标记 | 含义 | 例子 |
|------|------|------|
| [PROJECT FACT] | DX-RAG 当前真实实现 / SPEC 规定的内容 | "v1.6 regex 不允许中文 KB 名" |
| [ENGINEERING KNOWLEDGE] | 通用软件工程知识（与具体项目无关） | "校验应先于副作用执行" |
| [FUTURE] | 当前没有实现，只是未来可能的方案 | "kb_id/display_name/storage_key 三身份模型" |

⚠️ 尤其注意：Milvus、PostgreSQL metadata store、分布式 Chroma、异步任务队列、kb_id/display_name/storage_key 拆分、事务协调器——**全部没有在 v1 实现**。它们只会在第 2 节、第 13 节及 Engineering Review 的 Future 区域出现。

### 本章阅读路线

| 章节 | 深度 | 说明 |
|------|------|------|
| 第 0 节 阅读指南 + 项目地图 | 🟢 必看 | T0401 给系统加了什么能力 |
| 第 1 节 Phase 4 定位与 T0401 分工 | 🟢 必看 | 为什么 Phase 1 有能力还不够 |
| 第 2 节 "知识库"到底是什么 | 🟢 必看 | 三层视角，本章最重要的心智模型之一 |
| 第 3 节 用前端开发者熟悉的方式理解 | 🟢 必看 | APIRouter / decorator / Pydantic 的 TS 类比 |
| 第 4 节 逐行精读 collections.py | 🟢 必看 | 321 行真实代码（T0401 81 行 + T0402/T0403 级联），每段的项目意义 |
| 第 5 节 POST 完整链路追踪 | 🟢 必看 | 从 HTTP 到 ChromaDB + 文件系统再回来 |
| 第 6 节 GET 与 file_count 的诞生 | 🟢 必看 | Phase 1 get_files 第一次被业务消费 |
| 第 7 节 Validation Before Side Effects | 🟢 必看 | T0401 的核心工程原则 |
| 第 8 节 T0404 名称验证正式验收 | 🟢 必看 | 8 边界用例矩阵 + fullmatch 三函数 + "验收后置"时序 |
| 第 9 节 T0402 Rename 级联与补偿 | 🟢 必看 | 7 步编排、两层补偿、storage-level cascade 契约 |
| 第 10 节 T0403 Delete 级联 | 🟢 必看 | 4 步删除、顺序论证、不可逆语义、防御纵深 |
| 第 11 节 SPEC_CONFLICT 学习摘要 | 🟢 必看 | 真实工程事件的最小版本（完整复盘在 Engineering Review） |
| 第 12 节 与前面 Phase 的连接 | 🟢 必看 | Phase 0/1 怎么被用上，Phase 2/3 为什么没参与 |
| 第 13 节 向后连接 | 🟡 建议理解 | T0401–T0404 全部完成，其余全部 Future，只连不教 |
| 第 14 节 只需记住的 10 件事 | 🟢 必看 | 心智模型，不背函数 |
| 第 15 节 三级自测 | 🟢 必做 | 15 题 + T0404 附加 3 题 + T0402/T0403 附加 6 题，答案在节末 |
| 第 16 节 动手练习 | 🟡 建议做 | 7 个不动业务代码的练习 |
| 第 17 节 Quick Review Card | 🟢 必看 | 一屏复习卡 |
| 第 18 节 Python 新知识索引 | 🟢 按需 | 指向 python-for-frontend-dev.md 第 26/27 节 |
| 第 19 节 诚实核对与学习边界 | 🟡 建议理解 | 三层事实对照 + 诚实 AC 立场 |
| 延伸：完整工程复盘（SPEC_CONFLICT 全案 / ADR-01~08 / 一致性缺口 / 规模分析） | 🟡 | [phase-04-engineering-review.md](./engineering-review/phase-04-engineering-review.md) |
| 延伸：面试表达（30 秒 / 1-2 分钟 / STAR / 12 追问 + 7 工程追问） | 🟢 | [dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md) Phase 4 深度章 |

### 三种学习深度标记

| 标记 | 含义 |
|------|------|
| 🟢 **入门理解** | 第一遍必须掌握的内容。用 TypeScript 类比 + 简单解释。 |
| 🟡 **项目理解** | 解释 DX-RAG 为什么这样设计。帮你理解架构决策。 |
| 🔵 **进阶阅读** | 可以以后回来看。不影响理解 T0401 的核心内容。 |

### 当前进度（2026-08-25）

- **T0401**: ✅ DONE — [collections.py](../../backend/app/api/collections.py)（创建 + 列表；路由注册在 [router.py](../../backend/app/api/router.py)）
- **T0404**（Name Validation 正式验收）: ✅ DONE —— canonical regex 边界用例正式验收（74/74 实测 PASS），与 SPEC v1.6 对齐（第 8 节）
- **T0402**（Rename）: ✅ DONE —— 2026-08-25 Learning Pass：7 步级联 + 两层补偿 + storage-level cascade（第 9 节）
- **T0403**（Delete）: ✅ DONE —— 2026-08-25 Learning Pass：4 步级联删除 + 不可逆语义 + 防御纵深（第 10 节）
- **Learning Pass + Engineering Review**: ✅ T0401（2026-08-24 三层拆分完成）+ T0404（2026-08-25 增量更新）+ T0402/T0403（2026-08-25 增量更新）—— 教材（本文档）/ 工程复盘（Engineering Review）/ 面试话术（Interview Guide）三层各司其职
- **流程环节**: ⬜ Phase Gate Review + Phase Learning Review —— 完成后再按 Interview Update Cadence 做 Interview Guide 的 Phase 级 consolidation

### 全景速览（Phase 4 现状——四个 Task 全部 DONE）

先回答"Phase 4 到底给 DX-RAG 增加了什么能力"，再进细节。 [PROJECT FACT]

```text
Phase 0   FastAPI / Config / Error / Schema（架子）
   │
   ▼
Phase 1   VectorStore（11 个 public methods——内部能力）
   │
   ▼
Phase 4   /api/collections（第一个业务 API）
   │
   ├── POST Create KB（创建知识库）
   │      ├── ChromaDB Collection（cosine / HNSW，Phase 1 提供）
   │      └── uploads/{name}/ 目录（文件系统，同步创建）
   │
   ├── GET List KB（列出知识库）
   │      └── file_count（现场用 Phase 1 的 get_files() 聚合）
   │
   ├── PUT Rename KB（改名 = 改身份，7 步级联）
   │      ├── VectorStore.rename_collection（storage-level cascade，存储级原子）
   │      ├── uploads/{old}/ → uploads/{new}/（文件系统改名）
   │      ├── keyword index 失效 seam（T0602 填实现）
   │      └── 只读校验 → 失败逆序补偿 → 500 RENAME_FAILED（全旧状态）
   │
   └── DELETE Delete KB（不可逆，4 步级联）
          ├── ChromaDB 先删 → uploads 目录递归删 → keyword index 失效
          └── 中途失败 → 500 INTERNAL_ERROR + 残余状态如实记日志（不假装恢复）
   │
   ▼
[FUTURE] Phase 5 Upload —— 会依赖现在创建出来的 KB（上传必须有目标）
[FUTURE] Phase 10/11 Frontend —— 会调用现在的 Collection API
```

一句话：**Phase 1 造好了"存储机器"，T0401 第一次把机器接上 HTTP 开关；T0402/T0403 随后给开关配上了"改名"和"删除"两个操作——并把跨系统副作用的一致性管理（补偿 / 顺序设计 / 诚实残余报告）第一次带进了项目。**

---

## 1. Phase 4 定位与 T0401 分工

### T0401 解决了什么问题

[PROJECT FACT] Phase 1（T0102/T0107）已经实现了：

```python
store.create_collection(name)      # vector_store.py:265
store.list_collections()           # vector_store.py:284
store.get_files(collection)        # vector_store.py:491
```

但它们只是**内部能力**——只能被代码调用，不能被 HTTP 请求调用。在 T0401 之前：

```text
用户 / 前端
    │  无法通过 HTTP 使用这些能力 ❌
    ▼
VectorStore（能力在，入口不在）
```

T0401 第一次把"内部存储能力"变成"产品 API 能力"：

```text
用户 / 前端
    │  POST /api/collections   GET /api/collections
    │  PUT /api/collections/{name}   DELETE /api/collections/{name}
    ▼
collections.py（HTTP 入口，321 行）
    │
    ▼
VectorStore（Phase 1 的 11 个 public methods）
```

> **T0401 是 DX-RAG 从"底层基础设施"进入"业务 API 层"的重要转折。** [PROJECT FACT]
> 在此之前，backend/app/api/ 目录下只有 router.py 里的一个 /health（Phase 0 的探针）。collections.py 是整个项目**第一个承载产品功能的 API 文件**。

### T0401 的范围边界

[PROJECT FACT] 按 TASKS.md T0401（L1207-1250）：

**做什么**（Implementation Scope）：
- `POST /api/collections`：validate name → check duplicate → create collection → create uploads dir → return 201
- `GET /api/collections`：list all collections → 对每个算出 file_count → 返回列表
- 在 router.py 注册路由

**不做什么**（Out of Scope，当时）：
- ❌ Rename（→ T0402，**现已完成，见第 9 节**）
- ❌ Delete（→ T0403，**现已完成，见第 10 节**）
- ❌ 名称验证的正式边界用例验收（→ T0404，现已完成，见第 8 节）

**验证目标**（Acceptance / Verification）：
- AC-F001-01：创建 "test-kb" → 201，ChromaDB collection 存在，uploads 目录被创建
- AC-F001-02：重复创建 "test-kb" → 409 `COLLECTION_ALREADY_EXISTS`
- GET /api/collections → 返回 name + file_count
- 响应格式与 SPEC Section 6.5 完全一致

**一个诚实的时序观察** [PROJECT FACT]：TASKS.md 里 T0401 的 Out of Scope 写着"Do NOT implement name validation logic inline (use shared validation from T0404)"——而 T0404 在任务序列里排在 T0401 **之后**。实际发生的顺序是：T0401 先落地模块级共享函数 `validate_collection_name`（collections.py:77-88，docstring 明说 "T0404 formalizes the edge-case verification"），随后 T0404 完成正式验收并标记 DONE（2026-08-25，见第 8 节）——**函数先造出来，正式验收留给排位在后的 Task**。这不是违规，是任务计划里"Dependencies: T0404 (may depend on shared validation function)"那个"may"的现实落地方式；值得记住：**当依赖项排在自己后面时，先造出对方需要的接口形状、把正式验收留给对方**，是常见且合理的做法。同样的时序在 T0402 的 keyword index seam 上第二次发生（TASKS 说 "may need to coordinate with T0602"——T0402 先立契约 no-op，T0602 填实现，见第 9.7 节）。

---

## 2. "知识库"到底是什么？——三层视角

这是 T0401 必须讲清楚的第一个核心问题。不要停留在"一个 ChromaDB Collection"。

### 第一层：用户视角

[ENGINEERING KNOWLEDGE] 对用户来说：

```text
知识库 = 用户组织一组相关文档的容器
```

例如：

```text
产品文档
技术规范
人事制度
```

用户的心智模型里，知识库是一个"文件夹"或者"工作区"——他们不需要知道里面发生了什么。

### 第二层：DX-RAG 领域模型视角

[PROJECT FACT] 在 DX-RAG 的领域模型（SPEC Section 7.2）里，知识库是：

```
Collection {
    name: str              # 唯一名称，3-50 字符，字母/数字开头结尾
    file_count: int        # 该知识库中的文件数
}
```

注意两个细节：

1. **name 是唯一键**——v1 里 Collection 没有独立的 kb_id，name 就是身份（Engineering Review 的 ADR-01/02 会讲为什么）。
2. **v1 不记录 created_at**——SPEC 7.2 的 Note 明确说："ChromaDB 自身不保证提供该字段，且 v1 API 不需要该字段。避免引入不必要的 metadata storage。"这就是 v1 的克制：**只建模当前 API 真实需要的字段**。

### 第三层：存储实现视角

[PROJECT FACT] 当前 v1 的存储实现（SPEC F001 Detail）：

```text
KB name
   │
   ├── ChromaDB collection name（同名）
   │
   └── uploads/{KB name}/ 目录（同名）
```

即 **1 KB = 1 个同名 ChromaDB Collection + 1 个 uploads/{name}/ 目录**。三者用同一个字符串绑定在一起。

### 本章最重要的心智模型

> **"知识库"是业务概念；ChromaDB Collection 是当前 v1 对这个业务概念的存储实现。** [ENGINEERING KNOWLEDGE]
> 不要把两者混成同一个抽象层。

为什么要分得这么清？因为这两层可以**独立演化**：

```text
业务概念（知识库）     → 稳定，用户永远有"组织文档的容器"这个需求
存储实现（ChromaDB）   → 可替换，未来可能换 Milvus [FUTURE]
身份策略（name 直作存储名） → 可演进，未来可能拆 kb_id/display_name/storage_key [FUTURE]
```

如果代码里到处把"业务知识库"和"ChromaDB Collection"当成一回事写死，替换存储引擎时就得改遍所有业务代码。DX-RAG 的对策是 Phase 1 的 VectorStore 抽象层（F008）：业务 API 只认识 `create_collection(name)` 这种**业务动词**，不认识 ChromaDB SDK——Engineering Review 第 4 节 Data Ownership 会展开。

[FUTURE] 企业级产品将来可能会拆成：

```text
kb_id        = 稳定的内部身份（UUID，不可变）
display_name = 用户可见的名字（可改、可中文、可重复）
storage_key  = 基础设施安全的名字（给 ChromaDB / 目录用）
```

**但现在 v1 没有这么做**——v1 刻意选择了 1 KB = 1 同名 Collection 的最简模型。为什么？Engineering Review 的 SPEC_CONFLICT 案例（第 6 节）与 ADR-02 有完整答案。

---

## 3. 用前端开发者熟悉的方式理解

先建立类比地图，再读真实代码。⚠️ 类比都是"接近但不完全等价"——每个类比下面会标注差异。

### 3.1 APIRouter ≈ Express Router / Next.js route handler 的路由层概念

**TS 侧**（不完全等价）：

```ts
// Express
const collectionsRouter = express.Router();
collectionsRouter.post("/collections", handler);
app.use("/api", collectionsRouter);

// Next.js App Router
// app/api/collections/route.ts → export async function POST() {...}
```

**Python 侧真实代码**（router.py:5,14；main.py:68）：

```python
api_router = APIRouter()                       # router.py:5
api_router.include_router(collections_router)  # router.py:14
app.include_router(api_router, prefix="/api")  # main.py:68
```

**差异（必须知道）**：
- Express Router 的路由是**回调链**（req/res 手传）；FastAPI 的路由是**声明式函数**——函数签名就是契约，FastAPI 自己解析请求体、自己序列化返回值。
- Next.js App Router 用**文件路径约定**定义路由；FastAPI 用**装饰器字符串**定义路由（`@router.post("/collections")`）。
- FastAPI 的 Router 还能携带 `prefix` / `tags` / `dependencies` 等元数据，比 Express Router 更"配置化"。

### 3.2 路由装饰器 ≈ router.post(...) 注册调用

```python
@router.post("/collections", response_model=CollectionResponse, status_code=201)
def create_collection(body: CollectionCreate) -> CollectionResponse:
    ...
```

≈（概念上）：

```ts
router.post("/collections", zodValidate(bodySchema), (req, res) => {
  // ...业务逻辑...
  res.status(201).json(serialize(responseSchema, result));
});
```

**差异**：Express 里"校验请求体、设置状态码、序列化响应"都是**手写在 handler 里的代码**；FastAPI 里它们是**装饰器参数 + 类型标注**——框架自动完成。`response_model=CollectionResponse` 还自动做了一件事：**响应也会被校验和过滤**——handler 返回的 dict 里即使多出字段，也会被 CollectionResponse 裁剪成契约形状。这同时是 FastAPI 的强项（省代码）和代价（框架魔法多，出问题时得理解框架行为——见 Engineering Review 第 7.4 节的 Finding #3）。

### 3.3 Pydantic Request Schema ≈ TS interface + zod 运行时校验

```python
class CollectionCreate(BaseModel):      # schemas.py:32
    name: str = Field(description="...")
```

≈：

```ts
const CollectionCreateSchema = z.object({
  name: z.string(),
});
type CollectionCreate = z.infer<typeof CollectionCreateSchema>;
```

**差异**：TS 的 `interface` 只在编译期存在；Pydantic 模型是**运行时对象**——FastAPI 会在请求进来时真实验证 JSON body。所以 Python 侧不需要单独写"zod 层"，schema 定义即校验。

### 3.4 AppError ≈ 业务异常 + 全局 error middleware

```python
raise AppError("INVALID_COLLECTION_NAME")   # collections.py:87
```

≈：

```ts
throw new BusinessError("INVALID_COLLECTION_NAME");
// + 一个全局 error middleware 把它翻译成 { error: { code, message } }
```

DX-RAG 的"全局 error middleware"是 main.py:43-51 的 `@app.exception_handler(AppError)`——Phase 0 建的，现在第一次被业务端点真正用上（第 12 节）。

### 3.5 一张对照表：HTTP 端点开发的六个关注点

| 关注点 | Express / Node 侧 | FastAPI / T0401 侧 |
|--------|------------------|-------------------|
| request schema | zod / joi 手动调 | `body: CollectionCreate` 类型标注自动验 |
| response schema | 手写 res.json | `response_model=CollectionResponse` 自动序列化+裁剪 |
| status code | `res.status(201)` | `status_code=201` 装饰器参数 |
| business validation | handler 里 if/throw | `validate_collection_name()` 显式函数（仍手写，但位置固定） |
| service / storage call | 调 service 模块 | 调 VectorStore public interface（F008 边界） |
| error shape | error middleware | AppError + 全局 handler（Phase 0 建） |

---

## 4. 逐行精读 collections.py

T0401 时代这个文件只有 81 行；T0402/T0403 落地后现在共 **321 行**（rename 编排 + 补偿 120-246，delete 级联 254-321）。本节精读 T0401 部分的 81 行（行号已同步到当前文件），T0402/T0403 的新代码在第 9/10 节专讲。按"代码 → 人话 → 项目意义 → TS 类比 → 删掉会怎样"的结构过一遍。不逐行念语法——只挑真正决定行为的代码。

### 4.1 文件头：契约浓缩（collections.py:1-44）

```python
"""Knowledge Base Management API — create, list, rename, delete collections
(SPEC F001, Section 6.5).

T0401 + T0402 + T0403 scope:
  - POST /api/collections     — create a knowledge base
  - GET  /api/collections     — list knowledge bases with file_count
  - PUT  /api/collections/{name} — rename with full cascade + compensation
  - DELETE /api/collections/{name} — cascade delete (irreversible)

Create flow (SPEC F001 Detail, 5 steps):
  1. Validate name (canonical regex, 400 INVALID_COLLECTION_NAME)
  2. Check duplicate (409 COLLECTION_ALREADY_EXISTS)
  3. Create ChromaDB collection (VectorStore public interface, F008)
  4. Create uploads/{name}/ directory
  5. Return 201
...
"""
```

- **人话**：文件头把"这个模块实现什么、按什么顺序、不做什么"一次说清——现在包括 create/list/rename/delete 四条流。
- **项目意义**：这和 Phase 1/3 的文件头是同一个惯例——**文件头 = 浓缩契约**。任何读代码的人第一眼就能对照 SPEC F001 的五步，而不用去翻 SPEC。T0402 的 7 步 rename 流与 T0403 的 4 步 delete 流同样浓缩在文件头（第 9/10 节展开）。
- **删掉会怎样**：代码照跑，但"范围纪律"会丢——文件头明确标出每个 Task 的 scope，防止未来有人顺手把无关逻辑塞进来。

### 4.2 模块级正则常量（collections.py:70-74）

```python
# SPEC F001 canonical rule (v1.6 naming-compatibility patch): 3-50 chars,
# letter/digit at both ends, middle may contain letters, digits, _, -.
# No Chinese chars (ChromaDB collection names only accept [a-zA-Z0-9._-]),
# and no "." support by product decision.
_COLLECTION_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$")
```

- **人话**：把 KB 名称的合法规则编译成一个正则常量。拆解：
  - `^[A-Za-z0-9]` — 首字符：字母或数字
  - `[A-Za-z0-9_-]{1,48}` — 中间 1-48 个字符：字母/数字/下划线/连字符
  - `[A-Za-z0-9]$` — 末字符：字母或数字
  - 首(1) + 中(1~48) + 末(1) = **3~50 字符**
- **项目意义**：这是 SPEC v1.6 的 canonical regex——**它就是第 11 节 SPEC_CONFLICT 的最终产物**。注释里的三句话（v1.6 patch、无中文、产品决策不支持 `.`）就是这个常量的全部历史。8 个边界用例的逐条推演见第 8 节（T0404 正式验收）。它同时是"身份规则"：KB 名只能长这样，意味着 uploads/{name}/ 目录名和 ChromaDB collection 名也自动是文件系统安全的（`[A-Za-z0-9_-]` 在任何主流 OS 都是合法文件名字符——这间接为 Phase 5 的 path traversal 防线减负，也为 T0403 的防御性路径检查（第 10.4 节）提供了第一层保证）。
- **TS 类比**：`const COLLECTION_NAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$/;`——几乎逐字符对应。JS 的正则直接写字面量，Python 用 `re.compile()` 预编译成 Pattern 对象（预编译在本场景只是微优化 + 常量语义；语法见手册 26.3）。
- **删掉会怎样**：校验函数失去唯一事实来源，前后端规则漂移（SPEC F001 明确要求 frontend/backend 等价校验）。

### 4.3 校验函数（collections.py:77-88）

```python
def validate_collection_name(name: str) -> None:
    """SPEC F001 Create step 1: reject names outside the canonical rule.

    Shared by create (T0401) and rename (T0402).  T0404 formalizes the
    edge-case verification of this function.
    """
    if not _COLLECTION_NAME_PATTERN.fullmatch(name):
        raise AppError("INVALID_COLLECTION_NAME")
```

- **人话**：名字不满足正则 → 抛 400 错误；满足 → 静默返回 None。
- **项目意义**：
  1. **它是模块级函数而非 endpoint 内联代码**——因为 T0402（rename）也要用同一规则（docstring 明说 "Shared by create and rename"）。**把校验规则提炼成共享函数 = 让规则只有一个家**。
  2. **它只校验、不决策**——"名字不合法"它管；"名字合法但重复"它不管（那是第 2 步 duplicate check 的 409）。每个错误码有且只有一个抛出点。
  3. 返回 None 表示"通过"——Python 惯例：校验函数不返回布尔，通过就什么都不返回，失败就 raise。这与前端 `if (!valid) return error` 的返回式风格不同，是"异常式校验"。
- **TS 类比**：`function assertValidName(name: string): asserts name is string`——TS 的 assertion function 概念最接近（通过则类型收窄，失败则 throw）。
- **删掉会怎样**：非法名直接流进 ChromaDB——回到第 11 节的 500 事故现场。（T0404 已把这行函数的边界行为正式验收，见第 8 节。）

### 4.4 POST 端点（collections.py:90-101）

```python
@router.post("/collections", response_model=CollectionResponse, status_code=201)
def create_collection(body: CollectionCreate) -> CollectionResponse:
    """Create a knowledge base (ChromaDB collection + uploads directory)."""
    name = body.name
    validate_collection_name(name)
    store = ChromaVectorStore()
    if name in store.list_collections():
        raise AppError("COLLECTION_ALREADY_EXISTS")
    store.create_collection(name)
    uploads_dir = Path(settings.UPLOAD_DIR) / name
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return CollectionResponse(message="知识库创建成功", name=name)
```

逐行讲：

**第 90 行 — 装饰器**：

```python
@router.post("/collections", response_model=CollectionResponse, status_code=201)
```

- **人话**："把下面这个函数注册为 POST /api/collections 的处理器；它的返回值要按 CollectionResponse 校验并序列化；成功时 HTTP 状态码是 201。"
- **项目意义**：201（Created）不是默认的 200——SPEC Section 6.5 明确 Create 返回 201，所以装饰器里显式声明。**契约里的每个数字都有出处**（第 19 节三层对照会再核对）。
- **TS 类比**：`router.post("/collections", handler)` + handler 内 `res.status(201).json(...)`——Python 把"状态码"从函数体提到了装饰器参数（配置即声明）。

**第 91-92 行 — 请求体自动解析**：

```python
def create_collection(body: CollectionCreate) -> CollectionResponse:
```

- **人话**：FastAPI 看到 `body: CollectionCreate`，自动把 JSON body 解析成 Pydantic 对象；解析失败（缺 name / name 不是字符串）→ 422（框架默认行为，见 Engineering Review 第 7.4 节 Finding #3）。注意这里 Pydantic 保证的是**类型**（name 是 str），**不保证规则**（3-50 字符等）——规则是下一行的事。
- **项目意义**：**"类型校验归框架，规则校验归业务函数"**的分工，是 FastAPI 项目的标准姿势。

**第 94 行 — 校验（Step 1）**：

```python
    validate_collection_name(name)
```

- 非法 → `AppError("INVALID_COLLECTION_NAME")` → 全局 handler 翻译成 `400 {"error": {"code": "INVALID_COLLECTION_NAME", "message": "知识库名称格式无效", ...}}`（errors.py:43 的目录表提供 status+message）。

**第 95 行 — 每次请求新建 store**：

```python
    store = ChromaVectorStore()
```

- **人话**：每个请求进来都 new 一个 ChromaVectorStore（内部 new 一个 `chromadb.PersistentClient`）。
- **项目意义**：这是项目里**第三种实例化模式**——Phase 1 的调用方也这么干（每次操作 new 一个），Phase 2 的 embedding 是模块级懒加载单例，这里则是"每请求局部变量"。为什么 ChromaVectorStore 不搞单例？[ENGINEERING KNOWLEDGE] 因为 PersistentClient 本身是轻量句柄（ChromaDB 真正的持久化在磁盘），而**请求作用域的实例**避免共享状态、天然线程安全、生命周期清晰（请求结束即回收）。这个模式在手册 26.5 与 Phase 2 单例做对照。
- **TS 类比**：`const store = new ChromaVectorStore()`——在 handler 内部 new 依赖，等价于 Express handler 里 `const client = createDbClient()`。

**第 96-97 行 — 重复检查（Step 2）**：

```python
    if name in store.list_collections():
        raise AppError("COLLECTION_ALREADY_EXISTS")
```

- **人话**：把所有 collection 名拉出来，看目标名在不在里面；在 → 409。
- **项目意义**：
  1. **重复检查发生在任何持久化副作用之前**——第 7 节的核心原则。
  2. 用 `list_collections()` + `in` 是 O(n) 拉全表再查——[ENGINEERING KNOWLEDGE] 在 v1 的知识库数量规模（几十个）下完全合理，且**只有一条真实来源**（ChromaDB 自己就是 name 唯一性的裁判）；如果换成"查 ChromaDB get_collection 看抛不抛异常"反而把控制流交给异常，可读性更差。规模焦虑见 Engineering Review 第 8 节 Scalability Review。
- **删掉会怎样**：ChromaDB 对同名 collection 的 `create_collection` 会抛它自己的异常 → 不经过 AppError → 全局兜底变成 `500 INTERNAL_ERROR`，而契约要求 409——**错误码降级**。

**第 98 行 — 创建 Collection（Step 3）**：

```python
    store.create_collection(name)
```

- **人话**：通过 VectorStore public interface 创建 ChromaDB collection（内部用 cosine 距离 + HNSW，vector_store.py:265-274——Phase 1 T0102 的成果）。
- **项目意义**：**API 层不认识 ChromaDB SDK**——它只喊"创建知识库"这个业务动词。F008 约束 2/3：所有 ChromaDB 操作必须走 public interface，外部代码不得碰 `_client` 私有属性（Engineering Review 第 4 节 Data Ownership）。
- **TS 类比**：`await store.createCollection(name)`——service 层封装，controller 不直接写 SQL/DSL。

**第 99-100 行 — 创建目录（Step 4）**：

```python
    uploads_dir = Path(settings.UPLOAD_DIR) / name
    uploads_dir.mkdir(parents=True, exist_ok=True)
```

- **人话**：拼出 `uploads/{name}` 路径（`/` 运算符是 Path 的路径拼接），创建它；`parents=True` 连中间的 `uploads/` 一起建；`exist_ok=True` 表示"已存在不算错"。
- **项目意义**：
  1. `settings.UPLOAD_DIR = "uploads"`（config.py:41）是相对路径——`parents=True` 让第一次创建任何 KB 时顺带把 `uploads/` 本身也建出来。
  2. 为什么创建 KB 时要**同时**创建目录？因为 F001 数据模型规定 KB = Collection + 目录一体——目录是 Phase 5 上传落盘的位置，**在 KB 出生时就备好**，避免"上传时才建目录"把目录创建失败的风险挪到上传路径上。
  3. ⚠️ `exist_ok=True` 有隐藏语义：如果目录已存在（比如上次失败的残留孤儿目录）会**静默合并**——这是 Engineering Review 第 7.3 节一致性分析要诚实面对的点。
- **TS 类比**：`fs.mkdirSync(path, { recursive: true })`——`recursive` ≈ `parents`；但 Node 的 mkdirSync 没有 `exist_ok`，目录已存在会抛错（要自己包 try 或先 existsSync 判断）。

**第 101 行 — 返回（Step 5）**：

```python
    return CollectionResponse(message="知识库创建成功", name=name)
```

- **人话**：构造响应模型并返回；FastAPI 按 `response_model=CollectionResponse` 序列化，状态码 201。
- **项目意义**：响应 shape 与 SPEC 6.5 逐字段一致——`message`（人话："知识库创建成功"）+ `name`（回显）。注意：**没有 file_count、没有 created_at**——因为契约里就没有（第 2 节）。

### 4.5 GET 端点（collections.py:104-112）

```python
@router.get("/collections", response_model=CollectionListResponse)
def list_collections() -> CollectionListResponse:
    """List all knowledge bases with per-collection file_count."""
    store = ChromaVectorStore()
    items = [
        CollectionItem(name=name, file_count=len(store.get_files(name)))
        for name in store.list_collections()
    ]
    return CollectionListResponse(collections=items)
```

- **人话**：拉出所有 collection 名，对每个名字：调 `get_files()` 拿到该知识库的文件记录列表，`len()` 就是文件数；组装成 `CollectionItem` 列表返回。
- **项目意义**：
  1. **GET 装饰器没有 status_code**——默认 200，契约如此。
  2. **file_count 是现场算出来的**，不是存储的字段——第 6 节专讲。
  3. 列表推导（`[f(name) for name in ...]`）是 Phase 3 T0306 教过的 Python 知识（手册 23.3），这里第一次出现在 API 层——**Phase 3 的 Python 技能在 Phase 4 自然复用**。
- **TS 类比**：

```ts
const collections = await store.listCollections();
const items = collections.map(name => ({
  name,
  file_count: (await store.getFiles(name)).length,
}));
return { collections: items };
```

——几乎逐行对应，只是 Python 版没有 await（同步 I/O）。
- **删掉会怎样**：GET 返回空壳列表（只有名字没有文件数），前端 KB 列表页就失去了"每个库有多少文档"的信息——SPEC 6.5 的响应示例里 file_count 是必须字段。

---

## 5. POST /api/collections 完整链路追踪

把一次创建请求从 HTTP 走到 ChromaDB + 文件系统，再走回 HTTP。每一站标注"谁负责什么 / 谁不负责什么 / 为什么这样分"。 [PROJECT FACT]

```text
POST /api/collections
        │
        ▼
① FastAPI app（main.py:22）
   负责：接收 HTTP，路由到 api_router
   不负责：任何业务
        │
        ▼
② api_router（router.py:5，经 main.py:68 挂 /api 前缀）
   负责：把请求转给 collections_router
   不负责：路径细节（/collections 由子 router 自己声明）
        │
        ▼
③ collections router（collections.py:68）
   负责：声明 POST /collections 的 handler + response_model + 201
   不负责：校验、存储——它只是"声明"
        │
        ▼
④ CollectionCreate（schemas.py:32，FastAPI 自动解析 JSON body）
   负责：JSON → Pydantic 对象；类型校验（name 必须是 str）
   不负责：业务规则（3-50 字符等）——那是 validate_collection_name 的事
   失败 → 框架默认 422（见 Engineering Review 第 7.4 节 Finding #3）
        │
        ▼
⑤ validate_collection_name（collections.py:77）
   负责：name 是否符合 SPEC F001 canonical regex
   不负责：重复检查
   失败 → AppError("INVALID_COLLECTION_NAME") → 400
        │
        ▼
⑥ duplicate check（collections.py:96）
   负责：同名 KB 是否已存在
   不负责：创建
   失败 → AppError("COLLECTION_ALREADY_EXISTS") → 409
        │
        ▼
⑦ VectorStore.create_collection（vector_store.py:265）
   负责：把"创建知识库"翻译成 ChromaDB 调用（cosine/HNSW）
   不负责：目录、HTTP——它不认识 HTTP
   失败 → ChromaDB 异常上抛 → 全局兜底 500（见 Engineering Review 第 7.1 节 Failure Modes）
        │
        ├── ChromaDB: collection created ✅
        │
        ▼
⑧ uploads/{name}/ mkdir（collections.py:99-100）
   负责：在文件系统建原始文件目录
   不负责：ChromaDB（反之亦然）
   失败 → OSError 上抛 → 500（且 Collection 已存在——一致性 gap，见 Engineering Review 第 7.2 节）
        │
        └── Filesystem: uploads/{name}/ created ✅
        │
        ▼
⑨ CollectionResponse(message="知识库创建成功", name=name)
   负责：把结果塑形成 SPEC 6.5 的响应形状
        │
        ▼
HTTP 201
```

**为什么职责这样分**（三个要点）：

1. **框架管类型，业务管规则**（④ vs ⑤）：FastAPI/Pydantic 负责"这是不是一个 JSON 对象、name 是不是字符串"；"3-50 字符、首尾字母数字"是**产品规则**，属于 SPEC，必须落在业务代码里——这样换框架（[FUTURE] 理论上）产品规则不动。
2. **API 层管协议，VectorStore 管存储**（⑤⑥⑦ 之间）：HTTP 状态码、错误码、响应形状是 API 层的事；"怎么操作 ChromaDB"是 VectorStore 的事。中间的接口就是 Phase 1 的 11 个 public methods——**第 12 节会看到这是 Phase 1 的契约第一次被兑现**。
3. **两个持久化副作用由同一个 endpoint 编排**（⑦⑧）：数据库世界的"事务"直觉在这里不成立——ChromaDB 和文件系统是两个独立系统，中间没有任何 ACID。所以顺序很重要（第 7 节），一致性问题必须诚实面对（Engineering Review 第 7.2 节）。

---

## 6. GET /api/collections 数据从哪里来——file_count 的诞生

### 6.1 file_count 不是独立维护的字段

[PROJECT FACT] SPEC 7.3 Persistence Strategy 明确规定：v1 不引入 SQLite/PostgreSQL/Redis metadata store。File-level metadata（file_size、upload_time、ingestion_status）**冗余存储在该文件每个 chunk 的 ChromaDB metadata 里**。

所以"一个知识库里有几个文件"没有地方存——它只能**现场算**：

```text
collection
  ↓
get_files()（vector_store.py:491）—— Phase 1 T0107 的成果
  ↓
col.get(include=["metadatas"])        取该 collection 全部 chunk 的 metadata
  ↓
按 file_id group/deduplicate           同文件的 N 个 chunk 收敛成 1 条文件记录
  ↓
得到 files: List[Dict]（每条含 file_id/file_name/size/upload_time/chunk_count/status）
  ↓
len(files)                             ← T0401 加的这一步
  ↓
file_count
```

真实代码（collections.py:110）：

```python
CollectionItem(name=name, file_count=len(store.get_files(name)))
```

### 6.2 这为什么是"很值得学习的地方"

1. **派生数据 vs 存储数据** [ENGINEERING KNOWLEDGE]：file_count 是**派生数据**——它可以从已有数据（chunk metadata）计算出来，所以 v1 选择不算独立字段。派生数据的优点：永远一致（不存在"计数器忘了加一"）；代价：每次都要算（Engineering Review 第 8 节的规模分析）。
2. **Phase 1 不是学完就结束**：Phase 1 的 `get_files()`（T0107，按 file_id 聚合去重）当时看起来只是 VectorStore 的 11 个方法之一，现在它**第一次被真实业务 API 消费**。这是解决"每个 Phase 看完容易忘"的核心：**基础设施方法的价值在消费它的那一刻才显形**。
3. **一个空知识库的 file_count = 0 是怎么来的**：空 collection 的 `col.get()` 返回空 metadatas 列表 → `get_files` 返回 `[]` → `len([]) == 0`。整条链路上没有任何特殊分支——**空集合自然推导出 0**，这是列表聚合设计的优雅处。

### 6.3 反向想一下：如果 v1 有 metadata DB 会怎样

[FUTURE] 如果有 SQLite 存 FileRecord 表，GET 就是一条 `SELECT count(*) WHERE collection_name = ?`——快，但要维护两张表的一致性（上传成功写 Chunk 也要写 File 表、删除要两边删）。v1 用"反规范化 + 现场聚合"换掉了这套一致性负担。**权衡的本质：用查询时的计算成本，换写入时的一致性成本**。什么时候这个权衡翻转？文件数 × chunk 数大到每次 GET 都全量扫 metadata 不可接受时——Engineering Review 第 8 节。

---

## 7. Validation Before Side Effects（校验先于副作用）

这是 T0401 的核心工程原则之一。用真实链路讲。

### 7.1 错误顺序长什么样

```text
❌ 错误顺序：
   先创建 ChromaDB collection
    ↓
   再发现 name 不合法
    ↓
   请求失败（400）
   ——但系统状态已经改变（一个垃圾 collection 留在了 ChromaDB 里）
```

```text
✅ 正确顺序（F001 Create 五步就是按这个排的）：
   Step 1 Validate（400 出口）
   Step 2 Duplicate Check（409 出口）
   Step 3 Create ChromaDB collection   ← 从这里才开始有副作用
   Step 4 Create uploads dir           ← 第二个副作用
   Step 5 Return 201
```

[ENGINEERING KNOWLEDGE] 原则：**所有可能拒绝请求的检查，都放在第一个持久化副作用之前**。副作用之前的拒绝是"免费的"——系统状态没变，重试即可；副作用之后的拒绝是"昂贵的"——要么写补偿代码，要么留下脏状态。

### 7.2 用 "a中b" 走两条路径

[PROJECT FACT] 这正是 T0401 期间真实发生过的场景（第 11 节学习摘要；完整复盘见 Engineering Review 第 6 节）：

```text
旧规则（SPEC v1.5）时代："a中b" 是合法输入
    │
    ▼
validate_collection_name → PASS（旧正则允许中间有中文）
    │
    ▼
ChromaDB create_collection → FAIL（ChromaDB collection name 只接受 [a-zA-Z0-9._-]）
    │
    ▼
unhandled dependency exception → 全局兜底 → 500 INTERNAL_ERROR
    │
    契约说该输入应成功，却 500 —— 且 ChromaDB 里没有残留（创建失败），
    但用户体验是"合法名字却服务器错误"
```

```text
新规则（SPEC v1.6）时代："a中b" 在 validation 层直接被拒
    │
    ▼
400 INVALID_COLLECTION_NAME（明确、可预期、错误信息清晰）
    │
    系统状态从未被触碰
```

### 7.3 这个原则比"防用户输错"大得多

> 输入校验不只是"防止用户输错"，它也是**保护系统状态边界**的一部分。 [ENGINEERING KNOWLEDGE]

三个递进的层次：

1. **体验层**：400 "知识库名称格式无效" 比 500 "服务器内部错误" 对用户友好得多——后者会让用户以为系统坏了，且日志里出现一个根本不需要出现的 traceback。
2. **状态层**：校验发生在副作用之前，意味着"被拒绝的请求 = 零副作用的请求"——系统永远干净。
3. **契约层**：把"什么名字合法"收进校验函数，等于把**第三方依赖的约束**（ChromaDB 命名规则）翻译成**产品自己的规则**，在系统边界处拦截，而不是让依赖的异常穿透到用户面前。

[FUTURE] 这个原则在 Phase 5 会再次出现：TASKS.md T0501（L1436）要求"Validation happens BEFORE any file system write"——T0501 的六步校验管道（扩展名 → 大小 → 空文件 → 路径穿越 → KB 存在 → 重复）同样是"全部检查完才落盘"。**T0401 的 400/409 顺序，就是 Phase 5 六步管道的预演。**

---

## 8. T0404 — Collection Name Validation 正式验收（2026-08-25 Learning Pass）

### 8.1 T0404 到底做了什么——先讲清一个"奇怪"的时序

[PROJECT FACT] 按 TASKS.md 的任务序列，T0404 排在 T0401 **之后**（TASKS.md L1361）。但打开代码会发现：`validate_collection_name`（collections.py:77-88）在 T0401 实现时就已落地，docstring 里写着 "T0404 formalizes the edge-case verification of this function"。

所以 T0404 的真实工作不是"写一个新函数"，而是三件事：

1. **正式化边界用例验收**——把 TASKS.md T0404 验收表里的 8 个用例（TASKS.md L1390-1397）逐条与 SPEC v1.6 canonical regex 对齐，并扩大到合法/非法两侧共 15 个名字用例的实测（74/74 checks PASS，见 8.4）
2. **验收表与 SPEC 同步**——v1.5 时代验收表写"测试-kb → accepted"，v1.6 收紧后改为 rejected，并新增"a中b"用例（这个更新发生在 v1.6 patch 的回归阶段，见 Engineering Review 6.10）
3. **标记 DONE**——TASKS.md T0404 Status: TODO → DONE

> 一句话：**T0404 没有新增一行功能代码——它做的是把 T0401 提前交付的共享校验函数，正式验收为 SPEC v1.6 契约。** [PROJECT FACT]
> 任务价值不在代码量，在契约的确定性：从此每个边界输入都有唯一、可推演的答案。

这个时序本身也是第 1 节诚实观察（L170）的落地版：**依赖项排在自己后面时，先造出对方需要的接口形状，把正式验收留给对方**。

### 8.2 边界用例矩阵——8 个用例为什么这样判

[PROJECT FACT] 验收表（TASKS.md L1390-1397）逐条拆解。正则：`^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$`（三段：首 1 + 中 1~48 + 末 1 = 3~50 字符）。

| 输入 | 结果 | 为什么（指到正则的哪一段） |
|------|------|---------------------------|
| `a` | ❌ 400 | 只有首字符，没有"中间段"和"末字符"——总长 3 是下限 |
| `ab` | ❌ 400 | 首 `a` + 末 `b` 都对，但中间段 `{1,48}` 至少需要 1 个字符——`ab` 只有 2 段 |
| `a-b` | ✅ 通过 | 首 `a` + 中 `-`（1 个）+ 末 `b` = 3 字符，正好顶住下限 |
| `-bad` | ❌ 400 | 首字符必须是 `[A-Za-z0-9]`，连字符只被允许在中间段 |
| `bad-` | ❌ 400 | 末字符必须是 `[A-Za-z0-9]`——同样的连字符，位置决定合法性 |
| `测试-kb` | ❌ 400 | `测试` 不在首字符类 `[A-Za-z0-9]`——v1.6 收紧的直接后果 |
| `a中b` | ❌ 400 | 中间字符 `中` 不在中间段字符类 `[A-Za-z0-9_-]`——v1.5 时代它被放行、撞上真实 ChromaDB 500 |
| 51 字符（如 `a`+`b`×49+`c`） | ❌ 400 | 首(1) + 中最多 48 + 末(1) = 50 是上限，第 51 个字符无处安放 |
| `a b`（含空格） | ❌ 400 | 空格不在任何一段的字符类里——`[A-Za-z0-9_-]` 之外一律拒绝 |
| `bad.dot`（含 `.`） | ❌ 400 | `.` 不在中间段字符类——v1.6 产品决策刻意排除 |

> 合法侧边界同样要测（2026-08-25 实测覆盖）：`kb1`（数字开头）、`a_b`、`a1x-b2`、50 字符上限（`a`+48 中间字符+`b`）全部通过——**合法与非法两侧的边界都测，不是只测拒绝**（实测记录见 8.4）。

两个容易漏掉的推论：

- **数字开头/结尾是合法的**——`[A-Za-z0-9]` 包含数字，`3kb` 是合法 KB 名。SPEC 原文写的是"字母或数字开头结尾"（F001），regex 与之一致。
- **`.` 被刻意排除**——ChromaDB 本身接受 `.`，但 v1.6 产品决策不放宽（SPEC patch note）。[ENGINEERING KNOWLEDGE] 值得记住的工程判断：**"存储层允许什么"从来不是"产品允许什么"的上限**——产品规则可以比存储约束更窄。

### 8.3 为什么 `fullmatch` 而不是 `search`（这次真的学会这三个函数）

[PROJECT FACT] collections.py:86 用的是 `_COLLECTION_NAME_PATTERN.fullmatch(name)`。Python 的 re 模块有三个长得像但语义不同的入口：

| 函数 | 语义 | 类比 |
|------|------|------|
| `re.fullmatch` | 整个字符串**从头到尾**全部匹配 | JS 的 `/^...$/` + `.test()` |
| `re.match` | 从**开头**匹配（允许尾部剩余） | JS 的 `/^.../` |
| `re.search` | **任意位置**找到即返回 | JS 默认的 `.test()`（部分匹配） |

校验场景必须用 `fullmatch`（或等价的全串锚定）：**"名字必须整个合法"≠"名字里只要有一段合法"**。如果换成 `search`，校验的是"这串字符里是否存在一段像 KB 名的部分"——语义完全错了。

但注意一个诚实的细节：项目里的正则本身带有 `^` 和 `$` 锚点（collections.py:74），所以即使误用 `search`，结果也不会错——锚点已经保证了全串匹配。`fullmatch` + `^$` 是**双保险 + 显式意图**：锚点把"全匹配"写进正则文本，`fullmatch` 把"全匹配"写进调用点，读代码的人在两个位置都能看到同一个意图。

（`re.fullmatch` 与 JS `.test()` 的默认行为差异在手册 26.3 已讲，这里不重复。）

### 8.4 验证证据与诚实立场

[PROJECT FACT] T0404 的验收实测（2026-08-25）：**74/74 checks PASS**（real TestClient + real ChromaDB + real filesystem，临时目录，脚本已删除）。

- **6 个 valid 通过**：`test-kb` / `kb1` / `a-b` / `a_b` / `a1x-b2` / 50 字符边界（`a` + 48 中间字符 + `b`）
- **9 个 invalid 全部 400 `INVALID_COLLECTION_NAME`**：`a` / `ab` / `-bad` / `bad-` / `a b` / 51 字符 / `bad.dot` / `a中b` / `测试-kb`
- **Side-effect boundary（可观察证明）**：失败全部发生在 validation layer（collections.py:94 先于任何 store/目录操作）；每个 invalid 拒绝后无 ChromaDB Collection、无 uploads 目录；最终持久化世界恰好 = 5 个 valid KB（collection 列表、目录树、计数三方交叉验证）
- **单一实现点**：regex 只存在于 collections.py:74；backend 无重复 validation，frontend 无 validation（F017 等价校验 → T1101）
- **错误契约**：400 + `{error: {code, message, details}}` 信封，消息来自 errors.py:43 目录表

诚实声明：

- AC-F001-03 归属 T0404（TASKS.md L2871）——按 TASKS.md DONE + 上述实测记录 PASS，**不虚构额外的 PASS**。
- **脚本已删除**：验证跑过、但未固化——Engineering Review Finding #4 对 T0404 的表述因此更精确：**"验证发生过，但回归没有自动化保障"**。

### 8.5 TS 类比与 F017：一份规则，两处实现

[PROJECT FACT] SPEC F017 要求前端使用**等价校验**（T1101 落地，届时在 `frontend/lib/validators.ts` 建 TS 版）。TS 等价写法：

```ts
const COLLECTION_NAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$/;
function assertValidName(name: string): void {
  if (!COLLECTION_NAME_PATTERN.test(name)) throw new Error("INVALID_COLLECTION_NAME");
}
```

注意两个细节：

- **正则语法逐字符一致**——正则是一门跨语言技能，Python 和 JS 在这里的差异只有 API 形状（`fullmatch` vs `test`），没有语义差异。
- **[FUTURE] 漂移风险**：同一条规则存在两份代码（backend Python + frontend TS），中间没有机制性保障。当前防漂移靠"canonical regex 写在 SPEC 里"这条纪律；机制性方案（共享测试向量等）是 Engineering Review Pending #32。

### 8.6 Interview Candidates

> Candidate only — Phase Learning Review（2026-08-25）筛选结论：T0404 的候选问题与既有 P4Q5–P4Q7（校验/命名规则）重叠，未单独晋升；"任务排在依赖之后"的时序素材已并入 Interview Guide P4Q15（keyword seam 契约先行）。SPEC_CONFLICT 已在 T0401 时晋升 Guide（Phase 4 深度章），T0404 不再重复。

- **Technical Points**: `re.fullmatch` / `re.match` / `re.search` 三函数语义；正则作为跨语言技能的 TS/Python 对照；`{1,48}` 量词把"3-50 字符"表达成三段结构的思路；**证明"校验先于副作用"不靠读代码顺序，而靠可观察断言**——对每个 invalid 输入，拒绝后存储世界无任何痕迹（collection 列表 / 目录树 / 计数交叉验证）
- **Engineering Questions**: 校验规则为什么对齐**存储约束**而不是产品想象力（naming compatibility）；共享校验函数 = 规则的单一事实来源；"存储层允许 `.`" ≠ "产品允许 `.`"；**"验证类 Task 的代码资产已被前一 Task 提前交付，怎么办？"** → 不为 Task 而复制代码；本 Task 的价值 = formalize + 全边界用例证明 + Task 归属/状态同步。**Task 价值 ≠ 代码行数**
- **Candidate Interview Questions**: "为什么 KB 名不允许中文？" / "为什么 `a-b` 合法但 `a.b` 不合法？" / "这条正则怎么表达 3-50 字符的？" / **"50 字符为什么合法、51 为什么非法？"** → regex 三段结构 = 3-50 字符；边界测试不是猜数，是从 regex 结构推导（50 通过 + 51 拒绝都要测）
- **STAR Candidate**: 无新增（SPEC_CONFLICT STAR 已属 T0401）；可复用角度：**"任务排在依赖之后"的时序处理**（先交付接口形状、验收后置）——候选，待 Phase 4 完成时决定是否并入追问

---

## 9. T0402 — Rename：级联 + 补偿 + 原子性（2026-08-25 Learning Pass）

### 9.1 这个 Task 的复杂度为什么远超 T0401/T0404

一句话：T0401 是"两个副作用、无补偿"（Create 的一致性缺口诚实记录在 Engineering Review 7.2）；T0402 是**四类持久化步骤、任一步失败必须回到全旧状态**（AC-F001-06 原子性）。这是 SPEC 第一次对 Phase 4 提出**可观察原子性**要求——不是数据库事务（ChromaDB 和文件系统之间没有 ACID），而是"失败之后，从外部看什么都没发生过"。

[PROJECT FACT] TASKS.md T0402（L1254）的编排契约 → 真实代码 [collections.py:120-163](../../backend/app/api/collections.py#L120-L163)：

```python
@router.put("/collections/{name}", response_model=CollectionRenameResponse)
def rename_collection(name: str, body: CollectionRename) -> CollectionRenameResponse:
    old_name = name
    new_name = body.new_name
    validate_collection_name(new_name)

    store = ChromaVectorStore()
    if old_name not in store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")
    if new_name in store.list_collections():
        raise AppError("COLLECTION_ALREADY_EXISTS")

    vector_done = False
    uploads_done = False
    try:
        store.rename_collection(old_name, new_name)  # storage-level cascade
        vector_done = True
        _rename_uploads_dir(old_name, new_name)  # filesystem rename
        uploads_done = True
        invalidate_keyword_index(old_name)  # keyword index seam (D1)
        invalidate_keyword_index(new_name)
        _verify_rename(store, old_name, new_name)  # read-only verification
    except Exception as exc:
        _compensate_rename(store, old_name, new_name, vector_done, uploads_done)
        raise AppError("RENAME_FAILED") from exc

    return CollectionRenameResponse(
        message="知识库重命名成功", old_name=old_name, new_name=new_name
    )
```

### 9.2 7 步编排逐站讲解（谁负责什么）

1. **三个 4xx 全部前置**：`validate_collection_name(new_name)`（400）/ old 不存在（404）/ new 已占用（409）——**Validation Before Side Effects 在 rename 上的延伸**。因为它们都在 try 块**之前**，所以 4xx 永远不可能被映射成 500 RENAME_FAILED——每个错误码有且只有一个出口。
2. `store.rename_collection(old, new)` —— storage-level cascade（9.3）。这一步是**存储级原子**的：方法返回时 ChromaDB 状态要么全新名、要么全旧名。
3. `_rename_uploads_dir` —— 文件系统改名 `Path.rename`。注意语义：**rename 的源目录缺失 = 真实不一致**（必须失败），因为每个 KB 都该有自己的目录（9.5 与 delete 的对照）。
4-5. `invalidate_keyword_index(old_name)` + `(new_name)` —— **为什么两个都要**：old 名下若有索引缓存，内容已属于旧身份，必须失效；new 名下若有历史残留缓存（来自曾存在又删掉的同名 KB），也不能复用。当前是 no-op seam（9.7）。
6. `_verify_rename` —— 只读校验（9.4）。
7. 任何一步失败 → `_compensate_rename` 逆序补偿 → `raise AppError("RENAME_FAILED") from exc`——用户看到 500 + 可观察状态 = 完整旧状态。

### 9.3 存储级级联（vector_store.py:292-352）——SPEC v1.5 契约

[PROJECT FACT] 这是 F008 规定的"**唯一合法 metadata 写入路径**"（AC-F008-03：API/Service 层不得碰 `_collection` 私有属性，metadata 级联必须封装在 VectorStore 内部）。四个设计点：

1. **快照即补偿载荷**：改之前先把全部 chunk metadata 读出来（`col.get(include=["metadatas"])`）——这份旧 metadata 既是级联的源数据，也是失败时的恢复数据。**补偿不需要"记日志"，需要"记现场"**——这是 undo log 思想的最小实现。
2. **三步操作**：`col.modify(name=new_name)` 改 collection 名 → `get_collection(new_name).update(ids, new_metadatas)` 级联改每个 chunk 的 metadata。
3. **`source_file` 从 `file_name` 身份计算，不是字符串替换**：`f"uploads/{new_name}/{meta['file_name']}"`——只有 `collection_name` / `source_file` 两个字段变，`chunk_id` / `file_id` / `file_name` / `chunk_index` / content / embeddings 全不动（**无 re-ingest、无 UUID 再生**）。这就是第 1 节身份规则的兑现：**改名 = 改身份锚点，但 chunk 自己的身份不变**。
4. **方法内自补偿** `_restore_rename`（vector_store.py:354-390）：逆序恢复——先恢复全部 chunk 的旧 metadata（恢复目标是 `new_name` 还是 `old_name` 取决于正向 rename 是否已发生），再把 collection 名改回。**双重失败（正向 + 补偿都失败）logged not masked**——这是诚实的边界声明，不是缺陷。

TS 类比：`{...meta, collection_name: newName}` 的对象展开合并（`**meta` 的 JS 对应物）；补偿 ≈ saga 的 compensating action；快照 ≈ undo log。

### 9.4 只读校验（_verify_rename，collections.py:180-210）

- 只调 VectorStore **public read APIs**（list_collections / list_chunks）——绝不用 read API 当写入路径（TASKS Out of Scope 的明确禁令，AC-F008-03 的边界）。
- 校验三项：old 已不存在 / new 已存在 / 每个 chunk 的 `collection_name` 与 `source_file` 都指向新名字。
- 校验是**验证层**而非**修复层**：发现问题就抛 RuntimeError，交给补偿层去回滚——**校验绝不自己动手修数据**。
- 成本：O(该 KB 全部 chunks)——这是 rename 比 create 贵的根源（规模分析见 ER 第 8 节）。

### 9.5 两层补偿 vs 一层补偿：为什么分两处

| 层 | 位置 | 补偿什么 | 边界 |
|----|------|---------|------|
| 存储级 | vector_store.`_restore_rename` | `modify` + `update` 两步的内部失败 | 方法返回时 ChromaDB 必为全旧或全新（F001 存储级原子性） |
| 编排级 | collections.`_compensate_rename` | uploads 目录及后续步骤的失败 | 逆序（先目录回退、后存储回退）；keyword invalidation **不回滚**（F001：失效无恢复要求）；补偿失败 logged not masked |

两层各管各的作用域——这正是 ER 预检 PF-2（"子原子性归属未定"）的最终答案：**实现选择了"两个都要"**。为什么不能只有一层？

- 只有编排层 → `rename_collection` 内部失败时 ChromaDB 会留在半改状态（collection 已改、metadata 半改），而 API 层不能碰 `_collection`（F008）——**够不着，也没资格修**。
- 只有存储层 → uploads 目录改名失败时，API 层没有任何手段恢复存储侧。

[ENGINEERING KNOWLEDGE] 通用原则：**补偿代码的位置必须与它要恢复的资源的所有权一致**——谁拥有资源，谁负责恢复它。

### 9.6 RENAME_FAILED 的语义与例外链

- RENAME_FAILED 是 Phase 0 就建好的错误码（errors.py:46）——ER 预检 PF-5 记录的"零 raise 点"在此兑现，**无需改错误目录**。T0402 涉及的 4 个契约错误码（400/404/409/500）在 Phase 0 全部已存在。
- `raise AppError("RENAME_FAILED") from exc`：`from exc` 把底层异常挂到 `__cause__`（≈ JS 的 `Error` cause 属性）——日志里能同时看到"业务错误"和"根因链"两层。手册 18.4 讲过 `raise from`（T0201 第一次用），这里是项目第二次使用。
- 4xx 不会被映射成 RENAME_FAILED：它们全部发生在 try 块之前（第 9.2 节第 1 点）。

### 9.7 keyword index 失效 seam——"接口形状先于实现存在"

[PROJECT FACT] TASKS.md T0402 Dependencies 写着 "Phase 6 (keyword index — invalidation call, may be via shared cache reference)"——Phase 6 排在 T0402 **之后**。于是 T0402 新建了 [keyword_index.py](../../backend/app/services/keyword_index.py)（44 行，其中实现只有 1 行 no-op），定义契约：

```python
def invalidate_keyword_index(collection_name: str) -> None:
    # T0602: mark this collection's in-memory index dirty here.  Until
    # the Phase 6 index exists there is no cache to invalidate — no-op.
    return None
```

契约四要素（写进 docstring）：单 collection 作用域 / 幂等 / 索引不存在即 no-op / 真实失效失败时 raise（由 rename 编排捕获 → 补偿 → RENAME_FAILED）。当前函数体是**文档化的 no-op**——没有索引可失效，`None` 返回即契约满足。T0602 会替换函数体为真实的 dirty-flag 失效。

这就是第 1 节"依赖项排在自己后面"模式的**第二次发生**：T0404 是"函数先落地、验收后置"，keyword seam 是"**契约先落地、实现后置**"。两者共性：**先造出对方需要的接口形状**，让排在后面的 Task 只需填实现。真实 keyword-index 集成的验收 DEFER 至 T0602（ER PF-1 的答案）。

### 9.8 TS 类比

- 整体结构 ≈ Express handler 里的 try/catch + 补偿函数数组（`undoSteps.reverse().forEach(f => f())`）。
- `Path.rename` ≈ `fs.renameSync`（⚠️ 差异：目标已存在时行为平台相关——Windows 上抛 FileExistsError/OSError，这正是 ER 预检 PF-3 的场景）。
- `raise AppError(...) from exc` ≈ `throw new AppError(msg, { cause: exc })`。
- 无 await——同步 I/O，补偿顺序即代码顺序（读代码就能推演回滚路径）。

### 9.9 Interview Candidates

> 已于 2026-08-25 Phase Learning Review 晋升 Interview Guide：P4Q13（级联 + 可观察原子性）、P4Q14（两层补偿边界）、P4Q15（双失效 + seam 契约先行）、EP4-8（快照即补偿载荷 + 只读校验）；预检先行素材见 ER 7.9。

- **Technical Points**: 两层补偿作用域划分（资源所有权决定补偿位置）；快照即补偿载荷（undo log）；source_file 身份计算（非字符串替换）；只读校验作为独立验证步骤；`raise from` 例外链；invalidate 双名调用
- **Engineering Questions**: "跨 ChromaDB + 文件系统怎么保证原子性？" → 可观察原子性 + 两层补偿 + 补偿失败怎么办（诚实：logged not masked，双重失败是已知边界）；"verify 步骤值不值 O(chunks) 的成本？"
- **Candidate Interview Questions**: "rename 失败后用户看到什么？"（500 RENAME_FAILED + 完整旧状态）；"为什么 keyword index 要失效两次（old + new）？"；"为什么补偿先回目录、再回存储？"（逆序）
- **STAR Candidate**: 无重大闭环事件（普通 Task）；ER 预检清单（PF-1~5）→ 实现的逐条对照，可作"**预检先行的工程习惯**"素材

---

## 10. T0403 — Delete：级联删除 + 不可逆语义（2026-08-25 Learning Pass）

### 10.1 4 步流程（collections.py:254-291）

[PROJECT FACT] TASKS.md T0403（L1317）→ 真实代码：

```python
@router.delete("/collections/{name}", response_model=CollectionResponse)
def delete_collection(name: str) -> CollectionResponse:
    store = ChromaVectorStore()
    if name not in store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    chroma_deleted = False
    try:
        _assert_safe_uploads_target(name)  # validation, no side effect
        store.delete_collection(name)
        chroma_deleted = True
        _delete_uploads_dir(name)
        invalidate_keyword_index(name)
    except AppError:
        raise
    except Exception as exc:
        logger.exception(...)   # 结构化日志：chroma_deleted / uploads_dir_exists
        raise AppError("INTERNAL_ERROR") from exc

    return CollectionResponse(message="知识库删除成功", name=name)
```

逐站：

1. **存在性检查（404）**在任何破坏性操作之前——删一个不存在的 KB 连"检查"都不该有副作用。
2. `_assert_safe_uploads_target` —— 防御性路径检查，**无副作用**（10.4）。
3. **ChromaDB 先删**（10.2 顺序论证）。
4. `_delete_uploads_dir` —— `shutil.rmtree` 递归删除（10.5 缺失语义）。
5. keyword index 失效（seam，见 9.7）。

中途失败 → 500 INTERNAL_ERROR + 结构化日志（`chroma_deleted` / `uploads_dir_exists` 两个标志**如实记录残余状态**）——不补偿、不假装恢复。

### 10.2 为什么 Chroma 先删（顺序论证，T0403 D-1）

两个方向的中途失败形态对比：

| 顺序 | 最坏残余 | 危害 |
|------|---------|------|
| uploads 先删、Chroma 后删 | rmtree 半途失败 → **目录残缺但 KB 活着** | "活的 KB 缺文件"——用户数据看起来丢了，最坏形态 |
| **Chroma 先删、uploads 后删**（实现） | Chroma 失败 → 什么都没动（状态完好）；Chroma 成功后再失败 → 残留孤儿目录 | 孤儿目录无内容语义、可再删——**较轻的残余** |

结论：**顺序设计的目标不是"不失败"，而是"失败留下的残余最无害"**——这正是 ER 第 7.6 节 EP4-3（Engineering Question）说的"顺序设计"方案在本项目的真实落地。代码注释原文（collections.py:258-262）把这条论证直接写在了端点 docstring 里。

### 10.3 为什么删除不做补偿

- SPEC 6.5：删除**不可逆**（no undo / no recovery / no confirmation token）。
- 删除的目标状态是"不存在"——补偿 = 恢复已删数据，与不可逆语义**矛盾**；而且 ChromaDB 的 delete 之后没有"undo"原语可用。
- 所以中途失败的诚实策略是：**如实报告残余状态**（结构化日志记录 `chroma_deleted` 标志），而不是假装干净或试图"恢复"。

[ENGINEERING KNOWLEDGE] 这不是缺陷，是"不可逆操作 + 无事务协调器"下的最优诚实姿势：**失败后的第一义务是让残余状态可枚举**（日志里有答案），第二义务才是清理（手动或未来的一致性扫描，见 ER 第 8 节）。

### 10.4 `_assert_safe_uploads_target` —— 防御性路径检查（collections.py:294-308）

- `Path.resolve()` 消除 `..` 等符号成分 → 检查 resolved target 的 parent 必须等于 resolved upload root；不等 → RuntimeError。
- 为什么需要？v1.6 regex 已保证 API 创建的名字不含路径分隔符（第 4.2 节），404 检查又挡在前面——所以这里防的是**手工污染存储**（外部直接改 ChromaDB 塞进恶意 collection 名）的异常场景。
- [ENGINEERING KNOWLEDGE] **防御纵深（defense in depth）**：每一层都假设内层可能被绕过——regex 是第 1 层，404 是第 2 层，路径解析检查是第 3 层。删除是破坏性操作，多一层校验的代价（一次 resolve + 比较）远低于一次路径穿越事故。
- 失败形态：RuntimeError → 被外层 `except Exception` 捕获 → 日志 + INTERNAL_ERROR，**且发生在 delete_collection 之前——什么都没被碰**。

### 10.5 "目标状态决定缺失语义"——rename 与 delete 的对照

同一个现象（`uploads/{name}/` 目录不存在），两个 Task 的处理**相反**：

| 操作 | 目录不存在时 | 为什么 |
|------|------------|--------|
| rename（9.2 第 3 步） | **失败** → 补偿 → 500 RENAME_FAILED | 源目录是必须移动的对象——缺失是真实不一致 |
| delete（10.1 第 4 步） | **no-op**（`if target.exists()` guard） | 删除的目标状态是"不存在"——已不存在即满足 |

[ENGINEERING KNOWLEDGE] 语义跟随**操作的目标状态**，不跟随"目录"本身——这是幂等设计的最小形式（对照 T0308 的 `Path.unlink(missing_ok=True)`：同一思想第二次出现在项目里）。

另一个穿透细节：`except AppError: raise` —— 让 404 等业务错误**原样穿透**，不被 catch-all 映射成 INTERNAL_ERROR。≈ JS 的 `if (e instanceof AppError) throw e`。**catch-all 之前先放行自己认识的错误**。

### 10.6 Python 新知识与 TS 类比

- `shutil.rmtree(path)` ≈ `fs.rmSync(path, { recursive: true })`——递归删除整棵目录树。⚠️ 与 Node 不同：rmtree 对不存在的目录**抛 FileNotFoundError**（Node 的 `force: true` 静默跳过）——所以代码先 `if target.exists()` guard。
- `Path.resolve()` + `.parent` ≈ `path.resolve()` + `path.dirname()`——防御性路径检查的原料。
- `logger.exception(...)` ≈ `console.error(err)`（自动附带完整 traceback，比 `logger.error` 多一层堆栈）。
- `except AppError: raise` / `raise ... from exc` —— 见手册 18.4 / 27 节。
- 详细条目见第 18 节 Python 索引 + 手册第 27 节。

### 10.7 Interview Candidates

> 已于 2026-08-25 Phase Learning Review 晋升 Interview Guide：P4Q16（Chroma-first 顺序）、P4Q17（不补偿 + 目标状态语义）、P4Q18（防御纵深）。

- **Technical Points**: shutil.rmtree + exists guard；Path.resolve 防御纵深；"目标状态决定缺失语义"（rename vs delete 对照）；`except AppError: raise` 穿透模式
- **Engineering Questions**: "删除为什么不做补偿？" → 不可逆语义 + 无 undo 原语 + 诚实残余日志；"为什么 Chroma 先删？" → 残余形态对比；"404 检查之后为什么还要防御性路径检查？" → 防御纵深假设
- **Candidate Interview Questions**: "删除中途断电怎么办？" → 残余状态可枚举（日志里有 chroma_deleted 标志）、可清理（孤儿目录）；"delete 的孤儿目录和 Create 的孤儿 collection 是同类问题吗？"
- **STAR Candidate**: 无（普通 Task）

---

## 11. SPEC_CONFLICT — Learning Summary（精简版）

> 完整工程复盘（为什么不能 catch、BLOCKED 流程、7 维度 Option A/B 对比、三身份模型、仓库证据链、开发闭环）已迁移到 [Engineering Review](./engineering-review/phase-04-engineering-review.md) 第 6 节。本节只保留"学习 T0401 代码必需"的最小版本。

### 11.1 发生了什么

[PROJECT FACT] SPEC v1.5 时代，F001 的 canonical regex 是 `^[A-Za-z0-9][A-Za-z0-9_\-一-鿿]{1,48}[A-Za-z0-9]$`——名称**中间**允许中文字符，"a中b" 是 SPEC-valid 输入。但真实 ChromaDB 对 collection name 有自己的约束：只接受 `[a-zA-Z0-9._-]`。于是：

```text
SPEC validation PASS（"a中b" 合法）
    ↓
ChromaDB create_collection FAIL
    ↓
unhandled dependency exception → 500 INTERNAL_ERROR
```

而按产品契约该输入本应成功。所以这不是代码 bug（代码忠实地执行了 SPEC）——是**两个已冻结的要求无法同时成立**：要求甲（v1.5 允许中间中文）+ 要求乙（KB name 直接作 ChromaDB collection name）+ ChromaDB 第三方事实。

### 11.2 为什么会影响 T0401

因为 T0401 的 Step 1 校验规则**就是**这个 regex——校验规则的宽窄直接决定 Create 的 400/500 边界。规则比存储宽 → SPEC-valid 输入在存储层炸 500；规则与存储对齐 → 输入在边界处被 400 干净拒绝（第 7 节的 Validation Before Side Effects 由此得到保障）。

### 11.3 最终规则为什么变化

没有偷偷 catch 异常转 400（那等于实现者替产品缩窄名字空间），而是走 SPEC Freeze Policy：Task BLOCKED → 报告冲突 → 产品决策 → 收紧 regex（Option A：对齐存储约束）→ SPEC v1.6 patch → 回归验证 → DONE。产品同时决策：**不引入 KB 名称→存储名称映射层**（Option B 被否），**不因 ChromaDB 支持 `.` 而新增 `.` 支持**。当前正则（collections.py:74）：

```text
^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$   （3-50 字符，无中文，无 "."）
```

### 11.4 这个事件教会我什么

1. **mock 验证代码，真实依赖验证假设**——中文名冲突只有真实 ChromaDB 才暴露；如果 mock 掉 VectorStore，"a中b" 一路绿灯，冲突永远不会被发现。
2. **"会停下来报告问题"是工程能力，不是开发能力不足**——实现者能看见的约束永远少于产品/业务能看见的约束；"选一条自己觉得对的路偷偷走过去"会在上游决策变化时变成返工。
3. **产品规则应该比存储约束更窄**——"存储层允许什么"从来不是"产品允许什么"的上限。

### 11.5 去哪看完整版

- 完整工程复盘（为什么不能 catch 转 400、BLOCKED 流程、7 维度 Option A/B 对比、三身份模型、仓库证据链、开发闭环）→ [phase-04-engineering-review.md](./engineering-review/phase-04-engineering-review.md) 第 6 节
- 面试表达（STAR 故事 + 18 道高频追问 + 8 道工程深问）→ [dx-rag-interview-guide.md](./interview-notes/dx-rag-interview-guide.md) Phase 4 深度章

---

## 12. "T0401 使用了我之前学过的什么？"

> 解决"每个 Phase 看完容易忘"的核心章节：把 T0401 拆开，看它每一项能力来自哪个旧 Phase。

### Phase 0 → T0401：架子第一次承重

| Phase 0 建的 | T0401 怎么用 |
|-------------|-------------|
| FastAPI application（main.py） | POST/GET 请求的入口就是它 |
| router 结构（api_router + include_router + /api 前缀） | collections_router 挂进去（router.py:14） |
| Pydantic schemas（schemas.py） | `CollectionCreate` / `CollectionResponse` / `CollectionListResponse` 是 Phase 0 就定义好的模型，T0401 直接消费——**模型先行，端点后到** |
| AppError + 全局 exception handler | `raise AppError("INVALID_COLLECTION_NAME")` → 400 信封；`raise AppError("COLLECTION_ALREADY_EXISTS")` → 409 信封——Phase 0 的"错误机器"第一次被业务端点驱动 |
| Error catalog（errors.py:43-46） | 四个 Collections 错误码在 Phase 0 就在目录表里——T0401 第一次 raise 前两个（400/409），T0402 第一次 raise 后两个（404 COLLECTION_NOT_FOUND / 500 RENAME_FAILED，后者正是 ER 预检 PF-5 记录的"零 raise 点"） |

Phase 0 当时看起来像"搭架子"——现在它真正派上用场了：**端点不用写任何错误翻译代码，一个 raise 就得到完整契约错误**。

### Phase 1 → T0401：11 个 public methods 第一次被真实业务消费

| Phase 1 建的 | T0401 怎么用 |
|-------------|-------------|
| `create_collection()`（T0102） | POST 第 3 步——创建 ChromaDB collection（cosine/HNSW） |
| `list_collections()`（T0102） | POST 的重复检查 + GET 的遍历源 |
| `get_files()`（T0107） | GET 的 file_count（`len(get_files(name))`） |

三个方法 = T0401 的全部存储依赖。其余 8 个 public methods（search/add_texts/delete_by_file 等）在这个 Task 里没有被触碰——**每个 Task 只消费它需要的那几个契约**。

### Phase 2：本 Task 不使用 Embedding

[PROJECT FACT] T0401 **不使用** Phase 2。原因直白：**创建空知识库没有内容需要向量化**——没有文档、没有 chunk，就没有"文本 → 向量"这一步。Embedding 的第一次真实触发在 Phase 5 的 upload 链路（T0308 `IngestService.process` 内部，Phase 3 已实现但还没有 HTTP 入口）。

### Phase 3：本 Task 不触发 IngestService

[PROJECT FACT] T0401 **不触发** IngestService。因为：

> **创建 KB ≠ 上传文件。** [PROJECT FACT]

这是两个不同的生命周期，被 SPEC 刻意分开：

```text
KB 生命周期（Phase 4）:     create → rename → delete
文档生命周期（Phase 5/9）:  upload → ingest → list/preview/delete
```

但它们有一个**交汇点**：`uploads/{name}/` 目录。T0401 在 KB 出生时创建它；Phase 5 的上传把原始文件放进去；Phase 3 的 IngestService 从里面读文件、产出 chunk。**T0401 建目录 = 为两个生命周期握手提前铺好场地**——这解释了 4.4 节"为什么创建 KB 要同时创建目录"。

---

## 13. 向后连接（T0401–T0404 全部完成，其余只连不教）

> 只解释依赖关系，不提前教实现答案。Phase 4 四个 Task 全部完成；以下未完成的都是 Future / Not implemented yet。

```text
T0401  Create / List KB
  │
  ├── ✅ T0402 Rename（第 9 节）—— 复用 validate_collection_name；
  │       7 步级联 + 两层补偿 + 原子性（AC-F001-04/06）
  │
  ├── ✅ T0403 Delete（第 10 节）—— 级联删 collection + 目录 +
  │       keyword index seam，不可逆
  │
  ├── ✅ T0404 Name Validation 正式验收（第 8 节）—— canonical regex
  │       8 边界用例 + 74/74 实测；前端等价 TS regex 仍待 T1101
  │       （F017，[FUTURE]）
  │
  ├── [FUTURE] Phase 5 Upload —— 上传必须有目标 KB 存在
  │       （T0501 的 KB existence check 会查 VectorStore，依赖
  │        Phase 4 之后系统中真实存在 collection）
  │
  ├── [FUTURE] Phase 6 Keyword Index —— T0602 替换 keyword_index.py
  │       的 no-op 函数体为真实 dirty-flag 失效（第 9.7 节的 seam
  │       契约；AC-F001-04 的 keyword-index 子句验证 DEFER 至此）
  │
  └── [FUTURE] Phase 10/11 Frontend —— KnowledgeBaseManager 组件
          调用 POST/GET/PUT/DELETE /api/collections（创建表单 +
          列表 + file_count 展示 + 改名 + 删除入口）
```

**职责一句话**（不展开实现）：
- T0402（Rename）：✅ 已完成——改 KB 名 = 改身份，级联改 ChromaDB + chunk metadata + uploads 目录 + keyword index，失败全回滚（RENAME_FAILED，第 9 节）。
- T0403（Delete）：✅ 已完成——级联清三处，不可逆、不补偿、残余诚实记日志（第 10 节）。
- T0404（Name Validation）: ✅ 已完成——canonical regex 8 边界用例正式验收；前端等价 TS regex 待 T1101（F017）。

---

## 14. T0401 只需要牢牢记住的 10 件事

> 不背函数。背心智模型。

1. **Phase 1 提供存储能力，T0401 把它变成 HTTP 产品能力**——能力在、入口不在，就还不是产品。
2. **KB 是业务概念，Chroma Collection 是当前 v1 的存储映射**——两层可以独立演化，不要写死在同一个抽象层。
3. **Validation 必须在 side effect 之前**——副作用前的拒绝免费，副作用后的拒绝要么补偿要么留脏。
4. **file_count 是派生数据**——从 chunk metadata 现场聚合，不是存的字段；用查询成本换写入一致性。
5. **API 层只喊业务动词**——create_collection 而不是 chroma 调用；抽象边界是 Phase 1 立的，Phase 4 第一次被抽查。
6. **发现 SPEC 与真实世界冲突时，停下来报告是能力不是短板**——实现者无权替产品改规则。
7. **最小规格修订 > 提前引入身份模型**——v1 的取舍逻辑：为锦上添花付出 identity ripple 不值得。
8. **两个持久化副作用 = 一致性问题**——ChromaDB + 目录，没有 ACID，缺口要诚实标注而不是假装不存在。
9. **mock 验证代码，真实依赖验证假设**——中文名冲突只有真实 ChromaDB 才暴露。
10. **创建 KB ≠ 上传文件**——两个生命周期，一个交汇点（uploads/{name}/）。

### T0402/T0403 追加 5 件事（第 9/10 节的心智模型）

11. **改名 = 改身份，删除 = 销毁身份**——name 是 chunk metadata / uploads 路径的身份锚点（ADR-02 的代价），所以 rename 必须全套级联，delete 必须级联清场。
12. **补偿代码的位置 = 资源所有权的位置**——存储级补偿在 VectorStore 内部，编排级补偿在 API 层；谁拥有资源，谁负责恢复它。
13. **快照即补偿载荷**——改数据之前先读旧值，旧值既是级联源又是恢复数据（undo log）。
14. **顺序设计的目标不是"不失败"，而是"残余最无害"**——delete 先删 Chroma 后删目录；失败留下的残余（孤儿目录）比另一种顺序（活的 KB 缺文件）轻。
15. **不可逆操作失败的诚实姿势 = 让残余状态可枚举**——delete 不补偿，但日志如实记录 `chroma_deleted` 标志；"不知道系统现在什么状态"才是真正的事故。

---

## 15. 自测系统（15 题 + T0404 附加 3 题 + T0402/T0403 附加 6 题）

> 先自己做，答案在节末答案区。

### Level 1 — 看懂（5 题）

1. `APIRouter` 在 T0401 里扮演什么角色？`include_router` 做了什么？
2. POST /api/collections 和 GET /api/collections 分别做什么？各自的成功状态码是多少？
3. `validate_collection_name("a中b")` 在当前代码里会发生什么？在 SPEC v1.5 时代会发生什么？
4. `response_model=CollectionResponse` 这个参数的作用是什么？删掉它会发生什么？
5. `uploads_dir.mkdir(parents=True, exist_ok=True)` 两个参数各是什么意思？

### Level 2 — 项目理解（5 题）

6. Phase 1 已经有 `create_collection`，为什么还需要 T0401？
7. `file_count` 的完整计算链是什么？为什么 v1 不把它存起来？
8. 为什么"a中b"在 v1.5 时代是 500 而不是 400？这条 500 路径经过了哪些代码？
9. T0401 创建 KB 时，为什么要把 uploads 目录的创建也放进同一个端点？
10. T0401 的代码里哪几行体现了"F008 抽象边界"？如果违反会怎样？

### Level 3 — 工程判断（5 题）

11. 如果产品要求知识库名支持任意 Unicode，你会怎么重新设计 identity？列出至少三个必须跟着改的地方。
12. ChromaDB 创建成功但 mkdir 失败：描述最终系统状态、用户可见现象、以及你作为工程师会怎么做（短期 + 长期）。
13. 为什么"catch 依赖异常转 400"是错误的修复方式？举一个它会在未来造成返工的具体场景。
14. 如果 ChromaDB 换成 Milvus，collections.py 里哪些行需要改？为什么这么确定？
15. file_count 的"现场聚合"方案在什么规模下会撑不住？撑不住时你会按什么顺序引入什么方案？

（L3 的 11-15 题完整分析见 [Engineering Review](./engineering-review/phase-04-engineering-review.md) 第 6.8 / 7.2 / 6.4 / 5-ADR-04 / 8 节。）

### T0404 附加题（3 题）

T4-1. `re.fullmatch` 与 `re.search` 的语义差别是什么？为什么校验必须用 fullmatch？本项目里如果误用 search，结果会不会错？为什么？
T4-2. 不运行代码：`a-b`、`3kb`、`a.b`、`_ab` 四个名字分别会通过校验吗？各用正则的一段说明理由。
T4-3. F017 要求前后端等价校验，但 TS 版要等 T1101。T1101 落地前"等价"靠什么保证？落地后还需要什么机制性保障？

### T0402/T0403 附加题（6 题）

TR-1. rename 编排的补偿为什么先回 uploads 目录、再回存储层？反过来的话会出什么问题？
TR-2. rename 的三个 4xx（400/404/409）为什么永远不会被映射成 500 RENAME_FAILED？
TR-3. 为什么 `invalidate_keyword_index` 在 rename 里要调用两次（old_name + new_name）？现在这个函数真的做了什么吗？
TR-4. delete 为什么 Chroma 先删？如果 uploads 先删，最坏的残余状态是什么？
TR-5. delete 中途失败为什么不补偿？失败后系统靠什么保证"残余状态可枚举"？
TR-6. `_assert_safe_uploads_target` 防的是什么场景？v1.6 regex 和 404 检查都在，为什么还需要它？

### 答案区

<details>
<summary>点击展开答案（先自己做完再看）</summary>

**L1**

1. APIRouter 是 FastAPI 的路由分组容器——collections_router 声明 /collections 的两个端点；include_router 把它挂进 api_router，api_router 再由 main.py 以 /api 前缀挂进 app，最终路径 /api/collections。
2. POST 创建知识库（201），GET 列出全部知识库及其 file_count（200，默认）。各自契约见 SPEC 6.5。
3. 当前：`_COLLECTION_NAME_PATTERN.fullmatch` 失败 → `AppError("INVALID_COLLECTION_NAME")` → 400。v1.5：正则通过 → 流进 ChromaDB → 依赖异常 → 500。
4. 让 FastAPI 按 CollectionResponse 校验并序列化返回值（多出的字段会被裁剪）。删掉后返回 dict 也能响应，但失去响应形状约束和 OpenAPI 文档准确性。
5. `parents=True`：连中间目录一起建（uploads/ 不存在也会建）；`exist_ok=True`：目标已存在不算错误。

**L2**

6. Phase 1 的是内部能力（只能代码调用）；T0401 把它变成 HTTP 产品能力（用户/前端可用）。"能力在、入口不在，就还不是产品"。
7. collection → get_files（取全部 chunk metadata → 按 file_id 聚合去重）→ len()。v1 不存它是因为 SPEC 7.3 不引入 metadata DB，且派生数据永远一致；代价是每次列表现场算。
8. v1.5 正则放行 → ChromaDB create_collection 抛异常（非 AppError）→ 不被 AppError handler 接住 → 被 Exception 全局兜底接住（main.py:54-65）→ 500 INTERNAL_ERROR。
9. KB 数据模型 = collection + 目录一体（F001）；目录在 KB 出生时备好，风险在创建时暴露，不上传到路径；也是 KB/文档两个生命周期的握手点。
10. 全文没有 import chromadb、没有 `_client`——只有 store.create_collection / list_collections / get_files 三个 public 调用。违反会把存储实现泄漏进业务层（换存储全要改 + 私有属性泄漏）。

**L3**

11. kb_id（UUID）/ display_name / storage_key 三身份模型；必须跟着改：chunk metadata（collection_name/source_file 的锚点）、rename 级联（T0402）、uploads 目录命名、query/frontend 契约。这是 Future 设计不是当前实现。
12. 状态：ChromaDB 有 collection、无目录（孤儿）；用户看到 500 + 重试 409"名称已存在"。短期：手动清理或文档化已知缺口；长期：补偿逻辑（失败时 delete_collection）或先目录后 collection（留孤儿目录，性质更轻）。当前实现无补偿——诚实承认。
13. 因为那等于把"ChromaDB 的约束"当成"产品的规则"——没有 owner 拍板。未来场景：产品宣布"我们要支持中文名，加映射层"，此时被 catch 吞掉的输入范围又要重新挖出来；且前端 TS 校验和文档都还写着旧规则，三处漂移。
14. 零行（理论上）——它只调用 VectorStore public interface。确定是因为 F008 约束 2/3/4 的设计目的即在此；不确定的部分是实现层（MilvusVectorStore 的 collection 映射细节）。这是基于当前抽象的推断，非已验证事实。
15. 每次 GET 都全量拉 metadata 聚合，成本 O(总 chunks)。几百文件×几千 chunk 时开始明显。演进顺序：先缓存 file_count（带失效）→ 再考虑独立 metadata store（SQLite/Postgres，SPEC 外）→ 异步聚合。全为 Future。

**T0404 附加题**

T4-1. fullmatch = 全串匹配（从头到尾），search = 任意位置找到即返回（JS `.test()` 的默认行为）。校验必须全串匹配——"名字必须整个合法"≠"名字里只要有一段合法"。本项目不会错：正则自带 `^$` 锚点（collections.py:74），即使误用 search 也强制全串；fullmatch 是第二道显式保险（双保险 + 意图双处可见）。
T4-2. `a-b` ✅（首 `a` + 中 `-` + 末 `b`）；`3kb` ✅（数字在首末字符类 `[A-Za-z0-9]` 内）；`a.b` ❌（`.` 不在中间字符类，v1.6 产品决策：存储允许 ≠ 产品允许）；`_ab` ❌（首字符必须是字母/数字，下划线只允许在中间段）。
T4-3. 落地前靠纪律：canonical regex 写在 SPEC v1.6 里（单一契约来源），两处实现逐字符对照。落地后仍需机制性保障（共享测试向量 / 契约测试）——当前没有，见 Engineering Review Pending #32。

**TR 附加题**

TR-1. 因为补偿必须**逆序**（正向最后完成的步骤最先回退）：正向顺序是 存储 → 目录，补偿顺序是 目录 → 存储。反过来（先回存储）时，目录还是新名而 collection 已回旧名——两个身份锚点错位，制造出半改状态。逆序保证每步回退时依赖它的前一步仍处于已恢复状态。
TR-2. 位置决定命运：三个 4xx 校验都在 try 块**之前**执行（collections.py:139-145），根本不进入"失败 → 补偿 → RENAME_FAILED"的路径。只有持久化副作用中途的失败才映射 RENAME_FAILED——每个错误码有且只有一个出口。
TR-3. old 名下的索引缓存内容已属于旧身份，必须失效；new 名若有历史残留缓存（同名旧 KB 曾存在）也不能复用。所以双名都调。当前函数体是**文档化的 no-op**（keyword_index.py:42-44）——Phase 6 的索引还不存在，没有缓存可失效；真实失效实现待 T0602。
TR-4. 最坏残余对比：uploads 先删 → rmtree 半途失败留下"活的 KB 缺文件"（最坏形态）；Chroma 先删 → Chroma 失败时状态完好，成功后的失败只留孤儿目录（较轻）。顺序设计的目标是"失败残余最无害"。
TR-5. 删除的目标状态是"不存在"，补偿 = 恢复已删数据，与不可逆语义矛盾；且 ChromaDB 无 undo 原语。失败后的诚实姿势：结构化日志记录 `chroma_deleted` / `uploads_dir_exists` 两个标志，让残余状态**可枚举**——"不知道现在什么状态"才是真正的事故。
TR-6. 防的是**手工污染存储**：外部直接改 ChromaDB 塞进带路径分隔符的 collection 名（API 创建的名字被 v1.6 regex 挡住、404 挡住的是"不存在"而非"名字危险"）。防御纵深：每一层都假设内层可能被绕过；删除是破坏性操作，多一层 resolve+parent 检查的代价远低于一次路径穿越事故。

</details>

---

## 16. 动手练习（7 个）

> 全部不动项目正式业务代码。

**练习 1 — 手画 POST 请求路径**：不看书，画出完整链路图，从"HTTP 报文"画到"ChromaDB + uploads 目录"再回到"HTTP 201"。每站标一个"谁不负责"。画完对照第 5 节查漏。

**练习 2 — 状态码判断**：给每个输入判断最终状态码和错误码（答案见节末）：

| 输入 | 你的判断 |
|------|---------|
| `{"name": "test-kb"}`（首次） | |
| `{"name": "test-kb"}`（再次） | |
| `{"name": "ab"}` | |
| `{"name": "a中b"}` | |
| `{"name": "-bad"}` | |
| `{"name": "bad-"}` | |
| `{"name": "a" + "b"*49}`（51 字符） | |
| `{"name": "Test-KB_123"}` | |
| `{"name": "a.b"}` | |
| `{}`（无 name 字段） | |

<details>
<summary>答案</summary>

201 / 409 COLLECTION_ALREADY_EXISTS / 400 INVALID_COLLECTION_NAME / 400 / 400 / 400 / 400（51 字符） / 201 / 400（`.` 不在允许字符集——v1.6 产品决策） / 422（Pydantic 缺字段，框架默认形状——注意不是 400，见 Engineering Review 第 7.4 节 Finding #3）

</details>

**练习 3 — 手写 TS 伪代码**：不看 collections.py，用 TypeScript（Express 或 Next.js 任选）写出 create_collection 端点的等价伪代码，包括：schema 校验、业务校验、409 检查、storage 调用、目录创建、201 返回。然后对照 Python 版，找出**两处你必须自己处理而 FastAPI 帮你处理了的事**（提示：请求体解析与响应序列化）。

**练习 4 — SPEC_CONFLICT 复盘分析**：假设你接到任务"在 v1.5 规则下实现中文 KB 名支持"。写三小段：(a) 你发现冲突时的第一步行动；(b) 你会写进冲突报告的三项内容；(c) 如果 owner 选了 Option B，你预估至少 4 处代码要改。完整案例分析见 [Engineering Review 第 6 节](./engineering-review/phase-04-engineering-review.md)（本文档第 11 节是精简版）。

**练习 5 — Future 设计（明确标注 Future）**：设计 display_name/storage_key 模型的最小实现草图：三个字段各自的生命周期（谁生成、谁可变）、chunk metadata 里用哪个、uploads 目录用哪个、rename 时动谁。画一张"三个名字的流转图"。**明确这是设计练习，不是实现**——不要写进业务代码。（参考：Engineering Review 第 6.8 节的三身份模型。）

**练习 6 — 正则结构推演（T0404）**：不运行代码，把第 8.2 节矩阵的 8 个输入各写一句"被哪一段正则拒绝/放行"。然后做两件事：(a) 用 JS 写出等价 TS regex 并解释为什么它与 Python 版逐字符一致；(b) 解释"存储层允许 `.` 而产品拒绝 `.`"（v1.6 决策）在你看来合理在哪（提示：目录名歧义、隐藏文件、扩展名联想）。

**练习 7 — 补偿/残余状态矩阵推演（T0402/T0403）**：画两张表，不动业务代码。
(a) rename 的四步正向操作（storage → uploads → invalidate → verify）分别失败时，写出每步的补偿动作和**最终可观察状态**（提示：invalidate 失败要不要回滚？verify 失败补偿谁？）；
(b) delete 的三步正向操作（chroma → rmtree → invalidate）分别失败时，写出最终可观察状态和日志里 `chroma_deleted` 标志的值。画完对照第 9.2 / 10.1 节的代码顺序核对。

---

## 17. Phase 4 Quick Review Card

```text
┌─────────────────────────────────────────────────────────┐
│ Phase 4 Quick Review Card（T0401–T0404 全 DONE）        │
├─────────────────────────────────────────────────────────┤
│ 一句话定位    │ 把 Phase 1 的存储能力第一次变成 HTTP 产品能力   │
│              │（DX-RAG 从基础设施进入业务 API 层）           │
├─────────────────────────────────────────────────────────┤
│ 核心 API     │ POST /api/collections（201/400/409）        │
│              │ GET  /api/collections（200 + file_count）   │
│              │ PUT  /api/collections/{name}（200/500）     │
│              │ DELETE /api/collections/{name}（200/404/500）│
├─────────────────────────────────────────────────────────┤
│ 核心调用链    │ validate(400) → duplicate(409) →           │
│              │ VectorStore.create_collection →            │
│              │ uploads mkdir → 201                        │
│              │ GET: list_collections → get_files → len()  │
│              │ PUT: 前置校验 → storage cascade → 目录改名   │
│              │   → invalidate ×2 → verify → 失败补偿 500   │
│              │ DELETE: 404 → 路径防御 → Chroma 先删 →      │
│              │   rmtree → invalidate → 失败诚实日志 500    │
├─────────────────────────────────────────────────────────┤
│ 依赖 Phase   │ Phase 0（app/router/schema/error 架子）      │
│              │ Phase 1（create/list/rename/delete/get_files）│
│              │ 不使用 Phase 2/3（空 KB 无内容可处理）        │
│              │ keyword seam 先立契约（T0602 填实现）        │
├─────────────────────────────────────────────────────────┤
│ 关键错误     │ 400 INVALID_COLLECTION_NAME                 │
│              │ 404 COLLECTION_NOT_FOUND                    │
│              │ 409 COLLECTION_ALREADY_EXISTS              │
│              │ 500 RENAME_FAILED / INTERNAL_ERROR          │
├─────────────────────────────────────────────────────────┤
│ 最重要设计原则 │ Validation Before Side Effects             │
│              │ 补偿位置 = 资源所有权位置（两层补偿）          │
│              │ 顺序设计：残余最无害；不可逆失败：残余可枚举    │
├─────────────────────────────────────────────────────────┤
│ 最重要工程事件 │ SPEC v1.5 中文命名 vs ChromaDB 冲突          │
│              │ → BLOCKED → 产品决策 → v1.6 收紧 regex      │
├─────────────────────────────────────────────────────────┤
│ 面试一句话    │ "创建接口先校验后落库，存储走抽象层；开发中    │
│              │ 发现规格与真实 ChromaDB 冲突，走了正式修订流程" │
├─────────────────────────────────────────────────────────┤
│ T0404 验收   │ canonical regex 8 边界用例 + fullmatch 全串   │
│              │ 锚定；函数早于任务落地、验收后置（2026-08-25）  │
│ T0402/T0403  │ 7 步级联 + 两层补偿 + 快照即补偿载荷；         │
│              │ Chroma 先删 + 防御纵深 + 残余诚实日志         │
├─────────────────────────────────────────────────────────┤
│ Next         │ Phase Gate Review + Learning Review         │
│ connection   │ Phase 5 Upload 依赖 KB 存在（Future）        │
│              │ Phase 6 T0602 填 keyword seam 实现（Future） │
├─────────────────────────────────────────────────────────┤
│ 去哪深挖     │ 完整复盘 → engineering-review/               │
│              │   phase-04-engineering-review.md            │
│              │ 面试话术 → interview-notes/                  │
│              │   dx-rag-interview-guide.md Phase 4 深度章   │
└─────────────────────────────────────────────────────────┘
```

---

## 18. Python 新知识索引

T0401 真实代码中出现的新 Python/FastAPI 知识，已按惯例收入 [python-for-frontend-dev.md](./python-for-frontend-dev.md) 第 26 节：

| 知识点 | 手册位置 | 真实代码 |
|--------|---------|---------|
| `APIRouter` + `include_router`（Express Router 类比） | 26.1 | router.py:5,14 |
| 路由装饰器带配置参数（`response_model=` / `status_code=`） | 26.2 | collections.py:90,104 |
| `re.compile` + `re.fullmatch`（正则与 JS 的差异） | 26.3 | collections.py:74,86 |
| `Path.mkdir(parents=True, exist_ok=True)`（含 exist_ok 的隐藏语义） | 26.4 | collections.py:99-100 |
| 每请求新建实例 vs Phase 2 懒加载单例（三种实例化模式对照） | 26.5 | collections.py:95,107 |

T0402/T0403 引入的新 Python 知识，已按惯例收入手册第 27 节：

| 知识点 | 手册位置 | 真实代码 |
|--------|---------|---------|
| `Path.rename`（文件系统改名 + Windows 语义差异） | 27.1 | collections.py:177 |
| `shutil.rmtree`（递归删除 + 不存在即抛 vs Node force） | 27.2 | collections.py:321 |
| `Path.resolve()` + `.parent`（防御性路径检查原料） | 27.3 | collections.py:303-304 |
| `logger.exception`（自动附带 traceback 的日志） | 27.4 | collections.py:282, vector_store.py:377 |
| `**meta` dict 展开合并（≈ JS 对象展开 `{...meta}`） | 27.5 | vector_store.py:335-337 |
| `except AppError: raise` 穿透模式 | 27.6 | collections.py:279-280 |

已讲过的知识只链接不重复：列表推导（手册 23.2/23.3，GET 的 items 列表）、Pydantic BaseModel（手册第 7 节）、`raise AppError`（手册第 10 节）、decorator 基础（手册第 8 节，其 decorator 清单表已补充 `@router.post/get` 两行）、`raise ... from exc`（手册 18.4，T0201 首次出现、collections.py:159/289 再次使用）。

T0404 正式验收**没有引入新的 Python 语法**——`fullmatch` / `match` / `search` 三函数对照与边界用例推演在本文档第 8 节；手册 26.3 已覆盖 fullmatch 与 JS 的差异，不重复。

---

## 19. 诚实核对与学习边界

### 19.1 三层事实对照（SPEC / TASKS / 代码）

| 契约点 | SPEC（v1.6） | TASKS.md | 真实代码 | 一致？ |
|--------|-------------|----------|---------|--------|
| 创建五步顺序 | F001 Detail 五步 | T0401 Scope 同 | collections.py:94-101 同序 | ✅ |
| 名称正则 | v1.6: `^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$` | T0404 引用同 | collections.py:74 同 | ✅ |
| 201 + 响应形状 | 6.5: `{message, name}` 201 | "Responses match Section 6.5 exactly" | L90 装饰器 + L101 | ✅ |
| 400/409 错误码 | 6.5 错误表 + 9.2 目录表 | T0401 引用 | errors.py:43-45 + L86/L96 | ✅ |
| GET 响应含 file_count | 6.5 示例 | T0401 验证项 | L110 `len(store.get_files(name))` | ✅ |
| Rename 7 步编排 + 补偿 | F001 Rename Detail + v1.5 级联契约 | T0402 Scope 同 | collections.py:139-159 + vector_store.py:292-352 | ✅ |
| Rename 响应形状 | 6.5: `{message, old_name, new_name}` 200 | "Responses match Section 6.5" | schemas.py:62 + L161-163 | ✅ |
| Delete 4 步 + 不可逆 | F001 Delete Detail（4 步、irreversible） | T0403 Scope 同 | collections.py:269-289 | ✅ |
| 500 RENAME_FAILED / 404 COLLECTION_NOT_FOUND | 9.2 目录表（errors.py:44,46） | T0402/T0403 引用 | L159 / L143 / L270 | ✅ |
| T0401–T0404 状态 | — | 全部 DONE | 代码存在且注册 | ✅ |
| T0404 验收表 | v1.6 规则下的 8 边界用例 | TASKS.md L1390-1397 | 第 8.2 节矩阵推演 + 8.4 节 74/74 实测 | ✅ |
| AC-F001-01/02 归属 | Section 12 | Section 19 → T0401 | — | ✅ |
| AC-F001-03 归属 | Section 12 | Section 19 → T0404（L2871） | — | ✅ |
| AC-F001-04/06 归属 | Section 12 | Section 19 → T0402（L2872,2874） | — | ✅ |
| AC-F001-05 归属 | Section 12 | Section 19 → T0403（L2873） | — | ✅ |

### 19.2 验证与 AC 的诚实立场

- 仓库中**没有持久化的自动化测试脚本**（backend 无 test 文件）——本次学习的验证手段是：TASKS.md 的 DONE 记录 + 开发期真实集成验证（real TestClient + real ChromaDB + real filesystem，见 Engineering Review 第 6.10 节 Verification）+ 本次逐行代码审查（上表 15 项契约点全部核对通过）。
- AC-F001-01（创建成功）、AC-F001-02（重名 409）归属 T0401——按 TASKS.md 记录为 PASS，**不虚构额外的 PASS**。
- T0404 的验收证据：2026-08-25 实测 74/74 checks PASS（6 valid + 9 invalid + side-effect boundary 交叉验证，见第 8.4 节）。AC-F001-03 按 TASKS.md 记录 PASS，**不虚构额外 PASS**；验证脚本已删除——**验证发生过，但回归无自动化保障**。
- **T0402/T0403 的诚实声明**：TASKS.md 两个 Task 的 Status 均为 DONE，实现代码存在且与 AC 描述的行为一致（逐行核对，上表 5 行）。但仓库中**没有本会话可查的端点级验证执行记录**（无测试脚本、无 74/74 式的实测记录留存）——所以 AC-F001-04/05/06 的表述是：**按 TASKS.md 记录为 DONE，验证细节不虚构**。真实发生的运行时证据只有两条：ER 预检阶段（实现前）的 ChromaDB 1.5.9 探针（PF-4：`modify` / `update` 原语行为确认）与本次代码审查。若需要面试级的确证，应在 Phase 12 或后续回归中补做真实端点验证。
- 本文档未运行任何测试，也未创建任何测试脚本（学习任务约束）。

### 19.3 Learning Review Findings → 已迁往 Engineering Review

T0401 的 4 条 Learning Review Findings 与 Pending Questions #28–31（延续 Phase 3 的 #1–27 编号）属于工程评审职责，已迁移至 [phase-04-engineering-review.md](./engineering-review/phase-04-engineering-review.md) 第 7.6 节。本文档只保留一句话结论：

- **Finding #1/#2**：Create 的两个持久化副作用（ChromaDB + mkdir）之间没有补偿——**当前实现如此，未修复**（T0403 的 cascade delete 提供了一条事后清理路径，但 Create 本身仍无补偿）。
- **Finding #3**：请求体不合法 → FastAPI 默认 422 形状（非 SPEC 6.7 信封）——**待 T1201 实测确认**。
- **Finding #4**：仓库无持久化测试脚本——回归无自动化保障（T0404 的纯边界用例、T0402/T0403 的级联行为同样未被固化）。

T0404 增量评审（共享函数位置、F017 前后端漂移风险、验证证据两层结构）见 Engineering Review 第 7.8 节；新增 Pending #32。T0402/T0403 增量评审（PF-1~5 逐条评估、ADR-06~08、delete 顺序论证）见 Engineering Review 第 7.9 节；新增 Pending #33–#34。

> **Phase 4 编码收官 —— Learning Pass 完成（T0401: 2026-08-24；T0404: 2026-08-25；T0402/T0403: 2026-08-25）**：T0401 用 81 行代码兑现了 SPEC F001 的 Create/List 契约，并留下了比代码更值钱的东西——一次完整的"规格冲突 → 上报 → 产品决策 → 规格修订 → 回归"流程样本（SPEC v1.6）。T0404 随后以 0 行新增功能代码把共享校验函数正式验收为契约（74/74 实测）。T0402/T0403 把跨系统副作用的一致性管理第一次带进项目：rename 的两层补偿（存储级 + 编排级）、delete 的顺序设计与诚实残余日志、keyword index 的"契约先行"seam——AC-F001-04/05/06 对应实现全部落地。本文档（教材）与 Engineering Review（复盘）、Interview Guide（话术）三层各司其职：看代码来这，看取舍去 Engineering Review，备面试去 Interview Guide。Phase 4 编码到此完结。流程环节进展：Phase Learning Review ✅（2026-08-25）——Interview Guide 的 Phase 级 consolidation 已落地（新增 P4Q13–P4Q18 + EP4-8、修正 EP4-3、更新 3 分钟介绍与亮点 15）。剩余流程环节：Phase Gate Review。**本次学习到此为止，不启动下一 Task。**
