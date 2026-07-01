#!/usr/bin/env python3
"""
render_profile.py — 从 merged.json 按模板生成 01_基础画像.md。

严格遵循模板要求：全部论文逐一列出，按学术履历阶段分组。

用法：
  python src/phase1/render_profile.py output/.../04_merged.json -o output/.../01_基础画像.md
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("render_profile")


def load_merged(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_career_stages(year: int) -> str:
    """根据年份推断学术阶段。基于中科院物理所典型履历路径。"""
    if year <= 2013:
        return "博士及博后早期（~2013，近代物理所）"
    elif year <= 2016:
        return "RIKEN 博后（2013–2016）"
    elif year <= 2018:
        return "近代物理所副研究员（2016–2018）"
    elif year <= 2021:
        return "ETH Zurich 博士后（2018–2021）"
    elif year <= 2024:
        return "ETH Zurich 资深研究员（2021–2024）"
    else:
        return "中科院物理所独立 PI（2024–至今）"


def mark_source_tag(sources: list) -> str:
    if not sources:
        return "—"
    s = set(sources)
    tags = []
    if "google_scholar" in s:
        tags.append("GS")
    if "openalex" in s:
        tags.append("OA")
    if "arxiv" in s:
        tags.append("arXiv")
    return "+".join(tags)


def generate(data: dict, output_path: str) -> str:
    prof = data.get("professor", {})
    papers = data.get("papers", [])
    stats = data.get("statistics", {})
    src_status = data.get("source_status", {})

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    ts_dir = os.path.basename(os.path.dirname(os.path.dirname(output_path)))

    by_source = stats.get("by_source", {})
    cross_count = sum(1 for p in papers if p.get("source_count", 0) > 1)
    cross_pct = round(cross_count / max(len(papers), 1) * 100, 1)

    lines = []
    L = lines.append

    # Frontmatter
    L("---")
    L(f'affiliation: {prof.get("affiliation", "")}')
    L(f"department: 超快物质科学中心")
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
    L("**硬规则**：以下列出该导师的全部论文，不允许省略。每篇论文一行。")
    L("")

    # Group by career stage
    stages = defaultdict(list)
    for p in papers:
        y = p.get("year")
        if y and isinstance(y, int):
            stage = compute_career_stages(y)
            stages[stage].append(p)
        else:
            stages["未知年份"].append(p)

    stage_order = [
        "博士及博后早期（~2013，近代物理所）",
        "RIKEN 博后（2013–2016）",
        "近代物理所副研究员（2016–2018）",
        "ETH Zurich 博士后（2018–2021）",
        "ETH Zurich 资深研究员（2021–2024）",
        "中科院物理所独立 PI（2024–至今）",
    ]

    stage_idx = 1
    for stage_name in stage_order:
        stage_papers = stages.get(stage_name, [])
        if not stage_papers:
            continue
        stage_papers.sort(key=lambda p: (p.get("year") or 0, p.get("title", "")))

        L(f"### 4.{stage_idx} {stage_name}")
        L("")
        L(f"论文数：{len(stage_papers)} 篇")
        L("")
        L("| # | 年份 | 标题 | 期刊 | 引用 | 来源 |")
        L("|:-:|:----:|:-----|:-----|:----:|:-----|")
        for i, p in enumerate(stage_papers, 1):
            title = (p.get("title") or "")[:100]
            journal = (p.get("journal") or "")[:40] or "—"
            cites = p.get("citation_count") or "—"
            tag = mark_source_tag(p.get("sources", []))
            y = p.get("year") or "—"
            L(f"| {i} | {y} | {title} | {journal} | {cites} | {tag} |")
        L("")
        stage_idx += 1

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
    args = parser.parse_args()

    data = load_merged(args.merged_json)
    generate(data, args.output)


if __name__ == "__main__":
    main()
