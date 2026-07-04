#!/usr/bin/env python3
"""Apply reviewed paper exclusions to current Phase 1 merged state.

This script is for conservative-mode source review. It updates only the active
`04_merged.json` resolved by `--prof-dir`; raw GS/OA/arXiv source files are not
edited.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ProfDirResolver, clean_doi


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def write_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def require_source_url(source_url: str) -> str:
    source_url = (source_url or "").strip()
    if not source_url.startswith(("http://", "https://")):
        raise ValueError("--source-url is required and must be an HTTP(S) URL")
    return source_url


def normalize_dois(dois: Iterable[str]) -> Set[str]:
    normalized = {clean_doi(doi) for doi in dois if doi and clean_doi(doi)}
    if not normalized:
        raise ValueError("At least one --exclude-doi value is required")
    return normalized


def paper_doi(paper: Dict[str, Any]) -> str:
    raw = paper.get("doi")
    return clean_doi(str(raw)) if raw else ""


def recompute_statistics(merged: Dict[str, Any]) -> None:
    papers = merged.get("papers") or []
    by_source: Dict[str, int] = {}
    for paper in papers:
        sources = paper.get("sources")
        if isinstance(sources, list):
            source_values = sources
        else:
            source = paper.get("source")
            source_values = [source] if source else []
        for source in source_values:
            source_key = str(source)
            by_source[source_key] = by_source.get(source_key, 0) + 1

    stats = merged.setdefault("statistics", {})
    stats["total"] = len(papers)
    stats["unique"] = len(papers)
    stats["by_source"] = by_source


def exclusion_record(
    paper: Dict[str, Any],
    reason: str,
    source_url: str,
) -> Dict[str, Any]:
    return {
        "title": paper.get("title") or "[未找到]",
        "doi": paper.get("doi") or "[未找到]",
        "year": paper.get("year"),
        "authors": paper.get("authors"),
        "sources": paper.get("sources") or ([paper.get("source")] if paper.get("source") else []),
        "reason": reason,
        "source_url": source_url,
    }


def exclude_papers_by_doi(
    prof_dir: str,
    dois: Iterable[str],
    reason: str,
    source_url: str,
    ts: Optional[str] = None,
) -> int:
    source_url = require_source_url(source_url)
    reason = (reason or "").strip()
    if not reason:
        raise ValueError("--reason is required")

    targets = normalize_dois(dois)
    resolver = ProfDirResolver(prof_dir, ts)
    if not resolver.archive_dir:
        raise ValueError(f"{prof_dir} is missing _internal/latest.txt; run phase1_init.py first")

    merged = load_json(resolver.merged_path)
    papers = merged.get("papers")
    if not isinstance(papers, list):
        raise ValueError("04_merged.json must contain a papers list")

    remaining: List[Dict[str, Any]] = []
    removed: List[Dict[str, Any]] = []
    for paper in papers:
        if isinstance(paper, dict) and paper_doi(paper) in targets:
            removed.append(paper)
        else:
            remaining.append(paper)

    removed_dois = {paper_doi(paper) for paper in removed}
    missing = sorted(targets - removed_dois)
    if missing:
        raise ValueError(f"DOI not found in merged papers: {', '.join(missing)}")

    merged["papers"] = remaining
    review = merged.setdefault("metadata", {}).setdefault("paper_review", {})
    excluded = review.setdefault("excluded", [])
    for paper in removed:
        excluded.append(exclusion_record(paper, reason, source_url))

    recompute_statistics(merged)
    write_json(resolver.merged_path, merged)
    return len(removed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Exclude reviewed DOI rows from active Phase 1 merged state")
    parser.add_argument("--prof-dir", required=True, help="output/.../<name> profile directory")
    parser.add_argument("--ts", help="archive timestamp override")
    parser.add_argument("--exclude-doi", action="append", required=True, help="DOI to exclude; repeat as needed")
    parser.add_argument("--reason", required=True, help="Short review reason")
    parser.add_argument("--source-url", required=True, help="HTTP(S) source supporting the review context")
    args = parser.parse_args()

    count = exclude_papers_by_doi(
        prof_dir=args.prof_dir,
        dois=args.exclude_doi,
        reason=args.reason,
        source_url=args.source_url,
        ts=args.ts,
    )
    print(f"paper_review: excluded {count} papers")


if __name__ == "__main__":
    main()
