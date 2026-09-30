# Pilot Snapshot 01 — Human Full-Snapshot Coverage Review Packet

- Snapshot ID：`t2001-novatech-pilot-01`。
- Corpus version：`novatech-pilot-0.1`；4 source documents；total chunks = 38。
- 整理日期：2026-09-10。
- Human reviewer role：Human project owner；Review date：2026-09-10；未提供个人姓名，不虚构姓名。
- 当前状态：`coverage_reviewed = true` / **6/6 APPROVED**；Human 明确确认已逐题审阅完整冻结快照。
- 依据：[Reviewed annotation packet 0.2](../pilot-snapshot-01-annotation-packet-draft.md)、[Dataset Contract 0.3](../retrieval-evaluation-dataset-contract.md)、[snapshot.json](snapshot.json)、[完整 Chunk Inventory](chunk-inventory.md)。

本包是 coverage inspection aid，不是 new annotation pass。Codex 仅整理已存在的 Human judgments 和冻结文本，不为未列块建议等级，不增删 positive evidence，不改 Query，不提供 Retrieval ranking。审阅目的：逐题检查完整 38 个 chunks，确认除已有显式 Grade 1–3 外是否遗漏 positive evidence。Grade 1 也属于本次 coverage 审阅的 positive 范围，但 binary Relevant 仍只包括 grade >= 2。

每题全部 38 行按 `file_name → chunk_index` 展示；A/B 行完整复列该题现有 Human-reviewed explicit judgments，C 行没有 explicit Human judgment：

- **A — Explicit Positive：** 显示已有 Human Grade 1/2/3。
- **B — Explicit Grade 0：** 显示已有 Human Grade 0。
- **C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED：** 表格保留审阅时的原标识以便审计；其原 pending 状态已由本次 Human APPROVE 覆盖。C 行仍无 explicit judgment，当前依据 CD-1 具有 implicit Grade-0 semantics，不是 explicit Human Grade 0。

Preview 是同一 chunk 存储全文的开头摘录，仅将空白压缩为单空格，超出 200 字符处加省略号；没有重新概括或相关性推断。**全文审阅须结合上方 Chunk Inventory 或 snapshot.json**，不能只看 preview 就确认整块无遗漏。每题检查 A/B/C 全部内容，若发现新增证据或已有判断需修订，使用 REJECT / NEEDS CHANGES 并在 notes 中记录具体 chunk_id；本轮只持久化 Human 已完成的判断，不代做新的判断。

Codex 整理输出本身不是 Human approval；本轮依据 Human project owner 明确指令记录已经完成的 coverage approval，CD-1 条件现已满足。本包保留 228 行原 review views，不写回冻结快照，不改 Reviewed 0.2 的显式 labels。

**批准范围：** 仅限 `PILOT-CQ-001`～`PILOT-CQ-006`、当前 Human-reviewed annotation version **Reviewed 0.2**、corpus `novatech-pilot-0.1`、snapshot `t2001-novatech-pilot-01` 的 38 个冻结 chunks。MUST NOT 推广至未来 Queries、未来 corpus versions、重新入库快照或未来 48-query target dataset。

**Human statement（原文，2026-09-10）：**

> I reviewed the complete frozen 38-chunk snapshot for each Pilot query and confirm that no additional Grade 1–3 evidence is missing.
>
> Under CD-1, currently unlisted query–chunk pairs may be interpreted as implicit Grade 0 for this frozen Pilot snapshot.

**Decision provenance：** 本轮 Human project owner 指令逐题明确 CQ-001～CQ-006 APPROVE，并声明 Overall Pilot Coverage Gate = 6/6 APPROVED。不是从 Codex screening 推断的确认。

## PILOT-CQ-001

**Query：** 公司每天哪些时段要求大家一起协作？

**Query category：** Direct Fact

**Existing Human-reviewed explicit judgments：** 原审阅日期 2026-09-09，Human project owner；Human Grade 3/2/1/0 数量分别为 1/0/1/1。以下 A/B 行是全部 3 项原判断，C 类 35 项原为 coverage pending，现经 Human coverage approval 具有 implicit Grade-0 semantics。本题 `coverage_reviewed = true` / APPROVED。

| file_name             | chunk_index | exact chunk_id                         | concise content preview                  | 当前分类 / 已有 Human grade                    |
| --------------------- | :---------: | :------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| employee_handbook.md  |      0      | `5ce01f7c-a91d-48e6-a10b-0086bc62f552` | NovaTech（诺瓦科技）员工手册 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |      1      | `2392bb84-3ae9-452b-b044-1a538b99e939` | NovaTech（诺瓦科技）员工手册 &gt; 适用范围与服务渠道 本手册介绍员工日常工作安排和共同责任。人力资源部负责考勤、假期和福利咨询，部门负责人协调人员安排；具体费用由财务部按费用制度审核，账号和设备问题由 IT 服务台处理。员工应在入职时阅读手册，联系方式变更后及时更新人事资料。 | B — Explicit Grade 0；Human Grade 0       |
| employee_handbook.md  |      2      | `392ae2da-31b8-4baa-b7dc-03020e492488` | NovaTech（诺瓦科技）员工手册 &gt; 工作时间与考勤 公司通常每周一至周五工作，每日工作八小时。员工可在上午九点至十点之间到岗，午休一小时，下班时间按实际到岗时间顺延。团队需要共同协作的时间为上午十点至十二点、下午两点至五点，客户现场服务另按事先确认的排班执行。 需要临时离岗、调整班次或因交通中断无法按时到岗时，应尽快告知直属负责人。考勤漏记可在三个工作日内提交说明，由负责人核实。延长工作时间… | A — Explicit Positive；Human Grade 3      |
| employee_handbook.md  |      3      | `299c5bed-e316-4cd2-89cd-49670607f802` | NovaTech（诺瓦科技）员工手册 &gt; 试用期与岗位支持 试用期按员工签署的劳动合同约定执行。入职首周由负责人说明岗位目标并指定带教同事，人力资源部安排制度和安全培训。试用期间每月进行一次反馈，围绕工作成果、协作和所需支持沟通，不以单次失误代替整体评价。 转正评估前，员工与负责人共同整理阶段成果和后续发展计划。如岗位要求发生变化，应及时沟通目标，而不是在评估时临时增加此前未说明的考核项目。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |      4      | `193a39de-16cc-456f-85b8-74e801991e28` | NovaTech（诺瓦科技）员工手册 &gt; 年假与病假 年度带薪假期额度由人力资源部依据适用规定、员工履历和公司福利安排核定，并在员工系统中公布。通常连续请假三天以内提前三个工作日申请，超过三天提前十个工作日申请。负责人应结合项目交接安排休假，不要求员工在休假期间持续在线。 突发疾病无法工作时，应在能够联系的情况下及时告知负责人，并在返岗后三个工作日内补办病假记录；连续病假超过两天时提供就诊或休养证… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |      5      | `992fccef-928e-4c84-9233-3f45b900a0ad` | NovaTech（诺瓦科技）员工手册 &gt; 远程办公 完成试用期且岗位适合远程协作的员工，可以申请每周最多两天远程办公；负责人根据客户服务、现场工作和团队协作需要审批。常规申请在前一工作日下班前提交，临时照护或交通异常可以单独说明。远程办公不是休假，员工应保持约定协作时段可联系，并做好任务交接。 远程办公原则上使用公司设备。接入内部系统、文件共享和信息保护须遵守 &#91;信息安全制度&#93;(it_securi… | A — Explicit Positive；Human Grade 1      |
| employee_handbook.md  |      6      | `ca1a91b1-f45e-4527-9857-277ec4304ed9` | NovaTech（诺瓦科技）员工手册 &gt; 培训与职业发展 公司为新员工安排入职培训，为在岗员工提供内部分享和岗位技能学习机会。部门负责人在季度沟通中讨论能力发展需求，内部培训通常在工作时间内进行，参与人员应提前协调手头任务。 参加收费的外部课程，应先提交课程内容、业务关联、时间和费用预算，由负责人及人力资源部确认。获批参加课程不等于所有附带开支都可报销；课程费、交通与住宿的具体要求见 &#91;费用报销制… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |      7      | `9adc2e17-14ed-407a-8d70-aaa61e65ca6c` | NovaTech（诺瓦科技）员工手册 &gt; 员工福利 公司提供年度健康检查、工作日办公区茶水及员工关怀活动。健康检查由人力资源部统一预约；员工自行选择额外检查项目时，应先确认是否属于公司承担范围。部门团建需在部门预算内安排，不以个人垫付代替活动审批。 福利名额或活动日期发生调整时，人力资源部通过员工公告说明。员工应只提交办理福利必要的信息，体检报告等个人敏感材料不作为部门活动报名附件。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |      8      | `424e7665-108d-45da-b26f-6687c39c0834` | NovaTech（诺瓦科技）员工手册 &gt; 出差与费用责任 员工外出前应说明业务目的、地点、时间及预计费用，按 &#91;差旅管理制度&#93;(travel_policy.md) 取得批准。出行中保留与业务相关的订单、票据和变更记录，返回后按 &#91;费用报销制度&#93;(expense_policy.md) 办理结算。负责人负责业务真实性，财务部负责票据与标准核验；批准出差不等于豁免费用限额。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |      9      | `b7ad1041-2858-4162-b4cc-7b40961751c8` | NovaTech（诺瓦科技）员工手册 &gt; 信息保护与离职交接 员工对工作中接触的客户、产品和人员信息承担保密责任。离开工位应锁屏，发现可疑邮件、设备遗失或账号异常应及时联系 IT 服务台，不自行删除线索。具体处置与外部共享要求见 &#91;信息安全制度&#93;(it_security_policy.md)。 岗位调整或离职时，应将项目文件交回团队指定空间，归还公司设备和门禁介质，并与负责人、人力资源部和 IT … | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |      0      | `ea76f783-595b-4535-89ae-748258020c85` | NovaTech（诺瓦科技）费用报销制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |      1      | `605740ab-0d52-4655-81db-b9bcb008f6ed` | NovaTech（诺瓦科技）费用报销制度 &gt; 费用原则与提交期限 可报销费用应与公司业务直接相关、实际发生，并具备必要批准和有效凭证。员工应优先使用公司采购或统一预订渠道，确需垫付时说明用途，不将未经批准的个人消费转作公司支出。 普通零星费用应在发生后十五个工作日内提交；普通差旅及外部培训行程的费用，应在行程结束后十个工作日内集中提交。跨月费用仍按对应期限办理。因商家补票等客观原因延迟，应在期限内… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |      2      | `e3075f5f-eb85-4faf-9c1e-c560dfdcfb45` | NovaTech（诺瓦科技）费用报销制度 &gt; 发票与证明材料 境内采购和消费应取得抬头及识别信息正确的有效发票，电子发票直接提交原始电子文件。仅有付款截图不能替代发票；同时提供订单、支付记录或明细，以说明实际购买内容。发票信息错误时应联系开票方更正，不得自行修改文件内容。 确实无法取得境内发票的境外费用，可提交当地收据、支付凭证及业务说明，由财务按专项预算核验。外币金额需注明币种和交易日期，使用实… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |      3      | `c59ef50b-ba8a-4ab0-8bc2-2bcb350c3bbf` | NovaTech（诺瓦科技）费用报销制度 &gt; 审批与结算 申请人填写费用类别、业务事项、项目或部门归属，并关联事前批准。直属负责人确认业务真实性，预算负责人核验额度，财务检查票据、标准和重复申报。材料不完整时退回补充，不将退回修改视为最终拒付。 财务审核通过后纳入下一次付款安排，每周三集中支付；遇非工作日顺延。员工垫付返还至本人登记账户。对审核意见有异议时，可补充业务材料请求复核，不通过拆分报销单… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |      4      | `ff9dca7a-cc8b-41d6-a0ae-ed591b1d252f` | NovaTech（诺瓦科技）费用报销制度 &gt; 员工垫付与公司卡 员工垫付前应确认项目预算；大额采购宜由采购部门统一下单，不要求员工长期承担公司资金周转。需预借差旅款的，提交获批预算并在行程结算时核销，多余款项退回公司。 使用公司卡同样需要业务批准、发票及消费明细。公司卡已支付的金额不再向员工个人返款，但必须提交费用归属并完成对账。一次消费不得既申报员工垫付又登记公司卡报销。退款、折扣和商家返还金额… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |      5      | `8d63e548-66a8-41c7-83f3-778a0b66c9d5` | NovaTech（诺瓦科技）费用报销制度 &gt; 普通差旅费用 普通商务出差的交通、住宿和餐费补助按 &#91;差旅管理制度&#93;(travel_policy.md) 审核。报销时附差旅申请、实际行程及住宿明细；交通、住宿等实报实销项目在限额内按实际金额结算。餐费补助按差旅制度规定的日标准及扣减规则计算，无需逐餐提交个人餐饮发票。未经批准的私人延住、观光和同行亲友费用不属于公务支出。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |      6      | `baf22e41-98da-4746-9765-55e7e437a3a0` | NovaTech（诺瓦科技）费用报销制度 &gt; 业务招待 客户或合作方招待应在发生前说明业务目的、参加人数及预算，由直属负责人和预算负责人批准。餐饮招待通常每人每次不超过人民币 200 元；预计超过该标准时，须另获财务负责人特别批准。 报销时提供实际人数、业务事项及消费明细，避免记录不必要的客户个人信息。同一餐由公司承担招待费用后，参加该餐的出差员工应按差旅制度扣减个人餐费补助。与业务无关的聚餐、私… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |      7      | `7b2fbf99-8274-4610-ac08-3c3e7259ad09` | NovaTech（诺瓦科技）费用报销制度 &gt; 获批外部培训费用 收费的外部培训须先由直属负责人和人力资源部确认课程及参加资格，再由预算负责人批准费用。课程费按获批课程报价和实际支付额核销，交通费用按培训预算及有效票据报销；培训报名获批不代表允许更换高价课程或无预算增加陪同人员。 外部培训住宿按每间每晚人民币 350 元上限、凭票据实报实销，不发放定额住宿补贴。该标准适用于获批外部培训所需住宿，不区… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |      8      | `0a7b4a44-4ac1-49da-a973-6ee14d4792a8` | NovaTech（诺瓦科技）费用报销制度 &gt; 超限、变更与不予报销事项 超出已批准标准或预算的费用，应补充原因和特别批准记录。普通差旅住宿例外依差旅制度处理，外部培训例外依本制度培训条款处理；其他费用在发生前由预算负责人及财务负责人批准。拆分发票、分次提交或改写费用类别不能使超限费用自动合规。 培训取消或行程变更取得退款时，应及时告知财务；业务原因产生的必要退改损失提供证明后审核，个人原因产生的损… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      0      | `03cecd2d-125a-4454-80b3-19bb40296df2` | NovaTech（诺瓦科技）信息安全制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      1      | `176b8225-18b7-479d-b02b-aa3d0be7f724` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号、密码与 MFA 员工使用本人公司账号开展工作，不得共享账号、代收验证码或借用同事权限。密码至少十四位，应避免姓名、生日和连续数字，不得与个人网站密码重复。公司提供密码管理工具保存工作凭据；不得把密码写入共享文档、聊天记录或源代码。 公司邮箱、VPN 及远程访问系统必须启用多因素认证（MFA）。员工应只确认由本人发起的登录请求；收到意外推送时拒绝批… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      2      | `8bc6437d-8da4-43c0-8ad6-9d04b1bee39f` | NovaTech（诺瓦科技）信息安全制度 &gt; 网络接入与 VPN 通过公共或不可信网络访问公司内部系统，必须先连接公司 VPN，并使用 MFA 完成认证。酒店、机场和咖啡馆网络属于此类环境；家庭网络未纳入公司受管网络，也按不可信网络处理。连接 VPN 不意味着可以忽略设备更新、屏幕遮挡和文件权限。 在受管办公网络中，员工按已有授权访问内部系统；不能因为处于办公室就借用他人账号。VPN 不可用时应联… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      3      | `dbc829fc-563c-440d-af99-f9b1ccaffa5b` | NovaTech（诺瓦科技）信息安全制度 &gt; 公司设备与软件 工作原则上使用公司配置的电脑和移动设备，保持磁盘加密、终端防护及自动锁屏开启。离开工位立即锁屏，系统空闲五分钟后自动锁定。员工不得自行关闭安全软件、使用未经批准的管理员权限或安装来源不明的插件。 IT 推送的关键安全更新应在两个工作日内完成。确因现场业务无法按期更新时，提前联系 IT 确认临时保护措施和补装时间。设备故障、遗失或被盗应尽… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      4      | `6f911609-ca55-4da1-a326-60c2dd8d9dfa` | NovaTech（诺瓦科技）信息安全制度 &gt; 数据分类与处理 公司信息按公开、内部、保密三个等级管理。已正式发布的产品介绍可作为公开资料；未公开的内部流程和会议安排属于内部信息；客户合同、产品源代码、账号凭据及员工个人资料属于保密信息。对分类不确定时先向资料负责人确认，不自行降低等级以方便发送。 资料负责人决定访问范围，团队按最小必要权限开展协作。财务票据可能包含账户、行程和客户信息，人事假期材料… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      5      | `3554a997-36e8-4376-b16c-6b353976e167` | NovaTech（诺瓦科技）信息安全制度 &gt; 文件共享与外部协作 内部协作使用公司批准的文档空间，按人员或工作组授权。对外共享内部资料，应先取得资料负责人批准，使用实名访问的受控链接并设置到期时间；保密资料对外提供还需安全负责人确认目的和保护措施。不得使用“任何人持链接可访问”的方式发送内部或保密文件。 项目结束或协作人员退出后，资料负责人应及时撤销访问权限。禁止通过个人邮箱、个人网盘或未获批准的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      6      | `02a3ade4-c272-4212-b5de-f512437f75a7` | NovaTech（诺瓦科技）信息安全制度 &gt; 可移动存储与打印 默认不使用个人 U 盘或移动硬盘搬运工作文件。现场交付确需离线介质时，应向 IT 申请公司登记的加密介质，记录资料用途，交付完成后归还或按要求清除。未知来源的存储设备不得接入公司电脑。 打印保密材料应选择受控打印设备，及时取走并核对份数；废弃副本投入保密销毁箱。出差期间不得把合同、设备或工作介质留在无人看管的公共区域。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      7      | `f7017394-093c-4e03-98b4-2513089a96b2` | NovaTech（诺瓦科技）信息安全制度 &gt; 钓鱼邮件与可疑链接 遇到要求紧急付款、修改收款账户或输入密码的邮件，应通过已知联系方式另行核实，不直接使用可疑邮件提供的电话号码。未知附件、二维码和登录页面在核实前不要打开或输入信息。客户或领导的显示姓名不能单独证明邮件可信。 发现可疑邮件可通过公司邮件举报入口或 IT 服务台报告，保留原邮件，不在团队群中继续转发危险链接。已经点击或下载时也应如实说明… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      8      | `d111e21f-b2a6-461a-9cec-b7189635546f` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号异常与安全事件 发现非本人登录、意外 MFA 请求或疑似凭据泄露时，应立即通过可信渠道联系 IT 服务台。若怀疑当前设备感染恶意软件，先停止敏感操作并断开网络，使用另一台可信设备或电话报告。不要在疑似受控设备上反复输入新密码。 IT 根据情况暂停账号会话、协助更换凭据并保存日志；员工提供发生时间和已进行的操作，不自行删除邮件、重装系统或清空记录。涉… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |      9      | `6332122f-aa36-4c49-ac9a-f36d252171df` | NovaTech（诺瓦科技）信息安全制度 &gt; 远程办公、出差与离职 远程办公申请按 &#91;员工手册&#93;(employee_handbook.md) 办理，批准办公地点不等于批准使用个人设备或个人存储。出差连接酒店网络访问内部系统仍须使用公司 VPN；在公共场所应避免旁人看到屏幕或听到客户敏感信息。 离职或岗位变动前，将工作成果移交至团队指定空间，由负责人核对权限和资料归属。公司设备、加密介质及认证设备交… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |      0      | `72a1bf30-caec-42ee-ab67-31108e9d1e86` | NovaTech（诺瓦科技）差旅管理制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |      1      | `14f54027-316e-4f40-b50d-022696ec4f77` | NovaTech（诺瓦科技）差旅管理制度 &gt; 适用范围与出行目的 本制度适用于客户拜访、项目交付、供应商沟通等普通商务出差。员工应根据实际业务目的登记行程，不因出行地点相同就将不同活动合并申报。 已获批准的外部培训，其课程费、交通、住宿和其他费用适用 &#91;费用报销制度&#93;(expense_policy.md) 的外部培训条款，不适用本制度的普通差旅住宿限额和餐费补助。兼有培训与客户拜访的行程，应在申请… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |      2      | `330edce0-9b09-47ef-b371-9fa470b74dd0` | NovaTech（诺瓦科技）差旅管理制度 &gt; 差旅申请与审批 境内普通出差原则上提前三个工作日提交申请，注明业务目标、客户或项目、城市、起止日期及费用预算，经直属负责人和预算负责人批准后再预订。申请人应确认现场接待安排，避免仅因交通优惠而提前购买不可退改的行程。 紧急客户故障等无法提前办理的情况，可先通过公司沟通渠道取得负责人书面确认，并在下一个工作日补交申请。预计费用超出预算时，应说明增加原因并… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |      3      | `9c9bf530-eb9c-4aeb-8e0f-a634fc217662` | NovaTech（诺瓦科技）差旅管理制度 &gt; 城际交通 境内出行优先选择能够合理到达的高铁二等座或飞机经济舱。选择航班时综合考虑出发时间、接驳成本和退改条件，不要求员工为节省少量票价搭乘影响正常休息的行程。无普通席位而确需升级时，应在购买前说明可选方案，由预算负责人批准。 个人行程与公务行程衔接时，私人部分费用由员工承担。使用私家车开展公务应事先说明路线和用途，经批准后按可核验的业务里程和实际必要… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |      4      | `e9289ccd-a3ca-4c8e-9f29-910dbd49018c` | NovaTech（诺瓦科技）差旅管理制度 &gt; 普通商务出差住宿 境内普通商务出差，一线城市按每间每晚人民币 500 元为住宿报销上限，其他境内城市按每间每晚人民币 350 元为上限。本制度中的一线城市指北京、上海、广州和深圳。费用按实际发生额报销，上限不是固定发放的住宿补贴；自行免费住宿不领取住宿费。 住宿限额包含房费及必须支付的服务费用，不包含私人消费。员工应选择安全、交通合理的住宿地点。连续住… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |      5      | `d62a0153-11c5-434e-b15d-7b12ddb5d208` | NovaTech（诺瓦科技）差旅管理制度 &gt; 住宿超限与特别批准 展会期间房源紧张、客户指定现场住宿或安全条件限制导致无法在标准内预订时，应保留可选酒店报价，说明超限原因、晚数和预计总额，在预订前取得预算负责人及财务负责人的特别批准。普通差旅申请获批不等于超限申请获批。 途中发生突发取消、恶劣天气或安全事件，确需立即安排住宿的，应先保障人身安全，尽快报告负责人，并在两个工作日内补交情况和费用证明。… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |      6      | `de7f21a2-36a6-4ecf-ad67-5e201cae01b4` | NovaTech（诺瓦科技）差旅管理制度 &gt; 餐费补助与市内交通 境内普通商务出差餐费补助为每人每天人民币 80 元，按批准的实际出差自然日计算。客户或会议主办方提供工作餐时，每餐扣减 30 元，当日补助最低为零；不得同时申报已由他方承担的同一餐费用。业务招待另按费用报销制度办理，不计作个人餐费。 市内交通优先采用公共交通。携带设备、赶赴早晚班次或目的地公共交通不便时，可以选择合规出租车或网约车，… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |      7      | `5a501652-d3dd-46bf-bba0-9a3ded2c093b` | NovaTech（诺瓦科技）差旅管理制度 &gt; 取消、改签与行程延长 业务安排变化后，应及时取消不再需要的交通和住宿，减少退改损失。因客户变更或不可抗力发生的合理退改费用，提供变更原因及订单记录后可申请报销；个人原因导致的费用由个人承担。退款必须在结算时冲减，不得按原价报销已退回的款项。 延长出差天数或新增城市，应重新确认业务目的和预算。周末留宿如为衔接公务且比往返更合理，可事先申请；私人休闲产生的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |      8      | `1be0cf45-bf45-40f7-8975-0a3deb987696` | NovaTech（诺瓦科技）差旅管理制度 &gt; 境外出差与返回交接 境外出差应提前十个工作日提交申请，由部门负责人、财务负责人和总经理批准。预算须单独列明目的地、币种、交通、住宿、保险和必要证件费用；住宿及餐费按获批的境外专项预算执行，不套用境内城市标准。 出发前应了解目的地出行条件并与 IT 确认设备及数据访问安排。返回后及时向团队交接业务进展，按照费用报销制度的提交期限完成结算。报销材料中的客户… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |

