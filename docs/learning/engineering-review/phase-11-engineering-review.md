# Phase 11 — Frontend Features Engineering Review

> **Coverage**：T1101 KnowledgeBaseManager；T1102 FileUpload；T1103 QAPanel；T1104 FileManager；T1105 Cross-Component State Patterns
>
> **Status**：COMPLETE（2026-09-07）。本文件是 Layer 2 Engineering Review；完成表示工程决策复盘已经收口，不表示 Known Gaps 已被实现修复。
>
> **Gate context**：既有独立 Gate focused re-review 在 F-1 remediation 后给出 `PHASE_11_PASS — READY_FOR_PHASE_12`。该 verdict 仅作为输入，本文件不重发、不升级也不替代 Gate 结论。
>
> **Evidence vocabulary**：`STATIC/CODE-LEVEL` 表示当前源码、类型与冻结契约对照；`BUILD` 表示本轮真实 production build；`GATE CONTEXT / MOCKED` 表示复用既有 production UI + isolated in-memory mocked API 证据；`DEFERRED` 表示后续范围；`NOT_AVAILABLE` 表示当前没有 repository-owned 证据。
>
> **Boundary**：本轮只新增 Engineering Review 并同步学习导航；不修改 frontend application、`SPEC.md` 或 `TASKS.md`，不启动 Phase 12，不 commit/push。

## 1. 当前工程结论

Phase 11 已把 Phase 10 的单页 shell 变成四个可操作 feature，并在 F-1 remediation 后形成了清晰的两层状态所有权：`page.tsx` 拥有跨 feature 共享的 collection read model，各 feature 继续拥有与自身交互绑定的 transaction state。这个选择以很小的机制成本解决了 create/rename/delete 后四个 panel 的 collection identity 同步问题，符合 v1 “React built-in state、无全局状态库”的冻结约束。[STATIC/CODE-LEVEL]

当前实现不是“所有前端数据都全局一致”的系统。它对 collection CRUD 与 file delete 做 server-confirmed local projection，对 list/preview/QA 使用 request-version guard；但 upload success 没有通知 Home 更新 `file_count`，也没有让常驻 FileManager 重新拉取列表。上传与文件删除在用户切换 collection 时还存在 late-settlement ownership 边界。它们不改写既有 Phase 11 Gate verdict，却是 T1203 cross-feature verification 必须首先验证、必要时修复的具体入口条件。[STATIC/CODE-LEVEL]

| 维度 | 当前结论 | 工程姿态 |
|---|---|---|
| Feature coverage | KB CRUD、单文件上传、QA、文件列表/预览/删除均已接入 centralized client | 适合 v1 单页工作流 |
| Shared identity | Home-owned collection source + mutation revision + pure resolver | F-1 已关闭；避免四份 collection cache |
| Local interaction state | modal、upload outcome、conversation、preview/delete 状态留在 feature 内 | ownership 清晰，避免过度提升 state |
| Read race safety | collection list、file list、preview、QA answer 有 last-intent-wins guard | 旧响应不可覆盖新 owner；网络工作本身未取消 |
| Mutation concurrency | collection/file delete 仍有 closure/pending-slot race；upload 无 owner/version commit guard | 单用户顺序操作可用，并发与切换边界需收紧 |
| Cross-feature freshness | collection CRUD 与 file delete 有 projection；upload success 无 invalidation | T1203 的首要 integration risk |
| Verification | 本轮 build PASS；Gate browser evidence 可追溯；repository-owned frontend tests 不存在 | `NOT_AVAILABLE` 不得写成自动化测试通过 |
| Review disposition | Engineering Review 可关闭；应用改进留给明确 task/bug-fix scope | 不在 review 中顺手改业务代码 |

## 2. 为什么需要这个模块

Phase 10 只提供 transport 与 composition boundary。Phase 11 才建立用户真正可执行的闭环：

```text
collection CRUD
      ↓ shared collection identity
upload → ingest result
      ↓ durable chunks/files
QA → answer + backend-owned sources
      ↓ inspectability
file list → persisted preview → cascade delete
```

