---
name: brainstorming
description: "Use before changing project structure, workflow, quality-workbench methods, document standards, advisor-research process, skills, harness, verifier behavior, or any ambiguous multi-step design. In this project it means: understand the layer, propose a scoped design, get approval when the scope is not already approved, then edit only that layer."
---

# Brainstorming for This Project

Use this skill to prevent design work from turning into scattered edits. It is a gate before modifying behavior, structure, methods, standards, skills, harness, or long-lived documentation.

## Project Rule

Do not default to `docs/superpowers/specs`. This project stores current reusable design work in `quality-workbench/` until the rule is stable enough to move into `research-advisor`, templates, verifier, tests, or formal docs.

Do not make a new design document unless the user asks for one or the change spans independent subsystems that cannot be reviewed in one target file.

## Required Flow

1. **Read local context.** Start from `AGENTS.md` and the target files. For advisor work, read `quality-workbench/README.md` and the relevant M0/S/D file. Never read `archive/`.
2. **Lock the layer.** Name the current layer: `M0`, `S1-S4`, `D00-D04`, sample output, skill, verifier, harness, or global skill.
3. **Write a task contract.**

   ```text
   Goal:
   Inputs:
   Constraints:
   Done when:
   Verification:
   ```

4. **Separate design from editing.** If the user has not already approved the current scope, present the intended files, the main structural change, and what will stay untouched. Wait for approval.
5. **Edit narrowly.** After approval, change only the locked layer. Put cross-layer effects in a short "follow-up / later recovery" note instead of editing them immediately.
6. **Verify before closure.** Run the narrow checks named in the task contract and inspect `git status`.

## When The User Already Approved The Scope

If the user has already approved a concrete next step in the current conversation, do not ask again. State the layer lock and proceed.

Example:

```text
Layer: project skills.
Scope: update project-local superpowers skills only; do not edit global skills or S1-S4.
```

## Workbench Design Standard

For `quality-workbench/` and Chinese method documents, design from the reader's problem:

```text
What failure is this change trying to stop?
What source or prior decision supports it?
What execution action should it create?
How will a reviewer see that it worked?
What should not be generalized yet?
```

Avoid adding sections, diagrams, tables, or new files for completeness. Add a form only when it reduces a real review or reader burden.

## Questions

Ask at most one blocking question at a time. Prefer continuing with the safest scoped assumption when the answer can be recovered from the repo or the user's latest instruction.
