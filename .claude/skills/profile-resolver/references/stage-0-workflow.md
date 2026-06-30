# 阶段 0（身份验证）Workflow 详细说明

主文档：[`../SKILL.md`](../SKILL.md) — 读主文档了解本 skill 的总体框架。

## 步骤 0.0 — 用户输入解析

**输入格式**：`<姓名> + <机构名> + <官网 URL 可选>`

如果用户没给官网 URL，但给了机构主页域名（如 `iphy.ac.cn`），AI 必须先 Web 搜索找到具体老师页面。**不要凭空猜 URL**。

如果用户给了姓名但没给机构：
1. Web 搜 "{姓名} 教授" 或 "{姓名} 研究员"
2. 从结果反推机构
3. 把推断结果写入 00_身份验证卡.md 让用户确认

如果用户只给了姓名（罕见）：
- 同样 Web 搜，但用户必须明确接受"可能锁定错人"的风险
- 验证卡里必须显眼标注"未提供机构，判定风险高"

## 步骤 0.1 — 抓官网页面

调用 `scripts/get_homepage.py`（或 MCP fetch）：

```bash
python scripts/get_homepage.py <URL>
```

返回结构化 JSON：

```json
{
  "url": "https://edu.iphy.ac.cn/detail_teacher.php?id=6368",
  "name_cn": "张鹏举",
  "name_en": "Pengju Zhang",
  "title": "特聘研究员",
  "department": "超快物质科学中心",
  "email": "pengju.zhang@iphy.ac.cn",
  "research_text": "阿秒科学、强场物理、分子轨道层析成像...",
  "paper_titles": ["Time-resolved multi-electron...", "A liquid-phase HHG apparatus..."],
  "office": "M楼 318",
  "phone": "+86-10-..."
}
```

**容错**：返回 404 → 让用户确认 URL。返回字段不全 → 把已抓到的填入验证卡，缺的标"未提取到"。

## 步骤 0.2 — 学科自动识别

调用 `scripts/discipline_classifier.py`：

```bash
python scripts/discipline_classifier.py --text <research_text>
```

返回学科归类：

```json
{
  "primary": "atomic_molecular_optical",
  "confidence": 0.92,
  "matched_keywords": ["阿秒", "强场", "超快"],
  "arxiv_categories": ["physics.atom-ph", "physics.optics"]
}
```

**铁则**：AI 不要自己判断学科，必须用脚本。脚本的关键词字典来自 config.json。

## 步骤 0.3 — 并行查 ID（学科感知）

调用 `scripts/identity_resolver.py`：

```bash
python scripts/identity_resolver.py \
  --name "Pengju Zhang" \
  --affiliation "Institute of Physics, CAS" \
  --email "pengju.zhang@iphy.ac.cn" \
  --paper-titles-file /tmp/papers.json \
  --enable-sources openalex,arxiv,orcid,semantic_scholar \
  --ror "https://ror.org/05qbk4x57" \
  --discipline "atomic_molecular_optical"
```

返回每个启用数据源的候选列表：

```json
{
  "openalex": {
    "candidates": [
      {
        "id": "https://openalex.org/A5031655767",
        "display_name": "Pengju Zhang",
        "works_count": 65,
        "cited_by_count": 1565,
        "institutions": ["ETH Zurich", "Chinese Academy of Sciences"]
      },
      ... 24 个其他人
    ]
  },
  "orcid": {
    "candidates": [{"orcid": "0000-0002-...", "name": "Pengju Zhang"}]
  },
  "arxiv": {
    "candidates": [{"arxiv_id": "zhang_p_2", "url": "https://arxiv.org/a/zhang_p_2"}]
  },
  ...
}
```

**关键**：脚本对每个数据源独立查询，不互相依赖。各源返回的候选列表合并到下一步处理。

## 步骤 0.4 — 论文标题交叉比对

`identity_resolver.py` 内嵌此逻辑：

对每个 OpenAlex 候选（最关键，因为有 works endpoint）：
```bash
GET /authors/{id}/works?per_page=200
```

提取该候选的所有论文标题 → 与官网论文标题做匹配：

- ≥80% 命中：高置信
- 50-80% 命中：中置信
- <50% 命中：低置信

把候选按命中率排序。

**核心创新（vs 业界）**：用户给的官网是 ground truth，**避免了纯 ML 聚类的中文名消歧困难**。其他工具（OpenAlex 自己）用 ML，F1 ~85-95%；我们的方法命中率上限由官网论文列表的完整性决定。

## 步骤 0.5 — 输出 00_身份验证卡.md

调用 `scripts/build_verification_card.py`：

```bash
python scripts/build_verification_card.py \
  --name "Pengju Zhang" \
  --affiliation "中科院物理所" \
  --department "超快物质科学中心" \
  --email "pengju.zhang@iphy.ac.cn" \
  --title "特聘研究员" \
  --candidates-file /tmp/candidates.json \
  --discipline "atomic_molecular_optical" \
  --output "项目/导师/张鹏举/00_身份验证卡.md"
```

模板见 `assets/00_身份验证卡.md`。

**写完后必须 STOP**——AI 不能继续执行 Phase B。

输出结束时，AI 给用户的提示必须明确包含：

> 已写入：项目/导师/<姓名>/00_身份验证卡.md
> 请打开核对。要继续请输入 `yes`，要调整信息请输入 `modify [你的修改]`。

## 异常处理

| 情况 | 处理 |
|:-----|:-----|
| 官网返回 404 | 让用户确认 URL |
| 官网只列 1 篇论文 | 标"ground truth 不足"，匹配度阈降低（≥60% 当高置信） |
| 邮箱未提取到 | ORCID 搜索降级；其他源继续 |
| OpenAlex 0 命中 | 改用 arXiv Author ID + S2 双重搜索 |
| 所有数据源都 0 命中 | 输出降级报告，让用户手动给 ID |

## 验证来源

- Project Pipeline 文档：参考项目内 `计划/技术方案概述.md` v2+
- INSPIRE-HEP API：https://github.com/inspirehep/rest-api-doc
- OpenAlex 文档：https://docs.openalex.org
- 同类工具参考：https://github.com/ybq22/supervisor（4 种 Google Search 模式）

**版本**：v1.0
**生成日期**：2026-06-30
