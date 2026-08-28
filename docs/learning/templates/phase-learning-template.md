# Phase 学习笔记模板（Phase 4-12 用）

> **先读**：[Phase Learning Pass Workflow](./phase-learning-pass-workflow.md)。本模板定义 Technical Learning 文档的 **11 节结构**；workflow 定义 Agent 怎样收集证据、建立教学深度、执行 Task Learning Pass / Phase Learning Review 与完成 quality check。两者必须一起使用。
> 使用方法：Task 完成后可把本模板增量应用到当前 `docs/learning/phase-XX-name.md`；不要等到整个 Phase 结束才记录学习，也不要在 Task 级把整章写成 complete。Phase 全部 Tasks DONE 且 Gate 完成后，再做 Phase Learning Review / consolidation。Phase 5 的 [phase-05-file-upload.md](../phase-05-file-upload.md) 是 canonical depth/style precedent（不是业务内容或固定篇幅模板）。
> 写作纪律（与已有笔记一致）：
> ① **基于真实代码**——每个 project-specific / code-behavior 结论都能指到仓库证据（适用时带文件与行号）；② **区分三层事实**——SPEC 要求（契约）/ 当前实现（代码）/ 通用工程知识（经验），三者不混写；③ **诚实标注**——未实现的能力标 `Future / Not implemented in v1`，AC 未验证就写 DEFERRED，不虚构 PASS；④ **学习风格**——中文解释 + 英文技术术语 + TypeScript 类比 + 工程化思考；⑤ 深度标记：🟢 必会（面试高频）/ 🟡 了解原理即可 / 🔵 知道存在即可。
> 默认读者：熟悉 JavaScript / TypeScript / React、有少量 Node.js 经验，但没有系统 Python/backend 基础的前端开发者。准确的类比用于降低迁移成本；不准确时直接解释 Python/backend 语义，不硬凑。

---

## 0. 三层文档架构（Phase 4 起强制执行——先读这一节）

> 一份文档只承担一种职责。**禁止**再次把 Learning / Engineering / Interview 全塞进同一个巨型文件（2026-08-24 重构的决定，违反即退回"1500 行无人能读完"的老路）。

| 职责 | 文件 | 回答的问题 |
|------|------|-----------|
| **Layer 1 · Technical Learning** | `phase-XX-name.md`（本模板） | 代码是什么、如何运行、数据怎么流、我第一次需要掌握什么 Python/FastAPI 知识 |
| **Layer 2 · Engineering Review** | `engineering-review/phase-XX-engineering-review.md`（**每个 Phase 一份累计文件**，不按 Task 新建） | 作为工程师如何评价这个 Phase 的设计与实现（ADR / 一致性 / Failure Modes / Maintainability / Scalability / Known Gaps） |
| **Layer 3 · Interview Preparation** | `interview-notes/dx-rag-interview-guide.md`（**项目级累计文档**，永远不按 Task/Phase 新建零散文件） | 面试时如何讲这个项目（30 秒 / 1-2 分钟 / STAR / 追问 / 回答边界） |

**边界规则**：

- Layer 1 对工程/面试内容只放**摘要 + 链接**，不展开。以下内容禁止在 Layer 1 全文展开：完整 ADR、企业级扩展方案、大规模容量分析、完整 failure taxonomy、STAR、30 道 interview questions。
- Layer 2 在 Phase 内**增量更新**：T0402 完成后 Coverage 写 "T0401 + T0402"，Phase Gate Review 完成后才把 Status 从 IN PROGRESS 改为 COMPLETE（前提是实际流程支持该结论）。
- Layer 3 写入时机遵守下文 **Interview Update Cadence**：Task 级只记候选素材（Interview Candidates）；Phase 完成后统一 consolidation 再生成完整答案；重大闭环工程事件（如 SPEC_CONFLICT）可即时增量进入。写入时**不复制整个 Learning 文档**，只把新面试资产（STAR、追问、边界话术）加进对应 Phase 深度章。
- 三份文档互相 cross-link（Layer 1 ↔ Layer 2 ↔ Layer 3），不复制三遍完整内容。
- 事实标记贯穿三层：[PROJECT FACT]（仓库可证）/ [ENGINEERING KNOWLEDGE]（通用工程知识）/ [FUTURE]（任何未实现能力，如 PostgreSQL/Milvus/分布式事务/UUID identity/display_name-storage_name，必须标记）。
- **迁移纪律**：COPY → VERIFY → LINK → REMOVE DUPLICATE。先确认高价值内容已进入目标文件，再从原文件删除重复正文。

