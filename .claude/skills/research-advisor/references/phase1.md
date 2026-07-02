# 阶段 1 — AI 执行规则与叙事规范

> 技术执行细节（CLI 命令、数据格式、质量门）详见 `src/phase1/pipeline.md`。本文件只包含 AI 在执行阶段 1 时必须遵守的流程规则和叙事规范。

## 执行规则

### 错误恢复指南

- 如果 step 脚本遇到 API 429/503 错误：脚本内部已有指数退避重试（3 次）。等待后自动恢复。
- 如果 subAgent 自身遇到 API rate limit：等待 60 秒后重试整条命令。不要从头开始——archive/ 中的中间文件仍可复用。
- 如果 GS 被封锁（status=blocked）：降级到 OpenAlex 走 OA-only 路径。不重试。
- 如果 step 因网络中断失败：重新执行失败的 step，不是重新整条流水线。用 `--archive-dir` 参数指定已有 archive 路径。
- 如果 verify 未通过：看具体哪项失败 + 修复指引 → 修复 → 重新渲染 → 再验。不从头跑。用 `--archive-dir` 复用已采集数据。

## 执行规则

### 路径规范（禁止硬编码，第一条必读）

输出目录层级必须如下。不要猜，不要从网址推断——直接套这个模板：

```
output/<大学>/<学院所>/<部门>/<姓名>/
```

**中科院物理所的正确路径**（不是 `output/中科院物理所/...`）:

```
output/中国科学院大学/中科院物理所/超快物质科学中心/张鹏举/
            ^^^^^^^^         ^^^^^^^^          ^^^^^^^^    ^^^^^^
            大学层          学院所层            部门层      姓名
```

`archive/<timestamp>/` 下放全部中间文件。prof 根目录只放最终产出（`01_基础画像.md`）。

**常见错误**：把 `中科院物理所` 放在第一层。中科院物理所的上级大学是中国科学院大学，不是它自己。
- `latest.txt`：`{prof_root}/latest.txt` — 记录最新时间戳
- **career_stages.json 和 verified_ids.json 放在 archive/ 下，不在 prof 根目录**

如果手动执行，每个 step 脚本都接受 `--archive-dir` 参数替代 `-o`。AI 只需传 `--archive-dir <archive路径>`，文件名由脚本自动拼接。

如果使用 run.py，传 `--university --institute --department --name` 结构化参数，路径自动构造。

### 广度搜索步骤（Phase A 按此顺序执行）

MCP 搜索各平台，找到 ID 后填入 `verified_ids.json`：

1. **建 archive 目录**：Phase A 第一步先建 `archive/<timestamp>/`。之后所有阶段文件（verified_ids.json、career_stages.json 等）直接写进 archive/。**prof 根目录只放最终产出**。
2. **Google Scholar**：MCP 搜"姓名 + 机构 + Google Scholar" → 找到 GS profile → 提取 GS ID
2. **OpenAlex**：MCP 搜"姓名 + OpenAlex" 或用 ORCID 反查 → 找到 OA 作者 ID
3. **ORCID**：官网如有 ORCID 直接使用，否则 MCP 搜"姓名 + ORCID"
4. **交叉验证**：邮箱域名匹配（T1）、ORCID（T2）、论文指纹（T3）、综合判断（T4）
5. **填写 verified_ids.json**：记录所有 ID、验证层级、来源 URL。存入 archive/<ts>/00_verified_ids.json
6. **填写 career_stages.json**：从官网履历提取阶段，每一个（时间+机构+职位）变化独立为一段。存入 archive/<ts>/career_stages.json

### 验证卡模板（verified_ids.json 格式）

```json
{
  "name": "学者姓名",
  "name_pinyin": "Xing_Ming",
  "ids": {
    "gs_id": "GS_ID",
    "oa_id": "OA_ID",
    "orcid": "ORCID"
  },
  "verification": {
    "tier": "T1|T2|T3|T4",
    "email_domain": "邮箱域名",
    "gs_email_verified": true
  },
  "sources": {
    "gs_url": "https://scholar.google.com/...",
    "oa_url": "https://openalex.org/...",
    "orcid_url": "https://orcid.org/..."
  }
}
```

## 叙事规范

### 目标读者

画像的读者是物理专业**大二/大三本科生**。你有义务：
- 每个专业术语首次出现时用 1 句话解释（例："高次谐波产生（HHG）——用强激光打气体/固体，产生极紫外脉冲"）
- 每篇论文的叙事回答"为什么要做这个"（背景）和"这发现了什么"（发现），而不是只报论文标题
- 分层递进：先交代研究背景和技术原理（为什么要做、用什么技术），再讲具体发现（发现了什么、为什么重要）

### 叙事示例

以张鹏举的 ETH Zurich 阶段叙事为例：

