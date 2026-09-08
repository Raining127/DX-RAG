# Phase 12 Learning Review — 怎样证明 RAG 系统符合契约

> **学习复盘日期：2026-09-07。** T1201–T1204 已 DONE；本次完成学习层 consolidation，不修改 Task 状态或产品代码。
> **流程边界：**独立 fresh-reader 检查尚未执行，因此不将本次整理标为 Learning Pass workflow DoD 全部满足。
> **Gate 单独记账：**历史 `PHASE_12_FAIL — FIX_REQUIRED` 保留；F-6 remediation 后的独立增量 Re-review 已完成，当前 **PHASE_12_PASS / F-6 CLOSED**，见 [Gate closure](../verification/PHASE-12-GATE-CLOSURE.md)。独立 fresh-reader 与完整 Learning Review workflow 仍 pending。
> **证据时点：**复用并核对 T1204 的最终验收记录，本次不重跑 runtime suites、不调用 DashScope/DeepSeek。
> **阅读定位：**本文是当前 Phase 级学习入口；[原 Task Learning Pass](phase-12-integration-acceptance.md)保留为 pre-live 历史精读，旧稿中的“当前”“本轮”和计数属于旧检查点。

## 1. Phase 学习：先学会提出可验证的主张

**最终闭环补记：**F-6 曾因上传后的文件列表/数量不同步使 Gate FAIL。旧 source-string inspection 只证明调用名称存在，没有执行 Home 与组件之间的状态流；新增确定性 COMPONENT/INTEGRATION 使用实际组件和 MOCKED API/hooks，修复前失败、修复后 5/5 通过。随后独立增量 Re-review 再验证红/绿对照并裁定 **PHASE_12_PASS / F-6 CLOSED**。这条历史说明测试范围必须对应业务状态，不能把组件替身证据称为 browser upload E2E。

完整 ADR、failure taxonomy、规模取舍和未解决工程问题见 [Phase 12 Engineering Review](engineering-review/phase-12-engineering-review.md)（2026-09-07 完成工程分析；不代表 Known Gaps 已修复）。

你已经在 Phase 0–11 写出了上传、解析、向量化、检索、问答和前端。Phase 12 的输入不只是代码，而是**冻结要求、当前实现和待验证的行为主张**。输出是能够回到原始观察的验收证据。

本章统一使用一条推理链：

```text
SPEC 的 Given / When / Then
  -> 构造满足 Given 的 fixture
  -> 经过被测实现执行 When
  -> 观察 Then，以及不应发生的副作用
  -> 标明真实依赖与受控替代
  -> 将结果绑定到当前源码版本
  -> 得到有限、可复核的结论
```

🟢 **必会：**observable behavior、失败后的状态、证据边界、AC occurrence 与 ID 的区别。
🟡 **理解原理即可：**子进程隔离、Python import 缓存、异常 traceback 延长资源生命期、patch where-used。
🔵 **知道存在即可：**semantic manifest、CI 接管、大规模模型质量评估。这些不是本轮已交付能力。

建议先读本章第 3–6 节，再打开代码。读代码时始终问：“如果实现错了，这个断言会不会仍然通过？”这比记住某次脚本通过了多少检查更重要。

## 2. Phase 目标与项目位置

| Task | 在整个系统中证明什么 | 不能单独证明什么 |
|---|---|---|
| T1201 | 文件进入系统、三态 ingestion、失败零残留、真实 OCR 和本地 BGE | QA 回答正确性 |
| T1202 | 已入库知识到检索、context/history、真实 DeepSeek 答案和 sources | 任意语料上的准确率或注入防御保证 |
| T1203 | 用户按文件身份管理数据，删除不误伤另一 KB | 任意中途删除失败均有事务补偿 |
| T1204 | 所有 mandatory 条目有可追溯证据，接口/错误/字段与 DoD 没有遗漏 | 独立 Phase Gate 的新 verdict |

