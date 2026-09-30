# Phase 20 Gate Review — Evaluation Foundation

> 审查日期：2026-09-18。本文保存同日独立 Gate Review 的正式报告；随后按用户明确授权落盘并同步项目状态。审查本身为 REVIEW-ONLY，落盘不是第二次 Gate，也没有重新执行真实 Benchmark。原报告中的本地绝对链接改为仓库相对链接，结论、计数和验证边界不变。

## 1. Executive Summary

- **审查范围：** T2001、T2002、T2003，包含完整工作区及未跟踪的 T2003 基线目录。
- **模式：** REVIEW-ONLY。
- **审查日期：** 2026-09-18。
- **权威依据：** [V2 SPEC](../v2/SPEC.md) > [V2 TASKS](../v2/TASKS.md) > [CLAUDE.md](../../CLAUDE.md)，遵循 [Gate 模板](../learning/templates/phase-gate-review-template.md)。
- **结论：** 11 项 AC 均获得当前证据支持，未发现阻断推进的 BLOCKER 或 MAJOR。
- **验证边界：** 本轮执行离线复算、内存测试、回归测试及文件身份核对；没有重新执行真实 Benchmark。历史 Chroma 读取曾伴随持久化文件变化，因此本轮没有初始化真实索引客户端。
- **文件修改：** 审查期间无。未修复问题、改变任务状态、安装依赖、提交或推送。随后文档落盘和状态同步由用户另行授权，不追记为审查期间修改。
- **下一阶段：** 未启动。

真实检索证据来自独立核查的原始采集文件，而非已有 DONE、PASS 或报告结论。审查进度消息所述“27 个未跟踪文件”计数有误；最终核实为 **25 个**。

## 2. Gate Verdict

**PHASE_20_PASS — READY_FOR_PHASE_21**

PASS 表示评估基础、Runner 和 V1 基线满足已批准的验收契约；不表示检索质量优秀、排名完全稳定或已经批准任何 Candidate。Phase 21 仍须有获批协议、具体 Task 和执行授权。

## 3. Task Audit

| Task | Declared Status | Dependencies | Scope / Deliverables | Verification | AC Ownership | Gate Result | Notes |
|---|---|---|---|---|---|---|---|
| T2001 | DONE | PASS：Phase 20 批准记录及 V1 基线身份明确 | Contract 0.3、Pilot、标注职责、指标及数据交付检查点齐备 | 独立检查契约、Pilot coverage 和后续批准链 | AC-2001-1～3 | PASS | 未把 Pilot 自动视为正式 Benchmark |
| T2002 | DONE | PASS：冻结契约和执行授权存在 | validator、metrics、Runner、CLI、V1 adapter、synthetic fixtures 和执行说明齐备 | 本轮评估测试 7/7；QA 50/50；Query 10/10；核查完整历史测试原始日志 | AC-2002-1～4 | PASS | 写文件的 CLI 测试本轮未重跑，边界见第 6 节 |
| T2003 | DONE | PASS：正式数据冻结、Runner、模型及索引证据齐备 | 三轮真实 Hybrid 基线、身份记录、逐题及聚合结果、波动与局限齐备 | 原始证据核验、1,152 个指标复算、120 条记录重放、当前文件哈希核对 | AC-2003-1～4 | PASS | 接受已披露波动；没有效果提升要求 |

## 4. Acceptance Criteria Audit

证据类型按模板使用。`REAL（历史采集）` 指原始真实运行证据，本轮只读核查不构成新的真实检索执行。

