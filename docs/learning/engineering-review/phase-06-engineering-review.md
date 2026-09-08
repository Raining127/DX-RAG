# Phase 6 — Keyword Retrieval Engineering Review

## 1. Review Purpose — 这份评审要判断什么？

这是 Phase 6 关键词检索的工程回顾。[Technical Learning](../phase-06-keyword-retrieval.md) 负责解释概念、数据流和代码机制；本文假设读者已经理解这些内容，集中判断设计为何合理、牺牲了什么、一致性与失败边界在哪里，以及什么证据会促使我们换设计。

本次仅细化原评审的结构与判断表达，保留原 ADR-01～10 的编号与核心理由。正文区分原始设计、当前源码和后续补证；工程取舍结论不是新的 Gate 裁决，历史状态与验收记录见附录。

## 2. Executive Engineering Summary — 这个设计在什么前提下合理？

**要解决的工程问题**不只是增加一条关键词查询函数，而是让词面检索能与已有持久化数据和后续向量检索协作：文档与问题必须共享可复现的 normalization contract；索引必须能在上传、删除、重命名后恢复一致；返回分数必须有明确语义，便于下游组合。

关键词支路补充精确术语、缩写、型号和错误码等词面信号，但“精确”受分词边界约束，并非原字符串逐字相等。向量支路负责语义泛化；这是一项架构动机，没有证据表明本项目混合检索在统计上总优于单路。

最重要的设计判断是：

- **规则保持轻量、确定**：中文 bigram 与英文数字正则通道、稳定去重、纯函数复用，让索引 key 与评分分母可以直接核对。
- **持久化 chunks 是唯一权威来源**：关键词索引是可重建的内存派生状态，通过 `VectorStore.list_chunks()` 获取数据，不增加一份独立持久化格式。
- **索引表示与记录分开**：postings 只放 ID，返回时关联 ChunkRecord；避免每个 token 重复保存内容，代价是双表必须一致。
- **写路径通知，读路径重建**：lazy/dirty 全量 rebuild 避免每次 mutation 都重算；class-level state 使独立通知函数能影响同进程实例。
- **覆盖率分数边界明确**：unique-token presence 归一化到 `[0,1]`，供后续融合；它不包含词频、稀有度或位置相关性。

**最大的成本转移**是：写路径的轻量失效通知把全量读取、分词和建表延迟留给下一次查询；重建时旧/新快照还可能同时占内存。简单评分同时放弃了更细的词面相关性表达。没有 benchmark 能把这些成本换算成可承诺的延迟或容量。

**最重要的一致性风险**是所有权不完全匹配：缓存只以 collection name 为 key，store 却注入各个实例。同进程多 store 同名可能串缓存，多 worker 不共享 dirty，双表顺序发布也没有并发原子性。原评审采用本地单进程前提；单进程本身并不排除并发请求，相关交错仍未验证。

**重新评估的触发点**应是实测重建耗时/内存不可接受、实际语料出现召回缺口、需要位置或更细排名语义，或部署将引入多 store/worker。前两项需要测量，后两类契约/部署变化本身就足以触发设计复核，不应等到生产事故才处理。

## 3. Decision Map — 哪些问题决定了当前架构？

| Engineering Question | Current Decision | Main Benefit | Main Cost | Revisit When |
|---|---|---|---|---|
| 中文词面规则如何控制依赖与行为？ | bigram + 分离通道（ADR-01/02） | 无词典生命周期，字符边界明确 | 粗粒度字符信号、范围与顺序限制 | 真实语料缺口或位置要求出现 |
| 两侧如何保持同一比较契约？ | stable dedup + pure function（ADR-03/04） | 计分与诊断可重复 | 临时分配，状态需另行管理 | 配置化规则需求或分配成本有实测问题 |
| 怎样冻结规则而不扩大证明范围？ | exact examples + boundary tests（ADR-05） | 防止 key/分母回归 | 未覆盖 Unicode 全域或检索质量 | 新语料或契约变化需要回归证据 |
| 谁拥有可跨实例失效的缓存？ | class cache + instance store（ADR-06） | caller 不需持有 retriever | namespace 碰撞、进程不共享 | 多 store / worker 进入部署方案 |
| postings 是否复制完整记录？ | ID 索引 + 记录双表（ADR-07） | 减少重复内容存储 | 双表一致性和发布责任 | 并发保证或内存预算改变 |
| 为何索引可丢弃、何时重建？ | derived state + lazy/dirty full rebuild（ADR-08） | 单一权威源，写路径轻量 | 冷/脏首查延迟与峰值内存 | 重建或重启恢复成为实测瓶颈 |
| 下游需要什么分数契约？ | binary unique-token coverage（ADR-09） | 范围明确，可组合 | 不看词频/稀有度/位置 | 评测显示相关性信号不足 |
| 构建失败时能否继续信任共享表？ | local build 后发布（ADR-10） | 不发布构建阶段残表 | 非原子发布，本次失败向上传播 | 并发、版本或恢复要求提高 |

表中收益来自规格与原评审的设计理由，升级方向是工程推理或已记录的 Future；没有替代方案性能竞赛记录。详细 ADR 的证据指向附录 A/B 的源码与验证材料。

## 4. Architecture / Ownership Context — 谁对数据正确性负责？

```text
持久化 chunks（权威数据）
        │ VectorStore.list_chunks() public interface
        ▼
KeywordRetriever 实例的 vector_store
        │ 构建并发布
        ▼
同进程 class cache：postings + chunk snapshot + dirty set
        ▲                                      │
upload / rename / delete → invalidation seam    └→ keyword candidates
                                                         ↓
                                              后续 HybridRetriever
```

新增契约是 `str → ordered unique tokens`（按生成通道顺序稳定去重），以及 `collection/query/top_k → ranked keyword results`。tokenizer 不反向依赖索引或存储；retriever 只用公开的 `list_chunks()`，不穿透 Chroma 私有对象。这既限制耦合，也让 build 可以注入测试存储。

