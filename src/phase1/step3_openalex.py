#!/usr/bin/env python3
"""
step3_openalex.py — OpenAlex 数据获取

流水线位置：阶段 B 第二步。与 step2_gs 并行执行（互不依赖）。

数据流：
  [Phase A] 广域搜索确认 OA ID
      ↓
  [本脚本] → 02_oa.json
      ↓
  [step6_merge.py] 补充 GS 缺失的元数据（DOI/期刊/作者/引用数）

输出格式（统一 SOURCE_OUTPUT）：
  {
    "pipeline": "phase1",
    "source": "openalex",
    "status": "success | error",
    "professor": { name, affiliation, oa_id, orcid, h_index, total_citations },
    "papers": [{ title, year, authors, journal, doi, citation_count, source }, ...]
  }

特点：
  - 论文数通常少于 GS（对中文学者仅覆盖 22-38%）
  - 教授信息（h-index、affiliation）可能因消歧错误不准确
  - h-index 和引用数以 GS 为准，本脚本供对比参考
  - 加 --email 传真实邮箱可进 polite pool（10 req/s）
  - 无 email 时自动限速至 ~1 req/s 避免 503

用法：
  python src/phase1/step3_openalex.py {oa_id} --email your@email.com --prof-dir output/...

依赖：标准库（urllib）
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
from utils import write_output, retry, ProfDirResolver

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
        "institutions": [
            inst.get("display_name")
            for a in (paper.get("authorships") or [])
            for inst in (a.get("institutions") or [])
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
        # 限速：真实邮箱（标准 TLD）→ 10 req/s；其他 → 1 req/s
        # 排除保留域名 example.com / example.org / test.com 等
        domain_ok = False
        if email and "@" in email:
            domain = email.split("@")[1].lower()
            reserved = {"example.com", "example.org", "example.net", "test.com", "localhost"}
            if domain not in reserved and "." in domain and len(domain) >= 4:
                domain_ok = True
        if domain_ok:
            time.sleep(0.1)
        else:
            time.sleep(1.0)

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
    parser.add_argument("oa_id", help="OpenAlex Author ID（如 A5000000000）")
    parser.add_argument("--email", help="Polite pool email")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--archive-dir", help="archive 目录（自动设置输出路径）")
    parser.add_argument("--prof-dir", help="prof 根目录（output/.../姓名/），从 _internal/latest.txt 自动推导 archive_dir")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    if args.prof_dir and not args.archive_dir:
        args.archive_dir = ProfDirResolver(args.prof_dir).archive_dir
        if not args.archive_dir:
            parser.error(f"--prof-dir {args.prof_dir} 下找不到 _internal/latest.txt，请先跑 phase1_init.py")
    if args.archive_dir and not args.output:
        args.output = os.path.join(args.archive_dir, "02_oa.json")


    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    result = fetch(args.oa_id, args.email)
    write_output(result, args.output)

    if args.output:
        n = len(result["papers"])
        print(f"✅ [oa] {result['status']}: {n} papers → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
