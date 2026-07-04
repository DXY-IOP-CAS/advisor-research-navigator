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

        run_py = (ROOT / "src" / "phase1" / "run.py").read_text(encoding="utf-8")
        self.assertNotIn("统一入口", run_py)
        self.assertIn("兼容调试捷径", run_py)

    def test_plan_uses_e2e_quality_design_heading(self):
        text = (ROOT / "docs" / "计划书.md").read_text(encoding="utf-8")

        self.assertIn("第2章: 端到端质量重构设计", text)
        self.assertNotIn("第2章: 四阶段流水线设计", text)

    def test_pipeline_does_not_call_run_py_old_unified_entrypoint(self):
        text = (ROOT / "src" / "phase1" / "pipeline.md").read_text(encoding="utf-8")

        self.assertNotIn("旧统一入口", text)
        self.assertIn("兼容调试捷径（run.py）", text)

    def test_pipeline_examples_do_not_manual_expand_current_archive_path(self):
        text = (ROOT / "src" / "phase1" / "pipeline.md").read_text(encoding="utf-8")

        self.assertNotIn("$(cat \"$PROF/_internal/latest.txt\"", text)
        self.assertIn("validate_career_stages.py --prof-dir", text)
        self.assertIn("validate_verified_ids.py --prof-dir", text)

    def test_legacy_archive_previous_is_not_presented_as_current_entrypoint(self):
        for path in [ROOT / "AGENTS.md", ROOT / "CLAUDE.md"]:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("archive_previous / utils", text, str(path))

        pipeline = (ROOT / "src" / "phase1" / "pipeline.md").read_text(encoding="utf-8")
        self.assertNotIn("### 自动存档机制", pipeline)
        self.assertNotIn("该命令在阶段 A 开始前执行", pipeline)
        self.assertIn("### 旧版整目录存档", pipeline)

        archive_previous = (ROOT / "src" / "phase1" / "archive_previous.py").read_text(encoding="utf-8")
        self.assertNotIn("运行前自动存档已有产出", archive_previous)
        self.assertIn("旧版整目录迁移工具", archive_previous)

        run_py = (ROOT / "src" / "phase1" / "run.py").read_text(encoding="utf-8")
        self.assertNotIn("自动处理：存档旧版", run_py)
        self.assertIn("兼容旧流程", run_py)

    def test_archive_rule_distinguishes_manual_reads_from_prof_dir_tools(self):
        files = [
            ROOT / "AGENTS.md",
            ROOT / "QUICKSTART.md",
            ROOT / ".claude" / "skills" / "research-advisor" / "SKILL.md",
        ]

        required_phrase = "脚本通过 `--prof-dir` / `ProfDirResolver` 读取当前 active `_internal/archive/<ts>` 不属于手动读取 archive"
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertIn(required_phrase, text, str(path))

        plan = (ROOT / "docs" / "计划书.md").read_text(encoding="utf-8")
        self.assertNotIn("不作为普通收口命令直接运行", plan)
        self.assertIn(required_phrase, plan)

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

    def test_phase1_strategy_is_not_a_parallel_docs_entrypoint(self):
        self.assertFalse(
            (ROOT / "docs" / "phase1运行策略.md").exists(),
            "Phase 1 strategy must live in research-advisor references and src/phase1/pipeline.md",
        )

        pipeline = (ROOT / "src" / "phase1" / "pipeline.md").read_text(encoding="utf-8")
        self.assertNotIn("docs/phase1运行策略.md", pipeline)

    def test_obsolete_phase1_helpers_are_removed(self):
        obsolete = [
            ROOT / "src" / "phase1" / "archive_step.py",
            ROOT / "src" / "phase1" / "merge_tables.py",
        ]

        existing = [str(path.relative_to(ROOT)) for path in obsolete if path.exists()]
        self.assertEqual([], existing, "obsolete phase1 helpers should not remain as parallel entrypoints")

    def test_active_docs_do_not_reference_obsolete_phase1_helpers(self):
        obsolete = ["archive_step.py", "merge_tables.py"]
        active_docs = [
            ROOT / "QUICKSTART.md",
            ROOT / "AGENTS.md",
            ROOT / "src" / "phase1" / "pipeline.md",
            ROOT / ".claude" / "skills" / "research-advisor" / "SKILL.md",
            ROOT / ".claude" / "skills" / "research-advisor" / "references" / "phase1-core.md",
            ROOT / ".claude" / "skills" / "research-advisor" / "references" / "phase1-recovery.md",
        ]

        leaked = []
        for path in active_docs:
            text = path.read_text(encoding="utf-8")
            for helper in obsolete:
                if helper in text:
                    leaked.append(f"{path.relative_to(ROOT)} references {helper}")

        self.assertEqual([], leaked, "active docs should not send agents to removed helper scripts")

    def test_e2e_minimal_prompt_rules_live_in_quickstart(self):
        self.assertFalse(
            (ROOT / "END_TO_END_TEST.md").exists(),
            "Minimal-prompt E2E rules should not remain as a parallel root entrypoint",
        )

        quickstart = (ROOT / "QUICKSTART.md").read_text(encoding="utf-8")
        self.assertIn("端到端回归", quickstart)
        self.assertIn("只给三行最小输入", quickstart)
        self.assertIn("不要在 prompt 里附已知 GS ID", quickstart)
        self.assertIn("docs/e2e/YYYY-MM-DD-<name>-minimal-prompt.md", quickstart)

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
