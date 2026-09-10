# Pilot Snapshot 01 Annotation Packet — Reviewed 0.2

## Human Review authority 与版本

- Review type：Human Review。
- Review date：2026-09-09。
- Reviewer role：Human project owner；未提供姓名，不推定姓名。
- 决策来源：本轮人工指令明确提供的六题逐项 Human Review 决定；Codex 仅记录与核验，不自行决定 Human grade。
- Annotation packet version：Draft 0.1 → Reviewed 0.2。保留原路径中的 `draft` 以维持引用；当前状态以此版本记录为准，本文件是唯一 canonical reviewed Pilot annotation packet。
- Snapshot binding：`t2001-novatech-pilot-01`；Corpus version：`novatech-pilot-0.1`；4 source documents、38 frozen chunks。
- 依据：[Dataset Contract](retrieval-evaluation-dataset-contract.md)、[Snapshot README](pilot-snapshot-01/README.md)、[snapshot.json](pilot-snapshot-01/snapshot.json)、[Chunk Inventory](pilot-snapshot-01/chunk-inventory.md)。

**Codex suggestion ≠ Human Ground Truth decision。** 下列 Human grade 是人工批准的、绑定本快照的 Pilot labels。原建议及其理由在每题历史区完整保留，历史区中的待审状态和问题不代表当前状态。六题的措辞与类别均已 APPROVED，`PILOT-CQ-*` 仍是 Candidate Query IDs，未自动升级为最终 Benchmark Query IDs 或最终 Benchmark Dataset。

本次仅记录明确给出的 30 个 query–chunk 判断。未列出的 snapshot chunks 不自动补为 Grade 0，其覆盖语义已由 CD-1 定义，本 Pilot 的独立 Human coverage confirmation 已于 2026-09-10 获 6/6 APPROVED，见文末批准记录。原草稿逐题 38/38 阅读记录是 Codex 阅读历史，不等同于人工为所有未列块逐一确认等级。

本文件的 binary relevant set 按现有 `grade >= 2` 机械列出，仅表示已批准 Pilot labels 的集合映射，不是 Retrieval 输出或指标计算；集合展示顺序没有排名含义。未执行 Retrieval、metrics、Benchmark 或架构 Experiment，未修改语料、快照及 V1 行为。当前 T2001 = DONE（2026-09-10 Human Final Gate PASS）；Contract 0.3 FROZEN；T2002/T2003 = TODO，未获执行授权。

## PILOT-CQ-001

**Query：** 公司每天哪些时段要求大家一起协作？

**Category：** Direct Fact

**Human decision：** Query wording APPROVED；Category APPROVED。Human grade 均为 HUMAN REVIEW APPROVED（2026-09-09，Human project owner），绑定上述 Snapshot 01。

| file_name | chunk_index | chunk_id | 原 Codex suggested grade | Human grade | 决定与理由 |
|---|---:|---|---:|---:|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 | 0 | 一般 HR/IT/财务服务或协调渠道，没有实质回答本题的信息需要；Human 将 1 调整为 0。 |
| employee_handbook.md | 2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | 3 | 3 | 接受原建议。明确共同协作时间为 10–12 点、14–17 点；客户现场服务按确认排班，是直接答案及适用例外。 |
| employee_handbook.md | 5 | `992fccef-928e-4c84-9233-3f45b900a0ad` | 2 | 1 | 确认远程办公仍遵守约定协作时段，但没有给出所问的具体钟点，Human 将 2 调整为 1。 |

**Binary relevant set（现有 grade >= 2 映射）：**

- `392ae2da-31b8-4baa-b7dc-03020e492488`

<details>
<summary>Draft 0.1 原 Codex 建议、理由与审阅问题（历史记录，不是当前 Human labels）</summary>

**用途：** 验证明确时间事实与重复提及协作时段的远程办公规则如何区分。

**Candidate relevant chunks：** 所有等级均为 SUGGESTED — HUMAN REVIEW REQUIRED。

| file_name | chunk_index | chunk_id | suggested grade / 状态 | 摘要与理由 |
|---|---:|---|---|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 人力资源负责考勤，负责人协调人员安排；仅提供咨询与安排渠道，不给具体时段。 |
| employee_handbook.md | 2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | 3 — SUGGESTED — HUMAN REVIEW REQUIRED | 明确共同协作时间为 10–12 点、14–17 点；客户现场服务按确认排班，是直接答案及适用例外。 |
| employee_handbook.md | 5 | `992fccef-928e-4c84-9233-3f45b900a0ad` | 2 — SUGGESTED — HUMAN REVIEW REQUIRED | 远程办公也要在约定协作时段可联系，补充适用场景，但没有重述具体时间。 |

