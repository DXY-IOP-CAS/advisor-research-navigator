#!/usr/bin/env python3
"""
step6_merge.py — 多源合并去重 + 教授信息合并

流水线位置：阶段 B 最后一步。收集所有源输出后执行。

数据流：
  [01_gs.json] ────────────┐
  [02_oa.json] ────────────┤
  [03_arxiv.json] ─────────┤
                           ▼
                     [本脚本] → 04_merged.json
                           │
                           ▼
                     [render_profile.py] → 01_基础画像.md

输入：N 个统一 SOURCE_OUTPUT 格式的 JSON 文件
输出：MERGED_OUTPUT 格式（详见 pipeline.md §2.3）

处理逻辑：
  1. 教授信息合并（按字段优先级：GS > OA，详见 PROF_PRIORITY 表）
  2. 论文去重（P0:DOI → P1:arXiv ID → P2:归一化标题）
  3. 字段择优（引用数: OA > GS；期刊名: OA > GS；institutions: 仅 OA）
  4. 多源交叉验证标记（source_count/sources）

特点：
  - 不读任何缓存，每次全新合并
  - 教授信息：GS 占 h-index/i10-index/引用数，OA 占 DOI/ORCID
  - arXiv 噪声由 render_profile.py 过滤（arXiv-only 无 DOI 视为噪声）
  - 合并层保留 institutions 字段（来自 OA），供 render_profile 做机构网络过滤
  - 排序：多源验证优先 → 引用数高优先 → 年份新优先

用法：
  python src/phase1/step6_merge.py --prof-dir output/...

依赖：标准库（utils.py 的匹配函数）
"""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    write_output, normalize_title,
    clean_doi, doi_match,
    strip_arxiv_version, arxiv_id_match,
    title_match, ProfDirResolver,
)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("step6_merge")


# ── 加载 ─────────────────────────────────────────────────────────────

