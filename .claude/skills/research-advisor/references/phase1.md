# 阶段 1 执行步骤

本文件被 `../SKILL.md` 在阶段 1 时读取。内容对应计划书 2.2 节和 `src/phase1/pipeline.md`。

**注意**：无人工闸。全自动运行。

---

## 阶段 1 总体流程

```
阶段 A（AI 主导）：
  Step 1: 官网抓取 + 学科分类
  Step 2: 广域搜索 → 身份确认 → verified_ids.json

阶段 B（脚本 + AI 看门）：
  Step 3: step2_gs.py（scholarly 封装）
  Step 4: step3_openalex.py（OpenAlex 论文+元数据）
  Step 5: step5_arxiv.py（arXiv 预印本）
  Step 6: step6_merge.py（去重合并）

阶段 C（AI 主导）：
  Step 7: 读 merged.json → 写 01_基础画像.md
```

---

### Step 1: 官网抓取 + 学科识别

用 MCP fetch 读用户给的官网 URL。提取：
- 姓名（中文 + 拼音）
- 职称
- 邮箱
- 研究方向关键词

学科识别：

```bash
python src/phase1/step1_discipline.py --text "研究方向关键词" --affiliation "机构名"
```

解析 JSON 输出，取 `primary` 字段。

### Step 2: 广域搜索 + 身份确认

用 MCP Serper/Exa 搜：
- `{姓名} {机构}` → 百度百科、知乎、新闻
- `{姓名} Google Scholar` → 找 GS 链接
- `{姓名} ORCID` → 找 ORCID 链接

**邮箱校验是身份金标准**。找到 GS 链接后，检查 "Verified email at xxx" 是否与官网邮箱域名一致。一致即确认身份。

输出 `00_verified_ids.json`，包含所有确认的 ID 和公开信息源。

### Step 3: GS 数据获取（scholarly）

GS 永远是论文列表主源。OpenAlex 只做元数据补充。

```bash
python src/phase1/step2_gs.py {gs_id} -o output/<机构>/<部门>/<姓名>/archive/<timestamp>/01_gs.json
```

scholarly 返回：56 篇论文 + h-index + i10-index + 引用数 + email_domain。

**AI 质量门检查**：
- email_domain 是否匹配官网？→ 不匹配标记"身份存疑"
- 论文数 > 5？→ 太少标记"profile 可能不完整"

**GS 不可用时（403 封锁）**：换梯子节点重试。都不可用时降级到 OpenAlex。

### Step 4: OpenAlex 数据获取

```bash
python src/phase1/step3_openalex.py {oa_id} -o output/<机构>/<部门>/<姓名>/archive/<timestamp>/02_oa.json --email you@example.com
```

返回：论文列表（含 DOI/期刊/作者）+ profile（h-index/ORCID/机构）。

**AI 质量门检查**：
- h-index 与 GS 差异 > 50%？→ 标记"OA 数据可能错位，以 GS 为准"
- 论文主题是否匹配导师研究方向？→ 不匹配标记"OA ID 可能错位"

### Step 5: arXiv 预印本

```bash
python src/phase1/step5_arxiv.py "姓名拼音" -c "physics.atom-ph physics.optics" -o output/<机构>/<部门>/<姓名>/archive/<timestamp>/03_arxiv.json
```

**AI 质量门检查**：
- 同名噪声率？→ 标记噪声程度
- 是否与 GS/OA 确认论文有 DOI/标题匹配？→ 有匹配则反向筛选，无匹配则仅供参考

### Step 6: 合并去重

```bash
python src/phase1/step6_merge.py \
  output/<机构>/<部门>/<姓名>/archive/<timestamp>/01_gs.json \
  output/<机构>/<部门>/<姓名>/archive/<timestamp>/02_oa.json \
  output/<机构>/<部门>/<姓名>/archive/<timestamp>/03_arxiv.json \
  -o output/<机构>/<部门>/<姓名>/archive/<timestamp>/04_merged.json
```

去重优先级：P0:DOI → P1:arXiv ID → P2:归一化标题。
教授信息按字段优先级合并（GS 占 h-index/引用数，OA 占 DOI/ORCID）。

**AI 质量门检查**：
- 总论文数 > 5？
- 多源交叉验证比例？
- 标记结果（GS 正常 / OA 数据错位 / arXiv 噪声严重）

### Step 7: 渲染画像

**核心原则：脚本输出就是最终画像。AI 只能通过 Edit 工具插入文字，不能 Write 重写文件。**

#### 7.1 生成完整画像（脚本）

脚本直接输出到老师根目录（不是 archive）。

```bash
python src/phase1/render_profile.py output/<机构>/<部门>/<姓名>/archive/<timestamp>/04_merged.json \
  -o output/<机构>/<部门>/<姓名>/01_基础画像.md \
  --department "<部门>"
```

