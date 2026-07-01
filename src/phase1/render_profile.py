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
  3. 每篇论文附带 DOI/arXiv 超链接
  4. 头部嵌入运行统计（时间戳、各源状态、论文总数）
  5. 支持 --department 和 --stage-desc 参数定制内容

  脚本不写的内容（由 AI 渲染后补充）：
  - 学术履历表格     - 研究方向描述    - 合作网络
  - 公开信息整理     - 所有外部超链接  - 每阶段叙事段落

用法：
  python src/phase1/render_profile.py 04_merged.json -o 01_基础画像.md --department "超快物质科学中心"

可选参数：
  --stages career_stages.json   学术阶段配置
  --stage-desc stage_desc.json  阶段叙事描述

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import write_output, is_oa_pollution, mark_source_tag

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("render_profile")


def load_merged(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_career_stages(year: int, stages: list = None) -> str:
    """根据年份推断学术阶段。

    如果提供了 stages 配置（从 verified_ids.json 的 career_stages 读取），
    用配置中的年份区间匹配。否则按五年段通用分组。
    """
    if stages:
        for s in stages:
            start = s.get("start", 0)
            end = s.get("end", 9999)
            if start <= year <= end:
                return s.get("name", f"{start}–{end}")
    # 默认：每 5 年一段
    decade = (year // 5) * 5
    return f"{decade}–{decade + 4}"


def paper_link(paper: dict) -> str:
    """生成论文的超链接 markdown。优先 DOI，其次 arXiv。"""
    doi = paper.get("doi")
    if doi:
        clean = doi.strip()
        if clean.startswith("http"):
            return f"[DOI]({clean})"
        return f"[DOI](https://doi.org/{clean})"
    aid = paper.get("arxiv_id")
    if aid:
        return f"[arXiv](https://arxiv.org/abs/{aid})"
    return "—"


def generate(data: dict, output_path: str, stage_config: list = None,
              department: str = "", stage_descriptions: dict = None) -> str:
    prof = data.get("professor", {})
    papers = data.get("papers", [])
    stats = data.get("statistics", {})
    src_status = data.get("source_status", {})

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 向上 1 层到 professor 目录，再找 archive 子目录的最新时间戳
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
    L(f"run_timestamp: {ts}")
    L(f"run_archive: archive/{ts_dir}/")
    L("---")
    L("")

    # Title + Run info
    L(f"# {prof.get('name', '')} — 基础画像")
    L("")
    L("## 运行信息")
    L("")
    L("| 项目 | 内容 |")
    L("|:-----|:------|")
    L(f"| 生成时间 | {ts} |")
    L(f"| 运行存档 | `archive/{ts_dir}/` |")
    L(f"| 总论文数 | {len(papers)} 篇（去重合并后） |")
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

    # 4. 论文列表（按学术履历阶段分组）
    L("## 4. 全部论文（按学术履历阶段分组）")
    L("")
    L("<!-- 下方 4.x 节标题由 AI 渲染时填写。每节用 1-2 句话说明该阶段的研究主题，再列论文表格 -->")
    L("")

    # OA 错位论文过滤（剔除明显错位的论文）
    filtered_papers = []
    removed_titles = []
    for p in papers:
        title = p.get("title", "")
        sources = set(p.get("sources", []))
        # 仅过滤 OA 独有且标题命中错位关键词的论文
        if sources == {"openalex"} and is_oa_pollution(title):
            removed_titles.append(title)
            continue
        filtered_papers.append(p)

    # Group by career stage
    stages = defaultdict(list)
    for p in filtered_papers:
        y = p.get("year")
        if y and isinstance(y, int):
            stage = compute_career_stages(y, stage_config)
            stages[stage].append(p)
        else:
            stages["未知年份"].append(p)

    # Sort stages chronologically by their starting year
    def stage_start(name: str) -> int:
        m = re.search(r"(\d{4})", name)
        return int(m.group(1)) if m else 9999
    stage_order = sorted(stages.keys(), key=stage_start)

    stage_idx = 1
    for stage_name in stage_order:
        stage_papers = stages.get(stage_name, [])
        if not stage_papers:
            continue
        stage_papers.sort(key=lambda p: (p.get("year") or 0, p.get("title", "")))

        L(f"### 4.{stage_idx} {stage_name}")
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
        L("| # | 年份 | 标题 | 期刊 | 引用 | 来源 | 链接 |")
        L("|:-:|:----:|:-----|:-----|:----:|:-----|:-----|")
        for i, p in enumerate(stage_papers, 1):
            title = (p.get("title") or "")[:100]
            journal = (p.get("journal") or "")[:40] or "—"
            cites = p.get("citation_count") or "—"
            tag = mark_source_tag(p.get("sources", []))
            link = paper_link(p)
            y = p.get("year") or "—"
            L(f"| {i} | {y} | {title} | {journal} | {cites} | {tag} | {link} |")
        L("")
        stage_idx += 1

    # 标注被剔除的错位论文
    if removed_titles:
        L("<!-- 已被剔除的 OA 错位论文（同名不同人，不计入本导师）：")
        for t in removed_titles:
            L(f"- {t}")
        L("-->")

    # 8. 数据质量说明
    L("## 8. 数据质量说明")
    L("")
    L("| 数据源 | 状态 | 论文数 | 说明 |")
    L("|:-------|:----:|:------:|:-----|")
    gs_papers = len([p for p in papers if "google_scholar" in set(p.get("sources", []))])
    oa_papers = len([p for p in papers if "openalex" in set(p.get("sources", []))])
    arxiv_papers = len([p for p in papers if "arxiv" in set(p.get("sources", []))])
    L(f"| Google Scholar | {src_status.get('google_scholar', '?')} | {gs_papers} | h-index {prof.get('h_index')}, 引用 {prof.get('total_citations')} |")
    L(f"| OpenAlex | {src_status.get('openalex', '?')} | {oa_papers} | 元数据补充（DOI/期刊/作者） |")
    L(f"| arXiv | {src_status.get('arxiv', '?')} | {arxiv_papers} | 预印本（同名噪声已过滤） |")
    L(f"| 合并 | ✅ | {len(papers)} | 多源交叉验证 {cross_count} 篇（{cross_pct}%） |")
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
    parser.add_argument("--stages", help="学术阶段配置 JSON 文件")
    parser.add_argument("--department", "-d", default="", help="部门/实验室名称")
    parser.add_argument("--stage-desc", help="阶段描述 JSON 文件（{阶段名: 描述}）")
    args = parser.parse_args()

    stage_config = None
    if args.stages:
        with open(args.stages, "r", encoding="utf-8") as f:
            stage_config = json.load(f)

    stage_descriptions = None
    if args.stage_desc:
        with open(args.stage_desc, "r", encoding="utf-8") as f:
            stage_descriptions = json.load(f)

    data = load_merged(args.merged_json)
    args.output = os.path.abspath(args.output)
    args.output = os.path.normpath(args.output)
    generate(data, args.output, stage_config, args.department, stage_descriptions)
    print(f"✅ {len(data.get('papers', []))} papers → {args.output}", file=sys.stderr)