`keyword_index.py` 是写调用方与共享缓存的连接点，不拥有第二份索引。它曾是 documented no-op，Phase 6 将其接到 `KeywordRetriever.invalidate()`，既有 caller 无须改调用形状。当前代码后来增加了异常恢复，见第 6、9 节及附录 C；不能把恢复能力归入原始实现证据。

下游使用结果契约，不获得缓存所有权。后续 `HybridRetriever` 按 chunk_id 融合 keyword/vector 分数，`retrieve()` 把同一 store 注入三种 retriever。当前 `QAService` 和 QA API 也已存在，QAService 直接消费 HybridRetriever；原评审的“QA API 尚未实现”属于早期检查点，见附录 C。逐步机制继续由 Technical Learning 承担。

## 5. ADRs — 为什么保留这些选择，什么时候该换？

以下保留原有十条 ADR 的顺序和核心 Decision / Why / Trade-off，并补工程问题、替代方案性质、失败条件和当前判断。**KEEP / KEEP WITH KNOWN LIMIT** 是在已述约束下的工程建议，不是 Gate PASS，也不声称生产容量已经验证。

### ADR-01: v1 中文采用 overlapping character bigram

- **Engineering Problem / Constraints**: 需要中文词面信号，又要保持冻结分词契约与较小依赖面；不能把词典和模型维护带入这一切片。
- **Alternatives**: jieba 是规格明确排除的方案；单字 token 是学习文档中的设计对照。没有实验比较记录。
- **Decision**: 连续中文段用宽度 2、步长 1 的滑动窗口。
- **Context**: SPEC F009 明确排除 jieba、BM25 与 TF-IDF。
- **Why**: 零第三方依赖、无词典生命周期、O(n)、对未登录词与技术名词具有边界鲁棒性。
- **Trade-off**: 重叠窗口增加 token 与 posting 的存储压力；匹配只代表字符片段重合，不代表理解语义。与具体词典方案相比的唯一 key 数和体积尚未测量。
- **Future**: 若召回质量或索引规模成为实测瓶颈，再以评测集驱动替换，不提前优化。
- **Failure Modes**: 字符重合可能带来误召回；基本 CJK 范围之外的语料可能漏信号。原评审的“未登录词鲁棒性”指不依赖词典收录，不是实测召回质量优势。
- **Evidence / Current Verdict**: `tokenize()`、`TokenizeTests` 与 F009 分词契约；**KEEP WITH KNOWN LIMIT**，质量或体积出现实测问题再评估词级方案。

### ADR-02: 英文与中文使用两个互斥正则通道

- **Engineering Problem / Constraints**: 中英混合文本需要明确边界，同时必须满足 exact examples；下游目前不消费 token 位置。
- **Alternatives**: 单通道保留 source order、删除非中文后整体切分是设计对照；后者会制造跨标点或英文的假相邻关系，未采用。
- **Decision**: 英文/数字与连续中文段分别提取。
- **Why**: 规则直接对应 SPEC，标点自然成为边界，不需要先修改原字符串。
- **Trade-off**: 输出按通道分组，不保持跨语言原文顺序；中文范围不覆盖所有 Unicode 扩展区。
- **Assessment**: T0602 按集合语义消费 query tokens，matched counter 不把 token 顺序当相关性信号。
- **Failure Modes / Revisit When**: 消费者要求位置感知或跨语言 source order，或真实语料暴露 Unicode 范围缺口时，当前通道契约需要重审并重建索引。
- **Evidence / Current Verdict**: 两个 regex、`tokenize()`、segment boundary / mixed-language tests；**KEEP WITH KNOWN LIMIT**，只承诺当前字符范围和集合消费语义。

### ADR-03: 稳定去重采用 dict.fromkeys

- **Engineering Problem / Constraints**: 重复 query token 不能放大匹配计数或评分分母，测试与诊断又需要可复现的列表。
- **Alternatives**: set 去重是已记录的设计对照，可保持唯一性但不提供同样的输出顺序契约；没有性能比较记录。
- **Decision**: 过滤后以 insertion-ordered dict 去重。
- **Why**: keyword_score 的分母要求 unique tokens；稳定结果使测试与诊断可重复。
- **Trade-off**: 建立临时 dict，复杂度仍为 O(n)。原评审认为 query 长度下成本可忽略，这是工程估计，未做 benchmark。
- **Failure Modes / Revisit When**: 移除去重会改变 score 语义；换成无序输出会削弱 exact-list 诊断。只有观察到临时分配成本成为瓶颈，才值得重审此实现，且要保留唯一性与顺序契约。
- **Evidence / Current Verdict**: `dict.fromkeys()`、stable dedup test 与 F009 unique-token 公式；**KEEP**，没有内存/耗时 benchmark 支持进一步优化。

### ADR-04: tokenizer 保持纯函数

- **Engineering Problem / Constraints**: 建索引与查询必须始终使用同一 normalization contract；分词不应承担存储生命周期。
- **Alternatives**: 两侧复制规则、把 index/config 注入 tokenizer 是职责划分对照，非实验淘汰方案。
- **Decision**: 不把索引、cache、VectorStore 或配置注入 T0601。
- **Why**: document/query 两侧能复用同一规则；测试无需 fixture 或 mock；Task 边界清晰。
- **Trade-off**: KeywordRetriever 必须单独管理索引生命周期，不能从 tokenize() 获得状态。
- **Failure Modes / Revisit When**: 两侧规则复制后漂移会漏召回；替换规则而沿用旧缓存也会错配。只有实际需要配置化分词策略时才调整接口，并同时设计规则版本与重建边界。
- **Evidence / Current Verdict**: `tokenize()` 无状态，build/search 均复用它；纯分词测试不需要存储 fixture/mock；**KEEP**。

### ADR-05: exact examples + boundary tests 共同冻结契约

