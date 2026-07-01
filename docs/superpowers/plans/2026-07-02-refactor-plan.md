# 阶段 1 重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清理冗余 + 文档三层重构 + 抽公函数 + skills 对齐，使阶段 1 流水线简洁可靠

**Architecture:** 按 spec 附录 B 的五阶段顺序执行：文档结构重组（pipeline.md 成为单一事实源）→ 废弃文件归档 → utils 抽重 → skills 对齐 → 真机验证。每阶段 commit，不做跨阶段跳跃。

**Tech Stack:** Python 3.12+, scholarly, standard library only. 不引入新依赖。

## Global Constraints

- pipeline.md 是阶段 1 唯一技术事实源，不引用外部文件
- 三层文档结构：计划书(设计决策) / pipeline.md(技术细节) / skills(AI 指令)，层间不重复
- 废弃不移除，全部移入 `archive/_refactor_2026-07-02_清理/`
- archive/ 已有内容不碰
- 不修改任何 step 脚本的核心逻辑（只换函数调用）
- 验证 Subagent 从 git HEAD 运行，只给三个原始输入（姓名+机构+URL），不预填 ID
- 验证串行（张鹏举→常国庆），不得并行

---

### Task 1: pipeline.md 合并 .claude/rules/ 全部内容

**Context:** 当前 pipeline.md 只有索引（引用 .claude/rules/4 个文件）。需将其变为完整技术文档，合并 rules/00-03.md 的全部内容。

**Files:**
- Modify: `src/phase1/pipeline.md`
- Informational read: `.claude/rules/00-overview.md`
- Informational read: `.claude/rules/01-data-pipeline.md`
- Informational read: `.claude/rules/02-quality-gates.md`
- Informational read: `.claude/rules/03-archive.md`

**Interfaces:**
- Consumes: `.claude/rules/00-03.md` 的全部文字内容
- Produces: `src/phase1/pipeline.md` 作为阶段 1 的独立完整技术文档

- [ ] **Step 1: 读全 4 个 rules/ 文件和当前 pipeline.md**

读 `.claude/rules/00-overview.md`、`01-data-pipeline.md`、`02-quality-gates.md`、`03-archive.md` 和 `src/phase1/pipeline.md`，确认内容边界。

- [ ] **Step 2: 重写 pipeline.md**

**注意**：pipeline.md 应包含：
- 三阶段流程总览（来自 00-overview.md）
- 通用数据格式（SOURCE_OUTPUT、MERGED_OUTPUT 定义）
- 阶段 B 完整 CLI 命令 + 示例
- 阶段 C 渲染流程（render_profile → AI 叙事 → merge_tables → verify_profile）
- AI 质量门清单（GS / OA / arXiv / 渲染）
- 错误处理策略
- 输出目录结构
- 已知限制
- 不再引用 .claude/rules/ —— 自身就是完整文档

- [ ] **Step 3: 验证 pipeline.md 自身完整**

```bash
# pipeline.md 中不应再出现对 .claude/rules/ 的引用
grep -n "\.claude/rules" src/phase1/pipeline.md || echo "✅ 无 rules/ 引用"
```

Expected: `✅ 无 rules/ 引用`（即 grep 返回空）

- [ ] **Step 4: Commit**

```bash
git add src/phase1/pipeline.md
git commit -m "refactor: merge .claude/rules/ into pipeline.md — single technical source of truth

- 00-overview: three-phase overview
- 01-data-pipeline: SOURCE_OUTPUT/MERGED_OUTPUT format, CLI commands
- 02-quality-gates: quality checklist, error handling
- 03-archive: output structure, rules, known limitations
- pipeline.md no longer references external files
- Ready for .claude/rules/ deletion in next task"
```

---

### Task 2: 删除 .claude/rules/ 目录

**Context:** pipeline.md 已包含全部内容，rules/ 4 个文件不再需要。

**Files:**
- Delete: `.claude/rules/00-overview.md`
- Delete: `.claude/rules/01-data-pipeline.md`
- Delete: `.claude/rules/02-quality-gates.md`
- Delete: `.claude/rules/03-archive.md`
- Delete: `.claude/rules/` (empty directory)

**Interfaces:**
- Consumes: Task 1 已合并全部内容到 pipeline.md