前置知识按依赖回看：[Phase 5 上传与回滚](phase-05-file-upload.md)、[Phase 7 检索](phase-07-vector-retrieval.md)、[Phase 8 QA](phase-08-rag-qa.md)、[Phase 9 文件管理](phase-09-file-management.md)、[Phase 11 前端状态](phase-11-frontend-features.md)。不要把它们重新实现一遍；这次学习的是怎样让组合路径接受检验。

## 3. 统一 mental model：业务状态图，加上一张证据表

业务状态图回答“用户的一次操作改变了什么”；证据表回答“我们凭什么相信这些变化正确”。二者分开，才能避免把有测试误当成测试足够。

```text
上传 bytes
 -> validation -> raw file -> parse/native or OCR -> clean -> chunk
 -> BGE 512d -> Chroma records -> keyword cache invalidation
                     |
                     +-> persisted file list / preview / delete
                     |
问题 + collection + history
 -> collection preflight
    empty -> 409，retrieval/LLM 均不调用
    nonempty -> keyword + vector -> 0.3/0.7 fusion
             -> sort -> relevance >= 0.30 -> Top-K
             -> whole-chunk context + history -> DeepSeek -> answer
             -> backend-owned sources --------------------> API
```

文件名是显示和查重属性，`file_id` 是文件身份，`chunk_id` 是切片身份。删除后上传同名文件，身份应该更新；重命名知识库，原身份应该保留。两种场景看起来都“换了名字或路径”，但正确性条件相反。[PROJECT FACT]

验证时可以把状态写成 `S = (raw files, persisted chunks/vectors/metadata, file projection, keyword state, other-KB control)`。成功上传检查新增；FAILED 检查没有新增残留；删除检查目标消失、对照组不变。不是每个缓存字节都必须相同：已 invalidated 的缓存应通过下一次重建证明不再返回旧数据。[ENGINEERING KNOWLEDGE]

## 4. 四个 Task 怎样组合成一份完整论证

### 4.1 T1201：失败响应只是结果的一部分

定位 [verify_t1201_ingestion.py](../../backend/scripts/verify_t1201_ingestion.py) 的 PDF fixtures、FAILED 前后对比及同名重传场景；再读 [upload.py](../../backend/app/api/upload.py) 和 [IngestService](../../backend/app/services/ingest.py)。

真实 OCR 成功证明 adapter 确实与 Qwen 交互并得到文本；五页 PDF 的第三页受控超时证明局部失败仍保留其他四页；三页全部失败时，HTTP 422 之外还需要检查 raw、Chroma、keyword 与文件列表。最后用同名重新上传验证失败没有留下业务阻塞。

“返回 422，所以回滚正确”是不成立的：response 和持久化可能已经分叉。这个 Phase 实际发现 Windows malformed-PDF 句柄问题，就是一次反例，而不是假设出来的事故。

### 4.2 T1202：分别验证真实回答和精确控制流

定位 [live helper](../../backend/scripts/verify_t1202_live.py)、[确定性矩阵](../../backend/scripts/verify_t1202_retrieval_qa.py)、[failure contract](../../backend/scripts/verify_t1202_failure_contract.py)。

真实问答使用已知 fixture，例如课程编号 PY482、7 道练习；答案命中知识库独有事实比“回答非空”更能支持 grounding。代词问题还要检查相关事实及来源，不能因为答案没有重复“Python”这个词就判定失败。反过来，仅出现 Python 也不能证明优缺点答对。

0.8/0.9 的融合示例则适合受控输入：`0.8*0.3 + 0.9*0.7 = 0.87`。真实模型输出不必恰好产生这两个分数。真实检索与 literal 算术 fixture 是互补证据，不互相替代。

