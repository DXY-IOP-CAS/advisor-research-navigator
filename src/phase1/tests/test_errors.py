"""
tests/test_errors.py — errors.py 测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.phase1.errors import (
    Phase1Error, SourceFetchError, SourceBlockedError,
    SourceRateLimitError, InvalidSchemaError, ProfessorIdentityError,
    report_source_status, suggest_remediation,
)


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)


def assert_in(needle, haystack, msg=""):
    if needle not in haystack:
        raise AssertionError(f"{msg}: '{needle}' not in '{haystack}'")


# ── 异常类型 ──────────────────────────────────────────────────────────

def test_phase1_error_is_exception():
    assert_true(issubclass(Phase1Error, Exception))


def test_source_fetch_error_carries_source_name():
    e = SourceFetchError("google_scholar", "connection timeout")
    assert_eq(e.source, "google_scholar")
    assert_in("google_scholar", str(e))
    assert_in("connection timeout", str(e))


def test_source_blocked_error_inherits_fetch():
    e = SourceBlockedError("google_scholar", "403 forbidden")
    assert_true(isinstance(e, SourceFetchError))
    assert_true(isinstance(e, Phase1Error))


def test_source_rate_limit_error_inherits_fetch():
    e = SourceRateLimitError("openalex", "503 service unavailable")
    assert_true(isinstance(e, SourceFetchError))


def test_invalid_schema_error_carries_field_info():
    e = InvalidSchemaError("papers", "list", "string")
    assert_eq(e.field, "papers")
    assert_in("papers", str(e))


def test_professor_identity_error_distinct():
    e = ProfessorIdentityError("email mismatch")
    assert_true(isinstance(e, Phase1Error))
    assert_in("email mismatch", str(e))


# ── report_source_status ──────────────────────────────────────────────

def test_report_source_status_minimal():
    s = report_source_status("google_scholar", "success")
    assert_eq(s["source"], "google_scholar")
    assert_eq(s["status"], "success")
    assert_true("error" not in s or s["error"] is None)


def test_report_source_status_with_error():
    s = report_source_status("openalex", "error", "503 service unavailable")
    assert_eq(s["error"], "503 service unavailable")


# ── suggest_remediation ──────────────────────────────────────────────

def test_remediation_for_blocked_mentions_proxy():
    e = SourceBlockedError("google_scholar", "403")
    msg = suggest_remediation(e)
    assert_in("梯子", msg)


def test_remediation_for_rate_limit_mentions_email():
    e = SourceRateLimitError("openalex", "503")
    msg = suggest_remediation(e)
    assert_in("邮箱", msg)


def test_remediation_for_identity_mentions_verify():
    e = ProfessorIdentityError("email mismatch")
    msg = suggest_remediation(e)
    assert_in("核实", msg)


def test_remediation_for_schema():
    e = InvalidSchemaError("papers", "list", "string")
    msg = suggest_remediation(e)
    assert_in("papers", msg)


def test_remediation_for_unknown_error():
    e = Phase1Error("unknown")
    msg = suggest_remediation(e)
    assert_true(len(msg) > 0)


# ── 测试入口 ──────────────────────────────────────────────────────────

TESTS = [
    test_phase1_error_is_exception,
    test_source_fetch_error_carries_source_name,
    test_source_blocked_error_inherits_fetch,
    test_source_rate_limit_error_inherits_fetch,
    test_invalid_schema_error_carries_field_info,
    test_professor_identity_error_distinct,
    test_report_source_status_minimal,
    test_report_source_status_with_error,
    test_remediation_for_blocked_mentions_proxy,
    test_remediation_for_rate_limit_mentions_email,
    test_remediation_for_identity_mentions_verify,
    test_remediation_for_schema,
    test_remediation_for_unknown_error,
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