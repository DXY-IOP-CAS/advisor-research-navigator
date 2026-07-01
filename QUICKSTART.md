# QUICKSTART — 导师研究方向调研工具

## 一句话

输入姓名 + 机构 + 官网 URL → 输出 4 份结构化 Markdown 文档（基础画像 → 领域脉络 → 论文定位 → 学习讲义）。目前阶段 1（基础画像）已实现，阶段 2-4 待设计。

## 新窗口启动

```
1. 读 docs/计划书.md 第 2 章（理解整体设计）
2. 读 docs/上下文交接.md（当前进度）
3. 读 .claude/skills/research-advisor/SKILL.md（路由）
4. 读 .claude/skills/research-advisor/references/00-phase.md（执行步骤）
5. 读 src/ 目录了解可用脚本
6. 向用户确认当前任务
```

## 项目结构

```
pilot-test/
├── src/               # Python 源文件（替换了旧的 scripts/）
│   ├── gs_scraper.py          # GS profile 爬取（即将被 gs_browser.py 替代）
│   ├── openalex_works.py      # OA 作者 works 拉取
│   ├── oa_enrich.py           # OA 标题搜索补充元数据
│   ├── arxiv_preprints.py     # arXiv 预印本搜索
│   ├── paper_merger.py        # 多源合并去重
│   ├── paper_utils.py         # 共享工具库
│   ├── discipline_classifier.py  # 学科分类
│   ├── s2_enrich.py           # S2 TLDR 批量填充（可选）
│   └── identity_resolver.py   # 已废弃
├── tests/             # 测试文件
│   └── test_phase1.py
├── config/            # 配置
│   └── sources.json
├── docs/              # 文档（替换了旧的 计划/）
│   ├── 计划书.md
│   ├── 上下文交接.md
│   ├── 调研_学者分析工具全景.md
│   ├── 调研_阶段1工具选型.md
│   └── 阶段1重构计划.md
├── output/            # 输出数据（替换了旧的 项目/）
│   └── 导师/
│       ├── 张鹏举/
│       └── 李自翔/
├── archive/           # 历史参考文档
│   ├── 需求草稿/
│   └── 交接文档/
├── .cache/            # 缓存目录（gitignore）
├── .claude/           # Claude 配置和 skills
├── .gitignore
├── .claudeignore
├── CLAUDE.md
└── QUICKSTART.md
```

## 阶段 1 流程（8 步）

```
Step 1: 抓官网 + 学科识别
  → src/discipline_classifier.py

Step 2: 互联网广域搜索（MCP Web Search）
  → 找百度百科/新闻/GS/ORCID/ResearchGate 链接

Step 3: GS 爬论文列表（主源）
  → src/gs_scraper.py {gs_id} --pages 3 --delay 2
  → 检查 metrics（h-index、总引用）

Step 4: OpenAlex 元数据补充
  → src/openalex_works.py {oa_id}（profile 数据）
  → src/oa_enrich.py gs.json（标题搜索补 DOI/期刊）

Step 5: 同名过滤（GS 邮箱校验通过则跳过）

Step 6: arXiv 预印本
  → src/arxiv_preprints.py {姓名}

Step 7: 合并去重
  → src/paper_merger.py gs.json oa_enriched.json arxiv.json

Step 8: 输出 9 节画像到 output/导师/<姓名>/01_基础画像.md
```

## 脚本一览

| 脚本 | 位置 | 用途 | 必选 | API Key |
|:-----|:----|:------|:----:|:--------|
| gs_scraper.py | `src/` | GS profile 论文列表 + h-index | ✅ | 无 |
| openalex_works.py | `src/` | OA 作者 works 拉取 | ✅ | 无（加 email 提限速） |
| oa_enrich.py | `src/` | OA 标题搜索补充元数据 | ✅ | 无 |
| arxiv_preprints.py | `src/` | arXiv 预印本搜索 | ✅ | 无 |
| paper_merger.py | `src/` | 多源合并去重 | ✅ | 无 |
| paper_utils.py | `src/` | 共享工具库 | ✅ | 无 |
| discipline_classifier.py | `src/` | 学科分类 | ✅ | 无 |
| s2_enrich.py | `src/` | S2 TLDR 批量填充 | ⚠️ 推荐 | `S2_API_KEY`（免费申请） |
| identity_resolver.py | `src/` | 已废弃 | ❌ | — |

## API Key 配置

| Key | 获取地址 | 用途 | 免费额度 |
|:----|:---------|:-----|:---------|
| `S2_API_KEY` | https://www.semanticscholar.org/product/api#api-key | TLDR 摘要填充，有 key 时 delay=0.2s，无 key 时 1.0s | 免费 |
| OpenAlex email | 你自己的 email | polite pool 10 req/s | 无限 |

设置方式：
```bash
# PowerShell
$env:S2_API_KEY = "your_key_here"
# Bash
export S2_API_KEY="your_key_here"
```

## 核心原则

1. **GS 是论文列表主源**，OpenAlex 只做元数据补充
2. **GS 邮箱校验是身份金标准**，匹配官网 email 即确认身份
3. **先广搜再深挖** — Step 2 广域搜索找 profile 链接，Step 3+ 深度检索
4. **同名过滤** — GS 邮箱已验证不过滤，否则多维评分
5. **全降级** — GS 不存在时用 OpenAlex 做主源（覆盖 ≤ 50%）

## 关键引用

- Zheng et al. (2025) OpenAlex 中国论文覆盖不完整: https://doi.org/10.1002/asi.70013
- Zhao & Chen (2025) OpenAlex 中文作者消歧精度不足: https://arxiv.org/html/2502.11610v2
