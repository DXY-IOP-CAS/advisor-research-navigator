# pilot-test AGENTS.md

## 一句话

导师研究方向调研工具。用户输入 `姓名 + 机构路径 + 官网 URL`，主路径是 `Fact Pack -> Cognitive Blueprint -> 00-04 成品 -> 验证/自审 -> 回归与瘦身`。当前 V2 重心是用学习科学、证据可靠性和新手理解质量来打磨 `00-04` 五份成品标准，而不是继续堆 workflow。新窗口先读 `QUICKSTART.md` 和 `docs/上下文交接.md`；阶段 1 技术细节见 `src/phase1/pipeline.md`，设计决策见 `docs/计划书.md`。

## 目录角色

| 路径 | 用途 |
|:-----|:------|
| `src/phase1/` | 阶段 1 Python 脚本（phase1_init / step2_gs / step3_openalex / step4_arxiv_id / step5_arxiv / step6_merge / risk_gate / render_profile / verify_profile / utils） |
| `src/phase1/pipeline.md` | 阶段 1 技术执行文档（单一事实源） |
| `.agents/skills/` | Codex/其他 CLI Skill 入口（NTFS junction → `.claude/skills/`，同一份内容，不重复维护） |
| `.claude/skills/research-advisor/` | 当前 00-04 工作流入口、references、模板和验证脚本 |
| `quality-workbench/` | 当前讨论 `00-04` 文档标准、学习与认知原则、图文设计和章节逻辑的临时工作台；不是最终成品或正式 Harness 规则 |
| `output/` | 导师画像产出 |
| `archive/` | 旧版存档（只写不读） |

## 当前工作重心

- 先讨论成品质量，再反推 Harness。当前重点是把 `00-04` 设计成面向新手的学习脚手架：有主线、有阅读顺序、有读后自检、有来源核查、有合适的理解构件。
- 讨论阶段优先把可复用结论沉淀到 `quality-workbench/`，等五份文档标准讨论清楚后，再统一回收进成品、模板、skill reference、verifier 或计划书。
- 学习与认知原则先看 `quality-workbench/学习与认知原则.md`。成品中应自然解释“为什么这样读、这样做”，但不要把教育学术语堆给学生。
- `quality-workbench/` 中的内容未自动升格为长期规则。只有跨导师可复用、能稳定提高质量、且归属明确的结论，才在统一回收时进入正式 Harness。

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
- 规则唯一归属：设计原因进 `docs/计划书.md`；执行细节进 `.claude/skills/research-advisor/references/`；确定性检查进 `scripts/`；当前状态进 `docs/上下文交接.md`；阶段 1 技术细节进 `src/phase1/pipeline.md`。
- verifier 只做结构、来源、禁用语和格式 smoke，不做学术质量判断；模板只固定骨架，不替代检索和分析。
- 完成一个导师的 00-04 五份文档后，做一次轻量去重审计，清理或合并已经被正式规则取代的过程文档。
