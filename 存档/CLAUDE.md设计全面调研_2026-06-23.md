# CLAUDE.md 指导文件设计全面调研

调研日期：2026-06-23 | 数据来源：Tavily Research + Exa 语义搜索 | 覆盖：Anthropic 官方文档、Hacker News、Reddit、DEV Community、独立博客、学术论文

---

## 一、CLAUDE.md 的本质（你首先需要知道的事）

### 它不是系统提示词

Anthropic 在加载 CLAUDE.md 时，外面包了一层 disclaimer：

> "The contents of this file may or may not be relevant to the current task. Use your own judgement."

这意味着：**CLAUDE.md 是「建议」，不是「铁律」**。社区实测遵从率约 60-70%。短文件高一些，长文件断崖下跌。

### 它消耗的上下文预算是永久的

每一次对话开始，CLAUDE.md 的每一行都要被加载。200 行就是 200 行的固定开销——无论你这轮对话是要重构架构还是改一个 CSS 属性。

**由此得出第一原则：每一行都必须挣它的位置。删掉一条规则的代价是 Claude 可能犯那个错误，保留一条废规则的代价是 Claude 可能忽略十条重要的。**

---

## 二、社区共识的硬标准

以下结论在 10+ 独立来源中高度一致：

### 2.1 长度

| 标准 | 来源 |
|:---|:---|
| **硬上限 200 行** | Anthropic 官方最佳实践 |
| **推荐 60-80 行** | Karpathy 公开 CLAUDE.md 65 行；HumanLayer 生产环境 <60 行 |
| **150 条指令是模型注意力预算上限** | HumanLayer Blog (2026)；OTF Blog |
| **超过 200 行 → 遵从率断崖下跌至 50% 以下** | XDA Developers 实测；Hacker News 多用户报告 |

### 2.2 失败日志模式（Mitchell Hashimoto / Ghostty）

社区公认 **最有效的 CLAUDE.md 设计哲学**，来自 Hashimoto（Terraform/Vagrant 作者）：

> "Every single line exists because the agent made that specific mistake at least once. No line is aspirational. Every line is a scar from a real incident."

翻译：**每一条规则都必须对应一次真实的 AI 犯错记录**。没有「可能有用」的规则，没有「以防万一」的规则。

### 2.3 具体化 > 模糊化

| 模糊（被忽略） | 具体（被遵从） |
|:---|:---|
| "写干净的代码" | "变量用 camelCase，React 组件用 PascalCase" |
| "测试你的改动" | "每次改动后跑 `npm test`，`utils/` 下覆盖率 ≥ 80%" |
| "用 TypeScript" | "**必须**用 TypeScript strict mode，**禁止** `any` 类型" |
| "小心操作 git" | "每个任务新建分支，**禁止**直接提交到 main" |

### 2.4 禁止 + 替代 > 纯建议

来自独立开发者社区的验证：

| 弱 | 强 |
|:---|:---|
| "用 App Router" | "**禁止** Pages Router → 用 App Router" |
| "用函数组件" | "**禁止** class 组件 → 用函数组件" |
| "优先用 async/await" | "**禁止** completion handler → 用 async/await" |

原理：训练数据中旧模式的样本量远超新模式。只说「用新的」，模型在压力下会滑回多数类。**禁止词进入 context 后，模型 token-by-token 避开它**。

### 2.5 Voice Rules（反 AI 味）

社区公认最高效的反 AI 味手段——按效果排序：

| 手段 | 效果 | 原理 |
|:---|:---:|:---|
| **禁止词列表**（15-25 个具体词汇） | ★★★★★ | 模型被禁止后被迫寻找更自然的替代词 |
| **禁止句式**（"It's worth noting", "In today's world" 等） | ★★★★ | 阻止 AI 味最重的结构性习惯 |
| **结构约束**（段长 ≤ 3 句、句长 ≤ 40 字） | ★★★ | 打破 AI 默认的均匀长段落 |
| **模糊指引**（"写自然一点"） | ★ | 无法执行 |

来源验证：500k.io、willfrancis.com、ccforseo.com、llmbestpractices.com 四篇独立来源结论完全一致。

---

## 三、CLAUDE.md 应该包含什么

### 社区共识的「该放」

| 内容 | 重要性 | 说明 |
|:---|:---:|:---|
| **构建/运行/测试命令** | 最重要 | Claude 能跑对命令，其他都能救回来 |
| **锁定决策**（技术选型） | 高 | "用 Drizzle，不是 Prisma"——防止 Claude 反复 debate 已决定的栈 |
| **禁止模式**（不可逆操作） | 高 | "**禁止**修改已应用的 migration"——但更强的应走 Hooks |
| **项目特定约定** | 高 | 文件命名、目录结构、非标准惯例 |
| **Voice rules** | 中 | 禁止词列表 + 结构约束 + 语气偏好 |
| **架构约束** | 中 | "API handler 在 `src/api/handlers/`" |

