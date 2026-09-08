# DX-RAG Engineering Review Template V2

先读 [Final Learning & Engineering Workflow V2](./phase-learning-pass-workflow.md)。用于 `Phase X engineering review`，每 Phase 一份 `docs/learning/engineering-review/phase-XX-engineering-review.md`。Gate 状态先建立，优先在 Phase Learning Review consolidation 后执行；已有 Task 工程素材是输入，不代替独立核对当前实现和证据。

读者已理解技术机制。本文回答为何这样设计、成本、失败/一致性边界和何时换设计，不从零教学，不发出新 Gate PASS/FAIL，不自动修改代码。具体节标题以工程问题或决策命名；以下是结构提示，不为凑数量制造 ADR、事件或证据。

## 1. Review Purpose — 本次要判断什么？

简短说明 Phase 范围和本文与 Technical Learning 的不同职责。重型 Coverage/Status/Gate 放附录，区分本次评审时点、原始设计与后续补证。

## 2. Executive Engineering Summary — 当前设计为什么仍合理？

约 2–3 分钟可读完，回答：解决的工程问题、3–6 个最重要选择、最大代价、主要当前风险、重新评估条件。以设计问题开头，不以任务数量或通过率开头；“当前可接受”必须带假设与证据边界。

## 3. Decision Map — 哪些取舍决定了架构？

| Engineering Question | Decision | Benefit | Cost | Revisit When |
|---|---|---|---|---|
| <具体工程问题> | <已实现/已记录的选择> | <项目相关理由> | <真实代价> | <可观察条件或假设变化> |

表格用于导航，不替代 ADR。没有比较实验时不能把收益写成实测优势。

## 4. Architecture / Ownership Context — 谁拥有状态和责任？

只补支撑判断所需的组件关系/ownership 图。适用时标 durable truth、derived state、mutation、invalidation、rollback、process boundary；机制细节链接 Technical Learning。不要机械讨论与本 Phase 无关的数据库或分布式问题。

## 5. ADRs — 为什么选它，什么时候不再合适？

保留已有重要 ADR 编号、结论与演进。按实际决策数量填写，以下字段可以用小节或紧凑列表，但核心成本、失败、重审条件不可缺省。

### ADR-X — <人类可读的工程决策>

- **Engineering Problem**：哪个问题需要作决定？
- **Constraints**：实际 SPEC、部署、依赖、可测试性或规模假设，注明出处；不编造约束。
- **Alternatives**：实际考虑/记录、教育对照、未来候选分别标明；没有实验就不说“评测后淘汰”。
- **Chosen Design**：当前 DX-RAG 实际选择，简述而非逐行讲代码。
- **Why This Fits Current DX-RAG**：项目特定理由，区分 Documented / Inferred / Unknown。
- **Trade-offs**：具体放弃了什么，成本由谁/哪条路径承担。
- **Failure Modes**：何时可能 stale、错误、昂贵、模糊或难维护；标明观察还是推理。
- **When This Decision Stops Being Good**：当前假设 → 可观察问题/需求变化 → 重审条件 → 候选方案类别；无实测不写任意数值阈值。
- **Evidence**：实现/测试/组合/真实集成来源、时点与未证明部分；只提供支撑该 ADR 的证据。
- **Current Verdict**：KEEP / KEEP WITH KNOWN LIMIT / REVISIT WHEN … / TECHNICAL DEBT / FUTURE CANDIDATE 等简洁工程判断。

Current Verdict 不是 Gate verdict。若后续实现改变旧决策，分别记“当时选择/后来变化/当前判断”，不把新知识追记成最初动机。

## 6. Failure & Consistency — 跨组件风险在哪里？

综合 ADR 之间的责任接缝，不逐条重复全部内容。

| Failure / Risk | Cause / 性质 | Current Protection | Residual Risk | Upgrade Direction |
|---|---|---|---|---|
| <具体风险> | <observed finding / test-covered / reasoned / future scaling> | <现有保护与证据> | <仍可能出错部分> | <触发条件与改进类别> |

