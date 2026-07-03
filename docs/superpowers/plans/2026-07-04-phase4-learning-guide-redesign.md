# Phase 4 Learning Guide Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `04_学习向导.md` so it becomes a gradual, readable path from undergraduate foundations to Zhang Pengju's current research problems, without a day-by-day or training-camp structure.

**Architecture:** Keep `01/02/03` as inputs and rewrite only the phase 4 narrative surface plus the reusable phase 4 guidance rule. The document should be organized as a natural problem chain: why each next concept is needed, what paper route it unlocks, and how a student knows which missing piece to repair.

**Tech Stack:** Markdown documents, existing research-advisor skill references, existing deterministic verifier.

## Global Constraints

- Do not read or cite `archive/`.
- Use fresh source checks for phase 4 learning resources and current paper context.
- Do not write advisor evaluation, matching, recommendation, or application advice.
- Keep URLs traceable through clickable citation keys and the final `参考文献与资料` tables.
- Deterministic smoke is not academic-quality proof; report it as structural verification only.

---

### Task 1: Record the Phase 4 Rewrite Strategy

**Files:**
- Create: `docs/superpowers/plans/2026-07-04-phase4-learning-guide-redesign.md`

**Interfaces:**
- Consumes: user requirement: "循序渐进，由浅入深，从最基础的开始，一点点到前沿，最好一进组就能上手导师课题"
- Produces: a concise implementation record before touching phase 4 content

- [ ] **Step 1: Create this implementation plan**

Use this file to lock the rewrite target: problem-chain guide, not time plan or training manual.

- [ ] **Step 2: Commit the plan before major content edits**

Run:

```bash
git add docs/superpowers/plans/2026-07-04-phase4-learning-guide-redesign.md
git commit -m "docs: plan phase4 learning guide redesign"
```

Expected: commit succeeds on `codex/phase4-learning-guide-redesign`.

### Task 2: Rewrite the Active Phase 4 Document

**Files:**
- Modify: `output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/04_学习向导.md`

**Interfaces:**
- Consumes: `02_领域地图.md`, `03_论文路线.md`, phase 4 references, fresh search results for learning resources
- Produces: a redesigned learning guide centered on a gradual problem chain

- [ ] **Step 1: Remove the day-based and training-camp surface**

Delete or rewrite sections whose primary framing is:

```text
7 天快速摸底路径
三轮论文阅读
阶段产出物 as a training table
常见误区纠偏 as a checklist table
```

The content may be reused only if it becomes part of a natural reading path.

- [ ] **Step 2: Rebuild the document around a gradual problem chain**

Use these top-level sections:

```markdown
## 这份向导怎么用
## 终点：进组前应接近什么状态
## 第一段路：先知道光电子谱在看什么
## 第二段路：从静态谱走到时间分辨
## 第三段路：从飞秒过程走到阿秒电子运动
## 第四段路：从气相分子走到液相和凝聚相
## 第五段路：从读机制论文走到理解平台论文
## 回到张鹏举论文路线
## 卡住时怎么判断该补什么
## 资源指针
## 参考文献与资料
```

- [ ] **Step 3: Preserve citation discipline**

Keep in-text citations in this form:

```html
<sup><a href="#r4">[R4]</a></sup>
```

Keep the final source tables with five columns:

```markdown
| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
```

- [ ] **Step 4: Read the rewritten file for flow**

Check that the guide reads as a path:

```text
光电子谱看什么 -> 为什么需要时间分辨 -> 为什么需要阿秒/XUV -> 为什么液相更难 -> 为什么平台决定课题边界 -> 如何回到论文路线
```

### Task 3: Update Reusable Phase 4 Rules

**Files:**
- Modify: `.claude/skills/research-advisor/references/phase4-learning-guide.md`

**Interfaces:**
- Consumes: user feedback that explicit layer taxonomies feel unnatural
- Produces: reusable instruction preventing future phase 4 drafts from reverting to day plans or exposed classification frameworks

- [ ] **Step 1: Add a rule against exposed taxonomy headings**

Make clear that internal learning diagnostics may be used, but final headings should be student-facing problem-chain headings.

- [ ] **Step 2: Add a rule against fixed-day pacing**

Make clear that phase 4 may include progress checks, but not fixed day-by-day plans.

### Task 4: Verify and Commit

**Files:**
- Verify: `output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/04_学习向导.md`
- Verify: `.claude/skills/research-advisor/references/phase4-learning-guide.md`

**Interfaces:**
- Consumes: edited Markdown
- Produces: verification evidence and final commits

- [ ] **Step 1: Run deterministic smoke**

Run:

```bash
python .claude/skills/research-advisor/scripts/verify_phase_docs.py --prof-dir "output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举"
```

Expected: structure/source smoke passes, or failures are fixed and rerun.

- [ ] **Step 2: Check forbidden surface patterns**

Run:

```bash
rg -n "7 天|第 [0-9] 天|训练营|打卡|匹配度|推荐意见|是否应该申请" output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/04_学习向导.md .claude/skills/research-advisor/references/phase4-learning-guide.md
```

Expected: no day-plan or advisor-evaluation wording remains, except if the skill reference explicitly bans a pattern.

- [ ] **Step 3: Commit final changes**

Run:

```bash
git add output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/04_学习向导.md .claude/skills/research-advisor/references/phase4-learning-guide.md
git commit -m "docs: redesign phase4 learning guide"
```

Expected: commit succeeds.
