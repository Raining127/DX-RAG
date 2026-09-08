# T1204 frontend runtime evidence

Date: 2026-09-07. Browser: existing Chrome via CUA/Playwright accessibility
snapshots. Production build served at `http://127.0.0.1:3104/`.

Commands:

```text
python -u backend/scripts/serve_t1204_browser_backend.py
cd frontend
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3104
```

Both servers reached READY. Backend storage was
`<TEMP_DIR>/`.
The backend harness seeds `browser-empty`, `browser-kb` and
`machine-learning.txt`. FastAPI/HTTP/retrieval/Chroma are real; embeddings and
LLM answers/errors are DETERMINISTIC, not live provider evidence.

## Observed browser outcomes: 6 PASS, 0 FAIL

| Case / AC | Actions | Observed result |
|---|---|---|
| Navigation: F017-01 / FE-01 | QA -> File Manager -> Upload -> QA via menuitems | Main heading/region changes; URL remains `/`; QA conversation remains when returning. Source `app/page.tsx` keeps mounted panels and changes React state, not location/navigation. |
| QA: F017-03 / FE-03 | Select browser-kb using combobox/keyboard; fill `machinelearningtoken`; Control+Enter; expand sources | Pending article shows question and `正在检索证据并组织回答…`; loading image/button disabled. Completion shows history 2, heading `验收回答`, strong `机器学习`, list items, expandable source `machine-learning.txt` and code score `0.300`. Actual Markdown DOM elements observed. |
| Backend 500: F017-04 | Send `trigger500`; click retry | Loading -> alert `问答请求失败` / `问答模型返回了无法解析的响应，请重试。`; enabled `重 试` button. Clicking it enters RETRIEVING/loading again. Harness raises the declared LLM_RESPONSE_ERROR; this is controlled error evidence. |
| History lifecycle | Switch from browser-kb to browser-empty | History 2 -> 0, old answer removed, empty-conversation prompt shown. |
| Empty KB: FE-05 | Send `empty collection audit` to browser-empty | Alert `知识库暂时无法回答` / `知识库暂无文档，请先上传文件。`; retry button present. Real empty-collection API path returns 409 (also verified in API regression). |
| Network: FE-04 | Stop only the isolated backend; send `network audit` | Loading -> alert `问答请求失败` / `无法连接后端服务，请检查服务状态后重试。`; retry button present. This is an actual local transport outage, not a provider failure. |

Console error messages `DX-RAG API request failed Object` occurred during the
intentional 500/409/network scenarios; these are expected error-path logging,
not a claim of a zero-error console audit. No browser-wide accessibility,
cross-browser, or model-quality guarantee is made.

## Upload boundary: evidence limitation and complementary verification

The 51 MiB file chooser attempt was **BLOCKED_BY_BROWSER_PERMISSION**:
Chrome returned `Not allowed` on `fileChooser.setFiles`. No successful browser
file selection, drag/drop, upload or screenshot of its validation error is
claimed. The user was told how to enable the extension's file URL access;
no permission or browser setting was changed by the agent.

F017-02 / FE-02 are verified instead as **DETERMINISTIC component contracts**:
[frontend-component.txt](frontend-component.txt), run with
`cd frontend; node scripts/verify_t1204_contracts.cjs`.
This loads the actual FileUpload TSX, actual TypeScript, React element builder
and installed Ant Design components/constants. Only hook state/effects and
the API boundary are controlled. It invokes the component's actual
`beforeUpload`, re-renders its element tree and inspects the Alert props:

- 51 MiB: returns actual `Upload.LIST_IGNORE`, error Alert description is
  `文件大小超过 50MB 限制。`, upload API calls = 0.
- 50 MiB: returns true (allowed past validation), upload API calls = 0 at
  this pre-upload stage. This is not a claim that a 50 MiB upload was sent.

The installed Ant Design/rc-upload LIST_IGNORE guard and FileUpload's
`beforeUpload`/`customRequest` wiring were inspected. The separate existing
validator also passes 51/50 MiB, empty and unsupported-file cases (4/4).
This establishes the mandatory frontend boundary without claiming browser
upload evidence or introducing another test framework/dependency.

## Cleanup and execution qualifications

The created browser tab was closed. Both task-owned server sessions were
stopped deliberately (exit 1 on control-C is process shutdown, not test failure).
The exact temporary backend tree was verified and removed, along with
`tmp/t1204-upload-51mb.txt` (53,477,376 bytes). Business uploads/Chroma were
not targeted. No user's pre-existing tabs or processes were closed.

The initial component-probe subprocess exceeded its 60-second process budget
before producing a retained result; it was not counted as PASS. Direct rerun
and the final captured rerun succeeded (2/2, exit 0). The final capture uses a
360-second process limit. No source change was made to obtain that rerun.
Browser execution used the pre-CORS-fix server with default origins; frontend
files remained unchanged and default CORS behavior is verified unchanged by
the new backend configuration regression.
