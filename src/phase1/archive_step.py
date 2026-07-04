#!/usr/bin/env python3
"""
archive_step.py — step 输出自动副作用归档。

每个 step 完成后调用一次，把产物拷贝到 _internal/archive/<ts>/。
AI 不需要记得做这件事——直接挂在 step 末尾。

用法：
  python archive_step.py --prof-dir output/.../姓名 --source 01_gs.json
  python archive_step.py --prof-dir output/.../姓名 --source 04_merged.json
  python archive_step.py --prof-dir output/.../姓名 --source 01_基础画像.md

副作用：
  - 读 _internal/latest.txt 拿当前 ts
  - 把 <prof_dir>/<filename> 拷贝到 <prof_dir>/_internal/archive/<ts>/<filename>
  - 不存在则跳过（不报错）
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ProfDirResolver


def archive_one(prof_dir: str, source: str) -> bool:
    """把 prof_dir/source 拷贝到 prof_dir/_internal/archive/<ts>/source。

    返回 True 表示成功，False 表示源文件不存在（不算错）。
    """
    src = os.path.join(prof_dir, source)
    if not os.path.exists(src):
        return False
    resolver = ProfDirResolver(prof_dir)
    dst = os.path.join(resolver.archive_dir, source)
    if not resolver.archive_dir:
        print(f"  [archive] {prof_dir} 下没有 _internal/latest.txt，跳过", file=sys.stderr)
        return False
    os.makedirs(resolver.archive_dir, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  [archive] {source} → {resolver.archive_dir}/", file=sys.stderr)
    return True


def main():
    parser = argparse.ArgumentParser(description="step 输出自动归档")
    parser.add_argument("--prof-dir", required=True, help="prof 根目录")
    parser.add_argument("--source", action="append", required=True,
                        help="要归档的文件名（相对 prof_dir，可多次传）")
    args = parser.parse_args()

    for s in args.source:
        archive_one(args.prof_dir, s)


if __name__ == "__main__":
    main()
