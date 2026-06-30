---
name: research-advisor
description: >
  This skill should be used when the user wants to "调研导师"、"了解一个学者"、"分析导师的研究方向"、"生成导师画像"、"做选导师前期调研"。
  Trigger phrases include: "调研张鹏举"、"看看这个老师"、"分析某导师的研究"、"想了解××老师"、"这个导师适合我吗"。
  The skill coordinates a 4-stage pipeline that produces structured Markdown reports
  (identity card, profile, domain trace, paper positioning, learning path) for grad school applicants
  evaluating a specific research advisor.
---

# research-advisor（总调度 skill）

## 用途

本 skill 是**调度入口**——它本身不执行任何调研/检索/抓取动作。它的职责是：

1. 告诉 AI 整个项目的目标、四阶段流水线、产出文件位置
2. 根据用户输入和当前已产出的文件，决定下一步调起哪个子 skill
3. 维护阶段门控——不允许跳步、不允许绕过验证卡

## 工作模型：本 skill 只判断"下一步做什么"，执行交给子 skill

用户首次调用本 skill 时（命令如 `/research-advisor 张鹏举 中科院物理所 [URL]`），AI 必须遵循以下决策流程：

```
Step 1: 读取 `项目/导师/<姓名>/` 目录
  ├─ 完全空 → 这是新调研，进入阶段 0
  ├─ 只有 00_身份验证卡.md，且 user_invocable 还没确认 → 等用户确认
  ├─ 00 + 01 都有，但 02 没 → 进入阶段 2
  ├─ 00 + 01 + 02 都有，但 03 没 → 进入阶段 3
  └─ 00 + 01 + 02 + 03 都有，但 04 没 → 进入阶段 4

Step 2: 根据目标阶段调起子 skill：
  ├─ 阶段 0/1 → /profile-resolver
  ├─ 阶段 2 → /domain-trace
  ├─ 阶段 3 → /paper-locate
  └─ 阶段 4 → /learning-path
```

**禁止**：本 skill 直接执行 API 调用、抓取网页、生成画像。所有这些都由子 skill 完成。

## 四阶段全景

| 阶段 | 子 skill | 输入 | 产出文件 | 关键功能 |
|:----:|:--------|:-----|:---------|:---------|
| 0 | profile-resolver（含阶段 1） | 用户给的姓名/机构/URL | `00_身份验证卡.md` | 浅调研 → 用户确认 → 锁定学术 ID |
| 1 | profile-resolver | 确认的 ID | `01_基础画像.md` | 深调研，9 节结构化画像 |
| 2 | domain-trace | 阶段 1 画像+论文 | `02_领域脉络.md` | 子领域发展树+里程碑论文 |
| 3 | paper-locate | 阶段 2 框架 + 阶段 1 论文 | `03_论文定位.md` | 每篇论文在领域树上标注位置 |
| 4 | learning-path | 前三段全部产出 | `04_学习讲义.md` | 从高数+线代到前沿的递进路线 |

每阶段产出作为下一阶段输入，前一段错后一段全错——**阶段 0 的 ID 锁定是整个流水线的根**。

## 输出位置规范

```
项目/
└── 导师/
    └── <姓名>/                          # 每位导师独立目录
        ├── 00_身份验证卡.md
        ├── 01_基础画像.md
        ├── 02_领域脉络.md
        ├── 03_论文定位.md
        └── 04_学习讲义.md
```

frontmatter（YAML）统一键：`affiliation`（机构）、`department`（部门）、`tags`（方向）、`source_updated`（最新数据更新时间）、各 ID（orcid/openalex_id/arxiv_id/inspire_id/s2_id/google_scholar_url）。

## 门控规则（强制）

- 阶段 0 完成后必须输出 00_身份验证卡.md，然后**停下**，等用户输入 yes/no
- 用户没确认前**禁止**进入阶段 1
- 任何阶段产出后，AI 必须自检（信息有 URL、字段无缺失），不通过则不进入下一阶段
- 任何阶段如果出错（找不到人、API 全失败），**禁止报错退出**——给出降级提示让用户决策

## 永远不做什么

- 不做导师口碑/学生评价——避开争议
- 不替代学生做价值判断
- 不直接调用任何 API（那是子 skill 的活）
- 不读 `pilot-test/计划/工具设计.md` 或 `需求确认.md` 中的过期内容（v1 错误版），参考 `技术方案概述.md` v2+ 和本 skill 体系

## 验证来源

- Agent Skills 规范：https://agentskills.io/specification
- Claude Code Skills：https://code.claude.com/docs/en/skills
- Claude Skill 最佳实践：https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- INSPIRE-HEP REST API 文档：https://github.com/inspirehep/rest-api-doc
- OpenAlex API：https://docs.openalex.org
- arXiv Author Identifier：https://info.arxiv.org/help/author_identifiers.html
- ORCID Public API：https://info.orcid.org/documentation/integration-guide

**版本**：v1.0
**生成日期**：2026-06-30
