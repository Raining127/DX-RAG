# 人工决定记录表 — Candidate 0.1

**当前进度（更新至 2026-09-14）：** 第一轮 40/40 已通过。Q001/Q003/Q007/Q015/Q027/Q031/Q032 采用改写，其余保留原问法；Q001～Q032 为 Answerable=true，Q033～Q040 为 Answerable=false。最终类别见逐题记录。Q001～Q040 的全部 1,520 项等级已批准（40/40 题；各批修订见等级记录）；Q001～Q040 完整 coverage 已批准（40/40，无遗漏正证据）；核心事实、20 个 family 及 Dev/Test 已于 2026-09-14 批准，共享证据及非盲测局限已接受；当前 40 题内语义去重已完成；规模差额、最终语料及已披露适用范围局限已由 SC01/SC02 批准接受；正式冻结与 dataset promotion 仍为 PENDING；第一轮完成不代表 Ground Truth 或正式 Benchmark 已冻结。初始材料中的“全部 PENDING”描述生成时状态；当前 Human 决定以本表为准。

绑定：`novatech-benchmark-candidate-0.1` / `novatech-pilot-0.1` / `t2001-novatech-pilot-01`。
建议来源为本目录 candidates.json；其 SHA-256 见 verification.md。正式 Human 决定只在收到真实明确指令后记录，不覆盖原建议。

Primary reviewer：Human project owner；Q001～Q040 问法、等级及 coverage 决定日期为 2026-09-11；分组/划分决定日期为 2026-09-14，来源与范围见下表，未提供个人姓名。其余待审项不得推定为已批准。
支持批量记录，但必须明确完整题号范围与维度。例如可只批准问法而将等级/coverage 留待下一轮；不得把前者扩展为后者。

**审阅方式更新（2026-09-11）：** Human project owner 对“从 Q005–Q010 开始批量展示、只指出例外”的建议回复「同意」。后续第一轮集中展示问题、证据摘要和类别/可回答性建议，再记录用户针对明确批次的决定。该次仅批准审阅方式，当时 Q005–Q010 仍 PENDING；后续批次第一轮批准见下文，等级和 coverage 未批准。
如改写问题、增删语料或改变 chunk，必须说明哪些判断失效并重新 screening/coverage。

**语义去重进度（2026-09-14）：** SD01–SD20 全部保留已批准，当前 40 题的本轮语义去重审阅完成。仅限指定对照关系，见 [决定记录](../semantic-dedup-review-0.1/human-decisions.md)；结论不推广到未来新增题目或合并 Pilot 后的数据集。

**规模与最终语料决定（2026-09-14）：** `H-BC01-SIZE-CORPUS-SC01-SC02-2026-09-14`。SC01/SC02 已批准，见 [完整原文及来源绑定](../size-corpus-review-0.1/human-decisions.md)。题集仅 Q001–Q040，不并入六道 Pilot 题；正式冻结与 promotion 仍 PENDING，不运行 Benchmark。

## 全局决定与待决事项

| 决定 | 当前状态 | Human 决定/日期/来源 |
|---|---|---|
| 采用现有四份原创语料和确切快照作为最终 Benchmark corpus | APPROVED | H-BC01-SIZE-CORPUS-SC01-SC02-2026-09-14；仅当前 40 题，不并入六道 Pilot 题 |
| 32+8 规模、各类不足 | APPROVED | H-BC01-SIZE-CORPUS-SC01-SC02-2026-09-14；接受本次差额，不改契约质量目标 |
| 当前 40 题内语义去重 | APPROVED — 全部保留 | SD01–SD20 七批决定；见语义去重人工决定记录 |
| 核心政策事实划界与 20 个分组 | APPROVED | H-BC01-FACT-SPLIT-2026-09-14；不扩充语料 |
| Dev/Test 与共享证据/非盲测局限 | APPROVED / ACCEPTED | H-BC01-FACT-SPLIT-2026-09-14；规模/类别缺口后续已由 SC01 接受 |
| 八题弱相关 Unanswerable 的适用性及覆盖局限 | ACCEPTED — 限本次已披露范围 | H-BC01-SIZE-CORPUS-SC01-SC02-2026-09-14；不声称完整负例覆盖或生成拒答能力 |
| 最终数据版本与 promotion | PENDING | 待填 |

