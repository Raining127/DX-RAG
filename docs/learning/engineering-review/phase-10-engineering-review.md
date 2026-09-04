# Phase 10 — Frontend Foundation Engineering Review

> **Coverage**：T1001 Centralized API Client & TypeScript Types；T1002 Root Layout、SideMenu 与 Main Page Shell
>
> **Status**：COMPLETE（2026-09-04）。本文件是 Layer 2 Engineering Review；不重发 Phase Gate verdict，不替代 Technical Learning、Phase Learning Review 或 Phase 11 feature acceptance。
>
> **Evidence vocabulary**：`STATIC/CODE-LEVEL` 表示源码、类型或契约对照；`BUILD` 表示真实 production build；`MOCKED` 表示以 stubbed `fetch` 验证 client-owned branches；`REAL BROWSER` 表示真实浏览器中的 UI interaction；`DEFERRED` 表示后续范围；`NOT_AVAILABLE` 表示当前没有 repository-owned 证据。

## 1. 当前工程结论

Phase 10 建立了两条相互独立的前端 seam：T1001 把 Backend HTTP contract 翻译为 typed domain calls，T1002 把四个业务区域组织为 controlled single-page shell。前者拥有 base URL、wire serialization、JSON/error parsing 和 endpoint functions；后者拥有 navigation identity、selected state、panel projection 与 responsive composition。

```text
Phase 11 Feature Component
    │
    ├── domain call / ApiError
    ▼
T1001 typed transport boundary
    │ fetch + HTTP/JSON
    ▼
FastAPI

User click
    ▼
T1002 SideMenu event → MenuKey → Home.selectedKey → PANELS[selectedKey]
    ▼
Feature slot
```

当前实现与 SPEC F017 §17.1–17.2、TASKS T1001–T1002 及 AC-F017-01/AC-FE-01 的 Phase 10 范围一致，本轮没有发现需要阻断工程文档收口的 defect。最重要的工程边界是：TypeScript generic 只能提供 compile-time contract，当前 success payload 仍是未经 runtime validation 的 JSON cast；同时真正的 loading/error/empty/success state、request cancellation、conversation lifecycle 和 destructive confirmation 都属于 Phase 11 feature owner，不能从 shell 的完成状态推断出来。

可准确对外表述为：**前端 transport 与 composition foundation 已实现，production build 和真实菜单交互已有证据；API client branches 只有 mocked-fetch probes，repository-owned frontend tests 与 browser-to-FastAPI E2E 尚未建立。**

## 2. 为什么需要这个模块

如果业务组件直接拼 URL、解析 error envelope、维护菜单 key，它们会同时承担 HTTP protocol、domain state 和 page composition 三种变化。Phase 10 先把变化轴分开：

- Backend contract 变化集中影响 `types.ts` 与 `api-client.ts`；
- menu/panel composition 变化集中影响 `SideMenu.tsx` 与 `page.tsx`；
- Feature Component 只在 Phase 11 拥有 view lifecycle 与业务交互。

这不是抽象层越多越好，而是让每类变化拥有可定位的 owner。当前只有九个 API functions 和四个 workspaces，原生 `fetch`、local `useState` 与一个 panel registry 足够表达冻结 v1 contract；Axios、Redux、Zustand、router 和 schema-generation pipeline 暂无规模证据支持。

## 3. 核心设计决策（ADR）

### ADR-01：使用集中式 endpoint client，Feature Components 不直接 `fetch`

- **Decision**：所有 backend calls 通过 `api-client.ts` 的 endpoint-specific functions；共享 `request<T>()` 处理 transport success/failure。
- **Context / Problem**：散落的 URL、headers、JSON parsing 和 error mapping 会让同一 backend contract 出现多个前端版本。
- **Why**：单一 owner 便于审计 endpoint coverage，也为 Phase 11 提供稳定、可替换的 dependency seam。
- **Trade-off**：模块会随 endpoints 增长；若所有 functions 与内部 helpers 永远同文件，未来可能形成宽 import surface。
- **Future**：按 domain 拆分 clients 时保留共享 transport core，不让 components 重新拥有 protocol details。

### ADR-02：使用原生 `fetch`，不引入 Axios/interceptor ecosystem

