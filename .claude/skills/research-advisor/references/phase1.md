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

用 `render_profile.py` 从 merged.json 生成结构化画像。脚本确保全部论文逐一列出、来源标记分明、运行统计写入头部。

```bash
python src/phase1/render_profile.py output/<机构>/<部门>/<姓名>/archive/<timestamp>/04_merged.json \
  -o output/<机构>/<部门>/<姓名>/01_基础画像.md
```

如果 verified_ids.json 中包含了 `career_stages` 字段（学术阶段配置），传入 `--stages` 参数：

```bash
python src/phase1/render_profile.py 04_merged.json \
  --stages 00_verified_ids.json \
  -o 01_基础画像.md
```

**渲染后 AI 润色**：脚本生成论文表格和运行统计。AI 在脚本输出基础上补充以下内容（这些是脚本做不到的）：

1. **学术履历表格**（从官网/广域搜获取的教育和工作经历）
2. **研究方向描述**（中英文关键词 + 1-2 句总体概述）
3. **论文阶段叙事**（每阶段开头用一段话说明：该阶段的研究主题是什么？与上一阶段相比有什么变化？为什么会有这个变化？转型的契机是什么？）——这是画像的核心价值，不是报菜名
4. **合作网络分析**
5. **公开信息整理**（新闻/采访/讲座，含超链接）
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
