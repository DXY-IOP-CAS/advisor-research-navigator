#!/usr/bin/env python3
"""
archive_previous.py — 旧版整目录迁移工具。

规则：
  如果 output/<学校>/<学院>/<部门>/<姓名>/ 已存在
  → 整个目录移到 archive/旧版产出/<姓名>_<timestamp>/
  如果不存在 → 不操作

当前端到端主路径不调用本脚本；新运行默认通过 phase1_init.py
在同一导师目录下创建新的 _internal/archive/<timestamp>/ active state。
只有用户明确要求人工保留整份旧输出时，才使用本旧工具。

用法（旧版兼容）：
  python src/phase1/archive_previous.py "北京大学/物理学院/凝聚态物理与材料物理研究所/李新征"
  python src/phase1/archive_previous.py "中国科学院大学/中科院物理所/超快物质科学中心/王示例"
"""

import argparse
import os
import shutil
import sys
from datetime import datetime


def archive(professor_path: str) -> None:
    # 去掉 output/ 前缀（如果传了完整路径）
    if professor_path.startswith("output/"):
        professor_path = professor_path[7:]

    src = os.path.join("output", professor_path)
    if not os.path.isdir(src):
        print(f"  无需存档：{src} 不存在")
        return

    name = os.path.basename(professor_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join("archive", "旧版产出", f"{name}_{ts}")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    print(f"  已存档旧版：{src} → {dst}")


def main():
    parser = argparse.ArgumentParser(description="旧版整目录迁移工具（非当前主路径）")
    parser.add_argument("professor_path", help="output 下的老师路径（如 北京大学/物理学院/.../李新征）")
    args = parser.parse_args()
    archive(args.professor_path)


if __name__ == "__main__":
    main()
