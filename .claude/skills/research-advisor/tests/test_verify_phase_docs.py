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
            "## 运行信息\n资料链接：https://example.com\n",
        )
        self.write_doc(
            "02_领域地图.md",
            "# 张鹏举 (Pengju Zhang) - 领域地图\n\n"
            f"## 运行信息\n官方方向以导师主页为准。{cite('O1')}\n\n"
            "## 导师路径速览\n\n"
            "## 当前方向学科定位\n\n"
            "## 领域发展树\n\n"
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
            f"## 运行信息\n论文路线以代表论文为准。{cite('P1')}\n\n"
            "## 领域树节点定义\n\n"
            "## 论文路线总表\n\n"
            "## 当前主线论文\n\n"
            "## 前史积累论文\n\n"
            "## 旁支与弱证据\n需人工复核。\n\n"
            "## 给学习向导的知识点清单\n\n"
            "## 参考文献与资料\n\n"
            "### 论文与数据资料\n\n"
            + SOURCE_TABLE_HEADER
            + "|:---|:---|:---|:---|:---|\n"
            + source_table_row("P1"),
        )
        self.write_doc(
            "04_学习向导.md",
            "# 张鹏举 (Pengju Zhang) - 学习向导\n\n"
            f"## 运行信息\n学习路径以课程和综述倒推。{cite('R1')}\n\n"
            "## 读者起点\n\n"
            "## 学习主线总图\n\n"
            "## 数学基础\n\n"
            "## 物理基础\n\n"
            "## 领域核心工具\n\n"
            "## 导师当前方向专题\n\n"
            "## 论文阅读顺序\n\n"
            "## 概念小字典\n\n"
            "## 论文阅读训练\n\n"
            "## 阶段产出物\n\n"
            "## 自测与复盘\n\n"
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

    def test_rejects_forbidden_advisor_evaluation(self):
        text = (self.prof / "02_领域地图.md").read_text(encoding="utf-8")
        self.write_doc("02_领域地图.md", text + "\n推荐申请。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("禁用评价语" in m for m in result.messages))

    def test_rejects_missing_source_marker(self):
        self.write_doc(
            "04_学习向导.md",
            "# 张鹏举 (Pengju Zhang) - 学习向导\n\n"
            "## 运行信息\n\n"
            "## 读者起点\n\n"
            "## 学习主线总图\n\n"
            "## 数学基础\n\n"
            "## 物理基础\n\n"
            "## 领域核心工具\n\n"
            "## 导师当前方向专题\n\n"
            "## 论文阅读顺序\n\n"
            "## 概念小字典\n\n"
            "## 论文阅读训练\n\n"
            "## 阶段产出物\n\n"
            "## 自测与复盘\n\n"
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

    def test_accepts_yaml_frontmatter_before_title(self):
        text = (self.prof / "01_基础画像.md").read_text(encoding="utf-8")
        self.write_doc("01_基础画像.md", "---\nsource: https://example.com\n---\n" + text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertTrue(result.ok, result.messages)


if __name__ == "__main__":
    unittest.main()
