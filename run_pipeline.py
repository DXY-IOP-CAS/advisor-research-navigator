#!/usr/bin/env python3
"""Run Phase B and C for 常国庆."""
import subprocess, sys, json
from pathlib import Path

BASE = Path(r"V:\Default\Desktop\当前学习内容\寻找导师的邮件\李自翔\量子蒙特卡洛\pilot-test")
PROF = BASE / "output" / "中国科学院大学" / "中科院物理所" / "超快物质科学中心" / "常国庆"
TIMESTAMP = "20260702_013018"

ARCHIVE = PROF / "archive" / TIMESTAMP
ARCHIVE.mkdir(parents=True, exist_ok=True)

# Step 3: OpenAlex
print("=== Step 3: OpenAlex ===")
result = subprocess.run([
    sys.executable, str(BASE / "src/phase1/step3_openalex.py"),
    "A5050706950",
    "--email", "guoqing.chang@iphy.ac.cn",
    "-o", str(ARCHIVE / "02_oa.json")
], capture_output=True, text=True)
print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr[-500:])
print(f"Return code: {result.returncode}")

# Step 5: arXiv
print("\n=== Step 5: arXiv ===")
result = subprocess.run([
    sys.executable, str(BASE / "src/phase1/step5_arxiv.py"),
    "Chang_Guoqing",
    "-c", "physics.optics physics.atom-ph",
    "-o", str(ARCHIVE / "03_arxiv.json")
], capture_output=True, text=True)
print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr[-500:])
print(f"Return code: {result.returncode}")

# Step 6: Merge
print("\n=== Step 6: Merge ===")
# Check if files exist before merge
oa_file = ARCHIVE / "02_oa.json"
arxiv_file = ARCHIVE / "03_arxiv.json"
merge_args = []
if oa_file.exists():
    merge_args.append(str(oa_file))
else:
    print("WARNING: OA file not found")
if arxiv_file.exists():
    merge_args.append(str(arxiv_file))
else:
    print("WARNING: arXiv file not found")

result = subprocess.run([
    sys.executable, str(BASE / "src/phase1/step6_merge.py"),
    *merge_args,
    "-o", str(ARCHIVE / "04_merged.json")
], capture_output=True, text=True)
print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr[-500:])
print(f"Return code: {result.returncode}")

# Check merge result
if (ARCHIVE / "04_merged.json").exists():
    with open(ARCHIVE / "04_merged.json", encoding="utf-8") as f:
        merged = json.load(f)
    print(f"\nMerge result: {merged.get('status')}, {len(merged.get('papers', []))} papers")
