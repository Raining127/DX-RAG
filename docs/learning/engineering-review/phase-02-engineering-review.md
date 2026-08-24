# Phase 2 Engineering Review — Embedding Service

> 配套学习笔记：[phase-02-embedding.md](../phase-02-embedding.md)（Lazy Singleton 逐行精读、Python 新知识清单）
> 本文档定位：**工程决策复盘**。所有结论基于真实代码（`backend/app/services/embedding.py`，77 行）与 SPEC F007。
> 诚实状态声明：T0201–T0202 全部 DONE。Phase 2 是全部 Phase 中代码量最小的模块之一（77 行）——但它是**质量与性能的隐形开关**：模型加载策略选错，每次请求都变成灾难。

---

## 1. Phase 定位

| 维度 | 内容 |
|------|------|
| **业务目标** | 把自然语言文本变成"机器可比较"的向量——RAG 的"理解语义"能力来源 |
| **技术目标** | 用最小代码实现 SPEC F007 的两个契约：Lazy Singleton 模型加载策略 + `encode_chunks` 批量编码（384 维、L2 归一化） |
| **系统位置** | AI/Data Layer 的"编码器"。上游只依赖 Phase 0（config 的 `EMBED_MODEL`、errors 的 `EMBEDDING_MODEL_ERROR` 错误码） |
| **上游依赖** | Phase 0：`settings.EMBED_MODEL`（默认 `models/bge-small-zh-v1.5` 本地路径）、`AppError("EMBEDDING_MODEL_ERROR")` → HTTP 500 |
| **下游消费者** | Phase 3 Ingest（`IngestService.process` 的 embed 步骤 —— **已实际发生**）、Phase 7 VectorRetriever（T0701 将用 `encode_chunks` 编码 query —— Future）、Phase 1 VectorStore（`add_texts`/`search` 的向量参数终于有真实来源） |

**一句话**：Phase 2 是 Phase 1 的"上游供应商"——VectorStore 契约里的向量参数（`List[List[float]]`），第一次有了真实的生产者。

---

## 2. 为什么需要这个模块？

**没有 Embedding Service，系统会卡死在哪：**

1. **VectorStore 收不到合法输入**：Phase 1 的 `add_texts(embeddings=...)` 要求 384 维向量——没有编码器，Ingest 管道在 Chunk 之后无路可走，`search()` 的 query_embedding 也无从产生。
2. **没有语义检索**：RAG 区别于普通搜索的核心就是"语义相似"而非"字符串相等"。Embedding 模型是语义的翻译官——"AI 的子领域"与"机器学习是人工智能的分支"字面零重合，但向量距离极近。
3. **每个调用方各自加载模型会出大事故**：bge-small-zh-v1.5 约 100MB、加载需数秒、推理占内存——如果每次请求都 `SentenceTransformer(...)`，服务直接不可用。

特别地，**SPEC F007 强制了加载策略**（Lazy + Singleton + 失败即 500）——这不是"最佳实践建议"，而是写进 SPEC 的硬约束。原因有二：① 服务启动快（健康检查不被模型加载拖累）；② 进程内只存在一份模型（内存有界）。

---

## 3. 核心设计决策

### 决策 1：Lazy Loading —— 模型永远不在服务启动时加载

**Decision**: 模型在**第一次调用** `get_model()` 时才加载；应用启动（FastAPI import + uvicorn 启动）完全不触碰 sentence-transformers。

**Context**: SPEC F007 Model Loading Strategy 第一条："Lazy load on FIRST use (never at application startup)"。模型文件约 100MB 级，加载耗时数秒。

**Problem**: 若在模块 import 或应用启动时加载模型：① 服务启动时间被拖长数秒——健康检查、前端的连通性探测全部变慢；② 模型路径缺失/损坏时，**整个应用启动失败**——连 `/api/health` 都不可用，运维无法区分"服务挂了"和"模型坏了"；③ 纯管理操作（Phase 4 KB 管理、Phase 9 文件删除）根本不需要 embedding，启动时加载纯属浪费。

**Chosen Solution**: 模块 import 零副作用；`get_model()` 内做运行时 import + 构造。加载失败不是启动失败，而是**首次使用时**的 `AppError("EMBEDDING_MODEL_ERROR")` → HTTP 500。

