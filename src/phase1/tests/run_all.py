"""
tests/run_all.py — 一键跑所有阶段 1 测试

用法：
  python src/phase1/tests/run_all.py

退出码：0 = 全过，1 = 有失败。
"""

import sys
import subprocess
import os

TESTS = [
    "test_utils.py",
    "test_schema.py",
    "test_errors.py",
    "test_merge.py",
]

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    total_passed = total_failed = 0

    for t in TESTS:
        path = os.path.join(HERE, t)
        print(f"\n=== Running {t} ===")
        r = subprocess.run([sys.executable, path], env=env, capture_output=True, text=True)
        print(r.stdout.strip())
        if r.returncode != 0:
            print(f"STDERR: {r.stderr.strip()[:300]}")
        for line in r.stdout.split("\n"):
            if "passed," in line:
                parts = line.replace(",", "").split()
                try:
                    p, f = int(parts[0]), int(parts[2])
                    total_passed += p
                    total_failed += f
                except (ValueError, IndexError):
                    pass

    print(f"\n=== GRAND TOTAL: {total_passed} passed, {total_failed} failed ===")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())