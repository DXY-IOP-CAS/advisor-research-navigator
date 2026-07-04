#!/usr/bin/env python3
"""
step2_gs.py — Google Scholar 数据获取（scholarly 封装）

流水线位置：阶段 B 第一步。在阶段 A 确认 GS ID 后执行。

数据流：
  [Phase A] 广域搜索确认 GS ID
      ↓
  [本脚本] → 01_gs.json
      ↓
  [step6_merge.py] 合并三个源

输出格式（统一 SOURCE_OUTPUT，详见 pipeline.md §2.2）：
  {
    "pipeline": "phase1",
    "source": "google_scholar",
    "status": "success | blocked | error",
    "professor": { name, affiliation, email_domain, gs_id, h_index, i10_index, total_citations },
    "papers": [{ title, year, citation_count, source, url }, ...]
  }

特点：
  - 一次调用返回 GS profile 的全部论文（scholarly 库自动翻页）
  - 不返回 DOI、arXiv ID、作者列表（这些由 step3/step5 补充）
  - 期刊名含卷期号混杂（如 "Phys. Rev. A 83 (5), 052707"）
  - 梯子节点质量直接影响可用性

用法：
  python src/phase1/step2_gs.py {gs_id} --prof-dir output/...

依赖：pip install scholarly
"""

import argparse
import logging
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import write_output, ProfDirResolver

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("step2_gs")


def normalize_email_domain(value: str) -> str:
    """Normalize scholarly email_domain into a bare domain.

    scholarly can return display text or malformed truncations such as
    "...@@iphy.ac.cn". Downstream renderers already prepend "...@", so this
    function must return only "iphy.ac.cn".
    """
    if not value:
        return None
    text = str(value).strip().lower()
    text = text.replace("verified email at", " ")
    if "@" in text:
        text = text.split("@")[-1]
    matches = re.findall(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", text)
    return matches[-1] if matches else text.strip(" .@")


def _scholarly_to_paper(pub: dict, gs_id: str = None) -> dict:
    """将 scholarly 的一条 publication 转为统一论文格式。"""
    bib = pub.get("bib", {})
    title = (bib.get("title") or "").strip()
    year_raw = bib.get("pub_year")
    year = int(year_raw) if year_raw and str(year_raw).isdigit() else None
    citation_text = (bib.get("citation") or "").strip()

    # GS 不分离作者列表，但 scholarly 的 bib["author"] 含 "Name1 and Name2" 字符串
    authors_raw = bib.get("author")
    authors = [a.strip() for a in authors_raw.split(" and ")] if authors_raw else None
    author_pub_id = pub.get("author_pub_id")
    url = None
    if gs_id and author_pub_id:
        url = (
            "https://scholar.google.com/citations?"
            f"view_op=view_citation&hl=en&user={gs_id}&citation_for_view={author_pub_id}"
        )

    return {
        "title": title,
        "year": year,
        "authors": authors,
        "journal": citation_text or None,
        "doi": None,
        "arxiv_id": None,
        "url": url,
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
    papers = [_scholarly_to_paper(p, gs_id) for p in pubs]

    return {
        "pipeline": "phase1",
        "source": "google_scholar",
        "status": "success",
        "error": None,
        "professor": {
            "name": filled.get("name"),
            "affiliation": filled.get("affiliation"),
            "email_domain": normalize_email_domain(filled.get("email_domain")),
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
    parser.add_argument("--archive-dir", help="archive 目录（自动设置输出路径）")
    parser.add_argument("--prof-dir", help="prof 根目录（output/.../姓名/），从 _internal/latest.txt 自动推导 archive_dir")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    # prof-dir 优先于 archive-dir；AI 不必手动拼路径
    if args.prof_dir and not args.archive_dir:
        args.archive_dir = ProfDirResolver(args.prof_dir).archive_dir
        if not args.archive_dir:
            parser.error(f"--prof-dir {args.prof_dir} 下找不到 _internal/latest.txt，请先跑 phase1_init.py")
    if args.archive_dir and not args.output:
        args.output = os.path.join(args.archive_dir, "01_gs.json")

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