**完整性复核：** 38/38 已逐项阅读。培训在工作时间内进行不定义全公司共同协作时段，未列为潜在正相关；单纯出现日期、期限的其他政策也不提供此答案。

**Human review questions：** 问法是否自然、Direct Fact 是否合适？远程办公块应为 2 还是 1，咨询渠道是否过弱？是否遗漏相关块或存在过高/过低等级？

</details>

## PILOT-CQ-002

**Query：** 公司账号的密码至少要几位？能和我个人网站的密码用同一个吗？

**Category：** Direct Fact

**Human decision：** Query wording APPROVED；Category APPROVED。Human grade 均为 HUMAN REVIEW APPROVED（2026-09-09，Human project owner），绑定上述 Snapshot 01。

| file_name | chunk_index | chunk_id | 原 Codex suggested grade | Human grade | 决定与理由 |
|---|---:|---|---:|---:|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 | 0 | 一般 HR/IT/财务服务或协调渠道，没有实质回答本题的信息需要；Human 将 1 调整为 0。 |
| it_security_policy.md | 1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | 3 | 3 | 接受原建议。密码至少十四位，不得与个人网站密码重复，直接覆盖两个子问。 |

**Binary relevant set（现有 grade >= 2 映射）：**

- `176b8225-18b7-479d-b02b-aa3d0be7f724`

<details>
<summary>Draft 0.1 原 Codex 建议、理由与审阅问题（历史记录，不是当前 Human labels）</summary>

**用途：** 验证同一 chunk 内的两个明确事实，避免将同主题多处出现误当 Multi-chunk。

**Candidate relevant chunks：** 所有等级均为 SUGGESTED — HUMAN REVIEW REQUIRED。

| file_name | chunk_index | chunk_id | suggested grade / 状态 | 摘要与理由 |
|---|---:|---|---|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 账号问题由 IT 服务台处理，提供咨询渠道但没有密码规则。 |
| it_security_policy.md | 1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | 3 — SUGGESTED — HUMAN REVIEW REQUIRED | 密码至少十四位，不得与个人网站密码重复，直接覆盖两个子问。 |

**完整性复核：** 38/38 已逐项阅读。信息保护与离职交接、IT 离职规则中的“不得共享密码”，以及事件响应中的“更换凭据”，不回答长度或个人网站复用问题；未因同现“密码”而建议正相关。数据分类将凭据列为保密信息，也不定义本题两项要求。

**Human review questions：** 两个子问是否符合真实需求，Direct Fact 是否合适？账号服务渠道是否值得 1，是否应不列入？是否遗漏证据或需要调整等级？

</details>

## PILOT-CQ-003

**Query：** 昨天正常上班了，但系统里少了一条考勤记录，我还能补吗？找谁确认、最晚什么时候提交说明？

**Category：** Paraphrase

**Human decision：** Query wording APPROVED；Category APPROVED。Human grade 均为 HUMAN REVIEW APPROVED（2026-09-09，Human project owner），绑定上述 Snapshot 01。

| file_name | chunk_index | chunk_id | 原 Codex suggested grade | Human grade | 决定与理由 |
|---|---:|---|---:|---:|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 | 0 | 一般 HR/IT/财务服务或协调渠道，没有实质回答本题的信息需要；Human 将 1 调整为 0。 |
| employee_handbook.md | 2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | 3 | 3 | 接受原建议。漏记可在三个工作日内提交说明，由负责人核实，直接回答可否补记、找谁和期限。 |
| employee_handbook.md | 4 | `193a39de-16cc-456f-85b8-74e801991e28` | 1 | 0 | 本块是病假考勤更正；问题明确为正常出勤漏记。相似术语和期限不能使不同业务条件下的规则相关。 |

**Binary relevant set（现有 grade >= 2 映射）：**

- `392ae2da-31b8-4baa-b7dc-03020e492488`

<details>
<summary>Draft 0.1 原 Codex 建议、理由与审阅问题（历史记录，不是当前 Human labels）</summary>

**用途：** 用员工描述的“少了一条记录”表达“考勤漏记”，区分一般补记与病假补手续的不同语境。

**Candidate relevant chunks：** 所有等级均为 SUGGESTED — HUMAN REVIEW REQUIRED。

