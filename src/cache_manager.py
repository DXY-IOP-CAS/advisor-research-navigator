"""
cache_manager.py — 缓存模块，供 gs_lite / gs_browser / openalex / arxiv 使用。

用法：
  cache = CacheManager()
  data = cache.get("gs", user_id)   # None 表示过期或不存在
  cache.set("gs", user_id, data)     # 写入缓存

缓存目录：.cache/gs/ .cache/oa/ .cache/arxiv/
缓存 TTL：30 天（在构造函数中配置）
文件格式：JSON，每文件单条记录
"""

import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger("cache_manager")

DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
DEFAULT_TTL_DAYS = 30


class CacheManager:
    """自动过期、断点续跑友好的本地缓存。"""

    def __init__(
        self,
        cache_dir: str = DEFAULT_CACHE_DIR,
        ttl_days: int = DEFAULT_TTL_DAYS,
    ):
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_days * 86400
        # 每个源一个子目录
        self._subdirs = {}

    def _subdir(self, source: str) -> str:
        """获取某源的缓存子目录，不存在则创建。"""
        if source not in self._subdirs:
            path = os.path.join(self.cache_dir, source)
            os.makedirs(path, exist_ok=True)
            self._subdirs[source] = path
        return self._subdirs[source]

    def _path(self, source: str, key: str) -> str:
        """缓存文件路径。key 中的非法字符替换为 _。"""
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in key)
        return os.path.join(self._subdir(source), f"{safe}.json")

    def get(self, source: str, key: str) -> Optional[Any]:
        """读缓存。过期或不存在返回 None。"""
        path = self._path(source, key)
        try:
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)
            # TTL 检查
            if time.time() - record.get("cached_at", 0) > self.ttl_seconds:
                logger.info(f"Cache expired (>{self.ttl_seconds}s): {source}/{key}")
                return None
            logger.info(f"Cache hit: {source}/{key} ({len(json.dumps(record.get('data', {})))} bytes)")
            return record.get("data")
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.warning(f"Cache read error {source}/{key}: {e}")
            return None

    def set(self, source: str, key: str, data: Any) -> None:
        """写缓存。"""
        path = self._path(source, key)
        record = {
            "cached_at": time.time(),
            "source": source,
            "key": key,
            "data": data,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Cache written: {source}/{key}")
        except Exception as e:
            logger.warning(f"Cache write error {source}/{key}: {e}")

    def is_fresh(self, source: str, key: str) -> bool:
        """检查缓存是否存在且未过期。"""
        return self.get(source, key) is not None

    def clear_expired(self, source: Optional[str] = None) -> int:
        """清理过期缓存。返回清理文件数。"""
        cleared = 0
        sources = [source] if source else os.listdir(self.cache_dir)
        for src in sources:
            dirpath = self._subdir(src)
            if not os.path.isdir(dirpath):
                continue
            for fname in os.listdir(dirpath):
                if not fname.endswith(".json"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        record = json.load(f)
                    if time.time() - record.get("cached_at", 0) > self.ttl_seconds:
                        os.remove(fpath)
                        cleared += 1
                except Exception:
                    continue
        logger.info(f"Cleared {cleared} expired cache files")
        return cleared

    def invalidate(self, source: str, key: str) -> None:
        """强制失效一条缓存。"""
        path = self._path(source, key)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