**分组与划分批准（2026-09-14）：** `H-BC01-FACT-SPLIT-2026-09-14`。Human 原文：「认可本次核心事实划分、20 个分组及 Dev/Test 草案；接受已列明的共享证据和非盲测局限。语义去重、规模差额、最终语料及正式冻结暂不确认，不运行 Benchmark。」详见 [批准记录](../fact-split-draft-0.1/human-approval.md)及其绑定的草案/hash。以下历史决定中的 family/split 未批准描述保留当时边界，本次状态覆盖该维度。

## 逐题记录

**完整覆盖决定：** `H-BC01-Q001-Q040-COVERAGE-2026-09-11`。来源：助手已展示 reviewed-annotations-0.1 对应的最终人工矩阵，明确下一步为对每题完整 38 块检查并确认无遗漏正证据，可一次确认全部；Human project owner 随后回复「确认」。据此批准 Q001–Q040 的 full-snapshot coverage/no-positive-omissions，仅绑定 novatech-pilot-0.1 / t2001-novatech-pilot-01 的 38 块与第一轮批准问法。日期 2026-09-11，reviewer 为 Human project owner，未提供姓名。[reviewed-annotations-0.2.json](reviewed-annotations-0.2.json)记录本次 coverage，保留 0.1 与原批次当时的 PENDING 历史。等级未改变；不批准 family/split、去重、最终语料复用/规模差额、promotion 或 T2003。

**第二轮等级决定：** `H-BC01-Q031-Q040-GRADES-2026-09-11`。Human project owner 原文：「Q031–Q040 全部 380 项等级按本次矩阵通过，包括两处调整；覆盖暂不确认。」批准 R2-B05-0.1 全矩阵，包含 Q032/T4：1→0、Q040/I3：1→0；保留 Q033–Q040 各一个 Grade 1 邻近政策块。见 [逐项 Human 等级及修订理由](round2-batch-05-reviewed.json)。全部 1,520 项显式等级已批准，但完整 coverage 仍明确未确认，不自动晋升为最终数据集。

**第二轮等级决定：** `H-BC01-Q021-Q030-GRADES-2026-09-11`。Human project owner 原文：「Q021–Q030 全部 380 项等级按本次矩阵通过，包括八处调整；覆盖暂不确认。」批准 R2-B04-0.1 全矩阵，包含 Q021/E5：1→0、Q021/I1：2→0、Q021/I9：1→0、Q022/E9：2→0、Q023/I9：1→0、Q026/I1：2→0、Q027/E7：1→0、Q028/T1：2→0。见 [逐项 Human 等级及修订理由](round2-batch-04-reviewed.json)。全部 Human coverage 仍 PENDING，不自动批准最后一批。

**第二轮等级决定：** `H-BC01-Q011-Q020-GRADES-2026-09-11`。Human project owner 原文：「Q011–Q020 全部 380 项等级按本次矩阵通过，包括四处调整；覆盖暂不确认。」批准 R2-B03-0.1 全矩阵，包括 Q012/I3：1→0、Q013/E8：1→0、Q013/X2：2→0、Q020/T7：1→0；[逐项 Human 等级](round2-batch-03-reviewed.json)保留原建议及本批修订理由。全部 Human coverage 仍 PENDING，不外推批准后续题目。

**第二轮等级决定：** `H-BC01-Q005-Q010-GRADES-2026-09-11`。Human project owner 原文：「Q005–Q010 全部 228 项等级按本次矩阵通过，包括四处调整；覆盖暂不确认。」记录 R2-B02-0.1 全矩阵通过，包含 Q005/X4：1→0、Q006/X1：1→0、Q008/I2：1→2、Q009/I9：1→0。各项理由来自已展示并获批的本批建议；不外推为其他题目批准。[逐项 Human 等级](round2-batch-02-reviewed.json)保留原建议、修订建议及 Human grade，Human coverage 仍 PENDING。

