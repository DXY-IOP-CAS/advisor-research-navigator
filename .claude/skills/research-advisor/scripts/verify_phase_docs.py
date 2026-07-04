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
    "00_材料导读.md": [
        "## 这套材料解决什么问题",
        "## 建议阅读顺序",
        "## 如何阅读引用和证据标记",
        "## 起步讨论入口",
        "## 文件定位",
        "## 使用边界",
    ],
    "01_基础画像.md": ["## 资料概览"],
    "02_领域地图.md": [
        "## 资料概览",
        "## 导师路径速览",
        "## 当前方向学科定位",
        "## 领域怎样发展到当前问题",
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
        "## 从论文路线倒推出的学习准备",
    ],
    "04_学习向导.md": [
        "## 资料概览",
        "## 终点：进组前应接近什么状态",
        "## 进组前起步闭环",
        "## 回到<导师>论文路线",
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
    "领域发展树",
    "给学习向导",
    "语言层",
    "图像层",
    "方法层",
    "训练营",
    "刷课",
    "炫技",
    "给阶段三",
    "阶段 2-4",
    "阶段2-4",
    "自动论文表",
    "关键论文",
    "阶段三应",
    "阶段四应",
    "阶段三只",
    "阶段四可",
    "证明学生",
    "最小可交付",
    "最小闭环",
    "告诉你",
    "告诉我们",
    "我现在缺的是",
    "下面的路线图",
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
EVIDENCE_TABLE_HEADER = "| 文档位置 | 关键判断 | 来源 | 来源支撑了什么 | 证据强度 | 人工复核 |"
BLUEPRINT_REQUIRED_FIELDS = [
    ("读者起点", re.compile(r"读者起点")),
    ("导师当前方向一句话", re.compile(r"导师当前方向一句话|当前方向一句话")),
    ("目标论文", re.compile(r"目标论文")),
    ("核心图", re.compile(r"核心图|图组")),
    ("平台链路", re.compile(r"平台链路")),
    ("课程到论文的学习桥", re.compile(r"课程到论文|学习桥")),
    ("证据风险", re.compile(r"证据风险|人工复核|需人工复核")),
    ("可视化计划", re.compile(r"可视化计划")),
]
PHASE4_MINIMAL_LOOP_HEADING = "## 进组前起步闭环"
PHASE4_MINIMAL_LOOP_REQUIRED = ("论文", "图", "平台")
PHASE4_LEARNING_PATH_MIN_SECTIONS = 3
PHASE0_READING_ORDER_HEADING = "## 建议阅读顺序"
PHASE0_READING_ORDER_DOCS = (
    "01_基础画像.md",
    "02_领域地图.md",
    "03_论文路线.md",
    "04_学习向导.md",
)
PHASE4_CONCRETE_FIGURE_RE = re.compile(
    r"(?:Fig(?:ure)?\.?\s*[0-9]+[a-z]?)|(?:图\s*[0-9０-９一二三四五六七八九十]+)"
)
FIXED_DAY_RE = re.compile(
    r"第\s*[0-9０-９一二三四五六七八九十百两]+\s*天"
    r"|[0-9０-９]+\s*天(?:路线|计划|安排|训练|打卡|任务|课程)?"
)
VISIBLE_TAXONOMY_RE = re.compile(r"(?:主线[一二三四五六七八九十]+[:：]|第[一二三四五六七八九十]+类是)")
NUMBERED_PHASE4_PATH_RE = re.compile(r"第[一二三四五六七八九十]+段路")
PHASE4_ROUTE_HEADING_RE = re.compile(r"^## 回到.+论文路线\s*$", re.MULTILINE)
ALLOWED_ROOT_ENTRIES = set(DOCS) | {"_internal"}
MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", re.DOTALL)
MERMAID_START_RE = re.compile(
    r"^(?:flowchart|graph|sequenceDiagram|timeline|mindmap|quadrantChart|journey|gantt|classDiagram|"
    r"stateDiagram|erDiagram|pie|gitGraph|xychart-beta|block-beta|architecture-beta|packet-beta|"
    r"sankey-beta|venn|treemap|kanban|radar|requirementDiagram)\b"
)
MARKDOWN_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
TEXT_VISUAL_BLOCK_RE = re.compile(r"```(?:text|txt)\s*\n(.*?)\n```", re.DOTALL)
TEXT_VISUAL_MARKERS = ("->", "→", "├", "└", "│")
ORDINARY_PARAGRAPH_MAX_CHARS = 420
PARAGRAPH_BOUNDARY_RE = re.compile(
    r"^\s*(?:#{1,6}\s|[-*+]\s+|\d+[.)]\s+|>\s*|<!--|</?\w|---\s*$)"
)
TITLE_IDENTITY_RE = re.compile(r"^#\s+.+\s+\([^)]+\)")


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


def _has_visible_frontmatter(text: str) -> bool:
    return text.lstrip("\ufeff").startswith("---\n")


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


def _has_required_section(filename: str, section: str, text: str) -> bool:
    if filename == "04_学习向导.md" and section == "## 回到<导师>论文路线":
        return bool(PHASE4_ROUTE_HEADING_RE.search(text))
    return section in text


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
            "[FAIL] 04_学习向导.md 进组前起步闭环必须同时连接论文、核心图和平台链路"
        )
    if not PHASE4_CONCRETE_FIGURE_RE.search(section):
        messages.append("[FAIL] 04_学习向导.md 进组前起步闭环必须具体到核心图编号或图组")


