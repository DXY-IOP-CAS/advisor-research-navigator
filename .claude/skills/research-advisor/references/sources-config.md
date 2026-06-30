# 数据源详细配置

来源：`research-advisor/assets/config.json` 的 `sources` 段

## 调用协议总览

| 数据源 | 协议 | 是否需 key | 限速 | 是否可重试 |
|:-------|:----|:----------:|:----:|:----------:|
| OpenAlex | REST GET | 否（邮箱入 polite pool 是可选） | 10 req/s polite，100K/天 | 是 |
| Semantic Scholar | REST GET | key 可选（没 key 100 req/5min） | 100 req/5min | 是 |
| arXiv | REST GET（Atom） | 否 | 1 req/3s | 是 |
| ORCID | REST GET | 否 | 无限制 | 是 |
| INSPIRE-HEP | REST GET | 否 | 无限制（请礼貌） | 是 |
| NASA ADS | REST GET | **必填 token**（环境变量 ADS_API_TOKEN） | 5000 query/天 | 是 |
| Google Scholar | **无 API**——仅 Web Search 间接 | — | ~100 req/天后触发 CAPTCHA | 否 |
| CrossRef | REST GET | 否（polite pool 需邮箱） | 50 req/s polite | 是 |

## 各数据源特殊注意事项

### OpenAlex
- 中文名返回候选多（实测张鹏举 = 25 个同名）→ 必须后续用论文标题比对消歧
- 机构过滤：ROR ID（如中科院物理所 = `https://ror.org/05qbk4x57`）
- 邮箱入 polite pool 后可获 10 req/s 而非 1 req/s

### Semantic Scholar
- 物理领域覆盖率不如 OpenAlex，但 TLDR 是独一无二的资源
- 100 req/5min 容易撞限，调频率要谨慎

### arXiv
- **ArXiv Author ID** 格式：`https://arxiv.org/a/{lastname}_{firstinitial}_{n}`（小写 ASCII）
- 必须作者主动 claim 论文才有 ID，物理/数学/CS 领域常见
- 中文名大都是拼音 → arXiv API 用拼音搜；如果是中文搜索，返回为空或非预期

### ORCID
- 黄金锚点：expanded-search 支持按 email 查
- 中国物理学者覆盖率偏低，但有的就有非常可靠
- ID 格式：0000-0000-0000-0000（16 位带连字符的 16 位数字）

### INSPIRE-HEP
- 高能物理领域事实标准
- API 返回 JSON
- 自带 SPIRES 老语法：`a 张鹏举`（按 author 查），`ea 张鹏举`（exact author）

### NASA ADS
- 需 token，在 https://ui.adsabs.harvard.edu/user/settings/token 申请免费
- token 不写入仓库——存环境变量 `ADS_API_TOKEN`
- 仅天体物理启用，否则 token 浪费

### Google Scholar
- **无官方 API**——禁止用 requests/Puppeteer 直抓，会触发 CAPTCHA
- 唯一可用渠道：通过 Serper/Exa/Tavily 搜 `site:scholar.google.com/citations?user={xxx}` 找 profile URL，再 HTTP fetch 该页（限频）
- 角色：**仅做交叉验证**，不是主源

## 限速铁律

| 工具 | 必须遵守 |
|:-----|:--------|
| OpenAlex | polite pool 邮箱注入后，10 req/s 即可；不注只有 1 req/s |
| Semantic Scholar | 加 retry-after 处理 |
| arXiv | 严格 1 req/3s，加 sleep |
| NASA ADS | 5000 query/天，每天 bootstrap 一次统计剩余 |

## 验证来源

- OpenAlex rate limits：https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication
- Semantic Scholar API：https://api.semanticscholar.org/api-docs/
- arXiv API rate limits：https://info.arxiv.org/help/api/tou.html
- ORCID API docs：https://info.orcid.org/documentation/api-tutorials
- INSPIRE-HEP API：https://github.com/inspirehep/rest-api-doc
- ADS API：https://ui.adsabs.harvard.edu/help/api/

**版本**：v1.0
**生成日期**：2026-06-30