- **Engineering Problem / Constraints**: 示例正确不足以排除会改变索引 key 和评分分母的边界回归；验证结论必须可精确复查。
- **Alternatives**: 仅测 happy path 是覆盖对照；property-based / Unicode 全域测试是未来候选，当前没有这些证据。
- **Decision**: 除 SPEC exact examples 外，补测 alphanumeric lowercase、单字符、中文 segment boundary 与 stable dedup。
- **Context**: happy-path examples 证明主规则，但不能证明标点是否跨界、重复 token 的顺序或数字是否保留。
- **Why**: 这些边界会直接改变未来 inverted-index keys 与 score denominator。
- **Trade-off**: 当前测试仍不是 Unicode 全域或 property-based test；覆盖范围应诚实限定为已列场景。
- **Future**: 出现真实语料缺口后，再增加对应 regression case。
- **Failure Modes / Revisit When**: 列表样例通过仍可能漏掉未枚举语料或并发情形；有真实语料缺口时增加 regression case，字符支持范围扩大时再补对应系统性测试。
- **Evidence / Current Verdict**: 原始 6 个 `TokenizeTests` methods；**KEEP WITH KNOWN LIMIT**，这些是契约回归证据，不是检索质量评测。

### ADR-06: class-level shared cache + instance-level VectorStore

- **Engineering Problem / Constraints**: 写调用方只有 collection_name，却需要让同一进程里的检索实例看见失效通知；读取源还需可注入。
- **Alternatives**: instance cache 是所有权对照；application-owned singleton 或将 store identity 纳入 key 是原评审的 Future 方向，未实现。
- **Decision**: _indexes/_chunks/_dirty_collections 定义为 class attributes；vector_store 由 constructor 注入到 instance。
- **Context**: keyword_index.py 的 standalone seam 只有 collection_name，没有 retriever instance。
- **Why**: classmethod invalidate() 能从任意 mutation caller 标记全进程共享 cache；build 仍可通过 injected VectorStore 测试。
- **Trade-off**: cache namespace 只有 collection name。若同一进程存在多个独立 VectorStore namespace 且 collection 同名，会共享错误 snapshot。
- **Future**: 多 tenant/store 场景将 store identity 纳入 key，或改为 application-owned singleton service。
- **Failure Modes / Revisit When**: 同名独立 store 会串 snapshot；多 worker 的 dirty 不共享。只要部署或测试引入多数据源/多进程，就应先重审所有权和通知协议，不必等吞吐先变差。
- **Evidence / Current Verdict**: class attributes、instance `vector_store`、`invalidate()`；unit setUp 清共享表，未验证 namespace 隔离或跨进程一致性；**KEEP WITH KNOWN LIMIT**。

### ADR-07: 双表 snapshot，不在 posting 中复制 ChunkRecord

- **Engineering Problem / Constraints**: token postings 要便于查候选，返回时又需要文件信息和内容；公开存储接口已提供 ChunkRecord。
- **Alternatives**: 每个 posting 保存完整记录是已记录的表示对照；原子替换一个组合快照是针对并发的未来候选，不是当前能力。
- **Decision**: _indexes 保存 token → chunk_id set，_chunks 保存 chunk_id → ChunkRecord。
- **Why**: posting set 保持轻量；返回阶段按 chunk_id 做 in-memory join，避免每个 token 重复保存 content/metadata。
- **Trade-off**: 两张表必须来自同一次 build；当前是依次发布而非并发原子替换，否则可能出现 dangling id 或跨版本观察。
- **Mitigation**: 当前实现先在 local dict 完整构建，再依次替换 shared state；这能避免单线程异常时发布 half-built snapshot，但不提供无锁并发下的 atomic publication。
- **Failure Modes / Revisit When**: 双表跨版本可能形成 dangling id 或返回旧字段。需要并发读写保证、出现相关交错失败，或重建内存不可接受时，重新评估发布单元和表示。
- **Evidence / Current Verdict**: `_build_index()` 两次顺序 assignment、search 按 ID join；这是 CODE 事实，不是原子性测试结论；**KEEP WITH KNOWN LIMIT**。

### ADR-08: lazy build + dirty flag + query-time full rebuild

- **Engineering Problem / Constraints**: 持久化 chunks 是权威来源，索引可以重算；若维护第二份独立 durable truth，将新增同步责任。v1 明确仅内存、无增量。
- **Alternatives**: mutation-time rebuild 是设计对照；增量、持久化或独立 lexical engine 是未来候选，不能因更成熟就跳过规模/一致性证据直接迁移。
- **Decision**: cold/dirty cache 在下一次 keyword_search 前 full rebuild；mutation path 只 add dirty flag。
- **Why**: 符合 SPEC v1 明确的“无增量更新”；没有查询的 collection 不付 build 成本；upload/rename/delete 保持轻量。
- **Trade-off**: mutation 后第一个 query 承担全量重建 latency；旧 snapshot 在此之前仍占内存。
- **Future**: 只有真实规模证明 full rebuild 不可接受时才评估 incremental index。
- **Failure Modes / Revisit When**: 漏通知会保留 stale cache；查询集中承担重建和旧/新快照占用。重建 latency 或峰值内存实测不可接受、冷启动恢复成为明确要求时，才评估后台/增量/持久化方案。
- **Later boundary**: 当前 seam 已补普通失效异常后的强制 dirty 与日志；持久化上传/删除提交成功不因这类缓存维护失败而回报失败。该恢复契约属于后续补充，证据见第 9 节。
- **Evidence / Current Verdict**: F009 lifecycle、lazy/rebuild/no-op unit tests 与当前 seam；**KEEP WITH KNOWN LIMIT**，不是无界规模或所有故障下的恢复保证。

### ADR-09: binary unique-token coverage score

- **Engineering Problem / Constraints**: 下游需要定义明确、范围固定的 lexical score 来组合检索信号；当前规格选择 unique-token presence。
- **Alternatives**: term frequency、BM25、TF-IDF 是已记录的评分对照，后两者被 v1 明确排除；没有项目检索质量对比实验。
- **Decision**: matched unique query tokens / total unique query tokens。
- **Why**: 直接兑现 SPEC，天然归一化到 [0,1]，可供 Phase 7 与 vector score 融合。
- **Trade-off**: 不看 term frequency、inverse document frequency 或 token rarity；常见 token 与稀有 token 等权。
- **Failure Modes / Revisit When**: 1.0 不是答案概率或短语匹配；同范围不等于两路已校准。若评测发现常见词、稀有术语或长度偏差影响质量，再比较排名策略与融合参数。
- **Evidence / Current Verdict**: `keyword_search()` 公式、1.0/0.6/无命中 unit cases；后续 HybridRetriever 固定 0.3/0.7 融合，未证最优；**KEEP WITH KNOWN LIMIT**。