def _extract_h2_headings(text: str) -> list[str]:
    return [match.group(0).strip() for match in re.finditer(r"^## [^\n]+$", text, re.MULTILINE)]


def _check_phase4_learning_path_sections(filename: str, text: str, messages: list[str]) -> None:
    if filename != "04_学习向导.md":
        return

    headings = _extract_h2_headings(text)
    try:
        start_index = headings.index(PHASE4_MINIMAL_LOOP_HEADING)
    except ValueError:
        return

    route_index = None
    for index, heading in enumerate(headings[start_index + 1 :], start=start_index + 1):
        if PHASE4_ROUTE_HEADING_RE.match(heading):
            route_index = index
            break
    if route_index is None:
        return

    learning_path_headings = headings[start_index + 1 : route_index]
    if len(learning_path_headings) < PHASE4_LEARNING_PATH_MIN_SECTIONS:
        messages.append(
            "[FAIL] 04_学习向导.md 进组前起步闭环和回到论文路线之间至少需要 3 个方向适配的学习路径章节"
        )


def _check_phase0_reading_order(filename: str, text: str, messages: list[str]) -> None:
    if filename != "00_材料导读.md" or PHASE0_READING_ORDER_HEADING not in text:
        return

    section = _extract_markdown_section(text, PHASE0_READING_ORDER_HEADING)
    before_table = section.split("\n|", 1)[0]
    has_all_docs_in_explanation = all(doc in before_table for doc in PHASE0_READING_ORDER_DOCS)
    has_first_pass = any(token in before_table for token in ("第一遍", "第一次", "先粗读", "粗读"))
    has_final_revisit = any(token in before_table for token in ("最后", "回看", "回读"))

    if not (has_all_docs_in_explanation and has_first_pass and has_final_revisit):
        messages.append("[FAIL] 00_材料导读.md 建议阅读顺序缺少分步文字解释")

    if not _has_markdown_table(section):
        messages.append("[FAIL] 00_材料导读.md 建议阅读顺序缺少阅读顺序表")


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

    for match in VISIBLE_TAXONOMY_RE.finditer(text):
        messages.append(f"[FAIL] {filename} 含外显分类写法: {match.group(0)}")

    for match in NUMBERED_PHASE4_PATH_RE.finditer(text):
        messages.append(f"[FAIL] {filename} 含编号式学习路径标题: {match.group(0)}")


def _check_optional_markdown_docs(prof: Path, messages: list[str]) -> None:
    for path in sorted(prof.glob("*.md")):
        if path.name in DOCS:
            continue
        text = path.read_text(encoding="utf-8")
        if SOURCE_SECTION_MARKER in text:
            _check_source_format(path.name, text, messages)
        _check_forbidden_terms(path.name, text, messages)
        _check_forbidden_style(path.name, text, messages)


def _check_prof_root_cleanliness(prof: Path, messages: list[str]) -> None:
    if not prof.exists():
        return
    for child in sorted(prof.iterdir(), key=lambda p: p.name):
        if child.name in ALLOWED_ROOT_ENTRIES:
            continue
        messages.append(f"[FAIL] 导师根目录不得包含机器文件或目录: {child.name}")


def _check_title_identity_format(filename: str, body: str, messages: list[str]) -> None:
    first_line = body.splitlines()[0] if body.splitlines() else ""
    if first_line.startswith("# ") and not TITLE_IDENTITY_RE.match(first_line):
        messages.append(f"[FAIL] {filename} 一级标题姓名格式应为: 中文名 (English Name)")


def _has_markdown_table(text: str) -> bool:
    lines = text.splitlines()
    for index, line in enumerate(lines[:-2]):
        if "|" not in line:
            continue
        if not MARKDOWN_TABLE_SEPARATOR_RE.match(lines[index + 1]):
            continue
        if "|" not in lines[index + 2]:
            continue
        return True
    return False


def _has_text_visual_block(text: str) -> bool:
    for match in TEXT_VISUAL_BLOCK_RE.finditer(text):
        block = match.group(1)
        nonempty_lines = [line for line in block.splitlines() if line.strip()]
        if len(nonempty_lines) >= 3 and any(marker in block for marker in TEXT_VISUAL_MARKERS):
            return True
    return False


