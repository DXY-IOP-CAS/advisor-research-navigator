import importlib.util
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_mermaid_render.py"


def load_module():
    if not SCRIPT.exists():
        raise AssertionError(f"missing production script: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("verify_mermaid_render", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class VerifyMermaidRenderTest(unittest.TestCase):
    def setUp(self):
        workspace_tmp = Path(__file__).resolve().parents[4] / ".tmp" / "verify_mermaid_tests"
        workspace_tmp.mkdir(parents=True, exist_ok=True)
        self.prof = workspace_tmp / f"case_{uuid.uuid4().hex}"
        self.prof.mkdir(parents=True, exist_ok=False)

    def write_doc(self, name: str, text: str):
        (self.prof / name).write_text(text, encoding="utf-8")

    def test_extracts_mermaid_blocks_from_phase_docs(self):
        module = load_module()
        self.write_doc(
            "00_材料导读.md",
            "# 导读\n\n```mermaid\nflowchart LR\n    A --> B\n```\n",
        )
        self.write_doc(
            "04_学习向导.md",
            "# 学习向导\n\n```mermaid\nflowchart TD\n    C --> D\n```\n",
        )
        self.write_doc("_internal.md", "```mermaid\nflowchart LR\nX --> Y\n```\n")

        blocks = module.extract_mermaid_blocks(self.prof)

        self.assertEqual([block.filename for block in blocks], ["00_材料导读.md", "04_学习向导.md"])
        self.assertEqual(blocks[0].index, 1)
        self.assertIn("flowchart LR", blocks[0].code)
        self.assertIn("flowchart TD", blocks[1].code)

    def test_verify_blocks_invokes_renderer_for_each_block(self):
        module = load_module()
        blocks = [
            module.MermaidBlock("00_材料导读.md", 1, "flowchart LR\nA --> B"),
            module.MermaidBlock("04_学习向导.md", 1, "flowchart TD\nC --> D"),
        ]
        rendered = []

        result = module.verify_blocks(blocks, lambda block: rendered.append(block.filename))

        self.assertTrue(result.ok)
        self.assertEqual(rendered, ["00_材料导读.md", "04_学习向导.md"])

    def test_verify_blocks_reports_renderer_failure(self):
        module = load_module()
        blocks = [module.MermaidBlock("03_论文路线.md", 1, "flowchart LR\nA -->")]

        def fail_renderer(block):
            raise RuntimeError("parse error")

        result = module.verify_blocks(blocks, fail_renderer)

        self.assertFalse(result.ok)
        self.assertIn("[FAIL] 03_论文路线.md Mermaid #1 render failed: parse error", result.messages)

    def test_verify_blocks_skips_when_no_blocks_exist(self):
        module = load_module()

        result = module.verify_blocks([], lambda block: None)

        self.assertTrue(result.ok)
        self.assertIn("[OK] 未找到 Mermaid 代码块，渲染门跳过", result.messages)

    def test_puppeteer_config_uses_no_sandbox_without_bom(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            config = module.write_puppeteer_config(Path(tmp))
            raw = config.read_bytes()

        self.assertTrue(raw.startswith(b"{"))
        self.assertNotEqual(b"\xef\xbb\xbf", raw[:3])
        self.assertIn(b"--no-sandbox", raw)
        self.assertIn(b"--disable-setuid-sandbox", raw)

    def test_render_block_with_command_passes_puppeteer_config(self):
        module = load_module()
        block = module.MermaidBlock("02_领域地图.md", 1, "flowchart TD\nA --> B")

        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            config = temp_dir / "puppeteer.json"
            config.write_text('{"args":["--no-sandbox"]}', encoding="utf-8")

            def fake_run(cmd, **kwargs):
                output_path = Path(cmd[cmd.index("-o") + 1])
                output_path.write_text("<svg></svg>", encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, "", "")

            with patch.object(module.subprocess, "run", side_effect=fake_run) as run_mock:
                module.render_block_with_command(block, ["npx", "--yes", "@mermaid-js/mermaid-cli"], temp_dir, config)

        command = run_mock.call_args.args[0]
        self.assertIn("-p", command)
        self.assertEqual(str(config), command[command.index("-p") + 1])


if __name__ == "__main__":
    unittest.main()
