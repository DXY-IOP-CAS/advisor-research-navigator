# pilot-test CLAUDE.md

新窗口第一步：读 `QUICKSTART.md`。

---

## 一句话

导师研究方向调研工具。用户输入姓名+机构+官网URL → 四阶段流水线产出 Markdown 文档到 `output/<机构>/<部门>/<姓名>/`。

## 项目状态

- **阶段 1**：已实现，详见 `src/phase1/pipeline.md`
- **阶段 2-4**：待设计

## 可用 Skills

`.claude/skills/` 下已安装以下技能。**启动任何任务前阅读 `using-superpowers`**，它会指引如何调用其他技能。

| Skill | 何时使用 |
|:------|:---------|
| `using-superpowers` | 任何任务开始前（必读） |
| `brainstorming` | 需求不明确时，先厘清再动手 |
| `writing-plans` | 任务复杂度 > 5 分钟时，先拆计划 |
| `test-driven-development` | 修改代码逻辑时，先写测试 |
| `systematic-debugging` | 排查 bug 时 |
| `verification-before-completion` | 声称完成前验证 |

## 关键规则

- 来源必标 URL，缺失标 `[未找到]`
- 每次重要改动前 commit
- 每次改动后跑 `python src/phase1/run_all.py`（如存在）
