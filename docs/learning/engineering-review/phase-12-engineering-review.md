# Phase 12 — Integration & Acceptance Engineering Review

> **日期：2026-09-07。Status：COMPLETE（工程分析与文档交付）。** 覆盖 T1201–T1204 的验证设计、产品边界、失败模式、规模取舍和证据生命周期。完成不表示以下 Known Gaps 已修复。
>
> **边界：**本轮独立阅读当前实现和冻结要求，复用既有 runtime evidence，并重跑确定性 failure contract。不重新执行全量验收、浏览器或 live provider；不修改产品、SPEC、TASKS，不 commit/push。不是 Phase Gate Re-review，也不替代公开发布审查或 Learning fresh-reader 检查。

> **当前状态补记（2026-09-08）：**下文分析保留原工程评审时点；ER12-01 对应的 F-6 已修复并通过独立增量 Gate Re-review，当前 **PHASE_12_PASS**。见 [F-6 remediation](../../verification/T1204/F6-REMEDIATION.md) 和 [Gate closure](../../verification/PHASE-12-GATE-CLOSURE.md)。其他已记录工程边界及独立学习 workflow pending 状态不变。

## 1. 工程结论

Phase 12 最有价值的交付是可追溯的证据体系：业务状态、API 返回、持久化副作用和模型行为分别得到验证，而不是将单个成功响应当作完整正确性证明。当前 SPEC v1.7 的 BGE 基线为 512 dimensions；T1201–T1204 的 DONE 和历史 Gate 状态分别记账。[任务记录](../../TASKS.md)、[最终验收](../../verification/T1204/README.md)

这套设计适用于 SPEC §11.2 的单机、单用户/少量并发目标，但没有建立跨文件系统与 Chroma 的事务、跨进程缓存一致性或服务端总请求 deadline。另一个当前仍可从源码确认的缺口是上传成功未失效前端文件列表与文件数。后端 E2E 通过不能关闭这个 UI 数据新鲜度问题。

本评审保留已有验收结论的原始范围，不重新发布 104 项 AC 全部通过的独立 Gate verdict。工程风险、产品 AC 失败和证据未覆盖是三种不同判断。

## 2. 输入、所有权与证据范围

```text
冻结 SPEC / TASKS
    ├── 固定 fixture + 可控故障 → 验证状态转移、错误码和调用次数
    ├── 真实模型与 provider → 验证实际兼容性及指定样例质量
    └── section-qualified AC matrix → 要求 / owner / 实现 / 结果

运行记录 → 原始哈希 → 路径脱敏公开副本 → 公开哈希 + provenance
```

| 范围 | 实现所有权 | 验证所证明的边界 |
|---|---|---|
| T1201 摄取 | upload 保存与异常 cleanup；Ingest 解析/三态；VectorStore 批次补偿 | 实际 OCR、本地模型、成功/部分失败/全失败、失败无残留与重传 |
| T1202 QA | Hybrid 排序过滤；QA context/history；DeepSeekClient retry；后端 sources | 真实模型指定样例 + 确定性控制流；不是无限输入质量保证 |
| T1203 文件管理 | 持久化 chunks 作为列表/preview 来源；原文件和向量级联删除 | API 生命周期与 KB 隔离；不自动覆盖浏览器缓存同步 |
| T1204 总审计 | section + AC ID 保留独立要求；DoD 单列 | 冻结 mandatory inventory；不是新 Gate 或性能基准 |

核心代码：[upload.py](../../../backend/app/api/upload.py)、[ingest.py](../../../backend/app/services/ingest.py)、[vector_store.py](../../../backend/app/core/vector_store.py)、[qa.py](../../../backend/app/services/qa.py)、[files.py](../../../backend/app/api/files.py)。前端所有权见 [page.tsx](../../../frontend/app/page.tsx)、[FileUpload](../../../frontend/components/FileUpload.tsx)、[FileManager](../../../frontend/components/FileManager.tsx)。

## 3. 关键设计决策与取舍

### ADR-01：用组合证据覆盖不可控 provider

**问题：**真实请求能验证 SDK/鉴权/模型兼容，但无法保证某次运行自然遇到每个 HTTP 故障。为了制造限流或服务故障而增加请求既不稳定，也不能提高控制流测试的精确性。

