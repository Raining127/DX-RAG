# DX-RAG Phase Learning Pass Workflow

> **Canonical use**: 当用户要求执行某个 Task 或 Phase 的 Learning Pass 时，Agent 必须先阅读并遵循本文。
> **适用范围**: 未来 Learning Pass，以及用户明确要求的历史 Learning rework；不追溯重写现有 Phase 0–6 文档。
> **配套结构模板**: [phase-learning-template.md](./phase-learning-template.md)
> **深度 / 风格基准**: [phase-05-file-upload.md](../phase-05-file-upload.md)

本文定义 Agent **怎样执行** Learning Pass：怎样收集证据、建立学习路线、精读代码、解释验证、维护文档边界并检查产出质量。

`phase-learning-template.md` 定义学习文档**长什么样**。两者不能互相替代：workflow 负责方法与深度，template 负责 11 节结构与填写位置。

---

## 0. Learning Pass 的目的

Learning Pass 是一次**基于真实实现、面向学习者的技术教学整理**。完成后，学习者应能打开被引用的代码，独立解释：

1. 代码做什么；
2. 代码怎样运行；
3. 项目为什么需要它；
4. 它怎样连接之前与之后的 Phase；
5. 当前需要掌握哪些 Python / FastAPI / backend / RAG 概念；
6. 关键实现为什么这样写；
7. 怎样沿 control flow、data flow、state change 与 tests 自己推理代码。

每个 Task 的教学必须同时建立三种理解：

- **Code Understanding**：代码是什么、如何运行、数据和状态怎样变化；
- **Project Understanding**：为什么项目需要它、兑现什么契约、连接什么上下游；
- **Learning Understanding**：学习者现在应该掌握什么、怎样形成可迁移的 mental model。

Learning Pass **不是**：

- Task Completion summary；
- changelog 或 Files Changed 清单；
- concise implementation recap；
- Engineering Review；
- Interview Guide；
- 脱离仓库的 generic tutorial。

只有 Goal / Files Changed / Short Summary / AC PASS 的 Task 小节属于 completion report，不属于 Learning Pass。

---

## 1. 默认学习者画像与教学语言

默认读者是：

- 前端导向，熟悉 JavaScript / TypeScript / React；
- 有少量 Node.js 经验；
- 没有系统学习过 Python 与 backend engineering；
- 正在通过 DX-RAG 的真实实现学习 modern full-stack + RAG development。

Agent 必须据此写作：

- 以中文解释为主，在准确处保留 English technical terms；
- TypeScript / JavaScript / frontend analogy 只在真正降低学习成本时使用；
- 类比不准确时，直接解释 Python/backend 行为，不强凑对应物；
- Python-specific semantics 必须显式解释，不能假设读者已经熟悉 decorator、context manager、class attribute、exception propagation、typing 或 framework lifecycle；
- 把新概念连接到之前 Phase 已出现的概念，说明“这是第一次出现”还是“旧原则的新应用”；
- 不因 Agent 偏好 concise output，把教材压缩成面向 senior backend engineer 的摘要。

使用深度标记管理认知负担：

- 🟢 **必会**：本 Phase 核心机制、会影响后续理解或面试表达；
- 🟡 **了解原理即可**：能解释目的、主要行为和边界，不要求记住全部细节；
- 🔵 **知道存在即可**：当前只需建立名词与位置感，后续再深入。

---

## 2. 深度 / 风格 precedent

[phase-05-file-upload.md](../phase-05-file-upload.md) 是未来 Technical Learning 的 canonical **depth/style precedent**，不是业务内容模板，也不是固定篇幅模板。

未来 Learning Pass 应在适用处保持它的严谨度：

- 明确读者画像与 Phase 定位；
- 引用真实代码、SPEC、TASKS 和验证证据；
- 按 Task 建立 Code / Project / Learning 三种理解；
- 选择关键函数或 class 做 close reading；
- 解释“why this line exists”，不机械朗读 syntax；
- 对新的 Python 概念做显式教学；
- 用准确的 TypeScript analogy 降低迁移成本；
- 追踪项目依赖、data flow、state/cache/storage boundary；
- 在适用时深入 failure path 与 cleanup responsibility；
- 把 tests 与 verification method 当成学习内容；
- 提供 self-test 与 hands-on exercise；
- 对未实现能力保持诚实的 Future boundary。

不要求每个 Phase 与 Phase 5 行数相同。深度随概念复杂度调整，但不能因为文件少、代码短或 Agent 偏好简洁而跳过核心推理。小 Phase 可以更短，核心概念仍必须讲到学习者能理解、复述和读代码验证。

---

## 3. 文档所有权与边界

