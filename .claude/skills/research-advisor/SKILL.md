---
name: research-advisor
description: >
  Run Phase 1 (paper collection + structured profile) for a professor.
  Use when the user wants to "调研导师", "了解一个学者",
  "分析导师的研究方向", "生成导师画像", or "做选导师前期调研".
---

# research-advisor

## 用途

用户输入导师姓名 + 机构 + 官网 URL → 全自动三阶段流 → `01_基础画像.md`。

数据采集策略详见 `src/phase1/pipeline.md`（单一技术事实源）。

## 阶段总览

| 阶段 | 产出 | 状态 |
|:----:|:-----|:----:|
| 1 基础画像 | `01_基础画像.md` | ✅ 已实现 |
| 2 领域脉络 | `02_领域脉络.md` | ❌ 待设计 |
| 3 论文定位 | `03_论文定位.md` | ❌ 待设计 |
| 4 学习讲义 | `04_学习讲义.md` | ❌ 待设计 |

## 阶段 1 执行

详见 `references/phase1.md`（AI 叙事规范 + 硬约束）。
技术执行细节（CLI 命令、数据格式、质量门）见 `src/phase1/pipeline.md`。