### ADR-10: local build 后发布，失败不清 dirty

- **Engineering Problem / Constraints**: 构建过程可能在读取或分词时失败，不能让下一次查询误以为新快照已经有效。
- **Alternatives**: 边遍历边更新 shared dict 是对照；并发锁、版本化或组合快照发布是未来改进，原代码不具备。
- **Decision**: _build_index 先构建 local inverted_index/chunks；成功后才写 class cache 并 discard dirty。
- **Why**: list_chunks/tokenize 失败时不发布 half-built snapshot，下次查询仍可重试 rebuild。
- **Trade-off**: rebuild 峰值期间旧/新 snapshot 可能同时占内存；当前无并发 synchronization。
- **Failure Modes / Revisit When**: 构建异常仍会让本次查询失败，不回退返回旧表；两次 assignment 不是事务，并发 invalidate/build 交错未受保护。并发保证或重建资源预算成为要求时，重审发布和版本策略。
- **Evidence / Current Verdict**: `_build_index()` 的局部构建→顺序发布→discard dirty 是 CODE / STATIC 依据；原 7 个 retriever tests 未专门注入 build 中途异常或并发交错；**KEEP WITH KNOWN LIMIT**。

## 6. Failure & Consistency — 哪些保护有效，哪里仍可能失效？

核心区分是：缓存可重建不等于自动一致，构建失败保护不等于并发事务。写操作负责发出失效通知，retriever 负责查询前恢复快照；持久化存储决定重建内容。下面综合跨 ADR 风险，不把推导风险包装成真实 incident。

| Failure / Risk | Cause / 性质 | Current Protection | Residual Risk | Upgrade Direction / 触发 |
|---|---|---|---|---|
| 已变更数据仍用旧快照 | 通知遗漏或未被读取方看见；推导风险 | 正常 seam 标脏，next query 全量重建；unit 覆盖此链 | 未覆盖所有调用遗漏及 worker 间传播 | mutation 集成回归；跨进程部署前定义共享版本/通知 |
| 已提交上传被缓存异常误报失败 | 后续故障注入覆盖的提交边界问题 | 当前 seam 捕获普通 invalidate 异常，强制 `mark_dirty()` 并记录日志 | 兜底标记自身失败不在同一个 catch 保护内；不承诺进程/资源故障恢复 | 保持 durable commit 与 cache maintenance 分界；新增失败类型再补回归 |
| 两个 store 的同名 collection 串缓存 | class key 无 store identity；已知推导风险 | 在同一数据源 namespace 内共享通知 | 注入不同 store 不会自动隔离 cache，可能无异常而返回错数据 | 多 store/tenant 前重审 key 或 application-owned service |
| 写入后某些 worker 仍读旧内容 | 各进程有独立 dict/set；部署风险 | 同进程可见 | 没有跨进程 invalidation 协议 | 多 worker 前设计通知/版本检查，而非仅增加进程数 |
| 返回旧字段或 dangling ID | 双表发布跨版本；并发推导风险 | 局部建好再依次替换 | 无锁，不是 atomic publication | 需要并发保证时定义组合快照、锁或版本策略 |
| build 中途失败 | list_chunks/tokenize 异常；代码路径推导 | 构建阶段不发布局部残表，保留已有 dirty；cold cache 仍未建成 | 异常向上传播，本次查询失败；原 unit 未专测该故障 | 有恢复/可用性要求时先定义失败语义再补故障测试 |
| build 与 invalidate 交错 | 无版本/同步；未验证风险 | 正常顺序路径成功后才清 dirty | 不能证明并发下不漏更新；单进程不等于顺序执行 | 增加交错验证，并据结果定义同步协议 |
| 无结果或非法截断被误当算法错误 | 空 token、无命中、top_k 边界 | 空 token 与 missing posting 返回空；API 当前校验 top_k | class 内 0 返回 `[]`，负数仍按 Python slice；首个空 query 也可能先 build | 新的直接调用方要承担入参契约，不依赖 HTTP 层替它校验 |
| 同分结果顺序变化 | set 遍历影响候选初始顺序；已知限制 | 只保证 score DESC + top_k | 未定义 tie-breaker | 稳定回放/翻页成为需求时定义次序并测试 |
| 长文本/大量快照消耗资源 | 线性扫描、驻留缓存、重建峰值；规模风险 | tokenizer 不执行输入、不访问路径、不调用网络；内容来自 public records | 这些隔离不限制 CPU/内存，当前没有 question 最大长度约束 | 测量请求成本、驻留规模、峰值后决定限制或重建方案 |

当前普通 `invalidate()` 正常路径只做内存标记；新增 catch/force-dirty 处理的是后续提交后维护契约。关于原评审“失败映射不可达”的历史判断，见附录 C 的 Pending #34；不以旧结论否定后来恢复需求，也不把注入故障改写为线上事故。

## 7. Scalability & Upgrade Triggers — 哪个假设会先被打破？

当前简单方案的理由是较小依赖面、明确规则、可重建和可测试，以及原评审的本地单进程前提；**不是已有规模测试证明一切成本可接受**。先观察具体代价，再决定换哪一层。

