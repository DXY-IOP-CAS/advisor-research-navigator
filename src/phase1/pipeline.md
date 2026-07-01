# phase1 pipeline.md — 阶段 1 技术实现文档

**版本**：v2.0（完整重写）
**对应**：计划书第 2 章（工具设计）的技术落地
**目标读者**：实施此流水线的研究者、维护者

---

## 0. 全流程总览

用户给 3 条信息：导师姓名、机构、官网 URL。系统全自动跑出 `01_基础画像.md`。中间无人工闸。

```
                    用户输入（自然语言）
   姓名（张鹏举）+ 机构（中科院物理所）+ 官网 URL
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  阶段 A（AI 主导）                                              │
│  ─ 读官网 → 学科分类 → 广域搜 GS/ORCID/UCAS → 邮箱交叉验证     │
│  输出：verified_ids.json                                         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  阶段 B（脚本执行）                                              │
│  ─ GS (scholarly) → OA (REST API) → arXiv → 合并去重             │
│  输出：00/01/02/03/04_*.json（5 个中间文件）                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  阶段 C（脚本渲染 + AI 润色）                                     │
│  ─ render_profile.py 生成论文表格+统计 → AI 补充叙事/合作/公开信息│
│  输出：01_基础画像.md                                             │
└─────────────────────────────────────────────────────────────────┘
```

**核心特性**：
- **存档不是缓存**：每次运行从头查 API；archive/ 目录只用于错误溯源
- **统一输出格式**：所有阶段共享 SOURCE_OUTPUT / MERGED_OUTPUT schema
- **AI 质量门**：每步脚本后 AI 检查数据合理性（h-index、机构匹配、同名噪声）
- **退避重试**：API 失败自动 retry（utils.py 的 `@retry` 装饰器）

---

## 1. 文件清单（src/phase1/）

| 文件 | 用途 | 必选 |
|:-----|:-----|:----:|
| `step1_discipline.py` | 关键词字典分类（无网络） | ✅ |
| `step2_gs.py` | scholarly 封装取 GS profile | ✅ |
| `step3_openalex.py` | OpenAlex API 取论文+元数据 | ✅ |
| `step5_arxiv.py` | arXiv API 搜索预印本 | ✅ |
| `step6_merge.py` | 三源合并去重+教授信息合并 | ✅ |
| `render_profile.py` | 从 merged.json 生成画像（含超链接） | ✅ |
| `utils.py` | 共享：匹配函数、限速器、retry 装饰器 | ✅ |
| `pipeline.md` | 本文档 | — |

每个脚本的模块级 docstring 都包含：
- 流水线位置（阶段 A/B/C 第几步）
- 数据流图（ASCII 输入输出）
- 输出格式（JSON 字段清单）
- 关键约束与已知问题
- CLI 用法示例

---

## 2. 通用数据模式（所有脚本共用的契约）

### 2.1 单篇论文

```json
{
  "title": "...",        // 必填
  "year": 2020,           // int 或 null
  "authors": ["..."],     // list[str] 或 null
  "journal": "...",       // str 或 null
  "doi": "10.1103/...",   // 完整 URL 或裸 ID 或 null
  "arxiv_id": "2005.12345",  // 去掉版本后缀
  "citation_count": 42,   // int 或 null
  "source": "google_scholar"  // 字符串枚举
}
```

### 2.2 SOURCE_OUTPUT（每个数据源脚本产出）

```json
{
  "pipeline": "phase1",
  "source": "google_scholar | openalex | arxiv",
  "status": "success | blocked | error | empty",
  "error": null,
  "professor": {
    "name": str | null,
    "affiliation": str | null,
    "email_domain": str | null,
    "gs_id": str | null,
    "oa_id": str | null,
    "orcid": str | null,
    "h_index": int | null,
    "i10_index": int | null,
    "total_citations": int | null
  },
  "papers": [ 单篇论文, ... ],
  "metadata": { /* step-specific */ }
}
```

### 2.3 MERGED_OUTPUT（step6_merge.py 产出）

