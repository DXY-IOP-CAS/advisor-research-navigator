# API 与数据源调用参考

本文件提供阶段 1 各 API 的调用方法、限速、参数说明。按需由 `references/phase1-core.md` 或执行 AI 引用。

当前 pipeline 依赖三个数据源：Google Scholar（scholarly 库）、OpenAlex、arXiv。其余（S2/INSPIRE/NASA ADS/CrossRef）为可选补充，当前阶段未集成。

---

## Google Scholar（scholarly 库）

**用途**：论文列表主源（学者本人维护，最全）。h-index、引用数、email_domain（身份金标准）。

| 方法 | 用途 |
|:-----|:------|
| `scholarly.search_author_id(gs_id)` | 按 GS ID 取 profile |
| `scholarly.fill(author, sections=["publications", "indices"])` | 取全量论文 + 指标 |

**用法**（已封装为 step2_gs.py）：

```bash
python src/phase1/step2_gs.py XXXXXXXXAAAAJ --prof-dir "output/..."
```

**限制**：
- 不返回 DOI、arXiv ID、作者列表（由 OpenAlex 补充）
- 期刊名夹杂卷期号（如 "Physical Review A 83 (5), 052707"）
- 梯子节点质量直接影响可用性。403 时换节点重试

**输出字段**：

| scholarly 字段 | 输出字段 |
|:---------------|:---------|
| `filled["name"]` | `professor.name` |
| `filled["email_domain"]` | `professor.email_domain`（身份金标准） |
| `filled["hindex"]` | `professor.h_index` |
| `filled["i10index"]` | `professor.i10_index` |
| `filled["citedby"]` | `professor.total_citations` |
| `pub["bib"]["title"]` | `paper.title` |
| `pub["num_citations"]` | `paper.citation_count` |

---

## OpenAlex

**用途**：论文元数据补充（DOI/期刊/作者列表）。教授 profile 次要源（h-index 可能不准）。

| 端点 | 用途 | 参数 |
|:-----|:------|:------|
| `GET /authors/{id}` | 作者 profile（ORCID/h-index/机构） | 无 |
| `GET /works?filter=authorships.author.id:{id}` | 全量论文 | `per_page=200&cursor=*` |

**用法**（已封装为 step3_openalex.py）：

```bash
python src/phase1/step3_openalex.py A5000000000 --email you@example.com --prof-dir "output/..."
```

**限速**：polite pool 10 req/s（带 email），无 email 约 1 req/s。

**分页**：works 总数超过 200 时用 cursor 分页：

```
第一次: GET /works?filter=authorships.author.id:A123456789&per_page=200&cursor=*
响应: meta.next_cursor = "abcd"
第二次: GET /works?filter=authorships.author.id:A123456789&per_page=200&cursor=abcd
```

**已知问题**：
- 对中文学者覆盖约 22-38%（Zheng et al. 2025）
- h-index 和 affiliation 可能因身份消歧错误而非本人（Zhao & Chen 2025）
- **以 GS 数据为准**，OA 只做元数据补充

**输出字段**：

| OpenAlex 字段 | 输出字段 |
|:--------------|:---------|
| `display_name` | `professor.name`（被 GS 覆盖） |
| `h_index` | `professor.h_index`（被 GS 覆盖） |
| `orcid` | `professor.orcid` |
| `paper["title"]` | `paper.title` |
| `publication_date[:4]` | `paper.year` |
| `primary_location.source.display_name` | `paper.journal` |
| `paper["doi"]` | `paper.doi` |
| `cited_by_count` | `paper.citation_count` |
| `authorships[].author.display_name` | `paper.authors` |

---

## arXiv

**用途**：预印本补充，补 GS 可能遗漏的最新论文。

| 端点 | 用途 |
|:-----|:------|
| `GET /api/query?search_query=au:{query}&sortBy=submittedDate&max_results=200` | 按作者搜（au 支持 AND/OR 组合） |
| `https://arxiv.org/a/{ORCID}.atom2` | 按 ORCID 获取精确论文列表（零噪声，opt-in 机制） |

### 精确匹配（优先）

如果已确认 ORCID，访问 `https://arxiv.org/a/{ORCID}.atom2` 返回该作者在 arXiv 上的所有论文。这是最精确的方式（零噪声），但需要作者已将 ORCID 关联到 arXiv 账号（opt-in 机制）。

### au: 搜索（精确匹配失败时使用）

step5_arxiv.py 自动将 `姓_名`（如 `Wang_Shili`）拆分为 `au:Wang+AND+au:Shili`，搜索作者字段同时出现姓和名的论文。

**用法**：

```bash
python src/phase1/step5_arxiv.py "Wang_Shili" -c "physics.atom-ph physics.optics" --prof-dir "output/..."
```

`-c` 参数传 arXiv 学科分类（来自 step1_discipline 输出），用于减少同名噪声。

**限速**：≥3 秒间隔。响应格式：Atom XML。不支持按 ORCID/DOI 搜索。

### arXiv 论文过滤流程

1. step6_merge.py 按 DOI/arXiv ID/标题 与 GS/OA 匹配，匹配上的合并
2. render_profile.py 对 arXiv-only 论文做门控：
   - **有 DOI** → 保留（可能是尚未被 GS 收录的预印本）
   - **无 DOI** → 过滤（无其他源交叉验证，视为同名噪声）
3. 渲染时在 "剔除论文" 注释中记录被过滤的 arXiv-only 标题

### 已知问题

- `au:` 搜索只按作者名文本匹配，同名干扰率高
- arXiv author identifier 是 opt-in 机制，不是所有作者都有
- `<arxiv:affiliation>` 字段极少出现，格式不统一，**不可用于机构过滤**

---

## 学科识别（step1_discipline）

```bash
python src/phase1/step1_discipline.py --text "阿秒科学、强场物理" --affiliation "中科院物理所"
```

输出 JSON：

```json
{"primary": "atomic_molecular_optical", "confidence": 0.67, "arxiv_categories": ["physics.atom-ph", "physics.optics"]}
```

识别结果中的 `arxiv_categories` 传给 step5_arxiv 的 `-c` 参数，预筛 arXiv 结果。

---

## 可选源（当前阶段 1 未集成）

以下 API 可用但不属于当前 pipeline。阶段 2/3 可能需要：

| 源 | 用途 | 条件 |
|:---|:------|:------|
| Semantic Scholar | TLDR 摘要填充 | 有 S2_API_KEY（免费） |
| INSPIRE-HEP | 高能物理论文 | 学科为 high_energy_physics 时 |
| NASA ADS | 天体物理论文 | 学科为 astrophysics 时 + 有 ADS_API_TOKEN |
| CrossRef | DOI 元数据兜底 | OpenAlex 查不到时备用 |

---

## 全降级模式

三个数据源全部不可用时：

1. 跳过所有需 ID 的源
2. 只做 Web Search + arXiv 按姓名搜 + 官网抓取
3. 画像中标 "所有数据源均不可用"
4. 建议用户检查网络或提供其他 ID 链接

---

## 验证来源

- OpenAlex API: https://docs.openalex.org
- arXiv API: https://info.arxiv.org/help/api
- scholarly: https://github.com/scholarly-python-package/scholarly
- Zheng et al. (2025) OA 中文覆盖: https://doi.org/10.1002/asi.70013
- Zhao & Chen (2025) OA 消歧: https://arxiv.org/html/2502.11610v2

**版本**: v4.0
**生成日期**: 2026-07-01