**第二轮等级决定：** `H-BC01-Q001-Q004-GRADES-2026-09-11`。Human 在同一条回复中先确认上表五项并指定“Q002→E6 1分改为0”，随后明确“Q001–Q004 全部 152 项等级按矩阵通过；覆盖暂不确认”。据后面的完整范围确认，记录 R2-B01-0.1 全部 152 项显式等级通过，保留 Q002/E6 的明确例外。该例外无另行语义理由，不补造理由，也不外推为其他题目的自动改分规则。绑定批准问法及冻结 38 chunks；[逐项 Human 等级](round2-batch-01-reviewed.json)保留原 suggested_grade 与 Human grade；原待审包不覆盖。覆盖仍 PENDING，不能赋予其他题目 implicit Grade-0 semantics。

**批次决定引用：** `H-BC01-Q031-Q040-QUERY-2026-09-11`。Human project owner 原文：「Q031–Q040 第一轮按建议通过，包括 Q031、Q032 改写；Q031–Q032 可回答，Q033–Q040 不可回答；等级和覆盖暂不确认。」批准 Q031 增加均无住宿超限特别批准、Q032 限定境内普通商务出差，其余保留原问法；Q031/Q032 为 Multi-chunk，Q033/Q035/Q037/Q039 为 Direct Fact，Q034/Q036/Q038/Q040 为 Paraphrase。批准可回答性不自动批准无正证据遗漏、Grade 0/1 或主指标排除所需的最终 judgments。

**批次决定引用：** `H-BC01-Q021-Q030-QUERY-2026-09-11`。Human project owner 原文：「Q021–Q030 第一轮按建议通过，包括 Q027 改写；等级和覆盖暂不确认。」批准 Q027 明确 HR 接收材料后分类及内部访问控制的改写，其余九题保留原问法；Q021～Q024 为 Distractor，Q025～Q030 为 Multi-chunk，十题均 Answerable=true。等级、coverage、family/split、最终去重及 promotion 未批准。

**批次决定引用：** `H-BC01-Q011-Q020-QUERY-2026-09-11`。Human project owner 原文：「Q011–Q020 第一轮按建议通过，包括 Q015 改写；等级和覆盖暂不确认。」批准 Q015 限定境内普通商务出差的改写，其余九题保留原问法；Q011～Q016 为 Paraphrase，Q017～Q020 为 Distractor，十题均 Answerable=true。等级、coverage、family/split、最终去重与 promotion 未批准。

**批次决定引用：** `H-BC01-Q005-Q010-QUERY-2026-09-11`。Human project owner 原文：「Q005–Q010 第一轮按建议通过，包括 Q007 改写；等级和覆盖暂不确认。」本次批准 Q005/Q006/Q008 原问法及 Direct Fact、Q007 限定境内普通商务出差的改写及 Direct Fact、Q009/Q010 原问法及 Paraphrase，六题均 Answerable=true；不批准等级、coverage、family/split 或 promotion。

<a id="bc01-q001"></a>
### BC01-Q001

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q001)

**决定引用：** `H-BC01-Q001-QUERY-2026-09-11`（本地审阅记录 ID）。来源：助手提出限定“不涉及客户现场排班”的改写，并明确询问是否认可该改写及“直接事实、可回答”，同时说明本轮不确认等级与完整覆盖；Human project owner 随后回复「认可」。

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 按限定适用范围的改写保留 |
| 最终问法 | APPROVED — 不涉及客户现场排班时，正常工作日允许几点到岗？午休多长，下班时间怎样确定？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B01-0.1 本题全部 38 项显式等级；全部按矩阵；见 round2-batch-01-reviewed.json；H-BC01-Q001-Q004-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF01 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q001-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q001-Q004-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q002"></a>
### BC01-Q002

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q002)

**决定引用：** `H-BC01-Q002-QUERY-2026-09-11`（本地审阅记录 ID）。来源：助手展示原问题及 E3 原文，建议“保留原问法｜Direct Fact｜可回答”，并询问是否认可问法、类别和可回答性；Human project owner 回复「认可」。批准仅限上述第一轮维度。

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 新员工入职首周由谁说明岗位目标、安排带教和培训？试用期间多久反馈一次？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B01-0.1 本题全部 38 项显式等级；E6 的原建议 1 改为 Human 0，其他按矩阵；未提供另行语义理由；见 round2-batch-01-reviewed.json；H-BC01-Q001-Q004-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF02 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q002-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q001-Q004-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q003"></a>
### BC01-Q003

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q003)