```json
{
  "pipeline": "phase1",
  "step": "merge",
  "sources_used": ["google_scholar", "openalex", "arxiv"],
  "source_status": { ... },
  "professor": { ... 合并后的 },
  "papers": [
    {
      ...单篇论文字段,
      "sources": ["google_scholar", "openalex"],  // 多源验证标记
      "source_count": 2
    }
  ],
  "statistics": {
    "total": 75,
    "by_source": {"google_scholar": 54, "openalex": 13, "arxiv": 16}
  }
}
```

---

## 3. 阶段 A：广域搜索 + 身份确认（AI 主导）

### 3.1 步骤 1：官网抓取 + 学科分类

```
[AI] MCP Fetch 读官网
        ↓
    提取：姓名（中文+拼音）、职称、邮箱、研究方向文本
        ↓
[脚本] python src/phase1/step1_discipline.py \
        --text "研究方向关键词" \
        --affiliation "机构名"
        ↓
    输出（stdout JSON）：primary 学科 ID、arxiv_categories 列表
```

`step1_discipline.py` 是纯本地匹配，不发网络请求。`arxiv_categories` 传给 step5_arxiv 减少噪声。

### 3.2 步骤 2：广域搜索 + 身份确认

```
[AI] MCP Serper/Exa 搜：
    "{姓名} {机构}"     → 百科/新闻/采访
    "{姓名} Google Scholar"  → 找 GS profile URL
    "{姓名} ORCID"        → 找 ORCID URL
        ↓
[AI] 邮箱交叉验证：
    GS 头部 "Verified email at" 域名 == 官网邮箱域名？
        ↓
    是 → 身份确认。输出 verified_ids.json（结构见 3.3）
    否 → 标记"身份存疑"，按需降级到 OA/arXiv 姓名搜索
```

**邮箱匹配规则**：
- 域名一致（`@iphy.ac.cn` vs `@iphy.ac.cn`）→ 信任
- 域名不一致 → 不通过
- GS 不显示邮箱 → 标记"邮箱未验证"

### 3.3 verified_ids.json

```json
{
  "name": "张鹏举",
  "name_en": "Pengju Zhang",
  "institution": "中科院物理所",
  "department": "超快物质科学中心",
  "gs_id": "ls7XuGoAAAAJ",
  "oa_id": "A5000914228",
  "orcid": "0000-0001-7746-2113",
  "email_domain": "@iphy.ac.cn",
  "homepage_url": "https://edu.iphy.ac.cn/?q=detail_teacher&id=6368",
  "identity_verified": true,
  "identity_evidence": "GS email @iphy.ac.cn matches homepage domain",
  "public_notes": [
    {"source": "UCAS", "url": "https://people.ucas.ac.cn/~0052353", "note": "..."},
    {"source": "IPHY news", "url": "https://www.iop.cas.cn/...", "note": "..."}
  ],
  "career_stages": [   // 可选，提供给 render_profile.py
    {"start": 2010, "end": 2013, "name": "近代物理所博士"},
    {"start": 2013, "end": 2016, "name": "RIKEN 博后"},
    {"start": 2018, "end": 2021, "name": "ETH 博士后"},
    ...
  ]
}
```

---

## 4. 阶段 B：脚本数据获取

### 4.1 步骤 3：GS（scholarly 库）

```bash
python src/phase1/step2_gs.py {gs_id} -o archive/<ts>/01_gs.json
```

**输入**：`gs_id`（URL 中 `?user=XXX` 部分）
**输出**：`01_gs.json`，含 professor（h-index、email_domain）+ 56 篇论文
**限制**：不返回 DOI/arXiv ID（由 step3/step5 补）

**AI 质量门**：
- email_domain 匹配机构域？→ 不匹配标记"身份存疑"
- 论文数 > 5 篇？→ 太少标记"profile 可能不完整"
- 403 错误 → 换梯子节点重试

### 4.2 步骤 4：OpenAlex

