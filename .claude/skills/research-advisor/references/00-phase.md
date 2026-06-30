# 阶段 0 + 阶段 1 执行步骤

本文件被 `../SKILL.md` 在阶段 0/1 时读取。内容对应计划书 2.2 节。

## 阶段 0（身份验证）

### Step 1: 抓官网

用 Bash 或 MCP fetch 读用户给的 URL。提取：
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

### Step 3: 并行查 ID

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

### Step 4: 论文标题比对

`identity_resolver.py` 内部完成。对每个 OpenAlex 候选拉论文列表，与官网论文做归一化标题匹配。命中率 ≥80% = 高置信，50-80% = 中，<50% = 低。

### Step 5: 输出验证卡

```bash
# 合成验证卡（待脚本完成前可用手写 Markdown）
python scripts/build_verification_card.py ...（待实现）
```

现阶段无此脚本时，AI 直接按 `assets/00_身份验证卡.md` 模板手动渲染。

**写完后 STO P。** 等用户输入 yes/modify/no。

## 阶段 1（基础画像）

### Step 1: 拉 profile

用锁定的 OpenAlex ID：
- `GET /authors/{id}` → 作者基本信息、总引用、总论文
- `GET /authors/{id}/works?per_page=200&sort=cited_by_count:desc` → 论文列表

用 S2 ID（如有）：
- `GET /author/{id}/papers?fields=title,tldr,year,citationCount` → TLDR 摘要

用 ORCID（如有）：
- `GET /{orcid-id}/educations`、`employments` → 履历

### Step 2: 不需 ID 的采集

- arXiv：搜 `au:姓名拼音`，拿最新预印本
- Web Search（Serper/Exa）：搜 `姓名 机构 采访/讲座/新闻/B站`
- 机构官网：深度抓取实验室介绍、招生信息页
- 百度百科：搜姓名词条
- Google Scholar profile：Web Search 找 URL，限频抓页

### Step 3: 去重排序

去重规则：DOI 优先 → arXiv ID → 归一化标题相似度 ≥85%。合并时保留多源共证标记。排序键：多源共证优先，其次引用数，再次年份。

### Step 4: 输出画像

按 `assets/01_基础画像.md` 模板填充 9 节 + YAML frontmatter。写完后 AI 自检（所有信息有 URL、字段无缺失）。自检通过后给用户审阅。

## 全降级模式

如果所有 ID 源都空：
1. 不入 OpenAlex/S2/INSPIRE 等需 ID 的源
2. 只做 web_discovery（Web Search + ArXiv 按姓名 + 官网）
3. 画像中所有字段标 "[未找到，仅 Web 搜集]"
4. 让用户后续补充 ID

## 验证来源

- 计划书: `计划/计划书.md` 附录 A
- config: `config/sources.json`

**版本**: v1.0
**生成日期**: 2026-06-30
