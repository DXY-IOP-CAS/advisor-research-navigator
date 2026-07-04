import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectEntrypointDocsTests(unittest.TestCase):
    def test_agents_md_leads_with_e2e_quality_path(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("Fact Pack -> Cognitive Blueprint -> 00-04", text)
        self.assertNotIn("四阶段流水线", text)

    def test_plan_does_not_present_run_py_as_primary_entrypoint(self):
        text = (ROOT / "docs" / "计划书.md").read_text(encoding="utf-8")
        forbidden = [
            "run.py                         # 统一入口",
            "`run.py` — 统一入口",
        ]

        found = [phrase for phrase in forbidden if phrase in text]
        self.assertEqual([], found, "docs/计划书.md still presents run.py as primary entrypoint")
        self.assertIn("run.py                         # 兼容调试捷径", text)
        self.assertIn("`run.py` — 兼容调试捷径", text)


if __name__ == "__main__":
    unittest.main()
