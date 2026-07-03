#!/usr/bin/env python3
"""Light structural verifier for research-advisor phase documents.

This script intentionally checks only deterministic document hygiene. It does
not judge whether the field map, paper interpretation, or learning design is
correct; those remain workflow + human review responsibilities.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


DOCS = {
    "01_基础画像.md": ["## 运行信息"],
    "02_领域脉络.md": [
        "## 运行信息",
        "## 导师路径速览",
        "## 当前方向学科定位",
        "## 领域发展树",
        "## 关键问题和技术路线",
        "## 当前前沿",
        "## 来源与待复核点",
    ],
    "03_论文定位.md": [
        "## 运行信息",
        "## 领域树节点定义",
        "## 论文定位总表",
        "## 当前主线论文",
        "## 前史积累论文",
        "## 旁支与弱证据",
        "## 给学习讲义的知识点清单",
    ],
    "04_学习讲义.md": [
        "## 运行信息",
        "## 读者起点",
        "## 学习主线总图",
        "## 数学基础",
        "## 物理基础",
        "## 领域核心工具",
        "## 导师当前方向专题",
        "## 论文阅读顺序",
        "## 资源指针",
    ],
}

FORBIDDEN = [
    "推荐申请",
    "值得报考",
    "匹配度",
    "适合申请",
    "建议报考",
    "强烈推荐",
]

SOURCE_RE = re.compile(r"https?://|\[未找到\]|需人工复核")
CITATION_RE = re.compile(r"\[(O|P|R|B)(\d+)\]")
BARE_URL_RE = re.compile(r"(?<!\]\()https?://[^\s)]+")
SOURCE_SECTION_MARKER = "## 参考文献与来源"
SOURCE_TABLE_HEADER = "| 编号 | 来源 | 用途 | 链接 | 备注 |"


@dataclass
class VerifyResult:
    ok: bool
    messages: list[str]


def _has_source_marker(text: str) -> bool:
    return bool(SOURCE_RE.search(text))


def _body_after_frontmatter(text: str) -> str:
    stripped = text.lstrip("\ufeff")
    if not stripped.startswith("---\n"):
        return stripped
    parts = stripped.split("\n---\n", 1)
    if len(parts) == 2:
        return parts[1].lstrip()
    return stripped


def _extract_citation_keys(text: str) -> set[str]:
    return {f"[{kind}{number}]" for kind, number in CITATION_RE.findall(text)}


def _split_sources_section(text: str) -> tuple[str, str]:
    if SOURCE_SECTION_MARKER not in text:
        return text, ""
    body, sources = text.split(SOURCE_SECTION_MARKER, 1)
    return body, sources


def _check_source_format(filename: str, text: str, messages: list[str]) -> None:
    if filename == "01_基础画像.md":
        return

    body, sources = _split_sources_section(text)
    if not sources:
        messages.append(f"[FAIL] {filename} 缺少章节: {SOURCE_SECTION_MARKER}")
        return

    if BARE_URL_RE.search(body):
        messages.append(f"[FAIL] {filename} 正文含裸 URL")

    if SOURCE_TABLE_HEADER not in sources:
        messages.append(f"[FAIL] {filename} 来源表缺少五列表头: {SOURCE_TABLE_HEADER}")

    body_keys = _extract_citation_keys(body)
    source_keys = _extract_citation_keys(sources)
    missing = sorted(body_keys - source_keys)
    for key in missing:
        messages.append(f"[FAIL] {filename} 引用键未在来源表中定义: {key}")


def verify_prof_dir(prof_dir: str | Path) -> VerifyResult:
    prof = Path(prof_dir)
    messages: list[str] = []

    for filename, sections in DOCS.items():
        path = prof / filename
        if not path.exists():
            messages.append(f"[FAIL] 缺少文件: {filename}")
            continue

        text = path.read_text(encoding="utf-8")
        body = _body_after_frontmatter(text)
        if not body.startswith("# "):
            messages.append(f"[FAIL] {filename} 缺少一级标题")

        for section in sections:
            if section not in text:
                messages.append(f"[FAIL] {filename} 缺少章节: {section}")

        if not _has_source_marker(text):
            messages.append(f"[FAIL] {filename} 缺少来源 URL、[未找到] 或需人工复核标记")

        _check_source_format(filename, text, messages)

        for word in FORBIDDEN:
            if word in text:
                messages.append(f"[FAIL] {filename} 含禁用评价语: {word}")

    if not messages:
        messages.append("[OK] phase docs deterministic checks passed")
    return VerifyResult(ok=not any(m.startswith("[FAIL]") for m in messages), messages=messages)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify phase 1-4 markdown document hygiene.")
    parser.add_argument("--prof-dir", required=True, help="Profile directory containing 01-04 markdown docs")
    args = parser.parse_args()

    result = verify_prof_dir(args.prof_dir)
    for message in result.messages:
        print(message)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
