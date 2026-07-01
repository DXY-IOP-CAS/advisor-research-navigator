#!/usr/bin/env python3
"""
paper_merger.py — 多源论文合并与去重。

输入：多个 JSON 文件（openalex_works.py / arxiv_preprints.py / s2_enrich.py 输出）。
算法：P0:DOI → P1:arXiv ID → P2:归一化标题 ≥85%。
输出：合并去重后的 JSON 到 stdout。

用法：
  python scripts/paper_merger.py openalex.json arxiv.json s2.json --output merged.json

依赖：paper_utils.py（标准库）。
"""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_utils

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("paper_merger")


def load_works(path: str) -> List[Dict[str, Any]]:
    """从 JSON 文件中加载 works 列表。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    works = data.get("works", [])
    if not works:
        logger.warning(f"No works found in {path}")
    return works


def group_by_deduplication(works: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """按去重优先级对论文分组：同一篇论文的多个源归到一组。

    Args:
        works: 所有论文条目。

    Returns:
        {group_id: [论文条目]} 的映射。
    """
    n = len(works)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[py] = px

    # P0: DOI 匹配
    doi_groups: Dict[str, int] = {}
    for i, w in enumerate(works):
        doi = w.get("doi")
        if doi:
            clean_doi = paper_utils._clean_doi(doi)
            if clean_doi in doi_groups:
                union(i, doi_groups[clean_doi])
            else:
                doi_groups[clean_doi] = i

    # P1: arXiv ID 匹配
    arxiv_groups: Dict[str, int] = {}
    for i, w in enumerate(works):
        aid = w.get("arxiv_id")
        if aid:
            base = paper_utils._strip_arxiv_version(aid)
            if base in arxiv_groups:
                union(i, arxiv_groups[base])
            else:
                arxiv_groups[base] = i

    # P2: 标题匹配（只对尚无 P0/P1 关系的对做）
    roots_for = {}
    for i in range(n):
        roots_for[i] = find(i)

    for i in range(n):
        for j in range(i + 1, n):
            if roots_for[i] == roots_for[j]:
                continue
            t1, t2 = works[i].get("title", ""), works[j].get("title", "")
            if paper_utils.title_match(t1, t2):
                union(i, j)

    # 构建分组
    groups: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for i in range(n):
        root = find(i)
        groups[root].append(works[i])

    return dict(groups)


def merge_groups(groups: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """将去重分组合并为唯一论文列表。

    Args:
        groups: {group_id: [条目列表]}。

    Returns:
        合并后的论文列表。
    """
    merged: List[Dict[str, Any]] = []
    for group_id, entries in groups.items():
        m = paper_utils.merge_paper_entries(entries)
        if m:
            # GS 截断标题时保留原文本，不静默丢弃
            if not m.get("title"):
                m["title"] = m.get("original_title") or "[截断标题]"
                m["title_truncated"] = True
            merged.append(m)

    # 排序：共证源数多优先 → 引用数高优先 → 年份新优先
    merged.sort(
        key=lambda p: (
            -p.get("source_count", 0) if p.get("source_count") else 0,
            -(p.get("cited_by_count") or 0),
            -(int(p.get("year") or 0)),
        ),
    )
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(
        description="多源论文合并与去重",
        epilog="示例: python scripts/paper_merger.py openalex.json arxiv.json s2.json --output merged.json",
    )
    parser.add_argument("input_files", nargs="+", help="输入 JSON 文件（至少 1 个）")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # 加载所有源
    all_works: List[Dict[str, Any]] = []
    source_stats: Dict[str, int] = {}
    for path in args.input_files:
        works = load_works(path)
        all_works.extend(works)
        source_name = works[0].get("source", "unknown") if works else "unknown"
        source_stats[source_name] = source_stats.get(source_name, 0) + len(works)
        logger.info(f"{path}: {len(works)} works (source: {source_name})")

    if not all_works:
        logger.warning("No works loaded from any input file")
        result = {"merged_count": 0, "works": [], "source_stats": source_stats}
        paper_utils.write_output(result, args.output)
        return

    before = len(all_works)
    groups = group_by_deduplication(all_works)
    merged = merge_groups(groups)
    after = len(merged)

    logger.info(f"Before: {before} works, After dedup: {after} works (removed {before - after} duplicates)")

    result = {
        "merged_count": after,
        "source_stats": source_stats,
        "sources_used": list(source_stats.keys()),
        "works": merged,
    }

    paper_utils.write_output(result, args.output)

    if args.output:
        print(f"✅ {before} → {after} works after dedup → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
