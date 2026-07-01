# phase1 pipeline.md — 阶段 1 技术实现文档

**版本**：v1.0
**对应**：计划书第 2 章（工具设计）的技术落地
**目录**：[src/phase1/](../)

---

## 1. 流水线总览

```
                   ┌──────────────────────────────────────┐
                   │          用户输入                     │
                   │  姓名 + 机构 + GS ID + OA ID + URL    │
                   └────────────────┬─────────────────────┘
                                    │
                                    ▼
              ┌─────────────────────────────────────────┐
              │  step1_discipline.py                     │
              │  官网文本 → 学科分类                    │
              │  输出：学科标签JSON                      │
              └─────────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │  step2_gs.py     │  │ step3_openalex   │  │ step5_arxiv.py   │
   │  scholarly封装   │  │ OpenAlex API     │  │ arXiv API        │
   │  GS profile +    │  │ 作者论文 + 元数  │  │ 按姓名搜预印本   │
   │  论文 + 指标     │  │ 据 + h-index     │  │                  │
   │  → gs.json       │  │ → oa.json        │  │ → arxiv.json     │
   └──────────────────┘  └──────────────────┘  └──────────────────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
              ┌─────────────────────────────────────────┐
              │  step6_merge.py                          │
              │  3 源输入 → 去重 + 教授信息合并          │
              │  P0:DOI → P1:arXiv ID → P2:归一化标题    │
              │  → merged.json                            │
              └─────────────────────────────────────────┘
                                    │
                                    ▼
              ┌─────────────────────────────────────────┐
              │  AI 渲染（Claude Code）                   │
              │  读 merged.json → 按模板填充 9 节        │
              │  → output/导师/<姓名>/01_基础画像.md      │
              └─────────────────────────────────────────┘
```

---

## 2. 通用数据模式

每步脚本的输出格式统一。这是让管道无需手动转格式的关键。

### 2.1 单篇论文（每步都产）

```json
{
  "title": "Electron emission from single-electron capture...",
  "year": 2011,
  "authors": null,
  "journal": "Physical Review A 83 (5), 052707",
  "doi": null,
  "arxiv_id": null,
  "citation_count": 88,
  "source": "google_scholar",
  "abstract": null
}
```

### 2.2 源输出（每步产）

```json
{
  "pipeline": "phase1",
  "source": "google_scholar",
  "status": "success",
  "error": null,
  "professor": {
    "name": "Pengju Zhang",
    "affiliation": "Institute of Physics, CAS",
    "email_domain": "@iphy.ac.cn",
    "gs_id": "ls7XuGoAAAAJ",
    "oa_id": "A5000914228",
    "orcid": null,
    "h_index": 15,
    "i10_index": 20,
    "total_citations": 732
  },
  "papers": [ ... ],
  "metadata": {
    "publication_count": 56
  }
}
```

**status** 取值：`success` / `blocked` / `empty` / `error`

**字段命名的原则**：全小写、下划线分隔。引用数统一叫 `citation_count`，不混用 `citations` / `cited_by_count` / `num_citations`。

### 2.3 合并输出（step6 产）

```json
{
  "pipeline": "phase1",
  "step": "merge",
  "sources_used": ["google_scholar", "openalex", "arxiv"],
  "source_status": {
    "google_scholar": "success",
    "openalex": "success",
    "arxiv": "success"
  },
  "professor": {
    "name": "Pengju Zhang",
    "affiliation": "Institute of Physics, CAS",
    "email_domain": "@iphy.ac.cn",
    "gs_id": "ls7XuGoAAAAJ",
    "oa_id": "A5000914228",
    "orcid": "0000-0001-7746-2113",
    "h_index": 15,
    "i10_index": 20,
    "total_citations": 732
  },
  "papers": [
    {
      "title": "...",
      "year": 2020,
      "authors": ["Author 1", "Author 2"],
      "journal": "Phys. Rev. Lett.",
      "doi": "10.1103/PhysRevLett.125.123456",
      "arxiv_id": "2005.12345",
      "citation_count": 42,
      "source": "openalex",
      "sources": ["openalex", "google_scholar"],
      "source_count": 2,
      "abstract": "We report..."
    }
  ],
  "statistics": {
    "total": 60,
    "by_source": {"google_scholar": 56, "openalex": 14, "arxiv": 3},
    "unique": 60
  }
}
```

### 2.4 教授信息传播规则

| 字段 | 优先源 | 说明 |
|:----|:-------|:-----|
| `name` | **step3** OpenAlex | OA 的 `display_name` 最规范 |
| `affiliation` | **step3** OpenAlex | `last_known_institutions` |
| `email_domain` | **step2** GS | `email_domain`（身份金标准） |
| `gs_id` | **step2** GS | 用户输入 |
| `oa_id` | **step3** OA | 用户输入 |
| `orcid` | **step3** OA | OA profile 的 orcid |
| `h_index` | **step3** OA（优先），step2 GS 备用 | OA 的 h-index 更新更及时 |
| `i10_index` | **step2** GS（唯一源） | OA 不提供 |
| `total_citations` | **step3** OA（优先），step2 GS 备用 | OA 日更新 |

