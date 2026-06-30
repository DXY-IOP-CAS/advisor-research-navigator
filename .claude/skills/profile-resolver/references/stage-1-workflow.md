# 阶段 1（基础画像）Workflow 详细说明

主文档：[`../SKILL.md`](../SKILL.md)

## 何时进入

仅当阶段 0 输出的 `00_身份验证卡.md` 用户已确认（口头输入 `yes` 或显式确认）时进入。

## 步骤 1.0 — 前置检查

AI 必须读 `项目/导师/<姓名>/00_身份验证卡.md` 并确认：
- 至少有一个高置信度的学术 ID 被锁定（OpenAlex/ORCID/arXiv/INSPIRE/ADS 之一）
- 用户的决策是 yes，不是 modify/redirect

如果 00 卡显示 "全部未找到"——**不要退出**，按以下"全降级模式"继续：

## 步骤 1.1 — 用锁定的 ID 拉 profile

调用 `scripts/profile_fetcher.py`：

```bash
python scripts/profile_fetcher.py \
  --openalex "A5031655767" \
  --orcid "0000-0002-..." \
  --arxiv "zhang_p_2" \
  --inspire "INSPIRE-00140145" \
  --output /tmp/profile_raw.json
```

**每个 ID 调什么**：

| 平台 | 调用 | 拿什么 |
|:-----|:----|:------|
| OpenAlex | `GET /authors/A5031655767` | works_count, cited_by_count, last_known_institutions, counts_by_year |
| OpenAlex | `GET /authors/A5031655767/works?per_page=200&sort=cited_by_count:desc` | 论文列表（title, doi, year, cited_by_count, authors） |
| Semantic Scholar | `GET /author/{s2_id}/papers?fields=title,tldr,year,citationCount,influentialCitationCount` | TLDR 摘要 |
| ORCID | `GET /0000-0002-.../educations`, `employments` | 时间线履历 |
| INSPIRE-HEP | `GET /authors?q={id}` + `/literature?q=a {id}` | 高能物理领域完整论文列表 |
| NASA ADS | `GET /v1/search/query?q=author:"{name}"` | 天体物理论文 |

**容错**：某个 ID 没锁定就跳过该源的调用；某个 API 返回 5xx 就重试 1 次，仍失败标"未获取到"。

## 步骤 1.2 — 不需 ID 的并行采集

调用 `scripts/web_discovery.py`：

```bash
python scripts/web_discovery.py \
  --name "张鹏举" \
  --name-en "Pengju Zhang" \
  --affiliation "中科院物理所" \
  --output /tmp/web_raw.json
```

并行执行：

1. **arXiv 搜最新预印本**：`GET /query?search_query=au:Pengju+Zhang&sortBy=submittedDate&sortOrder=descending&max_results=20`
2. **Google Scholar profile 查找**：Serper/Exa 搜 `"site:scholar.google.com/citations?user=" "Pengju Zhang"`；若命中 URL 则 HTTP fetch 该页（限频）
3. **中文 Web Search（Serper 优先）**：搜 "{姓名} {机构}" + 关键词变体（采访、新闻、讲座、B站、知乎）
4. **抓机构主页深度内容**：从该导师的招生页、实验室介绍页、课题组页抓更详细内容
5. **百度百科 / 维基百科**：搜姓名词条

返回结构：

```json
{
  "arxiv_preprints": [{"arxiv_id": "2501.12345", "title": "...", "year": 2025}, ...],
  "google_scholar_url": "...",
  "news_articles": [{"title": "...", "url": "...", "snippet": "...", "date": "..."}],
  "homepage_extra": {"research_overview": "...", "lab_members": [...], "openings": "..."},
  "baidu_baike": "...",
  "wikipedia": "..."
}
```

**限速约束**：Google Scholar 部分每次会话不超过 50 次抓取，否则 CAPTCHA。

## 步骤 1.3 — 论文去重

调用 `scripts/deduplicate.py`：

```bash
python scripts/deduplicate.py \
  --inputs /tmp/openalex_works.json,/tmp/arxiv_preprints.json,/tmp/inspire_literature.json \
  --output /tmp/deduped_papers.json
```

**去重策略**：
1. DOI 完全匹配 → 合并为一篇
2. arXiv ID 匹配 → 合并为一篇
3. 归一化标题（去标点、去空格）相似度 ≥85% → 合并为一篇
4. 合并时优先保留引用数最多的源

合并后保留多源验证的"被多源共证"标记——画像阶段用于排序。

## 步骤 1.4 — 论文排序

调用 `scripts/rank_papers.py`：

排序键：
1. **被多源共证**（OpenAlex + Semantic Scholar + INSPIRE 都收录 +10 分；多源可能不一致）
2. **引用数**（OpenAlex `cited_by_count`）
3. **年份新**（仅在引用数相近时排序）

输出排序后的论文列表，每篇带：
- `title`, `year`, `doi`, `arxiv_id`
- `cited_by_count`
- `tldr`（来自 Semantic Scholar）
- `multi_source_verified`（bool）

## 步骤 1.5 — 合成 01_基础画像.md

调用 `scripts/build_profile.py`：

```bash
python scripts/build_profile.py \
  --name "张鹏举" \
  --affiliation "中科院物理所" \
  --department "超快物质科学中心" \
  --tags "[超快光学, 强场物理, 阿秒科学]" \
  --ids /tmp/ids.json \
  --profile-data /tmp/profile_raw.json \
  --web-data /tmp/web_raw.json \
  --papers /tmp/deduped_papers.json \
  --output "项目/导师/张鹏举/01_基础画像.md"
```

9 节结构（详细字段见 `assets/01_基础画像.md` 模板）：
1. 身份标识
2. 学术履历时间线
3. 研究方向
4. 代表性论文（按 1.4 的排序）
5. 学术影响力指标
6. 合作网络
7. 公开多维信息
8. 技术关键词
9. 来源说明与多源比对

## 步骤 1.6 — 自检 + 用户审阅

**AI 自检**（自动）：
- 所有字段是否有数据？空字段填 `[未找到]` 不要捏造
- 所有外部引用是否带 URL？
- 各数据源冲突是否列出？

**用户审阅**：写完后必须停下，让用户读 01_基础画像.md。

输出提示：

> 已写入：项目/导师/<姓名>/01_基础画像.md
> 该阶段结束，移交 research-advisor 调度，进入阶段 2（如需要）。

## 全降级模式

如果 00 卡的全部 ID 都为空，但用户仍想继续：

- **禁止报错退出**
- 仅做 web_discovery（Web Search + ArXiv 按姓名 + 抓官网页面）
- 用 00 卡的邮箱/官网信息做填充
- 01 基础画像.md 各字段大量标 `[未找到]，因身份未锁定暂不接入 OpenAlex/S2`
- 让用户后续尝试补充 ID

## 验证来源

- supervisor 4 种搜索模式：https://github.com/ybq22/supervisor
- ai-talent-graph 4 API 并行：https://github.com/rrrrrredy/ai-talent-graph
- scholar-megasearch 去重：https://github.com/TaewoooPark/scholar-megasearch
- INSPIRE-HEP API：https://github.com/inspirehep/rest-api-doc

**版本**：v1.0
**生成日期**：2026-06-30
