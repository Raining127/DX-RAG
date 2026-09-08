# DX-RAG Final Learning & Engineering Workflow V2

## 0. Purpose

This workflow defines how DX-RAG should generate and maintain learning and engineering-review documentation during future development.

The goal is to solve three problems at the same time:

1. **Development execution must remain strict and traceable.**
2. **Learning documentation must help the project owner genuinely understand the system.**
3. **Engineering Review must preserve design reasoning, trade-offs, failures, evidence, and future evolution.**

These three goals must NOT be collapsed into one document.

The central principle is:

```text
Task execution can be Task-centric.

Human learning must be Concept-centric.

Engineering review must be Decision-centric.

Verification must be Evidence-centric.
```

---

# 1. Final documentation architecture

DX-RAG should maintain four distinct documentation responsibilities.

```text
SPEC.md
"What must the system do?"
        │
        ▼
TASKS.md
"What should the coding agent implement next?"
        │
        ▼
Implementation + Tests
        │
        ├────────────────────────────┐
        ▼                            ▼
Task Learning Pass              Verification / Gate
"What did I just learn?"        "Did we satisfy the contract?"
        │                            │
        └────────────┬───────────────┘
                     ▼
             Phase Learning Review
            "Teach the whole Phase to me"
                     │
                     ▼
             Engineering Review
      "Was this a good engineering design?"
                     │
                     ▼
               Interview Guide
      "How do I explain this to someone else?"
```

These documents must not use the same narrative style.

---

# 2. Responsibility matrix

| Artifact              | Primary Question                                | Primary Audience               | Writing Style         |
| --------------------- | ----------------------------------------------- | ------------------------------ | --------------------- |
| SPEC                  | What must happen?                               | Coding agents / implementation | Contract-centric      |
| TASKS                 | What do we implement next?                      | Coding agents                  | Task-centric          |
| Task Learning Pass    | What did I just build and learn?                | Project owner                  | Task-aware learning   |
| Phase Learning Review | Do I actually understand this Phase?            | Project owner                  | Concept-centric       |
| Gate Review           | Did implementation satisfy acceptance criteria? | Reviewer / agent               | Evidence-centric      |
| Engineering Review    | Why was it designed this way?                   | Project owner / engineer       | Decision-centric      |
| Interview Guide       | How do I explain it clearly?                    | Candidate                      | Communication-centric |

No document should absorb another document's primary responsibility.

---

# 3. Per-Task workflow

For every implementation Task:

```text
Read SPEC / TASK
        ↓
Plan
        ↓
Implement
        ↓
Test
        ↓
Verify Task AC
        ↓
Review Diff
        ↓
Mark DONE
        ↓
Task Learning Pass
```

The Task Learning Pass happens **after the Task implementation is understood and verified**.

---

# 4. Task Learning Pass V2

Command pattern:

```text
Txxxx learning pass
```

The Task Learning Pass is allowed to remain relatively Task-centric because it records what was just implemented.

However, it must still be readable by a human.

Its purpose is:

> Capture fresh understanding while implementation context is still available.

It is NOT the final learning material.

---

## Task Learning Pass should answer

### 1. What did this Task add?

Use human-readable component/function names first.

Then include Task ID.

Example:

> This Task added vector-query projection through the embedding service and VectorStore abstraction.
>
> Task reference: T0701.

Not:

> T0701 implemented T0701 requirements.

---

### 2. Why does the system need it?

Explain the immediate engineering/product problem.

---

### 3. What new concepts appeared?

Explain unfamiliar concepts briefly.

Examples:

* inverted index;
* multipart upload;
* rollback;
* derived state;
* API envelope;
* state ownership.

Do not assume the project owner remembers internal terminology.

---

### 4. What code changed?

Prefer:

```text
File
→ Class / Function
→ Responsibility
→ Important behavior
```

Do not only list filenames.

---

### 5. What is the data/control flow?

Prefer a small diagram.

Example:

```text
Request
  ↓
API route
  ↓
Service
  ↓
Retriever
  ↓
Store
```

---

### 6. Why was it implemented this way?

