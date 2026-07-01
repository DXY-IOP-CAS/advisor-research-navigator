"""
identity_resolver.py — 已废弃（阶段 0 已删除）。

该脚本原用于 Phase 0 的多源 ID 查询 + 论文标题交叉比对。Phase 0 删除后不再使用。
身份验证现在在 Phase 1 Step 2/3 中通过 GS 邮箱校验完成。

保留此文件仅供历史参考，不参与当前流水线。
"""

import json
import argparse
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "sources.json"
TIMEOUT = 15
USER_AGENT = "research-advisor/1.0 (mailto:research-advisor@local)"


def load_sources():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["sources"], cfg["verification"]


def http_get_json(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"_error": str(e), "_url": url}


# 各数据源具体搜索函数
def search_orcid(email: str) -> list:
    """按 email 搜 ORCID（黄金锚点）"""
    if not email:
        return []
    url = f"https://pub.orcid.org/v3.0/expanded-search?q=email:{urllib.parse.quote(email)}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        results = data.get("expanded-result", [])
        return [
            {
                "orcid_id": r.get("orcid-id", ""),
                "given_name": r.get("given-name"),
                "family_name": r.get("family-name"),
                "institutions": r.get("institution-name", []),
                "match_score": 1.0 if r.get("institution-name") else 0.5,
            }
            for r in results
        ]
    except Exception:
        return [{"_error": "ORCID query failed"}]


def search_openalex(name: str, ror: str = None) -> list:
    """按姓名 + 机构 ROR 搜 OpenAlex"""
    params = {"search": name, "per_page": "20"}
    if ror:
        params["filter"] = f"last_known_institutions.id:{ror}"
    # OpenAlex 不接受 ":" URL 编码后的值。手动构建 query string。
    qs_parts = []
    for k, v in params.items():
        str_val = str(v)  # 确保是字符串（per_page 初始为整数）
        if k == "filter":
            encoded = urllib.parse.quote(str_val, safe=":/")
        else:
            encoded = urllib.parse.quote(str_val)
        qs_parts.append(f"{k}={encoded}")
    qs = "&".join(qs_parts)
    url = f"https://api.openalex.org/authors?{qs}"
    data = http_get_json(url)
    if not data or "results" not in data:
        return [{"_error": "OpenAlex query failed", "_raw": str(data)[:200]}]
    candidates = []
    for r in data.get("results", []):
        candidates.append({
            "openalex_id": r.get("id"),  # 形如 "https://openalex.org/Axxxxx"
            "display_name": r.get("display_name"),
            "works_count": r.get("works_count"),
            "cited_by_count": r.get("cited_by_count"),
            "last_known_institutions": [
                i.get("display_name") for i in r.get("last_known_institutions", [])
            ],
            "topics": [t.get("display_name") for t in r.get("topics", [])][:5],
        })
    return candidates


def search_semantic_scholar(name: str) -> list:
    """按姓名搜 S2"""
    params = {"query": name, "fields": "name,affiliations,paperCount,externalIds"}
    qs = urllib.parse.urlencode(params)
    url = f"https://api.semanticscholar.org/graph/v1/author/search?{qs}"
    data = http_get_json(url)
    if not data or "data" not in data:
        return [{"_error": "S2 query failed"}]
    return [
        {
            "s2_id": r.get("authorId"),
            "name": r.get("name"),
            "affiliations": r.get("affiliations", []),
            "paper_count": r.get("paperCount"),
            "external_ids": r.get("externalIds", {}),
        }
        for r in data["data"][:10]
    ]


def search_arxiv_author(name: str) -> list:
    """arXiv Author ID 通常需要 GUI 查找；这里做一个软尝试：抓 arXiv 用户搜索页"""
    # arXiv 没有官方的 author search API；只去 web 搜。这里返回空，让上层走 Web Search。
    return [{"_note": "arXiv Author ID 需通过 Web Search 找 profile URL 后抓取"}]