如果四个 feature 各自维护 collection 列表，rename/delete 会立刻形成 stale option、旧名称请求与 QA history 泄漏；如果把所有 state 都提升到 Home，modal input、pending question、preview drawer 等局部生命周期又会污染页面 owner。Phase 11 的工程价值因此不只在“有四个组件”，而在于区分了 shared server-resource projection 与 feature-local transaction state。

## 3. 核心设计决策（ADR）

### ADR-01：使用 persistent mounted panels 保留菜单切换状态

- **Decision**：四个 feature 始终挂载，以 wrapper `hidden` 切换可见性，不再按 `selectedKey` 条件卸载。
- **Context / Problem**：菜单切换若触发 unmount，上传结果、QA draft/history、文件 preview context 等 local state 会被无意清空，违反 AC-FE-01 的 preservation 目标。
- **Why**：不引入 router/global store，也能直接保留 feature-local state。
- **Trade-off**：隐藏 panel 的 effects、请求与 DOM 仍存在；所有 feature 静态进入首屏 bundle，后台 transaction 也可能在用户切走后继续完成。
- **Future**：只有 bundle/内存/后台请求 metrics 或更复杂 lifecycle 明确出现压力时，才评估 keep-alive abstraction、route split 或显式 state persistence。

### ADR-02：让 `Home` 成为唯一 shared collection read-model owner

- **Decision**：`page.tsx` 只执行一条 `listCollections()` lifecycle，并把 `collections/state/error/retry/mutation` 传给四个消费者。
- **Context / Problem**：最初每个 panel 各有 collection cache；persistent mount 会把 rename/delete 后的 stale cache 从短暂问题变成永久一致性问题，即 Gate F-1。
- **Why**：collection 是跨 feature 共享资源，最小共同 owner 正是页面；当前规模无需 Redux/Zustand 或 server-state library。
- **Trade-off**：Home 开始承载 resource callbacks；若未来共享资源种类持续增加，prop contract 与页面 reducer 会膨胀。
- **Future**：先按 resource 拆 provider/reducer；只有出现跨路由、dedupe、background refetch、invalidation policy 等需求时再采用 TanStack Query/SWR。

### ADR-03：用 mutation revision + pure resolver 修复 collection identity

- **Decision**：create/rename/delete 成功后发布单调 revision 的 `CollectionMutation`；children 通过 `resolveCollectionSelection()` 迁移 rename identity、保留仍存在的选择或 fallback 到第一项。
- **Why**：仅传最新 collections 无法区分“旧名称被 rename”与“旧选择已 delete”，而 QA 对两者都要把 owner change 当作 conversation reset boundary。
- **Trade-off**：该对象是 latest event，不是 event log；多个 mutation completion 在同一 render window 合并时，中间 identity transition 可能不可见。
- **Future**：并发 mutation 成为真实需求时，用 serialized command queue、reducer event log 或 authoritative refetch 代替单槽 latest event。

### ADR-04：mutation 成功后做 server-confirmed local projection

- **Decision**：collection create/rename/delete 与 file delete 都等待 Backend success，再更新 local arrays/counts；不做 pre-response optimistic commit。
- **Why**：避免 Backend rejection 后复杂 rollback，也让成功 toast 与页面事实基于 server acknowledgement。
- **Trade-off**：projection 不是 authoritative refetch；丢失 response、并发 callback、其他 client 修改或局部 side effect 都可能让 read model 漂移。
- **Future**：在 destructive/cross-feature mutation 后引入 targeted invalidation/refetch，并明确 loading continuity 与 error reconciliation UX。

### ADR-05：共享 resource state 与 feature transaction state 分层

- **Decision**：Home 只拥有 collection resource；KnowledgeBaseManager 拥有 modal/operation state，FileUpload 拥有 upload transaction，QAPanel 拥有 conversation，FileManager 拥有 file/preview/delete state。
- **Why**：state owner 与改变它的用户动作、异步 lifecycle 保持接近，减少 giant page reducer 与无关 rerender coupling。
- **Trade-off**：跨 feature mutation 必须显式发布 invalidation/projection；当前 upload→file list 正暴露了遗漏此协议的风险。
- **Future**：新增 mutation 时强制回答“它改变哪些 read models、由谁失效、late response 归谁”三个问题。