关键教训是**验收脚本也可能错**。旧 live runner 因没有真实观察到 429/5xx 而 exit 2，但 SPEC F013 与 §9.3 要求的是收到错误后的 retry contract，没有要求自然发生一次 provider 故障。审计移除的是脚本自行增加的门槛，原始 exit 2 和未观察状态仍保留。[BLOCKER-AUDIT](../verification/T1202/BLOCKER-AUDIT.md)

### 4.3 T1203：用“数据分叉”和对照组定位真实数据源

定位 [verify_t1203_file_management_security.py](../../backend/scripts/verify_t1203_file_management_security.py) 中的 preview、delete 和 KB-B 对照。

Preview 的强验证不是“得到一段文字”，而是先修改 raw file，再阻断 Parser/OCR/Embedding/LLM，观察 response 仍等于 persisted chunks 的 index 顺序拼接。这样才排除了“实现偷偷重读原始文件”的可能。

Path traversal 同理：除了 400，还比较请求前后 raw/Chroma 没有变化。删除则把 KB-B 的同名文件作为对照组，检查 UUID、内容和预览不受影响。完整 lifecycle 会暴露单个 endpoint 单元测试看不到的错误身份传递。

### 4.4 T1204：先保证账目完整，再逐项检查证据

定位 [完整矩阵](../verification/T1204/ACCEPTANCE-MATRIX.md)与 [JSON](../verification/T1204/acceptance-matrix.json)。

Section 5 有 65 个条目、Section 12 有 39 个，共 104 occurrences；去重后 85 IDs。F003 的部分同名 ID 在两节中含义不同，因此主键必须是 `(section, ac_id)`。`set(ids)` 能发现 ID 缺失，不能替你验证两个 Given/When/Then。

旧 T1203 删除 fixture 有 1 个 chunk，能验证该次 N-chunk 删除，但不能声称逐字构造了 F016-02 的 15-chunk Given。T1204 用实际持久化的 15 个 PDF chunks 补齐，并检查另两个文件不变；三文件列表也得到 literal fixture。

最终审计还发现 `CORS_ORIGINS` 有配置定义、没有运行时消费。这个例子说明：schema、配置类、甚至默认环境下成功的 browser 请求，都不能证明配置项有效。

## 5. 代码精读：把 Python 机制连接到验证目的

### 5.1 环境变量必须先于 import 设置

`config.py` 的模块级 `settings = Settings()` 在 import 时执行。之后再改 `os.environ`，已构造的对象不会重新读取。类似一个 TypeScript 模块在顶层执行 `const config = readEnv()`，后续使用的是同一个导出值。

因此 probe 先设置临时 `UPLOAD_DIR`、`CHROMA_PERSIST_DIR`，再导入 app。父进程启动 child，不只是避免全局变量污染；child 退出也释放 Chroma/native library 的进程级文件句柄，然后父进程删除自己创建的临时目录。不要对业务 uploads 使用同一清理代码。

旧稿 [§5.1–5.2](phase-12-integration-acceptance.md)保留子进程和 `sys.modules` 精读。那里模型替代的技术机制仍适用；“provider 不可用”的原因描述属于历史。

### 5.2 `patch` 要修改被测代码查找的名字

`qa.py` 使用 `from openai import OpenAI`，之后查找自己模块中的 `OpenAI` binding。所以测试 patch `app.services.qa.OpenAI`，而不是假设替换任意地方的 `openai.OpenAI` 都会影响已经导入的引用。

`patch` 是 context manager，`with` 退出时恢复原对象。把替代限定在被测外部边界，真实 `DeepSeekClient.generate_answer()` 仍构造 prompt、分类错误和执行 retry。若直接替换整个 `generate_answer()`，就不能用该测试证明它自己的 retry 实现。

### 5.3 为什么读取 PDF bytes 能修复 Windows rollback

当前 [parse_pdf_file](../../backend/app/services/ingest.py) 先执行：

```python
doc = fitz.open(stream=file_path.read_bytes(), filetype="pdf")
```

