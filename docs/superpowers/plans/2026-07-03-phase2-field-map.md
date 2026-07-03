# Phase 2 Field Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a reviewable `02_领域脉络.md` for 张鹏举 based on the active `01_基础画像.md`, fresh source search, and the new research-advisor phase 2 quality gates.

**Architecture:** Treat Phase 2 as a standalone evidence-building task. Preserve the active Phase 1 profile as the fact base, quarantine the accidental Phase 2 draft from the official output path, then write a new field map from fresh professor and field sources.

**Tech Stack:** Markdown deliverables, `.claude/skills/research-advisor` references/templates, `verify_phase_docs.py`, `git`.

## Global Constraints

- Do not read or reference `archive/`.
- Source URLs are mandatory; missing sources are `[未找到]`.
- Do not evaluate the professor or advise whether to apply.
- Do not treat deterministic smoke as proof of content quality.
- Do not run full subagent e2e unless the user explicitly requests it.
- Report progress frequently and stop for user review after Phase 2.

---

### Task 1: Quarantine Accidental Phase 2 Draft

**Files:**
- Modify: `output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/02_领域脉络.md`
- Create: `output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/_drafts/02_领域脉络_废稿_20260703.md`

**Interfaces:**
- Consumes: active professor directory.
- Produces: clean official path for the new `02_领域脉络.md`.

- [ ] **Step 1: Confirm the official path exists**

Run:

```powershell
Test-Path "output\中国科学院大学\中科院物理研究所\超快物质科学中心\张鹏举\01_基础画像.md"
```

Expected: `True`.

- [ ] **Step 2: Move the accidental draft out of the official filename**

Run a PowerShell move into `_drafts/` if `02_领域脉络.md` exists. Do not delete it.

- [ ] **Step 3: Confirm official Phase 2 path is clear**

Run:

```powershell
Test-Path "output\中国科学院大学\中科院物理研究所\超快物质科学中心\张鹏举\02_领域脉络.md"
```

Expected: `False`.

### Task 2: Extract Phase 1 Evidence Base

**Files:**
- Read: `output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/01_基础画像.md`
- Create: working notes only if needed under `.tmp/phase2_zhang_pengju/`

**Interfaces:**
- Consumes: `01_基础画像.md`.
- Produces: current-direction hypothesis, career-stage timeline, recent-paper seed list.

- [ ] **Step 1: Extract identity, current unit, research direction, career stages, and paper sections**

Use script or manual reading. Record only active-output evidence; do not read `archive/`.

- [ ] **Step 2: Form a provisional hypothesis**

Write down:

```text
Current direction:
Likely start period:
Direct predecessor stages:
Possible side branches:
Evidence gaps:
```

### Task 3: Fresh Source Search

**Files:**
- No repository write required until synthesis.

**Interfaces:**
- Consumes: Phase 1 seed list.
- Produces: source-backed field map evidence for `02_领域脉络.md`.

- [ ] **Step 1: Search professor/current-unit sources**

Search official profile, group page, ORCID, Google Scholar/OpenAlex-style metadata, and recent papers.

- [ ] **Step 2: Search field-context sources**

Search current-direction reviews/tutorials/lecture notes and parent discipline resources. Prefer sources that explain the field hierarchy, methods, and frontier.

- [ ] **Step 3: Label evidence**

Use `直接证据`, `交叉证据`, `弱证据`, and `需人工复核`.

### Task 4: Write Official `02_领域脉络.md`

**Files:**
- Create: `output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举/02_领域脉络.md`
- Use: `.claude/skills/research-advisor/assets/templates/02_领域脉络.md`

**Interfaces:**
- Consumes: Phase 1 evidence base and fresh search notes.
- Produces: Phase 2 document ready for user review and Phase 3 input.

- [ ] **Step 1: Use the template headings**

Headings must include:

```markdown
## 运行信息
## 导师路径速览
## 当前方向学科定位
## 领域发展树
## 关键问题和技术路线
## 当前前沿
## 来源与待复核点
```

- [ ] **Step 2: Write with current-direction weighting**

Keep biography short; focus on current field map, direction transition, methods, frontier, and uncertainties.

### Task 5: Verify, Report, and Commit

**Files:**
- Test: `.claude/skills/research-advisor/scripts/verify_phase_docs.py`
- Modify: git index only for the new/changed Phase 2 files and plan if appropriate.

**Interfaces:**
- Consumes: completed `02_领域脉络.md`.
- Produces: verification result, user review summary, commit checkpoint.

- [ ] **Step 1: Run deterministic smoke**

Run:

```powershell
python .claude\skills\research-advisor\scripts\verify_phase_docs.py --prof-dir "output\中国科学院大学\中科院物理研究所\超快物质科学中心\张鹏举"
```

Expected before 03/04 exist: only 03/04 missing-file failures are acceptable. Phase 2 must not fail its own structure/source checks.

- [ ] **Step 2: Summarize content risks**

Report strongest sources, weak inferences, and points needing user/domain review.

- [ ] **Step 3: Commit checkpoint**

Commit only the Phase 2 plan/draft handling/document files relevant to this task.
