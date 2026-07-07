# Codex 线程索引

本文件只记录对新项目仍有用的旧 Codex 线程线索。原始聊天不迁移进仓库；长期事实必须沉淀到 `AGENTS.md`、`QUICKSTART.md`、`docs/上下文交接.md`、`quality-workbench/`、`.agents/skills/research-advisor/` 或测试里。

## 使用边界

- 旧线程只能解释“为什么曾经这样改”，不能作为当前项目状态。
- 旧线程里的自我总结需要用 Git diff、文件内容和验证命令复核。
- 如果线程结论和当前文件冲突，按当前文件执行；必要时把冲突写进新的交接文档。
- 不要把旧线程里的账号、API、Docker、缓存或本机路径配置复制到新仓库。

## 已知相关线程

| 线程 ID | 标题 | 旧工作目录 | 作用 | 迁移处理 |
|:---|:---|:---|:---|:---|
| `019f3ad3-81b4-7492-8ed8-42e794ce979f` | `重构 workbench 支撑文档` | `V:\Default\Desktop\当前学习内容\寻找导师的邮件\李自翔\量子蒙特卡洛\pilot-test` | 记录 `quality-workbench/支撑方法/` 重构过程，尤其是 S4 可视化方法反复失败和最后一次文档修订。 | 不迁移原始聊天；把可复用结论写入本目录的迁移交接和失败复盘。 |

## 关联提交

旧线程最后相关提交在旧仓库里是：

```text
dd5e9be3 docs: ground visualization method in reviewable cases
```

过滤历史后，新仓库对应提交是：

```text
b7bdbb6 docs: ground visualization method in reviewable cases
```

提交哈希不同是正常结果。`git filter-repo` 把旧仓库子目录提升为新仓库根目录，提交对象会重新计算。

## 后续维护

如果以后需要把更多旧线程变成项目事实，按这个流程做：

1. 先找到线程 ID、标题、旧工作目录和相关提交。
2. 只摘录能被文件或 diff 验证的结论。
3. 把长期规则放回对应归属，不把聊天摘要堆进本文件。
4. 对失败教训只写“触发条件、失败机制、以后怎么检查”，不要写成泛泛的反思。
