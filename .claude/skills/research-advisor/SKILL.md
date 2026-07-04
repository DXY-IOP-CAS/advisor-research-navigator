---
name: research-advisor
description: >
  Run the professor research-direction workflow from official identity locking
  through four Markdown deliverables. Use when the user asks to 调研导师,
  了解学者, 分析导师研究方向, 生成导师画像, run Phase 1, write or verify
  01_基础画像.md, 02_领域地图.md, 03_论文路线.md, 04_学习向导.md,
  or build phase 2-4 documents that connect a professor's current institution,
  research direction, papers, and student learning path.
---

# research-advisor

## 核心契约

新导师运行时，用户输入只需要：

```text
姓名：<中文名>
机构：<大学> / <学院或研究所> / <部门>
官网 URL：<教授主页链接>
```

不要要求用户提供英文名、邮箱、Google Scholar ID、OpenAlex ID、ORCID、论文列表或 JSON 草稿。这些信息必须从来源中发现。最终画像姓名仍写成 `中文名(English Name)`；如果未找到英文名，写 `[未找到]` 并记录来源缺口。

五份成品文档是一条认知阶梯，不是互不相干的报告：

0. `00_材料导读.md`：回答“这套材料如何读，引用符号如何理解，五份文档怎样互相支撑”。
1. `01_基础画像.md`：回答“老师是谁、资料是否可靠、履历和论文集合是什么”。
2. `02_领域地图.md`：回答“老师当前处在哪个领域，这个领域是什么，老师的位置在哪里”。
3. `03_论文路线.md`：回答“老师在当前方向具体做什么，相关论文之间如何构成研究路线”。
4. `04_学习向导.md`：回答“学生如何从近似空白一步步学到能读懂当前前沿和相关论文”。

第一性原理：学生真正缺的不是资料堆叠，而是一条从陌生到理解导师当前研究的认知路径。任何阶段如果只是为了填章节、拼贴前文或展示检索结果，都应停下来重新界定任务。

新端到端基线不以旧 phase、旧模板或旧 verifier 为中心。主路径是：

```text
最小输入 -> Fact Pack -> Cognitive Blueprint -> 00-04 成品 -> 证据/图示/自审 -> 回归与瘦身
```

`Fact Pack` 负责锁定身份、履历、论文集合和风险；`Cognitive Blueprint` 负责在写成品前固定导师主线、目标论文、核心图、平台链路、学习路径、证据风险和可视化计划；`00-04` 成品只能消费蓝图和新检索证据，不能把“填满模板”误认为完成理解。

每位导师在写 `02-04` 前必须维护 `_internal/blueprint.md`。它不是过程日志，而是认知设计合同，至少包含：读者起点、导师当前方向一句话、目标论文及选择理由、核心图或图组、平台链路、课程到论文的学习桥、证据风险、每份文档的可视化计划。蓝图薄弱时先继续检索和核证，不要继续润色正文。

V2 基线默认执行 AI 是小白、读者也是小白。每份成品文档必须自包含：说明本文解决什么问题、为什么要这样读、读完应获得什么能力；关键术语和缩写首次出现时必须展开；不能假设读者已经读过项目规则或其他导师材料。不要把“为什么这么读”的认知框架只写在 `00_材料导读.md` 或项目文档里。

不闭门造车。凡是研究判断、学习路径、证据标准、可视化或 harness 设计拿捏不准，先调研官方文档、公开 skills、同类项目、论文或领域资料，再决定是否吸收。站在巨人肩膀上扬长避短，但不生搬硬套；不能为了实现某个技术而做技术。

长时迭代或目标模式下，每个里程碑只解决一类问题：先判断问题归属，再做最小有效改动，最后验证、提交并更新 `docs/上下文交接.md`。只有跨导师可复用、能降低幻觉或能提升学生理解质量的规则才沉淀到 harness；单个导师的表达问题先改成品，不要为每次小反馈新增长期规则文件。

可视化服务理解，不服务装饰。不要把所有内容强行画成 Mermaid 流程图；领域定位优先层级树或定位表，论文路线优先矩阵表，学习向导优先课程-能力-论文桥接表，只有真实流程或平台链路才优先用小型 Mermaid。

## 首个动作

新建阶段一时，用用户提供的机构路径初始化导师目录。不要手工创建输出目录。

```bash
python src/phase1/phase1_init.py \
  --university "<大学>" \
  --institute "<学院或研究所>" \
  --department "<部门>" \
  --name "<中文名>" \
  --official-url "<教授主页链接>"
```

后续步骤全部使用脚本打印出的 `prof_dir`。`phase1_init.py` 会把最小输入写入 `_internal/seed.json`；官网 URL 不是聊天临时信息，而是 Fact Pack 起点。使用 `--prof-dir` 参数，不要手动拼接 `output/` 或 `archive/` 路径。项目规则把 `archive/` 标为只写不读，agent 不得检查或引用其中内容。

如果导师目录已经存在，先从用户给出的路径或当前 `output/` 路径定位活跃 `prof_dir`。不要把旧输出或存档当证据。

## 路由

只读取当前任务需要的参考文件：

