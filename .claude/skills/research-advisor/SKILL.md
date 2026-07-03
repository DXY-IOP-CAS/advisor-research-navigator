---
name: research-advisor
description: >
  Run the professor research-direction workflow from official identity locking
  through four Markdown deliverables. Use when the user asks to 调研导师,
  了解学者, 分析导师研究方向, 生成导师画像, run Phase 1, write or verify
  01_基础画像.md, 02_领域脉络.md, 03_论文定位.md, 04_学习讲义.md,
  or build phase 2-4 documents that connect a professor's current institution,
  research direction, papers, and student learning path.
---

# research-advisor

## Contract

Input for a new professor run is exactly:

```text
姓名：<中文名>
机构：<大学> / <学院或研究所> / <部门>
官网 URL：<教授主页链接>
```

Do not ask the user for English name, email, Google Scholar ID, OpenAlex ID,
ORCID, papers, or JSON drafts. Discover them from sources. The final profile
name must still be `中文名(English Name)`; if no English name is found, use
`[未找到]` and record the source gap.

The four deliverables form one cognitive ladder:

1. `01_基础画像.md`: who the professor is, with career stages and paper corpus.
2. `02_领域脉络.md`: what the student must understand about the professor's
   current direction and how it sits inside larger disciplines.
3. `03_论文定位.md`: how the professor's papers map onto that current direction,
   including mainline, technical predecessors, side branches, and weak evidence.
4. `04_学习讲义.md`: how a near-beginner can build toward reading the current
   frontier and the professor's relevant papers.

## First Action

For a new Phase 1 run, initialize the profile directory with the user-provided
path. Do not hand-create output folders.

```bash
python src/phase1/phase1_init.py \
  --university "<大学>" \
  --institute "<学院或研究所>" \
  --department "<部门>" \
  --name "<中文名>"
```

Use the printed `prof_dir` for every later step. Use `--prof-dir`; do not
rebuild archive or output paths manually. Agents must not manually inspect
`archive/` because repo guidance marks it write-only/do-not-read.

For an existing professor directory, first locate the active `prof_dir` from the
user-provided path or current `output/` path. Do not use archived outputs as
evidence.

## Workflow Router

Read only the references needed for the requested phase:

| Task | Read |
|:--|:--|
| Phase 1 / `01_基础画像.md` | `references/phase1-core.md`; add `phase1-templates.md`, `phase1-anti-patterns.md`, `phase1-recovery.md`, or `01-data-sources.md` only when needed |
| Phase 2 / `02_领域脉络.md` | `references/phase2-field-map.md`, `references/evidence-rules.md`, `references/quality-gates.md` |
| Phase 3 / `03_论文定位.md` | `references/phase3-paper-position.md`, `references/evidence-rules.md`, `references/quality-gates.md` |
| Phase 4 / `04_学习讲义.md` | `references/phase4-learning-guide.md`, `references/evidence-rules.md`, `references/quality-gates.md` |
| Deterministic smoke check | run `python .claude/skills/research-advisor/scripts/verify_phase_docs.py --prof-dir "<prof_dir>"` |

Use templates in `assets/templates/` for headings and document skeletons. Do not
mistake templates for sufficient content.

## Phase 1 Procedure

1. Read `references/phase1-core.md`.
2. Lock identity from the official page, Google Scholar, OpenAlex, ORCID, and
   cross-source paper fingerprints.
3. Create required JSON files using `references/phase1-templates.md` when
   schema details are needed.
4. Run Phase B scripts in the order documented by `phase1-core.md`.
5. Run `python src/phase1/risk_gate.py --prof-dir "<prof_dir>"`. Continue in
   standard mode only when it prints `mode: standard`; if it prints
   `mode: conservative_required`, do targeted supplemental search using the
   printed reasons, then rerun the gate.
6. Render with `python src/phase1/render_profile.py --prof-dir "<prof_dir>" --department "<部门>"`.
7. Fill only narrative placeholders. Read `references/phase1-anti-patterns.md`
   before editing narrative.
8. Verify with `python src/phase1/verify_profile.py --prof-dir "<prof_dir>"`.
   If it fails, read `references/phase1-recovery.md`, fix, and rerun.
9. For end-to-end tests, write the process record to
   `docs/e2e/YYYY-MM-DD-<name>-minimal-prompt.md`.

## Phase 2-4 Procedure

1. Start from the verified `01_基础画像.md`; treat career-stage paper grouping as
   a hypothesis about direction shifts, not as a final explanation.
2. Perform fresh source search for current direction and field context. Use
   official pages, recent review papers, field/tutorial pages, textbooks or
   lecture notes, and paper metadata. Do not rely on `01_基础画像.md` alone.
3. Build Phase 2 before Phase 3, and Phase 3 before Phase 4. Each later phase
   must explicitly consume the previous phase.
4. Mark every weak inference as `需人工复核`; use `[未找到]` for missing sources.
5. If field understanding is thin, pause writing and search again or ask for
   domain clarification. Do not fill gaps with generic prose.
6. Run the deterministic verifier after writing or editing phase documents.

## Hard Constraints

- Source URLs are mandatory; missing source is `[未找到]`.
- Do not evaluate the professor or advise whether to apply.
- Do not modify generated paper tables in Phase 1; they come from `merged.json`.
- Do not rewrite the whole Phase 1 profile file. Replace placeholders only.
- Do not manually read `archive/`; use active `output/` paths and `--prof-dir`
  tools.
- Do not treat a passing deterministic smoke check as proof of academic quality.
  It only checks structure and forbidden hygiene failures.
- A run is complete only after the requested verifier passes and remaining
  content risks are stated.