| 当前设计 / 假设 | 首先可能疼在哪里 | 如何观察 | 触发重新设计的条件 | 可考虑的方案类别（尚未实现） |
|---|---|---|---|---|
| query 两次扫描与去重 | 长 query 的 CPU/分配量 | 按输入长度记录分词耗时、内存和请求延迟 | 已影响目标请求预算，或需要明确资源上限 | 输入长度约束、必要的分配优化 |
| cold/dirty 全量 build | 变更后首查延迟集中 | 分开记录 list_chunks、分词、建表耗时与发生频率 | 实测重建成本不能接受 | 后台/增量重建；同时定义读取旧版本还是等待 |
| 内存 postings + 记录表 | 驻留 collection 数、双快照峰值 | corpus 字符量、posting 数、驻留与峰值内存 | 资源预算被观察到突破，或恢复时间成要求 | 生命周期管理、持久化或独立索引；v1 当前不提供 |
| 单进程共享通知 | 扩 worker 后 stale 数据 | 比较 mutation 后不同进程的查询结果 | 部署计划开始要求多进程一致性 | 外部通知/版本检查或统一服务所有权 |
| 仅 collection name 隔离 | 新 store/tenant 同名碰撞 | namespace 与实例生命周期审计、隔离用例 | 引入独立数据源，而不仅是 corpus 增大 | store identity 进入 key、application-owned service |
| bigram 与等权 coverage | 语料漏召回/误召回或术语排序不足 | 建立标注 query/chunk 评测集，区分分词与评分原因 | 质量差距可复现且有证据 | 词典策略、BM25/TF-IDF/位置模型等对比，需重建与契约迁移 |

复杂度仍保留原分析：tokenizer 时间/空间约 **O(n)**；build 随 corpus 总字符量 C 约 **O(C)**，另有存储读取和逐 chunk 开销；q 个 query tokens、posting 集合大小之和 P 的查找计数约 **O(q+P)**，m 个候选排序 **O(m log m)**。这些是实现结构推导，不能换写成具体 latency/SLA。

原评审用 **10x query length / 100x corpus / 1000x corpus** 讨论压力：分别指向线性请求成本、full rebuild 与双快照峰值、单进程内存索引是否仍适用。保留这些思考维度，不把“通常可接受”当成已测容量。bigram 的重叠窗口带来 token 压力，但相比具体词典分词会产生多少唯一 keys，本仓库没有 corpus-level measurement，不能保证所有语料都更多。

专用 lexical engine（例如 Elasticsearch）仅是满足规模、排名或一致性要求后的**未来候选**，不是原团队已评测后否决的方案。BM25 是排名选择，独立搜索服务是部署/存储选择；两者不能被笼统当作一次“性能升级”。

## 8. Known Gaps — 哪些限制接受，哪些变化应触发行动？

### 8.1 Accepted v1 limitations：范围接受不等于没有影响

| Gap | 当前影响 | 为什么接受 / 触发行动 |
|---|---|---|
| 内存索引、全量 rebuild，无增量/持久化 | 重启冷缓存、首查成本、快照占用 | F009 明确范围；实测重建/恢复成本变化时再评估 |
| 基本 CJK 范围、通道顺序、无位置/词频/稀有度权重 | 不覆盖所有中文，不表达全部 lexical relevance | 当前冻结契约；真实语料与评测暴露缺口时修订 |
| 同分 tie-breaker 未定义 | 不承诺稳定回放/翻页 | 当前只要求降序/top_k；消费者需要稳定次序时行动 |

### 8.2 Technical debt：维护与所有权问题

| Gap | 当前影响 | 行动条件 |
|---|---|---|
| class cache 只有 collection key | 生命周期与多 store ownership 容易混淆 | 新增数据源前先处理隔离；无需等性能瓶颈 |
| build/invalidate 无同步、双表非原子发布 | 正确性依赖尚未验证的交错行为 | 明确并发要求并建立针对性验证后决定实现 |
| qa.py 继续承载检索与问答职责 | 文件职责扩大，阅读和改动边界需维护 | 真实改动耦合开始妨碍维护时按职责拆分，本文不改代码 |
| 原 module docstring 债务 | 当时名称落后于职责 | 当前 docstring 已更新，旧观察保留在附录 C；不继续列作未修复原文案 |

### 8.3 Unverified assumptions：实现存在不能代替证据

没有多 store 同名隔离、多 worker invalidation、并发 build/invalidate、双表原子性保证；没有 performance/corpus benchmark、property-based 或 Unicode 全域测试。原 7 个检索单测也没有专门证明 build 中途异常后的状态。把它们分别视为部署/正确性/质量问题，不能统一用“单测全绿”作答。

原 Known Gap #1 的 literal upload/rename/delete → real Chroma rebuild → query 在 Phase 6 收官时未覆盖。后续真实上传重建和文件删除生命周期已增加各自范围的证据（第 9 节），但不能合并成原 Phase 6 已证明所有 mutation、并发与浏览器链路。

### 8.4 Future capability：范围外功能不等于待修 bug

增量、持久化/分布式索引、后台重建、词典分词、BM25/TF-IDF/位置感知排名是后续候选，均需第 7 节的触发理由。Hybrid/QA 在原收官时是下游范围，当前已由后续阶段实现；其完成不补足本节未验证的规模和一致性假设。

## 9. Evidence & Verification Boundary — 哪些证据支持这些判断？

证据支持的是**指定行为在指定边界成立**。代码可以说明实现选择，单元测试可以防确定性回归，组合检查可以证明 wiring；只有明确经过真实依赖的验证，才能说明那段真实链路。以下使用原记录中的术语，并补充分类说明，不重新命名历史 PASS。

### 9.1 收官时知道什么？

从代码能确认 shared tokenizer、public-interface build、class-level cache、双表发布顺序、coverage 公式与 dirty lifecycle。这些是 **CODE / STATIC** 判断；无锁与 key 缺少 namespace 也由代码可见，但其生产故障频率未知。

原 **UNIT / unit-level behavior**：2026-08-27 执行 `python -m unittest tests.test_qa -v`，**13/13 test methods PASS**，其中 tokenizer 6、retriever 7。tokenizer 直接执行；retriever 使用 **MOCKED** `Mock(spec=VectorStore)`，每个 setUp 清空三份共享状态。该分类说明依赖替身，不改动原 Gate 的术语。

| 原始行为 | 证据支持的工程判断 |
|---|---|
| SPEC exact examples、lowercase、单字符过滤；额外 segment boundary / stable dedup | normalization key 与列表输出有确定性回归保护 |
| lazy list_chunks build + AC-F009-01 = 1.0 | 首次才从接口取数据，中文全命中 |
| AC-F009-02 = `[]` | 无命中不返回候选 |
| AC-F009-03 = 0.6 | 用 3/5 unique query token coverage，不用 raw term frequency |
| AC-F009-04 = 1.0 | 中英混合信号共同参与匹配 |
| score DESC + top_k | 排序/截断契约有测试，不保证同分 tie order |
| dirty → next search full rebuild | 替换 Mock source 并直接调用 seam 后能检索到新增记录 |
| absent index invalidation no-op | 未构建时不制造无意义 dirty entry |