- **Decision**：v1 依赖浏览器/Next runtime 的 `fetch`、`RequestInit`、`FormData` 和 `Response`。
- **Why**：当前需求只有 JSON、multipart 和统一错误转换；减少依赖与第二套 error semantics。
- **Trade-off**：timeout、cancellation、retry、middleware、request tracing 需要自行设计；当前全部未实现。
- **Future**：是否换库应由 cancellation、observability、auth 或 cross-runtime needs 驱动，不由偏好驱动。

### ADR-03：Base URL 通过 public build-time environment 配置并去除尾斜杠

- **Decision**：读取 `NEXT_PUBLIC_API_BASE_URL`，缺失时回退 `http://localhost:8000/api`，再移除 trailing slashes。
- **Why**：避免每个 endpoint 重复环境分支与双斜杠；符合 SPEC 配置 owner。
- **Trade-off**：`NEXT_PUBLIC_*` 会进入 browser bundle，构建后不是 secret 或运行时动态配置；错误值通常到首次请求才暴露。
- **Future**：部署拓扑需要 runtime discovery、same-origin proxy 或多环境切换时，重新定义 config delivery 与 CORS owner。

### ADR-04：`request<T>` 统一三类失败，但 success payload 仅做 compile-time cast

- **Decision**：network reject → `NETWORK_ERROR/status 0`；非 2xx → backend envelope 或 `INVALID_RESPONSE`；2xx invalid JSON → `INVALID_RESPONSE`；有效 JSON 以 `T` 返回。
- **Why**：调用方只处理 `ApiError`，不重复判断 `fetch` resolve/reject 与 `response.ok`。
- **Trade-off**：`(await response.json()) as T` 不检查字段与类型；`204` 的 `undefined as T` 也依赖 caller 选择正确 generic，当前 endpoints 没有 204 contract。
- **Future**：backend/frontend 独立发布或 drift 风险上升时，在 transport boundary 引入 runtime schema validation 或 OpenAPI-generated client。

### ADR-05：Error payload 先作为 `unknown`，只验证必要 envelope

- **Decision**：`isRecord()`/`isErrorResponse()` 只证明 `error.code` 与 `error.message` 是 string；`details` 非 object 时规范化为 `{}`。
- **Why**：网络输入不能因 TypeScript annotation 自动可信；minimal guard 能保留 backend error semantics，同时容忍 details 缺失/畸形。
- **Trade-off**：guard 不验证完整 error catalog，也不保证 details 的 domain shape；未知 code 因 `(string & {})` 被有意接受，无法 exhaustive switch。
- **Future**：若 UI 对特定 details 字段有强依赖，应按 error code 建 discriminated runtime schemas，而非在组件中盲读。

### ADR-06：JSON 与 multipart serialization 分离

- **Decision**：JSON requests 明确 `Content-Type: application/json`；upload 使用 `FormData`，不手写 multipart header。
- **Why**：浏览器必须为 multipart 自动生成匹配 body 的 boundary；复用 JSON helper 会产生错误 wire format。
- **Trade-off**：通用 request wrapper 不能单靠 headers 推断 body contract；upload progress 也不能从当前 fetch wrapper直接获得。
- **Future**：Phase 11 若 SPEC 真正要求可观测上传进度，需要明确 Ant Design Upload/custom request 与 transport ownership，而不是假设普通 fetch 提供 progress event。

### ADR-07：URL path/query values 在 client boundary 编码

- **Decision**：collection name、file id 与 query values 使用 `encodeURIComponent`。
- **Why**：避免 resource values 破坏 path/query structure；wire encoding 由 client owner 统一。
- **Trade-off**：encoding 不是业务 validation，也不是 backend filesystem path safety；合法性仍由 Feature UI 与 Backend 各自按契约处理。
- **Future**：不要把 URL encoding 复用为 collection-name validator。

### ADR-08：菜单配置推导 closed `MenuKey`，panel registry 使用 exhaustive `Record`

- **Decision**：`MENU_ENTRIES as const` 推导 key union；`Record<MenuKey, PanelDefinition>` 强制每个合法 key 有 panel definition。
- **Why**：menu identity 只有一个事实源，新增 key 但漏 panel 会成为 compile-time error。
- **Trade-off**：Ant Design click event 的 key type 更宽，边界仍有 `key as MenuKey`；安全性依赖 items 只由受控 entries 生成。
- **Future**：若菜单来自 server/config，closed union 不再成立，需要 runtime validation 与 unknown-key fallback。