### Human Coverage Decision

- [x] APPROVE — I reviewed the full 38-chunk frozen snapshot and confirm that no additional Grade 1–3 evidence is missing. Unlisted chunks may therefore be interpreted as implicit Grade 0 under CD-1.
- [ ] REJECT / NEEDS CHANGES — additional positive evidence exists or current judgments require revision.

Reviewer notes:

Human decision: APPROVE — no additional Grade 1–3 evidence found.

未添加或修改任何显式 relevance judgment。

Reviewer role: Human project owner

Review date: 2026-09-10

Human confirmation provenance: 本轮 Human project owner 对本 Query 的明确 APPROVE 及完整 38-chunk snapshot coverage 声明。

## PILOT-CQ-002

**Query：** 公司账号的密码至少要几位？能和我个人网站的密码用同一个吗？

**Query category：** Direct Fact

**Existing Human-reviewed explicit judgments：** 原审阅日期 2026-09-09，Human project owner；Human Grade 3/2/1/0 数量分别为 1/0/0/1。以下 A/B 行是全部 2 项原判断，C 类 36 项原为 coverage pending，现经 Human coverage approval 具有 implicit Grade-0 semantics。本题 `coverage_reviewed = true` / APPROVED。

| file_name             | chunk_index | exact chunk_id                         | concise content preview                  | 当前分类 / 已有 Human grade                    |
| --------------------- | ----------: | -------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| employee_handbook.md  |           0 | `5ce01f7c-a91d-48e6-a10b-0086bc62f552` | NovaTech（诺瓦科技）员工手册 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | NovaTech（诺瓦科技）员工手册 &gt; 适用范围与服务渠道 本手册介绍员工日常工作安排和共同责任。人力资源部负责考勤、假期和福利咨询，部门负责人协调人员安排；具体费用由财务部按费用制度审核，账号和设备问题由 IT 服务台处理。员工应在入职时阅读手册，联系方式变更后及时更新人事资料。 | B — Explicit Grade 0；Human Grade 0       |
| employee_handbook.md  |           2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | NovaTech（诺瓦科技）员工手册 &gt; 工作时间与考勤 公司通常每周一至周五工作，每日工作八小时。员工可在上午九点至十点之间到岗，午休一小时，下班时间按实际到岗时间顺延。团队需要共同协作的时间为上午十点至十二点、下午两点至五点，客户现场服务另按事先确认的排班执行。 需要临时离岗、调整班次或因交通中断无法按时到岗时，应尽快告知直属负责人。考勤漏记可在三个工作日内提交说明，由负责人核实。延长工作时间… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           3 | `299c5bed-e316-4cd2-89cd-49670607f802` | NovaTech（诺瓦科技）员工手册 &gt; 试用期与岗位支持 试用期按员工签署的劳动合同约定执行。入职首周由负责人说明岗位目标并指定带教同事，人力资源部安排制度和安全培训。试用期间每月进行一次反馈，围绕工作成果、协作和所需支持沟通，不以单次失误代替整体评价。 转正评估前，员工与负责人共同整理阶段成果和后续发展计划。如岗位要求发生变化，应及时沟通目标，而不是在评估时临时增加此前未说明的考核项目。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           4 | `193a39de-16cc-456f-85b8-74e801991e28` | NovaTech（诺瓦科技）员工手册 &gt; 年假与病假 年度带薪假期额度由人力资源部依据适用规定、员工履历和公司福利安排核定，并在员工系统中公布。通常连续请假三天以内提前三个工作日申请，超过三天提前十个工作日申请。负责人应结合项目交接安排休假，不要求员工在休假期间持续在线。 突发疾病无法工作时，应在能够联系的情况下及时告知负责人，并在返岗后三个工作日内补办病假记录；连续病假超过两天时提供就诊或休养证… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           5 | `992fccef-928e-4c84-9233-3f45b900a0ad` | NovaTech（诺瓦科技）员工手册 &gt; 远程办公 完成试用期且岗位适合远程协作的员工，可以申请每周最多两天远程办公；负责人根据客户服务、现场工作和团队协作需要审批。常规申请在前一工作日下班前提交，临时照护或交通异常可以单独说明。远程办公不是休假，员工应保持约定协作时段可联系，并做好任务交接。 远程办公原则上使用公司设备。接入内部系统、文件共享和信息保护须遵守 &#91;信息安全制度&#93;(it_securi… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           6 | `ca1a91b1-f45e-4527-9857-277ec4304ed9` | NovaTech（诺瓦科技）员工手册 &gt; 培训与职业发展 公司为新员工安排入职培训，为在岗员工提供内部分享和岗位技能学习机会。部门负责人在季度沟通中讨论能力发展需求，内部培训通常在工作时间内进行，参与人员应提前协调手头任务。 参加收费的外部课程，应先提交课程内容、业务关联、时间和费用预算，由负责人及人力资源部确认。获批参加课程不等于所有附带开支都可报销；课程费、交通与住宿的具体要求见 &#91;费用报销制… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           7 | `9adc2e17-14ed-407a-8d70-aaa61e65ca6c` | NovaTech（诺瓦科技）员工手册 &gt; 员工福利 公司提供年度健康检查、工作日办公区茶水及员工关怀活动。健康检查由人力资源部统一预约；员工自行选择额外检查项目时，应先确认是否属于公司承担范围。部门团建需在部门预算内安排，不以个人垫付代替活动审批。 福利名额或活动日期发生调整时，人力资源部通过员工公告说明。员工应只提交办理福利必要的信息，体检报告等个人敏感材料不作为部门活动报名附件。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           8 | `424e7665-108d-45da-b26f-6687c39c0834` | NovaTech（诺瓦科技）员工手册 &gt; 出差与费用责任 员工外出前应说明业务目的、地点、时间及预计费用，按 &#91;差旅管理制度&#93;(travel_policy.md) 取得批准。出行中保留与业务相关的订单、票据和变更记录，返回后按 &#91;费用报销制度&#93;(expense_policy.md) 办理结算。负责人负责业务真实性，财务部负责票据与标准核验；批准出差不等于豁免费用限额。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           9 | `b7ad1041-2858-4162-b4cc-7b40961751c8` | NovaTech（诺瓦科技）员工手册 &gt; 信息保护与离职交接 员工对工作中接触的客户、产品和人员信息承担保密责任。离开工位应锁屏，发现可疑邮件、设备遗失或账号异常应及时联系 IT 服务台，不自行删除线索。具体处置与外部共享要求见 &#91;信息安全制度&#93;(it_security_policy.md)。 岗位调整或离职时，应将项目文件交回团队指定空间，归还公司设备和门禁介质，并与负责人、人力资源部和 IT … | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           0 | `ea76f783-595b-4535-89ae-748258020c85` | NovaTech（诺瓦科技）费用报销制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           1 | `605740ab-0d52-4655-81db-b9bcb008f6ed` | NovaTech（诺瓦科技）费用报销制度 &gt; 费用原则与提交期限 可报销费用应与公司业务直接相关、实际发生，并具备必要批准和有效凭证。员工应优先使用公司采购或统一预订渠道，确需垫付时说明用途，不将未经批准的个人消费转作公司支出。 普通零星费用应在发生后十五个工作日内提交；普通差旅及外部培训行程的费用，应在行程结束后十个工作日内集中提交。跨月费用仍按对应期限办理。因商家补票等客观原因延迟，应在期限内… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           2 | `e3075f5f-eb85-4faf-9c1e-c560dfdcfb45` | NovaTech（诺瓦科技）费用报销制度 &gt; 发票与证明材料 境内采购和消费应取得抬头及识别信息正确的有效发票，电子发票直接提交原始电子文件。仅有付款截图不能替代发票；同时提供订单、支付记录或明细，以说明实际购买内容。发票信息错误时应联系开票方更正，不得自行修改文件内容。 确实无法取得境内发票的境外费用，可提交当地收据、支付凭证及业务说明，由财务按专项预算核验。外币金额需注明币种和交易日期，使用实… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           3 | `c59ef50b-ba8a-4ab0-8bc2-2bcb350c3bbf` | NovaTech（诺瓦科技）费用报销制度 &gt; 审批与结算 申请人填写费用类别、业务事项、项目或部门归属，并关联事前批准。直属负责人确认业务真实性，预算负责人核验额度，财务检查票据、标准和重复申报。材料不完整时退回补充，不将退回修改视为最终拒付。 财务审核通过后纳入下一次付款安排，每周三集中支付；遇非工作日顺延。员工垫付返还至本人登记账户。对审核意见有异议时，可补充业务材料请求复核，不通过拆分报销单… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           4 | `ff9dca7a-cc8b-41d6-a0ae-ed591b1d252f` | NovaTech（诺瓦科技）费用报销制度 &gt; 员工垫付与公司卡 员工垫付前应确认项目预算；大额采购宜由采购部门统一下单，不要求员工长期承担公司资金周转。需预借差旅款的，提交获批预算并在行程结算时核销，多余款项退回公司。 使用公司卡同样需要业务批准、发票及消费明细。公司卡已支付的金额不再向员工个人返款，但必须提交费用归属并完成对账。一次消费不得既申报员工垫付又登记公司卡报销。退款、折扣和商家返还金额… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           5 | `8d63e548-66a8-41c7-83f3-778a0b66c9d5` | NovaTech（诺瓦科技）费用报销制度 &gt; 普通差旅费用 普通商务出差的交通、住宿和餐费补助按 &#91;差旅管理制度&#93;(travel_policy.md) 审核。报销时附差旅申请、实际行程及住宿明细；交通、住宿等实报实销项目在限额内按实际金额结算。餐费补助按差旅制度规定的日标准及扣减规则计算，无需逐餐提交个人餐饮发票。未经批准的私人延住、观光和同行亲友费用不属于公务支出。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           6 | `baf22e41-98da-4746-9765-55e7e437a3a0` | NovaTech（诺瓦科技）费用报销制度 &gt; 业务招待 客户或合作方招待应在发生前说明业务目的、参加人数及预算，由直属负责人和预算负责人批准。餐饮招待通常每人每次不超过人民币 200 元；预计超过该标准时，须另获财务负责人特别批准。 报销时提供实际人数、业务事项及消费明细，避免记录不必要的客户个人信息。同一餐由公司承担招待费用后，参加该餐的出差员工应按差旅制度扣减个人餐费补助。与业务无关的聚餐、私… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           7 | `7b2fbf99-8274-4610-ac08-3c3e7259ad09` | NovaTech（诺瓦科技）费用报销制度 &gt; 获批外部培训费用 收费的外部培训须先由直属负责人和人力资源部确认课程及参加资格，再由预算负责人批准费用。课程费按获批课程报价和实际支付额核销，交通费用按培训预算及有效票据报销；培训报名获批不代表允许更换高价课程或无预算增加陪同人员。 外部培训住宿按每间每晚人民币 350 元上限、凭票据实报实销，不发放定额住宿补贴。该标准适用于获批外部培训所需住宿，不区… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           8 | `0a7b4a44-4ac1-49da-a973-6ee14d4792a8` | NovaTech（诺瓦科技）费用报销制度 &gt; 超限、变更与不予报销事项 超出已批准标准或预算的费用，应补充原因和特别批准记录。普通差旅住宿例外依差旅制度处理，外部培训例外依本制度培训条款处理；其他费用在发生前由预算负责人及财务负责人批准。拆分发票、分次提交或改写费用类别不能使超限费用自动合规。 培训取消或行程变更取得退款时，应及时告知财务；业务原因产生的必要退改损失提供证明后审核，个人原因产生的损… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           0 | `03cecd2d-125a-4454-80b3-19bb40296df2` | NovaTech（诺瓦科技）信息安全制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号、密码与 MFA 员工使用本人公司账号开展工作，不得共享账号、代收验证码或借用同事权限。密码至少十四位，应避免姓名、生日和连续数字，不得与个人网站密码重复。公司提供密码管理工具保存工作凭据；不得把密码写入共享文档、聊天记录或源代码。 公司邮箱、VPN 及远程访问系统必须启用多因素认证（MFA）。员工应只确认由本人发起的登录请求；收到意外推送时拒绝批… | A — Explicit Positive；Human Grade 3      |
| it_security_policy.md |           2 | `8bc6437d-8da4-43c0-8ad6-9d04b1bee39f` | NovaTech（诺瓦科技）信息安全制度 &gt; 网络接入与 VPN 通过公共或不可信网络访问公司内部系统，必须先连接公司 VPN，并使用 MFA 完成认证。酒店、机场和咖啡馆网络属于此类环境；家庭网络未纳入公司受管网络，也按不可信网络处理。连接 VPN 不意味着可以忽略设备更新、屏幕遮挡和文件权限。 在受管办公网络中，员工按已有授权访问内部系统；不能因为处于办公室就借用他人账号。VPN 不可用时应联… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           3 | `dbc829fc-563c-440d-af99-f9b1ccaffa5b` | NovaTech（诺瓦科技）信息安全制度 &gt; 公司设备与软件 工作原则上使用公司配置的电脑和移动设备，保持磁盘加密、终端防护及自动锁屏开启。离开工位立即锁屏，系统空闲五分钟后自动锁定。员工不得自行关闭安全软件、使用未经批准的管理员权限或安装来源不明的插件。 IT 推送的关键安全更新应在两个工作日内完成。确因现场业务无法按期更新时，提前联系 IT 确认临时保护措施和补装时间。设备故障、遗失或被盗应尽… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           4 | `6f911609-ca55-4da1-a326-60c2dd8d9dfa` | NovaTech（诺瓦科技）信息安全制度 &gt; 数据分类与处理 公司信息按公开、内部、保密三个等级管理。已正式发布的产品介绍可作为公开资料；未公开的内部流程和会议安排属于内部信息；客户合同、产品源代码、账号凭据及员工个人资料属于保密信息。对分类不确定时先向资料负责人确认，不自行降低等级以方便发送。 资料负责人决定访问范围，团队按最小必要权限开展协作。财务票据可能包含账户、行程和客户信息，人事假期材料… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           5 | `3554a997-36e8-4376-b16c-6b353976e167` | NovaTech（诺瓦科技）信息安全制度 &gt; 文件共享与外部协作 内部协作使用公司批准的文档空间，按人员或工作组授权。对外共享内部资料，应先取得资料负责人批准，使用实名访问的受控链接并设置到期时间；保密资料对外提供还需安全负责人确认目的和保护措施。不得使用“任何人持链接可访问”的方式发送内部或保密文件。 项目结束或协作人员退出后，资料负责人应及时撤销访问权限。禁止通过个人邮箱、个人网盘或未获批准的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           6 | `02a3ade4-c272-4212-b5de-f512437f75a7` | NovaTech（诺瓦科技）信息安全制度 &gt; 可移动存储与打印 默认不使用个人 U 盘或移动硬盘搬运工作文件。现场交付确需离线介质时，应向 IT 申请公司登记的加密介质，记录资料用途，交付完成后归还或按要求清除。未知来源的存储设备不得接入公司电脑。 打印保密材料应选择受控打印设备，及时取走并核对份数；废弃副本投入保密销毁箱。出差期间不得把合同、设备或工作介质留在无人看管的公共区域。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           7 | `f7017394-093c-4e03-98b4-2513089a96b2` | NovaTech（诺瓦科技）信息安全制度 &gt; 钓鱼邮件与可疑链接 遇到要求紧急付款、修改收款账户或输入密码的邮件，应通过已知联系方式另行核实，不直接使用可疑邮件提供的电话号码。未知附件、二维码和登录页面在核实前不要打开或输入信息。客户或领导的显示姓名不能单独证明邮件可信。 发现可疑邮件可通过公司邮件举报入口或 IT 服务台报告，保留原邮件，不在团队群中继续转发危险链接。已经点击或下载时也应如实说明… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           8 | `d111e21f-b2a6-461a-9cec-b7189635546f` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号异常与安全事件 发现非本人登录、意外 MFA 请求或疑似凭据泄露时，应立即通过可信渠道联系 IT 服务台。若怀疑当前设备感染恶意软件，先停止敏感操作并断开网络，使用另一台可信设备或电话报告。不要在疑似受控设备上反复输入新密码。 IT 根据情况暂停账号会话、协助更换凭据并保存日志；员工提供发生时间和已进行的操作，不自行删除邮件、重装系统或清空记录。涉… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           9 | `6332122f-aa36-4c49-ac9a-f36d252171df` | NovaTech（诺瓦科技）信息安全制度 &gt; 远程办公、出差与离职 远程办公申请按 &#91;员工手册&#93;(employee_handbook.md) 办理，批准办公地点不等于批准使用个人设备或个人存储。出差连接酒店网络访问内部系统仍须使用公司 VPN；在公共场所应避免旁人看到屏幕或听到客户敏感信息。 离职或岗位变动前，将工作成果移交至团队指定空间，由负责人核对权限和资料归属。公司设备、加密介质及认证设备交… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           0 | `72a1bf30-caec-42ee-ab67-31108e9d1e86` | NovaTech（诺瓦科技）差旅管理制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           1 | `14f54027-316e-4f40-b50d-022696ec4f77` | NovaTech（诺瓦科技）差旅管理制度 &gt; 适用范围与出行目的 本制度适用于客户拜访、项目交付、供应商沟通等普通商务出差。员工应根据实际业务目的登记行程，不因出行地点相同就将不同活动合并申报。 已获批准的外部培训，其课程费、交通、住宿和其他费用适用 &#91;费用报销制度&#93;(expense_policy.md) 的外部培训条款，不适用本制度的普通差旅住宿限额和餐费补助。兼有培训与客户拜访的行程，应在申请… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           2 | `330edce0-9b09-47ef-b371-9fa470b74dd0` | NovaTech（诺瓦科技）差旅管理制度 &gt; 差旅申请与审批 境内普通出差原则上提前三个工作日提交申请，注明业务目标、客户或项目、城市、起止日期及费用预算，经直属负责人和预算负责人批准后再预订。申请人应确认现场接待安排，避免仅因交通优惠而提前购买不可退改的行程。 紧急客户故障等无法提前办理的情况，可先通过公司沟通渠道取得负责人书面确认，并在下一个工作日补交申请。预计费用超出预算时，应说明增加原因并… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           3 | `9c9bf530-eb9c-4aeb-8e0f-a634fc217662` | NovaTech（诺瓦科技）差旅管理制度 &gt; 城际交通 境内出行优先选择能够合理到达的高铁二等座或飞机经济舱。选择航班时综合考虑出发时间、接驳成本和退改条件，不要求员工为节省少量票价搭乘影响正常休息的行程。无普通席位而确需升级时，应在购买前说明可选方案，由预算负责人批准。 个人行程与公务行程衔接时，私人部分费用由员工承担。使用私家车开展公务应事先说明路线和用途，经批准后按可核验的业务里程和实际必要… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           4 | `e9289ccd-a3ca-4c8e-9f29-910dbd49018c` | NovaTech（诺瓦科技）差旅管理制度 &gt; 普通商务出差住宿 境内普通商务出差，一线城市按每间每晚人民币 500 元为住宿报销上限，其他境内城市按每间每晚人民币 350 元为上限。本制度中的一线城市指北京、上海、广州和深圳。费用按实际发生额报销，上限不是固定发放的住宿补贴；自行免费住宿不领取住宿费。 住宿限额包含房费及必须支付的服务费用，不包含私人消费。员工应选择安全、交通合理的住宿地点。连续住… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           5 | `d62a0153-11c5-434e-b15d-7b12ddb5d208` | NovaTech（诺瓦科技）差旅管理制度 &gt; 住宿超限与特别批准 展会期间房源紧张、客户指定现场住宿或安全条件限制导致无法在标准内预订时，应保留可选酒店报价，说明超限原因、晚数和预计总额，在预订前取得预算负责人及财务负责人的特别批准。普通差旅申请获批不等于超限申请获批。 途中发生突发取消、恶劣天气或安全事件，确需立即安排住宿的，应先保障人身安全，尽快报告负责人，并在两个工作日内补交情况和费用证明。… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           6 | `de7f21a2-36a6-4ecf-ad67-5e201cae01b4` | NovaTech（诺瓦科技）差旅管理制度 &gt; 餐费补助与市内交通 境内普通商务出差餐费补助为每人每天人民币 80 元，按批准的实际出差自然日计算。客户或会议主办方提供工作餐时，每餐扣减 30 元，当日补助最低为零；不得同时申报已由他方承担的同一餐费用。业务招待另按费用报销制度办理，不计作个人餐费。 市内交通优先采用公共交通。携带设备、赶赴早晚班次或目的地公共交通不便时，可以选择合规出租车或网约车，… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           7 | `5a501652-d3dd-46bf-bba0-9a3ded2c093b` | NovaTech（诺瓦科技）差旅管理制度 &gt; 取消、改签与行程延长 业务安排变化后，应及时取消不再需要的交通和住宿，减少退改损失。因客户变更或不可抗力发生的合理退改费用，提供变更原因及订单记录后可申请报销；个人原因导致的费用由个人承担。退款必须在结算时冲减，不得按原价报销已退回的款项。 延长出差天数或新增城市，应重新确认业务目的和预算。周末留宿如为衔接公务且比往返更合理，可事先申请；私人休闲产生的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           8 | `1be0cf45-bf45-40f7-8975-0a3deb987696` | NovaTech（诺瓦科技）差旅管理制度 &gt; 境外出差与返回交接 境外出差应提前十个工作日提交申请，由部门负责人、财务负责人和总经理批准。预算须单独列明目的地、币种、交通、住宿、保险和必要证件费用；住宿及餐费按获批的境外专项预算执行，不套用境内城市标准。 出发前应了解目的地出行条件并与 IT 确认设备及数据访问安排。返回后及时向团队交接业务进展，按照费用报销制度的提交期限完成结算。报销材料中的客户… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |

### Human Coverage Decision

- [x] APPROVE — I reviewed the full 38-chunk frozen snapshot and confirm that no additional Grade 1–3 evidence is missing. Unlisted chunks may therefore be interpreted as implicit Grade 0 under CD-1.
- [ ] REJECT / NEEDS CHANGES — additional positive evidence exists or current judgments require revision.

Reviewer notes:

Human decision: APPROVE — no additional Grade 1–3 evidence found.

未添加或修改任何显式 relevance judgment。

Reviewer role: Human project owner

Review date: 2026-09-10

Human confirmation provenance: 本轮 Human project owner 对本 Query 的明确 APPROVE 及完整 38-chunk snapshot coverage 声明。

## PILOT-CQ-003

**Query：** 昨天正常上班了，但系统里少了一条考勤记录，我还能补吗？找谁确认、最晚什么时候提交说明？

**Query category：** Paraphrase

**Existing Human-reviewed explicit judgments：** 原审阅日期 2026-09-09，Human project owner；Human Grade 3/2/1/0 数量分别为 1/0/0/2。以下 A/B 行是全部 3 项原判断，C 类 35 项原为 coverage pending，现经 Human coverage approval 具有 implicit Grade-0 semantics。本题 `coverage_reviewed = true` / APPROVED。

| file_name             | chunk_index | exact chunk_id                         | concise content preview                  | 当前分类 / 已有 Human grade                    |
| --------------------- | ----------: | -------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| employee_handbook.md  |           0 | `5ce01f7c-a91d-48e6-a10b-0086bc62f552` | NovaTech（诺瓦科技）员工手册 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | NovaTech（诺瓦科技）员工手册 &gt; 适用范围与服务渠道 本手册介绍员工日常工作安排和共同责任。人力资源部负责考勤、假期和福利咨询，部门负责人协调人员安排；具体费用由财务部按费用制度审核，账号和设备问题由 IT 服务台处理。员工应在入职时阅读手册，联系方式变更后及时更新人事资料。 | B — Explicit Grade 0；Human Grade 0       |
| employee_handbook.md  |           2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | NovaTech（诺瓦科技）员工手册 &gt; 工作时间与考勤 公司通常每周一至周五工作，每日工作八小时。员工可在上午九点至十点之间到岗，午休一小时，下班时间按实际到岗时间顺延。团队需要共同协作的时间为上午十点至十二点、下午两点至五点，客户现场服务另按事先确认的排班执行。 需要临时离岗、调整班次或因交通中断无法按时到岗时，应尽快告知直属负责人。考勤漏记可在三个工作日内提交说明，由负责人核实。延长工作时间… | A — Explicit Positive；Human Grade 3      |
| employee_handbook.md  |           3 | `299c5bed-e316-4cd2-89cd-49670607f802` | NovaTech（诺瓦科技）员工手册 &gt; 试用期与岗位支持 试用期按员工签署的劳动合同约定执行。入职首周由负责人说明岗位目标并指定带教同事，人力资源部安排制度和安全培训。试用期间每月进行一次反馈，围绕工作成果、协作和所需支持沟通，不以单次失误代替整体评价。 转正评估前，员工与负责人共同整理阶段成果和后续发展计划。如岗位要求发生变化，应及时沟通目标，而不是在评估时临时增加此前未说明的考核项目。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           4 | `193a39de-16cc-456f-85b8-74e801991e28` | NovaTech（诺瓦科技）员工手册 &gt; 年假与病假 年度带薪假期额度由人力资源部依据适用规定、员工履历和公司福利安排核定，并在员工系统中公布。通常连续请假三天以内提前三个工作日申请，超过三天提前十个工作日申请。负责人应结合项目交接安排休假，不要求员工在休假期间持续在线。 突发疾病无法工作时，应在能够联系的情况下及时告知负责人，并在返岗后三个工作日内补办病假记录；连续病假超过两天时提供就诊或休养证… | B — Explicit Grade 0；Human Grade 0       |
| employee_handbook.md  |           5 | `992fccef-928e-4c84-9233-3f45b900a0ad` | NovaTech（诺瓦科技）员工手册 &gt; 远程办公 完成试用期且岗位适合远程协作的员工，可以申请每周最多两天远程办公；负责人根据客户服务、现场工作和团队协作需要审批。常规申请在前一工作日下班前提交，临时照护或交通异常可以单独说明。远程办公不是休假，员工应保持约定协作时段可联系，并做好任务交接。 远程办公原则上使用公司设备。接入内部系统、文件共享和信息保护须遵守 &#91;信息安全制度&#93;(it_securi… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           6 | `ca1a91b1-f45e-4527-9857-277ec4304ed9` | NovaTech（诺瓦科技）员工手册 &gt; 培训与职业发展 公司为新员工安排入职培训，为在岗员工提供内部分享和岗位技能学习机会。部门负责人在季度沟通中讨论能力发展需求，内部培训通常在工作时间内进行，参与人员应提前协调手头任务。 参加收费的外部课程，应先提交课程内容、业务关联、时间和费用预算，由负责人及人力资源部确认。获批参加课程不等于所有附带开支都可报销；课程费、交通与住宿的具体要求见 &#91;费用报销制… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           7 | `9adc2e17-14ed-407a-8d70-aaa61e65ca6c` | NovaTech（诺瓦科技）员工手册 &gt; 员工福利 公司提供年度健康检查、工作日办公区茶水及员工关怀活动。健康检查由人力资源部统一预约；员工自行选择额外检查项目时，应先确认是否属于公司承担范围。部门团建需在部门预算内安排，不以个人垫付代替活动审批。 福利名额或活动日期发生调整时，人力资源部通过员工公告说明。员工应只提交办理福利必要的信息，体检报告等个人敏感材料不作为部门活动报名附件。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           8 | `424e7665-108d-45da-b26f-6687c39c0834` | NovaTech（诺瓦科技）员工手册 &gt; 出差与费用责任 员工外出前应说明业务目的、地点、时间及预计费用，按 &#91;差旅管理制度&#93;(travel_policy.md) 取得批准。出行中保留与业务相关的订单、票据和变更记录，返回后按 &#91;费用报销制度&#93;(expense_policy.md) 办理结算。负责人负责业务真实性，财务部负责票据与标准核验；批准出差不等于豁免费用限额。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           9 | `b7ad1041-2858-4162-b4cc-7b40961751c8` | NovaTech（诺瓦科技）员工手册 &gt; 信息保护与离职交接 员工对工作中接触的客户、产品和人员信息承担保密责任。离开工位应锁屏，发现可疑邮件、设备遗失或账号异常应及时联系 IT 服务台，不自行删除线索。具体处置与外部共享要求见 &#91;信息安全制度&#93;(it_security_policy.md)。 岗位调整或离职时，应将项目文件交回团队指定空间，归还公司设备和门禁介质，并与负责人、人力资源部和 IT … | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           0 | `ea76f783-595b-4535-89ae-748258020c85` | NovaTech（诺瓦科技）费用报销制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           1 | `605740ab-0d52-4655-81db-b9bcb008f6ed` | NovaTech（诺瓦科技）费用报销制度 &gt; 费用原则与提交期限 可报销费用应与公司业务直接相关、实际发生，并具备必要批准和有效凭证。员工应优先使用公司采购或统一预订渠道，确需垫付时说明用途，不将未经批准的个人消费转作公司支出。 普通零星费用应在发生后十五个工作日内提交；普通差旅及外部培训行程的费用，应在行程结束后十个工作日内集中提交。跨月费用仍按对应期限办理。因商家补票等客观原因延迟，应在期限内… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           2 | `e3075f5f-eb85-4faf-9c1e-c560dfdcfb45` | NovaTech（诺瓦科技）费用报销制度 &gt; 发票与证明材料 境内采购和消费应取得抬头及识别信息正确的有效发票，电子发票直接提交原始电子文件。仅有付款截图不能替代发票；同时提供订单、支付记录或明细，以说明实际购买内容。发票信息错误时应联系开票方更正，不得自行修改文件内容。 确实无法取得境内发票的境外费用，可提交当地收据、支付凭证及业务说明，由财务按专项预算核验。外币金额需注明币种和交易日期，使用实… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           3 | `c59ef50b-ba8a-4ab0-8bc2-2bcb350c3bbf` | NovaTech（诺瓦科技）费用报销制度 &gt; 审批与结算 申请人填写费用类别、业务事项、项目或部门归属，并关联事前批准。直属负责人确认业务真实性，预算负责人核验额度，财务检查票据、标准和重复申报。材料不完整时退回补充，不将退回修改视为最终拒付。 财务审核通过后纳入下一次付款安排，每周三集中支付；遇非工作日顺延。员工垫付返还至本人登记账户。对审核意见有异议时，可补充业务材料请求复核，不通过拆分报销单… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           4 | `ff9dca7a-cc8b-41d6-a0ae-ed591b1d252f` | NovaTech（诺瓦科技）费用报销制度 &gt; 员工垫付与公司卡 员工垫付前应确认项目预算；大额采购宜由采购部门统一下单，不要求员工长期承担公司资金周转。需预借差旅款的，提交获批预算并在行程结算时核销，多余款项退回公司。 使用公司卡同样需要业务批准、发票及消费明细。公司卡已支付的金额不再向员工个人返款，但必须提交费用归属并完成对账。一次消费不得既申报员工垫付又登记公司卡报销。退款、折扣和商家返还金额… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           5 | `8d63e548-66a8-41c7-83f3-778a0b66c9d5` | NovaTech（诺瓦科技）费用报销制度 &gt; 普通差旅费用 普通商务出差的交通、住宿和餐费补助按 &#91;差旅管理制度&#93;(travel_policy.md) 审核。报销时附差旅申请、实际行程及住宿明细；交通、住宿等实报实销项目在限额内按实际金额结算。餐费补助按差旅制度规定的日标准及扣减规则计算，无需逐餐提交个人餐饮发票。未经批准的私人延住、观光和同行亲友费用不属于公务支出。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           6 | `baf22e41-98da-4746-9765-55e7e437a3a0` | NovaTech（诺瓦科技）费用报销制度 &gt; 业务招待 客户或合作方招待应在发生前说明业务目的、参加人数及预算，由直属负责人和预算负责人批准。餐饮招待通常每人每次不超过人民币 200 元；预计超过该标准时，须另获财务负责人特别批准。 报销时提供实际人数、业务事项及消费明细，避免记录不必要的客户个人信息。同一餐由公司承担招待费用后，参加该餐的出差员工应按差旅制度扣减个人餐费补助。与业务无关的聚餐、私… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           7 | `7b2fbf99-8274-4610-ac08-3c3e7259ad09` | NovaTech（诺瓦科技）费用报销制度 &gt; 获批外部培训费用 收费的外部培训须先由直属负责人和人力资源部确认课程及参加资格，再由预算负责人批准费用。课程费按获批课程报价和实际支付额核销，交通费用按培训预算及有效票据报销；培训报名获批不代表允许更换高价课程或无预算增加陪同人员。 外部培训住宿按每间每晚人民币 350 元上限、凭票据实报实销，不发放定额住宿补贴。该标准适用于获批外部培训所需住宿，不区… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           8 | `0a7b4a44-4ac1-49da-a973-6ee14d4792a8` | NovaTech（诺瓦科技）费用报销制度 &gt; 超限、变更与不予报销事项 超出已批准标准或预算的费用，应补充原因和特别批准记录。普通差旅住宿例外依差旅制度处理，外部培训例外依本制度培训条款处理；其他费用在发生前由预算负责人及财务负责人批准。拆分发票、分次提交或改写费用类别不能使超限费用自动合规。 培训取消或行程变更取得退款时，应及时告知财务；业务原因产生的必要退改损失提供证明后审核，个人原因产生的损… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           0 | `03cecd2d-125a-4454-80b3-19bb40296df2` | NovaTech（诺瓦科技）信息安全制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号、密码与 MFA 员工使用本人公司账号开展工作，不得共享账号、代收验证码或借用同事权限。密码至少十四位，应避免姓名、生日和连续数字，不得与个人网站密码重复。公司提供密码管理工具保存工作凭据；不得把密码写入共享文档、聊天记录或源代码。 公司邮箱、VPN 及远程访问系统必须启用多因素认证（MFA）。员工应只确认由本人发起的登录请求；收到意外推送时拒绝批… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           2 | `8bc6437d-8da4-43c0-8ad6-9d04b1bee39f` | NovaTech（诺瓦科技）信息安全制度 &gt; 网络接入与 VPN 通过公共或不可信网络访问公司内部系统，必须先连接公司 VPN，并使用 MFA 完成认证。酒店、机场和咖啡馆网络属于此类环境；家庭网络未纳入公司受管网络，也按不可信网络处理。连接 VPN 不意味着可以忽略设备更新、屏幕遮挡和文件权限。 在受管办公网络中，员工按已有授权访问内部系统；不能因为处于办公室就借用他人账号。VPN 不可用时应联… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           3 | `dbc829fc-563c-440d-af99-f9b1ccaffa5b` | NovaTech（诺瓦科技）信息安全制度 &gt; 公司设备与软件 工作原则上使用公司配置的电脑和移动设备，保持磁盘加密、终端防护及自动锁屏开启。离开工位立即锁屏，系统空闲五分钟后自动锁定。员工不得自行关闭安全软件、使用未经批准的管理员权限或安装来源不明的插件。 IT 推送的关键安全更新应在两个工作日内完成。确因现场业务无法按期更新时，提前联系 IT 确认临时保护措施和补装时间。设备故障、遗失或被盗应尽… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           4 | `6f911609-ca55-4da1-a326-60c2dd8d9dfa` | NovaTech（诺瓦科技）信息安全制度 &gt; 数据分类与处理 公司信息按公开、内部、保密三个等级管理。已正式发布的产品介绍可作为公开资料；未公开的内部流程和会议安排属于内部信息；客户合同、产品源代码、账号凭据及员工个人资料属于保密信息。对分类不确定时先向资料负责人确认，不自行降低等级以方便发送。 资料负责人决定访问范围，团队按最小必要权限开展协作。财务票据可能包含账户、行程和客户信息，人事假期材料… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           5 | `3554a997-36e8-4376-b16c-6b353976e167` | NovaTech（诺瓦科技）信息安全制度 &gt; 文件共享与外部协作 内部协作使用公司批准的文档空间，按人员或工作组授权。对外共享内部资料，应先取得资料负责人批准，使用实名访问的受控链接并设置到期时间；保密资料对外提供还需安全负责人确认目的和保护措施。不得使用“任何人持链接可访问”的方式发送内部或保密文件。 项目结束或协作人员退出后，资料负责人应及时撤销访问权限。禁止通过个人邮箱、个人网盘或未获批准的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           6 | `02a3ade4-c272-4212-b5de-f512437f75a7` | NovaTech（诺瓦科技）信息安全制度 &gt; 可移动存储与打印 默认不使用个人 U 盘或移动硬盘搬运工作文件。现场交付确需离线介质时，应向 IT 申请公司登记的加密介质，记录资料用途，交付完成后归还或按要求清除。未知来源的存储设备不得接入公司电脑。 打印保密材料应选择受控打印设备，及时取走并核对份数；废弃副本投入保密销毁箱。出差期间不得把合同、设备或工作介质留在无人看管的公共区域。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           7 | `f7017394-093c-4e03-98b4-2513089a96b2` | NovaTech（诺瓦科技）信息安全制度 &gt; 钓鱼邮件与可疑链接 遇到要求紧急付款、修改收款账户或输入密码的邮件，应通过已知联系方式另行核实，不直接使用可疑邮件提供的电话号码。未知附件、二维码和登录页面在核实前不要打开或输入信息。客户或领导的显示姓名不能单独证明邮件可信。 发现可疑邮件可通过公司邮件举报入口或 IT 服务台报告，保留原邮件，不在团队群中继续转发危险链接。已经点击或下载时也应如实说明… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           8 | `d111e21f-b2a6-461a-9cec-b7189635546f` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号异常与安全事件 发现非本人登录、意外 MFA 请求或疑似凭据泄露时，应立即通过可信渠道联系 IT 服务台。若怀疑当前设备感染恶意软件，先停止敏感操作并断开网络，使用另一台可信设备或电话报告。不要在疑似受控设备上反复输入新密码。 IT 根据情况暂停账号会话、协助更换凭据并保存日志；员工提供发生时间和已进行的操作，不自行删除邮件、重装系统或清空记录。涉… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           9 | `6332122f-aa36-4c49-ac9a-f36d252171df` | NovaTech（诺瓦科技）信息安全制度 &gt; 远程办公、出差与离职 远程办公申请按 &#91;员工手册&#93;(employee_handbook.md) 办理，批准办公地点不等于批准使用个人设备或个人存储。出差连接酒店网络访问内部系统仍须使用公司 VPN；在公共场所应避免旁人看到屏幕或听到客户敏感信息。 离职或岗位变动前，将工作成果移交至团队指定空间，由负责人核对权限和资料归属。公司设备、加密介质及认证设备交… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           0 | `72a1bf30-caec-42ee-ab67-31108e9d1e86` | NovaTech（诺瓦科技）差旅管理制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           1 | `14f54027-316e-4f40-b50d-022696ec4f77` | NovaTech（诺瓦科技）差旅管理制度 &gt; 适用范围与出行目的 本制度适用于客户拜访、项目交付、供应商沟通等普通商务出差。员工应根据实际业务目的登记行程，不因出行地点相同就将不同活动合并申报。 已获批准的外部培训，其课程费、交通、住宿和其他费用适用 &#91;费用报销制度&#93;(expense_policy.md) 的外部培训条款，不适用本制度的普通差旅住宿限额和餐费补助。兼有培训与客户拜访的行程，应在申请… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           2 | `330edce0-9b09-47ef-b371-9fa470b74dd0` | NovaTech（诺瓦科技）差旅管理制度 &gt; 差旅申请与审批 境内普通出差原则上提前三个工作日提交申请，注明业务目标、客户或项目、城市、起止日期及费用预算，经直属负责人和预算负责人批准后再预订。申请人应确认现场接待安排，避免仅因交通优惠而提前购买不可退改的行程。 紧急客户故障等无法提前办理的情况，可先通过公司沟通渠道取得负责人书面确认，并在下一个工作日补交申请。预计费用超出预算时，应说明增加原因并… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           3 | `9c9bf530-eb9c-4aeb-8e0f-a634fc217662` | NovaTech（诺瓦科技）差旅管理制度 &gt; 城际交通 境内出行优先选择能够合理到达的高铁二等座或飞机经济舱。选择航班时综合考虑出发时间、接驳成本和退改条件，不要求员工为节省少量票价搭乘影响正常休息的行程。无普通席位而确需升级时，应在购买前说明可选方案，由预算负责人批准。 个人行程与公务行程衔接时，私人部分费用由员工承担。使用私家车开展公务应事先说明路线和用途，经批准后按可核验的业务里程和实际必要… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           4 | `e9289ccd-a3ca-4c8e-9f29-910dbd49018c` | NovaTech（诺瓦科技）差旅管理制度 &gt; 普通商务出差住宿 境内普通商务出差，一线城市按每间每晚人民币 500 元为住宿报销上限，其他境内城市按每间每晚人民币 350 元为上限。本制度中的一线城市指北京、上海、广州和深圳。费用按实际发生额报销，上限不是固定发放的住宿补贴；自行免费住宿不领取住宿费。 住宿限额包含房费及必须支付的服务费用，不包含私人消费。员工应选择安全、交通合理的住宿地点。连续住… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           5 | `d62a0153-11c5-434e-b15d-7b12ddb5d208` | NovaTech（诺瓦科技）差旅管理制度 &gt; 住宿超限与特别批准 展会期间房源紧张、客户指定现场住宿或安全条件限制导致无法在标准内预订时，应保留可选酒店报价，说明超限原因、晚数和预计总额，在预订前取得预算负责人及财务负责人的特别批准。普通差旅申请获批不等于超限申请获批。 途中发生突发取消、恶劣天气或安全事件，确需立即安排住宿的，应先保障人身安全，尽快报告负责人，并在两个工作日内补交情况和费用证明。… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           6 | `de7f21a2-36a6-4ecf-ad67-5e201cae01b4` | NovaTech（诺瓦科技）差旅管理制度 &gt; 餐费补助与市内交通 境内普通商务出差餐费补助为每人每天人民币 80 元，按批准的实际出差自然日计算。客户或会议主办方提供工作餐时，每餐扣减 30 元，当日补助最低为零；不得同时申报已由他方承担的同一餐费用。业务招待另按费用报销制度办理，不计作个人餐费。 市内交通优先采用公共交通。携带设备、赶赴早晚班次或目的地公共交通不便时，可以选择合规出租车或网约车，… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           7 | `5a501652-d3dd-46bf-bba0-9a3ded2c093b` | NovaTech（诺瓦科技）差旅管理制度 &gt; 取消、改签与行程延长 业务安排变化后，应及时取消不再需要的交通和住宿，减少退改损失。因客户变更或不可抗力发生的合理退改费用，提供变更原因及订单记录后可申请报销；个人原因导致的费用由个人承担。退款必须在结算时冲减，不得按原价报销已退回的款项。 延长出差天数或新增城市，应重新确认业务目的和预算。周末留宿如为衔接公务且比往返更合理，可事先申请；私人休闲产生的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           8 | `1be0cf45-bf45-40f7-8975-0a3deb987696` | NovaTech（诺瓦科技）差旅管理制度 &gt; 境外出差与返回交接 境外出差应提前十个工作日提交申请，由部门负责人、财务负责人和总经理批准。预算须单独列明目的地、币种、交通、住宿、保险和必要证件费用；住宿及餐费按获批的境外专项预算执行，不套用境内城市标准。 出发前应了解目的地出行条件并与 IT 确认设备及数据访问安排。返回后及时向团队交接业务进展，按照费用报销制度的提交期限完成结算。报销材料中的客户… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |

### Human Coverage Decision

- [x] APPROVE — I reviewed the full 38-chunk frozen snapshot and confirm that no additional Grade 1–3 evidence is missing. Unlisted chunks may therefore be interpreted as implicit Grade 0 under CD-1.
- [ ] REJECT / NEEDS CHANGES — additional positive evidence exists or current judgments require revision.

Reviewer notes:

Human decision: APPROVE — no additional Grade 1–3 evidence found.

未添加或修改任何显式 relevance judgment。

Reviewer role: Human project owner

Review date: 2026-09-10

Human confirmation provenance: 本轮 Human project owner 对本 Query 的明确 APPROVE 及完整 38-chunk snapshot coverage 声明。

## PILOT-CQ-004

**Query：** 我没在登录，手机却弹出公司账号的验证请求。我该点同意吗，要怎么处理？

**Query category：** Paraphrase

**Existing Human-reviewed explicit judgments：** 原审阅日期 2026-09-09，Human project owner；Human Grade 3/2/1/0 数量分别为 1/2/0/2。以下 A/B 行是全部 5 项原判断，C 类 33 项原为 coverage pending，现经 Human coverage approval 具有 implicit Grade-0 semantics。本题 `coverage_reviewed = true` / APPROVED。

| file_name             | chunk_index | exact chunk_id                         | concise content preview                  | 当前分类 / 已有 Human grade                    |
| --------------------- | ----------: | -------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| employee_handbook.md  |           0 | `5ce01f7c-a91d-48e6-a10b-0086bc62f552` | NovaTech（诺瓦科技）员工手册 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | NovaTech（诺瓦科技）员工手册 &gt; 适用范围与服务渠道 本手册介绍员工日常工作安排和共同责任。人力资源部负责考勤、假期和福利咨询，部门负责人协调人员安排；具体费用由财务部按费用制度审核，账号和设备问题由 IT 服务台处理。员工应在入职时阅读手册，联系方式变更后及时更新人事资料。 | B — Explicit Grade 0；Human Grade 0       |
| employee_handbook.md  |           2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | NovaTech（诺瓦科技）员工手册 &gt; 工作时间与考勤 公司通常每周一至周五工作，每日工作八小时。员工可在上午九点至十点之间到岗，午休一小时，下班时间按实际到岗时间顺延。团队需要共同协作的时间为上午十点至十二点、下午两点至五点，客户现场服务另按事先确认的排班执行。 需要临时离岗、调整班次或因交通中断无法按时到岗时，应尽快告知直属负责人。考勤漏记可在三个工作日内提交说明，由负责人核实。延长工作时间… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           3 | `299c5bed-e316-4cd2-89cd-49670607f802` | NovaTech（诺瓦科技）员工手册 &gt; 试用期与岗位支持 试用期按员工签署的劳动合同约定执行。入职首周由负责人说明岗位目标并指定带教同事，人力资源部安排制度和安全培训。试用期间每月进行一次反馈，围绕工作成果、协作和所需支持沟通，不以单次失误代替整体评价。 转正评估前，员工与负责人共同整理阶段成果和后续发展计划。如岗位要求发生变化，应及时沟通目标，而不是在评估时临时增加此前未说明的考核项目。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           4 | `193a39de-16cc-456f-85b8-74e801991e28` | NovaTech（诺瓦科技）员工手册 &gt; 年假与病假 年度带薪假期额度由人力资源部依据适用规定、员工履历和公司福利安排核定，并在员工系统中公布。通常连续请假三天以内提前三个工作日申请，超过三天提前十个工作日申请。负责人应结合项目交接安排休假，不要求员工在休假期间持续在线。 突发疾病无法工作时，应在能够联系的情况下及时告知负责人，并在返岗后三个工作日内补办病假记录；连续病假超过两天时提供就诊或休养证… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           5 | `992fccef-928e-4c84-9233-3f45b900a0ad` | NovaTech（诺瓦科技）员工手册 &gt; 远程办公 完成试用期且岗位适合远程协作的员工，可以申请每周最多两天远程办公；负责人根据客户服务、现场工作和团队协作需要审批。常规申请在前一工作日下班前提交，临时照护或交通异常可以单独说明。远程办公不是休假，员工应保持约定协作时段可联系，并做好任务交接。 远程办公原则上使用公司设备。接入内部系统、文件共享和信息保护须遵守 &#91;信息安全制度&#93;(it_securi… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           6 | `ca1a91b1-f45e-4527-9857-277ec4304ed9` | NovaTech（诺瓦科技）员工手册 &gt; 培训与职业发展 公司为新员工安排入职培训，为在岗员工提供内部分享和岗位技能学习机会。部门负责人在季度沟通中讨论能力发展需求，内部培训通常在工作时间内进行，参与人员应提前协调手头任务。 参加收费的外部课程，应先提交课程内容、业务关联、时间和费用预算，由负责人及人力资源部确认。获批参加课程不等于所有附带开支都可报销；课程费、交通与住宿的具体要求见 &#91;费用报销制… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           7 | `9adc2e17-14ed-407a-8d70-aaa61e65ca6c` | NovaTech（诺瓦科技）员工手册 &gt; 员工福利 公司提供年度健康检查、工作日办公区茶水及员工关怀活动。健康检查由人力资源部统一预约；员工自行选择额外检查项目时，应先确认是否属于公司承担范围。部门团建需在部门预算内安排，不以个人垫付代替活动审批。 福利名额或活动日期发生调整时，人力资源部通过员工公告说明。员工应只提交办理福利必要的信息，体检报告等个人敏感材料不作为部门活动报名附件。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           8 | `424e7665-108d-45da-b26f-6687c39c0834` | NovaTech（诺瓦科技）员工手册 &gt; 出差与费用责任 员工外出前应说明业务目的、地点、时间及预计费用，按 &#91;差旅管理制度&#93;(travel_policy.md) 取得批准。出行中保留与业务相关的订单、票据和变更记录，返回后按 &#91;费用报销制度&#93;(expense_policy.md) 办理结算。负责人负责业务真实性，财务部负责票据与标准核验；批准出差不等于豁免费用限额。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           9 | `b7ad1041-2858-4162-b4cc-7b40961751c8` | NovaTech（诺瓦科技）员工手册 &gt; 信息保护与离职交接 员工对工作中接触的客户、产品和人员信息承担保密责任。离开工位应锁屏，发现可疑邮件、设备遗失或账号异常应及时联系 IT 服务台，不自行删除线索。具体处置与外部共享要求见 &#91;信息安全制度&#93;(it_security_policy.md)。 岗位调整或离职时，应将项目文件交回团队指定空间，归还公司设备和门禁介质，并与负责人、人力资源部和 IT … | A — Explicit Positive；Human Grade 2      |
| expense_policy.md     |           0 | `ea76f783-595b-4535-89ae-748258020c85` | NovaTech（诺瓦科技）费用报销制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           1 | `605740ab-0d52-4655-81db-b9bcb008f6ed` | NovaTech（诺瓦科技）费用报销制度 &gt; 费用原则与提交期限 可报销费用应与公司业务直接相关、实际发生，并具备必要批准和有效凭证。员工应优先使用公司采购或统一预订渠道，确需垫付时说明用途，不将未经批准的个人消费转作公司支出。 普通零星费用应在发生后十五个工作日内提交；普通差旅及外部培训行程的费用，应在行程结束后十个工作日内集中提交。跨月费用仍按对应期限办理。因商家补票等客观原因延迟，应在期限内… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           2 | `e3075f5f-eb85-4faf-9c1e-c560dfdcfb45` | NovaTech（诺瓦科技）费用报销制度 &gt; 发票与证明材料 境内采购和消费应取得抬头及识别信息正确的有效发票，电子发票直接提交原始电子文件。仅有付款截图不能替代发票；同时提供订单、支付记录或明细，以说明实际购买内容。发票信息错误时应联系开票方更正，不得自行修改文件内容。 确实无法取得境内发票的境外费用，可提交当地收据、支付凭证及业务说明，由财务按专项预算核验。外币金额需注明币种和交易日期，使用实… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           3 | `c59ef50b-ba8a-4ab0-8bc2-2bcb350c3bbf` | NovaTech（诺瓦科技）费用报销制度 &gt; 审批与结算 申请人填写费用类别、业务事项、项目或部门归属，并关联事前批准。直属负责人确认业务真实性，预算负责人核验额度，财务检查票据、标准和重复申报。材料不完整时退回补充，不将退回修改视为最终拒付。 财务审核通过后纳入下一次付款安排，每周三集中支付；遇非工作日顺延。员工垫付返还至本人登记账户。对审核意见有异议时，可补充业务材料请求复核，不通过拆分报销单… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           4 | `ff9dca7a-cc8b-41d6-a0ae-ed591b1d252f` | NovaTech（诺瓦科技）费用报销制度 &gt; 员工垫付与公司卡 员工垫付前应确认项目预算；大额采购宜由采购部门统一下单，不要求员工长期承担公司资金周转。需预借差旅款的，提交获批预算并在行程结算时核销，多余款项退回公司。 使用公司卡同样需要业务批准、发票及消费明细。公司卡已支付的金额不再向员工个人返款，但必须提交费用归属并完成对账。一次消费不得既申报员工垫付又登记公司卡报销。退款、折扣和商家返还金额… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           5 | `8d63e548-66a8-41c7-83f3-778a0b66c9d5` | NovaTech（诺瓦科技）费用报销制度 &gt; 普通差旅费用 普通商务出差的交通、住宿和餐费补助按 &#91;差旅管理制度&#93;(travel_policy.md) 审核。报销时附差旅申请、实际行程及住宿明细；交通、住宿等实报实销项目在限额内按实际金额结算。餐费补助按差旅制度规定的日标准及扣减规则计算，无需逐餐提交个人餐饮发票。未经批准的私人延住、观光和同行亲友费用不属于公务支出。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           6 | `baf22e41-98da-4746-9765-55e7e437a3a0` | NovaTech（诺瓦科技）费用报销制度 &gt; 业务招待 客户或合作方招待应在发生前说明业务目的、参加人数及预算，由直属负责人和预算负责人批准。餐饮招待通常每人每次不超过人民币 200 元；预计超过该标准时，须另获财务负责人特别批准。 报销时提供实际人数、业务事项及消费明细，避免记录不必要的客户个人信息。同一餐由公司承担招待费用后，参加该餐的出差员工应按差旅制度扣减个人餐费补助。与业务无关的聚餐、私… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           7 | `7b2fbf99-8274-4610-ac08-3c3e7259ad09` | NovaTech（诺瓦科技）费用报销制度 &gt; 获批外部培训费用 收费的外部培训须先由直属负责人和人力资源部确认课程及参加资格，再由预算负责人批准费用。课程费按获批课程报价和实际支付额核销，交通费用按培训预算及有效票据报销；培训报名获批不代表允许更换高价课程或无预算增加陪同人员。 外部培训住宿按每间每晚人民币 350 元上限、凭票据实报实销，不发放定额住宿补贴。该标准适用于获批外部培训所需住宿，不区… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           8 | `0a7b4a44-4ac1-49da-a973-6ee14d4792a8` | NovaTech（诺瓦科技）费用报销制度 &gt; 超限、变更与不予报销事项 超出已批准标准或预算的费用，应补充原因和特别批准记录。普通差旅住宿例外依差旅制度处理，外部培训例外依本制度培训条款处理；其他费用在发生前由预算负责人及财务负责人批准。拆分发票、分次提交或改写费用类别不能使超限费用自动合规。 培训取消或行程变更取得退款时，应及时告知财务；业务原因产生的必要退改损失提供证明后审核，个人原因产生的损… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           0 | `03cecd2d-125a-4454-80b3-19bb40296df2` | NovaTech（诺瓦科技）信息安全制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号、密码与 MFA 员工使用本人公司账号开展工作，不得共享账号、代收验证码或借用同事权限。密码至少十四位，应避免姓名、生日和连续数字，不得与个人网站密码重复。公司提供密码管理工具保存工作凭据；不得把密码写入共享文档、聊天记录或源代码。 公司邮箱、VPN 及远程访问系统必须启用多因素认证（MFA）。员工应只确认由本人发起的登录请求；收到意外推送时拒绝批… | A — Explicit Positive；Human Grade 3      |
| it_security_policy.md |           2 | `8bc6437d-8da4-43c0-8ad6-9d04b1bee39f` | NovaTech（诺瓦科技）信息安全制度 &gt; 网络接入与 VPN 通过公共或不可信网络访问公司内部系统，必须先连接公司 VPN，并使用 MFA 完成认证。酒店、机场和咖啡馆网络属于此类环境；家庭网络未纳入公司受管网络，也按不可信网络处理。连接 VPN 不意味着可以忽略设备更新、屏幕遮挡和文件权限。 在受管办公网络中，员工按已有授权访问内部系统；不能因为处于办公室就借用他人账号。VPN 不可用时应联… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           3 | `dbc829fc-563c-440d-af99-f9b1ccaffa5b` | NovaTech（诺瓦科技）信息安全制度 &gt; 公司设备与软件 工作原则上使用公司配置的电脑和移动设备，保持磁盘加密、终端防护及自动锁屏开启。离开工位立即锁屏，系统空闲五分钟后自动锁定。员工不得自行关闭安全软件、使用未经批准的管理员权限或安装来源不明的插件。 IT 推送的关键安全更新应在两个工作日内完成。确因现场业务无法按期更新时，提前联系 IT 确认临时保护措施和补装时间。设备故障、遗失或被盗应尽… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           4 | `6f911609-ca55-4da1-a326-60c2dd8d9dfa` | NovaTech（诺瓦科技）信息安全制度 &gt; 数据分类与处理 公司信息按公开、内部、保密三个等级管理。已正式发布的产品介绍可作为公开资料；未公开的内部流程和会议安排属于内部信息；客户合同、产品源代码、账号凭据及员工个人资料属于保密信息。对分类不确定时先向资料负责人确认，不自行降低等级以方便发送。 资料负责人决定访问范围，团队按最小必要权限开展协作。财务票据可能包含账户、行程和客户信息，人事假期材料… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           5 | `3554a997-36e8-4376-b16c-6b353976e167` | NovaTech（诺瓦科技）信息安全制度 &gt; 文件共享与外部协作 内部协作使用公司批准的文档空间，按人员或工作组授权。对外共享内部资料，应先取得资料负责人批准，使用实名访问的受控链接并设置到期时间；保密资料对外提供还需安全负责人确认目的和保护措施。不得使用“任何人持链接可访问”的方式发送内部或保密文件。 项目结束或协作人员退出后，资料负责人应及时撤销访问权限。禁止通过个人邮箱、个人网盘或未获批准的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           6 | `02a3ade4-c272-4212-b5de-f512437f75a7` | NovaTech（诺瓦科技）信息安全制度 &gt; 可移动存储与打印 默认不使用个人 U 盘或移动硬盘搬运工作文件。现场交付确需离线介质时，应向 IT 申请公司登记的加密介质，记录资料用途，交付完成后归还或按要求清除。未知来源的存储设备不得接入公司电脑。 打印保密材料应选择受控打印设备，及时取走并核对份数；废弃副本投入保密销毁箱。出差期间不得把合同、设备或工作介质留在无人看管的公共区域。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           7 | `f7017394-093c-4e03-98b4-2513089a96b2` | NovaTech（诺瓦科技）信息安全制度 &gt; 钓鱼邮件与可疑链接 遇到要求紧急付款、修改收款账户或输入密码的邮件，应通过已知联系方式另行核实，不直接使用可疑邮件提供的电话号码。未知附件、二维码和登录页面在核实前不要打开或输入信息。客户或领导的显示姓名不能单独证明邮件可信。 发现可疑邮件可通过公司邮件举报入口或 IT 服务台报告，保留原邮件，不在团队群中继续转发危险链接。已经点击或下载时也应如实说明… | B — Explicit Grade 0；Human Grade 0       |
| it_security_policy.md |           8 | `d111e21f-b2a6-461a-9cec-b7189635546f` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号异常与安全事件 发现非本人登录、意外 MFA 请求或疑似凭据泄露时，应立即通过可信渠道联系 IT 服务台。若怀疑当前设备感染恶意软件，先停止敏感操作并断开网络，使用另一台可信设备或电话报告。不要在疑似受控设备上反复输入新密码。 IT 根据情况暂停账号会话、协助更换凭据并保存日志；员工提供发生时间和已进行的操作，不自行删除邮件、重装系统或清空记录。涉… | A — Explicit Positive；Human Grade 2      |
| it_security_policy.md |           9 | `6332122f-aa36-4c49-ac9a-f36d252171df` | NovaTech（诺瓦科技）信息安全制度 &gt; 远程办公、出差与离职 远程办公申请按 &#91;员工手册&#93;(employee_handbook.md) 办理，批准办公地点不等于批准使用个人设备或个人存储。出差连接酒店网络访问内部系统仍须使用公司 VPN；在公共场所应避免旁人看到屏幕或听到客户敏感信息。 离职或岗位变动前，将工作成果移交至团队指定空间，由负责人核对权限和资料归属。公司设备、加密介质及认证设备交… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           0 | `72a1bf30-caec-42ee-ab67-31108e9d1e86` | NovaTech（诺瓦科技）差旅管理制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           1 | `14f54027-316e-4f40-b50d-022696ec4f77` | NovaTech（诺瓦科技）差旅管理制度 &gt; 适用范围与出行目的 本制度适用于客户拜访、项目交付、供应商沟通等普通商务出差。员工应根据实际业务目的登记行程，不因出行地点相同就将不同活动合并申报。 已获批准的外部培训，其课程费、交通、住宿和其他费用适用 &#91;费用报销制度&#93;(expense_policy.md) 的外部培训条款，不适用本制度的普通差旅住宿限额和餐费补助。兼有培训与客户拜访的行程，应在申请… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           2 | `330edce0-9b09-47ef-b371-9fa470b74dd0` | NovaTech（诺瓦科技）差旅管理制度 &gt; 差旅申请与审批 境内普通出差原则上提前三个工作日提交申请，注明业务目标、客户或项目、城市、起止日期及费用预算，经直属负责人和预算负责人批准后再预订。申请人应确认现场接待安排，避免仅因交通优惠而提前购买不可退改的行程。 紧急客户故障等无法提前办理的情况，可先通过公司沟通渠道取得负责人书面确认，并在下一个工作日补交申请。预计费用超出预算时，应说明增加原因并… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           3 | `9c9bf530-eb9c-4aeb-8e0f-a634fc217662` | NovaTech（诺瓦科技）差旅管理制度 &gt; 城际交通 境内出行优先选择能够合理到达的高铁二等座或飞机经济舱。选择航班时综合考虑出发时间、接驳成本和退改条件，不要求员工为节省少量票价搭乘影响正常休息的行程。无普通席位而确需升级时，应在购买前说明可选方案，由预算负责人批准。 个人行程与公务行程衔接时，私人部分费用由员工承担。使用私家车开展公务应事先说明路线和用途，经批准后按可核验的业务里程和实际必要… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           4 | `e9289ccd-a3ca-4c8e-9f29-910dbd49018c` | NovaTech（诺瓦科技）差旅管理制度 &gt; 普通商务出差住宿 境内普通商务出差，一线城市按每间每晚人民币 500 元为住宿报销上限，其他境内城市按每间每晚人民币 350 元为上限。本制度中的一线城市指北京、上海、广州和深圳。费用按实际发生额报销，上限不是固定发放的住宿补贴；自行免费住宿不领取住宿费。 住宿限额包含房费及必须支付的服务费用，不包含私人消费。员工应选择安全、交通合理的住宿地点。连续住… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           5 | `d62a0153-11c5-434e-b15d-7b12ddb5d208` | NovaTech（诺瓦科技）差旅管理制度 &gt; 住宿超限与特别批准 展会期间房源紧张、客户指定现场住宿或安全条件限制导致无法在标准内预订时，应保留可选酒店报价，说明超限原因、晚数和预计总额，在预订前取得预算负责人及财务负责人的特别批准。普通差旅申请获批不等于超限申请获批。 途中发生突发取消、恶劣天气或安全事件，确需立即安排住宿的，应先保障人身安全，尽快报告负责人，并在两个工作日内补交情况和费用证明。… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           6 | `de7f21a2-36a6-4ecf-ad67-5e201cae01b4` | NovaTech（诺瓦科技）差旅管理制度 &gt; 餐费补助与市内交通 境内普通商务出差餐费补助为每人每天人民币 80 元，按批准的实际出差自然日计算。客户或会议主办方提供工作餐时，每餐扣减 30 元，当日补助最低为零；不得同时申报已由他方承担的同一餐费用。业务招待另按费用报销制度办理，不计作个人餐费。 市内交通优先采用公共交通。携带设备、赶赴早晚班次或目的地公共交通不便时，可以选择合规出租车或网约车，… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           7 | `5a501652-d3dd-46bf-bba0-9a3ded2c093b` | NovaTech（诺瓦科技）差旅管理制度 &gt; 取消、改签与行程延长 业务安排变化后，应及时取消不再需要的交通和住宿，减少退改损失。因客户变更或不可抗力发生的合理退改费用，提供变更原因及订单记录后可申请报销；个人原因导致的费用由个人承担。退款必须在结算时冲减，不得按原价报销已退回的款项。 延长出差天数或新增城市，应重新确认业务目的和预算。周末留宿如为衔接公务且比往返更合理，可事先申请；私人休闲产生的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           8 | `1be0cf45-bf45-40f7-8975-0a3deb987696` | NovaTech（诺瓦科技）差旅管理制度 &gt; 境外出差与返回交接 境外出差应提前十个工作日提交申请，由部门负责人、财务负责人和总经理批准。预算须单独列明目的地、币种、交通、住宿、保险和必要证件费用；住宿及餐费按获批的境外专项预算执行，不套用境内城市标准。 出发前应了解目的地出行条件并与 IT 确认设备及数据访问安排。返回后及时向团队交接业务进展，按照费用报销制度的提交期限完成结算。报销材料中的客户… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |

### Human Coverage Decision

- [x] APPROVE — I reviewed the full 38-chunk frozen snapshot and confirm that no additional Grade 1–3 evidence is missing. Unlisted chunks may therefore be interpreted as implicit Grade 0 under CD-1.
- [ ] REJECT / NEEDS CHANGES — additional positive evidence exists or current judgments require revision.

Reviewer notes:

Human decision: APPROVE — no additional Grade 1–3 evidence found.

未添加或修改任何显式 relevance judgment。

Reviewer role: Human project owner

Review date: 2026-09-10

Human confirmation provenance: 本轮 Human project owner 对本 Query 的明确 APPROVE 及完整 38-chunk snapshot coverage 声明。

## PILOT-CQ-005

**Query：** 我获批去上海参加收费的外部培训，没有住宿超限的特别批准。订酒店时，每间每晚能报销的上限是多少？能按上海普通出差的 500 元标准订吗？

**Query category：** Distractor

**Existing Human-reviewed explicit judgments：** 原审阅日期 2026-09-09，Human project owner；Human Grade 3/2/1/0 数量分别为 1/4/0/6。以下 A/B 行是全部 11 项原判断，C 类 27 项原为 coverage pending，现经 Human coverage approval 具有 implicit Grade-0 semantics。本题 `coverage_reviewed = true` / APPROVED。