| file_name | chunk_index | chunk_id | suggested grade / 状态 | 摘要与理由 |
|---|---:|---|---|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 人力资源负责考勤咨询，提供辅助渠道；不能替代负责人核实。 |
| employee_handbook.md | 2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | 3 — SUGGESTED — HUMAN REVIEW REQUIRED | 漏记可在三个工作日内提交说明，由负责人核实，直接回答可否补记、找谁和期限。 |
| employee_handbook.md | 4 | `193a39de-16cc-456f-85b8-74e801991e28` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 病假条款提及人力资源协助更正考勤，可作有限渠道背景；“返岗后三个工作日”只适用于病假，不是正常出勤漏记期限。 |

**完整性复核：** 38/38 已逐项阅读。请假与漏记共享考勤渠道，但不能移植病假起算点；差旅申请等其他“三个工作日”条款未列入，因为业务对象不同。

**Human review questions：** “系统少记录”是否自然且没有引入新的处理规则，Paraphrase 是否准确？病假块应保留 1 还是建议 0？是否遗漏相关内容，其他等级是否需要调整？

</details>

## PILOT-CQ-004

**Query：** 我没在登录，手机却弹出公司账号的验证请求。我该点同意吗，要怎么处理？

**Category：** Paraphrase

**Human decision：** Query wording APPROVED；Category APPROVED。Human grade 均为 HUMAN REVIEW APPROVED（2026-09-09，Human project owner），绑定上述 Snapshot 01。

| file_name | chunk_index | chunk_id | 原 Codex suggested grade | Human grade | 决定与理由 |
|---|---:|---|---:|---:|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 | 0 | 一般 HR/IT/财务服务或协调渠道，没有实质回答本题的信息需要；Human 将 1 调整为 0。 |
| employee_handbook.md | 9 | `b7ad1041-2858-4162-b4cc-7b40961751c8` | 2 | 2 | 接受原 Grade 2：不仅是渠道，还明确账号异常联系 IT、保留线索等实质行动。 |
| it_security_policy.md | 1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | 3 | 3 | 接受原建议。只确认本人发起的登录，意外推送拒绝并联系 IT，直接回答两个子问。 |
| it_security_policy.md | 7 | `f7017394-093c-4e03-98b4-2513089a96b2` | 1 | 0 | 钓鱼邮件/登录页面只是邻近安全语境，没有为意外认证推送事件提供实质证据。 |
| it_security_policy.md | 8 | `d111e21f-b2a6-461a-9cec-b7189635546f` | 3 | 2 | 提供实质性事件报告和证据保存行动；拒绝意外认证请求的核心决定由 Grade 3 块更直接提供，因此 3 调整为 2。 |

**Binary relevant set（现有 grade >= 2 映射）：**

- `b7ad1041-2858-4162-b4cc-7b40961751c8`
- `176b8225-18b7-479d-b02b-aa3d0be7f724`
- `d111e21f-b2a6-461a-9cec-b7189635546f`

<details>
<summary>Draft 0.1 原 Codex 建议、理由与审阅问题（历史记录，不是当前 Human labels）</summary>

**用途：** 用实际体验表达“意外 MFA 请求”，检查直接拒绝规则、事件处理和一般员工责任的重叠。

**Candidate relevant chunks：** 所有等级均为 SUGGESTED — HUMAN REVIEW REQUIRED。

| file_name | chunk_index | chunk_id | suggested grade / 状态 | 摘要与理由 |
|---|---:|---|---|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 账号问题找 IT，提供一般服务入口，没有意外请求的具体规则。 |
| employee_handbook.md | 9 | `b7ad1041-2858-4162-b4cc-7b40961751c8` | 2 — SUGGESTED — HUMAN REVIEW REQUIRED | 账号异常及时联系 IT、不自行删除线索，并指向信息安全制度，提供可直接执行的补充行动。 |
| it_security_policy.md | 1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | 3 — SUGGESTED — HUMAN REVIEW REQUIRED | 只确认本人发起的登录，意外推送拒绝并联系 IT，直接回答两个子问。 |
| it_security_policy.md | 7 | `f7017394-093c-4e03-98b4-2513089a96b2` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 可疑登录页面/密码请求需核实，报告并保留邮件；仅作邻近安全背景，不假定本题经邮件发起。 |
| it_security_policy.md | 8 | `d111e21f-b2a6-461a-9cec-b7189635546f` | 3 — SUGGESTED — HUMAN REVIEW REQUIRED | 明确意外 MFA 请求立即通过可信渠道报告；提供时间、操作并保留记录。设备感染处置只在怀疑感染时适用。 |