- [ ] **Step 1: 删除全部 4 个 rules/ 文件和空目录**

```bash
rm .claude/rules/00-overview.md
rm .claude/rules/01-data-pipeline.md
rm .claude/rules/02-quality-gates.md
rm .claude/rules/03-archive.md
rmdir .claude/rules/
```

- [ ] **Step 2: 确认删除干净**

```bash
ls .claude/rules/ 2>&1
```

Expected: `ls: cannot access '.claude/rules/': No such file or directory`

- [ ] **Step 3: 检查是否有其他文件引用 .claude/rules/**

```bash
grep -rn "\.claude/rules" src/ .claude/ docs/ --include="*.md" --include="*.py" 2>/dev/null || echo "✅ 无残留引用"
```

Expected: `✅ 无残留引用`

- [ ] **Step 4: Commit**

```bash
git rm .claude/rules/00-overview.md .claude/rules/01-data-pipeline.md .claude/rules/02-quality-gates.md .claude/rules/03-archive.md
git commit -m "refactor: delete .claude/rules/ — content merged into pipeline.md"
```

---

### Task 3: 重写计划书第二章（纯设计决策）

**Context:** 计划书第二章目前混合了设计决策 + CLI 命令 + 字段格式 + 历史版本记录（"v3.3 修正"类文字）。重写为只含设计决策，删除实现细节。

**Files:**
- Modify: `docs/计划书.md` 第二章

**Interfaces:**
- Consumes: 计划书第一章（保留不动）
- Produces: 计划书第二章（纯设计决策，引用 pipeline.md 作为技术细节来源）

- [ ] **Step 1: 读当前计划书，确认第一章和第二章边界**

读 `docs/计划书.md`，识别：
- 第一章内容（保留）
- 第二章哪些是设计决策（保留/D）哪些是实现细节（删除）

设计决策示例：
- "GS 为什么比 OpenAlex 更适合做主源"（对比表格可保留）
- "同名干扰为什么用合著者+期刊+关键词三维过滤"
- "为什么分阶段 1/2/3/4"
- "为什么 GS 邮箱校验是身份金标准"
- "存档不是缓存原则的解释"

实现细节（删除）：
- 所有 CLI 命令（`python src/phase1/step2_gs.py ...`）
- 所有字段格式定义（SOURCE_OUTPUT 字段表）
- 所有 "v3.3 修正" "v3.4 修正" 等历史版本标记
- 所有 API 参数（URL、headers、限速等）

- [ ] **Step 2: 重写第二章**

新第二章结构（hint：h2 为 "## 第 2 章：工具设计"，h3 为每节）：

```
## 第 2 章：四阶段流水线设计

### 2.1 整体架构

2-3 段说明四段嵌套逻辑：
第 1 段（已实现）：输入 → 基础画像
第 2 段（待设计）：领域脉络
第 3 段（待设计）：论文定位
第 4 段（待设计）：学习讲义

强调阶段间认知递进关系。

### 2.2 数据采集策略

设计决策记录：
- **GS 主源、OA 辅助**：为什么 GS 论文完整性远优于 OA（对比表）
- **身份验证**：官网 email → GS profile 邮箱校验是金标准
- **同名干扰**：合著者+期刊+关键词三维过滤策略（GS 邮箱已验证时不执行）
- **降级策略**：GS 不可用时 OA 替补

### 2.3 输出文档规范

设计决策记录：
- 三层文档结构（给人/给维护者/给 AI）
- YAML frontmatter 标准键
- 来源标 URL、缺失标 [未找到]
- 不做导师评价

### 2.4 阶段 2/3/4 设计方向（待设计）
```

每个 h3 不超过 1-2 个表格 + 2-3 段解释性文字。**不写 CLI 命令、字段格式、API 参数。**

- [ ] **Step 3: 检查第二章与 pipeline.md 的重叠**

确认第二章无任何 CLI 命令、字段格式、API 参数。这些应引用 "详见 pipeline.md"。

- [ ] **Step 4: Commit**

```bash
git add docs/计划书.md
git commit -m "refactor: plan ch2 — design decisions only, trim 80% volume

- remove all CLI commands (belong in pipeline.md)
- remove all field format definitions (belong in pipeline.md)
- remove all historical version markers (v3.3/v3.4)
- retain: GS vs OA comparison, identity validation strategy,
  overlap filtering logic, downgrade strategy, output norms"
```

---

### Task 4: 精简 CLAUDE.md + 统一 QUICKSTART.md

**Context:** CLAUDE.md 含技术细节（run_all.py 引用、scholarly 安装等），需精简为纯地图。QUICKSTART.md 含多源描述，需与 pipeline.md 口径一致。

**Files:**
- Modify: `CLAUDE.md`
- Modify: `QUICKSTART.md`

**Interfaces:**
- Consumes: Task 1 产出的新 pipeline.md（技术细节已定义）
- Produces: CLAUDE.md（~10 行地图）+ QUICKSTART.md（指向 pipeline.md 的快速入口）

- [ ] **Step 1: 简化 CLAUDE.md**

新 CLAUDE.md 内容：

```markdown
# pilot-test CLAUDE.md

## 一句话

导师研究方向调研工具。用户输入姓名+机构+官网URL → 四阶段流水线产出 Markdown 文档。详见 `src/phase1/pipeline.md`（技术细节）和 `docs/计划书.md`（设计决策）。

## 目录角色

| 路径 | 用途 |
|:-----|:------|
| `src/phase1/` | 阶段 1 Python 脚本（step2_gs / step3_openalex / step5_arxiv / step6_merge / render_profile / merge_tables / verify_profile / archive_previous / utils） |
| `src/phase1/pipeline.md` | 阶段 1 技术执行文档（单一事实源） |
| `.claude/skills/research-advisor/` | Claude Code Skill 入口 |
| `output/` | 导师画像产出 |
| `archive/` | 旧版存档（只写不读） |

## 硬约束

- 来源必标 URL，缺失标 `[未找到]`
- 不做导师评价（匹配度、推荐意见等）
- 每次重要改动前 commit
```

- [ ] **Step 2: 统一 QUICKSTART.md**

检查并修改 QUICKSTART.md，确保：
- 所有 CLI 命令与 pipeline.md 一致
- 项目结构示意图反映当前状态（无 .claude/rules/）
- 所有引用指向 pipeline.md（而非已删除的 rules/）

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md QUICKSTART.md
git commit -m "refactor: trim CLAUDE.md to map-only, unify QUICKSTART.md with pipeline.md"
```

---

### Task 5: 废弃文件归档

**Context:** 将项目根下不再使用的文件移入 archive/ 目录，清理项目工作区。

**Files:**
- Archive: `scripts_tmp/` → `archive/_refactor_2026-07-02_清理/scripts_tmp/`
- Archive: `.cache/gs_cookies.json` → `archive/_refactor_2026-07-02_清理/.cache/`
- Archive: `docs/调研_学者分析工具全景.md` → `archive/_refactor_2026-07-02_清理/调研文档/`
- Archive: `docs/调研_阶段1工具选型.md` → `archive/_refactor_2026-07-02_清理/调研文档/`
- Archive: `docs/调研_GS数据获取方案多角度评估.md` → `archive/_refactor_2026-07-02_清理/调研文档/`
- Archive: `docs/调研_AI编程效率工具.md` → `archive/_refactor_2026-07-02_清理/调研文档/`
- Archive: `docs/付费方案备忘_规模化扩展.md` → `archive/_refactor_2026-07-02_清理/调研文档/`
- Archive: `docs/阶段1重构计划.md` → `archive/_refactor_2026-07-02_清理/调研文档/`
- Delete: `tests/`（空目录）
- Delete: `src/__pycache__/`
- Delete: `src/phase1/__pycache__/`

- [ ] **Step 1: 创建归档目录结构**

```bash
mkdir -p "archive/_refactor_2026-07-02_清理/scripts_tmp"
mkdir -p "archive/_refactor_2026-07-02_清理/.cache"
mkdir -p "archive/_refactor_2026-07-02_清理/调研文档"
```

- [ ] **Step 2: 移动废弃脚本和缓存**

```bash
mv scripts_tmp/ "archive/_refactor_2026-07-02_清理/scripts_tmp/"
mv .cache/gs_cookies.json "archive/_refactor_2026-07-02_清理/.cache/"
```

- [ ] **Step 3: 移动调研文档**

```bash
mv "docs/调研_学者分析工具全景.md" "archive/_refactor_2026-07-02_清理/调研文档/"
mv "docs/调研_阶段1工具选型.md" "archive/_refactor_2026-07-02_清理/调研文档/"
mv "docs/调研_GS数据获取方案多角度评估.md" "archive/_refactor_2026-07-02_清理/调研文档/"
mv "docs/调研_AI编程效率工具.md" "archive/_refactor_2026-07-02_清理/调研文档/"
mv "docs/付费方案备忘_规模化扩展.md" "archive/_refactor_2026-07-02_清理/调研文档/"
mv "docs/阶段1重构计划.md" "archive/_refactor_2026-07-02_清理/调研文档/"
```

- [ ] **Step 4: 删除空目录和缓存目录**

```bash
rmdir tests/ 2>/dev/null; echo "tests/ removed"
rm -rf src/__pycache__/
rm -rf src/phase1/__pycache__/
```

- [ ] **Step 5: 确认移动和删除**

```bash
# 确认文件不再在原位置
ls scripts_tmp/ 2>&1  # 应报错
ls .cache/ 2>&1        # 应报错或只有空目录
ls "archive/_refactor_2026-07-02_清理/调研文档/"  # 应有 6 个文件
```

- [ ] **Step 6: 添加 .gitignore 规则（可选）**

检查 `.gitignore` 是否需新增 `archive/_refactor_*/` 或 `scripts_tmp/`。不需要，因为这一切已被 git 跟踪过，存档只是 git mv。

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: archive obsolete files to archive/_refactor_2026-07-02_清理/

- scripts_tmp/ → archive (temporary script)
- docs/调研_*.md → archive (deprecated research docs)
- docs/阶段1重构计划.md → archive (obsolete Playwright plan)
- .cache/gs_cookies.json → archive (unused by scholarly)
- delete tests/ (empty dir) and __pycache__/ (compile cache)"
```

