#!/usr/bin/env python3
"""
step3_openalex.py — OpenAlex 数据获取。

从 OpenAlex 拉取教授 profile + 论文列表 + 元数据（DOI/期刊/引用数/作者）。
输出统一 SOURCE_OUTPUT 格式（pipeline.md §2.2）。

用法：
  python src/phase1/step3_openalex.py A5000914228 --email you@ex.com -o oa.json
  python src/phase1/step3_openalex.py A5000914228 --verbose

依赖：标准库
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import write_output, retry

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("step3_openalex")

BASE_URL = "https://api.openalex.org"
WORKS_FILTER = "filter=authorships.author.id"


@retry(max_retries=3, delay=2.0, backoff=2.0,
       retryable_exceptions=(HTTPError, URLError, OSError, TimeoutError))
def _fetch_json(url: str, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
    headers = {"Accept": "application/json"}
    if email:
        headers["User-Agent"] = f"mailto:{email}"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        if 500 <= e.code < 600:
            raise  # retry on 5xx
        logger.error(f"HTTP {e.code}: {url}")
        return None
    except (URLError, OSError, TimeoutError):
        raise  # retry on network errors
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from {url}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def _normalize_oa_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
    """OpenAlex 论文 → 统一论文格式。"""
    loc = paper.get("primary_location") or {}
    source = loc.get("source") or {}

    doi = paper.get("doi") or loc.get("doi")
    if not doi and source.get("doi"):
        doi = source["doi"]

    cited = paper.get("cited_by_count", 0)
    if isinstance(cited, dict):
        cited = cited.get("count", 0)

    return {
        "title": paper.get("title"),
        "year": (int(paper.get("publication_date", "")[:4])
                 if paper.get("publication_date") and paper["publication_date"][:4].isdigit()
                 else None),
        "authors": [
            a.get("author", {}).get("display_name")
            for a in (paper.get("authorships") or [])
        ] or None,
        "journal": source.get("display_name"),
        "doi": doi,
        "arxiv_id": None,
        "citation_count": cited,
        "source": "openalex",
        "abstract": None,
    }


def fetch(oa_id: str, email: Optional[str] = None, max_pages: int = 50) -> dict:
    """取 OA profile + 全部论文。返回统一 SOURCE_OUTPUT 格式。"""
    # 1. 取 profile
    profile = _fetch_json(f"{BASE_URL}/authors/{oa_id}", email)
    if not profile:
        return {
            "pipeline": "phase1", "source": "openalex",
            "status": "error", "error": f"Failed to fetch OA profile {oa_id}",
            "professor": None, "papers": [], "metadata": None,
        }

    # 2. 取全部论文（游标分页）
    works: List[Dict[str, Any]] = []
    cursor: Optional[str] = "*"
    page = 0
    while cursor and page < max_pages:
        page += 1
        params = f"per_page=200&sort=publication_year:desc&cursor={cursor}"
        url = f"{BASE_URL}/works?{WORKS_FILTER}:{oa_id}&{params}"
        data = _fetch_json(url, email)
        if not data:
            logger.warning(f"Works fetch stopped at page {page}")
            break
        batch = data.get("results", [])
        works.extend(batch)
        cursor = data.get("meta", {}).get("next_cursor")
        time.sleep(0.1)

    last_insts = profile.get("last_known_institutions") or []

    return {
        "pipeline": "phase1",
        "source": "openalex",
        "status": "success",
        "error": None,
        "professor": {
            "name": profile.get("display_name"),
            "affiliation": last_insts[0].get("display_name") if last_insts else None,
            "email_domain": None,
            "gs_id": None,
            "oa_id": oa_id,
            "orcid": profile.get("orcid"),
            "h_index": (profile.get("summary_stats") or {}).get("h_index"),
            "i10_index": None,
            "total_citations": profile.get("cited_by_count"),
        },
        "papers": [_normalize_oa_paper(w) for w in works],
        "metadata": {
            "works_count": profile.get("works_count"),
            "fetched_count": len(works),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenAlex 数据获取")
    parser.add_argument("oa_id", help="OpenAlex Author ID（如 A5000914228）")
    parser.add_argument("--email", help="Polite pool email")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    result = fetch(args.oa_id, args.email)
    write_output(result, args.output)

    if args.output:
        n = len(result["papers"])
        print(f"✅ [oa] {result['status']}: {n} papers → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
