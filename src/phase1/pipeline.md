# phase1 pipeline.md — 阶段 1 技术实现文档

**版本**：v1.1
**对应**：计划书第 2 章（工具设计）的技术落地
**目录**：[src/phase1/](../)

---

## 0. 全流程总览（AI 编排 + 脚本执行）

```
┌─────────────────────────────────────────────────────────────────────┐
│  阶段 A（AI 主导）：广域收集 + 身份确认                               │
│                                                                     │
│  [AI] Step 0: 用户输入                                               │
│    → 姓名 + 机构 + 官网 URL                                          │
│                                                                     │
│  [AI] Step 1: 官网抓取                                               │
│    → MCP Fetch 读官网 → 提取姓名/职称/邮箱/研究方向                     │
│    → step1_discipline.py 学科分类                                    │
│                                                                     │
│  [AI] Step 2: 广域搜索                                               │
│    → MCP Serper/Exa 搜：                                             │
│      "{姓名} {机构}" → 百度百科、知乎、新闻                            │
│      "{姓名} Google Scholar" → 找 GS 链接                            │
│      "{姓名} ORCID" → 找 ORCID 链接                                  │
│      "{姓名} ResearchGate" → 找 RG 链接                              │
│    → AI 判断哪些链接属于目标学者（交叉验证邮箱/机构/研究领域）          │
│    → 输出：verified_ids.json（GS ID, OA ID, ORCID, 公开信息笔记）     │
│                                                                     │
│  ← 你审核：这些 ID 对不对？确认或修改                                   │
│                                                                     │
│  阶段 B（脚本 + AI 看门）：深度数据获取                                │
│                                                                     │
│  [脚本] Step 3: GS 数据获取                                          │
│    → step2_gs.py {gs_id} → gs.json                                  │
│  [AI]   GS 质量门：email_domain 是否匹配机构？论文量是否合理？          │
│         → 不通过：换 GS ID 或标记降级                                  │
│                                                                     │
│  [脚本] Step 4: OpenAlex 数据获取                                    │
│    → step3_openalex.py {oa_id} → oa.json                            │
│  [AI]   OA 质量门：h-index 是否与 GS 接近？论文主题是否匹配研究方向？   │
│         → 不通过：标记"OA 数据可能错位"                                │
│                                                                     │
│  [脚本] Step 5: arXiv 搜索                                           │
│    → step5_arxiv.py "{姓名拼音}" → arxiv.json                       │
│  [AI]   arXiv 质量门：是否有同名噪声？返回论文是否含目标作者？         │
│         → 不通过：标记"arXiv 同名干扰严重"                             │
│                                                                     │
│  [脚本] Step 6: 合并去重                                             │
│    → step6_merge.py gs.json oa.json arxiv.json → merged.json       │
│  [AI]   合并质量门：总论文数是否合理？多源交叉验证比例？               │
│                                                                     │
│  阶段 C（AI 主导）：渲染输出                                         │
│                                                                     │
│  [AI] Step 7: 写画像                                                │
│    → 读 merged.json + 公开信息笔记                                   │
│    → 按模板填充 9 节                                                 │
│    → 论文按学术履历阶段分组（博士/博后/独立）                         │
│    → 输出：output/导师/<姓名>/01_基础画像.md                          │
│                                                                     │
│  ← 你审阅画像：质量是否达到要求？                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. 通用数据模式

（同 v1.0，不变）

每步脚本的输出格式统一。这是让管道无需手动转格式的关键。

### 1.1 单篇论文（每步都产）

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

### 1.2 源输出（每步脚本产）

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

### 1.3 合并输出（step6 产）

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
  "professor": { ... },
  "papers": [
    {
      "title": "...",
      "year": 2020,
      "authors": [...],
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
    "by_source": {"google_scholar": 56, "openalex": 14, "arxiv": 3}
  }
}
```

### 1.4 verified_ids.json（阶段 A 产出）

```json
{
  "name": "张鹏举",
  "name_en": "Pengju Zhang",
  "institution": "中科院物理所",
  "gs_id": "ls7XuGoAAAAJ",
  "oa_id": "A5000914228",
  "orcid": "0000-0001-7746-2113",
  "email_domain": "@iphy.ac.cn",
  "homepage_url": "http://english.iphy.ac.cn/...",
  "identity_verified": true,
  "identity_evidence": "GS email_domain matches institution domain",
  "public_notes": [
    {"source": "百度百科", "url": "https://baike.baidu.com/...", "note": "中科院物理所研究员"},
    {"source": "知乎", "url": "https://zhihu.com/...", "note": "采访：阿秒光源进展"}
  ],
  "known_issues": []
}
```

