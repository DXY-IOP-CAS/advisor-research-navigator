#!/usr/bin/env python3
"""
s2_enrich.py — [可选] Semantic Scholar TLDR 批量拉取。

注意：此脚本仅在有 Semantic Scholar API key 时有效。
无 key 时逐个请求模式限速严重（100 req/5min），55 篇论文耗时约 60s。
项目默认不依赖此脚本，跳过不影响画像质量。

输入：从 OpenAlex 或 arXiv 输出的 JSON 文件中提取 DOI 列表，批量查 TLDR。
输出：JSON 到 stdout，日志到 stderr。

用法：
  # 从 openalex_works.py 的 JSON 输出中提取 DOI，批量查 TLDR
  python scripts/s2_enrich.py openalex.json --output s2.json

  # 指定多个输入文件
  python scripts/s2_enrich.py openalex.json arxiv.json --output s2.json

依赖：标准库（urllib + json）。
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
import paper_utils

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("s2_enrich")

S2_BASE = "https://api.semanticscholar.org/graph/v1"
BATCH_SIZE = 50  # S2 batch 最大 50


def read_dois_from_file(path: str) -> List[str]:
    """从 openalex_works.py 或 arxiv_preprints.py 的输出中提取 DOI 列表。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    dois: List[str] = []
    for work in data.get("works", []):
        doi = work.get("doi")
        if doi:
            dois.append(doi)
    return dois


def batch_fetch_tldr(dois: List[str],
                     api_key: Optional[str] = None,
                     delay: float = 1.0) -> Dict[str, Dict[str, Any]]:
    """批量查 Semantic Scholar 的 TLDR 摘要。

    Args:
        dois: DOI 列表。
        api_key: S2 API key（可选，提高限速）。
        delay: 批处理间隔。

    Returns:
        {doi: {title, tldr, citation_count, venue}} 映射。
    """
    results: Dict[str, Dict[str, Any]] = {}

    for i in range(0, len(dois), BATCH_SIZE):
        batch = dois[i:i + BATCH_SIZE]
        ids = [f"DOI:{d}" for d in batch]
        url = f"{S2_BASE}/paper/batch"
        payload = json.dumps({"ids": ids}).encode()

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["x-api-key"] = api_key
        if not api_key:
            # 无 key 时用 GET
            return _fetch_one_by_one(dois, delay)

        try:
            req = Request(url, data=payload, headers=headers)
            with urlopen(req, timeout=30) as resp:
                data: List[Optional[Dict]] = json.loads(resp.read().decode())
        except HTTPError as e:
            logger.error(f"S2 batch HTTP {e.code}, falling back to individual queries")
            return _fetch_one_by_one(dois, delay)
        except Exception as e:
            logger.error(f"S2 batch error: {e}, falling back")
            return _fetch_one_by_one(dois, delay)

        for paper in data:
            if paper is None or paper.get("paperId") is None:
                continue
            doi = _extract_doi(paper)
            if doi:
                results[doi] = _normalize_s2_paper(paper)

        time.sleep(delay)

    return results


def _fetch_one_by_one(dois: List[str],
                      delay: float = 1.0) -> Dict[str, Dict[str, Any]]:
    """逐个查 S2（无 API key 时的降级方案）。"""
    results: Dict[str, Dict[str, Any]] = {}

    for i, doi in enumerate(dois):
        url = f"{S2_BASE}/paper/DOI:{doi}?fields=title,tldr,citationCount,venue,year,externalIds"
        try:
            with urlopen(url, timeout=15) as resp:
                paper: Dict[str, Any] = json.loads(resp.read().decode())
                results[doi] = _normalize_s2_paper(paper)
        except HTTPError:
            pass
        except Exception as e:
            logger.debug(f"S2 query failed for {doi}: {e}")

        if i > 0 and i % 10 == 0:
            logger.info(f"S2 progress: {i}/{len(dois)}")

        time.sleep(delay)

    logger.info(f"S2 enriched {len(results)}/{len(dois)} papers")
    return results


def _extract_doi(paper: Dict[str, Any]) -> Optional[str]:
    """从 S2 paper 对象中提取 DOI。"""
    doi = paper.get("doi") or (paper.get("externalIds") or {}).get("DOI")
    return doi


def _normalize_s2_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
    """归一化 S2 论文格式。"""
    tldr_data = paper.get("tldr") or {}
    return {
        "source": "s2",
        "title": paper.get("title"),
        "doi": _extract_doi(paper),
        "tldr": tldr_data.get("text") if isinstance(tldr_data, dict) else None,
        "citation_count": paper.get("citationCount"),
        "venue": paper.get("venue"),
        "year": paper.get("year"),
        "s2_paper_id": paper.get("paperId"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Semantic Scholar TLDR 批量填充",
        epilog="示例: python scripts/s2_enrich.py openalex.json --output s2.json",
    )
    parser.add_argument("input_files", nargs="+", help="输入 JSON 文件（openalex/arxiv 输出）")
    parser.add_argument("--api-key", help="Semantic Scholar API key（可选）")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--delay", type=float, default=1.0, help="请求间隔（秒）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # 从所有输入文件收集 DOI
    all_dois: List[str] = []
    seen: set = set()
    for path in args.input_files:
        dois = read_dois_from_file(path)
        for d in dois:
            if d not in seen:
                all_dois.append(d)
                seen.add(d)

    if not all_dois:
        logger.warning("No DOIs found in input files")
        result = {"source": "s2", "works_count": 0, "works": []}
        import paper_utils
        paper_utils.write_output(result, args.output)
        return

    logger.info(f"Enriching {len(all_dois)} papers via S2")
    enriched = batch_fetch_tldr(all_dois, args.api_key, args.delay)

    works = list(enriched.values())
    result = {
        "source": "s2",
        "works_count": len(works),
        "works": works,
    }

    paper_utils.write_output(result, args.output)

    if args.output:
        print(f"✅ {len(works)}/{len(all_dois)} papers enriched → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
