# DX-RAG Technical Learning Template V2

先读 [Final Learning & Engineering Workflow V2](./phase-learning-pass-workflow.md)。本文件提供两种结构：**Part A 记录 Task 原材料；Part B 产出 concept-centric Phase 教材**。选择与命令匹配的一种，不把整个模板复制成一章。

默认读者熟悉 JS/TS/React，正在学习 Python/backend/RAG。中文解释为主，先概念后符号、先 Why 后 How；保留真实代码深度和准确的前端类比。章节可以随 Phase 调整，不能为凑结构编造概念、事件、备选方案或测试。旧版 11 节与 Interview cadence 不再是未来默认结构，旧文档历史不因此删除。

## Part A — `Txxxx learning pass`：记录刚完成的理解

**时机**：实现已理解、测试与 Task AC 已核对、Task 已 DONE。若证据不足，只记有依据的草稿与缺口，不用文档替 Task 验收。默认更新当前 Phase 文件的 Task 素材区/附录或既有 Task notes；不自动开始 ER 或 Interview synthesis。

### <人类可读的新增组件或能力>

Task reference：Txxxx；记录日期：<date>；历史/当前范围：<本次 slice>。

| 要回答的问题 | 内容要求 |
|---|---|
| 1. 新增了什么？ | 用组件/函数与用户或系统行为解释，再附 Task ID |
| 2. 为什么需要？ | 明确原先缺少的能力、上游/下游契约 |
| 3. 出现哪些新概念？ | 简短解释陌生概念；必要的 Python/framework 语义和准确 TS 类比 |
| 4. 哪些代码承载它？ | File → Class/Function → Responsibility → Important behavior，不只列路径 |
| 5. 数据/控制怎么走？ | 输入 → 转换 → 状态/副作用 → 输出，并标失败出口 |
| 6. 为什么这样实现？ | 记录理由及成本，标 Documented / Inferred / Unknown；完整 ADR 留待 ER |
| 7. 难点或失败是什么？ | 实际 bug、框架意外、边界、调试、确实拒绝的方案；没有真实事件就直说 |
| 8. 如何验证？ | 行为与重要 assertion 在前；命令/结果/时点/真实与替代依赖在后；说明没有证明什么 |
| 9. 还有什么未完成？ | 当前限制、延期 owner、不可用依赖、未知测量分别写 |
| 10. Phase Review 应合并什么？ | core concept、关键 flow、engineering decision、failure lesson、candidate self-test |

三种理解应同时成立：Code（如何运行）、Project（为何需要和连接谁）、Learning（我学到了什么）。素材不应退化成 Goal / Files Changed / AC PASS 摘要。

可用的小图：

```text
<输入> → <route/service> → <transformation> → <state/store> → <输出>
                              └→ <failure / cleanup owner>
```

核心函数精读选最小充分集合，解释设计意图、控制流、状态变化和非显然代码；不要机械逐行念语法。可补一两个预测或手算练习。证据表可使用下列字段，标签遵循 workflow/Gate 的不同维度：

| 行为 | 代码 / test / artifact | 范围与依赖 | 结果 / 日期 / 是否本次执行 | 未证明 / 延期 owner |
|---|---|---|---|---|
| <行为> | <真实链接与符号> | <UNIT + MOCKED store 等> | <有记录才写结果> | <明确边界> |

Task ID 可以保留，但不代替技术名词。以上是 Phase consolidation 的原材料，不是最终 Phase 教材。

## Part B — `Phase X learning review`：形成一章技术教材

**前置**：全部 Phase Tasks DONE，Gate 状态明确，必要 remediation/tests/re-review 已按授权处理。阅读 Task 原材料、当前代码、SPEC 和证据后，执行 collect → deduplicate → reorganize → explain → consolidate。未解决 Gate 阻断项不能被学习完成状态覆盖。

**输出**：当前 canonical Phase Technical Learning，不在完整 Task 日志末尾再追加一篇总结。Task/history 放附录；旧独立学习入口先核对所有权，避免双份 canonical 内容。

以下标题是默认路线，按实际机制合并/细分；不要强制每个未来 Phase 都长得一样。

### 1. 这一阶段到底解决了什么问题？

用短段落解释目的、读者应能理解什么、必要前提。开头不放 Task/Gate 状态表。

### 2. Before → Problem → After

Phase 之前系统能做什么、缺哪种能力、之后行为怎样改变。区分当前能力、原收官范围与后续消费，不用 Task ID 链解释功能。

### 3. 先理解必要的基础知识

只教该 Phase 需要的概念。先解释术语，再引入类名或内部状态。使用小例子和准确类比；不要假设读者读过 TASKS 或记得内部工作流。

### 4. 在整个系统中的位置

用组件名画架构/依赖图：谁提供输入，谁执行转换，谁消费输出，哪些能力在先前存在、此 Phase 引入或后续实现。给出可复述的 mental model，而不是任务时间线。

### 5. DX-RAG 最终怎么实现？

