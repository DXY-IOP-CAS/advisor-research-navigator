#!/usr/bin/env python3
"""Per-title OpenAlex search for GS papers — enrich with DOI, journal, authors."""
import json
import sys
import time
import urllib.request
import urllib.parse

def search_openlex_by_title(title, email=None):
    """Search OpenAlex works by title. Returns best match or None."""
    query = urllib.parse.quote(title[:200])
    url = f"https://api.openalex.org/works?search={query}&per_page=5"
    headers = {"Accept": "application/json"}
    if email:
        headers["User-Agent"] = f"mailto:{email}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        if not results:
            return None
        best = results[0]
        loc = best.get("primary_location") or {}
        source = loc.get("source") or {}
        doi = best.get("doi") or loc.get("doi")
        return {
            "title_oa": best.get("title"),
            "doi": doi,
            "journal": source.get("display_name"),
            "publication_date": best.get("publication_date"),
            "type": best.get("type"),
            "cited_by_count": best.get("cited_by_count", 0),
            "authors": [
                a.get("author", {}).get("display_name")
                for a in (best.get("authorships") or [])
            ],
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    gs_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    email = "pengju.zhang@iphy.ac.cn"

    with open(gs_path, encoding="utf-8") as f:
        gs_data = json.load(f)

    enriched = []
    works = gs_data.get("works", [])
    total = len(works)

    for i, paper in enumerate(works):
        title = paper.get("title", "")
        print(f"[{i+1}/{total}] {title[:60]}...", file=sys.stderr)
        oa = search_openlex_by_title(title, email)
        enriched.append({
            "title_gs": title,
            "year_gs": paper.get("year"),
            "citations_gs": paper.get("citations"),
            "openalex": oa,
        })
        time.sleep(0.15)  # polite rate limit

    result = {
        "source": "gs+openalex_title_search",
        "total_papers": len(enriched),
        "matched": sum(1 for e in enriched if e["openalex"] and not e["openalex"].get("error")),
        "papers": enriched,
    }

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Done. {result['matched']}/{total} matched → {out_path}", file=sys.stderr)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
