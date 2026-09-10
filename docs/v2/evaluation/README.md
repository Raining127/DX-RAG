# V2 评估协议

本目录存放经过审阅的数据集契约与评估协议。[T2001 Retrieval Evaluation Dataset Contract](retrieval-evaluation-dataset-contract.md) 已记录本次人工确认的设计决定；T2001 已 DONE，Contract 0.3 FROZEN，Human Final Gate PASS（2026-09-10）。批准及授权边界见 [docs/v2/SPEC.md 第 1.1 节](../SPEC.md)。[docs/v2/TASKS.md](../TASKS.md) 中的 T2002/T2003 仍为 TODO，未获本次执行授权。当前目录有 Pilot 审阅证据，尚无完成 promotion 的正式 Benchmark Dataset 或已实现的评估器。

协议必须明确数据集 / 语料 / 查询版本、来源、相关性判断、审阅与数据泄漏边界、指标定义，以及可复现的执行要求。测试样例必须标为 test fixtures，不得将其作为有代表性的 Benchmark 数据。遵循 [docs/v2/SPEC.md](../SPEC.md) 第 3–4 节及第 6 节。

后续单独获授权的 [NovaTech Pilot Corpus](pilot-corpus/README.md) 包含四份项目原创合成源文档。2026-09-09 按进一步的单独授权完成真实 V1 入库，产生 38 个 chunks；身份、运行时配置和完整正文见 [Pilot Snapshot 01](pilot-snapshot-01/README.md)。这是冻结的 Pilot 入库证据；入库阶段未创建查询或 Ground Truth。

后续六题候选及本轮 Human Review 已记录于 [Pilot Annotation Packet — Reviewed 0.2](pilot-snapshot-01-annotation-packet-draft.md)。该文件保留原 Codex 建议、人工批准的 Pilot labels、修改理由及 rubric findings；路径保留 `draft` 以维持引用，当前版本为 Reviewed 0.2。它们未自动成为最终 Benchmark Dataset，未产生 Retrieval 或指标结果。CQ-005 的 binary mapping 已由 CD-2 确认，保留指标解释局限；该审阅阶段 T2001 为 IN_PROGRESS；当前状态见文末，T2002/T2003 仍为 TODO。


2026-09-10 已将 Human Closing Decisions CD-1～CD-4 整理至 [Dataset Contract 0.2 与 T2001 Closing Checklist](retrieval-evaluation-dataset-contract.md)，Pilot packet 追加 closing evidence，六题等级不变。Contract 未声明最终 FROZEN；该阶段 Pilot full-snapshot Human coverage confirmation 为 PENDING，当时 metric/execution 协议及独立 Human Gate 尚待确认；当前协议进展见下文。48-query Benchmark 只记录质量目标，未生成；本轮不授权 T2001 DONE 或 T2002/T2003 执行。


2026-09-10 本轮已将 Human 确认的 metric/execution protocol 写入 [Dataset Contract 0.3](retrieval-evaluation-dataset-contract.md)：AC-2001-2 为 SATISFIED BY CONTRACT，尚未实现或执行。新增 [Human Full-Snapshot Coverage Review Packet](pilot-snapshot-01/coverage-review-packet.md)，逐题展示 6 × 38 个冻结 chunks，并保留原 Human judgments；未列块均为 coverage pending，未自动标 0。准备 packet 时 Pilot coverage_reviewed 为 false / PENDING、AC-2001-1 尚待人工确认；该阶段 T2001 等待独立 Human Gate，当前状态见文末；T2002/T2003 不获执行授权。


2026-09-10 Human project owner 已明确完成 [Pilot Coverage Gate：6/6 APPROVED](pilot-snapshot-01/coverage-review-packet.md)。仅对 Reviewed 0.2 六题、novatech-pilot-0.1 与 t2001-novatech-pilot-01 的冻结 38 chunks 启用 coverage_reviewed=true；30 项显式判断不变，198 对未列项保持稀疏并取得 implicit Grade-0 semantics。[Contract 0.3 第 13、15 节](retrieval-evaluation-dataset-contract.md) 已更新 closing checklist 与 Final Gate readiness：AC-2001-1 SATISFIED，AC-2001-2/3 SATISFIED BY CONTRACT，当时无已知证据 blocker，等待独立 Human Final Gate；当时 Contract 未 FROZEN、T2001 IN_PROGRESS，当前状态见文末，T2002/T2003 TODO；本轮未执行 Retrieval/metrics/Benchmark。


**最终状态（2026-09-10）：** Human project owner 明确批准 [T2001 Final Human Gate PASS、T2001 DONE、Dataset Contract 0.3 FROZEN](retrieval-evaluation-dataset-contract.md)。AC-2001-1/2/3 均 SATISFIED；Pilot 6/6 Coverage APPROVED、30 显式和 198 隐式判断保持不变，全部 readiness READY、无剩余 T2001 blocker。冻结定义不得为适应实现/结果静默修改，真实缺陷须显式 Human-reviewed revision。此批准只适用于 T2001，T2002/T2003 TODO 且未获执行授权；正式 40+8 质量目标数据尚未构建，六题 Pilot 不自动成为正式 V1 Baseline Dataset。T2003 前必须存在真实版本化、Human-reviewed evaluation dataset。