---

### Task 6: utils.py 新增 5 个函数

**Context:** 各脚本有重复的 markdown 表格拼接、嵌套取值、论文链接、URL 规范化模式。抽到 utils.py。

**Files:**
- Modify: `src/phase1/utils.py`
- Test: 运行 import 验证 + 手动执行 doctest

**Interfaces:**
- Produces: `format_markdown_table(headers, rows, aligns)` — 生成标准 markdown 表格字符串
- Produces: `safe_get(d, *keys, default=None)` — 嵌套字典安全取值
- Produces: `make_paper_link(paper)` — 从 paper dict 生成 markdown 链接
- Produces: `norm_url(url)` — 确保 URL 以 https:// 开头
- Produces: `source_tag(sources)` — 别名（替代 mark_source_tag 旧名）
- Produces: 常量 `SOURCE_GS`, `SOURCE_OA`, `SOURCE_ARXIV`, `STATUS_OK`, `STATUS_ERR`, `STATUS_BLOCKED`, `STATUS_EMPTY`

- [ ] **Step 1: 在 utils.py 末尾新增常量**

```python
# ── 源名常量（替代散落字符串）──
SOURCE_GS = "google_scholar"
SOURCE_OA = "openalex"
SOURCE_ARXIV = "arxiv"

STATUS_OK = "success"
STATUS_ERR = "error"
STATUS_BLOCKED = "blocked"
STATUS_EMPTY = "empty"
```

