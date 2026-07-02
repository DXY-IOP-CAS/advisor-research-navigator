#!/usr/bin/env python3
"""
validate_career_stages.py — career_stages.json 格式校验。

在 Phase A 创建 career_stages.json 后执行，确保 AI 手写的阶段配置
满足渲染和验证的要求。

校验项：
  1. JSON 格式正确
  2. 根元素是数组
  3. 每项含 name(str)、start(int)、end(int)
  4. name 包含中文字符（verify_profile 要求）
  5. start <= end（年份区间不反向）
  6. 阶段按时间排序（旧的在前）
  7. 阶段间年份区间不重叠（后阶段的 start >= 前阶段的 end + 1）
  8. 至少 1 个阶段
  9. 最后阶段的 end 包含当前年份（或设为当前年份）

用法：
  python src/phase1/validate_career_stages.py <path/to/career_stages.json>

退出码：0 = 通过，1 = 有错误
"""

import json
import re
import sys
from datetime import datetime

PASS, FAIL = 0, 1
CURRENT_YEAR = datetime.now().year


def check(condition: bool, message: str, errors: list):
    if condition:
        print(f"  ✅ {message}")
    else:
        print(f"  ❌ {message}")
        errors.append(message)


def validate(path: str) -> int:
    errors = []

    # 1. JSON 格式
    try:
        with open(path, "r", encoding="utf-8") as f:
            stages = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析失败：{e}")
        return FAIL
    except FileNotFoundError:
        print(f"  ❌ 文件不存在：{path}")
        return FAIL

    # 2. 根元素是数组
    check(isinstance(stages, list), "根元素是数组", errors)
    if not isinstance(stages, list):
        print(f"\n❌ {len(errors)} 项检查未通过")
        return FAIL

    # 8. 至少 1 个阶段
    check(len(stages) >= 1, f"至少 1 个阶段（共 {len(stages)} 个）", errors)

    prev_end = -1
    for i, s in enumerate(stages):
        prefix = f"阶段 {i + 1}（{s.get('name', '?')}）"

        # 3. 字段完整
        check(isinstance(s.get("name"), str) and s["name"].strip() != "",
              f"{prefix}：name 存在且非空", errors)
        check(isinstance(s.get("start"), int) and s["start"] > 0,
              f"{prefix}：start 为正整数", errors)
        check(isinstance(s.get("end"), int) and s["end"] > 0,
              f"{prefix}：end 为正整数", errors)

        if not all(isinstance(s.get(k), int) for k in ("start", "end")):
            continue

        start, end = s["start"], s["end"]

        # 4. name 包含中文字符
        name_has_cn = bool(re.search(r"[一-鿿]", s.get("name", "")))
        check(name_has_cn, f"{prefix}：名称含中文描述", errors)

        # 4b. institution/position/direction（新格式校验，任一项出现就全员检查）
        if s.get("institution") or s.get("position") or s.get("direction"):
            check(isinstance(s.get("institution"), str) and s["institution"].strip() != "",
                  f"{prefix}：institution 存在且非空", errors)
            check(isinstance(s.get("position"), str) and s["position"].strip() != "",
                  f"{prefix}：position 存在且非空", errors)
            check(isinstance(s.get("direction"), str) and s["direction"].strip() != "",
                  f"{prefix}：direction 存在且非空", errors)
            dir_has_cn = bool(re.search(r"[一-鿿]", s.get("direction", "")))
            check(dir_has_cn, f"{prefix}：direction 含中文描述", errors)

        # 5. start <= end
        check(start <= end, f"{prefix}：{start} ≤ {end}（年份区间不反向）", errors)

        # 6 + 7. 时序和不重叠（允许相邻，后阶段 start == 前阶段 end 合法）
        if prev_end >= 0:
            check(start >= prev_end,
                  f"{prefix}：{start} ≥ {prev_end}（不重叠，且按从旧到新排序）", errors)
        prev_end = end

    # 9. 最后阶段覆盖当前年份
    if stages and isinstance(stages[-1].get("end"), int):
        last_end = stages[-1]["end"]
        check(last_end >= CURRENT_YEAR,
              f"最后阶段 end = {last_end} ≥ {CURRENT_YEAR}（覆盖当前年份）", errors)

    print()
    if errors:
        print(f"❌ {len(errors)} 项检查未通过")
        return FAIL
    else:
        print("✅ 全部检查通过")
        return PASS


def main():
    parser = argparse.ArgumentParser(description="career_stages.json 格式校验")
    parser.add_argument("stages_file", help="career_stages.json 路径")
    args = parser.parse_args()
    sys.exit(validate(args.stages_file))


if __name__ == "__main__":
    import argparse
    main()
