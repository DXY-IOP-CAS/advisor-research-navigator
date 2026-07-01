# AI 编程效率工具调研 — pilot-test 项目适配分析

**生成日期**：2026-07-01
**目的**：找出适合 pilot-test 项目当前阶段的 AI 编程效率工具，不生搬硬套
**核心问题**：你之前指出 pipeline.md 内容错位混乱——我加了太多东西但不实用。这次调研目的就是选有用的

---

## 1. 核心结论先说

| 推荐采用 | 强烈推荐 | 不推荐 |
|:--------|:--------|:-------|
| **保持当前最小结构 + 借鉴 Superpowers 的"skill 模式"** | 借鉴 leanclaude 的"目录级 CLAUDE.md"思路，限制 CLAUDE.md 文件大小 | 安装 superpowers 完整插件（你一个人项目不需要 14 个 skill） |
| | | 不引入 GSD/BMAD/SpecKit（项目规模和团队规模都不匹配） |
| | | 不引入 schema.py 这种"看起来工程化"的 dataclass 体系（YAGNI） |

**当前 src/phase1/ 需要清理的部分**（不是加东西，是减）：
- schema.py 的 dataclass 用不上——step 之间的 JSON 通信，AI 直接读 JSON 就好。schema validation 对 pipeline 帮助小，对脚本内调用有帮助但目前脚本内调用极少。
- errors.py 7 个异常子类用不上——脚本端都是 `if data: status=success else status=error`。自定义异常层级做过度工程。
- 66 个测试中 `test_clean_doi_lowercase` 等 trivial 测试是 noise——AI 不会因为它失败而停止。
- README.md 是 AI 写给 AI 看的，没人读。

---

## 2. 详细调研

### 2.1 Superpowers (obra/superpowers) — 240K⭐

**核心理念**：14 个 SKILL.md 文件 + session-start hook。AI 启动后必须先看相关 skill，再做事。

**7 阶段工作流**：
1. **brainstorming** — 写代码前用苏格拉底式提问搞清楚需求
2. **git-worktrees** — 每个非琐碎任务在新 worktree 跑
3. **writing-plans** — 把工作分成 2-5 分钟的微任务，每个有具体文件路径和验证步骤
4. **subagent-driven-development** — 每个任务用 fresh subagent，两阶段审查（spec 合规性 + 代码质量）
5. **test-driven-development** — 强制 RED-GREEN-REFACTOR，写代码前先写测试
6. **requesting-code-review** — 任务之间做对抗性审查
7. **finishing-a-development-branch** — 任务完成后清理

**对你的项目适配度分析**：

| Superpowers 组件 | 是否适合 pilot-test | 理由 |
|:----------------|:-------------------|:-----|
| brainstorming | ❌ 不需要 | 你已经手动 brainstorming 完成了（计划书、CLAUDE.md 都是设计产物） |
| git-worktrees | ⚠️ 可选 | 你一个人项目，不需要并行 worktree |
| writing-plans | ⚠️ 部分用 | 阶段 1 已经是 plan（pipeline.md §3-5），但 sub-task 粒度不够 |
| subagent-driven-development | ❌ 太重 | 阶段 1 只有 6 步脚本，不需要 subagent 派发 |
| test-driven-development | ✅ 部分用 | 你之前的反馈说"代码质量差"。TDD 的核心是"写测试 → 看失败 → 写代码 → 看通过"，对你有用 |
| requesting-code-review | ⚠️ 手动做 | 你每轮对话结尾都是我做的代码 review，但没结构化 |
| finishing-a-development-branch | ❌ 不需要 | 单人项目，不需要 git workflow 自动化 |

**关键洞察**：Superpowers 整套不适合你（你一个人、单人项目、阶段 1 只剩调优），但**它的"SKILL.md 模式"值得借鉴**——一个 markdown 文件描述一个工作流，AI 在合适的时候调用。

### 2.2 leanclaude — 4.5K⭐

