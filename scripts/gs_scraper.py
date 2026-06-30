#!/usr/bin/env python3
"""
gs_scraper.py — Google Scholar profile 论文列表爬取。

用途：当 OpenAlex 覆盖不足时，从 GS profile 获取完整的论文列表做补充。
输出：JSON 到 stdout（标题/年份/引用数），日志到 stderr。

注意：Google Scholar 无官方 API。本脚本爬取公开 profile 页面，限频使用。
单会话建议 ≤ 50 次请求以避免触发 CAPTCHA。

用法：
  python scripts/gs_scraper.py ls7XuGoAAAAJ
  python scripts/gs_scraper.py ls7XuGoAAAAJ --output gs_papers.json
  python scripts/gs_scraper.py ls7XuGoAAAAJ --pages 3

依赖：标准库（urllib + re + json）。
"""

import argparse
import json
import logging
import re
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("gs_scraper")

GS_BASE = "https://scholar.google.com/citations"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_page(user_id: str, start: int = 0) -> Optional[str]:
    """获取 GS profile 的一页论文列表。

    Args:
        user_id: GS profile 的 user 参数值。
        start: 分页偏移量（0, 20, 40, ...）。

    Returns:
        HTML 字符串，失败返回 None。
    """
    url = f"{GS_BASE}?user={user_id}&hl=en&sortby=pubdate&cstart={start}&pagesize=20"
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            if "captcha" in html.lower() or "unusual traffic" in html.lower():
                logger.error("CAPTCHA triggered — GS blocked this request")
                return None
            return html
    except HTTPError as e:
        logger.error(f"GS HTTP {e.code}")
        return None
    except URLError as e:
        logger.error(f"GS network error: {e.reason}")
        return None
    except Exception as e:
        logger.error(f"GS fetch failed: {e}")
        return None


def parse_metrics(html: str) -> Dict[str, Any]:
    """从 GS profile top 解析引用指标（总引用、h-index、i10-index）。

    返回：
        {"citations": int, "h_index": int, "i10_index": int} 等。
        解析失败时返回空 dict。
    """
    metrics: Dict[str, Any] = {}

    # GS 指标表：<td class="gsc_rsb_std">数字</td>
    values = re.findall(r'class="gsc_rsb_std"[^>]*>(\d+)</td>', html)

    if len(values) >= 3:
        metrics["citations"] = int(values[0])
        metrics["h_index"] = int(values[2])
        metrics["i10_index"] = int(values[4]) if len(values) >= 5 else None
    else:
        # 降级：直接从文字中提取
        hm = re.search(r'h-index[^<]*(?:<[^>]*>){0,5}?(\d+)', html)
        if hm:
            metrics["h_index_direct"] = int(hm.group(1))

    return metrics


def parse_papers(html: str) -> List[Dict[str, Any]]:
    """从 GS profile 的 HTML 中解析论文列表。

    Args:
        html: GS profile 页面 HTML。

    Returns:
        论文列表，每项含 title、year、citations。
    """
    papers: List[Dict[str, Any]] = []

    # 提取论文标题
    titles = re.findall(r'class="gsc_a_at"[^>]*>([^<]+)<', html)

    # 提取引用数（格式：<td class="gsc_a_c"><a ...>123</a></td>）
    citations = re.findall(r'class="gsc_a_c">[^<]*<a[^>]*>(\d+)<', html)

    # 提取年份（格式：<td class="gsc_a_y"><span ...>2024</span></td> 或 <td ...>2024</td>）
    years = re.findall(r'class="gsc_a_y"[^>]*>(?:<[^>]+>)?(\d{4})(?:</[^>]+>)?<', html)

    logger.info(f"Found {len(titles)} titles, {len(citations)} citations, {len(years)} years")

    for i, title in enumerate(titles):
        paper: Dict[str, Any] = {
            "title": title.strip(),
            "year": years[i] if i < len(years) else "",
            "citations": int(citations[i]) if i < len(citations) else 0,
            "source": "google_scholar",
        }
        papers.append(paper)

    return papers


def scrape_profile(user_id: str,
                   max_pages: int = 5,
                   delay: float = 3.0) -> Dict[str, Any]:
    """爬取 GS profile 的全部论文 + 引用指标。

    自动分页，直到某页无结果或超过 max_pages。

    Args:
        user_id: GS profile ID。
        max_pages: 最大爬取页数。
        delay: 页间延迟（秒）。

    Returns:
        {"works": [...], "metrics": {...}}
    """
    all_papers: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}

    for page in range(max_pages):
        start = page * 20
        logger.info(f"Fetching page {page + 1} (start={start})")

        html = fetch_page(user_id, start)
        if not html:
            logger.warning(f"Failed to fetch page {page + 1}, stopping")
            break

        # 第一页还解析引用指标
        if page == 0:
            metrics = parse_metrics(html)

        papers = parse_papers(html)
        if not papers:
            logger.info(f"No more papers at page {page + 1}, done")
            break

        # 去重：检查是否与已有结果重复（GS 翻页固定，但防无限循环）
        existing_titles = {p["title"] for p in all_papers}
        new_papers = [p for p in papers if p["title"] not in existing_titles]
        all_papers.extend(new_papers)

        if len(papers) < 20:
            logger.info(f"Page {page + 1} has < 20 papers, assuming last page")
            break

        time.sleep(delay)

    logger.info(f"Total: {len(all_papers)} papers from GS profile")
    return {"works": all_papers, "metrics": metrics}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Google Scholar profile 论文列表爬取",
        epilog=(
            "示例: python scripts/gs_scraper.py ls7XuGoAAAAJ\n"
            "      python scripts/gs_scraper.py ls7XuGoAAAAJ --output gs.json"
        ),
    )
    parser.add_argument("user_id", help="Google Scholar profile 的 user ID（URL 中的 user= 参数）")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--pages", "-n", type=int, default=5, help="最大爬取页数（每页 20 篇）")
    parser.add_argument("--delay", type=float, default=3.0, help="页间延迟（秒），建议 ≥ 3 秒")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    logger.info(f"Scraping GS profile: {args.user_id}")
    result = scrape_profile(args.user_id, args.pages, args.delay)

    output = {
        "source": "google_scholar",
        "user_id": args.user_id,
        "works_count": len(result["works"]),
        "works": result["works"],
        "metrics": result["metrics"],
    }

    import paper_utils
    paper_utils.write_output(output, args.output)

    if args.output:
        print(f"✅ {output['works_count']} papers → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
