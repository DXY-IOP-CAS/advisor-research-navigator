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
  --name "张鹏举"
```

脚本输出 `archive/<ts>/` 路径。后续所有 step 都用 `--prof-dir`（脚本自动推导 archive_dir），**不要拼路径字符串**。

## 阶段 1 五步流程

1. **Phase A 身份锁定**：MCP 搜官网/GS/OA/ORCID → 交叉验证 → 写 `verified_ids.json` + `career_stages.json`（schema 见 `phase1-templates.md`）
2. **Phase B 数据采集**：`step2_gs.py` → `step3_openalex.py` → `step4_arxiv_id.py`（或 `step5_arxiv.py`）→ `step6_merge.py`
3. **Phase C 渲染**：`render_profile.py --prof-dir ...` 生成 `01_基础画像.md` 骨架
4. **AI 填充叙事**：用 Edit 替换 `<!-- AI 渲染：... -->` 占位符（详见 `phase1-anti-patterns.md`）
5. **verify 门控**：`verify_profile.py --prof-dir ...`，全部 [OK] 才能声称完成（详见 `phase1-recovery.md`）

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