| Artifact | Canonical responsibility | Learning Pass 中怎样处理 |
|---|---|---|
| **Technical Learning** | code mechanics、project context、learner concepts、data flow、verification learning、practice | 本 workflow 的主要更新对象 |
| **Engineering Review** | 完整 ADR、trade-off、failure taxonomy、一致性、10x/100x/1000x、Known Gaps | 只写简短 engineering implication 并 cross-link；按既有 cadence 更新其 canonical 文件 |
| **Phase Gate Review** | 独立验收 Tasks、AC、contracts、runtime evidence、repository state，给出 verdict | 不能用 Learning Pass 替代；保持 [Gate protocol](./phase-gate-review-template.md) 的独立性 |
| **Phase Learning Review** | Gate 后做 Phase-level consolidation、去重、统一 mental model、候选面试素材晋升 | 与增量 Task Learning Pass 分开执行 |
| **Interview Guide** | project story、完整回答、STAR、follow-up answer bank | Task 级只记录 Interview Candidates；按 cadence 晋升并 cross-link |

Technical Learning 可以包含：

- 简短 decision summary；
- 对理解代码必要的 engineering implication；
- 简短 Interview Candidates。

Technical Learning 不复制：

- full ADR dossier；
- full failure taxonomy；
- 10x / 100x / 1000x capacity analysis；
- full STAR story；
- complete interview answer bank。

知识迁移遵循：**COPY → VERIFY → LINK → REMOVE DUPLICATE**。先确认 canonical destination 已完整承接，再建立 cross-link，最后才删除重复正文。

---

## 4. 两种执行层级

### 4.1 Task Learning Pass

一个 Task 完成后：

1. 增量更新当前 Phase Technical Learning；
2. 增加该 Task 的 Code / Project / Learning 教学；
3. 只在需要时调整 close-reading、data-flow、architecture sections；
4. 更新因新代码而失效的旧表述，但不把未完成 Phase 写成 complete；
5. 记录 Interview Candidates，不提前生成完整答案；
6. 按当前证据写 verification level；
7. 不自动启动下一 Task。

Task Learning Pass 不是对整章做无差别重写。保留仍准确的历史学习内容，并把“当时状态”与“当前状态”标清。

### 4.2 Phase Learning Consolidation / Phase Learning Review

只有在以下条件满足后执行：

- Phase 全部 Tasks 已 DONE；
- Phase Gate Review 已完成。

Phase Learning Review 才负责：

1. 删除 Task-to-Task duplication；
2. 把零散概念连接成一个 Phase mental model；
3. 将 fragmented explanation 提升为 Phase-level understanding；
4. reconcile prerequisites、current capability 与 downstream dependency；
5. 检查 self-test 是否覆盖整条 Phase reasoning chain；
6. 按 Interview cadence 筛选并晋升 Interview Candidates；
7. finalise document status。

不要把 Task Learning Pass、Phase Gate Review 与 Phase Learning Review 混成一次模糊的“Phase 完成”。历史流程记录保持原样；本 workflow 只治理未来执行和显式 rework。

---

## 5. 写作前：建立证据包

在写任何 project-specific conclusion 前，Agent 必须检查：

1. `CLAUDE.md`；
2. `docs/TASKS.md` 中当前 Phase 的相关 Tasks；
3. Tasks 引用的全部 SPEC sections 与 AC；
4. actual implementation files；
5. actual tests、verification scripts 与已有 runtime artifacts；
6. relevant git diff/history（当它能澄清实现边界、演进顺序或历史状态时）；
7. 建立 prerequisite context 所需的 previous Phase learning documents；
8. existing Phase Technical Learning；
9. current Phase Engineering Review，仅用于导航、cross-link 和边界核对，不能替代读代码。

最低证据原则：

- 不从 Task description 单独推断实现事实；
- 不把 Task Completion Report 当成充分证据；
- 不因 `DONE` 标签跳过代码与测试；
- 不因 Engineering Review 已经解释过就跳过 actual implementation；
- 代码、SPEC、TASKS、tests 之间有冲突时，诚实记录冲突，不替产品做决定；
- 当前状态以 `docs/TASKS.md` 为 Task authority，产品行为仍遵循 `docs/SPEC.md > docs/TASKS.md > CLAUDE.md`。

建议先建立一张内部 evidence map，再开始写：

| Claim / learning topic | Source | Evidence level | Document owner |
|---|---|---|---|
| <行为或概念> | `<file:line>` / AC / command | static / unit / integration / E2E / deferred | Learning / ER / Interview / Gate |

这张表可以是工作笔记，不要求写入最终教材；它的作用是阻止 Agent 从印象直接写结论。

---

## 6. 事实与验证纪律

统一使用三种事实标签：

- `[PROJECT FACT]`：必须由当前 repository evidence 支持；
- `[ENGINEERING KNOWLEDGE]`：通用知识，不能伪装成项目已实现行为；
- `[FUTURE]`：任何未实现能力，不得使用现在时描述为已存在。