### ADR-06：区分 menu switch 与 collection switch

- **Decision**：menu switch 保留 panel local state；collection identity 改变则清理 owner-scoped state。QAPanel 清空 history/draft/pending，FileUpload 清 outcome，FileManager 关闭 preview 并读取新 owner。
- **Why**：菜单只是视图导航；collection 是业务数据 owner。把两者都当 reset 或都当 preserve 都会产生错误语义。
- **Trade-off**：每个 feature 都要实现 collection reconciliation effect，代码有少量重复；新增 owner-scoped state 容易漏 reset。
- **Future**：将 owner transition 行为纳入 repository-owned component tests，而不是只靠 review memory。

### ADR-07：对 read/query 使用 last-intent-wins guard，而不是假设 Promise 按序完成

- **Decision**：collection list、file list、preview 和 QA 分别维护 request version；owner change、close 或新请求让旧 response 失去 commit 权。
- **Why**：网络完成顺序不等于用户意图顺序；只清 UI state 不能阻止旧 Promise 稍后写回。
- **Trade-off**：guard 只丢弃 late result，不取消 HTTP、retrieval 或 LLM 工作；FileUpload 与 mutation commands 还没有同等级 commit guard。
- **Future**：昂贵/长耗时请求需要 AbortController、server cancellation/request ID 或 mutation ownership token 时，再扩展 transport contract。

### ADR-08：前端校验用于 early feedback，Backend 保持最终 trust boundary

- **Decision**：collection name、extension、binary size 与 empty file 在发请求前校验；Backend 继续执行同类校验、path safety 与 persistence preflight。
- **Why**：减少明显无效请求并提供即时中文反馈，但浏览器输入与前端代码都不能替代服务端安全边界。
- **Trade-off**：50 MB、扩展名集合与 regex 在前后端有重复 owner，配置改变时可能 drift。
- **Future**：通过 generated metadata/config endpoint 或 contract tests降低 drift；不要删除 Backend validation。

### ADR-09：把 `SUCCESS_WITH_WARNINGS` 作为成功后的独立 domain outcome

- **Decision**：upload 使用 `idle/uploading/success/warning/error`，warnings 由独立映射展示，不把部分 OCR 页面失败压成 generic error。
- **Why**：Backend durable commit 已成功时，UI 必须承认文件可用，同时准确提示降级范围。
- **Trade-off**：warning 文案依赖已知 code catalog；未知 warning 的表达与 recovery policy有限。
- **Future**：warning catalog 扩大时，由 typed/domain metadata 驱动 title、severity 与 action。

### ADR-10：QA history 只记录完成的问答对，并绑定当前 collection

- **Decision**：pending question 独立展示；response 成功后才把 user/assistant pair 写入 history，并保留最近 20 条；collection change 清空全部 conversation state。
- **Why**：避免把失败或未完成 assistant turn 发回 Backend，也满足 F014 的 owner isolation 与长度上限。
- **Trade-off**：refresh/unmount 后丢失；没有 streaming、cancel、server session 或跨设备恢复。
- **Future**：若引入持久 conversation，必须先定义 conversation identity、privacy、migration 与跨 KB 禁止关系。

### ADR-11：answer content 与 sources 分开，source truth 由 Backend 返回

- **Decision**：answer 交给 ReactMarkdown；sources 读取 typed Backend response，以 `chunk_id` 作为 UI identity，显示 file name 与 relevance score。
- **Why**：LLM 自述 citation 不可靠；retrieval metadata 才是可追溯来源。
- **Trade-off**：Frontend 不验证 success payload runtime shape；Backend schema drift 仍可能在渲染期暴露。
- **Future**：在 API boundary 加 runtime schema validation，并保持 source display 不从 Markdown inline marker 推导。

### ADR-12：文件操作统一使用 immutable `file_id`

