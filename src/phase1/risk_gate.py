#!/usr/bin/env python3
"""Risk gate for Phase 1 standard vs conservative search mode.

The gate is intentionally deterministic. Agents start with standard search,
then run this script after identity locking and merge. If the gate reports
conservative_required, the agent must perform additional source checks before
rendering or claiming completion.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ProfDirResolver

STANDARD = "standard"
CONSERVATIVE = "conservative_required"
SINGLE_SOURCE_RATIO_LIMIT = 0.10
TOTAL_OVER_GS_LIMIT = 1.20


@dataclass
class RiskResult:
    mode: str
    reasons: List[str]
    actions: List[str]
    metrics: Dict[str, Any]


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def has_english_name(name: str) -> bool:
    return bool(re.search(r"\([A-Za-z][A-Za-z .'-]+\)", name or ""))


def paper_sources(paper: Dict[str, Any]) -> List[str]:
    sources = paper.get("sources")
    if isinstance(sources, list):
        return [str(s) for s in sources]
    source = paper.get("source")
    return [str(source)] if source else []


def count_single_source_oa_arxiv(papers: Iterable[Dict[str, Any]]) -> int:
    count = 0
    for paper in papers:
        sources = set(paper_sources(paper))
        if len(sources) == 1 and sources <= {"openalex", "arxiv"}:
            count += 1
    return count


def single_source_oa_arxiv_papers(papers: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for paper in papers:
        sources = set(paper_sources(paper))
        if len(sources) == 1 and sources <= {"openalex", "arxiv"}:
            rows.append(paper)
    return rows


def count_overlap(papers: Iterable[Dict[str, Any]], left: str, right: str) -> int:
    total = 0
    for paper in papers:
        sources = set(paper_sources(paper))
        if left in sources and right in sources:
            total += 1
    return total


def source_count(merged: Dict[str, Any], source: str) -> int:
    stats = merged.get("statistics") or {}
    by_source = stats.get("by_source") or {}
    raw = by_source.get(source, 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def evaluate_risk(
    merged: Dict[str, Any],
    verified_ids: Optional[Dict[str, Any]] = None,
    single_source_ratio_limit: float = SINGLE_SOURCE_RATIO_LIMIT,
) -> RiskResult:
    verified_ids = verified_ids or {}
    professor = merged.get("professor") or {}
    papers = merged.get("papers") or []
    total = len(papers)
    reasons: List[str] = []
    actions: List[str] = []

    profile_name = str(professor.get("name") or verified_ids.get("name") or "")
    if not has_english_name(profile_name):
        reasons.append("English name missing from professor/verified_ids name")
        actions.append("补官网英文名，保持 `中文名 (English Name)` 格式；补不到则在画像和 e2e 记录里写 `[未找到]`。")

    verification = verified_ids.get("verification") or {}
    tier = str(verification.get("tier") or "").upper()
    if tier == "T4":
        reasons.append("verification tier is T4; identity depends on full fallback")
        actions.append("重新做身份锁定：用官网、GS、OpenAlex、ORCID 和至少 3 篇 DOI/标题/年份论文指纹交叉验证。")
    elif verified_ids and tier not in {"T1", "T2", "T3"}:
        reasons.append("verification tier missing or invalid")
        actions.append("补充验证层级 T1/T2/T3/T4 及依据；缺依据时按 conservative 记录 `需人工复核`。")

    prof_email = str(professor.get("email_domain") or "").strip().lower()
    verified_email = str(verification.get("email_domain") or "").strip().lower()
    if prof_email and verified_email and prof_email != verified_email:
        reasons.append(f"email domain mismatch: professor={prof_email}, verified={verified_email}")
        actions.append("核查邮箱域名不一致是否来自 GS 滞后或跨机构履历；用官网当前邮箱、ORCID、OpenAlex 和论文指纹说明。")

    single_source = count_single_source_oa_arxiv(papers)
    single_source_ratio = (single_source / total) if total else 0.0
    if total and single_source_ratio > single_source_ratio_limit:
        reasons.append(
            f"single-source OA/arXiv ratio {single_source_ratio:.1%} exceeds {single_source_ratio_limit:.1%}"
        )
        actions.append("逐篇核查 OA/arXiv-only 论文是否属于该学者；不确定则剔除，或标为已人工核查后再进入画像。")

    gs_count = source_count(merged, "google_scholar")
    if gs_count and total > int(gs_count * TOTAL_OVER_GS_LIMIT):
        reasons.append(f"merged paper count {total} exceeds GS baseline {gs_count} by more than 20%")
        actions.append("检查合并结果是否混入同名作者论文，重点核查超出 GS baseline 的 OpenAlex/arXiv 单源论文。")

    ids = verified_ids.get("ids") or {}
    has_gs = bool(ids.get("gs_id"))
    has_oa = bool(ids.get("oa_id"))
    gs_oa_overlap = count_overlap(papers, "google_scholar", "openalex")
    if has_gs and has_oa and total >= 5 and gs_oa_overlap < 3:
        reasons.append(f"GS/OA overlap below threshold: {gs_oa_overlap} papers")
        actions.append("核查 GS profile 与 OpenAlex Author 是否为同一人；优先用 DOI、标题、年份和合著者网络建立交叉重合。")

    mode = CONSERVATIVE if reasons else STANDARD
    return RiskResult(
        mode=mode,
        reasons=reasons,
        actions=actions,
        metrics={
            "total_papers": total,
            "gs_baseline": gs_count,
            "single_source_oa_arxiv": single_source,
            "single_source_oa_arxiv_ratio": round(single_source_ratio, 4),
            "gs_oa_overlap": gs_oa_overlap,
            "verification_tier": tier or None,
        },
    )


def resolve_paths(args: argparse.Namespace) -> tuple[str, Optional[str]]:
    if args.prof_dir:
        resolver = ProfDirResolver(args.prof_dir, args.ts)
        merged_path = args.merged or resolver.merged_path
        verified_path = args.verified_ids or resolver.verified_ids_path
        return merged_path, verified_path
    if not args.merged:
        raise SystemExit("Pass --prof-dir or --merged")
    return args.merged, args.verified_ids


def print_result(result: RiskResult) -> None:
    print(f"mode: {result.mode}")
    if result.reasons:
        print("risk: FAIL")
        print("reason:")
        for reason in result.reasons:
            print(f"- {reason}")
        print("next_actions:")
        for action in result.actions:
            print(f"- {action}")
    else:
        print("risk: PASS")
        print("reason: no identity conflict or source-risk trigger")
    print("metrics:")
    for key, value in result.metrics.items():
        print(f"- {key}: {value}")


def print_single_source_papers(papers: Iterable[Dict[str, Any]]) -> None:
    rows = single_source_oa_arxiv_papers(papers)
    if not rows:
        print("single_source_oa_arxiv_papers: none")
        return
    print("single_source_oa_arxiv_papers:")
    for paper in rows:
        year = paper.get("year") or "[未找到]"
        title = paper.get("title") or "[未找到]"
        doi = paper.get("doi")
        arxiv_id = paper.get("arxiv_id")
        marker = doi or (f"arXiv:{arxiv_id}" if arxiv_id else "[未找到]")
        authors = paper.get("authors")
        if isinstance(authors, list) and authors:
            author_text = "; ".join(str(author) for author in authors[:8])
            if len(authors) > 8:
                author_text += "; ..."
        elif authors:
            author_text = str(authors)
        else:
            author_text = "[未找到]"
        print(f"- {year} | {title} | {marker} | {author_text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Decide Phase 1 standard vs conservative search mode")
    parser.add_argument("--prof-dir", help="output/.../<name> profile directory")
    parser.add_argument("--ts", help="archive timestamp override")
    parser.add_argument("--merged", help="04_merged.json path")
    parser.add_argument("--verified-ids", help="00_verified_ids.json path")
    parser.add_argument("--list-single-source", action="store_true", help="print OA/arXiv-only paper titles for conservative review")
    parser.add_argument("--strict", action="store_true", help="exit 2 when conservative mode is required")
    args = parser.parse_args()

    merged_path, verified_path = resolve_paths(args)
    merged = load_json(merged_path)
    verified_ids = load_json(verified_path) if verified_path and os.path.exists(verified_path) else {}
    result = evaluate_risk(merged, verified_ids)
    print_result(result)
    if args.list_single_source:
        print_single_source_papers(merged.get("papers") or [])
    if args.strict and result.mode == CONSERVATIVE:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
