import subprocess
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

    def test_phase1_entrypoint_docs_require_official_url_seed(self):
        files = [
            ROOT / "QUICKSTART.md",
            ROOT / ".claude" / "skills" / "research-advisor" / "SKILL.md",
            ROOT / "src" / "phase1" / "pipeline.md",
        ]

        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertIn("--official-url", text, str(path))
            self.assertIn("seed.json", text, str(path))

    def test_tracked_professor_roots_expose_only_final_docs_or_internal(self):
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "ls-files", "output"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        allowed_root_files = {
            "00_材料导读.md",
            "01_基础画像.md",
            "02_领域地图.md",
            "03_论文路线.md",
            "04_学习向导.md",
        }
        leaked = []
        for raw_path in result.stdout.splitlines():
            path = Path(raw_path)
            parts = path.parts
            if "archive" in parts or "_internal" in parts:
                continue
            if path.name not in allowed_root_files:
                leaked.append(raw_path)

        self.assertEqual([], leaked, "tracked professor roots contain exposed machine/process files")


if __name__ == "__main__":
    unittest.main()
