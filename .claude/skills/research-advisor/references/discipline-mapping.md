# 学科感知数据源地图

来源：`research-advisor/assets/config.json`（自动引用）

## 工作流程

1. 抓官网页面提取研究方向关键词（如"阿秒科学"、"强场物理"、"激光-物质相互作用"）
2. 把关键词匹配到 config.json 的 disciplines 段
3. **并行启用该学科的 primary_sources**
4. 优先级顺序：先 primary_sources 锁定 ID → 再 fallback 到通用源（OpenAlex/ORCID/S2）

## 六大物理学科（v1.0）

| 学科 | 关键词举例 | 启用数据源 |
|:-----|:----------|:----------|
| **高能物理/粒子物理/核物理** | 希格斯、强子、重离子、HEP、quark | INSPIRE-HEP + arXiv + OpenAlex |
| **天体物理** | 宇宙学、暗物质、星系、cosmology | NASA ADS + arXiv + OpenAlex |
| **凝聚态物理** | 超导、拓扑、莫特绝缘体 | arXiv + OpenAlex |
| **原子分子光物理（AMO）** | 阿秒、强场、超快、激光 | arXiv + OpenAlex |
| **量子信息** | qubit、quantum、纠缠 | arXiv + OpenAlex |
| **通用物理** | physics | OpenAlex + arXiv + S2 |

## 通用 fallback（任何学科都启用）

- **OpenAlex** — 任何物理导师都至少有部分论文
- **arXiv Author ID** — 大部分活跃导师都有
- **ORCID** — 注册过就有，没注册就跳过
- **Semantic Scholar** — 覆盖率略低但 TLDR 有用

## 反例：什么时候不调用某些源

- **Google Scholar Profile** — 仅当 Web Search 命中 profile URL 时抓取，避免 CAPTCHA
- **INSPIRE-HEP** — 仅高能/核物理，否则浪费时间
- **NASA ADS** — 仅天体物理，需要 API token
- **DBLP** — 计算机专用，物理领域跳过

## 自动识别工作原理（AI 必读）

```
Step 1: 抓官网页面（get_homepage.py）
        ↓
        提取研究方向段落（常包含在 HTML `<p class="research">` 之类的块中）
        ↓
Step 2: 关键词匹配（discipline_classifier.py）
        ↓
        遍历 config.json 的 disciplines 段
        对每个学科算关键词命中率
        ↓
Step 3: 选命中率最高的学科（至少 1 个关键词命中）
        ↓
        若 0 命中：标 "general_physics" + 启用 OpenAlex+arXiv+S2
```

**AI 不要自己判断学科**——必须调用 `discipline_classifier.py`（基于 config.json 的关键词字典）。AI 自身的"直觉"在中文细分学科上不可靠。

## 测试实例学科归类（验证）

| 导师 | 机构 | 学科归类 | 启用数据源 |
|:-----|:-----|:---------|:-----------|
| 张鹏举 | IPHY 超快物质科学中心 | atomic_molecular_optical（阿秒/强场） | arXiv + OpenAlex + ORCID |
| 李自翔 | 量子多体/蒙特卡洛 | condensed_matter 或 quantum_information | arXiv + OpenAlex |

## 验证来源

- INSPIRE-HEP API：https://github.com/inspirehep/rest-api-doc
- NASA ADS API：https://ui.adsabs.harvard.edu/help/api/
- arXiv 学科分类：https://arxiv.org/category_taxonomy
- OpenAlex Concepts：https://docs.openalex.org/api-entities/concepts

**版本**：v1.0
**生成日期**：2026-06-30
