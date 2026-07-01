# phase1 Pipeline — 完整技术文档

**版本**：v5.0（单文件完整版）

---

## 1 三阶段流程总览

```
用户输入（姓名 + 机构 + 官网 URL）
    │
阶段 A（AI 主导）
  读官网 + MCP 广域搜索 → 找 Google Scholar / ORCID 链接
  邮箱匹配官网域名 → 身份确认 → verified_ids.json
    │
阶段 B（脚本执行）
  step2_gs:   scholarly 取 Google Scholar 论文
  step3_openalex: OpenAlex API 论文 + 元数据
  step5_arxiv:  arXiv 预印本
  step6_merge:  三源合并去重
    │
阶段 C（脚本 + AI 协作）
  render_profile.py → 论文表格渲染
  AI 补充：学术履历、研究方向叙事、合作网络、公开信息
  → 01_基础画像.md
```

全自动化：用户输入姓名 + 机构 + 官网 URL 后，三阶段按序执行，产出单篇 Markdown 画像。

---

## 2 通用数据格式

所有 step 脚本是独立 CLI，输入输出是 JSON 文件。不互相 import。

### SOURCE_OUTPUT（单源产出）

每步输出的 JSON 结构一致：

```json
{
  "pipeline": "phase1",
  "source": "google_scholar | openalex | arxiv",
  "status": "success | blocked | error",
  "professor": {
    "name": "姓名",
    "affiliation": "机构",
    "email_domain": "邮箱域名",
    "h_index": 42,
    ...
  },
  "papers": [
    {
      "title": "论文标题",
      "year": 2024,
      "doi": "10.xxxx/xxxxx",
      "arxiv_id": "2401.xxxxx",
      "citation_count": 100,
      "source": "google_scholar"
    },
    ...
  ]
}
```

### MERGED_OUTPUT（合并产出）

step6_merge 的输出，在 SOURCE_OUTPUT 基础上增加：

- `sources`：每篇论文的来源标记（`["google_scholar", "openalex"]`），用于交叉验证
- `source_count`：来源数量，用于判断数据可信度

---

## 3 阶段 B — CLI 执行

### 完整运行示例

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROF="output/中科院物理所/超快物质科学中心/张鹏举"
mkdir -p "$PROF/archive/$TIMESTAMP"

# step2: Google Scholar（需要 GS ID）
python src/phase1/step2_gs.py ls7XuGoAAAAJ \
  -o "$PROF/archive/$TIMESTAMP/01_gs.json"

# step3: OpenAlex（需要 OpenAlex ID，请用真实邮箱避免限速）
python src/phase1/step3_openalex.py A5000914228 \
  --email your@real.com \
  -o "$PROF/archive/$TIMESTAMP/02_oa.json"

# step5: arXiv（用英文名搜索，加学科分类过滤）
python src/phase1/step5_arxiv.py "Zhang_Pengju" \
  -c "physics.atom-ph physics.optics" \
  -o "$PROF/archive/$TIMESTAMP/03_arxiv.json"

# step6: 三源合并去重
python src/phase1/step6_merge.py \
  "$PROF/archive/$TIMESTAMP/01_gs.json" \
  "$PROF/archive/$TIMESTAMP/02_oa.json" \
  "$PROF/archive/$TIMESTAMP/03_arxiv.json" \
  -o "$PROF/archive/$TIMESTAMP/04_merged.json"
```

### 依赖

- Python 3.10+
- `pip install scholarly`（Google Scholar 爬取依赖）

### 邮箱与限速

推荐使用真实邮箱（非 `test@example.com` 等保留域），否则 OpenAlex 被判定为低优先级、降入 1 req/s 的 polite pool。

---

## 4 阶段 C — 渲染流程

### 脚本渲染

```bash
python src/phase1/render_profile.py \
  "$PROF/archive/$TIMESTAMP/04_merged.json" \
  -o "$PROF/01_基础画像.md" \
  --department "超快物质科学中心"