此前由 PyMuPDF 按文件名打开 malformed PDF，失败异常的 traceback 可能保留 native 文件句柄；外层 rollback 即使已经进入 `except`，也可能因 Windows 文件仍被占用而无法 unlink。

`read_bytes()` 在自己的读文件作用域结束时关闭句柄；parser 随后面对 bytes。**异常被捕获，不意味着 traceback 中引用的资源已经释放。**当前 [test_upload.py](../../backend/tests/test_upload.py) 在异常仍存活时验证能够删除 malformed PDF，直接针对原 bug 的触发条件。

代价是额外的一份 PDF 内存拷贝；它不是零成本的资源技巧。这里修复的是有证据的 rollback 故障，没有添加 OCR 后处理或新格式能力。

### 5.4 重试验证看三件事：次数、间隔、最终映射

读 [DeepSeekClient.generate_answer](../../backend/app/services/qa.py)。初始请求不 sleep；每次决定再试之前才 sleep；两次重试最多产生 `[1, 2]` 秒等待。401/403 先走 auth 分支，立即映射 `500 LLM_AUTH_FAILED`，不落入 retry。

| 受控序列 | calls | sleeps | 最终结果 |
|---|---:|---|---|
| timeout -> success | 2 | `[1]` | 正常 answer |
| 429 -> 429 -> success | 3 | `[1, 2]` | 正常 answer |
| 503 -> 503 -> 503 | 3 | `[1, 2]` | 502 LLM_UNAVAILABLE |
| 403 | 1 | `[]` | 500 LLM_AUTH_FAILED |

单测里的 Mock 负责给出受控序列；实际循环、sleep 调用参数和 AppError 是被测代码生成的。这里的 429/503/403 不能称为真实 DeepSeek 响应。

### 5.5 CORS：测试应该区分“配置存在”和“配置被消费”

[main.py](../../backend/app/main.py) 的变化很小：`allow_origins=["*"]` 改为 `allow_origins=settings.CORS_ORIGINS`。但 [test_cors.py](../../backend/tests/test_cors.py) 验证的是 observable behavior：新进程传入允许列表，允许 origin 预检成功，未允许 origin 返回 400 且没有 allow-origin header；未配置时保留 wildcard 默认。

测试采用新进程和临时 cwd，避免 app import 缓存以及仓库 `.env` 覆盖默认场景。它没有改用户的 `.env`。这把 Phase 0 的配置知识接回 Phase 12 的最终验收，而不是新增一个 CORS 功能。

### 5.6 前端检查：组件契约和浏览器行为是两层

[verify_t1204_contracts.cjs](../../frontend/scripts/verify_t1204_contracts.cjs) 加载实际 FileUpload TSX 和 Ant Design 常量，但控制 React hooks/state 与 API boundary。51 MiB 输入触发实际 `beforeUpload`：返回 `Upload.LIST_IGNORE`，错误 Alert 的 description 正确，API 调用为 0。50 MiB 返回 true。

这能证明组件 handler/state 契约，不能证明浏览器成功选中了文件。实际 browser file chooser 被扩展权限阻止，该限制仍记录在 [browser.md](../verification/T1204/browser.md)。不要通过改名为“E2E”掩盖没有执行的交互。

## 6. Verification Learning：按主张复用证据

以下是上轮实际执行记录，本次复核来源与源码适用性，**没有再次执行**：