| AC | Owner Task | Requirement | Evidence | Evidence Type | Result | Boundary / Deferred Owner |
|---|---|---|---|---|---|---|
| AC-2001-1 | T2001 | 数据契约完整、一致并关联 V1 I/O | Contract §2–6、10–12；Pilot 快照与 coverage；V1 Hybrid 接口 | STATIC | PASS | 审批来源依据仓库保存的人工决定，不声称重新认证人工审阅过程 |
| AC-2001-2 | T2001 | 指标及边界定义完整 | Contract §6–9：K、映射、宏平均、同分、重复、缺失标注和无相关项处理 | STATIC | PASS | 定义与当前实现相符 |
| AC-2001-3 | T2001 | 负责人、授权、交付检查点及阻塞选择明确 | Contract §5、14、16；正式数据审批与规模决定 | STATIC | PASS | 32A+8U 低于目标的差额有明确批准 |
| AC-2002-1 | T2002 | 手算 fixtures 验证指标与边界 | 本轮手算、空结果、短列表、重复、弱相关、宏平均测试 | REAL、MOCKED | PASS | REAL 指实际指标代码；检索输入为 synthetic |
| AC-2002-2 | T2002 | 无效输入报错，输出身份与范围完整 | fail-fast 测试；CLI/adapter 审查；实际保存报告及历史 CLI 测试日志 | REAL、MOCKED、STATIC | PASS | validator 不认证 decision_ref 背后的人工行为 |
| AC-2002-3 | T2002 | 检查并披露重复性 | 本轮真实 Keyword/Hybrid 配合替代 store/vector 的三进程测试；波动诊断重放 | SUBSTITUTED | PASS | 不将替代依赖测试当作真实模型稳定性证明 |
| AC-2002-4 | T2002 | 回归保护与复现说明 | 本轮 QA 50/50、Query 10/10；V1 产品差异为空；调用说明 | MOCKED、STATIC | PASS | 非真实 LLM、存储或浏览器 E2E |
| AC-2003-1 | T2003 | 版本、数据、模型、索引、配置及命令准确 | 原始 report/execution、源码哈希、冻结数据、当前模型/索引文件核对 | REAL（历史采集）、STATIC | PASS | 工作区增量没有冒充测量 HEAD 已提交内容 |
| AC-2003-2 | T2003 | 真实逐题与聚合结果，失败和局限完整 | 三轮各 40 题原始返回；独立公式复算及报告重放 | REAL（历史采集）、REAL（离线复算）、SUBSTITUTED | PASS | 合成政策语料上的真实检索；无生成质量结论 |
| AC-2003-3 | T2003 | 按条件检查复现；说明 latency/cost | seeds 1/2/3、独立 PID、精确比较及完整诊断重算 | REAL（历史采集）、SUBSTITUTED、STATIC | PASS | 5 题排名变化、6 题分数映射变化、1 题指标变化；latency/cost 未测量 |
| AC-2003-4 | T2003 | 保留可复现基线、行为未变、局限明确 | 原始运行与前后身份记录；当前源码、29 个模型文件、45 个索引文件核对；回归 | REAL（历史采集）、STATIC、MOCKED | PASS | 本轮未新增 live 重跑；不保证异机迁移或逐位向量语义正确性 |

没有将 NOT_AVAILABLE 转换为 PASS，也没有将当前 Phase 必需 AC 延后给未来任务。

## 5. Implementation / Contract Audit

| 合同领域 | 独立检查结果 | 证据层级 / 结果 |
|---|---|---|
| 数据身份与有效性 | chunk ID、文件映射、快照绑定、等级、coverage、审批字段及 family/split 校验符合契约；无效数据在 search 前拒绝 | STATIC + REAL/MOCKED；PASS |
| 指标计算 | Recall/RR 使用 grade≥2；nDCG 使用完整 graded gain 和完整真值 IDCG；K=1/3/5/10 | STATIC + REAL；PASS |
| 排序及重复 | 消费原始顺序；重复 ID 保留首次并记录位置；不增加 tie-breaker、不补检索 | STATIC + REAL；PASS |
| 聚合 | Dev/Test、类别分别宏平均；Unanswerable 排除并保留返回；空有效分组为 null | REAL；PASS |
| V1 行为 | 0.3/0.7 权重、0.30 阈值及 Retrieve→Merge→Score→Sort→Filter→Top-K 保持 | STATIC + MOCKED；PASS |
| 深度边界 | 一次请求深度 10，分支候选 20、VectorStore 请求 40；明确不等同于独立生产 top_k=5 | STATIC；PASS |
| 数据划分 | 独立核对 40 题划分映射及核心事实不跨 split；20 families | REAL（离线检查）；PASS |
| 基线证据完整性 | manifest 覆盖其余 24 个文件；当前源码、数据、报告哈希一致；38 条采集 inventory 与冻结原始快照一致 | REAL（离线检查）；PASS |
| API / 产品保护 | 产品、前端、依赖声明及 V1 历史 SPEC/TASKS 相对 V1 tag 无差异；Query 契约回归通过 | STATIC + MOCKED；PASS |
| 新持久化、回滚、生产接口 | 当前 Phase 未引入此类产品行为 | NOT_APPLICABLE |

**Verification Accuracy：**

- **verified：** 当前指标计算、输入校验测试、保存结果数学一致性、回归断言、文件身份及划分结构。
- **partially verified：** 当前真实运行就绪由历史真实执行和当前文件一致性共同支持，本轮未重新加载模型或查询索引。
- **not verified：** 异机可移植复现、向量逐位语义审计、生成质量、latency/cost。
- **incorrectly claimed：** 未发现当前验收材料把上述未验证项宣称为已完成。

