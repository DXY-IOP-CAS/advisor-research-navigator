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


class PhaseDocsVerifierTests(unittest.TestCase):
    def test_accepts_problem_chain_phase4_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            (prof_dir / "01_基础画像.md").write_text(
                "# 测试导师 - 基础画像\n\n## 运行信息\n\n来源：https://example.com\n",
                encoding="utf-8",
            )
            (prof_dir / "02_领域地图.md").write_text(
                """# 测试导师 - 领域地图

## 运行信息
正文 <sup><a href="#o1">[O1]</a></sup>
## 导师路径速览
## 当前方向学科定位
## 领域发展树
## 关键问题和技术路线
## 当前前沿
## 证据与待复核点
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "03_论文路线.md").write_text(
                """# 测试导师 - 论文路线

## 运行信息
正文 <sup><a href="#o1">[O1]</a></sup>
## 先抓住论文在回答什么问题
## 论文路线总表
## 当前主线论文
## 前史积累论文
## 旁支与弱证据
## 给学习向导的知识点清单
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "04_学习向导.md").write_text(
                """# 测试导师 - 学习向导

## 运行信息
正文 <sup><a href="#o1">[O1]</a></sup>
## 终点：进组前应接近什么状态
## 进组前最小闭环
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
                "# 测试导师 - 基础画像\n\n## 运行信息\n\n来源：https://example.com\n",
                encoding="utf-8",
            )
            (prof_dir / "02_领域地图.md").write_text(
                """# 测试导师 - 领域地图

## 运行信息
正文 <sup><a href="#o1">[O1]</a></sup>
## 导师路径速览
## 当前方向学科定位
## 领域发展树
## 关键问题和技术路线
## 当前前沿
## 证据与待复核点
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "03_论文路线.md").write_text(
                """# 测试导师 - 论文路线

## 运行信息
正文 <sup><a href="#o1">[O1]</a></sup>
## 先抓住论文在回答什么问题
## 论文路线总表
## 当前主线论文
## 前史积累论文
## 旁支与弱证据
## 给学习向导的知识点清单
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "04_学习向导.md").write_text(
                """# 测试导师 - 学习向导

## 运行信息
正文 <sup><a href="#o1">[O1]</a></sup>
## 终点：进组前应接近什么状态
## 进组前最小闭环
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
                "# 测试导师 - 基础画像\n\n## 运行信息\n\n来源：https://example.com\n",
                encoding="utf-8",
            )
            (prof_dir / "02_领域地图.md").write_text(
                """# 测试导师 - 领域地图

## 运行信息
正文 <sup><a href="#o1">[O1]</a></sup>
## 导师路径速览
## 当前方向学科定位
## 领域发展树
## 关键问题和技术路线
## 当前前沿
## 证据与待复核点
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "03_论文路线.md").write_text(
                """# 测试导师 - 论文路线

## 运行信息
正文 <sup><a href="#o1">[O1]</a></sup>
## 先抓住论文在回答什么问题
## 论文路线总表
## 当前主线论文
## 前史积累论文
## 旁支与弱证据
## 给学习向导的知识点清单
"""
                + SOURCE_TABLE,
                encoding="utf-8",
            )
            (prof_dir / "04_学习向导.md").write_text(
                """# 测试导师 - 学习向导

## 运行信息
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
            "[FAIL] 04_学习向导.md 缺少章节: ## 进组前最小闭环",
            result.messages,
        )


if __name__ == "__main__":
    unittest.main()