### ADR-09：`Home` 拥有唯一 selected state，`SideMenu` 保持 controlled

- **Decision**：`selectedKey` 只在 page owner 中维护，同时驱动 Menu `selectedKeys` 和 `PANELS[selectedKey]`。
- **Why**：避免 menu highlight 与 content 分别维护 state 形成 split-brain；当前规模不需要 global store。
- **Trade-off**：reload 不持久化、无法 deep-link，浏览器 back/forward 不表示 workspace transition。
- **Future**：只有产品明确要求 URL identity 或跨页面生命周期时才引入 App Router state；不能在不改 F017 的情况下擅自增加独立 routes。

### ADR-10：用 `key={selectedKey}` 重建 placeholder subtree

- **Decision**：workspace 切换时 React remount placeholder section，重新触发 entry animation。
- **Why**：当前 placeholder 无业务 state，remount 行为简单且视觉明确。
- **Trade-off**：Phase 11 放入表单、QA history 或 in-flight request 后，remount 会清除 local state/effects；这可能与用户预期冲突。
- **Future**：接入每个 Feature Component 前明确 state preservation policy，决定移除 key、提升 state、cache subtree 或有意 reset。

### ADR-11：保持 single-page state switching，不增加独立 URL routes

- **Decision**：菜单 click 只更新 React memory state，pathname 保持 `/`。
- **Why**：直接符合 F017 single-page/no-independent-route contract，并满足 AC-F017-01 的无刷新切换。
- **Trade-off**：不能分享具体 workspace URL，也没有 route-level code splitting、history navigation 或 refresh recovery。
- **Future**：deep-link 是产品 contract change，不是纯 implementation refactor。

### ADR-12：Ant Design provider 位于 RootLayout，整个 shell 使用 client interactivity

- **Decision**：RootLayout 标记 `'use client'` 并直接提供 locale/theme；page/SideMenu 也为 Client Components。
- **Why**：当前 shell 所有交互和 Ant Design config wiring 简单集中，中文 locale 与 tokens 全局一致。
- **Trade-off**：root file 不能同时承担典型 server-only metadata/export patterns，client/provider boundary 较高；当前 `/` First Load JS 为 179 kB，但没有 baseline 或 budget，不能据此单独判定 regression。
- **Future**：若 bundle、SSR、metadata 或 hydration metrics 出现要求，将 ConfigProvider 下沉到最小 client provider；先测量再拆分。

### ADR-13：Responsive behavior 由 Ant Design breakpoint 与 CSS media queries 协作

- **Decision**：Sider 在 `lg` breakpoint 变为 zero-width，CSS 在 991px/640px 调整 fixed rail、content padding 与 single-column layout。
- **Why**：组件负责 collapse mechanics，CSS 负责品牌化版式和细节 reflow。
- **Trade-off**：breakpoint 存在两个 owner；Ant Design token/default 变化可能与 991px media query 漂移。
- **Future**：建立 viewport regression matrix或共享 breakpoint contract，避免只靠人工观察。

### ADR-14：Feature view state 明确保留给 Phase 11

- **Decision**：Phase 10 只提供四个 placeholder slots，不提前实现 loading/success/empty/error、QA history 或 destructive confirmation。
- **Why**：这些状态依赖具体 API call、用户动作和业务 recovery；塞入 shell 会让 composition owner 侵入 feature owner。
- **Trade-off**：shell“可点击”不等于应用业务可用；当前不能验收 AC-F017-02～04/AC-FE-02～05。
- **Future**：Phase 11 每个组件必须通过 T1001 client 接入，并独立定义 race、retry、unmount/cancellation 与 state preservation。

## 4. 架构影响

### 4.1 依赖方向

```text
app/layout.tsx ──→ Ant Design ConfigProvider / locale / theme
app/page.tsx   ──→ SideMenu + local selected state + panel registry
SideMenu.tsx   ──→ Ant Design Menu event boundary

Phase 11 Components ──→ lib/api-client.ts ──→ browser fetch ──→ FastAPI
                         └── lib/types.ts
```

`api-client.ts` 不依赖 React，保持 transport seam 可在组件外测试；shell 当前不调用 backend，保持 composition evidence 与 integration evidence 分离。

