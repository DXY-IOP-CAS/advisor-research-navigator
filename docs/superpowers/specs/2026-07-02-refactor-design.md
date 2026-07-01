# 导师调研工具 — 重构设计文档

## 一句话

清理冗余 + 抽公函数 + skills 对齐 + 真机验证 = 阶段 1 可维护、无人偷懒、可端到端跑老师

**日期**：2026-07-02（v2.0 新增文档重构方案）
**对应**：用户明确项目行为不再是最初"导师调研项目"的目标，而是"让 Claude Code 更强大，端到端用户输入简单指令后全自动满足需求"

---

## 第1章：核心理念

本节记录用户本轮确认的设计哲学，贯穿后续所有变更。

### 1.1 AI 自主 > 硬编码

用户强调：这个项目的最终目标是让 Claude Code 能端到端满足用户需求——用户输入姓名+机构+官网 URL，AI 自主完成全部工作，而不是跑硬编码脚本。硬编码脚本越多，维护成本越高，AI 越没有自主判断的余地。

但 AI 自主不能没有约束。格式规范（最终产品的组织结构、markdown 格式、超链接规范）必须统一，确保不同老师的输出互相对比时结构一致。

### 1.2 AI 能自己解决问题

不要在代码中预设"如果 A 源失败就走 B 源"的刚性逻辑——这个由 AI 在阶段 A 判断并选择工具和路径。脚本只做一件事：数据获取+转换格式。AI 编排它们。

### 1.3 验证必须真机

Subagent 端到端从用户原始输入（姓名+机构+官网URL）跑起。不得在任务描述中预先填入任何 ID 来作弊——这无法检验重构是否破坏了什么。

---

## 第2章：清理清单

### 2.1 原则

- 废弃不移除，全部移入 `archive/_refactor_2026-07-02_清理/`
- archive/ 已有内容不碰
- 废弃内容按子目录分类归档

### 2.2 具体清单

|  类型 | 源路径 | 目标路径 | 原因 |
|  --- | --- | --- | --- |
| 临时脚本 | `scripts_tmp/` | `archive/_refactor_2026-07-02_清理/scripts_tmp/` | 不属于流水线 |
| 过时文档 | `docs/调研_学者分析工具全景.md` | `archive/_refactor_2026-07-02_清理/调研文档/` | 调研已完成，已沉淀到计划书 |
| 过时文档 | `docs/调研_阶段1工具选型.md` | 同上 | 同上 |
| 过时文档 | `docs/调研_GS数据获取方案多角度评估.md` | 同上 | 同上 |
| 过时文档 | `docs/调研_AI编程效率工具.md` | 同上 | 同上 |
| 过时文档 | `docs/付费方案备忘_规模化扩展.md` | 同上 | 同上 |
| 过时文档 | `docs/阶段1重构计划.md` | 同上 | 指向旧 Playwright 架构 |
| 文档拆分 | `.claude/rules/00-overview.md` | 内容合并到 pipeline.md，删除文件 | 4 个文件承载同一个事实源，合并为 1 个 |
| 文档拆分 | `.claude/rules/01-data-pipeline.md` | 内容合并到 pipeline.md，删除文件 | 同上 |
| 文档拆分 | `.claude/rules/02-quality-gates.md` | 内容合并到 pipeline.md，删除文件 | 同上 |
| 文档拆分 | `.claude/rules/03-archive.md` | 内容合并到 pipeline.md，删除文件 | 同上 |
| 旧缓存 | `.cache/gs_cookies.json` | `archive/_refactor_2026-07-02_清理/.cache/` | scholarly 不用 |
| 空目录 | `tests/` | 直接删除 | 空壳 |
| pycache | `src/__pycache__/` | 直接删除 | 编译缓存 |
| pycache | `src/phase1/__pycache__/` | 直接删除 | 编译缓存 |

### 2.3 保留不动

- `docs/计划书.md`（核心设计文档——第二章待重写，见第4章）
- `docs/上下文交接.md`（工作日志）
- `docs/测试指令.md`（15 位老师名单，当前活跃）
- `CLAUDE.md`（精简为地图，不含技术细节）
- `QUICKSTART.md`（检查与当前实现的一致性，口径统一为 pipeline.md）
- `.claude/skills/` 非 research-advisor 的其他 skill（superpowers）
- `config/sources.json`
- `output/` 目录及已有产出
- **archive/ 已有所有内容**

---

## 第3章：抽公函数到 utils.py

