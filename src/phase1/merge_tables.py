#!/usr/bin/env python3
"""
merge_tables.py — 将草稿中的完整论文表格合并到 AI 润色版画像。

解决矛盾：
  AI 润色写叙事 → 但会毁表格
  脚本生成表格 → 但没叙事

用法：
  python src/phase1/merge_tables.py 01_基础画像.md _internal/archive/<ts>/01_基础画像_draft.md -o 01_基础画像.md

算法：
  1. 读取 AI 润色版（含叙事）和草稿版（含完整表格）
  2. 对每个 ### 4.x 阶段：
     - 在润色版中保留该阶段的叙事段落
     - 用草稿版的论文表格替换润色版中的表格
  3. 输出合并版
"""

import argparse
import logging
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("merge_tables")


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_section(content: str, section_header: str) -> dict:
    """提取某个 ## 节的内容。返回 {header_line, body, end}。"""
    pattern = rf"^({re.escape(section_header)})\n(.*?)(?=\n## |\Z)"
    m = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not m:
        return {}
    return {"header": m.group(1), "body": m.group(2), "full": m.group(0) + "\n"}


def extract_tables(stage_section: str) -> str:
    """从 ### 4.x 节中提取论文表格部分（从 | # | 行到下一个 ### 或末尾）。"""
    # 找 | # | 开头的第一行（表格头）到该节末尾或下一个 ###
    m = re.search(r"^(\| # \|.*?)(?=\n### |\Z)", stage_section, re.MULTILINE | re.DOTALL)
    if m:
        return m.group(1)
    return ""


def extract_narrative(stage_section: str) -> str:
    """从 ### 4.x 节中提取表格之前的内容（标题、叙事、说明）。"""
    m = re.search(r"^(.*?)(?=^\| # \|)", stage_section, re.MULTILINE | re.DOTALL)
    if m:
        return m.group(1)
    return stage_section


def parse_stages(content: str) -> list:
    """解析所有 ### 4.x 阶段。返回 [(header, narrative, tables, full_text)]"""
    stages = []
    pattern = r"^(### 4\.\d+ .*?)(?=\n### 4\.\d+|\n## |\Z)"
    for m in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        section = m.group(0)
        narrative = extract_narrative(section)
        tables = extract_tables(section)
        stages.append({
            "header": re.match(r"^### 4\.\d+ .+", section).group(0) if re.match(r"^### 4\.\d+ .+", section) else "",
            "narrative": narrative,
            "tables": tables,
            "full": section,
        })
    return stages


def merge(enriched_path: str, draft_path: str, output_path: str) -> None:
    enriched = read_file(enriched_path)
    draft = read_file(draft_path)

    # 提取完整 ### 4.x 节（含叙事和表格），按节序号索引 (4.1, 4.2...)
    enriched_stages = {}
    for s in parse_stages(enriched):
        m = re.match(r"^### (4\.\d+)", s["header"])
        if m:
            enriched_stages[m.group(1)] = s

    draft_stages = {}
    for s in parse_stages(draft):
        m = re.match(r"^### (4\.\d+)", s["header"])
        if m:
            draft_stages[m.group(1)] = s

    replacements = 0
    for idx, draft_s in draft_stages.items():
        if idx in enriched_stages:
            enriched_s = enriched_stages[idx]
            # 保留 AI 的叙事，替换表格
            new_section = enriched_s["narrative"].rstrip() + "\n\n" + draft_s["tables"]
            enriched = enriched.replace(enriched_s["full"], new_section)
            replacements += 1
            logger.info(f"Replaced tables in §{idx}: {draft_s['header'][:60]}")
        else:
            logger.info(f"Appending missing §{idx}: {draft_s['header'][:60]}")
            enriched = enriched.replace("## 5.", draft_s["full"] + "\n\n## 5.", 1)
            replacements += 1
            enriched = enriched.replace("## 5.", draft_s["full"] + "\n\n## 5.", 1)
            replacements += 1

    if replacements == 0:
        logger.warning("No stage sections found to replace. Check file formats.")
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(enriched)
        logger.info(f"Done. {replacements} sections processed → {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="合并草稿的论文表格到 AI 润色版")
    parser.add_argument("enriched", help="AI 润色后的画像（含叙事，表格可能不全）")
    parser.add_argument("draft", help="脚本生成的草稿画像（含完整表格）")
    parser.add_argument("--output", "-o", default="01_基础画像_merged.md", help="输出路径")
    args = parser.parse_args()

    merge(args.enriched, args.draft, args.output)


if __name__ == "__main__":
    main()
