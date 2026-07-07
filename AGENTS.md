# advisor-research-navigator AGENTS.md

## 一句话

`advisor-research-navigator` 是导师研究方向调研工具。用户输入 `姓名 + 机构路径 + 官网 URL`，主路径是 `Fact Pack -> Cognitive Blueprint -> 00-04 成品 -> 验证/自审 -> 回归与瘦身`。当前 V2 重心是先把 `quality-workbench/支撑方法/` 重构成能真正指导 `00-04` 的方法，再反修 M0 总方法，随后调整 `文档标准/`、真实样本、skill、verifier 和 harness。新窗口先读 `QUICKSTART.md` 和 `docs/上下文交接.md`；阶段 1 技术细节见 `src/phase1/pipeline.md`。当前文档设计以 `quality-workbench/README.md` 为入口，`docs/计划书.md` 只作历史设计参考。

## 目录角色

| 路径 | 用途 |
|:-----|:------|
| `src/phase1/` | 阶段 1 Python 脚本（phase1_init / step2_gs / step3_openalex / step4_arxiv_id / step5_arxiv / step6_merge / risk_gate / render_profile / verify_profile / utils） |
| `src/phase1/pipeline.md` | 阶段 1 技术执行文档（单一事实源） |
| `.agents/skills/` | Codex/其他 CLI Skill 入口（NTFS junction → `.claude/skills/`，同一份内容，不重复维护） |
| `.claude/skills/research-advisor/` | 当前 00-04 工作流入口、references、模板和验证脚本 |
| `quality-workbench/` | 当前 `00-04` 文档标准和支撑方法的设计工作台；根部只放 README，正文标准进 `文档标准/`，跨文档方法进 `支撑方法/` |
| `output/` | 导师画像产出 |
| `archive/` | 旧版存档（只写不读） |

## 当前工作重心

- 当前先重构四份支撑方法，顺序是 `S1 信息检索与筛查 -> S2 学习与认知原则 -> S3 学术品味与文稿设计 -> S4 可视化与理解`。S1 已按“资料获得正文资格”重构；继续工作时优先进入 S2，不要跳去改文档标准或样本。
- 支撑方法稳定后，回头反修 `quality-workbench/支撑方法/从资料堆到理解路径.md`。M0 现在只能当临时护栏，不可当成成熟总方法往下硬套。
- 等 S1-S4 和 M0 都稳定后，再调整 `quality-workbench/文档标准/00-04`。真实导师成品、`research-advisor`、模板、verifier 和 harness 排在文档标准之后。
- 方法文档必须从项目反复出现的痛点出发，说明参考资料怎样改变本项目判断、执行动作和停写条件。不要为了整齐凑“几类失败”“几条原则”。
- `quality-workbench/` 是当前设计源头，但未自动升格为正式 Harness。只有跨导师可复用、能稳定提高质量、且归属明确的结论，才在统一回收时进入正式 Harness。

## AI 协作路由与冲突消解

每次开始非小任务前，先写或在心里持有这组任务合同：

```text
当前层级：
本次目标：
输入和来源：
本次不碰：
完成条件：
验证方式：
人工审查边界：
```

层级只能选一个主层：`M0`、`S1-S4`、`D00-D04`、真实样本、project skill、global skill、verifier、harness、代码。一次只改当前层级；发现其他层也有问题时，写成后续回收，不顺手修改。

冲突按这个顺序消解：

1. 最新用户指令和本文件的硬约束决定当前任务范围。
2. 当前锁定层级的文件决定具体写法；例如重构 S2 时，以 S2 和已确认的 S1/M0 交接口为准。
3. `quality-workbench/` 的当前设计结论优先于旧模板、旧 `research-advisor` reference、旧 verifier 和 `docs/计划书.md`。
4. project skills 只提供工作方式和路由；如果 skill 里的历史流程与当前 workbench 冲突，记录冲突并按当前 workbench 执行。
5. 自动验证只证明格式、链接、禁用语、目录或 smoke。研究判断、论文路线、学习路径和图文必要性必须保留人工审查边界。

涉及调研、方法、论文路线、学习路径、可视化或 AI 协作规则时，先过“资料到判断”门：

```text
资料或来源：
它实际支撑什么：
它不支撑什么：
本项目吸收成什么判断或动作：
这会改变哪份文档、哪一步写作或哪条规则：
边界或不确定性：
```

写不出这组关系，参考资料不能进入正文主线。它可以留作工作备注，但不能装成方法依据。

## 硬约束