| file_name             | chunk_index | exact chunk_id                         | concise content preview                  | 当前分类 / 已有 Human grade                    |
| --------------------- | ----------: | -------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| employee_handbook.md  |           0 | `5ce01f7c-a91d-48e6-a10b-0086bc62f552` | NovaTech（诺瓦科技）员工手册 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | NovaTech（诺瓦科技）员工手册 &gt; 适用范围与服务渠道 本手册介绍员工日常工作安排和共同责任。人力资源部负责考勤、假期和福利咨询，部门负责人协调人员安排；具体费用由财务部按费用制度审核，账号和设备问题由 IT 服务台处理。员工应在入职时阅读手册，联系方式变更后及时更新人事资料。 | B — Explicit Grade 0；Human Grade 0       |
| employee_handbook.md  |           2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | NovaTech（诺瓦科技）员工手册 &gt; 工作时间与考勤 公司通常每周一至周五工作，每日工作八小时。员工可在上午九点至十点之间到岗，午休一小时，下班时间按实际到岗时间顺延。团队需要共同协作的时间为上午十点至十二点、下午两点至五点，客户现场服务另按事先确认的排班执行。 需要临时离岗、调整班次或因交通中断无法按时到岗时，应尽快告知直属负责人。考勤漏记可在三个工作日内提交说明，由负责人核实。延长工作时间… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           3 | `299c5bed-e316-4cd2-89cd-49670607f802` | NovaTech（诺瓦科技）员工手册 &gt; 试用期与岗位支持 试用期按员工签署的劳动合同约定执行。入职首周由负责人说明岗位目标并指定带教同事，人力资源部安排制度和安全培训。试用期间每月进行一次反馈，围绕工作成果、协作和所需支持沟通，不以单次失误代替整体评价。 转正评估前，员工与负责人共同整理阶段成果和后续发展计划。如岗位要求发生变化，应及时沟通目标，而不是在评估时临时增加此前未说明的考核项目。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           4 | `193a39de-16cc-456f-85b8-74e801991e28` | NovaTech（诺瓦科技）员工手册 &gt; 年假与病假 年度带薪假期额度由人力资源部依据适用规定、员工履历和公司福利安排核定，并在员工系统中公布。通常连续请假三天以内提前三个工作日申请，超过三天提前十个工作日申请。负责人应结合项目交接安排休假，不要求员工在休假期间持续在线。 突发疾病无法工作时，应在能够联系的情况下及时告知负责人，并在返岗后三个工作日内补办病假记录；连续病假超过两天时提供就诊或休养证… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           5 | `992fccef-928e-4c84-9233-3f45b900a0ad` | NovaTech（诺瓦科技）员工手册 &gt; 远程办公 完成试用期且岗位适合远程协作的员工，可以申请每周最多两天远程办公；负责人根据客户服务、现场工作和团队协作需要审批。常规申请在前一工作日下班前提交，临时照护或交通异常可以单独说明。远程办公不是休假，员工应保持约定协作时段可联系，并做好任务交接。 远程办公原则上使用公司设备。接入内部系统、文件共享和信息保护须遵守 &#91;信息安全制度&#93;(it_securi… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           6 | `ca1a91b1-f45e-4527-9857-277ec4304ed9` | NovaTech（诺瓦科技）员工手册 &gt; 培训与职业发展 公司为新员工安排入职培训，为在岗员工提供内部分享和岗位技能学习机会。部门负责人在季度沟通中讨论能力发展需求，内部培训通常在工作时间内进行，参与人员应提前协调手头任务。 参加收费的外部课程，应先提交课程内容、业务关联、时间和费用预算，由负责人及人力资源部确认。获批参加课程不等于所有附带开支都可报销；课程费、交通与住宿的具体要求见 &#91;费用报销制… | A — Explicit Positive；Human Grade 2      |
| employee_handbook.md  |           7 | `9adc2e17-14ed-407a-8d70-aaa61e65ca6c` | NovaTech（诺瓦科技）员工手册 &gt; 员工福利 公司提供年度健康检查、工作日办公区茶水及员工关怀活动。健康检查由人力资源部统一预约；员工自行选择额外检查项目时，应先确认是否属于公司承担范围。部门团建需在部门预算内安排，不以个人垫付代替活动审批。 福利名额或活动日期发生调整时，人力资源部通过员工公告说明。员工应只提交办理福利必要的信息，体检报告等个人敏感材料不作为部门活动报名附件。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           8 | `424e7665-108d-45da-b26f-6687c39c0834` | NovaTech（诺瓦科技）员工手册 &gt; 出差与费用责任 员工外出前应说明业务目的、地点、时间及预计费用，按 &#91;差旅管理制度&#93;(travel_policy.md) 取得批准。出行中保留与业务相关的订单、票据和变更记录，返回后按 &#91;费用报销制度&#93;(expense_policy.md) 办理结算。负责人负责业务真实性，财务部负责票据与标准核验；批准出差不等于豁免费用限额。 | B — Explicit Grade 0；Human Grade 0       |
| employee_handbook.md  |           9 | `b7ad1041-2858-4162-b4cc-7b40961751c8` | NovaTech（诺瓦科技）员工手册 &gt; 信息保护与离职交接 员工对工作中接触的客户、产品和人员信息承担保密责任。离开工位应锁屏，发现可疑邮件、设备遗失或账号异常应及时联系 IT 服务台，不自行删除线索。具体处置与外部共享要求见 &#91;信息安全制度&#93;(it_security_policy.md)。 岗位调整或离职时，应将项目文件交回团队指定空间，归还公司设备和门禁介质，并与负责人、人力资源部和 IT … | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           0 | `ea76f783-595b-4535-89ae-748258020c85` | NovaTech（诺瓦科技）费用报销制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           1 | `605740ab-0d52-4655-81db-b9bcb008f6ed` | NovaTech（诺瓦科技）费用报销制度 &gt; 费用原则与提交期限 可报销费用应与公司业务直接相关、实际发生，并具备必要批准和有效凭证。员工应优先使用公司采购或统一预订渠道，确需垫付时说明用途，不将未经批准的个人消费转作公司支出。 普通零星费用应在发生后十五个工作日内提交；普通差旅及外部培训行程的费用，应在行程结束后十个工作日内集中提交。跨月费用仍按对应期限办理。因商家补票等客观原因延迟，应在期限内… | B — Explicit Grade 0；Human Grade 0       |
| expense_policy.md     |           2 | `e3075f5f-eb85-4faf-9c1e-c560dfdcfb45` | NovaTech（诺瓦科技）费用报销制度 &gt; 发票与证明材料 境内采购和消费应取得抬头及识别信息正确的有效发票，电子发票直接提交原始电子文件。仅有付款截图不能替代发票；同时提供订单、支付记录或明细，以说明实际购买内容。发票信息错误时应联系开票方更正，不得自行修改文件内容。 确实无法取得境内发票的境外费用，可提交当地收据、支付凭证及业务说明，由财务按专项预算核验。外币金额需注明币种和交易日期，使用实… | B — Explicit Grade 0；Human Grade 0       |
| expense_policy.md     |           3 | `c59ef50b-ba8a-4ab0-8bc2-2bcb350c3bbf` | NovaTech（诺瓦科技）费用报销制度 &gt; 审批与结算 申请人填写费用类别、业务事项、项目或部门归属，并关联事前批准。直属负责人确认业务真实性，预算负责人核验额度，财务检查票据、标准和重复申报。材料不完整时退回补充，不将退回修改视为最终拒付。 财务审核通过后纳入下一次付款安排，每周三集中支付；遇非工作日顺延。员工垫付返还至本人登记账户。对审核意见有异议时，可补充业务材料请求复核，不通过拆分报销单… | B — Explicit Grade 0；Human Grade 0       |
| expense_policy.md     |           4 | `ff9dca7a-cc8b-41d6-a0ae-ed591b1d252f` | NovaTech（诺瓦科技）费用报销制度 &gt; 员工垫付与公司卡 员工垫付前应确认项目预算；大额采购宜由采购部门统一下单，不要求员工长期承担公司资金周转。需预借差旅款的，提交获批预算并在行程结算时核销，多余款项退回公司。 使用公司卡同样需要业务批准、发票及消费明细。公司卡已支付的金额不再向员工个人返款，但必须提交费用归属并完成对账。一次消费不得既申报员工垫付又登记公司卡报销。退款、折扣和商家返还金额… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           5 | `8d63e548-66a8-41c7-83f3-778a0b66c9d5` | NovaTech（诺瓦科技）费用报销制度 &gt; 普通差旅费用 普通商务出差的交通、住宿和餐费补助按 &#91;差旅管理制度&#93;(travel_policy.md) 审核。报销时附差旅申请、实际行程及住宿明细；交通、住宿等实报实销项目在限额内按实际金额结算。餐费补助按差旅制度规定的日标准及扣减规则计算，无需逐餐提交个人餐饮发票。未经批准的私人延住、观光和同行亲友费用不属于公务支出。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           6 | `baf22e41-98da-4746-9765-55e7e437a3a0` | NovaTech（诺瓦科技）费用报销制度 &gt; 业务招待 客户或合作方招待应在发生前说明业务目的、参加人数及预算，由直属负责人和预算负责人批准。餐饮招待通常每人每次不超过人民币 200 元；预计超过该标准时，须另获财务负责人特别批准。 报销时提供实际人数、业务事项及消费明细，避免记录不必要的客户个人信息。同一餐由公司承担招待费用后，参加该餐的出差员工应按差旅制度扣减个人餐费补助。与业务无关的聚餐、私… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           7 | `7b2fbf99-8274-4610-ac08-3c3e7259ad09` | NovaTech（诺瓦科技）费用报销制度 &gt; 获批外部培训费用 收费的外部培训须先由直属负责人和人力资源部确认课程及参加资格，再由预算负责人批准费用。课程费按获批课程报价和实际支付额核销，交通费用按培训预算及有效票据报销；培训报名获批不代表允许更换高价课程或无预算增加陪同人员。 外部培训住宿按每间每晚人民币 350 元上限、凭票据实报实销，不发放定额住宿补贴。该标准适用于获批外部培训所需住宿，不区… | A — Explicit Positive；Human Grade 3      |
| expense_policy.md     |           8 | `0a7b4a44-4ac1-49da-a973-6ee14d4792a8` | NovaTech（诺瓦科技）费用报销制度 &gt; 超限、变更与不予报销事项 超出已批准标准或预算的费用，应补充原因和特别批准记录。普通差旅住宿例外依差旅制度处理，外部培训例外依本制度培训条款处理；其他费用在发生前由预算负责人及财务负责人批准。拆分发票、分次提交或改写费用类别不能使超限费用自动合规。 培训取消或行程变更取得退款时，应及时告知财务；业务原因产生的必要退改损失提供证明后审核，个人原因产生的损… | A — Explicit Positive；Human Grade 2      |
| it_security_policy.md |           0 | `03cecd2d-125a-4454-80b3-19bb40296df2` | NovaTech（诺瓦科技）信息安全制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号、密码与 MFA 员工使用本人公司账号开展工作，不得共享账号、代收验证码或借用同事权限。密码至少十四位，应避免姓名、生日和连续数字，不得与个人网站密码重复。公司提供密码管理工具保存工作凭据；不得把密码写入共享文档、聊天记录或源代码。 公司邮箱、VPN 及远程访问系统必须启用多因素认证（MFA）。员工应只确认由本人发起的登录请求；收到意外推送时拒绝批… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           2 | `8bc6437d-8da4-43c0-8ad6-9d04b1bee39f` | NovaTech（诺瓦科技）信息安全制度 &gt; 网络接入与 VPN 通过公共或不可信网络访问公司内部系统，必须先连接公司 VPN，并使用 MFA 完成认证。酒店、机场和咖啡馆网络属于此类环境；家庭网络未纳入公司受管网络，也按不可信网络处理。连接 VPN 不意味着可以忽略设备更新、屏幕遮挡和文件权限。 在受管办公网络中，员工按已有授权访问内部系统；不能因为处于办公室就借用他人账号。VPN 不可用时应联… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           3 | `dbc829fc-563c-440d-af99-f9b1ccaffa5b` | NovaTech（诺瓦科技）信息安全制度 &gt; 公司设备与软件 工作原则上使用公司配置的电脑和移动设备，保持磁盘加密、终端防护及自动锁屏开启。离开工位立即锁屏，系统空闲五分钟后自动锁定。员工不得自行关闭安全软件、使用未经批准的管理员权限或安装来源不明的插件。 IT 推送的关键安全更新应在两个工作日内完成。确因现场业务无法按期更新时，提前联系 IT 确认临时保护措施和补装时间。设备故障、遗失或被盗应尽… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           4 | `6f911609-ca55-4da1-a326-60c2dd8d9dfa` | NovaTech（诺瓦科技）信息安全制度 &gt; 数据分类与处理 公司信息按公开、内部、保密三个等级管理。已正式发布的产品介绍可作为公开资料；未公开的内部流程和会议安排属于内部信息；客户合同、产品源代码、账号凭据及员工个人资料属于保密信息。对分类不确定时先向资料负责人确认，不自行降低等级以方便发送。 资料负责人决定访问范围，团队按最小必要权限开展协作。财务票据可能包含账户、行程和客户信息，人事假期材料… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           5 | `3554a997-36e8-4376-b16c-6b353976e167` | NovaTech（诺瓦科技）信息安全制度 &gt; 文件共享与外部协作 内部协作使用公司批准的文档空间，按人员或工作组授权。对外共享内部资料，应先取得资料负责人批准，使用实名访问的受控链接并设置到期时间；保密资料对外提供还需安全负责人确认目的和保护措施。不得使用“任何人持链接可访问”的方式发送内部或保密文件。 项目结束或协作人员退出后，资料负责人应及时撤销访问权限。禁止通过个人邮箱、个人网盘或未获批准的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           6 | `02a3ade4-c272-4212-b5de-f512437f75a7` | NovaTech（诺瓦科技）信息安全制度 &gt; 可移动存储与打印 默认不使用个人 U 盘或移动硬盘搬运工作文件。现场交付确需离线介质时，应向 IT 申请公司登记的加密介质，记录资料用途，交付完成后归还或按要求清除。未知来源的存储设备不得接入公司电脑。 打印保密材料应选择受控打印设备，及时取走并核对份数；废弃副本投入保密销毁箱。出差期间不得把合同、设备或工作介质留在无人看管的公共区域。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           7 | `f7017394-093c-4e03-98b4-2513089a96b2` | NovaTech（诺瓦科技）信息安全制度 &gt; 钓鱼邮件与可疑链接 遇到要求紧急付款、修改收款账户或输入密码的邮件，应通过已知联系方式另行核实，不直接使用可疑邮件提供的电话号码。未知附件、二维码和登录页面在核实前不要打开或输入信息。客户或领导的显示姓名不能单独证明邮件可信。 发现可疑邮件可通过公司邮件举报入口或 IT 服务台报告，保留原邮件，不在团队群中继续转发危险链接。已经点击或下载时也应如实说明… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           8 | `d111e21f-b2a6-461a-9cec-b7189635546f` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号异常与安全事件 发现非本人登录、意外 MFA 请求或疑似凭据泄露时，应立即通过可信渠道联系 IT 服务台。若怀疑当前设备感染恶意软件，先停止敏感操作并断开网络，使用另一台可信设备或电话报告。不要在疑似受控设备上反复输入新密码。 IT 根据情况暂停账号会话、协助更换凭据并保存日志；员工提供发生时间和已进行的操作，不自行删除邮件、重装系统或清空记录。涉… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           9 | `6332122f-aa36-4c49-ac9a-f36d252171df` | NovaTech（诺瓦科技）信息安全制度 &gt; 远程办公、出差与离职 远程办公申请按 &#91;员工手册&#93;(employee_handbook.md) 办理，批准办公地点不等于批准使用个人设备或个人存储。出差连接酒店网络访问内部系统仍须使用公司 VPN；在公共场所应避免旁人看到屏幕或听到客户敏感信息。 离职或岗位变动前，将工作成果移交至团队指定空间，由负责人核对权限和资料归属。公司设备、加密介质及认证设备交… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           0 | `72a1bf30-caec-42ee-ab67-31108e9d1e86` | NovaTech（诺瓦科技）差旅管理制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           1 | `14f54027-316e-4f40-b50d-022696ec4f77` | NovaTech（诺瓦科技）差旅管理制度 &gt; 适用范围与出行目的 本制度适用于客户拜访、项目交付、供应商沟通等普通商务出差。员工应根据实际业务目的登记行程，不因出行地点相同就将不同活动合并申报。 已获批准的外部培训，其课程费、交通、住宿和其他费用适用 &#91;费用报销制度&#93;(expense_policy.md) 的外部培训条款，不适用本制度的普通差旅住宿限额和餐费补助。兼有培训与客户拜访的行程，应在申请… | A — Explicit Positive；Human Grade 2      |
| travel_policy.md      |           2 | `330edce0-9b09-47ef-b371-9fa470b74dd0` | NovaTech（诺瓦科技）差旅管理制度 &gt; 差旅申请与审批 境内普通出差原则上提前三个工作日提交申请，注明业务目标、客户或项目、城市、起止日期及费用预算，经直属负责人和预算负责人批准后再预订。申请人应确认现场接待安排，避免仅因交通优惠而提前购买不可退改的行程。 紧急客户故障等无法提前办理的情况，可先通过公司沟通渠道取得负责人书面确认，并在下一个工作日补交申请。预计费用超出预算时，应说明增加原因并… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           3 | `9c9bf530-eb9c-4aeb-8e0f-a634fc217662` | NovaTech（诺瓦科技）差旅管理制度 &gt; 城际交通 境内出行优先选择能够合理到达的高铁二等座或飞机经济舱。选择航班时综合考虑出发时间、接驳成本和退改条件，不要求员工为节省少量票价搭乘影响正常休息的行程。无普通席位而确需升级时，应在购买前说明可选方案，由预算负责人批准。 个人行程与公务行程衔接时，私人部分费用由员工承担。使用私家车开展公务应事先说明路线和用途，经批准后按可核验的业务里程和实际必要… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           4 | `e9289ccd-a3ca-4c8e-9f29-910dbd49018c` | NovaTech（诺瓦科技）差旅管理制度 &gt; 普通商务出差住宿 境内普通商务出差，一线城市按每间每晚人民币 500 元为住宿报销上限，其他境内城市按每间每晚人民币 350 元为上限。本制度中的一线城市指北京、上海、广州和深圳。费用按实际发生额报销，上限不是固定发放的住宿补贴；自行免费住宿不领取住宿费。 住宿限额包含房费及必须支付的服务费用，不包含私人消费。员工应选择安全、交通合理的住宿地点。连续住… | A — Explicit Positive；Human Grade 2      |
| travel_policy.md      |           5 | `d62a0153-11c5-434e-b15d-7b12ddb5d208` | NovaTech（诺瓦科技）差旅管理制度 &gt; 住宿超限与特别批准 展会期间房源紧张、客户指定现场住宿或安全条件限制导致无法在标准内预订时，应保留可选酒店报价，说明超限原因、晚数和预计总额，在预订前取得预算负责人及财务负责人的特别批准。普通差旅申请获批不等于超限申请获批。 途中发生突发取消、恶劣天气或安全事件，确需立即安排住宿的，应先保障人身安全，尽快报告负责人，并在两个工作日内补交情况和费用证明。… | B — Explicit Grade 0；Human Grade 0       |
| travel_policy.md      |           6 | `de7f21a2-36a6-4ecf-ad67-5e201cae01b4` | NovaTech（诺瓦科技）差旅管理制度 &gt; 餐费补助与市内交通 境内普通商务出差餐费补助为每人每天人民币 80 元，按批准的实际出差自然日计算。客户或会议主办方提供工作餐时，每餐扣减 30 元，当日补助最低为零；不得同时申报已由他方承担的同一餐费用。业务招待另按费用报销制度办理，不计作个人餐费。 市内交通优先采用公共交通。携带设备、赶赴早晚班次或目的地公共交通不便时，可以选择合规出租车或网约车，… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           7 | `5a501652-d3dd-46bf-bba0-9a3ded2c093b` | NovaTech（诺瓦科技）差旅管理制度 &gt; 取消、改签与行程延长 业务安排变化后，应及时取消不再需要的交通和住宿，减少退改损失。因客户变更或不可抗力发生的合理退改费用，提供变更原因及订单记录后可申请报销；个人原因导致的费用由个人承担。退款必须在结算时冲减，不得按原价报销已退回的款项。 延长出差天数或新增城市，应重新确认业务目的和预算。周末留宿如为衔接公务且比往返更合理，可事先申请；私人休闲产生的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           8 | `1be0cf45-bf45-40f7-8975-0a3deb987696` | NovaTech（诺瓦科技）差旅管理制度 &gt; 境外出差与返回交接 境外出差应提前十个工作日提交申请，由部门负责人、财务负责人和总经理批准。预算须单独列明目的地、币种、交通、住宿、保险和必要证件费用；住宿及餐费按获批的境外专项预算执行，不套用境内城市标准。 出发前应了解目的地出行条件并与 IT 确认设备及数据访问安排。返回后及时向团队交接业务进展，按照费用报销制度的提交期限完成结算。报销材料中的客户… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |

