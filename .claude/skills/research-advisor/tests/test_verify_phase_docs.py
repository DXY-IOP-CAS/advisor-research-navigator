import importlib.util
import sys
import unittest
import uuid
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_phase_docs.py"
BLUEPRINT_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "templates" / "blueprint.md"
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "assets" / "templates"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_phase_docs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def cite(key: str) -> str:
    return f'<sup><a href="#{key.lower()}">[{key}]</a></sup>'


def source_table_row(key: str) -> str:
    lower = key.lower()
    return (
        f'| <a id="{lower}"></a>[{key}] | 示例文献或资料 | '
        f"支撑正文中的 [{key}] 判断 | https://example.com/{lower} | 测试资料 |\n"
    )


SOURCE_TABLE_HEADER = "| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |\n"
EVIDENCE_TABLE_HEADER = "| 文档位置 | 关键判断 | 来源 | 来源支撑了什么 | 证据强度 | 人工复核 |\n"
MERMAID_BLOCK = "```mermaid\nflowchart LR\n    A[起点] --> B[终点]\n```\n"
TABLE_VISUAL = (
    "| 论文 | 问题 | 角色 |\n"
    "|:---|:---|:---|\n"
    "| P1 | 示例问题 | 当前主线 |\n"
)
BLUEPRINT_TEXT = """# 测试导师认知蓝图

## 1. 读者起点

默认读者有高数、线代和普物基础。

## 2. 导师当前方向一句话

测试导师当前方向是一句可审查的方向描述。

## 5. 目标论文和论文路线

目标论文用于连接论文路线。

## 6. 核心图和读图链

核心图用于进入论文证据。

## 7. 平台链路

平台链路连接光源、样品、信号和瓶颈。

## 8. 课程到论文的学习桥

课程到论文的学习桥连接基础课和目标论文。

## 9. 可视化计划

可视化计划说明每份文档用什么理解构件。

## 10. 证据风险和人工复核

证据风险用于提醒弱证据和需人工复核点。
"""


