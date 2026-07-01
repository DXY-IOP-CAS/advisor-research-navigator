"""
utils.py — 阶段 1 共享工具库

被所有 step 脚本引用。提供的函数：
  normalize_title(str) → str      标题归一化（去标点小写去空格）
  clean_doi(str) → str            清洗 DOI 协议前缀
  doi_match(str, str) → bool      DOI 是否相同
  strip_arxiv_version(str) → str  去除 arXiv ID 版本后缀
  arxiv_id_match(str, str) → bool arXiv ID 是否相同
  title_match(str, str) → bool    标题模糊匹配
  write_output(data, path) → None 写 JSON 文件/输出
  safe_json(data) → str           安全 JSON 序列化

  class RateLimiter:               GS 限速器（2 req/min, 120 req/hr）
  retry(max_retries=3, delay=2):   API 重试装饰器（指数退避）
"""

import json
import re
import sys
import time
import os
import logging
from functools import wraps
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, Type

logger = logging.getLogger("utils")

# ── 通用输出模式（文档用） ────────────────────────────────────────────

COMMON_PAPER_SCHEMA = {
    "title": str,
    "year": (int, type(None)),
    "authors": (list, type(None)),
    "journal": (str, type(None)),
    "doi": (str, type(None)),
    "arxiv_id": (str, type(None)),
    "citation_count": (int, type(None)),
    "source": str,
    "abstract": (str, type(None)),
}

COMMON_SOURCE_OUTPUT = {
    "pipeline": str,
    "source": str,
    "status": str,
    "error": (str, type(None)),
    "professor": (dict, type(None)),
    "papers": list,
    "metadata": (dict, type(None)),
}


# ── 标题归一化 ────────────────────────────────────────────────────────

def normalize_title(title: str) -> str:
    """归一化标题：去标点 → 小写 → 去空格。"""
    if not title:
        return ""
    cleaned = re.sub(r"[^\w\s]", "", title)
    return re.sub(r"\s+", "", cleaned.lower().strip())


# ── DOI 比对 ──────────────────────────────────────────────────────────

def clean_doi(doi: str) -> str:
    """清洗 DOI：去空格、小写、去协议前缀。"""
    doi = doi.strip().lower()
    return doi.removeprefix("https://doi.org/").removeprefix("http://doi.org/").removeprefix("doi:")

def doi_match(doi1: Optional[str], doi2: Optional[str]) -> bool:
    if not doi1 or not doi2:
        return False
    return clean_doi(doi1) == clean_doi(doi2)


# ── arXiv ID 比对 ────────────────────────────────────────────────────

def strip_arxiv_version(arxiv_id: str) -> str:
    return re.sub(r"v\d+$", "", arxiv_id.strip())

def arxiv_id_match(id1: Optional[str], id2: Optional[str]) -> bool:
    if not id1 or not id2:
        return False
    return strip_arxiv_version(id1) == strip_arxiv_version(id2)


# ── OA 错位论文过滤 ───────────────────────────────────────────────────

OA_POLLUTION_KEYWORDS = [
    "dna hydrogel", "veterinary", "livestock", "agriculture",
    "wind imaging interferometer", "atmospheric remote sensing",
    "soil moisture", "plant science", "biomass",
    "marine biology", "fishery", "veterinary medicine",
]

def is_oa_pollution(title: str) -> bool:
    """检测论文标题是否是 OpenAlex 错位的（同名不同领域）。

    返回 True = 疑似错位（应剔除）
    """
    if not title:
        return False
    t = title.lower()
    return any(kw in t for kw in OA_POLLUTION_KEYWORDS)


# ── 标题模糊匹配 ─────────────────────────────────────────────────────

def title_match(t1: str, t2: str) -> bool:
    """返回 True 如果两标题匹配（精确匹配或完整子串）。"""
    n1, n2 = normalize_title(t1), normalize_title(t2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    if n1 in n2 or n2 in n1:
        return True
    return False


# ── JSON I/O ─────────────────────────────────────────────────────────

def safe_json(data: Any, indent: int = 2) -> str:
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)

def write_output(data: Any, output_path: Optional[str] = None) -> None:
    text = safe_json(data)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
        sys.stdout.write("\n")


# ── GS 限速器（PoP 式） ──────────────────────────────────────────────

class RateLimiter:
    """Publish or Perish 式自适应限速。

    仅被 step2_gs 使用，scholarly 库内部另有限速逻辑。
    """

    MAX_PER_MINUTE = 2
    YELLOW_PER_HOUR = 120
    RED_PER_HOUR = 150

    def __init__(self):
        self.minute_window: Deque[float] = deque()
        self.hour_window: Deque[float] = deque()

    def wait_if_needed(self) -> None:
        now = time.time()
        self._slide_window(now)

        if len(self.hour_window) >= self.RED_PER_HOUR:
            sleep_time = 600 + (len(self.hour_window) - self.RED_PER_HOUR) * 120
            time.sleep(sleep_time)
            return self.wait_if_needed()

        if len(self.hour_window) >= self.YELLOW_PER_HOUR:
            sleep_time = 120 + (len(self.hour_window) - self.YELLOW_PER_HOUR) * 30
            time.sleep(sleep_time)
            return self.wait_if_needed()

        if len(self.minute_window) >= self.MAX_PER_MINUTE:
            sleep_time = max(10.0, 60.0 / self.MAX_PER_MINUTE * len(self.minute_window))
            time.sleep(sleep_time)
            return self.wait_if_needed()

        self.minute_window.append(now)
        self.hour_window.append(now)

    def _slide_window(self, now: float) -> None:
        while self.minute_window and self.minute_window[0] < now - 60:
            self.minute_window.popleft()
        while self.hour_window and self.hour_window[0] < now - 3600:
            self.hour_window.popleft()


# ── 重试装饰器 ────────────────────────────────────────────────────────

def retry(
    max_retries: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
) -> Callable:
    """API 调用重试装饰器。

    对 retryable_exceptions 中的异常类型自动重试。
    默认只重试网络/超时/5xx 类异常（即 HTTP 层面可恢复的错误）。

    用法：
        @retry(max_retries=2, delay=1.0)
        def fetch_data(url):
            return urlopen(url).read()
    """
    if retryable_exceptions is None:
        retryable_exceptions = (OSError, TimeoutError, ConnectionError)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            wait = delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exc = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): "
                            f"{e}. Retrying in {wait:.1f}s"
                        )
                        time.sleep(wait)
                        wait *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
            raise last_exc
        return wrapper
    return decorator