```bash
python src/phase1/step3_openalex.py {oa_id} \
  --email your@real.com -o archive/<ts>/02_oa.json
```

**输入**：`oa_id`（A5000914228）+ **真实 email**（polite pool）
**输出**：`02_oa.json`，含 professor（ORCID、h-index）+ 14 篇论文（含 DOI/期刊/作者）

**⚠️ 关键：email 必须是真实邮箱**
- 真实邮箱 + `@` + 有效 TLD：polite pool 10 req/s
- 假邮箱（`example.com` / `x.com`）或无 email：限速 1 req/s
- Subagent 测试发现的 503 问题根因：用了 `test@example.com` 触发 10 req/s → OpenAlex 当匿名处理 → 超限 → 503

**AI 质量门**：
- h-index 与 GS 差异 > 50%？→ 标记"OA 数据错位，以 GS 为准"
- affiliation 不匹配官网机构？→ 标记"OA 机构信息错位"
- 论文主题不匹配研究方向？→ 标记"OA ID 可能属于同名不同人"

### 4.3 步骤 5：arXiv

```bash
python src/phase1/step5_arxiv.py "Zhang_Pengju" \
  -c "physics.atom-ph physics.optics" \
  -o archive/<ts>/03_arxiv.json
```

**输入**：姓名拼音（姓_名格式）+ arXiv 分类（来自 step1 输出）
**输出**：`03_arxiv.json`，含 16 篇预印本

**已知问题**：
- `au:` 搜索按姓名匹配，同名噪声率高（常见中文名 ~80%）
- 加 `-c` 学科分类可降低噪声
- 噪声过滤由 step6 通过 DOI/标题匹配 GS/OA 已确认论文完成

**AI 质量门**：
- 有 DOI/标题与 GS/OA 匹配的论文？→ 标记"已确认部分"
- 无任何匹配 → 标记"arXiv 噪声严重，结果仅供参考"

### 4.4 步骤 6：合并去重

```bash
python src/phase1/step6_merge.py \
  archive/<ts>/01_gs.json \
  archive/<ts>/02_oa.json \
  archive/<ts>/03_arxiv.json \
  -o archive/<ts>/04_merged.json
```

**输入**：N 个 SOURCE_OUTPUT 格式 JSON
**输出**：MERGED_OUTPUT 格式 JSON

**处理逻辑**：
1. 教授信息合并（PROF_PRIORITY 字段优先级表）
2. 论文去重（P0:DOI → P1:arXiv ID → P2:归一化标题）
3. 字段择优（引用数 OA > GS；期刊名 OA > GS）
4. 多源交叉验证标记

**PROF_PRIORITY**（合并优先级）：

| 字段 | 优先源 | 理由 |
|:-----|:-------|:-----|
| name | GS > OA | 学者自己维护的姓名更准 |
| affiliation | GS > OA | GS 通常更准确 |
| email_domain | **仅 GS** | 身份金标准 |
| gs_id | **仅 GS** | — |
| oa_id | **仅 OA** | — |
| orcid | **仅 OA** | — |
| h_index | GS > OA | GS 是学者维护；OA 算法可能错 |
| i10_index | **仅 GS** | OA 不提供 |
| total_citations | GS > OA | GS 覆盖更全 |

---

## 5. 阶段 C：渲染画像

### 5.1 步骤 7：脚本渲染

```bash
python src/phase1/render_profile.py archive/<ts>/04_merged.json \
  -o output/<机构>/<部门>/<姓名>/01_基础画像.md \
  --department "超快物质科学中心"
```

可选参数：
- `--stages career_stages.json` — 学术阶段配置（覆盖 5 年默认分组）
- `--stage-desc stage_desc.json` — 阶段叙事描述（{阶段名: 描述}）

**脚本生成**：
- 论文表格（每篇一行，含 DOI/arXiv 超链接）
- 按学术履历阶段分组（从 stages 或 5 年段）
- 头部运行统计（时间戳、存档路径、各源状态）
- 数据质量说明表

