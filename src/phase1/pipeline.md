# phase1 Pipeline — 完整技术文档

**版本**：v6.0（对齐 Harness 哲学 + 阶段 C 重写 + 学术阶段 enriched 格式）

---

## 1 三阶段流程总览

### 开始前准备

每次运行前必须先存档旧版产出（如果有的话）：

```bash
python src/phase1/archive_previous.py "<学校>/<学院>/<部门>/<姓名>"
```

如果没有同名老师（首次运行），此命令自动跳过。

### 三阶段流

```
用户输入（姓名 + 机构 + 官网 URL）
    │
阶段 A（AI 主导）—— 身份锁定 + 阶段配置
  Step 1: 官网抓取 → 提取 name, email, institution，履历
  Step 2: MCP 搜 GS/ORCID → 跨源身份锁定（见下方协议）
    → verified_ids.json
  Step 3: 官网履历 → career_stages.json（含 institution/position/direction）
  Step 4: step1_discipline → arXiv 学科分类
    │
阶段 B（脚本执行）—— 数据采集
  run.py（推荐）或手动：
    step2_gs:       scholarly 取 Google Scholar 论文
    step3_openalex:  OpenAlex API 论文 + 元数据
    step4_arxiv_id:  ORCID → arXiv 精确匹配（零噪声）
      └─失败→ step5_arxiv:  arXiv au: 搜索
    step6_merge:     三源合并去重 + 噪声过滤
    risk_gate:       判断 standard 是否足够，或要求 conservative 补搜
    │
阶段 C（脚本渲染 + AI 叙事 + verify 循环）
  render_profile.py → 骨架（§1/§2/§4/§8 自动，§3/§5/§6/§7/§9 占位）
  AI Edit → 填充叙事段落
  verify_profile.py → 9 项检查，未通过则回 AI Edit 再验
  ⇒ 通过后：01_基础画像.md
```

### 身份锁定协议（Phase A 核心）

身份锁定的目标：**确保找到的 GS profile 属于目标学者，不是同名其他人**。

锁定流程按信任等级降序执行：

```
Tier 1: 机构邮箱验证
  → 找到 GS profile → 检查 email_domain 是否匹配官网域名
  → 例：官网邮箱 @iphy.ac.cn → GS 显示 "Verified email at iphy.ac.cn" → 锁定
  → 信任度：最高（金标准）
  → GS profile 锁定后，该 profile 内所有论文视为已验证，跳过同名过滤

Tier 2: ORCID 匹配
  → 如果官网或 OpenAlex 提供 ORCID，用 ORCID 交叉验证 GS/OA
  → ORCID 是持久唯一标识，匹配即锁定

Tier 3: 论文指纹 + 合著者网络
  → GS profile 无邮箱或邮箱不匹配 + 无 ORCID 时：
    a) 检查 GS profile 中是否有至少 3 篇论文与官网 CV 或 OA profile 匹配
       (DOI/标题/年份 三重确认)
    b) 检查合著者网络：这些论文的合著者是否与官网一致
  → 信任度：中高

Tier 4: 信息综合判断
  → 以上都失败时：
    a) 比对机构是否匹配
    b) 比对研究方向（学科分类）
    c) 比对研究时间线
  → 信任度：低
  → 画像必须标注"身份未完全验证"

降级路径：
  - GS profile 找不到 → 跳过 GS，直接走 OpenAlex + arXiv
  - OA ID 找不到 → 跳过 OA
  - 都找不到 → 标注"所有数据源均不可用"

### arXiv 身份预检（Phase A 完成前可选）

身份锁定完成后，如果能获取到 ORCID 或打开 `arxiv.org/a/` 页面：

1. 访问 `https://arxiv.org/a/{ORCID}.atom2`（ORCID 为完整 0000-0001-2345-6789 格式）
2. 如果返回 Atom Feed → 直接获取该作者的 arXiv 论文列表（精确定位，零噪声）
3. 如果 404 或空 → 回退到 step5 的 `au:` 搜索
4. 如果能从 OpenAlex 论文的 `open_access.oa_url` 字段中提取 arXiv ID，直接传递给合并层

