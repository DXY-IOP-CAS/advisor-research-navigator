# 错误恢复与 verify 循环（L3 按需）

> step/verify 失败时读本页。其它时候不用读。

## step 失败的恢复路径

| 错误 | 原因 | 恢复动作 |
|:-----|:-----|:--------|
| `API 429/503` | 限速 | 脚本内部已有指数退避重试（3 次）。等待后自动恢复。 |
| `subAgent API rate limit` | 当前 session 命中限速 | 等待 60 秒后重试整条命令。**不要从头跑**——archive/ 中间文件可复用。 |
| `GS status=blocked` | GS 被封锁 | 降级到 OpenAlex 走 OA-only 路径。不重试 GS。 |
| `network interrupt` | 网络中断 | 重新执行失败的 step（不是整条流水线）。用 `--prof-dir` 复用已采集数据。 |
| `merged.json not found` | step6 没跑或路径错 | 先跑 step6，再 render。 |
| `prof_dir 下找不到 latest.txt` | phase1_init.py 没跑或 prof_dir 错 | 先跑 `phase1_init.py --university ... --name ...`。 |

---

## verify 失败的处理流程

```
verify_profile.py 失败
  ↓
看哪几项 [FAIL] + 每项后面的修复指引（print 在最后）
  ↓
按指引修复（改叙事 / 调配置 / 重新渲染）
  ↓
重新运行 verify 直到全部 [OK]
  ↓
不通过不能声称完成
```

### verify 9 项检查速查

| # | 检查 | 失败常见原因 |
|:-:|:-----|:------------|
| 1 | 禁词检查（"匹配度""推荐报考"等）| §3 narrative 写入了评价性词 |
| 2 | 学术履历非 0 行 | career_stages.json 缺 institution/position 字段 |
| 3 | §2 阶段后无空表头 | §2 表格后面跟着空行或缺换行 |
| 4 | AI 占位符全替换 | 还有 `<!-- AI 渲染：... -->` 未替换 |
| 5 | 论文表格列数 = 6 | 被人为加列（"关键论文""代表性论文"）|
| 6 | 表格无超 400 字符行 | 论文标题过长或被填入 narrative |
| 7 | 阶段表头含机构关键词 | 阶段名只写了年份 |
| 8 | 无重复论文 | 同名干扰没过滤掉 |
| 9 | 论文行数与 GS baseline 匹配 | OA/arXiv 混入太多 |

### lint-style 错误信息

`verify_profile.py` 失败时**每项 FAIL 后面直接给出修复命令**。例：

```
[FAIL] AI 占位符未全替换：还有 7 个 <!-- AI 渲染：... --> 未替换
  → 修复：用 Edit 替换占位符为实际叙事
  → 命令：Edit(output/.../01_基础画像.md, old="<!-- AI 渲染：方向 -->", new="...")
```

这是 OpenAI 百万行实验的关键技巧——把修复指引直接注入 LLM context，AI 不必自己猜怎么修。

---

## archive 行为（自动化，无需 AI 介入）

每个 step 完成后用 `archive_step.py` 自动归档到 `archive/<ts>/`：

```bash
python src/phase1/archive_step.py --prof-dir "output/..." --source 01_gs.json
```

AI **不需要记得手动归档**——脚本副作用会处理。如果忘了也没关系，archive 是 best-effort，不影响主流程。

---

## 中途接手时的恢复

如果是从某个 checkpoint 继续：

1. 读 `output/.../姓名/latest.txt` 拿当前 ts
2. 读 `archive/<ts>/00_verified_ids.json` 看已经锁定的身份
3. 读 `archive/<ts>/career_stages.json` 看阶段配置
4. 读 `archive/<ts>/04_merged.json` 看已合并的论文
5. 根据缺失的 step 从 Phase B 的对应位置继续

**不需要从头跑**。ProfDirResolver 会从 latest.txt 自动找到 archive 路径。