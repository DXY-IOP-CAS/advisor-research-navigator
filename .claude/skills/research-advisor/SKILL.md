---
name: research-advisor
description: >
  Run Phase 1 (paper collection + structured profile) for a professor.
  Use when the user wants to "调研导师", "了解一个学者",
  "分析导师的研究方向", "生成导师画像", or "做选导师前期调研".
---

# research-advisor

## 用途

用户输入导师姓名 + 机构 + 官网 URL → 阶段 1 全自动流 → `01_基础画像.md`。

数据采集策略详见 `src/phase1/pipeline.md`（CLI 命令、字段格式、API 参数）。
身份锁定协议和阶段设计详见 `docs/计划书.md` 第二章。

## 阶段总览

| 阶段 | 产出 | 状态 |
|:----:|:-----|:----:|
| 1 基础画像 | `01_基础画像.md` | ✅ 已实现 |
| 2 领域脉络 | `02_领域脉络.md` | ❌ 待设计 |
| 3 论文定位 | `03_论文定位.md` | ❌ 待设计 |
| 4 学习讲义 | `04_学习讲义.md` | ❌ 待设计 |

## 阶段 1 文档地图（progressive disclosure）

**原则**：subagent 启动只读本页（L1）。触发阶段 1 时按需读 references/，不要一次全读。

| 文件 | 何时读 | 内容 |
|:-----|:-------|:-----|
| `SKILL.md`（本页） | 始终（L1） | 入口、路由、阶段一览 |
| `references/phase1-core.md` | 触发阶段 1 时（L2） | 5 步流程 + 叙事规范 + 硬约束 |
| `references/phase1-templates.md` | Phase A 创建 JSON 时（L3） | verified_ids.json / career_stages.json schema |
| `references/phase1-anti-patterns.md` | 写叙事/调 verify 时（L3） | 反面案例 + 文件修改铁律 |
| `references/phase1-recovery.md` | step/verify 失败时（L3） | 错误恢复 + verify 循环指引 |
| `references/01-data-sources.md` | 调 API 失败时（L3） | 数据源细节、限速、降级 |
| `src/phase1/pipeline.md` | 看 CLI/字段格式时 | 技术细节（不是 AI 行为手册） |

**AI 工作流**：读到 SKILL.md → 触发阶段 1 → 读 phase1-core.md → 遇到具体问题时按需读 L3 文件。

## 第一步（必读）：初始化目录

用 `phase1_init.py` 创建目录，不要手动 mkdir 或拼路径：

```bash
python src/phase1/phase1_init.py \
  --university "中国科学院大学" \
  --institute "中科院物理所" \
  --department "超快物质科学中心" \
  --name "王示例"
```

脚本输出 `archive/<ts>/` 路径。后续所有 step 都用 `--prof-dir`（脚本自动推导 archive_dir），**不要拼路径字符串**。

## 端到端测试输入规范

如果本次会话是「端到端测试」（用户给姓名+机构+URL，没别的），遵守 [`../../END_TO_END_TEST.md`](../../END_TO_END_TEST.md)：
- 用户只给基础信息，不要找用户要更多
- 自主通过 MCP 获取 email / GS ID / OA ID / ORCID / 论文列表
- 自主决定降级路径（按本文件 §自主决策）
- 基础信息不够 → 记录 Harness 缺口到 `archive/<日期>_harness_缺口/`，回头优化 Harness

## 阶段 1 五步流程

1. **Phase A 身份锁定**：MCP 搜官网/GS/OA/ORCID → 交叉验证 → 写 `verified_ids.json` + `career_stages.json`（schema 见 `phase1-templates.md`）
2. **Phase B 数据采集**：`step2_gs.py` → `step3_openalex.py` → `step4_arxiv_id.py`（或 `step5_arxiv.py`）→ `step6_merge.py`
3. **Phase C 渲染**：`render_profile.py --prof-dir ...` 生成 `01_基础画像.md` 骨架
4. **AI 填充叙事**：用 Edit 替换 `<!-- AI 渲染：... -->` 占位符（详见 `phase1-anti-patterns.md`）
5. **verify 门控**：`verify_profile.py --prof-dir ...`，全部 [OK] 才能声称完成（详见 `phase1-recovery.md`）

## 自主决策：MCP 搜索 + 降级

**用户输入只有姓名+机构+官网 URL。其余信息（email、GS ID、论文列表）由你自主获取。**

### MCP 搜索策略（按此顺序）

1. **官网**：MCP fetch（Exa / Tavily）读 URL → 提取 email、履历、ORCID、研究方向
2. **Google Scholar**：MCP 搜 `"{英文名}" "{机构英文名}" Google Scholar` → 提取 GS ID
3. **OpenAlex**：MCP 搜 `"{英文名}" OpenAlex` → 提取 OA Author ID
4. **ORCID**：官网有就直接用，否则 MCP 搜 `"{英文名}" ORCID`
5. **arXiv 学科分类**：根据研究方向推断（如凝聚态 → `cond-mat.str-el`），参考 `references/01-data-sources.md`

**遇到 MCP 工具失败**：换另一个 MCP 工具（Exa → Tavily → Serper），不要反复重试同一个。具体工具选择见 `references/01-data-sources.md`。

### 数据源降级（自主决定）

| 失败情况 | 降级路径 |
|:--------|:--------|
| 官网打不开 | 跳过官网 fet ch，直接从 GS / OA / arXiv 推断身份 |
| GS 找不到 / 被封 | 走 OpenAlex + arXiv，画像开篇标注「未找到 GS profile，论文覆盖可能不完整」 |
| OA 找不到 | 只用 GS + arXiv |
| ORCID 没有 | 跳过 step4_arxiv_id.py，直接 step5_arxiv.py `au:` 搜索 |
| 所有 API 都失败 | 终止并报告，不假装跑通 |

**降级结果必须在 verified_ids.json 的 `verification.tier` 标注（T1/T2/T3/T4），并在画像 §9 验证来源列出来源 URL（缺失标 `[未找到]`）。**

### 不要做的事

- ❌ 找用户要更多信息（email、GS ID、JSON 草案）—— 你的任务是从基础信息出发自主获取
- ❌ 在 prompt 提示降级路径——按本页规则自主判断
- ❌ 评价导师（匹配度、推荐意见等）—— 客观描述，不评价
- ❌ 跳过 verify 就声称完成—— verify 9/9 必须通过

## 何时调用 Superpowers skills

按 `feedback-superpowers` 内存的规则：
- 任何「创新/设计」→ `brainstorming`
- 任何「bug/失败」→ `systematic-debugging`
- 任何「教学讲解」→ `teach-concept` / `simplify-topic`
- 任何「写论文」类比喻工作时 → 不要调用 Superpowers skills（pilot-test 是工程工具，不是论文写作）

## 硬约束速查

完整约束见 `phase1-core.md` §硬约束。最重要的 4 条：

1. **AI 不得修改论文表格**——表格由 `render_profile.py` 从 merged.json 生成，AI 只写表格前的叙事
2. **AI 不得做导师评价**——禁止「匹配度」「值得报考」「影响力大」等表述
3. **AI 必须用 Edit 而非 Write**——Write 会破坏 frontmatter、表格、格式
4. **必须通过 verify 门控才能声称完成**——verify 失败时按 `phase1-recovery.md` 的指引修复