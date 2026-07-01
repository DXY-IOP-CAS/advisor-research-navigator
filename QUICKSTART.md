# QUICKSTART — 导师研究方向调研工具

## 一句话

输入姓名 + 机构 + 官网 URL → 全自动产出基础画像到 `output/<机构>/<部门>/<姓名>/`。当前阶段 1 已实现，阶段 2-4 待设计。

## 新窗口启动

```
1. 读 docs/计划书.md 第 2 章（理解整体设计）
2. 读 src/phase1/pipeline.md（技术落地细节）
3. 读 CLAUDE.md（快速了解项目状态）
4. 向用户确认当前任务
```

## 项目结构

```
pilot-test/
├── src/phase1/           # 阶段 1 活跃脚本
│   ├── pipeline.md       # 技术落地文档
│   ├── step1_discipline.py  # 学科分类
│   ├── step2_gs.py          # scholarly 封装（GS 主源）
│   ├── step3_openalex.py    # OpenAlex 元数据
│   ├── step5_arxiv.py       # arXiv 预印本
│   ├── step6_merge.py       # 多源合并去重
│   └── utils.py             # 共享工具库
├── config/
│   └── sources.json         # 数据源 + 学科字典
├── docs/                    # 规划与调研文档
├── output/<机构>/<部门>/<姓名>/   # 导师画像产出
│   ├── 01_基础画像.md
│   └── archive/<timestamp>/ # 中间产物存档
└── archive/                 # 旧版脚本 + 旧版产出存档
    └── 旧版脚本/
```

## 全自动流水线（三阶段）

```
用户输入：姓名、机构、官网 URL

阶段 A（AI 主导）：广域搜索 + 身份确认
  → MCP Fetch 读官网 → MCP 搜 GS/ORCID/RG 链接
  → 邮箱匹配官网 → 身份确认 → verified_ids.json

阶段 B（脚本 + AI 质量门）：深度数据获取
  → step2_gs.py（scholarly）→ 56 篇论文 + h-index
  → step3_openalex.py → DOI/期刊/作者
  → step5_arxiv.py → 预印本补充
  → step6_merge.py → 去重合并

阶段 C（AI 主导）：渲染输出
  → 读 merged.json → 写 01_基础画像.md
```

各步骤输出统一格式，通过 JSON 文件通信，不互相 import。

## 脚本一览

| 脚本 | 位置 | 用途 | 必选 | API Key |
|:-----|:-----|:------|:----:|:--------|
| step1_discipline | `src/phase1/` | 学科关键词分类 | ✅ | 无 |
| step2_gs | `src/phase1/` | scholarly 封装取 GS 论文 | ✅ | 无（梯子节点要稳） |
| step3_openalex | `src/phase1/` | OpenAlex 论文+元数据 | ✅ | `--email` 提限速 |
| step5_arxiv | `src/phase1/` | arXiv 预印本搜索 | ✅ | 无 |
| step6_merge | `src/phase1/` | 多源合并去重 | ✅ | 无 |
| utils | `src/phase1/` | 共享工具库 | ✅ | 无 |

## 注意事项

- 每次运行**不读历史缓存**，全部重新查询。archive 目录仅供存档溯源
- GS 访问依赖梯子节点质量。一次 403 换节点重试，不需要 Playwright 或 curl_cffi
- OpenAlex 对中文学者覆盖约 22-38%，h-index 可能不准。以 GS 为准
- arXiv 同名噪声率高，merger 通过 DOI/标题匹配自动过滤

## 核心原则

1. **GS 是论文列表主源**，OpenAlex 只做元数据补充
2. **GS 邮箱校验是身份金标准**——匹配官网 email 即确认身份，不额外验证
3. **先广搜再深挖**——阶段 A 广域搜索找 profile 链接，阶段 B 深度检索
4. **全降级**——GS 不可用时 OA 做替补（覆盖 ≤ 50%），arXiv 补充
