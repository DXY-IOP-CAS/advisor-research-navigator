# D01 通用Agent调研与设想 — 内容分块与关键产出提取

## 文件总览

该文件夹共 17 个 .md 文件，构成 D01 模块的完整学习记录：1 份全景图、1 份定大纲（7 知识点）、13 份课件/沙盒/结果文档、1 份全景调研参考文档、1 份收尾盘点。

源文件全景覆盖：BMAD Method、Mary 需求诱导、BMAD Spec 模板、AgentFactory、Agent 自演化领域全景（五大路线 15+ 框架）、SDD 需求哲学、AI Workflow Store。

---

## 块 1：BMAD Method 整体研究

### 源文件
- 00_全景图.md（第二节）
- 02_K1b-1_BMAD背景与四阶段概况.md
- 04_1_K1b-3_设计问题与对照.md
- 04_2_分析_BMAD对照与判断.md

### 调研了什么

BMAD-METHOD（Breakthrough Method for Agile AI-Driven Development），一个开源的多 Agent 敏捷开发框架。四个阶段：Analysis（可选）→ Planning（必须）→ Solutioning（必须）→ Implementation（可选）。采用 Agent-as-Code 模式——每个 Agent 是一份 Markdown 文件，定义专业领域/职责/约束/输出格式。三条轨道：Quick Flow（5 分钟，Bug 修复）→ Standard（完整四阶段）→ Enterprise（合规治理）。区分 Greenfield（新建）和 Brownfield（已有代码库）的不同入口。

### 学到了什么

- Agent-as-Code 解决两个问题：上下文窗口浪费（按需加载）、角色混淆（Agent 分离强制关注点分离）。
- BMAD 的 Analysis 和 Implementation 可选，Planning 和 Solutioning 必须——这提示"固定阶段数"不是唯一设计。
- 三轨道设计（Quick / Standard / Enterprise）说明流程深度随项目复杂度自适应。
- BMAD 的文档来源：官方仓库 https://github.com/bmad-code-org/bmad-method，官方文档 https://docs.bmad-method.org/，以及 DEV Community 和 Medium 等多篇解读文章。

### 对工具设计的可借鉴点

- 阶段间传递持久化产物（artifact）作为"唯一真相来源"——导师调研工具的各阶段输出也应以结构化文档传递。
- 场景共识优先于约束条件——调研导师时，先了解学者画像和研究方向，再问具体约束（地域、经费等）。
- 阶段退出条件明确——每个调研阶段结束时有明确的"通过/不通过"判定。

### 用户结论/决策

- BMAD 与 project-pilot 相似度约 70%，但 BMAD 纯软件导向，project-pilot 通用。
- 用户判断：BMAD 的诱导顺序（先场景→再收敛→再约束）应该被 project-pilot 阶段 1 采纳。
- 用户判断：project-pilot 用阶段级验证代替 BMAD 的节级验证，粒度不同但核心价值相同——"在修正成本最低的时候验证"。
- 用户形成了"四个阶段各自独立优化"的架构洞察：每个阶段有自己的方法论接口，阶段间通过产物传递。

---

## 块 2：Mary 需求诱导对话流程

### 源文件
- 03_1_K1b-2_Mary需求诱导对话流程.md
- 03_2_沙盒_Mary需求诱导.md
- 03_3_结果_Mary需求诱导.md

### 调研了什么

BMAD 的 Mary（Business Analyst Agent）的需求诱导系统。四层嵌套结构：模式选择（Interactive vs YOLO）→ 11 节模板逐节填写 → 每节 QA 质量门（9 个选项，可循环直到用户满意）→ 可随时调用的 Advanced Elicitation 方法库（Stakeholder Round Table、Red Team vs Blue Team 等）。

### 学到了什么

- 11 节顺序的设计原理：第 1-4 节建立场景共识→第 5-7 节收敛范围→第 8-10 节约束与风险→第 11 节附录。认知基础是"先激活相关心智模型，再引入约束"。
- 逐节 QA 质量门 9 个选项：展开细节、对标验证、压力测试、探索替代方案、权衡分析、风险缓解、MVP 极简挑战、功能脑暴、假设推演。
- 逐节 QA vs 整篇再审的本质区别：前者检查"需求正确性"，后者只检查"转述正确性"。修改成本随发现错误的时间呈指数增长。
- Stakeholder Round Table 创建多个虚拟角色（投资人、技术主管、市场经理），从不同利益视角审视同一份需求，暴露角色偏见导致的盲点。
- Interactive Mode 的选择本身就是需求诱导动作——用户的犹豫程度帮助判断需求清晰度。
- Advanced Elicitation 方法库从 methods.csv 动态加载，可被社区扩展和淘汰——"方法库自进化"设计。