### 1.5 教授信息合并优先级

当前实现（step6_merge.py 的 PROF_PRIORITY 表）：

| 字段 | 优先源 | 说明 |
|:----|:-------|:-----|
| `name` | GS > OA | 学者自己维护的姓名（GS）优先 |
| `affiliation` | GS > OA | GS 更准确（OA 可能过时） |
| `email_domain` | **仅 GS** | 身份金标准，其他源不提供 |
| `gs_id` | **仅 GS** | |
| `oa_id` | **仅 OA** | |
| `orcid` | **仅 OA** | |
| `h_index` | GS > OA | GS 是学者本人维护 |
| `i10_index` | **仅 GS** | OA 不提供 |
| `total_citations` | GS > OA | GS 覆盖更全 |

---

## 2. 各步骤详情

### 2.0 Step 0-2（AI 主导，见第 0 节总览）

这些步骤不由 Python 脚本执行，而是由 Claude Code 根据本文档指令执行：
- MCP 工具做 web search
- AI 判断结果可信度
- 产出 verified_ids.json

### 2.1 step1_discipline.py — 学科分类

| 项目 | 内容 |
|:----|:------|
| **输入** | `--text` 研究方向文本，`--affiliation` 机构名 |
| **输出** | stdout JSON（学科ID、置信度、命中关键词、arXiv 分类） |
| **算法** | 关键词字典匹配（config/sources.json） |
| **网络** | 无（本地匹配） |
| **依赖** | 标准库，config/sources.json |

```bash
python src/phase1/step1_discipline.py --text "阿秒科学、强场物理" --affiliation "中科院物理所"
```

### 2.2 step2_gs.py — Google Scholar 数据获取

| 项目 | 内容 |
|:----|:------|
| **输入** | `gs_id`（GS profile ID） |
| **中间件** | scholarly 库（2K⭐） |
| **输出** | 统一 SOURCE_OUTPUT 格式 JSON |
| **网络** | 需要访问 scholar.google.com |
| **依赖** | `pip install scholarly` |

**scholarly 限制**：不返回 DOI、arXiv ID、作者列表。期刊名含卷期号混杂。以上由 merger 从 OA 和 arXiv 补。

**失败处理**：
- 403 → 换梯子节点重试
- 节点都 403 → 接受降级（merger 用 OA + arXiv）

### 2.3 step3_openalex.py — OpenAlex 数据获取

| 项目 | 内容 |
|:----|:------|
| **输入** | `oa_id`（如 A5000914228） |
| **API** | openalex.org |
| **输出** | 统一 SOURCE_OUTPUT 格式 JSON |
| **依赖** | 标准库 |
| **限速** | 加 `--email` 入 polite pool 10 req/s |

**注意**：OpenAlex 对中文学者的 profile 数据（h-index、affiliation）可能不准确（Zheng et al. 2025）。AI 质量门会对比 GS 和 OA 的 h-index 差异。差异大时标记"OA 数据可能错位"。

### 2.4 step5_arxiv.py — arXiv 预印本搜索

| 项目 | 内容 |
|:----|:------|
| **输入** | `author_name`（下划线拼音） |
| **API** | export.arxiv.org |
| **输出** | 统一 SOURCE_OUTPUT 格式 JSON |
| **依赖** | 标准库 |
| **限速** | arXiv 要求 ≥3 秒间隔 |

**同名噪声**：arXiv 按姓名搜索，返回大量同名作者论文。AI 质量门会检查首篇论文的 arXiv 分类和作者机构，判断是否为同一人。噪声严重的参数在 merger 中通过 DOI/标题匹配 GS 和 OA 已确认的论文来自动过滤。

### 2.5 step6_merge.py — 多源合并

| 项目 | 内容 |
|:----|:------|
| **输入** | N 个统一格式的 JSON 文件 |
| **输出** | MERGED_OUTPUT 格式 JSON |
| **去重** | P0:DOI → P1:arXiv ID → P2:归一化标题 |
| **引用数选取** | OA > GS（OA 日更新） |
| **期刊名选取** | OA > GS |
| **教授信息** | 按 §1.5 优先级合并 |

---

## 3. AI 质量门检查清单

每步脚本执行后，Claude Code 检查以下内容：