arXiv author identifier 是 opt-in 机制，不是所有作者都有。ORCID 关联是首选方式。

### 学术阶段配置（Phase A 完成前必须）

身份锁定完成后，从官网简历/履历中提取学术生涯阶段。**每个（时间 + 机构 + 职位）变化是一个独立阶段。**

推荐格式（含 institution/position/direction，render_profile 自动据此生成 §2 履历表）：

```json
[
  {"name": "博士阶段", "start": 2007, "end": 2013,
   "institution": "中科院近代物理所", "position": "博士研究生",
   "direction": "原子分子碰撞动力学"},
  {"name": "博后阶段", "start": 2013, "end": 2018,
   "institution": "RIKEN", "position": "博士后研究员",
   "direction": "原子分子碰撞动力学"},
  {"name": "独立阶段", "start": 2018, "end": 2026,
   "institution": "ETH Zurich / 中科院物理所", "position": "特聘研究员",
   "direction": "超快光谱学 / 阿秒科学"}
]
```

兼容旧格式（仅 name/start/end）。无 institution/position/direction 时，§2 履历表留占位符给 AI 手写。

保存为 `career_stages.json`，与 `verified_ids.json` 一起存入 `archive/<timestamp>/`。
建议运行 `validate_career_stages.py` 做快速自检（可选，不阻塞流程）。

---

## 2 数据采集原理

### 信息收集（三源互补，不遗漏）

```
                        Google Scholar（主源）
                        学者维护, 最完整
                        有 GS ID 就行
                            |
arXiv  ── step4（ORCID）──→ render_profile.py ←─ OpenAlex（元数据补充）
  │   精确匹配，零噪声              │                补 DOI/期刊/作者/引用
  │   step4 失败 → step5（au:）     │
  └──────────────────┴────────────┘
          │                         |
          ├─────────────────┴─────────────────┤
          ↓                                    ↓
     step6_merge.py 合并去重           OA 独有论文：合著者+期刊+机构网络过滤
     P0:DOI → P1:arXiv ID → P2:标题    arXiv 独有论文：有 DOI 保留，无 DOI 过滤

**不漏的原理**：GS profile 由学者本人维护。学者不会遗漏自己的论文。只要 GS profile 存在且邮箱已验证，该 profile 内的论文列表即视为该学者的完整论文列表。OA 和 arXiv 只做元数据补充和时间差填补（GS 可能没收录近 1-2 个月的预印本）。

**GS 不存在时的覆盖**：降级到 OpenAlex。OpenAlex 对非英语作者的覆盖约 22-50%（因学科而异）。画像首段标注"未找到 GS profile，论文覆盖可能不完整"。

### 信息过滤（三层网络 + arXiv 预印本门控）

过滤策略跨学科通用，因为使用的元数据（合著者、期刊）是所有学科都有的。

| 层 | 过滤对象 | 方法 | 跨学科？ |
|:---|:---------|:-----|:---------|
| 合著者网络 | OA 独有论文 | 与 GS 已确认论文共享合著者 → +2 分 | ✅ 所有学科都有合著者 |
| 期刊匹配 | OA 独有论文 | 期刊名称在已确认论文的期刊列表中 → +1 分 | ✅ 所有学科都有期刊 |
| 机构匹配 | OA 独有论文 | 作者机构在已确认论文的机构列表中 → +1 分 | ✅ 所有学科都有机构 |
| 标题去重 | 三源合并 | P0:DOI → P1:arXiv ID → P2:归一化标题 | ✅ 纯文本匹配 |
| arXiv 门控 | arXiv 独有论文 | 有 DOI 保留，无 DOI 过滤（无 DOI 无法交叉验证） | ✅ 所有学科 |

OA 独有论文总分 < 1 → 疑似同名干扰，过滤。总分 ≥ 1 → 保留。
arXiv 独有论文无 DOI → 无法交叉验证，视为同名噪声过滤。

### JSON → 正文生成

```
merged.json → render_profile.py → 6 列论文表格（脚本确保完整、可点击）
                                → AI 读表格写叙事（学术履历、研究方向等）
                                → verify_profile.py 最终检查
