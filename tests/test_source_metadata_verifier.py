import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / ".claude" / "skills" / "research-advisor" / "scripts" / "verify_source_metadata.py"

spec = importlib.util.spec_from_file_location("verify_source_metadata", VERIFY_PATH)
verify_source_metadata = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["verify_source_metadata"] = verify_source_metadata
spec.loader.exec_module(verify_source_metadata)


class SourceMetadataVerifierTests(unittest.TestCase):
    def test_accepts_matching_doi_title(self):
        text = """## 参考文献与资料

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|
| <a id="p1"></a>[P1] | Correct Paper Title | 支撑测试 | https://doi.org/10.1234/example | 论文 |
"""
        rows = verify_source_metadata.extract_doi_rows("03_论文路线.md", text)
        result = verify_source_metadata.verify_rows(
            rows,
            metadata={"10.1234/example": "Correct Paper Title"},
        )

        self.assertTrue(result.ok, "\n".join(result.messages))

    def test_flags_doi_title_mismatch(self):
        text = """## 参考文献与资料

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|
| <a id="p1"></a>[P1] | Wrong Mechanism Title | 支撑测试 | https://doi.org/10.1234/example | 论文 |
"""
        rows = verify_source_metadata.extract_doi_rows("03_论文路线.md", text)
        result = verify_source_metadata.verify_rows(
            rows,
            metadata={"10.1234/example": "Correct Paper Title"},
        )

        self.assertFalse(result.ok)
        self.assertIn(
            "[FAIL] 03_论文路线.md [P1] DOI title mismatch: document='Wrong Mechanism Title' crossref='Correct Paper Title'",
            result.messages,
        )

    def test_ignores_non_doi_rows_without_crossing_table_lines(self):
        text = """## 参考文献与资料

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|
| <a id="p1"></a>[P1] | Nature Paper Title | 支撑测试 | https://www.nature.com/articles/example | 论文 |
| <a id="p2"></a>[P2] | DOI Paper Title | 支撑测试 | https://doi.org/10.1234/example | 论文 |
"""

        rows = verify_source_metadata.extract_doi_rows("03_论文路线.md", text)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].label, "[P2]")
        self.assertEqual(rows[0].title, "DOI Paper Title")
        self.assertEqual(rows[0].doi, "10.1234/example")

    def test_converts_nature_article_links_to_doi(self):
        text = """## 参考文献与资料

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|
| <a id="p1"></a>[P1] | Nature Article Title | 支撑测试 | https://www.nature.com/articles/s41467-025-62162-6 | 论文 |
"""

        rows = verify_source_metadata.extract_doi_rows("03_论文路线.md", text)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].label, "[P1]")
        self.assertEqual(rows[0].doi, "10.1038/s41467-025-62162-6")

    def test_verify_prof_dir_uses_offline_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = Path(tmp)
            (prof_dir / "03_论文路线.md").write_text(
                """# 测试

## 参考文献与资料

| 编号 | 文献或资料 | 支撑内容 | 链接 | 类型 |
|:---|:---|:---|:---|:---|
| <a id="p1"></a>[P1] | Correct Paper Title | 支撑测试 | https://doi.org/10.1234/example | 论文 |
""",
                encoding="utf-8",
            )

            result = verify_source_metadata.verify_prof_dir(
                prof_dir,
                metadata={"10.1234/example": "Correct Paper Title"},
                filenames=["03_论文路线.md"],
            )

        self.assertTrue(result.ok, "\n".join(result.messages))


if __name__ == "__main__":
    unittest.main()