适用时回答：谁拥有 durable truth、派生状态、写入/失效/回滚？局部失败后留下什么？并发与跨进程会打破哪个前提？推导风险不是事故，构建局部保护不自动等于事务或并发安全。

## 7. Scalability & Upgrade Triggers — 何时要换设计？

| Current assumption / design | First likely bottleneck | How to observe | Redesign trigger | Candidate architecture class |
|---|---|---|---|---|
| <实际前提> | <本实现的成本> | <需观察的指标/行为> | <可识别条件> | <未实现时明确标未来> |

不强制 10x/100x/1000x；旧倍数分析可保留为定性推演。区分复杂度、实测结果和 SLA，不用“以后上 Redis/Elasticsearch/分布式”替代判断。

## 8. Known Gaps — 如何区分影响与优先级？

按 Accepted v1 Limitation / Technical Debt / Unverified Assumption / Future Capability 分类，不把范围外能力都称为 bug，也不把缺少证据写成已验证限制消失。

| Category | Gap | Current impact | Why accepted / unresolved | Trigger for action |
|---|---|---|---|---|
| <四类之一> | <具体缺口> | <影响> | <理由/owner> | <行动条件> |

旧缺口后来补证或修复时，保留历史与新证据；不要一并关闭未覆盖的相邻风险。

## 9. Evidence & Verification Boundary — 我们实际上知道什么？

行为在前，证据标签与数量在后。分别回答代码、unit、mocked、substituted integration、real/live、E2E 各建立什么结论，哪些仍 deferred/not available；引用旧结果注明本次是否重跑。

| Engineering claim | Source / command | Scope + dependency boundary | Result / date | Not established |
|---|---|---|---|---|
| <结论> | <可追溯来源> | <CODE/STATIC、UNIT+MOCKED 等> | <历史或本次执行> | <不能外推的部分> |

独立列 **Phase closure evidence** 与 **Later project evidence**。E2E 写清实际端到端边界；REAL provider 不证明规模或普遍质量。沿用稳定词汇，历史其他用词保留并解释映射。Gate 的字段/结果仍遵循独立 Gate protocol。

## 10. Engineering Lessons — 哪些判断可以迁移？

约 5–10 条有本 Phase 依据的工程教训，讲责任、取舍或证据原则，而非重复“函数用了 X”。后续事件启发的教训注明后续时点；不虚构 STAR 或线上经验。

## 11. Engineering Self-Review — 我能论证这些选择吗？

约 8–12 道推理问题，覆盖合理性前提、最脆弱假设、成本归属、失败边界、证据和重设计。不要直接附完整答案或面试脚本。

## Appendix A — Implementation / Task Traceability

| Engineering concept | File / Class / Function | Task coordinates |
|---|---|---|
| <概念先行> | <真实源码链接与符号> | <Task ID> |

## Appendix B — SPEC / AC / Gate / Evidence References

保存契约引用、AC、Gate finding/verdict、验证命令与 provenance，标清日期/环境/边界。引用已有 Gate，不另发 PASS/FAIL；若旧 Gate 内嵌于被改文档，原文和可用锚点保留，外层解释历史语境。

## Appendix C — Historical Notes

保留原 closure、后续状态、失败/修复/re-review、延期、原词汇和勘误。当前正文不强迫读者先重建历史，但附录必须能追溯重要判断。

## 完成检查

- [ ] 工程问题优先，没有成为另一份教程或验收报告
- [ ] 原有重要 ADR、理由、替代方案与成本保留
- [ ] 重要决策回答了何时不再适用，升级条件可观察
- [ ] failure/consistency 区分观察、测试、推理与规模担忧
- [ ] Known Gaps 有分类、影响、理由和行动触发
- [ ] 证据边界与原历史完整，没有把后续结果追记为收官证据
- [ ] 5–10 条有依据的教训、8–12 道推理问题
- [ ] Loss audit、独立读者检查及必要修正完成或诚实标 pending
- [ ] 链接、`git diff --check`、范围与既有工作树修改检查完成
- [ ] 未借文档评审修改实现、Gate/Task 状态、其他文档或自动开始后续工作