- **Decision**：Table row key、preview 与 delete 都使用 `file_id`；`file_name` 只做 display metadata。Preview 展示 persisted chunks 的诊断性拼接，不声称等于原文件。
- **Why**：名称可重复且可展示，UUID 才能稳定标识 resource；persisted preview 能检查真实入库内容而无需重新 Parser/OCR/Embedding/LLM。
- **Trade-off**：chunk overlap、heading prefix 与 5000-char truncation 会使 preview 不忠实于原文；无 download/原文件 render。
- **Future**：原文预览若成为产品需求，应设计独立安全下载/render contract，而不是改变当前 diagnostic semantics。

### ADR-13：destructive confirmation 只表达人类意图，级联仍由 Backend 拥有

- **Decision**：collection/file delete 在 UI 使用不可逆确认；Frontend 发送 resource identity，Backend 负责 filesystem、Chroma 与 keyword-index 级联及 path safety。
- **Why**：确认框可减少误触，却不能实现 authorization、transaction、rollback 或 containment。
- **Trade-off**：server commit 后 response 丢失时，UI 可能显示 error，而副作用已经发生；第二次 delete 也未定义为幂等 success。
- **Future**：高可靠需求需要 idempotency/reconciliation、audit trail 或 trash/undo 产品决策，不应由确认框伪装。

### ADR-14：采用 transport、feature、route 三层错误边界

- **Decision**：API client 规范化 network/non-2xx/invalid JSON；feature 捕获 expected async failure并给 owner-specific retry；`app/error.tsx` 处理 unexpected route render/lifecycle failure。
- **Why**：错误的恢复 owner 不同，不能用一个 global boolean 或 Error Boundary 覆盖全部分支。
- **Trade-off**：route fallback 尚无 runtime crash-injection proof；expected 4xx 也会进入 `console.error`，console cleanliness 与业务错误观测语义需要区分。
- **Future**：补充 error code→action policy、telemetry/redaction 与 error-boundary runtime test。

## 4. 架构影响

### 4.1 依赖方向

```text
SPEC F002 / F014 / F016 / F017
                 ↓
       lib/types.ts contracts
                 ↓
       lib/api-client.ts transport
                 ↓
    page.tsx shared collection owner
       │             │
       │             └── mutation revision / projection callbacks
       ↓
KnowledgeBaseManager · FileUpload · QAPanel · FileManager
       ↓                         ↓
 feature-local state      Backend durable truth
```

Feature components 不直接拥有 base URL、wire error parsing 或 Backend persistence；Home 不拥有 QA answer、upload file、preview result 等局部 transaction。依赖方向总体保持单向。

### 4.2 State 与 contract owners

| State / Contract | Owner | Consumer / effect | 当前刷新策略 |
|---|---|---|---|
| API URL、serialization、`ApiError` | `api-client.ts` | 全部 feature | 每次 request |
| collection array/load/error | `page.tsx` | 四个 feature | initial/retry GET + CRUD projection |
| collection identity transition | `page.tsx` mutation revision | Upload/QA/Files resolver | latest server-confirmed event |
| navigation selection | `page.tsx` | SideMenu + panel visibility | local controlled state |
| CRUD modal/pending/notice | KnowledgeBaseManager | 当前 panel | feature local |
| upload file/progress/outcome | FileUpload | 当前 panel | feature local；成功无跨 feature invalidation |
| QA question/history/query | QAPanel | 当前 collection | local max 20；owner change reset |
| file list/preview/delete | FileManager | 当前 collection | owner change/read retry/delete projection |
| persisted files/chunks/vectors | Backend | Upload/QA/Files APIs | Backend durable truth |

### 4.3 事件与 reconciliation 矩阵

| Event | Shared collection projection | Upload | QA | Files |
|---|---|---|---|---|
| menu switch | 不变 | preserve | preserve | preserve |
| collection create | append `{name,file_count:0}` | 空列表时 resolver 可选第一项 | 空列表时 resolver 可选第一项 | 空列表时 resolver 可选第一项并加载 |
| selected collection rename | old→new | selection migrate，outcome clear | selection migrate，conversation reset | selection migrate，preview close + reload |
| selected collection delete | remove + first/none fallback | fallback，outcome clear | fallback，conversation reset | fallback，preview close + reload |
| manual collection switch | 不变 | outcome clear | history/draft/pending clear，旧 answer 无 commit 权 | preview close + new list request |
| upload success | **当前无 file_count 更新** | success/warning result | 不变 | **当前无 list invalidation** |
| file delete success | matching `file_count - 1` | option count更新 | option count更新 | row local remove + notice |