完整数据/控制路径，每个重要步骤说明 What / Why / Owner。描述当前真实符号、state/storage boundaries、正常与失败出口。历史演进单独记账。

### 6. 用一条数据走完整流程

输入 → 转换 → 内部状态 → 输出。优先小而可手算的例子，清楚标明是真实验证 fixture 还是与实现一致的教学样例，不冒充生产观察。跨阶段实例只用于说明实际连接。

### 7. 核心代码怎么读？

| Concept | File | Class / Function | Responsibility |
|---|---|---|---|
| <概念> | <真实文件链接> | <实际符号> | <关键行为与原因> |

选关键代码精读，代码引用准确、片段短而有用；解释必要 Python 语义、状态与异常传播，连接回概念，不仅给出路径清单。

### 8. 为什么这么设计？

Problem → Alternatives → Decision → Reason → Trade-off。只解释理解机制必需的理由，完整 ADR 指向 ER。区分文档记录、推断、未知，以及实际评估过的方案与教育比较；不宣称未经测量的最优性。

### 9. 容易搞错的地方

列实际相关的误解及正确边界，避免内部 ID 充当解释。机制简单时可与下一节合并。

### 10. Failure scenarios

| Symptom | Cause | Owner | Current behavior |
|---|---|---|---|
| <具体失败> | <原因与证据性质> | <组件> | <异常/返回/清理/残留状态> |

区分历史观察、测试覆盖和推导风险。适用时明确谁 mutation、invalidate、rollback，哪些失败不受保护。

### 11. 测试到底证明了什么？

行为先于数量：解释关键 assertions 为什么支持结论，再列证据类型、执行时点和范围。不把 unit/替代依赖/受控组合写成全链真实验证；明确没证明什么、是否本次重跑。重型 AC/Gate ledger 放附录。

### 12. 当前局限

分别列 Current limitation / Future improvement / Not yet measured，不把未来功能或后续证据追记为本 Phase 原始能力。

### 13. 如果规模扩大怎么办？

当前假设 → 首先可能出现的问题 → 如何观察 → 何时考虑变更。给理解当前设计所需的摘要，详细规模/一致性方案引用 ER，不虚构 SLA、benchmark 或任意倍数阈值。

### 14. Self-Test

约 10–15 道主动回忆题，从概念到代码、行为预测、边界与设计推理。不紧跟每题写答案，不变成 interview script。附适当手算、REPL 或测试替身练习；练习不要求直接修改产品代码。

### 15. 一页复习

用紧凑表格/图重建 Phase 目标、核心概念、关键 flow、state/ownership、设计选择与成本、验证/限制和下游连接。

### Appendix — Engineering References

可按需拆分为代码地图、Task/SPEC/AC/Gate/evidence traceability、historical notes。状态和 ID 在此支持正文，不能成为正文的前提。

| 工程概念 / 行为 | Task / SPEC / AC | Source / Test / Gate | 时点与证据边界 |
|---|---|---|---|
| <概念先行> | <坐标> | <可核对链接> | <closure/current/later> |

保留失败、勘误、延期与后续补证；内嵌旧 Gate 记录保留原文与链接。机制详情归本文，完整 ADR 归 ER，独立验收归 Gate，完整表达话术归项目 Interview Guide。

## 完成检查

- [ ] Why-before-how / concept-before-symbol，准确使用学习者既有知识
- [ ] 隐藏 Task/Gate/Finding/AC/证据标签后，Phase 主解释仍然成立
- [ ] 全部重要 Task 素材已承接，但正文按概念组织，不是日志追加
- [ ] 数据流、真实代码、关键 Python 机制、failure owner 与误解均有覆盖
- [ ] 设计理由、事实、推断、未知及未来能力分开
- [ ] 行为先于证据计数；原收官、当前代码、后续验证分别记账
- [ ] 重要工程事实与历史未因去重丢失，链接可用
- [ ] 10–15 道 self-test、一页复习与适当练习可用于主动回忆
- [ ] 六个月回访读者无需重建 TASKS 历史即可理解；fresh-reader 问题已处理或诚实标 pending
- [ ] 未自动修改实现/验收/ER/Interview，`git diff --check` 和范围检查完成

## Interview Update Cadence

**历史链接保留，不是未来默认执行规则。** 旧 Phase 文档仍引用此锚点。旧版采用“Task 记 Interview Candidates，Phase 汇总晋升”的 cadence；对已完成 Discovery → Analysis → Decision → Resolution → Verification 的重大工程事件，曾允许即时写入 Interview Guide。T0401 的 SPEC_CONFLICT 是原模板明确保留的先例，既有内容不得因 V2 迁回或删除。

未来按 [Final Workflow V2](./phase-learning-pass-workflow.md) 执行：Task 记录理解与候选问题，Phase 整合概念，ER 形成工程判断；Interview Guide 从 consolidated Learning/ER、当前实现和状态独立派生。learning/review 命令不再自动生成完整面试答案，原事件不作为未来默认即时写入的例外。