## 6. Runtime Verification

环境：Windows / PowerShell，Python **3.14.6**；ChromaDB **1.5.9**、Sentence Transformers **6.0.1**、Transformers **5.16.1**、Torch **2.14.0**。与保存的基线环境版本一致。

所有 Python 检查使用 `-B`，并设置 `PYTHONDONTWRITEBYTECODE=1`，避免生成字节码。以下均为独立 Gate 审查期间的执行记录；报告落盘与 Learning Review 不冒充再次执行。

| Command / Check | Scope | Exit Status | Result / Count | Evidence Boundary |
|---|---|---:|---|---|
| `python -B docs/v2/benchmarks/t2003-v1-baseline-1.0/verify.py` | 原始基线校验 | 0 | PASS；1,152 个逐题指标值及聚合核对 | REAL 离线执行；未检索 |
| `python -B docs/v2/evaluation/novatech-retrieval-benchmark-1.0.0/verify.py` | 冻结 release 与批准 RC 内容核对 | 0 | PASS；40 题、1,520 judgments、38 chunks | REAL 数据检查 |
| 下列选择性 unittest 命令 | 评估测试 | 0 | PASS；7/7 | 指标真实代码；MOCKED / SUBSTITUTED 检索边界 |
| `python -B -m unittest discover -s tests -p test_qa.py -v` | QA 回归，backend 目录 | 0 | PASS；50/50 | MOCKED 外部依赖 |
| `python -B -m unittest discover -s tests -p test_query.py -v` | Query API 回归，backend 目录 | 0 | PASS；10/10 | 真实路由 / MOCKED 服务与存储 |
| `python -B -m pip check` | 依赖一致性 | 0 | PASS；无破损依赖 | 不证明所有运行路径兼容 |
| `python -B -`，只读内存探针 | 保存观察重放 | 0 | PASS；120 条查询、30 个聚合分组、完整 repeatability 对象 | SUBSTITUTED：以保存返回替代实时检索 |
| `python -B -`，只读身份/结构探针 | 模型、索引、数据映射、原始排序 | 0 | PASS；29 模型文件、45 索引文件无差异；40 题划分、38 条 inventory、120 条排序检查通过 | 文件及保存数据核验 |
| `git diff v1.0.0 --stat -- backend/app frontend backend/requirements.txt docs/SPEC.md docs/TASKS.md` | 继承契约与产品差异 | 0 | 无差异 | STATIC |
| `git -c core.safecrlf=false diff --check`；`git diff --cached --check` | 工作区格式 | 0 | PASS | STATIC |

评估测试实际选择命令，在 backend 目录执行：

```powershell
python -B -c "import sys,unittest; sys.path.insert(0,'tests'); import test_evaluation as t; names=[n for n in unittest.defaultTestLoader.getTestCaseNames(t.EvaluationTests) if n!='test_cli_fresh_processes_and_persisted_provenance']; r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(t.EvaluationTests(n) for n in names)); sys.exit(not r.wasSuccessful())"
```

本轮共重新运行 **67 个 unittest 方法，全部通过**。

`test_cli_fresh_processes_and_persisted_provenance` 会创建临时目录并写报告，因此按不修改文件的要求未执行。已检查其代码及基线目录保存的原始测试日志：历史完整评估测试为 **8/8**，QA **50/50**，Query **10/10**，对应命令退出码均为 0。这些历史数量没有冒充本轮重跑数量。

内存探针未保存成仓库脚本；原始调用输入保留于本次会话工具记录。其检查包括：以每轮 raw_results 按 query_text 重放 measure 并对比完整 per_query/aggregates；重算 repeatability；用 hashlib 对模型/索引目录与 execution 的 after 清单比较；核对 split 核心事实和 inventory 的正文/文件映射。不得将探针当成新增实时检索。

## 7. Findings Classification

**BLOCKER：0；MAJOR：0；MINOR：0；INFO：4。**

