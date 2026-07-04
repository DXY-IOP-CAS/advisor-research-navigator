import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / ".claude" / "skills" / "research-advisor" / "scripts" / "verify_phase_docs.py"

spec = importlib.util.spec_from_file_location("verify_phase_docs", VERIFY_PATH)
verify_phase_docs = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["verify_phase_docs"] = verify_phase_docs
spec.loader.exec_module(verify_phase_docs)


SOURCE_TABLE = """## 参考文献与资料

### 官方与身份资料

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|
| <a id="o1"></a>[O1] | 测试来源 | 支撑测试判断 | https://example.com | 官方来源 |
"""


def write_minimal_valid_phase_docs(prof_dir: Path) -> None:
    for filename, sections in verify_phase_docs.DOCS.items():
        lines = [f"# 测试导师 - {filename}", ""]
        for section in sections:
            lines.extend([section, '正文 <sup><a href="#o1">[O1]</a></sup>'])
            if section == verify_phase_docs.PHASE4_MINIMAL_LOOP_HEADING:
                lines.append("一篇论文、Fig. 2 核心图和一条平台链路。")
        if filename == "01_基础画像.md":
            lines.append("来源：https://example.com")
        else:
            lines.append(SOURCE_TABLE)
        (prof_dir / filename).write_text("\n".join(lines), encoding="utf-8")