**完整性复核：** 38/38 已逐项阅读。VPN 的正常 MFA 接入要求不说明异常推送处理，未列正相关；没有从“弹出请求”推断设备一定感染。多个强相关块在此提供重叠答案，题型仍优先 Paraphrase。

**Human review questions：** 不写 MFA 是否仍清楚、自然，类别是否合适？事件块应为 3 还是 2，邮件块的 1 是否过宽？是否遗漏其他证据或高估一般责任块？

</details>

## PILOT-CQ-005

**Query：** 我获批去上海参加收费的外部培训，没有住宿超限的特别批准。订酒店时，每间每晚能报销的上限是多少？能按上海普通出差的 500 元标准订吗？

**Category：** Distractor

**Human decision：** Query wording APPROVED；Category APPROVED。Human grade 均为 HUMAN REVIEW APPROVED（2026-09-09，Human project owner），绑定上述 Snapshot 01。

| file_name | chunk_index | chunk_id | 原 Codex suggested grade | Human grade | 决定与理由 |
|---|---:|---|---:|---:|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 | 0 | 一般 HR/IT/财务服务或协调渠道，没有实质回答本题的信息需要；Human 将 1 调整为 0。 |
| employee_handbook.md | 6 | `ca1a91b1-f45e-4527-9857-277ec4304ed9` | 2 | 2 | 接受原建议。参训不自动套用普通差旅住宿标准，费用细则指向报销制度；直接支持不能套用的判断。 |
| employee_handbook.md | 8 | `424e7665-108d-45da-b26f-6687c39c0834` | 1 | 0 | 一般费用限额责任不能确定培训专属金额或适用规则。 |
| expense_policy.md | 1 | `605740ab-0d52-4655-81db-b9bcb008f6ed` | 1 | 0 | 一般报销、发票、审批和预算流程虽属相关工作流，但没有实质回答培训住宿上限及上海普通差旅标准是否适用；Human 将 1 调整为 0。 |
| expense_policy.md | 2 | `e3075f5f-eb85-4faf-9c1e-c560dfdcfb45` | 1 | 0 | 一般报销、发票、审批和预算流程虽属相关工作流，但没有实质回答培训住宿上限及上海普通差旅标准是否适用；Human 将 1 调整为 0。 |
| expense_policy.md | 3 | `c59ef50b-ba8a-4ab0-8bc2-2bcb350c3bbf` | 1 | 0 | 一般报销、发票、审批和预算流程虽属相关工作流，但没有实质回答培训住宿上限及上海普通差旅标准是否适用；Human 将 1 调整为 0。 |
| expense_policy.md | 7 | `7b2fbf99-8274-4610-ac08-3c3e7259ad09` | 3 | 3 | 接受原建议。培训住宿每间每晚 350 元上限，凭票实报实销，不分一线城市，不能引用普通差旅 500 元；直接覆盖问题。 |
| expense_policy.md | 8 | `0a7b4a44-4ac1-49da-a973-6ee14d4792a8` | 2 | 2 | 接受原建议。培训例外按培训条款，超标准须特别批准，不能改类别规避；实质支持题设“无特别批准”的边界。 |
| travel_policy.md | 1 | `14f54027-316e-4f40-b50d-022696ec4f77` | 2 | 2 | 接受原建议。明确外部培训不适用普通差旅住宿限额，指向报销制度，直接排除错误适用。 |
| travel_policy.md | 4 | `e9289ccd-a3ca-4c8e-9f29-910dbd49018c` | 2 | 2 | 接受原 Grade 2：不能因含干扰金额 500 就判 0；完整 chunk 明确解释该金额不适用于外部培训，提供正确排除证据。 |
| travel_policy.md | 5 | `d62a0153-11c5-434e-b15d-7b12ddb5d208` | 0 | 0 | 接受原 Grade 0：普通商务差旅超限审批不适用于本题外部培训规则。 |

**Binary relevant set（现有 grade >= 2 映射）：**

- `ca1a91b1-f45e-4527-9857-277ec4304ed9`
- `7b2fbf99-8274-4610-ac08-3c3e7259ad09`
- `0a7b4a44-4ac1-49da-a973-6ee14d4792a8`
- `14f54027-316e-4f40-b50d-022696ec4f77`
- `e9289ccd-a3ca-4c8e-9f29-910dbd49018c`

