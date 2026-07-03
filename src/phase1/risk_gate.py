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

    profile_name = str(professor.get("name") or verified_ids.get("name") or "")
    if not has_english_name(profile_name):
        reasons.append("English name missing from professor/verified_ids name")

    verification = verified_ids.get("verification") or {}
    tier = str(verification.get("tier") or "").upper()
    if tier == "T4":
        reasons.append("verification tier is T4; identity depends on full fallback")
    elif verified_ids and tier not in {"T1", "T2", "T3"}:
        reasons.append("verification tier missing or invalid")

    prof_email = str(professor.get("email_domain") or "").strip().lower()
    verified_email = str(verification.get("email_domain") or "").strip().lower()
    if prof_email and verified_email and prof_email != verified_email:
        reasons.append(f"email domain mismatch: professor={prof_email}, verified={verified_email}")

    single_source = count_single_source_oa_arxiv(papers)
    single_source_ratio = (single_source / total) if total else 0.0
    if total and single_source_ratio > single_source_ratio_limit:
        reasons.append(
            f"single-source OA/arXiv ratio {single_source_ratio:.1%} exceeds {single_source_ratio_limit:.1%}"
        )

    gs_count = source_count(merged, "google_scholar")
    if gs_count and total > int(gs_count * TOTAL_OVER_GS_LIMIT):
        reasons.append(f"merged paper count {total} exceeds GS baseline {gs_count} by more than 20%")

    ids = verified_ids.get("ids") or {}
    has_gs = bool(ids.get("gs_id"))
    has_oa = bool(ids.get("oa_id"))
    gs_oa_overlap = count_overlap(papers, "google_scholar", "openalex")
    if has_gs and has_oa and total >= 5 and gs_oa_overlap < 3:
        reasons.append(f"GS/OA overlap below threshold: {gs_oa_overlap} papers")

    mode = CONSERVATIVE if reasons else STANDARD
    return RiskResult(
        mode=mode,
        reasons=reasons,
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
    else:
        print("risk: PASS")
        print("reason: no identity conflict or source-risk trigger")
    print("metrics:")
    for key, value in result.metrics.items():
        print(f"- {key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Decide Phase 1 standard vs conservative search mode")
    parser.add_argument("--prof-dir", help="output/.../<name> profile directory")
    parser.add_argument("--ts", help="archive timestamp override")
    parser.add_argument("--merged", help="04_merged.json path")
    parser.add_argument("--verified-ids", help="00_verified_ids.json path")
    parser.add_argument("--strict", action="store_true", help="exit 2 when conservative mode is required")
    args = parser.parse_args()

    merged_path, verified_path = resolve_paths(args)
    merged = load_json(merged_path)
    verified_ids = load_json(verified_path) if verified_path and os.path.exists(verified_path) else {}
    result = evaluate_risk(merged, verified_ids)
    print_result(result)
    if args.strict and result.mode == CONSERVATIVE:
        raise SystemExit(2)


if __name__ == "__main__":
    main()