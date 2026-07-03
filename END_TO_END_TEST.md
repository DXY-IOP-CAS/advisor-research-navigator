# 端到端测试规范

**目的**：防止 AI 把测试用例当成「手把手教学」。

## 用户输入（唯一允许的内容）

测试时用户**只**给以下基础信息。**任何额外内容**（已抓取的官网内容、已知 GS ID、JSON 草案、降级提示）都是违规：

```
姓名：<中文名>
机构：<大学>/<学院或研究所>/<部门>
官网 URL：<教授主页链接>
```

例如：
```
姓名：李自翔
机构：中国科学院大学 / 中科院物理所 / 理论实验室
官网 URL：https://edu.iphy.ac.cn/?q=detail_teacher&id=4443
```

**没了**。没有英文名、没有 email、没有论文列表、没有 GS ID、没有履历、没有 career_stages 草案、没有 MCP 搜索关键词建议、没有降级路径提示。英文名由 AI 从官网、GS、ORCID 或 OpenAlex 自主补全。

## 为什么这么严格

- 端到端测试的目的：发现 Harness 缺口，让 AI 自主补全
- 给 AI 越多提示 → 测试越像 tutorial → 越测不出 harness 真实缺陷
- 如果基础信息不够 AI 完成任务 → **问题在 Harness，不在测试** → 应回头优化 Harness

## 如果 AI 觉得「基础信息不够」

**禁止**：找用户要更多提示
**正确**：记录下来「Harness 缺口」，回头优化。具体动作：
1. 在 `docs/e2e/YYYY-MM-DD-<name>-minimal-prompt.md` 写 diagnosis 说明哪一步卡住、缺什么信息
2. 在对应的 phase1-core.md / SKILL.md 加 L3 reference 补充
3. 重新跑测试

## AI 在 Harness 缺口时该怎么决策

按 progressive disclosure 路由自主判断：
- 不知道 MCP 搜什么关键词 → 读 `references/01-data-sources.md`
- 不知道 JSON schema → 读 `references/phase1-templates.md`
- 不知道 verify 失败怎么修 → 读 `references/phase1-recovery.md`
- 不知道如何降级（GS 不可用怎么办）→ 读 `references/phase1-recovery.md` §step 失败的恢复路径
- 不知道如何写 narrative → 读 `references/phase1-anti-patterns.md`

如果这些文件都说了，AI 还是不会做 → **Harness 真的缺** → 记 diagnosis，不许要用户兜底。

## 禁止的「手把手」行为

- ❌ 在 prompt 里附已抓取的官网文本
- ❌ 在 prompt 里附已知 GS ID / OA ID / ORCID
- ❌ 在 prompt 里附 career_stages 草案
- ❌ 在 prompt 里说「按以下顺序搜：xxx / yyy / zzz」
- ❌ 在 prompt 里说「如果 xxx 失败，降级到 yyy」
- ❌ 在 prompt 里附 narrative 风格示例
- ❌ 在 prompt 里给修复指引

正确的 prompt：

```
跑阶段 1 端到端测试：
姓名：李自翔
机构：中国科学院大学 / 中科院物理所 / 理论实验室
官网 URL：https://edu.iphy.ac.cn/?q=detail_teacher&id=4443
```

**就这样。**
## 测试记录要求

每次端到端测试完成后，在 `docs/e2e/` 记录：

- 使用策略：`standard` 或 `conservative`
- `risk_gate.py --prof-dir ...` 的 mode、reason、metrics
- 是否触发补搜；如触发，补搜原因和处理结果
- `verify_profile.py --prof-dir ...` 的结果
- verify 之外仍需人工关注的内容风险
