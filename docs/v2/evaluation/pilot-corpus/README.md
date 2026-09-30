# NovaTech Pilot Corpus

## 来源与用途

本目录是 DX-RAG 项目原创的中文合成语料，由 AI 辅助撰写，依据项目负责人本次明确授权创建，供 T2001 验证 [Retrieval Evaluation Dataset Contract](../retrieval-evaluation-dataset-contract.md)。虚构组织为 **NovaTech（诺瓦科技）**；所有制度、金额、流程及组织角色均为虚构，不代表任何真实公司的政策，也不作为现实用工、财务或安全合规依据。

这些内容专为本项目创作，未引用真实公司的内部资料或员工信息，可随项目公开分发。来源责任归属 DX-RAG 项目；后续人工审阅结论应单独记录，本次不宣称已通过最终验收。

语料版本：`novatech-pilot-0.1`。创建日期：2026-09-09。当前为未提交的源文件版本；语料创建时尚未形成入库索引快照，后续入库记录见文末。最终语料规模不由这四份 Pilot 文件固定。

## 源文档清单

仅以下四个文件是拟入库的政策源文档。**本 README 是 provenance 说明，不作为入库语料。**

| 文件 | 内容 |
|---|---|
| [employee_handbook.md](employee_handbook.md) | 工作时间、假期、远程办公、培训福利及一般职责 |
| [travel_policy.md](travel_policy.md) | 差旅审批、交通、住宿、补助及行程变更 |
| [expense_policy.md](expense_policy.md) | 发票、付款、报销审批、招待及外部培训费用 |
| [it_security_policy.md](it_security_policy.md) | 账号、设备、网络接入、数据共享及安全事件处理 |

## 语料创建阶段的授权边界

本轮授权仅创建第一批 Pilot Corpus；这是此前 T2001 文档落盘授权之后的单独语料创建授权，不改变已批准的评估设计。T2001 仍为 IN_PROGRESS，T2002/T2003 仍为 TODO。

这些是待验证的 Pilot 材料，不是正式 Benchmark 数据或质量证据。本次未调用真实 ingestion pipeline，未观察 chunks 或检索结果。后续必须先通过真实 DX-RAG 入库并检查实际 chunks，才可创建 Pilot 查询及 Ground Truth；本文不授权自动开展这些后续工作。

语料未按 V1 检索结果调优，也未为任何 Retrieval Candidate 定制。文档之间的培训、出差、票据、远程办公和安全责任重叠来自合理的政策分工。普通差旅住宿与获批外部培训住宿按不同业务目的适用不同标准；跨文档引用只指向细则，不制造相互冲突的金额规则。

## 后续真实入库记录

2026-09-09 按新的单独人工授权，以上四份源文档各通过现有 V1 ingestion path 入库一次，未修改源文档。实际 collection 为 `t2001-novatech-pilot-01`，共 38 个 chunks；详见 [Pilot Snapshot 01 与完整 Chunk Inventory](../pilot-snapshot-01/README.md)。这仅是 Pilot 入库证据，Ground Truth 尚未创建，未执行 Retrieval 或 Benchmark。下一步人工标注须绑定该快照；重建 collection 将产生新快照并需要重新映射/审阅。T2001 仍为 IN_PROGRESS，T2002/T2003 仍为 TODO。
