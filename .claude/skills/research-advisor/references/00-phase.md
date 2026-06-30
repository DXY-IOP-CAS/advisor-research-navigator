# 阶段 1 执行步骤

本文件被 `../SKILL.md` 在阶段 1 时读取。内容对应计划书 2.2 节。

**注意**：阶段 0 已删除。用户输入姓名 + 机构 + 官网 URL 即可唯一确定导师，不需要单独的身份验证步骤。直接进入信息检索。

---

## 阶段 1：深调研 + 基础画像

### Step 1: 抓官网 + 学科识别

用 Bash（curl）或 MCP fetch 读用户给的 URL。提取：
- 姓名（中文 + 拼音）
- 职称
- 邮箱
- 研究方向关键词
- 论文标题列表（后续做合著者白名单）

容错：404 就停，让用户确认 URL。缺字段就标缺失。

学科识别：

```bash
python scripts/discipline_classifier.py --text "研究方向关键词" --affiliation "机构名"
```

解析 JSON 输出，取 `primary` 字段。匹配到高能物理/天体物理时，后续启用 INSPIRE/ADS。

### Step 2: 互联网广域搜索（新增 — 先广后深）

在进入论文检索之前，先在互联网上搜索该学者的公众信息。这一步有两个目的：一是在公开信息中找到该学者所有的学术 profile 链接（GS、ORCID、ResearchGate 等），二是对该学者的研究领域和公众形象有基本认知。

用 MCP Web Search 搜（用 Serper / Exa / Tavily）：
- `{姓名} {机构}` 或 `{姓名拼音} {机构拼音}` → 百度百科、知乎、新闻、采访等
- `{姓名} Google Scholar` → 找 GS profile 链接
- `{姓名} ORCID` → 找 ORCID 链接
- `{姓名} ResearchGate` → 找 ResearchGate 链接
- 如官网是 UCAS 页面，也去该学者的实验室主页或机构导师页看看

收集到的信息包括：
- 该学者的教育简历、研究领域简介（这些在百度百科或机构页面上通常有）
- 公众报道、奖项、学术兼职
- 所有能找到的学术 profile 链接

**GS profile 邮箱校验**：找到 GS 链接后，打开检查页面上显示的邮箱（GS profile 头部通常有"Verified email at xxx"），与官网提取的邮箱比对。一致 → 该 GS profile 确认属于目标学者。不一致或不显示 → 标记"GS 邮箱未验证"。

### Step 3: GS 爬论文列表（永远第一步）

**GS 是论文列表主源。** 不用 OpenAlex 做论文列表源，它只用来补充元数据。OpenAlex 对中文作者覆盖 22-38%，用 GS 能拿到完整的论文列表。

Web Search 搜 `{姓名拼音} Google Scholar` 找 GS profile 链接。找到后，**先做邮箱校验**：查看 GS 头部显示的 "Verified email at xxx"，与 Step 1 官网提取的邮箱比对。一致 → 确认该 GS profile 属于目标学者。不一致或不显示 → 标记"GS 邮箱未验证"，同名过滤时启用多维评分。

邮箱校验通过后：

```bash
python scripts/gs_scraper.py {gs_id} --output phase1_gs.json --pages 3 --delay 2
```

输出：论文标题 + 年份 + 引用数 + metrics（h-index、总引用、i10-index）。

**GS 不存在时**：降级到 OpenAlex 做主源（覆盖预期 ≤ 50%）。画像首段标注"未找到该学者的 Google Scholar profile。OpenAlex 对中文作者覆盖不完整（Zheng et al. 2025），论文列表可能不完整。建议提供 GS 链接。"

### Step 4: OpenAlex 元数据补充（不是论文列表源）

先调 `openalex_works.py` 拿作者 profile 数据（h-index、总引用数）：

```bash
python scripts/openalex_works.py {openalex_id} --output .cache/oa_profile.json
```

然后对 GS 每篇论文，用标题搜 OpenAlex 补 DOI/期刊/作者（**标题搜索比作者 works 列表覆盖更广**——对中文作者，OA 的作者 works 列表可能只收录了实际论文的 22-38%）：

```
对 GS 列表中的每篇论文 title:
  GET /works?search={urllib.parse.quote(title)}&per_page=3
  → 匹配上的：取 DOI、journal、authors、cited_by_count
  → 匹配不上的：保留 GS 原始数据（标记"仅 GS 来源"）
```

**注意**：OA 的作者 profile（h-index/引用数）不可靠——中文作者的 OA profile 常因身份消歧错误包含非本人的论文，导致指标失真。引用指标以 GS 的 `metrics` 字段为准。

### Step 5: 同名干扰过滤（仅在需要时）

名字独特时（如 "Zi-Xiang Li"）直接跳过。

名字常见时（如 "Pengju Zhang"），三筛过滤：

```
GS 邮箱验证优先：
  GS profile 绑定了机构邮箱（如 @iphy.ac.cn）时，
  → 该 profile 内所有论文视为已验证，跳过过滤。
  → 学者的职业阶段转换（碰撞物理→阿秒物理）是正常发展，不是同名干扰。

仅 GS 无法验证邮箱时，用多维评分：
  合著者重叠（+2 分） → 与已知论文共享合著者
  机构匹配（+1 分）   → 论文中的机构与履历一致
  期刊范围（+1 分）   → 论文发表在学科主流期刊
  领域关键词（+1 分） → 论文标题含研究方向关键词
  
  总分 ≥ 3 → 保留；总分 < 3 → 标记"疑似同名干扰"
```

### Step 6: arXiv 预印本补充

`au:姓名拼音` → 最新预印本 → 与 GS 论文去重。注意同名干扰（用 Step 4 的过滤方法）。

### Step 7: 合并 + 去重 + 按履历分组 + 输出

去重规则：P0:DOI → P1:arXiv ID → P2:归一化标题。

来源标记：
- GS 独有、OA 未匹配到 → "仅 GS 来源"
- GS+OA 都匹配到 → "GS+OA"
- arXiv 补充 → "arXiv"

**论文分组逻辑**：解析履历中的起止年份，每篇论文的发表年份落入哪个时间段就归入哪组。阶段名称根据真实经历动态设定，不硬编码。无 ORCID 履历时从机构 affiliation 推断。

**覆盖标注**：画像首段写"论文来自 {学者名} 的 Google Scholar profile（截至 {date}）。OpenAlex 补充元数据。仍可能缺失未更新到 GS 的最新预印本。"

### Step 8: 输出画像

AI 按 `assets/01_基础画像.md` 模板填充 9 节 + YAML frontmatter。写入 `项目/导师/<姓名>/01_基础画像.md`。

**写完后 AI 自检**：
- 所有信息有来源 URL
- 来源说明表列出各数据源状态
- 未找到的字段标 `[未找到]`
- 覆盖边界在首段标注
- 同名干扰过滤过程在来源说明中有记录

自检通过后给用户审阅。

---

## 全降级模式

GS 和 OpenAlex 都拿不到论文时：
1. 只用 arXiv 按姓名搜 + 官网抓取
2. 画像中标 `[未找到，仅 Web 搜集]`
3. 让用户后续补充 GS 或 ORCID 链接

---

## 验证来源

- 计划书: `计划/计划书.md` v3.3
- 调研报告: `计划/调研_学者分析工具全景.md`
- Config: `config/sources.json`
- Zhao & Chen (2025) OpenAlex 消歧精度: https://arxiv.org/html/2502.11610v2
- Zheng et al. (2025) OpenAlex 中国论文覆盖: https://doi.org/10.1002/asi.70013

**版本**: v3.0
**生成日期**: 2026-07-01