### 5.2 AI 润色（脚本后）

脚本不写的内容由 AI 在脚本输出基础上补充：
1. **学术履历表格**（教育+工作，含时间线）
2. **研究方向描述**（中英文关键词 + 总体概述）
3. **每阶段叙事段落**（该阶段的研究主题、与上一阶段的转型原因）—— 不是报菜名，是讲清楚在做什么、为什么
4. **合作网络分析**（博士导师、长期合作者）
5. **公开信息整理**（新闻、采访、讲座，含超链接）

**硬约束（AI 渲染必须遵守）**：
1. **全部论文逐一列出**，不允许省略或"代表性"字样
2. **每阶段表格前必须有叙事**，说明研究主题和方向变化
3. **每篇论文有外部超链接**（DOI 或 arXiv 或 GS）
4. **运行统计写在画像头部**（时间戳、来源状态、论文总数）
5. **缺失字段写 `[未找到]`**，不捏造

### 5.3 输出文件清单

```
output/<机构>/<部门>/<姓名>/
├── 01_基础画像.md               # 最终画像
├── latest.txt                    # 内容：最新 timestamp
└── archive/<timestamp>/          # 一次运行快照
    ├── 00_verified_ids.json
    ├── 01_gs.json
    ├── 02_oa.json
    ├── 03_arxiv.json
    └── 04_merged.json
```

---

## 6. 端到端 CLI 演示

```bash
TS=$(date +%Y%m%d_%H%M%S)
PROF="output/中科院物理所/超快物质科学中心/张鹏举"
mkdir -p "$PROF/archive/$TS"

# 阶段 A 由 AI 通过 MCP 工具完成（无可执行命令）

# 阶段 B
python src/phase1/step2_gs.py ls7XuGoAAAAJ \
  -o "$PROF/archive/$TS/01_gs.json"

python src/phase1/step3_openalex.py A5000914228 \
  --email your@real.com \
  -o "$PROF/archive/$TS/02_oa.json"

python src/phase1/step5_arxiv.py "Zhang_Pengju" \
  -c "physics.atom-ph physics.optics" \
  -o "$PROF/archive/$TS/03_arxiv.json"

python src/phase1/step6_merge.py \
  "$PROF/archive/$TS/01_gs.json" \
  "$PROF/archive/$TS/02_oa.json" \
  "$PROF/archive/$TS/03_arxiv.json" \
  -o "$PROF/archive/$TS/04_merged.json"

# 阶段 C
python src/phase1/render_profile.py \
  "$PROF/archive/$TS/04_merged.json" \
  -o "$PROF/01_基础画像.md" \
  --department "超快物质科学中心"
# AI 润色：补充叙事/合作/公开信息

echo "$TS" > "$PROF/latest.txt"
```

---

## 7. AI 质量门检查清单

每步脚本执行后，Claude Code 必须检查：

### 7.1 GS 质量门
- [ ] email_domain 是否 @iphy.ac.cn 之类机构域
- [ ] 论文数 > 5 篇（少于可能 profile 不全）
- [ ] h-index 存在且 > 0
- [ ] 引文数存在且 > 0

### 7.2 OA 质量门
- [ ] h-index 与 GS 差异是否 > 50%？（如 GS=15 OA=6 → 标记）
- [ ] affiliation 是否匹配官网机构？
- [ ] 论文主题是否匹配研究方向？
- [ ] ORCID 是否存在？

### 7.3 arXiv 质量门
- [ ] 是否传了 -c 学科分类参数？
- [ ] 有 DOI/标题与 GS/OA 已确认论文匹配的？
- [ ] 同名噪声率估计（>80% → 标记）

### 7.4 合并质量门
- [ ] 总论文数 > 5 篇？
- [ ] 至少 1 个源成功？
- [ ] 多源交叉验证比例（>=10% 较理想）

---

## 8. 错误处理

### 8.1 脚本级错误
脚本**不抛异常退出**。所有故障用 `status` 字段表示：