矩阵中 upload success 一行是不对称点：它不是冻结 F017 单组件状态遗漏，却会直接影响 T1203 的 upload→list 跨 feature workflow。

### 4.4 没有改变的边界

- Backend 仍是 collection、file、chunk/vector/metadata 与 QA answer/source 的 durable truth。
- Frontend 不执行 parser、OCR、embedding、retrieval、context assembly、LLM 或 cascade path safety。
- v1 仍无独立 URL routes、Redux/Zustand、authentication、dark mode、多语言、batch upload/delete、streaming 或 conversation persistence。
- Phase 12 verification 仍是 TODO；本 review 不把静态分析或 mocked Gate scenario 描述成真实 provider/Chroma full E2E。

## 5. 工程问题分析

### 5.1 可维护性

正向因素：

- 每个 feature 只通过 endpoint functions 调用 API，error normalization 与 URL encoding 未重新散落。
- `CollectionSourceProps` 与 pure resolver 明确共享 contract；F-1 remediation 没有引入第三方 global store。
- state unions 把 idle/loading/success/warning/empty/error 的 domain 差异写进 TypeScript，而不是多个互相矛盾的 booleans。
- request version 分 resource 独立维护，file list 与 preview 不共享一个取消槽。

压力点：

- 四个主要组件约 373–527 行；UI markup、state machine、error copy 与 async orchestration 已处于同文件。继续添加 pagination、cancel、telemetry 或 batch actions 会显著增宽组件职责。
- selection reconciliation effect 在 Upload/QA/Files 重复；它目前可读，但新增第五个 consumer 时应考虑 owner-aware hook，并保持 pure resolver 可单测。
- Home 的 projection callbacks 已开始承担跨 feature cache policy；新增 upload success、external refresh 或 optimistic update 后，简单 callbacks 容易演变为隐式 event bus。
- operation pending 多用单个 nullable id/string；这表达“一个当前操作”，不能表达合法并发集合。

### 5.2 一致性与数据语义

当前 collection ownership 是正确方向，但 consistency model 必须准确命名为：**single-page, server-confirmed, locally projected read model**。

1. **Collection CRUD**：成功后 functional create/rename projection；delete 仍从 render closure 计算 `remaining`。Gate F-3 已把并行 delete lost update 记为 MINOR `ACCEPTED_V1_BOUNDARY`。
2. **Upload→Files**：FileUpload success 只更新自己的 result。因为 FileManager 常驻且通常已在隐藏状态完成初始 list request，用户切回文件管理时可能继续看到旧空表/旧计数，直到切换 KB、错误 retry 或 reload。这是 T1203 必须验证/修复的 cross-feature freshness gap。
3. **Upload owner switch**：`runUpload()` 捕获开始时的 collection，却没有 request version/owner token。上传期间 Select 仍可切换，其他常驻 panel 也可 rename/delete collection；effect 清 outcome 后，旧 upload Promise 仍可晚到并把结果写回当前 panel。
4. **File delete owner switch**：Backend delete 成功后若用户已切换 collection，success branch 在 `onFileDeleted()` 前 return；新 owner 不被旧 result污染，但旧 owner 的 Home `file_count` projection 也未更新。
5. **Parallel file delete**：两个 handler 都使用各自 render closure 的 `files.filter(...)`，后完成的 local projection 可“复活”先前已删 row；单个 `deletingFileId` 的 finally 也可能提前清除另一操作的 indicator。Backend 数据未必复活，漂移发生在 local read model。
6. **External writers**：shared collection GET 只有 initial/retry，没有 focus/poll/subscription；其他 browser/client 的 CRUD/upload/delete 不会自动进入当前 read model。
7. **Latest mutation slot**：revision 防重复消费，但只保存最新事件；高并发 settlement 需要 event log、serialization 或 refetch 才能确保每次 identity transition 都可观察。