### Human Coverage Decision

- [x] APPROVE — I reviewed the full 38-chunk frozen snapshot and confirm that no additional Grade 1–3 evidence is missing. Unlisted chunks may therefore be interpreted as implicit Grade 0 under CD-1.
- [ ] REJECT / NEEDS CHANGES — additional positive evidence exists or current judgments require revision.

Reviewer notes:

Human decision: APPROVE — no additional Grade 1–3 evidence found.

未添加或修改任何显式 relevance judgment。

Reviewer role: Human project owner

Review date: 2026-09-10

Human confirmation provenance: 本轮 Human project owner 对本 Query 的明确 APPROVE 及完整 38-chunk snapshot coverage 声明。

## PILOT-CQ-006

**Query：** 我想申请每周两天在家办公，需要满足什么条件、什么时候提交申请？获批后用家里网络访问公司内部系统，还需要做哪些接入认证？

**Query category：** Multi-chunk

**Existing Human-reviewed explicit judgments：** 原审阅日期 2026-09-09，Human project owner；Human Grade 3/2/1/0 数量分别为 2/1/2/1。以下 A/B 行是全部 6 项原判断，C 类 32 项原为 coverage pending，现经 Human coverage approval 具有 implicit Grade-0 semantics。本题 `coverage_reviewed = true` / APPROVED。

