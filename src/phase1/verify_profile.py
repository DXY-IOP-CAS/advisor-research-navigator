#!/usr/bin/env python3
"""
verify_profile.py — 画像质量自动门控。

在阶段 C 完成后运行。检查画像是否满足成品标准。
所有检查项不通过则退出码非 0，AI 不能声称完成。

用法：
  python src/phase1/verify_profile.py --prof-dir output/<大学>/<学院所>/<部门>/<姓名>

退出码：0 = 通过，1 = 有失败项
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ProfDirResolver

PASS, FAIL = 0, 1


def check(condition: bool, message: str, errors: list):
    if condition:
        print(f"  [OK] {message}")
    else:
        print(f"  [FAIL] {message}")
        errors.append(message)


def _has_mixed_name_format(value: str) -> bool:
    value = (value or "").strip()
    has_chinese = bool(re.search(r"[一-鿿]", value))
    has_english = bool(re.search(r"[a-zA-Z]", value))
    has_paren = "(" in value or "（" in value
    return has_chinese and has_english and has_paren


def _extract_section(content: str, heading_pattern: str) -> str:
    match = re.search(heading_pattern, content, re.MULTILINE)
    if not match:
        return ""
    rest = content[match.end():]
    next_heading = re.search(r"\n##\s+\d+\.", rest)
    return rest[:next_heading.start()] if next_heading else rest


def verify(profile_path: str, merged_path: str = None) -> int:
    errors = []

    # 0. 路径规范：output/<大学>/[学院所]/[部门]/<姓名>/01_基础画像.md
    #    phase1_init.py 强制这一格式。verify 检查路径深度做兜底。
    parts = profile_path.replace("\\", "/").split("/")
    md_idx = next((i for i, p in enumerate(parts) if p.endswith(".md")), -1)
    path_depth = md_idx  # output/<...>/ 的层级数（不含文件名）
    if path_depth < 3:
        check(False,
              f"输出路径层级不规范：{profile_path}。"
              "应为 output/<大学>/<学院所>/<部门>/<姓名>/01_基础画像.md"
              f"（当前 {path_depth} 级，应 ≥4）",
              errors)
    elif path_depth < 5 and path_depth == 4:
        # 4 级路径如 output/中科院物理研究所/超快物质科学中心/姓名/ — 缺少大学层
        # 不 fail，但 warn
        pass

    with open(profile_path, encoding="utf-8") as f:
        content = f.read()

    # 1. 无禁止关键词
    forbidden = ["代表性论文", "关键论文", "以下见完整列表", "如下图"]
    for kw in forbidden:
        check(kw not in content, f"无禁止关键词「{kw}」", errors)

    # 1b. 成品 Markdown 不暴露流水线元数据。
    check(not content.startswith("---\n"), "不使用裸露 frontmatter", errors)

    html_comment_count = len(re.findall(r"<!--.*?-->", content, re.DOTALL))
    check(html_comment_count == 0,
          f"不含 HTML 注释（发现 {html_comment_count} 处）",
          errors)

    # 1c. 表格内部无空行（空行会破坏 markdown 表格渲染）
    table_regions = re.findall(r"^\| # \| 年份 \| 标题 \| 期刊 \| 引用 \| 来源 \|(.+?)(?=\n\n|\Z)", content, re.MULTILINE | re.DOTALL)
    blank_within_table = False
    for region in table_regions:
        lines = region.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "" and i > 0 and i < len(lines) - 1:
                # 检查旁边的行是否是表格行
                if i > 0 and lines[i - 1].strip().startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
                    blank_within_table = True
                    break
    check(not blank_within_table, "论文表格内部无空行", errors)

    # 2. 名字格式：硬约束——必须是「中文名 (English Name)」中英混合
    title = re.search(r"^# (.+)[–—―]+\s*基础画像$", content, re.MULTILINE)
    if title:
        t = title.group(1).strip()
        has_chinese = bool(re.search(r"[一-鿿]", t))
        has_english = bool(re.search(r"[a-zA-Z]", t))
        if _has_mixed_name_format(t):
            check(True, f"名字格式正确（中英混合）：「{t}」", errors)
        elif has_chinese and has_english:
            check(False,
                  f"名字格式：当前「{t}」含中英文但缺括号。应改为「中文名 (English Name)」",
                  errors)
        elif has_chinese:
            check(False,
                  f"名字格式：当前纯中文「{t}」。应加英文名 →「中文名 (English Name)」",
                  errors)
        else:
            check(False,
                  f"名字格式：当前纯英文「{t}」。硬约束要求中英混合 →「中文名 (English Name)」",
                  errors)
    else:
        check(False, "有标题行（# 中文名 (English Name) — 基础画像）", errors)

    identity_section = _extract_section(content, r"^## 1\.\s*身份标识\s*$")
    identity_name = re.search(r"^\|\s*姓名\s*\|\s*(.+?)\s*\|", identity_section, re.MULTILINE)
    if identity_name:
        name_value = identity_name.group(1).strip()
        check(_has_mixed_name_format(name_value),
              f"§1 姓名字段为中英混合格式：{name_value}",
              errors)
    else:
        check(False, "§1 姓名字段存在", errors)

    identity_email = re.search(r"^\|\s*邮箱\s*\|\s*(.+?)\s*\|", identity_section, re.MULTILINE)
    if identity_email:
        email_value = identity_email.group(1).strip()
        check("@@" not in email_value,
              f"§1 邮箱字段无双 @：{email_value}",
              errors)

    section9 = _extract_section(content, r"^## 9\.\s*验证来源\s*$")
    section9_header_count = len(re.findall(
        r"^\|\s*来源\s*\|\s*URL\s*\|\s*状态\s*\|",
        section9,
        re.MULTILINE,
    ))
    check(section9_header_count == 1,
          f"§9 验证来源表头只出现一次（发现 {section9_header_count} 次）",
          errors)

    source_rows = [
        line for line in section9.splitlines()
        if line.startswith("|")
        and not re.match(r"^\|\s*:?-+", line)
        and "来源" not in line
        and "URL" not in line
    ]
    check(len(source_rows) > 0, f"§9 验证来源表至少 1 行（{len(source_rows)} 行）", errors)

    section9_bullets = [
        line for line in section9.splitlines()
        if re.match(r"^\s*[-*]\s+", line)
    ]
    check(len(section9_bullets) == 0,
          f"§9 验证来源不用列表格式（发现 {len(section9_bullets)} 行）",
          errors)

    unverified_rows = [
        line for line in source_rows
        if "未验证" in line or "linkedin.com" in line.lower()
    ]
    check(len(unverified_rows) == 0,
          f"§9 验证来源不含未验证来源（发现 {len(unverified_rows)} 行）",
          errors)

    check(not re.search(r"^## 4\..+\n\n\n+### 4\.\d+", content, re.MULTILINE),
          "§4 大标题后没有多余空行",
          errors)

    # 3. 论文表格行数（如果提供了 merged.json）
    if merged_path:
        with open(merged_path, encoding="utf-8") as f:
            merged = json.load(f)
        total_merged = len(merged.get("papers", []))
        paper_rows = len(re.findall(r"^\| \d+ \| \d{4}", content, re.MULTILINE))

        # GS 论文数作为基准（GS 由学者维护，应全部保留）
        gs_papers = [p for p in merged.get("papers", [])
                     if "google_scholar" in p.get("sources", [])]
        gs_count = len(gs_papers)

        if gs_count > 0:
            # 有 GS 锚点：检查 GS 论文是否被完整渲染
            missing = gs_count - paper_rows
            check(missing <= max(3, int(gs_count * 0.05)),
                  f"GS 论文 {gs_count} 篇中至少渲染了 {paper_rows} 篇（缺失 {max(0, missing)} 篇）",
                  errors)
        else:
            # 无 GS：OA-only，用宽松容差
            tolerance = max(10, int(total_merged * 0.3))
            diff = abs(total_merged - paper_rows)
            check(diff <= tolerance,
                  f"论文行数：{paper_rows}（OA-only merged={total_merged}，差 {diff}，容差 {tolerance}）",
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

    # 6. 论文表格有可点击来源链接（DOI、arXiv 或 GS publication URL）
    links = len(re.findall(r"^\| \d+ \| \d{4} \| .*?\]\(https?://", content, re.MULTILINE))
    check(links > 0, f"有超链接（{links} 个）", errors)

    # 7. 全部 9 节必须存在至少 7 节（部分节可能因数据不足合理缺失）
    required_sections = [
        "## 1.", "## 2.", "## 3.", "## 4.",
        "## 5.", "## 6.", "## 7.", "## 8.", "## 9.",
    ]
    sections_found = sum(1 for s in required_sections if s in content)
    check(sections_found >= 7, f"基础章节 9 节中存在 {sections_found}/9", errors)

    # 8. AI 占位符必须已被替换（AI 渲染注释残留 = 叙事未完成）
    placeholder_count = content.count("<!-- AI 渲染")
    check(placeholder_count == 0,
          f"AI 叙事占位符已替换（仍有 {placeholder_count} 处 <!-- AI 渲染：... --> 未替换）",
          errors)

    # 9. 论文表格为 6 列（检查表头和数据行）
    table_headers = re.findall(r"^\| # \| 年份 \| 标题 \| 期刊 \| 引用 \| 来源 \|", content, re.MULTILINE)
    check(len(table_headers) >= 1, "论文表格表头为 6 列（#、年份、标题、期刊、引用、来源）", errors)

    paper_table_rows = re.findall(r"^\| \d+ \| \d{4} \| .+ \|$", content, re.MULTILINE)
    unvetted_single_source = []
    for row in paper_table_rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < 6:
            continue
        source_cell = cells[5]
        source_plain = re.sub(r"\s+", "", source_cell)
        is_single_source_external = source_plain.startswith("OA") or source_plain.startswith("arXiv")
        is_manually_checked = "已核查" in source_cell or "人工核查" in source_cell
        if is_single_source_external and not is_manually_checked:
            title = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", cells[2])
            unvetted_single_source.append(title)
    check(len(unvetted_single_source) == 0,
          f"单源 OA/arXiv 论文需人工核查（发现 {len(unvetted_single_source)} 行，例：{unvetted_single_source[:3]}）",
          errors)

    # 9b. 论文表格行宽不过长（超过 400 字符的行会破坏 markdown 表格渲染）
    table_lines = [l for l in content.split("\n") if l.startswith("| ") and l.count("|") >= 4]
    long_lines = [len(l) for l in table_lines if len(l) > 400]
    check(len(long_lines) == 0,
          f"论文表格行宽 ≤400 字符（发现 {len(long_lines)} 行超过 400 字符，最长 {max(long_lines) if long_lines else 0}）",
          errors)

    # 10. 阶段标题含年份范围（除外桶：其他阶段、未知年份）
    stage_headers = re.findall(r"^### 4\.\d+ (.+)$", content, re.MULTILINE)
    bare_years = [s for s in stage_headers
                  if s not in ("其他阶段", "未知年份")
                  and not re.search(r"\d{4}.*(?:\d{4}|至今)", s)]
    check(len(bare_years) == 0,
          f"阶段标题含年份范围（发现 {len(bare_years)} 个无年份的阶段：{bare_years[:5]}）",
          errors)

    # 11. 无重复论文标题
    dupes = set()
    if merged_path:
        # 从 merged.json 检测（比从 markdown 文本更准确，避免截断/格式干扰）
        with open(merged_path, encoding="utf-8") as f:
            merged = json.load(f)
        seen = set()
        for p in merged.get("papers", []):
            plain = (p.get("title") or "").strip().lower()
            if plain in seen:
                dupes.add(p.get("title", ""))
            seen.add(plain)
    else:
        # 备用：从 markdown 文本提取
        titles = re.findall(r"^\| \d+ \| \d{4} \| (.+?) \|", content, re.MULTILINE)
        seen = set()
        for t in titles:
            plain = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", t).strip().lower()
            if plain in seen:
                dupes.add(t)
            seen.add(plain)
    check(len(dupes) == 0, f"无重复论文标题（发现 {len(dupes)} 篇重复：{list(dupes)[:3]}）", errors)

    # 汇总
    print()
    if errors:
        print(f"[FAIL] {len(errors)} 项检查未通过")
        print()
        print("  下一步修复指引：")
        for e in errors:
            fix = next((f for k, f in FIX_MAP.items() if k in e), None)
            if fix:
                print(f"  - 「{e}」→ {fix}")
            else:
                print(f"  - 「{e}」→ 检查 §/节号是否正确，或重新运行 render 后 Edit")
        return FAIL
    else:
        print("[OK] 全部检查通过")
        return PASS


FIX_MAP = {
    "禁止关键词": "删除包含这些词的句子（参考 references/phase1-anti-patterns.md）",
    "frontmatter": "删除文件开头的 YAML 元数据；必要信息放入「资料概览」或「身份标识」",
    "HTML 注释": "删除最终 Markdown 中的 <!-- ... --> 隐藏注释；需要保留的信息改写为正文或数据质量说明",
    "表格内部无空行": "删除论文表格行之间的空行（只删表格内的，前后叙事段落保留）",
    "名字格式": "改为 '# 中文名 (English Name) — 基础画像' 格式",
    "论文行数": "merged JSON 有变化，跑 render_profile.py --prof-dir ... 重新生成",
    "学术履历": "跑 render_profile.py --prof-dir ... --stages career_stages.json 重新生成（career_stages.json 需含 institution/position/direction 字段）",
    "叙事": "每个 ### 4.x 阶段表格前必须有 1-2 句研究主题说明",
    "有超链接": "确认论文有 DOI、arXiv 或 Google Scholar 论文链接（render_profile.py 自动生成）",
    "基础章节": "补充缺失的章节（§3 方向 / §5 合作 / §6 公开 / §7 引用）",
    "重复论文标题": "去重 step6_merge.py 输出；保留唯一版本",
    "进度标题含年份": "跑 render_profile.py（career_stages.json 含 start/end 即自动生成年份范围）",
    "无中文的阶段": "career_stages.json 的 name 字段改为中文（如「博士阶段」）",
    "输出路径": "用 phase1_init.py 重建：python src/phase1/phase1_init.py --university 中国科学院大学 --institute 中科院物理研究所 --department 部门 --name 姓名 --official-url 官网URL",
    "AI 叙事占位符": "用 Edit 替换占位符：Edit(file_path, old='<!-- AI 渲染：方向 -->', new='实际研究方向描述')。参考 references/phase1-core.md §叙事规范",
    "论文表格表头": "论文表格必须 6 列：# / 年份 / 标题 / 期刊 / 引用 / 来源。禁止 AI 加 '关键论文' / '代表性论文' 等筛选表",
    "论文表格行宽": "论文标题过长（>400 字符）会被截断。检查 render 输出是否含异常长标题",
    "阶段含有论文表格": "career_stages.json 需要至少 2 个阶段，每个阶段必须有论文落入。检查阶段 start/end 是否覆盖了论文年份范围",
    "阶段后空文本": "§2 学术履历表格后到 ### 4.1 之间应有 1-2 句研究方向过渡段；如缺则在 §2 末尾 Edit 一段过渡文字",
}


def main():
    parser = argparse.ArgumentParser(
        description="画像质量自动门控",
        usage="%(prog)s --prof-dir PROF_DIR",
    )
    parser.add_argument("profile", nargs="?",
                        help=argparse.SUPPRESS)
    parser.add_argument("--merged", help=argparse.SUPPRESS)
    parser.add_argument("--archive-dir", help=argparse.SUPPRESS)
    parser.add_argument("--prof-dir", help="prof 根目录（output/.../姓名/），从 _internal/latest.txt 自动推导")
    args = parser.parse_args()

    # prof-dir 优先；archive-dir 仅保留内部兼容，AI 不必手动拼路径
    if args.prof_dir and not args.archive_dir:
        resolver = ProfDirResolver(args.prof_dir)
        args.archive_dir = resolver.archive_dir
        if args.archive_dir and not args.profile:
            args.profile = resolver.profile_path
        if not args.archive_dir:
            parser.error(f"--prof-dir {args.prof_dir} 下找不到 _internal/latest.txt，请先跑 phase1_init.py")

    merged_path = args.merged
    if not merged_path and args.archive_dir:
        merged_path = os.path.join(args.archive_dir, "04_merged.json")
    if not args.profile:
        parser.error("找不到 01_基础画像.md。传位置参数或 --prof-dir")

    result = verify(args.profile, merged_path)
    sys.exit(result)


if __name__ == "__main__":
    main()
