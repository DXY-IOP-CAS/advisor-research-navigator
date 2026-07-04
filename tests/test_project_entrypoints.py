import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectEntrypointDocsTests(unittest.TestCase):
    def test_agents_md_leads_with_e2e_quality_path(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("Fact Pack -> Cognitive Blueprint -> 00-04", text)
        self.assertNotIn("四阶段流水线", text)

    def test_claude_md_defers_to_agents_md_without_duplicate_rules(self):
        text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

        self.assertIn("AGENTS.md 是当前项目规则的单一事实源", text)
        self.assertIn("不要在 CLAUDE.md 里新增或复制项目规则", text)
        self.assertNotIn("## 硬约束", text)
        self.assertNotIn("来源必标 URL", text)
        self.assertNotIn("## 目录角色", text)

    def test_obsolete_run_py_entrypoint_is_removed(self):
        self.assertFalse(
            (ROOT / "src" / "phase1" / "run.py").exists(),
            "run.py should not remain as a parallel phase1 orchestration entrypoint",
        )

        active_docs = [
            ROOT / "QUICKSTART.md",
            ROOT / "docs" / "计划书.md",
            ROOT / "src" / "phase1" / "pipeline.md",
        ]
        leaked = []
        for path in active_docs:
            text = path.read_text(encoding="utf-8")
            if "run.py" in text:
                leaked.append(str(path.relative_to(ROOT)))

        self.assertEqual([], leaked, "active entrypoint docs should not route agents through run.py")

    def test_plan_uses_e2e_quality_design_heading(self):
        text = (ROOT / "docs" / "计划书.md").read_text(encoding="utf-8")

        self.assertIn("第2章: 端到端质量重构设计", text)
        self.assertNotIn("第2章: 四阶段流水线设计", text)

    def test_plan_does_not_retain_legacy_version_footer(self):
        text = (ROOT / "docs" / "计划书.md").read_text(encoding="utf-8")

        forbidden = ["**版本**：v5.0", "**下次更新**："]
        found = [phrase for phrase in forbidden if phrase in text]
        if found:
            self.fail(f"docs/计划书.md retains legacy footer markers: {found}")

    def test_pipeline_does_not_call_run_py_old_unified_entrypoint(self):
        text = (ROOT / "src" / "phase1" / "pipeline.md").read_text(encoding="utf-8")

        self.assertNotIn("旧统一入口", text)
        self.assertNotIn("兼容调试捷径（run.py）", text)

    def test_pipeline_examples_do_not_manual_expand_current_archive_path(self):
        text = (ROOT / "src" / "phase1" / "pipeline.md").read_text(encoding="utf-8")

        self.assertNotIn("$(cat \"$PROF/_internal/latest.txt\"", text)
        self.assertIn("validate_career_stages.py --prof-dir", text)
        self.assertIn("validate_verified_ids.py --prof-dir", text)

    def test_pipeline_does_not_document_root_latest_compatibility(self):
        text = (ROOT / "src" / "phase1" / "pipeline.md").read_text(encoding="utf-8")

        self.assertNotIn("旧版根目录 `latest.txt`", text)
        self.assertNotIn("根目录 `latest.txt` 只作过渡兼容", text)

    def test_legacy_archive_previous_entrypoint_is_removed(self):
        for path in [ROOT / "AGENTS.md", ROOT / "CLAUDE.md"]:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("archive_previous / utils", text, str(path))

        pipeline = (ROOT / "src" / "phase1" / "pipeline.md").read_text(encoding="utf-8")
        self.assertNotIn("### 自动存档机制", pipeline)
        self.assertNotIn("该命令在阶段 A 开始前执行", pipeline)
        self.assertNotIn("archive_previous.py", pipeline)
        self.assertFalse(
            (ROOT / "src" / "phase1" / "archive_previous.py").exists(),
            "archive_previous.py should not remain as an archive-writing legacy entrypoint",
        )

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

    def test_phase1_init_stdout_is_not_archive_entrypoint(self):
        text = (ROOT / "src" / "phase1" / "phase1_init.py").read_text(encoding="utf-8")

        self.assertNotIn("打印 archive 路径供后续步骤使用", text)
        self.assertNotIn("archive_dir:", text)
        self.assertNotIn("print(archive)", text)
        self.assertIn("print(base)", text)

    def test_phase1_references_use_prof_dir_for_step_outputs(self):
        text = (
            ROOT / ".claude" / "skills" / "research-advisor" / "references" / "01-data-sources.md"
        ).read_text(encoding="utf-8")

        forbidden = ["-o 01_gs.json", "-o 02_oa.json", "-o 03_arxiv.json"]
        leaked = [phrase for phrase in forbidden if phrase in text]
        self.assertEqual([], leaked, "phase1 source examples should write through --prof-dir")
        self.assertIn("--prof-dir \"output/...\"", text)

    def test_research_advisor_skill_uses_spaced_bilingual_name_contract(self):
        text = (ROOT / ".claude" / "skills" / "research-advisor" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("中文名 (English Name)", text)
        self.assertNotIn("中文名(English Name)", text)

    def test_active_skill_references_do_not_keep_local_version_footers(self):
        refs_dir = ROOT / ".claude" / "skills" / "research-advisor" / "references"
        leaked = []
        for path in refs_dir.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if "**版本**:" in text or "**生成日期**:" in text:
                leaked.append(str(path.relative_to(ROOT)))

        self.assertEqual([], leaked, "active skill references should rely on git history, not local version footers")

    def test_phase1_script_usage_examples_prefer_prof_dir(self):
        files = [
            ROOT / "src" / "phase1" / "step2_gs.py",
            ROOT / "src" / "phase1" / "step3_openalex.py",
            ROOT / "src" / "phase1" / "step4_arxiv_id.py",
            ROOT / "src" / "phase1" / "step5_arxiv.py",
            ROOT / "src" / "phase1" / "step6_merge.py",
            ROOT / "src" / "phase1" / "render_profile.py",
        ]
        forbidden = [
            "-o output/<机构>",
            "-o 03_arxiv.json",
            "-o <output_path>",
            "run.py",
            "01_gs.json 02_oa.json 03_arxiv.json -o 04_merged.json",
            "render_profile.py 04_merged.json -o 01_基础画像.md",
        ]

        leaked = []
        for path in files:
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                if phrase in text:
                    leaked.append(f"{path.relative_to(ROOT)} contains {phrase}")

        self.assertEqual([], leaked, "phase1 script usage examples should default to --prof-dir")

    def test_phase1_cli_help_does_not_expose_archive_dir(self):
        scripts = [
            ROOT / "src" / "phase1" / "step2_gs.py",
            ROOT / "src" / "phase1" / "step3_openalex.py",
            ROOT / "src" / "phase1" / "step4_arxiv_id.py",
            ROOT / "src" / "phase1" / "step5_arxiv.py",
            ROOT / "src" / "phase1" / "step6_merge.py",
            ROOT / "src" / "phase1" / "render_profile.py",
            ROOT / "src" / "phase1" / "verify_profile.py",
        ]

        leaked = []
        env = {
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
        for script in scripts:
            result = subprocess.run(
                [sys.executable, str(script), "--help"],
                cwd=ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            help_text = result.stdout + result.stderr
            for phrase in ("--archive-dir", "archive 目录", "archive_dir", "archive"):
                if phrase in help_text:
                    leaked.append(f"{script.relative_to(ROOT)} exposes {phrase}")

        self.assertEqual([], leaked, "phase1 public CLI help should route agents through --prof-dir only")

    def test_render_profile_docstring_matches_current_ai_edit_contract(self):
        text = (ROOT / "src" / "phase1" / "render_profile.py").read_text(encoding="utf-8")

        forbidden = ["5 年默认段", "脚本不写的内容", "学术履历表格     - 研究方向描述"]
        leaked = [phrase for phrase in forbidden if phrase in text]
        self.assertEqual([], leaked, "render_profile docs should match current §2 auto-render contract")
        self.assertIn("§2 学术履历表", text)
        self.assertIn("AI 只补充叙事占位符", text)

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
            ROOT / "src" / "phase1" / "archive_previous.py",
            ROOT / "src" / "phase1" / "merge_tables.py",
            ROOT / "src" / "phase1" / "run.py",
        ]

        existing = [str(path.relative_to(ROOT)) for path in obsolete if path.exists()]
        self.assertEqual([], existing, "obsolete phase1 helpers should not remain as parallel entrypoints")

    def test_active_docs_do_not_reference_obsolete_phase1_helpers(self):
        obsolete = ["archive_step.py", "archive_previous.py", "merge_tables.py", "run.py"]
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
