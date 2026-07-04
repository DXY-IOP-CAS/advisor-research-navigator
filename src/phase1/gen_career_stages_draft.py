#!/usr/bin/env python3
"""
gen_career_stages_draft.py — 从 merged.json 论文年份生成 career_stages 空骨架。

输入：merged.json
输出：career_stages_draft.json — 仅含单阶段（[未填] 占位符）+ 论文年份范围。
使用 --prof-dir 时，默认写入 _internal/career_stages_draft.json，避免导师根目录暴露机器草稿。

为什么是这个设计：
  - 阶段边界需要官网履历（机构/职位变化），脚本无法可靠识别
  - 但论文年份范围是机械事实，脚本可算
  - AI 从官网读履历后，自己加阶段边界（Edit 即可）
  - 脚本的真正价值：消除 AI 拼写 start/end 数字的错误源

用法：
  python gen_career_stages_draft.py merged.json -o career_stages_draft.json
  python gen_career_stages_draft.py --prof-dir "output/..."   # 自动找 merged.json，默认写 _internal/

AI 工作流：
  1. 跑此脚本生成 draft.json（单阶段 + 年份范围）
  2. 用 Edit 在 stages 数组里加阶段行（机构/职位/方向从官网读）
  3. validate_career_stages.py 校验
  4. rename 为 career_stages.json
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ProfDirResolver


DRAFT_HINT = (
    "脚本从 merged.json 读论文年份范围 + 机构（来自 professor.affiliation）。"
    "AI 必须根据官网履历扩展 stages 数组：每一（时间+机构+职位）变化独立一段。"
    "完成后用 validate_career_stages.py 校验。"
)


def generate_draft(merged_path: str) -> list:
    """从 merged.json 读论文年份范围 + professor 字段，生成空骨架。

    返回顶层 list——与 render_profile.py / validate_career_stages.py 的
    schema 一致（两者都直接 `for s in stages` 遍历顶层数组，不认识
    {"stages": [...]} 的 dict 包裹格式，传 dict 会在 render 阶段崩溃）。
    """
    with open(merged_path, encoding="utf-8") as f:
        data = json.load(f)
    papers = data.get("papers", [])
    years = sorted([p["year"] for p in papers if p.get("year")])

    if years:
        start, end = years[0], years[-1]
    else:
        start, end = 0, 0

    prof = data.get("professor", {})
    return [
        {
            "name": "[未命名]",
            "start": start,
            "end": end,
            "institution": prof.get("affiliation", "[未填]"),
            "position": "[未填]",
            "direction": "[未填]",
        }
    ]


def main():
    parser = argparse.ArgumentParser(description="生成 career_stages 空骨架")
    parser.add_argument("merged_json", nargs="?", help="04_merged.json 路径")
    parser.add_argument("--prof-dir", help="prof 根目录（自动找 merged.json）")
    parser.add_argument("--output", "-o", default="career_stages_draft.json",
                        help="输出路径；使用 --prof-dir 且未显式传 -o 时默认写入 _internal/")
    args = parser.parse_args()

    if args.prof_dir and not args.merged_json:
        resolver = ProfDirResolver(args.prof_dir)
        merged = os.path.join(resolver.archive_dir, "04_merged.json") if resolver.archive_dir else ""
        if not merged or not os.path.exists(merged):
            parser.error(f"--prof-dir {args.prof_dir} 下找不到 04_merged.json")
        args.merged_json = merged
        if args.output == "career_stages_draft.json":  # 默认路径写到 _internal
            args.output = os.path.join(args.prof_dir, "_internal", "career_stages_draft.json")

    if not args.merged_json or not os.path.exists(args.merged_json):
        parser.error("找不到 merged.json。传位置参数或 --prof-dir")

    draft = generate_draft(args.merged_json)
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)

    s = draft[0]
    print(f"✅ [career_stages_draft] {s['start']}-{s['end']} ({s['institution']}) "
          f"→ {args.output}", file=sys.stderr)
    print(f"   {DRAFT_HINT}", file=sys.stderr)


if __name__ == "__main__":
    main()