### 5.3 Failure taxonomy

| Failure class | 当前处理 | Residual risk / recovery boundary |
|---|---|---|
| collection GET late response | request version拒绝旧 commit | fetch 继续执行；无 timeout/abort |
| collection CRUD 4xx/5xx/network | modal/card error + retry；成功后 projection | 并行 command 共享单个 `pendingAction`，indicator 与 closure 可竞态 |
| invalid local upload | beforeUpload 拒绝，不发 request | 前后端常量可能 drift，Backend 仍须复验 |
| upload API failure | typed feature error + retry file | retry 可能遇到 server 已 commit/response 丢失，不天然幂等 |
| upload owner changed in flight | **无 commit guard** | late success/error 可覆盖已清理 outcome；需 owner token/disable switch/cancel/refetch policy |
| QA answer late after KB change | query version拒绝旧 commit | Backend retrieval/LLM 仍消耗资源；无取消 |
| empty KB query | `COLLECTION_EMPTY` → dedicated state/copy | retry 前若不上传文件通常仍确定性失败 |
| file list/preview late response | 独立 version guards；close 使 preview失效 | HTTP 仍继续；无 cancel |
| file delete after owner switch | 旧 owner UI commit 被拒绝 | server may have deleted；旧 owner count不更新，需 refetch/reconciliation |
| parallel file/collection delete | single pending slot + closure projection | local lost update/row resurrection；F-3 已接受其中 collection boundary |
| unexpected render/lifecycle error | route `error.tsx` + reset | runtime crash injection 未验证；reset 不回滚 Backend mutation |
| expected non-2xx | API client统一抛 `ApiError` 且 `console.error` code/status | 正常可恢复 4xx 也计入 console error；无 telemetry taxonomy |
| malformed 2xx JSON shape | JSON syntax检查；之后 `as T` | 合法 JSON 的 schema drift 可穿过 transport boundary |

### 5.4 性能、可用性与 accessibility

- 本轮 build 观察到 `/` route size 245 kB、First Load JS 385 kB，shared JS 87.2 kB。[BUILD] 这是单次 observation，不是 regression 结论；仓库没有 budget、baseline、Web Vitals 或低端设备数据。
- persistent panels + static imports 意味着四个 feature 首屏一起进入 bundle并挂载；换来 state preservation，也会让隐藏 FileManager 初始读取列表。
- FileManager `pagination={false}`，collection/file arrays 使用 O(n) map/filter/reduce。v1 小数据可接受；文件和 collection 达到百/千级前需要 server pagination/filtering 与 render virtualization。
- Upload 的 12%→100% 是 coarse UI progress，不是 byte progress 或 ingestion stage telemetry；F002 明确不包含 progress push，不能把它描述为真实管线进度。
- Ant Design 提供 Modal/Popconfirm/Select 等基础 keyboard/focus semantics，页面也使用 label/aria-live；但 portal focus、screen reader announcement、360px overlay 与 automated accessibility audit 仍无持续证据。
- QA 自动滚动、Markdown 与 expandable sources 改善可用性；大 answer/大量 sources 的 render cost 与 code-block overflow 没有性能基线。

### 5.5 安全、隐私与部署

- v1 仍假设 local/trusted network 且无认证；Frontend collection selector 不是 authorization boundary。暴露到不可信网络前必须补 authentication、authorization、TLS、CORS 与 audit policy。
- 文件扩展名、大小、空文件的前端校验只提供 UX；Backend path-safety、preflight、rollback/cascade 才是安全 owner。
- ReactMarkdown 当前未接入 raw-HTML plugin，降低直接执行 answer HTML 的风险；未来添加 `rehype-raw`、自定义 link/image renderer 时必须重新做 XSS 与 external-resource review。
- `NEXT_PUBLIC_API_BASE_URL` 是公开 build-time config，不是 secret，也不是运行时 service discovery。
- API client console 只记录 error code/status，当前未见 request body/file content 泄漏；但仓库没有 telemetry、PII redaction、correlation ID 或 production logging policy。