def search_inspire_hep(name: str) -> list:
    """高能物理学科专用"""
    params = {"q": name, "size": 20}
    qs = urllib.parse.urlencode(params)
    url = f"https://inspirehep.net/api/authors?{qs}"
    data = http_get_json(url)
    if not data or "hits" not in data:
        return [{"_error": "INSPIRE query failed"}]
    candidates = []
    for h in data["hits"].get("hits", []):
        meta = h.get("metadata", {})
        candidates.append({
            "inspire_id": h.get("id"),
            "name": meta.get("name", {}).get("preferred_name") or meta.get("name", {}).get("value"),
            "arxiv_eid": meta.get("arxiv_eprints", [{}])[0].get("value") if meta.get("arxiv_eprints") else None,
            "affiliations": [
                a.get("value") for a in meta.get("affiliations", []) if "value" in a
            ],
            "bai": meta.get("bai", {}),  # INSPIRE BAI (Basic Author Identifier)
        })
    return candidates


def cross_check_papers(candidate_id: str, source: str, papers_from_homepage: list[str]) -> dict:
    """拿候选人论文列表，对比官网论文标题命中率"""
    if not papers_from_homepage:
        return {"hit_rate": None, "matched": [], "candidate_papers_count": 0}

    if source == "openalex":
        # OpenAlex ID 形如 "https://openalex.org/Axxxxx"，取末段
        author_id = candidate_id.split("/")[-1]
        url = f"https://api.openalex.org/works?filter=authorships.author.id:{author_id}&per_page=200"
        data = http_get_json(url)
        if not data or "results" not in data:
            return {"hit_rate": 0, "matched": [], "_error": "fetch works failed"}
        cand_titles = [w.get("title", "").lower() for w in data["results"]]
        cand_titles_normalized = [_norm(t) for t in cand_titles]
        return _match(papers_from_homepage, cand_titles_normalized, cand_titles)
    return {"hit_rate": None, "matched": [], "candidate_papers_count": 0}


def _norm(s: str) -> str:
    """归一化便于匹配：去标点 + 小写"""
    import re
    return re.sub(r"[\s\W_]+", "", s.lower())


def _match(homepage_titles, cand_titles_norm, cand_titles_orig) -> dict:
    matched = []
    for hp_title in homepage_titles:
        hp_norm = _norm(hp_title)
        # 标题归一化后做子串匹配（防止小误差）
        hit = False
        for i, ctn in enumerate(cand_titles_norm):
            if hp_norm in ctn or ctn in hp_norm:
                matched.append({"homepage_title": hp_title, "candidate_title": cand_titles_orig[i]})
                hit = True
                break
        if not hit:
            matched.append({"homepage_title": hp_title, "candidate_title": None})

    hit_rate = sum(1 for m in matched if m["candidate_title"] is not None) / max(1, len(homepage_titles))
    return {"hit_rate": round(hit_rate, 2), "matched": matched, "candidate_papers_count": len(cand_titles_orig)}