### 3.1 原则

- 不改变任何 step 脚本的核心逻辑
- 只抽真正重复的模式，不抽"可能以后会用"的代码
- 现有 API（函数签名）保持向前兼容

### 3.2 新增常量和函数

```python
# ── 源名常量（替代散落字符串）──
SOURCE_GS = "google_scholar"
SOURCE_OA = "openalex"
SOURCE_ARXIV = "arxiv"

STATUS_OK = "success"
STATUS_ERR = "error"
STATUS_BLOCKED = "blocked"
STATUS_EMPTY = "empty"


# ── 通用表格渲染 ──
def format_markdown_table(headers: list, rows: list[list],
                           aligns: list[str] = None) -> str:
    """生成标准 markdown 表格。

    Parameters
    ----------
    headers : list[str]
        表头，如 ["#", "年份", "标题", "期刊", "引用", "来源"]
    rows : list[list]
        数据行，每行元素数与 headers 一致
    aligns : list[str], optional
        对齐方式，默认全部左对齐。支持 ":---" (左), "---:" (右), ":---:" (中)

    Returns
    -------
    str
        不含前后空行的纯表格 markdown

    Examples
    --------
    >>> print(format_markdown_table(["A", "B"], [["1", "2"]]))
    | A | B |
    |:-:|:-:|
    | 1 | 2 |
    """
    ...


# ── 安全嵌套取值 ──
def safe_get(d: dict, *keys, default=None):
    """嵌套字典安全取值。

    >>> safe_get({"a": {"b": 1}}, "a", "b")
    1
    >>> safe_get({"a": None}, "a", "b", default="?")
    '?'
    """
    ...


# ── 论文链接生成 ──
def make_paper_link(paper: dict) -> str:
    """从论文 dict 生成 markdown 链接。

    Priority: DOI > arXiv ID > None (return plain title)
    """
    ...


# ── URL 规范化 ──
def norm_url(url: str) -> str:
    """确保 URL 以 https:// 开头。"""
    ...


# ── 源标记（原名 mark_source_tag，增加别名） ──
def source_tag(sources: list) -> str:
    """同 mark_source_tag。改为 source_tag 更清晰。"""
    ...
```

### 3.3 修改脚本

| 脚本 | 改动 |
|  ---  |  --- |
| `render_profile.py` | `paper_url()` → `make_paper_link()`；表格拼接 → `format_markdown_table()` |
| `merge_tables.py` | 表格提取/replace 逻辑调用 `format_markdown_table()` |
| `step6_merge.py` | `mark_source_tag` → `source_tag`（别名保持兼容） |
| `step3_openalex.py` | `safe_get()` 替代散落嵌套；`norm_url()` 替代硬编码前缀判断 |
| `step5_arxiv.py` | `norm_url()` 替代硬编码前缀判断 |

### 3.4 不动

- `step1_discipline.py`、`step2_gs.py`：独立逻辑，不抽
- `archive_previous.py`：独立工具
- `verify_profile.py`：质量闸，不引入 utils 依赖之外的逻辑
- `utils.py` 中 `normalize_title`、`clean_doi`、`doi_match`、`title_match`、`retry`、`RateLimiter` —— 不改变签名和行为

---

## 第4章：.claude/skills/research-advisor/ 对齐

### 4.1 问题

| 问题 | 现状 | 目标 |
|  --- |  --- |  --- |
| SKILL.md 与 src/phase1/ 错位 | 仍说"AI 按模板写入" | 更正为 render_profile → AI 叙事 → merge_tables → verify_profile |
| references/phase1.md 重复 pipeline.md | 大量 CLI 命令+格式说明与 pipeline.md（即将成为单一事实源）重复 | 只保留 AI 专有指令，引用 pipeline.md |
| assets/01_基础画像.md 不再使用 | 旧模板文件，render_profile.py 已内嵌模板 | 删除该文件 |

### 4.2 修改后结构

```
.claude/skills/research-advisor/
├── SKILL.md              # 索引式入口（路由+阶段总览+核心约束）
├── references/
│   ├── phase1.md         # AI 叙事写作规范+硬约束（引用 pipeline.md 执行细节）
│   └── 01-data-sources.md  # 保留（API 参数细节，未在 pipeline.md 中复述）
└── assets/
    └── 00_身份验证卡.md   # 保留
```

### 4.3 不重复的内容