**核心理念**：CLAUDE.md 只做索引，所有规则分散到 `.claude/rules/` 下的多个文件，按需加载。

**关键数据**：
- 5,000 行 CLAUDE.md ≈ 13,000 tokens/session
- leanclaude 模板 ≈ 4,500 tokens/session（节省 65%）
- 每个 session 平均 20 次 prompt × 8,500 token 节省 = 170,000 token/天

**对你的项目适配度**：

✅ **非常适合**。你的 `pipeline.md` 已经 17K bytes，是单一文件包含所有信息。AI 每次启动都加载它，但大部分内容（§4 阶段 B 细节、§8 错误处理）只在特定情况下需要。

建议做法：
- `pipeline.md` 只保留 §0 全流程总览 + §2 数据契约 + 链接到子文件
- `src/phase1/pipeline_step1_to_3.md` — 阶段 A+B 详细步骤
- `src/phase1/pipeline_step4_to_6.md` — 步骤 4-6 详细
- `src/phase1/error_handling.md` — 错误处理细节
- AI 按需读

### 2.3 GSD (~8K⭐) — 速度导向

**核心理念**：context 防腐败。每个 phase 一个 fresh orchestrator，状态写到磁盘 markdown。复杂任务并行。

**对你的项目适配度**：❌ 不适合。你的项目是 sequential pipeline，不需要 wave parallelism。

### 2.4 BMAD (49K⭐) — 企业级

**核心理念**：模拟 12+ agent 角色（PM、架构师、开发者、QA），覆盖完整 agile 流程。

**对你的项目适配度**：❌ 严重过度工程。你一个人，不需要 PM/QA 角色分工。

### 2.5 GitHub Spec Kit (111K⭐)

**核心理念**：spec → plan → tasks → implement 四阶段，每阶段有人工审批。

**对你的项目适配度**：❌ 你已经有计划书（v4.0），再叠一层 spec-driven 是双轨。

### 2.6 OpenSpec (54K⭐)

**核心理念**：change-centric delta specs，brownfield 友好。

**对你的项目适配度**：❌ 不是 greenfield 项目，且你已经有 CLAUDE.md + pipeline.md 的事实标准。

---

## 3. 工具对比表

| 工具 | 适合规模 | 适配你 | 原因 |
|:-----|:---------|:------|:-----|
| Superpowers 完整 | Solo-小团队 | ❌ | 14 个 skill 对你太多 |
| Superpowers 单一 skill 模式 | 任何 | ✅ 部分 | 单个 SKILL.md 文件可借鉴 |
| leanclaude | Solo-中团队 | ✅ 强推荐 | 解决 CLAUDE.md 膨胀问题 |
| GSD | 中-大型团队 | ❌ | 速度导向，你不需要 |
| BMAD | 企业级 | ❌ | 12 角色对你 bloat |
| Spec Kit | 中-大型 | ❌ | 你已有计划书 |
| OpenSpec | Brownfield | ❌ | 你不是 brownfield |
| claude-code-harness | 任何 | ✅ 部分 | 4 个目录结构清晰 |

---

## 4. pilot-test 项目当前评估

### 4.1 我之前做错的事

```
错（应该删）                                    原因
─────────────────────────────       ────────────────
src/phase1/schema.py                  YAGNI：step 间 JSON 文件通信
                                     dataclass 验证帮不上忙，
                                     错了 json.load 直接抛

src/phase1/errors.py 7 个子类        YAGNI：脚本端 if/else 就够
                                     异常层级是装饰性的

66 个测试中 ~30 个 trivial 测试      noise：AI 不会因为
                                     test_clean_doi_lowercase 
                                     失败而停止

src/phase1/README.md                  给 AI 看的 doc 给 AI 写
                                     → 死循环，价值低

pyproject.toml 依赖锁定              项目还没部署给别人用
                                     pip install scholarly 一行
                                     就够

pipeline.md 17K bytes                单文件，所有信息塞一起
                                     应按 leanclaude 拆开
```

### 4.2 应该保留的

