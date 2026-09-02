# Phase 6 — Keyword Retrieval 学习笔记

> **Phase 状态**: T0601–T0602 DONE；Phase Gate Review 于 2026-08-27 裁定 PHASE_6_PASS；Phase Learning Review 完成（2026-08-27）
> **本文档状态**: T0601 + T0602 Learning Pass + Phase Learning Review 完成（2026-08-27）
> **配套文档**: [工程评审](./engineering-review/phase-06-engineering-review.md) · [面试指南](./interview-notes/dx-rag-interview-guide.md)

---

## 0. 三层文档边界

| Layer | 本次放什么 | 本次不放什么 |
|------|------------|--------------|
| Technical Learning（本文） | tokenize() 与 KeywordRetriever 如何运行、为什么这样写、测试如何证明行为、Python/TS 学习桥梁 | 完整 ADR、容量规划、完整面试答案 |
| [Engineering Review](./engineering-review/phase-06-engineering-review.md) | 设计取舍、维护性、性能、Known Gaps、Future 演进 | 逐行语法教学 |
| [Interview Guide](./interview-notes/dx-rag-interview-guide.md) | Phase Learning Review 已 consolidation 的项目级话术 | 在 Technical Learning 复制完整答案 |

本文把仓库能直接证明的 T0601 tokenizer 与 T0602 KeywordRetriever 标为 [PROJECT FACT]。Phase 7 的 T0702 hybrid merge/fusion/filter 与 T0703 `retrieve()` wiring facade 已在后续 Task 中实现；Phase 8 QA API、持久化/增量 keyword index 等仍属于 [FUTURE]；SPEC 已经设计好，不等于代码已经实现。

---

## 1. Phase 学习：先建立正确的心智模型

### 1.1 一句话定位

Phase 6 建成了一条 lexical retrieval（词面检索）支路：把 query 与 document 切成同一种 token，再用倒排索引从 token 找回 chunk。T0601 完成 tokenizer，T0602 完成 index lifecycle 与 search：

~~~text
自然语言 text
  → tokenize()                     ✅ T0601
  → unique tokens
  → inverted index lookup          ✅ T0602
  → keyword_score
  → ranked chunks
~~~

### 1.2 为什么 RAG 还需要关键词检索

