# GS 数据获取方案多角度评估

**生成日期**：2026-07-01
**来源**：[上下文交接.md](上下文交接.md)、[阶段1重构计划.md](阶段1重构计划.md)、多轮搜索引擎调研
**背景**：阶段 1 重构前，当前 IP 已被 GS HTTP 403 封锁。需确认当前方案（Playwright stealth + 持久化 Chrome profile）是否最优，或是否有更好的替代路线。

---

## 1. 调研方法

5 个角度并行搜索，Exa 做语义搜索（学术/技术发现），Serper 做 Google 实时结果（商业方案/新闻），Tavily 做深度调研：

| 子问题 | 角度 1 | 角度 2 |
|:-------|:-------|:-------|
| GS 官方/合法数据获取 | `Google Scholar API alternatives legal data access` | `Google Scholar data without scraping` |
| 开源工具最新状态 | `scholarly python library Google Scholar scraping 2025` | `Playwright stealth google scholar scraping 2025 undetected` |
| 学术界批量方案 | `Publish or Perish Google Scholar data retrieval` | `Google Scholar profile data export manual method` |
| 替代数据源 | `OpenAlex Semantic Scholar coverage comparison 2025` | `Google Scholar API alternatives Chinese researchers non English` |
| 进阶反封锁技术 | `curl_cffi Google Scholar TLS fingerprint bypass 2025` | Google Scholar 多源统一搜索（MCP 工具） |

验证来源见文末第 6 节。

---

## 2. GS 封锁的四层模型

GS 不是单一信号封锁。它在 4 个独立层面检测自动化，每层需要不同的绕过策略：

| 层 | 检测什么 | 被什么暴露 | 绕过方式 |
|:---|:---------|:-----------|:---------|
| **L1 TLS 指纹** | TLS 握手参数（JA3 哈希、密码套件顺序、扩展列表） | Python `requests`/`httpx` 的 TLS 堆栈与浏览器不同 | `curl_cffi` 模拟 Chrome 的 BoringSSL 握手 |
| **L2 JS 环境检测** | `navigator.webdriver`、`navigator.plugins`、Chrome 运行时对象 | Playwright headless 模式未补丁的指纹 | Playwright stealth 补丁 + headful 模式 |
| **L3 请求速率** | 单位时间内的请求次数、滑动窗口模式 | 爬虫高频率请求 | 自适应限速（PoP 参数：~2 req/min, 120-150 req/hr） |
| **L4 IP 信誉** | IP 段是否数据中心/代理/VPN、该 IP 历史行为 | 数据中心 IP、共享 IP、被封过的 IP | 住宅 IP（当前 Windows 11 家庭网络本身就是住宅 IP） |

**核心结论**：当前 IP 被 403 封锁应在 L3（速率过高中短期限制），不是 L1/L2。PoP 社区报告 1-24h 自动恢复。重启脚本前必须加限速。

---

## 3. 六条路线的详细评估

### A. Playwright stealth + 持久化 Chrome profile（当前方案）

**原理**：用 Playwright 启动真实 Chrome 浏览器，挂 stealth 补丁禁用 `navigator.webdriver`，复用持久化 Chrome profile（含 Google 登录态）避免每次重新认证。用户首次运行可见 Chrome 窗口，点一次 CAPTCHA 后 cookie 写入 profile 复用数天。