echo "$TIMESTAMP" > "$PROF/latest.txt"
```

`render_profile.py` 负责：
- 生成论文表格（含 DOI / arXiv 超链接）
- 按年份分组、统计运行指标

### AI 叙事补充（脚本完成后）

`render_profile.py` 输出骨架后，AI 补充以下内容：

1. **学术履历表** — 教育背景、职位变迁
2. **研究方向描述** — 精炼概括核心研究主题
3. **每阶段叙事** — 按年份或主题说明研究演变，不报菜名，讲清楚研究问题
4. **合作网络** — 高频合作者、代表性合作
5. **公开信息** — 获奖、学术兼职、项目等

---

## 5 AI 质量门清单

每步脚本执行后按以下清单检查：

### Google Scholar 质量门

- [ ] email_domain 匹配机构域名？
- [ ] 论文数 > 5？
- [ ] h-index 存在且 > 0？

### OpenAlex 质量门

- [ ] h-index 与 GS 差异 > 50%？→ 标记"以 GS 为准"
- [ ] affiliation 匹配官网机构？
- [ ] 论文标题命中 `OA_POLLUTION_KEYWORDS`（如 `dna hydrogel`、`wind imaging` 等非物理主题）？→ 剔除

### arXiv 质量门

- [ ] 是否加了 `-c` 学科分类过滤？
- [ ] 有 DOI 或标题与 GS/OA 匹配的论文？→ 保留，其余噪声仅供参考

### 渲染门

- [ ] 全部论文逐一列出（无"以下见完整列表"、"代表性论文"、"关键论文"等省略表述）
- [ ] 每阶段表格前有叙事段落说明研究主题
- [ ] 每篇论文有外部超链接
- [ ] 不做导师评价（匹配度、推荐意见等禁止出现）
- [ ] **§9 验证来源存在**（列出官网、GS、ORCID、OpenAlex 等源链接）
- [ ] **无重复论文标题**（同一篇论文不应在表格中出现两次）

### 表格格式规范

画像中所有 markdown 表格必须遵守以下固定列数：

| 表格位置 | 列数 | 列头 |
|:---------|:----:|:-----|
| §1 身份标识 | 2 | 字段、内容 |
| §2 学术履历 | 4 | 时间、机构、职位、方向 |
| §4 论文表格 | 6 | #、年份、标题、期刊、引用、来源 |
| §8 数据质量 | 4 | 数据源、状态、论文数、说明 |

禁止 AI 自主增减列数或合并列。论文表格必须保持 6 列，不得出现"关键论文"等筛选类表格。

论文表格列对齐方式统一为：`:---`（左对齐），不混合使用居中/右对齐。

---

## 6 错误处理策略

### 脚本退出规范

所有脚本不抛异常退出。故障用 JSON 内 `status: "error"` 字段表示，调用方检查该字段判断。

### 网络层重试

`utils.py` 提供 `@retry` 装饰器，默认 3 次指数退避（2s / 4s / 8s）。适用场景：
- OpenAlex 503 错误
- 网络超时
- SSL EOF

### OpenAlex 503 专项

**原因**：`test@example.com` 等保留域名邮箱被误判进 10 req/s 的 polite pool，触发限速。
**修复**：`step3_openalex.py` 内检测 email 是否为保留域，是则自动降为 1 req/s。

### 完全降级策略

三个数据源全部不可用时，step6 输出空论文列表（`papers: []`）。AI 渲染时在画像中写明"所有数据源均不可用"。

---

## 7 输出目录结构

### 目录命名规则

统一格式：`output/<学校>/<学院或研究所>/<部门>/<姓名>/`

```
output/
├── 北京大学/
│   └── 物理学院/
│       └── 凝聚态物理与材料物理研究所/
│           └── 李新征/
└── 中国科学院大学/
    └── 中科院物理所/
        └── 超快物质科学中心/
            └── 张鹏举/
```

### 个人目录内容

```
<姓名>/
├── 01_基础画像.md            # 最终画像（render_profile + AI 叙事）
├── latest.txt                # 最新运行 timestamp
└── archive/<timestamp>/      # 一次运行的全部数据快照
    ├── 00_verified_ids.json  # 身份验证结果
    ├── 01_gs.json            # Google Scholar 原始数据
    ├── 02_oa.json            # OpenAlex 原始数据
    ├── 03_arxiv.json         # arXiv 原始数据
    ├── 04_merged.json        # 三源合并结果
    └── 01_基础画像_draft.md  # render_profile 初始渲染（AI 补充前的半成品）
```

### 自动存档机制

运行前检查目标目录是否已存在，若存在则自动迁移旧版：

```bash
python src/phase1/archive_previous.py "<学校>/<学院>/<部门>/<姓名>"
```

该命令在阶段 A 开始前执行。旧版移动到 `archive/旧版产出/<姓名>_<timestamp>/`。无需手动清理。

---

## 8 已知限制

| 问题 | 影响 | 对策 |
|:-----|:-----|:------|
| OpenAlex 对中文学者覆盖 22-38% | OA 论文数量少 | 以 Google Scholar 为主源 |
| OpenAlex 消歧错误（h-index / affiliation 错位） | OA 数据不可靠 | merge 层以 GS 覆盖 OA |
| arXiv 同名噪声 80%+ | arXiv 返回大量无关结果 | `-c` 分类过滤 + merge 层筛选 |
| Google Scholar 不返回 DOI | DOI 字段缺失 | OpenAlex 补充 |

---

## 9 核心原则

1. **存档不是缓存**：每次运行从头查询所有 API，不读历史存档。archive 目录仅用于错误溯源，不用于数据加载。违反此原则会导致旧数据静默污染新结果，发现错误也无法通过重跑验证。
2. **来源必标 URL**：画像中每项数据标注来源 URL，缺失时标注 `[未找到]`。
3. **不做导师评价**：画像只呈现事实性信息，不输出匹配度判断、推荐意见等评价性内容。
4. **每次重要改动前 commit**：确保版本可追溯。

---

## 10 设计哲学

### 三层文档结构

- **本文件（pipeline.md）**：阶段 1 的单一技术事实源，包含所有规范、命令和检查清单。
- **CLAUDE.md**：项目级配置，定义快速指令和规则优先级。
- **脚本源码**：`utils.py`、`step*`、`render_profile.py`、`archive_previous.py` 实现具体逻辑。

本文件不引用其他文档路径，自身就是完整的操作手册。

### AI 自主 > 硬编码

脚本负责可自动化部分（数据获取、合并、表格渲染），AI 负责任意性判断（研究方向叙事、合作网络分析、公开信息整合）。这种分工使得流水线不需要为每类学者写分支逻辑。
