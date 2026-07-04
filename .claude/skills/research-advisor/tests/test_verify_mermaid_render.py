import importlib.util
import sys
import unittest
import uuid
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
