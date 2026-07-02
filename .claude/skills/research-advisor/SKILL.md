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

### 第一步（必须）：初始化目录结构

用 `phase1_init.py` 创建标准目录，不要手动 mkdir 或拼路径：

```bash
python src/phase1/phase1_init.py \
  --university "中国科学院大学" \
  --institute "中科院物理所" \
  --department "超快物质科学中心" \
  --name "张鹏举"
```

脚本输出 `archive/<ts>/` 路径，后续步骤通过 `--archive-dir` 使用。

### 后续步骤

详见 `references/phase1.md`（广度搜索、身份锁定、数据采集、渲染叙事）。
技术执行细节（CLI 命令、数据格式、质量门）见 `src/phase1/pipeline.md`。
