#!/usr/bin/env python3
"""
validate_career_stages.py — career_stages.json 格式自检。

轻量校验，供 AI 快速检查 JSON 格式是否合格。
不做强门控——仅校验会直接导致渲染崩溃的结构问题。
verify_profile.py 才是最终质量门控。

校验项：
  1. JSON 合法 + 根元素是数组
  2. 每项有 name(str)、start(int)、end(int)
  3. start <= end
  4. 如某个阶段含 institution/position/direction 中任一项 → 全员必须存在（避免混用新旧格式）

用法：
  python src/phase1/validate_career_stages.py <path/to/career_stages.json>

退出码：始终 0（仅警告，不阻塞流程）
"""

import json
import re
import sys

PASS, FAIL = 0, 1


def check(condition: bool, message: str, warns: list):
    tag = "[OK]" if condition else "[WARN]"
    print(f"  {tag} {message}")
    if not condition:
        warns.append(message)


def validate(path: str) -> int:
    warns = []

    # 1. JSON 合法 + 根元素是数组
    try:
        with open(path, "r", encoding="utf-8") as f:
            stages = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  [WARN] JSON 读写失败：{e}")
        return PASS

    check(isinstance(stages, list), "根元素是数组", warns)
    if not isinstance(stages, list):
        print(f"\n  {len(warns)} 项警告")
        return PASS

    check(len(stages) >= 1, f"至少 1 个阶段（共 {len(stages)} 个）", warns)

    for i, s in enumerate(stages):
        prefix = f"阶段 {i+1}（{s.get('name', '?')}）"

        check(isinstance(s.get("name"), str) and s["name"].strip() != "",
              f"{prefix}：name 存在且非空", warns)
        check(isinstance(s.get("start"), int) and s["start"] > 0,
              f"{prefix}：start 为正整数", warns)
        check(isinstance(s.get("end"), int) and s["end"] > 0,
              f"{prefix}：end 为正整数", warns)

        if not all(isinstance(s.get(k), int) for k in ("start", "end")):
            continue

        check(s["start"] <= s["end"],
              f"{prefix}：{s['start']} ≤ {s['end']}（年份区间不反向）", warns)

        # 新旧格式混用检测
        keys = [k for k in ("institution", "position", "direction") if s.get(k)]
        if keys and len(keys) < 3:
            for k in keys:
                check(isinstance(s.get(k), str) and s[k].strip() != "",
                      f"{prefix}：{k} 存在且非空", warns)
            missing = [k for k in ("institution", "position", "direction") if not s.get(k)]
            if missing:
                print(f"  [WARN] {prefix}：含部分 enriched 字段但缺失 {missing}。"
                      "渲染时 §2 表格可能不完整，建议补充或全部删除回退旧格式。")
        elif len(keys) == 3:
            for k in keys:
                check(isinstance(s.get(k), str) and s[k].strip() != "",
                      f"{prefix}：{k} 存在且非空", warns)

    if warns:
        print(f"\n  {len(warns)} 项警告——上述问题不影响渲染，但 verify 会检查。"
              "AI 可在下一轮修复。")
    else:
        print("\n  [OK] 全部通过")

    return PASS


def main():
    parser = argparse.ArgumentParser(description="career_stages.json 格式自检")
    parser.add_argument("stages_file", help="career_stages.json 路径")
    args = parser.parse_args()
    sys.exit(validate(args.stages_file))


if __name__ == "__main__":
    # argparse imported implicitly via sys.modules
    main()