```

脚本保障：render_profile.py 确保论文 100% 列出、每篇有超链接、表格格式一致。AI 在脚本骨架外填充叙事内容。

---

## 3 通用数据格式

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

## 4 阶段 B — CLI 执行

### 推荐：统一入口（run.py）

`run.py` 自动串联阶段 B + 阶段 C 的全部步骤。推荐大多数场景使用。

```bash
python src/phase1/run.py \
  --university "中国科学院大学" \
  --institute "中科院物理所" \
  --department "超快物质科学中心" \
  --name "王示例" \
  --gs-id XXXXXXXXAAAAJ \
  --oa-id A5048473780 \
  --email your@real.com \
  --orcid 0000-0000-0000-0000 \
  --categories "physics.atom-ph physics.optics"
```

自动完成：
1. 存档旧版产出 → 2. 建 archive/<ts>/ 目录 → 3. 校验 career_stages.json
4. GS 采集 → 5. OA 采集 → 6. arXiv（ORCID 精确匹配 / au: 回退）
7. 三源合并去重 → 8. risk gate → 9. 画像渲染 → 10. verify 检查

各参数均可选。无 GS/OA ID 时自动跳过对应步骤。

也可传结构化参数（--university + --name，替代 prof_path）让工具自动拼接路径。兼容旧用法（单 prof_path 参数）。

### 手动逐步骤执行（用 --archive-dir 简化路径）

所有 step 脚本都支持 `--archive-dir` 参数——AI 只需传递 archive 目录路径，输出的文件名和中间文件查找由脚本自动完成。

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROF="output/中科院物理所/超快物质科学中心/王示例"
mkdir -p "$PROF/archive/$TIMESTAMP"

# — 将 Phase A 产出存入 archive —
# career_stages.json 和 verified_ids.json 存在 archive/ 下，不在 prof 根目录
cp "$PROF/verified_ids.json" "$PROF/archive/$TIMESTAMP/00_verified_ids.json" 2>/dev/null || true
cp "$PROF/career_stages.json" "$PROF/archive/$TIMESTAMP/career_stages.json" 2>/dev/null || true
python src/phase1/validate_career_stages.py "$PROF/archive/$TIMESTAMP/career_stages.json"

# 每步用 --archive-dir 替代 -o，自动输出到 archive/<ts>/01_gs.json 等
python src/phase1/step2_gs.py XXXXXXXXAAAAJ --archive-dir "$PROF/archive/$TIMESTAMP"

python src/phase1/step3_openalex.py A5000000000 --email your@real.com --archive-dir "$PROF/archive/$TIMESTAMP"

# step4（ORCID 精确匹配）→ 失败回退 step5
python src/phase1/step4_arxiv_id.py "0000-0000-0000-0000" --name "Wang_Shili" --archive-dir "$PROF/archive/$TIMESTAMP" \
  || python src/phase1/step5_arxiv.py "Wang_Shili" -c "physics.atom-ph physics.optics" --archive-dir "$PROF/archive/$TIMESTAMP"

# step6 用 --archive-dir 自动读 01+02+03 文件
python src/phase1/step6_merge.py --archive-dir "$PROF/archive/$TIMESTAMP" -o "$PROF/archive/$TIMESTAMP/04_merged.json"
python src/phase1/risk_gate.py --prof-dir "$PROF"

# render 用 --archive-dir 自动找 career_stages.json（或显式传 --stages）
python src/phase1/render_profile.py \
  "$PROF/archive/$TIMESTAMP/04_merged.json" \
  -o "$PROF/01_基础画像.md" \
  --department "超快物质科学中心" \
  --archive-dir "$PROF/archive/$TIMESTAMP"

echo "$TIMESTAMP" > "$PROF/latest.txt"
```

