"""
paper_utils.py — 论文去重、标题归一化、跨源字段选取等共享函数。

依赖：零（标准库即可）。
用法：被 openalex_works.py / arxiv_preprints.py / paper_merger.py 等导入。
"""

import json
import re
import sys
from typing import Any, Dict, List, Optional


def normalize_title(title: str) -> str:
    """论文标题归一化：去标点 → 小写 → 去空格。

    Args:
        title: 原始标题。

    Returns:
        归一化后的纯小写字符串，仅含字母数字。
    """
    if not title:
        return ""
    cleaned = re.sub(r"[^\w\s]", "", title)
    return re.sub(r"\s+", "", cleaned.lower().strip())


def doi_match(doi1: Optional[str], doi2: Optional[str]) -> bool:
    """比对两个 DOI 是否相同（大小写不敏感）。"""
    if not doi1 or not doi2:
        return False
    return _clean_doi(doi1) == _clean_doi(doi2)


def _clean_doi(doi: str) -> str:
    """清洗 DOI：去空格、小写、去协议前缀。"""
    doi = doi.strip().lower()
    return doi.removeprefix("https://doi.org/").removeprefix("http://doi.org/").removeprefix("doi:")


def arxiv_id_match(id1: Optional[str], id2: Optional[str]) -> bool:
    """比对两个 arXiv ID 是否相同（忽略版本后缀 v1/v2 等）。

    例：2101.12345v1 → 2101.12345 与 2101.12345v2 视为匹配。
    """
    if not id1 or not id2:
        return False
    return _strip_arxiv_version(id1) == _strip_arxiv_version(id2)


def _strip_arxiv_version(arxiv_id: str) -> str:
    """去除 arXiv ID 的版本后缀。"""
    return re.sub(r"v\d+$", "", arxiv_id.strip())


def title_match(t1: str, t2: str, threshold: float = 0.85) -> bool:
    """通过归一化标题比对两篇论文是否相同。

    先精确匹配，再检查一方是否包含另一方（子串匹配）。
    阈值 threshold 仅在子串匹配时启用。

    Args:
        t1: 标题 1。
        t2: 标题 2。
        threshold: 最短标题长度与最长标题长度的比例阈值。

    Returns:
        是否匹配。
    """
    n1, n2 = normalize_title(t1), normalize_title(t2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    if n1 in n2 or n2 in n1:
        # 归一化后一方是完整的子串 → 强信号，直接匹配
        return True
    return False


def best_field(
    sources: List[Dict[str, Any]],
    field: str,
    priority: List[str],
) -> Optional[Any]:
    """从多个数据源中按优先级选取最佳字段值。

    Args:
        sources: 数据源列表，每项含 {"source": "openalex", ...}。
        field: 字段名。
        priority: 数据源优先级，['openalex', 's2'] 表示 openalex 优先。

    Returns:
        最优源的值，所有源都没有则返回 None。
    """
    for src in priority:
        for item in sources:
            if item.get("source") == src and item.get(field) is not None:
                return item[field]
    return None


def merge_paper_entries(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """合并同一篇论文的多个来源条目，按最佳字段选取合并。

    Args:
        entries: 来自不同源的同一篇论文的条目。

    Returns:
        合并后的论文对象，含独有的 source 列表。
    """
    if not entries:
        return {}

    sources = []
    for e in entries:
        source_name = e.get("source", "unknown")
        sources.append(source_name)

    merged = {
        "title": best_field(entries, "title", ["openalex", "s2", "arxiv", "google_scholar"]),
        "doi": best_field(entries, "doi", ["openalex", "crossref", "s2"]),
        "arxiv_id": best_field(entries, "arxiv_id", ["arxiv", "s2", "openalex"]),
        "publication_date": best_field(entries, "publication_date", ["openalex", "arxiv", "google_scholar"]),
        "journal": best_field(entries, "journal", ["openalex", "s2"]),
        "cited_by_count": best_field(entries, "cited_by_count", ["openalex", "s2", "google_scholar"]),
        "tldr": best_field(entries, "tldr", ["s2"]),
        "authors": best_field(entries, "authors", ["openalex", "s2"]),
        "year": best_field(entries, "year", ["openalex", "arxiv", "s2", "google_scholar"]),
        "type": best_field(entries, "type", ["openalex"]),
        "sources": sources,
        "source_count": len(set(sources)),
    }
    return merged


def find_duplicate_group(
    papers: List[Dict[str, Any]],
    lookup: Dict[str, List[int]],
) -> Dict[int, int]:
    """构建论文分组：每篇论文的索引映射到其组 ID。

    Args:
        papers: 论文列表（无结构化分组）。
        lookup: 预计算好的索引表（可选）。

    Returns:
        {论文索引: 组ID} 的映射。
    """
    n = len(papers)
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

    for i in range(n):
        for j in range(i + 1, n):
            p1, p2 = papers[i], papers[j]
            if doi_match(p1.get("doi"), p2.get("doi")):
                union(i, j)
            elif arxiv_id_match(p1.get("arxiv_id"), p2.get("arxiv_id")):
                union(i, j)
            elif title_match(p1.get("title", ""), p2.get("title", "")):
                union(i, j)

    group_map: Dict[int, int] = {}
    group_id = 0
    seen_roots = {}
    for i in range(n):
        root = find(i)
        if root not in seen_roots:
            seen_roots[root] = group_id
            group_id += 1
        group_map[i] = seen_roots[root]

    return group_map


def safe_json(data: Any, indent: int = 2) -> str:
    """安全的 JSON 序列化，处理非 ASCII 字符和 None。"""
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def write_output(data: Any, output_path: Optional[str] = None) -> None:
    """写 JSON 输出到文件或 stdout。"""
    text = safe_json(data)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
        sys.stdout.write("\n")