def _check_visualization_construct(filename: str, text: str, messages: list[str]) -> None:
    body, _sources = _split_sources_section(text)
    blocks = MERMAID_BLOCK_RE.findall(text)
    has_valid_mermaid = False
    has_invalid_mermaid = False
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if lines and MERMAID_START_RE.match(lines[0]):
            has_valid_mermaid = True
        else:
            has_invalid_mermaid = True

    if has_invalid_mermaid:
        messages.append(f"[FAIL] {filename} Mermaid 代码块缺少可识别图类型")
        return

    if has_valid_mermaid or _has_markdown_table(body) or _has_text_visual_block(body):
        return

    messages.append(f"[FAIL] {filename} 缺少可视化理解构件：Mermaid、正文表格/矩阵或文本层级树")


def _is_markdown_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") or MARKDOWN_TABLE_SEPARATOR_RE.match(stripped) is not None


def _visible_text_length(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def _check_paragraph_density(filename: str, text: str, messages: list[str]) -> None:
    body, _sources = _split_sources_section(_body_after_frontmatter(text))
    paragraph_lines: list[str] = []
    paragraph_start = 0
    in_code_block = False

    def flush() -> None:
        nonlocal paragraph_lines, paragraph_start
        if not paragraph_lines:
            return
        paragraph = " ".join(line.strip() for line in paragraph_lines)
        length = _visible_text_length(paragraph)
        if length > ORDINARY_PARAGRAPH_MAX_CHARS:
            messages.append(
                f"[FAIL] {filename} 普通正文段落过长: 第 {paragraph_start} 行约 {length} 字，"
                "建议拆成短段、表格、矩阵、层级树或必要 Mermaid"
            )
        paragraph_lines = []
        paragraph_start = 0

    for line_number, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if (
            not stripped
            or PARAGRAPH_BOUNDARY_RE.match(stripped)
            or _is_markdown_table_line(stripped)
        ):
            flush()
            continue
        if not paragraph_lines:
            paragraph_start = line_number
        paragraph_lines.append(line)

    flush()


def _check_evidence_tables(prof: Path, messages: list[str]) -> None:
    evidence_dir = prof / "_internal" / "evidence"
    if not evidence_dir.is_dir():
        messages.append("[FAIL] 缺少 _internal/evidence/ 关键判断证据核对表")
        return

    files = sorted(evidence_dir.glob("*.md"))
    if not files:
        messages.append("[FAIL] 缺少 _internal/evidence/ 关键判断证据核对表")
        return

    for path in files:
        text = path.read_text(encoding="utf-8")
        if EVIDENCE_TABLE_HEADER not in text:
            messages.append(f"[FAIL] _internal/evidence/{path.name} 缺少关键判断证据表头")


def _check_cognitive_blueprint(prof: Path, messages: list[str]) -> None:
    blueprint = prof / "_internal" / "blueprint.md"
    if not blueprint.is_file():
        messages.append("[FAIL] 缺少 _internal/blueprint.md 认知蓝图")
        return

    text = blueprint.read_text(encoding="utf-8")
    for label, pattern in BLUEPRINT_REQUIRED_FIELDS:
        if not pattern.search(text):
            messages.append(f"[FAIL] _internal/blueprint.md 缺少认知蓝图字段: {label}")


def verify_prof_dir(prof_dir: str | Path) -> VerifyResult:
    prof = Path(prof_dir)
    messages: list[str] = []

    _check_prof_root_cleanliness(prof, messages)
    _check_cognitive_blueprint(prof, messages)
    _check_evidence_tables(prof, messages)

    for filename, sections in DOCS.items():
        path = prof / filename
        if not path.exists():
            messages.append(f"[FAIL] 缺少文件: {filename}")
            continue

        text = path.read_text(encoding="utf-8")
        body = _body_after_frontmatter(text)
        if _has_visible_frontmatter(text):
            messages.append(f"[FAIL] {filename} 不使用裸露 frontmatter")
        if not body.startswith("# "):
            messages.append(f"[FAIL] {filename} 缺少一级标题")
        else:
            _check_title_identity_format(filename, body, messages)

        for section in sections:
            if not _has_required_section(filename, section, text):
                messages.append(f"[FAIL] {filename} 缺少章节: {section}")

        if not _has_source_marker(text):
            messages.append(f"[FAIL] {filename} 缺少来源 URL、[未找到] 或需人工复核标记")

        _check_source_format(filename, text, messages)
        _check_visualization_construct(filename, text, messages)
        _check_paragraph_density(filename, text, messages)
        _check_phase0_reading_order(filename, text, messages)
        _check_phase4_minimal_loop(filename, text, messages)
        _check_phase4_learning_path_sections(filename, text, messages)
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
