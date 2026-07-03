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


class VerifyPhaseDocsTest(unittest.TestCase):
    def setUp(self):
        workspace_tmp = Path(__file__).resolve().parents[4] / ".tmp" / "verify_phase_docs_tests"
        workspace_tmp.mkdir(parents=True, exist_ok=True)
        self.prof = workspace_tmp / f"case_{uuid.uuid4().hex}"
        self.prof.mkdir(parents=True, exist_ok=False)
        self.write_doc("01_基础画像.md", "# 张鹏举 (Pengju Zhang) — 基础画像\n\n## 运行信息\n来源：https://example.com\n")
        self.write_doc(
            "02_领域脉络.md",
            "# 张鹏举 (Pengju Zhang) — 领域脉络\n\n"
            "## 运行信息\n来源：[O1]\n\n"
            "## 导师路径速览\n\n## 当前方向学科定位\n\n## 领域发展树\n\n"
            "## 关键问题和技术路线\n\n## 当前前沿\n\n## 来源与待复核点\n需人工复核。\n\n"
            "## 参考文献与来源\n\n"
            "### 官方与身份来源\n\n"
            "| 编号 | 来源 | 用途 | 链接 | 备注 |\n"
            "|:---|:---|:---|:---|:---|\n"
            "| [O1] | 示例官网 | 支撑运行信息来源 | https://example.com | 测试来源 |\n",
        )
        self.write_doc(
            "03_论文定位.md",
            "# 张鹏举 (Pengju Zhang) — 论文定位\n\n"
            "## 运行信息\n来源：[P1]\n\n"
            "## 领域树节点定义\n\n## 论文定位总表\n\n## 当前主线论文\n\n"
            "## 前史积累论文\n\n## 旁支与弱证据\n需人工复核。\n\n"
            "## 给学习讲义的知识点清单\n\n"
            "## 参考文献与来源\n\n"
            "### 论文与数据来源\n\n"
            "| 编号 | 来源 | 用途 | 链接 | 备注 |\n"
            "|:---|:---|:---|:---|:---|\n"
            "| [P1] | 示例论文 | 支撑论文定位来源 | https://example.com/paper | 测试来源 |\n",
        )
        self.write_doc(
            "04_学习讲义.md",
            "# 张鹏举 (Pengju Zhang) — 学习讲义\n\n"
            "## 运行信息\n来源：[R1]\n\n"
            "## 读者起点\n\n## 学习主线总图\n\n## 数学基础\n\n## 物理基础\n\n"
            "## 领域核心工具\n\n## 导师当前方向专题\n\n## 论文阅读顺序\n\n## 资源指针\n\n"
            "## 参考文献与来源\n\n"
            "### 综述、教材与课程来源\n\n"
            "| 编号 | 来源 | 用途 | 链接 | 备注 |\n"
            "|:---|:---|:---|:---|:---|\n"
            "| [R1] | 示例讲义 | 支撑学习路径来源 | https://example.com/course | 测试来源 |\n",
        )

    def write_doc(self, name, text):
        (self.prof / name).write_text(text, encoding="utf-8")

    def test_accepts_complete_phase_docs(self):
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertTrue(result.ok, result.messages)

    def test_rejects_forbidden_advisor_evaluation(self):
        self.write_doc("02_领域脉络.md", (self.prof / "02_领域脉络.md").read_text(encoding="utf-8") + "\n推荐申请。\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("禁用评价语" in m for m in result.messages))

    def test_rejects_missing_source_marker(self):
        self.write_doc("04_学习讲义.md", "# 张鹏举 (Pengju Zhang) — 学习讲义\n\n## 运行信息\n\n## 读者起点\n\n## 学习主线总图\n\n## 数学基础\n\n## 物理基础\n\n## 领域核心工具\n\n## 导师当前方向专题\n\n## 论文阅读顺序\n\n## 资源指针\n")
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("来源" in m for m in result.messages))

    def test_rejects_bare_url_in_phase2_body(self):
        text = (self.prof / "02_领域脉络.md").read_text(encoding="utf-8")
        text = text.replace("来源：[O1]", "来源：https://example.com")
        self.write_doc("02_领域脉络.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("裸 URL" in m for m in result.messages))

    def test_rejects_phase3_citation_key_missing_from_source_table(self):
        text = (self.prof / "03_论文定位.md").read_text(encoding="utf-8")
        text = text.replace("来源：[P1]", "来源：[P2]")
        self.write_doc("03_论文定位.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("引用键未在来源表中定义" in m for m in result.messages))

    def test_rejects_phase4_missing_source_table_header(self):
        text = (self.prof / "04_学习讲义.md").read_text(encoding="utf-8")
        text = text.replace("| 编号 | 来源 | 用途 | 链接 | 备注 |", "| 编号 | 来源 | 链接 |")
        self.write_doc("04_学习讲义.md", text)
        module = load_module()
        result = module.verify_prof_dir(self.prof)
        self.assertFalse(result.ok)
        self.assertTrue(any("来源表缺少五列表头" in m for m in result.messages))

    def test_rejects_missing_required_section(self):
        text = (self.prof / "03_论文定位.md").read_text(encoding="utf-8").replace("## 当前主线论文\n", "")
        self.write_doc("03_论文定位.md", text)
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