| 主张 | 证据 | 能支持的结论 |
|---|---|---|
| 真实 OCR 与 ingestion | [T1201 live 91/91](../verification/T1201/live-final.txt) | 实际 Qwen 文本、三态、受控真实超时、rollback/re-upload |
| 真实 QA | [T1202 live 70/70](../verification/T1202/live-reviewed.txt) | fixture grounding、history、sources、实际 provider compatibility |
| 错误处理 | [15/15](../verification/T1204/t1202-faults.txt)、[42/42](../verification/T1204/t1204-final.txt) | 确定性 retry/auth/OCR/error contracts；没有自然 remote 故障的声明 |
| 真实本地模型 | [BGE 4/4](../verification/T1204/bge.txt) | 固定模型 revision、512d、norm、singleton、受控语义排序 |
| 当前回归 | [backend 83/83](../verification/T1204/backend-final.txt)、[最终报告](../verification/T1204/README.md) | 已记录的后端/前端/Phase 12 suites 通过；计数不可相加当 AC 覆盖率 |
| 前端 | [browser 6 场景](../verification/T1204/browser.md)、[component 2/2](../verification/T1204/frontend-component.txt) | 实际导航/QA/错误 UI，与确定性上传边界分别成立 |
| 全量 coverage | [104 行矩阵](../verification/T1204/ACCEPTANCE-MATRIX.md)、[DoD](../verification/T1204/DOD-MATRIX.md) | 每个 mandatory occurrence 的 requirement -> implementation -> evidence -> result |

复用旧 live 证据时，不能只检查文件存在。要确认关键源码是否改变；若改变，分析是不是相关执行路径，再决定是否重跑。[validity record](../verification/T1204/live-evidence-validity.json)记载 ingestion/QA/embedding/store 和 raw live logs 未变，只有 CORS 初始化接线改变且另有回归。

**不升级的结论：**有限 fixture 不是统计准确率；一次抵抗恶意文本不是安全保证；context 字符边界测试没有验收该条答案的全部事实；同名删除成功不证明所有 mid-cascade 故障都有补偿。[PROJECT FACT]

## 7. 架构与工程含义

验证资产也有职责：fixture 负责构造输入，probe 负责执行和观察，report 负责给证据解释及覆盖矩阵。报告不能修改历史 raw log，把当时失败的 exit code改为成功；脚本也不能自己发明 frozen requirements。

将所有替代品删掉并不自动提升测试质量。真实 provider 最适合验证兼容性和实际答案；可控制的错误序列最适合验证分支、重试上限和错误映射。反之，只运行 doubles 又无法证明模型真的能识图或基于知识回答。

完整 ADR、规模分析、故障分类和新增 Known Gaps 归独立 Engineering Review。Learning Review 当轮没有创建该文档；后续已完成 [Phase 12 Engineering Review](engineering-review/phase-12-engineering-review.md)，其中未修复风险单独记账，不借学习复盘给未验证场景背书。

## 8. Technical Decisions：本 Phase 值得记住的取舍

| 决策 | 为什么 | 保留的边界 |
|---|---|---|
| 512d BGE 基线 | 官方保留模型实际输出512d；产品授权更正冻结合同 | 不把旧384d数据直接混入新collection |
| bytes-open PDF | malformed parser异常不再持有原始文件路径句柄 | 额外内存副本 |
| live + deterministic | 分别回答模型行为和应用错误控制流的问题 | 不冒称自然429/5xx/403 |
| section-qualified matrix | 复用ID有不同含义 | JSON账本本身不是所有AC自动执行器 |
| 只修已发现的 CORS 偏差 | 已有配置必须影响运行时 | 不扩充认证/部署架构 |

## 9. Interview Notes：晋升有证据的主题