---

## Interview Update Cadence

> 原则：**Task 记录，Phase 汇总。重大且已经形成完整闭环的工程事件，可以在 Task 完成后即时进入 Interview Guide。**

### Default — Task Level

每个 Task 的 Learning Pass 默认只记录：

#### Interview Candidates

- 值得讲的技术点
- 值得讲的工程问题
- Candidate Interview Questions
- STAR Candidate（如果存在）

这些只是候选素材。

默认不要在每个普通 Task 完成后，为
`dx-rag-interview-guide.md`
生成大量完整面试答案。

### Phase Level

当整个 Phase 完成，并经过对应的：

- Task Verification
- Learning Pass
- Phase Gate Review
- Phase Learning Review
- Engineering Review

之后，再统一：

1. 筛选真正有面试价值的 Candidate；
2. 删除 Task 之间重复的问题；
3. 将零散技术点提升为 Phase / Project 级表达；
4. 更新项目整体介绍和架构描述；
5. 生成或完善完整面试回答；
6. 更新 `dx-rag-interview-guide.md`。

### Exception — Major Closed-loop Engineering Event

如果某个 Task 出现已经形成完整闭环、并具有明显面试价值的真实工程事件，例如：

- SPEC / implementation conflict；
- production-like failure investigation；
- architecture decision with meaningful trade-off；
- rollback / consistency incident；
- dependency incompatibility requiring formal decision；

并且事件已经完成：

```text
Discovery
→ Analysis
→ Decision
→ Resolution
→ Verification
```

则允许在该 Task 完成后立即增量加入：

`docs/learning/interview-notes/dx-rag-interview-guide.md`

但必须基于真实已经发生的事实。

不得提前编写未来 Phase 的面试故事。

> **既有先例**：T0401 的 SPEC_CONFLICT（Discovery → Analysis → Decision → Resolution → Verification，最终 SPEC v1.6）符合本例外，已即时写入 Interview Guide Phase 4 深度章（STAR / 30 秒 / 1-2 分钟 / 高频追问 / Engineering Questions）。该内容**全部保留**，不得删除、回滚或迁回 Learning Document。

---

# Phase X — <Phase 名称>

> **Phase 状态**: <Task-level：Txxxx DONE，剩余 Tasks / Gate 状态如实填写；Phase-level：全部 Tasks DONE + 实际 Gate verdict>
> **本文档状态**: <Task-level：截至 Txxxx Learning Pass 完成，Phase Learning Review 待执行；Phase-level：Learning Pass + Phase Learning Review 完成>
> **配套文档**: [工程评审](./engineering-review/phase-XX-engineering-review.md) · [面试指南](./interview-notes/dx-rag-interview-guide.md)

---

## 1. Phase 学习（本章学什么、怎么学）

> 一句话概括本 Phase 在系统中的角色 + 学习路线图。

- **一句话定位**: <例如：本 Phase 让"知识库"从数据容器变成可管理的 API 资源>
- **核心学习点**: 
  - 🟢 <本 Phase 最重要的 1-2 个概念，面试必考>
  - 🟡 <支撑概念，理解即可>
  - 🔵 <边缘知识点，知道存在即可>
- **前置依赖**: <上一 Phase 的哪些知识是本 Phase 的基础>
- **学习建议**: <先读哪个文件、跑哪个命令、对照哪个 SPEC 章节>

---

## 2. Phase 目标（为什么做这个 Phase）

> 从 SPEC 与 TASKS.md 提炼：业务目标 + 技术目标 + 明确"不做什么"。

- **业务目标**: <解决用户的什么需求，引用 SPEC F0XX>
- **技术目标**: <建成什么技术能力>
- **本 Phase 明确不做**: <引用 SPEC Out of Scope / TASKS 备注——范围纪律是学习重点>
- **SPEC 引用**: <SPEC Section X、F0XX 条款号>

