#!/usr/bin/env python3
"""
step4_arxiv_id.py — arXiv Author Identifier 精确获取。

替代 step5_arxiv.py 的 au: 搜索。当 Phase A 获取到 ORCID 后，
直接查 arXiv Author Identifier Feed 获取该作者在 arXiv 上的全部论文。
精确匹配、零噪声。

前提：作者已将 ORCID 关联到 arXiv 账号（opt-in 机制）。
不是所有作者都有。当此脚本返回 empty 时，回退到 step5 的 au: 搜索。

数据流：
  [Phase A] ORCID 确认 → 本脚本尝试精确匹配
       ↓                      ↓
  成功 → 03_arxiv.json   失败 → 回退到 step5 的 au: 搜索
      (精确无噪声)          (有噪声需过滤)

输出格式（统一 SOURCE_OUTPUT）：
  {
    "pipeline": "phase1",
    "source": "arxiv",
    "status": "success | empty | error",
    "papers": [{ title, year, authors, journal, doi, arxiv_id, abstract }, ...]
  }

用法：
  python src/phase1/step4_arxiv_id.py "0000-0000-0000-0000" --name "Wang_Shili" --prof-dir output/...

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
from urllib.request import urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ProfDirResolver, write_output

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("step4_arxiv_id")

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

FEED_URL = "https://arxiv.org/a/{author_id}.atom2"


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
        # arxiv:doi 元素优先
        doi_el = entry.find("arxiv:doi", NS)
        if doi_el is not None and doi_el.text:
            doi_text = doi_el.text.strip()
            if not doi_text.startswith("http"):
                doi_text = f"https://doi.org/{doi_text}"
            doi = doi_text

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


def fetch_by_orcid(orcid: str, name_hint: str = "",
                   delay: float = 3.0) -> dict:
    """通过 ORCID 取 arXiv author identifier feed。

    Parameters
    ----------
    orcid : str
        ORCID 标识符（含连字符的完整格式，如 0000-0000-0000-0000）
    name_hint : str
        可选的姓名拼音（姓_名），用于日志和占位，不影响搜索
    delay : float
        arXiv 要求的请求间隔秒数

    Returns
    -------
    dict
        SOURCE_OUTPUT 格式
    """
    # 清洗 ORCID
    clean_orcid = orcid.strip()
    if clean_orcid.startswith("https://"):
        clean_orcid = clean_orcid.split("orcid.org/")[-1].split("?")[0]
    # 确保 ORCID 格式正确（含连字符）
    if not re.match(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", clean_orcid, re.IGNORECASE):
        return {
            "pipeline": "phase1", "source": "arxiv",
            "status": "error", "error": f"Invalid ORCID format: {orcid}",
            "professor": None, "papers": [], "metadata": None,
        }

    url = FEED_URL.format(author_id=clean_orcid)
    logger.info(f"Fetching arXiv author feed: {url}")

    try:
        time.sleep(delay)
        with urlopen(url, timeout=30) as resp:
            xml_text = resp.read().decode()
    except HTTPError as e:
        if e.code == 404:
            logger.info(f"arXiv author feed not found for ORCID {clean_orcid} (not linked to arXiv)")
            return {
                "pipeline": "phase1", "source": "arxiv",
                "status": "empty", "error": None,
                "professor": None, "papers": [], "metadata": {
                    "orcid": clean_orcid,
                    "method": "author_id_feed",
                    "note": "ORCID 未关联 arXiv 账号，回退到 au: 搜索",
                },
            }
        logger.warning(f"arXiv HTTP {e.code} for author feed: {url}")
        return {
            "pipeline": "phase1", "source": "arxiv",
            "status": "error", "error": f"HTTP {e.code}",
            "professor": None, "papers": [], "metadata": None,
        }
    except URLError as e:
        logger.warning(f"arXiv network: {e.reason}")
        return {
            "pipeline": "phase1", "source": "arxiv",
            "status": "error", "error": f"Network: {e.reason}",
            "professor": None, "papers": [], "metadata": None,
        }

    # 解析 Atom Feed
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning(f"XML parse error: {e}")
        return {
            "pipeline": "phase1", "source": "arxiv",
            "status": "error", "error": f"XML parse: {e}",
            "professor": None, "papers": [], "metadata": None,
        }

    papers = []
    for entry in root.findall("atom:entry", NS):
        p = _parse_entry(entry)
        if p:
            papers.append(p)

    status = "success" if papers else "empty"
    logger.info(f"arXiv author feed: {len(papers)} papers for ORCID {clean_orcid}")
    return {
        "pipeline": "phase1",
        "source": "arxiv",
        "status": status,
        "error": None,
        "professor": {
            "name": name_hint.replace("_", " ") if name_hint else None,
            "orcid": clean_orcid,
        },
        "papers": papers,
        "metadata": {
            "orcid": clean_orcid,
            "method": "author_id_feed",
            "exact_match": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="arXiv Author Identifier Feed 精确获取")
    parser.add_argument("orcid", help="ORCID（含连字符，如 0000-0000-0000-0000）")
    parser.add_argument("--name", "-n", help="姓名拼音（姓_名），用于日志")
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
        args.output = os.path.join(args.archive_dir, "03_arxiv.json")


    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    result = fetch_by_orcid(args.orcid, args.name or "")
    write_output(result, args.output)

    if args.output:
        n = len(result["papers"])
        print(f"✅ [arxiv_id] {result['status']}: {n} papers → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