### 对工具设计的可借鉴点

- 对导师调研工具的直接启发：调研导师时也应分层——先建立学者背景共识（研究方向、代表作），再收敛需求（你想跟这个学者学什么），最后引入约束（时间、经费、地域）。不应一上来就问"你的预算是多少"。
- 逐节 QA 机制可移植：写完"学者候选列表"后，AI 停下来让用户验证——"这个学者真的符合你的目标吗？"而不是一次性输出全部再让用户确认。
- Stakeholder Round Table 对导师调研的启发：可模拟"导师视角"查看邮件草案——导师看到这封邮件会怎么想？会觉得你做了功课吗？会想回复吗？
- AI 的责任是"引导用户的思考，不是替用户想"——导师调研时不应替用户做判断，而是帮用户自己想清楚匹配标准。

### 用户结论/决策

- 用户沙盒实测（项目：QMC 讲义整理工具）选 Interactive Mode，理由是"一次性输出会认知过载"——验证了认知负荷理论。
- QA 操作选了选项 5（Generate risk mitigation strategies），Mary 产出三个风险分析：笔记碎片化超出预期、讲义结构强加于材料、元工具悖论。
- 用户评价："他那个分析效果还行"——逐节 QA + 即时风险分析命中真实痛点。
- 用户判断：project-pilot 用阶段级验证代替节级验证，但核心价值相同。

---

## 块 3：BMAD Spec 模板的软件工程基因限制

### 源文件
- 05_1_K1c_BMAD_Spec模板限制.md
- 05_2_沙盒_BMAD_Spec填表.md
- 05_3_结果_BMAD_Spec填表.md

### 调研了什么

BMAD 的 Specification 模板结构（产品定义、工作拆分、技术规格、质量保障、约束条件）。核心前提："需求可以被拆成可估算的工单，每个工单可以被独立实现和测试"。

### 学到了什么

- 三类崩塌场景：(1) 产出物是"理解"而非"功能"时验收标准不是二值的；(2) 工单依赖是循环图（写第 5 章时发现第 3 章分类有误），不是 DAG；(3) 验收标准不能机械判定（"零基础读者能看懂"无法自动测试）。
- 用户沙盒发现：Epics / User Stories / Acceptance Criteria 三个字段全部崩塌，而 MVP Scope / Post-MVP Vision / Constraints & Assumptions 可以迁移。
- 根因不是"讲义撰写没有标准"，而是"标准不是二值的"——评判方式需从"通过/不通过"改为"多维 rubrics"（像 IELTS 作文评分四个维度）。
- Technical Considerations 字段在非软件项目中含义自动漂移——用户填成了"读者假设"，说明字段定义需要重新设计。

### 对工具设计的可借鉴点

- 导师调研工具的产出模板不能套用软件工程的工单式字段。导师匹配是"理解型"任务——"这个学者适合当我的导师吗？"不是二值的，是多维的。
- 可采用 rubric 设计：研究方向匹配度、指导风格匹配、学术影响力、地理位置可行性、时间可行性等维度分别评分。
- 标记迁移可行性有三种状态的方法（可直接迁移 / 需改造 / 不可迁移）——对模板复用的工具化有价值。

### 用户结论/决策

- 用户自己发现 rubric 作为解决方向："教育家领域有没有用一系列客观标准评判主观内容的经验？"——这成了后续模块的一个研究点。
- 用户判断：project-pilot 的产出模板应与 BMAD Spec 有本质区别——从"功能规格"变为"多维评估框架"。

---

## 块 4：AgentFactory 核心机制

### 源文件
- 06_1_K1d-1_AgentFactory_背景与核心问题.md
- 07_1_K1d-2_AgentFactory_核心机制.md
- 08_1_K1d-3_AgentFactory_对project-pilot的可借鉴设计.md

### 调研了什么