- [ ] **Step 2: 新增 format_markdown_table**

```python
def format_markdown_table(
    headers: list,
    rows: list[list],
    aligns: list[str] = None,
) -> str:
    """生成标准 markdown 表格字符串。

    Parameters
    ----------
    headers : list[str]
        表头，如 ["#", "年份", "标题", "期刊", "引用", "来源"]
    rows : list[list]
        数据行，每行元素数与 headers 一致
    aligns : list[str], optional
        对齐方式，默认"左对齐"。支持 "---"(左), "---:"(右), ":---:"(中)

    Returns
    -------
    str
        不含前后空行的 markdown 表格

    Examples
    --------
    >>> print(format_markdown_table(["A", "B"], [["1", "2"]]))
    | A | B |
    |:-:|:-:|
    | 1 | 2 |
    """
    if not headers:
        return ""
    n = len(headers)
    if aligns is None:
        aligns = [":---"] * n
    elif len(aligns) < n:
        aligns = aligns + [":---"] * (n - len(aligns))
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(aligns[:n]) + " |")
    for row in rows:
        padded = list(row) + [""] * (n - len(row))
        lines.append("| " + " | ".join(str(c) for c in padded[:n]) + " |")
    return "\n".join(lines)
```

- [ ] **Step 3: 新增 safe_get**

