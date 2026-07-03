# Quality Gates for Phase 2-4

## Deterministic Gate

Run:

```bash
python .claude/skills/research-advisor/scripts/verify_phase_docs.py --prof-dir "<prof_dir>"
```

This gate checks required files, required headings, source markers, and banned
advisor-evaluation phrases. Passing this gate does not prove content quality.

## Shared Content Gate

Before calling a phase document usable, verify:

- It clearly consumes the previous phase instead of repeating it.
- It has nearby URLs, `[未找到]`, or `需人工复核` for factual claims.
- It separates direct evidence from inference.
- It avoids professor evaluation and application recommendation.
- It names open uncertainty instead of smoothing it into confident prose.

## Phase 2 Gate

`02_领域脉络.md` passes only if:

- It gives a concise career-path view, then focuses on the current institution
  and current direction.
- It identifies when the current direction appears to start and which earlier
  stages are relevant to it.
- It maps parent discipline, subfield, smaller problem, methods, and frontier.
- It explains why the field context matters for an incoming student.
- It is based on fresh field/context search, not only on `01_基础画像.md`.

## Phase 3 Gate

`03_论文定位.md` passes only if:

- Papers are grouped by relationship to the current direction, not merely by
  year.
- Mainline papers explain problem, method, system/material/model, result, and
  relation to the current direction.
- Predecessor papers explain which capability or topic they contributed.
- Side branches and weak evidence are explicitly marked.
- It exports a knowledge-point list for Phase 4.

## Phase 4 Gate

`04_学习讲义.md` passes only if:

- It starts from the student's likely current level and the Phase 3 target
  papers.
- It uses backward design: target abilities first, then prerequisite concepts,
  then learning sequence and resources.
- It gives a staged route from basic concepts to the professor's current
  frontier.
- It includes resource pointers rather than pretending to be a full textbook.
- It has checkpoints that reveal whether the student can read the target papers.
