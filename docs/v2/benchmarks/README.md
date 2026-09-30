# V2 Benchmark 证据

本目录存放真实运行的证据与分析。2026-09-14 已完成 [T2003 V1 Retrieval Baseline](t2003-v1-baseline-1.0/README.md)，包含完整原始结果、复现波动、验证与分析，AC-2003-1～4 PASS。后续于 2026-09-18 完成[独立 Phase 20 Gate](../../verification/PHASE-20-GATE-REVIEW.md)：PHASE_20_PASS — READY_FOR_PHASE_21；Phase 21 未启动。原基线包保留采集时状态与全部哈希，不回写其历史 Gate 描述。此前 Bootstrap 未运行 Benchmark 的记录为历史状态。

每次运行必须关联协议 / 数据集版本、Baseline / Candidate、实现与 Runner 版本、语料 / 索引 / 模型 / 配置、完整命令 / 环境、逐查询及聚合测量值、失败情况和局限。说明依赖是真实还是替代，以及 latency / cost 是否已测量。保留早期运行记录；更正时应说明取代了哪些内容。复现条件及波动情况应与结果一同记录。

`docs/verification/` 下的 V1 历史验收资料保持不变，不能替代本目录要求的质量 Benchmark。遵循 [docs/v2/SPEC.md](../SPEC.md) 中的 EVAL-03 和 EXP-01。
