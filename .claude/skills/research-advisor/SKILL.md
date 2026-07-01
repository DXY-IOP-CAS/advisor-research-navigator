---
name: research-advisor
description: >
  This skill should be used when the user wants to "调研导师"、"了解一个学者"、"分析导师的研究方向"、"生成导师画像"、"做选导师前期调研"。
  Trigger phrases include: "调研张鹏举"、"看看这个老师"、"分析某导师的研究"、"想了解××老师"、"这个导师适合我吗"。
  The skill runs Phase 1 (paper collection + structured profile with papers grouped by career stage). Stages 2-4 (domain trace, paper positioning, learning path) are under development.
  Data collection uses Google Scholar as primary source and OpenAlex for metadata enrichment.
---

# research-advisor

## 用途

本 skill 是导师研究方向调研工具的入口。用户输入导师姓名 + 机构 + 官网 URL（可选），工具执行四份文档流水线。当前阶段 1 已实现，阶段 2/3/4 待设计。数据收集策略：GS 做主源（论文列表）、OpenAlex 做元数据补充（DOI/期刊/作者），详见 `计划/计划书.md` 第 2.1.2 节。

## 阶段总览

| 阶段 | 产出文件 | 核心任务 | 状态 |
|:----:|:---------|:---------|:----:|
| 1 | `01_基础画像.md` | 官网抓身份 → GS 搜论文列表 → OA 补元数据 → arXiv 预印本 → 同名过滤 → 按履历分组 → 9 节画像 | ✅ 已实现 |
| 2 | `02_领域脉络.md` | 追溯子领域发展树和里程碑 | ❌ 待设计 |
| 3 | `03_论文定位.md` | 每篇论文在领域树上标注位置 | ❌ 待设计 |
| 4 | `04_学习讲义.md` | 从高数+线代到前沿的递进学习路径 | ❌ 待设计 |

**说明**：阶段 0（身份验证）已删除。用户输入姓名 + 机构 + 官网 URL 已足够唯一确定导师。

## 执行流程

用户输入姓名 + 机构 + 官网 URL 后，直接进入阶段 1：

```
检查 output/导师/<姓名>/
├─ 没有目录 → 新调研，调起阶段 1
├─ 01 存在，无 02 → 阶段 2 未实现，告知用户
├─ 02 存在... → 类推
```

阶段 1 的详细步骤写在 `references/00-phase.md`。本 SKILL.md 只做路由。

## 四份文件的递进关系

基础画像（阶段1）产出全部论文列表 → 领域脉络（阶段2）追溯子领域发展树 → 阶段2的认知反过来让阶段3的论文串联更有深度（不是简单时间线排列，而是讲清"为什么做"）→ 阶段4讲义从高数到前沿。每一份服务于下一份，阶段3回馈阶段2形成闭环。

## 核心规则

- 数据为空不报错，输出降级版标注"未找到"
- GS profile 不存在时降级到 OpenAlex（覆盖 ≤ 50%）
- 只查一个导师。不批量

## 输出目录

```
output/导师/<姓名>/
├── 01_基础画像.md
├── 02_领域脉络.md  [待开发]
├── 03_论文定位.md  [待开发]
└── 04_学习讲义.md  [待开发]
```

## 验证来源

- 计划书: `计划/计划书.md` v3.3
- 调研报告: `计划/调研_学者分析工具全景.md`
- OpenAlex: https://docs.openalex.org
- Zhao & Chen (2025) OpenAlex 消歧精度: https://arxiv.org/html/2502.11610v2
- Zheng et al. (2025) OpenAlex 中国论文覆盖: https://doi.org/10.1002/asi.70013

**版本**: v3.0
**生成日期**: 2026-07-01
