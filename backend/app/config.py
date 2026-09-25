"""
AETHER Capital — Application Configuration
Uses Pydantic Settings for type-safe environment variable management.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────
    PROJECT_NAME: str = "AETHER Capital"
    VERSION: str = "5.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    DEMO_MODE: bool = True  # When True, uses deterministic fallback data if APIs unavailable

    # ── Security ─────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "aether-dev-secret-change-in-production-2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # ── Database ─────────────────────────────────────────────────
    # SQLite by default for zero-config local dev; set DATABASE_URL for PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).resolve().parent.parent.parent / 'data' / 'aether.db'}"
    )

    # ── Redis (Optional) ─────────────────────────────────────────
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)

    # ── AI / LLM ─────────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")

    # ── Quantitative Risk Constraints ────────────────────────────
    MAX_VOLATILITY_THRESHOLD: float = 0.65      # 65% annualized hard veto
    MAX_SINGLE_POSITION_PCT: float = 0.20       # 20% max single position
    MAX_PORTFOLIO_EXPOSURE: float = 1.0         # 100% max portfolio exposure
    MAX_DRAWDOWN_PCT: float = 0.15              # 15% max drawdown
    RISK_FREE_RATE: float = 0.04                # 4% US Treasury benchmark
    DEFAULT_SLIPPAGE_BPS: float = 5.0           # 5 basis points
    INITIAL_CASH: float = 100_000.0             # Paper trading starting capital

    # ── Paths ────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"

    # ── Cache ────────────────────────────────────────────────────
    CACHE_TTL_SECONDS: int = 3600  # 1 hour

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def has_openai_key(self) -> bool:
        return bool(self.OPENAI_API_KEY and not self.OPENAI_API_KEY.startswith("your_") and len(self.OPENAI_API_KEY) > 20)


settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
