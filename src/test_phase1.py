#!/usr/bin/env python3
"""
Phase 1 数据采集管道的单元测试。

用法：
  python -m pytest scripts/test_phase1.py -v
  python scripts/test_phase1.py  （无 pytest 时的回退）
"""

import json
import os
import sys
import tempfile
import unittest

# 确保可导入同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_utils


class TestPaperUtils(unittest.TestCase):
    """paper_utils.py 的单元测试——不涉及网络调用。"""

    def test_normalize_title_removes_punctuation(self) -> None:
        self.assertEqual(paper_utils.normalize_title("Hello, World!"), "helloworld")

    def test_normalize_title_lowercases(self) -> None:
        self.assertEqual(paper_utils.normalize_title("ATTOSECOND PULSE"), "attosecondpulse")

    def test_normalize_title_collapses_spaces(self) -> None:
        self.assertEqual(paper_utils.normalize_title("Strong  Field   Physics"), "strongfieldphysics")

    def test_normalize_title_empty(self) -> None:
        self.assertEqual(paper_utils.normalize_title(""), "")
        self.assertEqual(paper_utils.normalize_title(None), "")  # type: ignore

    def test_doi_match_exact(self) -> None:
        self.assertTrue(paper_utils.doi_match(
            "10.1103/PhysRevLett.128.133001",
            "10.1103/PhysRevLett.128.133001",
        ))

    def test_doi_match_case_insensitive(self) -> None:
        self.assertTrue(paper_utils.doi_match(
            "10.1103/PhysRevLett.128.133001",
            "10.1103/PHYSREVLETT.128.133001",
        ))

    def test_doi_match_with_url_prefix(self) -> None:
        self.assertTrue(paper_utils.doi_match(
            "https://doi.org/10.1103/PhysRevLett.128.133001",
            "10.1103/PhysRevLett.128.133001",
        ))

    def test_doi_match_none(self) -> None:
        self.assertFalse(paper_utils.doi_match(None, "10.1103/xxx"))
        self.assertFalse(paper_utils.doi_match("10.1103/xxx", None))

    def test_doi_mismatch(self) -> None:
        self.assertFalse(paper_utils.doi_match(
            "10.1103/PhysRevLett.128.133001",
            "10.1103/PhysRevLett.128.133002",
        ))

    def test_arxiv_id_match_ignores_version(self) -> None:
        self.assertTrue(paper_utils.arxiv_id_match("2101.12345v1", "2101.12345v2"))
        self.assertTrue(paper_utils.arxiv_id_match("2101.12345", "2101.12345v1"))

    def test_arxiv_id_mismatch(self) -> None:
        self.assertFalse(paper_utils.arxiv_id_match("2101.12345", "2102.54321"))

    def test_title_match_exact(self) -> None:
        self.assertTrue(paper_utils.title_match(
            "Attosecond pulse generation by HHG",
            "Attosecond pulse generation by HHG",
        ))

    def test_title_match_different(self) -> None:
        self.assertFalse(paper_utils.title_match(
            "Quantum Monte Carlo for fermions",
            "Attosecond pulse generation",
        ))

    def test_title_match_substring(self) -> None:
        """归一化后一方含另一方子串 → 匹配。"""
        self.assertTrue(paper_utils.title_match(
            "Ab initio quantum Monte Carlo",
            "Ab initio quantum Monte Carlo simulation of fermions",
        ))

    def test_title_match_partial_overlap(self) -> None:
        """非子串关系的部分重叠 → 不匹配（归一化后无子串关系）。"""
        self.assertFalse(paper_utils.title_match(
            "Attosecond pulse generation by high harmonic generation: a review",
            "Attosecond pulse generation by HHG: a review",
        ))

    def test_best_field_priority(self) -> None:
        sources = [
            {"source": "openalex", "cited_by_count": 10},
            {"source": "s2", "cited_by_count": 15},
            {"source": "arxiv", "title": "Some paper"},
        ]
        self.assertEqual(paper_utils.best_field(sources, "cited_by_count", ["openalex", "s2"]), 10)
        self.assertEqual(paper_utils.best_field(sources, "title", ["openalex", "arxiv"]), "Some paper")

    def test_best_field_missing(self) -> None:
        sources = [{"source": "openalex", "cited_by_count": 10}]
        self.assertIsNone(paper_utils.best_field(sources, "tldr", ["openalex"]))

    def test_merge_paper_entries(self) -> None:
        entries = [
            {"source": "openalex", "title": "Test Paper", "doi": "10.1234/test", "cited_by_count": 10},
            {"source": "arxiv", "title": "Test Paper", "arxiv_id": "2101.12345", "cited_by_count": 5},
            {"source": "s2", "title": "Test Paper", "tldr": "This is a test paper."},
        ]
        merged = paper_utils.merge_paper_entries(entries)
        self.assertEqual(merged["title"], "Test Paper")
        self.assertEqual(merged["doi"], "10.1234/test")
        self.assertEqual(merged["cited_by_count"], 10)  # openalex 优先
        self.assertEqual(merged["tldr"], "This is a test paper.")
        self.assertEqual(merged["arxiv_id"], "2101.12345")
        self.assertEqual(merged["source_count"], 3)  # 3 个不同源

    def test_merge_single_entry(self) -> None:
        entries = [{"source": "openalex", "title": "Solo Paper", "doi": "10.1234/solo"}]
        merged = paper_utils.merge_paper_entries(entries)
        self.assertEqual(merged["title"], "Solo Paper")
        self.assertEqual(merged["source_count"], 1)

    def test_merge_empty(self) -> None:
        self.assertEqual(paper_utils.merge_paper_entries([]), {})


