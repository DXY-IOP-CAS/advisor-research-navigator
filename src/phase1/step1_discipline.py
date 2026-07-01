"""
step1_discipline.py — 学科关键词分类

用途：根据官网研究方向文本，自动判定该导师所属的物理学科分支。

流水线位置：阶段 A，在官网抓取后执行。

数据流：
  [MCP Fetch] 读官网提取研究方向文本
      ↓
  [本脚本] → 学科标签 JSON（含 arXiv 分类，传给 step5 减少噪声）

输出格式：
  {
    "primary": "atomic_molecular_optical",       # 学科 ID
    "confidence": 0.67,                            # 置信度
    "matched_keywords": ["attosecond", "ultrafast"],
    "arxiv_categories": ["physics.atom-ph", "physics.optics"],
    "primary_sources": ["openalex", "arxiv"]
  }

算法：关键词字典匹配（config/sources.json），不涉及网络请求。
取命中关键词数最多的学科。general_physics 作为无命中时的兜底。

用法：
  python src/phase1/step1_discipline.py --text "阿秒科学、强场物理" --affiliation "中科院物理所"

依赖：标准库 + config/sources.json
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