Capture important rationale while fresh.

If rationale is uncertain, label it:

```text
Documented
Inferred
Unknown
```

Do not invent motivations.

---

### 7. What failed or was tricky?

Record:

* bugs found;
* surprising framework/library behavior;
* edge cases;
* debugging lessons;
* rejected approaches.

Do not invent incidents.

---

### 8. How was it verified?

Explain behavior first, evidence second.

Separate:

```text
CODE
UNIT
MOCKED
SUBSTITUTED
REAL / LIVE
E2E
DEFERRED
NOT_AVAILABLE
```

Do not upgrade evidence strength.

---

### 9. What remains incomplete?

Record limitations and deferred work.

---

### 10. What should Phase Learning Review later consolidate?

Mark:

* core concept;
* important data flow;
* important engineering decision;
* failure lesson;
* candidate self-test question.

This makes Task Learning Pass the **raw material** for the Phase review.

---

# 5. Important rule for Task Learning Pass

Task Learning Pass may say:

```text
T0702 introduced ...
```

But it should still prefer:

```text
Hybrid fusion combines the keyword and vector branches...
Implementation reference: T0702
```

Task IDs are allowed.

Task IDs must never replace technical nouns.

---

# 6. When all Phase Tasks are complete

Once all implementation Tasks in a Phase are DONE:

```text
All Phase Tasks DONE
        ↓
Phase Gate Review
        ↓
If FAIL:
  remediation
  → tests
  → Gate re-review
        ↓
Final Gate state established
        ↓
Phase Learning Review
        ↓
Engineering Review
```

The preferred final sequence is:

> **Gate first → Phase Learning Review → Engineering Review**

Reason:

Gate findings may expose important behavior, bugs, consistency problems, or architectural weaknesses that should later be incorporated into both the learning material and engineering retrospective.

---

# 7. Phase Gate Review responsibility

Gate Review remains separate.

Its job is:

> Did the implementation satisfy the frozen acceptance contract?

It may use:

* ACs;
* test results;
* runtime evidence;
* REAL/MOCKED/SUBSTITUTED distinctions;
* findings;
* remediation;
* PASS / FAIL.

Gate Review should NOT try to become a learning tutorial.

Gate Review should NOT become the Engineering Review.

---

# 8. Phase Learning Review V2

Command pattern:

```text
Phase X learning review
```

This is the most important human-learning artifact.

It should consolidate all Task Learning Pass material into a single coherent technical textbook.

The Phase Learning Review MUST be:

> **Concept-centric, not Task-centric.**

It should assume:

> The reader knows programming basics but may have forgotten every Task ID and internal project-history detail.

---

# 9. Phase Learning Review target experience

After reading it, the project owner should think:

> **“我现在真的知道这个 Phase 在解决什么问题、怎么工作的、代码在哪里、为什么这么实现。”**

The primary cognitive order is:

```text
Why
↓
Problem
↓
Prerequisite Concepts
↓
Mental Model
↓
System Context
↓
Data Flow
↓
Implementation
↓
Code
↓
Design Reasoning
↓
Failure Modes
↓
Verification
↓
Limitations
↓
Self-Test
↓
Engineering References
```

---

# 10. Phase Learning Review default structure

The exact structure may vary by Phase.

Do not force identical headings where they do not fit.

However, the default sequence should be:

## 1. 这一阶段到底解决了什么问题？

Explain the purpose in plain technical language.

No Gate/Task status at the top.

---

## 2. Before → Problem → After

Explain:

```text
Before this Phase
        ↓
What capability/problem was missing?
        ↓
What changed after the Phase?
```

---

## 3. 先理解必要的基础知识

Teach concepts before internal implementation symbols.

Examples:

* embedding;
* inverted index;
* rollback;
* HTTP error mapping;
* controlled state;
* source projection;
* reranking.

---

## 4. 这个 Phase 在整个系统中的位置

Use architecture/data-flow diagrams.

Prefer component names.

Avoid Task-ID chains.

---

## 5. DX-RAG 最终怎么实现？

Explain actual implementation.

---