```
保留                                          原因
───────────────────────────────       ────────────────
6 个 step 脚本 + render_profile.py   工具主体，流程清晰

utils.py 的核心函数                   共享逻辑，重复代码是屎山根源

5-10 个核心单元测试（utils + merge）    TDD 的核心价值，trivial 测试是 noise

contracts 文档（不一定是 markdown，   AI 在合适时机加载
  可以分多个 SKILL.md）

git worktree 的局部使用                大改动时手动开 worktree
```

### 4.3 借鉴的具体模式

**借鉴 leanclaude 拆 CLAUDE.md**：
- `CLAUDE.md`（项目根）—— 只列目录索引，约 100 行
- `.claude/rules/00_project_basics.md` —— 项目结构、build 命令
- `.claude/rules/01_pipeline_overview.md` —— 3 阶段流程 + 数据契约
- `.claude/rules/02_step2_gs.md` —— GS 步骤细节
- `.claude/rules/03_step3_openalex.md` —— OA 步骤细节
- `src/phase1/README.md` —— 阶段 1 代码结构

AI 按需读。降低 token 消耗，加快启动。

**借鉴 harness 4 目录结构**：
```
.claude/
  CLAUDE.md           # 项目全局指引（短）
  skills/              # 行为 skills（verbs）
    research-advisor/  # 已存在的
      SKILL.md
      references/      # 已存在
  rules/               # 项目惯例（拆开的 CLAUDE.md）
  memory/              # 跨会话记忆
```

---

## 5. 具体执行计划（建议）

按优先级：

### 5.1 立即清理（YAGNI 卸载）

1. **删 `schema.py`** —— dataclass 没被任何 step import，没有验证需要
2. **删 `errors.py`** —— 7 个异常子类用不上，替换为 `print status: error, message`
3. **删 30 个 trivial 测试** —— 保留 utils 的核心 5 个 + merge 的核心 5 个 = 10 个
4. **删 `README.md`** —— 信息已在 pipeline.md 和 CLAUDE.md
5. **删 `pyproject.toml`** —— 单人项目，先 pip install scholarly 就够
6. **拆 `pipeline.md`** —— 按 leanclaude 模式拆成 4-5 个小文件

### 5.2 借鉴（不要全搬）

1. **保持 SKILL.md 模式**：`.claude/skills/research-advisor/` 已是这个模式，继续完善就好
2. **加 `.claude/rules/` 分主题规则** —— 把 pipeline.md 内容拆到这里
3. **CLAUDE.md 改成纯索引** —— 引用 rules/ 和 skills/ 路径
4. **不要装 superpowers 完整插件** —— 它的 14 个 skill 你用不上
5. **不要装 GSD/BMAD/SpecKit** —— 都不适合

### 5.3 不做

- 不引入 subagent 编排框架
- 不引入 spec-driven 工作流
- 不引入 multi-agent 角色模拟
- 不增加 dataclass/schema 体系
- 不增加 dataclass validation 框架（pydantic 等）

---

## 6. 验证来源

- Superpowers 文档：https://github.com/obra/superpowers/blob/main/README.md（fetch 时间 2026-07-01）
- 框架对比：https://github.com/olivomarco/genai-development-techniques（4 类别 10 个 Tier-1 技术）
- Ry Walker 对比研究：https://rywalker.com/research/agentic-skills-frameworks
- leanclaude 模板：https://github.com/aslammhdms/leanclaude
- claude-code-harness：https://github.com/revfactory/claude-code-harness

---

## 7. 一句话总结

**你的项目不需要新框架，需要减重 + 拆文档**。借鉴 leanclaude 的"小 CLAUDE.md + 分散规则"模式和你已有的 SKILL.md 结构，把 pipeline.md 从 17K 拆成 4-5 个小文件，删 schema/errors/trivial tests/pyproject 这些过度工程产物，工具就能从臃肿回到刚好。

不推荐直接装 superpowers 完整插件——它有 14 个 skill，你只需要其中 1-2 个的工作流模式。直接借鉴方式就行。