#!/usr/bin/env python3
"""
step5_arxiv.py — arXiv 预印本搜索。

按作者姓名拼音搜索 arXiv，返回统一 SOURCE_OUTPUT 格式。
注意同名噪声：搜索按姓名匹配，非目标作者的论文由 step6_merge
通过 DOI/标题匹配过滤（目标是 GS/OA 已验证的论文）。

用法：
  python src/phase1/step5_arxiv.py "Zhang_Pengju" -o arxiv.json
  python src/phase1/step5_arxiv.py "Zhang_Pengju" -c "physics" --verbose

依赖：标准库
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
from urllib.parse import quote
from urllib.request import urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import write_output

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("step5_arxiv")

ARIXV_SEARCH_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def _strip_version(arxiv_id: str) -> str:
    return re.sub(r"v\d+$", "", arxiv_id.strip())


def _extract_arxiv_id_from_url(url: str) -> str:
    m = re.search(r"(?:arxiv\.org/abs/|arxiv\.org/pdf/)([\w.]+)", url)
    return _strip_version(m.group(1)) if m else url


def _parse_entry(entry: Any) -> Optional[Dict[str, Any]]:
    try:
        title_el = entry.find("atom:title", NS)
        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""

        pub_el = entry.find("atom:published", NS)
        pub_date = pub_el.text[:10] if pub_el is not None else ""

        id_el = entry.find("atom:id", NS)
        raw_id = id_el.text.strip() if id_el is not None else ""
        arxiv_id = _extract_arxiv_id_from_url(raw_id)

        doi = None
        for link in entry.findall("atom:link", NS):
            href = link.get("href", "")
            if "doi.org" in href:
                doi = href

        summary_el = entry.find("atom:summary", NS)
        summary = (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else ""
        summary = summary[:200] + "..." if len(summary) > 200 else summary

        authors = []
        for author_el in entry.findall("atom:author", NS):
            name_el = author_el.find("atom:name", NS)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        return {
            "title": title,
            "year": int(pub_date[:4]) if pub_date and pub_date[:4].isdigit() else None,
            "authors": authors or None,
            "journal": "arXiv",
            "doi": doi,
            "arxiv_id": arxiv_id,
            "citation_count": None,
            "source": "arxiv",
            "abstract": summary or None,
        }
    except Exception as e:
        logger.warning(f"Parse arXiv entry failed: {e}")
        return None


def search(author_name: str, max_results: int = 50,
           delay: float = 3.0, categories: Optional[str] = None) -> dict:
    """按作者名搜索 arXiv。返回统一 SOURCE_OUTPUT 格式。"""
    search_parts = [f"au:{quote(author_name, safe='')}"]
    if categories:
        for cat in categories.split():
            search_parts.append(f"cat:{cat}")
    search_query = "+AND+".join(search_parts)
    url = (
        f"{ARIXV_SEARCH_URL}?search_query={search_query}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )

    try:
        time.sleep(delay)
        with urlopen(url, timeout=30) as resp:
            xml_text = resp.read().decode()
    except HTTPError as e:
        logger.error(f"arXiv HTTP {e.code}")
        return _empty_result(author_name, f"HTTP {e.code}")
    except URLError as e:
        logger.error(f"arXiv network: {e.reason}")
        return _empty_result(author_name, f"Network: {e.reason}")
    except Exception as e:
        logger.error(f"arXiv error: {e}")
        return _empty_result(author_name, str(e))

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return _empty_result(author_name, f"XML parse: {e}")

    papers = []
    for entry in root.findall("atom:entry", NS):
        p = _parse_entry(entry)
        if p:
            papers.append(p)

    status = "success" if papers else "empty"
    return {
        "pipeline": "phase1",
        "source": "arxiv",
        "status": status,
        "error": None,
        "professor": None,
        "papers": papers,
        "metadata": {"query": author_name, "max_results": max_results},
    }


def _empty_result(author_name: str, reason: str) -> dict:
    return {
        "pipeline": "phase1",
        "source": "arxiv",
        "status": "error",
        "error": reason,
        "professor": None,
        "papers": [],
        "metadata": {"query": author_name},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="arXiv 预印本搜索")
    parser.add_argument("author_name", help="作者姓名拼音（下划线分隔，如 Zhang_Pengju）")
    parser.add_argument("--max-results", "-n", type=int, default=50)
    parser.add_argument("--categories", "-c", help="arXiv 分类过滤，如 'physics'")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    result = search(args.author_name, args.max_results, categories=args.categories)
    write_output(result, args.output)

    if args.output:
        n = len(result["papers"])
        print(f"✅ [arxiv] {result['status']}: {n} papers → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
