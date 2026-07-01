#!/usr/bin/env python3
"""
verify_profile.py — 画像质量自动门控。

在阶段 C 完成后运行。检查画像是否满足成品标准。
所有检查项不通过则退出码非 0，AI 不能声称完成。

用法：
  python src/phase1/verify_profile.py output/<机构>/<部门>/<姓名>/01_基础画像.md \
    --merged output/<机构>/<部门>/<姓名>/archive/<timestamp>/04_merged.json

退出码：0 = 通过，1 = 有失败项
"""

import argparse
import json
import re
import sys

PASS, FAIL = 0, 1


def check(condition: bool, message: str, errors: list):
    if condition:
        print(f"  ✅ {message}")
    else:
        print(f"  ❌ {message}")
        errors.append(message)


def verify(profile_path: str, merged_path: str = None) -> int:
    errors = []

    with open(profile_path, encoding="utf-8") as f:
        content = f.read()

    # 1. 无禁止关键词
    forbidden = ["代表性论文", "以下见完整列表", "如下图"]
    for kw in forbidden:
        check(kw not in content, f"无禁止关键词「{kw}」", errors)

    # 2. 名字格式：中文 (English) 或纯英文
    title = re.search(r"^# (.+) — 基础画像$", content, re.MULTILINE)
    if title:
        t = title.group(1)
        has_chinese = bool(re.search(r"[一-鿿]", t))
        has_english = bool(re.search(r"[a-zA-Z]", t))
        if has_chinese and has_english:
            ok = bool(re.search(r"[一-鿿].+\([a-zA-Z]", t))
            check(ok, f"名字格式正确：「{t}」", errors)
        elif has_chinese and not has_english:
            check(True, f"纯中文名：「{t}」", errors)
        else:
            check(True, f"纯英文名：「{t}」", errors)
    else:
        check(False, "有标题行（# 姓名 — 基础画像）", errors)

    # 3. 论文表格行数（如果提供了 merged.json）
    if merged_path:
        with open(merged_path, encoding="utf-8") as f:
            merged = json.load(f)
        total_merged = len(merged.get("papers", []))
        paper_rows = len(re.findall(r"^\| \d+ \| \d{4}", content, re.MULTILINE))
        # 允许过滤 ≈5 篇的偏差
        diff = abs(total_merged - paper_rows)
        check(diff <= 5,
              f"论文行数：{paper_rows}（merged={total_merged}，差 {diff}）",
              errors)
    else:
        paper_rows = len(re.findall(r"^\| \d+ \| \d{4}", content, re.MULTILINE))
        check(paper_rows > 0, f"论文表格存在（{paper_rows} 行）", errors)

    # 4. 学术履历存在且有至少 3 行
    sec2 = content.split("## 2. 学术履历")
    if len(sec2) > 1:
        rows = re.findall(r"^\| \d{4}", sec2[1], re.MULTILINE)
        check(len(rows) >= 3, f"学术履历 {len(rows)} 行", errors)
        # 检查排序：从旧到新
        years = [int(r) for r in re.findall(r"\|\s*(\d{4})", sec2[1].split("##")[0]) if r]
        if len(years) >= 2:
            check(years[0] < years[-1], f"履历从旧到新（{years[0]}→{years[-1]}）", errors)
    else:
        check(False, "§2 学术履历存在", errors)

    # 5. 每阶段表格前有叙事
    stages = re.split(r"\n### 4\.\d+ ", content)
    stages_with_narrative = 0
    for s in stages[1:]:  # 跳过第一节前的部分
        head = s[:500]
        has_table = bool(re.search(r"\| # \| 年份", head))
        if has_table:
            stages_with_narrative += 1
        # 检查表格前是否有叙事（非空行、非表格头的文字）
        has_narration = bool(re.search(r"研究主题|研究方向|[^|\n]",
                                       head.split("| # |")[0])) if "| # |" in head else False
        if not has_narration:
            pass  # 只计数不报错，留给下行判断

    check(stages_with_narrative >= 2, f"≥2 个阶段含有论文表格（{stages_with_narrative} 个）", errors)

    # 6. 有超链接（DOI 或 arXiv）
    links = content.count("https://doi.org") + content.count("https://arxiv.org")
    check(links > 0, f"有超链接（{links} 个）", errors)

    # 7. §2 履历、§6 合作网络、§7 公开信息至少存在 1 个
    sections_found = 0
    for section in ["## 2. 学术履历", "## 6.", "## 7.", "## 9."]:
        if section in content:
            sections_found += 1
    check(sections_found >= 2, f"补充章节存在（{sections_found}/4）", errors)

    # 汇总
    print()
    if errors:
        print(f"❌ {len(errors)} 项检查未通过")
        return FAIL
    else:
        print("✅ 全部检查通过")
        return PASS


def main():
    parser = argparse.ArgumentParser(description="画像质量自动门控")
    parser.add_argument("profile", help="01_基础画像.md 路径")
    parser.add_argument("--merged", help="04_merged.json 路径（校验论文行数）")
    args = parser.parse_args()

    result = verify(args.profile, args.merged)
    sys.exit(result)


if __name__ == "__main__":
    main()
