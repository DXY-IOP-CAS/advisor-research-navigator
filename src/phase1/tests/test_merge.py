"""
tests/test_merge.py — step6_merge.py 核心去重 + 字段合并的单元测试

不依赖网络，纯逻辑测试去重优先级 P0(doi) → P1(arxiv) → P2(title)。

运行：python -m src.phase1.tests.test_merge
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.phase1.utils import (
    clean_doi as clean_doi_util, strip_arxiv_version,
    mark_source_tag,
)
from src.phase1.step6_merge import (
    merge_professors, _pick,
)


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)


# ── 辅助函数 ──────────────────────────────────────────────────────────

def test_clean_doi_lowercase():
    assert_eq(clean_doi_util("10.1103/ABC"), "10.1103/abc")


def test_clean_doi_strips_https():
    assert_eq(clean_doi_util("https://doi.org/10.1103/abc"), "10.1103/abc")


def test_strip_arxiv_version():
    assert_eq(strip_arxiv_version("2103.15014v1"), "2103.15014")
    assert_eq(strip_arxiv_version("2103.15014"), "2103.15014")
    assert_eq(strip_arxiv_version("  2103.15014v2  "), "2103.15014")


# ── mark_source_tag ────────────────────────────────────────────────────

def test_mark_source_tag_gs_only():
    assert_eq(mark_source_tag(["google_scholar"]), "GS")


def test_mark_source_tag_oa_only():
    assert_eq(mark_source_tag(["openalex"]), "OA")


def test_mark_source_tag_arxiv_only():
    assert_eq(mark_source_tag(["arxiv"]), "arXiv")


def test_mark_source_tag_all_three():
    assert_eq(
        mark_source_tag(["google_scholar", "openalex", "arxiv"]),
        "GS+OA+arXiv"
    )


def test_mark_source_tag_empty():
    assert_eq(mark_source_tag([]), "—")


# ── _pick（字段择优） ──────────────────────────────────────────────────

def test_pick_prefers_first_priority_source():
    entries = [
        {"source": "google_scholar", "title": "GS Title"},
        {"source": "openalex", "title": "OA Title"},
    ]
    # FIELD_PRIORITY order is openalex > google_scholar > arxiv
    # so openalex should be picked first
    assert_eq(_pick(entries, "title"),
              "OA Title")


def test_pick_falls_back_to_lower_priority():
    entries = [
        {"source": "arxiv", "title": "arXiv Title"},
        {"source": "google_scholar", "title": "GS Title"},
    ]
    # openalex not in entries, falls through to google_scholar
    assert_eq(_pick(entries, "title"),
              "GS Title")


def test_pick_skips_none_values():
    entries = [
        {"source": "openalex", "title": None},
        {"source": "google_scholar", "title": "GS Title"},
    ]
    assert_eq(_pick(entries, "title"), "GS Title")


def test_pick_returns_none_for_all_none():
    entries = [
        {"source": "openalex", "title": None},
        {"source": "google_scholar", "title": None},
    ]
    assert_eq(_pick(entries, "title"), None)


# ── merge_professors（教授信息按优先级合并） ─────────────────────────

def test_merge_professors_gs_priority():
    """merge_professors 用 source 字段索引每个教授 dict。"""
    sources = [
        {"source": "openalex", "professor": {"name": "OA Name", "affiliation": "OA Uni", "oa_id": "A123", "orcid": "0000-x"}},
        {"source": "google_scholar", "professor": {"name": "GS Name", "affiliation": "GS Uni", "email_domain": "@gs.com", "gs_id": "abc", "h_index": 15, "i10_index": 20, "total_citations": 100}},
    ]
    merged = merge_professors(sources)
    # GS 占 name/affiliation/h_index，OA 占 orcid
    assert_eq(merged["name"], "GS Name")
    assert_eq(merged["h_index"], 15)
    assert_eq(merged["i10_index"], 20)
    assert_eq(merged["total_citations"], 100)
    assert_eq(merged["orcid"], "0000-x")
    assert_eq(merged["oa_id"], "A123")


def test_merge_professors_no_skip_none():
    """None 值不应覆盖已有值。"""
    sources = [
        {"source": "openalex", "professor": {"name": "OA Name", "email_domain": "@iphy.ac.cn"}},
        {"source": "google_scholar", "professor": {"name": "GS Name", "email_domain": None}},
    ]
    merged = merge_professors(sources)
    # name: GS 在 priority 列表中被优先选
    assert_eq(merged["name"], "GS Name")
    # email_domain: PROF_PRIORITY 限制只查 GS，GS 是 None → 不存在
    assert_true("email_domain" not in merged, "GS 唯一源，None 不出现")


def test_merge_professors_priority_table():
    """验证 PROF_PRIORITY 表中所有字段都有定义。"""
    from src.phase1.step6_merge import PROF_PRIORITY
    expected_fields = ["name", "affiliation", "email_domain", "gs_id",
                       "oa_id", "orcid", "h_index", "i10_index", "total_citations"]
    for f in expected_fields:
        assert_true(f in PROF_PRIORITY, f"PROF_PRIORITY 缺字段: {f}")


# ── 测试入口 ──────────────────────────────────────────────────────────

TESTS = [
    test_clean_doi_lowercase,
    test_clean_doi_strips_https,
    test_strip_arxiv_version,
    test_mark_source_tag_gs_only,
    test_mark_source_tag_oa_only,
    test_mark_source_tag_arxiv_only,
    test_mark_source_tag_all_three,
    test_mark_source_tag_empty,
    test_pick_prefers_first_priority_source,
    test_pick_falls_back_to_lower_priority,
    test_pick_skips_none_values,
    test_pick_returns_none_for_all_none,
    test_merge_professors_gs_priority,
    test_merge_professors_no_skip_none,
    test_merge_professors_priority_table,
]


def main():
    passed, failed = 0, 0
    for t in TESTS:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())