**Why**: ① **失败域隔离**：服务可用性与模型可用性解耦——服务能起来、能报告健康，模型问题只在需要它的路径上暴露；② 惰性哲学与前端 lazy import 一致（类比 TypeScript：`React.lazy` / dynamic `import()`——首屏不加载用不到的重模块）；③ SPEC 是这么要求的——这是本项目"契约先行"的又一例。

**Trade-off**: **首个请求背锅**：第一个触发 embedding 的请求要等数秒模型加载——用户体验上有一个"首次慢"。v1 无预热机制，这是 SPEC 接受的代价（用户量小、本地部署）。

**Future Improvement**（Future / Not implemented in v1）: 启动后台预热（warm-up）+ 就绪探针（readiness probe 与 liveness probe 分离）；模型服务化后加载成本转移到独立服务。

---

### 决策 2：进程级单例 —— 模块级 `_model` 缓存 + `global`

**Decision**: `_model: Optional["SentenceTransformer"] = None` 模块级变量缓存实例；`get_model()` 用 `global _model` + `if _model is None` 保证整个进程只有一份模型。

**Context**: SPEC F007："Cache the loaded model as a process-level singleton; subsequent calls reuse the cached instance — never reload per request"。

**Problem**: 模型实例是重资源（数百 MB 内存 + 推理时的内部状态）。若每次请求都加载：内存泄漏式增长 + 每次数秒加载延迟 + 并发请求时 N 份模型吃光内存。FastAPI 是异步框架，多请求并发下尤其危险。

**Chosen Solution**: 模块级变量（Python 模块在进程中天然只 import 一次，模块级变量 = 进程级单例的最简实现）+ `global` 声明写回。不引入线程锁。

**Why**: ① **Python 惯用法**：模块级变量是 Python 生态公认的单例模式（比 `functools.lru_cache`、类单例更直白）；② **零依赖**：不需要额外的单例框架/装饰器；③ SPEC F007 明确点名 "process-level singleton"。类比 TypeScript：模块级 `let instance: Model | null` + `getInstance()`——同样的模式跨语言成立。

**Trade-off**: ① **非线程安全的最坏情况**：两个线程同时首次调用 `get_model()`，可能都通过 `if _model is None` 并各自构造一次——后写覆盖先写，浪费一次加载但结果正确。**GIL 使 Python 字节码交替执行，但构造模型是长时间操作，确实存在竞态**。v1 下 Ingest 是同步路径且实际触发点在请求处理器中，FastAPI sync endpoint 走线程池，理论上有竞态窗口。② 单例 = 全局可变状态——测试时难以重置（`get_model` 无 reset 接口）。

**Future Improvement**（Future / Not implemented in v1）: 加 `threading.Lock` 双检锁消除竞态；或模型服务化（单例问题在独立服务中自然消失）。

---

### 决策 3：函数内 import + TYPE_CHECKING —— 模块导入永不失败

**Decision**: `sentence_transformers` 的真实 import 放在 `get_model()` 函数体**内部**；模块顶部用 `if TYPE_CHECKING: from sentence_transformers import SentenceTransformer` 只为类型检查器服务。