---

## 3. 项目位置（这个 Phase 在系统地图的哪里）

> 对照 project-map 的架构图，标注本 Phase 的位置、上下游。

- **所属层**: <Frontend / API Layer / Service Layer / AI-Data Layer / Storage Layer>
- **上游依赖**: <本 Phase 消费了哪些已有模块的什么接口>
- **下游消费者**: <哪些未来 Phase 会使用本 Phase 的产物（列 Phase 编号）>
- **数据流角色**: <本 Phase 在摄取流水线/查询流水线的哪一段>

---

## 4. Task 学习（每个 Task 学了什么）

> 按 TASKS.md 逐个 Task 过：目标 → 实现 → 学到的新知识。每个 Task 一节。
> **每个 Task 的 Learning 只回答三类问题**（三层架构 0 节的落地规则）：
> - **A. Code Understanding**：代码是什么？如何运行？数据怎么流？
> - **B. Project Understanding**：为什么这里需要它？它连接哪个 Phase？
> - **C. Learning Understanding**：我第一次需要掌握什么 Python / FastAPI 知识？
> 三类之外的（完整 ADR、企业级扩展方案、大规模容量分析、完整 failure taxonomy、STAR、30 道 interview questions）→ 只给摘要 + 链接到 Layer 2 / Layer 3。
> Task section 不能退化成 Goal / Files Changed / Short Summary / AC PASS。具体深度与证据要求见 [Learning Pass Workflow §7](./phase-learning-pass-workflow.md#7-从证据生成教学内容)。

### Txxxx — <Task 名称>

- **Task 目标**: <TASKS.md 原文目标>
- **实现摘要**: <真实实现做了什么，指到文件:行号>
- **新知识**: 
  - <知识点 1>（🟢/🟡/🔵）
  - <知识点 2>
- **TS 类比**（如适用）: <用 TypeScript/前端概念类比，降低理解成本>
- **验证**: <Task 验收结果，AC 编号 + PASS/DEFERRED，诚实记录>
- **Interview Candidates**（可选，保持简短）:

  > Candidate only — not yet promoted to the project Interview Guide. 完整 30 秒答案 / 1-2 分钟答案 / STAR 完整稿 / 10+ follow-up questions 属于项目级 Interview Guide，不在这里写（更新时机见 Interview Update Cadence）。

  - **Technical Points**: <值得讲的技术点>
  - **Engineering Questions**: <值得讲的工程问题>
  - **Candidate Interview Questions**: <候选面试问题>
  - **STAR Candidate**: <如果存在，一句话事件轮廓>

---

## 5. 代码理解（关键代码逐行精读）

> 挑本 Phase **最核心的 1-3 个函数/类**做逐行讲解（参照 phase-00 的精读风格）。
> 原则：不逐行念语法，而是讲"每一行为什么这么写"——设计意图 > 语法含义。

### 精读 1: <函数名>（<文件>:<行号范围>）

```python
# 代码片段（保持真实，不简化）
```

- **逐行讲解**: <按行解释设计意图>
- **关键设计点**: <这段代码里最值得学的 1-2 个点>
- **TS 类比**: <对应 TypeScript 写法>

---

## 6. 数据流（数据在本 Phase 怎么流动）

> 画一条经过本 Phase 的完整数据流（ASCII 图），标注每步的输入输出类型。

```
<输入>
  → <步骤 1: 做什么，输入类型 → 输出类型>
  → <步骤 2>
  → <输出>
```

- **类型变化**: <数据在哪一步发生了本质变化（如 str → List[float]）>
- **错误在哪一步被拦截**: <每个可能失败点的失败形态（异常/状态/静默）>
- **Mental Model**: <读完后，学习者应该怎样在脑中概括这一 Phase；不要只复述流程图>

---

## 7. 架构设计（本 Phase 的架构影响）

> 回答：本 Phase 给系统新增了什么能力？改变了哪些依赖关系？

- **新增能力**: <能力 → 谁消费>
- **契约兑现**: <本 Phase 消费了哪些上游契约？本 Phase 又冻结了什么新契约供下游使用？>
- **设计边界**: <本 Phase 故意不做什么、责任边界在哪（如"谁缓存谁失效"）>

---

## 8. Engineering Review（工程决策复盘）

> 完成实现后，写/更新对应的 `engineering-review/phase-XX-engineering-review.md`，此处放摘要 + 链接。
> 评审六节：Phase 定位 / 为什么需要这个模块 / 核心设计决策（≥5 个，Decision-Context-Problem-Chosen Solution-Why-Trade-off-Future Improvement 格式）/ 架构影响 / 工程问题分析（可维护性/扩展性/数据一致性/错误处理/性能/安全）/ 规模扩大分析（10x/100x/1000x）。

- **本 Phase 设计决策速览**: <决策一句话列表，详见评审文档链接>
- **已知缺陷与工程债**: <诚实列出，每个带修法方向>

---

## 9. Technical Decision（技术决策备忘录）

> 本 Phase 做过的技术选型/取舍——面试时"为什么"类问题的答案库。
> 格式：决策 → 备选方案 → 选择理由 → 代价。

| 决策 | 备选方案 | 选择理由 | 代价/边界 |
|------|---------|---------|----------|
| <如：用 X 不用 Y> | <Y、Z> | <理由，引用规模假设> | <付出什么、何时要重新决策> |

---

## 10. Interview Notes（面试速记）

> 本 Phase 相关的面试问题与话术要点。更新时机遵守 **Interview Update Cadence**：Task 学习时只记 Interview Candidates；本 Phase 完成后（Task Verification → Learning Pass → Phase Gate Review → Phase Learning Review → Engineering Review）统一筛选、去重、提升为 Phase / Project 级表达，再更新 `interview-notes/dx-rag-interview-guide.md`（重大闭环工程事件例外，可即时增量进入）。

- **高频问题**: <本 Phase 最可能被问的 2-3 个问题 + 一句话回答要点>
- **亮点话术**: <本 Phase 值得主动展示的技术亮点（一句话）>
- **诚实边界**: <本 Phase 哪些设计是"已实现"、哪些是"已设计未实现"——面试时的区分话术>

---

## 11. Future Improvement（未来改进方向）

> 基于真实代码的已知限制，列出演进方向。全部标 `Future / Not implemented in v1`，并注明是 SPEC 已规划（引用条款）还是个人复盘建议。

| 方向 | 触发条件（什么时候需要） | 是否 SPEC 已规划 | 相关条款 |
|------|------------------------|----------------|---------|
| <如：异步摄取队列> | <并发/大文件出现时> | 是/否 | <SPEC x.x / 个人复盘> |

---

## 自测题与动手练习

> 存在有意义的学习内容时，本节是标准要求。混合 concept、code-reading、predict behavior、design reasoning 与 small hands-on exercise；测试真实 Phase 理解，不出术语 trivia。

1. <本 Phase 核心概念的自测题>
2. <设计决策类问题：为什么选 A 不选 B>
3. <动手练习：修改/扩展某个行为>

---

## 填写检查清单

- [ ] 每个代码结论能指到 文件:行号
- [ ] SPEC 引用带条款号（F0XX / Section X.X）
- [ ] 所有未来能力都标了 `Future / Not implemented in v1`
- [ ] AC 验证结果诚实（PASS 必须真的验过；未验写 DEFERRED）
- [ ] 测试不只报告数量：解释重要 assertion、observable behavior、mock/real boundary 与尚未验证内容
- [ ] TS 类比准确（不硬凑）
- [ ] 数据流覆盖 input / transformation / state-storage boundary / output / failure exit，并给出 Mental Model
- [ ] 自测与练习能检验概念、代码阅读、行为预测和设计推理
- [ ] 三层边界遵守：完整 ADR / failure taxonomy / STAR / 容量分析不在本文档展开（摘要 + 链接即可）
- [ ] Interview 写入时机符合 cadence：Task 级只记候选；Phase 完成统一 consolidation；重大闭环工程事件才即时进入 Interview Guide
- [ ] Task Learning Pass 未被误写成 Phase Learning Review；Phase consolidation 只在全部 Tasks DONE + Gate 完成后执行
- [ ] 同步更新：README 索引、engineering-review 文档、interview-notes 指南
