# Benchmark 历史审阅归档

已按 Human「按照你的推荐做法执行」于 2026-09-14 归档五个历史目录。74 个非缓存文件保留原始字节和仓库相对路径，逐条 SHA-256 与 ZIP CRC 均核验通过。

- [历史材料 ZIP](benchmark-review-history-2026-09-14.zip)：584,825 bytes，原文件共 10,741,626 bytes。
- [逐文件清单和 SHA-256](benchmark-review-history-2026-09-14.manifest.json)。ZIP SHA-256：`cefe852424318798d1c37b97eed46fed4aba41ea3d8b4dfcc43a86902c331629`。
- [当前正式数据集 1.0.0](../novatech-retrieval-benchmark-1.0.0/README.md)：完整保留，未删改其受 manifest 约束的证据副本。

永久删除原目录的操作被自动审批策略拒绝，返回“blocked by policy”，没有更具体说明。因此采用可恢复的替代整理：原目录已移到仓库内被 Git 忽略的 `tmp/benchmark-review-backup-2026-09-14/`。日常评估目录不再保留五个散落目录；原文件仍占用本地备份空间，未声称已永久删除或释放该空间。备份也包含两份未放入 ZIP 的可再生成 Python 缓存。

以下条目是历史目录的替代入口。旧路径在历史叙述、冻结证据和源码中可能仍以文本出现，表示归档前位置；不为整理目录而修改冻结文件或其 hash。

<a id="benchmark-candidate-0.1"></a>
## benchmark-candidate-0.1

33 个文件：候选问题、逐批审阅材料、原建议、等级与 coverage 决定和生成/核验脚本。

<a id="fact-split-draft-0.1"></a>
## fact-split-draft-0.1

9 个文件：核心事实、分组与 Dev/Test 草案、重叠审计及批准。

<a id="freeze-review-1.0.0-rc1"></a>
## freeze-review-1.0.0-rc1

24 个文件：正式冻结前的 RC 候选、证据副本、manifest 与核验脚本。获批 RC dataset/manifest 和必要证据仍完整保存在正式版本中。

<a id="semantic-dedup-review-0.1"></a>
## semantic-dedup-review-0.1

4 个文件：20 组语义去重对照与七批人工决定。

<a id="size-corpus-review-0.1"></a>
## size-corpus-review-0.1

4 个文件：规模差额、最终语料选择与 SC01/SC02 批准。

## 查看与恢复

日常查看历史材料时，可将 ZIP 解压到独立临时目录，ZIP 内路径以仓库根目录为基准。无需恢复这些材料即可运行正式版本 verify.py 或后续获授权的 Runner。

如要重跑历史生成/核验脚本，先核对 ZIP hash，确认五个原目录没有重新出现或产生新工作，再将压缩包解压到仓库根目录以恢复原路径；也可从本地备份恢复五个目录至 docs/v2/evaluation/。不要覆盖已有文件；若原路径已存在，应先比较差异。历史脚本可能依赖当时的上游文件和 hash，恢复不代表可以覆盖当前正式版本。

归档不修改产品、模型、Chroma、正式数据集或已作出的批准，不授权/执行 Benchmark。T2002 工具/测试和 T2003 预检、冒烟证据继续保留在原位置。