**Context**: 真实代码 [embedding.py:23-24](../../backend/app/services/embedding.py#L23-L24) 与 [embedding.py:50](..%2F..%2Fbackend%2Fapp%2Fservices%2Fembedding.py#L50)。SPEC F007 要求加载失败必须在"首次使用时"暴露。

**Problem**: 若顶部直接 `from sentence_transformers import SentenceTransformer`：① 该包未安装时，import `app.services.embedding` 直接抛 `ModuleNotFoundError`——**整个应用起不来**（embedding 被 Ingest import，Ingest 被 router import……级联爆炸）；② import 大包会拖慢模块导入链。

**Chosen Solution**: 运行时 import 收进函数；类型注解用 `"SentenceTransformer"` 字符串 + `TYPE_CHECKING` 块。`TYPE_CHECKING` 是 Python 标准库常量——运行时永远为 `False`，块内代码只有 mypy/pyright 等类型检查器"看到"。

**Why**: ① **失败域隔离**（与决策 1 配套）：import 失败被限制在 `get_model()` 的 `try/except` 内，转成语义化错误码；② **导入速度**：模块级 import 零重依赖；③ **类型安全不丢**：IDE 和类型检查器仍能获得 `SentenceTransformer` 的完整类型信息。类比 TypeScript：`import type { SentenceTransformer }` ——**编译期存在、运行期消失**，两种语言惊人一致。

**Trade-off**: ① 函数内 import 每次调用有微小的 import 开销（Python 会缓存已 import 模块，实际只查一次 sys.modules，开销可忽略）；② 读代码时"顶部看不到依赖"——需要看函数体才知道模块依赖什么。

**Future Improvement**（Future / Not implemented in v1）: 若依赖管理走向可选依赖（extras），可把 sentence-transformers 放进 `pip install dxrag[embedding]`，用 importlib 探测可用性。

---

### 决策 4：L2 归一化（normalize_embeddings=True）—— 与 Phase 1 cosine 度量的隐形耦合

**Decision**: `encode(chunks, normalize_embeddings=True)` —— 模型侧直接产出 L2 归一化向量（模长 = 1）。

**Context**: 真实代码 [embedding.py:77](../../backend/app/services/embedding.py#L77)。SPEC F007 明确写出该参数。Phase 1 决策 7 选定了 cosine 度量（`hnsw:space: cosine`）。

**Problem**: 余弦相似度只看方向。若不归一化：向量模长随文本长度变化，"AI"（短文本）与"人工智能是计算机科学的一个分支"（长文本）即使方向相近，在 **L2 距离**下也可能很远。Phase 1 用的是 cosine 空间，本无此问题——但归一化带来额外好处。

**Chosen Solution**: 模型 encode 时直接归一化（sentence-transformers 内置参数，零额外代码）。

**Why**: ① **数值稳定性**：归一化向量幅值有界，HNSW 索引构建更稳定；② **为度量迁移留余地**：归一化后，cosine 距离与欧氏距离（L2）单调等价——若未来换 L2 度量，向量不用重算；③ **融合分数可比**：向量内部一致性让 `similarity_score = clamp(1 - distance)` 的近似映射更稳定（Phase 1 决策 3）；④ 语义上"方向比长度重要"——文本长度不应影响语义相似度。类比：把向量视为"语义方向指针"，长度统一为 1，只比较指向。

**Trade-off**: ① 归一化是模型内部的额外计算（可忽略）；② 向量幅值信息被丢弃——若未来想做"置信度加权"（用模长表示可信度），此设计不支持。

**Future Improvement**（Future / Not implemented in v1）: 换用更大模型或需要幅值语义时，归一化决策需重新评估。

---

### 决策 5：`raise AppError(...) from exc` —— 异常链不断裂

**Decision**: 模型加载失败时 `raise AppError("EMBEDDING_MODEL_ERROR") from exc`——抛出自定义业务异常，同时用 `from exc` 保留原始异常的 `__cause__` 链。

**Context**: 真实代码 [embedding.py:54](..%2F..%2Fbackend%2Fapp%2Fservices%2Fembedding.py#L54)。Phase 0 的错误体系：`AppError` 携带错误码，全局 handler 转成 `{error: {code, message, details}}`。

**Problem**: 加载失败的具体原因五花八门：路径不存在（`FileNotFoundError`）、模型文件损坏（`OSError`）、内存不足（`MemoryError`）、包未安装（`ModuleNotFoundError`）。若只抛 `AppError`：上层能返回 500 错误码，但**日志里丢失了根因**；若只抛原始异常：全局 handler 只能返回无差别的 `INTERNAL_ERROR`，错误码体系被绕过。

**Chosen Solution**: `AppError` 是**对外契约**（错误码 + HTTP 状态 + 中文消息），`from exc` 是**对内真相**（traceback 里能一路追到根因）。`except Exception as exc` 的宽捕获在此处是**故意的**——SPEC F007 规定"ANY load failure → EMBEDDING_MODEL_ERROR"，不需要区分具体异常类型。

**Why**: ① **异常链是 Python 的调试命脉**：`raise X from Y` 让 traceback 同时显示 X 和 Y，排查"为什么模型加载失败"时不丢现场；② 宽捕获是契约要求：SPEC 把"路径缺失、文件损坏、OOM"统一成一个错误码，上层（Ingest）不需要知道模型是怎么坏的，只需要知道"embedding 不可用，本次 ingestion 失败"；③ 与 Phase 0 的 catch-all handler 形成两层防线：业务异常走 AppError handler，意外异常走 500 handler。

**Trade-off**: 宽捕获可能吞掉程序员错误（如拼错变量名）——但这类错误也会在 traceback 中保留（`from exc`），且范围被限定在加载路径。

**Future Improvement**（Future / Not implemented in v1）: 错误码细分（MODEL_NOT_FOUND / MODEL_CORRUPTED / OOM 各自成码）——SPEC 冻结为单码，未来需 SPEC 决策。

---

### 决策 6：空输入 → 空列表（不是错误）

**Decision**: `encode_chunks([])` 返回 `[]`，不报错、不加载模型（`if not chunks: return []` 在 `get_model()` 之前）。

**Context**: 真实代码 [embedding.py:75-76](..%2F..%2Fbackend%2Fapp%2Fservices%2Fembedding.py#L75-L76)。SPEC F007 错误表："Empty chunks → empty list (not an error)"。

**Problem**: 若空输入触发模型加载甚至报错：调用方必须自己先判空——契约变成"调用方责任"，每个调用方都可能漏判。而且"零个 chunk 需要编码"本身是合法语义（虽然 Ingest 管道实际会在 chunk 为空时更早失败——见 Phase 3 三态模型），数学上空集的编码就是空集。

**Chosen Solution**: 显式短路：空输入直接 `[]`，**连模型都不加载**（性能 + 语义双赢）。函数只对非空输入承担"可能需要加载模型"的代价。

**Why**: ① **契约自洽**："N 个输入 → N 个输出"对 N=0 天然成立；② **零成本路径**：空输入不触发最贵的操作（模型加载），符合惰性原则；③ 调用方零心智负担。类比 TypeScript：`Array.map` 对空数组返回空数组——**同构（structure-preserving）语义**。

**Trade-off**: 空输入被静默接受——若调用方 bug 导致意外空列表，问题会流向下一环（如 `add_texts` 收到空 embeddings）。v1 中 Ingest 在 chunk 阶段已保证非空才到 embed 步骤。

**Future Improvement**（Future / Not implemented in v1）: 无——此契约稳定，无需演进。

---

### 决策 7：本地模型路径 + `.tolist()` 可序列化 —— 离线部署与存储适配

**Decision**: ① `EMBED_MODEL` 默认值是**本地路径** `models/bge-small-zh-v1.5`（模型文件随项目部署），不是 HuggingFace 模型名；② `encode()` 返回的 numpy 数组经 `.tolist()` 转成纯 Python `List[float]` 后才离开模块。

**Context**: 真实代码 [config.py:38](..%2F..%2Fbackend%2Fapp%2Fcore%2Fconfig.py#L38) 与 [embedding.py:77](..%2F..%2Fbackend%2Fapp%2Fservices%2Fembedding.py#L77)。

**Problem A（为何本地路径）**: 若配置 HF 模型名（如 `BAAI/bge-small-zh-v1.5`），sentence-transformers 首次运行时**联网下载**——内网/离线部署场景直接失败，且首次使用延迟不可控（下载 100MB）。DX-RAG 的目标是企业内网知识库（SPEC 部署假设），离线是硬需求。

**Problem B（为何 tolist）**: `model.encode()` 返回 numpy 数组（`numpy.ndarray`）。Phase 1 的 `ChromaVectorStore.add_texts(embeddings=...)` 把它们塞进 ChromaDB——numpy 标量不是原生 JSON 类型，ChromaDB 序列化/反序列化时会出错或变成奇怪类型（`numpy.float32` 无法 JSON 序列化）。

**Chosen Solution**: ① 模型文件放 `models/` 目录随仓库/部署包分发，配置项指向本地路径；② 模块边界处 `.tolist()`——离开 embedding 模块的数据全是标准 Python 类型。

**Why**: ① **部署确定性**：模型版本与代码版本绑定（模型文件入库/入包），不依赖外部网络与 HF Hub 状态；② **序列化安全**：边界处类型归一化是数据契约的一部分——下游（VectorStore、ChromaDB）永远收到 `List[float]`；③ 性能无损失：`.tolist()` 是 O(384×N) 的内存拷贝，相比模型推理可忽略。

**Trade-off**: ① 模型文件使仓库/部署包变大（100MB+），需 git-lfs 或独立存储；② 模型升级 = 重新分发文件，而非改一行配置；③ `.tolist()` 产生一次性内存峰值（384 维 × 全量 chunk 数的 Python float 列表）。

**Future Improvement**（Future / Not implemented in v1）: 大批量编码时分批（batching）以控制内存峰值；模型版本化管理（模型文件 + 版本元数据）。

---

## 4. 架构影响

Phase 2 完成后，系统新增的能力与依赖关系：

| 新增能力 | 谁开始依赖它 | 未来 Phase 谁使用 |
|---------|------------|-----------------|
| `get_model()`（进程级 bge 单例） | `encode_chunks` 内部 | 无外部调用者（有意为之） |
| `encode_chunks()`（384 维 L2 归一化向量批量生成） | Phase 3 Ingest（`IngestService.process` 的 embed 步骤 —— **已实际发生**） | Phase 7 VectorRetriever（T0701 query 编码 —— Future） |
| 向量契约兑现：`List[List[float]]` | Phase 1 VectorStore 的 `add_texts`/`search` 参数第一次有真实生产者 | Phase 7（检索侧的兑现时刻） |
| 加载失败语义：`EMBEDDING_MODEL_ERROR` → 500 | Phase 3（Ingest 直接让该异常传播 → ingestion FAILED —— **已实际发生**） | Phase 5 Upload API（500 错误响应） |

**关键洞察**：Phase 2 的契约设计有两条"隐藏消费者链"：① **与 Phase 1 的向量维度耦合**——bge-small-zh-v1.5 固定 384 维，ChromaDB collection 中所有向量必须同维；若换模型，已入库向量全部作废或需重算（v1 无模型版本管理，这是"换模型 = 重建库"的隐性代价）；② **与 Phase 1 的度量耦合**（决策 4）——L2 归一化 + cosine 是配套设计，改任何一边都要同步想另一边。

---

## 5. 工程问题分析

### 可维护性

- ✅ 77 行极小模块，每个决策都有 SPEC F007 条款背书（docstring 顶部直接引用 SPEC 三条契约）
- ✅ `get_model()` 的 docstring 解释了"为什么 import 在函数内"——设计意图随代码留存
- ⚠️ 模块级可变全局状态（`_model`）没有 reset 机制——单元测试想测"加载失败"路径时难以构造（需 mock import 或临时删除模型文件）
- ⚠️ 宽泛的 `except Exception` 让静态分析工具（如 pylint broad-except）报警——需依赖注释/文档说明这是 SPEC 契约

### 扩展性

- ✅ 模块接口极小（`get_model` + `encode_chunks`），未来换模型服务只需改这两个函数内部
- ✅ 模型名来自配置（`settings.EMBED_MODEL`），换模型零代码改动（但见架构影响的维度耦合警告）
- ⚠️ 单模型假设硬编码在接口中：未来多模型（不同语言的 embedding 模型）需改接口签名——SPEC v1 单模型，冻结

### 数据一致性

- ✅ 进程内唯一模型实例 → 所有向量由同一模型产生 → **同一向量空间的严格保证**（不会出现"老请求用 v1 模型、新请求用 v2 模型"的混合空间——当然代价是模型热更新做不到）
- ✅ 空输入契约与 Ingest 管道状态模型兼容（FAILED 在 chunk 阶段触发，embed 不会收到空列表——两道防线）
- ⚠️ 模型文件与代码的版本绑定是**部署期**约束而非**运行期**校验：代码不校验模型文件的版本/完整性——文件损坏要到首次加载才暴露（500），不提供"模型指纹"检查

### 错误处理

- ✅ 加载失败 → 语义化 `EMBEDDING_MODEL_ERROR` + 异常链保留根因（决策 5）
- ✅ 空输入 → 空列表（决策 6），无错误路径
- ⚠️ **encode 阶段的运行时错误未单独处理**：`get_model()` 成功后，`encode()` 本身的 OOM/异常会以原始异常形态抛出 → Phase 0 的 catch-all handler 返回 500 `INTERNAL_ERROR`，错误码失去粒度（不报 EMBEDDING_MODEL_ERROR）。**SPEC F007 只契约了加载失败**，编码失败走通用 500——契约覆盖边界到此为止

### 性能

- ✅ 单例模型 + GPU/CPU 推理：批量编码 N 个 chunk 一次推理完成（sentence-transformers 内部 batch 处理），比逐条 encode 快一个数量级
- ✅ 惰性加载：管理类请求（KB CRUD、文件删除）零模型开销
- ⚠️ **首次请求冷启动**：第一个触发 embedding 的请求要等模型加载（数秒级）——v1 无预热
- ⚠️ **无显式 batch 大小控制**：`encode_chunks` 一次编码**文件全量 chunks**（Ingest 调用方传入全部）——大文件（万级 chunk）时 GPU/内存峰值不可控。SPEC 未要求 batching，v1 文件规模下可接受
- ⚠️ CPU 推理默认路径：本地部署无 GPU 时，384 维小模型 CPU 推理可接受，但批量大时延迟线性增长

### 安全

- ✅ 本地模型路径 → 无运行时联网下载 → 无供应链/网络注入风险（对比：HF 模型名在运行时拉取是供应链风险点）
- ✅ API key 无关：embedding 不涉及外部 API（DeepSeek/DashScope 的 key 与本模块无关）
- ⚠️ `models/` 目录含第三方模型文件（二进制），其完整性依赖部署方校验——代码层无签名/哈希验证
- ⚠️ 模型文件本身是潜在攻击面（恶意 pickle 的已知历史风险——safetensors 格式是缓解手段，本模块未显式检查格式）

---

## 6. 如果规模扩大怎么办？

> 本节所有方案均为 **Future / Not implemented in v1** 分析。SPEC NFR 11.2：v1 单机、万级 document。

### 10× 规模（文档量 ×10，如 embedding 调用频率上升一个量级）

**可能出现的瓶颈**：

- 首次加载延迟被高频触发：进程重启后第一个请求慢（每次部署都要"暖一次"）
- 单文件全量 chunks 一次 encode 的内存峰值（决策 7 Trade-off）
- CPU 推理吞吐：批量任务多时排队

**优化方向**（Not implemented in v1）：

- 启动预热 + readiness probe（服务"就绪"包含"模型已加载"）
- 显式 batch 大小上限：`encode_chunks` 内部按固定 batch（如 32/64）分批编码，控制峰值内存
- 推理设备可配置（`EMBED_DEVICE=cuda`），模型放 GPU

### 100× 规模（文档量 ×100，如 SaaS 化、并发 embedding 请求）

**可能出现的瓶颈**：

- **单机单模型成为热点**：所有 embedding 请求共享一个模型实例——GPU 利用率高但延迟抖动，CPU 则吞吐见顶
- 模型常驻内存（约 300-500MB 运行时）与向量库、倒排索引抢内存——单机内存总量成为上限
- 进程级单例的跨进程问题：若横向扩展多个 uvicorn worker，**每个进程各加载一份模型**——N 个 worker = N× 模型内存

**优化方向**（Not implemented in v1）：

- **模型服务化**：embedding 抽成独立服务（如 TEI / sentence-transformers + FastAPI 微服务，或 Triton）——worker 进程通过 HTTP/gRPC 调用，内存单份、可独立扩缩容
- 模型量化（int8）减小内存与推理时间
- 多 worker 场景：先量化 + 模型服务化，否则 `workers=4` 直接 4 份模型内存

### 1000× 规模（SaaS 化，亿级 chunk、高并发）

**可能出现的瓶颈**：

- 单模型服务吞吐上限：384 维小模型单卡数千 QPS 是上限，亿级 chunk 的批量任务需要集群
- 模型与向量库的维度强耦合放大：换更大模型（更高质量）需要全量重算 + 全库重建——亿级规模下这是天价迁移
- 无 embedding 缓存：相同/相似文本重复编码浪费算力

**优化方向**（Not implemented in v1）：

- **分布式模型服务 + GPU 集群**：embedding 服务多副本 + 负载均衡，任务队列削峰
- **Embedding 缓存层**：按文本哈希缓存向量（Redis），重复文档（版本重传）零重算
- **多模型架构**：轻量模型做初筛、大模型精排（rerank 模型）——注意：v1 明确无 reranker（CLAUDE.md Retrieval Invariants），这是规模演进路径而非 v1 路线
- **模型迁移的版本化方案**：metadata 记录 `embedding_model_version`，支持渐进式重建（新文档用新模型，旧文档后台重算）——需要 SPEC 级决策

**核心判断**：Phase 2 的 77 行代码把"模型与代码的边界"放在了正确的位置——**模型是可替换资源，契约是稳定接口**。规模扩大时的正确动作不是改代码结构，而是把资源（模型）从进程内搬出去。`encode_chunks` 的签名（文本进、向量出）在本地单例和远程模型服务两种实现下完全不变——这是本模块最重要的规模耐受力。
