---
name: research-advisor
description: >
  This skill should be used when the user wants to "调研导师"、"了解一个学者"、
  "分析导师的研究方向"、"生成导师画像"、"做选导师前期调研"。
  Trigger phrases include: "调研张鹏举"、"看看这个老师"、"分析某导师的研究"、
  "想了解××老师"、"这个导师适合我吗"。
  The skill runs Phase 1 (paper collection + structured profile with papers
  grouped by career stage). Stages 2-4 are under development.
  Data collection uses Google Scholar (via scholarly) as primary source
  and OpenAlex for metadata enrichment.
---

# research-advisor

## 用途

用户输入导师姓名 + 机构 + 官网 URL → 全自动三阶段流 → `01_基础画像.md`。
数据收集策略：scholarly 取 GS 论文列表（主源）、OpenAlex 补元数据（DOI/期刊/作者）、arXiv 补预印本。

详见 `docs/计划书.md` 第 2 章和 `src/phase1/pipeline.md`（技术落地）。

## 阶段总览

| 阶段 | 产出文件 | 核心任务 | 状态 |
|:----:|:---------|:---------|:----:|
| 1 | `01_基础画像.md` | 广域搜+身份确认 → GS 论文 → OA 元数据 → arXiv → 合并 → 9 节画像 | ✅ 已实现 |
| 2 | `02_领域脉络.md` | 追溯子领域发展树和里程碑 | ❌ 待设计 |
| 3 | `03_论文定位.md` | 每篇论文在领域树上标注位置 | ❌ 待设计 |
| 4 | `04_学习讲义.md` | 从高数+线代到前沿的递进学习路径 | ❌ 待设计 |

**说明**：无人工闸。阶段 A（广域搜索+身份确认）由 AI 全自动完成，不需要用户确认。

## 执行流程

用户输入姓名 + 机构 + 官网 URL 后，直接进入阶段 1。

阶段 1 的详细步骤写在 `references/phase1.md`。本 SKILL.md 只做路由。

## 输出目录

```
output/<机构>/<部门>/<姓名>/
├── 01_基础画像.md               # 最终画像
├── latest.txt                    # 指向最新存档
└── archive/<timestamp>/          # 中间产物存档（仅供溯源）
    ├── 00_verified_ids.json
    ├── 01_gs.json
    ├── 02_oa.json
    ├── 03_arxiv.json
    └── 04_merged.json
```

每次运行全新查询所有 API。archive 不缓存旧数据。

## 验证来源

- 计划书: `docs/计划书.md` v4.0
- 调研报告: `docs/调研_学者分析工具全景.md`
- OpenAlex: https://docs.openalex.org
- Zhao & Chen (2025) OpenAlex 消歧精度: https://arxiv.org/html/2502.11610v2
- Zheng et al. (2025) OpenAlex 中国论文覆盖: https://doi.org/10.1002/asi.70013

**版本**: v4.0
**生成日期**: 2026-07-01
