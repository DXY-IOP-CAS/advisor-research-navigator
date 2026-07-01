# 03 — 输出结构 + 存档 + 已知限制

## 输出目录

```
output/<机构>/<部门>/<姓名>/
├── 01_基础画像.md               # 最终画像
├── latest.txt                    # 最新 timestamp
└── archive/<timestamp>/          # 一次运行的完整快照
    ├── 00_verified_ids.json
    ├── 01_gs.json
    ├── 02_oa.json
    ├── 03_arxiv.json
    └── 04_merged.json
```

## 存档不是缓存（硬规矩）

- 每次运行从头查所有 API。不读任何历史存档。
- archive 目录仅用于错误溯源。
- 违反：旧数据静默污染新结果，发现错误无法通过重跑验证。

## 已知限制

| 问题 | 影响 | 对策 |
|:-----|:-----|:------|
| OpenAlex 对中文学者覆盖 22-38% | OA 论文少 | 以 GS 为主源 |
| OpenAlex 消歧错误（h-index/affiliation 错位） | OA 数据不可靠 | merge 层 GS 覆盖 OA |
| arXiv 同名噪声 80%+ | arXiv 结果噪声大 | -c 分类 + merge filter |
| GS 不返回 DOI | 字段缺失 | OA 补充 |