AC-F009-01～04 的 unit-level 行为已覆盖；AC-F009-05 当时是 **PASS（Phase 6 scope）** 的核心生命周期，literal E2E **DEFERRED TO PHASE 12**。没有真实 upload HTTP request、Chroma runtime 或 provider，不能把这 13 个测试写成真实集成。如今 test_qa.py 已扩展，原计数不代表当前全文件测试数。

### 9.2 后续项目才补到了哪里？

| 后续材料 | Evidence classification / 边界 | 支持的结论与不能推出的结论 |
|---|---|---|
| 向量、Hybrid 与 facade 检查 | UNIT；facade 3 个 tests 是 patched composition/propagation boundary | embedding/search 适配、0.3/0.7 融合/filter/Top-K、same-store wiring、empty/missing 行为；不是实际 Chroma E2E |
| QA route 检查 | 10 个 route-level MOCKED tests | 请求校验、委托、响应/错误格式；不是 provider/browser 证据 |
| [上传回滚 V11](../../../backend/scripts/verify_t0503_rollback.py)；[后续回归记录](../../verification/T1201/README.md) | 正常 invalidate 被注入异常；embedding SUBSTITUTED，真实应用/临时存储；回滚 suite 56/56 是后续记录 | 提交后缓存失败不应使上传回报失败，下一次查询可恢复；不是 Phase 6 原 unit 或线上事故 |
| [T1202 验收](../../verification/T1202/README.md) | REAL / LIVE：TestClient API、实际 BGE、临时 Chroma 与 DeepSeek；另列 DETERMINISTIC/SUBSTITUTED 检查 | F009-01～05 ledger 包含真实新上传后缓存重建；应用/API E2E，不是 browser/TCP/CORS/frontend E2E |
| [T1203 生命周期记录](../../verification/T1203/README.md) | REAL FastAPI、临时文件/Chroma、删除/失效；embedding 为 deterministic substitute；43/43 | 具体文件生命周期与隔离检查；原前端 source-string 检查仅 STATIC，新组件测试用受控 API/hooks，不等于浏览器上传 |

T1202 记录的 LIVE checks 为 **70/70**；focused QA/query **60/60**、deterministic matrix **46/46**、failure contract **15/15** 各有自己的证明范围，不能相加后当作 AC 数量。历史 live log 的 **exit 2** 来自后来移除的额外 gate，记录保留；该审计未重新请求 provider。真实 provider 429/5xx/403 仍为 **NOT_OBSERVED**，确定性故障注入没有被升级成 live 响应。

这些后续证据支持“原先延期的指定链路后来被验证”，不支持“Phase 6 收官时已完成真实 E2E”。最终验收以 [T1204 最终材料](../../verification/T1204/README.md) 的时点与范围为准，本文不另行发出 Phase Gate 结论。

### 9.3 仍不知道什么？

没有统计检索质量比较、固定融合权重最优性、真实大语料容量或 latency/SLA 证据；受控真实问答也不是通用质量或安全保证。源码推导的异常保护不能冒充故障注入结果，正常 lazy/dirty 单测不能冒充并发验证。第 8 节的部署与一致性缺口继续成立。

## 10. Engineering Lessons — 哪些判断值得复用？

1. **派生索引要有明确权威源和失效责任。** 能重算只是恢复条件；还必须知道谁发通知、谁在何时执行重算。
2. **共享缓存的 key 必须覆盖数据源身份。** class-level lifetime 与 instance-level dependency 不会天然一致；构造函数可注入并不自动提供缓存隔离。
3. **延迟工作是成本转移。** lazy rebuild 减轻写路径，却让首次读承担延迟和峰值内存，评估时要同时看两条路径。
4. **局部构建保护异常路径，不自动提供并发原子性。** 检查两张表的发布顺序和 dirty 清除时机，比只看最终结果更能暴露边界。
5. **确定性规则有利于建立契约，但不能证明检索质量。** exact examples 保护 key/分母，评测集才回答不同算法谁更适合语料。
6. **分数是组件间协议。** 范围、缺失分支与语义要明确；归一化不等于概率校准，更不等于融合参数最优。
7. **可重建缓存与 durable commit 应分开判断。** 后续恢复契约显示，缓存维护失败不应抹掉已持久化成功；这条教训的后续证据不能追记到原收官。
8. **未来方案需要触发条件。** 先定位规则、重建、内存或通知哪一层失效，再选择排名算法、索引表示或部署机制；成熟技术名称本身不是迁移理由。

## 11. Engineering Self-Review — 我能论证这些取舍吗？

1. 为什么关键词索引可以不独立持久化？新增一份 durable lexical state 会增加哪些同步责任？
2. lazy rebuild 节省了哪条路径的工作，又让谁承担成本？如何观测这种转移是否还能接受？
3. class-level cache 与 instance-level VectorStore 的生命周期不一致，为什么可能静默返回错数据？
4. 为什么本地单进程前提不能证明并发安全？要增加哪些交错证据才敢给出更强承诺？
5. local-build-then-publish 能防住哪种失败，为什么防不住双表跨版本观察？
6. 什么语料或测量结果足以推动替换 bigram、coverage 或 full rebuild？哪些改动要求索引一起迁移？
7. corpus 扩大 100 倍时，应该先看哪些指标？为何不能直接承诺改用 Elasticsearch 就解决问题？
8. normalized keyword score 为融合提供什么，仍缺什么？为什么 0.3/0.7 不能被称为实验最优？
9. 原始 Mock lifecycle、patched composition、后续 REAL API E2E 各能支撑哪个结论，不能互相替代什么？
10. 持久化提交成功但缓存维护失败时，怎样定义用户可见结果与后续恢复？这一判断在项目历史上何时获得补证？

## Appendix A — Implementation / Task Traceability

