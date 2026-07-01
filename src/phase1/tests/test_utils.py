"""
tests/test_utils.py — utils.py 核心函数的单元测试

不依赖网络，纯逻辑测试。

运行：python -m src.phase1.tests.test_utils
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.phase1.utils import (
    normalize_title, clean_doi, doi_match, strip_arxiv_version,
    arxiv_id_match, title_match, is_oa_pollution,
)


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)


# ── normalize_title ────────────────────────────────────────────────────

def test_normalize_title_basic():
    assert_eq(normalize_title("Hello World"), "helloworld")
    assert_eq(normalize_title("  Trim Me!  "), "trimme")
    assert_eq(normalize_title(""), "")


def test_normalize_title_unicode():
    r"""中文标点应被去掉，但中文字符保留（因 \w 包含 Unicode）。"""
    result = normalize_title("DNA水凝胶合成")
    assert_true(len(result) > 0, "应保留中文")


# ── DOI 比对 ──────────────────────────────────────────────────────────

def test_doi_match_basic():
    assert_true(doi_match("10.1103/PhysRevLett.128.133001", "10.1103/PhysRevLett.128.133001"))


def test_doi_match_url_prefix():
    assert_true(doi_match("https://doi.org/10.1103/abc", "10.1103/abc"))


def test_doi_match_case_insensitive():
    assert_true(doi_match("10.1103/ABC", "10.1103/abc"))


def test_doi_match_no_match():
    assert_true(not doi_match("10.1103/abc", "10.1103/xyz"))
    assert_true(not doi_match(None, "10.1103/abc"))
    assert_true(not doi_match("", "10.1103/abc"))


# ── arXiv ID 比对 ────────────────────────────────────────────────────

def test_arxiv_id_match_basic():
    assert_true(arxiv_id_match("2103.15014", "2103.15014"))


def test_arxiv_id_match_version_ignore():
    assert_true(arxiv_id_match("2103.15014v1", "2103.15014"))
    assert_true(arxiv_id_match("2103.15014v1", "2103.15014v2"))


def test_arxiv_id_match_no_match():
    assert_true(not arxiv_id_match("2103.15014", "2103.15015"))


# ── 标题匹配 ─────────────────────────────────────────────────────────

def test_title_match_exact():
    assert_true(title_match("DNA Hydrogel Synthesis", "DNA Hydrogel Synthesis"))


def test_title_match_substring():
    assert_true(title_match("DNA Hydrogel", "Convenient DNA Hydrogel Synthesis via Primers"))


def test_title_match_case_insensitive():
    assert_true(title_match("DNA Hydrogel", "dna hydrogel"))


def test_title_match_no_match():
    assert_true(not title_match("DNA Hydrogel", "Atmospheric Remote Sensing"))


def test_title_match_empty():
    assert_true(not title_match("", "anything"))
    assert_true(not title_match("anything", ""))


# ── OA 错位关键词过滤 ─────────────────────────────────────────────────

def test_oai_pollution_detects_dna_hydrogel():
    assert_true(is_oa_pollution("Convenient DNA Hydrogel Synthesis via Primers"))


def test_oai_pollution_detects_wind_imaging():
    assert_true(is_oa_pollution("Calibration of Frequency Shift System of Wind Imaging Interferometer"))


def test_oai_pollution_detects_agriculture():
    assert_true(is_oa_pollution("Soil Moisture Effects on Agriculture Yield"))


def test_oai_pollution_allows_real_physics():
    """真实物理论文不应被错位过滤误判。"""
    real_titles = [
        "Ionization energy of liquid water revisited",
        "Different timescales during ultrafast stilbene isomerization",
        "Intermolecular Coulombic Decay in Liquid Water",
        "Resolving the phase of Fano resonance wave packets with photoelectron spectroscopy",
        "A liquid-phase high-order harmonic generation apparatus",
    ]
    for t in real_titles:
        if is_oa_pollution(t):
            raise AssertionError(f"False positive: {t}")


def test_oai_pollution_handles_empty():
    assert_true(not is_oa_pollution(""))
    assert_true(not is_oa_pollution(None))


# ── 测试入口 ──────────────────────────────────────────────────────────

TESTS = [
    test_normalize_title_basic,
    test_normalize_title_unicode,
    test_doi_match_basic,
    test_doi_match_url_prefix,
    test_doi_match_case_insensitive,
    test_doi_match_no_match,
    test_arxiv_id_match_basic,
    test_arxiv_id_match_version_ignore,
    test_arxiv_id_match_no_match,
    test_title_match_exact,
    test_title_match_substring,
    test_title_match_case_insensitive,
    test_title_match_no_match,
    test_title_match_empty,
    test_oai_pollution_detects_dna_hydrogel,
    test_oai_pollution_detects_wind_imaging,
    test_oai_pollution_detects_agriculture,
    test_oai_pollution_allows_real_physics,
    test_oai_pollution_handles_empty,
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