# Phase 6 — Keyword Retrieval：从词面匹配到可重建的检索索引

## 1. 这一阶段我到底要学什么？

Phase 6 为 DX-RAG 加入**关键词检索**：把用户问题和文档片段转换成可比较的文本单元，找出包含这些单元的片段，再按匹配程度排序。它提供候选材料，后续问答才会利用这些材料组织回答。

你只需要知道：RAG 会先检索材料再生成回答；chunk 是文档切分后的片段；collection 是一组知识库数据。不需要先读 `TASKS.md`。读完应能手算一次关键词查询、读懂 `tokenize()` 与 `KeywordRetriever`，并解释索引过期、重建失败和测试边界。

```text
文档 → 解析与切分 → 持久化 chunks → Keyword Index（关键词索引）
                                           ↑             │
用户问题 ─────────────────────────→ Keyword Retrieval ────┘
                                           │
                                      候选 chunks
                                           ↓
                            后续：与向量结果融合 → RAG 问答
```

建议先读概念和例子，再对照实现；回访时可直接看第 16 节的一页复习。代码地图和验收历史放在附录，随时可查。

本文正文解释**当前仓库实现**；涉及后续增加的能力会明确说明。概念解释是一般技术知识；**Verified** 表示有明确代码或测试证据（会注明是哪一种），**Documented** 表示规格或评审记载，**Inferred** 表示据实现推导，**Unknown** 表示尚无证据。测试证明的范围不会因代码已经存在而扩大。

## 2. 为什么已经有向量检索，还需要关键词检索？

**词面匹配（lexical matching）**比较实际出现的文本信号；**语义匹配（semantic matching）**借助向量表示比较意思是否接近。假设材料写“机器学习是人工智能的分支”，问题问“AI 的子领域”，两者意思相关，但词面未必重合。只靠关键词可能找不到；向量检索为这种改写提供另一条路径。