以下内容只存在于 `pipeline.md`（不再在 skills/ 中复述）：
- 阶段 B CLI 命令
- 统一数据格式 SOURCE_OUTPUT、MERGED_OUTPUT
- 质量门检查清单
- 输出路径 + 存档规则

pipeline.md 是阶段 1 唯一技术事实源。.claude/rules/ 目录整体删除，其 4 个文件的内容全部合并入 pipeline.md。

---

## 第5章：验证方案

### 5.1 流程

```
重构代码 → git commit（HEAD）→ 写两个 Subagent 任务
  → Subagent 1: 张鹏举（全流程，仅给姓名+机构+URL）
    → 阶段 A: MCP 读官网+搜 GS/ORCID → 邮箱验证 → verified_ids.json
    → 阶段 B: step2_gs / step3_openalex / step5_arxiv / step6_merge
    → 阶段 C: render_profile → AI 叙事 → merge_tables → verify_profile
    → verify_profile 10/10 通过
  → Subagent 2: 常国庆（同上，无 GS → 测试降级路径）
    → verify_profile 10/10 通过
  → 重构完成
```

### 5.2 约束

- 两个 Subagent **串行**运行，不并行（避免触达 API 上限）
- 每个 Subagent 任务描述只能含：姓名+机构+官网URL+项目结构说明+规则引用
- 不得预填任何 ID（GS ID、OA ID、ORCID）
- Subagent 从 `git HEAD` 状态运行，避免 dirty tree 干扰
- 失败 → 记录失败点 → 我读 Subagent 日志 → 修 bug → commit → 重启该 Subagent

### 5.3 通过标准

```
① 张鹏举输出 output/中国科学院大学/中科院物理所/超快物质科学中心/张鹏举/01_基础画像.md
② verify_profile 10 项检查全 ✅
③ 常国庆输出 output/中国科学院大学/中科院物理所/超快物质科学中心/常国庆/01_基础画像.md
④ verify_profile 10 项检查全 ✅（常国庆无 GS profile 时，§8 数据质量说明标注"无 GS 数据"不算失败；其余 9 项照常检查）
```

---

## 第6章：文档重构（三层各司其职）

### 6.1 现状问题

当前文档体系 11 个 .md 文件互相引用，同一个技术细节平均存在 3-4 个版本：

| 内容 | 当前存在位置 |
|:-----|:------------|
| 统一输出格式 | `pipeline.md` + `rules/01-data-pipeline.md` + `skills/references/phase1.md` + `计划书第二章` |
| CLI 命令 | `rules/01-data-pipeline.md` + `skills/references/phase1.md` + `计划书第二章` |
| 质量门清单 | `rules/02-quality-gates.md` + `skills/references/phase1.md` + `计划书第二章` |
| API 参数 | `skills/references/01-data-sources.md` + `计划书附录A` |

更新一个漏另一个 → AI 拿到矛盾指令 → 输出质量不稳。这是"产品效果不好、格式不一致、信息有错误"的根因。

### 6.2 三层结构（最终确定）

| 层 | 受众 | 文件 | 内容 |
|:---|:------|:-----|:-----|
| 设计决策 | 人 | `docs/计划书.md` | 这项目做什么、为什么这么设计（不写字段格式/CLI） |
| 技术参考 | 维护者 | `src/phase1/pipeline.md` | 单一事实源：格式定义、CLI 命令、质量门、API 参数、存档规则 |
| AI 指令 | Claude Code | `SKILL.md` + `references/` | 执行顺序、叙事规范、硬约束。引用 pipeline.md，不重复 |

### 6.3 具体变更

**pipeline.md**（从索引版 → 完整技术文档）
- 合并 `.claude/rules/00-overview.md` 中三阶段总览
- 合并 `.claude/rules/01-data-pipeline.md` 中 CLI 命令和数据格式（SOURCE_OUTPUT、MERGED_OUTPUT）
- 合并 `.claude/rules/02-quality-gates.md` 中质量门检查清单和错误处理
- 合并 `.claude/rules/03-archive.md` 中输出路径和存档规则
- 增加 `skills/references/01-data-sources.md` 的 API 参数摘要（详细参数仍在原地，pipeline.md 只引用）
- pipeline.md 成为独自完整的阶段 1 技术文档——不引用任何外部文件

**`.claude/rules/` 目录** → 删除（4 个文件全部删除，内容已合并到 pipeline.md）