## 6. 用一条真实数据走完整流程

Whenever practical:

```text
Input
→ transformations
→ internal state
→ output
```

---

## 7. 核心代码怎么读？

Use:

| Concept | File | Class / Function | Responsibility |

Explain code mechanics.

---

## 8. 为什么这么设计？

Use:

```text
Problem
→ Alternatives
→ Decision
→ Reason
→ Trade-off
```

Do not claim experimental superiority without evidence.

---

## 9. 容易搞错的地方

Explicit misconceptions.

---

## 10. Failure scenarios

Teach:

```text
Symptom
→ Cause
→ Owner
→ Current behavior
```

---

## 11. 测试到底证明了什么？

Human-language behavior first.

Evidence classification second.

Explicitly state what evidence does NOT prove.

---

## 12. 当前局限

Separate:

```text
Current limitation
Future improvement
Not yet measured
```

---

## 13. 如果规模扩大怎么办？

Discuss upgrade conditions, not generic future architecture.

---

## 14. Self-Test

Approximately 10–15 active-recall questions.

No polished interview answers.

---

## 15. 一页复习

Compact mental-model rebuild.

---

## Appendix — Engineering References

Only here should the document become heavily traceability-oriented:

* Task IDs;
* SPEC references;
* ACs;
* Gate results;
* test references;
* historical notes;
* evidence provenance.

---

# 11. Phase Learning Review hard rule

The following test must pass:

> If every `Txxxx`, Gate ID, Finding ID, AC ID, and evidence label were hidden, would the main technical explanation still make sense?

If no, rewrite.

---

# 12. Phase Learning Review must consolidate, not append

Repeated Task Learning Passes naturally accumulate:

```text
T0601 notes
T0602 notes
T0603 notes
...
```

Phase Learning Review must NOT simply append another review section underneath them.

It should:

```text
collect
→ deduplicate
→ reorganize
→ explain
→ consolidate
```

The final Phase Learning document should read like **one book chapter**, not a chronological development log.

Historical material can remain in appendices.

---

# 13. Engineering Review V2

Command pattern:

```text
Phase X engineering review
```

Run this after the Phase Gate state is established and preferably after the Phase Learning Review has been consolidated.

The Engineering Review assumes the reader already understands the technical mechanics.

It answers:

> **“这个设计工程上到底好不好？”**

---

# 14. Engineering Review target experience

After reading it, the project owner should think:

> **“我知道为什么这样设计、代价是什么、哪里会出问题、什么情况下需要换设计。”**

Its cognitive order is:

```text
Engineering Question
↓
Decision
↓
Constraints
↓
Alternatives
↓
Why
↓
Trade-offs
↓
Failure Modes
↓
Consistency
↓
Upgrade Triggers
↓
Known Gaps
↓
Evidence
↓
Traceability
```

---

# 15. Engineering Review default structure

## 1. Review Purpose

Very short.

Explain the distinction from Technical Learning.

---

## 2. Executive Engineering Summary

Answer:

* What engineering problem did this Phase solve?
* What were the 3–6 most important decisions?
* What was the biggest trade-off?
* What is the largest current risk?
* When would the architecture need reconsideration?

---

## 3. Decision Map

Example:

| Engineering Question | Decision | Benefit | Cost | Revisit When |
| -------------------- | -------- | ------- | ---- | ------------ |

---

## 4. Architecture / Ownership Context

Only enough context to support engineering reasoning.

Do not reteach the full Phase.

---

## 5. ADRs

Use:

### Engineering Problem

### Constraints

### Alternatives

### Chosen Design

### Why This Fits Current DX-RAG

### Trade-offs

### Failure Modes

### When This Decision Stops Being Good

### Evidence

### Current Verdict

Verdicts may include:

```text
KEEP
KEEP WITH KNOWN LIMIT
REVISIT WHEN ...
TECHNICAL DEBT
FUTURE CANDIDATE
```

These are engineering conclusions.

They are NOT Gate verdicts.

---

# 16. Mandatory Engineering Review question

For every important architectural decision ask:

> **When does this decision stop being good?**

