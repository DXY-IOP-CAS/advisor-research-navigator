# Evidence Rules for Phase 2-4

## Source Hierarchy

Prefer sources in this order:

1. Professor official page, lab page, institution profile, CV, grant/project page.
2. DOI landing pages, publisher pages, arXiv, OpenAlex, Google Scholar, ORCID.
3. Recent review articles, tutorial articles, textbooks, lecture notes, and
   authoritative field pages for background.
4. Wikipedia or encyclopedia pages only for first-pass terminology checks; never
   use them as the sole source for a technical or career claim.

Every factual claim that affects the student's understanding of the professor,
field, paper positioning, or learning path needs a URL nearby. If no source is
found, write `[未找到]`. If a claim is plausible but not directly established,
write `需人工复核`.

## Citation and Link Style

Write final Markdown like a readable academic note, not a web-search transcript.

- Prefer citation keys in prose, such as `[P1]`, `[R2]`, `[O1]`, then put the
  clickable Markdown links in a final `参考文献与来源` section.
- Avoid bare raw URLs in body paragraphs. Use hidden Markdown links only when a
  sentence genuinely needs a direct clickable source.
- Use source categories:
  - `[O#]` official professor, lab, institution, ORCID, GS, OpenAlex;
  - `[P#]` papers, DOI pages, arXiv, publisher pages;
  - `[R#]` reviews, tutorials, textbooks, lecture notes;
  - `[B#]` background or terminology sources.
- Prefer official, DOI, publisher, arXiv, ORCID, GS, OpenAlex, and institution
  pages over secondary pages. Wikipedia is terminology background only.
- Every document must keep enough links for source checking, but the visible
  text should remain clean and easy to read.

## Search Discipline

- Search again when Phase 2 would otherwise be only a summary of
  `01_基础画像.md`.
- Search again when Phase 3 or Phase 4 would otherwise become repeated
  digestion of Phase 1 and Phase 2.
- Search for both the professor and the field: professor name + current unit,
  current direction keywords, recent paper titles, review keywords, and core
  method keywords.
- Use broad-to-narrow search: first locate the parent discipline and subfield,
  then identify the smaller research problem and the professor's role in it.
- When a term has multiple meanings, resolve it by matching papers, institution,
  coauthors, and research systems before writing.
- Do not use old outputs, caches, or `archive/` as evidence.
- For Phase 3, search for talks, group news, invited seminars, abstracts, review
  articles, and paper introductions when the paper route is unclear. Treat them
  as interpretive support, not as stronger evidence than papers or official
  pages.
- For Phase 4, search for field-standard textbooks, lecture notes, review
  articles, and course materials. The learning path should reflect disciplinary
  consensus and actual prerequisite structure, not invented AI sequencing.

## Inference Labels

Use explicit labels:

- `直接证据`: stated by official profile, paper title/abstract, DOI page, or
  review source.
- `交叉证据`: supported by multiple weaker sources or repeated paper patterns.
- `弱证据`: inferred from sparse metadata, coauthor context, or adjacent papers.
- `需人工复核`: needed when weak evidence affects structure, chronology, or
  learning sequence.

## Prohibited Moves

- Do not write application advice, advisor ranking, matching score, or
  recommendation language.
- Do not infer a professor's current direction only from the earliest or most
  cited papers.
- Do not turn Phase 2 into an encyclopedia article. The field map is filtered
  through what an incoming student needs for this professor's current direction.
- Do not turn Phase 3 into paper abstracts. Explain each relevant paper's role
  in the research route.
- Do not turn Phase 4 into a generic course syllabus. Backward-design it from
  the current direction and the papers selected in Phase 3.
