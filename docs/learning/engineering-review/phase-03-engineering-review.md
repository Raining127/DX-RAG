# Phase 3 Engineering Review — Document Processing Pipeline

> 配套学习笔记：[phase-03-document-processing.md](../phase-03-document-processing.md)（T0301–T0308 逐章精读）
> 本文档定位：**工程决策复盘**。所有结论基于真实代码（`backend/app/services/ingest.py`，686 行）与 SPEC F002–F006。
> 诚实状态声明：T0301–T0308 全部 DONE。Phase 3 是全项目**代码量最大、决策密度最高**的模块——它把"用户上传的文件"变成"可检索的向量 chunk"，RAG 的"R 与 A 之间的原料工厂"。

---

## 1. Phase 定位

| 维度 | 内容 |
|------|------|
| **业务目标** | 让用户扔进来的任意文件（TXT/MD/CSV/JSON/LOG/DOCX/XLSX/PDF）都变成知识库里的"可检索片段" |
| **技术目标** | 实现 SPEC F002 的 8 步摄取管道（Validate→Save→Parse→Clean→Chunk→Embed→Store→Invalidate keyword index）中的 **Parse→Clean→Chunk→Embed→Store** 五步（Validate/Save 归 Phase 5 上传层，Invalidate 归 Phase 6 检索层）；以及 F004 的三态状态模型 + FAILED 回滚 |
| **系统位置** | Service Layer 的"原料工厂"。上游：Phase 0（config：MAX_CHUNK_SIZE/CHUNK_OVERLAP/上传目录；errors：6 个专用错误码）、Phase 1（VectorStore：`add_texts`/`delete_by_file`）、Phase 2（`encode_chunks`） |
| **上游依赖** | Phase 0/1/2 全部兑现（Ingest 是第一个**整合前三个 Phase**的模块 —— 三方的契约第一次在同一段代码里交汇） |
| **下游消费者** | Phase 5 Upload API（T0503 调用 `IngestService.process` —— Future）、Phase 9 File Delete（复用 FAILED 回滚的 `delete_by_file` 路径 —— Future） |

**一句话**：Phase 3 是三条已建基础设施（配置/错误、向量库、Embedding）的**首次会师**——它自己不带新的第三方能力，而是把 Phase 0-2 的契约编织成一条生产流水线。

---

## 2. 为什么需要这个模块？

**没有 Document Processing Pipeline，系统会缺什么：**

1. **知识进不来**：Phase 1 的 `add_texts` 需要一个 `List[str]` 的 chunks 和 384 维向量——从用户上传的二进制文件到这个调用之间隔着"解析→清洗→切分→嵌入"四步，没有 Ingest，这条链路不存在。
2. **没有统一的数据形态**：文件格式千差万别（PDF 是版面、DOCX 是 XML、TXT 是字节流、XLSX 是工作表）——必须先"平面化"成纯文本，后面的清洗/切分/嵌入才有一致的输入类型。
3. **没有"半失败"的语义**：真实世界的摄取不可能 100% 成功——PDF 某页是扫描图、OCR 服务超时、文件清洗后为空……系统必须回答"这次上传到底是成功了、部分成功了、还是彻底失败了"，而且失败时**不能留下垃圾数据**（半入库的 chunk、孤儿文件会污染检索结果）。

特别地，**FAILED 回滚的原子性**是本模块区别于"朴素脚本"的分水岭：CLAUDE.md 的 Ingestion Invariants 要求"0 chunks → 全量回滚（无残留文件、无 ChromaDB chunks、keyword index 干净）"，且"同一文件名的重新上传不得被上次 FAILED 阻塞"。这是生产级摄取管道与一次性脚本的本质区别。

---

## 3. 核心设计决策

### 决策 1：strict-first 编码级联 —— UTF-8 → UTF-16 → GBK，前两级严格、最后一级忽略

**Decision**: 文本类文件按 `("utf-8", "utf-16", "gbk")` 顺序尝试解码；前两级 `errors="strict"`（失败即换下一个），GBK 是最后兜底且 `errors="ignore"`（丢弃非法字节，永不报错）；全部失败 → `AppError("FILE_PARSE_ERROR", details={"encoding_attempts": [...]})`。

