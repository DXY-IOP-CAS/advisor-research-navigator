#!/usr/bin/env python3
"""
run.py — 阶段 1 统一入口脚本。

将阶段 B（数据采集）+ 阶段 C（渲染）的 6 个脚本串联为一条命令。
自动处理：存档旧版 → 建目录 → 采集 → 合并 → 渲染 → 验证。

用法（常规）：
  python src/phase1/run.py "中科院物理所/超快物质科学中心/王示例" \
    --gs-id XXXXXXXXAAAAJ \
    --oa-id A5048473780 \
    --email your@real.com \
    --orcid 0000-0000-0000-0000 \
    --categories "physics.atom-ph physics.optics"

用法（最少参数，无 GS/OA 时）：
  python src/phase1/run.py "清华大学/中文系/李飞跃"

依赖：Python 3.10+, pip install scholarly
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

SRC_DIR = os.path.dirname(os.path.abspath(__file__))


def e(*args, **kwargs):
    """Run a phase1 script, print output, return exit code.

    First arg is a script filename relative to src/phase1/.
    """
    script = os.path.join(SRC_DIR, args[0])
    cmd = [sys.executable, script] + list(args[1:])
    print(f"\n$ {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=False, **kwargs)
    return result.returncode


def build_prof_path(university: str = "", institute: str = "",
                    department: str = "", name: str = "") -> str:
    """自动拼接输出目录路径。

    结构化参数拼接，保证层级一致：
      output/<大学>/<学院所>/<部门>/<姓名>/
    大学 + 姓名是必须的，有姓名的前提下学院所和部门可选。
    仅提供 name 时回退到单段（兼容旧用法）。
    """
    if university and name:
        parts = [p for p in [university, institute, department, name] if p]
        return "/".join(parts)
    return name


def run(prof_path: str, gs_id: str = "", oa_id: str = "",
        orcid: str = "", email: str = "", categories: str = "",
        department: str = "", stages_file: str = "",
        name_pinyin: str = "") -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"output/{prof_path}"
    archive = f"{base}/archive/{ts}"

    # 0. 存档旧版
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Phase 1 Pipeline — {prof_path}", file=sys.stderr)
    print(f"Timestamp: {ts}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    archive_script = os.path.join(SRC_DIR, "archive_previous.py")
    subprocess.run([sys.executable, archive_script, prof_path], capture_output=False)

    # 1. 建目录
    os.makedirs(archive, exist_ok=True)

    # 2. 复制 Phase A 文件（如果存在）
    for src_name, dst_name in [("verified_ids.json", "00_verified_ids.json"),
                                ("career_stages.json", "career_stages.json")]:
        src_path = os.path.join(base, src_name)
        if os.path.exists(src_path):
            import shutil
            shutil.copy2(src_path, os.path.join(archive, dst_name))
            print(f"  📄 {src_name} → archive/", file=sys.stderr)

    # 3. 校验 career_stages.json
    stages_path = stages_file or os.path.join(archive, "career_stages.json")
    if os.path.exists(stages_path):
        ret = e("validate_career_stages.py", stages_path)
        if ret != 0:
            print('  ⚠️ career_stages.json 校验未通过，请检查后重试', file=sys.stderr)
            # 不阻塞流程，论文将归入"其他阶段"
    else:
        print('  ⚠️ 未找到 career_stages.json，论文将按「其他阶段」归并', file=sys.stderr)

    # 4. Step 2: Google Scholar
    if gs_id:
        ret = e("step2_gs.py", gs_id, "-o", f"{archive}/01_gs.json")
        if ret != 0:
            print("  ⚠️ GS 获取失败，跳过", file=sys.stderr)
    else:
        print("  ⏭️ 无 GS ID，跳过 Google Scholar", file=sys.stderr)
        # 写入空的 GS 文件
        with open(f"{archive}/01_gs.json", "w") as f:
            json.dump({"pipeline": "phase1", "source": "google_scholar",
                       "status": "blocked", "professor": None, "papers": [],
                       "metadata": None}, f)

    # 5. Step 3: OpenAlex
    if oa_id:
        email_args = ["--email", email] if email else []
        ret = e("step3_openalex.py", oa_id, *email_args, "-o", f"{archive}/02_oa.json")
        if ret != 0:
            print("  ⚠️ OA 获取失败，跳过", file=sys.stderr)
    else:
        print("  ⏭️ 无 OA ID，跳过 OpenAlex", file=sys.stderr)
        with open(f"{archive}/02_oa.json", "w") as f:
            json.dump({"pipeline": "phase1", "source": "openalex",
                       "status": "blocked", "professor": None, "papers": [],
                       "metadata": None}, f)

    # 6. arXiv: step4（ORCID 精确匹配）→ 失败回退 step5（au: 搜索）
    name_cn = os.path.basename(prof_path)
    name_arxiv = name_pinyin or name_cn  # step5 需要拼音，没给就传中文
    if orcid:
        ret = e("step4_arxiv_id.py", orcid, "--name", name_cn,
                "-o", f"{archive}/03_arxiv.json")
        if ret != 0:
            print("  ⏬ STEP4 失败，回退到 STEP5", file=sys.stderr)
            orcid = ""  # 标记回退
    if not orcid:
        cat_args = ["-c", categories] if categories else []
        e("step5_arxiv.py", name_arxiv, *cat_args,
          "-o", f"{archive}/03_arxiv.json")

    # 7. Step 6: 合并
    gs_file = f"{archive}/01_gs.json"
    oa_file = f"{archive}/02_oa.json"
    arxiv_file = f"{archive}/03_arxiv.json"
    ret = e("step6_merge.py", gs_file, oa_file, arxiv_file,
            "-o", f"{archive}/04_merged.json")
    if ret != 0:
        print("  ❌ 合并失败", file=sys.stderr)
        return 1

    # 8. Render profile
    dept_args = ["--department", department] if department else []
    stage_args = ["--stages", stages_path] if os.path.exists(stages_path) else []
    ts_args = ["--run-timestamp", ts]
    ret = e("render_profile.py", f"{archive}/04_merged.json",
            "-o", f"{base}/01_基础画像.md",
            *dept_args, *stage_args, *ts_args)
    if ret != 0:
        print("  ❌ 渲染失败", file=sys.stderr)
        return 1

    # 9. 记录 latest.txt
    with open(f"{base}/latest.txt", "w") as f:
        f.write(f"{ts}\n")

    # 10. Verify
    merged_exists = os.path.exists(f"{archive}/04_merged.json")
    if merged_exists:
        ret = e("verify_profile.py", f"{base}/01_基础画像.md",
                "--merged", f"{archive}/04_merged.json")
        if ret == 0:
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"✅ 全部完成：{base}/01_基础画像.md", file=sys.stderr)
            print(f"   存档：{archive}/", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)
        else:
            print(f"\n⚠️ 画像已生成但 verify 未通过，请检查", file=sys.stderr)
    else:
        print(f"\n✅ 渲染完成（无 merged.json，跳过 verify）", file=sys.stderr)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Phase 1 统一入口")
    parser.add_argument("prof_path", nargs="?", default="",
                        help="output 下的学者路径，如 中科院物理所/超快物质科学中心/王示例。"
                             "不传时用 --university/--name 自动构造。")
    parser.add_argument("--university", help="大学/上级机构（如 中国科学院大学）")
    parser.add_argument("--institute", help="学院/研究所（如 中科院物理所）")
    parser.add_argument("--name", help="学者姓名（与 --university 配合自动构造路径）")
    parser.add_argument("--gs-id", help="Google Scholar ID")
    parser.add_argument("--oa-id", help="OpenAlex Author ID")
    parser.add_argument("--orcid", help="ORCID（含连字符）")
    parser.add_argument("--email", help="OpenAlex polite pool 邮箱")
    parser.add_argument("--categories", "-c", help="arXiv 学科分类，如 'physics.atom-ph physics.optics'")
    parser.add_argument("--department", "-d", help="部门/实验室名称")
    parser.add_argument("--stages", help="career_stages.json 路径（默认从输出目录自动查找）")
    parser.add_argument("--name-pinyin", help="姓名拼音（姓_名），arXiv 搜索用，如 Wang_Shili。不传则用中文名搜（不推荐）")
    args = parser.parse_args()

    # 路径构建：优先结构化参数，回退到 prof_path
    prof_path = args.prof_path or build_prof_path(
        args.university or "", args.institute or "",
        args.department or "", args.name or "")
    if not prof_path:
        parser.error("必须提供 prof_path 或 --university + --name")

    sys.exit(run(
        prof_path=prof_path,
        gs_id=args.gs_id or "",
        oa_id=args.oa_id or "",
        orcid=args.orcid or "",
        email=args.email or "",
        categories=args.categories or "",
        department=args.department or "",
        stages_file=args.stages or "",
        name_pinyin=args.name_pinyin or "",
    ))


if __name__ == "__main__":
    main()
