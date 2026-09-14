# T2003 前环境与索引就绪检查

**限定范围内预检通过；未运行 Benchmark，不等于端到端搜索或向量完整性已经验证。**

检查完成 UTC：2026-09-14T09:03:05.186855+00:00。授权见 SPEC §1.8。原始机器证据：[result.json](result.json)；检查代码：[check.py](check.py)。

| 检查 | 结果 |
|---|---|
| frozen_dataset | PASS |
| dependencies | PASS |
| configuration_and_paths | PASS |
| model_identity | PASS |
| offline_model_load | PASS |
| live_collection_inventory | PASS |
| implementation_identity | PASS |

## 具体结果

- 正式冻结数据集及全量 validator 通过，40 题/1,520 项等级/38 块与获批版本一致。
- Python：D:/Python/Python314/python.exe，3.14.6。7 项快照记录依赖与历史版本一致；pip check 无损坏依赖。
- 有效目录为 backend/models/bge-small-zh-v1.5 和 backend/chroma_db；配置与原快照一致，production Top-K=5，MIN_RELEVANCE_SCORE=0.30，chunk size=800/overlap=120。仅输出白名单非敏感字段，未输出 API 密钥或 .env 内容。
- 29 个历史模型文件 hash 全部一致。通过现有 get_model 离线加载成功，CPU，维度 512，max_seq_length=512；未调用 encode。HF/Transformers 离线及 telemetry 设置仅限检查进程。
- 通过 ChromaVectorStore.list_collections/list_chunks/get_chunk_count 读取实际 collection t2001-novatech-pilot-01：4 文件、38 块，chunk IDs、原文 hash、file_id/file_name/chunk_index 全匹配。
- 产品源码与 V1 tag 无 diff；当前 Runner 源码 hash 与正式数据集 manifest 一致。工作区有未提交工具/文档，不能仅凭 Git HEAD 重建本次运行环境。

## 索引完整性与运行边界

**本次未调用写入/删除/摄入 API，但不声称存储目录字节完全不变。** 公共客户端读取窗口内观察到 chroma.sqlite3 及一个 segment 下的 data_level0.bin、length.bin hash 变化；完整文件名见 result.json。客户端可能进行内部维护，也可能有并发写入；本次没有足够证据确定原因，不能把它归因为用户修改或宣称已重建索引。

逻辑 chunk 快照匹配已经验证；公开接口不返回原始向量，本次未访问私有 collection，也没有执行向量查询，故存储向量逐位一致性、实际搜索成功和排序复现性仍未验证。这里的 PASS 仅覆盖上述检查，不能称“所有索引完整性检查通过”。实际 baseline 前应保持无并发摄入/修改，并由每个 Runner worker 重新校验冻结 ID/文本映射。

T2003 仍 TODO、Benchmark 未获授权。当前 CLI 校验数据集审批状态，但不把 dataset 的 benchmark_authorized=false 字段作为强制执行门禁；该字段保留冻结时授权范围，执行权限依靠明确的后续 Human 授权，不得擅自修改冻结文件来取得权限。本轮没有运行 CLI、measure、检索、embedding encode 或指标计算。

无需配置生成 LLM API 来进行 Retrieval-only baseline；本次未调用 LLM 或检查生成服务凭据。请求深度10与生产Top-K5的候选深度差异、V1同分排序风险、小样本和非盲测限制继续有效。

## 执行记录与复核

首次检查使用了不存在的 count_chunks 方法，导致脚本本身失败，保存在 [result-attempt-01.json](result-attempt-01.json) 与 [check-attempt-01.py](check-attempt-01.py)。当时不是已确认的索引故障。修正为现有公开 get_chunk_count 后重新运行，所有检查通过；产品、冻结数据和 VectorStore 实现未改。

本报告是单次时点证据。check.py 拒绝覆盖既有结果；未来重查应使用新版本或新记录，不能覆盖本次证据。纯数据复核可使用正式版本的 verify.py，不会访问 Chroma 或加载模型。

下一步是由 Human 单独决定是否授权 T2003 baseline（需要接受上述未验证边界并在执行前维持环境不变）。当前不自动启动。