def synthesize_verdict(by_source: dict, papers_from_homepage: list[str]) -> dict:
    """
    综合各源结果，把候选人按综合置信度排序。
    优先级：
      - ORCID 命中机构 → 极高置信
      - OpenAlex 候选人 + 论文命中率 ≥80% → 高置信
      - 多源（≥2）的候选指向同一个人 → 高置信
      - 单源命中 50-80% → 中置信
    """
    candidates_aggregated = {}  # person_key -> aggregated record

    # ORCID 单源高置信
    for o in by_source.get("orcid", []):
        if "_error" in o or "orcid_id" not in o:
            continue
        key = (o.get("given_name", ""), o.get("family_name", ""))
        if o.get("match_score", 0) >= 1.0:  # 机构匹配
            candidates_aggregated.setdefault(key, {
                "name": f"{o.get('given_name')} {o.get('family_name')}",
                "orcid_id": o.get("orcid_id"),
                "evidence": [],
                "score": 0,
            })
            candidates_aggregated[key]["score"] += 50  # ORCID 强信号
            candidates_aggregated[key]["evidence"].append(
                f"ORCID 注册且机构匹配 ({o.get('institutions')})"
            )

    # OpenAlex + 论文比对
    best_openalex = None
    for c in by_source.get("openalex", []):
        if "_error" in c or "openalex_id" not in c:
            continue
        if not papers_from_homepage:
            # 没有官网论文可以比对，只按候选名字本身打分
            key = ("openalex-only", c.get("display_name", ""))
            candidates_aggregated.setdefault(key, {
                "name": c.get("display_name"),
                "openalex_id": c.get("openalex_id"),
                "evidence": [],
                "score": 5,  # OpenAlex 候机场默认分
            })
            continue
        # 拿论文
        xc = cross_check_papers(c["openalex_id"], "openalex", papers_from_homepage)
        rate = xc.get("hit_rate", 0) or 0
        key = ("openalex-verified", c.get("display_name", ""))
        score = rate * 40
        candidates_aggregated.setdefault(key, {
            "name": c.get("display_name"),
            "openalex_id": c.get("openalex_id"),
            "evidence": [f"OpenAlex 论文命中率 {int(rate*100)}%"],
            "score": score,
            "papers_in_openalex": xc.get("candidate_papers_count", 0),
            "papers_matched": [m for m in xc.get("matched", []) if m["candidate_title"]],
        })

    # INSPIRE-HEP 高置信（仅高能物理）
    for i in by_source.get("inspire-hep", []):
        if "_error" in i or "inspire_id" not in i:
            continue
        key = ("inspire", i.get("name", ""))
        candidates_aggregated.setdefault(key, {
            "name": i.get("name"),
            "inspire_id": i.get("inspire_id"),
            "evidence": ["INSPIRE-HEP 收录（高能物理领域权威）"],
            "score": 60,  # INSPIRE 强信号
        })
        candidates_aggregated[key]["affiliations"] = i.get("affiliations", [])

    # 排序按综合分
    ranked = sorted(
        candidates_aggregated.values(),
        key=lambda x: x.get("score", 0),
        reverse=True,
    )
    return {"candidates": ranked}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="姓名（拼音或英文）")
    parser.add_argument("--email", default="", help="邮箱（增强 ORCID 命中）")
    parser.add_argument("--ror", default="", help="机构 ROR ID（OpenAlex 用）")
    parser.add_argument("--papers-file", default="", help="JSON 列表文件，每项一个论文标题")
    parser.add_argument(
        "--enable",
        default="openalex,orcid,semantic_scholar",
        help="启用的数据源，逗号分隔",
    )
    parser.add_argument(
        "--discipline",
        default="general_physics",
        help="学科（决定是否启 INSPIRE/ADS）",
    )
    args = parser.parse_args()

    papers = []
    if args.papers_file and Path(args.papers_file).exists():
        with open(args.papers_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        if isinstance(papers, dict) and "papers" in papers:
            papers = papers["papers"]

    sources, verification = load_sources()
    enabled = set(args.enable.split(","))

    by_source = {}

    if "orcid" in enabled:
        by_source["orcid"] = search_orcid(args.email)

    if "openalex" in enabled:
        by_source["openalex"] = search_openalex(args.name, args.ror)

    if "semantic_scholar" in enabled:
        by_source["semantic_scholar"] = search_semantic_scholar(args.name)

    if "arxiv" in enabled:
        by_source["arxiv"] = search_arxiv_author(args.name)  # 占位

    if "inspire-hep" in enabled and args.discipline == "high_energy_physics":
        by_source["inspire-hep"] = search_inspire_hep(args.name)

    verdict = synthesize_verdict(by_source, papers)

    output = {
        "by_source": by_source,
        "verdict": verdict,
        "thresholds": verification["thresholds"],
        "user_gate_required": verification["user_gate_required"],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