AgentFactory（arXiv:2603.18000，北大+港理工+智源）。核心设计：Meta-Agent（调度器）维护一个子 Agent 池。三个角色：Meta-Agent（任务路由器）/ 子Agent池 / 工作区管理器。三轮生命周期：Install（创建）→ Self-Evolve（精炼）→ Deploy（导出）。七个元技能：create_subagent / run_subagent / modify_subagent / list_saved_subagents / view_subagent_code / get_skill_description / finish。

### 学到了什么

- 核心思维翻转："存代码，不存文字"——可执行代码比文字经验强的四个理由：确定性重执行、可定点修改、可跨系统移植、可积累。
- 文字经验的根本问题：对 LLM 没有约束力——只是"参考"不是"指令"。
- Meta-Agent 的决策依据是"任务类型匹配"而非"任务内容相似度"——它判断"search_scholar 这个能力有没有现成子Agent"，不是"Zhang Zhang 和 Di He 是不是相似"。
- 与 Voyager（NeurIPS 2023）的关键差异：Voyager 技能只增不改，AgentFactory 增加了 Self-Evolve 阶段（modify_subagent）。
- Skill 库从空字典增长，每次 CREATED 让池变大，每次 REUSED 省时间。

### 对工具设计的可借鉴点

- 可借鉴 1：专门化+最小工具集——导师调研的不同步骤（学者搜索、论文分析、邮件写作）各配只够的工具，不给全量。
- 可借鉴 2：标准化接口文档——每个阶段有清晰的"吃什么、吐什么、退出条件"的定义，这是阶段间交接的唯一依据。
- 可借鉴 3：工作区隔离——每个调研项目独立目录，互不污染。
- 需改造 1：从自动创建到手动选择模板——AgentFactory 自动判断，project-pilot 需要用户确认。
- 需改造 2：从子Agent 代码到阶段模板——导师调研不需要自动 Agent，但需要可参数化的对话模板（"帮你找导师"的引导话术可以复用）。
- 需改造 3：从自动修改到提示审查——经验总结自动生成，但模板更新需人确认。

### 用户结论/决策

- project-pilot 三个阶段设计决策：(1) 经验载体不是代码是模板；(2) 经验积累不自动，人审查；(3) 经验按阶段索引，不按任务索引。
- 四个阶段"各自可以独立优化和升级"的架构洞察在 AgentFactory 对照中被进一步确认。
- project-pilot 不需要动态创建阶段（阶段数固定为 4），也不需跨 Agent 框架的代码导出。

---

## 块 5：Agent 自演化领域全景

### 源文件
- K1d_参考_Agent自演化领域全景调研.md

### 调研了什么

搜索范围 2023-2026 年论文/开源项目/行业实践，覆盖五大技术路线：

**路线一：文字经验**（2023-2024 主流）
- Reflexion（Shinn et al., NeurIPS 2023）：言语强化学习，跑完任务写"反思"文字。
- Self-Refine（Madaan et al., NeurIPS 2023）：输出→自批评→修改→再批评循环。
- PromptBreeder（Fernando et al., ICML 2024）：进化算法优化 prompt。

**路线二：代码技能积累**（与 AgentFactory 最直接相关）
- Voyager（Wang et al., NeurIPS 2023）：Minecraft 环境，自动生成 JavaScript 技能，只增不改。
- AgentFactory（Zhang et al., 2026）：加上了 Self-Evolve 修改机制。
- OpenSpace（HKUDS, 2026）：自演化技能引擎，插到现有 Agent 上的技能演化层，MCP 兼容，支持技能市场化共享。

**路线三：架构/工作流自动优化**（2024-2025）
- ADAS（Hu et al., 2024）：Sakana AI + UBC，元 Agent 自动搜索最优 Agent 架构。
- AFlow（Zhang et al., ICLR 2025）：蒙特卡洛树搜索自动优化 Agent 工作流。
- AutoFlow（Li et al., 2024）：自动生成 Agent 工作流。

**路线四：递归自改进**（2025，最激进）
- Darwin Godel Machine（Zhang et al., 2025）：Agent 读写自己源代码，变异→评估→保留/丢弃。
- AlphaEvolve（Novikov et al., 2025）：Google DeepMind，代码进化做科学发现。

