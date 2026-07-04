# QUICKSTART - 导师研究方向调研工具

## 一句话

用户只提供 `姓名 + 机构路径 + 官网 URL`。项目主路径是：

```text
最小输入 -> Fact Pack -> Cognitive Blueprint -> 00-04 成品 -> 验证/自审 -> 回归与瘦身
```

阶段 1 技术细节见 `src/phase1/pipeline.md`；整体设计和取舍见 `docs/计划书.md`；当前状态和下一步见 `docs/上下文交接.md`。

## 新窗口启动

1. 读 `AGENTS.md`，尤其是 archive 禁读、每次从头查 API、先用 research-advisor skill。
2. 读 `docs/上下文交接.md`，确认当前分支、已完成里程碑和下一步。
3. 涉及导师调研或 00-04 文档时，读 `.claude/skills/research-advisor/SKILL.md`。
4. 只有执行阶段 1 技术步骤时，再读 `src/phase1/pipeline.md` 和相关 references。

不要从旧 quickstart、旧 e2e 记录或 `run.py` 反推当前 workflow。它们只能作历史或兼容参考。

## 项目结构

```text
pilot-test/
├── src/phase1/                         # 阶段 1 Python 脚本
│   ├── phase1_init.py                  # 新导师目录初始化，写 _internal/latest.txt
│   ├── pipeline.md                     # 阶段 1 技术执行文档
│   ├── step2_gs.py / step3_openalex.py # 论文采集
│   ├── step4_arxiv_id.py / step5_arxiv.py
│   ├── step6_merge.py                  # 多源合并
│   ├── risk_gate.py                    # standard / conservative 风险门
│   ├── render_profile.py               # 01 骨架生成
│   └── verify_profile.py               # 01 机械验证
├── .claude/skills/research-advisor/     # 00-04 工作流入口、模板和验证脚本
├── docs/                               # 计划书、交接、历史 e2e 记录
├── output/<大学>/<学院所>/<部门>/<姓名>/
│   ├── 00_材料导读.md
│   ├── 01_基础画像.md
│   ├── 02_领域地图.md
│   ├── 03_论文路线.md
│   ├── 04_学习向导.md
│   └── _internal/                      # latest、archive、blueprint、evidence 等内部状态
└── archive/                            # 旧版存档，只写不读
```

导师成品根目录只能暴露 `00-04` 五份 Markdown 和 `_internal/`。

## 常规执行骨架

从三行输入初始化目录：

```bash
python src/phase1/phase1_init.py \
  --university "<大学>" \
  --institute "<学院或研究所>" \
  --department "<部门>" \
  --name "<中文名>"
```

后续统一使用脚本输出的 `prof_dir` 和 `--prof-dir` 参数。不要手动拼 `_internal/archive/<ts>`。

阶段 1 完成后：

1. `risk_gate.py --prof-dir "<prof_dir>"` 必须输出 `mode: standard`，否则按 `next_actions` 定向补证据或剔除噪声。
2. `render_profile.py --prof-dir "<prof_dir>" --department "<部门>"` 生成 `01_基础画像.md` 骨架。
3. AI 只填叙事占位符，不重写脚本生成的论文表格。
4. `verify_profile.py --prof-dir "<prof_dir>"` 通过后，再进入蓝图和 00/02/03/04。

阶段 2-4 先写 `_internal/blueprint.md`，再生成或修订成品文档。蓝图必须固定导师主线、目标论文、核心图、平台链路、学习桥、证据风险和可视化计划。

## 验证

常用验证命令：

```bash
python src/phase1/verify_profile.py --prof-dir "<prof_dir>"
python .claude/skills/research-advisor/scripts/verify_phase_docs.py --prof-dir "<prof_dir>"
python .claude/skills/research-advisor/scripts/verify_mermaid_render.py --prof-dir "<prof_dir>"
python .claude/skills/research-advisor/scripts/verify_source_metadata.py --prof-dir "<prof_dir>"
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s .claude/skills/research-advisor/tests -p "test_*.py" -v
git diff --check -- . ':(exclude)archive/**' ':(exclude)output/**/archive/**'
```

这些验证只代表机械 smoke 通过，不代表学术质量最终通过。学术质量仍来自证据核查、蓝图、自审和人工反馈。

## 硬约束

- 来源必须可追溯；缺失写 `[未找到]`；弱推断写 `需人工复核`。
- 不做导师评价，不写匹配度、推荐申请或是否值得报考。
- 不读取或引用 `archive/` 与 `output/**/archive/**`。
- 每次运行从头查 API 和来源，不把 archive 当缓存。
- `run.py` 只是旧兼容/本地调试捷径，不是新端到端主入口。