This prevents shallow reviews such as:

> Current solution is simple; future could use Redis.

Instead require:

```text
Current assumptions
↓
Why current design is acceptable
↓
What observable problem changes the equation?
↓
What alternative class should then be considered?
```

No arbitrary thresholds unless measured.

---

# 17. Failure & Consistency Analysis

Engineering Review should synthesize cross-cutting risks.

Ask:

```text
What is durable truth?
What is derived state?
What can become stale?
Who owns mutation?
Who owns invalidation?
Who owns rollback?
What happens under partial failure?
What happens under concurrency?
What happens across process boundaries?
```

Only discuss questions relevant to the Phase.

Distinguish:

```text
Observed finding
Test-covered behavior
Reasoned engineering risk
Future scaling concern
```

Do not convert hypothetical risks into incidents.

---

# 18. Scalability & Upgrade Triggers

Avoid generic statements like:

> Use distributed architecture at scale.

Instead:

```text
Current assumption
→ Current design
→ First likely bottleneck
→ How we would observe it
→ Redesign trigger
→ Candidate architecture class
```

This section should teach engineering judgment.

---

# 19. Known Gaps taxonomy

Engineering Review should distinguish:

## Accepted v1 Limitation

Intentional current scope.

## Technical Debt

Worth improving even without feature expansion.

## Unverified Assumption

Believed/designed but not sufficiently proven.

## Future Capability

Explicitly outside current functionality.

Each important gap should answer:

```text
Gap
→ Impact
→ Why accepted/unresolved
→ Trigger for action
```

---

# 20. Evidence & Verification Boundary

Evidence remains mandatory.

But Evidence should appear **after engineering reasoning**, not define the document structure.

Separate:

```text
What code establishes
What unit tests establish
What mocked tests establish
What substituted integration establishes
What real/live evidence establishes
What E2E establishes
What remains deferred/not available
```

Never upgrade evidence.

---

# 21. Historical evidence rule

Always distinguish:

```text
Evidence available at Phase closure
```

from:

```text
Evidence established later by another Phase
```

Never rewrite later Phase evidence as if it existed earlier.

---

# 22. Engineering Review vs Gate Review

This boundary is permanent.

```text
Gate Review:
Did the implementation satisfy the acceptance contract?

Engineering Review:
What should we learn about the quality,
trade-offs, risks, and future of the design?
```

Engineering Review can analyze Gate findings.

Engineering Review cannot issue or replace Gate PASS/FAIL.

---

# 23. Engineering Review vs Technical Learning

Use this simple rule.

If the section primarily answers:

> How does it work?

Technical Learning owns it.

If the section primarily answers:

> Why was it engineered this way?

Engineering Review owns it.

---

# 24. Engineering Review self-review

End with approximately 8–12 reasoning questions.

Examples:

```text
Why was this architecture reasonable?
What assumption is most fragile?
What trade-off did we accept?
Which failure mode matters most?
What evidence supports that conclusion?
What remains unverified?
When would we redesign it?
```

No interview scripts.

---

# 25. Interview Guide generation

Interview Guide should NOT be continuously used as the primary learning source.

It is a derived artifact.

Preferred input:

```text
All Phase Learning Reviews
+
All Engineering Reviews
+
Current implementation
+
Current project status
```

Then transform:

```text
Understanding
→ Engineering judgment
→ Interview communication
```

Not:

```text
Task logs
→ memorized interview answers
```

---

# 26. Recommended future Phase lifecycle

For every future Phase:

```text
PHASE START
│
├── Read SPEC
├── Read Tasks
│
├── Task 1
│     ├ Implement
│     ├ Test
│     ├ Verify AC
│     ├ Mark DONE
│     └ "Txxxx learning pass"
│
├── Task 2
│     └ same
│
├── Task N
│     └ same
│
├── All tasks DONE
│
├── Phase Gate Review
│     │
│     ├ PASS
│     │
│     └ or FAIL
│          ↓
│        Remediation
│          ↓
│        Gate Re-review
│
├── Final Gate state established
│
├── "Phase X learning review"
│     ↓
│   Raw Task Learning
│     →
│   Concept-centric Technical Learning
│
├── "Phase X engineering review"
│     ↓
│   Decisions / Trade-offs / Failures
│   / Scale / Known Gaps / Evidence
│
└── Phase complete
```

