"""
errors.py — 自定义异常和错误处理工具

所有 step 脚本用统一的异常类型，让 AI 和上层脚本都能精确处理错误。
"""

import logging
from typing import Optional

logger = logging.getLogger("phase1.errors")


# ── 自定义异常 ────────────────────────────────────────────────────────

class Phase1Error(Exception):
    """阶段 1 所有错误的基类。"""
    pass


class SourceFetchError(Phase1Error):
    """数据源获取失败（网络/API 错误）。"""
    def __init__(self, source: str, message: str, original: Optional[Exception] = None):
        self.source = source
        self.original = original
        super().__init__(f"[{source}] {message}")


class SourceBlockedError(SourceFetchError):
    """数据源被封锁（403/CAPTCHA）。需要换节点或等。"""
    pass


class SourceRateLimitError(SourceFetchError):
    """数据源触发速率限制（429/503）。需要降速或重试。"""
    pass


class InvalidSchemaError(Phase1Error):
    """数据不符合 schema 契约。"""
    def __init__(self, field: str, expected: str, actual: any):
        self.field = field
        self.expected = expected
        self.actual = actual
        super().__init__(f"Invalid schema at '{field}': expected {expected}, got {type(actual).__name__}")


class ProfessorIdentityError(Phase1Error):
    """身份验证失败。GS 邮箱与官网邮箱不匹配。"""
    pass


# ── 错误处理工具 ──────────────────────────────────────────────────────

def safe_log_error(message: str, exc: Optional[Exception] = None) -> None:
    """统一错误日志格式。"""
    if exc:
        logger.error(f"{message}: {type(exc).__name__}: {exc}")
    else:
        logger.error(message)


def report_source_status(source: str, status: str, error: Optional[str] = None) -> dict:
    """生成统一的源状态报告（用于合并步骤统计）。"""
    return {"source": source, "status": status, "error": error}


def suggest_remediation(error: Phase1Error) -> str:
    """对错误给出修复建议（不是 AI 重试，而是用户/上游动作）。"""
    if isinstance(error, SourceBlockedError):
        return (
            f"建议：换梯子节点或等 1-24h 自动恢复。"
            f"如果持续阻塞，fallback 到 OpenAlex 做主源。"
        )
    if isinstance(error, SourceRateLimitError):
        return (
            f"建议：检查是否用了真实邮箱。"
            f"如果用了 test@example.com 等保留域，OpenAlex 不认，会按匿名 1 req/s 限速。"
        )
    if isinstance(error, ProfessorIdentityError):
        return "建议：手动核实 GS profile 是否属于目标学者，可能需要换 ID。"
    if isinstance(error, InvalidSchemaError):
        return f"建议：检查 {error.field} 字段。期望 {error.expected}，实际 {type(error.actual).__name__}。"
    return "建议：查看完整错误日志。"