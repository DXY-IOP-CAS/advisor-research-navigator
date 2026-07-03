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
    "01_基础画像.md": ["## 资料概览"],
    "02_领域地图.md": [
        "## 资料概览",
        "## 导师路径速览",
        "## 当前方向学科定位",
        "## 领域发展树",
        "## 关键问题和技术路线",
        "## 当前前沿",
        "## 证据与待复核点",
    ],
    "03_论文路线.md": [
        "## 资料概览",
        "## 先抓住论文在回答什么问题",
        "## 论文线怎样连成研究路线",
        "## 当前主线论文",
        "## 前史积累论文",
        "## 旁支与弱证据",
        "## 给学习向导的知识点清单",
    ],
    "04_学习向导.md": [
        "## 资料概览",
        "## 终点：进组前应接近什么状态",
        "## 进组前最小闭环",
        "## 第一段路：先知道光电子谱到底在看什么",
        "## 第二段路：从静态谱走到时间分辨",
        "## 第三段路：从飞秒过程走到阿秒电子运动",
        "## 第四段路：从气相分子走到液相和凝聚相",
        "## 第五段路：从读机制论文走到理解平台论文",
        "## 回到张鹏举论文路线",
        "## 进组后先从哪里接上",
        "## 卡住时怎么判断该补什么",
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

FORBIDDEN_STYLE = [
    "运行信息",
    "论文路线总表",
    "语言层",
    "图像层",
    "方法层",
    "训练营",
    "刷课",
    "炫技",
    "给阶段三",
    "阶段三应",
    "阶段四应",
    "阶段三只",
    "阶段四可",
]

SOURCE_RE = re.compile(r"https?://|\[未找到\]|需人工复核")
CITATION_RE = re.compile(r"\[(O|P|R|B)(\d+)\]")
LINKED_CITATION_RE = re.compile(
    r"<sup><a href=\"#([oprb]\d+)\">\[((O|P|R|B)(\d+))\]</a></sup>"
)
SOURCE_ANCHOR_RE = re.compile(r"<a id=\"([oprb]\d+)\"></a>\[((O|P|R|B)(\d+))\]")
BARE_URL_RE = re.compile(r"(?<!\]\()https?://[^\s)]+")
SOURCE_SECTION_MARKER = "## 参考文献与资料"
SOURCE_TABLE_HEADER = "| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |"
PHASE4_MINIMAL_LOOP_HEADING = "## 进组前最小闭环"
PHASE4_MINIMAL_LOOP_REQUIRED = ("论文", "图", "平台")
FIXED_DAY_RE = re.compile(
    r"第\s*[0-9０-９一二三四五六七八九十百两]+\s*天"
    r"|[0-9０-９]+\s*天(?:路线|计划|安排|训练|打卡|任务|课程)?"
)


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


def _extract_linked_body_citations(text: str) -> dict[str, str]:
    return {f"[{kind}{number}]": target for target, _, kind, number in LINKED_CITATION_RE.findall(text)}


def _extract_source_anchors(text: str) -> dict[str, str]:
    return {f"[{kind}{number}]": anchor for anchor, _, kind, number in SOURCE_ANCHOR_RE.findall(text)}


def _split_sources_section(text: str) -> tuple[str, str]:
    if SOURCE_SECTION_MARKER not in text:
        return text, ""
    body, sources = text.split(SOURCE_SECTION_MARKER, 1)
    return body, sources


def _extract_markdown_section(text: str, heading: str) -> str:
    marker = f"{heading}\n"
    start = text.find(marker)
    if start < 0:
        return ""
    section_start = start + len(marker)
    next_heading = text.find("\n## ", section_start)
    return text[section_start:] if next_heading < 0 else text[section_start:next_heading]


def _check_source_format(filename: str, text: str, messages: list[str]) -> None:
    if filename == "01_基础画像.md":
        return

    body, sources = _split_sources_section(text)
    if not sources:
        messages.append(f"[FAIL] {filename} 缺少章节: {SOURCE_SECTION_MARKER}")
        return

    if "\n## " in sources:
        messages.append(f"[FAIL] {filename} 参考文献与资料必须是最后一个二级章节")

    if BARE_URL_RE.search(body):
        messages.append(f"[FAIL] {filename} 正文含裸 URL")

    if SOURCE_TABLE_HEADER not in sources:
        messages.append(f"[FAIL] {filename} 参考文献表缺少五列表头: {SOURCE_TABLE_HEADER}")

    body_keys = _extract_citation_keys(body)
    linked_body_keys = _extract_linked_body_citations(body)
    plain_body_keys = sorted(body_keys - set(linked_body_keys))
    for key in plain_body_keys:
        messages.append(f"[FAIL] {filename} 正文引用键必须使用上标链接: {key}")

    for key, target in sorted(linked_body_keys.items()):
        expected_target = key.strip("[]").lower()
        if target != expected_target:
            messages.append(f"[FAIL] {filename} 正文引用键锚点不匹配: {key} -> #{target}")

    source_keys = _extract_citation_keys(sources)
    anchored_source_keys = _extract_source_anchors(sources)
    unanchored_source_keys = sorted(source_keys - set(anchored_source_keys))
    for key in unanchored_source_keys:
        messages.append(f"[FAIL] {filename} 参考文献表引用键缺少锚点: {key}")

    for key, anchor in sorted(anchored_source_keys.items()):
        expected_anchor = key.strip("[]").lower()
        if anchor != expected_anchor:
            messages.append(f"[FAIL] {filename} 参考文献表引用键锚点不匹配: {key} -> #{anchor}")

    missing = sorted(set(linked_body_keys) - set(anchored_source_keys))
    for key in missing:
        messages.append(f"[FAIL] {filename} 引用键未在参考文献表中定义: {key}")

    unused = sorted(set(anchored_source_keys) - set(linked_body_keys))
    for key in unused:
        messages.append(f"[WARN] {filename} 参考文献表引用键未在正文使用: {key}")


def _check_phase4_minimal_loop(filename: str, text: str, messages: list[str]) -> None:
    if filename != "04_学习向导.md" or PHASE4_MINIMAL_LOOP_HEADING not in text:
        return
    section = _extract_markdown_section(text, PHASE4_MINIMAL_LOOP_HEADING)
    if not all(token in section for token in PHASE4_MINIMAL_LOOP_REQUIRED):
        messages.append(
            "[FAIL] 04_学习向导.md 进组前最小闭环必须同时连接论文、核心图和平台链路"
        )


def _check_forbidden_terms(filename: str, text: str, messages: list[str]) -> None:
    for word in FORBIDDEN:
        if word in text:
            messages.append(f"[FAIL] {filename} 含禁用评价语: {word}")


def _check_forbidden_style(filename: str, text: str, messages: list[str]) -> None:
    for word in FORBIDDEN_STYLE:
        if word in text:
            messages.append(f"[FAIL] {filename} 含禁用写作风格: {word}")

    for match in FIXED_DAY_RE.finditer(text):
        messages.append(f"[FAIL] {filename} 含固定天数学习安排: {match.group(0)}")


def _check_optional_markdown_docs(prof: Path, messages: list[str]) -> None:
    for path in sorted(prof.glob("*.md")):
        if path.name in DOCS:
            continue
        text = path.read_text(encoding="utf-8")
        _check_forbidden_terms(path.name, text, messages)
        _check_forbidden_style(path.name, text, messages)


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
        _check_phase4_minimal_loop(filename, text, messages)
        _check_forbidden_terms(filename, text, messages)
        _check_forbidden_style(filename, text, messages)

    _check_optional_markdown_docs(prof, messages)

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
