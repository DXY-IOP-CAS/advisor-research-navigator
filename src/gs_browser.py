#!/usr/bin/env python3
"""
gs_browser.py — GS 数据获取兜底（Playwright stealth + 持久化 Chrome profile）。

当 curl_cffi（gs_lite.py）遭遇 CAPTCHA 且交互模式无法解决时，用真实浏览器兜底。

核心设计：
  - 持久化 Chrome user-data-dir（含 Google 登录态 + cookie）
  - 首次 headful，你过 CAPTCHA → 后续 headless+复用
  - 输出格式完全兼容 gs_lite.py / gs_scraper.py

用法：
  python src/gs_browser.py ls7XuGoAAAAJ
  python src/gs_browser.py ls7XuGoAAAAJ --output gs.json
  python src/gs_browser.py ls7XuGoAAAAJ --force-headful   # 强制显示浏览器窗口
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("gs_browser")

GS_BASE = "https://scholar.google.com/citations"
PROFILE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    ".cache", "chrome-profile",
)

try:
    from playwright.async_api import async_playwright
except ImportError:
    logger.error("playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


# ── Stealth 补丁 ──────────────────────────────────────────────────────

STEALTH_JS = """
// 1. 禁用 webdriver
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

// 2. 补全 plugins 数组（headless 默认为 0）
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});

// 3. 补全 languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
});

// 4. 模拟真实的 chrome 对象
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {},
};

// 5. 覆盖 Permissions API 避免暴露 headless
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications'
        ? Promise.resolve({state: Notification.permission})
        : originalQuery(parameters)
);
"""

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    f"--user-data-dir={PROFILE_DIR}",
    # 禁 WebRTC IP 泄露
    "--disable-webrtc",
    "--enforce-webrtc-ip-permission-check",
]


# ── 解析 ──────────────────────────────────────────────────────────────

def parse_metrics(html: str) -> Dict[str, Any]:
    """同 gs_lite.py 的 parse_metrics。"""
    import re
    metrics: Dict[str, Any] = {}
    values = re.findall(r'class="gsc_rsb_std"[^>]*>(\d+)</td>', html)
    if len(values) >= 3:
        metrics["citations"] = int(values[0])
        metrics["h_index"] = int(values[2])
        metrics["i10_index"] = int(values[4]) if len(values) >= 5 else None
    return metrics


def parse_papers(html: str) -> List[Dict[str, Any]]:
    """同 gs_lite.py 的 parse_papers。"""
    import re
    papers: List[Dict[str, Any]] = []
    titles = re.findall(r'class="gsc_a_at"[^>]*>([^<]+)<', html)
    citations = re.findall(r'class="gsc_a_c">[^<]*<a[^>]*>(\d+)<', html)
    years = re.findall(r'class="gsc_a_y"[^>]*>(?:<[^>]+>)?(\d{4})(?:</[^>]+>)?<', html)
    for i, title in enumerate(titles):
        papers.append({
            "title": title.strip(),
            "year": years[i] if i < len(years) else "",
            "citations": int(citations[i]) if i < len(citations) else 0,
            "source": "google_scholar",
        })
    return papers


def is_captcha_page(text: str) -> bool:
    """检测 GS 封锁/CAPTCHA。"""
    lower = text.lower()
    signals = ["captcha", "unusual traffic", "not a robot", "g-recaptcha"]
    return any(s in lower for s in signals)


# ── Playwright 爬取 ───────────────────────────────────────────────────

async def scrape_profile_async(
    user_id: str,
    max_pages: int = 5,
    headful: bool = False,
) -> Dict[str, Any]:
    """Playwright 爬取 GS profile。"""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=not headful,
            args=STEALTH_ARGS,
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            timezone_id="America/New_York",
        )
        await context.add_init_script(STEALTH_JS)
        page = await context.new_page()

        all_papers: List[Dict[str, Any]] = []
        metrics: Dict[str, Any] = {}
        blocked = False

        for page_num in range(max_pages):
            start = page_num * 20
            url = f"{GS_BASE}?user={user_id}&hl=en&sortby=pubdate&cstart={start}&pagesize=20"

            logger.info(f"Browser fetching page {page_num + 1} (start={start})")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # 等待论文表格渲染（或 CAPTCHA 出现）
                try:
                    await page.wait_for_selector("tr.gsc_a_tr, #captcha-form, #gs_captcha_c", timeout=15000)
                except Exception:
                    pass

                html = await page.content()

                # CAPTCHA 检测
                if is_captcha_page(html):
                    logger.warning("CAPTCHA in browser view")
                    if headful:
                        # 用户可见浏览器窗口，等手动解决
                        logger.info("Waiting up to 120s for you to solve CAPTCHA in the browser window...")
                        try:
                            await page.wait_for_selector("tr.gsc_a_tr", timeout=120000)
                            html = await page.content()
                            logger.info("CAPTCHA solved, continuing")
                        except Exception:
                            logger.error("CAPTCHA not solved in time")
                            blocked = True
                            break
                    else:
                        logger.error("CAPTCHA requires headful mode. Use --force-headful")
                        blocked = True
                        break

                # 解析
                if page_num == 0:
                    metrics = parse_metrics(html)

                papers = parse_papers(html)
                if not papers:
                    break

                existing = {p["title"] for p in all_papers}
                new_p = [p for p in papers if p["title"] not in existing]
                all_papers.extend(new_p)

                if len(papers) < 20:
                    break

                # GS 友好的页间等待
                await asyncio.sleep(12)

            except Exception as e:
                logger.error(f"Browser page {page_num + 1} failed: {e}")
                blocked = True
                break

        await browser.close()

        return {
            "works": all_papers,
            "metrics": metrics,
            "blocked": blocked,
        }


def scrape_profile(
    user_id: str,
    max_pages: int = 5,
    headful: bool = False,
) -> Dict[str, Any]:
    """同步入口。"""
    return asyncio.run(scrape_profile_async(
        user_id, max_pages=max_pages, headful=headful,
    ))


# ── CLI ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GS 数据获取（Playwright 兜底）")
    parser.add_argument("user_id", help="GS profile ID")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--pages", "-n", type=int, default=5, help="最大页数")
    parser.add_argument("--force-headful", action="store_true", help="强制显示浏览器窗口")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    result = scrape_profile(
        args.user_id,
        max_pages=args.pages,
        headful=args.force_headful,
    )

    output = {
        "source": "google_scholar",
        "method": "playwright",
        "user_id": args.user_id,
        "blocked": result.get("blocked", False),
        "works_count": len(result["works"]),
        "works": result["works"],
        "metrics": result["metrics"],
    }

    from paper_utils import write_output
    write_output(output, args.output)

    if args.output:
        print(f"✅ {output['works_count']} papers → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
