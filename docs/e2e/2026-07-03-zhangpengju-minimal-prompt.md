# 2026-07-03 张鹏举 Phase 1 最小输入 E2E 记录

> 历史记录：本文件只用于追溯早期 Phase 1 回归暴露的问题，不是当前 workflow 入口，也不是最新待办清单。当前入口以 `QUICKSTART.md`、`docs/上下文交接.md`、`research-advisor/SKILL.md` 和 `src/phase1/pipeline.md` 为准。

## 目的

验证当前 phase1 harness 在真实最小输入下的行为，而不是给 agent 手把手提示。

## 输入

严格按当时的端到端测试规范（现已吸收进 `QUICKSTART.md`），只给 subagent 以下内容：

```text
跑阶段 1 端到端测试：
姓名：张鹏举 (Pengju Zhang)
机构：中国科学院大学 / 中科院物理研究所 / 超快物质科学中心
官网 URL：https://edu.iphy.ac.cn/?q=detail_teacher&id=6368
```

未提供 email、GS ID、OA ID、ORCID、论文列表、career_stages 草案、命令顺序或修复提示。

## Subagent 自报结果

subagent 报告阶段 1 端到端测试完成，并通过门控：

- 输出文件：`output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/01_基础画像.md`
- GS：成功，采集 56 篇，最终保留 GS 主源 54 篇
- OpenAlex：成功，采集 14 篇
- arXiv：ORCID feed 未绑定，降级姓名+分类搜索成功，采集 5 篇
- 合并/渲染后人工核查剔除 5 条单源 OA/arXiv 同名噪声
- `verify_profile.py --prof-dir ...` 输出 `[OK] 全部检查通过`

subagent 还报告了一个 harness 问题：

- `render_profile.py --prof-dir` 未显式传 `-o` 时，把 `01_基础画像.md` 写到了工作区根目录；subagent 后来显式传 `-o` 重新渲染到正确目录，并删除了临时文件。

## 主线程复核

主线程没有读取 `archive/` 或 `output/**/archive/**` 内容。复核只基于非 archive 文件和直接指定最终 Markdown 路径的 verify。

运行：

```powershell
python src\phase1\verify_profile.py "output\中国科学院大学\中科院物理研究所\超快物质科学中心\张鹏举\01_基础画像.md"
```

结果：`[OK] 全部检查通过`。

关键输出证据：

- `§1 姓名字段为中英混合格式` 通过
- `§1 邮箱字段无双 @` 通过
- `§9 验证来源表至少 1 行` 通过，实际 5 行
- `§9 验证来源不用列表格式` 通过
- `§9 验证来源不含未验证来源` 通过
- `单源 OA/arXiv 论文需人工核查` 通过，发现 0 行
- 论文表格存在 54 行

## 暴露出的 harness 缺陷

### H1. 机构路径命名不一致

当前 repo 同时出现两套路径：

- 旧路径：`output/中国科学院大学/中科院物理所/超快物质科学中心/张鹏举/`
- 本次 E2E 新路径：`output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/`

根因不是 subagent 随机发挥，而是文档本身不一致：

- 当时的端到端测试规范示例使用 `中科院物理研究所`
- `src/phase1/pipeline.md`、`.claude/skills/research-advisor/SKILL.md` 多处使用 `中科院物理所`
- `phase1_init.py` 只拼接用户输入，没有 canonicalization

影响：

- 同一导师可以被写到两个不同 output 路径。
- 后续 `latest.txt`、最终画像、历史产物会分叉。
- Agent 可能以为新路径是新导师/新机构，造成重复运行和重复归档。

建议：

- 增加 `src/phase1/institution_aliases.py` 或在 `phase1_init.py` 内做最小 canonicalization。
- 至少先把 `中科院物理研究所` 规范成 `中科院物理所`。
- 同步更新端到端测试规范，避免测试输入和 canonical 路径冲突。该规范后来已吸收进 `QUICKSTART.md`。

### H2. `render_profile.py --prof-dir` 输出路径逻辑有 bug

subagent 自报：未显式传 `-o` 时，`render_profile.py --prof-dir` 会把 `01_基础画像.md` 写到工作区根目录。

主线程代码复核：

```python
parser.add_argument("--output", "-o", default="01_基础画像.md", help="输出路径")
...
if args.prof_dir and not args.output:
    args.output = os.path.join(args.prof_dir, "01_基础画像.md")
```

由于 argparse 已经给了默认值 `"01_基础画像.md"`，`not args.output` 永远为 false，所以 `--prof-dir` 不会自动改写 output 路径。

影响：

- skill 文档说 `render_profile.py --prof-dir ...` 会生成到 prof 根目录。
- 实际脚本若不显式传 `-o`，会写到当前工作区根目录。
- subagent 这次靠发现并补救才通过，不代表 harness 本身一致。

建议：

- 把 `--output` 默认值改成 `None`。
- 若传了 `--prof-dir` 且未传 `--output`，自动写 `prof_dir/01_基础画像.md`。
- 若既没有 `--prof-dir` 也没有 `--archive-dir`，再回退到当前目录 `01_基础画像.md`。
- 加单元测试覆盖 `render_profile.py --prof-dir` 默认输出路径。

### H3. E2E 成功依赖 subagent 人工判断，但过程未结构化留痕

subagent 报告“人工核查剔除了 5 条单源 OA/arXiv 同名噪声”，但当前最终 Markdown 只能看到剔除后的结果，看不到核查依据。

影响：

- verify 能确认“没有未核查单源 OA/arXiv 行”，但不能复核剔除是否正确。
- 下一次模型可能剔除不同论文，缺少可比较的 audit trail。

建议：

- 在最终画像或一个非 archive 的 run report 中记录“剔除论文标题 + 剔除原因 + 核查方式”。
- 不要求把完整中间数据搬到非 archive，但至少要留下最终决策摘要。

## 历史结论

这次最小输入 E2E 说明 harness 已经比之前有效：

- 新 verify 能迫使 subagent 处理单源 OA/arXiv 噪声，而不是静默放过。
- §1 姓名、邮箱、§9 表格等格式问题没有再次出现。
- 最终 Markdown 直接 verify 通过。

但它也暴露了三个工程一致性问题：

1. 机构路径 canonicalization 缺失。
2. `render_profile.py --prof-dir` 默认输出路径与文档承诺不一致。
3. 单源论文剔除决策缺少结构化留痕。

当前状态：H2 已通过 `render_profile.py --prof-dir` 默认输出到导师目录和对应测试修复；H3 已通过 `risk_gate.py --list-single-source`、`apply_paper_review.py` 和证据核对表机制吸收。H1 仍是单独的机构别名设计问题；当前活跃样本使用 `中科院物理研究所`，不要根据本历史记录自行改成 `中科院物理所`。