class TestIntegrationPointers(unittest.TestCase):
    """集成测试占位——标记了哪些测试需要网络。

    这些测试默认跳过，因为需要外部 API 调用。
    在开发阶段手动运行：
      python -m pytest scripts/test_phase1.py -v -k integration
    """

    @unittest.skip("需要 OpenAlex 网络访问")
    def test_openalex_fetch_real_author(self) -> None:
        """对已知 OpenAlex ID 做真实的 API 调用测试。"""
        pass

    @unittest.skip("需要 arXiv 网络访问")
    def test_arxiv_search_real(self) -> None:
        """对已知作者做真实的 arXiv 搜索测试。"""
        pass


class TestOutputFormat(unittest.TestCase):
    """验证脚本输出格式符合预期。"""

    def setUp(self) -> None:
        self.sample_merged = {
            "merged_count": 1,
            "source_stats": {"openalex": 5, "arxiv": 3},
            "sources_used": ["openalex", "arxiv"],
            "works": [
                {
                    "title": "Test",
                    "doi": "10.1234/test",
                    "sources": ["openalex", "arxiv"],
                    "source_count": 2,
                }
            ],
        }

    def test_json_serializable(self) -> None:
        """确保输出可以安全序列化为 JSON。"""
        text = paper_utils.safe_json(self.sample_merged)
        parsed = json.loads(text)
        self.assertEqual(parsed["merged_count"], 1)
        self.assertEqual(len(parsed["works"]), 1)

    def test_write_to_file(self) -> None:
        """验证写入文件功能。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            tmp_path = f.name
        try:
            paper_utils.write_output(self.sample_merged, tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["merged_count"], 1)
        finally:
            os.unlink(tmp_path)

    def test_title_normalized_field(self) -> None:
        """标题含特殊字符时归一化测试。"""
        titles = [
            ("HHG in solids: a review", "hhginsolidsareview"),
            ("Ab initio quantum Monte Carlo", "abinitioquantummontecarlo"),
            ("超快光谱", "超快光谱"),
        ]
        for raw, expected in titles:
            self.assertEqual(paper_utils.normalize_title(raw), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
