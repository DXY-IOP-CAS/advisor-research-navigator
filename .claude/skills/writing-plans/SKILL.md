---
name: writing-plans
description: "Use when a scoped design or requirements need a multi-step execution plan before implementation. In this project, plans must respect layer locking, anti-bloat rules, advisor-research evidence boundaries, and the difference between code verification and manual document-quality review."
---

# Writing Project Plans

Use this skill after a design is scoped and approved, when the work needs multiple steps or multiple files. Keep the plan as small as the task allows.

## Default Location

Do not default to `docs/superpowers/plans`.

Use this routing instead:

| Plan type | Default location |
|:---|:---|
| Workbench method or document-standard rewrite | Chat plan plus the target `quality-workbench/` file |
| Advisor workflow or skill change | Target skill/reference file, with a short implementation note if needed |
| Code, verifier, harness, or tests | Chat plan first; create a plan file only if the user asks or the change is too large for one reviewable diff |
| Current state handoff | The project handoff document, only when the state actually changed |

## Plan Header

Every nontrivial plan must start with:

```text
Layer:
Goal:
Files:
Do-not-touch:
Verification:
Manual review needed:
```

For this project, "Manual review needed" is not optional. Many advisor-document quality claims cannot be proven by scripts.

## Task Shape

Each task should produce one reviewable change.

Good task boundaries:

- Rewrite one support method.
- Add one M0 execution gate.
- Update one project skill.
- Add one verifier check and its tests.

Bad task boundaries:

- Rewrite all methods, standards, skills, and samples together.
- Change a method and quietly update a real advisor sample.
- Add a verifier that claims to prove academic quality.

## Code And Harness Plans

For code changes, include:

- Exact files.
- Test commands.
- Expected failing and passing behavior when TDD is practical.
- Data or fixture boundaries.
- Rollback risk.

Do not add new production dependencies unless the user explicitly approves or the existing project pattern requires them.

## Documentation Plans

For workbench, Chinese docs, and advisor deliverables, include:

```text
Reader entry:
Reader exit:
Evidence or source basis:
Section handoff:
Failure checks:
Mechanical checks:
```

Do not treat a Markdown outline as quality. A plan must say how the document moves a reader from entry to exit.

## Execution

After writing the plan, proceed only if the user has approved the scope or already asked to start. During execution, update the user when a task completes and rerun verification before claiming success.
