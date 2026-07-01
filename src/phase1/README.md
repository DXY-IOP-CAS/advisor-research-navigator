# src/phase1 — 阶段 1 pipeline

这是导师调研工具阶段 1 的全部代码。详见根目录 `QUICKSTART.md` 和本目录 `pipeline.md`。

## 文件结构

```
phase1/
├── __init__.py
├── pipeline.md              ← 技术实现文档（执行步骤 + 数据契约 + 错误处理）
├── schema.py                ← 数据契约定义（Paper/Professor/SourceOutput/MergedOutput + validation）
├── errors.py                ← 自定义异常 + 修复建议工具
├── utils.py                 ← 共享：标题归一化、DOI/arXiv 比对、retry 装饰器、OA 错位过滤、PoP 限速
├── step1_discipline.py      ← 阶段 A 学科分类（无网络）
├── step2_gs.py              ← 阶段 B GS 数据（scholarly 库）
├── step3_openalex.py        ← 阶段 B OpenAlex 数据
├── step5_arxiv.py           ← 阶段 B arXiv 数据
├── step6_merge.py           ← 阶段 B 三源合并去重
├── render_profile.py        ← 阶段 C 渲染画像（脚本生成表格，AI 补充叙事）
└── tests/
    ├── __init__.py
    ├── test_utils.py        ← utils.py 单元测试（19 个）
    ├── test_schema.py       ← schema.py 单元测试（19 个）
    ├── test_errors.py       ← errors.py 单元测试（13 个）
    ├── test_merge.py        ← step6_merge 核心去重测试（15 个）
    └── run_all.py           ← 一键跑所有测试
```

## 快速开始

### 跑测试（不需要网络）

```bash
python src/phase1/tests/run_all.py
```

期望输出：`GRAND TOTAL: 66 passed, 0 failed`

### 跑单个 step

每个 step 都是独立 CLI，输入输出是 JSON 文件：

```bash
# 阶段 A：学科分类（无网络）
python src/phase1/step1_discipline.py --text "阿秒科学、强场物理" --affiliation "中科院物理所"

# 阶段 B：数据获取
python src/phase1/step2_gs.py ls7XuGoAAAAJ -o output/张鹏举/01_gs.json
python src/phase1/step3_openalex.py A5000914228 --email pengju.zhang@iphy.ac.cn -o output/张鹏举/02_oa.json
python src/phase1/step5_arxiv.py "Zhang_Pengju" -c "physics.atom-ph physics.optics" -o output/张鹏举/03_arxiv.json
python src/phase1/step6_merge.py 01_gs.json 02_oa.json 03_arxiv.json -o 04_merged.json

# 阶段 C：渲染画像
python src/phase1/render_profile.py 04_merged.json -o 01_基础画像.md --department "超快物质科学中心"
```

详见 `pipeline.md`。

## 数据契约

每个 step 之间通过统一格式的 JSON 文件通信。详见 `pipeline.md §2` 和 `schema.py`：

- **单篇论文**：title / year / authors / journal / doi / arxiv_id / citation_count / source
- **SOURCE_OUTPUT**（每个数据源 step 的产出）：source / status / professor / papers / metadata
- **MERGED_OUTPUT**（step6 的产出）：sources_used / source_status / professor / papers（带 sources/source_count）/ statistics

每个 step 的输出应在自己的 `--output` 参数指定路径，不要覆盖他人。

## 错误处理原则

- 脚本不抛异常退出——所有错误用 `status: "error"` 字段表示
- 网络错误自动重试（utils.py 的 `@retry` 装饰器，3 次指数退避）
- OpenAlex 邮箱检测：真实邮箱 → polite pool 10 req/s；假邮箱/无 → 1 req/s
- arXiv 同名噪声：传 `-c` 学科分类参数减少噪声；merge 步骤自动通过 DOI/标题过滤
- 错位论文过滤：`is_oa_pollution()` 检测 DNA hydrogel / Wind Imaging 等明显错位关键词，render_profile.py 直接剔除

## 测试覆盖

| 文件 | 测试数 | 覆盖范围 |
|:-----|:------:|:---------|
| test_utils.py | 19 | normalize_title, doi_match, arxiv_id_match, title_match, is_oa_pollution |
| test_schema.py | 19 | Paper, Professor, SourceOutput, MergedOutput, validate_* |
| test_errors.py | 13 | Phase1Error 子类, report_source_status, suggest_remediation |
| test_merge.py | 15 | clean_doi, strip_arxiv_version, mark_source_tag, _pick, merge_professors, PROF_PRIORITY |

总计 66 个测试。所有测试纯逻辑，无网络依赖，可离线跑。

## 依赖

详见根目录 `pyproject.toml`：

- `scholarly>=1.7.11` — Google Scholar 数据获取
- `beautifulsoup4>=4.12.0` — HTML 解析（备用）
- Python 3.10+ 标准库

## 修改代码后的工作流

```
1. 改 src/phase1/*.py 中的某个文件
2. python src/phase1/tests/run_all.py  ← 验证没破坏现有逻辑
3. 改 src/phase1/tests/test_*.py 加测试覆盖新逻辑
4. 改 src/phase1/pipeline.md 更新文档（如有架构变更）
5. git commit -m "..."
```

修改代码前先跑一次测试看基线，改完再跑一次对比。