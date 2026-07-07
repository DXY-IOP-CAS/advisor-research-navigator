---
name: verification-before-completion
description: "Use before claiming work is complete, fixed, improved, committed, or ready for review. Requires fresh verification evidence, diff/status inspection, and explicit residual-risk reporting. Applies to docs, skills, advisor deliverables, code, verifier, harness, commits, and PRs."
---

# Verification Before Completion

Evidence comes before completion claims. Do not say work is complete, fixed, passing, improved, or committed until fresh checks support that exact claim.

## Gate

Before a completion or success claim:

1. Name the claim.
2. Choose the narrowest command or review that can support it.
3. Run the check in the current turn.
4. Read the output and exit code.
5. Inspect the diff or changed files when files changed.
6. State what passed and what remains manual or risky.

If no command can prove the claim, say so and report the manual review boundary.

## Project Check Sets

### Workbench And Chinese Docs

Run:

```powershell
git diff --check -- . ':(exclude)archive/**' ':(exclude)output/**/archive/**'
rg -n "<project banned wording regex>" "<changed-doc>"
git status --short
```

Also inspect the changed document for:

- reader entry and exit;
- section handoff;
- source-to-judgment-to-application chain;
- evidence boundary;
- tables, diagrams, and checklists serving a real reader task.

Mechanical checks do not prove academic or teaching quality.

### Project Skills

Run:

```powershell
git diff --check -- . ':(exclude)archive/**' ':(exclude)output/**/archive/**'
rg -n "<stale skill placeholder or old superpowers workflow regex>" ".claude/skills"
git status --short
```

Then inspect each changed `SKILL.md` for:

- valid YAML frontmatter with `name` and `description`;
- concise body;
- no stale generic workflow that conflicts with `AGENTS.md`;
- no unnecessary reference files or extra docs;
- clear routing for when to load the skill.

### Advisor Deliverables

When real `00-04` output changes, run the relevant project verifiers when available:

```powershell
python .claude/skills/research-advisor/scripts/verify_phase_docs.py --prof-dir "<prof_dir>"
python .claude/skills/research-advisor/scripts/verify_source_metadata.py --prof-dir "<prof_dir>"
python .claude/skills/research-advisor/scripts/verify_mermaid_render.py --prof-dir "<prof_dir>"
```

Only run commands that match the files changed and the available environment. Always state which academic-quality claims still require manual review.

### Code, Verifier, Harness, Or Tests

Run the narrowest meaningful tests, lint, type check, build, or smoke test for the changed area. If TDD applies, verify the red and green states when practical.

Do not treat doc smoke checks as proof that research judgment is correct.

## Commit Gate

Before committing:

1. Run the relevant check set.
2. Inspect `git diff --cached --stat` after staging.
3. Ensure staged files match the intended scope.
4. Commit only after verification and scope inspection.
5. Run `git status --short --branch` after commit.

## Reporting Shape

When closing work, report:

```text
Changed:
Verified:
Not proven by automation:
Git status / commit:
```

Do not imply stronger certainty than the evidence supports.
