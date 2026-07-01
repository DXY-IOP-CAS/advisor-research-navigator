#!/usr/bin/env python3
"""Analyze merged pipeline output for 常国庆."""
import json
from pathlib import Path
from collections import Counter

BASE = Path(r"V:\Default\Desktop\当前学习内容\寻找导师的邮件\李自翔\量子蒙特卡洛\pilot-test")
ARCHIVE = BASE / "output" / "中国科学院大学" / "中科院物理所" / "超快物质科学中心" / "常国庆" / "archive" / "20260702_013012"

# Load OA
with open(ARCHIVE / "02_oa.json", encoding="utf-8") as f:
    oa = json.load(f)

oa_papers = oa.get("papers", [])

# Categorize papers
ultrafast_kw = ["fiber", "fibre", "laser", "femtosecond", "ultrafast", "ultra-fast",
    "frequency comb", "microscopy", "amplification", "nonlinear", "photon",
    "pulse", "multiphoton", "soliton", "mid-ir", "mid-infrared", "terahertz",
    "coherent", "oscillator", "mode-lock", "chirp", "raman", "supercontinuum",
    "parametric", "optica", "optics", "optical", "spectroscopy", "spectrum",
    "cavity", "diode", "amplifier", "attenuation", "broadband", "carrier",
    "dispersion", "doppler", "grating", "interferometer", "millimeter",
    "nano", "photonic", "polarization", "refractive", "resonator",
    "sagnac", "saturable", "sensor", "silicon", "stark", "waveguide",
    "wavelength", "cep", "crystal", "diffraction", "detector",
    "electro-optic", "envelope", "faraday", "filter", "gain",
    "harmonic", "heterodyne", "homodyne", "imaging", "injection",
    "laser", "lens", "light", "modulator", "multimode", "noise",
    "phase", "photodetector", "photocurrent", "plasmon",
    "prism", "pump-probe", "quantum cascade", "reflectivity",
    "semiconductor", "single-mode", "slm", "swept-source",
    "switch", "sync", "synchrotron", "telescope", "thermal",
    "tunable", "upconversion", "visible", "ytterbium", "ybfiber",
    "erbium", "thulium", "holmium", "chirped", "pre-chirp",
    "self-phase", "spm", "sess", "astro-comb", "frequency comb",
    "filamentation", "hollow-core", "photonic crystal",
    "lithium niobate", "pcf", "large-pitch", "rod-type",
    "divided-pulse", "coherent beam combining", "cbc",
    "nalm", "cvcg", "raman soliton", "multiphoton",
    "second-harmonic", "third-harmonic", "two-photon",
    "three-photon", "shg", "thg", "2pef", "3pef",
    "slm microscopy", "optical biopsy", "cancer detection",
    "gastric", "frequency comb", "dfg", "difference frequency",
    "opa", "optical parametric", "supercontinuum",
    "cherenkov", "parabolic", "similariton", "few-cycle",
    "carrier-envelope", "astrophysical spectrograph",
    "harps", "radial velocity", "exoplanet", "inhomogeneous",
    "pulse compression", "multi-pass cell", "mpc",
    "microjoule", "millijoule", "nanojoule",
    "high-power", "high-energy", "high repetition",
    "bifurcation", "soliton", "dissipative",
    "noise-like", "mode-locked", "wave-breaking",
    "self-similar", "self-starting", "q-switch",
    "gain-switch", "thin-disk", "slab", "innoslab",
    "tapered", "double-clad", "multicore",
    "vortex", "orbital angular", "beam quality",
    "m²", "m^2", "mode area", "large mode area"]

topological_kw = ["weyl", "topological", "fermi arc", "semimetal", "fermion",
    "berry curvature", "kagome", "chiral crystal", "nodal line",
    "taas", "nbAs", "tap", "nbp", "frank heger", "su-yang",
    "m. zahid hasan", "hasan", "mz hasan",
    "quantum spin hall", "quantum material", "strongly correlated",
    "nodal", "dirac semimetal", "ti."]

ultrafast_papers = []
topological_papers = []
other_papers = []

for p in oa_papers:
    title = (p.get("title") or "").lower()
    if any(kw in title for kw in ultrafast_kw):
        ultrafast_papers.append(p)
    elif any(kw in title for kw in topological_kw):
        topological_papers.append(p)
    else:
        other_papers.append(p)

print(f"Total OA papers: {len(oa_papers)}")
print(f"Ultrafast/optics related: {len(ultrafast_papers)}")
print(f"Topological/condensed matter: {len(topological_papers)}")
print(f"Other/uncategorized: {len(other_papers)}")
print()

# Year distribution of each category
uf_years = Counter(p.get("year", 0) for p in ultrafast_papers)
top_years = Counter(p.get("year", 0) for p in topological_papers)
print("Year distribution - Ultrafast vs Topological:")
all_years = sorted(set(list(uf_years.keys()) + list(top_years.keys())))
print(f"{'Year':>6}  {'UF':>4}  {'Topo':>5}")
for y in all_years:
    print(f"{y:>6}  {uf_years.get(y, 0):>4}  {top_years.get(y, 0):>5}")
print()

# Show citation range for each category
uf_cites = [p.get("citation_count", 0) or 0 for p in ultrafast_papers]
top_cites = [p.get("citation_count", 0) or 0 for p in topological_papers]
print(f"Ultrafast total citations: {sum(uf_cites)}")
print(f"Topological total citations: {sum(top_cites)}")
print(f"Ultrafast mean citations: {sum(uf_cites)/max(len(uf_cites),1):.0f}")
print(f"Topological mean citations: {sum(top_cites)/max(len(top_cites),1):.0f}")
print()

# Show merge stats
with open(ARCHIVE / "04_merged.json", encoding="utf-8") as f:
    merged = json.load(f)
print(f"Merged papers: {len(merged.get('papers',[]))}")
print(f"Merged status: {merged.get('status')}")
print(f"Merged professor: {merged.get('professor',{}).get('name')}")
print(f"Merged h_index: {merged.get('professor',{}).get('h_index')}")
