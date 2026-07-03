# pilot-test AGENTS.md

## 一句话

导师研究方向调研工具。用户输入姓名+机构+官网URL → 四阶段流水线产出 Markdown 文档。详见 `src/phase1/pipeline.md`（技术细节）和 `docs/计划书.md`（设计决策）。

## 目录角色

| 路径 | 用途 |
|:-----|:------|
| `src/phase1/` | 阶段 1 Python 脚本（step2_gs / step3_openalex / step5_arxiv / step6_merge / render_profile / verify_profile / archive_previous / utils） |
| `src/phase1/pipeline.md` | 阶段 1 技术执行文档（单一事实源） |
| `.agents/skills/` | Codex/其他 CLI Skill 入口（NTFS junction → `.claude/skills/`，同一份内容，不重复维护） |
| `output/` | 导师画像产出 |
| `archive/` | 旧版存档（只写不读） |

## 硬约束

- 来源必标 URL，缺失标 `[未找到]`
- 不做导师评价（匹配度、推荐意见等）
- 每次重要改动前 commit
- 导师调研、阶段 1-4 文档生成、阶段 2-4 质量修订必须先使用 `.claude/skills/research-advisor/`；上下文较长或换新窗口时先读 `docs/上下文交接.md`
- **`archive/` 目录是旧版存档，禁止读取或引用其中的任何内容**。存档仅供人工溯源。Agent 不得通过 Bash 或其他方式访问 archive/。
- 每次运行从头查所有 API。不使用任何缓存或历史数据。

## 模型使用约定

- 平时开发、研究判断、规则设计、论文路线分析、学习路径设计、阶段 2-4 写作或质量修订，默认使用当前高质量模型，避免低质量推理造成返工和项目漂移。
- 当任务是批量性、重复性、低智力、可验证的机械工作（如 Markdown 表格统一、裸 URL 转引用键、引用键查漏、章节标题批量检查、运行 smoke verifier 并汇报结果）时，Agent 应先提醒用户可以切换到低成本模型执行。
- 低成本模型只适合执行边界清楚、有清单、有验证命令的机械任务；不得让低成本模型承担研究方向判断、证据强弱判断、论文主线重写、学习路线设计或长期规则修改。
- 低成本模型完成机械任务后，Agent 应提醒用户切回高质量模型做内容审查、研究判断和下一步设计。
