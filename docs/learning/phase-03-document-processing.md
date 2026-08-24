# Phase 3 — Document Processing Pipeline 学习笔记

> 这是一份随项目开发和个人理解逐步演进的学习文档。当前版本覆盖 **Phase 3 的全部八个 Task：T0301（文本文件解析）+ T0302（DOCX 解析）+ T0303（Excel 解析）+ T0304（PDF 原生提取）+ T0305（Qwen-VL OCR fallback）+ T0306（Text Cleaning）+ T0307（Text Chunking & ID Generation）+ T0308（Ingest Service 编排）**——Phase 3 到此完整收官，并已按 Phase 3 Learning Review 整理（第 42–44 节收尾整合）。
>
> 结构：第 0 节全景速览 → 第 1–11 节 T0301（文本解析 + 编码级联）→ 第 12–16 节 T0302（DOCX 解析）→ 第 17–21 节 T0303（Excel 解析）→ 第 22–26 节 T0304 + T0305（PDF 逐页解析 + OCR fallback，两个 Task 一个故事，合并教学）→ 第 27–31 节 T0306（Text Cleaning）→ 第 32–36 节 T0307（Text Chunking & ID Generation）→ 第 37–41 节 T0308（Ingest Service 编排，Phase 3 收官）→ 第 42–44 节 Phase 3 Learning Review 收尾整合（全 Phase 总复习卡 + 跨 Task 整合自测 + Pending #1–27 汇总收官）。
>
> 面向读者：前端开发者，熟悉 JavaScript / TypeScript / React，有少量 Node.js 经验，没有系统 Python 基础。

---

## 0. 阅读指南

### 这一章的目标是什么

读完 T0301 + T0302 后，你需要做到：

- 理解 Phase 3 在整条 Ingest Pipeline 中的位置（Parse 站），以及 T0301/T0302 在这站里各自负责的格式
- 能用 JS/TS 知识（`fs.readFileSync` + `Buffer` + `TextDecoder`）类比理解文本解析的代码
- 掌握 Python 的一个核心新概念：**`bytes` 和 `str` 是两种类型**，以及解码（decode）的方向
- 理解"编码级联"（UTF-8 → UTF-16 → GBK）为什么前两级用 strict、最后一级用 ignore——乱码（mojibake）是怎么产生的
- 知道 `FILE_PARSE_ERROR` 的两条触发路径，以及 `details.encoding_attempts` 第一次让错误响应有了"结构化上下文"
- 理解 DOCX 的本质（zip + XML 容器）、python-docx 替我们挡掉了什么，以及"段落在前、表格在后"这个 SPEC 固定顺序的含义（T0302）
- 理解 Excel 的本质（**又一个 zip 容器——与 DOCX 同族**）、openpyxl 的 `data_only` 语义，以及"跳过空行/空 sheet"的两层过滤结构（T0303）
- 理解 PDF 与前四种格式的本质区别（**不是文本、也不是 zip+XML——是排版指令 + 可选的文本层**）、"原生文本 vs 扫描图片页"的判定点，以及**回调契约**如何让 T0304 和 T0305 解耦（T0304）
- 理解 OCR fallback 的完整链路（渲染 → Base64 → 多模态 API → 重试）、**三层失败分级**（文件级 fatal / 页级容错 / 状态机），以及 Parse 站第一次出现的 500 错误码与 warnings（T0305）
- 理解清洗站的本质：**Parse 站之后的第一道"纯函数"工序**——三行列表推导组成的管道、"做 5 步、不做 5 件事"的边界纪律，以及空文本的拒绝权为什么在 T0308 而不在清洗站（T0306）
- 理解切分站的本质：**字符串第一次变成结构化数据的地方**——两段式切分（标题优先、超长递归再切）、UUID 身份体系（file_id / chunk_id / chunk_index 的分工与不可变性），以及"切分没有自己的错误码"的哲学（T0307）
- 理解编排站的本质：**管道第一次被"接起来"的地方**——parse → clean → chunk → embed → store 五站串联、F004 三态判定（SUCCESS / SUCCESS_WITH_WARNINGS / FAILED）第一次兑现、FAILED rollback 的原子性语义、以及"FAILED 是返回值不是异常"的哲学（T0308）

### 本章阅读路线

| 章节                                       | 深度      | 说明                                       |
| ---------------------------------------- | ------- | ---------------------------------------- |
| 第 1 节 Phase 3 定位与 T0301 分工               | 🟢 必看   | T0301 在整条管道里的位置                          |
| 第 2 节 用 JS/TS 类比理解                       | 🟢 必看   | Buffer / TextDecoder / fatal 对照          |
| 第 3 节 逐行精读 ingest.py（T0301 部分）           | 🟢 必看   | parse_text_file 逐行精读                     |
| 第 4 节 编码级联深潜                             | 🟢 必看   | 为什么 strict 打前站、ignore 兜底                 |
| 第 5 节 错误契约链路                             | 🟢 必看   | 两条错误路径 + details 第一次真正派上用场               |
| 第 6 节 与前后 Phase 的连接                      | 🟡 建议理解 | 上游是谁、下游是谁、为什么本模块"不决策"                    |
| 第 7 节 SPEC F003 3.1 对照与验证                | 🟡 建议理解 | 实现 vs SPEC 对照读法 + 诚实 AC 立场               |
| 第 8 节 Python 新知识索引                       | 🟢 按需   | 指向 python-for-frontend-dev.md 第 20 节     |
| 第 9 节 自测题与练习                             | 🟢 必看   | 检验 T0301 掌握程度                            |
| 第 10 节 快速复习卡                             | 🟢 必看   | T0301 收官速记                               |
| 第 11 节 进阶与 Pending Questions             | 🔵 以后再看 | 编码检测的固有权衡等                               |
| 第 12–16 节 T0302（DOCX 解析）                 | 🟢 必看   | parse_docx_file 逐行精读 + DOCX 本质 + SPEC 3.3 对照 |
| 第 17–21 节 T0303（Excel 解析）                | 🟢 必看   | parse_excel_file 逐行精读 + xlsx 本质 + data_only + SPEC 3.4 对照 |
| 第 22–26 节 T0304 + T0305（PDF + OCR）       | 🟢 必看   | parse_pdf_file / ocr_page 逐行精读 + 回调契约 + 三层失败分级 + SPEC 3.2/F004 对照 |
| 第 27–31 节 T0306（Text Cleaning）           | 🟢 必看   | clean_text 逐行精读 + 纯函数管道 + 五步五不做 + SPEC F005 对照 |
| 第 32–36 节 T0307（Text Chunking & ID Generation） | 🟢 必看   | chunk_text 逐行精读 + 两段式切分 + UUID 身份体系 + SPEC F006 对照 |
| 第 37–41 节 T0308（Ingest Service 编排）       | 🟢 必看   | IngestService 逐行精读 + 五站串联 + 三态判定 + FAILED rollback + SPEC F002/F004/F008 对照 |
| 第 42–44 节 Phase 3 Learning Review 收尾整合   | 🟢 必看   | 全 Phase 总复习卡（42A/42B/42C）+ 跨 Task 整合自测 + Pending #1–27 汇总与收官 |

### 三种学习深度标记

| 标记          | 含义                                 |
| ----------- | ---------------------------------- |
| 🟢 **入门理解** | 第一遍必须掌握的内容。用 TypeScript 类比 + 简单解释。 |
| 🟡 **项目理解** | 解释 DX-RAG 为什么这样设计。帮你理解架构决策。        |
| 🔵 **进阶阅读** | 可以以后回来看。不影响理解 T0301 的核心内容。         |

### 当前进度（2026-08-23）

- **T0301**: ✅ DONE — [ingest.py](../../backend/app/services/ingest.py)（`parse_text_file`，第 78–108 行）
- **T0302**: ✅ DONE — 同一文件第 111–147 行（`parse_docx_file`）
- **T0303**: ✅ DONE — 同一文件第 150–191 行（`parse_excel_file`）
- **T0304**: ✅ DONE — 同一文件第 194–251 行（`parse_pdf_file`）
- **T0305**: ✅ DONE — 同一文件第 253–378 行（OCR 警告基础设施 + `ocr_page`）
- **T0306**: ✅ DONE — 同一文件第 386–413 行（`clean_text`）
- **T0307**: ✅ DONE — 同一文件第 416–531 行（`chunk_text`；教学见第 32–36 节；T0308 起签名增加 `file_id` 参数，见第 34 节）
- **T0308**: ✅ DONE — 同一文件第 534–683 行（`IngestService`；教学见第 37–41 节）
- **Learning Review**: ✅ COMPLETED — 第 42–44 节收尾整合（2026-08-23）

### 全景速览（T0308 后更新 + Learning Review 复核——Phase 3 全貌）

Phase 3 目前的全部成果 = 一个 686 行文件里的 **7 个函数 + 1 个服务类（IngestService）+ 1 组模块级警告基础设施**。前七个 Task 各贡献一个函数——"一个函数撑起一个 Task"连续七次应验（第 32–36 节完整教学）；T0308 用**全模块第一个 class** 收官——编排不是"又一个函数"，而是把七个函数接成管道的第一层调度（第 37–41 节完整教学）：

```text
ingest.py（686 行）—— Phase 3 目前对外接口 = 7 个函数 + 1 个服务类
┌─────────────────────────────────────────────────────────┐
│ parse_text_file(file_path: Path) -> str     T0301 · 文本 │
│   ① read_bytes() 读文件 → bytes   └─ 失败 → 422          │
│   ② 编码级联循环（第 93–99 行）                           │
│        utf-8 strict ──▶ utf-16 strict ──▶ gbk ignore     │
│        （任何一级成功就 return，循环提前结束）              │
│   ③ 全败 → 422 + details.encoding_attempts               │
├─────────────────────────────────────────────────────────┤
│ parse_docx_file(file_path: Path) -> str     T0302 · DOCX │
│   ① 函数内 import + Document(str(file_path)) 打开         │
│        └─ 任何失败 → 422 FILE_PARSE_ERROR                │
│   ② 段落: "\n".join(p.text for p in doc.paragraphs)      │
│   ③ 表格: 行内 cell 用 " " 连，行间用 "\n" 连             │
│   ④ 段落 + 表格用 "\n" 拼接 → str（无任何合成标记）        │
├─────────────────────────────────────────────────────────┤
│ parse_excel_file(file_path: Path) -> str    T0303 · Excel│
│   ① 函数内 import + load_workbook(Path, data_only=True)  │
│        └─ 任何失败 → 422 FILE_PARSE_ERROR                │
│   ② 逐 sheet: iter_rows(values_only=True) 逐行读         │
│        行内 " ".join(str(cell) ... if cell is not None)  │
│   ③ 全空行跳过、全空 sheet 跳过                           │
│   ④ 非空 sheet 文本用 "\n" 拼接 → str                     │
├─────────────────────────────────────────────────────────┤
│ parse_pdf_file(file_path, ocr_page=...) -> str  T0304    │
│   ① fitz.open(str(file_path)) 打开；needs_pass → 422     │
│        ENCRYPTED_PDF（Parse 站第一个非 FILE_PARSE_ERROR）│
│   ② 逐页: get_text() 非空 → 原生文本；空 → 回调 ocr_page  │
│        （回调参数在 T0304 冻结 T0305 的契约，见第 22 节）  │
│   ③ 页间 "\n\n" 拼接（注意：两个换行，与其它 parser 不同）│
│   ④ finally: doc.close() —— 全模块第一次显式关资源        │
├─────────────────────────────────────────────────────────┤
│ ocr_page(pdf_path, page_number) -> str       T0305 · OCR │
│   ① key 未配 → 500 OCR_NOT_CONFIGURED（检查在最前）       │
│   ② 渲染 JPEG → Base64 data-URI → Qwen-VL-Plus 调用      │
│   ③ 重试: timeout/网络/429/5xx，1s/2s 退避，共 3 次       │
│        401/403 → 立即 500 OCR_AUTH_FAILED（不重试）       │
│   ④ 页级失败 → 返回 "" + 记录 warning（不中断整个文件）    │
├─────────────────────────────────────────────────────────┤
│ 警告基础设施（第 245–273 行）: _OCR_WARNINGS 模块级状态    │
│   + get_ocr_warnings() / clear_ocr_warnings() 访问器对    │
│   （生命周期由 T0308 编排管 ✅ 已兑现：process 开头 clear） │
├─────────────────────────────────────────────────────────┤
│ clean_text(text: str) -> str             T0306 · Cleaning│
│   ① splitlines() 按行边界切（认 \r\n 等，无末尾空串）      │
│   ② 每行 strip()（只动两端，行内空白保留）                 │
│   ③ 过滤 strip 后为空的行（if line 真值判断）              │
│   ④ "\n" 拼接；空结果 → ""（Step 5 免费：join 空列表）     │
│   ⑤ 纯函数：无 try、无 except、无状态、无 I/O（第 30 节）  │
├─────────────────────────────────────────────────────────┤
│ chunk_text(text, source_file, file_id=None) -> List[dict] │
│                       T0307 · 切分（T0308 起增参 file_id）│
│   ① 空/纯空白守卫 → []（不裁决——FAILED 判定已由 T0308     │
│        兑现，见下方编排框）                                │
│   ② Markdown 标题切分（所有文件）+ "章节 > 小节" 前缀      │
│   ③ 超长候选 → RecursiveCharacterTextSplitter 再切        │
│        （≤ 800 直通、短块不合并；重叠 ~120）               │
│   ④ UUID：file_id 由调用方传入（缺省才在此生成，第 34 节）、│
│        chunk_id 每块一个、chunk_index 0-based 仅排序      │
│   ⑤ 惰性导入 langchain——本模块第 4 次出现该模式           │
├─────────────────────────────────────────────────────────┤
│ IngestService（第 534–683 行）                T0308 · 编排│
│   ① 全模块第一个 class——前七站的调度者（第 37 节）         │
│   ② process: 解析(_parse 按扩展名分发) → 清洗 → 切分      │
│        → 嵌入 → 存储（五站串联，file_id 在最顶端生成）     │
│   ③ 三态判定（F004）：无警告 = SUCCESS；有警告 =           │
│        SUCCESS_WITH_WARNINGS；0 chunk = FAILED            │
│   ④ FAILED rollback：删原始文件 + delete_by_file          │
│        （keyword index 归上传层 T0502 管）                 │
│   ⑤ 错误边界：parse/OCR/embedding 的 AppError 原样传播；   │
│        FAILED 是返回值不是异常（第 40 节③）               │
└─────────────────────────────────────────────────────────┘
```

**数据形状的第一次分叉**：Parse 站五个函数统一 `Path → str`（文件 `bytes` / zip 容器 / PDF 对象 → Unicode 文本）；清洗站是 `str → str` 的纯变换（外形不变）；切分站第一次把字符串变成结构化数据——`str → List[dict]`（chunk_id / content / chunk_index / file_id 四键字典，第 32 节起完整教学）。**"字符串进、字典出"的分叉发生在切分站，不在清洗站**——清洗只是把脏 str 变成干净 str。**T0308 带来第二次分叉**：`process()` 吃 `(Path, str, str)` 吐**一个五键 dict**（status / file_id / file_name / chunks_count / warnings）——`List[dict]` 的"块列表"被收编成"一个文件的结果摘要"，数据形状从"列表"回到"单值"，但这次是**服务结果的形状**（F002 API 响应的雏形，第 37 节）。

**错误光谱第一次扩展**：前三个 Task 殊途同归——任何失败都落到 `FILE_PARSE_ERROR`（422）。T0304/T0305 打破了这个"单码世界"：`ENCRYPTED_PDF`（422，新场景新码）、`OCR_NOT_CONFIGURED` / `OCR_AUTH_FAILED`（**500——Parse 站第一次出现服务端错误码**）、以及两个**不是错误码的 warning**（`OCR_PAGE_FAILED` / `PAGE_RENDER_FAILED`，页级容错，见第 25 节③）。错误从"全有或全无"进化成"文件级 fatal / 页级容错"两级。**T0306 不进错误光谱**：clean_text 是全模块唯一没有异常路径的函数（无 raise、无 except）——错误哲学的复杂度属于"有外部世界"的站，不属于纯函数站（第 30 节①）。**T0307 也不进错误光谱，但原因不同**：chunk_text 没有 try/except 不是因为"不会失败"——库缺失会 ImportError——而是因为它的失败不归目录管：直接漏给全局处理器 → 500 `INTERNAL_ERROR`（SPEC 9.4，切分没有目录错误码，第 35 节⑤）。**T0308 给错误光谱做了最后一次扩展，并把"失败"分成两条哲学路径**：新码 `UNSUPPORTED_FILE_TYPE`（400，分发站第一次出现 4xx 目录码）；parse/OCR/embedding 的 AppError **原样穿管而过**（docstring 里的 Raises 列表就是"过境清单"）；而 0 chunk 则**不是错误**——`FAILED` 是返回值，是"管道跑完后的结果"之一（第 40 节③）。空/纯空白输入的拒绝权也终于在 T0308 被执行。

**调用方就位**：七个函数的第一个消费者 `IngestService.process` 已落地——"三层等待链"全部接通（parse_text_file → T0308、encode_chunks → T0308、add_texts → T0308，见第 6 节）。`_OCR_WARNINGS` 的 clear 生命周期也由 T0308 兑现（process 开头 `clear_ocr_warnings()`，每文件一次）。

---

## 1. Phase 3 定位与 T0301 分工

### 整条 Ingest Pipeline 中，T0301 站在哪里

CLAUDE.md 的 Ingestion Invariants 规定了 v1 的文件入库管道（共 8 站）：

```text
Validate → Save → Parse → Clean → Chunk → Embed → Store → Invalidate keyword index
（校验）  （落盘） （解析）  （清洗） （切分） （向量化）（存储） （关键词索引失效）
```

- **Validate / Save** 是 Phase 5（File Upload API）的活——校验文件名、大小，把文件保存到 `uploads/`
- **Parse** 是 Phase 3 的活——**T0301 就站在 Parse 站**，而且只负责这一站的"文本类"这一块
- **Clean（F005）/ Chunk（F006）** 也是 Phase 3 的活——当时还是"后面的 Task"（现在均已落地：T0306 见第 27–31 节、T0307 见第 32–36 节）
- **Embed** 已经就绪——Phase 2 的 `encode_chunks` 在这里等着（第 6 节）

### T0301–T0305：Parse 站的五块拼图

SPEC F003 的"包含"清单列出了 5 类格式，对应 Phase 3 的 5 个解析 Task：

| Task      | 格式                                       | 解析方式                 | 状态     |
| --------- | ---------------------------------------- | -------------------- | ------ |
| **T0301** | `.txt` / `.md` / `.csv` / `.json` / `.log` | 一律纯文本读取 + 编码级联       | ✅ DONE |
| **T0302** | `.docx`                                  | python-docx：段落 + 表格  | ✅ DONE |
| **T0303** | `.xlsx` 等                                | openpyxl：多 sheet 遍历  | ✅ DONE |
| **T0304** | `.pdf`                                   | PyMuPDF 原生文本逐页提取     | ✅ DONE |
| **T0305** | PDF 图片页                                  | Qwen-VL OCR fallback | ✅ DONE |

### 一条 v1 铁律：CSV/JSON 不做结构化解析

SPEC F003 Define 的"不包含"写着：**CSV/JSON 结构化解析**。Detail 3.1 第 4 条再次强调：

> CSV/JSON 在 v1 中作为普通文本读取，**不进行结构化解析**

这个决定值得单独拎出来看：`.csv` 和 `.json` 明明有成熟的结构化解析库（Python 标准库就有 `csv` / `json` 模块），SPEC 为什么故意不用？

- **范围控制**：结构化解析会带来 schema 设计、嵌套对象怎么转文本、超大文件流式读取等一系列新问题。v1 的目标是"知识库问答"，不是"数据分析导入"
- **效果可接受**：RAG 的知识来源是文本语义。把 JSON 原样当文本切块喂给 embedding，对问答场景足够
- 前端视角类比：这就像产品砍需求——"v1 不做富文本编辑器，textarea 就够"，不是技术做不到，是**不划算**

这也是阅读这份代码时最重要的前提：**`.csv` / `.json` / `.log` / `.md` 没有特殊待遇**，5 种扩展名走完全相同的代码路径。

### 一个边界声明：扩展名分发不在这里