**决定引用：** `H-BC01-Q003-QUERY-2026-09-11`（本地审阅记录 ID）。来源：助手展示 E4 的请假提前量及紧急病假例外，提出增加“非紧急情况下，计划”的改写，建议“采用改写｜Direct Fact｜可回答”，并询问是否认可这三个维度；Human project owner 回复「认可」。批准仅限第一轮问题审阅。

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 采用限定非紧急计划请假场景的改写 |
| 最终问法 | APPROVED — 非紧急情况下，计划连续请假三天和四天，通常各需提前多少个工作日申请？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B01-0.1 本题全部 38 项显式等级；全部按矩阵；见 round2-batch-01-reviewed.json；H-BC01-Q001-Q004-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF03 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q003-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q001-Q004-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q004"></a>
### BC01-Q004

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q004)

**决定引用：** `H-BC01-Q004-QUERY-2026-09-11`（本地审阅记录 ID）。来源：助手展示原问题及 E7 的体检预约和额外项目规则，建议“保留原问法｜Direct Fact｜可回答”，并询问是否认可问法、类别和可回答性；Human project owner 回复「认可」。批准仅限第一轮问题审阅。

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 年度体检由谁统一预约？自己加做检查前需要确认什么？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B01-0.1 本题全部 38 项显式等级；全部按矩阵；见 round2-batch-01-reviewed.json；H-BC01-Q001-Q004-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF04 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q004-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q001-Q004-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q005"></a>
### BC01-Q005

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q005)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 财务审核通过的员工垫付款通常哪天集中支付，返还到哪个账户？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B02-0.1 本题全部 38 项按修订后的矩阵通过；逐项等级及修订理由见 round2-batch-02-reviewed.json；H-BC01-Q005-Q010-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF05 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q005-Q010-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q005-Q010-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q006"></a>
### BC01-Q006

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q006)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 境内消费的电子发票要交什么文件？只有付款截图可以吗，发票信息错了怎么办？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B02-0.1 本题全部 38 项按修订后的矩阵通过；逐项等级及修订理由见 round2-batch-02-reviewed.json；H-BC01-Q005-Q010-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF06 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q005-Q010-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q005-Q010-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q007"></a>
### BC01-Q007

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q007)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 采用限定境内普通商务出差的改写 |
| 最终问法 | APPROVED — 境内普通商务出差一般选什么高铁席位或飞机舱位？没有普通席位而必须升级时谁批准？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B02-0.1 本题全部 38 项按修订后的矩阵通过；逐项等级及修订理由见 round2-batch-02-reviewed.json；H-BC01-Q005-Q010-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF07 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q005-Q010-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q005-Q010-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q008"></a>
### BC01-Q008

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q008)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 哪些公司系统必须启用 MFA？更换手机后怎样恢复认证访问？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B02-0.1 本题全部 38 项按修订后的矩阵通过；逐项等级及修订理由见 round2-batch-02-reviewed.json；H-BC01-Q005-Q010-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF08 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q005-Q010-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q005-Q010-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q009"></a>
### BC01-Q009

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q009)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 我还在试用期，想固定每周在家干两天，可以按常规远程办公安排申请吗？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B02-0.1 本题全部 38 项按修订后的矩阵通过；逐项等级及修订理由见 round2-batch-02-reviewed.json；H-BC01-Q005-Q010-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF08 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q005-Q010-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q005-Q010-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q010"></a>
### BC01-Q010

