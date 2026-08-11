---
name: git-save-push
description: |
  存档所有本地变更并推送到 GitHub 远程仓库。当用户说"存档"、"推送"、"存档并推送"、
  "save"、"push"、"commit and push"、"save and push"，或任何要求保存代码变更并推送
  到远程仓库的指令时，触发此技能。即使用户只说"推送"，也默认执行 stage → commit → push 全流程。
---

# Git 存档并推送

将所有本地变更（修改、新增、删除）提交并推送到 GitHub。

## 执行流程

### 1. 检查状态

```bash
git status --short
```

- 如果没有任何输出（工作区干净），提示 "Nothing to commit — working tree is clean." 并停止。
- 如果有变更，记住哪些文件被修改/新增/删除，用于编写 commit message。

### 2. 查看变更量

```bash
git diff --stat
```

通过 stat 了解变更幅度，辅助写出准确的 commit message。

### 3. 暂存所有变更

```bash
git add -A
```

### 4. 提交

Commit message 用**中文**编写，遵循项目现有风格：

- 一句话概括本次变更的内容（做了什么，不是怎么做的）
- 具体明确，避免模糊描述
- 格式参考 `git log --oneline -3`

**必须**在 commit message 末尾追加：
```
Co-Authored-By: Claude <noreply@anthropic.com>
```

示例：
```
git commit -m "Add backend config module and error handlers

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 5. 推送

```bash
git push
```

### 6. 报告

推送完成后，简洁报告：

```
已存档并推送 ✅

| 提交 | 变更 |
|------|------|
| <short-hash> | +N / -N 行，N 个文件 |
```

## 边界处理

- **无远程仓库**: `git remote -v` 为空时，提示用户先配置 remote。
- **非 Git 仓库**: 提示 "当前目录不是 Git 仓库"。
- **存在冲突**: `git status` 显示 `UU` 文件时，停止并提示先解决冲突。**禁止**强行提交。
- **Push 被拒绝** (non-fast-forward): 提示远程有更新的提交，建议先 `git pull --rebase`。**禁止** force push。
- **工作区干净**: 直接告知无需提交，优雅退出。
