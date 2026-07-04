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
| 补官网英文名，保持 `中文名 (English Name)` 格式；补不到则在画像和 e2e 记录里写 `[未找到]`。 | 已处理：`apply_identity_review.py` 写入 `汪非凡 (Feifan Wang)` |
| 核查邮箱域名不一致是否来自 GS 滞后或跨机构履历；用官网当前邮箱、ORCID、OpenAlex 和论文指纹说明。 | 已处理：active state 使用官网当前域名 `iphy.ac.cn`，GS 的 ETH 域名视作滞后线索 |
| 逐篇核查 OA/arXiv-only 论文是否属于该学者；不确定则剔除，或标为已人工核查后再进入画像。 | 已处理：`apply_paper_review.py` 剔除 10 条单源风险项 |
| 检查合并结果是否混入同名作者论文，重点核查超出 GS baseline 的 OpenAlex/arXiv 单源论文。 | 已处理：重跑 gate 后 total=29，与 GS baseline=29 一致 |

这次改动只增强 harness 可执行性，不代表汪非凡样本已经通过 Phase 1。当前保守核查已完成，下一步可以渲染 `01_基础画像.md` 并继续验证叙事质量。

## 2026-07-04 官方身份字段修正

官方来源使用物理所研究生教育网汪非凡页面：`https://edu.iphy.ac.cn/?q=detail_teacher&id=6009`。该页面列出中文名“汪非凡”、当前邮箱 `ffwang@iphy.ac.cn`，并在代表性论文列表中使用 `Feifan Wang` 作为英文作者名。

执行：

