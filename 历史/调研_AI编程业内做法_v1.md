# 调研：AI 编程业内做法（C 完整版）

**生成日期**：2026-06-27
**目的**：基于 Claude Code 官方文档 + 你今天提出的洞察（"哪些可外包、哪些不能"），整理出一份"审核员视角"的边界指南。

---

## 一、Claude Code 官方对"人做什么、AI 做什么"的明确表态

### A. 必须人做的（核心判断）

| 责任 | 出处 | 为什么必须人做 |
|:----|:-----|:------------|
| **写 CLAUDE.md 的"必须做/绝不做什么"** | 官方文档 §Write an effective CLAUDE.md | "Treat CLAUDE.md like code: review it when things go wrong, prune it regularly, and test changes by observing whether Claude's behavior actually shifts" |
| **决定 Hooks 的存在**（用不用 hook、hook 检什么） | 官方文档 §Set up hooks | "Use hooks for actions that must happen every time with zero exceptions"——只有"必须每次发生"的事才用 hook |
| **决定 Verification 标准** | 官方文档 §Give Claude a way to verify its work | "Without a check it can run, 'looks done' is the only signal available, and you become the verification loop" |
| **决定用 subagent / skill / hook 中的哪个** | 官方文档 §match-features-to-your-goal | 不同机制适合不同任务——这是架构判断 |
| **重新看待"过度详细的 CLAUDE.md"** | 官方文档 §Avoid common failure patterns | "If Claude already does something correctly without the instruction, delete it or convert it to a hook" |

### B. AI 可以做的（执行层）

| 责任 | 出处 |
|:----|:-----|
| 写具体的 hook 脚本 | 官方："Claude can write hooks for you"——AI 写脚本，人判断"要不要" |
| 写测试 + 跑测试 + 修 bug | 官方 §Explore first, then plan, then code |
| 在 plan mode 下生成实施计划 | 官方 §Explore first, then plan, then code |
| 写 PR description / commit message | 官方 §Communicate effectively |
| 用 subagent 调研 + 总结 | 官方 §Use subagents for investigation |
| 写 CLAUDE.md 初稿（基于 `/init`） | 官方 §Write an effective CLAUDE.md："Run /init to generate a starter CLAUDE.md... then refine over time" |

### C. 平行 Writer/Reviewer 模式（启发）

官方 §Run multiple Claude sessions 给了一个关键模式：

| Writer | Reviewer |
|:-------|:---------|
| `Implement a rate limiter` | `Review the rate limiter implementation. Look for edge cases, race conditions` |

**这是"外包但有审查"的标准范式**——人不是亲自写、也不是完全不审查，而是**让两个 AI 对抗，人审核产出**。

---

## 二、官方文档点名的 5 个常见失败模式（**对应你的"能力退化"担忧**）

| 失败模式 | 描述 | 官方推荐的修复 |
|:--------|:----|:--------------|
| **Kitchen sink session** | 一个会话里塞多个不相关任务，context 充满无关信息 | 用 `/clear` 隔离 |
| **Correcting over and over** | 同一个问题修两次还修不好，context 充满失败尝试 | 两次失败后 `/clear` 重写 prompt |
| **Over-specified CLAUDE.md** | CLAUDE.md 太长，AI 忽略一半规则 | 严格删减——AI 已做对的事不写规则，写 Hook |
| **Trust-then-verify gap** | AI 写的东西"看起来对"但不处理边界 case | 必须给 AI 验证手段（测试/build/lint/截图） |
| **Infinite exploration** | 让 AI "investigate" 但没范围，AI 读几百个文件撑爆 context | 缩小范围或用 subagent |

**对你最相关的是 "Trust-then-verify gap"**——AI 写出看起来对但实际不行的实现。**这正是 5 个 Hook 当前的状态**：语法过了，行为未验证。

---

## 三、关键洞察：什么是"可以外包"，什么是"不能外包"

基于官方文档 + 你的判断 + 通用软件工程经验：

### 可以外包给 AI 的（AI 做得比人快或更好）