### 4.2 Contract owners

| Contract | Owner | 不应泄漏给谁 |
|---|---|---|
| endpoint URL/method/body | API client | Feature Components |
| backend error envelope | API client / `ApiError` | Ant Design view controls |
| loading/empty/error/success | Phase 11 component | API client / App Shell |
| menu identity/selection | page + controlled SideMenu | individual feature components |
| response runtime validity | 当前仅 JSON parsing；future transport validator | 不能假定由 TS interface 保证 |
| history/file/form lifecycle | Phase 11 component | placeholder remount side effect |

### 4.3 没有改变的边界

Phase 10 没有实现业务组件、auth headers、retry、timeout、cancellation、upload validation/progress、QA history、Markdown/sources、file delete confirmation、routing、dark mode 或 global store。它也不证明 CORS、deployed base URL、backend compatibility 或真实 API latency。

## 5. 工程问题分析

### 5.1 可维护性

Endpoint-specific functions 可读且可搜索，snake_case translation 集中，适合当前规模。潜在 drift 面有三处：TypeScript interfaces 手工镜像 Pydantic；error code union 手工维护；endpoint functions 与 SPEC paths 手工同步。现在尚无 OpenAPI generation/check pipeline，变更必须同时 review backend schema 与 frontend client。

`Collection`/`CollectionItem`、`Source`/`SourceObject`、`PreviewResponse`/`FilePreviewResponse` aliases 提供命名兼容，但也可能让消费者不清楚 canonical name。当前不构成行为 defect；后续应在新组件中选择一个 canonical vocabulary，避免 alias 继续扩散。

### 5.2 一致性与数据语义

1. Optional values 只有在 `!== undefined` 时进入 payload；空字符串仍会被显式发送，由 backend validation 决定语义。
2. Error `details` 缺失或非 object 时变 `{}`，保证 consumer shape，但会丢弃 malformed backend diagnostic。
3. `ApiError.status=0` 是“没有 HTTP response”的 client convention，不是合法 HTTP status；UI 不应直接把它展示为服务器状态码。
4. Success generic 不做 runtime shape check，因此 deployed backend drift 可穿过 client，直到组件读取字段时才暴露。
5. `selectedKey` 是唯一 composition state；panel 是 derived value，不存在第二份 active-panel state。
6. Shell section 使用 key remount；未来 feature state 的“切换后保留还是清空”尚未由 Phase 10 定义。

### 5.3 Failure taxonomy

| Failure / state | 当前行为 | 当前证据 | 工程判断 |
|---|---|---|---|
| fetch reject / backend unreachable | `ApiError(NETWORK_ERROR, status=0)` | `MOCKED` probe | transport distinction 明确 |
| non-2xx + valid envelope | 保留 backend code/message/details/status | `MOCKED` probe | UI mapping 仍由 Phase 11 owner |
| non-2xx + invalid/non-JSON envelope | `INVALID_RESPONSE` + HTTP status | `MOCKED` probe | 不泄漏 raw body；diagnostic 较少 |
| 2xx + invalid JSON syntax | `INVALID_RESPONSE` | `MOCKED` probe | parse failure 已归一化 |
| 2xx + valid JSON but wrong shape | 作为 `T` resolve | `STATIC`; behavioral test `NOT_AVAILABLE` | 最大 contract-drift gap |
| unexpected 204 | `undefined as T` | `STATIC`; current endpoint `NOT_APPLICABLE` | generic API 可被误用 |
| wrong public base URL | 请求失败或命中错误服务 | `STATIC`; deployed test `NOT_AVAILABLE` | build-time config 缺少 fail-fast |
| hung/slow request | 无 timeout/cancellation | `NOT_AVAILABLE` | 页面切换后可能出现 stale completion |
| unknown Ant Menu key | cast 为 `MenuKey` 后索引可能为 undefined | `STATIC`; current items closed | 当前生成路径安全，动态 menu 会破坏假设 |
| workspace switch | section remount | `REAL BROWSER` for placeholder | Phase 11 local state/effect behavior 未验证 |
| narrow viewport | Sider zero-width、trigger 与 CSS reflow | `REAL BROWSER` two viewports | 非全浏览器/设备 matrix |
| runtime render/interaction warning | Gate 浏览器检查为 0 | `REAL BROWSER` scoped session | 长时间/未来组件不在证据范围 |

