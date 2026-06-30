# 阶段 0 + 阶段 1 执行步骤

本文件被 `../SKILL.md` 在阶段 0/1 时读取。内容对应计划书 2.2 节和 2.3 节。

## 阶段 0：浅调研 + 人闸确认

### Step 1: 抓官网

用 Bash（curl）或 MCP fetch 读用户给的 URL。提取：
- 姓名（中文 + 拼音）
- 职称
- 邮箱
- 研究方向关键词
- 论文标题列表（至少 2 篇才能做交叉比对）

容错：404 就停，让用户确认 URL。缺字段就标缺失。

### Step 2: 学科识别

```bash
python scripts/discipline_classifier.py --text "研究方向关键词" --affiliation "机构名"
```

解析 JSON 输出，取 `primary` 字段。匹配到高能物理/天体物理时，后续启用 INSPIRE/ADS。

### Step 3: 列出调研计划 → 用户审

**这一步是设计关键**——不是全自动查完再让人确认，而是先让人知道要查什么、从哪查。

列出一份清单让用户审。**每个渠道放可点击链接**（不是"[标题1]"这种形式）：

```
调研计划：张鹏举 @ 中科院物理所
─────────────────────────────
一、这是你要调研的老师吗？
  UCAS导师页: https://people.ucas.ac.cn/~0052353

二、锚定论文（官网提取的论文标题，将用于 ID 比对）
  1. Nature Chemistry 14, 1126-1132 (2022)
     → https://www.nature.com/articles/s41557-022-01012-0
  2. PRL 128, 133001 (2022)
     → https://doi.org/10.1103/PhysRevLett.128.133001

三、将查询的 ID 源（你可以先点开看候选池）
  OpenAlex: https://openalex.org/authors?search=Pengju+Zhang
  Semantic Scholar: https://www.semanticscholar.org/search?q=Pengju+Zhang
  arXiv: https://arxiv.org/search/?query=Zhang+Pengju&searchtype=author

四、Web 搜索
  - "张鹏举 物理所 超快"
  - "张鹏举 百度百科"

→ 请点开链接，确认没问题后回复 yes。modify 修改输入重跑。no 取消。
```

用户确认 yes 后继续。modify 则修改输入重跑。no 取消。

### Step 4: 批量执行查询

```bash
python scripts/identity_resolver.py \
  --name "姓名拼音" \
  --email "email" \
  --ror "机构 ROR" \
  --papers-file /tmp/papers.json \
  --enable openalex,orcid,semantic_scholar \
  --discipline 学科标识
```

6 个 ID 源：ORCID（by email）、OpenAlex（姓名+机构 ROR）、ArXiv Author ID（web 搜索）、Semantic Scholar（拼音）、INSPIRE-HEP（仅高能）、NASA ADS（仅天文）。

降级模式：单个源查不到不报错，跳过继续。

### Step 5: 论文标题比对

`identity_resolver.py` 内部完成。对每个 OpenAlex 候选拉论文列表，与官网论文做归一化标题匹配。命中率：
- ≥80% = 高置信
- 50-80% = 中置信
- <50% = 低置信

标题归一化规则：去标点 + 小写 + 去空格，做子串匹配。

### Step 6: 输出验证卡

AI 按 `assets/00_身份验证卡.md` 模板手动渲染 Markdown，写入 `项目/导师/<姓名>/00_身份验证卡.md`。

**写完后 STOP。** 等用户输入 yes/modify/no。

---

## 阶段 1：深调研 + 基础画像

### Step 1: 用锁定 ID 拉 profile

用锁定的 OpenAlex ID：
- `GET /authors/{id}` → 作者基本信息、总引用、总论文、h-index
- `GET /authors/{id}/works?per_page=200&sort=cited_by_count:desc` → 全部论文列表（**不是只拉前几篇，尽可能拉全**）

用 S2 ID（如有）：
- `GET /author/{id}/papers?fields=title,tldr,year,citationCount` → 全部论文的 TLDR 摘要

用 ORCID（如有）：
- `GET /{orcid-id}/educations`、`employments` → 履历

**硬规则**：论文要尽可能全面——已发表的和预印本都要收。OpenAlex 默认返回 25 篇/页，设 `per_page=200` 尽量拉满。单源覆盖不全时用多源合并（见 Step 3 去重）。

### Step 2: 不需 ID 的采集

并行执行：
- arXiv：`http://export.arxiv.org/api/query?search_query=au:姓名拼音`，拿最新预印本（注意区分同名干扰）
- 如果 au: 搜索不精确，用 arXiv 全文搜索姓名，手动筛选
- Web Search（Serper/Exa/Tavily）：搜 `姓名 机构 采访/讲座/新闻/B站`
- 机构官网：深度抓取实验室介绍、招生信息页
- 百度百科：搜姓名词条
- Google Scholar profile：Web Search 找 URL，限频抓页
- SSRN / ResearchGate / 其他预印本平台：如 Web Search 发现相关条目，一并收录

### Step 3: 去重排序 + 按履历分组

**去重规则**（优先级由高到低）：
1. DOI 相同 → 同一篇
2. arXiv ID 相同 → 同一篇
3. 归一化标题相似度 ≥85% → 同一篇

**论文分组逻辑**：
```
解析履历中的起止年份，每篇论文的发表年份落入哪个时间段就归入哪组。

阶段名称根据该老师的真实经历动态设定，不硬编码"博士/博后/独立"：
示例1（标准学术路径）: 博士期 / 博后期 / 独立后
示例2（有工业界经历）: 硕士期 / 工业界期 / 博士期 / 独立后
示例3（跨学科转型）: 物理博士期 / 生物博后期 / 独立后
```
跨阶段工作（如博士工作延至博后才发表）归属于实际完成阶段。

**排序键**：多源共证数优先 → 引用数次之 → 年份再次。

### Step 4: 输出画像

AI 按 `assets/01_基础画像.md` 模板填充 9 节 + YAML frontmatter。写入 `项目/导师/<姓名>/01_基础画像.md`。

**论文部分硬规则**：
- **不是"代表性论文"，是"全部论文"**。列出从所有渠道收集到的全部论文，按学术履历阶段分组（博士/博后/独立后）
- **包含预印本**。arXiv 上找到的未发表手稿也收录进去，标注"预印本"
- **SSRN、ResearchGate 上的预印本**如果找到也收录
- 论文表格每列：标题、期刊、年份、引用数、角色（一作/通讯/合作）、TLDR（一句话摘要）、来源

**写完后 AI 自检**：
- 所有信息有来源 URL（每条外部信息末尾标链接）
- 各节字段无缺失
- 无矛盾信息（有矛盾时并列标注 "来源X说...来源Y说..."）
- 未找到的字段标注 `[未找到]`

自检通过后给用户审阅。

---

## 全降级模式

如果所有 ID 源都空：
1. 不入 OpenAlex/S2/INSPIRE 等需 ID 的源
2. 只做 web_discovery（Web Search + ArXiv 按姓名 + 官网）
3. 画像中所有字段标 "[未找到，仅 Web 搜集]"
4. 让用户后续补充 ID（ORCID 链接、Google Scholar 链接等）

---

## 验证来源

- 计划书: `计划/计划书.md` v3.0 第 2 章
- Config: `config/sources.json`

**版本**: v2.0
**生成日期**: 2026-07-01