| Engineering concept | 当前实现位置 | 工程坐标 |
|---|---|---|
| shared normalization / deterministic tokens | [qa.py](../../../backend/app/services/qa.py)：patterns、`tokenize()` | T0601；ADR-01～05 |
| 状态所有权、双表和 build/search | [qa.py](../../../backend/app/services/qa.py)：`KeywordRetriever` | T0602，依赖 T0601 / T0108；ADR-06～10 |
| public chunk source | [vector_store.py](../../../backend/app/core/vector_store.py)：`VectorStore.list_chunks()`、`ChunkRecord` | T0108；F008 public-interface boundary |
| mutation 与共享状态接缝 | [keyword_index.py](../../../backend/app/services/keyword_index.py)：`invalidate_keyword_index()` | T0602 接入；后续 post-commit recovery |
| 上传、重命名、删除调用点 | [upload.py](../../../backend/app/api/upload.py)、[collections.py](../../../backend/app/api/collections.py)、[files.py](../../../backend/app/api/files.py) | T0502、T0402/T0403、T0903 |
| 原始契约单测 | [test_qa.py](../../../backend/tests/test_qa.py)：`TokenizeTests`、`KeywordRetrieverTests` | 原 6+7 methods；第 9 节明确边界 |
| 下游检索组合 | [qa.py](../../../backend/app/services/qa.py)：`VectorRetriever` / `HybridRetriever` / `retrieve()` | T0701 / T0702 / T0703 |
| 下游问答与请求契约 | [qa.py](../../../backend/app/services/qa.py)：`QAService`；[query.py](../../../backend/app/api/query.py)：`_parse_query_request()` / `query()` | T0804 / T0805；不归原 Phase 6 scope |

阅读分工保留：逐步代码与自测见 [Phase 6 Technical Learning](../phase-06-keyword-retrieval.md)；语法类比见 [Python / TS 映射](../python-for-frontend-dev.md)；项目级面试资产见 [Interview Guide](../interview-notes/dx-rag-interview-guide.md)。Phase Learning Review 已把 T0601/T0602 candidates 筛选、去重并晋升到 Phase 6 深度章，本文不复制话术。

## Appendix B — SPEC / AC / Gate / Evidence References

