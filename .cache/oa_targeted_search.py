#!/usr/bin/env python3
"""OpenAlex title search with long delays — process papers in small batches."""
import json, sys, time, urllib.request, urllib.parse

def search(title, email, max_retries=3):
    for attempt in range(max_retries):
        try:
            query = urllib.parse.quote(title[:200])
            url = f"https://api.openalex.org/works?search={query}&per_page=3"
            req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": f"mailto:{email}"})
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
                "oa_cited_by_count": best.get("cited_by_count", 0),
                "authors": [a.get("author", {}).get("display_name") for a in (best.get("authorships") or [])],
                "relevance_score": results[0].get("relevance_score"),
            }
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(10)
                continue
            return {"error": str(e)}

# Titles to enrich (key GS papers that need DOI/journal)
titles = [
    # ETH / IPHY era - high value papers
    "Generation and simulation of tabletop extreme ultraviolet high-order harmonics",
    "A liquid-phase high-order harmonic generation apparatus for investigating ultrafast dynamics in liquids",
    "Generation of isolated white-light attosecond pulses in solids",
    "Design and application of liquid-phase magnetic-bottle time resolved photoelectron spectroscopy",
    "Observing vibrational quantum beating in the ultrafast predissociation of SF6",
    "Effects of Autoionizing Resonances on Wave-Packet Dynamics Studied by Time-Resolved Photoelectron Spectroscopy",
    "Low-energy electron distributions from the photoionization of liquid water: a sensitive test of electron mean free paths",
    "Ionization energy of liquid water revisited",
    "Effect of electron correlations on attosecond photoionization delays in the vicinity of the Cooper minima of argon",
    "Observation of indirect (e, 3e) process of CO",
    "Interatomic relaxation processes induced in neon dimers by electron-impact ionization",
    "An experimental investigation of the dissociative ionization process of argon cluster ions induced by electron impact",
    "Direct evidence of Interatomic Coulombic Decay in electron impact ionization of Ne dimer",
    "Observation of interatomic Coulombic decay and electron-transfer-mediated decay in high-energy electron-impact ionization of Ar",
    "Evidence of strong projectile-target-core interaction in single ionization of neon by electron impact",
]

email = "pengju.zhang@iphy.ac.cn"
results = []
total = len(titles)

for i, title in enumerate(titles):
    print(f"[{i+1}/{total}] {title[:60]}...", file=sys.stderr)
    oa = search(title, email)
    results.append({"title_gs": title, "openalex": oa})
    time.sleep(3.5)  # long delay to avoid rate limit

with open("/v/Default/Desktop/当前学习内容/寻找导师的邮件/李自翔/量子蒙特卡洛/pilot-test/.cache/oa_title_enrich.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

matched = sum(1 for r in results if r["openalex"] and not r["openalex"].get("error"))
print(f"Done. {matched}/{total} matched", file=sys.stderr)