---

## 3. 各步骤详情

### 3.1 step1_discipline.py — 学科分类

| 项目 | 内容 |
|:----|:------|
| **输入** | `--text` 研究方向文本，`--affiliation` 机构名 |
| **输出** | stdout JSON（学科ID、置信度、命中关键词、arXiv 分类） |
| **算法** | 关键词字典匹配（config/sources.json） |
| **网络** | 无（本地匹配） |
| **依赖** | 标准库，config/sources.json |

**示例**：
```bash
python src/phase1/step1_discipline.py --text "阿秒科学、强场物理" --affiliation "中科院物理所"
# → {"primary": "atomic_molecular_optical", "confidence": 0.67, ...}
```

### 3.2 step2_gs.py — Google Scholar 数据获取

| 项目 | 内容 |
|:----|:------|
| **输入** | `gs_id`（GS profile ID） |
| **中间件** | scholarly 库（2K⭐） |
| **输出** | 统一 SOURCE_OUTPUT 格式 JSON |
| **网络** | 需要访问 scholar.google.com（建议用好的梯子节点） |
| **依赖** | `pip install scholarly` |
| **缓存** | 无（scholarly 一次调用，56 篇全回，不重复请求） |

**输出字段映射**：

| scholarly 字段 | 输出字段 | 备注 |
|:---------------|:---------|:-----|
| `filled["name"]` | `professor.name` | |
| `filled["affiliation"]` | `professor.affiliation` | |
| `filled["email_domain"]` | `professor.email_domain` | 身份金标准 |
| `filled["hindex"]` | `professor.h_index` | |
| `filled["i10index"]` | `professor.i10_index` | |
| `filled["citedby"]` | `professor.total_citations` | |
| `pub["bib"]["title"]` | `paper.title` | |
| `pub["bib"]["pub_year"]` | `paper.year` | 字符串转 int |
| `pub["num_citations"]` | `paper.citation_count` | |
| `pub["bib"]["citation"]` | `paper.journal` | 含卷/期/页码的字符串 |

**scholarly 返回内容的限制**：
- 不返回 DOI（需要 oa.json 补充）
- 不返回 arXiv ID（需要 arxiv.json 补充）
- 不返回作者列表
- 期刊名夹杂卷期号（`"Physical Review A 83 (5), 052707"`）
- 以上由 step6_merge 从 OA 和 arXiv 数据中补充

**限速**：scholarly 内部的 requests 自带限速。对 80 人规模，每人 1 次请求，全量约 80 次，分多批次跑。一次阶梯可能触发 CAPTCHA → 停手 1h 或换梯子节点。（没有硬性的"一次最多跑多少人"公式，看梯子节点的信誉度。）

### 3.3 step3_openalex.py — OpenAlex 数据获取

| 项目 | 内容 |
|:----|:------|
| **输入** | `oa_id`（OpenAlex Author ID，如 A5000914228） |
| **API** | `https://api.openalex.org/authors/{id}` → profile |
| | `https://api.openalex.org/works?filter=authorships.author.id:{id}` → 全部论文 |
| **输出** | 统一 SOURCE_OUTPUT 格式 JSON |
| **网络** | 需要 API.openalex.org |
| **依赖** | 标准库 |
| **限速** | polite pool 10 req/s（加 `--email`），无 email 约 1 req/s |

**论文输出字段映射**：

| OpenAlex API 字段 | 输出字段 |
|:-----------------|:---------|
| `paper["title"]` | `title` |
| `paper["publication_date"][:4]` | `year` |
| `authors => author.display_name` | `authors`（list） |
| `primary_location.source.display_name` | `journal` |
| `paper["doi"] 或 location["doi"]` | `doi` |
| `paper["cited_by_count"]` | `citation_count` |
| `paper["type"]` | 不导出（保留到 metadata） |

### 3.4 step5_arxiv.py — arXiv 预印本搜索

| 项目 | 内容 |
|:----|:------|
| **输入** | `author_name`（下划线分隔拼音，如 Zhang_Pengju） |
| **API** | `https://export.arxiv.org/api/query?search_query=au:{name}` |
| **输出** | 统一 SOURCE_OUTPUT 格式 JSON |
| **网络** | 需要 export.arxiv.org |
| **依赖** | 标准库 |
| **限速** | arXiv 要求 ≥3 秒间隔 |

**论文输出字段映射**：

