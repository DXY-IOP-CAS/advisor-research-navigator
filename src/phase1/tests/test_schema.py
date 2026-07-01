"""
tests/test_schema.py — schema.py 验证测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.phase1.schema import (
    Paper, Professor, SourceOutput, MergedPaper, MergedOutput,
    validate_source_output, validate_merged_output,
)


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)


def assert_raises(callable_, exc_type, msg=""):
    try:
        callable_()
    except exc_type as e:
        return e
    raise AssertionError(f"{msg}: expected {exc_type.__name__}")


# ── Paper ─────────────────────────────────────────────────────────────

def test_paper_minimal():
    p = Paper(title="Test Paper")
    d = p.to_dict()
    assert_eq(d["title"], "Test Paper")
    assert_true("year" not in d, "year=None 应被过滤")


def test_paper_full():
    p = Paper(
        title="Test", year=2020, authors=["Alice", "Bob"],
        journal="Nature", doi="10.1038/test", arxiv_id="2001.12345",
        citation_count=42, source="google_scholar", abstract="abstract text"
    )
    d = p.to_dict()
    assert_eq(d["year"], 2020)
    assert_eq(d["authors"], ["Alice", "Bob"])
    assert_eq(d["citation_count"], 42)


def test_paper_from_dict_missing_title_raises():
    """从无 title 的 dict 构造 Paper 应抛 ValueError。"""
    assert_raises(lambda: Paper.from_dict({}), ValueError)


def test_paper_from_dict_tolerates_missing_fields():
    """缺失字段应容忍（year/authors 等为 None）。"""
    p = Paper.from_dict({"title": "T", "year": 2020})
    assert_eq(p.title, "T")
    assert_eq(p.year, 2020)
    assert_eq(p.authors, None)


def test_paper_from_dict_filters_invalid_year():
    """year 是字符串时应被丢弃为 None。"""
    p = Paper.from_dict({"title": "T", "year": "not a year"})
    assert_eq(p.year, None)


# ── Professor ─────────────────────────────────────────────────────────

def test_professor_gs_only():
    p = Professor(name="Zhang San", gs_id="ls7XuGoAAAAJ", h_index=15)
    d = p.to_dict()
    assert_eq(d["name"], "Zhang San")
    assert_eq(d["gs_id"], "ls7XuGoAAAAJ")
    assert_eq(d["h_index"], 15)
    assert_true("oa_id" not in d, "None 字段应被过滤")


def test_professor_from_dict_invalid_h_index():
    """h_index 是字符串时应被丢弃。"""
    p = Professor.from_dict({"h_index": "not a number"})
    assert_eq(p.h_index, None)


# ── SourceOutput ──────────────────────────────────────────────────────

def test_source_output_minimal():
    so = SourceOutput(source="google_scholar")
    d = so.to_dict()
    assert_eq(d["source"], "google_scholar")
    assert_eq(d["status"], "success")
    assert_eq(d["papers"], [])


def test_source_output_round_trip():
    """构造 -> to_dict -> from_dict 应该等价。"""
    original = SourceOutput(
        source="openalex", status="success",
        professor=Professor(name="X", h_index=10),
        papers=[Paper(title="P1", year=2020), Paper(title="P2", year=2021)],
    )
    d = original.to_dict()
    restored = SourceOutput.from_dict(d)
    assert_eq(restored.source, "openalex")
    assert_eq(len(restored.papers), 2)
    assert_eq(restored.papers[0].title, "P1")


def test_source_output_from_dict_filters_invalid_papers():
    """无 title 的论文条目应被静默丢弃。"""
    so = SourceOutput.from_dict({
        "source": "arxiv",
        "papers": [
            {"title": "Good", "year": 2020},
            {"title": "", "year": 2020},   # 无 title，应丢弃
            {"year": 2020},                 # 无 title，应丢弃
            "not a dict",                   # 非 dict，应跳过
        ]
    })
    assert_eq(len(so.papers), 1)
    assert_eq(so.papers[0].title, "Good")


def test_source_output_missing_source_raises():
    assert_raises(
        lambda: SourceOutput.from_dict({"status": "success", "papers": []}),
        ValueError
    )


# ── validate_source_output ────────────────────────────────────────────

def test_validate_source_output_success():
    errs = validate_source_output({
        "source": "google_scholar", "status": "success", "papers": []
    })
    assert_eq(errs, [])


def test_validate_source_output_invalid_source():
    errs = validate_source_output({"source": "fake", "status": "success"})
    assert_true(len(errs) > 0)


def test_validate_source_output_invalid_status():
    errs = validate_source_output({"source": "google_scholar", "status": "wrong"})
    assert_true(any("status" in e for e in errs))


def test_validate_source_output_papers_not_list():
    errs = validate_source_output({"source": "gs", "status": "success", "papers": "wrong"})
    assert_true(any("papers" in e for e in errs))


def test_validate_source_output_raises_when_requested():
    assert_raises(
        lambda: validate_source_output({"source": "fake"}, raise_on_error=True),
        ValueError
    )


# ── MergedOutput ──────────────────────────────────────────────────────

def test_merged_paper_sources():
    base = Paper(title="Test", year=2020, source="google_scholar")
    mp = MergedPaper.from_paper(base, ["google_scholar", "openalex"])
    assert_eq(mp.source_count, 2)
    assert_eq(mp.sources, ["google_scholar", "openalex"])


def test_merged_output_round_trip():
    mo = MergedOutput(
        sources_used=["google_scholar", "openalex"],
        source_status={"google_scholar": "success", "openalex": "success"},
        professor=Professor(name="X"),
        papers=[MergedPaper.from_paper(Paper(title="P"), ["gs", "oa"])],
        statistics={"total": 1, "by_source": {"gs": 1, "oa": 1}},
    )
    d = mo.to_dict()
    assert_eq(d["step"], "merge")
    assert_eq(d["statistics"]["total"], 1)


def test_validate_merged_output_missing_step():
    errs = validate_merged_output({"sources_used": [], "papers": []})
    assert_true(any("step" in e for e in errs))


# ── 测试入口 ──────────────────────────────────────────────────────────

TESTS = [
    test_paper_minimal,
    test_paper_full,
    test_paper_from_dict_missing_title_raises,
    test_paper_from_dict_tolerates_missing_fields,
    test_paper_from_dict_filters_invalid_year,
    test_professor_gs_only,
    test_professor_from_dict_invalid_h_index,
    test_source_output_minimal,
    test_source_output_round_trip,
    test_source_output_from_dict_filters_invalid_papers,
    test_source_output_missing_source_raises,
    test_validate_source_output_success,
    test_validate_source_output_invalid_source,
    test_validate_source_output_invalid_status,
    test_validate_source_output_papers_not_list,
    test_validate_source_output_raises_when_requested,
    test_merged_paper_sources,
    test_merged_output_round_trip,
    test_validate_merged_output_missing_step,
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