精选为：失败状态证明、Windows资源生命期 bug、真实/确定性证据分工、验收器额外门槛、104/85 coverage、CORS配置接线。完整话术与追问放在 [Interview Guide Phase 12](interview-notes/dx-rag-interview-guide.md#phase-12-learning-review)，这里不复制回答库。

没有晋升为能力声明的内容包括生产级 SLA、大规模质量、安全保证和完整跨浏览器回归。当前可说“T1201–T1204 完成，F-6 经修复和独立增量复审关闭，Phase 12 Gate PASS”；独立学习 fresh-reader 仍待完成，不能折叠成“所有流程都已结束”。

## 10. Self-test：沿整条推理链回答

先独立回答，再对照要点。能背计数但不能指出代码中的分叉，仍不算掌握。

1. **给出一个“HTTP正确但状态错误”的反例。** 422 已返回但 malformed PDF仍锁住；raw未删除。同名重试或状态比较会发现。
2. **空KB与过滤后空结果分别走哪里？** 前者在chunk count preflight返回409且两种调用均为0；后者retrieval完成后继续LLM，200 + sources=[]。
3. **为什么上传同名新文件和rename的UUID预期不同？** 删除/重传是新身份；rename仅迁移collection/source metadata，不重新ingest。
4. **给出0.18的推导并预测sources。** keyword .6，vector 0，fusion .18 < .30；被过滤，不进入sources。
5. **为什么renderer正常不证明provider正常？** 浏览器后端可以受控生成答案；真实模型行为要查看实际provider records。
6. **一次真实401加确定性403证明了什么？** 实际provider auth集成，以及两种输入具有相同non-retry映射；没有观察到真实403。
7. **为什么移除exit2门槛不是篡改测试结果？** 改的是无frozen依据的验收策略；raw log仍exit2、未观察状态不变，失败checks仍失败。
8. **65+39为什么是104而不是85？** 104是section-qualified条目，85是ID集合大小；相同ID的不同语义不能丢失。
9. **如何发现preview偷偷读取raw？** 让raw与persisted chunks分叉；阻断parser等调用；断言返回persisted重建内容。
10. **为什么Settings测试要新进程？** 模块import时已经构造singleton；后改env不会重新初始化；临时cwd还避免.env干扰。
11. **50 MiB validator返回true是否等于上传成功？** 仅允许继续流程；API/storage/provider可能之后失败。
12. **Task DONE是否允许宣布Gate PASS？** 不允许。Task验收、Learning Review与独立Gate的输入/输出各自归属。

**动手练习（无需付费调用）：**

- 从JSON矩阵选 Section 5/12 各一条 F003-03，填 `requirement -> fixture -> assertion -> evidence level`，解释同ID为什么不同。
- 纸面模拟 `429, timeout, success`，给出attempts/sleeps/API结果；再运行已有failure-contract脚本对照类似序列，不改业务配置。
- 阅读`test_cors.py`，预测将生产接线改回硬编码时哪个subTest失败。只作推演，避免遗留故意损坏的代码。
- 从FAILED日志列出raw、Chroma、keyword、同名重传四项观察，指出缺任意一项会遗漏什么错误。
- 给一个候选“PASS”加上证据类型、适用版本和限制；练习把“测试过了”改成可复核的技术说明。

## 11. Future 与本轮收口

[FUTURE] repository-owned browser regression、CI运行矩阵、更多语料的quality评估、semantic manifest自动追踪仍可规划；它们不是本轮已完成事项或额外mandatory gate。Phase Gate Re-review 已独立完成 PASS；Phase 12 Engineering Review 已于后续独立评审中完成工程分析，两者不是新的产品 Feature。

本轮移除学习入口和当前面试介绍中的pre-live状态；把四份Task共同的隔离/证据原则集中讲一次；保留历史精读，新增资源生命期、错误门槛、CORS与component evidence的Phase级教学。当前计数只在证据表引用，详细AC结果归verification目录，完整面试回答归Interview Guide。

Reader self-check：本章有一句话作用、输入输出图、函数定位、可预测的错误序列、证据限制和12道自测；做了链接/状态/只改文档检查。未运行独立fresh-reader代理，不把作者自审称为独立评审。本轮不重跑昂贵验收、不改SPEC/TASKS/application、不提交、不启动下一Task。

保存检查时观察到另一个工作流整理了 T1204 evidence 文档和重复日志，见 [repository hygiene audit](../verification/RELEASE-REPOSITORY-AUDIT.md)。这些外部变更未被覆盖；本轮复核了学习文档的本地文件链接，产品代码、脚本、测试及 SPEC/TASKS 与本轮开始时的哈希一致。