---

# 27. What each command should mean

## `Txxxx learning pass`

Meaning:

> Capture what I just learned while implementation context is fresh.

Allowed:

* Task-centric references;
* source details;
* implementation mechanics;
* debugging notes;
* early design reasoning.

Not allowed:

* pretending this is the final Phase textbook;
* large project-history reconstruction.

---

## `Phase X learning review`

Meaning:

> Rewrite/consolidate the Phase learning material so that future me can genuinely relearn this Phase.

Must:

* remove Task-centric narrative from main body;
* explain concepts before symbols;
* explain Why before How;
* consolidate duplicated Task notes;
* preserve evidence in later sections/appendices;
* build self-test.

---

## `Phase X engineering review`

Meaning:

> Independently evaluate the engineering design now that implementation and Gate evidence exist.

Must:

* focus on engineering questions;
* preserve ADRs;
* discuss alternatives and constraints;
* identify trade-offs;
* analyze failures/consistency;
* define upgrade triggers;
* classify Known Gaps;
* preserve evidence boundaries.

---

# 28. Cross-document duplication rule

Some duplication is healthy.

But each document should own one depth.

Example:

### Learning

> Keyword Index is derived state and can be reconstructed from chunks.

### Engineering Review

> Making Keyword Index derived state avoids maintaining a second durable source of truth, but creates invalidation/rebuild responsibility and may become problematic under multi-process deployment.

This is good duplication.

Bad duplication:

Both documents spend three pages explaining exactly how `_dirty_collections` is mutated line by line.

---

# 29. Terminology hierarchy

Prefer this order:

```text
Human-readable concept
↓
Component / class / function
↓
File
↓
Task ID
↓
SPEC / AC
↓
Gate / Evidence reference
```

Never reverse it in Learning material.

Engineering Review may use internal references earlier, but the engineering concept still comes first.

---

# 30. Evidence vocabulary

Maintain a single stable vocabulary across future documentation.

Recommended conceptual levels:

```text
CODE / STATIC
UNIT
MOCKED
SUBSTITUTED
REAL / LIVE
E2E
DEFERRED
NOT_AVAILABLE
```

Do not silently change old terminology.

If historical documentation uses another term, preserve historical wording and explain mapping where necessary.

---

# 31. Verification honesty rule

Every statement about testing must answer:

> What behavior did this evidence actually establish?

Not just:

> Tests passed.

Avoid:

> Fully verified.

Prefer:

> Unit tests establish X and Y; they do not establish real provider integration or semantic retrieval quality.

---

# 32. Current truth vs historical truth

Documentation should distinguish:

### Historical state

What was true when the Task/Phase closed.

### Current implementation truth

What the repository implements today.

### Later verification

What subsequent Phases established.

Do not erase history.

Do not force learners to read history before understanding current mechanics.

---

# 33. Learning quality gate

Before accepting a Phase Learning Review, verify:

* Why-before-how?
* Concept-before-symbol?
* Task IDs removable without breaking comprehension?
* Real code mapped?
* Concrete data flow?
* Important failures explained?
* Evidence boundary honest?
* Limitations explicit?
* Self-test included?
* Six-month-return test passes?

Six-month-return test:

> Could the project owner return after six months and relearn this Phase without first reconstructing TASKS.md?

---

# 34. Engineering Review quality gate

Before accepting an Engineering Review, verify:

* Engineering-question-first?
* Important ADRs preserved?
* Alternatives distinguished honestly?
* Trade-offs explicit?
* Failure/consistency analysis present?
* "When does this stop being good?" answered?
* Upgrade triggers observable?
* Known Gaps categorized?
* Evidence preserved?
* Historical integrity preserved?
* Not another tutorial?
* Not another Gate report?

---

# 35. Final mental model

The entire workflow should teach the project owner three progressively deeper levels.