**路径规范**：prof 根目录（`output/<大学>/<学院所>/<部门>/<姓名>/`）只放最终产出（01_基础画像.md、后续阶段产出）。中间文件（step 输出 JSON、career_stages.json、verified_ids.json）全部放在 `archive/<ts>/` 下。

**ProfDirResolver**（`utils.py`）：脚本内部用 `ProfDirResolver(prof_dir)` 自动解析所有路径——从 `latest.txt` 读取时间戳、拼接 `archive/<ts>/`、定位 каждого文件。

### 依赖

- Python 3.10+
- `pip install scholarly`（Google Scholar 爬取依赖）

### 邮箱与限速

推荐使用真实邮箱（非 `test@example.com` 等保留域），否则 OpenAlex 被判定为低优先级、降入 1 req/s 的 polite pool。

---


### standard / conservative 运行策略

默认使用 `standard`：完成身份锁定、三源采集和合并后，先运行：

```bash
python src/phase1/risk_gate.py --prof-dir "$PROF"
```

输出 `mode: standard` 时继续渲染。输出 `mode: conservative_required` 时，不要凭感觉多轮乱搜；只按 reason 做定向补搜或人工核查，然后重新运行 risk gate。策略细节见 `docs/phase1运行策略.md`。
---

## 5 阶段 C — 渲染流程

### 脚本渲染

`render_profile.py` 自动生成：
- §1 身份标识（从 merged.json professor 字段）
- §2 学术履历表（从 career_stages.json 渲染，仅 enriched 格式）
- §4 论文分组表格（按 career_stages 年份切分，6 列含超链接）
- §8 数据质量统计
- §3/§5/§6/§7/§9 占位符（AI Edit 填充）

```bash
python src/phase1/render_profile.py \
  "$PROF/archive/$TIMESTAMP/04_merged.json" \
  -o "$PROF/01_基础画像.md" \
  --department "超快物质科学中心" \
  --stages "$PROF/archive/$TIMESTAMP/career_stages.json" \
  --run-timestamp "$TIMESTAMP"
```

### AI 叙事补充（脚本完成后）

AI 只通过 Edit 替换占位符，不 Write 覆盖文件、不改论文表格行：

1. **§3 研究方向描述** — 精炼概括核心研究主题，每个专业术语首次出现时解释
2. **§4 每阶段叙事** — 1-2 句话说明该阶段的研究主题和方向变化
3. **§5 合作网络** — 高频合作者、代表性合作
4. **§6 公开信息** — 获奖、学术兼职、项目等
5. **§7 引用影响力** — 总引用、h-index、近 3 年统计
6. **§9 验证来源** — 官网、GS、ORCID、OpenAlex 等源链接 + 验证状态

### verify 门控（最终检查）

```bash
python src/phase1/verify_profile.py "$PROF/01_基础画像.md" \
  --merged "$PROF/archive/$TIMESTAMP/04_merged.json"
```

9 项检查全部通过才算完成。未通过时，AI 看具体哪项失败 + 修复指引 → 修复 → 重新渲染 → 再验。

---

## 6 AI 质量门清单

每步脚本执行后按以下清单检查：

### Google Scholar 质量门

- [ ] email_domain 匹配机构域名？
- [ ] 论文数 > 5？
- [ ] h-index 存在且 > 0？

### OpenAlex 质量门

- [ ] h-index 与 GS 差异 > 50%？→ 标记"以 GS 为准"
- [ ] affiliation 匹配官网机构？
- [ ] OA 独有论文是否通过合著者/期刊网络过滤？→ 未通过者标记"疑似同名干扰"

### arXiv 质量门