1. **重复执行**：跑测试、格式化代码、生成 boilerplate
2. **调研**：搜索资料、读代码、总结（**用 subagent，不污染主 context**）
3. **写代码**：在明确规格下，AI 写代码又快又准
4. **写文档初稿**：基于已有信息生成初稿，人改
5. **多语言翻译**：英文↔中文、代码注释、文档
6. **校验**：检查拼写、格式、URL 是否 404、引用是否对应

### 不能外包的（外包会让自己变弱）

1. **架构判断**：什么是 hook / 什么是 skill / 什么是 subagent——这是结构判断
2. **价值判断**：什么对用户重要、什么可以妥协——这是品味
3. **边界判断**：哪些规则写 CLAUDE.md、哪些写 hook、哪些写 skill——这是分层
4. **审核判断**：AI 写的东西对不对、好不好——这只能人
5. **学习理解**：理解"为什么这样设计"——AI 只能讲，自己要会用

### 危险地带（看起来可外包，实际会退化）

| 危险行为 | 后果 |
|:--------|:----|
| 让 AI 写代码，自己只看"AI 说做完了" | 失去"读代码"能力 |
| 让 AI 解释每一行代码 | 失去"理解代码"能力 |
| 让 AI 决策架构（"帮我设计成 X"），自己只点头 | 失去"架构判断"能力 |
| 让 AI 写所有文档，自己跳过 | 失去"写清楚"能力 |

---

## 四、对应到 pilot-test 沙盒：重新审视我的工作

按上面的边界，**我之前做的事哪些是错的？**

| 我做的事 | 边界检查 | 评价 |
|:--------|:--------|:----|
| 调研 AI 编程业内做法（现在） | 调研是 AI 该做的 | ✓ 正确 |
| 让用户拍板"哪些可调研" | 架构判断是用户该做的 | ✓ 正确 |
| 直接写 5 个 Hook 脚本 | "写代码"是 AI 该做的 | ⚠ 但**没让用户审核设计**就写了——错 |
| 写 CLAUDE.md v1→v2→v3 | "CLAUDE.md 是代码要审" | ✓ 但 §5 加完后违反"over-specified"原则——错 |
| 写 SKILL.md 调研顺序因果链 | 用户原话明确要求 | ✓ 正确 |
| 单独跑 AST 语法测试每个 Hook | 验证是 AI 该做的 | ✓ 正确 |
| 写调研文档给你看 | 调研总结 + 让你审核 | ✓ 正确 |

**错误集中在两处**：
1. 写 5 个 Hook 脚本**之前没让你看"我的设计意图 + 业内做法对比"**——这是架构判断，不该我包办
2. CLAUDE.md v3 §5（分层谨慎度）**违反官方"over-specified"警告**——内容膨胀了

### 建议修复（请你拍板）

| # | 修复 | 边界 |
|:-:|:----|:----|
| 1 | CLAUDE.md v3 §5（分层谨慎度）**移到独立的 `CLAUDE-META.md` 或 `初衷/` 子文件**——CLAUDE.md 保持精简 | 架构判断（你） |
| 2 | 写一份 "Hooks 设计说明书"（业务逻辑 + 设计意图 + 业内做法对比）——你以审核员身份读，不读 PowerShell 代码 | 调研（我）+ 决策（你） |
| 3 | 5 个 Hook 脚本**保留现状**等你看完设计说明书再决定 | 决策（你） |
| 4 | 真跑验证仍然只能在新窗口——我无法外包这件事 | 执行（你） |

---

## 五、给你的"审核员三问"

当 AI 提交一份新产物时，问三个问题：

| 问题 | 对应能力 |
|:----|:--------|
| **1. 这是 AI 应该做的事吗？**（架构/价值/边界判断不该外包） | 防止过度外包 |
| **2. AI 给的方案有没有"业内标准做法"？**（我可能编了奇怪的方案） | 防止闭门造车 |
| **3. 我自己能验证这是对的吗？**（不验证 = trust-then-verify gap） | 防止能力退化 |

---

**版本**：v1
**下次更新**：你看完这份调研 + 给出判断后