脚本输出包含：
- 运行信息（时间戳 + 各源状态 + 论文总数）
- §1 身份标识（姓名、机构、邮箱、各平台 ID）
- §4 论文表格（**全部论文，每篇一行，标题含 DOI/arXiv 超链接**）
- §5 影响力指标（h-index、引用数）
- §8 数据质量说明（各源论文数 + 验证状态）

202 篇论文就会输出 202 行，不是"代表性论文"。

同一时间拷贝一份到 archive 做备份：
```bash
cp output/.../01_基础画像.md output/.../archive/<ts>/01_基础画像_draft.md
```

#### 7.2 AI 补充叙事（只能用 Edit 工具）

脚本写完后，AI 读取 `01_基础画像.md`，用 **Edit 工具**插入缺少的节和叙事段落。

**为什么不能用 Write 工具：** AI 用 Write 重写整个文件时，每次都会删掉脚本的表格。Edit 要求 old_string 精确匹配，AI 无法修改表格行。

AI 需要补充的内容（用 Edit 在已有节之间插入）：

| 节 | 插入位置 | 插入内容 |
|:---|:---------|:---------|
| §2 学术履历 | 在 §1（身份标识）后面 | 教育 + 工作经历时间线表格 |
| §3 研究方向 | 在 §2 后面 | 总体概述 + 3-4 个具体方向 |
| §6 合作网络 | 在 §5（影响力指标）后面 | 合作者、机构、关系、方向 |
| §7 公开信息 | 在 §6 后面 | 新闻/采访/讲座，每条含超链接 |
| §9 验证来源 | 在 §8（数据质量）后面 | 所有数据源 URL 链接 |

每个 `### 4.x` 阶段表格前，用 Edit 在标题行后插入一段叙事（1-2 句话说明该阶段研究主题和转型）。

**Edit 示例（插入叙事到 §4.1 表格前）：**

```
old_string: 论文数：N 篇
new_string: > **研究主题**：该阶段研究 XXX。
论文数：N 篇
```

**硬约束**：
- 禁止用 Write 工具修改 `01_基础画像.md`
- 禁止修改任何表格行（以 `| \d+ | \d{4} |` 开头的行）
- 禁止插入"代表性论文""列示""省略"等词汇
- 名字格式：`中文 (English)`

**成品标准检查表**（AI 自称完成前必须逐项确认）：
- [ ] 教授姓名格式统一：中文名 (英文名)，如 `张鹏举 (Pengju Zhang)`
- [ ] 所有 paper 标题含超链接（DOI 或 arXiv）
- [ ] §2 学术履历存在（教育 + 工作，有时间线）
- [ ] §3 研究方向是 1 段话 + 3-4 个具体方向
- [ ] §4 每个阶段表格前有叙事段落（不是只有表格）
- [ ] §6 合作网络存在（合作者、机构、关系、方向）
- [ ] §7 公开信息存在（每条含超链接）
- [ ] 无导师评价内容（禁止使用"值得报考""热门""影响力"等词）

4. **合作网络**（名字 + 机构 + 合作方向，含超链接到 GS/ORCID）。

5. **公开信息整理**（新闻/采访/讲座，**每条带上超链接**）。

6. **硬约束**：
   - 禁止做导师评价（"值得报考""热门方向""影响力大"等）
   - 每篇论文保留脚本生成的超链接列（DOI/arXiv）
   - 缺失字段标 `[未找到]`
   - 不在论文表格内写叙事——叙事写在表格前面单独的段落
6. **所有外部信息末尾标注来源超链接**（GS URL、DOI 链接、arXiv 链接、新闻 URL 等）

**硬约束（必须遵守）**：
1. **全部论文逐一列出，不得省略**。不允许出现"以下见完整列表""代表性论文"等字样。
2. **每阶段表格前必须有一段叙事**，说明该阶段的研究主题和方向变化。
3. **每篇论文有外部超链接**（DOI 或 arXiv 或 GS 引用页）。

画像写入 `output/<机构>/<部门>/<姓名>/01_基础画像.md`，中间产物保留在 archive 目录。

---

## 全降级模式

三个数据源全部不可用时：
1. 画像中写明"所有数据源均不可用"
2. 建议用户检查网络或提供其他 ID 链接

---

## 硬规则（守则第五条）

**存档不是缓存。** archive/ 目录仅用于错误溯源，每次运行必须从头查询所有 API。不得从历史存档中加载数据充当缓存。

---

## 验证来源

- 计划书: `docs/计划书.md` v4.0
- 技术文档: `src/phase1/pipeline.md` v1.2
- Config: `config/sources.json`
- Zhao & Chen (2025) OpenAlex 消歧精度: https://arxiv.org/html/2502.11610v2
- Zheng et al. (2025) OpenAlex 中国论文覆盖: https://doi.org/10.1002/asi.70013

**版本**: v4.0
**生成日期**: 2026-07-01