<details>
<summary>Draft 0.1 原 Codex 建议、理由与审阅问题（历史记录，不是当前 Human labels）</summary>

**用途：** 验证相同城市、住宿和报销词汇下的业务目的区别；完整 chunk 同时含干扰数字和明确排除规则时，不应机械建议 0。

**Candidate relevant chunks：** 所有等级均为 SUGGESTED — HUMAN REVIEW REQUIRED。

| file_name | chunk_index | chunk_id | suggested grade / 状态 | 摘要与理由 |
|---|---:|---|---|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 具体费用由财务按制度审核，是有限咨询渠道，不能提供上限。 |
| employee_handbook.md | 6 | `ca1a91b1-f45e-4527-9857-277ec4304ed9` | 2 — SUGGESTED — HUMAN REVIEW REQUIRED | 参训不自动套用普通差旅住宿标准，费用细则指向报销制度；直接支持不能套用的判断。 |
| employee_handbook.md | 8 | `424e7665-108d-45da-b26f-6687c39c0834` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 批准出差不豁免费用限额，财务核验标准；属于一般责任背景，不能据此给培训定价。 |
| expense_policy.md | 1 | `605740ab-0d52-4655-81db-b9bcb008f6ed` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 费用须实际发生、有批准和凭证，说明报销基本条件，不含培训住宿限额。 |
| expense_policy.md | 2 | `e3075f5f-eb85-4faf-9c1e-c560dfdcfb45` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 境内消费须有效发票及明细，为培训条款“凭票据实报实销”补充凭证背景，不决定上限。 |
| expense_policy.md | 3 | `c59ef50b-ba8a-4ab0-8bc2-2bcb350c3bbf` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 关联事前批准、预算核验及财务标准审核，是执行背景，不含具体金额。 |
| expense_policy.md | 7 | `7b2fbf99-8274-4610-ac08-3c3e7259ad09` | 3 — SUGGESTED — HUMAN REVIEW REQUIRED | 培训住宿每间每晚 350 元上限，凭票实报实销，不分一线城市，不能引用普通差旅 500 元；直接覆盖问题。 |
| expense_policy.md | 8 | `0a7b4a44-4ac1-49da-a973-6ee14d4792a8` | 2 — SUGGESTED — HUMAN REVIEW REQUIRED | 培训例外按培训条款，超标准须特别批准，不能改类别规避；实质支持题设“无特别批准”的边界。 |
| travel_policy.md | 1 | `14f54027-316e-4f40-b50d-022696ec4f77` | 2 — SUGGESTED — HUMAN REVIEW REQUIRED | 明确外部培训不适用普通差旅住宿限额，指向报销制度，直接排除错误适用。 |
| travel_policy.md | 4 | `e9289ccd-a3ca-4c8e-9f29-910dbd49018c` | 2 — SUGGESTED — HUMAN REVIEW REQUIRED | 虽写上海普通差旅 500 元，也明确培训不能据一线城市套用该上限；整个块有相关证据，不能仅视为干扰。 |

**重要干扰对照（不是正相关候选）：**

| file_name | chunk_index | chunk_id | suggested grade / 状态 | 摘要与理由 |
|---|---:|---|---|---|
| travel_policy.md | 5 | `d62a0153-11c5-434e-b15d-7b12ddb5d208` | 0 — SUGGESTED — HUMAN REVIEW REQUIRED | 普通差旅住宿超限特别批准程序，不是本题无例外批准的外部培训上限；不能移植为培训例外审批路径。 |

**完整性复核：** 38/38 已逐项阅读。普通差旅费用块只转引普通差旅标准，没有培训排除说明；境外出差预算也不适用于上海培训。餐补、城际交通、取消退款均非本题请求。未列任意无关块凑 0。

**Human review questions：** 场景是否真实清晰，Distractor 是否合适？费用凭证/审批/咨询背景的 1 是否过宽？培训指引与差旅排除块建议 2 是否合理，是否仍遗漏证据？普通差旅超限块建议 0 是否合适？

</details>

## PILOT-CQ-006

**Query：** 我想申请每周两天在家办公，需要满足什么条件、什么时候提交申请？获批后用家里网络访问公司内部系统，还需要做哪些接入认证？

**Category：** Multi-chunk

**Human decision：** Query wording APPROVED；Category APPROVED。Human grade 均为 HUMAN REVIEW APPROVED（2026-09-09，Human project owner），绑定上述 Snapshot 01。

