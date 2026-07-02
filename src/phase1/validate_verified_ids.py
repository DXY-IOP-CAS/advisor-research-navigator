#!/usr/bin/env python3
"""
validate_verified_ids.py — verified_ids.json 格式自检。

校验 AI 在 Phase A 填写的身份验证记录是否完整、格式正确。
轻量校验，仅警告不阻塞。verify_profile 是最终质量门控。

校验项：
  1. JSON 合法 + 根是对象
  2. 必填字段：name, gs_id(或空), oa_id(或空), orcid(或空)
  3. verification.tier 在 T1-T4 范围内
  4. sources 中的 URL 格式合法

用法：
  python src/phase1/validate_verified_ids.py <path/to/verified_ids.json>

退出码：始终 0
"""

import json
import re
import sys

RECOVERY = {
    "tier": "verification.tier 必须是 T1/T2/T3/T4。T1=邮箱验证, T2=ORCID, T3=论文指纹, T4=综合判断",
    "missing gs_id": "无 GS ID 不影响流程（跳过 GS 降级到 OA）",
    "missing oa_id": "无 OA ID 不影响流程（跳过 OA）",
}


def check(condition: bool, msg: str, warns: list):
    tag = "[OK]" if condition else "[WARN]"
    print(f"  {tag} {msg}")
    if not condition:
        warns.append(msg)


def validate(path: str) -> int:
    warns = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  [WARN] JSON 读写失败：{e}")
        return 0

    check(isinstance(data, dict), "根元素是对象", warns)

    # name 必填
    check(isinstance(data.get("name"), str) and data["name"].strip(),
          "name 存在且非空", warns)

    # ids 字段（可选，但格式需正确）
    ids = data.get("ids", {})
    for k in ("gs_id", "oa_id", "orcid"):
        val = ids.get(k)
        if val:
            check(isinstance(val, str), f"ids.{k} 为字符串", warns)

    # verification.tier
    vt = data.get("verification", {})
    tier = vt.get("tier", "")
    check(tier in ("T1", "T2", "T3", "T4"),
          f"verification.tier = {tier}（应为 T1-T4）", warns)

    # email_domain 推荐
    ed = vt.get("email_domain", "")
    if ed and not re.match(r"^[a-z0-9][a-z0-9.-]+\.[a-z]{2,}$", ed.strip().lower()):
        check(False, f"verification.email_domain 格式异常：{ed}", warns)

    # sources URL
    sources = data.get("sources", {})
    for label, url in sources.items():
        if url and not url.startswith("http"):
            check(False, f"sources.{label} URL 格式异常：{url[:60]}", warns)

    if warns:
        print(f"\n  {len(warns)} 项警告——不影响渲染，但 verify 会检查")
    else:
        print("\n  [OK] 全部通过")

    return 0


def main():
    parser = argparse.ArgumentParser(description="verified_ids.json 格式自检")
    parser.add_argument("ids_file", help="verified_ids.json 路径")
    args = parser.parse_args()
    sys.exit(validate(args.ids_file))


if __name__ == "__main__":
    import argparse
    main()
