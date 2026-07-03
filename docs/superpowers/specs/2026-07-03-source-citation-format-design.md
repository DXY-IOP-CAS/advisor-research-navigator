# Source Citation Format Design

## Goal

Standardize citations across the four professor research documents so readers can trace evidence without long raw URLs interrupting the prose.

The format must support batch use across one research institute, multiple universities, and eventually broad STEM coverage. It should be structured enough for deterministic checks, but not so rigid that every discipline reads like the same template.

## Problem

The documents must include traceable URLs because every factual claim, weak inference, and missing source needs auditability. However, raw URLs in the body are long, visually noisy, and make the documents harder for students to read.

The current project rules already say to avoid bare URLs and prefer citation keys such as `[O1]`, `[P2]`, and `[R3]`, but the rule is not yet strong enough as a four-document output format. The missing piece is a uniform source table with fields that explain what each source supports.

## Design

All four documents use short citation keys in the body and a source table at the end.

Body text uses citation keys only:

```markdown
The current direction centers on attosecond/XUV sources, liquid-phase photoelectron spectroscopy, and ultrafast dynamics in complex systems [O1][P3][R2].
```

Raw URLs are not used in body prose. A URL may remain inside a generated data table when the table itself is a source index, such as a Phase 1 paper list with DOI links.

Citation key categories are fixed:

```text
[O#] official, identity, institutional, group, CV, profile, project, or funding source
[P#] paper, DOI, arXiv, journal, publisher, Google Scholar, OpenAlex, ORCID paper metadata
[R#] review, textbook, course note, lecture note, tutorial, or field-learning resource
[B#] background term or auxiliary source
```

Each document ends with:

```markdown
## 参考文献与来源
```

The section groups sources by type:

```markdown
### 官方与身份来源

| 编号 | 来源 | 用途 | 链接 | 备注 |
|:---|:---|:---|:---|:---|

### 论文与数据来源

| 编号 | 来源 | 用途 | 链接 | 备注 |
|:---|:---|:---|:---|:---|

### 综述、教材与课程来源

| 编号 | 来源 | 用途 | 链接 | 备注 |
|:---|:---|:---|:---|:---|

### 背景与辅助来源

| 编号 | 来源 | 用途 | 链接 | 备注 |
|:---|:---|:---|:---|:---|
```

The `用途` column is required. It explains what the source supports in the document, for example:

```markdown
| [P3] | Intermolecular Coulombic decay in liquid water competes with proton transfer and non-adiabatic relaxation | 支撑液体水 ICD 与质子转移/非绝热弛豫竞争这条主线 | https://www.nature.com/articles/s41467-025-61912-w | 关键论文 |
```

Missing sources remain explicit in the body as `[未找到]`. Reasonable but insufficiently supported claims are marked `需人工复核`.

## Scope By Document

`01_基础画像.md` may retain DOI or source links inside the generated paper table because Phase 1 includes a data table whose purpose is direct source access. Narrative sections should still prefer citation keys where practical.

`02_领域脉络.md` must use citation keys in prose. This document is the most vulnerable to URL noise because it combines official profile sources, field sources, reviews, and papers.

`03_论文定位.md` must use citation keys in prose. Paper-route claims should be supported by `[P#]` sources; field interpretation should be supported by `[R#]` or strong paper evidence.

`04_学习讲义.md` must use citation keys in prose. Learning-path claims should rely heavily on `[R#]` sources such as textbooks, lecture notes, reviews, tutorials, and course materials.

## Quality Checks

Future deterministic checks should verify:

1. Body prose has no bare URLs, except generated source/data tables where explicitly allowed.
2. Every citation key used in the body appears in the final source tables.
3. Every source-table citation key is used in the body or in a generated data table.
4. Important factual claims have a citation key, `[未找到]`, or `需人工复核` nearby.
5. Paper-route claims rely mainly on `[P#]`.
6. Learning-path claims rely mainly on `[R#]`.

These checks are smoke tests only. Passing them does not prove scholarly quality.

## Non-Goals

This design does not require formal journal-style references, BibTeX, CSL, or author-year citation formatting.

This design does not force every document to have identical section names beyond the final `参考文献与来源` section.

This design does not require immediate mechanical rewriting of all existing Phase 1 script output.

## Implementation Targets

Update these project rules after approval:

- `.claude/skills/research-advisor/references/evidence-rules.md`
- `.claude/skills/research-advisor/references/quality-gates.md`
- `docs/计划书.md`

Optionally extend `.claude/skills/research-advisor/scripts/verify_phase_docs.py` later to check citation keys and bare URLs for Phase 2-4 documents.

## Self-Review

- No placeholders remain.
- The design chooses the table-based source format approved by the user.
- The distinction between Phase 1 generated data tables and Phase 2-4 prose is explicit.
- The design separates deterministic source-format checks from scholarly quality.
