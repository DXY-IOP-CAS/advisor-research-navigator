#!/usr/bin/env python3
"""
step5_arxiv.py — arXiv 预印本搜索

流水线位置：阶段 B 第三步。与 step2/step3 并行执行。

数据流：
  [Phase A] 广域搜索确认姓名拼音；step1 输出 arXiv 分类
      ↓
  [本脚本] → 03_arxiv.json
      ↓
  [step6_merge.py] 与 GS/OA 合并去重

输出格式（统一 SOURCE_OUTPUT）：
  {
    "pipeline": "phase1",
    "source": "arxiv",
    "status": "success | empty | error",
    "papers": [{ title, year, authors, journal, doi, arxiv_id, abstract }, ...]
  }

特点：
  - au: 搜索按姓名匹配，返回结果中同名噪声率高（常见中文名可达 80%+）
  - 加 -c 参数传 arXiv 学科分类（来自 step1_discipline.py 输出）可降低噪声
  - 噪声过滤由 step6_merge.py 通过 DOI/标题匹配 GS/OA 已确认论文完成
  - arXiv 要求 ≥3 秒请求间隔

用法：
  python src/phase1/step5_arxiv.py "Zhang_Pengju" -c "physics.atom-ph" -o output/<机构>/<部门>/<姓名>/archive/<timestamp>/03_arxiv.json

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


def _query_arxiv(search_query: str, max_results: int,
                  delay: float) -> Optional[str]:
    """向 arXiv API 发一次查询，返回 XML 文本。"""
    url = (
        f"{ARIXV_SEARCH_URL}?search_query={search_query}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )
    try:
        time.sleep(delay)
        with urlopen(url, timeout=30) as resp:
            return resp.read().decode()
    except HTTPError as e:
        logger.warning(f"arXiv HTTP {e.code} for: {search_query[:60]}")
        return None
    except URLError as e:
        logger.warning(f"arXiv network: {e.reason}")
        return None
    except Exception as e:
        logger.warning(f"arXiv error: {e}")
        return None


def _parse_xml(xml_text: str) -> list:
    """解析 arXiv Atom XML，返回论文列表。"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning(f"XML parse error: {e}")
        return []
    papers = []
    for entry in root.findall("atom:entry", NS):
        p = _parse_entry(entry)
        if p:
            papers.append(p)
    return papers


def search(author_name: str, max_results: int = 50,
           delay: float = 3.0, categories: Optional[str] = None) -> dict:
    """按作者名搜索 arXiv。返回统一 SOURCE_OUTPUT 格式。

    多个分类时分别查询（每个分类单独发请求），结果合并去重。
    因为 arXiv API 的 cat: 过滤器用 AND 语义，
    传多个分类一起查会要求论文同时属于所有分类，几乎永远返回 0。
    """
    encoded_name = quote(author_name, safe='')
    cat_list = categories.split() if categories else []

    all_papers = {}

    if cat_list:
        # 每个分类单独查
        for cat in cat_list:
            q = f"au:{encoded_name}+AND+cat:{cat}"
            xml_text = _query_arxiv(q, max_results, delay)
            if xml_text:
                for p in _parse_xml(xml_text):
                    dedup_key = (p.get("title", ""), p.get("arxiv_id", ""))
                    all_papers[dedup_key] = p
    else:
        # 无分类过滤
        q = f"au:{encoded_name}"
        xml_text = _query_arxiv(q, max_results, delay)
        if xml_text:
            for p in _parse_xml(xml_text):
                dedup_key = (p.get("title", ""), p.get("arxiv_id", ""))
                all_papers[dedup_key] = p

    papers = list(all_papers.values())
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