| ID | Severity | Requirement / Task | Evidence | Impact | Owner | Disposition |
|---|---|---|---|---|---|---|
| F-1 | INFO | EVAL-03 / T2003 | 三轮中 5 题排名、6 题分数映射、1 题指标变化 | 后续比较必须考虑基线波动；精确确定性不成立 | 后续实验协议负责人 | 已完整披露；无需当前修复 |
| F-2 | INFO | AC-2003-4 | 历史采集期间 3 个 Chroma 文件字节改变；公开逻辑数据一致；当前 45 文件与采集后完全相同 | 不能从逻辑一致推导运行期间向量逐位不变或唯一根因 | 后续复现执行负责人 | 保留边界；无需当前修复 |
| F-3 | INFO | EVAL-01 / T2001、T2003 | 32A+8U、单人审阅、7 个共享正证据块、2 条跨侧补充事实、非盲测，均有批准记录 | 限制泛化与独立测试解释；不得反复利用 Test 调参 | 数据及实验负责人 | 已批准的当前数据范围；无需当前修复 |
| F-4 | INFO | 证据保存 / T2003 | 基线包 25 文件均未跟踪，manifest 完整 | 当前 Gate 可审查，但不能把 Git HEAD 单独作为完整交付副本 | 仓库维护者 | 保留工作区证据；提交须另行授权 |

F-1～F-3 是测量和适用范围限制，没有违反当前“忠实采集并披露”的契约。F-4 不违反允许审查未提交工作区的 Gate 规则。

## 8. Architecture / Scope / Repository Hygiene

- 当前 HEAD：`1692aa5877af120680d0fd386b3aa9f82b0069ea`。
- V1 tag：`da8be59a60d7f35a2e3c1ab835624946c53d2a55`。
- 审查工作区：**8 个 tracked 修改、25 个 untracked 文件，无 staged 修改**。审查开始和结束的状态清单一致；此处不是后续文档落盘后的计数。
- tracked 修改属于 T2003 授权、完成导航及学习材料；学习 reader-test 修订与本次 Gate 分开处理，没有据此继承验收结论。
- 已审查 git status、普通及 staged diff、未跟踪清单；不能将空产品 diff 表述为工作区干净。
- Evaluation 包独立于产品运行入口；未发现新增 RRF、BM25、Reranker、Query Rewrite、生成评估或下一 Phase 业务实现。
- 没有新增第三方依赖或替换冻结技术栈；模型、索引、缓存和临时目录有忽略规则。
- 对 tracked/untracked 文本执行凭据模式检查，未发现匹配的真实密钥候选；没有输出本地 .env 内容。此检查不构成全面安全认证。
- 未 reset、移动 tag、创建分支、提交、推送或删除证据。

## 9. Next-Phase Readiness

1. **下一阶段的 Phase 20 阻塞依赖是否满足？** 是。契约、验证后的 Runner、正式数据及真实 V1 基线均已具备。Phase 21 自身的协议和执行授权仍须单独批准。
2. **当前阶段是否可作为安全基础？** 是，限于已声明的数据、深度、模型、索引和波动条件；不得扩大为一般企业效果或生成质量结论。
3. **是否存在未解决 BLOCKER / MAJOR？** 无。
4. **延后项目是否范围清楚、责任明确？** 是。生成质量归未来 Phase 24 获批协议；latency/cost 明确未测量；异机复现和更强向量审计应由需要这些证据的后续协议明确负责。没有借此延后当前必需 AC。
5. **启动下一阶段是否会掩盖或放大当前缺陷？** 在保留原始基线、披露波动、控制变量并保护 Test 用途的条件下，不会。忽略这些边界开展比较则可能产生错误结论。

## 10. Final Gate Decision

- **正式结论：PHASE_20_PASS — READY_FOR_PHASE_21**。
- **阻断修复或产品决定：** 无。
- **证据限制：** 本轮未重跑真实 Benchmark、写文件 CLI 测试或真实模型/索引初始化；未测 latency/cost、生成质量及异机复现。
- **历史材料用途：** T2001 Human Gate、T2002 完成报告、T2003 README、preflight/smoke 报告及学习材料仅用于导航和解释；验收另行核对实现、测试、原始 JSON/日志、哈希及本轮执行结果。
- **文件修改：** 审查期间无；任务状态未改变。随后用户授权保存报告和同步当前 Gate 状态，属于独立文档维护。
- **下一阶段：** 未启动；本结论不代替 Phase 21 的独立批准与执行授权。

### Evidence navigation

- [冻结数据契约](../v2/evaluation/retrieval-evaluation-dataset-contract.md)、[正式数据集](../v2/evaluation/novatech-retrieval-benchmark-1.0.0/README.md)。
- [指标实现](../../backend/evaluation/metrics.py)、[Runner](../../backend/evaluation/runner.py)、[测试](../../backend/tests/test_evaluation.py)。
- [原始报告](../v2/benchmarks/t2003-v1-baseline-1.0/run-01/report.json)、[execution](../v2/benchmarks/t2003-v1-baseline-1.0/run-01/execution.json)、[离线验证脚本](../v2/benchmarks/t2003-v1-baseline-1.0/verify.py)。
