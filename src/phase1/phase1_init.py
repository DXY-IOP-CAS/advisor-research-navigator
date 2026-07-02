#!/usr/bin/env python3
"""
phase1_init.py — Phase 1 初始化：建目录 + 写 latest.txt + 输出路径。

AI 不要手动 mkdir。用此脚本自动创建标准目录结构。

用法：
  python src/phase1/phase1_init.py \
    --university 中国科学院大学 \
    --institute 中科院物理所 \
    --department 超快物质科学中心 \
    --name 王示例

输出：
  1. 创建 output/<大学>/<学院所>/<部门>/<姓名>/ 目录
  2. 创建 archive/<timestamp>/ 目录
  3. 写 latest.txt
  4. 打印 archive 路径供后续步骤使用
"""

import argparse
import os
import sys
from datetime import datetime


def build_prof_path(university: str, institute: str, department: str, name: str) -> str:
    """构造标准输出路径。

    规则：output/<大学>/<学院所>/<部门>/<姓名>/
    """
    parts = [p for p in [university, institute, department, name] if p]
    return "/".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Phase 1 初始化：建目录")
    parser.add_argument("--university", required=True, help="大学（如 中国科学院大学）")
    parser.add_argument("--institute", default="", help="学院/研究所（如 中科院物理所）")
    parser.add_argument("--department", default="", help="部门（如 超快物质科学中心）")
    parser.add_argument("--name", required=True, help="学者姓名（如 王示例）")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    prof_path = build_prof_path(args.university, args.institute,
                                args.department, args.name)
    base = f"output/{prof_path}"
    archive = f"{base}/archive/{ts}"

    os.makedirs(archive, exist_ok=True)
    with open(f"{base}/latest.txt", "w", encoding="utf-8") as f:
        f.write(f"{ts}\n")

    print(f"prof_dir: {base}", file=sys.stderr)
    print(f"archive_dir: {archive}", file=sys.stderr)
    print(archive)  # 主输出：archive 路径，供 --archive-dir 使用

    return 0


if __name__ == "__main__":
    sys.exit(main())