- [ ] 是否加了 `-c` 学科分类过滤？
- [ ] ORCID 已知？→ 尝试 `arxiv.org/a/{ORCID}.atom2` 精确匹配
- [ ] 搜索结果无 DOI 的 arXiv-only 论文是否正确过滤？（渲染层自动执行，核对日志）

### 渲染门

- [ ] `verify_profile.py --merged` 全部 9 项通过？
- [ ] 全部论文逐一列出（无"以下见完整列表"、"代表性论文"、"关键论文"等省略表述）
- [ ] 每阶段表格前有叙事段落说明研究主题
- [ ] 不做导师评价（匹配度、推荐意见等禁止出现）
- [ ] **无重复论文标题**（verify 会检测，0 篇才通过）

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

## 7 错误处理策略

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

## 8 输出目录结构

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
            └── 王示例/
```

### 个人目录内容

```
<姓名>/
├── 01_基础画像.md            # 最终画像（render_profile + AI 叙事）
├── career_stages.json        # 学术阶段配置（AI 在 Phase A 创建）
├── verified_ids.json         # 身份验证记录
├── latest.txt                # 最新运行 timestamp
└── archive/<timestamp>/      # 一次运行的全部数据快照
    ├── 00_verified_ids.json  # 身份验证结果
    ├── 01_gs.json            # Google Scholar 原始数据
    ├── 02_oa.json            # OpenAlex 原始数据
    ├── 03_arxiv.json         # arXiv 原始数据
    ├── 04_merged.json        # 三源合并结果
    └── career_stages.json    # 阶段配置（渲染时通过 --stages 引用）
```

### 自动存档机制

运行前检查目标目录是否已存在，若存在则自动迁移旧版：

```bash
python src/phase1/archive_previous.py "<学校>/<学院>/<部门>/<姓名>"
```

该命令在阶段 A 开始前执行。旧版移动到 `archive/旧版产出/<姓名>_<timestamp>/`。无需手动清理。

---

## 9 已知限制

| 问题 | 影响 | 对策 |
|:-----|:-----|:------|
| OpenAlex 对中文学者覆盖 22-38% | OA 论文数量少 | 以 Google Scholar 为主源 |
| OpenAlex 消歧错误（h-index / affiliation 错位） | OA 数据不可靠 | merge 层以 GS 覆盖 OA |
| arXiv 同名噪声 80%+ | arXiv 返回大量无关结果 | `-c` 分类过滤 + arXiv-only 无 DOI 过滤 |
| Google Scholar 不返回 DOI | DOI 字段缺失 | OpenAlex 补充 |
| 无 GS 锚点时 OA 污染无自动检测 | 画像可能包含同名不同人的论文 | render_profile 标注"未经网络过滤"，AI 逐篇核查标题是否属于该研究方向 |

---

## 10 核心原则

1. **存档不是缓存**：每次运行从头查询所有 API，不读历史存档。archive 目录仅用于错误溯源，不用于数据加载。违反此原则会导致旧数据静默污染新结果，发现错误也无法通过重跑验证。
2. **来源必标 URL**：画像中每项数据标注来源 URL，缺失时标注 `[未找到]`。
3. **不做导师评价**：画像只呈现事实性信息，不输出匹配度判断、推荐意见等评价性内容。
4. **每次重要改动前 commit**：确保版本可追溯。

---

## 11 设计哲学

### 三层文档结构

- **本文件（pipeline.md）**：阶段 1 的单一技术事实源，包含所有规范、命令和检查清单。
- **CLAUDE.md**：项目级配置，定义快速指令和规则优先级。
- **脚本源码**：`utils.py`、`step*`、`render_profile.py`、`archive_previous.py` 实现具体逻辑。

本文件不引用其他文档路径，自身就是完整的操作手册。

### AI 自主 > 硬编码

脚本负责可自动化部分（数据获取、合并、表格渲染），AI 负责任意性判断（研究方向叙事、合作网络分析、公开信息整合）。这种分工使得流水线不需要为每类学者写分支逻辑。
