---
name: research-advisor
description: >
  This skill should be used when the user wants to "调研导师"、"了解一个学者"、"分析导师的研究方向"、"生成导师画像"、"做选导师前期调研"。
  Trigger phrases include: "调研张鹏举"、"看看这个老师"、"分析某导师的研究"、"想了解××老师"、"这个导师适合我吗"。
  The skill runs a multi-stage pipeline: Stage 0/1 (identity verification + profile) is the only stage currently implemented.
  Stages 2-4 (domain trace, paper positioning, learning path) are under development.
---

# research-advisor

## 用途

本 skill 是导师研究方向调研工具的入口。用户输入导师姓名 + 机构 + 官网 URL（可选），工具执行四阶段流水线产出结构化文档。当前仅阶段 0/1 实现（身份验证 + 基础画像）。

## 阶段总览

| 阶段 | 产出文件 | 核心任务 | 状态 |
|:----:|:---------|:---------|:-----|
| 0 | 00_身份验证卡.md | 浅调研锁定学术 ID，用户确认身份 | ✅ 已实现 |
| 1 | 01_基础画像.md | 全平台深调研，9 节结构化画像 | ✅ 已实现 |
| 2 | 02_领域脉络.md | [开发中] | ❌ |
| 3 | 03_论文定位.md | [开发中] | ❌ |
| 4 | 04_学习讲义.md | [开发中] | ❌ |

## 执行流程

用户首次调用（如 `/research-advisor 张鹏举 中科院物理所 [URL]`），按以下决策树走：

```
检查 项目/导师/<姓名>/
├─ 没有目录或空 → 新调研，调起阶段 0
├─ 只有 00 卡且未确认 → 等用户确认
├─ 00 卡已确认，无 01 → 进入阶段 1
├─ 01 存在，无 02 → 阶段 2 未实现，告知用户
├─ 02 存在... → 类推
```

阶段 0 和阶段 1 的详细执行步骤写在 `references/00-phase.md`。本 SKILL.md 只做路由。

## 输出目录

```
项目/导师/<姓名>/
├── 00_身份验证卡.md
├── 01_基础画像.md
├── 02_领域脉络.md  [待开发]
├── 03_论文定位.md  [待开发]
└── 04_学习讲义.md  [待开发]
```

## 门控规则

- 阶段 0 产出后必须停，用户输入 yes 后才能进阶段 1
- 数据为空不报错，输出降级版标注"未找到"
- 只查一个导师。不批量

## 验证来源

- OpenAlex: https://docs.openalex.org
- INSPIRE-HEP: https://github.com/inspirehep/rest-api-doc
- ArXiv Author ID: https://info.arxiv.org/help/author_identifiers.html
- ORCID: https://info.orcid.org/documentation/api-tutorials
- 计划书: https://github.com/DXY/pilot-test/blob/main/计划/计划书.md

**版本**: v1.0
**生成日期**: 2026-06-30
