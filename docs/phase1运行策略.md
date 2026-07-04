# Phase 1 运行策略

Phase 1 只有一套 harness，两种运行策略。默认使用 `standard`；只有确定性风险门控要求时，才升级到 `conservative`。

## standard

适用于 Codex 或其它检索和推理能力较强的 worker。流程是：官网锁定身份，GS/OA/ORCID 交叉验证，跑三源采集和合并，然后执行 risk gate。不要为了“保险”重复多轮搜索。

```bash
python src/phase1/risk_gate.py --prof-dir "output/..."
```

输出 `mode: standard` 时，继续 render、AI 填充叙事、verify。

## conservative

适用于低质量搜索工具、弱模型，或 risk gate 报告 `mode: conservative_required` 的场景。conservative 不是重跑全部流程，而是针对 gate 给出的 `reason` 和 `next_actions` 补证据：

- 身份不稳：补官网、GS、OpenAlex、ORCID、机构主页之间的姓名/邮箱/论文指纹交叉验证。
- 单源论文比例过高：逐篇核查 OA/arXiv-only 论文是否属于该学者，不确定则剔除或标为已人工核查后再进入画像。
- GS baseline 异常：检查合并是否混入同名作者论文。
- 英文名或验证层级缺失：补来源；补不到就保留 `[未找到]` 并在画像和 e2e 记录里说明。

补搜后重新运行：

```bash
python src/phase1/risk_gate.py --prof-dir "output/..."
```

`reason` 说明为什么不能继续标准流程；`next_actions` 是执行清单。执行 AI 必须先完成或记录每条 `next_actions`，再决定是否渲染画像。无法完成的动作必须写入 e2e 记录和画像来源风险，不能静默跳过。

当行动清单涉及官网英文名、当前官网邮箱域或其它已由官方来源核实的身份字段时，不手动编辑 `_internal/archive`。使用受控脚本修正 active state：

```bash
python src/phase1/apply_identity_review.py \
  --prof-dir "output/..." \
  --display-name "中文名 (English Name)" \
  --official-email-domain "iphy.ac.cn" \
  --official-affiliation "当前官方机构" \
  --official-url "https://..." \
  --note "官方页面支持该身份修正"
```

该脚本只更新当前 active `00_verified_ids.json` 和 `04_merged.json`，并在 metadata 里记录官方 URL 和说明；它可用于修正官网已核实的英文名、当前邮箱域和当前机构，不修改原始 GS/OA/arXiv 采集文件。

当行动清单要求逐篇核查 OA/arXiv-only 论文时，先列出单源论文：

```bash
python src/phase1/risk_gate.py --prof-dir "output/..." --list-single-source
```

`single_source_oa_arxiv_papers` 输出只作为保守核查清单。执行 AI 需要逐篇用 DOI、题名、作者、机构和领域判断是否属于目标学者；明显同名噪声应剔除，不确定项标为人工核查。

剔除 DOI 必须走受控脚本，不手动改 active JSON：
```bash
python src/phase1/apply_paper_review.py \
  --prof-dir "output/..." \
  --exclude-doi "10.xxxx/xxxxx" \
  --reason "conservative review: ..." \
  --source-url "https://..."
```

该脚本只更新当前 active `04_merged.json`，重算 `statistics`，并在 `metadata.paper_review.excluded` 记录题名、DOI、作者、来源、剔除理由和核查 URL；它不修改原始 GS/OA/arXiv 文件。

## 记录要求

端到端测试记录必须写入 `docs/e2e/`，并包含：

- 使用策略：`standard` 或 `conservative`
- `risk_gate.py` 输出的 mode、reason、next_actions、metrics
- 是否触发补搜，以及补搜改动了哪些输入或中间结果
- verify 结果和仍需人工关注的内容风险