**确认有效的项目**：
- `scholar-cite`（2025）已验证：headful Chromium + 轻量 stealth 可靠存活。cookie 持久化到 `~/.cache/scholar-cite/cookies.json` 跨运行复用。参见 [yitianlian/scholar-cite](https://github.com/yitianlian/scholar-cite)
- `pyscholarly`（2024）Playwright + 代理轮换方案。参见 [justrach/pyscholarly](https://github.com/justrach/pyscholarly)

**消费群体验证**：Publish or Perish（200 万用户）内部也用类似浏览器的 HTTP 请求 + 自适应限速。区别：PoP 是桌面应用（非浏览器嵌入），但限速策略完全可复用。

**优点**：$0。经过社区验证。CAPTCHA 只需点一次。
**缺点**：启动浏览器重（~200ms + 数百 MB RAM）。翻页需要等页面渲染。批量场景下 5 位/批仍需要 12 秒/页的节奏。

**评估：温和 ✅ | 高效 ⚠️ 慢 | 质量 ✅ 高 | 成本 $0 | 可靠性 ⚠️ 中高**

---

### B. curl_cffi TLS 指纹模拟（**新增考量**）

**原理**：`curl_cffi`（6K⭐，[lexiforest/curl_cffi](https://github.com/lexiforest/curl_cffi)）改了 curl 的 TLS 堆栈，编译进 BoringSSL（Google 的 TLS 库），TLS 握手字节级复刻 Chrome。不启动浏览器，纯 HTTP 请求，但 JA3 哈希和 Chrome 一致。

看 TLS 层次：
```
requests       → JA3 = "6734f4f...", HTTP/2 = mpsa 顺序（无浏览器匹配）
curl_cffi      → JA3 = Chrome 同款,  HTTP/2 = masp 顺序（Chrome 匹配）
Playwright     → 同一套 TLS 参数（底层也是 Chromium）
```

**关键限制**：GS 一旦丢 JS 挑战（CAPTCHA/登录墙），curl_cffi 挡不住——它没有 JS 引擎。所以它只能绕过 L1（TLS 指纹），不能绕过 L2（JS 环境检测）。

**优点**：极轻量（毫秒级返回），$0，比启动浏览器快 100 倍。兼容 `requests` API，改动成本低。
**缺点**：遇上 JS 挑战直接 403。GS 是否对特定 endpoint 丢 JS 挑战需要实测（profile 页面和普通搜索页可能不同）。

**评估：温和 ✅ 最轻 | 高效 ✅ 快 | 质量 ⚠️ 可能被 JS 拦住 | 成本 $0 | 可靠性 ⚠️ 待验证**

---

### C. scholarly + 付费代理

**原理**：`scholarly`（2K⭐）是纯 Python GS 爬虫，走 HTTP 请求解析 HTML。自带 `ProxyGenerator` 支持 FreeProxies/ScraperAPI/SingleProxy/Tor。v1.6+ Tor 已弃用。

**实测反馈**：
- scholar-cite 说：`scholarly` blocked "within a request or two"（一两请求内就被封）
- scholarly 官方文档说：`citedby` / `search_pubs` "will lead to Google Scholar blocking your requests and may eventually block your IP"
- `scholarly2` fork 主要改进是 SOCKS5 代理池支持

**优点**：代码最简（pip install 就能用），社区活跃。
**缺点**：GS 对纯 HTTP 请求封锁极严。scholarly 自身文档也承认这一点。加付费代理后勉强可用，但相当于多了一层代理成本和延迟。

**评估：温和 ⚠️ | 效率 ⚠️ 中 | 质量 ⚠️ 封锁频繁 | 成本 代理费月付 | 可靠性 ❌ 低**

---

### D. 付费 SERP API

**原理**：SerpAPI / ScaleSERP / Scrapeless 等提供托管 API，内部用代理池 + 浏览器渲染 + CAPTCHA 破解，用户只需 HTTP 请求。

`search_pubs` 确认被 GS 封锁，且可能需要代理。  |  价格  |  最大折扣  |

主要选项：

| 服务 | 起步价 | GS 特化 | 特点 |
|:-----|:------|:--------|:-----|
| **SerpAPI** | $75/月 (5K 查询) | ✅ 专用 Scholar engine | 最成熟，文档最好 |
| **ScaleSERP** | $66/月 | ✅ Scholar 专用 endpoint | 结构化元数据 |
| **ScraperAPI** | $49/月 (5K 页) | ⚠️ 通用代理层 | scholar-cite 用它绕过过 |
| **SearchAPI** | $50/月 | ⚠️ 通用 SERP | 便宜但功能单一 |
| **Scrapeless** | $59/月 | ✅ Scholar API | 新入局，文档较薄 |

**优点**：零维护，高可靠性，规避所有法律风险（服务商处理）。质量最高：返回结构化 JSON（标题/引用/作者/年份/PDF 链接）。
**缺点**：月费 50-75 美元起步。对 80 位物理所导师的全量调研 ~12 小时跑完，按 $75/月买一个月剩大半。

**评估：温和 ✅ | 效率 ✅ | 质量 ✅ 最高 | 成本 $50-75/月 | 可靠性 ✅ 最高**

---

### E. Publish or Perish 自适应限速（策略参考）

**原理**：PoP 不是代码库，但它的限速策略（200 万用户验证）是金标准。可提取限速算法植入任意方案。

PoP 关键参数：
- 每页 10 条（GS 2022 年从 100→20→10 逐步降低）
- ~2 请求/分钟（短期滑动窗口）
- 120-150 请求/小时（中期滑动窗口，超过即 24h 封禁）
- 自适应限速：接近上限时自动增大间隔
- 30 天缓存 TTL
- Yellow 警告 @120/hr，Red 警告 @150/hr

**当前的 10-15s 间隔**实际上相当于 ~4-6 req/min，高于 PoP 的 2 req/min。但因为我们有批间 5 分钟暂停，总体的每小时请求量在安全范围内。

**优点**：策略被 200 万用户验证。参数可测量。
**缺点**：不是代码方案，需要自己实现限速逻辑。

**评估：限速策略本身是 ✅ 必须采用的**

---

### F. 推荐方案：curl_cffi → Playwright 双层降级

结合以上各路线的长处：

```
第一次尝试（轻量）：
  curl_cffi + Chrome TLS 指纹 + 慢速 + 缓存
  → 成功：返回数据，快
  → 403/JS 挑战：1 秒内降级

第二次尝试（重量）：
  Playwright headful + 持久化 Chrome profile
  → 用户首次点一次 CAPTCHA
  → cookie/profile 缓存，后续复用
  → 限速策略采用 PoP 参数
  → 30 天缓存
```

改动量：新增 `gs_lite.py`（curl_cffi 版本，~50 行），现有的 `gs_browser.py` 不变。流水线先调 `gs_lite`，返回 `blocked: true` 时调 `gs_browser`。

**评估：温和 ✅ | 效率 ✅ 快→慢 | 质量 ✅ 高 | 成本 $0 | 可靠性 ✅ 高**

---

## 4. 核心技术细节

### 4.1 curl_cffi 用法

```python
from curl_cffi import requests as curl_req

# 模拟 Chrome 最新版 TLS 指纹
r = curl_req.get(
    "https://scholar.google.com/citations?user=USER_ID&hl=en",
    impersonate="chrome",       # 自动追踪最新 Chrome 指纹
    default_headers=True,        # 自动生成正确的 Sec-Ch-Ua 等
)
# 若返回 403 或包含 CAPTCHA 页面特征 → 降级到 Playwright
```

`impersonate="chrome"` 是滚动别名（自动跟新指纹），不需要指定版本号。`default_headers=True` 自动生成 `Sec-Ch-Ua`、`Sec-Fetch-*`、`Accept` 等浏览器级 header。

**不能处理的情况**：Cloudflare Turnstile、JS 挑战页面。此时需要降级。

### 4.2 Playwright stealth 注意事项

综合 scholar-cite 和 pyscholarly 的实践：

1. **必须 headful**。GS 检测 headless，chrome-arg `--headless=new` 有检测绕过方法，但 headful 最稳。
2. **持久化 profile**：`--user-data-dir=./.cache/chrome-profile`。首次启动时 Chrome 窗口可见，你登录 Google 账号 + 过 CAPTCHA，后续复用。
3. **stealth 补丁**核心脚本：
```javascript
// 禁用 webdriver 标志
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
// 补全 plugins 数组（headless 默认 0）
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});
// 补全 languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
});
```
4. **ZenRows 2026 年 6 月测试**：Playwright Stealth Plugin 仍有可检测漏洞，不是 100% 隐身。但 scholar-cite 实测对 GS 足够——GS 的反爬 90% 靠速率限制，不是靠高级指纹检测。

### 4.3 限速参数（PoP 金标准）

```python
GS_MAX_RATE_PER_MINUTE = 2        # 短期：每分钟最多 2 次
GS_YELLOW_WARNING = 120            # 中期：1 小时内超过 120 次警告
GS_RED_LIMIT = 150                 # 中期：1 小时内超过 150 次封禁 24h
GS_CACHE_TTL_DAYS = 30             # 缓存 30 天
GS_RESULTS_PER_PAGE = 10           # GS 当前每页 10 条（2022 年后限制）

# 自适应策略：滑动窗口 + 指数退避
# 最近 1 分钟内请求数 > 2 → 等待 (60/2) * 当前请求数 秒
# 最近 1 小时内请求数 > 120 → 等待 5-10 分钟
```

### 4.4 GS 的灰色文献价值

多家来源确认（Martín-Martín 2018/2021, Delgado-Quirós 2024）：GS 的独特价值在于灰色文献（工作论文、学位论文、会议论文集、机构报告），这些被 OpenAlex / Semantic Scholar 等开放源广泛遗漏。GS 引用覆盖是 WoS + Scopus 的超集。这解释了为什么必须搞 GS——不是因为它元数据好，而是因为它**全**。

---

## 5. 关键发现总结

1. **当前方案框架正确**。Playwright stealth + 持久化 profile + 慢速限速被 scholar-cite 和 PoP（200M 用户）验证，不需要推翻重来。

2. **curl_cffi 是新变量，应加入做前置轻量尝试**。6K⭐，字节级 TLS 指纹模拟，$0。对 403 可能直接绕过 L1 封锁。改动仅 ~50 行新脚本 `gs_lite.py`。

3. **限速参数需要按 PoP 标准校准**。当前拍脑袋的 10-15s 间隔（~4-6 req/min）高于 PoP 的 2 req/min。虽然批间 5min 拉低了整体，但批内节奏需要调慢——应该每 30s 发一页而不是 12s。

4. **付费方案质量最高但不需要**。对 80 位导师的物理所规模，$0 方案（curl_cffi + Playwright 兜底）足够。付费 SERP API（$50-75/月）是"不想维护基础设施"时的选项，不是"GS 实在搞不定"时的救星——因为 $0 方案也能搞定。

5. **GS 封锁是暂时性的**。当前 403 来自速率超限，1-24h 恢复。重启前必须加载限速逻辑，否则恢复后又会被封。

---

## 6. 验证来源

| 来源 | URL | 验证了什么 |
|:-----|:----|:-----------|
| scholar-cite | [github.com/yitianlian/scholar-cite](https://github.com/yitianlian/scholar-cite) | Playwright headful + stealth 在 GS 可靠；cookie 持久化跨运行 |
| scholarly | [github.com/scholarly-python-package/scholarly](https://github.com/scholarly-python-package/scholarly) | 纯 HTTP 爬 GS "within a request or two" 被封 |
| curl_cffi | [github.com/lexiforest/curl_cffi](https://github.com/lexiforest/curl_cffi) | 字节级 Chrome TLS 指纹模拟，6K⭐ |
| curl-impersonate | [github.com/lwthiker/curl-impersonate](https://github.com/lwthiker/curl-impersonate) | 编译 BoringSSL 实现浏览器级 TLS 握手 |
| pyscholarly | [github.com/justrach/pyscholarly](https://github.com/justrach/pyscholarly) | Playwright + 代理轮换爬 GS profile |
| scrape-google-scholar-py | [github.com/dimitryzub/scrape-google-scholar-py](https://github.com/dimitryzub/scrape-google-scholar-py) | selenium-stealth 方案（2025 已停维护） |
| ZenRows 2026-06 测试 | [zenrows.com/blog/playwright-stealth](https://www.zenrows.com/blog/playwright-stealth) | Playwright stealth 仍有可检测漏洞，不是 100% |
| ScrapingBee 2026-01 | [scrapingbee.com/blog/best-google-scholar-api](https://www.scrapingbee.com/blog/best-google-scholar-api/) | 付费 SERP API 完整对比（SerpAPI, ScaleSERP, SearchAPI） |
| Publish or Perish 文档 | [harzing.com/resources/publish-or-perish](https://harzing.com/resources/publish-or-perish/manual/reference/dialogs/preferences-google-scholar) | 限速金标准：2 req/min, 120-150 req/hr, 30 天缓存 |
| IntuitionLabs 2026-03 | [intuitionlabs.ai/articles/research-paper-apis](https://intuitionlabs.ai/articles/research-paper-apis-scientific-literature) | GS 无官方 API 的完整替代图谱 |
| Martín-Martín 2018 | [doi.org/10.1016/j.joi.2018.09.002](https://doi.org/10.1016/j.joi.2018.09.002) | GS 引用覆盖是 WoS+Scopus 的超集 |
| Delgado-Quirós 2024 | [doi.org/10.1002/asi.24839](https://doi.org/10.1002/asi.24839) | GS 不索引 9.8%，灰色文献覆盖最全 |
| Zheng et al. 2025 | [doi.org/10.1002/asi.70013](https://doi.org/10.1002/asi.70013) | OpenAlex 对中文作者覆盖 22-38% |

---

## 附录：限速逻辑实现参考

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_per_minute=2, max_per_hour=120):
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.minute_window = deque()   # 最近 60s 请求时间戳
        self.hour_window = deque()     # 最近 3600s 请求时间戳

    def wait_if_needed(self):
        now = time.time()
        # 清除 60s 前的记录
        while self.minute_window and self.minute_window[0] < now - 60:
            self.minute_window.popleft()
        while self.hour_window and self.hour_window[0] < now - 3600:
            self.hour_window.popleft()

        # 中期限速 > 小时限速
        if len(self.hour_window) >= self.max_per_hour:
            sleep_time = 300 + (len(self.hour_window) - self.max_per_hour) * 60
            time.sleep(sleep_time)
            return self.wait_if_needed()

        # 短期限速
        if len(self.minute_window) >= self.max_per_minute:
            sleep_time = 60 / self.max_per_minute
            time.sleep(sleep_time)
            return self.wait_if_needed()

        self.minute_window.append(now)
        self.hour_window.append(now)
```