```python
def safe_get(d: dict, *keys, default=None):
    """嵌套字典安全取值。

    替代散落的 d.get("a", {}).get("b") 模式。

    Examples
    --------
    >>> safe_get({"a": {"b": 1}}, "a", "b")
    1
    >>> safe_get({"a": None}, "a", "b", default="?")
    '?'
    """
    current = d
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current
```

- [ ] **Step 4: 新增 make_paper_link**

```python
def make_paper_link(paper: dict) -> str:
    """从论文 dict 生成 markdown 链接字符串。

    Priority: DOI > arXiv ID > None (return plain title).

    Examples
    --------
    >>> make_paper_link({"title": "Test", "doi": "10.1234/test"})
    '[Test](https://doi.org/10.1234/test)'
    """
    title = paper.get("title") or ""
    doi = paper.get("doi")
    if doi:
        clean = doi.strip()
        if not clean.startswith("http"):
            clean = f"https://doi.org/{clean}"
        return f"[{title}]({clean})"
    arxiv_id = paper.get("arxiv_id")
    if arxiv_id:
        return f"[{title}](https://arxiv.org/abs/{arxiv_id})"
    return title
```

- [ ] **Step 5: 新增 norm_url**

```python
def norm_url(url: str) -> str:
    """确保 URL 以 https:// 开头。

    Examples
    --------
    >>> norm_url("doi.org/10.1234/test")
    'https://doi.org/10.1234/test'
    >>> norm_url("https://example.com")
    'https://example.com'
    """
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return f"https://{url}"
    return url
```

- [ ] **Step 6: 新增 source_tag 别名**

```python
def source_tag(sources: list) -> str:
    """与 mark_source_tag 相同。更清晰的命名。"""
    return mark_source_tag(sources)
```

- [ ] **Step 7: 验证 utils.py 可导入**

```bash
python -c "from src.phase1.utils import format_markdown_table, safe_get, make_paper_link, norm_url, source_tag, SOURCE_GS, SOURCE_OA; print('✅ utils.py import OK')"
```

Expected: `✅ utils.py import OK`

- [ ] **Step 8: 验证 doctest**

```bash
python -m doctest src/phase1/utils.py -v 2>&1 | tail -5
```

Expected: 无失败 doctests

- [ ] **Step 9: Commit**

```bash
git add src/phase1/utils.py
git commit -m "feat: add 5 utility functions + 7 constants to utils.py

- format_markdown_table: standard table builder
- safe_get: nested dict access
- make_paper_link: DOI/arXiv markdown link
- norm_url: URL protocol normalization
- source_tag: alias for mark_source_tag
- SOURCE_GS/OA/ARXIV, STATUS_OK/ERR/BLOCKED/EMPTY constants"
```

---

### Task 7: render_profile.py + merge_tables.py 换用新函数

**Context:** render_profile.py 中有 `paper_url()` 和手动表格拼接；merge_tables.py 表格逻辑可简化——换用 utils.py 新函数。

**Files:**
- Modify: `src/phase1/render_profile.py`
- Modify: `src/phase1/merge_tables.py`

**Interfaces:**
- Consumes: Task 6 的 `format_markdown_table`, `make_paper_link`, `source_tag` 函数

- [ ] **Step 1: render_profile.py — 检查 paper_url 的调用点**

```bash
grep -n "paper_url" src/phase1/render_profile.py
```

Expected 输出格式（确认它只在 `generate()` 函数第 222 行附近被调用）：

分析结果：如果只在表格生成处调用 → 可替换为 make_paper_link 后删除。如果在其他地方也被调用 → 保留别名。

- [ ] **Step 2: render_profile.py — 替换表格中的 paper_url 调用**