```json
{"status": "error", "error": "HTTP 403: GS blocked"}
```

### 8.2 网络层重试（utils.py @retry）

```python
@retry(max_retries=3, delay=2.0, backoff=2.0,
       retryable_exceptions=(HTTPError, URLError, OSError, TimeoutError))
def _fetch_json(url, email):
    ...
```

API 调用自动重试 3 次，延迟 2s/4s/8s 指数退避。`@retry` 默认只重试网络异常，不重试 4xx 业务错误。

### 8.3 OpenAlex 503 专项处理

OpenAlex 对匿名请求限速 ~1 req/s。如果传了 `test@example.com` 之类的假邮箱被误判走 10 req/s，会触发 503。

**修复**（step3_openalex.py 已实现）：
- 真实邮箱（有效 TLD）→ 10 req/s（polite pool）
- 假邮箱或无 email → 1 req/s（自动限速）

### 8.4 AI 级重试（编排层）

Claude Code 见到 `status: "error"` 后：
1. 网络错误（403/429/5xx）→ 等 60 秒重试
2. 格式错误（空结果/字段缺失）→ 检查参数
3. 质量门不通过 → 标记"数据可能有问题"继续

### 8.5 完全降级

三个数据源全部不可用：
- step6 输出 `{"status": "error", "papers": []}`
- AI 渲染时写明"所有数据源均不可用"
- 建议用户检查网络或提供其他 ID 链接

---

## 9. 存档策略（不是缓存）

### 9.1 核心原则

**archive/ 目录仅用于错误溯源。每次运行必须从头查询所有 API。不得从历史存档加载数据充当缓存。**

理由：
- 缓存静默覆盖新结果会导致错误难以发现
- 重跑时不读历史数据，修复代码后能验证效果

### 9.2 存档结构

```
output/<机构>/<部门>/<姓名>/
└── archive/
    ├── 20260701_153000/        # 每次运行
    ├── 20260702_091500/        # 下次运行
    └── ...
```

每次：
1. 按时间戳建新目录
2. 所有脚本输出定向到新目录
3. 更新 `latest.txt` 指向最新运行
4. 画像内的 `source_updated` 字段标注运行时间戳

### 9.3 错误溯源

画像有问题 → 找到对应时间戳目录 → 检查各中间文件 → 定位问题步骤。

例：h-index 显示不对：
- 检查 `gs.json` 的 `professor.h_index` → 如果值对，但 OA 覆盖 → 数据源问题
- 如果合并后值不对 → step6 合并优先级设计问题
- 如果 merger 都正确 → AI 渲染读错了

---

## 10. 已知问题与限制

| 问题 | 影响 | 当前对策 |
|:-----|:-----|:---------|
| OpenAlex 对中文学者覆盖 22-38% | OA 论文数少 | 以 GS 为主源，OA 仅做元数据补充 |
| OpenAlex 消歧错误 | h-index/affiliation 错位 | 标记"OA 数据错位"，画像以 GS 为准 |
| arXiv 同名噪声 | 80%+ | -c 分类过滤 + merge 通过 DOI/标题匹配过滤 |
| GS 不返回 DOI/期刊全名 | 字段缺失 | OA 补充（覆盖到的论文） |
| 跨学科学者 | 阶段分组模糊 | 5 年默认段，AI 渲染时人工调整 |
| 早期论文（无 DOI） | 超链接缺失 | arXiv 链接兜底，无则标 "—" |

---

## 11. 版本记录

| 版本 | 日期 | 变更 |
|:----|:-----|:------|
| v2.0 | 2026-07-01 | 完整重写：加错误处理章节、API 重试机制、OpenAlex 503 专项处理、代码文档契约、AI 质量门清单 |
| v1.3 | 2026-07-01 | OA 质量门加 affiliation；arXiv 加 -c 分类参数 |
| v1.2 | 2026-07-01 | 全自动流；`output/<机构>/<部门>/<姓名>/`；存档替代缓存 |
| v1.0 | 2026-07-01 | 初版（已弃用） |