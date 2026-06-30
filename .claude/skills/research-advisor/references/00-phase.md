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

### Step 2: Google Scholar 获取论文列表（永远第一步）

**GS 是论文列表主源。** 不用 OpenAlex 做论文列表源，它只用来补充元数据。OpenAlex 对中文作者覆盖 22-38%，用 GS 能拿到完整的论文列表。

Web Search 搜 `{姓名拼音} Google Scholar` 找 GS profile 链接。找到后：

```bash
python scripts/gs_scraper.py {gs_id} --output phase1_gs.json --pages 3 --delay 2
```

输出：论文标题 + 年份 + 引用数。

**GS 不存在时**：降级到 OpenAlex 做主源（覆盖预期 ≤ 50%）。画像首段标注"未找到该学者的 Google Scholar profile。OpenAlex 对中文作者覆盖不完整（Zheng et al. 2025），论文列表可能不完整。建议提供 GS 链接。"

### Step 3: OpenAlex 元数据补充（不是论文列表源）

对 GS 每篇论文，用标题搜 OpenAlex，补充 DOI、期刊名、作者列表：

```
对 GS 列表中的每篇论文 title:
  GET /works?search={urllib.parse.quote(title)}&per_page=3
  → 匹配上的：取 DOI、journal、authors、cited_by_count
  → 匹配不上的：保留 GS 原始数据
```

不依赖 OpenAlex 的 works_count。OpenAlex 只做元数据补充。

### Step 4: 同名干扰过滤（仅在需要时）

名字独特时（如 "Zi-Xiang Li"）直接跳过。

名字常见时（如 "Pengju Zhang"），三筛过滤：

```
筛 1 — 合著者网络
  取官网论文中的合著者列表做白名单。
  候选论文至少与 1 位白名单合著者共著才保留。

筛 2 — 期刊范围
  限制在物理学科主流期刊。不在范围内的标记"期刊存疑"。

筛 3 — 领域关键词
  研究方向关键词正匹配。零命中的标记"主题存疑"。

汇总：三筛全过 → 可信高。仅通过合著者 → 可信中。零通过 → 排除。
```

### Step 5: arXiv 预印本补充

`au:姓名拼音` → 最新预印本 → 与 GS 论文去重。注意同名干扰（用 Step 4 的过滤方法）。

### Step 6: 合并 + 去重 + 按履历分组 + 输出

去重规则：P0:DOI → P1:arXiv ID → P2:归一化标题。

来源标记：
- GS 独有、OA 未匹配到 → "仅 GS 来源"
- GS+OA 都匹配到 → "GS+OA"
- arXiv 补充 → "arXiv"

**论文分组逻辑**：解析履历中的起止年份，每篇论文的发表年份落入哪个时间段就归入哪组。阶段名称根据真实经历动态设定，不硬编码。无 ORCID 履历时从机构 affiliation 推断。

**覆盖标注**：画像首段写"论文来自 {学者名} 的 Google Scholar profile（截至 {date}）。OpenAlex 补充元数据。仍可能缺失未更新到 GS 的最新预印本。"

### Step 7: 输出画像

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