## Level 1 — I understand it

Generated primarily by Technical Learning.

```text
What?
Why?
How?
Where in code?
```

## Level 2 — I can judge it

Generated primarily by Engineering Review.

```text
Why this design?
What trade-off?
What can fail?
When should it change?
```

## Level 3 — I can explain it

Generated later by Interview Guide.

```text
Can I explain the problem,
design,
trade-off,
failure,
evidence,
and improvement
clearly to another engineer?
```

Do not jump directly from implementation to Level 3.

---

# 36. Final rule

The documentation pipeline must preserve two things at the same time:

```text
Human understanding
+
Engineering truth
```

Never improve readability by deleting engineering truth.

Never improve traceability by making the human reconstruct the system from Task IDs.

The final DX-RAG workflow is:

```text
SPEC
↓
TASK
↓
IMPLEMENT
↓
TEST
↓
VERIFY
↓
TASK LEARNING PASS
↓
PHASE GATE
↓
PHASE LEARNING REVIEW
↓
ENGINEERING REVIEW
↓
SELF-LEARNING
↓
INTERVIEW SYNTHESIS
```

The expected outcomes are:

```text
Task Learning Pass:
"I know what I just did."

Phase Learning Review:
"I understand how this part of DX-RAG works."

Engineering Review:
"I understand whether this was a good design and its limits."

Interview Guide:
"I can explain and defend it."
```

Use this workflow for all future DX-RAG Tasks and Phases.

---

# Appendix A — Repository execution binding（2026-09-08）

上文第 0–36 节保留用户提供的 Final Workflow V2，作为未来 DX-RAG 学习与工程文档的规范；本附录把它接到现有仓库路径和命令。保留原 workflow 文件路径，避免已有入口失效。V2 取代旧版固定 11 节、Phase 正文按 Task 排列、学习阶段自动更新 ER/Interview 的默认要求；产品契约仍以 SPEC 为准，Task 状态仍以 TASKS 为准。

## A.1 命令、时机与写入范围

| 命令 / 事件 | 前置条件与动作 | 主要输出 | 不隐含的动作 |
|---|---|---|---|
| 完成一个 implementation Task | 读 SPEC/TASK → Plan → Implement → Test → Verify AC → Review Diff → Mark DONE，然后记录 Task Learning Pass | Task 实现报告 + 当前 Phase 的 Task 学习素材 | 不自动启动下一 Task/Phase，不用学习文档代替验收 |
| `Txxxx learning pass` | 核对该 Task 已实现、被理解且有相应验证；按学习模板 Part A 记录新理解 | 当前 `docs/learning/phase-XX-name.md` 的 Task 素材区/附录，或已存在的 canonical Task notes | 不将增量笔记当作最终 Phase 教材；不默认写 ER/Interview |
| `Phase X learning review` | 全部 Tasks DONE，Gate 结果已明确；若 FAIL，先按授权完成修复、测试与独立 re-review | 按模板 Part B 重组 canonical Phase Technical Learning，形成一章 | 不只在 Task 日志末尾追加总结；不改变 Gate/Task 状态 |
| `Phase X engineering review` | Gate 状态已建立，优先在 Phase Learning Review 后；独立查代码与证据 | `docs/learning/engineering-review/phase-XX-engineering-review.md` | 不生成另一本教程，不重新发 Gate PASS/FAIL |
| Phase Gate / Gate Re-review | 严格使用独立 Gate protocol；FAIL 的修复与重审是不同事件 | 独立验收结论、finding 与 evidence | 默认 REVIEW-ONLY，不因流程图自动获得修改实现的授权 |
| Interview synthesis | 作为独立派生产物，优先读取各 Phase Learning/ER、当前实现与项目状态 | `docs/learning/interview-notes/dx-rag-interview-guide.md` | 不把 Task logs 直接变成背诵稿，不作为 learning/review 命令的默认副作用 |

`Phase X learning pass` 若沿用旧称，按 Phase Learning Review 的 consolidation 语义和前置条件处理；不会因名字相近而退回按 Task 写整章。仅要求某个 Task 时只执行 Task 级学习。

