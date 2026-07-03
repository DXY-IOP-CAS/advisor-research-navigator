# Source Citation Format Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a uniform table-based citation/source format to the professor research workflow without rewriting existing content yet.

**Architecture:** The rule lives in the research-advisor evidence reference, quality gates, and the human-facing plan document. Deterministic verification is extended only after the written rule is in place, and only for Phase 2-4 source-format smoke checks.

**Tech Stack:** Markdown rules, Python verifier script, existing `.claude/skills/research-advisor/` workflow, existing `docs/计划书.md`.

## Global Constraints

- Do not read or use `archive/`.
- Do not write mentor evaluation, matching score, recommendation, or application advice.
- Keep the change scoped to citation/source format rules and optional deterministic source-format smoke checks.
- Do not rewrite `02_领域脉络.md`, `03_论文定位.md`, or generate `04_学习讲义.md` in this plan.
- Phase 1 generated paper tables may keep DOI/source links; Phase 2-4 prose should avoid bare URLs.
- Use table-based source sections with citation keys: `[O#]`, `[P#]`, `[R#]`, `[B#]`.

---

## File Structure

- Modify `.claude/skills/research-advisor/references/evidence-rules.md`: make the citation-key and source-table format explicit.
- Modify `.claude/skills/research-advisor/references/quality-gates.md`: add source-format gates for Phase 2-4 and clarify that smoke checks are not scholarly review.
- Modify `docs/计划书.md`: record the design decision in the output document specification section.
- Optionally modify `.claude/skills/research-advisor/scripts/verify_phase_docs.py`: add deterministic checks for bare URLs and missing/unused citation keys in Phase 2-4 documents.
- Test by running `python .claude/skills/research-advisor/scripts/verify_phase_docs.py --prof-dir "output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举"`.

---

### Task 1: Update Evidence Rules

**Files:**
- Modify: `.claude/skills/research-advisor/references/evidence-rules.md`

**Interfaces:**
- Consumes: Approved spec `docs/superpowers/specs/2026-07-03-source-citation-format-design.md`
- Produces: Canonical citation/source formatting rules for future Phase 2-4 writing

- [ ] **Step 1: Read current evidence rules**

Run:

```powershell
Get-Content -Encoding UTF8 -LiteralPath '.claude/skills/research-advisor/references/evidence-rules.md'
```

Expected: The file already contains citation-key guidance and avoidance of bare URLs.

- [ ] **Step 2: Add explicit table-based format**

Edit the `引用与链接格式` section so it contains these requirements:

