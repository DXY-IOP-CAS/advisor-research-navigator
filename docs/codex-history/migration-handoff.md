# advisor-research-navigator 迁移交接

日期：2026-07-07

## 迁移结果

新项目路径：

```text
V:\Default\Desktop\advisor-research-navigator
```

旧项目工作目录：

```text
V:\Default\Desktop\当前学习内容\寻找导师的邮件\李自翔\量子蒙特卡洛\pilot-test
```

旧 Git 根目录实际是：

```text
V:\Default\Desktop\当前学习内容
```

迁移后，项目根目录已经是 `AGENTS.md`、`QUICKSTART.md`、`quality-workbench/`、`.claude/skills/`、`src/`、`tests/` 这一层，不再嵌在旧中文路径下面。

## Git 历史

迁移使用的是“克隆副本后过滤历史”，没有重写旧仓库：

```text
git clone --no-local "V:\Default\Desktop\当前学习内容" "V:\Default\Desktop\advisor-research-navigator"
git filter-repo --path "寻找导师的邮件/李自翔/量子蒙特卡洛/pilot-test/" --path-rename "寻找导师的邮件/李自翔/量子蒙特卡洛/pilot-test/:"
```

`git subtree split` 曾因中文路径编码断言失败而停止，旧仓库没有因此产生脏状态。后续改用 `git filter-repo`，只在新克隆里重写历史。

当前新仓库分支：

```text
main
```

历史保留结果：

| 项 | 结果 |
|:---|:---|
| 旧工作分支 | `codex/e2e-quality-redesign` |
| 新默认分支 | `main` |
| 旧最新提交 | `dd5e9be3 docs: ground visualization method in reviewable cases` |
| 新最新提交 | `b7bdbb6 docs: ground visualization method in reviewable cases` |
| 新 `main` 提交数 | 477 |
| 旧 `main` 指针 | 保留为 `archive/source-main-before-migration` |

提交哈希会变化，因为过滤历史会把 `pilot-test/` 子目录提升为仓库根目录。判断迁移是否成功时，优先看提交信息、文件内容和提交数，不要要求新旧哈希一致。

## 已迁移内容

已随 Git 历史进入新仓库的内容包括：

- 根入口：`AGENTS.md`、`CLAUDE.md`、`QUICKSTART.md`
- 项目文档：`docs/`
- 当前设计工作台：`quality-workbench/`
- 项目 skill：`.claude/skills/research-advisor/`
- 阶段 1 脚本和文档：`src/phase1/`
- 测试：`tests/` 和 `.claude/skills/research-advisor/tests/`
- 当前输出样本：`output/`
- 已跟踪的存档目录：`archive/`

## 没有迁移或没有纳入 Git 的内容

这些旧目录存在于旧工作区，但没有作为新仓库的项目事实搬入：

| 旧内容 | 处理 |
|:---|:---|
| `.codex/config.toml` | 不迁移。它是本机 Codex 配置，可能含旧路径或账号环境假设。 |
| `.vscode/` | 不迁移。它是本机编辑器配置。 |
| `.tmp/` | 不迁移。它是临时目录。 |
| `.agents/skills/` | 不单独迁移。旧目录里它是指向 `.claude/skills/` 的 NTFS junction。 |
| `精髓转移/` | 暂不纳入 Git。它是被忽略的经验资料，若要继续使用，应先人工筛选，再改名放入合适的英文路径。 |

不要把这些本机内容直接复制进新仓库，尤其不要提交 `.codex/`、账号、令牌、API 配置或 Docker 相关状态。

## 新窗口启动方式

以后在 Codex 里继续这个项目时，先打开新路径：

```text
V:\Default\Desktop\advisor-research-navigator
```

新窗口按以下顺序读：

1. `AGENTS.md`
2. `QUICKSTART.md`
3. `docs/上下文交接.md`
4. 当前任务相关的 `quality-workbench/`、`.claude/skills/research-advisor/` 或 `src/phase1/pipeline.md`
5. 需要理解迁移背景时，再读 `docs/codex-history/`

旧 Codex 对话仍留在 Codex 应用历史里，但它们绑定旧工作目录。新项目状态以新仓库文件、Git 日志、验证命令和人工审查为准。