单独请求 learning/review，或本来允许写文档，不会授权修改 application code、测试、SPEC/TASKS、Gate 记录或自动修复缺陷。发现冲突时记录具体来源与影响，不替产品改要求。不重复索取本会话已经明确给予的授权，也不因完成文档而自动启动后续命令、commit 或 push。

若前置证据不足，可完成有证据支持的草稿、问题分析和缺口记录，但必须说明尚未满足最终收口条件。明确的 FAIL 可以作为回顾材料；未解决的阻断项不能被文档完成状态改成 Phase complete 或 next-Phase ready。

## A.2 模板、产物和深度所有权

- [phase-learning-template.md](./phase-learning-template.md)：Part A 是 Task 原材料表单，Part B 是 Phase concept-centric 默认结构，不把两套结构机械拼成一章。
- [phase-engineering-review-template.md](./phase-engineering-review-template.md)：decision-centric Review、ADR、失败/一致性、升级条件和 Known Gaps。
- [phase-gate-review-template.md](./phase-gate-review-template.md)：验收职责、标准结果与 evidence vocabulary；本次 V2 接入不修改该协议。
- Phase Learning Review 是整理过程，主要产物仍是 canonical Technical Learning；已有独立 `phase-XX-learning-review.md` 入口时先核对当前 README 的所有权，避免同时维护两份互相竞争的教材。
- Task 素材在当前 Phase 文件的明确区段/附录中积累；Phase consolidation 把有价值内容合并进概念主线，把历史留在附录。已有 Task 笔记路径可沿用，不强制另建文件。
- Engineering Review 每 Phase 一份。Task 的早期工程判断先留在 Task Learning Pass，正式 ER 在 Gate/Phase consolidation 后独立形成；既有增量 ER 历史保留，不追溯改流程。
- Interview Guide 仍是项目级派生产物。原模板的 T0401 即时晋升例外及既有候选/STAR 是历史资产，保留原事实；不继续作为未来普通学习命令自动生成面试答案的默认 cadence。

继承早期文档的教学深度，不继承过时结构：[Phase 5](../phase-05-file-upload.md) 可参考真实代码精读、Python/TS 桥梁和 failure/evidence 深度；[Phase 6 Technical Learning](../phase-06-keyword-retrieval.md) 与 [Engineering Review](../engineering-review/phase-06-engineering-review.md) 是 V2 两种阅读体验的试点，不是强制行数、ADR 数量或统一章节标题模板。

默认读者熟悉 JS/TS/React、有一般编程和少量 Python/Node 经验，正学习 backend/RAG。主要用中文，保留准确代码标识符和必要术语；在首次需要时解释 Python-specific semantics。准确的前端类比可帮助理解，但不能掩盖生命周期或并发差异。可使用 🟢 必会 / 🟡 了解原理 / 🔵 知道存在 管理负担，不以面试频率决定学习主线。小 Phase 可以短，但不得省略关键控制流、状态或失败推理。

## A.3 写作前的证据包

先读 CLAUDE、相关 TASKS、其引用的 SPEC/AC、当前 implementation、tests/verification scripts 与 runtime artifacts、现有 Learning/ER、Gate findings/remediation；必要时读前后 Phase 和 Git history。当前 DONE、旧 Completion Report、ER 或 Gate verdict 只是定位材料，不能替代事实核验。

建立内部 claim map：`行为/结论 → 代码/测试/日志来源 → 证据类型与时点 → 文档 owner`。分开写规格要求、代码机制、设计理由和验证结果；理由用 Documented / Inferred / Unknown，不把推断写成团队当年实际决定过的动机。

优先精读足以解释核心机制的少量函数/类，常见是 1–3 个，但不为数量删减或凑数。按“概念 → 系统角色 → 数据/控制/状态变化 → 真实符号 → 非显然代码机制 → 设计理由”讲解；代码片段保持准确，设计意图比逐行念语法重要。教学样例可以小而可手算，但要与实现一致并标明是教学 fixture，不能冒充实际用户数据或运行日志。