```markdown
## 引用与链接格式

最终 Markdown 应像可读的学术笔记，而不是网页检索记录。

- 正文原则上不放裸 URL。除非句子本身必须提供直接跳转，正文只使用短引用键。
- 引用键分类固定：
  - `[O#]`：官网、课题组、机构主页、简历、项目/基金页面、ORCID、Google Scholar、OpenAlex 等官方或身份来源；
  - `[P#]`：论文、DOI、arXiv、期刊/出版社页面、论文元数据；
  - `[R#]`：综述、教材、课程讲义、教程、领域学习资源；
  - `[B#]`：背景术语或辅助来源。
- 每份文档末尾必须有 `## 参考文献与来源`，并按来源类型分组。
- 来源表统一使用 `编号 / 来源 / 用途 / 链接 / 备注` 五列。
- `用途` 列必须说明该来源支撑本文中的什么判断。
- 缺失来源写 `[未找到]`；合理但证据不足的判断写 `需人工复核`。
```

- [ ] **Step 3: Verify no contradictory old wording remains**

Run:

```powershell
Select-String -Path '.claude/skills/research-advisor/references/evidence-rules.md' -Pattern '裸 URL|引用键|参考文献与来源|用途'
```

Expected: Output shows one coherent rule set, not competing formats.

- [ ] **Step 4: Commit**

Run:

```bash
git add .claude/skills/research-advisor/references/evidence-rules.md
git commit -m "docs: standardize advisor source citation format"
```

Expected: Commit succeeds.

---

### Task 2: Update Quality Gates

**Files:**
- Modify: `.claude/skills/research-advisor/references/quality-gates.md`

**Interfaces:**
- Consumes: Updated evidence rules from Task 1
- Produces: Human review criteria for source-format compliance

- [ ] **Step 1: Read current quality gates**

Run:

```powershell
Get-Content -Encoding UTF8 -LiteralPath '.claude/skills/research-advisor/references/quality-gates.md'
```

Expected: The file already distinguishes deterministic smoke checks from scholarly quality.

- [ ] **Step 2: Add source-format shared content gate**

Add these bullets under `共享内容门`:

```markdown
- 正文原则上不得出现裸 URL；URL 集中放在文末 `参考文献与来源`。
- 正文引用键 `[O#]`、`[P#]`、`[R#]`、`[B#]` 必须能在文末来源表找到。
- 文末来源表必须使用 `编号 / 来源 / 用途 / 链接 / 备注` 五列。
- 论文路线判断主要依赖 `[P#]`；学习路径判断主要依赖 `[R#]`。
```

- [ ] **Step 3: Verify source-format gate text**

Run:

```powershell
Select-String -Path '.claude/skills/research-advisor/references/quality-gates.md' -Pattern '裸 URL|参考文献与来源|编号 / 来源 / 用途 / 链接 / 备注'
```

Expected: Output shows all added source-format gates.

- [ ] **Step 4: Commit**

Run:

```bash
git add .claude/skills/research-advisor/references/quality-gates.md
git commit -m "docs: add citation format quality gates"
```

Expected: Commit succeeds.

---

### Task 3: Record Design Decision In Plan Book

**Files:**
- Modify: `docs/计划书.md`

**Interfaces:**
- Consumes: Approved source citation spec and updated advisor skill rules
- Produces: Human-facing design rationale for why the project uses table-based source references

- [ ] **Step 1: Locate output document specification**

Run:

```powershell
Select-String -Path 'docs/计划书.md' -Pattern '输出文档规范|画像格式规范|阶段 2/3/4 设计原则|证据强度'
```

Expected: Output points to `2.3 输出文档规范` and `2.4 阶段 2/3/4 设计原则`.

- [ ] **Step 2: Add source-format design paragraph**

Add this paragraph to the output specification or evidence-format area:

```markdown
四份文档统一采用“正文短引用键 + 文末来源表”的引用规范。正文原则上不放裸 URL，而使用 `[O#]`、`[P#]`、`[R#]`、`[B#]` 标明来源类型；文末设置 `参考文献与来源`，按官方与身份来源、论文与数据来源、综述教材与课程来源、背景与辅助来源分组，并统一使用 `编号 / 来源 / 用途 / 链接 / 备注` 五列表格。该设计保留可追溯 URL，同时避免长链接破坏阅读流。它不是正式论文参考文献格式，而是面向学生和批量质检的学术笔记格式。
```

- [ ] **Step 3: Verify paragraph exists once**

Run:

```powershell
Select-String -Path 'docs/计划书.md' -Pattern '正文短引用键 \\+ 文末来源表'
```

Expected: Exactly one match.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/计划书.md
git commit -m "docs: record source citation design decision"
```

Expected: Commit succeeds.

---

### Task 4: Optional Verifier Extension

**Files:**
- Modify: `.claude/skills/research-advisor/scripts/verify_phase_docs.py`

**Interfaces:**
- Consumes: Source-format rules from Tasks 1-3
- Produces: Deterministic smoke checks for Phase 2-4 citation format

- [ ] **Step 1: Read verifier**

Run:

```powershell
Get-Content -Encoding UTF8 -LiteralPath '.claude/skills/research-advisor/scripts/verify_phase_docs.py'
```

Expected: The file checks required files, headings, source markers, and banned evaluation terms.

- [ ] **Step 2: Add citation extraction helpers**

Add helper functions that:

```python
import re

CITATION_RE = re.compile(r"\[(O|P|R|B)(\d+)\]")
BARE_URL_RE = re.compile(r"(?<!\]\()https?://[^\s)]+")

def extract_citation_keys(text: str) -> set[str]:
    return {f"[{kind}{number}]" for kind, number in CITATION_RE.findall(text)}

def split_sources_section(text: str) -> tuple[str, str]:
    marker = "## 参考文献与来源"
    if marker not in text:
        return text, ""
    body, sources = text.split(marker, 1)
    return body, sources
```

- [ ] **Step 3: Add Phase 2-4 source-format checks**

Add checks that fail when:

```text
Phase 2-4 document lacks `## 参考文献与来源`.
Body prose contains a bare `http://` or `https://`.
Any citation key in the body is absent from the source section.
Source section lacks the table header `| 编号 | 来源 | 用途 | 链接 | 备注 |`.
```

Phase 1 should not use this strict bare-URL check because generated paper tables may include direct links.

- [ ] **Step 4: Run verifier on current active professor**

Run:

```powershell
python .claude/skills/research-advisor/scripts/verify_phase_docs.py --prof-dir 'output/中国科学院大学/中科院物理研究所/超快物质科学中心/张鹏举'
```

Expected now: FAIL is acceptable because `04_学习讲义.md` is still missing and current `02/03` may not yet follow the new source format. The failure messages should be specific.

- [ ] **Step 5: Commit**

Run:

```bash
git add .claude/skills/research-advisor/scripts/verify_phase_docs.py
git commit -m "test: check advisor source citation format"
```

Expected: Commit succeeds.

---

## Self-Review

Spec coverage:

- Table-based source format is implemented in Task 1.
- Human review gates are implemented in Task 2.
- Project design rationale is implemented in Task 3.
- Deterministic smoke checks are isolated as optional Task 4.

Placeholder scan:

- No `TBD`, `TODO`, or vague implementation placeholders remain.
- Optional verifier task is scoped and contains exact checks.

Type consistency:

- Citation keys are consistently `[O#]`, `[P#]`, `[R#]`, `[B#]`.
- Source table columns are consistently `编号 / 来源 / 用途 / 链接 / 备注`.
