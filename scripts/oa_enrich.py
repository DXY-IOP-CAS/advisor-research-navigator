#!/usr/bin/env python3
"""
oa_enrich.py — OpenAlex 标题搜索元数据补充。

输入：GS scraper 输出的 JSON（论文标题列表）。
处理：对每篇论文标题搜 OpenAlex，匹配上的补 DOI/期刊/作者/引用数。
输出：JSON 到 stdout，日志到 stderr。

用法：
  python scripts/oa_enrich.py .cache/gs.json --output .cache/oa_enriched.json
  python scripts/oa_enrich.py .cache/gs.json --delay 0.2

依赖：标准库（urllib + json）。
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_utils

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("oa_enrich")

OA_BASE = "https://api.openalex.org"


def load_gs_papers(path: str) -> List[Dict[str, Any]]:
    """从 GS scraper 输出中加载论文列表。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    papers = data.get("works", [])
    logger.info(f"Loaded {len(papers)} GS papers from {path}")
    return papers


def search_title(title: str, delay: float = 0.1, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """在 OpenAlex 中按标题搜索，返回最佳匹配的元数据。

    遇到 5xx 错误时自动重试（OA 偶尔返回 503/504）。
    """
    url = f"{OA_BASE}/works?search={quote(title)}&per_page=5"

    for attempt in range(max_retries):
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            break  # 成功则跳出重试循环
        except HTTPError as e:
            if 500 <= e.code < 600 and attempt < max_retries - 1:
                wait = (attempt + 1) * 2
                logger.warning(f"OA {e.code} for '{title[:30]}', retry {attempt+1}/{max_retries} after {wait}s")
                time.sleep(wait)
                continue
            logger.debug(f"HTTP {e.code} for title: {title[:40]}")
            return None
        except Exception as e:
            logger.debug(f"Error searching '{title[:40]}': {e}")
            return None

    results = data.get("results", [])
    if not results:
        return None

    # 选最佳匹配：归一化标题后比对
    best = None
    best_score = 0
    norm_gs = paper_utils.normalize_title(title)

    for r in results:
        oa_title = r.get("title", "")
        norm_oa = paper_utils.normalize_title(oa_title)
        # 计算最长公共子串长度比例
        if not norm_gs or not norm_oa:
            continue
        if norm_gs == norm_oa:
            best = r
            best_score = 1.0
            break
        # 子串匹配
        if norm_gs in norm_oa or norm_oa in norm_gs:
            score = min(len(norm_gs), len(norm_oa)) / max(len(norm_gs), len(norm_oa))
            if score > best_score:
                best = r
                best_score = score

    # 阈值 0.6
    if best and best_score >= 0.6:
        return _extract_oa_meta(best)

    return None


def _extract_oa_meta(paper: Dict[str, Any]) -> Dict[str, Any]:
    """从 OpenAlex 论文对象中提取需要的元数据。"""
    loc = paper.get("primary_location") or {}
    src = loc.get("source") or {}
    doi = paper.get("doi") or loc.get("doi") or ""
    cited = paper.get("cited_by_count", 0) or 0

    return {
        "source": "openalex",
        "doi": doi,
        "journal": src.get("display_name") or "",
        "cited_by_count": cited,
        "publication_date": paper.get("publication_date") or "",
        "type": paper.get("type") or "",
        "oa_title": paper.get("title") or "",
        "authors": [
            a.get("author", {}).get("display_name", "")
            for a in (paper.get("authorships") or [])
            if a.get("author")
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenAlex 标题搜索元数据补充",
        epilog="示例: python scripts/oa_enrich.py .cache/gs.json -o .cache/oa_enriched.json",
    )
    parser.add_argument("input", help="GS scraper 输出的 JSON 文件")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--delay", type=float, default=0.1, help="请求间隔（秒），OA polite pool 允许 10 req/s")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    papers = load_gs_papers(args.input)
    enriched = 0
    total = len(papers)

    for i, paper in enumerate(papers):
        title = paper.get("title", "")
        if not title:
            continue

        meta = search_title(title, args.delay)
        if meta:
            paper["doi"] = meta["doi"]
            paper["journal"] = meta["journal"]
            paper["cited_by_count_oa"] = meta["cited_by_count"]
            paper["publication_date"] = meta["publication_date"]
            paper["oa_authors"] = meta["authors"]
            enriched += 1

        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {i + 1}/{total}, matched {enriched}")
        time.sleep(args.delay)

    result = {
        "source": "openalex_enriched",
        "input": args.input,
        "total_gs_papers": total,
        "matched_in_oa": enriched,
        "match_rate": f"{enriched / total * 100:.0f}%" if total > 0 else "0%",
        "works": papers,
    }

    paper_utils.write_output(result, args.output)
    if args.output:
        print(f"✅ {enriched}/{total} titles matched → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
