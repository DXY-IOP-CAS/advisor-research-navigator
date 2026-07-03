# Source Citation Format Design

## Goal

Standardize citations across the four professor research documents so readers can trace evidence without long raw URLs interrupting the prose.

The format must support batch use across one research institute, multiple universities, and eventually broad STEM coverage. It should be structured enough for deterministic checks, but not so rigid that every discipline reads like the same template.

## Problem

The documents must include traceable URLs because every factual claim, weak inference, and missing source needs auditability. However, raw URLs in the body are long, visually noisy, and make the documents harder for students to read.

The current project rules avoid bare URLs and use clickable superscript citation keys such as `<sup><a href="#o1">[O1]</a></sup>`, `<sup><a href="#p2">[P2]</a></sup>`, and `<sup><a href="#r3">[R3]</a></sup>`. The source table must explain what each source supports, and each key must jump to an anchored row in the final source section.

## Design

All four documents use clickable short citation keys in the body and a source table at the end.

Body text uses superscript citation links:

```html
The current direction centers on attosecond/XUV sources, liquid-phase photoelectron spectroscopy, and ultrafast dynamics in complex systems.<sup><a href="#o1">[O1]</a></sup><sup><a href="#p3">[P3]</a></sup><sup><a href="#r2">[R2]</a></sup>
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
## 参考文献与资料
```

The section groups sources by type:

```markdown
### 官方与身份来源

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|

### 论文与数据来源

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|

### 综述、教材与课程来源

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|

### 背景与辅助来源

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|
```

The `支撑内容` column is required. The `编号` column anchors each citation key so body references can jump to the row. It explains what the source supports in the document, for example:

```markdown
| <a id="p3"></a>[P3] | Intermolecular Coulombic decay in liquid water competes with proton transfer and non-adiabatic relaxation | 支撑液体水 ICD 与质子转移/非绝热弛豫竞争这条主线 | https://www.nature.com/articles/s41467-025-61912-w | 关键论文 |
```

Missing sources remain explicit in the body as `[未找到]`. Reasonable but insufficiently supported claims are marked `需人工复核`.

## Scope By Document

`01_基础画像.md` may retain DOI or source links inside the generated paper table because Phase 1 includes a data table whose purpose is direct source access. Narrative sections should still prefer citation keys where practical.

`02_领域地图.md` must use citation keys in prose. This document is the most vulnerable to URL noise because it combines official profile sources, field sources, reviews, and papers.

`03_论文路线.md` must use citation keys in prose. Paper-route claims should be supported by `[P#]` sources; field interpretation should be supported by `[R#]` or strong paper evidence.

`04_学习向导.md` must use citation keys in prose. Learning-path claims should rely heavily on `[R#]` sources such as textbooks, lecture notes, reviews, tutorials, and course materials.

## Quality Checks

Future deterministic checks should verify:

1. Body prose has no bare URLs, except generated source/data tables where explicitly allowed.
2. Every citation key used in the body appears in the final source tables.
3. Body citation keys use superscript internal links, and source-table keys use matching anchors such as `<a id="p3"></a>[P3]`.
4. Every source-table citation key is used in the body or in a generated data table.
5. Important factual claims have a citation key, `[未找到]`, or `需人工复核` nearby.
6. Paper-route claims rely mainly on `[P#]`.
7. Learning-path claims rely mainly on `[R#]`.

These checks are smoke tests only. Passing them does not prove scholarly quality.

## Non-Goals

This design does not require formal journal-style references, BibTeX, CSL, or author-year citation formatting.

This design does not force every document to have identical section names beyond the final `参考文献与资料` section.

This design does not require immediate mechanical rewriting of all existing Phase 1 script output.

## Maintained Rule Locations

This design is maintained through:

- `.claude/skills/research-advisor/references/evidence-rules.md`
- `.claude/skills/research-advisor/references/quality-gates.md`
- `docs/计划书.md`
- `.claude/skills/research-advisor/scripts/verify_phase_docs.py`

The verifier remains a deterministic smoke check; it validates citation shape and required anchors, not scholarly quality.

## Self-Review

- No placeholders remain.
- The design chooses the table-based source format approved by the user.
- The distinction between Phase 1 generated data tables and Phase 2-4 prose is explicit.
- The design separates deterministic source-format checks from scholarly quality.