### 5.4 性能与可用性

- 当前 `/` production output 为 62.3 kB route、179 kB First Load JS；这是一次 build observation，不是性能 budget 或 regression conclusion。
- Root-level Ant Design provider、page 与 menu 均在 client side；当前 shell 很小，但 Phase 11 若直接把所有 feature modules 静态 import 到一个 page，single-route bundle 和 hydration work 可能继续增长。
- 无 request cancellation/deduplication/cache；Phase 11 的快速切换、重复提交或慢响应可能产生 stale response race。
- panel registry 是 O(1) lookup，menu 只有四项；在当前范围内没有算法压力。
- animation 遵守 `prefers-reduced-motion`，但尚无 automated accessibility、keyboard/focus 或 screen-reader regression evidence。

### 5.5 安全、隐私与部署

- `NEXT_PUBLIC_API_BASE_URL` 必然公开，不得放 secret；API keys 仍必须只在 backend。
- client logging 只输出 code/status，符合不记录 payload 的方向；`ApiError.details` 可能包含 network cause message，未来 UI/telemetry 不应无审查上传或展示完整 details。
- v1 无 auth，client 也不发送 credentials/auth headers；这符合 scope，不代表部署在不可信网络上安全。
- URL encoding 防止结构破坏，但不代替 backend validation、authorization 或 filesystem safety。
- CORS/same-origin、TLS、CSP、dependency vulnerability 与 production environment injection 本轮均未验证。

## 6. 规模扩大分析（Future / Not implemented in v1）

| 规模/变化 | 当前可推断行为 | 主要压力点 | 后续证据/决策 |
|---|---|---|---|
| 10x endpoints | 单文件 client/types 继续增长 | schema/error/path drift | domain clients、OpenAPI diff/generation、contract tests |
| Backend/frontend 独立发布 | success payload blind cast | rolling-version incompatibility | runtime schemas、compatibility policy |
| 4 → 20 workspaces | Record 仍 exhaustive | single page bundle、menu discoverability | lazy loading、information architecture、bundle budget |
| stateful Phase 11 panels | key remount 清除 subtree | form/history/in-flight state loss | preservation policy、component tests |
| 10x concurrent requests | 每次独立 fetch，无 cancellation/dedupe | stale response、duplicate mutation | AbortController、request identity、mutation guards |
| multi-environment deploy | public URL 在 build time 固化 | wrong target、CORS、promotion mismatch | config validation、same-origin proxy/runtime config |
| accessibility requirements | semantic nav/aria-live已有基础 | focus restore、keyboard、announcement noise | axe/component/browser AT matrix |
| performance budget | current First Load JS 179 kB observation | Ant Design/client boundary/features growth | baseline、bundle analyzer、Web Vitals/load tests |

没有真实 metrics 时，不把 client component、Ant Design 或 179 kB 自动写成性能问题；它们是需要 measurement 的 pressure points。

## 7. Verification Review

本轮在当前 checkout 独立执行：

```text
cd frontend
npm ls --depth=0
→ dependency tree resolved；Next 14.2.24 / Ant Design 5.22.7 /
  React 18.3.1 / TypeScript 5.9.3 等

npm run build（workspace sandbox）
→ spawn EPERM（Next worker 创建被环境阻止，不作为代码失败）

npm run build（授权后同一命令）
→ PASS：compiled、lint/type check、4/4 static page generation
→ / route 62.3 kB；First Load JS 179 kB（observation only）

git diff --check
→ PASS（无 whitespace error）
```

结合刚完成的独立 Phase 10 Gate evidence：

- **`BUILD`**：production compile、lint/type check 和 static generation 真实通过；不执行用户 interaction 或 backend calls。
- **`MOCKED`**：T1001 inline stubbed-fetch probes 5/5 PASS，覆盖 base URL、success JSON、valid/malformed error、network failure 与 invalid JSON 等 client-owned branches；不是 repository-owned regression suite。
- **`REAL BROWSER`**：四菜单切换 4/4、pathname 保持 `/`；640px 与约 360px 无水平溢出；scoped console check 为 0 error/warning。
- **`STATIC/CODE-LEVEL`**：endpoint coverage、Pydantic/TS fields、multipart header ownership、literal-derived keys 与 `Record` exhaustiveness 可由源码确认。
- **`DEFERRED / NOT_AVAILABLE`**：browser-to-FastAPI、real CORS/base URL、success runtime shape validation、multipart upload、Phase 11 feature states、request races、automated accessibility/component/E2E suite 均无当前完整证据。

