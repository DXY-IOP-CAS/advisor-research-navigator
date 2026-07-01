# 03 — 输出结构 + 存档规则

## 输出目录规则

```
高校：output/<学校>/<学院>/<部门>/<姓名>/
  例：output/北京大学/物理学院/凝聚态物理与材料物理研究所/李新征/

研究所：output/中国科学院大学/<研究所>/<部门>/<姓名>/
  例：output/中国科学院大学/中科院物理所/超快物质科学中心/张鹏举/
```

输出文件：
```
<姓名>/
├── 01_基础画像.md               # 最终画像
├── latest.txt                    # 最新 timestamp
└── archive/<timestamp>/          # 一次运行的完整快照
    ├── 00_verified_ids.json
    ├── 01_gs.json
    ├── 02_oa.json
    ├── 03_arxiv.json
    ├── 04_merged.json
    └── 01_基础画像_draft.md
```

## 自动存档（不是手动清理）

**运行前检查**：如果 `output/.../<姓名>/` 已存在 → 自动移到 `archive/旧版产出/<姓名>_<timestamp>/`

```bash
python src/phase1/archive_previous.py "<学校>/<学院>/<部门>/<姓名>"
```

这条命令在阶段 A 开始前执行。这样每次运行取最新数据，旧版自动归档，不手动操作。

## 存档不是缓存（硬规矩）

- 每次运行从头查所有 API。不读历史存档。
- archive 目录仅用于错误溯源，不用于加载。
- 违反：旧数据静默污染新结果，发现错误无法通过重跑验证。

## 已知限制

| 问题 | 影响 | 对策 |
|:-----|:-----|:------|
| OpenAlex 对中文学者覆盖 22-38% | OA 论文少 | 以 GS 为主源 |
| OpenAlex 消歧错误（h-index/affiliation 错位） | OA 数据不可靠 | merge 层 GS 覆盖 OA |
| arXiv 同名噪声 80%+ | arXiv 结果噪声大 | -c 分类 + merge filter |
| GS 不返回 DOI | 字段缺失 | OA 补充 |
