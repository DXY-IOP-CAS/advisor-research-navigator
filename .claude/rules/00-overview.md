# 00 — 三阶段总览

## 一句话

用户输入姓名 + 机构 + 官网 URL → 全自动 → 产出 `01_基础画像.md`。

## 三阶段流

```
用户输入（姓名 + 机构 + 官网 URL）
    │
阶段 A（AI 主导）
  读官网 + MCP 广域搜索 → 找 GS/ORCID 链接
  邮箱匹配官网域名 → 身份确认 → verified_ids.json
    │
阶段 B（脚本执行，详见 01-data-pipeline）
  step2_gs: scholarly 取 GS 论文
  step3_openalex: OpenAlex 论文+元数据
  step5_arxiv: arXiv 预印本
  step6_merge: 三源合并去重
    │
阶段 C（脚本 + AI，详见 01-data-pipeline）
  render_profile.py 表格渲染 → AI 补充叙事
  → 01_基础画像.md
```

## 核心原则

- 存档不是缓存（详见 03-archive）
- 来源必标 URL，缺失标 [未找到]
- 不做导师评价（匹配度、推荐意见等）
- 每次重要改动前 commit
