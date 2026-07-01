# phase1 pipeline.md

**版本**：v4.0（精简索引版）

详细内容已拆到 `.claude/rules/` 目录下，按需加载：

| 文件 | 内容 |
|:-----|:------|
| [00-overview.md](/.claude/rules/00-overview.md) | 三阶段流程总览 + 核心原则 |
| [01-data-pipeline.md](/.claude/rules/01-data-pipeline.md) | 通用数据格式 + 每步 CLI + 阶段 C 渲染 |
| [02-quality-gates.md](/.claude/rules/02-quality-gates.md) | 每步 AI 检查清单 + 错误处理 |
| [03-archive.md](/.claude/rules/03-archive.md) | 输出结构 + 存档规则 + 已知限制 |

## 快速参考

```bash
# 全流程一键跑
python src/phase1/step2_gs.py {gs_id} -o 01_gs.json
python src/phase1/step3_openalex.py {oa_id} --email you@real.com -o 02_oa.json
python src/phase1/step5_arxiv.py "Name_English" -c "physics.atom-ph" -o 03_arxiv.json
python src/phase1/step6_merge.py 01_gs.json 02_oa.json 03_arxiv.json -o 04_merged.json
python src/phase1/render_profile.py 04_merged.json -o 01_基础画像.md --department "部门"
```

**依赖**：`pip install scholarly`。Python 3.10+。

## 版本记录（精简）

| 版本 | 变更 |
|:-----|:------|
| v4.0 | 精简为索引，详细内容拆到 `.claude/rules/` |
| v3.0 | 加 tests/pyproject（后删除，YAGNI） |
| v2.0 | 完整重写 |