### 社区共识的「不该放」

| 内容 | 为什么不该放 |
|:---|:---|
| Linter/Formatter 能做的事 | 工具更快更可靠，不消耗 AI 注意力预算 |
| 标准语言惯例 | Claude 已经知道 TypeScript/Python 习惯用法 |
| 完整 API 文档 | 链接到文档，别粘进来 |
| README 的项目介绍 | CLAUDE.md 不是 README，它有不同目的 |
| 只在某些任务有用的内容 | 放到 Skills，按需加载 |
| 频繁变动的信息 | Sprint 任务/Git 状态等 → 放到 `current-state.md`，每次 SessionStart 重新读 |
| "以防万一"的规则 | 没发生过就别写。每条规则必须对应一次真实事故 |

---

## 四、CLAUDE.md 不是万能的——强制力层级

社区实测结论：CLAUDE.md 的遵从率约 60-70%。以下场景需要更强的强制力：

| 约束类型 | 应放位置 | 强制力 |
|:---|:---|:---:|
| 风格/约定/偏好 | **CLAUDE.md** | ~70% 遵从 |
| 可重复工作流 | **Skills**（`/fix-issue` 等） | 按需加载 |
| 特定路径规则 | **`.claude/rules/`**（path-scoped） | 仅在匹配路径生效 |
| 零例外强制 | **Hooks**（PreToolUse/SessionStart） | 100% 确定性 |
| 个人快捷键/WIP | **CLAUDE.local.md**（不入 Git） | 仅你可见 |

经验法则：**如果一条规则被违反两次且已经写在 CLAUDE.md 里——不是规则不够多，是该规则需要升格到 Hooks。**

---

## 五、维护铁律

| 原则 | 具体操作 |
|:---|:---|
| **事件驱动更新** | Claude 每犯一次错 → 加一条规则（而非「我觉得应该加」） |
| **季度剪枝** | 三个月没触发的规则 → 考虑删除 |
| **升格规则** | 规则从 CLAUDE.md 毕业后 → 删掉（避免两份都有） |
| **诊断测试** | 让 Claude 不看文件总结 10 条核心规则。如果对不上你关心的 → 文件太长/太乱 |
| **review like code** | 大重构后 → 同步更新 CLAUDE.md |

---

## 六、反模式速查

| 反模式 | 后果 |
|:---|:---|
| 太长（>200 行） | 所有规则的遵从率都被稀释 |
| 太模糊 | 模型无法执行，等于没写 |
| 自动生成（`/init` 输出直接当 CLAUDE.md） | 过于冗长/通用，不含你的真实约定 |
| 当 README 写 | 对 AI 无用，浪费上下文 |
| 当知识库 dump | 每次对话都加载不相关内容 |
| 只有正向规则没有禁止 | 模型在压力下滑回旧模式 |
| 写一次忘一次 | 3 个月后文件就过时了 |
| 靠 CLAUDE.md 拦截危险操作 | 应该走 Hooks 的事不要靠 CLAUDE.md |

---

## 七、对当前全局 CLAUDE.md 的诊断

你的全局 CLAUDE.md 当前约 68 行，结构如下：

| 节 | 行数 | 评价 |
|:---|:---:|:---|
| 自检 | 3 | 具体、有优先级、可验证。符合社区最佳实践。 |
| 身份 | 6 | 清晰的 WHAT，提供上下文。 |
| 沟通与格式 | 5 | 格式规则具体可执行。**缺失**：Voice rules（禁止词列表 + 结构约束）。 |
| 学习偏好 | 1 | 具体流程，可验证。 |
| 工作习惯 | 4 | 混合，部分具体（"产物保存到练习册/"）部分可更精确。 |
| 联网搜索 | 28 | 刚优化过，机制完整但偏长。可考虑外置到引用文件。 |

### 核心缺失

**Voice rules 完全空白**——这是你「AI 味太重」抱怨的根因。目前「沟通与格式」只约束了 emoji / 块引用 / 标题层级 / 竖线，对 AI 话术毫无约束。

### 建议添加的内容（约 15 行）

1. **禁止词汇**：AI 高频空洞词 15-20 个
2. **禁止句式**：签名式开头/结尾、restate the question、过渡句
3. **结构约束**：段长、句长、一段一个点

### 可能过长的节

「联网搜索」28 行占文件的 41%。对于高频使用的搜索规则来说算合理——但它属于「特定工作流」，理论上更适合放在 Skill 里。可以保留在 CLAUDE.md 因为搜索贯穿所有对话，但你也可以考虑精简到 15-18 行。

### 总体评估

**你的 CLAUDE.md 在社区标准里属于中上水平**——短（68 行）、具体（大部分规则可验证）、有优先级体系。最大的改进空间是用 15 行 Voice rules 堵住 AI 味漏洞。加上后约 83 行，仍在社区推荐的 60-80 行甜蜜区间内。
