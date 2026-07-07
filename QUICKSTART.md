# QUICKSTART - advisor-research-navigator

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

不要从旧 quickstart、旧 e2e 记录或已删除的兼容脚本反推当前 workflow。它们只能作历史参考。

## 项目结构

```text
advisor-research-navigator/
├── src/phase1/                         # 阶段 1 Python 脚本
│   ├── phase1_init.py                  # 新导师目录初始化，写 _internal/latest.txt 和 seed.json
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
  --name "<中文名>" \
  --official-url "<导师官网 URL>"
```

后续统一使用脚本输出的 `prof_dir` 和 `--prof-dir` 参数。不要手动拼 `_internal/archive/<ts>`；官网 URL 已写入 `_internal/seed.json`，作为身份锁定和 Fact Pack 的起点。

`phase1_init.py` 只创建目录和 seed，不会采集论文。初始化后，先完成 Phase A 身份锁定和阶段配置：从 `_internal/seed.json` 读取官网 URL，检索官网、Google Scholar、OpenAlex 和 ORCID，交叉验证身份，并把 `00_verified_ids.json` 与 `career_stages.json` 写入当前 active `_internal/archive/<ts>/`。

不要从 `phase1_init.py` 直接跳到 `risk_gate.py`；执行阶段 1 时先按 `src/phase1/pipeline.md` 和 `phase1-core.md` 完成 Phase A，再运行 `step2_gs.py`、`step3_openalex.py`、`step4_arxiv_id.py` 或 `step5_arxiv.py`、`step6_merge.py`，最后运行风险门。

阶段 1 完成后：

1. `risk_gate.py --prof-dir "<prof_dir>"` 必须输出 `mode: standard`，否则按 `next_actions` 定向补证据或剔除噪声。
2. `render_profile.py --prof-dir "<prof_dir>" --department "<部门>"` 生成 `01_基础画像.md` 骨架。
3. AI 只填叙事占位符，不重写脚本生成的论文表格。
4. `verify_profile.py --prof-dir "<prof_dir>"` 通过后，再进入蓝图和 00/02/03/04。

阶段 2-4 先写 `_internal/blueprint.md`，再生成或修订成品文档。蓝图必须固定导师主线、目标论文、核心图、平台链路、学习桥、证据风险和可视化计划。

## 端到端回归

端到端回归只给三行最小输入：

```text
姓名：<中文名>
机构：<大学>/<学院或研究所>/<部门>
官网 URL：<导师官网 URL>
```

不要在 prompt 里附已知 GS ID、OpenAlex ID、ORCID、英文名、邮箱、论文列表、官网摘录、career_stages 草案、搜索关键词、命令顺序或修复提示。端到端回归的目的不是手把手带 AI 跑通，而是暴露 harness 缺口；如果执行 AI 觉得三行输入不够，先记录缺口并改 harness，不向用户索要额外学术线索。

每次回归记录写入 `docs/e2e/YYYY-MM-DD-<name>-minimal-prompt.md`，至少记录 `risk_gate.py` mode/reason/next_actions/metrics、补证据或剔除动作、`verify_profile.py`、`verify_phase_docs.py`、可视化/DOI smoke 结果，以及 smoke 之外仍需人工学术审查的身份、论文归属、核心图、平台链路和学习路径风险。

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
- archive 禁读指 Agent 不得手动打开、搜索、复制或引用历史/中间文件。脚本通过 `--prof-dir` / `ProfDirResolver` 读取当前 active `_internal/archive/<ts>` 不属于手动读取 archive；不要手动拼 archive 路径，也不要把脚本中间 JSON 当正文证据。
- 每次运行从头查 API 和来源，不把 archive 当缓存。
