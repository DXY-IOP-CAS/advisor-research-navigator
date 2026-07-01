# 02 — AI 质量门 + 错误处理

## 质量检查清单

每步脚本后检查：

### GS 质量门
- [ ] email_domain 匹配机构域名？
- [ ] 论文数 > 5？
- [ ] h-index 存在且 > 0？

### OA 质量门
- [ ] h-index 与 GS 差异 > 50%？→ 标记"以 GS 为准"
- [ ] affiliation 匹配官网机构？
- [ ] 论文标题命中 `OA_POLLUTION_KEYWORDS`（dna hydrogel / wind imaging 等）？→ 剔除

### arXiv 质量门
- [ ] 是否加了 `-c` 学科分类过滤？
- [ ] 有 DOI/标题与 GS/OA 匹配的？→ 保留，其他噪声仅供参考

### 渲染门
- [ ] 全部论文逐一列出（无"以下见完整列表"等字样）
- [ ] 每阶段表格前有叙事段落
- [ ] 每篇论文有外部超链接
- [ ] 不做导师评价内容

## 错误处理

脚本不抛异常退出。所有故障用 `status: "error"` 字段表示。

### 网络层重试
`utils.py` 的 `@retry` 装饰器：默认 3 次指数退避（2s/4s/8s）。

适用场景：OA 503 错误、网络超时、SSL EOF。

### OpenAlex 503 专项
原因：用了 `test@example.com` 等假邮箱被误判进 10 req/s polite pool，触发限速。
修复：`step3_openalex.py` 内检测 email 是否为保留域，是则自动降为 1 req/s。

### 完全降级
三个数据源全部不可用时，step6 输出空论文列表。AI 渲染时写明"所有数据源均不可用"。