## 6. 规模扩大分析（Future / Not implemented in v1）

| Scale / Trigger | 当前压力 | 需要先定义 | 可能演进方向 |
|---|---|---|---|
| 10x collections/files | O(n) option/list operations、无分页、四 panel eager mount | expected counts、latency/bundle budget | server pagination/search、virtual table、dynamic import（先测量） |
| 10x concurrent UI actions | single pending slot、closure projection、latest mutation event | command serialization与可否并发 | mutex或 pending `Set`、functional reducer、mutation后 refetch |
| slow upload/QA | coarse progress、无 abort、旧工作继续 | cancellation semantics、server commit point、retry idempotency | AbortController/request ID、job status、明确 reconciliation |
| multiple browser clients | initial/retry snapshot会 stale | freshness SLA、冲突策略、authoritative owner | focus/poll refetch、query cache invalidation、SSE/WebSocket |
| more shared resources/pages | Home props/callbacks 扩张 | cache key、ownership、route lifecycle | domain provider/reducer；达到阈值后采用 server-state library |
| 100x QA history/large answers | DOM/source render与 payload 增长 | token/message/DOM budgets | conversation paging、streaming、server session（产品变更） |
| 1000x users/untrusted network | 无 auth/audit/tenant boundary | identity、RBAC、tenant isolation、privacy retention | authenticated gateway、per-tenant storage、audit/observability |
| independent frontend/backend releases | compile-time types不能发现 runtime drift | schema compatibility与发布策略 | OpenAPI generated client、runtime validators、contract tests |

不要在没有 workload 和 metrics 时预装复杂 state/cache infrastructure。当前最优先的升级不是“换库”，而是先让 upload/delete 的 invalidation 与 owner-transition protocol 可重复验证。

## 7. Verification Review

本轮在当前 checkout 独立执行：

```text
frontend> npm.cmd run build
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Generating static pages (4/4)
exit code 0

Route /: 245 kB
First Load JS: 385 kB
```

脚本盘点：

```text
npm.cmd run
available: dev, build, start
test script: NOT_AVAILABLE
```

证据分层：

- **`STATIC/CODE-LEVEL`**：对照 F002/F014/F016/F017 与 T1101–T1105；精读 `page.tsx`、四个 feature components、collection resolver、validators、API client、types 与 route error boundary。
- **`BUILD`**：当前工作树 production compile、lint/type validation、page-data collection、static generation PASS。
- **`GATE CONTEXT / MOCKED`**：既有 focused re-review 使用真实 production Next UI + isolated in-memory mocked API，验证 single collection GET、create/rename/delete propagation、selection fallback、QA reset、menu preservation 与 observation window 内 console 0 warning/error。该证据未在本 review 重跑，也不是真实 FastAPI/provider/Chroma E2E。
- **`DEFERRED / NOT_AVAILABLE`**：upload→list→preview→delete→re-upload full flow、real provider/Chroma/upload、owner-switch slow response、parallel mutation reproduction、runtime Error Boundary crash injection、完整 portal/focus/a11y、performance metrics 与 repository-owned frontend regression suite。

因此准确说法是：**当前 frontend production build PASS；既有 scoped browser evidence 可追溯；repository-owned frontend automated tests 为 `NOT_AVAILABLE`。**

## 8. Known Gaps & Pending Questions

### 8.1 Phase 12 首要验证/修复候选

1. **Upload invalidation**：upload success 后由谁更新 Home `file_count`、让 FileManager 刷新、避免隐藏 panel 的旧列表？T1203 应覆盖“先访问 Files → 上传 → 返回 Files”场景。
2. **Upload late settlement**：上传中手动切 KB、rename/delete target 或切 panel 后，旧 response 是否仍可展示为新 owner outcome？需要 owner/version guard、禁用策略或 cancel/reconcile 方案。
3. **Delete owner transition**：file delete 完成前切 KB 时，Backend success 与 old-owner count/list 如何收敛？不能只丢弃 UI commit 而永不 invalidation。
4. **Parallel mutations**：复现 collection/file concurrent delete；至少决定全局 mutex、pending set + functional update，或 success 后 authoritative refetch。Gate F-3 的 accepted boundary 不等于永久忽略。
5. **Full cross-feature evidence**：按 T1203 执行 upload→list→preview→delete→re-upload、cross-KB isolation 与三存储 side effects；MOCKED API 不替代这条证据。