**路线五：记忆系统**（基础设施层）
- MEM1（Zhou et al., 2025）：Agent 学会"什么时候该记、记什么"。
- A-MEM（Xu et al., 2025）：专门的"记忆 Agent"管理另一个 Agent 的记忆。
- Agent KB（Tang et al., 2025）：跨领域经验共享。
- EvolveR（OpenReview 2025）：完整经验生命周期闭环。

**产业界实践**：OpenClaw（自托管 Agent 运行时）、self-improving-agent（BerriAI，diff 提议+PR 创建）、OpenAI Self-Evolving Agents Cookbook（2025）。

### 学到了什么

- 自演化 Agent 的核心问题：经验怎么存、怎么让 Agent 下次用上、怎么越用越强。
- 五条路线按"经验载体从软到硬"排列：文字→代码→架构→源码→记忆系统。
- AFlow 等架构优化路线与 project-pilot 的四阶段流水线最直接相关——它会问"你怎么知道这个顺序是最优的？"
- OpenSpace 的"插件式技能引擎"思路：自演化可以是独立于 Agent 框架的外挂层。
- 两篇综述：Gao et al. (arXiv:2507.21046) 按"演化什么/什么时候/怎么演化/在哪里演化"四维度分类；Xiang et al. 的 Awesome-Self-Evolving-Agents 仓库持续更新。

### 对工具设计的可借鉴点

- 对导师调研工具的核心启示：不需要从零搭建 Meta-Agent 动态创建能力，但需要"保存项目经验为模板"——做完一次导师调研后，搜索策略、邮件模板、评估标准可以存下来复用。
- OpenSpace 的"即插即用"设计思路：导师调研工具可以作为 project-pilot 的一个"插件模块"，不依赖完整的四阶段框架也能独立使用。
- 工作流不应该完全固化——简单导师调研（"搜一下这位学者"）和深度导师调研（"系统评估 5 位候选导师"）需要不同深度级别。
- 记忆系统的思路："存什么、怎么查、怎么更新"——每次调研结束后，产出（学者评估表、邮件草案）作为"指纹"存下来，下次同类项目检索复用。

### 用户结论/决策

- "代码技能积累"是刚需但不需要全部照搬——project-pilot 需要模板化积累，不是代码化积累。
- 工作流不应该固化——四阶段可能需要"快速模式"和"深度模式"。
- 记忆系统是长期必须的，当前最简方案：每个项目结束后把阶段 1 产出作为"指纹"保存。
- 总览对比表显示：代码技能路线和架构优化路线对 project-pilot 价值最高，递归自改进路线太底层不适合。

---

## 块 6：SDD 需求先行哲学

### 源文件
- 09_1_K2a_SDD需求先行哲学.md

### 调研了什么

SDD（Spec-Driven Development），2025 年下半年随 AI 编码 Agent 普及兴起的方法论。人写规格书→AI 读 Spec→AI 生成代码→人审查代码。Martin Fowler 将 SDD 分为三级：Spec-first（一次性）、Spec-anchored（长期保留）、Spec-as-source（Spec 即源码）。核心假设："需求可以在动手之前被完全无歧义地写清楚"。

### 学到了什么

- SDD 的假设在"项目目标明确、验收标准可机械判定"的场景成立（如"做一个登录页面"），在"产物是理解、需求本身是探索性的"场景崩塌。
- Martin Fowler 自己试用后的批判：修一个 Bug 被拆成 4 个 User Story + 16 条验收标准是"用牛刀杀鸡"；中等复杂度功能生成了 8 个 Markdown 文件——"我宁愿审查代码，也不愿审查这么多 Markdown"。
- SDD 的 Constitution（不可变的高层原则）——是所有 Spec 必须遵守的顶层约束。

### 对工具设计的可借鉴点

- 可借鉴 1：结构化字段——导师调研的需求板应有类型化字段（"你想学什么方向/你期待什么指导风格/时间限制"），不是自由文本。
- 可借鉴 2：Constitution 概念——导师调研工具需要一个"项目宪章"：核心约束（如"必选国内""预算上限 X"）在调研各阶段不被推翻。
- 不借鉴 1：一次写完——导师调研中，用户的需求理解一定会在调研中改变（"原来这位学者做的是这个方向，我不太感兴趣"），必须允许迭代修正。
- 不借鉴 2：Spec-as-Source——调研产出（学者评估表、邮件）必须被人修改。

