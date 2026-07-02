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
- **`archive/` 目录是旧版存档，禁止读取或引用其中的任何内容**。存档仅供人工溯源。Agent 不得通过 Bash 或其他方式访问 archive/。
- 每次运行从头查所有 API。不使用任何缓存或历史数据。
