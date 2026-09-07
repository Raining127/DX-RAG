# Phase 11 — Frontend Features Technical Learning

> **Phase 状态**：COMPLETE（T1101–T1105 DONE；Gate re-review 结论：`PHASE_11_PASS — READY_FOR_PHASE_12`）
> **本文档状态**：Task Learning Pass + Phase Learning Review 完成（2026-09-07）
> **当前证据**：production build PASS；Task-level 真实 browser-to-FastAPI smoke、validator/formatter probes 与 static contract evidence；Gate focused re-review 使用真实 production Next UI + isolated in-memory **MOCKED API** 验证 shared collection synchronization、rename/delete fallback、QA reset、menu-state preservation 与 console 0 warning/error；repository-owned frontend automated tests 为 `NOT_AVAILABLE`
> **边界**：Gate PASS 表示已具备进入 Phase 12 的条件，不等于 Phase 12 已启动；[Phase 11 Engineering Review](./engineering-review/phase-11-engineering-review.md) 已于 2026-09-07 独立完成。本次状态同步不修改 application/SPEC/TASKS，不 commit/push。

---

## 0. 三层文档边界

| 层 | 当前归属 | 本次职责 |
|---|---|---|
| Technical Learning | 本文件 | T1101–T1105 代码精读，并在 Gate 后完成跨 Task 去重、统一 mental model、自测链与证据边界 |
| Engineering Review | [phase-11-engineering-review.md](./engineering-review/phase-11-engineering-review.md) | 已独立评审 ADR、failure taxonomy、scale 与 Known Gaps；不由 Technical Learning 替代 |
| Interview Guide | [Phase 11 深度章](./interview-notes/dx-rag-interview-guide.md#phase-11-learning-review) | 已按 Phase cadence 晋升精选 candidates、Gate remediation 闭环与诚实边界 |

本文件仍不是 completion report、Gate verdict 或 Engineering Review。它回答三个问题：代码怎样工作、五个 Task 如何组成同一套前端状态架构、哪些知识可以迁移到其他 React/TypeScript 系统。

---

## 1. Phase 学习：从“可切换骨架”进入“可操作产品”

### 一句话定位

Phase 11 把 Phase 10 的四个 placeholder 变成可操作产品：KnowledgeBaseManager、FileUpload、QAPanel 与 FileManager 共同消费 centralized API client；`page.tsx` 统一拥有 collection resource，feature components 则拥有各自的表单、上传、会话、文件列表、预览与 mutation lifecycle。[PROJECT FACT]

### Phase Learning Review mental model：一条共享脊柱，四个局部状态机

```text
Backend durable truth
        │
centralized api-client.ts             transport owner
        │
page.tsx collection source            shared server-resource projection
        ├── collections / load state / retry
        ├── mutation revision: create | rename | delete
        └── server-confirmed projection callbacks
             │
    ┌────────┼──────────┬───────────┐
    ▼        ▼          ▼           ▼
KB Manager  Upload      QA          Files
CRUD form   upload tx   conversation file/list/preview/delete
state       state       state        state
```

这张图的重点不是“把所有 state 都提升”。共享事实只提升到最小共同 owner；与单个交互绑定的 transaction state 继续留在 feature 内。[ENGINEERING KNOWLEDGE]

### 跨 Task 核心学习点

1. **共享 server resource 与局部 transaction 必须分开**：collection 列表影响四个 feature，归 Home；modal input、upload outcome、QA history 与 preview 则只属于各自 feature。
2. **preservation 不等于 freshness**：persistent panels 解决菜单切换丢 state，却曾放大四份独立 collection cache 的 stale-read 风险；Gate F-1 促成 shared source remediation。
3. **identity change 必须触发 reconciliation**：rename 把旧选择迁移到新名称，delete 让已删除 owner 回退到第一项；QAPanel 同时清空旧 owner 的 conversation。
4. **异步正确性取决于 commit ownership**：request version/ref guards 让旧 list、preview 或 answer 不能覆盖用户的新选择；它们不等于网络取消。
5. **错误按责任分层**：API client 统一 transport error，feature 处理 expected async failure，`app/error.tsx` 处理 unexpected route render failure。
6. **前端校验只提供 early feedback**：collection regex、extension/size/empty checks 减少无效请求，Backend 仍是最终 trust boundary。
7. **状态标签服从 domain semantics**：empty、error、partial warning、empty KB 与 pending answer 不是同一种失败，不能压成一个 boolean。

### TypeScript / Node 类比

- shared collection source 像一个 request-scoped read model owner；feature state 像各 controller 的 local transaction context。
- `resolveCollectionSelection()` 像 referential-integrity repair：identity rename 时迁移引用，identity delete 时选择合法 fallback。
- `setCollections(current => ...)` 像基于最新 snapshot 提交；读取旧 closure 更像基于 stale cache 做 lost-update-prone 写入。
- `Popconfirm` 只是用户意图 gate，不是 backend transaction、undo log 或 authorization。

> **阅读时间线**：第 2–61 节保留各 Task Learning Pass 当时的验证范围与收口边界；其中“本轮未启动下一 Task/Gate”等句子是历史 checkpoint。当前 Phase-level canonical 结论以第 1、66、73、74、76–78 节为准；F-1 remediation 后的代码事实已经回填到相关 Code Understanding 小节。

---

## 2. T1101 目标与契约

### 2.1 用户目标

用户进入知识库管理工作区后，应能：

- 看见正在加载、加载失败、空列表或已有列表；
- 创建合法名称的知识库；
- 在 modal 中重命名，且新旧名称不能相同；
- 在明确 cascade warning 后删除知识库；
- 从失败状态获得可理解的反馈和可操作的 retry path。

### 2.2 直接依赖

| Dependency | T1101 怎样消费 |
|---|---|
| T1001 API client | Home 使用 `listCollections`；组件使用 `createCollection/renameCollection/deleteCollection` 与 `ApiError` |
| T1002 App Shell | `page.tsx` persistent mount 四个 feature，并用 `hidden` 切换可见性 |
| T0404 canonical validation | frontend regex 与 backend `fullmatch` observable behavior 对齐 |
| F001 Collection API | success fields、409 duplicate、400 invalid、rename/delete semantics |
| F017 §17.3 | CRUD controls 与 loading/success/empty/error states |

### 2.3 本 Task 不做什么

- 不实现 upload、QA、file manager 或跨知识库迁移；
- 不实现 export/import；
- 不新增 router、Redux/Zustand、auth 或 backend contract；
- 不证明带文件知识库 rename/delete 的真实跨存储 cascade；本轮 smoke 只使用空 collection；
- 不建立 Phase 11 Gate、Phase Learning Review 或 Engineering Review。

---

## 3. 项目位置与 ownership

```text
Home.selectedKey
    ├── query lifecycle: loadCollections()
    ├── shared collections / state / error
    ├── mutation revision + CRUD projection callbacks
    └── selectedKey === "knowledge-base"
             ▼
KnowledgeBaseManager
    ├── create lifecycle: create modal + validation + mutation
    ├── rename lifecycle: target + validation + mutation
    ├── delete lifecycle: Popconfirm + mutation
    └── feedback: notice / operationError / modal errors
             │
             ▼
centralized api-client.ts
             │
             ▼
FastAPI Collection API → ChromaDB + uploads directory + keyword lifecycle
```

### Ownership 表

| Concern | Owner | 原因 |
|---|---|---|
| URL/method/JSON/error envelope | `api-client.ts` | transport knowledge 不应散入组件 |
| collection name business rule | SPEC + Backend | 最终 trust boundary |
| 即时名称提示 | `validators.ts` + component | 减少无效 request，改善交互 |
| collection list + loading/empty/ready/error | `page.tsx` | 四个 feature 共同消费同一 server-resource projection |
| CRUD form、pending 与 feedback | `KnowledgeBaseManager` | 只与当前 feature transaction 绑定 |
| selected workspace + shared collection projection | `page.tsx` | shell composition 与最小公共 resource owner |
| actual create/rename/delete side effects | Backend | browser state 不能替代 durable truth |

组件没有直接 `fetch`、没有拼 endpoint path、没有解析 Section 6.7 envelope。这说明 Phase 10 的“双插座底板”开始被真实业务组件消费，而不是停留在抽象设计。[PROJECT FACT]

---

## 4. Code Understanding：逐段读懂 `KnowledgeBaseManager`

### 4.1 类型先描述状态空间

```ts
type ViewState = 'loading' | 'success' | 'empty' | 'error';

interface OperationError {
  message: string;
  retry?: () => void;
}
```

`ViewState` 把列表区域限制为四个互斥状态，比 `isLoading/isEmpty/hasError` 三个 boolean 更安全：多个 boolean 可能同时为真，而 union 至少要求调用方选择一个标签。

但当前 state 仍不是完整 discriminated union。`collectionState='error'` 与 `collectionError=''` 在类型上仍可同时出现；`ready` 与空 `collections` 也没有 compile-time 禁止。更严格的写法可以把 data/error 和 tag 绑在同一 union 中，但是否值得升级应由后续复杂度决定。[ENGINEERING KNOWLEDGE]

`OperationError.retry` 把 recovery action 和 message 绑定。这里 delete failure 保存 `() => void handleDelete(name)`，使 Alert 可以重试同一个 resource；它不是通用 command bus，只是一个局部 retry seam。

### 4.2 `getErrorMessage()` 是 domain error → user message adapter

```ts
function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error && error.message) return error.message;
  return '操作未完成，请稍后重试。';
}
```

`catch` 输入按 `unknown` 对待，先 narrow 再读取。`ApiError` 的 message 来自 backend standardized envelope；普通 `Error` 保留 local/runtime message；其他 throwable 使用 fallback。

边界是：当前函数没有按 `ApiError.code` 做 feature-specific translation。例如 `COLLECTION_ALREADY_EXISTS` 直接展示 backend message。这符合统一错误展示的最小 contract，但未来若需要针对 code 给出不同 CTA，应在组件层显式 mapping，不能依赖字符串匹配。

### 4.3 Query lifecycle：Home `loadCollections()` + feature callback

```ts
const loadCollections = useCallback(async () => {
  const requestVersion = collectionRequestVersionRef.current + 1;
  collectionRequestVersionRef.current = requestVersion;
  setCollectionState('loading');
  setCollectionError('');

  try {
    const response = await listCollections();
    if (requestVersion !== collectionRequestVersionRef.current) return;
    setCollections(response.collections);
    setCollectionMutation(null);
    setCollectionState(response.collections.length > 0 ? 'ready' : 'empty');
  } catch (error) {
    if (requestVersion !== collectionRequestVersionRef.current) return;
    setCollectionError(getErrorMessage(error));
    setCollectionState('error');
  }
}, []);
```

状态转换为：

```text
Home mount / retry
    → loading
       ├── response.collections.length === 0 → empty
       ├── response.collections.length > 0  → ready
       └── throw                             → error
```

`useCallback([])` 给 Home effect 一个稳定 function identity；request version 使较旧 collection response 不能覆盖更新的 retry 或 mutation projection。它控制 commit，不取消网络请求。

KnowledgeBaseManager 不再调用 `listCollections()`。CRUD 成功后，它把 Backend response 中的 identity 交给 `onCollectionCreated/onCollectionRenamed/onCollectionDeleted`；Home 再更新 shared projection 并发布带递增 revision 的 mutation event。这样 query owner 与 transaction owner 分离，其他三个 feature 可在同一 render cycle 看到合法 collection 集合。[PROJECT FACT]

### 4.4 Derived state：`totalFiles`

```ts
const totalFiles = useMemo(
  () => collections.reduce((total, item) => total + item.file_count, 0),
  [collections],
);
```

总文件数完全由 `collections` 派生，因此没有第二个 `useState<number>`。这避免 rename/delete 后忘记同步 summary。`useMemo` 在当前数据量不是性能必需；更重要的是表达“derived, not independently mutable”。

### 4.5 Create：validation before mutation，server success 后 append

Create modal 每次打开都会清理 name/touched/error/notice/operationError，避免上一次交互污染新会话。`handleCreate()` 顺序是：

```text
touch field
→ validateCollectionName(createName)
→ invalid: return, no API call
→ pendingAction = "create"
→ createCollection()
   ├── success: notify Home → shared append + close + notice
   └── failure: keep modal open + createError
→ finally: clear pending
```

Home 的 `onCollectionCreated` handler 使用 `setCollections(current => [...current, ...])`，基于 React 提供的最新 collection snapshot，避免 async closure 中的旧数组覆盖较新的 state。

这里采用 server-confirmed shared projection，而不是 mutation 后再次 `listCollections()`：优点是少一次 round trip、四个 feature 同步快；代价是 client 假设 `CollectionResponse.name` 足以构造 `{name, file_count: 0}`。对于新建空库，这与 contract 一致；若 backend 将来返回 normalization 或额外字段，应重新检查 projection。

### 4.6 Rename：target snapshot + no-op guard + functional map

`renameTarget` 保存被操作的完整 `Collection`，modal 初始值为当前 name。额外规则：

```ts
renameTarget && renameName === renameTarget.name
  ? '新名称需要与当前名称不同'
  : validateCollectionName(renameName)
```

canonical regex 只回答“名称是否合法”，不能回答“这是不是 no-op”，所以两条规则被组合。成功后组件把 backend response 的 `old_name/new_name` 交给 Home；Home 做 functional map 并发布 rename revision，而不是盲目使用输入值，这让 server response 成为 mutation projection 的依据。

当前并未在 rename 期间锁住所有其他 card actions；`pendingAction` 只有一个 string slot。单用户顺序操作下成立，并发 action 的状态表示能力有限。[ENGINEERING KNOWLEDGE]

### 4.7 Delete：confirmation、irreversibility 与 closure snapshot

```text
click 删除
→ Popconfirm 展示 cascade + irreversible warning
→ confirm
→ pendingAction = `delete:${name}`
→ deleteCollection(name)
   ├── success: notify Home → filter shared list → empty/ready + notice
   └── failure: operationError + retry closure
```

Popconfirm 只证明用户明确确认；真正的 cascade order、compensation 与 path safety 仍由 Backend Phase 4 contract 拥有。UI 文案“文件、切片与索引，且无法恢复”把 destructive scope 提前给用户，是 interface safety，而不是 transaction safety。

Home delete callback 当前写成：

```ts
const remaining = collections.filter((item) => item.name !== name);
setCollections(remaining);
```

它读取 handler 创建时 closure 中的 `collections`，与 create/rename 的 functional update 不同。顺序点击时正常；如果允许两个 delete 并发完成，后完成者可能基于旧 snapshot 把先删除的 item 重新带回 UI。这是一个明确的 concurrency boundary，不是本次 smoke 已触发的 defect。后续可用 functional update 同时计算 next state，或全局序列化 mutations。[ENGINEERING KNOWLEDGE]

### 4.8 Rendering：四态区域与三类反馈

列表主体按 `viewState` 互斥渲染：

- `loading` → 三张 Skeleton cards；
- `error` → load Alert + “重新加载”；
- `empty` → Empty + create CTA；
- `success` → collection cards。

反馈又分三类 owner：

- `collectionError`：shared collection query/view 无法建立；
- `createError` / `renameError`：modal 内的具体 mutation 失败，保留用户输入；
- `operationError`：页面级 mutation error，目前由 delete 使用，并携带 retry。

这种分层比一个全局 `error` 更准确，因为错误的 recovery scope 不同：load 失败需要重新获取整个列表；create/rename 失败应留在 modal 修改输入；delete 失败要对同一 resource retry。

---

## 5. Canonical Validation：前后端等价，不是重复浪费

Frontend：

```ts
/^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$/
```

Backend：

```py
re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$").fullmatch(name)
```

它们的 observable rule 都是：3–50 字符，字母/数字开头结尾，中间允许字母、数字、下划线、连字符，不允许中文、`.`、空格或路径分隔符。[PROJECT FACT]

双层校验的职责不同：

- Frontend 是 UX optimization：即时提示、禁用 submit、减少无效 request；
- Backend 是 security/business boundary：任何 caller 都可绕过浏览器，最终规则必须在 server enforcement。

前端 regex 即使与当前 SPEC 完全一致，也不能成为唯一 truth。未来 contract 修改必须同步两层，并通过共享 case matrix 或 generated schema 检查 drift。

### 边界样例

| Input | 结果 | 原因 |
|---|---|---|
| `ab` | invalid | 只有 2 字符 |
| `abc` | valid | 最短合法名称 |
| `a_b-c9` | valid | 中间字符合法 |
| `_abc` | invalid | 不能以下划线开头 |
| `abc-` | invalid | 不能以连字符结尾 |
| `知识库1` | invalid | v1.6 canonical rule 不允许中文 |
| `abc.def` | invalid | 不支持 `.` |
| 51 chars | invalid | 超过最大长度 |

---

## 6. Data Flow：四条端到端交互链

### 6.1 Initial load

```text
mount
→ Home useEffect
→ loadCollections
→ collectionState=loading
→ listCollections()
→ GET /api/collections
→ CollectionListResponse
→ Home collections state
→ empty | ready shared props
→ KnowledgeBaseManager maps ready → success rendering
```

### 6.2 Create

```text
Input string
→ frontend canonical validation
→ createCollection(name)
→ { name } JSON
→ Backend validation + create
→ { message, name }
→ local Collection { name, file_count: 0 }
→ card + summary + notice
```

### 6.3 Rename

```text
selected Collection
→ modal target/name
→ canonical + no-op validation
→ renameCollection(oldName, newName)
→ PUT /api/collections/{old}
→ { old_name, new_name }
→ functional map by old_name
→ renamed card + notice
```

### 6.4 Delete

```text
selected collection name
→ irreversible Popconfirm
→ deleteCollection(name)
→ Backend cascade
→ 200 confirmation
→ local filter
→ success | empty + notice
```

### Type changes

```text
DOM Input value: string
→ validated collection name: string with runtime invariant
→ request DTO: CollectionCreateRequest / CollectionRenameRequest
→ JSON wire payload
→ response DTO
→ React Collection[] projection
→ Ant Design visual state
```

TypeScript 不会创建“ValidatedCollectionName” runtime brand；当前 invariant 只存在于 control flow。若 future code 可从多个入口调用 mutation handler，可能需要 branded type 或让 validator 返回 result object，但当前规模不必过度抽象。

---

## 7. React 状态设计：为什么不是“几个 `useState` 就结束”

### 7.1 Query state 与 data 是否应该完全分开

Home 的 `collections` 与 `collectionState` 是两份相关状态；KnowledgeBaseManager 再把 `ready` 映射为展示层的 `success`：

```text
collections=[] + collectionState=loading → 合法
collections=[] + collectionState=empty   → 合法
collections=[] + collectionState=ready   → 理论可表示但语义异常
collections=[...] + collectionState=error → 可能显示旧 summary + error body
```

这叫 representable invalid states：类型允许某些业务上不希望出现的组合。可以用 discriminated union 收紧：

```ts
type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; collections: Collection[] };
```

但当前实现的显式 setter 顺序短且可读，Learning Pass 只记录 trade-off，不授权重构。

### 7.2 一个 `pendingAction` 的表达能力

`pendingAction: string | null` 能表达“当前只有一个 mutation”。它用 `'create'`、`'rename'`、`delete:${name}` 复用同一 slot，减少多个 loading flags。

代价是 UI 没有全局阻止另一种 action：某张 card 删除时，另一张 card 理论上还能发起操作；新 action 会覆盖旧 pending key，先完成的 finally 又可能清空后一个 action 的 indicator。当前交互通常被 Modal/Popconfirm 串行化，但类型和代码没有建立严格 global mutex。

可选升级路径：

1. 明确全局 mutation lock，pending 时禁用所有 destructive actions；
2. 使用 `Set<ActionKey>` 表达并发；
3. 使用 reducer/state machine 管理 action identity 与 completion；
4. 引入 query/mutation library，但只有在更多 Phase 11 components 出现共同需求时才合理。

### 7.3 Local projection 与 refetch

| 策略 | 优点 | 风险 |
|---|---|---|
| 当前 Home-level append/map/filter | 四个 feature 同步、少网络、交互连续 | delete closure race、遗漏 server-derived fields |
| mutation 后 full refetch | 以 server 为最终 snapshot | 多 round trip、loading flicker、refetch failure |
| optimistic update before server | 最快 | rollback、并发 conflict、错误恢复复杂 |

当前代码不是 optimistic update：KnowledgeBaseManager 等待 server success 后才通知 Home 修改 list，应称为 **server-confirmed shared projection**。它仍是 Backend durable truth 的客户端投影，不是第二套权威数据源。

---

## 8. Error Handling 与失败边界

| Failure | 当前 UI | 当前 evidence | 边界 |
|---|---|---|---|
| initial list failure | page Alert + 重新加载 | `STATIC`; browser injection `NOT_AVAILABLE` | retry handler 存在但未真实点击验证 |
| invalid create name | submit disabled / field hint | `REAL BROWSER` | 证明 browser guard，不证明 Backend validation |
| duplicate create | modal `创建失败`，保留 input | `REAL BROWSER + REAL FASTAPI` | console 出现预期 API error log |
| rename same name | save disabled + validation message path | `REAL BROWSER` disabled state | 未发送 request |
| rename API failure | modal Alert，保留 target/input | `STATIC` | 无专门 injected failure evidence |
| delete before confirmation | 无 request | `REAL BROWSER` confirmation visible | 不证明 backend cascade |
| delete failure | page Alert + retry closure | `STATIC` | retry click / partial backend failure未验证 |
| concurrent mutations | pending/closure 可能漂移 | `NOT_AVAILABLE` | 没有 race tests 或 mutex contract |
| component unmount during request | promise 仍可能 settle | `NOT_AVAILABLE` | 无 abort/ignore-stale policy |

`ApiError.message` 当前直接进入 UI。它满足“用户可理解错误”的最小路径，但若 backend message 同时服务日志与 UI，未来可能需要 error-code-to-copy mapping。不要直接显示 arbitrary `details`，其中可能包含内部诊断信息。

---

## 9. Engineering Review 摘要（非完整 Phase Review）

1. **Separation of concerns**：组件消费 typed client，不重复 HTTP protocol。
2. **State ownership**：Home 拥有共享 collection resource 与 workspace selection；Feature Component 只拥有本地 transaction lifecycle。
3. **Validation defense in depth**：前端提供即时反馈，后端仍是最终 enforcement。
4. **Server-confirmed projection**：成功后局部更新，避免把未确认 mutation提前画进 UI。
5. **Destructive affordance**：delete 先展示 cascade/irreversible warning。
6. **Concurrency debt**：单 pending slot、无 abort；Home delete projection 仍基于 callback closure snapshot，Gate 将并行删除 race 接受为 v1 MINOR boundary。
7. **Testability debt**：关键 helpers 未导出、API imports 未注入，仍可通过 module mocking/browser tests覆盖，但当前没有 repository-owned suite。
8. **Accessibility baseline**：label、button semantics、Alert、Popconfirm、`aria-live` 已有基础；focus return、screen-reader announcement 和 keyboard matrix 未验证。

完整 Phase 11 ADR/failure taxonomy/scale review 仍须独立执行 Engineering Review。本节是 Technical Learning 的局部推理摘要，不能替代该产物。

---

## 10. Technical Decisions 速查

| 决策 | 备选方案 | 当前理由 | 代价 |
|---|---|---|---|
| Home-owned collection resource | component-owned duplicate caches | 四个 feature 共享同一 server-resource projection | Home 需维护 mutation propagation 与 selection reconciliation |
| `ViewState` union | 多个 booleans | 明确四个互斥标签 | data/error 未与 tag 绑定 |
| canonical regex helper | modal 内重复 regex | create/rename 共享规则 | 与 Backend 仍需手工同步 |
| shared append/map/filter | 每次 refetch | 少 round trip、四区即时同步 | concurrency/server drift |
| server-confirmed mutation | optimistic before response | 无 rollback 需求 | latency期间只显示 loading |
| single `pendingAction` | 多 flags / reducer | 当前 mutation 数量小 | 不能安全表达并发 actions |
| Popconfirm | immediate delete | 显式不可逆意图 | 仍不是 undo/authorization |
| separate load/modal/operation errors | one global error | recovery scope 不同 | state 数量增加 |

---

## 11. Interview Candidates（Task-level only）

以下只保留候选素材；Phase 11 Gate 与 Learning Review 未完成，不晋升项目级 Interview Guide：

- **30 秒主线**：我让第一个真实 Feature Component 沿 Phase 10 两个 seam 接入：typed API client 负责 transport；Home 管 shared query 四态，KnowledgeBaseManager 管 CRUD form/action feedback，并在成功后把 identity mutation 回传给 shared owner。
- **Engineering Questions**：为什么 loading/empty/error 不放进 API client？为什么前端 regex 不能替代 backend validation？local projection 与 refetch 如何取舍？
- **Failure Questions**：两个 delete 并发时 closure snapshot 会怎样？组件卸载后 request settle 怎么办？一个 `pendingAction` 能否表达多个 mutation？
- **Destructive UX**：Popconfirm 能证明什么，不能证明什么？为什么必须把 cascade 与不可逆性写进确认文案？
- **Evidence honesty**：本轮 real CRUD smoke 使用空 collection；它证明浏览器→FastAPI 的 collection flow，不证明有文件知识库的 rename/delete cascade。

本 Task 没有真实生产 incident，不构造 STAR。

---

## 12. Future Improvement（Future / Not implemented）

| 方向 | 触发条件 | 可能方案 |
|---|---|---|
| repository-owned component tests | T1101 开始频繁演进 | Vitest/RTL 或 browser tests 覆盖四态、validation、CRUD |
| request cancellation | workspace switch/retry race 出现 | AbortController + stale result guard |
| mutation serialization | 允许多个 card 同时操作 | global mutex 或 reducer/action map |
| delete functional update | concurrency evidence 出现 | `setCollections(current => ...)` 并从 next state 派生 view |
| runtime response validation | backend/frontend 独立发布 | schema validation / generated client |
| code-based error copy | 需要精确 CTA | `ApiError.code` discriminated mapping |
| query cache library | shared server resources 与 cache policies 明显增多 | 当前 page-level owner 足够；达到阈值再评估 TanStack Query |
| accessibility automation | modal/actions 继续增加 | focus、keyboard、axe、screen-reader smoke |
| responsive matrix | card数量与长名称增长 | 320/640/desktop + overflow/zoom tests |
| stale Phase label cleanup | Phase 11 UI product化 | shell phase/status copy 由 product context 决定 |

---

## 13. Verification Ledger（2026-09-04）

### 本轮执行

```text
cd frontend
npm run build
→ PASS：compiled、lint/type check、4/4 static page generation

真实浏览器 + local Next.js + real FastAPI/Chroma/filesystem
→ invalid create name: submit disabled
→ create empty collection: PASS
→ duplicate create: error displayed
→ same-name rename: submit disabled
→ valid rename: PASS
→ delete confirmation: cascade/irreversible warning visible
→ confirmed delete: collection removed，empty state visible
→ cleanup: temporary original/renamed collection absent

console
→ 1 expected error log from duplicate-name API response
→ no additional unexpected error observed in scoped flow

git diff --check
→ PASS
```

### 证据分级

| Evidence | Label | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| production build | `BUILD / REAL` | TS、Next compile、lint、static generation | 用户交互、真实 API semantics |
| canonical regex static comparison | `STATIC` | frontend/backend pattern 当前文本一致 | 所有边界 case 已自动回归 |
| empty collection CRUD smoke | `REAL BROWSER + REAL BACKEND` | browser→client→FastAPI 的 list/create/duplicate/rename/delete basic flow | 含文件 cascade、失败补偿、并发 |
| invalid/same-name disabled state | `REAL BROWSER` | 前端提前阻止 submit | request count 的自动 network assertion |
| load error + retry branch | `STATIC / NOT_AVAILABLE runtime` | code 存在 Alert 与 callback | 真实 backend outage 后恢复 |
| rename/delete injected failures | `NOT_AVAILABLE` | — | modal/page error recovery behavior |
| repository-owned frontend suite | `NOT_AVAILABLE` | — | 持续 regression protection |
| full Phase 11 flow | `DEFERRED` | — | upload/QA/files components 与 cross-feature state |

首次尝试使用本地 Playwright helper 时，两个服务均成功启动，但 Python 环境缺少 `playwright` 模块，因此脚本未执行、没有产生 PASS 证据，也没有安装新依赖。随后使用现有浏览器自动化完成上述 real smoke。临时 collection 与 server process 已清理。

---

## 14. 自测题与答案

### Concept

1. 为什么 API client 不应该拥有 loading/empty/success/error UI state？
2. `ViewState` union 比三个 boolean 好在哪里？它仍允许哪些 invalid combinations？
3. Frontend regex 与 Backend regex 为什么都需要？
4. Popconfirm 是安全边界、transaction，还是 interaction gate？
5. server-confirmed shared projection 与 optimistic update 有何区别？

### Code reading

6. Home `loadCollections()` 从 mount 到 empty/ready/error 的转换路径是什么？KnowledgeBaseManager 如何映射 view state？
7. `createTouched` 为什么独立于 `createName`？
8. Create 为什么使用 functional setter？
9. Rename 为什么使用 response 的 `old_name/new_name` 更新？
10. Delete 为什么存在 stale closure / lost-update 风险？
11. `pendingAction` 能表达哪些状态，不能表达哪些状态？
12. `getErrorMessage()` 为什么接收 `unknown`？
13. `totalFiles` 为什么不是独立 state？

### Design reasoning

14. 如果 mutation 成功但 local projection 失败，应该 refetch、rollback 还是显示 warning？
15. 如果用户切换菜单时 shared collection request 尚未结束，会发生什么？
16. 如何测试 initial load error 的 retry，而不真的关闭生产 Backend？
17. 为什么空 collection CRUD smoke 不能证明 collection cascade delete？
18. 如果未来引入 TanStack Query，哪些 ownership 可以交给 library，哪些仍属于 component？

### 答案要点

1. client 只拥有 transport；Home 拥有 shared collection lifecycle，feature 拥有具体 recovery/visual 与 transaction semantics。
2. union 强制选择一个 tag；但 data/error 仍是独立 state，类型上可出现 `success + []` 等组合。
3. frontend 做即时 UX，backend 对所有 callers 做最终 enforcement。
4. interaction gate；不提供 authorization、atomicity、undo 或 compensation。
5. 当前等待 server success 后由 callback 更新 Home projection；optimistic update 会先更新并需要失败 rollback。
6. Home effect → loading → list call → length 判断 empty/ready，异常进入 error；KnowledgeBaseManager 把 ready 映射为 success。
7. 区分“尚未交互”与“已经输入非法值”，避免 modal 一打开就显示红色错误。
8. async completion 时基于 React 最新数组，降低旧 closure 覆盖新 state 的风险。
9. server response 是已提交 mutation 的权威命名结果。
10. handler 直接读取 render 时的 `collections`；并发完成可能各自基于旧 snapshot filter。
11. 能表达一个 create/rename/specific delete；不能表达两个同时 pending 的 action。
12. JavaScript 可以 throw 任意值；必须 narrow 后才能安全读 message。
13. 它完全可由 collections reduce 得出，复制 state 会产生同步债务。
14. 先承认 server 已提交；通常 refetch durable truth 并给出恢复提示，不能假装 rollback 已发生。
15. Home 不会因菜单切换 unmount，request 会继续；version guard 只允许最新 request commit。当前没有 AbortController，因此网络工作本身不会取消。
16. stub client/module、browser route interception 或 test server failure；证据必须标 MOCKED/SUBSTITUTED。
17. 空库没有 uploads/chunks/index state，无法覆盖多存储删除顺序与残留。
18. query cache、dedupe、stale/refetch 可交给 library；业务 empty/error copy、modal intent、destructive confirmation 仍由 component 拥有。

---

## 15. T1101 Learning Pass 收口边界

T1101 Learning Pass 已完成。当前可准确表述为：**KnowledgeBaseManager 已实现真实 collection CRUD、四态 rendering、canonical frontend validation、mutation feedback 与 irreversible delete confirmation；production build 和一条空 collection 的真实 browser-to-FastAPI smoke 已通过。页面级 outage retry、mutation failure matrix、async race、含文件 cascade 与 repository-owned automated tests 仍未完整验证。**

T1101 本轮只新增/更新学习文档；没有修改 `KnowledgeBaseManager.tsx`、`validators.ts`、`page.tsx`、CSS、SPEC 或 TASKS，也没有在该次 pass 中启动 T1102。

---

## 16. T1102 学习：FileUpload 是两个状态机之间的协议适配器

### 一句话定位

T1102 把 Phase 5 的 multipart upload API 接入 Phase 10 shell：先加载并选择目标知识库，再由 `beforeUpload` 做浏览器侧 extension/size/empty guard，最后用 `customRequest` 把 Ant Design Upload lifecycle 翻译为 T1001 `uploadFile()`，并把 Backend 的 `SUCCESS`、`SUCCESS_WITH_WARNINGS` 或 `ApiError` 投影成不同 UI。[PROJECT FACT]

### 为什么不是“放一个上传按钮”

文件上传同时跨越五种状态：

```text
resource state      collection loading / ready / empty / error
selection state     selectedCollection
file validation     accepted / rejected before request
transport state     idle / uploading / success / warning / error
ingestion outcome   SUCCESS / SUCCESS_WITH_WARNINGS / exception
```

这些状态不能只靠 Ant Design 内部 file status 表达。`UploadFile.status` 只描述控件看到的单个文件；产品还需要知识库是否可选、Backend ingestion 是否部分成功、错误是否允许 retry，以及 result 中 chunks/warnings 的业务含义。

### 前端工程类比

- `beforeUpload` 类似 Express/Fastify route 前的 cheap guard：尽早拒绝，但不能替代后端 validation。
- `customRequest` 类似第三方 SDK adapter：把 library callback protocol 翻译成项目 Promise API。
- `SUCCESS_WITH_WARNINGS` 类似 HTTP 成功中的 domain partial success，不应该进入 catch，也不能渲染成纯绿色 success。
- 12%→100% 类似 job lifecycle indicator，不是 `Content-Length` 级 byte progress。

---

## 17. T1102 目标、依赖与明确边界

### 17.1 目标

- 从 Home shared collection source 填充 KB selector；保留合法选择，rename 时迁移，delete/缺失时回退第一项；
- 使用单文件 `Upload.Dragger`；
- 在 request 前拒绝不支持 extension、超过 50MB、0 byte 或无目标知识库；
- 通过 `uploadFile(file, selectedCollection)` 发送 multipart；
- 区分 idle/uploading/success/warning/error；
- 展示 success chunks、warning page/error code 和 user-actionable error。

### 17.2 依赖

| Dependency | T1102 使用方式 |
|---|---|
| T1001 | `uploadFile()`、`ApiError`、typed responses；collection GET 由 Home 集中调用 |
| T1002 | persistent `<FileUpload />` panel，由 `hidden` 切换可见性 |
| T1101 / shared collection source | CRUD success 更新 Home projection；mutation revision 驱动 selector reconciliation |
| Phase 5 Upload API | multipart、11 extensions、50MB、empty/duplicate/error/warnings contract |
| Ant Design Upload | Dragger、fileList、beforeUpload、customRequest callbacks、visual progress |

### 17.3 Out of scope

- folder/multi-file/batch upload；
- resume、chunked upload、后台 job progress；
- 浏览器端解析文件内容或判断 encrypted PDF；
- 取代 Backend filename/path-safety、duplicate、collection existence 与 failure atomicity；
- upload success 后自动递增 Home 中的 `file_count`（当前没有对应 callback）；
- T1103 QA panel 或独立 Phase 11 Engineering Review。

---

## 18. Code Understanding：`upload-validation.ts`

### 18.1 把规则从 UI component 抽成纯函数

```ts
export function validateUploadFile(
  file: Pick<File, 'name' | 'size'>,
): string | null
```

只依赖 `name` 与 `size`，让 validator 不必持有完整 DOM `File`，也更容易用 plain object 做 runtime probe。返回 `null | string` 把规则结果和用户提示合并；规模小时直接，规则增多后可能升级为 `{code, message}`，避免调用方靠文案识别错误。

### 18.2 Extension normalization

```ts
const dotIndex = fileName.lastIndexOf('.');
return dotIndex >= 0 ? fileName.slice(dotIndex).toLowerCase() : '';
```

行为要点：

- 只看最后一个 `.` 之后的 suffix；`archive.tar.gz` 按 `.gz` 判断；
- uppercase 会 lower-case，因此 `REPORT.PDF` 合法；
- 无点号返回空 extension，进入 unsupported；
- `accept` 只是 file-picker hint，真正阻止 request 的是 validator。

Frontend list 与 Backend `_ALLOWED_EXTENSIONS` 当前都包含 11 项：`.txt/.md/.csv/.json/.log/.pdf/.docx/.xlsx/.xlsm/.xltx/.xltm`。[STATIC CONTRACT REVIEW]

### 18.3 50MB 边界与校验顺序

```ts
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024;

if (file.size > MAX_UPLOAD_SIZE_BYTES) ...
if (file.size === 0) ...
```

只拒绝严格大于，因此恰好 50 MiB 被允许，与 SPEC AC-F002-04/AC-FE-02 一致。UI 文案写 MB，但代码使用 binary MiB-style bytes；因为 Backend 同样乘 `1024 * 1024`，observable boundary 一致。

顺序是 extension → oversize → empty。一个 0-byte `.exe` 会先显示 unsupported。SPEC 明确不冻结多违规输入的错误优先级，因此这不是 contract conflict；无论顺序如何，Backend 仍会完整拥有最终安全校验。

---

## 19. Code Understanding：Collection resource state

FileUpload 不再自行读取 collection endpoint；它消费 Home 提供的 `collections/collectionState/collectionError/collectionMutation/onRetryCollections`：

```text
Home load / CRUD mutation
→ shared collection source props
   ├── loading  → selector Skeleton + Dragger disabled
   ├── empty    → create-KB guidance + Dragger disabled
   ├── error    → Alert + Home retry callback
   └── ready    → resolveCollectionSelection()
                  ├── current still exists → preserve
                  ├── selected rename      → oldName → newName
                  └── current missing      → first collection
```

`handledMutationRevisionRef` 保证同一个 rename event 只被消费一次；`resolveCollectionSelection()` 先处理当前 owner 的 rename，再检查 current 是否仍存在，最后才 fallback。这个顺序把 selection reconciliation 变成四个 feature 共享的纯函数 contract。

Home 是 collection read model 的单一 frontend owner，Backend 仍是 durable truth。FileUpload 只拥有 `selectedCollection` 与 upload transaction state：它不会因为共享 resource 而把 `File`、progress、warning 或 retry input 提升到页面层。[PROJECT FACT]

---

## 20. Code Understanding：Ant Upload adapter

### 20.1 `beforeUpload` 是 no-request gate

```text
file selected/dropped
→ validateUploadFile(file)
   ├── error → set error UI + Upload.LIST_IGNORE
   └── valid
→ selectedCollection exists?
   ├── no → error + LIST_IGNORE
   └── yes → true → customRequest
```

`Upload.LIST_IGNORE` 同时阻止自动 upload 并避免 rejected file 留在 upload list。这里清理 `uploadResult/retryFile/fileList`，保证新 validation failure 不与旧 success/retry 混在一起。

### 20.2 `customRequest` 翻译 callback protocol

Ant Design 给出 `{file, onProgress, onSuccess, onError}`；项目真正的 transport 是 Promise-based `uploadFile()`。Adapter 将 `file as File` 交给 `runUpload()`，并在 Promise resolution/rejection 时调用 library callbacks，使 Ant Upload 自己的 file status 与项目 `UploadState` 同步。

这个 `as File` 依赖浏览器 input 的实际对象确实是 DOM `File`。如果未来支持 controlled synthetic item、remote URL 或 transformFile，必须重新验证这个 boundary。

### 20.3 为什么进度不是精确上传百分比

`runUpload()` 在开始时发送 12%，成功时发送 100%。中间没有 XHR `upload.onprogress`、stream bytes、Backend stage event 或 polling。因此：

- 12% 表示“请求已启动”；
- 100% 表示“Backend 已完成整个 ingestion 并返回”；
- 12% 到 100% 之间可能包含网络、parse、OCR、chunk、embedding、Chroma write；
- UI 的 active bar 是等待反馈，不是可审计的 pipeline progress。

准确话术应为 **coarse lifecycle progress indicator**，不能称为真实 byte/pipeline progress telemetry。[ENGINEERING KNOWLEDGE]

---

## 21. Upload state machine 与 outcome projection

```text
idle
 ├── invalid file / no KB ───────────────→ error(no retryFile)
 └── accepted file → uploading(12%)
                         ├── throw ───────→ error(retryFile retained)
                         ├── SUCCESS ─────→ success(result, 100%)
                         └── SUCCESS_WITH_WARNINGS → warning(result, 100%)

success/warning/error
 └── continue / remove / collection change → idle
error with retryFile
 └── retry → uploading
```

### SUCCESS

绿色 Alert 显示 `file_name`、`collection_name` 和 `chunks`。成功后 `retryFile=null`，避免误把已提交文件再作为失败重试。

### SUCCESS_WITH_WARNINGS

这是 HTTP 200/domain success，raw file 和有效 chunks 已 durable commit；UI 使用黄色 warning，而不是抛 error。每条 warning 映射 `page_number + error_code`：

- `OCR_PAGE_FAILED` → OCR 识别失败；
- `PAGE_RENDER_FAILED` → 页面渲染失败。

当前 mapping 是 closed TypeScript `Record`，compile time 能检查已知 union；但 T1001 success payload 没有 runtime validation。若 Backend 滚动发布返回未知 warning code，运行时文案可能成为 `undefined`。这是 contract-drift boundary，不是当前 frozen schema 已失败。

### ERROR

如果 request 已开始，`retryFile` 被保留，Error Alert 显示“重试”；如果 validation 在 request 前失败，没有 retryFile，显示“重新选择”。这把 recovery action 与 side-effect boundary 对齐：只有真正可以安全重发同一 file 的失败路径才提供 retry。

但 duplicate error 的 retry 如果不换 KB/filename 仍会重复失败；当前 `ERROR_MESSAGES` 提供解释，真正修复输入仍需用户重新选择文件或知识库。

---

## 22. Data Flow：从浏览器 File 到 persisted ingestion result

```text
DOM File {name, size, bytes}
→ accept hint
→ validateUploadFile(name, size)
→ beforeUpload returns true
→ customRequest
→ runUpload(file)
→ api-client uploadFile()
→ FormData[file, collection_name]
→ POST /api/upload
→ Backend filename/extension/size/empty/KB/duplicate validation
→ raw write → parse/OCR → chunk → embed → Chroma → index invalidation
→ UploadResponse
→ success | warning UI
```

### 两道 validation 的关系

| Frontend 能做 | Backend 必须重做/独有 |
|---|---|
| extension、`File.size`、empty、selected KB presence | filename path safety、真实 body bytes、collection existence、case-insensitive duplicate |
| 快速提示并阻止正常 UI request | 对任何 caller 强制执行 |
| 固定 50MB 常量 | 以运行时 settings 为最终配置 |

这里存在配置 drift 风险：Frontend 固定 50，Backend `MAX_UPLOAD_SIZE_MB` 可配置。如果部署把 Backend 改为其他值，前端提示/guard 不再等价。当前 SPEC default/frozen acceptance 使用 50；未来若真要配置化，应让 frontend 获得公开 capability/config，而不是读取 backend secret env。[ENGINEERING KNOWLEDGE]

---

## 23. Error mapping 与 safety boundary

`ERROR_MESSAGES` 把 backend codes 转成 feature-specific recovery copy：unsupported、unsafe filename、empty、too large、duplicate、missing collection、parse failure、network failure。未列出的 code fallback 到 `ApiError.message`。

这层 mapping 的价值是 UI 不依赖后端中文文案稳定性；code 才是 machine contract。边界包括：

1. mapping 使用 `Record<string,string>`，不会要求所有 `ApiErrorCode` exhaustive；新增 backend code 依靠 fallback，不会 compile-fail。
2. Frontend 不读取/展示 arbitrary `details`，避免把内部诊断直接暴露。
3. `INVALID_FILE_NAME` 没有 frontend path validation；这是合理 defense boundary，因为浏览器 file picker 通常只给 basename，但 Backend 必须覆盖非浏览器 caller。
4. retry 会重发同一个 in-memory `File`；页面 refresh/unmount 后该对象不会持久化。
5. switching collection 调用 `clearOutcome()`，会清除 retry file，避免把旧 KB 失败文件无意重发到新 KB。

---

## 24. T1102 Verification

### 本轮执行证据

```text
npm run build
→ PASS：compiled、lint/type check、4/4 static page generation
→ / route 153 kB；First Load JS 274 kB（observation only）

validateUploadFile runtime probes
→ uppercase supported extension: PASS
→ unsupported extension: PASS
→ 0 byte: PASS
→ exactly 50 * 1024 * 1024: PASS
→ limit + 1 byte: PASS
→ 5/5 PASS

真实浏览器 + local Next.js + real FastAPI collection list
→ upload workspace renders
→ real collection appears and is selected by default
→ accept attribute contains all 11 extensions
→ temporary collection deleted after check
```

### Evidence ledger

| Evidence | Label | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| production build | `BUILD / REAL` | FileUpload/adapter/types/CSS compile 与 static generation | upload runtime outcomes |
| validator 5/5 | `RUNTIME / ISOLATED` | extension、empty、exact 50MB boundary | browser no-request network assertion |
| upload UI + real collection selector | `REAL BROWSER + REAL BACKEND READ` | shell mount、GET collections、default selection、11-format accept | file body POST/ingestion |
| `beforeUpload`/LIST_IGNORE | `STATIC` | rejection control flow 存在 | rejected file 确实产生 0 requests |
| valid upload success | `NOT_AVAILABLE` | — | raw/chunks/index commit 与 chunks display |
| SUCCESS_WITH_WARNINGS | `STATIC`; runtime `NOT_AVAILABLE` | branch/mapping 存在 | 真实 OCR partial success UI |
| error + retry | `STATIC`; runtime `NOT_AVAILABLE` | retryFile/action control flow 存在 | backend failure 后真实 retry |
| repository-owned frontend tests | `NOT_AVAILABLE` | — | 持续 regression suite |

当前 IDE 提到的 `.t1102-warning.pdf` 在本轮 filesystem 检查时并不存在，因此没有把它作为 warning evidence，也没有创建、修改或删除该路径。浏览器环境能验证 UI 与 real collection read，但当前自动化接口无法注入一个真实 `File` 到 file input；因此没有虚构 valid upload 或 warning outcome PASS。

Build 后 `/` route size 相比 T1101 evidence 增长，但本轮没有 bundle baseline/budget 或 analyzer；274 kB 只能记录为 time-specific observation，不能直接宣称 performance regression。

---

## 25. T1102 Engineering Questions（短摘要）

1. 为什么 `accept` 不能替代 `beforeUpload`？——它主要是 picker hint，仍可被拖拽或程序化输入绕过。
2. 为什么 Frontend validation 不能替代 Backend？——浏览器不是 trust boundary，配置也可能 drift。
3. 为什么 warning 不是 error？——Backend 已 durable commit 有效结果；warning 描述部分页面处理失败。
4. 12% 是什么？——request lifecycle marker，不是 byte/ingestion stage progress。
5. 为什么换 KB 要清空 outcome？——避免 result/retryFile 的 collection ownership 漂移。
6. 为什么上传成功不直接更新 KB card 的 `file_count`？——collection list 已共享，但 FileUpload 没有 success callback 更新 Home projection；共享 resource 不会自动同步所有 child mutation。
7. `customRequest` 的作用是什么？——把 Ant callback lifecycle 适配到项目 Promise client。
8. retry 是否总是正确？——network/transient failure 可重试；duplicate/parse failure 未改变输入时可能确定性再次失败。

---

## 26. T1102 Interview Candidates（Task-level only）

- **30 秒主线**：我没有让 Upload 组件直接拥有 HTTP 细节，而是用 `beforeUpload` 做 cheap client guard、用 `customRequest` 适配 centralized API client，再把 Backend success/warning/error 投影为五态 UI。
- **高价值追问**：为什么 50MB 用 `>` 而不是 `>=`？为什么 `accept` 不是校验？为什么 partial OCR failure 必须显示 warning 而不是 error？
- **工程边界**：粗粒度进度、frontend/backend config drift、success payload runtime validation、persistent panel 中 `File` 的内存生命周期，以及 upload success 尚未回写 shared `file_count`。
- **诚实证据**：validator 与 real selector 已验证；真实 file upload、warning fixture 和 retry path 本轮没有 runtime evidence。

本 Task 没有生产 incident，不构造 STAR；Phase 11 Gate 前不晋升 Interview Guide。

---

## 27. T1102 自测题与答案

### Questions

1. `accept`、`beforeUpload`、Backend validation 分别是什么责任？
2. 为什么恰好 50MB 被允许？
3. `.PDF`、`archive.tar.gz`、无扩展名分别怎样处理？
4. `Upload.LIST_IGNORE` 与返回 `false` 的产品意图有什么不同？
5. `customRequest` 如何连接 callback API 与 Promise API？
6. `uploadState` 为什么需要 `warning`？
7. `retryFile` 为什么只在 request 开始后保存？
8. collection change 为什么清空 outcome？
9. 12%→100% 为什么不是真实进度？
10. 前端固定 50MB、后端可配置会有什么 drift？
11. SUCCESS_WITH_WARNINGS 是否允许 rollback？
12. 为什么空 collection 的 selector evidence 不等于 upload E2E？
13. 菜单切换后 FileUpload state 会怎样？
14. 两次快速选择文件/重试可能出现什么 race？
15. 如何测试 warning UI 而不调用真实 OCR provider？证据应标什么？

### Answer keys

1. accept 是 hint；beforeUpload 是 UX/no-request guard；Backend 是最终 enforcement。
2. contract 拒绝 `size > limit`，等于 limit 合法。
3. `.PDF` lower-case 后合法；`.gz` 不在 whitelist；无扩展名得到空 suffix 并拒绝。
4. LIST_IGNORE 既阻止 upload 又不把 rejected file 保留在 list；具体 Ant 行为应由 component test 锁定。
5. adapter把 file/callbacks 交给 runUpload，Promise resolve/reject再回调 onSuccess/onError/onProgress。
6. partial success 已 commit，既不是纯 success 也不是 failed request。
7. validation failure 不值得原样 retry；transport/backend failure 才保留同一 File。
8. result、error 和 retry File 都绑定原 selected collection。
9. 没有 byte/stage events，中间只是等待 Backend 整体完成。
10. UI 可能提前拒绝 Backend 本可接受的文件，或允许 Backend 会拒绝的文件。
11. 不允许按 FAILED 对待；有效 chunks/raw 已是 durable outcome。
12. 只执行 GET collections，没有 multipart POST、parser、embedding 或 storage commit。
13. 当前 persistent panel 只切换 wrapper `hidden`，local selected/result/retry state 保留；collection source 由 Home 共享，不会因菜单切换重新 fetch。
14. fileList、uploadState 和 callbacks 可能互相覆盖；当前 disabled 降低正常 UI 并发，但没有完整 race proof。
15. stub `uploadFile()` 返回 typed warning response 并做 component/browser test，标 `MOCKED`，不能叫 real OCR E2E。

---

## 28. T1102 Learning Pass 收口边界

T1102 Learning Pass 完成。当前准确表述是：**FileUpload 已实现知识库选择、11-format/empty/50MB frontend validation、Ant Design `beforeUpload + customRequest` adapter、coarse progress indicator，以及 success/warning/error outcome UI；production build、validator 5/5 probes 和真实 collection selector 已验证。真实 multipart ingestion、SUCCESS_WITH_WARNINGS fixture、error retry、no-request network assertion 与 repository-owned frontend regression tests 仍为 `NOT_AVAILABLE / DEFERRED`。**

本次只更新 Technical Learning、README 与 Project Map；不修改 `FileUpload.tsx`、`upload-validation.ts`、`page.tsx`、CSS、SPEC 或 TASKS，不启动 T1103，不执行 Phase 11 Gate/Learning Review/Engineering Review，不 commit/push。

---

## 29. T1103 学习：QAPanel 是 conversation transaction coordinator

QAPanel 看起来像聊天框，真正职责却是协调一次有边界的 conversation transaction：选择知识库、冻结本次问题与历史快照、调用 `POST /api/query`、拒绝 stale response、把成功结果提交为一对消息，并为失败保留 retry input。[PROJECT FACT]

可以用 TypeScript/Node 的 controller 类比：

```text
React controlled input
  → command validation
  → request snapshot
  → async API adapter
  → version guard
  → atomic UI commit or recoverable failure
```

这里至少有三个彼此相关、但不应混为一谈的模型：

1. `CollectionState`：能否选到 query target。
2. `QueryState`：当前 request lifecycle 与 outcome。
3. `history`：已经完成并可用于下一轮 prompt 的 conversation facts。

`pendingQuestion` 不属于 completed history。它是 in-flight/retry buffer；只有 Backend 成功返回后，问题与答案才一起进入 `history`。这避免失败问题被错误发送给下一次请求，当成一轮已经完成的对话。

---

## 30. T1103 目标、依赖与不做什么

### 目标

- 消费 Home shared knowledge-base source，并维护可自动 reconcile 的当前选择；
- 支持按钮与 `Ctrl+Enter` 发送问题；
- 显示 user bubble、loading answer、Markdown answer 与 expandable sources；
- 在 React state 中维护最近 20 条 messages；
- 将 `COLLECTION_EMPTY` 映射为独立 `empty_kb` warning；
- 普通错误保留失败问题并提供 retry；
- knowledge-base switch 清空 conversation，并隔离旧的 async response。

### 依赖

| Dependency | QAPanel 使用方式 |
|---|---|
| T1001 API client | `queryQA()`、normalized `ApiError`；collection GET 由 Home 集中调用 |
| T1002 shell | persistent QA panel、responsive workspace 与 shared collection props |
| T0805 Query API | typed request/response 与 error envelope |
| F014 | history 由 Frontend 持有、最多 20 条、切换 KB 清空 |
| F015 | Backend-owned `sources`；Frontend 只展示，不重建 citation |
| `react-markdown` | 把 Backend answer string 转成 React element tree |

### 明确不做

- 不把 history 写入 localStorage、cookie 或 Backend；refresh/unmount 后丢失是 v1 contract；
- 不实现 token streaming、cancel、chat export 或 server-side session；
- 不让 Frontend 自己执行 retrieval、拼 context 或推导 sources；
- 不实现 T1104 FileManager；cross-component resource consistency 由 T1105/F-1 remediation 统一处理；
- 不把 Task Learning Pass 当作 Phase Gate、Phase Learning Review 或 Engineering Review。

---

## 31. 两个状态机与一个提交日志

### 31.1 CollectionState

```text
loading
  ├── collections.length > 0 → ready
  ├── collections.length = 0 → empty
  └── request throws          → error

error --重新加载--> loading
```

CollectionState 来自 Home；QAPanel 通过 `resolveCollectionSelection()` 保存仍合法的 selection、消费 rename revision，或在删除/缺失时回退到第一项。resolved owner 一旦改变，effect 会递增 request version 并调用 `resetConversation()`，因此 shared resource change 与 conversation ownership rule 在同一处汇合。[PROJECT FACT]

### 31.2 QueryState

```text
idle
  └── valid send → loading
                    ├── 200 → success
                    ├── COLLECTION_EMPTY → empty_kb
                    └── other throw → error

error / empty_kb --retry pendingQuestion--> loading
any state --KB switch--> idle + clear conversation
```

`success` 没有单独的 success banner；它表示 request 已提交到 `history`，渲染层从 message records 得到 answer 和 sources。这里 state 表示 lifecycle，不重复存储 response payload。

### 31.3 history 是 append-only completed log

正常成功路径一次提交两条：

```ts
[
  { role: 'user', content: normalizedQuestion },
  { role: 'assistant', content: response.answer, sources: response.sources },
]
```

随后：

```ts
[...current, ...completedPair].slice(-20)
```

因此正常路径保持 Q/A pair 顺序，最多 10 轮。注意 contract 说的是最近 20 条 messages，不是 20 轮。当前输入只能由成功 pair 产生，所以通常是偶数；若未来支持 system message、导入历史或 partial commit，仅按 message slicing 可能切在 pair 中间，需要重新定义 invariant。

---

## 32. DisplayMessage 与 request DTO 必须分层

`DisplayMessage extends ChatMessage`，增加：

- `id`：React list identity；
- `sources?`：assistant answer 的展示附件。

但 Query API history 只接受 `{role, content}`。`toRequestHistory()` 同时完成两个动作：

```ts
history.slice(-20).map(({ role, content }) => ({ role, content }))
```

1. defensive truncation：即使 UI state invariant 被未来代码破坏，请求仍只发送最近 20 条；
2. DTO projection：剥离 `id` 和 `sources`，避免把 view-only data 泄漏到 API contract。

这相当于 Node service 中从 rich domain/view object 显式构造 request DTO，而不是直接 `JSON.stringify(entity)`。TypeScript structural typing 不能替代 runtime payload construction；真正决定 wire format 的是被序列化的 object。

`sources` 不应重新进入 history，因为 F014 只用对话文本帮助指代消解；来源是本轮答案的 evidence metadata，不是下一轮 prompt 中独立可信的新事实来源。

---

## 33. sendQuestion：先快照，再进入 async boundary

发送流程可精读为：

```text
questionToSend.trim()
  → reject empty / no collection / already loading
  → snapshot requestHistory
  → allocate requestVersion
  → pendingQuestion = normalized question
  → clear composer and prior error
  → queryState = loading
  → queryQA(question, selectedCollection, undefined, requestHistory)
  → version still current?
      ├── no: ignore stale completion
      └── yes: commit pair or failure state
```

几个工程细节：

- `normalizedQuestion` 确保 whitespace-only input 不发 request；Backend 仍必须重复校验，因为 browser 不是 trust boundary。
- `requestHistory` 在 `await` 前创建，是本次 request 的 immutable snapshot；后续 React render 不会改变已经发出的 body。
- `topK` 传 `undefined`，使 API client 不写入 `top_k`，由 Backend 使用 frozen default 5。
- composer 在 request 开始时清空，但问题保存在 `pendingQuestion`；这既让 UI 立即显示 user pending bubble，也支持失败重试。
- `queryState === 'loading'` 与 disabled button/input 降低正常 UI double-submit；它不是跨事件/程序化调用的形式化互斥锁。

成功时 question + answer 作为一个 React state update 一起提交，避免只出现半轮 completed conversation。失败时 completed `history` 不变；pending question 留在 error/warning 上方，retry 仍发送相同 question 和相同 completed-history snapshot（只要期间未切换 KB）。

---

## 34. requestVersionRef：防的是 stale commit，不是取消网络请求

切换知识库时：

```ts
requestVersionRef.current += 1;
setSelectedCollection(value);
resetConversation();
```

每个 request 也领取新的 version。response/error 返回后先比较：

```ts
if (requestVersion !== requestVersionRef.current) return;
```

假设 KB-A 的请求仍在 flight，用户切到 KB-B。即使 A 最后成功，version 已经失效，所以它不能把 A 的 answer/sources 写进 B 的 history。这是 last-intent-wins 的 stale response guard。

但它没有 `AbortController`，所以：

- Backend/LLM 工作仍会继续，算力与网络成本不会取消；
- old Promise 仍会 settle，只是 Frontend 丢弃结果；
- 它只保护 UI commit，不提供 server-side cancellation 或 exactly-once semantics。

这里选择 `useRef` 而不是 state，是因为 version 是跨 async callback 的 mutable coordination token，不需要触发 render。Node 类比是 request generation counter，而不是业务数据字段。

还有一个细节：当前 input 在 `loading` 时 disabled，正常 UI 无法再发送第二个问题；但 KB Select 本身未 disabled，所以用户仍可在请求期间切换知识库，switch isolation path 是可达且有意义的。

---

## 35. Markdown 与 sources：答案和证据是平行通道

assistant content 使用：

```tsx
<ReactMarkdown>{message.content}</ReactMarkdown>
```

它负责 headings、lists、bold、inline code 与 fenced code blocks 的 structure；CSS 负责视觉层。没有使用 `dangerouslySetInnerHTML`，默认也没有启用 raw HTML plugin，因此 Backend answer 不会被当成任意 HTML 直接执行。这降低 XSS surface，但不等于完成完整 Markdown security/accessibility audit。

来源由 Backend `sources[]` 独立返回，QAPanel 用 `Collapse` 展示 `file_name` 与 `relevance_score.toFixed(3)`：

```text
answer Markdown ───────────→ human-readable explanation
sources[] ────────────────→ inspectable evidence records
```

Frontend 不解析答案中的 `[1]`，也不把 answer 与 source 强行按内联编号连接；这符合 frozen v1 contract：LLM 正文不要求内联引用，Backend-owned sources 单独展示。

`chunk_id` 是 source list key，符合 immutable identity；`file_name` 只显示，不作为 identity。`relevance_score` 是 Backend 输出的 final hybrid relevance，Frontend 只格式化三位小数，不重算、不 resort、不声称是概率。

边界：当前 Collapse 只显示 file name + score，虽然 `file_id/chunk_id` 存在于 type 中，却不展示定位详情或 preview deep link；这属于未来产品设计，不应在 T1103 擅自扩展。

---

## 36. `empty_kb` 与“无匹配内容”不是同一件事

QAPanel 只在 `ApiError.code === 'COLLECTION_EMPTY'` 时进入 `empty_kb`：

- collection 存在但 0 chunks；
- Backend 返回 HTTP 409；
- retrieval 与 LLM 不应被调用；
- UI 提示“知识库暂无文档，请先上传文件”。

相反，一个有 chunks 的知识库可能因 relevance filter 得到 0 results。Backend contract 要求继续调用 LLM，让它说明当前知识库没有足够信息，并返回 `sources=[]`。这是 HTTP 200 success，不应被 Frontend 误映射为 `empty_kb`。

```text
0 persisted chunks → 409 COLLECTION_EMPTY → warning + upload guidance
persisted chunks, 0 relevant results → 200 answer + [] → normal assistant message
```

这个区分体现了 storage state 与 retrieval outcome 的不同。仅凭 `sources.length === 0` 推断 empty KB 会违反 contract；当前实现没有犯这个错误。

---

## 37. Retry、history ownership 与失败语义

error/empty alert 调用：

```ts
sendQuestion(pendingQuestion)
```

重试不是“重复渲染”，而是重新执行完整 `queryQA()`。它使用当时 React closure 中的 completed `history` 与当前 selected collection。由于 loading 时 history 不变，而且 KB switch 会清空 pending/error 并增加 version，正常路径可保持 ownership：失败问题仍属于原 KB。

不同错误的 retry value 并不相同：

- `NETWORK_ERROR`、`LLM_UNAVAILABLE`：可能是 transient，retry 有价值；
- `COLLECTION_EMPTY`：不上传文件就重试，通常确定性失败；按钮虽存在，但 recovery copy 已指出真正动作；
- `LLM_NOT_CONFIGURED` / `LLM_AUTH_FAILED`：需要管理员修配置，用户 retry 通常无效；
- `INVALID_HISTORY_FORMAT`：当前 UI 构造的 history 应合法；若真的出现，切 KB/reset 比原样 retry 更合理。

因此“所有 error 都显示同一个 retry action”是简单 v1 UX，不等于每种 failure 都具备相同 recoverability。Phase Engineering Review 可以进一步讨论按 error taxonomy 选择 action，但本 Learning Pass 不修改实现。

一个值得记录的细节：retry 成功后 `pendingQuestion` 清空；retry 失败则保持。成功 answer 使用 `Date.now()` 生成 pair IDs，同一 pair 后缀不同；跨极短时间的不同成功请求理论上可能同毫秒，但 UI 阻止并发，实际碰撞风险很低。若未来支持并发/持久化，应使用 UUID 或 request ID。

---

## 38. 完整 data flow 与 trust boundaries

```text
User selects collection
  → GET /api/collections
  → selectedCollection

User types question
  → trim + local empty/loading guards
  → project latest completed 20 messages
  → POST /api/query
       {question, collection_name, history}
  → API validates question / collection / top_k / history
  → collection chunk-count preflight
  → hybrid retrieval
  → context assembly + history formatting
  → LLM answer generation
  → Backend assembles sources
  → {answer, sources, query, collection_name}
  → version guard
  → append completed user/assistant pair
  → ReactMarkdown + expandable source list
```

Frontend guard 的目标是 immediate UX；Backend validation 是 security/correctness boundary。Frontend 持有 conversation lifecycle，Backend 持有 retrieval、prompt construction、LLM access 与 source truth。API key 永远不进入 browser bundle。

当前 `request<T>()` 对 success JSON 使用 TypeScript assertion，而没有 runtime schema validation。因此 build 能证明 compile-time shape agreement，不能证明 deployed Backend 永远返回正确 `sources`。例如 malformed `relevance_score` 会在 `.toFixed()` 处暴露 runtime failure。这是 T1001 的既有边界，在 T1103 渲染路径上变得具体可见。

---

## 39. T1103 Verification 与证据账本

### 本轮执行证据

```text
npm.cmd run build
→ PASS: compiled successfully
→ PASS: lint/type validity
→ PASS: 4/4 static pages generated
→ / route 194 kB; First Load JS 315 kB (observation only)

Static contract inspection
→ QAPanel mounted in qa shell slot
→ react-markdown dependency installed and imported
→ five QueryState values present
→ history projection/truncation and KB-switch reset present
→ stale response guard present
→ source rendering uses chunk_id + file_name + relevance_score
```

### Evidence ledger

| Evidence | Label | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| production build | `BUILD / REAL` | component/types/dependency/CSS compile；static generation | Backend、LLM 或 browser interaction outcomes |
| QAPanel/source/history close read | `STATIC` | current control flow 与 frozen contract 对齐 | event sequence 在真实 browser 中必然无 bug |
| Markdown rendering path | `STATIC` | answer 交给 `react-markdown`；相关 CSS 存在 | headers/lists/code 的视觉与 accessibility browser evidence |
| collection selector | `STATIC` | list/default/error/empty branches 存在 | 当前 Backend collection read 成功 |
| success + sources | `NOT_AVAILABLE` | — | 真实 retrieval、LLM、Markdown answer 与 sources flow |
| 409 empty KB | `NOT_AVAILABLE` | branch 与 copy 存在 | 真实 409、无 retrieval/LLM side effect 与 UI outcome |
| error + retry | `NOT_AVAILABLE` | retry control flow 存在 | Backend failure 后真实第二次 request |
| Ctrl+Enter | `STATIC` | key handler 存在 | browser keyboard interaction |
| repository-owned frontend tests | `NOT_AVAILABLE` | — | repeatable component/E2E regression suite |

本轮没有启动真实 LLM/provider，也没有把 Backend unit tests、build 或 static branch 当成 QA E2E。T1103 的 AC-F017-03 / AC-FE-03 / AC-FE-05 需要 browser-to-real-Backend evidence；其中完整 QA 还依赖真实 embedding/vector data 与 LLM provider，留给独立验证或 Phase 12 E2E。

Bundle 从 T1102 记录的 153 kB / 274 kB 增至 194 kB / 315 kB，与加入 `react-markdown` 和 QA code 的时间点相关，但没有 analyzer、baseline policy 或 route-level budget，不能仅凭相关性断言具体依赖贡献或 performance regression。

---

## 40. T1103 Engineering Questions（短摘要）

1. 为什么 pending question 不立即进入 history？——失败 request 不是 completed conversation fact。
2. 为什么 history 不发送 sources/id？——它们是 view metadata，不属于 F014 request DTO。
3. 为什么切 KB 要递增 request version？——清 state 不足以阻止旧 Promise 随后提交。
4. request version 是否取消 LLM？——否，只丢弃 stale UI completion。
5. 为什么 0 sources 不等于 empty KB？——前者可能是 relevance outcome；后者是 0 persisted chunks。
6. 为什么 answer 与 sources 分开？——v1 citation contract 由 Backend 提供独立 evidence array，不依赖 LLM inline marker。
7. 为什么 score 不能说成概率？——它是 retrieval relevance score，Frontend 只做格式化。
8. 20 条为什么是 10 轮？——正常 transaction 每次原子追加 user + assistant 两条。
9. build PASS 为什么不是 QA flow PASS？——build 不执行 browser events、HTTP、retrieval 或 LLM。
10. 所有错误都适合 retry 吗？——否，transient 与 configuration/domain errors 的 recovery 不同。

---

## 41. T1103 Interview Candidates（Task-level only）

- **30 秒主线**：我把聊天 UI 当作 conversation transaction coordinator。发送时冻结 question/history，成功后原子提交 Q/A pair；失败保留 pending question；KB switch 用 generation token 清历史并拒绝 stale response。
- **高价值追问**：为什么 `useRef` 能解决 stale commit，却不能取消 request？为什么 sources 不进入下一轮 history？为什么 `COLLECTION_EMPTY` 不能由 `sources=[]` 推断？
- **TypeScript/Node 类比**：`DisplayMessage → ChatMessage` 是显式 DTO projection；`requestVersionRef` 是 generation counter；`queryQA` 是 centralized transport adapter。
- **安全边界**：ReactMarkdown 默认渲染 element tree；Frontend 不持有 provider secret；Backend 仍负责 input/history validation 与 source truth。
- **诚实证据**：build 与 static contract inspection 已通过；真实 provider QA、empty-KB browser flow、retry 和 keyboard interaction 本轮没有 runtime evidence。

本 Task 没有生产 incident，不构造 STAR；Phase 11 Gate 前不晋升项目级 Interview Guide。

---

## 42. T1103 自测题与答案

### Questions

1. `history`、`pendingQuestion`、`question` 各自代表什么生命周期？
2. 为什么失败问题不能先写入 completed history？
3. `toRequestHistory()` 同时建立了哪两个边界？
4. 第 11 轮成功后，history 保留多少条、多少轮？
5. 为什么 sources 不应传回下一轮 history？
6. `requestVersionRef` 如何阻止 KB-A 响应污染 KB-B？
7. 它为什么不等于 request cancellation？
8. `queryQA(..., undefined, history)` 中的 `undefined` 有什么语义？
9. 何时进入 `empty_kb`？
10. 有文档但没有相关结果时，Frontend 应进入 `empty_kb` 吗？
11. `relevance_score.toFixed(3)` 改变了 score 语义吗？
12. 为什么用 `chunk_id` 做 source list key，而不是 `file_name`？
13. ReactMarkdown 当前降低了哪类风险，又没有证明什么？
14. 为什么 `queryState=success` 不需要另存 response object？
15. Ctrl+Enter handler 存在为何仍只是 STATIC evidence？
16. 哪些 error 原样 retry 多半无效？
17. 页面切走 QA panel 后 history 会怎样？
18. 如何在不调用真实 LLM 的情况下测试 Markdown/sources/empty/error UI？证据应标什么？

### Answer keys

1. `question` 是 composer draft；`pendingQuestion` 是 in-flight/retry buffer；`history` 是 completed conversation log。
2. request 可能失败；先提交会把不存在的 answer 前提带入后续 prompt。
3. 最近 20 条 truncation，以及从 display model 到 `{role,content}` request DTO projection。
4. 保留最近 20 条，即正常路径最近 10 轮。
5. sources 是 evidence metadata；F014 history 只接受 role/content，并且 history 不能升级为额外事实源。
6. switch 增加 current version；A settle 时 version mismatch，直接 return。
7. 没有 AbortController/server cancellation；网络与 Backend 工作仍运行。
8. API client 不发送 `top_k`，Backend 使用默认值 5。
9. 仅收到 `ApiError` 且 code 为 `COLLECTION_EMPTY`。
10. 不应；这是 200 answer + empty sources 的合法 success outcome。
11. 不改变，只把展示精度格式化为三位小数；它仍不是概率。
12. chunk_id 是 immutable unique identity；file_name 只是 display name，且一个文件可贡献多个 chunks。
13. 未直接执行任意 raw HTML；但尚无完整 XSS、plugin、visual 或 accessibility runtime audit。
14. success payload 已规范化为 history message；另存会制造 duplicated state/source of truth。
15. 静态存在不证明真实 key event、focus、IME 或 browser default behavior。
16. empty KB、未配置/认证失败、输入或 history 格式错误通常需要改变外部状态或输入。
17. `page.tsx` conditional render 会 unmount QAPanel；v1 不持久化，所以 local history 丢失。
18. mock `listCollections/queryQA` 做 component/browser tests，覆盖 typed fixtures；标 `MOCKED`，不能叫 real QA/LLM E2E。

---

## 43. T1103 Learning Pass 收口边界

T1103 Learning Pass 完成。当前准确表述是：**QAPanel 已实现 knowledge-base selection、controlled composer、Ctrl+Enter、pending/loading/success/error/empty-KB outcomes、Markdown answer、expandable Backend-owned sources、最近 20 条 message history、KB switch reset 与 stale-response guard；production build 和 static contract inspection 已验证。真实 browser QA、retrieval/LLM answer、409 empty-KB side-effect boundary、retry event sequence 与 repository-owned frontend regression tests 仍为 `NOT_AVAILABLE / DEFERRED`。**

本次只更新 Technical Learning、README 与 Project Map；不修改 `QAPanel.tsx`、`api-client.ts`、`types.ts`、`page.tsx`、CSS、SPEC 或 TASKS，不启动 T1104，不执行 Phase 11 Gate/Learning Review/Engineering Review，不 commit/push。

---

## 44. T1104 学习：FileManager 是 persisted-state inspector 与 destructive-command surface

FileManager 不是普通“文件浏览器”。它展示的是 Backend 从 persisted chunk metadata 聚合出的 `FileRecord`，preview 展示的是 persisted chunk content 的诊断性重建，而 delete 则触发跨 raw filesystem、Chroma vectors/metadata 和 keyword index 的不可逆级联。[PROJECT FACT]

可以用 TypeScript/Node 后台管理页类比：

```text
read model table
  ├── inspect(resource identity) → diagnostic projection
  └── destructive command       → confirm → server commit → local projection
```

三个动作拥有不同语义：

| UI action | Backend truth | Frontend responsibility |
|---|---|---|
| list | persisted chunks 聚合出的 file records | 展示、格式化、区分 empty/error |
| preview | persisted chunks 按 `chunk_index` 重建后的文本 | 展示诊断内容与 truncation notice |
| delete | irreversible three-surface cascade | 明示风险、以 `file_id` 发命令、成功后同步 view |

最重要的学习边界是：**UI 表格不是 source of truth，raw filename 不是 resource identity，Modal 中的文本也不是 original document fidelity。**

---

## 45. T1104 目标、依赖与明确边界

### 目标

- 消费 Home shared knowledge bases，并选择/自动 reconcile 一个 collection；
- 读取文件列表，展示 name、size、upload time、chunk count 与 ingestion status；
- 用 immutable `file_id` 作为 row key、preview identity 和 delete identity；
- preview modal 覆盖 loading/success/error，并提示内容截断；
- delete 前明确说明不可恢复及级联范围；
- delete 成功后从当前 table 移除记录，并通过 callback 更新 Home shared file count；
- 对 collection、file-list、preview 与 action failure 提供分层反馈；
- 使用 version/ref guards 避免部分 stale async result 污染新 collection。

### 依赖

| Dependency | FileManager 使用方式 |
|---|---|
| T1001 API client | `listFiles()`、`previewFile()`、`deleteFile()`、`ApiError`；collection GET 由 Home 集中调用 |
| T1002 shell | persistent files panel、responsive content area 与 shared collection props |
| T0901 | persisted `FileRecord` list contract |
| T0902 | chunk-based preview contract 与 5000-char Backend cap |
| T0903 | immutable identity、path safety、cascade ordering 与 irreversible delete |
| Ant Design | Table、Modal、Popconfirm、Skeleton、Alert、Tag、Select |

### 明确不做

- 不下载或忠实渲染 original PDF/DOCX/XLSX；
- 不重新运行 Parser、OCR、Embedding 或 LLM；
- 不实现 file rename、batch delete、move/copy、undo/trash；
- 不把 Frontend local removal 描述成 distributed transaction proof；
- 不在 T1104 内完成 cross-component state work；该职责由 T1105/F-1 remediation 收口；
- 不以 Task Learning Pass 代替 Phase Gate、Learning Review 或 Engineering Review。

---

## 46. 四类状态：resource、read model、preview 与 mutation overlay

FileManager 没有把所有状态压进一个巨大 union，而是分成多个正交层：

```text
CollectionState = loading | ready | empty | error
FileState       = idle | loading | success | empty | error
PreviewState    = idle | loading | success | error

Mutation overlays:
  deletingFileId: string | null
  actionError: {message, retry} | null
  notice: string
```

为什么这种拆分合理？collection list failure、file list failure、preview failure 与 delete failure 的恢复动作不同：

- collection error → 重新加载 collections；
- file-list error → 针对 selected collection 重试 list；
- preview error → 针对 modal target 重试 preview；
- delete error → 重发对应 destructive command；
- delete success → notice，但 table 仍可继续操作。

如果只用 `status='error'`，UI 将不知道应重试哪条 command，也无法同时保留 table 与 action-level error。

`idle` 只在还没有合法 collection target 时使用；合法 target 产生后，file read model 才进入 loading/success/empty/error。这里 collection 是 parent resource，files 是 child read model。

---

## 47. Collection → File list：两级资源加载与 stale response guard

初次 mount 或 shared collection 变化：

```text
Home shared collection source
  → resolveCollectionSelection(current, collections, mutation, handledRevision)
  → preserve current / migrate rename / fallback first
  → selectedCollectionRef = resolved owner
  → close old preview and clear owner-scoped feedback
  → if owner exists: loadFileList(owner)
```

FileManager 与 Upload/QAPanel 共用同一个 selection resolver。合法 current 会保留；selected collection 被重命名时迁移到 `newName`；被删除时回退到第一项。File list、preview 与 action feedback 仍是 owner-scoped local state，不会因为 collection list 提升而变成全局状态。[PROJECT FACT]

`loadFileList(collectionName)` 为每个 request 分配递增 version：

```ts
const requestVersion = fileRequestVersionRef.current + 1;
fileRequestVersionRef.current = requestVersion;
```

response/error commit 前比较 current version。若用户快速从 KB-A 切到 KB-B，A 的旧 response 不能覆盖 B 的 table。它与 QAPanel 的 generation token 是同一类 last-intent-wins pattern：防 stale commit，不取消 Backend request。

加载新 list 时同时清除 `actionError` 与 `notice`，避免旧 collection 的 mutation feedback 漂移到新 owner。`handleCollectionChange()` 也先 `closePreview()`，因此 preview target/result 不会跨 collection 保留。

---

## 48. FileRecord：展示字段与 immutable identity

`FileRecord` 包含：

```ts
{
  file_id,
  file_name,
  size,
  upload_time,
  chunk_count,
  status
}
```

身份规则贯穿整个 component：

- `<Table rowKey="file_id">`：React row reconciliation identity；
- preview：`previewFile(file.file_id, selectedCollection)`；
- delete：`deleteFile(file.file_id, collectionName)`；
- local removal：按 `item.file_id !== file.file_id`；
- open preview cleanup：比较 `previewTarget.file_id`。

`file_name` 只用于用户显示、extension badge 与 delete success copy。它可能重复、可能未来被重命名，也不能安全地被 client 拼成 filesystem path。Backend 必须从可信 persisted metadata 通过 `file_id` 找出 filename，再执行 path containment checks。

这类似数据库管理 UI：前端显示 `display_name`，所有 mutation route 与 row identity 使用不可变 primary key。把 filename 放进 delete URL 会混淆 display metadata、identity 与 path input 三个层次。

---

## 49. Table formatting：presentation conversion 不改变 domain truth

### 49.1 File size

`formatFileSize()` 使用 1024-based units：

```text
0         → 0 B
1023      → 1023 B
1024      → 1.00 KB
10240     → 10.0 KB
1048576   → 1.00 MB
52428800  → 50.0 MB
```

小于 10 的 unit value 保留两位，否则保留一位。这只是 presentation rounding；Backend `size` 的整数 bytes 才是 contract truth。T1104 的有效 upload 文件最大 50 MiB，因此当前 units 覆盖实际范围；helper 虽能继续显示 GB，却不需要在 v1 支持 TB。

### 49.2 Upload time

`formatUploadTime()` 先 `new Date(value)`，invalid date 原样返回；valid date 使用浏览器 `Intl.DateTimeFormat('zh-CN')`。因此最终时区解释受 ISO string 是否含 offset 以及浏览器 timezone 影响。UI 显示值不是新的 persisted timestamp；若 Backend 发送 naive datetime，跨时区部署需要明确 contract。

### 49.3 Status

`SUCCESS` 显示绿色“已入库”，`SUCCESS_WITH_WARNINGS` 显示 warning tag“已入库 · 有警告”。后者仍是 durable ingestion outcome，不应当成 failed file；FileManager 也没有重跑 OCR 或提供 retry ingestion。

extension badge 来自最后一个 `.` 后的 suffix 并 upper-case。它是视觉提示，不是 MIME detection 或 security validation；真正 supported-format enforcement 已发生在 upload/backend boundary。

---

## 50. Preview：查看已入库文本，不是打开原文件

preview request 由二元身份定位：

```text
GET /api/files/{file_id}/preview?collection_name={collection}
```

Backend 语义为：

```text
get_chunks_by_file(collection_name, file_id)
  → sort chunk_index ASC
  → join content with "\n\n"
  → total_chars = full joined length
  → content = first MAX_PREVIEW_CHARS
  → preview_chars = returned content length
```

因此 modal 标题中的“已入库内容预览”和 meta 中的 `PERSISTED CHUNK CONTENT` 非常重要。它告诉读者：

- 内容已经经过 parsing/OCR、cleaning、chunking；
- chunk overlap 可能让相邻文本重复；
- 表格、图片、版式、分页等 original fidelity 可能不存在；
- preview 不重新读取 raw file，也不重新运行 expensive pipeline；
- `total_chars` 是 chunk-concatenated length，不是 original file characters。

Frontend 不硬编码 5000，而用 `preview_chars < total_chars` 决定是否显示 truncation alert。这让 UI 依赖 response semantics，而不是复制 Backend configurable cap。`preview_chars / total_chars` 是字符计数，不是 bytes、tokens 或 chunks。

内容使用 `<pre>{previewResult.content}</pre>`。React 将文本 escape，不会把 persisted content 当成 HTML 执行；同时保留 whitespace 便于诊断。它不是 Markdown renderer，也不应把文档中的指令当成 application commands。

---

## 51. Preview async isolation：close 也必须使 request 失效

`loadPreview()` 使用独立 `previewRequestVersionRef`，与 file-list version 分开：

```text
click file A preview → version 1 → loading A
click/close/switch   → increment current version
A response arrives  → mismatch → ignored
```

`closePreview()` 不只清 modal state，还递增 version。这解决了一个常见 React race：如果只关闭 Modal，旧 Promise 稍后 success，仍可能重新写入 `previewResult`。当前 guard 让 closed/stale result 无法 commit。

它依然不是 HTTP cancellation；Backend 已经开始的 preview read 会完成。由于 preview 是 read-only 且不运行 parser/OCR/LLM，浪费成本相对有限。若未来 preview 变成 large streaming operation，再考虑 AbortController。

删除当前正在 preview 的 file 后，success path 调用 `closePreview()`；这同时清除已经显示的 stale diagnostic content，并使仍在 flight 的 preview request 失效。

---

## 52. Delete：确认框只是 human guard，Backend 才执行安全级联

Popconfirm 明确展示：

> 将级联删除原文件、所有切片、向量与元数据，并使关键词索引失效。此操作无法恢复。

这是 destructive UX 的必要组成，但不是 authorization、transaction 或 path-safety enforcement。真实命令为：

```text
DELETE /api/files/{file_id}?collection_name={collection}
```

当前 Backend 顺序是：

```text
1. collection existence preflight
2. get_files() 并按 immutable file_id 找 record
3. 从 trusted record 取 file_name
4. resolve + containment checks 后 raw unlink(missing_ok=True)
5. Chroma delete_by_file(collection, file_id)
6. keyword-index invalidation seam
7. return FileDeleteResponse
```

path safety 不能由 Frontend 保证。Backend 使用 `PureWindowsPath(file_name).name == file_name`、resolved parent equality 与 collection-root containment，防止 display filename 逃逸目标目录。`missing_ok=True` 允许 raw file 已缺失时仍继续清理 persisted chunks。

`delete_by_file()` 以 `where={"file_id": file_id}` 删除该文件的 chunks、vectors 与 metadata。keyword invalidation 让下次 keyword search rebuild；当前 seam 在普通 invalidation failure 时尝试 `mark_dirty()` 并记录日志，但极端 fallback failure 仍不是 distributed transaction。

不可逆意味着：确认后没有 undo/trash，response success 前也不能假设能恢复。对 UI 而言必须把 confirm 放在 request 前；对 Backend 而言必须在任何副作用前完成 collection/file preflight。

---

## 53. Delete success 后的 local projection 与 partial-failure boundary

Frontend 不是 optimistic delete：它等待 `deleteFile()` 成功后才移除 row。success 后：

```text
filter local files by file_id
→ onFileDeleted(collectionName)
→ Home decrements shared collection.file_count, floor at 0
→ success or empty state
→ show response-derived notice
→ close matching preview
```

这是一份 server-acknowledged local projection，不是 authoritative refetch。优点是快，缺点是 view 可能与 Backend 漂移：其他 client 同时操作、response 丢失、局部后端失败或并发 local mutations 都可能使表格过时。

Backend cascade 本身也没有跨 filesystem/Chroma transaction：

- raw unlink 成功、Chroma delete 失败 → raw file 已不可恢复，但 chunks 可能仍存在；
- Chroma delete 成功、keyword dirty fallback 也失败 → durable vector truth 已变，但 in-memory keyword view 可能 stale；
- client 在 server commit 后断网 → Frontend 显示 error，retry 可能得到 `FILE_NOT_FOUND`，但第一次 delete 实际已完成。

因此 error 不等于“没有副作用”，retry 也不等于天然 idempotent success。当前 API 对第二次 delete 返回 `FILE_NOT_FOUND`，Frontend 作为 error 展示；更强 reconciliation 可在 failure 后 refetch list，但这属于工程改进，不在 Learning Pass 修改范围。

---

## 54. 并发删除 race：单个 deletingFileId 不是 mutation set

当前每次 render 只记录一个 `deletingFileId`，只 disable 对应 row。其他 row 仍可发 delete，因此两个 request 可以并发：

```text
initial files = [A, B, C]

delete A captures [A, B, C]
delete B captures [A, B, C]

A success → setFiles([B, C])
B success → setFiles([A, C])   // A 在 local UI 中被“复活”
```

原因是 `handleDelete()` success 使用 render closure 中的 `files.filter(...)`，而不是 functional update。`finally { setDeletingFileId(null) }` 也可能在另一个 delete 仍进行时提前清除全局 deleting indicator。

这不代表 Backend resurrection；两个 server deletes 都可能已经成功。它证明 Frontend local read model 在 concurrent mutations 下可能 stale。常见修复方向有：

1. 全表 mutation mutex：delete 期间 disable 所有 destructive actions；
2. `Set<file_id>` 表示 per-row pending，并使用 `setFiles(current => current.filter(...))`；
3. 每次 success 后 authoritative `loadFileList(collectionName)`；
4. mutation library 的 cache invalidation/serialization。

选择哪种需要结合 UX 与 T1105 cross-component strategy。T1104 Learning Pass 只记录当前 race，不越权改代码。

---

## 55. Error ownership 与 retry closure

错误被分成三层：

| Error owner | Stored data | Retry target |
|---|---|---|
| collection | `collectionError` | Home `onRetryCollections()` |
| file list | `fileError` | `loadFileList(selectedCollection)` |
| preview | `previewError + previewTarget` | `loadPreview(previewTarget)` |
| delete action | `ActionError {message,retry}` | closure 中的 `handleDelete(file)` |

`ActionError.retry` 保存具体 file record，类似 Node command object 中捕获重试参数。它让 error banner 即使不在 row 内也知道重试哪个 delete。代价是 closure 捕获旧 record/state；collection switch 会在新 list load 开始时清除 action error，且 delete commit 前检查 `selectedCollectionRef`，降低跨 owner 重试风险。

`selectedCollectionRef` 解决 delete async callback 读取 stale state 的问题：delete A-KB 期间切到 B-KB，A response 不会修改 B 的 files/count/notice。它不取消 A 的真实删除；A 的 Backend side effect 仍可能完成。

`FILE_NOT_FOUND` 提示重新加载 list，反映 stale read model；`COLLECTION_NOT_FOUND` 要求刷新 knowledge-base list；`NETWORK_ERROR` 提示检查 service。未知 `ApiError.code` fallback 到 Backend message，保持 forward compatibility，但没有 exhaustive UI recovery taxonomy。

---

## 56. T1104 完整 data flow

```text
Mount FileManager
  → consume Home shared collections
  → preserve / rename-migrate / fallback selection
  → GET /api/files?collection_name=...
  → FileRecord[]
  → Table(rowKey=file_id)

Preview
  → click row preview
  → GET /api/files/{file_id}/preview?collection_name=...
  → Backend reconstructs persisted chunks
  → version guard
  → <pre> content + preview_chars/total_chars
  → conditional truncation warning

Delete
  → Popconfirm irreversible warning
  → DELETE /api/files/{file_id}?collection_name=...
  → Backend preflight
  → safe raw unlink
  → Chroma delete_by_file
  → keyword invalidation/dirty fallback
  → response
  → collection-owner guard
  → local row/count projection + notice
```

Trust boundaries：

- Frontend 决定 presentation、confirmation 与 local state；
- API route 验证 collection/file existence；
- Backend 从 persisted record 取得 filename 并负责 path safety；
- Chroma/persisted chunks 是 v1 file metadata source of truth；
- Backend success JSON 当前只有 compile-time TypeScript type，没有 runtime schema parser；malformed numeric/date fields 仍可能导致展示异常。

---

## 57. T1104 Verification 与证据账本

### 本轮执行证据

```text
npm.cmd run build
→ PASS: compiled successfully
→ PASS: lint/type validity
→ PASS: 4/4 static pages generated
→ / route 261 kB; First Load JS 383 kB (observation only)

formatFileSize isolated runtime probes
→ 0 B: PASS
→ 1023 B: PASS
→ 1 KiB: PASS
→ 10 KiB: PASS
→ 1 MiB: PASS
→ 50 MiB: PASS
→ 6/6 PASS

Static contract inspection
→ FileManager mounted in files shell slot
→ row/preview/delete identity uses file_id
→ list and preview version guards present
→ preview truncation predicate present
→ irreversible cascade copy present
→ all resource/action state branches present
```

formatter probe 通过临时脚本从当前 TSX 提取并 transpile 实际 helper；脚本完成后已删除。最初一次 PowerShell inline harness 因 quoting 失败，未执行产品逻辑，不计为 product failure，也不计入 6/6 evidence。

### Evidence ledger

| Evidence | Label | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| production build | `BUILD / REAL` | FileManager/types/CSS compile；static generation | browser events、HTTP 或 Backend side effects |
| formatter 6/6 | `RUNTIME / ISOLATED` | actual helper 的 bytes→display boundary | table/browser locale rendering |
| FileManager close read | `STATIC` | state、identity、guard、truncation、delete control flow 存在 | event sequence 在真实 browser 中必然正确 |
| Backend T0901–T0903 prior route tests | `MOCKED / PRIOR` | route orchestration 与 no-side-effect preflight | real filesystem + Chroma + keyword three-store E2E |
| list/empty/error UI | `NOT_AVAILABLE` | — | real Backend read 与 browser outcome |
| preview/truncation UI | `NOT_AVAILABLE` | — | real persisted chunks reconstruction 与 modal outcome |
| delete/notice/retry UI | `NOT_AVAILABLE` | — | confirmation、真实 cascade 与 reconciliation |
| concurrent delete | `STATIC RISK` | closure/state model 允许 race | race 的具体 browser reproduction frequency |
| repository-owned frontend tests | `NOT_AVAILABLE` | — | repeatable component/E2E regression suite |

本轮没有删除任何用户文件，也没有创建 test collection/file。真实 upload → list → preview → delete → re-query、path-safety 与 three-store cleanup 仍没有本轮 E2E evidence。既有 Backend route tests 使用 patched seams，只能作为 `MOCKED / PRIOR` 背景，不能升级成 T1104 real browser evidence。

Bundle 从 T1103 的 194 kB / 315 kB 增至 261 kB / 383 kB，与 FileManager/Table/Modal code 加入同一时间点，但没有 bundle analyzer、dependency attribution 或 performance budget；只能记录为 time-specific observation，不能单独宣判 regression。

---

## 58. T1104 Engineering Questions（短摘要）

1. 为什么 delete/preview 必须用 `file_id`？——filename 是可变 display metadata，也不应成为 path input。
2. preview 为什么不是 original file viewer？——它从 persisted chunks 重建，反映 ingestion truth。
3. `preview_chars < total_chars` 为什么优于写死 5000？——依赖 response semantics，避免复制 Backend config。
4. close modal 为什么递增 preview version？——阻止已关闭 request 的 late response commit。
5. Popconfirm 能保证 path safety 吗？——不能；它只提供 human guard，Backend 负责 containment。
6. delete success 后 filter row 是 optimistic 吗？——不是，先等 server success；但仍是 local projection。
7. error 是否意味着 delete 没发生？——不一定，response 丢失或 cascade partial failure 都可能已有副作用。
8. `missing_ok=True` 的意义是什么？——raw file 缺失时仍可继续清理 persisted chunks。
9. 为什么并发 delete 可能“复活”row？——多个 closure 基于同一旧 `files` 计算 replacement state。
10. build PASS 为什么不是 FileManager flow PASS？——build 不执行 modal、confirm、HTTP 与跨存储副作用。

---

## 59. T1104 Interview Candidates（Task-level only）

- **30 秒主线**：我把 FileManager 分成 parent collection、file read model、preview inspector 与 destructive mutation 四个边界；所有资源操作使用 immutable `file_id`，preview 明确展示 persisted chunk reconstruction，delete 用 confirm 和 owner/version guards 管理 UI，但 Backend 才负责 path safety 与级联。
- **高价值追问**：为什么 preview 不能叫原文？为什么 delete error 不保证零副作用？为什么 `file_id` 同时适合 React key 与 API identity？
- **并发追问**：单个 `deletingFileId` 配合 captured `files` 会怎样？两个并发 success 可能使 local row resurrection；可用 functional update、pending set、mutex 或 refetch 处理。
- **TypeScript/Node 类比**：Table 是 read model；preview 是 diagnostic projection；delete 是 destructive command；`ActionError.retry` 是携带参数的 retry command。
- **诚实证据**：build 与 formatter probes 已通过；真实 browser list/preview/delete 和 three-store cleanup 本轮未执行。

本 Task 没有生产 incident，不构造 STAR；Phase 11 Gate 前不晋升项目级 Interview Guide。

---

## 60. T1104 自测题与答案

### Questions

1. FileManager 展示的 FileRecord 从哪里来？
2. 为什么 `file_name` 不能用作 delete identity？
3. `file_id` 在 component 中承担哪四处 identity？
4. preview content 与 original document 有什么区别？
5. `total_chars` 统计的是什么？
6. 为什么可能出现 chunk overlap 重复？
7. truncation notice 的判断条件是什么？
8. preview modal close 后，旧 response 为什么不会写回？
9. request version guard 是否取消 Backend 工作？
10. delete 的真实 side-effect 顺序是什么？
11. Frontend Popconfirm 能保证哪些事，不能保证哪些事？
12. raw file 已缺失时为什么仍允许继续 delete？
13. delete success 后 UI 做了哪些 local projection？
14. delete request 报 network error 是否证明文件仍存在？
15. 两个并发 delete 如何导致 row resurrection？
16. `selectedCollectionRef` 解决什么 stale ownership 问题？
17. `SUCCESS_WITH_WARNINGS` 为什么仍显示为已入库？
18. formatter 的 rounding 是否改变 Backend byte truth？
19. 为什么 `<pre>` 比 Markdown renderer 更符合 preview 语义？
20. 如何测试 FileManager 而不真的删除生产文件？证据应如何标注？

### Answer keys

1. Backend 从同一 `file_id` 的 persisted chunk metadata group/deduplicate 得到，不来自独立 SQL file table。
2. 它是可变/可重复 display metadata；还会把 API identity 与 filesystem path input 混在一起。
3. Table row key、preview route、delete route、local filter/preview cleanup comparison。
4. preview 是 parsed/OCR/cleaned/chunked persisted text reconstruction，不保证 layout/media/original fidelity。
5. 所有 persisted chunk contents 按顺序用双换行拼接后的截断前字符数。
6. chunking 为保持上下文会复制相邻边界文本，reconstruction 不去 overlap。
7. `preview_chars < total_chars`。
8. close 增加 `previewRequestVersionRef`；late result version mismatch 后 return。
9. 不取消，只阻止 stale Frontend commit。
10. preflight → persisted record lookup → safe raw unlink → Chroma delete_by_file → keyword invalidation → response。
11. 能让用户看到不可逆风险并要求确认；不能保证 authorization、path containment、transaction 或 compensation。
12. `missing_ok=True` 让清理可继续收敛，不因 raw artifact 已缺失而保留 vectors/metadata。
13. remove row、decrement local count、切 success/empty、显示 notice、关闭同 file preview。
14. 不能；server 可能已 commit，只有 response 丢失，或级联已经部分执行。
15. 两个 handler 捕获同一旧 files，各自 replacement 只移除自己的 ID，后写入者可能恢复另一行。
16. 用户切换 KB 后，旧 delete completion 不能修改新 KB 的 table/count/notice。
17. 它表示 durable ingestion with partial page warnings，不是 failed ingestion。
18. 不改变；format string 只是 presentation，integer bytes 仍是 truth。
19. preview 是诊断性文本；`pre` 保留 whitespace 且不会引入 Markdown interpretation。
20. mock API client 做 component tests 并使用 disposable fixtures；mocked test 标 `MOCKED`，真实隔离环境的跨存储流程才可标 real E2E。

---

## 61. T1104 Learning Pass 收口边界

T1104 Learning Pass 完成。当前准确表述是：**FileManager 已实现 knowledge-base selection、typed file table、immutable `file_id` identity、size/time/status formatting、persisted-chunk preview、response-driven truncation notice、irreversible cascade confirmation、delete success local projection，以及 file-list/preview/collection ownership guards；production build、formatter 6/6 probes 与 static contract inspection 已验证。真实 browser list/preview/delete、three-store cleanup、path-safety、partial-failure reconciliation、concurrent-delete reproduction 与 repository-owned frontend regression tests 仍为 `NOT_AVAILABLE / DEFERRED`。**

本次只更新 Technical Learning、README 与 Project Map；不修改 `FileManager.tsx`、`api-client.ts`、`types.ts`、`page.tsx`、CSS、SPEC 或 TASKS，不启动 T1105，不执行 Phase 11 Gate/Learning Review/Engineering Review，不 commit/push。

---

## 62. T1105 学习：Cross-component consistency 是 ownership policy，不是相同代码

T1105 不是再增加一个业务组件，而是回答三个横切问题：

1. 菜单切换时，组件 state 应保留还是销毁？
2. knowledge-base ownership 改变时，哪些 state 必须清空？
3. expected API failure 与 unexpected React failure 分别由谁恢复？

核心不是让四个组件拥有完全相同的 union type，而是让相同类别的状态遵守一致 policy：resource fetch 有 loading/success-or-ready/empty/error；expected failure 在 feature 内显示并提供相关 retry；conversation state 不能跨 KB；unexpected render failure 交给 route error boundary。

TypeScript/Node 类比：这像多个 controller 共享同一套 lifecycle convention，但各自拥有不同 domain state。统一的是 protocol，不是把所有 controller 塞进一个 global singleton。

---

## 63. T1105 目标、依赖与明确不做什么

### 目标

- 菜单切换不刷新页面，并保留各 feature 的 local state；
- QAPanel 内切换 KB 时清空 history、draft、pending question 与 query error；
- stale KB request 不得提交到新 KB conversation；
- 四个 data-fetching components 都覆盖 loading、usable/success、empty、error；
- loading 使用 Skeleton/Spin，expected error 使用 Alert + contextual retry，empty state 提供下一步 guidance；
- `app/error.tsx` 为 unexpected route render error 提供 fallback 与 `reset()`；
- 检查 normal navigation 的 React key warning/console error。

### 依赖

| Dependency | T1105 使用方式 |
|---|---|
| T1101 | collection CRUD resource/action state |
| T1102 | collection + upload transaction state |
| T1103 / F014 | KB-bound conversation lifecycle 与 stale response guard |
| T1104 | parent/list/preview/delete 分层 state 与 ownership refs |
| T1001 | normalized `ApiError` transport boundary |
| Next.js App Router | route-segment `error.tsx` 与 `reset()` |

### 明确不做

- 不引入 Redux、Zustand 或新的 global state layer；
- 不实现 server-side session、persistent conversation 或 component cache library；
- Task Learning Pass 当时只记录 cache/race/observability trade-offs；后续 F-1 remediation 才获得实现授权；
- 不把 Phase Tasks 全部 DONE 自动升级成 Phase Gate PASS；PASS 来自后续独立 Gate re-review；
- 不启动 Phase 12 integration/acceptance work。

---

## 64. 菜单切换：从 conditional mount 改为 persistent panels

当前 `page.tsx` 始终渲染四个 feature：

```tsx
<div className="feature-panel" hidden={selectedKey !== 'qa'}>
  <QAPanel />
</div>
```

CSS 明确保证：

```css
.feature-panel[hidden] {
  display: none;
}
```

这与早期的 conditional rendering 有根本区别：

```text
旧模式：selectedKey === 'qa' ? <QAPanel /> : ...
        switch away → unmount → local state destroyed

当前：  four children always mounted + one wrapper visible
        switch away → hidden → local state retained
```

`selectedKey` 只控制 presentation visibility，不再控制 component lifetime。因此 QA draft/history、upload result、FileManager preview-related state、KB modal/form state 理论上都留在各自 component instance 中；浏览器实测确认 QA composer draft 在 QA → Files → QA 后仍保留。

native `hidden` 让非当前 panel 不参与布局，并从正常 accessibility presentation 中隐藏；运行时 DOM 检查确认四个 `.feature-panel` 同时存在，恰有一个没有 `hidden`。

这里的“preserve”是 browser-memory preservation，不是 persistence：refresh、route replacement 或真正 unmount 仍会清空 local React state。

---

## 65. Persistent mount 的代价：首屏工作与后台 effects

隐藏不等于未挂载。四个 component 的 local effect 仍会在首屏运行；F-1 remediation 后，collection read 已集中到 Home，因此只有一条 `listCollections()` 调用路径。FileManager 在 resolved collection 存在时仍会加载该 owner 的 file list。

```text
Home mount
  ├── Home                 → GET collections (shared once per effect execution)
  ├── KnowledgeBaseManager → no collection GET; derive view from shared props
  ├── FileUpload           → reconcile local selection from shared props
  ├── QAPanel              → reconcile owner; reset conversation if owner changes
  └── FileManager          → reconcile owner → GET files
```

Gate focused browser trace 观察到一次 shared collection GET；代码搜索也确认只有 `page.tsx` 调用 `listCollections()`。[MOCKED BROWSER + STATIC] React development Strict Mode 仍可能重复执行 effect，确切 request 数量取决于运行配置，不能把一次观察当作框架级 guarantee。

代价包括：

- 首屏即加载用户还没打开的 feature data；
- hidden feature 仍会做 selection reconciliation、scroll effect 或 child-resource read；
- hidden component 的 polling/subscription 若未来加入，也会继续运行；
- bundle 与 mounted tree 同时包含四个重组件。

可选方案仍包括 lazy-first-mount + keep-alive、query cache 或 URL route-per-feature；但每种方案会改变 complexity、state semantics 与 deep-link behavior。当前 v1 选择 persistent panels + page-level shared collection source，不引入第三方 server-state library。

---

## 66. State preservation 不等于 cross-component freshness

本节保留的是一次真实 Gate 闭环，而不是当前缺陷描述。

### Gate 发现：preserve 了 component，却没有同步 read model

Task Learning Pass 时，四个 feature 各自持有 collections cache 并在 mount 时 GET。persistent panels 让 local state 得以保留，也让隐藏组件不再通过 remount 获得偶然 refresh：

```text
KB Manager creates/renames/deletes KB
  → only KnowledgeBaseManager local collections update
  → hidden Upload / QA / Files caches do not automatically refresh
```

Gate 将此裁定为 F-1：跨组件 stale collection selection 会使后续请求指向已重命名/删除的 owner。关键学习是：**state preservation 与 server-resource freshness 是两个独立维度**。

### Remediation：共享资源上移，局部事务下沉

当前实现采用最小提升，而不是全局 store：

1. Home 持有 `collections/collectionState/collectionError`，成为单一 frontend collection projection owner；
2. KnowledgeBaseManager 在 server-confirmed CRUD success 后调用 parent callback；
3. Home 用 functional updates 处理 create/rename，并发布递增 `CollectionMutation.revision`；
4. `resolveCollectionSelection()` 在 children 内统一 preserve、rename migration 与 delete fallback；
5. QAPanel owner 改变时清 conversation 并递增 request generation；FileManager 同步关闭旧 preview、使旧 reads 失效。

### Focused re-review：F-1 CLOSED

Gate re-review 在真实 production Next UI + isolated in-memory MOCKED API 上验证：只有一次 collection GET；create 对 manager/upload/QA/files 同步可见；rename `kb-a → kb-b` 后旧名消失、选择与后续 request 使用 `kb-b`；delete selected collection 后各 consumer fallback，QA history 清空；手动 KB switch 同样清 history；menu switch 仍保留 QA draft；console warning/error 为 0。[MOCKED BROWSER]

当前仍有一条被接受的 v1 边界：Home 的 delete projection 基于 callback closure 中的 `collections` 计算 remaining；并行删除在极端时序下可能产生 local lost update。Gate 将其记录为 F-3 MINOR `ACCEPTED_V1_BOUNDARY`，不是 F-1 未关闭。[PROJECT FACT]

---

## 67. 两种切换必须区分：menu switch 与 KB switch

### Menu switch

改变的是当前可见 feature：

```text
selectedKey: qa → files → qa
QAPanel instance: same
QA draft/history: retained
```

### KB switch inside QAPanel

改变的是 conversation owner：

```ts
requestVersionRef.current += 1;
setSelectedCollection(value);
resetConversation();
```

`resetConversation()` 清除：

- `history`；
- composer `question`；
- `pendingQuestion`；
- `queryState` → idle；
- `queryError`。

这两个 policy 并不矛盾：菜单只是 view navigation，不改变 QA conversation identity；KB 则是 domain boundary，旧 history 不得进入新 KB request。

真实 browser smoke 使用两个 disposable empty KB 验证：Ctrl+Enter 发问后得到真实 409 `COLLECTION_EMPTY` 与 pending/error UI；切换到另一 KB 后 pending question 和 warning 消失，history meter 保持 0，重新出现 idle guidance。[REAL BROWSER + REAL BACKEND]

---

## 68. `requestVersionRef` 补足了“清 state”无法解决的 race

只调用 `setHistory([])` 不够。假设：

```text
KB-A request starts
→ user switches to KB-B
→ visible history clears
→ KB-A response arrives later
```

若没有 version guard，旧 response 仍会把 A 的 answer/sources 追加到 B 的空 history。QAPanel 为每次 request 分配 generation，KB switch 先递增 current generation；settle 时 mismatch 就丢弃。

```ts
if (requestVersion !== requestVersionRef.current) return;
```

这建立的是 commit ownership，不是 network cancellation：A 的 Backend retrieval/LLM 仍可能完成，只是 UI 不接纳结果。若希望节省 provider cost，还需 AbortController 与 Backend cancellation semantics；v1 没有这个 contract。

FileManager 对 list/preview 使用同类 version guard，对 delete 使用 `selectedCollectionRef` ownership check。FileUpload 在 collection switch 时清 outcome/retry file，但没有 in-flight request version 或 abort；其 Select 在 uploading 时 disabled，因此正常 UI 降低了 switch race。KnowledgeBaseManager 没有跨 collection selection，也就没有同类 owner switch。

---

## 69. 四个组件的 state protocol 对照

| Component | Resource/data state | Loading UI | Empty guidance | Expected error + recovery |
|---|---|---|---|---|
| KnowledgeBaseManager | `ViewState: loading/success/empty/error` | card Skeleton | 创建第一个知识库 CTA | list retry；create/rename modal error；delete action retry |
| FileUpload | collection 4-state + upload 5-state | selector Skeleton + upload progress | 先创建 KB | collection reload；validation correction；request retry file |
| QAPanel | collection 4-state + query 5-state | selector Skeleton + answer Spin | create/upload guidance | collection reload；query retry；empty-KB warning |
| FileManager | collection + file + preview states + action overlays | selector/table/modal Skeleton | create/upload guidance | owner-specific list/preview/delete retry |

命名并非完全一致：有的使用 `ready`，有的使用 `success`，FileManager 还有 `idle`。一致性应看语义：

- `loading`：尚不能使用目标数据；
- `ready/success`：存在可操作 read model；
- `empty`：request 成功但集合为空；
- `error`：request 未得到可用结果；
- transaction-specific states：uploading、warning、empty_kb、preview 等不能被强行压平。

这体现 discriminated state 的价值：empty 不是 error，partial ingestion warning 不是 error，empty KB query 也不是 generic network failure。

---

## 70. 三层错误边界：transport、feature、route

```text
API client
  → normalize HTTP/network/invalid JSON into ApiError

Feature component
  → catch expected async failure
  → map code/message to user-facing Alert
  → preserve retry inputs where appropriate

app/error.tsx
  → catch unexpected route-segment render failure
  → show Result + reset()
```

### Transport layer

`api-client.ts` 统一 `status/code/message/details`，避免每个 component 重复解析 response envelope。它对所有 non-2xx 和 network/invalid JSON 使用 `console.error()`。

### Feature layer

异步 handlers 都用 try/catch 把 expected failure 转为 local state。retry 与 owner绑定，而不是盲目 reload entire page。每个 component 仍拥有自己的 `ERROR_MESSAGES/getErrorMessage`，能写 feature-specific recovery copy，但带来 mapping duplication 与 drift 可能。

### Route error boundary

`app/error.tsx` 是 Client Component，使用 Ant `Result` 展示 unexpected error fallback，并调用 Next 注入的 `reset()` 尝试重新渲染 route segment。它适合 render/lifecycle tree 中未被 feature 捕获的异常。

它不是万能 catch：

- 不替代 event handler / async Promise 的显式 try/catch；
- 不保证捕获同 segment 的 root layout 本身错误；全局 layout fallback 需要独立 `global-error.tsx` strategy；
- `reset()` 不是 browser hard reload，也不回滚已经发生的 Backend mutation；
- 当前忽略传入的 `error/digest`，没有 telemetry/reporting；
- 本轮没有故意注入 crash，因此只有 build/static evidence，没有 runtime catch proof。

---

## 71. “No console errors”必须定义 observation window

T1105 acceptance 写明 normal operation 不应出现 console errors。证据必须说明做了什么：

- fresh page load + normal menu navigation：初始 console error/warning 列表为空；连续打开 Upload、Files、KB、QA 没有新增 warning/error；
- React list identities 静态使用 collection name、message ID、chunk ID、file ID 或 warning composite key；browser navigation 中未观察到 key warning；
- 主动向 empty KB 发 query 后，UI 正确处理 409，但 centralized client 仍记录一条 `console.error("DX-RAG API request failed", ...)`。

第三点不应混入“normal success navigation”结论，也不能隐藏。`COLLECTION_EMPTY` 是 expected domain rejection：用户体验上已处理，console policy上却仍被记为 error。若团队要求“所有已处理 domain errors 不污染 console”，需要让 logger 区分 expected 4xx、unexpected 5xx/network；当前实现尚未做该 taxonomy。

反过来，console clean 也不能证明没有 UI bug、race、stale cache 或 accessibility issue。它只是特定操作窗口中没有捕获到 warning/error。

---

## 72. 常驻组件与 overlay/DOM 的边界

`hidden` wrapper 能隐藏普通 descendant layout/accessibility content，但 UI library 的 Modal、Select popup 等可能通过 portal 渲染到 `document.body`。这意味着“component hidden”与“该 component 创建的所有 overlay 一定自动隐藏”不是普遍等价关系。

本轮探索中，KB create Modal 打开时第一次点击侧边菜单被 modal/mask 消费并关闭 dialog，visible panel 没有切换；再次导航才会切换。这符合 modal interaction 的阻塞性质，但说明 overlay lifecycle 需要单独测试，不能仅凭 wrapper `hidden` 推断。

其他相关边界：

- hidden panel 仍可完成 async request 并更新 local state；
- screen reader visibility 由 native hidden 与 portal behavior 共同决定；
- focus 若在 panel 切换前位于内部 control，切换后的 focus management 需要 browser/a11y test；
- T1105 smoke 验证基本导航，不是完整 keyboard/focus/portal audit。

---

## 73. Cross-component data flow 与 ownership map

```text
                       Home
 selectedKey + shared collection source
 collections/state/error + mutation revision
 CRUD projection callbacks + collection retry
                       │ props down / events up
       ┌───────────────┼───────────────┬───────────────┐
       │               │               │               │
 KB Manager         Upload            QA             Files
 CRUD form/action    selected KB       selected KB     selected KB
 state               upload state      conversation    file/preview/delete
       │               │               │               │
       └───────────────┴──── centralized api-client ───┘
                               │
                            Backend
                     durable source of truth
```

当前 shared state 有意保持很窄：Home 只拥有所有 feature 都依赖的 collection projection，没有把 upload file、QA history、file list 或 preview 提升。各 feature 仍拥有自己的 selected KB，因为不同工作区不要求同步用户选择；它们只共享“哪些 owner 合法”以及 identity mutation 事件。

几个 ownership invariant：

- menu selection belongs to Home；
- collection projection and mutation revision belong to Home；
- each feature selection belongs to that feature, but must resolve against the shared projection；
- QA history belongs to exactly one selected KB；
- retry input belongs to the operation/owner that created it；
- file/collection durable truth belongs to Backend；
- Backend is durable truth；Home collections 与 FileManager files 都是可失效的 client projections；
- API errors are normalized centrally, recovery copy/state belongs to feature；
- unexpected render fallback belongs to route boundary。

---

## 74. Phase 11 Verification 与证据账本

### 本轮执行证据

```text
npm.cmd run build
→ PASS: compiled successfully
→ PASS: lint/type validity
→ PASS: 4/4 static pages generated
→ / route 245 kB; First Load JS 385 kB (Gate observation only)

Task Learning Pass: real browser + local Next.js + real FastAPI
→ four menu targets visible and switch without page navigation
→ four .feature-panel nodes remain mounted; exactly one visible
→ QA draft survives QA → Files → QA
→ Ctrl+Enter to real empty KB returns 409 and renders empty-KB guidance
→ switching KB clears pending/error and restores idle state
→ normal four-panel navigation adds 0 console warnings/errors
→ expected 409 path emits 1 centralized API-client console.error
→ two disposable empty collections deleted after smoke
→ browser tab and local servers closed

Focused Gate re-review: production Next UI + isolated in-memory MOCKED API
→ one shared collection GET
→ create propagates to manager/upload/QA/files
→ rename kb-a → kb-b propagates; old absent; subsequent request uses kb-b
→ delete selected collection propagates; consumers fall back; QA history clears
→ manual KB switch clears history; menu switch preserves QA draft
→ no stale request after rename/delete
→ console warning/error count 0
→ F-1 CLOSED; verdict PHASE_11_PASS — READY_FOR_PHASE_12
```

### Evidence ledger

| Evidence | Label | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| production build | `BUILD / REAL` | page/error/components/types/CSS compile；static generation | runtime error catch 或 all interactions |
| four-menu navigation | `REAL BROWSER` | visible modules switch、URL 不导航、无新增 console warning/error | state correctness inside every feature |
| persistent panel DOM | `REAL BROWSER` | four wrappers coexist，one visible | hidden effects 无成本或 overlays 全部隔离 |
| QA draft preservation | `REAL BROWSER` | menu switch retains controlled input | full success history preservation |
| empty-KB + KB switch | `REAL BROWSER + REAL BACKEND` | Ctrl+Enter、409 UI、owner switch reset | real retrieval/LLM success history |
| `requestVersionRef` | `STATIC` | stale-response rejection control flow 存在 | real slow-response race reproduction |
| all component state matrix | `STATIC + PARTIAL RUNTIME` | branches、indicators、retry actions 存在；部分 states observed | 每个 state 的 exhaustive visual behavior |
| route `error.tsx` | `BUILD / STATIC` | Next convention file 与 fallback/reset compile | injected render crash 确实被 catch |
| expected 409 console log | `REAL BROWSER` | handled domain error 仍被 client 记为 console error | production logging policy suitability |
| shared collection synchronization | `MOCKED BROWSER + STATIC` | single GET、CRUD propagation、selection migration/fallback、QA owner reset | browser-to-real-FastAPI full workflow、并行 delete race |
| repository-owned frontend tests | `NOT_AVAILABLE` | — | repeatable component/E2E regression suite |

Task smoke 没有调用真实 LLM、上传文件、删除用户数据或进入 Phase 12；只创建两个明确命名的 empty test collections 来验证 owner switch，随后清理。Gate focused re-review 使用 isolated in-memory MOCKED API，不触碰真实 Backend data。

首次尝试使用本地 `agent-browser` CLI 时工具未安装；Python Playwright package 也不可用，因此按已加载的 Web App Testing fallback 使用现有 in-app browser。一次 `networkidle` wait 与一次 page-evaluate probe 受当前 browser interface 限制失败，均未改变应用状态，也没有被计为 product failure 或 PASS evidence。

Bundle 数字没有 analyzer、stable baseline、production measurement 或 budget；只作为 Gate checkout 的 time-specific observation，不推导 regression。F-3 parallel-delete local projection race 以 MINOR `ACCEPTED_V1_BOUNDARY` 保留；F-4 error-boundary runtime injection 以 INFO deferred 到 T1204。

---

## 75. T1105 Engineering Questions（短摘要）

1. 为什么 menu switch 保留 state，而 KB switch 清 history？——前者改变 view，后者改变 conversation owner。
2. `hidden` 是否等于 unmount？——否；component/effects/state 继续存在。
3. persistent mount 的成本是什么？——eager child-resource work、mounted tree 与后台 effects；collection GET 已集中，但 hidden feature 仍然 mounted。
4. state preservation 是否保证 data freshness？——否；本项目通过 Home shared projection + mutation revision 单独解决 collection freshness。
5. 为什么四个组件不必使用完全相同 state names？——要统一 lifecycle semantics，不抹平 domain-specific states。
6. error boundary 能捕获 fetch rejection 吗？——不能依赖它；async handler 应显式 catch。
7. `reset()` 是否回滚 Backend mutation？——否，只尝试重新渲染 segment。
8. 为什么 expected 409 仍出现 console.error？——transport client 对所有 non-2xx 统一 error logging。
9. 无 console warning 是否证明 app 正确？——否，只证明特定 observation window 无已记录消息。
10. 为什么 version guard 不等于 cancellation？——它控制 UI commit，不停止已经发出的工作。

---

## 76. Phase 11 Interview Promotion

- **30 秒主线**：我把 cross-component consistency 定义为 ownership policy。菜单只改变 visibility，所以 persistent mount 保留 local state；collection resource 由 Home 共享；KB identity 改变时各 feature reconcile selection，QAPanel 清空旧 owner state 并用 generation token 拒绝旧响应。
- **Gate remediation 闭环**：Gate 发现 persistent panels 保留了四份 stale collection cache；修复把 collection resource 提升到最小公共 owner，并用 revision event 传播 rename/delete identity change；focused re-review 证明 F-1 CLOSED。
- **关键 trade-off**：没有引入 Redux/React Query，而是用 page-level source + pure resolver；复杂度较小，但 delete projection 的并行 closure race 作为 v1 MINOR 边界保留。
- **错误分层**：API client 做 transport normalization，feature 处理 expected async errors，Next route boundary 处理 unexpected render failure；`reset()` 不回滚后端。
- **高价值追问**：为什么 empty-KB 409 UI 正确但 console 仍有 error？为什么 modal portal 不能只靠 parent hidden 推断？为什么 Context/query cache 应由故障模型驱动而不是为了“统一”而引入？
- **诚实证据**：Task smoke 真实连过 FastAPI 的 navigation、draft preserve、409 与 KB reset；F-1 focused verification 是真实 production UI + MOCKED API。error-boundary crash、slow-response race、real QA success 与全面 a11y 仍未验证。

精选内容已晋升到 [Interview Guide 的 Phase 11 深度章](./interview-notes/dx-rag-interview-guide.md#phase-11-learning-review)。这是一段 Gate discovery/remediation/verification 闭环，不是生产 incident；面试时不得包装成线上事故。

---

## 77. T1105 自测题与答案

### Questions

1. 当前 menu switch 为什么能保留 QAPanel draft？
2. `hidden` panel 是否仍会执行 `useEffect()`？
3. F-1 remediation 后首屏 collection read 的 owner 是谁？hidden panels 是否仍会执行 effects？
4. menu switch 与 KB switch 在 domain identity 上有什么不同？
5. QAPanel 切 KB 时具体清除哪些 state？
6. 只清空 history 为何仍不足以阻止 old answer 污染 new KB？
7. persistent mount 为什么曾增加 collection cache staleness，当前怎样修复？
8. Home 现在拥有哪些 shared state，为什么没有把所有 feature state 都提升？
9. 四个 component 的一致性体现在哪些 lifecycle semantics？
10. `empty` 与 `error` 为什么必须分开？
11. API client、feature Alert、route error boundary 分别处理什么？
12. `app/error.tsx` 不能替代哪些 try/catch？
13. `reset()` 会刷新整个 browser 或回滚 mutation 吗？
14. 为什么当前 error boundary 只有 STATIC/BUILD evidence？
15. normal navigation 的 console evidence 是什么？
16. 为什么 empty-KB 测试后仍出现一条 console.error？
17. React key warning 未出现能证明所有 identity 都正确吗？
18. hidden wrapper 为什么不能自动证明 portal overlay isolation？
19. 不引入 Redux 时，当前 collection freshness 方案是什么？
20. 全部 T1101–T1105 DONE 与 Gate PASS 的逻辑关系是什么？当前 verdict 是什么？

### Answer keys

1. 四个 feature 始终 mounted，menu 只切换 wrapper 的 `hidden`。
2. 会；hidden 影响 presentation，不销毁 component instance。
3. Home 是唯一 `listCollections()` caller；hidden children 仍 mounted，会运行自己的 reconciliation、scroll 或 child-resource effects。development effect 仍可能重复。
4. menu 只换 view；KB 改变 conversation/data owner。
5. history、draft question、pending question、query state 和 query error，并递增 request version。
6. in-flight Promise 仍可 settle；version mismatch guard 才能拒绝 late commit。
7. 旧架构让四份独立 cache 长期存活；当前由 Home shared collection projection、CRUD callbacks、mutation revision 与 resolver 统一同步。
8. Home 保存 `selectedKey`、collections/load/error、mutation event；feature selection 与 upload/QA/file transaction state 仍归各 feature。
9. loading、usable/success、empty、expected error 与 contextual recovery；domain-specific 额外状态可保留。
10. empty 是 successful read with zero items，可给下一步 guidance；error 是没有得到 usable result，需要 retry/recovery。
11. client 规范化 transport error；feature 把 expected failure 映射为 recovery UI；route boundary 处理 unexpected render failure。
12. event handler、async fetch/mutation rejection 仍需显式处理。
13. 不会；它尝试重渲染 route segment，不提供 data compensation。
14. 本轮未注入 render crash，只确认 convention file 存在且 build 通过。
15. fresh load 为空；连续四模块导航没有新增 warning/error。
16. client 对所有 non-2xx 统一 `console.error`，即使 feature 已把 409 处理成 expected warning。
17. 不能；只证明本次 interaction window 没观察到 warning，仍需 component regression tests。
18. Modal/Select popup 可 portal 到 wrapper 之外，需独立 lifecycle/focus 测试。
19. page-level shared source + server-confirmed projection callbacks + revision event + pure selection resolver；规模扩大后才评估 query cache。
20. DONE 只证明任务状态；独立 Gate 在 F-1 remediation 后给出 `PHASE_11_PASS — READY_FOR_PHASE_12`，随后才执行本 Phase Learning Review。

---

## 78. Phase Learning Review 收口边界

Phase Learning Review 完成。当前准确表述是：**Phase 11 四个 feature 已采用 persistent mounted panels 保留 menu-switch local state；Home 提供共享 collection source 与 mutation revision，children 统一 reconcile rename/delete 后的 selection；QAPanel 在 owner change 时清空 conversation 并拒绝 stale response；各 feature 具备 domain-specific loading/usable/empty/error/recovery，`app/error.tsx` 提供 route-level fallback。Gate 在 F-1 remediation 后给出 `PHASE_11_PASS — READY_FOR_PHASE_12`。**

证据必须分层表述：production build 为 REAL/BUILD；Task smoke 部分使用真实 browser-to-FastAPI；F-1 focused re-review 为真实 production Next UI + isolated in-memory MOCKED API。Error-boundary crash injection、real QA success、slow-response race、全面 overlay/focus/a11y 与 repository-owned frontend regression suite 仍为 `NOT_AVAILABLE / DEFERRED`；并行 delete projection race 是已接受的 v1 MINOR boundary。

该 Learning Review 当轮只更新 Technical Learning、README、Project Map 与 Interview Guide；未修改 `page.tsx`、`error.tsx`、components、API client、CSS、SPEC 或 TASKS，也未启动 Phase 12。Phase 11 Engineering Review 后续已于 2026-09-07 独立完成；仍未 commit/push。