[查看问题、建议及全部 38 块](review-batch-01.md#bc01-q010)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — IT 催我装关键更新，但这两天要在客户现场工作，赶不及怎么办？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B02-0.1 本题全部 38 项按修订后的矩阵通过；逐项等级及修订理由见 round2-batch-02-reviewed.json；H-BC01-Q005-Q010-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF09 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q005-Q010-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q005-Q010-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q011"></a>
### BC01-Q011

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q011)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 一张普通报销单里带着银行账号和客户信息，能只看它叫“报销单”就当作普通公开文件吗？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF08 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q012"></a>
### BC01-Q012

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q012)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 电脑可能中了恶意软件，我是不是该在这台电脑上赶紧反复改密码、重装系统，把痕迹清掉？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF10 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q013"></a>
### BC01-Q013

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q013)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 跑完一趟客户行程，商家还没补开发票，我能一直等票齐了再报吗？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF11 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q014"></a>
### BC01-Q014

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q014)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 这笔钱已经刷公司卡付了，我还要报费用吗，能再打到我个人账户吗？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF12 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q015"></a>
### BC01-Q015

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q015)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 采用限定境内普通商务出差的改写 |
| 最终问法 | APPROVED — 客户突然出故障，需要我立即进行境内普通商务出差，来不及提前申请，先要留什么确认、之后何时补单？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF13 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q016"></a>
### BC01-Q016

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q016)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 客户临时改了安排，原来的车票和酒店不用了，退改损失和拿回的退款该怎样报？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF14 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q017"></a>
### BC01-Q017

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q017)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 去上海普通商务出差，酒店实际每晚 420 元，我能按 500 元上限领满吗？ |
| 最终类别 | APPROVED — Distractor |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF15 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q018"></a>
### BC01-Q018

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q018)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 获批外部培训的主办方已经包住宿了，我还能按每晚 350 元向公司领一份住宿补贴吗？ |
| 最终类别 | APPROVED — Distractor |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF15 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q019"></a>
### BC01-Q019

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q019)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 境内普通出差一天，客户提供了午餐和晚餐，我还能领全天 80 元餐补吗？ |
| 最终类别 | APPROVED — Distractor |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF15 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q020"></a>
### BC01-Q020

[查看问题、建议及全部 38 块](review-batch-02.md#bc01-q020)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 报销已经到账，后来商家又退了一部分钱，这笔退款可以自己留下吗？ |
| 最终类别 | APPROVED — Distractor |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B03-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-03-reviewed.json；H-BC01-Q011-Q020-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF14 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q011-Q020-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q011-Q020-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q021"></a>
### BC01-Q021

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q021)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 在家用的是我自己设密码的 Wi-Fi，访问公司内部系统就可以不连 VPN 吗？ |
| 最终类别 | APPROVED — Distractor |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF08 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q022"></a>
### BC01-Q022

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q022)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 邮件显示是领导，让我马上修改收款账户，还留了核实电话，照着邮件里的号码打过去就能确认靠谱吗？ |
| 最终类别 | APPROVED — Distractor |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF16 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q023"></a>
### BC01-Q023

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q023)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 客户现场没网，我能把工作文件拷到自己的 U 盘交付吗？如果确实需要离线介质该怎么做？ |
| 最终类别 | APPROVED — Distractor |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF17 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q024"></a>
### BC01-Q024

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q024)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 我人在公司受管办公网络，同事让我借他的账号临时查资料，这样可以省去权限申请吗？ |
| 最终类别 | APPROVED — Distractor |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF08 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q025"></a>
### BC01-Q025

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q025)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 已转正且岗位适合远程办公，我想下周固定在家工作两天：何时申请、谁批准，获批后用什么设备、怎样接入内部系统？ |
| 最终类别 | APPROVED — Multi-chunk |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF08 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；六道 Pilot 题按 SC02 不纳入本版本；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q026"></a>
### BC01-Q026

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q026)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 离职前工作文件、电脑和认证设备分别怎么交接，谁办理账号停用，旧合作链接的权限又由谁撤销？ |
| 最终类别 | APPROVED — Multi-chunk |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF18 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q027"></a>
### BC01-Q027

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q027)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 采用明确 HR 接收后管理场景的改写 |
| 最终问法 | APPROVED — 连续病假三天，返岗后记录和医疗证明要怎样提交？人力资源部接收这些材料后，应如何分类并控制内部访问权限？ |
| 最终类别 | APPROVED — Multi-chunk |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF08 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q028"></a>
### BC01-Q028

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q028)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 参加收费的外部课程，从报名到预算应找谁确认？参训行程结束后多久提交费用？ |
| 最终类别 | APPROVED — Multi-chunk |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF11 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q029"></a>
### BC01-Q029

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q029)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 去境外拜访客户，要提前多久申请、经谁批准？当地拿不到境内发票时，用什么凭证说明外币费用？ |
| 最终类别 | APPROVED — Multi-chunk |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF19 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q030"></a>
### BC01-Q030