**当前决策：**LIVE 证明真实 QA/OCR；DETERMINISTIC 证明收到 429/5xx/403 后的 retry/auth contract。SPEC F013、§9.3 没有自然观察这些状态的附加要求。已观测的真实 401 和受控真实 transport timeout 保持原始分类。[T1202 blocker audit](../../verification/T1202/BLOCKER-AUDIT.md)

**代价：**测试替身可能偏离 SDK 异常形状，因此既读 adapter 的 exception/status 分支，也保留实际 SDK 调用证据。确定性通过不能改写为 live failure PASS；provider 升级后需要根据受影响接口重新验证。

### ADR-02：把回滚定义为多个状态面的恢复

**当前决策：**失败后检查原始文件、持久化 chunks、可检索结果和同名重传。VectorStore 内部为多批写入失败补偿，upload 负责自己保存的原始文件；正常成功后才失效关键词缓存。

**收益：**副作用的恢复靠近产生它的 owner，测试可用公共 API 观察结果。

**代价：**这是应用层补偿，不是跨系统原子事务。cleanup 自身遇到 I/O 错误、进程中断、并发读取等路径，不因常规 rollback 场景通过就得到保证。特别是文件删除顺序为 raw unlink → vector delete → keyword invalidate，中段异常可留下部分完成状态。

### ADR-03：PDF 以 bytes 打开，缩短磁盘句柄生命周期

**事实：**T1201 修复了 Windows malformed PDF 解析异常可能保留文件句柄、阻碍删除的问题。当前 `fitz.open(stream=file_path.read_bytes(), filetype="pdf")` 把磁盘文件读取的生命周期与 parser 对象分开。[回归测试](../../../backend/tests/test_upload.py)

**取舍：**增加内存副本，换取可预测的文件释放。上传入口本身已读取完整 content；PDF/OCR 图像和 embedding 对象还会增加内存。50 MiB 上传限制并不是整个请求的内存上界，也不是所有并发请求的总内存上界。

### ADR-04：关闭 SDK 自动 retry，由应用统一控制

**当前决策：**`OpenAI(..., max_retries=0)`，应用最多初始请求 + 两次重试，仅重试前等待 1s/2s；401/403 和 400 不重试。

**收益：**避免 SDK 与应用层重试相乘，调用次数和错误码容易验证。

**代价：**同步等待占用执行资源；配置的单次 timeout 不等于端到端 deadline。检索、连接、响应读取和多次退避的总时间不能简单由一个配置字段承诺。未做抖动、熔断或全链路取消，属于规模边界，SPEC §11.1 未设强制 SLA。

### ADR-05：context 截断与 sources 保持不同语义

**当前决策：**`assemble_context` 按分数依次加入完整 chunk，遇到超限即停止；`assemble_sources` 使用最终检索 Top-K。符合 F012 的停止规则及 F015 Detail 的 sources 定义。

**收益：**不切断 chunk，不由 LLM 构造 source 身份，保持可检查的检索证据。

**代价：**sources 可能包含未进入截断后 prompt 的 chunk；source 是检索来源，不等于逐句引用或模型实际采用的证据。F015 Explain 的概述不能代替 Detail 的明确 Top-K 定义。本轮不将此判成字段 bug，也不擅自修改 sources 合同。

### ADR-06：配置必须验证运行时消费点

T1204 将 middleware 的 `allow_origins=["*"]` 改为 `settings.CORS_ORIGINS`，并用独立进程测试允许、拒绝和默认行为。[main.py](../../../backend/app/main.py)、[test_cors.py](../../../backend/tests/test_cors.py)

配置字段存在、类型正确，只证明可声明；实际消费者是否读取它需要单独验证。CORS 仍不是认证系统：SPEC 的可信网络假设不能因为 origin allowlist 可配置而被升级为公网多租户隔离。

### ADR-07：验收定位使用 section + AC ID

104 个出现位置、85 个独立 ID 不能只保存为 ID-keyed map。不同 section 的同名 F003 AC 含义不同，需要保留原文位置和独立结果。Section 15 是导航索引，不应覆盖显式 Determine 枚举。[矩阵](../../verification/T1204/ACCEPTANCE-MATRIX.md)