### 用户结论/决策

- SDD 和 project-pilot 的核心分歧：SDD 假设需求可写清楚，project-pilot 假设需求只能在做的过程中被逐渐搞清楚。对应到导师调研：用户一开始说"找个做凝聚态物理的导师"，可能调研后才意识到"我更想做拓扑物态"——不是缺陷，是设计意图。
- "Constitution"概念被采纳到收尾盘点的三层结构（协议层）。

---

## 块 7：AI Workflow Store

### 源文件
- 10_1_K2b_AI_Workflow_Store.md

### 调研了什么

Columbia + Google 2026 年 5 月的论文（arXiv:2605.10907）。核心诊断：今天大多数 AI Agent 的执行模式是"即兴合成"——每次从零编方案、调工具、执行，绕过了传统软件工程的可靠性机制。答案是把经过打磨和测试的可靠工作流存下来形成 Workflow Store。每个工作流是一个工程化包裹：类型化输入、工具白名单、人工确认点、评估用例+对抗测试、日志遥测、版本+弃用策略。

### 学到了什么

- "即兴 vs 硬化"的二分法：大多数任务不该被硬化——只对重复且高风险的硬化工作流。真正新颖的、一次性的、探索性任务让 Agent 即兴发挥但有人监督。
- 与 AgentFactory 的关键区别：AgentFactory 存子Agent 代码（自动），AI Workflow Store 存工作流规范（人工设计、审查、维护）。
- LLM 角色被重新定位：从"建筑师的实施者+操作者"缩小为"工作流选择器+参数提取器+执行监控者"。

### 对工具设计的可借鉴点

- 导师调研也可以区分"模板化路径"和"探索路径"：同类型调研（再次找导师、再次搜论文）走模板，首次调研类型从零跑。
- 类型化输入设计：导师调研模板应设结构化字段——项目类型/学者类型/研究方向/产出形态/已知信息/已知盲区/硬约束。
- 人工确认点：拟邮件、发邀请等不可逆操作前必须人确认。
- 不借鉴"硬化"程度：导师调研不能冻住，用户的理解随时可以改。

### 用户结论/决策

- AI Workflow Store 与 project-pilot 的结构相似度最高（约 80%），但方向不同——AI Workflow Store 面向重复性高风险操作（订机票），project-pilot 面向探索性项目（写讲义、做调研）。
- 用户判断："即兴 vs 硬化"的二分法对 project-pilot 的阶段设计有直接参考价值。

---

## 块 8：整合与决策（收尾盘点）

### 源文件
- 收尾盘点.md
- 00_全景图.md

### 调研了什么

project-pilot 启动时的已有积累盘点：学习方法论 v7.0、论文下载与翻译 SOP、CLAUDE.md 双轨路由、搜索回退链、教学六步法。以及 D01 诞生的四个关键设计问题。

### 学到了什么

- 四个问题的 D01 后答案：
  1. 框架形式：三层结构——协议层（Constitution，不可变 Markdown 规则）、模板层（Templates，可精炼的 Markdown 模板）、经验层（Experience，结构化踩坑记录）。
  2. Skill 借用：阶段 2（调研）有现成 Skills；阶段 1/3/4 都需要自研。
  3. 翻译工具定位：作为 project-pilot 的第一个完整走通四阶段的项目。
  4. 迭代机制：经验自动记录、模板人工决定是否更新、协议不改（除非方法论重大升级）。
- D01 后产出更精细的骨架图（三层架构+阶段 1/2/3+4 各挂具体工具）。
- D01 后仍开放的 4 个问题：阶段间数据格式、阶段回退协议、自适应深度、模板市场（长期）。

### 用户结论/决策

- 核心判断在 D01 启动时就是清楚的且在学完后没有被推翻：project-pilot 不是独立 Agent 平台，是增强现有 Agent 的方法论框架+可复用模板。
- 四个框架各从不同角度验证了这个判断。
- "经验自动记录、模板人工更新、协议不改"——三层迭代机制形成最终架构。

---

## 该文件夹对你设计导师调研工具的可参考价值评估

### 高价值直接可用的设计思路

1. **诱导顺序"先场景再约束"**：导师调研的需求锚定阶段，应先建立学者背景共识（研究方向/代表作/学术风格），再收敛"你想学什么"，最后引入约束（地域/时间/经费）。不应一上来就问预算或地域。