[SPEC F009](../SPEC.md#f009-keyword-retrieval) 的目标不是替代 vector retrieval，而是补它的盲区。向量检索擅长“意思接近”，关键词检索擅长“字面必须出现”，例如产品型号、错误码、类名和缩写。T0702 已在 Phase 7 把两路结果按 `chunk_id` 融合；T0601 先解决一个更基础的问题：什么叫“字面相同”？

### 1.3 本章核心学习点

- 🟢 **overlapping character bigram**：固定宽度 2、步长 1 的字符窗口。
- 🟢 **同一 tokenizer 契约**：query 与 chunk content 必须进入同一个 token space。
- 🟢 **unique token 语义**：去重不是输出美化，而是在为 T0602 的评分分母准备数据。
- 🟡 Python 的 re.compile / finditer / generator expression / slice / dict.fromkeys。
- 🟡 pure function 为什么是检索基础设施的好边界。
- 🟢 **inverted index**：token → Set[chunk_id]，把“扫全部文档”改成“按 token 直达候选”。
- 🟢 **lazy build + dirty flag**：修改操作只标脏，查询时才 full rebuild。
- 🟢 **normalized coverage score**：matched unique tokens / total unique tokens。
- 🟡 class-level cache、dependency injection、Mock(spec=...) 与测试隔离。
- 🔵 当前 CJK regex 和跨语言输出顺序的真实实现边界。

### 1.4 建议学习路径

1. 读 SPEC F009 Detail 的分词规则与三个例子。
2. 手算“机器学习算法”为什么是 5 个 bigram。
3. 对照 [qa.py:9-21](../../backend/app/services/qa.py#L9) 读两条扫描通道。
4. 对照 [test_qa.py:22-51](../../backend/tests/test_qa.py#L22) 判断每个 tokenizer test 保护哪条契约。
5. 对照 [qa.py:24-82](../../backend/app/services/qa.py#L24) 追踪 build → invalidate → rebuild → search。
6. 对照 [test_qa.py:54-138](../../backend/tests/test_qa.py#L54) 判断 7 个 retriever tests 各自保护什么。

### 1.5 Phase-level Mental Model：先统一坐标系，再维护一张可重建的查找表

完成 T0601 与 T0602 后，不要把它们记成“一个分词函数 + 一个搜索 class”两个孤立知识点。更有用的心智模型是：

~~~text
tokenize() = 共享坐标系
  document content ─┐
                    ├─→ 相同 token space
  query text ───────┘

inverted index = 这个坐标系上的可重建查找表
  token → chunk_ids → ChunkRecord → coverage score

dirty flag = “查找表已落后于真实 VectorStore”的状态声明
  mutation 只声明 stale
  next query 从 source of truth 全量重建
~~~

`VectorStore.list_chunks()` 才是真实数据源，内存索引只是 derived snapshot。tokenizer 决定“什么算同一个字面信号”，倒排索引决定“怎样快速找到带这些信号的 chunk”，score 决定“一个 chunk 覆盖了 query 的多少 unique signals”。三者分别回答 equality、lookup、ranking，合起来才是完整 lexical retrieval。

TypeScript 类比：可以把它想成一个由同一 `normalize()` 同时服务写入侧和读取侧的 derived store。mutation 不直接重算 selector cache，只把 cache 标成 stale；下一次读取再从 canonical store materialize 新 snapshot。类比只帮助理解 lifecycle——当前 Python 实现使用 class-level dict/set，并没有 Redux 的 immutable update 或并发原子发布保证。

---

## 2. Phase 目标与实现切片

### 2.1 完整 F009 与当前实现

SPEC F009 定义的是完整 keyword retrieval，而不是一个字符串工具函数。

| F009 能力 | 仓库证据 | 状态 |
|-----------|----------|------|
| 英文/数字连续 alphanumeric token + lowercase | [qa.py:9](../../backend/app/services/qa.py#L9)、[qa.py:15](../../backend/app/services/qa.py#L15) | [PROJECT FACT] T0601 |
| 连续中文段 overlapping bigram | [qa.py:10](../../backend/app/services/qa.py#L10)、[qa.py:17-19](../../backend/app/services/qa.py#L17) | [PROJECT FACT] T0601 |
| 最小长度 2 + query 内去重 | [qa.py:21](../../backend/app/services/qa.py#L21) | [PROJECT FACT] T0601 |
| 倒排索引、lazy build、dirty invalidation、全量 rebuild | [qa.py:27-51](../../backend/app/services/qa.py#L27) | [PROJECT FACT] T0602 |
| query 匹配、keyword_score、排序、top_k | [qa.py:53-82](../../backend/app/services/qa.py#L53) | [PROJECT FACT] T0602 |
| invalidation seam 接入 shared cache | [keyword_index.py:4-8](../../backend/app/services/keyword_index.py#L4) | [PROJECT FACT] T0602 |

### 2.2 明确不做

T0601 的 Out of Scope 来自 [TASKS:1590](../TASKS.md#L1590)，并与 [SPEC F009](../SPEC.md#f009-keyword-retrieval) 一致：

- 不引入 jieba 或其他中文 NLP dependency。
- 不实现 BM25 / TF-IDF weighting。
- 不做 stop-word removal。
- 不做 position-aware matching。

[ENGINEERING KNOWLEDGE] “不做”同样是契约。若擅自加停用词，query token 分母会改变；若提前加 jieba，SPEC 示例的 exact output 也可能改变。

---

## 3. 项目位置：查询链最前面的 normalization boundary

- **所属层**: Service Layer；实现位于 [backend/app/services/qa.py](../../backend/app/services/qa.py)。
- **直接依赖**: T0601 tokenize() + T0108 VectorStore.list_chunks() public interface。
- **输入/输出契约**: keyword_search(collection, query, top_k) → List[Dict[str, object]]，字段为 chunk_id/file_id/file_name/content/keyword_score。
- **下游消费者**: Phase 7 T0702 `HybridRetriever` 消费 keyword results；T0703 `retrieve()` facade 负责组装统一检索入口；QA endpoint 仍为 [FUTURE]。
- **边界**: qa.py 已有 tokenizer、KeywordRetriever、HybridRetriever 与 T0703 `retrieve()` facade，但没有 LLM QA service 或 HTTP query endpoint。

TypeScript 类比：tokenize() 像无副作用的 tokenize.ts utility；KeywordRetriever 像注入 VectorStore port 的 in-memory search service，而不是 route handler。

---

## 4. Task 学习

### T0601 — Query Tokenizer

#### A. Code Understanding

tokenize() 不是“按空格 split”：

1. 用 alphanumeric regex 扫描全部英文/数字 run 并 lowercase。
2. 用 CJK regex 找到每个连续中文 segment。
3. 在每个 segment 内用宽度 2、步长 1 的 slice 生成 bigram。
4. 丢弃长度小于 2 的 token。
5. 保留每个 token 的首次出现，返回 deterministic list。

#### B. Project Understanding

倒排索引要求 query 与 document 使用相同的 key。若 chunk 建索引时得到“机器 / 器学 / 学习”，query 却得到“机器学习”一个 token，两边永远无法相交。T0601 冻结的是 Phase 6 的 shared normalization contract。

去重也与未来评分直接相关。[SPEC:1097](../SPEC.md#L1097) 定义：

~~~text
keyword_score = matched_unique_query_tokens / total_unique_query_tokens
~~~

因此 tokenizer 返回 unique tokens，可以防止 query 中重复词无意放大分母。在 T0601 checkpoint，评分尚未实现；T0602 已按这条输入契约完成 matched_count / len(query_tokens)。

#### C. Learning Understanding

- Python regex Match 是对象，group() 才取出字符串。
- slice 的右边界 exclusive，与 JS String.slice 一致。
- generator expression 是 lazy iterable，可直接喂给 list.extend。
- dict 的 key 唯一性 + insertion order 可以组成 stable dedup。
- pure function 的价值不是“代码短”，而是相同输入必得相同输出、无环境依赖、测试成本低。

#### 验证边界

T0601 checkpoint（尚未加入 T0602 tests）在 2026-08-27 实际执行：

~~~text
python -m unittest tests.test_qa -v
Ran 6 test methods
OK
~~~

同一命令在 T0602 完成后的当前 suite 会运行 13 个 test methods；完整结果见下方 T0602 验证。

| 验收项 | 结果 | 证据 |
|--------|------|------|
| SPEC 三个 query 示例 | PASS | [test_qa.py:23](../../backend/tests/test_qa.py#L23) |
| 英文/数字 lowercase | PASS | [test_qa.py:41](../../backend/tests/test_qa.py#L41) |
| 单字符丢弃 | PASS | [test_qa.py:44](../../backend/tests/test_qa.py#L44) |
| 中文不跨标点 segment 组 bigram | PASS（额外边界测试） | [test_qa.py:47](../../backend/tests/test_qa.py#L47) |
| stable dedup | PASS（额外边界测试） | [test_qa.py:50](../../backend/tests/test_qa.py#L50) |
| AC-F009-01 完整检索与 1.0 score | T0601 时 DEFERRED；T0602 后 PASS | [test_qa.py:62](../../backend/tests/test_qa.py#L62) |
| AC-F009-04 完整检索与 1.0 score | T0601 时 DEFERRED；T0602 后 PASS | [test_qa.py:98](../../backend/tests/test_qa.py#L98) |
| AC-F009-02/03 | T0601 时 DEFERRED；T0602 后 PASS | [test_qa.py:82](../../backend/tests/test_qa.py#L82) |

#### T0601 Interview Candidates

> Candidate source — Phase Learning Review 已筛选并晋升“shared tokenizer contract / stable dedup / bigram 取舍”到累计 Interview Guide 的 Phase 6 深度章；这里保留最初候选作为学习来源，不复制完整回答。

- **Technical Point**: 零依赖 mixed-language tokenizer：英文/数字 run + 中文 overlapping bigram。
- **Engineering Question**: 为什么 query 与 document 必须复用同一 tokenizer？
- **Candidate Question**: dict.fromkeys 与 set 都能去重，为什么这里选择前者？
- **STAR Candidate**: 无；本 Task 没有形成重大闭环工程事件。

### T0602 — Inverted Index & Keyword Search

#### A. Code Understanding

[KeywordRetriever](../../backend/app/services/qa.py#L24) 把每个 collection 的状态拆成三张 class-level 表：

~~~text
_indexes[collection][token]  → Set[chunk_id]
_chunks[collection][chunk_id] → ChunkRecord
_dirty_collections            → Set[collection]
~~~

- _indexes 负责“token 命中了谁”。
- _chunks 负责“chunk_id 对应什么返回数据”。
- _dirty_collections 只表达“缓存已过期”，不在写操作当场重建。

keyword_search() 首先确保 index 存在且不脏，再 tokenize query；随后对每个 unique query token 查 posting set，按 chunk_id 累计命中数，除以 query token 总数得到 keyword_score，最后降序排序并切 top_k。

#### B. Project Understanding

T0602 第一次兑现了 Phase 1 的 VectorStore.list_chunks() 只读契约：[qa.py:44](../../backend/app/services/qa.py#L44) 没有访问 _collection 或任何 Chroma private API。它也填上了 Phase 4/5 预留的 invalidation seam：[keyword_index.py:4-8](../../backend/app/services/keyword_index.py#L4) 将 upload / rename / delete 的失效通知转交给 KeywordRetriever.invalidate()。

#### C. Learning Understanding

- Dict[str, Set[str]] 是 inverted index 的直接 Python 表达；TS 常见写法是 Map<string, Set<string>>。
- setdefault(token, set()) 将“若无则创建 posting set”和“取出现有 set”合成一步。
- classmethod 让 invalidation 不需要持有某个 retriever instance。
- constructor injection 让 KeywordRetriever 只依赖 VectorStore interface；测试可以传 Mock(spec=VectorStore)。
- dirty flag 是 deferred work：写路径 O(1) 标记，读路径在真正需要数据时 full rebuild。

#### T0602 验证

2026-08-27 Phase Learning Review 重新执行 test_qa.py 全文件：13 test methods PASS，其中 7 个属于 KeywordRetrieverTests。

| 行为 | 结果 | 单测证据 |
|------|------|----------|
| 首次 search 才调用 list_chunks | PASS | [test_qa.py:62](../../backend/tests/test_qa.py#L62) |
| AC-F009-01 中文全命中 = 1.0 | PASS | [test_qa.py:62](../../backend/tests/test_qa.py#L62) |
| AC-F009-02 无命中 = [] | PASS | [test_qa.py:82](../../backend/tests/test_qa.py#L82) |
| AC-F009-03 部分命中 = 0.6 | PASS | [test_qa.py:89](../../backend/tests/test_qa.py#L89) |
| AC-F009-04 mixed-language 全命中 = 1.0 | PASS | [test_qa.py:98](../../backend/tests/test_qa.py#L98) |
| score DESC + top_k | PASS | [test_qa.py:109](../../backend/tests/test_qa.py#L109) |
| invalidation 后 next search full rebuild | PASS | [test_qa.py:121](../../backend/tests/test_qa.py#L121) |
| absent index invalidation = no-op | PASS | [test_qa.py:135](../../backend/tests/test_qa.py#L135) |

**AC-F009-05 的诚实边界**：单测以 Mock 更新 list_chunks 返回值并直接调用 invalidate_keyword_index()，已证明 seam → dirty → next search rebuild → 新 chunk searchable 的核心生命周期；它没有发起真实 upload HTTP request。upload-to-search 的端到端链路仍待 Phase 12 integration acceptance。

#### T0602 Interview Candidates

> Candidate source — Phase Learning Review 已筛选并晋升“inverted index / lazy-dirty lifecycle / 双表 snapshot / shared cache 边界”到累计 Interview Guide 的 Phase 6 深度章；这里保留最初候选作为学习来源，不复制完整回答。

- **Technical Point**: per-collection in-memory inverted index + lazy full rebuild。
- **Engineering Question**: 为什么 invalidation 只标 dirty，不立即重建？
- **Candidate Question**: 为什么同时缓存 _indexes 和 _chunks？
- **Candidate Question**: class-level cache 给 seam 带来什么便利，又引入什么隔离风险？
- **STAR Candidate**: 无；本 Task 没有重大 incident / conflict 闭环。

---

## 5. 代码理解：逐行精读

Phase 6 主实现位于 [qa.py:1-82](../../backend/app/services/qa.py#L1)：T0601 是 13-21 行的 pure tokenizer，T0602 是 24-82 行的 stateful retriever。

### 5.1 模块职责与 imports（qa.py:1-6）

~~~python
"""Query tokenization for keyword retrieval."""

import re
from typing import Dict, List, Set

from app.core.vector_store import ChunkRecord, VectorStore
~~~

- [PROJECT FACT] module docstring 仍只写 Query tokenization，但文件已经包含 KeywordRetriever；这是随 T0602 出现的维护债，不代表 search 未实现。
- re 是标准库，符合“不引入 jieba”的范围纪律。
- Dict/List/Set 描述 tokenizer、posting sets、cache 与动态结果容器；Python runtime 不会自动校验 annotation。
- ChunkRecord 是 build snapshot 的数据模型，VectorStore 是 injected public interface。

TypeScript 对照：

~~~ts
export function tokenize(text: string): string[] { /* ... */ }
~~~

Python annotation 与 TS type 都表达契约；差异是 TS 会在 compile time 检查，而普通 Python runtime 不会因为返回了错误类型自动报错。

### 5.2 模块级预编译两条 pattern（qa.py:9-10）

~~~python
_ALPHANUMERIC_PATTERN = re.compile(r"[a-zA-Z0-9]+")
_CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")
~~~

第一条 pattern：方括号表示 character class；加号表示连续出现一次或更多次，所以 Python3 是一个 token。lowercase 不写进 regex，而在匹配后调用 lower()。

第二条 pattern：Unicode range U+4E00–U+9FFF 是基本 CJK Unified Ideographs 区；加号先找连续中文 segment，bigram 再在 segment 内生成。标点、空格、ASCII 会切断 segment，因此“机器，学习”不会产生跨逗号的“器学”。

[PROJECT FACT] 当前实现只覆盖这个基本区间；没有证据表明它覆盖全部汉字扩展区。这是已知边界，不应扩写成“支持所有中文 Unicode”。

模块级常量的前导下划线表示 module-private convention，类似 TS 文件中不 export 的 const；它不是安全边界，外部仍可访问。

### 5.3 英文/数字通道（qa.py:13-15）

~~~python
def tokenize(text: str) -> List[str]:
    """Tokenize text into unique alphanumeric tokens and Chinese bigrams."""
    tokens = [match.group().lower() for match in _ALPHANUMERIC_PATTERN.finditer(text)]
~~~

数据变化：

~~~text
text: str → finditer: Iterator[Match] → group/lower: str → List[str]
~~~

为什么用 finditer 而不是 split？split 需要先枚举所有分隔符；regex 反过来声明“我要什么”，所有非 alphanumeric 字符自然成为边界。

TypeScript 类比：

~~~ts
const tokens = [...text.matchAll(/[a-zA-Z0-9]+/g)]
  .map(match => match[0].toLowerCase());
~~~

### 5.4 中文 segment 与 sliding window（qa.py:17-19）

~~~python
for match in _CHINESE_PATTERN.finditer(text):
    segment = match.group()
    tokens.extend(segment[index : index + 2] for index in range(len(segment) - 1))
~~~

以“机器学习”为例：

| index | slice | token |
|------:|-------|-------|
| 0 | segment[0:2] | 机器 |
| 1 | segment[1:3] | 器学 |
| 2 | segment[2:4] | 学习 |

长度 n 的 segment 有 n - 1 个合法起点。长度 1 时 range(0) 为空，因此不会产生单汉字 token；无需单独 if。

extend 接收的是 generator expression。它按需产生 token 并逐个追加；如果写 append(generator)，列表里会装进 generator 对象本身，语义完全不同。

TypeScript 直译：

~~~ts
for (const segment of chineseSegments) {
  for (let index = 0; index < segment.length - 1; index++) {
    tokens.push(segment.slice(index, index + 2));
  }
}
~~~

### 5.5 过滤与 stable dedup（qa.py:21）

~~~python
return list(dict.fromkeys(token for token in tokens if len(token) >= 2))
~~~

从内到外读：

1. generator 过滤 len(token) < 2。
2. dict.fromkeys(...) 把 token 变成唯一 key。
3. dict 保留首次插入顺序。
4. list(...) 只取 keys，恢复公开返回类型 List[str]。

TypeScript 类比：

~~~ts
return [...new Set(tokens.filter(token => token.length >= 2))];
~~~

为什么不直接 return list(set(tokens))？set 可以去重，但稳定输出不是它的公开契约；dict.fromkeys 让 SPEC exact examples、单测失败信息和调试输出都可预测。

### 5.6 一次完整 trace

输入“Python PYTHON 机器机器”：

1. alphanumeric 通道 → python, python。
2. 中文 segment → 机器, 器机, 机器。
3. 长度过滤 → 全部保留。
4. stable dedup → python, 机器, 器机。

这正是 [test_qa.py:50-51](../../backend/tests/test_qa.py#L50) 的断言。它同时证明 lowercase 后的英文会去重，以及重复中文 bigram 会去重。

### 5.7 一个容易忽略的输出顺序

[PROJECT FACT] 实现先扫描全文的英文/数字，再扫描全文中文。因此对于“机器Python学习”，返回顺序会是 python, 机器, 学习，而不是严格按原文交错顺序。

当前 SPEC 把 query tokens 用作 unique set 参与匹配与评分，没有定义跨语言 source order；T0602 的 matched-token counter 也只看 token presence，不把 list 位置当作权重。

### 5.8 三份 class-level 状态（qa.py:24-32）

~~~python
class KeywordRetriever:
    _indexes: Dict[str, Dict[str, Set[str]]] = {}
    _chunks: Dict[str, Dict[str, ChunkRecord]] = {}
    _dirty_collections: Set[str] = set()

    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store
~~~

这三份容器定义在 class body，不是 __init__ 内，所以所有 KeywordRetriever instances 共享。实际探针确认 a._indexes is b._indexes 为 True。

为什么仍把 vector_store 放在 instance 上？build 时需要调用具体 storage adapter；测试传 Mock，未来运行时传真实 ChromaVectorStore。TypeScript 类比：

~~~ts
class KeywordRetriever {
  static indexes = new Map<string, Map<string, Set<string>>>();
  constructor(private readonly vectorStore: VectorStore) {}
}
~~~

[ENGINEERING KNOWLEDGE] static/shared cache 让独立 invalidation seam 无需找到某个 instance；代价是 cache key 必须足以区分所有数据源。当前 key 只有 collection name，多 VectorStore/backend namespace 下的同名 collection 可能碰撞，详见 Engineering Review。

### 5.9 invalidate()：只给已有 index 标脏（qa.py:34-38）

~~~python
@classmethod
def invalidate(cls, collection: str) -> None:
    if collection in cls._indexes:
        cls._dirty_collections.add(collection)
~~~

- classmethod 的 cls 指向 KeywordRetriever class，因此能修改 shared state。
- 只有 index 已存在才加入 dirty set；不存在时 no-op，因为首次 search 本来就会 build。
- 重复 add 同一 collection 仍只有一个 set member，所以 invalidation 天然 idempotent。
- invalidate 不删除旧 index。旧数据暂时仍在内存，但 keyword_search 在 dirty 状态下不会使用它，而是先 rebuild。

[keyword_index.py:4-8](../../backend/app/services/keyword_index.py#L4) 用函数内 import 获取 KeywordRetriever，再调用此 classmethod。函数内 import 的可观察效果是调用时才解析依赖；不要把它误读为一个独立 cache。

### 5.10 _build_index()：一次 full snapshot（qa.py:40-51）

~~~python
def _build_index(self, collection: str) -> None:
    inverted_index: Dict[str, Set[str]] = {}
    chunks: Dict[str, ChunkRecord] = {}

    for chunk in self.vector_store.list_chunks(collection):
        chunks[chunk.chunk_id] = chunk
        for token in tokenize(chunk.content):
            inverted_index.setdefault(token, set()).add(chunk.chunk_id)

    self._indexes[collection] = inverted_index
    self._chunks[collection] = chunks
    self._dirty_collections.discard(collection)
~~~

关键顺序：

1. 先在 local dict 构建完整 snapshot。
2. 每个 chunk 进入 _chunks lookup。
3. 同一 tokenize() 处理 document content，避免 query/index normalization drift。
4. setdefault 建 posting set，Set 保证同一 chunk_id 在一个 token 下只出现一次。
5. 构建完才替换 shared cache，最后清 dirty。

这一顺序比“边遍历边修改旧 shared dict”更安全：list_chunks 或 tokenize 中途抛异常时，旧 _indexes/_chunks 尚未被覆盖，dirty flag 也没有被清掉。它不是数据库 transaction，但避免发布 half-built snapshot。

### 5.11 keyword_search() 的六步检索（qa.py:53-82）

#### Step 1：ensure index

~~~python
if collection not in self._indexes or collection in self._dirty_collections:
    self._build_index(collection)
~~~

两个条件对应 cold cache 与 stale cache。由于 or short-circuit，任一成立就 full rebuild。

#### Step 2：query tokenize + empty short-circuit

~~~python
query_tokens = tokenize(query)
if not query_tokens:
    return []
~~~

注意 build 发生在 tokenize query 之前。这与 SPEC 检索流程顺序一致，但意味着首次空 query 也会触发一次 index build；这是当前真实成本。

#### Step 3：posting lookup + matched count

~~~python
matched_tokens: Dict[str, int] = {}
index = self._indexes[collection]
for token in query_tokens:
    for chunk_id in index.get(token, set()):
        matched_tokens[chunk_id] = matched_tokens.get(chunk_id, 0) + 1
~~~

- index.get(token, set()) 让 no-match token 变成空迭代，不需要 if。
- query_tokens 已由 T0601 去重，因此每个 token 对同一 chunk 最多加 1。
- matched_tokens 的 value 实际是“该 chunk 命中的 unique query token 数”，不是 term frequency。

TypeScript 类比是 Map.get(token) ?? new Set()，再用 Map.set(chunkId, (old ?? 0) + 1)。

#### Step 4：join chunk data + normalize score

~~~python
"keyword_score": matched_count / len(query_tokens)
~~~

_indexes 只存 chunk_id，所以这里用 _chunks 做 in-memory join，补回 file_id/file_name/content。分子不大于分母，score 自然落在 [0, 1]；空 query 已提前 return，避免 division by zero。

返回 dict 只选择 SPEC F009 规定的 chunk_id、file_id、file_name、content、keyword_score。虽然缓存里保存的是完整 ChunkRecord，collection_name、chunk_index 与 metadata 并没有被顺手暴露；“内部 snapshot 更丰富”不等于“公开 retrieval result 可以扩字段”。

#### Step 5/6：sort + top_k

~~~python
results.sort(key=lambda result: result["keyword_score"], reverse=True)
return results[:top_k]
~~~

lambda 提取动态 dict 字段作为 sort key；reverse=True 表示高分在前。list slice 返回新列表并截断。当前没有定义同分 tie-breaker；测试只冻结“分数降序 + top_k”，不应声称同分结果顺序稳定。

---

## 6. 测试理解：每个测试在防什么回归

### 6.1 SPEC examples 是 executable contract

[test_qa.py:23-39](../../backend/tests/test_qa.py#L23) 把 [SPEC:1066](../SPEC.md#L1066) 的三个例子直接写成 assertEqual。这里用 list equality，不只是比较集合：内容、数量和顺序都必须一致。

### 6.2 项目补充的边界测试

- PyThOn3 RAG2026：证明 lowercase 不会把数字拆掉。
- A 1 中：证明孤立英文字母、数字和单汉字都返回空。
- 机器，学习：证明 bigram 不跨 punctuation boundary。
- Python PYTHON 机器机器：证明 normalized 后去重，并保留 first-seen order。

### 6.3 unittest 的 TS 类比

Python 的 self.assertEqual(tokenize(...), expected) 约等于 Vitest/Jest 的 expect(tokenize(...)).toEqual(expected)。assertEqual 对 list 做 structural equality；不是 is identity comparison。

### 6.4 当前测试没有证明什么

- 没有证明所有 Unicode 汉字、emoji 或 accented Latin letters 的行为。
- 没有 performance benchmark；O(n) 是基于实现结构的复杂度分析，不是实测 SLA。
- 没有经过真实 ChromaVectorStore；T0602 tests 使用 Mock(spec=VectorStore)。
- 没有经过真实 upload/rename/delete HTTP workflow；AC-F009-05 单测直接调用 invalidation seam。
- 没有并发测试，也没有验证多个 VectorStore namespace 下同名 collection 的隔离。
- 没有冻结 equal-score results 的 tie order。

### 6.5 Mock(spec=VectorStore) 与 setUp 隔离

[test_qa.py:55-60](../../backend/tests/test_qa.py#L55) 每个 test 都 clear 三份 class-level state，再创建 Mock(spec=VectorStore)：

~~~python
KeywordRetriever._indexes.clear()
KeywordRetriever._chunks.clear()
KeywordRetriever._dirty_collections.clear()
self.store = Mock(spec=VectorStore)
self.retriever = KeywordRetriever(self.store)
~~~

- clear 是必要的，因为 class attributes 会跨 test instance 存活；漏掉会让 lazy-build test 误用前一场景 cache。
- spec=VectorStore 限制 mock 只能模拟 interface 上存在的 attribute；拼错 list_chunks 会更早暴露。
- TypeScript 类比：beforeEach 清空 static Maps，再注入一个满足 VectorStore interface 的 typed mock。

### 6.6 T0602 七场景如何形成证据链

1. lazy test 在 search 前 assert_not_called，search 后 assert_called_once_with，证明真正的延迟构建。
2. no-match test 证明所有 posting lookup 为空时返回 []。
3. partial-score test 证明 3/5 = 0.6，而不是按 raw term frequency 计分。
4. mixed-language test 让 T0601 的两个 token channel 第一次进入完整 retrieval。
5. top-k test 同时检查 full-match 排在 partial-match 前并截成一条。
6. rebuild test 先建立 old snapshot，再更新 mock source、调用 seam，第二次 search 找到 new，并确认 list_chunks 共调用两次。
7. absent invalidation test 证明“无 cache 即 no-op”，不会制造无意义 dirty entry。

---

## 7. 数据流与复杂度

~~~text
text: str
  ├─ alphanumeric finditer → Match → group → lowercase ─┐
  └─ Chinese finditer → Match → segment → bigrams ──────┤
                                                         ▼
                                                  raw List[str]
                                                         │
                                              len >= 2 filter
                                                         │
                                              stable dedup
                                                         ▼
                                                unique List[str]
~~~

- **类型变化**: str → Iterator[Match] → str tokens → List[str]。
- **时间复杂度**: 两次线性 regex 扫描 + 线性过滤去重，总体 O(n)。
- **空间复杂度**: raw token list 与 dedup dict 都随输入长度增长，O(n)。
- **失败形态**: 对合法 str 没有业务异常分支；空串、无匹配字符或只有单字符时返回空列表。类型 annotation 不是 runtime validation，非 str 输入不属于声明契约。

T0602 search data flow：

~~~text
collection + query + top_k
  → cache missing/dirty?
      → VectorStore.list_chunks(collection)
      → tokenize(each content)
      → build token → Set[chunk_id] + chunk lookup
  → tokenize(query)
  → posting-set lookup
  → Dict[chunk_id, matched_count]
  → join ChunkRecord + matched_count / len(query_tokens)
  → sort DESC
  → slice top_k
  → List[{chunk_id, file_id, file_name, content, keyword_score}]
~~~

- **build complexity**: 令所有 chunk content 总字符数为 C，tokenizer + posting registration 约 O(C)。
- **search complexity**: 令 query token 数为 q，各 posting set 大小之和为 P，则 lookup/计数约 O(q + P)，再对 m 个 matched chunks 排序 O(m log m)。
- **rebuild failure**: list_chunks/tokenize 抛异常时向上传播；local snapshot 未发布，dirty flag 不会被 discard。

---

## 8. 架构理解

### 8.1 新增能力与契约

T0601 新增 deterministic normalization boundary，T0602 已消费它建立 retrieval：

~~~text
tokenize(chunk.content) ──→ _indexes[collection][token].add(chunk_id)
tokenize(query)         ──→ lookup → count → normalize → rank
~~~

两条路径只有复用相同函数，字符规则、lowercase、长度过滤和去重才不会 drift。

### 8.2 责任边界

- tokenizer 负责 normalization，不负责存储和检索。
- KeywordRetriever 负责 index/cache/score/top_k。
- VectorStore 负责通过 public list_chunks() 提供数据；外部不得访问 Chroma private API。
- Phase 7/T0702 负责 keyword/vector fusion；不要把 merge/filter 塞进 tokenizer。
- keyword_index.py 是 mutation callers 与 shared cache 之间的 seam；它不拥有第二份 index。

---

## 9. Engineering Review 摘要

Phase 6 的工程主线从“小函数，大契约”扩展为“shared snapshot lifecycle”：zero-dependency tokenizer、public-interface build、class-level per-collection cache、lazy build、dirty/full rebuild、binary token coverage score。完整 ADR、共享状态风险与规模分析见 [Phase 6 Engineering Review](./engineering-review/phase-06-engineering-review.md)。

---

## 10. Technical Decision 速查

| 决策 | 备选方案 | 为什么选它 | 代价 / 边界 |
|------|----------|------------|-------------|
| 中文 character bigram | jieba、单字 token | SPEC 冻结；零 dependency；未登录词不依赖词典 | token 更多；不理解词义 |
| 英文连续 alphanumeric | 按字符、按 whitespace | 保留 Python3 / RAG2026 技术 token | 下划线、连字符、accented Latin 会断开 |
| 先找中文 segment 再切片 | 删除非中文后整体切 | 不跨标点/英文制造假 bigram | 标点会打断中文连续性 |
| dict.fromkeys stable dedup | set | unique + deterministic output | 多一个临时 dict |
| pure function | tokenizer 内持有 index state | 两条路径复用、单测简单、职责单一 | state 由 KeywordRetriever 管理 |
| class-level per-collection cache | instance cache / global service object | standalone seam 可按 collection 失效所有 instance 可见状态 | 同名 collection 跨 VectorStore namespace 可能碰撞 |
| dirty flag + query-time rebuild | mutation-time rebuild / incremental update | 写路径轻量；符合 v1 full rebuild | 首个后续 query 承担延迟 |
| 双表 index + chunk lookup | posting 中复制完整 ChunkRecord | posting 轻量，返回阶段按 id join；单次 build 先在 local dict 完成，再顺序发布两张表 | 两次 class-dict assignment 不是并发意义上的 atomic publication；无锁场景仍可能观察到跨版本双表 |
| binary coverage score | term frequency / BM25 | 精确兑现 SPEC，归一化到 [0,1] | 不区分稀有词与常见词 |

完整 ADR 与 Future 评估只保存在 Engineering Review。

---

## 11. Interview Notes 路由

按 cadence，Task candidates 仍保留在第 4 节的 [T0601 candidates](#t0601-interview-candidates) 与 [T0602 candidates](#t0602-interview-candidates) 作为来源；Phase Learning Review 已完成筛选、去重与 Phase-level 提升，完整话术进入累计的 [Interview Guide Phase 6 深度章](./interview-notes/dx-rag-interview-guide.md)。本文不复制 30 秒 / 1–2 分钟 / 高频追问答案。

本 Phase 没有真实 incident、SPEC conflict 或 production-like failure investigation，因此没有为了凑格式虚构 STAR；晋升的是可由代码与测试证明的技术与工程问答。

- **诚实边界**：tokenizer、inverted index、lazy/dirty lifecycle、keyword score 与 top_k 已实现并通过 unit tests；T0702 的 service-level hybrid retrieval 与 T0703 `retrieve()` facade 已实现并通过独立 unit tests；真实 concrete Chroma lifecycle、upload-to-search E2E 与 QA API 尚未完成。

---

## 12. Future / Not Implemented

| 方向 | 触发或 owner | SPEC 状态 |
|------|--------------|-----------|
| incremental index | [FUTURE] 规模增长后才评估 | v1 明确排除 |
| BM25 / TF-IDF / position-aware match | [FUTURE] 需要质量评测证明价值时 | v1 明确排除 |
| 扩大中文 Unicode 范围 | [FUTURE] 出现真实语料缺口时 | 非当前 SPEC |
| 保留跨语言 source order | [FUTURE] 消费者需要位置语义时 | 非当前 SPEC |
| cache namespace 纳入 VectorStore identity | [FUTURE] 多 store/tenant 场景 | 非当前 SPEC |
| equal-score deterministic tie-breaker | [FUTURE] API 需要稳定翻页/回放时 | 非当前 SPEC |
| upload → invalidate → query E2E | [FUTURE] Phase 12 acceptance | SPEC AC-F009-05 完整工作流 |

---

## 13. 自测与动手练习

### 自测题

1. 为什么 n 个连续汉字只产生 n - 1 个 bigram？
2. “机器，学习”为什么不会产生“器学”？
3. Python3 为什么返回一个 token，而 Python-3 最终只返回 python？数字 3 在哪一步被丢弃？
4. dict.fromkeys 在这里同时兑现了哪两个契约？
5. 为什么 AC-F009-05 可以说 lifecycle unit behavior PASS，却仍不能说 literal upload-to-query E2E PASS？
6. “机器Python学习”的实际输出顺序是什么？为什么？
7. 哪些结论来自 SPEC，哪些来自当前代码，哪些只是 Future 建议？
8. 为什么 _indexes 与 _chunks 要先在 local dict 构建完成、再顺序替换？这种写法防住了哪类异常，又为什么仍不等于并发下的 atomic publication？
9. absent collection invalidation 为什么不加入 dirty set？
10. partial-match 的 0.6 是如何从 posting lookup 得出的？
11. class-level cache 为什么要求 setUp 显式 clear？
12. 如果 document build 侧 lowercase、query 侧不 lowercase，会出现什么 indexing/query drift？为什么“复用同一函数”比“复制同一规则”更可靠？
13. 从 upload 成功到新 chunk 可检索，完整 lifecycle 是什么？当前 unit tests 证明到了哪一段，真实 E2E 又缺哪一段？

### 动手练习（不要直接改产品代码）

在 Python REPL import tokenize()，先预测再执行：

~~~python
tokenize("")
tokenize("A 中 1")
tokenize("Python-3")
tokenize("机器Python学习")
tokenize("机器，机器")
~~~

然后为每个结果指出：是 alphanumeric regex、Chinese segment、length filter 还是 stable dedup 决定了它。

再手工构造两个 chunks：一个内容为“机器学习算法”，另一个为“机器学习”。不用运行代码，先画出 query“机器学习算法”涉及的 posting sets，计算两个 chunk 的 matched_count / keyword_score，并预测 `top_k=1` 返回谁；最后再用 `KeywordRetriever` + Mock 验证你的推理。

---

## Quick Review

~~~text
Phase model
  Contract    tokenize() 统一 document/query token space
  Snapshot    VectorStore.list_chunks() → token postings + chunk lookup
  Lifecycle   cold/dirty → query-time full rebuild
  Ranking     unique-token coverage → DESC → top_k

T0601
  Input       str
  Core        English/digits regex + lowercase
              Chinese segment + overlapping bigram
  Finalize    min length 2 + stable unique
  Output      List[str]
  Nature      deterministic pure function
  Verified    6 tokenizer test methods PASS

T0602
  State       _indexes + _chunks + _dirty_collections
  Build       lazy, from VectorStore.list_chunks()
  Invalidate  existing cache → dirty; absent cache → no-op
  Rebuild     next search, full snapshot
  Score       matched unique query tokens / total unique query tokens
  Output      score DESC → top_k
  Verified    7 retriever test methods PASS
  Deferred    literal upload-to-search E2E → Phase 12
~~~

> **Phase 6 Learning Review 收官（2026-08-27）**：T0601 tokenizer + T0602 inverted index/search 已 consolidation 为一个“共享 normalization contract → derived snapshot → dirty/full rebuild → normalized coverage ranking”的统一心智模型。Phase Gate Review 已裁定 PHASE_6_PASS，Interview Candidates 已筛选晋升到项目级 Interview Guide；真实 upload-to-search E2E 仍归 Phase 12。本段记录的是当时的历史 checkpoint。
>
> **后续状态（T0701 Learning Pass，2026-08-28）**：Phase 6 收官时尚未启动 Phase 7；之后 T0701 已在 `qa.py` 增加 `VectorRetriever`，其 query embedding、`similarity_score → vector_score` 映射与 expanded recall 见 [Phase 7 Technical Learning](./phase-07-vector-retrieval.md)。
>
> **后续状态（T0702 Learning Pass，2026-08-31）**：Phase 7 已在 `qa.py` 增加 `HybridRetriever`，按 `chunk_id` 做 0.3/0.7 weighted fusion、`MIN_RELEVANCE_SCORE` filter 与最终 Top-K；当时 T0703 unified wiring、真实 upload-to-search E2E 与 QA API 仍为 Future。本段保留 T0702 checkpoint 的历史边界，不把 keyword branch 的完成误写成完整 QA 完成。
>
> **后续状态（T0703 Learning Pass，2026-08-31）**：T0703 已在 `qa.py` 提供 `retrieve(query, collection, top_k)` facade：创建 concrete `ChromaVectorStore`，先做 empty-collection preflight，非空时把同一个 store 注入 Keyword/Vector/Hybrid retrievers，并让 missing-collection 异常自然向上传播。此 facade 的 wiring tests 是 patched composition boundary；真实 upload → ChromaDB → query E2E、QA API 与 context/LLM 仍属于后续范围。本段只同步后续事实，不改写 Phase 6 原有 Gate/Learning Review 结论。
