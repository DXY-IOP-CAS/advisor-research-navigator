#!/usr/bin/env python3
"""
step2_gs.py — Google Scholar 数据获取（scholarly 封装）。

step1 之后的数据源。一次调用获取教授信息 + 全部论文 + 引用指标。

用法：
  python src/phase1/step2_gs.py ls7XuGoAAAAJ -o output/导师/姓名/gs.json
  python src/phase1/step2_gs.py ls7XuGoAAAAJ --verbose

输出格式见 pipeline.md §2.2（统一 SOURCE_OUTPUT 格式）。

依赖：pip install scholarly
"""

import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import write_output

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("step2_gs")


def _scholarly_to_paper(pub: dict) -> dict:
    """将 scholarly 的一条 publication 转为统一论文格式。"""
    bib = pub.get("bib", {})
    title = (bib.get("title") or "").strip()
    year_raw = bib.get("pub_year")
    year = int(year_raw) if year_raw and str(year_raw).isdigit() else None
    citation_text = (bib.get("citation") or "").strip()

    return {
        "title": title,
        "year": year,
        "authors": None,
        "journal": citation_text or None,
        "doi": None,
        "arxiv_id": None,
        "citation_count": pub.get("num_citations"),
        "source": "google_scholar",
        "abstract": None,
    }


def scrape(gs_id: str) -> dict:
    """用 scholarly 取 GS profile 数据。返回统一 SOURCE_OUTPUT 格式。"""
    from scholarly import scholarly

    author = scholarly.search_author_id(gs_id)
    if not author:
        return {
            "pipeline": "phase1", "source": "google_scholar",
            "status": "error", "error": f"No author found for GS ID {gs_id}",
            "professor": None, "papers": [], "metadata": None,
        }

    filled = scholarly.fill(author, sections=["publications", "indices"])
    pubs = filled.get("publications", [])
    papers = [_scholarly_to_paper(p) for p in pubs]

    return {
        "pipeline": "phase1",
        "source": "google_scholar",
        "status": "success",
        "error": None,
        "professor": {
            "name": filled.get("name"),
            "affiliation": filled.get("affiliation"),
            "email_domain": filled.get("email_domain"),
            "gs_id": gs_id,
            "oa_id": None,
            "orcid": None,
            "h_index": filled.get("hindex"),
            "i10_index": filled.get("i10index"),
            "total_citations": filled.get("citedby"),
        },
        "papers": papers,
        "metadata": {"publication_count": len(pubs)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="GS 数据获取（scholarly 封装）")
    parser.add_argument("gs_id", help="Google Scholar profile ID")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    result = scrape(args.gs_id)
    write_output(result, args.output)

    if args.output:
        n = len(result["papers"])
        status = result["status"]
        print(f"✅ [gs] {status}: {n} papers → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