**`docs/计划书.md` 第二章** → 重写
- 只保留设计决策："GS 为什么是主源"、"同名干扰为什么三维过滤"、"为什么分阶段"
- 删除所有 CLI 命令、字段格式、API 参数
- 删除所有历史版本迭代记录（"v3.3 修正"类文字）
- 改为引用 pipeline.md 作为技术细节来源

**`CLAUDE.md`** → 精简
- 只含：项目一句话 + 目录角色 + 启动命令 + 硬约束（来源标 URL、不做评价）
- 删除技术细节重复

**`QUICKSTART.md`** → 口径与 pipeline.md 统一

**`skills/references/phase1.md`** → 瘦身
- 只保留 AI 专有内容：叙事写作规范、硬约束（禁止评价导师、"代表性论文"等）
- 删除所有 CLI 命令和格式定义，改为引用 pipeline.md

**`skills/references/01-data-sources.md`** → 保留不变（API 参数细节）

### 6.4 变更前后对比

```
重构前（11 个文件相互引用）             重构后（4 个文件各司其职）

pipeline.md (索引版)                    pipeline.md (单一事实源)
  ├→ .claude/rules/00-overview.md          (已合并，文件删除)
  ├→ .claude/rules/01-data-pipeline.md     (已合并，文件删除)
  ├→ .claude/rules/02-quality-gates.md     (已合并，文件删除)
  └→ .claude/rules/03-archive.md           (已合并，文件删除)

CLAUDE.md (19行，含实现细节)              CLAUDE.md (~10行，纯地图)
QUICKSTART.md (口径多源)                  QUICKSTART.md (指向 pipeline.md)

计划书第二章 (技术细节+设计决策混合)      计划书第二章 (纯设计决策)
    
skills/references/phase1.md               skills/references/phase1.md
  ├ 重复 CLI 命令                              (删除，引用 pipeline.md)
  ├ 重复 SOURCE_OUTPUT 格式                    (删除，引用 pipeline.md)
  └ AI 叙事规范                                (保留)
```

### 6.5 验证：文档无重复检查

重构完成后逐文件检查：
- [ ] pipeline.md 作为单一事实源——不引用任何外部技术文件
- [ ] skills/references/ 不包含 pipeline.md 已写的 CLI/格式/质量门
- [ ] 计划书第二章不包含字段格式定义和 CLI 命令
- [ ] CLAUDE.md 不含技术实现细节
- [ ] QUICKSTART.md 与 pipeline.md 口径一致

---

## 附录 A：不做的

| 事项 | 原因 |
|  --- |  ---  |
| 重写 step 脚本核心逻辑 | 产品效果问题不在脚本内部 |
| 新增 step 脚本（如 S2 集成） | YAGNI——不在清理重构范围内 |
| 改动 archive/ 已有内容 | 用户反复强调 archive/ 不动 |
| docs/ 测试指令.md 扩充 | 不在范围内 |

## 附录 B：重构执行顺序

按以下顺序执行，每一步 commit 后再下一步：

```
Phase 1: 文档重构（不动代码）
  Step 1: pipeline.md 合并 rules/00-03.md 全部内容 → 单一事实源
  Step 2: 删除 .claude/rules/ 目录（4 个文件）
  Step 3: 计划书第二章重写（纯设计决策）
  Step 4: CLAUDE.md 精简 + QUICKSTART.md 统一口径
  → commit

Phase 2: 代码清理（不动核心逻辑）
  Step 5: 废弃内容移到 archive/_refactor_2026-07-02_清理/
  Step 6: 删除 tests/ 空目录 + __pycache__ + .cache/
  → commit

Phase 3: 抽公函数
  Step 7: utils.py 新增 format_markdown_table / safe_get / make_paper_link / norm_url / source_tag
  Step 8: render_profile.py / merge_tables.py / step3_openalex.py / step5_arxiv.py 改用新函数
  → commit

Phase 4: skills 对齐
  Step 9: SKILL.md 重写 + references/phase1.md 瘦身
  Step 10: 删除 assets/01_基础画像.md
  → commit

Phase 5: 验证
  Step 11: Subagent 跑张鹏举（串行，仅给三个原始输入）
  Step 12: Subagent 跑常国庆（同上）
  Step 13: 两位 verify_profile 通过 → 重构完成
```

---

**版本**: v2.0
**生成日期**: 2026-07-02
**主要修订**: v2.0 新增文档重构方案（pipeline.md 合并 .claude/rules/、删除 rules/ 目录、计划书第二章重写、CLAUDE.md 精简）
**下一版本触发器**: 验证发现需要调整的范围