验证语言必须与实际证据匹配：

| Evidence level | 可以怎样写 |
|---|---|
| code inspection only | code-level verification / static inspection；不能写 runtime PASS |
| unit test executed | unit-tested，并写明 mock/fake boundary |
| integration test executed | integration-tested，并写明真实依赖与替代依赖 |
| literal E2E executed | real E2E verified，并给出路径、环境和结果 |
| test exists but not rerun | covered by existing test；not independently rerun during this Learning Pass |
| later owner | DEFERRED，并点名 Task / Phase |
| unavailable environment | NOT AVAILABLE，并说明缺什么；不能升级为 PASS |

不允许把 inference 升级为 executed evidence。例如：

- 看见测试文件不等于测试已通过；
- unit test 不等于 API / browser / persistence E2E；
- mocked dependency 不证明 real dependency compatibility；
- 代码路径看起来正确不等于失败路径已经实际执行；
- 历史 PASS 不自动证明当前 checkout 仍 PASS。

如果本次 Learning Pass 重新执行验证，记录 exact command、结果、范围及 mock/real boundary。如果没有重新执行，同样直说。

---

## 7. 从证据生成教学内容

### Step 1 — 定位 Phase 与学习主线

先用一句话回答“这个 Phase 让系统新增了什么能力”。再整理：

- upstream capability；
- 本 Phase 的 transformations 与 boundaries；
- downstream consumer；
- 本轮最重要的 1–3 个 mental hooks；
- 🟢 / 🟡 / 🔵 学习深度。

不要从文件列表开始。学习者需要先知道“为什么要读这些代码”。

### Step 2 — 按 Task 建立三种理解

每个 Task 必须有有意义的覆盖：

#### A. Code Understanding

- important functions / classes / modules；
- inputs 与 outputs；
- control flow；
- state changes 与 side effects；
- 新出现的 Python syntax / semantics；
- implementation 为什么采用当前结构。

#### B. Project Understanding

- Task 为什么存在；
- 消费了什么 upstream contract；
- 兑现了什么 SPEC / Task contract；
- downstream Phase 怎样消费它；
- 它位于整体 data flow 的哪一段。

#### C. Learning Understanding

- 当前必须掌握什么；
- 建立在哪个旧知识之上；
- 常见误解是什么；
- 怎样用准确的 TS/JS mental model 迁移；
- 最后应该记住哪个可复用模型。

### Step 3 — 选择最小但充分的 close-reading set

选择能够解释 Phase 核心机制的最少代码，通常是 1–3 个 function/class；复杂 Phase 可以增加，简单 Phase 不为凑数强行选三个。

每段 close reading 必须：

- 准确引用或链接真实代码；
- 解释 design intent；
- 解释 non-obvious Python behavior；
- 追踪 control flow、state/data transformation 与 side effects；
- 说明看似更简单的写法为什么可能不正确（仅在确实相关时）；
- 连接 SPEC / Task requirement；
- 在有帮助时给出 TypeScript analogy。

核心原则：**Design intent > syntax narration**。不机械解释没有教学价值的每一行，也不为缩短篇幅跳过困难行。

### Step 4 — 画 data flow，并给 mental model

必须给出真实 Phase data flow，适用时用 ASCII diagram 展示：

```text
input
  → validation / normalization
  → transformation
  → state / cache / storage boundary
  → output
  ↘ error / failure exit
```

至少说明：

- input 与 output；
- important transformations；
- state / cache / storage boundary；
- error/failure exits（如适用）；
- upstream / downstream connection。

随后补一个简短 **Mental Model**：读完后，学习者脑中应该把这一 Phase 想成什么？Mental model 不能只是重述流程图，而要把多个细节压成一个可以迁移的概念模型。

### Step 5 — 把 verification 变成学习材料

不要只列“13 tests passed”。挑真正有教学价值的 tests 或 verification design 解释：

- test 在证明哪个 observable behavior；
- assertion 为什么重要；
- 它锁定 implementation detail 还是 public behavior；
- mock / fake / substitute / real dependency 的边界；
- 哪些行为仍未验证。

只有当前 Phase 真实出现时，才讲 public-interface assertion、baseline comparison、subprocess isolation、monkey patching、GUARD/CHECK、real vs substituted evidence 等方法；不得从历史 Phase 搬来凑内容。

### Step 6 — 写 engineering implication，但保持所有权

Technical Learning 应帮助读者理解“为什么这样写”，但完整工程评审仍归 Layer 2。做法是：

1. 在代码附近解释理解该实现所必需的 trade-off；
2. 在 Engineering Review 节保留 decision summary；
3. cross-link 到 canonical ER；
4. 不在 Learning 文档复制完整 ADR、failure taxonomy 或 scale dossier。