## A.4 证据词汇怎样与 Gate 保持一致？

第 30 节的词汇不是一条从弱到强的自动升级阶梯，而包含不同维度：

| 维度 | 用词与写法 |
|---|---|
| 代码检查 | CODE / STATIC；Gate 的 Evidence Type 使用原协议的 `STATIC` |
| 测试范围 | UNIT、integration、E2E；写明起点/终点，不等于依赖全真 |
| 依赖与执行路径 | MOCKED / SUBSTITUTED / REAL；LIVE 明确外部服务实际交互 |
| 尚待执行 / 环境不可用 | DEFERRED（明确 owner）、NOT_AVAILABLE（明确缺失项） |
| 结果 | 沿用原测试/审计结果，不用证据类别代替结果；Gate AC Result 只按 Gate protocol |

例如 `UNIT + MOCKED VectorStore` 和 `API integration + REAL Chroma + SUBSTITUTED embedding` 应分别说明。E2E 必须列出实际链路，应用/API E2E 不能冒充 browser/TCP/CORS E2E。NOT_AVAILABLE 不等于 PASS；未验证也不一律写 DEFERRED：只有有明确延期 owner 时才这样记，当前应验未验的要求仍按 Gate 规则判断。

旧 `[PROJECT FACT]` / `[ENGINEERING KNOWLEDGE]` / `[FUTURE]`、`NOT AVAILABLE`、partially verified 等历史词保留，必要时解释映射。Verified 应同时注明验证方法；源码核对不能混写为已执行测试。测试存在但本次未运行，写 existing coverage / not independently rerun；引用历史执行要记日期与来源，不冒充当前 checkout 再次通过。

每次新执行记录 exact command、环境、结果、exit status、计数口径、真实/替代边界。文档维护本身不要求重新调用 provider 或扩跑全部 suite；根据结论需要和已有授权选择必要验证。不同阶段的证据分别记账，不删历史失败、勘误、补偿或后续恢复记录。

## A.5 保留审计、读者检验与交付

1. **Loss audit**：对照原稿，检查核心概念、ADR、替代方案性质、trade-off、失败、一致性、延期、source links、Task/SPEC/AC/Gate 与证据历史。合并重复内容先确保 `COPY → VERIFY → LINK → REMOVE DUPLICATE`；旧 Gate 若内嵌在目标文档，保留原记录及可用链接，不用新评审覆盖它。
2. **Learner audit**：Phase 正文隐藏 Task/Gate/Finding/AC/证据标签后仍能解释问题、机制和真实代码；技术名词先解释再引入内部符号。Self-Test 约 10–15 题，配适当预测/手算/REPL 练习，不把答案紧跟每题。
3. **Engineering audit**：重点决策都有约束、诚实替代方案、成本、失败和“何时不再合适”；Known Gaps 四分类，升级条件可观察。Self-Review 约 8–12 个推理问题，不生成采访或面试脚本。
4. **Fresh-reader test**：沿用原 workflow 的独立读者要求。用不带写作上下文的读者核对概念、代码定位、证据与历史是否可理解；Engineering Review 另检验判断/限制/升级条件，勿以教程标准要求它从零教学。发现关键歧义后定点修正并复核。未执行则明确 pending，不能宣称完整 reader-test DoD 满足；它不替代事实或运行验证。
5. **Repository check**：`git diff --check`；检查 tracked/staged/untracked 及完整相关 diff，以本轮起点区分既有修改；确认只改授权文档。必要索引/链接做最小同步，不能以“同步”为由自动改其他 Phase、ER、Interview 或验证记录。
6. **Report**：说明实际文件、结构变化、保留的事实/历史、证据边界、验证与未执行项，以及任何有意删减。Task DONE、Gate verdict、Learning consolidation、Engineering Review 和 Interview synthesis 各自记账；不以一个完成替代其他状态。

V2 默认治理未来 Tasks/Phases；既有文档只有被明确指定迁移时才按新结构整理。不追溯删除旧面试内容、不批量重写历史 Phase、不更改已有验收结论。最终标准同时包含人能理解与事实可追溯。
