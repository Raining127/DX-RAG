# V2 评估协议

**当前正式数据集（2026-09-14）：** [novatech-retrieval-benchmark-1.0.0](novatech-retrieval-benchmark-1.0.0/README.md) 已 FROZEN / promotion APPROVED，40 题、38 块、1,520 项等级。后续按 SPEC §1.10 获授权完成 [T2003 完整基线](../benchmarks/t2003-v1-baseline-1.0/README.md)，T2003 DONE；冻结 release 保留发布时历史状态，不改其授权字段。

本目录存放经过审阅的数据集契约与评估协议。[T2001 Retrieval Evaluation Dataset Contract](retrieval-evaluation-dataset-contract.md) 已 DONE / 0.3 FROZEN。[T2002 Runner 0.1.0](t2002-runner.md) 已于 2026-09-11 完成实现与验证。T2003 三轮真实 Hybrid 检索证据已保存在 benchmarks；2026-09-18 [独立 Phase 20 Gate](../../verification/PHASE-20-GATE-REVIEW.md)已 PASS，Phase 21 未启动；后续协议、Task 与执行仍需独立授权。冻结 release、原始 Benchmark 和历史批准文件不回写。下文历史记录保留各次授权当时的状态。

**历史候选准备（2026-09-11）：** 按 [SPEC §1.4](../SPEC.md) 的新授权交付 [Benchmark 候选审阅包 0.1](archives/README.md#benchmark-candidate-0.1)，含 32 Answerable +8 Unanswerable、全快照建议矩阵、family/split 草案和待填人工决定。全部 Human 状态仍 PENDING；正式语料复用、标签、coverage、划分及 promotion 未批准。历史文字中的数据构建未授权指各次当时状态；本次候选准备未启动 T2003。历史第一批材料见 [第一批](archives/README.md#benchmark-candidate-0.1) 开始人工审题。

协议必须明确数据集 / 语料 / 查询版本、来源、相关性判断、审阅与数据泄漏边界、指标定义，以及可复现的执行要求。测试样例必须标为 test fixtures，不得将其作为有代表性的 Benchmark 数据。遵循 [docs/v2/SPEC.md](../SPEC.md) 第 3–4 节及第 6 节。

后续单独获授权的 [NovaTech Pilot Corpus](pilot-corpus/README.md) 包含四份项目原创合成源文档。2026-09-09 按进一步的单独授权完成真实 V1 入库，产生 38 个 chunks；身份、运行时配置和完整正文见 [Pilot Snapshot 01](pilot-snapshot-01/README.md)。这是冻结的 Pilot 入库证据；入库阶段未创建查询或 Ground Truth。

后续六题候选及本轮 Human Review 已记录于 [Pilot Annotation Packet — Reviewed 0.2](pilot-snapshot-01-annotation-packet-draft.md)。该文件保留原 Codex 建议、人工批准的 Pilot labels、修改理由及 rubric findings；路径保留 `draft` 以维持引用，当前版本为 Reviewed 0.2。它们未自动成为最终 Benchmark Dataset，未产生 Retrieval 或指标结果。CQ-005 的 binary mapping 已由 CD-2 确认，保留指标解释局限；该审阅阶段 T2001 为 IN_PROGRESS；当前状态见文末，T2002/T2003 仍为 TODO。


2026-09-10 已将 Human Closing Decisions CD-1～CD-4 整理至 [Dataset Contract 0.2 与 T2001 Closing Checklist](retrieval-evaluation-dataset-contract.md)，Pilot packet 追加 closing evidence，六题等级不变。Contract 未声明最终 FROZEN；该阶段 Pilot full-snapshot Human coverage confirmation 为 PENDING，当时 metric/execution 协议及独立 Human Gate 尚待确认；当前协议进展见下文。48-query Benchmark 只记录质量目标，未生成；本轮不授权 T2001 DONE 或 T2002/T2003 执行。


2026-09-10 本轮已将 Human 确认的 metric/execution protocol 写入 [Dataset Contract 0.3](retrieval-evaluation-dataset-contract.md)：AC-2001-2 为 SATISFIED BY CONTRACT，尚未实现或执行。新增 [Human Full-Snapshot Coverage Review Packet](pilot-snapshot-01/coverage-review-packet.md)，逐题展示 6 × 38 个冻结 chunks，并保留原 Human judgments；未列块均为 coverage pending，未自动标 0。准备 packet 时 Pilot coverage_reviewed 为 false / PENDING、AC-2001-1 尚待人工确认；该阶段 T2001 等待独立 Human Gate，当前状态见文末；T2002/T2003 不获执行授权。


2026-09-10 Human project owner 已明确完成 [Pilot Coverage Gate：6/6 APPROVED](pilot-snapshot-01/coverage-review-packet.md)。仅对 Reviewed 0.2 六题、novatech-pilot-0.1 与 t2001-novatech-pilot-01 的冻结 38 chunks 启用 coverage_reviewed=true；30 项显式判断不变，198 对未列项保持稀疏并取得 implicit Grade-0 semantics。[Contract 0.3 第 13、15 节](retrieval-evaluation-dataset-contract.md) 已更新 closing checklist 与 Final Gate readiness：AC-2001-1 SATISFIED，AC-2001-2/3 SATISFIED BY CONTRACT，当时无已知证据 blocker，等待独立 Human Final Gate；当时 Contract 未 FROZEN、T2001 IN_PROGRESS，当前状态见文末，T2002/T2003 TODO；本轮未执行 Retrieval/metrics/Benchmark。


**最终状态（2026-09-10）：** Human project owner 明确批准 [T2001 Final Human Gate PASS、T2001 DONE、Dataset Contract 0.3 FROZEN](retrieval-evaluation-dataset-contract.md)。AC-2001-1/2/3 均 SATISFIED；Pilot 6/6 Coverage APPROVED、30 显式和 198 隐式判断保持不变，全部 readiness READY、无剩余 T2001 blocker。冻结定义不得为适应实现/结果静默修改，真实缺陷须显式 Human-reviewed revision。此批准只适用于 T2001，T2002/T2003 TODO 且未获执行授权；正式 40+8 质量目标数据尚未构建，六题 Pilot 不自动成为正式 V1 Baseline Dataset。T2003 前必须存在真实版本化、Human-reviewed evaluation dataset。

**目录整理（2026-09-14）：** 五个已完成的审阅目录共 74 个文件已打包到 [历史归档](archives/README.md)，原目录移至 Git 忽略的本地备份。正式数据集及核验方式不变。
