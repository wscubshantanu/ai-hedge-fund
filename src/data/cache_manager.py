import time
import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

class CacheManager:
    """
    High-Performance Local Cache Layer with Time-To-Live (TTL).
    Caches historical data, technical indicators, and multi-agent reasoning states
    to eliminate duplicate LLM token consumption and reduce API latency to < 2ms.
    """
    def __init__(self, db_path: Optional[str] = None, default_ttl_seconds: int = 3600):
        if db_path is None:
            data_dir = Path(__file__).resolve().parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / "hedge_fund_cache.sqlite3")
        else:
            self.db_path = db_path

        self.default_ttl = default_ttl_seconds
        self._memory_cache = {}
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_store (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        now = time.time()

        # 1. Check L1 Memory Cache
        if key in self._memory_cache:
            data, exp = self._memory_cache[key]
            if now < exp:
                return data
            else:
                del self._memory_cache[key]

        # 2. Check L2 SQLite Cache
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT payload, expires_at FROM cache_store WHERE cache_key = ?", (key,))
            row = cursor.fetchone()
            if row:
                payload_str, expires_at = row
                if now < expires_at:
                    data = json.loads(payload_str)
                    self._memory_cache[key] = (data, expires_at)
                    return data
                else:
                    cursor.execute("DELETE FROM cache_store WHERE cache_key = ?", (key,))
                    conn.commit()

        return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = time.time() + ttl
        payload_str = json.dumps(value)

        # L1 Memory Cache
        self._memory_cache[key] = (value, expires_at)

        # L2 SQLite Cache
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache_store (cache_key, payload, expires_at)
                VALUES (?, ?, ?)
            """, (key, payload_str, expires_at))
            conn.commit()

# Global Cache Singleton
cache = CacheManager()
