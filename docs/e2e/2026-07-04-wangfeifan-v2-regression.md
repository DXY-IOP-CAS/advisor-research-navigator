# 汪非凡 V2 回归样本检查记录

## 目的

本记录用于检查非张鹏举导师样本是否能直接作为 V2 harness 回归样本。检查对象是当前工作区中已有的汪非凡试跑目录；本次不把该目录纳入提交，也不读取或引用 `archive/` 内容。

## 输入线索

| 项目 | 内容 |
|:---|:---|
| 姓名 | 汪非凡 |
| 机构路径 | 中国科学院大学 / 中科院物理研究所 / 超快物质科学中心 |
| 官网 URL | https://edu.iphy.ac.cn/?q=detail_teacher&id=6009 |
| 来源 | `docs/batches/超快物质科学中心导师清单.md` |

## 执行检查

运行：

```powershell
python .claude\skills\research-advisor\scripts\verify_phase_docs.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡"
```

结果失败，失败类型如下：

| 失败类型 | 说明 |
|:---|:---|
| 成品根目录不干净 | 根目录存在 `latest.txt` 和 `archive/` |
| 缺少内部证据表 | 缺 `_internal/evidence/` 关键判断证据核对表 |
| 成品文档不完整 | 缺 `00_材料导读.md`、`02_领域地图.md`、`03_论文路线.md`、`04_学习向导.md` |
| 只能算 Phase 1 试跑 | 当前目录只有 `01_基础画像.md`，不能代表 V2 四阶段标准品 |

## 判断

这个现有目录不能作为 V2 回归样本直接验收。它只证明早期 Phase 1 试跑产物尚未迁移到 V2 目录契约和四阶段成品结构。

下一步如果要使用汪非凡作为非张鹏举回归样本，应从官网 URL 和机构路径重新走 research-advisor 流程：先用 `_internal/` 目录契约生成或迁移阶段 1，再补 `00/02/03/04`、证据表和可视化理解构件，最后跑完整验证门。不得把旧 `archive/` 内容当作证据来源。

## 2026-07-04 重新试跑状态

已用官网 URL 和机构路径重新初始化汪非凡 V2 目录，并完成 Phase 1 的三源采集与合并。当前未把该目录纳入提交，因为成品文档尚未形成，只能作为回归试跑状态。

运行：

```powershell
python src\phase1\risk_gate.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡"
```

当前结果：

| 项目 | 结果 |
|:---|:---|
| mode | `conservative_required` |
| total_papers | 39 |
| gs_baseline | 29 |
| single_source_oa_arxiv | 10 |
| single_source_oa_arxiv_ratio | 25.64% |
| gs_oa_overlap | 25 |
| verification_tier | T2 |

触发原因：

| 原因 | 下一步处理 |
|:---|:---|
| `English name missing from professor/verified_ids name` | 从官网英文名补回身份锁定 JSON 或渲染输入，保持 `中文名 (English Name)` 格式。 |
| `email domain mismatch: professor=mat.ethz.ch, verified=iphy.ac.cn` | 判断是否为 Google Scholar 滞后邮箱；需用官网当前邮箱、ORCID、OpenAlex 和 DOI 论文指纹交叉说明，不能直接忽略。 |
| `single-source OA/arXiv ratio 25.6% exceeds 10.0%` | 逐篇核查 OA-only/arXiv-only 论文；无法核实时剔除或标为人工核查后再进入画像。 |
| `merged paper count 39 exceeds GS baseline 29 by more than 20%` | 检查是否混入同名作者或 OpenAlex 消歧扩张，重点核查超出 GS baseline 的论文。 |

本轮发现一个 harness 执行缺口：`phase1-core.md` 已要求 `step4_arxiv_id.py --prof-dir`，但脚本本身此前不支持；同时 ORCID 精确匹配失败后的 `step5_arxiv.py` 回退搜索也不支持 `--prof-dir`。已通过 TDD 补上两者入口，避免执行 AI 在 Phase B 手动拼 `_internal/archive` 路径。

## 2026-07-04 风险门行动清单补强

`risk_gate.py` 已补充 `next_actions` 输出，避免小白执行 AI 只看到风险原因却不知道下一步怎么补证据。当前汪非凡样本输出的行动清单是：

| next_action | 处理状态 |
|:---|:---|
| 补官网英文名，保持 `中文名 (English Name)` 格式；补不到则在画像和 e2e 记录里写 `[未找到]`。 | 待处理 |
| 核查邮箱域名不一致是否来自 GS 滞后或跨机构履历；用官网当前邮箱、ORCID、OpenAlex 和论文指纹说明。 | 待处理 |
| 逐篇核查 OA/arXiv-only 论文是否属于该学者；不确定则剔除，或标为已人工核查后再进入画像。 | 待处理 |
| 检查合并结果是否混入同名作者论文，重点核查超出 GS baseline 的 OpenAlex/arXiv 单源论文。 | 待处理 |

这次改动只增强 harness 可执行性，不代表汪非凡样本已经通过 Phase 1。下一步必须按上表完成保守核查，再决定是否渲染 `01_基础画像.md`。

## 2026-07-04 官方身份字段修正

官方来源使用物理所研究生教育网汪非凡页面：`https://edu.iphy.ac.cn/?q=detail_teacher&id=6009`。该页面列出中文名“汪非凡”、当前邮箱 `ffwang@iphy.ac.cn`，并在代表性论文列表中使用 `Feifan Wang` 作为英文作者名。

执行：

```powershell
python src\phase1\apply_identity_review.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡" --display-name "汪非凡 (Feifan Wang)" --official-email-domain iphy.ac.cn --official-url "https://edu.iphy.ac.cn/?q=detail_teacher&id=6009" --note "IOP graduate profile lists 汪非凡, current email ffwang@iphy.ac.cn, and representative papers authored as Feifan Wang."
```

重跑：

```powershell
python src\phase1\risk_gate.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡"
```

结果仍为 `mode: conservative_required`，但已消除：

| 已消除风险 | 说明 |
|:---|:---|
| `English name missing from professor/verified_ids name` | active state 已使用 `汪非凡 (Feifan Wang)` |
| `email domain mismatch: professor=mat.ethz.ch, verified=iphy.ac.cn` | active merged profile 已使用官网当前邮箱域 `iphy.ac.cn`，GS 的 ETH 邮箱域视作滞后线索，不作为当前邮箱输出 |

剩余风险：

| 剩余原因 | 下一步 |
|:---|:---|
| `single-source OA/arXiv ratio 25.6% exceeds 10.0%` | 逐篇核查 10 篇 OA/arXiv-only 论文 |
| `merged paper count 39 exceeds GS baseline 29 by more than 20%` | 检查超出 GS baseline 的论文是否混入同名作者 |

因此当前仍不能渲染 Phase 1 成品。
