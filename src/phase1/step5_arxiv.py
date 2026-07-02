#!/usr/bin/env python3
"""
step5_arxiv.py — arXiv 预印本搜索

流水线位置：阶段 B 第三步。与 step2/step3 并行执行。

数据流：
  [Phase A] 广域搜索确认姓名拼音 + ORCID；step1 输出 arXiv 分类
      ↓
  [本脚本] → 03_arxiv.json
      ↓
  [step6_merge.py] 与 GS/OA 合并去重
      ↓
  [render_profile.py] arXiv-only 无 DOI → 过滤

输出格式（统一 SOURCE_OUTPUT）：
  {
    "pipeline": "phase1",
    "source": "arxiv",
    "status": "success | empty | error",
    "papers": [{ title, year, authors, journal, doi, arxiv_id, abstract }, ...]
  }

查询策略：
  - 输入格式：`姓_名`（下划线分隔，如 Zhang_Pengju）
  - 自动拆为 `au:Zhang+AND+au:Pengju`，AND 组合搜索作者字段中同时出现姓和名的论文
  - 加 -c 参数传 arXiv 学科分类降低噪声，多个分类分别查询（cat: 用 AND 语义）
  - 噪声过滤：render_profile.py 对 arXiv-only 无 DOI 论文直接过滤

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
                  delay: float, attempt: int = 0) -> Optional[str]:
    """向 arXiv API 发一次查询，返回 XML 文本。

    对 429/503 响应自动重试（指数退避，最多 3 次）。
    """
    url = (
        f"{ARIXV_SEARCH_URL}?search_query={search_query}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )
    try:
        time.sleep(delay)
        with urlopen(url, timeout=30) as resp:
            return resp.read().decode()
    except HTTPError as e:
        if e.code in (429, 503) and attempt < 3:
            wait = 10 * (2 ** attempt)
            logger.warning(f"arXiv HTTP {e.code}, retrying in {wait}s (attempt {attempt + 1}/3)")
            time.sleep(wait)
            return _query_arxiv(search_query, max_results, delay, attempt + 1)
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


def _build_arxiv_author_query(author_name: str) -> str:
    """将 `姓_名` 格式转为 arXiv 兼容的 au: 查询。

    arXiv 作者字段存的是 "Pengju Zhang"（名在前姓在后，空格分隔）。
    下划线分隔的 "Zhang_Pengju" 不能直接传入 au:，因为下划线不会被拆成空格。

    策略：拆成姓和名，用 AND 组合搜索作者字段中同时出现两者的论文。
    """
    parts = author_name.split("_")
    if len(parts) >= 2:
        last = quote(parts[0], safe="")
        first = quote("_".join(parts[1:]), safe="")
        return f"au:{last}+AND+au:{first}"
    return f"au:{quote(author_name, safe='')}"


def search(author_name: str, max_results: int = 200,
           delay: float = 3.0, categories: Optional[str] = None) -> dict:
    """按作者名搜索 arXiv。返回统一 SOURCE_OUTPUT 格式。

    多个分类时分别查询（每个分类单独发请求），结果合并去重。
    因为 arXiv API 的 cat: 过滤器用 AND 语义，
    传多个分类一起查会要求论文同时属于所有分类，几乎永远返回 0。
    """
    author_query = _build_arxiv_author_query(author_name)
    cat_list = categories.split() if categories else []

    all_papers = {}

    if cat_list:
        # 每个分类单独查
        for cat in cat_list:
            q = f"{author_query}+AND+cat:{cat}"
            xml_text = _query_arxiv(q, max_results, delay)
            if xml_text:
                for p in _parse_xml(xml_text):
                    dedup_key = (p.get("title", ""), p.get("arxiv_id", ""))
                    all_papers[dedup_key] = p
    else:
        # 无分类过滤
        xml_text = _query_arxiv(author_query, max_results, delay)
        if xml_text:
            for p in _parse_xml(xml_text):
                dedup_key = (p.get("title", ""), p.get("arxiv_id", ""))
                all_papers[dedup_key] = p

    papers = list(all_papers.values())
    status = "success" if papers else "empty"

    # 0 篇时：检测是否因中文名导致 arXiv 搜不到
    if status == "empty" and any("一" <= c <= "鿿" for c in author_name):
        logger.warning(
            "arXiv 返回 0 篇。姓名含中文字符，arXiv 只支持拼音。\n"
            "  → 重试：python src/phase1/step5_arxiv.py \"Li_Yutong\" "
            f"-c \"{' '.join(cat_list)}\" -o <output_path>\n"
            "  → 或传给 run.py 的 --name-pinyin 参数"
        )

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
    parser.add_argument("--max-results", "-n", type=int, default=200)
    parser.add_argument("--categories", "-c", help="arXiv 分类过滤，如 'physics'")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--archive-dir", help="archive 目录（自动设置输出路径）")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    if args.archive_dir and not args.output:
        args.output = os.path.join(args.archive_dir, "03_arxiv.json")


    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    result = search(args.author_name, args.max_results, categories=args.categories)
    write_output(result, args.output)

    if args.output:
        n = len(result["papers"])
        print(f"✅ [arxiv] {result['status']}: {n} papers → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