| file_name | chunk_index | chunk_id | 原 Codex suggested grade | Human grade | 决定与理由 |
|---|---:|---|---:|---:|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 | 0 | 一般 HR/IT/财务服务或协调渠道，没有实质回答本题的信息需要；Human 将 1 调整为 0。 |
| employee_handbook.md | 2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | 1 | 1 | 接受原 Grade 1：为远程规则引用的协作时段提供真实解释背景，但问题未直接询问具体钟点。 |
| employee_handbook.md | 5 | `992fccef-928e-4c84-9233-3f45b900a0ad` | 3 | 3 | 接受原 Grade 3：直接、完整提供必要的远程申请子答案；整体问题另需家庭网络认证证据，不妨碍此块为 3。 |
| it_security_policy.md | 1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | 2 | 2 | 接受原建议。VPN/远程访问必须启用 MFA，使用本人账号；补充认证规则，但不说明家庭网络归类。 |
| it_security_policy.md | 2 | `8bc6437d-8da4-43c0-8ad6-9d04b1bee39f` | 3 | 3 | 接受原 Grade 3：直接、完整提供必要的家庭网络 VPN/MFA 子答案；其他必要子答案由员工手册提供。 |
| it_security_policy.md | 9 | `6332122f-aa36-4c49-ac9a-f36d252171df` | 1 | 1 | 接受原 Grade 1：提供有限的远程安全边界，但不是所问家庭网络 VPN/MFA 要求。 |

**Binary relevant set（现有 grade >= 2 映射）：**

- `992fccef-928e-4c84-9233-3f45b900a0ad`
- `176b8225-18b7-479d-b02b-aa3d0be7f724`
- `8bc6437d-8da4-43c0-8ad6-9d04b1bee39f`

<details>
<summary>Draft 0.1 原 Codex 建议、理由与审阅问题（历史记录，不是当前 Human labels）</summary>

**用途：** 申请条件、期限与家庭网络认证分别在员工手册和 IT 制度中；两块提供互补的必要子答案，不能只凭同主题重复认定 Multi-chunk。

**Candidate relevant chunks：** 所有等级均为 SUGGESTED — HUMAN REVIEW REQUIRED。

| file_name | chunk_index | chunk_id | suggested grade / 状态 | 摘要与理由 |
|---|---:|---|---|---|
| employee_handbook.md | 1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 负责人协调人员安排、账号问题找 IT，提供两个问题的服务渠道。 |
| employee_handbook.md | 2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 给出共同协作时段，为远程条款“约定时段可联系”补充背景，不直接给申请或认证要求。 |
| employee_handbook.md | 5 | `992fccef-928e-4c84-9233-3f45b900a0ad` | 3 — SUGGESTED — HUMAN REVIEW REQUIRED | 完成试用期、岗位适合、每周最多两天、负责人审批、常规申请前一工作日下班前提交；给出申请子答案并转引安全规则。 |
| it_security_policy.md | 1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | 2 — SUGGESTED — HUMAN REVIEW REQUIRED | VPN/远程访问必须启用 MFA，使用本人账号；补充认证规则，但不说明家庭网络归类。 |
| it_security_policy.md | 2 | `8bc6437d-8da4-43c0-8ad6-9d04b1bee39f` | 3 — SUGGESTED — HUMAN REVIEW REQUIRED | 家庭网络也按不可信网络处理，访问内部系统先连接 VPN 并完成 MFA；给出不可缺少的家庭接入子答案。 |
| it_security_policy.md | 9 | `6332122f-aa36-4c49-ac9a-f36d252171df` | 1 — SUGGESTED — HUMAN REVIEW REQUIRED | 远程申请指向员工手册，地点批准不等于个人设备/存储批准；酒店 VPN 示例不直接回答家庭网络要求。 |

**完整性复核：** 38/38 已逐项阅读。试用期与岗位支持块没有远程申请资格或期限；设备维护、文件共享等是一般安全义务，不是本题接入认证要求。两份核心块分别缺少另一半答案，必须联合使用；尚未建立答案或证据组合的最终 schema。

**Human review questions：** 两个子问是否符合员工办理远程办公的自然流程，Multi-chunk 是否合适？两个必要子答案分别建议 3 是否合理？IT 指引块和协作时段块应为 1 还是更高/不相关，是否遗漏内容？

</details>

## Human label 数量与变更历史