2. **逐节验证 vs 整体验证**：导师调研的每一步（如"学者候选列表"）写完都停下来让用户确认。避免用户在一无所知时接受整份列表，之后发现方向错了却因为投入过大而不愿回头。

3. **多视角验证**：Stakeholder Round Table 模式可移植到导师调研——模拟"导师视角"阅读邮件，检查"这封邮件会让我想回复吗？"。这对中国学生写英文套磁邮件尤其有价值——用户往往无法自己判断邮件是否得体。

4. **类型化输入避免自由文本**：导师调研的需求板应该设计结构化字段（项目类型/学者类型/研究方向/产出形态/已知盲区/硬约束），而不是"描述一下你想要什么样的导师"。

5. **模板化积累**：做完一次导师调研后，搜索策略、评估标准、邮件模板可以结构化保存，下次同类项目直接复用。不需要 Code-level 的 AgentFactory，但需要 Template-level 的复用。

6. **项目宪章（Constitution）**：核心约束（如"必须国内""不走学术路线只求就业指导"）在各调研阶段不被推翻，防止方向漂移。

### 部分可用的概念

7. **"即兴 vs 硬化"二分法**：简单导师调研（"搜一下这位学者"）走轻量路径，系统导师调研（"找 5 位候选+写邮件+评估"）走完整路径。不同级别不同深度。

8. **Rubric 替代通过/不通过**：导师匹配不是二值的。可以设计多维评估框架：研究方向匹配度、指导风格、学术影响力、地域、费用等——综合评分而非暴力拒绝/接受。

9. **工作区隔离**：每个导师调研项目在独立目录中运行，经验教训不会跨项目污染。

### 低价值或不适用的部分

10. **AgentFactory 的动态创建子Agent**：导师调研不需要 AI 自动创建新 Agent。阶段是固定的——需求锚定→学者搜索→评估排序→邮件联络。不需要动态长出新阶段。

11. **递归自改进**：Darwin Godel Machine 这类自改代码的方向过于底层。导师调研工具不需要进化自己的代码，只需要优化模板和经验。

12. **BMAD Spec 的工作拆分类**：Epics/User Stories/Acceptance Criteria 在导师调研场景中崩塌——你不能把"找导师"拆成可独立估算的工单。这部分完全不可迁移。

### 总评

D01 调研的四个框架（BMAD、AgentFactory、SDD、AI Workflow Store）中，对导师调研工具最直接有参考价值的是 **BMAD 的诱导对话设计**和 **AI Workflow Store 的"即兴 vs 硬化"二分法**。BMAD 的逐节 QA、11 节诱导顺序、多视角验证是需求锚定阶段可以直接移植的机制。AI Workflow Store 的类型化输入和人工确认点是第二阶段（计划制定+执行）的设计参考。AgentFactory 的价值主要在"如何积累复用经验"这一长远问题上，而非工具初版。

所有文件的验证来源列表（按文件路径索引）：
- BMAD 官方仓库: https://github.com/bmad-code-org/bmad-method
- BMAD 官方文档: https://docs.bmad-method.org/
- BMAD Advanced Elicitation SKILL.md: https://github.com/bmad-code-org/BMAD-METHOD/blob/main/src/core-skills/bmad-advanced-elicitation/SKILL.md
- AgentFactory 论文: arXiv:2603.18000, https://github.com/zzatpku/AgentFactory
- Agent 自演化全景领域：包含 Reflexion (arXiv:2303.11366), Voyager (arXiv:2305.16291), ADAS (arXiv:2408.08435), AFlow (arXiv:2410.10762), AutoFlow (arXiv:2407.12821), DGM (arXiv:2505.22954), AlphaEvolve (arXiv:2506.13131), MEM1 (arXiv:2506.15841), A-MEM (arXiv:2502.12110), Agent KB (arXiv:2507.06229), EvolveR (OpenReview), 两篇综述 (arXiv:2507.21046; Awesome-Self-Evolving-Agents GitHub)
- SDD: Martin Fowler 文章 (martinfowler.com), Augment Code 指南, GitHub spec-kit, arXiv:2602.00180
- AI Workflow Store: arXiv:2605.10907, Alchemic Technology 解读