[F009](../../SPEC.md#f009-keyword-retrieval) 的 tokenization、index structure、public data source、lifecycle、score 与返回契约对应 [TASKS 的 T0601/T0602](../../TASKS.md#t0601--query-tokenizer)。F008 的 private API 隔离支持存储依赖边界；后续 F010/F011 约束向量与融合。当前 F009/T0602 另含 post-commit invalidation failure recovery，历史差异见附录 C。

**原始覆盖与状态记录：**Coverage 为 T0601 + T0602；原 Status 为 **COMPLETE（2026-08-27）**，指 T0601/T0602 实现、PHASE_6_PASS Gate 与 Phase Learning Review 已完成。本次结构细化不改变这些状态。

下方是原文件内嵌的 Gate Review，**全文保留，未重审、未改写**。保留原编号和标题以维持既有链接；其中“当前”“本次”“第 8 节”均属于原 2026-08-27 记录语境，旧 Known Gaps 与时点差异在附录 C 说明。这里记录的是当时验收，不是本次 Engineering Review 新发出的 PASS/FAIL。

## 10. Phase 6 Gate Review（2026-08-27）

### 10.1 Verdict

**PHASE_6_PASS**。T0601/T0602 的实现与冻结 SPEC F009 一致，没有发现阻断 Phase 6 收口的问题；允许进入 Phase Learning Review，但本次不启动 Phase 7。

### 10.2 Gate evidence

| Gate item | Result | Evidence |
|---|---|---|
| T0601 exact tokenizer contract | PASS | SPEC 三组示例、lowercase、单字符过滤、segment boundary、stable dedup 均由 `TokenizeTests` 覆盖 |
| T0602 public-interface index build | PASS | `KeywordRetriever._build_index()` 只调用 `VectorStore.list_chunks()`，未访问 Chroma private object |
| Lazy build + dirty/full rebuild | PASS | 首次查询只构建一次；shared invalidation seam 标脏；下一次查询重新读取全量 chunks |
| Score / sort / top-k | PASS | AC-F009-01=1.0、AC-F009-02=[]、AC-F009-03=0.6、AC-F009-04=1.0，降序与 top-k 有独立测试 |
| Mutation integration seam | PASS（代码路径 + unit lifecycle） | upload、rename、delete 的既有调用点均进入 `invalidate_keyword_index()`；真实 HTTP/Chroma E2E 仍按计划留给 Phase 12/T1202 |
| Focused test | PASS | `python -m unittest tests.test_qa -v` → 13/13 |
| Discovered regression suite | PASS | `python -m unittest discover -s tests -v` → 13/13（当前仓库 tests 仅此 suite） |
| Syntax/import compilation | PASS | `python -m compileall -q app tests` |
| Diff hygiene | PASS | `git diff --check` 无 whitespace error；未修改冻结的 `docs/SPEC.md`，未引入 dependency 或 Phase 7 代码 |

> **记录澄清（Learning Pass 补记，2026-08-27）**：上表 Diff hygiene 行的「未修改 `docs/SPEC.md`」指 T0601/T0602 的实现 diff。当日另有一次独立提交 `33e0bdb`（15:05，Gate Review 之前）修正了冻结 SPEC F009「Python机器学习」示例的笔误（6 tokens → 4 tokens，与 TASKS.md 同步）——属示例勘误，不是实现改动；Gate 的 `git diff --check` 针对实现工作树，结论不受影响。

`black` 与 `ruff` 不在当前环境/requirements 中，因此对应检查记为 **NOT AVAILABLE**，不作为 Gate failure；本次没有为审查新增依赖。

### 10.3 Acceptance decision

- **AC-F009-01 — PASS**：中文 bigram 全命中，score = 1.0。
- **AC-F009-02 — PASS**：无 token 命中返回空列表。
- **AC-F009-03 — PASS**：3/5 unique query tokens 命中，score = 0.6。
- **AC-F009-04 — PASS**：中英混合 query 的 `python` / `编程` 均命中，score = 1.0。
- **AC-F009-05 — PASS（Phase 6 scope）**：已建索引经 shared seam 标脏后，下一次 search 全量重建并检索到新增 chunk。真实 upload HTTP → ChromaDB → query 的字面 E2E 未宣称通过，继续归 Phase 12/T1202。

### 10.4 Non-blocking findings

第 8 节的多进程 invalidation、并发锁、同分 tie-break、基本 CJK 范围、benchmark 与 module docstring 债务均不违反 v1 F009 或当前 Task Completion Conditions，维持 Known Gaps / Future 状态。Gate 不把这些改写成已实现能力，也不以“顺手优化”扩大 Phase 6 scope。

## Appendix C — Historical Notes

### C.1 旧判断如何映射到当前事实？

原文的工程结论、架构影响和 Known Gaps 随后续阶段追加过状态。以下保留旧结论的适用时点，避免“已经实现”和“当时验证”混淆。

| 历史记录 | 当时含义 | 当前解释 / 去向 |
|---|---|---|
| unit-level 行为闭环，真实 upload-to-query 仍待 Phase 12 | 13 methods 不能证明真实 Chroma/HTTP/provider | 原记录保持；第 9 节分别列出后续指定链路补证，不整批升级 |
| Known Gap #1：literal upload/rename/delete → invalidate → real Chroma rebuild → query E2E 未覆盖 | Phase 6 没有完整 mutation E2E | 上传重建、文件删除等后续证据按各自范围引用；不声称全链所有场景皆由旧测试覆盖 |
| Known Gaps #2～5：store namespace、多 worker、无锁并发、tie-break | 原 Gate 接受的 non-blocking 限制 | 仍在第 6～8 节；后续 API E2E 不关闭这些风险 |
| Known Gap #6：qa.py / test_qa.py docstring 仍只写 tokenization/T0601 | 当时文案落后于新增 retriever 职责 | 当前分别为 “Keyword and vector retrieval services.” / “Tests for the retrieval services.”；旧文案债已变化，qa.py 职责扩大风险仍保留 |
| Known Gap #7：基本 CJK；无 corpus benchmark / property-based / Unicode 全域测试 | 字符支持与证据有限 | 范围和测量缺口仍在，未升级为全域支持 |
| QA API、top_k/request validation 属于未来边界 | 原检索器不拥有 HTTP 校验 | 当前 query adapter 校验非空 question 与 top_k 类型/范围；class 仍不校验，当前请求未设 question 最大长度 |
| 10x/100x/1000x 压力分析 | 线性扫描、重建、内存架构的定性推演 | 保留为第 7 节触发分析，不写作实测容量 |

**Pending #34 的原裁决保留：**Phase 4 ER 曾问“invalidate 失败 → RENAME_FAILED 映射是否成立”。原评审在 T0602 落地后判断：`invalidate()` 是 in-memory 标脏（`set.add`），当前实现没有业务失败路径；契约第四要素“真失败 raise”保持防御性条款，RENAME_FAILED 映射在当时 in-memory 实现下不可达，与调用方补偿逻辑无冲突。

**后续变化单列：**当前 `invalidate()` 委托 `mark_dirty()`，seam 捕获正常 invalidate 抛出的 Exception 后强制标脏、记录异常；当前 SPEC/TASKS 明确持久化上传/删除提交后的缓存恢复契约。后续 V11 对此做了故障注入回归。旧裁决只说明当时普通标记逻辑，不意味着运行环境不可能异常，也不能覆盖后来的维护契约。

### C.2 原有后续 checkpoints（原文保留）

以下“尚未”“不启动”“仍待”均以段内日期为准。当前后续 QA/真实验证状态见第 9 节，不回写这几段历史。

> **T0602 review boundary**: 本评审覆盖 Phase 6 implementation；不启动 Phase 7，不把 unit tests 写成 E2E PASS。

> **后续状态（T0701 Learning Pass，2026-08-28）**：上面的“不启动 Phase 7”是 2026-08-27 Phase 6 review checkpoint。之后 T0701 已实现 `VectorRetriever`，把 query embedding 接到 `VectorStore.search()` 并透传 `vector_score`；详见 [Phase 7 Technical Learning](../phase-07-vector-retrieval.md) 与 [Phase 7 Engineering Review](./phase-07-engineering-review.md)。
>
> **后续状态（T0702 Learning Pass，2026-08-31）**：T0702 已在 `qa.py` 中按 `chunk_id` 完成 0.3/0.7 weighted fusion、relevance filter 与最终 Top-K，并以 unit tests 验证 service-level behavior。当时 T0703 unified wiring、真实 upload → ChromaDB → query E2E 与 QA API 仍未实现；本 Phase 6 review 的历史 Gate 结论不因此被改写。
>
> **后续状态（T0703 Learning Pass，2026-08-31）**：T0703 已在 `qa.py` 提供 `retrieve(query, collection, top_k)` facade。它在边界处创建 concrete `ChromaVectorStore`，对空 collection 返回 `[]`，非空时把同一 store 注入 Keyword/Vector/Hybrid retrievers；missing collection 的异常不被吞掉。3 个 facade tests 验证的是 patched composition/propagation boundary，而非真实 Chroma lifecycle 或 upload → query E2E。Phase 6 的 Gate/Learning Review 历史结论保持不变；QA API、context/LLM 与真实集成仍待后续 Phase。

### C.3 本次结构细化的保留范围

原十条 ADR 的核心设计、理由、代价保持；原架构/维护性/一致性/错误/安全/规模分析归入第 4、6～8 节；原测试行为、精确命令、工具 NOT AVAILABLE、AC 与 Gate 勘误全部保留在第 9 节和附录 B；原 Known Gaps 八项在第 8 节及 C.1 可追溯；原后续 checkpoints 保留于 C.2。

机制教学只保留支撑判断所需上下文，分词窗口、数据结构逐步讲解和 Python 语法继续引用 Technical Learning。未有意删除有意义的工程结论；未新增 benchmark、生产事故或 Gate 裁决；后续证据独立标记，不能当作 Phase 6 收官时已知。
