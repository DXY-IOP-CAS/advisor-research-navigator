# API 与数据源调用参考

本文件提供阶段 0/1 中各 API 的调用方法、限速、参数说明。被 `references/00-phase.md` 引用，AI 在执行阶段 0/1 时按需读取。

**注意**：AI 直接调用这些 API，不经过自定义脚本（除非特定步骤标注用脚本）。

---

## OpenAlex

**用途**：论文元数据、作者资料、引用数。阶段 0 做候选人搜索，阶段 1 做全量论文拉取。

| 端点 | 用途 | 参数 |
|:-----|:------|:------|
| `GET /authors?search={name}&filter=last_known_institutions.id:{ror}` | 搜候选人 | `per_page=20` |
| `GET /authors/{id}` | 作者 profile | 无额外参数 |
| `GET /works?filter=authorships.author.id:{id}&per_page=200&sort=publication_year:desc` | 全量论文 | `cursor=*` 分页 |

限速：100K/天（带 email），10 req/s polite pool。无 API key。

**分页**：works 总数超过 200 时用 cursor 分页：

```
第一次: GET /works?filter=authorships.author.id:A123456789&per_page=200&cursor=*
响应: meta.next_cursor = "abcd" ← 下一批游标
第二次: GET /works?filter=authorships.author.id:A123456789&per_page=200&cursor=abcd
```

**标题归一化**（用于 ID 消歧的标题比对）：去标点 + 小写 + 去空格，做子串匹配。在阶段 0 Step 5 中使用。

---

## Semantic Scholar

**用途**：TLDR 摘要、补漏论文、引用影响力标记。阶段 1 使用。

| 端点 | 用途 | 参数 |
|:-----|:------|:------|
| `GET /author/search?query={name}&fields=name,affiliations,paperCount,externalIds` | 阶段 0 搜候选人 | — |
| `GET /author/{id}/papers?fields=title,tldr,year,citationCount,externalIds,venue` | 阶段 1 拉论文 | — |
| `POST /paper/batch?fields=tldr,title,year,citationCount` | 批量查 TLDR | body: `{"ids":["DOI:10.1103/...","CorpusId:..."]}` |

限速：100 req/5min（无 key），1 req/s（有 key）。可请求免费 API key。

注意：S2 的 citationCount 可能高于 OpenAlex（因覆盖范围不同），两个都保留做交叉验证。

---

## arXiv

**用途**：补预印本时间差。阶段 0/1 均使用。

| 端点 | 用途 |
|:-----|:------|
| `GET /api/query?search_query=au:Lastname_Firstname&sortBy=submittedDate&sortOrder=descending&max_results=50` | 按作者搜 |
| `https://arxiv.org/a/{lastname_lower}_{firstinitial}_` | 手动检查 Author ID（如已知） |

响应格式：Atom XML。限速 1 req/3s。

常见问题：`au:` 搜索只按作者名匹配，返回结果可能有同名干扰。AI 手动筛选。

---

## ORCID

**用途**：身份精确匹配（阶段 0）+ 教育/工作履历（阶段 1）。

| 端点 | 用途 |
|:-----|:------|
| `GET /expanded-search?q=email:{email}` | 按 email 搜 ORCID ID |
| `GET /v3.0/{orcid-id}/educations` | 教育经历 |
| `GET /v3.0/{orcid-id}/employments` | 工作经历 |

限速：无官方限制。公共 API 免费。

注意：填写 email 并关联 ORCID 的学者注册率低。email 查不到不报错，跳到下一步。

---

## INSPIRE-HEP

**用途**：仅高能物理学科启用（`discipline=high_energy_physics` 时）。

| 端点 | 用途 |
|:-----|:------|
| `GET /api/authors?q={name}&size=20` | 搜作者 |
| `GET /api/literature?sort=mostrecent&size=25&q=a {bai}` | 论文列表 |

---

## NASA ADS

**用途**：仅天体物理学科启用（`discipline=astrophysics` 时）。需 `ADS_API_TOKEN` 环境变量。

| 端点 | 用途 |
|:-----|:------|
| `GET /search/query?q=author:"{name}"&fl=title,author,year,citation_count` | 按作者搜 |

---

## CrossRef

**用途**：DOI 元数据兜底，OpenAlex 查不到的论文由 CrossRef 查。

| 端点 | 用途 |
|:-----|:------|
| `GET /works/{doi}` | 单篇元数据 |
| `GET /works?query.author={name}&query.title={title}` | 按标题+作者搜 |

限速 50 req/s。

---

## 学科识别（本地脚本）

```bash
python scripts/discipline_classifier.py --text "方向关键词" --affiliation "机构名"
```

输出 JSON：`{"primary": "atomic_molecular_optical", "sources": ["openalex", "arxiv"]}`

识别结果控制后续启用哪些数据源：
- `high_energy_physics` → 启用 INSPIRE-HEP
- `astrophysics` → 启用 NASA ADS
- 其他学科 → 只走通用源 OpenAlex + arXiv + S2

---

## 全降级模式

所有 API 都空时（极少出现）：
1. 跳过所有需 ID 的源（OpenAlex/S2/INSPIRE/ADS）
2. 只做 Web Search + arXiv 按姓名搜 + 官网抓取
3. 画像中标 `[未找到，仅 Web 搜集]`
4. 让用户后续补充 ORCID 或 Google Scholar 链接

---

## 验证来源

- OpenAlex API: https://docs.openalex.org
- Semantic Scholar API: https://api.semanticscholar.org/
- arXiv API: https://info.arxiv.org/help/api
- ORCID Public API: https://info.orcid.org/documentation/api-tutorials
- INSPIRE-HEP API: https://github.com/inspirehep/rest-api-doc
- NASA ADS API: https://ui.adsabs.harvard.edu/help/api/
- CrossRef API: https://api.crossref.org

**版本**: v1.0
**生成日期**: 2026-07-01