class VerifyPhaseDocsTest(unittest.TestCase):
    def setUp(self):
        workspace_tmp = Path(__file__).resolve().parents[4] / ".tmp" / "verify_phase_docs_tests"
        workspace_tmp.mkdir(parents=True, exist_ok=True)
        self.prof = workspace_tmp / f"case_{uuid.uuid4().hex}"
        self.prof.mkdir(parents=True, exist_ok=False)
        (self.prof / "_internal").mkdir()
        (self.prof / "_internal" / "blueprint.md").write_text(BLUEPRINT_TEXT, encoding="utf-8")
        evidence_dir = self.prof / "_internal" / "evidence"
        evidence_dir.mkdir()
        (evidence_dir / "key_claims.md").write_text(
            "# 关键判断证据核对表\n\n"
            + EVIDENCE_TABLE_HEADER
            + "|:---|:---|:---|:---|:---|:---|\n"
            + "| 00_材料导读.md | 阅读顺序 | [O1] | 支撑导读来源 | 直接证据 | 否 |\n",
            encoding="utf-8",
        )
        self.write_doc(
            "00_材料导读.md",
            "# 张鹏举 (Pengju Zhang) - 材料导读\n\n"
            f"## 这套材料解决什么问题\n这套材料帮助学生建立阅读顺序。{cite('O1')}\n\n"
            "## 建议阅读顺序\n"
            "第一遍先粗读 `01_基础画像.md`，只建立身份、履历、论文集合和来源风险的初印象。\n\n"
            "第二步读 `02_领域地图.md`，第三步读 `03_论文路线.md`，第四步读 `04_学习向导.md`。最后回看 `01_基础画像.md`，用领域、论文和学习路径理解反过来核查事实底座。\n\n"
            "| 阅读轮次 | 文档 | 读这一遍要抓住什么 |\n"
            "|:---|:---|:---|\n"
            "| 第一遍 | `01_基础画像.md` | 粗读身份、履历、论文集合和来源风险 |\n"
            "| 第二步 | `02_领域地图.md` | 建立当前方向的领域坐标 |\n"
            "| 第三步 | `03_论文路线.md` | 看论文怎样连成问题链 |\n"
            "| 第四步 | `04_学习向导.md` | 从基础课倒推到论文和平台链路 |\n"
            "| 最后 | `01_基础画像.md` | 回看事实底座和风险 |\n\n"
            "## 如何阅读引用和证据标记\n[O#] 代表官方或身份来源，[P#] 代表论文来源，[R#] 代表教材、讲义或综述，[B#] 代表背景资料；[未找到] 表示暂缺来源，需人工复核表示判断还不够强。\n\n"
            "## 起步讨论入口\n用一篇目标论文、Fig. 2 核心图和一条平台链路进入讨论。\n\n"
            "## 文件定位\n五份文档按认知阶梯互相支撑。\n\n"
            "## 使用边界\n本材料不做导师评价、不做申请建议、不替代论文和教材。\n\n"
            + MERMAID_BLOCK
            + "\n"
            "## 参考文献与资料\n\n"
            "### 官方与身份资料\n\n"
            + SOURCE_TABLE_HEADER
            + "|:---|:---|:---|:---|:---|\n"
            + source_table_row("O1"),
        )
        self.write_doc(
            "01_基础画像.md",
            "# 张鹏举 (Pengju Zhang) - 基础画像\n\n"
            "## 资料概览\n资料链接：https://example.com\n\n"
            + MERMAID_BLOCK,
        )
        self.write_doc(
            "02_领域地图.md",
            "# 张鹏举 (Pengju Zhang) - 领域地图\n\n"
            f"## 资料概览\n官方方向以导师主页为准。{cite('O1')}\n\n"
            + MERMAID_BLOCK
            + "\n"
            "## 导师路径速览\n\n"
            "## 当前方向学科定位\n\n"
            "## 领域怎样发展到当前问题\n\n"
            "## 关键问题和技术路线\n\n"
            "## 当前前沿\n\n"
            "## 证据与待复核点\n需人工复核。\n\n"
            "## 参考文献与资料\n\n"
            "### 官方与身份资料\n\n"
            + SOURCE_TABLE_HEADER
            + "|:---|:---|:---|:---|:---|\n"
            + source_table_row("O1"),
        )
        self.write_doc(
            "03_论文路线.md",
            "# 张鹏举 (Pengju Zhang) - 论文路线\n\n"
            f"## 资料概览\n论文路线以代表论文为准。{cite('P1')}\n\n"
            + MERMAID_BLOCK
            + "\n"
            "## 先抓住论文在回答什么问题\n\n"
            "## 论文线怎样连成研究路线\n\n"
            "## 当前主线论文\n\n"
            "## 前史积累论文\n\n"
            "## 旁支与弱证据\n需人工复核。\n\n"
            "## 从论文路线倒推出的学习准备\n\n"
            "## 参考文献与资料\n\n"
            "### 论文与数据资料\n\n"
            + SOURCE_TABLE_HEADER
            + "|:---|:---|:---|:---|:---|\n"
            + source_table_row("P1"),
        )
        self.write_doc(
            "04_学习向导.md",
            "# 张鹏举 (Pengju Zhang) - 学习向导\n\n"
            f"## 资料概览\n学习路径以课程和综述倒推。{cite('R1')}\n\n"
            + MERMAID_BLOCK
            + "\n"
            "## 终点：进组前应接近什么状态\n\n"
            "## 进组前起步闭环\n\n"
            "一篇主线论文、Fig. 2 核心图和一条平台链路可以组成进组前起步闭环。\n\n"
            "## 先知道光电子谱到底在看什么\n\n"
            "## 再把静态谱读成时间过程\n\n"
            "## 随后进入阿秒电子运动\n\n"
            "## 进入液相和凝聚相复杂环境\n\n"
            "## 最后把机制论文接回平台边界\n\n"
            "## 回到张鹏举论文路线\n\n"
            "## 进组后先从哪里接上\n\n"
            "## 卡住时怎么判断该补什么\n\n"
            "## 资源指针\n\n"
            "## 参考文献与资料\n\n"
            "### 综述、教材与课程资料\n\n"
            + SOURCE_TABLE_HEADER
            + "|:---|:---|:---|:---|:---|\n"
            + source_table_row("R1"),
        )

    def write_doc(self, name, text):
        (self.prof / name).write_text(text, encoding="utf-8")

    def test_accepts_complete_phase_docs(self):
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertTrue(result.ok, result.messages)

    def test_blueprint_template_contains_required_fields(self):
        module = load_module()
        self.assertTrue(BLUEPRINT_TEMPLATE.exists(), f"missing template: {BLUEPRINT_TEMPLATE}")
        text = BLUEPRINT_TEMPLATE.read_text(encoding="utf-8")

        for label, pattern in module.BLUEPRINT_REQUIRED_FIELDS:
            self.assertRegex(text, pattern, f"blueprint template missing {label}")

    def test_phase_templates_use_spaced_bilingual_title_placeholders(self):
        for filename in ["00_材料导读.md", "02_领域地图.md", "03_论文路线.md", "04_学习向导.md"]:
            text = (TEMPLATE_DIR / filename).read_text(encoding="utf-8")
            first_line = text.splitlines()[0]
            self.assertIn("<中文名> (<English Name>)", first_line, filename)

    def test_material_guide_template_lists_all_five_deliverables(self):
        text = (TEMPLATE_DIR / "00_材料导读.md").read_text(encoding="utf-8")
        for filename in [
            "00_材料导读.md",
            "01_基础画像.md",
            "02_领域地图.md",
            "03_论文路线.md",
            "04_学习向导.md",
        ]:
            self.assertIn(filename, text)
        self.assertIn("五份", text)
        self.assertNotIn("四份文档", text)

    def test_rejects_missing_cognitive_blueprint(self):
        (self.prof / "_internal" / "blueprint.md").unlink()

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertIn("[FAIL] 缺少 _internal/blueprint.md 认知蓝图", result.messages)

    def test_rejects_blueprint_without_core_fields(self):
        (self.prof / "_internal" / "blueprint.md").write_text(
            "# 测试导师认知蓝图\n\n## 1. 读者起点\n\n只有读者起点。\n",
            encoding="utf-8",
        )

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertIn("[FAIL] _internal/blueprint.md 缺少认知蓝图字段: 目标论文", result.messages)

    def test_accepts_domain_adapted_phase4_learning_headings(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        text = text.replace("## 先知道光电子谱到底在看什么", "## 先知道谱学到底在读什么信号")
        text = text.replace("## 随后进入阿秒电子运动", "## 随后再看固体 HHG 和阿秒电子运动")
        text = text.replace("## 进入液相和凝聚相复杂环境", "## 进入软晶格和凝聚态复杂环境")
        self.write_doc("04_学习向导.md", text)

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertTrue(result.ok, result.messages)

    def test_accepts_fully_domain_adapted_phase4_learning_path_headings(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        text = text.replace("## 先知道光电子谱到底在看什么", "## 先知道二维 Kerr 信号在读什么")
        text = text.replace("## 再把静态谱读成时间过程", "## 再分清电子响应和声子响应")
        text = text.replace("## 随后进入阿秒电子运动", "## 随后进入太赫兹驱动和非线性响应")
        text = text.replace("## 进入液相和凝聚相复杂环境", "## 进入软晶格和极化子图像")
        text = text.replace("## 最后把机制论文接回平台边界", "## 最后把平台链路接回目标论文")
        self.write_doc("04_学习向导.md", text)

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertTrue(result.ok, result.messages)

    def test_rejects_phase4_without_learning_path_sections(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        text = text.replace("## 先知道光电子谱到底在看什么\n\n", "")
        text = text.replace("## 再把静态谱读成时间过程\n\n", "")
        text = text.replace("## 随后进入阿秒电子运动\n\n", "")
        text = text.replace("## 进入液相和凝聚相复杂环境\n\n", "")
        text = text.replace("## 最后把机制论文接回平台边界\n\n", "")
        self.write_doc("04_学习向导.md", text)

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 进组前起步闭环和回到论文路线之间至少需要 3 个方向适配的学习路径章节",
            result.messages,
        )

    def test_rejects_missing_material_guide(self):
        (self.prof / "00_材料导读.md").unlink()
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertIn("[FAIL] 缺少文件: 00_材料导读.md", result.messages)

    def test_rejects_material_guide_without_explicit_reading_order_explanation(self):
        self.write_doc(
            "00_材料导读.md",
            "# 张鹏举 (Pengju Zhang) - 材料导读\n\n"
            f"## 这套材料解决什么问题\n这套材料帮助学生建立阅读顺序。{cite('O1')}\n\n"
            "## 建议阅读顺序\n先粗读基础画像，再读领域地图、论文路线和学习向导，最后回看基础画像。\n\n"
            "## 如何阅读引用和证据标记\n[O#] 代表官方或身份来源，[P#] 代表论文来源，[R#] 代表教材、讲义或综述，[B#] 代表背景资料；[未找到] 表示暂缺来源，需人工复核表示判断还不够强。\n\n"
            "## 起步讨论入口\n用一篇目标论文、Fig. 2 核心图和一条平台链路进入讨论。\n\n"
            "## 文件定位\n五份文档按认知阶梯互相支撑。\n\n"
            "## 使用边界\n本材料不做导师评价、不做申请建议、不替代论文和教材。\n\n"
            + MERMAID_BLOCK
            + "\n"
            "## 参考文献与资料\n\n"
            "### 官方与身份资料\n\n"
            + SOURCE_TABLE_HEADER
            + "|:---|:---|:---|:---|:---|\n"
            + source_table_row("O1"),
        )
        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertIn("[FAIL] 00_材料导读.md 建议阅读顺序缺少分步文字解释", result.messages)
        self.assertIn("[FAIL] 00_材料导读.md 建议阅读顺序缺少阅读顺序表", result.messages)

    def test_rejects_machine_files_in_professor_root(self):
        (self.prof / "latest.txt").write_text("20260704_010203\n", encoding="utf-8")
        (self.prof / "career_stages.json").write_text("{}", encoding="utf-8")
        (self.prof / "archive").mkdir()

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertIn("[FAIL] 导师根目录不得包含机器文件或目录: latest.txt", result.messages)
        self.assertIn("[FAIL] 导师根目录不得包含机器文件或目录: career_stages.json", result.messages)
        self.assertIn("[FAIL] 导师根目录不得包含机器文件或目录: archive", result.messages)

    def test_accepts_table_visualization_without_mermaid(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        self.write_doc(
            "03_论文路线.md",
            text.replace(MERMAID_BLOCK + "\n", TABLE_VISUAL + "\n"),
        )

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertTrue(result.ok, result.messages)

    def test_rejects_missing_visualization_construct(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        self.write_doc("03_论文路线.md", text.replace(MERMAID_BLOCK + "\n", ""))

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 03_论文路线.md 缺少可视化理解构件：Mermaid、正文表格/矩阵或文本层级树",
            result.messages,
        )

    def test_rejects_overlong_ordinary_body_paragraph(self):
        text = (self.prof / "02_领域地图.md").read_text(encoding="utf-8")
        long_paragraph = "这是一段没有被表格、列表或图示承载的普通正文。" * 32
        self.write_doc(
            "02_领域地图.md",
            text.replace("## 当前方向学科定位\n\n", f"## 当前方向学科定位\n{long_paragraph}\n\n"),
        )

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("02_领域地图.md 普通正文段落过长" in message for message in result.messages),
            result.messages,
        )

    def test_rejects_invalid_mermaid_even_when_table_exists(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        self.write_doc(
            "03_论文路线.md",
            text.replace(MERMAID_BLOCK, "```mermaid\nnotAChart\nA --> B\n```\n" + TABLE_VISUAL),
        )

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertIn("[FAIL] 03_论文路线.md Mermaid 代码块缺少可识别图类型", result.messages)

    def test_rejects_missing_key_claim_evidence_table(self):
        (self.prof / "_internal" / "evidence" / "key_claims.md").unlink()

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertIn("[FAIL] 缺少 _internal/evidence/ 关键判断证据核对表", result.messages)

    def test_rejects_malformed_key_claim_evidence_table(self):
        evidence_file = self.prof / "_internal" / "evidence" / "key_claims.md"
        evidence_file.write_text("# 关键判断证据核对表\n\n| 判断 | 来源 |\n", encoding="utf-8")

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertIn("[FAIL] _internal/evidence/key_claims.md 缺少关键判断证据表头", result.messages)

    def test_rejects_title_without_space_between_chinese_and_english_name(self):
        text = (self.prof / "00_材料导读.md").read_text(encoding="utf-8")
        self.write_doc(
            "00_材料导读.md",
            text.replace("# 张鹏举 (Pengju Zhang)", "# 张鹏举(Pengju Zhang)", 1),
        )

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertFalse(result.ok)
        self.assertTrue(any("一级标题姓名格式" in m for m in result.messages))

    def test_rejects_pipeline_run_info_heading(self):
        text = (self.prof / "02_领域地图.md").read_text(encoding="utf-8")
        self.write_doc("02_领域地图.md", text.replace("## 资料概览", "## 运行信息"))
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("运行信息" in m for m in result.messages))

    def test_rejects_old_phase3_route_table_heading(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        self.write_doc("03_论文路线.md", text.replace("## 论文线怎样连成研究路线", "## 论文路线总表"))
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("论文路线总表" in m for m in result.messages))

    def test_rejects_visible_numbered_mainline_taxonomy(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        self.write_doc(
            "03_论文路线.md",
            text + "\n### 主线一：液相光电子谱\n\n因此，学生可以用下面的路线图理解论文关系。\n\n第一类是前史论文。\n",
        )
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("主线一：" in m for m in result.messages))
        self.assertTrue(any("路线图" in m for m in result.messages))
        self.assertTrue(any("第一类是" in m for m in result.messages))

    def test_rejects_old_phase2_field_tree_heading(self):
        text = (self.prof / "02_领域地图.md").read_text(encoding="utf-8")
        self.write_doc(
            "02_领域地图.md",
            text.replace("## 领域怎样发展到当前问题", "## 领域发展树"),
        )
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("领域发展树" in m for m in result.messages))

    def test_rejects_internal_pipeline_wording_in_final_docs(self):
        text = (self.prof / "02_领域地图.md").read_text(encoding="utf-8")
        text = text.replace("## 证据与待复核点\n需人工复核。", "## 证据与待复核点\n### 给阶段三的检查点\n阶段三应逐篇核对，阶段三只标为分支。")
        self.write_doc("02_领域地图.md", text)
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        text = text.replace("## 从论文路线倒推出的学习准备\n", "## 从论文路线倒推出的学习准备\n阶段四应从论文路线倒推，阶段四可把它作为背景。\n")
        self.write_doc("03_论文路线.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("给阶段三" in m for m in result.messages))
        self.assertTrue(any("阶段四应" in m for m in result.messages))
        self.assertTrue(any("阶段三只" in m for m in result.messages))
        self.assertTrue(any("阶段四可" in m for m in result.messages))

    def test_rejects_internal_learning_guide_handoff_heading(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        self.write_doc(
            "03_论文路线.md",
            text.replace("## 从论文路线倒推出的学习准备", "## 给学习向导的知识点清单"),
        )
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("给学习向导" in m for m in result.messages))

    def test_rejects_internal_phase_range_wording_in_final_docs(self):
        text = (self.prof / "01_基础画像.md").read_text(encoding="utf-8")
        self.write_doc("01_基础画像.md", text + "\n阶段 2-4 可继续使用这些材料。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("阶段 2-4" in m for m in result.messages))

    def test_rejects_internal_auto_table_wording_in_final_docs(self):
        text = (self.prof / "01_基础画像.md").read_text(encoding="utf-8")
        self.write_doc("01_基础画像.md", text + "\n自动论文表保留原始输出。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("自动论文表" in m for m in result.messages))

    def test_rejects_key_paper_label_in_final_docs(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        self.write_doc("03_论文路线.md", text + "\n关键论文不应作为成品文档里的筛选式标签。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("关键论文" in m for m in result.messages))

    def test_rejects_four_deliverable_ladder_wording_in_final_docs(self):
        text = (self.prof / "00_材料导读.md").read_text(encoding="utf-8")
        self.write_doc("00_材料导读.md", text + "\n这四份文档是一条认知阶梯。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("这四份文档" in m for m in result.messages))

    def test_rejects_forbidden_advisor_evaluation(self):
        text = (self.prof / "02_领域地图.md").read_text(encoding="utf-8")
        self.write_doc("02_领域地图.md", text + "\n推荐申请。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("禁用评价语" in m for m in result.messages))

    def test_rejects_overpromising_student_proof_wording(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        self.write_doc("04_学习向导.md", text + "\n这个汇报能证明学生已经理解主线。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("证明学生" in m for m in result.messages))

    def test_rejects_chatty_second_person_writing_in_final_docs(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        self.write_doc(
            "04_学习向导.md",
            text + "\n本文告诉你怎么读论文：我现在缺的是某个概念。\n",
        )
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("告诉你" in m for m in result.messages))
        self.assertTrue(any("我现在缺的是" in m for m in result.messages))

    def test_rejects_project_delivery_wording_in_optional_guides(self):
        self.write_doc("00_材料导读.md", "# 材料导读\n\n## 最小可交付理解\n\n这里是项目交付口吻。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("最小可交付" in m for m in result.messages))

    def test_checks_optional_guide_source_format_when_sources_present(self):
        self.write_doc(
            "00_材料导读.md",
            "# 材料导读\n\n"
            f"这份导读也使用正文引用。{cite('P1')}\n\n"
            "## 参考文献与资料\n\n"
            "### 论文与数据资料\n\n"
            + SOURCE_TABLE_HEADER
            + "|:---|:---|:---|:---|:---|\n"
            + source_table_row("P2"),
        )
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("00_材料导读.md 引用键未在参考文献表中定义" in m for m in result.messages))

    def test_rejects_old_minimal_loop_wording_in_final_docs(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        self.write_doc("04_学习向导.md", text + "\n这里又写回了进组前最小闭环。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("最小闭环" in m for m in result.messages))

    def test_rejects_numbered_phase4_path_headings(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        self.write_doc(
            "04_学习向导.md",
            text
            + "\n## 第一段路：旧标题\n\n"
            + "## 第二段路：旧标题\n\n"
            + "## 第三段路：旧标题\n\n",
        )
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("第一段路" in m for m in result.messages))

    def test_rejects_missing_source_marker(self):
        self.write_doc(
            "04_学习向导.md",
            "# 张鹏举 (Pengju Zhang) - 学习向导\n\n"
            "## 资料概览\n\n"
            "## 终点：进组前应接近什么状态\n\n"
            "## 进组前起步闭环\n\n"
            "一篇主线论文、一张核心图和一条平台链路可以组成进组前起步闭环。\n\n"
            "## 先知道光电子谱到底在看什么\n\n"
            "## 再把静态谱读成时间过程\n\n"
            "## 随后进入阿秒电子运动\n\n"
            "## 进入液相和凝聚相复杂环境\n\n"
            "## 最后把机制论文接回平台边界\n\n"
            "## 回到张鹏举论文路线\n\n"
            "## 进组后先从哪里接上\n\n"
            "## 卡住时怎么判断该补什么\n\n"
            "## 资源指针\n",
        )
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("来源" in m or "资料" in m for m in result.messages))

    def test_rejects_bare_url_in_phase2_body(self):
        text = (self.prof / "02_领域地图.md").read_text(encoding="utf-8")
        text = text.replace(cite("O1"), "https://example.com")
        self.write_doc("02_领域地图.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("裸 URL" in m for m in result.messages))

    def test_rejects_reference_section_before_later_phase_sections(self):
        text = (self.prof / "02_领域地图.md").read_text(encoding="utf-8")
        evidence_heading = "## 证据与待复核点\n需人工复核。\n\n"
        text = text.replace(evidence_heading, "")
        text = text + "\n" + evidence_heading
        self.write_doc("02_领域地图.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("参考文献与资料必须是最后一个二级章节" in m for m in result.messages))

    def test_rejects_plain_body_citation_key_without_superscript_link(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        text = text.replace(cite("P1"), "[P1]")
        self.write_doc("03_论文路线.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("正文引用键必须使用上标链接" in m for m in result.messages))

    def test_rejects_old_markdown_link_citation(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        text = text.replace(cite("P1"), "[P1](#p1)")
        self.write_doc("03_论文路线.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("正文引用键必须使用上标链接" in m for m in result.messages))

    def test_rejects_phase3_citation_key_missing_from_reference_table(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        text = text.replace(cite("P1"), cite("P2"))
        self.write_doc("03_论文路线.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("引用键未在参考文献表中定义" in m for m in result.messages))

    def test_rejects_reference_table_key_without_anchor(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        text = text.replace('<a id="r1"></a>[R1]', "[R1]")
        self.write_doc("04_学习向导.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("参考文献表引用键缺少锚点" in m for m in result.messages))

    def test_rejects_phase4_missing_reference_table_header(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        text = text.replace(SOURCE_TABLE_HEADER.strip(), "| 编号 | 文献或资料 | 链接 |")
        self.write_doc("04_学习向导.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("参考文献表缺少五列表头" in m for m in result.messages))

    def test_rejects_missing_required_section(self):
        text = (self.prof / "03_论文路线.md").read_text(encoding="utf-8")
        text = text.replace("## 当前主线论文\n", "")
        self.write_doc("03_论文路线.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("缺少章节" in m for m in result.messages))

    def test_accepts_professor_specific_phase4_route_heading(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        self.write_doc(
            "04_学习向导.md",
            text.replace("## 回到张鹏举论文路线", "## 回到测试导师论文路线"),
        )

        module = load_module()
        result = module.verify_prof_dir(self.prof)

        self.assertTrue(result.ok, result.messages)

    def test_rejects_missing_phase4_minimal_loop_section(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        text = text.replace("## 进组前起步闭环\n\n", "")
        self.write_doc("04_学习向导.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 缺少章节: ## 进组前起步闭环",
            result.messages,
        )

    def test_rejects_phase4_minimal_loop_without_paper_figure_platform(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        text = text.replace("一篇主线论文、Fig. 2 核心图和一条平台链路可以组成进组前起步闭环。\n\n", "")
        self.write_doc("04_学习向导.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 进组前起步闭环必须同时连接论文、核心图和平台链路",
            result.messages,
        )

    def test_rejects_phase4_minimal_loop_without_concrete_figure_marker(self):
        text = (self.prof / "04_学习向导.md").read_text(encoding="utf-8")
        text = text.replace("Fig. 2 核心图", "一张核心图")
        self.write_doc("04_学习向导.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 进组前起步闭环必须具体到核心图编号或图组",
            result.messages,
        )

    def test_rejects_yaml_frontmatter_before_title(self):
        text = (self.prof / "01_基础画像.md").read_text(encoding="utf-8")
        self.write_doc("01_基础画像.md", "---\nsource: https://example.com\n---\n" + text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertIn("[FAIL] 01_基础画像.md 不使用裸露 frontmatter", result.messages)


if __name__ == "__main__":
    unittest.main()