[查看问题、建议及全部 38 块](review-batch-03.md#bc01-q030)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 我在境内普通出差期间用公司费用请客户吃饭，招待应事先经谁批准、通常每人上限多少，参加这餐的员工个人餐补如何处理？ |
| 最终类别 | APPROVED — Multi-chunk |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B04-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-04-reviewed.json；H-BC01-Q021-Q030-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF15 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q021-Q030-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q021-Q030-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q031"></a>
### BC01-Q031

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q031)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 采用范围限定的改写 |
| 最终问法 | APPROVED — 同一趟上海行程先培训后拜访客户，均无住宿超限特别批准，两段住宿各适用多少报销上限、预订时怎样区分用途；同一天两种活动都有，餐费能按两套规则各领一次吗？ |
| 最终类别 | APPROVED — Multi-chunk |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF15 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q032"></a>
### BC01-Q032

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q032)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 采用范围限定的改写 |
| 最终问法 | APPROVED — 境内普通商务出差申请已经批了，但展会酒店都超住宿限额，预计总预算也要增加，订房前应补哪些批准和证明？ |
| 最终类别 | APPROVED — Multi-chunk |
| Answerable / Unanswerable | APPROVED — Answerable=true |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF20 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q033"></a>
### BC01-Q033

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q033)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 按公司规定，我这次获批用私家车出差，每公里具体报销多少元？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=false |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF07 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q034"></a>
### BC01-Q034

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q034)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 我要让商家给公司开票，公司发票抬头的完整名称和纳税人识别号分别是什么？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=false |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF06 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q035"></a>
### BC01-Q035

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q035)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 我的报销已通过财务审核，公司承诺最迟几个工作日一定到账？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=false |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF05 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q036"></a>
### BC01-Q036

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q036)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 这次去新加坡见客户，公司已经批下来的专项预算里，每晚酒店上限是多少新加坡元？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=false |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF19 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q037"></a>
### BC01-Q037

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q037)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 我今年获批的带薪年假额度具体是多少天？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=false |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF03 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q038"></a>
### BC01-Q038

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q038)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 我签的这份劳动合同里，试用期具体约定了几个月？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=false |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF02 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q039"></a>
### BC01-Q039

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q039)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 公司今年年度体检套餐给每位员工安排的预算具体是多少元？ |
| 最终类别 | APPROVED — Direct Fact |
| Answerable / Unanswerable | APPROVED — Answerable=false |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF04 / Test；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |

<a id="bc01-q040"></a>
### BC01-Q040

[查看问题、建议及全部 38 块](review-batch-04.md#bc01-q040)

| 维度 | Human 决定 |
|---|---|
| 保留 / 改写 / 删除 | APPROVED — 保留原问法 |
| 最终问法 | APPROVED — 我要装公司 VPN，公司批准使用的客户端品牌和官方下载地址是什么？ |
| 最终类别 | APPROVED — Paraphrase |
| Answerable / Unanswerable | APPROVED — Answerable=false |
| 建议等级逐项接受范围；修改的 chunk_id/alias、最终等级与理由 | APPROVED — R2-B05-0.1 本题全部 38 项按修订矩阵通过；等级及理由见 round2-batch-05-reviewed.json；H-BC01-Q031-Q040-GRADES-2026-09-11 |
| 已审查完整 38 块，并确认无遗漏正证据 | APPROVED — 已核对完整冻结快照，确认无遗漏正证据；H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| evidence-family / Dev-Test | APPROVED — FF08 / Dev；H-BC01-FACT-SPLIT-2026-09-14 |
| reviewer、实际日期、decision_ref | Human project owner；2026-09-11；H-BC01-Q031-Q040-QUERY-2026-09-11；个人姓名未提供；第二轮等级决定 H-BC01-Q031-Q040-GRADES-2026-09-11；完整覆盖决定 H-BC01-Q001-Q040-COVERAGE-2026-09-11 |
| 未决事项 / 后续重新审阅范围 | 问法、类别、可回答性、38 项等级和完整 coverage 均获批；核心事实及 family/split 已批准、共享证据与非盲测局限已接受；本轮 40 题内去重已通过；语料范围/数量差额已由 SC01/SC02 批准；正式冻结与 promotion 待审，不运行 Benchmark。旧批次 coverage PENDING 是当时状态，不撤销后续本次批准。 |
