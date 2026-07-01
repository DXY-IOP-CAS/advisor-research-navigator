#!/usr/bin/env python3
"""
gs_lite.py — GS 数据获取主力（curl_cffi + PoP 限速 + 缓存）。

替代 gs_scraper.py（已废弃）。输出格式完全兼容。

核心设计：
  - curl_cffi impersonate="chrome" 绕过 TLS 指纹检测（L1）
  - PoP 自适应限速（2 req/min, 120 req/hr）（L3）
  - CAPTCHA 检测 → 弹出链接让你手动点一次 → cookie 缓存 → 继续
  - 缓存优先（30 天 TTL，断点续跑）
  - Playwright 兜底由 gs_browser.py 负责，本脚本不启动浏览器

用法：
  python src/gs_lite.py ls7XuGoAAAAJ
  python src/gs_lite.py ls7XuGoAAAAJ --output gs.json
  python src/gs_lite.py ls7XuGoAAAAJ --interactive-captcha
"""

import argparse
import json
import logging
import os
import sys
import tempfile
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional

# curl_cffi: pip install curl-cffi
from curl_cffi import requests as curl_req
from curl_cffi.requests import Response

import cache_manager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("gs_lite")

GS_BASE = "https://scholar.google.com/citations"
CACHE = cache_manager.CacheManager()


# ── PoP 限速器 ────────────────────────────────────────────────────────

class RateLimiter:
    """Publish or Perish 式自适应限速。

    PoP 金标准（200 万用户验证）：
      - 短期：≤2 req/min
      - 中期：120 req/hr → yellow warning, 150 req/hr → red → 24h block
      - 自适应：接近上限时放大间隔
    """

    MAX_PER_MINUTE = 2
    YELLOW_PER_HOUR = 120
    RED_PER_HOUR = 150

    def __init__(self):
        self.minute_window: Deque[float] = deque()
        self.hour_window: Deque[float] = deque()

    def wait_if_needed(self) -> None:
        """阻塞直到安全可发请求。"""
        now = time.time()
        self._slide_window(now)

        # 中期检查：接近小时内上限则长等待
        if len(self.hour_window) >= self.RED_PER_HOUR:
            sleep_time = 600 + (len(self.hour_window) - self.RED_PER_HOUR) * 120
            logger.warning(f"Red rate limit ({len(self.hour_window)}/hr). Sleeping {sleep_time:.0f}s")
            time.sleep(sleep_time)
            return self.wait_if_needed()

        if len(self.hour_window) >= self.YELLOW_PER_HOUR:
            sleep_time = 120 + (len(self.hour_window) - self.YELLOW_PER_HOUR) * 30
            logger.info(f"Yellow rate limit ({len(self.hour_window)}/hr). Sleeping {sleep_time:.0f}s")
            time.sleep(sleep_time)
            return self.wait_if_needed()

        # 短期检查
        if len(self.minute_window) >= self.MAX_PER_MINUTE:
            sleep_time = max(10.0, 60.0 / self.MAX_PER_MINUTE * len(self.minute_window))
            logger.info(f"Short rate limit ({len(self.minute_window)}/min). Sleeping {sleep_time:.0f}s")
            time.sleep(sleep_time)
            return self.wait_if_needed()

        self.minute_window.append(now)
        self.hour_window.append(now)

    def _slide_window(self, now: float) -> None:
        """清除窗口外的旧记录。"""
        while self.minute_window and self.minute_window[0] < now - 60:
            self.minute_window.popleft()
        while self.hour_window and self.hour_window[0] < now - 3600:
            self.hour_window.popleft()


# ── curl_cffi 会话 ────────────────────────────────────────────────────

class GSSession:
    """维护一个 curl_cffi session，带 Cookie 持久化和 CAPTCHA 交互。"""

    def __init__(self, interactive_captcha: bool = False):
        self.interactive_captcha = interactive_captcha
        self.cookie_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".cache", "gs_cookies.json",
        )
        self._session = curl_req.Session()
        self._session.impersonate = "chrome"
        self._session.default_headers = True
        self._load_cookies()

    def fetch(self, url: str, timeout: int = 30) -> Optional[str]:
        """发 GET 请求，返回 HTML 文本。检测到 CAPTCHA/403/封锁时返回 None。"""
        try:
            resp: Response = self._session.get(url, timeout=timeout)

            # 403 封锁（速率超限，IP 被封）
            if resp.status_code == 403:
                logger.error(f"GS 403 blocked (L3 rate limit). Wait 1-24h for recovery.")
                return None

            text = resp.text

            # CAPTCHA / 封锁页面检测
            blocked_reason = self._check_blocked(text)
            if blocked_reason:
                logger.warning(f"GS blocked: {blocked_reason}")
                if blocked_reason == "captcha" and self.interactive_captcha:
                    self._handle_captcha_interactive(url)
                    resp = self._session.get(url, timeout=timeout)
                    text = resp.text
                    if self._check_blocked(text):
                        logger.error("Still blocked after interactive CAPTCHA")
                        return None
                else:
                    return None

            self._save_cookies()
            return text

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    def _check_blocked(self, text: str) -> Optional[str]:
        """检测 GS 封锁类型。返回封锁原因或 None。"""
        lower = text.lower()
        signals = {
            "captcha": ["captcha", "g-recaptcha", "please show you're not a robot",
                        "sorry, we can't verify that you're not a robot"],
            "rate_limit": ["unusual traffic", "sorry...", "our systems have detected unusual traffic"],
            "cf_challenge": ["cf-challenge", "cloudflare"],
        }
        for reason, keywords in signals.items():
            if any(k in lower for k in keywords):
                return reason
        return None

    def _handle_captcha_interactive(self, original_url: str) -> None:
        """交互式 CAPTCHA bypass：显示 URL，等你手动过 CAPTCHA 后粘贴 cookies。"""
        print(
            f"\n{'='*60}\n"
            f"GS CAPTCHA 需要手动处理。\n\n"
            f"1. 在浏览器中打开：\n   {original_url}\n"
            f"2. 过 CAPTCHA（点一下就行）\n"
            f"3. 回到此终端，按 Enter（等待 30 秒让你操作）\n"
            f"{'='*60}\n",
            file=sys.stderr,
        )
        # 显示后等 3 秒让你看到
        time.sleep(3)
        try:
            input("  完成后按 Enter 继续...")
        except EOFError:
            # 非交互终端下直接等待 30 秒
            logger.info("Non-interactive terminal, waiting 30s for CAPTCHA...")
            time.sleep(30)

        # 尝试从文件中加载最新 cookies（scholar-cite 模式：用户粘贴 cURL 到文件）
        manual_cookies = os.path.join(
            os.path.dirname(self.cookie_file), "gs_cookies_manual.json",
        )
        if os.path.exists(manual_cookies):
            try:
                with open(manual_cookies, "r") as f:
                    cookies = json.load(f)
                for name, value in cookies.items():
                    self._session.cookies.set(name, value)
                logger.info("Loaded manual cookies")
            except Exception as e:
                logger.warning(f"Failed to load manual cookies: {e}")

    def _load_cookies(self) -> None:
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, "r") as f:
                    cookies = json.load(f)
                for name, value in cookies.items():
                    self._session.cookies.set(name, value)
                logger.info(f"Loaded {len(cookies)} cookies from {self.cookie_file}")
            except Exception as e:
                logger.warning(f"Cookie load failed: {e}")

    def _save_cookies(self) -> None:
        try:
            cookies = dict(self._session.cookies.items())
            os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
            with open(self.cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)
        except Exception as e:
            logger.warning(f"Cookie save failed: {e}")

    def close(self) -> None:
        self._save_cookies()
        self._session.close()