| Candidate Query | Grade 3 | Grade 2 | Grade 1 | Grade 0 |
|---|---:|---:|---:|---:|
| PILOT-CQ-001 | 1 | 0 | 1 | 1 |
| PILOT-CQ-002 | 1 | 0 | 0 | 1 |
| PILOT-CQ-003 | 1 | 0 | 0 | 2 |
| PILOT-CQ-004 | 1 | 2 | 0 | 2 |
| PILOT-CQ-005 | 1 | 4 | 0 | 6 |
| PILOT-CQ-006 | 2 | 1 | 2 | 1 |
| 合计 | 7 | 7 | 3 | 13 |

类别维持 2 Direct Fact / 2 Paraphrase / 1 Distractor / 1 Multi-chunk。共有 30 项 Human labels，其中 14 项修改、16 项接受原建议；以上是 query–chunk 标签数量，不是检索指标。原建议总数为 Grade 3/2/1/0 = 8/7/14/1。每项原等级及修改理由均在对应题目表中保留。

## Pilot-derived annotation rubric findings

### 既有契约定义（未修改）

Dataset Contract 定义 3 = Highly Relevant、2 = Relevant、1 = Weakly Relevant、0 = Irrelevant。Recall/MRR 的 binary mapping 仍为 `grade >= 2`，nDCG 保留四级等级。本次不修改映射阈值或指标定义，也不将以下 Pilot 澄清写成已全局冻结的新契约。

### 本轮 Human Review 得出的操作性澄清

| Grade | Pilot operational clarification |
|---|---|
| 3 — Core / necessary evidence | 直接提供回答 Query 所需的核心证据。真正的 Multi-chunk 问题中，直接、完整提供一个必要子答案的块可为 3，即使其他必要子答案需要其他块。 |
| 2 — Substantive complementary evidence | 不独立提供主要答案，但贡献明确、实质、正确的证据，实质改善完整回答；强于主题相似或一般背景。 |
| 1 — Limited genuine evidence value | 必须有真实但有限的解释或支持价值；不能只因共享关键词、相同部门、宽泛主题或工作流中某个通用流程就标 1。 |
| 0 — No substantive evidence for this information need | 对当前具体信息需要没有实质证据，即使语义或词汇相似。 |

- **Channel-only rule：** 泛化的 HR / IT / Finance 联系渠道不自动获得 Grade 1；不实质回答当前问题时为 0。CQ-004 员工手册 index 9 包含异常处置与证据保留动作，所以不是 channel-only。
- **Wrong-context rule：** 不同业务条件下的规则，不能因术语、动作、期限或数字相同就算相关。例如正常出勤漏记与病假考勤补办。
- **Generic-process rule：** 通用发票、审批、报销或服务流程必须对特定 Query 贡献证据，不能只因属于同一工作流就获得正相关。
- **Full-chunk evidence rule：** 不能仅因出现干扰事实或金额就判不相关；须检查完整 chunk。明确解释干扰规则为何不适用的排除证据可实质相关，见 CQ-005 的普通差旅住宿块。
- **Necessary-subanswer rule：** 真正 Multi-chunk 问题的必要子答案直接证据可为 Grade 3，见 CQ-006 的远程申请与家庭网络接入两块。

这些是本轮 Pilot 的人工审阅澄清及判例，不代表 Dataset Contract 的所有最终标注约定已完成冻结。

## CQ-005 binary relevance breadth — 历史 finding 与 CD-2 决定

**历史状态（Reviewed 0.2，2026-09-09）：OPEN。当前映射决定已由 CD-2（2026-09-10 记录）确认，见文末 Closing Decisions 附录；以下保留发现及原待审问题的来源。** CQ-005 有五个 Human grade >= 2 的 chunks。按当前契约，五块全部进入 Recall/MRR 的 binary relevant set；这只记录集合映射，不是运行或测量结果，也不能证明现有映射最优。

历史待审问题：**Grade-2 补充/排除证据的操作性尺度与 `grade >= 2` binary mapping 结合，是否会使某些 exclusion / Distractor queries 的 relevant set 过宽？**

Reviewed 0.2 当时没有解决此问题，也未改变 threshold、指标定义或 CQ-005 的 Human labels；本次 Closing Decisions 记录 Human 的后续明确决定，不修改六题任何等级或 binary set。

未列 chunks 的 coverage 与 promotion 语义现见 Dataset Contract CD-1/CD-3；本 Pilot 的实际人工覆盖确认现已完成，最终 Benchmark 纳入尚未发生。原快照说明中的“Ground Truth 尚未创建”描述的是入库取证阶段，本次批准的 Pilot labels 在本文件独立记录，不回写冻结快照证据。