- 来源必标 URL，缺失标 `[未找到]`
- 不做导师评价（匹配度、推荐意见等）
- 重要改动前后按“Git 保存纪律”处理：先检查状态；达到可审查里程碑后提交或明确说明未提交原因。
- 导师调研、阶段 1-4 文档生成、阶段 2-4 质量修订必须先使用 `.claude/skills/research-advisor/`；上下文较长或换新窗口时先读 `docs/上下文交接.md`
- **`archive/` 目录是旧版存档，禁止读取或引用其中的任何内容**。存档仅供人工溯源。Agent 不得通过 Bash 或其他方式访问 archive/。
- archive 禁读指 Agent 不得手动打开、搜索、复制或引用历史/中间文件。脚本通过 `--prof-dir` / `ProfDirResolver` 读取当前 active `_internal/archive/<ts>` 不属于手动读取 archive；不要手动拼 archive 路径，也不要把脚本中间 JSON 当正文证据。
- 每次运行从头查所有 API。不使用任何缓存或历史数据。

## Skills 使用纪律

- 开始任务前按可用 skills 判断是否需要加载相关 skill；不要只惯性使用项目内 `research-advisor`。
- 中文长回复、文档讨论、`00-04` 成品、导师材料、学习向导、项目说明和 workbench 内容：必须使用全局 `human-readable-chinese-docs`，先保证读者路径、具体内容、证据边界和自然节奏，再润色。
- `chinese-style-guide` 只做中英文混排和排版辅助，不能替代 `human-readable-chinese-docs` 的可读性审查。
- 导师调研、`00-04` 文档、学习路径、证据规则和成品质量修订：必须使用 `.claude/skills/research-advisor/`。
- 讨论新结构、新流程、新规范、文档设计或 Harness 方向：先使用 `brainstorming`，形成设计判断后再改文件。
- 学习科学、教学设计、论文证据、可视化方法、agent workflow 或外部最佳实践拿不准：使用可用的全局研究类/学习类 skills，并优先查可靠来源。
- bug、验证失败或异常行为：使用 `systematic-debugging`。实现或修改脚本时，按风险使用 `test-driven-development`。
- 声称完成、修复、通过或准备提交前：遵循 `verification-before-completion`，先运行能证明当前声明的检查命令，再汇报结论。

## 模型使用约定

- 平时开发、研究判断、规则设计、论文路线分析、学习路径设计、阶段 2-4 写作或质量修订，默认使用当前高质量模型，避免低质量推理造成返工和项目漂移。
- 不再主动建议为了省额度切换到低成本模型。即使是批量性、重复性、低智力、可验证的机械工作，也优先由当前高质量模型执行并完成验证。
- 只有当用户明确要求使用低成本模型时，才把任务限制在边界清楚、有清单、有验证命令的机械工作；不得让低成本模型承担研究方向判断、证据强弱判断、论文主线重写、学习路线设计、长期规则修改或上下文交接。
- 低成本模型完成机械任务后，Agent 必须提醒用户切回高质量模型做内容审查、研究判断和下一步设计；如果发现验证失败、编码异常或上下文压缩风险，应立即停止低成本模型流程。

## Git 保存纪律

- 重要修改前先运行 `git status --short`，确认工作树状态，不覆盖用户改动；若已有未提交改动，先判断是否与当前任务相关。
- 每完成一个可审查里程碑后，再运行 `git status --short`，并按用户意图提交或明确说明“尚未提交”和原因。
- 如果用户要求保存、集成、收尾或切换任务，必须明确当前分支、未提交文件、是否已提交，以及提交哈希或未提交原因。
- 不得在汇报中暗示已经保存、集成或提交，除非实际完成 `git add` / `git commit` 并确认结果。
- 工作台讨论可以按阶段提交，例如完成一个文档标准、完成学习原则整理、完成一次统一回收。

## 反臃肿原则

- 不为每次小讨论新增长期 spec/plan/规则文件。只有能稳定提高 00-04 五份文档质量、能跨导师复用、且归属明确的规则才沉淀。
- 当前讨论期的规则归属：支撑方法、M0 和文档标准先进 `quality-workbench/`；当前状态进 `docs/上下文交接.md`；阶段 1 技术细节进 `src/phase1/pipeline.md`。等 S1-S4、M0 和 D00-D04 都稳定后，再统一回收进 `docs/计划书.md`、`.claude/skills/research-advisor/references/`、模板、verifier 或 tests。
- verifier 只做结构、来源、禁用语和格式 smoke，不做学术质量判断；模板只固定骨架，不替代检索和分析。
- 完成一个导师的 00-04 五份文档后，做一次轻量去重审计，清理或合并已经被正式规则取代的过程文档。