```
❌ 仅罗列发现（不要这样写）：
"在 ETH Zurich 期间，利用 XUV 时间分辨光电子谱学研究了 cis-stilbene 的光异构化动力学，
观测到气相和液相的不同时间尺度，发表在 Nature Chemistry。"

✅ 分层递进（按此风格）：
"2018 年张鹏举加入 ETH Zurich Hans Jakob Wörner 组，研究方向从离子碰撞转移到超快光学。
他用高次谐波产生的极紫外脉冲作为泵浦光，激发分子到电子激发态，然后用红外探测光电离分子，
测量光电子动能随时间的变化。这个技术的核心优势是飞秒（10⁻¹⁵ s）时间分辨率——
可以拍到原子核运动过程中的电子分布变化。

利用这套装置，他研究了 cis-stilbene 的光异构化。cis-stilbene 分子吸收紫外光后，
中间的 C=C 双键打开，分子从弯曲构型转变为直线构型。他发现：在气相中这个过程在
约 200 fs 内完成；在液相中由于溶剂分子的碰撞阻碍，时间延长到约 1 ps。
这一对比说明溶剂环境对分子反应动力学有重要影响（Nature Chemistry, 2022）。"
```

### 姓名格式

统一格式：`中文名 (英文名)`，如 `张鹏举 (Pengju Zhang)`。

### 学术履历

§2 学术履历表由 `render_profile.py` 从 `career_stages.json` 自动生成（当 JSON 含 institution/position/direction 字段时）。**AI 不再需要手写 §2。**

如果 career_stages.json 只含 name/start/end（旧格式），§2 留占位符给 AI Edit。建议升级到 enriched 格式让脚本自动处理。

### 研究方向

1 段总体概述 + 3-4 个具体方向（中英文关键词）。客观描述导师研究什么，不做评价。

### 论文分组叙事

- 对每个 `### 4.x` 阶段，表格前必须有 1-2 句叙事段落
- 叙事说明该阶段的研究主题和方向变化，不报菜名
- **阶段划分不是按年份，而是按学术履历阶段**。Phase A 必须创建 `career_stages.json`
  - 推荐格式（enriched，脚本自动生成 §2 + §4）：
    ```json
    {"name": "博士阶段", "start": 2007, "end": 2013,
     "institution": "中科院近代物理所", "position": "博士研究生",
     "direction": "原子分子碰撞动力学"}
    ```
  - 兼容旧格式（name/start/end 紧耦合，AI 需手写 §2）
- 建议运行 `validate_career_stages.py` 做快速自检
- 脚本接收 `--stages career_stages.json` 自动按阶段分组论文。不需要 AI 事后重命名阶段名
- "禁写" `代表性论文`、`以下见完整列表`、`如下图` 等字样
- 论文表格由脚本生成，AI 不得修改表格行数或内容。只写表格前的叙事

### 合作网络

列出高频合作者（姓名 + 机构 + 合作方向），每条带来源超链接（GS/ORCID）。

### 公开信息

列出新闻/采访/讲座等公开信息，每条带超链接。

## 硬约束（禁止）

- 禁止评价导师（匹配度、推荐意见、"值得报考"、"热点方向"、"影响力大"等）
- 禁止在论文表格内写叙事——叙事写在表格前面单独的段落
- 禁止改写论文表格内容——表格由 render_profile.py 脚本生成
- 每篇论文必须保留脚本生成的超链接列（DOI/arXiv）
- 全部论文逐一列出，不得省略
- 缺失字段标 `[未找到]`
- 所有外部信息标注来源超链接

### 文件修改方式（重要）

AI 补充叙事时**只能使用 Edit（精确替换），不得使用 Write（整体重写）**。

```
正确的做法：
  1. 读 render_profile.py 生成的骨架文件（含 <!-- AI 渲染：... --> 占位符）
  2. 用 Edit 替换每个占位符为实际叙事文字
  3. 论文表格所在的行（以 | 开头）禁止触碰
  
错误的做法：
  ❌ 用 Write 覆盖整个文件（会破坏 frontmatter、表格、格式）
  ❌ 修改 | # | 年份 | 标题 | 期刊 | 引用 | 来源 | 表格内容
  ❌ 改写 <!-- AI 渲染：... --> 以外的任何脚本输出
  ❌ 修改 §2 学术履历表格（由脚本从 career_stages.json 自动生成，AI 改 career_stages 即可）
```

### 表格约束

所有表格必须遵守 `pipeline.md` 第 5 节的"表格格式规范"，禁止 AI 自主增减列数。论文表格固定 6 列，不得新增"关键论文"、"代表性论文"等筛选表。

## 输出结构

最终输出 `01_基础画像.md`。输出路径 `output/<学校>/<学院或研究所>/<部门>/<姓名>/01_基础画像.md`。

### verify 门控循环

运行 `python src/phase1/verify_profile.py <画像路径> --merged <merged.json 路径>`。9 项检查全部通过后才能声称完成。

verify 未通过时：
1. 看哪几项 [FAIL] 了 + 每项后面的修复指引
2. 按指引修复（改叙事 / 调配置 / 重新渲染）
3. 重新运行 verify 直到全部 [OK]
4. 不通过不能声称完成

### arXiv 精确匹配（可选但推荐）

如果 Phase A 获取到 ORCID，在阶段 B 中优先使用 step4 替代 step5：
- `python src/phase1/step4_arxiv_id.py "ORCID" --name "姓_名" -o ...`
- 精确匹配、零噪声。返回 404 或空时回退到 step5 的 `au:` 搜索
