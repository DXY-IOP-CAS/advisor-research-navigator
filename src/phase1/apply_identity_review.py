#!/usr/bin/env python3
"""Apply a reviewed identity correction to current Phase 1 state.

This is for conservative-mode fixes after official-source review. It updates
only the active `00_verified_ids.json` and `04_merged.json` resolved by
`--prof-dir`; it does not edit raw GS/OA/arXiv source files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ProfDirResolver


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


def require_official_url(official_url: str) -> str:
    official_url = (official_url or "").strip()
    if not official_url.startswith(("http://", "https://")):
        raise ValueError("--official-url is required and must be an HTTP(S) URL")
    return official_url


def apply_identity_review(
    prof_dir: str,
    display_name: Optional[str] = None,
    official_email_domain: Optional[str] = None,
    official_affiliation: Optional[str] = None,
    official_url: str = "",
    note: str = "",
    ts: Optional[str] = None,
) -> None:
    official_url = require_official_url(official_url)
    resolver = ProfDirResolver(prof_dir, ts)
    if not resolver.archive_dir:
        raise ValueError(f"{prof_dir} 下找不到 _internal/latest.txt，请先跑 phase1_init.py")

    verified = load_json(resolver.verified_ids_path)
    merged = load_json(resolver.merged_path)

    normalized_name = (display_name or "").strip()
    normalized_domain = (official_email_domain or "").strip().lower()
    normalized_affiliation = (official_affiliation or "").strip()

    if normalized_name:
        verified["name"] = normalized_name
        merged.setdefault("professor", {})["name"] = normalized_name

    if normalized_domain:
        verified.setdefault("verification", {})["email_domain"] = normalized_domain
        merged.setdefault("professor", {})["email_domain"] = normalized_domain

    if normalized_affiliation:
        verified["affiliation"] = normalized_affiliation
        merged.setdefault("professor", {})["affiliation"] = normalized_affiliation

    verified.setdefault("sources", {})["official_profile_url"] = official_url
    review = {
        "official_url": official_url,
        "note": note.strip() if note else "official identity review",
    }
    if normalized_name:
        review["display_name"] = normalized_name
    if normalized_domain:
        review["official_email_domain"] = normalized_domain
    if normalized_affiliation:
        review["official_affiliation"] = normalized_affiliation

    verified["identity_review"] = review
    merged.setdefault("metadata", {})["identity_review"] = review

    write_json(resolver.verified_ids_path, verified)
    write_json(resolver.merged_path, merged)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply reviewed identity fields to active Phase 1 state")
    parser.add_argument("--prof-dir", required=True, help="output/.../<name> profile directory")
    parser.add_argument("--ts", help="archive timestamp override")
    parser.add_argument("--display-name", help="Reviewed display name, e.g. 汪非凡 (Feifan Wang)")
    parser.add_argument("--official-email-domain", help="Reviewed current official email domain, e.g. iphy.ac.cn")
    parser.add_argument("--official-affiliation", help="Reviewed current official affiliation")
    parser.add_argument("--official-url", required=True, help="Official source URL supporting this review")
    parser.add_argument("--note", default="", help="Short review note")
    args = parser.parse_args()

    apply_identity_review(
        prof_dir=args.prof_dir,
        display_name=args.display_name,
        official_email_domain=args.official_email_domain,
        official_affiliation=args.official_affiliation,
        official_url=args.official_url,
        note=args.note,
        ts=args.ts,
    )
    print("identity_review: updated active verified_ids and merged profile")


if __name__ == "__main__":
    main()