[ingest.py:62-64](../../backend/app/services/ingest.py#L62-L64) 的 docstring 写明：

```
Extension-based dispatch to these parsers is owned by the ingest pipeline
(a later task) — this module only provides the parsing functions.
```

翻译：**"按扩展名决定调用哪个 parser"这件事，归后面的 ingest 管道管（T0308）——本模块只提供解析函数。**（T0308 落地后这句 "(a later task)" 已过期：`IngestService._parse` 已把分发写进本文件——实现注释没同步更新，见 Pending #23。）

所以 `parse_text_file` 自己不看扩展名、不判断"这个文件是不是 txt"。它是被动的能力提供者。这延续了 Phase 2 确立的模块边界哲学：**模块只提供能力，不决定流程**。

---

## 2. 用 JS/TS 类比理解这份代码

在逐行精读之前，先用你已经会的 Node.js 知识建立直觉。这份解析逻辑（T0301 时代的 57 行版本）在 Node 世界里长这样：

```ts
// Node.js 版本（心智模型，不是逐行翻译）
import { readFileSync } from 'fs';
import { TextDecoder } from 'util';

function parseTextFile(filePath: string): string {
  let raw: Buffer;
  try {
    raw = readFileSync(filePath);            // ≈ Path.read_bytes()
  } catch (e) {
    throw new AppError('FILE_PARSE_ERROR');  // 读失败 → 422
  }

  const attempts: { encoding: string; error: string }[] = [];
  for (const encoding of ['utf-8', 'utf-16le', 'gbk']) {
    const fatal = encoding !== 'gbk';        // GBK 是最后兜底，不抛错
    try {
      // Node 没有内置 GBK —— 这是 Python 的第一个天然优势
      return decodeWith(encoding, raw, fatal);
    } catch (e) {
      attempts.push({ encoding, error: String(e) });
    }
  }
  throw new AppError('FILE_PARSE_ERROR', { details: { encoding_attempts: attempts } });
}
```

### 三个核心对照

**① `Path.read_bytes()` ≈ `fs.readFileSync(path)`**

| Python                   | Node.js                       | 返回                      |
| ------------------------ | ----------------------------- | ----------------------- |
| `file_path.read_bytes()` | `readFileSync(path)`          | `bytes`（Node: `Buffer`） |
| `file_path.read_text()`  | `readFileSync(path, 'utf-8')` | `str`（Node: `string`）   |

Python 的 `Path` 把"路径"做成对象（方法挂在路径上），Node 把操作做成独立函数（`fs` 模块）。两套哲学，做的事一样。

**② `.decode(encoding, errors=...)` ≈ `new TextDecoder(encoding, opts).decode(buf)`**

```ts
// TS：TextDecoder 默认 fatal: false —— 非法字节替换成 � (U+FFFD)，不抛错
new TextDecoder('utf-8', { fatal: true }).decode(buf);   // ≈ errors="strict"：抛错
new TextDecoder('utf-8', { fatal: false }).decode(buf);  // ≈ errors="replace"：替换成 �
// errors="ignore" 在 JS 没有直接等价物：Python 直接丢弃非法字节，连 � 都不留
```

`fatal: true` 就是你已有的直觉——"严格模式，解不开就报错"。Python 把它做成了 decode 的 `errors` 参数。

**③ Python 内置 GBK，Node 需要装 iconv-lite**

Python 标准库内置了 100+ 种编解码器（GBK、GB2312、GB18030、BIG5……），`"gbk"` 直接能用。Node 的 `TextDecoder` 在标准环境只有 UTF-8/UTF-16 等少量编码，GBK 要 `npm install iconv-lite`。

这是"老系统兼容"场景下 Python 的天然优势——**中文 Windows 生态的历史文件（GBK 编码）是 Python 标准库的一等公民**。DX-RAG 的编码级联能这么写，一半归功于此。

---

## 3. 逐行精读 ingest.py（T0301 部分）

文件：[ingest.py](../../backend/app/services/ingest.py)（686 行）。本节精读 T0301 的 `parse_text_file`（第 78–108 行），按 5 个片段展开；T0302 的 `parse_docx_file`（第 111–147 行）见第 14 节；T0303 的 `parse_excel_file`（第 150–191 行）见第 19 节；T0304/T0305 的 PDF 部分见第 24 节。

> 行号说明：T0302 完成时把文件头 docstring 重组为"文本 + DOCX 双契约"（1–25 行），`parse_text_file` 整体下移 7 行；T0303 完成时 docstring 再补 Excel 契约（1–30 行），`parse_text_file` 再下移 5 行；T0304/T0305 完成时 docstring 再补 PDF + OCR 两段（1–58 行），imports 也扩了 3 行（base64 / time / config），`parse_text_file` 再下移 16 行；T0308 完成时 docstring 再补 Ingest 管道段（1–65 行）、imports 加 1 行（datetime），全文件再下移 8 行（第 6 次偏移事件，见第 32 节"零偏移事件"的后续）。本节行号为当前（T0308 后）真实行号。

### 片段 0：docstring——八段契约（第 1–65 行）

```python
"""Document parsing — text file parser + DOCX parser (SPEC F003).

Text files (SPEC F003 3.1):
  v1 rule: .txt / .md / .csv / .json / .log are ALL read as plain text —
  no CSV/JSON structured parsing (SPEC F003 Define / Detail 3.1).

  Encoding cascade (SPEC F003 3.1):
    UTF-8 (strict) → UTF-16 (strict) → GBK (errors="ignore")
    UTF-8/UTF-16 are strict so a wrong guess FAILS and falls through to
    the next encoding instead of silently returning mojibake.

DOCX (SPEC F003 3.3):
  Paragraphs joined by "\n", then table text (cells joined by " " per
  row, rows by "\n"), all joined by "\n".  v1 adds NO synthetic table
  markers ([表格] etc.).

Excel (SPEC F003 3.4):
  openpyxl with data_only=True; per row cells joined by " " (None cells
  skipped), all-empty rows and all-empty sheets skipped, non-empty
  sheets joined by "\n".

PDF (SPEC F003 3.2):
  Per-page loop with PyMuPDF (fitz): native text via page.get_text();
  empty page → OCR fallback callback ocr_page(pdf_path, page_number)
  with 1-based page_number, or empty text; pages joined in order by
  "\n\n".  Encrypted PDF → ENCRYPTED_PDF.

OCR fallback (SPEC F004):
  Qwen-VL-Plus via DashScope MultiModalConversation; page rendered to
  JPEG, Base64 data-URI; retry on timeout/network/429/5xx (initial + 2
  retries, ~1s/~2s backoff per SPEC 9.3); 401/403 raise immediately;
  per-page failure → empty text + structured warning
  {page_number, error_code} in the module warning list.

Cleaning (SPEC F005):
  5 steps in order: splitlines → per-line strip → drop lines empty
  after strip → join with "\n" → empty result returns "".  An empty
  cleaned text is rejected by the ingest pipeline (a later task).
  v1 does NOT: HTML tag removal, special-char filtering, language
  detection, encoding conversion (handled in parsing).

Chunking & IDs (SPEC F006):
  Markdown header splitting (# → ## → ### → ####) for every file (F006
  Step 1 for .md, Step 2.1 for others), header path prefix
  "{path}\n\n{content}", oversized candidates re-split with
  RecursiveCharacterTextSplitter using the frozen separator list, short
  candidates pass through.  IDs (SPEC 7.1): file_id UUID4 per call,
  chunk_id UUID4 per chunk, chunk_index 0-based.

Ingest pipeline (SPEC F002/F004 — IngestService.process):
  parse (by extension, PDF with OCR fallback) → clean → chunk → embed
  → store, file_id generated at start.  Status model: SUCCESS /
  SUCCESS_WITH_WARNINGS / FAILED (0 chunks → FAILED with rollback:
  raw file deleted, delete_by_file; keyword index is the caller's
  concern).  Parse/OCR/embedding AppErrors propagate unchanged.

Error contract (SPEC F003 error table):
  - File missing/unreadable/corrupt → AppError("FILE_PARSE_ERROR") → 422
  - All encoding attempts fail → AppError("FILE_PARSE_ERROR") with
    details.encoding_attempts → HTTP 422

Extension-based dispatch to these parsers is owned by the ingest
pipeline (a later task) — this module only provides the parsing
functions.
"""
```

这和 embedding.py 的 docstring 是同一套路——**文件头 = 浓缩契约**，把 SPEC 的内容压缩成 65 行：

- **文本契约（T0301 建立）**：5 种扩展名一律纯文本读；级联 UTF-8（strict）→ UTF-16（strict）→ GBK（ignore），并解释了**为什么** strict 打前站——"错猜必须失败并降级，而不是静默返回乱码"
- **DOCX 契约（T0302 补充）**：段落 + 表格的拼接规则 + "无合成标记"的 v1 铁律
- **Excel 契约（T0303 补充）**：data_only=True、逐 sheet 逐行提取、None 单元格跳过、空行空 sheet 跳过、sheet 间 "\n" 连接
- **PDF 契约（T0304 补充）**：逐页循环、原生文本 vs OCR fallback 回调（**冻结了 ocr_page(pdf_path, page_number) 的 1-based 页码契约**）、页间 "\n\n" 连接、加密 → ENCRYPTED_PDF
- **OCR 契约（T0305 补充）**：Qwen-VL-Plus 调用、渲染 Base64、重试规则（初始 + 2 次、~1s/~2s 退避）、401/403 不重试、页级失败 → 空文本 + 结构化 warning
- **清洗契约（T0306 补充）**：5 步顺序（splitlines → strip → 滤空行 → join → 空结果返回 ""）+ 5 条不做（HTML 标签、特殊字符、语言检测、编码转换、脱敏）
- **切分契约（T0307 补充）**：两段式切分（标题优先、超长递归再切）+ header path 前缀 + ID 规则（file_id 每调用一个、chunk_id 每块一个、chunk_index 0-based——教学见第 32–36 节）
- **管道契约（T0308 补充）**：五站顺序（parse → clean → chunk → embed → store）、file_id 在管道顶端生成、三态判定（SUCCESS / SUCCESS_WITH_WARNINGS / FAILED）、FAILED rollback 边界（删原始文件 + delete_by_file，keyword index 归调用方）、AppError 原样传播——**docstring 第一次描述了"本文件自己的行为"，而不再只是"本文件提供的函数们"**（第 37 节）
- **错误契约**：FILE_PARSE_ERROR 422；编码全败带 `details.encoding_attempts`
- **边界声明**：扩展名分发不归我管（T0302 后注意用词从 "this parser" 变成了 "these parsers"——一个文件里多个解析器了；T0308 后这句已过期，见 Pending #23）

> 历史对照：T0301 完成时的 docstring 只有文本部分（18 行）。T0302 把标题改成 "text file parser + DOCX parser"、补上 DOCX 段、错误契约合并为一条；T0303 再补 Excel 段（5 行）；T0304/T0305 再补 PDF 段（5 行）+ OCR 段（6 行）；T0306 补 Cleaning 段（7 行）、T0307 补 Chunking 段（7 行）；T0308 补 Ingest 管道段（7 行）——**docstring 跟着功能走**，这正是"文件头 = 当前契约快照"的体现。（不过标题还是 "text file parser + DOCX parser"、没跟上后面的功能——见第 21 节 Pending Question #5，T0308 后这个问题第三次升级：八个功能，标题只写了两个。）

> 学习提示：读到任何一个项目文件，**先读 docstring**。它通常在说"这段代码兑现了 SPEC 的哪几条"。Phase 2 的 embedding.py 如此，这里同样如此。

### 片段 1：imports——pathlib 首次进项目（第 67–75 行）

```python
import base64
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.core.config import settings
from app.core.errors import AppError
```

- `from pathlib import Path`——**`pathlib` 是 Python 3.4+ 的标准路径库**，这是它第一次在项目里出现（Phase 0 的 config.py 用的是字符串路径）。`Path` 是一个类：`Path("data/a.txt")` 得到一个路径对象，上面挂着 `read_bytes()`、`read_text()`、`exists()`、`parent` 等方法。TS 类比：`node:path` 的纯函数 + `fs` 的操作，合并成一个对象 API
- `from typing import Dict, List`——两个类型标注用：`List[Dict[str, str]]`（尝试记录表）
- **T0304/T0305 新加的三组 import**（第 60–67 行从 4 行扩成 7 行）：
  - `import base64`——OCR 图片编码（标准库，第 24 节片段详解）
  - `import time`——重试退避的 `time.sleep`（标准库）
  - `from typing import Any, Callable, Optional`——`Optional[Callable[[Path, int], str]]` 回调标注（`Any` 是警告字典的值类型；`Callable` 见手册 22.2）
  - `from app.core.config import settings`——**第一次在服务层用配置单例**（`settings.get_dashscope_key()`，OCR 需要 API key）
- `AppError`——老朋友（Phase 0 T0004 建立），这里多个 raise 都要用
- **T0307/T0308 续扩**：`import uuid`（T0307 的 UUID 身份体系）+ `from datetime import datetime, timezone`（T0308 的 upload_time，第 37 节）——datetime 是**标准库的"日期时间"模块**，`datetime` 既是模块名也是类名（`datetime.datetime.now(...)` 的简写靠 from-import 拆开，见手册 25.2）

### 片段 2：函数签名 + 读文件（第 78–98 行）

```python
def parse_text_file(file_path: Path) -> str:
    """Parse a text-format file (.txt/.md/.csv/.json/.log) to plain text.
    ...
    """
    try:
        raw = file_path.read_bytes()
    except OSError as exc:
        raise AppError("FILE_PARSE_ERROR") from exc
```

逐点看：

**`file_path: Path`**——参数类型是 `Path` 对象而不是 `str`。调用方要传 `Path("uploads/xxx.txt")` 而不是字符串路径。这是 pathlib 的惯例：**类型本身就是路径语义**，比裸 `str` 更安全（TS 类比：用 `type FilePath = string` 的 branded type，而不是裸 string）。

**`raw = file_path.read_bytes()`**——一次性把整个文件读成 `bytes`。注意是 `read_bytes`（读二进制）不是 `read_text`（按编码读文本）——**为什么？** 因为这个函数的核心工作就是"自己猜编码"，`read_text` 默认按 UTF-8 读，猜错了没机会补救。先拿原始字节，再自己决定怎么解。

> 为什么敢一次性读全文件？因为文件大小在上传层有 `MAX_UPLOAD_SIZE_MB` 兜底（Phase 5 的 Validate 站），能走到这里的文件不会太大。v1 不需要流式读取。

**`except OSError as exc:`**——`OSError` 是 Python 的"系统调用失败"异常基类，覆盖文件不存在（`FileNotFoundError`）、权限不足（`PermissionError`）、磁盘错误等一切"读不了"的情况。**这是项目里第一次按具体类型捕获异常**——T0201 写的是 `except Exception`（全收）。对比：

|      | T0201 embedding.py | T0301 ingest.py                          |
| ---- | ------------------ | ---------------------------------------- |
| 捕获   | `except Exception` | `except OSError` / `except UnicodeDecodeError` |
| 意图   | 模型加载任何失败都翻译成一个错误码  | 按失败类型分流：读不了 vs 解码失败                      |

**`raise AppError("FILE_PARSE_ERROR") from exc`**——`from exc` 异常链（T0201 已学过）：把 OSError 翻译成项目错误码，同时保留根因在 traceback 里。这里不带 `details`——文件读不了，没什么结构化的上下文好带。

### 片段 3：编码级联循环（第 101–107 行）

```python
    attempts: List[Dict[str, str]] = []
    for encoding in ("utf-8", "utf-16", "gbk"):
        # GBK is the last resort: ignore undecodable bytes (SPEC F003 3.1)
        errors = "ignore" if encoding == "gbk" else "strict"
        try:
            return raw.decode(encoding, errors=errors)
        except UnicodeDecodeError as exc:
            attempts.append({"encoding": encoding, "error": str(exc)})
```

逐点看：

**`attempts: List[Dict[str, str]] = []`**——局部变量标注（T0107 学过：运行时完全不检查，纯给读者看）。这张表记录每次失败的尝试：`[{"encoding": "utf-8", "error": "..."}, ...]`。

**`for encoding in ("utf-8", "utf-16", "gbk")`**——元组字面量直接当迭代对象。顺序即优先级：先试最现代的 UTF-8，再试 Unicode 时代的 UTF-16，最后试中文 Windows 的遗留编码 GBK。

**`errors = "ignore" if encoding == "gbk" else "strict"`**——三元表达式（Python 和 JS 语法几乎一样，只是关键词不同）。GBK 是最后一级，用 ignore；前两级用 strict。

**`return raw.decode(encoding, errors=errors)`**——`bytes.decode()`：把字节按指定编码解成 `str`。**return 在 try 块里**——这是整个循环的胜负手：

- 解成功了 → 立刻 return，函数结束，循环**提前退出**
- 解失败了 → 抛 `UnicodeDecodeError` → 被 except 接住 → 记入 attempts → 循环继续试下一个

**循环能完整走完 = 三次全败**。这是 Python 里常见的"循环试到成功"模式——没有显式的 `break` 或成功标志变量，靠 `return` 直接退出。

**`except UnicodeDecodeError as exc:`**——第二个具体异常类型。`UnicodeDecodeError` 是"按这个编码解不开"的信号，专门区别于其他错误。**关键认知：解码失败在这里不是"事故"，是"信号"**——它告诉循环"这个编码猜错了，换下一个"。所以它不进 AppError，而是被记入 attempts。

**`attempts.append({"encoding": encoding, "error": str(exc)})`**——`str(exc)` 把异常对象转成可读字符串，比如：

```
'utf-8' codec can't decode byte 0xd6 in position 0: invalid continuation byte
```

（`0xd6` 是 GBK 中文字节——对 UTF-8 来说是非法的起始字节，一眼就能看出"这文件八成是 GBK"。）

### 片段 4：兜底 raise（第 108 行）

```python
    raise AppError("FILE_PARSE_ERROR", details={"encoding_attempts": attempts})
```

能执行到这一行，只有一种可能：**循环三次全败**。此时把整张失败记录表装进 `details`——这是全项目**第一次**给 AppError 的 `details` 传真实内容：

```json
{
  "error": {
    "code": "FILE_PARSE_ERROR",
    "message": "文件解析失败",
    "details": {
      "encoding_attempts": [
        {"encoding": "utf-8", "error": "'utf-8' codec can't decode byte 0xd6..."},
        {"encoding": "utf-16", "error": "'utf-16' codec can't decode..."},
        {"encoding": "gbk", "error": "'gbk' codec can't decode byte..."}
      ]
    }
  }
}
```

为什么值得带？**调试友好**：调用方看到 422，打开 details 就知道"三种编码都试过、各自为什么失败"——是文件真损坏，还是碰上了第四种编码（比如 Big5）？一眼可辨。

### 读完自检：4 个问题

1. 这份文件里一共有几个 `raise`？分别在第几行、什么条件下触发？
2. 循环里为什么没有写 `break`，却能在第一次成功时退出？
3. 哪个变量在成功路径上完全不会出现（不会进任何返回值）？
4. `read_bytes()` 的返回类型是什么？`decode()` 之后变成了什么？

（答案：① 2 个——98 行读失败、108 行三次全败。② `return` 直接结束函数，比 break 更彻底。③ `attempts`——只在失败时被填充。④ `bytes` → `str`。）

---

## 4. 编码级联深潜：为什么 strict 打前站、ignore 兜底

### 乱码（mojibake）是怎么产生的

先建立直觉。一个 GBK 编码的中文文件，字节是：

```
0xD6 0xD0 0xCE 0xC4      （GBK 的"中文"）
```

用 UTF-8 解它：`0xD6` 不是合法的 UTF-8 起始字节 → **抛错**（strict）。

但如果当初用的是 `errors="replace"` 或 `errors="ignore"`，解出来是 `"����"` 或空字符串——**"能读"，但不是原文**。更阴险的情况：有些错误字节组合恰好是合法字符，解出来是"读得通但全错的文字"。这种"悄悄成功"的坏结果，就是**乱码**。

### 为什么前两级必须 strict

[ingest.py:9-26](../../backend/app/services/ingest.py#L9-L26) 的 docstring 给出了答案：

> UTF-8/UTF-16 are strict so a wrong guess FAILS and falls through to the next encoding instead of silently returning mojibake.

**strict = 错猜必须"响亮地失败"，把机会让给下一级**。如果 UTF-8 对 GBK 文件用了 replace，就会静默返回一坨 �，级联到此终止——用户的知识库里全是乱码，而且没有报错、无从排查。

### 为什么最后一级 GBK 用 ignore

因为**已经没有下一级了**。GBK 是全村的希望：

- 如果 GBK 也 strict，解码失败 → 整个文件 FAILED → 用户收到 422。但 GBK 文件可能只是**个别字节损坏**，99% 内容可读
- 用 ignore，损坏字节被丢弃，**保住可读的绝大部分**——"宁丢字节，不丢文件"

这是 SPEC F003 3.1 的明示决策（"失败则尝试 GBK（errors='ignore'）"），实现忠实照抄。前端类比：图片加载失败的 `onError` fallback 链——前几张图加载失败要报错换源（strict），最后一张兜底图再失败就静默显示占位（ignore）。

### 为什么顺序是 UTF-8 → UTF-16 → GBK

30 秒中文编码史：ASCII（英文）→ GB2312 / GBK（中文 Windows 遗留）→ GB18030（国标扩充）→ Unicode 家族（UTF-8 / UTF-16，现代默认）。三种编码的实际来源：

| 编码     | 典型来源                                     | 在现代文件中的占比 |
| ------ | ---------------------------------------- | --------- |
| UTF-8  | 现代 Linux/macOS/Windows 10+ 默认            | 绝大多数      |
| UTF-16 | 老 Windows "Unicode 文本"（记事本"另存为 Unicode"） | 少见        |
| GBK    | 中文 Windows XP/7 时代的老文件                   | 遗留场景      |

**优先级 = 现实占比倒序**：最常见的先试，最罕见的最后试。每级 strict 都保证"猜错立刻换下一个"。

> 🔵 一个细节：Python 的 `"utf-16"` 解码依赖文件开头的 BOM（字节序标记）判断大小端。没有 BOM 的 UTF-16 文件可能解出乱码或报错——真实世界的 UTF-16 文件几乎都带 BOM，v1 不做无 BOM 探测。

### 级联 ≠ 检测（一个固有权衡）

严格说，这个级联是"**顺序尝试**"，不是"**编码检测**"。它有一个理论上的漏洞：

> 一个 GBK 文件，如果它的字节序列**恰好也是合法的 UTF-8**，会被按 UTF-8 解掉——解出来的不是原文（乱码），而且不会报错。

这种情况在实际中概率很低（GBK 双字节和 UTF-8 多字节的合法结构重叠极小），专业的编码检测（chardet 等库）能进一步降低误判，但 SPEC 明确选择了"顺序尝试"而非引入检测库——**v1 范围控制**。这是一个"SPEC 设计固有的权衡"，不是实现的 bug，记入第 11 节 Pending Questions。

---

## 5. 错误契约链路：FILE_PARSE_ERROR 的两条路径

### 完整链路图

```text
路径 A：文件读不了（第 95–98 行）
  read_bytes() 抛 OSError
    → except OSError 接住
    → raise AppError("FILE_PARSE_ERROR") from exc      [details 空 {}]
    → errors.py:56 查目录 → (422, "文件解析失败")
    → main.py 全局 handler → HTTP 422
    → {"error": {"code": "FILE_PARSE_ERROR", "message": "文件解析失败", "details": {}}}

路径 B：三种编码全败（第 101–107 行）
  utf-8 strict 失败 → utf-16 strict 失败 → gbk ignore 失败
    → raise AppError("FILE_PARSE_ERROR",
                     details={"encoding_attempts": [...]})   [第 108 行]
    → 同样的 422，但 details 里有完整尝试记录
```

### 目录里的位置

[errors.py:56](../../backend/app/core/errors.py#L72)：

```python
"FILE_PARSE_ERROR": (422, "文件解析失败"),
```

值得注意两点：

**① 422 第一次在项目服务层出现。** 此前各模块用的错误码是 400（校验类）、404、409、500。422（Unprocessable Entity）的语义是"请求格式没问题，但**内容处理不了**"——文件字节存在，但解不出来，用 422 恰如其分。这也是项目里第一个"业务处理失败"级别的 4xx。

**② `details` 第一次真正派上用场。** Phase 0 定义的 `ErrorDetail.details` 字段一直是空壳（T0105、T0201 的 raise 都没传 details）。SPEC F003 明确要求"携带 `details.encoding_attempts`"，T0301 兑现了它——**错误响应从"只有 code/message"进化到"带结构化上下文"**。当时预测"后续 Task（PDF 的 ENCRYPTED_PDF、OCR 的 warnings）会继续扩展这个模式"——**T0304/T0305 已兑现**：`ENCRYPTED_PDF` 让 Parse 站第一次出现非 FILE_PARSE_ERROR 的 422 码；OCR 的 `{page_number, error_code}` 结构化 warning 更是把"错误上下文"从 exception 的 details 扩展到了"正常响应旁的 warnings 通道"（第 22–26 节）。

### 与前一个错误码的对比

|         | EMBEDDING_MODEL_ERROR（T0201） | FILE_PARSE_ERROR（T0301）              |
| ------- | ---------------------------- | ------------------------------------ |
| 触发      | 模型加载失败                       | 读文件失败 / 三编码全败                        |
| HTTP    | 500                          | **422**                              |
| details | 空（不泄露内部异常）                   | 空（路径 A）/ **encoding_attempts（路径 B）** |
| 翻译方式    | `raise ... from exc`         | `raise ... from exc`（路径 A 同款）        |

T0201 的 details 刻意留空（模型内部异常不外泄）；T0301 的 details 刻意填充（编码尝试记录对排查有用）。**details 什么时候填、填什么，是每个错误码的独立契约**——SPEC 说了算。

---

## 6. 与前后 Phase 的连接

### 上游：文件从哪里来（Phase 5 的故事）

`parse_text_file` 接收一个 `Path`，但**文件是谁保存到磁盘上的？** 不是它。上游链是：

```text
Phase 5（T0501–T0503，未开始）
  HTTP 上传 → Validate（扩展名/文件名/大小校验）→ Save（写入 uploads/）
    → 拿到 Path
      → 调用 parse_text_file(Path)   ← 本函数
```

本模块对上游一无所知——它只承诺"给我一个文件路径，我给你文本"。**这种"不知道上游"的被动性是好事**：Phase 5 可以自由调整校验逻辑，本模块一行不用改（和 Phase 1 的 `add_texts` 不关心向量从哪来，同一哲学）。

### 下游：文本往哪里去（F005 → F006 → Phase 2）

返回的 `str` 会继续走管道：

```text
parse_text_file → str
  → T0306 文本清洗（F005，✅ 第 27–31 节）
  → T0307 切分 + chunk_id（F006，✅ 第 32–36 节）
  → T0308 编排接管道（F002/F004，✅ 第 37–41 节）
      → encode_chunks()（Phase 2，已就绪 ✅）
      → add_texts()（Phase 1，已就绪 ✅）
```

**"三层等待链"的第三环**：Phase 1 的 `add_texts` 等 Phase 2 的向量（已兑现）；Phase 2 的 `encode_chunks` 等 Phase 3 的文本（文本的第一个生产者 `parse_text_file` 就位了）；`parse_text_file` 又等 T0308 的编排来调用它——**T0308 落地后，三层等待链全部接上**。每一层的"无调用方"都是当时的常态——管道从中间向两端接，最后在 T0308 汇合。

### 一个分工细节：空文件不是 parser 的错

`read_bytes()` 读空文件得到 `b""`，`b"".decode(...)` 得到 `""`——空文件解析结果是空字符串，**不是错误**。为什么？

- 上传层的 `EMPTY_FILE`（0 字节）校验是 Phase 5 的活
- SPEC F003 3.3 提到"DOCX 无任何内容 → 返回空字符串，**后续清洗时拒绝**（见 F005）"——清洗站只"报告"空文本（返回 `""`），真正"拒绝"（FAILED 判定）是 T0308 编排的活（责任链，见第 30 节③）

**Parser 的职责是"忠实提取"，不是"内容把关"**。每个站只管自己的事，管道才能组合。

---

## 7. SPEC F003 3.1 逐条对照与验证

### 逐条对照表

SPEC F003 Detail 3.1 的 4 条要求 vs 实现：

| #    | SPEC 要求                      | 实现位置                                     | 结论                |
| ---- | ---------------------------- | ---------------------------------------- | ----------------- |
| 1    | 尝试 UTF-8 编码读取                | [ingest.py:101](../../backend/app/services/ingest.py#L101) 元组第一位 | ✅                 |
| 2    | 失败则尝试 UTF-16                 | 元组第二位                                    | ✅                 |
| 3    | 失败则尝试 GBK（`errors="ignore"`） | 元组第三位 + 79 行条件                           | ✅ 且仅 GBK 用 ignore |
| 4    | CSV/JSON 作为普通文本读取，不结构化解析     | 全文只有一个函数，无任何格式分支                         | ✅                 |

错误场景表对照：

| SPEC 错误场景                                | 实现                       | 结论   |
| ---------------------------------------- | ------------------------ | ---- |
| 文件无法打开/损坏 → 422 `FILE_PARSE_ERROR`       | 71–74 行 `except OSError` | ✅    |
| 编码检测全部失败 → 422 携带 `details.encoding_attempts` | 76–84 行                  | ✅    |

### 诚实 AC 验证（不虚构 PASS）

T0301 的 AC 是 **AC-F003-01**（UTF-8 txt → 正确文本）和 **AC-F003-02**（GBK txt → UTF-8/UTF-16 失败后 GBK 成功）。

**仓库没有自动化测试**（与前两个 Phase 一致的已知事实），因此这两个 AC 的数值/行为验证我**没有执行**，也**不虚构 PASS**。能做的只有代码审查层面的结构确认：

| 检查项                                 | 方式                          | 结果   |
| ----------------------------------- | --------------------------- | ---- |
| 级联顺序 = SPEC 的 UTF-8 → UTF-16 → GBK  | 读第 101 行元组                  | ✅ 一致 |
| errors 策略：strict 打前站、仅 GBK 用 ignore | 读第 103 行                    | ✅ 一致 |
| 全败时 details.encoding_attempts 携带    | 读第 108 行                    | ✅ 一致 |
| 读失败 → FILE_PARSE_ERROR              | 读第 95–98 行                  | ✅ 一致 |
| 空文件 → 空字符串（SPEC 未明说，行为良性）           | 逻辑推导（`b"".decode()` = `""`） | ✅ 合理 |

**一个好消息**：T0301 是项目里第一个**不依赖模型、不依赖网络、不依赖外部服务**的模块——学习者完全可以自己写个小脚本实测 AC-F003-01/02（见第 9 节练习 1）。我作为学习文档不虚构结果，但**你可以**亲手验证。

---

## 8. Python 新知识索引

T0301 引入的新 Python 概念，详细讲解都在 [python-for-frontend-dev.md](./python-for-frontend-dev.md) 第 20 节：

| 新概念                              | 一句话                                  | 手册位置 |
| -------------------------------- | ------------------------------------ | ---- |
| `pathlib.Path` + `read_bytes()`  | 路径对象 + 一次性读文件为 bytes                 | 20.1 |
| `bytes` vs `str`                 | Python 的二进制与文本是两种类型，靠 `.decode()` 转换 | 20.2 |
| `errors="strict"/"ignore"`       | 解码遇非法字节：抛错 / 丢弃                      | 20.3 |
| `OSError` / `UnicodeDecodeError` | 按具体类型捕获异常（项目第一次）                     | 20.4 |
| `str(exc)`                       | 异常对象转可读字符串                           | 20.5 |

已学概念的复习点：`raise ... from exc`（T0201，18.4）、局部变量标注（T0107）、三元表达式（JS 同款）。

---

## 9. 自测题与练习

### 自测题（10 道）

1. `parse_text_file` 的返回类型是什么？文件不存在时会发生什么（错误码 + HTTP 状态码）？
2. 编码级联的完整顺序是什么？每一级对应的 `errors` 策略是什么？
3. 为什么 UTF-8/UTF-16 用 strict、GBK 用 ignore？（各一句话）
4. TS 里 `TextDecoder` 的什么配置对应 Python 的 strict？什么行为在 JS 里没有直接等价物？
5. 一个 GBK 文件恰好也能按 UTF-8 解（不抛错），实现会按哪个编码解？这叫什么风险？这是 bug 吗？
6. `for encoding in (...)` 循环里没有 `break`，为什么第一次成功就能退出？
7. 两个 `raise` 分别在什么条件下触发？哪个的 `details` 有内容，装的是什么？
8. `raise AppError("FILE_PARSE_ERROR") from exc` 里的 `from exc` 有什么作用？
9. 为什么用 `read_bytes()` 而不是 `read_text()`？`bytes` 和 `str` 的根本区别是什么？
10. 空文件解析的结果是什么？为什么这不是错误、也不需要 parser 拒绝？

### 练习

1. **亲手跑一次级联**（T0301 无模型依赖，可直接执行）：用 Python 交互环境造一个 GBK 文件再解析——
   ```python
   from pathlib import Path
   Path("test_gbk.txt").write_bytes("中文测试".encode("gbk"))
   # 然后调用 parse_text_file(Path("test_gbk.txt"))，观察返回值与 attempts
   ```
   验证 AC-F003-02 的真实行为（UTF-8/UTF-16 失败 → GBK 成功）。
2. **Node 对比实验**：拿同一份 GBK 字节，在 Node 里用 `TextDecoder("utf-8")` 解一遍——观察默认 fatal:false 的行为与 Python strict 的差异；再试试不用 iconv-lite 能不能解出 GBK 原文。体会"Python 内置编解码器"这个差异。
3. **链路走读**：从 [ingest.py:108](../../backend/app/services/ingest.py#L108) 的 `raise` 出发，追到 [main.py:43-51](../../backend/app/main.py#L59-L67) 的 `app_error_handler`，写出三次全败场景下客户端收到的完整 JSON（含 details）。
4. **预测练习**（不要真改实现）：如果 SPEC 改成"UTF-8 用 `errors="replace"`"，一个 GBK 文件会发生什么？请描述字节级的过程，并说明为什么这违背了 docstring 的设计意图。

---

## 10. 快速复习卡

```text
T0301 — Text File Parser（parse_text_file，第 78–108 行）

一句话：读 bytes → 三级编码级联解成 str → 全败报 422 带尝试记录

数据形状：bytes → str（模块边界内完成翻译）
级联：utf-8 strict → utf-16 strict → gbk ignore（顺序 = 现实占比倒序）
strict 的意义：错猜必须响亮失败，把机会让给下一级（防乱码）
ignore 的意义：最后兜底宁丢字节不丢文件
两个 raise：
  98 行  OSError（读不了）→ 422，details 空
  108 行  三编码全败 → 422，details.encoding_attempts（每次尝试+失败原因）
铁律：CSV/JSON 纯文本读，不结构化解析（v1 范围控制）
边界：扩展名分发不归本模块管（已由 T0308 的 _parse 兑现，第 37 节）；空文件不是错误（T0308 判定 FAILED）
调用方：已就位——IngestService.process（第 37–41 节），三层等待链接上

新 Python 知识：Path/read_bytes、bytes vs str、errors=、具体异常类型、str(exc)
旧知识复习：raise from exc、局部变量标注、三元表达式
```

---

## 11. 进阶与 Pending Questions

### 🔵 进阶话题

- **UTF-16 与 BOM**：Python 的 `"utf-16"` 解码依赖文件头的 BOM 判断大小端；无 BOM 的 UTF-16 文件行为取决于平台字节序。真实世界的 UTF-16 文件几乎都带 BOM，v1 不做无 BOM 探测。
- **编码检测（chardet）**：顺序尝试是"猜"，chardet 等库是"检测"（按字节统计特征推断）。SPEC 选择前者是范围控制，不是不知道后者存在。
- **`for ... else` 语法**：Python 的循环可以带 `else` 子句（循环正常走完才执行，被 break/return 打断则不执行）——"三次全败"在有的代码风格里会写成 `else: raise ...`。本文件选择把 raise 放在循环外（第 108 行），语义等价。🟢 知道有这个语法即可，不要求用。（注意：这里说的是 **for-else**；T0305 的 ocr_page 用的是**另一种 else**——try/except/else，见手册 22.1。）

### Pending Questions（学习中发现，未修复，仅记录）

1. **GBK 文件恰好合法 UTF-8 的误判风险**：级联是顺序尝试而非检测，理论上存在"GBK 字节恰好构成合法 UTF-8 → 按 UTF-8 解出乱码且不报错"的窗口。SPEC 固有权衡（v1 不引入 chardet），非实现 bug。若未来用户反馈乱码，这是第一个排查方向。
2. **无自动化测试**：与 Phase 1/2 相同。AC-F003-01/02 未以测试形式固化为回归保护。学习者可手工验证（练习 1），但仓库本身没有。
3. **UTF-16 无 BOM 文件**：此类文件可能被 GBK 或报错路径处理，v1 未覆盖（SPEC 未要求）。
4. **`errors="ignore"` 的静默性**：GBK 兜底丢字节不产生任何警告（与 PDF OCR 的 warnings 机制不同——那是 F004 的明示要求）。若未来需要"解码质量"可观测性，可在 details 中附加丢失字节数。

### 下一个 Task 展望（仅高层，不提前教）

> 更新：T0303 已按预期落地（第 17–21 节）；T0304 也已落地（第 22–26 节）——当时的展望"PyMuPDF（fitz）逐页提取、空页触发 OCR（F004）、加密 PDF → 422"已全部兑现，`ENCRYPTED_PDF` 果然在等待后被启用（"目录先行、实现随后"的第三次应验）。

下一个是 **T0306（Text Cleaning）**：F005 文本清洗管道——逐行 strip、空行移除、空白归一化。清洗站将拒绝 parser 们交出的空文本（第 6 节的"空文件不是 parser 的错"在这里兑现），也是 SUCCESS_WITH_WARNINGS / FAILED 状态判定中"有效 Chunk"概念的第一站。

---

> **T0301 部分完**。你已会读 bytes 与 str、看懂编码级联、说出 FILE_PARSE_ERROR 的两条路径。继续第 12 节进入 T0302（DOCX 解析）。

---

## 12. T0302 定位：第二个函数加入文件

### 文件发生了什么变化

T0302 完成后，[ingest.py](../../backend/app/services/ingest.py) 从 57 行长到 103 行；T0303 再长到 151 行；T0304/T0305 再长到 354 行；T0306/T0307 落地后是 517 行；**T0308 落地后是 686 行**：

|                       | T0301 完成时   | T0302 完成时                  | T0303 完成时                | T0304/T0305 完成时            | T0306/T0307 完成时（当前）        |
| --------------------- | ----------- | -------------------------- | ------------------------ | -------------------------- | -------------------------- |
| docstring             | 18 行（纯文本契约） | 25 行（文本 + DOCX 双契约，错误契约合并） | 30 行（+ Excel 契约）         | 43 行（+ PDF 契约 + OCR 契约）    | 58 行（+ 清洗契约 + 切分契约）        |
| `parse_text_file`     | 第 26–56 行   | 第 33–63 行（内容零改动，仅下移 7 行）   | 第 38–68 行（再下移 5 行，依旧零改动） | 第 70–100 行（再下移 16 行，依旧零改动） | 第 70–100 行（再下移 16 行，依旧零改动） |
| `parse_docx_file`     | 不存在         | 第 66–102 行（37 行）           | 第 71–107 行（下移 5 行，内容零改动） | 第 103–139 行（下移 16 行，内容零改动） | 第 103–139 行（下移 16 行，内容零改动） |
| `parse_excel_file`    | 不存在         | 不存在                        | 第 110–151 行（42 行）        | 第 142–183 行（下移 16 行，内容零改动） | 第 142–183 行（下移 16 行，内容零改动） |
| `parse_pdf_file`      | 不存在         | 不存在                        | 不存在                      | 第 186–243 行（58 行）          | 第 186–243 行（下移 16 行，内容零改动） |
| OCR 基础设施 + `ocr_page` | 不存在         | 不存在                        | 不存在                      | 第 245–370 行（126 行）         | 第 245–370 行（下移 16 行，内容零改动） |

**重点：T0301 的函数一个字都没改**。T0302 只做了三件事——重组 docstring、加一个新函数、把错误契约的用词从 "File missing/unreadable" 扩成 "File missing/unreadable/corrupt"（因为现在还要涵盖损坏的 DOCX）。T0303 完全重复这套动作：docstring 补一段 Excel 契约、加一个新函数、旧函数零改动。T0304/T0305 照旧：docstring 补 PDF/OCR 两段、加新函数（和一个回调参数）、旧函数零改动。T0306/T0307 依旧照旧：docstring 补清洗/切分两段、加新函数、旧函数零改动。**新 Task 不碰旧函数的实现**，这个习惯在项目里一再出现（Phase 1 的 8 个 Task、Phase 2 的 T0202、Phase 3 的 T0302–T0307，都是"加"而不是"改"）。**T0308 第一次打破了这个习惯**：除了加 `IngestService` 类和补 docstring，它**改了** `chunk_text`——新增 `file_id: Optional[str] = None` 参数（"生成或接收"，TASKS T0307 原本就允许 "or receive from caller"）。"加"是默认，"改"需要理由——T0308 的理由是身份必须生成在管道顶端（第 40 节①）。

### T0302 在管道里的位置

和 T0301 完全相同——**Parse 站的第二个格式**。SPEC F003 Define 的输入/输出契约对两个函数一模一样：`Path` 进、`str` 出、失败都是 `FILE_PARSE_ERROR`。从调用方（T0308 的 `_parse`，第 37 节）视角看，两个 parser 的"外形"完全一致，只有内部提取逻辑不同——**这就是可替换性**：T0308 分发时只需按扩展名选函数，下游管道（清洗/切分/向量化）分不清文本来自 txt 还是 docx。

### 分工对比

|      | parse_text_file       | parse_docx_file                |
| ---- | --------------------- | ------------------------------ |
| 格式   | txt/md/csv/json/log   | docx                           |
| 输入形状 | 磁盘上的字节流               | **zip 容器**（含 XML 的压缩包）         |
| 关键库  | 无（标准库 `bytes.decode`） | **python-docx**（项目第一个文档解析第三方库） |
| 内容提取 | 全部字节                  | 段落 + 表格（不含图片/页眉页脚/批注）          |
| 编码问题 | 核心问题（级联）              | **不存在**（XML 自带编码声明，库处理）        |
| 失败形态 | 读不了 / 解码全败            | **任何异常**（损坏可能以十几种异常形态出现）       |

---

## 13. 用 JS/TS 类比理解 DOCX 解析

### DOCX 到底是什么：一个 zip 改名

先打破一个直觉：`.docx` **不是一个"文本格式"，是一个 zip 压缩包**。把它改成 `.zip` 解压，你会看到：

```text
document.docx
└─（解压后）
   ├─ [Content_Types].xml
   ├─ _rels/.rels
   ├─ word/
   │   ├─ document.xml      ← 正文内容在这里
   │   ├─ styles.xml        ← 样式
   │   └─ media/image1.png  ← 内嵌图片
   └─ docProps/             ← 元数据（作者、修改时间）
```

正文 `document.xml` 是一棵 XML 树：段落是 `<w:p>`，文字藏在 `<w:r><w:t>` 里，表格是 `<w:tbl>`。**直接解析它需要处理 XML 命名空间、样式继承、嵌套结构**——这是一整个领域的复杂度。

**python-docx 的角色**：把这个"zip + XML 的世界"翻译成普通 Python 对象——

```python
doc = Document("a.docx")
doc.paragraphs   # [<Paragraph>, <Paragraph>, ...] —— 一层抽象，挡住 w:p/w:r/w:t
p.text           # "Hello" —— 连 XML 都不用碰
doc.tables       # [<Table>, ...] —— w:tbl 的友好版本
```

### TS 类比：你在 Node 里解析 docx 需要什么

| Python                | Node.js                                  | 说明                          |
| --------------------- | ---------------------------------------- | --------------------------- |
| `python-docx`         | [mammoth.js](https://github.com/mwilliamson/mammoth.js)（docx → HTML/text） | 同定位：挡掉 zip+XML 细节           |
| `Document(str(path))` | `mammoth.convertToHtml({ path })`        | 传路径，拿结果                     |
| `doc.paragraphs`      | 无直接对应（mammoth 直接给结果）                     | python-docx 更"对象化"，按需取段落/表格 |
| zip 解压 + XML 遍历       | `jszip` / `adm-zip` + `DOMParser`        | 自己造轮子时才需要                   |

学习要点不是库 API（需要时查文档即可），而是**分层思想**：python-docx 之于 docx，就像 `JSON.parse` 之于 JSON 文本——你关心的是"段落有哪些、文字是什么"，不是"字节怎么组织的"。

### 为什么编码问题在 DOCX 这里不存在

T0301 的核心是编码级联。T0302 **完全没有编码问题**——因为 XML 文件自带编码声明（`<?xml version="1.0" encoding="UTF-8"?>`），python-docx 读 XML 时自动按声明解码。**不同格式的解析难点完全不同**：纯文本难在编码，DOCX 难在结构（zip+XML），Excel 难在**单元格值**（None 单元格、公式缓存、类型杂多——第 18 节），PDF 难在**"原生文本 vs 图片页"**（T0304/T0305，第 22 节起）。Parse 站的每个 Task 各打一场不同的仗。

---

## 14. 逐行精读 parse_docx_file（第 103–139 行）

### 片段 1：docstring 与签名（第 111–134 行）

```python
def parse_docx_file(file_path: Path) -> str:
    """Parse a .docx file to plain text (SPEC F003 3.3).

    Paragraphs and table cells are extracted as plain text:
    - Paragraphs: ``"\\n".join(p.text for p in doc.paragraphs)``
    - Tables: cells joined by ``" "`` within a row, rows by ``"\\n"``
    - Paragraphs and tables joined by ``"\\n"``
    - v1 adds NO synthetic table markers (SPEC F003 3.3 step 5)

    The ``python-docx`` import lives inside this function so that
    importing this module never fails when the package is unavailable —
    the failure surfaces on first use as FILE_PARSE_ERROR.

    Args:
        file_path: Path to the .docx file.

    Returns:
        Plain text of paragraphs and tables.  Empty DOCX → empty string
        (later rejected by cleaning, see F005).

    Raises:
        AppError: FILE_PARSE_ERROR (422) if the file cannot be opened or
            parsed (corrupt file, missing package, etc.).
    """
```

和 T0301 的 docstring 同款风格：**拼接规则直接写进 docstring**（三条 join 规则），**v1 铁律明示**（无合成标记），**空 DOCX 的去向写明**（空字符串 → F005 清洗时拒绝）。还多了一段**"为什么函数内 import"**的解释——见片段 2。

### 片段 2：打开文档（第 135–140 行）

```python
    try:
        from docx import Document

        doc = Document(str(file_path))
    except Exception as exc:
        raise AppError("FILE_PARSE_ERROR") from exc
```

三个教学点：

**① 函数内 import——T0201 的模式第二次出现。** [embedding.py:50](../../backend/app/services/embedding.py#L66) 的 `get_model()` 里 `from sentence_transformers import ...` 是同一个套路：**重依赖不进模块顶部**。好处照旧——import ingest 模块时永远不碰 python-docx；包没装也不炸，失败推迟到"第一次真用"时，以 `FILE_PARSE_ERROR` 的形态出现。

但注意一个**差异**：T0201 顶部还有 `if TYPE_CHECKING:` 的"假 import"（因为要标注 `SentenceTransformer` 类型）；T0302 **没有**——`parse_docx_file` 的签名只用到 `Path` 和 `str`，不需要引用任何 docx 类型。**需要类型标注时才需要 TYPE_CHECKING，不需要就一个函数内 import 足矣。**

**② `Document(str(file_path))`——`str()` 桥接。** python-docx 是老牌库（API 定型早于 pathlib 普及），它的 `Document()` 接受字符串路径（或文件对象）。项目内部用 `Path`（现代惯例），交接处用 `str(path)` 转换一下——**一行转换，两种惯例和平共处**。TS 类比：老库的 API 要 `string`，你手上是 `URL` 对象，传 `url.href`。新知识详解见手册 20.6。

**③ `except Exception`——这一次是"全收"而不是具体捕获。** 和 T0301 的 `except OSError` / `except UnicodeDecodeError` 形成对比（第 15 节展开）。理由先记住一句：**损坏的 zip 容器可能抛出十几种异常类型**（`PackageNotFoundError`、`BadZipFile`、`KeyError`、XML 解析错误……），逐个列举既脆弱又无意义——"打不开就 422"这个契约覆盖一切。

### 片段 3：段落提取（第 142 行）

```python
    paragraphs = [p.text for p in doc.paragraphs]
```

- `doc.paragraphs` → 库对象给的段落列表（`<Paragraph>` 对象的 list）
- `p.text` → 段落对象的属性，返回该段文字
- `[p.text for p in ...]` → **列表推导**（T0102 学过：≈ `.map()`），把 Paragraph 对象列表变成 `list[str]`

一句话：`doc.paragraphs.map(p => p.text)`（TS）。

### 片段 4：表格提取（第 143–146 行）

```python
    tables: List[str] = []
    for table in doc.tables:
        rows = [" ".join(cell.text for cell in row.cells) for row in table.rows]
        tables.append("\n".join(rows))
    return "\n".join(paragraphs + tables)
```

嵌套结构逐层拆（从外到内）：

| 层       | 代码                                       | 结果形状             |
| ------- | ---------------------------------------- | ---------------- |
| 表格集合    | `doc.tables`                             | `[<Table>, ...]` |
| 单个表格    | `table.rows`                             | `[<Row>, ...]`   |
| 单行      | `row.cells`                              | `[<Cell>, ...]`  |
| 单元格     | `cell.text`                              | `str`            |
| 行内拼接    | `" ".join(cell.text for cell in row.cells)` | 一行一个 `str`       |
| 行间拼接    | `"\n".join(rows)`                        | 一个表格一个 `str`     |
| 段落+表格拼接 | `"\n".join(paragraphs + tables)`         | 最终一个 `str`       |

**新语法两处**：

- **`" ".join(可迭代对象)`**——Python 的 join 挂在**字符串**上（分隔符），JS 的 join 挂在**数组**上。方向相反，极容易写反：JS 是 `rows.join(" ")`，Python 是 `" ".join(rows)`。这是"最容易混淆"清单的新成员（手册 20.8）。
- **`(cell.text for cell in row.cells)`**——**生成器表达式**（generator expression）：圆括号版列表推导，不先造中间 list，直接喂给 `join()` 挨个取。惰性求值——`join` 消费多少取多少。手册 20.7。

**`paragraphs + tables`**——两个 list 用 `+` 拼接成一个（JS 的 `[...a, ...b]` / `a.concat(b)`），最后统一用 `"\n"` join。

### 读完自检：3 个问题

1. 段落和表格的先后顺序由谁决定？（段落全在前、表格全在后——**SPEC 固定**，见第 15 节）
2. 一个 3×2 的表格（3 行 2 列）最终在返回文本里占几行？（3 行——每行是 2 个 cell 用空格拼成的一个字符串）
3. 函数里 `from docx import Document` 为什么放里面？（重依赖不进模块顶部——T0201 模式复用）

---

## 15. 设计决策深潜：四个值得停下来看的选择

### ① 为什么 `except Exception` 全收，而不是像 T0301 那样按类型捕获

先回顾 T0301 的哲学：`except UnicodeDecodeError` 把"解码失败"当作**信号**（换下一个编码），所以必须和 `except OSError`（真失败）分流。

T0302 的情况完全不同：**没有"重试/降级"逻辑**。`Document()` 打不开就是打不开，契约只有一个——"任何失败 → 422"。而损坏的 docx（本质是损坏的 zip）失败形态千奇百怪：

```text
docx 损坏的可能异常形态（python-docx 内部各种层都可能炸）：
  zipfile.BadZipFile         ← zip 容器损坏
  PackageNotFoundError       ← 关键部件缺失（不是合法 docx）
  KeyError                   ← 引用的样式不存在
  XML 解析错误（各种）        ← word/document.xml 坏掉
  OSError                    ← 文件不存在/无权限
```

逐一 `except` 这些类型？**脆弱**——库升级可能换异常类型；**无意义**——反正结果都是 422。于是"全收 + `from exc` 保根因"是正确选择。**设计原则：按"是否需要分流处理"决定捕获粒度。** 需要分流（T0301：换编码继续）→ 具体捕获；不需要分流（T0302：一律失败）→ 全收。

### ② 为什么 `str(file_path)` 而不是直接用 Path

python-docx 的 API 定型早于 pathlib（2008 vs 2014）。它接受的"路径"是 `str` 或文件对象。项目内部统一 `Path`，交接处 `str()` 桥接。**第三方库的 API 不由我们定，桥接一行就够**——不值得为"新库支持旧接口"而放弃内部的现代惯例。

### ③ 段落在前、表格在后——位置信息被丢掉了

SPEC F003 3.3 第 4 条固定了拼接顺序：**段落文本在前，表格文本在后**。这意味着一个"段落 → 表格 → 段落"的文档，提取结果是"所有段落 + 所有表格"——**表格在原文中的位置丢了**：

```text
原文：                   提取结果：
第 1 段                  第 1 段
┌表格┐                  第 2 段
第 2 段                  （表格内容整块排最后）
```

这是 SPEC 的**明示简化**（v1 不保留位置来源信息，与 PDF 的"不保留 page_number provenance"同一精神——见 SPEC 3.2 第 4 条）。语义检索场景下影响可控：chunk 里文字和位置本来就弱相关。但要知道这是**权衡**：如果一个文档的表格必须紧跟上下文才可读，v1 会损失这层结构。

### ④ 为什么禁止合成标记（`[表格]` 之类）

SPEC 3.3 第 5 条明确 SHALL NOT 添加 `[表格]` / `[/表格]` 标记。为什么？因为**下游是 embedding**——任何注入文本的标记都会变成向量的一部分。`[表格]` 三个字会参与切分、参与语义匹配，可能让"搜索'表格'这个词"命中无关文档。**语义管道的原则：提取的文本要"干净"，标记是污染。** 表格语义增强（标记、结构化保留）被 SPEC 明确划为 future work。

### 与 T0301 的横向对比总结

| 维度    | T0301 文本解析                          | T0302 DOCX 解析          |
| ----- | ----------------------------------- | ---------------------- |
| 核心难点  | 编码猜不猜得对                             | 结构（zip+XML）能不能打开       |
| 降级策略  | 有（三级编码级联）                           | 无（打不开就 422）            |
| 捕获粒度  | 具体（OSError / UnicodeDecodeError 分流） | 全收（异常形态不可枚举，无分流需求）     |
| 第三方库  | 无                                   | python-docx（首个文档解析库）   |
| 重依赖防护 | 无（标准库）                              | 函数内 import（T0201 模式复用） |
| 内容取舍  | 全部字节                                | 段落+表格（图片/页眉/批注丢弃）      |

**同一个 FILE_PARSE_ERROR，两种到达方式**——这正是"契约统一、实现各异"。

---

## 16. SPEC F003 3.3 对照、诚实 AC 与新知识索引

### SPEC 3.3 逐条对照

| #    | SPEC 要求                                  | 实现位置                                     | 结论     |
| ---- | ---------------------------------------- | ---------------------------------------- | ------ |
| 1    | 用 python-docx 打开                         | [ingest.py:136-138](../../backend/app/services/ingest.py#L136-L138) `from docx import Document` + `Document(str(file_path))` | ✅      |
| 2    | 段落：`"\n".join(p.text for p in doc.paragraphs)` | [ingest.py:142](../../backend/app/services/ingest.py#L142) 逐字一致 | ✅      |
| 3    | 表格：行内 cell 用 `" "` 连、行间用 `"\n"` 连        | [ingest.py:145-146](../../backend/app/services/ingest.py#L145-L146) | ✅      |
| 4    | 段落和表格用 `"\n"` 连接                         | [ingest.py:147](../../backend/app/services/ingest.py#L147) `"\n".join(paragraphs + tables)` | ✅      |
| 5    | v1 SHALL NOT 添加 `[表格]` 等合成标记             | 全文无任何标记注入                                | ✅      |
| —    | 文件无法打开/损坏 → 422 `FILE_PARSE_ERROR`       | [ingest.py:139-140](../../backend/app/services/ingest.py#L139-L140) | ✅      |
| —    | DOCX 无任何内容 → 空字符串 → 后续清洗拒绝               | 空文档 `paragraphs == []` 且 `tables == []` → `"\n".join([])` = `""` | ✅ 逻辑成立 |

> 注意第 2 条：SPEC 的伪代码和实现**逐字一致**（连 `p.text for p in doc.paragraphs` 都相同）——当 SPEC 给到伪代码级别时，实现忠实照抄，不"优化"。

### 诚实 AC 验证（T0302，不虚构 PASS）

T0302 的 AC 是 **AC-F003-04**（DOCX 含段落和表格 → 两者均被提取；行内 cell 以空格分隔）。仓库**没有自动化测试**（延续前两节的已知事实），且验证需要一个真实 docx 文件——**我没有构造测试文件，也没有虚构 PASS**。结构审查结论：

| 检查项           | 方式                           | 结果   |
| ------------- | ---------------------------- | ---- |
| 段落+表格都被提取并拼接  | 读第 141–147 行                 | ✅ 一致 |
| 行内 cell 以空格分隔 | 读第 145–146 行 `" ".join(...)` | ✅ 一致 |
| 无合成标记         | 全文搜索无 `[表格]` 等注入             | ✅ 一致 |
| 空 DOCX → 空字符串 | 逻辑推导（空 list join = `""`）     | ✅ 合理 |
| 损坏文件 → 422    | 读第 139–140 行                 | ✅ 一致 |

学习者可自验证：python-docx 已装在环境里（requirements.txt 由 T0001 声明），造一个含表格的 docx 跑 `parse_docx_file` 即可（比 T0301 的验证门槛稍高——需要一个真实的 docx 文件）。

### Python 新知识索引（→ 手册第 20 节）

| 新概念                     | 一句话                            | 手册位置 |
| ----------------------- | ------------------------------ | ---- |
| `str(path)` 桥接          | Path → 字符串，喂给只认 str 的老库 API    | 20.6 |
| 生成器表达式 `(x for x in y)` | 圆括号版列表推导：惰性、不造中间 list          | 20.7 |
| `"sep".join(iterable)`  | Python 的 join 在字符串上（与 JS 方向相反） | 20.8 |

已学概念复用：列表推导（T0102）、函数内 import（T0201，18.2）、`raise ... from exc`（T0201，18.4）、局部变量标注（T0107）。

### 自测题（8 道）

1. `.docx` 文件本质上是什么？python-docx 替我们挡掉了什么？
2. `from docx import Document` 为什么写在函数里面？这和 T0201 的哪个模式相同？T0302 为什么不需要 `TYPE_CHECKING`？
3. `Document(str(file_path))` 里为什么要有 `str()`？
4. T0302 为什么用 `except Exception` 全收，而 T0301 按类型捕获？设计原则一句话是什么？
5. 一个"段落 → 表格 → 段落"的文档，提取结果是什么顺序？这是 bug 还是 SPEC 明示简化？
6. `" ".join(cell.text for cell in row.cells)` 中圆括号里的表达式叫什么？它和列表推导的区别？
7. JS 的 `rows.join(" ")` 翻译成 Python 怎么写？（注意方向）
8. 为什么 v1 禁止在表格前后加 `[表格]` 标记？（下游是谁？）               

### 练习（T0302）

1. **亲手跑一次**：在 Python 里用 python-docx 造一个"一段文字 + 一个 2×2 表格"的 docx（`Document()` → `add_paragraph()` → `add_table()` → `save()`），再调 `parse_docx_file` 观察输出顺序与行内空格。
2. **zip 解剖实验**：把一个 docx 复制成 `.zip` 解压，找到 `word/document.xml`，搜一段你写的文字——亲眼确认"docx = zip + XML"。
3. **错误路径走读**：把练习 1 的 docx 用文本编辑器破坏几个字节，再调 `parse_docx_file`，观察它落在 `except Exception` 的哪个形态（traceback 里 `__cause__` 是什么）。

### T0302 快速复习卡

```text
T0302 — DOCX Parser（parse_docx_file，第 103–139 行，37 行）

一句话：python-docx 打开 zip+XML 容器 → 段落在前、表格在后 → 拼接成干净 str

本质认知：docx = zip 压缩包（word/document.xml 是正文）；库负责挡 XML
提取规则：段落 "\n" join；表格 行内 " "、行间 "\n"；段落+表格 "\n" join
铁律：无合成标记（标记会污染 embedding 语义）
错误：任何失败 → except Exception 全收 → 422 FILE_PARSE_ERROR（无降级，故无需分流）
空文档 → ""（F005 清洗时拒绝）
模式复用：函数内 import（T0201 第二次出现）
新语法：str(path) 桥接、生成器表达式、字符串上的 .join()
```

---

> **T0302 部分完**。Parse 站已完成 2/5：文本（T0301）+ DOCX（T0302）。两个 parser 外形一致（Path 进、str 出、同一错误码），内部各打各的仗——文本打编码战、DOCX 打结构战。继续第 17 节进入 T0303（Excel 解析）。

---

## 17. T0303 定位：第三个函数加入文件

### 文件发生了什么变化（T0303）

T0303 完成后，[ingest.py](../../backend/app/services/ingest.py) 从 103 行长到 151 行；T0304/T0305 后再长到 354 行；T0306/T0307 落地后是 517 行；T0308 落地后是 686 行（完整历史表见第 12 节）：

|                        | T0301 完成时   | T0302 完成时           | T0303 完成时                | T0304/T0305 完成时            | T0306/T0307 完成时（当前）        |
| ---------------------- | ----------- | ------------------- | ------------------------ | -------------------------- | -------------------------- |
| docstring              | 18 行（纯文本契约） | 25 行（文本 + DOCX 双契约） | 30 行（+ Excel 契约）         | 43 行（+ PDF + OCR 契约）       | 58 行（+ 清洗 + 切分契约）          |
| `parse_text_file`      | 第 26–56 行   | 第 33–63 行（下移 7 行）   | 第 38–68 行（再下移 5 行，依旧零改动） | 第 70–100 行（再下移 16 行，依旧零改动） | 第 70–100 行（再下移 16 行，依旧零改动） |
| `parse_docx_file`      | 不存在         | 第 66–102 行（37 行）    | 第 71–107 行（下移 5 行，内容零改动） | 第 103–139 行（下移 16 行，内容零改动） | 第 103–139 行（下移 16 行，内容零改动） |
| `parse_excel_file`     | 不存在         | 不存在                 | 第 110–151 行（42 行）        | 第 142–183 行（下移 16 行，内容零改动） | 第 142–183 行（下移 16 行，内容零改动） |
| `parse_pdf_file` + OCR | 不存在         | 不存在                 | 不存在                      | 第 186–370 行                | 第 186–370 行（下移 16 行，内容零改动） |

**"加"而不是"改"，第七次应验。** T0303 做了三件事：docstring 补一段 Excel 契约、加一个新函数、旧函数一个字没动。T0304/T0305 照旧，T0306/T0307 依旧照旧。至此，"新 Task 不碰旧函数的实现"从个案变成了铁律——连续七个 Task 零改动累加，`parse_text_file` 从 T0301 完成起**一行都没变过**，只是被 docstring 推着挪了四次位置。

### T0303 在管道里的位置

和 T0301/T0302 完全相同——**Parse 站的第三个格式**。SPEC F003 Define 的输入/输出契约三个函数一模一样：`Path` 进、`str` 出、失败都是 `FILE_PARSE_ERROR`。从调用方（T0308 的 `_parse`）视角看，三个 parser 的"外形"完全一致，只有内部提取逻辑不同——**可替换性**扩展到三函数：T0308 分发时只需按扩展名选函数，下游管道（清洗/切分/向量化）分不清文本来自 txt、docx 还是 xlsx。

### 三函数分工对比

|        | parse_text_file     | parse_docx_file  | parse_excel_file            |
| ------ | ------------------- | ---------------- | --------------------------- |
| 格式     | txt/md/csv/json/log | docx             | xlsx/xlsm/xltx/xltm         |
| 输入形状   | 磁盘字节流               | zip 容器（OOXML 文档） | **zip 容器（OOXML 表格）**        |
| 关键库    | 无（标准库）              | python-docx      | **openpyxl**                |
| 内容提取   | 全部字节                | 段落 + 表格          | **所有非空 sheet 的单元格文本**       |
| 编码问题   | 核心问题（级联）            | 不存在（XML 声明）      | **不存在（同 DOCX）**             |
| 失败形态   | 读不了 / 解码全败          | 任何异常（zip 损坏）     | **任何异常（zip 损坏）**            |
| 格式特有难点 | —                   | 段落表格顺序（SPEC 固定）  | **None 单元格 / 公式缓存 / 值类型杂多** |

---

## 18. 用 JS/TS 类比理解 Excel 解析

### XLSX 的本质：又一个 zip 容器

第 13 节学的"DOCX = zip + XML"在这里**直接复用**：`.xlsx`（以及 `.xlsm`/`.xltx`/`.xltm`）是**同一个家族**——Microsoft 的 OOXML（Office Open XML）格式族，全部是 zip 容器。把 xlsx 改名 zip 解压：

```text
report.xlsx
└─（解压后）
   ├─ xl/
   │   ├─ workbook.xml          ← 有哪些 sheet、叫什么名
   │   ├─ worksheets/sheet1.xml ← 每个 sheet 的单元格
   │   └─ sharedStrings.xml     ← 文本池（重复字符串去重存储）
   └─ docProps/                 ← 元数据
```

- docx 的正文藏在 `word/document.xml`；xlsx 的单元格藏在 `xl/worksheets/sheetN.xml`。**同族格式，换了个目录名。**
- 所以第 13 节的知识完全迁移：**编码问题不存在**（XML 自带声明）、损坏 = zip 损坏（十几种异常形态）、库（openpyxl）替我们挡 XML。
- **为什么 `.xls` 被 SPEC 划出范围**：`.xls` 是 Excel 97–2003 的遗留**二进制**格式（BIFF），和 OOXML 毫无关系——openpyxl 根本不支持它。"库不支持 + 格式已死"双重理由，v1 不做（SPEC 明示 Out of Scope）。

### openpyxl ≈ Node 里的什么

| Python                           | Node.js                                  | 说明          |
| -------------------------------- | ---------------------------------------- | ----------- |
| `openpyxl`                       | [SheetJS](https://sheetjs.com/)（社区版 `xlsx`） | 同定位：读写 xlsx |
| `load_workbook(path)`            | `XLSX.readFile(path)`                    | 打开工作簿       |
| `ws.iter_rows(values_only=True)` | `XLSX.utils.sheet_to_json(ws, {header: 1})` 的逐行版 | 逐行拿值        |
| `wb.worksheets`                  | `wb.Sheets`（对象，需 `Object.keys` 遍历）       | sheet 集合    |

学习要点依旧**不是 API 本身**，而是分层思想：openpyxl 之于 xlsx，就像 python-docx 之于 docx——你关心的是"哪个 sheet、每行有哪些值"，不是"XML 怎么组织的"。

### Parse 站的三场仗

T0301 打**编码战**（字节怎么解成字符），T0302 打**结构战**（zip+XML 怎么变成段落和表格），T0303 打的是**单元格值战**：

- **None 单元格**：空格子、以及"没有缓存值的公式格"（见第 20 节①），都要跳过——但不能误杀 0（见第 20 节②）
- **公式 vs 值**：`data_only=True` 决定读哪个（第 20 节①）
- **值类型杂多**：同一个 sheet 里 int / float / datetime / str / bool 共存，必须 `str()` 统一（手册 21.5）

同一个"文件 → 文本"的契约，三种完全不同的世界——**Parse 站的乐趣正在于此**。

### 从 Sheet 的角度看数据形状（四级嵌套）

DOCX 是三层（表格 → 行 → 单元格），Excel 是**四层**：

```text
workbook（工作簿）→ worksheet（工作表）→ row（行元组）→ cell（单元格值）
  wb.worksheets       ws.iter_rows(...)      row               cell
```

每往下一层，粒度细一级。最终目标是**把四级结构压扁成一个 str**——通过"行内 join + 行间 join + sheet 间 join"三级拼接（与 DOCX 的段落/表格拼接同款思路，但多了一层）。

---

## 19. 逐行精读 parse_excel_file（第 142–183 行）

### 片段 1：docstring 与签名（第 150–173 行）

```python
def parse_excel_file(file_path: Path) -> str:
    """Parse an Excel file (.xlsx/.xlsm/.xltx/.xltm) to plain text.

    SPEC F003 3.4:
    - openpyxl opened with ``data_only=True``
    - Iterate all sheets; per row cells joined by ``" "`` with ``None``
      cells skipped; all-empty rows skipped; all-empty sheets skipped
    - Non-empty sheet texts joined by ``"\\n"``

    The ``openpyxl`` import lives inside this function so that
    importing this module never fails when the package is unavailable —
    the failure surfaces on first use as FILE_PARSE_ERROR.
    ...
    """
```

和 T0301/T0302 同款 docstring 风格：**SPEC 条目照抄**（data_only、逐 sheet、None 跳过、空行/空 sheet 跳过、sheet 间 join——五条规则一句不少）、**函数内 import 的理由写明**、**错误契约写明**。文件头（1–65 行）也同步补了 Excel 段——"docstring 跟着功能走"第三次应验（第四次、第五次是 T0304/T0305 的 PDF/OCR 段）。

> 小观察：文件头第 1 行的标题还是 "text file parser + DOCX parser"——**漏了 Excel**。功能加了，标题没跟上。学习时发现，不修实现，记入 Pending Questions（第 21 节 #5）。

### 片段 2：打开工作簿（第 174–179 行）

```python
    try:
        from openpyxl import load_workbook

        wb = load_workbook(file_path, data_only=True)
    except Exception as exc:
        raise AppError("FILE_PARSE_ERROR") from exc
```

四个教学点：

**① 函数内 import——第三次出现，模式已成惯例。** T0201（sentence_transformers）、T0302（docx）、T0303（openpyxl），同一个套路连续三次：**重依赖不进模块顶部**。三次重复之后，这已经不只是"模式"，而是项目惯例——`ingest.py` 加第四个 parser 时，可以直接预测它的 import 也写在函数里。**预测兑现**：T0304 的 `import fitz`（第 230 行）、T0305 的 `import dashscope` / `import fitz` / `from dashscope import MultiModalConversation`（第 321–323 行）果然都写在函数里——惯例连续五次。

**② `load_workbook(file_path, ...)`——没有 `str()` 桥接！** 和 T0302 的 `Document(str(file_path))` 对比：这里**直接传 `Path` 对象**。openpyxl 是新一代库（与 pathlib 同期成长），API 直接支持 Path。**T0302 手册 20.6 曾预测"T0303 大概率也是同款"——预测被证伪**。教训：桥接只在"老库不认新类型"时需要，新库不需要。判断方法：看库文档的 `filename: str | Path`。

**③ `data_only=True`——本次 Task 的关键词。** 公式单元格读缓存值而不是公式文本（深潜见第 20 节①）。

**④ `except Exception` 全收——与 T0302 同理由。** xlsx 损坏 = zip 损坏，失败形态同样不可枚举（BadZipFile、KeyError、XML 错误……），同样无分流需求——"任何失败 → 422"一条契约覆盖。

### 片段 3：双循环骨架与行过滤（第 181–190 行）

```python
    sheet_texts: List[str] = []
    for ws in wb.worksheets:
        rows = []
        for row in ws.iter_rows(values_only=True):
            # SPEC 3.4: " ".join(str(cell) for cell in row if cell is not None)
            line = " ".join(str(cell) for cell in row if cell is not None)
            if line:  # skip entirely empty rows
                rows.append(line)
```

逐点看：

**`sheet_texts` 在外、`rows` 在内——聚合器的初始化位置 = 生命周期。** 外层聚合器（sheet_texts）在循环**外**初始化，全程累积；每 sheet 一个的聚合器（rows）在 sheet 循环**内**初始化——每个 sheet 从头攒一份行列表，攒满后推进外层。写在外层意味着跨 sheet 混行——所以位置不能换。

**`ws.iter_rows(values_only=True)`**：openpyxl 的逐行生成器。`values_only=True` 表示元组里是**单元格值**（int/float/str/None），默认 False 给 Cell 对象（要自己 `.value`）。TS 类比：`sheet_to_json({header: 1})` 的思想——逐行拿裸值。

**`" ".join(str(cell) for cell in row if cell is not None)`**：一行里同时发生三件事——**过滤**（`if cell is not None` 挡掉空格子）、**转换**（`str(cell)` 把数字/日期统一成文本）、**拼接**（`" ".join(...)` 空格连接）。执行顺序是**先过滤、后转换**：`if` 检查的是原始 cell，None 在 `str()` 之前就被挡掉。

**`if line:` 跳全空行**：一行全是 None（或被过滤到什么都没剩）时，join 结果是 `""`——空字符串是假值（T0202 真值判断），直接跳过。注意：这里用真值判断是**安全**的——值已经转成字符串了；0 的陷阱发生在**过滤之前**（`cell is not None` 已保住 0，`str(0)` = `"0"` 非空，不会误杀）。

### 片段 4：sheet 过滤与最终拼接（第 191 行）

```python
        if rows:  # skip entirely empty sheets
            sheet_texts.append("\n".join(rows))
    return "\n".join(sheet_texts)
```

**`if rows:` 跳全空 sheet**：一个 sheet 的所有行都被跳过时，rows 是空 list——假值（T0202 复用），整个 sheet 不进入结果。**AC-F003-05 的核心**（3 个 sheet、sheet2 全空 → 只出 sheet1 + sheet3）就是这一行实现的。

**`"\n".join(sheet_texts)`**：sheet 之间用换行连接。注意**没有 sheet 名标记**——和 DOCX"无合成标记"同一逻辑（SPEC 3.4 没提标记，v1 也不加；sheet 名是元数据，不是内容）。sheet 顺序保留（worksheets 的顺序），但**行列坐标丢失**——和 DOCX 丢表格位置同款权衡（第 20 节④）。

### 结构对比：三层拼接 vs DOCX 的两层

|      | T0302 DOCX        | T0303 Excel                |
| ---- | ----------------- | -------------------------- |
| 数据层级 | 3 层（表格→行→单元格）     | **4 层（工作簿→表→行→单元格）**       |
| 拼接次数 | 2 次（行内 + 行间/段落表格） | **3 次（行内 + 行间 + sheet 间）** |
| 过滤   | 无（段落表格全要）         | **两层过滤（空行、空 sheet）**       |
| 聚合器  | 无中间聚合（直接拼接）       | 一个中间聚合器（sheet_texts）       |

DOCX 是"**提取 → 拼接**"两步；Excel 是"**提取 → 过滤 → 拼接**"三步——过滤是 Excel 特有的：空行/空 sheet 是结构性噪声，SPEC 明示要跳过。

### 读完自检：3 个问题（T0303）

1. `data_only=True` 去掉会发生什么？（公式单元格变成 `=SUM(A1:A2)` 文本）
2. `if cell is not None` 改成 `if cell` 会发生什么？（0 单元格被误杀）
3. `rows = []` 为什么写在 `for ws` 里面而不是外面？（每 sheet 一份；写外面会跨 sheet 混行）

---

## 20. 设计决策深潜：四个值得停下来看的选择

### ① 为什么 `data_only=True`：值 vs 公式的取舍

Excel 公式单元格有两层内容：**公式文本**（`=SUM(A1:A2)`）和**上次保存时算好的缓存值**（42）。openpyxl 默认读公式文本；`data_only=True` 读缓存值。

**RAG 场景要值**：知识库要"用户看到的内容"。公式文本对语义检索没有意义——搜"42"不应该命中 `=SUM(...)`。所以 SPEC 3.4 第一条就锁定 data_only=True。

**⚠️ 代价（连锁反应）**：缓存值只在"用 Excel 打开过并保存"的文件里存在。**程序生成的 xlsx**（openpyxl 写、BI 工具导出）的公式格没有缓存 → data_only=True 读到 None → 被 `is not None` 过滤跳过。链条：**data_only → None → 跳过**。对 RAG 的影响：机器生成文件里的公式列可能整体消失（记入 Pending Questions #6）。SPEC 的取舍是"宁缺毋滥"——读不到值就跳过，绝不把公式文本混进知识库。

### ② 为什么 `cell is not None` 而不是 `if cell`：0 是合法值

这是本 Task 最核心的 Python 陷阱，也是 SPEC 伪代码里最微妙的一个词：

| 单元格值        | `if cell`（真值判断） | `cell is not None` |
| ----------- | --------------- | ------------------ |
| `None`（空格子） | 跳过 ✓            | 跳过 ✓               |
| `0`（合法数字）   | **跳过 ✗**        | 保留 ✓               |
| `0.0`       | **跳过 ✗**        | 保留 ✓               |
| `""`（空串）    | 跳过              | 保留（join 后无差别）      |
| `"0"`（文本零）  | 保留 ✓            | 保留 ✓               |

Python 的假值家族：`None`、`0`、`0.0`、`""`、`[]`、`{}`、`False`。如果写 `if cell`，**0 会被当成空格子丢掉**——财务表的"本期利润 0"就消失了。JS 的 `0` 同样是 falsy，坑法一致；正确姿势是 Python 用 `is not None`（T0201 的 is 身份比较）、JS 用 `!== null`。

**两条过滤线的分工**：`is not None` 挡"没有值"（0 是值！），`if line:` 挡"空文本"（已经是 str 了，空串才是没内容）。一个过滤值、一个过滤文本，各司其职。

### ③ 为什么没有 `str(file_path)` 桥接：预测被证伪的诚实记录

T0302 手册 20.6 写了一句预测："后续 T0303（openpyxl）大概率也是同款——老库认 str 路径。"**T0303 落地：`load_workbook(file_path, ...)` 直接传 Path，没有桥接。预测错了。**

原因：openpyxl 是 2010 年代的库，和 pathlib（2014）同期成长，API 直接支持 Path（底层 zipfile 自 Python 3.6 起接受 Path）；python-docx 是 2008 年的库，API 定型早于 pathlib。

教训两层：**桥接只在"老库不认新类型"时需要**；**学习文档的预测会错，错了就改**——这份文档的价值在于记录验证过的现状，预测单独标注、错了更新。

### ④ 位置信息又丢了一层：行列坐标与 sheet 名

和 DOCX 丢表格位置同款权衡：提取结果**保留 sheet 顺序、丢失行列坐标**（"第 3 行第 5 列"这个概念不存在于输出里），也不带 sheet 名标记。行内空格、行间换行、sheet 间换行——就是全部结构。v1 语义检索场景下影响可控（与 DOCX 的理由相同），但要知道：一个"列标题在左上角"的表，提取后标题和数据的关系只剩文本相邻。

### 横向对比总结（T0304/T0305 后扩展为五函数）

| 维度    | T0301 文本                            | T0302 DOCX       | T0303 Excel          | T0304 PDF       | T0305 OCR             |
| ----- | ----------------------------------- | ---------------- | -------------------- | --------------- | --------------------- |
| 核心难点  | 编码猜不猜得对                             | 结构（zip+XML）能不能打开 | 单元格值（None/公式缓存/类型）   | 原生文本 vs 图片页     | 外部 API 的不可靠性          |
| 降级策略  | 有（三级编码级联）                           | 无                | 无                    | 有（空页回调 OCR）     | 有（重试 3 次 → 页级放弃）      |
| 捕获粒度  | 具体（OSError / UnicodeDecodeError 分流） | 全收               | 全收                   | 全收 + 分场景 raise  | 具体分流（渲染 vs API vs 认证） |
| 第三方库  | 无                                   | python-docx      | openpyxl             | PyMuPDF（fitz）   | dashscope + fitz      |
| 重依赖防护 | 无（标准库）                              | 函数内 import       | 函数内 import（第三次）      | 函数内 import（第四次） | 函数内 import（第五次）       |
| 过滤    | 无                                   | 无                | 两层（空行、空 sheet）       | 空页 → OCR / 空串   | 失败页 → "" + warning    |
| 内容取舍  | 全部字节                                | 段落+表格（图片/页眉丢弃）   | 所有非空 sheet（公式无缓存时丢失） | 文本层（页面位置信息丢失）   | 仅无文本层的页面              |
| 失败形态  | 全有或全无（422）                          | 全有或全无（422）       | 全有或全无（422）           | 422 ×2 种        | 500 ×2 种 + 页级容错       |

**前三个函数：同一个 FILE_PARSE_ERROR，三种到达方式**——"契约统一、实现各异"。**T0304/T0305 打破了"全有或全无"**：Parse 站第一次有了"部分失败也算成功"的容错哲学（第 25 节③）。

---

## 21. SPEC F003 3.4 对照、诚实 AC 与新知识索引

### SPEC 3.4 逐条对照

| #    | SPEC 要求                                  | 实现位置                                     | 结论   |
| ---- | ---------------------------------------- | ---------------------------------------- | ---- |
| 1    | 用 openpyxl 打开（`data_only=True`）          | [ingest.py:175-177](../../backend/app/services/ingest.py#L175-L177) `from openpyxl import load_workbook` + `load_workbook(file_path, data_only=True)` | ✅    |
| 2    | 遍历所有 sheet                               | [ingest.py:182](../../backend/app/services/ingest.py#L182) `for ws in wb.worksheets:` | ✅    |
| 3    | 每行: `" ".join(str(cell) for cell in row if cell is not None)` | [ingest.py:186](../../backend/app/services/ingest.py#L186) **逐字一致**（连 `is not None` 都相同） | ✅    |
| 4    | 跳过全空行                                    | [ingest.py:187](../../backend/app/services/ingest.py#L187) `if line:` | ✅    |
| 5    | 所有 sheet 文本用 `"\n"` 连接返回                 | [ingest.py:190-191](../../backend/app/services/ingest.py#L190-L191) | ✅    |
| —    | 文件无法打开/损坏 → 422 `FILE_PARSE_ERROR`       | [ingest.py:178-179](../../backend/app/services/ingest.py#L178-L179) | ✅    |

> 注意第 3 条：SPEC 伪代码和实现**逐字一致**——这是 SPEC 给到伪代码级别的**第二次**逐字照抄（第一次是 DOCX 段落 join）。`is not None` 这个词不是实现者自己选的，是 SPEC 写好的——说明 SPEC 作者知道 0 的陷阱（第 20 节②）。

> 补充观察：SPEC 3.4 Detail 没写"跳过全空 sheet"（第 4 条只写了空行），但 AC-F003-05 要求 sheet2 全空被跳过——实现用 `if rows:` 兑现了 AC，比 SPEC 伪代码多一层过滤。**AC 也是契约的一部分**：伪代码没写全时，AC 补上。

### 诚实 AC 验证（T0303，不虚构 PASS）

T0303 的 AC 是 **AC-F003-05**（3 个 sheet、sheet2 全空 → sheet1 + sheet3 被提取，sheet2 被跳过）。仓库**没有自动化测试**（延续前三节的已知事实），且验证需要一个真实的 3-sheet xlsx 文件——**我没有构造测试文件，也没有虚构 PASS**。结构审查结论：

| 检查项                       | 方式                                 | 结果   |
| ------------------------- | ---------------------------------- | ---- |
| 遍历所有 sheet（3 个都过一遍）       | 读第 182 行 `for ws in wb.worksheets` | ✅ 一致 |
| 空 sheet 被跳过（sheet2 不产出文本） | 读第 189 行 `if rows:`                | ✅ 一致 |
| sheet1 + sheet3 内容保留、顺序保留 | 读第 190–191 行 append + join         | ✅ 一致 |
| None 单元格跳过                | 读第 186 行 `if cell is not None`     | ✅ 一致 |
| 损坏文件 → 422                | 读第 178–179 行                       | ✅ 一致 |

学习者可自验证：openpyxl 已在环境里（requirements.txt 第 7 行），造一个 3-sheet xlsx（sheet2 留空）跑 `parse_excel_file` 即可——**三个 parser 里验证门槛最低的一个**（不需要真实文档，程序就能造出合法测试文件，见练习 1）。

### Python 新知识索引（→ 手册第 21 节）

| 新概念                           | 一句话                                      | 手册位置 |
| ----------------------------- | ---------------------------------------- | ---- |
| `is not None` 过滤              | 判断"没有值"；⚠️ 0 是合法值且假值，真值判断会误杀             | 21.1 |
| 带过滤的生成器表达式                    | `(expr for x in xs if cond)`——先过滤、后转换    | 21.2 |
| `data_only=True`              | 公式单元格读缓存值不读公式文本；无缓存 → None               | 21.3 |
| `iter_rows(values_only=True)` | 逐行生成器 + openpyxl 直接收 Path（20.6 预测被证伪）    | 21.4 |
| `str(cell)` 多类型统一             | 单元格值 int/float/datetime/str 杂多，str() 统一（20.8 预防针兑现） | 21.5 |

已学概念复用：真值判断 `if line` / `if rows`（T0202，19.1）、`"sep".join`（T0302，20.8）、函数内 import（T0201，18.2）、`except Exception` 全收（T0302）、`raise ... from exc`（T0201，18.4）、局部变量标注（T0107，17.10）。

### 自测题（T0303，8 道）

1. `.xlsx` 和 `.docx` 是什么关系？`.xls` 为什么被 SPEC 划出范围？
2. `data_only=True` 读的是公式还是值？去掉它会怎样？程序生成的 xlsx 为什么公式格会读到 None？
3. `if cell is not None` 改成 `if cell` 会有什么 bug？举一个具体的单元格值。
4. 为什么 Excel 这里不需要 `str(file_path)` 桥接，而 DOCX 需要？
5. 一行 `" ".join(str(cell) for cell in row if cell is not None)` 里发生了哪三件事？执行顺序是什么？
6. 全空行和全空 sheet 分别在哪一行被跳过？各用了什么真值判断？
7. 提取结果里保留了哪些顺序、丢失了哪些信息？
8. `from openpyxl import load_workbook` 为什么写在函数里面？这是这个模式第几次出现？

### 练习（T0303）

1. **亲手验证 AC-F003-05**：用 openpyxl 造一个 3-sheet 的 xlsx（sheet1 两行数据、sheet2 全空、sheet3 一行含 0 和 None 的混合行），调 `parse_excel_file` 观察：sheet2 是否消失、0 是否保留、None 是否被跳过。
2. **公式实验**：造一个含公式的 sheet（`ws["A1"] = "=SUM(1,2)"`），分别用 `data_only=True` 和 `data_only=False` 打开，对比 A1 读到什么（一个 None、一个 `"=SUM(1,2)"`）——亲手确认"缓存值"机制。再用 Excel 打开保存一次后重跑，观察缓存出现。
3. **zip 解剖实验**：把练习 1 的 xlsx 复制成 `.zip` 解压，找到 `xl/worksheets/sheet1.xml` 和 `xl/sharedStrings.xml`，对比 docx 的 `word/document.xml`——确认"同族格式"。

### T0303 快速复习卡

```text
T0303 — Excel Parser（parse_excel_file，第 142–183 行，42 行）

一句话：openpyxl 打开 xlsx → 逐 sheet 逐行提取 → 两层过滤 → 拼接成干净 str

本质认知：xlsx = zip + XML（与 docx 同族 OOXML）；.xls 是遗留二进制，out of scope
提取规则：行内 " " join（None 跳过）、行间 "\n"、sheet 间 "\n"；空行空 sheet 跳过
铁律：data_only=True 读值不读公式；is not None 不误杀 0
错误：任何失败 → except Exception 全收 → 422 FILE_PARSE_ERROR（无降级）
模式复用：函数内 import（第三次）；"加"不改（第三次）
新语法：带过滤的生成器表达式、iter_rows(values_only=True)
```

### Pending Questions（T0303 新增，学习中发现，未修复，仅记录）

5. **文件头 docstring 标题未更新**：[ingest.py:1](../../backend/app/services/ingest.py#L1) 仍写 "text file parser + DOCX parser"，漏了 Excel。T0302 时改过一次标题，T0303 补了正文段但标题没跟上——docstring 的自描述滞后于内容。**T0304/T0305 后升级**：正文段已含 5 份契约（文本/DOCX/Excel/PDF/OCR），标题仍只写两个；**T0306 后再次升级**：正文段已含 7 份契约（再加清洗 + 切分），标题仍只写两个——滞后度随功能数增长。
6. **机器生成文件的公式格静默消失**：data_only=True + 无缓存 → None → 被过滤。BI 导出/程序生成的 xlsx 中公式列可能整体丢失，且没有任何警告（与 GBK ignore 的静默性同类问题，见第 11 节 Pending #4）。
7. **隐藏 sheet 也会被解析**：`wb.worksheets` 包含隐藏工作表。SPEC 写"遍历所有 sheet"，实现符合 SPEC——但"隐藏"通常是"不想被索引的内容"，v1 无法区分。
8. **workbook 未显式关闭**：openpyxl 官方建议用完后 `wb.close()` 释放文件句柄；本函数直接返回，靠 GC 回收。单次请求影响小，高并发上传场景可能积累句柄（T0308 编排时值得复查）。
9. **合并单元格只取左上角**：merged cells 的其余位置读为 None → 被跳过。合并单元格的内容不会丢失（在左上角），但"合并关系"信息丢失（与位置信息丢失同类权衡）。

---

> **T0303 部分完**。Parse 站已完成 3/5：文本（T0301）+ DOCX（T0302）+ Excel（T0303）。三个 parser 外形一致（Path 进、str 出、同一错误码），内部各打各的仗——文本打编码战、DOCX 打结构战、Excel 打单元格值战。下一站：T0304 + T0305 PDF 原生提取（PyMuPDF）+ Qwen-VL OCR fallback——Parse 站的第四场仗是"原生文本 vs 图片页"，而且它把 Parse 站的错误哲学从"全有或全无"升级成了"页级容错"（第 22 节起）。

---

## 22. T0304/T0305 定位：两个 Task、一个故事

### 为什么两个 Task 合并教学

前三个 Task 各讲各的格式（文本/DOCX/Excel），**T0304 和 T0305 是一个故事的上下半场**，无法分开讲：

- **T0304 建循环、留口子**：`parse_pdf_file` 负责逐页循环 + 原生文本提取，遇到"无原生文本的页"时**不自己处理**，而是调用一个回调参数 `ocr_page`
- **T0305 填实现**：`ocr_page` 就是那个回调的真身——渲染 → Base64 → Qwen-VL → 重试

分在两个 Task 里的原因在 TASKS.md 里写得很清楚：T0304 的 Out of Scope 是"Do NOT implement the OCR call itself (→ T0305)"。**先搭骨架、后填肉**——这是任务编排的艺术：T0304 完成时 parse_pdf_file 已经是一个**完整可测**的函数（传个假回调就能验证循环逻辑），T0305 的失败不会阻塞 T0304 的验证。

### 关键创新：回调契约在 T0304 被"冻结"

看 [ingest.py:216-219](../../backend/app/services/ingest.py#L216-L219) 的 docstring：

```
ocr_page: Optional per-page OCR fallback callback with the
    frozen T0305 contract ``ocr_page(pdf_path, page_number) ->
    str`` — called with the PDF path and the 1-based page
    number of a page whose native text is empty.
```

"**frozen T0305 contract**"——T0304 在 T0305 还没写的时候就**替 T0305 定了函数签名**：`ocr_page(pdf_path: Path, page_number: int) -> str`。T0305 落地时只能按这个签名实现（[ingest.py:284](../../backend/app/services/ingest.py#L284) 逐字吻合）。这是"接口先行"（interface-first）的工程实践：**先定契约，再各自实现**——和 Phase 1 的 ABC（T0101）同一种思想，但形态不同：ABC 用类继承声明接口，这里用**函数签名**声明接口。TS 类比：先写 `type OcrCallback = (pdfPath: string, pageNumber: number) => string;`，再让两个团队各自开发。

### 七函数 + 一服务类（T0308 后全景）

|        | parse_text_file     | parse_docx_file  | parse_excel_file    | parse_pdf_file                       | ocr_page                                 | clean_text      | chunk_text                   | IngestService                            |
| ------ | ------------------- | ---------------- | ------------------- | ------------------------------------ | ---------------------------------------- | --------------- | ---------------------------- | ---------------------------------------- |
| 格式     | txt/md/csv/json/log | docx             | xlsx/xlsm/xltx/xltm | pdf                                  | （PDF 的图片页）                               | （任意解析后文本）       | （清洗后的任何文本）                   | （编排以上全部）                                 |
| 输入形状   | 磁盘字节流               | zip 容器（OOXML）    | zip 容器（OOXML）       | **排版指令 + 可选文本层**                     | PDF 页渲染图                                 | **str（原始解析文本）** | **str（干净文本）**                | **Path + str + str（file_path, file_name, collection_name）** |
| 输出形状   | str                 | str              | str                 | str                                  | str                                      | str             | **List[dict]（第一次分叉）**        | **dict（五键，第二次分叉）**                       |
| 关键库    | 无（标准库）              | python-docx      | openpyxl            | **PyMuPDF（fitz）**                    | **dashscope + fitz**                     | **无（str 内置方法）** | **langchain_text_splitters** | **无（全部复用）**                              |
| 依赖外部服务 | 否                   | 否                | 否                   | 否                                    | **是（DashScope API）**                     | 否               | 否                            | **间接（经 ocr_page / embedding）**           |
| 失败形态   | 全有或全无               | 全有或全无            | 全有或全无               | 文件级 fatal + 页级委派                     | **页级容错 + 文件级 fatal**                     | **不失败（纯函数）**    | 空输入 → []（守卫跳过）               | **三态：SUCCESS / SUCCESS_WITH_WARNINGS / FAILED（0 chunks → 回滚）** |
| 错误码    | FILE_PARSE_ERROR    | FILE_PARSE_ERROR | FILE_PARSE_ERROR    | FILE_PARSE_ERROR + **ENCRYPTED_PDF** | **OCR_NOT_CONFIGURED / OCR_AUTH_FAILED** + warnings | **无**           | **无（ImportError → 全局 500）**  | **UNSUPPORTED_FILE_TYPE**（扩展名不在集合）       |
| 降级策略   | 三级编码级联              | 无                | 无                   | 空页 → 回调                              | 重试 3 次 → 页级放弃                            | 无（空结果 → 调用方拒绝）  | 超长候选递归再切                     | 无（FAILED → 幂等回滚清残留）                      |

**一个新维度出现了：依赖外部服务。** 前四个 parser 都是"本地文件 → 本地计算"，ocr_page 第一次把网络 API 拉进 Parse 站——这带来全新的问题域：超时、限流（429）、认证、密钥配置。**错误处理的复杂度不是文件格式带来的，是"外部世界不可靠"带来的**（第 25 节③）。

**T0306 把另一个极端拉进本表：纯函数。** 表格两端是复杂度谱系的两个端点——最折腾的 ocr_page（网络 API）与最安静的 clean_text（零外部依赖、零失败路径）。**T0307 的 chunk_text 落在两极之间**：没有外部服务、没有异常路径（与 clean_text 一样安静），但引入了本模块第 4 个第三方库（langchain_text_splitters，惰性导入、**无 try/except 包裹**）——它的"失败"只有一种：库不存在 → ImportError → 全局 500（第 35 节⑤）。同时它带来**输出形状的第一次分叉**：前六列"输入杂、输出同（都是 str）"，到这里变成"输入 str、输出 List[dict]"（第 32 节）。

**T0308 的 IngestService 不是第九种"格式处理器"——它是第七列之后的第一列"编排者"（第 37 节）。** 它自己不解析、不清洗、不切分、不向量化，只是按 SPEC F002 的顺序**调用**前七列 + embedding + ChromaDB。因此它的每一行都是"间接"：依赖外部服务是间接的（经 ocr_page）、关键库是"无（全部复用）"、失败形态不是单个函数的成败而是**三态汇总**（第 40 节②）。它是输出形状的**第二次分叉**：chunk_text 已经分叉出 List[dict]，process 再分叉出**五键 dict**——注意五键里甚至**没有文本**：文本进管道，出来的是**状态 + 元数据**。第八列的职责是"把材料做成成品并汇报结果"，不是"加工材料"。

---

## 23. 用 JS/TS 类比理解 PDF 解析与 OCR fallback

### PDF 与前四个格式的本质区别：排版指令 + 可选的文本层

txt 是字节，docx/xlsx 是 zip+XML。**PDF 是第三种东西**：它的核心是**排版指令**（"在坐标 (x, y) 用字号 12 画这串字符"），文本只是其中**可选的一层**：

```text
PDF 的两种"页"
┌─────────────────────────────┐  ┌─────────────────────────────┐
│ 文本型 PDF（Word 导出等）      │  │ 扫描型 PDF（复印/拍照）        │
│                             │  │                             │
│ page.get_text() → "合同"     │  │ page.get_text() → ""         │
│                             │  │ （文字是像素，不是字符）        │
│ [文字是"画"出来的，           │  │ [只有一张大图片，              │
│  但画的内容是字符]            │  │  字符信息完全丢失]             │
└─────────────────────────────┘  └─────────────────────────────┘
```

文本型 PDF 里，`get_text()` 能抽出文字（因为排版指令里就有字符）；扫描型 PDF 是**照片**——文字对计算机来说只是像素。后者就是 OCR fallback 存在的理由（SPEC F004 Define："扫描件、图片型 PDF 无法通过原生文本提取获取内容"）。

### PyMuPDF（fitz）≈ Node 里的什么

| Python                 | Node.js                                  | 说明               |
| ---------------------- | ---------------------------------------- | ---------------- |
| PyMuPDF（`import fitz`） | [pdf.js](https://mozilla.github.io/pdf.js/) | 同定位：PDF 的读取/渲染引擎 |
| `fitz.open(path)`      | `pdfjsLib.getDocument({url})`            | 打开文档             |
| `page.get_text()`      | `page.getTextContent()`（+拼装）             | 提取原生文本           |
| `page.get_pixmap()`    | 渲染到 `<canvas>`                           | 页面渲染成图片          |
| `doc.needs_pass`       | `getDocument` 的 password 提示              | 加密检测             |

前端直觉非常好迁移：**pdf.js 在浏览器里做的事（打开、翻页、取文本、渲染到 canvas），PyMuPDF 在服务端做**。区别是：浏览器渲染给用户看，服务端渲染喂给 OCR API。

### OCR fallback ≈ 前端世界里没有的原生等价物

浏览器没有内置 OCR，所以这个类比要换一种方式想：**"一张图片 + 一个视觉 AI API"**。你在前端要做"识别截图里的文字"，流程是：

```ts
// 心智模型（前端版）
const blob = canvas.toDataURL('image/jpeg');          // ≈ page.get_pixmap() → tobytes("jpg")
const dataUri = blob;                                  // ≈ base64 编码的 data-URI
await visionApi({                                       // ≈ MultiModalConversation.call
  image: dataUri,
  prompt: '请提取图片中的所有文字，保持格式'
});
```

**前端早就熟悉"图 → data-URI → API"这条链**（头像上传、截图识别都是它）。T0305 的服务端版本唯一的新东西是：调用的是**多模态大模型**（Qwen-VL-Plus），不是传统 OCR 引擎——模型"看"图片、"读"文字，和 ChatGPT 看图是同一类能力。

### 回调注入 ≈ TS 里传函数参数

`parse_pdf_file(file_path, ocr_page=...)` 的第二个参数，对前端开发者来说**毫无新意**：

```ts
// TS 里你天天这么写
function parsePdf(filePath: string, ocrPage?: (p: string, n: number) => string): string {
  // ... if (text.trim()) { ... } else if (ocrPage) { pageTexts.push(ocrPage(filePath, page.number + 1)) }
}
```

函数作为参数传递（callback / 高阶函数）在前端是日用技能（`array.map(fn)`、`onClick`、事件订阅都是）。Python 里完全一样——只不过**类型标注**长得不同：`Optional[Callable[[Path, int], str]]`（手册 22.2）。**理解上没有新概念，只有新语法。**

---

## 24. 逐行精读：parse_pdf_file + OCR 基础设施 + ocr_page

### 全景：686 行文件的第三个区段（第 194–378 行）

```text
第 194–251 行  parse_pdf_file     T0304 · 逐页循环 + 原生提取 + 回调口
第 253–255 行  分节注释           全文件第一条 "----" 分节线
第 257–281 行  OCR 常量与状态      prompt / 重试参数 / _OCR_WARNINGS + 3 个小函数
第 284–378 行  ocr_page           T0305 · 渲染 → Base64 → API → 重试
```

和前三个 parser 的"单函数"格局不同，T0304/T0305 带来了**模块的第二次进化**：函数不再是唯一的组织单位——**分节注释、模块级常量、模块级状态**都出现了（第一次进化是 T0302 引入多函数）。

**本区段之后还有三个区段**：第四区段（清洗，第 386–413 行，T0306——见第 27 节）、第五区段（切分，第 416–531 行，T0307——见第 32–36 节）和第六区段（管道编排，第 534–683 行，T0308——见第 37–41 节）。到 T0308 落地后，686 行文件里共有 4 条分节线、6 个区段。

### 片段 1：打开 PDF 与加密检测（第 229–238 行）

```python
    try:
        import fitz

        doc = fitz.open(str(file_path))
    except Exception as exc:
        raise AppError("FILE_PARSE_ERROR") from exc

    try:
        if doc.needs_pass:
            raise AppError("ENCRYPTED_PDF")
```

四个教学点：

**① 函数内 import——第四次出现，惯例连续五次。** `import fitz`（PyMuPDF 的模块名是 `fitz`，包名是 PyMuPDF——历史原因，别问为什么）和第 19 节预测的一模一样：第四个 parser 的 import 果然在函数里。

**② `str(file_path)` 桥接回来了！** 第 19 节刚讲过"openpyxl 不需要 str() 桥接"，这里 `fitz.open(str(file_path))` 又需要了。**三个库三种情况**：python-docx（2008 老库）要桥、openpyxl（2010 新库）不要、fitz（C++ 绑定库）又要。教训升级：**Path 支持没有统一答案，看库文档的 `filename: str | Path` 标注，不确定就 `str()` 一下——多写一行永远不炸。**（20.6 的"第三幕"见手册 20.6。）

**③ `doc.needs_pass`——加密检测在打开之后。** fitz 能"打开"加密 PDF（文件结构可读），只是内容需要密码。`needs_pass` 是文档对象上的布尔属性——**询问对象的状态**，而不是 try/except 猜异常。SPEC F003 错误场景表："PDF 加密/受保护 → 422 `ENCRYPTED_PDF`"——**这是 Parse 站第一个不是 FILE_PARSE_ERROR 的 422 码**：加密不是"解析失败"，是"内容被锁"，值得一个专属错误码（调用方可以提示用户"请提供未加密的 PDF"，而不是"文件坏了"）。

**④ 两层 try 的分工。** 外层 try 管"打开"（fitz import 失败、文件损坏 → FILE_PARSE_ERROR）；内层 try 管"使用"（needs_pass 检查、逐页循环 → 各自的错误）。**打开的错误和使用中的错误分开处理**——前三个 parser 没有这个需要（它们打开后就没有"使用中"的失败形态了）。

### 片段 2：逐页循环与回调口（第 239–251 行）

```python
        page_texts: List[str] = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                page_texts.append(text)
            elif ocr_page is not None:
                page_texts.append(ocr_page(file_path, page.number + 1))
            else:
                page_texts.append("")
        return "\n\n".join(page_texts)
    finally:
        doc.close()
```

逐点看：

**`for page in doc`——文档对象本身可迭代。** PyMuPDF 的 `Document` 实现了迭代协议（`__iter__`），直接 for 出每一页。这是 Python 生态的普遍做法——**库对象"假装自己是容器"**，让遍历代码读起来自然（手册 22.8）。

**`text.strip()` 是判定点。** SPEC F003 3.2 第 2 条："如果提取文本非空（`text.strip()` 为 True），使用原生文本"。注意判定标准是 **strip 后非空**——一页只有空白字符（空格、换行）的 PDF 会被判定为"无文本"→ 触发 OCR。这是 SPEC 明示的规则，实现逐字照抄。

**三岔口的逻辑**（原生 / 回调 / 空串）：

- 有原生文本 → 直接用（**混合页只取原生文本**：SPEC 3.2 限制第 1 条"单页内既有原生文本又有图片嵌入文字的情况，v1 仅使用原生文本"——`if/elif` 的结构天然保证：有文本就不会进 OCR 分支）
- 无原生文本 + 有回调 → 调 `ocr_page(file_path, page.number + 1)`
- 无原生文本 + 无回调 → 追加 `""`（**页位置保留，内容是空**——所以"不保留 page_number provenance"（SPEC 3.2 第 4 条）指的不是丢页，而是不保留"这段文本来自第几页"的标签）

**`page.number + 1`——0-based → 1-based 的契约转换。** PyMuPDF 内部页码从 0 数起；SPEC F004 的警告格式 `{page_number: 3}` 显然是从 1 数起（人类习惯）。**转换发生在契约边界**：内部 0-based，跨函数边界一律 1-based（T0305 那边再转回来，见片段 4——一进一出，两个方向的转换各一次，都只有一行）。

**`"\n\n".join(page_texts)`——页间分隔是两个换行。** 注意与前三个 parser 的区别：行间是 `"\n"`，**页间是 `"\n\n"`**（一个空行）。这是 SPEC 3.2 第 3 条明示的分隔符。为什么？页是比行更高层级的结构——下游切分（F006）看到空行能感知"这里换页了"。

**`finally: doc.close()`——全模块第一次显式关资源。** 回顾第 21 节 Pending Question #8：openpyxl 的 workbook 没关，靠 GC 回收。T0304 **换了个姿势**：`finally` 保证无论成功、raise 还是中途异常，文件句柄都释放。**资源纪律在同一个模块里出现了两次不同的水准**——不修旧函数（"加"不改），但新函数按更高标准写。这是"新代码比旧代码好"的正常演化，不是 inconsistency bug。

### 片段 3：OCR 常量与警告状态（第 253–281 行）

```python
# ---------------------------------------------------------------------------
# OCR fallback (SPEC F004 — Qwen-VL-Plus via DashScope)
# ---------------------------------------------------------------------------

_OCR_PROMPT = "请提取图片中的所有文字，保持格式"

# SPEC 9.3: initial request + max 2 retries = max 3 total attempts,
# exponential backoff (~1s, ~2s)
_MAX_TOTAL_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = (1.0, 2.0)

# Structured warnings {page_number, error_code} recorded by ocr_page.
# Lifecycle (clear per file) is owned by the ingest pipeline (T0308).
_OCR_WARNINGS: List[Dict[str, Any]] = []


def get_ocr_warnings() -> List[Dict[str, Any]]:
    """Return the warnings recorded by ``ocr_page`` since the last clear."""
    return list(_OCR_WARNINGS)


def clear_ocr_warnings() -> None:
    """Reset the OCR warning list."""
    _OCR_WARNINGS.clear()


def _record_ocr_warning(page_number: int, error_code: str) -> None:
    """Append a SPEC F004 structured warning."""
    _OCR_WARNINGS.append({"page_number": page_number, "error_code": error_code})
```

五个教学点：

**① 分节注释——全文件第一条。** 686 行文件需要地图了。`# ----` 线把"parser 们"和"OCR 世界"划开——**文件长大到一定程度，组织方式自动升级**（单函数 → 多函数 → 多区段）。

**② 模块级常量：把 SPEC 的魔法数字请进代码里当"有名字的量"。** `_MAX_TOTAL_ATTEMPTS = 3`、`_RETRY_BACKOFF_SECONDS = (1.0, 2.0)`、`_OCR_PROMPT`——SPEC 9.3 的"初始 + 2 次重试、~1s/~2s 退避"和 F004 的 prompt 原文，全部变成**可读、可改、可引用的常量**。前三个 parser 没有常量需求（规则都是流程，不是参数）；T0305 的规则是**参数**，所以常量化。**常量名即文档**：改退避策略只需改这一处。

**③ `_OCR_WARNINGS` 模块级可变状态——模块开始"有记忆"。** 前三个 parser 是纯函数（同样的输入 → 同样的输出，无副作用）；T0305 需要"跨调用收集警告"，于是引入模块级 list。**这是纯函数世界到有状态世界的第一次跨越**（手册 22.3）。注释里写明生命周期："Lifecycle (clear per file) is owned by the ingest pipeline (T0308)"——**状态归谁清，写在注释里**（见第 25 节⑥）。

**④ get/clear 访问器对——模块当"单例对象"用。** 没有 class，但 getter / setter / 内部 helper（`_record_ocr_warning`）一个不少。Python 社区常见做法：**简单状态不值得开 class 时，模块级变量 + 访问函数就是"穷人版单例"**。注意 `get_ocr_warnings` 返回 `list(_OCR_WARNINGS)` 是**防御性拷贝**——调用方拿到的 list 改不动模块内部状态。

**⑤ `Any` 类型第一次进本文件。** `List[Dict[str, Any]]`——警告字典的 value 类型"随便"（int 的页码、str 的错误码混在一个 dict 里）。`Any` = 放弃类型检查（TS 的 `any`），用在这里是务实选择：警告结构由 SPEC 定义、由 T0308 消费，写死 union 类型收益不大。

### 片段 4：ocr_page——渲染、调用、重试（第 284–378 行）

先看整体骨架（四段）：

```python
def ocr_page(pdf_path: Path, page_number: int) -> str:
    """..."""
    if settings.get_dashscope_key() is None:          # ① key 检查（最前）
        raise AppError("OCR_NOT_CONFIGURED")

    try:
        import dashscope                                  # ② 打开 + 三连 import
        import fitz
        from dashscope import MultiModalConversation
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise AppError("FILE_PARSE_ERROR") from exc

    try:                                                 # ③ 主体（渲染→调用→重试）
        try:
            page = doc.load_page(page_number - 1)        #    渲染段
            pix = page.get_pixmap()
            img_b64 = base64.b64encode(pix.tobytes("jpg")).decode("ascii")
        except Exception:
            _record_ocr_warning(page_number, "PAGE_RENDER_FAILED")
            return ""

        dashscope.api_key = settings.get_dashscope_key()
        messages = [ ... ]                                #    消息组装

        for attempt in range(1, _MAX_TOTAL_ATTEMPTS + 1): #    重试段
            try:
                response = MultiModalConversation.call(...)
            except Exception:
                retriable = True
            else:
                if response.status_code == 200: ...       #    成功
                if response.status_code in (401, 403): ...#    认证失败
                retriable = ...
            if attempt < _MAX_TOTAL_ATTEMPTS and retriable:
                time.sleep(_RETRY_BACKOFF_SECONDS[attempt - 1])
                continue
            break

        _record_ocr_warning(page_number, "OCR_PAGE_FAILED")  # ④ 兜底
        return ""
    finally:
        doc.close()
```

逐点看：

**① key 检查在函数最前面——SPEC F004 禁止行为的兑现。** "仅在首次需要 Qwen-VL OCR 时才校验 key"——`ocr_page` 被调用的那一刻就是"首次需要"的时刻。检查放在 open 之前：少开一次文件、错误更快。**对纯文本文件的影响是零**：parse_pdf_file 对原生文本页根本不调 ocr_page（第 25 节⑤）。

**② 一个 try 里三个 import。** `import dashscope` + `import fitz` + `from dashscope import MultiModalConversation`——第五次函数内 import（惯例连续五次），且一次包三个。任何 import 失败或文件打不开 → FILE_PARSE_ERROR。

**③ 三层嵌套 try 的分工**（这是全项目最深的 try 结构，值得停下来画图）：

```text
try（外层，finally close）                       ← 资源层：保证 doc 必关
  try（渲染段）                                  ← 容错层 1：渲染失败 → warning + ""
  for attempt ...（重试段）
    try（API 调用）                              ← 容错层 2：网络失败 → retriable
    else（响应处理）                              ← 成功/认证/状态码分流
```

**④ `page.load_page(page_number - 1)`——1-based → 0-based 的逆转换。** 和 T0304 的 `page.number + 1` 正好相反方向——**契约是 1-based，库是 0-based，每个边界各转一次**。有人会问"为什么不统一成 0-based"？因为 SPEC F004 的警告格式、以及人类说"第 3 页"的习惯都是 1-based——**API 契约向人妥协，内部向库妥协，边界处一行转换**。

**⑤ 渲染链：`get_pixmap()` → `tobytes("jpg")` → `b64encode` → `.decode("ascii")`。** 四步把"PDF 页"变成"API 要的字符串"：渲染成像素图 → 编码 JPEG 字节 → Base64（二进制 → 64 个安全字符）→ bytes 转 str（Base64 只含 ASCII 字符，所以 `.decode("ascii")` 永远成功）。最后拼成 `data:image/jpeg;base64,...`——**和网页 `<img src>` 里的 data-URI 一模一样**（前端直觉：这就是你传头像时 `FileReader.readAsDataURL()` 的结果）。

**⑥ 消息格式是 Qwen-VL 的 API 契约。** `content` 是一个 list，混装图片和文本：

```python
messages = [{"role": "user", "content": [
    {"image": "data:image/jpeg;base64," + img_b64},
    {"text": _OCR_PROMPT},
]}]
```

多模态模型的消息格式：图片不是"附件"，是**内容的一部分**——和文本并列放在 content 数组里（ChatGPT 上传图片聊天的 API 同构）。

**⑦ 重试循环——本次 Task 最需要精读的结构**（第 333–357 行）：

```python
        for attempt in range(1, _MAX_TOTAL_ATTEMPTS + 1):
            try:
                response = MultiModalConversation.call(
                    model="qwen-vl-plus", messages=messages
                )
            except Exception:
                retriable = True  # timeout / network error (SPEC 9.3)
            else:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    return "".join(
                        item["text"]
                        for item in content
                        if isinstance(item, dict) and "text" in item
                    )
                if response.status_code in (401, 403):
                    # Auth failure: terminate the whole file, no retry (F004)
                    raise AppError("OCR_AUTH_FAILED")
                # Retry only timeout/network/429/5xx; anything else fails
                # the page on this attempt.
                retriable = response.status_code == 429 or response.status_code >= 500
            if attempt < _MAX_TOTAL_ATTEMPTS and retriable:
                time.sleep(_RETRY_BACKOFF_SECONDS[attempt - 1])
                continue
            break
```

- **`range(1, N+1)`——1-based 循环计数器**：循环变量 attempt 从 1 数到 3，因为要拿它算"还有没有下次"和"该睡多久"（手册 22.5）
- **`try / except / else`——else 块第一次进项目**（手册 22.1）。语义：`except` 只接"调用炸了"（网络层）；`else` 只处理"调用成功返回了"（HTTP 层）。**关键微妙处：else 块里 raise 的 `OCR_AUTH_FAILED` 不会被本层 except 捕获**——except 只护着 try 块。所以认证失败能干净地穿透重试循环、穿透渲染层的 try（已经过了）、直达外层 finally（close）后继续向 parse_pdf_file 传播——**一个 raise 穿过三层结构，finally 每层都执行了**。如果写错成"在 try 里 raise"，反而会被自己的 except Exception 吞掉
- **`except Exception: retriable = True`**——网络异常（超时、连接断开）没有 status_code，一律按可重试处理（SPEC 9.3 的 "timeout, network error"）
- **200 → 解析响应**：`response.output.choices[0].message.content`——SDK 的对象链；然后用 `isinstance(item, dict) and "text" in item` 做**防御性过滤**（手册 22.4）：外部 API 返回什么不完全由我们控制，只取"像文本的东西"
- **401/403 → raise，不重试**：认证错误是配置问题，重试 N 次还是 401（第 25 节④）
- **429/5xx → 可重试**；**其他状态码（4xx 等）→ retriable=False → break**——直接按页失败处理（docstring："Other non-200 → page failure (no retry)"）
- **`if attempt < _MAX_TOTAL_ATTEMPTS and retriable:`**——两个条件都满足才睡+继续：没到 3 次上限 + 这次失败可重试。**最后一次尝试失败后不再睡，直接 break**（没有"第 4 次的等待"）
- **`_RETRY_BACKOFF_SECONDS[attempt - 1]`**——attempt 是 1-based，元组下标是 0-based：第 1 次失败睡 1.0s、第 2 次失败睡 2.0s（**指数退避——每次等待翻倍**，给服务器喘息时间；SPEC 9.3 明示的 ~1s/~2s）

**⑧ 兜底与 finally**（第 359 行起至函数尾）：

```python
        _record_ocr_warning(page_number, "OCR_PAGE_FAILED")
        return ""
    finally:
        doc.close()
```

能走到 359 行 = 重试 3 次全败（或 429/5xx 之外的不可重试状态码）。**记录 warning + 返回空串——页被"温和地放弃"，文件继续**。这就是 SPEC F004 的"跳过该页，记录 warning，继续处理"。最后 `finally: doc.close()` 第二次显式关资源。

### 读完自检：4 个问题（T0304/T0305）

1. `parse_pdf_file` 在什么情况下会**不调用** `ocr_page`？（原生文本非空的页；或根本没传回调参数）
2. `page.number + 1` 和 `page_number - 1` 各出现在哪个函数里？为什么两个方向都要转换？
3. `OCR_AUTH_FAILED` 的 raise 写在 `else` 块里，它会被同一层的 `except Exception` 捕获吗？它最终会传播到哪里？
4. `_OCR_WARNINGS` 是谁写入的？谁负责清空？`get_ocr_warnings()` 为什么返回 `list(...)` 拷贝？

（答案：① 两种：text.strip() 非空走原生；ocr_page is None 走 else "" 分支。② 前者在 parse_pdf_file（0-based → 1-based 出契约），后者在 ocr_page（1-based 契约 → 0-based 进库）。③ 不会——except 只护 try 块；它穿透重试循环和 try/finally（finally 照常执行 close），最终传到 parse_pdf_file 的调用方（T0308）。④ ocr_page 的 `_record_ocr_warning` 写入；T0308 编排负责 clear（生命周期注释写明）；拷贝防止调用方改到模块内部状态。）

---

## 25. 设计决策深潜：六个值得停下来看的选择

### ① 为什么用回调而不是直接调用：T0304/T0305 的解耦

`parse_pdf_file` 的 docstring 里有一句话最值得琢磨：**"the Qwen-VL call itself is implemented in T0305"**——T0304 的代码里**完全没有 dashscope 的影子**。它只知道"有个回调，签名是 `(Path, int) -> str`"。

这带来三层好处：

- **任务解耦**：T0304 完成时 T0305 还没写。回调参数让 parse_pdf_file 在 OCR 不存在时**已经是完整可测的函数**（传个假回调就能验证逐页循环）
- **依赖解耦**：`import dashscope` 只存在于 ocr_page。一个纯文本 PDF 的知识库，理论上可以只装 PyMuPDF 不装 dashscope 包（虽然 v1 的 requirements 都装）
- **哲学延续**：Phase 1 用 ABC 声明接口（"谁实现都行"），这里用函数签名声明接口（"回调是谁都行，契约说了算"）——**依赖倒置在项目里的第二种形态**。TS 类比：`type OcrCallback = ...` 接口 + 依赖注入，和 Angular 的 DI、React 的 render props 同源

### ② 为什么 ocr_page 每次重新打开 PDF：冻结契约的代价

冻结契约只传 `(pdf_path, page_number)`——**没有传 doc 对象**。所以 ocr_page 每次被调用都要自己 `fitz.open()` + `close()` 一次。一个 300 页扫描 PDF = 300 次 open/close。

为什么不把 doc 传过去？——契约冻结在 T0304（当时 OCR 的实现形态未知），`(pdf_path, page_number)` 是最小、最不侵入的接口：OCR 实现者可以自由选择"怎么打开这个文件"（甚至未来换成别的渲染库）。**代价是 O(n) 次 open**——对本项目（一次一个文件、文件大小有上传上限）完全可接受；对高吞吐批处理场景是优化点。这是"接口简单性 vs 实现效率"的经典取舍（记入 Pending Questions #12）。

### ③ 为什么失败分三层：Parse 站错误哲学的一次升级（本 Task 最核心的决策）

前三个 parser 的错误哲学是**全有或全无**：任何失败 → 422 → 整个文件失败。T0304/T0305 建立了**三层失败分级**：

| 层             | 形态                                       | 触发                          | 后果        |
| ------------- | ---------------------------------------- | --------------------------- | --------- |
| **文件级 fatal** | raise AppError → HTTP 4xx/5xx            | 打不开/损坏、加密、key 缺失、认证失败       | 整个文件失败    |
| **页级容错**      | warning + 空串                             | 渲染失败、OCR 重试耗尽               | 跳过该页，文件继续 |
| **状态机**       | SUCCESS / SUCCESS_WITH_WARNINGS / FAILED | warnings 非空但 chunks>0 / 全失败 | T0308 判定  |

为什么 PDF 特殊？三个理由：

1. **页是天然边界**：一个 PDF 天生就是"几页独立内容"——第 3 页坏了和第 1、2 页没关系（对比：txt 的字节流没有这种内部边界）
2. **OCR 依赖外部服务**：外部世界不可靠（超时、限流、模型抽风）——**不可靠的依赖必须可容忍**，否则任何抖动都导致文件级失败
3. **SPEC F004 明文禁止**："禁止因单页 OCR 失败而丢弃其他页面已成功提取的文本"——不是实现者发明，是 SPEC 定好的产品决策

**分界线原则**（值得记住的判据）：**配置/身份问题 = 文件级**（key 缺失、401/403——重试无用，且对所有页都一样错）；**单页执行问题 = 页级**（渲染失败、OCR 失败——换一页可能成功）。这条线在 T0803（LLM 重试）会再次出现：单次回答失败可重试，但 LLM key 缺失就是文件级 fatal（LLM_NOT_CONFIGURED）。

### ④ 为什么 401/403 不重试、还要终止整个文件

SPEC 9.3："No retry for: 401, 403 (auth errors)"。理由：认证失败是**配置错误**，不是**瞬时故障**——重试 3 次还是 401，纯属浪费请求和等待时间。而终止整个文件（而不是页级容错）是因为：**key 错了意味着接下来每一页都会 401**——页级容错是为"单页执行问题"准备的，认证问题是"全文件性问题"，属于文件级 fatal（`OCR_AUTH_FAILED`，500）。

和 `OCR_NOT_CONFIGURED`（key 缺失）对照记忆：**没有 key → 500 NOT_CONFIGURED；key 错了 → 500 AUTH_FAILED**。两者都是"配置问题"，都终止整个文件，都不重试。

### ⑤ 为什么 key 检查放在 ocr_page 最前面

SPEC F004 禁止行为第三条："**禁止**因 `DASHSCOPE_API_KEY` 缺失而阻止纯文本文件或含原生文本 PDF 的上传处理（仅在首次实际需要 Qwen-VL OCR 时才校验 key）"。

"首次需要"的时刻 = ocr_page 第一次被调用的时刻。实现把检查放在函数第一行——**被调用才检查，检查在最前**。效果：

- 纯文本文件：OCR 函数从未被调用 → 从不检查 key → key 缺失完全不影响
- 含原生文本的 PDF：只有碰到第一个图片页才检查 → 前面几页照常处理
- 检查位置在 `fitz.open` 之前：省一次文件打开，错误更快

对照 embedding 的 `get_model()`：模型在**首次使用时**加载（懒加载），key 在**首次需要时**检查——同一哲学（"用不着的依赖不打扰用户"）在两个模块各自落地。

### ⑥ 为什么 warnings 走模块级旁路而不是返回值

ocr_page 的失败信息为什么不放进返回值（比如返回 `(text, warning)` 元组）？因为**五个函数的外形必须一致**（第 22 节）：都是 `Path → str`（parse_pdf_file 多了个可选回调）。如果 ocr_page 返回元组，parse_pdf_file 就要拆包、传警告、改自己的返回类型——**外形破坏会传染**，最终 T0308 编排要对每种 parser 写不同的调用代码。

模块级 `_OCR_WARNINGS` + get/clear 访问器是**旁路通道**：主数据流（str）保持纯净，副作用（警告）走侧面。生命周期注释明确"clear per file 由 T0308 管"——**状态的所有权写清楚，是谁的锅一目了然**。TS 类比：模块级数组 ≈ 事件收集器（类似 RxJS 的 subject，或全局错误队列）。

---

## 26. SPEC 3.2 + F004 对照、诚实 AC 与新知识索引

### SPEC 3.2 逐条对照

| #    | SPEC 要求                        | 实现位置                                     | 结论                 |
| ---- | ------------------------------ | ---------------------------------------- | ------------------ |
| 1    | 使用 PyMuPDF（`fitz.open()`）打开    | [ingest.py:229-232](../../backend/app/services/ingest.py#L229-L232) `import fitz` + `fitz.open(str(file_path))` | ✅                  |
| 2a   | 每页 `page.get_text()` 提取原生文本    | [ingest.py:241](../../backend/app/services/ingest.py#L241) | ✅                  |
| 2b   | 非空（`text.strip()` 为 True）用原生文本 | [ingest.py:242-243](../../backend/app/services/ingest.py#L242-L243) `if text.strip():` | ✅ 逐字一致             |
| 2c   | 空则对该页调用 Qwen-VL OCR            | [ingest.py:244-245](../../backend/app/services/ingest.py#L244-L245) 回调 `ocr_page(file_path, page.number + 1)` | ✅（回调形态，T0305 填充实现） |
| 3    | 按原始页码顺序 `"\n\n".join(...)` 拼接  | [ingest.py:239-248](../../backend/app/services/ingest.py#L239-L248) | ✅                  |
| 4    | 不保留 page_number provenance     | 返回纯 `str`，无页标签                           | ✅                  |
| —    | 混合页 v1 仅用原生文本，不做增强 OCR         | `if/elif` 结构：有原生文本不进 OCR 分支              | ✅ 结构保证             |
| —    | 不引入 PyPDF2/PdfReader           | 全文无 PyPDF2                               | ✅                  |
| —    | 加密/受保护 → 422 `ENCRYPTED_PDF`   | [ingest.py:237-238](../../backend/app/services/ingest.py#L237-L238) | ✅                  |

### F004 逐条对照

| #    | SPEC 要求                                  | 实现位置                                     | 结论                |
| ---- | ---------------------------------------- | ---------------------------------------- | ----------------- |
| 1    | 渲染页面 JPEG：`page.get_pixmap()` → `pix.tobytes("jpg")` | [ingest.py:331-332](../../backend/app/services/ingest.py#L331-L332) | ✅ 逐字一致            |
| 2    | Base64 编码，image format `data:image/jpeg;base64,{img_base64}` | [ingest.py:333](../../backend/app/services/ingest.py#L333) + [ingest.py:343](../../backend/app/services/ingest.py#L343) | ✅                 |
| 3    | DashScope MultiModalConversation，model `qwen-vl-plus` | [ingest.py:351-353](../../backend/app/services/ingest.py#L351-L353) | ✅                 |
| 4    | prompt `"请提取图片中的所有文字，保持格式"`              | [ingest.py:257](../../backend/app/services/ingest.py#L257) 模块常量，逐字一致 | ✅                 |
| 5    | 重试 timeout/network/429/5xx，初始 + 2 次 = 3 次总尝试 | [ingest.py:349-373](../../backend/app/services/ingest.py#L349-L373)（`_MAX_TOTAL_ATTEMPTS = 3`） | ✅                 |
| 6    | 退避 ~1s/~2s（指数退避）                         | [ingest.py:262](../../backend/app/services/ingest.py#L262) + [ingest.py:371](../../backend/app/services/ingest.py#L371) | ✅                 |
| 7    | 401/403 认证失败不重试，终止整个文件                   | [ingest.py:364-366](../../backend/app/services/ingest.py#L364-L366) `raise AppError("OCR_AUTH_FAILED")` | ✅                 |
| 8    | 页级失败不终止，跳过该页，记录 structured warning       | [ingest.py:335](../../backend/app/services/ingest.py#L335)（渲染失败）+ [ingest.py:375-376](../../backend/app/services/ingest.py#L375-L376)（重试耗尽） | ✅                 |
| 9    | warning 格式 `{page_number, error_code}`   | [ingest.py:281](../../backend/app/services/ingest.py#L281) | ✅ 逐字一致            |
| 10   | key 缺失仅在首次需要 OCR 时检测 → 500 `OCR_NOT_CONFIGURED` | [ingest.py:317-318](../../backend/app/services/ingest.py#L317-L318) 函数第一行 | ✅                 |
| 11   | 禁止静默忽略（失败必须暴露）                           | `_OCR_WARNINGS` 收集 + get 访问器             | ✅（见下方诚实 AC 的边界讨论） |
| 12   | 单页渲染失败 → `PAGE_RENDER_FAILED` warning，继续处理 | [ingest.py:334-336](../../backend/app/services/ingest.py#L334-L336) | ✅                 |

> 注意第 2、4、9 条：SPEC 的代码/字符串和实现**逐字一致**——`page.get_pixmap()` → `pix.tobytes("jpg")`、prompt 原文、warning 格式。SPEC 给到伪代码/字面量级别的，实现照抄，这是全项目第三次成规模的逐字照抄（前两次：DOCX 段落 join、Excel 行内 join）。

### 诚实 AC 验证（T0304/T0305，不虚构 PASS）

涉及的 AC：**AC-F003-03**（混合 PDF：第 1 页原生 + 第 2 页 OCR → 按页序拼接）、**AC-F004-01**（纯图片 PDF 全量 OCR 成功 → SUCCESS、warnings=[]）、**AC-F004-02**（混合 PDF 全部成功 → SUCCESS）、**AC-F004-03**（部分页失败 → SUCCESS_WITH_WARNINGS）、**AC-F004-04**（全部失败 → FAILED + rollback）、**AC-F004-05**（禁止静默忽略）。

仓库**没有自动化测试**（延续前四节的已知事实）。这些 AC 的完整行为验证需要：真实扫描 PDF + 真实 DashScope API key + 网络调用 + 上传 API（T0501+）——**是整个 Phase 3 验证门槛最高的一组**。我没有构造环境、没有调用真实 API，也**不虚构 PASS**。能做的是代码审查层面的结构确认：

| 检查项                                      | 方式                                       | 结果   |
| ---------------------------------------- | ---------------------------------------- | ---- |
| 原生文本页 → 直接用、不触发 OCR（AC-F003-03 第 1 页）    | 读第 242–243 行 `if text.strip():`          | ✅ 一致 |
| 空文本页 → 回调被调用且页码为 1-based（AC-F003-03 第 2 页） | 读第 244–245 行 `ocr_page(file_path, page.number + 1)` | ✅ 一致 |
| 页序拼接 `"\n\n"`（AC-F003-03 按页码顺序）          | 读第 248 行 `return "\n\n".join(page_texts)` | ✅ 一致 |
| OCR 成功页 → 文本返回、无 warning（AC-F004-01/02 的一半） | 读第 357–361 行 200 分支直接 return             | ✅ 一致 |
| 页级失败 → warning + ""，不中断（AC-F004-03/05）   | 读第 335–336/375–376 行（渲染失败 / 重试耗尽）        | ✅ 一致 |
| 认证失败 → 立即终止不重试（AC-F004-01 反面场景）          | 读第 364–366 行 raise                       | ✅ 一致 |
| key 缺失 → 500 OCR_NOT_CONFIGURED          | 读第 317–318 行                             | ✅ 一致 |

**明确 DEFERRED 的部分**：AC-F004-01/02/03/04 的 `SUCCESS` / `SUCCESS_WITH_WARNINGS` / `FAILED` **状态判定与 rollback 在 T0308（Ingest 编排）才兑现**——T0305 只负责"收集 warnings"，不负责"判定状态"。AC-F004-04 的 rollback（uploads/ 无残留、ChromaDB 无 chunk、keyword index 干净）属于 CLAUDE.md 的 Ingestion Invariants，同样是 T0308 + Phase 5 的活。

**验证门槛的三个层级**（本项目通用）：T0301（纯本地，一个脚本就能验）< T0303（程序能造测试文件）< **T0304/T0305（要真实扫描件 + API key + 网络——学习者可自验证到哪一步算哪一步，见练习）**。

### Python 新知识索引（→ 手册第 22 节）

| 新概念                                     | 一句话                                      | 手册位置 |
| --------------------------------------- | ---------------------------------------- | ---- |
| `try/except/else`                       | else 块只在 try 无异常时执行，且**它的异常不被本层 except 捕获** | 22.1 |
| 回调函数 + `Callable` 标注                    | 函数可以当参数传；`Optional[Callable[[Path, int], str]]` 是"可选的函数类型" | 22.2 |
| 模块级可变状态 + 访问器                           | 模块级 list + get/clear 函数 = "穷人版单例"（无 class 的状态容器） | 22.3 |
| `isinstance(x, dict)`                   | 运行时类型检查——防御外部 API 的不可信数据                 | 22.4 |
| `time.sleep` + `range(1, N+1)`          | 退避等待；1-based 循环计数器                       | 22.5 |
| `base64.b64encode(...).decode("ascii")` | 二进制 → Base64 文本；`bytes.decode("ascii")` 是安全的（Base64 只含 ASCII） | 22.6 |
| `try/finally` 资源释放                      | finally 无论成败都执行——`doc.close()` 的保证       | 22.7 |
| `for page in doc`（库对象迭代）                | 第三方库对象实现 `__iter__`，for 直接遍历             | 22.8 |

已学概念复用：函数内 import（第五次）、`except Exception` 全收（T0302）、`str(path)` 桥接（T0302，20.6 第三幕）、`raise ... from exc`、`is None`（key 检查）、`in (401, 403)` 元组成员测试（T0103）、模块级常量命名 `_UPPER_CASE`（T0102 下划线约定）、`Optional`（T0101）、局部变量标注、防御性拷贝 `list(...)`（T0107）。

### 自测题（T0304/T0305，10 道）

1. PDF 为什么是"第三种东西"？文本型 PDF 和扫描型 PDF 的本质区别是什么？
2. `parse_pdf_file` 的三岔口（原生/回调/空串）分别对应什么条件？"混合页只取原生文本"是哪个结构保证的？
3. `page.number + 1` 和 `page_number - 1` 为什么都存在？各在哪个函数？
4. `doc.needs_pass` 为什么不放在外层 try 里和 fitz.open 一起处理？两层 try 的分工是什么？
5. 页间分隔符是 `"\n\n"` 而其它 parser 的行间是 `"\n"`——为什么？
6. `OCR_AUTH_FAILED` 写在 `else` 块里，为什么不会被 `except Exception` 吞掉？它的传播路径是什么？
7. 重试循环里 `retriable` 有几种取值来源？429 和 401 各走哪条路？
8. `_OCR_WARNINGS` 为什么不作为 ocr_page 的返回值？`get_ocr_warnings()` 为什么返回 `list(...)`？
9. 三层失败分级是什么？"配置问题"和"单页执行问题"各归哪一层？判据一句话是什么？
10. 为什么 key 检查放在 ocr_page 的第一行，而不在模块顶部或文件上传时检查？

### 练习（T0304/T0305）

1. **无外部依赖验证 T0304 的核心逻辑**：用 PyMuPDF 造一个 2 页 PDF（第 1 页写文字 `page.insert_text()`，第 2 页留空），然后：
   ```python
   # ① 不传回调：观察第 2 页产出 ""（页位置保留、内容为空）
   parse_pdf_file(Path("test.pdf"))
   # ② 传一个假回调：验证回调只在第 2 页被调用、页码是 1-based 的 2
   parse_pdf_file(Path("test.pdf"), ocr_page=lambda p, n: f"[OCR 第{n}页]")
   ```
   亲手确认"原生文本 vs 回调"的判定点——**不需要 API key、不需要网络**。
2. **加密实验**：用 fitz 保存一个加密 PDF（`doc.save(..., encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="123")`），调 `parse_pdf_file`，观察 `ENCRYPTED_PDF` 的 raise 路径（`doc.needs_pass` 为 True）。
3. **重试状态机纸面推演**：给 ocr_page 的 6 个场景画出控制流——① 第 1 次 429、第 2 次 200 ② 3 次全是 5xx ③ 第 1 次网络异常、第 2 次 401 ④ 渲染抛异常 ⑤ 直接 200 但 content 里没有 "text" 键 ⑥ key 未配置。对每个场景回答：返回什么？warning 记没记？整个文件活没活？（场景 ⑤ 的结果会指向 Pending Questions #10——先自己推，再看答案。）

### T0304/T0305 快速复习卡

```text
T0304 — PDF Parser（parse_pdf_file，第 186–243 行，58 行）
一句话：fitz 逐页提取原生文本；空页 → 回调 ocr_page；页间 "\n\n" 拼接

本质认知：PDF = 排版指令 + 可选文本层（扫描页的"文字"是像素）
三岔口：text.strip() 非空 → 原生；空 + 有回调 → ocr_page(file_path, page.number + 1)；空 + 无回调 → ""
错误：打开失败 → 422 FILE_PARSE_ERROR；needs_pass → 422 ENCRYPTED_PDF（Parse 站第一个新 422 码）
模式复用：函数内 import（第四次）；str() 桥接回来了（fitz 要 str）；finally 第一次显式 close

T0305 — OCR Fallback（ocr_page，第 276–370 行，95 行 + 基础设施 245–273）
一句话：渲染 JPEG → Base64 data-URI → Qwen-VL-Plus → 重试 → 失败页记 warning

流程：key 检查最前（500 NOT_CONFIGURED）→ 打开 → 渲染（失败 → PAGE_RENDER_FAILED + ""）
      → API 调用 → 200 解析返回 / 401,403 raise（500 AUTH_FAILED，不重试）/ 429,5xx 重试（1s,2s 退避 ×3）
      → 重试耗尽 → OCR_PAGE_FAILED warning + ""（页级容错，文件继续）
核心新语法：try/except/else（else 的异常不被本层 except 捕获——AUTH_FAILED 能穿透）
核心新结构：模块级常量 + 模块级 _OCR_WARNINGS + get/clear 访问器（穷人版单例，生命周期归 T0308）
三层失败分级：文件级 fatal（raise）→ 页级容错（warning + ""）→ 状态机（T0308 判定）
```

### Pending Questions（T0304/T0305 新增，学习中发现，未修复，仅记录）

10. **200 响应但结构不符 → 异常穿透、整个文件失败**：[ingest.py:358](../../backend/app/services/ingest.py#L358) 的 `response.output.choices[0].message.content` 若结构与预期不符（KeyError / IndexError / AttributeError），异常发生在 `else` 块——**不被本层 `except Exception` 捕获**——穿透 ocr_page → 穿透 parse_pdf_file 的循环（L244 无 try）→ 整个文件失败。与"页级容错"哲学的边界情况：SPEC F004 只说"200 → 提取 content text"，未定义响应结构异常的处理。
11. **200 但提取结果为空 → 静默空页无 warning**：[ingest.py:359-363](../../backend/app/services/ingest.py#L359-L363) 的 join 结果若为 `""`（content 里没有 dict 且带 "text" 的 item），直接 return——**该页输出空文本且无任何 warning**。与 AC-F004-05"禁止静默忽略"的精神存在边界：警告覆盖的是"渲染失败/重试耗尽"，不覆盖"API 成功但内容为空"。
12. **ocr_page 每页重开 PDF（O(n) 次 open/close）**：冻结契约只传 `(pdf_path, page_number)`，不传 doc 对象。几百页的扫描 PDF = 几百次 `fitz.open`。单文件串行场景影响小，批量导入场景值得实测（T0308 已落地，但学习环境无真实扫描 PDF，未做性能实测）。
13. **`parse_pdf_file` 无回调时空页静默产 `""`**：[ingest.py:246-247](../../backend/app/services/ingest.py#L246-L247) 的 else 分支不记录任何 warning（与 ocr_page 的警告机制不对称）。若 T0308 编排时忘记传回调，扫描 PDF 会"成功"返回空文本，靠下游 F005 清洗 + FAILED 判定兜底——防御层级存在，但错误定位信息为零（**T0308 落地验证**：process 确实传了 `ocr_page=ocr_page`，此风险未触发，见第 39 节）。
14. **`dashscope.api_key = ...` 是 SDK 的模块级全局赋值**：[ingest.py:338](../../backend/app/services/ingest.py#L338)。v1 单进程单 key 假设下安全；未来多 key / 多租户需注意（与 embedding.py 的 `_model` 模块级单例同类模式，但那是自己的状态、这是第三方库的全局）。
15. **`get_pixmap()` 未指定渲染分辨率**：[ingest.py:332](../../backend/app/services/ingest.py#L332) 用默认参数（约 72dpi）。低分辨率渲染可能影响 OCR 识别率——SPEC F004 未定义渲染参数，v1 接受默认。

---

> **T0304/T0305 部分完**。Parse 站已完成 5/5：文本（T0301）+ DOCX（T0302）+ Excel（T0303）+ PDF 原生（T0304）+ OCR fallback（T0305）。五个函数外形一致（Path 进、str 出），内部各打各的仗——文本打编码战、DOCX 打结构战、Excel 打单元格值战、PDF 打"原生 vs 图片页"战、OCR 打"外部世界不可靠"战。**Parse 站的错误哲学也完成了进化**：从"全有或全无"到"文件级 fatal / 页级容错"两级。下一站：T0306 Text Cleaning——parser 们交出的文本在这里第一次被"把关"（清洗站只"报告"空文本、不"裁决"——拒绝权归 T0308，见第 30 节③）。

---

## 27. T0306 定位：Parse 站之后的第一道"纯"工序

### 管道里的位置：第五站，但和 Parse 站不在一个世界

```text
T0301–T0305 Parse 站 ──▶ T0306 Cleaning 站 ──▶ T0307 Chunking 站 ──▶ T0308 编排
（五个 parser + OCR）    （clean_text）          （chunk_text）          （判定 SUCCESS/FAILED）
```

`clean_text` 在 686 行文件里的位置：第 3 条分节线之后（第 381–383 行），独占第四区段（第 386–413 行）。它是全模块唯一一个**既没有 `try`、也没有 `except`、也没有 raise、也没有 return 错误**的函数。

### 为什么 T0306 是"最简单的 Task"

- **依赖：None**（TASKS.md 原文："Dependencies: None (pure text transformation)"）——不依赖配置、不依赖第三方库、不依赖任何其它 Task
- **输入 str → 输出 str**：不碰磁盘、不碰网络、不碰状态
- **SPEC 的 5 步要求 → 3 行代码 + 1 行注释**

简单不等于不重要。SPEC F005 Define 说得很清楚：**"原始文本可能含有多余空行、空格、控制字符，影响后续切分质量和检索精度"**——清洗是 Parse 站输出的质量闸门，也是 SPEC 管道定义的正式一站："产生了至少 1 个有效 Chunk（**经 F005 清洗 + F006 切分后**）→ SUCCESS"。

### 文件发生了什么变化（T0306+T0307 一起落地）

**第 5 次行号偏移事件**：docstring 43→58 行（+Cleaning 段 7 行 +Chunking 段 7 行 + 空行 1 行）+ imports +1 行（`import uuid`——T0307 的）→ 老代码整体 +16。分节线从 1 条变 3 条：模块从"单函数时代"（T0301）→ "多函数时代"（T0302）→ "分节 + 状态时代"（T0304/T0305）→ "五区段时代"（T0306/T0307）。

---

## 28. 用 JS/TS 类比理解清洗

清洗这件事，前端闭眼能写：

```ts
const cleaned = text
  .split(/\r?\n/)
  .map(line => line.trim())
  .filter(line => line.length > 0)
  .join('\n');
```

Python 版三行：

```python
lines = text.splitlines()
lines = [line.strip() for line in lines]
lines = [line for line in lines if line]
return "\n".join(lines)
```

逐项对照：

| JS/TS                              | Python                             | 差异                                      |
| ---------------------------------- | ---------------------------------- | --------------------------------------- |
| `split(/\r?\n/)`                   | `splitlines()`                     | **Python 更省心**：内置"行边界"概念，正则都不用写（见 29.2） |
| `.map(line => line.trim())`        | `[line.strip() for line in lines]` | 列表推导 ≈ map（17.1）                        |
| `.filter(line => line.length > 0)` | `[line for line in lines if line]` | 带 if 的列表推导 ≈ filter（21.2 的方括号版）         |
| `.join('\n')`                      | `"\n".join(lines)`                 | 同款语义（20.8），注意 join 在字符串上                |

两个结构性差异值得停下来看：**Python 用 `splitlines()` 而不是 `split('\n')`**（行感知，见 29.2 / 手册 23.1）；**Python 没有方法链**，管道靠"重赋值 + 列表推导"表达（见 29.3 / 手册 23.2）。

---

## 29. 逐行精读 clean_text（第 386–413 行）

### 片段 1：docstring（第 386–409 行）——"做 5 步、不做 5 件事"

[ingest.py:386-409](../../backend/app/services/ingest.py#L386-L409)

这个函数 28 行，docstring 占 23 行、函数体只有 4 行——**重点在边界，不在算法**。docstring 分三块：

**① 做（5 步，SPEC F005 Detail 逐字）**：splitlines → 每行 strip → 滤空行 → join → 空结果返回 ""（"the ingest pipeline rejects the file"——拒绝方是管道，不是清洗）。

**② 不做（5 条）**：编码转换（已在 F003 解析阶段处理）、HTML 标签去除、特殊字符过滤、敏感信息脱敏、语言检测。

**③ 语义补充**：一行点睛——"Dropping empty lines collapses consecutive blank lines（合并连续空白行）"；"line-internal whitespace is preserved（行内空白保留）——only line ends are stripped"。

**为什么"不做"要写进 docstring**：清洗函数是项目里**最容易被加料的函数**——"顺手去个 HTML 标签吧"、"顺手过滤特殊字符吧"。docstring 的不做清单是 SPEC 边界在代码里的化身（第 30 节②）。

### 片段 2：三行管道（第 410–413 行）

[ingest.py:410-413](../../backend/app/services/ingest.py#L410-L413)

```python
lines = text.splitlines()  # Step 1: split by line boundaries
lines = [line.strip() for line in lines]  # Step 2: strip line ends
lines = [line for line in lines if line]  # Step 3: drop empty lines
return "\n".join(lines)  # Step 4; empty → "" (Step 5)
```

逐行精读：

- **Step 1 `splitlines()`**：按**行边界**切分——不是按 `"\n"` 字符。它认识 Python 定义的全部行边界：`\n`、`\r\n`（Windows）、`\r`（老 Mac）、`\v`、`\f`、Unicode 行分隔符（U+2028/2029）；且**不产生末尾空串**（`"a\nb\n".splitlines()` → `["a", "b"]`，`split("\n")` 会多一个 `""`）。为什么清洗站必须用行感知 API：输入来自五种 parser，PDF 提取的文本尤其可能混用行边界——"行边界"是概念，不是字符（手册 23.1）。
- **Step 2 `strip()`**：去每行**两端**的空白。两个细节：只动两端（行内 `"a  b"` 保持）；去的是全部 Unicode 空白（含 `\t`、全角空格 U+3000、不换行空格 U+00A0）——对中文文档是优点，但比 SPEC 字面的"空格"更激进（Pending #17）。
- **Step 3 过滤**：`if line` 真值判断（19.1：空串是假值）。与 T0303 的 `cell is not None`（第 20 节②）横向对比：Excel 里 `0` 是合法值，只能用"有没有值"；清洗里空串就是要删的对象，直接用"是不是假值"。**判断标准跟着"假值里有没有要保留的合法值"走**。
- **Step 4 join**：`"\n"` 连接——全模块第五次出现 join，第三次用 `"\n"` 做行连接（前两次：DOCX 段落、Excel 行）。
- **Step 5 免费**：`"\n".join([])` 天然返回 `""`——SPEC 要求的"空结果返回空字符串"**一行代码都不用写**。注释自己写着 `# Step 4; empty → "" (Step 5)`——实现者知道 Step 5 被 Step 4 免费覆盖了（手册 23.4）。

### 关键顺序：strip 必须先于过滤

SPEC 的 5 步顺序是 **load-bearing**（承重的）。假设交换 Step 2/3——先过滤后 strip：

```text
输入行 "  \t "（纯空白）：
  先过滤：非空 → 存活 ✓（错）
  后 strip：变 "" → 但已经过了过滤，脏行留在输出里 ✗
```

过滤条件用的是"**strip 后**"的结果，所以 strip 必须先发生。SPEC 的步骤表不是一个"大致流程"，是精确的顺序契约——AC-F005-01（"每行首尾无空格"）就靠这个顺序保证。

### 读完自检：4 个问题（T0306）

1. `"a\nb\n".splitlines()` 和 `"a\nb\n".split("\n")` 结果有何不同？
2. 把 Step 2 和 Step 3 交换会发生什么？
3. Step 5 的代码在哪里？
4. clean_text 为什么不需要 try/except？

**答案**：① splitlines → `["a", "b"]`；split → `["a", "b", ""]`（末尾多一个空串）。② 纯空白行在交换后存活——filter 时它非空，strip 时它才变空，输出被脏行污染。③ 没有代码——`"\n".join([])` 天然返回 `""`，Step 5 被 Step 4 免费覆盖。④ 它是纯函数：不读文件、不调网络、不碰外部状态——没有任何"外部世界"的失败需要处理。

---

## 30. 设计决策深潜：四个值得停下来看的选择

### ① 为什么 clean_text 是纯函数——全模块唯一无异常路径

Parse 站打"外部世界不可靠"的仗（磁盘、网络、认证、限流），清洗站**没有外部世界**：输入是内存里的 str，输出是内存里的 str。纯函数带来三个保证：**同输入必同输出**（可测性——全 Phase 3 验证门槛最低）、**无副作用**（多次调用无害）、**无失败路径**（调用方不需要 try）。横向看完七个函数，最干净的一条规律浮现出来：**错误处理的复杂度跟着外部依赖走，不跟着代码行数走**——ocr_page 最折腾（网络 API），clean_text 最安静（零依赖）。

### ② 为什么"做 5 步、不做 5 件事"——边界纪律

TASKS.md 的 Out of Scope 原话："Do NOT add HTML/special char filtering; Do NOT add semantic cleaning; Do NOT add language detection"。SPEC 的"不做"清单逐条对应真实诱惑：HTML 标签（网页转存的文档里可能有）、特殊字符（正则清洗的诱惑）、语言检测（"顺手"的事）……v1 全部拒绝。**边界靠 docstring 和纪律维护，不靠代码**——没有防加料的代码防线，未来人"顺手"加 HTML 清理时不会报错，只会偏离 SPEC（与 CLAUDE.md 的 Scope Discipline 同源）。

### ③ 空文本的拒绝权在谁——责任链的三级传递

```text
parser 返回空（不拒绝）──▶ clean_text 返回 ""（不拒绝）──▶ T0308 判定 FAILED（拒绝）
```

前两站只"报告"，第三站"裁决"。与 T0301 的"空文件不是 parser 的错"（第 6 节）同一哲学：**管道里的组件只做自己的变换，裁决留给编排者**。SPEC F005 Step 5 的原文是"后续 Ingest Service 应拒绝并返回错误"——拒绝的活明确不在清洗站。这也修正了 T0304/T0305 收官里"空文本在这里被拒绝"的说法：**清洗站只标记，不拒绝**。

### ④ "合并连续空白行"的两种读法

SPEC F005 Define 说"合并连续空白行"，Detail 说"去除 strip() 后为空的行"。两者对"空行"的结果一致（空行不产生内容），但语义不同：**合并**可能意味着"N 个空行压成 1 个"，**去除**意味着"全删"。实现按 Detail（全删）。v1 无影响——但如果未来想要"保留单个空行"（比如 Markdown 段落之间留一行），Define 和 Detail 会给出不同答案（Pending #16）。

---

## 31. SPEC F005 对照、诚实 AC 与新知识索引

### SPEC F005 逐条对照

| SPEC 条目                  | 实现                                       | 位置        |
| ------------------------ | ---------------------------------------- | --------- |
| 步骤 1 按行分割 `splitlines()` | `lines = text.splitlines()`              | 第 410 行   |
| 步骤 2 每行 `strip()`        | `lines = [line.strip() for line in lines]` | 第 411 行   |
| 步骤 3 过滤空行                | `lines = [line for line in lines if line]` | 第 412 行   |
| 步骤 4 `"\n".join`         | `return "\n".join(lines)`                | 第 413 行   |
| 步骤 5 空结果返回空              | join 空列表天然 `""`（Step 4 免费覆盖）             | 第 413 行注释 |
| 不做：编码转换                  | 无（F003 解析阶段已处理）                          | docstring |
| 不做：HTML 标签去除             | 无                                        | docstring |
| 不做：特殊字符过滤                | 无                                        | docstring |
| 不做：敏感信息脱敏                | 无                                        | docstring |
| 不做：语言检测                  | 无                                        | docstring |

### 诚实 AC 验证（T0306，不虚构 PASS）

仓库没有自动化测试（延续前五节的已知事实）。**T0306 的验证门槛是 Phase 3 最低的**：纯字符串函数，不需要文件、不需要网络、不需要 API key——一条 `python -c` 就能验。但我仍不虚构 PASS：没有执行验证，只做代码审查层面的结构确认：

- **AC-F005-01**（多余空行 + 行首尾空格 → 空行移除、每行首尾无空格）：结构确认——Step 1–3 恰好构成"切行 → 去端白 → 滤空行"，过滤条件用的是 strip 后的结果，逻辑自洽
- **AC-F005-02**（纯空白文本 → 返回 ""）：结构确认——纯空白文本 splitlines 后每行 strip 均为空 → 全部被滤 → `"\n".join([])` == `""`（Step 5 免费路径）

**结论**：结构上满足两条 AC；行为验证留给学习练习 3（一条 `python -c` 就能做）——T0308 已落地，但它的集成验证需要本地 embedding 模型 + ChromaDB，门槛反而高于本函数的独立验证。

### Python 新知识索引（→ 手册第 23 节）

| 知识点                       | 手册位置    |
| ------------------------- | ------- |
| `str.splitlines()` 行感知切分  | 23.1    |
| 管道式重赋值（列表推导流水线）           | 23.2    |
| 带过滤条件的列表推导                | 23.3    |
| join 空列表 == ""（Step 5 免费） | 23.4    |
| `str.strip()` 的精确语义       | 23.5    |
| 纯函数概念（本 Task 的设计核心）       | 第 30 节① |

### 自测题（T0306，8 道）

1. clean_text 的 5 个 SPEC 步骤分别对应哪行代码？
2. 为什么用 `splitlines()` 而不是 `split("\n")`？给出一个 split 会出错的输入。
3. `"a\r\nb"` 经过 clean_text 后是什么？
4. 纯空白文本 `"\n \t\n"` 经过 clean_text 后是什么？走了哪条"免费路径"？
5. 把 Step 2 和 Step 3 交换会破坏哪个 AC？构造一个反例输入。
6. `clean_text("a  b\n\n c")` 输出什么？（注意行内空格）
7. clean_text 为什么是全模块唯一没有 try/except 的函数？
8. 空字符串 `""` 经过 clean_text 后是什么？谁负责"拒绝"它？

**答案**：① 第 410–413 行四行代码，Step 5 免费。② splitlines 认 `\r\n` / `\r` 等全部行边界且无末尾空串；`"a\nb\n"` 用 split 会多出末尾 `""`。③ `"a\nb"`（`\r` 被行边界吸收）。④ `""`——三行全滤，`"\n".join([])` 免费返回 `""`。⑤ 破坏 AC-F005-01；反例输入 `" \t "`（先过滤时非空存活，后 strip 变空但已过闸）。⑥ `"a  b\nc"`——行内空格保留、空行删除。⑦ 纯函数：无外部世界可失败。⑧ `""`；T0308 编排（FAILED 判定）负责拒绝。

### 练习（T0306）

1. **手推管道**：拿纸手推 `"  标题  \n\n\n正文第一段\n\t\n正文第二段  "` 经过 3 行代码的每一步（splitlines → strip → filter → join），写下每步的中间值，再对照 `python -c` 验证。
2. **反例构造**：构造一个"先过滤后 strip"会出错的输入，验证顺序不可交换。
3. **一次性验证两条 AC**：本函数是 Phase 3 唯一不需要准备任何环境（文件/网络/key）的验证对象——一条命令就能同时验证 AC-F005-01 与 AC-F005-02。

### T0306 快速复习卡

```text
T0306 — Text Cleaning（clean_text，第 386–413 行，28 行：docstring 23 + 函数体 4）
一句话：三行列表推导管道，把脏 str 变成"无空行、无端白"的干净 str

五步 → 三行 + 免费：splitlines（行感知）→ strip（只动两端）→ 过滤（if line 真值）→ join
Step 5 免费："\n".join([]) == ""——SPEC 的"空结果返回空"不需要代码
纯函数：无 try、无 except、无状态、无 I/O——全模块唯一（错误哲学不进清洗站）
五不做：编码转换 / HTML / 特殊字符 / 脱敏 / 语言检测——边界纪律，docstring 是化身
拒绝权在 T0308：清洗只报告（返回 ""），不裁决（FAILED）
```

### Pending Questions（T0306 新增，学习中发现，未修复，仅记录）

16. **SPEC Define"合并连续空白行" vs Detail"去除空行"**：Define（包含：合并连续空白行）与 Detail（步骤 3：去除 strip 后为空的行）措辞不一致。实现按 Detail 全删。若未来需要"保留单个空行"（如 Markdown 段落分隔），两处 SPEC 会给出不同答案。
17. **strip() 的"空格"范围未定义**：SPEC 说"行首行尾空格"，实现（`str.strip()` 无参）去掉的是所有 Unicode 空白（含 `\t`、全角空格 U+3000、不换行空格 U+00A0）。对中文文档是优点，但严格说实现比 SPEC 字面更激进。
18. **页间 `"\n\n"` 会被清洗折叠**：[ingest.py:248](../../backend/app/services/ingest.py#L248) 的页间双换行（F003 3.2 的页边界标记）经 clean_text 删除空行后丢失——两页文本在清洗后无缝相连。v1 的 chunking 不需要页边界所以无影响；若未来要"按页切块"或"引注页码"，SPEC 需要澄清页边界是否应在 F005 保留。

---

> **T0306 部分完**。清洗站是全项目最安静的一站：没有新错误码、没有新依赖、没有新状态——只有一个 4 行函数体的纯函数和它 23 行的边界声明。但它是 Parse 站与 Chunking 站之间的**质量闸门**："做 5 步、不做 5 件事"的纪律，以及"报告不裁决"的责任链（T0308 才有 FAILED）。下一站：T0307 Text Chunking（第 32–36 节，代码在 [ingest.py:416-531](../../backend/app/services/ingest.py#L416-L531)）——字符串在这里第一次变成结构化数据（chunk_id / content / chunk_index / file_id）。

---

## 32. T0307 定位：字符串第一次变成结构化数据

### 管道位置：Chunking 站

```text
T0301–T0305 Parse 站 ──▶ T0306 Cleaning 站 ──▶ T0307 Chunking 站 ──▶ T0308 编排 ✅
（五个 parser + OCR）    （clean_text）          （chunk_text）          （判定 SUCCESS/FAILED）
Path → str               str → str              str → List[dict]        接管道 + 拒绝（已落地，第 37–41 节）
```

chunk_text 站在清洗站与向量化之间：上游是 clean_text 交出的干净 str，下游是 Phase 2 的 `encode_chunks()`（它吃 `List[str]`）——**切分站是"字符串"与"结构化世界"的分界线**。

### 这一站为什么值得停下来看：四个"第一次"

- **① 数据形状的第一次分叉**：前六个 Task 全部 `str` 进 `str` 出（Path → str、str → str），chunk_text 是第一个 `str → List[dict]`——返回的每个 dict 带四键：chunk_id / content / chunk_index / file_id
- **② 身份体系的出生地**：SPEC 7.1 的 ID 规则（UUID4、不可变性、chunk_index 仅排序）从纸面规范第一次变成代码现实。**从今往后检索合并、去重、文件删除全都依赖这套 ID**——它们的"出生证明"在这里签发
- **③ 第一个"切分"性质的第三方库**：前三个第三方库（python-docx / openpyxl / fitz）都是"解析器"（把文件变文本），`langchain_text_splitters` 是"切分器"（把文本变块）——导入姿势相同（函数内），错误待遇不同（第 35 节⑤）
- **④ 第一个"裸奔"的第三方库导入**：第 4 次惰性导入，**唯一没有 try/except 包裹的**——docx/openpyxl/fitz 的导入失败都包成 AppError，langchain 的导入失败直接漏出（见第 35 节⑤为什么）

### 零偏移事件的终结：第 6 次偏移事件应验

上轮 Pass（T0307）创造了项目里唯一一次零偏移记录，并留下预言："若未来 T0308 在文件头部加东西，第 6 次偏移事件才会出现。"**T0308 落地，预言应验**：

- 模块 docstring 58 → 65 行（新增 "Ingest pipeline (SPEC F002/F004)" 契约段）+ imports 新增 `from datetime import datetime, timezone` → 头部以下所有锚点统一 **+8**
- chunk_text 内部另有变化：docstring 37 → 41 行（+4，写进 file_id 继承契约）+ `if file_id is None:` 单行变双行（+1）→ 函数体锚点再 +16（守卫至 overlap）/+17（Step 1 起）

"零偏移"纪录只维持了一个 Task 间隔——**行号偏移是这份学习文档的常态，零偏移才是特例**（完整偏移史见第 12 节）。教学上这也是一次"预言-应验"循环：上轮预告的偏移条件，本轮逐条兑现。

### 结构预览：六个片段

[ingest.py:416-430](../../backend/app/services/ingest.py#L416-L430) 常量区 → [433-478](../../backend/app/services/ingest.py#L433-L478) 签名 + docstring → [479-490](../../backend/app/services/ingest.py#L479-L490) 守卫 + 惰性导入 + ID 准备 → [492-508](../../backend/app/services/ingest.py#L492-L508) Step 1 标题切分 → [510-521](../../backend/app/services/ingest.py#L510-L521) Step 2/3 尺寸判定 → [523-531](../../backend/app/services/ingest.py#L523-L531) 返回列表推导。

chunk_text 是 99 行（docstring 41 + 函数体 57 + def 行）——T0308 之后**超过 ocr_page（95 行）成为全模块最长的函数**，但复杂度远低于后者：没有重试、没有网络、没有状态机。同时它有**全模块最长的 docstring（41 行）**：函数越"规则"，契约文字越多——因为它的行为几乎全部由 SPEC 定义，值得逐条写清楚。

---

## 33. 用 JS/TS 类比理解切分

### 一个直觉：切分 = 找边界

两种切分器本质都是"在合适的地方下刀"：

- **Markdown 标题切分**：按 `#` ~ `####` 这种**显式标记**下刀——结构化文本的边界是作者画好的
- **递归字符切分**：按**分隔符优先级**从粗到细找刀口——平文本的边界是猜出来的（先段落、再行、再句子标点、最后字符）

### 类比表

| Python（LangChain）                | 前端等价物                                  | 类比点                         |
| -------------------------------- | -------------------------------------- | --------------------------- |
| `MarkdownHeaderTextSplitter`     | 手写正则 `/^(#{1,4})\s+/` 扫描的分段函数          | 按标记切分 + 顺带记录标题层级            |
| `RecursiveCharacterTextSplitter` | 按优先级列表递归找分隔符的手写函数                      | 从 `"\n\n"` 一路降到 `""`（字符级兜底） |
| separators 优先级                   | CSS fallback 链（`font-family: A, B, C`） | 按顺序尝试，先找到的生效                |
| `chunk_overlap=120`              | 滑动窗口（sliding window）                   | 相邻块共享一段内容                   |
| `uuid.uuid4()`                   | `crypto.randomUUID()`                  | 随机 128 位全局唯一 ID             |
| `List[dict]` 四键字典                | `Array<ChunkRecord>`                   | 结构化输出                       |

### 两个简化 JS 实现（理解用，非生产）

标题切分（LangChain 版的骨架：扫标题行 → 每个标题开启新 section → 前导内容归属当前 section）：

```js
function splitByHeaders(md) {
  const sections = [];
  let cur = { path: [], lines: [] };
  const flush = () => { if (cur.lines.length) sections.push(cur); cur = { path: [], lines: [] }; };
  for (const line of md.split("\n")) {
    const m = line.match(/^(#{1,4})\s+(.*)$/);
    if (m) {
      flush();
      const level = m[1].length;
      cur.path = [...cur.path.slice(0, level - 1), m[2]];
    } else {
      cur.lines.push(line);
    }
  }
  flush();
  return sections;
}
```

递归切分（骨架：找到存在的最粗分隔符 → 切开 → 对每段递归；LangChain 真实实现还要做碎片合并、overlap、"切不动就放弃"——但递归骨架就是这样）：

```js
function recursiveSplit(text, separators, maxSize) {
  if (text.length <= maxSize) return [text];
  const sep = separators.find(s => text.includes(s));
  if (sep === undefined) return [text]; // 没有可用分隔符，放弃
  return text.split(sep).flatMap(part => recursiveSplit(part, separators, maxSize));
}
```

### 两个反直觉点

- **"标题切分对所有文件"**：JS 直觉是 .md 才需要标题切分。但 SPEC F006 Step 1 说 .md 用标题切分，Step 2.1 说非 .md 文件"先尝试标题切分"——两条合起来 = 所有文件都过一遍。无标题的纯文本过 MarkdownHeaderTextSplitter 会自然切成 1 个无前缀 section（零成本直通）——"尝试"被实现成了"总是"（第 35 节②）
- **"重叠约 120"不是精确值**：JS 滑动窗口是精确的（窗口步长确定），但 LangChain 的 overlap 发生在分隔符边界，实际重叠随文本浮动（Pending #21）。SPEC 用"约"字——规范者知道这一点

---

## 34. 逐行精读 chunk_text（第 433–531 行）

### 片段 0：分节线 + 常量区（[ingest.py:416-430](../../backend/app/services/ingest.py#L416-L430)）

```python
# ---------------------------------------------------------------------------
# Chunking & ID generation (SPEC F006)
# ---------------------------------------------------------------------------

# SPEC F006 Detail: header levels # → ## → ### → #### (metadata keys are
# the LangChain convention for MarkdownHeaderTextSplitter)
_MD_HEADERS_TO_SPLIT_ON = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
]

# SPEC F006 Detail: separator priority from high to low
_CHUNK_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
```

- 第 3 条分节线，第五区段开始——与 OCR 区（L253）、清洗区（L381）同款"功能横幅"
- 两个常量都是 **SPEC 参数的化身**：注释直接引用 SPEC 条目——与 `_MAX_TOTAL_ATTEMPTS`（"SPEC 9.3"）、`_OCR_PROMPT` 同款模式：**常量 + SPEC 出处注释**
- `_MD_HEADERS_TO_SPLIT_ON` 是**元组列表**：每对 =（Markdown 前缀, metadata 键）。键名 `"Header 1"`…`"Header 4"` 是 **LangChain 库的约定**（库把标题塞进 `doc.metadata` 时用的键）——第三方库的词汇表反向定义了我们的代码（手册 24.3）
- `_CHUNK_SEPARATORS` 从粗到细：段落（`\n\n`）→ 行（`\n`）→ 中文句末标点（。！？；，）→ 空格 → **空串**（字符级兜底）。最后这个 `""` 保证"任何长度都能切"——最坏情况按单字符拆
- 下划线前缀 = 模块私有约定（与 `_OCR_WARNINGS` 等五个先行者同款）

### 片段 1：签名 + docstring（[ingest.py:433-478](../../backend/app/services/ingest.py#L433-L478)）

- 契约自述四块：三步管道、ID 规则（file_id 继承或生成 / chunk_id 每块一个 / chunk_index 0-based）、惰性导入的失败路径（ImportError → 500，SPEC 9.4）、`source_file` 的装饰品参数声明
- **全模块最长的 docstring（41 行）**——行为几乎全部由 SPEC 定义，值得逐条写清；T0308 又补进一句 file_id 继承契约："The caller may supply `file_id`（the ingest pipeline generates it once per file, T0308）"
- 签名里有个"装饰品参数"：`source_file: str`。docstring 明说 "Kept for the frozen signature"——**它在函数体里一次都没被用到**（第 35 节②、Pending #20）。T0308 起签名多了一个**有行为**的参数：`file_id: Optional[str] = None`——装饰品之外，签名开始长肉了

### 片段 2：守卫 + 惰性导入 + ID 准备（[ingest.py:479-490](../../backend/app/services/ingest.py#L479-L490)）

```python
    if not text.strip():
        return []

    from langchain_text_splitters import (
        MarkdownHeaderTextSplitter,
        RecursiveCharacterTextSplitter,
    )

    if file_id is None:
        file_id = str(uuid.uuid4())
    max_chunk_size = settings.MAX_CHUNK_SIZE
    chunk_overlap = settings.CHUNK_OVERLAP
```

- **守卫**：`if not text.strip(): return []`——与 parse_pdf 的 `if text.strip():` 同款真值判断（手册 23.5 的"检测器"用法）。`strip()` 不能省：省了的话 `" \n "` 会继续往下走。**注意：守卫是"跳过"不是"拒绝"**——返回 `[]` 不 raise，FAILED 判定是 T0308 的事（责任链延续，第 40 节③已兑现）
- 管道内这个守卫其实已被 clean_text 覆盖（空白文本在清洗站就变 `""`）——它是**直接调用的第二道防线**（defense，不是 contract）
- **第 4 次惰性导入，唯一"裸奔"的**：docx/openpyxl/fitz 的导入都在 try 里包成 AppError；这里没有 try/except——docstring 自己解释了为什么："chunking has no catalog error code"（第 35 节⑤）
- **`file_id` 继承或生成（T0308 改的）**：原来是"循环外生成一次"（`str(uuid.uuid4())` 先于一切循环）。T0308 的 process() 需要"每文件一个"的身份在管道入口就存在（FAILED 回滚也要用，第 40 节①），于是签名新增 `file_id: Optional[str] = None`，函数体变成"**传了就用传的、没传才生成**"——缺省行为不变，直接调用者（练习、测试）一行不用改
- 两个尺寸参数从 `settings` 读出（800 / 120）——不在函数里写死，与 Phase 3 其他参数同款（第 1 节 config 契约）

### 片段 3：Step 1 —— 标题切分循环（[ingest.py:492-508](../../backend/app/services/ingest.py#L492-L508)）

```python
    # Step 1 — Markdown header splitting (every file, see docstring)
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_MD_HEADERS_TO_SPLIT_ON
    )
    candidates: List[str] = []
    for doc in header_splitter.split_text(text):
        content = doc.page_content
        if not content.strip():
            continue  # degenerate empty section — nothing to chunk
        header_values = [
            doc.metadata.get(key)
            for key in ("Header 1", "Header 2", "Header 3", "Header 4")
        ]
        header_path = " > ".join(value for value in header_values if value)
        if header_path:
            content = header_path + "\n\n" + content
        candidates.append(content)
```

- `doc` 是 LangChain 的 `Document` 对象（`page_content` + `metadata`）——不是 dict，所以用 `.page_content` / `.metadata` 属性
- **空 section 跳过**：两个相邻标题之间没有内容（如 `## A` 紧接着 `### B`）时库会吐出空 section——`continue` 兜住（与 clean_text 的过滤同思路）
- `header_values` 用 `metadata.get(key)` 而不是 `[key]`——**缺键返回 None 不炸**（无标题 section 的四个键全 None）
- `header_path`：过滤掉 None → `" > "` 连接——"过滤 + 连接"组合在项目里第三次出现（parse_docx 的 `" ".join(cell.text ...)`、clean_text 的过滤推导、这里）
- **前缀进 content**：`header_path + "\n\n" + content`——标题路径成为 chunk 内容的一部分（第 35 节③）
- **文件开头的前导内容**（第一个标题之前的段落）：header_path 为空 → 无前缀直通（Pending #22）

### 片段 4：Step 2/3 —— 尺寸判定（[ingest.py:510-521](../../backend/app/services/ingest.py#L510-L521)）

```python
    # Step 2/3 — oversized candidates re-split, short ones pass through
    recursive_splitter = RecursiveCharacterTextSplitter(
        separators=_CHUNK_SEPARATORS,
        chunk_size=max_chunk_size,
        chunk_overlap=chunk_overlap,
    )
    pieces: List[str] = []
    for candidate in candidates:
        if len(candidate) <= max_chunk_size:
            pieces.append(candidate)
        else:
            pieces.extend(recursive_splitter.split_text(candidate))
```

- 两个 splitter 都是**先构造、后使用**：LangChain 的 splitter 是"配置好的无状态工具对象"（构造时配好参数，调用时只吃文本）——前端类比：`new Intl.NumberFormat("zh-CN", opts)` 先构造再 `.format()`
- `len(candidate) <= 800` → 直通——**AC-F006-03（短文本单 chunk）的实现点**；短 section 零成本通过
- **append vs extend**（手册 24.4）：直通是单个 str → `append`；递归再切返回 `List[str]` → `extend`。换错的话：`append(列表)` 会嵌套出 `List[List[str]]`，下游 chunk 的 content 变成 list
- **短块不合并**：pieces 里没有任何合并逻辑——SPEC Step 3 的"不对过短 chunks 进行合并"和 F005 的 Step 5 一样，是"无代码"实现的（注释不需要，因为**没有合并的代码就是没有合并的行为**）
- 尺寸判定用 `len()` 数**字符**不是字节——中文 1 字符 = 1（Python str 是码点序列，手册 23 节前置知识）

### 片段 5：返回列表推导（[ingest.py:523-531](../../backend/app/services/ingest.py#L523-L531)）

```python
    return [
        {
            "chunk_id": str(uuid.uuid4()),
            "content": piece,
            "chunk_index": index,
            "file_id": file_id,
        }
        for index, piece in enumerate(pieces)
    ]
```

- 四键字典 = SPEC 7.4 ChunkRecord 的子集（embedding / metadata 由下游 Phase 2 与存储层补上）
- **`chunk_id` 每轮求值、`file_id` 引用函数参数**：列表推导每迭代一次就重新执行 `str(uuid.uuid4())` → 每块新 ID；`file_id` 引用片段 2 的变量（编排层传入或本函数生成）→ 全块共享。**求值位置决定"每块"还是"每次调用"**（手册 24.6 核心）
- `enumerate(pieces)` → 0-based 下标——SPEC 7.1 的"chunk_index 仅排序、0-based"天然兑现。**对比 T0305 的页码**：ocr_page 的 page_number 是 1-based（人类计数，两端都要 ±1 转换），chunk_index 是 0-based（机器身份，枚举天然）——同一个文件里两种计数哲学并存（第 35 节④）

### 自检 4 问（含答案）

1. 守卫里的 `.strip()` 省掉会怎样？——`" \n "` 会白跑 LangChain 切分（结果碰巧仍是 `[]`，因为空 section 被片段 3 的 continue 兜住）——**但不该依赖兜底**，守卫的意义就是"不进这扇门"
2. `source_file` 参数在函数体里出现了几次？——**0 次**。冻结签名：保留参数、声明不用（第 35 节②）——T0308 新增的 `file_id` 参数则相反：**有行为**（继承或生成）
3. `append` 和 `extend` 换错会怎样？——`append(列表)` 嵌套出 list-in-list；`extend(str)` 把字符串按字符拆开
4. `file_id` 和 `chunk_id` 的 `uuid4()` 位置互换会怎样？——file_id 每块不同（文件身份碎掉）、chunk_id 全块相同（块身份碎掉）。T0308 后 file_id 的生成点在"编排层传入"与"本函数兜底"之间二选一——两条路都必须在循环外

---

## 35. 设计决策深潜：五个值得停下来看的选择

### ① 两段式切分：语义边界优先

为什么先标题切分、再对超长候选递归再切——而不是一个 splitter 一刀切？

- **标题是作者画的语义边界**：按它切，chunk 边界落在章节处，检索命中时上下文完整；递归切分只是"尺寸警察"，收拾超长的漏网之鱼
- **反过来（先递归再标题）会碎**：递归切分不认识标题，会把 `## 章节A` 切成两半——语义边界先被破坏，后面想修复也晚了
- **效率**：大多数候选 ≤ 800 直接通过，递归只对少数超长候选运行
- 前端类比：组件拆分先按业务模块拆（语义），再对超大文件按行数拆（尺寸）——顺序不能反

### ② "先尝试标题切分" → "所有文件都过一遍"，以及 source_file 冻结签名（T0308 后修订：签名第一次演化）

SPEC Step 1 写"仅 .md 文件"做标题切分，Step 2.1 写非 .md 文件"先尝试 Markdown 标题切分（处理含标题的通用文本）"——两条合起来的逻辑后果是：**所有文件都过一遍标题切分**。实现把两条合流成一条"总是过一遍"：无标题的纯文本经过 split_text 自然产出 1 个无前缀 section（尝试的零成本实现）。

于是 `source_file` 参数在 v1 **没有任何行为作用**——但 SPEC F006 Define 的"输入"写了"源文件名 (str)"、TASKS 的实现范围也写了签名 `chunk_text(text: str, source_file: str)`。实现的处理：保留参数 + docstring 声明 "Kept for the frozen signature"。**冻结签名 = 契约优先于当前行为**：如果未来 Step 1 变回"仅 .md"，调用方一行不用改——参数已就位（Pending #20）。

**T0308 打破了这个冻结——但改法是"向后兼容的扩展"**：process() 需要"file_id 每文件一个"，于是 chunk_text 签名第一次被修改，新增 `file_id: Optional[str] = None`。注意三个细节：**只增不改**（source_file 原样保留）、**默认 None**（缺省行为与旧版完全一致）、**位置放最后**（旧的两种调用方式一行不用改）。"冻结"的实质不是"永不修改"，而是**修改必须是向后兼容的扩展**——函数契约和 API 契约在这点上同源（SPEC 7.7 的版本纪律）。source_file 依然 0 次使用（Pending #20）。

### ③ header path 前缀进 content：chunk 自包含

`"章节A > 小节A1\n\n内容"`——标题路径成为 chunk 内容的一部分。为什么？

- **检索命中时 chunk 脱离原文仍携带位置**：RAG 回答引用"这段来自哪一章"时可读、可引用
- **代价**：长章节多 chunk 时前缀重复占字符（每块都背着同一串路径）
- SPEC 明示要这样做（Step 1 第 3/4 条 + AC-F006-01 的 Then 原文）——实现无选择权
- 前端类比：面包屑（breadcrumb）——每条数据自带位置信息，而不是依赖全局上下文推断

### ④ UUID 身份体系：四字段分工（SPEC 7.1）

| 字段            | 角色        | 规则                                       |
| ------------- | --------- | ---------------------------------------- |
| `chunk_id`    | 块的全局唯一标识  | UUID4 每块一个；Hybrid merge / dedup / 引用依据   |
| `file_id`     | 文件的全局唯一标识 | UUID4 每文件一个——**T0308 起由编排层 process() 生成并传入；chunk_text 缺省时兜底生成**（继承或生成）；文件级删除、chunk 关联依据 |
| `chunk_index` | 块在文件内的顺序  | 0-based，仅排序，**不是 ID**                    |
| `file_name`   | 面向用户的显示名  | 仅显示，**不是 ID**                            |

- **为什么不是 `file_name:chunk_index` 当 ID**：重命名知识库会改 file_name（7.1 第 5 条：rename 不得改任何 ID）；重传同名文件视为新文件（新 file_id + 新 chunk_id）。拼接 ID 破坏不可变性——**身份必须与任何可变的显示信息解耦**
- **0-based 与 1-based 的对比**：chunk_index 0-based（机器身份，enumerate 天然）；ocr_page 的页码 1-based（人类计数，`page.number + 1` / `page_number - 1` 两端转换）——同一个文件里两种计数哲学并存，各有各的读者
- **下游用途预告**（第 8 章检索章会兑现）：Hybrid 检索 merge/dedup 靠 chunk_id；文件级删除靠 file_id；chunk_index 只用于排序展示

### ⑤ 错误哲学：切分没有目录错误码

对比 parser 与切分站的失败归属：

|         | parser（T0301–T0305）     | 切分（T0307）                                |
| ------- | ----------------------- | ---------------------------------------- |
| 失败含义    | "用户的文件坏了"（坏编码、坏 zip、加密） | "程序环境坏了"（库缺失、上游喂错类型）                     |
| 处理      | 包成 AppError → 目录码 422   | 不包 → 漏给全局处理器 → 500 INTERNAL_ERROR        |
| SPEC 依据 | F003 错误表                | 9.4（"chunking has no catalog error code"，docstring 原话） |

**400 与 500 的分界**：用户的错要翻译成可提示的码（422 FILE_PARSE_ERROR），系统的错要完整报出（traceback 进日志、响应只给 INTERNAL_ERROR）。切分的失败没有"用户可纠正"的含义——所以不占目录里的名额。

**与 T0306 责任链衔接**：空输入守卫只"跳过"（返回 `[]`）不"裁决"——空 list 与清洗站的空 str 一样，都是"报告"而非"拒绝"，FAILED 判定是 T0308（管道层）的活——**本节的"仍在"在 T0308 落地后成为历史**：process() 的两道闸门（cleaned 为空 / chunks 为空）正是接住这两类"报告"的裁决点（第 40 节③）。

---

## 36. SPEC F006 对照、诚实 AC 与新知识索引

### SPEC F006 逐条对照

| SPEC 条目                         | 实现                                       | 位置                                       |
| ------------------------------- | ---------------------------------------- | ---------------------------------------- |
| 参数 `max_chunk_size=800`         | `settings.MAX_CHUNK_SIZE`                | [ingest.py:489](../../backend/app/services/ingest.py#L489) |
| 参数 `chunk_overlap=120`          | `settings.CHUNK_OVERLAP`                 | [ingest.py:490](../../backend/app/services/ingest.py#L490) |
| separators 冻结清单                 | `_CHUNK_SEPARATORS`                      | [ingest.py:430](../../backend/app/services/ingest.py#L430) |
| Step 1 标题切分 `#`→`####`（.md）     | `MarkdownHeaderTextSplitter`（所有文件）       | [ingest.py:493-495](../../backend/app/services/ingest.py#L493-L495) |
| Step 1 标题路径前缀 `"章节 > 小节"`       | `" > ".join(...)` + `"\n\n"` 前缀          | [ingest.py:505-507](../../backend/app/services/ingest.py#L505-L507) |
| Step 2.1 非 md"先尝试"              | 与 Step 1 合流（同一循环）                        | [ingest.py:497](../../backend/app/services/ingest.py#L497) |
| Step 2.2 长度 ≤ max 直接保留          | `len <= max` → `append`                  | [ingest.py:518-519](../../backend/app/services/ingest.py#L518-L519) |
| Step 2.3 长度 > max 递归再切          | `split_text` → `extend`                  | [ingest.py:521](../../backend/app/services/ingest.py#L521) |
| Step 3 短文本单 chunk、不合并           | 直通 + 无合并代码                               | [ingest.py:518-519](../../backend/app/services/ingest.py#L518-L519) |
| chunk_id UUID4 每块               | `str(uuid.uuid4())` 循环内                  | [ingest.py:525](../../backend/app/services/ingest.py#L525) |
| file_id 每文件一个（**T0308 起继承或生成**） | `if file_id is None: file_id = str(uuid.uuid4())`——编排层传入则共享，缺省则本函数生成 | [ingest.py:487-488](../../backend/app/services/ingest.py#L487-L488) |
| chunk_index 0-based 仅顺序         | `enumerate`                              | [ingest.py:530](../../backend/app/services/ingest.py#L530) |
| 7.1 不可变性（rename 不动 ID）          | ID 与名字解耦（docstring 契约）                   | docstring                                |

### 诚实 AC 验证（T0307，不虚构 PASS）

仓库没有自动化测试（延续前六节的已知事实，第七次陈述）。**T0307 的验证门槛中等**：需要 `langchain_text_splitters` 包（requirements 已含，无网络下载），但不需要文件、网络、API key——一条 `python -c` 可验（练习 2）。我仍不虚构 PASS，只做代码审查层面的结构确认：

- **AC-F006-01**（Markdown 含 `## 章节A` + `### 小节A1` → 独立 chunks 带完整标题路径前缀）：结构确认——L497–507 实现 split_text + metadata 四键读取 + `" > "` join + `"\n\n"` 前缀；行为验证留给练习 2
- **AC-F006-02**（2000 字符段落 → 多个 ≤800 的 chunk、重叠约 120）：结构确认——L518–521 尺寸判定 + 递归再切。⚠️ 重叠是"约"：LangChain 的重叠发生在分隔符边界、尽力而为，不能逐字断言 120（Pending #21）
- **AC-F006-03**（300 字符 → 单 chunk 不切分）：结构确认——300 ≤ 800 → 直通路径；无标题的 300 字符文本经 split_text 产出 1 个无前缀 section → 1 块
- **TASKS 附加验证**（chunk_id/file_id 为合法 UUID4、chunk_index 从 0 顺序递增）：结构确认——`str(uuid.uuid4())` 保证格式；`enumerate` 保证 0-based 顺序；file_id 的"继承或生成"（L487–488）保证 T0308 传入时全块共享同一身份

**结论**：结构上满足三条 AC + 三项附加验证；行为验证留给学习练习 2（一条命令验证三条 AC）——T0308 已落地，其集成验证需要本地 embedding 模型 + ChromaDB（见第 41 节诚实 AC）。

### Python 新知识索引（→ 手册第 24 节）

| 知识点                                     | 手册位置    |
| --------------------------------------- | ------- |
| `uuid.uuid4()` + `str()`（UUID 对象 → 字符串） | 24.1    |
| `enumerate()`（带下标遍历）                    | 24.2    |
| 元组与元组列表（键值对常量表 + 解包）                    | 24.3    |
| `list.extend()` vs `append()`           | 24.4    |
| 惰性导入第四次出现（模式回顾）                         | 24.5    |
| 字典字面量 + 列表推导（造数据组合技）                    | 24.6    |
| 真值守卫 `if not text.strip()`（检测器用法）       | 手册 23.5 |

### 自测题（T0307，8 道）

1. chunk_text 的输入和输出形状各是什么？这个变化对整条管道意味着什么？
2. `if not text.strip(): return []` 的守卫是"拒绝"吗？谁才是真正的拒绝者？
3. 为什么标题切分适用于所有文件而不只是 .md？`source_file` 参数有什么用？
4. `"Header 1"` 这些 metadata 键是谁定义的？为什么我们的代码要用它？
5. 一段 2000 字符、无任何标题的文本，切分路径是什么？（从 split_text 到最终 chunks）
6. `pieces.append` 与 `pieces.extend` 的区别？换错了会怎样？
7. `file_id` 为什么在循环外生成、`chunk_id` 为什么在循环内？反了会怎样？
8. chunk_index 为什么不能当 ID？重命名知识库后哪些 ID 会变、哪些不变？

**答案**：① `str → List[dict]`——形状第一次分叉，下游 encode_chunks 吃 List[str]、存储层吃带 ID 的结构体。② 不是——返回 `[]` 只是"跳过"，T0308 管道层判定 FAILED 才是"拒绝"（责任链，第 40 节③）。③ SPEC Step 1 + Step 2.1 合起来 = 所有文件过一遍；无标题文本自然 1 个无前缀 section。`source_file` 在 v1 无行为作用（T0308 传入真实文件名后依然只是"身份标签"）——签名已被 T0308 首次修改（加 file_id），"仅 .md"之门仍开着（Pending #20）。④ LangChain 库的约定（markdown 标题在 metadata 里的键名）——第三方库的词汇表反向定义我们的代码。⑤ split_text → 1 个无前缀 section（候选）→ 2000 > 800 → 递归再切（按分隔符优先级）→ 多个 ≤800 的 chunk。⑥ append 加一个元素、extend 摊开加一筐；换错会嵌套 list 或把 str 拆成字符。⑦ 位置决定共享——但 T0308 起"外层"换成了 IngestService.process（每文件生成一次、全管道共享），chunk_text 只"继承或生成"（L487–488）：传了就用传的，没传才自己生成。chunk_id 仍在循环内生成。互换后文件身份/块身份碎裂。⑧ chunk_index 只表示文件内顺序、随内容变化，不能做全局身份；rename 知识库后 file_id / chunk_id / chunk_index 都不变（7.1 第 5 条），重传同名文件则全部换新。

### 练习（T0307）

1. **手推两段式切分**：拿一个含 `## 章节A`、`### 小节A1` 和一段 1000 字正文的 Markdown 文本，手推 split_text 的 section 划分、每个候选的 header_path、以及最终 chunks（哪些直通、哪些递归再切），再对照 `python -c` 验证。
2. **一条命令验证三条 AC**（需要 backend 依赖已装，无需网络/key）：
   ```bash
   python -c "
   from app.services.ingest import chunk_text
   md = '## 章节A\n内容X\n### 小节A1\n内容Y'
   print(chunk_text(md, 't.md'))          # AC-F006-01: 前缀 '章节A > 小节A1'
   cs = chunk_text('字' * 2000, 't.txt')   # AC-F006-02: 多块、每块 <= 800
   print(len(cs), [len(c['content']) for c in cs])
   one = chunk_text('字' * 300, 't.txt')   # AC-F006-03: 单块不切分
   print(len(one), one[0]['chunk_index'])  # 附加验证: index 从 0
   # file_id 继承实验（T0308 的签名扩展）:
   two = chunk_text('你好', 't.txt', file_id='FIXED')
   print(set(c['file_id'] for c in two))   # {'FIXED'}——所有块共享传入身份
   no_arg = chunk_text('你好', 't.txt')
   print(set(c['file_id'] for c in no_arg))  # 自动生成、且所有块同享一个
   "
   ```
3. **边界实验**：`"字" * 800` 与 `"字" * 801` 各跑一次，观察直通与递归再切的转折点——加深"≤ 800 直通"的边界直觉。

### T0307 快速复习卡

```text
T0307 — Text Chunking & ID Generation（chunk_text，第 433–531 行，99 行：docstring 41 + 函数体 58）
一句话：两段式切分把干净 str 变成带身份的结构化 chunk 列表

两段式：Markdown 标题切分（所有文件）→ 超长候选递归再切（≤ 800 直通、短块不合并）
守卫：空/纯空白 → []（跳过不裁决——FAILED 仍是 T0308 的事）
身份（SPEC 7.1）：file_id 继承或生成（T0308 起编排层传入）/ chunk_id 每块一个 / chunk_index 0-based 仅排序
前缀：header path "章节 > 小节\n\n内容"——chunk 自包含位置信息
错误哲学：无目录错误码——ImportError → 全局 500（SPEC 9.4）；切分的失败是"环境坏"，不是"文件坏"
偏移：本 Pass 零偏移（唯一一次）；T0308 落地即第 6 次偏移事件——"零偏移"纪录只维持了一个 Task 间隔
```

### Pending Questions（T0307 新增，学习中发现，未修复，仅记录）

19. **SPEC F006 Define 输出写 `List[str]`，Detail/7.4/TASKS 要求带 ID 的字典**：Define 表格"输出：chunks 列表 (List[str])"与 Detail 的 ID 生成规则、7.4 ChunkRecord、TASKS T0307 的 `List[dict]` 不一致。实现按后者（四键字典）。SPEC 定义表应更新为"chunks 列表（每块含 chunk_id / content / chunk_index / file_id）"。
20. **`source_file` 参数在 v1 无行为作用（T0308 后更新）**：F006 Define 输入含"源文件名 (str)"，但 v1 Detail 未定义其行为（Step 1 对所有文件生效）。实现保留参数但不参与逻辑。**T0308 起该参数第一次收到真实值**（file_name，经 process 传入）——但依然只作"身份标签"，不改变切分行为。若未来 Step 1 变回"仅 .md"，参数立刻有用；SPEC 需澄清 v1 该参数的角色。注：本函数签名已被 T0308 **首次修改**（新增 `file_id` 参数）——"冻结签名"时代结束（第 35 节②）。
21. **AC-F006-02 的"重叠约 120"不精确**：`RecursiveCharacterTextSplitter` 的重叠是 separator-aware 尽力而为——重叠发生在分隔符边界，实际重叠长度随文本浮动。SPEC 用"约"字所以实现合规，但验证时不能逐字断言 120。
22. **首个标题之前的内容无路径前缀**：文本在第一个标题之前的前导段落（无任何标题）时，header_path 为空 → chunk 无前缀。SPEC F006 未定义此场景（AC-F006-01 只覆盖"标题后内容"）。实现行为（直通无前缀）合理但未被 SPEC 显式覆盖。

---

> **T0307 部分完**。切分站是 Phase 3 的"形状转换站"：字符串在这里第一次变成带身份的结构化数据（chunk_id / content / chunk_index / file_id），SPEC 7.1 的身份体系在这里落地——从今往后检索合并、去重、文件删除都靠这套 ID。两段式切分是"语义优先"的务实选择：标题切分保住作者画的边界，递归切分只收拾超长的漏网之鱼。错误哲学延续 T0306 的责任链——守卫只跳过、不裁决，FAILED 仍是 T0308 的事；切分自己的失败（库缺失）则走 500 全局通道，不进目录。**下一站：T0308 Ingest Service 编排（✅ 已完成，第 37–41 节）**——管道在这里第一次被"接起来"，拒绝权在这里第一次被执行，而且它回头**改了 chunk_text 的签名**（file_id 继承）——"只加不改"惯例在 Phase 3 收官的 Task 里第一次被打破（第 12 节）。

---

## 37. T0308 定位：管道第一次被"接起来"

### 管道位置：SPEC F002 十步流程里的第 8 步

```text
F002 十步（SPEC 6.3 POST /api/v1/files）：
 1–7 上传层（校验/保存/重名检查……）    ← T0501/T0502 的活，本模块不碰
 8   Ingest Pipeline（parse→clean→chunk→embed→store）  ← ★ T0308
 9   关键词索引失效                        ← T0502 的活
 10  组装三态响应                          ← T0502 的活
```

SPEC F002 把"上传 API"和"摄入管道"拆成两个世界：上传层负责"文件从哪来、存到哪、答什么"，管道层负责"文件变成检索用的知识"。T0308 实现的是**步骤 8**——前七个 Task 造的零件（五个 parser、清洗、切分）加上 Phase 1/2 的向量存储与 embedding，第一次被按 SPEC 顺序**接成一条流水线**。

### 六个"第一次"：收官 Task 的新东西密度

- **① 模块第一个 class**：前七个 Task 造的是 7 个函数 + 1 组模块级状态，T0308 带来 `IngestService`——**函数已不足以表达"一个带多步骤、多出口、共享身份的过程"**，class 成为新的组织单位（形态进化第 4 步：单函数 → 多函数 → 分节+状态 → 类，见第 12 节）
- **② 第一次修改既有函数**：chunk_text 新增 `file_id` 参数——"只加不改"惯例被打破（第 35 节②）
- **③ 第一个编排者**：七个零件第一次有了"指挥"——它们谁都不认识谁，process() 是唯一知道全部顺序的代码
- **④ 第一个 400 目录码**：`UNSUPPORTED_FILE_TYPE`（[errors.py:48](../../backend/app/core/errors.py#L48)）——此前目录里全是 404/409/422/500，这是**第一个 400**（"请求本身不对"——扩展名根本不支持，不是"文件内容处理不了"的 422）
- **⑤ f-string 和 set 字面量第一次进项目**：`f"uploads/{collection_name}/{file_name}"`（第一个 f-string）、`_TEXT_EXTENSIONS = {".txt", ...}`（第一个 set）
- **⑥ FAILED 是第一个"不是错误的失败"**：全项目第一次出现"失败"作为**正常返回值**之一——不 raise、不 HTTP 错误，就是 dict 里一个 `"status": "FAILED"`（第 40 节③）

### 结构预览：第九个区段（第 534–683 行，150 行）

```text
第 534–537 行  第 4 条分节线 + 区段横幅     第六区段开始
第 538–539 行  两个扩展名常量集             文本五件套 / Excel 四件套
第 542–560 行  class IngestService + 类 docstring   状态模型 + 错误边界声明
第 562–587 行  process 签名 + 方法 docstring  入参出参 + Raises 契约
第 588–596 行  惰性导入 + 身份准备           file_id / upload_time / clear_ocr_warnings
第 598–608 行  管道主干 + 两道闸门           parse→clean→[闸]→chunk→[闸]→warnings→status
第 610–625 行  metadata 九字段组装           列表推导 + f-string + stat()
第 627–642 行  embed + store + 五键返回      encode_chunks + add_texts
第 644–656 行  _parse 扩展名分发             四个 if + 兜底 raise
第 658–683 行  _fail 回滚 + FAILED 组装      unlink + delete_by_file
```

---

## 38. 用 JS/TS 类比理解编排与三态

### `@classmethod` + `cls` ≈ static 方法的 `this`

```python
class IngestService:
    @classmethod
    def process(cls, file_path, ...):   # cls ≈ 类本身
        raw_text = cls._parse(file_path)  # cls._parse ≈ IngestService._parse
```

```ts
class IngestService {
  static process(filePath: string, ...) {
    const rawText = IngestService._parse(filePath);
  }
}
```

`cls` 在 TS 心智里就是"**static 方法体里的类引用**"：它不是实例（根本没有实例），是"以类名为名的命名空间"。注意一个诚实的细节：`_fail` 也标了 `@classmethod` 但**没用 `cls`**（Pending #24）——装饰器选了"风格统一"，不是"必须用到"。

### 三态返回 ≈ discriminated union（可辨识联合）

```ts
type IngestResult =
  | { status: "SUCCESS"; chunks_count: number; warnings: [] }
  | { status: "SUCCESS_WITH_WARNINGS"; chunks_count: number; warnings: OcrWarning[] }
  | { status: "FAILED"; chunks_count: 0; warnings: OcrWarning[] };
```

Python 的 dict 没有类型系统护航，**三态契约靠 docstring + SPEC 维持**——这是动态语言与 TS 结构类型的真实差距：TS 里 `switch (r.status)` 会收窄类型，Python 里调用方只能"信契约"。前端开发者读这段代码的加分项：**把三态理解成 discriminated union，契约的完整性要求就一目了然**（每种 status 下哪些键必有、值域是什么）。

### FAILED rollback ≈ compensating transaction（补偿事务）

没有数据库事务的分布式步骤（写文件、写 ChromaDB）做不到"真原子"，于是用**补偿**：失败后执行反向操作把已发生的副作用抹掉——`file_path.unlink()`（删文件）抵消"文件已保存"、`delete_by_file()`（删向量）抵消"万一有 chunk 残留"。前端类比：Saga 模式的补偿函数、或者 `try/finally` 里的清理——**"正向步骤 + 反向补偿"成对设计**。

### 其它小类比

| Python（T0308）                            | JS/TS                                    | 类比点                       |
| ---------------------------------------- | ---------------------------------------- | ------------------------- |
| `datetime.now(timezone.utc).isoformat()` | `new Date().toISOString()`               | UTC 时间戳字符串，机器可排序          |
| `f"uploads/{c}/{f}"`                     | `` `uploads/${c}/${f}` ``                | 字符串插值——Python 3.6+ 的模板字符串 |
| `{".txt", ".md", ...}`                   | `new Set([".txt", ...])`                 | 成员测试容器（`in` ≈ `.has()`）   |
| `file_path.unlink(missing_ok=True)`      | `fs.rmSync(p, { force: true })`          | "没有就跳过"的删除——幂等            |
| `IngestService` 整个类                      | 一个 service 模块（`export const ingestService = {...}`） | 无状态服务、以类为命名空间             |

---

## 39. 逐行精读 IngestService（第 534–683 行）

### 片段 0：分节线 + 两个扩展名常量集（第 534–539 行）

```python
# ---------------------------------------------------------------------------
# Ingest pipeline orchestration (SPEC F002 step 8, F004 status model)
# ---------------------------------------------------------------------------

_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}
_EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xltx", ".xltm"}
```

- **第 4 条分节线**：全文件六个区段齐了（1 parse×3 + 2 OCR + 3 cleaning + 4 chunking + 5 编排）
- **set 字面量第一次进项目**（手册 25.4）：花括号在这里是 set 不是 dict——dict 有键值对，set 只有元素。为什么不用 list？成员测试 `suffix in _TEXT_EXTENSIONS` 是 O(1)（哈希），list 是 O(n)——虽然这里就 5 个元素，**语义**才是关键："扩展名是不是这一族"天然是集合问题
- 文本五件套和 T0301 的 docstring 契约逐字一致；Excel 四件套含 `.xlsm`（带宏）/`.xltx`/`.xltm`（模板）——T0303 的契约
- 注意**没出现的格式**：`.pdf` 不在任何集合里（单独 if）、`.docx` 单独 if、`.txt` 之外的文本族（`.rtf`?）不支持——v1 范围

### 片段 1：class docstring——三块契约（第 542–560 行）

- **状态模型块**：SUCCESS / SUCCESS_WITH_WARNINGS / FAILED 的判定条件各一句——"no warnings, chunks > 0" / "OCR per-page warnings, chunks > 0" / "0 chunks（cleaned text empty）; rollback deletes the raw file and all its chunks"
- **职责边界块**："The keyword index is NOT touched here"——SPEC F002 步骤 9（关键词索引失效）明确划给上传层（T0502）。**docstring 写"不做什么"**是这个项目的老传统（clean_text 的"五不做"、SPEC 的 Out of Scope），边界靠声明
- **错误边界块**：parse/OCR/embedding 的 AppError "propagate unchanged"（原样穿透）——错误目录的映射是 API 层的事；"FAILED is returned as a status, not raised"——一句话区分了"错误"与"失败状态"两种哲学

### 片段 2：process 签名 + docstring（第 562–587 行）

```python
    @classmethod
    def process(
        cls,
        file_path: Path,
        file_name: str,
        collection_name: str,
    ) -> Dict[str, Any]:
```

- **`@classmethod` 第一次出现**（手册 25.1）：手动里只有 `@staticmethod`（T0108）。区别：classmethod 把**类本身**作为第一个参数传入（`cls`），staticmethod 什么都不传。这里选 classmethod 的原因见第 40 节④
- **入参形状**：`file_path` 是"已保存的原始文件"（docstring 写明 saved by the upload layer）——**T0308 不负责保存**（Out of Scope 划给 T0502）；`file_name` 仅显示；`collection_name` 是知识库名
- **docstring 的 Raises 块列了 6 个错误码**：UNSUPPORTED_FILE_TYPE、FILE_PARSE_ERROR、ENCRYPTED_PDF、OCR_NOT_CONFIGURED、OCR_AUTH_FAILED、EMBEDDING_MODEL_ERROR——**本函数一个都不接**，全是"上游抛、我转手"（错误边界声明，第 40 节⑤）

### 片段 3：惰性导入 + 身份准备（第 588–596 行）

```python
        from app.core.vector_store import ChromaVectorStore
        from app.services.embedding import encode_chunks

        # Per-file lifecycle: one file_id for all chunks of this upload
        # (SPEC 7.1), one upload timestamp (denormalized, SPEC 7.4),
        # fresh OCR warning list (T0305 channel).
        file_id = str(uuid.uuid4())
        upload_time = datetime.now(timezone.utc).isoformat()
        clear_ocr_warnings()
```

- **第 5、6 次惰性导入**（惯例连续七次，第 7 次在 `_fail`）：`ChromaVectorStore` 和 `encode_chunks` 都是重依赖（ChromaDB 客户端 / sentence-transformers 模型），不进模块顶部。**有趣的是 ChromaVectorStore 在同一个模块里被 import 了两次**（这里 + `_fail`）——Python 的 sys.modules 缓存让第二次 import 近乎免费，代价只是两处重复一行（Pending #24 相关讨论见第 40 节④）
- **`file_id` 在管道第一行生成**——"身份先于管道"（第 40 节①）
- **`upload_time`**：`datetime.now(timezone.utc).isoformat()`（手册 25.2）——UTC 显式声明 + ISO 8601 字符串。`timezone.utc` 不能省：省略时区的话跨服务器/跨时区部署时同一时刻会写出不同字符串。**取一次、全文件共享**——SPEC 7.4 的"file-level 字段跨 chunk 一致"在这里锚定
- **`clear_ocr_warnings()`**：T0305 的"穷人版单例"生命周期终于被执行——**清空发生在身份准备之后、管道之前**；收尾在 `get_ocr_warnings()`（片段 4/8）。这是 T0304 注释里"Lifecycle is owned by the ingest pipeline (T0308)"的兑现时刻

### 片段 4：管道主干 + 两道闸门（第 598–608 行）

```python
        raw_text = cls._parse(file_path)
        cleaned = clean_text(raw_text)
        if not cleaned:
            return cls._fail(file_path, file_id, file_name, collection_name)

        chunks = chunk_text(cleaned, file_name, file_id=file_id)
        if not chunks:
            return cls._fail(file_path, file_id, file_name, collection_name)

        warnings = get_ocr_warnings()
        status = "SUCCESS_WITH_WARNINGS" if warnings else "SUCCESS"
```

- **F002 的管道顺序逐字兑现**：parse → clean → chunk →（embed → store 在片段 6）。四个调用全部平铺直写、无嵌套 try——因为错误不在这里处理（第 40 节⑤）
- **闸门 ①**：`if not cleaned:`——接住 clean_text 的 `""`（T0306 的"报告不裁决"，第 30 节③的责任链终点）
- **闸门 ②**：`if not chunks:`——接住 chunk_text 的 `[]`（T0307 守卫）
- **两道闸门走同一个出口**：`_fail`——失败路径归一化（第 40 节②）。注意闸门里的 `return` 让后面的代码自然形成"成功走廊"（happy path 无嵌套）
- **`file_id=file_id` 关键字实参**（手册 25.3）：chunk_text 的第三参是新加的，用关键字传——**位置参数防的是"签名再变"**：未来 source_file 和 file_id 顺序调整，关键字调用不受影响
- **`warnings` 快照 + 状态判定**：warnings 非空 ⇔ 有页级 OCR 失败 ⇔ SUCCESS_WITH_WARNINGS（F004 的三态定义）。**判定时机**在 chunk 之后——warnings 只在 parse 阶段产生，chunk 后快照 = 完整收集
- **`get_ocr_warnings()` 的防御性拷贝**（T0305）在这里派上用场：拿到的是拷贝，之后 `_fail` 再取也不会互相污染

### 片段 5：metadata 九字段组装（第 610–625 行）

```python
        metadatas = [
            {
                "chunk_id": chunk["chunk_id"],
                "file_id": file_id,
                "file_name": file_name,
                "collection_name": collection_name,
                "chunk_index": chunk["chunk_index"],
                "source_file": f"uploads/{collection_name}/{file_name}",
                "file_size": file_path.stat().st_size,
                "upload_time": upload_time,
                "ingestion_status": status,
            }
            for chunk in chunks
        ]
```

- **F008 Metadata Schema 的九字段**：SPEC 7.4 定义、F008 公共接口消费——chunk_id / file_id / file_name / collection_name / chunk_index / source_file / file_size / upload_time / ingestion_status，一个不少（第 41 节逐条对照）
- **`chunk_id` 和 `chunk_index` 从 chunk 里搬**，其余七个对每个 chunk 都相同——**denormalization（反规范化）**：SPEC 7.4 明示"file-level 字段跨 chunk 冗余存储"，为的是检索时**单块自足**（不用 join 回文件表查 file_size）
- **f-string 第一次出现**（手册 25.5）：`f"uploads/{collection_name}/{file_name}"`——`source_file` 的路径由两部分拼成。注意它不是从 `file_path` 取的：file_path 是保存位置的**实现细节**，source_file 是 SPEC 规定的**展示路径**（v1 恰好一致）
- **`file_path.stat().st_size`**：每个 chunk 都 `stat()` 一次——文件存在（闸门已保证非空文本），size 不变，结果一致。可以提到循环外，但九字段列表推导的"每行一个键"对称性更可读（微效率 vs 可读性，实现选了可读性）
- **`ingestion_status: status`**：status 在 metadata 里也冗余一份——查询层不用翻 ingest 结果就能按状态过滤

### 片段 6：embed + store + 五键返回（第 627–642 行）

```python
        embeddings = encode_chunks([chunk["content"] for chunk in chunks])
        store = ChromaVectorStore()
        store.add_texts(
            collection=collection_name,
            chunks=[chunk["content"] for chunk in chunks],
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return {
            "status": status,
            "file_id": file_id,
            "file_name": file_name,
            "chunks_count": len(chunks),
            "warnings": warnings,
        }
```

- **`[chunk["content"] for chunk in chunks]` 出现两次**（embed 和 add_texts 各一次）——同一批字符串喂给 Phase 2 的 `encode_chunks` 和 Phase 1 的 `add_texts`。**前两个 Phase 造的零件在这里第一次被 Phase 3 使用**：T0202 的 `encode_chunks` 等这个调用方等了 5 个 Task，T0108 的 `add_texts` 等了 7 个
- **`store = ChromaVectorStore()` 直接实例化**（不是惰性单例模式）——ChromaDB 的 PersistentClient 是轻量客户端，构造开销可接受；与 embedding 的 `get_model()` 懒加载单例（模型重）形成对比：**重资源懒加载、轻资源直接建**
- **五键 dict（第二次形状分叉）**：status / file_id / file_name / chunks_count / warnings——**没有文本**。文本进管道，出来的是"状态 + 元数据"（第 22 节分工表的第八列）
- **keyword 实参**：`add_texts(collection=..., chunks=..., embeddings=..., metadatas=...)`——四个都带名，长参数列表防顺序错误

### 片段 7：_parse 扩展名分发（第 644–656 行）

```python
    @staticmethod
    def _parse(file_path: Path) -> str:
        """Dispatch to the per-extension parser (SPEC F003)."""
        suffix = file_path.suffix.lower()
        if suffix in _TEXT_EXTENSIONS:
            return parse_text_file(file_path)
        if suffix == ".pdf":
            return parse_pdf_file(file_path, ocr_page=ocr_page)
        if suffix == ".docx":
            return parse_docx_file(file_path)
        if suffix in _EXCEL_EXTENSIONS:
            return parse_excel_file(file_path)
        raise AppError("UNSUPPORTED_FILE_TYPE")
```

- **`@staticmethod`（不是 classmethod）**：分发逻辑不碰 `cls` 也不碰 self——T0108 学过的装饰器第一次在 ingest.py 出现。两个装饰器在同一个类里并存：**用到类引用就 classmethod，用不到就 staticmethod**（第 40 节④）
- **`suffix.lower()`**：`.PDF` 和 `.pdf` 同等待遇——路径后缀大小写不敏感是文件系统的常态。**`.lower()` 让集合比较在比较前统一口径**
- **`.pdf` 单独 if（不在集合里）**：因为它的调用**带实参**（`ocr_page=ocr_page`）——集合只能判"在不在"，带参调用必须单独分支。这也是 T0304 冻结契约的兑现：调用方确实传了回调（Pending #13 的担忧未触发）
- **兜底 `raise AppError("UNSUPPORTED_FILE_TYPE")`**：四个 if 全不中 → 400——"请求本身不对"。**这是 ingest.py 里第一个 raise 在函数尾的"合法值域"式分发**：先列合法、最后拒绝（与 parse_text_file 的"级联后最终 raise"同构，一个是编码尝试、一个是格式枚举）
- **和 T0502 的配合**：上传层的校验会先过滤扩展名，`_parse` 的 raise 是第二道防线（防绕过）——defense in depth

### 片段 8：_fail 回滚 + FAILED 组装（第 658–683 行）

```python
    @classmethod
    def _fail(
        cls,
        file_path: Path,
        file_id: str,
        file_name: str,
        collection_name: str,
    ) -> Dict[str, Any]:
        """FAILED rollback + result dict (SPEC F002 failure atomicity)."""
        from app.core.vector_store import ChromaVectorStore

        file_path.unlink(missing_ok=True)
        ChromaVectorStore().delete_by_file(collection_name, file_id)
        return {
            "status": "FAILED",
            "file_id": file_id,
            "file_name": file_name,
            "chunks_count": 0,
            "warnings": get_ocr_warnings(),
        }
```

- **`unlink(missing_ok=True)`**（手册 25.7）："文件不存在就算成功"——**幂等**。为什么需要幂等？两道闸门进来时文件一定存在（上传层保存的）……但未来重试、并发、或调用顺序变化时不保证——幂等让 rollback "多执行一次无害"
- **`delete_by_file(collection_name, file_id)`**：F008 的公共接口第一次被真实调用——按 file_id 删残留 chunk。**闸门 ② 之前没有任何 store 写入**，所以这里是"清空式防御"：正常路径下没有残留，但执行了也不炸
- **FAILED 的 warnings 也带**：`get_ocr_warnings()` 再取一次——比如 PDF 所有页 OCR 失败 → 页级 warnings 收集了、但文本为空 → 闸门 ① 触发 → FAILED **带 warnings** 返回（F004 结构：FAILED 时 warnings 仍要有内容，不能丢）
- **`@classmethod` 但没用 `cls`**（Pending #24）：功能上 `@staticmethod` 也行——选 classmethod 是风格统一（与 process 对称）。诚实的观察：**装饰器的选择有时是"对称性"而非"必要性"**
- **_fail 不 raise、只返回**：FAILED 是"业务结果"，走 return 通道；真正的异常（文件系统错误、ChromaDB 连接错误）不在这里处理，直接漏给全局 handler——**回滚自身失败 = 环境问题 = 500**，不是三态能表达的事

### 读完自检：4 个问题（T0308）

1. `file_id` 为什么在 process() 的第一行生成，而不是在 chunk_text 里？
2. 两道闸门（`if not cleaned:` / `if not chunks:`）为什么不合并成一个？
3. `_parse` 的 `.pdf` 分支为什么不进 `_TEXT_EXTENSIONS` 集合？
4. `_fail` 里的 `delete_by_file` 在正常流程（闸门触发时）真的删到东西吗？

（答案：① 因为 FAILED 可能发生在 chunk_text 之前（cleaned 为空），回滚需要 file_id 去 `delete_by_file`——身份必须先于管道存在，且"每文件一个"是编排层的职责，chunk_text 只"继承或生成"。② 两道闸门各自对应不同站点的"报告"：clean_text 的 `""` 和 chunk_text 的 `[]`——虽然都是空值，但**来源不同、语义不同**，且未来某个站点可能想对空值做不同处理；合并成"chunk 后统一判"会丢掉"哪一站空的"信息（虽然 v1 的 FAILED 响应不带这个信息，代码结构保留了可扩展性）。③ 因为它的调用带实参（`ocr_page=ocr_page`）——集合只能判成员，带参调用必须单独分支。④ 删不到——两道闸门都在 store 写入之前触发，`delete_by_file` 是幂等防御（"清空式回滚"），防的是未来顺序变化或残留场景。）

---

## 40. 设计决策深潜：五个值得停下来看的选择

### ① 身份先于管道：file_id 为什么在 process() 顶部生成

FAILED 可以发生在**任何 chunk 存在之前**（清洗后为空、切分后为空），而 FAILED 的回滚要用 `file_id` 调 `delete_by_file`。如果 file_id 生成在 chunk_text 里（T0307 的原位置），闸门 ① 触发时**根本没有 file_id 可用**——回滚的"删 chunk"一步就没了钥匙。

于是 T0308 做了两个动作：**生成点上移**到 process() 第一行 + **签名扩展**让 chunk_text 接收它（第 35 节②）。"每文件一个"的决策权从函数上移到编排层——因为**只有编排层知道"这个文件"的完整生命周期**（从保存到回滚）。设计原则一句话：**身份的生命周期边界 = 管道入口，谁拥有生命周期谁生成身份**。

### ② 失败路径归一化 + 幂等 rollback

两道闸门 → 同一个 `_fail`：**所有失败形态收敛到一条路径**。好处：

- **回滚逻辑只有一份**：unlink + delete_by_file 写一次，两处闸门共享——未来加第三道闸门（比如 embedding 后校验）只需要多一行 `return cls._fail(...)`
- **幂等设计让"清空式回滚"成立**：`missing_ok=True` + `delete_by_file` 在"没有任何副作用发生"时执行也安全——**回滚可以不精确，但不能不幂等**。对比前端：`try { ... } catch { cleanup() }` 里的 cleanup 写两遍就迟早漂移

SPEC F002 的四项原子性检查里，前两项（uploads/ 无残留、ChromaDB 无残留）由这里的两个幂等操作保证；后两项（keyword index 干净、重传不被 409 卡）属于上传层（T0502）——**原子性被拆在两个 Task 里实现，本类只承担自己的一半**。

### ③ FAILED 是返回值，不是异常

```text
文件内容"空/不可用"  →  三态里的 FAILED（return）        ← 业务结果，用户可理解
文件本身"坏了/不支持" →  AppError（raise）→ 4xx/5xx        ← 错误，用户要纠正
```

判据：**失败原因是不是"用户可纠正的错误"**。空文件 → "换个文件"是产品语义，SPEC 决定用三态表达；损坏的 zip / 不支持的类型 → 是错误，走错误目录（422/400）。两种通道的边界在 docstring 里写死："FAILED is returned as a status, not raised"。

这个区分有一个微妙后果：**SUCCESS_WITH_WARNINGS 里的 warnings 与 FAILED 的 warnings 同构**——页级失败在两种状态下都只是 warnings 列表里的条目（F004 结构），FAILED 不因为"更失败"就改 warnings 的格式。

### ④ 为什么用 class 而不是第 8 个函数

process/_parse/_fail 三个方法其实可以写成三个模块级函数（`_parse` 甚至已经是 staticmethod）。选 class 的理由：

- **一组内聚的私有成员**：`_parse` 和 `_fail` 的私有性由下划线表达——class 让"这是编排内部件"的边界更清楚（虽然模块级下划线也有同样效果）
- **未来可扩展的挂点**：v2 若需要"按 collection 配置管道参数"，class 可以加实例属性；模块级函数要改签名
- **spec 里的措辞**：SPEC F002 写 "Ingest Service"——实现用同名 class 让"规范里的名词"和"代码里的名词"一一对应

**诚实的代价**：`@classmethod` 的 `cls` 在 `_fail` 里没用上（Pending #24）、`ChromaVectorStore` 被 import 两次。**设计没有免费的午餐**——class 的组织收益 vs 装饰器的仪式感，实现选了组织收益。

### ⑤ 错误边界传播 + 双闸门：兜"空"不兜"错"

process() 对错误的态度是**一刀切的穿透**：

```text
parse 的 422（FILE_PARSE_ERROR/ENCRYPTED_PDF）  ─┐
OCR 的 500（NOT_CONFIGURED/AUTH_FAILED）        ├─→ 原样传播，process 不接
embedding 的 500（EMBEDDING_MODEL_ERROR）       ─┘
空文本/空 chunks                                 ──→ 闸门接住 → _fail（FAILED）
```

为什么编排层不 try/except 包一层？**编排层不知道错误该映射成什么 HTTP 码**——那是 API 层（T0502）的事；中间包一层只会丢失错误类型（全变 INTERNAL_ERROR）。**错误边界声明在 docstring**（Raises 块列全 6 个码），调用方按声明写契约。

这也解释了双闸门与 try 的边界：**"空"是数据问题（可判、可回滚），"错"是执行问题（传播、让上层翻译）**——两条通道泾渭分明。遗留的 SPEC 空白：AppError 路径（如损坏文件）下**没有 rollback**，raw 文件会留在 uploads/（Pending #27）——SPEC F002 的原子性表只覆盖三态，不覆盖异常路径，这是 T0502 集成时要面对的规范缺口。

---

## 41. SPEC F002/F004/F008 对照、诚实 AC 与新知识索引

### SPEC F002 逐条对照（本 Task 承担的部分）

| #       | SPEC 要求                                  | 实现位置                                     | 结论                  |
| ------- | ---------------------------------------- | ---------------------------------------- | ------------------- |
| 步骤 8a   | 按扩展名选择 parser                            | [ingest.py:644-656](../../backend/app/services/ingest.py#L644-L656) `_parse` 四个 if + 兜底 raise | ✅                   |
| 步骤 8b   | parse → clean → chunk → embed → store 顺序 | [ingest.py:598-634](../../backend/app/services/ingest.py#L598-L634) 平铺直写、逐字对应 | ✅                   |
| 步骤 8c   | 三态判定（warnings 非空 + chunks>0 → SUCCESS_WITH_WARNINGS 等） | [ingest.py:607-608](../../backend/app/services/ingest.py#L607-L608) | ✅                   |
| 原子性 ①   | FAILED → uploads/ 无残留文件                  | [ingest.py:675](../../backend/app/services/ingest.py#L675) `file_path.unlink(missing_ok=True)` | ✅ 本类承担              |
| 原子性 ②   | FAILED → ChromaDB 无残留 chunk              | [ingest.py:676](../../backend/app/services/ingest.py#L676) `delete_by_file` | ✅ 本类承担              |
| 原子性 ③   | FAILED → keyword index 干净                | 不在本类——上传层 T0502 负责（docstring 明示）         | ⏭ DEFERRED TO T0502 |
| 原子性 ④   | 重传同名文件不被 409 卡                           | 上传层的重名逻辑（T0502）                          | ⏭ DEFERRED TO T0502 |
| 步骤 9/10 | 关键词索引失效、三态响应                             | 上传层 T0502                                | ⏭ DEFERRED TO T0502 |

### SPEC F004 逐条对照

| #                | SPEC 要求                                  | 实现位置                                     | 结论          |
| ---------------- | ---------------------------------------- | ---------------------------------------- | ----------- |
| 状态模型             | SUCCESS / SUCCESS_WITH_WARNINGS / FAILED 三态 | [ingest.py:608](../../backend/app/services/ingest.py#L608) + [ingest.py:678](../../backend/app/services/ingest.py#L678) 两个出口 | ✅           |
| warnings 结构化     | `{page_number, error_code}` 列表贯穿三态       | [ingest.py:607](../../backend/app/services/ingest.py#L607)（成功路径）+ [ingest.py:682](../../backend/app/services/ingest.py#L682)（FAILED 路径） | ✅ 两种路径都带    |
| warnings 生命周期    | clear per file                           | [ingest.py:596](../../backend/app/services/ingest.py#L596) `clear_ocr_warnings()`——T0305 注释的兑现 | ✅           |
| OCR 失败 → 页级容错不中断 | ocr_page 内部实现（T0305），编排层不干预              | 经 `_parse` 的 `ocr_page=ocr_page` 传参启用    | ✅（T0305 已验） |
| 禁止静默忽略           | warnings 进入返回 dict 的 `warnings` 键        | 五键 dict                                  | ✅ 结构保证      |

### SPEC F008 Metadata Schema 九字段逐条对照（[ingest.py:612-625](../../backend/app/services/ingest.py#L612-L625)）

| 字段               | 值来源                                      | 类型          |
| ---------------- | ---------------------------------------- | ----------- |
| chunk_id         | chunk 搬运（chunk_text 生成）                  | str UUID4   |
| file_id          | process() 顶部生成、全块共享                      | str UUID4   |
| file_name        | 入参（仅显示）                                  | str         |
| collection_name  | 入参（知识库名）                                 | str         |
| chunk_index      | chunk 搬运                                 | int 0-based |
| source_file      | f-string 拼接 `uploads/{collection_name}/{file_name}` | str         |
| file_size        | `file_path.stat().st_size`               | int 字节      |
| upload_time      | process() 顶部取一次（ISO 8601 UTC）            | str         |
| ingestion_status | 三态 status 冗余                             | str         |

七条一致（七个 file-level 字段跨 chunk 相同，SPEC 7.4 的 denormalization 约束）+ 两条搬运（chunk_id/chunk_index 逐块不同）——**字段齐全、一致性靠"循环外取一次"保证**。

### 诚实 AC 验证（T0308，不虚构 PASS——第八次陈述）

仓库**没有自动化测试**（延续前七节的已知事实）。涉及的 AC：**AC-F002-08**（SUCCESS → 元数据/状态正确）、**AC-F002-09**（FAILED 回滚 → 四项残留检查）、**AC-F004-03**（部分页失败 → SUCCESS_WITH_WARNINGS）、**AC-F004-04**（全部失败 → FAILED）。

**本 Task 是 Phase 3 验证门槛最高的一站**：完整行为验证需要本地 embedding 模型（sentence-transformers 下载）+ ChromaDB 持久化目录 + 上传 API（T0501/T0502 未实现）——**上传 API 还不存在，端到端验证在 v1 当前进度下无法进行**。我没有构造环境、没有虚构 PASS。代码审查层面的结构确认：

| 检查项                                      | 方式                        | 结果                  |
| ---------------------------------------- | ------------------------- | ------------------- |
| 三态判定条件与 F004 一致                          | 读 L607-608 + L677-683     | ✅ 一致                |
| 九字段与 F008 一致                             | 逐字段对照上表                   | ✅ 一致                |
| 回滚两步（unlink + delete_by_file）幂等          | 读 L675-676                | ✅ 一致                |
| warnings 两条路径都携带                         | 读 L607 + L682             | ✅ 一致                |
| 6 个 AppError 原样传播（无 try 包裹）              | 读 L598-642 全段             | ✅ 一致                |
| uploads/ 无残留、ChromaDB 无残留（AC-F002-09 前两项） | 结构确认：闸门先于 store 写入 + 幂等回滚 | ✅ 结构保证              |
| keyword index 干净、重传不被 409 卡（AC-F002-09 后两项） | 上传层职责（TASKS 明示 T0502）     | ⏭ DEFERRED TO T0502 |

**行为验证建议**（学习者自证）：`_parse` 的扩展名分发是**轻量实验**（练习 2）；process() 全流程需要本地模型 + ChromaDB，可等 Phase 5 上传 API 落地后再做端到端验证（TASKS 的 T1201 验收阶段也会覆盖）。

### Python 新知识索引（→ 手册第 25 节）

| 新概念                                      | 一句话                                   | 手册位置 |
| ---------------------------------------- | ------------------------------------- | ---- |
| `@classmethod` + `cls`                   | 类方法：第一个参数是类本身，`cls` ≈ static 方法的 this | 25.1 |
| `datetime.now(timezone.utc).isoformat()` | UTC 时间戳字符串——显式时区 + ISO 8601           | 25.2 |
| 关键字实参 `file_id=file_id`                  | 按参数名传值——防签名漂移                         | 25.3 |
| set 字面量 `{".txt", ...}`                  | 无重复无序容器；`in` 成员测试                     | 25.4 |
| f-string `f"uploads/{c}/{f}"`            | Python 3.6+ 字符串插值（≈ JS 模板字符串）         | 25.5 |
| `Optional[str] = None` 默认参数              | "可传可不传"的类型表达                          | 25.6 |
| `Path.unlink(missing_ok=True)`           | 幂等删除："不存在也算成功"                        | 25.7 |
| 惰性导入第 5–7 次                              | 惯例回顾（ChromaVectorStore 被 import 两次）   | 25.8 |

已学概念复用：`@staticmethod`（T0108，与 classmethod 对照）、`raise AppError`（T0103 起）、`uuid.uuid4()`（T0307）、`settings` 配置契约（T0002）、`get_ocr_warnings` 防御性拷贝（T0305）、列表推导造 dict（T0307 手册 24.6）、`Dict[str, Any]` 返回值标注（T0302）、`if not x` 真值判断（T0306）。

### 自测题（T0308，8 道）

1. F002 十步流程里 T0308 承担哪一步？步骤 1–7、9、10 归谁？
2. `file_id` 为什么上移到 process()？如果还在 chunk_text 里，哪个场景会出问题？
3. FAILED 为什么不 raise？"用户可纠正的错误"和"业务结果"的分界判据是什么？
4. 两道闸门各自接住哪个站点产出的空值？合并成一道会丢什么信息？
5. `_parse` 里 `.pdf` 为什么单独 if？`suffix.lower()` 防的是什么？
6. 回滚的两步为什么都要幂等？"清空式回滚"成立的前提是什么？
7. metadata 九字段里哪两个是"搬运"的？哪七个是 file-level 冗余？为什么冗余（denormalization）？
8. `clear_ocr_warnings()` 和 `get_ocr_warnings()` 分别在什么时候调用？为什么 FAILED 路径也要取 warnings？

**答案**：① 步骤 8（parse→clean→chunk→embed→store）。1–7（校验/保存/重名）和 9（关键词索引失效）、10（响应组装）都是上传层 T0502 的活。② 因为 FAILED 可能发生在 chunk 之前（cleaned 为空 → 闸门 ①），回滚要 file_id 调 delete_by_file——身份先于管道。③ 空文件是"换一个"的产品语义，不是用户要纠正的错误——SPEC 决定三态表达；损坏文件/不支持类型才走 AppError → 4xx/5xx。④ 闸门 ① 接 clean_text 的 `""`、闸门 ② 接 chunk_text 的 `[]`；合并会丢"哪一站空的"信息。⑤ `.pdf` 调用带实参（ocr_page）必须单独分支；`.lower()` 统一大小写口径（`.PDF` 也认）。⑥ unlink 的 missing_ok=True、delete_by_file 删不存在的也安全——幂等让"多执行一次无害"；前提是闸门先于一切写入（正常路径下回滚其实是空操作）。⑦ chunk_id/chunk_index 搬运；其余七个 file-level 冗余——检索时单块自足，不用回文件表 join。⑧ clear 在管道开始前（身份准备时），get 在 chunk 之后（成功路径）和 _fail 里（FAILED 路径）；FAILED 也要 warnings 是因为 F004 结构要求 FAILED 时 warnings 仍完整携带（如全页 OCR 失败 → FAILED + warnings）。

### 练习（T0308）

1. **手推三态**：构造三个输入——① 正常文本文件 ② 混合 PDF（第 1 页原生、第 2 页 OCR 失败）③ 空文件——对每个输入推演：两道闸门各过没过？status 是什么？warnings 里有什么？回滚执行了哪几步？再对照片段 4/8 的代码核对。
2. **_parse 轻量实验**（不需要模型、不需要 ChromaDB）：
   ```python
   from pathlib import Path
   from app.services.ingest import IngestService
   # 造一个临时 txt，只测分发：
   p = Path("test.TXT"); p.write_text("hello", encoding="utf-8")
   print(IngestService._parse(p))          # "hello"——suffix.lower() 认大写
   print(IngestService._parse(Path("a.exe")))  # AppError: UNSUPPORTED_FILE_TYPE (400)
   p.unlink()
   ```
   亲手确认"分发正确"和"兜底拒绝"——**Phase 3 里唯一不需要模型就能验证 T0308 行为的实验**。
3. **file_id 继承实验**（对照第 36 节练习 2 的扩展）：`chunk_text('你好', 't.txt', file_id='FIXED')` 的所有块 file_id 都是 'FIXED'；不传则自动生成——然后回看 process() 第 603 行的 `file_id=file_id` 调用，理解"编排层生成、切分层继承"的完整链路。

### Pending Questions（T0308 新增，学习中发现，未修复，仅记录）

23. **模块 docstring 两处 "(a later task)" 已过期**：[ingest.py:38](../../backend/app/services/ingest.py#L38)（"rejected by the ingest pipeline (a later task)"）和 [ingest.py:62-64](../../backend/app/services/ingest.py#L62-L64)（"Extension-based dispatch ... owned by the ingest pipeline (a later task)"）——T0308 已落地，"a later task" 指向的就是现在的 IngestService。学习时发现，不修实现（注释滞后是文档债，不是行为 bug）。
24. **`_fail` 标了 `@classmethod` 却不用 `cls`**：[ingest.py:658-659](../../backend/app/services/ingest.py#L658-L659)。功能上 `@staticmethod` 完全等价——实现选择对称性（与 process 同款装饰器）。同理 `ChromaVectorStore` 在模块里被 import 两次（[ingest.py:588](../../backend/app/services/ingest.py#L588) 和 [ingest.py:673](../../backend/app/services/ingest.py#L673)）——sys.modules 缓存让成本近零，但重复 import 是风格瑕疵。
25. **source_file 现在收到真实 file_name 但依然无行为**：process() 第 603 行传了 `file_name`——Pending #20 的"装饰品参数"第一次收到真值，行为依然为零。若未来 Step 1 变回"仅 .md"，参数已经就位（好消息）；SPEC 仍未澄清 v1 该参数的角色（老问题）。
26. **FAILED → HTTP 422 的映射不在本类**：SPEC F002 错误表说 FAILED 由 API 层映射为 422 FILE_PARSE_ERROR——TASKS T0502 的职责（"FAILED → 422"）。本类只返回 dict，映射是上传层的事——**三态与 HTTP 语义的边界在 Task 之间**，T0502 落地前无法端到端验证。
27. **AppError 路径无 rollback（SPEC 空白）**：损坏文件 → FILE_PARSE_ERROR raise → raw 文件留在 uploads/。SPEC F002 的原子性表只覆盖三态（SUCCESS/SUCCESS_WITH_WARNINGS/FAILED），**未定义异常路径的清理责任**——上传层（T0502）若不清理，坏文件会积压在 uploads/。这是本学习 Pass 发现的**最实质的 SPEC 缺口**，标记给 T0502 集成时对照（不修 SPEC、不修实现，仅记录）。

### T0308 快速复习卡

```text
T0308 — Ingest Service（IngestService，第 534–683 行，150 行）
一句话：把 Phase 1/2/3 的七个零件按 F002 顺序接成流水线，产出三态结果

管道：_parse（扩展名分发）→ clean → [闸门①] → chunk（file_id 继承）→ [闸门②] → warnings → status
      → metadata 九字段 → embed → store → 五键 dict
三态：SUCCESS（无 warnings）/ SUCCESS_WITH_WARNINGS（warnings 非空）/ FAILED（0 chunks → 回滚）
身份：file_id 在 process() 顶部生成（身份先于管道）→ chunk_text 继承；upload_time 取一次全文件共享
回滚：unlink(missing_ok=True) + delete_by_file——幂等"清空式"补偿（闸门先于写入，正常路径空操作）
错误边界：6 个 AppError 原样传播（docstring Raises 契约）；FAILED 是返回值不是异常
第一次们：模块第一个 class / 第一个 400 目录码 / 第一个 f-string 和 set / 第一次改既有函数
```

---

> **T0308 部分完 —— Phase 3 全 Task 完成（T0301–T0308）**。八站齐了：解析五格式（T0301–T0305）、清洗（T0306）、切分（T0307）、编排（T0308）。一根管道从"磁盘上的字节"走到"ChromaDB 里的向量块"，途中诞生了三态模型、身份体系、责任链和回滚——**而这条管道的入口（上传 API）和出口的响应组装还在 Phase 5 等着**：本类只是个"纯管道"，要等 T0502 把它嵌进 F002 的十步流程，Phase 3 的零件才算真正通电。下一站：Phase 4 Knowledge Base Management API（T0401–T0404，尚未开始）——建议等其实现后再做 Learning Pass。

---

## 42. Phase 3 总复习卡（全 Phase）（Learning Review 新增）

**一句话**：686 行 = 一根八站管道——磁盘上的字节 → 五个 parser（Path 进、str 出）→ 清洗（纯函数，报告不裁决）→ 切分（两段式 + 身份）→ 编码（Phase 2 的机器）→ 写入（Phase 1 的搬运工）→ 编排（三态 + 幂等回滚），错误分三条通道（fatal / warnings / FAILED 返回值）泾渭分明。

**8 个关键词（一站一个）**：编码级联（T0301）、结构战（T0302）、单元格值战（T0303）、页级容错（T0304/T0305）、报告不裁决（T0306）、位置即声明（T0307）、身份先于管道（T0308）、幂等回滚（T0308）。

**2 张图**：第 0 节全景速览的八站管道图 + 第 37 节的 F002 十步流程定位（本模块只占第 8 步）。

**5 个最易混（Phase 3 版）**：

1. `read_bytes` vs `read_text`——要"自己猜编码"就必须从原始字节开始；`read_text` 按 UTF-8 读，猜错了没机会补救（第 3 节）；
2. **Path 支持没有统一答案**——python-docx 要桥 `str()`、openpyxl 不要、fitz 又要（手册 20.6 三幕故事）——看库文档的参数标注，不确定就 `str()` 一下；
3. **FAILED 是返回值不是异常**——"空"是数据问题（可判、可回滚），"错"是执行问题（传播、让上层翻译）——两条通道泾渭分明（第 40 节④）；
4. **warnings 走旁路不返回值**——五个 parser 外形必须一致（都是 `Path → str`），警告走模块级旁路，主数据流保持纯净（第 25 节⑥）；
5. **位置决定共享**——`file_id` 在循环外（T0308 起在管道入口）、`chunk_id` 在循环内；没有"共享声明"，位置就是声明（第 35 节②）。

**收官状态**：T0301–T0308 全 DONE（TASKS.md），ingest.py 686 行（103 → 151 → 354 → 517 → 686 成长史见第 12 节）。`IngestService.process` 无调用方（正常——F002 十步流程的其余步骤在 T0501/T0502 上传层，Phase 5 才出现）。越界检查：5 个新依赖（python-docx / openpyxl / PyMuPDF / dashscope / langchain_text_splitters）均 SPEC 明示或任务必需；CSV/JSON 结构化解析、流式输出等 SPEC Out of Scope 均未触碰。

### 42A. Phase 3 只需要真正掌握的 12 件事

1. 编码级联三件套：UTF-8 strict → UTF-16 strict → GBK ignore；任何一级成功就提前 return；三次全败 → FILE_PARSE_ERROR + `details.encoding_attempts`。（第 3/4 节）
2. `read_bytes()` 不是 `read_text()`：`errors` 参数（strict / ignore）是"猜错时的行为开关"。（第 3 节）
3. python-docx 双提取：段落 `doc.paragraphs` + 表格 `doc.tables`，SPEC 固定"段落在前、表格在后"；`Document(str(file_path))` 的 Path 桥接。（第 14 节）
4. openpyxl 三层过滤：`data_only=True` 读缓存值（公式格无缓存 → None）、行内 None 过滤、全空 sheet 跳过。（第 19 节）
5. PDF 三种结局：`needs_pass` → ENCRYPTED_PDF；`text.strip()` 非空 → 原生文本；空 → ocr_page 回调；`finally: doc.close()` 保证句柄必释放。（第 24 节）
6. OCR 重试状态机：初始请求 + 最多 2 次重试（SPEC 9.3）+ 指数退避；页级失败走 warnings 旁路，不终止整个文件。（第 24/25 节）
7. clean_text 五步纯函数 + "做 5 步、不做 5 件事"；只报告空文本，不裁决——拒绝权归 T0308。（第 29/30 节）
8. 两段式切分：MarkdownHeaderTextSplitter 按标题保语义边界，RecursiveCharacterTextSplitter 当"尺寸警察"收拾超长漏网之鱼；重叠是"约数"。（第 34 节）
9. 身份体系三分工：file_id 每文件一个（管道入口生成）、chunk_id 每块一个（循环内生成）、chunk_index 仅排序——SPEC 7.1 落地。（第 34/35 节）
10. 导入与资源纪律：惰性导入 7 组（重依赖一律函数内）；资源释放两级水准（openpyxl 靠 GC vs fitz 用 finally）——新代码按更高标准写，不回头改旧的。（第 40 节）
11. IngestService 三件套：双闸门（cleaned 空 / chunks 空 → FAILED）、三态判定（warnings 非空 → SUCCESS_WITH_WARNINGS）、幂等回滚（`unlink(missing_ok=True)` + `delete_by_file`）。（第 39 节）
12. 错误哲学三层：文件级 fatal（AppError 目录码）→ 页级容错（warnings）→ 状态机（FAILED 返回值）——"用户的错"、"系统的错"、"数据的问题"三条通道。（第 40/41 节）

### 42B. 现在可以暂时不懂的内容（Phase 3 级汇总）

| 内容                               | 为什么可以暂时不懂                         | 什么时候需要              |
| -------------------------------- | --------------------------------- | ------------------- |
| LangChain splitters 内部实现         | 只需知道"两段式 + 调用式 + 重叠是约数"           | 自定义切分策略时            |
| PyMuPDF 渲染细节                     | `get_text` / `get_pixmap` 调用式照抄即可 | 做 PDF 增强功能时         |
| Qwen-VL 多模态 API 全部参数             | 项目只用 model + messages + 重试策略      | 调优 OCR 质量时          |
| openpyxl 样式 / 公式引擎               | v1 只要 `values_only` 的缓存值          | 做 Excel 导出功能时       |
| 编码检测算法（chardet 原理）               | SPEC 定死顺序尝试，不引入检测库                | 用户反馈乱码时（Pending #1） |
| sentence-transformers / torch 内部 | Phase 2 已声明（其 17B 节）              | 换模型 / 调优时           |

### 42C. 完整代码阅读路线（一次读完 686 行）

打开 [ingest.py](../../backend/app/services/ingest.py)（686 行），按九站顺序读：

1. [第 1–65 行](../../backend/app/services/ingest.py#L1-L65) 文件 docstring —— 八段契约（五种 parser + 清洗 + 切分 + 编排）。读完能背出"Path 进、str 出、FILE_PARSE_ERROR"就算过。
2. [第 78–108 行](../../backend/app/services/ingest.py#L78-L108) parse_text_file —— 编码战。
3. [第 111–147 行](../../backend/app/services/ingest.py#L111-L147) parse_docx_file —— 结构战。
4. [第 150–191 行](../../backend/app/services/ingest.py#L150-L191) parse_excel_file —— 单元格值战。
5. [第 194–251 行](../../backend/app/services/ingest.py#L194-L251) parse_pdf_file —— 原生 vs 图片页。
6. [第 253–378 行](../../backend/app/services/ingest.py#L253-L378) OCR 基础设施 + ocr_page —— 外部世界战。
7. [第 381–413 行](../../backend/app/services/ingest.py#L381-L413) clean_text —— 纯函数。
8. [第 416–531 行](../../backend/app/services/ingest.py#L416-L531) chunk_text —— 两段式 + 身份。
9. [第 534–683 行](../../backend/app/services/ingest.py#L534-L683) IngestService —— 编排 + 三态 + 回滚。

读完能回答 4 个问题：① 全文 7 个函数 + 1 个类的输入输出契约各是什么？② 全文有几个 `raise`？（8 个——L108 / L139 / L178 / L234 / L238 / L364 / L375 / L656）③ 两个"闸门"在哪几行？（L600 / L604）④ 惰性导入出现在哪 7 组？（parse_docx_file L136 / parse_excel_file L175 / parse_pdf_file L230 / ocr_page L321–323 / chunk_text L482–485 / process L588–589 / _fail L673——计数口径见第 44 节）

---

## 43. 跨 Task 整合自测（Learning Review 新增；不给答案）

> 答不出的回对应章节找。这些题刻意跨 Task 出——单看某一节都能答对不等于理解管道。

1. 一句话讲完 686 行——要求同时覆盖 8 站顺序、三种错误通道、三态结果。
2. 五种文件（txt / docx / xlsx / 原生 PDF / 扫描 PDF）各走哪条路径？哪两种会进 warnings 通道？哪几种可能触发 FAILED？
3. 一个"损坏的扫描 PDF"（渲染失败 + 重试耗尽 + 最后清洗出空文本）从上传到响应的完整旅程——三态、warnings、回滚各发生在哪一步？
4. 为什么"FAILED 是返回值而 FILE_PARSE_ERROR 是异常"？这两种结局对调用方（T0502 上传层）的要求有什么不同？
5. file_id 的生成权为什么从 chunk_text 上移到 process()？如果没上移，F002 的 FAILED 回滚会缺什么？
6. 惰性导入 7 组分别在哪些函数？哪两行 import 的是同一个类？为什么重复 import 不亏？
7. 从 clean_text 的"报告不裁决"到 process 的"双闸门"，"空文本"的裁决权经历了哪几步交接？每步的依据是什么？
8. 如果让你加第 9 种格式（.ppt），按项目惯例要动哪些行？（提示：集合 or 单独 if、解析函数外形、错误码、docstring 契约）
9. 为什么 rollback 的两个动作必须幂等？闸门开在"写向量库之前"和幂等之间有什么关系？
10. 第 11 节的 Pending #1（GBK 误判窗口）与第 41 节的 Pending #27（AppError 无 rollback）哪个是"SPEC 权衡"、哪个是"SPEC 缺口"？为什么后者是 T0502 集成时必须面对的坑？

---

## 44. Pending Questions 汇总与收官（Learning Review 新增）

### Pending #1–27 汇总

> 八站学习过程中发现的待确认点（只记录，不修复）。分散在各节的 Pending 列表里，这里合并成一张总表。状态列是 Learning Review 时点的判断。

| #    | 来源       | 一句话                                      | 状态                                 |
| ---- | -------- | ---------------------------------------- | ---------------------------------- |
| 1    | T0301    | GBK 文件恰好合法 UTF-8 的误判窗口                   | SPEC 固有权衡（v1 不引入 chardet）          |
| 2    | T0301    | 无自动化测试（延续 Phase 1/2）                     | 全项目已知事实                            |
| 3    | T0301    | UTF-16 无 BOM 文件未覆盖                       | v1 未覆盖（SPEC 未要求）                   |
| 4    | T0301    | `errors="ignore"` 丢字节无警告                 | SPEC 权衡（静默性）                       |
| 5    | T0303    | 文件头 docstring 标题漏了 Excel                 | 文档债（持续存在）                          |
| 6    | T0303    | 公式格（无缓存）静默消失                             | data_only 语义的固有代价                  |
| 7    | T0303    | 隐藏 sheet 也被解析                            | 实现符合 SPEC，观察                       |
| 8    | T0303    | workbook 未显式关闭                           | 旧代码观察；T0304 起新代码用 finally 示范（部分演进） |
| 9    | T0303    | 合并单元格只取左上角                               | 观察（内容不丢、关系丢）                       |
| 10   | T0304/05 | 200 但响应结构不符 → 异常穿透                       | 边界情况（SPEC 未定义）                     |
| 11   | T0304/05 | 200 但内容为空 → 静默空页无 warning                | 边界情况（警告覆盖范围有限）                     |
| 12   | T0304/05 | ocr_page 每页重开 PDF（O(n)）                  | 性能观察（无真实扫描 PDF 未实测）                |
| 13   | T0304/05 | 无回调时空页静默产 `""`                           | ✅ T0308 落地验证未触发（process 确实传了回调）    |
| 14   | T0304/05 | `dashscope.api_key` 模块级全局赋值              | 单进程单 key 假设                        |
| 15   | T0304/05 | get_pixmap 未指定渲染分辨率                      | SPEC 未定义，v1 接受默认                   |
| 16   | T0306    | Define"合并空行" vs Detail"去除空行"             | SPEC 内部措辞不一致                       |
| 17   | T0306    | strip() 范围比 SPEC 字面更激进                   | 实现善意超范围，SPEC 澄清需求                  |
| 18   | T0306    | 页间 `"\n\n"` 被清洗折叠                        | 未来需求风险（按页切块/引注页码）                  |
| 19   | T0307    | F006 Define 输出类型与 Detail/7.4 不一致         | SPEC 定义表应更新                        |
| 20   | T0307    | `source_file` 参数无行为（T0308 起收到真值仍无行为）     | SPEC 澄清需求（老问题延续）                   |
| 21   | T0307    | 重叠"约 120"不精确                             | 实现合规（SPEC 用"约"字）                   |
| 22   | T0307    | 首个标题前的内容无路径前缀                            | SPEC 未定义场景                         |
| 23   | T0308    | docstring 两处 "(a later task)" 已过期        | 文档债                                |
| 24   | T0308    | `_fail` 的 `@classmethod` 不用 `cls` + ChromaVectorStore 双 import | 风格瑕疵（对称性选择）                        |
| 25   | T0308    | source_file 收到真值仍无行为（#20 延伸）             | 同 #20                              |
| 26   | T0308    | FAILED → 422 映射不在本类                      | 待 T0502（三态与 HTTP 语义的边界在 Task 之间）   |
| 27   | T0308    | **AppError 路径无 rollback（SPEC 空白）**       | ⚠️ **最实质 SPEC 缺口**——T0502 集成时对照    |

### 计数口径说明（惰性导入"第 N 次"的漂移）

T0301–T0305 时代的教学把 Phase 2 embedding.py 的 sentence_transformers 算作第 1 次，按 Task 分组数到 ocr_page 的"第五次"（第 21/24 节）；T0306 起的教学改用"ingest.py 内重型第三方库"口径——docx(1)、openpyxl(2)、fitz(3)、langchain(4)、ChromaVectorStore(5)、encode_chunks(6)、_fail 里的 ChromaVectorStore(7)，dashscope 作为轻量 SDK 不计、ocr_page 里的 fitz 是同库复用不重复计。**Learning Review 确认的最终口径：惯例在 ingest.py 连续出现 7 组**（两种计数只是"是否把 embedding 的 import 和 dashscope 算进来"的口径差异，各时代内部自洽）。

### Gate Review 说明

仓库中未找到 Phase 3 Gate Review 的书面结论或 Findings（TASKS.md 中唯一的 Gate Review 记录属于 Phase 0）。本文档"Phase 3 完成"的依据 = TASKS.md T0301–T0308 的 DONE 状态 + 真实代码 + SPEC 对照。若 Gate Review 有正式结论，应回填本节。

### Phase 4/5 将建立在什么基础上（只做高层连接，不提前教授实现）

- **Phase 4（T0401–T0404）KB 管理 API**：消费 Phase 1 的 ChromaVectorStore CRUD——与 Phase 3 的连接点只有一个参数：`collection_name`（ingest 写入、检索命中的容器由 Phase 4 管理）。
- **Phase 5（T0501–T0503）上传 API**：`IngestService.process` 的第一个调用方。F002 十步流程的 1–7 步（保存 / 校验 / 防路径穿越）与 9–10 步（keyword index 失效、响应组装）在那里落位；Pending #26（FAILED → 422）、#27（异常路径清理）、F004 检查③④（keyword index 干净、重传不 409）都在 T0502 验收——**Phase 3 的零件在那里才真正通电**。
- **Phase 6–8 检索链**：消费 chunk 四键字典（chunk_id 去重合并）与 metadata 九字段（relevance / citation）。
- **Phase 9（T0901 文件列表）**：消费 metadata 聚合（file_size / upload_time / chunk_count）。
- 以上连接点全部通过已写死的接口发生，**Phase 3 的代码无需任何改动**。

---

> **Phase 3 收官 —— Learning Review 完成**：T0301–T0308 全部完成（ingest.py 共 686 行，八站齐备，越界干净，错误通道三层分明）。五个 parser（编码战 / 结构战 / 单元格值战 / 原生 vs 图片页 / 外部世界战）、一道纯函数闸门、一座形状转换站、一层三态编排——一根管道从"磁盘上的字节"走到"ChromaDB 里的向量块"，身份体系（SPEC 7.1）与 metadata 九字段（F008）在途中落地。`IngestService.process` 尚无调用方——Phase 5（T0501–T0503）的上传 API 将是第一个消费者：届时 F002 的十步流程闭合，Pending #26/#27 与 F004 检查③④ 在那里得到最终答案。本文档已按 Phase 3 Learning Review 整理：第 0 节全景速览 → 第 1–11 节 T0301 → 第 12–16 节 T0302 → 第 17–21 节 T0303 → 第 22–26 节 T0304 + T0305 → 第 27–31 节 T0306 → 第 32–36 节 T0307 → 第 37–41 节 T0308 → 第 42–44 节收尾整合。下一步学习 Phase 4 Knowledge Base Management API（建议待实现后开展）。