class PhaseDocsVerifierTests(unittest.TestCase):
    def test_scans_optional_guide_for_forbidden_advisor_evaluation_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            write_minimal_valid_phase_docs(prof_dir)
            (prof_dir / "00_材料导读.md").write_text(
                "# 材料导读\n\n这里不应出现匹配度。",
                encoding="utf-8",
            )

            result = verify_phase_docs.verify_prof_dir(prof_dir)

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 00_材料导读.md 含禁用评价语: 匹配度",
            result.messages,
        )

    def test_rejects_old_layered_training_camp_style(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            write_minimal_valid_phase_docs(prof_dir)
            phase4 = prof_dir / "04_学习向导.md"
            phase4.write_text(
                phase4.read_text(encoding="utf-8")
                + "\n## 旧式补充\n第 1 天训练营：先分语言层、图像层、方法层。\n",
                encoding="utf-8",
            )

            result = verify_phase_docs.verify_prof_dir(prof_dir)

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 含禁用写作风格: 训练营",
            result.messages,
        )
        self.assertIn(
            "[FAIL] 04_学习向导.md 含禁用写作风格: 语言层",
            result.messages,
        )
        self.assertIn(
            "[FAIL] 04_学习向导.md 含固定天数学习安排: 第 1 天",
            result.messages,
        )

    def test_rejects_chatty_second_person_style(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            write_minimal_valid_phase_docs(prof_dir)
            phase4 = prof_dir / "04_学习向导.md"
            phase4.write_text(
                phase4.read_text(encoding="utf-8")
                + "\n本文告诉你怎么读论文：我现在缺的是某个概念。\n",
                encoding="utf-8",
            )

            result = verify_phase_docs.verify_prof_dir(prof_dir)

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 含禁用写作风格: 告诉你",
            result.messages,
        )
        self.assertIn(
            "[FAIL] 04_学习向导.md 含禁用写作风格: 我现在缺的是",
            result.messages,
        )

    def test_accepts_problem_chain_phase4_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            (prof_dir / "01_基础画像.md").write_text(
                "# 测试导师 - 基础画像\n\n## 资料概览\n\n来源：https://example.com\n",
                encoding="utf-8",
            )
            (prof_dir / "02_领域地图.md").write_text(
                """# 测试导师 - 领域地图

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 导师路径速览
## 当前方向学科定位
## 领域怎样发展到当前问题
## 关键问题和技术路线
## 当前前沿
## 证据与待复核点
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "03_论文路线.md").write_text(
                """# 测试导师 - 论文路线

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 先抓住论文在回答什么问题
## 论文线怎样连成研究路线
## 当前主线论文
## 前史积累论文
## 旁支与弱证据
## 从论文路线倒推出的学习准备
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "04_学习向导.md").write_text(
                """# 测试导师 - 学习向导

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 终点：进组前应接近什么状态
## 进组前起步闭环
一篇主线论文、Fig. 2 核心图和一条平台链路可以组成进组前起步闭环。
## 第一段路：先知道光电子谱到底在看什么
## 第二段路：从静态谱走到时间分辨
## 第三段路：从飞秒过程走到阿秒电子运动
## 第四段路：从气相分子走到液相和凝聚相
## 第五段路：从读机制论文走到理解平台论文
## 回到张鹏举论文路线
## 进组后先从哪里接上
## 卡住时怎么判断该补什么
## 资源指针
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )

            result = verify_phase_docs.verify_prof_dir(prof_dir)

        self.assertTrue(result.ok, "\n".join(result.messages))

    def test_requires_phase4_group_entry_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            (prof_dir / "01_基础画像.md").write_text(
                "# 测试导师 - 基础画像\n\n## 资料概览\n\n来源：https://example.com\n",
                encoding="utf-8",
            )
            (prof_dir / "02_领域地图.md").write_text(
                """# 测试导师 - 领域地图

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 导师路径速览
## 当前方向学科定位
## 领域怎样发展到当前问题
## 关键问题和技术路线
## 当前前沿
## 证据与待复核点
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "03_论文路线.md").write_text(
                """# 测试导师 - 论文路线

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 先抓住论文在回答什么问题
## 论文线怎样连成研究路线
## 当前主线论文
## 前史积累论文
## 旁支与弱证据
## 从论文路线倒推出的学习准备
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "04_学习向导.md").write_text(
                """# 测试导师 - 学习向导

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 终点：进组前应接近什么状态
## 进组前起步闭环
一篇主线论文、Fig. 2 核心图和一条平台链路可以组成进组前起步闭环。
## 第一段路：先知道光电子谱到底在看什么
## 第二段路：从静态谱走到时间分辨
## 第三段路：从飞秒过程走到阿秒电子运动
## 第四段路：从气相分子走到液相和凝聚相
## 第五段路：从读机制论文走到理解平台论文
## 回到张鹏举论文路线
## 卡住时怎么判断该补什么
## 资源指针
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )

            result = verify_phase_docs.verify_prof_dir(prof_dir)

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 缺少章节: ## 进组后先从哪里接上",
            result.messages,
        )

    def test_requires_phase4_minimal_group_entry_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            (prof_dir / "01_基础画像.md").write_text(
                "# 测试导师 - 基础画像\n\n## 资料概览\n\n来源：https://example.com\n",
                encoding="utf-8",
            )
            (prof_dir / "02_领域地图.md").write_text(
                """# 测试导师 - 领域地图

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 导师路径速览
## 当前方向学科定位
## 领域怎样发展到当前问题
## 关键问题和技术路线
## 当前前沿
## 证据与待复核点
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "03_论文路线.md").write_text(
                """# 测试导师 - 论文路线

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 先抓住论文在回答什么问题
## 论文线怎样连成研究路线
## 当前主线论文
## 前史积累论文
## 旁支与弱证据
## 从论文路线倒推出的学习准备
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "04_学习向导.md").write_text(
                """# 测试导师 - 学习向导

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 终点：进组前应接近什么状态
## 第一段路：先知道光电子谱到底在看什么
## 第二段路：从静态谱走到时间分辨
## 第三段路：从飞秒过程走到阿秒电子运动
## 第四段路：从气相分子走到液相和凝聚相
## 第五段路：从读机制论文走到理解平台论文
## 回到张鹏举论文路线
## 进组后先从哪里接上
## 卡住时怎么判断该补什么
## 资源指针
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )

            result = verify_phase_docs.verify_prof_dir(prof_dir)

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 缺少章节: ## 进组前起步闭环",
            result.messages,
        )

    def test_requires_phase4_minimal_loop_to_connect_paper_figure_and_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            (prof_dir / "01_基础画像.md").write_text(
                "# 测试导师 - 基础画像\n\n## 资料概览\n\n来源：https://example.com\n",
                encoding="utf-8",
            )
            (prof_dir / "02_领域地图.md").write_text(
                """# 测试导师 - 领域地图

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 导师路径速览
## 当前方向学科定位
## 领域怎样发展到当前问题
## 关键问题和技术路线
## 当前前沿
## 证据与待复核点
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "03_论文路线.md").write_text(
                """# 测试导师 - 论文路线

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 先抓住论文在回答什么问题
## 论文线怎样连成研究路线
## 当前主线论文
## 前史积累论文
## 旁支与弱证据
## 从论文路线倒推出的学习准备
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "04_学习向导.md").write_text(
                """# 测试导师 - 学习向导

## 资料概览
正文 <sup><a href="#o1">[O1]</a></sup>
## 终点：进组前应接近什么状态
## 进组前起步闭环
这一节只泛泛总结学习成果，没有把真实科研入口说清楚。
## 第一段路：先知道光电子谱到底在看什么
## 第二段路：从静态谱走到时间分辨
## 第三段路：从飞秒过程走到阿秒电子运动
## 第四段路：从气相分子走到液相和凝聚相
## 第五段路：从读机制论文走到理解平台论文
## 回到张鹏举论文路线
## 进组后先从哪里接上
## 卡住时怎么判断该补什么
## 资源指针
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )

            result = verify_phase_docs.verify_prof_dir(prof_dir)

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 进组前起步闭环必须同时连接论文、核心图和平台链路",
            result.messages,
        )

    def test_rejects_old_minimal_loop_wording(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            write_minimal_valid_phase_docs(prof_dir)
            phase4 = prof_dir / "04_学习向导.md"
            phase4.write_text(
                phase4.read_text(encoding="utf-8") + "\n这里又写回了进组前最小闭环。\n",
                encoding="utf-8",
            )

            result = verify_phase_docs.verify_prof_dir(prof_dir)

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 04_学习向导.md 含禁用写作风格: 最小闭环",
            result.messages,
        )

    def test_rejects_visible_frontmatter_in_phase_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            write_minimal_valid_phase_docs(prof_dir)
            phase2 = prof_dir / "02_领域地图.md"
            phase2.write_text(
                "---\nsource: https://example.com\n---\n" + phase2.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            result = verify_phase_docs.verify_prof_dir(prof_dir)

        self.assertFalse(result.ok)
        self.assertIn("[FAIL] 02_领域地图.md 不使用裸露 frontmatter", result.messages)


if __name__ == "__main__":
    unittest.main()