def load_source(path: str) -> Optional[dict]:
    """加载统一格式的源输出。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None


# ── 教授信息合并 ──────────────────────────────────────────────────────

PROF_PRIORITY = {
    "name": ["google_scholar", "openalex"],
    "affiliation": ["google_scholar", "openalex"],
    "email_domain": ["google_scholar"],
    "gs_id": ["google_scholar"],
    "oa_id": ["openalex"],
    "orcid": ["openalex"],
    "h_index": ["google_scholar", "openalex"],
    "i10_index": ["google_scholar"],
    "total_citations": ["google_scholar", "openalex"],
}

def merge_professors(sources: List[dict]) -> dict:
    """按字段优先级合并教授信息。跳过 None 值。"""
    profs_by_source = {}
    for src in sources:
        src_name = src.get("source")
        prof = src.get("professor") or {}
        profs_by_source[src_name] = prof

    merged = {}
    for field, priority in PROF_PRIORITY.items():
        for src_name in priority:
            val = profs_by_source.get(src_name, {}).get(field)
            if val is not None:
                merged[field] = val
                break
    return merged


# ── 去重 ──────────────────────────────────────────────────────────────

def group_papers(all_papers: List[tuple]) -> Dict[int, List[tuple]]:
    """按去重优先级分組。返回 {group_id: [(paper, source_name), ...]}。"""
    n = len(all_papers)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[py] = px

    # P0: DOI
    doi_map = {}
    for i, (paper, _) in enumerate(all_papers):
        doi = paper.get("doi")
        if doi:
            cdoi = clean_doi(doi)
            if cdoi in doi_map:
                union(i, doi_map[cdoi])
            else:
                doi_map[cdoi] = i

    # P1: arXiv ID
    arxiv_map = {}
    for i, (paper, _) in enumerate(all_papers):
        aid = paper.get("arxiv_id")
        if aid:
            base = strip_arxiv_version(aid)
            if base in arxiv_map:
                union(i, arxiv_map[base])
            else:
                arxiv_map[base] = i

    # P2: 标题
    for i in range(n):
        for j in range(i + 1, n):
            if find(i) == find(j):
                continue
            t1, t2 = all_papers[i][0].get("title", ""), all_papers[j][0].get("title", "")
            if title_match(t1, t2):
                union(i, j)

    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(all_papers[i])

    return dict(groups)


# ── 合并单组论文 ────────────────────────────────────────────────────

FIELD_PRIORITY = {
    "title": ["openalex", "google_scholar", "arxiv"],
    "year": ["openalex", "arxiv", "google_scholar"],
    "authors": ["openalex", "arxiv"],
    "institutions": ["openalex"],
    "journal": ["openalex", "google_scholar", "arxiv"],
    "doi": ["openalex", "arxiv"],
    "arxiv_id": ["arxiv", "openalex"],
    "url": ["google_scholar", "openalex", "arxiv"],
    "citation_count": ["openalex", "google_scholar"],
    "abstract": ["arxiv"],
    "source": [],  # maintain the winning source for the best-field logic
}


def _pick(entries: List[dict], field: str) -> Any:
    """按优先级取最佳值。"""
    priority = FIELD_PRIORITY.get(field, [])
    for src in priority:
        for entry in entries:
            if entry.get("source") == src and entry.get(field) is not None:
                return entry[field]
    for entry in entries:
        if entry.get(field) is not None:
            return entry[field]
    return None


def merge_paper_group(entries: List[tuple]) -> dict:
    """合并一组论文为一个。entries = [(paper, source_name), ...]"""
    papers_only = [e[0] for e in entries]
    source_names = list(set(e[1] for e in entries))

    return {
        "title": _pick(papers_only, "title"),
        "year": _pick(papers_only, "year"),
        "authors": _pick(papers_only, "authors"),
        "institutions": _pick(papers_only, "institutions"),
        "journal": _pick(papers_only, "journal"),
        "doi": _pick(papers_only, "doi"),
        "arxiv_id": _pick(papers_only, "arxiv_id"),
        "url": _pick(papers_only, "url"),
        "citation_count": _pick(papers_only, "citation_count"),
        "source": _pick(papers_only, "source"),
        "sources": source_names,
        "source_count": len(source_names),
        "abstract": _pick(papers_only, "abstract"),
    }


# ── 主合并逻辑 ──────────────────────────────────────────────────────

def merge(source_paths: List[str]) -> dict:
    """合并多个源文件。返回 MERGED_OUTPUT 格式。"""
    sources = []
    for p in source_paths:
        src = load_source(p)
        if src:
            sources.append(src)
        else:
            logger.warning(f"Skipping unreadable source: {p}")

    if not sources:
        return {
            "pipeline": "phase1", "step": "merge",
            "status": "error", "error": "No valid source files",
            "sources_used": [], "source_status": {},
            "professor": {}, "papers": [], "statistics": {},
        }

    # 源状态
    source_status = {s.get("source", f"src{i}"): s.get("status", "unknown")
                     for i, s in enumerate(sources)}
    sources_used = list(source_status.keys())

    # 教授信息合并
    professor = merge_professors(sources)

    # 论文收集（(paper, source_name) 对）
    all_pairs: List[tuple] = []
    for src in sources:
        src_name = src.get("source", "unknown")
        for p in src.get("papers", []):
            if p.get("title"):  # 无标题的论文跳过
                all_pairs.append((p, src_name))

    # 去重
    groups = group_papers(all_pairs)
    merged_papers = [merge_paper_group(entries) for entries in groups.values()]
    merged_papers.sort(key=lambda p: (
        -(p.get("source_count") or 0),
        -(p.get("citation_count") or 0),
        -(p.get("year") or 0),
    ))

    # 统计
    by_source = defaultdict(int)
    for p in merged_papers:
        for s in p.get("sources", []):
            by_source[s] += 1

    return {
        "pipeline": "phase1",
        "step": "merge",
        "sources_used": sources_used,
        "source_status": source_status,
        "professor": professor,
        "papers": merged_papers,
        "statistics": {
            "total": len(merged_papers),
            "by_source": dict(by_source),
            "unique": len(merged_papers),
        },
    }


# ── CLI ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="多源合并去重")
    parser.add_argument("input_files", nargs="*", help="统一格式的 JSON 源文件（常规执行不传，由 --prof-dir 推导）")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--archive-dir", help=argparse.SUPPRESS)
    parser.add_argument("--prof-dir", help="prof 根目录（output/.../姓名/），从 _internal/latest.txt 自动推导 active state")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    # prof-dir 优先；archive-dir 仅保留内部兼容，AI 不必手动拼路径
    if args.prof_dir and not args.archive_dir:
        args.archive_dir = ProfDirResolver(args.prof_dir).archive_dir
        if not args.archive_dir:
            parser.error(f"--prof-dir {args.prof_dir} 下找不到 _internal/latest.txt，请先跑 phase1_init.py")

    if args.archive_dir and not args.output:
        args.output = os.path.join(args.archive_dir, "04_merged.json")

    files = args.input_files
    if not files and args.archive_dir:
        files = [
            os.path.join(args.archive_dir, n)
            for n in ("01_gs.json", "02_oa.json", "03_arxiv.json")
            if os.path.exists(os.path.join(args.archive_dir, n))
        ]
    if not files:
        logger.error("没有输入文件。传 input_files 或 --prof-dir")
        sys.exit(1)

    result = merge(files)
    write_output(result, args.output)

    if args.output:
        s = result.get("statistics", {})
        print(f"✅ [merge] {s.get('total', 0)} papers from {len(result['sources_used'])} sources"
              f" → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