### Step 7 — 设计 self-test 与 hands-on practice

存在有意义学习内容时，自测与练习是标准要求，不是装饰性附录。混合使用：

- concept question；
- code-reading question；
- predict output / behavior question；
- design-reasoning question；
- small hands-on exercise。

问题必须测试当前 Phase 的真实理解，而非术语 trivia。优先设计“学习者不重读答案，能否自己推理出来”的题目。

---

## 8. 增量更新规则

更新 existing Phase document 时：

1. 先区分 historical checkpoint 与 current state；
2. 保留仍有学习价值且仍准确的旧内容；
3. 新 Task 改变旧结论时，明确写“当时 / 现在”，不要把历史段落静默改造成从未发生过的新叙事；
4. 更新 Phase positioning、Task learning、close reading、data flow、architecture links、self-test 中受影响的部分；
5. 检查 README index、project map、Python handbook、Engineering Review 与 Interview cadence 是否需要最小同步；
6. 不因为顺手整理而重写其他历史 Phase；
7. 不修改 application code、`SPEC.md` 或 Task status，除非用户另有明确授权。

Historical learning documents 是 evidence / precedent，不是默认 migration target。本 workflow 不授权 retroactive normalization。

---

## 9. Quality Guardrails

以下任一情况都说明 Learning Pass 不充分：

- 只总结 changed files；
- 只复述 `TASKS.md`；
- 没读真实代码却给 generic definitions；
- 没有 code references；
- 没有 learner-specific explanation；
- 在有帮助时仍删除 TS analogy；
- 跳过困难 control flow、state change 或 failure reasoning；
- 只报 test count，不解释重要 verification；
- 因 Agent 偏好 concise output 而无理由缩短；
- 用 Engineering Review 替代 Technical Learning 深度；
- 把 `[FUTURE]` 写成已实现；
- 把 static / mocked evidence 写成 real E2E PASS。

最终质量测试：

> **目标学习者能否读完本文，打开引用代码，并用自己的话解释这个 Phase？**

若不能，Learning Pass 尚未完成。

---

## 10. 完成前审阅与 Reader Test

### 10.1 Agent 自审

- [ ] 三种理解均有覆盖：Code / Project / Learning
- [ ] project-specific claims 都有 repository evidence
- [ ] 重要代码引用准确，line anchors 未明显漂移
- [ ] close reading 讲 design intent，不是 syntax narration
- [ ] Python-specific behavior 对目标学习者讲清楚
- [ ] TS analogy 准确且非强行类比
- [ ] data flow 含 state/storage/error boundaries；mental model 明确
- [ ] verification language 与实际 evidence level 一致
- [ ] self-test / practice 能检验真实推理能力
- [ ] `[PROJECT FACT]` / `[ENGINEERING KNOWLEDGE]` / `[FUTURE]` 未混淆
- [ ] Learning / ER / Interview / Gate 边界未越界
- [ ] Task Learning Pass 与 Phase Learning Review 状态未混淆
- [ ] 未把 historical document 静默重写为当前叙事

### 10.2 Fresh-reader test

使用不带写作上下文的 fresh reader 检查：

1. 它能否说清 Phase 的一句话作用、输入、关键转换和输出？
2. 它能否定位并解释核心代码？
3. 它能否区分 implemented、general knowledge 与 Future？
4. 它能否说明 tests 真正证明了什么、没证明什么？
5. 它能否区分 Technical Learning、Engineering Review、Gate 与 Interview ownership？
6. 是否存在 stale status、unsupported claim、broken link、重复 canonical content 或隐含前置知识？

发现问题后只做针对性修正，再复测。Reader Test 通过不替代事实核验；它只检查文档是否能被正确理解。

---

## 11. Repository Verification 与交付

完成文档更新后：

1. 运行 `git diff --check`；
2. review full diff，包括 untracked learning files；
3. 确认实际变更只覆盖用户授权的 documentation/workflow files；
4. 确认 application code 未被本次 Learning Pass 修改；
5. 确认 `docs/SPEC.md` 未修改；
6. 确认 Task status 未修改；
7. 确认 [Phase Gate Review protocol](./phase-gate-review-template.md) 仍完整且无冲突；
8. 确认 workflow 与 template 的职责仍清楚分离；
9. 报告本次实际更新的 learning artifacts、evidence boundary 与未执行事项；
10. 未经明确授权，不 commit、不 push、不启动 implementation Task 或下一 Phase。

最终报告应以实际 diff 为准，不把 pre-existing worktree changes 归因给本次 Learning Pass。

---

> **Definition of Done**: Learning Pass 只有在“真实证据可追溯、目标学习者能理解和复述、三层边界正确、验证语言诚实、增量状态准确、fresh-reader 无关键歧义”同时成立时，才算完成。
