# JSON Schema 模板（L3 按需）

> Phase A 写 JSON 时读本页。其它时候不用读。

## verified_ids.json

```json
{
  "name": "学者姓名",
  "name_pinyin": "Xing_Ming",
  "ids": {
    "gs_id": "GS profile ID（不含 ?hl=zh 等参数）",
    "oa_id": "OA Author ID（如 A5000914228）",
    "orcid": "0000-0000-0000-0000（含连字符）"
  },
  "verification": {
    "tier": "T1 | T2 | T3 | T4",
    "email_domain": "邮箱域名（如 iopcas.cn）",
    "gs_email_verified": true
  },
  "sources": {
    "gs_url": "https://scholar.google.com/citations?user=...",
    "oa_url": "https://openalex.org/authors/...",
    "orcid_url": "https://orcid.org/..."
  }
}
```

### 验证层级定义

| Tier | 标准 | 适用 |
|:----:|:-----|:-----|
| T1 | 官网 email 域名 == GS verified email 域名 | 绝大多数教授 |
| T2 | ORCID 匹配（OA 或官网） | 有 ORCID 但 GS 邮箱未验证 |
| T3 | 官网论文标题精确匹配 GS 论文 ≥ 3 篇 | 邮箱不可得，论文标题明确 |
| T4 | 全降级——走 OA + arXiv，无 GS | 极端情况，需在画像开篇标注 |

---

## career_stages.json（enriched，推荐格式）

```json
{
  "stages": [
    {
      "name": "博士阶段",
      "start": 2007,
      "end": 2013,
      "institution": "中科院近代物理所",
      "position": "博士研究生",
      "direction": "原子分子碰撞动力学"
    },
    {
      "name": "博后阶段",
      "start": 2013,
      "end": 2018,
      "institution": "ETH Zurich",
      "position": "博士后",
      "direction": "超快 XUV 光电子谱学"
    }
  ]
}
```

脚本自动从 `institution/position/direction` 三个字段渲染 §2 学术履历表 + §4 论文分组。**AI 不要手写 §2**。

### 旧格式兼容（不推荐）

如果只有 `name/start/end` 三字段（缺 institution/position/direction），§2 留占位符给 AI Edit，AI 自己补表格。建议升级到 enriched 格式让脚本接管。

### 阶段划分铁律

**每个（时间区间 + 机构 + 职位）变化是一个独立阶段。**

- 同一机构不同方向 → 拆
- 同一方向不同机构 → 拆
- 博士后到助理研究员（机构变了）→ 拆
- 助理研究员到副研究员（机构没变）→ 拆
- 实习生算独立阶段（如有需要）

---

## JSON 校验脚本

- `validate_verified_ids.py verified_ids.json` — 字段完整性
- `validate_career_stages.py career_stages.json` — 阶段合理性（轻量警告，不阻塞）

两者**只警告不阻塞**。最终门控是 `verify_profile.py`。