**Context**: 真实代码 [ingest.py:100-108](../../backend/app/services/ingest.py#L100-L108)。SPEC F003 3.1 固定该策略。中文企业场景的文本文件常见 GBK/GB2312 编码（Windows 老文件），而 UTF-16 常见于 Windows 记事本保存的文件。

**Problem**: 文件编码没有可靠的自描述（无 BOM 或 BOM 缺失时），任何单一编码策略都会失败：只按 UTF-8 → 中文老文件全乱码；只按 GBK → 现代 UTF-8 文件乱码。而"探测编码"（chardet 类库）是启发式——正确率不是 100%，且引入新依赖。

**Chosen Solution**: **确定性级联**（deterministic cascade），顺序按使用概率从高到低（UTF-8 现代默认 → UTF-16 Windows 记事本 → GBK 中文老文件），最后一级容忍损坏字节——"宁可丢字节，不可丢文件"。UTF-8 和 UTF-16 用 strict 是因为这两个编码的非法字节序列几乎必然意味着"猜错了编码"（UTF-8 严格的格式约束使其误判率极低），而 GBK 作为末位，ignore 保证它**永不失败**。

**Why**: ① **不引入依赖**：chardet 是启发式猜测，级联是确定性规则——SPEC 选择了可解释、零依赖的方案；② **末位永不失败**：级联必须有一个"兜底兜底"，否则 pipeline 又回到"编码错误中断文件"的老路；③ `details` 携带每次失败的尝试历史——排查"为什么解析失败"时能看到三条记录，错误码体系的可诊断性得到兑现。

**Trade-off**: ① GBK ignore 会**静默丢字节**：一个实际上是其他编码的文件，可能被 GBK "成功"解码成乱码文本——错误变成了坏数据（更隐蔽）。缓解：UTF-8 strict 在前，绝大多数文件在第一级就正确分流；② 无 BOM 检测的显式逻辑（UTF-16 的 BOM 由 Python 解码器处理）；③ 编码探测类库的正确率优势被放弃。

**Future Improvement**（Future / Not implemented in v1）: 文件级编码元数据记录（解析时用了哪个编码，写进 chunk metadata，便于追溯乱码来源）；或引入 chardet 作为 GBK 之前的补充探测——均需 SPEC 决策。

---

### 决策 2：逐页 PDF 解析 + OCR 回调解耦 —— 解析器不认识 DashScope

**Decision**: `parse_pdf_file` 逐页提取原生文本；页文本为空时调用**注入的** `ocr_page` 回调（契约 `ocr_page(pdf_path, page_number) -> str`，1-based 页码）。Qwen-VL 的实现（T0305）通过回调注入，解析器本身不 import dashscope。页文本按原页序 `"\n\n"` 拼接；`finally: doc.close()` 保证 PDF 句柄释放。

**Context**: 真实代码 [ingest.py:194-250](../../backend/app/services/ingest.py#L194-L250)。T0304（PDF 解析）与 T0305（OCR fallback）是两个独立 Task，SPEC F003 3.2 / F004 分别契约。

**Problem**: 扫描版 PDF 的原生文本为空——用户上传的合同扫描件、纸质书扫描没有可提取的文本层。选项：① 解析器内部直接调用 OCR API——**解析与外部服务焊死**，换 OCR 供应商/加缓存都要改解析器；② 解析器抛异常——一页扫描图导致**整个文件失败**，太粗暴；③ 回调注入——解析器定义"什么时候需要 OCR"，OCR 的"怎么 OCR"由外部提供。

**Chosen Solution**: 方案③。逐页循环：`page.get_text()` 非空 → 用原生文本；空 → 有回调则调 `ocr_page`，无回调则贡献空串。**v1 明确不做**：对已有原生文本的页做增强 OCR（成本翻倍，收益递减）。

**Why**: ① **依赖倒置**：PDF 解析（通用能力）不依赖 OCR 供应商（外部服务）——`parse_pdf_file` 可独立测试（传 mock 回调），`ocr_page` 可独立演进（换供应商只改回调实现）；② **契约冻结在 Task 边界**：T0304 时回调还没有真实实现（T0305 才写），`Optional[Callable]` 让两个 Task 解耦交付——这是"接口先行"开发顺序的范例；③ **页序保持**：`"\n\n"` 拼接 + 原页序循环保证 chunk 的上下文顺序与原文一致；④ `finally` 释放 PDF 文件句柄——Windows 上打开的文件无法删除，FAILED 回滚的 `unlink` 依赖此行为。

**Trade-off**: ① 回调签名只有 `(pdf_path, page_number)` 两个参数——渲染页面的活（`page.get_pixmap()`）在 `ocr_page` 内部重新打开 PDF 完成（重复打开文件，微开销）；② 回调返回空串与"页失败"不可区分（`ocr_page` 内部用 warning 通道记录失败——见决策 8）；③ 无 OCR 缓存——同一页重传时再次付费调用。

**Future Improvement**（Future / Not implemented in v1）: OCR 结果缓存（按 PDF 哈希 + 页码）；增强混合 OCR（原生文本 + 版面识别提升质量——SPEC 明确 defer）。

---

### 决策 3：两级错误模型 —— 页失败跳过页，文件级问题终止文件

**Decision**: OCR 错误分两级：**页级**（渲染失败/重试耗尽/其他非 200）→ 返回空串 + 记录 warning，文件继续；**文件级致命**（API key 未配置 → `OCR_NOT_CONFIGURED`；401/403 → `OCR_AUTH_FAILED`；加密 PDF → `ENCRYPTED_PDF`）→ 抛 `AppError`，整个摄取终止。

**Context**: 真实代码 [ingest.py:291-301](../../backend/app/services/ingest.py#L291-L301)（docstring 明确列出 Fatal errors 清单）。SPEC F004：per-page tolerance + fatal error 表。重试策略：初始 + 2 次重试 = 3 次总尝试，指数退避 ~1s/~2s；**401/403 不重试**（重试无用且浪费配额）。

**Problem**: 若所有 OCR 错误都致命：一本 200 页扫描书里 1 页识别失败 → 整个文件摄取失败 → 用户被迫重传。若所有错误都容忍：认证配置错误（key 缺失）→ 每页都静默失败 → 文件"成功"入库但内容全空——**比失败更糟的假成功**。

**Chosen Solution**: 按"**是否可局部恢复**"分级：页级失败是局部噪声（跳过一页，损失一页）；认证/配置错误是系统性故障（每页都会失败，容忍它只会制造 N 个 warning + 一个空文件）——必须立刻停。401/403 不重试的理由：认证失败是确定性错误，重试不会改变结果，只会加倍延迟和 API 调用次数。

**Why**: ① **失败粒度与恢复粒度对齐**：能恢复的（单页）不升级，不能恢复的（系统性的）不降级；② **错误码语义清晰**：上层 API 收到 500 OCR_AUTH_FAILED 时知道"这是部署问题（key 配错了），不是用户文件问题"；③ **成本控制**：无意义重试是 API 配额浪费，401/403 免重试是成本意识。

**Trade-off**: ① 页级失败只记录 `{page_number, error_code}`——**不含错误详情**（原始异常信息丢失，排查"为什么这页 OCR 失败"只能靠 warning 码推断）；② 3 次尝试的总延迟上限 = 页数 × 最坏 ~3s（timeout + 2 次退避），100 页扫描文件最坏 300s+——同步管道下用户等待感明显。

**Future Improvement**（Future / Not implemented in v1）: warning 携带结构化错误详情；超时预算（整文件 OCR 时间上限，超过则快速失败）。

---

### 决策 4：三态状态模型 + FAILED 全量回滚 —— 失败是返回值，不是异常

**Decision**: `process()` 返回三种状态：`SUCCESS`（无 warning、chunks>0）、`SUCCESS_WITH_WARNINGS`（有 OCR 页级 warning、chunks>0）、`FAILED`（清洗后为空或 0 chunks）——**FAILED 以返回值表达，不以异常表达**；FAILED 时 `_fail()` 执行 `file_path.unlink(missing_ok=True)` + `delete_by_file(collection_name, file_id)` 全量回滚。

**Context**: 真实代码 [ingest.py:658-683](../../backend/app/services/ingest.py#L658-L683)。SPEC F002/F004。CLAUDE.md Ingestion Invariants 将其列为不可违反的契约。注意责任边界：**keyword index 失效不在 Ingest 内**（T0308/T0502 scope split——上传层负责，因为 v1 的 keyword index 是 Phase 6 的检索侧缓存）。

**Problem**: 若 FAILED 用异常表达：① 上传 API 无法区分"用户文件问题"（返回 FAILED 状态给用户看）与"系统错误"（500）——`FAILED` 是**业务结果**，不是程序错误；② 空文件（清洗后为空）太常见，用异常表达会把正常业务流变成错误流。若失败不回滚：残留的 raw 文件和 ChromaDB chunks 会让 `get_files()` 列出幽灵文件、检索命中半成品——**数据污染**。

**Chosen Solution**: 状态模型 + 补偿式回滚。`_fail` 的两步删除覆盖两个存储：文件系统（`unlink(missing_ok=True)` 幂等——文件已被删也不报错）和 ChromaDB（`delete_by_file` 按 file_id 清理——即便 add_texts 从未执行也无害，**幂等**）。回滚后返回 FAILED dict（含 warnings），保证"重新上传同文件名不被上次 FAILED 残留阻塞"。

**Why**: ① **失败即无痕**：FAILED 文件在所有存储中不可见——检索、文件列表、关键词索引三处都"像从未上传过"；② **幂等设计**：`missing_ok=True` 和 `delete_by_file` 对"不存在"都安全——回滚可以重复执行；③ 三态映射到 HTTP 层很自然（Phase 5：SUCCESS/SUCCESS_WITH_WARNINGS → 200，FAILED → 200 带状态字段——SPEC 契约，不映射为 4xx/5xx）；④ 回滚是**补偿模式**（无跨存储事务可用）：操作顺序"先文件后 ChromaDB"，补偿顺序"先文件后 ChromaDB"。

**Trade-off**: ① **进程崩溃窗口**：`_fail` 只覆盖管道内失败——若进程在 add_texts 之后、返回之前崩溃，残留 chunk 无人清理（v1 无备份/恢复策略，SPEC OQ-011 defer）；② FAILED 不是异常 → 调用方必须**检查返回值**而非依赖异常处理——契约更隐式（Phase 5 上传层必须记得处理三态）；③ `ingestion_status` 只有 SUCCESS 类状态会入库（FAILED 无 chunk 可写）——"这个文件 FAILED 过"的历史不持久化。

**Future Improvement**（Future / Not implemented in v1）: 崩溃恢复的孤儿清理任务（启动时扫描 uploads/ 与 ChromaDB 的差异）；FAILED 历史记录（需要元数据库）。

---

### 决策 5：所有文件统一走 Markdown 标题拆分 + 标题路径前缀

**Decision**: `chunk_text` 对**所有格式**（不只 .md）先跑 `MarkdownHeaderTextSplitter`（# → #### 四级）；落在标题下的候选 chunk 加 `"Header 1 > Header 2\n\ncontent"` 前缀（非空标题值用 `" > "` 连接）；超长候选（> MAX_CHUNK_SIZE=800）再用 `RecursiveCharacterTextSplitter` 按冻结的分隔符优先级 `["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]` 切分（重叠 120 字）；短 chunk **永不合并**。

**Context**: 真实代码 [ingest.py:433-531](../../backend/app/services/ingest.py#L433-L531)。SPEC F006：Step 1 对 .md 用标题切分，Step 2.1 其他文件"先尝试 Markdown 标题切分"——**v1 行为等价于全文件统一**（docstring 明示："the extension does not gate behavior in v1"）。函数签名保留 `source_file` 参数是"冻结签名"的产物。

**Problem**: ① **纯字符切分丢失文档结构**：把 800 字硬切成块会截断章节边界——"3.1 系统架构"的正文可能被切进"3.2 数据模型"的 chunk；② **检索结果缺上下文**：chunk 被检索到后，用户看到的片段没有"它属于哪一章"的信息——来源引用（Phase 8）和相关性判断都需要。

**Chosen Solution**: 两级切分。第一级：标题结构优先——文档的自然边界（章节）成为 chunk 边界，切分成本为零、语义损失最小；第二级：超长章节用递归分隔符从高到低（段落→换行→句号→……→单字）寻找最"温柔"的切点，重叠窗口保持语义连续。标题路径作为前缀写进 chunk 内容（而非只写 metadata）——**检索和展示天然携带章节上下文**。

**Why**: ① **结构是免费的切分信号**：标题边界是作者标注好的语义边界，比任何算法都好；② **中文标点分隔符是本地化设计**：`。！？；，` 的优先级来自中文文本的特征（英文 splitter 只认空格），这是本项目的"中文工程"细节；③ 短 chunk 不合并：合并小章节会破坏结构边界（把"标题 A"和"标题 B"粘在一起）——SPEC 选择宁碎勿合；④ 标题路径进 content 而非仅 metadata：`final_score` 排序、关键词索引（Phase 6 对 content 分词）、展示全部受益，**信息在数据里，不在管道里**。

**Trade-off**: ① **非 Markdown 文件的标题切分是"尽力而为"**：纯 TXT 里出现 `#` 开头的行会被误判为标题（如代码日志）——v1 接受此误判（SPEC Step 2.1 的原话就是"先尝试"）；② 标题路径前缀会**增加 chunk 长度**（每 chunk 多几十字，且同章节 chunks 重复前缀——检索时前缀词权重被稀释/放大）；③ 800/120 的固定参数对长文档与短文档一刀切——短文本文档可能被切得很碎（但短 chunk 不合并已兜住下限）。

**Future Improvement**（Future / Not implemented in v1）: 按文档类型分派切分策略（代码文件用 AST 切分）；chunk 级参数化（每文件或每类型不同 chunk_size）。

---

### 决策 6：UUID 身份在 Ingest 侧生成 —— 一次上传一个 file_id

**Decision**: `process()` 开始时生成一个 `file_id`（UUID4），传给 `chunk_text` 共享给该文件的所有 chunks；每个 chunk 另有自己的 `chunk_id`（UUID4）和 0-based `chunk_index`（发射顺序）。身份生成**发生在摄取管道内**，上传层不提供业务 ID。

**Context**: 真实代码 [ingest.py:594](../../backend/app/services/ingest.py#L594)、[ingest.py:523-530](../../backend/app/services/ingest.py#L523-L530)。SPEC 7.1 身份规则；CLAUDE.md Identity Rules。`file_id` 最终成为 ChromaDB 元数据（Phase 1 决策 4 的下游兑现：chunk_id 即 ChromaDB document id）。

**Problem**: 身份若由上传层/前端生成：① 前端可伪造/冲突 ID；② 上传层与摄取层出现新的契约耦合。身份若用文件名/时间戳：重名、时钟回拨、并发冲突全来了。UUID4 由谁生成、何时生成、如何共享给所有 chunks——是管道设计的细节但对删除/引用/回滚的正确性至关重要。

**Chosen Solution**: 摄取管道入口生成 file_id，参数显式传递（`chunk_text(cleaned, file_name, file_id=file_id)`——函数自身也支持缺省生成，保持可独立使用）；chunk_id 在发射时逐 chunk 生成。`chunk_index` 是 `enumerate` 的产物——**顺序号，不是身份**（删除中间 chunk 不影响其他 chunk 身份）。

**Why**: ① **身份与内容同生命周期**：file_id 在解析文件的那一刻诞生，FAILED 回滚时用它精准删除（`delete_by_file(collection, file_id)` 依赖这个 ID 在失败路径上仍然有效——回滚字典里也带着它）；② **前端零信任**：业务 ID 全部服务端生成，前端只拿结果；③ 与 Phase 1 的存储契约无缝衔接：chunk_id 直接用作 ChromaDB document id，file_id 直接用作 where 过滤键——**身份系统端到端贯通**。

**Trade-off**: ① 重传同一文件 = 新 file_id（无去重语义——v1 明确无文件版本化）；② file_id 的生成时机意味着"文件已落盘"先于"身份诞生"（上传层保存文件时还没有 file_id——文件名是唯一的早期引用，Phase 5 需要处理这个时序）。

**Future Improvement**（Future / Not implemented in v1）: 内容哈希去重（相同文件重传复用向量）；file_id 与上传会话的绑定。

---

### 决策 7：CSV/JSON 当纯文本解析 —— v1 不做结构化解析

**Decision**: `.csv`/`.json` 文件走 `parse_text_file`（编码级联 + 原样文本），**不解析成行列/字段结构**。`parse_excel_file` 用 openpyxl `data_only=True` 提取各 sheet 的**计算值**（非公式），单元格按行拼接。

**Context**: 真实代码 [ingest.py:538](../../backend/app/services/ingest.py#L538)（`_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}`）与 parse_excel_file（T0303）。CLAUDE.md Out of Scope 明确："CSV/JSON structured parsing"。SPEC F003 3.4 对 Excel 契约了 `data_only=True`。

**Problem**: 结构化解析（CSV→表格语义、JSON→字段语义）意味着：① 每种格式的语义模型都要定义"什么是可检索单元"（一行？一列？一个对象？）；② chunk 的 metadata 要承载结构信息（字段名、行号）；③ 检索侧的展示（Phase 8 来源引用）要理解结构。这是**一个完整的子项目**。

**Chosen Solution**: v1 把所有文本类文件统一为"纯文本流"——CSV 的逗号分隔、JSON 的括号都只是文本的一部分，交给清洗和切分自然处理。Excel 特殊对待（二进制格式必须解析），但只提取**值**（`data_only=True` 拿缓存的计算结果而非公式字符串）——用户看到的是数据不是公式。

**Why**: ① **YAGNI 与 SPEC 冻结**：结构化解析是明确的 v1 Out of Scope——为它建抽象是超前设计；② **统一管道收益**：纯文本是清洗/切分/嵌入的唯一输入类型——格式差异在 parse 层终结，后面三层完全复用；③ `data_only=True` 是 Excel 场景的常识级正确选择（公式字符串对检索无意义）。

**Trade-off**: ① JSON 的结构信息（键值关系）在文本化后丢失——检索"字段 X 的值"的能力不存在（v1 接受）；② CSV 的逗号在中文标点分隔符优先级中不特殊——列边界被当普通字符处理；③ Excel 的行列结构被"行内空格连接"拍平——列对齐关系丢失。

**Future Improvement**（Future / Not implemented in v1）: 结构化解析（CSV/JSON 的字段级 metadata、表格的行列保留）——SPEC 明确 defer，需要重新打开 F003。

---

### 决策 8：模块级 OCR 警告通道 + keyword index 职责外移 —— 管道边界的两次切割

**Decision**: ① OCR 页级失败通过**模块级列表** `_OCR_WARNINGS` 传递（`_record_ocr_warning` 写入、`get_ocr_warnings`/`clear_ocr_warnings` 读写），`process()` 开始时 `clear_ocr_warnings()` 保证 per-file 隔离，结束时收集进返回值的 `warnings` 字段；② **keyword index 失效不在 Ingest 内**——上传层负责（T0502 scope split），Ingest 的 docstring 明确声明。

**Context**: 真实代码 [ingest.py:264-281](../../backend/app/services/ingest.py#L264-L281) 与 [ingest.py:552-553](../../backend/app/services/ingest.py#L552-L553)。SPEC F004 要求 warnings 出现在 UploadResponse；v1 的 keyword index 在 Phase 6 才存在（Phase 3 时它还不存在——提前失效它 = 依赖未来模块）。

**Problem A（warning 怎么传）**: `parse_pdf_file` → `ocr_page` 的调用链是函数嵌套，页级失败发生在深层。选项：① 异常携带——但页级失败不抛异常（决策 3）；② 返回值携带——`ocr_page` 的返回值契约已冻结为"文本或空串"，加返回值会破坏 T0305 的冻结契约；③ 显式收集器参数——污染所有函数签名。

**Problem B（index 失效归谁）**: Ingest 管不管 keyword index？Phase 3 实现时 index 尚不存在（Phase 6）——在 ingest 里写失效逻辑 = 预建未来模块的接口。

**Chosen Solution**: A → ③'：模块级"便签"（side channel）——深度调用链的叶子上写一笔，管道入口统一收割。契约显式化：`clear` 由 process 在文件开始处调用，`get` 在结束时调用，**生命周期归属管道**。B → 责任外移：Ingest 的边界是"文件 → chunks → 向量库"，index 是检索侧缓存，由知道 index 存在的层（上传层在 T0502 与 Phase 6 协作后）失效。

**Why**: ① **冻结契约不破坏**：warning 通道不动 `ocr_page` 的签名和返回值；② **管道拥有生命周期**：docstring 明示 "Lifecycle (clear per file) is owned by the ingest pipeline (T0308)"——全局状态的局部化治理；③ **依赖方向正确**：Ingest 不依赖未来的 Phase 6——"谁缓存谁失效"是缓存管理的基本法则；④ warning 结构化：`{page_number, error_code}` 恰好就是 SPEC F004 的 UploadWarning schema——服务层与 API 层模型零转换。

**Trade-off**: ① **模块级全局可变状态**：并发摄取时 `clear_ocr_warnings()` 可能清掉**另一个文件**正在累积的 warnings——FastAPI 线程池并发下这是真实竞态（v1 低并发假设下概率低，但设计上是已知弱点，**这是本模块最值得在面试里主动承认的工程债**）；② 回滚路径（`_fail`）也依赖 warning 通道——两处收割点要保持同步；③ index 失效外移后，调用方若忘记失效 → 检索结果陈旧——责任转移换来的解耦需要 Phase 5 的纪律来兑现。

**Future Improvement**（Future / Not implemented in v1）: warning 通道改为显式收集器对象（线程安全/上下文局部）；摄取与索引失效的编排化（事件驱动）。

---

## 4. 架构影响

Phase 3 完成后，系统新增的能力与依赖关系：

| 新增能力 | 谁开始依赖它 | 未来 Phase 谁使用 |
|---------|------------|-----------------|
| `IngestService.process()`（完整 5 步管道 + 三态） | —（Phase 3 内自洽） | Phase 5 Upload API（T0503 直接调用 —— Future） |
| 三态状态模型（SUCCESS/SUCCESS_WITH_WARNINGS/FAILED） | — | Phase 5（UploadResponse 的 `status` 字段契约来源） |
| FAILED 回滚（unlink + delete_by_file） | — | Phase 9 File Delete（复用 `delete_by_file` —— Future） |
| 9 字段 metadata 契约（含 denormalized file_size/upload_time/ingestion_status） | Phase 1 VectorStore（写入侧接收 —— **已实际发生**） | Phase 4（file_count 聚合）、Phase 9（FileRecord） |
| `parse_pdf_file` 的 OCR 回调位 | `_parse`（注入 `ocr_page` —— 已实际发生） | —（契约已闭合） |
| 结构化 warnings `{page_number, error_code}` | — | Phase 5（UploadResponse.warnings 直通 —— Future） |
| Phase 0-2 首次整合 | 全链路：config + errors + VectorStore + Embedding 在同一流程中协作 | 后续 Phase 全部站在此整合之上 |

**关键洞察**：Phase 3 验证了 Phase 0-2 契约的**真实可用性**：Ingest 不需要知道 ChromaDB 的 `_collection`（只用 `add_texts`/`delete_by_file`）、不需要知道 sentence-transformers 的加载细节（只调 `encode_chunks`）、不需要自己构造错误响应（只抛 `AppError`）。**分层架构的第一次集成考试通过**——这正是 Phase 0-2 抽象设计的回报。同时注意两处**跨层时序契约**：① 文件由上传层保存、由 Ingest 在 FAILED 时删除——文件生命周期跨越两层，Phase 5 必须精确遵守；② keyword index 失效在 Ingest 之外——Phase 5/6 集成时是已知的联动点。

---

## 5. 工程问题分析

### 可维护性

- ✅ 单文件 686 行但结构清晰：解析器（按格式）→ 清洗 → 切分 → OCR → 编排，函数粒度与 SPEC 条款一一对应（docstring 都引用 F003/F004/F005/F006 的具体条款）
- ✅ 所有函数内 import 都有 docstring 解释原因（"importing this module never fails..."）——设计意图随代码留存
- ⚠️ `_parse` 的扩展分派是 `if/elif` 链 + 硬编码扩展名集合——新增格式要改两处（集合 + 分派）；集合是模块级常量，改起来直观但分派逻辑无注册机制
- ⚠️ `_fail` 的签名要求 file_id 在**所有失败路径之前**已生成——若未来有人在生成 file_id 之前插入失败路径，`_fail` 会用不存在的 file_id 做无意义删除（幂等兜住正确性，但逻辑上别扭）

### 扩展性

- ✅ 解析器是**可插拔的**（新增格式 = 新函数 + 分派表一行）；OCR 回调是可替换的（换供应商只改 `ocr_page`）
- ✅ 切分参数配置化（`MAX_CHUNK_SIZE`/`CHUNK_OVERLAP` 来自 settings）——调参不改代码
- ⚠️ **同步管道**：`process()` 从解析到入库一气呵成，无进度、无暂停、无取消——未来要进度推送/异步化需重构成任务模型
- ⚠️ 分隔符优先级列表是模块级常量（冻结于 SPEC）——想针对不同语言/文体调整需要改代码 + SPEC

### 数据一致性

- ✅ 9 字段 metadata 由管道一次构造——同 file_id 的 denormalized 字段天然一致（Phase 1 决策 5 的一致性约束在这里被兑现）
- ✅ FAILED 回滚幂等（`missing_ok=True` + `delete_by_file` 对不存在安全）——重复回滚无副作用
- ⚠️ **`_OCR_WARNINGS` 模块级全局的并发竞态**（决策 8 Trade-off）：两个文件并发摄取，A 的 `clear` 可能清掉 B 已记录的 warnings → B 的 SUCCESS_WITH_WARNINGS 误报为 SUCCESS。**数据一致性的真实裂缝**——v1 低并发假设掩盖了它
- ⚠️ **崩溃窗口**（决策 4 Trade-off）：add_texts 与返回之间进程崩溃 → 残留 chunk 无回滚执行者
- ⚠️ `source_file` 字段硬编码 `uploads/{collection_name}/{file_name}` 前缀——若 `UPLOAD_DIR` 配置被改，metadata 与真实路径脱节（**配置与数据的隐性耦合**，当前两者默认值一致所以无感）

### 错误处理

- ✅ 6 个专用错误码覆盖解析/OCR 全谱系：UNSUPPORTED_FILE_TYPE、FILE_PARSE_ERROR（422）、ENCRYPTED_PDF（422）、OCR_NOT_CONFIGURED / OCR_AUTH_FAILED（500）、（EMBEDDING_MODEL_ERROR 来自 Phase 2 直通）
- ✅ `FILE_PARSE_ERROR` 的 details 携带编码尝试历史（决策 1）——错误可诊断性超基线
- ✅ 错误边界宣言清晰：parse/OCR 致命/embedding 错误**原样传播**（docstring 明示），FAILED **返回不抛出**——"什么冒泡、什么不冒泡"是显式契约
- ⚠️ **chunking 无专用错误码**：`langchain_text_splitters` import 失败 → 原始 ImportError → 全局 handler 兜底 500 INTERNAL_ERROR（docstring 诚实标注 "chunking has no catalog error code"）——错误码体系在管道末端有一处空白
- ⚠️ `parse_docx_file`/`parse_excel_file` 的宽捕获 `except Exception` 统一成 FILE_PARSE_ERROR——具体损坏原因丢失（docx 是缺段落还是缺样式表，用户不知道）

### 性能

- ✅ 惰性 import：不解析 PDF 就永远不加载 fitz/dashscope——请求路径的模块加载按需发生
- ✅ PDF 逐页处理 + `finally: doc.close()`：内存峰值约等于单页文本 + 拼接结果，不会整本 PDF 常驻
- ⚠️ **OCR 是性能与成本黑洞**：每页最多 3 次 API 调用 + 退避延迟——100 页扫描件最坏 300s+，且每次调用都要钱。v1 同步管道下这直接决定上传接口的响应时间
- ⚠️ `encode_chunks` 一次编码全量 chunks（Phase 2 决策 7 的调用方正是这里）——大文件无 batch 上限
- ⚠️ Markdown 标题拆分 + 递归拆分是**纯 CPU 串行**处理——超大文件（万字级）管道整体秒级

### 安全

- ✅ 文件名不参与任何身份/查询构造（file_name 仅 display + metadata）——Phase 5 的路径穿越校验与 Ingest 的 `source_file` 拼接是分离的两层（本模块信任上传层已完成校验——边界契约）
- ✅ 无 eval/反序列化攻击面：DOCX/XLSX 用标准库解析器（python-docx/openpyxl 对 zip 炸弹类攻击有基本防护，但无显式大小上限）
- ⚠️ **无文件大小上限校验**：Ingest 不校验 `file_size`——超大文件（GB 级）会拖垮内存（上传层的校验归 Phase 5，Ingest 是"已保存文件"的消费者，边界信任明确但值得知晓）
- ⚠️ OCR 发送页面图像到外部服务（DashScope）——敏感文档内容离开本机（SPEC 部署假设接受；API key env-only 已守）

---

## 6. 如果规模扩大怎么办？

> 本节所有方案均为 **Future / Not implemented in v1** 分析。SPEC NFR 11.2：v1 单机、万级 document；v1 明确无上传进度推送（F002）、无结构化解析。

### 10× 规模（文档量 ×10，如批量上传、大文件变多）

**可能出现的瓶颈**：

- **同步管道阻塞请求**：上传 API 在 process() 内完成全管道才返回——10× 文件量意味着单个大文件（含 OCR）可能占住请求数分钟，请求线程池被拖垮
- OCR 成本线性放大：页数 × 3 次尝试 × API 单价
- `_OCR_WARNINGS` 并发竞态从"理论"变成"实际"（并发上传增多）

**优化方向**（Not implemented in v1）：

- **同步 → 异步任务队列**（Celery/RQ）：上传 API 秒回"已受理"，ingest 在 worker 中执行，前端轮询状态（SPEC 2.5 明确 defer）
- warning 通道改为线程安全的收集器（或每文件独立对象）
- OCR 结果缓存（文件哈希 → 页文本），重传零成本

### 100× 规模（文档量 ×100，如团队级知识库、每日大量文档）

**可能出现的瓶颈**：

- 单机 CPU 全被打切分/嵌入/OCR 吃满——与查询请求（Phase 7/8 的检索 + LLM 调用）争抢同一进程资源，**查询延迟被摄入拖累**
- uploads/ 单目录文件数膨胀（Windows 单目录万级文件性能骤降）
- OCR 配额与账单：百倍量级下 Qwen-VL 调用费成为显著成本项

**优化方向**（Not implemented in v1）：

- **摄取与查询分离部署**：ingest worker 独立进程/机器（任务队列的必然延伸）
- 对象存储（S3/MinIO）替代本地 uploads/ 目录，source_file 语义改为对象键
- OCR 成本治理：低分辨率预检（能出原生文本就不调用）、页级缓存、供应商比价

### 1000× 规模（SaaS 化，多租户、亿级 chunk）

**可能出现的瓶颈**：

- **管道吞吐成为系统吞吐**：亿级 chunk 的摄入 = 大量 CPU（切分/嵌入）+ GPU（嵌入）+ 外部 API（OCR）的混合调度问题——需要专门的摄取集群
- 单文件阻塞模型彻底失效：需要分片摄取、断点续传、进度上报
- 编码级联/标题切分等确定性策略在异构语料（多语言、代码、扫描件混合）下的正确率成为质量瓶颈
- metadata 反规范化（Phase 1 决策 5）在亿级 chunk 下的写入放大与存储成本

**优化方向**（Not implemented in v1）：

- **分布式摄取平台**：摄取任务分片到多 worker（按文件/按 PDF 页范围），任务队列 + 结果汇聚
- **摄取管道可观测化**：每步耗时/失败率的 metrics（v1 无 APM——CLAUDE.md Out of Scope）
- 格式分派注册机制（插件式解析器）+ 语料自适应切分策略
- 专用元数据库接管 FileRecord（Phase 1 决策 5 的规模终局）——chunk metadata 瘦身

**核心判断**：Phase 3 的决策本质是**用同步管道 + 确定性策略换简单与正确**——在 v1 规模下这是完全正确的取舍（万级文档、单机、低并发）。规模扩大时，最先要动的是"同步→异步"和"warning 通道线程安全"，然后是摄取与查询的资源隔离；解析/切分的确定性策略本身反而是最耐用的部分——它们不依赖任何单机假设。
