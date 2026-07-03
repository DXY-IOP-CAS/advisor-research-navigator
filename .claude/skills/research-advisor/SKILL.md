---
name: research-advisor
description: >
  Run Phase 1 of the professor research-direction tool: identity locking,
  paper collection, profile rendering, and verification for a professor from
  only Chinese name, institution path, and official profile URL. Use when the
  user asks to 调研导师, 了解学者, 分析导师研究方向, 生成导师画像, run Phase 1,
  or do an end-to-end advisor-profile test.
---

# research-advisor

## Contract

Input is exactly:

```text
姓名：<中文名>
机构：<大学> / <学院或研究所> / <部门>
官网 URL：<教授主页链接>
```

Do not ask the user for English name, email, GS ID, OA ID, ORCID, papers, or JSON drafts. Discover them from sources. The final profile name must still be `中文名 (English Name)`; if no English name is found, use `[未找到]` and record the source gap.

## First Action

Initialize the profile directory with the user-provided path. Do not hand-create output folders.

```bash
python src/phase1/phase1_init.py \
  --university "<大学>" \
  --institute "<学院或研究所>" \
  --department "<部门>" \
  --name "<中文名>"
```

Use the printed `prof_dir` for every later step. Use `--prof-dir`; do not rebuild archive or output paths manually. Scripts may read/write their own intermediate files under the profile archive. Agents must not manually inspect `archive/` because repo guidance marks it write-only/do-not-read.

## Workflow

1. Read `references/phase1-core.md`.
2. Lock identity from the official page, Google Scholar, OpenAlex, ORCID, and cross-source paper fingerprints.
3. Create the required JSON files using `references/phase1-templates.md` when schema details are needed.
4. Run Phase B scripts in the order documented by `phase1-core.md`.
5. Render with `python src/phase1/render_profile.py --prof-dir "<prof_dir>" --department "<部门>"`.
6. Fill only narrative placeholders. Read `references/phase1-anti-patterns.md` before editing narrative.
7. Verify with `python src/phase1/verify_profile.py --prof-dir "<prof_dir>"`. If it fails, read `references/phase1-recovery.md`, fix, and rerun.
8. For end-to-end tests, write the process record to `docs/e2e/YYYY-MM-DD-<name>-minimal-prompt.md`.

## Reference Map

| File | Read When | Purpose |
|:-----|:----------|:--------|
| `references/phase1-core.md` | Every Phase 1 run | Main procedure, narrative rules, hard constraints |
| `references/phase1-templates.md` | Writing identity/stage JSON | `verified_ids.json` and `career_stages.json` schema |
| `references/phase1-anti-patterns.md` | Editing the profile | What not to rewrite; narrative examples |
| `references/phase1-recovery.md` | A step or verify fails | Recovery loop and failure handling |
| `references/01-data-sources.md` | API/search uncertainty | Source-specific search, limits, fallback |
| `src/phase1/pipeline.md` | CLI details are unclear | Technical source of truth for scripts |
| `END_TO_END_TEST.md` | Running a true e2e test | Minimal-prompt test rules |

## Source Search

Search in this order:

1. Official page: extract Chinese/English names, email, ORCID, biography, research directions, and source URL.
2. Google Scholar: search with discovered English name plus institution English name; extract profile URL and GS ID.
3. OpenAlex: search by English name, ORCID, and institution; extract Author ID.
4. ORCID: use official-page ORCID if present; otherwise search by English name.
5. arXiv: prefer ORCID-based exact matching; fall back to author search and relevant subject categories.

If a source fails, use another source instead of repeatedly retrying the same failure. If all paper sources fail, stop and report the blocker; do not fabricate output.

## Hard Constraints

- Source URLs are mandatory; missing source is `[未找到]`.
- Do not evaluate the professor or advise whether to apply.
- Do not modify generated paper tables; they come from `merged.json`.
- Do not rewrite the whole profile file. Replace placeholders only.
- Do not manually read `archive/`; use `--prof-dir` tools.
- A run is complete only after `verify_profile.py --prof-dir "<prof_dir>"` passes and remaining content risks are stated.