代价是矩阵需要随证据迁移维护链接和版本。重复测试数量不能累加成“覆盖率”；静态字段检查、组件替身与浏览器交互也不能互相冒名。

### ADR-08：公开证据采用双哈希溯源

公开副本仅替换机器路径，原始文件保存在忽略目录，original/public 哈希分别记录。本轮检查 17 个 public hash 全部匹配；没有读取私有原件，也没有重新执行历史观察。[脱敏策略](../../verification/SANITIZATION-PROVENANCE.md)

这证明公开文件与 manifest 一致，不独立证明脱敏转换只影响路径；后者复用发布审查的变换核验。版本库接收者若没有原始本地副本，也不能独立重建其原字节。公开副本不能继续被无条件称为原始 capture。

## 4. Failure taxonomy 与一致性边界

| 触发 | 当前处理 / 观察 | 剩余风险 |
|---|---|---|
| 不合法上传名/类型/大小 | validate 在目标文件写入前拒绝；路径穿越有实际 API probes | 入口先读取整个上传内容，拒绝不代表未消耗内存 |
| 部分页 OCR 失败 | 保留有效页，SUCCESS_WITH_WARNINGS | warnings 需要调用方展示；通过的样例不是任意 PDF 质量保证 |
| 全页失败、解析失败 | FAILED/错误码与应用层 cleanup；验证无残留、同名重传 | cleanup 失败和进程崩溃不具备事务恢复 |
| delete raw 成功而 Chroma delete 失败 | 异常中断，后续 keyword invalidation 不执行 | raw 与 persisted preview 分叉；正常删除验收不能覆盖此时点 |
| DeepSeek transient failure | bounded retry，耗尽映射 LLM_UNAVAILABLE | 重试延长请求；没有全链路取消与 deadline |
| 认证失败 | 立即 LLM_AUTH_FAILED，不重试 | key 配置正确性是部署条件；无 secret 输出 |
| 空 KB / 非空 KB 无相关结果 | 前者 409 且不调用 LLM；后者继续以空 context 请求 LLM | 后者仍依赖 provider 可用性与提示遵循 |
| 上传成功后切换菜单 | 常驻 panel 保持 state | FileManager 同 KB 不自动重新拉取，file_count 不更新 |
| KB 指令注入 | system/user 分层，system 明确数据不能覆盖规则 | prompt-level mitigation；没有通用注入免疫证明 |

## 5. 当前发现与 Known Gaps

优先级用于安排后续工程讨论，不是本轮创建 Task 或重新判 Gate。STATIC 推导未声称已完成浏览器复现。

| ID / 优先级 | 具体触发、证据与影响 | 处置与最小验证 |
|---|---|---|
| ER12-01 / HIGH | FileManager 已在 KB-A 完成首次加载；在同 KB 上传成功，再切文件菜单。`page.tsx` 常驻隐藏 panel，FileUpload 成功只更新局部结果，没有上传事件；FileManager effect 在选择不变时直接返回。列表和 shared file_count 可保持旧值。[STATIC] | **CLOSED / REMEDIATED（F-6）**。历史为 OPEN，API lifecycle 和 source-string inspection 未覆盖跨组件状态。实际 Home/components、MOCKED API/hooks integration 捕获修复前失败并在修复后通过；独立增量 Gate 确认 PASS。不是 browser upload E2E。见上方两份证据链接。 |
| ER12-02 / MEDIUM | 上传中切 KB 后原请求完成，`runUpload` 没有 owner/version commit guard，旧结果可进入当前 panel；现有 guard 主要覆盖读取/QA。[STATIC] | OPEN；后续受控延迟响应验证 A→B owner 转移。无需真实 provider 制造延迟。 |
| ER12-03 / MEDIUM | raw 删除与 vector 删除之间、批次写入与 cleanup 之间中断，多个存储面可能不一致。[STATIC] | KNOWN BOUNDARY；后续如要求更强恢复保证，先定义恢复语义再选补偿/日志方案。不能宣称当前 crash-safe。 |
| ER12-04 / MEDIUM | KeywordRetriever 缓存为进程内 class state，以 collection name 为 key；其他 worker 的 invalidation 不自动传播。[STATIC] | 部署边界：不能把单进程验证推导到多 worker。多 worker 成为目标时再明确缓存 namespace 和失效协议。 |
| ER12-05 / LOW | 页面仍显示 Phase 10/application shell，与当前产品阶段不一致。[STATIC，page.tsx] | 文案陈旧，不是后端 AC 回归。本轮不改产品 UI。 |
| ER12-06 / EVIDENCE LIMIT | 浏览器真实选取超限文件受权限限制；组件 2/2 检查 handler、提示和零 API 调用。[既有证据] | 不冒称 browser-upload PASS。需要该交互级保证时补 browser fixture，非新增 live failure gate。 |

