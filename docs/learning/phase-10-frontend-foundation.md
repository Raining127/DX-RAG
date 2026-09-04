# Phase 10 — Frontend Foundation

> **Phase 状态**: COMPLETE（T1001、T1002 DONE；`PHASE_10_PASS — READY_FOR_PHASE_11`）  
> **本文档状态**: T1001、T1002 Learning Pass + Phase Learning Review 完成（2026-09-04）  
> **配套文档**: [Phase 10 Engineering Review](./engineering-review/phase-10-engineering-review.md) · [Interview Guide 的 Phase 10 深度章](./interview-notes/dx-rag-interview-guide.md#phase-10-深度章--frontend-foundationt1001t1002-已实现--gate--learning-review-完成) · [Learning Pass Workflow](./templates/phase-learning-pass-workflow.md)

---

## 1. Phase 学习（本章学什么、怎么学）

- **一句话定位**：Phase 10 在稳定的 FastAPI HTTP contract 与未来 React Feature Components 之间建立前端基础层；T1001 建立 typed API boundary，T1002 建立不依赖 URL routing 的 application shell 与 navigation state。
- **核心学习点**：
  - 🟢 TypeScript type contract 与 Python/Pydantic schema 的对应关系，以及二者都不能自动保证跨网络数据正确。
  - 🟢 用一个 generic `request<T>()` 统一 transport、JSON parsing 与 error normalization，让组件只处理业务状态。
  - 🟡 `fetch` 的三类失败：网络失败、HTTP 非 2xx、HTTP 成功但响应不是合法 JSON。
  - 🟡 JSON request、`multipart/form-data` upload、path parameter、query parameter 的不同编码责任。
  - 🟢 React controlled component：`page.tsx` 拥有 `selectedKey`，`SideMenu` 只接收 value 与 callback。
  - 🟢 用 literal data source 推导 `MenuKey`，让菜单配置、state 与 panel mapping 保持 compile-time 对齐。
  - 🟡 Next.js Server/Client Component boundary：使用 `useState` 和浏览器交互的文件必须声明 `'use client'`。
  - 🟡 Ant Design `ConfigProvider`、`Layout/Sider/Menu` 的全局主题、结构与响应式职责。
  - 🔵 Next.js 的 `NEXT_PUBLIC_*` 环境变量属于 browser-visible build-time configuration。
- **前置依赖**：Phase 4–9 已冻结并实现 Section 6 后端 endpoints；T1001 不重新定义 contract，而是消费它们。
- **学习建议**：先读 `types.ts → api-client.ts` 理解 I/O boundary，再读 `SideMenu.tsx → page.tsx → layout.tsx → globals.css`，追踪一次 menu click 怎样只改变 React state，最后在窄屏观察 Sider breakpoint。

### 先建立一个 mental model

可以把 T1001 看成前端的 **Anti-Corruption Layer（防腐层）**：

```text
React component
  只表达业务意图：queryQA(...) / uploadFile(...) / deleteFile(...)
        ↓
endpoint wrapper
  把 camelCase 函数参数翻译为 HTTP method + path/query + snake_case body
        ↓
request<T>()
  统一执行 fetch、识别失败、解析 JSON
        ↓
FastAPI Section 6 contract
```

它没有管理 React `loading/success/empty/error` state。根据 SPEC F017 §17.2，这些仍由每个 Feature Component 自己负责。

T1002 在它上面再加一层 **UI composition boundary**：

```text
RootLayout
  → ConfigProvider：全局 locale/theme
  → Home：拥有 selectedKey
      ├─ SideMenu：显示选中项并上报 click
      └─ PANELS[selectedKey]：选择当前 placeholder content
```

这里没有 route transition、API request 或业务组件 mount。它先冻结稳定的页面骨架，Phase 11 再把 placeholder 逐个替换为真实 Feature Components。

### Phase Learning Review：两个边界、三类契约、一条交互链

Task-by-Task 阅读时，T1001 像“请求工具”，T1002 像“页面外壳”。Phase-level 视角要再向上抽象一层：Phase 10 建立的是 **Frontend Foundation Boundary**，把未来业务组件夹在两个稳定边界之间。

```text
                     UI composition boundary（T1002）
User event ──→ SideMenu ──→ selectedKey ──→ Feature slot
                                               │
                                               │ Phase 11 component
                                               ▼
component state ──→ endpoint function ──→ request<T>() ──→ FastAPI
                     HTTP contract boundary（T1001）
```

这条完整链包含三类契约：

| 契约 | 代表类型/状态 | Owner | 防止的问题 |
|---|---|---|---|
| **Domain data contract** | `QueryRequest`、`FileRecord`、`ErrorResponse` | `types.ts` + backend Section 6 | 前后端字段、可选性、literal value 漂移 |
| **Transport contract** | method、path/query、JSON/FormData、`ApiError` | `api-client.ts` | 组件重复拼协议、错误分支不一致 |
| **Composition contract** | `MenuKey`、`selectedKey`、`PANELS`、feature slot | `SideMenu.tsx` + `page.tsx` | 菜单选择与内容区域 split state、漏配 panel |

Phase 10 最值得迁移的三个原则是：

1. **Boundary owns translation**：camelCase → snake_case、domain error envelope → `ApiError`、library menu key → project `MenuKey`，都在边界处翻译，不把协议细节泄漏给下游。
2. **One state, derived projections**：`selectedKey` 是唯一 navigation state，左侧 selection 和右侧 panel 都从它派生；`panel` 不应成为第二份 state。
3. **Static guarantees stop at runtime input**：TypeScript 能保证项目内部调用与 mapping 完整，却不能证明服务器返回的 JSON 一定符合 `T`。静态保证和运行时信任边界必须分开陈述。

**Phase-level Mental Model**：Phase 10 是一块“双插座底板”——上方插 UI 功能模块，下方插后端 HTTP API。T1002 决定模块放在哪里、怎样切换；T1001 决定模块怎样与后端通信。Phase 11 应填充插槽，而不是绕过底板重新发明 navigation 或 raw `fetch`。

---

## 2. Phase 目标（为什么做这个 Phase）

### 2.1 业务目标

F017 要交付一个 Next.js 14 + Ant Design 5 的单页 Web 应用。用户最终会在 UI 中管理知识库、上传文件、进行知识问答和管理文件。T1001 本身不渲染 UI；它先为这些功能提供统一的后端访问入口。

### 2.2 技术目标

T1001 要兑现四项 client responsibility（SPEC F017 §17.2）：

1. 统一 Backend Base URL；
2. 统一 request/response handling；
3. 统一解析 Section 6.7 error envelope；
4. 为请求与响应提供 TypeScript type safety。

当前实现分别落在：

- `frontend/lib/types.ts:9-165`：API data shapes；
- `frontend/lib/api-client.ts:19-24`：base URL；
- `frontend/lib/api-client.ts:26-106`：typed error 与错误解析；
- `frontend/lib/api-client.ts:108-148`：共享 request pipeline；
- `frontend/lib/api-client.ts:162-252`：每个 Section 6 endpoint 的业务函数。

T1002 再兑现 application-shell contract：

- `frontend/app/layout.tsx:1-49`：全局 Ant Design locale/theme provider；
- `frontend/components/SideMenu.tsx:1-49`：四项 controlled navigation；
- `frontend/app/page.tsx:1-139`：single-page shell、navigation state 与 placeholder composition；
- `frontend/app/globals.css:7-446`：design tokens、desktop shell、responsive breakpoint 与 reduced-motion fallback。

### 2.3 明确不做什么

根据 TASKS T1001：

- 不实现 React components；
- 不在 browser client 加 retry；后端 LLM retry 是另一层责任；
- 不添加 auth headers，因为 v1 没有 authentication；
- 不引入 Redux/Zustand；
- 不把不同成功响应强塞进 universal success wrapper。
- 不实现 T1101–T1105 的真实业务组件；
- 不引入 React Router 或独立 URL routes；
- 不添加 dark-mode toggle；
- 不让 SideMenu 私自拥有第二份 selected state。

### 2.4 权威来源

- **[SPEC REQUIREMENT]** F017 §17.1–17.2：Frontend architecture 与 centralized API client；
- **[SPEC REQUIREMENT]** Section 6.1–6.7：全部 HTTP contracts 与 unified error response；
- **[SPEC REQUIREMENT]** §8.2：`NEXT_PUBLIC_API_BASE_URL`；
- **[TASK CONTRACT]** T1001、T1002：实现范围、验收项与 out-of-scope。

---

## 3. 项目位置（这个 Phase 在系统地图的哪里）

- **所属层**：Frontend integration boundary；位于 React UI 与 FastAPI API Layer 之间。
- **上游依赖**：后端 `/api/health`、`/api/upload`、`/api/query`、`/api/collections`、`/api/files` 的稳定 contracts。
- **下游消费者**：T1101 KnowledgeBaseManager、T1102 FileUpload、T1103 QAPanel、T1104 FileManager；它们将进入 T1002 预留的四个 content slots，T1105 再审查跨组件 state pattern。
- **数据流角色**：它不拥有业务数据，也不持久化 state；它只完成 in-memory values 与 HTTP representation 之间的转换。

```text
UI event
  → endpoint function parameters
  → RequestInit / FormData / encoded URL
  → fetch
  → Response
  → typed success value OR ApiError
  → component-owned UI state
```

这条边界很重要：API client 负责“请求怎么发、错误长什么样”，组件负责“loading spinner、empty view、retry button 怎么显示”。

T1002 的 shell 负责“当前显示哪个功能区域”，但不拥有每个功能内部的 data-fetching state。这避免把 navigation state、domain state 与 transport state 混成一个巨型对象。

---

## 4. Task 学习

### T1001 — Centralized API Client & TypeScript Types

- **Task 目标**：实现覆盖全部 backend API contracts 的集中式 client 与 TypeScript type definitions。
- **实现摘要**：
  - `frontend/lib/types.ts:9-121` 定义 collection、upload、query、source、file 与 health contracts；
  - `frontend/lib/types.ts:123-165` 定义可扩展的 API error types；
  - `frontend/lib/api-client.ts:19-24` 读取并规范化 base URL；
  - `frontend/lib/api-client.ts:26-148` 建立统一 error/request pipeline；
  - `frontend/lib/api-client.ts:162-252` 提供 10 个 endpoint functions，覆盖 SPEC Section 6。
- **新知识**：
  - 🟢 TypeScript 的 `interface` 是 compile-time contract；Pydantic `BaseModel` 除了 schema，还会在 Python runtime validation/serialization 中参与工作。
  - 🟢 `Promise<T>` 描述调用成功后的静态类型，而 `throw ApiError` 描述失败 control flow；TypeScript 没有 Java 风格 checked exceptions，因此调用方要通过 `try/catch` 和 `instanceof ApiError` 收窄。
  - 🟡 `unknown` + type guard 比直接使用 `any` 更安全：必须先证明 shape，才能读取字段。
  - 🟡 URL path/query values 使用 `encodeURIComponent`；JSON 使用 `JSON.stringify`；文件上传交给 `FormData`。三者不可混用。
- **TS/前端类比**：这很像把多个 React components 中散落的 `fetch()` 抽到一个 typed SDK。组件调用 declarative function，不重复拼 URL、method、headers 和 error branches。
- **验证**：
  - **REAL / STATIC BUILD**：2026-09-04 在 `frontend` 执行 `npm run build`，Next.js production build、lint 和 type checking 通过；证明当前代码能被项目 TypeScript configuration 编译。
  - **STATIC CONTRACT REVIEW**：逐项对照 SPEC Section 6、`backend/app/models/schemas.py` 和 `backend/app/core/errors.py`，endpoint/method/shape 一致。
  - **NOT AVAILABLE**：仓库当前没有 T1001 focused unit tests；没有用 stubbed `fetch` 自动验证各 error branch。
  - **DEFERRED**：没有启动真实 FastAPI + browser 执行 frontend-to-backend E2E，因此不能声称 runtime integration 已通过。
- **Interview Candidates**：
  - **Technical Points**：generic request core、typed endpoint facade、`unknown` narrowing、transport/application error normalization。
  - **Engineering Questions**：为什么 compile-time `T` 仍不能保证 server JSON runtime shape？为什么 upload 不能手写 multipart `Content-Type`？
  - **Candidate Interview Questions**：你怎样设计前端 API layer，使 React component 不依赖 backend error envelope 细节？
  - **STAR Candidate**：无；这是正常 foundation task，没有真实 incident，不虚构闭环故事。

#### T1001 补充：TypeScript types 怎样映射 Pydantic

| 后端 Pydantic | 前端 TypeScript | 关键语义 |
|---|---|---|
| `CollectionItem` | `Collection` / alias `CollectionItem` | 相同 JSON shape，不必复制两套 interface |
| `Literal["SUCCESS", "SUCCESS_WITH_WARNINGS"]` | string literal union `IngestionStatus` | 排除 HTTP 200 中不存在的 `FAILED` |
| `List[UploadWarning]` | `UploadWarning[]` | JSON array 的元素 shape 固定 |
| `Optional`/defaulted request fields | optional property `?` | 前端可省略，让后端应用 default |
| Python `float` / `int` | TypeScript `number` | JSON/JS 不区分整数与浮点类型 |
| `Dict[str, Any]` | `{ [key: string]: unknown }` | details 可扩展，但读取前必须 narrow |

这里有一个不能忽略的差异：Pydantic model 能在运行时验证输入；TypeScript types 被编译后会擦除（type erasure）。所以 `return (await response.json()) as T` 是对编译器的承诺，不是 runtime validation。

### T1002 — Root Layout, SideMenu & Main Page Shell

- **Task 目标**：建立由 Ant Design `ConfigProvider` 包裹的 single-page shell，用左侧菜单和 React state 切换四个 placeholder content areas。
- **实现摘要**：
  - `frontend/app/layout.tsx:1-49` 将 `zh_CN` locale 与共享 design tokens 提供给整个 app；
  - `frontend/components/SideMenu.tsx:6-18` 用一个 `as const` 数据源推导合法 `MenuKey`，并定义 controlled props；
  - `frontend/components/SideMenu.tsx:20-49` 把配置映射为 Ant Design items，将 click 回传给 parent；
  - `frontend/app/page.tsx:17-46` 用 `Record<MenuKey, PanelDefinition>` 保证四个 menu key 都有 panel definition；
  - `frontend/app/page.tsx:48-139` 由 `selectedKey` 驱动 Sider selection 与 content rendering；
  - `frontend/app/globals.css:7-446` 定义 shell styling、`lg` 以下的 fixed Sider，以及 640px 以下的 content reflow。
- **新知识**：
  - 🟢 **Single source of truth**：`selectedKey` 只存在于 `Home`，child menu 通过 props 读取并通过 callback 请求更新。
  - 🟢 **Derived union type**：`(typeof MENU_ENTRIES)[number]['key']` 从 runtime constant 推导 compile-time union，避免手写两份可能漂移的 key list。
  - 🟢 **Exhaustive mapping**：`Record<MenuKey, PanelDefinition>` 要求每个合法 key 都有 content；新增菜单却漏加 panel 会在编译期报错。
  - 🟡 **Client boundary**：`page.tsx` 因 `useState` 必须是 Client Component；`SideMenu.tsx` 因 event handler 也必须是 Client Component。
  - 🟡 **Controlled Menu**：`selectedKeys={[selectedKey]}` 由 parent state 决定视觉选择，不依赖 Menu 内部隐式 state。
  - 🟡 **Responsive Sider**：`breakpoint="lg"` + `collapsedWidth={0}` 把窄屏 navigation 收起为 zero-width trigger；CSS 再调整 position、padding 与 panel grid。
- **TS/React 类比**：这与 controlled `<input value={value} onChange={...}>` 完全同构。SideMenu 不决定当前 value，只把 event 翻译为 `MenuKey` 并交回 owner。
- **验证**：
  - **REAL / STATIC BUILD**：2026-09-04 执行 `npm run build`，production compile、lint、type checking 与 static page generation 全部通过。
  - **REAL / BROWSER INTERACTION**：在 `http://localhost:3000/` 依次点击知识库管理、文件上传、知识问答、文件管理，heading、description、placeholder 和 sequence 均切换，URL 始终为 `/`。
  - **REAL / RESPONSIVE BROWSER CHECK**：viewport 设为 640×900 时，Sider 进入 `ant-layout-sider-collapsed`、`ant-layout-sider-below`、`ant-layout-sider-zero-width`，computed width 约 0，zero-width trigger 存在；测试后已重置 viewport override。
  - **REAL / CONSOLE CHECK**：页面加载与四项菜单交互后，captured browser console error/warning 列表为空。
  - **STATIC CONTRACT REVIEW**：代码未导入 router，content 由 `useState<MenuKey>` 与 `PANELS[selectedKey]` 选择；符合 F017 §17.1 与 AC-F017-01。
  - **NOT AVAILABLE**：仓库没有 T1002 component test 或 Playwright/Cypress regression suite。
  - **DEFERRED**：T1101–T1105 真实组件及其 loading/success/empty/error behavior 尚未实现；placeholder 不能替代这些验收。
- **Interview Candidates**：
  - **Technical Points**：controlled navigation、literal-derived union、exhaustive `Record` mapping、Client Component boundary、responsive Sider。
  - **Engineering Questions**：为什么 navigation state 放在 parent？何时 single-page state switching 应升级为 URL routing？
  - **Candidate Interview Questions**：如何用 TypeScript 让 menu configuration 与 content registry 不发生 key drift？
  - **STAR Candidate**：无；这是正常 UI foundation task，没有 production-like incident。

---

## 5. 代码理解（关键代码精读）

### 精读 1：Base URL configuration（`frontend/lib/api-client.ts:19-24`）

```ts
const DEFAULT_API_BASE_URL = "http://localhost:8000/api";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/+$/, "");
```

- default value 让本地开发无需额外配置即可连接 FastAPI；
- `NEXT_PUBLIC_` 表示变量可以进入 browser bundle，因此这里不能存 secret；
- `||` 在变量缺失或为空字符串时回退默认值；
- `.replace(/\/+$/, "")` 移除一个或多个结尾 slash，避免后续 `${API_BASE_URL}/query` 形成 `//query`；
- `/api` 已属于 base URL，endpoint wrapper 只追加 `/query`、`/files` 等 path。

### 精读 2：`ApiError` 与 defensive parsing（`frontend/lib/api-client.ts:26-106`）

```ts
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ErrorDetails;
  readonly response: ErrorResponse;

  constructor(message: string, options: { status: number; code: string; details?: ErrorDetails }) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code;
    this.details = options.details || {};
    this.response = { error: { code: this.code, message: this.message, details: this.details } };
  }
}
```

- 继承原生 `Error`，所以既能保留 stack/message 语义，也能携带 HTTP/domain metadata；
- `readonly` 防止 catch 之后意外改变 error identity；
- `details` 缺失时规范化为 `{}`，下游组件不用反复判断 `undefined`；
- `response` 重建 Section 6.7 envelope，便于需要完整结构的消费者使用。

错误 JSON 先以 `unknown` 接收，再由 `isRecord()` 与 `isErrorResponse()` 做最小 shape check。只有 `error.code` 和 `error.message` 被证明是 string，payload 才按 backend error 处理；`details` 不是 object 时降级成 `{}`。

这是一种 **parse, then narrow** 思路。但当前 guard 只验证错误响应的必要字段，不是完整 schema validator。

### 精读 3：共享 `request<T>()`（`frontend/lib/api-client.ts:108-148`）

```ts
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (cause) {
    throw new ApiError("Unable to connect to the backend service", {
      status: 0,
      code: "NETWORK_ERROR",
      details: cause instanceof Error ? { cause: cause.message } : {},
    });
  }

  if (!response.ok) {
    return parseErrorResponse(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
```

逐段看 control flow：

1. `fetch` reject 表示 request 没拿到正常 HTTP response，例如连接失败；它被归一化为 `NETWORK_ERROR`，并用 `status: 0` 表示“没有 HTTP status”。
2. `fetch` 对 404/500 不会自动 reject，所以必须显式检查 `response.ok`。
3. 非 2xx 交给 `parseErrorResponse()`：合法 Section 6.7 payload 保留 backend code/message/details；坏 JSON 或错误 shape 变成 `INVALID_RESPONSE`。
4. 204 没有 body，避免调用 `response.json()`；当前 Section 6 endpoints 没有 204，这是一条 defensive generic-client branch。
5. 成功响应若不是合法 JSON，也转成 `INVALID_RESPONSE`。
6. `as T` 只影响 static type。若服务端成功响应偷偷缺字段，当前 client 不会自动发现。

### 精读 4：为什么 upload 单独使用 `FormData`（`frontend/lib/api-client.ts:186-200`）

```ts
const formData = new FormData();
formData.append("file", file);
if (collectionName !== undefined) {
  formData.append("collection_name", collectionName);
}

return request<UploadResponse>("/upload", {
  method: "POST",
  body: formData,
});
```

- upload contract 是 `multipart/form-data`，不是 JSON；
- 不手动设置 `Content-Type`，因为 browser 必须自动补上与 body 一致的 multipart boundary；
- `collectionName` 未提供时不发送字段，让 backend 使用 frozen default；空字符串则会作为显式值发送，这与 `undefined` 不同；
- 仍复用同一个 `request<T>()`，所以成功/失败 semantics 不分叉。

### 精读 5：endpoint wrapper 是 protocol adapter（`frontend/lib/api-client.ts:202-247`）

`queryQA()` 把易于组件调用的 camelCase arguments 转成 backend 所需的 snake_case JSON：`collectionName → collection_name`、`topK → top_k`。可选字段只在不为 `undefined` 时加入，保留 server defaults。

文件 APIs 同时编码两类用户输入：

- `fileId` 进入 path segment，使用 `encodeURIComponent(fileId)`；
- `collectionName` 进入 query value，也使用 `encodeURIComponent(collectionName)`。

这不是 backend 的 filesystem path-safety 替代品。URL encoding 负责正确构造 HTTP URL；backend validation 才负责判断业务输入是否合法。

### 精读 6：从数据推导 `MenuKey`（`frontend/components/SideMenu.tsx:6-18`）

```tsx
const MENU_ENTRIES = [
  { key: 'knowledge-base', label: '知识库管理', index: '01' },
  { key: 'upload', label: '文件上传', index: '02' },
  { key: 'qa', label: '知识问答', index: '03' },
  { key: 'files', label: '文件管理', index: '04' },
] as const;

export type MenuKey = (typeof MENU_ENTRIES)[number]['key'];
```

- 没有 `as const` 时，`key` 很可能被 widen 成普通 `string`；
- `typeof MENU_ENTRIES` 取得 array 的静态类型；
- `[number]` 取所有 element types 的 union；
- `['key']` 再投影出 `'knowledge-base' | 'upload' | 'qa' | 'files'`；
- runtime menu entries 与 compile-time key union 来自同一来源，减少 duplicated truth。

`SideMenuProps` 随后把 `selectedKey` 和 `onSelect` 都约束为这个 union。`handleClick` 中仍有 `key as MenuKey`，因为 Ant Design 的 generic event type 只承诺较宽的 key type；安全性依赖 Menu items 确实只由 `MENU_ENTRIES` 生成。

### 精读 7：controlled navigation 与 exhaustive panel registry（`frontend/app/page.tsx:17-50`）

```tsx
const PANELS: Record<MenuKey, PanelDefinition> = { /* four definitions */ };

export default function Home() {
  const [selectedKey, setSelectedKey] = useState<MenuKey>('knowledge-base');
  const panel = PANELS[selectedKey];
```

- `Record<MenuKey, PanelDefinition>` 把“所有 menu key 必须有 panel”变成 compile-time invariant；
- `useState<MenuKey>` 阻止 state 进入未知 key；
- `panel` 是 derived value，不需要第二个 `useState`，因此不会出现 key 已变但 panel 仍旧的 split state；
- 初始 key 是 `knowledge-base`，对应应用首次加载展示知识库管理工作区；
- `SideMenu selectedKey={selectedKey} onSelect={setSelectedKey}` 构成典型的 state down / event up 数据流。

### 精读 8：为什么 content section 使用 `key` 与 `aria-live`（`frontend/app/page.tsx:106-134`）

- `key={selectedKey}` 让 React 在菜单切换时把 placeholder section 视为新 subtree；这里会重新触发 `panel-in` animation。未来放入真实 Feature Component 前，需要重新判断是否希望切换时 remount，因为 remount 会清除组件 local state。
- `data-panel-key` 是可观察的 DOM identity，便于浏览器验证和未来测试定位；它不参与业务逻辑。
- `aria-live="polite"` 尝试让 assistive technology 感知内容区域变化，同时不强行打断当前朗读。
- `aria-labelledby="panel-title"` 把 heading 作为 section 的 accessible name。
- decoration 使用 `aria-hidden="true"`，避免“DX”“01 grid”等视觉元素污染 accessibility tree。

### 精读 9：global provider 与 responsive boundary

`frontend/app/layout.tsx:14-45` 通过最外层 `ConfigProvider` 统一中文 locale、color tokens、font 与 Menu/Layout component tokens；未来 Ant Design components 自动消费同一 theme，不必各自重复配置。

`frontend/app/page.tsx:54-59` 用 Ant Design `breakpoint="lg"` 和 `collapsedWidth={0}` 定义组件级 responsive behavior；`frontend/app/globals.css:354-434` 再负责 layout-specific reflow。两者职责不同：Sider prop 改变组件状态，CSS media query 改变视觉布局。

---

## 6. 数据流

### 6.1 成功的 JSON request

```text
queryQA(question, collectionName, topK?, history?)
  → QueryRequest object（camelCase parameters → snake_case JSON fields）
  → jsonRequest(): RequestInit + JSON.stringify
  → request<QueryResponse>("/query", init)
  → fetch("{base}/query")
  → HTTP 2xx Response
  → response.json(): unknown runtime value
  → static assertion as QueryResponse
  → Promise<QueryResponse> resolves
```

### 6.2 失败 request 的三路分流

```text
fetch
  ├─ throws before HTTP response
  │    → ApiError(status=0, code=NETWORK_ERROR)
  ├─ resolves with !response.ok
  │    ├─ valid Section 6.7 envelope → preserve backend status/code/message/details
  │    └─ invalid JSON/shape         → ApiError(code=INVALID_RESPONSE)
  └─ resolves with response.ok
       ├─ valid JSON syntax → return as T
       └─ invalid JSON      → ApiError(code=INVALID_RESPONSE)
```

### 6.3 类型变化与 state boundary

- `File` + optional string → `FormData` → HTTP body；
- plain object → JSON string → HTTP body；
- runtime `Response` → parsed JavaScript object → statically typed `T`；
- failed response → normalized `ApiError`；
- client 内没有 React state、cache 或 persistent storage。

**Mental Model**：endpoint wrappers 决定“说哪一种 HTTP 方言”；`request<T>()` 决定“所有请求共同怎样成功或失败”；types 决定“编译器允许下游怎样使用返回值”。

### 6.4 菜单点击的数据流

```text
User clicks Ant Design Menu item
  → MenuProps['onClick'] event carries key
  → SideMenu.handleClick(key)
  → onSelect(key as MenuKey)
  → Home.setSelectedKey(key)
  → React schedules re-render
  → PANELS[selectedKey] selects PanelDefinition
  → controlled selectedKeys + heading + placeholder render consistently
  → URL remains http://localhost:3000/
```

- **类型变化**：Ant Design event key（wide library type）→ project-specific `MenuKey` → `PanelDefinition`。
- **state owner**：只有 `Home` 拥有 `selectedKey`；SideMenu 和 content 都是 consumers。
- **storage boundary**：纯 in-memory React state；reload 会恢复默认值，既不写 URL，也不写 localStorage。
- **failure boundary**：如果配置新增 key 却漏写 `PANELS` entry，TypeScript build 应失败；runtime 不需要 undefined fallback。

**T1002 Mental Model**：这是“一个状态、两个投影”——同一个 `selectedKey` 同时投影为左侧选中态与右侧内容，不需要 router，也不需要 global store。

---

## 7. 架构设计（本 Phase Tasks 的架构影响）

### 7.1 新增能力

- Feature Components 不再直接依赖 URL 拼接和 raw `fetch`；
- backend snake_case contract 被封装在 client boundary；
- 所有功能共享一个 `ApiError` vocabulary；
- 后续 UI 可以用 `error.code` 做稳定分支，例如 `COLLECTION_EMPTY` 提示先上传文档，而不是解析 message 文案。
- 应用获得一个稳定 shell：global provider、responsive Sider、四项 navigation 和 content slot；
- menu key 同时成为 navigation identity 与 content-registry key，为 Phase 11 组件替换提供稳定 seam。

### 7.2 契约兑现

T1001 消费已有 backend contracts，没有新增 server API。它向下游组件提供一组 frontend-facing function signatures：

```text
create/list/rename/deleteCollection
uploadFile
queryQA
list/preview/deleteFile
healthCheck
```

T1002 不新增 HTTP contract，而是兑现 F017 的 UI composition contract：四个固定功能入口、单页 state switching、无独立 route。

### 7.3 关键责任边界

- **Backend**：runtime validation、business rules、HTTP status、Section 6.7 envelope；
- **API client**：transport、serialization、URL encoding、error normalization、static return types；
- **Feature Component**：loading/success/empty/error state、retry action、用户提示；
- **T1001 不负责**：authentication、retry policy、global UI state、runtime success schema validation。
- **RootLayout**：全局 locale/theme 与 document shell；
- **Home page**：navigation state 与 feature-slot composition；
- **SideMenu**：render menu + emit typed selection intent；
- **Phase 11 Feature Components**：各自管理业务请求和四态 UI；
- **T1002 不负责**：真实 CRUD/upload/QA/file-management behavior。

---

## 8. Engineering Review（工程决策摘要）

> Phase 10 两个 implementation Tasks 已 DONE，独立 Gate verdict 为 `PHASE_10_PASS — READY_FOR_PHASE_11`，且 [Phase 10 Engineering Review](./engineering-review/phase-10-engineering-review.md) 已于 2026-09-04 完成。本节只保留理解代码所需的 engineering implications，不复制完整 ADR。

- 单一 request core 降低重复，但它也成为所有 frontend API calls 的共享故障点；改动必须覆盖 JSON、multipart 与 error paths。
- `ApiError` 同时保留 Error semantics 与 backend fields，适合组件按 machine-readable `code` 分支。
- 当前 success path 使用 type assertion，没有 runtime schema validation；这是 v1 简洁性与防御性的明确 trade-off。
- error-code union 末尾保留 `(string & {})`，对新增 backend code 保持 forward compatibility，但会弱化 exhaustive checking。
- 当前使用 `console.error` 记录 code/status，不记录 payload 或用户内容，减少无意泄露；项目尚无 structured frontend observability。
- navigation state 单点拥有使 shell 易于推理；代价是 reload/deep-link/back-forward 不保存当前模块，这是 F017 明确选择的 single-page no-route boundary。
- `key={selectedKey}` 对 placeholder animation 很合适，但未来真实组件可能因 remount 丢失 local state；Phase 11 接入时必须有意识地决定保留还是移除。
- RootLayout 当前是 Client Component，方便直接包裹 Ant Design provider；代价是放弃了 root server boundary 的一部分能力，未来若需要 server metadata/SSR optimization 可拆出 client provider。
- responsive behavior 同时存在于 Ant Design breakpoint 与 CSS media queries；两处 breakpoint 演进时要避免不一致。

---

## 9. Technical Decision（技术决策备忘录）

| 决策 | 备选方案 | 选择理由 | 代价/边界 |
|---|---|---|---|
| 原生 `fetch` + shared wrapper | Axios | v1 需求简单，减少依赖；browser/Next.js 原生支持 | 没有 interceptor ecosystem；需自己维护错误解析 |
| endpoint-specific functions | 组件直接调用 `fetch` | 集中 protocol knowledge，组件更容易测试和阅读 | API contract 变化时仍需同步 wrapper/types |
| `unknown` + type guards 解析 error | `any` / blind cast | 强迫代码先证明字段可读 | guard 只验证必要字段，不等于完整 validation |
| generic `request<T>` | 每个函数重复 JSON parsing | 统一 success/error semantics | `T` 在 runtime 被擦除 |
| browser 生成 multipart header | 手写 `Content-Type` | 自动携带正确 boundary | 调试时 header 不在源码中显式出现 |
| unknown error code 仍允许进入 `ApiError` | 封闭 enum 后拒绝 | 前后端滚动升级时更稳健 | 编译器无法强制 exhaustive switch |
| parent-owned `selectedKey` | SideMenu internal state / global store | 同时驱动 menu 与 content，避免 split state；规模不需要 Redux/Zustand | reload 不持久化，无法 deep-link |
| `Record<MenuKey, PanelDefinition>` | switch/if chain | compile-time 检查 menu-panel 完整性 | panel metadata 需集中维护 |
| state switching，不使用 router | Next/React Router routes | 直接符合 F017 单页契约，无页面导航 | 浏览器 back/forward 不切模块 |
| Ant Design responsive Sider | 自建 drawer/navigation | 复用成熟 breakpoint/collapse behavior | 对 Ant Design class/token contract 有依赖 |
| global design tokens + scoped CSS | 每组件 inline style | 一致主题且保留 layout 精细控制 | theme token 与 CSS variables 需共同维护 |

---

## 10. Interview Notes（Phase Learning Review 晋升结果）

Phase 10 candidates 已按 cadence 完成筛选、去重与晋升。完整口语答案统一维护在 [Interview Guide 的 Phase 10 深度章](./interview-notes/dx-rag-interview-guide.md#phase-10-深度章--frontend-foundationt1001t1002-已实现--gate--learning-review-完成)，本教材不再复制 answer bank。

- **晋升主线**：typed HTTP boundary → normalized failures → controlled composition boundary。
- **保留的高价值问题**：compile-time vs runtime contract、`fetch` 三类失败、multipart boundary、literal-derived key、single source of truth、no-router/no-global-store 的范围理由、`key` remount 风险、证据等级。
- **未晋升为 STAR**：Phase 10 没有真实 production incident、复杂故障闭环或修复事件；正常实现与验证不包装成事故故事。
- **亮点话术**：我先用 typed API client 收敛 HTTP contract，再用 literal-derived keys、controlled state 和 exhaustive panel registry 搭出单页 shell，让 Phase 11 组件可以沿稳定 seam 接入。
- **诚实边界**：production build、mocked API-client failure probes、四菜单真实浏览器切换、两个窄屏 viewport 和 console check 已完成；真实 Feature Components、browser↔FastAPI E2E 与 repository-owned frontend regression suite 尚未完成。

---

## 11. Future Improvement（未来改进方向）

以下均为 **Future / Not implemented in v1**：

| 方向 | 触发条件 | 是否 SPEC 已规划 | 说明 |
|---|---|---|---|
| success response runtime validation | backend/frontend 独立发布、contract drift 开始出现 | 否，个人复盘 | 可引入 Zod/Valibot 或生成式 schema client |
| generated API types/client | endpoint 数量增长、人工同步成本升高 | 否，个人复盘 | 可从 OpenAPI 生成，仍需检查生成结果语义 |
| focused tests with stubbed `fetch` | T1001 regression risk 增长 | 否，个人复盘 | 覆盖 network、4xx envelope、bad JSON、204、multipart |
| request cancellation | 页面切换或搜索竞态导致 stale response | 否，个人复盘 | 使用 `AbortController`，由组件 lifecycle 协调 |
| authentication headers | 产品未来加入登录/权限 | v1 明确不包含 | 应集中注入，不散落到 components |
| frontend telemetry | 需要定位线上错误率与延迟 | 否，个人复盘 | 避免记录文件内容、问题或答案等敏感数据 |
| feature component state-preservation policy | Phase 11 组件接入、用户切换菜单时 | 否，个人复盘 | 决定是否移除 content `key`，或显式保存/重置 local state |
| URL/deep-link navigation | 用户需要分享具体模块或使用 back/forward | v1 明确不包含 | 需产品修改 F017 后再考虑 App Router routes |
| split Server RootLayout + Client Providers | 需要 server metadata、SSR boundary 或减少 client surface | 否，个人复盘 | 将 interactive/provider 部分下沉到独立 client component |
| automated accessibility/component tests | UI 结构频繁演进 | 否，个人复盘 | 验证 menu roles、focus、live region 与 keyboard navigation |
| unify responsive breakpoint source | CSS 与 Ant Design breakpoint 开始分叉 | 否，个人复盘 | 用共享约定或测试防止双重配置漂移 |

---

## 自测题与动手练习

### 自测题

1. 为什么 `fetch()` 收到 HTTP 404 时通常不会进入 `catch`？当前代码在哪里处理它？
2. `request<QueryResponse>()` 中的 `QueryResponse` 在 JavaScript runtime 还存在吗？为什么？
3. 为什么 error payload 先声明为 `unknown`，而不是 `ErrorResponse` 或 `any`？
4. `collectionName === undefined` 与 `collectionName === ""` 对 `uploadFile()` 的 wire payload 有何不同？
5. 为什么 `FormData` 请求不能复用 `jsonRequest()`？为什么不应手写 multipart `Content-Type`？
6. `NETWORK_ERROR` 为什么使用 `status: 0`？它与 backend 返回 500 有什么本质区别？
7. `encodeURIComponent` 能否替代 backend 的 collection name validation 或 path-safety？
8. 如果 backend 返回 200 和 `{ "answer": 42 }`，当前 client 会怎样？TypeScript 会在 runtime 拦住吗？
9. 为什么 Feature Component 仍要拥有 `loading/error/empty/success` state？
10. `(string & {})` 给 `ApiErrorCode` 带来了什么兼容性收益和类型检查代价？
11. `MenuKey` 是怎样从 `MENU_ENTRIES` 推导出来的？`as const` 去掉后会发生什么？
12. 为什么 `PANELS` 使用 `Record<MenuKey, PanelDefinition>` 比 `Record<string, PanelDefinition>` 更安全？
13. menu item click 后，state 从哪里流向哪里？为什么 SideMenu 不应再维护内部 selected state？
14. 为什么菜单切换能做到 URL 不变？这与“没有页面刷新”有什么关系？
15. `key={selectedKey}` 会怎样影响 React subtree identity？接入真实组件后需要评估什么？
16. Ant Design Sider props 与 CSS media queries 在 responsive behavior 中分别负责什么？
17. 为什么 `page.tsx` 和 `SideMenu.tsx` 需要 `'use client'`？

### Phase 级贯通自测

18. 一个 Phase 11 `QAPanel` 从菜单被选中到收到 backend 错误，依次跨过哪些 owner boundary？
19. 如果组件自己写 `fetch('/api/query')`，同时又在本地维护一个与 SideMenu 无关的 `activePanel`，分别破坏了 Phase 10 的哪两个原则？
20. 新增菜单 `settings` 时，当前 TypeScript 设计会在哪些位置帮助发现漏配？哪些行为仍只能靠 runtime/component test？
21. 为什么“production build PASS”不能单独证明 AC-F017-01？为什么“四菜单点击 PASS”又不能证明真实 API integration？
22. Phase 11 替换 placeholder 时，为什么必须重新审查 `key={selectedKey}`？它可能与 F017 要求的 component-state behavior 怎样冲突？

### 答案要点

1. 404 是已收到的 HTTP response；由 `!response.ok → parseErrorResponse()` 处理。
2. 不存在；TypeScript types 编译后擦除，`T` 只约束开发期使用方式。
3. 网络输入未经信任；`unknown` 强制 narrow，避免盲目读字段。
4. `undefined` 不 append，backend 可用 default；空字符串会作为显式 form field 发送并由 backend 处理。
5. wire format 不同；browser 要根据 FormData 自动生成 multipart boundary。
6. status 0 表示没有 HTTP response；500 是 server 已响应的应用/服务器失败。
7. 不能；URL encoding 是传输编码，validation/path-safety 是业务与安全规则。
8. JSON parsing 会成功，并被断言成 `QueryResponse`；runtime 不会验证 `answer` 类型。
9. client 不拥有 view lifecycle；同一个 request result 在不同组件中可能对应不同 UI。
10. 新 code 不会破坏 consumer，但 switch 很难获得真正的 exhaustiveness guarantee。
11. `typeof` 取数组类型、`[number]` 取元素 union、`['key']` 投影 key；没有 `as const` 时 literal 通常 widen 为 `string`。
12. 前者要求所有合法 key 都有定义，并拒绝无关 key；后者不能发现漏项。
13. `Menu event → onSelect → Home.setSelectedKey → props/derived panel`；单一 owner 防止 menu 和 content 不一致。
14. click handler 只更新 React memory state，没有 link/router navigation；浏览器验证显示四次切换均停留在 `/`。
15. key 改变会 remount subtree；真实组件接入后要评估是否会意外清除 form、history 或 fetch state。
16. Sider props 改变 collapsed component state；media queries 调整 position、padding、grid 等视觉布局。
17. 它们使用 `useState`/event handlers 等 client-only interactivity；Server Component 不能直接持有这些行为。
18. `SideMenu → Home.selectedKey → QAPanel slot → queryQA → request<T> → FastAPI → ApiError → QAPanel error state`；shell、component、transport、backend 各自拥有一段责任。
19. raw `fetch` 绕过 centralized transport contract；第二份 `activePanel` 破坏 single source of truth，可能让 menu 与 content 不一致。
20. `MenuKey` 从 entries 推导，`Record<MenuKey, PanelDefinition>` 会要求 panel definition；但文案正确性、视觉呈现、click/focus behavior 仍需 runtime verification。
21. build 证明可编译，不执行用户 click；browser click 证明本地 UI state transition，不调用 backend，也不证明 API payload/response compatibility。
22. key 改变会 remount subtree并清除 local state；真实 QA history、form input 或 request state 是否应保留，必须按 F017/T1105 的明确行为重新判断。

### 动手练习

不改生产代码，先设计 `request<T>()` 的测试矩阵：

```text
Case A: fetch rejects
Case B: 404 + valid Section 6.7 JSON
Case C: 500 + malformed JSON
Case D: 200 + invalid JSON syntax
Case E: 200 + valid JSON
Case F: upload FormData contains file and optional collection_name
```

对每个 case 写出：mocked `Response`、预期 resolve/reject、`ApiError.status/code/details` assertions，以及它属于 `MOCKED` 还是 `REAL E2E` evidence。完成后再考虑是否值得把测试正式加入未来 task；本次 Learning Pass 不越界修改实现或新增测试。

再为 T1002 设计一个 component/browser test matrix：

```text
Case G: initial selected item = knowledge-base
Case H: click each item → matching heading/data-panel-key
Case I: every switch keeps pathname = "/"
Case J: 640px viewport → Sider zero-width + trigger visible
Case K: keyboard navigation and focus visibility
Case L: replace placeholder with stateful probe → decide whether key-driven remount is desired
```

G–J 已有本次手动 browser evidence，但还没有进入 automated regression suite；K–L 是接入 Phase 11 前值得验证的边界。

---

## Verification Ledger（T1001–T1002 + Phase 10 Gate）

| Evidence | Result | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| `npm run build`（2026-09-04，Gate 独立复跑） | PASS / REAL | Next.js production compile、lint、TypeScript validity、4/4 static page generation 通过 | 真实 backend integration、用户交互语义 |
| SPEC / Pydantic / TS static comparison | PASS | endpoint coverage、field names/types、error envelope 在源码层对齐 | deployed service 一定返回相同 shape |
| 初次 sandbox build | `spawn EPERM` | 受限环境不允许 Next worker spawn | 不是源码或类型失败；授权后同命令 PASS |
| T1001 inline `fetch` probes | 5/5 PASS / MOCKED | base URL、success JSON、合法 error envelope、malformed error、network failure、invalid success JSON 的 owned logic | 真实 backend、multipart upload E2E |
| Repository-owned T1001 tests | NOT_AVAILABLE | — | 上述 probes 尚未形成持续 regression suite |
| Browser ↔ FastAPI E2E | DEFERRED | — | 不能声称真实跨层调用已验收 |
| T1002 four-menu browser interaction | PASS / REAL | 四项 heading/content 随 state 切换，URL 保持 `/`，AC-F017-01 当前行为成立 | 自动回归、Phase 11 真实模块切换 |
| 640px + 约 360px responsive browser checks | 2/2 PASS / REAL | Sider zero-width、trigger、单列 reflow、无 horizontal overflow | 全设备/浏览器视觉矩阵 |
| Browser console error/warning check | PASS / REAL | 本次 load 与 menu interaction 未捕获 console error/warning | 长时间运行或未来组件错误 |
| T1002 focused automated tests | NOT_AVAILABLE | — | menu、responsive、accessibility 尚无持续回归保障 |
| Phase 10 Gate Review | `PHASE_10_PASS — READY_FOR_PHASE_11` | 独立审计 Tasks、AC-F017-01/AC-FE-01、contracts、runtime 与完整 Git state | 只授权 readiness，不代表 Phase 11 已开始 |

### Phase Learning Review 收口边界

- Technical Learning 已完成跨 Task consolidation；README、Project Map 与 Interview Guide 做最小同步；
- 不修改 T1001/T1002 实现或 TASKS 状态；
- 本次 Phase Learning Review 当时不创建完整 Engineering Review；后续独立评审现已完成，详见 [Phase 10 Engineering Review](./engineering-review/phase-10-engineering-review.md)；
- Interview Candidates 已按 Phase cadence 晋升到项目级 Interview Guide，并从本节移除重复 answer bank；
- Gate verdict 作为 Phase Learning Review 的前置事实保留，不把 Learning Review 当成第二次 Gate；
- 不开始 Phase 11，不 commit、不 push。