```python
# 在 import 中增加：
from utils import ... , make_paper_link, source_tag

# 在 `generate()` 函数中（约第 219-227 行）：
# 原：
url = paper_url(p)
title_display = f"[{title}]({url})" if url else title

# 改为：
title_display = make_paper_link(p)

- [ ] **Step 3: 删除 paper_url() 函数（如果不再被调用）**

确认 `paper_url` 不再被任何代码调用后删除：

```bash
grep -n "paper_url" src/phase1/render_profile.py
```

Expected: 无输出（函数定义行已被删除）

删除函数体（约第 74-88 行）。

- [ ] **Step 4: render_profile.py — 表格拼接 → format_markdown_table()**

找到 render_profile.py 中手动拼接表格的部分（约第 217 行附近）：

```python
# 替换手动拼接的 L("| # | 年份 | 标题 | ...") 代码块
# 改为：

headers = ["#", "年份", "标题", "期刊", "引用", "来源"]
rows = []
for i, p in enumerate(stage_papers, 1):
    title_display = make_paper_link(p)
    journal = (p.get("journal") or "")[:40] or "—"
    cites = p.get("citation_count") or "—"
    tag = source_tag(p.get("sources", []))
    y = p.get("year") or "—"
    rows.append([str(i), str(y), title_display, journal, str(cites), tag])

table = format_markdown_table(headers, rows)
for line in table.split("\n"):
    L(line)
```

注意：需要确保 `filtered_papers` 变量在表格生成前已定义（当前代码中 `filtered_papers` 在第 129 行空声明、第 173 行重新赋值，这里存在 bug——第 141 行引用时还是空列表。Fix 一并改）：

```python
# 去掉第 129-130 行的空声明：
# filtered_papers = []
# removed_titles = []

# 第 141 行改为：
L(f"| 总论文数 | {len(papers)} 篇（合并后）|")
# 而不是引用 filtered_papers
```

- [ ] **Step 5: merge_tables.py — 无需修改**

确认：merge_tables.py 只做 markdown 解析替换（不是生成），故无需引入 format_markdown_table。

- [ ] **Step 6: step6_merge.py — 添加 source_tag 引用**

```python
# 在 step6_merge.py import 中：
from utils import ... , source_tag  # mark_source_tag 保留不动，新代码用 source_tag
```

当前 `merge_paper_group` 不直接调用 mark_source_tag，所以 step6_merge.py 实际无需修改。source_tag 是为 future use 准备的 alias。

- [ ] **Step 7: 验证 render_profile.py 可运行**

```bash
python -c "
import sys
sys.path.insert(0, 'src/phase1')
from render_profile import generate, load_merged, compute_career_stages
print('✅ render_profile.py import OK')
"
```

Expected: `✅ render_profile.py import OK`（确认 paper_url 已移除，不再需要导入）

- [ ] **Step 8: Commit**

```bash
git add src/phase1/render_profile.py
git commit -m "refactor: render_profile.py — use make_paper_link, format_markdown_table from utils"
```

注：如果 paper_url 未被调用（已替换为 make_paper_link），可一并删除。检查引用后再决定。

---

### Task 8: step3_openalex.py + step5_arxiv.py 换用新函数

**Context:** step3_openalex.py 有散落的嵌套 `.get("a", {}).get("b")` 模式，step5_arxiv.py 有手动 URL 前缀判断。改用 safe_get 和 norm_url。

**Files:**
- Modify: `src/phase1/step3_openalex.py`
- Modify: `src/phase1/step5_arxiv.py`

**Interfaces:**
- Consumes: Task 6 的 `safe_get`, `norm_url` 函数

- [ ] **Step 1: step3_openalex.py — 用 safe_get 替代嵌套 .get**

不改逻辑，只改调用风格。举例：

```python
# 原（第 82-85 行）：
loc = paper.get("primary_location") or {}
source = loc.get("source") or {}
doi = paper.get("doi") or loc.get("doi")