当前没有 `test` script，也没有 Vitest/Jest/Playwright/Cypress repository-owned tests。Gate probes 与人工 browser checks 是有效但不可持续自动回归的证据，不能描述成“frontend test suite”。

## 8. Known Gaps & Pending Questions

1. **Success runtime validation**：合法 JSON 但错误 shape 会穿过 `request<T>`；需要决定 schema validator 或 generated client 的升级阈值。
2. **Repository-owned tests**：client branches、menu state、responsive、accessibility 均无持续 regression suite。
3. **Request lifecycle**：无 timeout、AbortController、dedupe 或 stale-response protection；Phase 11 必须定义 unmount/switch behavior。
4. **State preservation**：`key={selectedKey}` 会 remount；QA history、表单草稿和 mutation progress 的保留/清除 policy 未冻结。
5. **Root client boundary**：RootLayout 直接 client 化简化 provider wiring，但 metadata/server boundary 与 bundle trade-off 尚无测量。
6. **Schema drift**：Pydantic、TS interfaces、error codes 和 endpoint paths 依赖人工同步，无 CI contract-diff check。
7. **Upload progress ownership**：普通 fetch wrapper 没有 upload progress callback；Phase 11 不能只引用“Ant Design 内置”就忽略 custom request semantics。
8. **Responsive dual ownership**：Ant `lg` 与 CSS 991px/640px 分别控制 behavior/layout，版本或 token 变化可能漂移。
9. **Accessibility depth**：已有 nav label、aria-live、reduced motion，但 focus management、keyboard 与 screen-reader behavior 未自动验证。
10. **Deployment integration**：CORS、TLS、same-origin proxy、public env injection、backend version compatibility 尚未验证。
11. **Security boundary**：无 auth 是 v1 scope；不能把 client types、URL encoding 或 trusted-network 文案表述为 access control。
12. **Bundle/performance budget**：有一次 179 kB observation，无 baseline、threshold、Web Vitals 或低端设备 evidence。

这些项目属于 Phase 11/12 或新的 engineering decision；本 review 不通过修改冻结 F017、增加依赖或重构代码来“顺手解决”。

## 9. Cross-links

- Technical Learning：[phase-10-frontend-foundation.md](../phase-10-frontend-foundation.md)
- Phase Gate / Learning Review context：[Verification Ledger](../phase-10-frontend-foundation.md#verification-ledgert1001t1002--phase-10-gate)
- Source contract：[SPEC F017](../../SPEC.md#f017-frontend) · [SPEC Section 12.5](../../SPEC.md#125-frontend-f017)
- Task contract：[T1001](../../TASKS.md#t1001--centralized-api-client--typescript-types) · [T1002](../../TASKS.md#t1002--root-layout-sidemenu--main-page-shell)
- Upstream API review：[phase-09-engineering-review.md](./phase-09-engineering-review.md)
- Project map：[dx-rag-project-map.md](../project-map/dx-rag-project-map.md)
- Interview Guide：[Phase 10 深度章](../interview-notes/dx-rag-interview-guide.md#phase-10-深度章--frontend-foundationt1001t1002-已实现--gate--learning-review-完成)

> **Ownership boundary**：Technical Learning 解释代码与 mental model；本文件记录 ADR、failure modes、一致性、规模与 Known Gaps；Interview Guide 负责口语化答案。三者 cross-link，不复制完整分析。

## 10. Review closure

Phase 10 Engineering Review 完成并仅产生文档层变更；既有 Gate verdict `PHASE_10_PASS — READY_FOR_PHASE_11` 仍是独立 context，不由本文件重判。评审未修改 `SPEC.md`、`TASKS.md` 或 frontend application code，未启动 Phase 11，也未 commit/push。

收口结论：**typed API client 与 controlled shell 已形成清晰的 transport/composition boundary；production build 与 scoped browser behavior 有真实证据。成功 payload runtime validity、业务组件状态、request lifecycle、持续自动回归和 browser-to-FastAPI integration 继续保持 `DEFERRED`，不得描述为已解决。**
