#!/usr/bin/env python3
"""Verify DOI titles in phase source tables against DOI metadata.

This is a source-hygiene check, not an academic quality judge. It catches hard
metadata drift such as a source table title describing the wrong mechanism.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Mapping


DEFAULT_DOCS = ["02_领域地图.md", "03_论文路线.md", "04_学习向导.md"]
SOURCE_LABEL_RE = re.compile(r"<a id=\"[oprb]\d+\"></a>\[(?P<label>[OPRB]\d+)\]")
DOI_URL_RE = re.compile(r"^https://doi\.org/(?P<doi>[^\s]+)$", re.IGNORECASE)
NATURE_ARTICLE_RE = re.compile(
    r"^https://www\.nature\.com/articles/(?P<article>s[0-9a-z-]+)$",
    re.IGNORECASE,
)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
NON_WORD_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class DoiRow:
    filename: str
    label: str
    title: str
    doi: str


@dataclass
class VerifyResult:
    ok: bool
    messages: list[str]


def normalize_title(title: str) -> str:
    without_tags = TAG_RE.sub(" ", html.unescape(title))
    collapsed = SPACE_RE.sub(" ", without_tags).strip().lower()
    return NON_WORD_RE.sub(" ", collapsed).strip()


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


def extract_doi_rows(filename: str, text: str) -> list[DoiRow]:
    rows: list[DoiRow] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue

        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if len(columns) < 5:
            continue

        label_match = SOURCE_LABEL_RE.search(columns[0])
        if not label_match:
            continue

        doi = doi_from_link(columns[3])
        if not doi:
            continue

        rows.append(
            DoiRow(
                filename=filename,
                label=f"[{label_match.group('label')}]",
                title=columns[1],
                doi=doi,
            )
        )
    return rows


def doi_from_link(link: str) -> str | None:
    doi_match = DOI_URL_RE.match(link.strip())
    if doi_match:
        return doi_match.group("doi").strip().rstrip(".")

    nature_match = NATURE_ARTICLE_RE.match(link.strip())
    if nature_match:
        return f"10.1038/{nature_match.group('article')}"

    return None


def _fetch_crossref_title(doi: str) -> str | None:
    encoded = urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(
        f"https://api.crossref.org/works/{encoded}",
        headers={"User-Agent": "pilot-test-source-metadata-verifier/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    titles = payload.get("message", {}).get("title") or []
    if not titles:
        return None
    return " ".join(str(part) for part in titles)


def _fetch_datacite_title(doi: str) -> str | None:
    encoded = urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(
        f"https://api.datacite.org/dois/{encoded}",
        headers={"User-Agent": "pilot-test-source-metadata-verifier/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    titles = payload.get("data", {}).get("attributes", {}).get("titles") or []
    for item in titles:
        title = item.get("title") if isinstance(item, dict) else None
        if title:
            return str(title)
    return None


def verify_rows(
    rows: list[DoiRow],
    metadata: Mapping[str, str] | None = None,
    title_similarity_threshold: float = 0.92,
) -> VerifyResult:
    messages: list[str] = []
    metadata = metadata or {}

    for row in rows:
        expected_title = metadata.get(row.doi)
        if expected_title is None:
            expected_title = _fetch_crossref_title(row.doi)
        if expected_title is None:
            expected_title = _fetch_datacite_title(row.doi)

        if expected_title is None:
            messages.append(f"[WARN] {row.filename} {row.label} DOI metadata unavailable: {row.doi}")
            continue

        if _similarity(row.title, expected_title) < title_similarity_threshold:
            messages.append(
                f"[FAIL] {row.filename} {row.label} DOI title mismatch: "
                f"document='{row.title}' crossref='{expected_title}'"
            )

    if not messages:
        messages.append("[OK] DOI source metadata checks passed")
    return VerifyResult(ok=not any(message.startswith("[FAIL]") for message in messages), messages=messages)


def verify_prof_dir(
    prof_dir: str | Path,
    metadata: Mapping[str, str] | None = None,
    filenames: list[str] | None = None,
) -> VerifyResult:
    prof = Path(prof_dir)
    rows: list[DoiRow] = []
    for filename in filenames or DEFAULT_DOCS:
        path = prof / filename
        if not path.exists():
            continue
        rows.extend(extract_doi_rows(filename, path.read_text(encoding="utf-8")))

    return verify_rows(rows, metadata=metadata)


def _load_metadata(path: str | None) -> dict[str, str] | None:
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in data.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify DOI source titles in phase source tables.")
    parser.add_argument("--prof-dir", required=True, help="Profile directory containing phase markdown docs")
    parser.add_argument(
        "--metadata-json",
        help="Optional JSON object mapping DOI to expected title; useful for deterministic tests",
    )
    args = parser.parse_args()

    result = verify_prof_dir(args.prof_dir, metadata=_load_metadata(args.metadata_json))
    for message in result.messages:
        print(message)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
