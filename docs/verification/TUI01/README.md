# 整体布局与知识问答页优化验收

日期：2026-09-30。Task：TUI01。分支：`codex/frontend-optimization`。
基线：`main` / `4d122381483a8e729fea45a2bf43e817f97c624a`，独立 worktree；原检索实验工作区没有参与本次实现。

## 页面检查与结果

修改前在实际 Next.js 页面中检查 1440×1000 与 390×844 布局，使用隔离的知识库列表 fixture。原页头包含大标题、Phase 10 标记及开发术语；问答区使用固定的最小高度，输入区不能完整保留在首屏；窄屏页面空白区域较长。

本次缩小页头与桌面导航，采用深绿导航、浅灰背景和白色工作面；清理开发阶段文案。问答页以动态视口高度分配空间，对话区独立滚动、输入区留在页面内；Markdown 使用清晰的标题、段落、引用和代码块样式，来源显示文件名与原始相关性数值。窄屏导航采用 Ant Design Drawer，保留四个入口与默认知识库管理入口。

## 验收证据

| 验收项 | 本次执行证据 | 结果 |
|---|---|---|
| AC-UI01-1：先检查实际页面、简洁专业风格 | 修改前后桌面/窄屏截图 | PASS |
| AC-UI01-2：390 / 768 / 1440px 无横向溢出、输入可见、长内容滚动 | 浏览器 scrollWidth/clientWidth、输入 bounding box、对话 scrollHeight/clientHeight 断言 | PASS |
| AC-UI01-3：保留 API 与业务状态 | 组件联动 5/5、上传大小边界 2/2；浏览器请求、历史、切库与竞态断言；保护路径 diff 无变化 | PASS |
| AC-UI01-4：构建、状态回归、运行预览 | TypeScript exit 0；生产构建 exit 0；浏览器 20/20；`npm run preview` | PASS |

执行命令（工作目录为 `frontend/`）：

```text
node node_modules/typescript/bin/tsc --noEmit
node scripts/verify_f6_integration.cjs
node scripts/verify_t1204_contracts.cjs
node scripts/verify_frontend_ui.cjs
node node_modules/next/dist/bin/next build
```

浏览器脚本使用现有 Playwright 工具运行时；通过 `PLAYWRIGHT_MODULE` 指定模块路径、`CHROMIUM_PATH` 指定本机 Chrome。脚本不新增项目依赖。必须先启动隔离预览，输出默认位于 `tmp/frontend-ui/`。完整结果见 [browser.json](browser.json)。

生产构建通过编译、类型检查、4/4 静态页面生成和 build traces。根路由输出：250 kB / First Load JS 389 kB。没有测量运行性能提升。

本次没有未捕获的浏览器 JavaScript 异常。控制台保留了受控 500、409 故障与 API 日志，以及既有 favicon 404；不声称控制台零日志或全面无障碍审计。

## 运行预览

```powershell
npm run preview
```

默认页面为 `http://127.0.0.1:3001`，演示 API 为 `http://127.0.0.1:8011/api`。可用 `PREVIEW_PORT` / `PREVIEW_API_PORT` 覆盖端口。顶部标记为「演示预览」。关闭启动进程后结束预览。

演示 API 使用内存中的三个知识库、文件元数据和固定答案；创建、改名、上传、删除只影响该进程内存，重启即重置。上传不进行真实解析或向量化。没有调用真实存储、embedding、检索、OCR 或 LLM。

正常业务仍使用 `npm run dev` 与既有 `NEXT_PUBLIC_API_BASE_URL`（默认 `http://localhost:8000/api`）。演示设置只传给预览子进程，未修改正常 API client、后端或环境文件。

## 保护范围与截图

相对 main 核对：`backend/`、`frontend/lib/`、知识库/上传/文件管理组件、package-lock、冻结 V1 SPEC / TASKS 无差异。四个功能组件继续挂载，保持隐藏页面的草稿、历史和文件联动。

本地截图位于 `tmp/frontend-ui/`：`desktop-collections.png`、`desktop-qa-empty.png`、`desktop-qa-answer.png`、`768px-qa-answer.png`、`390px-qa-answer.png`；修改前截图位于该目录的 `before/`。图片没有写入冻结历史验收目录。

用户已确认「优化采纳」，并在 2026-09-30 要求提交、合并该分支。本次交付包含提交 `codex/frontend-optimization`、推送并通过 PR 合入 `main`；实际提交与合并状态以 Git / PR 记录为准。此授权不包含网站发布或另一工作区的检索融合改动。
