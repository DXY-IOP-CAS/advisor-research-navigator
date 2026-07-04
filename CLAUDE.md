# pilot-test CLAUDE.md

## 一句话

导师研究方向调研工具。用户输入 `姓名 + 机构路径 + 官网 URL`，项目通过 `Fact Pack -> Cognitive Blueprint -> 00-04 成品 -> 验证/自审` 产出 Markdown 文档。详见 `AGENTS.md`（当前硬约束）、`docs/计划书.md`（设计决策）、`docs/上下文交接.md`（当前状态）和 `src/phase1/pipeline.md`（阶段 1 技术细节）。

## 目录角色

| 路径 | 用途 |
|:-----|:------|
| `src/phase1/` | 阶段 1 Python 脚本（step2_gs / step3_openalex / step5_arxiv / step6_merge / render_profile / verify_profile / archive_previous / utils） |
| `src/phase1/pipeline.md` | 阶段 1 技术执行文档（单一事实源） |
| `.agents/skills/` | Codex/其他 CLI Skill 入口（NTFS junction → `.claude/skills/`） |
| `.claude/skills/research-advisor/` | research-advisor Skill 入口 |
| `output/` | 导师画像产出 |
| `archive/` | 旧版存档（只写不读） |

## 硬约束

- 来源必标 URL，缺失标 `[未找到]`
- 不做导师评价（匹配度、推荐意见等）
- 每次重要改动前 commit
- 导师调研、阶段 1-4 文档生成、阶段 2-4 质量修订必须先使用 `.claude/skills/research-advisor/`
- **`archive/` 目录是旧版存档，禁止读取或引用其中的任何内容**。存档仅供人工溯源。Agent 不得通过 Bash 或其他方式访问 archive/。
- 每次运行从头查所有 API。不使用任何缓存或历史数据。