| file_name             | chunk_index | exact chunk_id                         | concise content preview                  | 当前分类 / 已有 Human grade                    |
| --------------------- | ----------: | -------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| employee_handbook.md  |           0 | `5ce01f7c-a91d-48e6-a10b-0086bc62f552` | NovaTech（诺瓦科技）员工手册 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           1 | `2392bb84-3ae9-452b-b044-1a538b99e939` | NovaTech（诺瓦科技）员工手册 &gt; 适用范围与服务渠道 本手册介绍员工日常工作安排和共同责任。人力资源部负责考勤、假期和福利咨询，部门负责人协调人员安排；具体费用由财务部按费用制度审核，账号和设备问题由 IT 服务台处理。员工应在入职时阅读手册，联系方式变更后及时更新人事资料。 | B — Explicit Grade 0；Human Grade 0       |
| employee_handbook.md  |           2 | `392ae2da-31b8-4baa-b7dc-03020e492488` | NovaTech（诺瓦科技）员工手册 &gt; 工作时间与考勤 公司通常每周一至周五工作，每日工作八小时。员工可在上午九点至十点之间到岗，午休一小时，下班时间按实际到岗时间顺延。团队需要共同协作的时间为上午十点至十二点、下午两点至五点，客户现场服务另按事先确认的排班执行。 需要临时离岗、调整班次或因交通中断无法按时到岗时，应尽快告知直属负责人。考勤漏记可在三个工作日内提交说明，由负责人核实。延长工作时间… | A — Explicit Positive；Human Grade 1      |
| employee_handbook.md  |           3 | `299c5bed-e316-4cd2-89cd-49670607f802` | NovaTech（诺瓦科技）员工手册 &gt; 试用期与岗位支持 试用期按员工签署的劳动合同约定执行。入职首周由负责人说明岗位目标并指定带教同事，人力资源部安排制度和安全培训。试用期间每月进行一次反馈，围绕工作成果、协作和所需支持沟通，不以单次失误代替整体评价。 转正评估前，员工与负责人共同整理阶段成果和后续发展计划。如岗位要求发生变化，应及时沟通目标，而不是在评估时临时增加此前未说明的考核项目。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           4 | `193a39de-16cc-456f-85b8-74e801991e28` | NovaTech（诺瓦科技）员工手册 &gt; 年假与病假 年度带薪假期额度由人力资源部依据适用规定、员工履历和公司福利安排核定，并在员工系统中公布。通常连续请假三天以内提前三个工作日申请，超过三天提前十个工作日申请。负责人应结合项目交接安排休假，不要求员工在休假期间持续在线。 突发疾病无法工作时，应在能够联系的情况下及时告知负责人，并在返岗后三个工作日内补办病假记录；连续病假超过两天时提供就诊或休养证… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           5 | `992fccef-928e-4c84-9233-3f45b900a0ad` | NovaTech（诺瓦科技）员工手册 &gt; 远程办公 完成试用期且岗位适合远程协作的员工，可以申请每周最多两天远程办公；负责人根据客户服务、现场工作和团队协作需要审批。常规申请在前一工作日下班前提交，临时照护或交通异常可以单独说明。远程办公不是休假，员工应保持约定协作时段可联系，并做好任务交接。 远程办公原则上使用公司设备。接入内部系统、文件共享和信息保护须遵守 &#91;信息安全制度&#93;(it_securi… | A — Explicit Positive；Human Grade 3      |
| employee_handbook.md  |           6 | `ca1a91b1-f45e-4527-9857-277ec4304ed9` | NovaTech（诺瓦科技）员工手册 &gt; 培训与职业发展 公司为新员工安排入职培训，为在岗员工提供内部分享和岗位技能学习机会。部门负责人在季度沟通中讨论能力发展需求，内部培训通常在工作时间内进行，参与人员应提前协调手头任务。 参加收费的外部课程，应先提交课程内容、业务关联、时间和费用预算，由负责人及人力资源部确认。获批参加课程不等于所有附带开支都可报销；课程费、交通与住宿的具体要求见 &#91;费用报销制… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           7 | `9adc2e17-14ed-407a-8d70-aaa61e65ca6c` | NovaTech（诺瓦科技）员工手册 &gt; 员工福利 公司提供年度健康检查、工作日办公区茶水及员工关怀活动。健康检查由人力资源部统一预约；员工自行选择额外检查项目时，应先确认是否属于公司承担范围。部门团建需在部门预算内安排，不以个人垫付代替活动审批。 福利名额或活动日期发生调整时，人力资源部通过员工公告说明。员工应只提交办理福利必要的信息，体检报告等个人敏感材料不作为部门活动报名附件。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           8 | `424e7665-108d-45da-b26f-6687c39c0834` | NovaTech（诺瓦科技）员工手册 &gt; 出差与费用责任 员工外出前应说明业务目的、地点、时间及预计费用，按 &#91;差旅管理制度&#93;(travel_policy.md) 取得批准。出行中保留与业务相关的订单、票据和变更记录，返回后按 &#91;费用报销制度&#93;(expense_policy.md) 办理结算。负责人负责业务真实性，财务部负责票据与标准核验；批准出差不等于豁免费用限额。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| employee_handbook.md  |           9 | `b7ad1041-2858-4162-b4cc-7b40961751c8` | NovaTech（诺瓦科技）员工手册 &gt; 信息保护与离职交接 员工对工作中接触的客户、产品和人员信息承担保密责任。离开工位应锁屏，发现可疑邮件、设备遗失或账号异常应及时联系 IT 服务台，不自行删除线索。具体处置与外部共享要求见 &#91;信息安全制度&#93;(it_security_policy.md)。 岗位调整或离职时，应将项目文件交回团队指定空间，归还公司设备和门禁介质，并与负责人、人力资源部和 IT … | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           0 | `ea76f783-595b-4535-89ae-748258020c85` | NovaTech（诺瓦科技）费用报销制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           1 | `605740ab-0d52-4655-81db-b9bcb008f6ed` | NovaTech（诺瓦科技）费用报销制度 &gt; 费用原则与提交期限 可报销费用应与公司业务直接相关、实际发生，并具备必要批准和有效凭证。员工应优先使用公司采购或统一预订渠道，确需垫付时说明用途，不将未经批准的个人消费转作公司支出。 普通零星费用应在发生后十五个工作日内提交；普通差旅及外部培训行程的费用，应在行程结束后十个工作日内集中提交。跨月费用仍按对应期限办理。因商家补票等客观原因延迟，应在期限内… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           2 | `e3075f5f-eb85-4faf-9c1e-c560dfdcfb45` | NovaTech（诺瓦科技）费用报销制度 &gt; 发票与证明材料 境内采购和消费应取得抬头及识别信息正确的有效发票，电子发票直接提交原始电子文件。仅有付款截图不能替代发票；同时提供订单、支付记录或明细，以说明实际购买内容。发票信息错误时应联系开票方更正，不得自行修改文件内容。 确实无法取得境内发票的境外费用，可提交当地收据、支付凭证及业务说明，由财务按专项预算核验。外币金额需注明币种和交易日期，使用实… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           3 | `c59ef50b-ba8a-4ab0-8bc2-2bcb350c3bbf` | NovaTech（诺瓦科技）费用报销制度 &gt; 审批与结算 申请人填写费用类别、业务事项、项目或部门归属，并关联事前批准。直属负责人确认业务真实性，预算负责人核验额度，财务检查票据、标准和重复申报。材料不完整时退回补充，不将退回修改视为最终拒付。 财务审核通过后纳入下一次付款安排，每周三集中支付；遇非工作日顺延。员工垫付返还至本人登记账户。对审核意见有异议时，可补充业务材料请求复核，不通过拆分报销单… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           4 | `ff9dca7a-cc8b-41d6-a0ae-ed591b1d252f` | NovaTech（诺瓦科技）费用报销制度 &gt; 员工垫付与公司卡 员工垫付前应确认项目预算；大额采购宜由采购部门统一下单，不要求员工长期承担公司资金周转。需预借差旅款的，提交获批预算并在行程结算时核销，多余款项退回公司。 使用公司卡同样需要业务批准、发票及消费明细。公司卡已支付的金额不再向员工个人返款，但必须提交费用归属并完成对账。一次消费不得既申报员工垫付又登记公司卡报销。退款、折扣和商家返还金额… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           5 | `8d63e548-66a8-41c7-83f3-778a0b66c9d5` | NovaTech（诺瓦科技）费用报销制度 &gt; 普通差旅费用 普通商务出差的交通、住宿和餐费补助按 &#91;差旅管理制度&#93;(travel_policy.md) 审核。报销时附差旅申请、实际行程及住宿明细；交通、住宿等实报实销项目在限额内按实际金额结算。餐费补助按差旅制度规定的日标准及扣减规则计算，无需逐餐提交个人餐饮发票。未经批准的私人延住、观光和同行亲友费用不属于公务支出。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           6 | `baf22e41-98da-4746-9765-55e7e437a3a0` | NovaTech（诺瓦科技）费用报销制度 &gt; 业务招待 客户或合作方招待应在发生前说明业务目的、参加人数及预算，由直属负责人和预算负责人批准。餐饮招待通常每人每次不超过人民币 200 元；预计超过该标准时，须另获财务负责人特别批准。 报销时提供实际人数、业务事项及消费明细，避免记录不必要的客户个人信息。同一餐由公司承担招待费用后，参加该餐的出差员工应按差旅制度扣减个人餐费补助。与业务无关的聚餐、私… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           7 | `7b2fbf99-8274-4610-ac08-3c3e7259ad09` | NovaTech（诺瓦科技）费用报销制度 &gt; 获批外部培训费用 收费的外部培训须先由直属负责人和人力资源部确认课程及参加资格，再由预算负责人批准费用。课程费按获批课程报价和实际支付额核销，交通费用按培训预算及有效票据报销；培训报名获批不代表允许更换高价课程或无预算增加陪同人员。 外部培训住宿按每间每晚人民币 350 元上限、凭票据实报实销，不发放定额住宿补贴。该标准适用于获批外部培训所需住宿，不区… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| expense_policy.md     |           8 | `0a7b4a44-4ac1-49da-a973-6ee14d4792a8` | NovaTech（诺瓦科技）费用报销制度 &gt; 超限、变更与不予报销事项 超出已批准标准或预算的费用，应补充原因和特别批准记录。普通差旅住宿例外依差旅制度处理，外部培训例外依本制度培训条款处理；其他费用在发生前由预算负责人及财务负责人批准。拆分发票、分次提交或改写费用类别不能使超限费用自动合规。 培训取消或行程变更取得退款时，应及时告知财务；业务原因产生的必要退改损失提供证明后审核，个人原因产生的损… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           0 | `03cecd2d-125a-4454-80b3-19bb40296df2` | NovaTech（诺瓦科技）信息安全制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           1 | `176b8225-18b7-479d-b02b-aa3d0be7f724` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号、密码与 MFA 员工使用本人公司账号开展工作，不得共享账号、代收验证码或借用同事权限。密码至少十四位，应避免姓名、生日和连续数字，不得与个人网站密码重复。公司提供密码管理工具保存工作凭据；不得把密码写入共享文档、聊天记录或源代码。 公司邮箱、VPN 及远程访问系统必须启用多因素认证（MFA）。员工应只确认由本人发起的登录请求；收到意外推送时拒绝批… | A — Explicit Positive；Human Grade 2      |
| it_security_policy.md |           2 | `8bc6437d-8da4-43c0-8ad6-9d04b1bee39f` | NovaTech（诺瓦科技）信息安全制度 &gt; 网络接入与 VPN 通过公共或不可信网络访问公司内部系统，必须先连接公司 VPN，并使用 MFA 完成认证。酒店、机场和咖啡馆网络属于此类环境；家庭网络未纳入公司受管网络，也按不可信网络处理。连接 VPN 不意味着可以忽略设备更新、屏幕遮挡和文件权限。 在受管办公网络中，员工按已有授权访问内部系统；不能因为处于办公室就借用他人账号。VPN 不可用时应联… | A — Explicit Positive；Human Grade 3      |
| it_security_policy.md |           3 | `dbc829fc-563c-440d-af99-f9b1ccaffa5b` | NovaTech（诺瓦科技）信息安全制度 &gt; 公司设备与软件 工作原则上使用公司配置的电脑和移动设备，保持磁盘加密、终端防护及自动锁屏开启。离开工位立即锁屏，系统空闲五分钟后自动锁定。员工不得自行关闭安全软件、使用未经批准的管理员权限或安装来源不明的插件。 IT 推送的关键安全更新应在两个工作日内完成。确因现场业务无法按期更新时，提前联系 IT 确认临时保护措施和补装时间。设备故障、遗失或被盗应尽… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           4 | `6f911609-ca55-4da1-a326-60c2dd8d9dfa` | NovaTech（诺瓦科技）信息安全制度 &gt; 数据分类与处理 公司信息按公开、内部、保密三个等级管理。已正式发布的产品介绍可作为公开资料；未公开的内部流程和会议安排属于内部信息；客户合同、产品源代码、账号凭据及员工个人资料属于保密信息。对分类不确定时先向资料负责人确认，不自行降低等级以方便发送。 资料负责人决定访问范围，团队按最小必要权限开展协作。财务票据可能包含账户、行程和客户信息，人事假期材料… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           5 | `3554a997-36e8-4376-b16c-6b353976e167` | NovaTech（诺瓦科技）信息安全制度 &gt; 文件共享与外部协作 内部协作使用公司批准的文档空间，按人员或工作组授权。对外共享内部资料，应先取得资料负责人批准，使用实名访问的受控链接并设置到期时间；保密资料对外提供还需安全负责人确认目的和保护措施。不得使用“任何人持链接可访问”的方式发送内部或保密文件。 项目结束或协作人员退出后，资料负责人应及时撤销访问权限。禁止通过个人邮箱、个人网盘或未获批准的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           6 | `02a3ade4-c272-4212-b5de-f512437f75a7` | NovaTech（诺瓦科技）信息安全制度 &gt; 可移动存储与打印 默认不使用个人 U 盘或移动硬盘搬运工作文件。现场交付确需离线介质时，应向 IT 申请公司登记的加密介质，记录资料用途，交付完成后归还或按要求清除。未知来源的存储设备不得接入公司电脑。 打印保密材料应选择受控打印设备，及时取走并核对份数；废弃副本投入保密销毁箱。出差期间不得把合同、设备或工作介质留在无人看管的公共区域。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           7 | `f7017394-093c-4e03-98b4-2513089a96b2` | NovaTech（诺瓦科技）信息安全制度 &gt; 钓鱼邮件与可疑链接 遇到要求紧急付款、修改收款账户或输入密码的邮件，应通过已知联系方式另行核实，不直接使用可疑邮件提供的电话号码。未知附件、二维码和登录页面在核实前不要打开或输入信息。客户或领导的显示姓名不能单独证明邮件可信。 发现可疑邮件可通过公司邮件举报入口或 IT 服务台报告，保留原邮件，不在团队群中继续转发危险链接。已经点击或下载时也应如实说明… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           8 | `d111e21f-b2a6-461a-9cec-b7189635546f` | NovaTech（诺瓦科技）信息安全制度 &gt; 账号异常与安全事件 发现非本人登录、意外 MFA 请求或疑似凭据泄露时，应立即通过可信渠道联系 IT 服务台。若怀疑当前设备感染恶意软件，先停止敏感操作并断开网络，使用另一台可信设备或电话报告。不要在疑似受控设备上反复输入新密码。 IT 根据情况暂停账号会话、协助更换凭据并保存日志；员工提供发生时间和已进行的操作，不自行删除邮件、重装系统或清空记录。涉… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| it_security_policy.md |           9 | `6332122f-aa36-4c49-ac9a-f36d252171df` | NovaTech（诺瓦科技）信息安全制度 &gt; 远程办公、出差与离职 远程办公申请按 &#91;员工手册&#93;(employee_handbook.md) 办理，批准办公地点不等于批准使用个人设备或个人存储。出差连接酒店网络访问内部系统仍须使用公司 VPN；在公共场所应避免旁人看到屏幕或听到客户敏感信息。 离职或岗位变动前，将工作成果移交至团队指定空间，由负责人核对权限和资料归属。公司设备、加密介质及认证设备交… | A — Explicit Positive；Human Grade 1      |
| travel_policy.md      |           0 | `72a1bf30-caec-42ee-ab67-31108e9d1e86` | NovaTech（诺瓦科技）差旅管理制度 &gt; 本文是 DX-RAG 项目原创、可公开分发的合成评估材料。NovaTech（诺瓦科技）为虚构组织，以下内容不代表真实公司的政策。 | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           1 | `14f54027-316e-4f40-b50d-022696ec4f77` | NovaTech（诺瓦科技）差旅管理制度 &gt; 适用范围与出行目的 本制度适用于客户拜访、项目交付、供应商沟通等普通商务出差。员工应根据实际业务目的登记行程，不因出行地点相同就将不同活动合并申报。 已获批准的外部培训，其课程费、交通、住宿和其他费用适用 &#91;费用报销制度&#93;(expense_policy.md) 的外部培训条款，不适用本制度的普通差旅住宿限额和餐费补助。兼有培训与客户拜访的行程，应在申请… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           2 | `330edce0-9b09-47ef-b371-9fa470b74dd0` | NovaTech（诺瓦科技）差旅管理制度 &gt; 差旅申请与审批 境内普通出差原则上提前三个工作日提交申请，注明业务目标、客户或项目、城市、起止日期及费用预算，经直属负责人和预算负责人批准后再预订。申请人应确认现场接待安排，避免仅因交通优惠而提前购买不可退改的行程。 紧急客户故障等无法提前办理的情况，可先通过公司沟通渠道取得负责人书面确认，并在下一个工作日补交申请。预计费用超出预算时，应说明增加原因并… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           3 | `9c9bf530-eb9c-4aeb-8e0f-a634fc217662` | NovaTech（诺瓦科技）差旅管理制度 &gt; 城际交通 境内出行优先选择能够合理到达的高铁二等座或飞机经济舱。选择航班时综合考虑出发时间、接驳成本和退改条件，不要求员工为节省少量票价搭乘影响正常休息的行程。无普通席位而确需升级时，应在购买前说明可选方案，由预算负责人批准。 个人行程与公务行程衔接时，私人部分费用由员工承担。使用私家车开展公务应事先说明路线和用途，经批准后按可核验的业务里程和实际必要… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           4 | `e9289ccd-a3ca-4c8e-9f29-910dbd49018c` | NovaTech（诺瓦科技）差旅管理制度 &gt; 普通商务出差住宿 境内普通商务出差，一线城市按每间每晚人民币 500 元为住宿报销上限，其他境内城市按每间每晚人民币 350 元为上限。本制度中的一线城市指北京、上海、广州和深圳。费用按实际发生额报销，上限不是固定发放的住宿补贴；自行免费住宿不领取住宿费。 住宿限额包含房费及必须支付的服务费用，不包含私人消费。员工应选择安全、交通合理的住宿地点。连续住… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           5 | `d62a0153-11c5-434e-b15d-7b12ddb5d208` | NovaTech（诺瓦科技）差旅管理制度 &gt; 住宿超限与特别批准 展会期间房源紧张、客户指定现场住宿或安全条件限制导致无法在标准内预订时，应保留可选酒店报价，说明超限原因、晚数和预计总额，在预订前取得预算负责人及财务负责人的特别批准。普通差旅申请获批不等于超限申请获批。 途中发生突发取消、恶劣天气或安全事件，确需立即安排住宿的，应先保障人身安全，尽快报告负责人，并在两个工作日内补交情况和费用证明。… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           6 | `de7f21a2-36a6-4ecf-ad67-5e201cae01b4` | NovaTech（诺瓦科技）差旅管理制度 &gt; 餐费补助与市内交通 境内普通商务出差餐费补助为每人每天人民币 80 元，按批准的实际出差自然日计算。客户或会议主办方提供工作餐时，每餐扣减 30 元，当日补助最低为零；不得同时申报已由他方承担的同一餐费用。业务招待另按费用报销制度办理，不计作个人餐费。 市内交通优先采用公共交通。携带设备、赶赴早晚班次或目的地公共交通不便时，可以选择合规出租车或网约车，… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           7 | `5a501652-d3dd-46bf-bba0-9a3ded2c093b` | NovaTech（诺瓦科技）差旅管理制度 &gt; 取消、改签与行程延长 业务安排变化后，应及时取消不再需要的交通和住宿，减少退改损失。因客户变更或不可抗力发生的合理退改费用，提供变更原因及订单记录后可申请报销；个人原因导致的费用由个人承担。退款必须在结算时冲减，不得按原价报销已退回的款项。 延长出差天数或新增城市，应重新确认业务目的和预算。周末留宿如为衔接公务且比往返更合理，可事先申请；私人休闲产生的… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |
| travel_policy.md      |           8 | `1be0cf45-bf45-40f7-8975-0a3deb987696` | NovaTech（诺瓦科技）差旅管理制度 &gt; 境外出差与返回交接 境外出差应提前十个工作日提交申请，由部门负责人、财务负责人和总经理批准。预算须单独列明目的地、币种、交通、住宿、保险和必要证件费用；住宿及餐费按获批的境外专项预算执行，不套用境内城市标准。 出发前应了解目的地出行条件并与 IT 确认设备及数据访问安排。返回后及时向团队交接业务进展，按照费用报销制度的提交期限完成结算。报销材料中的客户… | C — UNLISTED — HUMAN COVERAGE REVIEW REQUIRED |

### Human Coverage Decision

- [x] APPROVE — I reviewed the full 38-chunk frozen snapshot and confirm that no additional Grade 1–3 evidence is missing. Unlisted chunks may therefore be interpreted as implicit Grade 0 under CD-1.
- [ ] REJECT / NEEDS CHANGES — additional positive evidence exists or current judgments require revision.

Reviewer notes:

Human decision: APPROVE — no additional Grade 1–3 evidence found.

未添加或修改任何显式 relevance judgment。

Reviewer role: Human project owner

Review date: 2026-09-10

Human confirmation provenance: 本轮 Human project owner 对本 Query 的明确 APPROVE 及完整 38-chunk snapshot coverage 声明。

## Overall Pilot Coverage Gate

当前状态：**6/6 APPROVED**；`coverage_reviewed = true`。Review date：2026-09-10；Reviewer role：Human project owner。六个 APPROVE 勾选用于记录本轮已明确作出的 Human 决定，REJECT 保持未勾选。

| Query        | A：已有 Grade 1–3 | B：已有 Grade 0 | C：UNLISTED / implicit Grade 0 |
| ------------ | -------------: | -----------: | ----------------------------: |
| PILOT-CQ-001 |              2 |            1 |                            35 |
| PILOT-CQ-002 |              1 |            1 |                            36 |
| PILOT-CQ-003 |              1 |            2 |                            35 |
| PILOT-CQ-004 |              3 |            2 |                            33 |
| PILOT-CQ-005 |              5 |            6 |                            27 |
| PILOT-CQ-006 |              5 |            1 |                            32 |

Human 已明确确认 6/6 Query 的完整快照审阅及无遗漏 Grade 1–3 evidence；当前批准集的 CD-1 coverage 条件满足。30 项显式 Human judgments 保持 Grade 3/2/1/0 = 7/7/3/13；剩余 198 个 query–chunk pairs 通过此 coverage confirmation 具有 implicit Grade-0 semantics，未物化为 198 条显式标注。CQ-005 的五块 binary relevant set 不变。

本 Gate 仅适用于上方确切范围；它不批准未来 Query、corpus 或索引版本，不完成最终 Benchmark promotion。Human 已批准覆盖；后续独立 T2001 Final Gate 于 2026-09-10 PASS，详见 [Contract 第 16 节](../retrieval-evaluation-dataset-contract.md)。

T2001 = DONE（独立 Human Final Gate PASS，2026-09-10）；Contract 0.3 FROZEN；T2002/T2003 = TODO，未获执行授权。Task 完成来自独立 Final Gate，不是从 coverage review 自动推断。