### 3.1 GS 质量门

```yaml
检查项:
  - email_domain 是否匹配机构域名
  - 论文数是否 < 5 篇（太少了，可能是空 profile 或同名）
  - h-index 是否存在且 > 0
  - 引文数是否存在且 > 0
决策:
  全部通过 → 继续
  email 不匹配 → 标记"GS 邮箱校验未通过，可能同名"
  论文数 < 5 篇 → 标记"GS profile 可能不完整"
```

### 3.2 OA 质量门

```yaml
检查项:
  - h-index 与 GS 差异是否 > 50%
  - 论文主题是否与导师研究方向一致（检查论文标题关键词）
  - ORCID 是否存在
决策:
  h-index 与 GS 差异大 → 标记"OA 数据可能错位，以 GS 为准"
  主题不匹配 → 标记"OA ID 可能属于同名不同人"
```

### 3.3 arXiv 质量门

```yaml
检查项:
  - 返回论文的第一作者是否包含目标姓名
  - arXiv 分类是否与学科一致
  - 返回论文中哪些与 GS/OA 已确认的论文匹配（by DOI/标题）
决策:
  0 篇匹配 GS → 标记"arXiv 噪声率高，结果仅供参考"
  有匹配 → 从确认论文反向筛选
```

### 3.4 合并质量门

```yaml
检查项:
  - 总论文数是否 > 5 篇
  - 至少 1 个源成功
  - 多源交叉验证比例（多个源确认的论文数 / 总论文数）
决策:
  总论文数 0 → 标记"所有数据源均不可用"
  多源比例 < 10% → 标记"各源间重叠少，合并效果有限"
```

---

## 4. 错误处理与重试

### 4.1 脚本级错误

脚本不抛异常退出。所有故障用 `status` 字段表示。

```json
{"status": "error", "error": "HTTP 403: GS blocked"}
```

### 4.2 AI 级重试

Claude Code 见到 `status: "error"` 后：

```
1. 如果是网络错误（403/429/5xx）：
   → 等待 60 秒后重试同一命令
   → 重试 2 次失败后标记"源不可用"，继续下一步

2. 如果是格式错误（空结果/字段缺失）：
   → 检查参数是否正确（GS ID 是否正确？）
   → 尝试替代参数后重试
   → 仍失败后标记"参数错误"

3. 如果是质量门不通过：
   → 不自动重试，在画像中标注"数据可能有问题"
```

### 4.3 完全降级

三个数据源全部不可用时：

```
step6 输出 {"status": "error", "papers": []}
AI 渲染时写：
  "由于所有数据源均不可用，无法生成论文列表"
  "请检查网络连接或提供其他 ID 链接"
```

---

## 5. 调用关系与数据流

```bash
# 阶段 A（AI 做：web search → verified_ids.json）
# 你审核

# 阶段 B（脚本 + AI 看门）
python src/phase1/step2_gs.py {gs_id} -o output/导师/<姓名>/gs.json
# AI 检查 gs.json
# → pass: 继续
# → fail: 换 ID 或标记降级

python src/phase1/step3_openalex.py {oa_id} -o output/导师/<姓名>/oa.json
# AI 检查 oa.json

python src/phase1/step5_arxiv.py "{姓名拼音}" -o output/导师/<姓名>/arxiv.json
# AI 检查 arxiv.json

python src/phase1/step6_merge.py output/导师/<姓名>/gs.json output/导师/<姓名>/oa.json output/导师/<姓名>/arxiv.json -o output/导师/<姓名>/merged.json
# AI 检查 merged.json

# 阶段 C（AI 做：读 merged.json → 写 01_基础画像.md）
# 你审阅
```

---

## 6. 输出文件清单

```
output/导师/<姓名>/
├── verified_ids.json   # 阶段 A：AI 确认的身份信息
├── gs.json             # step2_gs.py 输出
├── oa.json             # step3_openalex.py 输出
├── arxiv.json          # step5_arxiv.py 输出
├── merged.json         # step6_merge.py 输出
└── 01_基础画像.md       # 最终画像（在上一级或同级）
```

---

## 7. 版本记录

| 版本 | 日期 | 变更 |
|:----|:-----|:------|
| v1.1 | 2026-07-01 | 加入全流程总览（AI 编排 + 脚本执行）、AI 质量门、错误处理与重试 |
| v1.0 | 2026-07-01 | 初版。scholarly 主力、统一输出格式、去除 oa_enrich 和旧爬虫 |
