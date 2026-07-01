"""
step1_discipline.py — 根据官网研究方向文本判定学科。

输入：研究方向文本（中英文混合） + 机构名
输出：学科归类 + 置信度 + 命中关键词
依赖：config/sources.json

用法：
  python src/phase1/step1_discipline.py --text "阿秒科学、强场物理" --affiliation "中科院物理所"
"""

import json
import argparse
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "sources.json"


def load_disciplines():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["disciplines"]


def classify(text: str, disciplines: dict) -> dict:
    """统计每个学科的关键词命中数。返回命中数最高者，平局取第一个。"""
    text_lower = text.lower()

    scores = {}
    hits = {}
    for disc_id, info in disciplines.items():
        if disc_id == "general_physics":
            continue
        all_kw = info.get("keywords_cn", []) + info.get("keywords_en", [])
        score = sum(1 for kw in all_kw if kw.lower() in text_lower)
        if score > 0:
            scores[disc_id] = score
            hits[disc_id] = [kw for kw in all_kw if kw.lower() in text_lower]

    if not scores:
        return {
            "primary": "general_physics",
            "confidence": 0.0,
            "matched_keywords": [],
            "arxiv_categories": disciplines["general_physics"]["arxiv_categories"],
            "primary_sources": disciplines["general_physics"]["primary_sources"],
        }

    primary = max(scores, key=scores.get)
    max_score = scores[primary]
    total_kws = len(disciplines[primary]["keywords_cn"] + disciplines[primary]["keywords_en"])
    confidence = min(1.0, max_score / max(1, total_kws / 2))

    return {
        "primary": primary,
        "confidence": round(confidence, 2),
        "matched_keywords": hits[primary],
        "arxiv_categories": disciplines[primary]["arxiv_categories"],
        "primary_sources": disciplines[primary]["primary_sources"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="研究方向文本（中英文）")
    parser.add_argument("--affiliation", default="", help="机构名（备用）")
    args = parser.parse_args()

    disciplines = load_disciplines()
    result = classify(args.text, disciplines)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
