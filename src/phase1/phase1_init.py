#!/usr/bin/env python3
"""
phase1_init.py — Phase 1 初始化：建目录 + 写 _internal/latest.txt + 输出路径。

AI 不要手动 mkdir。用此脚本自动创建标准目录结构。

用法：
  python src/phase1/phase1_init.py \
    --university 中国科学院大学 \
    --institute 中科院物理研究所 \
    --department 超快物质科学中心 \
    --name 王示例 \
    --official-url "https://..."

输出：
  1. 创建 output/<大学>/<学院所>/<部门>/<姓名>/ 目录
  2. 创建 _internal/archive/<timestamp>/ 目录
  3. 写 _internal/latest.txt
  4. 写 _internal/seed.json 记录最小输入
  5. 打印 prof_dir 路径供后续 --prof-dir 步骤使用
"""

import argparse
import json
import os
import sys
from datetime import datetime


INSTITUTE_ALIASES = {
    "中科院物理所": "中科院物理研究所",
}


def canonicalize_institute(institute: str) -> str:
    value = (institute or "").strip()
    return INSTITUTE_ALIASES.get(value, value)


def build_prof_path(university: str, institute: str, department: str, name: str) -> str:
    """构造标准输出路径。

    规则：output/<大学>/<学院所>/<部门>/<姓名>/
    """
    parts = [
        (university or "").strip(),
        canonicalize_institute(institute),
        (department or "").strip(),
        (name or "").strip(),
    ]
    parts = [p for p in parts if p]
    return "/".join(parts)


def require_http_url(value: str) -> str:
    value = (value or "").strip()
    if not value.startswith(("http://", "https://")):
        raise argparse.ArgumentTypeError("--official-url must be an HTTP(S) URL")
    return value


def main():
    parser = argparse.ArgumentParser(description="Phase 1 初始化：建目录")
    parser.add_argument("--university", required=True, help="大学（如 中国科学院大学）")
    parser.add_argument("--institute", default="", help="学院/研究所（如 中科院物理研究所）")
    parser.add_argument("--department", default="", help="部门（如 超快物质科学中心）")
    parser.add_argument("--name", required=True, help="学者姓名（如 王示例）")
    parser.add_argument("--official-url", required=True, type=require_http_url, help="导师官网 URL")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    institute = canonicalize_institute(args.institute)
    prof_path = build_prof_path(args.university, institute,
                                args.department, args.name)
    base = f"output/{prof_path}"
    internal = f"{base}/_internal"
    archive = f"{internal}/archive/{ts}"

    os.makedirs(archive, exist_ok=True)
    with open(f"{internal}/latest.txt", "w", encoding="utf-8") as f:
        f.write(f"{ts}\n")
    seed = {
        "name": args.name,
        "university": args.university,
        "institute": institute,
        "department": args.department,
        "official_url": args.official_url,
        "created_at": ts,
    }
    with open(f"{internal}/seed.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"prof_dir: {base}", file=sys.stderr)
    print(f"archive_dir: {archive}", file=sys.stderr)
    print(base)  # 主输出：prof_dir 路径，供 --prof-dir 使用

    return 0


if __name__ == "__main__":
    sys.exit(main())