### 8.2 持续工程债务

6. **Repository-owned tests**：为 resolver、validators、API error branches、owner reset、stale commit、warning states 与 mutation propagation建立 component/integration tests，再补 Playwright E2E。
7. **Error Boundary runtime proof**：F-4/T1204 仍需 deterministic render-crash injection，验证 fallback 与 reset；build 不能证明 runtime catch。
8. **Success runtime validation**：合法 JSON 错误 shape 仍可穿过 `request<T>`；需要定义 Zod/Valibot/OpenAPI generation 的升级阈值。
9. **Frontend/backend config drift**：50 MB、extension catalog、collection regex 是重复事实；至少需要 contract probe 或 generated/shared metadata。
10. **External freshness**：visibility/focus refetch、polling或订阅何时需要？先定义 local/trusted v1 的 freshness expectation。
11. **Mutation event semantics**：latest revision 是否足够，还是需要有序 event/reducer？答案取决于是否允许 overlapping commands。
12. **Retry/idempotency**：upload/delete 在 server commit 后 response 丢失时如何向用户解释并收敛，而不是简单重复 command？
13. **Observability taxonomy**：expected validation/empty/not-found 与 infrastructure failure 是否都应 `console.error`？生产环境需要什么 correlation/telemetry/redaction？
14. **Performance/a11y budgets**：385 kB First Load JS observation、eager mount、table scale、portal focus 与 screen-reader behavior 尚无阈值或自动回归。
15. **UI stage metadata drift**：页面 footer/stamp 仍显示 “Phase 10 · application shell” / “SHELL READY” / Phase 10；不影响 API contract，却会让已完成 Phase 11 的产品界面与实际阶段不一致。

## 9. Cross-links

- Technical Learning：[phase-11-frontend-features.md](../phase-11-frontend-features.md)
- Phase verification context：[Phase 11 Verification 与证据账本](../phase-11-frontend-features.md#74-phase-11-verification-与证据账本)
- Source contracts：[SPEC F002](../../SPEC.md#f002-file-upload) · [SPEC F014](../../SPEC.md#f014-conversation-memory) · [SPEC F016](../../SPEC.md#f016-file-management) · [SPEC F017](../../SPEC.md#f017-frontend)
- Task contracts：[T1101–T1105](../../TASKS.md#17-phase-11--frontend-features)
- Next verification scope：[T1201–T1204](../../TASKS.md#18-phase-12--integration--acceptance)
- Preceding frontend decisions：[Phase 10 Engineering Review](./phase-10-engineering-review.md)
- Project map：[DX-RAG Project Map](../project-map/dx-rag-project-map.md)
- Interview Guide：[Phase 11 深度章](../interview-notes/dx-rag-interview-guide.md#phase-11-learning-review)

> **Ownership boundary**：Technical Learning 解释代码、状态机与 mental model；本文件记录 ADR、failure modes、一致性、规模与 Known Gaps；Interview Guide 负责口语化答案。三者 cross-link，不复制完整分析。

## 10. Review closure

Phase 11 Engineering Review 完成并仅产生文档层变更；既有 Gate verdict `PHASE_11_PASS — READY_FOR_PHASE_12` 仍是独立 context，不由本文件重判。评审未修改 `SPEC.md`、`TASKS.md` 或 frontend application code，未启动 Phase 12，也未 commit/push。

收口结论：**Phase 11 已建立适合 v1 的 shared collection owner、feature-local state machines、identity reconciliation 与 last-intent-wins read guards；F-1 的结构性 stale-cache 问题已关闭。Upload→FileManager freshness、owner-switch late settlement、并行 mutation projection、runtime Error Boundary 与持续自动回归仍是明确 Known Gaps，其中跨 feature 文件生命周期应由 T1203 优先验证并按 bug-fix scope 收敛。**
