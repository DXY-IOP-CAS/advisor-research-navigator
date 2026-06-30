---
name: profile-resolver
description: >
  This skill should be used when the user wants to "验证导师身份"、"拉取学者画像"、"做基础信息调研"、"获取导师论文列表"。
  It combines Stage 0 (identity verification via 00_身份验证卡.md) and Stage 1 (deep profile via 01_基础画像.md) of the research-advisor pipeline.
  Always triggers when the parent research-advisor skill routes to Stage 0 or 1.
---

# profile-resolver（合并阶段 0 + 阶段 1）

## 本 skill 是什么

合并了**身份验证**（人闸前）和**基础画像**（人闸后）两个阶段的人闸式流水线：

```
用户输入：<姓名> + <机构> + <官网 URL 可选> + <方向关键词可选>
              │
              ▼
┌─────────────────────────────────────────────────┐
│ Phase A: 学科自动识别 + 浅调研（10-15 次 API）   │
│                                                  │
│   ① 用 get_homepage.py 抓官网 → 提取 email/论文 │
│   ② 用 discipline_classifier.py 自动识别学科     │
│   ③ 按学科启用数据源，并行查学术 ID              │
│   ④ 用论文标题交叉比对，算各源命中率             │
│   ⑤ 输出 00_身份验证卡.md → ⚠ STOP HERE         │
└─────────────────────────────────────────────────┘
              │
              │ 用户说 yes → 才继续
              ▼
┌─────────────────────────────────────────────────┐
│ Phase B: 全量采集（15-25 次 API + 多源 Web）      │
│                                                  │
│   ① 用锁定的 OpenAlex/ORCID/INSPIRE/ADS ID      │
│      拉完整 profile                                │
│   ② 用 Web Search 拉中文网络（新闻/采访/讲座）   │
│   ③ 用 ArXiv 按姓名搜最新预印本                  │
│   ④ 用 Google Scholar profile（如果 Web 命中）    │
│   ⑤ 用 deduplicate.py 合并去重                   │
│   ⑥ 输出 01_基础画像.md                          │
│   ⑦ AI 自检：所有信息有 URL、字段无缺失          │
└─────────────────────────────────────────────────┘
```

## 强约定

### Phase A 结束必须停下

写完 `00_身份验证卡.md` 后，AI 必须**停下输出**，等用户输入 `yes`/`no`/`modify`。**禁止**自动进入 Phase B。
- 这是阶段门控——ID 锁错后面全错
- 即使用户已经说"是的"，也必须等用户在验证卡的 prompt 处确认

### 不报错退出

如果所有数据源都返回空：
1. **禁止**输出 `Error` 或抛出异常
2. 把"未找到"事实写入 00_身份验证卡.md
3. 列出已尝试的所有数据源
4. 让用户补充信息（如：确切的 ORCID ID、inspirehep ID、论文 DOI 等）
5. 把决策权交给用户

### 必须为单人查询，不要批量

每次调用处理一个导师。流水线不并发跑多个导师——避免数据互相污染。

## 执行细节

### 阶段 0（Phase A）— 浅调研

参见 `references/stage-0-workflow.md`

要点：
1. 抓官网页面（MCP HTTP fetch / 命令行调用 `scripts/get_homepage.py`）
2. 从页面提取：邮箱、姓名（英/中）、职称、官网明确列出的论文标题
3. 用关键词匹配到 config.json 的学科段
4. 调用脚本 `scripts/identity_resolver.py`，按学科并行查：
   - ORCID (by email)
   - arXiv Author ID (按姓名拼音搜 arxiv → 提取作者页面)
   - OpenAlex (by name + institution ROR)
   - Semantic Scholar (by name pinyin)
   - INSPIRE-HEP（若高能物理）
   - NASA ADS（若天体物理）
5. 标题比对：脚本计算每个候选人的命中率，返回排序列表
6. 写 00_身份验证卡.md

### 阶段 1（Phase B）— 深调研

参见 `references/stage-1-workflow.md`

要点：
1. 用锁定的 OpenAlex/ORCID/INSPIRE/ADS ID 拉数据：
   - OpenAlex `/authors/{id}/works?per_page=200&sort=cited_by_count:desc`
   - OpenAlex `/authors/{id}`（含 works_count, cited_by_count）
   - Semantic Scholar `/author/{id}/papers?fields=title,tldr,year,citationCount`
   - ORCID（若匹配）`/{orcid-id}`（读 education/employment/qualification）
   - INSPIRE（若适用）`/authors?q={id}` 拉完整论文列表
2. 并行（无需 ID）采集：
   - arXiv `au:{姓名拼音}` 搜最新预印本
   - Web Search（Serper/Exa）"{姓名} {机构} 采访/讲座/新闻"
   - Web Search `site:scholar.google.com/citations?user={姓}` 找 Google Scholar profile
   - 抓官网页面更深一层（实验室介绍、招生信息）
3. 合并去重（DOI 优先 → arXiv ID → 归一化标题 ≥85%）
4. 排序（被多源共证优先）
5. 写入 01_基础画像.md（frontmatter + 9 节）
6. AI 自检 + 用户审阅

## 输出文件位置

`项目/导师/<姓名>/`
- `00_身份验证卡.md`
- `01_基础画像.md`

## 调用脚本

| 脚本 | 用途 |
|:-----|:-----|
| `scripts/get_homepage.py` | 抓官网页面，提取结构化字段 |
| `scripts/discipline_classifier.py` | 关键词→学科映射 |
| `scripts/identity_resolver.py` | 多源 ID 查询 + 论文标题比对 |
| `scripts/profile_fetcher.py` | 用 ID 拉完整 profile |
| `scripts/web_discovery.py` | Web 搜索 + 中文信息采集 |
| `scripts/deduplicate.py` | 论文去重 |
| `scripts/rank_papers.py` | 论文排序（按多源共证+引用数） |
| `scripts/build_profile.py` | 把所有数据合并成 01_基础画像.md |

## 验证来源

- OpenAlex disambiguation 原理：https://github.com/ourresearch/openalex-name-disambiguation/tree/main/V3
- INSPIRE-HEP 完整文档：https://inspirehep.net/help/knowledge-base/full-listing-of-search-terms/
- ArXiv Author Identifier 机制：https://info.arxiv.org/help/author_identifiers.html
- ORCID 搜索 API：https://info.orcid.org/documentation/api-tutorials/search-tutorial
- WhoIsWho 学术消歧框架：https://github.com/THUDM/WhoIsWho
- CrossND 跨源消歧：https://github.com/zfjsail/CrossND

**版本**：v1.0
**生成日期**：2026-06-30