反过来，类名 `KeywordRetriever`、缩写 `NLP`、技术 token `Python3` 往往带有具体定位意义。保留词面信号可以补充语义泛化。这是 [SPEC 的关键词检索动机](../SPEC.md#f009-keyword-retrieval)，不是本项目已经测得“混合检索总是更好”的结论。

这里的“精确”指**经过同一分词规则后的 token 相同**，不是原始字符串逐字相等。当前实现会忽略英文大小写，也会在下划线、连字符处断开。因此不能据此承诺所有型号、错误码或复合标识符都被完整保留。

两种检索互补的架构动机是 Documented；后续受控语料的真实验证见附录 C。它们并不构成对不同检索方案的统计质量比较，0.3/0.7 融合权重也没有实验最优性证据。

## 3. 先理解基础概念

### 3.1 Tokenization：先决定“拿什么来匹配”

**Tokenization（分词）**把字符串变成一串用于匹配的单元，单个单元叫 token。这里的 token 不是 LLM 用于计费或上下文长度计算的模型 token。

例如 `Python FastAPI` 变成 `python`、`fastapi`。其中把大小写统一叫 **normalization（归一处理）**：让不同写法进入同一个比较规则。文档和问题必须复用同一个 `tokenize()`，否则文档里的索引 key 与问题里的查找 key 可能对不上。

### 3.2 中文为什么不能只按空格切？

中文句子通常没有词间空格。当前 DX-RAG 不使用词典判断词义，而是在连续中文段里每次取两个相邻字符，再向右移动一个字符。这叫 **overlapping character bigram（重叠双字符片段）**。

```text
机器学习
位置 0：机器
位置 1：  器学
位置 2：    学习
输出：机器 / 器学 / 学习
```

“器学”不必是语言学意义上的词；它只是可比较的字符片段。连续 n 个汉字产生 n−1 个窗口。`机器，学习` 的逗号先把中文分成两段，只产生 `机器`、`学习`，不会制造跨标点的 `器学`。

实际规则是：英文和数字取连续 `[a-zA-Z0-9]+` 并转小写；中文仅取 `U+4E00–U+9FFF` 的连续段；生成 bigram；过滤长度小于 2 的 token；按 token 生成顺序稳定去重（先英文数字通道，再中文通道，不是跨语言原文顺序）。去重使重复 token 不重复计分。单汉字、孤立字母和数字不会留下 token。

### 3.3 Inverted Index：从文本单元反查片段

普通文档表回答“这个 chunk 有什么内容”；**倒排索引（inverted index）**反过来回答“哪些 chunk 包含这个 token”。

```text
Chunk A: Python FastAPI
Chunk B: Python RAG

python  → {A, B}
fastapi → {A}
rag     → {B}
```

每个 token 后面的 ID 集合叫 **posting set**。查询 `FastAPI` 时只查 `fastapi` 对应的集合，不必重新分词每篇文档。集合只表示“出现过”，不会因同一 token 在 chunk 中出现十次而重复加入 ID。

### 3.4 分数：覆盖了问题的多少信号？

**Coverage（覆盖率）**在本项目中表示：一个 chunk 包含了多少种问题 token。问题有 5 种不同 token，某 chunk 命中其中 3 种，它的关键词分数就是 3/5 = 0.6。

```text
keyword_score = 命中的 unique query token 数 / 全部 unique query token 数
```

这是分数的归一化：分母把命中数转为 `[0,1]` 范围内的比例。它不是按候选最高分再缩放，也不是答案正确的概率。1.0 只表示所有问题 token 都出现了；不保证原句相邻、语序一致或语义正确。无命中的 chunk 不进入返回列表，不会作为分数为 0 的行返回。

**Ranking（排序）**把高分候选放前面；**Top-K**只取前 K 条。后续融合需要知道两路分数的范围和含义才能加权，但范围相同不等于两种分数经过了概率校准。

## 4. Phase 6 在整个 DX-RAG 中处于什么位置？

```text
上传 / 摄入
    ↓
解析、清洗、切分、生成 embedding
    ↓
VectorStore / Chroma：持久化文本、向量和元数据
    ├─ list_chunks() → 关键词索引 → KeywordRetriever ─┐
    └─ search() + 问题向量 ───────→ VectorRetriever ──┤
                                                     ↓
                                               HybridRetriever
                                                     ↓
                                       上下文与历史 → LLM → 答案和来源
```

在 Phase 6 之前，存储层已提供公开的 chunk 读取接口，上传与知识库管理已有索引失效通知的调用位置。Phase 6 新增共享分词规则、内存倒排索引、失效重建和关键词候选排序。这里读取文本不需要重新生成 embedding，也不需要从向量反推原文。

向量查询适配、两路融合和统一检索入口在后续检索阶段接上；问答编排和 HTTP 接口再由后续问答阶段接上。当前这些组件已经存在，不能把它们都算作 Phase 6 收官时的能力。

实现位于 Service Layer 的 [qa.py](../../backend/app/services/qa.py)。`KeywordRetriever` 通过构造函数接收 `VectorStore`，这叫**依赖注入**：使用者提供具体存储对象，检索器依赖公开接口。它类似一个接收 TypeScript interface 实现的 service，不是 route handler。工程任务坐标见附录 B。

## 5. DX-RAG 的 Keyword Retrieval 是怎么工作的？

### 5.1 同一份文本契约，同时用于建索引和查询

需要先统一比较规则，才能可靠查表。`qa.py` 的 `tokenize(text: str) -> List[str]` 是纯函数：同样的字符串得到同样的列表，不读写索引、不依赖网络或运行环境配置。标准库 `re` 提供正则扫描，没有新增中文 NLP 依赖。

Python 的 `Dict`、`List`、`Set` 是类型注解，不会自动进行运行时校验。`str -> List[str]` 可类比 TypeScript 的 `(text: string) => string[]`，但普通 Python 执行时不会因为违反注解就自动拒绝值。非 `str` 输入不属于这里声明的契约。

#### 5.1.1 模块级预编译两条 pattern

~~~python
_ALPHANUMERIC_PATTERN = re.compile(r"[a-zA-Z0-9]+")
_CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")
~~~

第一条 pattern：方括号表示 character class；加号表示连续出现一次或更多次，所以 Python3 是一个 token。lowercase 不写进 regex，而在匹配后调用 lower()。

第二条 pattern：Unicode range U+4E00–U+9FFF 是基本 CJK Unified Ideographs 区；加号先找连续中文 segment，bigram 再在 segment 内生成。标点、空格、ASCII 会切断 segment，因此“机器，学习”不会产生跨逗号的“器学”。

**实现核对（Verified）** 当前实现只覆盖这个基本区间；没有证据表明它覆盖全部汉字扩展区。这是已知边界，不应扩写成“支持所有中文 Unicode”。

模块级常量的前导下划线表示 module-private convention，类似 TS 文件中不 export 的 const；它不是安全边界，外部仍可访问。

#### 5.1.2 英文/数字通道

~~~python
def tokenize(text: str) -> List[str]:
    """Tokenize text into unique alphanumeric tokens and Chinese bigrams."""
    tokens = [match.group().lower() for match in _ALPHANUMERIC_PATTERN.finditer(text)]
~~~

正则匹配返回 Match 对象，`group()` 才取出匹配字符串，`lower()` 再转小写。数据变化：

~~~text
text: str → finditer: Iterator[Match] → group/lower: str → List[str]
~~~

这里的 finditer 直接声明“要保留哪些字符段”，再逐个读取匹配结果；所有非 alphanumeric 字符自然成为边界。正则 split 也能表达分隔规则，这里是不同的实现表达方式，并非 split 无法完成。

TypeScript 类比：

~~~ts
const tokens = [...text.matchAll(/[a-zA-Z0-9]+/g)]
  .map(match => match[0].toLowerCase());
~~~

#### 5.1.3 中文 segment 与 sliding window

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

Python slice 的右边界不包含在结果中，与 JS String.slice 一致。长度 n 的 segment 有 n - 1 个合法起点。长度 1 时 range(0) 为空，因此不会产生单汉字 token；无需单独 if。

extend 接收的是 generator expression。它按需产生 token 并逐个追加；如果写 append(generator)，列表里会装进 generator 对象本身，语义完全不同。

TypeScript 直译：

~~~ts
for (const segment of chineseSegments) {
  for (let index = 0; index < segment.length - 1; index++) {
    tokens.push(segment.slice(index, index + 2));
  }
}
~~~

#### 5.1.4 过滤与 stable dedup

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

#### 5.1.5 一次完整 trace

输入“Python PYTHON 机器机器”：

1. alphanumeric 通道 → python, python。
2. 中文 segment → 机器, 器机, 机器。
3. 长度过滤 → 全部保留。
4. stable dedup → python, 机器, 器机。

这正是 [stable dedup 测试](../../backend/tests/test_qa.py) 的断言。它同时证明 lowercase 后的英文会去重，以及重复中文 bigram 会去重。

#### 5.1.6 一个容易忽略的输出顺序

**实现核对（Verified）** 实现先扫描全文的英文/数字，再扫描全文中文。因此对于“机器Python学习”，返回顺序会是 python, 机器, 学习，而不是严格按原文交错顺序。

当前 SPEC 把 query tokens 用作 unique set 参与匹配与评分，没有定义跨语言 source order；KeywordRetriever 的 matched-token counter 也只看 token presence，不把 list 位置当作权重。

### 5.2 构建：把持久化文本变成查找表

为了避免每次查询都扫描并切分全部内容， `KeywordRetriever._build_index()` 会一次读取整个 collection，并准备两类数据：token 到 ID 的倒排表，以及 ID 到完整 `ChunkRecord` 的查找表。

```python
for chunk in self.vector_store.list_chunks(collection):
    chunks[chunk.chunk_id] = chunk
    for token in tokenize(chunk.content):
        inverted_index.setdefault(token, set()).add(chunk.chunk_id)
```

`VectorStore.list_chunks()` 是唯一的构建数据入口。当前 concrete adapter 从 Chroma 读取 documents/metadatas 并转换成 `ChunkRecord`，不读取 embedding 向量。检索器不能绕过这个接口访问 `_collection` 或 Chroma 私有对象。

`setdefault(token, set())` 表示“已有就取出，没有就放入一个空集合”，随后 `.add()` 注册 ID。Python `Dict[str, Set[str]]` 可类比 `Map<string, Set<string>>`。每个 chunk 都进入记录表，即使它没有生成可索引 token；posting 只保存 ID，避免为每个 token 重复保存整段内容。

这两张表先在函数的局部变量中完整建好，再发布到共享缓存。它们是什么、为什么必须一起更新，见第 7、8 节。

### 5.3 查询：查候选、计数、补全数据、排序

先把索引视为可用查找表；如果从未构建，或底层数据改过，查询必须先刷新它，生命周期在第 8 节展开。实际执行顺序如下：

```text
keyword_search(collection, query, top_k)
  → 确保索引存在且有效，必要时 _build_index(collection)
  → tokenize(query)，无 token 则返回 []
  → 逐个 token 查 posting set
  → 按 chunk_id 累计命中 token 数
  → 通过 ID 补回 chunk 数据，计算 coverage
  → 分数降序 → 截取 top_k → 返回候选
```

索引检查在分词之前。因此首次空 query 也可能付出全量 build 成本；不能把“空 token 直接返回”理解成“绝不访问存储”。

计数代码只关心 token 是否出现：

```python
for token in query_tokens:
    for chunk_id in index.get(token, set()):
        matched_tokens[chunk_id] = matched_tokens.get(chunk_id, 0) + 1
```

没有对应 token 时，`get(token, set())` 给出空集合，循环自然跳过。可类比 JS 的 `map.get(token) ?? new Set()`。问题 token 已经去重，posting 又是集合，因此每种问题 token 对一个 chunk 最多加一次分；`matched_tokens` 不是文本词频表。

返回阶段用 ID 从记录表取出 `file_id`、`file_name`、`content`，这叫 **in-memory join（内存中的按键关联）**。`keyword_score = matched_count / len(query_tokens)`；前面的空 token 分支同时避免除以零。公开结果只包含：

```text
{chunk_id, file_id, file_name, content, keyword_score}
```

内部 `ChunkRecord` 更丰富，并不意味着 `collection_name`、`chunk_index`、`metadata` 会随关键词结果一起暴露。

```python
results.sort(key=lambda result: result["keyword_score"], reverse=True)
return results[:top_k]
```

`lambda` 取出每行的排序字段，`reverse=True` 表示降序；slice 返回截断后的新列表。当前没有额外的同分排序规则，posting set 的遍历可能影响同分候选的初始顺序；不能承诺同分结果稳定。

## 6. 用一个具体例子走完整流程

以下是与实现一致的教学数据，A/B 是便于手算的 chunk ID 简写，实际 ID 由存储记录提供。两条记录各自带有 file_id、file_name 等字段，这里只展开内容。

| chunk | 原始 content | `tokenize(content)` |
|---|---|---|
| A | 机器学习算法 | 机器、器学、学习、习算、算法 |
| B | 机器学习 | 机器、器学、学习 |

首次查询时构建：

```text
倒排表                         记录表
机器 → {A, B}                 A → A 的 ChunkRecord
器学 → {A, B}                 B → B 的 ChunkRecord
学习 → {A, B}
习算 → {A}
算法 → {A}
```

用户查询 `机器学习算法`，同一个函数给出 5 个 unique tokens。依次查表后，A 累计 5 次，B 累计 3 次。候选是 posting sets 的并集 `{A,B}`，不是要求每个 token 都命中的交集。

| 候选 | 命中数 | 分母 | `keyword_score` | 结果顺序 |
|---|---:|---:|---:|---:|
| A | 5 | 5 | 1.0 | 1 |
| B | 3 | 5 | 0.6 | 2 |

返回前补回各自的文件信息和内容。`top_k=2` 返回 A、B；`top_k=1` 只返回 A。若查询改成 `量子计算`，三个 token 都找不到 posting，返回 `[]`。

现在尝试只改一个条件：让 B 的内容变成“机器学习，机器学习”。逗号隔开两段，重复不会产生新的 unique token，所以 B 仍得 0.6。如果直接拼成“机器学习机器学习”，跨边界会新增“习机”；它不在本次 query 中，因此分数也仍为 0.6。这说明这里的分数是问题信号覆盖率，不是出现次数越多分数越高。

## 7. 核心数据结构：系统到底记住了什么？

为了避免每次查询重复读持久化数据，系统保存了一份内存**快照（snapshot）**，即上次构建时读到的记录与索引。它可以从持久化 chunks 重新计算，因此叫**派生状态（derived state）**。

底层变更后，旧快照可能不再可信。系统用 **dirty（脏）标记**记录“下次使用前需要重建”；标记过期的动作叫 **invalidation（失效通知）**。

```text
KeywordRetriever 的共享状态
  collection name
    ├─ _indexes[collection] → token → Set[chunk_id]
    ├─ _chunks[collection]  → chunk_id → ChunkRecord
    └─ collection 是否属于 _dirty_collections？
```

| 状态 | 保存什么、为何需要 | 写入者 | 读取者 | 过期或不一致的影响 |
|---|---|---|---|---|
| `_indexes` | 每个 collection 的 token→ID 集合，快速找候选 | `_build_index()` 发布完整表 | `keyword_search()` 查 posting；`invalidate()` 检查是否已有缓存 | 新内容漏召回，删除内容仍可能命中 |
| `_chunks` | 每个 collection 的 ID→完整记录，补回返回字段 | `_build_index()` 发布完整表 | `keyword_search()` 按 ID 关联 | 旧文件名/内容；若与倒排表跨版本，可能找不到 ID |
| `_dirty_collections` | 需要刷新快照的 collection 名集合 | `mark_dirty()` 添加；成功 build 后 `discard()` | `keyword_search()` 决定是否重建 | 漏标会继续用旧快照；没清除会重复重建 |

三份容器定义在 class body，而 `self.vector_store` 定义在 `__init__` 中。前者是 **class-level state（类级共享状态）**，同一进程内的实例共享；后者是实例自己的依赖。原学习记录里的对象身份探针确认 `a._indexes is b._indexes` 为 True。

```text
Retriever A ── vector_store A      Retriever B ── vector_store B
      │                                  │
      └──── 同一进程共享 class dict/set ───┘
                      │
              key 只有 collection name
```

可类比 TypeScript 的 `static Map` 配合实例构造参数，或模块级共享缓存。它不表示所有 retriever 是同一个实例，也不等于有一个统一管理依赖的 singleton（单例服务）。当前确实可以创建多个实例。

这产生一个重要边界：若两个独立 store 都有名为 `docs` 的 collection，缓存没有记录 store identity，后创建的实例可能读取前一个 store 的快照。类级共享解决了通知可见性，却没有自动解决数据源隔离；这是已知风险，未有多 store 隔离测试。

## 8. 为什么要有 lazy / dirty rebuild？

### 8.1 数据已经持久化，索引为什么还会旧？

持久化 chunks 是索引内容的 **source of truth（权威数据源）**；内存表只是它的派生结果。上传增加内容、删除移走内容、重命名改变名称或元数据，都可能让旧表与真实记录不一致。写入 Chroma 不会自动修改 Python 内存字典。

**Lazy build（延迟构建）**表示等首次需要索引时才建；**lazy rebuild（延迟重建）**表示先标记过期，下一次查询才重新计算。这样没有被查询的 collection 不付建表成本，写路径只做轻量标记，代价由后续首次读取承担。

```text
尚无索引 ──首次 keyword_search──→ 全量读取 → 有效快照
   │                                         │
   └─正常 invalidate：no-op                  └─数据变更 → 标 dirty
                                                        │
                            有效快照 ← 全量重建 ← 下次 keyword_search
```

没有索引时正常失效通知不需要制造 dirty entry，因为首次查询本来就会 build。`invalidate()` 是 `@classmethod`：`cls` 指向类，不必先找到某个实例。它只在 `_indexes` 已有 collection 时调用 `mark_dirty()`；后者向共享 set 添加名字。重复添加是幂等的，即重复通知不改变最终标记结果。按 dict/set 常规操作推导，正常标记的平均成本约 O(1)，不随 collection 内容全量扫描。

### 8.2 写操作怎样通知检索器？

[失效通知接口](../../backend/app/services/keyword_index.py)里的 `invalidate_keyword_index()` 是 mutation callers 与缓存之间的连接点（seam）。上传、文件删除、知识库删除和重命名调用它；重命名通知旧名和新名。函数内 import 表示调用时才解析 `KeywordRetriever` 依赖，它没有自己的第二份索引。

**当前实现核对（Verified：代码）**：接口先调用 `KeywordRetriever.invalidate()`；如果该调用抛出 `Exception`，捕获后调用 `mark_dirty()` 强制标脏，并用 `logger.exception()` 记录原异常。这是后续增加的恢复路径，不是原 Phase 6 单测当时证明过的能力。

持久化上传/删除已经提交后，缓存维护失败不应把成功操作报告为失败；下一次检索应从持久化记录恢复。当前 SPEC 也明确了这条提交后缓存维护契约。它不保证进程崩溃、内存耗尽或兜底标记本身失败都能恢复；捕获范围是正常 `invalidate()` 调用。后续故障注入证据及历史变化见附录 C。

### 8.3 全量构建如何避免发布半张表？

`_build_index()` 先用局部 `inverted_index` 和 `chunks` 构建完成，最后才执行：

```python
self._indexes[collection] = inverted_index
self._chunks[collection] = chunks
self._dirty_collections.discard(collection)
```

若 `list_chunks()` 或 `tokenize()` 在构建阶段抛异常，异常向上传播，旧表没有被覆盖，已有 dirty 标记不会被清除。冷启动时也不会发布残表，下次查询仍会尝试构建。`discard()` 删除不存在的标记也不会报错。

它避免了单线程构建异常暴露半成品，但两次赋值不是一个并发事务。没有锁的并发查询可能观察到不同版本的两张表；build 与 invalidate 交错也缺少测试保障。重建时旧表和新表还可能同时占内存。

### 8.4 一致性保证到哪里？

正常单进程、顺序执行的路径中，dirty 查询先重建再读，不会主动回退到旧快照；失效通知只保留旧表等待替换，不立即删除数据。服务重启后缓存消失，首次相关查询重新构建，并非启动时自动扫描全部 collection。

多个 worker 是多个进程，各自有一套字典和 dirty set。一个进程处理写入并标脏，不会自动通知其他进程。当前代码没有跨进程缓存一致性协议，也没有并发原子发布保证。

## 9. 为什么这样设计？

下表的选择与理由来自冻结的关键词契约和 [Engineering Review](./engineering-review/phase-06-engineering-review.md)（Documented）；升级触发条件是工程推理（Inferred），不是已达到的性能门槛。表里的对照方案是设计比较或未来选项，没有仓库证据说明它们已做实验竞赛。jieba 是词典驱动的中文分词工具；TF-IDF 用词频与词在全库中的稀有程度加权，BM25 还考虑词频饱和与文档长度等因素。这里介绍名称是为了理解设计边界，不表示项目已经实现这些方法。

| 问题 | 当前选择与 v1 理由 | 代价 / 对照方案 | 何时重新评估 |
|---|---|---|---|
| 中文无空格，且不引入词典依赖 | 连续中文段 bigram；零第三方依赖，无未登录词词典维护 | 字符重合不理解词义；jieba、单字 token 只是对照，jieba 在当前范围外 | 实际语料暴露召回缺口或索引体积压力 |
| 英文技术词带数字 | 连续 alphanumeric + lowercase，保留 Python3/RAG2026 | 按字符或空格是对照；当前下划线、连字符、accented Latin 会断开 | 真实标识符查询失败时先补回归案例 |
| 标点不能制造虚假中文相邻关系 | 先找 segment 再切窗口，不是删光非中文后拼接 | 标点确实打断连续性 | 消费者提出不同边界契约时 |
| 重复词不应改变分母，输出需可复查 | `dict.fromkeys` 稳定去重 | `set` 不能承诺相同输出顺序；多一个临时 dict | 有实测内存压力才评估实现 |
| 文档和查询必须匹配同样的 key | 纯函数复用，状态单独放在 retriever | 不在 tokenizer 内持有索引或配置；替换规则需要重建索引 | 新规则有评测依据且能统一迁移时 |
| 查 token 后还要返回文件信息 | ID postings + ChunkRecord 双表，避免每项复制内容 | 双表必须一致；不是原子发布 | 并发访问需求或相关失败暴露时 |
| 写调用方没有 retriever 实例 | class-level cache + classmethod 通知 | instance cache / application-owned singleton 是对照；同名 store 隔离风险 | 多 store/tenant 或应用生命周期管理需求 |
| 缓存可重算，不希望写路径重建全部内容 | 内存、lazy build、dirty 后全量 rebuild；v1 明确无增量 | 首个后续 query 延迟、重启冷缓存；mutation-time rebuild / incremental 是对照 | 重建耗时与峰值内存实测不可接受时 |
| 下游需要范围明确的分数 | binary unique-token coverage，自然归一化 | 不用词频、稀有度或位置；BM25/TF-IDF 不在 v1 范围 | 评测证明等权覆盖不足时 |

“适合 v1”指规则直接、接口清楚、实现可验证，且评审采用本地单进程前提，不表示索引能支撑无限数据量或已有线上性能验证。不能把零依赖、O(n) 推导写成具体 SLA（服务级别承诺）。

## 10. 它如何和后面的 Hybrid Retrieval 连接？

两路先各自召回候选，再把同一片段的信号合并，这叫 **hybrid fusion（混合融合）**。按 `chunk_id` 合并，才能识别“同一个片段同时被两路找到”，而不是按内容字符串误合并不同记录。

```text
KeywordRetriever → keyword_score ─┐
                                  ├→ 按 chunk_id 合并 → 加权分数 → 过滤 → Top-K
VectorRetriever  → vector_score ──┘
```

关键词分支交出 `chunk_id/file_id/file_name/content/keyword_score`。当前后续 `HybridRetriever.hybrid_search()` 给两路分别请求 `top_k * 2` 的候选预算，缺失分支的分数置零，再计算：

```text
final_score = keyword_score × 0.3 + vector_score × 0.7
```

`VectorRetriever` 把问题 embedding 交给 `VectorStore.search()`，将 `similarity_score` 映射为 `vector_score`；其内部还会扩大存储搜索预算并截回收到的候选预算。融合按最终分数降序，移除低于 `MIN_RELEVANCE_SCORE` 的项，再取最终 Top-K。固定权重是契约，不是质量最优参数。

例如关键词得 0.6、向量分支未召回的片段，在融合中只得 0.18；当前阈值为 0.30，最终会被过滤。因此“关键词检索到了”不等于“最终答案一定使用它”。

当前有两种上层组装方式：`retrieve(query, collection, top_k)` 是统一检索 facade（封装组装细节的入口），创建 concrete `ChromaVectorStore`，先检查空 collection，再把同一 store 注入三种 retriever；missing collection 异常自然向上传播。`QAService.answer()` 则直接使用 `HybridRetriever`，串起 context/history、LLM 与 sources，并不复用这个 facade。`POST /api/query` 负责请求校验、collection existence check、委托 QAService 和响应/错误格式。

Phase 6 自身不负责生成向量、融合权重、relevance filter、上下文拼接、LLM 调用或 HTTP 校验。后续代码已接上不改变这些责任边界；任务与验证坐标放在附录。

## 11. 常见失败场景和容易误解的地方

以下表格是根据代码进行的失败推理，不是虚构生产 incident。历史故障注入与工程判断另见附录 C。

| 症状或误解 | 原因 | 责任组件与当前行为 |
|---|---|---|
| 上传后搜不到新内容，或删后仍返回旧内容 | 派生快照落后，通知遗漏或另一个 worker 未标脏 | 写路径负责通知，KeywordRetriever 负责 dirty 后重建；无跨进程通知机制 |
| 大小写不同就漏召回 | 两侧规则不一致的假设性回归 | 当前两侧复用 `tokenize()` 避免规则漂移；复制两份规则比复用更易分叉 |
| 空 query 仍访问存储 | 索引有效性检查早于 query 分词 | `keyword_search()` 先 build，随后空 tokens 返回 `[]` |
| collection 存在但没有 chunks | 空数据与“collection 不存在”是不同状态 | 直接 keyword search 可建空表并返回 `[]`；`retrieve()` 的 count preflight 提前返回 |
| collection 不存在时出错 | cold/dirty build 调用存储接口，存储查找失败 | KeywordRetriever 不吞异常，也不逐次检查已有 clean cache 对应的存储是否仍存在；API/facade 有各自存在性边界 |
| 重建失败，查询报错 | `list_chunks()` 或分词阶段抛异常 | `_build_index()` 向上传播，不发布局部残表，不清已有 dirty，也不降级返回旧表 |
| 已提交上传因缓存失效调用失败而被误报失败 | 持久化结果与可重建缓存曾被混作一次成功条件 | 当前 seam 捕获正常 invalidate 异常、强制 dirty、记录日志；后续恢复证据不冒充 Phase 6 原始单测 |
| 两个 store 的同名库拿到错数据 | 共享 key 只有 collection name | 类级缓存没有 store namespace；当前不承诺这种部署隔离 |
| ID 存在但补不回内容，或读到旧字段 | 并发下双表可能跨版本 | local build 保护构建异常，不提供双表原子发布；无并发测试 |
| 1.0 被当作答案概率或短语匹配 | 覆盖率语义被扩大 | 只看 token presence，不看位置、词频、稀有度，不是 BM25 |
| 认为同分顺序固定或所有 top_k 输入都被校验 | 把底层 slice 当成 API validation | 类内 `top_k=0` 返回 `[]`，负数按 Python slice 取列表；合法输入应由调用边界保证 |

合法 `str` 的 tokenizer 没有业务异常分支，空串、无匹配字符或全是单字符会返回空列表。它不执行输入、访问路径或调用网络，但超长文本仍消耗 CPU/内存；不能因此推导出无资源风险。HTTP 输入约束不归 tokenizer 所有。

## 12. 测试到底证明了什么？

Phase 6 的测试证明了分词契约一致、索引按需构建、查询按定义计算覆盖率并排序，以及收到失效通知后下次查询会读取新快照。先记住这些行为，再看测试数量；数量不等于覆盖强度。

### 12.1 文本契约：输出内容和顺序都要对

[TokenizeTests](../../backend/tests/test_qa.py) 的 6 个测试方法包含规格示例及补充边界。一个方法可能有多条断言，因此“6 methods”不是“6 个输入”。

| 行为 | 测试方法 / 输入 | 真正冻结的内容 |
|---|---|---|
| 中文窗口 | `test_spec_chinese_examples`：机器学习、机器学习算法 | 3 个 / 5 个 bigram 的列表 |
| 混合语言 | `test_spec_mixed_language_examples`：Python机器学习、NLP 自然语言处理 | 英文通道 + 中文通道的精确列表；前者 4 tokens |
| 英文数字归一 | `test_english_and_numbers_are_lowercased_alphanumeric_tokens`：PyThOn3 RAG2026 | 小写且数字不拆开 |
| 单字符过滤 | `test_single_character_tokens_are_discarded`：A 1 中 | 返回空列表 |
| 标点边界 | `test_chinese_bigrams_do_not_cross_segment_boundaries`：机器，学习 | 不跨标点产生器学 |
| 稳定去重 | `test_duplicate_tokens_are_removed_in_first_seen_order`：Python PYTHON 机器机器 | python、机器、器机，首次出现顺序 |

`self.assertEqual(list, expected)` 类似 Jest/Vitest 的 `expect(...).toEqual(...)`，比较结构、数量、顺序，不是 `is` 对象身份；只比较集合会丢失这层输出契约。

### 12.2 索引与查询：用可控存储替身观察生命周期

[KeywordRetrieverTests](../../backend/tests/test_qa.py) 注入 `Mock(spec=VectorStore)`。Mock 是测试控制的存储替身，返回手工记录；`spec` 限制可访问属性属于接口，但并不等于真实 Chroma 行为或完整类型校验。

| 行为 | 测试方法 | 观察点 |
|---|---|---|
| 首次才建索引，中文全命中 | `test_index_is_built_lazily_from_list_chunks` | 查询前 `assert_not_called`，之后 `assert_called_once_with`，score 1.0 |
| 无匹配 | `test_no_matching_tokens_returns_empty_list` | posting lookup 全空时返回 `[]` |
| 部分命中 | `test_partial_match_score_uses_unique_query_token_count` | 机器学习对机器学习算法得 3/5 = 0.6 |
| 中英共同命中 | `test_mixed_language_tokens_can_all_match` | Python编程对应 python、编程，得 1.0 |
| 排序并截断 | `test_results_are_sorted_by_score_and_limited_to_top_k` | full-match 在 partial-match 前，top_k=1 只留一条 |
| 通知后全量重建 | `test_invalidation_triggers_full_rebuild_on_next_search` | 改 Mock source，调用 seam，再查到 new；list_chunks 总计两次 |
| 无缓存通知 | `test_invalidation_is_no_op_when_index_does_not_exist` | 不制造 dirty entry |

每个 `setUp()` 清空三份类级容器再创建 store/retriever。否则上个测试的缓存会跨实例存活，让本应 lazy build 的场景误用旧表。可类比 `beforeEach` 清空 static Maps 并注入 typed mock。

### 12.3 这些测试没有证明什么？

这些是 **MOCKED dependency 的单元行为证据**：分词/索引算法真实执行，存储被替代。重建测试直接调用通知函数，没有发真实 upload HTTP request，也没有真实 Chroma lifecycle、provider 调用或前端。因此 Phase 6 单测通过不等于 upload-to-query E2E 通过。

它们还没有证明所有 Unicode 汉字、emoji、accented Latin 行为；没有 property-based test、并发重建/失效验证、多 store 同名隔离验证或同分次序保证。确定性示例不是统计检索质量 benchmark，复杂度推导不是性能 SLA。

**Verification references：**原收官时 6 个 tokenizer + 7 个 retriever methods 的精确命令和 Gate 结果见附录 B；后续真实应用/API 链路验证与替代依赖的区分见附录 C。当前 `test_qa.py` 已包含后续阶段测试，不能再说“运行全文件就是 13 个测试”。本次文档迁移不重跑 provider 或接受新的 runtime 验收结论。

## 13. 当前设计的局限是什么？

### 13.1 当前限制（实现事实）

关键词索引只在内存中、按 collection 全量重建，无增量更新、磁盘持久化或缓存淘汰策略。类级 key 不包含 store identity，多 worker 不共享通知，双表没有并发锁。同分 tie-breaker 未定义。

文本规则只覆盖基本 CJK 区和 ASCII 英文数字，不保留跨语言原文位置。没有 jieba、stop-word removal、BM25、TF-IDF 或 position-aware matching。修改分词规则会改变索引 key、命中结果和评分分母，不能只替换函数而忽略旧缓存。

### 13.2 未来改进（尚未实现）

| 方向 | 重新评估条件 | 当前范围 |
|---|---|---|
| incremental / persisted index | 全量重建成本超出可接受范围 | v1 明确不做 |
| BM25 / TF-IDF / 位置感知匹配 | 质量评测证明收益 | v1 明确不做 |
| jieba 或其他词典分词 | 实际语料需要词级规则且能接受契约变化 | 当前未引入，仅设计比较 |
| 扩大中文 Unicode 范围 | 出现真实语料缺口 | 非当前分词契约 |
| 保留跨语言 source order | 消费者需要位置语义 | 非当前分词契约 |
| store identity 纳入缓存 key | 多 store/tenant 场景 | 尚未实现 |
| 同分确定性规则 | 需要稳定回放或翻页 | 尚未定义 |

### 13.3 尚未测量（Unknown）

没有 corpus-level 索引体积、重建延迟、并发吞吐或大规模召回质量数据；没有实验表明 bigram 优于 jieba、coverage 优于 BM25，或固定融合权重最优。后续小规模真实问答验证填补了链路证据，不填补这些质量与规模问题。原文“真实上传到查询仍待后续验收”是历史延期项，其后来补证状态放在附录 C，不再冒充当前缺口。

## 14. 如果规模扩大，我会怎么重新思考？

先测量当前设计最直接的成本，再决定是否改架构。以下是根据循环与数据结构推导的复杂度（Inferred），不是实测 benchmark。

| 路径 | 成本推导 | 优先观察的实际指标 |
|---|---|---|
| 分词 | 长度 n：两次 regex 扫描、窗口、过滤去重约 O(n)；原始 token list 与临时 dict 空间 O(n) | 长 query / 长 chunk 的 CPU 和分配量 |
| 全量 build | corpus 总字符量 C：分词与 posting 注册约 O(C)，另有读存储和逐 chunk 开销 | cold/dirty 首次查询耗时、list_chunks 读取成本 |
| 已有索引查询 | q 个 query tokens，posting 大小和 P：计数约 O(q+P)；m 个候选排序 O(m log m) | 高频 token 的候选量、排序耗时 |
| 重建峰值 | 旧/新快照及存储读取记录可同时占内存 | 峰值内存、驻留 collection 数量 |

评审的 v1 前提是本地单进程，未给可承诺的容量上限。若 query 长度扩大，先检查请求约束和分词成本；若 corpus 扩大，先量重建耗时和双快照峰值，再考虑后台重建、增量或持久化索引。后台重建本身还需要定义查询读哪个版本，不能当作已解决一致性的开关。

若部署先变成多 worker，优先问题可能不是单次查询速度，而是失效通知不可见；若要支持多个 store，必须先解决 namespace；若误召回/漏召回成为主要问题，先建立评测集再比较分词和评分。原评审的 10x query、100x/1000x corpus 是压力讨论，不是验证过的运行容量。

## 15. 我现在应该能够回答这些问题

不看代码先用自己的话解释，必要时画图；答案不要只复述函数名。

1. 关键词检索和向量检索分别匹配什么？为什么只靠任意一路都有盲区？
2. token、倒排索引和 posting set 分别是什么？能用 Python/FastAPI/RAG 两个 chunk 画出来吗？
3. 中文为什么不能只按空格切？n 个连续汉字为什么产生 n−1 个 bigram？为什么“机器，学习”不产生“器学”？
4. `Python3` 与 `Python-3` 输出有何不同？数字 3 在哪一步被丢弃？“机器Python学习”的实际输出顺序是什么？
5. `dict.fromkeys` 同时满足哪两个契约？若建索引侧 lowercase、查询侧不 lowercase，会怎样？
6. `_indexes`、`_chunks`、`_dirty_collections` 分别记住什么？哪些状态属于类，哪些属于实例？测试为什么要 clear？
7. 为什么关键词索引是派生状态？权威数据源是什么？正常 absent-index invalidation 为什么 no-op？
8. 从上传提交到新内容可检索，中间经过哪些步骤？正常通知失败后当前如何恢复？
9. 为什么先局部建表再发布？防住哪种失败，又为何不等于并发下的原子事务？
10. 对“机器学习算法”查询，只有“机器学习”的 chunk 为什么得 0.6？重复词会加分吗？1.0 为什么不是概率？
11. 关键词候选交给融合时带哪些字段？为何关键词得 0.6 的候选仍可能被最终过滤？
12. 为什么当前没有直接采用 BM25、jieba 或增量索引？哪些理由有规格/评审记录，哪些收益仍未知？
13. Phase 6 的单测证明了什么，没证明什么？为什么 lifecycle PASS 当时不等于真实 upload-to-query E2E PASS？
14. 后续真实验证补到了哪一层？如何区分原始历史边界、当前实现、REAL / MOCKED / SUBSTITUTED 与尚未观测的行为？
15. 若重建延迟、数据量、worker 数或 store 数增加，分别应先检查什么？为什么不能承诺同分稳定或无限扩展？

**动手练习（在 REPL 或测试替身中，不修改产品代码）：**先预测再调用 `tokenize("")`、`tokenize("A 中 1")`、`tokenize("Python-3")`、`tokenize("机器Python学习")`、`tokenize("机器，机器")`；逐项指出是 regex、segment、长度过滤还是 stable dedup 决定结果。

再遮住第 6 节，手算两个 chunk 的 posting sets、matched_count、score 和 `top_k=1`；最后用 `KeywordRetriever` + Mock 验证。能解释完整数据流后，再进入 Interview Guide；本章不提供背诵话术。

## 16. 一页复习

| 要点 | 应恢复出的心智模型 |
|---|---|
| 目标 | 给 RAG 提供词面匹配的候选，与语义检索互补 |
| 比较规则 | ASCII 英文数字连续串小写；基本 CJK 连续段 overlapping bigram；长度≥2；稳定去重 |
| 核心数据流 | `list_chunks → tokenize(content) → postings`；`tokenize(query) → lookup → count → coverage → DESC → top_k` |
| 三份状态 | `_indexes` 找 ID；`_chunks` 补记录；`_dirty_collections` 要求刷新；同进程类级共享 |
| 生命周期 | 持久化 chunks 是权威来源；cold/dirty 在查询时全量 build；写路径通知，当前支持普通失效调用失败后强制 dirty |
| 分数 | matched unique query tokens / total unique query tokens；1.0 不等于概率、短语匹配或最终被采用 |
| 主要取舍 | 零分词依赖、规则直观、索引可重建；代价是首查延迟、内存和较粗的相关性信号 |
| 一致性限制 | 局部构建后顺序发布，不是并发原子发布；无多 worker 通知；无 store namespace；同分顺序未定义 |
| 验证边界 | 原始 6+7 单测：真实算法 + Mock 存储；后续 API/真实依赖证据单独记账；不是规模/质量 benchmark |
| 后续连接 | `HybridRetriever` 按 ID 做固定 0.3/0.7 融合、阈值过滤、Top-K；QAService 再组织 context/history/LLM/sources |

## Appendix A — Source Code Map

按概念读代码，不必按任务顺序读。下列以当前符号定位，避免把原收官时的行号当成当前行号。

| 概念 | 文件 | Class / Function | 为什么重要 |
|---|---|---|---|
| 共享文本规则 | [qa.py](../../backend/app/services/qa.py) | `_ALPHANUMERIC_PATTERN`、`_CHINESE_PATTERN`、`tokenize()` | 文档和查询进入同一 token space |
| 内存索引与记录表 | [qa.py](../../backend/app/services/qa.py) | `KeywordRetriever._build_index()` | 公开接口读取、局部 build、双表发布 |
| 覆盖率和排序 | [qa.py](../../backend/app/services/qa.py) | `KeywordRetriever.keyword_search()` | posting lookup、计数、补记录和 top_k |
| 失效状态 | [qa.py](../../backend/app/services/qa.py) | `invalidate()`、`mark_dirty()` | 已有缓存正常标脏与强制标脏的区别 |
| 提交后缓存维护 | [keyword_index.py](../../backend/app/services/keyword_index.py) | `invalidate_keyword_index()` | 通知共享状态；当前失败恢复与日志 |
| 权威 chunk 读取 | [vector_store.py](../../backend/app/core/vector_store.py) | `VectorStore.list_chunks()`、`ChromaVectorStore.list_chunks()`、`ChunkRecord` | 不穿透 Chroma 私有 API；文本/元数据到记录 |
| 上传后的通知 | [upload.py](../../backend/app/api/upload.py) | `upload_file()` | 持久化提交后维护缓存 |
| 知识库变更通知 | [collections.py](../../backend/app/api/collections.py) | `rename_collection()`、`delete_collection()` | 重命名旧/新名字与删除后的索引失效 |
| 文件删除通知 | [files.py](../../backend/app/api/files.py) | `delete_file()` | 文件级持久化删除后使快照过期 |
| 后续检索消费 | [qa.py](../../backend/app/services/qa.py) | `VectorRetriever`、`HybridRetriever`、`retrieve()` | 分数映射、融合、组装入口与 empty/missing 边界 |
| 后续问答与 HTTP | [qa.py](../../backend/app/services/qa.py)、[query.py](../../backend/app/api/query.py) | `QAService.answer()`、`query()` | 直接消费 hybrid；HTTP 请求/响应适配 |
| 原始行为验证 | [test_qa.py](../../backend/tests/test_qa.py) | `TokenizeTests`、`KeywordRetrieverTests` | exact examples、6+7 个单元方法及测试隔离 |
| 后续提交后失效回归 | [verify_t0503_rollback.py](../../backend/scripts/verify_t0503_rollback.py) | V11 场景 | 故障注入后持久化成功保持、下一次查询恢复 |
| 后续真实检索验收 | [T1202 README](../verification/T1202/README.md) | AC ledger 与关联 runner/logs | 真实链路、替代依赖、未观测状态分别记账 |

Python/TS 基础可回看 [前端开发者的 Python 桥梁](./python-for-frontend-dev.md)。完整 ADR、维护性和规模讨论在 [Phase 6 Engineering Review](./engineering-review/phase-06-engineering-review.md)；它也保留自己的历史时点，本文迁移不修改该评审。

## Appendix B — Engineering Traceability

### B.1 实现与规格坐标

| 人类可读的能力 | 工程坐标 | 规格与验收关联 |
|---|---|---|
| 共享分词 | [T0601](../TASKS.md#t0601--query-tokenizer) — DONE | [F009](../SPEC.md#f009-keyword-retrieval) Detail：中文/英文数字、小写、最小长度、exact examples；Determine AC-F009-01～04 的分词部分 |
| 倒排表、生命周期、覆盖率排序 | [T0602](../TASKS.md#t0602--inverted-index--keyword-search) — DONE | F009 index/lifecycle/data source/retrieval flow/formula；AC-F009-01～05；当前条目另含提交后失效恢复 |
| 全量 chunk 读取 | T0108 | VectorStore public `list_chunks()`；F008 / AC-F008-03 私有属性隔离 |
| 既有写操作通知入口 | Phase 4/5：T0402、T0403、T0502；后续文件删除 T0903 | upload / rename / delete 调用 shared invalidation seam |
| 向量适配、融合、统一入口 | T0701 / T0702 / T0703 | F010 / F011；详见 [Phase 7 Learning](./phase-07-vector-retrieval.md) |
| 上下文、历史、LLM、问答、HTTP | T0801–T0805 | [Phase 8 Learning](./phase-08-rag-qa.md)，不属于原 Phase 6 完成范围 |
| 真实检索/问答验收 | T1202；最终审计 T1204 | [检索证据](../verification/T1202/README.md)、[最终验收](../verification/T1204/README.md) |

T0601 无存储依赖（pure function）；T0602 依赖 T0601 与 T0108。学习顺序无需记住这串 ID，工程追溯时再用它们定位。

### B.2 原始验收映射与精确历史结果

**2026-08-27 的历史证据，未作为本次重跑结果：**

| 验收项 | 原始状态演进 | 对应行为 |
|---|---|---|
| SPEC 三组 query 示例、lowercase、单字符过滤 | T0601 PASS | exact list equality；另加 punctuation / stable dedup 边界 |
| AC-F009-01 | T0601 完整检索 DEFERRED → T0602 unit PASS | 中文全命中 1.0，同时验证 lazy build |
| AC-F009-02 | T0601 DEFERRED → T0602 unit PASS | 无匹配 `[]` |
| AC-F009-03 | T0601 DEFERRED → T0602 unit PASS | 3/5 = 0.6 |
| AC-F009-04 | T0601 完整检索 DEFERRED → T0602 unit PASS | python / 编程均命中，1.0 |
| AC-F009-05 | PASS（Phase 6 scope）；literal E2E DEFERRED TO PHASE 12/T1202 | Mock source 更新 + 直接 seam → dirty → next search rebuild → new searchable |
| 非 AC 的补充行为 | T0602 PASS | 分数降序 + top_k；无缓存 invalidate no-op |

T0601 checkpoint 实际命令为 `python -m unittest tests.test_qa -v`，结果 **Ran 6 test methods / OK**。加入检索器后，2026-08-27 Phase Learning Review 重新执行同一命令，结果 **13/13 PASS**，其中 tokenizer 6 个、KeywordRetriever 7 个。原稿“当前 suite 13 个”指当时，不能用于今天已经扩展的全文件。

[Phase 6 Gate Review（工程评审第 10 节）](./engineering-review/phase-06-engineering-review.md#10-phase-6-gate-review2026-08-27) 裁定 **PHASE_6_PASS**：exact tokenizer、public-interface build、lazy/dirty rebuild、score/sort/top_k、mutation seam 代码路径 + unit lifecycle 均 PASS；真实 HTTP/Chroma E2E 仍明确延期。

| 历史 Gate 检查 | 精确记录 |
|---|---|
| Focused suite | `python -m unittest tests.test_qa -v` → 13/13 PASS |
| Discovered regression | `python -m unittest discover -s tests -v` → 13/13 PASS；当时仓库 tests 仅此 suite |
| Syntax/import compilation | `python -m compileall -q app tests` → PASS |
| Diff hygiene | `git diff --check` → PASS；实现 diff 未改 SPEC、未引入 dependency 或 Phase 7 代码 |
| black / ruff | NOT AVAILABLE：当时环境/requirements 未提供，不算 Gate failure，也未为审查新增依赖 |

**勘误边界：**工程评审记录同日独立提交 `33e0bdb`（15:05，Gate 之前）把 SPEC “Python机器学习”示例的 6 tokens 修正为 4 tokens，与 TASKS 同步。这是示例勘误；上表“未修改 SPEC”指实现 diff，不抹去这次独立修正。本次迁移也不修改 SPEC。

多进程通知、并发锁、同分排序、基本 CJK 范围、benchmark 和当时的 module docstring 债务是 non-blocking findings，并未被 Gate 判作已解决。完整结论仍以原工程评审为准。

### B.3 Learning / Interview 资产边界

Phase 6 的 T0601 + T0602 Learning Pass 与 Phase Learning Review 于 2026-08-27 完成。原文任务候选已筛选、去重并晋升到 [Interview Guide 的 Phase 6 深度章](./interview-notes/dx-rag-interview-guide.md)，本文只保存来源，不复制 30 秒、1–2 分钟话术或高频追问答案。

#### T0601 Interview Candidates

> Candidate source — Phase Learning Review 已筛选并晋升“shared tokenizer contract / stable dedup / bigram 取舍”到累计 Interview Guide 的 Phase 6 深度章；这里保留最初候选作为学习来源，不复制完整回答。

- **Technical Point**: 零依赖 mixed-language tokenizer：英文/数字 run + 中文 overlapping bigram。
- **Engineering Question**: 为什么 query 与 document 必须复用同一 tokenizer？
- **Candidate Question**: dict.fromkeys 与 set 都能去重，为什么这里选择前者？
- **STAR Candidate**: 无；本 Task 没有形成重大闭环工程事件。

#### T0602 Interview Candidates

> Candidate source — Phase Learning Review 已筛选并晋升“inverted index / lazy-dirty lifecycle / 双表 snapshot / shared cache 边界”到累计 Interview Guide 的 Phase 6 深度章；这里保留最初候选作为学习来源，不复制完整回答。

- **Technical Point**: per-collection in-memory inverted index + lazy full rebuild。
- **Engineering Question**: 为什么 invalidation 只标 dirty，不立即重建？
- **Candidate Question**: 为什么同时缓存 _indexes 和 _chunks？
- **Candidate Question**: class-level cache 给 seam 带来什么便利，又引入什么隔离风险？
- **STAR Candidate**: 无；本 Task 没有重大 incident / conflict 闭环。

---

本 Phase 原记录没有真实 incident、SPEC conflict 或 production-like failure investigation，不虚构 STAR；技术问题和工程问答的依据是代码与测试。后续故障注入也不追记成 Phase 6 的生产事故。

## Appendix C — Historical / Evidence Notes

### C.1 原文历史 checkpoints（保留当时结论）

以下逐段保留原稿历史更新。其中“尚未”“Future”“仍待”均限定于段内日期，不代表当前实现缺失。后续状态补证见 C.2；不会倒推改写 Phase 6 Gate。

> **Phase 6 Learning Review 收官（2026-08-27）**：T0601 tokenizer + T0602 inverted index/search 已 consolidation 为一个“共享 normalization contract → derived snapshot → dirty/full rebuild → normalized coverage ranking”的统一心智模型。Phase Gate Review 已裁定 PHASE_6_PASS，Interview Candidates 已筛选晋升到项目级 Interview Guide；真实 upload-to-search E2E 仍归 Phase 12。本段记录的是当时的历史 checkpoint。
>
> **后续状态（T0701 Learning Pass，2026-08-28）**：Phase 6 收官时尚未启动 Phase 7；之后 T0701 已在 `qa.py` 增加 `VectorRetriever`，其 query embedding、`similarity_score → vector_score` 映射与 expanded recall 见 [Phase 7 Technical Learning](./phase-07-vector-retrieval.md)。
>
> **后续状态（T0702 Learning Pass，2026-08-31）**：Phase 7 已在 `qa.py` 增加 `HybridRetriever`，按 `chunk_id` 做 0.3/0.7 weighted fusion、`MIN_RELEVANCE_SCORE` filter 与最终 Top-K；当时 T0703 unified wiring、真实 upload-to-search E2E 与 QA API 仍为 Future。本段保留 T0702 checkpoint 的历史边界，不把 keyword branch 的完成误写成完整 QA 完成。
>
> **后续状态（T0703 Learning Pass，2026-08-31）**：T0703 已在 `qa.py` 提供 `retrieve(query, collection, top_k)` facade：创建 concrete `ChromaVectorStore`，先做 empty-collection preflight，非空时把同一个 store 注入 Keyword/Vector/Hybrid retrievers，并让 missing-collection 异常自然向上传播。此 facade 的 wiring tests 是 patched composition boundary；真实 upload → ChromaDB → query E2E、QA API 与 context/LLM 仍属于后续范围。本段只同步后续事实，不改写 Phase 6 原有 Gate/Learning Review 结论。
>
> **后续状态（T0803 Learning Pass，2026-09-02）**：**在该 T0803 checkpoint**，`qa.py` 已增加 DeepSeek client、System Prompt、message assembly、bounded retry 与错误映射，但尚未把 keyword/retrieval 结果接入 QA orchestration；本段保留该历史边界，不改写 Phase 6 的历史收官结论。
>
> **后续状态（T0804 Learning Pass，2026-09-02）**：T0804 已在同一 `qa.py` 增加 `QAService.answer()`，直接消费 `HybridRetriever` 的结果并串起 context/history、LLM 与 sources；它不是 T0703 facade 的复用，也不是 HTTP endpoint。真实 upload → ChromaDB → query → provider E2E 与 `/api/query` 仍属后续范围。
>
> **后续状态（T0805 Learning Pass，2026-09-02）**：T0805 已增加 `POST /api/query` 的 request validation、collection existence check、`QAService` delegation、`QueryResponse` 与统一错误 envelope，并以 10 个 route-level Mocked tests 验证 HTTP boundary。真实 provider/Chroma/upload → query E2E 与前端集成仍属后续范围；本段不改写 Phase 6 的历史收官结论。

### C.2 后续实现与证据补记（本次只核对，未重跑）

**当前代码与原精读差异：**原文的 `qa.py:1–82`、`tokenize:13–21`、`KeywordRetriever:24–82` 和测试行号都是早期位置。后续同文件增加向量、融合和问答代码，本文改用文件 + 符号地图定位。原文指出 qa.py docstring 仅写 “Query tokenization”、test_qa.py 仅写 T0601 的维护债，历史判断保留；当前两者已分别描述 “Keyword and vector retrieval services.” / “Tests for the retrieval services.”，不能继续说这项旧文案原封不动。

原 `invalidate()` 直接向 set 添加 collection，原 seam 只做函数内 import 后转发。当前 `invalidate()` 委托 `mark_dirty()`，seam 增加捕获普通失效异常后的强制 dirty + 日志。当前 [SPEC F009](../SPEC.md#f009-keyword-retrieval) 与 [TASKS](../TASKS.md) 已记录 post-commit cache maintenance；这是后续契约/实现事实，不是本次重设计。

原工程评审 Pending #34 的历史裁决是：Phase 4 曾问 invalidate 失败是否能映射 `RENAME_FAILED`；当时仅有内存 set 标脏、没有业务失败分支，因此该映射在当时实现下不可达，真失败 raise 保留为防御条款。当前不能拿这个旧判断覆盖后来新增的失效恢复契约。后续 [上传回滚验证 V11](../../backend/scripts/verify_t0503_rollback.py) 对正常 invalidation 故障做注入，检查提交成功保持和下一次查询恢复；这是受控故障验证，不是线上事故。

**验证强度分开记账：**

| 时点 / 证据 | 真实部分与替代部分 | 可以得出的结论 |
|---|---|---|
| Phase 6 unit checkpoint | REAL tokenizer/index 算法 + MOCKED `VectorStore` | 定义的单元行为；真实 upload-to-search 当时 DEFERRED |
| 后续 retrieval facade tests | patched composition，组装依赖被替代 | same-store wiring、空集合与异常传播；不等于真实 Chroma E2E |
| 后续 QA route tests | 10 个 route-level MOCKED tests | HTTP validation/delegation/response/error boundary；不是 provider 或浏览器集成 |
| 后续确定性应用验证 | REAL app / 临时存储，SUBSTITUTED embedding 或 provider transport；精确分支分数可用 fixtures | 受控契约与恢复路径；不能标为 live provider |
| [T1202 最终验收](../verification/T1202/README.md)，2026-09-07 | REAL TestClient upload/query、解析切分、local BGE 512d、临时 Chroma、关键词/向量/融合、DeepSeek SDK 与远端响应 | 受控应用/API E2E，补齐真实新上传后缓存重建证据；不是 browser/TCP/CORS/frontend E2E |

T1202 的 AC ledger 明确列出 F009-01 中文 1.0、F009-02 空结果、F009-03 0.6、F009-04 混合 1.0、F009-05 真实新增上传后缓存重建的 PASS。这是后来增加的独立证据，不把原 7 个 Mock 检索测试改称 E2E。

该验收的既有 LIVE checks 为 **70/70 PASS**；focused QA/query 为 **60/60**，deterministic matrix 为 **46/46**，额外 failure-contract 为 **15/15**。计数是 checks/test methods 的各自口径，不是 AC 个数。历史 live log 保留 **exit 2**：它来自后来移除的额外未观测状态 gate，不是失败断言；该审计没有重新请求 provider。

真实 DeepSeek 429/5xx/403 仍为 **NOT_OBSERVED**。确定性故障注入证明错误处理控制流，不能升级成真实 provider 响应；受控真实超时/连接错误也不是 provider 端事故。受控语料的实际答案与召回不构成广泛质量、性能或安全保证。

最终范围应查 [T1204 最终 README](../verification/T1204/README.md) 和 [Phase 12 Learning Review](./phase-12-learning-review.md)。旧 [T1204 审计稿](../T1204-SPEC-ACCEPTANCE-AUDIT.md) 中的 pre-live BLOCKED / NOT_AVAILABLE 是历史快照，不能用它推翻后续补证。同样，后续前端组件修复的 MOCKED API/hooks 证据不自动变成 browser upload E2E。

### C.3 迁移保留索引

原稿的 Task Learning、代码精读、数据流/复杂度、架构与决策表已分别归入正文概念、实现、状态、生命周期、设计和规模章节；原始测试场景及方法数归入第 12 节与附录 B；13 道原自测的技术点合入 15 道主动回忆题并保留 REPL/手算练习；Quick Review 改为一页复习。候选来源与所有后续 checkpoint 移到附录，没有删除工程事实或延期记录。

重复的任务状态导语、同义摘要和已失效的行号定位合并或替换；旧 docstring / seam 代码不再作为当前代码展示，其差异在 C.2 明示。正文无需识别 Task/Gate ID 即可理解，附录保留工程坐标与历史强度。这次只迁移学习文档，不重新裁定 Gate，也不修改其他学习、评审或验收材料。
