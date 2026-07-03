# QUICKSTART — 导师研究方向调研工具

## 一句话

阶段 1 已实现；阶段 2-4 已沉淀为 `research-advisor` skill、模板和 smoke 验证器，正在用张鹏举 pilot 做提交版质量收敛。阶段 1 技术细节见 `src/phase1/pipeline.md`，整体设计见 `docs/计划书.md`。

## 新窗口启动

```
1. 读 src/phase1/pipeline.md（阶段 1 技术执行文档）
2. 读 docs/计划书.md（设计决策）
3. 读 AGENTS.md（项目硬约束，尤其 archive 禁读）
4. 若做导师调研或阶段 2-4，读 .claude/skills/research-advisor/SKILL.md 和对应 references
5. 向用户确认当前任务
```

## 项目结构

```
pilot-test/
├── src/phase1/           # 阶段 1 活跃脚本
│   ├── pipeline.md       # 技术执行文档（单一事实源）
│   ├── step1_discipline.py  # 学科关键词分类
│   ├── step2_gs.py          # scholarly 封装（GS 主源）
│   ├── step3_openalex.py    # OpenAlex 元数据
│   ├── step5_arxiv.py       # arXiv 预印本
│   ├── step6_merge.py       # 多源合并去重
│   ├── render_profile.py    # 论文表格渲染
│   ├── verify_profile.py    # 质量门控验证
│   ├── archive_previous.py  # 自动存档旧版产出
│   └── utils.py             # 共享工具库
├── config/
│   └── sources.json         # 数据源 + 学科字典
├── docs/                    # 规划与设计文档
├── output/<机构>/<部门>/<姓名>/   # 导师画像产出
│   ├── 00_材料导读.md
│   ├── 01_基础画像.md
│   ├── 02_领域地图.md
│   ├── 03_论文路线.md
│   ├── 04_学习向导.md
│   └── archive/<timestamp>/ # 中间产物存档（脚本写入，Agent 不读）
└── archive/                 # 旧版存档（只写不读）
```

## 流水线速览

阶段 1 详见 `src/phase1/pipeline.md`。三阶段流：

```
阶段 A（AI 主导）：读官网 + MCP 搜 GS/ORCID → 邮箱验证 → verified_ids.json
阶段 B（脚本执行）：step2_gs / step3_openalex / step5_arxiv / step6_merge
阶段 C（脚本+AI）：render_profile → AI Edit 叙事填充 → verify_profile
```

阶段 2-4 详见 `.claude/skills/research-advisor/`：

```
阶段 2：从 01 出发，建立当前领域地图
阶段 3：用领域地图重读当前相关论文，解释论文线如何构成研究路线
阶段 4：从目标论文和当前前沿倒推学习路径，形成进组前最小闭环
```

## 注意事项

- 每次运行不读历史缓存，全部重新查询。archive 目录仅供存档溯源
- Agent 不读取或引用 `archive/` 或 `output/**/archive/**`
- GS 访问依赖梯子节点质量，scholarly 库自动处理
- OpenAlex 对中文学者覆盖约 22-38%，h-index 可能不准，以 GS 为准
- arXiv 同名噪声率高，merge 时通过 DOI/标题匹配自动过滤
- 阶段 2-4 的验证器只做结构、来源、禁用语和 DOI 元数据 smoke，不证明学术质量

## 核心原则

1. **GS 是论文列表主源**，OpenAlex 只做元数据补充
2. **GS 邮箱校验是身份金标准**——匹配官网 email 即确认身份
3. **存档不是缓存**——每次运行从头查 API
4. **全降级**——GS 不可用时 OA 做替补