| 任务 | 读取 |
|:--|:--|
| `00_材料导读.md` | `references/phase0-material-guide.md`, `references/evidence-rules.md`, `references/quality-gates.md` |
| Phase 1 / `01_基础画像.md` | `references/phase1-core.md`; add `phase1-templates.md`, `phase1-anti-patterns.md`, `phase1-recovery.md`, or `01-data-sources.md` only when needed |
| Phase 2 / `02_领域地图.md` | `references/phase2-field-map.md`, `references/evidence-rules.md`, `references/quality-gates.md` |
| Phase 3 / `03_论文路线.md` | `references/phase3-paper-position.md`, `references/evidence-rules.md`, `references/quality-gates.md` |
| Phase 4 / `04_学习向导.md` | `references/phase4-learning-guide.md`, `references/evidence-rules.md`, `references/quality-gates.md` |
| 认知蓝图 / E2E 主路径 | 本文件“端到端基线” + `references/evidence-rules.md`, `references/quality-gates.md` |
| 确定性 smoke | run `python .claude/skills/research-advisor/scripts/verify_phase_docs.py --prof-dir "<prof_dir>"` |
| DOI 来源元数据 smoke | run `python .claude/skills/research-advisor/scripts/verify_source_metadata.py --prof-dir "<prof_dir>"` when network is available |

`assets/templates/` 提供 `blueprint/00/02/03/04` 的章节骨架。执行 AI 可以把 `assets/templates/blueprint.md` 复制为导师目录下的 `_internal/blueprint.md`，再基于证据填充；但蓝图模板只是脚手架，不是证据、不是结论，也不能替代检索、核证和认知判断。`01_基础画像.md` 不走 Markdown 模板，而由 `render_profile.py` 从 active Phase 1 状态生成骨架，AI 只替换叙事占位符。模板不是内容质量，不能把填满模板误认为完成理解。

导师成品目录根部只放 `00_材料导读.md`、`01_基础画像.md`、`02_领域地图.md`、`03_论文路线.md`、`04_学习向导.md` 和 `_internal/`。`latest.txt`、archive、中间 JSON、证据核对表和图源文件都属于 `_internal/`，不得裸露在导师根目录。

## 阶段一流程

1. 读取 `references/phase1-core.md`。
2. 用官网、Google Scholar、OpenAlex、ORCID 和跨来源论文指纹锁定身份。
3. 需要 schema 细节时读取 `references/phase1-templates.md` 并创建必需 JSON。
4. 按 `phase1-core.md` 的顺序运行 Phase B 脚本。
5. 运行 `python src/phase1/risk_gate.py --prof-dir "<prof_dir>"`。只有输出 `mode: standard` 才继续标准流程；如果输出 `mode: conservative_required`，按原因做定向补检，再重跑 gate。
6. 渲染：`python src/phase1/render_profile.py --prof-dir "<prof_dir>" --department "<部门>"`。
7. 只填叙事占位符。编辑叙事前读取 `references/phase1-anti-patterns.md`。
8. 验证：`python src/phase1/verify_profile.py --prof-dir "<prof_dir>"`。失败时读取 `references/phase1-recovery.md`，修复后重跑。
9. 端到端测试记录写入 `docs/e2e/YYYY-MM-DD-<name>-minimal-prompt.md`。

## 阶段二到四流程

1. 从已验证的 `01_基础画像.md` 出发。把“按履历阶段分组的论文”当作方向变化假设，而不是最终解释。
2. 先写或更新 `_internal/blueprint.md`。蓝图必须把导师主线、目标论文、核心图、平台链路、学习桥、证据风险和可视化计划说清楚；否则暂停写作，继续检索官方页面、论文、综述、课程或图源。
3. 每个阶段都做 fresh search。阶段一、蓝图和前序文档是可靠输入源，但不能替代当前阶段的信息检索、筛选和分析。
4. 严格按 `02 -> 03 -> 04` 推进。后一个阶段必须显式消费前一个阶段和蓝图，但不能简单复述。
5. 阶段二先建立当前领域地图；阶段三深入导师当前研究内容和论文群内部逻辑；阶段四把目标前沿倒推成学习路径。
6. 弱推断标 `需人工复核`；来源缺失写 `[未找到]`。
7. 领域理解薄、方向转折证据不足、论文关系不清、核心图无法核对或学习桥像通用课程表时，暂停写作并继续检索。不要用顺滑但空泛的文字补洞。
8. 写作或修改阶段文档后运行确定性验证器；有网络时再运行 DOI 来源元数据 smoke，修正 `[FAIL] DOI title mismatch`。
9. 完成一位导师后做轻量去重审计：被蓝图、skill 或 verifier 正式吸收的临时过程说明不再扩散成新规则文件。

## 硬约束

- 来源 URL 必须可追溯；缺失来源写 `[未找到]`。
- 不评价导师，不写匹配度、推荐意见或是否应该申请。
- 阶段一不要修改脚本生成的论文表格；表格来自 `merged.json`。
- 阶段一不要整篇重写，只替换占位叙事。
- 不手动读取 `archive/`；只用活跃 `output/` 路径和 `--prof-dir` 工具。
- 确定性 smoke 通过不等于学术质量通过；它只检查结构、来源标记和禁用语。
- 只有请求的验证器通过，并且剩余内容风险被明确说明，才能说完成。
