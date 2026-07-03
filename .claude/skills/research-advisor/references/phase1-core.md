# 阶段 1 核心步骤与叙事规范

> L2 必读。触发阶段 1 时由 SKILL.md 加载。L3 文件（templates / anti-patterns / recovery）按需读取。

## Phase A — 身份锁定与数据准备

### A.1 初始化目录

`phase1_init.py` 已经自动建 `output/<路径>/archive/<ts>/` 并写 `latest.txt`。**不要手动 mkdir**。

### A.2 广度搜索

按以下顺序用 MCP 搜（不要漏步骤、也不要乱序）：

1. **官网**：MCP fetch 读 → 提取姓名、英文名、机构、email、ORCID、履历
2. **Google Scholar**：优先用官网/ORCID/OpenAlex 取得的英文名搜 `"英文名" + "机构英文名" + Google Scholar` → 提取 GS profile URL 和 GS ID
3. **OpenAlex**：MCP 搜"姓名 + OpenAlex" 或用 ORCID 反查 → 提取 OA Author ID
4. **ORCID**：官网有就直接用，否则 MCP 搜"姓名 + ORCID"
5. **交叉验证**：邮箱域名匹配（T1）/ ORCID 匹配（T2）/ 论文指纹（T3）/ 全降级（T4）

### A.3 写两份 JSON 到 archive/<ts>/

- `00_verified_ids.json`：所有 ID + 验证层级（schema 见 `phase1-templates.md`）
- `career_stages.json`：从官网履历提取的学术阶段（schema 见 `phase1-templates.md`）

### A.4 阶段划分的核心规则

**论文按履历分组的目的不是按年份归档，而是看每个职业阶段的研究方向演变。**

每个（时间区间 + 机构 + 职位）变化是一个独立阶段。机构没变但职位升了、方向变了，也要拆开。

---

## Phase B — 三源数据采集

按以下顺序执行（脚本接收 `--prof-dir`，自动推导 `archive-dir` 和 `output` 路径）：

```bash
python src/phase1/step2_gs.py {gs_id} --prof-dir "output/..."
python src/phase1/step3_openalex.py {oa_id} --prof-dir "output/..."
python src/phase1/step4_arxiv_id.py {orcid} --name "姓_名" --prof-dir "output/..."  # ORCID 精确匹配，零噪声
# step4 失败时回退：python src/phase1/step5_arxiv.py "姓_名" -c "physics.atom-ph" --prof-dir "output/..."
python src/phase1/step6_merge.py --prof-dir "output/..."
python src/phase1/risk_gate.py --prof-dir "output/..."
```

**采信优先级**：GS > OA > arXiv。多源重合以 GS 标题为准，OA 补充 DOI/期刊/作者，arXiv 补充预印本。`risk_gate.py` 决定是否必须从 standard 升级到 conservative；如果输出 `mode: conservative_required`，按 reason 做定向补搜后重跑 gate。

### 数据源细节

需要调 API 时读 `references/01-data-sources.md`（限速、降级、噪声过滤）。

---

## Phase C — 渲染骨架

```bash
python src/phase1/render_profile.py --prof-dir "output/..." --department "..."
```

脚本自动生成 §1 身份标识、§2 学术履历表、§4 论文分组表格、§8 数据质量统计。其余节（§3 方向 / §5 合作 / §6 公开 / §7 引用 / §9 来源）留 `<!-- AI 渲染：... -->` 占位符。

**AI 工作**：用 Edit 替换占位符。详见 `phase1-anti-patterns.md`。

---

## Phase D — verify 门控

```bash
python src/phase1/verify_profile.py --prof-dir "output/..."
```

9 项检查全部 [OK] 才能声称完成。失败处理见 `phase1-recovery.md`。

---

## 叙事规范

### 目标读者

画像的读者是物理专业**大二/大三本科生**。义务：

- 每个专业术语首次出现时用 1 句话解释（例："高次谐波产生（HHG）——用强激光打气体/固体，产生极紫外脉冲"）
- 每篇论文叙事回答"为什么要做这个"（背景）和"这发现了什么"（发现），不只是报标题
- 分层递进：先研究背景和技术原理，再讲具体发现

### 姓名格式

统一格式：`中文名 (英文名)`，如 `王示例 (Shili Wang)`。端到端输入只给中文名，英文名必须从官网、GS、ORCID 或 OpenAlex 自主提取；找不到则标 `[未找到]`，不要向用户索要。

### §2 学术履历

由 `render_profile.py` 从 `career_stages.json` 自动生成。**AI 不要再手写 §2**。如果脚本没有生成，说明 `career_stages.json` 缺字段（institution/position/direction），补字段后重新渲染。

### §3 研究方向

1 段总体概述 + 3-4 个具体方向（中英文关键词）。客观描述，不做评价。

### §4 论文分组叙事

- 每个 `### 4.x` 阶段表格前必须有 1-2 句叙事段落
- 叙事说明该阶段的研究主题和方向变化，不报菜名
- 论文表格由脚本生成，AI 不得修改表格行数或内容
- 禁写 `代表性论文`、`以下见完整列表`、`如下图` 等字样

### §5-§7

- §5 合作网络：高频合作者（姓名 + 机构 + 合作方向）+ 来源超链接
- §6 公开信息：新闻/采访/讲座等 + 超链接
- §7 引用影响力：总引用、h-index、近 3 年统计

---

## 硬约束（禁止）

- 禁止评价导师（匹配度、推荐意见、"值得报考"、"热点方向"、"影响力大"等）
- 禁止在论文表格内写叙事——叙事写在表格前
- 禁止改写论文表格内容
- 每篇论文必须保留脚本生成的超链接列（DOI/arXiv）
- 全部论文逐一列出，不得省略
- 缺失字段标 `[未找到]`
- 所有外部信息标注来源超链接
- 表格列数固定 6 列（#/年份/标题/期刊/引用/来源），AI 不得增减

---

## arXiv 精确匹配（Phase B 推荐）

如果 Phase A 获取到 ORCID，Phase B 优先用 `step4_arxiv_id.py`（精确匹配、零噪声），失败时回退到 `step5_arxiv.py` 的 `au:` 搜索。
