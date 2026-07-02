#!/usr/bin/env python3
"""
render_profile.py — 从 merged.json 按模板生成 01_基础画像.md

流水线位置：阶段 C。在 step6_merge.py 输出 merged.json 后执行。

数据流：
  [04_merged.json] ────────────┐
                               ▼
                         [本脚本] → 01_基础画像.md
                               │
                          [AI 润色] → 补充叙事/合作网络/公开信息

功能：
  1. 读取 merged.json，生成包含全部论文表格的结构化画像
  2. 论文按学术履历阶段分组（从 --stages 文件或 5 年默认段）
  3. 内联过滤：
     - OA 独有论文：通过合著者+期刊+机构网络评分（< 1 分过滤）
     - arXiv 独有论文：无 DOI 则过滤（无法交叉验证）
  4. 每篇论文附带 DOI/arXiv 超链接
  5. 头部嵌入运行统计（时间戳、各源状态、论文总数）
  6. 支持 --department 和 --stage-desc 参数定制内容

  脚本不写的内容（由 AI 渲染后补充）：
  - 学术履历表格     - 研究方向描述    - 合作网络
  - 公开信息整理     - 所有外部超链接  - 每阶段叙事段落

用法：
  python src/phase1/render_profile.py 04_merged.json -o 01_基础画像.md --department "超快物质科学中心"

可选参数：
  --stages career_stages.json   学术阶段配置
  --run-timestamp TS

依赖：标准库
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from collections import defaultdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    write_output, mark_source_tag,
    format_markdown_table, make_paper_link, source_tag,
    score_oa_noise,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("render_profile")


def load_merged(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_career_stages(year: int, stages: list = None) -> str:
    """根据学术履历阶段匹配论文。

    从 verified_ids.json 的 career_stages 读取阶段配置（博士/博后/独立等）。
    每篇论文的发表年份落入哪个阶段就归入哪组。
    无 stages 配置时返回 None（外部处理）。
    """
    if stages:
        for s in stages:
            start = s.get("start", 0)
            end = s.get("end", 9999)
            if start <= year <= end:
                return s.get("name", f"{start}–{end}")
    return None


def _build_stage_lookup(stage_config: list) -> dict:
    """从 career_stages 构建 name → 原数据的查找表。

    enriched stages 的 name 字段不含年份信息（如"博士阶段"）。
    通过查找表获取 start/end，用于排序和生成含年份范围的标题。
    """
    return {s["name"]: s for s in stage_config} if stage_config else {}


def _stage_header_name(name: str, meta: dict, enriched: bool) -> str:
    """生成含年份范围的阶段标题。

    enriched 新格式：显示 博士阶段（2000–2004）
    旧格式（name 已含年份信息）：直接返回 name，不重复追加
    """
    if enriched and meta and "start" in meta and "end" in meta:
        start, end = meta["start"], meta["end"]
        end_str = f"{end}" if end < 9999 else "至今"
        return f"{name}（{start}–{end_str}）"
    return name


def paper_url(paper: dict) -> str:
    """已弃用。请使用 utils.make_paper_link。保留向后兼容。"""
    return make_paper_link(paper)


def _shorten_markdown_link(link_text: str, max_text_len: int = 80) -> str:
    """截断 markdown 链接的显示文本，保留 URL。

    "[Very Long Paper Title...](https://doi.org/xxx)"  →  "[Very Long Paper Ti…](https://doi.org/xxx)"
    纯文本超出长度也截断。
    """
    m = re.match(r"^\[(.+?)\]\((https?://.+)\)$", link_text)
    if m:
        text, url = m.group(1), m.group(2)
        if len(text) > max_text_len:
            return f"[{text[:max_text_len-1]}…]({url})"
        return link_text
    # 纯文本回退
    return (link_text[:max_text_len-1] + "…") if len(link_text) > max_text_len else link_text


def _is_enriched_stages(stages: list) -> bool:
    """所有阶段都有 institution/position/direction → 自动生成 §2。

    任一阶段缺 institution 就回退到旧占位符（避免混用格式导致表格缺列）。
    """
    if not stages:
        return False
    return all(s.get("institution") for s in stages)


def render_career_timeline(stages: list) -> str:
    """从 career_stages 生成 §2 学术履历表格。

    career_stages.json 是唯一事实源。渲染时直接读它生成表格，
    AI 不再需要手动 Edit §2 内容。
    """
    lines = []
    L = lines.append
    L("## 2. 学术履历")
    L("")
    L("| 时间 | 机构 | 职位 | 方向 |")
    L("|:-----|:-----|:-----|:------|")
    for s in stages:
        start = s.get("start", "")
        end = s.get("end", "")
        period = f"{start}–{end}" if end and end < 9999 else f"{start}–至今"
        L(f"| {period} | {s.get('institution', '')} | {s.get('position', '')} | {s.get('direction', '')} |")
    L("")
    L("---")
    L("")
    return "\n".join(lines)


def generate(data: dict, output_path: str, stage_config: list = None,
              department: str = "", stage_descriptions: dict = None,
              run_timestamp: str = "") -> str:
    prof = data.get("professor", {})
    papers = data.get("papers", [])
    stats = data.get("statistics", {})
    src_status = data.get("source_status", {})

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 优先使用传入的 run_timestamp，否则从 archive 目录取最新
    if run_timestamp:
        ts_dir = run_timestamp
    else:
        prof_dir = os.path.dirname(output_path)
        archive_dir = os.path.join(prof_dir, "archive")
        if os.path.isdir(archive_dir):
            subdirs = sorted(os.listdir(archive_dir), reverse=True)
            ts_dir = subdirs[0] if subdirs else "latest"
        else:
            ts_dir = "latest"

    by_source = stats.get("by_source", {})
    cross_count = sum(1 for p in papers if p.get("source_count", 0) > 1)
    cross_pct = round(cross_count / max(len(papers), 1) * 100, 1)

    lines = []
    L = lines.append

    # Frontmatter
    L("---")
    L(f'affiliation: {prof.get("affiliation", "")}')
    L(f"department: {department}")
    L(f"source_updated: {ts}")
    L(f'orcid: {prof.get("orcid", "")}')
    L(f"google_scholar_url: https://scholar.google.com/citations?hl=en&user={prof.get('gs_id', '')}")
    L(f'openalex_id: {prof.get("oa_id", "")}')
    L(f"run_timestamp: {ts}")
    L(f"run_archive: archive/{ts_dir}/")
    L("---")
    L("")

    # 写入 filtered_papers 和 removed_titles 的逻辑在下面
    # 这里提前声明
    filtered_papers = []
    removed_titles = []

    # Title + Run info
    L(f"# {prof.get('name', '')} — 基础画像")
    L("")
    L("## 运行信息")
    L("")
    L("| 项目 | 内容 |")
    L("|:-----|:------|")
    L(f"| 生成时间 | {ts} |")
    L(f"| 运行存档 | `archive/{ts_dir}/` |")
    L(f"| 总论文数 | {len(papers)} 篇（合并后）|")
    L(f"| GS 状态 | {src_status.get('google_scholar', 'N/A')} |")
    L(f"| OA 状态 | {src_status.get('openalex', 'N/A')} |")
    L(f"| arXiv 状态 | {src_status.get('arxiv', 'N/A')} |")
    L(f"| 身份验证 | 已验证（email {prof.get('email_domain', '')}） |")
    L("")
    L("---")
    L("")

    # 1. 身份标识
    L("## 1. 身份标识")
    L("")
    L("| 字段 | 内容 |")
    L("|:-----|:------|")
    L(f'| 姓名 | {prof.get("name", "")} |')
    L(f'| 机构 | {prof.get("affiliation", "")} |')
    L(f'| 邮箱 | ...@{prof.get("email_domain", "")} |')
    L(f'| GS ID | {prof.get("gs_id", "")} |')
    L(f'| OA ID | {prof.get("oa_id", "")} |')
    L(f'| ORCID | {prof.get("orcid", "")} |')
    L("")
    L("---")
    L("")

    # 2. 学术履历（从 career_stages 生成）
    if _is_enriched_stages(stage_config):
        L(render_career_timeline(stage_config))
    else:
        L("## 2. 学术履历")
        L("")
        L("| 时间 | 机构 | 职位 | 方向 |")
        L("|:-----|:-----|:-----|:------|")
        L("")
        L("<!-- AI 渲染：从官网履历逐条填写，按从旧到新排序，教育→工作。每行含时间、机构、职位、方向。-->")
        L("")
        L("---")
        L("")

    # 3. 研究方向
    L("## 3. 研究方向")
    L("")
    L("<!-- AI 渲染：1 段总体概述 + 3-4 个具体方向。不做评价。每个专业术语首次出现时解释。 -->")
    L("")
    L("---")
    L("")

    # 4. 论文列表（按学术履历阶段分组）
    L("## 4. 全部论文（按学术履历阶段分组）")
    L("")
    L("<!-- 下方 4.x 节标题由 AI 渲染时填写。每节用 1-2 句话说明该阶段的研究主题，再列论文表格 -->")
    L("")

    # OA 错位论文过滤（通用合著者+期刊网络，不依赖学科关键词）
    filtered_papers = []
    removed_titles = []
    gs_or_multi = [p for p in papers if "google_scholar" in p.get("sources", [])
                   or p.get("source_count", 0) > 1]
    no_gs_anchor = not gs_or_multi and len(papers) > 0
    for p in papers:
        title = p.get("title", "")
        sources = set(p.get("sources", []))
        if sources == {"openalex"}:
            if no_gs_anchor:
                # 没有 GS 锚点 → 跳过 OA 噪声过滤，保留全部论文
                # 所有论文标记"未验证"但保留在正文中
                p["_no_gs_anchor"] = True
            else:
                score = score_oa_noise(p, gs_or_multi)
                if score < 1:
                    removed_titles.append(f"[OA 噪声] {title}")
                    continue
        # arXiv 独有论文过滤：无 DOI 的 arXiv-only 论文无法交叉验证，视为同名噪声
        # 有 DOI 的 arXiv-only 论文保留（可能是尚未被 GS 收录的预印本）
        if sources == {"arxiv"} and not p.get("doi"):
            removed_titles.append(f"[arXiv 无 DOI] {title}")
            continue
        filtered_papers.append(p)

    # Group by career stage
    stages = defaultdict(list)
    for p in filtered_papers:
        y = p.get("year")
        if y and isinstance(y, int):
            stage = compute_career_stages(y, stage_config)
            stages[stage if stage else "其他阶段"].append(p)
        else:
            stages["未知年份"].append(p)

    # Build stage lookup for enriched stages (name → start/end metadata)
    enriched = _is_enriched_stages(stage_config)
    stage_lookup = _build_stage_lookup(stage_config) if enriched else {}

    # Sort stages chronologically by their starting year
    def stage_sort_key(name: str) -> int:
        if enriched and name in stage_lookup:
            return stage_lookup[name].get("start", 9999)
        # 旧格式：从 name 字符串提取年份（如"博士阶段（2007–2013）"）
        m = re.search(r"(\d{4})", name)
        return int(m.group(1)) if m else 9999
    stage_order = sorted(stages.keys(), key=stage_sort_key)

    stage_idx = 1
    for stage_name in stage_order:
        stage_papers = stages.get(stage_name, [])
        if not stage_papers:
            continue
        stage_papers.sort(key=lambda p: (p.get("year") or 0, p.get("title", "")))

        header_name = _stage_header_name(stage_name, stage_lookup.get(stage_name, {}), enriched)
        L(f"### 4.{stage_idx} {header_name}")
        L("")
        # Stage narrative (from --stage-desc or AI enrichment placeholder)
        if stage_descriptions and stage_name in stage_descriptions:
            L(stage_descriptions[stage_name])
            L("")
        else:
            L(f"<!-- AI 渲染：1-2 句话说明该阶段的研究主题和方向变化。不写评价。 -->")
            L("")
        L(f"论文数：{len(stage_papers)} 篇")
        L("")
        headers = ["#", "年份", "标题", "期刊", "引用", "来源"]
        rows = []
        for i, p in enumerate(stage_papers, 1):
            title_display = _shorten_markdown_link(make_paper_link(p))
            journal = (p.get("journal") or "")[:40] or "—"
            cites = p.get("citation_count") or "—"
            tag = source_tag(p.get("sources", []))
            y = p.get("year") or "—"
            rows.append([str(i), str(y), title_display, journal, str(cites), tag])
        table = format_markdown_table(headers, rows)
        for line in table.split("\n"):
            L(line)
        L("")
        stage_idx += 1

    # 标注被剔除的错位论文
    if removed_titles:
        L("<!-- 已被剔除的 OA 错位论文（同名不同人，不计入本导师）：")
        for t in removed_titles:
            L(f"- {t}")
        L("-->")
    elif no_gs_anchor:
        L("<!-- 未找到 Google Scholar 档案。以下论文全部来自 OpenAlex，未经合著者/期刊网络过滤。")
        L("OpenAlex 作者 ID 可能聚合了多位同名学者的论文。")
        L("")
        L("核查步骤：")
        L("1. 检查标题是否属于该导师的研究领域（激光等离子体物理）。非本领域的论文（如 SAR 图像处理、材料科学、电化学等）应标记。")
        L("2. 确认方式：用 MCP 搜索工具查该论文标题 + 导师姓名，看是否真正属于此人。")
        L("3. 确认不相关的论文可在 AI 叙事中说明。不要删除论文表格行（表格由脚本生成）。")
        L("-->")
        L("")

    # 5. 合作网络（占位，AI 填充）
    L("## 5. 合作网络")
    L("")
    L("<!-- AI 渲染：列出高频合作者（姓名 + 机构 + 合作方向），每条带来源超链接。 -->")
    L("")
    L("---")
    L("")

    # 6. 公开信息（占位，AI 填充）
    L("## 6. 公开信息")
    L("")
    L("<!-- AI 渲染：列出新闻/采访/讲座/获奖/学术兼职等，每条带超链接。 -->")
    L("")
    L("---")
    L("")

    # 7. 引用与影响力分析（占位，AI 填充）
    L("## 7. 引用与影响力分析")
    L("")
    L("<!-- AI 渲染：总引用数、h-index、i10-index、单篇最高引用、近 3 年论文数等。 -->")
    L("")
    L("---")
    L("")

    # 8. 数据质量说明（按过滤后的论文统计）
    L("## 8. 数据质量说明")
    L("")
    L("| 数据源 | 状态 | 论文数 | 说明 |")
    L("|:-------|:----:|:------:|:-----|")
    gs_papers = len([p for p in filtered_papers if "google_scholar" in set(p.get("sources", []))])
    oa_papers = len([p for p in filtered_papers if "openalex" in set(p.get("sources", []))])
    arxiv_papers = len([p for p in filtered_papers if "arxiv" in set(p.get("sources", []))])
    total_unique = len(filtered_papers)
    L(f"| Google Scholar | {src_status.get('google_scholar', '?')} | {gs_papers} | h-index {prof.get('h_index')}, 引用 {prof.get('total_citations')} |")
    L(f"| OpenAlex | {src_status.get('openalex', '?')} | {oa_papers} | 元数据补充（DOI/期刊/作者） |")
    L(f"| arXiv | {src_status.get('arxiv', '?')} | {arxiv_papers} | 预印本（同名噪声已过滤） |")
    L(f"| 合并 | ✅ | {total_unique} | 去重后唯一数（多源论文在各源计数中重复计算） |")
    L("")
    # 交叉验证统计
    cross_count = sum(1 for p in filtered_papers if p.get("source_count", 0) > 1)
    cross_pct = round(cross_count / max(total_unique, 1) * 100, 1)
    if cross_count:
        L(f"多源交叉验证 {cross_count} 篇（{cross_pct}%）")
    L("")

    # 9. 验证来源（占位，AI 填充）
    L("## 9. 验证来源")
    L("")
    L("| 来源 | URL | 状态 |")
    L("|:-----|:----|:------|")
    L("")
    L("<!-- AI 渲染：列出官网、GS、ORCID、OpenAlex 等源链接，标注验证状态。 -->")
    L("")
    L("---")
    L("")

    # Save
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Profile written: {output_path} ({len(papers)} papers, {stage_idx - 1} stages)")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description="从 merged.json 生成基础画像")
    parser.add_argument("merged_json", help="04_merged.json 路径")
    parser.add_argument("--output", "-o", default="01_基础画像.md", help="输出路径")
    parser.add_argument("--stages", help="学术阶段配置 JSON 文件（不传则从 archive 自动查找）")
    parser.add_argument("--archive-dir", help="archive 目录路径（自动查找 career_stages.json、merged.json 等）")
    parser.add_argument("--department", "-d", default="", help="部门/实验室名称")
    parser.add_argument("--run-timestamp", help="当前运行的时间戳（如 20260702_024857），用于 frontmatter 中指向 archive 目录")
    args = parser.parse_args()

    stage_config = None
    stages_path = args.stages
    if not stages_path and args.archive_dir:
        stages_path = os.path.join(args.archive_dir, "career_stages.json")
    if stages_path and os.path.exists(stages_path):
        with open(stages_path, "r", encoding="utf-8") as f:
            stage_config = json.load(f)

    stage_descriptions = None

    data = load_merged(args.merged_json)
    generate(data, args.output, stage_config, args.department, stage_descriptions, args.run_timestamp)
    print(f"✅ {len(data.get('papers', []))} papers → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
