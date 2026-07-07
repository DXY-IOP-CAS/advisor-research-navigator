---
name: using-superpowers
description: "Use at the start of a task to choose relevant project skills and avoid stale or conflicting workflow instructions. Applies to this repository's advisor-research, quality-workbench, Chinese documentation, skill, debugging, TDD, planning, and verification work."
---

# Using Project Skills

Use skills as routing instructions, not as permission to ignore the user's current request. User instructions, `AGENTS.md`, and task-specific constraints take precedence when they are more specific.

## Quick Route

Before substantive work, choose the smallest relevant skill set.

| Task | Skill |
|:---|:---|
| Advisor research, `00-04`, evidence rules, learning paths | `research-advisor` |
| New structure, workflow, method, standard, or harness design | `brainstorming` |
| Updating or creating a skill | `skill-creator` |
| Chinese docs, workbench prose, AI-flavor control | `human-readable-chinese-docs` |
| Bug, failure, unexpected behavior | `systematic-debugging` |
| Feature or bugfix code implementation | `test-driven-development` when tests are meaningful |
| Multi-step implementation plan | `writing-plans` |
| Completion, commit, PR, or success claim | `verification-before-completion` |

Load the selected `SKILL.md` files before acting. Do not load unrelated references unless the selected skill explicitly points to them and the current task needs them.

## Project Overrides

- Do not read or cite `archive/` or `output/**/archive/**`.
- Do not create `docs/superpowers/specs` or `docs/superpowers/plans` by default. For this project, reusable design decisions usually go into `quality-workbench/`, the project handoff document, the relevant project skill, or the target file being edited.
- For workbench and advisor-document work, lock the current layer before editing: `M0`, `S1-S4`, `D00-D04`, sample output, skill, verifier, or harness.
- If a skill's generic instruction conflicts with the current project route, follow the project route and mention the conflict briefly in the work summary.
- Keep skill use lean. A skill should reduce ambiguity; if loading it only adds noise, stop expanding and return to the task contract.

## Start-of-Task Contract

For nontrivial work, write or hold these five facts before editing:

```text
Current layer:
Goal:
Inputs:
Do-not-touch:
Verification:
```

If the user has already approved a concrete scope, proceed inside that scope. Ask a question only when a missing answer would make a safe implementation impossible.
