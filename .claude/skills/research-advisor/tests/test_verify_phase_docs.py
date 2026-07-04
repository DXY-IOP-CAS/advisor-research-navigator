import importlib.util
import sys
import unittest
import uuid
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_phase_docs.py"


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


class VerifyPhaseDocsTest(unittest.TestCase):
    def setUp(self):
        workspace_tmp = Path(__file__).resolve().parents[4] / ".tmp" / "verify_phase_docs_tests"
        workspace_tmp.mkdir(parents=True, exist_ok=True)
        self.prof = workspace_tmp / f"case_{uuid.uuid4().hex}"
        self.prof.mkdir(parents=True, exist_ok=False)
        self.write_doc(
            "01_基础画像.md",
            "# 张鹏举 (Pengju Zhang) - 基础画像\n\n"
            "## 资料概览\n资料链接：https://example.com\n",
        )
        self.write_doc(
            "02_领域地图.md",
            "# 张鹏举 (Pengju Zhang) - 领域地图\n\n"
            f"## 资料概览\n官方方向以导师主页为准。{cite('O1')}\n\n"
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
            "## 终点：进组前应接近什么状态\n\n"
            "## 进组前起步闭环\n\n"
            "一篇主线论文、Fig. 2 核心图和一条平台链路可以组成进组前起步闭环。\n\n"
            "## 第一段路：先知道光电子谱到底在看什么\n\n"
            "## 第二段路：从静态谱走到时间分辨\n\n"
            "## 第三段路：从飞秒过程走到阿秒电子运动\n\n"
            "## 第四段路：从气相分子走到液相和凝聚相\n\n"
            "## 第五段路：从读机制论文走到理解平台论文\n\n"
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

    def test_rejects_missing_source_marker(self):
        self.write_doc(
            "04_学习向导.md",
            "# 张鹏举 (Pengju Zhang) - 学习向导\n\n"
            "## 资料概览\n\n"
            "## 终点：进组前应接近什么状态\n\n"
            "## 进组前起步闭环\n\n"
            "一篇主线论文、一张核心图和一条平台链路可以组成进组前起步闭环。\n\n"
            "## 第一段路：先知道光电子谱到底在看什么\n\n"
            "## 第二段路：从静态谱走到时间分辨\n\n"
            "## 第三段路：从飞秒过程走到阿秒电子运动\n\n"
            "## 第四段路：从气相分子走到液相和凝聚相\n\n"
            "## 第五段路：从读机制论文走到理解平台论文\n\n"
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
