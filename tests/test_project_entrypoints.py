import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectEntrypointDocsTests(unittest.TestCase):
    def test_agents_md_leads_with_e2e_quality_path(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("Fact Pack -> Cognitive Blueprint -> 00-04", text)
        self.assertNotIn("四阶段流水线", text)


if __name__ == "__main__":
    unittest.main()