当前未发现需要在本轮立即修改冻结 SPEC 的新冲突。以上风险不会因 SAFE_TO_COMMIT 消失；公开发布审查处理的是文件内容、秘密与溯源，职责不同。[发布结论](../../verification/PUBLIC-RELEASE-READINESS.md)

## 6. 规模分析与重新评估条件

- **摄取内存：**入口完整 bytes、PDF bytes、OCR 图片、chunk strings 和 embedding 数组均可能共存。容量需按并发请求与展开后数据估算；本轮没有测 RSS，不给出虚构峰值。
- **列表/关键词：**`get_files` 从 chunks 投影文件元数据，关键词索引全量 rebuild 并在进程内保存内容与 posting sets。文件数少但 chunk 数多时也会有成本；列表长度不是唯一规模指标。
- **QA：**context 的 4000 字符只限制该段；history 限制最近 20 条是条数限制，不是总字符/token 限制。同步调用和退避随并发消耗执行资源。
- **模型质量：**固定 fixture、真实 512d 与融合公式通过，不构成整体召回率、事实正确率或对抗鲁棒性 benchmark。

SPEC §11/OQ-009～011 明确未要求正式性能 SLA、高级监控或自动备份。只有实际部署假设扩大、观测到内存/延迟压力、或恢复要求提高时，才重新讨论 worker、队列、增量索引或持久化协调；这些都是讨论触发条件，没有在本轮实施。

## 7. 本轮验证记录

| 执行 / 核查 | 类型 | 本轮结果 | 限制 |
|---|---|---|---|
| 根目录 `python backend/scripts/verify_t1202_failure_contract.py` | DETERMINISTIC | PASS 15，FAIL 0，SKIP 0，exit 0；provider_requests=0 | 429/500/503/599 恢复与耗尽，401/403/400 单次不重试；不是 live HTTP |
| Python hashlib 校验 `sanitization-provenance.json` 中 public_path 对 sanitized_sha256 | STATIC / INTEGRITY | 17/17 匹配，exit 0 | 不读取私有原件，不重新证明转换过程 |
| T1204 pre-audit baseline 对当前 backend/app、frontend/app/components/lib | STATIC / VERSION | 33 个文件；仅 backend/app/main.py 不同，exit 0 | baseline 是修复前快照；该变化对应已有 CORS 修复及测试 |
| T1201 Qwen 91/91、T1202 DeepSeek 70/70、T1203 43/43、T1204 42/42 与全套 83/83 | REUSED LIVE / E2E / DETERMINISTIC | 复核已有最终记录，未重新执行 | 保留各 provider/替身边界，不累计为新测试数 |

复用入口：[最终 commands/results](../../verification/T1204/README.md)、[T1202 blocker audit](../../verification/T1202/BLOCKER-AUDIT.md)、[browser evidence](../../verification/T1204/browser.md)、[source applicability](../../verification/T1204/live-evidence-validity.json)。没有重复昂贵 provider 请求，也没有新测试框架或 dependency。

## 8. 交付与责任边界

新增本 Engineering Review，同步学习目录与 Phase 12 学习章链接。保留既有未提交代码、发布文件和历史记录；没有修改应用、验收矩阵、Task 状态或 SPEC，没有启动修复或下一 Task。

工程复盘已完成；ER12-01 已作为 F-6 CLOSED / REMEDIATED；ER12-02 等其他边界未被本次修复覆盖。独立 Phase Gate Re-review 已完成 PHASE_12_PASS，Learning fresh-reader 也仍待执行。本文件不授予 SAFE_TO_COMMIT 给本轮新增文档，发布组若要纳入该文件需按其正常 diff review 处理。