# 改为（可选，不影响功能）：
doi = safe_get(paper, "doi") or safe_get(paper, "primary_location", "doi")
```

**注意**：这一步风险/收益比低——改动可能引入 bug 但收益有限。可选执行。

- [ ] **Step 2: step5_arxiv.py — 用 norm_url 替代手动前缀判断**

```python
# 原（第 61 行附近）：
def _extract_arxiv_id_from_url(url: str) -> str:
    m = re.search(r"(?:arxiv\.org/abs/|arxiv\.org/pdf/)([\w.]+)", url)
    ...

# 不改此函数——它不涉及 URL 规范化
```

step5_arxiv.py 当前手动拼接 URL 的方式无 bug，不改。

- [ ] **Step 3: 验证两个脚本 import 正常**

```bash
python -c "
import sys
sys.path.insert(0, 'src/phase1')
from step3_openalex import fetch, _normalize_oa_paper
from step5_arxiv import search, _parse_entry
print('✅ step3_openalex + step5_arxiv import OK')
"
```

Expected: `✅ step3_openalex + step5_arxiv import OK`

- [ ] **Step 4: Commit（即使没有实质改动）**

```bash
git add src/phase1/step3_openalex.py src/phase1/step5_arxiv.py
git commit -m "chore: no-op — step3/step5 unchanged after utils refactor review"
```

---

### Task 9: SKILL.md 重写 + references/phase1.md 瘦身

**Context:** SKILL.md 仍引用旧流程（"AI 按模板写入"），references/phase1.md 重复 pipeline.md 内容。

**Files:**
- Modify: `.claude/skills/research-advisor/SKILL.md`
- Modify: `.claude/skills/research-advisor/references/phase1.md`

**Interfaces:**
- Consumes: Task 1 产出的 pipeline.md（作为引用目标）
- Produces: SKILL.md（路由入口）+ references/phase1.md（AI 专有指令）

- [ ] **Step 1: 读当前 SKILL.md 和 references/phase1.md**

确认哪些内容与 pipeline.md 重复、哪些是 AI 专有。

- [ ] **Step 2: 重写 SKILL.md**

```markdown
---
name: research-advisor
description: >
  Use when a user wants to "调研导师", "了解一个学者",
  "分析导师的研究方向", "生成导师画像", or "做选导师前期调研".
  Runs Phase 1 paper collection + structured profile.
---

# research-advisor

## 用途

用户输入导师姓名 + 机构 + 官网 URL → 全自动三阶段流 → `01_基础画像.md`。
数据采集策略详见 `src/phase1/pipeline.md`（单一技术事实源）。

## 阶段总览

| 阶段 | 产出 | 状态 |
|:----:|:-----|:----:|
| 1 基础画像 | `01_基础画像.md` | ✅ 已实现 |
| 2 领域脉络 | `02_领域脉络.md` | ❌ 待设计 |
| 3 论文定位 | `03_论文定位.md` | ❌ 待设计 |
| 4 学习讲义 | `04_学习讲义.md` | ❌ 待设计 |

## 阶段 1 执行

