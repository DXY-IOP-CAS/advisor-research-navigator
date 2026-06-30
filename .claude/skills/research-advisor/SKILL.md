---
name: research-advisor
description: >
  This skill should be used when the user wants to "调研导师"、"了解一个学者"、"分析导师的研究方向"、"生成导师画像"、"做选导师前期调研"。
  Trigger phrases include: "调研张鹏举"、"看看这个老师"、"分析某导师的研究"、"想了解××老师"、"这个导师适合我吗"。
  The skill runs a multi-stage pipeline: Stage 0 (shallow collect + user review + ID verification) and Stage 1 (deep profile with papers grouped by career stage) are documented.
  Stages 2-4 (domain trace, paper positioning, learning path) are under development.
---

# research-advisor

## 用途

本 skill 是导师研究方向调研工具的入口。用户输入导师姓名 + 机构 + 官网 URL（可选），工具执行四阶段流水线产出结构化文档。当前阶段 0/1 已实现，阶段 2/3/4 待设计。

## 阶段总览

| 阶段 | 产出文件 | 核心任务 | 人闸 | 状态 |
|:----:|:---------|:---------|:----:|:----:|
| 0 | 00_身份验证卡.md | 官网抓取 → 列调研计划给你审 → 确认后批量查 ID → 论文比对锁定身份 | 两次 | ✅ 已实现 |
| 1 | 01_基础画像.md | 全平台深调研，**全部论文按真实学术履历阶段分组（阶段名根据实际经历动态设定），含已发表+预印本**，9 节结构化画像 | 一次 | ✅ 已实现 |
| 2 | 02_领域脉络.md | 追溯子领域发展树和里程碑 | TBD | ❌ |
| 3 | 03_论文定位.md | 每篇论文在领域树上标注位置（阶段2的认知回环） | TBD | ❌ |
| 4 | 04_学习讲义.md | 从高数+线代到前沿的递进学习路径 | TBD | ❌ |

## 执行流程

用户首次调用（如 "调研张鹏举 中科院物理所 [URL]"），按以下决策树走：

```
检查 项目/导师/<姓名>/
├─ 没有目录或空 → 新调研，调起阶段 0（先浅收集→列计划→你审→再深入）
├─ 只有 00 卡且未确认 → 等你的 yes/modify/no
├─ 00 卡已确认，无 01 → 进入阶段 1
├─ 01 存在，无 02 → 阶段 2 未实现，告知用户
├─ 02 存在... → 类推
```

阶段 0 和阶段 1 的详细步骤写在 `references/00-phase.md`。本 SKILL.md 只做路由。

## 五份文件的递进关系

基础画像（阶段1）产出全部论文列表 → 领域脉络（阶段2）追溯子领域发展树 → **阶段2的认知反过来让阶段3的论文串联更有深度**（不是简单时间线排列，而是在"做了什么"的基础上讲清"为什么做"）→ 阶段4讲义从高数到前沿。每一份服务于下一份，阶段3回馈阶段2形成闭环。

## 阶段 0 核心设计（重要）

与一般全自动流程不同，阶段 0 中间有一步**人审**：

```
抓官网 → 学科识别 → 列出"我要查什么"给你审 → 确认后再批量查 → 论文比对 → 输出 → 停等yes
                         ↑
                    你确认链接和锚点无误
```

这不是"全自动查完让你确认"，而是让你先知道我要查什么、从哪些渠道查，确认锚点后再深入。

## 门控规则

- 阶段 0 产出后必须停（等你的 yes/modify/no）
- 阶段 0 中间有人闸——列出调研计划后需你确认再批量查
- 数据为空不报错，输出降级版标注"未找到"
- 只查一个导师。不批量

## 输出目录

```
项目/导师/<姓名>/
├── 00_身份验证卡.md
├── 01_基础画像.md
├── 02_领域脉络.md  [待开发]
├── 03_论文定位.md  [待开发]
└── 04_学习讲义.md  [待开发]
```

## 验证来源

- 计划书: `计划/计划书.md` v3.0
- OpenAlex: https://docs.openalex.org
- INSPIRE-HEP: https://github.com/inspirehep/rest-api-doc
- ArXiv Author ID: https://info.arxiv.org/help/author_identifiers.html
- ORCID: https://info.orcid.org/documentation/api-tutorials

**版本**: v2.0
**生成日期**: 2026-07-01