| arXiv API 字段 | 输出字段 |
|:--------------|:---------|
| `entry:title` | `title` |
| `entry:published[:4]` | `year` |
| `entry:author > name` | `authors` |
| `entry:link[@href~doi.org]` | `doi` |
| `entry:id` | `arxiv_id` |
| `entry:summary` | `abstract`（截断前 200 字） |

**同名噪声**：arXiv 按姓名搜索，同名作者论文会返回。去重由 step6_merge 负责——通过 DOI 和标题匹配过滤非目标作者论文。

### 3.5 step6_merge.py — 多源合并

| 项目 | 内容 |
|:----|:------|
| **输入** | N 个统一格式的 JSON 文件（gs.json, oa.json, arxiv.json, ...） |
| **输出** | MERGED_OUTPUT 格式 JSON |
| **去重优先级** | P0:DOI → P1:arXiv ID → P2:归一化标题匹配 |
| **引用数选取** | OA > S2 > GS（OA 日更新，GS 不更新） |
| **期刊名选取** | OA > 其他 |
| **年份选取** | OA > arXiv > GS |

**教授信息合并规则**：后加载的源覆盖前一个源的同名字段（name, affiliation, h_index 等）。email_domain 只来自 GS（其他源不提供）。

**去重逻辑**：
1. DOI 完全匹配 → 同一篇
2. arXiv ID 去版本号后匹配 → 同一篇
3. 归一化标题精确或子串匹配 → 同一篇
4. 不满足以上条件 → 不同论文
5. 匹配到的条目合并 fields（取优先级最高的值）

---

## 4. 调用关系与数据流

```
# 完整流水线（shell/CLI）
python src/phase1/step1_discipline.py --text "..." --affiliation "..." > discipline.json

python src/phase1/step2_gs.py ls7XuGoAAAAJ -o gs.json
python src/phase1/step3_openalex.py A5000914228 -o oa.json
python src/phase1/step5_arxiv.py "Zhang_Pengju" -o arxiv.json

python src/phase1/step6_merge.py gs.json oa.json arxiv.json -o merged.json

# merged.json → AI 读取 → 写 output/导师/<姓名>/01_基础画像.md
```

每步独立通过 JSON 文件通信。不互相 import（保持解耦）。任一步失败不影响其他步。

---

## 5. 可选组件：step_s2.py

Semantic Scholar TLDR 摘要填充。开箱即用不需要它，但加上能让画像的「每篇论文的 TLDR 摘要」一栏更充实。

| 项目 | 内容 |
|:----|:------|
| **输入** | N 个 JSON 文件（提取 DOI） |
| **输出** | S2 source 格式 JSON |
| **要求** | `S2_API_KEY` 环境变量（免费，5000 req/min） |
| **不设 key** | 自动降级到逐个请求（100 req/5 min） |

如果 merged.json 已经包含 TLDR（来自 OpenAlex 的 abstract 字段），step_s2 是锦上添花。初期可以跳过。

---

## 6. 错误处理策略

| 场景 | 行为 |
|:-----|:------|
| GS 403 blocked | step2 输出 `status: "blocked"`，papers 为空。merger 用 OA + arXiv 数据 |
| OA 网络错误 | step3 输出 `status: "error"`。merger 仅用 GS + arXiv |
| arXiv 无结果 | step5 输出 `status: "empty"`。merger 仅用 GS + OA |
| 所有源都不可用 | step6 输出 `status: "error"`，无论文。AI 渲染时写明"所有数据源均不可用" |
| 某篇论文在 OA 有 DOI、在 arXiv 有全文 | merger 按去重规则合并为一篇，取各源最优字段 |
| 期刊名在 GS 是"Physical Review A 83 (5), 052707"，在 OA 是"Physical Review A" | merger 取 OA 的期刊名（优先级高） |

**不报错退出原则**：所有源失败时，脚本用 `status` 字段标记错误而非抛出异常。下游脚本根据 `status` 确定是否还有数据可合并。

---

## 7. 缓存策略

scholarly 一次调用返回 56 篇。缓存不是必须的（每次请求成本低）。

但如果需要缓存（断点续跑场景），用 `src/phase1/cache.py`：

```python
from utils import CacheManager
cache = CacheManager()
cached = cache.get("gs", user_id)
```

---

## 8. 输出文件清单

```
output/导师/<姓名>/
├── gs.json          # step2_gs.py 输出
├── oa.json          # step3_openalex.py 输出
├── arxiv.json       # step5_arxiv.py 输出
└── merged.json      # step6_merge.py 输出
```

`01_基础画像.md` 不放在这里，由 AI 单独渲染到 `output/导师/<姓名>/01_基础画像.md`。

---

## 9. 版本记录

| 版本 | 日期 | 变更 |
|:----|:-----|:------|
| v1.0 | 2026-07-01 | 初版。scholarly 主力、统一输出格式、去除 oa_enrich 和旧爬虫 |