详见 `references/phase1.md`（AI 叙事规范 + 硬约束）。
技术执行细节见 `src/phase1/pipeline.md`。
```

- [ ] **Step 3: 瘦身 references/phase1.md**

保留以下 AI 专有内容：
- "禁止评价导师"规则
- "禁止写‘代表性论文’等字样"规则
- 叙事写作规范（每阶段表格前有 1-2 句研究主题说明）
- 名字格式：中文 (English)
- 超链接格式要求
- 输出路径规范（引用 pipeline.md 格式）

删除（与 pipeline.md 重复）：
- 所有 CLI 命令
- SOURCE_OUTPUT 格式定义
- 质量门检查清单
- 错误处理策略
- API 参数细节

改为引用：

```markdown
技术执行细节（CLI 命令、数据格式、质量门）详见 `src/phase1/pipeline.md`。
本文件只包含 AI 在执行阶段 1 时必须遵守的叙事规范和硬约束。
```

- [ ] **Step 4: 删除 assets/01_基础画像.md**

```bash
rm .claude/skills/research-advisor/assets/01_基础画像.md
```

保留 `assets/00_身份验证卡.md`。

- [ ] **Step 5: 检查 Skills 目录无断链**

```bash
grep -rn "\.md" .claude/skills/research-advisor/*.md .claude/skills/research-advisor/references/*.md 2>/dev/null | grep -i "\[" | head -20
```

所有引用指向存在的文件。

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/research-advisor/
git commit -m "refactor: skills align — SKILL.md routing-only, phase1.md AI-specific, delete obsolete template

- SKILL.md: routing + phase overview only
- references/phase1.md: remove CLI/format duplicated with pipeline.md
- assets/01_基础画像.md: deleted (script-rendered template replaces it)"
```

---

### Task 10: 验证 — Subagent 跑张鹏举

**Context:** 重构完成后，用真实场景验证。Subagent 从 git HEAD 启动，只给姓名+机构+URL 三个输入。

**Run from:** `git HEAD`（确保所有之前 Task 的 commit 在 HEAD 中）

- [ ] **Step 1: 确认工作区 clean**

```bash
git status --short
```

Expected: 空输出（clean working tree）

- [ ] **Step 2: 启动 Subagent 执行张鹏举**

```bash
# 使用 Agent tool 启动 subagent，任务描述：
# "你是导师研究方向调研工具。用户输入：
#   姓名：张鹏举
#   机构：中科院物理所 / 超快物质科学中心
#   官网：https://edu.iphy.ac.cn/?q=detail_teacher&id=6368
# 请执行阶段 1 全流程：阶段 A 读官网+MCP 搜 GS/ORCID+邮箱验证身份→
# 阶段 B 执行 step2_gs/step3_openalex/step5_arxiv/step6_merge→
# 阶段 C render_profile→AI 叙事→merge_tables→verify_profile。
# 
# 规则文件：src/phase1/pipeline.md、CLAUDE.md、.claude/skills/research-advisor/
# 输出路径：output/中国科学院大学/中科院物理所/超快物质科学中心/张鹏举/01_基础画像.md
# 
# 注意：串行执行，不并发。只给这三个输入，其他 ID 自己找。"
```

Subagent 启动后，等待它完成。过程中的关键日志：
- 阶段 A 找到了什么 GS URL？
- 邮箱验证通过？
- 阶段 B 各 step 成功？
- 阶段 C verify_profile 通过？

- [ ] **Step 3: 检查 verify_profile 结果**

```bash
python src/phase1/verify_profile.py "output/中国科学院大学/中科院物理所/超快物质科学中心/张鹏举/01_基础画像.md" --merged "output/中国科学院大学/中科院物理所/超快物质科学中心/张鹏举/archive/*/04_merged.json" 2>&1
```

Expected: 全部 10 项 ✅，退出码 0

- [ ] **Step 4: 如果失败，读日志 → 修 bug → commit → 重启 Subagent**

记录失败点和修复。

---

### Task 11: 验证 — Subagent 跑常国庆

**Context:** 常国庆无 GS profile，测试降级路径。同理，Subagent 从 git HEAD。

**Run from:** `git HEAD`（Task 10 的修复如果 commit 了，HEAD 已包含）

- [ ] **Step 1: 确认工作区 clean**

```bash
git status --short
```

Expected: 空输出

- [ ] **Step 2: 启动 Subagent 执行常国庆**

任务描述同理，URL 替换为 `https://edu.iphy.ac.cn/?q=detail_teacher&id=3165`，姓名替换为"常国庆"。注意标注"该老师可能无 GS profile"。

- [ ] **Step 3: 检查 verify_profile 结果**

```bash
python src/phase1/verify_profile.py "output/中国科学院大学/中科院物理所/超快物质科学中心/常国庆/01_基础画像.md" --merged "output/中国科学院大学/中科院物理所/超快物质科学中心/常国庆/archive/*/04_merged.json" 2>&1
```

Expected: 9/10 项 ✅（§8 "无 GS 数据"不算失败），退出码 0

- [ ] **Step 4: 重构完成确认**

两位老师均通过 verify_profile → 项目状态更新为"重构完成"。

写入 CLAUDE.md 末尾：

```markdown
## 重构日志

- 2026-07-02: v2.0 重构完成。pipeline.md 合并 .claude/rules/ 为单一事实源。
  计划书第二章重写为纯设计决策。存档废弃文件 archive/_refactor_2026-07-02_清理/。
  utils.py 新增 5 函数。skills/research-advisor/ 对齐。
  验证：张鹏举 + 常国庆 verify_profile 通过。
```