# ── HTML 解析 ─────────────────────────────────────────────────────────

def parse_metrics(html: str) -> Dict[str, Any]:
    """从 GS profile HTML 解析引用指标。

    与 gs_scraper.py 的 parse_metrics 共用解析逻辑。
    """
    import re
    metrics: Dict[str, Any] = {}
    values = re.findall(r'class="gsc_rsb_std"[^>]*>(\d+)</td>', html)
    if len(values) >= 3:
        metrics["citations"] = int(values[0])
        metrics["h_index"] = int(values[2])
        metrics["i10_index"] = int(values[4]) if len(values) >= 5 else None
    else:
        hm = re.search(r'h-index[^<]*(?:<[^>]*>){0,5}?(\d+)', html)
        if hm:
            metrics["h_index_direct"] = int(hm.group(1))
    return metrics


def parse_papers(html: str) -> List[Dict[str, Any]]:
    """从 GS profile HTML 解析论文列表。

    与 gs_scraper.py 的 parse_papers 共用解析逻辑。
    """
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


# ── 主爬取逻辑 ────────────────────────────────────────────────────────

def scrape_profile(
    user_id: str,
    max_pages: int = 5,
    interactive_captcha: bool = False,
) -> Dict[str, Any]:
    """爬取 GS profile 的全部论文 + 引用指标。

    兼容 gs_scraper.py 的输出格式：works / metrics / blocked

    Args:
        user_id: GS profile ID。
        max_pages: 最大页数（每页 20 条）。
        interactive_captcha: 遇到 CAPTCHA 时是否交互处理。

    Returns:
        {"works": [...], "metrics": {...}, "blocked": bool}
    """
    # 缓存优先
    cached = CACHE.get("gs", user_id)
    if cached:
        logger.info(f"Returning cached data for {user_id}")
        return cached

    limiter = RateLimiter()
    session = GSSession(interactive_captcha=interactive_captcha)
    all_papers: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}
    blocked = False

    try:
        for page in range(max_pages):
            start = page * 20
            url = f"{GS_BASE}?user={user_id}&hl=en&sortby=pubdate&cstart={start}&pagesize=20"

            logger.info(f"Fetching page {page + 1} (start={start})")

            # ⏱ PoP 限速
            limiter.wait_if_needed()

            html = session.fetch(url)
            if not html:
                blocked = True
                logger.warning(f"GS blocked on page {page + 1}")
                break

            # 第一页解析指标
            if page == 0:
                metrics = parse_metrics(html)

            papers = parse_papers(html)
            logger.info(f"Parsed {len(papers)} papers on page {page + 1}")

            if not papers:
                break

            # 去重
            existing = {p["title"] for p in all_papers}
            new_p = [p for p in papers if p["title"] not in existing]
            all_papers.extend(new_p)

            if len(papers) < 20:
                break

            # 页间额外等待（保险）
            time.sleep(5)

    finally:
        session.close()

    result = {
        "works": all_papers,
        "metrics": metrics,
        "blocked": blocked,
    }

    # 写入缓存（仅当成功时）
    if not blocked and all_papers:
        CACHE.set("gs", user_id, result)

    return result


# ── CLI ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GS 数据获取（curl_cffi 主力）")
    parser.add_argument("user_id", help="GS profile ID（URL 中的 user= 参数）")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--pages", "-n", type=int, default=5, help="最大页数（每页 20 篇）")
    parser.add_argument("--interactive-captcha", action="store_true",
                        help="遇到 CAPTCHA 时交互处理")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    result = scrape_profile(
        args.user_id,
        max_pages=args.pages,
        interactive_captcha=args.interactive_captcha,
    )

    output = {
        "source": "google_scholar",
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