## Closing Decisions evidence addendum — 2026-09-10

本附录记录本轮 Human project owner 已确认的 CD-1～CD-4，权威来源是人工指令；Codex 仅整理，不新增 Human labels。Reviewed 0.2 的版本、2026-09-09 审阅日期、六题措辞/类别、原建议及 Human judgments 全部保留。日期 2026-09-10 是 closing decisions 的落盘日期，不回写先前审阅日期。

- **CD-1 / coverage：** 允许稀疏显式判断；全部 Grade 1–3 与选定 Grade 0 显式保留。只有全快照 screening、Human full-snapshot review、明确无遗漏 positive evidence、coverage_reviewed=true、snapshot identity/version 与 reviewer metadata 全部满足后，未列块才具有 implicit Grade-0 semantics。该 Closing Decisions 附录落盘时 coverage confirmation 为 PENDING；本轮独立 Human 确认已补齐，当前批准范围见文末，历史 pending 不再代表当前状态。
- **CD-2 / CQ-005：** 保留五块 grade >= 2，且不是 annotation error；binary mapping 仍为 grade >= 2，nDCG 保留四级。原映射问题已有人工作出决定，保留其 measurement limitation：Recall/MRR 无法区分 Grade 3 与 Grade 2 的重要性，不能单独证明 core evidence 被检索，须结合 graded nDCG 与 per-query evidence analysis。Grade-3 / Core-Evidence Recall@K 仅是未来 T2002 candidate diagnostic，非 required metric、未批准本轮实现。
- **CD-3 / authority：** 完整 Human review、coverage、judgment、final approval 与 promotion gate 见契约；单一 Human project owner 为 benchmark v1 primary reviewer，无强制第二标注员，不声称双标注或 inter-annotator agreement。未决/缺少必要 review 的 Query 不进入 frozen Benchmark。
- **CD-4 / target：** 48 是质量目标：40 Answerable（四类各 10）+ 8 Unanswerable；Dev/Test 各 20+4、四类各 5。质量不足可低于目标，但须记录缺口/局限并获 Human 最终批准。同一 evidence_family_id MUST NOT 跨 split，不能只随机分题。本次不构造目标数据。

完整 schema、条件与待决清单见 [Dataset Contract 0.2 第 5–14 节](retrieval-evaluation-dataset-contract.md)。Pilot judgments 有效不自动证明覆盖或 Benchmark 晋升；覆盖现已另有明确 Human confirmation，未自动晋升最终 Benchmark。该阶段 T2001 closing checklist 等待独立 Human Gate；后续 2026-09-10 Final Gate 已 PASS，T2001 DONE、Contract 0.3 FROZEN，T2002/T2003 TODO。


## Human Full-Snapshot Coverage Gate — 2026-09-10

Review type：Human Full-Snapshot Coverage Review；Reviewer role：Human project owner；Review date：2026-09-10；个人姓名未提供，不虚构。来源为本轮 Human 指令逐题 CQ-001～CQ-006 APPROVE — no additional Grade 1–3 evidence found，以及整体完整 38-chunk 审阅声明；原文与六项决定见 [Coverage Gate evidence](pilot-snapshot-01/coverage-review-packet.md)。

**6/6 APPROVED；coverage_reviewed = true。** 仅适用于 PILOT-CQ-001～006、当前 Human-reviewed annotation version Reviewed 0.2、corpus novatech-pilot-0.1 和 snapshot t2001-novatech-pilot-01 的冻结 38 chunks。MUST NOT 推广至未来 Queries、未来语料版本、re-ingested snapshots 或未来 48-query dataset。

本文件的 30 项显式 Human labels 全部不变，Grade 3/2/1/0 = 7/7/3/13；CQ-005 五块 binary relevant set 不变。剩余 198 个 query–chunk pairs 根据 CD-1 和 Human coverage confirmation 具有 implicit Grade-0 semantics；没有新增 198 条 explicit Human Grade 0，也没有生成新 relevance judgment。该确认不是从 LLM screening 推断。

Reviewed 0.2 保留原标签版本，本节追加覆盖证据。后续 Human project owner 已于 2026-09-10 明确批准 T2001 DONE、Contract 0.3 FROZEN、Final Gate PASS；[最终决定](retrieval-evaluation-dataset-contract.md) 不改变本文件任何标签或 coverage 范围。
