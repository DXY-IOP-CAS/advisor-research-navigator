#!/usr/bin/env python3
"""
arxiv_preprints.py — arXiv 预印本检索（按作者姓名拼音）。

输出：JSON 到 stdout，日志到 stderr。

用法：
  python scripts/arxiv_preprints.py "Lastname_Firstname"
  python scripts/arxiv_preprints.py "Lastname_Firstname" --output arxiv.json

依赖：标准库（urllib + xml.etree）。
"""

import argparse
import logging
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_utils

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("arxiv_preprints")

ARIXV_SEARCH_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def strip_version(arxiv_id: str) -> str:
    """去掉 arXiv ID 的版本后缀。"""
    return re.sub(r"v\d+$", "", arxiv_id.strip())


def _extract_arxiv_id_from_url(url: str) -> str:
    """从 arXiv URL 中提取 ID。"""
    m = re.search(r"(?:arxiv\.org/abs/|arxiv\.org/pdf/)([\w.]+)", url)
    return strip_version(m.group(1)) if m else url


def search_by_author(author_name: str,
                     max_results: int = 50,
                     delay: float = 3.0) -> List[Dict[str, Any]]:
    """按作者搜索 arXiv 预印本。

    Args:
        author_name: 作者姓名拼音（下划线分隔姓和名），如 "Lastname_Firstname"。
        max_results: 最大返回数（arXiv 上限 2000，但为礼貌设 50）。
        delay: 请求间隔（arXiv 要求 3 秒）。

    Returns:
        论文列表。
    """
    url = (
        f"{ARIXV_SEARCH_URL}?search_query=au:{author_name}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )

    try:
        time.sleep(delay)
        with urlopen(url, timeout=30) as resp:
            xml_text = resp.read().decode()
    except HTTPError as e:
        logger.error(f"arXiv HTTP {e.code}")
        return []
    except URLError as e:
        logger.error(f"arXiv network error: {e.reason}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return []

    papers: List[Dict[str, Any]] = []
    for entry in root.findall("atom:entry", NS):
        paper = _parse_entry(entry)
        if paper:
            papers.append(paper)

    logger.info(f"arXiv found {len(papers)} entries for au:{author_name}")
    return papers


def _parse_entry(entry: Any) -> Optional[Dict[str, Any]]:
    """解析单条 Atom entry。"""
    try:
        title_el = entry.find("atom:title", NS)
        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""

        published = entry.find("atom:published", NS)
        pub_date = published.text[:10] if published is not None else ""

        updated = entry.find("atom:updated", NS)
        update_date = updated.text[:10] if updated is not None else ""

        # 提取 arXiv ID
        id_el = entry.find("atom:id", NS)
        raw_id = id_el.text.strip() if id_el is not None else ""
        arxiv_id = _extract_arxiv_id_from_url(raw_id)
        versioned_id = raw_id.split("/")[-1] if "/" in raw_id else raw_id

        # 提取 DOI（如果有）
        doi = None
        for link in entry.findall("atom:link", NS):
            href = link.get("href", "")
            if "doi.org" in href:
                doi = href
                break

        # 提取摘要前 200 字
        summary_el = entry.find("atom:summary", NS)
        summary = (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else ""
        summary = summary[:200] + "..." if len(summary) > 200 else summary

        # 提取作者
        authors = []
        for author_el in entry.findall("atom:author", NS):
            name_el = author_el.find("atom:name", NS)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        # 提取分类
        categories = []
        for cat in entry.findall("atom:category", NS):
            term = cat.get("term")
            if term:
                categories.append(term)

        return {
            "source": "arxiv",
            "arxiv_id": arxiv_id,
            "arxiv_versioned_id": versioned_id,
            "title": title,
            "doi": doi,
            "publication_date": pub_date,
            "updated_date": update_date,
            "summary": summary,
            "authors": authors,
            "categories": categories,
            "year": pub_date[:4] if pub_date else "",
            "type": "preprint",
        }
    except Exception as e:
        logger.warning(f"Failed to parse arXiv entry: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="检索 arXiv 预印本（按作者姓名拼音）",
        epilog="示例: python scripts/arxiv_preprints.py Lastname_Firstname",
    )
    parser.add_argument("author_name", help="作者姓名拼音（如 Lastname_Firstname）")
    parser.add_argument("--max-results", "-n", type=int, default=50, help="最大返回数")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    papers = search_by_author(args.author_name, args.max_results)

    result = {
        "source": "arxiv",
        "query": args.author_name,
        "works_count": len(papers),
        "works": papers,
    }

    paper_utils.write_output(result, args.output)

    if args.output:
        print(f"✅ {len(papers)} preprints → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