```powershell
python src\phase1\apply_identity_review.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡" --display-name "汪非凡 (Feifan Wang)" --official-email-domain iphy.ac.cn --official-affiliation "中国科学院物理研究所 / 超快物质科学中心" --official-url "https://edu.iphy.ac.cn/?q=detail_teacher&id=6009" --note "IOP graduate profile lists 汪非凡, current email ffwang@iphy.ac.cn, current IOP appointment, and representative papers authored as Feifan Wang."
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

## 2026-07-04 单源论文清单

为避免手动读取 `_internal/archive`，已给 `risk_gate.py` 增加 `--list-single-source` 明细输出。

运行：

```powershell
python src\phase1\risk_gate.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡" --list-single-source
```

待逐篇核查清单：

| 年份 | 标题 | DOI / arXiv | 作者摘要 | 初步判断 |
|:---|:---|:---|:---|:---|
| 2023 | Preparation of Fe-Lignin/Geopolymer Porous Microspheres for Catalytic Degradation of Dye Wastewater | https://doi.org/10.1021/acs.iecr.3c00404 | Feifan Wang; Jianli Tan; Yan He; Quan Ye; Xuemin Cui | 待核查，题名与当前超快/非线性光谱方向不一致 |
| 2024 | Active Beam Steering Enabled by Photonic-Crystal Surface-Emitting Laser | https://doi.org/10.1021/acsnano.3c09793 | Mingjin Wang; Feifan Wang; Jingxuan Chen; Wenzhen Liu; ... | 待核查，题名疑似光子器件方向 |
| 2021 | Observation of miniaturized bound states in the continuumwith ultra-high quality factors | https://doi.org/10.21203/rs.3.rs-381924/v1 | Zihao Chen; Xuefan Yin; Jicheng Jin; Zhao Zheng; ... | 待核查，预印本 DOI，需核作者 |
| 2025 | Low-loss grating coupler enabled by unidirectional guided resonance through band inversion | https://doi.org/10.1016/j.optcom.2025.131978 | Haoran Wang; Yi Zuo; Yuefeng Hu; Zixuan Zhang; Feifan Wang; Xuefan Yin; Chao Peng | 待核查，题名疑似集成光子方向 |
| 2025 | Author response for "Wrinkles in 2D TMD Heterostructures: Unlocking Enhanced Hydrogen Evolution Reaction Catalysis" | https://doi.org/10.1039/d5ta00681c/v2/response1 | Kailiang Ren; Feifan Wang; Tianyang Liu; Huasong Qin; Jing Yu | 待核查，疑似作者回应条目，不应直接进入论文表 |
| 2023 | Ultra-small-size microcavity with high quality factor utilizing bound state in the continuum | https://doi.org/10.1117/12.2691303 | Yi Zuo; Xinyi Zhou; Zihao Chen; Feifan Wang; Chao Peng | 待核查，会议论文，需核作者 |
| 2023 | Nonlinear THz Control of the Lead Halide Perovskite Lattice - Experimental data | https://doi.org/10.5281/zenodo.7825059 | Maximilian Frenzel; Marie Cherasse; J. Urban; Feifan Wang; ... | 待核查，可能是有效数据集而非论文 |
| 2022 | The impact of green finance on the value of Chinese photovolatic enterprises in the context of COVID-19–based on the research of listed photovoltaic enterprises | https://doi.org/10.1201/9781003203704-19 | Feifan Wang | 待核查，题名疑似经管方向同名噪声 |
| 2021 | CCDC 1886888: Experimental Crystal Structure Determination | https://doi.org/10.5517/ccdc.csd.cc21bgc7 | Yongping Fu; Matthew P. Hautzinger; Ziyu Luo; Feifan Wang; ... | 待核查，晶体结构数据条目，不应直接当论文 |
| 2021 | CCDC 1888368: Experimental Crystal Structure Determination | https://doi.org/10.5517/ccdc.csd.cc21d03l | Yongping Fu; Matthew P. Hautzinger; Ziyu Luo; Feifan Wang; ... | 待核查，晶体结构数据条目，不应直接当论文 |

下一步应建立受控的论文核查/剔除机制，而不是手动改 `04_merged.json`。

## 2026-07-04 受控剔除与风险门回归

已新增 `src/phase1/apply_paper_review.py`，用于在 conservative 模式下按 DOI 剔除已核查的单源风险项。脚本只更新当前 active `04_merged.json`，重算 `statistics`，并把剔除记录写入 `metadata.paper_review.excluded`；不修改原始 GS/OA/arXiv 采集文件。

执行：
```powershell
python src\phase1\apply_paper_review.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡" --source-url "https://edu.iphy.ac.cn/?q=detail_teacher&id=6009" --reason "conservative review: OA/arXiv-only item is same-name noise, response/data/crystal-structure record, or not cross-supported by Google Scholar; see docs/e2e/2026-07-04-wangfeifan-v2-regression.md" --exclude-doi "10.1021/acs.iecr.3c00404" --exclude-doi "10.1021/acsnano.3c09793" --exclude-doi "10.21203/rs.3.rs-381924/v1" --exclude-doi "10.1016/j.optcom.2025.131978" --exclude-doi "10.1039/d5ta00681c/v2/response1" --exclude-doi "10.1117/12.2691303" --exclude-doi "10.5281/zenodo.7825059" --exclude-doi "10.1201/9781003203704-19" --exclude-doi "10.5517/ccdc.csd.cc21bgc7" --exclude-doi "10.5517/ccdc.csd.cc21d03l"
```

结果：
```text
paper_review: excluded 10 papers
```

重跑风险门：
```powershell
python src\phase1\risk_gate.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡" --list-single-source
```

结果：
| 项目 | 结果 |
|:---|:---|
| mode | `standard` |
| total_papers | 29 |
| gs_baseline | 29 |
| single_source_oa_arxiv | 0 |
| single_source_oa_arxiv_ratio | 0.0 |
| gs_oa_overlap | 25 |
| verification_tier | T2 |
| single_source_oa_arxiv_papers | none |

判断：汪非凡 Phase 1 当前数据已从 conservative 风险状态回到 standard，可以进入 `render_profile.py`。这只说明身份和论文合并风险门通过，不代表后续 `01_基础画像.md` 叙事质量或 00/02/03/04 已完成。

## 2026-07-04 Phase 1 渲染与验证

渲染前发现 active `04_merged.json` 的机构字段仍继承 Google Scholar 的旧 ETH Zurich 信息。已通过 TDD 扩展 `apply_identity_review.py`，增加 `--official-affiliation`，使官方当前机构能进入 active state，而不是只在最终 Markdown 手改。

重新执行身份修正后渲染：
```powershell
python src\phase1\render_profile.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡" --department "超快物质科学中心"
```

脚本输出：
```text
Profile written: output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡\01_基础画像.md (29 papers, 5 stages)
```

随后只替换 `<!-- AI 渲染：... -->` 叙事占位符和 §9 来源表，没有改动论文表格行。验证命令：
```powershell
python src\phase1\verify_profile.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡"
```

结果：
```text
[OK] 全部检查通过
```

判断：汪非凡 Phase 1 `01_基础画像.md` 已通过机械 smoke。当前仍不是完整 V2 标准品，因为 `00_材料导读.md`、`02_领域地图.md`、`03_论文路线.md`、`04_学习向导.md` 和 `_internal/evidence/` 尚未完成。

## 2026-07-05 V2 四阶段补齐与验证

已继续把汪非凡作为非张鹏举回归样本推进到完整 V2 成品结构。新增或补齐：

| 文件 | 状态 | 说明 |
|:---|:---|:---|
| `00_材料导读.md` | 已补齐 | 包含阅读顺序、引用符号说明、起步讨论入口、文件定位和使用边界 |
| `02_领域地图.md` | 已补齐 | 使用领域定位表、路径速览表和证据/复核表解释当前方向 |
| `03_论文路线.md` | 已补齐 | 使用问题链矩阵解释 2D-OKE、Kerr、极化子、软声子和 THz 控制论文关系 |
| `04_学习向导.md` | 已补齐 | 从高数、线代、普物接到波动、量子、固体、非线性光学、目标论文、核心图和平台链路 |
| `_internal/evidence/key_claims.md` | 已补齐 | 覆盖身份锁定、领域定位、论文路线、学习路线和平台链路关键判断 |

可视化策略采用表格、矩阵和平台链路表，不强行使用 Mermaid。这样可以避免长条流程图导致字号过小或维护成本过高，同时满足“可视化理解构件”质量门。

验证命令：

```powershell
python .claude\skills\research-advisor\scripts\verify_phase_docs.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡"
python src\phase1\verify_profile.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡"
python .claude\skills\research-advisor\scripts\verify_mermaid_render.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡"
python .claude\skills\research-advisor\scripts\verify_source_metadata.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\汪非凡"
```

结果：

| 验证门 | 结果 |
|:---|:---|
| `verify_phase_docs.py` | `[OK] phase docs deterministic checks passed` |
| `verify_profile.py` | `[OK] 全部检查通过` |
| `verify_mermaid_render.py` | `[OK] 未找到 Mermaid 代码块，渲染门跳过` |
| `verify_source_metadata.py` | `[OK] DOI source metadata checks passed` |

判断：汪非凡已从“旧目录失败样本”推进为一个非张鹏举 V2 回归样本，机械 smoke 已通过。剩余风险仍是学术质量风险：Fig. 1 / Fig. 4 的具体子图顺序、官网 in revision / in preparation 方向、固体 HHG 与阿秒方向的公开论文链，都需要后续人工读原文和更新来源继续复核。
