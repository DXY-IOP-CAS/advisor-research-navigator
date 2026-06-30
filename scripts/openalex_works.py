#!/usr/bin/env python3
"""
openalex_works.py — OpenAlex 作者作品全量拉取（含游标分页）。

输出：JSON 到 stdout，日志到 stderr。

用法：
  python scripts/openalex_works.py A123456789 --email user@ex.com
  python scripts/openalex_works.py A123456789 --email user@ex.com --output works.json

依赖：标准库（urllib + json）。
"""

import argparse
import json
import logging
import sys
import os
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# 同级模块导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_utils

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("openalex_works")

BASE_URL = "https://api.openalex.org"
# 作者作品的正确路径：GET /works?filter=authorships.author.id:{author_id}
WORKS_FILTER = "filter=authorships.author.id"


def _fetch_json(url: str, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """GET 请求并返回 JSON。失败返回 None，日志写 stderr。"""
    headers = {"Accept": "application/json"}
    if email:
        headers["User-Agent"] = f"mailto:{email}"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        logger.error(f"HTTP {e.code}: {url}")
        if e.code == 429:
            logger.warning("Rate limited. Consider passing --email for polite pool.")
        return None
    except URLError as e:
        logger.error(f"Network error: {e.reason}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON response from {url}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def fetch_author_profile(author_id: str,
                          email: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """取 OpenAlex 作者 profile（h-index、引用数等）。"""
    url = f"{BASE_URL}/authors/{author_id}"
    return _fetch_json(url, email)


def fetch_all_works(author_id: str,
                    email: Optional[str] = None,
                    max_pages: int = 50) -> List[Dict[str, Any]]:
    """拉取作者全部论文（游标分页）。

    Args:
        author_id: OpenAlex Author ID（如 A123456789）。
        email: 用于 polite pool，不传也行但限速更严。
        max_pages: 最大页数限制，防止死循环。

    Returns:
        论文列表，每项含 title/doi/publication_date 等。
        失败返回空列表。
    """
    works: List[Dict[str, Any]] = []
    cursor: Optional[str] = "*"
    page = 0

    while cursor and page < max_pages:
        page += 1
        # OpenAlex 的作品分页使用 filter=author.id 查询参数格式
        # cursor= 用于游标分页，* 表示第一页
        page += 1
        params = f"per_page=200&sort=publication_year:desc&cursor={cursor}"
        url = f"{BASE_URL}/works?{WORKS_FILTER}:{author_id}&{params}"

        data = _fetch_json(url, email)
        if not data:
            logger.warning(f"Stopping at page {page} after fetch failure")
            break

        batch = data.get("results", [])
        works.extend(batch)
        logger.info(f"Page {page}: +{len(batch)} works, total {len(works)}")

        cursor = data.get("meta", {}).get("next_cursor")
        time.sleep(0.1)  # 礼貌限速

    if page >= max_pages:
        logger.warning(f"Reached max pages ({max_pages}). Results may be incomplete.")

    return works


def _extract_doi_from_location(location: Optional[Dict]) -> Optional[str]:
    """从 primary_location 中提取 DOI。"""
    if not location:
        return None
    return location.get("doi") or (location.get("source") or {}).get("doi")


def normalize_openalex_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
    """归一化 OpenAlex 论文字段为统一格式。"""
    loc = paper.get("primary_location") or {}
    source = loc.get("source") or {}

    # 从 primary_location 里取 DOI（OpenAlex 有时 doi 字段是空的）
    doi = paper.get("doi") or loc.get("doi")
    if not doi and source.get("doi"):
        doi = source["doi"]

    cited = paper.get("cited_by_count", 0)
    if isinstance(cited, dict):
        cited = cited.get("count", 0)

    return {
        "source": "openalex",
        "id": paper.get("id"),
        "title": paper.get("title"),
        "doi": doi,
        "publication_date": paper.get("publication_date"),
        "journal": source.get("display_name"),
        "cited_by_count": cited,
        "year": (paper.get("publication_date") or "")[:4],
        "type": paper.get("type"),
        "authors": [
            {
                "name": a.get("author", {}).get("display_name"),
                "orcid": a.get("author", {}).get("orcid"),
                "position": a.get("author_position"),
            }
            for a in (paper.get("authorships") or [])
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="拉取 OpenAlex 作者全部论文",
        epilog="示例: python scripts/openalex_works.py A123456789 --email user@ex.com",
    )
    parser.add_argument("author_id", help="OpenAlex Author ID（如 A123456789）")
    parser.add_argument("--email", help="Polite pool email（提高限速）")
    parser.add_argument("--output", "-o", help="输出 JSON 文件（缺省输出到 stdout）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    logger.info(f"Fetching profile for author {args.author_id}")
    profile = fetch_author_profile(args.author_id, args.email)
    if not profile:
        logger.error("Failed to fetch author profile — aborting")
        sys.exit(1)

    logger.info(f"Fetching all works for {args.author_id}")
    raw_works = fetch_all_works(args.author_id, args.email)
    works = [normalize_openalex_paper(w) for w in raw_works]

    result = {
        "source": "openalex",
        "author_id": args.author_id,
        "profile": {
            "display_name": profile.get("display_name"),
            "orcid": profile.get("orcid"),
            "h_index": profile.get("summary_stats", {}).get("h_index"),
            "works_count": profile.get("works_count"),
            "cited_by_count": profile.get("cited_by_count"),
            "2yr_mean_citedness": profile.get("summary_stats", {}).get("2yr_mean_citedness"),
            "last_known_institutions": [
                inst.get("display_name")
                for inst in (profile.get("last_known_institutions") or [])
            ],
        },
        "works_count": len(works),
        "works": works,
    }

    paper_utils.write_output(result, args.output)

    if args.output:
        print(f"✅ {len(works)} works → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
